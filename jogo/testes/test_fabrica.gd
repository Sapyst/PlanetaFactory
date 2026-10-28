extends Caso
## Simulação do que o jogador constrói: extrator → esteira → braço → baú com energia; sem energia nada anda;
## fornalha escolhe a receita e queima carvão; carga lateral; torre recebe munição; reconstruir guarda os itens.

func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 22):
		for y in range(-8, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot := 0) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


## Gerador com carvão + postes cobrindo a região do extrator e do braço.
func _energia(c: Construtor, f: Fabrica) -> int:
	var g := _por(c, "gerador", Vector2i(8, 6))
	_por(c, "poste_energia", Vector2i(11, 6))
	_por(c, "poste_energia", Vector2i(17, 3))
	_por(c, "poste_energia", Vector2i(17, -2))
	return g


func _rodar(f: Fabrica, s: float) -> void:
	for i in int(s * 30):
		f.tick(1.0 / 30.0)


func _linha_cristal(c: Construtor) -> Array:
	var ext := _por(c, "extrator_cristal", Vector2i(14, 4))
	c.executar(c.plano_linha("esteira", Vector2i(15, 3), Vector2i(15, -1), 0))
	var br := _por(c, "braco", Vector2i(15, -2), 2)
	var bau := _por(c, "bau", Vector2i(15, -3))
	return [ext, br, bau]


func test_cadeia_com_energia() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var g := _energia(c, f)
	var ids := _linha_cristal(c)
	f.reconstruir()
	f.combustivel[g] = 30.0
	igual(f.caminhos.size(), 1, "5 tiles de esteira = 1 caminho")
	var poluiu := {}
	for i in 60 * 30:
		f.tick(1.0 / 30.0)
		for id in f.emissao:
			poluiu[id] = true
	var no_bau := int(f.baus[ids[2]].get("cristal_bruto", 0))
	verificar(no_bau >= 20, "cristal chegou ao baú (%d em 60 s; extrator faz 1 a cada 2 s)" % no_bau)
	verificar(poluiu.has(ids[0]), "extrator trabalhando polui")
	verificar(poluiu.has(g), "gerador queimando polui")
	verificar(f.combustivel[g] < 30.0, "gerador gastou carvão")


func test_sem_energia_nada_anda() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	_energia(c, f)
	var ids := _linha_cristal(c)
	f.reconstruir()                 # gerador sem combustível
	_rodar(f, 20.0)
	igual(f.maquinas[ids[0]].estado, Maquina.Estado.SEM_ENERGIA, "extrator parado sem energia")
	igual(int(f.baus[ids[2]].get("cristal_bruto", 0)), 0)
	verificar(f.emissao.is_empty(), "parado não polui")


func test_fornalha_escolhe_receita_e_queima() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var g := _energia(c, f)
	var forn := _por(c, "fornalha", Vector2i(0, 0))
	var bau := _por(c, "bau", Vector2i(0, -2))
	_por(c, "braco", Vector2i(0, -1), 0)                     # do baú (sul) para a fornalha (norte)
	_por(c, "poste_energia", Vector2i(-2, -1))
	_por(c, "poste_energia", Vector2i(4, 2))
	_por(c, "poste_energia", Vector2i(10, 2))
	c.executar(c.plano_linha("esteira", Vector2i(1, 2), Vector2i(1, 6), 0))   # saída N0 da fornalha
	f.reconstruir()
	f.combustivel[g] = 30.0
	f.baus[bau].merge({"minerio_ferro": 10, "carvao": 3})   # o braço já aponta para este baú
	_rodar(f, 45.0)
	igual(f.maquinas[forn].receita_id, "fundir_ferro", "minério de ferro → receita de placa")
	var placas := 0
	for cm in f.caminhos:
		placas += (cm.esteira as EsteiraCaminho).itens.count("placa_ferro")
	verificar(placas >= 5, "placas saíram pela porta para a esteira (%d)" % placas)
	verificar(f.maquinas[forn].produzidos >= 5)


func test_carga_lateral() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	c.executar(c.plano_linha("esteira", Vector2i(-4, 0), Vector2i(-1, 0), 0))   # leste, termina na lateral
	c.executar(c.plano_linha("esteira", Vector2i(0, -3), Vector2i(0, 4), 0))    # norte
	f.reconstruir()
	igual(f.caminhos.size(), 2)
	var leste: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-4, 0)][0]].esteira
	var norte: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(0, 4)][0]].esteira
	for i in 6:
		leste.inserir_na_entrada("pedra")
		_rodar(f, 0.2)
	_rodar(f, 3.0)
	verificar(norte.itens.count("pedra") >= 4, "itens passaram para a esteira do lado (%d)" % norte.itens.count("pedra"))


func test_torre_recebe_municao_e_reconstruir_guarda_itens() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var g := _energia(c, f)
	var torre := _por(c, "torre_defesa", Vector2i(18, -6))
	var bau := _por(c, "bau", Vector2i(19, -3))
	_por(c, "braco", Vector2i(19, -4), 2)
	var tiros := {"n": 0}
	f.torre_receber = func(_id: int, n: int) -> void: tiros.n += n
	f.reconstruir()
	f.combustivel[g] = 30.0
	f.baus[bau].merge({"municao": 5, "pedra": 3})
	_rodar(f, 10.0)
	igual(tiros.n, 50, "5 munições = 50 tiros na torre")
	igual(int(f.baus[bau].get("pedra", 0)), 3, "braço não pega o que a torre não aceita")
	# itens nas esteiras sobrevivem à remontagem
	c.executar(c.plano_linha("esteira", Vector2i(-4, 3), Vector2i(3, 3), 0))
	f.reconstruir()
	var e: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-4, 3)][0]].esteira
	for i in 5:
		e.inserir_em("pedra", 1.0 + i * 1.2)
	c.executar(c.plano_peca("bau", Vector2i(-4, -5), 0))
	f.reconstruir()
	var e2: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-4, 3)][0]].esteira
	igual(e2.itens.size(), 5, "os 5 itens continuam na esteira depois de construir outra coisa")


func test_ponto_no_tile() -> void:
	# reta: da borda de entrada à de saída
	var a := Fabrica.ponto_no_tile(Vector2i(0, 0), 0, 0, 0.0)
	var b := Fabrica.ponto_no_tile(Vector2i(0, 0), 0, 0, 1.0)
	perto(a.distance_to(Vector2(0.5, 0.0)), 0.0, 1e-5, "entra pelo sul")
	perto(b.distance_to(Vector2(0.5, 1.0)), 0.0, 1e-5, "sai pelo norte")
	# curva norte → leste: arco de raio 0,5 em volta do canto (1, 0)
	var m := Fabrica.ponto_no_tile(Vector2i(0, 0), 0, 1, 0.5)
	perto(m.distance_to(Vector2(1, 0)), 0.5, 1e-4, "meio da curva no arco")
	perto(Fabrica.ponto_no_tile(Vector2i(0, 0), 0, 1, 1.0).distance_to(Vector2(1.0, 0.5)), 0.0, 1e-4, "sai pelo leste")


func test_nucleo_custos_e_pesquisa() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var p := Pesquisa.new()
	c.cobrar = true
	c.pesquisa = p
	c.inventario = {"placa_ferro": 5, "engrenagem": 1}
	f.estoque_nucleo = c.inventario
	f.pesquisa = p
	# esteira custa 1 placa: um traço de 8 só tem 5 verdes
	var pl := c.plano_linha("esteira", Vector2i(-5, 6), Vector2i(2, 6), 0)
	igual(Construtor.contar(pl).ok, 5, "estoque dá para 5 tiles")
	igual(pl[5].motivo, "sem_recursos")
	c.executar(pl)
	igual(int(c.inventario.placa_ferro), 0, "gastou as 5 placas")
	igual(c.plano_peca("torre_defesa", Vector2i(0, 0), 0)[0].motivo, "bloqueado", "torre só depois da pesquisa Defesa")
	# remover devolve; desfazer a remoção volta a cobrar
	c.executar(c.plano_remocao(Vector2i(-5, 6), Vector2i(-4, 6)))
	igual(int(c.inventario.placa_ferro), 2, "duas esteiras devolvidas")
	c.desfazer()
	igual(int(c.inventario.placa_ferro), 0, "desfazer a remoção cobra de novo")
	# limpar obstáculo rende material
	var t := Vector2i(9999, 9999)
	for x in range(8, 40):
		var o := c.mapa.gerador.distribuicao.obstaculo(Vector2i(x, 20))
		if not o.is_empty() and Registro.progressao.drops.has(o.nome):
			t = Vector2i(x, 20)
			break
	var antes := c.inventario.duplicate()
	c.executar(c.plano_remocao(t, t))
	verificar(c.inventario.hash() != antes.hash(), "limpar %s rendeu itens (%s)" % [t, c.inventario])
	# núcleo recebe da esteira; laboratório pesquisa com pacotes
	c.inventario["placa_ferro"] = 100
	c.inventario["placa_cobre"] = 100
	c.inventario["engrenagem"] = 100
	var nuc := c.mapa.colocar("nucleo", Vector2i(10, -6), 0)        # boca oeste no tile (10, −5) → esteira em (9, −5)
	c.executar(c.plano_linha("esteira", Vector2i(4, -5), Vector2i(9, -5), 0))
	var lab := c.mapa.colocar("laboratorio", Vector2i(-4, -6), 0)
	_energia(c, f)
	_por(c, "poste_energia", Vector2i(-3, -3))       # cobre o laboratório (centro a 2 tiles)
	_por(c, "poste_energia", Vector2i(2, -1))
	_por(c, "poste_energia", Vector2i(8, 1))
	f.reconstruir()
	for id in f.combustivel: f.combustivel[id] = 30.0
	var e: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(4, -5)][0]].esteira
	for i in 4:
		e.inserir_em("pedra", 5.5 - i * 0.5)
	_rodar(f, 6.0)
	igual(int(c.inventario.get("pedra", 0)), 4, "4 pedras entraram no núcleo pela boca oeste")
	p.escolher("defesa")
	f.laboratorios[lab].pacotes = 8
	var feito := false
	for i in 30 * 60:
		f.tick(1.0 / 30.0)
		if "defesa" in f.concluidas: feito = true
	verificar(feito, "laboratório concluiu Defesa com 8 pacotes")
	igual(c.plano_peca("torre_defesa", Vector2i(0, 0), 0)[0].motivo, "", "torre liberada")
	verificar(nuc > 0)


func test_fabrica_salva_e_carrega() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var g := _energia(c, f)
	var ids := _linha_cristal(c)
	f.reconstruir()
	f.combustivel[g] = 30.0
	_rodar(f, 15.0)
	var texto := var_to_str({"mapa": c.mapa.estruturas.duplicate(true), "fab": f.estado()})
	var d: Dictionary = str_to_var(texto)
	var m2 := MapaOcupacao.new(c.mapa.gerador)
	m2.restaurar(d.mapa, c.mapa.limpos.keys(), c.mapa._prox_id)
	var f2 := Fabrica.new(m2)
	f2.restaurar(d.fab)
	igual(f2.baus[ids[2]], f.baus[ids[2]], "baú igual")
	igual(f2.caminhos[0].esteira.itens.size(), f.caminhos[0].esteira.itens.size(), "mesmos itens na esteira")
	perto(f2.combustivel[g], f.combustivel[g], 1e-6, "mesmo combustível")
	igual(f2.maquinas[ids[0]].produzidos, f.maquinas[ids[0]].produzidos)
	_rodar(f2, 10.0)
	verificar(int(f2.baus[ids[2]].get("cristal_bruto", 0)) > int(f.baus[ids[2]].get("cristal_bruto", 0)), "a fábrica carregada continua produzindo")


func test_divisor_e_juncao() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	# esteira norte até o divisor em (0, 0); saídas norte, leste e oeste
	c.executar(c.plano_linha("esteira", Vector2i(0, -5), Vector2i(0, -1), 0))
	c.executar(c.plano_peca("divisor", Vector2i(0, 0), 0))     # pelo construtor: o fim da esteira vira reta
	c.executar(c.plano_linha("esteira", Vector2i(0, 1), Vector2i(0, 4), 0))
	c.executar(c.plano_linha("esteira", Vector2i(1, 0), Vector2i(4, 0), 0))
	c.executar(c.plano_linha("esteira", Vector2i(-1, 0), Vector2i(-4, 0), 0))
	f.reconstruir()
	var ent: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(0, -5)][0]].esteira
	for i in 30 * 20:
		if i % 10 == 0:
			ent.inserir_na_entrada("pedra")
		f.tick(1.0 / 30.0)
	var n: int = f.caminhos[f._no_tile[Vector2i(0, 4)][0]].esteira.itens.size()
	var l: int = f.caminhos[f._no_tile[Vector2i(4, 0)][0]].esteira.itens.size()
	var o: int = f.caminhos[f._no_tile[Vector2i(-4, 0)][0]].esteira.itens.size()
	verificar(n > 0 and l > 0 and o > 0, "divisor reparte nas 3 saídas (%d, %d, %d)" % [n, l, o])
	verificar(absi(n - l) <= 2 and absi(l - o) <= 2, "em partes iguais")
	# junção: duas esteiras (sul e leste) viram uma
	var c2 := _c()
	var f2 := Fabrica.new(c2.mapa)
	c2.executar(c2.plano_linha("esteira", Vector2i(0, -4), Vector2i(0, -1), 0))
	c2.executar(c2.plano_linha("esteira", Vector2i(4, 0), Vector2i(1, 0), 0))
	c2.executar(c2.plano_peca("juncao", Vector2i(0, 0), 0))
	c2.executar(c2.plano_linha("esteira", Vector2i(0, 1), Vector2i(0, 8), 0))
	f2.reconstruir()
	var a: EsteiraCaminho = f2.caminhos[f2._no_tile[Vector2i(0, -4)][0]].esteira
	var b: EsteiraCaminho = f2.caminhos[f2._no_tile[Vector2i(4, 0)][0]].esteira
	for i in 30 * 6:
		if i % 15 == 0:
			a.inserir_na_entrada("pedra")
			b.inserir_na_entrada("carvao")
		f2.tick(1.0 / 30.0)
	var saida: EsteiraCaminho = f2.caminhos[f2._no_tile[Vector2i(0, 8)][0]].esteira
	verificar(saida.itens.has("pedra") and saida.itens.has("carvao"), "junção juntou as duas (%s)" % str(saida.itens))


func test_bomba_cano_refinador() -> void:
	var c := Construtor.new(MapaOcupacao.new(GeradorMundo.new(1337)))
	var m := c.mapa
	# acha uma poça de seiva com terra seca em volta para o arranjo
	var bomba := Vector2i(99999, 0)
	for r in range(40, 400, 3):
		for k in 64:
			var t := Vector2i((Vector2.from_angle(k * TAU / 64) * r).round())
			var j := m.gerador.distribuicao.jazida(t)
			if j.is_empty() or j.tipo != "poca_seiva":
				continue
			for x in range(-2, 8):
				for y in range(-2, 8):
					m.limpar_obstaculo(t + Vector2i(x, y))
			if m.motivo_bloqueio("bomba", t, 0) == "" and m.motivo_bloqueio("refinador", t + Vector2i(2, 3), 0) == "":
				bomba = t
				break
		if bomba.x != 99999:
			break
	if not verificar(bomba.x != 99999, "achou poça de seiva com espaço"):
		return
	var bid := _por(c, "bomba", bomba, 0)                                   # sai pelo norte
	c.executar(c.plano_linha("cano", bomba + Vector2i(0, 1), bomba + Vector2i(1, 4), 0))
	var ref := _por(c, "refinador", bomba + Vector2i(2, 3), 0)               # entra pelo oeste (meio)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	f._membros.clear()                        # teste sem postes: máquinas com energia cheia
	igual(f.redes_fluido.size(), 1, "os canos formam uma rede")
	igual(f._ligacoes_fluido.size(), 2, "bomba e refinador ligados a ela")
	f.escolher_receita(ref, "bateria")
	var rm: Maquina = f.maquinas[ref]
	for i in 4:
		rm.receber("placa_cobre")
		rm.receber("placa_ferro")
	_rodar(f, 20.0)
	verificar(f.maquinas[bid].produzidos > 5, "bomba bombeou (%d)" % f.maquinas[bid].produzidos)
	verificar(rm.produzidos >= 2, "refinador fez bateria com seiva + placas (%d)" % rm.produzidos)
	var rede := f.rede_de(m.tiles[bomba + Vector2i(0, 1)])
	igual(rede.fluido, "seiva")
	# fluido sobrevive à remontagem
	var antes: float = rede.qtd
	c.executar(c.plano_peca("bau", bomba + Vector2i(-2, -2), 0))
	f.reconstruir()
	perto(f.rede_de(m.tiles[bomba + Vector2i(0, 1)]).qtd, antes, 0.01, "seiva continua nos canos")


func test_esteira_elevada_com_rampas() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	# no chão, uma esteira norte–sul atravessa o caminho em x = 0; um baú (0,62 m) fica em (2, 3)
	c.executar(c.plano_linha("esteira", Vector2i(0, -4), Vector2i(0, 4), 0))
	_por(c, "bau", Vector2i(2, 3))
	# leste: chão → rampa ↑ → elevada a 0,5 m por cima → rampa ↓ → chão
	c.executar(c.plano_linha("esteira", Vector2i(-6, 0), Vector2i(-3, 0), 0))
	var r1 := c.plano_peca("esteira_rampa", Vector2i(-2, 0), Construtor.rot_do_fluxo(1))
	igual(r1[0].motivo, "", "rampa de subida no chão")
	c.executar(r1)
	c.nivel = 1
	var alto := c.plano_linha("esteira", Vector2i(-1, 0), Vector2i(3, 0), 0)
	verificar(Construtor.pode_tudo(alto), "esteira elevada passa sobre a esteira de baixo (%s)" % str(alto.map(func(i): return i.motivo)))
	igual(c.plano_linha("esteira", Vector2i(2, 2), Vector2i(2, 4), 0)[1].motivo, "estrutura_alta_embaixo", "a 0,5 m não passa sobre o baú")
	var pilares := 0
	for it in alto:
		pilares += it.get("pilares", []).size()
	verificar(pilares >= 2, "o traço elevado ganhou pilares (%d)" % pilares)
	c.executar(alto)
	var r2 := c.plano_peca("rampa_desce", Vector2i(4, 0), Construtor.rot_do_fluxo(1))
	igual(r2[0].motivo, "", "rampa de descida no fim do trecho alto")
	c.executar(r2)
	c.nivel = 0
	c.executar(c.plano_linha("esteira", Vector2i(5, 0), Vector2i(9, 0), 0))
	igual(c.plano_peca("fornalha", Vector2i(0, 0), 0)[0].motivo, "ocupado")
	igual(c.plano_peca("montadora", Vector2i(2, 1), 0)[0].motivo, "esteira_em_cima", "máquina alta não cabe debaixo da elevada")
	f.reconstruir()
	var ent: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-6, 0)][0]].esteira
	igual(f._no_tile[Vector2i(-6, 0)][0], f._no_tile[Vector2i(9, 0)][0], "chão, rampa, alto, rampa e chão = um caminho só")
	var cruz: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(0, -4)][0]].esteira
	verificar(cruz != ent, "a esteira de baixo é outro caminho")
	for i in 6:
		ent.inserir_na_entrada("pedra")
		_rodar(f, 0.3)
	_rodar(f, 10.0)
	var c_fim: Dictionary = f.caminhos[f._no_tile[Vector2i(9, 0)][0]]
	var alturas := []
	for p in ent.posicoes():
		alturas.append(f.altura_do_item(c_fim, p))
	igual(ent.itens.size(), 6, "os 6 itens atravessaram por cima e chegaram ao fim")
	igual(cruz.itens.size(), 0, "nada caiu na esteira de baixo")
	# remover um tile elevado leva os pilares dele; desfazer devolve
	var antes := c.mapa.estruturas.size()
	c.executar(c.plano_remocao(Vector2i(-1, 0), Vector2i(-1, 0)))
	verificar(c.mapa.estruturas.size() < antes, "removeu esteira elevada (e pilares)")
	c.desfazer()
	igual(c.mapa.estruturas.size(), antes, "desfazer devolve esteira e pilares")
