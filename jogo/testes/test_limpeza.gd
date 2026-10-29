extends Caso
## Consequências da sujeira e limpeza: bomba com poça contaminada rende menos e se desgasta; chão sujo deixa as
## aranhas furiosas; coletor, filtro e viveiro (mudas que viram árvore) limpam.

func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var f := Fabrica.new(m)
	return [g, m, f, AmbienteVivo.new(g, m, 3)]


## Liga a máquina sem rede elétrica (o teste é do ambiente, não da fiação) e roda n segundos.
func _rodar(a: AmbienteVivo, f: Fabrica, ids: Array, n: int) -> void:
	for i in n:
		for id in ids:
			var mq: Maquina = f.maquinas[id]
			mq.energia = 1.0
			mq.fluidos.clear()                 # a seiva sai pelo cano (sem cano a bomba encheria e pararia)
			mq.tick(1.0)
		a.tick(1.0, f, null)


func _limpar_area(m: MapaOcupacao, t: Vector2i, lado: int) -> void:
	for x in lado:
		for y in lado:
			m.limpar_obstaculo(t + Vector2i(x, y))


func _soma(a: AmbienteVivo, c: Vector2i, r: int, canal: int) -> float:
	var s := 0.0
	for x in range(-r, r + 1):
		for y in range(-r, r + 1):
			s += a.valor(c + Vector2i(x, y), canal)
	return s


func test_coletor_aspira_sujeira_e_oleo() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	_limpar_area(m, Vector2i(2, 2), 2)
	var id := m.colocar("coletor_lixo", Vector2i(2, 2), 0)
	verificar(id >= 0, "coletor colocado")
	f.reconstruir()
	for x in range(-2, 8):
		for y in range(-2, 8):
			a.somar(Vector2i(x, y), AmbienteVivo.SUJ, 0.5)
			a.somar(Vector2i(x, y), AmbienteVivo.OLEO, 0.4)
	a.somar(Vector2i(30, 30), AmbienteVivo.SUJ, 0.5)
	_rodar(a, f, [id], 60)
	var suj := a.valor(Vector2i(4, 4), AmbienteVivo.SUJ)
	verificar(suj < 0.3, "sujeira perto foi aspirada (%.3f)" % suj)
	verificar(a.valor(Vector2i(4, 4), AmbienteVivo.OLEO) < 0.25, "óleo também")
	verificar(a.valor(Vector2i(30, 30), AmbienteVivo.SUJ) > 0.45, "fora do raio não muda")
	# sem energia não limpa
	var b2 := _base()
	var m2: MapaOcupacao = b2[1]
	var f2: Fabrica = b2[2]
	var a2: AmbienteVivo = b2[3]
	_limpar_area(m2, Vector2i(2, 2), 2)
	m2.colocar("coletor_lixo", Vector2i(2, 2), 0)
	f2.reconstruir()
	a2.somar(Vector2i(4, 4), AmbienteVivo.SUJ, 0.5)
	for i in 60:
		a2.tick(1.0, f2, null)
	verificar(a2.valor(Vector2i(4, 4), AmbienteVivo.SUJ) > 0.45, "desligado não aspira")


func test_filtro_encosta_na_agua_e_limpa() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var lugar := Vector2i(9999, 0)
	for x in range(-300, 300, 2):
		for y in range(-300, 300, 2):
			var t := Vector2i(x, y)
			if lugar.x == 9999 and g.terreno(t) == GeradorMundo.Terreno.TERRA and g.terreno(t + Vector2i(2, 0)) == GeradorMundo.Terreno.RIO:
				_limpar_area(m, t, 2)
				if m.motivo_bloqueio("filtro_agua", t, 0) == "":
					lugar = t
	verificar(lugar.x != 9999, "lugar na margem do rio")
	_limpar_area(m, Vector2i(2, 2), 2)
	if g.terreno(Vector2i(2, 2)) == GeradorMundo.Terreno.TERRA and not m.encosta_na_agua(Vector2i(2, 2), Vector2i(2, 2), 0):
		igual(m.motivo_bloqueio("filtro_agua", Vector2i(2, 2), 0), "longe_da_agua", "longe da água não pode")
	var id := m.colocar("filtro_agua", lugar, 0)
	f.reconstruir()
	for x in range(-4, 7):
		for y in range(-4, 7):
			var t := lugar + Vector2i(x, y)
			if g.eh_agua(g.terreno(t)):
				a.somar(t, AmbienteVivo.AGUA, 0.6)
	var antes := _soma(a, lugar + Vector2i(1, 1), 4, AmbienteVivo.AGUA)
	verificar(antes > 0.5, "tinha água suja (%.2f)" % antes)
	_rodar(a, f, [id], 40)
	var depois := _soma(a, lugar + Vector2i(1, 1), 4, AmbienteVivo.AGUA)
	verificar(depois < antes * 0.5, "filtro limpou a água em volta (%.2f → %.2f)" % [antes, depois])


func test_bomba_com_poca_contaminada_rende_menos_e_desgasta() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var poca := Vector2i(9999, 0)
	for x in range(-300, 300):
		for y in range(-300, 300, 2):
			var t := Vector2i(x, y)
			if poca.x == 9999:
				var j := g.distribuicao.jazida(t)
				if not j.is_empty() and j.tipo == "poca_seiva":
					m.limpar_obstaculo(t)
					if m.motivo_bloqueio("bomba", t, 0) == "":
						poca = t
	verificar(poca.x != 9999, "achou poça de seiva")
	var id := m.colocar("bomba", poca, 0)
	f.reconstruir()
	var gasto := [0.0]
	a.dano = func(qual: int, pontos: float) -> void:
		if qual == id:
			gasto[0] += pontos
	_rodar(a, f, [id], 5)
	igual(a.contaminacao.get(id, -1.0), 0.0, "poça limpa")
	perto(f.maquinas[id].velocidade, 1.0, 0.001, "rende normal")
	igual(gasto[0], 0.0, "não desgasta")
	a.somar(poca, AmbienteVivo.OLEO, 0.8)
	_rodar(a, f, [id], 20)
	var c: float = a.contaminacao.get(id, 0.0)
	verificar(c > 0.6, "poça contaminada (%.2f)" % c)
	verificar(f.maquinas[id].velocidade < 0.6, "rende menos (%.2f)" % f.maquinas[id].velocidade)
	verificar(gasto[0] > 4.0, "bomba se desgasta (%.1f pontos)" % gasto[0])


func test_viveiro_planta_mudas_que_crescem_e_limpam() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var pol := Poluicao.new(g)
	a.poluicao = pol
	var lugar := Vector2i(9999, 0)
	for x in range(40, 300, 3):
		if lugar.x == 9999 and g.terreno(Vector2i(x, 40)) == GeradorMundo.Terreno.TERRA:
			_limpar_area(m, Vector2i(x, 40) - Vector2i(9, 9), 20)
			if m.motivo_bloqueio("viveiro", Vector2i(x, 40), 0) == "":
				lugar = Vector2i(x, 40)
	verificar(lugar.x != 9999, "lugar para o viveiro")
	var id := m.colocar("viveiro", lugar, 0)
	f.reconstruir()
	for x in range(-9, 11):
		for y in range(-9, 11):
			a.somar(lugar + Vector2i(x, y), AmbienteVivo.QUEIM, 0.8)
	var q0 := _soma(a, lugar + Vector2i(1, 1), 8, AmbienteVivo.QUEIM)
	var mq: Maquina = f.maquinas[id]
	for i in 6:
		mq.produzidos += 1                     # ciclos prontos (a seiva chega pelo cano no jogo)
		a.tick(1.0, f, null)
	igual(a.plantas.size(), 6, "6 mudas plantadas")
	for t: Vector2i in a.plantas:
		verificar((Vector2(t) + Vector2(0.5, 0.5)).distance_to(Vector2(lugar) + Vector2.ONE) <= 8.6, "muda no raio do viveiro")
		verificar(not m.tiles.has(t), "muda fora da construção")
	pol.emitir(lugar, 50.0)
	var p0 := pol.em(lugar)
	for i in 200:
		a.tick(1.0, f, null)
	for t: Vector2i in a.plantas:
		perto(a.plantas[t], 1.0, 0.001, "muda virou árvore")
	verificar(pol.em(lugar) < p0 - 2.0, "árvores absorveram poluição (%.1f → %.1f)" % [p0, pol.em(lugar)])
	var q1 := _soma(a, lugar + Vector2i(1, 1), 8, AmbienteVivo.QUEIM)
	verificar(q1 < q0, "chão queimado recupera mais rápido perto das árvores")
	# construir em cima (ou a 2 tiles: o piso de fábrica chega lá) corta a árvore
	var alvo: Vector2i = a.plantas.keys()[0]
	var n := a.plantas.size()
	m.colocar("bau", alvo, 0)
	a.tick(1.0, f, null)
	verificar(not a.plantas.has(alvo) and a.plantas.size() < n, "construção em cima corta a planta")
	for t: Vector2i in a.plantas:
		verificar(maxi(absi(t.x - alvo.x), absi(t.y - alvo.y)) > 2, "nenhuma planta debaixo do piso novo")
	# salva e restaura
	var a2 := AmbienteVivo.new(g, m, 3)
	a2.restaurar(a.estado())
	igual(a2.plantas.size(), a.plantas.size(), "plantas voltam do save")


func test_aranhas_ficam_furiosas_com_chao_sujo() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var pol := Poluicao.new(g)
	var a := AmbienteVivo.new(g, m, 3)
	var col := Colonia.new(m, pol, 7)
	col.ambiente = a
	var lugar := Vector2i(9999, 0)
	for x in range(100, 300, 3):
		if lugar.x == 9999 and m.motivo_bloqueio("ninho_aranha", Vector2i(x, 100), 0) == "":
			lugar = Vector2i(x, 100)
	verificar(lugar.x != 9999, "lugar para ninho")
	var ninho := col._criar_ninho(lugar, 1.0)
	var ar := col._nova_aranha(ninho)
	var fontes: Array[Dictionary] = []
	col.tick(0.1, fontes)
	perto(col.ninhos[ninho].furia, 0.0, 0.001, "chão limpo: sem fúria")
	for x in range(-24, 25):
		for y in range(-24, 25):
			a.somar(lugar + Vector2i(x, y), AmbienteVivo.SUJ, 0.15)
	col.tick(6.0, fontes)
	verificar(col.ninhos[ninho].furia > 0.9, "chão sujo: aranhas furiosas (%.2f)" % col.ninhos[ninho].furia)
	verificar(col.furia(col.aranhas[ar]) > 0.9, "aranha herda a fúria do ninho")
	# furiosas nascem mais rápido com a mesma poluição
	var nascidas := func(furiosas: bool) -> int:
		var m2 := MapaOcupacao.new(g)
		var p2 := Poluicao.new(g)
		var a2 := AmbienteVivo.new(g, m2, 3)
		var c2 := Colonia.new(m2, p2, 7)
		c2.ambiente = a2
		var nn := c2._criar_ninho(lugar, 1.0)
		if furiosas:
			for x in range(-24, 25):
				for y in range(-24, 25):
					a2.somar(lugar + Vector2i(x, y), AmbienteVivo.SUJ, 0.15)
		for i in 12:
			p2.emitir(lugar, 1.0)
			c2.tick(1.0, fontes)
		return c2.aranhas_do_ninho(nn).size()
	var calmas: int = nascidas.call(false)
	var bravas: int = nascidas.call(true)
	verificar(bravas > calmas, "furiosas nascem mais (%d contra %d)" % [bravas, calmas])
