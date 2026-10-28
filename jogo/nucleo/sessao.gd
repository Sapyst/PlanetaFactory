extends Node
## Autoload: o que o menu escolheu para a próxima partida e as configurações do jogador (salvas em user://).
##   modo: "novo" (mundo do zero, com núcleo e kit inicial), "continuar" (carrega o salvo), "demo" (fábrica pronta,
##   construção livre sem custo).

const ARQ_CONFIG := "user://configuracoes.cfg"

var modo := "demo"
var config := {"volume": 0.8, "musica": 0.5, "sombras": true, "texto": 1.0, "autosalvar_s": 120}


func _init() -> void:
	var cf := ConfigFile.new()
	if cf.load(ARQ_CONFIG) == OK:
		for k in config:
			config[k] = cf.get_value("jogo", k, config[k])


func salvar_config() -> void:
	var cf := ConfigFile.new()
	for k in config:
		cf.set_value("jogo", k, config[k])
	cf.save(ARQ_CONFIG)


## Aplica as configurações: tamanho da interface, volumes (barramentos Efeitos e Musica) e sombras do sol.
func aplicar() -> void:
	var tree := get_tree()
	if tree == null:
		return
	tree.root.content_scale_factor = float(config.texto)
	for b in ["Efeitos", "Musica"]:
		if AudioServer.get_bus_index(b) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, b)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Efeitos"), linear_to_db(maxf(float(config.volume), 0.0001)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Musica"), linear_to_db(maxf(float(config.musica), 0.0001)))
	var cena := tree.current_scene
	if cena != null:
		var sol := cena.get_node_or_null("Sol") as DirectionalLight3D
		if sol != null:
			sol.shadow_enabled = bool(config.sombras)


func _ready() -> void:
	aplicar.call_deferred()
