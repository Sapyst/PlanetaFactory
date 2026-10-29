class_name BarraConstrucao
extends CanvasLayer
## Interface de construção, toda montada por código (PC e toque, botões grandes):
##   embaixo — abas de categoria + peças da categoria (ícone renderizado da arte + nome);
##   à direita — Girar, Remover, Desfazer, Cancelar;
##   em cima — dica: o que está na mão e por que o fantasma ficou vermelho.
## Não sabe de regra: só emite sinais. Categorias e textos vêm de dados/menu_construcao.json.

signal peca_escolhida(nome: String)
signal acao_pendente(acao: String)    ## "girar", "mover", "construir", "cancelar_peca"
signal ferramenta(nome: String)       ## "girar", "remover", "desfazer", "cancelar", "recursos", "poluicao", "pesquisa", "menu"

const TAM_PECA := Vector2(116, 112)
const COR_FUNDO := Color(0.09, 0.10, 0.13, 0.92)
const COR_BORDA := Color(0.28, 0.30, 0.36)
const COR_DESTAQUE := Color(0.96, 0.74, 0.24)
const COR_PERIGO := Color(0.95, 0.35, 0.30)
const COR_CIANO := Color(0.31, 0.9, 0.87)

var toque := false                     ## sem atalhos de teclado nos textos
var liberado: Callable                 ## nome da peça → bool (pesquisa); vazio = tudo liberado
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
var _botoes_peca: Dictionary = {}      ## nome → Button
var _botoes_ferr: Dictionary = {}
var _info: Label
var _alerta: Label
var _detalhe: PanelContainer
var _det_titulo: Label
var _det_texto: Label
var _det_botoes: VBoxContainer
var _det_assinatura := ""
signal fechar_detalhe_pedido
var _cat := 0
var _selecionada := ""
var _removendo := false


## Área segura do aparelho (barra de status/câmera e barra de gestos): margens em pixels de tela.
func _seguro() -> Dictionary:
	var m := {"left": 12, "right": 12, "top": 10, "bottom": 10}
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
	for lado in seg:
		margem.add_theme_constant_override("margin_" + lado, seg[lado])
	margem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.add_child(margem)
	var linha := HBoxContainer.new()
	linha.mouse_filter = Control.MOUSE_FILTER_IGNORE
	linha.add_theme_constant_override("separation", 8)
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
	chips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# raio pequeno: o texto tem várias linhas, um canto em pílula cortaria as pontas das linhas
	var caixa_info := Tema.caixa(Color(0.03, 0.05, 0.06, 0.72), Color(0.31, 0.9, 0.87, 0.25), 10, 8)
	caixa_info.content_margin_left = 16
	caixa_info.content_margin_right = 18
	chips.add_theme_stylebox_override("panel", caixa_info)
	chips.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	info_vb.add_child(chips)
	_info = Label.new()
	_info.add_theme_font_size_override("font_size", 15)
	_info.add_theme_color_override("font_color", Color(0.62, 0.95, 0.92))
	chips.add_child(_info)
	_alerta = Label.new()
	_alerta.add_theme_color_override("font_color", COR_PERIGO.lightened(0.2))
	_alerta.visible = false
	info_vb.add_child(_alerta)
	_detalhe = PanelContainer.new()
	_detalhe.visible = false
	_detalhe.custom_minimum_size = Vector2(320, 0)
	_detalhe.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	info_vb.add_child(_detalhe)
	_paineis.append(_detalhe)
	var dv := VBoxContainer.new()
	dv.add_theme_constant_override("separation", 6)
	_detalhe.add_child(dv)
	var topo_det := HBoxContainer.new()
	dv.add_child(topo_det)
	_det_titulo = Label.new()
	_det_titulo.add_theme_color_override("font_color", COR_CIANO)
	_det_titulo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	topo_det.add_child(_det_titulo)
	var fechar := Button.new()
	fechar.text = "✕"
	fechar.focus_mode = Control.FOCUS_NONE
	fechar.custom_minimum_size = Vector2(48, 44)
	fechar.pressed.connect(func(): fechar_detalhe_pedido.emit())
	topo_det.add_child(fechar)
	var rolagem := ScrollContainer.new()
	rolagem.custom_minimum_size = Vector2(0, 0)
	rolagem.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	rolagem.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var corpo := VBoxContainer.new()
	corpo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_det_texto = Label.new()
	_det_texto.add_theme_font_size_override("font_size", 15)
	_det_texto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_det_texto.custom_minimum_size = Vector2(296, 0)
	corpo.add_child(_det_texto)
	_det_botoes = VBoxContainer.new()
	_det_botoes.add_theme_constant_override("separation", 4)
	corpo.add_child(_det_botoes)
	rolagem.add_child(corpo)
	rolagem.custom_minimum_size = Vector2(0, 360)
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
	_dica.add_theme_font_size_override("font_size", 15)
	_dica.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_dica.custom_minimum_size = Vector2(420, 0)
	_dica_painel.add_child(_dica)
	_dica_painel.visible = false
	# meio-direita: ferramentas em cima + painel de peças
	var dir := VBoxContainer.new()
	dir.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dir.add_theme_constant_override("separation", 8)
	linha.add_child(dir)
	var ferr_painel := PanelContainer.new()
	ferr_painel.size_flags_horizontal = Control.SIZE_SHRINK_END
	dir.add_child(ferr_painel)
	_paineis.append(ferr_painel)
	_ferr = HFlowContainer.new() if false else HBoxContainer.new()
	_ferr.add_theme_constant_override("separation", 4)
	ferr_painel.add_child(_ferr)
	for f in [["nivel", "⇡ chão", "N"], ["remover", "✕ Remover", "X"], ["aplainar", "▭ Aplainar", "L"], ["desfazer", "↶", "Ctrl+Z"],
			["recursos", "◈ Recursos", "V"], ["poluicao", "☁", "P"], ["pesquisa", "⚗", "T"], ["menu", "☰", "Esc"]]:
		var b := Button.new()
		b.text = f[1]
		b.tooltip_text = "%s (%s)" % [f[0].capitalize(), f[2]]
		b.custom_minimum_size = Vector2(48, 48)
		b.add_theme_font_size_override("font_size", 16)
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
	_painel_pecas.custom_minimum_size = Vector2(400, 0)
	_painel_pecas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_painel_pecas.size_flags_horizontal = Control.SIZE_SHRINK_END
	_painel_pecas.visible = false
	dir.add_child(_painel_pecas)
	_paineis.append(_painel_pecas)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 8)
	_painel_pecas.add_child(pv)
	_titulo_cat = Label.new()
	_titulo_cat.add_theme_font_size_override("font_size", 19)
	_titulo_cat.add_theme_color_override("font_color", COR_CIANO)
	pv.add_child(_titulo_cat)
	var rol := ScrollContainer.new()
	rol.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rol.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pv.add_child(rol)
	_pecas = VBoxContainer.new()
	_pecas.add_theme_constant_override("separation", 6)
	_pecas.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rol.add_child(_pecas)
	# coluna de categorias (polegar direito)
	var col := PanelContainer.new()
	linha.add_child(col)
	_paineis.append(col)
	var cv := VBoxContainer.new()
	cv.add_theme_constant_override("separation", 6)
	cv.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_child(cv)
	_abas = cv
	var cats: Array = Registro.menu.get("categorias", [])
	var icc: Dictionary = Registro.menu.get("icones_categoria", {})
	for i in cats.size():
		var b := Button.new()
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(72, 66)
		b.focus_mode = Control.FOCUS_NONE
		b.icon = _icone(icc.get(cats[i].nome, cats[i].pecas[0]))
		b.expand_icon = true
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.tooltip_text = cats[i].nome
		b.pressed.connect(func(): Som.tocar("clique"); _tocar_categoria(i))
		cv.add_child(b)
	# barra de ações da peça pendente (segue o fantasma): Girar · Mover · Construir · ✕
	_acoes = PanelContainer.new()
	_acoes.visible = false
	raiz.add_child(_acoes)
	_paineis.append(_acoes)
	var ah := HBoxContainer.new()
	ah.add_theme_constant_override("separation", 6)
	_acoes.add_child(ah)
	for a in [["girar", "⟲ Girar", Color(0, 0, 0, 0)], ["mover", "✥ Mover", Color(0, 0, 0, 0)],
			["construir", "✓ Construir", Color(0.12, 0.56, 0.35)], ["cancelar_peca", "✕", Color(0.56, 0.17, 0.17)]]:
		var b := Button.new()
		b.text = a[1]
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(56 if a[0] == "cancelar_peca" else 96, 52)
		if a[2].a > 0.0:
			b.add_theme_stylebox_override("normal", Tema.caixa(a[2], a[2].lightened(0.4), 10, 6))
			b.add_theme_stylebox_override("hover", Tema.caixa(a[2].lightened(0.1), a[2].lightened(0.5), 10, 6))
		b.pressed.connect(func(): Som.tocar("clique"); acao_pendente.emit(a[0]))
		ah.add_child(b)
		_botoes_acao[a[0]] = b
	marcar("", false)


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
	_destacar(_botoes_acao["mover"], movendo, COR_CIANO)


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
		_destacar(_botoes_peca[k], k == nome, COR_CIANO)
	_destacar(_botoes_ferr["remover"], removendo, COR_PERIGO)
	_destacar(_botoes_ferr["aplainar"], nome == "#aplainar", Color(0.35, 0.85, 0.8))
	var ativo := nome != "" or removendo
	_botoes_ferr["cancelar"].disabled = not ativo
	_botoes_ferr["girar"].disabled = nome == "" or nome.begins_with("#")


## Texto do botão de nível (chão / 0,5 m / 1,0 m).
func mostrar_nivel(n: int) -> void:
	var t: String = ["chão", "0,5 m", "1,0 m"][n]
	_botoes_ferr["nivel"].text = "⇡ " + t
	_destacar(_botoes_ferr["nivel"], n > 0, Color(0.45, 0.75, 1.0))


func pode_desfazer(sim: bool) -> void:
	_botoes_ferr["desfazer"].disabled = not sim


## Texto do painel de situação; `alerta` vazio esconde a linha vermelha.
func situacao(texto: String, alerta := "") -> void:
	_info.text = texto
	_alerta.text = alerta
	_alerta.visible = alerta != ""


## Mostra o painel de detalhe. botoes: [{texto, ligado (destaque), acao: Callable}]. Os botões só são refeitos
## quando mudam (o texto é atualizado sempre) — refazer a cada atualização engoliria cliques.
func detalhe(titulo: String, texto: String, botoes: Array) -> void:
	_detalhe.visible = true
	_det_titulo.text = titulo
	_det_texto.text = texto
	var assin := titulo + "|" + "|".join(botoes.map(func(b): return "%s%s" % [b.texto, b.get("ligado", false)]))
	if assin == _det_assinatura:
		return
	_det_assinatura = assin
	for c in _det_botoes.get_children():
		c.queue_free()
	for b in botoes:
		var bt := Button.new()
		bt.text = b.texto
		bt.focus_mode = Control.FOCUS_NONE
		bt.custom_minimum_size = Vector2(0, 46)
		bt.alignment = HORIZONTAL_ALIGNMENT_LEFT
		bt.pressed.connect(b.acao)
		_det_botoes.add_child(bt)
		_destacar(bt, b.get("ligado", false), COR_DESTAQUE)


func fechar_detalhe() -> void:
	_detalhe.visible = false
	_det_assinatura = ""


func ligar_recursos(sim: bool) -> void:
	_destacar(_botoes_ferr["recursos"], sim, Color(0.35, 0.85, 0.8))


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
	var icones: Dictionary = Registro.menu.get("icones", {})
	var expl: Dictionary = Registro.menu.get("explicacoes", {})
	var pecas := pecas_da_categoria()
	for k in pecas.size():
		var nome: String = pecas[k]
		var b := Button.new()
		b.custom_minimum_size = Vector2(0, 74)
		b.focus_mode = Control.FOCUS_NONE
		b.icon = _icone(icones.get(nome, nome))
		b.expand_icon = false
		b.add_theme_constant_override("icon_max_width", 58)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		var custo := Construtor.custo_de(nome)
		var partes: Array[String] = []
		for it in custo:
			partes.append("%d %s" % [custo[it], Registro.itens.get(it, {}).get("nome", it).to_lower()])
		var kw := float(Registro.estruturas.get(nome, {}).get("energia_kw", 0.0))
		var extra := (" · ⚡%d kW" % kw) if kw > 0.0 else ""
		var bloqueada: bool = liberado.is_valid() and not liberado.call(nome)
		b.text = "%s%s\n%s\n%s%s" % [rotulo(nome), "" if toque else "  (%d)" % (k + 1), expl.get(nome, ""),
				"🔒 pesquisar" if bloqueada else ", ".join(partes), "" if bloqueada else extra]
		b.add_theme_font_size_override("font_size", 14)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.pressed.connect(func(): Som.tocar("clique"); peca_escolhida.emit(nome); fechar_pecas())
		if bloqueada:
			b.modulate = Color(0.6, 0.6, 0.65)
		_pecas.add_child(b)
		_botoes_peca[nome] = b
	if _botoes_ferr.has("remover"):
		marcar(_selecionada, _removendo)


func _icone(modelo: String) -> Texture2D:
	var c := "res://assets/icones/%s.png" % modelo
	return load(c) if ResourceLoader.exists(c) else null


func _destacar(b: Button, sim: bool, cor: Color) -> void:
	if sim:
		var s := (_tema.get_stylebox("normal", "Button") as StyleBoxFlat).duplicate() as StyleBoxFlat
		s.border_color = cor
		s.set_border_width_all(3)
		s.bg_color = cor.darkened(0.72)
		b.add_theme_stylebox_override("normal", s)
		b.add_theme_stylebox_override("hover", s)
	else:
		b.remove_theme_stylebox_override("normal")
		b.remove_theme_stylebox_override("hover")
