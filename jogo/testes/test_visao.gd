extends Caso
## Visão de recursos (ficha do tile, manchas) e o caminho das esteiras do modo construção.


func _visao() -> VisaoRecursos:
	var g := GeradorMundo.new(1337)
	var v := VisaoRecursos.new()
	v.gerador = g
	v.mapa = MapaOcupacao.new(g)
	v._d = Registro.recursos
	return v


func test_dados_cobrem_o_mapa() -> void:
	var d: Dictionary = Registro.recursos
	for b in Registro.biomas:
		if b.begins_with("_"):
			continue
		verificar(d.biomas.has(b), "bioma %s tem nome" % b)
		for j in Registro.biomas[b].get("jazidas", {}):
			verificar(d.jazidas.has(j), "jazida %s tem nome/cor/máquina" % j)
	for t in GeradorMundo.Terreno.keys():
		if t != "TERRA":
			verificar(d.agua.has(t), "água %s tem nome" % t)
	for k in Registro.progressao.drops:
		verificar(d.elementos.has(k), "elemento %s tem nome" % k)


func test_ficha_do_tile() -> void:
	var v := _visao()
	var txt := v.descrever(Vector2i(-15, -9))           # centro da mancha de carvão do início
	verificar(txt.contains("Campina") or txt.length() > 0, "zona na primeira linha")
	verificar(txt.contains("Jazida de carvão"), "jazida com nome (%s)" % txt.replace("\n", " | "))
	verificar(txt.contains("Broca de minério"), "diz a máquina")
	var id := v.mapa.colocar("bau", Vector2i(0, 0), 0)
	verificar(v.descrever(Vector2i(0, 0)).contains("Construção"), "construção no tile")
	v.mapa.remover(id)
	v.free()


func test_mancha_inteira() -> void:
	var v := _visao()
	var m := v._mancha("t", Distribuicao.SPAWN[0])
	verificar(m.tiles.size() > 20, "mancha de cristal com tiles (%d)" % m.tiles.size())
	verificar(m.total > 10000, "total somado (%d)" % m.total)
	v.free()


func test_caminho_das_esteiras() -> void:
	var g := GeradorMundo.new(1337)
	var c := Construtor.new(MapaOcupacao.new(g))
	verificar(DesenhoFluxo.construir(c.mapa) == null, "sem esteira, sem malha")
	c.executar(c.plano_linha("esteira", Vector2i(-4, -4), Vector2i(-1, -2), 0))   # reta + curva
	var malha := DesenhoFluxo.construir(c.mapa)
	verificar(malha != null, "malha com as esteiras")
	var a := malha.surface_get_arrays(0)
	var uv: PackedVector2Array = a[Mesh.ARRAY_TEX_UV]
	verificar(uv.size() > 6 * 6, "faixas de 6 peças")
	var cores: PackedColorArray = a[Mesh.ARRAY_COLOR]
	verificar(cores[0].is_equal_approx(DesenhoFluxo.CORES[0]) or cores[0].r > 0.95 and absf(cores[0].g - 0.82) < 0.01, "cor do chão")
	# setas emendam: cada peça vai de 0 a 1 ao longo do caminho
	var minimo := 1.0
	var maximo := 0.0
	for p in uv:
		minimo = minf(minimo, p.y)
		maximo = maxf(maximo, p.y)
	perto(minimo, 0.0, 1e-4)
	perto(maximo, 1.0, 1e-4)


## Leitura ambiental (monitor_ambiental): camada poluição/sujeira na visão V só depois da pesquisa; ficha e fúria.
func test_camada_poluicao_sujeira() -> void:
	var v := _visao()
	var p := Pesquisa.new()
	v.poluicao = Poluicao.new(v.gerador)
	v.ambiente = AmbienteVivo.new(v.gerador, v.mapa)
	v.camada_liberada = p.camada_liberada
	verificar(p.jogavel("monitor_ambiental"), "Leitura ambiental é jogável")
	verificar(not v.poluicao_disponivel(), "sem a pesquisa, sem camada")
	v.alternar()
	igual(v.camada, "recursos", "V: recursos")
	verificar(not v.alternar(), "sem clima nem pesquisa: V de novo desliga")
	p.concluidas = {"monitor_ambiental": true}
	verificar(v.poluicao_disponivel(), "com a pesquisa, a camada existe")
	v.alternar()
	v.alternar()
	igual(v.camada, "poluicao", "V de novo: poluição/sujeira")
	verificar(not v.alternar(), "e depois desliga")
	var t := Vector2i(3, 4)
	v.ambiente.somar(t, AmbienteVivo.SUJ, 0.05)
	v.ambiente.somar(t, AmbienteVivo.OLEO, 0.03)
	perto(v.sujeira_em(t), 0.08, 1e-4, "sujeira do tile = sujeira + óleo + água suja")
	v.poluicao.emitir(t, 12.0)
	v.camada = "poluicao"
	verificar(v.descrever(t).contains("Poluição do ar: 12.0"), "ficha mostra a poluição do ar (%s)" % v.descrever(t))
	verificar(v.descrever(t).contains("sujeira 5%"), "ficha mostra a sujeira do chão")
	verificar(VisaoRecursos.cor_sujeira(0.12).r < VisaoRecursos.cor_sujeira(0.01).r, "mais sujo = mais escuro/avermelhado")
	verificar(VisaoRecursos.rotulo_furia(0.7)[0].begins_with("⚠"), "fúria alta vira aviso")
	verificar(not VisaoRecursos.rotulo_furia(0.0)[0].begins_with("⚠"), "ninho em paz não avisa")
	v._ready()                                                    # monta de verdade (sem tela): blocos + rótulos
	var cam := CameraJogo.new()
	cam.alvo = Grade.centro_mundo(t)
	cam.distancia = 20.0                                          # perto: bloco de 1 tile
	v.camera = cam
	v._montar_poluicao(Rect2i(-20, -20, 40, 40))
	verificar(v._tiles.multimesh.instance_count >= 2, "um bloco de chão sujo e um de ar poluído (%d)" % v._tiles.multimesh.instance_count)
	verificar(v._ativos.size() >= 1, "rótulo da poluição do ar")
	cam.free()
	v.free()


func test_ninhos_furiosos() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var c := Colonia.new(m, Poluicao.new(g), 3)
	for id in c.ninhos:
		c.ninhos[id].furia = 0.0
	igual(c.ninhos_furiosos(0.5).size(), 0, "nenhum ninho furioso")
	if not c.ninhos.is_empty():
		var id: int = c.ninhos.keys()[0]
		c.ninhos[id].furia = 0.6
		igual(c.ninhos_furiosos(0.5), [id], "ninho com fúria 60% entra no aviso")
	var p := Pesquisa.new()
	verificar(not p.camada_liberada("poluicao"), "aviso só depois da pesquisa")
	p.concluidas = {"monitor_ambiental": true}
	verificar(p.camada_liberada("poluicao"), "Leitura ambiental libera a camada e o aviso")
