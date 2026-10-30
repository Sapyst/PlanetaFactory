extends Caso
## Turbina alta (turbina_alta, lote 14 — energia II): modelo do estudo (estudo_turbina_alta.py, do Antigravity;
## arte/estudos/conv_lote14.py) com nacele e rotor nas partes que o Animador vira para o vento; pesquisa turbina_alta
## (renovável + liga leve; básico/automação/químico × 60, 8 s), que é o que destrava o Defletor de vento. 600 kW, a
## mesma curva da turbina eólica; conta como +2 níveis de altura no vento do lugar.


func _cena() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 12):
		for y in range(-4, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	var t1 := m.colocar("turbina_eolica", Vector2i(-3, 0), 0)
	var t2 := m.colocar("turbina_alta", Vector2i(2, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	return {"m": m, "f": f, "t1": t1, "t2": t2}


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("turbina_alta", {})
	igual(Fiacao.papel("turbina_alta"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -600.0, 1e-6, "600 kW (árvore)")
	igual(r.get("renovavel", ""), "vento", "renovável do vento")
	perto(float(r.altura_vento), 2.0, 1e-6, "+2 níveis de altura (árvore)")
	var md: Dictionary = Registro.modelos.get("turbina_alta", {})
	igual(Registro.area("turbina_alta"), Vector2i(3, 3), "3×3 (árvore)")
	igual(md.get("estudo", ""), "estudo_turbina_alta.py", "convertido do estudo do Antigravity")
	var partes: Array = md.get("partes", []).map(func(p): return p.nome)
	for n in ["nacele", "helice", "rotor", "antena"]:
		verificar(n in partes, "parte do Animador: " + n)
	verificar(int(md.tris) <= 8000, "leve (%d triângulos)" % md.tris)
	verificar(float(md.dims[2]) > 5.0, "bem mais alta que a eólica (%.1f m)" % float(md.dims[2]))
	verificar(md.get("portas", []).is_empty(), "sem bocas")
	igual(md.get("terminais", []).size(), 4, "fio preso na base, 4 cantos")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/turbina_alta.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "turbina_alta" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("turbina_alta", {}).is_empty(), "custo de construção")


func test_rende_tres_vezes_a_eolica() -> void:
	var c := _cena()
	var f: Fabrica = c.f
	f.vento = 0.8
	var v1 := -f.kw_de(c.t1)
	var v2 := -f.kw_de(c.t2)
	verificar(v1 > 0.0, "a eólica gira")
	perto(v2, v1 * 3.0, 1e-3, "mesma curva, 3× a potência")
	f.vento = 0.05
	perto(-f.kw_de(c.t2), 0.0, 1e-6, "na calmaria para, como a eólica")
	f.vento = 1.5
	verificar(f.em_protecao(c.t2), "na ventania põe as pás em bandeira")


func test_conta_dois_niveis_de_altura() -> void:
	var c := _cena()
	var m: MapaOcupacao = c.m
	var v := VentoLocal.new(m.gerador, m, null)
	var por_nivel := float(Registro.ambiente.vento_local.por_nivel)
	var alto_max := float(Registro.ambiente.vento_local.alto_max)
	# procura um chão plano (sem desnível em volta): ali +2 níveis valem por inteiro
	var t := Vector2i(9999, 0)
	for x in range(-120, 120, 3):
		for y in range(-120, 120, 3):
			if t.x == 9999 and absf(v._desnivel(Vector2i(x, y))) < 0.01:
				t = Vector2i(x, y)
	verificar(t.x != 9999, "achou chão plano")
	var f0 := v.fator(t)
	perto(v.fator(t, Vector2.ZERO, 2.0), minf(f0 + 2.0 * por_nivel, float(Registro.ambiente.vento_local.get("maximo", 1.6))), 1e-5, "+2 níveis = +%.0f%%" % (2.0 * por_nivel * 100))
	# no alto do morro o limite é o mesmo de qualquer lugar: não passa do alto_max
	var morro := Vector2i(9999, 0)
	for x in range(-400, 400, 7):
		for y in range(-400, 400, 7):
			if morro.x == 9999 and v._desnivel(Vector2i(x, y)) * por_nivel >= alto_max:
				morro = Vector2i(x, y)
	if morro.x != 9999:
		perto(v.fator(morro, Vector2.ZERO, 2.0), v.fator(morro), 1e-5, "no topo do morro não ganha mais que o limite")


func test_pesquisa_e_destrava_o_defletor() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("turbina_alta"), "Turbina eólica alta ligada no jogo")
	verificar(not p.em_desenvolvimento("turbina_alta"), "fora do em desenvolvimento")
	igual(p.custo("turbina_alta"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60}, "custo da árvore")
	verificar(not p.peca_liberada("turbina_alta"), "começa travado")
	# o defletor saiu do "Em desenvolvimento" e fica só preso aos pré-requisitos dele
	verificar(not p.em_desenvolvimento("controle_vento"), "Defletor de vento fora do em desenvolvimento")
	verificar(not p.peca_em_desenvolvimento("defletor_vento"), "peça do defletor idem")
	p.concluidas = {"renovavel": true}
	verificar(not p.disponivel("turbina_alta"), "pede a liga leve")
	p.concluidas["liga_leve"] = true
	verificar(p.disponivel("turbina_alta"), "com renovável e liga leve: pesquisável")
	p.concluidas["turbina_alta"] = true
	verificar(p.peca_liberada("turbina_alta"), "libera a turbina alta")
	verificar(not p.disponivel("controle_vento"), "defletor ainda pede a semeadura de nuvens")
	p.concluidas["semeadura_nuvens"] = true
	verificar(p.disponivel("controle_vento"), "com semeadura e turbina alta: defletor pesquisável")
	p.concluidas["controle_vento"] = true
	verificar(p.peca_liberada("defletor_vento"), "libera o defletor")
