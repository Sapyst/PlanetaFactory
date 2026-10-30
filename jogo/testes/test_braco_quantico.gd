extends Caso
## Braço quântico (pesquisa braco_quantico, lote 16; arte de estudo_bracos_novos.py via conv_lote16.py): ciclo 0,2 s,
## até 8 itens iguais por vez; a lança telescópica pega de 1 a 3 tiles atrás (escolhido no painel) e solta no tile da
## frente. Animação própria (não é o IK de 2 elos): as seções lanca1..4 andam k·e, a ponta 4e, o cabo estica, o
## carretel gira e os anéis do rastro aparecem quando a ponta passa; o item voa pelo caminho do campo.
## Travado pela árvore: pede computacao_quantica (sem estudo) — só o modo demonstração constrói.

func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 8):
		for y in range(-8, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot := 0) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("braco_quantico", {})
	igual(r.get("grupo", ""), "braco")
	perto(float(r.get("ciclo_s", 0)), 0.2, 1e-6, "ciclo 0,2 s (árvore)")
	igual(int(r.get("pilha", 0)), 8, "8 itens por vez (árvore)")
	igual(int(r.get("alcance_max", 0)), 3, "alcance 1 a 3 (árvore)")
	var md: Dictionary = Registro.modelos.get("braco_quantico", {})
	igual(md.get("estudo", ""), "estudo_bracos_novos.py")
	var partes := {}
	for p in md.get("partes", []):
		partes[p.nome] = p
	for n in ["lanca1", "lanca2", "lanca3", "lanca4", "ponta", "cabo", "carretel"]:
		verificar(partes.has(n), "parte " + n)
	for i in range(1, 9):
		verificar(partes.has("anel%d" % i), "anel do rastro %d" % i)
	verificar(not partes.has("braco1"), "sem IK de 2 elos (a lança fica de pé)")
	verificar(md.has("lanca"), "medidas da lança no .json")
	igual(md.get("portas", []).size(), 2, "pega no sul, solta no norte")
	verificar(ResourceLoader.exists("res://assets/icones/braco_quantico.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return "braco_quantico" in cat.pecas), "no menu")
	for k in Construtor.custo_de("braco_quantico"):
		verificar(Registro.itens.has(k), "custo com item que existe (%s)" % k)


func test_pesquisa_travada() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("braco_quantico"), "ligada em progressao.json")
	igual(Registro.progressao.pesquisas.braco_quantico.requer, ["braco_empilhador", "computacao_quantica"])
	p.concluidas = {"braco_empilhador": true}
	verificar(not p.disponivel("braco_quantico"), "computação quântica não existe: travado")
	verificar(Pesquisa.new(true).peca_liberada("braco_quantico"), "modo demonstração constrói")


## Baú a `alc` tiles atrás → braço quântico → baú na frente: leva 8 iguais por ciclo de 0,2 s.
func test_alcance_e_vazao() -> void:
	for alc in [1, 2, 3]:
		var c := _c()
		var f := Fabrica.new(c.mapa)
		var de := _por(c, "bau", Vector2i(0, -alc))
		var b := _por(c, "braco_quantico", Vector2i(0, 0), 0)
		var para := _por(c, "bau", Vector2i(0, 1))
		c.mapa.estruturas[b]["alcance"] = alc
		f.reconstruir()
		igual(Fabrica.alcance_origem(c.mapa.estruturas[b]), alc)
		f.baus[de]["placa_ferro"] = 100
		var br: Braco = f.bracos[b]
		br.energia = 1.0
		var maior := 0
		for i in 30:                                     # 1 s
			br.tick(1.0 / 30.0)
			maior = maxi(maior, br.qtd)
		igual(maior, 8, "garra com 8 iguais (alcance %d)" % alc)
		var levou := int(f.baus[para].get("placa_ferro", 0))
		verificar(levou >= 32, "em 1 s levou %d (≥ 4 ciclos × 8)" % levou)
		igual(levou + br.qtd + int(f.baus[de].get("placa_ferro", 0)), 100, "nada some")
	# fora do alcance escolhido não pega; alcance fora de 1..3 é limitado
	var c2 := _c()
	var f2 := Fabrica.new(c2.mapa)
	var de2 := _por(c2, "bau", Vector2i(0, -3))
	var b2 := _por(c2, "braco_quantico", Vector2i(0, 0), 0)
	_por(c2, "bau", Vector2i(0, 1))
	c2.mapa.estruturas[b2]["alcance"] = 2
	f2.reconstruir()
	f2.baus[de2]["placa_ferro"] = 10
	f2.bracos[b2].energia = 1.0
	for i in 30:
		f2.bracos[b2].tick(1.0 / 30.0)
	igual(int(f2.baus[de2].placa_ferro), 10, "baú a 3 tiles com alcance 2: nada")
	c2.mapa.estruturas[b2]["alcance"] = 9
	igual(Fabrica.alcance_origem(c2.mapa.estruturas[b2]), 3, "no máximo 3")
	igual(Portas.costas_braco(c2.mapa.estruturas[b2]), Vector2i(0, -3), "as costas seguem o alcance")


## Animador: a lança estica até o alcance; os anéis aparecem com a ponta; o item voa da origem ao destino.
func test_lanca_estica() -> void:
	var raiz := Node3D.new()
	var no: Node3D = (load(Registro.modelos.braco_quantico.modelo) as PackedScene).instantiate()
	raiz.add_child(no)
	var a := Animador.new()
	a.modelo = "braco_quantico"
	no.add_child(a)
	a._ready()
	verificar(a.tem("lanca4") and a.tem("ponta") and a.tem("anel8"), "partes achadas pelo nome")
	var z0: float = (a._partes["ponta"] as Node3D).position.z
	a.alcance = 3.0
	for i in 30:
		a._lanca_quantica(0.5)
	perto((a._partes["ponta"] as Node3D).position.z - z0, 2.0, 1e-3, "alcance 3: a ponta anda 2 m para a origem")
	perto((a._partes["lanca2"] as Node3D).position.z - (a._base["lanca2"] as Transform3D).origin.z, 1.0, 1e-3, "seção 2 anda 2e")
	verificar((a._partes["anel8"] as Node3D).visible, "o último anel aparece com a lança toda esticada")
	a.alcance = 1.0
	for i in 30:
		a._lanca_quantica(0.5)
	perto((a._partes["ponta"] as Node3D).position.z, z0, 1e-3, "alcance 1: recolhida")
	verificar(not (a._partes["anel1"] as Node3D).visible, "anéis somem com a lança recolhida")
	a.fase_braco = 0.0
	var p0 := a.ponto_garra()
	a.fase_braco = 0.5
	var p1 := a.ponto_garra()
	perto(p0.z, 1.0, 0.05, "começa na origem (1 tile atrás: +z do Godot é o sul)")
	perto(p1.z, -1.0, 0.05, "termina no tile da frente")
	verificar(p0.y < 0.4 and p1.y < 0.4, "pega e solta na altura da esteira")
	a.fase_braco = 0.25
	verificar(a.ponto_garra().y > 1.0, "no meio do caminho voa por cima da lança")
	raiz.free()
