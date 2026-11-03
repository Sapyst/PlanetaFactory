extends Node3D
## Automatizador da Parte B (PlanetaFactory):
## 1) Renderiza a folha de 4 quadros em sequência (começo, meio, fim, em fundo neutro dia e noite) para cada um dos 28 efeitos.
## 2) Mede o desempenho com 20 instâncias simultâneas do mesmo efeito na tela (FPS e ms/quadro) e grava relatorio_benchmark.json.

const LISTA_EFEITOS := [
	"rastro_metralhadora", "rastro_torre_energia", "rastro_lanca_foguetes", "rastro_foguete_enxame",
	"rastro_artilharia", "rastro_municao_perfurante", "rastro_municao_carregada", "rastro_drone_combate",
	"impacto_metralhadora", "impacto_torre_energia", "impacto_lanca_foguetes", "impacto_foguete_enxame",
	"impacto_artilharia", "impacto_municao_perfurante", "impacto_municao_carregada", "impacto_drone_combate",
	"explosao_foguete", "explosao_artilharia", "disparo_mina_pulso",
	"amb_brilho_jazida_cristal", "amb_faisca_fungo_noite", "amb_esporos_cogumelo", "amb_vagalumes_flor",
	"amb_reflexo_agua", "amb_poeira_vento", "amb_vapor_seiva", "amb_brasa_queimado", "geiser_termico"
]

const TEMPOS_QUADROS := [0.14, 0.38, 0.64, 0.88]
const LARG_Q := 440
const ALT_Q := 330

var _subviewports: Array[SubViewport] = []
var _cams_q: Array[Camera3D] = []
var _sois_q: Array[DirectionalLight3D] = []
var _ambs_q: Array[WorldEnvironment] = []
var _raizes_q: Array[Node3D] = []

var _palco_bench: Node3D
var _cam_bench: Camera3D


func _ready() -> void:
	_criar_subviewports_4_quadros()
	_criar_palco_benchmark()
	_executar_pipeline()


func _criar_subviewports_4_quadros() -> void:
	for q in range(4):
		var sv := SubViewport.new()
		sv.size = Vector2i(LARG_Q, ALT_Q)
		sv.own_world_3d = true
		sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		add_child(sv)
		_subviewports.append(sv)

		var raiz_c := Node3D.new()
		sv.add_child(raiz_c)

		var we := WorldEnvironment.new()
		var env := Environment.new()
		env.background_mode = Environment.BG_COLOR
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		we.environment = env
		raiz_c.add_child(we)
		_ambs_q.append(we)

		var sol := DirectionalLight3D.new()
		sol.rotation_degrees = Vector3(-46.0, 34.0, 0.0)
		sol.shadow_enabled = false
		raiz_c.add_child(sol)
		_sois_q.append(sol)

		var chao := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(22.0, 16.0)
		chao.mesh = pm
		var mat_c := StandardMaterial3D.new()
		mat_c.albedo_color = Color(0.22, 0.24, 0.22)
		mat_c.roughness = 0.92
		chao.material_override = mat_c
		raiz_c.add_child(chao)

		var cam := Camera3D.new()
		cam.current = true
		raiz_c.add_child(cam)
		_cams_q.append(cam)

		var conteiner_ef := Node3D.new()
		raiz_c.add_child(conteiner_ef)
		_raizes_q.append(conteiner_ef)


func _configurar_camera_e_clima_quadro(q: int, inst: Node3D) -> void:
	# Quadros 0 e 1 em fundo neutro Dia (ou Noite se o efeito for estritamente noturno);
	# Quadros 2 e 3 em fundo neutro Noite para comprovar leitura nos dois climas.
	var usar_noite: bool = bool(inst.get("modo_noturno")) or (q >= 2)
	_sois_q[q].light_energy = 0.24 if usar_noite else 1.25
	_sois_q[q].light_color = Color(0.55, 0.68, 0.95) if usar_noite else Color(1.0, 0.97, 0.90)
	var env := _ambs_q[q].environment
	env.background_color = Color(0.05, 0.06, 0.09) if usar_noite else Color(0.18, 0.20, 0.23)
	env.ambient_light_color = Color(0.15, 0.19, 0.28) if usar_noite else Color(0.45, 0.48, 0.52)
	env.ambient_light_energy = 0.48 if usar_noite else 0.85

	var cam := _cams_q[q]
	if "tipo_arma" in inst:
		cam.position = Vector3(0.0, 2.75, 4.35)
		cam.look_at_from_position(cam.position, Vector3(0.0, 0.72, 0.0), Vector3.UP)
		cam.fov = 46.0
	elif "tipo_impacto" in inst:
		cam.position = Vector3(0.0, 2.40, 3.85)
		cam.look_at_from_position(cam.position, Vector3(0.0, 0.48, 0.0), Vector3.UP)
		cam.fov = 44.0
	else:
		cam.position = Vector3(0.0, 1.80, 2.70)
		cam.look_at_from_position(cam.position, Vector3(0.0, 0.52, 0.0), Vector3.UP)
		cam.fov = 42.0


func _criar_palco_benchmark() -> void:
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.12, 0.14, 0.17)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.38, 0.42, 0.48)
	env.ambient_light_energy = 0.75
	we.environment = env
	add_child(we)

	var sol := DirectionalLight3D.new()
	sol.rotation_degrees = Vector3(-48.0, 32.0, 0.0)
	sol.light_energy = 1.0
	sol.shadow_enabled = false
	add_child(sol)

	var chao := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(36.0, 28.0)
	chao.mesh = pm
	var mat_c := StandardMaterial3D.new()
	mat_c.albedo_color = Color(0.20, 0.22, 0.20)
	mat_c.roughness = 0.92
	chao.material_override = mat_c
	add_child(chao)

	_cam_bench = Camera3D.new()
	_cam_bench.position = Vector3(0.0, 6.8, 9.5)
	_cam_bench.look_at_from_position(_cam_bench.position, Vector3(0.0, 0.4, -0.5), Vector3.UP)
	_cam_bench.fov = 50.0
	_cam_bench.current = true
	add_child(_cam_bench)

	_palco_bench = Node3D.new()
	add_child(_palco_bench)


func _executar_pipeline() -> void:
	await get_tree().process_frame
	await get_tree().process_frame

	var resultados: Dictionary = {}

	for idx in range(LISTA_EFEITOS.size()):
		var nome: String = LISTA_EFEITOS[idx]
		var cena := load("res://" + nome + ".tscn") as PackedScene
		if cena == null:
			push_error("Falha ao carregar cena: " + nome)
			continue

		# ------------------------------------------------------------------
		# 1. Captura da folha de 4 quadros (u = 0.14, 0.38, 0.64, 0.88)
		# ------------------------------------------------------------------
		var insts_q: Array[Node3D] = []
		for q in range(4):
			for ant in _raizes_q[q].get_children():
				ant.free()
			var inst_q: Node3D = cena.instantiate()
			inst_q.set("repetir_em_loop", false)
			_raizes_q[q].add_child(inst_q)
			inst_q.set("_ativo", false)
			inst_q.call("definir_progresso", TEMPOS_QUADROS[q])
			_configurar_camera_e_clima_quadro(q, inst_q)
			insts_q.append(inst_q)

		await get_tree().process_frame
		await get_tree().process_frame

		var img_folha := Image.create(LARG_Q * 4, ALT_Q, false, Image.FORMAT_RGBA8)
		for q in range(4):
			var img_q: Image = _subviewports[q].get_texture().get_image()
			img_q.convert(Image.FORMAT_RGBA8)
			img_folha.blit_rect(img_q, Rect2i(0, 0, LARG_Q, ALT_Q), Vector2i(q * LARG_Q, 0))

		var caminho_folha: String = ProjectSettings.globalize_path("res://fotos/folha_" + nome + ".png")
		img_folha.save_png(caminho_folha)

		var part_unit: int = int(insts_q[0].call("contagem_particulas"))
		var usa_luz: bool = bool(insts_q[0].call("usa_luz_dinamica"))
		var dur_ef: float = float(insts_q[0].get("duracao"))

		for q in range(4):
			for ant in _raizes_q[q].get_children():
				ant.free()

		# ------------------------------------------------------------------
		# 2. Benchmark com 20 instâncias simultâneas do mesmo efeito
		# ------------------------------------------------------------------
		for ant in _palco_bench.get_children():
			ant.free()

		for k in range(20):
			var inst_b: Node3D = cena.instantiate()
			var gx: int = k % 5
			var gz: int = k / 5
			inst_b.position = Vector3((float(gx) - 2.0) * 2.2, 0.0, (float(gz) - 1.5) * 1.8)
			inst_b.scale = Vector3.ONE * 0.45
			_palco_bench.add_child(inst_b)
			# Defasa o ciclo de cada uma das 20 instâncias para todas rodarem ativas em fases distintas
			var d_b: float = float(inst_b.get("duracao"))
			inst_b.set("_tempo", (float(k) / 20.0) * d_b)

		# 4 quadros de aquecimento + 16 quadros medidos
		for _w in range(4):
			await get_tree().process_frame

		var t0_usec: int = Time.get_ticks_usec()
		var soma_proc_ms: float = 0.0
		var n_medidos: int = 16
		for _m in range(n_medidos):
			await get_tree().process_frame
			soma_proc_ms += Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
		var dt_usec: int = Time.get_ticks_usec() - t0_usec

		var ms_parede: float = float(dt_usec) / 1000.0 / float(n_medidos)
		var ms_proc: float = soma_proc_ms / float(n_medidos)
		var ms_final: float = maxf(0.15, minf(ms_parede, ms_proc if ms_proc > 0.05 else ms_parede))
		var fps_est: float = minf(240.0, 1000.0 / maxf(0.1, ms_parede))

		print("EFEITO_OK %-28s | part=%3d (20x=%4d) | luz=%s | ms_20x=%.2f ms | fps=%.1f" % [
			nome, part_unit, part_unit * 20, "SIM" if usa_luz else "NAO", ms_parede, fps_est
		])

		resultados[nome] = {
			"arquivo_cena": nome + ".tscn",
			"arquivo_script": nome + ".gd",
			"folha_4_quadros": "fotos/folha_" + nome + ".png",
			"particulas_1x": part_unit,
			"particulas_20x": part_unit * 20,
			"usa_luz_dinamica": usa_luz,
			"duracao_s": snappedf(dur_ef, 0.01),
			"ms_quadro_20x": snappedf(ms_parede, 0.01),
			"ms_process_20x": snappedf(ms_final, 0.01),
			"fps_20x": snappedf(fps_est, 0.1)
		}

	for ant in _palco_bench.get_children():
		ant.free()

	var arq_json := FileAccess.open("res://relatorio_benchmark.json", FileAccess.WRITE)
	if arq_json != null:
		arq_json.store_string(JSON.stringify(resultados, "\t"))
		arq_json.close()

	print("GERAR_E_MEDIR_CONCLUIDO_OK")
	get_tree().quit(0)
