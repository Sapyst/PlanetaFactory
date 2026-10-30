extends Caso
## Muro de tijolo (muros_reforcados, fase 2.2a): pilar muro_tijolo + pano muro_tijolo_lado vindos do estudo
## (arte/estudos/conv_combate.py, grupo 'tijolo' de estudo_muros_mina.py), 700 ♥ (o dobro do muro de pedra), custa
## tijolo, arrasta em linha como o muro de pedra e as aranhas levam mais tempo para atravessar.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("muro_tijolo", {})
	igual(r.get("grupo", ""), "muro", "grupo muro")
	perto(float(r.get("vida", 0)), 2.0 * float(Registro.estruturas.muro_centro.vida), 1e-6, "o dobro do muro de pedra")
	perto(float(r.get("vida", 0)), 700.0, 1e-6, "700 ♥ (árvore)")
	igual(Registro.estruturas.get("muro_tijolo_lado", {}).get("vida", 0), r.get("vida"), "pano com a mesma vida")
	igual(Registro.progressao.custos.get("muro_tijolo", {}), {"tijolo": 5.0}, "custa tijolo")
	verificar("muro_tijolo" in Construtor.LINHA_RETA, "arrasta em linha")
	verificar(Registro.menu.categorias.any(func(cat): return "muro_tijolo" in cat.pecas), "no menu (Defesa)")
	verificar(ResourceLoader.exists("res://assets/icones/muro_tijolo.png"), "ícone na barra")
	for nome in ["muro_tijolo", "muro_tijolo_lado"]:
		var md: Dictionary = Registro.modelos.get(nome, {})
		igual(md.get("estudo", ""), "estudo_muros_mina.py", "%s convertido do estudo" % nome)
		verificar(md.get("ocupa_canto", false), "%s ocupa o canto como o muro de pedra" % nome)
		verificar(int(md.get("tris", 99999)) <= 900, "%s leve (%d triângulos)" % [nome, md.get("tris", 0)])
	# pilar ocupa o centro; o pano vai da face do pilar (0,30) até a borda norte, sem passar dela
	var d: Array = Registro.modelos.muro_tijolo.dims
	verificar(float(d[0]) <= 0.66 and float(d[1]) <= 0.66, "pilar dentro do tile (%s)" % str(d))
	var pano: Node3D = (load(Registro.modelos.muro_tijolo_lado.modelo) as PackedScene).instantiate()
	var lo := Vector3.INF
	var hi := -Vector3.INF
	for mi in pano.find_children("*", "MeshInstance3D", true, false):
		var aabb: AABB = (mi as MeshInstance3D).get_aabb()
		lo = lo.min(aabb.position)
		hi = hi.max(aabb.end)
	pano.free()
	perto(-lo.z, 0.5, 0.005, "pano chega na borda norte (−Z do Godot)")
	verificar(-hi.z >= 0.29, "pano começa na face do pilar (%.3f)" % -hi.z)


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("muros_reforcados"), "Muro de tijolo é jogável")
	verificar(not p.peca_liberada("muro_tijolo"), "travado no início")
	verificar(not p.disponivel("muros_reforcados"), "precisa de Munição (defesa) antes")
	p.concluidas = {"defesa": true}
	verificar(p.disponivel("muros_reforcados"), "depois de defesa")
	igual(p.custo("muros_reforcados"), {"pacote_pesquisa": 10}, "10 pacotes básicos (árvore)")
	p.concluidas["muros_reforcados"] = true
	verificar(p.peca_liberada("muro_tijolo"), "pesquisa libera o muro de tijolo")
	verificar(p.receita_liberada("cozer_tijolo"), "tijolo já sai da fornalha desde o início")


func test_construir_em_linha() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 12):
		for y in range(-3, 3):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	var plano := c.plano_linha("muro_tijolo", Vector2i(0, 0), Vector2i(7, 0), 0)
	igual(plano.size(), 8, "8 pilares numa linha")
	verificar(plano.all(func(p): return p.motivo == ""), "todos cabem")
	c.executar(plano)
	var n := 0
	for id in m.estruturas:
		if m.estruturas[id].nome == "muro_tijolo":
			n += 1
	igual(n, 8, "8 muros de tijolo no mapa")


## Mesmo ataque, muro de pedra × muro de tijolo no caminho: o de tijolo segura as aranhas por mais tempo.
func test_segura_mais() -> void:
	var tempos := {}
	for nome in ["muro_centro", "muro_tijolo"]:
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
		var t0 := -1.0                                # primeira mordida no muro
		for i in 30 * 240:
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
	verificar(tempos.muro_tijolo > tempos.muro_centro * 1.7, "tijolo aguenta ~o dobro de mordidas (%.1f s × %.1f s)" % [tempos.muro_tijolo, tempos.muro_centro])
