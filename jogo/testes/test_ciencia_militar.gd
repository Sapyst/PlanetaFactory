extends Caso
## Ciência militar (fase 2.4): pesquisa ciencia_militar (metralhadora + muro de tijolo + automação; básico × 40 +
## automação × 40) libera o pacote militar (2 munições + 1 barra de aço + 2 tijolos → 2 na montadora, 10 s). Com ele
## existindo, as melhorias já ligadas que o pedem passam a ser pesquisáveis: dano de energia 3, cadência de energia 1,
## dano de bala 3 e cadência de bala 2 (dano de energia 4 e cadência de energia 2 esperam a ciência de tempestade).


func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


func test_item_e_receita() -> void:
	verificar(Registro.itens.has("pacote_militar"), "item pacote_militar")
	igual(Registro.itens.pacote_militar.nome, "Pacote militar")
	verificar(ResourceLoader.exists("res://assets/icones/itens/pacote_militar.png"), "ícone do pacote militar")
	verificar(Registro.modelos.has(Registro.itens.pacote_militar.get("modelo_de", "")), "modelo (derivado) na esteira")
	var r: Dictionary = Registro.receitas.pacote_militar
	igual(r.maquina, "montadora", "na montadora (árvore)")
	igual(_int(r.entradas), {"municao": 2, "barra_aco": 1, "tijolo": 2}, "2 munições + 1 aço + 2 tijolos")
	igual(_int(r.saidas), {"pacote_militar": 2}, "→ 2")
	perto(float(r.tempo), 10.0, 1e-6, "10 s")
	igual(Pesquisa.TIPOS_PACOTE.militar, "pacote_militar", "tipo 'militar' da árvore")


func test_pesquisa_pela_arvore() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("ciencia_militar"), "jogável")
	igual(p.arvore().ciencia_militar.get("existente", false), true, "marcada como existente na árvore")
	p.concluidas = {"defesa": true, "aco": true, "torre_metralhadora": true, "logistica": true, "eletronica": true}
	verificar(not p.disponivel("ciencia_militar"), "precisa do muro de tijolo e da automação")
	p.concluidas.merge({"muros_reforcados": true, "automacao": true})
	verificar(p.disponivel("ciencia_militar"), "metralhadora + muro de tijolo + automação")
	igual(p.custo("ciencia_militar"), {"pacote_pesquisa": 40, "pacote_automacao": 40}, "básico × 40 + automação × 40")
	verificar(not p.pacote_liberado("pacote_militar"), "laboratório ainda não estoca o militar")
	verificar(not p.receita_liberada("pacote_militar"), "receita travada antes")
	p.concluidas["ciencia_militar"] = true
	verificar(p.receita_liberada("pacote_militar"), "libera a receita do pacote militar")
	verificar(p.pacote_liberado("pacote_militar"), "laboratório aceita o pacote militar")


func test_melhorias_destravadas() -> void:
	var p := Pesquisa.new()
	p.concluidas = {"defesa": true, "aco": true, "logistica": true, "eletronica": true, "automacao": true,
			"dano_energia_1": true, "dano_energia_2": true, "torre_metralhadora": true, "muros_reforcados": true,
			"dano_bala_1": true, "dano_bala_2": true, "cadencia_bala_1": true}
	for id in ["dano_energia_3", "cadencia_energia_1", "dano_bala_3", "cadencia_bala_2"]:
		verificar(p.jogavel(id), "jogável: " + id)
		verificar(not p.disponivel(id), "%s espera a ciência militar" % id)
	p.concluidas["ciencia_militar"] = true
	for id in ["dano_energia_3", "cadencia_energia_1", "dano_bala_3", "cadencia_bala_2"]:
		verificar(p.disponivel(id), "pesquisável com o pacote militar: " + id)
		verificar("pacote_militar" in p.tipos(id), "%s gasta pacote militar" % id)
	igual(p.custo("dano_energia_3"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_militar": 60}, "dano de energia 3 (árvore)")
	igual(p.custo("cadencia_energia_1"), {"pacote_pesquisa": 50, "pacote_automacao": 50, "pacote_militar": 50}, "cadência de energia 1 (árvore)")
	igual(p.custo("dano_bala_3"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_militar": 60}, "dano de bala 3 (árvore)")
	# os bônus somam
	p.concluidas.merge({"dano_energia_3": true, "cadencia_energia_1": true, "dano_bala_3": true, "cadencia_bala_2": true})
	perto(p.bonus("dano_torre_energia"), 0.7, 1e-6, "energia: +20% +20% +30%")
	perto(p.bonus("cadencia_torre_energia"), 0.2, 1e-6, "cadência de energia 1: +20%")
	perto(p.bonus("economia_tiro_torre"), 0.1, 1e-6, "−10% de energia por tiro")
	perto(p.bonus("dano_bala"), 0.45, 1e-6, "bala: +10% +15% +20%")
	perto(p.bonus("cadencia_bala"), 0.3, 1e-6, "metralhadora: +10% +20%")
	# 4 e cadência 2 seguem travadas: pedem o pacote de tempestade (fase 2.5)
	for id in ["dano_energia_4", "cadencia_energia_2"]:
		verificar(p.jogavel(id), "%s ligada" % id)
		verificar(not p.disponivel(id), "%s espera a ciência de tempestade" % id)


func test_cadencia_energia_na_torre() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 20):
		for y in range(-4, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	m.colocar("torre_defesa", Vector2i(0, 0), 0)
	c._criar_ninho(Vector2i(14, 0), 1.0)
	var gasto := [0.0]
	c.torre_energia = func(_id: int, mj: float) -> bool:
		gasto[0] += mj
		return true
	c.bonus = func(k: String) -> float: return {"cadencia_torre_energia": 0.2, "economia_tiro_torre": 0.1}.get(k, 0.0)
	var n := 0
	for i in 30 * 5:
		c.tick(1.0 / 30.0, [])
		for e in c.eventos:
			if e.tipo == "tiro":
				n += 1
	verificar(n >= 17 and n <= 19, "3 tiros/s × 1,2 = 3,6/s (%d em 5 s)" % n)
	perto(gasto[0] / n, 0.045, 1e-6, "cada tiro gasta 10% menos energia")


func test_montadora_faz_pacote() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 6):
		for y in range(-4, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	var f := Fabrica.new(m)
	var id := m.colocar("montadora", Vector2i(0, 0), 0)
	f.reconstruir()
	f.escolher_receita(id, "pacote_militar")
	var mq: Maquina = f.maquinas[id]
	for it in ["municao", "municao", "barra_aco", "tijolo", "tijolo"]:
		verificar(mq.receber(it), "aceita " + it)
	for i in 30:
		mq.energia = 1.0
		mq.tick(0.5)
	igual(int(mq.saidas.get("pacote_militar", 0)), 2, "2 munições + 1 aço + 2 tijolos → 2 pacotes militares")
