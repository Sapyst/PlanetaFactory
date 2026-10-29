class_name TelaPesquisa
extends CanvasLayer
## Árvore de pesquisa (botão ⚗ / T), por cima do jogo: cada pesquisa é um nó com o ícone do que libera, em colunas
## por profundidade (sem pré-requisito à esquerda) e ligado aos pré-requisitos por linhas (verde = já feito).
## O quadro rola nas duas direções pelo dedo (RolagemToque). Tocar num nó mostra o detalhe ao lado: custo, o que
## libera em casas com ícone, o que falta e o botão Pesquisar.

signal fechou

const NO := Vector2(250, 92)           ## tamanho de um nó
const ESP := Vector2(72, 18)           ## espaço entre colunas / entre nós
const COR_FEITA := Tema.COR.sucesso
const COR_TRAVADA := Tema.COR.travado

var pesquisa: Pesquisa
var rotulo: Callable                     ## nome da peça → texto (BarraConstrucao.rotulo)
var nome_item: Callable                  ## item → nome
var tema: Theme

var _painel: PanelContainer
var _raiz: Control
var _status: Label
var _barra: ProgressBar
var _rolagem: ScrollContainer
var _arvore: Control                     ## quadro com os nós (desenha as linhas)
var _lado: PanelContainer
var _det: VBoxContainer
var _pos: Dictionary = {}                ## id → retângulo do nó no quadro
var _nos: Dictionary = {}                ## id → Button
var _sel := ""
var _assinatura := ""
var _t := 0.0


func _ready() -> void:
	layer = 15
	visible = false
	var raiz := Control.new()
	raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.theme = tema
	raiz.visible = false                  # escondida de verdade: o fundo de tela cheia não pode engolir toques
	add_child(raiz)
	_raiz = raiz
	var fundo := ColorRect.new()
	fundo.color = Color(0, 0, 0, 0.6)
	fundo.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.add_child(fundo)
	_painel = PanelContainer.new()
	raiz.add_child(_painel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	_painel.add_child(v)
	var topo := HBoxContainer.new()
	topo.add_theme_constant_override("separation", 12)
	v.add_child(topo)
	var titulo := Label.new()
	titulo.text = "Pesquisa"
	titulo.add_theme_font_size_override("font_size", 24)
	titulo.add_theme_color_override("font_color", Tema.cor("titulo"))
	topo.add_child(titulo)
	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.add_theme_font_size_override("font_size", 15)
	_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_status.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	topo.add_child(_status)
	var fechar_b := Button.new()
	fechar_b.text = "✕  Fechar"
	fechar_b.custom_minimum_size = Vector2(120, 52)
	fechar_b.focus_mode = Control.FOCUS_NONE
	fechar_b.pressed.connect(fechar)
	topo.add_child(fechar_b)
	v.add_child(Tema.faixa_titulo())
	_barra = ProgressBar.new()
	_barra.custom_minimum_size = Vector2(0, 12)
	_barra.show_percentage = false
	v.add_child(_barra)
	var corpo := HBoxContainer.new()
	corpo.size_flags_vertical = Control.SIZE_EXPAND_FILL
	corpo.add_theme_constant_override("separation", 10)
	v.add_child(corpo)
	_rolagem = ScrollContainer.new()
	_rolagem.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_rolagem.size_flags_vertical = Control.SIZE_EXPAND_FILL
	corpo.add_child(_rolagem)
	_arvore = Control.new()
	_arvore.draw.connect(_desenhar_linhas)
	_rolagem.add_child(_arvore)
	_rolagem.add_child(RolagemToque.new())
	_lado = PanelContainer.new()
	_lado.add_theme_stylebox_override("panel", Tema.caixa(Color(0.05, 0.05, 0.06, 0.95), Color(Tema.cor("filete"), 0.7), 10, 12))
	corpo.add_child(_lado)
	var rl := ScrollContainer.new()
	rl.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_lado.add_child(rl)
	_det = VBoxContainer.new()
	_det.add_theme_constant_override("separation", 8)
	_det.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rl.add_child(_det)
	rl.add_child(RolagemToque.new())
	get_viewport().size_changed.connect(_posicionar)


func alternar() -> void:
	if visible:
		fechar()
	else:
		abrir()


func abrir() -> void:
	visible = true
	_raiz.visible = true
	_assinatura = ""
	if _sel == "" and pesquisa != null:
		_sel = pesquisa.ativa
	_posicionar()
	_atualizar()


func fechar() -> void:
	if visible:
		visible = false
		_raiz.visible = false
		fechou.emit()


func _posicionar() -> void:
	var tela := _painel.get_viewport().get_visible_rect().size
	var m := 12.0
	_painel.position = Vector2(m, m)
	_painel.size = tela - Vector2(2.0 * m, 2.0 * m)
	_painel.custom_minimum_size = _painel.size
	_lado.custom_minimum_size.x = clampf(tela.x * 0.3, 250.0, 360.0)


func _process(delta: float) -> void:
	if not visible:
		return
	_t -= delta
	if _t <= 0.0:
		_t = 0.4
		_atualizar()


func _atualizar() -> void:
	if pesquisa == null:
		return
	var at: Dictionary = pesquisa.pesquisas().get(pesquisa.ativa, {})
	if pesquisa.livre:
		_status.text = "Demonstração: tudo já está liberado."
	elif not at.is_empty():
		_status.text = "Pesquisando %s — %d de %d pacotes" % [at.nome, pesquisa.feitos, at.pacotes]
	else:
		_status.text = "Toque numa pesquisa para ver e escolher."
	_barra.visible = not at.is_empty()
	if not at.is_empty():
		_barra.max_value = float(at.pacotes)
		_barra.value = float(pesquisa.feitos)
	var assin := "%s|%s|%d|%s" % [pesquisa.ativa, pesquisa.concluidas.keys(), pesquisa.feitos, _sel]
	if assin == _assinatura:
		return
	var primeira := _assinatura == ""
	_assinatura = assin
	_montar_arvore()
	_mostrar_detalhe()
	if primeira and _sel != "" and _pos.has(_sel):         # abre com a pesquisa ativa à vista
		var r: Rect2 = _pos[_sel]
		_rolagem.set_deferred("scroll_horizontal", int(maxf(0.0, r.position.x - 40.0)))
		_rolagem.set_deferred("scroll_vertical", int(maxf(0.0, r.position.y - 80.0)))


# ------------------------------------------------------------------ árvore
func _profundidade(id: String, memo: Dictionary) -> int:
	if memo.has(id):
		return memo[id]
	var p := 0
	for r in pesquisa.pesquisas()[id].get("requer", []):
		p = maxi(p, _profundidade(r, memo) + 1)
	memo[id] = p
	return p


## Colunas por profundidade; dentro da coluna, na ordem média dos pré-requisitos (linhas cruzam menos).
func _layout() -> void:
	var memo := {}
	var colunas: Dictionary = {}
	for id in pesquisa.pesquisas():
		var p := _profundidade(id, memo)
		if not colunas.has(p):
			colunas[p] = []
		colunas[p].append(id)
	var linha: Dictionary = {}
	_pos.clear()
	var maior := 0
	for p in range(colunas.size()):
		var lista: Array = colunas.get(p, [])
		lista.sort_custom(func(a, b): return _media(a, linha) < _media(b, linha))
		for i in lista.size():
			linha[lista[i]] = i
			_pos[lista[i]] = Rect2(Vector2(16 + p * (NO.x + ESP.x), 16 + i * (NO.y + ESP.y)), NO)
		maior = maxi(maior, lista.size())
	_arvore.custom_minimum_size = Vector2(32 + colunas.size() * (NO.x + ESP.x) - ESP.x, 32 + maior * (NO.y + ESP.y) - ESP.y)


func _media(id: String, linha: Dictionary) -> float:
	var req: Array = pesquisa.pesquisas()[id].get("requer", [])
	if req.is_empty():
		return float(pesquisa.pesquisas().keys().find(id))
	var s := 0.0
	for r in req:
		s += float(linha.get(r, 0))
	return s / req.size()


func _montar_arvore() -> void:
	for c in _arvore.get_children():
		c.queue_free()
	_nos.clear()
	_layout()
	for id in _pos:
		var pq: Dictionary = pesquisa.pesquisas()[id]
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.position = (_pos[id] as Rect2).position
		b.size = NO
		b.custom_minimum_size = NO
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.icon = _icone_da(id)
		b.expand_icon = false
		b.add_theme_constant_override("icon_max_width", 56)
		b.text = "%s\n%s" % [pq.nome, _situacao(id)]
		b.add_theme_font_size_override("font_size", 16)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var cor := _cor(id)
		var fundo := Color(0.05, 0.08, 0.1, 0.96).lerp(cor, 0.12)
		for estado in ["normal", "hover", "pressed"]:
			var st := Tema.caixa(fundo.lightened(0.06 if estado == "hover" else 0.0), cor, 10, 8)
			st.border_width_left = 3 if _sel != id else 5
			st.border_width_right = st.border_width_left
			st.border_width_top = st.border_width_left
			st.border_width_bottom = st.border_width_left
			b.add_theme_stylebox_override(estado, st)
		b.pressed.connect(RolagemToque.so_clique(func():
			Som.tocar("clique")
			_sel = id
			_atualizar()))
		_arvore.add_child(b)
		_nos[id] = b
	_arvore.queue_redraw()


func _desenhar_linhas() -> void:
	for id in _pos:
		var r: Rect2 = _pos[id]
		for req in pesquisa.pesquisas()[id].get("requer", []):
			if not _pos.has(req):
				continue
			var rr: Rect2 = _pos[req]
			var a := Vector2(rr.end.x, rr.get_center().y)
			var b := Vector2(r.position.x, r.get_center().y)
			# cada ligação dobra numa altura própria do corredor (pelo nó de destino): troncos não se sobrepõem
			var lado := float(int(r.position.y / (NO.y + ESP.y)) % 4) / 3.0
			var mx := a.x + ESP.x * (0.25 + 0.5 * lado)
			var cor := COR_FEITA if pesquisa.concluidas.has(req) else COR_TRAVADA
			_arvore.draw_polyline(PackedVector2Array([a, Vector2(mx, a.y), Vector2(mx, b.y), b]), cor, 3.0, true)
			_arvore.draw_circle(b, 5.0, cor)


func _cor(id: String) -> Color:
	if pesquisa.ativa == id:
		return BarraConstrucao.COR_DESTAQUE
	if pesquisa.concluidas.has(id):
		return COR_FEITA
	if pesquisa.disponivel(id):
		return Tema.cor("pesquisa")
	return COR_TRAVADA


func _situacao(id: String) -> String:
	var pq: Dictionary = pesquisa.pesquisas()[id]
	if pesquisa.concluidas.has(id):
		return "✓ concluída"
	if pesquisa.ativa == id:
		return "pesquisando %d/%d" % [pesquisa.feitos, int(pq.pacotes)]
	if pesquisa.disponivel(id):
		return "%d pacotes" % int(pq.pacotes)
	return "🔒 %d pacotes" % int(pq.pacotes)


## Ícone do nó: a primeira peça que libera; sem peça, o primeiro item das receitas.
func _icone_da(id: String) -> Texture2D:
	var pq: Dictionary = pesquisa.pesquisas()[id]
	for n in pq.get("libera", []):
		var t := _tex_peca(n)
		if t != null:
			return t
	for r in pq.get("receitas", []):
		for it in Registro.receitas.get(r, {}).get("saidas", {}):
			var t := _tex_item(it)
			if t != null:
				return t
	return null


static func _tex_peca(n: String) -> Texture2D:
	var icones: Dictionary = Registro.menu.get("icones", {})
	var nome: String = icones.get(n, n)
	for c in ["res://assets/icones/%s.png" % nome, "res://assets/icones/%s_reta.png" % nome]:
		if ResourceLoader.exists(c):
			return load(c)
	return null


static func _tex_item(it: String) -> Texture2D:
	var c := "res://assets/icones/itens/%s.png" % it
	return load(c) if ResourceLoader.exists(c) else null


# ------------------------------------------------------------------ detalhe do nó escolhido
func _mostrar_detalhe() -> void:
	for c in _det.get_children():
		c.queue_free()
	if _sel == "" or not pesquisa.pesquisas().has(_sel):
		var l := Label.new()
		l.text = "Toque numa pesquisa da árvore.\n\nO laboratório (com energia) gasta pacotes de pesquisa. A montadora faz cada pacote com 1 cristal lapidado + 1 engrenagem; um braço leva os pacotes ao laboratório."
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.add_theme_font_size_override("font_size", 15)
		_det.add_child(l)
		return
	var pq: Dictionary = pesquisa.pesquisas()[_sel]
	var nome := Label.new()
	nome.text = pq.nome
	nome.add_theme_font_size_override("font_size", 22)
	nome.add_theme_color_override("font_color", _cor(_sel).lightened(0.2))
	nome.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_det.add_child(nome)
	var custo := HBoxContainer.new()
	custo.add_theme_constant_override("separation", 8)
	custo.add_child(Casa.nova(_tex_item("pacote_pesquisa"), str(int(pq.pacotes))))
	var cl := Label.new()
	cl.text = "pacotes de pesquisa\n%d s cada no laboratório" % pq.get("tempo", 5)
	cl.add_theme_font_size_override("font_size", 14)
	custo.add_child(cl)
	_det.add_child(custo)
	var tl := Label.new()
	tl.text = "Libera"
	tl.add_theme_color_override("font_color", Tema.cor("titulo"))
	_det.add_child(tl)
	var casas := HFlowContainer.new()
	casas.add_theme_constant_override("h_separation", 6)
	casas.add_theme_constant_override("v_separation", 6)
	_det.add_child(casas)
	var nomes: Array[String] = []
	for n in pq.get("libera", []):
		casas.add_child(Casa.nova(_tex_peca(n), "", rotulo.call(n) if rotulo.is_valid() else n))
		nomes.append(rotulo.call(n) if rotulo.is_valid() else n)
	for r in pq.get("receitas", []):
		for it in Registro.receitas.get(r, {}).get("saidas", {}):
			var nm: String = nome_item.call(it) if nome_item.is_valid() else it
			casas.add_child(Casa.nova(_tex_item(it), "", "receita: " + nm))
			nomes.append("receita de " + nm.to_lower())
	var ln := Label.new()
	ln.text = ", ".join(nomes) if not nomes.is_empty() else "—"
	ln.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ln.add_theme_font_size_override("font_size", 14)
	_det.add_child(ln)
	var req: Array = pq.get("requer", [])
	if not req.is_empty():
		var rl := Label.new()
		var partes: Array[String] = []
		for r in req:
			partes.append(("✓ " if pesquisa.concluidas.has(r) else "✗ ") + pesquisa.pesquisas()[r].nome)
		rl.text = "Precisa de: " + ", ".join(partes)
		rl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		rl.add_theme_font_size_override("font_size", 14)
		_det.add_child(rl)
	var b := Button.new()
	b.custom_minimum_size = Vector2(0, 56)
	b.focus_mode = Control.FOCUS_NONE
	if pesquisa.concluidas.has(_sel):
		b.text = "✓ Concluída"
		b.disabled = true
	elif pesquisa.ativa == _sel:
		b.text = "Pesquisando… %d/%d" % [pesquisa.feitos, pq.pacotes]
		b.disabled = true
	elif pesquisa.disponivel(_sel):
		b.text = "Pesquisar"
		var id := _sel
		b.pressed.connect(RolagemToque.so_clique(func():
			Som.tocar("clique")
			pesquisa.escolher(id)
			_atualizar()))
	else:
		b.text = "Termine antes o que falta"
		b.disabled = true
	_det.add_child(b)
