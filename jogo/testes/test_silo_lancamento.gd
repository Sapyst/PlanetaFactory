extends Caso
## Silo de lançamento (silo_lancamento, lote 17): modelo do estudo (estudo_silo_lancamento.py, do Antigravity;
## arte/estudos/conv_lote17.py), sem o foguete (o jogo o desenha crescendo com as partes e subindo); monta o foguete
## de proliferação por 100 partes (casco + 5 processadores quânticos + 50 de propelente), depois a carga-semente
## (núcleo-semente + mapa estelar + 10 módulos de produtividade 3) e lança: fim da campanha. As peças ainda não
## existem e as pesquisas (silo_lancamento, foguete_proliferacao) seguem em desenvolvimento.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(196, 206):
		for y in range(-4, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_dados_e_modelo() -> void:
	var r := SiloLancamento.regra("silo_lancamento")
	verificar(SiloLancamento.eh_silo("silo_lancamento"), "regra do silo")
	igual(int(r.partes), 100, "100 partes (árvore)")
	igual(int(r.parte.casco_foguete), 1, "parte: 1 casco")
	igual(int(r.parte.processador_quantico), 5, "parte: 5 processadores quânticos")
	igual(int(r.parte_fluido.propelente_cristal), 50, "parte: 50 de propelente")
	igual(int(r.carga.modulo_produtividade_3), 10, "carga: 10 módulos de produtividade 3")
	igual(Fiacao.papel("silo_lancamento"), "consumo", "precisa de energia")
	var md: Dictionary = Registro.modelos.get("silo_lancamento", {})
	igual(Registro.area("silo_lancamento"), Vector2i(3, 3), "3×3")
	igual(md.get("estudo", ""), "estudo_silo_lancamento.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (robôs e umbilicais)")
	verificar(float(md.dims[2]) < 4.0, "sem o foguete que sobe (%s)" % str(md.dims))
	var tipos := {}
	for p in md.get("portas", []):
		tipos[p.nome.right(2) + p.tipo] = true
	verificar(tipos.has("S1ITEM") and tipos.has("O1ITEM") and tipos.has("L1FLUIDO"), "bocas: itens sul e oeste, fluido leste (%s)" % str(tipos.keys()))
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/silo_lancamento.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "silo_lancamento" in cat.pecas), "no menu (Proliferação)")
	var raiz: Node = (load(str(md.modelo)) as PackedScene).instantiate()
	for n in raiz.find_children("*", "Node3D", true, false):
		var i := String(n.name).rfind("_")
		var suf := String(n.name).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor", "haste", "camisa"], "nome neutro: " + n.name)
	raiz.free()


func test_pesquisas_em_desenvolvimento() -> void:
	var p := Pesquisa.new()
	for id in ["silo_lancamento", "foguete_proliferacao"]:
		verificar(p.jogavel(id), "ligada no jogo: " + id)
		verificar(p.arvore()[id].get("existente", false), "marcada como existente: " + id)
		verificar(p.em_desenvolvimento(id), "em desenvolvimento: " + id)
	verificar(p.arvore().foguete_proliferacao.get("objetivo", false), "o foguete continua sendo o objetivo")
	verificar(not p.jogavel("casco_foguete") and not p.jogavel("propulsao_cristal"), "casco e propulsão ainda não existem")
	verificar(p.peca_em_desenvolvimento("silo_lancamento"), "silo em cinza fora da demonstração")
	verificar(not Pesquisa.new(true).peca_em_desenvolvimento("silo_lancamento"), "na demonstração se constrói")


func test_braco_so_poe_o_que_falta() -> void:
	var m := _mapa()
	var id := m.colocar("silo_lancamento", Vector2i(200, 0), 0)
	verificar(id >= 0, "coube")
	var f := Fabrica.new(m)
	f.reconstruir()
	var d: Object = f.destino_em(Vector2i(201, 1))
	verificar(d != null and not d.aceita("placa_ferro"), "não aceita o que o foguete não usa")
	for i in 3:
		d.receber("casco_foguete")
	igual(int(m.estruturas[id].silo_itens.get("casco_foguete", 0)), 2, "guarda 2 cascos (2 partes)")
	verificar(d.aceita("nucleo_semente"), "aceita o núcleo-semente (carga)")


func test_monta_carga_e_lanca() -> void:
	var m := _mapa()
	var id := m.colocar("silo_lancamento", Vector2i(200, 0), 0)
	var en := [1.0]
	var carga := [false]
	var s := SiloLancamento.new(m)
	s.energia = func(_i: int) -> float: return en[0]
	s.carga_liberada = func() -> bool: return carga[0]
	igual(s.motivo(id), "faltam_itens", "sem peças: espera")
	s.itens(id).merge({"casco_foguete": 2, "processador_quantico": 10})
	igual(s.motivo(id), "falta_propelente", "sem propelente: espera")
	perto(s.abastecer(id, "agua", 100.0), 0.0, 1e-6, "água não serve")
	perto(s.abastecer(id, "propelente_cristal", 1000.0), 500.0, 1e-6, "tanque de 500")
	igual(s.motivo(id), "", "monta")
	for i in 10:
		s.tick(1.0)
	igual(s.partes(id), 1, "1 parte em 10 s")
	igual(int(s.itens(id).casco_foguete), 1, "gastou 1 casco")
	igual(int(s.itens(id).processador_quantico), 5, "e 5 processadores")
	perto(s.propelente(id), 450.0, 1e-4, "e 50 de propelente")
	verificar(s.montando(id), "anima montando")
	en[0] = 0.0
	s.tick(5.0)
	igual(s.motivo(id), "sem_energia", "sem energia para")
	en[0] = 1.0
	m.estruturas[id]["partes"] = 100
	igual(s.motivo(id), "falta_pesquisa_carga", "100 partes: a carga espera a pesquisa")
	carga[0] = true
	igual(s.motivo(id), "faltam_itens", "falta a carga-semente")
	s.itens(id).merge({"nucleo_semente": 1, "mapa_estelar": 1, "modulo_produtividade_3": 10})
	verificar(not s.lancar(id), "sem carga não lança")
	for i in 30:
		s.tick(1.0)
	verificar(s.tem_carga(id) and s.pronto(id), "carga-semente pronta: foguete pronto")
	igual(s.eventos.filter(func(e): return e.tipo == "carga_pronta").size(), 1, "aviso de pronto")
	verificar(s.lancar(id), "lança")
	verificar(not s.lancar(id), "não lança duas vezes")
	s.tick(3.0)
	verificar(s.subida(id) > 1.0, "subindo (%.1f m)" % s.subida(id))
	s.tick(3.5)
	igual(s.eventos.filter(func(e): return e.tipo == "foguete_lancado").size(), 1, "foguete lançado: fim da campanha")
	igual(s.partes(id), 0, "o silo esvaziou")
	igual(int(m.estruturas[id].lancados), 1, "conta o lançamento")


func test_desenho_do_foguete() -> void:
	var m := _mapa()
	var id := m.colocar("silo_lancamento", Vector2i(200, 0), 0)
	var s := SiloLancamento.new(m)
	var ds := DesenhoSilo.new()
	ds.silo = s
	ds._process(0.1)
	igual(ds.visiveis(), 0, "sem partes: sem foguete")
	m.estruturas[id]["partes"] = 50
	ds._process(0.1)
	igual(ds.visiveis(), 1, "meio foguete à vista")
	ds.free()
