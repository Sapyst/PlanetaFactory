extends Caso
## Muro de liga e muro de campo (fase 2.4): pilares muro_liga / muro_escudo + panos *_lado vindos de
## estudo_muros_mina.py (conv_combate_meio.py), mesmo sistema do muro de tijolo (arrasta em linha; o pilar ganha um
## pano por vizinho muro, de qualquer tipo). Liga: 1.500 ♥, pesquisa muro_liga (muro de tijolo + liga leve + ciência
## militar), feito de liga leve (receita nova: 1 aço + 2 placas de cobre + 1 resina → 2). Campo: regenera 5 ♥/s com
## energia da rede (10 kW por pilar); pesquisa muro_escudo pede escudo 2 (ciência de tempestade, fase 2.5): travada.


func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


func test_dados_e_modelos() -> void:
	perto(float(Registro.estruturas.muro_liga.vida), 1500.0, 1e-6, "liga: 1.500 ♥ (árvore)")
	perto(float(Registro.estruturas.muro_escudo.regenera), 5.0, 1e-6, "campo: 5 ♥/s (árvore)")
	verificar(float(Registro.estruturas.muro_escudo.get("energia_kw", 0)) > 0.0, "campo consome energia")
	igual(Fiacao.papel("muro_escudo"), "consumo", "campo entra na rede")
	for nome in ["muro_liga", "muro_escudo"]:
		verificar(nome in Construtor.LINHA_RETA, "%s arrasta em linha" % nome)
		verificar(Registro.menu.categorias.any(func(cat): return nome in cat.pecas), "%s no menu (Defesa)" % nome)
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % nome), "ícone de " + nome)
		verificar(not Registro.progressao.custos.get(nome, {}).is_empty(), "custo de " + nome)
	for nome in ["muro_liga", "muro_liga_lado", "muro_escudo", "muro_escudo_lado"]:
		var md: Dictionary = Registro.modelos.get(nome, {})
		igual(md.get("estudo", ""), "estudo_muros_mina.py", "%s convertido do estudo" % nome)
		verificar(md.get("ocupa_canto", false), "%s ocupa o canto como os outros muros" % nome)
		verificar(int(md.get("tris", 99999)) <= 1400, "%s leve (%d triângulos)" % [nome, md.get("tris", 0)])
		verificar(float(md.dims[0]) <= 1.0 and float(md.dims[1]) <= 1.0, "%s dentro do tile (%s)" % [nome, str(md.dims)])
	for nome in ["muro_liga", "muro_escudo"]:
		verificar(float(Registro.modelos[nome].dims[2]) > float(Registro.inimigos.aranha.altura_que_bloqueia), "%s barra as aranhas" % nome)
	# panos: do pilar até a borda norte, sem passar dela
	for nome in ["muro_liga_lado", "muro_escudo_lado"]:
		var pano: Node3D = (load(Registro.modelos[nome].modelo) as PackedScene).instantiate()
		var lo := Vector3.INF
		for mi in pano.find_children("*", "MeshInstance3D", true, false):
			lo = lo.min((mi as MeshInstance3D).get_aabb().position)
		pano.free()
		verificar(-lo.z <= 0.501, "%s não passa da borda norte (%.3f)" % [nome, -lo.z])
	verificar(Registro.modelos.muro_escudo_lado.has("campo"), "pano do campo diz onde vai a parede")


func test_liga_leve() -> void:
	verificar(Registro.itens.has("liga_leve"), "item liga leve")
	verificar(ResourceLoader.exists("res://assets/icones/itens/liga_leve.png"), "ícone da liga leve")
	var r: Dictionary = Registro.receitas.liga_leve
	igual(r.maquina, "montadora")
	igual(_int(r.entradas), {"barra_aco": 1, "placa_cobre": 2, "resina": 1}, "receita da árvore")
	igual(_int(r.saidas), {"liga_leve": 2}, "→ 2")
	var p := Pesquisa.new()
	verificar(p.jogavel("liga_leve"), "pesquisa liga leve jogável")
	p.concluidas = {"quimica": true}
	verificar(not p.disponivel("liga_leve"), "precisa do aço")
	p.concluidas["aco"] = true
	verificar(p.disponivel("liga_leve"), "química + aço")
	igual(p.custo("liga_leve"), {"pacote_pesquisa": 40, "pacote_automacao": 40, "pacote_quimico": 40}, "custo da árvore")
	p.concluidas["liga_leve"] = true
	verificar(p.receita_liberada("liga_leve"), "libera a receita")


func test_pesquisas() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("muro_liga") and p.jogavel("muro_escudo"), "as duas jogáveis")
	p.concluidas = {"muros_reforcados": true, "ciencia_militar": true}
	verificar(not p.disponivel("muro_liga"), "liga espera a liga leve")
	p.concluidas["liga_leve"] = true
	verificar(p.disponivel("muro_liga"), "muro de tijolo + liga leve + ciência militar")
	igual(p.custo("muro_liga"), {"pacote_pesquisa": 40, "pacote_automacao": 40, "pacote_militar": 40, "pacote_quimico": 40}, "custo da árvore")
	p.concluidas["muro_liga"] = true
	verificar(p.peca_liberada("muro_liga"), "libera o muro de liga")
	verificar(not p.disponivel("muro_escudo"), "muro de campo espera o escudo 2 (tempestade)")
	verificar(not p.jogavel("escudo_2"), "escudo 2 ainda em breve")
	p.livre = true
	verificar(p.peca_liberada("muro_escudo"), "no modo livre (demo) o campo já se constrói")


func test_construir_em_linha_e_ligar() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 14):
		for y in range(-3, 3):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	for nome in ["muro_liga", "muro_escudo"]:
		var y := 0 if nome == "muro_liga" else 2
		var plano := c.plano_linha(nome, Vector2i(0, y), Vector2i(5, y), 0)
		igual(plano.size(), 6, "%s: 6 pilares numa linha" % nome)
		verificar(plano.all(func(p): return p.motivo == ""), "%s: todos cabem" % nome)
		c.executar(plano)
	var n := {}
	for id in m.estruturas:
		n[m.estruturas[id].nome] = int(n.get(m.estruturas[id].nome, 0)) + 1
	igual(n.get("muro_liga", 0), 6, "6 de liga")
	igual(n.get("muro_escudo", 0), 6, "6 de campo")
	# os panos ligam qualquer tipo de muro (tabela do mundo)
	var muros: Dictionary = load("res://cenas/mundo_demo.gd").MUROS
	igual(muros.get("muro_liga"), "muro_liga_lado", "pilar de liga → pano de liga")
	igual(muros.get("muro_escudo"), "muro_escudo_lado", "pilar de campo → pano de campo")
	var parede: MeshInstance3D = load("res://cenas/mundo_demo.gd").parede_de_campo(Registro.modelos.muro_escudo_lado.campo)
	verificar(parede.material_override is ShaderMaterial, "parede de campo com o shader do campo")
	verificar(-parede.position.z > 0.25 and -parede.position.z < 0.5, "parede sobre o trilho do pano")
	verificar(parede.position.y > 0.5, "em pé sobre o trilho")
	parede.free()


## Mesmo ataque, muro de tijolo × muro de liga: o de liga segura as aranhas por mais tempo (1.500 × 700 ♥).
func test_liga_segura_mais() -> void:
	var tempos := {}
	for nome in ["muro_tijolo", "muro_liga"]:
		var m := MapaOcupacao.new(GeradorMundo.new(1337))
		var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
		for x in range(-38, 37):
			for y in range(-6, 8):
				m.limpar_obstaculo(Vector2i(x, y))
		var fonte := m.colocar("fornalha", Vector2i(-34, 0), 0)
		var ninho := c._criar_ninho(Vector2i(30, 0), 1.0)
		var muros: Array[int] = []
		for y in range(-6, 8):
			muros.append(m.colocar(nome, Vector2i(-10, y), 0))
		for k in 4:
			var a := c._nova_aranha(ninho)
			c.aranhas[a].estado = Colonia.E.ATACANDO
			c.aranhas[a].alvo = fonte
		var fontes: Array[Dictionary] = [{"id": fonte, "pos": Vector2(-33, 1)}]
		var t := -1.0
		var t0 := -1.0
		for i in 30 * 300:
			c.tick(1.0 / 30.0, fontes)
			if t0 < 0.0 and muros.any(func(id): return c.vida.has(id)):
				t0 = i / 30.0
			for e in c.eventos:
				if e.tipo == "destruida" and e.id in muros and t < 0.0:
					t = i / 30.0
			if t >= 0.0:
				break
		verificar(t > 0.0 and t0 >= 0.0, "%s foi derrubado" % nome)
		tempos[nome] = t - t0
	verificar(tempos.muro_liga > tempos.muro_tijolo * 1.8, "liga aguenta ~2× o tijolo (%.1f s × %.1f s)" % [tempos.muro_liga, tempos.muro_tijolo])


func test_campo_regenera_com_energia() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 16):
		for y in range(-4, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var f := Fabrica.new(m)
	var g := m.colocar("gerador", Vector2i(8, 6), 0)
	m.colocar("poste_energia", Vector2i(6, 3), 0)
	var muro := m.colocar("muro_escudo", Vector2i(4, 2), 0)
	var sem := m.colocar("muro_escudo", Vector2i(-3, -3), 0)       # longe do poste: sem energia
	verificar(muro >= 0 and sem >= 0, "montagem")
	f.reconstruir()
	f.combustivel[g] = 50.0
	c.energia = f.energia
	c.vida[muro] = 300.0
	c.vida[sem] = 300.0
	for i in 30 * 10:
		f.tick(1.0 / 30.0)
		c.tick(1.0 / 30.0, [])
	perto(f.energia(muro), 1.0, 1e-3, "o pilar recebe energia do poste")
	perto(f.energia(sem), 0.0, 1e-6, "o de longe não")
	perto(float(c.vida.get(muro, 800.0)), 350.0, 2.0, "com energia: +5 ♥/s (10 s → +50)")
	perto(float(c.vida[sem]), 300.0, 1e-6, "sem energia não regenera")
	c.vida[muro] = 795.0
	for i in 30 * 2:
		f.tick(1.0 / 30.0)
		c.tick(1.0 / 30.0, [])
	verificar(not c.vida.has(muro), "inteiro: sai da lista de dano (barra some)")
	# o muro de liga não regenera
	var liga := m.colocar("muro_liga", Vector2i(0, 6), 0)
	c.vida[liga] = 1000.0
	for i in 30 * 3:
		c.tick(1.0 / 30.0, [])
	perto(float(c.vida[liga]), 1000.0, 1e-6, "liga não regenera")
