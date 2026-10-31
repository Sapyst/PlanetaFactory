class_name Efeitos
extends Node3D
## Efeitos que leem a simulação (não decidem nada):
##  - fumaça: sai de quem poluiu neste passo (fornalha/gerador queimando, extrator trabalhando) — a fumaça é a
##    poluição visível;
##  - ícone de estado em cima da máquina parada: sem energia (raio), sem insumo (caixa vazia), saída cheia
##    (caixa cheia), sem receita (engrenagem); pisca devagar, só com a câmera perto;
##  - marca de destruição: chão queimado + sucata onde algo foi derrubado (some em 90 s);
##  - jato do supressor de incêndio: arco de água do canhão até o foco que ele está apagando (`fabrica.jatos`).

const DIST_ICONES := 60.0
const VIDA_MARCA := 90.0
## Poluem, mas não têm chaminé: a fumaça nascia no topo da caixa do modelo e virava uma bola preta parada no alto da torre.
const SEM_CHAMINE := ["extrator_cristal", "extrator_ressonante", "broca_minerio", "broca_grande", "broca_nucleo"]

var fabrica: Fabrica
var mostrar_icones := true          ## mostruário (vídeos) desliga
var mapa: MapaOcupacao
var _fumaca: Dictionary = {}       ## id → CPUParticles3D
var _icones: Dictionary = {}       ## id → Sprite3D
var _tex: Dictionary = {}          ## estado → Texture2D
var _marcas: Array[Dictionary] = []
var _jatos: Dictionary = {}        ## id do supressor → CPUParticles3D
var _mat_fumaca: StandardMaterial3D
var _mat_marca: StandardMaterial3D


func _ready() -> void:
	_mat_marca = StandardMaterial3D.new()
	_mat_marca.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_marca.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat_marca.albedo_texture = _textura_marca()
	for k in [Maquina.Estado.SEM_ENERGIA, Maquina.Estado.SEM_INSUMO, Maquina.Estado.SAIDA_CHEIA, Maquina.Estado.SEM_RECEITA]:
		_tex[k] = ImageTexture.create_from_image(_desenhar_icone(k))


func _process(delta: float) -> void:
	if fabrica == null:
		return
	_atualizar_fumaca()
	_atualizar_jatos()
	_atualizar_icones()
	_atualizar_marcas(delta)


## Algo foi destruído aqui (evento "destruida" da colônia).
func marcar_destruicao(centro: Vector2, tamanho: float) -> void:
	var q := QuadMesh.new()
	q.size = Vector2.ONE * (1.4 + tamanho)
	q.orientation = PlaneMesh.FACE_Y
	var mi := MeshInstance3D.new()
	mi.mesh = q
	mi.material_override = _mat_marca.duplicate()
	mi.position = Grade.ponto_mundo(centro, 0.025)
	mi.rotation.y = randf() * TAU
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	# sucata: alguns pedaços de metal tortos em volta
	for i in 3 + int(tamanho * 2):
		var b := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(randf_range(0.08, 0.22), randf_range(0.04, 0.10), randf_range(0.08, 0.3))
		b.mesh = bm
		b.material_override = Materiais.material(_metal())
		b.position = Vector3(randf_range(-0.6, 0.6), 0.04, randf_range(-0.6, 0.6)) * (0.6 + tamanho * 0.4)
		b.rotation = Vector3(randf() * 0.6, randf() * TAU, randf() * 0.6)
		mi.add_child(b)
	_marcas.append({"no": mi, "vida": VIDA_MARCA})


func _metal() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.resource_name = "P_Escuro"
	m.albedo_color = Color(0.2, 0.2, 0.22)
	m.roughness = 0.7
	return m


func _atualizar_fumaca() -> void:
	for id in fabrica.emissao:
		if not _fumaca.has(id) and mapa.estruturas.has(id) and not mapa.estruturas[id].nome in SEM_CHAMINE:
			_fumaca[id] = _criar_fumaca(id)
	for id in _fumaca.keys():
		var p: CPUParticles3D = _fumaca[id]
		if not mapa.estruturas.has(id):
			p.queue_free()
			_fumaca.erase(id)
			continue
		p.emitting = fabrica.emissao.has(id) and Visao.dentro(Vector2(p.position.x, -p.position.z), 1.1)   # fora da visão: calado


## Supressor apagando: gotas e névoa em arco (lançadas a 35°, alcance = distância até o foco).
func _atualizar_jatos() -> void:
	for id in fabrica.jatos:
		if not _jatos.has(id) and mapa.estruturas.has(id):
			var p := CPUParticles3D.new()
			p.amount = 48
			p.spread = 5.0
			p.gravity = Vector3(0, -9.8, 0)
			p.damping_min = 0.0
			p.damping_max = 0.3
			Fumaca.configurar(p, [Color(0.78, 0.86, 0.92, 0.0), Color(0.82, 0.9, 0.96, 0.75), Color(0.9, 0.94, 0.97, 0.0)], 0.10, 0.22, 2.2)
			add_child(p)
			_jatos[id] = p
	for id in _jatos.keys():
		var p: CPUParticles3D = _jatos[id]
		if not mapa.estruturas.has(id):
			p.queue_free()
			_jatos.erase(id)
			continue
		var ativo: bool = fabrica.jatos.has(id) and Visao.dentro(Vector2(p.position.x, -p.position.z), 1.1)
		p.emitting = ativo
		if not ativo:
			continue
		var e: Dictionary = mapa.estruturas[id]
		var dims: Array = Registro.modelos.get(e.nome, {}).get("dims", [1, 1, 1])
		var c := Grade.centro_da_area(e.minimo, e.area, e.rot)
		p.position = Grade.ponto_mundo(c, float(dims[2]) * 0.8)
		var alvo: Vector2 = fabrica.jatos[id]
		var h := Grade.ponto_mundo(alvo) - Grade.ponto_mundo(c)
		var alcance := maxf(1.0, h.length())
		var ang := deg_to_rad(35.0)
		var v := sqrt(alcance * 9.8 / sin(2.0 * ang))
		p.direction = (h.normalized() * cos(ang) + Vector3.UP * sin(ang)).normalized()
		p.initial_velocity_min = v * 0.92
		p.initial_velocity_max = v * 1.04
		p.lifetime = 2.0 * v * sin(ang) / 9.8 + 0.15


func _criar_fumaca(id: int) -> CPUParticles3D:
	var e: Dictionary = mapa.estruturas[id]
	var dims: Array = Registro.modelos.get(e.nome, {}).get("dims", [1, 1, 1])
	var p := CPUParticles3D.new()
	p.amount = 22
	p.lifetime = 4.2
	p.direction = Vector3(0.25, 1, 0.1)
	p.spread = 16.0
	p.initial_velocity_min = 0.35
	p.initial_velocity_max = 0.7
	p.gravity = Vector3(0.18, 0.10, 0.04)          # sobe devagar e é levada pela brisa
	p.damping_min = 0.05
	p.damping_max = 0.15
	Fumaca.configurar(p, [Color(0.36, 0.34, 0.33, 0.0), Color(0.40, 0.38, 0.37, 0.62), Color(0.62, 0.60, 0.59, 0.0)], 0.7, 1.2, 3.0)
	p.position = Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot), float(dims[2]) + 0.1)
	add_child(p)
	return p


func _atualizar_icones() -> void:
	var cam := get_viewport().get_camera_3d() as CameraJogo
	var perto := (cam == null or cam.distancia < DIST_ICONES) and mostrar_icones
	var pisca := 0.65 + 0.35 * sin(Time.get_ticks_msec() * 0.004)
	for id in fabrica.maquinas:
		var m: Maquina = fabrica.maquinas[id]
		var mostrar := perto and _tex.has(m.estado)
		var s: Sprite3D = _icones.get(id)
		if not mostrar:
			if s != null:
				s.visible = false
			continue
		if s == null:
			s = Sprite3D.new()
			s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			s.pixel_size = 0.009
			s.no_depth_test = true
			s.render_priority = 2
			var e: Dictionary = mapa.estruturas[id]
			var dims: Array = Registro.modelos.get(e.nome, {}).get("dims", [1, 1, 1])
			s.position = Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot), float(dims[2]) + 0.6)
			add_child(s)
			_icones[id] = s
		s.texture = _tex[m.estado]
		s.modulate.a = pisca
		s.visible = true
	for id in _icones.keys():
		if not fabrica.maquinas.has(id):
			_icones[id].queue_free()
			_icones.erase(id)


func _atualizar_marcas(delta: float) -> void:
	for i in range(_marcas.size() - 1, -1, -1):
		var m: Dictionary = _marcas[i]
		m.vida -= delta
		var no: MeshInstance3D = m.no
		(no.material_override as StandardMaterial3D).albedo_color.a = clampf(m.vida / 20.0, 0.0, 1.0)
		if m.vida <= 0.0:
			no.queue_free()
			_marcas.remove_at(i)


# ------------------------------------------------------------------ texturas desenhadas por código
## Ícone 64×64: disco colorido com borda escura e um símbolo branco.
func _desenhar_icone(estado: int) -> Image:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var fundo: Color = {Maquina.Estado.SEM_ENERGIA: Color(0.85, 0.22, 0.18), Maquina.Estado.SEM_INSUMO: Color(0.9, 0.55, 0.12),
			Maquina.Estado.SAIDA_CHEIA: Color(0.25, 0.5, 0.85), Maquina.Estado.SEM_RECEITA: Color(0.5, 0.5, 0.56)}[estado]
	var simbolo := _simbolo(estado)
	for y in 64:
		for x in 64:
			var d := Vector2(x - 31.5, y - 31.5).length()
			if d > 30.0:
				continue
			var c: Color = fundo if d < 26.5 else Color(0.08, 0.08, 0.1)
			if d < 26.5 and _dentro(simbolo, Vector2(x, y)):
				c = Color(1, 1, 1)
			img.set_pixel(x, y, c)
	return img


func _dentro(polis: Array, p: Vector2) -> bool:
	for poli in polis:
		if Geometry2D.is_point_in_polygon(p, poli):
			return true
	return false


func _simbolo(estado: int) -> Array:
	match estado:
		Maquina.Estado.SEM_ENERGIA:     # raio
			return [PackedVector2Array([Vector2(36, 10), Vector2(20, 35), Vector2(31, 35), Vector2(26, 54), Vector2(44, 28), Vector2(33, 28), Vector2(38, 10)])]
		Maquina.Estado.SEM_INSUMO:      # caixa vazia (contorno)
			return [PackedVector2Array([Vector2(18, 22), Vector2(46, 22), Vector2(46, 26), Vector2(18, 26)]),
					PackedVector2Array([Vector2(18, 42), Vector2(46, 42), Vector2(46, 46), Vector2(18, 46)]),
					PackedVector2Array([Vector2(18, 22), Vector2(22, 22), Vector2(22, 46), Vector2(18, 46)]),
					PackedVector2Array([Vector2(42, 22), Vector2(46, 22), Vector2(46, 46), Vector2(42, 46)])]
		Maquina.Estado.SAIDA_CHEIA:     # caixa cheia com seta para cima
			return [PackedVector2Array([Vector2(18, 32), Vector2(46, 32), Vector2(46, 48), Vector2(18, 48)]),
					PackedVector2Array([Vector2(32, 10), Vector2(43, 24), Vector2(36, 24), Vector2(36, 29), Vector2(28, 29), Vector2(28, 24), Vector2(21, 24)])]
	# sem receita: engrenagem (disco com dentes)
	var pts := PackedVector2Array()
	for i in 16:
		var r := 17.0 if i % 2 == 0 else 12.0
		var a := i * TAU / 16.0
		pts.append(Vector2(32, 32) + Vector2.from_angle(a) * r)
	return [pts]


## Disco macio (borda some) para a fumaça não sair quadrada.
func _textura_fumaca() -> Texture2D:
	var img := Image.create(32, 32, false, Image.FORMAT_RGBA8)
	for y in 32:
		for x in 32:
			var d := Vector2(x - 15.5, y - 15.5).length() / 15.5
			img.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - d, 0.0, 1.0) ** 1.6))
	return ImageTexture.create_from_image(img)


func _textura_marca() -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		for x in 64:
			var p := Vector2(x - 31.5, y - 31.5)
			var ruido := sin(x * 0.9) * cos(y * 1.3) * 0.15 + sin((x + y) * 0.37) * 0.1
			var a := clampf(1.0 - p.length() / 30.0 + ruido, 0.0, 1.0)
			img.set_pixel(x, y, Color(0.08, 0.06, 0.05, a * 0.85))
	return ImageTexture.create_from_image(img)
