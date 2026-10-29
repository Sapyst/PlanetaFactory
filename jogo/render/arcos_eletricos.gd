class_name ArcosEletricos
extends MeshInstance3D
## Faíscas do acumulador: arcos curtos e quebrados entre o topo das quatro bobinas e o cristal do meio.
## Quanto mais carga guardada (e mais ainda carregando/descarregando), mais arcos por segundo.
## Cada arco é uma fita em cruz (duas faixas perpendiculares: tem corpo de qualquer ângulo, sem virar para a câmera),
## vive ~0,1 s. Tudo numa ImmediateMesh só, com o shader aditivo de raio (render/shaders/raio.gdshader): núcleo
## branco acima de 1 (o bloom pega) e halo ciano largo em malha (brilha mesmo sem bloom, no celular). Uma luz ciano
## pisca no arco mais novo e ilumina o chão em volta; cada arco novo estala (som "faisca").

## Pontas no espaço do modelo (Godot: x, y para cima, z = −y do Blender): topo das bobinas e ponta do cristal.
const BOBINAS: Array[Vector3] = [Vector3(-0.40, 1.19, -0.40), Vector3(0.40, 1.19, -0.40), Vector3(0.40, 1.19, 0.40), Vector3(-0.40, 1.19, 0.40)]
const CRISTAL := Vector3(0.0, 1.62, -0.04)
const LARGURA := 0.014
const HALO := 0.07
const COR_NUCLEO := Color(0.92, 1.0, 1.0, 1.0)
const COR_HALO := Color(0.25, 0.95, 0.85, 0.12)

## id → {no: Node3D, forca: 0..1}; o mundo atualiza todo quadro
var fontes: Dictionary = {}
var _arcos: Array = []               ## {a, b, vida, no}
var _malha := ImmediateMesh.new()
var _rng := RandomNumberGenerator.new()
var _luz := OmniLight3D.new()


func _ready() -> void:
	mesh = _malha
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := ShaderMaterial.new()
	m.shader = preload("res://render/shaders/raio.gdshader")
	material_override = m
	extra_cull_margin = 1.0e4
	top_level = true
	_luz.light_color = Color(0.55, 1.0, 0.92)
	_luz.omni_range = 3.2
	_luz.shadow_enabled = false
	_luz.visible = false
	add_child(_luz)


func _process(delta: float) -> void:
	for id in fontes:
		var f: Dictionary = fontes[id]
		var no: Node3D = f.no
		if not is_instance_valid(no) or not no.is_visible_in_tree():
			continue
		if _rng.randf() < delta * 7.0 * float(f.forca):
			var i := _rng.randi() % 4
			var b: Vector3 = CRISTAL if _rng.randf() < 0.6 else BOBINAS[(i + (1 if _rng.randf() < 0.5 else 3)) % 4]
			_arcos.append({"a": BOBINAS[i], "b": b, "vida": _rng.randf_range(0.06, 0.16), "no": no})
			Som.tocar("faisca", no.global_position + Vector3.UP, -8.0)
	for k in range(_arcos.size() - 1, -1, -1):
		_arcos[k].vida -= delta
		if _arcos[k].vida <= 0.0 or not is_instance_valid(_arcos[k].no):
			_arcos.remove_at(k)
	_malha.clear_surfaces()
	_luz.visible = not _arcos.is_empty()
	if _arcos.is_empty():
		return
	var ultimo: Dictionary = _arcos[-1]
	var tu: Transform3D = (ultimo.no as Node3D).global_transform
	_luz.global_position = tu * (((ultimo.a as Vector3) + (ultimo.b as Vector3)) * 0.5)
	_luz.light_energy = _rng.randf_range(1.2, 3.0)               # tremula como arco de verdade
	_malha.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for arco in _arcos:
		var t: Transform3D = (arco.no as Node3D).global_transform
		_desenhar(t * (arco.a as Vector3), t * (arco.b as Vector3))
	_malha.surface_end()


## Linha quebrada de a até b (arqueada para cima, desvios ao acaso), em fita cruzada.
func _desenhar(a: Vector3, b: Vector3) -> void:
	var n := 6
	var d := b - a
	var lado := d.cross(Vector3.UP).normalized()
	if lado.length() < 0.5:
		lado = Vector3.RIGHT
	var cima := lado.cross(d).normalized()
	var pts: Array[Vector3] = []
	for i in n + 1:
		var s := float(i) / n
		var p := a + d * s + Vector3.UP * sin(s * PI) * 0.08
		if i > 0 and i < n:
			p += lado * _rng.randf_range(-0.05, 0.05) + cima * _rng.randf_range(-0.05, 0.05)
		pts.append(p)
	for camada in [[HALO, COR_HALO], [LARGURA, COR_NUCLEO]]:
		_malha.surface_set_color(camada[1])
		for i in n:
			var p0 := pts[i]
			var p1 := pts[i + 1]
			for eixo in [lado, cima]:
				var w: Vector3 = eixo * float(camada[0])
				for v in [p0 - w, p0 + w, p1 + w, p0 - w, p1 + w, p1 - w]:
					_malha.surface_add_vertex(v)
