extends Caso
## Fornalha elétrica (fornalha_eletrica, lote 10 — produção I): modelo do estudo (estudo_fornalha_eletrica.py, do
## Antigravity; arte/estudos/conv_lote10.py) com eletrodos, lingotes e cristal; pesquisa fornalha_eletrica (fornalha de
## aço + química; 3 pacotes × 50, 8 s). As mesmas receitas da fornalha, velocidade 2,0, sem combustível (só energia),
## sem poluição direta (nem fumaça, nem despejo, nem fogo em volta) e 2 encaixes de módulo.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("fornalha_eletrica", {})
	igual(r.get("maquina", ""), "fornalha", "faz as receitas da fornalha")
	perto(float(r.velocidade), 2.0, 1e-6, "velocidade 2,0 (árvore)")
	verificar(not r.has("combustivel"), "sem combustível (árvore)")
	verificar(float(r.energia_kw) > 0.0, "usa energia")
	igual(float(r.get("poluicao", 0.0)), 0.0, "sem poluição direta")
	igual(int(r.encaixes_modulo), 2, "2 encaixes de módulo (árvore)")
	igual(Fiacao.papel("fornalha_eletrica"), "consumo", "precisa de energia")
	var amb: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://dados/ambiente.json"))
	verificar(not amb.despejo.has("fornalha_eletrica"), "não despeja na água")
	verificar(not "fornalha_eletrica" in amb.fogo.maquinas_quentes, "não acende a vegetação seca")
	var md: Dictionary = Registro.modelos.get("fornalha_eletrica", {})
	igual(Registro.area("fornalha_eletrica"), Vector2i(2, 2), "2×2 (como a fornalha)")
	igual(md.get("estudo", ""), "estudo_fornalha_eletrica.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	verificar(float(md.dims[0]) <= 2.1 and float(md.dims[1]) <= 2.1, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 7000, "no nível da fornalha (%d triângulos; o estudo tem 5.796)" % md.tris)
	var bocas := {}
	for p in md.get("portas", []):
		bocas[p.nome] = p
	for n in ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_SAI_N0", "PORTA_FLUIDO_ENT_O1"]:
		verificar(bocas.has(n), "boca %s (do estudo)" % n)
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/fornalha_eletrica.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Produção" and "fornalha_eletrica" in cat.pecas), "no menu (Produção)")
	verificar(not Registro.progressao.custos.get("fornalha_eletrica", {}).is_empty(), "custo de construção")


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 12):
		for y in range(-4, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


## Com gerador e poste: funde pela escolha do que chega, sem carvão, sem emissão; sem rede, para.
func test_funciona_so_com_energia() -> void:
	var m := _mapa()
	var ge := m.colocar("gerador", Vector2i(4, 0), 0)
	m.colocar("poste_energia", Vector2i(3, 2), 0)
	var b := m.colocar("fornalha_eletrica", Vector2i(0, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[ge] = 40.0
	verificar(f.maquinas.has(b), "é máquina de receita")
	verificar(not f.combustivel.has(b), "sem estoque de fogo")
	var d: Object = f.destino_em(Vector2i(0, 0))
	verificar(not d.aceita("carvao"), "recusa carvão como combustível (não é receita)")
	verificar(d.receber("minerio_ferro"), "recebe minério sem receita escolhida")
	igual(f.maquinas[b].receita_id, "fundir_ferro", "a receita sai do que chegou")
	var mq: Maquina = f.maquinas[b]
	var n := 0
	var emitiu := 0.0
	for i in 64:
		while mq.receber("minerio_ferro"):
			pass
		f.tick(0.25)
		emitiu += float(f.emissao.get(b, 0.0))
		n += int(mq.saidas.get("placa_ferro", 0))
		mq.saidas.erase("placa_ferro")
		mq.acordar()
	verificar(n >= 8, "em 16 s fez %d placas, sem carvão (a fornalha faz 5)" % n)
	igual(emitiu, 0.0, "nenhuma emissão (sem fumaça nem sujeira)")
	perto(f.kw_de(b), float(Registro.estruturas.fornalha_eletrica.energia_kw), 1e-6, "puxa a energia da regra")


func test_sem_energia_para() -> void:
	var m := _mapa()
	var b := m.colocar("fornalha_eletrica", Vector2i(0, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.escolher_receita(b, "fundir_ferro")
	var mq: Maquina = f.maquinas[b]
	mq.receber("minerio_ferro")
	f.tick(0.5)
	igual(mq.energia, 0.0, "sem rede, não trabalha")
	verificar(mq.estado != Maquina.Estado.TRABALHANDO, "parada")
	var p := 0.0
	for i in 8:
		f.tick(0.5)
		p = maxf(p, mq.progresso)
	igual(p, 0.0, "e não avança")


## O que depende dela: a fundição de cristal segue em desenvolvimento (sem estudo no jogo).
func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("fornalha_eletrica"), "Fornalha elétrica ligada no jogo")
	verificar(not p.em_desenvolvimento("fornalha_eletrica"), "fora do em desenvolvimento")
	igual(p.custo("fornalha_eletrica"), {"pacote_pesquisa": 50, "pacote_automacao": 50, "pacote_quimico": 50}, "custo da árvore")
	verificar(not p.peca_liberada("fornalha_eletrica"), "começa travada")
	p.concluidas = {"quimica": true}
	verificar(not p.disponivel("fornalha_eletrica"), "pede a fornalha de aço")
	p.concluidas["fornalha_aco"] = true
	verificar(p.disponivel("fornalha_eletrica"), "com fornalha de aço e química: pesquisável")
	p.concluidas["fornalha_eletrica"] = true
	verificar(p.peca_liberada("fornalha_eletrica"), "libera a fornalha elétrica")
	verificar(not Pesquisa.new().peca_em_desenvolvimento("fornalha_eletrica"), "a peça não fica em cinza")
