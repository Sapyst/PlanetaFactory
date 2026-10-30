extends Caso
## Acumulador de cristal (acumulador_cristal, lote 14 — energia II): modelo do estudo (estudo_acumulador_cristal.py, do
## Antigravity; arte/estudos/conv_lote14.py); pesquisa acumulador_cristal (acumulador 2 + ciência de tempestade;
## básico/automação/químico/ecológico/tempestade × 120, 12 s). Guarda 600 MJ e troca até 4 MW com a rede.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("acumulador_cristal", {})
	igual(Fiacao.papel("acumulador_cristal"), "fonte", "conta como fonte da rede")
	perto(float(r.acumula_mj), 600.0, 1e-6, "600 MJ (árvore)")
	perto(float(r.acumula_kw), 4000.0, 1e-6, "4 MW (árvore)")
	verificar(float(r.acumula_mj) > float(Registro.estruturas.acumulador_2.acumula_mj), "guarda mais que o acumulador 2")
	var md: Dictionary = Registro.modelos.get("acumulador_cristal", {})
	igual(Registro.area("acumulador_cristal"), Vector2i(2, 2), "2×2 (árvore)")
	igual(md.get("estudo", ""), "estudo_acumulador_cristal.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (ventilador, anel, cristais e LEDs do estudo)")
	verificar(float(md.dims[0]) <= 2.05 and float(md.dims[1]) <= 2.05, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 7000, "leve (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/acumulador_cristal.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "acumulador_cristal" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("acumulador_cristal", {}).is_empty(), "custo de construção")


func test_guarda_e_devolve_na_rede() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 52):
		for y in range(-6, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	var a := m.colocar("acumulador_cristal", Vector2i(0, 0), 0)
	var po0 := m.colocar("poste_energia", Vector2i(3, 0), 0)
	Fiacao.ligar_novo(m, a)
	Fiacao.ligar_novo(m, po0)
	var cargas := 0
	for x in range(0, 48, 4):                            # 12 refinadores = 5 MW: passa dos 4 MW que ele solta
		var pq := m.colocar("poste_energia", Vector2i(x, 3), 0)
		Fiacao.ligar_novo(m, pq)
		var q := m.colocar("refinador", Vector2i(x, 5), 0)
		Fiacao.ligar_novo(m, q)
		cargas += 1
	var f := Fabrica.new(m)
	f.reconstruir()
	igual(cargas, 12, "os 12 refinadores")
	f.acumulado[a] = 550.0
	f._membros[a].acum_mj = 550.0
	f.tick(1.0)
	perto(550.0 - float(f.acumulado[a]), 4.0, 0.01, "solta 4 MW, o limite dele")
	# carrega: um raio de 120 MJ passa de 600 MJ, o resto se perde
	f.acumulado[a] = 500.0
	f._membros[a].acum_mj = 500.0
	perto(f.injetar(a, 120.0), 100.0, 1e-3, "só cabem 100 MJ")
	perto(float(f.acumulado[a]), 600.0, 1e-3, "cheio em 600 MJ")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("acumulador_cristal"), "Acumulador de cristal ligada no jogo")
	verificar(not p.em_desenvolvimento("acumulador_cristal"), "fora do em desenvolvimento")
	var pacotes := {"pacote_pesquisa": 120, "pacote_automacao": 120, "pacote_quimico": 120, "pacote_ecologico": 120, "pacote_tempestade": 120}
	igual(p.custo("acumulador_cristal"), pacotes, "custo da árvore")
	verificar(not p.peca_liberada("acumulador_cristal"), "começa travado")
	p.concluidas = {"acumulacao_2": true}
	verificar(not p.disponivel("acumulador_cristal"), "pede a ciência de tempestade")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("acumulador_cristal"), "com acumulador 2 e ciência de tempestade: pesquisável")
	p.concluidas["acumulador_cristal"] = true
	verificar(p.peca_liberada("acumulador_cristal"), "libera o acumulador de cristal")
