class_name DesenhoClimaLocal
extends Node3D
## Desenha o clima das máquinas de clima (só lê ClimaLocal e Raios), sempre no mundo — nada de filtro de tela:
##  - cúpula contra raios: meia esfera de campo no raio dela (shader campo_escudo, quase invisível: só a borda e a
##    trama fraca), que acende quando pega um raio (o contador de descargas da cúpula mudou);
##  - semeador de nuvens (e regulador em chuva): chuva de verdade só dentro do círculo — partículas num anel do raio
##    da máquina, a ~22 m de altura, com o mesmo risco 3D da chuva do clima; some quando já chove mais que isso.

const CAMPO := preload("res://render/shaders/campo_escudo.gdshader")
const GOTAS_PC := 1400
const GOTAS_CELULAR := 350
const ALTURA_CHUVA := 22.0

var clima_local: ClimaLocal
var raios: Raios
var camera: CameraJogo
var clima: Clima
var _cupulas: Dictionary = {}      ## id → {no, mat, impacto, descargas}
var _chuvas: Dictionary = {}       ## id → GPUParticles3D


func _process(delta: float) -> void:
	if clima_local == null:
		return
	var vivas := {}
	var chovendo := {}
	for z in clima_local.zonas:
		var id: int = z.id
		if z.tipo == "cupula":
			vivas[id] = true
			_cupula(id, z, delta)
		elif z.tipo == "chuva" or (z.tipo == "regulador" and z.modo == "chuva"):
			chovendo[id] = true
			_chuva(id, z)
	for id in _cupulas.keys():
		if not vivas.has(id):
			(_cupulas[id].no as Node).queue_free()
			_cupulas.erase(id)
	for id in _chuvas.keys():
		if not chovendo.has(id):
			(_chuvas[id] as Node).queue_free()
			_chuvas.erase(id)


func _perto(c: Vector2, r: float) -> bool:
	if camera == null:
		return true
	return Vector2(camera.alvo.x - c.x, -camera.alvo.z - c.y).length() < r + camera.distancia * 2.5


func _cupula(id: int, z: Dictionary, delta: float) -> void:
	var r := float(z.raio)
	if not _cupulas.has(id):
		var esf := SphereMesh.new()
		esf.radius = r
		esf.height = r
		esf.is_hemisphere = true
		esf.radial_segments = 64
		esf.rings = 20
		var m := ShaderMaterial.new()
		m.shader = CAMPO
		m.set_shader_parameter("escala_hex", 6.0)
		var no := MeshInstance3D.new()
		no.mesh = esf
		no.material_override = m
		no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(no)
		no.position = Grade.ponto_mundo(z.centro, 0.0)
		_cupulas[id] = {"no": no, "mat": m, "impacto": 0.0, "descargas": _descargas(id)}
	var c: Dictionary = _cupulas[id]
	var n := _descargas(id)
	if n != int(c.descargas):
		c.descargas = n
		c.impacto = 1.0
	c.impacto = maxf(0.0, float(c.impacto) - delta * 1.6)
	(c.no as Node3D).visible = _perto(z.centro, r)
	(c.mat as ShaderMaterial).set_shader_parameter("forca", 0.22 + 0.6 * float(c.impacto))
	(c.mat as ShaderMaterial).set_shader_parameter("impacto", float(c.impacto))


func _descargas(id: int) -> int:
	return int(raios.descargas.get(id, 0)) if raios != null else 0


func _chuva(id: int, z: Dictionary) -> void:
	var r := float(z.raio)
	if not _chuvas.has(id):
		_chuvas[id] = _criar_chuva(r)
		(_chuvas[id] as Node3D).position = Grade.ponto_mundo(z.centro, ALTURA_CHUVA)
	var p: GPUParticles3D = _chuvas[id]
	var global := float(clima.valores.chuva) if clima != null else 0.0
	var local := float(z.regra.get("chuva", 0.75)) if z.tipo == "chuva" else float(z.regra.get("chuva", 0.4))
	p.emitting = _perto(z.centro, r) and global < local - 0.05
	p.amount_ratio = clampf(local - global, 0.1, 1.0)
	if clima != null:          # o vento inclina as gotas, como na chuva do clima
		var v := clima.direcao_vento * (0.5 + float(clima.valores.vento)) * 3.0
		(p.process_material as ParticleProcessMaterial).gravity = Vector3(v.x, -9.8, -v.y)


func _criar_chuva(r: float) -> GPUParticles3D:
	var celular := OS.has_feature("mobile")
	var p := GPUParticles3D.new()
	p.amount = GOTAS_CELULAR if celular else GOTAS_PC
	p.lifetime = 1.15
	p.local_coords = false
	p.visibility_aabb = AABB(Vector3(-r - 5, -ALTURA_CHUVA - 5, -r - 5), Vector3(2 * r + 10, ALTURA_CHUVA + 10, 2 * r + 10))
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
	pm.emission_ring_axis = Vector3.UP
	pm.emission_ring_radius = r
	pm.emission_ring_inner_radius = 0.0
	pm.emission_ring_height = 2.0
	pm.direction = Vector3.DOWN
	pm.spread = 2.0
	pm.initial_velocity_min = 15.0
	pm.initial_velocity_max = 19.0
	pm.gravity = Vector3(0, -9.8, 0)
	pm.particle_flag_align_y = true
	p.process_material = pm
	var gota := BoxMesh.new()
	gota.size = Vector3(0.014, 0.5, 0.014)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(0.78, 0.82, 0.88, 0.32)
	gota.material = m
	p.draw_pass_1 = gota
	add_child(p)
	return p


## Quantas cúpulas e chuvas locais estão desenhadas (testes).
func contagem() -> Dictionary:
	return {"cupulas": _cupulas.size(), "chuvas": _chuvas.size()}
