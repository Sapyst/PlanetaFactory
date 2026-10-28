extends Caso

func test_chunks() -> void:
	igual(Grade.chunk_de(Vector2i(0, 0)), Vector2i(0, 0))
	igual(Grade.chunk_de(Vector2i(-1, -1)), Vector2i(-1, -1), "negativos arredondam para baixo")
	igual(Grade.chunk_de(Vector2i(32, 31)), Vector2i(1, 0))
	igual(Grade.local_de(Vector2i(-1, 33)), Vector2i(31, 1))


func test_rotacao() -> void:
	igual(Grade.girar_i(Vector2i(0, 1), 1), Vector2i(-1, 0), "norte girado 90° anti-horário = oeste")
	igual(Grade.girar_i(Vector2i(1, 0), 3), Vector2i(0, -1))
	igual(Grade.area_girada(Vector2i(2, 3), 1), Vector2i(3, 2))


func test_mundo_e_grade() -> void:
	igual(Grade.tile_de_mundo(Grade.centro_mundo(Vector2i(5, -7))), Vector2i(5, -7))
	# a rotação do nó no Godot (em torno de +Y) tem que bater com girar() da grade
	var v := Vector2(0.3, 1.0)
	var r := 1
	var g := Grade.girar(v, r)
	var b := Basis(Vector3.UP, Grade.angulo(r))
	var w := b * Grade.ponto_mundo(v)
	perto(w.x, g.x, 1e-5, "x"); perto(-w.z, g.y, 1e-5, "y")


func test_portas_extrator() -> void:
	var d: Dictionary = Registro.estruturas["extrator_cristal"]
	var area := Registro.area("extrator_cristal")
	igual(area, Vector2i(3, 3))
	var p: Dictionary = d.portas[0]
	for r in 4:
		var pm := Grade.porta_no_mundo(p, Vector2i(10, 10), area, r)
		var dentro: Vector2i = pm.tile_dentro
		var fora: Vector2i = pm.tile_fora
		igual(fora - dentro, pm.dir, "fora = dentro + dir (r=%d)" % r)
		verificar(Grade.tiles_da_area(Vector2i(10, 10), area, r).has(dentro), "tile de dentro pertence à área (r=%d)" % r)
		verificar(not Grade.tiles_da_area(Vector2i(10, 10), area, r).has(fora), "tile de fora não pertence (r=%d)" % r)
	# r = 0: saída no meio da borda sul → tile de fora (11, 9)
	igual(Grade.porta_no_mundo(p, Vector2i(10, 10), area, 0).tile_fora, Vector2i(11, 9))
