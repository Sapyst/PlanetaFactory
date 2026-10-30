extends Caso
## Divisor com filtro (divisor_filtro, fase 2.2b): modelo do estudo_esteiras_niveis.py, cena 'filtro'
## (arte/estudos/conv_logistica_base.py: divisor + leitor de item, câmera da IA, mostrador, seletor de prioridade).
## O item escolhido sai só pela saída do filtro; o resto vai pela saída de prioridade (ou em rodízio).


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 12):
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _rodar(f: Fabrica, s: float) -> void:
	for i in int(s * 30):
		f.tick(1.0 / 30.0)


## Linha entupida: itens encostados da saída até a entrada.
func _encher(e: EsteiraCaminho, item: String) -> void:
	var p := 0.0
	while p <= e.util() + 1e-4:
		e.inserir_em(item, p)
		p += EsteiraCaminho.ESPACO


func test_dados_e_modelo() -> void:
	var md: Dictionary = Registro.modelos.get("divisor_filtro", {})
	igual(md.get("estudo", ""), "estudo_esteiras_niveis.py", "convertido do estudo")
	igual(md.get("portas", []), Registro.modelos.divisor.portas, "mesmas portas do divisor (entra S, sai N/L/O)")
	verificar(md.get("anima", false), "mecanismo animado como o divisor")
	verificar(int(md.get("tris", 99999)) <= 4500, "leve (%d triângulos)" % md.get("tris", 0))
	var d: Array = md.dims
	verificar(float(d[0]) <= 1.001 and float(d[1]) <= 1.001, "dentro do tile (%s)" % str(d))
	igual(Registro.estruturas.divisor_filtro.grupo, "esteira")
	verificar("divisor_filtro" in Fabrica.DISTRIBUIDORES, "é distribuidor")
	verificar(Portas.eh_esteira("divisor_filtro"), "conta como esteira para as portas")
	verificar(ResourceLoader.exists("res://assets/icones/divisor_filtro.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return "divisor_filtro" in cat.pecas), "no menu")
	verificar(not Construtor.custo_de("divisor_filtro").is_empty(), "tem custo")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("divisor_filtro"), "jogável")
	verificar(not p.peca_liberada("divisor_filtro"), "travado no início")
	p.concluidas = {"eletronica": true, "automacao": true}
	verificar(p.disponivel("divisor_filtro"), "depois de automação")
	igual(p.custo("divisor_filtro"), {"pacote_pesquisa": 25, "pacote_automacao": 25}, "básico × 25 + automação × 25 (árvore)")
	p.concluidas["divisor_filtro"] = true
	verificar(p.peca_liberada("divisor_filtro"), "libera o divisor com filtro")


## Divisor com filtro no meio de uma linha norte; saídas N, L e O em esteiras; conta o que chega em cada uma.
func _montar(opcoes: Dictionary) -> Dictionary:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	c.executar(c.plano_linha("esteira", Vector2i(0, -6), Vector2i(0, -1), 0))
	var rel := c.executar(c.plano_peca("divisor_filtro", Vector2i(0, 0), 0))
	var div: int = rel.colocados[0]
	c.mapa.estruturas[div].merge(opcoes, true)
	c.executar(c.plano_linha("esteira", Vector2i(0, 1), Vector2i(0, 6), Construtor.rot_do_fluxo(0)))
	c.executar(c.plano_linha("esteira", Vector2i(1, 0), Vector2i(6, 0), Construtor.rot_do_fluxo(1)))
	c.executar(c.plano_linha("esteira", Vector2i(-1, 0), Vector2i(-6, 0), Construtor.rot_do_fluxo(3)))
	f.reconstruir()
	return {"c": c, "f": f, "div": div}


func _contar(m: Dictionary, itens: Array, s := 20.0) -> Dictionary:
	var f: Fabrica = m.f
	var ent: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(0, -6)][0]].esteira
	var cont := {"N": {}, "L": {}, "O": {}}
	var i := 0
	for q in int(s * 30):
		if q % 12 == 0 and i < itens.size():
			if ent.inserir_na_entrada(itens[i]):
				i += 1
		f.tick(1.0 / 30.0)
	for par in [["N", Vector2i(0, 6)], ["L", Vector2i(6, 0)], ["O", Vector2i(-6, 0)]]:
		var e: EsteiraCaminho = f.caminhos[f._no_tile[par[1]][0]].esteira
		for it in e.itens:
			cont[par[0]][it] = int(cont[par[0]].get(it, 0)) + 1
	return cont


func test_filtro_para_a_direita() -> void:
	var m := _montar({"filtro_item": "minerio_ferro", "saida_filtro": "L", "prioridade": "N"})
	var itens := []
	for k in 12:
		itens.append("minerio_ferro" if k % 2 == 0 else "placa_ferro")
	var cont := _contar(m, itens)
	igual(int(cont.L.get("minerio_ferro", 0)), 6, "todo o minério foi para a direita (L) %s" % str(cont))
	igual(int(cont.L.get("placa_ferro", 0)), 0, "nada além do filtrado na saída do filtro")
	igual(int(cont.N.get("placa_ferro", 0)), 6, "o resto foi pela prioridade (frente)")
	igual(cont.O.size(), 0, "a esquerda não recebeu nada (prioridade livre)")


func test_prioridade_transborda() -> void:
	# sem filtro, prioridade à esquerda: tudo vai para a esquerda; tirando a esquerda do caminho, vai para as outras
	var m := _montar({"prioridade": "O"})
	var itens := []
	for k in 8:
		itens.append("pedra")
	var cont := _contar(m, itens, 12.0)
	igual(int(cont.O.get("pedra", 0)), 8, "prioridade à esquerda leva tudo %s" % str(cont))
	# esquerda cheia (fim da linha entupido): transborda para as outras
	var m2 := _montar({"prioridade": "O"})
	var f: Fabrica = m2.f
	var esq: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-6, 0)][0]].esteira
	_encher(esq, "carvao")
	var itens2 := []
	for k in 6:
		itens2.append("pedra")
	var cont2 := _contar(m2, itens2, 12.0)
	igual(int(cont2.O.get("pedra", 0)), 0, "esquerda entupida não recebe")
	igual(int(cont2.N.get("pedra", 0)) + int(cont2.L.get("pedra", 0)), 6, "transbordou para frente/direita %s" % str(cont2))


func test_sem_opcoes_e_rodizio() -> void:
	var m := _montar({})
	var itens := []
	for k in 9:
		itens.append("pedra")
	var cont := _contar(m, itens, 15.0)
	for l in ["N", "L", "O"]:
		igual(int(cont[l].get("pedra", 0)), 3, "rodízio: 3 para %s %s" % [l, str(cont)])


func test_saida_do_filtro_cheia_espera() -> void:
	var m := _montar({"filtro_item": "carvao", "saida_filtro": "N"})
	var f: Fabrica = m.f
	var frente: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(0, 6)][0]].esteira
	_encher(frente, "pedra")
	var cont := _contar(m, ["carvao", "carvao"], 6.0)
	igual(int(cont.L.get("carvao", 0)) + int(cont.O.get("carvao", 0)), 0, "o filtrado não escapa por outra saída %s" % str(cont))
	igual(f.distribuidores[m.div].buffer.count("carvao") >= 1, true, "fica esperando no divisor")
	# a ordem das saídas
	var saidas := [{"lado": "N"}, {"lado": "L"}, {"lado": "O"}]
	igual(f.ordem_saidas(m.div, "carvao", saidas, 0), [0] as Array[int], "filtrado: só a saída do filtro")
	igual(f.ordem_saidas(m.div, "pedra", saidas, 0), [1, 2] as Array[int], "resto: nunca a saída do filtro")
