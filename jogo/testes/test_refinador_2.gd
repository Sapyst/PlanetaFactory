extends Caso
## Refinador 2 (refinador_2, lote 10 — produção I): modelo do estudo (estudo_refinador_2.py, do Antigravity;
## arte/estudos/conv_lote10.py) com agitadores, anel quântico, robô de inspeção e visor de nível; pesquisa refinador_2
## (química + ciência de tempestade; 5 pacotes × 120, 12 s). Melhoria real do refinador: as mesmas receitas,
## velocidade 2,0, suja o mesmo por minuto (metade por produto: "50% menos água suja"), 3 encaixes de módulo e uma 2ª
## entrada de fluido ao sul. Com ele, a Estação de tratamento sai do "em desenvolvimento".


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-10, 14):
		for y in range(-10, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


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
	var r: Dictionary = Registro.estruturas.get("refinador_2", {})
	igual(r.get("maquina", ""), "refinador", "faz as receitas do refinador")
	perto(float(r.velocidade), 2.0, 1e-6, "velocidade 2,0 (árvore)")
	igual(int(r.encaixes_modulo), 3, "3 encaixes de módulo (árvore)")
	var r1: Dictionary = Registro.estruturas.refinador
	perto(float(r.poluicao) / float(r.velocidade), 0.5 * float(r1.poluicao) / float(r1.velocidade), 1e-6, "suja a metade por produto")
	var md: Dictionary = Registro.modelos.get("refinador_2", {})
	igual(Registro.area("refinador_2"), Vector2i(3, 3), "3×3 (como o refinador)")
	igual(md.get("estudo", ""), "estudo_refinador_2.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	verificar(float(md.dims[0]) <= 3.1 and float(md.dims[1]) <= 3.1, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 12000, "no nível do refinador (%d triângulos; o estudo tem 28.672)" % md.tris)
	var bocas := {}
	for p in md.get("portas", []):
		bocas[p.nome] = p
	for n in ["PORTA_FLUIDO_ENT_O1", "PORTA_FLUIDO_SAI_L1", "PORTA_ITEM_SAI_N0", "PORTA_FLUIDO_ENT_S1"]:
		verificar(bocas.has(n), "boca %s (do estudo)" % n)
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/refinador_2.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Produção" and "refinador_2" in cat.pecas), "no menu (Produção)")
	verificar(not Registro.progressao.custos.get("refinador_2", {}).is_empty(), "custo de construção")


## Resina (30 seiva + 10 água → 1, 3 s) com seiva pelo oeste e água pela 2ª entrada (sul): em 6 s o refinador 2 faz 2.
func test_resina_duas_vezes_mais_rapido() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("refinador_2", Vector2i(0, 0), 0)
	var oeste := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_O1", 2)
	var sul := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_S1", 2)
	f.reconstruir()
	var r_seiva := f.rede_de(c.mapa.tiles[oeste])
	var r_agua := f.rede_de(c.mapa.tiles[sul])
	verificar(r_seiva != r_agua, "duas redes de entrada")
	r_seiva.fluido = "seiva"
	r_seiva.qtd = 400.0
	r_agua.fluido = "agua"
	r_agua.qtd = 400.0
	f.escolher_receita(id, "resina")
	var m: Maquina = f.maquinas[id]
	perto(m.velocidade, 2.0, 1e-6, "velocidade 2,0 na máquina")
	var n := 0
	for i in 12:
		m.energia = 1.0
		f._tick_fluidos(0.5)
		m.tick(0.5)
		n += int(m.saidas.get("resina", 0))
		m.saidas.erase("resina")
		m.acordar()
	verificar(n >= 3, "em 6 s fez %d resinas (o refinador 1 faz 2)" % n)


func test_pesquisa_e_tratamento() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("refinador_2"), "Refinador 2 ligada no jogo")
	verificar(not p.em_desenvolvimento("refinador_2"), "fora do em desenvolvimento")
	igual(p.custo("refinador_2"), {"pacote_pesquisa": 120, "pacote_automacao": 120, "pacote_quimico": 120, "pacote_ecologico": 120,
			"pacote_tempestade": 120}, "custo da árvore")
	verificar(not p.peca_liberada("refinador_2"), "começa travado")
	p.concluidas = {"quimica": true}
	verificar(not p.disponivel("refinador_2"), "pede a ciência de tempestade")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("refinador_2"), "com química e tempestade: pesquisável")
	p.concluidas["refinador_2"] = true
	verificar(p.peca_liberada("refinador_2"), "libera o refinador 2")
	verificar(not Pesquisa.new().em_desenvolvimento("estacao_tratamento"), "a estação de tratamento sai do em desenvolvimento")
	verificar(not Pesquisa.new().peca_em_desenvolvimento("estacao_tratamento"), "e a peça não fica mais em cinza")
