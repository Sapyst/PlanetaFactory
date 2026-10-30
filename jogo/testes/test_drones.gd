extends Caso
## Drones (fase 2.6; estudo_drones.py e estudo_drones_modelo.py via arte/estudos/conv_drones.py): estação de drones
## 2×2 que monta drones (placas + motor + circuitos + 50 de água) e os lança — reparo (escaneia e solda o que as
## aranhas morderam, pagando placas do núcleo), combate (caça aranhas, pode ser derrubado) e logístico (provedor →
## requisitante); bateria, raios e as melhorias da árvore.

const DT := 1.0 / 30.0


func _base() -> Dictionary:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	for x in range(-40, 80):
		for y in range(-40, 60):
			m.limpar_obstaculo(Vector2i(x, y))
	var f := Fabrica.new(m)
	var col := Colonia.new(m, Poluicao.new(g), 3)
	var dr := Drones.new(m, f, col)
	return {"g": g, "m": m, "f": f, "col": col, "dr": dr}


## Lugar livre para `nome` perto de `perto` (espiral).
func _lugar(m: MapaOcupacao, nome: String, perto: Vector2i) -> Vector2i:
	for r in 30:
		for dx in range(-r, r + 1):
			for dy in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) == r and m.motivo_bloqueio(nome, perto + Vector2i(dx, dy), 0) == "":
					return perto + Vector2i(dx, dy)
	return Vector2i(9999, 9999)


## Estação com núcleo encostado (energia sem fio) e n drones prontos no hangar.
func _estacao(b: Dictionary, n := 2, tipo := "reparo") -> int:
	var m: MapaOcupacao = b.m
	var nu := m.colocar("nucleo", _lugar(m, "nucleo", Vector2i(0, 0)), 0)
	var en: Dictionary = m.estruturas[nu]
	var est := m.colocar(Drones.ESTACAO, _lugar(m, Drones.ESTACAO, en.minimo + Vector2i(4, 0)), 0)
	m.estruturas[est]["drones_tipo"] = tipo
	(b.f as Fabrica).reconstruir()
	(b.f as Fabrica).tick(DT)
	var dr: Drones = b.dr
	for i in n:
		var id := dr.novo(est)
		dr.drones[id].e = Drones.E.HANGAR
	return est


func _rodar(b: Dictionary, s: float) -> void:
	for i in int(s / DT):
		(b.f as Fabrica).tick(DT)
		(b.dr as Drones).tick(DT)


func test_dados_e_modelos() -> void:
	var md: Dictionary = Registro.modelos.get(Drones.ESTACAO, {})
	igual(md.get("estudo", ""), "estudo_drones.py", "estação convertida do estudo")
	igual(Registro.area(Drones.ESTACAO), Vector2i(2, 2), "2×2")
	verificar(float(md.dims[0]) <= 2.01 and float(md.dims[1]) <= 2.01, "dentro da área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 10000, "orçamento (%d)" % md.tris)
	verificar(md.get("anima", false), "garras, plugue e braço abastecedor animam")
	igual(md.portas.size(), 1, "uma entrada de água")
	igual(md.portas[0].nome, "PORTA_FLUIDO_ENT_S1", "pela borda sul, tile leste")
	perto(float(md.portas[0].pos[2]), float(Registro.modelos.cano_reto.portas[0].pos[2]), 0.01, "na altura dos canos")
	verificar(ResourceLoader.exists("res://assets/icones/estacao_drones.png"), "ícone da barra")
	verificar(ResourceLoader.exists("res://assets/icones/itens/drone.png"), "ícone do item drone")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Drones" and Drones.ESTACAO in cat.pecas), "aba Drones")
	verificar(not Registro.progressao.custos.get(Drones.ESTACAO, {}).is_empty(), "custo")
	igual(Fiacao.papel(Drones.ESTACAO), "consumo", "precisa de energia")
	var rd: Dictionary = Registro.receitas.fabricar_drone
	igual([int(rd.entradas.placa_ferro), int(rd.entradas.motor), int(rd.entradas.circuito)], [4, 1, 2], "drone da árvore: 4 placas + 1 motor + 2 circuitos")
	igual(int(rd.entradas_fluido.agua), 50, "+ 50 de água")
	var partes_tipo := {"drone_reparo": ["giro", "ombro", "cotovelo"], "drone_defesa": ["torre", "canhao", "boca"],
			"drone_logistico": ["pendulo", "carga"]}
	for n in partes_tipo:
		var dm: Dictionary = Registro.modelos.get(n, {})
		igual(dm.get("estudo", ""), "estudo_drones_modelo.py", "drone do estudo: " + n)
		igual(dm.get("tipo", ""), "veiculo", n)
		var nomes: Array = dm.get("partes", []).map(func(p): return p.nome)
		for k in 4:
			verificar(("rotor%d" % k) in nomes, "%s: rotor%d gira" % [n, k])
		for p in partes_tipo[n]:
			verificar(p in nomes, "%s: parte %s" % [n, p])
		verificar(int(dm.tris) <= 3200, "drone leve: %s %d" % [n, dm.tris])
		verificar(float(dm.dims[0]) < 0.7, "drone pequeno (%s)" % str(dm.dims))
	for t in Drones.TIPOS:
		verificar(Registro.modelos.has(DesenhoDrones.MODELOS[t]), "modelo do tipo " + t)


func test_pesquisas() -> void:
	var p := Pesquisa.new()
	for id in ["drones", "drones_bateria_1", "drones_frota_1", "drones_velocidade_1", "drones_logisticos", "drones_frota_2",
			"drones_bateria_2", "drones_velocidade_2", "drones_logisticos_2", "drones_tempestade", "drones_defesa"]:
		verificar(p.jogavel(id), "jogável: " + id)
	p.concluidas = {"bomba_agua": true}
	verificar(not p.disponivel("drones"), "drones esperam a energia sem fio")
	p.concluidas["sem_fio"] = true
	verificar(p.disponivel("drones"), "bomba d'água + sem fio")
	igual(p.custo("drones"), {"pacote_pesquisa": 50, "pacote_automacao": 50}, "custo da árvore")
	p.concluidas["drones"] = true
	verificar(p.peca_liberada(Drones.ESTACAO), "libera a estação")
	verificar(p.receita_liberada("fabricar_drone"), "libera o drone")
	p.concluidas.merge({"drones_frota_1": true, "drones_frota_2": true, "drones_bateria_1": true, "drones_velocidade_1": true,
			"drones_defesa": true, "drones_logisticos_2": true, "drones_tempestade": true})
	perto(p.bonus("drones_frota"), 12.0, 1e-6, "frota 8 → 20")
	perto(p.bonus("drones_bateria"), 0.3, 1e-6, "+30% de voo")
	perto(p.bonus("drones_velocidade"), 0.25, 1e-6, "+25% de velocidade")
	perto(p.bonus("drones_dano"), 1.0, 1e-6, "defesa: +100% de dano")
	perto(p.bonus("drones_vida"), 0.5, 1e-6, "defesa: +50% de vida")
	perto(p.bonus("drones_carga"), 3.0, 1e-6, "logístico 2: 4 itens")
	verificar(p.pesquisas().drones_logisticos.get("modos", []).has("drones_logistico"), "logísticos liberam o porto")


func test_monta_drone_na_estacao() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var f: Fabrica = b.f
	var dr: Drones = b.dr
	var est := _estacao(b, 0)
	verificar(est >= 0, "estação montada")
	var mq: Maquina = f.maquinas[est]
	igual(mq.receita_id, "fabricar_drone", "receita do drone")
	verificar(f.energia(est) > 0.5, "o núcleo dá energia (%.2f)" % f.energia(est))
	for i in 8:
		mq.receber("placa_ferro")
	for i in 2:
		mq.receber("motor")
	for i in 4:
		mq.receber("circuito")
	mq.receber_fluido("agua", 100.0)
	_rodar(b, 13.0)
	igual(dr.frota(est), 1, "um drone pronto entrou na frota")
	var d: Dictionary = dr.drones.values()[0]
	verificar(d.e in [Drones.E.NASCENDO, Drones.E.HANGAR], "nasce na fabricadora (holograma)")
	igual(mq.pegar_para_braco(""), "", "braço não tira drone da estação")
	_rodar(b, 13.0)
	igual(dr.frota(est), 2, "segundo drone")
	_rodar(b, 4.0)
	igual(dr.no_hangar(est), 2, "entram no hangar")
	# frota cheia: a máquina para com o drone na saída
	for i in dr.frota_max() - 2:
		var id := dr.novo(est)
		dr.drones[id].e = Drones.E.HANGAR
	for i in 8:
		mq.receber("placa_ferro")
	mq.receber("motor")
	for i in 4:
		mq.receber("circuito")
	mq.receber_fluido("agua", 100.0)
	_rodar(b, 30.0)
	igual(dr.frota(est), dr.frota_max(), "não passa da frota")
	verificar(int(mq.saidas.get("drone", 0)) >= 1, "o drone que sobra espera na saída")
	m.estruturas[est]["drones_tipo"] = "reparo"


func test_reparo_paga_placas() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var col: Colonia = b.col
	var dr: Drones = b.dr
	var est := _estacao(b, 1, "reparo")
	dr.cobrar = true
	dr.inventario["placa_ferro"] = 3
	var c := dr.centro(est)
	var alvo := m.colocar("muro_centro", _lugar(m, "muro_centro", Vector2i(c.floor()) + Vector2i(10, 6)), 0)
	var vmax := float(Registro.estruturas.muro_centro.vida)
	col.vida[alvo] = vmax - 60.0
	var longe := m.colocar("muro_centro", _lugar(m, "muro_centro", Vector2i(c.floor()) + Vector2i(60, 0)), 0)
	col.vida[longe] = 100.0
	_rodar(b, 1.0)
	var d: Dictionary = dr.drones.values()[0]
	verificar(d.e in [Drones.E.DECOLANDO, Drones.E.INDO], "decolou para o muro mordido")
	igual(d.alvo, alvo, "alvo: o muro no alcance (o de 60 m fica de fora)")
	var t := 0.0
	var soldou := false
	while t < 30.0 and col.vida.has(alvo):
		_rodar(b, 0.5)
		t += 0.5
		soldou = soldou or d.e == Drones.E.TRABALHANDO
	verificar(soldou, "parou ao lado e soldou")
	verificar(not col.vida.has(alvo), "muro inteiro de novo")
	igual(int(dr.inventario.placa_ferro), 0, "60 ♥ = 3 placas (1 a cada 25)")
	verificar(col.vida.has(longe), "fora do alcance ninguém conserta")
	_rodar(b, 20.0)
	igual(d.e, Drones.E.HANGAR, "voltou ao hangar")
	# sem placa no núcleo (e sem crédito de placa já gasta), não decola
	dr.pago.clear()
	col.vida[alvo] = vmax - 30.0
	_rodar(b, 3.0)
	igual(d.e, Drones.E.HANGAR, "sem placas fica no hangar")
	perto(float(col.vida[alvo]), vmax - 30.0, 1e-3, "e o muro continua mordido")


func test_combate_caca_aranhas() -> void:
	var b := _base()
	var col: Colonia = b.col
	var dr: Drones = b.dr
	var est := _estacao(b, 3, "combate")
	var c := dr.centro(est)
	col.aranhas[900] = {"id": 900, "pos": c + Vector2(14, 3), "vida": 60.0, "ninho": -1, "estado": Colonia.E.PARADA, "alvo": -1,
			"destino": c + Vector2(14, 3), "mordendo": false, "t": 0.0, "preso": 0.0}
	col.aranhas[901] = {"id": 901, "pos": c + Vector2(80, 0), "vida": 60.0, "ninho": -1, "estado": Colonia.E.PARADA, "alvo": -1,
			"destino": c + Vector2(80, 0), "mordendo": false, "t": 0.0, "preso": 0.0}
	var tiros := 0
	for i in int(25.0 / DT):
		(b.f as Fabrica).tick(DT)
		dr.tick(DT)
		for e in dr.eventos:
			if e.tipo == "drone_tiro":
				tiros += 1
				verificar((e.para as Vector2).distance_to(e.de) <= 8.01, "atira de até 8 m")
	verificar(not col.aranhas.has(900), "aranha no alcance morta pelos drones")
	verificar(col.aranhas.has(901), "a de 80 m (fora do alcance de 45) fica")
	verificar(tiros >= 15, "tiros (%d): 60 de vida / 4 de dano" % tiros)
	# drone baixo no meio de muitas aranhas é derrubado
	var b2 := _base()
	var dr2: Drones = b2.dr
	var col2: Colonia = b2.col
	var est2 := _estacao(b2, 1, "combate")
	var c2 := dr2.centro(est2)
	for k in 8:
		col2.aranhas[700 + k] = {"id": 700 + k, "pos": c2 + Vector2(12, 0) + Vector2.from_angle(k * TAU / 8.0) * 1.0, "vida": 600.0,
				"ninho": -1, "estado": Colonia.E.PARADA, "alvo": -1, "destino": c2, "mordendo": false, "t": 0.0, "preso": 0.0}
	var abatido := false
	var sucata := false
	for i in int(30.0 / DT):
		(b2.f as Fabrica).tick(DT)
		dr2.tick(DT)
		for e in dr2.eventos:
			abatido = abatido or e.tipo == "drone_abatido"
			sucata = sucata or e.tipo == "drone_sucata"
	verificar(abatido, "mordido até a vida acabar: derrubado")
	verificar(sucata, "caiu e virou sucata")
	igual(dr2.frota(est2), 0, "a frota perdeu o drone (a estação monta outro com itens)")
	# drones de defesa: +100% de dano e +50% de vida
	dr2.bonus = func(k: String) -> float: return {"drones_dano": 1.0, "drones_vida": 0.5}.get(k, 0.0)
	perto(dr2.dano(), 8.0, 1e-6, "dano 4 → 8")
	perto(dr2.vida_max(), 90.0, 1e-6, "vida 60 → 90")


func test_logistica() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var f: Fabrica = b.f
	var dr: Drones = b.dr
	var est := _estacao(b, 2, "logistico")
	verificar(dr.tipo_de(est) == "reparo", "sem a pesquisa o porto não abre (volta a reparo)")
	dr.logistica_ok = func() -> bool: return true
	igual(dr.tipo_de(est), "logistico", "com drones logísticos")
	var c := Vector2i(dr.centro(est).floor())
	var prov := m.colocar("bau", _lugar(m, "bau", c + Vector2i(-8, 8)), 0)
	var req := m.colocar("bau", _lugar(m, "bau", c + Vector2i(10, -6)), 0)
	f.reconstruir()
	m.estruturas[prov]["logistica"] = "provedor"
	m.estruturas[req]["logistica"] = "requisitante"
	m.estruturas[req]["pede_item"] = "engrenagem"
	m.estruturas[req]["pede_qtd"] = 3
	f.baus[prov]["engrenagem"] = 10
	f.baus[prov]["pedra"] = 5
	_rodar(b, 40.0)
	igual(int(f.baus[req].get("engrenagem", 0)), 3, "trouxe até a quantidade pedida")
	igual(int(f.baus[prov].get("engrenagem", 0)), 7, "tirou do provedor")
	igual(int(f.baus[req].get("pedra", 0)), 0, "só o item pedido")
	_rodar(b, 20.0)
	igual(dr.no_hangar(est), 2, "voltaram ao porto")
	# logísticos 2: 4 itens por viagem e o dobro do alcance
	perto(dr.alcance(est), 45.0, 1e-6, "alcance 45")
	dr.bonus = func(k: String) -> float: return {"drones_carga": 3.0, "drones_alcance": 1.0}.get(k, 0.0)
	igual(dr.carga_max(), 4, "4 itens")
	perto(dr.alcance(est), 90.0, 1e-6, "porto 2× alcance")


func test_bateria_e_raios() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var col: Colonia = b.col
	var dr: Drones = b.dr
	var est := _estacao(b, 1, "reparo")
	var c := Vector2i(dr.centro(est).floor())
	var raios := [true]
	dr.raios_agora = func() -> bool: return raios[0]
	# silo quase no chão (900 ♥): serviço longo o bastante para a bateria pesar
	var silo := m.colocar("silo_granel", _lugar(m, "silo_granel", c + Vector2i(18, 0)), 0)
	col.vida[silo] = 1.0
	_rodar(b, 3.0)
	var d: Dictionary = dr.drones.values()[0]
	igual(d.e, Drones.E.HANGAR, "com raios caindo não decola")
	raios[0] = false
	_rodar(b, 3.0)
	verificar(d.e in [Drones.E.DECOLANDO, Drones.E.INDO, Drones.E.TRABALHANDO], "sem raios, decola")
	raios[0] = true
	_rodar(b, 1.0)
	igual(d.e, Drones.E.VOLTANDO, "raio: os do ar voltam")
	dr.bonus = func(k: String) -> float: return 1.0 if k == "drones_tempestade" else 0.0
	verificar(dr.pode_voar(), "blindados voam na tempestade")
	_rodar(b, 12.0)
	verificar(d.e in [Drones.E.INDO, Drones.E.TRABALHANDO], "voltou ao serviço com a blindagem")
	# bateria: volta antes de acabar
	d.bateria = 6.5
	_rodar(b, 0.2)
	igual(d.e, Drones.E.VOLTANDO, "bateria baixa: volta")
	col.vida.erase(silo)
	_rodar(b, 8.0)
	igual(d.e, Drones.E.HANGAR, "pousou antes de acabar")
	verificar(float(d.bateria) > 0.0, "chegou com bateria")
	_rodar(b, 16.0)
	perto(float(d.bateria), dr.voo_max(), 0.5, "recarregou no hangar com a energia da estação")


func test_salvar_e_desmontar() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var dr: Drones = b.dr
	var est := _estacao(b, 2, "combate")
	var dados: Dictionary = str_to_var(var_to_str(dr.estado()))
	var dr2 := Drones.new(m, b.f, b.col)
	dr2.restaurar(dados)
	igual(dr2.drones.size(), 2, "drones voltam do salvo")
	igual(dr2.frota(est), 2, "da mesma estação")
	var id := dr2.novo(est)
	verificar(not dados.drones.has(id), "o contador segue (id novo)")
	m.remover(est)
	dr2.tick(DT)
	igual(dr2.drones.size(), 0, "estação desmontada: os drones do hangar somem")
