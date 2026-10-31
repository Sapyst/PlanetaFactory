extends Caso
## Mina de pulso (mina_pulso, fase 2.4): modelo do estudo (estudo_muros_mina.py, coleção 'mina'; conv_combate_meio.py),
## pesquisa pela árvore (ciência militar; básico/automação/militar × 30). Aranha a menos de 1,2 m dispara: as aranhas
## em 3 m ficam atordoadas 3 s (paradas, sem morder) e a mina rearma em 20 s. Baixa: não barra a passagem.


func _base() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	for x in range(-38, 37):
		for y in range(-6, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return [m, c]


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("mina_pulso", {})
	verificar(r.has("pulso"), "regra do pulso")
	perto(float(r.pulso.atordoa), 3.0, 1e-6, "atordoa 3 s (árvore)")
	perto(float(r.pulso.rearme), 20.0, 1e-6, "rearma em 20 s (árvore)")
	verificar(not r.has("energia_kw"), "sem energia")
	var md: Dictionary = Registro.modelos.get("mina_pulso", {})
	igual(Registro.area("mina_pulso"), Vector2i(1, 1), "1×1")
	igual(md.get("estudo", ""), "estudo_muros_mina.py", "convertida do estudo")
	verificar(float(md.dims[0]) <= 1.01 and float(md.dims[1]) <= 1.01, "não passa do tile (%s)" % str(md.dims))
	verificar(float(md.dims[2]) < float(Registro.inimigos.aranha.altura_que_bloqueia), "baixa: as aranhas passam por cima")
	verificar(int(md.tris) <= 4100, "leve (%d triângulos)" % md.tris)
	verificar(ResourceLoader.exists("res://assets/icones/mina_pulso.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return "mina_pulso" in cat.pecas), "no menu (Defesa)")
	verificar(not Registro.progressao.custos.get("mina_pulso", {}).is_empty(), "custo de construção")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("mina_pulso"), "jogável")
	verificar(not p.disponivel("mina_pulso"), "travada no início")
	p.concluidas = {"ciencia_militar": true}
	verificar(p.disponivel("mina_pulso"), "depois da ciência militar")
	igual(p.custo("mina_pulso"), {"pacote_pesquisa": 30, "pacote_automacao": 30, "pacote_militar": 30}, "custo da árvore")
	p.concluidas["mina_pulso"] = true
	verificar(p.peca_liberada("mina_pulso"), "libera a mina")


func test_atordoa_e_rearma() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var mina := m.colocar("mina_pulso", Vector2i(0, 0), 0)
	verificar(mina >= 0, "coube")
	var ninho := c._criar_ninho(Vector2i(30, 0), 1.0)
	var perto_a := c._nova_aranha(ninho)
	var vizinha := c._nova_aranha(ninho)
	var longe := c._nova_aranha(ninho)
	for a in [perto_a, vizinha, longe]:
		c.aranhas[a].estado = Colonia.E.VOLTANDO
	c.aranhas[perto_a].pos = Vector2(4.0, 0.5)
	c.aranhas[vizinha].pos = Vector2(2.6, 2.4)            # 2,9 m do centro: dentro do raio
	c.aranhas[longe].pos = Vector2(5.5, 3.5)
	c.tick(1.0 / 30.0, [])
	verificar(c.mina_armada(mina), "armada, ninguém perto")
	c.aranhas[perto_a].pos = Vector2(1.2, 0.6)            # 0,7 m: pisou
	c.tick(1.0 / 30.0, [])
	var pulsos := c.eventos.filter(func(e): return e.tipo == "pulso")
	igual(pulsos.size(), 1, "disparou")
	verificar(not c.mina_armada(mina), "rearmando")
	verificar(float(c.aranhas[perto_a].get("atordoada", 0.0)) > 2.9, "a que pisou ficou atordoada")
	verificar(float(c.aranhas[vizinha].get("atordoada", 0.0)) > 2.9, "a vizinha (2,9 m) também")
	verificar(float(c.aranhas[longe].get("atordoada", 0.0)) <= 0.0, "a de longe não")
	# atordoada não anda
	var p0: Vector2 = c.aranhas[vizinha].pos
	for i in 60:
		c.tick(1.0 / 30.0, [])
	perto(c.aranhas[vizinha].pos.distance_to(p0), 0.0, 1e-6, "parada por 2 s")
	for i in 45:
		c.tick(1.0 / 30.0, [])
	verificar(c.aranhas[vizinha].pos.distance_to(p0) > 0.05, "depois de 3 s volta a andar")
	# rearma em 20 s: antes disso não dispara de novo (aranha nova parada em cima da mina)
	var n := 0
	var pisa := c._nova_aranha(ninho)
	c.aranhas[pisa].estado = Colonia.E.PARADA
	for i in 30 * 15:                        # até ~18,6 s desde o disparo
		if c.aranhas.has(pisa):
			c.aranhas[pisa].pos = Vector2(0.9, 0.5)
		c.tick(1.0 / 30.0, [])
		n += c.eventos.filter(func(e): return e.tipo == "pulso").size()
	igual(n, 0, "não dispara rearmando")
	pisa = c._nova_aranha(ninho)
	for i in 30 * 3:
		c.aranhas[pisa].pos = Vector2(0.9, 0.5)
		c.tick(1.0 / 30.0, [])
		n += c.eventos.filter(func(e): return e.tipo == "pulso").size()
	igual(n, 1, "rearmou em 20 s e disparou de novo")


func test_atordoada_nao_morde() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var muro := m.colocar("muro_centro", Vector2i(0, 0), 0)
	var mina := m.colocar("mina_pulso", Vector2i(1, 0), 0)
	var ninho := c._criar_ninho(Vector2i(30, 0), 1.0)
	var a := c._nova_aranha(ninho)
	c.aranhas[a].estado = Colonia.E.ATACANDO
	c.aranhas[a].alvo = muro
	c.aranhas[a].pos = Vector2(4.0, 0.5)
	var mordeu_atordoada := false
	var disparou := false
	for i in 30 * 4:
		c.tick(1.0 / 30.0, [])
		if c.eventos.any(func(e): return e.tipo == "pulso"):
			disparou = true
		if float(c.aranhas[a].get("atordoada", 0.0)) > 0.0 and c.aranhas[a].mordendo:
			mordeu_atordoada = true
	verificar(disparou, "a aranha pisou na mina a caminho do muro")
	verificar(not mordeu_atordoada, "atordoada não morde")
	verificar(mina >= 0 and m.estruturas.has(mina), "a mina segue no lugar")


func test_salvar() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var c: Colonia = b[1]
	var mina := m.colocar("mina_pulso", Vector2i(0, 0), 0)
	c._listas()
	c.minas[mina] = {"recarga": 12.0}
	var d := c.estado()
	var c2 := Colonia.new(m, Poluicao.new(m.gerador), 3)
	c2.restaurar(d)
	verificar(not c2.mina_armada(mina), "rearme volta do salvo")
