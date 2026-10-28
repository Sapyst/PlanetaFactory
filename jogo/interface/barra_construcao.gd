class_name BarraConstrucao
extends CanvasLayer
## Interface de construção, toda montada por código (PC e toque, botões grandes):
##   embaixo — abas de categoria + peças da categoria (ícone renderizado da arte + nome);
##   à direita — Girar, Remover, Desfazer, Cancelar;
##   em cima — dica: o que está na mão e por que o fantasma ficou vermelho.
## Não sabe de regra: só emite sinais. Categorias e textos vêm de dados/menu_construcao.json.

signal peca_escolhida(nome: String)
signal ferramenta(nome: String)       ## "girar", "remover", "desfazer", "cancelar", "recursos", "poluicao", "pesquisa", "menu"

const TAM_PECA := Vector2(116, 112)
const COR_FUNDO := Color(0.09, 0.10, 0.13, 0.92)
const COR_BORDA := Color(0.28, 0.30, 0.36)
const COR_DESTAQUE := Color(0.96, 0.74, 0.24)
const COR_PERIGO := Color(0.95, 0.35, 0.30)

var toque := false                     ## sem atalhos de teclado nos textos
var liberado: Callable                 ## nome da peça → bool (pesquisa); vazio = tudo liberado
var _tema: Theme
var _abas: HBoxContainer
var _pecas: HBoxContainer
var _ferr: VBoxContainer
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


func _ready() -> void:
	layer = 10
	toque = DisplayServer.is_touchscreen_available()
	_tema = Tema.criar()
	var raiz := Control.new()
	raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.theme = _tema
	add_child(raiz)
	# layout por containers (escala com a tela): dica em cima, ferramentas à direita, barra embaixo
	var margem := MarginContainer.new()
	margem.set_anchors_preset(Control.PRESET_FULL_RECT)
	for lado in ["left", "right", "top", "bottom"]:
		margem.add_theme_constant_override("margin_" + lado, 10)
	raiz.add_child(margem)
	var coluna := VBoxContainer.new()
	margem.add_child(coluna)
	var topo := CenterContainer.new()          # dica: logo acima da barra (no celular o canto de cima é do painel de situação)
	var meio := HBoxContainer.new()
	meio.size_flags_vertical = Control.SIZE_EXPAND_FILL
	coluna.add_child(meio)
	var vazio := Control.new()
	vazio.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	meio.add_child(vazio)
	var lado_dir := CenterContainer.new()
	meio.add_child(lado_dir)
	coluna.add_child(topo)
	var base := CenterContainer.new()
	coluna.add_child(base)
	for c in [margem, coluna, topo, meio, vazio, lado_dir, base]:
		(c as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE

	# barra de baixo: abas + peças
	var baixo := PanelContainer.new()
	base.add_child(baixo)
	_paineis.append(baixo)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 8)
	baixo.add_child(vb)
	_abas = HBoxContainer.new()
	_abas.add_theme_constant_override("separation", 4)
	vb.add_child(_abas)
	_pecas = HBoxContainer.new()
	_pecas.add_theme_constant_override("separation", 6)
	_pecas.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.add_child(_pecas)
	var grupo := ButtonGroup.new()
	var cats: Array = Registro.menu.get("categorias", [])
	for i in cats.size():
		var b := Button.new()
		b.text = cats[i].nome
		b.toggle_mode = true
		b.button_group = grupo
		b.custom_minimum_size = Vector2(0, 44)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(_mostrar_categoria.bind(i))
		_abas.add_child(b)

	# ferramentas à direita
	var dir := PanelContainer.new()
	lado_dir.add_child(dir)
	_paineis.append(dir)
	_ferr = VBoxContainer.new()
	_ferr.add_theme_constant_override("separation", 4)
	dir.add_child(_ferr)
	for f in [["nivel", "Nível: chão", "N"], ["girar", "Girar", "R"], ["remover", "Remover", "X"], ["desfazer", "Desfazer", "Ctrl+Z"], ["cancelar", "Cancelar", "Esc"],
			["recursos", "Recursos", "V"], ["poluicao", "Poluição", "P"], ["pesquisa", "Pesquisa", "T"], ["menu", "Menu", "Esc"]]:
		var b := Button.new()
		b.text = f[1] if toque else "%s  (%s)" % [f[1], f[2]]
		b.custom_minimum_size = Vector2(150, 46)
		b.add_theme_font_size_override("font_size", 16)
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(func(): Som.tocar("clique"); ferramenta.emit(f[0]))
		_ferr.add_child(b)
		_botoes_ferr[f[0]] = b

	# painel de situação no canto de cima (poluição, ninhos, aranhas, alerta de ataque)
	var canto := MarginContainer.new()
	_canto = canto
	canto.set_anchors_preset(Control.PRESET_TOP_LEFT)
	for lado in ["left", "top"]:
		canto.add_theme_constant_override("margin_" + lado, 10)
	canto.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.add_child(canto)
	var info_painel := PanelContainer.new()
	info_painel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canto.add_child(info_painel)
	var info_vb := VBoxContainer.new()
	info_painel.add_child(info_vb)
	_info = Label.new()
	_info.add_theme_font_size_override("font_size", 16)
	info_vb.add_child(_info)
	_alerta = Label.new()
	_alerta.add_theme_color_override("font_color", COR_PERIGO.lightened(0.2))
	_alerta.visible = false
	info_vb.add_child(_alerta)
	# painel de detalhe (peça ou trem selecionado): estado, conteúdo e escolhas (receita, rota)
	_detalhe = PanelContainer.new()
	_detalhe.visible = false
	_detalhe.custom_minimum_size = Vector2(300, 0)
	info_vb.add_child(_detalhe)
	_paineis.append(_detalhe)
	var dv := VBoxContainer.new()
	dv.add_theme_constant_override("separation", 6)
	_detalhe.add_child(dv)
	var topo_det := HBoxContainer.new()
	dv.add_child(topo_det)
	_det_titulo = Label.new()
	_det_titulo.add_theme_color_override("font_color", COR_DESTAQUE)
	_det_titulo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	topo_det.add_child(_det_titulo)
	var fechar := Button.new()
	fechar.text = "Fechar"
	fechar.focus_mode = Control.FOCUS_NONE
	fechar.custom_minimum_size = Vector2(90, 44)
	fechar.pressed.connect(func(): fechar_detalhe_pedido.emit())
	topo_det.add_child(fechar)
	_det_texto = Label.new()
	_det_texto.add_theme_font_size_override("font_size", 16)
	dv.add_child(_det_texto)
	_det_botoes = VBoxContainer.new()
	_det_botoes.add_theme_constant_override("separation", 4)
	dv.add_child(_det_botoes)

	# dica em cima
	_dica_painel = PanelContainer.new()
	_dica_painel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	topo.add_child(_dica_painel)
	_dica = Label.new()
	_dica.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_dica_painel.add_child(_dica)
	_dica_painel.visible = false

	(_abas.get_child(0) as Button).button_pressed = true
	_mostrar_categoria(0)
	marcar("", false)


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
		_destacar(_botoes_peca[k], k == nome, COR_DESTAQUE)
	_destacar(_botoes_ferr["remover"], removendo, COR_PERIGO)
	var ativo := nome != "" or removendo
	_botoes_ferr["cancelar"].disabled = not ativo
	_botoes_ferr["girar"].disabled = nome == ""


## Texto do botão de nível (chão / 0,5 m / 1,0 m).
func mostrar_nivel(n: int) -> void:
	var t: String = ["chão", "0,5 m", "1,0 m"][n]
	_botoes_ferr["nivel"].text = "Nível: " + t if toque else "Nível: %s  (N)" % t
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
	var n := _abas.get_child_count()
	_cat = posmod(_cat + passo, n)
	(_abas.get_child(_cat) as Button).button_pressed = true
	_mostrar_categoria(_cat)


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
	var icones: Dictionary = Registro.menu.get("icones", {})
	var pecas := pecas_da_categoria()
	for k in pecas.size():
		var nome: String = pecas[k]
		var b := Button.new()
		b.custom_minimum_size = TAM_PECA
		b.focus_mode = Control.FOCUS_NONE
		b.icon = _icone(icones.get(nome, nome))
		b.expand_icon = true
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		b.text = rotulo(nome) if toque else "%d · %s" % [k + 1, rotulo(nome)]
		b.add_theme_font_size_override("font_size", 16)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.tooltip_text = Registro.modelos.get(icones.get(nome, nome), {}).get("descricao", "")
		b.pressed.connect(func(): Som.tocar("clique"); peca_escolhida.emit(nome))
		if liberado.is_valid() and not liberado.call(nome):
			b.modulate = Color(0.55, 0.55, 0.6)        # bloqueada: ainda dá para tocar e ler o que falta
			b.text = rotulo(nome) + "\n(pesquisar)"
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
