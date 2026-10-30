extends Caso
## Esteira expressa (logistica_4) e quântica (logistica_5): as mesmas peças da esteira com classe 3 e 4
## (Construtor.CLASSES_ESTEIRA) — modelo <peça>_expressa / <peça>_quantica convertido do estudo
## (arte/estudos/conv_esteiras_niveis.py: faixa azul-aço do nível 3 e violeta do nível 4 de estudo_esteiras_niveis.py,
## lonas P_EsteiraExpressa e P_EsteiraQuantica), 3× e 4× a velocidade da básica, passagem de 8 e 10 tiles livres.
## A quântica pede computação quântica e pacote quântico (fase futura): fica travada pela árvore.

const PECAS := ["esteira_reta", "esteira_curva_esq", "esteira_curva_dir", "esteira_rampa", "esteira_inicio",
		"esteira_fim", "esteira_juncao", "esteira_tunel_entrada", "esteira_tunel_saida"]
## sufixo → [classe, fator, lona, alcance da passagem, pesquisa]
const NIVEIS := {"expressa": [3, 3.0, "P_EsteiraExpressa", 9, "logistica_4"],
		"quantica": [4, 4.0, "P_EsteiraQuantica", 11, "logistica_5"]}


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


func _menu(suf: String) -> Array:
	return ["esteira_" + suf, "esteira_rampa_" + suf, "rampa_desce_" + suf, "esteira_tunel_entrada_" + suf,
			"esteira_tunel_saida_" + suf]


func test_dados_e_modelos() -> void:
	for suf in NIVEIS:
		var nv: Array = NIVEIS[suf]
		for p in PECAS:
			var r: String = p + "_" + suf
			var md: Dictionary = Registro.modelos.get(r, {})
			verificar(not md.is_empty(), "modelo %s" % r)
			if md.is_empty():
				continue
			igual(md.get("estudo", ""), Registro.modelos[p].get("estudo", ""), "%s sai do mesmo estudo da básica" % r)
			igual(md.get("portas", []), Registro.modelos[p].get("portas", []), "%s: mesmas portas" % r)
			igual(md.get("area", []), Registro.modelos[p].get("area", []), "%s: mesma área" % r)
			perto(float(Registro.estruturas[r].velocidade), float(nv[1]) * float(Registro.estruturas[p].velocidade), 1e-6,
					"%s: %.0f× a velocidade" % [r, nv[1]])
			verificar(ResourceLoader.exists("res://assets/icones/%s.png" % r), "ícone %s" % r)
			var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
			var achou := false
			var tris := 0
			for mi in cena.find_children("*", "MeshInstance3D", true, false):
				var me: Mesh = (mi as MeshInstance3D).mesh
				for s in me.get_surface_count():
					var mat := me.surface_get_material(s)
					achou = achou or (mat != null and mat.resource_name.begins_with(nv[2]))
					tris += (me.surface_get_arrays(s)[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
			cena.free()
			verificar(achou, "%s: lona %s" % [r, nv[2]])
			verificar(tris > 0 and int(md.tris) <= int(Registro.modelos[p + "_rapida"].tris) + 4, "%s: não pesa mais que a rápida (%d)" % [r, int(md.tris)])
		perto(float(Materiais.ROLAGEM[nv[2]]), float(nv[1]) * float(Materiais.ROLAGEM.P_Esteira), 1e-6, "lona %s rola %.0f×" % [suf, nv[1]])
		igual(int(Registro.estruturas["esteira_tunel_entrada_" + suf].alcance), int(nv[3]), "passagem %s: até %d tiles livres" % [suf, int(nv[3]) - 1])
		for nome in _menu(suf):
			verificar(Registro.menu.categorias.any(func(cat): return nome in cat.pecas), "%s no menu" % nome)
			verificar(not Construtor.custo_de(nome).is_empty(), "%s tem custo" % nome)
			verificar(Registro.menu.rotulos.has(nome), "%s tem rótulo" % nome)
			for k in Construtor.custo_de(nome):
				verificar(Registro.itens.has(k), "custo de %s usa item que existe (%s)" % [nome, k])
		verificar(Construtor.arrastavel("esteira_" + suf), "esteira %s se arrasta" % suf)
		igual(Construtor.separar_classe("esteira_" + suf), ["esteira", nv[0]])
		igual(Construtor.separar_classe("rampa_desce_" + suf), ["rampa_desce", nv[0]])
		igual(Construtor.separar_classe("esteira_reta_" + suf), ["esteira_reta_" + suf, 1], "nome de modelo não é peça de menu")
		igual(Construtor.chave_custo("esteira_curva_dir", nv[0]), "esteira_" + suf)
		igual(Construtor.chave_custo("rampa_desce", nv[0]), "esteira_rampa_" + suf)
		igual(Construtor.modelo_classe("esteira_fim", nv[0]), "esteira_fim_" + suf)
	perto(float(Registro.estruturas.esteira_reta_expressa.velocidade), 5.625, 1e-6, "expressa 5,625 (árvore)")
	perto(float(Registro.estruturas.esteira_reta_quantica.velocidade), 7.5, 1e-6, "quântica 7,5 (árvore)")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("logistica_4"), "Logística 4 é jogável")
	verificar(not p.peca_liberada("esteira_expressa"), "expressa travada no início")
	p.concluidas = {"logistica": true, "eletronica": true, "automacao": true, "logistica_3": true}
	verificar(not p.disponivel("logistica_4"), "precisa de liga leve")
	p.concluidas["liga_leve"] = true
	verificar(p.disponivel("logistica_4"), "logística 3 + liga leve")
	igual(p.custo("logistica_4"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60},
			"básico × 60 + automação × 60 + químico × 60 (árvore)")
	p.concluidas["logistica_4"] = true
	for nome in _menu("expressa"):
		verificar(p.peca_liberada(nome), "libera %s" % nome)
	# quântica: ligada, mas a computação quântica (e o pacote quântico) ainda não existem no jogo
	verificar(not p.disponivel("logistica_5"), "quântica travada pela computação quântica")
	igual(Registro.progressao.pesquisas.logistica_5.requer, ["logistica_4", "computacao_quantica"], "pré-requisitos da árvore")
	verificar("pacote_quantico" in Registro.progressao.pesquisas.logistica_5.tipos, "pede pacote quântico (árvore)")
	verificar(not p.peca_liberada("esteira_quantica"), "quântica travada")
	p.concluidas["logistica_5"] = true
	for nome in _menu("quantica"):
		verificar(p.peca_liberada(nome), "logistica_5 libera %s" % nome)
	var demo := Pesquisa.new(true)
	verificar(demo.peca_liberada("esteira_quantica"), "modo demonstração constrói a quântica")


func test_traco_e_troca_entre_niveis() -> void:
	var c := _c()
	c.executar(c.plano_linha("esteira_expressa", Vector2i(0, 0), Vector2i(5, 0), 0))
	for x in 6:
		igual(int(_no(c, Vector2i(x, 0)).get("classe", 1)), 3, "tile %d é expresso" % x)
	igual(Construtor.modelo_de(_no(c, Vector2i(2, 0))), "esteira_reta_expressa")
	igual(Construtor.modelo_de(_no(c, Vector2i(0, 0))), "esteira_inicio_expressa")
	# quântica por cima da expressa troca; rápida por cima da quântica também; desfazer volta
	var troca := c.plano_linha("esteira_quantica", Vector2i(2, 0), Vector2i(3, 0), 0)
	igual(troca[0].acao, "substituir", "quântica por cima da expressa: substitui")
	c.executar(troca)
	igual(int(_no(c, Vector2i(2, 0)).get("classe", 1)), 4)
	igual(int(_no(c, Vector2i(1, 0)).get("classe", 1)), 3, "o resto continua expresso")
	c.desfazer()
	igual(int(_no(c, Vector2i(2, 0)).get("classe", 1)), 3, "desfazer volta a expressa")
	var igual_antes := c.plano_linha("esteira_expressa", Vector2i(1, 0), Vector2i(1, 0), Construtor.rot_do_fluxo(1))
	igual(igual_antes[0].acao, "igual", "expressa por cima de expressa: nada")
	# curva quântica
	c.executar(c.plano_linha("esteira_quantica", Vector2i(0, 3), Vector2i(4, 5), 0))
	var curvas := 0
	for id in c.mapa.estruturas:
		var e: Dictionary = c.mapa.estruturas[id]
		if e.nome.begins_with("esteira_curva"):
			curvas += 1
			igual(int(e.get("classe", 1)), 4, "curva quântica")
	verificar(curvas >= 1, "traço em L fez curva")


func test_custo_da_troca() -> void:
	var c := _c()
	c.cobrar = true
	c.pesquisa = Pesquisa.new()
	c.pesquisa.concluidas = {"logistica_3": true, "logistica_4": true}
	c.inventario = {"placa_ferro": 100, "engrenagem": 100, "liga_leve": 100}
	c.executar(c.plano_linha("esteira_rapida", Vector2i(0, 0), Vector2i(3, 0), 0))
	igual(int(c.inventario.placa_ferro), 92, "4 rápidas: 8 placas")
	c.executar(c.plano_linha("esteira_expressa", Vector2i(0, 0), Vector2i(3, 0), 0))
	igual(int(c.inventario.placa_ferro), 100, "trocar por expressa devolve a rápida")
	igual(int(c.inventario.liga_leve), 96, "e cobra 1 liga leve por peça")
	igual(int(c.inventario.engrenagem), 92, "e 2 engrenagens por peça")
	c.executar(c.plano_remocao(Vector2i(0, 0), Vector2i(3, 0)))
	igual(int(c.inventario.liga_leve), 100, "remover a expressa devolve o custo dela")
	igual(int(c.inventario.engrenagem), 100)
	var bloq := c.plano_linha("esteira_quantica", Vector2i(0, 2), Vector2i(3, 2), 0)
	verificar(bloq.all(func(it): return it.motivo == "em_desenvolvimento"), "Logística 5 em desenvolvimento (computação quântica, pacote quântico): quântica não se põe")
	c.pesquisa.concluidas = {}
	var bloq_r := c.plano_linha("esteira_rapida", Vector2i(0, 4), Vector2i(3, 4), 0)
	verificar(bloq_r.all(func(it): return it.motivo == "bloqueado"), "sem Logística 3: rápida bloqueada (pesquisável, não em desenvolvimento)")


## Mesma linha cheia, mesmo tempo: a expressa entrega 3× e a quântica 4× a básica.
func test_vazao() -> void:
	var entregues := {}
	for peca in ["esteira", "esteira_expressa", "esteira_quantica"]:
		var c := _c()
		var f := Fabrica.new(c.mapa)
		c.executar(c.plano_linha(peca, Vector2i(0, 0), Vector2i(9, 0), 0))
		f.reconstruir()
		var cam: Dictionary = f.caminhos[f._no_tile[Vector2i(0, 0)][0]]
		igual(int(cam.get("classe", 1)), {"esteira": 1, "esteira_expressa": 3, "esteira_quantica": 4}[peca])
		var n := [0]
		cam.esteira.saida = func(_i: String) -> bool:
			n[0] += 1
			return true
		for i in 30 * 16:
			if i == 30 * 6:
				n[0] = 0
			cam.esteira.inserir_na_entrada("pedra")
			f.tick(1.0 / 30.0)
		entregues[peca] = n[0]
	verificar(entregues.esteira > 40, "a básica entrega (%d)" % entregues.esteira)
	perto(float(entregues.esteira_expressa) / float(entregues.esteira), 3.0, 0.15, "expressa 3× (%d × %d)" % [entregues.esteira_expressa, entregues.esteira])
	perto(float(entregues.esteira_quantica) / float(entregues.esteira), 4.0, 0.2, "quântica 4× (%d × %d)" % [entregues.esteira_quantica, entregues.esteira])


## Básica → expressa → quântica na mesma linha: três caminhos ligados pela ponta, cada um na sua velocidade.
func test_mistura_de_classes() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	c.executar(c.plano_linha("esteira", Vector2i(0, 0), Vector2i(3, 0), 0))
	c.executar(c.plano_linha("esteira_expressa", Vector2i(4, 0), Vector2i(7, 0), 0))
	c.executar(c.plano_linha("esteira_quantica", Vector2i(8, 0), Vector2i(11, 0), 0))
	f.reconstruir()
	var a: int = f._no_tile[Vector2i(0, 0)][0]
	var b: int = f._no_tile[Vector2i(5, 0)][0]
	var d: int = f._no_tile[Vector2i(10, 0)][0]
	verificar(a != b and b != d, "três caminhos")
	verificar(f.caminhos[a].esteira.proximo == f.caminhos[b].esteira, "básica entrega na expressa")
	verificar(f.caminhos[b].esteira.proximo == f.caminhos[d].esteira, "expressa entrega na quântica")
	perto(f.caminhos[b].esteira.velocidade, 5.625, 1e-6, "trecho expresso a 5,625")
	perto(f.caminhos[d].esteira.velocidade, 7.5, 1e-6, "trecho quântico a 7,5")
	for i in 12:
		f.caminhos[a].esteira.inserir_na_entrada("pedra")
		_rodar(f, 0.2)
	_rodar(f, 10.0)
	igual(f.caminhos[d].esteira.itens.size(), 12, "os 12 itens chegaram ao fim")


func test_passagens() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var leste := Construtor.rot_do_fluxo(1)
	# expressa: 8 tiles livres no meio liga; a rápida (6) não
	c.executar(c.plano_peca("esteira_tunel_entrada_expressa", Vector2i(0, 0), leste))
	c.executar(c.plano_peca("esteira_tunel_saida_expressa", Vector2i(9, 0), leste))
	c.executar(c.plano_peca("esteira_tunel_entrada_rapida", Vector2i(0, 3), leste))
	c.executar(c.plano_peca("esteira_tunel_saida_rapida", Vector2i(9, 3), leste))
	# quântica: 10 tiles livres
	c.executar(c.plano_peca("esteira_tunel_entrada_quantica", Vector2i(-6, 6), leste))
	c.executar(c.plano_peca("esteira_tunel_saida_quantica", Vector2i(5, 6), leste))
	# classes trocadas não ligam
	c.executar(c.plano_peca("esteira_tunel_entrada_quantica", Vector2i(0, 8), leste))
	c.executar(c.plano_peca("esteira_tunel_saida_expressa", Vector2i(2, 8), leste))
	f.reconstruir()
	igual(f._no_tile[Vector2i(0, 0)][0], f._no_tile[Vector2i(9, 0)][0], "passagem expressa alcança 8 tiles livres")
	igual(f.caminhos[f._no_tile[Vector2i(0, 0)][0]].oculto.count(true), 8, "8 tiles debaixo da terra")
	verificar(f._no_tile[Vector2i(0, 3)][0] != f._no_tile[Vector2i(9, 3)][0], "a rápida não alcança 8")
	igual(f._no_tile[Vector2i(-6, 6)][0], f._no_tile[Vector2i(5, 6)][0], "passagem quântica alcança 10 tiles livres")
	igual(f.caminhos[f._no_tile[Vector2i(-6, 6)][0]].oculto.count(true), 10, "10 tiles debaixo da terra")
	verificar(f._no_tile[Vector2i(0, 8)][0] != f._no_tile[Vector2i(2, 8)][0], "entrada quântica não liga com saída expressa")


func test_rampas() -> void:
	var c := _c()
	var norte := Construtor.rot_do_fluxo(0)
	c.executar(c.plano_peca("esteira_rampa_expressa", Vector2i(0, 0), norte))
	var e := {}
	for id in c.mapa.estruturas:
		e = c.mapa.estruturas[id]
	igual(e.nome, "esteira_rampa")
	igual(int(e.get("classe", 1)), 3, "rampa expressa")
	igual(Construtor.modelo_de(e), "esteira_rampa_expressa")
	c.nivel = 1
	var desce := c.plano_peca("rampa_desce_quantica", Vector2i(3, 0), norte)
	igual(desce[0].nome, "esteira_rampa")
	verificar(desce[0].desce, "desce")
	igual(int(desce[0].get("classe", 1)), 4, "rampa quântica de descida")
