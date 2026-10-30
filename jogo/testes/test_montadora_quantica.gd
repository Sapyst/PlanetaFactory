extends Caso
## Montadora quântica (montadora_quantica, lote 11): velocidade 2,5, 4 encaixes e 2 receitas ao mesmo tempo (Fabrica.linha2:
## o braço entrega a quem pede o item e tira de qualquer uma). A única que faz o casco de foguete.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("montadora_quantica", {})
	igual(r.get("maquina", ""), "montadora", "receitas da montadora")
	perto(float(r.velocidade), 2.5, 1e-6, "velocidade 2,5 (árvore)")
	igual(int(r.encaixes_modulo), 4, "4 encaixes (árvore)")
	igual(int(r.linhas), 2, "2 receitas")
	UtilLote11.modelo(self, "montadora_quantica", ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_SAI_N1", "PORTA_ITEM_ENT_O1", "PORTA_ITEM_SAI_L1"])


func _fabrica() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("montadora_quantica", o + Vector2i(5, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	return [m, f, id, o + Vector2i(5, 1)]


func test_duas_receitas_ao_mesmo_tempo() -> void:
	var b := _fabrica()
	var f: Fabrica = b[1]
	var id: int = b[2]
	var t: Vector2i = b[3]
	verificar(f.linha2.has(id), "tem a linha 2")
	f.escolher_receita(id, "fio")
	f.escolher_receita(id, "engrenagem", 2)
	igual(f.maquinas[id].receita_id, "fio", "linha 1")
	igual(f.linha2[id].receita_id, "engrenagem", "linha 2")
	var d: Object = f.destino_em(t)
	verificar(d.receber("placa_cobre"), "cobre vai para a linha 1")
	verificar(d.receber("placa_ferro") and d.receber("placa_ferro"), "ferro vai para a linha 2")
	verificar(not d.aceita("pedra"), "o que ninguém pede não entra")
	f.tick(0.05)
	f.tick(0.05)
	verificar(f.trabalhando(id), "trabalhando")
	igual(f.maquinas[id].estado, Maquina.Estado.TRABALHANDO, "linha 1 trabalhando")
	igual(f.linha2[id].estado, Maquina.Estado.TRABALHANDO, "linha 2 trabalhando")
	for i in 20:
		f.tick(0.05)
	igual(int(f.maquinas[id].saidas.get("fio_cobre", 0)), 2, "saíram fios")
	igual(int(f.linha2[id].saidas.get("engrenagem", 0)), 1, "saiu engrenagem")
	var o: Object = f.origem_em(t)
	var tirou := [o.pegar_para_braco(""), o.pegar_para_braco(""), o.pegar_para_braco("")]
	tirou.sort()
	igual(tirou, ["engrenagem", "fio_cobre", "fio_cobre"], "o braço tira das duas")
	o.devolver("engrenagem")
	igual(int(f.linha2[id].saidas.get("engrenagem", 0)), 1, "devolver volta para a linha certa")


func test_salva_a_linha_2() -> void:
	var b := _fabrica()
	var f: Fabrica = b[1]
	var id: int = b[2]
	f.escolher_receita(id, "engrenagem", 2)
	f.destino_em(b[3]).receber("placa_ferro")
	var salvo := f.estado().duplicate(true)
	var g := Fabrica.new(b[0])
	g.restaurar(salvo)
	igual(g.linha2[id].receita_id, "engrenagem", "receita da linha 2 volta")
	igual(int(g.linha2[id].entradas.placa_ferro), 1, "e o que estava dentro")


func test_casco_so_nela() -> void:
	var r: Dictionary = Registro.receitas.casco_foguete
	igual(r.entradas, {"liga_leve": 10.0, "processador_quantico": 2.0}, "casco da árvore")
	perto(float(r.tempo), 30.0, 1e-6, "30 s")
	verificar(Registro.receita_cabe("casco_foguete", "montadora_quantica"), "faz na quântica")
	verificar(not Registro.receita_cabe("casco_foguete", "montadora_3"), "não na montadora 3")
	verificar(not Registro.receita_cabe("casco_foguete", "montadora"), "nem na comum")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "montadora_4", "montadora_quantica")
