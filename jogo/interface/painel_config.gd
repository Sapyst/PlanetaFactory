class_name PainelConfig
extends VBoxContainer
## Configurações (menu inicial e pausa): volumes, tamanho da interface (acessibilidade), sombras, autosalvar.
## Cada mudança aplica na hora e grava em user://configuracoes.cfg.

signal voltar

var _rolagem: ScrollContainer
var _corpo: VBoxContainer

const AUTOSALVAR := [0, 60, 120, 300, 600, 900, 1800]      ## segundos; 0 = desligado


func _ready() -> void:
	add_theme_constant_override("separation", Tema.n("menu_sep"))
	var t := Label.new()
	t.text = "Configurações"
	t.add_theme_font_size_override("font_size", Tema.n("f_config_titulo"))
	add_child(t)
	# as opções rolam quando a interface está grande e não cabem na tela; Voltar fica sempre à vista
	_rolagem = ScrollContainer.new()
	_rolagem.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(_rolagem)
	_corpo = VBoxContainer.new()
	_corpo.add_theme_constant_override("separation", Tema.n("menu_sep"))
	_corpo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_rolagem.add_child(_corpo)
	_rolagem.add_child(RolagemToque.new())
	_deslizante("Volume geral", "volume_geral", 0.0, 1.0, 0.05)
	_deslizante("Volume dos efeitos", "volume", 0.0, 1.0, 0.05)
	_deslizante("Volume do ambiente", "volume_ambiente", 0.0, 1.0, 0.05)
	_deslizante("Tamanho da interface", "texto", Sessao.TEXTO_MIN, Sessao.TEXTO_MAX, 0.04)
	_deslizante("Resolução do 3D (menos = mais leve)", "resolucao", 0.5, 1.0, 0.05)
	var sombra := CheckButton.new()
	sombra.text = "Sombras (desligar deixa mais leve no celular)"
	sombra.button_pressed = bool(Sessao.config.sombras)
	sombra.toggled.connect(func(v: bool): _mudar("sombras", v))
	_corpo.add_child(sombra)
	var fps := CheckButton.new()
	fps.text = "Mostrar FPS (quadros por segundo)"
	fps.button_pressed = bool(Sessao.config.fps)
	fps.toggled.connect(func(v: bool): _mudar("fps", v))
	_corpo.add_child(fps)
	var cl := CheckButton.new()
	cl.text = "Clima dinâmico (chuva, neblina, nuvens)"
	cl.button_pressed = bool(Sessao.config.get("clima", true))
	cl.toggled.connect(func(v: bool): _mudar("clima", v))
	_corpo.add_child(cl)
	var gr := CheckButton.new()
	gr.text = "Gramado denso (desligar deixa mais leve)"
	gr.button_pressed = bool(Sessao.config.get("grama", true))
	gr.toggled.connect(func(v: bool): _mudar("grama", v))
	_corpo.add_child(gr)
	var ori := HBoxContainer.new()
	var lo := Label.new()
	lo.text = "Estoque de recursos na tela"
	lo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ori.add_child(lo)
	var op_o := OptionButton.new()
	op_o.add_item("Vertical (coluna)")
	op_o.add_item("Horizontal (linha)")
	op_o.select(1 if str(Sessao.config.get("recursos_orientacao", "vertical")) == "horizontal" else 0)
	op_o.item_selected.connect(func(i: int): _mudar("recursos_orientacao", "horizontal" if i == 1 else "vertical"))
	ori.add_child(op_o)
	_corpo.add_child(ori)
	var auto := HBoxContainer.new()
	var la := Label.new()
	la.text = "Salvar sozinho a cada"
	la.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	auto.add_child(la)
	var op := OptionButton.new()
	for seg in AUTOSALVAR:
		op.add_item("desligado" if seg == 0 else "%d min" % (seg / 60))
	op.select(_indice_autosalvar(int(Sessao.config.autosalvar_s)))
	op.item_selected.connect(func(i: int): _mudar("autosalvar_s", AUTOSALVAR[i]))
	auto.add_child(op)
	_corpo.add_child(auto)
	var aa_box := HBoxContainer.new()
	var laa := Label.new()
	laa.text = "Antisserrilhado"
	laa.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	aa_box.add_child(laa)
	var op_aa := OptionButton.new()
	op_aa.add_item("Desligado")
	op_aa.add_item("Leve")
	op_aa.add_item("Alto")
	var aa_atual: String = str(Sessao.config.get("antialiasing", "leve"))
	var idx_aa := 1
	if aa_atual == "desligado":
		idx_aa = 0
	elif aa_atual == "alto":
		idx_aa = 2
	op_aa.select(idx_aa)
	op_aa.item_selected.connect(func(i: int):
		var val := "leve"
		if i == 0:
			val = "desligado"
		elif i == 2:
			val = "alto"
		_mudar("antialiasing", val))
	aa_box.add_child(op_aa)
	_corpo.add_child(aa_box)

	var v := Button.new()
	v.text = "Voltar"
	v.custom_minimum_size = Vector2(0, Tema.n("config_voltar"))
	v.pressed.connect(func(): voltar.emit())
	add_child(v)
	var vp := get_viewport()
	if vp != null:
		vp.size_changed.connect(_ajustar_rolagem)
	visibility_changed.connect(_ajustar_rolagem)
	_ajustar_rolagem.call_deferred()


## Altura da lista: o que ela precisa, até o que sobra na tela (título, Voltar e a moldura do painel ficam de fora).
func _ajustar_rolagem() -> void:
	if _corpo == null or _rolagem == null:
		return
	var vp := get_viewport()
	var alt_disp := vp.get_visible_rect().size.y if vp != null else 720.0
	var tam := _corpo.get_combined_minimum_size()
	_rolagem.custom_minimum_size = Vector2(tam.x + 12.0, minf(tam.y, alt_disp - Tema.f("config_folga")))



## Opção da lista para o valor salvo (um valor fora dela mostra a mais próxima, sem mudar nada até a pessoa escolher).
static func _indice_autosalvar(seg: int) -> int:
	var melhor := 0
	for i in AUTOSALVAR.size():
		if absi(AUTOSALVAR[i] - seg) < absi(AUTOSALVAR[melhor] - seg):
			melhor = i
	return melhor


func _deslizante(rotulo: String, chave: String, mn: float, mx: float, passo: float) -> void:
	var l := Label.new()
	_corpo.add_child(l)
	var s := HSlider.new()
	s.scrollable = false                 # a roda rola a lista, não muda o valor por acidente
	s.min_value = mn
	s.max_value = mx
	s.step = passo
	s.value = float(Sessao.config.get(chave, 1.0 if chave == "volume_geral" else 0.8))
	s.custom_minimum_size = Tema.v("config_slider")
	var texto := func(x: float) -> void: l.text = "%s: %d%%" % [rotulo, roundi(x * 100)]
	texto.call(s.value)
	s.value_changed.connect(func(x: float):
		texto.call(x)
		_mudar(chave, x))
	_corpo.add_child(s)


func _mudar(chave: String, valor) -> void:
	Sessao.config[chave] = valor
	Sessao.salvar_config()
	Sessao.aplicar()
