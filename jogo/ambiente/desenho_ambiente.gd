class_name DesenhoAmbiente
extends Node3D
## Desenha o AmbienteVivo: manda o mapa de cada chunk mudado para o chão (1×/s), e o fogo — chamas e fumaça só nos
## focos perto da câmera (limite fixo de emissores, reaproveitados).

const MAX_CHAMAS := 36
const MAX_LUZES := 4                ## luz laranja nos aglomerados de fogo mais perto (ilumina o entorno)

var ambiente: AmbienteVivo
var chunks: Dictionary              ## o dicionário de chunks do mundo (DesenhoChunk)
var camera: CameraJogo
var clima: Clima
var _t := 0.0
var _chamas: Array[CPUParticles3D] = []
var _fumacas: Array[CPUParticles3D] = []
var _som_t := 0.0
var _t_fogo := 0.0
var _luzes: Array[OmniLight3D] = []
var _img_fogo: Image
var _tex_fogo: ImageTexture
var _t_veg := 0.0
const LADO_FOGO := 96
var _plumas: Array[CPUParticles3D] = []


var _mat_chama: ShaderMaterial
var _rampa_chama: Gradient
var pool_efeitos: PoolEfeitos
var _t_amb: float = 0.0



func _ready() -> void:
	pool_efeitos = PoolEfeitos.new()
	add_child(pool_efeitos)
	_mat_chama = ShaderMaterial.new()
	_mat_chama.shader = load("res://render/shaders/chama.gdshader")
	_mat_chama.set_shader_parameter("ruido", load("res://assets/texturas/ruido_detalhe.png"))
	_rampa_chama = Gradient.new()                       # r = vida (sobe linear), a = força (nasce, segura, morre)
	_rampa_chama.set_color(0, Color(0.0, 0, 0, 0.0))
	_rampa_chama.add_point(0.12, Color(0.12, 0, 0, 1.0))
	_rampa_chama.add_point(0.6, Color(0.6, 0, 0, 0.85))
	_rampa_chama.set_color(1, Color(1.0, 0, 0, 0.0))
	for i in MAX_LUZES:
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.42, 0.12)
		l.omni_range = 4.5
		l.omni_attenuation = 2.2
		l.shadow_enabled = false
		l.visible = false
		add_child(l)
		_luzes.append(l)
		# pluma: fumaça escura comprida, sobe e deita na direção do vento
		var pl := CPUParticles3D.new()
		pl.amount = 46
		pl.lifetime = 7.0
		pl.local_coords = false
		pl.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
		pl.emission_sphere_radius = 1.4
		pl.direction = Vector3.UP
		pl.spread = 18.0
		pl.initial_velocity_min = 0.6
		pl.initial_velocity_max = 1.0
		pl.damping_min = 0.15
		pl.damping_max = 0.3
		Fumaca.configurar(pl, [Color(0.3, 0.29, 0.29, 0.0), Color(0.34, 0.33, 0.33, 0.22), Color(0.6, 0.6, 0.61, 0.0)], 2.2, 3.4, 5.0)
		pl.emitting = false
		add_child(pl)
		_plumas.append(pl)
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
		# chama procedural (render/shaders/chama.gdshader): todas as partículas usam o mesmo material
		var q := QuadMesh.new()
		q.size = Vector2(0.8, 1.2)
		q.center_offset = Vector3(0, 0.45, 0)
		q.material = _mat_chama
		c.mesh = q
		c.amount = 9
		c.lifetime = 1.0
		c.emission_box_extents = Vector3(0.42, 0.02, 0.42)
		c.initial_velocity_min = 0.15
		c.initial_velocity_max = 0.4
		c.gravity = Vector3(0, 0.25, 0)
		c.scale_amount_min = 0.55
		c.scale_amount_max = 1.25
		c.color_ramp = _rampa_chama
		c.scale_amount_curve = null
		c.emitting = false
		add_child(c)
		_chamas.append(c)
		var f := CPUParticles3D.new()
		f.amount = 4
		f.lifetime = 2.5
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
func _tex_chama_antiga() -> Texture2D:
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
	if clima != null:
		var w: Vector2 = clima.direcao_vento * (0.3 + 1.4 * clima.valores.vento)
		_mat_chama.set_shader_parameter("vento", Vector2(w.x, -w.y))
	for l in _luzes:
		if l.visible:
			l.light_energy = clampf(l.light_energy + randf_range(-0.2, 0.2), 0.5, 1.8)     # tremula
	_t_veg -= delta
	if _t_veg <= 0.0:
		_t_veg = 0.3
		_mapa_vegetacao()
	_t_fogo -= delta
	if _t_fogo <= 0.0:
		_t_fogo = 0.25
		_atualizar_fogo()
	_t_amb -= delta
	if _t_amb <= 0.0:
		_t_amb = 0.5
		_atualizar_brilhos_ambiente()
	if not ambiente.fogo.is_empty():
		_som_t -= delta
		if _som_t <= 0.0:
			_som_t = 2.2
			Som.tocar("fogo", Vector3.INF, -10.0)


## Mapa global (96×96 tiles em volta da câmera): B = queimando agora, A = queimado (vegetação); R = encardido da
## estrutura que ocupa o tile (material_pf). Só os tiles com algo (o resto fica transparente) — barato.
func _mapa_vegetacao() -> void:
	if _img_fogo == null:
		_img_fogo = Image.create(LADO_FOGO, LADO_FOGO, false, Image.FORMAT_RGBA8)
		_tex_fogo = ImageTexture.create_from_image(_img_fogo)
		RenderingServer.global_shader_parameter_set("fogo_mapa", _tex_fogo)
	var c := Grade.tile_de_mundo(camera.alvo) - Vector2i(LADO_FOGO / 2, LADO_FOGO / 2)
	_img_fogo.fill(Color(0, 0, 0, 0))
	for k in ambiente.dados:
		var base: Vector2i = k * AmbienteVivo.T
		if base.x + AmbienteVivo.T < c.x or base.y + AmbienteVivo.T < c.y or base.x > c.x + LADO_FOGO or base.y > c.y + LADO_FOGO:
			continue
		var arr: PackedFloat32Array = ambiente.dados[k]
		for i in AmbienteVivo.T * AmbienteVivo.T:
			var q := arr[i * 4 + 3]
			if q <= 0.01:
				continue
			var t := base + Vector2i(i % AmbienteVivo.T, i / AmbienteVivo.T) - c
			if t.x >= 0 and t.y >= 0 and t.x < LADO_FOGO and t.y < LADO_FOGO:
				_img_fogo.set_pixel(t.x, t.y, Color(0, 0, 0, q))
	for id in ambiente.encardido:                                  # encardido das estruturas, tile a tile
		var g: float = ambiente.encardido[id]
		if g <= 0.004 or not ambiente.mapa.estruturas.has(id):
			continue
		var e: Dictionary = ambiente.mapa.estruturas[id]
		var m: Vector2i = e.minimo - c
		if m.x < -4 or m.y < -4 or m.x > LADO_FOGO or m.y > LADO_FOGO:
			continue                                               # longe da câmera
		for t in Grade.tiles_da_area(e.minimo, e.area, e.rot):
			var l: Vector2i = t - c
			if l.x >= 0 and l.y >= 0 and l.x < LADO_FOGO and l.y < LADO_FOGO:
				var px := _img_fogo.get_pixel(l.x, l.y)
				_img_fogo.set_pixel(l.x, l.y, Color(g, px.g, px.b, px.a))
	for t in ambiente.fogo:
		var l: Vector2i = t - c
		if l.x >= 0 and l.y >= 0 and l.x < LADO_FOGO and l.y < LADO_FOGO:
			var px := _img_fogo.get_pixel(l.x, l.y)
			_img_fogo.set_pixel(l.x, l.y, Color(px.r, 0, clampf(float(ambiente.fogo[t]) / 4.5 / ambiente._madeira(t), 0.0, 1.0), px.a))
	_tex_fogo.update(_img_fogo)
	RenderingServer.global_shader_parameter_set("fogo_origem", Vector2(c))


func _atualizar_fogo() -> void:
	var olho := Vector2(camera.alvo.x, -camera.alvo.z)
	var lista: Array = ambiente.fogo.keys()
	lista.sort_custom(func(a, b): return Vector2(a).distance_squared_to(olho) < Vector2(b).distance_squared_to(olho))
	for i in MAX_CHAMAS:
		var ligar := i < lista.size() and Vector2(lista[i]).distance_to(olho) < camera.distancia * 1.4 and Visao.dentro(Vector2(lista[i]), 1.1)
		_chamas[i].emitting = false            # fogo é desenhado no chão e na grama (sem sprite)
		_fumacas[i].emitting = false
		if ligar:
			var p := Grade.centro_mundo(lista[i], 0.02)
			_chamas[i].global_position = p
			_fumacas[i].global_position = p + Vector3(0, 0.3, 0)
	# aglomerados: média dos focos perto de cada um dos mais próximos → luz + pluma
	var usados := 0
	var centros: Array[Vector2] = []
	for t in lista:
		if usados >= MAX_LUZES:
			break
		var tp := Vector2(t) + Vector2(0.5, 0.5)
		var longe := true
		for c in centros:
			longe = longe and c.distance_to(tp) > 6.0
		if not longe:
			continue
		var soma := Vector2.ZERO
		var n := 0
		for u in lista:
			var up := Vector2(u) + Vector2(0.5, 0.5)
			if up.distance_to(tp) < 5.0:
				soma += up
				n += 1
		var m := soma / n
		centros.append(m)
		var l := _luzes[usados]
		l.visible = true
		l.global_position = Grade.ponto_mundo(m, 1.2)
		l.light_energy = 0.7 + minf(1.0, n * 0.06) + randf() * 0.3
		var pl := _plumas[usados]
		pl.emitting = true
		pl.global_position = Grade.ponto_mundo(m, 0.6)
		var w := Vector2.ZERO
		if clima != null:
			w = clima.direcao_vento * (0.8 + 2.2 * clima.valores.vento)
		pl.gravity = Vector3(w.x, 0.12, -w.y) * 1.0 + Vector3(w.x, 0, -w.y) * 1.2
		pl.emission_sphere_radius = 0.8 + minf(2.5, n * 0.08)
		usados += 1
	for i in range(usados, MAX_LUZES):
		_luzes[i].visible = false
		_plumas[i].emitting = false


## Posiciona os efeitos procedurais de ambiente onde a coisa existe perto da visão da câmera.
func _atualizar_brilhos_ambiente() -> void:
	if pool_efeitos == null:
		return
	pool_efeitos.desativar_ambientes()
	if camera == null or chunks == null or chunks.is_empty():
		return
	var olho := Vector2(camera.alvo.x, -camera.alvo.z)
	var raio_busca: float = camera.distancia * 1.35 + 16.0
	var noite: bool = (clima != null and clima.luz_dia() < 0.35)
	var crepusculo: bool = (clima != null and clima.luz_dia() < 0.55)
	var vento_forte: bool = (clima != null and clima.valores.vento > 0.6)

	for k in chunks:
		var chk = chunks[k]
		if not is_instance_valid(chk) or not (chk is DesenhoChunk):
			continue
		var dados: Dictionary = chk._dados
		if dados.is_empty() or not dados.has("transf"):
			continue
		var base_chunk := Vector2(k * Grade.TAM_CHUNK) + Vector2.ONE * (Grade.TAM_CHUNK * 0.5)
		if base_chunk.distance_to(olho) > raio_busca + Grade.TAM_CHUNK:
			continue
		var transf: Dictionary = dados.transf

		# 1. Jazida de cristal (refrata luz e desprende micro-prismas)
		if transf.has("jazida_cristal"):
			for t: Transform3D in transf["jazida_cristal"]:
				if Vector2(t.origin.x, -t.origin.z).distance_to(olho) < raio_busca:
					var inst := pool_efeitos.alocar_ambiente("brilho_jazida_cristal")
					if inst != null:
						inst.global_position = t.origin + Vector3(0, 0.12, 0)
						inst.visible = true
						inst._ativo = true

		# 2. Esporos de cogumelos gigantes (a e b)
		for cog in ["cogumelo_gigante_a", "cogumelo_gigante_b"]:
			if transf.has(cog):
				for t: Transform3D in transf[cog]:
					if Vector2(t.origin.x, -t.origin.z).distance_to(olho) < raio_busca:
						var inst := pool_efeitos.alocar_ambiente("esporos_cogumelo")
						if inst != null:
							inst.global_position = t.origin + Vector3(0, 1.4, 0)
							inst.visible = true
							inst._ativo = true

		# 3. Faíscas no fungo à noite
		if noite:
			for i in range(1, 7):
				var f_nome := "arv_fungo_cristal_%d" % i
				if transf.has(f_nome):
					for t: Transform3D in transf[f_nome]:
						if Vector2(t.origin.x, -t.origin.z).distance_to(olho) < raio_busca:
							var inst := pool_efeitos.alocar_ambiente("faisca_fungo_noite")
							if inst != null:
								inst.global_position = t.origin + Vector3(0, 1.35, 0)
								inst.visible = true
								inst._ativo = true

		# 4. Vaga-lumes na flor luminosa (ao entardecer / noite)
		if crepusculo and transf.has("flor_luminosa"):
			for t: Transform3D in transf["flor_luminosa"]:
				if Vector2(t.origin.x, -t.origin.z).distance_to(olho) < raio_busca:
					var inst := pool_efeitos.alocar_ambiente("vagalumes_flor")
					if inst != null:
						inst.global_position = t.origin + Vector3(0, 0.45, 0)
						inst.visible = true
						inst._ativo = true

		# 5. Reflexo de água na rocha de água / margem
		if transf.has("rocha_agua"):
			for t: Transform3D in transf["rocha_agua"]:
				if Vector2(t.origin.x, -t.origin.z).distance_to(olho) < raio_busca:
					var inst := pool_efeitos.alocar_ambiente("reflexo_agua")
					if inst != null:
						inst.global_position = t.origin + Vector3(0, 0.05, 0)
						inst.visible = true
						inst._ativo = true

		# 6. Vapor de seiva sobre poça de seiva
		if transf.has("poca_seiva"):
			for t: Transform3D in transf["poca_seiva"]:
				if Vector2(t.origin.x, -t.origin.z).distance_to(olho) < raio_busca:
					var inst := pool_efeitos.alocar_ambiente("vapor_seiva")
					if inst != null:
						inst.global_position = t.origin + Vector3(0, 0.08, 0)
						inst.visible = true
						inst._ativo = true

	# 7. Poeira com vento forte no chão
	if vento_forte:
		var inst_p := pool_efeitos.alocar_ambiente("poeira_vento")
		if inst_p != null:
			inst_p.global_position = Grade.ponto_mundo(olho, 0.08)
			inst_p.visible = true
			inst_p._ativo = true

	# 8. Brasa em chão recém-queimado
	if ambiente != null and not ambiente.fogo.is_empty():
		var focos: Array = ambiente.fogo.keys()
		for i in mini(focos.size(), 4):
			var tile: Vector2i = focos[i]
			if Vector2(tile).distance_to(olho) < raio_busca:
				var inst_b := pool_efeitos.alocar_ambiente("brasa_queimado")
				if inst_b != null:
					inst_b.global_position = Grade.centro_mundo(tile, 0.04)
					inst_b.visible = true
					inst_b._ativo = true

