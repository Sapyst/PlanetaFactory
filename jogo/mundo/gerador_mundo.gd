class_name GeradorMundo
extends RefCounted
## Mundo plano infinito, determinístico pela semente. Tudo é função do tile (sem estado):
## gerar o mesmo tile por qualquer chunk dá sempre o mesmo resultado — não existe costura entre chunks.
##
## Camadas (cada uma um FastNoiseLite):
##   continente  → terra × água (oceano/mar); o spawn é puxado para terra
##   temperatura, umidade (com distorção de domínio) → bioma pelo centro mais próximo em biomas.json
##   rio         → faixas onde |ruído| ≈ 0 (rede de rios que serpenteiam)
##   lago        → manchas baixas em terra (lago), e pequenas (lagoa)

enum Terreno { TERRA, PRAIA, RIO, LAGO, LAGOA, MAR, OCEANO }
const NOMES_TERRENO := ["terra", "praia", "rio", "lago", "lagoa", "mar", "oceano"]
const RAIO_SPAWN_TERRA := 90.0

var semente: int
var _continente := FastNoiseLite.new()
var _temperatura := FastNoiseLite.new()
var _umidade := FastNoiseLite.new()
var _distorcao := FastNoiseLite.new()
var _rio := FastNoiseLite.new()
var _lago := FastNoiseLite.new()
var _lagoa := FastNoiseLite.new()
var _biomas: Dictionary
var _nomes_biomas: Array[String] = []
var distribuicao: Distribuicao
var registro: Node   ## autoload Registro (buscado em tempo de execução: funciona também em scripts -s)


func _init(p_semente := 1337, biomas: Dictionary = {}) -> void:
	semente = p_semente
	registro = (Engine.get_main_loop() as SceneTree).root.get_node("Registro")
	_biomas = biomas if not biomas.is_empty() else registro.biomas
	for n in _biomas:
		_nomes_biomas.append(n)
	_config(_continente, 1, 0.0028, 5)
	_config(_temperatura, 2, 0.0035, 3)
	_config(_umidade, 3, 0.0040, 3)
	_config(_distorcao, 4, 0.02, 2)
	_config(_rio, 5, 0.0045, 2)
	_config(_lago, 6, 0.018, 2)
	_config(_lagoa, 7, 0.03, 2)
	distribuicao = Distribuicao.new(self)


func _config(n: FastNoiseLite, salt: int, freq: float, oitavas: int) -> void:
	n.seed = semente * 7919 + salt
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = freq
	n.fractal_type = FastNoiseLite.FRACTAL_FBM
	n.fractal_octaves = oitavas


## Elevação "continental" −1..1 com o spawn garantido em terra.
func elevacao(tile: Vector2i) -> float:
	var e := _continente.get_noise_2d(tile.x, tile.y)
	var d2 := float(tile.x * tile.x + tile.y * tile.y)
	# dois sinos somados: um forte e estreito (spawn sempre em terra) e um largo (continente em volta)
	return e + 0.9 * exp(-d2 / (2.0 * 60.0 * 60.0)) + 0.3 * exp(-d2 / (2.0 * RAIO_SPAWN_TERRA * RAIO_SPAWN_TERRA * 2.8))


func terreno(tile: Vector2i) -> int:
	var e := elevacao(tile)
	if e < -0.32: return Terreno.OCEANO
	if e < -0.18: return Terreno.MAR
	if e < -0.14: return Terreno.PRAIA
	var perto_spawn := maxi(absi(tile.x), absi(tile.y)) < 40   # spawn seco (quadrado): jazidas iniciais nunca caem em rio/lago
	if not perto_spawn:
		var r := absf(_rio.get_noise_2d(tile.x, tile.y))
		var largura := 0.012 + 0.010 * clampf(1.0 - e, 0.0, 1.0)   # rios alargam perto do mar
		if r < largura: return Terreno.RIO
		if _lago.get_noise_2d(tile.x, tile.y) < -0.55 and e > -0.05: return Terreno.LAGO
		if _lagoa.get_noise_2d(tile.x, tile.y) < -0.58: return Terreno.LAGOA
	return Terreno.TERRA


## Direção da correnteza num tile de rio: ao longo do rio (perpendicular ao gradiente do ruído do rio),
## virada para o lado mais baixo (o rio desce para o mar).
func direcao_rio(tile: Vector2i) -> Vector2:
	var gx := _rio.get_noise_2d(tile.x + 1, tile.y) - _rio.get_noise_2d(tile.x - 1, tile.y)
	var gy := _rio.get_noise_2d(tile.x, tile.y + 1) - _rio.get_noise_2d(tile.x, tile.y - 1)
	var tan := Vector2(-gy, gx)
	if tan.length() < 1e-6:
		return Vector2.ZERO
	tan = tan.normalized()
	var ex := elevacao(tile + Vector2i(1, 0)) - elevacao(tile - Vector2i(1, 0))
	var ey := elevacao(tile + Vector2i(0, 1)) - elevacao(tile - Vector2i(0, 1))
	if tan.dot(Vector2(ex, ey)) > 0.0:
		tan = -tan
	return tan


func eh_agua(t: int) -> bool:
	return t in [Terreno.RIO, Terreno.LAGO, Terreno.LAGOA, Terreno.MAR, Terreno.OCEANO]


## (temperatura, umidade) em 0..1, com distorção para bordas de bioma orgânicas.
func clima(tile: Vector2i) -> Vector2:
	# deslocamento em x e y independentes (com o mesmo valor nos dois eixos a borda saía em retas a 45°)
	var wx := _distorcao.get_noise_2d(tile.x, tile.y) * 18.0
	var wy := _distorcao.get_noise_2d(tile.x + 913.0, tile.y - 577.0) * 18.0
	var t := _temperatura.get_noise_2d(tile.x + wx, tile.y + wy) * 0.5 + 0.5
	var u := _umidade.get_noise_2d(tile.x - wy, tile.y + wx) * 0.5 + 0.5
	return Vector2(clampf(t * 1.25 - 0.12, 0, 1), clampf(u * 1.25 - 0.12, 0, 1))


func bioma(tile: Vector2i) -> String:
	var c := clima(tile)
	var melhor := ""
	var dist := INF
	for n in _nomes_biomas:
		var cc: Array = _biomas[n].centro
		var d := c.distance_squared_to(Vector2(cc[0], cc[1]))
		if d < dist:
			dist = d
			melhor = n
	return melhor


func indice_bioma(nome: String) -> int:
	return _nomes_biomas.find(nome)


func nomes_biomas() -> Array[String]:
	return _nomes_biomas


func dados_bioma(nome: String) -> Dictionary:
	return _biomas.get(nome, {})


## Tudo de um chunk de uma vez (para desenhar e para o mapa de ocupação).
func gerar_chunk(chunk: Vector2i) -> ChunkDados:
	var c := ChunkDados.new()
	c.coord = chunk
	var n := Grade.TAM_CHUNK
	c.terreno.resize(n * n)
	c.bioma.resize(n * n)
	var base := chunk * n
	var cx := Distribuicao.contexto()          # cada tile é calculado uma vez só neste chunk
	for j in n:
		for i in n:
			var t := base + Vector2i(i, j)
			var k := j * n + i
			c.terreno[k] = distribuicao._ter(t, cx)
			c.bioma[k] = indice_bioma(distribuicao._bio(t, cx))
			var jaz := distribuicao.jazida(t, cx)
			if not jaz.is_empty():
				c.jazidas[t] = jaz
			var ob := distribuicao.obstaculo(t, cx)
			if not ob.is_empty() and ob.ancora == t:
				c.obstaculos[t] = ob
			var dc := distribuicao.deco(t, cx, ob)
			if not dc.is_empty():
				c.decos.append(dc)
	return c
