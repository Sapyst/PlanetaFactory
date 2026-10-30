extends Caso
## Módulos (lote 11): itens modulo_{velocidade,eficiencia,produtividade}_{1,2,3} (montadora) que se encaixam pelo painel,
## vindos do estoque do núcleo, nas máquinas e laboratórios com encaixes (fornalha elétrica, fundição, montadora 2/3/
## quântica, refinador 2, laboratório 2/quântico). Mudam velocidade, energia, poluição e produto. Ficam na estrutura.


func test_itens_e_receitas_da_arvore() -> void:
	var ef := {"modulo_velocidade_1": {"velocidade": 0.2, "energia": 0.5}, "modulo_velocidade_2": {"velocidade": 0.3, "energia": 0.5},
			"modulo_velocidade_3": {"velocidade": 0.5, "energia": 0.5},
			"modulo_eficiencia_1": {"energia": -0.3, "poluicao": -0.3}, "modulo_eficiencia_2": {"energia": -0.4, "poluicao": -0.4},
			"modulo_eficiencia_3": {"energia": -0.5, "poluicao": -0.5},
			"modulo_produtividade_1": {"produtividade": 0.04, "velocidade": -0.15, "poluicao": 0.4},
			"modulo_produtividade_2": {"produtividade": 0.06, "velocidade": -0.15, "poluicao": 0.4},
			"modulo_produtividade_3": {"produtividade": 0.10, "velocidade": -0.15, "poluicao": 0.4}}
	for it in ef:
		verificar(Fabrica.eh_modulo(it), "é módulo: " + it)
		igual(Registro.itens[it].modulo, ef[it], "efeito da árvore: " + it)
		verificar(ResourceLoader.exists("res://assets/icones/itens/%s.png" % it), "ícone: " + it)
		igual(Registro.receitas[it].maquina, "montadora", "sai na montadora")
	igual(Registro.receitas.modulo_velocidade_1.entradas, {"processador": 3.0, "circuito": 2.0}, "nível 1")
	igual(Registro.receitas.modulo_eficiencia_2.entradas, {"modulo_eficiencia_1": 3.0, "cristal_carregado": 2.0}, "nível 2")
	igual(Registro.receitas.modulo_produtividade_3.entradas, {"modulo_produtividade_2": 3.0, "processador_quantico": 1.0}, "nível 3")
	var p := Pesquisa.new()
	for t in ["velocidade", "eficiencia", "produtividade"]:
		for n in [1, 2, 3]:
			var id := "modulo_%s_%d" % [t, n]
			verificar(p.jogavel(id) and not p.em_desenvolvimento(id), "pesquisa: " + id)
			verificar(not p.receita_liberada(id), "travado: " + id)
			p.concluidas[id] = true
			verificar(p.receita_liberada(id), "liberado: " + id)


func test_encaixes_previstos() -> void:
	for par in [["fornalha_eletrica", 2], ["fundicao_cristal", 4], ["montadora_2", 2], ["montadora_3", 4], ["montadora_quantica", 4],
			["refinador_2", 3], ["laboratorio_2", 2], ["laboratorio_quantico", 4], ["irradiador_modulos", 2], ["montadora", 0]]:
		igual(Fabrica.encaixes(par[0]), par[1], "encaixes de " + par[0])


func _montadora() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("montadora_2", o + Vector2i(5, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.estoque_nucleo = {"modulo_velocidade_1": 3, "modulo_eficiencia_1": 1, "modulo_produtividade_1": 2}
	f.tick(0.05)
	return [m, f, id, o + Vector2i(5, 1)]


func test_velocidade_energia_e_estoque() -> void:
	var b := _montadora()
	var f: Fabrica = b[1]
	var id: int = b[2]
	perto(f.maquinas[id].velocidade, 1.0, 1e-6, "sem módulo")
	perto(f.kw_de(id), 200.0, 1e-3, "200 kW")
	verificar(f.por_modulo(id, "modulo_velocidade_1"), "encaixa do núcleo")
	igual(int(f.estoque_nucleo.modulo_velocidade_1), 2, "saiu do núcleo")
	f.tick(0.05)
	perto(f.maquinas[id].velocidade, 1.2, 1e-6, "+20%")
	perto(f.kw_de(id), 300.0, 1e-3, "+50% de energia")
	verificar(f.por_modulo(id, "modulo_velocidade_1"), "2º")
	verificar(not f.por_modulo(id, "modulo_velocidade_1"), "2 encaixes na montadora 2")
	igual(int(f.estoque_nucleo.modulo_velocidade_1), 1, "o que não coube fica no núcleo")
	f.tick(0.05)
	perto(f.maquinas[id].velocidade, 1.4, 1e-6, "somam")
	igual(f.tirar_modulo(id, 1), "modulo_velocidade_1", "tira")
	igual(int(f.estoque_nucleo.modulo_velocidade_1), 2, "volta para o núcleo")
	igual(f.tirar_modulo(id, 5), "", "encaixe vazio")
	f.tick(0.05)
	perto(f.maquinas[id].velocidade, 1.2, 1e-6, "um a menos")
	verificar(not f.por_modulo(id, "placa_ferro"), "só módulo")
	f.estoque_nucleo.erase("modulo_eficiencia_1")
	verificar(not f.por_modulo(id, "modulo_eficiencia_1"), "sem no núcleo, não encaixa")
	verificar(f.por_modulo(id, "modulo_eficiencia_1", true), "na demonstração, de graça")


func test_eficiencia_e_poluicao() -> void:
	var b := _montadora()
	var f: Fabrica = b[1]
	var id: int = b[2]
	f.por_modulo(id, "modulo_eficiencia_1")
	f.tick(0.05)
	perto(f.kw_de(id), 140.0, 1e-3, "−30% de energia")
	f.escolher_receita(id, "lapidar")
	var d: Object = f.destino_em(b[3])
	d.receber("cristal_bruto")
	d.receber("cristal_bruto")
	f.tick(0.1)
	var e := float(f.emissao.get(id, 0.0))
	perto(e, 3.0 / 60.0 * 0.1 * 0.7, 1e-6, "−30% de poluição")


func test_produtividade() -> void:
	var b := _montadora()
	var f: Fabrica = b[1]
	var id: int = b[2]
	f.por_modulo(id, "modulo_produtividade_1")
	f.por_modulo(id, "modulo_produtividade_1")
	f.tick(0.05)
	perto(f.maquinas[id].velocidade, 0.7, 1e-6, "−15% cada")
	perto(f.maquinas[id].produtividade, 0.08, 1e-6, "+4% cada")
	f.escolher_receita(id, "lapidar")
	var q: Maquina = f.maquinas[id]
	var saiu := 0
	for k in 100:                                 # 100 ciclos: 8 de graça
		q.entradas["cristal_bruto"] = 2
		q.acordar()
		for i in 60:
			q.tick(0.05)
		saiu += int(q.saidas.get("cristal_lapidado", 0))
		q.saidas.clear()
	verificar(saiu >= 106 and saiu <= 110, "+8%% de produto (%d em 100 ciclos)" % saiu)


func test_laboratorio_com_modulo() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("laboratorio_2", o + Vector2i(5, 1), 0)
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.pesquisa.ativa = "defesa"
	f.reconstruir()
	f.estoque_nucleo = {"modulo_produtividade_3": 2}
	f.por_modulo(id, "modulo_produtividade_3")
	f.por_modulo(id, "modulo_produtividade_3")
	f.laboratorios[id].pacotes = {"pacote_pesquisa": 10}
	f.tick(0.05)
	perto(float(f.efeito_modulos(id).produtividade), 0.2, 1e-6, "2 × 10%")
	f.laboratorios[id]["extra"] = 0.9
	var feitos0 := f.pesquisa.feitos
	f.laboratorios[id].t = 100.0
	f.tick(0.05)
	igual(f.pesquisa.feitos - feitos0, 2, "1 unidade + 1 de graça")
	igual(int(f.laboratorios[id].pacotes.pacote_pesquisa), 9, "gastou 1 pacote só")


func test_salva_e_devolve_ao_remover() -> void:
	var b := _montadora()
	var m: MapaOcupacao = b[0]
	var f: Fabrica = b[1]
	var id: int = b[2]
	f.por_modulo(id, "modulo_velocidade_1")
	igual(m.estruturas[id].modulos, ["modulo_velocidade_1"], "fica na estrutura (vai no salvamento)")
	f.reconstruir()
	f.tick(0.05)
	perto(f.maquinas[id].velocidade, 1.2, 1e-6, "remontar a fábrica não perde")
	var c := Construtor.new(m)
	c.cobrar = true
	c.inventario = {}
	c.executar(c.plano_remocao(b[3], b[3]))
	igual(int(c.inventario.get("modulo_velocidade_1", 0)), 1, "remover a máquina devolve o módulo")
	c.desfazer()
	igual(int(c.inventario.get("modulo_velocidade_1", 0)), 0, "desfazer tira do estoque")
	var volta: int = m.tiles[b[3]]
	igual(m.estruturas[volta].get("modulos", []), ["modulo_velocidade_1"], "e o módulo volta encaixado")
