extends Node
## Autoload: o que o menu escolheu para a próxima partida e as configurações do jogador (salvas em user://).
##   modo: "novo" (mundo do zero, com núcleo e kit inicial), "continuar" (carrega o salvo), "demo" (fábrica pronta,
##   construção livre sem custo).

const ARQ_CONFIG := "user://configuracoes.cfg"

var modo := "demo"
var config := {"volume": 0.8, "sombras": true, "texto": 1.0, "autosalvar_s": 120, "resolucao": 1.0, "fps": true, "clima": true, "grama": true}   ## fps ligado por padrão na fase de testes


func _init() -> void:
	if OS.has_feature("mobile"):
		# celular: tela de altíssima resolução e GPU modesta — 3D a 70% (a interface continua nítida) e sem sombra
		config.resolucao = 0.7
		config.sombras = false
		DesenhoChunk.densidade_grama = 22.0         # gramado mais ralo no celular
	var cf := ConfigFile.new()
	if cf.load(ARQ_CONFIG) == OK:
		for k in config:
			config[k] = cf.get_value("jogo", k, config[k])


func salvar_config() -> void:
	var cf := ConfigFile.new()
	for k in config:
		cf.set_value("jogo", k, config[k])
	cf.save(ARQ_CONFIG)


## Aplica as configurações: tamanho da interface, volume (barramento Efeitos) e sombras do sol.
func aplicar() -> void:
	var tree := get_tree()
	if tree == null:
		return
	tree.root.content_scale_factor = float(config.texto)
	for b in ["Efeitos"]:
		if AudioServer.get_bus_index(b) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, b)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Efeitos"), linear_to_db(maxf(float(config.volume), 0.0001)))
	tree.root.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if float(config.resolucao) < 0.99 else Viewport.SCALING_3D_MODE_BILINEAR
	tree.root.scaling_3d_scale = float(config.resolucao)
	var cena := tree.current_scene
	if cena != null:
		var sol := cena.get_node_or_null("Sol") as DirectionalLight3D
		if sol != null:
			sol.shadow_enabled = bool(config.sombras)
		var amb := cena.get_node_or_null("Ambiente") as WorldEnvironment
		if amb != null:
			amb.environment.glow_enabled = not OS.has_feature("mobile")   # brilho custa caro na GPU do celular


var _fps_label: Label
var _fps_t := 0.0


func _ready() -> void:
	# contador de FPS embutido (canto de cima, no meio): vale para o menu e para o jogo
	var camada := CanvasLayer.new()
	camada.layer = 50
	add_child(camada)
	_fps_label = Label.new()
	_fps_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP, Control.PRESET_MODE_MINSIZE, 6)
	_fps_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_fps_label.add_theme_font_size_override("font_size", 18)
	_fps_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	_fps_label.add_theme_constant_override("outline_size", 6)
	_fps_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	camada.add_child(_fps_label)
	process_mode = Node.PROCESS_MODE_ALWAYS
	aplicar.call_deferred()


func _process(delta: float) -> void:
	_fps_label.visible = bool(config.fps)
	if not _fps_label.visible:
		return
	_fps_t -= delta
	if _fps_t > 0.0:
		return
	_fps_t = 0.25
	var fps := Engine.get_frames_per_second()
	_fps_label.text = "%d FPS · %.1f ms" % [fps, 1000.0 / maxf(fps, 1.0)]
	_fps_label.add_theme_color_override("font_color", Color(0.5, 1, 0.5) if fps >= 50 else (Color(1, 0.85, 0.3) if fps >= 28 else Color(1, 0.4, 0.35)))
