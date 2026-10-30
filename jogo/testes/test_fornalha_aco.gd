extends Caso
## Fornalha de aço (fornalha_aco, lote 10 — produção I): modelo do estudo (estudo_fornalha_aco.py, do Antigravity;
## arte/estudos/conv_lote10.py) com elevador skip, soprador, corrente de lingotes e cristal; pesquisa fornalha_aco
## (aço + automação; 2 pacotes × 30, 6 s). Melhoria real da fornalha: as mesmas receitas (escolhe pelo que chega),
## velocidade 2,0 com o mesmo fogo (metade de combustível por produto) e −25% de poluição por produto.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("fornalha_aco", {})
	igual(r.get("maquina", ""), "fornalha", "faz as receitas da fornalha")
	perto(float(r.velocidade), 2.0, 1e-6, "velocidade 2,0 (árvore)")
	verificar(bool(r.get("combustivel", false)), "queima combustível (árvore)")
	igual(Fiacao.papel("fornalha_aco"), Fiacao.papel("fornalha"), "sem fio, como a fornalha")
	var r1: Dictionary = Registro.estruturas.fornalha
	perto(float(r.poluicao) / float(r.velocidade), 0.75 * float(r1.poluicao) / float(r1.velocidade), 1e-6, "−25% de poluição por produto")
	var md: Dictionary = Registro.modelos.get("fornalha_aco", {})
	igual(Registro.area("fornalha_aco"), Vector2i(2, 2), "2×2 (como a fornalha)")
	igual(md.get("estudo", ""), "estudo_fornalha_aco.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	verificar(float(md.dims[0]) <= 2.1 and float(md.dims[1]) <= 2.1, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 8000, "no nível da fornalha (%d triângulos; o estudo tem 7.484)" % md.tris)
	var bocas := {}
	for p in md.get("portas", []):
		bocas[p.nome] = p
	for n in ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_SAI_N0"]:
		verificar(bocas.has(n), "boca %s (do estudo)" % n)
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/fornalha_aco.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Produção" and "fornalha_aco" in cat.pecas), "no menu (Produção)")
	verificar(not Registro.progressao.custos.get("fornalha_aco", {}).is_empty(), "custo de construção")


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 10):
		for y in range(-2, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


## Destino de braço: o minério escolhe a receita, o carvão vira fogo; em 16 s faz o dobro da fornalha com o mesmo carvão
## e polui 1,5× no total (0,75 por produto).
func test_mais_rapida_mesmo_fogo() -> void:
	var m := _mapa()
	var a := m.colocar("fornalha", Vector2i(0, 0), 0)
	var b := m.colocar("fornalha_aco", Vector2i(4, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	verificar(f.maquinas.has(b) and f.combustivel.has(b), "máquina com estoque de fogo")
	var d: Object = f.destino_em(Vector2i(4, 0))
	verificar(d.aceita("minerio_ferro"), "aceita minério sem receita escolhida")
	verificar(d.aceita("carvao"), "aceita combustível")
	verificar(not d.aceita("engrenagem"), "recusa o que não funde")
	verificar(d.receber("minerio_ferro"), "recebe o minério")
	igual(f.maquinas[b].receita_id, "fundir_ferro", "a receita sai do que chegou")
	f.escolher_receita(a, "fundir_ferro")
	var feitos := {}
	var fogo := {}
	var pol := {}
	for id in [a, b]:
		f.combustivel[id] = 8.0
		var mq: Maquina = f.maquinas[id]
		var n := 0
		for i in 64:
			while mq.receber("minerio_ferro"):
				pass
			f.emissao.clear()
			f.tick(0.25)
			pol[id] = float(pol.get(id, 0.0)) + float(f.emissao.get(id, 0.0))
			n += int(mq.saidas.get("placa_ferro", 0))
			mq.saidas.erase("placa_ferro")
			mq.acordar()
		feitos[id] = n
		fogo[id] = 8.0 - float(f.combustivel[id])
	verificar(int(feitos[b]) >= 2 * int(feitos[a]), "o dobro de placas em 16 s (%d contra %d)" % [feitos[b], feitos[a]])
	perto(float(fogo[b]), float(fogo[a]), 0.2, "o mesmo fogo no mesmo tempo")
	perto(float(pol[b]) / float(feitos[b]), 0.75 * float(pol[a]) / float(feitos[a]), 0.03, "−25% de poluição por produto")


func test_pede_combustivel() -> void:
	var m := _mapa()
	var b := m.colocar("fornalha_aco", Vector2i(0, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	var mq: Maquina = f.maquinas[b]
	f.escolher_receita(b, "fundir_ferro")
	mq.receber("minerio_ferro")
	f.tick(0.5)
	igual(mq.energia, 0.0, "sem carvão não trabalha")
	f.por_combustivel(b, "carvao")
	f.tick(0.5)
	igual(mq.energia, 1.0, "com carvão, sim")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("fornalha_aco"), "Fornalha de aço ligada no jogo")
	verificar(not p.em_desenvolvimento("fornalha_aco"), "fora do em desenvolvimento")
	igual(p.custo("fornalha_aco"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "custo da árvore")
	verificar(not p.peca_liberada("fornalha_aco"), "começa travada")
	p.concluidas = {"automacao": true}
	verificar(not p.disponivel("fornalha_aco"), "pede aço")
	p.concluidas["aco"] = true
	verificar(p.disponivel("fornalha_aco"), "com aço e automação: pesquisável")
	p.concluidas["fornalha_aco"] = true
	verificar(p.peca_liberada("fornalha_aco"), "libera a fornalha de aço")
	verificar(not Pesquisa.new().peca_em_desenvolvimento("fornalha_aco"), "a peça não fica em cinza")
