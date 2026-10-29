extends Caso
## Árvores por receita: espécie + variação no sorteio do mapa, dados completos, fogo em etapas (queimada de pé ou
## caída vento abaixo), o que rende ao tirar e a rebrota na primavera.

const ESPECIES := ["arv_carvalho", "arv_betula", "arv_pinheiro", "arv_salgueiro", "arv_acacia", "arv_fungo_cristal"]


func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	return [g, m, Fabrica.new(m), AmbienteVivo.new(g, m, 3)]


## Primeira árvore por receita numa varredura em volta de (-78, -30) (bosque de campina da semente 1337).
func _uma_arvore(g: GeradorMundo) -> Vector2i:
	for y in range(-40, -10):
		for x in range(-90, -60):
			var o := g.distribuicao.obstaculo(Vector2i(x, y))
			if not o.is_empty() and str(o.nome).begins_with("arv_"):
				return Vector2i(x, y)
	return Vector2i(9999, 9999)


func test_especie_e_variacao() -> void:
	igual(Distribuicao.especie("arv_carvalho_3"), "arv_carvalho", "tira a variação")
	igual(Distribuicao.especie("arv_fungo_cristal_6"), "arv_fungo_cristal", "nome com _ no meio")
	igual(Distribuicao.especie("arbusto"), "arbusto", "outros nomes ficam")
	verificar(Distribuicao.eh_arvore("arv_pinheiro_2") and Distribuicao.eh_arvore("arvore_morta"), "árvores")
	verificar(not Distribuicao.eh_arvore("arbusto"), "arbusto não é árvore")
	var g := GeradorMundo.new(1337)
	var vistas := {}
	for y in range(-120, 120, 3):
		for x in range(-120, 120, 3):
			var o := g.distribuicao.obstaculo(Vector2i(x, y))
			if not o.is_empty() and str(o.nome).begins_with("arv_"):
				vistas[o.nome] = true
				verificar(Registro.modelos.has(o.nome), "modelo %s existe" % o.nome)
	verificar(vistas.size() >= 12, "o mapa tem muitas variações (%d)" % vistas.size())


func test_dados_de_cada_especie() -> void:
	var mad: Dictionary = Registro.ambiente.fogo.madeira
	for e in ESPECIES:
		verificar(Registro.progressao.drops.has(e), "%s rende algo" % e)
		verificar(Registro.recursos.elementos.has(e), "%s tem nome" % e)
		verificar(mad.has(e), "%s queima" % e)
		for n in range(1, Distribuicao.VARIACOES_ARVORE + 1):
			verificar(Registro.modelos.has("%s_%d" % [e, n]), "%s_%d existe" % [e, n])
	for k in ["arvore_queimada", "tronco_caido"]:
		verificar(Registro.progressao.drops[k].has("carvao"), "%s rende carvão" % k)


func test_fogo_curto_deixa_de_pe_queimada() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var a: AmbienteVivo = b[3]
	var t := _uma_arvore(g)
	verificar(t.x != 9999, "achou árvore")
	a.fogo[t] = 6.0
	for i in 10:
		a.tick(1.0, b[2], null)
	verificar(not a.fogo.has(t), "fogo apagou")
	igual(m.arvores.get(t, {}).get("e", ""), "queimada", "ficou de pé, carbonizada")
	verificar(not m.limpos.has(t), "continua bloqueando o tile")
	var o := m.limpar_obstaculo(t)
	igual(o.get("estado", ""), "queimada", "ao tirar, sabe que estava queimada")
	verificar(MapaOcupacao.drops_de(o).has("carvao"), "rende carvão")
	verificar(not m.arvores.has(t), "estado sai junto")


func test_fogo_longo_derruba_vento_abaixo() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var a: AmbienteVivo = b[3]
	var t := _uma_arvore(g)
	a.fogo[t] = 30.0
	var c := Clima.new(4)
	c.forcar("limpo", true)
	var caiu := {}
	for i in 40:
		a.tick(1.0, b[2], c)
		for ev in a.eventos:
			if ev.tipo == "arvore_caiu":
				caiu = ev
		a.eventos.clear()
	igual(m.arvores.get(t, {}).get("e", ""), "caida", "fogo longo derrubou")
	verificar(not caiu.is_empty() and caiu.tile == t, "avisou o mundo (animação)")
	var dir: Vector2 = m.arvores[t].dir
	verificar(dir.dot(c.direcao_vento) > 0.6, "caiu a favor do vento")
	igual(MapaOcupacao.drops_de({"nome": "x", "estado": "caida"}), Registro.progressao.drops.tronco_caido, "tronco caído rende carvão")


func test_nao_cai_em_cima_de_construcao() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var a: AmbienteVivo = b[3]
	var t := _uma_arvore(g)
	var v := Vector2.RIGHT
	for k in [1, 2]:
		var tt := t + Vector2i(k, 0)
		m.limpar_obstaculo(tt)
		m.colocar("muro_centro", tt, 0)
	var d := a._rumo_queda(t, v)
	verificar(d.dot(v) < 0.99, "desviou da construção (%s)" % d)


func test_rebrota_na_primavera() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var a: AmbienteVivo = b[3]
	m.arvores[Vector2i(1, 1)] = {"e": "queimada"}
	m.arvores[Vector2i(2, 2)] = {"e": "caida", "dir": Vector2.RIGHT}
	var c := Clima.new(4)
	c.estacao = 3
	a.tick(1.0, b[2], c)
	c.estacao = 0
	a.tick(1.0, b[2], c)
	verificar(not m.arvores.has(Vector2i(1, 1)), "queimada de pé rebrotou")
	verificar(m.arvores.has(Vector2i(2, 2)), "caída continua no chão")


func test_materiais_de_folha() -> void:
	for nome in Materiais.PERFIL_FOLHA:
		var mat := StandardMaterial3D.new()
		mat.resource_name = nome
		var sm := Materiais.material(mat, 1.0) as ShaderMaterial
		igual(sm.get_shader_parameter("perfil_folha"), Materiais.PERFIL_FOLHA[nome], "%s tem perfil" % nome)
		verificar(float(sm.get_shader_parameter("vento")) > 0.0, "%s balança" % nome)
	var c := StandardMaterial3D.new()
	c.resource_name = "P_FolhaCaduca"
	verificar(Materiais.material(c, 1.0, 0.0, false, true).get_shader_parameter("carbonizada"), "versão carbonizada")
