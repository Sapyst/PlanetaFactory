extends Caso
## Broca grande (broca_grande, lote 10 — produção I): modelo do estudo (estudo_broca_grande.py, do Antigravity;
## arte/estudos/conv_lote10.py) com trado, pistões, ventoinhas e pedras na esteira; pesquisa broca_grande (mineração 1 +
## liga leve; 3 pacotes × 50, 8 s). Melhoria real da broca: as mesmas jazidas, 2,5× mais rápida, −20% de poluição por
## minério, produtividade de mineração vale, despeja direto na esteira pela saída sul. A broca de núcleo segue depois.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("broca_grande", {})
	var r1: Dictionary = Registro.estruturas.broca_minerio
	igual(r.get("maquina", ""), "broca", "minera como a broca")
	igual(r.get("requer_jazida", []), r1.requer_jazida, "as mesmas jazidas")
	perto(float(r.velocidade) / float(r1.velocidade), 2.5, 1e-6, "2,5× mais rápida (árvore)")
	perto(float(r.poluicao) / float(r.velocidade), 0.8 * float(r1.poluicao) / float(r1.velocidade), 1e-6, "−20% de poluição por minério")
	igual(Fiacao.papel("broca_grande"), "consumo", "precisa de energia")
	var md: Dictionary = Registro.modelos.get("broca_grande", {})
	igual(Registro.area("broca_grande"), Vector2i(3, 3), "3×3 (árvore)")
	igual(md.get("estudo", ""), "estudo_broca_grande.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	verificar(float(md.dims[0]) <= 3.1 and float(md.dims[1]) <= 3.1, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 8500, "no nível da broca (%d triângulos; o estudo tem 8.392)" % md.tris)
	var bocas := {}
	for p in md.get("portas", []):
		bocas[p.nome] = p
	for n in ["PORTA_ITEM_SAI_S1", "PORTA_FLUIDO_ENT_O1"]:
		verificar(bocas.has(n), "boca %s (do estudo)" % n)
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/broca_grande.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Produção" and "broca_grande" in cat.pecas), "no menu (Produção)")
	verificar(not Registro.progressao.custos.get("broca_grande", {}).is_empty(), "custo de construção")


## Canto mínimo de uma área 3×3 sobre jazida, com o sul livre para a esteira e chão para gerador e poste perto.
func _lugar(m: MapaOcupacao) -> Vector2i:
	for r in range(5, 400):
		for k in 48:
			var t := Vector2i((Vector2.from_angle(k * TAU / 48.0) * r).round())
			var j := m.gerador.distribuicao.jazida(t + Vector2i(1, 1))
			if j.is_empty() or not j.tipo in Registro.estruturas.broca_grande.requer_jazida:
				continue
			for x in range(-8, 12):
				for y in range(-8, 8):
					m.limpar_obstaculo(t + Vector2i(x, y))
			if m.motivo_bloqueio("broca_grande", t, 0) == "":
				return t
	return Vector2i(9999, 0)


func test_exige_jazida() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var fora := Vector2i(9999, 0)
	for r in range(5, 200):
		var t := Vector2i(r, 0)
		var limpo := true
		for x in 3:
			for y in 3:
				limpo = limpo and m.gerador.distribuicao.jazida(t + Vector2i(x, y)).is_empty() and m.gerador.terreno(t + Vector2i(x, y)) == GeradorMundo.Terreno.TERRA
		if limpo:
			fora = t
			break
	verificar(fora.x != 9999, "achou chão sem jazida")
	for x in 3:
		for y in 3:
			m.limpar_obstaculo(fora + Vector2i(x, y))
	igual(m.motivo_bloqueio("broca_grande", fora, 0), "sem_jazida", "sem jazida embaixo não vai")


## Sobre a jazida, com energia: despeja na esteira da saída sul sem braço, 2,5× mais que a broca, com a produtividade.
func test_minera_e_despeja() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := _lugar(m)
	verificar(o.x != 9999, "achou jazida")
	var c := Construtor.new(m)
	var f := Fabrica.new(m)
	var b := m.colocar("broca_grande", o, 0)
	verificar(b >= 0, "colocou na jazida")
	var e: Dictionary = m.estruturas[b]
	var saida := Vector2i(9999, 0)
	for pt in Registro.modelos.broca_grande.portas:
		if pt.tipo == "ITEM":
			var pm := Grade.porta_no_mundo(pt, e.minimo, e.area, e.rot)
			saida = pm.tile_fora
			c.executar(c.plano_linha("esteira", pm.tile_fora, pm.tile_fora + pm.dir * 3, Construtor.rot_do_fluxo(Grade.DIRECOES.find(pm.dir))))
	var ge := m.colocar("gerador", o + Vector2i(5, 0), 0)
	m.colocar("poste_energia", o + Vector2i(4, 1), 0)
	f.reconstruir()
	f.combustivel[ge] = 40.0
	var mq: Maquina = f.maquinas[b]
	verificar(mq.receita_id.begins_with("minerar_"), "a receita sai da jazida embaixo (%s)" % mq.receita_id)
	perto(mq.velocidade, 1.25, 1e-6, "velocidade da máquina")
	var item: String = Registro.receitas[mq.receita_id].saidas.keys()[0]
	var est: EsteiraCaminho = f.caminhos[0].esteira
	var poluiu := 0.0
	for i in 40:                                 # 10 s: ciclos de 1,2 a 2 s conforme a jazida
		f.tick(0.25)
		poluiu += float(f.emissao.get(b, 0.0))
	verificar(est.itens.size() > 0, "o %s foi para a esteira sem braço" % item)
	verificar(poluiu > 0.0, "trabalhando, polui")
	verificar(f.kw_de(b) > 0.0, "puxa energia")


func test_mais_rapida_com_produtividade() -> void:
	var a := Maquina.new("broca_minerio", float(Registro.estruturas.broca_minerio.velocidade))
	var b := Maquina.new("broca_grande", float(Registro.estruturas.broca_grande.velocidade))
	var feitos := {}
	for q in [a, b]:
		q.definir_receita("minerar_ferro", Registro.receitas.minerar_ferro)
		q.energia = 1.0
		var n := 0
		for i in 800:
			q.tick(0.05)
			n += int(q.saidas.get("minerio_ferro", 0))
			q.saidas.erase("minerio_ferro")
			q.acordar()
		feitos[q] = n
	verificar(float(feitos[b]) / float(feitos[a]) >= 2.4, "em 40 s: %d contra %d" % [feitos[b], feitos[a]])
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := _lugar(m)
	var id := m.colocar("broca_grande", o, 0)
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.pesquisa.concluidas = {"mineracao_1": true}
	f.reconstruir()
	f.tick(0.1)
	perto(f.maquinas[id].produtividade, 0.1, 1e-6, "a produtividade de mineração vale nela")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("broca_grande"), "Broca grande ligada no jogo")
	verificar(not p.em_desenvolvimento("broca_grande"), "fora do em desenvolvimento")
	igual(p.custo("broca_grande"), {"pacote_pesquisa": 50, "pacote_automacao": 50, "pacote_quimico": 50}, "custo da árvore")
	verificar(not p.peca_liberada("broca_grande"), "começa travada")
	p.concluidas = {"mineracao_1": true}
	verificar(not p.disponivel("broca_grande"), "pede a liga leve")
	p.concluidas["liga_leve"] = true
	verificar(p.disponivel("broca_grande"), "com mineração 1 e liga leve: pesquisável")
	p.concluidas["broca_grande"] = true
	verificar(p.peca_liberada("broca_grande"), "libera a broca grande")
	verificar(not Pesquisa.new().peca_em_desenvolvimento("broca_grande"), "a peça não fica em cinza")
