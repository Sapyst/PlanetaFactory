extends Caso
## Braço empilhador (braco_empilhador): modelo de estudo_bracos_novos.py (arte/estudos/conv_bracos_novos.py: garra-
## gaiola com pinças e prensa, pistão de elevação na frente), IK com giro/braco1/braco2/garra + camisa/haste. Pega de
## uma vez até 4 itens IGUAIS que estão na origem e solta um por vez (árvore: até 4 itens por ciclo).


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 22):
		for y in range(-8, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot := 0) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s" % [nome, t])
	return id


func _global(n: Node3D) -> Transform3D:
	var t := n.transform
	var p := n.get_parent()
	while p is Node3D:
		t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("braco_empilhador", {})
	igual(r.get("grupo", ""), "braco", "grupo braço")
	igual(int(r.get("pilha", 0)), 4, "até 4 itens por ciclo (árvore)")
	igual(int(r.get("alcance", 0)), 1, "alcance 1")
	verificar(Fiacao.papel("braco_empilhador") == "consumo", "liga num poste como os outros braços")
	var md: Dictionary = Registro.modelos.get("braco_empilhador", {})
	verificar(not md.is_empty(), "modelo")
	var partes := {}
	for p in md.get("partes", []):
		partes[p.nome] = p
	for n in ["giro", "braco1", "braco2", "garra", "camisa", "haste"]:
		verificar(partes.has(n), "parte %s (IK do Animador)" % n)
	igual(partes.camisa.pai, "giro", "camisa presa no giro")
	igual(partes.haste.pai, "braco1", "haste presa no braço 1")
	verificar(md.has("garra"), "medidas da garra (pulso/item)")
	verificar(int(md.get("tris", 99999)) <= 4500, "leve (%d triângulos)" % md.get("tris", 0))
	igual(md.get("portas", []).size(), 2, "pega no sul, solta no norte")
	verificar(float(md.dims[0]) <= 1.0, "base cabe no tile (%s)" % str(md.dims))
	verificar(ResourceLoader.exists("res://assets/icones/braco_empilhador.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return "braco_empilhador" in cat.pecas), "no menu")
	verificar(Registro.menu.rotulos.has("braco_empilhador"), "rótulo")
	for k in Construtor.custo_de("braco_empilhador"):
		verificar(Registro.itens.has(k), "custo com item que existe (%s)" % k)
	verificar(Construtor.custo_de("braco_empilhador").has("processador"), "custa processador (árvore pede processador)")


func test_ik() -> void:
	var c: Node3D = (load(Registro.modelos.braco_empilhador.modelo) as PackedScene).instantiate()
	var a := Animador.new()
	a.modelo = "braco_empilhador"
	a.pega = Vector2(1.0, 0.42)
	a.solta = Vector2(1.0, 0.62)
	c.add_child(a)
	a._ready()
	var dz := float(Registro.modelos.braco_empilhador.garra.pulso_dz)
	var g := c.find_child("braco_empilhador_garra", true, false) as Node3D
	var camisa := c.find_child("braco_empilhador_camisa", true, false) as Node3D
	var haste := c.find_child("braco_empilhador_haste", true, false) as Node3D
	verificar(g != null and camisa != null and haste != null, "nós das partes")
	if g != null and camisa != null and haste != null:
		var eixo0 := _global(camisa).basis * Vector3.FORWARD
		var desvio := eixo0.signed_angle_to(_global(haste).origin - _global(camisa).origin, Vector3.RIGHT)
		for caso in [[0.0, a.pega, 1.0], [0.5, a.solta, -1.0]]:
			a.fase_braco = caso[0]
			a._braco_mecanico()
			var w := _global(g)
			var alvo: Vector2 = caso[1]
			perto(w.origin.z * caso[2], alvo.x, 0.02, "fase %.1f: pulso na distância" % caso[0])
			perto(w.origin.y, alvo.y + dz, 0.02, "fase %.1f: pulso na altura" % caso[0])
			perto(w.basis.y.dot(Vector3.UP), 1.0, 0.01, "fase %.1f: garra de pé" % caso[0])
			var eixo := _global(camisa).basis * Vector3.FORWARD
			perto(eixo.signed_angle_to(_global(haste).origin - _global(camisa).origin, _global(camisa).basis.x), desvio, 0.02,
					"fase %.1f: camisa mira a haste" % caso[0])
	c.free()


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("braco_empilhador"), "jogável")
	verificar(not p.peca_liberada("braco_empilhador"), "travado no início")
	p.concluidas = {"eletronica": true, "automacao": true, "braco_filtro": true}
	verificar(not p.disponivel("braco_empilhador"), "precisa de processador")
	for r in ["refino", "bomba_agua", "quimica", "processador"]:
		p.concluidas[r] = true
	verificar(p.disponivel("braco_empilhador"), "braço com filtro + processador")
	igual(p.custo("braco_empilhador"), {"pacote_pesquisa": 50, "pacote_automacao": 50, "pacote_quimico": 50},
			"básico × 50 + automação × 50 + químico × 50 (árvore)")
	p.concluidas["braco_empilhador"] = true
	verificar(p.peca_liberada("braco_empilhador"), "libera o empilhador")


## Baú com 10 placas → braço → baú: o empilhador leva 4 por ciclo; o comum, 1.
func test_leva_4_por_vez() -> void:
	var levou := {}
	for nome in ["braco", "braco_empilhador"]:
		var c := _c()
		var f := Fabrica.new(c.mapa)
		var de := _por(c, "bau", Vector2i(0, -1))
		var b := _por(c, nome, Vector2i(0, 0), 0)
		var para := _por(c, "bau", Vector2i(0, 1))
		f.reconstruir()
		f.baus[de]["placa_ferro"] = 10
		f.baus[de]["carvao"] = 3
		var br: Braco = f.bracos[b]
		br.energia = 1.0
		var maior := 0
		for i in 30 * 3:
			br.tick(1.0 / 30.0)
			maior = maxi(maior, br.qtd)
		levou[nome] = int(f.baus[para].get("placa_ferro", 0)) + int(f.baus[para].get("carvao", 0))
		if nome == "braco_empilhador":
			igual(maior, 4, "garra com 4 iguais")
			var b2: Dictionary = f.baus[para]
			verificar(int(b2.get("placa_ferro", 0)) + int(b2.get("carvao", 0)) + br.qtd + int(f.baus[de].get("placa_ferro", 0)) + int(f.baus[de].get("carvao", 0)) == 13, "nada some (%s / %s)" % [b2, f.baus[de]])
		else:
			igual(maior, 1, "o comum leva 1")
	verificar(levou.braco_empilhador >= 3 * levou.braco, "empilhador leva ~4× no mesmo tempo (%d × %d)" % [levou.braco_empilhador, levou.braco])


## Da esteira: pega só os iguais que estão no tile da origem naquele instante; nunca mistura.
func test_da_esteira_nao_mistura() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	_por(c, "gerador", Vector2i(8, 6))
	_por(c, "poste_energia", Vector2i(11, 6))
	_por(c, "poste_energia", Vector2i(17, 3))
	_por(c, "poste_energia", Vector2i(5, 3))
	c.executar(c.plano_linha("esteira", Vector2i(-3, 0), Vector2i(8, 0), 0))
	var b := _por(c, "braco_empilhador", Vector2i(1, 1), 0)
	var bau := _por(c, "bau", Vector2i(1, 2), 0)
	f.reconstruir()
	for id in f.combustivel: f.combustivel[id] = 30.0
	var br: Braco = f.bracos[b]
	var e: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-3, 0)][0]].esteira
	var tipos := ["pedra", "pedra", "carvao", "pedra"]
	for i in 30 * 20:
		if i % 8 == 0:
			e.inserir_na_entrada(tipos[(i / 8) % 4])
		f.tick(1.0 / 30.0)
	verificar(br.energia > 0.5, "com energia")
	verificar(int(f.baus[bau].get("pedra", 0)) > 0 and int(f.baus[bau].get("carvao", 0)) > 0, "pegou da esteira (%s)" % f.baus[bau])
	verificar(br.qtd <= 4, "nunca mais de 4")


## Salvar no meio do ciclo: a pilha volta com a quantidade.
func test_salvo() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var b := _por(c, "braco_empilhador", Vector2i(0, 0), 0)
	f.reconstruir()
	f.bracos[b].segurando = "engrenagem"
	f.bracos[b].qtd = 3
	f.bracos[b].estado = Braco.Estado.INDO_SOLTAR
	var d := f.estado()
	var f2 := Fabrica.new(c.mapa)
	f2.restaurar(d)
	igual(f2.bracos[b].qtd, 3, "3 na garra depois de carregar")
	igual(f2.bracos[b].pilha_max, 4)
	d.bracos[b].erase("qtd")
	var f3 := Fabrica.new(c.mapa)
	f3.restaurar(d)
	igual(f3.bracos[b].qtd, 1, "salvo antigo: 1 na garra")
