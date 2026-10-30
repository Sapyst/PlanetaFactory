extends Caso
## Rede lógica (pesquisa rede_logica, lote 16): sensor de esteira (ao lado da esteira, conta os itens que passam no
## tile da frente: itens/min), sensor de tanque (peça de cano: nível da rede em %), comparador (canal > ou < número:
## liga/desliga as estruturas dos 4 tiles encostados) e válvula (entre duas redes: passa acima/abaixo de um nível,
## sempre, ou quando o comparador manda). Cada sensor manda pelo seu canal (A–D); o canal soma os sensores dele.

const PECAS := ["sensor_esteira", "sensor_tanque", "comparador", "valvula"]


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 24):
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _rodar(f: Fabrica, s: float, cada := Callable()) -> void:
	for i in int(s * 30):
		if cada.is_valid():
			cada.call()
		f.tick(1.0 / 30.0)


func _id(c: Construtor, t: Vector2i) -> int:
	return c.mapa.tiles[t]


func test_dados() -> void:
	for n in PECAS:
		var md: Dictionary = Registro.modelos.get(n, {})
		verificar(not md.is_empty(), "modelo: " + n)
		igual(md.get("estudo", ""), "estudo_%s.py" % n, "convertido do estudo: " + n)
		igual(Registro.area(n), Vector2i(1, 1), "1×1 (árvore): " + n)
		igual(Registro.estruturas[n].grupo, "logica")
		verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Lógica" and n in cat.pecas), "na categoria Lógica: " + n)
		verificar(Registro.menu.rotulos.has(n), "rótulo: " + n)
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % n), "ícone: " + n)
		verificar(not Construtor.custo_de(n).is_empty(), "custo: " + n)
	for n in ["sensor_tanque", "valvula"]:
		igual(Registro.modelos[n].portas.size(), 2, "peça de cano (S → N): " + n)
		perto(float(Registro.modelos[n].portas[0].pos[2]), float(Registro.modelos.cano_reto.portas[0].pos[2]), 0.01, "na altura dos canos")
		verificar(Portas.eh_cano(n), "é cano para as portas: " + n)
	verificar(Registro.modelos.sensor_esteira.portas.is_empty() and Registro.modelos.comparador.portas.is_empty(), "sem portas")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("rede_logica"), "jogável")
	igual(Registro.progressao.pesquisas.rede_logica.requer, ["processador", "divisor_filtro"], "pré-requisitos da árvore")
	igual(p.custo("rede_logica"), {"pacote_pesquisa": 40, "pacote_automacao": 40, "pacote_quimico": 40})
	for n in PECAS:
		verificar(not p.peca_liberada(n), "travado no início: " + n)
	p.concluidas = {"processador": true, "divisor_filtro": true}
	verificar(p.disponivel("rede_logica"), "pesquisável")
	p.concluidas["rede_logica"] = true
	for n in PECAS:
		verificar(p.peca_liberada(n), "liberado: " + n)


## Esteira leste–oeste em y 0 (x −4..8), sensor no tile (2, −1) olhando para o norte (a esteira).
func _esteira() -> Dictionary:
	var c := _c()
	c.executar(c.plano_linha("esteira", Vector2i(-4, 0), Vector2i(8, 0), Construtor.rot_do_fluxo(1)))
	c.mapa.colocar("sensor_esteira", Vector2i(2, -1), 0)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	var a: Array = f._no_tile[Vector2i(-4, 0)]
	return {"c": c, "f": f, "est": f.caminhos[a[0]].esteira, "s": _id(c, Vector2i(2, -1))}


func test_sensor_de_esteira_conta() -> void:
	var m := _esteira()
	var f: Fabrica = m.f
	var est: EsteiraCaminho = m.est
	igual(f._sens_esteira.size(), 1, "a cabeça achou a esteira da frente")
	var postos := [0]
	_rodar(f, 12.0, func():
		if postos[0] < 20 and est.inserir_na_entrada("placa_ferro"):
			postos[0] += 1)
	var total := int(f.sensores[m.s].total)
	igual(postos[0], 20)
	igual(total, 20, "contou os 20 que passaram (a fila para depois do sensor)")
	perto(f.valor_sensor(m.s), float(total) * 60.0 / 10.0, float(total) * 6.0 * 0.35, "itens/min dos últimos 10 s")
	verificar(not f.sensor_contando(m.s), "a fila parou depois dele: não está contando agora")
	# esteira para (fim entupido não conta de novo o que está parado)
	var antes := int(f.sensores[m.s].total)
	_rodar(f, 12.0)
	igual(int(f.sensores[m.s].total), antes, "parado não conta de novo")
	_rodar(f, 12.0)
	perto(f.valor_sensor(m.s), 0.0, 1e-6, "nada passando: 0 itens/min")
	# canal
	igual(Fabrica.canal_de(m.c.mapa.estruturas[m.s]), "A", "canal A por padrão")
	# virado de costas: não olha nada
	var c2 := _c()
	c2.executar(c2.plano_linha("esteira", Vector2i(-4, 0), Vector2i(8, 0), Construtor.rot_do_fluxo(1)))
	c2.mapa.colocar("sensor_esteira", Vector2i(2, -1), 2)
	var f2 := Fabrica.new(c2.mapa)
	f2.reconstruir()
	igual(f2._sens_esteira.size(), 0, "de costas para a esteira não conta")


## Linha de cano leste–oeste: cano (0,0), sensor de tanque (1,0), cano (2,0), tanque (3..4, 0..1) pela boca O0.
func _canos() -> Dictionary:
	var c := _c()
	var leste := Construtor.rot_do_fluxo(1)
	c.executar(c.plano_peca("cano_reto", Vector2i(0, 0), leste))
	c.mapa.colocar("sensor_tanque", Vector2i(1, 0), leste)
	c.executar(c.plano_peca("cano_reto", Vector2i(2, 0), leste))
	c.mapa.colocar("tanque", Vector2i(3, 0), 0)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	return {"c": c, "f": f, "s": _id(c, Vector2i(1, 0))}


func test_sensor_de_tanque() -> void:
	var m := _canos()
	var f: Fabrica = m.f
	var r := f.rede_de(m.s)
	verificar(not r.is_empty(), "o sensor é parte da rede")
	verificar(r == f.rede_de(_id(m.c, Vector2i(3, 0))), "mesma rede do tanque")
	perto(float(r.cap), 25300.0, 1e-3, "2 canos + sensor + tanque")
	r.fluido = "agua"
	r.qtd = float(r.cap) * 0.5
	perto(f.valor_sensor(m.s), 50.0, 1e-3, "50%")
	f.tick(1.0 / 30.0)
	perto(float(f.canais.A), 50.0, 1e-3, "manda pelo canal A")
	m.c.mapa.estruturas[m.s]["canal"] = "C"
	f.tick(1.0 / 30.0)
	perto(float(f.canais.A), 0.0, 1e-6, "trocou de canal")
	perto(float(f.canais.C), 50.0, 1e-3)


func test_comparador_liga_e_desliga() -> void:
	var m := _canos()
	var c: Construtor = m.c
	var f: Fabrica = m.f
	c.mapa.colocar("comparador", Vector2i(1, 3), 0)
	c.mapa.colocar("braco", Vector2i(1, 4), 0)                 # encostado ao norte
	c.mapa.colocar("bau", Vector2i(0, 3), 0)                   # encostado a oeste
	c.mapa.colocar("braco", Vector2i(5, 5), 0)                 # longe
	f.reconstruir()
	var cmp := _id(c, Vector2i(1, 3))
	var br := _id(c, Vector2i(1, 4))
	var longe := _id(c, Vector2i(5, 5))
	var e: Dictionary = c.mapa.estruturas[cmp]
	e["op"] = ">"
	e["numero"] = 40
	var r := f.rede_de(m.s)
	r.fluido = "agua"
	r.qtd = float(r.cap) * 0.5
	f.tick(1.0 / 30.0)
	verificar(f.condicao_comparador(cmp), "50 > 40")
	verificar(f.ligada(br), "condição vale: braço ligado")
	r.qtd = float(r.cap) * 0.3
	f.tick(1.0 / 30.0)
	verificar(not f.condicao_comparador(cmp), "30 > 40 não vale")
	verificar(not f.ligada(br), "braço encostado desligado")
	verificar(not f.ligada(_id(c, Vector2i(0, 3))), "baú encostado também recebe a ordem")
	verificar(f.ligada(longe), "o de longe não")
	e["op"] = "<"
	f.tick(1.0 / 30.0)
	verificar(f.ligada(br), "30 < 40: liga")
	e["op"] = ">"
	e["desligada"] = true
	f.tick(1.0 / 30.0)
	verificar(f.ligada(br), "comparador desligado não manda em ninguém")
	e.erase("desligada")
	# braço desligado pelo comparador fica sem energia (não trabalha)
	f.tick(1.0 / 30.0)
	igual(float(f.bracos[br].energia), 0.0, "sem energia enquanto desligado")


func test_comparador_com_bomba_de_estacao() -> void:
	var c := _c()
	c.mapa.colocar("bomba_estacao", Vector2i(4, 4), 0)
	c.mapa.colocar("comparador", Vector2i(5, 4), 0)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	var b := _id(c, Vector2i(4, 4))
	c.mapa.estruturas[_id(c, Vector2i(5, 4))]["numero"] = 10      # canal A = 0: 0 > 10 não vale
	f.tick(1.0 / 30.0)
	verificar(not f.ligada(b), "o comparador manda na bomba de estação")


## Válvula entre a rede A (oeste: cano + tanque) e a rede B (leste: cano + tanque).
func _valvula() -> Dictionary:
	var c := _c()
	var leste := Construtor.rot_do_fluxo(1)
	c.mapa.colocar("tanque", Vector2i(-3, 0), 0)                 # 2×2 em −3..−2: boca L0 dá no tile (−1, 1)
	c.executar(c.plano_peca("cano_reto", Vector2i(-1, 1), leste))
	c.mapa.colocar("valvula", Vector2i(0, 1), leste)
	c.executar(c.plano_peca("cano_reto", Vector2i(1, 1), leste))
	c.mapa.colocar("tanque", Vector2i(2, 1), 0)                  # boca O0 dá no tile (1, 1)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	return {"c": c, "f": f, "v": _id(c, Vector2i(0, 1)), "a": f.rede_de(_id(c, Vector2i(-1, 1))), "b": f.rede_de(_id(c, Vector2i(1, 1)))}


func test_valvula() -> void:
	var m := _valvula()
	var f: Fabrica = m.f
	var a: Dictionary = m.a
	var b: Dictionary = m.b
	verificar(not a.is_empty() and not b.is_empty() and a != b, "duas redes separadas pela válvula")
	verificar(f._valvulas.size() == 1 and f._valvulas[0].ent >= 0 and f._valvulas[0].sai >= 0, "a válvula achou as duas")
	a.fluido = "agua"
	a.qtd = float(a.cap) * 0.8
	var e: Dictionary = m.c.mapa.estruturas[m.v]
	e["modo_valvula"] = "acima"
	e["nivel_valvula"] = 50
	_rodar(f, 1.0)
	perto(float(b.qtd), 1000.0, 40.0, "acima de 50%: passa 1.000/s")
	verificar(f.valvula_passou.has(m.v), "passando")
	_rodar(f, 30.0)
	perto(float(a.qtd) / float(a.cap), 0.5, 0.01, "para quando a entrada chega no nível")
	var total := float(a.qtd) + float(b.qtd)
	perto(total, float(a.cap) * 0.8, 1.0, "nada se perde")
	# abaixo: enche a saída até o nível
	e["modo_valvula"] = "abaixo"
	e["nivel_valvula"] = 40
	b.qtd = 0.0
	_rodar(f, 30.0)
	perto(float(b.qtd) / float(b.cap), 0.4, 0.01, "abaixo de 40%: enche a saída até 40%")
	# sempre aberta, mas o comparador fecha
	e["modo_valvula"] = "sempre"
	m.c.mapa.colocar("comparador", Vector2i(0, 2), 0)
	f.reconstruir()
	m.c.mapa.estruturas[_id(m.c, Vector2i(0, 2))]["numero"] = 9999
	var b2 := f.rede_de(_id(m.c, Vector2i(1, 1)))
	var antes := float(b2.qtd)
	_rodar(f, 1.0)
	perto(float(b2.qtd), antes, 1e-3, "comparador fechou a válvula")
	# fluido diferente não mistura
	m.c.mapa.estruturas[_id(m.c, Vector2i(0, 2))]["numero"] = -1
	b2.fluido = "seiva"
	var a2 := f.rede_de(_id(m.c, Vector2i(-1, 1)))
	var qa := float(a2.qtd)
	_rodar(f, 1.0)
	perto(float(a2.qtd), qa, 1e-3, "seiva do outro lado: não mistura água")


func test_salva_contagem() -> void:
	var m := _esteira()
	var f: Fabrica = m.f
	f.sensores[m.s].total = 77
	f.sensores[m.s].janela = [1, 2, 3]
	var d: Dictionary = str_to_var(var_to_str(f.estado()))
	var f2 := Fabrica.new(m.c.mapa)
	f2.restaurar(d)
	igual(int(f2.sensores[m.s].total), 77, "contagem salva")
	igual((f2.sensores[m.s].janela as Array).size(), 3, "janela salva")
