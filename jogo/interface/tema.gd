class_name Tema
## Tema único da interface (barra, menus, painéis): painéis escuros, borda fina, destaque âmbar.

static func criar() -> Theme:
	var t := Theme.new()
	t.default_font_size = 18
	var painel := caixa(BarraConstrucao.COR_FUNDO, BarraConstrucao.COR_BORDA, 12, 10)
	t.set_stylebox("panel", "PanelContainer", painel)
	var normal := caixa(Color(0.16, 0.17, 0.21), Color(0.30, 0.32, 0.38), 8, 6)
	var hover := caixa(Color(0.22, 0.23, 0.28), Color(0.45, 0.47, 0.54), 8, 6)
	var apertado := caixa(BarraConstrucao.COR_DESTAQUE.darkened(0.6), BarraConstrucao.COR_DESTAQUE, 8, 6)
	var desligado := caixa(Color(0.12, 0.12, 0.15), Color(0.2, 0.2, 0.24), 8, 6)
	t.set_stylebox("normal", "Button", normal)
	t.set_stylebox("hover", "Button", hover)
	t.set_stylebox("pressed", "Button", apertado)
	t.set_stylebox("hover_pressed", "Button", apertado)
	t.set_stylebox("disabled", "Button", desligado)
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", Color(0.90, 0.91, 0.94))
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", Color.WHITE)
	t.set_color("font_disabled_color", "Button", Color(0.45, 0.46, 0.5))
	t.set_constant("icon_max_width", "Button", 64)
	t.set_stylebox("slider", "HSlider", caixa(Color(0.12, 0.12, 0.15), Color(0.3, 0.32, 0.38), 6, 4))
	t.set_color("font_color", "CheckButton", Color(0.9, 0.91, 0.94))
	return t


static func caixa(fundo: Color, borda: Color, raio: int, margem: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = fundo
	s.border_color = borda
	s.set_border_width_all(2)
	s.set_corner_radius_all(raio)
	s.set_content_margin_all(margem)
	return s
