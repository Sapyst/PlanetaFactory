extends Caso
## Painel solar 2 (painel_solar_2, lote 13 — energia I): modelo do estudo (estudo_painel_solar_2.py, do Antigravity;
## arte/estudos/conv_lote13.py) com o rastreador biaxial, limpadores e lentes; pesquisa renovavel_2 (renovável +
## processador; básico/automação/químico × 60, 8 s). Melhoria real do painel 1: 500 kW (o 1 dá 300) e com nuvem ou
## chuva perde só 15% (o 1 perde até ~80%); à noite, nada.


func _cena() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 8):
		for y in range(-4, 4):
			m.limpar_obstaculo(Vector2i(x, y))
	var p1 := m.colocar("painel_solar", Vector2i(-3, 0), 0)
	var p2 := m.colocar("painel_solar_2", Vector2i(1, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	return {"m": m, "f": f, "p1": p1, "p2": p2}


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("painel_solar_2", {})
	igual(Fiacao.papel("painel_solar_2"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -500.0, 1e-6, "500 kW (árvore)")
	igual(r.get("renovavel", ""), "sol", "renovável do sol")
	perto(float(r.perda_nuvem), 0.15, 1e-6, "perde só 15% com nuvem (árvore)")
	verificar(-float(r.energia_kw) > -float(Registro.estruturas.painel_solar.energia_kw), "mais forte que o painel 1")
	var md: Dictionary = Registro.modelos.get("painel_solar_2", {})
	igual(Registro.area("painel_solar_2"), Vector2i(2, 2), "2×2 (como o painel 1)")
	igual(md.get("estudo", ""), "estudo_painel_solar_2.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (rastreador do estudo)")
	verificar(float(md.dims[0]) <= 2.05 and float(md.dims[1]) <= 2.05, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 5500, "leve (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/painel_solar_2.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "painel_solar_2" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("painel_solar_2", {}).is_empty(), "custo de construção")


func test_rende_mais_e_aguenta_nuvem() -> void:
	var c := _cena()
	var f: Fabrica = c.f
	# meio-dia limpo
	f.sol = 1.0
	f.sol_limpo = 1.0
	f.encoberto = 0.0
	perto(-f.kw_de(c.p1), 300.0, 1e-3, "painel 1: 300 kW")
	perto(-f.kw_de(c.p2), 500.0, 1e-3, "painel 2: 500 kW")
	# tempestade (o mundo calcula o sol do painel 1 assim)
	f.sol = 1.0 * 0.5 * (1.0 - 0.5 * 1.0) * (1.0 - 0.6 * 1.0)
	f.encoberto = 1.0
	perto(-f.kw_de(c.p2), 425.0, 1e-3, "painel 2 encoberto: perde só 15%")
	verificar(-f.kw_de(c.p1) < 0.2 * 300.0, "painel 1 cai muito mais (%.0f kW)" % -f.kw_de(c.p1))
	# noite
	f.sol = 0.0
	f.sol_limpo = 0.0
	perto(-f.kw_de(c.p2), 0.0, 1e-6, "à noite, nada")


func test_entra_na_rede() -> void:
	var c := _cena()
	var m: MapaOcupacao = c.m
	var po := m.colocar("poste_energia", Vector2i(4, 2), 0)
	Fiacao.ligar_novo(m, po)
	var mq := m.colocar("montadora", Vector2i(5, -3), 0)
	Fiacao.ligar_novo(m, mq)
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(m.estruturas[c.p2].get("fios", []).has(po), "o poste ligou no painel 2")
	f.sol = 0.0
	f.sol_limpo = 1.0
	f.encoberto = 0.5
	f.tick(1.0 / 30.0)
	perto(f.rede.satisfacao(mq), 1.0, 1e-3, "a montadora roda com o painel 2 mesmo nublado")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("renovavel_2"), "Painel solar 2 ligada no jogo")
	verificar(not p.em_desenvolvimento("renovavel_2"), "fora do em desenvolvimento")
	igual(p.custo("renovavel_2"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60}, "custo da árvore")
	verificar(not p.peca_liberada("painel_solar_2"), "começa travado")
	p.concluidas = {"renovavel": true}
	verificar(not p.disponivel("renovavel_2"), "pede o processador")
	p.concluidas["processador"] = true
	verificar(p.disponivel("renovavel_2"), "com renovável e processador: pesquisável")
	p.concluidas["renovavel_2"] = true
	verificar(p.peca_liberada("painel_solar_2"), "libera o painel solar 2")
