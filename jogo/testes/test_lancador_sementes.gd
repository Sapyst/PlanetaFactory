extends Caso
## Lançador de sementes (lancador_sementes, lote 17): modelo do estudo (estudo_lancador_sementes.py, do Antigravity;
## arte/estudos/conv_lote17.py) com o disparo (culatra, recuo e pistões) tocando uma vez por tiro; item e receita
## núcleo-semente (montadora); recebe a semente por braço, carrega com energia, dispara e a cápsula voa até o alvo
## (rumo e distância do painel, 60–400 m); onde pousa nasce um posto avançado. A pesquisa Núcleo-semente é jogável
## (pede o posto avançado, que saiu do "em desenvolvimento" com a Transmissão longa — poste alto, lote 13).


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(196, 206):
		for y in range(-4, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


## Lançador em (200, 0) + lógica; o alvo vai para um chão seco e plano achado perto.
func _cena(energia := [1.0]) -> Dictionary:
	var m := _mapa()
	var d := Descoberta.new()
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var id := m.colocar("lancador_sementes", Vector2i(200, 0), 0)
	verificar(id >= 0, "lançador coube (%s)" % m.motivo_bloqueio("lancador_sementes", Vector2i(200, 0), 0))
	var l := Lancador.new(m, d)
	l.colonia = c
	l.energia = func(_id: int) -> float: return energia[0]
	return {"m": m, "d": d, "c": c, "id": id, "l": l}


## Primeiro rumo/distância com pouso possível (o mapa tem rio, lago e encosta).
func _mirar_valido(l: Lancador, id: int) -> bool:
	for dist in [200, 150, 250, 300, 100]:
		for r in 8:
			l.mirar(id, r, dist)
			if l.motivo(id) in ["", "sem_semente"] and l.lugar_de_pouso(l.alvo(id)) != Lancador.SEM_LUGAR:
				return true
	return false


func test_dados_item_receita_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("lancador_sementes", {})
	verificar(Lancador.eh_lancador("lancador_sementes"), "regra do lançador")
	perto(float(r.lancador.alcance), 400.0, 1e-6, "alcance de 400 m (árvore)")
	igual(String(r.lancador.pousa), "posto_avancado", "a semente vira posto avançado")
	igual(Fiacao.papel("lancador_sementes"), "consumo", "precisa de energia")
	verificar(Registro.itens.has("nucleo_semente"), "item núcleo-semente")
	var rec: Dictionary = Registro.receitas.get("nucleo_semente", {})
	var ent := {}
	for k in rec.get("entradas", {}):
		ent[k] = int(rec.entradas[k])
	igual(ent, {"nucleo_cristal": 4, "celula_energia": 2, "liga_leve": 10, "processador": 2}, "receita da árvore")
	igual(int(rec.get("saidas", {}).get("nucleo_semente", 0)), 1, "→ 1 núcleo-semente")
	perto(float(rec.tempo), 60.0, 1e-6, "60 s")
	igual(rec.maquina, "montadora", "na montadora (a montadora 3 da árvore ainda não existe)")
	verificar(ResourceLoader.exists("res://assets/icones/itens/nucleo_semente.png"), "ícone do item")
	var md: Dictionary = Registro.modelos.get("lancador_sementes", {})
	igual(Registro.area("lancador_sementes"), Vector2i(3, 3), "3×3")
	igual(md.get("estudo", ""), "estudo_lancador_sementes.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (disparo do estudo)")
	verificar(int(md.tris) <= 8500, "leve (%d triângulos)" % md.tris)
	var portas: Array = md.get("portas", [])
	verificar(portas.size() == 1 and portas[0].nome.ends_with("S1") and portas[0].io == "ENT", "boca de entrada ao sul")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/lancador_sementes.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "lancador_sementes" in cat.pecas), "no menu (Proliferação)")
	verificar(not Registro.progressao.custos.get("lancador_sementes", {}).is_empty(), "custo de construção")


func test_modelo_sem_a_capsula_que_voa() -> void:
	var cena: PackedScene = load(str(Registro.modelos.lancador_sementes.modelo))
	var raiz := cena.instantiate()
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo (disparo)")
	var md: Dictionary = Registro.modelos.lancador_sementes
	verificar(float(md.dims[1]) < 3.4 and float(md.dims[2]) < 4.6, "a cápsula que voa saiu do modelo (%s: só o tubo passa 0,14 m da borda norte)" % str(md.dims))
	for n in raiz.find_children("*", "Node3D", true, false):
		var i := String(n.name).rfind("_")
		var suf := String(n.name).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor", "haste", "camisa"], "nome neutro: " + n.name)
	raiz.free()


func test_pesquisa_jogavel() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("nucleo_semente"), "pesquisa ligada no jogo")
	verificar(p.arvore().nucleo_semente.get("existente", false), "marcada como existente na árvore")
	igual(p.custo("nucleo_semente"), {"pacote_pesquisa": 150, "pacote_automacao": 150, "pacote_quimico": 150, "pacote_ecologico": 150,
			"pacote_tempestade": 150}, "custo da árvore")
	verificar(not p.em_desenvolvimento("nucleo_semente"), "saiu do em desenvolvimento (a transmissão existe)")
	verificar(not p.peca_em_desenvolvimento("lancador_sementes"), "a peça não fica mais em cinza")
	verificar(not p.disponivel("nucleo_semente"), "sem o posto avançado não se escolhe")
	verificar(not p.em_desenvolvimento("colonias"), "Colônias (receptor de cápsulas) também saiu")
	p.concluidas = {"posto_avancado": true, "drones_frota_1": true, "ciencia_tempestade": true}
	verificar(not p.em_desenvolvimento("nucleo_semente") and p.disponivel("nucleo_semente"), "com o posto avançado: pesquisável")
	p.concluidas["nucleo_semente"] = true
	verificar(p.peca_liberada("lancador_sementes") and p.receita_liberada("nucleo_semente"), "libera o lançador e a receita")


func test_recebe_so_o_nucleo_semente() -> void:
	var c := _cena()
	var f := Fabrica.new(c.m)
	f.reconstruir()
	var dest: Object = f.destino_em(Vector2i(201, 1))
	verificar(dest != null, "aceita braço")
	verificar(not dest.aceita("placa_ferro"), "não aceita outra coisa")
	verificar(dest.receber("nucleo_semente"), "recebe o núcleo-semente")
	igual(c.l.sementes(c.id), 1, "1 semente dentro")
	verificar(not dest.aceita("nucleo_semente"), "cabe 1")


func test_alvo_rumo_e_distancia() -> void:
	var c := _cena()
	var l: Lancador = c.l
	var id: int = c.id
	l.mirar(id, 2, 300)
	perto(l.alvo(id).distance_to(l.centro(id) + Vector2(300, 0)), 0.0, 1e-3, "300 m a leste")
	l.mirar(id, 0, 1000)
	perto(l.distancia(id), 400.0, 1e-6, "preso no alcance de 400 m")
	l.mirar(id, 4, 10)
	perto(l.distancia(id), 60.0, 1e-6, "mínimo de 60 m")
	verificar(l.alvo(id).y < l.centro(id).y, "rumo sul")
	igual(l.motivo(id), "sem_semente", "sem semente não carrega")


func test_dispara_voa_e_pousa_como_posto_avancado() -> void:
	var energia := [1.0]
	var c := _cena(energia)
	var l: Lancador = c.l
	var m: MapaOcupacao = c.m
	var id: int = c.id
	verificar(_mirar_valido(l, id), "achou um alvo seco e plano")
	m.estruturas[id]["sementes"] = 1
	igual(l.motivo(id), "", "com semente, energia e alvo: carrega")
	energia[0] = 0.0
	l.tick(1.0)
	igual(l.motivo(id), "sem_energia", "sem energia: parado")
	perto(l.carga(id), 0.0, 1e-6, "não carregou")
	energia[0] = 0.5
	for i in 39:
		l.tick(1.0)
	verificar(not l.disparando(id), "meia energia: 39 s ainda não basta (40 s)")
	l.tick(1.0)
	verificar(l.disparando(id), "carregou: disparo")
	igual(l.eventos.filter(func(e): return e.tipo == "disparo_inicio").size(), 1, "evento do disparo (o laço toca do começo)")
	l.tick(1.0)
	igual(l.voos.size(), 0, "a cápsula ainda está na culatra")
	l.tick(1.5)
	igual(l.voos.size(), 1, "saiu no quadro 50 (2,08 s)")
	igual(l.sementes(id), 0, "gastou a semente")
	var alvo := l.alvo(id)
	var v: Dictionary = l.voos[0]
	perto(float(v.total), l.distancia(id) / 40.0, 1e-3, "voa a 40 m/s")
	var meio := v.duplicate()
	meio.t = float(v.total) * 0.5
	verificar(Lancador.posicao_no_voo(meio).z > 20.0, "em arco (%.0f m no alto)" % Lancador.posicao_no_voo(meio).z)
	var conta_postos := func() -> int: return m.estruturas.values().filter(func(e): return e.nome == "posto_avancado").size()
	var antes: int = conta_postos.call()
	var d: Descoberta = c.d
	for i in int(ceil(float(v.total))) + 1:
		l.tick(1.0)
	igual(l.voos.size(), 0, "pousou")
	var pousos := l.eventos.filter(func(e): return e.tipo == "semente_pousou")
	igual(pousos.size(), 1, "evento do pouso")
	igual(conta_postos.call(), antes + 1, "um posto avançado novo")
	if pousos.size() == 1:
		var pid: int = pousos[0].id
		igual(m.estruturas[pid].nome, "posto_avancado", "nasceu um posto avançado")
		verificar((pousos[0].para as Vector2).distance_to(alvo) <= 9.0, "perto do alvo (%.1f m)" % (pousos[0].para as Vector2).distance_to(alvo))
		verificar(d.chunk_completo(Grade.chunk_de(Vector2i((pousos[0].para as Vector2).floor()))), "o chunk do pouso saiu da névoa")
		igual((pousos[0].rel.colocados as Array), [pid], "relatório para o mundo criar o nó")
	verificar(not l.disparando(id), "o laço terminou")
	igual(l.motivo(id), "sem_semente", "espera a próxima semente")


func test_semente_se_perde_sem_lugar() -> void:
	var c := _cena()
	var l: Lancador = c.l
	l.voos.append({"de": Vector2(200, 0), "para": Vector2(-100000, -100000), "t": 0.0, "total": 0.5, "altura": 1.0, "lancador": c.id,
			"pousa": "posto_avancado", "procura": 0})
	var m: MapaOcupacao = c.m
	# ocupa o alvo: o próprio lançador no centro do pouso
	l.voos[0].para = l.centro(c.id)
	var antes := m.estruturas.size()
	l.tick(1.0)
	igual(m.estruturas.size(), antes, "nada nasce em cima do lançador")
	igual(l.eventos.filter(func(e): return e.tipo == "semente_perdida").size(), 1, "aviso de semente perdida")


func test_salva_e_restaura() -> void:
	var c := _cena()
	var l: Lancador = c.l
	verificar(_mirar_valido(l, c.id), "alvo")
	c.m.estruturas[c.id]["sementes"] = 1
	for i in 25:
		l.tick(1.0)
	verificar(l.voos.size() == 1, "semente no ar")
	var st := str_to_var(var_to_str(l.estado())) as Dictionary
	var l2 := Lancador.new(c.m, c.d)
	l2.restaurar(st)
	igual(l2.voos.size(), 1, "o voo volta do salvo")
	perto(float(l2.voos[0].t), float(l.voos[0].t), 1e-4, "no mesmo ponto")
	igual(l2.rumo(c.id), l.rumo(c.id), "o alvo fica na estrutura (vai no mapa)")
