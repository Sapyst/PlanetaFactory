class_name DesenhoColonia
extends Node3D
## Desenha a Colonia: aranhas (nó Aranha com marcha e IK, seguindo a posição lógica), ninhos (crescem durante a
## obra), tiros das torres (traço luminoso + torre mirando), faíscas de morte, barras de vida das estruturas
## mordidas. Só lê a lógica e os eventos do tick — não decide nada.
## Todo tiro ejeta uma cápsula (regra da arte: metralhadora e torre de energia) pela calha do modelo ("ejecao" em
## modelos.json, via Animador.ejecao): a cápsula voa girando, quica no chão, para e some; a calha solta uma
## fumacinha enquanto a torre atira. Na metralhadora o tiro também gira o tambor (Animador.rajada).

const FAISCA := Color(1.0, 0.65, 0.25)
const MAX_CAPSULAS := 240
const VIDA_CAPSULA := 2.6           ## s desde o tiro até sumir (encolhe nos últimos 0,5 s, já parada no chão)
const RAIO_CAPSULA := 0.014
const LAJE := 0.08                  ## topo da laje das torres (onde a cápsula quica)

var colonia: Colonia
var mapa: MapaOcupacao
var animadores_torre: Callable      ## id da torre → Animador (ou null), vem do mundo

var _aranhas: Dictionary = {}       ## id → Aranha
var _ninhos: Dictionary = {}        ## id → Node3D
var _tracos: Array[Dictionary] = [] ## {de: Vector3, para: Vector3, vida: float}
var _malha_tracos: ImmediateMesh
var _barras: Dictionary = {}        ## id → [fundo, frente]
var _mat_traco: StandardMaterial3D
var _capsulas: Array[Dictionary] = []   ## {p, v, chao, eixo, ang, w, rumo, vida, quiques, parada}
var _mm_capsulas: MultiMesh
var _fumacinhas: Dictionary = {}        ## id da torre → {no: CPUParticles3D, t: s de fumaça pela frente}


func _ready() -> void:
	_malha_tracos = ImmediateMesh.new()
	var mi := MeshInstance3D.new()
	mi.mesh = _malha_tracos
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mat_traco = StandardMaterial3D.new()
	_mat_traco.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_traco.albedo_color = Color(1.0, 0.92, 0.55)
	_mat_traco.emission_enabled = true
	_mat_traco.emission = Color(1.0, 0.8, 0.3)
	_mat_traco.cull_mode = BaseMaterial3D.CULL_DISABLED      # a fita pode ficar de costas conforme o ângulo
	mi.material_override = _mat_traco
	add_child(mi)
	# cápsulas: um MultiMesh só (até MAX_CAPSULAS no ar/chão ao mesmo tempo)
	var cil := CylinderMesh.new()
	cil.top_radius = RAIO_CAPSULA * 0.85
	cil.bottom_radius = RAIO_CAPSULA
	cil.height = 0.075
	cil.radial_segments = 8
	cil.rings = 1
	var latao := StandardMaterial3D.new()
	latao.albedo_color = Color(0.62, 0.45, 0.19)
	latao.metallic = 0.7
	latao.roughness = 0.4
	cil.material = latao
	_mm_capsulas = MultiMesh.new()
	_mm_capsulas.transform_format = MultiMesh.TRANSFORM_3D
	_mm_capsulas.mesh = cil
	_mm_capsulas.instance_count = MAX_CAPSULAS
	_mm_capsulas.visible_instance_count = 0
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = _mm_capsulas
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)


## Chamado a cada quadro, depois do tick lógico. `eventos` = os acumulados desde o último quadro.
func atualizar(eventos: Array[Dictionary], delta: float) -> void:
	for e in eventos:
		match e.tipo:
			"tiro":
				var de := Grade.ponto_mundo(e.de, 1.25)
				var para := Grade.ponto_mundo(e.para, 0.6)
				_tracos.append({"de": de + (para - de).normalized() * 0.9, "para": para, "vida": 0.10})
				_cartucho(e)
			"aranha_morta":
				if _aranhas.has(e.id):
					(_aranhas[e.id] as Aranha).morrer()
					_aranhas.erase(e.id)
				_faiscas(Grade.ponto_mundo(e.pos, 0.6), 24)
			"ninho_destruido":
				if _ninhos.has(e.id):
					var n: Node3D = _ninhos[e.id]
					_ninhos.erase(e.id)
					var tw := n.create_tween()
					tw.tween_property(n, "position:y", -1.6, 1.2).set_ease(Tween.EASE_IN)
					tw.tween_callback(n.queue_free)
				_faiscas(Grade.ponto_mundo(e.pos, 1.0), 60)
			"destruida":
				_faiscas(Grade.ponto_mundo(e.centro, 0.6), 40)
	_sincronizar_aranhas()
	_sincronizar_ninhos(delta)
	_mirar_torres()
	_desenhar_tracos(delta)
	_mover_capsulas(delta)
	_atualizar_fumacinhas(delta)
	_desenhar_barras()


## Só ganha nó (marcha + IK a cada quadro) a aranha perto do que a câmera vê; as outras seguem só na lógica.
func _perto_da_vista(p: Vector2) -> bool:
	if Visao.ativa:
		return Visao.dentro(p, 1.15)                 # fora do oval de visão a aranha segue só na lógica
	var cam := get_viewport().get_camera_3d() as CameraJogo if get_viewport() != null else null
	if cam == null:
		return true
	return p.distance_to(Vector2(cam.alvo.x, -cam.alvo.z)) < cam.distancia * 1.25 + 12.0


func _sincronizar_aranhas() -> void:
	for id in colonia.aranhas:
		var ar: Dictionary = colonia.aranhas[id]
		var no: Aranha = _aranhas.get(id)
		if not _perto_da_vista(ar.pos):
			if no != null:
				no.queue_free()
				_aranhas.erase(id)
			continue
		if no == null:
			no = Aranha.new()
			no.position = Grade.ponto_mundo(ar.pos)
			add_child(no)
			_aranhas[id] = no
		var p := Grade.ponto_mundo(ar.pos)
		no.ir_para(p)
		no.definir_furia(colonia.furia(ar))
		no.atacando = ar.mordendo
		if ar.mordendo and ar.has("mordida"):
			no.encarar(Grade.ponto_mundo(ar.mordida))
	for id in _aranhas.keys():
		if not colonia.aranhas.has(id):
			(_aranhas[id] as Aranha).morrer()
			_aranhas.erase(id)


func _sincronizar_ninhos(delta: float) -> void:
	for id in colonia.ninhos:
		var n: Dictionary = colonia.ninhos[id]
		var no: Node3D = _ninhos.get(id)
		if not _perto_da_vista(n.centro):
			if no != null:
				no.queue_free()
				_ninhos.erase(id)
			continue
		if no == null:
			no = (load(Registro.modelos["ninho_aranha"].modelo) as PackedScene).instantiate()
			add_child(no)
			Materiais.converter(no)
			no.position = Grade.ponto_mundo(n.centro)
			no.rotation.y = fposmod(n.centro.x * 1.7 + n.centro.y * 0.9, TAU)
			_ninhos[id] = no
		# obra: cresce do chão, tremendo
		var alvo: float = 0.25 + 0.75 * n.obra
		var s := lerpf(no.scale.y, alvo, minf(1.0, delta * 4.0))
		no.scale = Vector3(s, s, s)
		no.position.x = n.centro.x + (sin(Time.get_ticks_msec() * 0.05) * 0.03 if n.obra < 1.0 else 0.0)


func _mirar_torres() -> void:
	if not animadores_torre.is_valid():
		return
	for id in colonia.torres:
		var a: Animador = animadores_torre.call(id)
		if a == null:
			continue
		var t: Dictionary = colonia.torres[id]
		a.ponto_alvo = Grade.ponto_mundo(t.mira, 0.6) if t.mirando else Vector3.INF


func _desenhar_tracos(delta: float) -> void:
	_malha_tracos.clear_surfaces()
	var vivos: Array[Dictionary] = []
	for tr in _tracos:
		tr.vida -= delta
		if tr.vida > 0.0:
			vivos.append(tr)
	_tracos = vivos
	if _tracos.is_empty():
		return
	_malha_tracos.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var cam := get_viewport().get_camera_3d()
	for tr in _tracos:
		# fita virada para a câmera (linha grossa visível de longe)
		var d: Vector3 = (tr.para - tr.de).normalized()
		var olho: Vector3 = (cam.global_position - tr.de).normalized() if cam != null else Vector3.UP
		var lado := d.cross(olho).normalized() * 0.07
		var v := [tr.de - lado, tr.de + lado, tr.para + lado, tr.para - lado]
		for i in [0, 1, 2, 0, 2, 3]:
			_malha_tracos.surface_add_vertex(v[i])
	_malha_tracos.surface_end()


func _desenhar_barras() -> void:
	for id in _barras.keys():
		if not colonia.vida.has(id) or not mapa.estruturas.has(id):
			for n in _barras[id]:
				n.queue_free()
			_barras.erase(id)
	for id in colonia.vida:
		if not mapa.estruturas.has(id):
			continue
		var e: Dictionary = mapa.estruturas[id]
		var total: float = Registro.estruturas.get(e.nome, {}).get("vida", 100)
		var f := clampf(colonia.vida[id] / total, 0.0, 1.0)
		if not _barras.has(id):
			_barras[id] = [_quad(Color(0.08, 0.08, 0.1, 0.85), 0), _quad(Color.WHITE, 1)]
		var dims: Array = Registro.modelos.get(e.nome, {}).get("dims", [1, 1, 1])
		var topo := Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot), float(dims[2]) + 0.45)
		var fundo: MeshInstance3D = _barras[id][0]
		var frente: MeshInstance3D = _barras[id][1]
		fundo.position = topo
		frente.position = topo
		(frente.mesh as QuadMesh).size = Vector2(1.0 * f, 0.10)
		(frente.mesh as QuadMesh).center_offset = Vector3(-(1.0 - f) * 0.5, 0, 0)
		(frente.material_override as StandardMaterial3D).albedo_color = Color(1.0 - f, 0.35 + 0.6 * f, 0.25)


func _quad(cor: Color, prioridade: int) -> MeshInstance3D:
	var q := QuadMesh.new()
	q.size = Vector2(1.04, 0.14) if prioridade == 0 else Vector2(1.0, 0.10)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.no_depth_test = true
	m.render_priority = prioridade
	m.albedo_color = cor
	var mi := MeshInstance3D.new()
	mi.mesh = q
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


## Faíscas de uma vez (some sozinha).
func _faiscas(p: Vector3, n: int) -> void:
	var f := CPUParticles3D.new()
	f.one_shot = true
	f.emitting = true
	f.amount = n
	f.lifetime = 0.7
	f.explosiveness = 0.95
	f.direction = Vector3.UP
	f.spread = 70.0
	f.initial_velocity_min = 2.0
	f.initial_velocity_max = 4.5
	f.gravity = Vector3(0, -9.0, 0)
	f.scale_amount_min = 0.05
	f.scale_amount_max = 0.10
	var malha := BoxMesh.new()
	malha.size = Vector3.ONE
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = FAISCA
	malha.material = m
	f.mesh = malha
	f.position = p
	add_child(f)
	get_tree().create_timer(1.2).timeout.connect(f.queue_free)


# ------------------------------------------------------------------ cápsulas ejetadas
## Tiro: gira o tambor (metralhadora) e, perto da vista, ejeta a cápsula com fumacinha pela calha do modelo.
func _cartucho(e: Dictionary) -> void:
	if not animadores_torre.is_valid():
		return
	var a: Animador = animadores_torre.call(e.get("torre", -1))
	if a == null:
		return
	a.rajada = 0.25
	if not _perto_da_vista(e.de):
		return
	var ej := a.ejecao()
	if ej.is_empty():
		return
	ejetar_capsula(ej[0], ej[1], Grade.ponto_mundo(e.de).y + LAJE)
	if not _fumacinhas.has(e.torre):
		_fumacinhas[e.torre] = {"no": _nova_fumacinha(), "t": 0.0}
	var f: Dictionary = _fumacinhas[e.torre]
	f.t = 0.18
	(f.no as CPUParticles3D).position = ej[0]            # o desenho da colônia fica na origem do mundo


## Uma cápsula voando de `pos` com velocidade `vel` (m/s, mundo); quica em `chao` (altura do mundo).
func ejetar_capsula(pos: Vector3, vel: Vector3, chao: float) -> void:
	if _capsulas.size() >= MAX_CAPSULAS:
		_capsulas.pop_front()
	var jit := Vector3(randf_range(-0.12, 0.12), randf_range(-0.08, 0.08), randf_range(-0.12, 0.12))
	var eixo := Vector3(randf_range(-1, 1), randf_range(-0.3, 0.3), randf_range(-1, 1))
	_capsulas.append({"p": pos, "v": vel + jit, "chao": minf(chao, pos.y), "eixo": eixo.normalized() if eixo.length() > 0.1 else Vector3.RIGHT,
			"ang": randf() * TAU, "w": randf_range(16.0, 24.0) * (1.0 if randf() < 0.5 else -1.0), "rumo": randf() * TAU,
			"vida": 0.0, "quiques": 0, "parada": false})


func _mover_capsulas(delta: float) -> void:
	var vivas: Array[Dictionary] = []
	for c in _capsulas:
		c.vida += delta
		if c.vida >= VIDA_CAPSULA:
			continue
		if not c.parada:
			c.v.y -= 9.81 * delta
			c.p += c.v * delta
			c.ang += c.w * delta
			if c.p.y <= c.chao + RAIO_CAPSULA:
				c.p.y = c.chao + RAIO_CAPSULA
				if c.v.y < -0.6 and c.quiques < 2:          # quica (perde muito), depois para deitada
					c.v = Vector3(c.v.x * 0.5, -c.v.y * 0.35, c.v.z * 0.5)
					c.w *= 0.6
					c.quiques += 1
				else:
					c.parada = true
		vivas.append(c)
	_capsulas = vivas
	_mm_capsulas.visible_instance_count = _capsulas.size()
	for i in _capsulas.size():
		var c: Dictionary = _capsulas[i]
		var s := clampf((VIDA_CAPSULA - c.vida) / 0.5, 0.0, 1.0)
		var b: Basis
		if c.parada:
			b = Basis.from_euler(Vector3(0.0, c.rumo, PI * 0.5))     # deitada no chão
		else:
			b = Basis(c.eixo, c.ang)
		_mm_capsulas.set_instance_transform(i, Transform3D(b.scaled(Vector3(s, s, s)), c.p))


## Quantas cápsulas estão no ar ou no chão agora (testes).
func capsulas() -> int:
	return _capsulas.size()


func _nova_fumacinha() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 10
	p.lifetime = 0.9
	p.local_coords = false
	p.emitting = false
	p.direction = Vector3(0, 1, 0)
	p.spread = 30.0
	p.initial_velocity_min = 0.12
	p.initial_velocity_max = 0.3
	p.gravity = Vector3(0.05, 0.3, 0.0)                # sobe devagar
	p.damping_min = 0.2
	p.damping_max = 0.4
	Fumaca.configurar(p, [Color(0.5, 0.48, 0.46, 0.0), Color(0.55, 0.53, 0.5, 0.5), Color(0.72, 0.71, 0.7, 0.0)], 0.10, 0.18, 2.6)
	add_child(p)
	return p


func _atualizar_fumacinhas(delta: float) -> void:
	for id in _fumacinhas.keys():
		var f: Dictionary = _fumacinhas[id]
		if not colonia.torres.has(id) or not mapa.estruturas.has(id):
			(f.no as Node).queue_free()
			_fumacinhas.erase(id)
			continue
		f.t = maxf(0.0, f.t - delta)
		(f.no as CPUParticles3D).emitting = f.t > 0.0
