extends Caso
## Gerador a fluido (gerador_fluido, lote 13 — energia I): modelo do estudo (estudo_gerador_fluido.py, do Antigravity;
## arte/estudos/conv_lote13.py) com ventiladores, volante, visor de fluxo e anel quântico; pesquisa Combustível de
## seiva (química + briquete; básico/automação/químico × 40, 8 s) libera o fluido combustível de seiva (refinador:
## 40 seiva → 30, 4 s) e o gerador 3×3, que puxa o combustível pelo cano da boca sul (10 = 12 MJ) e dá até 2,4 MW.


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-10, 24):
		for y in range(-10, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	c.cobrar = false
	return c


func _cano_na_porta(c: Construtor, id: int, nome_porta: String, comp := 2) -> Vector2i:
	var e: Dictionary = c.mapa.estruturas[id]
	for pt in Registro.modelos[e.nome].portas:
		if pt.nome == nome_porta:
			var p := Grade.porta_no_mundo(pt, e.minimo, e.area, e.rot)
			var d := Grade.DIRECOES.find(p.dir)
			c.executar(c.plano_linha("cano", p.tile_fora, p.tile_fora + p.dir * (comp - 1), Construtor.rot_do_fluxo(d)))
			return p.tile_fora
	return Vector2i(9999, 0)


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("gerador_fluido", {})
	igual(Fiacao.papel("gerador_fluido"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -2400.0, 1e-6, "2,4 MW (árvore)")
	verificar(Fabrica.eh_gerador_fluido("gerador_fluido"), "queima fluido")
	perto(float(r.combustivel_fluido.combustivel_seiva) * 10.0, 12.0, 1e-6, "10 de combustível = 12 MJ (árvore)")
	verificar(Registro.fluidos.has("combustivel_seiva"), "fluido novo")
	igual(Registro.nome_fluido("combustivel_seiva"), "Combustível de seiva", "nome com acento")
	var md: Dictionary = Registro.modelos.get("gerador_fluido", {})
	igual(Registro.area("gerador_fluido"), Vector2i(3, 3), "3×3")
	igual(md.get("estudo", ""), "estudo_gerador_fluido.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (ventiladores, volante e anel do estudo)")
	verificar(float(md.dims[0]) <= 3.05 and float(md.dims[1]) <= 3.05, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 9000, "leve (%d triângulos)" % md.tris)
	var ps: Array = md.get("portas", [])
	igual(ps.size(), 1, "uma boca")
	if ps.size() == 1:
		igual([ps[0].tipo, ps[0].io, ps[0].nome], ["FLUIDO", "ENT", "PORTA_FLUIDO_ENT_S1"], "entrada de fluido ao sul (S1)")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/gerador_fluido.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "gerador_fluido" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("gerador_fluido", {}).is_empty(), "custo de construção")
	var rc: Dictionary = Registro.receitas.get("combustivel_seiva", {})
	igual(rc.get("maquina", ""), "refinador", "combustível sai do refinador")
	perto(float(rc.entradas_fluido.seiva), 40.0, 1e-6, "40 de seiva")
	perto(float(rc.saidas_fluido.combustivel_seiva), 30.0, 1e-6, "→ 30 de combustível")
	perto(float(rc.tempo), 4.0, 1e-6, "4 s")


func test_refinador_faz_combustivel() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("refinador", Vector2i(0, 0), 0)
	var oeste := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_O1", 2)
	var leste := _cano_na_porta(c, id, "PORTA_FLUIDO_SAI_L1", 3)
	f.reconstruir()
	var r_seiva := f.rede_de(c.mapa.tiles[oeste])
	var r_sai := f.rede_de(c.mapa.tiles[leste])
	r_seiva.fluido = "seiva"
	r_seiva.qtd = 200.0
	f.escolher_receita(id, "combustivel_seiva")
	var m: Maquina = f.maquinas[id]
	for i in 20:
		m.energia = 1.0
		f._tick_fluidos(0.5)
		m.tick(0.5)
	f._tick_fluidos(0.5)
	igual(r_sai.fluido, "combustivel_seiva", "o cano da boca leste leva combustível")
	verificar(float(r_sai.qtd) >= 30.0, "saiu combustível (%.0f)" % float(r_sai.qtd))
	verificar(float(r_seiva.qtd) < 200.0, "bebeu a seiva")


func test_gerador_queima_do_cano() -> void:
	var c := _c()
	var g := c.mapa.colocar("gerador_fluido", Vector2i(0, 0), 0)
	var boca := _cano_na_porta(c, g, "PORTA_FLUIDO_ENT_S1", 2)
	verificar(boca != Vector2i(9999, 0), "cano na boca sul")
	var po := c.mapa.colocar("poste_energia", Vector2i(5, 1), 0)
	Fiacao.ligar_novo(c.mapa, po)
	var maqs: Array[int] = []
	for y in [-4, 0, 4]:
		var mq := c.mapa.colocar("montadora", Vector2i(7, y), 0)
		Fiacao.ligar_novo(c.mapa, mq)
		maqs.append(mq)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	verificar(f.gerador_no_cano(g), "o gerador achou o cano")
	perto(-f.kw_de(g), 2400.0, 1e-3, "até 2,4 MW")
	var rede := f.rede_de(c.mapa.tiles[boca])
	rede.fluido = "seiva"
	rede.qtd = 100.0
	f.tick(1.0 / 30.0)
	perto(float(f.combustivel[g]), 0.0, 1e-6, "seiva não queima")
	perto(float(rede.qtd), 100.0, 1e-6, "e fica no cano")
	rede.fluido = "combustivel_seiva"
	f.tick(1.0 / 30.0)
	verificar(float(f.combustivel[g]) > 39.0, "encheu o estoque (%.1f MJ, até 40)" % float(f.combustivel[g]))
	verificar(float(rede.qtd) < 70.0 and float(rede.qtd) > 66.0, "40 MJ = 33,3 de combustível do cano (sobrou %.1f)" % float(rede.qtd))
	for i in 30:
		f.tick(1.0 / 30.0)
	verificar(f.rede.satisfacao(maqs[0]) > 0.99, "as montadoras têm energia")
	verificar(f.transmitindo(g), "queimando para a rede")
	verificar(float(rede.qtd) < 66.6, "segue puxando do cano enquanto queima (%.1f)" % float(rede.qtd))


func test_sem_cano_fica_parado() -> void:
	var c := _c()
	var g := c.mapa.colocar("gerador_fluido", Vector2i(0, 0), 0)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	verificar(not f.gerador_no_cano(g), "sem cano na boca")
	f.tick(1.0 / 30.0)
	perto(float(f.combustivel.get(g, -1.0)), 0.0, 1e-6, "estoque vazio (não pega item por braço)")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("combustivel_seiva"), "Combustível de seiva ligada no jogo")
	verificar(not p.em_desenvolvimento("combustivel_seiva"), "fora do em desenvolvimento")
	igual(p.custo("combustivel_seiva"), {"pacote_pesquisa": 40, "pacote_automacao": 40, "pacote_quimico": 40}, "custo da árvore")
	verificar(not p.peca_liberada("gerador_fluido") and not p.receita_liberada("combustivel_seiva"), "começa travado")
	p.concluidas = {"quimica": true, "briquete": true}
	verificar(p.disponivel("combustivel_seiva"), "com química e briquete: pesquisável")
	p.concluidas["combustivel_seiva"] = true
	verificar(p.peca_liberada("gerador_fluido") and p.receita_liberada("combustivel_seiva"), "libera o gerador e a receita")
