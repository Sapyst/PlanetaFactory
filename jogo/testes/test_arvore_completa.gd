extends Caso
## Lote 11: a árvore fechou. Percorre a árvore inteira como um jogador faria, do zero: uma pesquisa só entra quando os
## pré-requisitos estão feitos e cada pacote que ela gasta tem receita liberada cujas entradas têm fonte. No fim, as 166
## estão feitas, nada fica "Em desenvolvimento", toda peça tem modelo/custo com fonte e o foguete (vitória) tem tudo.

## Itens que vêm de fora das receitas: chão (drops de obstáculos), máquina que recolhe, colônia.
const FONTES_SEM_RECEITA := {"biomassa": "", "residuo": "coletor_lixo_2", "pacote_genese": "colonias"}


## Máquina de receita disponível? `libera` = peças liberadas agora (receita com so_em exige uma das estruturas).
func _tem_maquina(r: String, pecas: Dictionary) -> bool:
	var rec: Dictionary = Registro.receitas[r]
	for nome in Registro.estruturas:
		if Registro.estruturas[nome].get("maquina", "") == rec.get("maquina", "") and pecas.has(nome) and Registro.receita_cabe(r, nome):
			return true
	return false


## Receita que alguma pesquisa (ou o início) libera. As outras são fixas da máquina (bomba, coletor, viveiro…): vêm com ela.
func _listada(p: Pesquisa, r: String) -> bool:
	if r in Registro.progressao.receitas_inicio:
		return true
	for id in p.pesquisas():
		if r in p.pesquisas()[id].get("receitas", []):
			return true
	return false


func _fechar(p: Pesquisa) -> Array:
	var pecas := {}
	for n in Registro.progressao.liberado_inicio:
		pecas[n] = true
	var itens := {}                              # o kit inicial não conta como fonte: tem de haver produção
	var fluidos := {}
	var ordem := []
	while true:
		# peças pelas pesquisas feitas
		for id in p.concluidas:
			for n in p.pesquisas()[id].get("libera", []):
				pecas[n] = true
		# fontes sem receita
		for k in FONTES_SEM_RECEITA:
			var q: String = FONTES_SEM_RECEITA[k]
			if q == "" or pecas.has(q) or p.modo_liberado(q):
				itens[k] = true
		# receitas: fecha o conjunto de itens e fluidos que dá para fazer agora
		var mudou := true
		while mudou:
			mudou = false
			for r in Registro.receitas:
				var rec: Dictionary = Registro.receitas[r]
				if (_listada(p, r) and not p.receita_liberada(r)) or not _tem_maquina(r, pecas):
					continue
				var ok := true
				for i in rec.get("entradas", {}):
					ok = ok and itens.has(i)
				for fl in rec.get("entradas_fluido", {}):
					ok = ok and (fluidos.has(fl) or (fl == "agua" and fluidos.has("agua_limpa")))
				if not ok:
					continue
				for i in rec.get("saidas", {}):
					if not itens.has(i):
						itens[i] = true
						mudou = true
				for fl in rec.get("saidas_fluido", {}):
					if not fluidos.has(fl):
						fluidos[fl] = true
						mudou = true
		# próxima leva de pesquisas
		var leva := []
		for id in p.pesquisas():
			if p.concluidas.has(id):
				continue
			var pode := true
			for rq in p.pesquisas()[id].get("requer", []):
				pode = pode and p.concluidas.has(rq)
			for t in p.tipos(id):
				pode = pode and itens.has(t)
			if pode:
				leva.append(id)
		if leva.is_empty():
			break
		for id in leva:
			p.concluidas[id] = true
			ordem.append(id)
	return [pecas, itens, fluidos, ordem]


func test_percorre_a_arvore_inteira() -> void:
	var p := Pesquisa.new()
	var fim := _fechar(p)
	var pecas: Dictionary = fim[0]
	var itens: Dictionary = fim[1]
	var fluidos: Dictionary = fim[2]
	var presas := []
	for id in p.arvore():
		if not p.concluidas.has(id):
			presas.append(id)
	igual(presas, [], "nenhuma pesquisa presa")
	igual(p.concluidas.size(), 166, "as 166 pesquisas feitas")
	# nenhum item é beco sem saída: toda entrada de receita tem fonte
	for r in Registro.receitas:
		for i in Registro.receitas[r].get("entradas", {}):
			verificar(itens.has(i), "receita %s: %s tem fonte" % [r, i])
		for fl in Registro.receitas[r].get("entradas_fluido", {}):
			verificar(fluidos.has(fl) or (fl == "agua" and fluidos.has("agua_limpa")), "receita %s: %s tem fonte" % [r, fl])
		if Registro.receitas[r].get("maquina", "") in ["montadora", "refinador", "fornalha", "forja"]:
			verificar(_listada(p, r) and p.receita_liberada(r), "receita de escolher %s é liberada por alguma pesquisa" % r)
	# toda peça liberada custa o que dá para fazer
	for nome in pecas:
		for i in Construtor.custo_de(nome):
			verificar(itens.has(i), "custo de %s: %s tem fonte" % [nome, i])


func test_nada_em_desenvolvimento() -> void:
	var p := Pesquisa.new()
	for id in p.arvore():
		verificar(p.jogavel(id), "jogável: " + id)
		verificar(not p.em_desenvolvimento(id), "fora do em desenvolvimento: %s (%s)" % [id, p.motivo_desenvolvimento(id)])
		verificar(p.arvore()[id].get("existente", false), "existente na árvore: " + id)
		for t in p.tipos(id):
			verificar(Registro.itens.has(t), "pacote existe: " + t)
	igual(p.arvore().size(), 166, "166 nós")
	for cat in Registro.menu.categorias:
		for nome in cat.pecas:
			verificar(not p.peca_em_desenvolvimento(nome), "peça fora do em desenvolvimento: " + nome)
	for t in Pesquisa.TIPOS_PACOTE.values():
		verificar(Registro.itens.has(t), "pacote: " + t)
		verificar(ResourceLoader.exists("res://assets/icones/itens/%s.png" % t), "ícone do pacote: " + t)


## O que a dona pediu para conferir: tudo isto fica alcançável.
func test_destravou() -> void:
	var p := Pesquisa.new()
	var fim := _fechar(p)
	var ordem: Array = fim[3]
	for id in ["computacao_quantica", "fusao", "singularidade", "braco_quantico", "logistica_5", "transportador_quantico", "controle_clima",
			"casco_foguete", "propulsao_cristal", "navegacao", "silo_lancamento", "foguete_proliferacao",
			"mineracao_infinita", "pesquisa_infinita", "dano_bala_infinito", "eficiencia_infinita"]:
		verificar(id in ordem, "alcançável: " + id)
	for n in ["reator_fusao", "nucleo_singularidade", "braco_quantico", "esteira_quantica", "transportador_quantico", "regulador_clima", "silo_lancamento", "forja_quantica"]:
		verificar(p.peca_liberada(n), "peça alcançável: " + n)


## Vitória no modo novo: tudo que o silo pede tem fonte; o propelente chega pelo cano.
func test_vitoria_alcancavel() -> void:
	var p := Pesquisa.new()
	var fim := _fechar(p)
	var itens: Dictionary = fim[1]
	var r := SiloLancamento.regra("silo_lancamento")
	for k in r.parte:
		verificar(itens.has(k), "parte: " + k)
	for k in r.carga:
		verificar(itens.has(k), "carga: " + k)
	for fl in r.parte_fluido:
		verificar(fim[2].has(fl), "fluido da parte: " + fl)
		verificar(Registro.fluidos.has(fl), "fluido existe: " + fl)
	verificar(p.modo_liberado("carga_semente"), "a pesquisa libera a carga-semente")


func test_cano_enche_o_silo_e_lanca() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("silo_lancamento", o + Vector2i(5, 1), 0)
	var e: Dictionary = m.estruturas[id]
	var boca := Grade.porta_no_mundo(Registro.modelos.silo_lancamento.portas.filter(func(q): return q.tipo == "FLUIDO")[0], e.minimo, e.area, e.rot)
	var c := Construtor.new(m)
	c.executar(c.plano_linha("cano", boca.tile_fora, boca.tile_fora + boca.dir * 2, 0))
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(f.silo_no_cano(id), "cano na boca leste")
	var cano: int = m.tiles[boca.tile_fora]
	f.rede_de(cano).fluido = "agua"
	f.rede_de(cano).qtd = 100.0
	f.tick(0.05)
	perto(float(e.get("propelente", 0.0)), 0.0, 1e-6, "água não entra")
	f.rede_de(cano).fluido = "propelente_cristal"
	f.rede_de(cano).qtd = 300.0
	f.tick(0.05)
	perto(float(e.propelente), 300.0, 1e-6, "propelente entra")
	var s := SiloLancamento.new(m)
	s.energia = f.energia
	s.carga_liberada = func() -> bool: return true
	s.itens(id).merge({"casco_foguete": 1, "processador_quantico": 5, "nucleo_semente": 1, "mapa_estelar": 1, "modulo_produtividade_3": 10})
	f.tick(0.05)
	for i in 12:
		s.tick(1.0)
	igual(s.partes(id), 1, "montou uma parte com o propelente do cano")
	e["partes"] = 100
	for i in 32:
		s.tick(1.0)
	verificar(s.pronto(id), "foguete pronto")
	verificar(s.lancar(id), "lança")
	for i in 8:
		s.tick(1.0)
	igual(s.eventos.filter(func(ev): return ev.tipo == "foguete_lancado").size(), 1, "fim da campanha")


func test_propelente_no_refinador_2() -> void:
	var r: Dictionary = Registro.receitas.propelente_cristal
	igual(r.entradas, {"cristal_carregado": 1.0}, "cristal por braço")
	igual(r.entradas_fluido, {"combustivel_seiva": 50.0}, "combustível pelo cano")
	igual(r.saidas_fluido, {"propelente_cristal": 50.0}, "sai 50")
	verificar(Registro.receita_cabe("propelente_cristal", "refinador_2") and not Registro.receita_cabe("propelente_cristal", "refinador"), "só no refinador 2")
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("refinador_2", o + Vector2i(5, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.escolher_receita(id, "propelente_cristal")
	var q: Maquina = f.maquinas[id]
	q.fluidos["combustivel_seiva"] = 50.0
	f.destino_em(o + Vector2i(5, 1)).receber("cristal_carregado")
	for i in 22:
		f.tick(0.25)
	perto(float(q.fluidos.get("propelente_cristal", 0.0)), 50.0, 1e-6, "10 s ÷ 2: 50 de propelente (espera o cano)")


## Toda a interface aguenta o que entrou: detalhe de cada pesquisa, botão de cada peça, modelo de cada item.
func test_interface_de_tudo() -> void:
	var p := Pesquisa.new()
	var tela := TelaPesquisa.new()
	tela.pesquisa = p
	for id in p.arvore():
		tela._det = VBoxContainer.new()
		tela._sel = id
		tela._mostrar_detalhe()
		verificar(tela._det.get_child_count() > 0, "detalhe de " + id)
		var txt := ""
		for ch in tela._det.get_children():
			if ch is Button:
				txt = (ch as Button).text
		verificar(not txt.contains(Tema.TEXTO_DESENVOLVIMENTO), "sem o selo no detalhe: " + id)
		tela._det.free()
		var nb := tela._botao_no(id)
		verificar(nb.get_node_or_null("SeloDesenvolvimento") == null, "nó sem o selo: " + id)
		nb.free()
	tela.free()
	var barra := BarraConstrucao.new()
	barra.liberado = func(n: String) -> bool: return p.peca_liberada(n)
	barra.em_desenvolvimento = func(n: String) -> bool: return p.peca_em_desenvolvimento(n)
	for nome in ["forja_quantica", "fundicao_cristal", "montadora_3", "montadora_quantica", "extrator_ressonante", "broca_nucleo", "laboratorio_quantico", "irradiador_modulos"]:
		var b := barra.botao_peca(nome, 0)
		verificar(b.get_node_or_null("SeloDesenvolvimento") == null, "peça sem o selo: " + nome)
		b.free()
	barra.free()
	for it in Registro.itens:
		var info: Dictionary = Registro.itens[it]
		verificar(Registro.modelos.has(info.get("modelo_de", it)), "item com modelo na esteira: " + it)
		verificar(ResourceLoader.exists("res://assets/icones/itens/%s.png" % it), "ícone do item: " + it)
