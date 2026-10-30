extends Caso
## Fundição de cristal (fundicao_cristal, lote 11): as receitas da fornalha, velocidade 4,0, só energia, 4 encaixes de
## módulo e minério de ferro direto em aço (fundir_aco_direto, exclusiva dela).


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("fundicao_cristal", {})
	igual(r.get("maquina", ""), "fornalha", "receitas da fornalha")
	perto(float(r.velocidade), 4.0, 1e-6, "velocidade 4,0 (árvore)")
	igual(int(r.encaixes_modulo), 4, "4 encaixes (árvore)")
	verificar(not r.get("combustivel", false), "sem combustível")
	UtilLote11.modelo(self, "fundicao_cristal", ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_ENT_O1", "PORTA_ITEM_SAI_N1", "PORTA_FLUIDO_ENT_L1"])


func test_minerio_direto_em_aco() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("fundicao_cristal", o + Vector2i(5, 1), 0)
	var fo := m.colocar("fornalha_eletrica", o + Vector2i(9, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	var d: Object = f.destino_em(o + Vector2i(5, 1))
	for i in 5:
		verificar(d.receber("minerio_ferro"), "recebe minério")
	igual(f.maquinas[id].receita_id, "fundir_aco_direto", "minério de ferro vai direto em aço")
	f.destino_em(o + Vector2i(9, 1)).receber("minerio_ferro")
	igual(f.maquinas[fo].receita_id, "fundir_ferro", "na fornalha elétrica, continua placa")
	for i in 4 * 5:                              # 16 s ÷ 4 = 4 s
		f.tick(0.25)
	igual(int(f.maquinas[id].saidas.get("barra_aco", 0)), 1, "4 s: 1 barra (16 s ÷ 4)")
	f.origem_em(o + Vector2i(5, 1)).pegar_para_braco("")
	f.escolher_receita(id, "fundir_ferro")
	igual(f.maquinas[id].receita_id, "fundir_ferro", "no painel dá para escolher placa")
	var c: Object = f.destino_em(o + Vector2i(5, 1))
	verificar(not Registro.receita_cabe("fundir_aco_direto", "fornalha_eletrica"), "a receita é só dela")
	verificar(Registro.receita_cabe("fundir_aco_direto", "fundicao_cristal") and Registro.receita_cabe("fundir_ferro", "fundicao_cristal"), "faz as duas")
	verificar(c.aceita("minerio_ferro"), "aceita pela receita escolhida")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "fundicao_cristal", "fundicao_cristal")
	var p := Pesquisa.new()
	p.concluidas = {"fundicao_cristal": true}
	verificar(p.receita_liberada("fundir_aco_direto"), "libera o aço direto")
