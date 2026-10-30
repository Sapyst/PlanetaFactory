extends Caso
## Para-raios (para_raios, 1×1) e para-raios de cristal (para_raios_2, 1×1) — fase 2.5; estudo_para_raios.py via
## arte/estudos/conv_clima.py. Pegam o raio que cairia a até 14 m / 22 m da ponta (protegem o que está em volta) e
## mandam 120 / 200 MJ por raio para os acumuladores da rede deles (poste perto); sem acumulador, só protegem.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-12, 40):
		for y in range(-12, 20):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_dados_e_modelo() -> void:
	for n in ["para_raios", "para_raios_2"]:
		var md: Dictionary = Registro.modelos.get(n, {})
		igual(md.get("estudo", ""), "estudo_para_raios.py", "convertido do estudo: " + n)
		igual(Registro.area(n), Vector2i(1, 1), "1×1: " + n)
		verificar(float(md.dims[0]) <= 1.0 and float(md.dims[1]) <= 1.0, "dentro do tile (%s)" % str(md.dims))
		verificar(int(md.tris) <= 4500, "leve (%d)" % md.tris)
		verificar(md.get("ponta_raio", []).size() == 3, "ponto onde o raio bate: " + n)
		perto(float(md.ponta_raio[2]), float(md.dims[2]), 0.05, "a ponta é o topo do captor")
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % n), "ícone: " + n)
		verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Clima" and n in cat.pecas), "aba Clima: " + n)
		verificar(not Registro.progressao.custos.get(n, {}).is_empty(), "custo de construção")
		igual(Fiacao.papel(n), "fonte", "liga num poste (o raio entra na rede)")
		verificar(ResourceLoader.exists(md.modelo), "modelo no jogo")
	perto(float(Registro.estruturas.para_raios.capta_raio.raio), 14.0, 1e-6, "14 m (árvore)")
	perto(float(Registro.estruturas.para_raios.capta_raio.mj), 120.0, 1e-6, "120 MJ por raio (árvore)")
	perto(float(Registro.estruturas.para_raios_2.capta_raio.raio), 22.0, 1e-6, "22 m (árvore)")
	perto(float(Registro.estruturas.para_raios_2.capta_raio.mj), 200.0, 1e-6, "200 MJ por raio (árvore)")
	verificar(float(Registro.modelos.para_raios_2.dims[2]) > float(Registro.modelos.para_raios.dims[2]), "o de cristal é mais alto")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("para_raios") and p.jogavel("para_raios_2"), "jogáveis")
	p.concluidas = {"automacao": true}
	verificar(not p.disponivel("para_raios"), "espera o aço")
	p.concluidas["aco"] = true
	verificar(p.disponivel("para_raios"), "automação + aço")
	igual(p.custo("para_raios"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "custo da árvore")
	p.concluidas["para_raios"] = true
	verificar(p.peca_liberada("para_raios"), "libera o para-raios")
	verificar(not p.disponivel("para_raios_2"), "o de cristal espera a ciência de tempestade")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("para_raios_2"), "para-raios + ciência de tempestade")
	igual(p.custo("para_raios_2"), {"pacote_pesquisa": 80, "pacote_automacao": 80, "pacote_quimico": 80, "pacote_ecologico": 80, "pacote_tempestade": 80}, "custo da árvore")


func test_pega_e_protege() -> void:
	var m := _mapa()
	var pr := m.colocar("para_raios", Vector2i(0, 0), 0)
	var forn := m.colocar("fornalha", Vector2i(3, 0), 0)        # mais baixa que o para-raios, a 3 m
	verificar(pr >= 0 and forn >= 0, "montagem")
	var r := Raios.new(m, 3)
	var danos := {}
	r.dano = func(id: int, p: float) -> void: danos[id] = p
	var q := r.cair(Vector2(4.0, 1.0))                         # em cima da fornalha
	igual(q.tipo, "para_raios", "o para-raios pegou")
	igual(int(q.id), pr)
	verificar(danos.is_empty(), "a fornalha ficou inteira")
	var pt := r.ponta(pr)
	perto(float(q.alt), pt.z, 1e-6, "o raio bate na ponta")
	perto((q.pos as Vector2).distance_to(Vector2(0.5, 0.5)), 0.0, 1e-4, "no topo do mastro")
	var q2 := r.cair(Vector2(0.5 + 13.5, 0.5))
	igual(q2.tipo, "para_raios", "a 13,5 m ainda pega")
	var q3 := r.cair(Vector2(0.5 + 14.6, 0.5))
	igual(q3.tipo, "chao", "a 14,6 m não")
	igual(int(r.descargas[pr]), 2, "contador de descargas")
	# o de cristal pega mais longe; com dois, o mais perto
	var pc := m.colocar("para_raios_2", Vector2i(30, 0), 0)
	igual(r.cair(Vector2(30.5 + 21.0, 0.5)).tipo, "para_raios", "o de cristal pega a 21 m")
	igual(int(r.cair(Vector2(16.0, 0.5)).id), pc, "a 16 m do comum (fora dos 14) só o de cristal alcança")
	igual(int(r.cair(Vector2(9.0, 0.5)).id), pr, "a 8,5 m do comum e 21,5 m do de cristal: o comum")


func test_energia_para_os_acumuladores() -> void:
	var m := _mapa()
	var pr := m.colocar("para_raios", Vector2i(0, 0), 0)
	m.colocar("poste_energia", Vector2i(2, 0), 0)
	var a1 := m.colocar("acumulador", Vector2i(4, 0), 0)
	var a2 := m.colocar("acumulador", Vector2i(4, 3), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(Fiacao.ligacoes(m, m.estruturas[pr]) > 0, "o poste ligou no para-raios")
	var r := Raios.new(m, 3)
	r.fabrica = f
	var q := r.cair(Vector2(1.0, 1.0))
	perto(float(q.mj), 120.0, 1e-4, "120 MJ entraram na rede")
	perto(float(f.acumulado[a1]) + float(f.acumulado[a2]), 120.0, 1e-4, "nos dois acumuladores")
	perto(float(f.acumulado[a1]), 60.0, 1e-4, "divididos pelo espaço livre")
	var q2 := r.cair(Vector2(1.0, 1.0))
	perto(float(q2.mj), 40.0, 1e-4, "cheios (160 MJ): só 40 couberam")
	perto(float(f.acumulado[a1]), 80.0, 1e-4, "acumulador cheio")
	for i in 30:
		f.tick(1.0 / 30.0)
	verificar(float(f.acumulado[a1]) > 79.0, "a carga fica guardada no acumulador")
	# sem poste: só proteção
	var m2 := _mapa()
	var pr2 := m2.colocar("para_raios", Vector2i(0, 0), 0)
	m2.colocar("acumulador", Vector2i(10, 0), 0)
	var f2 := Fabrica.new(m2)
	f2.reconstruir()
	var r2 := Raios.new(m2, 3)
	r2.fabrica = f2
	var q3 := r2.cair(Vector2(1.0, 1.0))
	igual(int(q3.id), pr2, "pegou")
	perto(float(q3.mj), 0.0, 1e-6, "sem rede, o raio é só aterrado")


func test_no_mundo_protege_a_base() -> void:
	# 300 raios sorteados em volta de uma base pequena: sem para-raios as fornalhas apanham; com um no meio, nenhuma
	for com in [false, true]:
		var m := _mapa()
		var pr := m.colocar("para_raios", Vector2i(10, 6), 0) if com else -1
		m.colocar("fornalha", Vector2i(6, 6), 0)
		m.colocar("fornalha", Vector2i(13, 6), 0)
		var r := Raios.new(m, 11)
		var danos := [0]
		r.dano = func(_id: int, _p: float) -> void: danos[0] += 1
		var pegos := 0
		for i in 300:
			var q := r.cair(r.sortear_ponto(Vector2.ZERO))
			if q.tipo == "para_raios":
				pegos += 1
		if com:
			igual(danos[0], 0, "com o para-raios, nenhum raio pegou nas fornalhas")
			verificar(pegos > 120, "e ele pega boa parte dos raios em volta da base (%d de 300)" % pegos)
			igual(int(r.descargas[pr]), pegos)
		else:
			verificar(danos[0] > 10, "sem para-raios as fornalhas apanham (%d raios)" % danos[0])
