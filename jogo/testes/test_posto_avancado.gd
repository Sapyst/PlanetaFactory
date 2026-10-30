extends Caso
## Posto avançado (posto_avancado, lote 17): modelo do estudo (estudo_posto_avancado.py, do Antigravity;
## arte/estudos/conv_lote17.py) com a antena girando e os pistões dos silos; núcleo-filho 3×3: 150 kW próprios sem
## cabo para as máquinas em volta (como o núcleo), estoque próprio de 3.200 itens por braço (estoque dos drones
## logísticos) e a obra perto dele paga primeiro com esse estoque. A pesquisa (transmissão + silo de granel + ciência
## militar; básico/automação/militar × 50) é jogável desde que a Transmissão longa (poste alto, lote 13) entrou.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(190, 240):
		for y in range(-8, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("posto_avancado", {})
	verificar(Fabrica.eh_posto("posto_avancado"), "regra do posto")
	perto(float(r.energia_kw), -150.0, 1e-6, "150 kW próprios (árvore)")
	verificar(bool(r.get("sem_fio", false)) and bool(r.get("inesgotavel", false)), "fonte sem cabo e sem combustível, como o núcleo")
	igual(Fiacao.papel("posto_avancado"), "poste", "papel de poste (liga as máquinas em volta)")
	verificar(Fiacao.eh_nucleo("posto_avancado"), "núcleo-filho")
	var md: Dictionary = Registro.modelos.get("posto_avancado", {})
	igual(Registro.area("posto_avancado"), Vector2i(3, 3), "3×3")
	igual(md.get("estudo", ""), "estudo_posto_avancado.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (antena e pistões do estudo)")
	verificar(float(md.dims[0]) <= 3.05 and float(md.dims[1]) <= 3.05, "não passa da área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 9500, "leve (%d triângulos)" % md.tris)
	var lados := {}
	for p in md.get("portas", []):
		if p.tipo == "ITEM" and p.io == "ENT":
			lados[p.nome.right(2)] = true
	igual(lados.size(), 4, "4 bocas de entrada, uma em cada borda (%s)" % str(lados.keys()))
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/posto_avancado.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "posto_avancado" in cat.pecas), "no menu (Proliferação)")
	verificar(not Registro.progressao.custos.get("posto_avancado", {}).is_empty(), "custo de construção")


func test_modelo_anima() -> void:
	var cena: PackedScene = load(str(Registro.modelos.posto_avancado.modelo))
	var raiz := cena.instantiate()
	var nomes := {}
	for n in raiz.find_children("*", "Node3D", true, false):
		nomes[String(n.name)] = n
	verificar(nomes.has("antena"), "antena irradiadora do estudo")
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo")
	for n in nomes:                                         # o Animador não mexe por cima (só toca o laço)
		var i := String(n).rfind("_")
		var suf := String(n).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor", "haste", "camisa"], "nome neutro: " + n)
	raiz.free()


func test_pesquisa_jogavel() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("posto_avancado"), "pesquisa ligada no jogo")
	verificar(p.arvore().posto_avancado.get("existente", false), "marcada como existente na árvore")
	igual(p.custo("posto_avancado"), {"pacote_pesquisa": 50, "pacote_automacao": 50, "pacote_militar": 50}, "custo da árvore")
	verificar(p.jogavel("transmissao"), "Transmissão longa (poste alto, lote 13) existe")
	verificar(not p.em_desenvolvimento("posto_avancado"), "saiu do em desenvolvimento")
	verificar(not p.peca_em_desenvolvimento("posto_avancado"), "a peça não fica mais em cinza")
	p.concluidas = {"silo_granel": true, "ciencia_militar": true, "automacao": true}
	verificar(not p.disponivel("posto_avancado"), "sem a transmissão não se escolhe")
	p.concluidas["transmissao"] = true
	verificar(p.disponivel("posto_avancado"), "com a transmissão: pesquisável")
	verificar(not p.peca_liberada("posto_avancado"), "a peça só sai com a pesquisa")
	p.concluidas["posto_avancado"] = true
	verificar(p.peca_liberada("posto_avancado"), "libera o posto")


func test_energia_propria_sem_cabo() -> void:
	var m := _mapa()
	var posto := m.colocar("posto_avancado", Vector2i(200, 0), 0)
	var farol := m.colocar("farol_cristal", Vector2i(205, 1), 0)
	var longe := m.colocar("farol_cristal", Vector2i(225, 1), 0)
	verificar(posto >= 0 and farol >= 0 and longe >= 0, "couberam")
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(Fiacao.fios(m.estruturas[farol]).has(posto), "o farol a 3 m da borda liga no posto")
	verificar(Fiacao.liga_sem_cabo(m.estruturas[posto], m.estruturas[farol]), "sem cabo (núcleo-filho)")
	verificar(not Fiacao.fios(m.estruturas[longe]).has(posto), "a 23 m não liga")
	for i in 5:
		f.tick(0.2)
	verificar(f.energia(farol) > 0.99, "o posto alimenta o farol sozinho (%.2f)" % f.energia(farol))
	perto(f.energia(longe), 0.0, 1e-6, "o de longe fica sem energia")
	var poste := m.colocar("poste_energia", Vector2i(206, 4), 0)
	Fiacao.ligar_novo(m, poste)
	if Fiacao.fios(m.estruturas[poste]).has(posto):
		verificar(not Fiacao.liga_sem_cabo(m.estruturas[posto], m.estruturas[poste]), "com poste é cabo, como o núcleo")


func test_estoque_proprio_por_braco_e_drones() -> void:
	var m := _mapa()
	var posto := m.colocar("posto_avancado", Vector2i(200, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(f.baus.has(posto), "tem estoque próprio")
	igual(f.capacidade_bau(posto), 3200, "3.200 itens")
	var dest: Object = f.destino_em(Vector2i(201, 1))
	verificar(dest != null and dest.receber("placa_ferro"), "braço põe item no posto")
	igual(int(f.baus[posto].get("placa_ferro", 0)), 1, "guardou")
	var orig: Object = f.origem_em(Vector2i(202, 2))
	igual(orig.pegar_para_braco(""), "placa_ferro", "braço tira do posto")
	var dr := Drones.new(m, f, Colonia.new(m, Poluicao.new(m.gerador), 3))
	igual(dr.papel(posto), "estoque", "drones logísticos usam o posto como estoque")
	igual(f.posto_que_cobre(Vector2i(220, 0)), posto, "obra a 19 m: coberta")
	igual(f.posto_que_cobre(Vector2i(240, 0)), -1, "a 39 m: fora dos 32 m")


func test_obra_perto_paga_com_o_estoque_do_posto() -> void:
	var m := _mapa()
	var posto := m.colocar("posto_avancado", Vector2i(200, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	var c := Construtor.new(m)
	c.cobrar = true
	c.inventario = {"placa_ferro": 2}
	c.estoque_local = func(t: Vector2i) -> Dictionary:
		var p := f.posto_que_cobre(t)
		return {} if p < 0 else {"id": p, "estoque": f.baus[p]}
	c.estoque_do_posto = func(p: int) -> Variant: return f.baus.get(p)
	f.baus[posto]["placa_ferro"] = 5
	# esteira custa 1 placa: perto do posto, 5 do posto + 2 do núcleo = 7 tiles verdes
	var pl := c.plano_linha("esteira", Vector2i(205, 4), Vector2i(214, 4), 0)
	igual(Construtor.contar(pl).ok, 7, "posto (5) + núcleo (2) dão 7 tiles")
	c.executar(pl)
	igual(int(f.baus[posto].get("placa_ferro", 0)), 0, "gastou o estoque do posto primeiro")
	igual(int(c.inventario.get("placa_ferro", 0)), 0, "e o resto do núcleo")
	c.desfazer()
	igual(int(f.baus[posto].get("placa_ferro", 0)), 5, "desfazer devolve ao posto")
	igual(int(c.inventario.get("placa_ferro", 0)), 2, "e ao núcleo")
	# longe do posto só o núcleo paga
	var pl2 := c.plano_linha("esteira", Vector2i(235, 6), Vector2i(238, 6), 0)
	igual(Construtor.contar(pl2).ok, 2, "longe: só as 2 do núcleo")
