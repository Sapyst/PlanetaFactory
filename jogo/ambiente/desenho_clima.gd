class_name DesenhoClima
extends Node3D
## Desenha o Clima (só lê a lógica):
##  - parâmetros globais de shader: sombra das nuvens (correndo com o vento) e chão molhado — ver clima.gdshaderinc;
##  - luz: sol e céu baixam com as nuvens; relâmpago acende tudo por um instante e o trovão vem depois;
##  - neblina: existe no mundo, não é filtro — pilha de fatias finas rente ao chão (ver neblina.gdshader), com corpo,
##    andando com o vento, abrindo onde há calor (`fontes_calor`); a névoa do ambiente só dá a distância;
##  - raios de sol: feixes descendo pelos buracos das nuvens (ver raios_sol.gdshader) — com céu parcialmente
##    nublado, mais fortes com ar úmido (depois da chuva, neblina);
##  - chuva: partículas na GPU só em volta do que a câmera vê (menos no celular), com som em loop.

const GOTAS_PC := 1600
const GOTAS_CELULAR := 600
const FATIAS_PC := 10
const FATIAS_CELULAR := 6
const TOPO_NEBLINA := 3.2
const FATIAS_RAIOS_PC := 14
const FATIAS_RAIOS_CELULAR := 7
const TOPO_RAIOS := 18.0
const COR_NEBLINA := Color(0.72, 0.74, 0.76)
const COR_TEMPESTADE := Color(0.36, 0.39, 0.43)

var clima: Clima
var camera: CameraJogo
var ambiente: WorldEnvironment
var sol: DirectionalLight3D
var fontes_calor: Callable           ## → Array de Vector3 (x, z do mundo, raio): onde a névoa abre

var _chuva: GPUParticles3D
var _proc: ParticleProcessMaterial
var _neblina: MeshInstance3D
var _mat_neblina: ShaderMaterial
var _fatias := 0
var _raios_sol: MeshInstance3D
var _mat_raios: ShaderMaterial
var _fatias_raios := 0
var _claros: Dictionary = {}         ## Vector2i(ponto arredondado) → [Vector3 fonte, força 0..1] (abre e fecha devagar)
var _raio: MeshInstance3D
var _malha_raio: ImmediateMesh
var _som_chuva: AudioStreamPlayer
var _base := {}
var _flash := 0.0
var _vida_raio := 0.0
var _trovoes: Array[float] = []      ## segundos até cada trovão pendente


func _ready() -> void:
	var env := ambiente.environment
	_base = {"sol": sol.light_energy, "ceu": env.ambient_light_energy, "neblina": env.fog_light_color,
			"saturacao": env.adjustment_saturation}
	_criar_chuva()
	_criar_neblina()
	_criar_raios_sol()
	_criar_raio()
	_som_chuva = AudioStreamPlayer.new()
	_som_chuva.bus = "Efeitos"
	add_child(_som_chuva)


func _process(delta: float) -> void:
	if clima == null:
		return
	clima.ativo = bool(Sessao.config.get("clima", true))
	var v := clima.valores
	RenderingServer.global_shader_parameter_set("nuvem_cobertura", v.nuvens)
	RenderingServer.global_shader_parameter_set("nuvem_deslocamento", clima.deslocamento)
	RenderingServer.global_shader_parameter_set("molhado", clima.molhado)
	RenderingServer.global_shader_parameter_set("sol_dir", sol.global_transform.basis.z.normalized())
	_relampagos(delta)
	# luz e névoa do ambiente
	var env := ambiente.environment
	sol.light_energy = _base.sol * v.luz + _flash * 2.6
	sol.shadow_opacity = 1.0 - 0.55 * v.nuvens      # céu fechado: luz difusa, sombra fraca
	env.ambient_light_energy = _base.ceu * (0.7 + 0.3 * v.luz) + _flash * 1.2
	var cor: Color = (_base.neblina as Color).lerp(COR_NEBLINA, v.neblina * 0.7).lerp(COR_TEMPESTADE, v.chuva * 0.65)
	env.fog_light_color = cor
	# névoa mais rala quanto mais longe a câmera (de longe o mapa não desbota); neblina engrossa em qualquer zoom
	env.fog_density = (0.055 + 0.05 * v.neblina + 0.06 * v.chuva) / camera.distancia
	env.adjustment_saturation = _base.saturacao - 0.18 * v.chuva - 0.10 * v.neblina
	_atualizar_neblina(delta, v.neblina, v.luz)
	_atualizar_raios_sol(v)
	_atualizar_chuva(v.chuva, v.vento)


# ------------------------------------------------------------------ chuva
func _criar_chuva() -> void:
	_chuva = GPUParticles3D.new()
	_chuva.amount = GOTAS_CELULAR if OS.has_feature("mobile") else GOTAS_PC
	_chuva.lifetime = 1.1
	_chuva.local_coords = false
	_chuva.visibility_aabb = AABB(Vector3(-70, -30, -70), Vector3(140, 60, 140))
	_chuva.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_proc = ParticleProcessMaterial.new()
	_proc.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	_proc.direction = Vector3.DOWN
	_proc.spread = 2.0
	_proc.initial_velocity_min = 17.0
	_proc.initial_velocity_max = 22.0
	_proc.gravity = Vector3(0, -9.8, 0)
	_chuva.process_material = _proc
	var gota := QuadMesh.new()
	gota.size = Vector2(0.025, 0.6)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	m.albedo_color = Color(0.78, 0.82, 0.88, 0.32)
	gota.material = m
	_chuva.draw_pass_1 = gota
	_chuva.emitting = false
	add_child(_chuva)


func _atualizar_chuva(chuva: float, vento: float) -> void:
	var ligar := chuva > 0.03
	if ligar != _chuva.emitting:
		_chuva.emitting = ligar
	var vol := linear_to_db(maxf(chuva * 0.9, 0.0001))
	if chuva > 0.03 and DisplayServer.get_name() != "headless":
		if not _som_chuva.playing and Som._sons.has("chuva"):
			var s: AudioStreamWAV = Som._sons["chuva"]
			s.loop_mode = AudioStreamWAV.LOOP_FORWARD
			s.loop_end = s.data.size() / 2
			_som_chuva.stream = s
			_som_chuva.play()
		_som_chuva.volume_db = vol
	elif _som_chuva.playing:
		_som_chuva.stop()
	if not ligar:
		return
	_chuva.amount_ratio = chuva
	# caixa de onde as gotas caem: segue o ponto olhado, do tamanho da vista (com limite)
	var e := clampf(camera.distancia * 0.55, 12.0, 45.0)
	_proc.emission_box_extents = Vector3(e, 3.0, e * 0.8)
	_chuva.global_position = camera.alvo + Vector3(0, 15, 0)
	var w := clima.direcao_vento * 7.0 * vento
	_proc.gravity = Vector3(w.x, -9.8, w.y)


# ------------------------------------------------------------------ neblina de chão
func _criar_neblina() -> void:
	_fatias = FATIAS_CELULAR if OS.has_feature("mobile") else FATIAS_PC
	_mat_neblina = ShaderMaterial.new()
	_mat_neblina.shader = load("res://ambiente/neblina.gdshader")
	_mat_neblina.set_shader_parameter("topo", TOPO_NEBLINA)
	_neblina = MeshInstance3D.new()
	_neblina.mesh = _fatias_planas(_fatias, TOPO_NEBLINA, 1.4)      # mais fatias perto do chão, onde é densa
	_neblina.material_override = _mat_neblina
	_neblina.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_neblina.extra_cull_margin = 8.0
	_neblina.visible = false
	add_child(_neblina)


func _atualizar_neblina(delta: float, neblina: float, luz: float) -> void:
	_neblina.visible = neblina > 0.03
	if not _neblina.visible:
		return
	var lado := clampf(camera.distancia * 2.6, 40.0, 320.0)
	_neblina.position = Vector3(camera.alvo.x, 0, camera.alvo.z)
	_neblina.scale = Vector3(lado, 1, lado)
	# a pilha inteira chega a ~90% onde é densa: cada fatia leva a sua parte
	var alvo := 0.9 * clampf(neblina, 0.0, 1.0)
	_mat_neblina.set_shader_parameter("alfa_fatia", 1.0 - pow(1.0 - alvo, 1.0 / _fatias))
	var c := ambiente.environment.fog_light_color
	_mat_neblina.set_shader_parameter("cor_luz", c * (0.75 + 0.35 * luz))
	_mat_neblina.set_shader_parameter("cor_base", c * (0.55 + 0.2 * luz) * Color(0.95, 0.98, 1.05))
	_mat_neblina.set_shader_parameter("flash", _flash)
	_atualizar_claros(delta)


## Calor abre a névoa aos poucos e ela volta a fechar quando a fonte para (16 mais perto da câmera).
func _atualizar_claros(delta: float) -> void:
	var vivas := {}
	if fontes_calor.is_valid():
		for f: Vector3 in fontes_calor.call():
			vivas[Vector2i(roundi(f.x), roundi(f.y))] = f
	for k in vivas:
		if not _claros.has(k):
			_claros[k] = [vivas[k], 0.0]
		_claros[k][0] = vivas[k]
	var lista: Array = []
	for k in _claros.keys():
		var cl: Array = _claros[k]
		cl[1] = clampf(cl[1] + (delta / 2.5 if vivas.has(k) else -delta / 6.0), 0.0, 1.0)
		if cl[1] <= 0.0 and not vivas.has(k):
			_claros.erase(k)
			continue
		lista.append(cl)
	var olho := Vector2(camera.alvo.x, camera.alvo.z)
	lista.sort_custom(func(a, b): return Vector2(a[0].x, a[0].y).distance_squared_to(olho) < Vector2(b[0].x, b[0].y).distance_squared_to(olho))
	var arr := PackedVector4Array()
	arr.resize(16)
	var n := mini(lista.size(), 16)
	for i in n:
		var f: Vector3 = lista[i][0]
		arr[i] = Vector4(f.x, f.y, f.z, smoothstep(0.0, 1.0, lista[i][1]))
	_mat_neblina.set_shader_parameter("claros", arr)
	_mat_neblina.set_shader_parameter("n_claros", n)


# ------------------------------------------------------------------ raios de sol
func _fatias_planas(n: int, topo: float, curva: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for f in n:
		var y := topo * pow((f + 0.5) / n, curva)
		var c := [Vector3(-0.5, y, -0.5), Vector3(0.5, y, -0.5), Vector3(0.5, y, 0.5), Vector3(-0.5, y, 0.5)]
		var uv := [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]
		for k in [0, 1, 2, 0, 2, 3]:
			st.set_uv(uv[k])
			st.add_vertex(c[k])
	return st.commit()


func _criar_raios_sol() -> void:
	_fatias_raios = FATIAS_RAIOS_CELULAR if OS.has_feature("mobile") else FATIAS_RAIOS_PC
	_mat_raios = ShaderMaterial.new()
	_mat_raios.shader = load("res://ambiente/raios_sol.gdshader")
	_mat_raios.set_shader_parameter("topo", TOPO_RAIOS)
	_raios_sol = MeshInstance3D.new()
	_raios_sol.mesh = _fatias_planas(_fatias_raios, TOPO_RAIOS, 1.0)
	_raios_sol.material_override = _mat_raios
	_raios_sol.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_raios_sol.extra_cull_margin = 20.0
	_raios_sol.visible = false
	add_child(_raios_sol)


func _atualizar_raios_sol(v: Dictionary) -> void:
	# feixe só existe com céu QUASE fechado: poucos buracos pequenos, cada um uma coluna de luz com escuro em volta
	# (céu aberto = sol em tudo = nenhum feixe); ar úmido (depois da chuva, neblina) deixa o feixe mais visível
	var buracos: float = smoothstep(0.68, 0.8, v.nuvens) * (1.0 - smoothstep(0.93, 0.99, v.nuvens))
	var umidade: float = 0.45 + 0.35 * clima.molhado + 0.5 * v.neblina
	var f: float = buracos * smoothstep(0.45, 0.7, v.luz) * umidade
	_raios_sol.visible = f > 0.02
	if not _raios_sol.visible:
		return
	var lado := clampf(camera.distancia * 2.8, 50.0, 340.0)
	_raios_sol.position = Vector3(camera.alvo.x, 0, camera.alvo.z)
	_raios_sol.scale = Vector3(lado, 1, lado)
	_mat_raios.set_shader_parameter("forca", f * 0.75 / _fatias_raios)
	_mat_raios.set_shader_parameter("cor", sol.light_color)


# ------------------------------------------------------------------ relâmpagos
func _criar_raio() -> void:
	_malha_raio = ImmediateMesh.new()
	_raio = MeshInstance3D.new()
	_raio.mesh = _malha_raio
	_raio.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = Color(0.92, 0.95, 1.0)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	_raio.material_override = m
	add_child(_raio)


func _relampagos(delta: float) -> void:
	for ev in clima.eventos:
		if ev == "raio":
			_flash = 1.0
			_vida_raio = 0.22
			_desenhar_raio()
			_trovoes.append(randf_range(0.6, 2.6))
	clima.eventos.clear()
	# dois piscos: acende, cai, volta um pouco e apaga
	_flash = maxf(0.0, _flash - delta * 5.0)
	if _vida_raio > 0.0:
		_vida_raio -= delta
		if _vida_raio <= 0.0:
			_malha_raio.clear_surfaces()
		elif _vida_raio < 0.12 and _vida_raio + delta >= 0.12:
			_flash = 0.7
	for i in range(_trovoes.size() - 1, -1, -1):
		_trovoes[i] -= delta
		if _trovoes[i] <= 0.0:
			Som.tocar("trovao", Vector3.INF, -2.0)
			_trovoes.remove_at(i)


## Linha quebrada do céu ao chão num ponto aleatório da vista, em fita virada para a câmera.
func _desenhar_raio() -> void:
	var r := camera.distancia * 0.5
	var chao := camera.alvo + Vector3(randf_range(-r, r), 0, randf_range(-r * 0.7, r * 0.7))
	var pts: Array[Vector3] = []
	var n := 9
	for i in n + 1:
		var t := float(i) / n
		var p := chao + Vector3(0, 45.0 * (1.0 - t), 0)
		if i > 0 and i < n:
			p += Vector3(randf_range(-2.2, 2.2), 0, randf_range(-2.2, 2.2))
		pts.append(p)
	_malha_raio.clear_surfaces()
	_malha_raio.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in n:
		var a := pts[i]
		var b := pts[i + 1]
		var olho := (camera.global_position - a).normalized()
		var lado := (b - a).normalized().cross(olho).normalized() * 0.18
		var q := [a - lado, a + lado, b + lado, b - lado]
		for k in [0, 1, 2, 0, 2, 3]:
			_malha_raio.surface_add_vertex(q[k])
	_malha_raio.surface_end()
