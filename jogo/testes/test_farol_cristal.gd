extends Caso
## Farol de cristal (farol_cristal, lote 17): modelo do estudo (estudo_farol_cristal.py, do Antigravity;
## arte/estudos/conv_lote17.py) com o carrossel óptico girando; pesquisa pela árvore (eletrônica; básico × 10, 4 s).
## Com energia (30 kW), à noite acende uma luz de 10 m: o que está nela sai da névoa e as aranhas que entram dão aviso.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(196, 204):
		for y in range(-4, 4):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


## Mapa + descoberta + colônia + farol em (200, 0) + lógica com energia e luz do dia controladas.
func _cena(energia := [1.0], dia := [0.0]) -> Dictionary:
	var m := _mapa()
	var d := Descoberta.new()
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var id := m.colocar("farol_cristal", Vector2i(200, 0), 0)
	verificar(id >= 0, "farol coube (%s)" % m.motivo_bloqueio("farol_cristal", Vector2i(200, 0), 0))
	var f := Farol.new(m, d)
	f.colonia = c
	f.energia = func(_id: int) -> float: return energia[0]
	f.luz_dia = func() -> float: return dia[0]
	return {"m": m, "d": d, "c": c, "id": id, "f": f}


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("farol_cristal", {})
	verificar(Farol.eh_farol("farol_cristal"), "regra do farol")
	perto(float(r.farol.raio), 10.0, 1e-6, "luz de 10 m (árvore)")
	igual(Fiacao.papel("farol_cristal"), "consumo", "precisa de energia")
	verificar(float(r.energia_kw) > 0.0, "gasta energia")
	var md: Dictionary = Registro.modelos.get("farol_cristal", {})
	igual(Registro.area("farol_cristal"), Vector2i(1, 1), "1×1")
	igual(md.get("estudo", ""), "estudo_farol_cristal.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (carrossel do estudo)")
	verificar(float(md.dims[0]) <= 1.1 and float(md.dims[1]) <= 1.1, "quase só o tile (%s: os estais saem 3 cm)" % str(md.dims))
	verificar(int(md.tris) <= 5500, "leve (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas (só energia)")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/farol_cristal.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "farol_cristal" in cat.pecas), "no menu (Proliferação)")
	verificar(not Registro.progressao.custos.get("farol_cristal", {}).is_empty(), "custo de construção")


func test_modelo_gira_o_carrossel() -> void:
	var cena: PackedScene = load(str(Registro.modelos.farol_cristal.modelo))
	var raiz := cena.instantiate()
	var nomes := {}
	for n in raiz.find_children("*", "Node3D", true, false):
		nomes[String(n.name)] = n
	verificar(nomes.has("giro"), "carrossel óptico (giro) do estudo")
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo")
	if ap != null and ap.has_animation("trabalho"):
		perto(ap.get_animation("trabalho").length, 4.0, 0.1, "laço de 4 s")
	for n in nomes:                                         # o Animador não mexe por cima (só toca o laço)
		var i := String(n).rfind("_")
		var suf := String(n).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor"], "nome neutro: " + n)
	raiz.free()


func test_pesquisa_pela_arvore() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("farol_cristal"), "jogável")
	verificar(not p.em_desenvolvimento("farol_cristal"), "não está mais em desenvolvimento")
	verificar(p.arvore().farol_cristal.get("existente", false), "marcada como existente na árvore")
	igual(p.custo("farol_cristal"), {"pacote_pesquisa": 10}, "custo da árvore (básico × 10)")
	verificar(not p.disponivel("farol_cristal"), "travado no início")
	verificar(p.peca_em_desenvolvimento("farol_cristal") == false, "a peça sai de 'em desenvolvimento'")
	p.concluidas = {"logistica": true, "eletronica": true}
	verificar(p.disponivel("farol_cristal"), "depois da eletrônica")
	verificar(not p.peca_liberada("farol_cristal"), "peça travada antes da pesquisa")
	p.concluidas["farol_cristal"] = true
	verificar(p.peca_liberada("farol_cristal"), "libera o farol")


func test_acende_so_de_noite_com_energia() -> void:
	var energia := [1.0]
	var dia := [1.0]
	var c := _cena(energia, dia)
	var f: Farol = c.f
	var id: int = c.id
	verificar(not f.aceso(id), "de dia fica apagado")
	perto(f.forca(id), 0.0, 1e-6, "sem luz de dia")
	dia[0] = 0.5
	verificar(not f.aceso(id), "entardecer claro: ainda apagado")
	dia[0] = 0.2
	verificar(f.aceso(id), "escureceu: acende")
	dia[0] = 0.0
	verificar(f.aceso(id) and f.forca(id) > 0.95, "noite fechada: luz plena (%.2f)" % f.forca(id))
	energia[0] = 0.0
	verificar(not f.aceso(id), "sem energia não acende")
	energia[0] = 0.4
	verificar(f.aceso(id) and f.forca(id) < 0.95, "pouca energia: luz mais fraca (%.2f)" % f.forca(id))
	energia[0] = 1.0
	c.m.estruturas[id]["desligada"] = true
	verificar(not f.aceso(id), "desligado pelo painel: apagado")
	igual(f.acesos().size(), 0, "nenhum aceso")


func test_luz_tira_a_nevoa_num_raio_de_10_m() -> void:
	var dia := [1.0]
	var c := _cena([1.0], dia)
	var f: Farol = c.f
	var d: Descoberta = c.d
	f.tick(1.0)
	verificar(not d.descoberto(Vector2i(200, 0)), "de dia não descobre nada")
	dia[0] = 0.0
	f.tick(1.0)
	verificar(d.descoberto(Vector2i(200, 0)), "o tile do farol")
	verificar(d.descoberto(Vector2i(208, 0)), "8 m a leste")
	verificar(d.descoberto(Vector2i(200, -7)), "7 m ao sul")
	verificar(not d.descoberto(Vector2i(214, 0)), "14 m: fora da luz")
	verificar(f.iluminado(Vector2(205.0, 0.5)), "ponto a 5 m está iluminado")
	verificar(not f.iluminado(Vector2(215.0, 0.5)), "ponto a 15 m não")


func test_avisa_aranhas_que_entram_na_luz() -> void:
	var dia := [0.0]
	var c := _cena([1.0], dia)
	var f: Farol = c.f
	var col: Colonia = c.c
	for a in col.aranhas.keys():
		col.aranhas.erase(a)
	col.aranhas[9001] = {"id": 9001, "pos": Vector2(230.0, 0.5)}
	f.tick(1.0)
	igual(f.eventos.size(), 0, "aranha longe: nada")
	col.aranhas[9001].pos = Vector2(206.0, 0.5)
	f.tick(1.0)
	igual(f.eventos.size(), 1, "entrou na luz: aviso")
	if f.eventos.size() == 1:
		igual(f.eventos[0].tipo, "aranhas_no_farol", "tipo do aviso")
		igual(int(f.eventos[0].n), 1, "uma aranha")
		verificar((f.eventos[0].de as Vector2).x > 200.0, "vem do leste")
	f.eventos.clear()
	f.tick(1.0)
	igual(f.eventos.size(), 0, "a mesma aranha não avisa de novo")
	col.aranhas[9002] = {"id": 9002, "pos": Vector2(196.0, 0.5)}
	f.tick(1.0)
	igual(f.eventos.size(), 0, "aranha nova logo depois: espera os 30 s")
	col.aranhas.erase(9001)
	col.aranhas.erase(9002)
	for i in 30:
		f.tick(1.0)
	col.aranhas[9003] = {"id": 9003, "pos": Vector2(200.5, 8.0)}
	f.tick(1.0)
	igual(f.eventos.size(), 1, "passados 30 s: aranha nova avisa de novo")
	f.eventos.clear()
	dia[0] = 1.0
	f.tick(1.0)
	igual(f.aranhas_na_luz(c.id).size(), 0, "de dia o farol não vê ninguém")


func test_desenho_acende_a_luz() -> void:
	var c := _cena([1.0], [0.0])
	var dz := DesenhoFarol.new()
	dz.farol = c.f
	Engine.get_main_loop().root.add_child(dz)
	dz._process(0.1)
	igual(dz.acesas(), 1, "uma luz acesa")
	perto(dz._luzes[0].omni_range, 10.0, 1e-4, "luz de 10 m")
	dz.queue_free()
