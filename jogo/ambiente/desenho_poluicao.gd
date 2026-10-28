class_name DesenhoPoluicao
extends MultiMeshInstance3D
## Camada de poluição (liga/desliga): um quadrado roxo por chunk sujo, mais opaco quanto mais poluído
## (escala log). Atualiza 2× por segundo — a nuvem anda devagar.

var poluicao: Poluicao
var _t := 0.0


func _ready() -> void:
	var q := PlaneMesh.new()
	q.size = Vector2(Grade.TAM_CHUNK, Grade.TAM_CHUNK)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.vertex_color_use_as_albedo = true
	m.no_depth_test = false
	q.material = m
	multimesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	multimesh.mesh = q
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	visible = false


func _process(delta: float) -> void:
	if not visible or poluicao == null:
		return
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.5
	var ks := poluicao.valores.keys()
	multimesh.instance_count = ks.size()
	for i in ks.size():
		var k: Vector2i = ks[i]
		var v: float = poluicao.valores[k]
		var c := Grade.ponto_mundo(Vector2(k * Grade.TAM_CHUNK) + Vector2.ONE * Grade.TAM_CHUNK / 2.0, 0.06)
		multimesh.set_instance_transform(i, Transform3D(Basis(), c))
		multimesh.set_instance_color(i, Color(0.62, 0.25, 0.85, clampf(log(1.0 + v) / 8.0, 0.0, 0.45)))
