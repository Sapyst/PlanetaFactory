class_name Fumaca
## Fumaça/poeira das partículas: folha 4×4 de baforadas desenhadas por código (ferramentas/gerar_fumaca.py), cada
## partícula sorteia uma baforada e um ângulo, gira devagar, cresce e some — iluminada pela luz do mundo (não é
## mancha chapada). `configurar` prepara um CPUParticles3D; a cor/opacidade vem do degradê de cada uso.

static var _material: StandardMaterial3D


static func material() -> StandardMaterial3D:
	if _material == null:
		var m := StandardMaterial3D.new()
		m.albedo_texture = load("res://assets/texturas/fumaca.png")
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.particles_anim_h_frames = 4
		m.particles_anim_v_frames = 4
		m.particles_anim_loop = false
		m.vertex_color_use_as_albedo = true
		m.shading_mode = BaseMaterial3D.SHADING_MODE_PER_VERTEX
		m.roughness = 1.0
		m.disable_receive_shadows = true
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		_material = m
	return _material


## `cores`: [início, meio, fim] (o alfa de cada um é a opacidade naquele momento da vida da partícula).
static func configurar(p: CPUParticles3D, cores: Array, tam_min: float, tam_max: float, cresce := 2.4) -> void:
	var q := QuadMesh.new()
	q.material = material()
	p.mesh = q
	p.anim_offset_min = 0.0
	p.anim_offset_max = 1.0                   # cada partícula com uma baforada diferente
	p.angle_min = 0.0
	p.angle_max = 360.0
	p.angular_velocity_min = -14.0
	p.angular_velocity_max = 14.0
	p.scale_amount_min = tam_min
	p.scale_amount_max = tam_max
	var curva := Curve.new()
	curva.add_point(Vector2(0, 0.45))
	curva.add_point(Vector2(1, cresce))
	p.scale_amount_curve = curva
	var g := Gradient.new()
	g.set_color(0, cores[0])
	g.set_color(1, cores[2])
	g.add_point(0.18, cores[1])
	p.color_ramp = g
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
