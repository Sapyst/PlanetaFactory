extends Caso
## Captador de carga (captador_carga, 2×2) — fase 2.5; estudo_captador_carga.py via arte/estudos/conv_clima.py.
## Mastro próprio que pega os raios a até 10 m (antes dos para-raios). Cada raio carrega 1 cristal lapidado (boca sul,
## por braço) + 30 de água (cano pela borda norte) em 1 cristal carregado (sai pela boca oeste); a sobra do raio
## (60 MJ) vai para os acumuladores da rede. Sem raio não faz nada: fica "de prontidão" com o insumo dentro.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-12, 40):
		for y in range(-12, 20):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


func test_dados_e_modelo() -> void:
	var md: Dictionary = Registro.modelos.get("captador_carga", {})
	igual(md.get("estudo", ""), "estudo_captador_carga.py", "convertido do estudo")
	igual(Registro.area("captador_carga"), Vector2i(2, 2), "2×2")
	verificar(float(md.dims[0]) <= 2.0 and float(md.dims[1]) <= 2.0, "dentro da área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 10000, "orçamento (%d)" % md.tris)
	verificar(md.get("anima", false), "anima (carrossel, eletrodos) depois do raio")
	var nomes := (md.portas as Array).map(func(p): return p.nome)
	nomes.sort()
	igual(nomes, ["PORTA_FLUIDO_ENT_N0", "PORTA_ITEM_ENT_S1", "PORTA_ITEM_SAI_O0"], "portas do estudo")
	verificar(md.get("ponta_raio", []).size() == 3 and float(md.ponta_raio[2]) > 3.0, "ponta captora no alto do mastro")
	verificar(float(md.ponta_raio[0]) > 0.3 and float(md.ponta_raio[1]) > 0.3, "no canto nordeste")
	verificar(ResourceLoader.exists("res://assets/icones/captador_carga.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Clima" and "captador_carga" in cat.pecas), "aba Clima")
	var r: Dictionary = Registro.receitas.carregar_cristal
	igual(r.maquina, "captador")
	igual(_int(r.entradas), {"cristal_lapidado": 1}, "1 cristal lapidado")
	igual(_int(r.entradas_fluido), {"agua": 30}, "+ 30 de água (árvore)")
	igual(_int(r.saidas), {"cristal_carregado": 1}, "→ 1 cristal carregado")
	verificar(Registro.itens.has("cristal_carregado"), "item cristal carregado")
	verificar(ResourceLoader.exists("res://assets/icones/itens/cristal_carregado.png"), "ícone do cristal carregado")
	verificar(Registro.modelos.has(Registro.itens.cristal_carregado.get("modelo_de", "")), "modelo (derivado) na esteira")
	igual(Fiacao.papel("captador_carga"), "fonte", "liga num poste (a sobra do raio vai para a rede)")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("captador_carga"), "jogável")
	p.concluidas = {"para_raios": true, "acumulacao": true}
	verificar(not p.disponivel("captador_carga"), "espera a química")
	p.concluidas["quimica"] = true
	verificar(p.disponivel("captador_carga"), "para-raios + acumulação + química")
	igual(p.custo("captador_carga"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60}, "custo da árvore")
	p.concluidas["captador_carga"] = true
	verificar(p.peca_liberada("captador_carga"), "libera o captador")


func test_raio_carrega_cristal() -> void:
	var m := _mapa()
	var id := m.colocar("captador_carga", Vector2i(0, 0), 0)
	verificar(id >= 0, "montagem")
	var f := Fabrica.new(m)
	f.reconstruir()
	var mq: Maquina = f.maquinas[id]
	igual(mq.receita_id, "carregar_cristal", "receita fixa")
	verificar(mq.aceita("cristal_lapidado"), "aceita cristal lapidado pelo braço")
	verificar(mq.falta_fluido("agua") >= 60.0, "tanque de água (%.0f)" % mq.falta_fluido("agua"))
	f.tick(0.1)
	igual(mq.estado, Maquina.Estado.SEM_INSUMO, "vazio: esperando insumo")
	mq.receber("cristal_lapidado")
	mq.receber("cristal_lapidado")
	mq.receber_fluido("agua", 60.0)
	for i in 30:
		f.tick(0.1)
	igual(mq.estado, Maquina.Estado.PRONTIDAO, "com insumo: de prontidão, esperando o raio")
	igual(int(mq.saidas.get("cristal_carregado", 0)), 0, "sem raio não carrega nada")
	var r := Raios.new(m, 3)
	r.fabrica = f
	var q := r.cair(Vector2(3.0, 3.0))
	igual(q.tipo, "captador", "o captador pegou")
	verificar(q.carregou, "carregou um cristal")
	igual(int(mq.saidas.get("cristal_carregado", 0)), 1, "1 cristal carregado pronto")
	igual(int(mq.entradas.get("cristal_lapidado", 0)), 1, "gastou 1 lapidado")
	perto(float(mq.fluidos.agua), 30.0, 1e-6, "gastou 30 de água")
	f.tick(0.1)
	igual(mq.estado, Maquina.Estado.TRABALHANDO, "a descarga anima os eletrodos")
	for i in 50:
		f.tick(0.1)
	igual(mq.estado, Maquina.Estado.PRONTIDAO, "depois volta à prontidão")
	igual(mq.pegar_para_braco(""), "cristal_carregado", "o braço tira o cristal carregado")
	r.cair(Vector2(1.0, 1.0))
	r.cair(Vector2(1.0, 1.0))
	igual(int(mq.saidas.get("cristal_carregado", 0)), 1, "segundo raio carregou o último lapidado; o terceiro não tinha insumo")
	igual(int(r.descargas[id]), 3, "mas pegou os três (protege)")


func test_prioridade_sobre_para_raios() -> void:
	var m := _mapa()
	var cap := m.colocar("captador_carga", Vector2i(0, 0), 0)
	var pr := m.colocar("para_raios", Vector2i(6, 0), 0)
	var r := Raios.new(m, 3)
	var pc := r.ponta(cap)
	var q := r.cair(Vector2(6.5, 0.5))                       # em cima do para-raios, a ~6 m da ponta do captador
	verificar(Vector2(pc.x, pc.y).distance_to(Vector2(6.5, 0.5)) < 10.0, "dentro dos 10 m do captador")
	igual(int(q.id), cap, "o captador pega antes do para-raios")
	var q2 := r.cair(Vector2(15.5, 0.5))
	igual(int(q2.id), pr, "fora dos 10 m do captador, o para-raios")


func test_sobra_vai_para_a_rede() -> void:
	var m := _mapa()
	var cap := m.colocar("captador_carga", Vector2i(0, 0), 0)
	m.colocar("poste_energia", Vector2i(3, 0), 0)
	var a := m.colocar("acumulador", Vector2i(5, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	var r := Raios.new(m, 3)
	r.fabrica = f
	var q := r.cair(Vector2(1.0, 1.0))
	igual(int(q.id), cap)
	verificar(not q.carregou, "sem insumo não carrega")
	perto(float(f.acumulado[a]), 60.0, 1e-4, "60 MJ para o acumulador")
