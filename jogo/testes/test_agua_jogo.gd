extends Caso
## Água em jogo: canal escavado ao lado de rio/lago enche aos poucos, não transborda, é barrado por dique (construção
## no seco), volta a encher quando o dique sai, seca ao aterrar; construção sobre a água vira plataforma.

func _achar(g: GeradorMundo) -> Array:
	for x in range(-300, 300):
		for y in range(-300, 300):
			var w := Vector2i(x, y)
			var ter := g.terreno(w)
			if ter != GeradorMundo.Terreno.LAGO and ter != GeradorMundo.Terreno.RIO:
				continue
			var ok := true
			for i in range(1, 8):
				var t := w + Vector2i(i, 0)
				if g.terreno(t) != GeradorMundo.Terreno.TERRA or g.nivel(t) < g.nivel(w):
					ok = false
				for d in [Vector2i(0, 1), Vector2i(0, -1)]:
					if g.eh_agua(g.terreno(t + d)):
						ok = false
			if ok:
				return [w, g.nivel(w)]
	return []


func test_canal_enche_dique_e_aterro() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var a := AguaJogo.new(g, m)
	var achou := _achar(g)
	verificar(not achou.is_empty(), "achou margem de rio/lago com terra reta ao lado")
	if achou.is_empty():
		return
	var w: Vector2i = achou[0]
	var s: int = achou[1]
	var t := func(i: int) -> Vector2i: return w + Vector2i(i, 0)
	for i in range(1, 8):
		m.limpar_obstaculo(t.call(i))
	# canal de 3 tiles, 1 nível abaixo da água
	for i in range(1, 4):
		g.aplainar(t.call(i), s - 1)
	a.recalcular()
	a.tick(0.31)
	verificar(a.cheios.has(t.call(1)) and not a.cheios.has(t.call(3)), "enche aos poucos, a partir da margem")
	for i in 5:
		a.tick(0.31)
	verificar(a.cheios.has(t.call(1)) and a.cheios.has(t.call(2)) and a.cheios.has(t.call(3)), "o canal todo encheu")
	igual(g.nivel(t.call(2)), s, "construir em cima do tile cheio é na superfície")
	# não transborda: tile escavado mas no mesmo nível da água não enche; e o que está depois dele também não
	g.aplainar(t.call(4), s)
	g.aplainar(t.call(5), s - 1)
	a.recalcular()
	a.encher_tudo()
	verificar(not a.cheios.has(t.call(4)) and not a.cheios.has(t.call(5)), "sem transbordar: só enche abaixo da superfície")
	# dique: escava 4 e 5, mas antes põe um muro no 4 (no seco)
	g.aplainar(t.call(4), s - 1)
	var dique := m.colocar("muro_centro", t.call(4), 0)
	verificar(dique >= 0, "muro coube no canal seco (%s)" % m.motivo_bloqueio("muro_centro", t.call(4), 0))
	a.recalcular()
	a.encher_tudo()
	verificar(not a.cheios.has(t.call(4)) and not a.cheios.has(t.call(5)), "o dique segura a água")
	m.remover(dique)
	a.recalcular()
	for i in 10:
		a.tick(0.31)
	verificar(a.cheios.has(t.call(4)) and a.cheios.has(t.call(5)), "sem o dique a água passa")
	# construção sobre a água: plataforma, não barra
	var bau := m.colocar("bau", t.call(2), 0)
	verificar(bau >= 0 and m.estruturas[bau].get("sobre_agua", false), "baú sobre o canal vira plataforma")
	a.recalcular()
	verificar(a.cheios.has(t.call(2)) and a.cheios.has(t.call(5)), "plataforma deixa a água passar")
	# aterrar a ligação seca o resto
	m.remover(bau)
	g.aplainar(t.call(1), s)
	a.recalcular()
	verificar(a.cheios.is_empty(), "aterrou a ligação: secou tudo (%d)" % a.cheios.size())
	igual(g.nivel(t.call(3)), s - 1, "seco volta ao fundo escavado")


func test_construir_sobre_rio_e_nao_no_mar() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var rio := Vector2i(9999, 0)
	var mar := Vector2i(9999, 0)
	for x in range(-400, 400, 3):
		for y in range(-400, 400, 3):
			var t := Vector2i(x, y)
			var ter := g.terreno(t)
			if rio.x == 9999 and ter == GeradorMundo.Terreno.RIO:
				rio = t
			if mar.x == 9999 and ter == GeradorMundo.Terreno.OCEANO:
				mar = t
	verificar(rio.x != 9999, "achou rio")
	m.limpar_obstaculo(rio)
	igual(m.motivo_bloqueio("esteira_reta", rio, 0), "", "esteira sobre o rio pode (ponte)")
	var id := m.colocar("esteira_reta", rio, 0)
	verificar(id >= 0 and m.estruturas[id].get("sobre_agua", false), "marcada sobre a água")
	if mar.x != 9999:
		igual(m.motivo_bloqueio("esteira_reta", mar, 0), "agua", "no oceano não (fundo demais)")
	igual(m.motivo_bloqueio("ninho_aranha", rio + Vector2i(0, 0), 0) in ["agua", "ocupado"], true, "ninho nunca na água")
