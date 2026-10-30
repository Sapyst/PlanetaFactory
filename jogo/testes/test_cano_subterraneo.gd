extends Caso
## Cano subterrâneo (cano_subterraneo, fase 2.2b): entrada e saída 1×1 do estudo_cano_subterraneo.py
## (arte/estudos/conv_logistica_base.py); a entrada liga na primeira saída alinhada à frente, mesma rotação, até 9
## tiles livres no meio (alcance 10) — uma rede de fluido só, e os tiles do meio ficam livres para construir.


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 20):
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func test_dados_e_modelos() -> void:
	for p in ["cano_subterraneo_entrada", "cano_subterraneo_saida"]:
		var md: Dictionary = Registro.modelos.get(p, {})
		igual(md.get("estudo", ""), "estudo_cano_subterraneo.py", "%s convertido do estudo" % p)
		igual(Registro.estruturas[p].grupo, "cano")
		verificar(DesenhoLotes.aceita(p), "%s desenhado em lote como os canos" % p)
		verificar(Portas.eh_cano(p), "%s é cano para as portas" % p)
		igual(md.get("portas", []).size(), 1, "%s: uma porta de fluido na superfície" % p)
		verificar(int(md.get("tris", 99999)) <= 1600, "%s leve (%d)" % [p, md.get("tris", 0)])
		var d: Array = md.dims
		verificar(float(d[0]) <= 1.0 and float(d[1]) <= 1.0, "%s dentro do tile (%s)" % [p, str(d)])
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % p), "ícone %s" % p)
		verificar(Registro.menu.categorias.any(func(cat): return p in cat.pecas), "%s no menu" % p)
		verificar(not Construtor.custo_de(p).is_empty(), "%s tem custo" % p)
	igual(Registro.modelos.cano_subterraneo_entrada.portas[0].nome, "PORTA_FLUIDO_ENT_S0", "entrada recebe pelo sul")
	igual(Registro.modelos.cano_subterraneo_saida.portas[0].nome, "PORTA_FLUIDO_SAI_N0", "saída entrega pelo norte")
	perto(float(Registro.modelos.cano_subterraneo_entrada.portas[0].pos[2]), float(Registro.modelos.cano_reto.portas[0].pos[2]), 0.01, "na altura dos canos")
	igual(int(Registro.estruturas.cano_subterraneo_entrada.alcance), 10, "até 9 tiles livres no meio (árvore)")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("cano_subterraneo"), "jogável")
	verificar(not p.peca_liberada("cano_subterraneo_entrada"), "travado no início")
	p.concluidas = {"fluidos": true}
	verificar(not p.disponivel("cano_subterraneo"), "precisa de logística")
	p.concluidas["logistica"] = true
	verificar(p.disponivel("cano_subterraneo"), "fluidos + logística")
	igual(p.custo("cano_subterraneo"), {"pacote_pesquisa": 15}, "básico × 15 (árvore)")
	p.concluidas["cano_subterraneo"] = true
	verificar(p.peca_liberada("cano_subterraneo_entrada") and p.peca_liberada("cano_subterraneo_saida"), "libera entrada e saída")


func test_uma_rede_por_baixo() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var leste := Construtor.rot_do_fluxo(1)
	c.executar(c.plano_linha("cano", Vector2i(-4, 0), Vector2i(-1, 0), leste))
	c.executar(c.plano_peca("cano_subterraneo_entrada", Vector2i(0, 0), leste))
	c.executar(c.plano_linha("esteira", Vector2i(4, -3), Vector2i(4, 3), 0))       # obstáculos no meio
	c.mapa.colocar("bau", Vector2i(6, 0), 0)
	c.executar(c.plano_peca("cano_subterraneo_saida", Vector2i(10, 0), leste))      # 9 tiles livres no meio
	c.executar(c.plano_linha("cano", Vector2i(11, 0), Vector2i(14, 0), leste))
	f.reconstruir()
	var ent: int = c.mapa.tiles[Vector2i(0, 0)]
	var sai: int = c.mapa.tiles[Vector2i(10, 0)]
	igual(f.par_subterraneo(ent), sai, "a entrada achou a saída")
	var a := f.rede_de(c.mapa.tiles[Vector2i(-4, 0)])
	var b := f.rede_de(c.mapa.tiles[Vector2i(14, 0)])
	verificar(not a.is_empty() and a == b, "uma rede só, dos dois lados")
	igual(f.redes_fluido.size(), 1, "uma rede de fluido")
	perto(float(a.cap), 10.0 * 100.0, 1e-3, "8 canos + entrada + saída")
	# o fluido posto de um lado é o mesmo do outro (volume único) e sobrevive à remontagem
	a.fluido = "seiva"
	a.qtd = 600.0
	f.reconstruir()
	var b2 := f.rede_de(c.mapa.tiles[Vector2i(14, 0)])
	igual(b2.fluido, "seiva")
	perto(float(b2.qtd), 600.0, 0.5, "seiva continua na rede depois de remontar")


func test_limites() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var leste := Construtor.rot_do_fluxo(1)
	var norte := Construtor.rot_do_fluxo(0)
	# longe demais (10 livres no meio)
	c.executar(c.plano_peca("cano_subterraneo_entrada", Vector2i(0, 0), leste))
	c.executar(c.plano_peca("cano_subterraneo_saida", Vector2i(11, 0), leste))
	# rotação diferente não liga
	c.executar(c.plano_peca("cano_subterraneo_entrada", Vector2i(0, 3), leste))
	c.executar(c.plano_peca("cano_subterraneo_saida", Vector2i(3, 3), norte))
	# saída atrás não liga
	c.executar(c.plano_peca("cano_subterraneo_entrada", Vector2i(5, 6), leste))
	c.executar(c.plano_peca("cano_subterraneo_saida", Vector2i(2, 6), leste))
	# a primeira saída alinhada é a que vale
	c.executar(c.plano_peca("cano_subterraneo_entrada", Vector2i(0, 9), leste))
	c.executar(c.plano_peca("cano_subterraneo_saida", Vector2i(3, 9), leste))
	c.executar(c.plano_peca("cano_subterraneo_saida", Vector2i(6, 9), leste))
	f.reconstruir()
	igual(f.par_subterraneo(c.mapa.tiles[Vector2i(0, 0)]), -1, "10 tiles livres: longe demais")
	igual(f.par_subterraneo(c.mapa.tiles[Vector2i(0, 3)]), -1, "rotação diferente")
	igual(f.par_subterraneo(c.mapa.tiles[Vector2i(5, 6)]), -1, "saída atrás")
	igual(f.par_subterraneo(c.mapa.tiles[Vector2i(0, 9)]), c.mapa.tiles[Vector2i(3, 9)], "a primeira saída à frente")
	igual(f.par_subterraneo(c.mapa.tiles[Vector2i(3, 9)]), -1, "saída não procura par")
	verificar(f.rede_de(c.mapa.tiles[Vector2i(0, 0)]) != f.rede_de(c.mapa.tiles[Vector2i(11, 0)]), "redes separadas sem par")
