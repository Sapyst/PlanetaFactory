class_name Tema
## Tema único da interface (barra, menus, painéis) com cara de fábrica: chapas de metal grafite gastas, borda
## chanfrada (luz em cima, sombra embaixo), rebites nos cantos, filete de cobre e listras de perigo amarelo-sujo
## e preto nos destaques; cores por situação e por tipo (COR, CORES_CATEGORIA). As texturas são geradas aqui por código (sem imagem externa) e fatiadas em 9 partes.

const AMARELO := Color(0.80, 0.62, 0.13)
const PRETO := Color(0.07, 0.07, 0.075)

## Paleta por situação e por tipo (nada de uma cor só para tudo). Quem desenha interface pede pela função:
## Tema.cor("pesquisa"), Tema.cor_categoria("Energia")...
const COR := {
	"titulo": Color(0.93, 0.82, 0.58),      # latão claro: títulos e cabeçalhos
	"texto": Color(0.88, 0.87, 0.83),
	"info": Color(0.70, 0.74, 0.78),        # aço: textos de apoio, status
	"filete": Color(0.55, 0.45, 0.30),      # cobre gasto: filete das chapas
	"destaque": Color(0.96, 0.74, 0.24),    # âmbar: selecionado, construir
	"perigo": Color(0.92, 0.36, 0.28),      # vermelho: remover, ataque, falta
	"sucesso": Color(0.50, 0.85, 0.42),     # verde: pronto, concluído
	"energia": Color(1.00, 0.82, 0.25),     # ouro: energia, raio
	"pesquisa": Color(0.68, 0.60, 0.98),    # violeta: pesquisa disponível
	"agua": Color(0.42, 0.72, 0.96),        # azul: fluidos, vento, recursos
	"travado": Color(0.45, 0.47, 0.50),     # cinza: bloqueado
}
const CORES_CATEGORIA := {
	"Esteiras": Color(0.96, 0.74, 0.24), "Braços": Color(0.78, 0.80, 0.84), "Canos": Color(0.42, 0.72, 0.96),
	"Produção": Color(0.96, 0.56, 0.26), "Limpeza": Color(0.50, 0.85, 0.42), "Energia": Color(1.00, 0.86, 0.30),
	"Defesa": Color(0.92, 0.36, 0.28), "Trilhos": Color(0.78, 0.52, 0.34),
}


static func cor(funcao: String) -> Color:
	return COR.get(funcao, COR.texto)


static func cor_categoria(nome: String) -> Color:
	return CORES_CATEGORIA.get(nome, COR.texto)

static var _cache: Dictionary = {}


static func criar() -> Theme:
	var t := Theme.new()
	t.default_font_size = 18
	t.set_stylebox("panel", "PanelContainer", chapa_estilo())
	t.set_stylebox("normal", "Button", botao_estilo("normal"))
	t.set_stylebox("hover", "Button", botao_estilo("hover"))
	t.set_stylebox("pressed", "Button", botao_estilo("apertado"))
	t.set_stylebox("hover_pressed", "Button", botao_estilo("apertado"))
	t.set_stylebox("disabled", "Button", botao_estilo("desligado"))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", Color(0.90, 0.91, 0.94))
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", Color.WHITE)
	t.set_color("font_disabled_color", "Button", Color(0.45, 0.46, 0.5))
	t.set_constant("icon_max_width", "Button", 64)
	t.set_stylebox("slider", "HSlider", caixa(Color(0.12, 0.12, 0.15), Color(0.3, 0.32, 0.38), 6, 4))
	t.set_color("font_color", "CheckButton", Color(0.9, 0.91, 0.94))
	t.set_stylebox("background", "ProgressBar", caixa(Color(0.02, 0.025, 0.03), Color(0.25, 0.27, 0.3), 3, 0))
	t.set_stylebox("fill", "ProgressBar", caixa(cor("destaque").darkened(0.2), cor("destaque"), 3, 0))
	return t


static func caixa(fundo: Color, borda: Color, raio: int, margem: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = fundo
	s.border_color = borda
	s.set_border_width_all(2)
	s.set_corner_radius_all(raio)
	s.set_content_margin_all(margem)
	return s


# ------------------------------------------------------------------ estilos de textura
## Painel: chapa grafite com rebites (margem de conteúdo para não encostar nos rebites).
static func chapa_estilo() -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex("chapa", func(): return _chapa(96, true))
	s.set_texture_margin_all(18)
	s.set_content_margin_all(14)
	return s


## A mesma chapa com rebites, com margens curtas (painéis pequenos, como o estoque do núcleo).
static func chapa_compacta() -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex("chapa", func(): return _chapa(96, true))
	s.set_texture_margin_all(12)
	s.set_content_margin_all(8)
	return s


static func botao_estilo(estado: String) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex("botao_" + estado, func(): return _placa(48, estado))
	s.set_texture_margin_all(8)
	s.set_content_margin_all(8)
	return s


## Botão destacado (ligado, selecionado): a mesma placa, com miolo puxado para a cor e moldura dela por dentro.
static func botao_cor_estilo(c: Color) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex("botao_cor_" + c.to_html(), func(): return _placa_cor(48, c))
	s.set_texture_margin_all(8)
	s.set_content_margin_all(8)
	return s


static func _placa_cor(n: int, cor_d: Color) -> Image:
	var img := _placa(n, "normal")
	for y in n:
		for x in n:
			var d := mini(mini(x, y), mini(n - 1 - x, n - 1 - y))
			var c := img.get_pixel(x, y)
			if d >= 3 and d <= 5:
				c = cor_d.darkened(0.1 + 0.15 * _ruido(x, y, 29))
			elif d > 5:
				c = c.lerp(cor_d.darkened(0.72), 0.85)
			img.set_pixel(x, y, Color(c, 0.97))
	return img


## Moldura de listras de perigo (faixa do modo construção, alertas): miolo escuro, borda listrada.
static func perigo_estilo(espessura := 7) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex("moldura_perigo_%d" % espessura, func(): return _moldura_perigo(64, espessura))
	s.set_texture_margin_all(espessura + 3)
	s.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE      # listras repetem, não esticam
	s.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	s.set_content_margin_all(espessura + 8)
	return s


## Botão listrado (Sair, ações perigosas).
static func botao_perigo_estilo(apertado := false) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex("botao_perigo_%s" % apertado, func(): return _botao_perigo(48, apertado))
	s.set_texture_margin_all(11)
	s.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	s.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	s.set_content_margin_all(14)
	return s


## O que ainda não entrou no jogo (pesquisa "em breve" ou travada por ela, peça sem modelo): placa cinza escuro e
## selo "Em desenvolvimento".
const COR_DESENVOLVIMENTO := Color(0.20, 0.20, 0.22)
const TEXTO_DESENVOLVIMENTO := "Em desenvolvimento"


## Selo por cima de um botão (nó da pesquisa, peça da barra): véu cinza escuro no botão inteiro e a etiqueta com
## moldura de listras no canto de baixo. Não pega toque: quem decide se o botão clica é ele.
static func selo_desenvolvimento(alvo: Control, tam_fonte := 12) -> Control:
	var veu := ColorRect.new()
	veu.name = "SeloDesenvolvimento"
	veu.color = Color(0.05, 0.05, 0.06, 0.58)
	veu.mouse_filter = Control.MOUSE_FILTER_IGNORE
	veu.set_anchors_preset(Control.PRESET_FULL_RECT)
	var et := PanelContainer.new()
	var caixa_et := caixa(Color(0.09, 0.09, 0.10, 0.96), AMARELO.darkened(0.2), 3, 0)
	caixa_et.content_margin_left = 7
	caixa_et.content_margin_right = 7
	caixa_et.content_margin_top = 1
	caixa_et.content_margin_bottom = 1
	et.add_theme_stylebox_override("panel", caixa_et)
	et.mouse_filter = Control.MOUSE_FILTER_IGNORE
	et.anchor_left = 1.0
	et.anchor_right = 1.0
	et.anchor_top = 1.0
	et.anchor_bottom = 1.0
	et.offset_right = -7.0
	et.offset_bottom = -6.0
	et.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	et.grow_vertical = Control.GROW_DIRECTION_BEGIN
	var l := Label.new()
	l.text = TEXTO_DESENVOLVIMENTO.to_upper()
	l.add_theme_font_size_override("font_size", tam_fonte)
	l.add_theme_color_override("font_color", AMARELO.lightened(0.25))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	et.add_child(l)
	veu.add_child(et)
	alvo.add_child(veu)
	return veu


## Botão em desenvolvimento: placa cinza escuro em todos os estados (inclusive desligado), texto apagado e o selo.
static func botao_desenvolvimento(b: Button, tam_fonte := 12) -> void:
	var st := botao_cor_estilo(COR_DESENVOLVIMENTO)
	for k in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
		b.add_theme_stylebox_override(k, st)
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_disabled_color"]:
		b.add_theme_color_override(k, Color(0.55, 0.56, 0.58))
	b.tooltip_text = TEXTO_DESENVOLVIMENTO + ": ainda não está no jogo"
	if b.get_node_or_null("SeloDesenvolvimento") == null:
		selo_desenvolvimento(b, tam_fonte)


## Barra listrada para pôr sob títulos (TextureRect em ladrilho).
static func listra() -> Texture2D:
	return _tex("listra", func(): return _listras(64, 10, 0.0))


static func faixa_titulo() -> TextureRect:
	var r := TextureRect.new()
	r.texture = listra()
	r.stretch_mode = TextureRect.STRETCH_TILE
	r.custom_minimum_size = Vector2(0, 7)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


static func _tex(chave: String, fazer: Callable) -> Texture2D:
	if not _cache.has(chave):
		_cache[chave] = ImageTexture.create_from_image(fazer.call())
	return _cache[chave]


# ------------------------------------------------------------------ desenho das texturas
static func _ruido(x: int, y: int, s: int) -> float:
	var h := (x * 374761393 + y * 668265263 + s * 2147483647) & 0x7fffffff
	h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
	return float(h % 1000) / 1000.0


## Chapa: grafite com ruído fino e manchas de sujeira, chanfro de 3 px, contorno escuro, filete ciano e rebites.
static func _chapa(n: int, rebites: bool) -> Image:
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var base := Color(0.075, 0.085, 0.10)
	for y in n:
		for x in n:
			var c := base
			c = c.lightened(0.04 * _ruido(x, y, 1) - 0.02)
			# sujeira: manchas largas mais escuras perto das bordas
			var borda := minf(minf(x, y), minf(n - 1 - x, n - 1 - y)) / float(n) * 2.0
			var mancha := _ruido(x / 6, y / 6, 7)
			c = c.darkened(0.18 * mancha * (1.0 - borda))
			var a := 0.94
			if x == 0 or y == 0 or x == n - 1 or y == n - 1:
				c = Color(0.01, 0.01, 0.012)
				a = 1.0
			elif x <= 3 or y <= 3:
				c = c.lightened(0.22 - 0.04 * minf(x, y))           # luz de cima/esquerda
			elif x >= n - 4 or y >= n - 4:
				c = c.darkened(0.45)                               # sombra de baixo/direita
			elif x == 5 or y == 5 or x == n - 6 or y == n - 6:
				c = c.lerp(cor("filete"), 0.35)                    # filete de cobre gasto
			img.set_pixel(x, y, Color(c, a))
	if rebites:
		for cx in [9, n - 10]:
			for cy in [9, n - 10]:
				_rebite(img, cx, cy)
	return img


static func _rebite(img: Image, cx: int, cy: int) -> void:
	for y in range(cy - 3, cy + 4):
		for x in range(cx - 3, cx + 4):
			var d := Vector2(x - cx, y - cy).length()
			if d > 3.2:
				continue
			var luz := clampf(1.0 - Vector2(x - cx + 1.2, y - cy + 1.2).length() / 3.5, 0.0, 1.0)
			var c := Color(0.22, 0.24, 0.27).lerp(Color(0.62, 0.64, 0.68), luz)
			if d > 2.4:
				c = Color(0.03, 0.03, 0.035)
			img.set_pixel(x, y, c)


## Placa de botão: relevo (normal), mais clara (hover), afundada com brilho ciano (apertado), apagada (desligado).
static func _placa(n: int, estado: String) -> Image:
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var base: Color = {"normal": Color(0.13, 0.145, 0.165), "hover": Color(0.17, 0.19, 0.215),
			"apertado": Color(0.18, 0.14, 0.07), "desligado": Color(0.10, 0.10, 0.11)}[estado]
	var afunda := estado == "apertado"
	for y in n:
		for x in n:
			var c := base.lightened(0.05 * _ruido(x, y, 3) - 0.025)
			if x == 0 or y == 0 or x == n - 1 or y == n - 1:
				c = Color(0.01, 0.01, 0.012)
			elif x <= 2 or y <= 2:
				c = c.darkened(0.4) if afunda else c.lightened(0.18)
			elif x >= n - 3 or y >= n - 3:
				c = c.lightened(0.12) if afunda else c.darkened(0.4)
			if afunda and (x == 4 or y == 4 or x == n - 5 or y == n - 5) and x > 3 and y > 3 and x < n - 4 and y < n - 4:
				c = c.lerp(cor("destaque"), 0.55)
			img.set_pixel(x, y, Color(c, 0.97))
	return img


## Listras de perigo diagonais, gastas (manchas e arranhões tiram tinta).
static func _listras(larg: int, alt: int, fase: float) -> Image:
	var img := Image.create(larg, alt, false, Image.FORMAT_RGBA8)
	for y in alt:
		for x in larg:
			img.set_pixel(x, y, _cor_listra(x, y, fase))
	return img


static func _cor_listra(x: int, y: int, fase: float) -> Color:
	var amarela := fposmod(float(x + y) + fase, 16.0) < 8.0
	var c := AMARELO if amarela else PRETO
	var sujo := _ruido(x / 3, y / 3, 11)
	c = c.darkened(0.35 * sujo)
	if amarela and _ruido(x, y, 13) > 0.93:
		c = PRETO.lightened(0.1)                                   # tinta arrancada
	return c


static func _moldura_perigo(n: int, esp: int) -> Image:
	var img := _chapa(n, false)
	for y in n:
		for x in n:
			var d := mini(mini(x, y), mini(n - 1 - x, n - 1 - y))
			if d >= 1 and d <= esp:
				img.set_pixel(x, y, _cor_listra(x, y, 0.0))
			elif d == esp + 1:
				img.set_pixel(x, y, Color(0.02, 0.02, 0.02))
	return img


## Botão de perigo (Sair): placa de metal em relevo, gasta (arranhões e cantos sem tinta), com uma moldura fina de
## listras por dentro do chanfro e miolo escuro para o texto — parece botão, não uma faixa.
static func _botao_perigo(n: int, apertado: bool) -> Image:
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var base := Color(0.16, 0.15, 0.14) if not apertado else Color(0.11, 0.10, 0.09)
	for y in n:
		for x in n:
			var d := mini(mini(x, y), mini(n - 1 - x, n - 1 - y))
			var c := base.lightened(0.05 * _ruido(x, y, 5) - 0.025)
			if d == 0:
				c = Color(0.01, 0.01, 0.012)
			elif d <= 3:
				var luz := (x <= 3 or y <= 3) and not (x >= n - 4 or y >= n - 4)
				if apertado:
					luz = not luz
				c = c.lightened(0.25) if luz else c.darkened(0.5)
				if _ruido(x, y, 17) > 0.86:
					c = c.lerp(Color(0.5, 0.48, 0.44), 0.6)         # canto sem tinta, metal à mostra
			elif d <= 8:
				c = _cor_listra(x, y, 2.0).darkened(0.15 if not apertado else 0.35)
			elif d == 9:
				c = Color(0.02, 0.02, 0.02)
			else:
				c = c.darkened(0.15 * _ruido(x / 4, y / 4, 19))
				if _ruido(x, y * 3, 23) > 0.985:
					c = c.lightened(0.25)                           # arranhão
			img.set_pixel(x, y, c)
	return img
