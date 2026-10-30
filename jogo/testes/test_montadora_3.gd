extends Caso
## Montadora 3 (montadora_3, lote 11): as mesmas receitas da montadora, velocidade 1,5, 4 encaixes de módulo.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("montadora_3", {})
	igual(r.get("maquina", ""), "montadora", "receitas da montadora")
	perto(float(r.velocidade), 1.5, 1e-6, "velocidade 1,5 (árvore)")
	igual(int(r.encaixes_modulo), 4, "4 encaixes (árvore)")
	UtilLote11.modelo(self, "montadora_3", ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_SAI_N1", "PORTA_FLUIDO_ENT_O1"])


func test_monta_mais_rapido() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var a := m.colocar("montadora", o + Vector2i(5, 1), 0)
	var b := m.colocar("montadora_3", o + Vector2i(9, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	for id in [a, b]:
		f.escolher_receita(id, "lapidar")
		var d: Object = f.destino_em(m.estruturas[id].minimo)
		for i in 4:
			d.receber("cristal_bruto")
	var ciclos := {}
	for i in 5:
		f.tick(0.25)
	for id in [a, b]:
		ciclos[id] = f.maquinas[id].progresso + f.maquinas[id].produzidos
	perto(float(ciclos[b]) / float(ciclos[a]), 1.5 / 0.75, 0.05, "2× a montadora (1,5 contra 0,75)")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "montadora_3", "montadora_3")
