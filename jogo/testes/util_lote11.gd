class_name UtilLote11
extends RefCounted
## Ajudantes dos testes do lote 11 (produção II): conferência do modelo e chão livre para montar a fábrica de teste.


static func modelo(c: Caso, nome: String, bocas: Array, area := Vector2i(3, 3), menu := "Produção") -> void:
	var md: Dictionary = Registro.modelos.get(nome, {})
	c.igual(Registro.area(nome), area, "tamanho na grade (árvore)")
	c.igual(md.get("estudo", ""), "estudo_%s.py" % nome, "convertido do estudo do Antigravity")
	c.verificar(bool(md.get("anima", false)), "anima (laço do estudo)")
	c.verificar(float(md.dims[0]) <= area.x + 0.1 and float(md.dims[1]) <= area.y + 0.1, "cabe na área (%s)" % str(md.dims))
	c.verificar(int(md.tris) <= 8500, "orçamento (%d triângulos)" % md.tris)
	var nomes: Array = md.get("portas", []).map(func(p): return p.nome)
	nomes.sort()
	var esperado := bocas.duplicate()
	esperado.sort()
	c.igual(nomes, esperado, "bocas do estudo")
	c.verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	c.verificar(ResourceLoader.exists("res://assets/icones/%s.png" % nome), "ícone na barra")
	c.verificar(Registro.menu.categorias.any(func(cat): return cat.nome == menu and nome in cat.pecas), "no menu (%s)" % menu)
	c.verificar(Registro.menu.rotulos.has(nome) and Registro.menu.explicacoes.has(nome), "rótulo e explicação")
	c.verificar(not Registro.progressao.custos.get(nome, {}).is_empty(), "custo de construção")


## Pesquisa da peça: ligada, fora do em desenvolvimento, custo igual ao da árvore, trava até os pré-requisitos, libera.
static func pesquisa(c: Caso, id: String, peca: String) -> void:
	var p := Pesquisa.new()
	c.verificar(p.jogavel(id) and bool(p.arvore()[id].get("existente", false)), "%s ligada e marcada na árvore" % id)
	c.verificar(not p.em_desenvolvimento(id), "fora do em desenvolvimento")
	var esperado := {}
	for par in p.arvore()[id].pacotes:
		esperado[Pesquisa.TIPOS_PACOTE[par[0]]] = int(par[1])
	c.igual(p.custo(id), esperado, "custo da árvore")
	c.verificar(not p.disponivel(id), "começa travada")
	for r in p.pesquisas()[id].requer:
		p.concluidas[r] = true
	c.verificar(p.disponivel(id), "com os pré-requisitos: pesquisável")
	if peca != "":
		c.verificar(not p.peca_liberada(peca), "a peça espera a pesquisa")
		p.concluidas[id] = true
		c.verificar(p.peca_liberada(peca), "libera a peça")
		c.verificar(not Pesquisa.new().peca_em_desenvolvimento(peca), "a peça não fica em cinza")


## Canto de um quadrado w×w de chão (TERRA, nível único, limpo). (9999, 0) se não achou.
static func chao(m: MapaOcupacao, w := 22) -> Vector2i:
	for r in range(30, 400, 4):
		for k in 24:
			var t := Vector2i((Vector2.from_angle(k * TAU / 24.0) * r).round())
			var ok := true
			for i in w:
				for j in w:
					var q := t + Vector2i(i, j)
					if m.gerador.terreno(q) != GeradorMundo.Terreno.TERRA or m.gerador.nivel(q) != m.gerador.nivel(t) or m.gerador.em_encosta(q) or m.tiles.has(q):
						ok = false
						break
				if not ok:
					break
			if ok:
				for i in w:
					for j in w:
						m.limpar_obstaculo(t + Vector2i(i, j))
				return t
	return Vector2i(9999, 0)


## Fonte de sobra (núcleo de singularidade) + poste ligando tudo em volta de `o`.
static func energia(m: MapaOcupacao, o: Vector2i) -> void:
	m.colocar("nucleo_singularidade", o, 0)
	for x in [3, 8, 13, 18]:
		m.colocar("poste_energia", o + Vector2i(x, 4), 0)


## Canto de um 3×3 sobre a jazida (de um dos `tipos`), com o sul e o leste livres.
static func jazida(m: MapaOcupacao, nome: String) -> Vector2i:
	var tipos: Array = Registro.estruturas[nome].requer_jazida
	for r in range(5, 500):
		for k in 48:
			var t := Vector2i((Vector2.from_angle(k * TAU / 48.0) * r).round())
			var j := m.gerador.distribuicao.jazida(t + Vector2i(1, 1))
			if j.is_empty() or not j.tipo in tipos:
				continue
			for x in range(-8, 12):
				for y in range(-8, 8):
					m.limpar_obstaculo(t + Vector2i(x, y))
			if m.motivo_bloqueio(nome, t, 0) == "":
				return t
	return Vector2i(9999, 0)
