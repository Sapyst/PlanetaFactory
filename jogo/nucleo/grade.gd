class_name Grade
## Coordenadas do mapa. Tile (i, j) ocupa [i, i+1] × [j, j+1] no plano da grade (j cresce para o norte).
## No mundo 3D do Godot: x = i, z = −j (os modelos vêm do Blender com +Y = norte = −Z).
## Cantos (vértices da grade) usam a coordenada inteira do ponto: o canto (i, j) é o sudoeste do tile (i, j).

const TAM_CHUNK := 32
## Lados: 0 = N, 1 = L (leste), 2 = S, 3 = O. Rotação r = quartos de volta no sentido anti-horário (como no Blender).
const DIRECOES: Array[Vector2i] = [Vector2i(0, 1), Vector2i(1, 0), Vector2i(0, -1), Vector2i(-1, 0)]
const LADOS := {"N": 0, "L": 1, "S": 2, "O": 3}


static func chunk_de(tile: Vector2i) -> Vector2i:
	return Vector2i(floori(tile.x / float(TAM_CHUNK)), floori(tile.y / float(TAM_CHUNK)))


static func local_de(tile: Vector2i) -> Vector2i:
	return Vector2i(posmod(tile.x, TAM_CHUNK), posmod(tile.y, TAM_CHUNK))


static func centro_mundo(tile: Vector2i, altura := 0.0) -> Vector3:
	return Vector3(tile.x + 0.5, altura, -(tile.y + 0.5))


static func ponto_mundo(p: Vector2, altura := 0.0) -> Vector3:
	return Vector3(p.x, altura, -p.y)


static func tile_de_mundo(pos: Vector3) -> Vector2i:
	return Vector2i(floori(pos.x), floori(-pos.z))


## Gira um vetor da grade r quartos de volta (anti-horário).
static func girar(v: Vector2, r: int) -> Vector2:
	match posmod(r, 4):
		1: return Vector2(-v.y, v.x)
		2: return Vector2(-v.x, -v.y)
		3: return Vector2(v.y, -v.x)
	return v


static func girar_i(v: Vector2i, r: int) -> Vector2i:
	var g := girar(Vector2(v), r)
	return Vector2i(roundi(g.x), roundi(g.y))


## Ângulo (rad, em torno de +Y do Godot) que aplica a rotação r ao modelo.
static func angulo(r: int) -> float:
	return posmod(r, 4) * PI / 2.0


static func area_girada(area: Vector2i, r: int) -> Vector2i:
	return area if posmod(r, 2) == 0 else Vector2i(area.y, area.x)


## Tiles ocupados por uma estrutura com canto sudoeste em `minimo`.
static func tiles_da_area(minimo: Vector2i, area: Vector2i, r: int) -> Array[Vector2i]:
	var a := area_girada(area, r)
	var out: Array[Vector2i] = []
	for i in a.x:
		for j in a.y:
			out.append(minimo + Vector2i(i, j))
	return out


## Cantos (vértices) cobertos pela área, inclusive os da borda.
static func cantos_da_area(minimo: Vector2i, area: Vector2i, r: int) -> Array[Vector2i]:
	var a := area_girada(area, r)
	var out: Array[Vector2i] = []
	for i in a.x + 1:
		for j in a.y + 1:
			out.append(minimo + Vector2i(i, j))
	return out


static func centro_da_area(minimo: Vector2i, area: Vector2i, r: int) -> Vector2:
	return Vector2(minimo) + Vector2(area_girada(area, r)) / 2.0


## Portas no mundo. `porta` vem de modelos.json: {nome, tipo, io, pos:[x,y,z], dir:[x,y,z]} no espaço do modelo (centro = origem).
## Devolve pos (ponto na borda), dir (para fora), tile_dentro e tile_fora (vizinho onde a esteira/cano/trilho encosta).
static func porta_no_mundo(porta: Dictionary, minimo: Vector2i, area: Vector2i, r: int) -> Dictionary:
	var c := centro_da_area(minimo, area, r)
	var p := Vector2(porta.pos[0], porta.pos[1])
	var d := Vector2(porta.dir[0], porta.dir[1])
	var pm := c + girar(p, r)
	var dm := girar(d, r)
	var dentro := Vector2i((pm - dm * 0.5).floor())
	var fora := Vector2i((pm + dm * 0.5).floor())
	return {"nome": porta.nome, "tipo": porta.tipo, "io": porta.io, "pos": pm,
			"dir": Vector2i(roundi(dm.x), roundi(dm.y)), "tile_dentro": dentro, "tile_fora": fora,
			"altura": float(porta.pos[2])}
