extends Node3D
## Vitrine interativa de todos os 28 efeitos do PlanetaFactory (Parte B).
## Permite alternar entre os efeitos (Setas Esquerda/Direita), alternar Dia/Noite (Espaço ou N)
## e testar o modo de 20 instâncias simultâneas (Tecla B).

const LISTA_EFEITOS := [
	"rastro_metralhadora", "rastro_torre_energia", "rastro_lanca_foguetes", "rastro_foguete_enxame",
	"rastro_artilharia", "rastro_municao_perfurante", "rastro_municao_carregada", "rastro_drone_combate",
	"impacto_metralhadora", "impacto_torre_energia", "impacto_lanca_foguetes", "impacto_foguete_enxame",
	"impacto_artilharia", "impacto_municao_perfurante", "impacto_municao_carregada", "impacto_drone_combate",
	"explosao_foguete", "explosao_artilharia", "disparo_mina_pulso",
	"amb_brilho_jazida_cristal", "amb_faisca_fungo_noite", "amb_esporos_cogumelo", "amb_vagalumes_flor",
	"amb_reflexo_agua", "amb_poeira_vento", "amb_vapor_seiva", "amb_brasa_queimado", "geiser_termico"
]

var _idx_atual: int = 0
var _noite: bool = false
var _modo_20x: bool = false
var _container_efeitos: Node3D
var _sol: DirectionalLight3D
var _amb: WorldEnvironment
var _lbl_info: Label


func _ready() -> void:
	_montar_cenario_base()
	_carregar_efeito_atual()


func _montar_cenario_base() -> void:
	_amb = WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_amb.environment = env
	add_child(_amb)

	_sol = DirectionalLight3D.new()
	_sol.rotation_degrees = Vector3(-45.0, 35.0, 0.0)
	_sol.shadow_enabled = false
	add_child(_sol)

	var chao := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(24.0, 16.0)
	chao.mesh = pm
	var mat_c := StandardMaterial3D.new()
	mat_c.albedo_color = Color(0.22, 0.24, 0.22)
	mat_c.roughness = 0.92
	chao.material_override = mat_c
	add_child(chao)

	var cam := Camera3D.new()
	cam.position = Vector3(0.0, 2.75, 4.45)
	cam.rotation_degrees = Vector3(-28.0, 0.0, 0.0)
	cam.fov = 45.0
	cam.current = true
	add_child(cam)

	_container_efeitos = Node3D.new()
	add_child(_container_efeitos)

	var canvas := CanvasLayer.new()
	add_child(canvas)
	_lbl_info = Label.new()
	_lbl_info.position = Vector2(18, 14)
	_lbl_info.add_theme_font_size_override("font_size", 18)
	canvas.add_child(_lbl_info)
	_atualizar_clima()


func _atualizar_clima() -> void:
	_sol.light_energy = 0.22 if _noite else 1.25
	_sol.light_color = Color(0.55, 0.68, 0.95) if _noite else Color(1.0, 0.97, 0.90)
	_amb.environment.background_color = Color(0.05, 0.06, 0.09) if _noite else Color(0.18, 0.20, 0.23)
	_amb.environment.ambient_light_color = Color(0.14, 0.18, 0.28) if _noite else Color(0.45, 0.48, 0.52)
	_amb.environment.ambient_light_energy = 0.45 if _noite else 0.85


func _carregar_efeito_atual() -> void:
	for c in _container_efeitos.get_children():
		c.queue_free()
	var nome: String = LISTA_EFEITOS[_idx_atual]
	var cena := load("res://" + nome + ".tscn") as PackedScene
	if cena == null:
		return
	var qtd_inst: int = 20 if _modo_20x else 1
	var part_unit: int = 0
	for k in range(qtd_inst):
		var inst: Node3D = cena.instantiate()
		if qtd_inst > 1:
			var gx: int = k % 5
			var gz: int = k / 5
			inst.position = Vector3((float(gx) - 2.0) * 1.65, 0.0, (float(gz) - 1.5) * 1.25)
			inst.scale = Vector3.ONE * 0.48
		_container_efeitos.add_child(inst)
		if k == 0:
			part_unit = inst.call("contagem_particulas")
			_noite = bool(inst.get("modo_noturno"))
			_atualizar_clima()
	_lbl_info.text = "[%d/%d] %s | Partículas: %d (x%d = %d) | Clima: %s | [Setas] Trocar  [N] Dia/Noite  [B] 20x" % [
		_idx_atual + 1, LISTA_EFEITOS.size(), nome, part_unit, qtd_inst, part_unit * qtd_inst,
		"NOITE" if _noite else "DIA"
	]


func _unhandled_key_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	var ek := event as InputEventKey
	if ek.keycode == KEY_RIGHT:
		_idx_atual = (_idx_atual + 1) % LISTA_EFEITOS.size()
		_carregar_efeito_atual()
	elif ek.keycode == KEY_LEFT:
		_idx_atual = (_idx_atual - 1 + LISTA_EFEITOS.size()) % LISTA_EFEITOS.size()
		_carregar_efeito_atual()
	elif ek.keycode == KEY_N or ek.keycode == KEY_SPACE:
		_noite = not _noite
		_atualizar_clima()
	elif ek.keycode == KEY_B:
		_modo_20x = not _modo_20x
		_carregar_efeito_atual()
