extends Caso
## Metralhadora (torre_metralhadora, fase 2.2a): modelo vindo do estudo (arte/estudos/conv_combate.py), pesquisa
## jogável pela árvore (defesa + aço), tiro só com munição trazida por braço (até municao_max), 10 tiros/s,
## melhorias dano_bala / cadencia_bala, e o desenho: tambor girando na rajada e cápsula ejetada a cada tiro.


func _base() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var p := Poluicao.new(m.gerador)
	var c := Colonia.new(m, p, 3)
	for x in range(-38, 37):
		for y in range(-6, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return [m, p, c]


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("torre_metralhadora", {})
	igual(r.get("grupo", ""), "defesa", "grupo defesa")
	perto(float(r.get("cadencia", 0)), 10.0, 1e-6, "10 tiros/s (árvore)")
	perto(float(r.get("alcance", 0)), 18.0, 1e-6, "alcance 18 m (árvore)")
	verificar(not r.has("energia_kw") and not r.has("carga_mj"), "não usa energia: só bala")
	var md: Dictionary = Registro.modelos.get("torre_metralhadora", {})
	igual(Registro.area("torre_metralhadora"), Vector2i(2, 2), "2×2")
	igual(md.get("estudo", ""), "estudo_metralhadora.py", "convertida do estudo")
	var partes := {}
	for p in md.get("partes", []):
		partes[p.nome] = p.pai
	igual(partes.get("giro"), "base", "giro na base")
	igual(partes.get("canhao"), "giro", "canhão no giro")
	igual(partes.get("tambor"), "canhao", "tambor no canhão")
	var eixo: Array = md.get("eixo_tambor", [])
	verificar(eixo.size() == 3 and float(eixo[1]) > 0.98, "tambor gira no eixo dos canos (para +Y do Blender)")
	verificar(md.has("ejecao") and md.has("vel_ejecao"), "calha de cápsulas no modelo")
	verificar(Registro.modelos.torre_defesa.has("ejecao"), "torre de energia também ejeta cápsula")
	var portas: Array = md.get("portas", [])
	verificar(portas.size() == 1 and portas[0].io == "ENT" and portas[0].tipo == "ITEM", "munição entra pela porta sul")
	verificar(ResourceLoader.exists("res://assets/icones/torre_metralhadora.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return "torre_metralhadora" in cat.pecas), "está no menu (Defesa)")
	var custo: Dictionary = Registro.progressao.custos.get("torre_metralhadora", {})
	verificar(not custo.is_empty(), "tem custo de construção")
	var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
	for p in ["base", "giro", "canhao", "tambor"]:
		verificar(cena.find_child("torre_metralhadora_" + p, true, false) != null, "nó da parte " + p)
	cena.free()


func test_pesquisa_pela_arvore() -> void:
	var p := Pesquisa.new()
	for id in ["torre_metralhadora", "dano_bala_1", "cadencia_bala_1", "dano_bala_2"]:
		verificar(p.jogavel(id), "jogável: " + id)
	verificar(not p.peca_liberada("torre_metralhadora"), "travada no início")
	p.concluidas = {"defesa": true}
	verificar(not p.disponivel("torre_metralhadora"), "precisa de aço também")
	p.concluidas = {"defesa": true, "aco": true}
	verificar(p.disponivel("torre_metralhadora"), "defesa + aço: dá para pesquisar")
	p.concluidas["torre_metralhadora"] = true
	verificar(p.peca_liberada("torre_metralhadora"), "pesquisa libera a peça")
	verificar(p.disponivel("dano_bala_1") and p.disponivel("cadencia_bala_1"), "melhorias da bala abertas")
	verificar(not p.disponivel("dano_bala_2"), "dano 2 espera automação e dano 1")
	p.concluidas.merge({"dano_bala_1": true, "cadencia_bala_1": true})
	perto(p.bonus("dano_bala"), 0.1, 1e-6, "dano 1: +10%")
	perto(p.bonus("cadencia_bala"), 0.1, 1e-6, "cadência 1: +10%")
	p.concluidas.merge({"logistica": true, "eletronica": true, "automacao": true})
	verificar(p.disponivel("dano_bala_2"), "dano 2 com automação")
	igual(p.tipos("dano_bala_2"), ["pacote_pesquisa", "pacote_automacao"], "dano 2 gasta pacote de automação")
	p.concluidas["dano_bala_2"] = true
	perto(p.bonus("dano_bala"), 0.25, 1e-6, "dano 1 + 2: +25%")
	verificar(not p.jogavel("dano_bala_3") and not p.jogavel("ciencia_militar"), "dano 3 / ciência militar ficam para a 2.4")
	# munição já sai da pesquisa "defesa" (2 sílex + 1 placa de cobre na montadora)
	var r: Dictionary = Registro.receitas.municao
	igual(r.maquina, "montadora", "munição na montadora")
	igual(r.entradas, {"silex": 2.0, "placa_cobre": 1.0}, "receita da árvore")
	verificar(ResourceLoader.exists("res://assets/icones/itens/municao.png"), "ícone da munição")


func _tiros(c: Colonia, segundos: float, fontes: Array[Dictionary] = []) -> Array:
	var tiros: Array = []
	for i in int(segundos * 30):
		c.tick(1.0 / 30.0, fontes)
		for e in c.eventos:
			if e.tipo == "tiro":
				tiros.append(e)
	return tiros


func test_atira_so_com_municao() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[2]
	var ninho := c._criar_ninho(Vector2i(14, 0), 1.0)
	var t := m.colocar("torre_metralhadora", Vector2i(0, 0), 0)
	verificar(t >= 0, "coube")
	c.torre_energia = func(_id: int, _mj: float) -> bool: return true     # energia não serve para ela
	var vida0: float = c.ninhos[ninho].vida
	igual(_tiros(c, 1.0).size(), 0, "sem munição (começa vazia), sem tiro")
	c.carregar_torre(t, 50)
	var tiros := _tiros(c, 2.0)
	verificar(tiros.size() >= 19 and tiros.size() <= 21, "10 tiros/s (%d em 2 s)" % tiros.size())
	verificar(tiros.all(func(e): return e.bala and e.nome == "torre_metralhadora"), "todo tiro é bala (ejeta cápsula)")
	igual(c.torres[t].municao, 50 - tiros.size(), "cada tiro gasta um")
	perto(vida0 - c.ninhos[ninho].vida, 3.0 * tiros.size(), 1e-3, "3 de dano por bala")


func test_derruba_aranhas() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[2]
	var fonte := m.colocar("fornalha", Vector2i(-34, 0), 0)
	var ninho := c._criar_ninho(Vector2i(30, 0), 1.0)
	var t := m.colocar("torre_metralhadora", Vector2i(-28, 0), 0)
	c.carregar_torre(t, 200)
	for k in 4:
		var a := c._nova_aranha(ninho)
		c.aranhas[a].estado = Colonia.E.ATACANDO
		c.aranhas[a].alvo = fonte
	var fontes: Array[Dictionary] = [{"id": fonte, "pos": Vector2(-33, 1)}]
	var mortas := 0
	for i in 30 * 90:
		c.tick(1.0 / 30.0, fontes)
		for e in c.eventos:
			if e.tipo == "aranha_morta": mortas += 1
	igual(mortas, 4, "metralhadora matou as 4")
	verificar(m.estruturas.has(fonte), "a fornalha sobreviveu")


func test_melhorias_de_bala() -> void:
	var res := []
	for bon in [0.0, 0.25]:
		var b := _base()
		var m: MapaOcupacao = b[0]
		var c: Colonia = b[2]
		var ninho := c._criar_ninho(Vector2i(14, 0), 1.0)
		var t := m.colocar("torre_metralhadora", Vector2i(0, 0), 0)
		c.bonus = func(chave: String) -> float: return bon if chave in ["dano_bala", "cadencia_bala"] else 0.0
		c.carregar_torre(t, 200)
		var v0: float = c.ninhos[ninho].vida
		var n := _tiros(c, 4.0).size()
		res.append([n, (v0 - c.ninhos[ninho].vida) / n])
	verificar(res[1][0] > res[0][0] * 1.15, "cadência +25%%: mais tiros (%d → %d)" % [res[0][0], res[1][0]])
	perto(res[1][1], res[0][1] * 1.25, 1e-3, "dano +25% por bala")
	# a torre de energia não ganha cadência de bala
	var b := _base()
	var c2: Colonia = b[2]
	b[0].colocar("torre_defesa", Vector2i(0, 0), 0)
	c2._criar_ninho(Vector2i(14, 0), 1.0)
	c2.torre_energia = func(_id: int, _mj: float) -> bool: return true
	c2.bonus = func(chave: String) -> float: return 1.0 if chave == "cadencia_bala" else 0.0
	var tiros := _tiros(c2, 2.0)
	verificar(tiros.size() <= 7, "torre de energia segue 3 tiros/s (%d em 2 s)" % tiros.size())
	verificar(tiros.all(func(e): return not e.bala), "tiro de energia não é bala")


func test_braco_abastece_ate_encher() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 22):
		for y in range(-8, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	var con := Construtor.new(m)
	var col := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var f := Fabrica.new(m)
	var g := m.colocar("gerador", Vector2i(8, 6), 0)
	for t in [Vector2i(11, 6), Vector2i(17, 3), Vector2i(17, -2)]:
		m.colocar("poste_energia", t, 0)
	var torre := m.colocar("torre_metralhadora", Vector2i(18, -6), 0)
	var bau := m.colocar("bau", Vector2i(19, -3), 0)
	verificar(torre >= 0 and bau >= 0 and m.colocar("braco", Vector2i(19, -4), 2) >= 0, "montagem")
	f.torre_receber = func(id: int, n: int) -> void: col.carregar_torre(id, n)
	f.torre_aceita = col.aceita_municao
	f.reconstruir()
	f.combustivel[g] = 30.0
	f.baus[bau].merge({"municao": 30, "pedra": 3})
	for i in 30 * 40:
		f.tick(1.0 / 30.0)
	var maximo := int(Registro.estruturas.torre_metralhadora.municao_max)
	igual(int(col.torres[torre].municao), maximo, "encheu até %d tiros" % maximo)
	igual(int(f.baus[bau].get("municao", 0)), 30 - maximo / Fabrica.TIROS_POR_MUNICAO, "o resto ficou no baú")
	igual(int(f.baus[bau].get("pedra", 0)), 3, "braço não leva o que a torre não aceita")
	col.torres[torre].municao = 0                 # gastou tudo atirando: o braço volta a trazer
	for i in 30 * 10:
		f.tick(1.0 / 30.0)
	verificar(int(col.torres[torre].municao) > 0, "vazia, volta a receber")
	verificar(con != null)


# ------------------------------------------------------------------ desenho
func _raiz() -> Node:
	return (Engine.get_main_loop() as SceneTree).root


func test_tambor_e_capsula() -> void:
	var md: Dictionary = Registro.modelos.torre_metralhadora
	var n: Node3D = (load(md.modelo) as PackedScene).instantiate()
	_raiz().add_child(n)
	var a := Animador.new()
	a.modelo = "torre_metralhadora"
	n.add_child(a)
	if not a.is_inside_tree():
		a._ready()
	# cápsula sai pela calha (lado direito do canhão), com o giro em 0
	var ej := a.ejecao()
	if not verificar(ej.size() == 2, "ejeção do modelo"):
		n.queue_free()
		return
	var e: Array = md.ejecao
	var esperado := Vector3(e[0], e[2], -e[1])
	perto((ej[0] as Vector3).distance_to(esperado), 0.0, 0.01, "ponto da calha no mundo")
	verificar((ej[1] as Vector3).x > 0.5, "cápsula sai para a direita da arma (%s)" % str(ej[1]))
	# girou a cabeça 90° (mira para −X): a calha gira junto
	a._gira("giro", PI * 0.5)
	var ej2 := a.ejecao()
	verificar((ej2[1] as Vector3).z < -0.5, "com a mira girada a cápsula sai para o lado novo (%s)" % str(ej2[1]))
	# tambor: parado sem tiro; na rajada gira no próprio eixo
	var tam := n.find_child("torre_metralhadora_tambor", true, false) as Node3D
	var b0 := tam.transform
	a._girar_tambor(0.1)
	verificar(tam.transform.is_equal_approx(b0), "sem tiro o tambor fica parado")
	a.rajada = 0.25
	for i in 6:
		a._girar_tambor(0.05)
	verificar(not tam.transform.basis.is_equal_approx(b0.basis), "na rajada o tambor gira")
	var eixo := Vector3(md.eixo_tambor[0], md.eixo_tambor[2], -md.eixo_tambor[1]).normalized()
	perto((tam.transform.basis * eixo).distance_to(b0.basis * eixo), 0.0, 1e-3, "gira em volta do eixo dos canos")
	verificar(tam.transform.origin.is_equal_approx(b0.origin), "sem sair do lugar")
	# desenho da colônia: cada tiro gira o tambor e ejeta uma cápsula, que cai, quica, para e some
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var dc := DesenhoColonia.new()
	dc.mapa = m
	dc.colonia = Colonia.new(m, Poluicao.new(m.gerador), 3)
	dc.animadores_torre = func(_id: int) -> Animador: return a
	_raiz().add_child(dc)
	if not dc.is_inside_tree():
		dc._ready()
	a.rajada = 0.0
	dc._cartucho({"tipo": "tiro", "torre": 7, "nome": "torre_metralhadora", "bala": true, "de": Vector2.ZERO, "para": Vector2(10, 0)})
	igual(dc.capsulas(), 1, "uma cápsula por tiro")
	verificar(a.rajada > 0.0, "tiro acende a rajada do tambor")
	verificar(dc._fumacinhas.has(7), "calha solta fumacinha")
	var chao := Grade.ponto_mundo(Vector2.ZERO).y + DesenhoColonia.LAJE
	var parou := false
	for i in 30:
		dc._mover_capsulas(1.0 / 30.0)
	var c: Dictionary = dc._capsulas[0]
	verificar(c.parada, "parou no chão em 1 s")
	perto(c.p.y, chao + DesenhoColonia.RAIO_CAPSULA, 1e-4, "deitada na laje")
	parou = c.parada
	for i in 60:
		dc._mover_capsulas(1.0 / 30.0)
	igual(dc.capsulas(), 0, "e some depois de %.1f s" % DesenhoColonia.VIDA_CAPSULA)
	verificar(parou)
	for k in DesenhoColonia.MAX_CAPSULAS + 20:
		dc.ejetar_capsula(Vector3(0, 1, 0), Vector3.ZERO, 0.0)
	igual(dc.capsulas(), DesenhoColonia.MAX_CAPSULAS, "no máximo %d cápsulas de uma vez" % DesenhoColonia.MAX_CAPSULAS)
	dc.queue_free()
	n.queue_free()
