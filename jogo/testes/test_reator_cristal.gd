extends Caso
## Reator de cristal (reator_cristal, lote 14 — energia II): modelo do estudo (estudo_reator_cristal.py, do Antigravity;
## arte/estudos/conv_lote14.py) com anel, barras de controle, núcleo e injetor; pesquisa reator_cristal (energia avançada
## + ciência de tempestade; básico/automação/químico/ecológico/tempestade × 150, 12 s). 8 MW queimando célula de energia
## (240 MJ) ou cristal carregado (480 MJ), que um braço põe pela boca sul; o combustível só anda com carga na rede.


func _c() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-12, 60):
		for y in range(-12, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	var r := m.colocar("reator_cristal", Vector2i(0, 0), 0)
	var c := Construtor.new(m)
	c.cobrar = false
	return {"m": m, "r": r, "c": c}


func _carga(m: MapaOcupacao, n: int) -> Array[int]:
	var po := m.colocar("poste_energia", Vector2i(4, 0), 0)
	Fiacao.ligar_novo(m, po)
	var q: Array[int] = []
	for i in n:
		var pq := m.colocar("poste_energia", Vector2i(4 + i * 4, 3), 0)
		Fiacao.ligar_novo(m, pq)
		var k := m.colocar("refinador", Vector2i(4 + i * 4, 5), 0)
		Fiacao.ligar_novo(m, k)
		q.append(k)
	return q


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("reator_cristal", {})
	igual(Fiacao.papel("reator_cristal"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -8000.0, 1e-6, "8 MW (árvore)")
	verificar(Fabrica.eh_reator("reator_cristal"), "reator queima item")
	verificar(r.combustivel_item.has("celula_energia") and r.combustivel_item.has("cristal_carregado"), "célula de energia ou cristal carregado (árvore)")
	verificar(not Registro.itens.celula_energia.has("combustivel_mj") and not Registro.itens.cristal_carregado.has("combustivel_mj"), "gerador e fornalha não queimam isso")
	var md: Dictionary = Registro.modelos.get("reator_cristal", {})
	igual(Registro.area("reator_cristal"), Vector2i(3, 3), "3×3 (árvore)")
	igual(md.get("estudo", ""), "estudo_reator_cristal.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (anel, barras, núcleo do estudo)")
	verificar(float(md.dims[0]) <= 3.05 and float(md.dims[1]) <= 3.05, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 7000, "leve (%d triângulos)" % md.tris)
	var ps: Array = md.get("portas", [])
	igual(ps.size(), 1, "uma boca")
	igual([ps[0].tipo, ps[0].io, ps[0].nome], ["ITEM", "ENT", "PORTA_ITEM_ENT_S1"], "entrada de item ao sul (S1)")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/reator_cristal.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "reator_cristal" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("reator_cristal", {}).is_empty(), "custo de construção")


func test_so_aceita_o_combustivel_dele() -> void:
	var c := _c()
	var f := Fabrica.new(c.m)
	f.reconstruir()
	var d: Object = f.destino_em(Vector2i(0, 0))
	verificar(d != null, "o reator recebe de braço")
	verificar(not d.aceita("carvao"), "carvão não")
	verificar(not d.aceita("cristal_lapidado"), "cristal sem carga não")
	verificar(d.receber("celula_energia"), "célula sim")
	perto(float(f.combustivel[c.r]), 240.0, 1e-6, "célula = 240 MJ")
	verificar(d.receber("cristal_carregado"), "cristal carregado sim")
	perto(float(f.combustivel[c.r]), 720.0, 1e-6, "cristal carregado = 480 MJ")
	verificar(d.receber("celula_energia"), "ainda cabe")
	verificar(not d.aceita("celula_energia"), "cheio em 960 MJ: recusa")
	igual(Fabrica.valor_combustivel("celula_energia"), 0.0, "a célula não vale na fornalha")


func test_braco_tira_da_esteira_na_boca_sul() -> void:
	var c := _c()
	var cons: Construtor = c.c
	var m: MapaOcupacao = c.m
	var e: Dictionary = m.estruturas[c.r]
	var porta := Grade.porta_no_mundo(Registro.modelos.reator_cristal.portas[0], e.minimo, e.area, e.rot)
	var fim: Vector2i = porta.tile_fora + porta.dir
	var ini: Vector2i = fim + porta.dir * 2
	cons.executar(cons.plano_linha("esteira", ini, fim, Construtor.rot_do_fluxo(Grade.DIRECOES.find(-porta.dir))))
	var br := m.colocar("braco", porta.tile_fora, 0)        # rotação 0: a frente do braço é o norte (o reator)
	var po := m.colocar("poste_energia", porta.tile_fora + Vector2i(2, 0), 0)
	Fiacao.ligar_novo(m, po)
	Fiacao.ligar_novo(m, br)
	verificar(Portas.ligada(m, e, Registro.modelos.reator_cristal.portas[0]), "a boca sul conta como ligada")
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[c.r] = 10.0                               # reserva: o próprio reator move o braço
	var dest: Object = f.destino_em(ini)
	verificar(dest != null and dest.aceita("celula_energia"), "esteira aceita a célula")
	dest.receber("celula_energia")
	for i in 450:
		f.tick(1.0 / 30.0)
	verificar(float(f.combustivel.get(c.r, 0.0)) > 200.0, "a célula chegou ao reator pelo braço (%.1f MJ)" % float(f.combustivel.get(c.r, 0.0)))


func test_gera_8_mw_e_gasta_conforme_a_carga() -> void:
	var c := _c()
	var q := _carga(c.m, 3)                         # 3 refinadores = 1,26 MW
	var f := Fabrica.new(c.m)
	f.reconstruir()
	perto(-f.kw_de(c.r), 8000.0, 1e-3, "até 8 MW")
	f.tick(1.0)
	verificar(f.rede.satisfacao(q[0]) < 0.01, "sem combustível não gera")
	f.combustivel[c.r] = 100.0
	f.tick(1.0)
	verificar(f.rede.satisfacao(q[0]) > 0.99, "com combustível as máquinas têm energia")
	verificar(f.transmitindo(c.r), "transmitindo")
	var gasto := 100.0 - float(f.combustivel[c.r])
	perto(gasto, 1.26, 0.02, "gasta só o que a rede pede (%.2f MJ em 1 s, não 8)" % gasto)


func test_salva_combustivel() -> void:
	var c := _c()
	var f := Fabrica.new(c.m)
	f.reconstruir()
	f.combustivel[c.r] = 333.0
	var dados: Dictionary = f.estado()
	var f2 := Fabrica.new(c.m)
	f2.reconstruir()
	f2.restaurar(dados)
	perto(float(f2.combustivel[c.r]), 333.0, 1e-6, "o combustível volta no salvamento")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("reator_cristal"), "Reator de cristal ligada no jogo")
	verificar(not p.em_desenvolvimento("reator_cristal"), "fora do em desenvolvimento")
	var pacotes := {"pacote_pesquisa": 150, "pacote_automacao": 150, "pacote_quimico": 150, "pacote_ecologico": 150, "pacote_tempestade": 150}
	igual(p.custo("reator_cristal"), pacotes, "custo da árvore")
	verificar(not p.peca_liberada("reator_cristal"), "começa travado")
	p.concluidas = {"energia": true}
	verificar(not p.disponivel("reator_cristal"), "pede a ciência de tempestade")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("reator_cristal"), "com energia avançada e ciência de tempestade: pesquisável")
	p.concluidas["reator_cristal"] = true
	verificar(p.peca_liberada("reator_cristal"), "libera o reator de cristal")
