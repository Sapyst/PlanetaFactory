extends Caso
## Química da era do meio (fase 2.3): pesquisa "Química de seiva" (refino + bomba d'água) libera resina (30 seiva +
## 10 água) e o pacote químico (1 resina + 1 bateria + 20 água → 2) no refinador; "Bioquímica" (reflorestar + filtro
## que devolve água + química) libera o pacote ecológico (5 biomassa + 1 vidro + 30 água LIMPA). Com o pacote químico
## existindo, as melhorias que o pedem (mineração 2, pesquisa 2) passam a ser pesquisáveis. A resina bebe dois
## fluidos: seiva por uma boca do refinador e água pela outra (a saída de fluido vira 2ª entrada quando a receita
## não solta fluido).


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-10, 14):
		for y in range(-10, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _cano_na_porta(c: Construtor, id: int, nome_porta: String, comp := 2) -> Vector2i:
	var e: Dictionary = c.mapa.estruturas[id]
	for pt in Registro.modelos[e.nome].portas:
		if pt.nome == nome_porta:
			var p := Grade.porta_no_mundo(pt, e.minimo, e.area, e.rot)
			var d := Grade.DIRECOES.find(p.dir)
			c.executar(c.plano_linha("cano", p.tile_fora, p.tile_fora + p.dir * (comp - 1), Construtor.rot_do_fluxo(d)))
			return p.tile_fora
	return Vector2i(9999, 0)


## Os números do JSON chegam como float: compara como inteiros.
func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


func test_itens_e_receitas() -> void:
	for it in ["resina", "pacote_quimico", "pacote_ecologico"]:
		verificar(Registro.itens.has(it), "item %s" % it)
		verificar(ResourceLoader.exists("res://assets/icones/itens/%s.png" % it), "ícone do item %s" % it)
		verificar(Registro.modelos.has(Registro.itens[it].get("modelo_de", it)), "%s tem modelo (derivado) na esteira" % it)
	igual(Registro.itens.pacote_quimico.nome, "Pacote químico", "nome com acento")
	igual(Registro.itens.pacote_ecologico.nome, "Pacote ecológico", "nome com acento")
	var r := Registro.receitas
	igual(_int(r.resina.entradas_fluido), {"seiva": 30, "agua": 10}, "resina: 30 seiva + 10 água (árvore)")
	igual(_int(r.resina.saidas), {"resina": 1})
	igual(_int(r.pacote_quimico.entradas), {"resina": 1, "bateria": 1}, "pacote químico: resina + bateria")
	igual(_int(r.pacote_quimico.entradas_fluido), {"agua": 20}, "+ 20 água")
	igual(_int(r.pacote_quimico.saidas), {"pacote_quimico": 2}, "→ 2")
	igual(_int(r.pacote_ecologico.entradas), {"biomassa": 5, "vidro": 1}, "pacote ecológico: 5 biomassa + 1 vidro")
	igual(_int(r.pacote_ecologico.entradas_fluido), {"agua_limpa": 30}, "+ 30 água LIMPA")
	for k in ["resina", "pacote_quimico", "pacote_ecologico"]:
		igual(r[k].maquina, "refinador", "%s no refinador" % k)


func test_pesquisas() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("quimica") and p.jogavel("bioquimica"), "química e bioquímica jogáveis")
	p.concluidas = {"refino": true}
	verificar(not p.disponivel("quimica"), "química precisa da bomba d'água")
	p.concluidas["bomba_agua"] = true
	verificar(p.disponivel("quimica"), "refino + bomba d'água")
	igual(p.custo("quimica"), {"pacote_pesquisa": 50, "pacote_automacao": 50}, "básico × 50 + automação × 50")
	verificar(not p.pacote_liberado("pacote_quimico"), "laboratório ainda não estoca químico")
	p.concluidas["quimica"] = true
	verificar(p.receita_liberada("resina") and p.receita_liberada("pacote_quimico"), "libera resina e pacote químico")
	verificar(p.pacote_liberado("pacote_quimico"), "laboratório aceita o pacote químico")
	p.concluidas["mineracao_1"] = true
	p.concluidas["pesquisa_vel_1"] = true
	verificar(p.disponivel("mineracao_2"), "mineração 2 deixou de ser travada (o pacote químico existe)")
	verificar(p.disponivel("pesquisa_vel_2"), "velocidade de pesquisa 2 também")
	verificar(not p.disponivel("bioquimica"), "bioquímica precisa do filtro que devolve água e do reflorestamento")
	p.concluidas["filtro_agua_limpa"] = true
	p.concluidas["reflorestar"] = true
	verificar(p.disponivel("bioquimica"), "reflorestar + filtro_agua_limpa + química")
	igual(p.custo("bioquimica"), {"pacote_pesquisa": 40, "pacote_automacao": 40, "pacote_quimico": 40}, "+ químico × 40")
	p.concluidas["bioquimica"] = true
	verificar(p.pacote_liberado("pacote_ecologico"), "laboratório aceita o ecológico")


func test_laboratorio_aceita_quimico() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var p := Pesquisa.new()
	f.pesquisa = p
	var id := c.mapa.colocar("laboratorio", Vector2i(0, 0), 0)
	f.reconstruir()
	var lab: Dictionary = f.laboratorios[id]
	verificar(not f.lab_aceita(lab, "pacote_quimico"), "sem química, não aceita")
	p.concluidas = {"refino": true, "bomba_agua": true, "quimica": true}
	verificar(f.lab_aceita(lab, "pacote_quimico"), "com química, estoca")
	p.concluidas.merge({"automacao": true, "mineracao_1": true})
	p.escolher("mineracao_2")
	igual(p.ativa, "mineracao_2", "mineração 2 pesquisável")
	igual(p.tipos_ativa(), ["pacote_pesquisa", "pacote_automacao", "pacote_quimico"], "gasta 1 de cada (com o químico)")


func test_resina_com_dois_fluidos() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("refinador", Vector2i(0, 0), 0)
	var oeste := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_O1", 2)
	var leste := _cano_na_porta(c, id, "PORTA_FLUIDO_SAI_L1", 2)
	f.reconstruir()
	var r_seiva := f.rede_de(c.mapa.tiles[oeste])
	var r_agua := f.rede_de(c.mapa.tiles[leste])
	verificar(r_seiva != r_agua, "duas redes, uma por boca")
	r_seiva.fluido = "seiva"
	r_seiva.qtd = 200.0
	r_agua.fluido = "agua"
	r_agua.qtd = 200.0
	f.escolher_receita(id, "resina")
	var m: Maquina = f.maquinas[id]
	for i in 14:
		m.energia = 1.0
		f._tick_fluidos(0.5)
		m.tick(0.5)
	igual(int(m.saidas.get("resina", 0)), 2, "duas resinas em 7 s (3 s cada)")
	verificar(float(r_seiva.qtd) < 200.0 and float(r_agua.qtd) < 200.0, "bebeu dos dois canos")
	# pacote químico com a resina feita, bateria e água
	f.escolher_receita(id, "pacote_quimico")
	m.receber("resina")
	m.receber("bateria")
	for i in 26:
		m.energia = 1.0
		f._tick_fluidos(0.5)
		m.tick(0.5)
	igual(int(m.saidas.get("pacote_quimico", 0)), 2, "1 resina + 1 bateria + 20 água → 2 pacotes químicos")


func test_ecologico_so_com_agua_limpa() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("refinador", Vector2i(0, 0), 0)
	var oeste := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_O1", 2)
	f.reconstruir()
	var rede := f.rede_de(c.mapa.tiles[oeste])
	rede.fluido = "agua"
	rede.qtd = 200.0
	f.escolher_receita(id, "pacote_ecologico")
	var m: Maquina = f.maquinas[id]
	for i in 5:
		m.receber("biomassa")
	m.receber("vidro")
	for i in 20:
		m.energia = 1.0
		f._tick_fluidos(0.5)
		m.tick(0.5)
	igual(int(m.saidas.get("pacote_ecologico", 0)), 0, "água do rio não serve (precisa de limpa)")
	rede.fluido = "agua_limpa"
	m.acordar()
	for i in 20:
		m.energia = 1.0
		f._tick_fluidos(0.5)
		m.tick(0.5)
	igual(int(m.saidas.get("pacote_ecologico", 0)), 1, "com água limpa sai o pacote ecológico")
