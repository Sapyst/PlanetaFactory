class_name MarcadorPortas
extends MultiMeshInstance3D
## Marcadores de porta pintados no chão, em lote (uma MultiMesh): um quadrado de listras de construção no tile exato
## onde o item ou o fluido entra ou sai (tile_fora da porta), com a seta do fluxo. O brilho e o corte do oval de visão
## estão no shader. Usado pelo aviso de porta solta (DesenhoPortas) e pelo fantasma (verde/vermelho).

const VERMELHO := Color(0.66, 0.012, 0.01)     ## cor crua do shader sem luz (linear): vermelho de verdade, não salmão
const VERDE := Color(0.02, 0.50, 0.10)
const LADO := 0.92                         ## cabe no tile sem encostar nos vizinhos
const ALTURA := 0.05                       ## acima do chão; o resto do desempate é o viés de profundidade do shader

static var _malha: PlaneMesh
static var _material: ShaderMaterial


func _init() -> void:
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	multimesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	multimesh.use_custom_data = true
	if _malha == null:
		_malha = PlaneMesh.new()
		_malha.size = Vector2(LADO, LADO)
		_material = ShaderMaterial.new()
		_material.shader = preload("res://render/shaders/marcador_porta.gdshader")
		_material.render_priority = 2
	multimesh.mesh = _malha
	material_override = _material


## lista: [{tile_fora: Vector2i, dir: Vector2i (para fora da estrutura), io: "ENT"/"SAI", tipo: "ITEM"/"FLUIDO", cor?: Color}].
func definir(lista: Array) -> void:
	multimesh.instance_count = lista.size()
	for i in lista.size():
		var it: Dictionary = lista[i]
		multimesh.set_instance_transform(i, transform_de(it))
		multimesh.set_instance_color(i, it.get("cor", VERMELHO))
		multimesh.set_instance_custom_data(i, Color(1.0 if it.get("tipo", "ITEM") == "FLUIDO" else 0.0, 0, 0, 0))
	visible = not lista.is_empty()


## Onde o quadrado fica: centro do tile da porta, com a seta (−Z local) no sentido do fluxo.
static func transform_de(it: Dictionary) -> Transform3D:
	var fluxo := direcao_fluxo(Vector2i(it.dir), String(it.io))
	return Transform3D(Basis(Vector3.UP, atan2(-float(fluxo.x), float(fluxo.y))), Grade.centro_mundo(it.tile_fora, ALTURA))


## Sentido em que o recurso anda: a saída vai para fora da estrutura; a entrada, para dentro.
static func direcao_fluxo(dir: Vector2i, io: String) -> Vector2i:
	return dir if io == "SAI" else -dir
