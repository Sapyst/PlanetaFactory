class_name DesenhoLancador
extends Node3D
## Lançador de sementes (Lancador) no mapa: a cápsula-semente em voo (ogiva com a ponta de cristal acesa e uma luz
## fraca) no arco até o alvo, e o alvo de cada lançador marcado no chão (anel violeta). Também as cápsulas das
## colônias (Genese) voando até o receptor (sai a 3 m do chão e desce no funil, a 1,2 m). Só lê o Lancador e a Genese.

const COR := Color(0.62, 0.32, 1.0)

var lancador: Lancador
var genese: Genese                     ## (opcional) cápsulas de pacote gênese das colônias
var _capsulas: Array[Node3D] = []
var _alvos: Array[MeshInstance3D] = []
var _mat_corpo: StandardMaterial3D
var _mat_cristal: StandardMaterial3D
var _mat_alvo: StandardMaterial3D


func _materiais() -> void:
	_mat_corpo = StandardMaterial3D.new()
	_mat_corpo.albedo_color = Color(0.42, 0.42, 0.44)
	_mat_corpo.metallic = 0.6
	_mat_corpo.roughness = 0.45
	_mat_cristal = StandardMaterial3D.new()
	_mat_cristal.albedo_color = COR
	_mat_cristal.emission_enabled = true
	_mat_cristal.emission = COR
	_mat_cristal.emission_energy_multiplier = 3.0
	_mat_alvo = StandardMaterial3D.new()
	_mat_alvo.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_alvo.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat_alvo.albedo_color = Color(COR, 0.65)


func _nova_capsula() -> Node3D:
	var n := Node3D.new()
	var corpo := MeshInstance3D.new()
	var cil := CapsuleMesh.new()
	cil.radius = 0.22
	cil.height = 1.1
	corpo.mesh = cil
	corpo.material_override = _mat_corpo
	corpo.rotation.x = PI / 2.0                    # deitada no eixo −Z local (o look_at aponta −Z para o rumo)
	n.add_child(corpo)
	var ponta := MeshInstance3D.new()
	var pr := PrismMesh.new()
	pr.size = Vector3(0.3, 0.4, 0.3)
	ponta.mesh = pr
	ponta.material_override = _mat_cristal
	ponta.position = Vector3(0, 0, -0.6)
	ponta.rotation.x = -PI / 2.0
	n.add_child(ponta)
	var l := OmniLight3D.new()
	l.light_color = COR
	l.omni_range = 4.0
	l.light_energy = 1.5
	n.add_child(l)
	add_child(n)
	return n


func _process(_delta: float) -> void:
	if lancador == null:
		return
	if _mat_corpo == null:
		_materiais()
	var voos: Array = lancador.voos.duplicate()
	if genese != null:
		voos.append_array(genese.voos)
	while _capsulas.size() < voos.size():
		_capsulas.append(_nova_capsula())
	for i in _capsulas.size():
		var n := _capsulas[i]
		n.visible = i < voos.size()
		if not n.visible:
			continue
		var v: Dictionary = voos[i]
		var p := Lancador.posicao_no_voo(v)
		var pos := _no_mundo(v, p)
		var v2: Dictionary = v.duplicate()
		v2.t = float(v.t) + 0.05
		var frente := _no_mundo(v2, Lancador.posicao_no_voo(v2))
		n.position = pos
		if frente.distance_to(pos) > 1e-4 and absf((frente - pos).normalized().dot(Vector3.UP)) < 0.999:
			n.look_at_from_position(pos, frente, Vector3.UP)
	# alvos: um anel por lançador
	var ids := lancador.lancadores.keys()
	while _alvos.size() < ids.size():
		var a := MeshInstance3D.new()
		var anel := TorusMesh.new()
		anel.inner_radius = 2.0
		anel.outer_radius = 2.4
		a.mesh = anel
		a.material_override = _mat_alvo
		add_child(a)
		_alvos.append(a)
	for i in _alvos.size():
		_alvos[i].visible = i < ids.size()
		if _alvos[i].visible and lancador.mapa.estruturas.has(ids[i]):
			_alvos[i].position = Grade.ponto_mundo(lancador.alvo(ids[i]), 0.15)


## Ponto do voo no mundo: o arco (z) sobre a reta que vai de 3 m acima da saída a 1,2 m acima da chegada.
static func _no_mundo(v: Dictionary, p: Vector3) -> Vector3:
	var f := clampf(float(v.t) / maxf(float(v.total), 1e-6), 0.0, 1.0)
	var base := lerpf(Grade.altura_em(v.de) + 3.0, Grade.altura_em(v.para) + 1.2, f)
	return Vector3(p.x, base + p.z, -p.y)


## Cápsulas no ar e alvos marcados (testes e roteiro).
func contagem() -> Dictionary:
	return {"capsulas": _capsulas.filter(func(n: Node3D): return n.visible).size(),
			"alvos": _alvos.filter(func(n: Node3D): return n.visible).size()}
