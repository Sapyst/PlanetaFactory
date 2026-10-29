class_name Casa
extends PanelContainer
## Casa de item/peça: quadrado afundado com o ícone no meio e o número no canto de baixo (como uma casa de
## inventário). `cor` tinge a borda (falta = vermelho, pronto = verde). Usada na árvore de pesquisa e no painel
## das máquinas.

const LADO := 60.0


static func nova(tex: Texture2D, numero := "", dica := "", cor := Color(0.35, 0.4, 0.45)) -> Casa:
	var c := Casa.new()
	c.custom_minimum_size = Vector2(LADO, LADO)
	c.tooltip_text = dica
	c.mouse_filter = Control.MOUSE_FILTER_PASS
	var st := Tema.caixa(Color(0.025, 0.035, 0.045, 0.95), cor, 6, 2)
	st.border_width_top = 2
	st.border_width_left = 2
	st.border_width_bottom = 1
	st.border_width_right = 1
	st.shadow_color = Color(0, 0, 0, 0.5)
	st.shadow_size = 2
	c.add_theme_stylebox_override("panel", st)
	var icone := TextureRect.new()
	icone.texture = tex
	icone.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icone.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icone.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(icone)
	if numero != "":
		var n := Label.new()
		n.text = numero
		n.add_theme_font_size_override("font_size", 15)
		n.add_theme_color_override("font_color", Color.WHITE)
		n.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		n.add_theme_constant_override("outline_size", 6)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		n.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.add_child(n)
	return c
