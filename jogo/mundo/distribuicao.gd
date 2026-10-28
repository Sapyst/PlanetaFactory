class_name Distribuicao
extends RefCounted
## Onde fica cada coisa do mapa, por padrão bio-territorial. Sem estado: tudo sai de um hash do tile,
## então qualquer chunk (e qualquer ordem de geração) chega no mesmo resultado.
##
## Jazidas: uma mancha por célula de 40×40 (centro afastado da borda → manchas nunca se sobrepõem).
##   Tipo sorteado pelos pesos do bioma do centro. Manchas crescem e enriquecem com a distância do spawn.
##   Perto do spawn há manchas fixas garantidas (cristal, ferro, cobre, carvão, pedra).
## Obstáculos grandes (rocha 2×2, montanhas): no máximo um por célula de 6×6, inteiro dentro da célula.
## Obstáculos 1×1 e enfeites: chance por tile, pelos pesos do bioma.

const CEL_JAZIDA := 40
const MARGEM_JAZIDA := 10
const CEL_GRANDE := 6
const RAIO_LIVRE_SPAWN := 7
const SPAWN := [
	{"tipo": "jazida_cristal", "centro": Vector2(15, 5), "raio": 4.5},
	{"tipo": "jazida_ferro", "centro": Vector2(-13, 9), "raio": 4.5},
	{"tipo": "jazida_cobre", "centro": Vector2(6, -15), "raio": 4.0},
	{"tipo": "jazida_carvao", "centro": Vector2(-15, -9), "raio": 4.0},
	{"tipo": "jazida_pedra", "centro": Vector2(1, 17), "raio": 3.5},
]
const RAIO_SO_SPAWN := 30.0

var g: GeradorMundo


func _init(gerador: GeradorMundo) -> void:
	g = gerador


## Hash inteiro → [0, 1). Igual em qualquer máquina (só inteiros de 64 bits).
static func h(x: int, y: int, salt: int) -> float:
	var n: int = x * 374761393 + y * 668265263 + salt * 1442695041
	n = (n ^ (n >> 13)) * 1274126177
	n = n ^ (n >> 16)
	return float(n & 0xFFFFFF) / 16777216.0


static func sortear(pesos: Dictionary, r: float) -> String:
	var total := 0.0
	for k in pesos:
		total += float(pesos[k])
	if total <= 0.0:
		return ""
	var alvo := r * total
	for k in pesos:
		alvo -= float(pesos[k])
		if alvo < 0.0:
			return k
	return pesos.keys()[-1]


# ------------------------------------------------------------------ cache por chunk
## `cx` (opcional) guarda o que já foi calculado durante a geração de UM chunk: terreno, bioma, jazida e as células
## de mancha/obstáculo grande. Mesmo resultado com ou sem cache (função pura do tile); só não recalcula.
func _ter(t: Vector2i, cx: Dictionary) -> int:
	if not cx.has("_"):
		return g.terreno(t)
	var k := Vector3i(t.x, t.y, 0)
	if not cx.has(k):
		cx[k] = g.terreno(t)
	return cx[k]


func _bio(t: Vector2i, cx: Dictionary) -> String:
	if not cx.has("_"):
		return g.bioma(t)
	var k := Vector3i(t.x, t.y, 1)
	if not cx.has(k):
		cx[k] = g.bioma(t)
	return cx[k]


static func contexto() -> Dictionary:
	return {"_": true}


# ------------------------------------------------------------------ jazidas
func mancha_da_celula(cel: Vector2i, cx := {}) -> Dictionary:
	if cx.has("_"):
		var k := Vector3i(cel.x, cel.y, 3)
		if not cx.has(k):
			cx[k] = mancha_da_celula(cel)
		return cx[k]
	var base := Vector2(cel * CEL_JAZIDA)
	var c := base + Vector2(MARGEM_JAZIDA, MARGEM_JAZIDA) + Vector2(h(cel.x, cel.y, 11), h(cel.x, cel.y, 12)) * (CEL_JAZIDA - 2 * MARGEM_JAZIDA)
	var dist := c.length()
	if dist < RAIO_SO_SPAWN + 12.0:
		return {}
	var chance := 0.40 + minf(0.30, dist / 3000.0)
	if h(cel.x, cel.y, 13) > chance:
		return {}
	var tc := Vector2i(c.floor())
	if g.terreno(tc) != GeradorMundo.Terreno.TERRA:
		return {}
	var tipo := sortear(g.dados_bioma(g.bioma(tc)).get("jazidas", {}), h(cel.x, cel.y, 14))
	if tipo == "":
		return {}
	var raio := 3.0 + h(cel.x, cel.y, 15) * 3.0 + minf(3.5, dist / 600.0)
	return {"tipo": tipo, "centro": c, "raio": raio, "riqueza": 1.0 + dist / 800.0}


func jazida(tile: Vector2i, cx := {}) -> Dictionary:
	if cx.has("_"):
		var k := Vector3i(tile.x, tile.y, 2)
		if not cx.has(k):
			cx[k] = _jazida(tile, cx)
		return cx[k]
	return _jazida(tile, cx)


func _jazida(tile: Vector2i, cx: Dictionary) -> Dictionary:
	var t := _ter(tile, cx)
	if t != GeradorMundo.Terreno.TERRA:
		return {}
	var p := Vector2(tile) + Vector2(0.5, 0.5)
	var manchas: Array = []
	if p.length() < RAIO_SO_SPAWN + 8.0:
		manchas = SPAWN
	else:
		var cel := Vector2i(floori(tile.x / float(CEL_JAZIDA)), floori(tile.y / float(CEL_JAZIDA)))
		var m := mancha_da_celula(cel, cx)
		if not m.is_empty():
			manchas = [m]
	for m in manchas:
		var d: float = p.distance_to(m.centro)
		var borda: float = m.raio - h(tile.x, tile.y, 21) * 1.3
		if d < borda:
			var rq: float = m.get("riqueza", 1.0)
			return {"tipo": m.tipo, "quantidade": int((300.0 + 1500.0 * (1.0 - d / m.raio)) * rq)}
	return {}


# ------------------------------------------------------------------ obstáculos
func _livre_spawn(tile: Vector2i, raio: int) -> bool:
	return tile.x * tile.x + tile.y * tile.y > raio * raio


func grande_da_celula(cel: Vector2i, cx := {}) -> Dictionary:
	if cx.has("_"):
		var k := Vector3i(cel.x, cel.y, 4)
		if not cx.has(k):
			cx[k] = _grande(cel, cx)
		return cx[k]
	return _grande(cel, cx)


func _grande(cel: Vector2i, cx: Dictionary) -> Dictionary:
	var centro := cel * CEL_GRANDE + Vector2i(CEL_GRANDE / 2, CEL_GRANDE / 2)
	var dados: Dictionary = g.dados_bioma(_bio(centro, cx)).get("grandes", {})
	if dados.is_empty() or h(cel.x, cel.y, 31) > float(dados.get("chance", 0.0)):
		return {}
	var nome := sortear(dados.get("tipos", {}), h(cel.x, cel.y, 32))
	if nome == "":
		return {}
	var area: Vector2i = g.registro.area(nome)
	var folga := Vector2i(CEL_GRANDE, CEL_GRANDE) - area
	if folga.x < 0 or folga.y < 0:
		return {}
	var ancora := cel * CEL_GRANDE + Vector2i(int(h(cel.x, cel.y, 33) * (folga.x + 1)), int(h(cel.x, cel.y, 34) * (folga.y + 1)))
	for t in Grade.tiles_da_area(ancora, area, 0):
		if _ter(t, cx) != GeradorMundo.Terreno.TERRA or not jazida(t, cx).is_empty() or not _livre_spawn(t, RAIO_LIVRE_SPAWN + 4):
			return {}
	return {"nome": nome, "ancora": ancora, "area": area, "rot": 0}


func obstaculo(tile: Vector2i, cx := {}) -> Dictionary:
	var cel := Vector2i(floori(tile.x / float(CEL_GRANDE)), floori(tile.y / float(CEL_GRANDE)))
	var gr := grande_da_celula(cel, cx)
	if not gr.is_empty():
		var a: Vector2i = gr.ancora
		var ar: Vector2i = gr.area
		if tile.x >= a.x and tile.y >= a.y and tile.x < a.x + ar.x and tile.y < a.y + ar.y:
			return gr
	if _ter(tile, cx) != GeradorMundo.Terreno.TERRA or not jazida(tile, cx).is_empty() or not _livre_spawn(tile, RAIO_LIVRE_SPAWN):
		return {}
	var dados: Dictionary = g.dados_bioma(_bio(tile, cx)).get("obstaculos", {})
	if h(tile.x, tile.y, 41) > float(dados.get("chance", 0.0)):
		return {}
	var nome := sortear(dados.get("tipos", {}), h(tile.x, tile.y, 42))
	if nome == "":
		return {}
	return {"nome": nome, "ancora": tile, "area": Vector2i.ONE, "rot": int(h(tile.x, tile.y, 43) * 4.0)}


# ------------------------------------------------------------------ enfeites
func deco(tile: Vector2i, cx := {}, obst: Variant = null) -> Dictionary:
	var t := _ter(tile, cx)
	var nome := ""
	if t == GeradorMundo.Terreno.LAGO or t == GeradorMundo.Terreno.LAGOA:
		if h(tile.x, tile.y, 51) < 0.08:
			nome = "vitoria_regia"
	elif t == GeradorMundo.Terreno.TERRA and (obstaculo(tile, cx) if obst == null else obst).is_empty() and jazida(tile, cx).is_empty():
		var dados: Dictionary = g.dados_bioma(_bio(tile, cx)).get("deco", {})
		if h(tile.x, tile.y, 52) < float(dados.get("chance", 0.0)):
			nome = sortear(dados.get("tipos", {}), h(tile.x, tile.y, 53))
	if nome == "":
		return {}
	var pos := Vector2(tile) + Vector2(0.2 + 0.6 * h(tile.x, tile.y, 54), 0.2 + 0.6 * h(tile.x, tile.y, 55))
	return {"nome": nome, "pos": pos, "rot": h(tile.x, tile.y, 56) * TAU}
