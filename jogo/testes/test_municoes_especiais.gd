extends Caso
## Munição perfurante (+60%, atravessa 1 aranha), munição carregada (salta para 2 aranhas) e foguete de enxame (abre em 4
## ogivas): itens, receitas da árvore e efeito nas torres. A torre gasta a mais forte primeiro; a comum continua valendo.


func _base() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	for x in range(-38, 40):
		for y in range(-10, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	return [m, c]


func test_receitas_e_pesquisas() -> void:
	igual(Registro.receitas.municao_perfurante.entradas, {"municao": 1.0, "barra_aco": 1.0}, "perfurante")
	igual(Registro.receitas.municao_carregada.entradas, {"municao_perfurante": 1.0, "cristal_carregado": 1.0}, "carregada")
	igual(Registro.receitas.municao_carregada.saidas, {"municao_carregada": 5.0}, "rende 5")
	igual(Registro.receitas.foguete_enxame.entradas, {"foguete": 2.0, "processador": 1.0}, "enxame")
	for par in [["municao_perfurante", "municao_perfurante"], ["municao_cristal", "municao_carregada"], ["foguete_enxame", "foguete_enxame"]]:
		UtilLote11.pesquisa(self, par[0], "")
		var p := Pesquisa.new()
		verificar(not p.receita_liberada(par[1]), "travada: " + par[1])
		p.concluidas[par[0]] = true
		verificar(p.receita_liberada(par[1]), "liberada: " + par[1])
		verificar(ResourceLoader.exists("res://assets/icones/itens/%s.png" % par[1]), "ícone: " + par[1])


func _aranhas_em(c: Colonia, ninho: int, pontos: Array) -> Array:
	var ids := []
	for p in pontos:
		var a := c._nova_aranha(ninho)
		c.aranhas[a].pos = p
		c.aranhas[a].vida = 1000.0
		c.aranhas[a].estado = Colonia.E.PARADA
		ids.append(a)
	return ids


func test_perfurante_atravessa() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var t := m.colocar("torre_metralhadora", Vector2i(0, 0), 0)
	var n := c._criar_ninho(Vector2i(30, 8), 1.0)
	var a := _aranhas_em(c, n, [Vector2(6, 1), Vector2(8, 1), Vector2(14, 1)])
	c.carregar_especial(t, "municao_perfurante")
	igual(int(c.torres[t].especial.municao_perfurante), 10, "1 item = 10 tiros")
	c._listas()
	c._torres(0.01)
	perto(c.aranhas[a[0]].vida, 1000.0 - 3.0 * 1.6, 1e-3, "+60% de dano no alvo")
	perto(c.aranhas[a[1]].vida, 1000.0 - 3.0 * 1.6, 1e-3, "atravessa para a de trás")
	perto(c.aranhas[a[2]].vida, 1000.0, 1e-3, "longe: não")
	igual(int(c.torres[t].especial.municao_perfurante), 9, "gastou 1 tiro especial")
	igual(c.eventos.filter(func(e): return e.tipo == "salto").size(), 1, "desenha o traço")


func test_carregada_salta_em_2() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var t := m.colocar("torre_metralhadora", Vector2i(0, 0), 0)
	var n := c._criar_ninho(Vector2i(30, 8), 1.0)
	var a := _aranhas_em(c, n, [Vector2(6, 1), Vector2(8, 1), Vector2(9, 1), Vector2(9, 3)])
	c.carregar_especial(t, "municao_perfurante")
	c.carregar_especial(t, "municao_carregada")
	c._listas()
	c._torres(0.01)
	perto(c.aranhas[a[0]].vida, 1000.0 - 4.8, 1e-3, "alvo")
	perto(c.aranhas[a[1]].vida, 1000.0 - 2.4, 1e-3, "salto 1, metade")
	perto(c.aranhas[a[2]].vida, 1000.0 - 2.4, 1e-3, "salto 2, metade")
	perto(c.aranhas[a[3]].vida, 1000.0, 1e-3, "só salta para 2")
	igual(int(c.torres[t].especial.municao_carregada), 9, "a mais forte primeiro")
	igual(int(c.torres[t].especial.municao_perfurante), 10, "a outra fica")


func test_cheia_recusa_e_braco_entrega() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var t := m.colocar("torre_metralhadora", Vector2i(0, 0), 0)
	var f := Fabrica.new(m)
	f.torre_receber = func(id: int, k: int) -> void: c.carregar_torre(id, k)
	f.torre_aceita = c.aceita_municao
	f.torre_especial = c.carregar_especial
	f.reconstruir()
	var d: Object = f.destino_em(Vector2i(0, 0))
	verificar(d.aceita("municao") and d.aceita("municao_perfurante") and d.aceita("municao_carregada"), "aceita as 3")
	verificar(not d.aceita("foguete_enxame"), "foguete não")
	verificar(d.receber("municao_perfurante"), "recebe")
	igual(c.tiros_especiais(t), 10, "10 tiros")
	for i in 19:
		d.receber("municao_carregada")
	verificar(not d.aceita("municao"), "200 tiros: cheia")


func test_enxame_abre_em_4() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var t := m.colocar("torre_foguetes", Vector2i(0, 0), 0)
	var n := c._criar_ninho(Vector2i(30, 8), 1.0)
	var a := _aranhas_em(c, n, [Vector2(14, 1), Vector2(17, 1)])
	c.carregar_especial(t, "foguete_enxame")
	c._listas()
	c._torres(0.01)
	igual(c.projeteis.size(), 1, "um foguete no ar")
	verificar(int(c.projeteis[0].ogivas) == 4, "leva 4 ogivas")
	var explosoes := 0
	for i in 200:
		c.eventos.clear()
		c._voar(0.05)
		explosoes += c.eventos.filter(func(e): return e.tipo == "explosao").size()
	igual(explosoes, 5, "abre e as 4 ogivas explodem")
	verificar(c.aranhas[a[1]].vida < 1000.0, "ogiva pegou a aranha a 3 m do ponto")
