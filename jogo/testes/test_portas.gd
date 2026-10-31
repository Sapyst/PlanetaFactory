extends Caso
## Girar estrutura já construída, porta solta/ligada (Portas) e frente do braço.


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 16):                                      # tira pedras e árvores da área dos testes
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_girar_quadrada_mantem_id_e_area() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	verificar(id >= 0, "colocou")
	verificar(m.girar(id), "girou")
	igual(m.estruturas[id].rot, 3, "um quarto horário")
	igual(m.estruturas[id].minimo, Vector2i(2, 2), "quadrada: mesmo canto")
	igual(m.tiles.get(Vector2i(3, 3), -1), id, "mesmos tiles")
	for i in 3:
		m.girar(id)
	igual(m.estruturas[id].rot, 0, "volta inteira")


func test_girar_bloqueado_por_vizinho() -> void:
	var m := _mapa()
	var id := m.colocar("estacao", Vector2i(10, 0), 0)          # 2×3: girada vira 3×2
	verificar(id >= 0, "colocou a estação")
	var c := Grade.centro_da_area(m.estruturas[id].minimo, m.estruturas[id].area, 0)
	var bloqueio := m.colocar("bau", Vector2i(floori(c.x) + 1, floori(c.y)), 0)
	verificar(bloqueio >= 0, "baú encostado")
	verificar(not m.girar(id), "não gira por cima do baú")
	igual(m.estruturas[id].rot, 0, "continua como estava")


func test_porta_solta_e_ligada() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	var soltas := Portas.soltas(m, id)
	igual(soltas.size(), 2, "fornalha sozinha: entrada e saída soltas")
	# esteira encostada na saída norte
	var saida: Dictionary = {}
	for p in Registro.modelos.fornalha.portas:
		if p.io == "SAI":
			saida = p
	var pm := Grade.porta_no_mundo(saida, m.estruturas[id].minimo, m.estruturas[id].area, 0)
	verificar(m.colocar("esteira_reta", pm.tile_fora, 0) >= 0, "esteira na saída")
	igual(Portas.soltas(m, id).size(), 1, "só a entrada continua solta")


func test_braco_serve_por_qualquer_lado() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	# braço a oeste soltando para dentro (frente para leste: rot 3)
	var b := m.colocar("braco", Vector2i(1, 2), 3)
	igual(Portas.frente_braco(m.estruturas[b]), Vector2i(2, 2), "frente do braço girado para leste")
	verificar(Portas.braco_serve(m, m.estruturas[id], true), "braço alimenta pela lateral")
	var tem_ent := false
	for s in Portas.soltas(m, id):
		tem_ent = tem_ent or s.io == "ENT"
	verificar(not tem_ent, "entrada atendida pelo braço não aparece como solta")


## Aviso da estrutura pronta: marcador no tile exato da porta (tile_fora), item e fluido; some quando atendida.
func test_marcador_no_tile_da_porta() -> void:
	var m := _mapa()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	var e: Dictionary = m.estruturas[id]
	var avisos := DesenhoPortas.avisos(m)
	igual(avisos.size(), 2, "as duas portas da fornalha")
	for p in Registro.modelos.fornalha.portas:
		var pm := Grade.porta_no_mundo(p, e.minimo, e.area, e.rot)
		var achou := false
		for a in avisos:
			achou = achou or (a.tile_fora == pm.tile_fora and a.io == p.io)
		verificar(achou, "marcador em %s" % pm.tile_fora)
		verificar(not Grade.tiles_da_area(e.minimo, e.area, e.rot).has(pm.tile_fora), "fora da estrutura")
	igual(MarcadorPortas.direcao_fluxo(Vector2i(0, 1), "SAI"), Vector2i(0, 1), "saída: seta para fora")
	igual(MarcadorPortas.direcao_fluxo(Vector2i(0, 1), "ENT"), Vector2i(0, -1), "entrada: seta para dentro")
	for a in avisos:                                                # atendidas uma a uma: some
		verificar(m.colocar("esteira_reta", a.tile_fora, 0) >= 0, "esteira na porta")
	igual(DesenhoPortas.avisos(m).size(), 0, "tudo atendido: nenhum marcador")


func test_marcador_multimesh() -> void:
	var t := MarcadorPortas.transform_de({"tile_fora": Vector2i(3, -2), "dir": Vector2i(1, 0), "io": "SAI"})
	perto(t.origin.x, 3.5, 1e-4, "centro do tile em x")
	perto(t.origin.z, 1.5, 1e-4, "centro do tile em z (−y da grade)")
	var frente: Vector3 = t.basis * Vector3(0, 0, -1)                # a seta do shader aponta para −Z local
	perto(frente.x, 1.0, 1e-4, "saída para leste: seta para +x")
	perto(frente.z, 0.0, 1e-4, "saída para leste: nada em z")
	var t2 := MarcadorPortas.transform_de({"tile_fora": Vector2i(0, 0), "dir": Vector2i(0, 1), "io": "ENT"})
	perto((t2.basis * Vector3(0, 0, -1)).z, 1.0, 1e-4, "entrada na porta norte: seta para o sul (+z do mundo)")
	var mm := MarcadorPortas.new()
	mm.definir([{"tile_fora": Vector2i(3, -2), "dir": Vector2i(1, 0), "io": "SAI", "tipo": "FLUIDO"}])
	igual(mm.multimesh.instance_count, 1, "um por porta")
	verificar(mm.visible, "com aviso: visível")
	mm.definir([])
	verificar(not mm.visible, "sem aviso: invisível")
	mm.free()


## Fluido: braço não atende (só carrega item); cano atende; esteira não vale para porta de fluido.
func test_porta_de_fluido() -> void:
	var nome := ""
	var porta_f := {}
	for n in Registro.modelos:
		if not Portas.mostra_aviso(n) or not Registro.estruturas.has(n) or Registro.estruturas[n].has("requer_jazida") or Registro.estruturas[n].get("no_rio", false) or Registro.estruturas[n].get("perto_agua", false) or Registro.estruturas[n].get("tomada_agua", false):
			continue
		for p in Registro.modelos[n].get("portas", []):
			if p.tipo == "FLUIDO":
				nome = n
				porta_f = p
		if nome != "":
			break
	verificar(nome != "", "há máquina com porta de fluido")
	if nome == "":
		return
	var m := _mapa()
	var id := m.colocar(nome, Vector2i(2, 2), 0)
	verificar(id >= 0, "colocou " + nome)
	var e: Dictionary = m.estruturas[id]
	var pm := Grade.porta_no_mundo(porta_f, e.minimo, e.area, e.rot)
	var solta := func() -> bool:
		for s in Portas.soltas(m, id):
			if s.tile_fora == pm.tile_fora and s.tipo == "FLUIDO":
				return true
		return false
	verificar(solta.call(), "porta de fluido solta aparece")
	var est := m.colocar("esteira_reta", pm.tile_fora, 0)
	verificar(solta.call(), "esteira não atende fluido")
	m.remover(est)
	m.colocar("cano_reto", pm.tile_fora, 0)
	verificar(not solta.call(), "cano atende")


func _item(nome: String, tile: Vector2i, rot := 0) -> Dictionary:
	return {"nome": nome, "minimo": tile, "rot": rot, "motivo": "", "acao": "colocar"}


func _plano(it: Dictionary) -> Array[Dictionary]:
	var p: Array[Dictionary] = [it]
	return p


## Fantasma: verde onde já encaixa, vermelho onde falta, na mesma regra do aviso depois de construído.
func test_fantasma_verde_e_vermelho() -> void:
	var m := _mapa()
	var plano := _plano(_item("fornalha", Vector2i(2, 2)))
	var mk := Fantasma.marcadores(plano, m)
	igual(mk.size(), 2, "duas portas")
	for k in mk:
		igual(k.cor, MarcadorPortas.VERMELHO, "sem nada: em falta")
	# esteira exatamente no tile da saída: só ela fica verde
	var sai: Dictionary = mk[0] if mk[0].io == "SAI" else mk[1]
	m.colocar("esteira_reta", sai.tile_fora, 0)
	mk = Fantasma.marcadores(plano, m)
	for k in mk:
		igual(k.cor, MarcadorPortas.VERDE if k.io == "SAI" else MarcadorPortas.VERMELHO, "porta %s" % k.io)
	# girar muda onde a porta cai: a mesma esteira deixa de encaixar
	var girado := _plano(_item("fornalha", Vector2i(2, 2), 2))
	for k in Fantasma.marcadores(girado, m):
		if k.io == "SAI":
			igual(k.cor, MarcadorPortas.VERMELHO, "girada: saída noutro lado, em falta")
	# braço servindo a entrada por qualquer lado também é verde
	m.colocar("braco", Vector2i(1, 2), 3)
	for k in Fantasma.marcadores(plano, m):
		if k.io == "ENT":
			igual(k.cor, MarcadorPortas.VERDE, "braço alimenta: verde")
	# construída: o que estava verde não avisa, o que estava vermelho avisa
	var verdes := Fantasma.marcadores(plano, m).filter(func(k): return k.ok).size()
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	igual(Portas.soltas(m, id).size(), 2 - verdes, "fantasma e aviso concordam")


func test_fantasma_sem_marcador_onde_nao_cabe() -> void:
	var m := _mapa()
	igual(Fantasma.marcadores(_plano(_item("bau", Vector2i(2, 2))), m).size(), 0, "baú: portas opcionais")
	igual(Fantasma.marcadores(_plano(_item("nucleo", Vector2i(2, 2))), m).size(), 0, "núcleo: sem aviso")
	igual(Fantasma.marcadores(_plano(_item("torre_defesa", Vector2i(2, 2))), m).size(), 0, "torre de energia: sem aviso")
	igual(Fantasma.marcadores(_plano(_item("esteira_reta", Vector2i(2, 2))), m).size(), 0, "esteira: só setas")
	igual(Fantasma.marcadores(_plano(_item("fornalha", Vector2i(2, 2))), m, true).size(), 0, "removendo: nada")


func _motivo(m: MapaOcupacao, nome: String, t: Vector2i, motivo: String) -> Array[Dictionary]:
	var it := _item(nome, t)
	it.motivo = motivo
	return Bloqueios.do_item(m, it)


## Motivos curtos e quais tiles atrapalham.
func test_bloqueios() -> void:
	var m := _mapa()
	igual(Bloqueios.do_item(m, _item("fornalha", Vector2i(2, 2))).size(), 0, "pode: nada")
	# ocupado: só o tile do baú, com o nome dele
	m.colocar("bau", Vector2i(3, 3), 0)
	var mf := Registro.area("fornalha")
	var plano := _plano(_item("fornalha", Vector2i(2, 2)))
	plano[0].motivo = m.motivo_bloqueio("fornalha", Vector2i(2, 2), 0)
	igual(plano[0].motivo, "ocupado", "motivo do mapa")
	var r := Bloqueios.resumo(m, plano)
	igual(r.size(), 1, "um motivo")
	igual(r[0].texto, "ocupado: " + Registro.menu.rotulos.bau, "diz quem ocupa")
	igual(r[0].tiles.size(), 1, "só o tile que atrapalha, de %s" % mf)
	igual(r[0].tiles[0], Vector2i(3, 3), "o tile do baú")
	igual(_motivo(m, "fornalha", Vector2i(2, 2), "bloqueado")[0].texto, "sem pesquisa", "pesquisa")
	igual(_motivo(m, "fornalha", Vector2i(2, 2), "sem_recursos")[0].texto, "falta material", "material")
	igual(_motivo(m, "fornalha", Vector2i(2, 2), "sem_recursos").size(), mf.x * mf.y, "material: a pegada inteira")
	# obstáculo e água de verdade: procura no mundo
	var g2 := GeradorMundo.new(1337)
	var m2 := MapaOcupacao.new(g2)
	var achou := {}
	for x in range(-300, 300):
		for y in range(-300, 300, 3):
			var t := Vector2i(x, y)
			var o := g2.distribuicao.obstaculo(t)
			if not o.is_empty():
				var nm: String = Bloqueios.nome_obstaculo(String(o.nome))
				if not achou.has(nm):
					achou[nm] = t
			elif g2.eh_agua(g2.terreno(t)) and not achou.has("água"):
				achou["água"] = t
	verificar(achou.has("árvore"), "o mundo tem árvore")
	verificar(achou.has("rocha"), "o mundo tem rocha")
	verificar(achou.has("água"), "o mundo tem água")
	for nm in ["árvore", "rocha"]:
		if achou.has(nm):
			var b := _motivo(m2, "esteira_reta", achou[nm], "obstaculo")
			igual(b[0].texto, nm, "obstáculo em %s" % achou[nm])
			igual(b[0].tile, achou[nm], "no tile certo")
	if achou.has("água"):
		igual(_motivo(m2, "esteira_reta", achou["água"], "agua")[0].texto, "água", "água")
	igual(Bloqueios.nome_peca("esteira_curva_e"), Registro.menu.rotulos.get("esteira", "Esteira"), "variante cai na família")


## Traço com dois motivos: agrupa, sem repetir tile.
func test_bloqueios_resumo_traco() -> void:
	var m := _mapa()
	m.colocar("bau", Vector2i(3, 3), 0)
	var a := _item("esteira_reta", Vector2i(3, 3))
	a.motivo = "ocupado"
	var b := _item("esteira_reta", Vector2i(4, 3))
	b.motivo = "sem_recursos"
	var c := _item("esteira_reta", Vector2i(5, 3))
	c.motivo = "sem_recursos"
	var ok := _item("esteira_reta", Vector2i(6, 3))
	var plano: Array[Dictionary] = [a, b, c, ok]
	var r := Bloqueios.resumo(m, plano)
	igual(r.size(), 2, "dois motivos")
	igual(r[1].texto, "falta material", "segundo motivo")
	igual(r[1].tiles.size(), 2, "dois tiles sem material")
