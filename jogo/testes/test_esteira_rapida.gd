extends Caso
## Esteira rápida (logistica_3, fase 2.2b): as mesmas peças da esteira com classe 2 (Construtor.CLASSES_ESTEIRA) —
## modelo <peça>_rapida convertido do estudo (arte/estudos/conv_logistica_base.py: faixa vermelha gasta do nível 2 de
## estudo_esteiras_niveis.py, lona P_EsteiraRapida), o dobro da velocidade (3,75), passagem de até 6 tiles livres.

const PECAS := ["esteira_reta", "esteira_curva_esq", "esteira_curva_dir", "esteira_rampa", "esteira_inicio",
		"esteira_fim", "esteira_juncao", "esteira_tunel_entrada", "esteira_tunel_saida"]


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 24):
		for y in range(-8, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _rodar(f: Fabrica, s: float) -> void:
	for i in int(s * 30):
		f.tick(1.0 / 30.0)


func _no(c: Construtor, t: Vector2i) -> Dictionary:
	return c.mapa.estruturas[c.mapa.tiles[t]]


func test_dados_e_modelos() -> void:
	for p in PECAS:
		var r: String = p + "_rapida"
		var md: Dictionary = Registro.modelos.get(r, {})
		verificar(not md.is_empty(), "modelo %s" % r)
		igual(md.get("estudo", ""), Registro.modelos[p].get("estudo", ""), "%s sai do mesmo estudo da básica" % r)
		igual(md.get("portas", []), Registro.modelos[p].get("portas", []), "%s: mesmas portas" % r)
		igual(md.get("area", []), Registro.modelos[p].get("area", []), "%s: mesma área" % r)
		perto(float(Registro.estruturas[r].velocidade), 2.0 * float(Registro.estruturas[p].velocidade), 1e-6, "%s: o dobro da velocidade" % r)
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % r), "ícone %s" % r)
		# a lona é outra (rola no dobro): P_EsteiraRapida no .glb
		var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
		var achou := false
		for mi in cena.find_children("*", "MeshInstance3D", true, false):
			var me: Mesh = (mi as MeshInstance3D).mesh
			for s in me.get_surface_count():
				var mat := me.surface_get_material(s)
				achou = achou or (mat != null and mat.resource_name.begins_with("P_EsteiraRapida"))
		cena.free()
		verificar(achou, "%s: lona P_EsteiraRapida" % r)
	perto(float(Materiais.ROLAGEM.P_EsteiraRapida), 2.0 * float(Materiais.ROLAGEM.P_Esteira), 1e-6, "lona rola no dobro")
	igual(int(Registro.estruturas.esteira_tunel_entrada_rapida.alcance), 7, "passagem rápida: até 6 tiles livres no meio")
	perto(float(Registro.estruturas.esteira_reta_rapida.velocidade), 3.75, 1e-6, "3,75 (árvore)")
	for nome in ["esteira_rapida", "esteira_rampa_rapida", "rampa_desce_rapida", "esteira_tunel_entrada_rapida", "esteira_tunel_saida_rapida"]:
		verificar(Registro.menu.categorias.any(func(cat): return nome in cat.pecas), "%s no menu" % nome)
		verificar(not Construtor.custo_de(nome).is_empty(), "%s tem custo" % nome)
	verificar(Construtor.arrastavel("esteira_rapida"), "esteira rápida se arrasta")
	igual(Construtor.separar_classe("esteira_rapida"), ["esteira", 2])
	igual(Construtor.separar_classe("rampa_desce_rapida"), ["rampa_desce", 2])
	igual(Construtor.separar_classe("esteira_reta_rapida"), ["esteira_reta_rapida", 1], "nome de modelo não é peça de menu")
	igual(Construtor.chave_custo("esteira_curva_dir", 2), "esteira_rapida")
	igual(Construtor.chave_custo("rampa_desce", 2), "esteira_rampa_rapida")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("logistica_3"), "Logística 3 é jogável")
	verificar(not p.peca_liberada("esteira_rapida"), "travada no início")
	p.concluidas = {"logistica": true}
	verificar(not p.disponivel("logistica_3"), "precisa de automação")
	p.concluidas = {"logistica": true, "eletronica": true, "automacao": true}
	verificar(p.disponivel("logistica_3"), "logística + automação")
	igual(p.custo("logistica_3"), {"pacote_pesquisa": 40, "pacote_automacao": 40}, "básico × 40 + automação × 40 (árvore)")
	p.concluidas["logistica_3"] = true
	for nome in ["esteira_rapida", "esteira_rampa_rapida", "rampa_desce_rapida", "esteira_tunel_entrada_rapida", "esteira_tunel_saida_rapida"]:
		verificar(p.peca_liberada(nome), "libera %s" % nome)


func test_traco_e_troca() -> void:
	var c := _c()
	c.executar(c.plano_linha("esteira_rapida", Vector2i(0, 0), Vector2i(5, 0), 0))
	igual(_no(c, Vector2i(0, 0)).nome, "esteira_inicio")
	igual(_no(c, Vector2i(5, 0)).nome, "esteira_fim")
	for x in 6:
		igual(int(_no(c, Vector2i(x, 0)).get("classe", 1)), 2, "tile %d é rápido" % x)
	igual(Construtor.modelo_de(_no(c, Vector2i(2, 0))), "esteira_reta_rapida")
	# curva rápida
	c.executar(c.plano_linha("esteira_rapida", Vector2i(0, 3), Vector2i(4, 5), 0))
	var curvas := 0
	for id in c.mapa.estruturas:
		var e: Dictionary = c.mapa.estruturas[id]
		if e.nome.begins_with("esteira_curva"):
			curvas += 1
			igual(int(e.get("classe", 1)), 2, "curva rápida")
	verificar(curvas >= 1, "traço em L fez curva")
	# traçar a básica por cima troca de volta (e a rápida por cima da básica, também)
	c.executar(c.plano_linha("esteira", Vector2i(2, 0), Vector2i(3, 0), 0))
	igual(int(_no(c, Vector2i(2, 0)).get("classe", 1)), 1, "básica por cima: troca")
	igual(int(_no(c, Vector2i(1, 0)).get("classe", 1)), 2, "o resto continua rápido")
	var igual_antes := c.plano_linha("esteira_rapida", Vector2i(1, 0), Vector2i(1, 0), Construtor.rot_do_fluxo(1))
	igual(igual_antes[0].acao, "igual", "rápida por cima de rápida igual: nada")
	var troca := c.plano_linha("esteira_rapida", Vector2i(2, 0), Vector2i(3, 0), 0)
	igual(troca[0].acao, "substituir", "rápida por cima da básica: substitui")
	# desfazer volta a classe
	c.executar(troca)
	igual(int(_no(c, Vector2i(2, 0)).get("classe", 1)), 2)
	c.desfazer()
	igual(int(_no(c, Vector2i(2, 0)).get("classe", 1)), 1, "desfazer volta a básica")


func test_custo_da_troca() -> void:
	var c := _c()
	c.cobrar = true
	c.pesquisa = Pesquisa.new()
	c.pesquisa.concluidas = {"logistica_3": true}
	c.inventario = {"placa_ferro": 100, "engrenagem": 100}
	c.executar(c.plano_linha("esteira", Vector2i(0, 0), Vector2i(3, 0), 0))
	igual(int(c.inventario.placa_ferro), 96, "4 básicas: 4 placas")
	c.executar(c.plano_linha("esteira_rapida", Vector2i(0, 0), Vector2i(3, 0), 0))
	igual(int(c.inventario.placa_ferro), 100 - 8, "trocar por rápida devolve a básica e cobra a rápida (2 placas cada)")
	igual(int(c.inventario.engrenagem), 96, "e 1 engrenagem cada")
	c.executar(c.plano_remocao(Vector2i(0, 0), Vector2i(3, 0)))
	igual(int(c.inventario.placa_ferro), 100, "remover a rápida devolve o custo dela")
	igual(int(c.inventario.engrenagem), 100)
	var p2 := Pesquisa.new()
	c.pesquisa = p2
	var bloq := c.plano_linha("esteira_rapida", Vector2i(0, 2), Vector2i(3, 2), 0)
	verificar(bloq.all(func(it): return it.motivo == "bloqueado"), "sem Logística 3: bloqueada")


## A rápida leva o dobro: mesmo tempo, mesma linha cheia, o dobro de itens no fim.
func test_vazao_dobrada() -> void:
	var entregues := {}
	for peca in ["esteira", "esteira_rapida"]:
		var c := _c()
		var f := Fabrica.new(c.mapa)
		c.executar(c.plano_linha(peca, Vector2i(0, 0), Vector2i(9, 0), 0))
		f.reconstruir()
		var cam: Dictionary = f.caminhos[f._no_tile[Vector2i(0, 0)][0]]
		igual(int(cam.get("classe", 1)), 2 if peca == "esteira_rapida" else 1)
		var n := [0]
		cam.esteira.saida = func(_i: String) -> bool:
			n[0] += 1
			return true
		for i in 30 * 16:
			if i == 30 * 6:
				n[0] = 0                              # linha já cheia: conta só a vazão (10 s)
			cam.esteira.inserir_na_entrada("pedra")
			f.tick(1.0 / 30.0)
		entregues[peca] = n[0]
	verificar(entregues.esteira > 40, "a básica entrega (%d)" % entregues.esteira)
	perto(float(entregues.esteira_rapida) / float(entregues.esteira), 2.0, 0.1, "a rápida entrega o dobro (%d × %d)" % [entregues.esteira_rapida, entregues.esteira])


## Básica → rápida → básica na mesma linha: três caminhos ligados pela ponta, cada um na sua velocidade; nada se perde.
func test_mistura_de_classes() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	c.executar(c.plano_linha("esteira", Vector2i(0, 0), Vector2i(3, 0), 0))
	c.executar(c.plano_linha("esteira_rapida", Vector2i(4, 0), Vector2i(7, 0), 0))
	c.executar(c.plano_linha("esteira", Vector2i(8, 0), Vector2i(11, 0), 0))
	igual(_no(c, Vector2i(3, 0)).nome, "esteira_reta", "ligadas pela ponta (não vira fim)")
	igual(_no(c, Vector2i(4, 0)).nome, "esteira_reta")
	f.reconstruir()
	var a: int = f._no_tile[Vector2i(0, 0)][0]
	var b: int = f._no_tile[Vector2i(5, 0)][0]
	var d: int = f._no_tile[Vector2i(10, 0)][0]
	verificar(a != b and b != d, "três caminhos")
	verificar(f.caminhos[a].esteira.proximo == f.caminhos[b].esteira, "básica entrega na rápida")
	verificar(f.caminhos[b].esteira.proximo == f.caminhos[d].esteira, "rápida entrega na básica")
	perto(f.caminhos[b].esteira.velocidade, 3.75, 1e-6, "trecho rápido a 3,75")
	perto(f.caminhos[a].esteira.velocidade, 1.875, 1e-6, "trecho básico a 1,875")
	for i in 12:
		f.caminhos[a].esteira.inserir_na_entrada("pedra")
		_rodar(f, 0.2)
	_rodar(f, 10.0)
	igual(f.caminhos[d].esteira.itens.size(), 12, "os 12 itens chegaram ao fim")
	igual(f.caminhos[a].esteira.itens.size() + f.caminhos[b].esteira.itens.size(), 0, "nada ficou no caminho")
	# salvar/restaurar: a classe vai junto na estrutura
	var est := f.estado()
	var f2 := Fabrica.new(c.mapa)
	f2.restaurar(est)
	igual(f2.caminhos.size(), f.caminhos.size(), "remontou igual")


func test_passagem_rapida() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var leste := Construtor.rot_do_fluxo(1)
	# 6 tiles livres no meio: a rápida liga, a básica não
	c.executar(c.plano_peca("esteira_tunel_entrada_rapida", Vector2i(0, 0), leste))
	c.executar(c.plano_peca("esteira_tunel_saida_rapida", Vector2i(7, 0), leste))
	c.executar(c.plano_peca("esteira_tunel_entrada", Vector2i(0, 3), leste))
	c.executar(c.plano_peca("esteira_tunel_saida", Vector2i(7, 3), leste))
	# classes trocadas não ligam
	c.executar(c.plano_peca("esteira_tunel_entrada_rapida", Vector2i(0, 6), leste))
	c.executar(c.plano_peca("esteira_tunel_saida", Vector2i(2, 6), leste))
	f.reconstruir()
	igual(f._no_tile[Vector2i(0, 0)][0], f._no_tile[Vector2i(7, 0)][0], "passagem rápida alcança 6 tiles livres")
	igual(f.caminhos[f._no_tile[Vector2i(0, 0)][0]].oculto.count(true), 6, "6 tiles debaixo da terra")
	verificar(f._no_tile[Vector2i(0, 3)][0] != f._no_tile[Vector2i(7, 3)][0], "a básica não alcança")
	verificar(f._no_tile[Vector2i(0, 6)][0] != f._no_tile[Vector2i(2, 6)][0], "entrada rápida não liga com saída básica")
	igual(Construtor.modelo_de(_no(c, Vector2i(0, 0))), "esteira_tunel_entrada_rapida")


func test_rampa_rapida() -> void:
	var c := _c()
	var norte := Construtor.rot_do_fluxo(0)
	c.executar(c.plano_peca("esteira_rampa_rapida", Vector2i(0, 0), norte))
	var e := {}
	for id in c.mapa.estruturas:
		e = c.mapa.estruturas[id]
	igual(e.nome, "esteira_rampa")
	igual(int(e.get("classe", 1)), 2, "rampa rápida")
	igual(Construtor.modelo_de(e), "esteira_rampa_rapida")
	c.nivel = 1
	var desce := c.plano_peca("rampa_desce_rapida", Vector2i(3, 0), norte)
	igual(desce[0].nome, "esteira_rampa")
	verificar(desce[0].desce, "desce")
	igual(int(desce[0].get("classe", 1)), 2, "rampa rápida de descida")
