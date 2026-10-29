extends Caso
## Ambiente vivo: sujeira em volta de quem polui, óleo, despejo correndo na água, fogo andando e apagando,
## estações e tufão ligado à poluição.

func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var f := Fabrica.new(m)
	return [g, m, f, AmbienteVivo.new(g, m, 3)]


func test_sujeira_em_volta_e_some_devagar() -> void:
	var b := _base()
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	for i in 120:
		f.emissao = {id: 4.0 / 60.0}
		a.tick(1.0, f, null)
	var perto := a.valor(Vector2i(3, 3), AmbienteVivo.SUJ)
	var longe := a.valor(Vector2i(12, 12), AmbienteVivo.SUJ)
	verificar(perto > 0.01, "chão suja perto da fornalha (%.3f)" % perto)
	igual(longe, 0.0, "longe continua limpo")
	f.emissao = {}
	for i in 60:
		a.tick(1.0, f, null)
	verificar(a.valor(Vector2i(3, 3), AmbienteVivo.SUJ) < perto and a.valor(Vector2i(3, 3), AmbienteVivo.SUJ) > perto * 0.5, "some, mas devagar")


func test_despejo_corre_na_agua() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	# acha um rio e põe um refinador perto
	var rio := Vector2i.ZERO
	for x in range(-300, 300, 2):
		for y in range(-300, 300, 2):
			if rio == Vector2i.ZERO and g.terreno(Vector2i(x, y)) == GeradorMundo.Terreno.RIO and g.direcao_rio(Vector2i(x, y)) != Vector2.ZERO:
				rio = Vector2i(x, y)
	verificar(rio != Vector2i.ZERO, "achou rio")
	var lugar := Vector2i.ZERO
	for r in range(3, 8):
		for d in [Vector2i(r, 0), Vector2i(-r, 0), Vector2i(0, r), Vector2i(0, -r)]:
			if lugar == Vector2i.ZERO:
				for x in 3:
					for y in 3:
						m.limpar_obstaculo(rio + d + Vector2i(x, y))
				if m.motivo_bloqueio("refinador", rio + d, 0) == "":
					lugar = rio + d
	verificar(lugar != Vector2i.ZERO, "lugar para o refinador")
	var id := m.colocar("refinador", lugar, 0)
	for i in 200:
		f.emissao = {id: 0.1}
		a.tick(1.0, f, null)
	var total := 0.0
	for k in a.dados:
		var arr: PackedFloat32Array = a.dados[k]
		for i in arr.size() / 4:
			total += arr[i * 4 + 2]
	verificar(total > 0.3, "água ficou suja (%.2f)" % total)


func test_fogo_anda_e_apaga() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var c := Clima.new(5)
	c.forcar("limpo", true)
	c.estacao = 1                       # verão
	var t0 := Vector2i.ZERO
	for x in range(50, 300, 3):
		if t0 == Vector2i.ZERO and a._inflamavel(Vector2i(x, 0)):
			t0 = Vector2i(x, 0)
	verificar(t0 != Vector2i.ZERO, "achou vegetação")
	a._acender(t0)
	var maior := 0
	for i in 40:
		a.tick(1.0, f, c)
		maior = maxi(maior, a.fogo.size())
	verificar(maior > 3, "fogo espalhou (%d focos)" % maior)
	verificar(a.valor(t0, AmbienteVivo.QUEIM) > 0.5, "chão queimado onde começou")
	c.forcar("tempestade", true)
	for i in 30:
		a.tick(1.0, f, c)
	igual(a.fogo.size(), 0, "a chuva apaga")


func test_estacoes_e_tufao() -> void:
	var c := Clima.new(3)
	var vistas := {}
	for i in 3000:
		c.tick(1.0)
		vistas[c.nome_estacao()] = true
	igual(vistas.size(), 4, "passa pelas 4 estações")
	# poluição alta: tufão bem mais provável depois da tempestade
	var limpo := 0
	var sujo := 0
	for i in 2000:
		c.poluicao_total = 0.0
		c.atual = "tempestade"
		if c._sortear(Registro.clima.estados.tempestade.proximo) == "tufao": limpo += 1
		c.poluicao_total = 3000.0
		if c._sortear(Registro.clima.estados.tempestade.proximo) == "tufao": sujo += 1
	verificar(sujo > limpo * 3, "ar sujo traz tufão (%d contra %d)" % [sujo, limpo])


func test_salvar() -> void:
	var b := _base()
	var a: AmbienteVivo = b[3]
	a.somar(Vector2i(4, 4), AmbienteVivo.OLEO, 0.7)
	a.fogo[Vector2i(9, 9)] = 5.0
	var a2: AmbienteVivo = _base()[3]
	a2.restaurar(str_to_var(var_to_str(a.estado())))
	perto(a2.valor(Vector2i(4, 4), AmbienteVivo.OLEO), 0.7, 1e-4, "óleo volta")
	verificar(a2.fogo.has(Vector2i(9, 9)), "fogo volta")
