extends Caso
## Máquinas de clima (fase 2.5; estudo_clima_2x2.py e estudo_clima_3x3.py via arte/estudos/conv_clima.py), cada uma
## com efeito real no clima do raio dela (ClimaLocal), só ligadas e com energia:
##  - semeador de nuvens 2×2: chuva (≥ 75%) em 40 m — coletores enchem, fogo apaga, nada pega fogo;
##  - defletor de vento 2×2: o vento de 40 m sopra para a frente da peça, sem ventania (tufão não machuca, fogo e
##    poluição vão para lá); pesquisa travada pela turbina alta (sem estudo);
##  - cúpula contra raios 3×3: nenhum raio cai em 30 m (a cúpula pega e manda a carga para os acumuladores);
##  - regulador climático 3×3: céu firme ou chuva mansa em 80 m, sem raio nem tufão; travado pela computação quântica.


const NOMES := {"semeador_nuvens": [Vector2i(2, 2), 40.0, "chuva"], "defletor_vento": [Vector2i(2, 2), 40.0, "vento"],
		"cupula_raios": [Vector2i(3, 3), 30.0, "cupula"], "regulador_clima": [Vector2i(3, 3), 80.0, "regulador"]}


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-20, 60):
		for y in range(-16, 24):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


## ClimaLocal com energia ligada/desligada à mão (as zonas só existem com energia).
func _clima(m: MapaOcupacao, energia := [1.0]) -> ClimaLocal:
	var cl := ClimaLocal.new(m)
	cl.energia = func(_id: int) -> float: return energia[0]
	return cl


func test_dados_e_modelos() -> void:
	for n in NOMES:
		var md: Dictionary = Registro.modelos.get(n, {})
		var r: Dictionary = Registro.estruturas.get(n, {})
		igual(Registro.area(n), NOMES[n][0], "área: " + n)
		igual(md.get("estudo", ""), "estudo_clima_2x2.py" if NOMES[n][0].x == 2 else "estudo_clima_3x3.py", "convertido do estudo: " + n)
		verificar(float(md.dims[0]) <= NOMES[n][0].x + 0.01 and float(md.dims[1]) <= NOMES[n][0].y + 0.01, "dentro da área: %s %s" % [n, str(md.dims)])
		verificar(md.get("portas", []).is_empty(), "sem portas (só energia): " + n)
		perto(float(r.clima_local.raio), NOMES[n][1], 1e-6, "raio da árvore: " + n)
		igual(String(r.clima_local.tipo), NOMES[n][2])
		igual(Fiacao.papel(n), "consumo", "precisa de energia: " + n)
		verificar(ResourceLoader.exists("res://assets/icones/%s.png" % n), "ícone: " + n)
		verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Clima" and n in cat.pecas), "aba Clima: " + n)
		verificar(not Registro.progressao.custos.get(n, {}).is_empty(), "custo: " + n)
		verificar(int(md.tris) <= 12000, "orçamento: %s %d" % [n, md.tris])
	verificar(Registro.modelos.defletor_vento.get("anima", false), "defletor anima (ventiladores, palhetas)")
	verificar(Registro.modelos.semeador_nuvens.get("anima", false), "semeador anima (carrossel)")
	verificar(Registro.modelos.cupula_raios.get("ponta_raio", []).size() == 3, "cúpula: ponto do cristal")


func test_pesquisas() -> void:
	var p := Pesquisa.new()
	for id in ["semeadura_nuvens", "cupula_tempestade", "controle_vento", "controle_clima"]:
		verificar(p.jogavel(id), "ligada: " + id)
	p.concluidas = {"condensador_neblina": true}
	verificar(not p.disponivel("semeadura_nuvens"), "semeadura espera a tempestade")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("semeadura_nuvens"), "condensador + ciência de tempestade")
	igual(p.custo("semeadura_nuvens"), {"pacote_pesquisa": 120, "pacote_automacao": 120, "pacote_quimico": 120, "pacote_ecologico": 120, "pacote_tempestade": 120}, "custo da árvore")
	p.concluidas.merge({"para_raios_2": true})
	verificar(not p.disponivel("cupula_tempestade"), "cúpula espera o escudo 1")
	p.concluidas["escudo_1"] = true
	verificar(p.disponivel("cupula_tempestade"), "para-raios de cristal + escudo 1")
	p.concluidas.merge({"semeadura_nuvens": true, "cupula_tempestade": true})
	verificar(p.jogavel("turbina_alta"), "turbina alta jogável (lote 14)")
	verificar(not p.em_desenvolvimento("controle_vento"), "defletor fora do em desenvolvimento")
	verificar(not p.disponivel("controle_vento"), "defletor pede a turbina alta pesquisada")
	p.concluidas["turbina_alta"] = true
	verificar(p.disponivel("controle_vento"), "com semeadura e turbina alta: defletor pesquisável")
	verificar(not p.jogavel("computacao_quantica"), "computação quântica em breve")
	verificar(not p.disponivel("controle_clima"), "regulador travado pela computação quântica")
	p.concluidas.merge({"semeadura_nuvens": true, "cupula_tempestade": true})
	for par in [["semeadura_nuvens", "semeador_nuvens"], ["cupula_tempestade", "cupula_raios"], ["controle_vento", "defletor_vento"], ["controle_clima", "regulador_clima"]]:
		var q := Pesquisa.new()
		q.concluidas = {par[0]: true}
		verificar(q.peca_liberada(par[1]), "%s libera %s" % par)
	p.livre = true
	verificar(p.peca_liberada("defletor_vento") and p.peca_liberada("regulador_clima"), "no modo livre (demo) já se constroem")


func test_so_com_energia() -> void:
	var m := _mapa()
	var s := m.colocar("semeador_nuvens", Vector2i(0, 0), 0)
	verificar(s >= 0, "montagem")
	var en := [0.0]
	var cl := _clima(m, en)
	cl.atualizar()
	verificar(cl.zonas.is_empty(), "sem energia não faz nada")
	en[0] = 1.0
	cl.atualizar()
	igual(cl.zonas.size(), 1, "com energia, a zona existe")
	m.estruturas[s]["desligada"] = true
	cl.atualizar()
	verificar(cl.zonas.is_empty(), "desligado pelo painel, também não")
	# na rede de verdade (gerador + poste)
	m.estruturas[s].erase("desligada")
	var g := m.colocar("gerador", Vector2i(6, 0), 0)
	m.colocar("poste_energia", Vector2i(3, 3), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[g] = 100.0
	f.tick(0.1)
	var cl2 := ClimaLocal.new(m)
	cl2.energia = f.energia
	cl2.atualizar()
	igual(cl2.zonas.size(), 1, "ligado a um gerador com combustível: ativo")


func test_semeador_chama_chuva() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var a := AmbienteVivo.new(g, m, 3)
	var t0 := Vector2i(9999, 0)                        # vegetação seca com lugar para o semeador a ~10 m
	var lugar := Vector2i.ZERO
	for x in range(50, 400, 3):
		if t0.x != 9999 or not a._inflamavel(Vector2i(x, 0)):
			continue
		for d in [Vector2i(-10, 0), Vector2i(8, 4), Vector2i(0, 8), Vector2i(0, -10)]:
			var s0: Vector2i = Vector2i(x, 0) + d
			for i in 2:
				for j in 2:
					m.limpar_obstaculo(s0 + Vector2i(i, j))
			if t0.x == 9999 and m.motivo_bloqueio("semeador_nuvens", s0, 0) == "":
				t0 = Vector2i(x, 0)
				lugar = s0
	verificar(t0.x != 9999, "achou mato e lugar")
	a._acender(t0)
	var s := m.colocar("semeador_nuvens", lugar, 0)
	var cl := _clima(m)
	cl.atualizar()
	a.clima_local = cl
	var pt := Vector2(t0) + Vector2(0.5, 0.5)
	perto(cl.chuva_em(pt, 0.0), 0.75, 1e-6, "chove 75% no raio")
	perto(cl.chuva_em(pt, 0.9), 0.9, 1e-6, "tempestade por cima: vale a maior")
	perto(cl.chuva_em(pt + Vector2(60, 0), 0.0), 0.0, 1e-6, "fora dos 40 m, o tempo do planeta")
	var c := Clima.new(5)
	c.forcar("limpo", true)
	c.estacao = 1
	for i in 8:
		a.tick(1.0, Fabrica.new(m), c)
	verificar(not a.fogo.has(t0), "a chuva do semeador apagou o fogo")
	verificar(not a._inflamavel(t0), "no raio nada pega fogo (molhado)")
	m.remover(s)
	cl.atualizar()
	if not a.fogo.has(t0) and a.valor(t0, AmbienteVivo.QUEIM) < 0.6:
		verificar(a._inflamavel(t0) or a.valor(t0, AmbienteVivo.QUEIM) > 0.0, "sem o semeador volta a secar")


func test_semeador_enche_coletor() -> void:
	var m := _mapa()
	var s := m.colocar("semeador_nuvens", Vector2i(0, 0), 0)
	var col := m.colocar("coletor_chuva", Vector2i(10, 0), 0)
	verificar(s >= 0 and col >= 0, "montagem")
	var cl := _clima(m)
	cl.atualizar()
	var f := Fabrica.new(m)
	f.reconstruir()
	f.chuva = 0.0                                       # céu limpo no planeta
	var ec: Dictionary = m.estruturas[col]
	f.chuva_maq[col] = cl.chuva_em(Grade.centro_da_area(ec.minimo, ec.area, ec.rot), f.chuva)
	for i in 30:
		f.tick(1.0 / 30.0 * 10.0)
	verificar(float(f.maquinas[col].fluidos.get("agua", 0.0)) > 100.0, "o coletor encheu com a chuva do semeador (%.0f)" % float(f.maquinas[col].fluidos.get("agua", 0.0)))
	f.chuva_maq.clear()
	var antes := float(f.maquinas[col].fluidos.get("agua", 0.0))
	for i in 30:
		f.tick(1.0 / 30.0 * 10.0)
	perto(float(f.maquinas[col].fluidos.get("agua", 0.0)), antes, 1e-3, "sem o semeador, no seco, nada")


func test_defletor_fixa_o_vento() -> void:
	var m := _mapa()
	var d := m.colocar("defletor_vento", Vector2i(0, 0), 1)          # girado 1/4: aponta para oeste
	var cl := _clima(m)
	cl.atualizar()
	var v := cl.vento_em(Vector2(10, 5), Vector2(0, 1), 1.4)
	perto(v.normalized().dot(Vector2(-1, 0)), 1.0, 1e-4, "o vento sopra para onde a peça aponta (oeste)")
	perto(v.length(), 0.8, 1e-6, "ventania cortada (até 80%)")
	perto(cl.vento_em(Vector2(10, 5), Vector2(1, 0), 0.05).length(), 0.3, 1e-6, "calmaria vira brisa (30%): as turbinas giram")
	perto(cl.vento_em(Vector2(80, 5), Vector2(1, 0), 1.4).length(), 1.4, 1e-6, "fora dos 40 m, o vento do planeta")
	verificar(cl.sem_tufao(Vector2(10, 5)) and not cl.sem_tufao(Vector2(80, 5)), "tufão não machuca no raio")
	# tufão: o poste dentro do raio fica inteiro, o de fora apanha
	var dentro := m.colocar("poste_energia", Vector2i(8, 4), 0)
	var fora := m.colocar("poste_energia", Vector2i(50, 4), 0)
	var a := AmbienteVivo.new(m.gerador, m, 3)
	a.clima_local = cl
	var danos := {}
	a.dano = func(id: int, p: float) -> void: danos[id] = p
	a._tufao(Vector2(1.6, 0))
	verificar(not danos.has(dentro), "poste no raio do defletor: sem dano de tufão")
	verificar(danos.has(fora), "poste fora: apanha")
	verificar(not danos.has(d), "o defletor não é frágil")
	# poluição: o chunk coberto vaza para o oeste
	var vc := cl.vento_chunks()
	verificar(vc.has(Vector2i(0, 0)), "chunk do defletor na lista")
	var pol := Poluicao.new(m.gerador)
	var pesos := pol.pesos_vento(vc[Vector2i(0, 0)])
	perto(pesos[3], 0.7 + 0.3 * 0.25, 1e-4, "70% vaza a oeste (+ a parte igual)")
	pol.vento = Vector2(1, 0)
	pol.vento_chunks = vc
	pol.valores[Vector2i(0, 0)] = 100.0
	pol.tick(1.0)
	verificar(pol.em_chunk(Vector2i(-1, 0)) > pol.em_chunk(Vector2i(1, 0)) * 3.0, "contra o vento do planeta, a nuvem foi para oeste")


func test_cupula_pega_os_raios() -> void:
	var m := _mapa()
	var cu := m.colocar("cupula_raios", Vector2i(0, 0), 0)
	m.colocar("poste_energia", Vector2i(4, 0), 0)
	var g := m.colocar("gerador", Vector2i(6, 0), 0)
	var ac := m.colocar("acumulador", Vector2i(6, 3), 0)
	var forn := m.colocar("fornalha", Vector2i(20, 0), 0)
	verificar(cu >= 0 and ac >= 0 and forn >= 0, "montagem")
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[g] = 100.0
	f.tick(0.1)
	var cl := ClimaLocal.new(m)
	cl.energia = f.energia
	cl.atualizar()
	igual(cl.zonas.size(), 1, "cúpula ligada na rede")
	var r := Raios.new(m, 3)
	r.fabrica = f
	r.clima_local = cl
	var danos := {}
	r.dano = func(id: int, p: float) -> void: danos[id] = p
	var q := r.cair(Vector2(21.0, 1.0))                             # em cima da fornalha, a ~20 m
	igual(q.tipo, "cupula", "a cúpula pegou")
	verificar(danos.is_empty(), "a fornalha a 20 m ficou inteira")
	verificar(float(q.alt) > 20.0, "bate no campo, alto (%.1f m)" % float(q.alt))
	verificar((q.ponta as Vector3).z > 8.0, "e desce até o cristal")
	perto(float(f.acumulado[ac]), 80.0, 1e-3, "a descarga foi para o acumulador (cheio)")
	igual(int(r.descargas[cu]), 1, "contador da cúpula")
	igual(r.cair(Vector2(35.0, 1.0)).tipo, "chao", "fora dos 30 m, cai")
	f.combustivel[g] = 0.0
	f.acumulado[ac] = 0.0
	f.rede.nos[ac].acum_mj = 0.0
	for i in 3:
		f.tick(0.1)
	cl.atualizar()
	verificar(cl.zonas.is_empty(), "sem energia a cúpula apaga")
	igual(r.cair(Vector2(21.0, 1.0)).tipo, "estrutura", "e o raio volta a pegar a fornalha")


func test_regulador() -> void:
	var m := _mapa()
	var rg := m.colocar("regulador_clima", Vector2i(0, 0), 0)
	var forn := m.colocar("fornalha", Vector2i(40, 0), 0)
	verificar(rg >= 0 and forn >= 0, "montagem")
	var cl := _clima(m)
	cl.atualizar()
	var p := Vector2(41.0, 1.0)
	perto(cl.chuva_em(p, 1.0), 0.0, 1e-6, "céu firme: sem chuva nem na tempestade")
	verificar(cl.sem_raio(p) and cl.sem_tufao(p), "sem raio e sem tufão")
	verificar(cl.vento_em(p, Vector2(1, 0), 1.5).length() <= 0.4 + 1e-6, "vento manso")
	var r := Raios.new(m, 3)
	r.clima_local = cl
	var danos := {}
	r.dano = func(id: int, pt: float) -> void: danos[id] = pt
	igual(r.cair(p).tipo, "nenhum", "o raio não cai no raio do regulador")
	igual(r.total, 0, "não conta")
	verificar(danos.is_empty(), "nada atingido")
	m.estruturas[rg]["modo_clima"] = "chuva"
	cl.atualizar()
	perto(cl.chuva_em(p, 0.0), 0.4, 1e-6, "chuva mansa (40%) no céu limpo")
	perto(cl.chuva_em(p, 1.0), 0.4, 1e-6, "e na tempestade também (estabiliza)")
	verificar(cl.sem_raio(p), "sem raio")
	perto(cl.chuva_em(Vector2(90, 1), 1.0), 1.0, 1e-6, "fora dos 80 m, o planeta")


# ------------------------------------------------------------------ desenho
func _raiz() -> Node:
	return (Engine.get_main_loop() as SceneTree).root


func test_desenho_cupula_e_chuva() -> void:
	var m := _mapa()
	var cu := m.colocar("cupula_raios", Vector2i(0, 0), 0)
	m.colocar("semeador_nuvens", Vector2i(10, 0), 0)
	var cl := _clima(m)
	cl.atualizar()
	var r := Raios.new(m, 3)
	r.clima_local = cl
	var d := DesenhoClimaLocal.new()
	d.clima_local = cl
	d.raios = r
	var c := Clima.new(5)
	c.forcar("limpo", true)
	d.clima = c
	_raiz().add_child(d)
	d._process(0.016)
	igual(d.contagem(), {"cupulas": 1, "chuvas": 1}, "uma cúpula e uma chuva local")
	var no: MeshInstance3D = d._cupulas[cu].no
	perto((no.mesh as SphereMesh).radius, 30.0, 1e-6, "cúpula de 30 m")
	verificar((no.mesh as SphereMesh).is_hemisphere, "meia esfera")
	verificar(no.material_override is ShaderMaterial, "campo (shader), não filtro")
	var chuva: GPUParticles3D = d._chuvas.values()[0]
	verificar(chuva.emitting, "chove só no círculo do semeador")
	perto((chuva.process_material as ParticleProcessMaterial).emission_ring_radius, 40.0, 1e-6, "anel de 40 m")
	r.cair(Vector2(5, 5))
	d._process(0.016)
	verificar(float(d._cupulas[cu].impacto) > 0.9, "o raio acende a cúpula")
	c.forcar("tempestade", true)
	d._process(0.016)
	verificar(not chuva.emitting, "chovendo forte no planeta, a chuva do semeador some (não dobra)")
	cl.zonas.clear()
	d._process(0.016)
	igual(d.contagem(), {"cupulas": 0, "chuvas": 0}, "sem energia, nada")
	d.queue_free()
