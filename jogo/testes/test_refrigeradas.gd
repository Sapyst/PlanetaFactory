extends Caso
## Receitas refrigeradas (fase 2.3, decisão A de Sapyst): fundir aço e lapidar cristal continuam sem água (fornalha e
## montadora); a pesquisa "Água como insumo" (bomba_agua) libera as versões refrigeradas, com +50% de produto, que
## rodam no refinador (a máquina das receitas com fluido: a fornalha e a montadora não têm boca de cano) bebendo água
## pela boca oeste. Água limpa serve onde a receita pede água.


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-10, 14):
		for y in range(-10, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _cano_na_porta(c: Construtor, id: int, nome_porta: String, comp := 3) -> Vector2i:
	var e: Dictionary = c.mapa.estruturas[id]
	for pt in Registro.modelos[e.nome].portas:
		if pt.nome == nome_porta:
			var p := Grade.porta_no_mundo(pt, e.minimo, e.area, e.rot)
			var d := Grade.DIRECOES.find(p.dir)
			c.executar(c.plano_linha("cano", p.tile_fora, p.tile_fora + p.dir * (comp - 1), Construtor.rot_do_fluxo(d)))
			return p.tile_fora
	return Vector2i(9999, 0)


func _rodar(f: Fabrica, id: int, s: float, passo := 0.5) -> void:
	var m: Maquina = f.maquinas[id]
	for i in int(s / passo):
		m.energia = 1.0
		f._tick_fluidos(passo)
		m.tick(passo)


func test_mais_cinquenta_por_cento() -> void:
	var r := Registro.receitas
	var aco := float(r.fundir_aco.saidas.barra_aco) / float(r.fundir_aco.entradas.placa_ferro)
	var aco_r := float(r.aco_refrigerado.saidas.barra_aco) / float(r.aco_refrigerado.entradas.placa_ferro)
	perto(aco_r / aco, 1.5, 1e-6, "aço refrigerado: +50% de barras pelas mesmas placas")
	perto(float(r.aco_refrigerado.entradas_fluido.agua) / float(r.aco_refrigerado.saidas.barra_aco), 20.0, 1e-6, "20 de água por barra (PLANO_CLIMA)")
	var lap := float(r.lapidar.saidas.cristal_lapidado) / float(r.lapidar.entradas.cristal_bruto)
	var lap_r := float(r.lapidar_refrigerado.saidas.cristal_lapidado) / float(r.lapidar_refrigerado.entradas.cristal_bruto)
	perto(lap_r / lap, 1.5, 1e-6, "lapidação refrigerada: +50% de cristal")
	perto(float(r.lapidar_refrigerado.entradas_fluido.agua) / float(r.lapidar_refrigerado.saidas.cristal_lapidado), 10.0, 1e-6, "10 de água por cristal")
	for k in ["aco_refrigerado", "lapidar_refrigerado"]:
		igual(r[k].maquina, "refinador", "%s roda no refinador (boca de cano)" % k)


func test_sem_agua_continua_igual() -> void:
	var r := Registro.receitas
	verificar(not r.fundir_aco.has("entradas_fluido"), "fundir aço continua sem água")
	verificar(not r.lapidar.has("entradas_fluido"), "lapidar continua sem água")
	igual(r.fundir_aco.maquina, "fornalha")
	igual(r.lapidar.maquina, "montadora")
	var p := Pesquisa.new()
	verificar(p.receita_liberada("lapidar"), "lapidar liberada desde o início")
	p.concluidas = {"aco": true}
	verificar(p.receita_liberada("fundir_aco"), "aço sem água com a pesquisa Aço")
	verificar(not p.receita_liberada("aco_refrigerado") and not p.receita_liberada("lapidar_refrigerado"), "refrigeradas só com a bomba d'água")


func test_refinador_tempera_com_agua_do_cano() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("refinador", Vector2i(0, 0), 0)
	var fora := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_O1", 3)
	f.reconstruir()
	var rede := f.rede_de(c.mapa.tiles[fora])
	verificar(not rede.is_empty(), "cano na boca oeste do refinador")
	rede.fluido = "agua"
	rede.qtd = 300.0
	f.escolher_receita(id, "aco_refrigerado")
	var m: Maquina = f.maquinas[id]
	for i in 10:
		verificar(m.receber("placa_ferro"), "aceita placa %d" % i)
	_rodar(f, id, 33.0)
	igual(int(m.saidas.get("barra_aco", 0)), 3, "10 placas viraram 3 barras")
	perto(float(rede.qtd) + float(m.fluidos.get("agua", 0.0)), 240.0, 0.5, "gastou 60 de água")
	# sem água para: as placas esperam
	rede.qtd = 0.0
	rede.fluido = ""
	m.fluidos.clear()
	for i in 10:
		m.receber("placa_ferro")
	m.saidas.clear()
	_rodar(f, id, 40.0)
	igual(m.estado, Maquina.Estado.SEM_INSUMO, "sem água espera")
	igual(int(m.saidas.get("barra_aco", 0)), 0, "sem água não sai barra")


func test_lapidar_com_agua_limpa() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var id := c.mapa.colocar("refinador", Vector2i(0, 0), 0)
	var fora := _cano_na_porta(c, id, "PORTA_FLUIDO_ENT_O1", 2)
	f.reconstruir()
	var rede := f.rede_de(c.mapa.tiles[fora])
	rede.fluido = "agua_limpa"
	rede.qtd = 200.0
	f.escolher_receita(id, "lapidar_refrigerado")
	var m: Maquina = f.maquinas[id]
	for i in 8:
		m.receber("cristal_bruto")
	_rodar(f, id, 9.0)
	igual(int(m.saidas.get("cristal_lapidado", 0)), 6, "8 brutos → 6 lapidados (água limpa serve como água)")
	verificar(Registro.fluido_serve("agua_limpa", "agua"), "água limpa serve como água")
	verificar(not Registro.fluido_serve("agua", "agua_limpa"), "água comum não serve como limpa")
	verificar(not Registro.fluido_serve("seiva", "agua"), "seiva não é água")
