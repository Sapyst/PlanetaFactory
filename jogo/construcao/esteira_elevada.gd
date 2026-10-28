class_name EsteiraElevada
extends RefCounted
## Planeja os pilares de um trecho de esteira elevada (lógica física simples, sem invadir área de construção):
##  - a esteira passa a `nivel` metros (múltiplo de 0,5); embaixo só pode haver estrutura com altura ≤ nivel − FOLGA;
##  - apoio = "pórtico": os 2 cantos da borda de entrada de um tile (um de cada lado da esteira);
##  - vão máximo entre pórticos: VAO_MAX tiles; o planejador tenta o tile ideal e recua/avança 1 se o canto estiver ocupado;
##  - se não achar apoio dentro do vão → o trecho é recusado com o tile do problema.

const NIVEL := 0.5
const FOLGA := 0.25
const VAO_MAX := 4


## caminho: tiles em ordem; direcoes: índice 0..3 (N, L, S, O) do fluxo em cada tile; niveis: altura da esteira em cada tile.
## Devolve {ok, erro, tile, pilares: [{canto: Vector2i, altura: float}]}.
static func planejar(mapa: MapaOcupacao, caminho: Array[Vector2i], direcoes: Array[int], niveis: Array[float]) -> Dictionary:
	var n := caminho.size()
	for i in n:
		var nv := niveis[i]
		if absf(nv / NIVEL - roundf(nv / NIVEL)) > 1e-4:
			return {"ok": false, "erro": "nivel_fora_do_degrau", "tile": caminho[i], "pilares": []}
		if nv > 0.0 and mapa.altura_no_tile(caminho[i]) > nv - FOLGA:
			return {"ok": false, "erro": "estrutura_alta_embaixo", "tile": caminho[i], "pilares": []}
	var pilares: Array[Dictionary] = []
	var ultimo := -1000
	var i := 0
	while i < n:
		if niveis[i] <= 0.0:
			ultimo = i
			i += 1
			continue
		if i - ultimo < VAO_MAX and ultimo >= 0:
			i += 1
			continue
		# precisa de apoio no tile i (ideal), ou recua até 1 / avança até 1
		var achou := -1
		for k in [i, i - 1, i + 1]:
			if k < 0 or k >= n or niveis[k] <= 0.0 or k <= ultimo:
				continue
			var cs := cantos_de_entrada(caminho[k], direcoes[k])
			if mapa.canto_livre(cs[0]) and mapa.canto_livre(cs[1]):
				achou = k
				break
		if achou < 0:
			return {"ok": false, "erro": "sem_apoio", "tile": caminho[i], "pilares": []}
		for c in cantos_de_entrada(caminho[achou], direcoes[achou]):
			pilares.append({"canto": c, "altura": niveis[achou]})
		ultimo = achou
		i = achou + 1
	return {"ok": true, "erro": "", "tile": Vector2i.ZERO, "pilares": pilares}


## Os 2 vértices da borda por onde o fluxo entra no tile.
static func cantos_de_entrada(tile: Vector2i, dir: int) -> Array[Vector2i]:
	match dir:
		0: return [tile, tile + Vector2i(1, 0)]                       # entra pelo sul
		1: return [tile, tile + Vector2i(0, 1)]                       # entra pelo oeste
		2: return [tile + Vector2i(0, 1), tile + Vector2i(1, 1)]      # entra pelo norte
	return [tile + Vector2i(1, 0), tile + Vector2i(1, 1)]             # entra pelo leste


## Quantas peças de pilar (segmentos de 0,5 m) para uma altura.
static func segmentos(altura: float) -> int:
	return maxi(0, roundi(altura / NIVEL) - 1)
