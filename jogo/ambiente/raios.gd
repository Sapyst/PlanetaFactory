class_name Raios
extends RefCounted
## Raios da tempestade (fase 2.5, lógica pura). O Clima solta o evento "raio" (tempestade e tufão); aqui ele vira um
## raio de verdade, num ponto do mapa, com consequência:
##  1. sorteio: perto da fábrica — um ponto a até `raio_sorteio` m de uma construção sorteada, as altas com mais
##     chance (peso = altura²: o raio procura o ponto alto; sem construção, em volta de onde a câmera olha);
##  2. regulador climático (céu firme ou chuva mansa) cobrindo o ponto: o raio não cai;
##  3. cúpula contra raios com energia cobrindo o ponto: a cúpula pega (bate no campo, escorre até o cristal) e a
##     carga vai para os acumuladores da rede dela;
##  4. para-raios / captador no raio de captação ("capta_raio": raio, mj): o mais perto pega (o captador antes dos
##     para-raios — é a peça feita para isso). Para-raios: `mj` vão para os acumuladores da rede dele (sem acumulador,
##     é só proteção). Captador: carrega 1 cristal lapidado (30 de água) em cristal carregado; a sobra vai para a rede;
##  5. sem proteção: a construção mais alta a até `busca` m leva `dano` (o escudo do gerador absorve, se cobrir) e a
##     vegetação em volta pode pegar fogo; sem construção, a árvore/mato do ponto pega fogo ou o chão fica queimado.
## Cada raio vira uma "queda" (para o desenho: onde bate, a que altura, de que tipo) e conta no contador de descargas
## da peça que pegou (salvo).

var mapa: MapaOcupacao
var fabrica: Fabrica                  ## (opcional) energia para os acumuladores, captador
var ambiente: AmbienteVivo            ## (opcional) fogo e chão queimado
var colonia: Colonia                  ## (opcional) escudo absorve o raio
var clima_local: ClimaLocal           ## (opcional) cúpula e regulador
var dano: Callable                    ## func(id, pontos): o mundo aplica (pode destruir)
var quedas: Array[Dictionary] = []    ## {tipo, pos: Vector2 (grade), alt: m acima do chão, id, ...}; quem desenha limpa
var descargas: Dictionary = {}        ## id da peça que pega → raios pegos
var total := 0                        ## raios que caíram (para testes e relatório)
var _rng := RandomNumberGenerator.new()
var _d: Dictionary
var _versao := -1
var _captam: Array[int] = []          ## para-raios, captadores e cúpulas do mapa
var _altos: Array[int] = []           ## construções (sem ninhos) para o sorteio, com o peso acumulado em _pesos
var _pesos: PackedFloat64Array = []
var _peso_total := 0.0


func _init(p_mapa: MapaOcupacao, semente := 7) -> void:
	mapa = p_mapa
	_rng.seed = semente * 31 + 5
	_d = Registro.clima.get("raios", {})


## Consome os eventos "raio" do clima.
func tick(clima: Clima) -> void:
	if clima == null or clima.eventos.is_empty():
		return
	var resto: Array[String] = []
	for ev in clima.eventos:
		if ev == "raio":
			cair(sortear_ponto(clima.foco))
		else:
			resto.append(ev)
	clima.eventos = resto


## Ponto (grade) onde o próximo raio cai.
func sortear_ponto(foco: Vector2) -> Vector2:
	var r := float(_d.get("raio_sorteio", 20.0))
	var centro := foco
	_atualizar_lista()
	if _peso_total > 0.0:
		var x := _rng.randf() * _peso_total
		var i := _pesos.bsearch(x)
		var e: Dictionary = mapa.estruturas[_altos[mini(i, _altos.size() - 1)]]
		centro = Grade.centro_da_area(e.minimo, e.area, e.rot)
	else:
		r *= 1.5
	return centro + Vector2.from_angle(_rng.randf() * TAU) * r * sqrt(_rng.randf())


## O raio cai em `p` (grade). Devolve a queda (também guardada em `quedas`); tipo "nenhum" se não caiu.
func cair(p: Vector2) -> Dictionary:
	if clima_local != null and clima_local.sem_raio(p):
		return {"tipo": "nenhum", "pos": p}
	total += 1
	var q := _resolver(p)
	quedas.append(q)
	while quedas.size() > 8:
		quedas.pop_front()
	return q


func _resolver(p: Vector2) -> Dictionary:
	_atualizar_lista()
	# cúpula com energia: nenhum raio cai dentro
	if clima_local != null:
		var z := clima_local.zona_em(p, "cupula")
		if not z.is_empty():
			var id: int = z.id
			var r := float(z.raio)
			var d := minf(p.distance_to(z.centro), r)
			_contar(id)
			var mj := float(Registro.estruturas[mapa.estruturas[id].nome].get("capta_raio", {}).get("mj", 0.0))
			var guardou := _injetar(id, mj)
			return {"tipo": "cupula", "pos": p, "alt": sqrt(maxf(0.0, r * r - d * d)), "id": id, "centro": z.centro,
					"raio_cupula": r, "ponta": ponta(id), "mj": guardou}
	# para-raios e captadores
	var melhor := -1
	var chave := INF
	for id in _captam:
		if not mapa.estruturas.has(id):
			continue
		var e: Dictionary = mapa.estruturas[id]
		var cr: Dictionary = Registro.estruturas[e.nome].get("capta_raio", {})
		if not cr.has("raio"):
			continue
		var pt := ponta(id)
		var d := p.distance_to(Vector2(pt.x, pt.y))
		if d > float(cr.raio):
			continue
		var k := float(cr.get("prioridade", 1)) * 1000.0 + d
		if k < chave:
			chave = k
			melhor = id
	if melhor >= 0:
		return _captar(melhor, p)
	return _atingir(p)


func _captar(id: int, p: Vector2) -> Dictionary:
	var e: Dictionary = mapa.estruturas[id]
	var cr: Dictionary = Registro.estruturas[e.nome].capta_raio
	_contar(id)
	var pt := ponta(id)
	var q := {"tipo": "para_raios", "pos": Vector2(pt.x, pt.y), "alt": pt.z, "id": id, "de": p}
	var mj := float(cr.get("mj", 0.0))
	if fabrica != null and fabrica.maquinas.has(id):          # captador: carrega um cristal
		q.tipo = "captador"
		q["carregou"] = fabrica.raio_no_captador(id)
	q["mj"] = _injetar(id, mj)
	if ambiente != null:
		ambiente._mancha(Vector2(Grade.centro_da_area(e.minimo, e.area, e.rot)), 0.9, AmbienteVivo.QUEIM, 0.25)
	return q


## Sem proteção: a construção mais alta perto leva o raio; sem construção, o chão/a vegetação.
func _atingir(p: Vector2) -> Dictionary:
	var busca := float(_d.get("busca", 3.0))
	var alvo := -1
	var alt := 0.0
	var dist := INF
	var t0 := Vector2i(p.floor())
	var r := int(ceil(busca)) + 3
	var vistos := {}
	for dx in range(-r, r + 1):
		for dy in range(-r, r + 1):
			var id: int = mapa.tiles.get(t0 + Vector2i(dx, dy), -1)
			if id < 0 or vistos.has(id) or not mapa.estruturas.has(id):
				continue
			vistos[id] = true
			var e: Dictionary = mapa.estruturas[id]
			var regra: Dictionary = Registro.estruturas.get(e.nome, {})
			if regra.get("grupo", "") == "inimigo":
				continue
			var d := Colonia._dist_estrutura(p, e)
			if d > busca:
				continue
			var h := altura(e.nome)
			if h > alt + 0.05 or (absf(h - alt) <= 0.05 and d < dist):
				alvo = id
				alt = h
				dist = d
	if alvo >= 0:
		var e: Dictionary = mapa.estruturas[alvo]
		var c := Grade.centro_da_area(e.minimo, e.area, e.rot)
		var pontos := float(_d.get("dano", 150.0))
		var absorveu := colonia != null and colonia._escudo_absorve(alvo, pontos, p)
		if not absorveu and dano.is_valid():
			dano.call(alvo, pontos)
		_fogo_em_volta(c, maxf(e.area.x, e.area.y) * 0.5 + 1.0)
		if ambiente != null:
			ambiente._mancha(c, 1.4 + 0.5 * maxf(e.area.x, e.area.y), AmbienteVivo.QUEIM, 0.45)
		return {"tipo": "escudo" if absorveu else "estrutura", "pos": c, "alt": alt, "id": alvo, "dano": 0.0 if absorveu else pontos}
	# chão: árvore e mato pegam fogo; senão fica a marca queimada
	var t := Vector2i(p.floor())
	var q := {"tipo": "chao", "pos": Vector2(t) + Vector2(0.5, 0.5), "alt": 0.0, "id": -1}
	if ambiente != null:
		var o := ambiente.gerador.distribuicao.obstaculo(t) if not mapa.limpos.has(t) else {}
		if not o.is_empty() and Distribuicao.eh_arvore(o.nome):
			q.alt = float(_d.get("altura_arvore", 4.0))
		if ambiente._inflamavel(t):
			ambiente._acender(t)
			q.tipo = "fogo"
		ambiente._mancha(q.pos, 1.3, AmbienteVivo.QUEIM, 0.5)
	return q


func _fogo_em_volta(c: Vector2, r: float) -> void:
	if ambiente == null:
		return
	for i in int(_d.get("fogo_tentativas", 3)):
		var t := Vector2i((c + Vector2.from_angle(_rng.randf() * TAU) * r).floor())
		if ambiente._inflamavel(t):
			ambiente._acender(t)


## Energia do raio para os acumuladores da rede da peça. Devolve quanto guardou (MJ).
func _injetar(id: int, mj: float) -> float:
	if fabrica == null or mj <= 0.0:
		return 0.0
	return fabrica.injetar(id, mj)


func _contar(id: int) -> void:
	descargas[id] = int(descargas.get(id, 0)) + 1


func _atualizar_lista() -> void:
	if mapa.versao == _versao:
		return
	_versao = mapa.versao
	_captam.clear()
	_altos.clear()
	_pesos.clear()
	_peso_total = 0.0
	for id in mapa.estruturas:
		var regra: Dictionary = Registro.estruturas.get(mapa.estruturas[id].nome, {})
		if regra.has("capta_raio"):
			_captam.append(id)
		if regra.get("grupo", "") != "inimigo":
			var h := altura(mapa.estruturas[id].nome)
			_peso_total += h * h
			_altos.append(id)
			_pesos.append(_peso_total)
	for id in descargas.keys():
		if not mapa.estruturas.has(id):
			descargas.erase(id)


## Altura (m) do modelo da estrutura (para "o mais alto pega").
static func altura(nome: String) -> float:
	var dm: Array = Registro.estruturas.get(nome, {}).get("dims", [])
	return float(dm[2]) if dm.size() > 2 else 1.0


## Ponta onde o raio bate (grade x, y; z = altura acima do chão): "ponta_raio" do modelo, girada com a peça.
func ponta(id: int) -> Vector3:
	var e: Dictionary = mapa.estruturas[id]
	var c := Grade.centro_da_area(e.minimo, e.area, e.rot)
	var pr: Array = Registro.estruturas.get(e.nome, {}).get("ponta_raio", [])
	if pr.size() < 3:
		return Vector3(c.x, c.y, altura(e.nome))
	var xy := c + Grade.girar(Vector2(float(pr[0]), float(pr[1])), int(e.rot))
	return Vector3(xy.x, xy.y, float(pr[2]))


func estado() -> Dictionary:
	return {"descargas": descargas.duplicate(), "total": total, "rng": _rng.state}


func restaurar(d: Dictionary) -> void:
	descargas = d.get("descargas", {}).duplicate()
	total = int(d.get("total", 0))
	if d.has("rng"):
		_rng.state = d.rng
