extends Caso

var g := GeradorMundo.new(1337)


func test_deterministico() -> void:
	var g2 := GeradorMundo.new(1337)
	for t in [Vector2i(0, 0), Vector2i(500, -320), Vector2i(-1234, 77)]:
		igual(g.terreno(t), g2.terreno(t), "terreno igual com a mesma semente")
		igual(g.bioma(t), g2.bioma(t))
		igual(g.distribuicao.jazida(t), g2.distribuicao.jazida(t))
		igual(g.distribuicao.obstaculo(t), g2.distribuicao.obstaculo(t))


func test_sem_costura_entre_chunks() -> void:
	# o chunk gerado de uma vez tem que bater tile a tile com a consulta isolada (inclusive nos tiles da borda)
	for ch in [Vector2i(0, 0), Vector2i(3, -2), Vector2i(-5, 4)]:
		var c: ChunkDados = g.gerar_chunk(ch)
		var ok := true
		for j in Grade.TAM_CHUNK:
			for i in Grade.TAM_CHUNK:
				var t: Vector2i = ch * Grade.TAM_CHUNK + Vector2i(i, j)
				if c.terreno[c.indice(t)] != g.terreno(t) or g.nomes_biomas()[c.bioma[c.indice(t)]] != g.bioma(t):
					ok = false
		verificar(ok, "chunk %s igual à consulta por tile" % str(ch))


func test_spawn_jogavel() -> void:
	# terra firme e todas as jazidas iniciais a até 30 tiles do centro
	var tipos := {}
	var agua := 0
	for x in range(-30, 31):
		for y in range(-30, 31):
			var t := Vector2i(x, y)
			if g.eh_agua(g.terreno(t)):
				agua += 1
			var j := g.distribuicao.jazida(t)
			if not j.is_empty():
				tipos[j.tipo] = tipos.get(j.tipo, 0) + 1
	igual(agua, 0, "sem água no spawn")
	for tipo in ["jazida_cristal", "jazida_ferro", "jazida_cobre", "jazida_carvao", "jazida_pedra"]:
		verificar(tipos.get(tipo, 0) >= 25, "%s com pelo menos 25 tiles perto do spawn (veio %d)" % [tipo, tipos.get(tipo, 0)])
	for x in range(-6, 7):
		for y in range(-6, 7):
			verificar(g.distribuicao.obstaculo(Vector2i(x, y)).is_empty(), "centro do spawn livre de obstáculos")


func test_variedade_de_biomas_e_agua() -> void:
	# amostra grossa de uma região grande: todos os biomas e todos os tipos de água aparecem
	var biomas := {}
	var terrenos := {}
	for x in range(-1500, 1500, 9):
		for y in range(-1500, 1500, 9):
			var t := Vector2i(x, y)
			biomas[g.bioma(t)] = true
			terrenos[g.terreno(t)] = terrenos.get(g.terreno(t), 0) + 1
	for b in g.nomes_biomas():
		verificar(biomas.has(b), "bioma %s aparece" % b)
	for k in GeradorMundo.Terreno.values():
		verificar(terrenos.get(k, 0) > 0, "terreno %s aparece" % GeradorMundo.NOMES_TERRENO[k])
	var total := 0
	for k in terrenos: total += terrenos[k]
	var terra := float(terrenos.get(GeradorMundo.Terreno.TERRA, 0)) / total
	verificar(terra > 0.45 and terra < 0.85, "terra firme entre 45 e 85 por cento do mapa (veio %.0f)" % (terra * 100))


func test_grandes_nao_se_sobrepoem() -> void:
	# cada tile pertence a no máximo um obstáculo e grandes cabem inteiros em terra sem jazida
	var dono := {}
	for x in range(-120, 120):
		for y in range(-120, 120):
			var t := Vector2i(x, y)
			var o := g.distribuicao.obstaculo(t)
			if o.is_empty():
				continue
			verificar(g.terreno(t) == GeradorMundo.Terreno.TERRA, "obstáculo só em terra")
			verificar(g.distribuicao.jazida(t).is_empty(), "obstáculo não cobre jazida")
			var chave: String = str(o.ancora) + o.nome
			if dono.has(t):
				igual(dono[t], chave, "tile com dois obstáculos")
			dono[t] = chave


func test_chunk_rapido() -> void:
	var t0 := Time.get_ticks_usec()
	for i in 4:
		g.gerar_chunk(Vector2i(10 + i, 7))
	var ms := (Time.get_ticks_usec() - t0) / 4000.0
	print("      gerar_chunk: %.1f ms" % ms)
	verificar(ms < 400.0, "chunk gerado em menos de 400 ms (veio %.1f)" % ms)
