extends Node
## Autoload: toca os sons (assets/sons, gerados por ferramentas/gerar_sons.py) e a trilha em loop.
## Sons do mundo saem posicionados (mais baixo longe da câmera); cada som tem um intervalo mínimo para uma
## rajada de tiros não virar ruído. Barramentos "Efeitos" e "Musica" (volumes nas configurações).

const INTERVALO := {"tiro": 0.07, "construir": 0.05, "clique": 0.03, "aranha_morre": 0.08, "alerta": 4.0, "apito_trem": 3.0, "trovao": 1.5, "fogo": 2.0, "faisca": 0.15}

var _sons: Dictionary = {}
var _ultimo: Dictionary = {}
var _pool2d: Array[AudioStreamPlayer] = []
var _pool3d: Array[AudioStreamPlayer3D] = []
var _musica: AudioStreamPlayer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for f in DirAccess.get_files_at("res://assets/sons"):
		var nome := f.get_basename()
		if f.ends_with(".wav") and not _sons.has(nome):
			_sons[nome] = load("res://assets/sons/" + f)
		elif f.ends_with(".wav.import") and not _sons.has(nome.get_basename()):
			_sons[nome.get_basename()] = load("res://assets/sons/" + nome)
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.bus = "Efeitos"
		add_child(p)
		_pool2d.append(p)
	for i in 10:
		var p := AudioStreamPlayer3D.new()
		p.bus = "Efeitos"
		p.unit_size = 18.0
		p.max_distance = 160.0
		add_child(p)
		_pool3d.append(p)
	_musica = AudioStreamPlayer.new()
	_musica.bus = "Musica"
	add_child(_musica)


func tocar(nome: String, onde := Vector3.INF, volume_db := 0.0) -> void:
	if not _sons.has(nome) or DisplayServer.get_name() == "headless":
		return
	var agora := Time.get_ticks_msec() / 1000.0
	if agora - float(_ultimo.get(nome, -99.0)) < float(INTERVALO.get(nome, 0.0)):
		return
	_ultimo[nome] = agora
	if onde == Vector3.INF:
		var p := _livre2d()
		p.stream = _sons[nome]
		p.volume_db = volume_db
		p.pitch_scale = randf_range(0.97, 1.03)
		p.play()
	else:
		var p := _livre3d()
		p.stream = _sons[nome]
		p.global_position = onde
		p.volume_db = volume_db
		p.pitch_scale = randf_range(0.94, 1.06)
		p.play()


func musica(ligar := true) -> void:
	if not ligar or not _sons.has("trilha") or DisplayServer.get_name() == "headless":
		_musica.stop()
		return
	if _musica.playing:
		return
	var s: AudioStreamWAV = _sons["trilha"]
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_end = s.data.size() / 2
	_musica.stream = s
	_musica.play()


func _livre2d() -> AudioStreamPlayer:
	for p in _pool2d:
		if not p.playing:
			return p
	return _pool2d[0]


func _livre3d() -> AudioStreamPlayer3D:
	for p in _pool3d:
		if not p.playing:
			return p
	return _pool3d[0]
