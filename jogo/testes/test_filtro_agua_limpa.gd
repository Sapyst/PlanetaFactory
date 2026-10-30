extends Caso
## Filtro que devolve água (pesquisa filtro_agua_limpa, fase 2.3): o filtro de água continua limpando o rio e passa a
## soltar água limpa (fluido "agua_limpa", 15/s) pela boca de cano que o modelo já tinha; sem cano (ou com a rede
## cheia) a sobra volta ao rio e ele não para de limpar. Água limpa serve onde a receita pede água.


func _base() -> Array:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var f := Fabrica.new(m)
	return [g, m, f, AmbienteVivo.new(g, m, 3), Construtor.new(m)]


func _margem(g: GeradorMundo, m: MapaOcupacao) -> Vector2i:
	for x in range(-300, 300, 2):
		for y in range(-300, 300, 2):
			var t := Vector2i(x, y)
			if g.terreno(t) == GeradorMundo.Terreno.TERRA and g.terreno(t + Vector2i(2, 0)) == GeradorMundo.Terreno.RIO:
				for dx in 2:
					for dy in 2:
						m.limpar_obstaculo(t + Vector2i(dx, dy))
				if m.motivo_bloqueio("filtro_agua", t, 0) == "":
					return t
	return Vector2i(9999, 0)


func test_pesquisa_e_dados() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("filtro_agua_limpa"), "jogável")
	p.concluidas = {"bomba_agua": true}
	verificar(not p.disponivel("filtro_agua_limpa"), "precisa de Limpeza")
	p.concluidas["limpeza"] = true
	verificar(p.disponivel("filtro_agua_limpa"), "bomba d'água + limpeza")
	igual(p.custo("filtro_agua_limpa"), {"pacote_pesquisa": 20, "pacote_automacao": 20})
	verificar(not p.receita_liberada("filtrar_agua_limpa"), "antes, só limpa")
	p.concluidas["filtro_agua_limpa"] = true
	verificar(p.receita_liberada("filtrar_agua_limpa"), "depois, devolve água")
	igual(int(Registro.receitas.filtrar_agua_limpa.saidas_fluido.agua_limpa), 15, "15 de água limpa/s")
	var portas: Array = Registro.modelos.filtro_agua.portas
	verificar(portas.any(func(pt): return pt.tipo == "FLUIDO" and pt.io == "SAI"), "o filtro tem boca de cano de saída")
	igual(Registro.nome_fluido("agua_limpa"), "Água limpa")


func test_solta_agua_limpa_e_continua_limpando() -> void:
	var b := _base()
	var g: GeradorMundo = b[0]
	var m: MapaOcupacao = b[1]
	var f: Fabrica = b[2]
	var a: AmbienteVivo = b[3]
	var c: Construtor = b[4]
	var t := _margem(g, m)
	verificar(t.x != 9999, "lugar na margem")
	var id := m.colocar("filtro_agua", t, 0)
	var p := Pesquisa.new()
	f.pesquisa = p
	f.reconstruir()
	f._aplicar_melhorias()
	igual(f.maquinas[id].receita_id, "filtrar_agua", "sem a pesquisa, só limpa")
	p.concluidas = {"limpeza": true, "bomba_agua": true, "filtro_agua_limpa": true}
	f._aplicar_melhorias()
	var mq: Maquina = f.maquinas[id]
	igual(mq.receita_id, "filtrar_agua_limpa", "com a pesquisa, solta água limpa")
	# sem cano: transborda (a sobra volta ao rio) e continua trabalhando
	for i in 30:
		mq.energia = 1.0
		mq.tick(1.0)
	igual(mq.estado, Maquina.Estado.TRABALHANDO, "sem cano não trava")
	verificar(float(mq.fluidos.get("agua_limpa", 0.0)) <= mq.limite_fluido("agua_limpa") + 1e-6, "guarda só o limite")
	for x in range(-4, 7):
		for y in range(-4, 7):
			if g.eh_agua(g.terreno(t + Vector2i(x, y))):
				a.somar(t + Vector2i(x, y), AmbienteVivo.AGUA, 0.6)
	a.tick(1.0, f, null)
	var antes := a.valor(t + Vector2i(2, 0), AmbienteVivo.AGUA)
	for i in 10:
		mq.energia = 1.0
		mq.tick(1.0)
		a.tick(1.0, f, null)
	verificar(a.valor(t + Vector2i(2, 0), AmbienteVivo.AGUA) < antes, "continua limpando o rio")
	# com cano na boca de saída: a água limpa vai para a rede
	var pt: Dictionary = {}
	for q in Registro.modelos.filtro_agua.portas:
		if q.tipo == "FLUIDO" and q.io == "SAI":
			pt = Grade.porta_no_mundo(q, Vector2i(t), Vector2i(2, 2), 0)
	if g.eh_agua(g.terreno(pt.tile_fora)) or not m.motivo_bloqueio("cano_reto", pt.tile_fora, 0) in ["", "obstaculo"]:
		return                                       # a boca dá na água neste lugar: o resto já foi conferido
	m.limpar_obstaculo(pt.tile_fora)
	c.executar(c.plano_linha("cano", pt.tile_fora, pt.tile_fora, Construtor.rot_do_fluxo(Grade.DIRECOES.find(pt.dir))))
	f.reconstruir()
	var rede := f.rede_de(m.tiles.get(pt.tile_fora, -1))
	verificar(not rede.is_empty(), "cano encostado na boca do filtro")
	for i in 5:
		mq.energia = 1.0
		mq.tick(1.0)
		f._tick_fluidos(1.0)
	igual(rede.get("fluido", ""), "agua_limpa", "a rede leva água limpa")
	verificar(float(rede.get("qtd", 0.0)) > 50.0, "água limpa no cano (%.0f)" % float(rede.get("qtd", 0.0)))
