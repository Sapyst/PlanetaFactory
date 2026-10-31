extends Caso
## Noite (pedido de Sapyst): cor da energia por rede (RedeEnergia), postes e faíscas só com energia passando, luz das
## estruturas só com a máquina ativa, e os limites do conjunto de luzes.


func _rede(base_kw: float, ger_kw: float, consumo: float) -> RedeEnergia:
	var r := RedeEnergia.new()
	r.adicionar(1, consumo)
	if base_kw > 0.0:
		var b := r.adicionar(2, -base_kw, 1.0e12, true)
		b.base = true
		r.ligar(1, 2)
	if ger_kw > 0.0:
		r.adicionar(3, -ger_kw, 1000.0)
		r.ligar(1, 3)
	r.calcular()
	r.tick(1.0)
	return r


func test_base_maior_fica_roxo() -> void:
	igual(_rede(260.0, 0.0, 100.0).origem_de(1), RedeEnergia.BASE, "só o núcleo")
	igual(_rede(260.0, 900.0, 200.0).origem_de(1), RedeEnergia.BASE, "livre primeiro: 200 kW entregues, todos do núcleo")


func test_geradores_maiores_ficam_amarelo() -> void:
	igual(_rede(0.0, 900.0, 100.0).origem_de(1), RedeEnergia.GERADORES, "só gerador")
	igual(_rede(260.0, 900.0, 1000.0).origem_de(1), RedeEnergia.GERADORES, "260 do núcleo contra 740 do gerador")


func test_sem_mistura_e_sem_carga() -> void:
	var r := _rede(260.0, 900.0, 0.0)
	igual(r.origem_de(1), "", "ninguém puxando: nada acende")
	verificar(not r.fluxo_em(1) and not r.fluxo_em(2), "sem fluxo em nenhum nó")
	igual(RedeEnergia.decidir_origem(0.0, 0.0), "", "zero é sem origem")
	igual(RedeEnergia.decidir_origem(0.0, 0.0, RedeEnergia.BASE), "", "zero é sem origem mesmo com cor anterior")
	igual(_rede(0.0, 0.0, 100.0).origem_de(1), "", "sem fonte")


func test_renovavel_e_acumulador_contam_como_geradores() -> void:
	var r := RedeEnergia.new()
	r.adicionar(1, 400.0)
	var nu := r.adicionar(2, -100.0, 1.0e12, true)
	nu.base = true
	r.adicionar(3, -300.0, 1.0e12, true)              # painel solar: livre, mas não é a base
	r.ligar(1, 2)
	r.ligar(1, 3)
	r.calcular()
	r.tick(1.0)
	igual(r.origem_de(1), RedeEnergia.GERADORES, "painel entrega mais que o núcleo")
	var q := RedeEnergia.new()
	q.adicionar(1, 400.0)
	var b := q.adicionar(2, -100.0, 1.0e12, true)
	b.base = true
	var a := q.adicionar(3, 0.0)
	a.acum_cap = 100.0
	a.acum_kw = 500.0
	a.acum_mj = 100.0
	q.ligar(1, 2)
	q.ligar(1, 3)
	q.calcular()
	q.tick(1.0)
	igual(q.origem_de(1), RedeEnergia.GERADORES, "acumulador descarregando 300 contra 100 do núcleo")
	# carregando acumulador com energia do núcleo continua sendo do núcleo
	var c := RedeEnergia.new()
	c.adicionar(1, 10.0)
	var bc := c.adicionar(2, -260.0, 1.0e12, true)
	bc.base = true
	var ac := c.adicionar(3, 0.0)
	ac.acum_cap = 100.0
	ac.acum_kw = 500.0
	c.ligar(1, 2)
	c.ligar(1, 3)
	c.calcular()
	c.tick(1.0)
	igual(c.origem_de(1), RedeEnergia.BASE, "acumulador carregando do núcleo")


func test_histerese() -> void:
	var D := RedeEnergia.decidir_origem(100.0, 105.0, RedeEnergia.BASE)
	igual(D, RedeEnergia.BASE, "geradores 5% acima: fica na base")
	igual(RedeEnergia.decidir_origem(100.0, 111.0, RedeEnergia.BASE), RedeEnergia.GERADORES, "11% acima: vira")
	igual(RedeEnergia.decidir_origem(105.0, 100.0, RedeEnergia.GERADORES), RedeEnergia.GERADORES, "base 5% acima: fica nos geradores")
	igual(RedeEnergia.decidir_origem(111.0, 100.0, RedeEnergia.GERADORES), RedeEnergia.BASE, "11% acima: vira")
	igual(RedeEnergia.decidir_origem(105.0, 100.0), RedeEnergia.BASE, "sem cor anterior vale o maior")
	# na rede: o consumo oscila em volta do empate e a cor não pisca
	var r := RedeEnergia.new()
	var m := r.adicionar(1, 200.0)
	var b := r.adicionar(2, -100.0, 1.0e12, true)
	b.base = true
	r.adicionar(3, -500.0, 1.0e6)
	r.ligar(1, 2)
	r.ligar(1, 3)
	r.calcular()
	r.tick(1.0)
	igual(r.origem_de(1), RedeEnergia.BASE, "empate 100 × 100: base")
	var trocas := 0
	var antes := r.origem_de(1)
	for i in 200:
		m.kw = 200.0 + 8.0 * sin(i * 0.7)              # 96–104 de gerador contra 100 da base
		r.tick(0.1)
		if r.origem_de(1) != antes:
			trocas += 1
			antes = r.origem_de(1)
	igual(trocas, 0, "dentro da margem não troca")
	m.kw = 400.0
	r.tick(0.1)
	igual(r.origem_de(1), RedeEnergia.GERADORES, "passou a margem: amarelo")
	m.kw = 0.0
	r.tick(0.1)
	igual(r.origem_de(1), "", "parou de passar energia: apaga")
	m.kw = 201.0
	r.tick(0.1)
	igual(r.origem_de(1), RedeEnergia.GERADORES, "voltou perto do empate: segura a última cor")
	r.calcular()
	r.tick(0.1)
	igual(r.origem_de(1), RedeEnergia.GERADORES, "recalcular as redes não perde a cor")


func test_rede_refeita_herda_a_cor() -> void:
	var v := RedeEnergia.new()
	v.adicionar(1, 400.0)
	var b := v.adicionar(2, -195.0, 1.0e12, true)
	b.base = true
	v.adicionar(3, -500.0, 1.0e6)
	v.ligar(1, 2)
	v.ligar(1, 3)
	v.calcular()
	v.tick(1.0)
	igual(v.origem_de(1), RedeEnergia.GERADORES, "205 contra 195")
	var n := RedeEnergia.new()
	n.adicionar(1, 390.0)
	var b2 := n.adicionar(2, -195.0, 1.0e12, true)
	b2.base = true
	n.adicionar(3, -500.0, 1.0e6)
	n.ligar(1, 2)
	n.ligar(1, 3)
	n.calcular()
	n.herdar_origem(v)
	n.tick(1.0)
	igual(n.origem_de(1), RedeEnergia.GERADORES, "empate 195 × 195 em rede nova: mantém a cor de antes")


func test_fluxo_so_no_caminho_de_verdade() -> void:
	var r := RedeEnergia.new()
	r.adicionar(1, -500.0, 1000.0)      # gerador
	r.adicionar(2, 0.0)                 # poste
	r.adicionar(3, 100.0)               # máquina
	r.adicionar(4, 0.0)                 # poste de ramal morto
	r.adicionar(5, 0.0)                 # poste na ponta do ramal
	r.adicionar(6, 0.0)                 # máquina desligada (0 kW)
	r.adicionar(7, -300.0, 0.0)         # gerador sem combustível
	r.ligar(1, 2)
	r.ligar(2, 3)
	r.ligar(2, 4)
	r.ligar(4, 5)
	r.ligar(4, 6)
	r.ligar(2, 7)
	r.calcular()
	r.tick(1.0)
	r.atualizar_fluxo()
	for id in [1, 2, 3]:
		verificar(r.fluxo_em(id), "passa em %d" % id)
	for id in [4, 5, 6, 7]:
		verificar(not r.fluxo_em(id), "não passa em %d" % id)


func _base_fabrica() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(180, 215):
		for y in range(-14, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	return [m, Fabrica.new(m)]


func _luzes(m: MapaOcupacao, f: Fabrica) -> DesenhoLuzes:
	var d := DesenhoLuzes.new()
	d.mapa = m
	d.fabrica = f
	d._d = Registro.luzes
	return d


func test_luz_so_com_a_maquina_ativa() -> void:
	var b := _base_fabrica()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	var g := m.colocar("gerador", Vector2i(190, 0), 0)
	var p := m.colocar("poste_energia", Vector2i(194, 0), 0)
	var ponta := m.colocar("poste_energia", Vector2i(190, -10), 0)
	var maq := m.colocar("montadora_quantica", Vector2i(197, 0), 0)
	verificar(g >= 0 and p >= 0 and maq >= 0 and ponta >= 0, "tudo coube")
	f.reconstruir()
	var d := _luzes(m, f)
	var fg := {"id": g, "tipo": "fogo", "regra": Registro.estruturas.gerador}
	var fp := {"id": p, "tipo": "poste", "regra": {}}
	var fm := {"id": maq, "tipo": "cristal", "regra": Registro.estruturas.montadora_quantica}
	perto(d.forca_alvo(fg), 0.0, 1e-4, "gerador sem carvão: apagado")
	perto(d.forca_alvo(fp), 0.0, 1e-4, "poste sem energia: apagado")
	perto(d.forca_alvo(fm), 0.0, 1e-4, "cristal sem energia: apagado")
	f.combustivel[g] = 1000.0
	for i in 40:
		f.tick(1.0 / 30.0)
	igual(f.rede.origem_de(p), RedeEnergia.GERADORES, "rede do gerador")
	perto(d.forca_alvo(fg), 1.0, 1e-4, "gerador queimando: aceso")
	verificar(d.forca_alvo(fp) > 0.0, "poste aceso")
	var pouca := d.forca_alvo(fp)
	verificar(pouca < 1.0, "carga parcial, luz parcial")
	perto(d.forca_alvo(fm), float(Registro.luzes.ocioso_cristal), 1e-4, "com energia e parada: espera fraca")
	m.estruturas[maq]["desligada"] = true
	perto(d.forca_alvo(fm), 0.0, 1e-4, "desligada: apagada")
	m.estruturas[g]["desligada"] = true
	perto(d.forca_alvo(fg), 0.0, 1e-4, "gerador desligado: apagado")
	d.free()


func test_escuro_e_escolha() -> void:
	perto(DesenhoLuzes.fator_escuro(0.0), 1.0, 1e-4, "noite fechada")
	perto(DesenhoLuzes.fator_escuro(1.0), 0.0, 1e-4, "meio-dia")
	perto(DesenhoLuzes.fator_escuro(1.0, 0.0), 0.0, 1e-4, "meio-dia de tempestade ainda não é noite")
	verificar(DesenhoLuzes.fator_escuro(0.3, 0.0) > DesenhoLuzes.fator_escuro(0.3, 1.0), "céu fechado escurece antes")
	var lista := []
	for i in 10:
		lista.append({"id": i, "p": Vector2(i * 2.0, 0.0), "w": 0.0})
	var e := DesenhoLuzes.escolher(lista, Vector2.ZERO, 3)
	igual(e.size(), 3, "só o conjunto")
	igual(e[0].id, 0, "o mais perto primeiro")
	lista[4].w = 1.0                                     # já tem luz: não perde para quem está só um pouco mais perto
	var e2 := DesenhoLuzes.escolher(lista, Vector2(7.0, 0.0), 2)
	verificar(e2.any(func(x): return x.id == 4), "folga para não trocar à toa")
	for t in [0.0, 1.3, 7.7]:
		for k in ["fogo", "cristal", "choque", "lampada"]:
			var v := DesenhoLuzes.pulso(k, t, 0.4)
			verificar(v > 0.0 and v <= 1.0, "pulso em 0..1")


func test_dados() -> void:
	var d: Dictionary = Registro.luzes
	verificar(int(d.pc.luzes) <= 8 and int(d.celular.luzes) <= int(d.pc.luzes), "luzes dentro do limite do Mobile")
	verificar(int(d.celular.halos) <= int(d.pc.halos) and int(d.celular.faiscas) <= int(d.pc.faiscas) and int(d.pc.faiscas) <= 8, "limites")
	for nome in d.maquinas:
		var e: Dictionary = d.maquinas[nome]
		verificar(Registro.modelos.has(nome), "%s existe" % nome)
		verificar(d.forca_real.has(e.tipo) and d.cores.has(e.tipo), "%s: tipo %s" % [nome, e.tipo])
		var dims: Array = Registro.modelos[nome].dims
		verificar(float(e.pos[1]) <= float(dims[2]) + 0.1, "%s: luz dentro da altura do modelo" % nome)
		verificar(absf(float(e.pos[0])) <= float(dims[0]) * 0.6 and absf(float(e.pos[2])) <= float(dims[1]) * 0.6, "%s: luz dentro do modelo" % nome)
		for ch in e.get("chamas", []):
			verificar(float(ch[1]) <= float(dims[2]) + 0.4, "%s: chama na altura do modelo" % nome)
	for nome in ["fornalha", "gerador", "refinador", "refinador_2", "biodigestor"]:
		verificar(d.maquinas[nome].has("chamas") and d.maquinas[nome].tipo == "fogo", "%s tem labareda" % nome)
	for nome in d.postes:
		verificar(Registro.estruturas[nome].grupo == "poste", "%s é poste" % nome)


func test_faisca_so_em_cabo_com_energia() -> void:
	var b := _base_fabrica()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	var g := m.colocar("gerador", Vector2i(190, 0), 0)
	var maq := m.colocar("montadora_quantica", Vector2i(203, 0), 0)
	for x in [194, 199]:
		m.colocar("poste_energia", Vector2i(x, 0), 0)
	f.reconstruir()
	var d := DesenhoFios.new()
	d.mapa = m
	d.fabrica = f
	d._ready()
	d.refazer()
	verificar(not d._lista.is_empty(), "tem cabo")
	verificar(maq >= 0, "máquina coube")
	var maximo := 0
	for i in 900:
		d._atualizar_faiscas(1.0 / 30.0)
		maximo = maxi(maximo, d.faiscas_em_cena())
	igual(maximo, 0, "sem energia: nenhuma faísca")
	f.combustivel[g] = 100000.0
	f.tick(1.0 / 30.0)
	d._lista = d._lista.duplicate()
	for i in 200:                                       # muitos cabos: testa o limite
		d._lista.append(d._lista[0])
	var vistas := 0
	var cores := {}
	for i in 900:
		d._atualizar_faiscas(1.0 / 30.0)
		maximo = maxi(maximo, d.faiscas_em_cena())
		vistas += d.faiscas_em_cena()
		for x in d._faiscas:
			cores[x.cor] = true
	verificar(vistas > 0, "com energia aparece")
	verificar(maximo <= int(Registro.luzes.pc.faiscas), "limite em cena (%d)" % maximo)
	igual(cores.size(), 1, "uma cor por rede, sem mistura")
	verificar(cores.has(d._cor_geradores), "amarelo: vem do gerador")
	var raro := DesenhoFios.new()
	raro.mapa = m
	raro.fabrica = f
	raro._ready()
	raro.refazer()
	var quadros_com := 0
	for i in 1800:
		raro._atualizar_faiscas(1.0 / 30.0)
		quadros_com += 1 if raro.faiscas_em_cena() > 0 else 0
	verificar(quadros_com < 900, "rara: poucos cabos quase sempre apagados (%d de 1800 quadros)" % quadros_com)
	d.free()
	raro.free()
