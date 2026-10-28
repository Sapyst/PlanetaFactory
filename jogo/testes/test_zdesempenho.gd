extends Caso
## Fábrica grande (milhares de peças, 60 aranhas, 20 torres, 6 trens) — mede o custo de um passo de simulação
## (1/30 s). Orçamento para não travar no celular: o passo inteiro bem abaixo de ~8 ms aqui no PC.

const LINHAS := 40
const COMPRIMENTO := 60


func test_fabrica_grande() -> void:
	var g := GeradorMundo.new(1337)
	g.relevo_ativo = false                  # a fábrica de teste é maior que a área plana do início
	var m := MapaOcupacao.new(g)
	var c := Construtor.new(m)
	for x in range(-10, LINHAS * 2 + 10):
		for y in range(-12, COMPRIMENTO + 12):
			m.limpar_obstaculo(Vector2i(x, y))
	var t0 := Time.get_ticks_usec()
	for i in LINHAS:
		c.executar(c.plano_linha("esteira", Vector2i(i * 2, 0), Vector2i(i * 2, COMPRIMENTO - 1), 0))
	for i in 20:
		c.executar(c.plano_peca("torre_defesa", Vector2i(i * 4, -6), 0))
		c.executar(c.plano_peca("fornalha", Vector2i(i * 4, COMPRIMENTO + 2), 0))
	print("      montar %d estruturas: %d ms" % [m.estruturas.size(), (Time.get_ticks_usec() - t0) / 1000])
	var f := Fabrica.new(m)
	t0 = Time.get_ticks_usec()
	f.reconstruir()
	var t_rec := (Time.get_ticks_usec() - t0) / 1000.0
	for cm in f.caminhos:
		var e: EsteiraCaminho = cm.esteira
		for k in 120:
			e.inserir_em("pedra", k * 0.45)
	var itens := 0
	for cm in f.caminhos:
		itens += cm.esteira.itens.size()
	var p := Poluicao.new(m.gerador)
	var col := Colonia.new(m, p, 3)
	var ninho := col._criar_ninho(Vector2i(LINHAS, COMPRIMENTO + 30), 1.0)
	for k in 60:
		var a := col._nova_aranha(ninho)
		col.aranhas[a].estado = Colonia.E.ATACANDO
		col.aranhas[a].alvo = m.tiles[Vector2i(k % LINHAS * 2, COMPRIMENTO - 1)]
	var fontes: Array[Dictionary] = []
	for id in m.estruturas:
		if m.estruturas[id].nome == "fornalha":
			fontes.append({"id": id, "pos": Vector2(m.estruturas[id].minimo)})
	var dt := 1.0 / 30.0
	var tf := 0
	var tc := 0
	var tp := 0
	for i in 90:
		var a := Time.get_ticks_usec()
		f.tick(dt)
		var b := Time.get_ticks_usec()
		col.tick(dt, fontes)
		var cc := Time.get_ticks_usec()
		p.emitir(Vector2i(10, 10), 1.0)
		p.tick(dt)
		tp += Time.get_ticks_usec() - cc
		tf += b - a
		tc += cc - b
	var ms_f := tf / 90.0 / 1000.0
	var ms_c := tc / 90.0 / 1000.0
	print("      %d estruturas, %d caminhos, %d itens: remontar %.1f ms · passo fábrica %.2f ms · colônia (60 aranhas, 20 torres) %.2f ms · poluição %.3f ms" % [
			m.estruturas.size(), f.caminhos.size(), itens, t_rec, ms_f, ms_c, tp / 90.0 / 1000.0])
	verificar(ms_f + ms_c < 8.0, "passo de simulação cabe no orçamento (%.2f ms)" % (ms_f + ms_c))
	verificar(t_rec < 250.0, "remontar a fábrica inteira é rápido o bastante para cada construção (%.0f ms)" % t_rec)
