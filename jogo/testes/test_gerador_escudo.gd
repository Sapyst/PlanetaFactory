extends Caso
## Gerador de escudo (gerador_escudo, fase 2.4): modelo do estudo (estudo_gerador_escudo.py; conv_combate_meio.py) com
## a animação do cardã/pistões/ventoinhas; pesquisa escudo_1 (ciência militar + processador + acumulação; básico/
## automação/militar/químico × 75), que pede o processador (receita nova: 2 circuitos + 1 resina + 1 cristal lapidado
## + 5 água, no refinador). Bolha de 8 m: mordida em construção dentro dela gasta a carga do gerador (8 MJ = 400 de
## dano) em vez de vida; a carga vem da rede a 200 kW. Sem carga, a mordida passa.


func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("gerador_escudo", {})
	perto(float(r.escudo.raio), 8.0, 1e-6, "bolha de 8 m (árvore)")
	perto(float(r.carga_mj) / float(r.escudo.mj_por_dano), 400.0, 1e-3, "absorve 400 de dano (árvore)")
	igual(Fiacao.papel("gerador_escudo"), "consumo", "recarrega pela rede")
	var md: Dictionary = Registro.modelos.get("gerador_escudo", {})
	igual(Registro.area("gerador_escudo"), Vector2i(2, 2), "2×2")
	igual(md.get("estudo", ""), "estudo_gerador_escudo.py", "convertido do estudo")
	verificar(md.get("portas", []).is_empty(), "sem portas de item (só energia)")
	verificar(float(md.dims[0]) <= 2.0 and float(md.dims[1]) <= 2.0, "dentro da área (%s): a bolha do estudo saiu" % str(md.dims))
	verificar(float(md.dims[2]) < 3.0, "sem o fio de luz até o topo da bolha")
	verificar(md.get("anima", false), "tem a animação do estudo (cardã, pistões, ventoinhas)")
	verificar(ResourceLoader.exists("res://assets/icones/gerador_escudo.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return "gerador_escudo" in cat.pecas), "no menu (Defesa)")
	verificar(not Registro.progressao.custos.get("gerador_escudo", {}).is_empty(), "custo de construção")
	var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
	var ap := cena.find_children("*", "AnimationPlayer", true, false)
	verificar(not ap.is_empty() and (ap[0] as AnimationPlayer).has_animation("trabalho"), "animação trabalho no .glb")
	cena.free()


func test_processador_e_pesquisa() -> void:
	verificar(Registro.itens.has("processador"), "item processador")
	verificar(ResourceLoader.exists("res://assets/icones/itens/processador.png"), "ícone do processador")
	var r: Dictionary = Registro.receitas.processador
	igual(r.maquina, "refinador", "no refinador (bebe água; a montadora não tem boca de cano)")
	igual(_int(r.entradas), {"circuito": 2, "resina": 1, "cristal_lapidado": 1}, "receita da árvore")
	igual(_int(r.entradas_fluido), {"agua": 5}, "+ 5 água")
	var p := Pesquisa.new()
	verificar(p.jogavel("processador") and p.jogavel("escudo_1"), "jogáveis")
	p.concluidas = {"quimica": true}
	verificar(p.disponivel("processador"), "processador depois da química")
	igual(p.custo("processador"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60}, "custo da árvore")
	p.concluidas.merge({"processador": true, "ciencia_militar": true})
	verificar(p.receita_liberada("processador"), "libera o processador")
	verificar(not p.disponivel("escudo_1"), "escudo espera a acumulação")
	p.concluidas["acumulacao"] = true
	verificar(p.disponivel("escudo_1"), "ciência militar + processador + acumulação")
	igual(p.custo("escudo_1"), {"pacote_pesquisa": 75, "pacote_automacao": 75, "pacote_militar": 75, "pacote_quimico": 75}, "custo da árvore")
	p.concluidas["escudo_1"] = true
	verificar(p.peca_liberada("gerador_escudo"), "libera o gerador de escudo")


func _cena() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-10, 30):
		for y in range(-10, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var f := Fabrica.new(m)
	c.torre_energia = f.gastar_torre
	return [m, c, f]


func test_absorve_mordida() -> void:
	var b := _cena()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var f: Fabrica = b[2]
	var esc := m.colocar("gerador_escudo", Vector2i(0, 0), 0)
	var dentro := m.colocar("fornalha", Vector2i(4, 0), 0)
	var fora := m.colocar("fornalha", Vector2i(20, 0), 0)
	verificar(esc >= 0 and dentro >= 0 and fora >= 0, "montagem")
	f.reconstruir()
	f.carga_torre[esc] = 8.0                                   # escudo cheio
	var ninho := c._criar_ninho(Vector2i(24, 8), 1.0)
	var a1 := c._nova_aranha(ninho)
	var a2 := c._nova_aranha(ninho)
	c.aranhas[a1].pos = Vector2(5.0, 2.6)
	c.aranhas[a2].pos = Vector2(21.0, 2.6)
	var impactos := 0
	for i in 30 * 5:
		for a in [a1, a2]:
			c.aranhas[a].estado = Colonia.E.ATACANDO
		c.aranhas[a1].alvo = dentro
		c.aranhas[a2].alvo = fora
		c.tick(1.0 / 30.0, [])
		impactos += c.eventos.filter(func(e): return e.tipo == "escudo").size()
	verificar(not c.vida.has(dentro), "dentro da bolha a fornalha não perdeu vida")
	verificar(c.vida.has(fora), "fora da bolha perdeu")
	var gasto := 8.0 - float(f.carga_torre[esc])
	var dano_fora := float(Registro.estruturas.fornalha.vida) - float(c.vida[fora])
	perto(gasto, dano_fora * 0.02, 0.05, "o escudo gastou 0,02 MJ por ponto de dano (%.2f MJ)" % gasto)
	verificar(impactos >= 10 and impactos <= 25, "impactos na bolha para o desenho, no máximo 4/s (%d)" % impactos)
	# sem carga a mordida passa
	f.carga_torre[esc] = 0.0
	for i in 30 * 2:
		c.aranhas[a1].estado = Colonia.E.ATACANDO
		c.aranhas[a1].alvo = dentro
		c.tick(1.0 / 30.0, [])
	verificar(c.vida.has(dentro), "sem carga, a fornalha de dentro também perde vida")


func test_recarrega_pela_rede() -> void:
	var b := _cena()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[2]
	var g := m.colocar("gerador", Vector2i(8, 6), 0)
	m.colocar("poste_energia", Vector2i(5, 4), 0)
	var esc := m.colocar("gerador_escudo", Vector2i(2, 2), 0)
	f.reconstruir()
	f.combustivel[g] = 100.0
	igual(float(f.carga_torre.get(esc, -1.0)), 0.0, "começa vazio")
	for i in 30 * 10:
		f.tick(1.0 / 30.0)
	perto(float(f.carga_torre[esc]), 2.0, 0.1, "200 kW: 2 MJ em 10 s")
	for i in 30 * 40:
		f.tick(1.0 / 30.0)
	perto(float(f.carga_torre[esc]), 8.0, 1e-3, "cheio em 40 s e para de puxar")


# ------------------------------------------------------------------ desenho
func _raiz() -> Node:
	return (Engine.get_main_loop() as SceneTree).root


func test_bolha_no_desenho() -> void:
	var b := _cena()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var esc := m.colocar("gerador_escudo", Vector2i(0, 0), 0)
	var dc := DesenhoColonia.new()
	dc.mapa = m
	dc.colonia = c
	var carga := [8.0]
	dc.carga = func(_id: int) -> float: return carga[0]
	_raiz().add_child(dc)
	if not dc.is_inside_tree():
		dc._ready()
	c.tick(1.0 / 30.0, [])
	dc.atualizar([] as Array[Dictionary], 0.016)
	perto(dc.forca_bolha(esc), 1.0, 1e-6, "bolha cheia")
	var no: MeshInstance3D = dc._bolhas[esc].no
	perto((no.mesh as SphereMesh).radius, 8.0, 1e-6, "no raio da regra")
	verificar((no.mesh as SphereMesh).is_hemisphere, "meia esfera sobre o chão")
	dc.atualizar([{"tipo": "escudo", "id": esc, "centro": Vector2(1, 1), "pos": Vector2(9, 1)}] as Array[Dictionary], 0.016)
	verificar(float(dc._bolhas[esc].impacto) > 0.9, "a mordida acende a bolha em âmbar")
	carga[0] = 0.0
	dc.atualizar([] as Array[Dictionary], 0.016)
	verificar(not no.visible, "sem carga a bolha some")
	m.remover(esc)
	dc.atualizar([] as Array[Dictionary], 0.016)
	igual(dc.forca_bolha(esc), -1.0, "gerador removido: sem bolha")
	dc.queue_free()
