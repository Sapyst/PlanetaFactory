extends Caso
## Raios da tempestade (fase 2.5, ambiente/raios.gd): o evento "raio" do clima (tempestade e tufão) cai num ponto do
## mapa perto da fábrica. Sem proteção, a construção mais alta perto leva 150 de dano (o escudo absorve) e a vegetação
## em volta pode pegar fogo; no chão, o mato pega fogo ou fica a marca queimada. O desenho usa a queda (ponto e altura).


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-12, 40):
		for y in range(-12, 20):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_dados() -> void:
	var r: Dictionary = Registro.clima.get("raios", {})
	verificar(not r.is_empty(), "regra dos raios em clima.json")
	perto(float(r.dano), 150.0, 1e-6, "150 de dano sem proteção")
	verificar(Registro.clima.estados.tempestade.get("raios", false) and Registro.clima.estados.tufao.get("raios", false), "tempestade e tufão têm raios")
	verificar(not Registro.clima.estados.chuva.get("raios", false), "chuva comum não tem")
	perto(Raios.altura("fornalha"), float(Registro.modelos.fornalha.dims[2]), 1e-6, "altura vem do modelo")


func test_evento_do_clima_vira_raio() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(0, 0), 0)
	verificar(id >= 0, "montagem")
	var r := Raios.new(m, 3)
	var c := Clima.new(5)
	c.forcar("tempestade", true)
	var n := 0
	for i in 600:                           # 60 s de tempestade (~0,07 raio/s)
		c.tick(0.1)
		n += c.eventos.count("raio")
		r.tick(c)
		if i % 100 == 0:
			verificar(not c.eventos.has("raio"), "o raio do clima foi consumido")
	verificar(n >= 1, "a tempestade soltou raios (%d)" % n)
	igual(r.total, n, "cada evento virou um raio no mapa")
	verificar(not r.quedas.is_empty(), "queda para o desenho")
	var q: Dictionary = r.quedas[-1]
	verificar(q.has("pos") and q.has("alt") and q.has("tipo"), "queda tem ponto, altura e tipo")
	c.forcar("limpo", true)
	var antes := r.total
	for i in 600:
		c.tick(0.1)
		r.tick(c)
	igual(r.total, antes, "céu limpo: nenhum raio")


func test_sorteio_perto_da_fabrica() -> void:
	var m := _mapa()
	m.colocar("fornalha", Vector2i(20, 10), 0)
	var r := Raios.new(m, 9)
	var longe := 0.0
	for i in 300:
		var p := r.sortear_ponto(Vector2(-300, -300))
		longe = maxf(longe, p.distance_to(Vector2(21, 11)))
	verificar(longe <= 20.01, "cai a até 20 m de uma construção, não onde a câmera olha (%.1f m)" % longe)
	verificar(longe > 10.0, "espalha pelo círculo (%.1f m)" % longe)
	var vazio := Raios.new(MapaOcupacao.new(GeradorMundo.new(1337)), 9)
	var p2 := vazio.sortear_ponto(Vector2(100, 100))
	verificar(p2.distance_to(Vector2(100, 100)) <= 30.01, "sem construção: em volta do foco")
	# o ponto alto atrai: fornalha (3 m) × muro (1,5 m) → ~4× mais raios em volta da fornalha
	var m2 := _mapa()
	m2.colocar("fornalha", Vector2i(-10, 0), 0)
	m2.colocar("muro_centro", Vector2i(30, 0), 0)
	var r2 := Raios.new(m2, 5)
	var perto_f := 0
	for i in 400:
		if r2.sortear_ponto(Vector2.ZERO).x < 10.0:
			perto_f += 1
	verificar(perto_f > 280 and perto_f < 360, "peso pela altura²: %d de 400 perto da fornalha (esperado ~320)" % perto_f)


func test_atinge_o_mais_alto() -> void:
	var m := _mapa()
	var baixa := m.colocar("torre_defesa", Vector2i(0, 0), 0)        # 1,6 m
	var alta := m.colocar("fornalha", Vector2i(3, 0), 0)             # 3,1 m
	var r := Raios.new(m, 3)
	var danos := {}
	r.dano = func(id: int, p: float) -> void: danos[id] = float(danos.get(id, 0.0)) + p
	var q := r.cair(Vector2(2.0, 1.0))                               # entre as duas
	igual(q.tipo, "estrutura", "sem proteção pega a construção")
	igual(int(q.id), alta, "a mais alta perto leva o raio")
	perto(float(danos.get(alta, 0.0)), 150.0, 1e-6, "150 de dano")
	verificar(not danos.has(baixa), "a baixa não")
	perto(float(q.alt), Raios.altura("fornalha"), 1e-6, "o raio bate no topo do modelo")
	var q2 := r.cair(Vector2(35.5, 15.5))
	igual(q2.tipo, "chao", "longe de tudo: chão")
	igual(r.total, 2, "dois raios")


func test_escudo_absorve_o_raio() -> void:
	var m := _mapa()
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var f := Fabrica.new(m)
	c.torre_energia = f.gastar_torre
	var esc := m.colocar("gerador_escudo", Vector2i(0, 0), 0)
	var forn := m.colocar("fornalha", Vector2i(4, 0), 0)
	f.reconstruir()
	f.carga_torre[esc] = 8.0
	c.tick(1.0 / 30.0, [])                                           # lista dos escudos
	var r := Raios.new(m, 3)
	r.colonia = c
	var danos := {}
	r.dano = func(id: int, p: float) -> void: danos[id] = p
	var q := r.cair(Vector2(5.0, 1.0))
	igual(q.tipo, "escudo", "o escudo pegou")
	verificar(danos.is_empty(), "a fornalha não perdeu vida")
	perto(float(f.carga_torre[esc]), 8.0 - 150.0 * 0.02, 1e-4, "gastou 3 MJ do escudo (150 × 0,02)")
	f.carga_torre[esc] = 0.0
	r.cair(Vector2(5.0, 1.0))
	perto(float(danos.get(forn, 0.0)), 150.0, 1e-6, "sem carga o raio passa")


func test_fogo_e_chao_queimado() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var a := AmbienteVivo.new(g, m, 3)
	var r := Raios.new(m, 3)
	r.ambiente = a
	var t0 := Vector2i(9999, 0)
	for x in range(50, 400, 3):
		if t0.x == 9999 and a._inflamavel(Vector2i(x, 0)):
			t0 = Vector2i(x, 0)
	verificar(t0.x != 9999, "achou vegetação seca")
	var q := r.cair(Vector2(t0) + Vector2(0.5, 0.5))
	igual(q.tipo, "fogo", "no mato o raio acende fogo")
	verificar(a.fogo.has(t0), "o tile pegou fogo")
	verificar(a.valor(t0, AmbienteVivo.QUEIM) > 0.0, "e o chão ficou queimado")
	# água: só a marca (não pega fogo)
	var w := Vector2i(9999, 0)
	for x in range(-400, 400, 4):
		for y in range(-200, 200, 8):
			if w.x == 9999 and g.terreno(Vector2i(x, y)) != GeradorMundo.Terreno.TERRA:
				w = Vector2i(x, y)
	if w.x != 9999:
		var q2 := r.cair(Vector2(w) + Vector2(0.5, 0.5))
		igual(q2.tipo, "chao", "fora do mato não pega fogo")


func test_salvar() -> void:
	var m := _mapa()
	var id := m.colocar("para_raios", Vector2i(0, 0), 0)
	var r := Raios.new(m, 3)
	r.cair(Vector2(2.5, 0.5))
	r.cair(Vector2(1.5, 3.5))
	igual(int(r.descargas.get(id, 0)), 2, "contador de descargas")
	var r2 := Raios.new(m, 4)
	r2.restaurar(r.estado())
	igual(int(r2.descargas.get(id, 0)), 2, "volta do salvo")
	igual(r2.total, 2)
	var p1 := r.sortear_ponto(Vector2.ZERO)
	var p2 := r2.sortear_ponto(Vector2.ZERO)
	perto(p1.distance_to(p2), 0.0, 1e-6, "mesmo sorteio depois de carregar")


func test_desenho_no_lugar_do_raio() -> void:
	var m := _mapa()
	var pr := m.colocar("para_raios", Vector2i(4, 4), 0)
	var r := Raios.new(m, 3)
	r.cair(Vector2(6.0, 6.0))
	var raiz := (Engine.get_main_loop() as SceneTree).root
	var cam := CameraJogo.new()
	raiz.add_child(cam)
	cam.alvo = Vector3(4.5, 0, -4.5)
	cam.distancia = 20.0
	cam.position = Vector3(4.5, 15.0, 8.0)
	var dc := DesenhoClima.new()
	dc.clima = Clima.new(5)
	dc.camera = cam
	dc.raios = r
	dc._criar_raio()
	dc._relampagos(0.016)
	verificar(r.quedas.is_empty(), "o desenho consumiu a queda")
	igual(dc._malha_raio.get_surface_count(), 1, "o raio foi desenhado")
	var aabb := dc._malha_raio.get_aabb()
	var pt := r.ponta(pr)
	verificar(aabb.position.y > pt.z - 1.5 and aabb.position.y <= pt.z + 0.01, "termina na ponta do para-raios (%.2f m; a fita tem 1,4 m de halo), não no chão (%.2f)" % [pt.z, aabb.position.y])
	verificar(aabb.has_point(Vector3(pt.x, pt.z + 0.01, -pt.y)) or aabb.grow(1.5).has_point(Vector3(pt.x, pt.z, -pt.y)), "no lugar do para-raios")
	verificar(dc._flash > 0.9, "perto da câmera: clarão forte")
	verificar(dc._trovoes.size() == 1, "trovão marcado")
	dc.free()
	cam.queue_free()
