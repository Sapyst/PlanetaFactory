extends Caso
## Bomba d'água (bomba_agua, fase 2.3): 2×2 do estudo_bomba_agua.py (arte/estudos/conv_agua.py), encostada na água
## pelo lado SUL (a tomada com a grade; gira com a peça), 40 de água/s pelo cano da borda norte (fluido "agua" na rede
## de canos de sempre); água suja na tomada rende menos. Pesquisa "Água como insumo" (fluidos + automação).


func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	return [g, m, Fabrica.new(m), AmbienteVivo.new(g, m, 3), Construtor.new(m)]


## Lugar 2×2 em terra com água logo ao sul (rio/lago) — gira 0.
func _margem(g: GeradorMundo, m: MapaOcupacao) -> Vector2i:
	for x in range(-300, 300, 2):
		for y in range(-300, 300, 2):
			var t := Vector2i(x, y)
			if g.terreno(t) != GeradorMundo.Terreno.TERRA or not g.eh_agua(g.terreno(t + Vector2i(0, -1))):
				continue
			for dx in 2:
				for dy in 2:
					m.limpar_obstaculo(t + Vector2i(dx, dy))
			if m.motivo_bloqueio("bomba_agua", t, 0) == "":
				return t
	return Vector2i(9999, 0)


## Cano saindo da porta de fluido `n` (índice em modelos.json) da estrutura `id`, `comp` tiles para fora.
func _cano_na_porta(c: Construtor, id: int, n := 0, comp := 3) -> Vector2i:
	var e: Dictionary = c.mapa.estruturas[id]
	var p := Grade.porta_no_mundo(Registro.modelos[e.nome].portas[n], e.minimo, e.area, e.rot)
	var d := Grade.DIRECOES.find(p.dir)
	for i in comp:
		c.mapa.limpar_obstaculo(p.tile_fora + p.dir * i)
	c.executar(c.plano_linha("cano", p.tile_fora, p.tile_fora + p.dir * (comp - 1), Construtor.rot_do_fluxo(d)))
	return p.tile_fora


func test_dados_e_modelo() -> void:
	var md: Dictionary = Registro.modelos.get("bomba_agua", {})
	igual(md.get("estudo", ""), "estudo_bomba_agua.py", "convertido do estudo")
	igual(Registro.area("bomba_agua"), Vector2i(2, 2), "2×2")
	igual(md.portas.size(), 1, "uma porta")
	igual(md.portas[0].nome, "PORTA_FLUIDO_SAI_N1", "solta pela borda norte, tile leste")
	perto(float(md.portas[0].pos[2]), float(Registro.modelos.cano_reto.portas[0].pos[2]), 0.01, "flange na altura dos canos")
	verificar(int(md.tris) <= 10000, "orçamento de triângulos (%d)" % md.tris)
	verificar(float(md.dims[1]) <= 2.5, "cais e grade avançam no máximo meio tile sobre a água (%s)" % str(md.dims))
	var r: Dictionary = Registro.estruturas.bomba_agua
	igual(r.grupo, "maquina")
	verificar(r.get("tomada_agua", false), "precisa de água na tomada")
	igual(int(Registro.receitas.bombear_agua.saidas_fluido.agua), 40, "40 de água/s (árvore)")
	verificar(ResourceLoader.exists("res://assets/icones/bomba_agua.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Canos" and "bomba_agua" in cat.pecas), "na aba Canos")
	verificar(not Construtor.custo_de("bomba_agua").is_empty(), "tem custo")
	igual(Registro.nome_fluido("agua"), "Água", "nome do fluido com acento")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("bomba_agua"), "jogável")
	verificar(not p.peca_liberada("bomba_agua"), "travada no início")
	p.concluidas = {"fluidos": true}
	verificar(not p.disponivel("bomba_agua"), "precisa de automação")
	p.concluidas["automacao"] = true
	verificar(p.disponivel("bomba_agua"), "fluidos + automação")
	igual(p.custo("bomba_agua"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "básico × 30 + automação × 30")
	p.concluidas["bomba_agua"] = true
	verificar(p.peca_liberada("bomba_agua"), "libera a bomba")
	verificar(p.receita_liberada("aco_refrigerado") and p.receita_liberada("lapidar_refrigerado"), "libera as receitas refrigeradas")


func test_tomada_precisa_de_agua_ao_sul() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var t := _margem(g, m)
	verificar(t.x != 9999, "achou margem com água ao sul")
	igual(m.motivo_bloqueio("bomba_agua", t, 0), "", "tomada encostada na água: pode")
	for tt in MapaOcupacao.tiles_da_tomada(t, Vector2i(2, 2), 0):
		igual(tt.y, t.y - 1, "a tomada fica logo ao sul")
	# girada 180°: a tomada olha para o norte (terra) — se lá não houver água, não pode
	var norte := MapaOcupacao.tiles_da_tomada(t, Vector2i(2, 2), 2)
	var tem := false
	for tt in norte:
		tem = tem or g.eh_agua(g.terreno(tt))
	if not tem:
		igual(m.motivo_bloqueio("bomba_agua", t, 2), "tomada_seca", "girada para a terra: não pode")
	# longe da água
	var seco := Vector2i(9999, 0)
	for x in range(-60, 60, 3):
		if seco.x == 9999 and g.terreno(Vector2i(x, 40)) == GeradorMundo.Terreno.TERRA:
			var ok := true
			for dx in range(-2, 4):
				for dy in range(-2, 4):
					ok = ok and not g.eh_agua(g.terreno(Vector2i(x + dx, 40 + dy)))
			if ok:
				for dx in 2:
					for dy in 2:
						m.limpar_obstaculo(Vector2i(x + dx, 40 + dy))
				if g.nivel(Vector2i(x, 40)) == g.nivel(Vector2i(x + 1, 41)) and g.nivel(Vector2i(x, 40)) == g.nivel(Vector2i(x + 1, 40)) and g.nivel(Vector2i(x, 40)) == g.nivel(Vector2i(x, 41)):
					seco = Vector2i(x, 40)
	verificar(seco.x != 9999, "achou chão seco")
	igual(m.motivo_bloqueio("bomba_agua", seco, 0), "tomada_seca", "longe da água não pode")
	verificar(Registro.menu.motivos.has("tomada_seca"), "a dica explica o motivo")


func test_bombeia_agua_no_cano() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var c: Construtor = b[4]
	var t := _margem(b[0], m)
	var id := m.colocar("bomba_agua", t, 0)
	var fora := _cano_na_porta(c, id, 0, 4)
	f.reconstruir()
	var bomba: Maquina = f.maquinas[id]
	igual(bomba.receita_id, "bombear_agua")
	var rede := f.rede_de(m.tiles[fora])
	verificar(not rede.is_empty(), "o cano encostado na flange norte é uma rede")
	for i in 5:
		bomba.energia = 1.0
		bomba.tick(1.0)
		f._tick_fluidos(1.0)
	igual(rede.fluido, "agua", "a rede leva água")
	perto(float(rede.qtd), 200.0, 0.5, "40/s em 5 s (4 canos de 100 cabem)")
	bomba.energia = 0.0
	var antes := float(rede.qtd)
	bomba.tick(1.0)
	f._tick_fluidos(1.0)
	perto(float(rede.qtd), antes, 0.01, "sem energia não bombeia")


func test_agua_suja_rende_menos() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var t := _margem(b[0], m)
	var id := m.colocar("bomba_agua", t, 0)
	f.reconstruir()
	a.tick(1.0, f, null)
	perto(f.maquinas[id].velocidade, 1.0, 1e-3, "água limpa: rende tudo")
	for tt in MapaOcupacao.tiles_da_tomada(t, Vector2i(2, 2), 0):
		a.somar(tt, AmbienteVivo.AGUA, 1.0)
	a.tick(1.0, f, null)
	verificar(float(a.contaminacao.get(id, 0.0)) > 0.9, "tomada suja")
	verificar(f.maquinas[id].velocidade < 0.5, "rende menos (%.2f)" % f.maquinas[id].velocidade)
