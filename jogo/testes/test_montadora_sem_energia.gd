extends Caso
## Montadora (engrenagem) e o braço que a alimenta, longe de qualquer poste: o ícone tem de ser "sem energia",
## não "falta insumo" (a caixa laranja escondia a causa — save da Sapyst, montadora e braço com "fios": []).

func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 6):
		for y in range(-4, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot := 0) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


func _rodar(f: Fabrica, s: float) -> void:
	for i in int(s * 30):
		f.tick(1.0 / 30.0)


func test_montadora_sem_poste_mostra_sem_energia() -> void:
	var c := _c()
	var mt := _por(c, "montadora", Vector2i(0, 0), 3)
	var br := _por(c, "braco", Vector2i(-1, 1), 3)        # costas no baú, frente na montadora
	var bau := _por(c, "bau", Vector2i(-2, 1))
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	f.escolher_receita(mt, "engrenagem")
	f.baus[bau]["placa_ferro"] = 10
	_rodar(f, 5.0)
	igual(f.maquinas[mt].estado, Maquina.Estado.SEM_ENERGIA, "montadora sem poste: ícone sem energia")
	igual(f.bracos[br].entregues, 0, "braço sem energia não põe placa")
	verificar(int(f.baus[bau].placa_ferro) >= 9, "placas continuam no baú (a garra parada fica com 1, como no save)")
	# com gerador e poste, o mesmo arranjo anda
	var g := _por(c, "gerador", Vector2i(-6, 3))
	_por(c, "poste_energia", Vector2i(-2, 3))
	Fiacao.ligar_novo(c.mapa, g)
	Fiacao.ligar_novo(c.mapa, c.mapa.tiles[Vector2i(-2, 3)])
	f.reconstruir()
	f.combustivel[g] = 30.0
	_rodar(f, 10.0)
	verificar(f.bracos[br].entregues >= 2, "com energia o braço põe placas (%d)" % f.bracos[br].entregues)
	verificar(f.maquinas[mt].produzidos >= 1 or f.maquinas[mt].estado == Maquina.Estado.TRABALHANDO,
			"montadora fazendo engrenagem")


## Save da Sapyst: braço segurando carvão e o destino dele foi tirado → "receber" em Nil a cada tick, e o erro
## cortava o resto do tick da fábrica (braços seguintes e esteiras paravam).
func test_braco_segurando_sem_destino_espera() -> void:
	var c := _c()
	var a := _por(c, "bau", Vector2i(0, 0))
	var br := _por(c, "braco", Vector2i(1, 0), 3)
	var b2 := _por(c, "bau", Vector2i(2, 0))
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	var b: Braco = f.bracos[br]
	b.energia = 1.0
	f.baus[a]["carvao"] = 5
	b.tick(0.01)
	igual(b.segurando, "carvao", "pegou carvão")
	c.mapa.remover(b2)
	f.reconstruir()
	verificar(b.destino == null, "sem destino agora")
	for i in 60:
		b.tick(1.0 / 30.0)
	igual(b.segurando, "carvao", "continua segurando, sem erro")
	_por(c, "bau", Vector2i(2, 0))
	f.reconstruir()
	for i in 60:
		b.tick(1.0 / 30.0)
	igual(b.segurando, "", "baú novo na frente: soltou")
