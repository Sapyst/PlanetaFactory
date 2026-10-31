class_name PainelRecursos
extends PanelContainer
## Estoque do núcleo: casas pequenas com ícone + número (nome e quantidade exata na dica do mouse), em coluna ou em
## linha (Configurações). A alça ▾/▴ alterna entre tudo o que há no núcleo e só os principais. Quem posiciona e diz
## quanto espaço há é a BarraConstrucao, para não cobrir o resto da interface.

const PRINCIPAIS := ["placa_ferro", "placa_cobre", "engrenagem", "pedra"]
const LADO := 20.0                     ## ícone
const LARGURA_CASA := 58.0             ## ícone + até 5 caracteres ("1,2M")
const ALTURA_CASA := 22.0
const SEPARACAO := 2

var horizontal := false
var resumo := false
var mudou_resumo: Callable             ## chamada quando o jogador toca na alça (grava a escolha)
var _grade: GridContainer
var _alca: Button
var _casas: Dictionary = {}            ## item → {no, numero}
var _assinatura := ""
var _estoque: Dictionary = {}
var _limite := -1.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	add_theme_stylebox_override("panel", Tema.chapa_compacta())
	_grade = GridContainer.new()
	_grade.add_theme_constant_override("h_separation", SEPARACAO + 2)
	_grade.add_theme_constant_override("v_separation", SEPARACAO)
	add_child(_grade)
	_alca = Button.new()
	_alca.focus_mode = Control.FOCUS_NONE
	_alca.custom_minimum_size = Vector2(LARGURA_CASA, ALTURA_CASA)
	_alca.add_theme_font_size_override("font_size", Tema.n("f_alca"))
	_alca.add_theme_color_override("font_color", Tema.cor("titulo"))
	for k in ["normal", "hover", "pressed"]:
		_alca.add_theme_stylebox_override(k, Tema.caixa(Color(0.10, 0.10, 0.11, 0.95) if k != "hover" else Color(0.17, 0.16, 0.14, 0.95), Color(Tema.COR.filete, 0.8), 3, 0))
	_alca.pressed.connect(func():
		resumo = not resumo
		_assinatura = ""
		atualizar(_estoque)
		if mudou_resumo.is_valid():
			mudou_resumo.call(resumo))
	_grade.add_child(_alca)
	visible = false


## Itens mostrados, nesta ordem: os principais e depois os outros, na ordem de dados/itens.json (recursos, peças,
## avançados). Só o que há no núcleo; no resumo, só os principais, mesmo zerados.
static func itens_visiveis(estoque: Dictionary, so_principais: bool) -> Array:
	var out: Array = PRINCIPAIS.duplicate()
	if so_principais:
		return out
	out = out.filter(func(k): return int(estoque.get(k, 0)) > 0)
	for k in Registro.itens:
		if not k in PRINCIPAIS and int(estoque.get(k, 0)) > 0:
			out.append(k)
	for k in estoque:                  # item fora do itens.json (save antigo): não some
		if not out.has(k) and not Registro.itens.has(k) and int(estoque[k]) > 0:
			out.append(k)
	return out


## 1234 → "1234"; 12345 → "12k"; 1234567 → "1,2M" (cabe na casa).
static func numero_curto(n: int) -> String:
	if n < 10000:
		return str(n)
	if n < 1000000:
		return "%dk" % (n / 1000)
	if n < 10000000:
		return ("%.1fM" % (n / 1000000.0)).replace(".", ",")
	return "%dM" % (n / 1000000)


## Colunas da grade para `n` casas: em coluna, as que precisar para caber em `limite` de altura; em linha, as que
## couberem em `limite` de largura. Sem limite (<= 0), uma coluna / uma linha.
static func colunas_para(n: int, em_linha: bool, limite: float) -> int:
	if n <= 0:
		return 1
	if em_linha:
		var cabem := int((limite + SEPARACAO) / (LARGURA_CASA + SEPARACAO + 2)) if limite > 0.0 else n
		return clampi(cabem, 1, n)
	var linhas := int((limite + SEPARACAO) / (ALTURA_CASA + SEPARACAO)) if limite > 0.0 else n
	return ceili(float(n) / maxi(linhas, 1))


func atualizar(estoque: Dictionary) -> void:
	_estoque = estoque
	var lista := itens_visiveis(estoque, resumo)
	var assin := "%s" % [lista]
	if assin != _assinatura:
		_assinatura = assin
		_alca.text = "▾ tudo" if resumo else "▴ menos"
		_alca.tooltip_text = "Mostrar tudo o que há no núcleo" if resumo else "Mostrar só os principais"
		for k in _casas.keys():
			if not lista.has(k):
				_grade.remove_child(_casas[k].no)      # agora: a contagem de colunas vem logo abaixo
				_casas[k].no.queue_free()
				_casas.erase(k)
		for k in lista:
			if not _casas.has(k):
				_casas[k] = _casa(k)
		for i in lista.size():
			_grade.move_child(_casas[lista[i]].no, i)
		_grade.move_child(_alca, -1)
		_limite = -1.0
	for k in lista:
		var q := int(estoque.get(k, 0))
		_casas[k].numero.text = numero_curto(q)
		_casas[k].numero.modulate.a = 1.0 if q > 0 else 0.45
		_casas[k].no.tooltip_text = "%s: %d" % [Registro.itens.get(k, {}).get("nome", k), q]
	visible = true


## Reparte as casas para o espaço disponível (altura em coluna, largura em linha).
func organizar(limite: float) -> void:
	var margens := get_theme_stylebox("panel").get_minimum_size()
	var util := limite - (margens.x if horizontal else margens.y)
	if is_equal_approx(util, _limite) and _grade.get_meta("horizontal", false) == horizontal:
		return
	_limite = util
	_grade.set_meta("horizontal", horizontal)
	_grade.columns = colunas_para(_grade.get_child_count(), horizontal, util)
	size = get_combined_minimum_size()


func _casa(item: String) -> Dictionary:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 3)
	h.custom_minimum_size = Vector2(LARGURA_CASA, ALTURA_CASA)
	h.mouse_filter = Control.MOUSE_FILTER_STOP                # o que recebe a dica
	var fundo := PanelContainer.new()                          # encaixe afundado, como a Casa grande das máquinas
	var st := Tema.caixa(Color(0.025, 0.035, 0.045, 0.95), Color(0.33, 0.35, 0.38), 3, 0)
	st.set_border_width_all(1)
	fundo.add_theme_stylebox_override("panel", st)
	fundo.custom_minimum_size = Vector2(ALTURA_CASA, ALTURA_CASA)
	fundo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(fundo)
	var ic := TextureRect.new()
	ic.texture = TelaPesquisa._tex_item(item)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.custom_minimum_size = Vector2(LADO, LADO)
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fundo.add_child(ic)
	var n := Label.new()
	n.add_theme_font_size_override("font_size", Tema.n("f_recurso"))
	n.add_theme_color_override("font_color", Tema.cor("texto"))
	n.add_theme_color_override("font_outline_color", Color.BLACK)
	n.add_theme_constant_override("outline_size", 3)
	n.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(n)
	_grade.add_child(h)
	return {"no": h, "numero": n}
