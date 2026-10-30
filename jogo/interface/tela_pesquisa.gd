class_name TelaPesquisa
extends CanvasLayer
## Árvore de pesquisa (botão ⚗ / T), por cima do jogo: a árvore de tecnologia inteira (dados/arvore.json) em três
## faixas, uma por era (base, meio, super avançada), cada uma com a sua cor. Dentro da faixa, colunas por profundidade
## (sem pré-requisito da mesma era à esquerda); linhas ligam aos pré-requisitos (verde = já feito). As pesquisas que
## já existem no jogo (progressao.json) se pesquisam; as que ainda não dá para fazer (fora do jogo, ou travadas por
## pacote/pesquisa que não existe: Pesquisa.em_desenvolvimento) ficam em cinza escuro com o selo "Em desenvolvimento"
## e não se escolhem (o detalhe diz por quê).
## O quadro rola nas duas direções pelo dedo (RolagemToque) e tem zoom: pinça com dois dedos, Ctrl + roda do mouse,
## gesto do trackpad ou os botões − e +. Tocar num nó mostra o detalhe ao lado: custo, o que
## libera em casas com ícone, o que falta e o botão Pesquisar.

signal fechou

const NO := Vector2(250, 92)           ## tamanho de um nó
const ESP := Vector2(72, 18)           ## espaço entre colunas / entre nós
const COR_FEITA := Tema.COR.sucesso
const COR_TRAVADA := Tema.COR.travado
const CABECALHO := 46.0                ## altura do título da faixa da era
const ERA_COR := {"base": Color(0.36, 0.62, 0.29), "meio": Color(0.29, 0.5, 0.77), "avancada": Color(0.6, 0.37, 0.79)}
const COR_OBJETIVO := Color(0.85, 0.31, 0.25)
const TIPOS := {                       ## o que a tecnologia faz no jogo: símbolo e explicação
	"estrutura": ["■", "estrutura nova"], "receita": ["⚗", "receita nova"], "melhoria": ["▲", "melhora o que já existe"],
	"infinita": ["∞", "melhoria infinita"], "objetivo": ["★", "objetivo final"]}
const ZOOM_MIN := 0.3
const ZOOM_MAX := 1.6

var pesquisa: Pesquisa
var rotulo: Callable                     ## nome da peça → texto (BarraConstrucao.rotulo)
var nome_item: Callable                  ## item → nome
var tema: Theme

var _painel: PanelContainer
var _raiz: Control
var _status: Label
var _barra: ProgressBar
var _rolagem: ScrollContainer
var _arvore: Control                     ## quadro com os nós (desenha as linhas); escala = zoom
var _palco: Control                      ## ocupa na rolagem o tamanho do quadro já com zoom
var _rt: RolagemToque
var _zoom := 0.0                         ## 0 = ainda não ajustado à tela
var _dedos: Dictionary = {}              ## índice do toque → posição (pinça)
var _pinca := {}                         ## {dist, zoom} no começo da pinça
var _lado: PanelContainer
var _det: VBoxContainer
var _pos: Dictionary = {}                ## id → retângulo do nó no quadro
var _faixas: Array = []                  ## [{rect, cor, nome}] das eras
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
	for z in [["−", 1.0 / 1.25], ["+", 1.25]]:                     # zoom por botão (mesmo efeito da pinça)
		var zb := Button.new()
		zb.text = z[0]
		zb.custom_minimum_size = Vector2(52, 52)
		zb.focus_mode = Control.FOCUS_NONE
		zb.add_theme_font_size_override("font_size", 26)
		var fator: float = z[1]
		zb.pressed.connect(func(): _zoom_em(_zoom * fator, _rolagem.size / 2.0))
		topo.add_child(zb)
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
	_palco = Control.new()
	_rolagem.add_child(_palco)
	_arvore = Control.new()
	_arvore.draw.connect(_desenhar_linhas)
	_palco.add_child(_arvore)
	_rt = RolagemToque.new()
	_rolagem.add_child(_rt)
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
	if _zoom == 0.0:                                              # 1ª vez: cabe mais na tela pequena
		_zoom = clampf(_painel.get_viewport().get_visible_rect().size.x / 1700.0, 0.5, 1.0)
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
	_painel.custom_minimum_size = tela - Vector2(2.0 * m, 2.0 * m)   # mínimo antes: senão o antigo (maior) segura o tamanho
	_painel.size = _painel.custom_minimum_size
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
		_status.text = "Pesquisando %s — %d de %d (%s)" % [at.nome, pesquisa.feitos, pesquisa.unidades(pesquisa.ativa), pesquisa.custo_texto(pesquisa.ativa)]
	else:
		_status.text = "Toque numa pesquisa para ver e escolher."
	_barra.visible = not at.is_empty()
	if not at.is_empty():
		_barra.max_value = float(pesquisa.unidades(pesquisa.ativa))
		_barra.value = float(pesquisa.feitos)
	var assin := "%s|%s|%d|%s" % [pesquisa.ativa, pesquisa.assinatura(), pesquisa.feitos, _sel]
	if assin == _assinatura:
		return
	var primeira := _assinatura == ""
	_assinatura = assin
	_montar_arvore()
	_mostrar_detalhe()
	if primeira and _sel != "" and _pos.has(_sel):         # abre com a pesquisa ativa à vista
		var r: Rect2 = _pos[_sel]
		_rolagem.set_deferred("scroll_horizontal", int(maxf(0.0, r.position.x * _zoom - 40.0)))
		_rolagem.set_deferred("scroll_vertical", int(maxf(0.0, r.position.y * _zoom - 80.0)))


# ------------------------------------------------------------------ zoom
func _aplicar_zoom() -> void:
	_arvore.scale = Vector2(_zoom, _zoom)
	_palco.custom_minimum_size = _arvore.custom_minimum_size * _zoom


## Zoom mantendo parado o ponto do quadro que está sob `foco` (posição dentro da área de rolagem).
func _zoom_em(novo: float, foco: Vector2) -> void:
	novo = clampf(novo, ZOOM_MIN, ZOOM_MAX)
	if is_equal_approx(novo, _zoom):
		return
	var rol := Vector2(_rolagem.scroll_horizontal, _rolagem.scroll_vertical)
	var conteudo := (rol + foco) / _zoom
	_zoom = novo
	_aplicar_zoom()
	await get_tree().process_frame                               # barras de rolagem já com o tamanho novo
	var alvo := conteudo * _zoom - foco
	_rolagem.scroll_horizontal = int(maxf(0.0, alvo.x))
	_rolagem.scroll_vertical = int(maxf(0.0, alvo.y))
	_rt.sincronizar()


func _input(e: InputEvent) -> void:
	if not visible:
		return
	var dentro := func(p: Vector2) -> bool: return _rolagem.get_global_rect().has_point(p)
	if e is InputEventMagnifyGesture and dentro.call(e.position):
		_zoom_em(_zoom * e.factor, e.position - _rolagem.global_position)
	elif e is InputEventMouseButton and e.pressed and e.ctrl_pressed and dentro.call(e.position) \
			and e.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
		_zoom_em(_zoom * (1.1 if e.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.1), e.position - _rolagem.global_position)
		get_viewport().set_input_as_handled()
	elif e is InputEventScreenTouch:
		if e.pressed and dentro.call(e.position):
			_dedos[e.index] = e.position
		else:
			_dedos.erase(e.index)
		if _dedos.size() == 2:
			var p: Array = _dedos.values()
			_pinca = {"dist": maxf((p[0] as Vector2).distance_to(p[1]), 1.0), "zoom": _zoom}
			_rt.parado = true
		elif _dedos.size() < 2 and _rt.parado:
			_pinca = {}
			_rt.parado = false
			_rt.sincronizar()
	elif e is InputEventScreenDrag and _dedos.has(e.index):
		_dedos[e.index] = e.position
		if _dedos.size() == 2 and not _pinca.is_empty():
			var p: Array = _dedos.values()
			var meio: Vector2 = ((p[0] as Vector2) + (p[1] as Vector2)) / 2.0 - _rolagem.global_position
			_zoom_em(_pinca.zoom * (p[0] as Vector2).distance_to(p[1]) / _pinca.dist, meio)
			get_viewport().set_input_as_handled()


# ------------------------------------------------------------------ árvore
## Todos os nós: a árvore completa; sem arvore.json, só as pesquisas jogáveis.
func _ids() -> Array:
	return pesquisa.arvore().keys() if not pesquisa.arvore().is_empty() else pesquisa.pesquisas().keys()


## Dados de um nó: os da pesquisa jogável (custo real em pacotes) com a era da árvore; ou só os da árvore.
func _no(id: String) -> Dictionary:
	var a: Dictionary = pesquisa.arvore().get(id, {})
	if pesquisa.jogavel(id):
		var d: Dictionary = pesquisa.pesquisas()[id].duplicate()
		d.era = a.get("era", "base")
		d.tipo = a.get("tipo", "estrutura")
		d.texto = a.get("libera", "")
		return d
	return a


func _em_breve(id: String) -> bool:
	return not pesquisa.jogavel(id)


## Ainda não dá para fazer no jogo (em breve, ou travada por algo em breve): cinza escuro, selo, não se pesquisa.
func _em_dev(id: String) -> bool:
	return pesquisa.em_desenvolvimento(id)


func _nome(id: String) -> String:
	return str(_no(id).get("nome", id))


## Profundidade dentro da própria era: só contam os pré-requisitos da mesma era.
func _profundidade(id: String, memo: Dictionary) -> int:
	if memo.has(id):
		return memo[id]
	var p := 0
	var era: String = _no(id).get("era", "")
	for r in _no(id).get("requer", []):
		if _no(r).get("era", "") == era:
			p = maxi(p, _profundidade(r, memo) + 1)
	memo[id] = p
	return p


## Uma faixa por era, lado a lado; na faixa, colunas por profundidade e, dentro da coluna, na ordem média dos
## pré-requisitos (linhas cruzam menos).
func _layout() -> void:
	var memo := {}
	var por_era: Dictionary = {}
	for id in _ids():
		var era: String = _no(id).get("era", "base")
		if not por_era.has(era):
			por_era[era] = {}
		var p := _profundidade(id, memo)
		if not por_era[era].has(p):
			por_era[era][p] = []
		por_era[era][p].append(id)
	var ordem: Array = []
	for e in pesquisa.eras():
		ordem.append(e.id)
	for e in por_era:
		if not e in ordem:
			ordem.append(e)
	var linha: Dictionary = {}
	_pos.clear()
	_faixas.clear()
	var x := 16.0
	var maior := 0
	for era in ordem:
		if not por_era.has(era):
			continue
		var colunas: Dictionary = por_era[era]
		var x0 := x
		var mais := 0
		for p in range(colunas.size()):
			var lista: Array = colunas.get(p, [])
			lista.sort_custom(func(a, b): return _media(a, linha) < _media(b, linha))
			for i in lista.size():
				linha[lista[i]] = i
				_pos[lista[i]] = Rect2(Vector2(x + 14.0, 16 + CABECALHO + i * (NO.y + ESP.y)), NO)
			mais = maxi(mais, lista.size())
			x += NO.x + ESP.x
		maior = maxi(maior, mais)
		var nome_era: String = era
		for e in pesquisa.eras():
			if e.id == era:
				nome_era = e.nome
		_faixas.append({"x0": x0, "x1": x + 28.0 - ESP.x, "cor": ERA_COR.get(era, COR_TRAVADA), "nome": nome_era, "era": era})
		x += 28.0 + 24.0
	var alto := 32 + CABECALHO + maior * (NO.y + ESP.y) - ESP.y
	for f in _faixas:
		f.rect = Rect2(Vector2(f.x0, 8), Vector2(f.x1 - f.x0, alto - 8))
	_arvore.custom_minimum_size = Vector2(x, alto)
	_arvore.size = _arvore.custom_minimum_size
	_aplicar_zoom()


func _media(id: String, linha: Dictionary) -> float:
	var req: Array = _no(id).get("requer", [])
	if req.is_empty():
		return float(_ids().find(id))
	var s := 0.0
	for r in req:
		s += float(linha.get(r, 0))
	return s / req.size()


func _montar_arvore() -> void:
	for c in _arvore.get_children():
		c.queue_free()
	_nos.clear()
	_layout()
	for f in _faixas:                                             # título de cada era no alto da faixa
		var t := Label.new()
		var n := 0
		for id in _pos:
			if _no(id).get("era", "") == f.era:
				n += 1
		t.text = "%s  ·  %d tecnologias" % [f.nome, n]
		t.add_theme_font_size_override("font_size", 20)
		t.add_theme_color_override("font_color", (f.cor as Color).lightened(0.35))
		t.position = Vector2(f.rect.position.x + 26.0, f.rect.position.y + 10.0)
		_arvore.add_child(t)
	for id in _pos:
		var b := _botao_no(id)
		b.position = (_pos[id] as Rect2).position
		_arvore.add_child(b)
		_nos[id] = b
	_arvore.queue_redraw()


## Botão de um nó da árvore (placa na cor da situação; em desenvolvimento: cinza escuro com o selo, clica só para
## ver o detalhe).
func _botao_no(id: String) -> Button:
	var pq: Dictionary = _no(id)
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.size = NO
	b.custom_minimum_size = NO
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.icon = _icone_da(id)
	b.expand_icon = false
	b.add_theme_constant_override("icon_max_width", 56)
	b.text = "%s\n%s" % [pq.get("nome", id), _situacao(id)]
	b.add_theme_font_size_override("font_size", 16)
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	# placa em relevo com moldura na cor da situação (a mesma da barra de construção); escolhida = âmbar
	var cor := Tema.cor("destaque") if _sel == id else _cor(id)
	if _em_dev(id):                                # cinza escuro + selo; escolhida = moldura âmbar apagada
		Tema.botao_desenvolvimento(b, 12)
		if _sel == id:
			b.add_theme_stylebox_override("normal", Tema.botao_cor_estilo(Tema.cor("destaque").darkened(0.45)))
			b.add_theme_stylebox_override("hover", Tema.botao_cor_estilo(Tema.cor("destaque").darkened(0.45)))
	else:
		b.add_theme_stylebox_override("normal", Tema.botao_cor_estilo(cor))
		b.add_theme_stylebox_override("hover", Tema.botao_cor_estilo(cor.lightened(0.18)))
		b.add_theme_stylebox_override("pressed", Tema.botao_cor_estilo(cor.lightened(0.3)))
		b.add_theme_stylebox_override("hover_pressed", Tema.botao_cor_estilo(cor.lightened(0.3)))
	b.pressed.connect(RolagemToque.so_clique(func():
		Som.tocar("clique")
		_sel = id
		_atualizar()))
	return b


func _desenhar_linhas() -> void:
	var ci := _arvore.get_canvas_item()
	for f in _faixas:                                             # faixas das eras: chapa com rebites, tinta da era
		var c: Color = f.cor
		var r: Rect2 = f.rect
		Tema.chapa_estilo().draw(ci, r)
		_arvore.draw_rect(r.grow(-6.0), Color(c, 0.07))
		var cab := Rect2(r.position + Vector2(10, 8), Vector2(r.size.x - 20, CABECALHO - 12))
		_arvore.draw_rect(cab, Color(c.darkened(0.55), 0.85))
		_arvore.draw_texture_rect(Tema.listra(), Rect2(cab.position.x, cab.end.y, cab.size.x, 7), true)   # listras sob o título
		_arvore.draw_rect(Rect2(cab.position, Vector2(6, cab.size.y)), c)
	for id in _pos:
		var r: Rect2 = _pos[id]
		for req in _no(id).get("requer", []):
			if not _pos.has(req):
				continue
			var rr: Rect2 = _pos[req]
			var a := Vector2(rr.end.x, rr.get_center().y)
			var b := Vector2(r.position.x, r.get_center().y)
			# cada ligação dobra numa altura própria do corredor (pelo nó de destino): troncos não se sobrepõem
			var lado := float(int(r.position.y / (NO.y + ESP.y)) % 4) / 3.0
			var mx := a.x + ESP.x * (0.25 + 0.5 * lado)
			var cor := COR_FEITA if pesquisa.concluidas.has(req) else COR_TRAVADA
			if _em_dev(id):
				cor = Color(0.34, 0.34, 0.36, 0.5)
			_arvore.draw_polyline(PackedVector2Array([a, Vector2(mx, a.y), Vector2(mx, b.y), b]), cor, 3.0, true)
			_arvore.draw_circle(b, 5.0, cor)


func _cor(id: String) -> Color:
	if _em_dev(id):
		return Tema.COR_DESENVOLVIMENTO.lightened(0.25)
	if pesquisa.ativa == id:
		return BarraConstrucao.COR_DESTAQUE
	if pesquisa.concluidas.has(id):
		return COR_FEITA
	if pesquisa.disponivel(id):
		return Tema.cor("pesquisa")
	return COR_TRAVADA


## Custo da árvore em texto curto: "básico 30 + automação 30".
func _custo_texto(pq: Dictionary) -> String:
	var partes: Array[String] = []
	for c in pq.get("pacotes", []):
		partes.append("%s %d" % [c[0], int(c[1])])
	return " + ".join(partes)


func _situacao(id: String) -> String:
	var pq: Dictionary = _no(id)
	var tipo: String = (TIPOS.get(pq.get("tipo", ""), [""]) as Array)[0]
	if _em_dev(id):
		return tipo + " " + ("objetivo final" if pq.get("objetivo", false) else Tema.TEXTO_DESENVOLVIMENTO.to_lower())
	return tipo + " " + _situacao_jogavel(id, pq)


func _situacao_jogavel(id: String, pq: Dictionary) -> String:
	if pesquisa.concluidas.has(id):
		return "✓ concluída"
	var n := pesquisa.unidades(id)
	var nt := pesquisa.tipos(id).size()
	var custo := "%d pacotes" % n if nt == 1 else "%d × %d tipos" % [n, nt]
	if pesquisa.infinita(id):
		custo = "nível %d · %s" % [pesquisa.nivel(id) + 1, custo]
	if pesquisa.ativa == id:
		return "pesquisando %d/%d" % [pesquisa.feitos, n]
	if pesquisa.disponivel(id):
		return custo
	return "🔒 " + custo


## Ícone do nó: a primeira peça que libera; sem peça, o primeiro item das receitas.
func _icone_da(id: String) -> Texture2D:
	var pq: Dictionary = _no(id)
	if _em_breve(id):
		return null
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
	if _sel == "" or not _no(_sel).size():
		var l := Label.new()
		l.text = "Toque numa pesquisa da árvore.\n\nO laboratório (com energia) gasta pacotes de pesquisa: cada unidade gasta 1 pacote de cada tipo pedido. A montadora faz o pacote básico com 1 cristal lapidado + 1 engrenagem; um braço leva os pacotes ao laboratório."
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.add_theme_font_size_override("font_size", 15)
		_det.add_child(l)
		return
	var pq: Dictionary = _no(_sel)
	var nome := Label.new()
	nome.text = pq.get("nome", _sel)
	nome.add_theme_font_size_override("font_size", 22)
	nome.add_theme_color_override("font_color", _cor(_sel).lightened(0.2))
	nome.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_det.add_child(nome)
	var era := Label.new()
	for e in pesquisa.eras():
		if e.id == pq.get("era", ""):
			era.text = e.nome
	era.add_theme_font_size_override("font_size", 14)
	era.add_theme_color_override("font_color", (ERA_COR.get(pq.get("era", ""), COR_TRAVADA) as Color).lightened(0.3))
	_det.add_child(era)
	var tp := Label.new()
	var tipo_rot: Array = TIPOS.get(pq.get("tipo", ""), ["", ""])
	tp.text = "%s  %s" % [tipo_rot[0], tipo_rot[1]]
	tp.add_theme_font_size_override("font_size", 14)
	tp.add_theme_color_override("font_color", Tema.cor("info"))
	_det.add_child(tp)
	if _em_breve(_sel):
		_detalhe_em_breve(pq)
		return
	var custo := HBoxContainer.new()
	custo.add_theme_constant_override("separation", 8)
	for tp_pac in pesquisa.tipos(_sel):                            # uma casa por tipo de pacote
		custo.add_child(Casa.nova(_tex_item(tp_pac), str(pesquisa.unidades(_sel)), "pacote " + Pesquisa.nome_tipo(tp_pac)))
	var cl := Label.new()
	cl.text = "%s\n%s s por unidade no laboratório" % [pesquisa.custo_texto(_sel), String.num(float(pq.get("tempo", 5)), 1).trim_suffix(".0")]
	cl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cl.add_theme_font_size_override("font_size", 14)
	custo.add_child(cl)
	_det.add_child(custo)
	var faltam_pacotes: Array[String] = []
	for t in pesquisa.tipos(_sel):
		if not Registro.itens.has(t):
			faltam_pacotes.append(Pesquisa.nome_tipo(t))
	if not faltam_pacotes.is_empty():                             # depende de pacote que ainda é "em breve"
		var fl := Label.new()
		fl.text = "Pacote %s: em desenvolvimento (a receita vem numa pesquisa que ainda não está no jogo)." % ", ".join(faltam_pacotes)
		fl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		fl.add_theme_font_size_override("font_size", 14)
		fl.add_theme_color_override("font_color", Tema.cor("info"))
		_det.add_child(fl)
	if pesquisa.infinita(_sel):                                   # infinita: nível feito e o próximo custo
		var nl := Label.new()
		nl.text = "Nível feito: %d · o próximo custa ×%s" % [pesquisa.nivel(_sel), String.num(Pesquisa.CUSTO_NIVEL, 1)]
		nl.add_theme_font_size_override("font_size", 14)
		nl.add_theme_color_override("font_color", Tema.cor("info"))
		_det.add_child(nl)
	if not pq.get("bonus", {}).is_empty():                        # melhoria: diz o efeito, não há casas
		var ml := Label.new()
		ml.text = "Melhora"
		ml.add_theme_color_override("font_color", Tema.cor("titulo"))
		_det.add_child(ml)
		var mt := Label.new()
		mt.text = str(pq.get("texto", ""))
		mt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		mt.add_theme_font_size_override("font_size", 14)
		_det.add_child(mt)
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
	ln.text = ", ".join(nomes) if not nomes.is_empty() else str(pq.get("texto", "—"))   # ex.: camada nova da visão
	if nomes.is_empty() and not pq.get("bonus", {}).is_empty():   # só melhora: sem seção "Libera" vazia
		tl.visible = false
		casas.visible = false
		ln.visible = false
	ln.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ln.add_theme_font_size_override("font_size", 14)
	_det.add_child(ln)
	var req: Array = pq.get("requer", [])
	if not req.is_empty():
		var rl := Label.new()
		var partes: Array[String] = []
		for r in req:
			partes.append(("✓ " if pesquisa.concluidas.has(r) else "✗ ") + _nome(r))
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
		b.text = "Pesquisando… %d/%d" % [pesquisa.feitos, pesquisa.unidades(_sel)]
		if pesquisa.infinita(_sel):
			b.text = "Nível %d: %d/%d (segue sozinha)" % [pesquisa.nivel(_sel) + 1, pesquisa.feitos, pesquisa.unidades(_sel)]
		b.disabled = true
	elif _em_dev(_sel):                                           # travada por algo que ainda não está no jogo
		b.text = Tema.TEXTO_DESENVOLVIMENTO
		b.disabled = true
		Tema.botao_desenvolvimento(b, 12)
		var dl := Label.new()
		dl.text = "%s: %s." % [Tema.TEXTO_DESENVOLVIMENTO, pesquisa.motivo_desenvolvimento(_sel)]
		dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		dl.add_theme_font_size_override("font_size", 14)
		dl.add_theme_color_override("font_color", Tema.AMARELO.lightened(0.25))
		_det.add_child(dl)
	elif pesquisa.disponivel(_sel):
		b.text = "Pesquisar nível %d" % (pesquisa.nivel(_sel) + 1) if pesquisa.infinita(_sel) else "Pesquisar"
		var id := _sel
		b.pressed.connect(RolagemToque.so_clique(func():
			Som.tocar("clique")
			pesquisa.escolher(id)
			_atualizar()))
	else:
		b.text = "Termine antes o que falta"
		b.disabled = true
	_det.add_child(b)


## Pesquisa que ainda não existe no jogo: custo planejado, o que vai liberar, o que precisa antes.
func _detalhe_em_breve(pq: Dictionary) -> void:
	var linhas: Array[String] = []
	linhas.append("Custo planejado: " + _custo_texto(pq) + " pacotes" if not pq.get("pacotes", []).is_empty() else "Sem pacotes: só as colônias produzem.")
	if pq.has("tempo"):
		linhas.append("%s s por pacote no laboratório" % String.num(float(pq.tempo), 1).trim_suffix(".0"))
	var l := Label.new()
	l.text = "\n".join(linhas)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", 14)
	_det.add_child(l)
	var tl := Label.new()
	tl.text = "Vai liberar"
	tl.add_theme_color_override("font_color", Tema.cor("titulo"))
	_det.add_child(tl)
	var lib := Label.new()
	lib.text = str(pq.get("libera", "—"))
	lib.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lib.add_theme_font_size_override("font_size", 14)
	_det.add_child(lib)
	var req: Array = pq.get("requer", [])
	if not req.is_empty():
		var rl := Label.new()
		var partes: Array[String] = []
		for r in req:
			partes.append(("✓ " if pesquisa.concluidas.has(r) else "✗ ") + _nome(r))
		rl.text = "Precisa de: " + ", ".join(partes)
		rl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		rl.add_theme_font_size_override("font_size", 14)
		_det.add_child(rl)
	var b := Button.new()
	b.custom_minimum_size = Vector2(0, 56)
	b.focus_mode = Control.FOCUS_NONE
	b.text = "★ Objetivo final — em desenvolvimento" if pq.get("objetivo", false) else Tema.TEXTO_DESENVOLVIMENTO + ": ainda não está no jogo"
	b.disabled = true
	Tema.botao_desenvolvimento(b, 12)
	_det.add_child(b)
