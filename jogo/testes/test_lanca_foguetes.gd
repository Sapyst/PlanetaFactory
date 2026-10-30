extends Caso
## Lança-foguetes (torre_foguetes, fase 2.4): modelo do estudo (arte/estudos/conv_combate_meio.py), pesquisa pela
## árvore (ciência militar + química; básico/automação/militar/químico × 60) que libera a peça e a receita do foguete
## (1 resina + 1 aço + 1 circuito → 1). O foguete chega por esteira/braço (1 foguete = 1 disparo, guarda 18), voa e
## explode com dano em área; melhorias dano_foguete_1 / cadencia_foguete_1. Todo disparo ejeta o selo traseiro (cápsula
## maior) com fumaça e o foguete voa com rastro no desenho.


func _base() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	for x in range(-38, 40):
		for y in range(-10, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	return [m, c]


func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("torre_foguetes", {})
	igual(r.get("grupo", ""), "defesa", "grupo defesa")
	perto(float(r.get("alcance", 0)), 30.0, 1e-6, "alcance 30 m (árvore)")
	igual(r.get("municao_item", ""), "foguete", "munição: foguete")
	igual(Colonia.item_municao("torre_foguetes"), "foguete")
	igual(Colonia.tiros_por_item("torre_foguetes"), 1, "um foguete = um disparo")
	igual(Colonia.tiros_por_item("torre_metralhadora"), Fabrica.TIROS_POR_MUNICAO, "a bala segue com 10 tiros por munição")
	verificar(r.has("projetil") and float(r.projetil.raio) > 1.0, "dano em área")
	verificar(not r.has("energia_kw"), "sem energia: só foguete")
	var md: Dictionary = Registro.modelos.get("torre_foguetes", {})
	igual(Registro.area("torre_foguetes"), Vector2i(3, 3), "3×3")
	igual(md.get("estudo", ""), "estudo_lanca_foguetes.py", "convertido do estudo")
	verificar(int(md.get("tris", 0)) > 3000 and int(md.get("tris", 0)) <= 10000, "orçamento de triângulos (%d)" % md.get("tris", 0))
	var partes := {}
	for p in md.get("partes", []):
		partes[p.nome] = p.pai
	igual(partes.get("giro"), "base", "giro na base")
	igual(partes.get("canhao"), "giro", "casulo (canhão) no giro")
	verificar(md.has("boca") and md.has("ejecao") and md.has("vel_ejecao"), "boca dos tubos e saída do selo no modelo")
	verificar(float(md.boca[1]) > 0.3 and float(md.ejecao[1]) < -0.3, "boca na frente (+Y), selo sai por trás")
	verificar(float(md.get("capsula", {}).get("escala", 1.0)) > 1.5, "selo maior que a cápsula de bala")
	var portas: Array = md.get("portas", [])
	verificar(portas.size() == 1 and portas[0].nome == "PORTA_ITEM_ENT_S1", "foguetes entram pela boca sul (S1)")
	verificar(ResourceLoader.exists("res://assets/icones/torre_foguetes.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return "torre_foguetes" in cat.pecas), "no menu (Defesa)")
	verificar(not Registro.progressao.custos.get("torre_foguetes", {}).is_empty(), "custo de construção")
	var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
	for p in ["base", "giro", "canhao"]:
		verificar(cena.find_child("torre_foguetes_" + p, true, false) != null, "nó da parte " + p)
	cena.free()


func test_foguete_item_e_receita() -> void:
	verificar(Registro.itens.has("foguete"), "item foguete")
	verificar(ResourceLoader.exists("res://assets/icones/itens/foguete.png"), "ícone do foguete")
	verificar(Registro.modelos.has(Registro.itens.foguete.get("modelo_de", "")), "modelo (derivado) na esteira")
	var r: Dictionary = Registro.receitas.foguete
	igual(r.maquina, "montadora")
	igual(_int(r.entradas), {"resina": 1, "barra_aco": 1, "circuito": 1}, "1 resina + 1 aço + 1 circuito (árvore)")
	igual(_int(r.saidas), {"foguete": 1})


func test_pesquisa_pela_arvore() -> void:
	var p := Pesquisa.new()
	for id in ["torre_foguetes", "dano_foguete_1", "cadencia_foguete_1"]:
		verificar(p.jogavel(id), "jogável: " + id)
	p.concluidas = {"ciencia_militar": true}
	verificar(not p.disponivel("torre_foguetes"), "precisa da química também")
	p.concluidas["quimica"] = true
	verificar(p.disponivel("torre_foguetes"), "ciência militar + química")
	igual(p.custo("torre_foguetes"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_militar": 60, "pacote_quimico": 60}, "custo da árvore")
	verificar(not p.peca_liberada("torre_foguetes") and not p.receita_liberada("foguete"), "travado antes")
	p.concluidas["torre_foguetes"] = true
	verificar(p.peca_liberada("torre_foguetes") and p.receita_liberada("foguete"), "libera a peça e o foguete")
	verificar(p.disponivel("dano_foguete_1") and p.disponivel("cadencia_foguete_1"), "melhorias abertas")
	p.concluidas.merge({"dano_foguete_1": true, "cadencia_foguete_1": true})
	perto(p.bonus("dano_foguete"), 0.2, 1e-6, "+20% de dano")
	perto(p.bonus("cadencia_foguete"), 0.2, 1e-6, "+20% de disparos")


func _tick(c: Colonia, s: float, tipos: Array) -> Array:
	var out := []
	for i in int(s * 30):
		c.tick(1.0 / 30.0, [])
		for e in c.eventos:
			if e.tipo in tipos:
				out.append(e)
	return out


func test_dano_em_area() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var t := m.colocar("torre_foguetes", Vector2i(0, -1), 0)
	verificar(t >= 0, "coube")
	var ninho := c._criar_ninho(Vector2i(32, -2), 1.0)
	# grupo de 3 aranhas paradas juntas a ~20 m
	var ids: Array[int] = []
	for k in 3:
		var a := c._nova_aranha(ninho)
		c.aranhas[a].pos = Vector2(21.0 + k * 0.6, 0.5 + (k % 2) * 0.5)
		c.aranhas[a].vida = 1000.0
		c.aranhas[a].atordoada = 99.0            # paradas no lugar para medir o dano
		ids.append(a)
	igual(_tick(c, 1.0, ["tiro"]).size(), 0, "sem foguete, sem disparo")
	c.carregar_torre(t, 1)
	var ev := _tick(c, 0.2, ["tiro"])
	igual(ev.size(), 1, "um foguete, um disparo")
	verificar(ev[0].get("projetil", false) and ev[0].bala, "disparo de projétil (ejeta selo)")
	igual(c.projeteis.size(), 1, "foguete no ar")
	verificar(ids.all(func(a): return is_equal_approx(c.aranhas[a].vida, 1000.0)), "no ar ainda não feriu")
	var ex := _tick(c, 1.5, ["explosao"])
	igual(ex.size(), 1, "explodiu ao chegar")
	igual(c.projeteis.size(), 0, "saiu do ar")
	var feridas := ids.filter(func(a): return c.aranhas[a].vida < 1000.0)
	igual(feridas.size(), 3, "as três aranhas do grupo levaram dano (área)")
	verificar(ids.all(func(a): return c.aranhas[a].vida >= 1000.0 - 40.0 - 1e-3 and c.aranhas[a].vida <= 1000.0 - 20.0 + 1e-3), "dano entre metade (borda) e 40 (centro)")


func test_mata_grupo_e_cadencia() -> void:
	var res := []
	for bon in [0.0, 0.2]:
		var b := _base()
		var m: MapaOcupacao = b[0]
		var c: Colonia = b[1]
		var t := m.colocar("torre_foguetes", Vector2i(0, -1), 0)
		c._criar_ninho(Vector2i(20, -2), 1.0)
		c.bonus = func(k: String) -> float: return bon if k in ["dano_foguete", "cadencia_foguete"] else 0.0
		c.carregar_torre(t, 18)
		var v0: float = c.ninhos.values()[0].vida
		var tiros := _tick(c, 4.0, ["tiro"]).size()
		var explosoes := _tick(c, 0.0, [])
		c.carregar_torre(t, -int(c.torres[t].municao))          # para de atirar: só os que já estão no ar
		explosoes = _tick(c, 2.0, ["explosao"])
		var dano: float = v0 - (c.ninhos.values()[0].vida if not c.ninhos.is_empty() else 0.0)
		res.append([tiros, dano / maxf(1.0, tiros), explosoes.size()])
	verificar(res[0][0] >= 5 and res[0][0] <= 7, "1,5 disparos/s (%d em 4 s)" % res[0][0])
	verificar(res[1][0] > res[0][0], "cadência +20%%: mais disparos (%d → %d)" % [res[0][0], res[1][0]])
	perto(res[1][1], res[0][1] * 1.2, 0.5, "dano +20% por foguete")
	# aranhas em ataque: o lança-foguetes segura a onda
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var fonte := m.colocar("fornalha", Vector2i(-34, 0), 0)
	var ninho := c._criar_ninho(Vector2i(34, 0), 1.0)
	var t := m.colocar("torre_foguetes", Vector2i(-26, -1), 0)
	c.carregar_torre(t, 18)
	for k in 4:
		var a := c._nova_aranha(ninho)
		c.aranhas[a].estado = Colonia.E.ATACANDO
		c.aranhas[a].alvo = fonte
	var fontes: Array[Dictionary] = [{"id": fonte, "pos": Vector2(-33, 1)}]
	var mortas := 0
	for i in 30 * 90:
		c.tick(1.0 / 30.0, fontes)
		for e in c.eventos:
			if e.tipo == "aranha_morta": mortas += 1
	igual(mortas, 4, "matou as 4 aranhas do ataque")
	verificar(m.estruturas.has(fonte), "a fornalha sobreviveu")


func test_braco_traz_foguete() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 22):
		for y in range(-12, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	var col := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var f := Fabrica.new(m)
	var g := m.colocar("gerador", Vector2i(8, 6), 0)
	for t in [Vector2i(11, 6), Vector2i(17, 3), Vector2i(17, -2)]:
		m.colocar("poste_energia", t, 0)
	var torre := m.colocar("torre_foguetes", Vector2i(18, -8), 0)        # tiles y −8..−6; boca sul no tile (19, −5)
	var bau := m.colocar("bau", Vector2i(19, -4), 0)
	verificar(torre >= 0 and bau >= 0 and m.colocar("braco", Vector2i(19, -5), 2) >= 0, "montagem")
	f.torre_receber = func(id: int, n: int) -> void: col.carregar_torre(id, n)
	f.torre_aceita = col.aceita_municao
	f.reconstruir()
	f.combustivel[g] = 30.0
	f.baus[bau].merge({"foguete": 25, "municao": 5})
	for i in 30 * 40:
		f.tick(1.0 / 30.0)
	igual(int(col.torres[torre].municao), 18, "encheu com 18 foguetes")
	igual(int(f.baus[bau].get("foguete", 0)), 7, "o resto ficou no baú")
	igual(int(f.baus[bau].get("municao", 0)), 5, "munição de bala não serve ao lança-foguetes")


# ------------------------------------------------------------------ desenho
func _raiz() -> Node:
	return (Engine.get_main_loop() as SceneTree).root


func test_selo_rastro_e_explosao() -> void:
	var md: Dictionary = Registro.modelos.torre_foguetes
	var n: Node3D = (load(md.modelo) as PackedScene).instantiate()
	_raiz().add_child(n)
	var a := Animador.new()
	a.modelo = "torre_foguetes"
	n.add_child(a)
	if not a.is_inside_tree():
		a._ready()
	var ej := a.ejecao()
	verificar(ej.size() == 2, "saída do selo")
	if ej.size() == 2:
		verificar((ej[1] as Vector3).z > 1.0, "selo sai para trás do casulo (%s)" % str(ej[1]))
	var boca := a.boca()
	verificar(boca != Vector3.INF and boca.z < -0.3, "boca na frente (−Z do Godot) (%s)" % str(boca))
	a._gira("giro", PI * 0.5)
	verificar(a.boca().x < -0.3, "a boca gira com o giro (%s)" % str(a.boca()))
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var dc := DesenhoColonia.new()
	dc.mapa = m
	dc.colonia = Colonia.new(m, Poluicao.new(m.gerador), 3)
	dc.animadores_torre = func(_id: int) -> Animador: return a
	_raiz().add_child(dc)
	if not dc.is_inside_tree():
		dc._ready()
	var ev: Array[Dictionary] = [{"tipo": "tiro", "torre": 3, "nome": "torre_foguetes", "bala": true, "projetil": true, "dur": 1.0,
			"de": Vector2.ZERO, "para": Vector2(20, 0), "aranha": -1, "ninho": -1}]
	dc.atualizar(ev, 0.0)
	igual(dc.capsulas(), 1, "todo disparo ejeta o selo")
	perto(float(dc._capsulas[0].esc), float(md.capsula.escala), 1e-6, "selo na escala do modelo")
	igual(dc.voando(), 1, "foguete voando no desenho")
	dc._cartucho(ev[0])                       # (o atualizar solta a fumaça de torre que não está no mapa do teste)
	verificar(dc._fumacinhas.has(3), "o jato solta fumaça")
	if dc._fumacinhas.has(3):
		verificar((dc._fumacinhas[3].no as CPUParticles3D).amount >= 25, "fumaça do jato maior que a da bala (%d)" % (dc._fumacinhas[3].no as CPUParticles3D).amount)
	dc._capsulas.pop_back()
	var alto := -INF
	for i in 20:
		dc.atualizar([] as Array[Dictionary], 0.05)
		if dc.voando() > 0:
			alto = maxf(alto, (dc._voos[0].no as Node3D).position.y)
	verificar(alto > Grade.ponto_mundo(Vector2.ZERO).y + 1.0, "voa em arco")
	dc.atualizar([] as Array[Dictionary], 0.1)
	igual(dc.voando(), 0, "chegou e sumiu")
	var antes := dc.get_child_count()
	dc.atualizar([{"tipo": "explosao", "pos": Vector2(20, 0), "raio": 2.5, "torre": 3, "nome": "torre_foguetes"}] as Array[Dictionary], 0.0)
	verificar(dc.get_child_count() > antes, "explosão: faíscas, fumaça e clarão")
	dc.queue_free()
	n.queue_free()
