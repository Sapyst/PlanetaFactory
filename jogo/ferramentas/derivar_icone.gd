extends SceneTree
## Deriva o ícone de um item de outro já existente, trocando a cor da parte colorida (ex.: o líquido do frasco do
## pacote de pesquisa) por outro tom. Mantém sombra e brilho (só o matiz muda; saturação e valor ficam).
## Uso: godot --headless --path jogo -s res://ferramentas/derivar_icone.gd -- <base> <novo> <matiz 0..1> [faixa] [nivel]
## Ex.: ... -- pacote_pesquisa pacote_automacao 0.08
## `nivel` (1..3): carimba N marcas claras no canto de cima (módulos 1/2/3 do mesmo tipo têm o mesmo desenho).


func _init() -> void:
	var a := OS.get_cmdline_user_args()
	if a.size() < 3:
		push_error("uso: -- <base> <novo> <matiz> [faixa]")
		quit(1)
		return
	var img := Image.load_from_file("res://assets/icones/itens/%s.png" % a[0])
	img.convert(Image.FORMAT_RGBA8)
	var alvo := float(a[2])
	var faixa := float(a[3]) if a.size() > 3 else 0.12
	# matiz dominante da parte colorida: média dos pixels bem saturados
	var soma := Vector2.ZERO
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			if c.a > 0.5 and c.s > 0.3:
				soma += Vector2(cos(c.h * TAU), sin(c.h * TAU))
	var base := fposmod(soma.angle() / TAU, 1.0)
	var n := 0
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			var d := absf(fposmod(c.h - base + 0.5, 1.0) - 0.5)
			if c.a > 0.0 and c.s > 0.15 and d < faixa:
				img.set_pixel(x, y, Color.from_hsv(alvo, minf(c.s * 1.1, 1.0), c.v, c.a))
				n += 1
	if a.size() > 4:
		_marcas(img, int(a[4]))
	img.save_png("res://assets/icones/itens/%s.png" % a[1])
	print("%s.png: matiz %.3f → %.3f em %d pixels" % [a[1], base, alvo, n])
	quit()


## N barrinhas claras com contorno escuro, no canto esquerdo de cima.
func _marcas(img: Image, nivel: int) -> void:
	var escala := img.get_width() / 128.0
	var larg := int(10 * escala)
	var alt := int(24 * escala)
	var passo := int(16 * escala)
	var borda := maxi(int(2 * escala), 1)
	for i in nivel:
		var x := int(4 * escala) + i * passo
		var y := int(4 * escala)
		img.fill_rect(Rect2i(x - borda, y - borda, larg + borda * 2, alt + borda * 2), Color(0.05, 0.05, 0.07))
		img.fill_rect(Rect2i(x, y, larg, alt), Color(1.0, 0.93, 0.55))
