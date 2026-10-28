class_name PainelConfig
extends VBoxContainer
## Configurações (menu inicial e pausa): volumes, tamanho da interface (acessibilidade), sombras, autosalvar.
## Cada mudança aplica na hora e grava em user://configuracoes.cfg.

signal voltar


func _ready() -> void:
	add_theme_constant_override("separation", 10)
	var t := Label.new()
	t.text = "Configurações"
	t.add_theme_font_size_override("font_size", 26)
	add_child(t)
	_deslizante("Volume dos efeitos", "volume", 0.0, 1.0, 0.05)
	_deslizante("Volume da música", "musica", 0.0, 1.0, 0.05)
	_deslizante("Tamanho da interface", "texto", 0.8, 1.6, 0.1)
	_deslizante("Resolução do 3D (menos = mais leve)", "resolucao", 0.5, 1.0, 0.05)
	var sombra := CheckButton.new()
	sombra.text = "Sombras (desligar deixa mais leve no celular)"
	sombra.button_pressed = bool(Sessao.config.sombras)
	sombra.toggled.connect(func(v: bool): _mudar("sombras", v))
	add_child(sombra)
	var fps := CheckButton.new()
	fps.text = "Mostrar FPS (quadros por segundo)"
	fps.button_pressed = bool(Sessao.config.fps)
	fps.toggled.connect(func(v: bool): _mudar("fps", v))
	add_child(fps)
	var auto := HBoxContainer.new()
	var la := Label.new()
	la.text = "Salvar sozinho a cada"
	la.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	auto.add_child(la)
	var op := OptionButton.new()
	for m in [1, 2, 5, 10]:
		op.add_item("%d min" % m, m)
	op.select([60, 120, 300, 600].find(int(Sessao.config.autosalvar_s)))
	op.item_selected.connect(func(i: int): _mudar("autosalvar_s", [60, 120, 300, 600][i]))
	auto.add_child(op)
	add_child(auto)
	var v := Button.new()
	v.text = "Voltar"
	v.custom_minimum_size = Vector2(0, 52)
	v.pressed.connect(func(): voltar.emit())
	add_child(v)


func _deslizante(rotulo: String, chave: String, mn: float, mx: float, passo: float) -> void:
	var l := Label.new()
	add_child(l)
	var s := HSlider.new()
	s.min_value = mn
	s.max_value = mx
	s.step = passo
	s.value = float(Sessao.config[chave])
	s.custom_minimum_size = Vector2(320, 32)
	var texto := func(x: float) -> void: l.text = "%s: %d%%" % [rotulo, roundi(x * 100)]
	texto.call(s.value)
	s.value_changed.connect(func(x: float):
		texto.call(x)
		_mudar(chave, x))
	add_child(s)


func _mudar(chave: String, valor) -> void:
	Sessao.config[chave] = valor
	Sessao.salvar_config()
	Sessao.aplicar()
