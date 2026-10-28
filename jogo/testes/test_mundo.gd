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


func test_relevo() -> void:
	var g := GeradorMundo.new(1337)
	for x in range(-35, 36, 5):
		for y in range(-35, 36, 5):
			igual(g.nivel(Vector2i(x, y)), 0, "início plano (%d, %d)" % [x, y])
	var vistos := {}
	var saltos := 0
	for x in range(-300, 300, 3):
		for y in range(-300, 300, 3):
			var t := Vector2i(x, y)
			var nv := g.nivel(t)
			vistos[nv] = true
			verificar(nv >= -3 and nv <= 3, "nível dentro da faixa")
			var t2 := t + Vector2i(1, 0)
			if absi(g.nivel(t2) - nv) > 1 and not g.eh_agua(g.terreno(t)) and not g.eh_agua(g.terreno(t2)):
				saltos += 1                       # (rio cava o leito; mar fica no nível do mar)
	verificar(vistos.size() >= 4, "relevo com vários níveis (%s)" % [vistos.keys()])
	verificar(saltos < 40, "barrancos de no máximo 1 nível na maior parte (%d saltos de 2+)" % saltos)
	igual(g.nivel(Vector2i(120, -77)), g.nivel_bruto(Vector2i(120, -77)), "cache por chunk = cálculo direto")
	var m := MapaOcupacao.new(g)
	# acha um barranco e confere que máquina 2×2 em cima dele é recusada
	for x in range(60, 300):
		var t := Vector2i(x, 0)
		if g.nivel(t) != g.nivel(t + Vector2i(1, 0)) and not g.eh_agua(g.terreno(t)) and not g.eh_agua(g.terreno(t + Vector2i(1, 0))):
			for y in [0, -1]:
				m.limpar_obstaculo(t + Vector2i(0, y))
				m.limpar_obstaculo(t + Vector2i(1, y))
			igual(m.motivo_bloqueio("fornalha", t + Vector2i(0, -1), 0), "desnivel", "fornalha sobre barranco")
			break


func test_hidrologia() -> void:
	var gg := GeradorMundo.new(1337)
	var rios := 0
	var lagos := 0
	var sobe := 0
	for x in range(-700, 700, 2):
		for y in range(-700, 700, 2):
			var t := Vector2i(x, y)
			var a := gg.hidro.agua_em(t)
			if a.is_empty():
				continue
			if a.tipo == GeradorMundo.Terreno.RIO:
				rios += 1
				# rio nunca sobe: o tile rio abaixo tem nível ≤ este
				var f: Vector2 = a.fluxo
				var prox := Vector2i((Vector2(t) + Vector2(0.5, 0.5) + f * 1.5).floor())
				var b := gg.hidro.agua_em(prox)
				if not b.is_empty() and b.tipo == GeradorMundo.Terreno.RIO and int(b.nivel) > int(a.nivel):
					sobe += 1
			else:
				lagos += 1
				verificar(int(a.nivel) == gg.nivel_bruto(t) or gg.nivel_bruto(t) < int(a.nivel), "lago não sobe a borda")
	verificar(rios > 200, "há rios (%d amostras)" % rios)
	verificar(lagos > 50, "há lagos (%d amostras)" % lagos)
	verificar(sobe < rios / 50, "rio quase nunca sobe (%d de %d)" % [sobe, rios])
	for x in range(-40, 41, 4):
		for y in range(-40, 41, 4):
			verificar(gg.hidro.agua_em(Vector2i(x, y)).is_empty(), "início seco")
