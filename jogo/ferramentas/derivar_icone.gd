extends SceneTree
## Deriva o ícone de um item de outro já existente, trocando a cor da parte colorida (ex.: o líquido do frasco do
## pacote de pesquisa) por outro tom. Mantém sombra e brilho (só o matiz muda; saturação e valor ficam).
## Uso: godot --headless --path jogo -s res://ferramentas/derivar_icone.gd -- <base> <novo> <matiz 0..1> [faixa]
## Ex.: ... -- pacote_pesquisa pacote_automacao 0.08


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
	img.save_png("res://assets/icones/itens/%s.png" % a[1])
	print("%s.png: matiz %.3f → %.3f em %d pixels" % [a[1], base, alvo, n])
	quit()
