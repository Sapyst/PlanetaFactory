class_name BarraConstrucao
extends CanvasLayer
## Interface de construção, toda montada por código; medidas por perfil em Tema.MEDIDAS (celular: botões grandes; PC: refinado):
##   embaixo — abas de categoria + peças da categoria (ícone renderizado da arte + nome);
##   à direita — Girar, Remover, Desfazer, Cancelar;
##   em cima — dica: o que está na mão e por que o fantasma ficou vermelho.
## Não sabe de regra: só emite sinais. Categorias e textos vêm de dados/menu_construcao.json.

signal peca_escolhida(nome: String)
signal acao_pendente(acao: String)    ## "girar", "mover", "construir", "cancelar_peca"
signal ferramenta(nome: String)       ## "girar", "remover", "desfazer", "cancelar", "recursos", "poluicao", "pesquisa", "menu"

const COR_FUNDO := Color(0.09, 0.10, 0.13, 0.92)
const COR_BORDA := Color(0.28, 0.30, 0.36)
const COR_DESTAQUE := Color(0.96, 0.74, 0.24)
const COR_PERIGO := Color(0.95, 0.35, 0.30)
const COR_TITULO := Tema.COR.titulo     ## (era ciano) títulos e cabeçalhos

var toque := false                     ## sem atalhos de teclado nos textos
var liberado: Callable                 ## nome da peça → bool (pesquisa); vazio = tudo liberado
var em_desenvolvimento: Callable       ## nome da peça → bool (Pesquisa.peca_em_desenvolvimento); vazio = nenhuma
var _tema: Theme
var _abas: VBoxContainer
var _pecas: VBoxContainer
var _ferr: HBoxContainer
var _painel_pecas: PanelContainer
var _titulo_cat: Label
var _acoes: PanelContainer
var _botoes_acao: Dictionary = {}
var _det_rolagem: ScrollContainer
var _dica_painel: PanelContainer
var _dica: Label
var _paineis: Array[Control] = []
var _canto: Control
var _seg := {}                         ## margens da área segura
var _botoes_peca: Dictionary = {}      ## nome → Button
var _botoes_ferr: Dictionary = {}
var _info: Label
var _alerta: Label
var _detalhe: PanelContainer
var _det_titulo: Label
var _det_texto: Label
var _det_botoes: VBoxContainer
var _det_assinatura := ""
var _recursos: PainelRecursos
var _salvando: Label
var _raiz: Control
signal fechar_detalhe_pedido
var _cat := 0
var _selecionada := ""
var _removendo := false


## Área segura do aparelho (barra de status/câmera e barra de gestos): margens em pixels de tela.
func _seguro() -> Dictionary:
	var m := {"left": Tema.n("seg_x"), "right": Tema.n("seg_x"), "top": Tema.n("seg_y"), "bottom": Tema.n("seg_y")}
	var tela := DisplayServer.screen_get_size()
	var seg := DisplayServer.get_display_safe_area()
	if OS.has_feature("mobile") and seg.size.x > 0 and tela.x > 0:
		var esc := get_viewport().get_visible_rect().size.x / float(tela.x)
		m.left = maxi(12, int(seg.position.x * esc) + 8)
		m.top = maxi(10, int(seg.position.y * esc) + 6)
		m.right = maxi(12, int((tela.x - seg.end.x) * esc) + 8)
		m.bottom = maxi(10, int((tela.y - seg.end.y) * esc) + 8)
	return m


func _ready() -> void:
	layer = 10
	toque = DisplayServer.is_touchscreen_available()
	_tema = Tema.criar()
	var raiz := Control.new()
	raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.theme = _tema
	add_child(raiz)
	# layout B: estado em chips (cima, esquerda) · ferramentas (cima, direita) · coluna de categorias (direita,
	# ao alcance do polegar) · painel deslizante com as peças explicadas · dica embaixo. Tudo dentro da área segura.
	var margem := MarginContainer.new()
	margem.set_anchors_preset(Control.PRESET_FULL_RECT)
	var seg := _seguro()
	_seg = seg
	for lado in seg:
		margem.add_theme_constant_override("margin_" + lado, seg[lado])
	margem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.add_child(margem)
	var linha := HBoxContainer.new()
	linha.mouse_filter = Control.MOUSE_FILTER_IGNORE
	linha.add_theme_constant_override("separation", Tema.n("sep"))
	margem.add_child(linha)
	# esquerda: chips de estado + painel de detalhe; dica embaixo
	var esq := VBoxContainer.new()
	esq.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	esq.mouse_filter = Control.MOUSE_FILTER_IGNORE
	linha.add_child(esq)
	var canto := MarginContainer.new()
	_canto = canto
	canto.mouse_filter = Control.MOUSE_FILTER_IGNORE
	esq.add_child(canto)
	var info_vb := VBoxContainer.new()
	info_vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canto.add_child(info_vb)
	var chips := PanelContainer.new()
	chips.mouse_filter = Control.MOUSE_FILTER_STOP     # tocar no status abre/fecha os detalhes
	if Tema.estilo("atalhos"):
		chips.tooltip_text = "Clique para abrir ou fechar os detalhes"
	chips.gui_input.connect(func(e: InputEvent):
		if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT and not e.pressed:
			_status_aberto = not _status_aberto
			_mostrar_status())
	_paineis.append(chips)
	# raio pequeno: o texto tem várias linhas, um canto em pílula cortaria as pontas das linhas
	var caixa_info := Tema.caixa(Color(0.04, 0.045, 0.05, 0.78), Color(Tema.COR.filete, 0.6), Tema.n("info_raio"), Tema.n("info_cont"))
	caixa_info.content_margin_top = Tema.n("info_cont")
	caixa_info.content_margin_bottom = Tema.n("info_cont")
	caixa_info.content_margin_left = Tema.n("info_esq")
	caixa_info.content_margin_right = Tema.n("info_dir")
	chips.add_theme_stylebox_override("panel", caixa_info)
	chips.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	info_vb.add_child(chips)
	_info = Label.new()
	_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_info.add_theme_font_size_override("font_size", Tema.n("f_texto"))
	_info.add_theme_color_override("font_color", Tema.cor("info"))
	chips.add_child(_info)
	_alerta = Label.new()
	_alerta.add_theme_color_override("font_color", COR_PERIGO.lightened(0.2))
	_alerta.visible = false
	info_vb.add_child(_alerta)
	_detalhe = PanelContainer.new()
	_detalhe.visible = false
	_detalhe.custom_minimum_size = Vector2(Tema.f("det_inicial"), 0)
	_detalhe.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	raiz.add_child(_detalhe)                       # gaveta: posição e altura por _posicionar_detalhe (cabe na tela)
	_paineis.append(_detalhe)
	var dv := VBoxContainer.new()
	dv.add_theme_constant_override("separation", Tema.n("det_sep"))
	_detalhe.add_child(dv)
	var topo_det := HBoxContainer.new()
	dv.add_child(topo_det)
	_det_titulo = Label.new()
	_det_titulo.add_theme_color_override("font_color", COR_TITULO)
	_det_titulo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if Tema.estilo("painel_compacto"):              # cabeçalho: ícone, nome, vida, estado com a causa
		topo_det.add_theme_constant_override("separation", Tema.n("sep"))
		_det_icone = TextureRect.new()
		_det_icone.custom_minimum_size = Vector2(Tema.f("maq_icone"), Tema.f("maq_icone"))
		_det_icone.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_det_icone.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		topo_det.add_child(_det_icone)
		var cab_v := VBoxContainer.new()
		cab_v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		cab_v.add_theme_constant_override("separation", 1)
		topo_det.add_child(cab_v)
		_det_titulo.add_theme_font_size_override("font_size", Tema.n("f_titulo"))
		_det_titulo.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		cab_v.add_child(_det_titulo)
		_det_estado = Label.new()
		_det_estado.add_theme_font_size_override("font_size", Tema.n("f_peq"))
		_det_estado.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		cab_v.add_child(_det_estado)
		_det_vida = ProgressBar.new()
		_det_vida.max_value = 1.0
		_det_vida.show_percentage = false
		_det_vida.custom_minimum_size = Vector2(0, 4)
		_det_vida.mouse_filter = Control.MOUSE_FILTER_PASS
		cab_v.add_child(_det_vida)
	else:
		topo_det.add_child(_det_titulo)
	var fechar := Button.new()
	fechar.text = "✕"
	fechar.focus_mode = Control.FOCUS_NONE
	fechar.custom_minimum_size = Tema.v("det_fechar")
	if Tema.estilo("atalhos"):
		fechar.tooltip_text = "Fechar (clique direito no mapa não fecha: use aqui)"
	fechar.pressed.connect(func(): fechar_detalhe_pedido.emit())
	topo_det.add_child(fechar)
	dv.add_child(Tema.faixa_titulo())
	if Tema.estilo("painel_compacto"):              # ações comuns, sempre à vista (fora da rolagem)
		_det_acoes = HFlowContainer.new()
		_det_acoes.add_theme_constant_override("h_separation", 2)
		_det_acoes.add_theme_constant_override("v_separation", 2)
		dv.add_child(_det_acoes)
	var rolagem := ScrollContainer.new()
	rolagem.custom_minimum_size = Vector2(0, 0)
	rolagem.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	rolagem.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var corpo := VBoxContainer.new()
	corpo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if Tema.estilo("painel_compacto"):
		_det_barras = VBoxContainer.new()
		_det_barras.add_theme_constant_override("separation", 2)
		corpo.add_child(_det_barras)
	_det_maquina = VBoxContainer.new()                # máquina: ícone, receita em casas, barras (detalhe_maquina)
	_det_maquina.add_theme_constant_override("separation", Tema.n("det_sep"))
	_det_maquina.visible = false
	corpo.add_child(_det_maquina)
	_det_texto = Label.new()
	_det_texto.add_theme_font_size_override("font_size", Tema.n("f_texto"))
	_det_texto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_det_texto.custom_minimum_size = Vector2(Tema.f("det_texto"), 0)
	corpo.add_child(_det_texto)
	_det_botoes = VBoxContainer.new()
	_det_botoes.add_theme_constant_override("separation", Tema.n("det_botoes_sep"))
	corpo.add_child(_det_botoes)
	rolagem.add_child(corpo)
	rolagem.add_child(RolagemToque.new())          # arrastar em cima dos botões rola a lista (celular)
	rolagem.custom_minimum_size = Vector2(0, 0)
	_det_rolagem = rolagem
	dv.add_child(rolagem)
	var vazio := Control.new()
	vazio.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vazio.mouse_filter = Control.MOUSE_FILTER_IGNORE
	esq.add_child(vazio)
	var topo := CenterContainer.new()
	topo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	esq.add_child(topo)
	_dica_painel = PanelContainer.new()
	_dica_painel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	topo.add_child(_dica_painel)
	_dica = Label.new()
	_dica.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_dica.add_theme_font_size_override("font_size", Tema.n("f_texto"))
	_dica.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_dica.custom_minimum_size = Vector2(Tema.f("dica_max"), 0)
	_dica_painel.add_child(_dica)
	_dica_painel.visible = false
	# meio-direita: ferramentas em cima + painel de peças
	var dir := VBoxContainer.new()
	dir.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dir.add_theme_constant_override("separation", Tema.n("sep"))
	linha.add_child(dir)
	var ferr_painel := PanelContainer.new()
	ferr_painel.size_flags_horizontal = Control.SIZE_SHRINK_END
	dir.add_child(ferr_painel)
	_paineis.append(ferr_painel)
	_ferr = HFlowContainer.new() if false else HBoxContainer.new()
	_ferr.add_theme_constant_override("separation", Tema.n("ferr_sep"))
	ferr_painel.add_child(_ferr)
	for f in [["nivel", "⇡ chão"], ["remover", "✕ Remover"], ["aplainar", "▭ Aplainar"], ["escavar", "⌄ Escavar"], ["desfazer", "↶"],
			["recursos", "◈ Recursos"], ["poluicao", "☁"], ["pesquisa", "⚗"], ["menu", "☰"]]:
		var b := Button.new()
		var dica_f: Array = FERRAMENTAS[f[0]]
		b.text = Tema.com_atalho(f[1], dica_f[1])
		b.tooltip_text = "%s (%s)" % dica_f if Tema.estilo("atalhos") else "%s (%s)" % [f[0].capitalize(), dica_f[1]]
		b.custom_minimum_size = Tema.v("ferr_botao")
		b.add_theme_font_size_override("font_size", Tema.n("f_ferr"))
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(func(): Som.tocar("clique"); ferramenta.emit(f[0]))
		_ferr.add_child(b)
		_botoes_ferr[f[0]] = b
	# girar/cancelar: escondidos na coluna (a peça pendente tem a barra de ações própria); continuam no teclado
	for f in [["girar", "⟲"], ["cancelar", "✕"]]:
		var b := Button.new()
		b.text = f[1]
		b.visible = false
		b.pressed.connect(func(): ferramenta.emit(f[0]))
		_ferr.add_child(b)
		_botoes_ferr[f[0]] = b
	_painel_pecas = PanelContainer.new()
	_painel_pecas.custom_minimum_size = Vector2(Tema.f("pecas_max"), 0)
	_painel_pecas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_painel_pecas.size_flags_horizontal = Control.SIZE_SHRINK_END
	_painel_pecas.visible = false
	dir.add_child(_painel_pecas)
	_paineis.append(_painel_pecas)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", Tema.n("sep"))
	_painel_pecas.add_child(pv)
	_titulo_cat = Label.new()
	_titulo_cat.add_theme_font_size_override("font_size", Tema.n("f_titulo"))
	_titulo_cat.add_theme_color_override("font_color", COR_TITULO)
	pv.add_child(_titulo_cat)
	var rol := ScrollContainer.new()
	rol.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rol.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pv.add_child(rol)
	_pecas = VBoxContainer.new()
	_pecas.add_theme_constant_override("separation", Tema.n("peca_sep"))
	_pecas.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rol.add_child(_pecas)
	rol.add_child(RolagemToque.new())
	# coluna de categorias (polegar direito)
	var col := PanelContainer.new()
	linha.add_child(col)
	_paineis.append(col)
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", Tema.n("cat_sep"))
	cv.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_child(cv)
	_abas = cv
	var cats: Array = Registro.menu.get("categorias", [])
	var icc: Dictionary = Registro.menu.get("icones_categoria", {})
	for i in cats.size():
		var b := Button.new()
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(Tema.f("cat_larg"), Tema.f("cat_alt_max"))
		b.focus_mode = Control.FOCUS_NONE
		b.icon = _icone(icc.get(cats[i].nome, cats[i].pecas[0]))
		b.expand_icon = true
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.tooltip_text = cats[i].nome + (" (Tab: próxima aba)" if Tema.estilo("atalhos") else "")
		var cc := Tema.cor_categoria(cats[i].nome)       # cada categoria com a sua cor (ícone branco tingido)
		b.add_theme_color_override("icon_normal_color", cc.darkened(0.08))
		b.add_theme_color_override("icon_hover_color", cc.lightened(0.15))
		b.add_theme_color_override("icon_pressed_color", cc.lightened(0.25))
		b.add_theme_color_override("icon_hover_pressed_color", cc.lightened(0.25))
		b.pressed.connect(func(): Som.tocar("clique"); _tocar_categoria(i))
		cv.add_child(b)
	# barra de ações da peça pendente (segue o fantasma): Girar · Mover · Construir · ✕
	_acoes = PanelContainer.new()
	_acoes.visible = false
	raiz.add_child(_acoes)
	_paineis.append(_acoes)
	var ah := HBoxContainer.new()
	ah.add_theme_constant_override("separation", Tema.n("acao_sep"))
	_acoes.add_child(ah)
	for a in [["girar", "⟲ Girar", Color(0, 0, 0, 0), "R"], ["mover", "✥ Mover", Color(0, 0, 0, 0), ""],
			["construir", "✓ Construir", Color(0.12, 0.56, 0.35), "Enter"], ["cancelar_peca", "✕", Color(0.56, 0.17, 0.17), "Esc"]]:
		var b := Button.new()
		b.text = Tema.com_atalho(a[1], a[3])
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Tema.v("acao_x") if a[0] == "cancelar_peca" else Tema.v("acao_botao")
		b.add_theme_font_size_override("font_size", Tema.n("f_ferr") if Tema.estilo("fino") else Tema.n("f_base"))
		if a[2].a > 0.0:
			b.add_theme_stylebox_override("normal", Tema.caixa(a[2], a[2].lightened(0.4), 10, 6))
			b.add_theme_stylebox_override("hover", Tema.caixa(a[2].lightened(0.1), a[2].lightened(0.5), 10, 6))
		b.pressed.connect(func(): Som.tocar("clique"); acao_pendente.emit(a[0]))
		ah.add_child(b)
		_botoes_acao[a[0]] = b
	marcar("", false)
	_criar_faixa(raiz)
	_recursos = PainelRecursos.new()
	_recursos.horizontal = str(Sessao.config.get("recursos_orientacao", "vertical")) == "horizontal"
	_recursos.resumo = bool(Sessao.config.get("recursos_resumo", false))
	_recursos.mudou_resumo = func(v: bool): Sessao.config["recursos_resumo"] = v; Sessao.salvar_config()
	raiz.add_child(_recursos)
	_paineis.append(_recursos)
	_raiz = raiz
	get_viewport().size_changed.connect(_ajustar_tamanhos)
	_ajustar_tamanhos()


## Faixa do modo construção: no alto, entre o status e as categorias, diz o que a mão está fazendo e tem um Sair
## grande (antes só as setas das esteiras mostravam que o jogo ainda estava construindo).
var _faixa: PanelContainer
var _faixa_texto: Label


func _criar_faixa(raiz: Control) -> void:
	_faixa = PanelContainer.new()
	_faixa.add_theme_stylebox_override("panel", Tema.perigo_estilo())
	_faixa.visible = false
	raiz.add_child(_faixa)
	_paineis.append(_faixa)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", Tema.n("faixa_sep"))
	_faixa.add_child(h)
	_faixa_texto = Label.new()
	_faixa_texto.add_theme_font_size_override("font_size", Tema.n("f_faixa"))
	_faixa_texto.add_theme_color_override("font_color", Color(1.0, 0.92, 0.7))
	_faixa_texto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_faixa_texto.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_faixa_texto.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	h.add_child(_faixa_texto)
	var sair := Button.new()
	sair.text = Tema.com_atalho("✕  Sair", "Esc")
	sair.custom_minimum_size = Tema.v("sair_botao")
	sair.focus_mode = Control.FOCUS_NONE
	sair.pressed.connect(func(): Som.tocar("clique"); ferramenta.emit("sair"))
	for est in ["normal", "hover"]:
		sair.add_theme_stylebox_override(est, Tema.botao_perigo_estilo())
	sair.add_theme_stylebox_override("pressed", Tema.botao_perigo_estilo(true))
	sair.add_theme_color_override("font_color", Color.WHITE)
	sair.add_theme_color_override("font_hover_color", Color.WHITE)
	sair.add_theme_color_override("font_outline_color", Color.BLACK)
	sair.add_theme_constant_override("outline_size", 8 if not Tema.estilo("fino") else 4)
	sair.add_theme_font_size_override("font_size", Tema.n("f_sair"))
	h.add_child(sair)


## Texto vazio = fora do modo construção (some).
func modo_construcao(texto: String) -> void:
	_faixa.visible = texto != ""
	if not _faixa.visible:
		_faixa_no_ar = false
	elif _faixa_texto.text != texto:
		_faixa_texto.text = texto


## A faixa nunca cobre o que está aberto: procura, nos retângulos reais dos painéis, o vão livre mais à direita (onde ela
## mora) e desliza até lá em animação curta quando a lista ou a gaveta abre. Sem vão na altura dela, desce até achar.
func _posicionar_faixa(delta := -1.0) -> void:
	var tela := get_viewport().get_visible_rect().size
	var topo := (_ferr.get_parent() as Control).get_global_rect().end.y + 8.0
	_faixa_texto.custom_minimum_size.x = 0.0
	var fora_texto := _faixa.get_combined_minimum_size().x        # moldura + botão: medidos, não supostos
	_faixa_texto.custom_minimum_size.x = maxf(Tema.f("faixa_min") - fora_texto, 40.0)
	var alt := _faixa.get_combined_minimum_size().y
	var obst: Array[Rect2] = []
	for c in [_info.get_parent(), _alerta, _recursos, _detalhe, _painel_pecas, _abas.get_parent(), _ferr.get_parent(), _dica_painel]:
		if c != null and (c as Control).is_visible_in_tree():
			obst.append((c as Control).get_global_rect())
	var lugar := BarraConstrucao.lugar_faixa(tela, alt, topo, obst, Tema.f("faixa_min"), Tema.f("faixa_max"))
	_faixa_texto.custom_minimum_size.x = maxf(lugar.size.x - fora_texto, 40.0)
	var tam := _faixa.get_combined_minimum_size()
	if tam.y > alt + 0.5:                                # o texto quebrou numa largura menor: a altura mudou, confere de novo
		lugar = BarraConstrucao.lugar_faixa(tela, tam.y, topo, obst, Tema.f("faixa_min"), Tema.f("faixa_max"))
	_faixa.size = tam
	_faixa_alvo = lugar.position
	if delta < 0.0 or not _faixa_no_ar:
		_faixa.position = _faixa_alvo                    # acabou de aparecer: já no lugar, sem vir voando
		_faixa_no_ar = true
	else:
		_faixa.position = _faixa.position.lerp(_faixa_alvo, 1.0 - exp(-14.0 * delta))
		if _faixa.position.distance_squared_to(_faixa_alvo) < 0.25:
			_faixa.position = _faixa_alvo


var _faixa_alvo := Vector2.ZERO
var _faixa_no_ar := false


## Onde a faixa cabe. Varre a altura a partir de `topo`: em cada altura, os vãos horizontais que nenhum obstáculo toca; fica com o
## mais à direita que tenha pelo menos `larg_min`, encostada à direita dele. Pura para o teste.
static func lugar_faixa(tela: Vector2, alt: float, topo: float, obstaculos: Array[Rect2], larg_min: float, larg_max: float, folga := 8.0) -> Rect2:
	var y := topo
	while y + alt <= tela.y:
		var cortes: Array[Vector2] = []
		for r in obstaculos:
			if r.position.y < y + alt + folga and r.end.y > y - folga:
				cortes.append(Vector2(r.position.x - folga, r.end.x + folga))
		cortes.sort_custom(func(a, b): return a.x > b.x)
		var dir := tela.x - folga
		var achou := false
		var proximo_y := INF
		for c in cortes:
			if c.y >= dir:                               # está à direita do que já foi visto (ou encosta): só encolhe o limite
				dir = minf(dir, c.x)
				continue
			if dir - c.y >= larg_min:
				achou = true
				return Rect2(Vector2(dir - minf(dir - c.y, larg_max), y), Vector2(minf(dir - c.y, larg_max), alt))
			dir = minf(dir, c.x)
		if not achou and dir - folga >= larg_min:         # último vão: da margem esquerda até o obstáculo mais à esquerda
			return Rect2(Vector2(dir - minf(dir - folga, larg_max), y), Vector2(minf(dir - folga, larg_max), alt))
		for r in obstaculos:                              # nada nesta altura: desce até o obstáculo mais baixo que tocava acabar
			if r.position.y < y + alt + folga and r.end.y > y - folga:
				proximo_y = minf(proximo_y, r.end.y + folga)
		if proximo_y == INF or proximo_y <= y:
			break
		y = proximo_y
	return Rect2(Vector2(folga, topo), Vector2(larg_min, alt))    # tela pequena demais: canto, mas nunca fora dela


const ENCOLHEM := ["remover", "aplainar", "escavar", "recursos"]   ## em tela estreita ficam só com o ícone
## nome → [o que é, atalho]: dica do mouse e atalho à vista no PC.
const FERRAMENTAS := {"nivel": ["Nível da esteira", "N"], "remover": ["Remover", "X"], "aplainar": ["Aplainar o chão", "L"], "escavar": ["Escavar", "K"], "desfazer": ["Desfazer", "Ctrl+Z"],
		"recursos": ["Visão de recursos", "V"], "poluicao": ["Nuvem de poluição", "P"], "pesquisa": ["Pesquisa", "T"], "menu": ["Menu", "Esc"]}


## Painel de detalhe como gaveta: da borda de baixo do status até a borda de baixo da tela (área segura), largura
## pela tela. A lista rola dentro dela — nunca passa da tela (antes crescia para baixo e o fim ficava inalcançável).
func _process(d: float) -> void:
	if _detalhe != null and _detalhe.visible:
		_posicionar_detalhe()
	if _faixa != null and _faixa.visible:
		_posicionar_faixa(d)
	if _recursos != null and _recursos.visible:
		_posicionar_recursos()


## Estoque do núcleo: canto esquerdo, logo abaixo do status. Em coluna ou em linha, conforme a configuração; com a
## gaveta de detalhe aberta, vai para o lado dela.
func estoque(itens: Dictionary) -> void:
	_recursos.horizontal = str(Sessao.config.get("recursos_orientacao", "vertical")) == "horizontal"
	_recursos.atualizar(itens)
	_posicionar_recursos()


func _posicionar_recursos() -> void:
	var tela := get_viewport().get_visible_rect().size
	var pos := Vector2(float(_seg.get("left", 12)), _canto.get_global_rect().end.y + 6.0)
	if _detalhe.visible:
		pos.x = _detalhe.get_global_rect().end.x + 6.0
	var baixo := tela.y - float(_seg.get("bottom", 10))
	if _dica_painel.visible:
		baixo = minf(baixo, _dica_painel.get_global_rect().position.y - 6.0)
	# à direita, o que estiver na altura dele: ferramentas, faixa do modo construção, peças e categorias
	var dir := (_abas.get_parent() as Control).get_global_rect().position.x
	for p in [_ferr.get_parent(), _painel_pecas]:       # (a faixa é quem desvia do estoque)
		var c := p as Control
		if c.visible and c.get_global_rect().end.y > pos.y:
			dir = minf(dir, c.get_global_rect().position.x)
	_recursos.organizar(dir - pos.x - 6.0 if _recursos.horizontal else baixo - pos.y)
	if _recursos.position != pos:
		_recursos.position = pos
	var tam := _recursos.get_combined_minimum_size()          # encolhe também (Control sozinho só cresce)
	if _recursos.size != tam:
		_recursos.size = tam


## Aviso discreto do salvar automático (não pega mouse nem empurra nada).
func indicador_salvando(sim: bool) -> void:
	if _salvando == null:
		_salvando = Label.new()
		_salvando.text = "Salvando…"
		_salvando.add_theme_font_size_override("font_size", Tema.n("f_salvando"))
		_salvando.add_theme_color_override("font_color", Tema.cor("titulo"))
		_salvando.add_theme_color_override("font_outline_color", Color.BLACK)
		_salvando.add_theme_constant_override("outline_size", 4)
		_salvando.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_raiz.add_child(_salvando)
	var status := (_info.get_parent() as Control).get_global_rect()
	_salvando.position = Vector2(status.end.x + 10.0, status.position.y + 6.0)   # ao lado do status
	_salvando.visible = sim


func _posicionar_detalhe() -> void:
	var tela := get_viewport().get_visible_rect().size
	var topo := _canto.get_global_rect().end.y + 8.0
	var baixo := tela.y - float(_seg.get("bottom", 10))
	var larg := clampf(tela.x * Tema.f("det_fator"), Tema.f("det_min"), Tema.f("det_max"))
	var pos := Vector2(float(_seg.get("left", 12)), topo)
	var tam := Vector2(larg, maxf(160.0, baixo - topo))
	if _detalhe.position != pos or _detalhe.size != tam:
		_detalhe.custom_minimum_size = tam
		_detalhe.position = pos
		_detalhe.size = tam
		_det_texto.custom_minimum_size.x = larg - Tema.f("det_folga")


## Troca o texto de uma ferramenta respeitando o modo estreito (só o ícone).
func texto_ferramenta(chave: String, texto: String) -> void:
	var b: Button = _botoes_ferr[chave]
	texto = Tema.com_atalho(texto, FERRAMENTAS.get(chave, ["", ""])[1])
	b.set_meta("texto_cheio", texto)
	b.text = _encolhido(texto) if get_viewport().get_visible_rect().size.x < Tema.f("largura_estreita") and chave in ENCOLHEM else texto


## Só o ícone (e o atalho, se o perfil mostra).
static func _encolhido(texto: String) -> String:
	var ic := texto.get_slice(" ", 0)
	return ic + " " + texto.substr(texto.rfind("[")) if Tema.estilo("atalhos") and texto.contains("[") else ic


## Tela estreita (celular 16:9, tablet, interface ampliada): ferramentas só com ícone e painéis mais estreitos, para
## nada passar da borda nem empurrar o resto. Refeito quando a tela muda de tamanho.
func _ajustar_tamanhos() -> void:
	var tela := get_viewport().get_visible_rect().size
	var estreita := tela.x < Tema.f("largura_estreita")
	for k in _botoes_ferr:
		var b: Button = _botoes_ferr[k]
		if not b.has_meta("texto_cheio"):
			b.set_meta("texto_cheio", b.text)
		var cheio: String = b.get_meta("texto_cheio")
		b.text = _encolhido(cheio) if estreita and k in ENCOLHEM else cheio
	_painel_pecas.custom_minimum_size.x = clampf(tela.x * Tema.f("pecas_fator"), Tema.f("pecas_min"), Tema.f("pecas_max"))
	_dica.custom_minimum_size.x = clampf(tela.x * Tema.f("dica_fator"), Tema.f("dica_min"), Tema.f("dica_max"))
	# status do canto: quebra as linhas longas em vez de alargar a coluna da esquerda
	_info.custom_minimum_size.x = clampf(tela.x * Tema.f("info_fator"), Tema.f("info_min"), Tema.f("info_max"))
	# categorias: a coluna inteira cabe na altura (8 botões de 66 passavam dos 533 de um celular e esticavam tudo)
	var n := _abas.get_child_count()
	var alt := clampf((tela.y - 44.0 - (n - 1) * Tema.f("cat_sep")) / maxf(n, 1), Tema.f("cat_alt_min"), Tema.f("cat_alt_max"))
	for b in _abas.get_children():
		(b as Control).custom_minimum_size = Vector2(Tema.f("cat_larg") if not estreita else Tema.f("cat_larg_estreita"), alt)


## Barra de ações da peça pendente: mostra em `pos` (tela, abaixo do fantasma) ou esconde (INF).
func acoes_em(pos: Vector2, pode: bool, movendo: bool) -> void:
	_acoes.visible = pos != Vector2.INF
	if not _acoes.visible:
		return
	var tam := _acoes.get_combined_minimum_size()
	var tela := get_viewport().get_visible_rect().size
	_acoes.position = Vector2(clampf(pos.x - tam.x / 2.0, 8.0, tela.x - tam.x - 8.0), clampf(pos.y + 24.0, 8.0, tela.y - tam.y - 40.0))
	_acoes.size = tam
	_botoes_acao["construir"].disabled = not pode
	_destacar(_botoes_acao["mover"], movendo, Tema.cor("agua"))


func _tocar_categoria(i: int) -> void:
	if _painel_pecas.visible and _cat == i:
		_painel_pecas.visible = false
		(_abas.get_child(i) as Button).button_pressed = false
		return
	_mostrar_categoria(i)
	_painel_pecas.visible = true
	for k in _abas.get_child_count():
		(_abas.get_child(k) as Button).button_pressed = k == i


func fechar_pecas() -> void:
	_painel_pecas.visible = false
	for k in _abas.get_child_count():
		(_abas.get_child(k) as Button).button_pressed = false


# ------------------------------------------------------------------ API
func rotulo(nome: String) -> String:
	return Registro.menu.get("rotulos", {}).get(nome, nome)


func texto_motivo(motivo: String) -> String:
	return Registro.menu.get("motivos", {}).get(motivo, motivo)


## Destaca a peça na mão (ou nenhuma) e o modo remover.
func marcar(nome: String, removendo: bool) -> void:
	_selecionada = nome
	_removendo = removendo
	for k in _botoes_peca:
		if not _botoes_peca[k].has_meta("em_desenvolvimento"):     # a placa cinza do selo fica
			_destacar(_botoes_peca[k], k == nome, COR_DESTAQUE)
	_destacar(_botoes_ferr["remover"], removendo, COR_PERIGO)
	_destacar(_botoes_ferr["aplainar"], nome == "#aplainar", COR_DESTAQUE)
	_destacar(_botoes_ferr["escavar"], nome == "#escavar", Color(0.35, 0.65, 0.95))
	var ativo := nome != "" or removendo
	_botoes_ferr["cancelar"].disabled = not ativo
	_botoes_ferr["girar"].disabled = nome == "" or nome.begins_with("#")


## Texto do botão de nível (chão / 0,5 m / 1,0 m).
func mostrar_nivel(n: int) -> void:
	var t: String = ["chão", "0,5 m", "1,0 m"][n]
	_botoes_ferr["nivel"].text = Tema.com_atalho("⇡ " + t, "N")
	_destacar(_botoes_ferr["nivel"], n > 0, Color(0.45, 0.75, 1.0))


func pode_desfazer(sim: bool) -> void:
	_botoes_ferr["desfazer"].disabled = not sim


## Texto do painel de situação; `alerta` vazio esconde a linha vermelha.
## Status do canto: fechado mostra só o essencial (hora/clima, núcleo, pesquisa) em poucas linhas; tocar abre tudo.
func situacao(texto: String, alerta := "") -> void:
	_status_texto = texto
	_mostrar_status()
	_alerta.text = alerta
	_alerta.visible = alerta != ""


var _status_aberto := false
var _status_texto := ""


func _mostrar_status() -> void:
	var linhas := _status_texto.split("\n")
	if _status_aberto or linhas.size() <= 2:
		_info.text = _status_texto + "   ▴"
		return
	var curtas: Array[String] = [linhas[0]]
	for l in linhas:
		if l.begins_with("Pesquisa:"):
			curtas.append(l)
	_info.text = "\n".join(curtas) + "   ▾"


## Mostra o painel de detalhe. botoes: [{texto, ligado (destaque), acao: Callable}]. Os botões só são refeitos
## quando mudam (o texto é atualizado sempre) — refazer a cada atualização engoliria cliques.
var _det_maquina: VBoxContainer
var _det_maq_assin := ""
var _det_icone: TextureRect          ## (daqui para baixo, só no painel compacto do PC)
var _det_estado: Label
var _det_vida: ProgressBar
var _det_acoes: HFlowContainer
var _det_barras: VBoxContainer
var _det_barras_assin := ""
var _det_numeros: Dictionary = {}    ## inventário: item → [rótulo da quantidade, botão]


## Parte de cima do painel numa máquina (como no painel de uma montadora): ícone grande da construção, a receita em
## casas — entradas (número = o que tem; borda vermelha = falta) → saída — e as barras de progresso e de energia.
## m vazio = some. m: {icone, entradas: [{tex, n, dica, falta}], saidas: [...], progresso 0..1, energia 0..1 ou -1}
func detalhe_maquina(m: Dictionary) -> void:
	_det_maquina.visible = not m.is_empty()
	if m.is_empty():
		_det_maq_assin = ""
		return
	var assin := str(m.get("entradas", [])) + str(m.get("saidas", [])) + str(m.get("icone"))
	if assin != _det_maq_assin:
		_det_maq_assin = assin
		for c in _det_maquina.get_children():
			c.queue_free()
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", Tema.n("sep") + 2)
		_det_maquina.add_child(h)
		if not Tema.estilo("painel_compacto"):     # no compacto o ícone está no cabeçalho
			var ic := TextureRect.new()
			ic.texture = m.get("icone")
			ic.custom_minimum_size = Vector2(Tema.f("maq_icone"), Tema.f("maq_icone"))
			ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			h.add_child(ic)
		var receita := HFlowContainer.new()
		receita.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		receita.add_theme_constant_override("h_separation", 4)
		receita.add_theme_constant_override("v_separation", 4)
		h.add_child(receita)
		for e in m.get("entradas", []):
			receita.add_child(Casa.nova(e.tex, str(e.n), e.dica, COR_PERIGO if e.get("falta", false) else Color(0.35, 0.4, 0.45)))
		if not m.get("saidas", []).is_empty():
			var seta := Label.new()
			seta.text = "→"
			seta.add_theme_font_size_override("font_size", Tema.n("f_seta"))
			seta.custom_minimum_size = Vector2(Tema.f("f_seta"), Casa.lado())
			seta.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			receita.add_child(seta)
		for e in m.get("saidas", []):
			receita.add_child(Casa.nova(e.tex, str(e.n), e.dica, Color(0.45, 0.85, 0.45)))
		for b in [] if Tema.estilo("painel_compacto") else [["progresso", Color(0.35, 0.85, 0.35)], ["energia", Color(0.95, 0.8, 0.2)]]:     # no compacto, barras com rótulo
			var pb := ProgressBar.new()
			pb.name = b[0]
			pb.max_value = 1.0
			pb.show_percentage = false
			pb.custom_minimum_size = Vector2(0, Tema.n("barra_alt"))
			var cheio := Tema.caixa(b[1], b[1].lightened(0.3), 3, 0)
			pb.add_theme_stylebox_override("fill", cheio)
			_det_maquina.add_child(pb)
	var pr := _det_maquina.get_node_or_null("progresso") as ProgressBar
	if pr != null:
		pr.value = float(m.get("progresso", 0.0))
	var en := _det_maquina.get_node_or_null("energia") as ProgressBar
	if en != null:
		en.visible = float(m.get("energia", -1.0)) >= 0.0
		en.value = float(m.get("energia", 0.0))


## extra (painel compacto do PC): {icone, estado, cor, vida 0..1 ou -1, vida_dica, barras: [{rotulo, valor, cor, dica?}], stats}. Vazio = sem cabeçalho (trem, pesquisa).
func detalhe(titulo: String, texto: String, botoes: Array, extra := {}) -> void:
	_detalhe.visible = true
	_det_titulo.text = titulo
	_det_texto.text = texto
	_det_texto.visible = texto != "" or not Tema.estilo("painel_compacto")
	if Tema.estilo("painel_compacto"):
		_cabecalho_detalhe(extra)
	var assin := titulo + "|" + "|".join(botoes.map(func(b): return "%s%s" % [b.get("texto", b.get("titulo", "")), b.get("ligado", false)]))
	if assin == _det_assinatura:
		for b in botoes:                         # só a quantidade mudou: atualiza sem refazer (refazer engoliria cliques)
			if b.has("numero") and _det_numeros.has(b.chave):
				_det_numeros[b.chave][0].text = b.numero
				_det_numeros[b.chave][1].tooltip_text = b.dica_num
		return
	_det_assinatura = assin
	_det_numeros.clear()
	for c in _det_botoes.get_children():
		c.queue_free()
	if _det_acoes != null:
		for c in _det_acoes.get_children():
			c.queue_free()
	var grade: HFlowContainer = null             # botões com "icone" seguidos ficam lado a lado
	var grupo_aberto := ""                       # (compacto) nome do grupo de botões em linha que está aberto
	var linha_grupo: HBoxContainer = null
	var compacto := Tema.estilo("painel_compacto")
	var titulo_receita := ""
	for b in botoes:
		if compacto and b.get("secao", "") == "acoes":
			_det_acoes.add_child(_botao_acao_detalhe(b))
			continue
		if compacto and b.has("grupo"):
			if b.grupo != grupo_aberto:
				grupo_aberto = b.grupo
				_det_botoes.add_child(_cabecalho_secao(b.grupo))
				linha_grupo = HBoxContainer.new()
				linha_grupo.add_theme_constant_override("separation", 2)
				_det_botoes.add_child(linha_grupo)
			linha_grupo.add_child(_botao_grupo(b))
			grade = null
			continue
		grupo_aberto = ""
		if b.has("titulo"):
			_det_botoes.add_child(_cabecalho_secao(b.titulo))
			grade = null
			continue
		if b.has("icone"):
			if grade == null:
				grade = HFlowContainer.new()
				grade.add_theme_constant_override("h_separation", 3)
				grade.add_theme_constant_override("v_separation", 3)
				_det_botoes.add_child(grade)
			grade.add_child(_botao_icone(b))
			continue
		grade = null
		if compacto and b.has("receita"):
			if b.get("grupo_receita", "") != titulo_receita:
				titulo_receita = b.grupo_receita
				_det_botoes.add_child(_cabecalho_secao(titulo_receita))
			_det_botoes.add_child(_botao_receita(b))
			continue
		var bt := Button.new()
		bt.text = b.texto
		bt.focus_mode = Control.FOCUS_NONE
		bt.custom_minimum_size = Vector2(0, Tema.n("det_botao"))
		bt.add_theme_font_size_override("font_size", Tema.n("f_texto") if Tema.estilo("fino") else Tema.n("f_base"))
		bt.alignment = HORIZONTAL_ALIGNMENT_LEFT
		bt.pressed.connect(RolagemToque.so_clique(b.acao))
		_det_botoes.add_child(bt)
		_destacar(bt, b.get("ligado", false), COR_DESTAQUE)


func _cabecalho_secao(texto: String) -> Label:
	var cab := Label.new()
	cab.text = texto
	cab.add_theme_font_size_override("font_size", Tema.n("f_peq"))
	cab.add_theme_color_override("font_color", COR_TITULO)
	return cab


func _cabecalho_detalhe(extra: Dictionary) -> void:
	_det_icone.visible = extra.get("icone") != null
	_det_icone.texture = extra.get("icone")
	_det_estado.visible = str(extra.get("estado", "")) != ""
	_det_estado.text = str(extra.get("estado", ""))
	_det_estado.add_theme_color_override("font_color", extra.get("cor", Tema.cor("info")))
	var vida := float(extra.get("vida", -1.0))
	_det_vida.visible = vida >= 0.0
	_det_vida.value = maxf(vida, 0.0)
	_det_vida.tooltip_text = str(extra.get("vida_dica", ""))
	if vida >= 0.0:
		var cv: Color = Tema.cor("sucesso") if vida > 0.5 else (Tema.cor("destaque") if vida > 0.25 else Tema.cor("perigo"))
		_det_vida.add_theme_stylebox_override("fill", _caixa_barra(cv))
	var barras: Array = extra.get("barras", [])
	var stats := str(extra.get("stats", ""))
	var assin := "|".join(barras.map(func(b): return str(b.rotulo))) + ("#" if stats != "" else "")
	if assin != _det_barras_assin:
		_det_barras_assin = assin
		for c in _det_barras.get_children():
			c.queue_free()
		for b in barras:
			var h := HBoxContainer.new()
			h.add_theme_constant_override("separation", 4)
			h.name = "b_" + str(b.rotulo).validate_node_name()
			var l := Label.new()
			l.text = str(b.rotulo)
			l.add_theme_font_size_override("font_size", Tema.n("f_alca"))
			l.add_theme_color_override("font_color", Tema.cor("info"))
			l.custom_minimum_size = Vector2(62, 0)
			l.clip_text = true
			h.add_child(l)
			var pb := ProgressBar.new()
			pb.max_value = 1.0
			pb.show_percentage = false
			pb.custom_minimum_size = Vector2(0, Tema.n("barra_alt"))
			pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			pb.add_theme_stylebox_override("fill", _caixa_barra(b.cor))
			pb.mouse_filter = Control.MOUSE_FILTER_PASS
			h.add_child(pb)
			var pc := Label.new()
			pc.add_theme_font_size_override("font_size", Tema.n("f_alca"))
			pc.custom_minimum_size = Vector2(30, 0)
			pc.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			h.add_child(pc)
			_det_barras.add_child(h)
		if stats != "":
			var ls := Label.new()
			ls.name = "stats"
			ls.add_theme_font_size_override("font_size", Tema.n("f_alca"))
			ls.add_theme_color_override("font_color", Tema.cor("info"))
			ls.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			_det_barras.add_child(ls)
	var i := 0
	for c in _det_barras.get_children():
		if c.is_queued_for_deletion():
			continue
		if c is Label:
			(c as Label).text = stats
		elif i < barras.size():
			var v := clampf(float(barras[i].valor), 0.0, 1.0)
			(c.get_child(1) as ProgressBar).value = v
			(c.get_child(1) as ProgressBar).tooltip_text = str(barras[i].get("dica", barras[i].rotulo))
			(c.get_child(2) as Label).text = "%d%%" % roundi(v * 100.0)
			i += 1


func _caixa_barra(c: Color) -> StyleBoxFlat:
	return Tema.caixa(c, c.lightened(0.3), 2, 0)


## Botão pequeno da linha de ações: rótulo curto, explicação e atalho na dica.
func _botao_acao_detalhe(b: Dictionary) -> Button:
	var bt := Button.new()
	bt.text = str(b.get("icone_txt", b.texto))
	var tecla := str(b.get("tecla", ""))
	bt.tooltip_text = "%s (%s)" % [str(b.texto).strip_edges(), tecla] if tecla != "" else str(b.texto)
	bt.focus_mode = Control.FOCUS_NONE
	bt.custom_minimum_size = Vector2(0, Tema.n("det_botao") - 2)
	bt.add_theme_font_size_override("font_size", Tema.n("f_peq"))
	bt.pressed.connect(RolagemToque.so_clique(b.acao))
	if b.get("perigo", false):
		bt.add_theme_color_override("font_color", COR_PERIGO.lightened(0.3))
	_destacar(bt, b.get("ligado", false), Tema.cor("sucesso"))
	return bt


## Uma opção de grupo (modo, limite...): segmento de largura igual; o texto completo vai na dica.
func _botao_grupo(b: Dictionary) -> Button:
	var bt := Button.new()
	bt.text = str(b.get("curto", b.texto))
	bt.tooltip_text = str(b.texto)
	bt.focus_mode = Control.FOCUS_NONE
	bt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bt.custom_minimum_size = Vector2(0, Tema.n("det_botao") - 2)
	bt.add_theme_font_size_override("font_size", Tema.n("f_peq"))
	bt.pressed.connect(RolagemToque.so_clique(b.acao))
	_destacar(bt, b.get("ligado", false), COR_DESTAQUE)
	return bt


## Receita como ela é: entradas → saídas em ícones com a quantidade, escolhida em âmbar; o texto inteiro fica na dica.
func _botao_receita(b: Dictionary) -> Button:
	var bt := Button.new()
	bt.focus_mode = Control.FOCUS_NONE
	bt.tooltip_text = str(b.texto)
	bt.custom_minimum_size = Vector2(0, 30)
	bt.pressed.connect(RolagemToque.so_clique(b.acao))
	_destacar(bt, b.get("ligado", false), COR_DESTAQUE)
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 6
	h.offset_right = -6
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_theme_constant_override("separation", 3)
	bt.add_child(h)
	var r: Dictionary = b.receita
	for e in r.entradas:
		_item_receita(h, e)
	var seta := Label.new()
	seta.text = "→"
	seta.mouse_filter = Control.MOUSE_FILTER_IGNORE
	seta.add_theme_font_size_override("font_size", Tema.n("f_texto"))
	seta.add_theme_color_override("font_color", Tema.cor("info"))
	h.add_child(seta)
	for e in r.saidas:
		_item_receita(h, e)
	return bt


func _item_receita(h: HBoxContainer, e: Dictionary) -> void:
	if e.tex != null:
		var ic := TextureRect.new()
		ic.texture = e.tex
		ic.custom_minimum_size = Vector2(20, 20)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(ic)
	var l := Label.new()
	l.text = str(e.n) if e.tex != null else "%d %s" % [e.n, e.get("fluido", e.dica)]
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_size_override("font_size", Tema.n("f_alca"))
	l.add_theme_color_override("font_color", Tema.cor("agua") if e.has("fluido") else Tema.cor("texto"))
	h.add_child(l)


## Casa de escolha em grade: só o ícone (o nome fica na dica); o escolhido ganha a moldura âmbar.
func _botao_icone(b: Dictionary) -> Button:
	var bt := Button.new()
	bt.icon = b.icone
	bt.expand_icon = true
	bt.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	bt.tooltip_text = b.texto
	bt.focus_mode = Control.FOCUS_NONE
	bt.custom_minimum_size = Vector2(Tema.f("det_icone_botao"), Tema.f("det_icone_botao"))
	bt.add_theme_constant_override("icon_max_width", Tema.n("det_icone_max"))
	bt.pressed.connect(RolagemToque.so_clique(b.acao))
	_destacar(bt, b.get("ligado", false), COR_DESTAQUE)
	if b.has("numero"):                            # casa de inventário: quantidade no canto
		bt.tooltip_text = b.dica_num
		var n := Label.new()
		n.text = b.numero
		n.set_anchors_preset(Control.PRESET_FULL_RECT)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		n.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		n.offset_right = -2
		n.add_theme_font_size_override("font_size", Tema.n("f_casa"))
		n.add_theme_color_override("font_outline_color", Color.BLACK)
		n.add_theme_constant_override("outline_size", 4)
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
		bt.add_child(n)
		_det_numeros[b.chave] = [n, bt]
	return bt


func fechar_detalhe() -> void:
	_detalhe.visible = false
	_det_assinatura = ""


func ligar_recursos(sim: bool, camada := "recursos") -> void:
	_destacar(_botoes_ferr["recursos"], sim, Tema.cor("agua"))
	texto_ferramenta("recursos", "◈ Vento" if sim and camada == "vento" else ("◈ Sujeira" if sim and camada == "poluicao" else "◈ Recursos"))


func ligar_poluicao(sim: bool) -> void:
	_destacar(_botoes_ferr["poluicao"], sim, Color(0.75, 0.45, 0.95))


func dica(texto: String, ruim := false) -> void:
	_dica_painel.visible = texto != ""
	_dica.text = texto
	_dica.add_theme_color_override("font_color", COR_PERIGO.lightened(0.25) if ruim else Color(0.93, 0.94, 0.96))


## Peças da categoria aberta (para os atalhos 1..9).
## Depois de uma pesquisa: refaz os botões (tira o cinza das peças liberadas).
func atualizar_bloqueios() -> void:
	_mostrar_categoria(_cat)


func pecas_da_categoria() -> Array:
	var cats: Array = Registro.menu.get("categorias", [])
	return cats[_cat].pecas if _cat < cats.size() else []


func proxima_categoria(passo := 1) -> void:
	_tocar_categoria(posmod(_cat + passo, _abas.get_child_count()))


## A posição de tela cai em cima da interface? (gestos ali não constroem nem mexem a câmera)
func sobre_interface(pos: Vector2) -> bool:
	for p in _paineis:
		if p.visible and p.get_global_rect().grow(4).has_point(pos):
			return true
	return false


## Retângulos de tela tomados pela interface (rótulos do mapa não ficam embaixo deles).
func areas_ocupadas() -> Array[Rect2]:
	var out: Array[Rect2] = []
	for p in _paineis + [_canto]:
		if p != null and p.is_visible_in_tree():
			out.append(p.get_global_rect())
	return out


## Centro de um botão na tela (peça, ferramenta ou "cat:<n>") — usado pelos roteiros de teste automático.
func centro_de(chave: String) -> Vector2:
	var b: Control = null
	if chave.begins_with("cat:"):
		b = _abas.get_child(int(chave.substr(4)))
	elif _botoes_acao.has(chave):
		b = _botoes_acao[chave]
	elif _botoes_peca.has(chave):
		b = _botoes_peca[chave]
	elif _botoes_ferr.has(chave):
		b = _botoes_ferr[chave]
	return b.get_global_rect().get_center() if b != null else Vector2(-1, -1)


# ------------------------------------------------------------------ montagem
func _mostrar_categoria(i: int) -> void:
	_cat = i
	for c in _pecas.get_children():
		c.queue_free()
	_botoes_peca.clear()
	var cats: Array = Registro.menu.get("categorias", [])
	_titulo_cat.text = cats[i].nome if i < cats.size() else ""
	var pecas := pecas_da_categoria()
	for k in pecas.size():
		var b := botao_peca(pecas[k], k)
		_pecas.add_child(b)
		_botoes_peca[pecas[k]] = b
	if _botoes_ferr.has("remover"):
		marcar(_selecionada, _removendo)


## A peça ainda não está no jogo (sem modelo, ou só uma pesquisa em desenvolvimento a libera)?
func peca_em_desenvolvimento(nome: String) -> bool:
	return em_desenvolvimento.is_valid() and bool(em_desenvolvimento.call(nome))


## Botão de uma peça da barra (ícone, nome, explicação, custo ou cadeado). Peça em desenvolvimento: placa cinza
## escuro com o selo, desligado (não escolhe).
func botao_peca(nome: String, k: int) -> Button:
	var icones: Dictionary = Registro.menu.get("icones", {})
	var expl: Dictionary = Registro.menu.get("explicacoes", {})
	var b := Button.new()
	b.custom_minimum_size = Vector2(0, Tema.n("peca_alt"))
	b.focus_mode = Control.FOCUS_NONE
	b.icon = _icone(icones.get(nome, nome))
	b.expand_icon = false
	b.add_theme_constant_override("icon_max_width", Tema.n("peca_icone"))
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	var custo := Construtor.custo_de(nome)
	var partes: Array[String] = []
	for it in custo:
		partes.append("%d %s" % [custo[it], Registro.itens.get(it, {}).get("nome", it).to_lower()])
	var f := ficha(nome)
	var extra := (" · " + f) if f != "" else ""
	var bloqueada: bool = liberado.is_valid() and not liberado.call(nome)
	var dev := peca_em_desenvolvimento(nome)
	var custo_txt: String = "" if dev else ("🔒 pesquisar" if bloqueada else ", ".join(partes))
	if Tema.estilo("peca_duas_linhas"):        # PC: denso; a explicação inteira fica na dica do mouse
		b.text = "%s  [%d]\n%s" % [rotulo(nome), k + 1, custo_txt]
		b.tooltip_text = "%s\n%s\n%s%s" % [rotulo(nome), expl.get(nome, ""), custo_txt, "" if bloqueada or dev else extra]
	else:
		b.text = "%s%s\n%s\n%s%s" % [rotulo(nome), "" if toque else "  (%d)" % (k + 1), expl.get(nome, ""), custo_txt, "" if bloqueada or dev else extra]
	b.add_theme_font_size_override("font_size", Tema.n("f_peq"))
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	if dev:                                    # ainda não está no jogo: cinza escuro, selo, não escolhe
		b.disabled = true
		b.set_meta("em_desenvolvimento", true)
		Tema.botao_desenvolvimento(b)
	else:
		b.pressed.connect(RolagemToque.so_clique(func(): Som.tocar("clique"); peca_escolhida.emit(nome); fechar_pecas()))
	if bloqueada and not dev:
		b.modulate = Color(0.6, 0.6, 0.65)
	return b


## Dados técnicos curtos da peça: consumo/geração de energia, armazenamento e integridade.
static func ficha(nome: String) -> String:
	var r: Dictionary = Registro.estruturas.get(nome, Registro.estruturas.get(nome + "_reta", {}))
	var p: Array[String] = []
	var kw := float(r.get("energia_kw", 0.0))
	if kw > 0.0:
		p.append("⚡ usa %d kW" % kw)
	elif kw < 0.0:
		p.append("⚡ gera %d kW" % -kw)
	if r.has("acumula_mj"):
		p.append("guarda %d MJ" % r.acumula_mj)
	if r.has("capacidade_itens"):
		p.append("%d itens" % r.capacidade_itens)
	if r.has("capacidade") and int(r.capacidade) > 100:
		p.append("%d de fluido" % r.capacidade)
	if r.has("vida"):
		p.append("♥ %d" % r.vida)
	return " · ".join(p)


## Ícone de peça (render do modelo, .png) ou de categoria (símbolo em vetor, "categorias/<nome>" → .svg).
func _icone(modelo: String) -> Texture2D:
	var c := "res://assets/icones/%s.%s" % [modelo, "svg" if modelo.begins_with("categorias/") else "png"]
	return load(c) if ResourceLoader.exists(c) else null


func _destacar(b: Button, sim: bool, cor: Color) -> void:
	if sim:
		var s := Tema.botao_cor_estilo(cor)            # placa em relevo com moldura na cor da situação
		b.add_theme_stylebox_override("normal", s)
		b.add_theme_stylebox_override("hover", s)
	else:
		b.remove_theme_stylebox_override("normal")
		b.remove_theme_stylebox_override("hover")
