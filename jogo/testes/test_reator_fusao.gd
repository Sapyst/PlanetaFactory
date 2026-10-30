extends Caso
## Reator de fusão (reator_fusao, lote 14 — energia II): modelo do estudo (estudo_reator_fusao.py, do Antigravity;
## arte/estudos/conv_lote14.py) com plasma, anel e fluxômetros; pesquisa fusao (reator de cristal + computação quântica;
## 6 pacotes × 300, 15 s). 30 MW: cristal carregado (1.800 MJ) por braço na boca sul e água pelo cano da boca oeste
## (15/s a plena carga). Pesquisável depois da computação quântica (lote 11); na Demonstração já se constrói.


func _c() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-12, 60):
		for y in range(-12, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	var r := m.colocar("reator_fusao", Vector2i(0, 0), 0)
	var c := Construtor.new(m)
	c.cobrar = false
	return {"m": m, "r": r, "c": c}


func _cano(c: Dictionary, comp := 3) -> Vector2i:
	var e: Dictionary = c.m.estruturas[c.r]
	for pt in Registro.modelos.reator_fusao.portas:
		if pt.tipo == "FLUIDO":
			var p := Grade.porta_no_mundo(pt, e.minimo, e.area, e.rot)
			var d := Grade.DIRECOES.find(p.dir)
			c.c.executar(c.c.plano_linha("cano", p.tile_fora, p.tile_fora + p.dir * (comp - 1), Construtor.rot_do_fluxo(d)))
			return p.tile_fora
	return Vector2i(9999, 0)


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("reator_fusao", {})
	igual(Fiacao.papel("reator_fusao"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -30000.0, 1e-6, "30 MW (árvore)")
	verificar(Fabrica.eh_reator("reator_fusao"), "queima item")
	igual(r.combustivel_item.keys(), ["cristal_carregado"], "só cristal carregado (árvore)")
	verificar(float(r.agua_por_mj) > 0.0, "bebe água (árvore)")
	var md: Dictionary = Registro.modelos.get("reator_fusao", {})
	igual(Registro.area("reator_fusao"), Vector2i(3, 3), "3×3 (árvore)")
	igual(md.get("estudo", ""), "estudo_reator_fusao.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (plasma, anel, fluxômetros do estudo)")
	verificar(float(md.dims[0]) <= 3.05 and float(md.dims[1]) <= 3.05, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 7500, "leve (%d triângulos)" % md.tris)
	var ps: Array = md.get("portas", []).map(func(p): return p.nome)
	igual(ps, ["PORTA_ITEM_ENT_S1", "PORTA_FLUIDO_ENT_O1"], "item ao sul, água a oeste")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/reator_fusao.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "reator_fusao" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("reator_fusao", {}).is_empty(), "custo de construção")


func test_so_aceita_cristal_carregado() -> void:
	var c := _c()
	var f := Fabrica.new(c.m)
	f.reconstruir()
	var d: Object = f.destino_em(Vector2i(0, 0))
	verificar(not d.aceita("celula_energia"), "célula de energia não")
	verificar(d.receber("cristal_carregado"), "cristal carregado sim")
	perto(float(f.combustivel[c.r]), 1800.0, 1e-6, "1.800 MJ")
	d.receber("cristal_carregado")
	verificar(not d.aceita("cristal_carregado"), "cheio em 3.600 MJ")


func test_precisa_de_agua_e_cristal() -> void:
	var c := _c()
	var boca := _cano(c)
	var m: MapaOcupacao = c.m
	var po := m.colocar("poste_energia", Vector2i(3, 3), 0)
	Fiacao.ligar_novo(m, po)
	var k := m.colocar("refinador", Vector2i(6, 3), 0)
	Fiacao.ligar_novo(m, k)
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(f.gerador_no_cano(c.r), "achou o cano da boca oeste")
	f.combustivel[c.r] = 1800.0
	f.tick(1.0)
	perto(-f.kw_de(c.r), 0.0, 1e-6, "sem água não gera")
	verificar(f.rede.satisfacao(k) < 0.01, "sem água a máquina fica parada")
	perto(float(f.combustivel[c.r]), 1800.0, 1e-6, "e não queima o cristal")
	var rede := f.rede_de(m.tiles[boca])
	rede.fluido = "seiva"
	rede.qtd = 50.0
	f.tick(1.0)
	perto(float(f.agua_reator[c.r]), 0.0, 1e-6, "seiva não serve")
	perto(float(rede.qtd), 50.0, 1e-6, "e fica no cano")
	rede.fluido = "agua_limpa"
	rede.qtd = 1000.0
	f.tick(1.0)
	perto(float(f.agua_reator[c.r]), 300.0, 1e-6, "água limpa serve e enche o tanque (300)")
	perto(float(rede.qtd), 700.0, 1e-6, "saiu do cano")
	f.tick(1.0)
	perto(-f.kw_de(c.r), 30000.0, 1e-3, "com água: 30 MW")
	verificar(f.rede.satisfacao(k) > 0.99, "a máquina tem energia")
	verificar(f.transmitindo(c.r), "transmitindo")
	var mj := 1800.0 - float(f.combustivel[c.r])
	verificar(mj > 0.2 and mj < 1.0, "gasta conforme a carga: %.2f MJ em ~1 s, não 30" % mj)
	# sem água de novo: para
	rede.qtd = 0.0
	rede.fluido = ""
	f.agua_reator[c.r] = 0.2
	for i in 90:
		f.tick(1.0 / 30.0)
	perto(float(f.agua_reator[c.r]), 0.0, 1e-3, "bebeu o tanque (0,5 por MJ)")
	perto(-f.kw_de(c.r), 0.0, 1e-6, "acabou a água: para")
	verificar(f.rede.satisfacao(k) < 0.01, "a máquina para junto")


func test_consumo_a_plena_carga() -> void:
	var c := _c()
	var m: MapaOcupacao = c.m
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[c.r] = 3000.0
	f.agua_reator[c.r] = 300.0
	var kw := -f.kw_de(c.r)
	perto(kw, 30000.0, 1e-3, "plena")
	perto(kw / 1000.0 * float(Registro.estruturas.reator_fusao.agua_por_mj), 15.0, 1e-6, "15 de água/s a plena carga: uma bomba (40/s) dá para 2")


func test_salva_a_agua() -> void:
	var c := _c()
	var f := Fabrica.new(c.m)
	f.reconstruir()
	f.agua_reator[c.r] = 123.0
	f.combustivel[c.r] = 900.0
	var d: Dictionary = f.estado()
	var f2 := Fabrica.new(c.m)
	f2.reconstruir()
	f2.restaurar(d)
	perto(float(f2.agua_reator[c.r]), 123.0, 1e-6, "água volta no salvamento")
	perto(float(f2.combustivel[c.r]), 900.0, 1e-6, "cristal também")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("fusao"), "Reator de fusão ligada no progressao.json")
	igual(p.custo("fusao"), {"pacote_pesquisa": 300, "pacote_automacao": 300, "pacote_quimico": 300, "pacote_ecologico": 300, "pacote_tempestade": 300, "pacote_quantico": 300}, "custo da árvore")
	verificar(not p.em_desenvolvimento("fusao"), "fora do em desenvolvimento")
	verificar(not p.peca_em_desenvolvimento("reator_fusao"), "a peça não fica em cinza")
	verificar(not p.disponivel("fusao"), "não se pesquisa")
	var q := Pesquisa.new()
	q.concluidas = {"fusao": true}
	verificar(q.peca_liberada("reator_fusao"), "pesquisada, libera a peça")
	verificar(Pesquisa.new(true).peca_liberada("reator_fusao"), "na Demonstração já se constrói")
