class_name DesenhoColonia
extends Node3D
## Desenha a Colonia: aranhas (nó Aranha com marcha e IK, seguindo a posição lógica), ninhos (crescem durante a
## obra), tiros das torres (traço luminoso + torre mirando), faíscas de morte, barras de vida das estruturas
## mordidas. Só lê a lógica e os eventos do tick — não decide nada.

const FAISCA := Color(1.0, 0.65, 0.25)

var colonia: Colonia
var mapa: MapaOcupacao
var animadores_torre: Callable      ## id da torre → Animador (ou null), vem do mundo

var _aranhas: Dictionary = {}       ## id → Aranha
var _ninhos: Dictionary = {}        ## id → Node3D
var _tracos: Array[Dictionary] = [] ## {de: Vector3, para: Vector3, vida: float}
var _malha_tracos: ImmediateMesh
var _barras: Dictionary = {}        ## id → [fundo, frente]
var _mat_traco: StandardMaterial3D


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


## Chamado a cada quadro, depois do tick lógico. `eventos` = os acumulados desde o último quadro.
func atualizar(eventos: Array[Dictionary], delta: float) -> void:
	for e in eventos:
		match e.tipo:
			"tiro":
				var de := Grade.ponto_mundo(e.de, 1.25)
				var para := Grade.ponto_mundo(e.para, 0.6)
				_tracos.append({"de": de + (para - de).normalized() * 0.9, "para": para, "vida": 0.10})
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
	_desenhar_barras()


## Só ganha nó (marcha + IK a cada quadro) a aranha perto do que a câmera vê; as outras seguem só na lógica.
func _perto_da_vista(p: Vector2) -> bool:
	var cam := get_viewport().get_camera_3d() as CameraJogo
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
