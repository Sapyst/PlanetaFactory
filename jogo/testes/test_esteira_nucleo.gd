extends Caso
## A esteira que termina apontando para o núcleo entrega direto no estoque, sem braço, por qualquer lado e em qualquer
## tile do lado (não só nas bocas). Só o núcleo: máquina, baú e posto avançado continuam pedindo braço.

const DT := 1.0 / 30.0


func _base(sem_nucleo := false) -> Dictionary:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	for x in range(-30, 40):
		for y in range(-30, 40):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	var f := Fabrica.new(m)
	f.estoque_nucleo = {}
	return {"g": g, "m": m, "c": c, "f": f}


func _rodar(f: Fabrica, s: float) -> void:
	for i in int(s / DT):
		f.tick(DT)


func _esteira_em(f: Fabrica, t: Vector2i) -> EsteiraCaminho:
	return f.caminhos[f._no_tile[t][0]].esteira


## Rotação de uma peça que anda no sentido v.
func _rot_para(v: Vector2i) -> int:
	return Construtor.rot_do_fluxo(Grade.DIRECOES.find(v))


## Traço do jeito do jogador; devolve o nome da última peça.
func _tracar(b: Dictionary, de: Vector2i, ate: Vector2i) -> String:
	var plano: Array[Dictionary] = b.c.plano_linha("esteira", de, ate, 0)
	for it in plano:
		igual(it.motivo, "", "traço livre de %s a %s" % [de, ate])
	b.c.executar(plano)
	return b.m.estruturas[b.m.tiles[ate]].nome


func test_entra_pelos_4_lados_sem_braco() -> void:
	# (de, até): uma esteira chegando em cada lado do núcleo 3×3, que ocupa de (0,0) a (2,2)
	var casos := {"norte": [Vector2i(1, -6), Vector2i(1, -1)], "sul": [Vector2i(1, 8), Vector2i(1, 3)],
			"oeste": [Vector2i(-6, 1), Vector2i(-1, 1)], "leste": [Vector2i(8, 1), Vector2i(3, 1)]}
	for lado in casos:
		var b := _base()
		var nu: int = b.m.colocar("nucleo", Vector2i(0, 0), 0)
		verificar(nu >= 0, "núcleo coube")
		_tracar(b, casos[lado][0], casos[lado][1])
		b.f.reconstruir()
		_esteira_em(b.f, casos[lado][0]).inserir_na_entrada("pedra")
		_rodar(b.f, 5.0)
		igual(int(b.f.estoque_nucleo.get("pedra", 0)), 1, "%s: a pedra entrou no núcleo" % lado)
		igual(_esteira_em(b.f, casos[lado][0]).quantidade(), 0, "%s: esteira vazia" % lado)


func test_fora_da_boca_tambem() -> void:
	# nos tiles de canto do lado (a boca fica só no do meio)
	for x in [0, 2]:
		var b := _base()
		b.m.colocar("nucleo", Vector2i(0, 0), 0)
		var fim := Vector2i(x, -1)
		var nome := _tracar(b, Vector2i(x, -6), fim)
		igual(nome, "esteira_reta", "a ponta encostada no núcleo é reta, não fim")
		b.f.reconstruir()
		_esteira_em(b.f, fim).inserir_em("carvao", 2.0)
		_rodar(b.f, 3.0)
		igual(int(b.f.estoque_nucleo.get("carvao", 0)), 1, "x=%d: entrou fora da boca" % x)


func test_fila_inteira_entra_e_nao_para() -> void:
	# o estoque do núcleo não tem limite: a fila não fica presa
	var b := _base()
	b.m.colocar("nucleo", Vector2i(0, 0), 0)
	_tracar(b, Vector2i(1, -6), Vector2i(1, -1))
	b.f.reconstruir()
	var e := _esteira_em(b.f, Vector2i(1, -6))
	var postos := 0
	for i in 200 * 30:
		if postos < 200 and e.cabe_na_entrada() and e.inserir_na_entrada("pedra"):
			postos += 1
		b.f.tick(DT)
	igual(postos, 200, "a esteira nunca entupiu")
	igual(int(b.f.estoque_nucleo.get("pedra", 0)), 200, "todas no estoque")


func test_peca_fim_de_save_antigo_entrega() -> void:
	var b := _base()
	var nu: int = b.m.colocar("nucleo", Vector2i(0, 0), 0)
	var id: int = b.m.colocar("esteira_fim", Vector2i(1, -1), _rot_para(Vector2i(0, 1)))
	verificar(nu >= 0 and id >= 0, "colocados")
	b.f.reconstruir()
	_esteira_em(b.f, Vector2i(1, -1)).inserir_na_entrada("pedra")
	_rodar(b.f, 2.0)
	igual(int(b.f.estoque_nucleo.get("pedra", 0)), 1, "peça fim encostada também entrega")


func test_passando_ao_lado_nao_entrega() -> void:
	# esteira correndo ao longo do núcleo, sem apontar para ele: passa reto e não vira sozinha na ponta
	var b := _base()
	b.m.colocar("nucleo", Vector2i(0, 0), 0)
	_tracar(b, Vector2i(-4, -1), Vector2i(0, -1))
	igual(b.m.estruturas[b.m.tiles[Vector2i(0, -1)]].nome, "esteira_fim", "o traço não curva sozinho para o núcleo fora da boca")
	b.f.reconstruir()
	_esteira_em(b.f, Vector2i(-4, -1)).inserir_na_entrada("pedra")
	_rodar(b.f, 6.0)
	igual(int(b.f.estoque_nucleo.get("pedra", 0)), 0, "não entrou")
	igual(_esteira_em(b.f, Vector2i(-4, -1)).quantidade(), 1, "item parado no fim")


func test_outras_estruturas_continuam_sem_receber() -> void:
	for nome in ["fornalha", "bau", "posto_avancado", "laboratorio", "gerador"]:
		var b := _base()
		var id: int = b.m.colocar(nome, Vector2i(0, 0), 0)
		verificar(id >= 0, "%s coube" % nome)
		var e: Dictionary = b.m.estruturas[id]
		b.m.colocar("esteira_fim", Vector2i(e.minimo.x, e.minimo.y - 1), _rot_para(Vector2i(0, 1)))
		b.f.reconstruir()
		var est := _esteira_em(b.f, Vector2i(e.minimo.x, e.minimo.y - 1))
		est.inserir_na_entrada("carvao")
		_rodar(b.f, 3.0)
		igual(est.quantidade(), 1, "%s: o item fica parado no fim da esteira" % nome)
		igual(int(b.f.estoque_nucleo.get("carvao", 0)), 0, "%s: nada no estoque do núcleo" % nome)


func test_nucleo_com_braco_continua() -> void:
	var b := _base()
	b.m.colocar("nucleo", Vector2i(0, 0), 0)
	b.m.colocar("esteira_fim", Vector2i(1, -2), _rot_para(Vector2i(0, 1)))
	b.m.colocar("braco", Vector2i(1, -1), _rot_para(Vector2i(0, 1)))
	b.f.reconstruir()
	_esteira_em(b.f, Vector2i(1, -2)).inserir_na_entrada("pedra")
	_rodar(b.f, 5.0)
	igual(int(b.f.estoque_nucleo.get("pedra", 0)), 1, "braço ainda entrega")


func test_salvar_e_carregar() -> void:
	var b := _base()
	b.m.colocar("nucleo", Vector2i(0, 0), 0)
	_tracar(b, Vector2i(1, -8), Vector2i(1, -1))
	b.f.reconstruir()
	var e := _esteira_em(b.f, Vector2i(1, -8))
	for i in 3:
		e.inserir_na_entrada("pedra")
		_rodar(b.f, 0.3)
	var texto := var_to_str({"mapa": b.m.estruturas.duplicate(true), "fab": b.f.estado()})
	var d: Dictionary = str_to_var(texto)
	var m2 := MapaOcupacao.new(b.g)
	m2.restaurar(d.mapa, b.m.limpos.keys(), b.m._prox_id)
	var f2 := Fabrica.new(m2)
	f2.estoque_nucleo = {}
	f2.restaurar(d.fab)
	igual(_esteira_em(f2, Vector2i(1, -8)).quantidade(), 3, "os 3 itens voltaram na esteira")
	_rodar(f2, 6.0)
	igual(int(f2.estoque_nucleo.get("pedra", 0)), 3, "depois de carregar, entram no núcleo")


func test_nucleo_sem_aviso_de_porta() -> void:
	verificar(not Portas.mostra_aviso("nucleo"), "as entradas do núcleo são opcionais")
	var b := _base()
	var nu: int = b.m.colocar("nucleo", Vector2i(0, 0), 0)
	igual(Portas.soltas(b.m, nu).size(), 0, "nenhuma placa de falta entrada")
	verificar(Portas.mostra_aviso("posto_avancado"), "o posto segue com aviso")
