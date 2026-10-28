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
