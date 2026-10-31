class_name Tema
## Tema único da interface (barra, menus, painéis) com cara de fábrica: chapas de metal grafite gastas, borda
## chanfrada (luz em cima, sombra embaixo), rebites nos cantos, filete de cobre e listras de perigo amarelo-sujo
## e preto nos destaques; cores por situação e por tipo (COR, CORES_CATEGORIA). As texturas são geradas aqui por código (sem imagem externa) e fatiadas em 9 partes.
##
## Dois perfis, uma tabela só (MEDIDAS): celular (APK: alvos de dedo, como sempre foi) e PC (refinado: alvos de mouse, ícones
## e fontes menores, chapa fina). Quem desenha interface pede a medida: Tema.n("f_texto"), Tema.v("ferr_botao"), nunca um número nem um "if pc".

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

## Perfil de interface. Celular de verdade (APK) ou forçado com `-- celular`; o resto é PC. Os testes trocam à mão.
static var pc: bool = detectar_pc()


static func detectar_pc() -> bool:
	return not (OS.has_feature("mobile") or OS.has_feature("android") or OS.get_cmdline_user_args().has("celular"))


## chave → [celular, PC]. A coluna do celular são os números de sempre: não mudar sem testar no aparelho (test_perfil_interface.gd confere).
const MEDIDAS := {
	# fontes
	"f_base": [18, 14], "f_texto": [15, 13], "f_peq": [14, 12], "f_titulo": [19, 15], "f_ferr": [16, 13], "f_faixa": [17, 13], "f_sair": [19, 13],
	"f_casa": [15, 11], "f_seta": [28, 18], "f_selo": [12, 9], "f_salvando": [13, 11], "f_recurso": [13, 12],
	"f_tela": [24, 17], "f_no": [16, 12], "f_era": [20, 14], "f_det_nome": [22, 15], "f_zoom": [26, 15], "f_alca": [12, 11],
	"f_menu_titulo": [44, 30], "f_menu_botao": [20, 14], "f_pausa_titulo": [30, 20], "f_config_titulo": [26, 18],
	# chapa, placa e moldura (os números de textura escolhem entre a versão larga e a fina)
	"borda": [2, 1], "chapa_tex": [18, 8], "chapa_cont": [14, 6], "compacta_tex": [12, 8], "compacta_cont": [8, 4], "botao_tex": [8, 3], "botao_cont": [8, 4],
	"perigo_esp": [7, 3], "perigo_botao_tex": [11, 6], "perigo_botao_cont": [14, 7], "faixa_titulo_alt": [7, 3], "barra_alt": [12, 6],
	# barra de construção
	"sep": [8, 4], "seg_x": [12, 6], "seg_y": [10, 6], "ferr_botao": [Vector2(48, 48), Vector2(26, 25)], "ferr_sep": [4, 2], "largura_estreita": [1300, 1040],
	"peca_alt": [74, 40], "peca_icone": [58, 30], "peca_sep": [6, 2], "pecas_min": [250, 210], "pecas_max": [400, 290], "pecas_fator": [0.36, 0.22],
	"cat_larg": [72, 34], "cat_larg_estreita": [58, 34], "cat_alt_min": [40, 24], "cat_alt_max": [66, 32], "cat_sep": [6, 2], "icone_max": [64, 28],
	"acao_botao": [Vector2(96, 52), Vector2(70, 26)], "acao_x": [Vector2(56, 52), Vector2(26, 26)], "acao_sep": [6, 3],
	"sair_botao": [Vector2(112, 52), Vector2(70, 24)], "faixa_sep": [12, 6], "faixa_min": [260, 220], "faixa_max": [560, 440],
	"info_min": [220, 170], "info_max": [420, 330], "info_fator": [0.3, 0.22], "dica_min": [220, 200], "dica_max": [420, 380], "dica_fator": [0.36, 0.3],
	"info_esq": [16, 8], "info_dir": [18, 8], "info_raio": [10, 3], "info_cont": [8, 3],
	# painel de detalhe
	"det_inicial": [320, 250], "det_texto": [296, 226], "det_min": [270, 250], "det_max": [380, 310], "det_fator": [0.34, 0.2], "det_folga": [36, 24], "det_sep": [6, 3], "det_botao": [46, 26], "det_botoes_sep": [4, 2],
	"det_icone_botao": [46, 28], "det_icone_max": [34, 22], "det_fechar": [Vector2(48, 44), Vector2(22, 20)], "maq_icone": [84, 40], "casa": [60, 32],
	# tela de pesquisa
	"no": [Vector2(250, 92), Vector2(186, 50)], "no_esp": [Vector2(72, 18), Vector2(44, 8)], "cabecalho": [46, 26], "era_texto": [Vector2(26, 10), Vector2(12, 5)], "no_icone": [56, 30],
	"tela_margem": [12, 8], "tela_sep": [8, 4], "tela_corpo_sep": [10, 6], "tela_fechar": [Vector2(120, 52), Vector2(84, 24)], "tela_zoom": [Vector2(52, 52), Vector2(24, 24)],
	"lado_min": [250, 220], "lado_max": [360, 300], "lado_fator": [0.3, 0.2], "pesquisar_alt": [56, 30], "det_tela_sep": [8, 4], "casas_sep": [6, 3],
	"linha": [3.0, 2.0], "linha_ponta": [5.0, 3.0], "zoom_ref": [1700.0, 1100.0],
	# menus
	"pausa_botao": [Vector2(360, 54), Vector2(250, 30)], "menu_botao": [Vector2(420, 58), Vector2(300, 34)], "pausa_margem": [20, 10], "menu_margem": [22, 12], "menu_sep": [10, 5],
	"config_slider": [Vector2(320, 32), Vector2(280, 18)], "config_voltar": [52, 28], "config_folga": [190, 120],
}
## Por perfil, além de medida: o que muda de forma, não de tamanho (também só aqui).
const ESTILO_CELULAR := {"peca_duas_linhas": false, "atalhos": false, "painel_compacto": false, "fino": false}
const ESTILO_PC := {"peca_duas_linhas": true, "atalhos": true, "painel_compacto": true, "fino": true}


static func n(chave: String) -> int:
	return int(MEDIDAS[chave][1 if pc else 0])


static func f(chave: String) -> float:
	return float(MEDIDAS[chave][1 if pc else 0])


static func v(chave: String) -> Vector2:
	return MEDIDAS[chave][1 if pc else 0]


static func estilo(chave: String) -> bool:
	return bool((ESTILO_PC if pc else ESTILO_CELULAR)[chave])


## Texto de botão com o atalho à vista, onde há teclado.
static func com_atalho(texto: String, tecla: String) -> String:
	return "%s [%s]" % [texto, tecla] if estilo("atalhos") and tecla != "" else texto


static func criar() -> Theme:
	var t := Theme.new()
	t.default_font_size = n("f_base")
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
	t.set_constant("icon_max_width", "Button", n("icone_max"))
	t.set_stylebox("slider", "HSlider", caixa(Color(0.12, 0.12, 0.15), Color(0.3, 0.32, 0.38), 6, 4))
	t.set_color("font_color", "CheckButton", Color(0.9, 0.91, 0.94))
	t.set_stylebox("background", "ProgressBar", caixa(Color(0.02, 0.025, 0.03), Color(0.25, 0.27, 0.3), 3, 0))
	t.set_stylebox("fill", "ProgressBar", caixa(cor("destaque").darkened(0.2), cor("destaque"), 3, 0))
	if estilo("fino"):                      # lista, dica do mouse e seletor na mesma chapa fina (o celular segue com os de fábrica)
		for k in ["normal", "hover", "pressed", "disabled"]:
			t.set_stylebox(k, "OptionButton", botao_estilo({"pressed": "apertado", "disabled": "desligado"}.get(k, k)))
		var dica := caixa(Color(0.05, 0.055, 0.065, 0.97), Color(COR.filete, 0.9), 2, 7)
		t.set_stylebox("panel", "TooltipPanel", dica)
		t.set_font_size("font_size", "TooltipLabel", n("f_peq"))
		t.set_color("font_color", "TooltipLabel", COR.texto)
		t.set_stylebox("panel", "PopupMenu", dica)
		t.set_font_size("font_size", "PopupMenu", n("f_texto"))
		var trilho := caixa(Color(0.03, 0.035, 0.04, 0.8), Color(0.03, 0.035, 0.04, 0.8), 1, 0)
		trilho.set_border_width_all(0)
		trilho.content_margin_left = 5
		trilho.content_margin_right = 5
		trilho.content_margin_top = 5
		trilho.content_margin_bottom = 5
		var pega := caixa(Color(0.30, 0.31, 0.34), Color(0.30, 0.31, 0.34), 1, 0)
		pega.set_border_width_all(0)
		for bar in ["VScrollBar", "HScrollBar"]:
			t.set_stylebox("scroll", bar, trilho)
			t.set_stylebox("grabber", bar, pega)
			t.set_stylebox("grabber_highlight", bar, pega)
			t.set_stylebox("grabber_pressed", bar, pega)
	return t


static func caixa(fundo: Color, borda: Color, raio: int, margem: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = fundo
	s.border_color = borda
	s.set_border_width_all(n("borda"))
	s.set_corner_radius_all(mini(raio, 3) if estilo("fino") else raio)
	s.set_content_margin_all(ceili(margem * 0.6) if estilo("fino") else margem)
	return s


# ------------------------------------------------------------------ estilos de textura
## Painel: chapa grafite com rebites (margem de conteúdo para não encostar nos rebites).
static func chapa_estilo() -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex_chapa()
	s.set_texture_margin_all(n("chapa_tex"))
	s.set_content_margin_all(n("chapa_cont"))
	return s


## A mesma chapa com rebites, com margens curtas (painéis pequenos, como o estoque do núcleo).
static func chapa_compacta() -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = _tex_chapa()
	s.set_texture_margin_all(n("compacta_tex"))
	s.set_content_margin_all(n("compacta_cont"))
	return s


static func botao_estilo(estado: String) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	var fino := estilo("fino")
	s.texture = _tex("botao_fino_" + estado if fino else "botao_" + estado, func(): return _placa(20, estado, 1) if fino else _placa(48, estado))
	s.set_texture_margin_all(n("botao_tex"))
	s.set_content_margin_all(n("botao_cont"))
	return s


## Botão destacado (ligado, selecionado): a mesma placa, com miolo puxado para a cor e moldura dela por dentro.
static func botao_cor_estilo(c: Color) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	var fino := estilo("fino")
	s.texture = _tex(("botao_cor_fino_" if fino else "botao_cor_") + c.to_html(), func(): return _placa_cor(20, c, 1) if fino else _placa_cor(48, c))
	s.set_texture_margin_all(n("botao_tex"))
	s.set_content_margin_all(n("botao_cont"))
	return s


static func _placa_cor(lado: int, cor_d: Color, chanfro := 2) -> Image:
	var img := _placa(lado, "normal", chanfro)
	var fim_moldura := chanfro + 3 if chanfro >= 2 else chanfro + 1     # a fina: moldura de 1 px
	for y in lado:
		for x in lado:
			var d := mini(mini(x, y), mini(lado - 1 - x, lado - 1 - y))
			var c := img.get_pixel(x, y)
			if d > chanfro and d <= fim_moldura:
				c = cor_d.darkened(0.1 + 0.15 * _ruido(x, y, 29))
			elif d > fim_moldura:
				c = c.lerp(cor_d.darkened(0.72), 0.85)
			img.set_pixel(x, y, Color(c, 0.97))
	return img


## Moldura de listras de perigo (faixa do modo construção, alertas): miolo escuro, borda listrada.
static func perigo_estilo(espessura := -1) -> StyleBoxTexture:
	if espessura < 0:
		espessura = n("perigo_esp")
	var s := StyleBoxTexture.new()
	s.texture = _tex("moldura_perigo_%d" % espessura, func(): return _moldura_perigo(64, espessura))
	s.set_texture_margin_all(espessura + 3)
	s.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE      # listras repetem, não esticam
	s.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	s.set_content_margin_all(espessura + (4 if estilo("fino") else 8))
	return s


## Botão listrado (Sair, ações perigosas).
static func botao_perigo_estilo(apertado := false) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	var fino := estilo("fino")
	s.texture = _tex("botao_perigo_%s%s" % ["fino_" if fino else "", apertado], func(): return _botao_perigo(24, apertado, 1, 3) if fino else _botao_perigo(48, apertado))
	s.set_texture_margin_all(n("perigo_botao_tex"))
	s.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	s.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE
	s.set_content_margin_all(n("perigo_botao_cont"))
	return s


## O que ainda não entrou no jogo (pesquisa "em breve" ou travada por ela, peça sem modelo): placa cinza escuro e
## selo "Em desenvolvimento".
const COR_DESENVOLVIMENTO := Color(0.20, 0.20, 0.22)
const TEXTO_DESENVOLVIMENTO := "Em desenvolvimento"


## Selo por cima de um botão (nó da pesquisa, peça da barra): véu cinza escuro no botão inteiro e a etiqueta com
## moldura de listras no canto de baixo. Não pega toque: quem decide se o botão clica é ele.
static func selo_desenvolvimento(alvo: Control, tam_fonte := -1) -> Control:
	if tam_fonte < 0:
		tam_fonte = n("f_selo")
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
static func botao_desenvolvimento(b: Button, tam_fonte := -1) -> void:
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
	r.custom_minimum_size = Vector2(0, n("faixa_titulo_alt"))
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


static func _tex_chapa() -> Texture2D:
	return _tex("chapa_fina", func(): return _chapa(48, true, 1)) if estilo("fino") else _tex("chapa", func(): return _chapa(96, true))


static func _tex(chave: String, fazer: Callable) -> Texture2D:
	if not _cache.has(chave):
		_cache[chave] = ImageTexture.create_from_image(fazer.call())
	return _cache[chave]


# ------------------------------------------------------------------ desenho das texturas
static func _ruido(x: int, y: int, s: int) -> float:
	var h := (x * 374761393 + y * 668265263 + s * 2147483647) & 0x7fffffff
	h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
	return float(h % 1000) / 1000.0


## Chapa: grafite com ruído fino e manchas de sujeira, chanfro, contorno escuro, filete de cobre e rebites.
## chanfro 3 = a chapa grossa de sempre; 1 = a fina do PC (mesmo desenho, rebite menor).
static func _chapa(lado: int, rebites: bool, chanfro := 3) -> Image:
	var img := Image.create(lado, lado, false, Image.FORMAT_RGBA8)
	var base := Color(0.075, 0.085, 0.10)
	var filete := chanfro + 2
	for y in lado:
		for x in lado:
			var c := base
			c = c.lightened(0.04 * _ruido(x, y, 1) - 0.02)
			# sujeira: manchas largas mais escuras perto das bordas
			var borda := minf(minf(x, y), minf(lado - 1 - x, lado - 1 - y)) / float(lado) * 2.0
			var mancha := _ruido(x / 6, y / 6, 7)
			c = c.darkened(0.18 * mancha * (1.0 - borda))
			var a := 0.94
			if x == 0 or y == 0 or x == lado - 1 or y == lado - 1:
				c = Color(0.01, 0.01, 0.012)
				a = 1.0
			elif x <= chanfro or y <= chanfro:
				c = c.lightened(0.22 - 0.04 * minf(x, y))           # luz de cima/esquerda
			elif x >= lado - 1 - chanfro or y >= lado - 1 - chanfro:
				c = c.darkened(0.45)                               # sombra de baixo/direita
			elif x == filete or y == filete or x == lado - 1 - filete or y == lado - 1 - filete:
				c = c.lerp(cor("filete"), 0.35)                    # filete de cobre gasto
			img.set_pixel(x, y, Color(c, a))
	if rebites:
		var r := 3 if chanfro >= 3 else 1
		var pos := 9 if chanfro >= 3 else 4
		for cx in [pos, lado - 1 - pos]:
			for cy in [pos, lado - 1 - pos]:
				_rebite(img, cx, cy, r)
	return img


static func _rebite(img: Image, cx: int, cy: int, r := 3) -> void:
	var ri := float(r)
	for y in range(cy - r, cy + r + 1):
		for x in range(cx - r, cx + r + 1):
			var d := Vector2(x - cx, y - cy).length()
			if d > ri + 0.2 + (0.3 if r < 3 else 0.0):
				continue
			var luz := clampf(1.0 - Vector2(x - cx + 0.4 * ri, y - cy + 0.4 * ri).length() / (ri + 0.5), 0.0, 1.0)
			var c := Color(0.22, 0.24, 0.27).lerp(Color(0.62, 0.64, 0.68), luz)
			if d > ri - 0.6 and r >= 3:
				c = Color(0.03, 0.03, 0.035)
			img.set_pixel(x, y, c)


## Placa de botão: relevo (normal), mais clara (hover), afundada com brilho (apertado), apagada (desligado).
## chanfro 2 = a de sempre; 1 = a fina do PC.
static func _placa(lado: int, estado: String, chanfro := 2) -> Image:
	var img := Image.create(lado, lado, false, Image.FORMAT_RGBA8)
	var base: Color = {"normal": Color(0.13, 0.145, 0.165), "hover": Color(0.17, 0.19, 0.215),
			"apertado": Color(0.18, 0.14, 0.07), "desligado": Color(0.10, 0.10, 0.11)}[estado]
	var afunda := estado == "apertado"
	var filete := chanfro + 2 if chanfro >= 2 else chanfro + 1
	for y in lado:
		for x in lado:
			var c := base.lightened(0.05 * _ruido(x, y, 3) - 0.025)
			if x == 0 or y == 0 or x == lado - 1 or y == lado - 1:
				c = Color(0.01, 0.01, 0.012)
			elif x <= chanfro or y <= chanfro:
				c = c.darkened(0.4) if afunda else c.lightened(0.18)
			elif x >= lado - 1 - chanfro or y >= lado - 1 - chanfro:
				c = c.lightened(0.12) if afunda else c.darkened(0.4)
			var d := mini(mini(x, y), mini(lado - 1 - x, lado - 1 - y))
			if afunda and d == filete:
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
static func _botao_perigo(lado: int, apertado: bool, chanfro := 3, faixa := 5) -> Image:
	var img := Image.create(lado, lado, false, Image.FORMAT_RGBA8)
	var base := Color(0.16, 0.15, 0.14) if not apertado else Color(0.11, 0.10, 0.09)
	for y in lado:
		for x in lado:
			var d := mini(mini(x, y), mini(lado - 1 - x, lado - 1 - y))
			var c := base.lightened(0.05 * _ruido(x, y, 5) - 0.025)
			if d == 0:
				c = Color(0.01, 0.01, 0.012)
			elif d <= chanfro:
				var luz := (x <= chanfro or y <= chanfro) and not (x >= lado - 1 - chanfro or y >= lado - 1 - chanfro)
				if apertado:
					luz = not luz
				c = c.lightened(0.25) if luz else c.darkened(0.5)
				if _ruido(x, y, 17) > 0.86:
					c = c.lerp(Color(0.5, 0.48, 0.44), 0.6)         # canto sem tinta, metal à mostra
			elif d <= chanfro + faixa:
				c = _cor_listra(x, y, 2.0).darkened(0.15 if not apertado else 0.35)
			elif d == chanfro + faixa + 1:
				c = Color(0.02, 0.02, 0.02)
			else:
				c = c.darkened(0.15 * _ruido(x / 4, y / 4, 19))
				if _ruido(x, y * 3, 23) > 0.985:
					c = c.lightened(0.25)                           # arranhão
			img.set_pixel(x, y, c)
	return img
