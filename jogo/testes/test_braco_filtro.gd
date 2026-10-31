extends Caso
## Braço com filtro (braco_filtro, fase 2.2b): modelo de estudo_bracos_novos.py (arte/estudos/conv_logistica_base.py:
## scanner na garra, painel de 5 luzes, giroflex), IK com giro/braco1/braco2/garra + pistão (camisa/haste); só pega os
## itens escolhidos pelo jogador, até 5 (filtro_max). Todo outro braço escolhe 1 item, ou fica em Auto.


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


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("braco_filtro", {})
	igual(r.get("grupo", ""), "braco", "grupo braço")
	igual(int(r.get("filtro_max", 0)), 5, "escolhe até 5 itens (árvore)")
	igual(int(r.get("alcance", 0)), 1, "alcance 1")
	verificar(float(r.get("energia_kw", 0)) > 0.0, "usa energia")
	verificar(Fiacao.papel("braco_filtro") == "consumo", "liga num poste como os outros braços")
	verificar(not Registro.estruturas.braco.has("filtro_max"), "o braço comum não tem filtro_max: escolhe 1")
	var md: Dictionary = Registro.modelos.get("braco_filtro", {})
	igual(md.get("estudo", ""), "conv_logistica_base.py", "convertido do estudo")
	var partes := {}
	for p in md.get("partes", []):
		partes[p.nome] = p
	for n in ["giro", "braco1", "braco2", "garra", "camisa", "haste"]:
		verificar(partes.has(n), "parte %s (IK do Animador)" % n)
	igual(partes.giro.pai, "base")
	igual(partes.camisa.pai, "giro", "camisa presa no giro")
	igual(partes.haste.pai, "braco1", "haste presa no braço 1")
	verificar(md.has("garra"), "medidas da garra (pulso/item)")
	verificar(int(md.get("tris", 99999)) <= 4000, "leve (%d triângulos)" % md.get("tris", 0))
	igual(md.get("portas", []).size(), 2, "pega no sul, solta no norte")
	verificar(ResourceLoader.exists("res://assets/icones/braco_filtro.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return "braco_filtro" in cat.pecas), "no menu")
	igual(Construtor.custo_de("braco_filtro").get("circuito", 0), 4.0, "custa circuitos")
	# cada parte do .glb existe e tem malha; a base fica dentro do tile
	var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
	for n in ["giro", "braco1", "braco2", "garra", "camisa", "haste"]:
		var no := cena.find_child("*_" + n, true, false)
		verificar(no != null, "nó da parte %s no .glb" % n)
	cena.free()
	var d: Array = md.dims
	verificar(float(d[0]) <= 1.0, "base cabe no tile (%s)" % str(d))


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("braco_filtro"), "jogável")
	verificar(not p.peca_liberada("braco_filtro"), "travado no início")
	p.concluidas = {"eletronica": true}
	verificar(not p.disponivel("braco_filtro"), "precisa de automação")
	p.concluidas["automacao"] = true
	verificar(p.disponivel("braco_filtro"), "depois de automação")
	igual(p.custo("braco_filtro"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "básico × 30 + automação × 30 (árvore)")
	p.concluidas["braco_filtro"] = true
	verificar(p.peca_liberada("braco_filtro"), "libera o braço com filtro")


func test_limite_de_5() -> void:
	var e := {"nome": "braco_filtro", "filtros": ["a", "b", "c", "d", "e", "f", "g"]}
	igual(Fabrica.filtros_de(e), ["a", "b", "c", "d", "e"], "no máximo 5")
	igual(Fabrica.filtros_de({"nome": "braco_filtro"}), [], "vazio = Auto")
	igual(Fabrica.filtros_de({"nome": "braco", "filtros": ["carvao"]}), ["carvao"], "salvo antigo de braço comum continua")


## Esteira com pedra, carvão e placa de ferro passando: o braço com filtro (carvão + ferro) só tira esses dois.
func test_so_pega_o_escolhido() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	_por(c, "gerador", Vector2i(8, 6))
	_por(c, "poste_energia", Vector2i(11, 6))
	_por(c, "poste_energia", Vector2i(17, 3))
	_por(c, "poste_energia", Vector2i(5, 3))
	c.executar(c.plano_linha("esteira", Vector2i(-3, 0), Vector2i(8, 0), 0))
	var b := _por(c, "braco_filtro", Vector2i(1, 1), 0)                  # tira da esteira (sul) → baú (norte)
	var bau := _por(c, "bau", Vector2i(1, 2), 0)
	c.mapa.estruturas[b]["filtros"] = ["carvao", "placa_ferro"]
	f.reconstruir()
	for id in f.combustivel: f.combustivel[id] = 30.0
	var e: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-3, 0)][0]].esteira
	var tipos := ["pedra", "carvao", "placa_ferro"]
	for i in 30 * 30:
		if i % 30 == 0:
			e.inserir_na_entrada(tipos[(i / 30) % 3])
		f.tick(1.0 / 30.0)
	verificar(f.bracos[b].energia > 0.5, "braço com energia")
	verificar(int(f.baus[bau].get("carvao", 0)) > 3, "pegou carvão (%s)" % f.baus[bau])
	verificar(int(f.baus[bau].get("placa_ferro", 0)) > 3, "pegou placa de ferro (%s)" % f.baus[bau])
	igual(int(f.baus[bau].get("pedra", 0)), 0, "pedra passa reta")
	# Auto (sem filtro): pega de tudo
	c.mapa.estruturas[b]["filtros"] = []
	f.reconstruir()
	e = f.caminhos[f._no_tile[Vector2i(-3, 0)][0]].esteira               # remontar faz caminhos novos
	for i in 30 * 20:
		if i % 30 == 0:
			e.inserir_na_entrada(tipos[(i / 30) % 3])
		f.tick(1.0 / 30.0)
	verificar(int(f.baus[bau].get("pedra", 0)) > 0, "sem filtro pega a pedra também (%s)" % f.baus[bau])


## O filtro é guardado na estrutura (vai junto no salvamento) e sobrevive à remontagem.
func test_filtro_salvo() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var b := _por(c, "braco_filtro", Vector2i(0, 0), 0)
	c.mapa.estruturas[b]["filtros"] = ["engrenagem"]
	f.reconstruir()
	igual(f.bracos[b].filtros, ["engrenagem"])
	igual(f.bracos[b].filtro, "engrenagem", "um item só: pega direto da máquina/baú por nome")
	f.reconstruir()
	igual(f.bracos[b].filtros, ["engrenagem"], "continua depois de remontar")


## Todo braço escolhe 1 item; o com filtro, até 5. Tocar de novo no escolhido volta ao Auto.
func test_todo_braco_escolhe_um() -> void:
	for nome in Registro.estruturas:
		if Registro.estruturas[nome].get("grupo", "") == "braco":
			igual(Fabrica.max_filtros(nome), 5 if nome == "braco_filtro" else 1, "quantos %s escolhe" % nome)
	igual(Fabrica.escolher_filtro([], "carvao", 1), ["carvao"], "escolhe")
	igual(Fabrica.escolher_filtro(["carvao"], "pedra", 1), ["pedra"], "troca, não soma")
	igual(Fabrica.escolher_filtro(["carvao"], "carvao", 1), [], "de novo: Auto")
	igual(Fabrica.escolher_filtro(["a", "b"], "c", 1), ["c"], "save antigo com vários: tocar deixa um só")
	igual(Fabrica.escolher_filtro(["a", "b"], "c", 3), ["a", "b", "c"], "com filtro soma")
	igual(Fabrica.escolher_filtro(["a", "b", "c"], "b", 3), ["a", "c"], "com filtro tira")
	igual(Fabrica.escolher_filtro(["a", "b", "c"], "d", 3), ["a", "b", "c"], "cheio não muda")
	for it in Registro.itens:
		verificar(TelaPesquisa._tex_item(it) != null, "ícone de %s para a grade" % it)


## Braço comum com 1 item: só tira esse da esteira, e o filtro passa por salvar e carregar (texto do save → remontar).
func test_braco_comum_pega_um_e_salva() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	_por(c, "gerador", Vector2i(8, 6))
	_por(c, "poste_energia", Vector2i(11, 6))
	_por(c, "poste_energia", Vector2i(5, 3))
	c.executar(c.plano_linha("esteira", Vector2i(-3, 0), Vector2i(8, 0), 0))
	var b := _por(c, "braco", Vector2i(1, 1), 0)
	var bau := _por(c, "bau", Vector2i(1, 2), 0)
	c.mapa.estruturas[b]["filtros"] = ["carvao"]
	var volta = str_to_var(var_to_str(c.mapa.estruturas))
	igual(volta[b].get("filtros", []), ["carvao"], "o filtro vai no save")
	c.mapa.estruturas[b] = volta[b]
	f.reconstruir()
	igual(f.bracos[b].filtro, "carvao", "remontado com o filtro do save")
	for id in f.combustivel: f.combustivel[id] = 30.0
	var e: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-3, 0)][0]].esteira
	for i in 30 * 30:
		if i % 30 == 0:
			e.inserir_na_entrada(["pedra", "carvao"][(i / 30) % 2])
		f.tick(1.0 / 30.0)
	verificar(int(f.baus[bau].get("carvao", 0)) > 3, "pegou carvão (%s)" % f.baus[bau])
	igual(int(f.baus[bau].get("pedra", 0)), 0, "pedra passa reta")
