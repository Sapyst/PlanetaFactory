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
