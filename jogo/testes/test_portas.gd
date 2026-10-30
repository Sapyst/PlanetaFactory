extends Caso
## Girar estrutura já construída, porta solta/ligada (Portas) e frente do braço.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 16):                                      # tira pedras e árvores da área dos testes
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_girar_quadrada_mantem_id_e_area() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	verificar(id >= 0, "colocou")
	verificar(m.girar(id), "girou")
	igual(m.estruturas[id].rot, 3, "um quarto horário")
	igual(m.estruturas[id].minimo, Vector2i(2, 2), "quadrada: mesmo canto")
	igual(m.tiles.get(Vector2i(3, 3), -1), id, "mesmos tiles")
	for i in 3:
		m.girar(id)
	igual(m.estruturas[id].rot, 0, "volta inteira")


func test_girar_bloqueado_por_vizinho() -> void:
	var m := _mapa()
	var id := m.colocar("estacao", Vector2i(10, 0), 0)          # 2×3: girada vira 3×2
	verificar(id >= 0, "colocou a estação")
	var c := Grade.centro_da_area(m.estruturas[id].minimo, m.estruturas[id].area, 0)
	var bloqueio := m.colocar("bau", Vector2i(floori(c.x) + 1, floori(c.y)), 0)
	verificar(bloqueio >= 0, "baú encostado")
	verificar(not m.girar(id), "não gira por cima do baú")
	igual(m.estruturas[id].rot, 0, "continua como estava")


func test_porta_solta_e_ligada() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	var soltas := Portas.soltas(m, id)
	igual(soltas.size(), 2, "fornalha sozinha: entrada e saída soltas")
	# esteira encostada na saída norte
	var saida: Dictionary = {}
	for p in Registro.modelos.fornalha.portas:
		if p.io == "SAI":
			saida = p
	var pm := Grade.porta_no_mundo(saida, m.estruturas[id].minimo, m.estruturas[id].area, 0)
	verificar(m.colocar("esteira_reta", pm.tile_fora, 0) >= 0, "esteira na saída")
	igual(Portas.soltas(m, id).size(), 1, "só a entrada continua solta")


func test_braco_serve_por_qualquer_lado() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	# braço a oeste soltando para dentro (frente para leste: rot 3)
	var b := m.colocar("braco", Vector2i(1, 2), 3)
	igual(Portas.frente_braco(m.estruturas[b]), Vector2i(2, 2), "frente do braço girado para leste")
	verificar(Portas.braco_serve(m, m.estruturas[id], true), "braço alimenta pela lateral")
	var tem_ent := false
	for s in Portas.soltas(m, id):
		tem_ent = tem_ent or s.io == "ENT"
	verificar(not tem_ent, "entrada atendida pelo braço não aparece como solta")
