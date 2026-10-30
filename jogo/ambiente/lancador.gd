class_name Lancador
extends RefCounted
## Lançador de sementes (proliferação; pesquisa "nucleo_semente", regra "lancador" em estruturas.json). Lógica pura:
##  - o núcleo-semente entra por braço (Fabrica._NoLancador guarda em `sementes` na própria estrutura do mapa);
##  - o alvo é um rumo (8, de norte no sentido horário) e uma distância (alcance_min…alcance m) escolhidos no painel e
##    guardados na estrutura (`alvo_rumo`, `alvo_dist`);
##  - com semente, alvo válido e energia, carrega `carga_s` (÷ energia); pronto, toca o disparo (o laço do estudo, do
##    começo) e a cápsula sai em `disparo_s`; voa em arco a `velocidade` m/s até o alvo;
##  - onde pousa nasce a estrutura `pousa` (o posto avançado, núcleo-filho) no lugar seco, plano e livre mais perto do
##    alvo (até `procura` tiles; árvores e pedras são limpas). O chunk do pouso sai da névoa e os ninhos dele passam a
##    existir. Sem lugar no pouso, a semente se perde (aviso). O mundo cria o nó do posto pelo relatório do evento.
##    Com a pesquisa Colônias, o posto que nasce é uma colônia (`colonia` na estrutura; kit no estoque; Genese).
## Grade: +x leste, +y norte.

const RUMOS := ["norte", "nordeste", "leste", "sudeste", "sul", "sudoeste", "oeste", "noroeste"]
const LACO_S := 4.0                         ## duração do laço do estudo (o disparo toca uma vez)
const SEM_LUGAR := Vector2i(2147483647, 0)

var mapa: MapaOcupacao
var descoberta: Descoberta
var colonia: Colonia                        ## (opcional) cria os ninhos do chunk do pouso
var energia: Callable                       ## func(id) -> 0..1 (Fabrica.energia); sem ela, energia plena
var colonias: Callable                      ## func() -> bool: pesquisa Colônias (a semente vira colônia); sem ela, não
var lancadores: Dictionary = {}             ## id → {t: s de carga, disparo: s desde o começo do disparo (-1 = parado), saiu}
var voos: Array[Dictionary] = []            ## {de: Vector2, para: Vector2, t, total, altura, lancador}
var eventos: Array[Dictionary] = []         ## disparo_inicio {id}, semente_lancada {id, para}, semente_pousou {id, para, rel}, semente_perdida {para}
var _versao := -1
var _pousos: Dictionary = {}                ## cache de lugar_de_pouso: chave → [versão do mapa, resultado]


func _init(p_mapa: MapaOcupacao, p_descoberta: Descoberta) -> void:
	mapa = p_mapa
	descoberta = p_descoberta


static func regra(nome: String) -> Dictionary:
	return Registro.estruturas.get(nome, {}).get("lancador", {})


static func eh_lancador(nome: String) -> bool:
	return not regra(nome).is_empty()


static func direcao(rumo: int) -> Vector2:
	return Vector2.from_angle(PI / 2.0 - posmod(rumo, 8) * PI / 4.0)


func _regra_id(id: int) -> Dictionary:
	return regra(mapa.estruturas[id].nome) if mapa.estruturas.has(id) else {}


func centro(id: int) -> Vector2:
	var e: Dictionary = mapa.estruturas[id]
	return Grade.centro_da_area(e.minimo, e.area, e.rot)


func sementes(id: int) -> int:
	return int(mapa.estruturas[id].get("sementes", 0)) if mapa.estruturas.has(id) else 0


func rumo(id: int) -> int:
	return posmod(int(mapa.estruturas[id].get("alvo_rumo", 0)), 8)


func distancia(id: int) -> float:
	var r := _regra_id(id)
	return clampf(float(mapa.estruturas[id].get("alvo_dist", 200)), float(r.get("alcance_min", 60)), float(r.get("alcance", 400)))


## Escolhe o alvo (painel): rumo 0..7 (N, NE, L, SE, S, SO, O, NO) e distância em m (presa ao alcance).
func mirar(id: int, p_rumo: int, dist: float) -> void:
	var r := _regra_id(id)
	mapa.estruturas[id]["alvo_rumo"] = posmod(p_rumo, 8)
	mapa.estruturas[id]["alvo_dist"] = int(clampf(dist, float(r.get("alcance_min", 60)), float(r.get("alcance", 400))))


func alvo(id: int) -> Vector2:
	return centro(id) + direcao(rumo(id)) * distancia(id)


func energia_de(id: int) -> float:
	if not mapa.estruturas.has(id) or mapa.estruturas[id].get("desligada", false):
		return 0.0
	return clampf(float(energia.call(id)), 0.0, 1.0) if energia.is_valid() else 1.0


## Mínimo (canto sudoeste) da estrutura que nasce no pouso: o lugar seco, plano e livre mais perto de `p`, até
## `procura` tiles; SEM_LUGAR se nenhum.
func lugar_de_pouso(p: Vector2, nome := "posto_avancado", procura := 6) -> Vector2i:
	var chave := "%s|%s|%d" % [p.round(), nome, procura]
	if _pousos.has(chave) and int(_pousos[chave][0]) == mapa.versao:
		return _pousos[chave][1]
	if _pousos.size() > 64:
		_pousos.clear()
	var r := _lugar_de_pouso(p, nome, procura)
	_pousos[chave] = [mapa.versao, r]
	return r


## Parado sem trabalho (sem semente, desligado, alvo inválido): puxa só uma fração da energia.
func ocioso(id: int) -> bool:
	return not motivo(id) in ["", "disparando", "sem_energia"]


func _lugar_de_pouso(p: Vector2, nome: String, procura: int) -> Vector2i:
	var area: Vector2i = Registro.area(nome)
	var base := Vector2i((p - Vector2(area) * 0.5).round())
	var cand: Array = []
	for dy in range(-procura, procura + 1):
		for dx in range(-procura, procura + 1):
			cand.append([dx * dx + dy * dy, dy, dx])
	cand.sort()
	for c in cand:
		var m := base + Vector2i(c[2], c[1])
		if _pode_pousar(m, area):
			return m
	return SEM_LUGAR


func _pode_pousar(minimo: Vector2i, area: Vector2i) -> bool:
	var g := mapa.gerador
	var n0 := g.nivel(minimo)
	for t in Grade.tiles_da_area(minimo, area, 0):
		if g.nivel(t) != n0 or g.em_encosta(t) or mapa.tiles.has(t) or g.eh_agua(g.terreno(t)):
			return false
		for n in range(1, MapaOcupacao.NIVEIS + 1):
			if mapa.altos.has(Vector3i(t.x, t.y, n)):
				return false
	return true


## Por que não carrega agora ("" = carregando): sem_semente, desligado, sem_energia, alvo_invalido, disparando.
func motivo(id: int) -> String:
	if not mapa.estruturas.has(id):
		return "sem_lancador"
	if lancadores.has(id) and float(lancadores[id].disparo) >= 0.0:
		return "disparando"
	if sementes(id) <= 0:
		return "sem_semente"
	if mapa.estruturas[id].get("desligada", false):
		return "desligado"
	if energia_de(id) <= 0.0:
		return "sem_energia"
	var r := _regra_id(id)
	if lugar_de_pouso(alvo(id), String(r.get("pousa", "posto_avancado")), int(r.get("procura", 6))) == SEM_LUGAR:
		return "alvo_invalido"
	return ""


## Carga de 0 a 1 (painel).
func carga(id: int) -> float:
	if not lancadores.has(id):
		return 0.0
	return clampf(float(lancadores[id].t) / float(_regra_id(id).get("carga_s", 20.0)), 0.0, 1.0)


func disparando(id: int) -> bool:
	return lancadores.has(id) and float(lancadores[id].disparo) >= 0.0


func _atualizar_lista() -> void:
	if mapa.versao == _versao:
		return
	_versao = mapa.versao
	for id in lancadores.keys():
		if not mapa.estruturas.has(id) or not eh_lancador(mapa.estruturas[id].nome):
			lancadores.erase(id)
	for id in mapa.estruturas:
		if not lancadores.has(id) and eh_lancador(mapa.estruturas[id].nome):
			lancadores[id] = {"t": 0.0, "disparo": -1.0, "saiu": false}


func tick(dt: float) -> void:
	_atualizar_lista()
	for id in lancadores:
		var s: Dictionary = lancadores[id]
		var r := _regra_id(id)
		if float(s.disparo) >= 0.0:
			s.disparo = float(s.disparo) + dt
			if not s.saiu and float(s.disparo) >= float(r.get("disparo_s", 2.083)):
				s.saiu = true
				_lancar(id)
			if float(s.disparo) >= LACO_S:
				s.disparo = -1.0
			continue
		var mot := motivo(id)
		if mot == "sem_semente":
			s.t = 0.0
		if mot != "":
			continue
		s.t = float(s.t) + dt * energia_de(id)
		if float(s.t) >= float(r.get("carga_s", 20.0)):
			s.t = 0.0
			s.disparo = 0.0
			s.saiu = false
			eventos.append({"tipo": "disparo_inicio", "id": id})
	for i in range(voos.size() - 1, -1, -1):
		var v: Dictionary = voos[i]
		v.t = float(v.t) + dt
		if float(v.t) >= float(v.total):
			voos.remove_at(i)
			_pousar(v)


func _lancar(id: int) -> void:
	var r := _regra_id(id)
	var e: Dictionary = mapa.estruturas[id]
	e["sementes"] = maxi(0, sementes(id) - 1)
	var de := centro(id)
	var para := alvo(id)
	var d := de.distance_to(para)
	voos.append({"de": de, "para": para, "t": 0.0, "total": d / float(r.get("velocidade", 40.0)), "altura": d * float(r.get("arco", 0.3)),
			"lancador": id, "pousa": String(r.get("pousa", "posto_avancado")), "procura": int(r.get("procura", 6))})
	eventos.append({"tipo": "semente_lancada", "id": id, "para": para})


## Onde a cápsula está no voo `v` (grade) e a altura dela (m acima do chão de saída), para o desenho.
static func posicao_no_voo(v: Dictionary) -> Vector3:
	var f := clampf(float(v.t) / maxf(float(v.total), 1e-6), 0.0, 1.0)
	var p: Vector2 = (v.de as Vector2).lerp(v.para, f)
	return Vector3(p.x, p.y, 4.0 * float(v.altura) * f * (1.0 - f))


func _pousar(v: Dictionary) -> void:
	var nome := String(v.get("pousa", "posto_avancado"))
	var m := lugar_de_pouso(v.para, nome, int(v.get("procura", 6)))
	if m == SEM_LUGAR:
		eventos.append({"tipo": "semente_perdida", "para": v.para})
		return
	var limpos: Array[Dictionary] = []
	for t in Grade.tiles_da_area(m, Registro.area(nome), 0):
		if not mapa.limpos.has(t):
			var o := mapa.limpar_obstaculo(t)
			if not o.is_empty():
				limpos.append({"tile": t, "tiles": Grade.tiles_da_area(o.ancora, o.area, 0)})
	var pid := mapa.colocar(nome, m, 0)
	if pid < 0:
		eventos.append({"tipo": "semente_perdida", "para": v.para})
		return
	var col: Dictionary = Registro.estruturas.get(nome, {}).get("posto", {}).get("colonia", {})
	var e_colonia := not col.is_empty() and colonias.is_valid() and bool(colonias.call())
	if e_colonia:                                   # pesquisa Colônias: nasce colônia, com o kit no estoque
		mapa.estruturas[pid]["colonia"] = true
		mapa.estruturas[pid]["kit_inicial"] = (col.get("kit", {}) as Dictionary).duplicate()
	Fiacao.ligar_novo(mapa, pid)
	var c := Grade.centro_da_area(m, Registro.area(nome), 0)
	var k := Grade.chunk_de(Vector2i(c.floor()))
	descoberta.marcar_chunk(k)
	if colonia != null:
		colonia.descobrir_chunk(k)
	var rel := {"colocados": [pid] as Array[int], "removidos": [] as Array[Dictionary], "limpos": limpos,
			"restaurados": [] as Array[Dictionary], "trens": [] as Array[Dictionary], "estoque": {}, "locais": {}, "aplainados": []}
	eventos.append({"tipo": "semente_pousou", "id": pid, "para": c, "rel": rel, "lancador": v.get("lancador", -1), "colonia": e_colonia})


func estado() -> Dictionary:
	var l := {}
	for id in lancadores:
		l[id] = (lancadores[id] as Dictionary).duplicate()
	return {"lancadores": l, "voos": voos.map(func(v): return (v as Dictionary).duplicate())}


func restaurar(d: Dictionary) -> void:
	lancadores.clear()
	voos.clear()
	for id in d.get("lancadores", {}):
		var s: Dictionary = d.lancadores[id]
		lancadores[int(id)] = {"t": float(s.get("t", 0.0)), "disparo": float(s.get("disparo", -1.0)), "saiu": bool(s.get("saiu", false))}
	for v in d.get("voos", []):
		voos.append((v as Dictionary).duplicate())
	_versao = -1
