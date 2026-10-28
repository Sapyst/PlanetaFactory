extends Caso
## Trem: grafo montado do mapa (reta, curva 3×3, fim de linha, sinal, estação), viagem entre estações com
## inversão (vai-e-vem), carga levada de uma estação à outra, volta com curvas e dois trens respeitando blocos.

const CARROS: Array[String] = ["locomotiva", "vagao_carga", "vagao_carga", "locomotiva"]


func _construtor(de: Vector2i, ate: Vector2i) -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(de.x, ate.x + 1):
		for y in range(de.y, ate.y + 1):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot: int) -> void:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])


## Linha reta norte–sul em x = 0, de y = −16 a 16, com fim de linha nas duas pontas e 2 estações a leste.
func _linha() -> Construtor:
	var c := _construtor(Vector2i(-2, -18), Vector2i(4, 18))
	_por(c, "trilho_fim", Vector2i(0, -16), 2)
	for y in range(-15, 16):
		_por(c, "trilho_reto", Vector2i(0, y), 0)
	_por(c, "trilho_fim", Vector2i(0, 16), 0)
	_por(c, "estacao", Vector2i(1, 8), 0)       # A: parada em (0,5; 9,5)
	_por(c, "estacao", Vector2i(1, -12), 0)     # B: parada em (0,5; −10,5)
	return c


## Volta retangular (sentido horário com 4 curvas 3×3) em x 0..14, y 0..14, estações nos dois lados.
func _volta() -> Construtor:
	var c := _construtor(Vector2i(-2, -2), Vector2i(18, 16))
	_por(c, "trilho_curva", Vector2i(0, 12), 0)
	_por(c, "trilho_curva", Vector2i(12, 12), 3)
	_por(c, "trilho_curva", Vector2i(12, 0), 2)
	_por(c, "trilho_curva", Vector2i(0, 0), 1)
	for k in range(3, 12):
		_por(c, "trilho_reto", Vector2i(0, k), 0)
		_por(c, "trilho_reto", Vector2i(14, k), 0)
		_por(c, "trilho_reto", Vector2i(k, 14), 1)
		_por(c, "trilho_reto", Vector2i(k, 0), 1)
	_por(c, "estacao", Vector2i(1, 6), 0)
	_por(c, "estacao", Vector2i(15, 6), 0)
	return c


## Roda a simulação; troca carga nas chegadas. Devolve a lista de chegadas [trem, estrutura].
func _rodar(g: GrafoTrilhos, trens: Array[Trem], estoques: Dictionary, segundos: float, checar := Callable()) -> Array:
	var chegadas := []
	var dt := 1.0 / 30.0
	for i in int(segundos / dt):
		for t in trens:
			t.tick(dt)
			if t.chegada >= 0:
				if not estoques.has(t.chegada):
					estoques[t.chegada] = {"enviar": {}, "recebido": {}}
				t.trocar_carga(estoques[t.chegada], t.chegada)
				chegadas.append([t.id, t.chegada])
				t.chegada = -1
		if checar.is_valid():
			checar.call()
	return chegadas


func test_grafo_do_mapa() -> void:
	var g := GrafoTrilhos.de_mapa(_volta().mapa)
	igual(g.pecas.size(), 4 + 36, "4 curvas + 36 retas")
	var pontas_ruins := 0
	for k in g.arestas:
		if g.arestas[k].size() != 2:
			pontas_ruins += 1
	igual(pontas_ruins, 0, "na volta fechada toda ponta liga exatamente 2 peças (curvas encaixam nas retas)")
	igual(g.estacoes.size(), 2)
	for e in g.estacoes:
		verificar(e.peca >= 0, "parada da estação cai em cima do trilho")
	# eixo da curva é contínuo e tem o raio certo
	for p in g.pecas:
		if p.nome == "trilho_curva":
			perto(p.pontos[0].distance_to(p.a), 0.0, 1e-4, "arco começa na ponta a")
			perto(p.pontos[-1].distance_to(p.b), 0.0, 1e-4, "arco termina na ponta b")
	var l := GrafoTrilhos.de_mapa(_linha().mapa)
	igual(l.pecas.size(), 33)
	var fins := 0
	for k in l.arestas:
		if l.arestas[k].size() == 1:
			fins += 1
	igual(fins, 2, "duas pontas mortas (para-choques)")


func test_vai_e_vem_com_carga() -> void:
	var c := _linha()
	var g := GrafoTrilhos.de_mapa(c.mapa)
	var t := Trem.new(1, g, CARROS.duplicate())
	var base := g.peca_no_ponto(Vector2(0.5, -3.0))
	verificar(t.colocar(base.peca, g.pecas[base.peca].a), "trem cabe na linha")
	var a: int = g.estacoes[0].estrutura
	var b: int = g.estacoes[1].estrutura
	var est := {a: {"enviar": {"cristal_bruto": 100}, "recebido": {}}, b: {"enviar": {}, "recebido": {}}}
	var chegadas := _rodar(g, [t] as Array[Trem], est, 90.0)
	verificar(chegadas.size() >= 4, "fez várias viagens (%d chegadas)" % chegadas.size())
	if chegadas.size() >= 2:
		igual(chegadas[0][1], a, "vai primeiro à estação A")
		igual(chegadas[1][1], b, "depois à B (inverte, vai-e-vem)")
	igual(int(est[b].recebido.get("cristal_bruto", 0)), 100, "levou os 100 cristais de A para B (2 vagões × 40 por viagem)")
	igual(int(est[a].enviar.get("cristal_bruto", 0)), 0, "A ficou vazia")
	# parado centrado na estação
	var t2 := Trem.new(2, GrafoTrilhos.de_mapa(c.mapa), CARROS.duplicate())
	var g2 := t2.grafo
	var b2 := g2.peca_no_ponto(Vector2(0.5, -3.0))
	t2.colocar(b2.peca, g2.pecas[b2.peca].a)
	var parou := false
	for i in 30 * 40:
		t2.tick(1.0 / 30.0)
		if t2.chegada >= 0:
			var meio: Vector2 = t2.ponto_em(t2.s - t2.comprimento() / 2.0).pos
			perto(meio.distance_to(g2.estacoes[0].ponto), 0.0, 0.15, "meio do trem na parada")
			parou = true
			break
	verificar(parou, "chegou")


func test_volta_com_curvas() -> void:
	var c := _volta()
	var g := GrafoTrilhos.de_mapa(c.mapa)
	var t := Trem.new(1, g, CARROS.duplicate())
	var base := g.peca_no_ponto(Vector2(7.5, 0.5))
	verificar(t.colocar(base.peca, g.pecas[base.peca].a), "trem cabe na volta")
	var max_salto := 0.0
	var fora := 0.0
	var checar := func():
		for i in range(1, t.pontos.size()):
			max_salto = maxf(max_salto, t.pontos[i].distance_to(t.pontos[i - 1]))
		for pose in t.poses():
			for tr in pose.truques:
				var r := g.peca_no_ponto(tr.pos, 0.08)
				if r.is_empty():
					fora += 1
	var chegadas := _rodar(g, [t] as Array[Trem], {}, 120.0, checar)
	verificar(chegadas.size() >= 3, "deu voltas parando nas 2 estações (%d chegadas)" % chegadas.size())
	verificar(max_salto <= 1.01, "trilha contínua, sem salto (maior trecho %.2f m)" % max_salto)
	igual(fora, 0.0, "todo truque sempre em cima do eixo de alguma peça")


func test_dois_trens_e_sinais() -> void:
	var c := _volta()
	# sinais dividem a volta em 4 blocos (um no meio de cada lado)
	_por(c, "sinal_trem", Vector2i(-1, 7), 0)
	_por(c, "sinal_trem", Vector2i(15, 10), 0)
	_por(c, "sinal_trem", Vector2i(7, 15), 0)
	_por(c, "sinal_trem", Vector2i(7, -1), 0)
	var g := GrafoTrilhos.de_mapa(c.mapa)
	igual(g.calcular_blocos(), 4, "4 sinais na volta = 4 blocos")
	var curtos: Array[String] = ["locomotiva", "vagao_carga", "locomotiva"]
	var t1 := Trem.new(1, g, curtos.duplicate())
	var t2 := Trem.new(2, g, curtos.duplicate())
	var p1 := g.peca_no_ponto(Vector2(0.5, 4.0))
	var p2 := g.peca_no_ponto(Vector2(14.5, 10.0))
	verificar(t1.colocar(p1.peca, g.pecas[p1.peca].a), "trem 1")
	verificar(t2.colocar(p2.peca, g.pecas[p2.peca].b), "trem 2 em outro bloco, mesmo sentido (horário)")
	var t3 := Trem.new(3, g, curtos.duplicate())
	var p3 := g.peca_no_ponto(Vector2(0.5, 5.0))
	verificar(not t3.colocar(p3.peca, g.pecas[p3.peca].a), "não põe trem em bloco ocupado")
	var choques := 0
	var checar := func():
		var b1 := _blocos_sob(t1)
		for b in _blocos_sob(t2):
			if b1.has(b):
				choques += 1
	var chegadas := _rodar(g, [t1, t2] as Array[Trem], {}, 180.0, checar)
	igual(choques, 0, "nunca dois trens no mesmo bloco")
	var por_trem := {1: 0, 2: 0}
	for ch in chegadas:
		por_trem[ch[0]] += 1
	verificar(por_trem[1] >= 2 and por_trem[2] >= 2, "os dois andam e param (%s)" % por_trem)


func _blocos_sob(t: Trem) -> Dictionary:
	var out := {}
	for sg in t.segs:
		if sg.s1 > t.s - t.comprimento() and sg.s0 < t.s:
			out[t.grafo.pecas[sg.peca].bloco] = true
	return out


func test_reancorar_quando_a_malha_muda() -> void:
	var c := _linha()
	var g := GrafoTrilhos.de_mapa(c.mapa)
	var t := Trem.new(1, g, CARROS.duplicate())
	var base := g.peca_no_ponto(Vector2(0.5, -3.0))
	t.colocar(base.peca, g.pecas[base.peca].a)
	_rodar(g, [t] as Array[Trem], {}, 3.0)
	# põe um sinal em outro lugar: a malha é remontada e o trem continua
	_por(c, "sinal_trem", Vector2i(-1, -14), 0)
	var g2 := GrafoTrilhos.de_mapa(c.mapa)
	verificar(t.reancorar(g2), "trem segue na malha nova")
	var ch := _rodar(g2, [t] as Array[Trem], {}, 20.0)
	verificar(ch.size() >= 1, "e chega à estação")
	# tira o trilho debaixo do trem: descarrila (o mundo remove o trem)
	var debaixo: Vector2 = t.ponto_em(t.s - 1.0).pos
	c.mapa.remover(c.mapa.tiles[Vector2i(floori(debaixo.x), floori(debaixo.y))])
	verificar(not t.reancorar(GrafoTrilhos.de_mapa(c.mapa)), "sem trilho embaixo = fora da linha")


func test_rota_escolhida() -> void:
	var c := _volta()
	_por(c, "estacao", Vector2i(6, 15), 1)          # terceira estação, no lado de cima
	var g := GrafoTrilhos.de_mapa(c.mapa)
	igual(g.estacoes.size(), 3)
	var t := Trem.new(1, g, CARROS.duplicate())
	var base := g.peca_no_ponto(Vector2(7.5, 0.5))
	t.colocar(base.peca, g.pecas[base.peca].a)
	var a: int = g.estacoes[0].estrutura
	var cc: int = g.estacoes[2].estrutura
	t.rota = [cc, a] as Array[int]
	var chegadas := _rodar(g, [t] as Array[Trem], {}, 150.0)
	var onde := {}
	for ch in chegadas:
		onde[ch[1]] = true
	verificar(chegadas.size() >= 3, "andou (%d chegadas)" % chegadas.size())
	igual(onde.keys().size(), 2, "só parou nas 2 estações da rota")
	verificar(not onde.has(g.estacoes[1].estrutura), "pulou a estação fora da rota")
	if chegadas.size() > 0:
		igual(chegadas[0][1], cc, "na ordem escolhida")


func test_trens_de_frente_destravam() -> void:
	var c := _volta()
	_por(c, "sinal_trem", Vector2i(-1, 7), 0)
	_por(c, "sinal_trem", Vector2i(15, 10), 0)
	_por(c, "sinal_trem", Vector2i(7, 15), 0)
	_por(c, "sinal_trem", Vector2i(7, -1), 0)
	var g := GrafoTrilhos.de_mapa(c.mapa)
	var curtos: Array[String] = ["locomotiva", "vagao_carga", "locomotiva"]
	var t1 := Trem.new(1, g, curtos.duplicate())
	var t2 := Trem.new(2, g, curtos.duplicate())
	var p1 := g.peca_no_ponto(Vector2(0.5, 4.0))
	var p2 := g.peca_no_ponto(Vector2(14.5, 4.0))
	verificar(t1.colocar(p1.peca, g.pecas[p1.peca].a), "trem 1 subindo (horário)")
	verificar(t2.colocar(p2.peca, g.pecas[p2.peca].a), "trem 2 subindo do outro lado (anti-horário): vão se encarar")
	var choques := 0
	var checar := func():
		var b1 := _blocos_sob(t1)
		for b in _blocos_sob(t2):
			if b1.has(b):
				choques += 1
	var chegadas := _rodar(g, [t1, t2] as Array[Trem], {}, 300.0, checar)
	igual(choques, 0, "mesmo destravando, nunca dois no mesmo bloco")
	var por := {1: 0, 2: 0}
	for ch in chegadas:
		por[ch[0]] += 1
	verificar(por[1] >= 3 and por[2] >= 3, "os dois seguem fazendo viagens (%s)" % por)


func test_trem_salvo_e_carregado() -> void:
	var c := _linha()
	var g := GrafoTrilhos.de_mapa(c.mapa)
	var t := Trem.new(1, g, CARROS.duplicate())
	var base := g.peca_no_ponto(Vector2(0.5, -3.0))
	t.colocar(base.peca, g.pecas[base.peca].a)
	t.rota = [g.estacoes[1].estrutura] as Array[int]
	t.carga = {"cristal_bruto": 7}
	_rodar(g, [t] as Array[Trem], {}, 3.0)
	var texto := var_to_str(t.para_salvar())          # como vai para o arquivo
	var g2 := GrafoTrilhos.de_mapa(c.mapa)
	var t2 := Trem.de_salvo(str_to_var(texto), g2)
	verificar(t2 != null, "voltou do salvo")
	perto(t2.ponto_em(t2.s).pos.distance_to(t.ponto_em(t.s).pos), 0.0, 0.01, "frente no mesmo lugar")
	igual(t2.carga, t.carga, "mesma carga")
	igual(t2.rota, t.rota, "mesma rota")
	var ch := _rodar(g2, [t2] as Array[Trem], {}, 40.0)
	verificar(ch.size() >= 1 and ch[0][1] == g.estacoes[1].estrutura, "segue para a estação da rota")
