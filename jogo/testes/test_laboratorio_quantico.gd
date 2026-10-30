extends Caso
## Laboratório quântico (laboratorio_quantico, lote 11): 4× a velocidade, 4 encaixes de módulo; os mesmos pacotes.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("laboratorio_quantico", {})
	igual(r.get("grupo", ""), "laboratorio", "é laboratório")
	perto(float(r.velocidade), 4.0, 1e-6, "4× (árvore)")
	igual(int(r.encaixes_modulo), 4, "4 encaixes (árvore)")
	igual(Fiacao.papel("laboratorio_quantico"), "consumo", "precisa de energia")
	UtilLote11.modelo(self, "laboratorio_quantico", ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_ENT_O1", "PORTA_FLUIDO_ENT_L1"])


func test_pesquisa_4x() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var a := m.colocar("laboratorio", o + Vector2i(5, 1), 0)
	var b := m.colocar("laboratorio_quantico", o + Vector2i(9, 1), 0)
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.pesquisa.ativa = "defesa"
	f.reconstruir()
	verificar(f.laboratorios.has(a) and f.laboratorios.has(b), "os dois são laboratórios")
	f.laboratorios[a].pacotes = {"pacote_pesquisa": 10}
	f.laboratorios[b].pacotes = {"pacote_pesquisa": 10}
	var tempo: float = f.pesquisa.tempo_por_pacote()
	for i in int(tempo * 2.0 / 0.05):
		f.tick(0.05)
		f.tick(0.0)
	verificar(int(f.laboratorios[b].pacotes.pacote_pesquisa) <= 10 - 7, "quântico gasta 4× (%d)" % f.laboratorios[b].pacotes.pacote_pesquisa)
	verificar(int(f.laboratorios[a].pacotes.pacote_pesquisa) >= 10 - 2, "o comum gasta 1× (%d)" % f.laboratorios[a].pacotes.pacote_pesquisa)
	f.pesquisa.ativa = "logistica"
	f.pesquisa.feitos = 0
	f.laboratorios[b].pacotes = {"pacote_pesquisa": 5}
	verificar(f.lab_trabalhando(b), "pesquisando")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "laboratorio_3", "laboratorio_quantico")
