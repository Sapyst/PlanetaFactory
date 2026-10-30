class_name Farol
extends RefCounted
## Farol de cristal (proliferação; pesquisa "farol_cristal", regra "farol" em estruturas.json). Lógica pura:
##  - o farol ligado e com energia acende quando escurece (luz do dia abaixo de `acende_abaixo`) e fica aceso a noite
##    toda: uma luz de `raio` m (10) em volta dele (o desenho põe a luz; a força acompanha o escuro e a energia);
##  - aceso, o que está na luz fica descoberto (sai da névoa) e as aranhas que entram nela são vistas: a primeira que
##    chega depois de `aviso_s` sem aranha nova dá um aviso ("aranhas chegando") com o rumo delas.
## Grade: +x leste, +y norte.

var mapa: MapaOcupacao
var descoberta: Descoberta
var colonia: Colonia                  ## (opcional) as aranhas que a luz mostra
var energia: Callable                 ## func(id) -> 0..1 (Fabrica.energia); sem ela, todo farol conta com energia plena
var luz_dia: Callable                 ## func() -> 0..1 (Clima.luz_dia); sem ela, é sempre dia (apagado)
var farois: Dictionary = {}           ## id → {vistas: {aranha: true}, aviso_t: s desde o último aviso}
var eventos: Array[Dictionary] = []   ## {tipo: "aranhas_no_farol", id, n, de: Vector2 (média das aranhas)}
var _versao := -1


func _init(p_mapa: MapaOcupacao, p_descoberta: Descoberta) -> void:
	mapa = p_mapa
	descoberta = p_descoberta


static func regra(nome: String) -> Dictionary:
	return Registro.estruturas.get(nome, {}).get("farol", {})


static func eh_farol(nome: String) -> bool:
	return not regra(nome).is_empty()


func _regra_id(id: int) -> Dictionary:
	return regra(mapa.estruturas[id].nome) if mapa.estruturas.has(id) else {}


func raio(id: int) -> float:
	return float(_regra_id(id).get("raio", 10.0))


func centro(id: int) -> Vector2:
	var e: Dictionary = mapa.estruturas[id]
	return Grade.centro_da_area(e.minimo, e.area, e.rot)


func energia_de(id: int) -> float:
	if not mapa.estruturas.has(id) or mapa.estruturas[id].get("desligada", false):
		return 0.0
	return clampf(float(energia.call(id)), 0.0, 1.0) if energia.is_valid() else 1.0


func dia() -> float:
	return clampf(float(luz_dia.call()), 0.0, 1.0) if luz_dia.is_valid() else 1.0


## Escuro o bastante para o farol acender (a regra do primeiro farol vale para todos: é a mesma peça).
func noite(id := -1) -> bool:
	var r := _regra_id(id) if id >= 0 else regra("farol_cristal")
	return dia() < float(r.get("acende_abaixo", 0.35))


func aceso(id: int) -> bool:
	return energia_de(id) > 0.0 and noite(id)


## Força da luz (0..1) para o desenho: cresce com o escuro (plena na noite fechada) e cai com pouca energia.
func forca(id: int) -> float:
	if not aceso(id):
		return 0.0
	var lim := float(_regra_id(id).get("acende_abaixo", 0.35))
	return clampf(0.35 + 0.65 * (1.0 - dia() / lim), 0.0, 1.0) * clampf(energia_de(id) * 1.5, 0.3, 1.0)


func _atualizar_lista() -> void:
	if mapa.versao == _versao:
		return
	_versao = mapa.versao
	for id in farois.keys():
		if not mapa.estruturas.has(id) or not eh_farol(mapa.estruturas[id].nome):
			farois.erase(id)
	for id in mapa.estruturas:
		if not farois.has(id) and eh_farol(mapa.estruturas[id].nome):
			farois[id] = {"vistas": {}, "aviso_t": 1.0e9}


## Ids dos faróis acesos agora.
func acesos() -> Array[int]:
	_atualizar_lista()
	var out: Array[int] = []
	for id in farois:
		if aceso(id):
			out.append(id)
	return out


## Aranhas dentro da luz do farol (vazio se apagado).
func aranhas_na_luz(id: int) -> Array[int]:
	var out: Array[int] = []
	if colonia == null or not aceso(id):
		return out
	var c := centro(id)
	var r := raio(id)
	for a in colonia.aranhas:
		if (colonia.aranhas[a].pos as Vector2).distance_to(c) <= r:
			out.append(a)
	return out


## O ponto está na luz de algum farol aceso?
func iluminado(p: Vector2) -> bool:
	for id in acesos():
		if p.distance_to(centro(id)) <= raio(id):
			return true
	return false


func tick(dt: float) -> void:
	_atualizar_lista()
	for id in farois:
		var f: Dictionary = farois[id]
		f.aviso_t = float(f.aviso_t) + dt
		if not aceso(id):
			f.vistas = {}
			continue
		descoberta.marcar_circulo(centro(id), raio(id))
		var agora := {}
		var novas: Array[int] = []
		for a in aranhas_na_luz(id):
			agora[a] = true
			if not (f.vistas as Dictionary).has(a):
				novas.append(a)
		f.vistas = agora
		if novas.is_empty() or float(f.aviso_t) < float(_regra_id(id).get("aviso_s", 30.0)):
			continue
		f.aviso_t = 0.0
		var soma := Vector2.ZERO
		for a in agora:
			soma += colonia.aranhas[a].pos as Vector2
		eventos.append({"tipo": "aranhas_no_farol", "id": id, "n": agora.size(), "de": soma / float(agora.size())})
