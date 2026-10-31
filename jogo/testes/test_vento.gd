extends Caso
## Vento: rumo predominante da estação, oscilação, rajadas, média medida, fator do lugar (VentoLocal), curva da
## turbina com proteção em ventania, poluição do ar indo vento abaixo e a camada de vento da visão de recursos.


func _clima() -> Clima:
	var c := Clima.new(21)
	c.t_estacao = float(Registro.clima.estacao_s) * 0.5          # meio da estação: sem resto da anterior
	return c


func test_nome_do_rumo() -> void:
	igual(Clima.nome_rumo(Vector2(-1, 0)), "de leste", "soprando para oeste vem de leste")
	igual(Clima.nome_rumo(Vector2(0, 1)), "de sul", "soprando para norte vem de sul")
	igual(Clima.nome_rumo(Vector2(1, 1)), "de sudoeste", "diagonal")


func test_rumo_da_estacao_e_oscilacao() -> void:
	var c := _clima()
	for e in Registro.clima.estacoes.size():
		c.estacao = e
		var rumo := c.rumo_estacao()
		igual(Clima.nome_rumo(rumo), "de " + str(Registro.clima.estacoes[e].vento_de), "estação %d sopra do rumo dela" % e)
		var maior := 0.0
		var soma := Vector2.ZERO
		for i in 1200:
			c.tick(1.0)
			maior = maxf(maior, absf(rad_to_deg(c.direcao_vento.angle_to(rumo))))
			soma += c.direcao_vento
		verificar(maior <= 40.5 and maior > 15.0, "oscila em volta do rumo (até %.0f°)" % maior)
		verificar(absf(rad_to_deg(soma.angle_to(rumo))) < 20.0, "na média, sopra do rumo")


func test_rajada_passa_pelo_foco() -> void:
	var c := _clima()
	c.foco = Vector2(50, -20)
	c.prox_rajada = 0.0
	c.tick(0.1)
	verificar(not c.rajada.is_empty(), "rajada nasceu")
	var forte := 0.0
	var base: float = c.valores.vento
	for i in 400:
		c.tick(0.1)
		forte = maxf(forte, c.vento_em(c.foco) - float(c.valores.vento))
		if c.rajada.is_empty():
			break
	verificar(forte > 0.05, "a rajada somou força ao passar pelo foco (+%.2f)" % forte)
	verificar(c.rajada.is_empty(), "e foi embora vento abaixo")
	perto(c.vento_em(Vector2(9999, 9999)), float(c.valores.vento), 1e-6, "sem rajada: força do clima")
	verificar(base > 0.0, "clima tem vento")


func test_media_medida_e_save() -> void:
	var c := _clima()
	for i in 3000:
		c.tick(1.0)
	verificar(c.vento_medio.length() > 0.1, "média medida tem força (%.2f)" % c.vento_medio.length())
	verificar(absf(rad_to_deg(c.vento_medio.angle_to(c.rumo_estacao()))) < 35.0, "média aponta para o rumo da estação")
	var c2 := Clima.new(3)
	c2.restaurar(c.estado())
	perto(c2.t_vento, c.t_vento, 1e-6, "tempo do vento volta do save")
	verificar(c2.vento_medio.is_equal_approx(c.vento_medio), "média volta do save")


func test_curva_da_turbina() -> void:
	perto(Fabrica.curva_turbina(0.2), 0.0, 1e-6, "abaixo do corte: parada")
	perto(Fabrica.curva_turbina(0.55), 0.5, 1e-4, "meio caminho")
	perto(Fabrica.curva_turbina(1.0), 1.0, 1e-6, "plena")
	perto(Fabrica.curva_turbina(1.3), 0.4, 1e-6, "ventania: bandeira, rende 40%")


func test_fator_do_lugar() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var a := AmbienteVivo.new(g, m, 1)
	var vl := VentoLocal.new(g, m, a)
	var t := Vector2i(6, 2)
	for x in range(0, 12):
		for y in range(-2, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	var livre := vl.fator(t, Vector2.LEFT)
	verificar(livre >= 0.4 and livre <= 1.6, "fator no intervalo (%.2f)" % livre)
	# sotavento: montadora (alta e larga) logo a leste, vento soprando para oeste
	var id := m.colocar("montadora", Vector2i(7, 1), 0)
	verificar(id >= 0, "montadora colocada")
	perto(vl.fator(t, Vector2.LEFT), livre - 0.2, 1e-4, "atrás da montadora venta menos")
	perto(vl.fator(t, Vector2.RIGHT), livre, 1e-4, "com vento do outro lado, não")
	m.remover(id)
	# árvores crescidas em volta abrigam
	for k in 3:
		a.plantas[t + Vector2i(k - 1, 2)] = 1.0
	perto(vl.fator(t, Vector2.LEFT), maxf(0.4, livre - 0.18), 1e-4, "3 árvores: −18%")


func test_poluicao_vai_vento_abaixo() -> void:
	var p := Poluicao.new(GeradorMundo.new(1337))
	var sem := p.pesos_vento()
	for w in sem:
		perto(w, 0.25, 1e-6, "sem vento: igual para os 4 lados")
	p.vento = Vector2(1, 0)
	var pesos := p.pesos_vento()
	var soma := 0.0
	for w in pesos:
		soma += w
	perto(soma, 1.0, 1e-5, "soma 1 (o total que vaza não muda)")
	var i_leste := Grade.DIRECOES.find(Vector2i(1, 0))
	perto(pesos[i_leste], 0.775, 1e-4, "vento forte para leste: 70% + 7,5% vão para leste")
	p.valores[Vector2i.ZERO] = 100.0
	p.tick(1.0)
	verificar(p.em_chunk(Vector2i(1, 0)) > p.em_chunk(Vector2i(-1, 0)) * 5.0, "a nuvem anda com o vento")


func test_visao_camada_vento() -> void:
	var g := GeradorMundo.new(1337)
	var v := VisaoRecursos.new()
	v.gerador = g
	v.mapa = MapaOcupacao.new(g)
	v._d = Registro.recursos
	v.clima = _clima()
	v.vento_local = VentoLocal.new(g, v.mapa)
	v.clima.vento_medio = Vector2(-0.5, 0)
	verificar(v.descrever(Vector2i(3, 3)).contains("Vento médio aqui"), "ficha mostra o vento médio")
	verificar(v.descrever(Vector2i(3, 3)).contains("de leste"), "e de onde vem")
	verificar(VisaoRecursos.cor_vento(0.1).b > VisaoRecursos.cor_vento(1.0).b, "calmo azul, ventania quente")
	verificar(v.alternar(), "liga em recursos")
	igual(v.camada, "recursos", "primeiro recursos")
	verificar(v.alternar(), "segue ligada")
	igual(v.camada, "vento", "depois vento")
	verificar(not v.alternar(), "depois desliga")
	v.free()


## Vento forte é amplitude, não velocidade: o ritmo quase não muda e nenhum shader multiplica o tempo pela força
## (além de parecer jogo acelerado, TIME × força salta de fase quando a força muda).
func test_vento_forte_nao_acelera() -> void:
	perto(Clima.ritmo_vento(0.0), 1.0, 0.001, "calmaria")
	verificar(Clima.ritmo_vento(1.0) <= 1.35, "ventania acelera pouco (%.2f)" % Clima.ritmo_vento(1.0))
	var re := RegEx.create_from_string("(TIME|vento_tempo)\\s*\\*\\s*\\([^)]*(intensidade|forte|i_v)")
	for f in ["material_pf.gdshaderinc", "grama.gdshader", "clima.gdshaderinc"]:
		var txt := FileAccess.get_file_as_string("res://render/shaders/" + f)
		verificar(txt != "", "achou " + f)
		igual(re.search(txt), null, "%s: tempo multiplicado pela força" % f)
	var veg := FileAccess.get_file_as_string("res://render/shaders/material_pf.gdshaderinc")
	verificar(veg.contains("vento_tranco(") and veg.contains("vento_tempo"), "vegetação com trancos e relógio próprio")
	var gr := FileAccess.get_file_as_string("res://render/shaders/grama.gdshader")
	verificar(gr.contains("vento_tranco_leve(") and gr.contains("vento_tempo"), "grama também")
