class_name Varredura
extends RefCounted
## Sensor de varredura (proliferação; pesquisa "sensor_varredura", regra "varredura" em estruturas.json). Lógica pura:
##  - cada sensor ligado e com energia revela os chunks em volta dele, do mais perto para o mais longe, um a cada
##    `intervalo_s` (60 s; mais devagar com pouca energia), até `chunks` (6). Com a Varredura profunda (pesquisa
##    "cartografia", modo `modo_profunda`) vai até `chunks_profunda` (16). Chunk que já estava todo descoberto entra na
##    hora (não gasta o minuto);
##  - revelar = o chunk inteiro sai da névoa (Descoberta) e os ninhos dele passam a existir (Colonia.descobrir_chunk,
##    mesmo longe da câmera: a artilharia já pode mirá-los);
##  - os ninhos dos chunks de cada sensor ficam **marcados** no mapa enquanto o sensor está de pé (o desenho põe a
##    marca; ninho novo que nasce ali também aparece);
##  - com a profunda, o sensor mede a **riqueza das jazidas** dos chunks dele (tipo, total, riqueza e onde fica).
## Grade: +x leste, +y norte.

var mapa: MapaOcupacao
var descoberta: Descoberta
var colonia: Colonia                  ## (opcional) cria e lista os ninhos
var energia: Callable                 ## func(id) -> 0..1 (Fabrica.energia); sem ela, todo sensor conta com energia plena
var profunda: Callable                ## func() -> bool: Varredura profunda pesquisada (Pesquisa.modo_liberado)
var sensores: Dictionary = {}         ## id → {feitos: Array (chunks revelados, em ordem), t: s no chunk da vez}
var eventos: Array[Dictionary] = []   ## {tipo: "chunk_revelado", id, chunk} (o mundo limpa depois de ler)
var _versao := -1
var _jazidas: Dictionary = {}         ## id → {chave, lista} (cache da medição)


func _init(p_mapa: MapaOcupacao, p_descoberta: Descoberta) -> void:
	mapa = p_mapa
	descoberta = p_descoberta


static func regra(nome: String) -> Dictionary:
	return Registro.estruturas.get(nome, {}).get("varredura", {})


static func eh_sensor(nome: String) -> bool:
	return not regra(nome).is_empty()


func _regra_id(id: int) -> Dictionary:
	return regra(mapa.estruturas[id].nome) if mapa.estruturas.has(id) else {}


func e_profunda() -> bool:
	return profunda.is_valid() and bool(profunda.call())


## Quantos chunks o sensor revela no total (6; 16 com a profunda).
func limite(id: int) -> int:
	var r := _regra_id(id)
	return int(r.get("chunks_profunda" if e_profunda() else "chunks", 6))


func centro(id: int) -> Vector2:
	var e: Dictionary = mapa.estruturas[id]
	return Grade.centro_da_area(e.minimo, e.area, e.rot)


## Os chunks do sensor, do mais perto (centro do chunk ao centro do sensor) para o mais longe; empate pela posição.
func ordem(id: int, n := -1) -> Array[Vector2i]:
	if n < 0:
		n = limite(id)
	var c := centro(id)
	var k0 := Grade.chunk_de(Vector2i(c.floor()))
	var r := int(ceil(sqrt(float(n)))) + 1
	var lista: Array = []
	for dy in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var k := k0 + Vector2i(dx, dy)
			var meio := (Vector2(k) + Vector2(0.5, 0.5)) * Grade.TAM_CHUNK
			lista.append([meio.distance_squared_to(c), k.y, k.x, k])
	lista.sort()
	var out: Array[Vector2i] = []
	for i in mini(n, lista.size()):
		out.append(lista[i][3])
	return out


## Sensor pode trabalhar agora: ligado pelo painel e com energia (0..1).
func energia_de(id: int) -> float:
	if not mapa.estruturas.has(id) or mapa.estruturas[id].get("desligada", false):
		return 0.0
	return clampf(float(energia.call(id)), 0.0, 1.0) if energia.is_valid() else 1.0


func _atualizar_lista() -> void:
	if mapa.versao == _versao:
		return
	_versao = mapa.versao
	for id in sensores.keys():
		if not mapa.estruturas.has(id) or not eh_sensor(mapa.estruturas[id].nome):
			sensores.erase(id)
			_jazidas.erase(id)
	for id in mapa.estruturas:
		if not sensores.has(id) and eh_sensor(mapa.estruturas[id].nome):
			sensores[id] = {"feitos": [], "t": 0.0}


func tick(dt: float) -> void:
	_atualizar_lista()
	for id in sensores:
		var s: Dictionary = sensores[id]
		var en := energia_de(id)
		if en <= 0.0:
			continue
		var lista := ordem(id)
		var intervalo := float(_regra_id(id).get("intervalo_s", 60.0))
		while true:
			var k := Vector2i(2147483647, 0)
			for c in lista:                          # o próximo da ordem que falta (a profunda continua a mesma ordem)
				if not (s.feitos as Array).has(c):
					k = c
					break
			if k.x == 2147483647:
				break
			if descoberta.chunk_completo(k):         # já visto: entra na hora
				_revelar(id, k)
				continue
			s.t = float(s.t) + dt * en
			if float(s.t) >= intervalo:
				s.t = float(s.t) - intervalo
				_revelar(id, k)
			break


func _revelar(id: int, k: Vector2i) -> void:
	var s: Dictionary = sensores[id]
	s.feitos.append(k)
	descoberta.marcar_chunk(k)
	if colonia != null:
		colonia.descobrir_chunk(k)
	_jazidas.erase(id)
	eventos.append({"tipo": "chunk_revelado", "id": id, "chunk": k})


## Segundos até o próximo chunk (com a energia de agora); -1 = terminou ou parado sem energia.
func falta_s(id: int) -> float:
	if not sensores.has(id):
		return -1.0
	var s: Dictionary = sensores[id]
	var en := energia_de(id)
	if s.feitos.size() >= limite(id) or en <= 0.0:
		return -1.0
	return maxf(0.0, float(_regra_id(id).get("intervalo_s", 60.0)) - float(s.t)) / en


func feitos(id: int) -> int:
	return (sensores[id].feitos as Array).size() if sensores.has(id) else 0


## Chunks revelados pelos sensores que estão de pé.
func chunks_cobertos() -> Dictionary:
	_atualizar_lista()
	var out := {}
	for id in sensores:
		for k in sensores[id].feitos:
			out[k] = id
	return out


## Ninhos marcados: os que estão (centro) num chunk revelado por um sensor de pé.
func ninhos_marcados() -> Array[int]:
	var out: Array[int] = []
	if colonia == null:
		return out
	var cob := chunks_cobertos()
	if cob.is_empty():
		return out
	for n in colonia.ninhos:
		var c: Vector2 = colonia.ninhos[n].centro
		if cob.has(Grade.chunk_de(Vector2i(c.floor()))):
			out.append(n)
	return out


func ninho_marcado(n: int) -> bool:
	return n in ninhos_marcados()


## Ninhos marcados pelo sensor `id` (painel).
func ninhos_do_sensor(id: int) -> Array[int]:
	var out: Array[int] = []
	if colonia == null or not sensores.has(id):
		return out
	var meus := {}
	for k in sensores[id].feitos:
		meus[k] = true
	for n in colonia.ninhos:
		var c: Vector2 = colonia.ninhos[n].centro
		if meus.has(Grade.chunk_de(Vector2i(c.floor()))):
			out.append(n)
	return out


## Riqueza das jazidas nos chunks do sensor (só com a Varredura profunda): uma entrada por mancha cujo centro cai num
## chunk revelado — {tipo, centro: Vector2, total (unidades somadas dos tiles), riqueza (×, cresce longe do spawn),
## nivel: "pobre"/"média"/"rica"}, da maior para a menor.
func jazidas(id: int) -> Array:
	if not e_profunda() or not sensores.has(id):
		return []
	var meus := {}
	for k in sensores[id].feitos:
		meus[k] = true
	var chave := str(meus.keys())
	if _jazidas.has(id) and _jazidas[id].chave == chave:
		return _jazidas[id].lista
	var dist: Distribuicao = mapa.gerador.distribuicao
	var cel := Distribuicao.CEL_JAZIDA
	var vistas := {}
	var lista: Array = []
	for k in meus:
		var a: Vector2i = k * Grade.TAM_CHUNK
		for cy in range(floori(a.y / float(cel)), floori((a.y + Grade.TAM_CHUNK - 1) / float(cel)) + 1):
			for cx in range(floori(a.x / float(cel)), floori((a.x + Grade.TAM_CHUNK - 1) / float(cel)) + 1):
				var cc := Vector2i(cx, cy)
				if vistas.has(cc):
					continue
				vistas[cc] = true
				var m := dist.mancha_da_celula(cc)
				if m.is_empty() or not meus.has(Grade.chunk_de(Vector2i((m.centro as Vector2).floor()))):
					continue
				lista.append(_medir(dist, m))
	for i in Distribuicao.SPAWN.size():                 # jazidas fixas do começo
		var m: Dictionary = Distribuicao.SPAWN[i]
		if meus.has(Grade.chunk_de(Vector2i((m.centro as Vector2).floor()))):
			lista.append(_medir(dist, m))
	lista = lista.filter(func(j): return int(j.total) > 0)
	lista.sort_custom(func(a, b): return int(a.total) > int(b.total))
	_jazidas[id] = {"chave": chave, "lista": lista}
	return lista


static func _medir(dist: Distribuicao, m: Dictionary) -> Dictionary:
	var total := 0
	var c: Vector2 = m.centro
	var r := int(ceil(float(m.raio))) + 1
	for y in range(floori(c.y) - r, floori(c.y) + r + 1):
		for x in range(floori(c.x) - r, floori(c.x) + r + 1):
			var j := dist.jazida(Vector2i(x, y))
			if not j.is_empty() and j.tipo == m.tipo:
				total += int(j.quantidade)
	var riq := float(m.get("riqueza", 1.0))
	return {"tipo": String(m.tipo), "centro": c, "total": total, "riqueza": riq, "nivel": nivel_riqueza(total)}


## Faixas de riqueza pelo total da mancha (uma mancha média tem ~30 mil).
static func nivel_riqueza(total: int) -> String:
	if total >= 60000:
		return "rica"
	if total >= 20000:
		return "média"
	return "pobre"


func estado() -> Dictionary:
	var out := {}
	for id in sensores:
		out[id] = {"feitos": (sensores[id].feitos as Array).duplicate(), "t": sensores[id].t}
	return out


func restaurar(d: Dictionary) -> void:
	sensores.clear()
	_jazidas.clear()
	for id in d:
		var feitos_s: Array = []
		for k in d[id].get("feitos", []):
			feitos_s.append(k if k is Vector2i else Vector2i(int(k.x), int(k.y)))
		sensores[int(id)] = {"feitos": feitos_s, "t": float(d[id].get("t", 0.0))}
	_versao = -1
