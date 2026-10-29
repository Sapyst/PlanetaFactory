extends Caso
## Variações e opções internas: fontes livres (solar, eólica) antes do combustível, acumulador, liga/desliga,
## modos eco/turbo, baú grande e limite de baú, reparo.

func test_fonte_livre_antes_do_combustivel() -> void:
	var r := RedeEnergia.new()
	r.adicionar(1, 400.0)
	r.adicionar(2, -300.0, 1.0e12, true)
	var g := r.adicionar(3, -450.0, 10.0)
	r.ligar(1, 2)
	r.ligar(1, 3)
	r.calcular()
	r.tick(1.0)
	perto(r.satisfacao(1), 1.0, 1e-4, "400 kW atendidos")
	perto(g.combustivel_mj, 10.0 - 0.1, 1e-4, "gerador só cobriu os 100 kW que faltaram")
	perto(float(r.estat_de(1).gera), 400.0, 1e-3, "estatística: gera 400")
	perto(float(r.estat_de(1).gera_max), 750.0, 1e-3, "podia 750")


func test_acumulador_carrega_e_descarrega() -> void:
	var r := RedeEnergia.new()
	var maq := r.adicionar(1, 100.0)
	var sol := r.adicionar(2, -300.0, 1.0e12, true)
	var a := r.adicionar(3, 0.0)
	a.acum_cap = 10.0
	a.acum_kw = 150.0
	r.ligar(1, 2)
	r.ligar(1, 3)
	r.calcular()
	r.tick(10.0)
	perto(a.acum_mj, 1.5, 1e-3, "sobra de 200 kW, mas carrega no máximo 150 kW: 1,5 MJ em 10 s")
	verificar(r.tem_fonte(1), "acumulador conta como fonte")
	sol.kw = 0.0                                     # noite/nublado: sem geração
	r.tick(5.0)
	perto(r.satisfacao(1), 1.0, 1e-4, "acumulador segura a máquina")
	perto(a.acum_mj, 1.0, 1e-3, "gastou 100 kW × 5 s")
	maq.kw = 400.0
	r.tick(1.0)
	perto(r.satisfacao(1), 150.0 / 400.0, 1e-3, "descarga limitada a 150 kW")
	for i in 20:
		r.tick(1.0)
	perto(a.acum_mj, 0.0, 1e-6, "esvaziou")
	perto(r.satisfacao(1), 0.0, 1e-6, "sem nada: parada")


func _fab() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 20):
		for y in range(-2, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return [m, Fabrica.new(m)]


func _por(m: MapaOcupacao, nome: String, t: Vector2i) -> int:
	var id := m.colocar(nome, t, 0)
	Fiacao.ligar_novo(m, id)
	return id


func test_solar_e_eolica_seguem_o_clima() -> void:
	var b := _fab()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	var p := _por(m, "painel_solar", Vector2i(0, 0))
	var t := _por(m, "turbina_eolica", Vector2i(0, 4))
	_por(m, "poste_energia", Vector2i(3, 2))
	var mq := _por(m, "montadora", Vector2i(5, 1))
	f.reconstruir()
	verificar(f.rede.tem_fonte(mq), "montadora ligada às renováveis")
	f.sol = 1.0
	f.vento = 1.0
	f.tick(1.0)
	perto(f.kw_de(p), -300.0, 1e-3, "sol pleno: 300 kW")
	perto(f.kw_de(t), -200.0, 1e-3, "vento forte: 200 kW")
	perto(f.rede.satisfacao(mq), 1.0, 1e-3, "500 kW para 150 kW")
	verificar(not f.combustivel.has(p) and not f.combustivel.has(t), "renovável não usa combustível")
	f.sol = 0.0
	f.vento = 0.15
	f.tick(1.0)
	perto(f.rede.satisfacao(mq), 30.0 / 150.0, 1e-3, "sem sol e quase sem vento: 30 de 150 kW")


func test_desligar_e_modos() -> void:
	var b := _fab()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	_por(m, "turbina_eolica", Vector2i(0, 0))
	_por(m, "poste_energia", Vector2i(3, 1))
	var mq := _por(m, "montadora", Vector2i(5, 0))
	f.vento = 1.0
	f.reconstruir()
	f.escolher_receita(mq, "engrenagem")
	perto(f.kw_de(mq), 150.0, 1e-3, "normal: 150 kW")
	m.estruturas[mq]["modo"] = "turbo"
	f.reconstruir()
	perto(f.kw_de(mq), 300.0, 1e-3, "turbo: dobro de energia")
	perto(f.maquinas[mq].velocidade, 0.75 * 1.5, 1e-4, "turbo: 1,5× mais rápida")
	m.estruturas[mq]["modo"] = "eco"
	f.reconstruir()
	perto(f.kw_de(mq), 60.0, 1e-3, "eco: 40% da energia")
	perto(f.maquinas[mq].velocidade, 0.75 * 0.5, 1e-4, "eco: metade da velocidade")
	m.estruturas[mq]["desligada"] = true
	f.reconstruir()
	f.maquinas[mq].entradas = {"placa_ferro": 4}
	f.maquinas[mq].acordar()
	for i in 5:
		f.tick(1.0)
	perto(f.kw_de(mq), 0.0, 1e-6, "desligada não consome")
	igual(f.maquinas[mq].estado, Maquina.Estado.SEM_ENERGIA, "desligada não trabalha")
	m.estruturas[mq].erase("desligada")
	f.reconstruir()
	for i in 3:
		f.tick(1.0)
	igual(f.maquinas[mq].estado, Maquina.Estado.TRABALHANDO, "religada volta a trabalhar")


func test_bau_grande_e_limite() -> void:
	var b := _fab()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	var bg := m.colocar("bau_grande", Vector2i(0, 0), 0)
	var bp := m.colocar("bau", Vector2i(4, 0), 0)
	f.reconstruir()
	igual(f.capacidade_bau(bg), 6400, "baú grande: 6400 itens")
	igual(f.capacidade_bau(bp), 1600, "baú: 1600")
	m.estruturas[bp]["limite"] = 0.25
	igual(f.capacidade_bau(bp), 400, "limite 25%")
	var alvo: Object = f.destino_em(Vector2i(4, 0))
	var n := 0
	while alvo.receber("pedra"):
		n += 1
	igual(n, 400, "parou no limite")
	verificar(f.destino_em(Vector2i(1, 1)).receber("pedra"), "baú grande recebe pelo tile do meio também")


func test_acumulador_salva() -> void:
	var b := _fab()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	_por(m, "painel_solar", Vector2i(0, 0))
	var a := _por(m, "acumulador", Vector2i(0, 4))
	_por(m, "poste_energia", Vector2i(3, 2))
	f.sol = 1.0
	f.reconstruir()
	for i in 30:
		f.tick(1.0)
	perto(f.acumulado[a], 300.0 * 30.0 / 1000.0, 1e-3, "guardou a sobra do painel (sem consumo)")
	var f2 := Fabrica.new(m)
	f2.restaurar(f.estado())
	perto(f2.acumulado[a], f.acumulado[a], 1e-6, "volta do save")
