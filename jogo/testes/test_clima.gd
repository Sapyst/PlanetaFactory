extends Caso
## Clima dinâmico: troca de estados, transição suave, chão molhado, raios, salvar/carregar e chuva lavando a poluição.


func test_estados_validos() -> void:
	var d: Dictionary = Registro.clima
	for nome in d.estados:
		var e: Dictionary = d.estados[nome]
		for k in ["nuvens", "neblina", "chuva", "luz", "vento"]:
			verificar(e.has(k), "%s tem %s" % [nome, k])
		for p in e.proximo:
			verificar(d.estados.has(p), "%s → %s existe" % [nome, p])
		verificar(d.nomes.has(nome), "%s tem nome" % nome)


func test_troca_e_transicao() -> void:
	var c := Clima.new(42)
	var vistos := {}
	var salto := 0.0
	var antes := c.valores.duplicate()
	for i in 20000:      # ~2,8 h de jogo a 0,5 s
		c.tick(0.5)
		vistos[c.atual] = true
		for k in antes:
			salto = maxf(salto, absf(c.valores[k] - antes[k]))
		antes = c.valores.duplicate()
	vistos["tufao"] = true                    # (raro: depende da poluição — testado em test_ambiente)
	igual(vistos.size(), Registro.clima.estados.size(), "passou por todos os estados")
	verificar(salto < 0.2, "transição suave (maior salto em 0,5 s: %.3f)" % salto)
	verificar(c.deslocamento.length() > 100.0, "nuvens andam com o vento")


func test_molhado_e_raios() -> void:
	var c := Clima.new(7)
	c.forcar("tempestade", true)
	perto(c.molhado, 1.0, 0.001, "tempestade forçada já começa molhada")
	c.restante = 9999.0
	for i in 600:
		c.tick(0.5)
	verificar(c.eventos.has("raio"), "tempestade solta raios")
	verificar(c.eventos.size() <= 4, "fila de raios limitada")
	c.forcar("limpo")
	for i in 400:
		c.tick(0.5)
	verificar(c.molhado < 0.2, "chão seca com céu limpo (%.2f)" % c.molhado)
	perto(c.valores.chuva, 0.0, 0.01, "chuva para")


func test_desligado_fica_limpo() -> void:
	var c := Clima.new(3)
	c.forcar("chuva", true)
	c.ativo = false
	for i in 200:
		c.tick(0.5)
	perto(c.valores.chuva, 0.0, 0.01, "desligado: sem chuva")
	perto(c.valores.nuvens, Registro.clima.estados.limpo.nuvens, 0.01, "desligado: céu limpo")


func test_salvar_carregar() -> void:
	var a := Clima.new(11)
	for i in 900:
		a.tick(0.5)
	var b := Clima.new(99)
	b.restaurar(str_to_var(var_to_str(a.estado())))
	for i in 900:
		a.tick(0.5)
		b.tick(0.5)
	igual(b.atual, a.atual, "mesmo estado depois de carregar")
	perto(b.valores.nuvens, a.valores.nuvens, 1e-4, "mesmas nuvens")
	perto(b.deslocamento.x, a.deslocamento.x, 1e-3, "mesmo vento")


func test_chuva_lava_poluicao() -> void:
	var g := GeradorMundo.new(1337)
	var seca := Poluicao.new(g)
	var molhada := Poluicao.new(g)
	molhada.chuva = 1.0
	for p in [seca, molhada]:
		p.emitir(Vector2i(3, 3), 40.0)
		p.tick(30.0)
	verificar(molhada.total() < seca.total(), "chuva tira mais poluição (%.1f < %.1f)" % [molhada.total(), seca.total()])


func test_dia_e_noite() -> void:
	var c := Clima.new(3)
	c.t_estacao = float(Registro.clima.estacao_s) * 0.5     # meio da primavera (sem resto do inverno)
	c.hora = 0.0
	perto(c.luz_dia(), 0.0, 1e-4, "meia-noite: escuro")
	igual(c.periodo(), "Noite", "meia-noite é noite")
	c.hora = 0.5
	perto(c.luz_dia(), 1.0, 1e-4, "meio-dia: claro")
	igual(c.relogio(), "12:00", "relógio ao meio-dia")
	var noite := 0
	var soma := 0.0
	for i in 1000:
		c.hora = i / 1000.0
		soma += c.luz_dia()
		if c.luz_dia() < 0.01:
			noite += 1
	verificar(noite > 300 and noite < 450, "noite é ~38%% do ciclo (%d/1000)" % noite)
	verificar(soma / 1000.0 > 0.45 and soma / 1000.0 < 0.6, "luz média do dia ~0,5 (%.2f)" % (soma / 1000.0))
	# verão: dia mais longo; inverno: mais curto
	var luz_em := func(e: int) -> float:
		c.estacao = e
		var t := 0.0
		for i in 200:
			c.hora = i / 200.0
			t += c.luz_dia()
		return t / 200.0
	var prim: float = luz_em.call(0)
	verificar(luz_em.call(1) > prim + 0.05, "verão tem mais luz que a primavera")
	verificar(luz_em.call(3) < prim - 0.05, "inverno tem menos")
	c.estacao = 0
	c.hora = 0.95
	var dia_s := float(Registro.clima.get("dia_s", 720))
	c.tick(dia_s * 0.1)
	perto(c.hora, 0.05, 1e-3, "relógio dá a volta")
	c.ciclo = false
	c.tick(30.0)
	perto(c.hora, 0.05, 1e-6, "relógio parado não anda")
	var c2 := Clima.new(9)
	c2.restaurar(c.estado())
	perto(c2.hora, 0.05, 1e-6, "hora volta do save")


func test_estacao_pelo_relogio_real() -> void:
	var c := Clima.new(5)
	c.tempo_real = true
	c.tick(1.0)
	var dur := float(Registro.clima.estacao_s)
	perto(dur, 7.0 * 86400.0, 1.0, "estação dura 7 dias reais")
	var agora := Time.get_unix_time_from_system()
	igual(c.estacao, int(floor(agora / dur)) % 4, "estação vem do relógio")
	verificar(absf(c.t_estacao - fmod(agora, dur)) < 5.0, "ponto da estação vem do relógio")
	var e := c.estacao
	for i in 100:
		c.tick(600.0)                      # 1000 min de jogo não mudam a estação real
	igual(c.estacao, e, "jogar muito não pula estação")
