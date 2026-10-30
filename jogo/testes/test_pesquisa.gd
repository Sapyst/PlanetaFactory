extends Caso
## Pesquisa por tipo de pacote: custo de cada pesquisa jogável bate com a tabela de balanceamento (arvore.json),
## o laboratório aceita e gasta 1 pacote de cada tipo por unidade, salvos antigos (número) continuam abrindo.


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-6, 22):
		for y in range(-8, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot := 0) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


## Laboratório ligado num gerador com carvão (mesma montagem do test_fabrica).
func _lab_com_energia(p: Pesquisa) -> Array:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	f.pesquisa = p
	var g := _por(c, "gerador", Vector2i(8, 6))
	_por(c, "poste_energia", Vector2i(11, 6))
	_por(c, "poste_energia", Vector2i(17, 3))
	_por(c, "poste_energia", Vector2i(17, -2))
	_por(c, "poste_energia", Vector2i(8, 1))
	_por(c, "poste_energia", Vector2i(2, -1))
	_por(c, "poste_energia", Vector2i(-3, -3))
	var lab := _por(c, "laboratorio", Vector2i(-4, -6))
	f.reconstruir()
	f.combustivel[g] = 200.0
	return [f, lab]


func _rodar(f: Fabrica, s: float) -> void:
	for i in int(s * 30):
		f.tick(1.0 / 30.0)


## Algum pré-requisito (direto ou indireto) ainda é "em breve"?
func _depende_de_em_breve(p: Pesquisa, id: String) -> bool:
	for rq in p.arvore()[id].requer:
		if not p.jogavel(rq) or _depende_de_em_breve(p, rq):
			return true
	return false


func test_custo_bate_com_a_tabela() -> void:
	var p := Pesquisa.new()
	for id in p.pesquisas():
		var a: Dictionary = p.arvore()[id]
		var esperado := {}
		for par in a.pacotes:
			verificar(Pesquisa.TIPOS_PACOTE.has(par[0]), "tipo de pacote conhecido: %s em %s" % [par[0], id])
			esperado[Pesquisa.TIPOS_PACOTE.get(par[0], "")] = int(par[1])
		igual(p.custo(id), esperado, "custo por tipo igual à tabela: " + id)
		perto(float(p.pesquisas()[id].get("tempo", 5)), float(a.tempo), 1e-6, "tempo igual à tabela: " + id)
		for t in p.tipos(id):                    # pacote que ainda não existe: só depois de pesquisa "em breve"
			if not Registro.itens.has(t):
				verificar(_depende_de_em_breve(p, id), "pacote %s de %s não existe e a pesquisa depende de algo em breve" % [t, id])
	igual(p.tipos("defesa"), ["pacote_pesquisa"], "sem 'tipos' = só o básico")
	igual(p.custo_texto("defesa"), "básico × 8", "texto do custo")


func test_lab_gasta_um_de_cada_tipo() -> void:
	var p := Pesquisa.new()
	p._d = Registro.progressao.duplicate(true)                    # pesquisa de dois tipos só para o teste
	p._d.pesquisas["teste_dois"] = {"nome": "Teste", "pacotes": 10, "tempo": 4, "requer": [], "tipos": ["pacote_pesquisa", "pacote_automacao"]}
	var r := _lab_com_energia(p)
	var f: Fabrica = r[0]
	var lab: Dictionary = f.laboratorios[r[1]]
	var no := Fabrica._NoLab.new(f, lab)
	verificar(no.aceita("pacote_pesquisa"), "sem pesquisa, aceita o básico")
	verificar(not no.aceita("pacote_automacao"), "sem pesquisa, não aceita automação")
	verificar(not no.aceita("placa_ferro"), "não aceita o que não é pacote")
	p.escolher("teste_dois")
	igual(p.ativa, "teste_dois", "escolheu pesquisa de dois tipos")
	verificar(no.aceita("pacote_automacao"), "pesquisa ativa pede automação: aceita")
	for i in 5:
		no.receber("pacote_pesquisa")
	_rodar(f, 20.0)
	igual(p.feitos, 0, "só com básico não avança (falta automação)")
	for i in 3:
		no.receber("pacote_automacao")
	_rodar(f, 30.0)
	igual(p.feitos, 3, "3 unidades com 3 de automação")
	igual(int(lab.pacotes.get("pacote_pesquisa", 0)), 2, "gastou 1 básico por unidade")
	igual(int(lab.pacotes.get("pacote_automacao", 0)), 0, "gastou 1 automação por unidade")
	for i in Fabrica.LAB_MAX:
		no.receber("pacote_automacao")
	verificar(not no.aceita("pacote_automacao"), "cheio: %d de cada tipo" % Fabrica.LAB_MAX)


func test_salvo_antigo_com_numero() -> void:
	var p := Pesquisa.new()
	var r := _lab_com_energia(p)
	var f: Fabrica = r[0]
	var antigo := f.estado()
	antigo.laboratorios = {r[1]: {"pacotes": 7, "t": 0.5, "energia": 1.0}}
	f.restaurar(antigo)
	igual(f.laboratorios[r[1]].pacotes, {"pacote_pesquisa": 7}, "número antigo vira pacotes básicos")
	p.restaurar({"livre": false, "concluidas": ["defesa"], "ativa": "logistica", "feitos": 4.0})
	igual(p.feitos, 4, "feitos antigo (número) restaurado")
	p.escolher("aco")
	verificar(f.lab_tem_unidade(f.laboratorios[r[1]]), "básico guardado serve na pesquisa nova")


func test_automacao() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("automacao"), "Automação é jogável")
	igual(p.pesquisas().automacao.requer, ["eletronica"], "Automação depois de Eletrônica")
	var r: Dictionary = Registro.receitas.get("pacote_automacao", {})
	igual(r.get("maquina", ""), "montadora", "pacote de automação sai da montadora")
	igual(r.get("entradas", {}), {"motor": 1.0, "circuito": 2.0}, "1 motor + 2 circuitos")
	igual(r.get("saidas", {}), {"pacote_automacao": 2.0}, "→ 2 pacotes")
	perto(float(r.get("tempo", 0)), 10.0, 1e-6, "10 s")
	igual(Registro.itens.get("pacote_automacao", {}).get("nome", ""), "Pacote de automação", "nome do item")
	verificar(ResourceLoader.exists("res://assets/icones/itens/pacote_automacao.png"), "ícone do item")
	verificar(not p.receita_liberada("pacote_automacao"), "receita travada antes da pesquisa")
	verificar(not p.pacote_liberado("pacote_automacao"), "laboratório não estoca automação antes")
	p.concluidas = {"logistica": true, "eletronica": true, "automacao": true}
	verificar(p.receita_liberada("pacote_automacao"), "Automação libera a receita")
	verificar(p.pacote_liberado("pacote_automacao"), "laboratório aceita o pacote de automação")
	verificar(not p.pacote_liberado("pacote_militar"), "pacote que ainda não existe não entra")
	var r2 := _lab_com_energia(p)
	var f: Fabrica = r2[0]
	verificar(Fabrica._NoLab.new(f, f.laboratorios[r2[1]]).aceita("pacote_automacao"), "laboratório estoca automação sem pesquisa ativa")


func test_pacote_automacao_na_esteira() -> void:
	var d := DesenhoItens.new()
	var mmi := d._instancia("pacote_automacao")
	verificar(mmi != null, "pacote de automação tem malha (a do pacote de pesquisa)")
	if mmi != null:
		var achou := false
		for s in mmi.multimesh.mesh.get_surface_count():
			var m := mmi.multimesh.mesh.surface_get_material(s) as ShaderMaterial
			if m != null and m.resource_name.begins_with("P_Cristal"):
				achou = true
				perto((m.get_shader_parameter("cor") as Color).h, 0.07, 0.02, "líquido âmbar")
		verificar(achou, "tem a parte de cristal tingida")
		var base := d._instancia("pacote_pesquisa")
		for s in base.multimesh.mesh.get_surface_count():
			var m := base.multimesh.mesh.surface_get_material(s) as ShaderMaterial
			if m != null and m.resource_name.begins_with("P_Cristal"):
				verificar(absf((m.get_shader_parameter("cor") as Color).h - 0.07) > 0.1, "o pacote básico continua com a cor dele")
	d.free()


func test_produtividade_de_mineracao() -> void:
	var m := Maquina.new("broca_minerio")
	m.definir_receita("minerar_ferro", Registro.receitas.minerar_ferro)
	m.jazida_restante = 1000
	m.produtividade = 0.1
	var total := 0
	for i in 100 * 60:                              # 100 ciclos de 2 s
		m.tick(1.0 / 30.0)
		while m.pegar_para_braco() != "":
			total += 1
	igual(m.produzidos, 100, "100 ciclos")
	igual(total, 110, "+10%: 110 minérios em 100 ciclos")
	igual(m.jazida_restante, 900, "o extra não gasta a jazida")
	var p := Pesquisa.new()
	perto(p.bonus("produtividade_mineracao"), 0.0, 1e-6, "sem pesquisa, sem extra")
	p.concluidas = {"mineracao_1": true, "mineracao_2": true, "mineracao_3": true}
	perto(p.bonus("produtividade_mineracao"), 0.3, 1e-6, "três níveis: +30%")


## Primeiro tile (perto da origem) onde a peça cabe (broca precisa de jazida embaixo).
func _lugar(c: Construtor, nome: String) -> Vector2i:
	for r in 40:
		for x in range(-r, r + 1):
			for y in range(-r, r + 1):
				if maxi(absi(x), absi(y)) == r and c.mapa.motivo_bloqueio(nome, Vector2i(x, y), 0) == "":
					return Vector2i(x, y)
	return Vector2i(9999, 9999)


func test_melhoria_chega_na_broca_e_no_extrator() -> void:
	var p := Pesquisa.new()
	var c := _c()
	var f := Fabrica.new(c.mapa)
	f.pesquisa = p
	var broca := _por(c, "broca_minerio", _lugar(c, "broca_minerio"))
	var ext := _por(c, "extrator_cristal", Vector2i(14, 4))
	var mont := _por(c, "montadora", _lugar(c, "montadora"))
	f.reconstruir()
	f.tick(1.0 / 30.0)
	perto(f.maquinas[broca].produtividade, 0.0, 1e-6, "sem pesquisa: broca normal")
	p.concluidas = {"mineracao_1": true}
	f.tick(1.0 / 30.0)
	perto(f.maquinas[broca].produtividade, 0.1, 1e-6, "Produtividade de mineração 1 na broca")
	perto(f.maquinas[ext].produtividade, 0.1, 1e-6, "e no extrator")
	perto(f.maquinas[mont].produtividade, 0.0, 1e-6, "montadora não ganha")


func test_velocidade_de_pesquisa_e_dano() -> void:
	var p := Pesquisa.new()
	p.concluidas = {"pesquisa_vel_1": true}
	p.ativa = "aco"
	perto(p.tempo_por_pacote(), 5.0 / 1.2, 1e-6, "+20% de velocidade no laboratório")
	p.concluidas = {"pesquisa_vel_1": true, "pesquisa_vel_2": true, "pesquisa_vel_3": true}
	perto(p.tempo_por_pacote(), 5.0 / 1.9, 1e-6, "três níveis: +90%")
	p.concluidas = {"dano_energia_1": true, "dano_energia_2": true, "dano_energia_3": true, "dano_energia_4": true}
	perto(p.bonus("dano_torre_energia"), 1.0, 1e-6, "dano da torre: 20 + 20 + 30 + 30%")
	p.concluidas = {"cadencia_energia_1": true, "cadencia_energia_2": true}
	perto(p.bonus("cadencia_torre_energia"), 0.4, 1e-6, "cadência +40%")
	perto(p.bonus("economia_tiro_torre"), 0.1, 1e-6, "−10% de energia por tiro")


func test_melhorias_alcancaveis_agora() -> void:
	var p := Pesquisa.new()
	p.concluidas = {"logistica": true, "eletronica": true, "automacao": true, "defesa": true, "dano_energia_1": true}
	for id in ["mineracao_1", "pesquisa_vel_1", "dano_energia_2"]:
		verificar(p.disponivel(id), "dá para pesquisar já: " + id)
	p.concluidas.merge({"mineracao_1": true, "pesquisa_vel_1": true, "dano_energia_2": true})
	for id in ["mineracao_2", "pesquisa_vel_2", "dano_energia_3", "cadencia_energia_1"]:
		verificar(not p.disponivel(id), "espera pacote/pesquisa em breve: " + id)


func test_briquete() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("briquete"), "Briquete é jogável")
	var r: Dictionary = Registro.receitas.get("briquete", {})
	igual(r.get("maquina", ""), "montadora", "briquete sai da montadora")
	igual(r.get("entradas", {}), {"biomassa": 4.0}, "4 biomassa")
	igual(r.get("saidas", {}), {"briquete": 1.0}, "→ 1 briquete")
	perto(Fabrica.valor_combustivel("briquete"), 10.0, 1e-6, "10 MJ")
	verificar(ResourceLoader.exists("res://assets/icones/itens/briquete.png"), "ícone do briquete")
	verificar(not p.receita_liberada("briquete"), "travado antes da pesquisa")
	p.concluidas = {"limpeza": true, "fluidos": true, "reflorestar": true, "briquete": true}
	verificar(p.receita_liberada("briquete"), "pesquisa libera a receita")
	var c := _c()
	var f := Fabrica.new(c.mapa)
	f.pesquisa = p
	var forn := _por(c, "fornalha", _lugar(c, "fornalha"))
	var ger := _por(c, "gerador", _lugar(c, "gerador"))
	f.reconstruir()
	var na_fornalha := Fabrica._NaMaquina.new(f, forn)
	verificar(na_fornalha.aceita("briquete"), "fornalha queima briquete")
	na_fornalha.receber("briquete")
	perto(f.combustivel[forn], 10.0, 1e-6, "fornalha guardou 10 MJ")
	var no_gerador := Fabrica._NoGerador.new(f, ger)
	verificar(no_gerador.aceita("briquete"), "gerador queima briquete")
	no_gerador.receber("briquete")
	perto(f.combustivel[ger], 10.0, 1e-6, "gerador guardou 10 MJ")
	# poluição: mesma fornalha, um minuto queimando briquete × carvão
	var base := float(Registro.estruturas.fornalha.poluicao)
	f.emissao.clear()
	f._emitir(forn, 60.0)
	perto(f.emissao[forn], base * 0.7, 1e-6, "briquete: −30% de poluição")
	f.fator_fogo.erase(forn)
	f.combustivel[forn] = 0.0
	for i in 5:
		f.por_combustivel(forn, "carvao")
	f.por_combustivel(forn, "briquete")
	f.emissao.clear()
	f._emitir(forn, 60.0)
	perto(f.emissao[forn], base * (20.0 + 7.0) / 30.0, 1e-6, "mistura: média pelos MJ (20 MJ de carvão + 10 de briquete)")
	var salvo := f.estado().duplicate(true)
	f.fator_fogo.clear()
	f.restaurar(salvo)
	perto(f.fator_fogo.get(forn, 1.0), 0.9, 1e-6, "salvar guarda a mistura do fogo")


func test_infinitas() -> void:
	var p := Pesquisa.new()
	for id in ["mineracao_infinita", "pesquisa_infinita", "dano_energia_infinito"]:
		verificar(p.jogavel(id) and p.infinita(id), "infinita jogável: " + id)
		igual(p.unidades(id), 500, "nível 1 custa 500: " + id)
	# as infinitas pedem o pacote gênese (em desenvolvimento): o laboratório não as avança de verdade
	verificar(p.em_desenvolvimento("mineracao_infinita"), "infinita espera o pacote gênese: em desenvolvimento")
	p.ativa = "mineracao_infinita"
	p.avancar()
	igual(p.ativa, "", "em desenvolvimento não avança (larga)")
	igual(p.nivel("mineracao_infinita"), 0, "nenhum nível")
	# simula a pesquisa já com o que falta (cópia dos dados: sem pré-requisito, só pacote básico): dois níveis
	p._d = Registro.progressao.duplicate(true)
	p._d.pesquisas.mineracao_infinita.requer = []
	p._d.pesquisas.mineracao_infinita.tipos = ["pacote_pesquisa"]
	p._dev_assin = -1
	p.ativa = "mineracao_infinita"
	for i in 500:
		p.avancar()
	igual(p.nivel("mineracao_infinita"), 1, "500 unidades: nível 1")
	igual(p.ativa, "mineracao_infinita", "continua sozinha no próximo nível")
	verificar(not p.concluidas.has("mineracao_infinita"), "infinita nunca fica concluída")
	igual(p.unidades("mineracao_infinita"), 750, "nível 2 custa × 1,5")
	perto(p.bonus("produtividade_mineracao"), 0.1, 1e-6, "nível 1: +10% de minério")
	var fim := ""
	for i in 750:
		var f := p.avancar()
		if f != "":
			fim = f
	igual(fim, "mineracao_infinita", "avisa o nível concluído")
	igual(p.nivel("mineracao_infinita"), 2, "nível 2")
	igual(p.unidades("mineracao_infinita"), 1125, "nível 3 custa 500 × 1,5²")
	perto(p.bonus("produtividade_mineracao"), 0.2, 1e-6, "+10% por nível")
	p.concluidas = {"mineracao_1": true}
	perto(p.bonus("produtividade_mineracao"), 0.3, 1e-6, "soma com as normais")
	p.niveis["dano_energia_infinito"] = 3
	perto(p.bonus("dano_torre_energia"), 0.3, 1e-6, "dano +10% por nível")
	p.niveis["pesquisa_infinita"] = 2
	p.ativa = "aco"
	perto(p.tempo_por_pacote(), 5.0 / 1.2, 1e-6, "laboratório +10% por nível")
	# salvar guarda o nível; salvo antigo (sem níveis) abre com zero
	var e := p.estado()
	var q := Pesquisa.new()
	q.restaurar(e)
	igual(q.nivel("mineracao_infinita"), 2, "salvo guarda o nível")
	igual(q.nivel("dano_energia_infinito"), 3, "de cada infinita")
	q.restaurar({"livre": false, "concluidas": [], "ativa": "", "feitos": 0})
	igual(q.niveis, {}, "salvo antigo: sem níveis")
	# fábrica refaz a produtividade quando o nível sobe
	var c := _c()
	var f := Fabrica.new(c.mapa)
	f.pesquisa = q
	var broca := _por(c, "broca_minerio", _lugar(c, "broca_minerio"))
	f.reconstruir()
	f.tick(1.0 / 30.0)
	perto(f.maquinas[broca].produtividade, 0.0, 1e-6, "sem nível, sem extra")
	q.niveis["mineracao_infinita"] = 1
	f.tick(1.0 / 30.0)
	perto(f.maquinas[broca].produtividade, 0.1, 1e-6, "nível novo chega na broca")


## Pedido de Sapyst: o que ainda não entrou no jogo fica "em desenvolvimento" — a pesquisa não se escolhe nem se
## conclui; a peça não se constrói fora do modo demonstração (que constrói tudo o que tem modelo).
func test_em_desenvolvimento() -> void:
	var p := Pesquisa.new()
	verificar(p.em_desenvolvimento("escavar_canal"), "em breve (fora do progressao.json): em desenvolvimento")
	verificar(p.em_desenvolvimento("braco_quantico"), "jogável travada pela computação quântica (em breve)")
	verificar(p.em_desenvolvimento("logistica_5"), "logística 5 (pacote quântico não existe)")
	verificar(not p.em_desenvolvimento("logistica"), "logística 2 já é do jogo")
	verificar(p.motivo_desenvolvimento("braco_quantico").contains("quântico"), "motivo: %s" % p.motivo_desenvolvimento("braco_quantico"))
	verificar(p.motivo_desenvolvimento("controle_vento").contains("Turbina eólica alta"), "motivo: %s" % p.motivo_desenvolvimento("controle_vento"))
	verificar(p.motivo_desenvolvimento("logistica").is_empty(), "sem motivo para o que é do jogo")
	# não se inicia: nem com todos os pré-requisitos jogáveis feitos
	p.concluidas = {"braco_empilhador": true, "processador": true}
	verificar(not p.disponivel("braco_quantico"), "não fica disponível")
	p.escolher("braco_quantico")
	igual(p.ativa, "", "escolher não pega")
	p.escolher("escavar_canal")
	igual(p.ativa, "", "nem a em breve")
	# não se conclui: forçada como ativa (salvo antigo), o laboratório não avança e larga
	p.ativa = "braco_quantico"
	var concluiu := ""
	for i in p.unidades("braco_quantico") + 5:
		concluiu += p.avancar()
	igual(concluiu, "", "não conclui")
	verificar(not p.concluidas.has("braco_quantico"), "não ficou concluída")
	igual(p.ativa, "", "largou a pesquisa em desenvolvimento")
	# com a dependência concluída (salvo/teste), deixa de estar em desenvolvimento
	verificar(p.em_desenvolvimento("controle_vento"), "controle de vento espera a turbina alta")
	p.concluidas["turbina_alta"] = true
	verificar(not p.em_desenvolvimento("controle_vento"), "dependência feita: sai de em desenvolvimento")
	# peças
	var q := Pesquisa.new()
	for n in ["braco_quantico", "esteira_quantica", "defletor_vento", "regulador_clima"]:
		verificar(q.peca_em_desenvolvimento(n), "peça em desenvolvimento: " + n)
	for n in ["esteira", "braco", "sensor_varredura", "artilharia", "torre_metralhadora", "estacao_tratamento", "posto_avancado"]:
		verificar(not q.peca_em_desenvolvimento(n), "peça do jogo: " + n)
	verificar(q.peca_em_desenvolvimento("peca_que_nao_existe"), "sem modelo: em desenvolvimento")
	var demo := Pesquisa.new(true)
	verificar(not demo.peca_em_desenvolvimento("braco_quantico"), "demonstração constrói o que tem modelo")
	verificar(demo.peca_em_desenvolvimento("peca_que_nao_existe"), "nem a demonstração constrói sem modelo")
	# construtor: fora da demonstração não põe; na demonstração põe
	var c := _c()
	c.pesquisa = q
	c.cobrar = true
	c.inventario = {"liga_leve": 99, "processador": 99, "cristal_carregado": 99}
	var plano := c.plano_peca("braco_quantico", Vector2i(2, 2), 0)
	verificar(not plano.is_empty() and plano.all(func(it): return it.motivo == "em_desenvolvimento"), "plano marcado em desenvolvimento")
	verificar(not Construtor.pode_tudo(plano), "não constrói")
	var antes := c.mapa.estruturas.size()
	c.executar(plano)
	igual(c.mapa.estruturas.size(), antes, "nada foi posto no mapa")
	var cd := _c()
	cd.pesquisa = demo
	cd.cobrar = false
	var plano_d := cd.plano_peca("braco_quantico", Vector2i(2, 2), 0)
	verificar(Construtor.pode_tudo(plano_d), "na demonstração o braço quântico se constrói (tem modelo)")
	# interface: barra e tela de pesquisa em cinza escuro com o selo
	var barra := BarraConstrucao.new()
	barra.liberado = func(n: String) -> bool: return q.peca_liberada(n)
	barra.em_desenvolvimento = func(n: String) -> bool: return q.peca_em_desenvolvimento(n)
	var bq := barra.botao_peca("braco_quantico", 0)
	verificar(bq.disabled, "barra: braço quântico desligado")
	verificar(bq.get_node_or_null("SeloDesenvolvimento") != null, "barra: selo Em desenvolvimento")
	verificar(bq.text.contains("Braço quântico") and not bq.text.contains("🔒"), "barra: nome sem cadeado (%s)" % bq.text)
	var bb := barra.botao_peca("braco", 1)
	verificar(not bb.disabled and bb.get_node_or_null("SeloDesenvolvimento") == null, "barra: braço comum normal")
	barra._botoes_peca = {"braco_quantico": bq, "braco": bb}
	barra._destacar(bb, true, BarraConstrucao.COR_DESTAQUE)
	for k in barra._botoes_peca:                            # (o mesmo laço de marcar(): o cinza do selo fica)
		if not barra._botoes_peca[k].has_meta("em_desenvolvimento"):
			barra._destacar(barra._botoes_peca[k], false, BarraConstrucao.COR_DESTAQUE)
	verificar(bq.get_theme_stylebox("normal") == bq.get_theme_stylebox("disabled"), "marcar outra peça não tira o cinza")
	for b in [bq, bb]:
		b.free()
	barra.free()
	var tela := TelaPesquisa.new()
	tela.pesquisa = q
	var nb := tela._botao_no("braco_quantico")
	verificar(nb.get_node_or_null("SeloDesenvolvimento") != null, "tela: nó com o selo")
	verificar(not nb.disabled, "tela: o nó ainda abre o detalhe")
	verificar(tela._situacao("braco_quantico").contains("em desenvolvimento"), "tela: situação diz em desenvolvimento")
	var nl := tela._botao_no("logistica")
	verificar(nl.get_node_or_null("SeloDesenvolvimento") == null, "tela: pesquisa do jogo sem selo")
	verificar(tela._situacao("escavar_canal").contains("em desenvolvimento"), "tela: em breve também")
	tela._det = VBoxContainer.new()
	tela._sel = "braco_quantico"
	tela._mostrar_detalhe()
	var botao_det: Button = null
	var rodape := ""
	for ch in tela._det.get_children():
		if ch is Button:
			botao_det = ch
		elif ch is Label:
			rodape += (ch as Label).text + "\n"
	verificar(botao_det != null and botao_det.disabled and botao_det.text == Tema.TEXTO_DESENVOLVIMENTO, "tela: botão Pesquisar vira Em desenvolvimento (desligado)")
	verificar(rodape.contains("Em desenvolvimento: o pacote quântico"), "tela: rodapé diz por quê")
	for x in [nb, nl, tela._det]:
		x.free()
	tela.free()
