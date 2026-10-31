extends Caso
## Coletor de chuva e condensador de neblina (fase 2.3; arte/estudos/conv_agua.py): 2×2 em qualquer lugar, água pelo
## cano da borda sul. O coletor (sem energia) rende 25/s × chuva do clima e guarda 2.000 no tanque; o condensador
## (80 kW) rende 12/s × neblina. Sem chuva/neblina esperam ("esperando o tempo mudar").


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-10, 14):
		for y in range(-10, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _cano_na_porta(c: Construtor, id: int, comp := 3) -> Vector2i:
	var e: Dictionary = c.mapa.estruturas[id]
	var p := Grade.porta_no_mundo(Registro.modelos[e.nome].portas[0], e.minimo, e.area, e.rot)
	var d := Grade.DIRECOES.find(p.dir)
	c.executar(c.plano_linha("cano", p.tile_fora, p.tile_fora + p.dir * (comp - 1), Construtor.rot_do_fluxo(d)))
	return p.tile_fora


## Passos de 1 s como no jogo: a fábrica põe o clima na máquina; a energia vem à mão (o teste não é da fiação).
func _rodar(f: Fabrica, id: int, n: int, energia := 1.0) -> void:
	for i in n * 20:
		f.maquinas[id].energia = energia
		f.maquinas[id].clima = f.chuva if f.maquinas[id].receita_id == "coletar_chuva" else f.neblina
		f.maquinas[id].tick(0.05)
		f._tick_fluidos(0.05)


func test_dados() -> void:
	for n in ["coletor_chuva", "condensador_neblina"]:
		var md: Dictionary = Registro.modelos.get(n, {})
		igual(md.get("estudo", ""), "estudo_%s.py" % n, "%s convertido do estudo" % n)
		igual(Registro.area(n), Vector2i(2, 2), "%s 2×2" % n)
		igual(md.portas.size(), 1, "%s: uma saída de fluido" % n)
		igual(String(md.portas[0].nome).left(18), "PORTA_FLUIDO_SAI_S", "%s solta pela borda sul" % n)
		verificar(int(md.tris) <= 11000, "%s leve (%d)" % [n, md.tris])
		verificar(float(md.dims[0]) <= 2.01 and float(md.dims[1]) <= 2.01, "%s dentro da área (%s)" % [n, str(md.dims)])
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % n), "ícone %s" % n)
		verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Canos" and n in cat.pecas), "%s na aba Canos" % n)
		verificar(not Construtor.custo_de(n).is_empty(), "%s tem custo" % n)
	perto(float(Registro.modelos.coletor_chuva.portas[0].pos[2]), 0.35, 0.01, "saída do coletor desce à altura dos canos")
	igual(float(Registro.estruturas.coletor_chuva.get("energia_kw", 0)), 0.0, "coletor não gasta energia")
	igual(int(Registro.estruturas.condensador_neblina.energia_kw), 80, "condensador usa 80 kW")
	igual(int(Registro.estruturas.coletor_chuva.tanque_fluido), 2000, "tanque de 2.000")


func test_pesquisas() -> void:
	var p := Pesquisa.new()
	p.concluidas = {"fluidos": true, "automacao": true}
	verificar(not p.disponivel("coletor_chuva"), "coletor precisa da bomba d'água")
	p.concluidas["bomba_agua"] = true
	verificar(p.disponivel("coletor_chuva"), "bomba d'água → coletor")
	verificar(not p.disponivel("condensador_neblina"), "condensador precisa do coletor")
	igual(p.custo("coletor_chuva"), {"pacote_pesquisa": 25, "pacote_automacao": 25})
	p.concluidas["coletor_chuva"] = true
	verificar(p.disponivel("condensador_neblina"), "coletor → condensador")
	igual(p.custo("condensador_neblina"), {"pacote_pesquisa": 30, "pacote_automacao": 30})
	p.concluidas["condensador_neblina"] = true
	verificar(p.peca_liberada("coletor_chuva") and p.peca_liberada("condensador_neblina"), "liberam as peças")


func test_coletor_so_com_chuva() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("coletor_chuva", Vector2i(0, 0), 0)
	var fora := _cano_na_porta(c, id, 3)
	f.reconstruir()
	var m: Maquina = f.maquinas[id]
	igual(m.receita_id, "coletar_chuva")
	verificar(not f._membros.has(id), "coletor fica fora da rede elétrica (não precisa de poste)")
	var rede := f.rede_de(c.mapa.tiles[fora])
	f.chuva = 0.0
	_rodar(f, id, 5)
	igual(m.estado, Maquina.Estado.ESPERANDO_CLIMA, "no seco espera")
	perto(float(rede.qtd), 0.0, 1e-6, "no seco nada")
	f.chuva = 1.0
	_rodar(f, id, 4)
	igual(rede.fluido, "agua")
	perto(float(rede.qtd), 100.0, 25.5, "chuva forte: 25/s")
	f.chuva = 0.7
	rede.qtd = 0.0
	_rodar(f, id, 10)
	perto(float(rede.qtd) + float(m.fluidos.get("agua", 0.0)), 175.0, 25.0, "chuva comum: ~70%")


func test_coletor_guarda_dois_mil() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("coletor_chuva", Vector2i(0, 0), 0)
	f.reconstruir()
	var m: Maquina = f.maquinas[id]
	f.chuva = 1.0
	for i in 100:
		m.clima = f.chuva
		m.tick(1.0)
	perto(float(m.fluidos.get("agua", 0.0)), 2000.0, 0.01, "sem cano enche o tanque de 2.000")
	igual(m.estado, Maquina.Estado.SAIDA_CHEIA, "cheio para")
	# um cano depois esvazia o tanque e ele volta a coletar
	var fora := _cano_na_porta(c, id, 3)
	f.reconstruir()
	f._tick_fluidos(1.0)
	perto(float(f.rede_de(c.mapa.tiles[fora]).qtd), 300.0, 0.5, "o cano puxou do tanque")
	verificar(not m.dormindo(), "acordou")


func test_condensador_com_neblina_e_energia() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("condensador_neblina", Vector2i(0, 0), 0)
	var fora := _cano_na_porta(c, id, 4)
	f.reconstruir()
	var m: Maquina = f.maquinas[id]
	igual(m.receita_id, "condensar_neblina")
	var rede := f.rede_de(c.mapa.tiles[fora])
	f.neblina = 0.0
	_rodar(f, id, 3)
	igual(m.estado, Maquina.Estado.ESPERANDO_CLIMA, "sem neblina espera")
	f.neblina = 1.0
	_rodar(f, id, 10, 0.0)
	igual(m.estado, Maquina.Estado.SEM_ENERGIA, "com neblina mas sem energia não condensa")
	_rodar(f, id, 10)
	perto(float(rede.qtd), 120.0, 12.5, "neblina cheia: 12/s")
	# a fábrica põe a neblina do clima na máquina a cada passo
	f.neblina = 0.5
	m.energia = 1.0
	f.tick(1.0)
	perto(m.clima, 0.5, 1e-6, "Fabrica.tick passa a neblina")
	f.chuva = 0.3
	var col := c.mapa.colocar("coletor_chuva", Vector2i(6, 6), 0)
	f.reconstruir()
	f.tick(1.0)
	perto(f.maquinas[col].clima, 0.3, 1e-6, "Fabrica.tick passa a chuva")
