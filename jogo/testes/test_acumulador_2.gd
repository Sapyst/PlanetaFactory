extends Caso
## Acumulador 2 (acumulador_2, lote 13 — energia I): modelo do estudo (estudo_acumulador_2.py, do Antigravity;
## arte/estudos/conv_lote14.py) com ventilador, anel de foco, cristal e as 12 barras de LED; pesquisa acumulacao_2
## (acumulação + processador; básico/automação/químico × 60, 8 s). Guarda 200 MJ e troca até 1,5 MW com a rede.


func _cena() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 12):
		for y in range(-6, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	var po := m.colocar("poste_energia", Vector2i(3, 0), 0)
	var g := m.colocar("gerador", Vector2i(0, 0), 0)
	var a := m.colocar("acumulador_2", Vector2i(5, 0), 0)
	for id in [po, g, a]:
		Fiacao.ligar_novo(m, id)
	var f := Fabrica.new(m)
	f.reconstruir()
	return {"m": m, "f": f, "g": g, "a": a, "po": po}


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("acumulador_2", {})
	igual(Fiacao.papel("acumulador_2"), "fonte", "conta como fonte da rede")
	perto(float(r.acumula_mj), 200.0, 1e-6, "200 MJ (árvore)")
	perto(float(r.acumula_kw), 1500.0, 1e-6, "1,5 MW (árvore)")
	verificar(float(r.acumula_mj) > float(Registro.estruturas.acumulador.acumula_mj), "guarda mais que o acumulador")
	var md: Dictionary = Registro.modelos.get("acumulador_2", {})
	igual(Registro.area("acumulador_2"), Vector2i(2, 2), "2×2 (árvore)")
	igual(md.get("estudo", ""), "estudo_acumulador_2.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (ventilador, anel e LEDs do estudo)")
	verificar(float(md.dims[0]) <= 2.05 and float(md.dims[1]) <= 2.05, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 9000, "leve (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/acumulador_2.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "acumulador_2" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("acumulador_2", {}).is_empty(), "custo de construção")


func test_carrega_ate_1_5_mw_e_guarda_mais_de_80_mj() -> void:
	var c := _cena()
	var f: Fabrica = c.f
	f.combustivel[c.g] = 400.0
	f.tick(1.0)
	var um: float = f.acumulado[c.a]
	verificar(um > 0.8 and um <= 0.9001, "carrega com a sobra do gerador, 900 kW (%.2f MJ em 1 s)" % um)
	f.acumulado[c.a] = 199.5
	f._membros[c.a].acum_mj = 199.5
	f.tick(1.0)
	perto(float(f.acumulado[c.a]), 200.0, 1e-3, "enche em 200 MJ")
	f.tick(1.0)
	perto(float(f.acumulado[c.a]), 200.0, 1e-3, "e não passa")


func test_descarrega_para_as_maquinas() -> void:
	var c := _cena()
	var m: MapaOcupacao = c.m
	var f0: Fabrica = c.f
	f0.combustivel[c.g] = 0.0
	var maqs: Array[int] = []
	for x in [-5, -1, 3, 7]:                               # 4 refinadores = 1,68 MW: passa do que ele solta (1,5 MW)
		var pq := m.colocar("poste_energia", Vector2i(x, 3), 0)
		Fiacao.ligar_novo(m, pq)
		var q := m.colocar("refinador", Vector2i(x, 5), 0)
		Fiacao.ligar_novo(m, q)
		maqs.append(q)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.acumulado[c.a] = 100.0
	f._membros[c.a].acum_mj = 100.0
	f.tick(1.0)
	var gasto := 100.0 - float(f.acumulado[c.a])
	igual(maqs.size(), 4, "quatro refinadores")
	perto(gasto, 1.5, 0.01, "solta 1,5 MW, o limite dele (%.2f MJ em 1 s)" % gasto)


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("acumulacao_2"), "Acumulador 2 ligada no jogo")
	verificar(not p.em_desenvolvimento("acumulacao_2"), "fora do em desenvolvimento")
	igual(p.custo("acumulacao_2"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60}, "custo da árvore")
	verificar(not p.peca_liberada("acumulador_2"), "começa travado")
	p.concluidas = {"acumulacao": true}
	verificar(not p.disponivel("acumulacao_2"), "pede o processador")
	p.concluidas["processador"] = true
	verificar(p.disponivel("acumulacao_2"), "com acumulação e processador: pesquisável")
	p.concluidas["acumulacao_2"] = true
	verificar(p.peca_liberada("acumulador_2"), "libera o acumulador 2")
