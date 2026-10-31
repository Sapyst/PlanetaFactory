extends Caso
## Limpeza nova (fase 2.6; estudo_limpeza_2x2.py, estudo_purificador_atmosferico.py, estudo_viveiro2_semeador.py e
## estudo_biodigestor_tratamento.py via arte/estudos/conv_limpeza.py), cada uma com efeito nos sistemas do ambiente:
## coletor 2 (sujeira, óleo e cinza em 10 m → resíduo), purificadores (poluição do chunk; o atmosférico condensa em
## resíduo), viveiro 2 (espécie do bioma, 2× mais rápido), semeador de bioma (chão queimado e árvores carbonizadas),
## biodigestor (resíduo + água → biomassa + seiva), estação de tratamento (água suja em 16 m → água limpa) e a
## recuperação de solo (aplainar limpa o chão). O pacote ecológico passa a ser pedido por essas pesquisas.

const NOMES := {"coletor_lixo_2": Vector2i(2, 2), "purificador_ar": Vector2i(2, 2), "purificador_ar_2": Vector2i(3, 3),
		"viveiro_2": Vector2i(2, 2), "semeador_bioma": Vector2i(3, 3), "biodigestor": Vector2i(3, 3), "estacao_tratamento": Vector2i(3, 3)}


func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var f := Fabrica.new(m)
	var a := AmbienteVivo.new(g, m, 3)
	a.poluicao = Poluicao.new(g)
	return [g, m, f, a]


## Máquina ligada sem rede elétrica (o teste é do ambiente) por n segundos.
func _rodar(a: AmbienteVivo, f: Fabrica, ids: Array, n: int, seiva := false) -> void:
	for i in n:
		for id in ids:
			var mq: Maquina = f.maquinas[id]
			mq.energia = 1.0
			if seiva:
				mq.fluidos["seiva"] = 100.0
			mq.tick(1.0)
		a.tick(1.0, f, null)


func _lugar(m: MapaOcupacao, nome: String, perto: Vector2i) -> Vector2i:
	for r in 40:
		for dx in range(-r, r + 1):
			for dy in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var t := perto + Vector2i(dx, dy)
				for x in range(-1, 4):
					for y in range(-1, 4):
						m.limpar_obstaculo(t + Vector2i(x, y))
				if m.motivo_bloqueio(nome, t, 0) == "":
					return t
	return Vector2i(9999, 9999)


func test_dados_e_modelos() -> void:
	var estudos := {"coletor_lixo_2": "estudo_limpeza_2x2.py", "purificador_ar": "estudo_limpeza_2x2.py",
			"purificador_ar_2": "estudo_purificador_atmosferico.py", "viveiro_2": "estudo_viveiro2_semeador.py",
			"semeador_bioma": "estudo_viveiro2_semeador.py", "biodigestor": "estudo_biodigestor_tratamento.py",
			"estacao_tratamento": "estudo_biodigestor_tratamento.py"}
	for n in NOMES:
		var md: Dictionary = Registro.modelos.get(n, {})
		igual(md.get("estudo", ""), estudos[n], "convertido do estudo: " + n)
		igual(Registro.area(n), NOMES[n], "área: " + n)
		verificar(md.get("anima", false), "anima (laço do estudo): " + n)
		verificar(int(md.tris) <= 16500, "orçamento: %s %d" % [n, md.tris])
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % n), "ícone: " + n)
		verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Limpeza" and n in cat.pecas), "aba Limpeza: " + n)
		verificar(not Registro.progressao.custos.get(n, {}).is_empty(), "custo: " + n)
		igual(Fiacao.papel(n), "consumo", "precisa de energia: " + n)
	var canos := float(Registro.modelos.cano_reto.portas[0].pos[2])
	var p_v: Dictionary = Registro.modelos.viveiro_2.portas[0]
	igual(p_v.nome, "PORTA_FLUIDO_ENT_O0", "viveiro 2: seiva pelo oeste (como o viveiro 1)")
	var p_s: Dictionary = Registro.modelos.semeador_bioma.portas[0]
	igual(p_s.nome, "PORTA_FLUIDO_ENT_O1", "semeador: seiva pelo oeste, tile do meio")
	perto(float(p_s.pos[1]), 0.0, 1e-6, "semeador: no eixo do tile (o estudo tinha 0,38)")
	perto(float(p_s.pos[2]), canos, 0.01, "semeador: na altura dos canos")
	var nb: Array = Registro.modelos.biodigestor.portas.map(func(p): return p.nome)
	verificar("PORTA_FLUIDO_ENT_S0" in nb and "PORTA_FLUIDO_SAI_L1" in nb, "biodigestor: água pelo sul, seiva pelo leste (%s)" % str(nb))
	igual(Registro.modelos.estacao_tratamento.portas[0].nome, "PORTA_FLUIDO_SAI_L0", "tratamento: água limpa pelo leste")
	verificar(Registro.estruturas.estacao_tratamento.get("tomada_agua", false), "tratamento: tomada na água como a bomba")
	verificar(ResourceLoader.exists("res://assets/icones/itens/residuo.png"), "ícone do resíduo")
	verificar(Registro.modelos.has(Registro.itens.residuo.get("modelo_de", "")), "resíduo tem modelo (derivado) na esteira")


func test_pesquisas_usam_o_pacote_ecologico() -> void:
	var p := Pesquisa.new()
	for id in ["coletor_lixo_2", "purificador_ar", "viveiro_2", "biodigestor", "recuperar_solo", "purificador_ar_2",
			"estacao_tratamento", "restauracao_bioma"]:
		verificar(p.jogavel(id), "jogável: " + id)
		verificar("pacote_ecologico" in p.tipos(id), "pede pacote ecológico: " + id)
	p.concluidas = {"limpeza": true, "reflorestar": true}
	verificar(not p.disponivel("coletor_lixo_2"), "coletor 2 espera a bioquímica")
	p.concluidas["bioquimica"] = true
	for id in ["coletor_lixo_2", "purificador_ar", "viveiro_2"]:
		verificar(p.disponivel(id), "com bioquímica: " + id)
	igual(p.custo("coletor_lixo_2"), {"pacote_pesquisa": 40, "pacote_automacao": 40, "pacote_quimico": 40, "pacote_ecologico": 40}, "custo da árvore")
	verificar(not p.disponivel("biodigestor"), "biodigestor espera o coletor 2")
	p.concluidas["coletor_lixo_2"] = true
	verificar(p.disponivel("biodigestor"), "biodigestor")
	p.concluidas["viveiro_2"] = true
	verificar(p.disponivel("recuperar_solo"), "recuperação de solo: viveiro 2 + coletor 2")
	p.concluidas.merge({"recuperar_solo": true, "ciencia_tempestade": true, "purificador_ar": true, "filtro_agua_limpa": true})
	verificar(p.disponivel("restauracao_bioma"), "semeador de bioma")
	verificar(p.disponivel("purificador_ar_2"), "purificador atmosférico")
	verificar(p.jogavel("refinador_2"), "refinador 2 jogável (lote 10)")
	verificar(not p.disponivel("estacao_tratamento"), "tratamento pede o refinador 2 pesquisado")
	verificar(not p.em_desenvolvimento("estacao_tratamento"), "e não está mais em desenvolvimento")
	p.concluidas.merge({"quimica": true, "refinador_2": true})
	verificar(p.disponivel("estacao_tratamento"), "com o refinador 2: tratamento pesquisável")
	for par in [["restauracao_bioma", "semeador_bioma"], ["estacao_tratamento", "estacao_tratamento"], ["purificador_ar_2", "purificador_ar_2"]]:
		var q := Pesquisa.new()
		q.concluidas = {par[0]: true}
		verificar(q.peca_liberada(par[1]), "%s libera %s" % par)


func test_coletor_2_cinza_e_residuo() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var t := _lugar(m, "coletor_lixo_2", Vector2i(2, 2))
	var id := m.colocar("coletor_lixo_2", t, 0)
	f.reconstruir()
	var c := t + Vector2i(1, 1)
	for x in range(-12, 13):
		for y in range(-12, 13):
			a.somar(c + Vector2i(x, y), AmbienteVivo.SUJ, 0.5)
			a.somar(c + Vector2i(x, y), AmbienteVivo.QUEIM, 0.6)
	var tira := func(): return f.maquinas[id].pegar_para_braco("")
	var residuos := 0
	for i in 60:
		_rodar(a, f, [id], 1)
		while tira.call() == "residuo":
			residuos += 1
	verificar(a.valor(c + Vector2i(8, 0), AmbienteVivo.SUJ) < 0.4, "aspira a 8 m (o coletor 1 só alcança 6): %.3f" % a.valor(c + Vector2i(8, 0), AmbienteVivo.SUJ))
	verificar(a.valor(c + Vector2i(2, 2), AmbienteVivo.QUEIM) < 0.4, "recolhe a cinza (queimado) também")
	verificar(a.valor(c + Vector2i(12, 0), AmbienteVivo.SUJ) > 0.45, "fora dos 10 m fica")
	verificar(residuos >= 20, "compacta o que recolheu em resíduo (%d)" % residuos)
	igual(f.maquinas[id].receita_id, "coletar_lixo", "mesma receita do coletor 1")


func test_purificadores() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var p1 := m.colocar("purificador_ar", _lugar(m, "purificador_ar", Vector2i(4, 4)), 0)
	var p2 := m.colocar("purificador_ar_2", _lugar(m, "purificador_ar_2", Vector2i(4 + 64, 4)), 0)
	f.reconstruir()
	var k1 := Grade.chunk_de(Vector2i(Grade.centro_da_area(m.estruturas[p1].minimo, m.estruturas[p1].area, 0).floor()))
	var k2 := Grade.chunk_de(Vector2i(Grade.centro_da_area(m.estruturas[p2].minimo, m.estruturas[p2].area, 0).floor()))
	verificar(k1 != k2, "chunks diferentes")
	a.poluicao.valores[k1] = 100.0
	a.poluicao.valores[k2] = 100.0
	_rodar(a, f, [p1, p2], 60)
	perto(a.poluicao.em_chunk(k1), 94.0, 0.05, "purificador de ar: 6 por minuto")
	perto(a.poluicao.em_chunk(k2), 60.0, 0.05, "atmosférico: 40 por minuto")
	igual(int(f.maquinas[p2].saidas.get("residuo", 0)), 2, "atmosférico: 40 absorvidos = 2 resíduos (1 a cada 20)")
	igual(int(f.maquinas[p1].saidas.get("residuo", 0)), 0, "o de ar não faz resíduo")
	# sem energia não purifica
	f.maquinas[p1].energia = 0.0
	for i in 10:
		f.maquinas[p1].tick(1.0)
		a.tick(1.0, f, null)
	perto(a.poluicao.em_chunk(k1), 94.0, 0.05, "desligado não absorve")


func _pantano(g: GeradorMundo, m: MapaOcupacao) -> Vector2i:
	for x in range(-400, 400, 9):
		for y in range(-400, 400, 9):
			var q := Vector2i(x, y)
			if g.bioma(q) != "pantano" or g.terreno(q) != GeradorMundo.Terreno.TERRA:
				continue
			for dx in range(-1, 4):
				for dy in range(-1, 4):
					m.limpar_obstaculo(q + Vector2i(dx, dy))
			if m.motivo_bloqueio("viveiro_2", q, 0) == "" and g.bioma(q + Vector2i(1, 1)) == "pantano":
				return q
	return Vector2i(9999, 9999)


func test_viveiro_2_especie_e_crescimento() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	# um lugar de pântano (salgueiro) com chão livre em volta
	var t := _pantano(g, m)
	verificar(t.x != 9999, "achou pântano")
	if t.x == 9999:
		return
	igual(a.especie_do_bioma(t), "arv_salgueiro", "espécie do pântano: salgueiro")
	var id := m.colocar("viveiro_2", t, 0)
	f.reconstruir()
	perto(f.maquinas[id].velocidade, 2.0, 1e-6, "planta no dobro do ritmo")
	_rodar(a, f, [id], 30, true)
	verificar(a.plantas.size() >= 3, "plantou (%d mudas em 30 s; o viveiro 1 faria 2)" % a.plantas.size())
	var com_especie := 0
	for p in a.plantas:
		if a.especies.has(p):
			com_especie += 1
			perto(float(a.rapidas.get(p, 1.0)), 2.0, 1e-6, "muda 2× mais rápida")
	verificar(com_especie >= 1, "mudas da espécie do bioma (%d)" % com_especie)
	# crescimento: 2× o de uma muda comum no mesmo chão
	var q2 := Vector2i(t.x + 40, t.y)
	a.plantas.clear()
	a.especies.clear()
	a.rapidas.clear()
	a.plantas[q2] = 0.05
	a.plantas[q2 + Vector2i(0, 3)] = 0.05
	a.rapidas[q2] = 2.0
	for i in 20:
		a._plantas()
	var normal := float(a.plantas[q2 + Vector2i(0, 3)]) - 0.05
	var rapida := float(a.plantas[q2]) - 0.05
	perto(rapida, normal * 2.0, 1e-4, "cresce 2× mais rápido")


func test_semeador_de_bioma() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var t := _lugar(m, "semeador_bioma", Vector2i(10, 10))
	var id := m.colocar("semeador_bioma", t, 0)
	f.reconstruir()
	var c := t + Vector2i(1, 1)
	for x in range(-10, 11):
		for y in range(-10, 11):
			a.somar(c + Vector2i(x, y), AmbienteVivo.QUEIM, 0.9)
	m.arvores[c + Vector2i(5, 0)] = {"e": "queimada"}
	m.arvores[c + Vector2i(-6, 2)] = {"e": "caida", "dir": Vector2.RIGHT}
	m.arvores[c + Vector2i(40, 0)] = {"e": "queimada"}
	_rodar(a, f, [id], 40, true)
	verificar(a.valor(c + Vector2i(4, 4), AmbienteVivo.QUEIM) < 0.5, "tira o queimado do chão (%.2f)" % a.valor(c + Vector2i(4, 4), AmbienteVivo.QUEIM))
	verificar(not m.arvores.has(c + Vector2i(5, 0)) and not m.arvores.has(c + Vector2i(-6, 2)), "árvores carbonizada e caída voltaram")
	verificar(m.arvores.has(c + Vector2i(40, 0)), "fora dos 14 m continua queimada")
	verificar(a.plantas.size() >= 2, "plantou mudas no chão queimado (%d)" % a.plantas.size())


func test_biodigestor() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var t := _lugar(m, "biodigestor", Vector2i(-20, 8))
	var id := m.colocar("biodigestor", t, 0)
	f.reconstruir()
	var mq: Maquina = f.maquinas[id]
	igual(mq.receita_id, "biodigerir")
	verificar(mq.aceita("residuo"), "aceita resíduo por braço")
	for i in 8:
		mq.receber("residuo")
	mq.receber_fluido("agua", 80.0)
	mq.energia = 1.0
	for i in 12:
		mq.tick(1.0)
	igual(int(mq.saidas.get("biomassa", 0)), 2, "2 biomassas por ciclo")
	perto(float(mq.fluidos.get("seiva", 0.0)), 30.0, 0.01, "30 de seiva por ciclo")
	igual(int(mq.entradas.get("residuo", 0)), 0, "8 resíduos = 2 ciclos (o 2º em andamento)")


## Margem com água ao sul de uma estação de tratamento 3×3 (tomada); suja o rio em volta e devolve a soma da água suja
## depois de 30 s com a estação ligada ou não (a correnteza também leva a sujeira: o teste compara os dois).
func _rio_tratado(ligada: bool) -> Array:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var t := Vector2i(9999, 0)
	for x in range(-300, 300, 3):
		for y in range(-300, 300, 3):
			var q := Vector2i(x, y)
			if t.x != 9999 or g.terreno(q + Vector2i(1, -1)) != GeradorMundo.Terreno.RIO:
				continue
			for dx in 3:
				for dy in 3:
					m.limpar_obstaculo(q + Vector2i(dx, dy))
			if m.motivo_bloqueio("estacao_tratamento", q, 0) == "":
				t = q
	if t.x == 9999:
		return []
	var id := m.colocar("estacao_tratamento", t, 0)
	f.reconstruir()
	var c := t + Vector2i(1, 1)
	var agua: Array[Vector2i] = []
	for x in range(-14, 15):
		for y in range(-14, 15):
			var q := c + Vector2i(x, y)
			if g.eh_agua(g.terreno(q)):
				a.somar(q, AmbienteVivo.AGUA, 0.8)
				agua.append(q)
	var mq: Maquina = f.maquinas[id]
	for i in 30:
		mq.energia = 1.0 if ligada else 0.0
		mq.tick(1.0)
		a.tick(1.0, f, null)
	var soma := 0.0
	for q in agua:
		soma += a.valor(q, AmbienteVivo.AGUA)
	return [soma, agua.size(), mq]


func test_tratamento_limpa_o_rio() -> void:
	var lig := _rio_tratado(true)
	var des := _rio_tratado(false)
	verificar(not lig.is_empty(), "achou margem com a água ao sul")
	if lig.is_empty():
		return
	verificar(int(lig[1]) > 5, "tem rio em volta (%d tiles)" % lig[1])
	verificar(float(lig[0]) < float(des[0]) * 0.6, "ligada limpa a água suja em 16 m (%.1f contra %.1f só com a correnteza)" % [lig[0], des[0]])
	var mq: Maquina = lig[2]
	igual(mq.receita_id, "tratar_agua")
	verificar(float(mq.fluidos.get("agua_limpa", 0.0)) > 0.0, "solta água limpa")
	verificar(mq.estado == Maquina.Estado.TRABALHANDO, "sem cano a sobra volta ao rio e ela continua")


func test_recuperar_solo() -> void:
	var b := _base()
	var a: AmbienteVivo = b[3]
	var t := Vector2i(3, 3)
	a.somar(t, AmbienteVivo.SUJ, 0.7)
	a.somar(t, AmbienteVivo.OLEO, 0.5)
	a.somar(t, AmbienteVivo.QUEIM, 0.9)
	a.somar(t + Vector2i(1, 0), AmbienteVivo.SUJ, 0.7)
	a.recuperar(t)
	perto(a.valor(t, AmbienteVivo.SUJ) + a.valor(t, AmbienteVivo.OLEO) + a.valor(t, AmbienteVivo.QUEIM), 0.0, 1e-6, "tile recuperado: limpo")
	perto(a.valor(t + Vector2i(1, 0), AmbienteVivo.SUJ), 0.7, 1e-6, "o vizinho não")
	verificar(Registro.progressao.pesquisas.recuperar_solo.get("acoes", []).has("recuperar_solo"), "a pesquisa liga a ação")
