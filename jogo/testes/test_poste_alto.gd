extends Caso
## Poste alto (poste_alto, lote 13 — energia I): modelo do estudo (estudo_poste_alto.py, do Antigravity;
## arte/estudos/conv_lote13.py) com o anel de ressonância girando no topo; pesquisa Transmissão longa (aço +
## automação; básico/automação × 30, 6 s). Fio de 30 m até outro poste alto (com poste comum vale o menor, 9 m) e
## ligação de 3 m até a borda de máquina/gerador. É ele que tira o posto avançado (e a proliferação atrás dele) do
## "em desenvolvimento".


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-30, 80):
		for y in range(-12, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	c.cobrar = false
	return c


func _por(c: Construtor, nome: String, t: Vector2i) -> int:
	var antes := c.mapa._prox_id
	c.executar(c.plano_peca(nome, t, 0))
	verificar(c.mapa.estruturas.has(antes), "coube %s em %s" % [nome, t])
	return antes


func _ligados(c: Construtor, a: int, b: int) -> bool:
	return c.mapa.estruturas[a].get("fios", []).has(b) and c.mapa.estruturas[b].get("fios", []).has(a)


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("poste_alto", {})
	igual(Fiacao.papel("poste_alto"), "poste", "papel de poste")
	verificar(not Fiacao.eh_sem_fio("poste_alto"), "leva por cabo (não é sem fio)")
	perto(float(r.raio_fio), 30.0, 1e-6, "fio de 30 m (árvore)")
	perto(float(r.raio_ligacao), 3.0, 1e-6, "ligação de 3 m (árvore)")
	var md: Dictionary = Registro.modelos.get("poste_alto", {})
	igual(Registro.area("poste_alto"), Vector2i(1, 1), "1×1")
	igual(md.get("estudo", ""), "estudo_poste_alto.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (anel de ressonância do estudo)")
	verificar(int(md.tris) <= 4500, "leve (%d triângulos)" % md.tris)
	verificar(float(md.dims[2]) > 5.0, "alto: %.2f m (o poste comum tem 2,3 m)" % float(md.dims[2]))
	verificar(md.get("portas", []).is_empty(), "sem bocas (só energia)")
	igual(md.get("terminais", []).size(), 4, "fio preso no pé das 4 cadeias de isoladores")
	for t in md.get("terminais", []):
		verificar(float(t[2]) > 3.0 and float(t[2]) < float(md.dims[2]), "terminal no alto da torre (%s)" % str(t))
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/poste_alto.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "poste_alto" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("poste_alto", {}).is_empty(), "custo de construção")


func test_modelo_gira_o_anel() -> void:
	var cena: PackedScene = load(str(Registro.modelos.poste_alto.modelo))
	var raiz := cena.instantiate()
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo")
	if ap != null and ap.has_animation("trabalho"):
		var an := ap.get_animation("trabalho")
		perto(an.length, 4.0, 0.1, "laço de 4 s")
		var alvos := []
		for i in an.get_track_count():
			alvos.append(String(an.track_get_path(i)))
		verificar(alvos.any(func(s): return s.contains("anel")), "a trilha mexe o anel (%s)" % str(alvos))
	raiz.free()


func test_fio_de_30_m() -> void:
	var c := _c()
	var g := _por(c, "gerador", Vector2i(-20, 0))               # 2×2 em (-20..-19, 0..1)
	var a1 := _por(c, "poste_alto", Vector2i(-17, 0))           # 2 m da borda do gerador
	verificar(_ligados(c, g, a1), "liga no gerador a 2 m")
	var a2 := _por(c, "poste_alto", Vector2i(11, 0))            # 28 m
	verificar(_ligados(c, a1, a2), "dois postes altos se ligam a 28 m, por cabo")
	verificar(not Fiacao.liga_sem_cabo(c.mapa.estruturas[a1], c.mapa.estruturas[a2]), "é cabo de verdade (desenhado)")
	var a3 := _por(c, "poste_alto", Vector2i(43, 0))            # 32 m: longe demais
	igual(c.mapa.estruturas[a3].fios.size(), 0, "a 32 m fica solto")
	var comum := _por(c, "poste_energia", Vector2i(23, 0))      # 12 m do a2: o comum só alcança 9
	verificar(not _ligados(c, a2, comum), "com poste comum vale o fio menor (9 m)")
	var comum2 := _por(c, "poste_energia", Vector2i(19, 0))     # 8 m do a2
	verificar(_ligados(c, a2, comum2), "poste comum a 8 m liga no alto")
	var longe := _por(c, "montadora", Vector2i(11, 5))          # borda a 4 m do a2
	verificar(not _ligados(c, a2, longe), "máquina a 4 m não pega no alto (ligação de 3 m)")
	var maq := _por(c, "montadora", Vector2i(11, -4))           # 3×3 em (11..13, -4..-2): borda a 1,5 m
	verificar(_ligados(c, a2, maq), "máquina a 1,5 m pega no alto")
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	verificar(f.rede.tem_fonte(maq), "a montadora está na rede do gerador, 30 m adiante")
	verificar(not f.rede.tem_fonte(a3), "o poste solto não")
	f.combustivel[g] = 20.0
	f.tick(1.0 / 30.0)
	verificar(not f.transmitindo(a3), "sem rede, o anel do solto fica parado")
	perto(f.rede.satisfacao(maq), 1.0, 1e-3, "energia chegou pela linha alta")
	verificar(f.transmitindo(a1) and f.transmitindo(a2), "passando energia: o anel dos postes da linha gira")


func test_terminal_virado_para_o_fio() -> void:
	var c := _c()
	var a1 := _por(c, "poste_alto", Vector2i(0, 0))
	var a2 := _por(c, "poste_alto", Vector2i(25, 0))
	var e: Dictionary = c.mapa.estruturas[a1]
	var p := Fiacao.ponto_fio(e, Fiacao.centro(c.mapa.estruturas[a2]))
	var cx := Grade.ponto_mundo(Fiacao.centro(e), 0.0)
	verificar(p.x > cx.x + 0.3, "o fio sai da ponta da cruzeta virada para o outro poste")
	verificar(p.y > 3.0, "e lá no alto (%.2f m)" % p.y)


func test_arrastar_poe_um_a_cada_20() -> void:
	var c := _c()
	var q := c.plano_linha("poste_alto", Vector2i(0, 0), Vector2i(45, 0), 0)
	igual(q.size(), 4, "um a cada 20 tiles + o último")
	igual(q[1].minimo, Vector2i(20, 0))
	var d := c.plano_linha("poste_energia", Vector2i(-6, 0), Vector2i(6, 0), 0)
	igual(d.size(), 3, "o comum segue a cada 6")


func test_pesquisa_transmissao() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("transmissao"), "Transmissão longa ligada no jogo")
	verificar(not p.em_desenvolvimento("transmissao"), "não está mais em desenvolvimento")
	igual(p.custo("transmissao"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "custo da árvore")
	verificar(not p.peca_liberada("poste_alto"), "começa travado")
	verificar(not p.disponivel("transmissao"), "pede aço e automação")
	p.concluidas = {"aco": true, "automacao": true}
	verificar(p.disponivel("transmissao"), "com aço e automação: pesquisável")
	p.concluidas["transmissao"] = true
	verificar(p.peca_liberada("poste_alto"), "libera o poste alto")
	verificar(not p.peca_em_desenvolvimento("poste_alto"), "o poste alto não fica em cinza")
	# o posto avançado (e a proliferação atrás dele) sai do "em desenvolvimento"
	verificar(not Pesquisa.new().em_desenvolvimento("posto_avancado"), "posto avançado: pesquisável pela árvore")
