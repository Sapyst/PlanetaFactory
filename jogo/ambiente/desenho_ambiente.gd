class_name DesenhoAmbiente
extends Node3D
## Desenha o AmbienteVivo: manda o mapa de cada chunk mudado para o chão (1×/s), e o fogo — chamas e fumaça só nos
## focos perto da câmera (limite fixo de emissores, reaproveitados).

const MAX_CHAMAS := 36

var ambiente: AmbienteVivo
var chunks: Dictionary              ## o dicionário de chunks do mundo (DesenhoChunk)
var camera: CameraJogo
var _t := 0.0
var _chamas: Array[CPUParticles3D] = []
var _fumacas: Array[CPUParticles3D] = []
var _som_t := 0.0
var _t_fogo := 0.0


func _ready() -> void:
	for i in MAX_CHAMAS:
		var c := CPUParticles3D.new()
		c.amount = 10
		c.lifetime = 0.7
		c.local_coords = false
		c.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
		c.emission_box_extents = Vector3(0.38, 0.02, 0.38)
		c.direction = Vector3.UP
		c.spread = 10.0
		c.initial_velocity_min = 0.8
		c.initial_velocity_max = 1.6
		c.gravity = Vector3(0, 1.2, 0)
		# línguas de fogo: quad alto e fino, de pé (gira só em Y), textura de chama desenhada por código, luz somada
		var q := QuadMesh.new()
		q.size = Vector2(0.35, 0.7)
		q.center_offset = Vector3(0, 0.35, 0)
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
		mat.vertex_color_use_as_albedo = true
		mat.albedo_texture = _tex_chama()
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		q.material = mat
		c.mesh = q
		c.amount = 14
		c.lifetime = 0.55
		c.initial_velocity_min = 0.2
		c.initial_velocity_max = 0.5
		c.gravity = Vector3(0, 0.6, 0)
		c.scale_amount_min = 0.6
		c.scale_amount_max = 1.2
		var curva := Curve.new()
		curva.add_point(Vector2(0, 0.5))
		curva.add_point(Vector2(0.3, 1.0))
		curva.add_point(Vector2(1, 0.2))
		c.scale_amount_curve = curva
		var g := Gradient.new()
		g.set_color(0, Color(1.3, 0.9, 0.35, 0.0))
		g.add_point(0.15, Color(1.4, 0.55, 0.12, 1.0))
		g.set_color(1, Color(0.9, 0.18, 0.03, 0.0))
		c.color_ramp = g
		c.emitting = false
		add_child(c)
		_chamas.append(c)
		var f := CPUParticles3D.new()
		f.amount = 8
		f.lifetime = 3.0
		f.local_coords = false
		f.direction = Vector3(0.2, 1, 0)
		f.spread = 15.0
		f.initial_velocity_min = 0.6
		f.initial_velocity_max = 1.1
		f.gravity = Vector3(0.3, 0.2, 0)
		Fumaca.configurar(f, [Color(0.12, 0.11, 0.10, 0.0), Color(0.14, 0.13, 0.12, 0.7), Color(0.35, 0.33, 0.32, 0.0)], 0.8, 1.3, 3.4)
		f.emitting = false
		add_child(f)
		_fumacas.append(f)


## Chama: gota alta com base larga e ponta fina, recortada por ruído (labaredas), mais clara no miolo.
func _tex_chama() -> Texture2D:
	var w := 32
	var h := 64
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var ruido := FastNoiseLite.new()
	ruido.frequency = 0.12
	for y in h:
		for x in w:
			var v := 1.0 - float(y) / h                   # 0 embaixo… 1 em cima (imagem: y cresce para baixo)
			var u := (x + 0.5) / w * 2.0 - 1.0
			var larg := 0.85 * pow(1.0 - v, 0.7) * (0.75 + 0.25 * ruido.get_noise_2d(x * 2.0, y))
			var d := absf(u) / maxf(larg, 0.01)
			var a := clampf(1.0 - d, 0.0, 1.0) * smoothstep(0.0, 0.08, 1.0 - v) * smoothstep(1.0, 0.85, v + 0.1)
			a = pow(a, 0.8)
			var miolo := clampf(1.0 - d * 1.6, 0.0, 1.0) * (1.0 - v)
			img.set_pixel(x, y, Color(1.0, 0.75 + 0.25 * miolo, 0.4 + 0.6 * miolo, a))
	return ImageTexture.create_from_image(img)


func _process(delta: float) -> void:
	if ambiente == null:
		return
	_t -= delta
	if _t <= 0.0:
		_t = 1.0
		for k in ambiente.sujos.keys():
			if chunks.has(k):
				(chunks[k] as DesenhoChunk).atualizar_ambiente(ambiente.imagem(k))
				ambiente.sujos.erase(k)
	_t_fogo -= delta
	if _t_fogo <= 0.0:
		_t_fogo = 0.25
		_atualizar_fogo()
	if not ambiente.fogo.is_empty():
		_som_t -= delta
		if _som_t <= 0.0:
			_som_t = 2.2
			Som.tocar("fogo", Vector3.INF, -10.0)


func _atualizar_fogo() -> void:
	var olho := Vector2(camera.alvo.x, -camera.alvo.z)
	var lista: Array = ambiente.fogo.keys()
	lista.sort_custom(func(a, b): return Vector2(a).distance_squared_to(olho) < Vector2(b).distance_squared_to(olho))
	for i in MAX_CHAMAS:
		var ligar := i < lista.size() and Vector2(lista[i]).distance_to(olho) < camera.distancia * 1.4
		_chamas[i].emitting = ligar
		_fumacas[i].emitting = ligar
		if ligar:
			var p := Grade.centro_mundo(lista[i], 0.05)
			_chamas[i].global_position = p
			_fumacas[i].global_position = p + Vector3(0, 0.4, 0)
