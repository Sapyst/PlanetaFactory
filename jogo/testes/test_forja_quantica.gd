extends Caso
## Forja quântica (forja_quantica, lote 11 — produção II): modelo do estudo com martelo, anel de confinamento e carrossel;
## pesquisa computacao_quantica. Faz o processador quântico e o pacote quântico (e, com a navegação, o mapa estelar).


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("forja_quantica", {})
	igual(r.get("maquina", ""), "forja", "máquina própria")
	igual(Fiacao.papel("forja_quantica"), "consumo", "precisa de energia")
	UtilLote11.modelo(self, "forja_quantica", ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_ENT_O1", "PORTA_ITEM_SAI_N1", "PORTA_FLUIDO_ENT_L1"])


func test_receitas_da_arvore() -> void:
	igual(Registro.receitas_da_maquina("forja"), ["processador_quantico", "pacote_quantico", "mapa_estelar"], "as 3 da árvore")
	var q: Dictionary = Registro.receitas.processador_quantico
	igual(q.entradas, {"processador": 2.0, "cristal_carregado": 1.0, "liga_leve": 1.0}, "processador quântico")
	perto(float(q.tempo), 20.0, 1e-6, "20 s")
	var pq: Dictionary = Registro.receitas.pacote_quantico
	igual(pq.entradas, {"processador_quantico": 1.0, "celula_energia": 1.0, "cristal_carregado": 1.0}, "pacote quântico")
	igual(pq.saidas, {"pacote_quantico": 3.0}, "sai 3")
	var me: Dictionary = Registro.receitas.mapa_estelar
	igual(me.entradas, {"processador_quantico": 1.0, "pacote_genese": 5.0}, "mapa estelar")
	var p := Pesquisa.new()
	p.concluidas = {"computacao_quantica": true}
	verificar(p.receita_liberada("processador_quantico") and p.receita_liberada("pacote_quantico"), "liberadas pela computação quântica")
	verificar(not p.receita_liberada("mapa_estelar"), "o mapa estelar vem da navegação")
	p.concluidas["navegacao"] = true
	verificar(p.receita_liberada("mapa_estelar"), "navegação libera o mapa estelar")
	verificar(p.pacote_liberado("pacote_quantico"), "o laboratório pode estocar o pacote quântico")


func test_faz_o_pacote() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	verificar(o.x != 9999, "achou chão")
	UtilLote11.energia(m, o)
	var id := m.colocar("forja_quantica", o + Vector2i(5, 1), 0)
	verificar(id >= 0, "coube")
	var f := Fabrica.new(m)
	f.reconstruir()
	f.escolher_receita(id, "pacote_quantico")
	var d: Object = f.destino_em(o + Vector2i(5, 1))
	verificar(not d.aceita("placa_ferro"), "só o que a receita pede")
	for it in ["processador_quantico", "celula_energia", "cristal_carregado"]:
		verificar(d.receber(it), "recebe " + it)
	for i in 21 * 4:
		f.tick(0.25)
	igual(int(f.maquinas[id].saidas.get("pacote_quantico", 0)), 3, "20 s: 3 pacotes")
	verificar(f.origem_em(o + Vector2i(5, 1)).pegar_para_braco("") == "pacote_quantico", "o braço tira")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "computacao_quantica", "forja_quantica")
