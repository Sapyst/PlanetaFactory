class_name DesenhoSelecao
extends MeshInstance3D
## Contorno da estrutura selecionada: uma caixa de arestas na altura do modelo + moldura no chão, uma malha só, sem luz, que
## atravessa o que estiver na frente. Não mexe no material da peça (ela é desenhada em lote, com o encardido no shader dela).

const COR := Color(1.0, 0.72, 0.16)
const FOLGA := 0.06            ## folga em volta da pegada
const ARESTA := 0.022          ## meia largura das arestas
const ALTURA_MIN := 0.35       ## peças rasas (esteira) ainda ganham um contorno com volume

var _chave := ""


func _init() -> void:
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := ShaderMaterial.new()
	m.shader = preload("res://render/shaders/selecao.gdshader")
	m.render_priority = 3
	material_override = m
	visible = false


func mostrar(e: Dictionary) -> void:
	var chave := "%s|%s|%s|%s" % [e.nome, e.minimo, e.rot, e.get("nivel", 0)]
	if chave != _chave:
		_chave = chave
		var caixa := caixa_de(e)
		mesh = _malha(caixa.tam)
		position = caixa.pos
	visible = true


func esconder() -> void:
	visible = false
	_chave = ""


## Caixa em torno da estrutura: pos = canto de baixo, no mundo; tam em metros. Tile (i, j) ocupa z de −j−1 a −j.
static func caixa_de(e: Dictionary) -> Dictionary:
	var area: Vector2i = e.get("area", Registro.area(e.nome))
	var a := Grade.area_girada(area, int(e.rot))
	var mn := Vector2(e.minimo)
	var alt := maxf(float(Registro.modelos.get(Construtor.modelo_de(e), Registro.modelos.get(e.nome, {})).get("dims", [0, 0, 0])[2]), ALTURA_MIN)
	var base := Grade.altura_chao(e.minimo) + float(e.get("nivel", 0)) * 0.5
	return {"pos": Vector3(mn.x - FOLGA, base + 0.02, -(mn.y + a.y) - FOLGA), "tam": Vector3(a.x + 2.0 * FOLGA, alt, a.y + 2.0 * FOLGA)}


func _malha(t: Vector3) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var w := ARESTA
	for y in [0.0, t.y]:                                  # retângulos de baixo e de cima
		_barra(st, Vector3(0, y, 0), Vector3(t.x, y, 0), w)
		_barra(st, Vector3(0, y, t.z), Vector3(t.x, y, t.z), w)
		_barra(st, Vector3(0, y, 0), Vector3(0, y, t.z), w)
		_barra(st, Vector3(t.x, y, 0), Vector3(t.x, y, t.z), w)
	for x in [0.0, t.x]:                                  # colunas dos cantos
		for z in [0.0, t.z]:
			_barra(st, Vector3(x, 0, z), Vector3(x, t.y, z), w)
	return st.commit()


## Barra de seção quadrada de a até b (só nos eixos).
func _barra(st: SurfaceTool, a: Vector3, b: Vector3, w: float) -> void:
	var mn := Vector3(minf(a.x, b.x) - w, minf(a.y, b.y) - w, minf(a.z, b.z) - w)
	var mx := Vector3(maxf(a.x, b.x) + w, maxf(a.y, b.y) + w, maxf(a.z, b.z) + w)
	var p := [Vector3(mn.x, mn.y, mn.z), Vector3(mx.x, mn.y, mn.z), Vector3(mx.x, mx.y, mn.z), Vector3(mn.x, mx.y, mn.z),
			Vector3(mn.x, mn.y, mx.z), Vector3(mx.x, mn.y, mx.z), Vector3(mx.x, mx.y, mx.z), Vector3(mn.x, mx.y, mx.z)]
	for f in [[0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7], [1, 5, 6, 2], [3, 2, 6, 7], [4, 5, 1, 0]]:
		for i in [0, 1, 2, 0, 2, 3]:
			st.add_vertex(p[f[i]])
