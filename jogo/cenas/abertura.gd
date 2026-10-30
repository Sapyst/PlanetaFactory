class_name Abertura
extends Node3D
## Abertura do jogo novo (~14 s; qualquer toque/tecla pula): o núcleo — a unidade semeadora da IA — chega do
## espaço. Só referência, sem história longa: a IA é um erro que segue a diretriz de proliferar.
##  1. Espaço escuro: o planeta curvo embaixo (atmosfera brilhando na borda), o sol ofuscando atrás dele, a nave
##     só em silhueta com poucos veios de luz; o núcleo se solta e despenca rumo ao planeta, esquentando.
##  2. Nuvens densas: a tela fecha em branco — é aí que a cena troca para o mapa de verdade (o limite do mapa
##     carregado nunca aparece).
##  3. Abaixo das nuvens: a cápsula de reentrada (nucleo_queda, convertida de estudo_nucleo_queda.py — pétalas
##     recolhidas em saia ablativa e ogiva) vem perto do chão, bate (estrondo, poeira, tremor) e a animação "chegada"
##     do estudo toca do impacto em diante: a ogiva é ejetada, as pétalas cravam no chão, os cabos-raiz descem, as
##     esteiras saem e o monólito sobe; no fim (a pose do laço do núcleo) ela dá lugar ao núcleo do jogo. Linhas de
##     sistema; a câmera desce até a visão de jogo. Sem o modelo da chegada, desce o próprio núcleo (como antes).
## A cena do espaço fica a 6 km de altura (longe do mapa) e usa um ambiente próprio na câmera.

signal terminou

const ESPACO := Vector3(0, 6000, 0)
const T_SOLTA := 2.6
const T_BRANCO := 4.9        ## começa a fechar em nuvem
const T_TROCA := 5.5         ## tela toda branca: troca espaço → mapa
const T_CHAO := 7.6          ## impacto
const T_TEXTO := 8.2
const T_CAMERA := 14.4       ## a chegada (impacto → núcleo pronto) dura 7,5 s depois do impacto
const T_FIM := 16.4
const Q_IMPACTO_S := 59.0 / 24.0     ## tempo do impacto na animação "chegada" (quadro 60 a 24 qps)
const Q_FECHADA_S := 0.2             ## pose da cápsula fechada (descendo)
const ALT_NUVEM := 40.0      ## de onde o núcleo sai das nuvens, acima do chão
const LINHAS := ["UNIDADE SEMEADORA 7 · CHEGADA CONFIRMADA", "DIRETRIZ: PROLIFERAR",
		"ERRO 0x1F · limite da diretriz não encontrado", "…prosseguindo."]

var nucleo: Node3D
var camera_jogo: Camera3D
var barra: Node             ## barra de construção (escondida durante a abertura)

var _t := 0.0
var _final := Vector3.ZERO
var _cam: Camera3D
var _espaco: Node3D
var _amb_espaco: Environment
var _copia: Node3D           ## núcleo de enfeite na cena do espaço
var _nave: Node3D
var _calor: Sprite3D
var _rastro_e: CPUParticles3D
var _rastro: CPUParticles3D
var _poeira: CPUParticles3D
var _nuvens: Array[Sprite3D] = []
var _texto: Label
var _veu: ColorRect
var _no_mapa := false
var _impacto := false
var _som_queda := false
var _tremor := 0.0
var _pulando := false
var _env: Environment
var _guardado := {}
var _tex_macia: Texture2D
var _raios: Sprite3D
var _sois: Array[Sprite3D] = []       ## núcleo, halo e raios do sol (reposicionados a cada quadro na borda do planeta)
var _centro_planeta := Vector3.ZERO
var _raio_planeta := 0.0
var _crescer := -1.0                  ## tempo desde o pouso (o piso de fábrica cresce em volta)
var _queda: Node3D                    ## cápsula de reentrada (nucleo_queda) no mapa; nulo = sem o modelo
var _anim: AnimationPlayer            ## animação "chegada" da cápsula
var _trocou := false                  ## a cápsula já deu lugar ao núcleo do jogo


func _ready() -> void:
	_final = nucleo.position
	var q := _instancia_queda()
	if not q.is_empty():
		_queda = q[0]
		_anim = q[1]
		add_child(_queda)
		_queda.position = _final
		_queda.visible = false
	_tex_macia = _textura_macia()
	_cam = Camera3D.new()
	_cam.fov = 50.0
	_cam.far = 30000.0
	_cam.near = 2.0                 # no espaço: precisão de profundidade para o planeta cobrir o sol
	add_child(_cam)
	_cam.make_current()
	if barra != null:
		barra.set("visible", false)
	var amb := get_tree().current_scene.get_node_or_null("Ambiente") as WorldEnvironment
	if amb != null:
		_env = amb.environment
		_guardado = {"densidade": _env.fog_density}
	_criar_espaco()
	_criar_mapa()
	_criar_tela()
	nucleo.visible = false
	_cam.environment = _amb_espaco
	_piso(0.0)
	_posicionar(0.0)


func _input(e: InputEvent) -> void:
	if _pulando or _t < 0.6:
		return
	var aperto: bool = (e is InputEventKey and e.pressed) or (e is InputEventMouseButton and e.pressed) or (e is InputEventScreenTouch and e.pressed)
	if aperto:
		_pulando = true                                    # pula: núcleo no lugar e a câmera desce rápido
		_t = maxf(_t, T_CAMERA + 1.4)
		_ir_para_mapa()
		_trocar()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_t += delta
	_posicionar(delta)
	if _t >= T_FIM:
		_acabar()


func _posicionar(delta: float) -> void:
	var t := _t
	if t < T_TROCA and not _pulando:
		_fase_espaco(t, delta)
	else:
		if not _no_mapa:
			_ir_para_mapa()
		_fase_mapa(t, delta)
	_tela(t)
	if _tremor > 0.0:
		_tremor = maxf(0.0, _tremor - delta * 1.6)
		_cam.global_position += Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * 0.35 * _tremor


# ------------------------------------------------------------------ 1. espaço
func _fase_espaco(t: float, delta: float) -> void:
	var preso := ESPACO + Vector3(0, -4.2, 0)
	var s := maxf(0.0, t - T_SOLTA)
	# solto: despenca rumo ao planeta, acelerando (e um pouco para a frente)
	var pos := preso + Vector3(0, -s * s * 110.0, -s * s * 70.0)
	_copia.global_position = pos
	_copia.rotation = Vector3(s * 0.35, s * 0.6, s * 0.25)
	_nave.global_position = ESPACO + Vector3(-8.0 + t * 1.6, 0, 0) + Vector3(0, s * s * 0.6, 0)
	if _raios != null:
		_raios.rotation.z = t * 0.05                       # raios do sol girando devagar
	_por_sol()
	var quente := smoothstep(T_SOLTA + 0.9, T_BRANCO, t)
	_calor.global_position = pos + Vector3(0, -1.6, 0)
	_calor.modulate = Color(1.0, 0.55, 0.25, 0.85 * quente)
	_calor.pixel_size = 0.05 + 0.06 * quente
	_rastro_e.global_position = pos + Vector3(0, 1.0, 0)
	_rastro_e.emitting = quente > 0.15
	if s > 0.0 and not _som_queda:
		_som_queda = true
		Som.tocar("reentrada", Vector3.INF, -2.0)
	if t < T_SOLTA + 0.4:
		# perto e de baixo: a nave só em parte, em silhueta, com o planeta e o sol ao fundo
		_cam.global_position = ESPACO + Vector3(9.0 - t * 0.5, -3.0, 15.0)
		_cam.look_at(preso + Vector3(-2.0, -7.5, -10.0))           # borda do planeta embaixo, nave em cima
	else:
		# segue a queda de trás; o planeta cresce e a curva do horizonte desce na tela
		var olho := pos + Vector3(3.0, 5.0, 12.0)
		_cam.global_position = _cam.global_position.lerp(olho, 1.0 - exp(-4.0 * delta)) if delta > 0.0 else olho
		_cam.look_at(pos + Vector3(0, -8.0 - s * 6.0, -14.0))


## Sol exatamente na borda do planeta vista da câmera, longe atrás dele: o planeta cobre a metade de baixo.
func _por_sol() -> void:
	var cam := _cam.global_position
	var para := _centro_planeta - cam
	var d := para.length()
	var v := para / d
	var ang := asin(clampf(_raio_planeta / d, 0.0, 1.0))
	var lado := (_cam.global_basis.y + _cam.global_basis.x * 0.45)       # na borda de cima, um pouco à direita
	var u := (lado - v * lado.dot(v)).normalized()
	var dir := v * cos(ang) + u * sin(ang)
	var dist := d * 2.5                                               # atrás do planeta (dentro do far da câmera)
	for sp in _sois:
		sp.global_position = cam + dir * dist
		sp.pixel_size = float(sp.get_meta("tam")) * dist / float(sp.texture.get_width())


# ------------------------------------------------------------------ 2/3. mapa
func _ir_para_mapa() -> void:
	_no_mapa = true
	_espaco.visible = false
	_cam.environment = null
	_cam.near = 0.05
	_cam.far = 900.0
	nucleo.visible = _queda == null or _trocou
	if _queda != null and not _trocou:
		_queda.visible = true
		_posar(Q_FECHADA_S)
	for n in _nuvens:
		n.visible = true


func _fase_mapa(t: float, delta: float) -> void:
	var u := clampf((t - T_TROCA) / (T_CHAO - T_TROCA), 0.0, 1.0)
	if _pulando:
		u = 1.0
	var corpo := _corpo()
	if u < 1.0:
		corpo.position = _final + Vector3(0, ALT_NUVEM * (1.0 - pow(u, 1.5)), 0)
		var gira := 1.0 - smoothstep(0.55, 0.9, u)
		corpo.rotation = Vector3(sin(t * 1.7) * 0.2, t * 0.7, cos(t * 1.3) * 0.15) * gira
		_rastro.emitting = u < 0.93
	else:
		corpo.position = _final
		corpo.rotation = Vector3.ZERO
		_rastro.emitting = false
		if not _impacto:
			_impacto = true
			_crescer = 0.0
			if _anim != null:                               # a cápsula abre e vira o núcleo (animação do estudo)
				_anim.play("chegada")
				_anim.seek(Q_IMPACTO_S, true)
			if not _pulando:
				_bater()
	if _anim != null and _impacto and not _trocou and (not _anim.is_playing()
			or _anim.current_animation_position >= _anim.current_animation_length - 0.02):
		_trocar()
	_rastro.global_position = corpo.global_position + Vector3(0, 1.2, 0)
	if _crescer >= 0.0:
		_crescer += delta
		_piso(5.5 * smoothstep(0.0, 2.6, _crescer))       # o piso se espalha a partir do núcleo pousado
	var tq := t - T_CHAO
	if tq > 0.0 and tq < 1.4 and not _pulando:
		var s := 1.0 + sin(tq * 9.0) * 0.08 * exp(-tq * 3.0)
		corpo.scale = Vector3(1.0 / s, s, 1.0 / s)
	else:
		corpo.scale = Vector3.ONE
	# câmera olhando para baixo (o horizonte não aparece): segue a queda e para num ponto fixo antes do chão
	var olho: Vector3
	var mira: Vector3
	if u < 0.75:
		olho = corpo.position + Vector3(5.0, 9.0, 6.0)
		mira = corpo.position + Vector3(0, -4.0, 0)
	else:
		olho = _final + Vector3(9.0, 12.0, 11.0)
		mira = _final + Vector3(0, 0.8, 0)
	if t > T_CAMERA:
		var k := smoothstep(T_CAMERA, T_FIM - 0.3, t)
		var de := Transform3D(Basis.looking_at(mira - olho), olho)
		_cam.global_transform = de.interpolate_with(camera_jogo.global_transform, k)
	else:
		_cam.global_position = _cam.global_position.lerp(olho, 1.0 - exp(-7.0 * delta)) if delta > 0.0 and t > T_TROCA + 0.1 else olho
		_cam.look_at(mira)
	if _env != null:
		# névoa grossa logo abaixo das nuvens, voltando à do jogo perto do chão
		_env.fog_density = lerpf(0.03, float(_guardado.densidade), smoothstep(T_TROCA, T_CHAO + 1.5, t))


func _bater() -> void:
	Som.tocar("impacto", Vector3.INF, 0.0)
	_tremor = 1.0
	_poeira.global_position = _final + Vector3(0, 0.3, 0)
	_poeira.restart()
	_poeira.emitting = true


# ------------------------------------------------------------------ tela (véu e texto)
func _tela(t: float) -> void:
	var a := 0.0
	var cor := Color(0.92, 0.94, 0.96)
	if t < 0.9:
		cor = Color.BLACK
		a = 1.0 - t / 0.9
	elif not _pulando and t >= T_BRANCO and t < T_TROCA + 1.0:
		a = smoothstep(T_BRANCO, T_TROCA - 0.1, t) * (1.0 - smoothstep(T_TROCA + 0.15, T_TROCA + 1.0, t))
	elif not _pulando and t >= T_CHAO and t < T_CHAO + 0.4:
		cor = Color(1, 0.95, 0.85)
		a = 0.5 * (1.0 - (t - T_CHAO) / 0.4)                    # clarão do impacto
	_veu.color = Color(cor, a)
	if t > T_TEXTO and not _pulando:
		var total := int((t - T_TEXTO) * 38.0)
		var txt := ""
		for l in LINHAS:
			if total <= 0:
				break
			txt += l.substr(0, total) + "\n"
			total -= l.length() + 6
		_texto.text = txt
		_texto.modulate.a = 1.0 - smoothstep(T_CAMERA + 0.8, T_FIM - 0.2, t)


## Raio (tiles) até onde o piso de fábrica aparece em volta do núcleo; ≥ 1e5 = sem limite (jogo normal).
func _piso(raio: float) -> void:
	RenderingServer.global_shader_parameter_set("piso_crescer", Vector3(_final.x, -_final.z, raio))


## O que desce do céu: a cápsula da chegada (se houver o modelo) ou o próprio núcleo.
func _corpo() -> Node3D:
	return _queda if _queda != null and not _trocou else nucleo


## Cápsula de reentrada (nucleo_queda) com a animação "chegada": [nó, AnimationPlayer] ou [] sem o modelo.
func _instancia_queda() -> Array:
	if not Registro.modelos.has("nucleo_queda"):
		return []
	var q: Node3D = (load(Registro.modelos.nucleo_queda.modelo) as PackedScene).instantiate()
	Materiais.converter(q)
	for p in q.find_children("*", "AnimationPlayer", true, false):
		var ap := p as AnimationPlayer
		if ap.has_animation("chegada"):
			ap.get_animation("chegada").loop_mode = Animation.LOOP_NONE
			return [q, ap]
	q.free()
	return []


## Cápsula parada numa pose da chegada (fechada, descendo).
func _posar(tempo: float) -> void:
	if _anim == null:
		return
	_anim.play("chegada")
	_anim.seek(tempo, true)
	_anim.pause()


## A cápsula aberta (pose do laço do núcleo) dá lugar ao núcleo do jogo, no mesmo lugar.
func _trocar() -> void:
	if _queda == null or _trocou:
		return
	_trocou = true
	_queda.visible = false
	nucleo.position = _final
	nucleo.rotation = Vector3.ZERO
	nucleo.scale = Vector3.ONE
	nucleo.visible = true


func _acabar() -> void:
	_trocar()
	if _queda != null:
		_queda.queue_free()
	_piso(1.0e6)
	if _env != null:
		_env.fog_density = _guardado.densidade
	nucleo.position = _final
	nucleo.rotation = Vector3.ZERO
	nucleo.scale = Vector3.ONE
	nucleo.visible = true
	camera_jogo.make_current()
	if barra != null:
		barra.set("visible", true)
	terminou.emit()
	queue_free()


# ------------------------------------------------------------------ cena do espaço
func _criar_espaco() -> void:
	_espaco = Node3D.new()
	add_child(_espaco)
	_amb_espaco = Environment.new()
	_amb_espaco.background_mode = Environment.BG_COLOR
	_amb_espaco.background_color = Color(0.004, 0.005, 0.01)
	_amb_espaco.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_amb_espaco.ambient_light_color = Color(0.08, 0.10, 0.14)
	_amb_espaco.ambient_light_energy = 0.2
	_amb_espaco.tonemap_mode = Environment.TONE_MAPPER_AGX
	_amb_espaco.glow_enabled = true
	_amb_espaco.glow_intensity = 0.9
	_amb_espaco.glow_bloom = 0.15
	_amb_espaco.glow_hdr_threshold = 0.9
	var sol_dir := Vector3(0.25, 0.30, -0.92).normalized()
	# planeta curvo bem embaixo, enchendo a parte de baixo da tela; halo da atmosfera
	var raio := 2400.0
	var centro := ESPACO + Vector3(0, -raio - 1500.0, -1700.0)     # alto o bastante para não ver tudo de raspão     # longe: o horizonte curvo aparece com o escuro em cima
	# superfície, nuvens (girando devagar) e halo da atmosfera
	for k in 3:
		var esf := SphereMesh.new()
		esf.radius = raio * [1.0, 1.008, 1.025][k]
		esf.height = esf.radius * 2.0
		esf.radial_segments = 128
		esf.rings = 64
		var mi := MeshInstance3D.new()
		mi.mesh = esf
		var mat := ShaderMaterial.new()
		mat.shader = load("res://cenas/halo_abertura.gdshader" if k == 2 else "res://cenas/planeta_abertura.gdshader")
		mat.set_shader_parameter("sol_dir", sol_dir)
		if k < 2:
			mat.set_shader_parameter("mapa", load("res://assets/texturas/planeta.png" if k == 0 else "res://assets/texturas/planeta_nuvens.png"))
			mat.set_shader_parameter("nuvens", k == 1)
			mat.set_shader_parameter("gira", 0.0 if k == 0 else 0.0025)
			if k == 1:
				mat.render_priority = 1
				# nuvens precisam de transparência
				mat.shader = load("res://cenas/nuvens_abertura.gdshader")
				mat.set_shader_parameter("mapa", load("res://assets/texturas/planeta_nuvens.png"))
				mat.set_shader_parameter("sol_dir", sol_dir)
				mat.set_shader_parameter("gira", 0.0025)
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_espaco.add_child(mi)
		mi.global_position = centro
	# sol amarelo forte atrás da borda do planeta, com halo e raios (giram devagar)
	_centro_planeta = centro
	_raio_planeta = raio
	for k in 3:
		var sp := Sprite3D.new()
		sp.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		sp.shaded = false
		sp.texture = load("res://assets/texturas/sol_raios.png" if k == 2 else "res://assets/texturas/sol.png")
		sp.set_meta("tam", [0.16, 0.55, 0.85][k])          # tamanho aparente na tela (radianos)
		sp.modulate = [Color(2.2, 2.0, 1.4), Color(1.4, 1.1, 0.55, 0.55), Color(1.6, 1.35, 0.8, 0.85)][k]
		sp.render_priority = k
		_espaco.add_child(sp)
		_sois.append(sp)
		if k == 2:
			_raios = sp
	# estrelas
	var estrelas := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var q := QuadMesh.new()
	q.size = Vector2(1.6, 1.6)
	var me := StandardMaterial3D.new()
	me.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	me.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	me.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	me.albedo_texture = _tex_macia
	me.vertex_color_use_as_albedo = true
	q.material = me
	mm.mesh = q
	mm.instance_count = 600
	for i in 600:
		var d := Vector3(randf_range(-1, 1), randf_range(-0.15, 1), randf_range(-1, 1)).normalized()
		mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * randf_range(0.5, 1.6)), d * 1500.0))
		mm.set_instance_color(i, Color(1, 1, 1, randf_range(0.3, 1.0)))
	estrelas.multimesh = mm
	_espaco.add_child(estrelas)
	estrelas.global_position = ESPACO
	# nave: só silhueta, quase sem luz, veios ciano
	_nave = Node3D.new()
	_espaco.add_child(_nave)
	var casco := _metal(Color(0.035, 0.037, 0.045))
	var veio := _metal(Color(0.05, 0.2, 0.2), Color(0.3, 0.95, 0.9))
	_caixa(_nave, Vector3(34, 3.6, 9), Vector3(0, 0, 0), casco)
	_caixa(_nave, Vector3(26, 1.8, 14), Vector3(-3, 1.8, 0), casco)
	_caixa(_nave, Vector3(12, 2.6, 7), Vector3(20, -0.2, 0), casco, Vector3(0, 0, 0.12))
	for z in [-7.0, 7.0]:
		_caixa(_nave, Vector3(16, 2.4, 2.4), Vector3(-9, -0.8, z), casco)
		_caixa(_nave, Vector3(0.5, 1.8, 1.8), Vector3(-17.2, -0.8, z), _metal(Color(0.3, 0.15, 0.08), Color(1.0, 0.5, 0.2)))
	for z in [-4.6, 4.6]:
		_caixa(_nave, Vector3(9, 0.05, 0.08), Vector3(4, -1.82, z), veio)
	for x in [-2.4, 2.4]:
		_caixa(_nave, Vector3(0.5, 2.6, 0.5), Vector3(x, -2.9, 0), casco)
	# a cápsula fechada (modelo da chegada parado na pose da queda) presa sob a nave; sem ele, cópia do núcleo
	var cq := _instancia_queda()
	if not cq.is_empty():
		_copia = cq[0]
		_espaco.add_child(_copia)
		(cq[1] as AnimationPlayer).play("chegada")
		(cq[1] as AnimationPlayer).seek(Q_FECHADA_S, true)
		(cq[1] as AnimationPlayer).pause()
	else:
		_copia = nucleo.duplicate() as Node3D
		_espaco.add_child(_copia)
	_copia.visible = true
	# calor da reentrada: brilho e rastro
	_calor = Sprite3D.new()
	_calor.texture = _tex_macia
	_calor.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_calor.shaded = false
	_espaco.add_child(_calor)
	_rastro_e = _particulas_rastro()
	_espaco.add_child(_rastro_e)


# ------------------------------------------------------------------ peças do mapa (abaixo das nuvens)
func _criar_mapa() -> void:
	for i in 18:                                               # nuvens que ficam para trás logo após a troca
		var s := Sprite3D.new()
		s.texture = _tex_macia
		s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		s.pixel_size = randf_range(0.8, 1.5)
		s.modulate = Color(0.93, 0.95, 0.97, randf_range(0.6, 0.85))
		var a := randf() * TAU
		var r := randf_range(6.0, 30.0)
		s.position = _final + Vector3(cos(a) * r, randf_range(ALT_NUVEM + 4.0, ALT_NUVEM + 16.0), sin(a) * r)
		s.visible = false
		add_child(s)
		_nuvens.append(s)
	_rastro = _particulas_rastro()
	add_child(_rastro)
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
	Fumaca.configurar(_poeira, [Color(0.52, 0.47, 0.40, 0.85), Color(0.55, 0.50, 0.44, 0.7), Color(0.62, 0.58, 0.52, 0.0)], 2.4, 4.6, 2.2)
	_poeira.emitting = false
	add_child(_poeira)


func _particulas_rastro() -> CPUParticles3D:
	var r := CPUParticles3D.new()
	r.amount = 260
	r.lifetime = 1.6
	r.local_coords = false
	r.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	r.emission_sphere_radius = 0.9
	r.direction = Vector3.UP
	r.spread = 14.0
	r.initial_velocity_min = 2.0
	r.initial_velocity_max = 5.0
	r.gravity = Vector3.ZERO
	Fumaca.configurar(r, [Color(1.0, 0.72, 0.38, 0.9), Color(0.55, 0.45, 0.40, 0.75), Color(0.40, 0.39, 0.40, 0.0)], 1.8, 3.4, 2.8)
	r.emitting = false
	return r


func _quad_macio() -> QuadMesh:
	var q := QuadMesh.new()
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = _tex_macia
	q.material = m
	return q


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


func _metal(cor: Color, brilho := Color.BLACK) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = cor
	m.metallic = 0.7
	m.roughness = 0.4
	if brilho != Color.BLACK:
		m.emission_enabled = true
		m.emission = brilho
		m.emission_energy_multiplier = 1.2
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


func _textura_macia() -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		for x in 64:
			var d := Vector2(x - 31.5, y - 31.5).length() / 31.5
			var n := 0.85 + 0.15 * sin(x * 0.7) * cos(y * 0.9)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - d, 0.0, 1.0) ** 1.4 * n))
	return ImageTexture.create_from_image(img)
