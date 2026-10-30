extends Caso
## Receptor de cápsulas e colônias (receptor_capsulas e pesquisa colonias, lote 17): modelo do estudo
## (estudo_receptor_capsulas.py, do Antigravity; arte/estudos/conv_lote17.py) com garras, pistões, empurrador e roletes
## tocando uma vez por cápsula. Com a pesquisa Colônias, o núcleo-semente lançado vira colônia (posto com o kit) que
## fabrica 1 pacote gênese a cada 30 s e manda por cápsula ao receptor com energia mais perto; o pacote sai do receptor
## por braço. A pesquisa é jogável (núcleo-semente → posto avançado → transmissão, que entrou no lote 13).


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(190, 260):
		for y in range(-8, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_dados_item_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("receptor_capsulas", {})
	verificar(Genese.eh_receptor("receptor_capsulas"), "regra do receptor")
	igual(Fiacao.papel("receptor_capsulas"), "consumo", "precisa de energia")
	var c := Genese.cfg("posto_avancado")
	perto(float(c.genese_s), 30.0, 1e-6, "1 pacote gênese a cada 30 s por colônia (árvore)")
	igual(String(c.item), "pacote_genese", "fabrica pacote gênese")
	verificar(int(c.kit.get("drone", 0)) == 2, "kit com 2 drones (árvore)")
	verificar(Registro.itens.has("pacote_genese"), "item pacote gênese")
	verificar(not Registro.receitas.values().any(func(rc): return rc.get("saidas", {}).has("pacote_genese")), "sem receita: só as colônias fazem")
	verificar(ResourceLoader.exists("res://assets/icones/itens/pacote_genese.png"), "ícone do pacote")
	var md: Dictionary = Registro.modelos.get("receptor_capsulas", {})
	igual(Registro.area("receptor_capsulas"), Vector2i(2, 2), "2×2")
	igual(md.get("estudo", ""), "estudo_receptor_capsulas.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (garras, empurrador, roletes)")
	verificar(float(md.dims[0]) <= 2.0 and float(md.dims[1]) <= 2.0 and float(md.dims[2]) < 2.5, "na área, sem a cápsula pairando (%s)" % str(md.dims))
	var portas: Array = md.get("portas", [])
	verificar(portas.size() == 1 and portas[0].io == "SAI" and portas[0].dir[1] > 0, "boca de saída ao norte")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/receptor_capsulas.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "receptor_capsulas" in cat.pecas), "no menu (Proliferação)")


func test_modelo_nomes_neutros() -> void:
	var raiz: Node = (load(str(Registro.modelos.receptor_capsulas.modelo)) as PackedScene).instantiate()
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo")
	for n in raiz.find_children("*", "Node3D", true, false):
		var i := String(n.name).rfind("_")
		var suf := String(n.name).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor", "haste", "camisa", "pistao0", "pistao1"], "nome neutro: " + n.name)
	raiz.free()


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("colonias"), "Colônias ligada no jogo")
	verificar(p.arvore().colonias.get("existente", false), "marcada como existente na árvore")
	igual(p.custo("colonias"), {"pacote_pesquisa": 200, "pacote_automacao": 200, "pacote_quimico": 200, "pacote_ecologico": 200,
			"pacote_tempestade": 200}, "custo da árvore")
	verificar(not p.em_desenvolvimento("colonias"), "saiu do em desenvolvimento (a transmissão existe)")
	verificar(not p.peca_em_desenvolvimento("receptor_capsulas"), "receptor não fica mais em cinza")
	verificar(not p.disponivel("colonias"), "sem o núcleo-semente não se escolhe")
	p.concluidas = {"nucleo_semente": true, "drones_logisticos": true}
	verificar(not p.em_desenvolvimento("colonias") and p.disponivel("colonias"), "com o núcleo-semente: pesquisável")
	verificar(not p.modo_liberado("colonias"), "antes: a semente vira só posto")
	p.concluidas["colonias"] = true
	verificar(p.modo_liberado("colonias") and p.peca_liberada("receptor_capsulas"), "libera colônias e o receptor")


## Lança uma semente com/sem a pesquisa Colônias e devolve {m, f, l, pid}.
func _pousar(colonias: bool) -> Dictionary:
	var m := _mapa()
	var d := Descoberta.new()
	var f := Fabrica.new(m)
	var l := Lancador.new(m, d)
	l.colonias = func() -> bool: return colonias
	var alvo := Vector2(230.5, 0.5)
	l.voos.append({"de": Vector2(200, 0), "para": alvo, "t": 0.0, "total": 0.5, "altura": 5.0, "lancador": -1, "pousa": "posto_avancado", "procura": 6})
	l.tick(1.0)
	var ev := l.eventos.filter(func(e): return e.tipo == "semente_pousou")
	var pid: int = ev[0].id if not ev.is_empty() else -1
	f.reconstruir()
	return {"m": m, "f": f, "l": l, "pid": pid, "ev": ev}


func test_semente_vira_colonia_com_a_pesquisa() -> void:
	var sem := _pousar(false)
	verificar(sem.pid >= 0, "pousou")
	verificar(not sem.m.estruturas[sem.pid].get("colonia", false), "sem a pesquisa: posto avançado comum")
	igual((sem.f as Fabrica).baus[sem.pid], {}, "estoque vazio")
	var com := _pousar(true)
	verificar(com.pid >= 0 and com.m.estruturas[com.pid].get("colonia", false), "com Colônias: nasce colônia")
	verificar(bool(com.ev[0].colonia), "o evento avisa que é colônia")
	var b: Dictionary = (com.f as Fabrica).baus[com.pid]
	igual(int(b.get("drone", 0)), 2, "kit: 2 drones no estoque")
	verificar(int(b.get("placa_ferro", 0)) > 0, "kit: material")
	verificar(not com.m.estruturas[com.pid].has("kit_inicial"), "o kit foi para o estoque (uma vez)")


func test_colonia_manda_pacote_genese_ao_receptor() -> void:
	var c := _pousar(true)
	var m: MapaOcupacao = c.m
	var f: Fabrica = c.f
	var col: int = c.pid
	var g := Genese.new(m, f)
	igual(g.colonias(), [col] as Array[int], "uma colônia")
	# sem receptor: o pacote espera no estoque da colônia
	for i in 30:
		g.tick(1.0)
	igual(g.esperando(col), 1, "30 s sem receptor: 1 pacote esperando na colônia")
	var rid := m.colocar("receptor_capsulas", Vector2i(196, 2), 0)
	verificar(rid >= 0, "receptor coube")
	f.reconstruir()
	# energia: sem rede montada, energia 0 → o receptor não serve
	igual(g.receptor_para(g.centro(col)), -1, "receptor sem energia não recebe")
	var g2 := Genese.new(m, null)                         # sem fábrica: energia plena (lógica pura)
	g2.voos = g.voos
	igual(g2.receptor_para(g2.centro(col)), rid, "com energia: o receptor mais perto")
	m.estruturas[col]["genese_t"] = 29.95
	g2.tick(0.1)
	igual(g2.voos.size(), 1, "cápsula no ar")
	var v: Dictionary = g2.voos[0]
	igual(int(v.receptor), rid, "para o receptor")
	perto(float(v.total), g2.centro(col).distance_to(g2.centro(rid)) / 60.0, 1e-3, "a 60 m/s")
	for i in int(ceil(float(v.total))) + 1:
		g2.tick(1.0)
	igual(g2.voos.size(), 0, "chegou")
	igual(int(g2.recebido(rid).get("pacote_genese", 0)), 1, "1 pacote gênese no receptor")
	verificar(g2.animando(rid), "o receptor toca o laço (garras)")
	igual(g2.eventos.filter(func(e): return e.tipo == "capsula_chegou").size(), 1, "evento da chegada")
	var orig: Object = f.origem_em(Vector2i(196, 2))
	verificar(orig != null and orig.pegar_para_braco("") == "pacote_genese", "o braço tira o pacote do receptor")
	verificar(f.destino_em(Vector2i(196, 2)) == null, "o receptor não aceita item de braço")


func test_receptor_cheio_e_perdida() -> void:
	var m := _mapa()
	var rid := m.colocar("receptor_capsulas", Vector2i(200, 0), 0)
	var g := Genese.new(m, null)
	g.recebido(rid)["pacote_genese"] = 100
	igual(g.receptor_para(Vector2(230, 0)), -1, "cheio: não é destino")
	g.voos.append({"de": Vector2(230, 0), "para": g.centro(rid), "t": 0.0, "total": 0.5, "altura": 4.0, "receptor": rid, "item": "pacote_genese", "colonia": -1})
	g.tick(1.0)
	igual(g.eventos.filter(func(e): return e.tipo == "capsula_perdida").size(), 1, "cápsula para receptor cheio se perde")
	var st := str_to_var(var_to_str(g.estado())) as Dictionary
	var g2 := Genese.new(m, null)
	g2.restaurar(st)
	igual(g2.voos.size(), 0, "salvo sem voos")
