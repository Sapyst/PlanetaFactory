extends Caso
## Laboratório 2 (laboratorio_2, lote 10 — produção I): modelo do estudo (estudo_laboratorio_2.py, do Antigravity;
## arte/estudos/conv_lote10.py) com carrossel, braço, gaveta, comporta e anel de força; pesquisa laboratorio_2 (velocidade
## de pesquisa 2 + processador; 3 pacotes × 80, 8 s). Faz o mesmo do laboratório na velocidade 2,0 (soma com as melhorias
## de velocidade de pesquisa), com 2 encaixes de módulo. É ele que a computação quântica pede — ela e o laboratório
## quântico seguem em desenvolvimento até existirem a forja quântica e o pacote quântico.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("laboratorio_2", {})
	igual(r.get("grupo", ""), "laboratorio", "é laboratório")
	perto(float(r.velocidade), 2.0, 1e-6, "2× a velocidade (árvore)")
	igual(int(r.encaixes_modulo), 2, "2 encaixes de módulo (árvore)")
	igual(Fiacao.papel("laboratorio_2"), "consumo", "precisa de energia")
	var md: Dictionary = Registro.modelos.get("laboratorio_2", {})
	igual(Registro.area("laboratorio_2"), Vector2i(3, 3), "3×3 (árvore)")
	igual(md.get("estudo", ""), "estudo_laboratorio_2.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	verificar(float(md.dims[0]) <= 3.1 and float(md.dims[1]) <= 3.1, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 10000, "no nível do laboratório (%d triângulos)" % md.tris)
	var bocas := {}
	for p in md.get("portas", []):
		bocas[p.nome] = p
	for n in ["PORTA_ITEM_ENT_S1", "PORTA_ITEM_ENT_O1", "PORTA_FLUIDO_ENT_L1"]:
		verificar(bocas.has(n), "boca %s (do estudo)" % n)
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/laboratorio_2.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Produção" and "laboratorio_2" in cat.pecas), "no menu (Produção)")
	verificar(not Registro.progressao.custos.get("laboratorio_2", {}).is_empty(), "custo de construção")


func _fabrica(nome: String) -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-4, 14):
		for y in range(-4, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	var ge := m.colocar("gerador", Vector2i(6, 0), 0)
	m.colocar("poste_energia", Vector2i(5, 1), 0)
	var lab := m.colocar(nome, Vector2i(0, 0), 0)
	var f := Fabrica.new(m)
	f.pesquisa = Pesquisa.new()
	f.pesquisa.ativa = "aco"
	f.reconstruir()
	f.combustivel[ge] = 40.0
	return [f, lab]


## "aço": 5 s por pacote. Em 20 s o laboratório gasta 4 pacotes e o laboratório 2, 8.
func test_pesquisa_duas_vezes_mais_rapido() -> void:
	var gastos := {}
	for nome in ["laboratorio", "laboratorio_2"]:
		var par := _fabrica(nome)
		var f: Fabrica = par[0]
		var lab: Dictionary = f.laboratorios[par[1]]
		var d: Object = f.destino_em(Vector2i(0, 0))
		verificar(d != null and d.aceita("pacote_pesquisa"), "%s aceita pacote" % nome)
		for i in 10:
			d.receber("pacote_pesquisa")
		verificar(not f.lab_trabalhando(par[1]) or lab.energia > 0.0, "só trabalha com energia")
		for i in 21 * 10:
			f.tick(0.1)
		verificar(f.lab_trabalhando(par[1]), "%s pesquisando" % nome)
		gastos[nome] = 10 - int(lab.pacotes.get("pacote_pesquisa", 0))
	igual(int(gastos.laboratorio), 4, "laboratório 1: 4 pacotes em 21 s")
	igual(int(gastos.laboratorio_2), 8, "laboratório 2: 8 pacotes em 21 s")


func test_soma_com_melhoria_e_para_sem_energia() -> void:
	var par := _fabrica("laboratorio_2")
	var f: Fabrica = par[0]
	var lab: Dictionary = f.laboratorios[par[1]]
	f.pesquisa.concluidas = {"pesquisa_vel_1": true}      # +20%: 5 / 1,2 s por pacote, ÷ 2 = 2,08 s
	lab.pacotes = {"pacote_pesquisa": 10}
	for i in 10 * 10:
		f.tick(0.1)
	igual(10 - int(lab.pacotes.pacote_pesquisa), 4, "com velocidade 1: 4 pacotes em 10 s")
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 6):
		for y in range(-2, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	var s := m.colocar("laboratorio_2", Vector2i(0, 0), 0)
	var g := Fabrica.new(m)
	g.pesquisa = Pesquisa.new()
	g.pesquisa.ativa = "aco"
	g.reconstruir()
	g.laboratorios[s].pacotes = {"pacote_pesquisa": 10}
	for i in 100:
		g.tick(0.1)
	igual(int(g.laboratorios[s].pacotes.pacote_pesquisa), 10, "sem rede não gasta")
	verificar(not g.lab_trabalhando(s), "nem anima")


## Salvo: o laboratório 2 volta com os pacotes.
func test_salvo() -> void:
	var par := _fabrica("laboratorio_2")
	var f: Fabrica = par[0]
	f.laboratorios[par[1]].pacotes = {"pacote_pesquisa": 7}
	var d: Dictionary = f.estado()
	var g := Fabrica.new(f.mapa)
	g.reconstruir()
	g.restaurar(d)
	igual(int(g.laboratorios[par[1]].pacotes.pacote_pesquisa), 7, "pacotes voltam")


func test_pesquisa_e_arvore() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("laboratorio_2"), "Laboratório 2 ligado no jogo")
	verificar(not p.em_desenvolvimento("laboratorio_2"), "fora do em desenvolvimento")
	igual(p.custo("laboratorio_2"), {"pacote_pesquisa": 80, "pacote_automacao": 80, "pacote_quimico": 80}, "custo da árvore")
	verificar(not p.peca_liberada("laboratorio_2"), "começa travado")
	p.concluidas = {"processador": true}
	verificar(not p.disponivel("laboratorio_2"), "pede a velocidade de pesquisa 2")
	p.concluidas["pesquisa_vel_2"] = true
	verificar(p.disponivel("laboratorio_2"), "com velocidade 2 e processador: pesquisável")
	p.concluidas["laboratorio_2"] = true
	verificar(p.peca_liberada("laboratorio_2"), "libera o laboratório 2")
	var q := Pesquisa.new()
	verificar(not q.peca_em_desenvolvimento("laboratorio_2"), "a peça não fica em cinza")
	verificar(q.em_desenvolvimento("computacao_quantica"), "computação quântica segue em desenvolvimento: falta a forja quântica")
	verificar(q.em_desenvolvimento("laboratorio_3"), "e o laboratório quântico também")
	igual(Registro.arvore.nos.computacao_quantica.requer, ["ciencia_tempestade", "laboratorio_2", "energia"], "a árvore pede o laboratório 2")
