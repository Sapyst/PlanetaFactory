extends Caso
## Supressor de incêndio (supressor_fogo, fase 2.3; estudo_supressor_fogo.py via arte/estudos/conv_agua.py): 1×1, água
## pelo cano da borda leste (no eixo do tile, como os canos do jogo) num reservatório de 200. Com energia e água vigia
## 8 m: havendo fogo (vegetação queimando: AmbienteVivo.fogo), gasta 10/s e apaga os focos do raio; enquanto tiver
## água, a vegetação do raio não pega fogo (molhada). Sem água não faz nada.


func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var f := Fabrica.new(m)
	var c := Clima.new(5)
	c.forcar("limpo", true)
	c.estacao = 1                       # verão (seco)
	return [g, m, f, AmbienteVivo.new(g, m, 3), c, Construtor.new(m)]


## Vegetação que pega fogo e um tile livre a 3–5 m dela para o supressor.
func _lugar(a: AmbienteVivo, m: MapaOcupacao) -> Array:
	for x in range(50, 400, 3):
		var t0 := Vector2i(x, 0)
		if not a._inflamavel(t0):
			continue
		for d in [Vector2i(4, 0), Vector2i(-4, 0), Vector2i(0, 4), Vector2i(0, -4), Vector2i(3, 3)]:
			var s: Vector2i = t0 + d
			m.limpar_obstaculo(s)
			if m.motivo_bloqueio("supressor_fogo", s, 0) == "":
				return [t0, s]
	return []


func test_dados_e_pesquisa() -> void:
	var md: Dictionary = Registro.modelos.get("supressor_fogo", {})
	igual(md.get("estudo", ""), "estudo_supressor_fogo.py", "convertido do estudo")
	igual(Registro.area("supressor_fogo"), Vector2i(1, 1), "1×1")
	igual(md.portas.size(), 1, "uma entrada de água")
	igual(md.portas[0].nome, "PORTA_FLUIDO_ENT_L0", "pelo leste")
	perto(float(md.portas[0].pos[1]), 0.0, 1e-6, "no eixo do tile (como os canos do jogo)")
	perto(float(md.portas[0].pos[2]), float(Registro.modelos.cano_reto.portas[0].pos[2]), 0.01, "na altura dos canos")
	verificar(float(md.dims[0]) <= 1.01 and float(md.dims[1]) <= 1.01, "dentro do tile (%s)" % str(md.dims))
	verificar(int(md.tris) <= 7000, "leve (%d)" % md.tris)
	verificar(ResourceLoader.exists("res://assets/icones/supressor_fogo.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Limpeza" and "supressor_fogo" in cat.pecas), "aba Limpeza")
	igual(int(Registro.estruturas.supressor_fogo.apaga.raio), 8, "raio de 8 m (árvore)")
	var p := Pesquisa.new()
	p.concluidas = {"bomba_agua": true}
	verificar(not p.disponivel("supressor_fogo"), "precisa de Limpeza")
	p.concluidas["limpeza"] = true
	verificar(p.disponivel("supressor_fogo"), "bomba d'água + limpeza")
	igual(p.custo("supressor_fogo"), {"pacote_pesquisa": 25, "pacote_automacao": 25})


func test_enche_pelo_cano() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var c: Construtor = b[5]
	for x in range(-2, 8):
		for y in range(-2, 3):
			m.limpar_obstaculo(Vector2i(x, y))
	var id := m.colocar("supressor_fogo", Vector2i(0, 0), 0)
	c.executar(c.plano_linha("cano", Vector2i(4, 0), Vector2i(1, 0), Construtor.rot_do_fluxo(3)))
	f.reconstruir()
	var rede := f.rede_de(m.tiles[Vector2i(1, 0)])
	verificar(not rede.is_empty(), "cano na boca leste")
	rede.fluido = "agua"
	rede.qtd = 400.0
	for i in 3:
		f.tick(1.0)
	var mq: Maquina = f.maquinas[id]
	perto(float(mq.fluidos.get("agua", 0.0)), 200.0, 0.01, "encheu o reservatório de 200")
	perto(float(rede.qtd), 200.0, 0.01, "o resto ficou no cano")
	f.tick(5.0)
	perto(float(mq.fluidos.get("agua", 0.0)), 200.0, 0.01, "sem fogo não gasta água")


func test_apaga_fogo_no_raio() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var cl: Clima = b[4]
	var l := _lugar(a, m)
	verificar(not l.is_empty(), "achou vegetação e lugar perto")
	var t0: Vector2i = l[0]
	var id := m.colocar("supressor_fogo", l[1], 0)
	f.reconstruir()
	var mq: Maquina = f.maquinas[id]
	mq.energia = 1.0
	mq.fluidos["agua"] = 200.0
	var t1 := Vector2i(9999, 0)                 # outra vegetação no raio, que não vai queimar
	for dx in range(-6, 7):
		for dy in range(-6, 7):
			var tt: Vector2i = l[1] + Vector2i(dx, dy)
			if t1.x == 9999 and tt.distance_to(t0) > 2.5 and (Vector2(tt) - Vector2(l[1])).length() < 7.0 and a._inflamavel(tt):
				t1 = tt
	a._acender(t0)
	verificar(a.fogo.has(t0), "pegou fogo")
	var trabalhou := false
	var mirou := false
	for i in 3:
		a.tick(1.0, f, cl)
		trabalhou = trabalhou or mq.estado == Maquina.Estado.TRABALHANDO
		mirou = mirou or f.jatos.has(id)
	verificar(not a.fogo.has(t0), "o supressor apagou o foco")
	verificar(trabalhou, "trabalhou (a animação toca) enquanto borrifava")
	verificar(mirou, "o jato mirou o foco")
	verificar(float(mq.fluidos.agua) < 200.0, "gastou água (%.0f)" % float(mq.fluidos.agua))
	a.tick(1.0, f, cl)
	igual(mq.estado, Maquina.Estado.PRONTIDAO, "sem fogo: de prontidão")
	verificar(f.jatos.is_empty(), "sem fogo, sem jato")
	# molhado: não pega fogo no raio; fora dele, pega
	verificar(a.protegido(t0), "dentro do raio")
	verificar(not a.protegido(l[1] + Vector2i(30, 0)), "fora do raio não é protegido")
	if t1.x != 9999 and not a.fogo.has(t1):
		verificar(not a._inflamavel(t1), "vegetação molhada não pega fogo")
		mq.fluidos["agua"] = 0.0
		a.tick(1.0, f, cl)
		verificar(a._inflamavel(t1), "sem água volta a poder pegar fogo")


func test_sem_agua_nada() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var cl: Clima = b[4]
	var l := _lugar(a, m)
	var t0: Vector2i = l[0]
	var id := m.colocar("supressor_fogo", l[1], 0)
	f.reconstruir()
	var mq: Maquina = f.maquinas[id]
	mq.energia = 1.0
	a._acender(t0)
	a.tick(1.0, f, cl)
	igual(mq.estado, Maquina.Estado.SEM_INSUMO, "sem água: esperando insumo")
	verificar(a.fogo.has(t0), "o fogo continua")
	verificar(not a.protegido(t0), "sem água não protege")
	# sem energia também não
	mq.fluidos["agua"] = 200.0
	mq.energia = 0.0
	a.tick(1.0, f, cl)
	igual(mq.estado, Maquina.Estado.SEM_ENERGIA, "sem energia")
	perto(float(mq.fluidos.agua), 200.0, 1e-6, "sem energia não gasta")
