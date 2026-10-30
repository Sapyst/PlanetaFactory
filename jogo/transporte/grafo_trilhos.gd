class_name GrafoTrilhos
extends RefCounted
## Malha ferroviária como grafo de "pontas": cada peça de trilho liga uma porta de entrada a uma de saída
## (pontos no meio da borda de tile). Duas peças se ligam quando as pontas coincidem.
## Rotas por A* (custo = comprimento). Sinais dividem a malha em blocos; um trem reserva os blocos da rota
## à frente e só entra num bloco livre — dois trens nunca ocupam o mesmo bloco.
## Sinal em cadeia (pesquisa trem_automatico) divide igual, mas o trem só passa por ele se também conseguir a SAÍDA:
## os blocos da rota até o próximo sinal comum e o bloco depois dele (Trem._trecho_cadeia) — ninguém para no meio
## do cruzamento.

var arestas: Dictionary = {}       ## ponto (Vector2, chave arredondada) → Array[{para: Vector2, custo: float, peca: int}]
var pecas: Array[Dictionary] = []  ## {nome, a: Vector2, b: Vector2, comprimento, bloco, pontos: PackedVector2Array (de a até b), estrutura}
var sinais: Dictionary = {}        ## ponto → true (sinal na ponta)
var cadeia: Dictionary = {}        ## ponto → true (o sinal da ponta é em cadeia)
var reserva: Dictionary = {}       ## bloco → id do trem
var estacoes: Array[Dictionary] = []   ## {estrutura, ponto: Vector2 (parada no eixo da linha), peca, nome}

const SEG_CURVA := 12
## Peças retas de 1 tile (trem se põe nelas, sinal se encosta nelas): o trilho comum e o energizado (trem_eletrico).
const RETOS := ["trilho_reto", "trilho_energizado"]


static func chave(p: Vector2) -> Vector2:
	return (p * 2.0).round() / 2.0


## Adiciona uma peça a partir das portas no mundo (Grade.porta_no_mundo). Trilho é de mão dupla.
## `pontos` = eixo da peça de a até b (vazio = reta).
## `ponta_morta` = b é um para-choque (não arredonda para não colar no trilho do tile vizinho).
func adicionar_peca(nome: String, a: Vector2, b: Vector2, comprimento: float, pontos := PackedVector2Array(), estrutura := -1, ponta_morta := false) -> int:
	var id := pecas.size()
	a = chave(a)
	b = b if ponta_morta else chave(b)
	if pontos.is_empty():
		pontos = PackedVector2Array([a, b])
	pecas.append({"nome": nome, "a": a, "b": b, "comprimento": comprimento, "bloco": -1, "pontos": pontos, "estrutura": estrutura})
	for par in [[a, b], [b, a]]:
		if not arestas.has(par[0]):
			arestas[par[0]] = []
		arestas[par[0]].append({"para": par[1], "custo": comprimento, "peca": id})
	return id


func adicionar_sinal(p: Vector2, em_cadeia := false) -> void:
	sinais[chave(p)] = true
	if em_cadeia:
		cadeia[chave(p)] = true


## Recalcula blocos: peças ligadas sem atravessar sinal formam um bloco.
func calcular_blocos() -> int:
	for p in pecas:
		p.bloco = -1
	var n := 0
	for i in pecas.size():
		if pecas[i].bloco >= 0:
			continue
		var fila: Array[int] = [i]
		pecas[i].bloco = n
		while not fila.is_empty():
			var k: int = fila.pop_back()
			for ponta in [pecas[k].a, pecas[k].b]:
				if sinais.has(ponta):
					continue
				for ar in arestas.get(ponta, []):
					var j: int = ar.peca
					if pecas[j].bloco < 0:
						pecas[j].bloco = n
						fila.append(j)
		n += 1
	return n


## A* de ponta a ponta. Devolve lista de ids de peça (vazia se não há caminho).
## `proibida` = peça que não pode ser usada (a que está debaixo do trem: não dá meia-volta em cima de si).
func rota(de: Vector2, para: Vector2, proibida := -1) -> Array[int]:
	if not arestas.has(de): de = chave(de)       # para-choque não é arredondado
	if not arestas.has(para): para = chave(para)
	var aberto := {de: 0.0}
	var g := {de: 0.0}
	var veio := {}
	while not aberto.is_empty():
		var atual: Vector2 = aberto.keys()[0]
		for k in aberto:
			if aberto[k] < aberto[atual]:
				atual = k
		if atual == para:
			var caminho: Array[int] = []
			var p := atual
			while veio.has(p):
				caminho.push_front(veio[p][1])
				p = veio[p][0]
			return caminho
		aberto.erase(atual)
		for ar in arestas.get(atual, []):
			if ar.peca == proibida:
				continue
			var ng: float = g[atual] + ar.custo
			if ng < g.get(ar.para, INF):
				g[ar.para] = ng
				veio[ar.para] = [atual, ar.peca]
				aberto[ar.para] = ng + (ar.para as Vector2).distance_to(para)
	return []


## Tenta reservar todos os blocos de um trecho de rota para o trem. Tudo ou nada.
func reservar(trem: int, trecho: Array[int]) -> bool:
	var blocos := {}
	for id in trecho:
		blocos[pecas[id].bloco] = true
	for b in blocos:
		if reserva.has(b) and reserva[b] != trem:
			return false
	for b in blocos:
		reserva[b] = trem
	return true


func liberar(trem: int, bloco := -1) -> void:
	for b in reserva.keys():
		if reserva[b] == trem and (bloco < 0 or b == bloco):
			reserva.erase(b)


# ------------------------------------------------------------------ montar a partir do mapa
## Lê trilhos, sinais e estações já construídos. Curva 3×3 vira arco de raio 2,5 m; fim de linha termina no
## para-choque. Sinal (no tile ao lado da linha) divide os blocos na ponta de entrada do trilho vizinho.
## Estação: a parada fica no eixo da linha encostada a oeste (meio do lado de 3 tiles).
static func de_mapa(mapa: MapaOcupacao) -> GrafoTrilhos:
	var g := GrafoTrilhos.new()
	var sinais_pend: Array[Vector2i] = []
	var cadeia_pend: Dictionary = {}     ## tile do sinal → true (sinal em cadeia)
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		var area := Registro.area(e.nome)
		var c := Grade.centro_da_area(e.minimo, area, e.rot)
		match e.nome:
			"trilho_reto", "trilho_curva", "trilho_fim", "trilho_energizado":
				var portas: Array = Registro.modelos[e.nome].portas
				var a: Vector2 = Grade.porta_no_mundo(portas[0], e.minimo, area, e.rot).pos
				var b: Vector2
				var pts := PackedVector2Array()
				if e.nome in RETOS:
					b = Grade.porta_no_mundo(portas[1], e.minimo, area, e.rot).pos
				elif e.nome == "trilho_fim":
					b = c + Grade.girar(Vector2(0, 0.30), e.rot)          # para-choque
					pts = PackedVector2Array([chave(a), b])
				else:
					b = Grade.porta_no_mundo(portas[1], e.minimo, area, e.rot).pos
					var cc := c + Grade.girar(Vector2(1.5, -1.5), e.rot)   # centro do arco
					var a0 := (a - cc).angle()
					var da := angle_difference(a0, (b - cc).angle())
					for k in SEG_CURVA + 1:
						pts.append(cc + Vector2.from_angle(a0 + da * k / SEG_CURVA) * 2.5)
					pts[0] = chave(a)
					pts[SEG_CURVA] = chave(b)
				var comp := 2.5 * PI / 2.0 if e.nome == "trilho_curva" else a.distance_to(b)
				g.adicionar_peca(e.nome, a, b, comp, pts, id, e.nome == "trilho_fim")
			"sinal_trem", "sinal_cadeia":
				sinais_pend.append(e.minimo)
				if e.nome == "sinal_cadeia":
					cadeia_pend[e.minimo] = true
			"estacao":
				g.estacoes.append({"estrutura": id, "ponto": c + Grade.girar(Vector2(-1.5, 0), e.rot), "peca": -1})
	for t in sinais_pend:
		for d in Grade.DIRECOES:
			var v: int = mapa.tiles.get(t + d, -1)
			if v >= 0 and mapa.estruturas[v].nome in RETOS:
				var e: Dictionary = mapa.estruturas[v]
				var p: Dictionary = Registro.modelos["trilho_reto"].portas[0]
				g.adicionar_sinal(Grade.porta_no_mundo(p, e.minimo, Vector2i.ONE, e.rot).pos, cadeia_pend.has(t))
				break
	for est in g.estacoes:
		est.peca = g.peca_no_ponto(est.ponto).get("peca", -1)
	g.calcular_blocos()
	return g


## Peça cujo eixo passa pelo ponto: {peca, s (distância desde a)} ou {} se nenhuma.
func peca_no_ponto(p: Vector2, tol := 0.05) -> Dictionary:
	for i in pecas.size():
		var pts: PackedVector2Array = pecas[i].pontos
		var acum := 0.0
		for k in pts.size() - 1:
			var q := Geometry2D.get_closest_point_to_segment(p, pts[k], pts[k + 1])
			if q.distance_to(p) <= tol:
				return {"peca": i, "s": acum + pts[k].distance_to(q)}
			acum += pts[k].distance_to(pts[k + 1])
	return {}


## Pontos da peça percorrida a partir da ponta `de` (a ou b).
func pontos_a_partir(peca: int, de: Vector2) -> PackedVector2Array:
	var pts: PackedVector2Array = pecas[peca].pontos
	if de == pecas[peca].a:
		return pts
	var r := PackedVector2Array()
	for i in range(pts.size() - 1, -1, -1):
		r.append(pts[i])
	return r


## Outra ponta da peça.
## (`de` precisa ser uma das pontas exatas da peça; para-choque não é arredondado.)
func outra_ponta(peca: int, de: Vector2) -> Vector2:
	return pecas[peca].b if de == pecas[peca].a else pecas[peca].a
