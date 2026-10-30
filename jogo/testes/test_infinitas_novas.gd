extends Caso
## Infinitas do lote 11 (balas, foguetes, artilharia, escudo, frota, purificação, eficiência) e a Mente distribuída.


func test_infinitas_da_arvore() -> void:
	var p := Pesquisa.new()
	var bonus := {"dano_bala_infinito": {"dano_bala": 0.1}, "dano_foguete_infinito": {"dano_foguete": 0.1}, "dano_artilharia_infinito": {"dano_artilharia": 0.1},
			"escudo_infinito": {"escudo_carga": 0.15}, "drones_infinito": {"drones_velocidade": 0.1, "velocidade_trens": 0.1},
			"purificacao_infinita": {"limpeza": 0.1}, "eficiencia_infinita": {"reducao_energia": 0.05},
			"mineracao_infinita": {"produtividade_mineracao": 0.1}, "pesquisa_infinita": {"velocidade_pesquisa": 0.1}}
	for id in bonus:
		verificar(p.jogavel(id) and p.infinita(id), "infinita: " + id)
		verificar(not p.em_desenvolvimento(id), "fora do em desenvolvimento: " + id)
		igual(p.pesquisas()[id].bonus, bonus[id], "bônus da árvore: " + id)
		igual(p.unidades(id), 500, "500 no 1º nível")
		igual(p.arvore()[id].tipo, "infinita", "tipo infinita")
	p.niveis["eficiencia_infinita"] = 4
	perto(p.bonus("reducao_energia"), 0.2, 1e-6, "soma por nível")


func test_eficiencia_de_rede_ate_50() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m)
	UtilLote11.energia(m, o)
	var id := m.colocar("montadora", o + Vector2i(5, 1), 0)
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.reconstruir()
	f.tick(0.05)
	perto(f.kw_de(id), 150.0, 1e-3, "150 kW")
	f.pesquisa.niveis["eficiencia_infinita"] = 2
	f.tick(0.05)
	perto(f.kw_de(id), 135.0, 1e-3, "−10%")
	perto(float(f._membros[id].kw), 135.0, 1e-3, "a rede vê o novo consumo")
	f.pesquisa.niveis["eficiencia_infinita"] = 40
	f.tick(0.05)
	perto(f.kw_de(id), 75.0, 1e-3, "no máximo −50%")


func test_limpeza_e_trem() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.pesquisa.niveis["purificacao_infinita"] = 3
	perto(f.bonus_de("limpeza"), 0.3, 1e-6, "o ambiente lê por aqui")
	f.pesquisa.niveis["drones_infinito"] = 2
	perto(f.pesquisa.bonus("velocidade_trens"), 0.2, 1e-6, "trens")
	perto(f.pesquisa.bonus("drones_velocidade"), 0.2, 1e-6, "e drones")


func test_mente_distribuida_junta_as_redes() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var a := UtilLote11.chao(m)
	var n := m.colocar("nucleo", Vector2i(0, 0), 0)
	var col := m.colocar("posto_avancado", a, 0)
	m.estruturas[col]["colonia"] = true
	var maq := m.colocar("montadora", a + Vector2i(5, 0), 0)      # ligada ao posto sem cabo
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.reconstruir()
	f.tick(0.05)
	verificar(f._membros[n].rede != f._membros[col].rede, "sem a pesquisa: redes separadas")
	f.pesquisa.concluidas["rede_colonias"] = true
	f.tick(0.05)
	igual(f._membros[n].rede, f._membros[col].rede, "com a pesquisa: uma rede só, sem obra")
	verificar(maq >= 0, "ok")
	f.reconstruir()
	igual(f._membros[n].rede, f._membros[col].rede, "e continua depois de remontar")


func test_pacote_genese_no_laboratorio() -> void:
	var p := Pesquisa.new()
	verificar(not p.pacote_liberado("pacote_genese"), "antes das colônias, não")
	p.concluidas["colonias"] = true
	verificar(p.pacote_liberado("pacote_genese"), "com as colônias, o laboratório pode estocar")
