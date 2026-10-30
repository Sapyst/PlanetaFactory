extends Caso
## Núcleo de singularidade (nucleo_singularidade, lote 14 — energia II): modelo do estudo (estudo_nucleo_singularidade.py,
## do Antigravity; arte/estudos/conv_lote14.py) com os 3 anéis, disco de acreção e ventoinhas; pesquisa singularidade
## (fusão + colônias; 7 pacotes × 500, 20 s). 100 MW, sem combustível e sem poluição. Continua em desenvolvimento até a
## computação quântica e o pacote quântico existirem; na Demonstração já se constrói.


func _c() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 16):
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	var n := m.colocar("nucleo_singularidade", Vector2i(0, 0), 0)
	return {"m": m, "n": n}


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("nucleo_singularidade", {})
	igual(Fiacao.papel("nucleo_singularidade"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -100000.0, 1e-6, "100 MW (árvore)")
	verificar(bool(r.get("inesgotavel", false)), "não gasta nada")
	verificar(float(r.get("poluicao", 0.0)) == 0.0, "sem poluição (árvore)")
	verificar(not Fiacao.eh_nucleo("nucleo_singularidade"), "não é o núcleo do jogador (não liga sem cabo)")
	var md: Dictionary = Registro.modelos.get("nucleo_singularidade", {})
	igual(Registro.area("nucleo_singularidade"), Vector2i(3, 3), "3×3 (árvore)")
	igual(md.get("estudo", ""), "estudo_nucleo_singularidade.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (anéis e disco do estudo)")
	verificar(float(md.dims[0]) <= 3.2 and float(md.dims[1]) <= 3.2, "cabe na área, com folga de 8 cm de cada lado (%s)" % str(md.dims))
	verificar(int(md.tris) <= 13000, "orçamento (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/nucleo_singularidade.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "nucleo_singularidade" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("nucleo_singularidade", {}).is_empty(), "custo de construção")


func test_gera_de_graca_na_rede() -> void:
	var c := _c()
	var m: MapaOcupacao = c.m
	var po := m.colocar("poste_energia", Vector2i(3, 0), 0)
	Fiacao.ligar_novo(m, po)
	var q := m.colocar("refinador", Vector2i(6, 0), 0)
	Fiacao.ligar_novo(m, q)
	var f := Fabrica.new(m)
	f.reconstruir()
	perto(-f.kw_de(c.n), 100000.0, 1e-3, "100 MW")
	verificar(not f.combustivel.has(c.n), "sem estoque de combustível")
	verificar(f.destino_em(Vector2i(0, 0)) == null, "não recebe item")
	f.tick(1.0)
	verificar(f.rede.satisfacao(q) > 0.99, "a máquina tem energia")
	verificar(f.transmitindo(c.n), "transmitindo")
	m.estruturas[c.n]["desligada"] = true
	perto(f.kw_de(c.n), 0.0, 1e-6, "desligado não gera")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("singularidade"), "Núcleo de singularidade ligada no progressao.json")
	var tipos := ["pacote_pesquisa", "pacote_automacao", "pacote_quimico", "pacote_ecologico", "pacote_tempestade", "pacote_quantico", "pacote_genese"]
	var custo := {}
	for t in tipos:
		custo[t] = 500
	igual(p.custo("singularidade"), custo, "custo da árvore")
	verificar(p.em_desenvolvimento("singularidade"), "em desenvolvimento: falta o pacote quântico e a fusão")
	verificar(p.peca_em_desenvolvimento("nucleo_singularidade"), "peça em desenvolvimento pelo mesmo motivo")
	verificar(p.motivo_desenvolvimento("singularidade") != "", "diz o motivo")
	verificar(not p.disponivel("singularidade"), "não se pesquisa")
	var q := Pesquisa.new()
	q.concluidas = {"singularidade": true}
	verificar(q.peca_liberada("nucleo_singularidade"), "pesquisada, libera a peça")
	verificar(Pesquisa.new(true).peca_liberada("nucleo_singularidade"), "na Demonstração já se constrói")
