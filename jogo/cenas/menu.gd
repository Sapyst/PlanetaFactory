extends Control
## Menu inicial: Continuar (se há partida salva), Novo jogo, Demonstração (fábrica pronta, construção livre),
## Configurações, Sair. Foto real do jogo de fundo. Com argumentos de teste (roteiro/camera/relatorio/modo)
## vai direto para o jogo — os testes automáticos não passam por aqui.

const JOGO := "res://cenas/mundo_demo.tscn"

var _caixa: VBoxContainer
var _config: PainelConfig


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.has("roteiro") or args.has("camera") or args.has("relatorio") or args.has("modo"):
		var m := args.find("modo")
		Sessao.modo = args[m + 1] if m >= 0 and args.size() > m + 1 else "demo"
		get_tree().change_scene_to_file.call_deferred(JOGO)
		return
	theme = Tema.criar()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var fundo := TextureRect.new()
	fundo.texture = load("res://assets/ui/fundo_menu.png")
	fundo.set_anchors_preset(Control.PRESET_FULL_RECT)
	fundo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	fundo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	fundo.modulate = Color(0.55, 0.55, 0.62)
	add_child(fundo)
	var centro := CenterContainer.new()
	centro.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(centro)
	var painel := PanelContainer.new()
	centro.add_child(painel)
	var m := MarginContainer.new()
	for lado in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + lado, 22)
	painel.add_child(m)
	var pilha := VBoxContainer.new()
	m.add_child(pilha)
	_caixa = VBoxContainer.new()
	_caixa.add_theme_constant_override("separation", 10)
	pilha.add_child(_caixa)
	_config = PainelConfig.new()
	_config.visible = false
	_config.voltar.connect(func(): _config.visible = false; _caixa.visible = true)
	pilha.add_child(_config)

	var titulo := Label.new()
	titulo.text = "PlanetaFactory"
	titulo.add_theme_font_size_override("font_size", 44)
	titulo.add_theme_color_override("font_color", BarraConstrucao.COR_DESTAQUE)
	titulo.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caixa.add_child(titulo)
	var sub := Label.new()
	sub.text = "A fábrica drena o planeta. O planeta reage."
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_color_override("font_color", Color(0.75, 0.77, 0.82))
	_caixa.add_child(sub)
	_caixa.add_child(HSeparator.new())
	if Salvamento.existe():
		var d := Salvamento.ler()
		_botao("Continuar" + ("  (%s)" % String(d.get("salvo_em", "")).replace("T", " ") if not d.is_empty() else ""), func(): _ir("continuar"))
	_botao("Novo jogo", func(): _ir("novo"))
	_botao("Demonstração (fábrica pronta, construção livre)", func(): _ir("demo"))
	_botao("Configurações", func(): _caixa.visible = false; _config.visible = true)
	if not OS.has_feature("web"):
		_botao("Sair", func(): get_tree().quit())


func _botao(texto: String, acao: Callable) -> void:
	var b := Button.new()
	b.text = texto
	b.custom_minimum_size = Vector2(420, 58)
	b.add_theme_font_size_override("font_size", 20)
	b.pressed.connect(acao)
	_caixa.add_child(b)


func _ir(modo: String) -> void:
	Sessao.modo = modo
	get_tree().change_scene_to_file(JOGO)
