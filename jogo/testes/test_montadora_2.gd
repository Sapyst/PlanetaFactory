extends Caso
## Montadora 2 (montadora_2, lote 10 — produção I): modelo do estudo (estudo_montadora_2.py, do Antigravity;
## arte/estudos/conv_lote10.py) com esteira, alimentador, braços, prensa e travas; pesquisa montadora_2 (automação +
## aço; básico/automação × 30, 6 s). Melhoria real da montadora: as mesmas receitas, velocidade 1,0 (a 1 faz 0,75),
## mesmas bocas de item (S1 → N1) e 2 encaixes de módulo (os módulos ainda não existem).


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("montadora_2", {})
	igual(r.get("maquina", ""), "montadora", "faz as receitas da montadora")
	perto(float(r.velocidade), 1.0, 1e-6, "velocidade 1,0 (árvore)")
	verificar(float(r.velocidade) > float(Registro.estruturas.montadora.velocidade), "mais rápida que a montadora")
	igual(int(r.encaixes_modulo), 2, "2 encaixes de módulo (árvore)")
	igual(Fiacao.papel("montadora_2"), "consumo", "precisa de energia")
	var md: Dictionary = Registro.modelos.get("montadora_2", {})
	igual(Registro.area("montadora_2"), Vector2i(3, 3), "3×3 (como a montadora)")
	igual(md.get("estudo", ""), "estudo_montadora_2.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	verificar(float(md.dims[0]) <= 3.15 and float(md.dims[1]) <= 3.15, "quase só a área (%s: a flange do fluido sai 6 cm)" % str(md.dims))
	verificar(int(md.tris) <= 11500, "no nível da montadora (%d triângulos)" % md.tris)
	var bocas := {}
	for p in md.get("portas", []):
		bocas[p.nome] = true
	for n in ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_SAI_N1"]:
		verificar(bocas.has(n), "boca %s, igual à da montadora" % n)
	verificar(bocas.has("PORTA_FLUIDO_ENT_O1"), "boca de fluido a oeste (do estudo)")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/montadora_2.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Produção" and "montadora_2" in cat.pecas), "no menu (Produção)")
	verificar(not Registro.progressao.custos.get("montadora_2", {}).is_empty(), "custo de construção")


func test_mais_rapida() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 10):
		for y in range(-2, 4):
			m.limpar_obstaculo(Vector2i(x, y))
	var a := m.colocar("montadora", Vector2i(0, 0), 0)
	var b := m.colocar("montadora_2", Vector2i(5, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(f.maquinas.has(b), "é máquina de receita")
	for id in [a, b]:
		f.escolher_receita(id, "engrenagem")
	var feitos := {}
	for id in [a, b]:
		var mq: Maquina = f.maquinas[id]
		var n := 0
		for i in 60:
			while mq.receber("placa_ferro"):                 # braço sempre trazendo
				pass
			mq.energia = 1.0
			mq.tick(0.25)
			n += int(mq.saidas.get("engrenagem", 0))     # tira o que ficou pronto (como um braço)
			mq.saidas.erase("engrenagem")
			mq.acordar()
		feitos[id] = n
	verificar(int(feitos[b]) > int(feitos[a]), "em 15 s a montadora 2 fez mais (%d contra %d)" % [feitos[b], feitos[a]])
	var rec_a := Registro.receitas_da_maquina(Registro.estruturas.montadora.maquina)
	var rec_b := Registro.receitas_da_maquina(Registro.estruturas.montadora_2.maquina)
	igual(rec_b, rec_a, "as mesmas receitas")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("montadora_2"), "Montadora 2 ligada no jogo")
	verificar(not p.em_desenvolvimento("montadora_2"), "fora do em desenvolvimento")
	igual(p.custo("montadora_2"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "custo da árvore")
	verificar(not p.peca_liberada("montadora_2"), "começa travada")
	p.concluidas = {"automacao": true}
	verificar(not p.disponivel("montadora_2"), "pede aço")
	p.concluidas["aco"] = true
	verificar(p.disponivel("montadora_2"), "com automação e aço: pesquisável")
	p.concluidas["montadora_2"] = true
	verificar(p.peca_liberada("montadora_2"), "libera a montadora 2")
