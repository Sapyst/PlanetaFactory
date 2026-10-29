class_name MapaOcupacao
extends RefCounted
## Quem ocupa cada tile e cada canto da grade. Regras de construção:
##  - área inteira em terra construível, sem outra estrutura e sem obstáculo natural (precisa limpar antes);
##  - extratores/brocas/bombas exigem jazida compatível em pelo menos um tile da área;
##  - cantos: pilares de esteira elevada só em canto que nenhuma estrutura "ocupa_canto" reivindica,
##    e estrutura "ocupa_canto" (muro, trilho, obstáculo) não pode cobrir canto que já tem pilar.
##  - esteira elevada (nível n = n × 0,5 m) mora em `altos`, não ocupa o chão: passa por cima de estrutura mais
##    baixa que o nível − FOLGA; e nada mais alto que isso pode ser construído debaixo dela depois.

var gerador: GeradorMundo
var registro: Node
var tiles: Dictionary = {}          ## Vector2i → id
var cantos: Dictionary = {}         ## Vector2i (vértice) → id (estrutura que ocupa canto ou pilar)
var estruturas: Dictionary = {}     ## id → {nome, minimo, rot, area}
var limpos: Dictionary = {}         ## tiles cujo obstáculo natural já foi removido
var altos: Dictionary = {}          ## Vector3i(x, y, nível 1..2) → id (esteira elevada / rampa de cima)
const NIVEIS := 2                   ## até 1,0 m
const FOLGA := 0.25
var _prox_id := 1
var versao := 0                     ## muda a cada colocar/remover (quem guarda listas sabe quando refazer)


func _init(p_gerador: GeradorMundo) -> void:
	gerador = p_gerador
	registro = gerador.registro


## "" se pode; senão o motivo.
func motivo_bloqueio(nome: String, minimo: Vector2i, rot: int) -> String:
	var def: Dictionary = registro.estruturas.get(nome, registro.modelos.get(nome, {}))
	if def.is_empty():
		return "estrutura desconhecida"
	var area: Vector2i = registro.area(nome)
	var precisa: Array = def.get("requer_jazida", [])
	var achou_jazida := precisa.is_empty()
	var nivel0 := gerador.nivel(minimo)
	for t in Grade.tiles_da_area(minimo, area, rot):
		if gerador.nivel(t) != nivel0:
			return "desnivel"                          # (encosta pode: a construção aplaina o chão)
		if tiles.has(t):
			return "ocupado"
		var ter := gerador.terreno(t)
		if gerador.eh_agua(ter):
			return "agua"
		if not limpos.has(t) and not gerador.distribuicao.obstaculo(t).is_empty():
			return "obstaculo"
		if not achou_jazida:
			var j := gerador.distribuicao.jazida(t)
			if not j.is_empty() and precisa.has(j.tipo):
				achou_jazida = true
	if not achou_jazida:
		return "sem_jazida"
	var alt := _altura(nome)
	for t in Grade.tiles_da_area(minimo, area, rot):
		for n in range(1, NIVEIS + 1):
			if altos.has(Vector3i(t.x, t.y, n)) and alt > n * 0.5 - FOLGA:
				return "esteira_em_cima"
	if def.get("ocupa_canto", false):
		for c in Grade.cantos_da_area(minimo, area, rot):
			if cantos.has(c) and estruturas[cantos[c]].nome.begins_with("pilar"):
				return "pilar_no_canto"
	return ""


## Esteira/rampa no nível n ≥ 1 (só peças 1×1 de esteira): livre naquele nível, estrutura de baixo mais baixa.
func motivo_alto(t: Vector2i, n: int) -> String:
	if altos.has(Vector3i(t.x, t.y, n)):
		return "ocupado"
	if altura_no_tile(t) > n * 0.5 - FOLGA:
		return "estrutura_alta_embaixo"
	if not limpos.has(t) and not gerador.distribuicao.obstaculo(t).is_empty():
		return "obstaculo"
	return ""


## `extras`: campos a mais na entrada (nivel, desce, pilares). Nível ≥ 1 vai para `altos`.
func colocar(nome: String, minimo: Vector2i, rot: int, extras := {}) -> int:
	var n: int = extras.get("nivel", 0)
	var motivo := motivo_bloqueio(nome, minimo, rot) if n == 0 else motivo_alto(minimo, n)
	if motivo != "":
		return -1
	var id := _prox_id
	_prox_id += 1
	versao += 1
	var area: Vector2i = registro.area(nome)
	estruturas[id] = {"nome": nome, "minimo": minimo, "rot": rot, "area": area}
	estruturas[id].merge(extras)
	if n > 0:
		altos[Vector3i(minimo.x, minimo.y, n)] = id
		return id
	for t in Grade.tiles_da_area(minimo, area, rot):
		tiles[t] = id
	var def: Dictionary = registro.estruturas.get(nome, {})
	if def.get("ocupa_canto", false):
		for c in Grade.cantos_da_area(minimo, area, rot):
			cantos[c] = id
	return id


func remover(id: int) -> void:
	if not estruturas.has(id):
		return
	var e: Dictionary = estruturas[id]
	versao += 1
	if e.get("nivel", 0) > 0:
		altos.erase(Vector3i(e.minimo.x, e.minimo.y, e.nivel))
		estruturas.erase(id)
		return
	# só a área da própria estrutura (não varre o mapa inteiro)
	for t in Grade.tiles_da_area(e.minimo, e.area, e.rot):
		if tiles.get(t, -1) == id:
			tiles.erase(t)
	for c in Grade.cantos_da_area(e.minimo, e.area, e.rot):
		if cantos.get(c, -1) == id:
			cantos.erase(c)
	estruturas.erase(id)


var _terra_versao := -1
var _terra := false


## Há uma Terraplenagem construída (libera Aplainar em qualquer lugar do mapa).
func tem_terraplenagem() -> bool:
	if _terra_versao != versao:
		_terra_versao = versao
		_terra = false
		for id in estruturas:
			if estruturas[id].nome == "terraplenagem":
				_terra = true
				break
	return _terra


func limpar_obstaculo(tile: Vector2i) -> Dictionary:
	var o := gerador.distribuicao.obstaculo(tile)
	if o.is_empty() or limpos.has(tile):
		return {}
	for t in Grade.tiles_da_area(o.ancora, o.area, 0):
		limpos[t] = true
	return o


## Canto livre para pilar: ninguém reivindica e nenhum tile em volta é obstáculo natural de pé.
func canto_livre(c: Vector2i) -> bool:
	if cantos.has(c):
		return false
	for d in [Vector2i(0, 0), Vector2i(-1, 0), Vector2i(0, -1), Vector2i(-1, -1)]:
		var t: Vector2i = c + d
		if gerador.eh_agua(gerador.terreno(t)):
			return false
		if not limpos.has(t) and not gerador.distribuicao.obstaculo(t).is_empty():
			return false
	return true


func reservar_pilar(c: Vector2i, altura: float) -> int:
	if not canto_livre(c):
		return -1
	var id := _prox_id
	_prox_id += 1
	estruturas[id] = {"nome": "pilar", "minimo": c, "rot": 0, "area": Vector2i.ZERO, "altura": altura}
	cantos[c] = id
	return id


## Altura (m) da estrutura mais alta no tile (0 se vazio). Usado para saber se a esteira elevada passa por cima.
func altura_no_tile(t: Vector2i) -> float:
	if not tiles.has(t):
		return 0.0
	return _altura(estruturas[tiles[t]].nome)


func _altura(nome: String) -> float:
	var dims: Array = registro.modelos.get(nome, {}).get("dims", [0, 0, 0])
	return float(dims[2])


## Ids de tudo no tile: chão primeiro, depois os níveis de cima.
func ids_no_tile(t: Vector2i) -> Array[int]:
	var out: Array[int] = []
	if tiles.has(t):
		out.append(tiles[t])
	for n in range(1, NIVEIS + 1):
		var k := Vector3i(t.x, t.y, n)
		if altos.has(k):
			out.append(altos[k])
	return out


## Recria o mapa de um salvamento: mesmas estruturas com os MESMOS ids (estações, trens, torres e máquinas
## guardam estado pelo id). Tiles e cantos são refeitos a partir das estruturas.
func restaurar(p_estruturas: Dictionary, p_limpos: Array, prox_id: int) -> void:
	estruturas.clear()
	tiles.clear()
	cantos.clear()
	limpos.clear()
	altos.clear()
	for t in p_limpos:
		limpos[t] = true
	for id in p_estruturas:
		var e: Dictionary = p_estruturas[id]
		estruturas[id] = e
		if e.nome == "pilar":
			cantos[e.minimo] = id
			continue
		if e.get("nivel", 0) > 0:
			altos[Vector3i(e.minimo.x, e.minimo.y, e.nivel)] = id
			continue
		for t in Grade.tiles_da_area(e.minimo, e.area, e.rot):
			tiles[t] = id
		if registro.estruturas.get(e.nome, {}).get("ocupa_canto", false):
			for c in Grade.cantos_da_area(e.minimo, e.area, e.rot):
				cantos[c] = id
	_prox_id = prox_id
