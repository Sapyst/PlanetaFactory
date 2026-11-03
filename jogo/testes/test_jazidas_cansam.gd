extends Caso
## Testes de Jazidas Cansam (Pedido 4 — Tarefa 5):
## - Jazidas não se esgotam totalmente, mas contam o total extraído.
## - Estados da jazida:
##     * "rica": extração < 12.000 itens (fator 1.0, 100% frequência)
##     * "cansada": 12.000 <= extração < 36.000 itens (fator 0.5, metade da frequência)
##     * "exausta": extração >= 36.000 itens (fator 0.25, 75% de queda na produção)
## - Persistência no save e restauração de partida.
## - Exibição do estado no painel da broca.
## - Regra da broca de núcleo (rende_esgotada = 0.1) mantida.


func _criar_cenario_broca() -> Dictionary:
	var g := GeradorMundo.new(1337)
	g.relevo_ativo = false
	var m := MapaOcupacao.new(g)
	# Achar uma jazida de ferro próxima
	var pos_jazida := Vector2i(9999, 9999)
	for x in range(-25, 25):
		for y in range(-25, 25):
			var t := Vector2i(x, y)
			var j := g.distribuicao.jazida(t)
			if not j.is_empty() and j.tipo == "jazida_ferro":
				m.limpar_obstaculo(t)
				pos_jazida = t
				break
		if pos_jazida.x != 9999:
			break
	var c := Construtor.new(m)
	c.cobrar = false
	var f := Fabrica.new(m)
	return {"mapa": m, "gerador": g, "construtor": c, "fabrica": f, "pos": pos_jazida}


func test_estados_e_fatores_jazida() -> void:
	var cen := _criar_cenario_broca()
	var f: Fabrica = cen.fabrica
	var m: MapaOcupacao = cen.mapa
	var pos: Vector2i = cen.pos
	verificar(pos.x != 9999, "encontrou posição de jazida de ferro")

	var id := m.colocar("broca_minerio", pos, 0)
	verificar(id >= 0, "colocou broca sobre jazida")
	f.reconstruir()

	var ch := f.chave_jazida_da_estrutura(id)
	verificar(ch != "", "broca identificou a chave da jazida: %s" % ch)
	igual(f.estado_jazida(ch), "rica", "jazida nova inicia rica")
	igual(f.fator_producao_jazida(ch), 1.0, "fator inicial é 1.0")

	# Simular extração até 11.999
	f.jazidas_extraido[ch] = 11999
	igual(f.estado_jazida(ch), "rica", "11.999 itens ainda é rica")
	igual(f.fator_producao_jazida(ch), 1.0, "fator 1.0")

	# Passar de 12.000 -> cansada (metade da produção)
	f.jazidas_extraido[ch] = 12000
	igual(f.estado_jazida(ch), "cansada", "12.000 itens transita para cansada")
	igual(f.fator_producao_jazida(ch), 0.5, "fator cai para 0.5 (metade)")

	# 35.999 itens ainda cansada
	f.jazidas_extraido[ch] = 35999
	igual(f.estado_jazida(ch), "cansada", "35.999 itens ainda cansada")
	igual(f.fator_producao_jazida(ch), 0.5, "fator 0.5")

	# Atingir 36.000 itens -> exausta (cai 75%, fica em 25%)
	f.jazidas_extraido[ch] = 36000
	igual(f.estado_jazida(ch), "exausta", "36.000 itens transita para exausta")
	igual(f.fator_producao_jazida(ch), 0.25, "fator cai para 0.25 (25% produção)")

	# Muito além de 36.000 continua exausta sem sumir (não esgota totalmente)
	f.jazidas_extraido[ch] = 100000
	igual(f.estado_jazida(ch), "exausta", "100.000 itens continua produzindo como exausta")
	igual(f.fator_producao_jazida(ch), 0.25, "fator mantém 0.25 sem zerar")


func test_ritmo_minacao_e_acumulo_automatico() -> void:
	var cen := _criar_cenario_broca()
	var f: Fabrica = cen.fabrica
	var m: MapaOcupacao = cen.mapa
	var pos: Vector2i = cen.pos

	var id := m.colocar("broca_minerio", pos, 0)
	var ge := m.colocar("gerador", pos + Vector2i(3, 0), 0)
	m.colocar("poste_energia", pos + Vector2i(2, 0), 0)
	f.reconstruir()
	f.combustivel[ge] = 50.0
	var ch := f.chave_jazida_da_estrutura(id)
	var ext_antes := int(f.jazidas_extraido.get(ch, 0))
	# Simular avanço de produção da máquina
	# Cada ciclo de minerar_ferro leva 2.0s
	for i in 60: # 60 * 0.1s = 6.0s => 3 ciclos
		f.tick(0.1)

	var ext_depois := int(f.jazidas_extraido.get(ch, 0))
	verificar(ext_depois > ext_antes, "extração acumulou automaticamente na jazida (%d -> %d)" % [ext_antes, ext_depois])


func test_persistencia_jazidas_save() -> void:
	var cen := _criar_cenario_broca()
	var f: Fabrica = cen.fabrica
	var ch := "jazida_ferro_-13.0_9.0"

	f.jazidas_extraido[ch] = 25000
	var salvo := f.estado()
	verificar(salvo.has("jazidas_extraido"), "estado da fábrica contém jazidas_extraido")
	igual(int(salvo.jazidas_extraido.get(ch, 0)), 25000, "gravou 25.000 itens extraídos")

	# Restaurar em uma fábrica nova
	var f2 := Fabrica.new(cen.mapa)
	f2.restaurar(salvo)
	igual(int(f2.jazidas_extraido.get(ch, 0)), 25000, "restaurou 25.000 itens extraídos")
	igual(f2.estado_jazida(ch), "cansada", "restaurou estado cansada")


func test_broca_nucleo_mantem_regra() -> void:
	var cen := _criar_cenario_broca()
	var f: Fabrica = cen.fabrica
	var m: MapaOcupacao = cen.mapa
	var pos: Vector2i = cen.pos

	var id := m.colocar("broca_nucleo", pos, 0)
	f.reconstruir()
	var mq: Maquina = f.maquinas[id]
	perto(float(mq.rende_esgotada), 0.1, 1e-6, "broca de núcleo preserva rende_esgotada de 10%")

	# Quando jazida_restante = 0 (regra antiga de esgotamento total para testes)
	mq.jazida_restante = 0
	mq.energia = 1.0
	mq.tick(0.01)
	verificar(mq.estado != Maquina.Estado.SEM_JAZIDA, "broca de núcleo não para com jazida_restante = 0")
