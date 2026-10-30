extends Caso
## Sensor de varredura (sensor_varredura, lote 17): modelo do estudo (estudo_sensor_varredura.py, do Antigravity;
## arte/estudos/conv_lote17.py) com o laço do estudo (giro + antena); pesquisa pela árvore (eletrônica; básico × 20).
## Com energia (150 kW) revela 1 chunk por minuto, do mais perto para o mais longe, até 6 (Varredura profunda —
## cartografia —: 16): o chunk sai da névoa e os ninhos dele passam a existir e ficam marcados. A cartografia destrava
## a artilharia (e a profunda mede a riqueza das jazidas).


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(196, 204):
		for y in range(-4, 4):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


## Mapa + descoberta + colônia + sensor 2×2 em (200, 0) (longe do spawn: há ninhos em volta) + varredura.
func _cena(energia := [1.0], profunda := [false]) -> Dictionary:
	var m := _mapa()
	var d := Descoberta.new()
	var c := Colonia.new(m, Poluicao.new(m.gerador), 3)
	var s := m.colocar("sensor_varredura", Vector2i(200, 0), 0)
	verificar(s >= 0, "sensor coube (%s)" % m.motivo_bloqueio("sensor_varredura", Vector2i(200, 0), 0))
	var v := Varredura.new(m, d)
	v.colonia = c
	v.energia = func(_id: int) -> float: return energia[0]
	v.profunda = func() -> bool: return profunda[0]
	return {"m": m, "d": d, "c": c, "s": s, "v": v}


func _rodar(v: Varredura, segundos: float, dt := 1.0) -> void:
	for i in int(segundos / dt):
		v.tick(dt)


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("sensor_varredura", {})
	verificar(Varredura.eh_sensor("sensor_varredura"), "regra da varredura")
	perto(float(r.varredura.intervalo_s), 60.0, 1e-6, "1 chunk por minuto (árvore)")
	igual(int(r.varredura.chunks), 6, "até 6 chunks (árvore)")
	igual(int(r.varredura.chunks_profunda), 16, "profunda: até 16 chunks (árvore)")
	igual(Fiacao.papel("sensor_varredura"), "consumo", "precisa de energia")
	perto(float(r.energia_kw), 150.0, 1e-6, "150 kW")
	var md: Dictionary = Registro.modelos.get("sensor_varredura", {})
	igual(Registro.area("sensor_varredura"), Vector2i(2, 2), "2×2")
	igual(md.get("estudo", ""), "estudo_sensor_varredura.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (giro e antena do estudo)")
	verificar(float(md.dims[0]) <= 2.01 and float(md.dims[1]) <= 2.01, "não passa da área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 8500, "leve (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas (só energia)")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/sensor_varredura.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "sensor_varredura" in cat.pecas),
			"no menu (categoria nova Proliferação)")
	verificar(not Registro.progressao.custos.get("sensor_varredura", {}).is_empty(), "custo de construção")


func test_modelo_anima_giro_e_antena() -> void:
	var cena: PackedScene = load(str(Registro.modelos.sensor_varredura.modelo))
	var raiz := cena.instantiate()
	var nomes := {}
	for n in raiz.find_children("*", "Node3D", true, false):
		nomes[String(n.name)] = n
	verificar(nomes.has("giro") and nomes.has("antena"), "partes giro e antena do estudo")
	verificar(nomes.has("antena") and (nomes.antena as Node).get_parent() == nomes.get("giro"), "antena presa no giro")
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo")
	if ap != null and ap.has_animation("trabalho"):
		perto(ap.get_animation("trabalho").length, 4.0, 0.1, "laço de 4 s")
	for n in nomes:                                         # o Animador não mexe por cima (só toca o laço)
		var i := String(n).rfind("_")
		var suf := String(n).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor"], "nome neutro: " + n)
	raiz.free()


func test_pesquisa_destrava_cartografia_e_artilharia() -> void:
	var p := Pesquisa.new()
	for id in ["sensor_varredura", "cartografia", "monitor_ambiental", "artilharia"]:
		verificar(p.jogavel(id), "jogável: " + id)
		verificar(not p.em_desenvolvimento(id), "não está mais em desenvolvimento: " + id)
	igual(p.custo("sensor_varredura"), {"pacote_pesquisa": 20}, "custo da árvore (básico × 20)")
	igual(p.custo("cartografia"), {"pacote_pesquisa": 50, "pacote_automacao": 50, "pacote_quimico": 50}, "custo da árvore")
	verificar(not p.disponivel("sensor_varredura"), "travado no início")
	p.concluidas = {"logistica": true, "eletronica": true}
	verificar(p.disponivel("sensor_varredura"), "depois da eletrônica")
	p.concluidas["sensor_varredura"] = true
	verificar(p.peca_liberada("sensor_varredura"), "libera o sensor")
	verificar(not p.modo_liberado("varredura_profunda"), "sem a profunda ainda")
	p.concluidas["limpeza"] = true
	verificar(p.disponivel("monitor_ambiental"), "Leitura ambiental: sensor + limpeza")
	verificar(not p.disponivel("cartografia"), "cartografia espera o processador")
	p.concluidas["processador"] = true
	verificar(p.disponivel("cartografia"), "sensor + processador → cartografia pesquisável")
	p.escolher("cartografia")
	igual(p.ativa, "cartografia", "escolheu a cartografia")
	var fim := ""
	for i in p.unidades("cartografia"):
		var f := p.avancar()
		if f != "":
			fim = f
	igual(fim, "cartografia", "cartografia concluída")
	verificar(p.modo_liberado("varredura_profunda"), "libera a varredura profunda")
	verificar(not p.disponivel("artilharia"), "artilharia ainda pede lança-foguetes e liga leve")
	p.concluidas.merge({"torre_foguetes": true, "liga_leve": true})
	verificar(p.disponivel("artilharia"), "torre_foguetes + liga_leve + cartografia → artilharia pesquisável")
	verificar(not p.peca_em_desenvolvimento("artilharia"), "a artilharia sai de 'em desenvolvimento'")


func test_revela_um_chunk_por_minuto() -> void:
	var c := _cena()
	var v: Varredura = c.v
	var d: Descoberta = c.d
	var s: int = c.s
	var ordem := v.ordem(s)
	igual(ordem.size(), 6, "6 chunks")
	igual(ordem[0], Grade.chunk_de(Vector2i(201, 1)), "o primeiro é o do próprio sensor")
	var cen := v.centro(s)
	for i in range(1, ordem.size()):                     # do mais perto para o mais longe
		var a := ((Vector2(ordem[i - 1]) + Vector2(0.5, 0.5)) * Grade.TAM_CHUNK).distance_to(cen)
		var b := ((Vector2(ordem[i]) + Vector2(0.5, 0.5)) * Grade.TAM_CHUNK).distance_to(cen)
		verificar(a <= b + 1e-3, "ordem por distância (%d)" % i)
	_rodar(v, 59.0)
	igual(v.feitos(s), 0, "antes de 1 min nada")
	verificar(not d.chunk_completo(ordem[0]), "ainda na névoa")
	_rodar(v, 1.0)
	igual(v.feitos(s), 1, "1 min: 1 chunk")
	verificar(d.chunk_completo(ordem[0]) and d.descoberto(Vector2i(201, 1)), "o chunk saiu da névoa")
	verificar(not d.chunk_completo(ordem[1]), "o próximo ainda não")
	perto(v.falta_s(s), 60.0, 1e-3, "próximo em 60 s")
	_rodar(v, 600.0)
	igual(v.feitos(s), 6, "para em 6 chunks")
	verificar(v.falta_s(s) < 0.0, "terminou")
	for k in ordem:
		verificar(d.chunk_completo(k), "revelado %s" % k)
	verificar(not d.chunk_completo(v.ordem(s, 7)[6]), "o 7º fica na névoa")


func test_energia_desligado_e_ja_visto() -> void:
	var en := [0.0]
	var c := _cena(en)
	var v: Varredura = c.v
	var s: int = c.s
	_rodar(v, 300.0)
	igual(v.feitos(s), 0, "sem energia não varre")
	en[0] = 0.5
	_rodar(v, 100.0)
	igual(v.feitos(s), 0, "meia energia: 100 s ainda não deu 1 minuto de trabalho")
	_rodar(v, 20.0)
	igual(v.feitos(s), 1, "120 s com meia energia = 1 chunk")
	en[0] = 1.0
	(c.m as MapaOcupacao).estruturas[s]["desligada"] = true
	_rodar(v, 120.0)
	igual(v.feitos(s), 1, "desligado pelo painel: parado")
	(c.m as MapaOcupacao).estruturas[s].erase("desligada")
	var prox: Vector2i = v.ordem(s)[1]
	(c.d as Descoberta).marcar_chunk(prox)                # o jogador já tinha visto o próximo
	v.tick(0.1)
	igual(v.feitos(s), 2, "chunk já visto entra na hora")
	# na rede de verdade: sem poste, parado; gerador + poste, varre
	var m: MapaOcupacao = c.m
	for x in range(203, 214):
		for y in range(-4, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	var f := Fabrica.new(m)
	f.reconstruir()
	f.tick(0.1)
	v.energia = f.energia
	perto(v.energia_de(s), 0.0, 1e-6, "sem poste: sem energia")
	var g := m.colocar("gerador", Vector2i(208, 0), 0)
	m.colocar("poste_energia", Vector2i(204, 3), 0)
	f.reconstruir()
	f.combustivel[g] = 100.0
	f.tick(0.1)
	verificar(v.energia_de(s) > 0.99, "gerador com combustível + poste: energia plena")


func test_profunda_vai_a_16_e_mede_jazidas() -> void:
	var prof := [false]
	var c := _cena([1.0], prof)
	var v: Varredura = c.v
	var s: int = c.s
	_rodar(v, 6 * 60.0 + 30.0, 2.0)
	igual(v.feitos(s), 6, "nível 1: 6")
	verificar(v.jazidas(s).is_empty(), "sem a profunda não mede jazidas")
	prof[0] = true
	igual(v.limite(s), 16, "profunda: 16")
	var seis: Array = (v.sensores[s].feitos as Array).duplicate()
	_rodar(v, 10 * 60.0 + 30.0, 2.0)
	igual(v.feitos(s), 16, "profunda: chega a 16")
	igual((v.sensores[s].feitos as Array).slice(0, 6), seis, "continua a mesma ordem (não repete os 6)")
	var jz := v.jazidas(s)
	verificar(not jz.is_empty(), "16 chunks longe do spawn têm jazida (%d)" % jz.size())
	for i in jz.size():
		verificar(int(jz[i].total) > 0, "jazida com total")
		verificar(String(jz[i].nivel) in ["pobre", "média", "rica"], "nível de riqueza")
		verificar(float(jz[i].riqueza) >= 1.0, "riqueza ×")
		verificar(v.chunks_cobertos().has(Grade.chunk_de(Vector2i((jz[i].centro as Vector2).floor()))), "centro num chunk revelado")
		if i > 0:
			verificar(int(jz[i - 1].total) >= int(jz[i].total), "da maior para a menor")


func test_marca_ninhos() -> void:
	var c := _cena([1.0], [true])
	var v: Varredura = c.v
	var col: Colonia = c.c
	var m: MapaOcupacao = c.m
	var s: int = c.s
	igual(col.ninhos.size(), 0, "nenhum chunk visto: nenhum ninho ainda")
	verificar(v.ninhos_marcados().is_empty(), "nada marcado")
	_rodar(v, 17 * 60.0, 2.0)
	verificar(not col.ninhos.is_empty(), "revelar cria os ninhos dos chunks (%d)" % col.ninhos.size())
	var marc := v.ninhos_marcados()
	verificar(not marc.is_empty(), "ninhos marcados (%d)" % marc.size())
	for n in marc:
		verificar(v.chunks_cobertos().has(Grade.chunk_de(Vector2i((col.ninhos[n].centro as Vector2).floor()))), "marcado está num chunk revelado")
	igual(v.ninhos_do_sensor(s).size(), marc.size(), "painel: os mesmos do sensor")
	# desenho: um alfinete por ninho marcado, rótulos das jazidas com a profunda
	var dv := DesenhoVarredura.new()
	dv.varredura = v
	(Engine.get_main_loop() as SceneTree).root.add_child(dv)
	dv._process(1.0)
	igual(dv.contagem().ninhos, marc.size(), "uma marca por ninho")
	igual(dv.contagem().jazidas, v.jazidas(s).size(), "um rótulo por jazida medida")
	# tirou o sensor: o mapa continua descoberto, as marcas somem
	var k0: Vector2i = v.ordem(s)[0]
	m.remover(s)
	verificar(v.ninhos_marcados().is_empty(), "sem sensor, sem marcas")
	verificar((c.d as Descoberta).chunk_completo(k0), "o que foi revelado continua descoberto")
	dv._process(1.0)
	igual(dv.contagem(), {"ninhos": 0, "jazidas": 0}, "desenho limpo")
	dv.free()


func test_salvar() -> void:
	var c := _cena()
	var v: Varredura = c.v
	var s: int = c.s
	_rodar(v, 150.0)
	var e := var_to_str(v.estado())                        # como o salvamento grava (texto)
	var v2 := Varredura.new(c.m, c.d)
	v2.restaurar(str_to_var(e))
	igual(v2.feitos(s), 2, "chunks revelados voltam")
	perto(float(v2.sensores[s].t), 30.0, 1e-3, "tempo do próximo volta")
	v2.tick(30.0)
	igual(v2.feitos(s), 3, "continua de onde parou")
