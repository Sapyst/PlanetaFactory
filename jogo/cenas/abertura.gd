class_name Abertura
extends Node3D
## Abertura do jogo novo (~13 s; qualquer toque/tecla pula): o núcleo — a unidade semeadora da IA — chega do
## espaço. Preso sob uma nave, desacopla, cai atravessando as nuvens com rastro de calor, bate no chão (estrondo,
## poeira, tremor), se acomoda; poucas linhas de sistema aparecem e a câmera desce até a visão de jogo.
## Só referência, sem história longa: a IA é um erro que segue a diretriz de proliferar.

signal terminou

const ALTURA := 140.0
const T_SOLTA := 2.4
const T_QUEDA := 5.0
const T_TEXTO := 8.0
const T_CAMERA := 11.6
const T_FIM := 13.6
const LINHAS := ["UNIDADE SEMEADORA 7 · CHEGADA CONFIRMADA", "DIRETRIZ: PROLIFERAR",
		"ERRO 0x1F · limite da diretriz não encontrado", "…prosseguindo."]

var nucleo: Node3D
var camera_jogo: Camera3D
var barra: Node             ## barra de construção (escondida durante a abertura)

var _t := 0.0
var _final := Vector3.ZERO
var _cam: Camera3D
var _nave: Node3D
var _rastro: CPUParticles3D
var _luz: OmniLight3D
var _poeira: CPUParticles3D
var _nuvens: Array[Sprite3D] = []
var _texto: Label
var _veu: ColorRect
var _impacto := false
var _som_queda := false
var _tremor := 0.0
var _pulando := false
var _cam_segura := Transform3D()
var _env: Environment
var _ceu: ProceduralSkyMaterial
var _guardado := {}


func _ready() -> void:
	_final = nucleo.position
	_cam = Camera3D.new()
	_cam.fov = 50.0
	_cam.far = 900.0
	add_child(_cam)
	_cam.make_current()
	if barra != null:
		barra.set("visible", false)
	_criar_nave()
	_criar_nuvens()
	_criar_efeitos()
	_criar_tela()
	# lá do alto, o que ainda não carregou some na névoa de altitude (céu "de baixo" com a cor da névoa)
	var amb := get_tree().current_scene.get_node_or_null("Ambiente") as WorldEnvironment
	if amb != null:
		_env = amb.environment
		_ceu = _env.sky.sky_material as ProceduralSkyMaterial if _env.sky != null else null
		_guardado = {"densidade": _env.fog_density, "cor": _env.fog_light_color}
		if _ceu != null:
			_guardado["chao"] = _ceu.ground_bottom_color
			_guardado["horizonte"] = _ceu.ground_horizon_color
			_ceu.ground_bottom_color = Color(0.62, 0.67, 0.72)
			_ceu.ground_horizon_color = Color(0.70, 0.74, 0.78)
	_posicionar(0.0)


func _input(e: InputEvent) -> void:
	if _pulando or _t < 0.6:
		return
	var aperto: bool = (e is InputEventKey and e.pressed) or (e is InputEventMouseButton and e.pressed) or (e is InputEventScreenTouch and e.pressed)
	if aperto:
		_pulando = true                                    # pula: núcleo no lugar e a câmera desce rápido
		_t = maxf(_t, T_CAMERA + 1.4)
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_t += delta
	_posicionar(delta)
	if _t >= T_FIM:
		_acabar()


func _posicionar(delta: float) -> void:
	var t := _t
	var u := clampf((t - T_SOLTA) / T_QUEDA, 0.0, 1.0)
	var deriva := Vector3(-30.0 + 6.0 * t, 0, -6.0)            # a nave passa devagar
	var nave_pos := _final + Vector3(0, ALTURA, 0) + deriva
	_nave.position = nave_pos + Vector3(0, maxf(0.0, t - T_SOLTA) * maxf(0.0, t - T_SOLTA) * 1.2, 0)
	# núcleo: preso sob a nave, depois cai acelerando e se endireita antes do chão
	var solto := nave_pos + Vector3(0, -3.6, 0)
	if t < T_SOLTA or _pulando and u < 1.0 and false:
		nucleo.position = solto
		nucleo.rotation = Vector3.ZERO
	elif u < 1.0 and not _pulando:
		var y := lerpf(solto.y, _final.y, pow(u, 1.8))
		var xz := Vector2(solto.x, solto.z).lerp(Vector2(_final.x, _final.z), 1.0 - pow(1.0 - u, 2.2))
		nucleo.position = Vector3(xz.x, y, xz.y)
		var gira := (1.0 - smoothstep(0.7, 0.95, u))
		nucleo.rotation = Vector3(sin(t * 1.7) * 0.25, t * 0.9, cos(t * 1.3) * 0.2) * gira
		_rastro.emitting = u > 0.12 and u < 0.97
		_luz.light_energy = 6.0 * smoothstep(0.15, 0.4, u) * (1.0 - smoothstep(0.85, 0.98, u))
		if not _som_queda:
			_som_queda = true
			Som.tocar("reentrada", Vector3.INF, -2.0)
	else:
		nucleo.position = _final
		nucleo.rotation = Vector3.ZERO
		_rastro.emitting = false
		_luz.light_energy = 0.0
		if not _impacto:
			_impacto = true
			if not _pulando:
				_bater()
	_rastro.global_position = nucleo.global_position + Vector3(0, 1.2, 0)
	_luz.global_position = nucleo.global_position + Vector3(0, 1.0, 0)
	# acomodar: quica de leve
	var tq := t - (T_SOLTA + T_QUEDA)
	if tq > 0.0 and tq < 1.4 and not _pulando:
		var s := 1.0 + sin(tq * 9.0) * 0.08 * exp(-tq * 3.0)
		nucleo.scale = Vector3(1.0 / s, s, 1.0 / s)
	else:
		nucleo.scale = Vector3.ONE
	_camera(t, u, delta)
	_tela(t)
	if _env != null:
		var alto := clampf((_cam.global_position.y - _final.y) / 120.0, 0.0, 1.0)
		var volta := smoothstep(T_SOLTA + T_QUEDA, T_CAMERA, t_atual())       # perto do chão volta à névoa do jogo
		_env.fog_density = lerpf(lerpf(0.004, 0.022, alto), float(_guardado.densidade), volta)
		_env.fog_light_color = Color(0.66, 0.72, 0.78)


func _camera(t: float, u: float, delta: float) -> void:
	var olho: Vector3
	var mira: Vector3
	if t < T_SOLTA + 0.3:
		olho = _nave.position + Vector3(26, 3, 20)
		mira = nucleo.position + Vector3(0, 1.5, 0)
	elif u < 0.86:
		var ang := t * 0.25
		olho = nucleo.position + Vector3(cos(ang) * 16.0, 7.0, sin(ang) * 16.0)
		mira = nucleo.position
	else:
		if _cam_segura == Transform3D():
			_cam_segura = _cam.global_transform
		olho = _final + Vector3(15, 9, 17)                  # espera o impacto de um ponto fixo
		mira = _final + Vector3(0, 1.0, 0)
	if t > T_CAMERA:
		var k := smoothstep(T_CAMERA, T_FIM - 0.3, t)
		var alvo := camera_jogo.global_transform
		var de := Transform3D(Basis.looking_at(mira - olho), olho)
		_cam.global_transform = de.interpolate_with(alvo, k)
	else:
		_cam.global_position = _cam.global_position.lerp(olho, 1.0 - exp(-6.0 * delta)) if delta > 0.0 and t > T_SOLTA + 0.3 else olho
		_cam.look_at(mira)
	if _tremor > 0.0:
		_tremor = maxf(0.0, _tremor - delta * 1.6)
		_cam.global_position += Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * 0.35 * _tremor


func _bater() -> void:
	Som.tocar("impacto", Vector3.INF, 0.0)
	_tremor = 1.0
	_poeira.global_position = _final + Vector3(0, 0.3, 0)
	_poeira.restart()
	_poeira.emitting = true
	_veu.color = Color(1, 0.95, 0.85, 0.55)


func _tela(t: float) -> void:
	# entra do preto; clarão do impacto some rápido
	if t < 0.8:
		_veu.color = Color(0, 0, 0, 1.0 - t / 0.8)
	elif _veu.color.a > 0.0 and _veu.color.r > 0.5:
		_veu.color.a = maxf(0.0, _veu.color.a - get_process_delta_time() * 2.5)
	elif t >= 0.8 and _veu.color.r < 0.5:
		_veu.color.a = 0.0
	# linhas de sistema digitadas
	if t > T_TEXTO and not _pulando:
		var cps := 38.0
		var total := int((t - T_TEXTO) * cps)
		var txt := ""
		for l in LINHAS:
			if total <= 0:
				break
			txt += l.substr(0, total) + "\n"
			total -= l.length() + 6
		_texto.text = txt
		_texto.modulate.a = 1.0 - smoothstep(T_CAMERA + 0.8, T_FIM - 0.2, t)


func t_atual() -> float:
	return _t


func _acabar() -> void:
	if _env != null:
		_env.fog_density = _guardado.densidade
		_env.fog_light_color = _guardado.cor
		if _ceu != null:
			_ceu.ground_bottom_color = _guardado.chao
			_ceu.ground_horizon_color = _guardado.horizonte
	nucleo.position = _final
	nucleo.rotation = Vector3.ZERO
	nucleo.scale = Vector3.ONE
	camera_jogo.make_current()
	if barra != null:
		barra.set("visible", true)
	terminou.emit()
	queue_free()


# ------------------------------------------------------------------ peças da cena
func _metal(cor: Color, brilho := Color.BLACK) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = cor
	m.metallic = 0.6
	m.roughness = 0.45
	if brilho != Color.BLACK:
		m.emission_enabled = true
		m.emission = brilho
		m.emission_energy_multiplier = 2.5
	return m


func _caixa(pai: Node3D, tam: Vector3, pos: Vector3, mat: Material, rot := Vector3.ZERO) -> void:
	var b := BoxMesh.new()
	b.size = tam
	var mi := MeshInstance3D.new()
	mi.mesh = b
	mi.material_override = mat
	mi.position = pos
	mi.rotation = rot
	pai.add_child(mi)


## Nave-mãe: casco escuro alongado, naceles, veios de luz e o berço do núcleo embaixo.
func _criar_nave() -> void:
	_nave = Node3D.new()
	add_child(_nave)
	var casco := _metal(Color(0.12, 0.13, 0.15))
	var veio := _metal(Color(0.1, 0.3, 0.3), Color(0.3, 0.95, 0.9))
	_caixa(_nave, Vector3(30, 3.2, 8), Vector3(0, 0, 0), casco)
	_caixa(_nave, Vector3(10, 2.4, 6), Vector3(18, -0.2, 0), casco, Vector3(0, 0, 0.12))
	_caixa(_nave, Vector3(22, 1.6, 12), Vector3(-2, 1.6, 0), casco)
	for z in [-6.2, 6.2]:
		_caixa(_nave, Vector3(14, 2.2, 2.2), Vector3(-8, -0.6, z), casco)
		_caixa(_nave, Vector3(0.6, 1.6, 1.6), Vector3(-15.3, -0.6, z), _metal(Color(0.4, 0.2, 0.1), Color(1.0, 0.55, 0.2)))
	_caixa(_nave, Vector3(28, 0.15, 0.3), Vector3(0, 1.66, 4.1), veio)
	_caixa(_nave, Vector3(28, 0.15, 0.3), Vector3(0, 1.66, -4.1), veio)
	for x in [-2.2, 2.2]:                                     # garras do berço
		_caixa(_nave, Vector3(0.5, 2.4, 0.5), Vector3(x, -2.6, 0), casco)
	var luz := OmniLight3D.new()
	luz.light_color = Color(0.4, 1.0, 0.95)
	luz.light_energy = 3.0
	luz.omni_range = 12.0
	luz.position = Vector3(0, -2.5, 0)
	_nave.add_child(luz)


func _criar_nuvens() -> void:
	var tex := _textura_macia()
	for i in 16:
		var s := Sprite3D.new()
		s.texture = tex
		s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		s.pixel_size = randf_range(0.7, 1.3)
		s.modulate = Color(0.92, 0.94, 0.97, randf_range(0.55, 0.8))
		s.shaded = true
		var a := randf() * TAU
		var r := randf_range(4.0, 34.0)
		s.position = _final + Vector3(cos(a) * r, randf_range(44.0, 62.0), sin(a) * r)
		add_child(s)
		_nuvens.append(s)


func _criar_efeitos() -> void:
	var tex := _textura_macia()
	_rastro = CPUParticles3D.new()
	_rastro.amount = 320
	_rastro.lifetime = 1.4
	_rastro.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	_rastro.emission_sphere_radius = 0.9
	_rastro.local_coords = false
	_rastro.direction = Vector3.UP
	_rastro.spread = 12.0
	_rastro.initial_velocity_min = 2.0
	_rastro.initial_velocity_max = 5.0
	_rastro.gravity = Vector3.ZERO
	_rastro.scale_amount_min = 1.4
	_rastro.scale_amount_max = 3.0
	var cresce := Curve.new()
	cresce.add_point(Vector2(0, 0.6))
	cresce.add_point(Vector2(1, 2.2))
	_rastro.scale_amount_curve = cresce
	var grad := Gradient.new()
	grad.set_color(0, Color(1.0, 0.75, 0.35, 0.9))
	grad.set_color(1, Color(0.35, 0.33, 0.33, 0.0))
	_rastro.color_ramp = grad
	var q := QuadMesh.new()
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = tex
	q.material = m
	_rastro.mesh = q
	_rastro.emitting = false
	add_child(_rastro)
	_luz = OmniLight3D.new()
	_luz.light_color = Color(1.0, 0.6, 0.3)
	_luz.omni_range = 14.0
	_luz.light_energy = 0.0
	add_child(_luz)
	_poeira = CPUParticles3D.new()
	_poeira.amount = 260
	_poeira.lifetime = 2.4
	_poeira.one_shot = true
	_poeira.explosiveness = 0.95
	_poeira.local_coords = false
	_poeira.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING
	_poeira.emission_ring_axis = Vector3.UP
	_poeira.emission_ring_radius = 1.6
	_poeira.emission_ring_inner_radius = 1.2
	_poeira.emission_ring_height = 0.2
	_poeira.direction = Vector3(1, 0.25, 0)
	_poeira.spread = 180.0
	_poeira.flatness = 0.85
	_poeira.initial_velocity_min = 5.0
	_poeira.initial_velocity_max = 11.0
	_poeira.damping_min = 4.0
	_poeira.damping_max = 6.0
	_poeira.gravity = Vector3(0, 0.6, 0)
	_poeira.scale_amount_min = 2.0
	_poeira.scale_amount_max = 4.2
	var gp := Gradient.new()
	gp.set_color(0, Color(0.55, 0.5, 0.44, 0.75))
	gp.set_color(1, Color(0.6, 0.57, 0.52, 0.0))
	_poeira.color_ramp = gp
	_poeira.mesh = q
	_poeira.emitting = false
	add_child(_poeira)


func _criar_tela() -> void:
	var camada := CanvasLayer.new()
	camada.layer = 30
	add_child(camada)
	_veu = ColorRect.new()
	_veu.set_anchors_preset(Control.PRESET_FULL_RECT)
	_veu.color = Color(0, 0, 0, 1)
	_veu.mouse_filter = Control.MOUSE_FILTER_IGNORE
	camada.add_child(_veu)
	_texto = Label.new()
	_texto.position = Vector2(28, 28)
	_texto.add_theme_font_size_override("font_size", 20)
	_texto.add_theme_color_override("font_color", Color(0.45, 1.0, 0.95))
	_texto.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_texto.add_theme_constant_override("outline_size", 6)
	_texto.mouse_filter = Control.MOUSE_FILTER_IGNORE
	camada.add_child(_texto)
	var dica := Label.new()
	dica.text = "toque para pular"
	dica.add_theme_font_size_override("font_size", 14)
	dica.modulate = Color(1, 1, 1, 0.45)
	dica.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT, Control.PRESET_MODE_MINSIZE, 16)
	dica.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	dica.grow_vertical = Control.GROW_DIRECTION_BEGIN
	camada.add_child(dica)


func _textura_macia() -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		for x in 64:
			var d := Vector2(x - 31.5, y - 31.5).length() / 31.5
			var n := 0.85 + 0.15 * sin(x * 0.7) * cos(y * 0.9)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - d, 0.0, 1.0) ** 1.4 * n))
	return ImageTexture.create_from_image(img)
