extends Caso
## Vagão-tanque (pesquisa vagao_tanque): trem-tanque (locomotiva + 2 vagões-tanque + locomotiva, 25.000 de fluido por
## vagão). Cano com a boca virada para a estação liga o tanque dela (25.000) à rede: "carregar" puxa da rede e o
## trem enche ao parar; "descarregar" esvazia o trem (fluido de outra estação) no tanque, que solta na rede a
## 1.000/s; "desligado" não mexe. Como o vagão de carga faz com itens (Trem.trocar_carga).

func _tanque() -> Array[String]:
	var c: Array[String] = ["locomotiva", "vagao_tanque", "vagao_tanque", "locomotiva"]
	return c


func _por(c: Construtor, nome: String, t: Vector2i, rot: int) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


## Linha norte–sul (como test_trens._linha) com estação A (y 8..10) e B (y −12..−10) a leste; cada estação com
## um cano reto encostado no leste e um tanque atrás dele.
func _linha() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 9):
		for y in range(-18, 19):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	_por(c, "trilho_fim", Vector2i(0, -16), 2)
	for y in range(-15, 16):
		_por(c, "trilho_reto", Vector2i(0, y), 0)
	_por(c, "trilho_fim", Vector2i(0, 16), 0)
	_por(c, "estacao", Vector2i(1, 8), 0)
	_por(c, "estacao", Vector2i(1, -12), 0)
	var leste := Construtor.rot_do_fluxo(1)
	_por(c, "cano_reto", Vector2i(3, 9), leste)
	_por(c, "tanque", Vector2i(4, 9), 0)
	_por(c, "cano_reto", Vector2i(3, -12), leste)
	_por(c, "tanque", Vector2i(4, -12), 0)
	return c


func _rodar(f: Fabrica, g: GrafoTrilhos, trens: Array[Trem], segundos: float) -> int:
	var chegadas := 0
	var dt := 1.0 / 30.0
	for i in int(segundos / dt):
		f.tick(dt)
		for t in trens:
			t.tick(dt)
			if t.chegada >= 0:
				if f.estoques.has(t.chegada):
					t.trocar_carga(f.estoques[t.chegada], t.chegada)
				chegadas += 1
				t.chegada = -1
	return chegadas


func _montar() -> Dictionary:
	var c := _linha()
	var g := GrafoTrilhos.de_mapa(c.mapa)
	var f := Fabrica.new(c.mapa)
	var est := {}
	for e in g.estacoes:
		est[e.estrutura] = {"enviar": {}, "recebido": {}}
		Fabrica.tanque_estacao(est[e.estrutura])
	f.estoques = est
	f.reconstruir()
	var a: int = c.mapa.tiles[Vector2i(1, 8)]
	var b: int = c.mapa.tiles[Vector2i(1, -12)]
	return {"c": c, "g": g, "f": f, "a": a, "b": b, "ra": f.rede_de(c.mapa.tiles[Vector2i(3, 9)]),
			"rb": f.rede_de(c.mapa.tiles[Vector2i(3, -12)])}


func _total(m: Dictionary, trens: Array[Trem]) -> float:
	var n: float = float(m.ra.qtd) + float(m.rb.qtd) + float(m.f.estoques[m.a].fluido.qtd) + float(m.f.estoques[m.b].fluido.qtd)
	for t in trens:
		n += t.fluido_qtd
	return n


func test_dados() -> void:
	verificar(Registro.modelos.has("vagao_tanque"), "modelo do vagão-tanque (estudo_trem)")
	igual(Trem.COMPOSICOES.trem_tanque, ["locomotiva", "vagao_tanque", "vagao_tanque", "locomotiva"])
	var t := Trem.new(1, GrafoTrilhos.new(), _tanque())
	perto(t.capacidade_fluido(), 50000.0, 1e-6, "2 vagões × 25.000 (árvore)")
	igual(t.capacidade(), 0, "trem-tanque não leva itens")
	igual(t.peca(), "trem_tanque")
	var carga: Array[String] = ["locomotiva", "vagao_carga", "vagao_carga", "locomotiva"]
	var tc := Trem.new(2, GrafoTrilhos.new(), carga)
	igual(tc.peca(), "trem")
	perto(tc.capacidade_fluido(), 0.0, 1e-6, "trem de carga não leva fluido")
	verificar(Registro.menu.categorias.any(func(cat): return "trem_tanque" in cat.pecas), "trem-tanque no menu")
	verificar(Registro.menu.rotulos.has("trem_tanque"), "rótulo")
	verificar(ResourceLoader.exists("res://assets/icones/%s.png" % Registro.menu.icones.trem_tanque), "ícone")
	verificar(not Construtor.custo_de("trem_tanque").is_empty(), "tem custo")
	igual(int(Registro.estruturas.estacao.tanque_fluido), 25000, "tanque da estação")
	igual(int(Registro.estruturas.estacao.vazao_fluido), 1000, "vazão do cano da estação")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("vagao_tanque"), "Vagão-tanque é jogável")
	igual(Registro.progressao.pesquisas.vagao_tanque.requer, ["trem_automatico", "fluidos"], "pré-requisitos da árvore")
	igual(p.custo("vagao_tanque"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "básico × 30 + automação × 30 (árvore)")
	verificar(not p.peca_liberada("trem_tanque"), "travado no início")
	p.concluidas = {"ferrovia": true, "fluidos": true, "automacao": true}
	verificar(not p.disponivel("vagao_tanque"), "trem automático (sinal em cadeia, sem estudo) ainda não existe: travado")
	p.concluidas["vagao_tanque"] = true
	verificar(p.peca_liberada("trem_tanque"), "libera o trem-tanque")
	verificar(Pesquisa.new(true).peca_liberada("trem_tanque"), "modo demonstração constrói")


func test_construtor() -> void:
	var c := _linha()
	var p := c.plano_peca("trem_tanque", Vector2i(0, 0), 0)
	igual(p[0].acao, "trem")
	igual(p[0].nome, "trem_tanque")
	igual(p[0].motivo, "")
	igual(c.plano_peca("trem_tanque", Vector2i(6, 0), 0)[0].motivo, "sem_trilho", "fora do trilho: vermelho")
	c.cobrar = true
	c.inventario = {"placa_ferro": 100, "engrenagem": 100, "tubo": 100, "barra_aco": 100}
	var rel := c.executar(c.plano_peca("trem_tanque", Vector2i(0, 0), 0))
	igual(rel.trens.size(), 1)
	igual(rel.trens[0].get("nome", ""), "trem_tanque", "o mundo sabe que é trem-tanque")
	igual(int(c.inventario.tubo), 100 - int(Construtor.custo_de("trem_tanque").tubo), "cobra o custo do trem-tanque")


func test_cano_liga_na_estacao() -> void:
	var m := _montar()
	verificar(m.f.estacao_tem_cano(m.a), "cano encostado no leste da estação A")
	verificar(m.f.estacao_tem_cano(m.b), "e na B")
	perto(float(m.ra.cap), 25100.0, 1e-3, "rede A: cano + tanque")
	# cano de lado (paralelo à estação) não liga
	var c2 := _linha()
	var est2 := {}
	var f2 := Fabrica.new(c2.mapa)
	_por(c2, "estacao", Vector2i(1, -2), 0)
	_por(c2, "cano_reto", Vector2i(3, -1), 0)                 # norte–sul: nenhuma boca para a estação
	var s2: int = c2.mapa.tiles[Vector2i(1, -2)]
	est2[s2] = {"enviar": {}, "recebido": {}}
	f2.estoques = est2
	f2.reconstruir()
	verificar(not f2.estacao_tem_cano(s2), "cano paralelo não liga")


func test_modos_da_estacao() -> void:
	var m := _montar()
	var f: Fabrica = m.f
	m.ra.fluido = "agua"
	m.ra.qtd = 20000.0
	var ta: Dictionary = f.estoques[m.a].fluido
	igual(ta.modo, "desligado", "começa desligado (não rouba fluido da rede)")
	for i in 30 * 3:
		f.tick(1.0 / 30.0)
	perto(float(ta.qtd), 0.0, 1e-6, "desligado: nada")
	ta.modo = "carregar"
	for i in 30 * 3:
		f.tick(1.0 / 30.0)
	perto(float(ta.qtd), 3000.0, 40.0, "carregar: 1.000/s da rede para o tanque da estação")
	igual(ta.f, "agua")
	perto(float(m.ra.qtd), 17000.0, 40.0, "saiu da rede")
	# descarregar devolve
	ta.modo = "descarregar"
	for i in 30 * 2:
		f.tick(1.0 / 30.0)
	perto(float(ta.qtd), 1000.0, 40.0, "descarregar: tanque → rede")
	# fluido diferente não mistura
	var tb: Dictionary = f.estoques[m.b].fluido
	tb.modo = "descarregar"
	tb.f = "seiva"
	tb.qtd = 500.0
	m.rb.fluido = "agua"
	m.rb.qtd = 10.0
	for i in 30:
		f.tick(1.0 / 30.0)
	perto(float(tb.qtd), 500.0, 1e-6, "seiva não entra em rede de água")


## O trem-tanque leva a água da rede A para a rede B, ida e volta, sem perder nada.
func test_leva_fluido_de_a_para_b() -> void:
	var m := _montar()
	var f: Fabrica = m.f
	var g: GrafoTrilhos = m.g
	m.ra.fluido = "agua"
	m.ra.qtd = 25100.0
	f.estoques[m.a].fluido.modo = "carregar"
	f.estoques[m.b].fluido.modo = "descarregar"
	var t := Trem.new(1, g, _tanque())
	var base := g.peca_no_ponto(Vector2(0.5, -3.0))
	verificar(t.colocar(base.peca, g.pecas[base.peca].a), "trem-tanque cabe na linha")
	var trens: Array[Trem] = [t]
	var chegadas := _rodar(f, g, trens, 150.0)
	verificar(chegadas >= 4, "várias viagens (%d chegadas)" % chegadas)
	perto(_total(m, trens), 25100.0, 1.0, "nada se perde (rede A + estações + trem + rede B)")
	verificar(float(m.rb.qtd) > 15000.0, "a água chegou na rede B (%.0f)" % m.rb.qtd)
	igual(m.rb.fluido, "agua")
	verificar(float(m.ra.qtd) < 10000.0, "a rede A esvaziou (%.0f)" % m.ra.qtd)
	verificar(t.fluido_qtd <= 0.0 or t.origem_fluido == m.a, "o que está no trem veio de A")


## Trem cheio não descarrega na estação de onde veio; estação desligada não troca; salvo leva o fluido.
func test_regras_do_trem() -> void:
	var t := Trem.new(1, GrafoTrilhos.new(), _tanque())
	var a := {"enviar": {}, "recebido": {}, "fluido": {"modo": "carregar", "f": "seiva", "qtd": 24000.0}}
	t.trocar_carga(a, 7)
	perto(t.fluido_qtd, 24000.0, 1e-6, "o trem leva tudo o que a estação tinha")
	perto(float(a.fluido.qtd), 0.0, 1e-6, "estação vazia")
	igual(t.fluido, "seiva")
	igual(t.origem_fluido, 7)
	a.fluido.modo = "descarregar"
	a.fluido.qtd = 0.0
	t.trocar_carga(a, 7)
	perto(t.fluido_qtd, 24000.0, 1e-6, "não devolve na estação de onde veio")
	var b := {"enviar": {}, "recebido": {}, "fluido": {"modo": "desligado", "f": "", "qtd": 0.0}}
	t.trocar_carga(b, 9)
	perto(t.fluido_qtd, 24000.0, 1e-6, "desligada: nada")
	var agua := {"enviar": {}, "recebido": {}, "fluido": {"modo": "descarregar", "f": "agua", "qtd": 100.0}}
	t.trocar_carga(agua, 10)
	perto(t.fluido_qtd, 24000.0, 1e-6, "não descarrega seiva num tanque com água")
	b.fluido.modo = "descarregar"
	b.fluido.qtd = 5000.0
	b.fluido.f = "seiva"
	t.trocar_carga(b, 9)
	perto(float(b.fluido.qtd), 25000.0, 1e-6, "descarrega até encher o tanque da estação")
	perto(t.fluido_qtd, 4000.0, 1e-6, "sobra no trem")
	# estação de salvo antigo (sem "fluido"): o trem não quebra
	t.trocar_carga({"enviar": {}, "recebido": {}}, 11)
	perto(t.fluido_qtd, 4000.0, 1e-6)
	# salvar/restaurar
	var m := _montar()
	var g: GrafoTrilhos = m.g
	var t2 := Trem.new(3, g, _tanque())
	var base := g.peca_no_ponto(Vector2(0.5, -3.0))
	t2.colocar(base.peca, g.pecas[base.peca].a)
	t2.fluido = "agua"
	t2.fluido_qtd = 1234.0
	t2.origem_fluido = m.a
	var d := t2.para_salvar()
	g.liberar(t2.id)
	var t3 := Trem.de_salvo(d, g)
	verificar(t3 != null, "restaura")
	if t3 != null:
		igual(t3.fluido, "agua")
		perto(t3.fluido_qtd, 1234.0, 1e-6)
		igual(t3.origem_fluido, m.a)
		igual(t3.peca(), "trem_tanque")
	# salvo antigo sem os campos de fluido
	d.erase("fluido")
	d.erase("fluido_qtd")
	d.erase("origem_fluido")
	g.liberar(3)
	var t4 := Trem.de_salvo(d, g)
	verificar(t4 != null and t4.fluido_qtd == 0.0, "salvo antigo carrega sem fluido")
