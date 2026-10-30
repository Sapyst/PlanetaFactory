class_name DesenhoSilo
extends Node3D
## Foguete de proliferação no silo de lançamento (SiloLancamento): cresce no poço com as partes montadas (fuselagem,
## ogiva com o cristal de navegação quando a carga-semente está dentro) e sobe acelerando no lançamento, com a chama
## e uma luz embaixo. Só lê o SiloLancamento.

const ALTURA_MAX := 3.2               ## fuselagem com as 100 partes (m)
const RAIO := 0.32

var silo: SiloLancamento
var _foguetes: Dictionary = {}        ## id → Node3D
var _mat_casco: StandardMaterial3D
var _mat_cristal: StandardMaterial3D
var _mat_chama: StandardMaterial3D


func _materiais() -> void:
	_mat_casco = StandardMaterial3D.new()
	_mat_casco.albedo_color = Color(0.78, 0.76, 0.70)
	_mat_casco.metallic = 0.5
	_mat_casco.roughness = 0.4
	_mat_cristal = StandardMaterial3D.new()
	_mat_cristal.albedo_color = Color(0.15, 0.85, 0.95)
	_mat_cristal.emission_enabled = true
	_mat_cristal.emission = Color(0.15, 0.85, 0.95)
	_mat_cristal.emission_energy_multiplier = 3.0
	_mat_chama = StandardMaterial3D.new()
	_mat_chama.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_chama.albedo_color = Color(1.0, 0.6, 0.2)


func _novo() -> Node3D:
	var n := Node3D.new()
	var corpo := MeshInstance3D.new()
	corpo.name = "fuselagem"
	var c := CylinderMesh.new()
	c.top_radius = RAIO
	c.bottom_radius = RAIO
	c.height = 1.0
	corpo.mesh = c
	corpo.material_override = _mat_casco
	n.add_child(corpo)
	var ogiva := MeshInstance3D.new()
	ogiva.name = "ogiva"
	var o := CylinderMesh.new()
	o.top_radius = 0.0
	o.bottom_radius = RAIO
	o.height = 0.7
	ogiva.mesh = o
	ogiva.material_override = _mat_cristal
	n.add_child(ogiva)
	var chama := MeshInstance3D.new()
	chama.name = "chama"
	var ch := CylinderMesh.new()
	ch.top_radius = RAIO * 0.9
	ch.bottom_radius = 0.05
	ch.height = 2.2
	chama.mesh = ch
	chama.material_override = _mat_chama
	chama.position = Vector3(0, -1.1, 0)
	n.add_child(chama)
	var l := OmniLight3D.new()
	l.name = "luz"
	l.light_color = Color(1.0, 0.6, 0.25)
	l.omni_range = 14.0
	l.light_energy = 4.0
	l.position = Vector3(0, -0.8, 0)
	n.add_child(l)
	add_child(n)
	return n


func _process(_delta: float) -> void:
	if silo == null:
		return
	if _mat_casco == null:
		_materiais()
	var vivos := {}
	for id in silo.todos():
		vivos[id] = true
		if not _foguetes.has(id):
			_foguetes[id] = _novo()
		var n: Node3D = _foguetes[id]
		var r := SiloLancamento.regra(silo.mapa.estruturas[id].nome)
		var f := clampf(float(silo.partes(id)) / float(r.get("partes", 100)), 0.0, 1.0)
		var lanc := silo.lancando.has(id)
		n.visible = f > 0.0 or lanc
		if not n.visible:
			continue
		var h := maxf(ALTURA_MAX * f, 0.2)
		var e: Dictionary = silo.mapa.estruturas[id]
		n.position = Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot), 0.3 + silo.subida(id))
		var corpo := n.get_node("fuselagem") as MeshInstance3D
		(corpo.mesh as CylinderMesh).height = h
		corpo.position = Vector3(0, h * 0.5, 0)
		var ogiva := n.get_node("ogiva") as MeshInstance3D
		ogiva.visible = silo.tem_carga(id) or lanc
		ogiva.position = Vector3(0, h + 0.35, 0)
		(n.get_node("chama") as Node3D).visible = lanc and float(silo.lancando[id]) > 0.8
		(n.get_node("luz") as Node3D).visible = lanc and float(silo.lancando[id]) > 0.8
	for id in _foguetes.keys():
		if not vivos.has(id):
			(_foguetes[id] as Node3D).queue_free()
			_foguetes.erase(id)


## Foguetes à vista (testes e roteiro).
func visiveis() -> int:
	return _foguetes.values().filter(func(n: Node3D): return n.visible).size()
