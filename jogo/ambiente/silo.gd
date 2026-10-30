class_name SiloLancamento
extends RefCounted
## Silo de lançamento (proliferação; pesquisa "silo_lancamento", regra "silo"). Lógica pura; o estado fica na própria
## estrutura do mapa (vai no salvamento):
##  - `silo_itens` (o que o braço pôs: só o que uma parte/carga pede, até `guarda` vezes) e `propelente` (fluido, até
##    `tanque`; `abastecer`);
##  - com energia, monta uma parte em `parte_s` (× energia) gastando `parte` + `parte_fluido`, até `partes` (100);
##  - com as partes prontas e a pesquisa da carga (`pesquisa_carga`, modo "carga_semente"), monta a carga-semente com
##    `carga` em `carga_s`;
##  - foguete pronto (partes + carga): `lancar` → `lancamento_s` de subida e o evento "foguete_lancado" — fim da
##    campanha (o silo esvazia e pode montar outro).
## O propelente entra pelo cano da boca leste (Fabrica._tick_silos_fluido). Os itens chegam por braço: casco de foguete e
## processador quântico (parte), núcleo-semente, mapa estelar e módulo de produtividade 3 (carga).

var mapa: MapaOcupacao
var energia: Callable                         ## func(id) -> 0..1; sem ela, energia plena
var carga_liberada: Callable                  ## func() -> bool (Pesquisa.modo_liberado("carga_semente")); sem ela, não
var eventos: Array[Dictionary] = []           ## parte_montada {id, partes}, carga_pronta {id}, lancamento_inicio {id}, foguete_lancado {id}
var _montando: Dictionary = {}                ## id → s desde o último avanço (anima enquanto < 0,5 s)
var lancando: Dictionary = {}                 ## id → s desde o começo do lançamento


func _init(p_mapa: MapaOcupacao) -> void:
	mapa = p_mapa


static func regra(nome: String) -> Dictionary:
	return Registro.estruturas.get(nome, {}).get("silo", {})


static func eh_silo(nome: String) -> bool:
	return not regra(nome).is_empty()


func _r(id: int) -> Dictionary:
	return regra(mapa.estruturas[id].nome)


func itens(id: int) -> Dictionary:
	return Fabrica.campo(mapa.estruturas[id], "silo_itens")


func partes(id: int) -> int:
	return int(mapa.estruturas[id].get("partes", 0))


func tem_carga(id: int) -> bool:
	return bool(mapa.estruturas[id].get("carga", false))


func propelente(id: int) -> float:
	return float(mapa.estruturas[id].get("propelente", 0.0))


## Põe fluido no tanque do silo (cano); devolve quanto entrou.
func abastecer(id: int, fluido: String, qtd: float) -> float:
	var r := _r(id)
	if not (r.get("parte_fluido", {}) as Dictionary).has(fluido):
		return 0.0
	var cabe := maxf(0.0, float(r.get("tanque", 500)) - propelente(id))
	var entra := minf(cabe, qtd)
	mapa.estruturas[id]["propelente"] = propelente(id) + entra
	return entra


## O braço pode pôr este item agora? (só o que uma parte ou a carga pede, até `guarda` vezes.)
static func aceita(e: Dictionary, item: String) -> bool:
	var r := regra(e.nome)
	var pede := 0
	for grupo in ["parte", "carga"]:
		pede = maxi(pede, int((r.get(grupo, {}) as Dictionary).get(item, 0)))
	if pede <= 0:
		return false
	var dentro := int((e.get("silo_itens", {}) as Dictionary).get(item, 0))
	return dentro < pede * int(r.get("guarda", 2))


func energia_de(id: int) -> float:
	if not mapa.estruturas.has(id) or mapa.estruturas[id].get("desligada", false):
		return 0.0
	return clampf(float(energia.call(id)), 0.0, 1.0) if energia.is_valid() else 1.0


func _tem(id: int, pede: Dictionary) -> bool:
	var it := itens(id)
	for k in pede:
		if int(it.get(k, 0)) < int(pede[k]):
			return false
	return true


func _gastar(id: int, pede: Dictionary) -> void:
	var it := itens(id)
	for k in pede:
		it[k] = int(it.get(k, 0)) - int(pede[k])


func pronto(id: int) -> bool:
	return partes(id) >= int(_r(id).get("partes", 100)) and tem_carga(id)


## O que falta agora para avançar (painel): "" = montando; sem_energia, faltam_itens, falta_propelente,
## falta_pesquisa_carga, pronto, lancando.
func motivo(id: int) -> String:
	var r := _r(id)
	if lancando.has(id):
		return "lancando"
	if pronto(id):
		return "pronto"
	if energia_de(id) <= 0.0:
		return "sem_energia"
	if partes(id) < int(r.get("partes", 100)):
		if not _tem(id, r.get("parte", {})):
			return "faltam_itens"
		for f in r.get("parte_fluido", {}):
			if propelente(id) < float(r.parte_fluido[f]):
				return "falta_propelente"
		return ""
	if not (carga_liberada.is_valid() and bool(carga_liberada.call())):
		return "falta_pesquisa_carga"
	if not _tem(id, r.get("carga", {})):
		return "faltam_itens"
	return ""


func montando(id: int) -> bool:
	return lancando.has(id) or (_montando.has(id) and float(_montando[id]) < 0.5)


func todos() -> Array[int]:
	var out: Array[int] = []
	for id in mapa.estruturas:
		if eh_silo(mapa.estruturas[id].nome):
			out.append(id)
	return out


func tick(dt: float) -> void:
	for k in _montando.keys():
		_montando[k] = float(_montando[k]) + dt
	for id in todos():
		var e: Dictionary = mapa.estruturas[id]
		var r := _r(id)
		if lancando.has(id):
			lancando[id] = float(lancando[id]) + dt
			if float(lancando[id]) >= float(r.get("lancamento_s", 6.0)):
				lancando.erase(id)
				e["partes"] = 0
				e["carga"] = false
				e["lancados"] = int(e.get("lancados", 0)) + 1
				eventos.append({"tipo": "foguete_lancado", "id": id})
			continue
		if motivo(id) != "":
			continue
		var montando_parte := partes(id) < int(r.get("partes", 100))
		e["silo_t"] = float(e.get("silo_t", 0.0)) + dt * energia_de(id)
		_montando[id] = 0.0
		if montando_parte and float(e.silo_t) >= float(r.get("parte_s", 10.0)):
			e.silo_t = 0.0
			_gastar(id, r.get("parte", {}))
			for f in r.get("parte_fluido", {}):
				e["propelente"] = propelente(id) - float(r.parte_fluido[f])
			e["partes"] = partes(id) + 1
			eventos.append({"tipo": "parte_montada", "id": id, "partes": partes(id)})
		elif not montando_parte and float(e.silo_t) >= float(r.get("carga_s", 30.0)):
			e.silo_t = 0.0
			_gastar(id, r.get("carga", {}))
			e["carga"] = true
			eventos.append({"tipo": "carga_pronta", "id": id})


## Começa o lançamento (painel). Só com o foguete pronto.
func lancar(id: int) -> bool:
	if not mapa.estruturas.has(id) or not pronto(id) or lancando.has(id):
		return false
	lancando[id] = 0.0
	eventos.append({"tipo": "lancamento_inicio", "id": id})
	return true


## Altura do foguete acima do silo (m) durante o lançamento, para o desenho (acelera: s²).
func subida(id: int) -> float:
	if not lancando.has(id):
		return 0.0
	return 3.0 * pow(maxf(float(lancando[id]) - 1.0, 0.0), 2.0)
