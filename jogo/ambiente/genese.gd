class_name Genese
extends RefCounted
## Colônias e receptor de cápsulas (proliferação; pesquisa "colonias"; regra "colonia" no posto avançado e "receptor"
## no receptor de cápsulas). Lógica pura:
##  - colônia = posto avançado que nasceu de um núcleo-semente lançado depois da pesquisa Colônias (`colonia` na
##    estrutura; o Lancador marca). Cada colônia de pé fabrica 1 pacote gênese a cada `genese_s` (30 s) — o pacote
##    gênese não tem receita: só as colônias o produzem;
##  - o pacote vai por cápsula (voo em arco a `velocidade` m/s) ao receptor de cápsulas com energia e lugar (contando
##    as que estão no ar) mais perto da colônia. Sem receptor, fica no estoque da própria colônia (até `guarda`) e sai
##    na próxima cápsula;
##  - a cápsula que chega entra no `recebido` do receptor (guardado na estrutura; os braços tiram) e o receptor toca o
##    laço do estudo uma vez (garras, empurrador, roletes). Receptor que sumiu ou encheu no meio do voo: perdida.
## Grade: +x leste, +y norte.

const LACO_S := 4.0

var mapa: MapaOcupacao
var fabrica: Fabrica                         ## estoque das colônias (baus) e energia dos receptores
var voos: Array[Dictionary] = []             ## {de, para, t, total, altura, receptor, item, colonia}
var eventos: Array[Dictionary] = []          ## capsula_enviada {colonia, receptor}, capsula_chegou {receptor}, capsula_perdida {receptor}
var _chegou: Dictionary = {}                 ## receptor → s desde a última cápsula (anima enquanto < LACO_S)


func _init(p_mapa: MapaOcupacao, p_fabrica: Fabrica) -> void:
	mapa = p_mapa
	fabrica = p_fabrica


static func cfg(nome: String) -> Dictionary:
	return Registro.estruturas.get(nome, {}).get("posto", {}).get("colonia", {})


static func eh_receptor(nome: String) -> bool:
	return Registro.estruturas.get(nome, {}).has("receptor")


func eh_colonia(id: int) -> bool:
	return mapa.estruturas.has(id) and bool(mapa.estruturas[id].get("colonia", false)) and not cfg(mapa.estruturas[id].nome).is_empty()


func colonias() -> Array[int]:
	var out: Array[int] = []
	for id in mapa.estruturas:
		if eh_colonia(id):
			out.append(id)
	return out


func receptores() -> Array[int]:
	var out: Array[int] = []
	for id in mapa.estruturas:
		if eh_receptor(mapa.estruturas[id].nome):
			out.append(id)
	return out


func centro(id: int) -> Vector2:
	var e: Dictionary = mapa.estruturas[id]
	return Grade.centro_da_area(e.minimo, e.area, e.rot)


func recebido(id: int) -> Dictionary:
	return Fabrica.campo(mapa.estruturas[id], "recebido")


func capacidade(id: int) -> int:
	return int(Registro.estruturas[mapa.estruturas[id].nome].receptor.get("capacidade", 100))


static func _total(d: Dictionary) -> int:
	var n := 0
	for k in d:
		n += int(d[k])
	return n


func a_caminho(rid: int) -> int:
	return voos.filter(func(v): return int(v.receptor) == rid).size()


func energia_de(id: int) -> float:
	if not mapa.estruturas.has(id) or mapa.estruturas[id].get("desligada", false):
		return 0.0
	return fabrica.energia(id) if fabrica != null else 1.0


## Receptor com energia e lugar mais perto do ponto; -1 se nenhum.
func receptor_para(p: Vector2) -> int:
	var melhor := -1
	var md := INF
	for rid in receptores():
		if energia_de(rid) <= 0.0 or _total(recebido(rid)) + a_caminho(rid) >= capacidade(rid):
			continue
		var d := centro(rid).distance_to(p)
		if d < md:
			md = d
			melhor = rid
	return melhor


## Pacotes gênese esperando no estoque da colônia (sem receptor).
func esperando(id: int) -> int:
	if fabrica == null or not fabrica.baus.has(id):
		return 0
	return int(fabrica.baus[id].get(String(cfg(mapa.estruturas[id].nome).get("item", "pacote_genese")), 0))


## Segundos até o próximo pacote da colônia.
func falta_s(id: int) -> float:
	var c := cfg(mapa.estruturas[id].nome)
	return maxf(0.0, float(c.get("genese_s", 30.0)) - float(mapa.estruturas[id].get("genese_t", 0.0)))


func animando(rid: int) -> bool:
	return _chegou.has(rid) and float(_chegou[rid]) < LACO_S


func tick(dt: float) -> void:
	for id in colonias():
		var e: Dictionary = mapa.estruturas[id]
		var c := cfg(e.nome)
		e["genese_t"] = float(e.get("genese_t", 0.0)) + dt
		while float(e.genese_t) >= float(c.get("genese_s", 30.0)):
			e.genese_t = float(e.genese_t) - float(c.get("genese_s", 30.0))
			_produzir(id, c)
	for i in range(voos.size() - 1, -1, -1):
		var v: Dictionary = voos[i]
		v.t = float(v.t) + dt
		if float(v.t) >= float(v.total):
			voos.remove_at(i)
			_chegar(v)
	for rid in _chegou.keys():
		_chegou[rid] = float(_chegou[rid]) + dt
		if float(_chegou[rid]) > LACO_S or not mapa.estruturas.has(rid):
			_chegou.erase(rid)


func _produzir(id: int, c: Dictionary) -> void:
	var item := String(c.get("item", "pacote_genese"))
	var n := 1 + mini(esperando(id), 1)                    # o novo e, se havia, um que esperava
	if esperando(id) > 0:
		fabrica.baus[id][item] = esperando(id) - 1
	for i in n:
		var rid := receptor_para(centro(id))
		if rid >= 0:
			var de := centro(id)
			var para := centro(rid)
			var d := de.distance_to(para)
			voos.append({"de": de, "para": para, "t": 0.0, "total": maxf(d / float(c.get("velocidade", 60.0)), 0.5),
					"altura": maxf(d * float(c.get("arco", 0.25)), 4.0), "receptor": rid, "item": item, "colonia": id})
			eventos.append({"tipo": "capsula_enviada", "colonia": id, "receptor": rid})
		elif fabrica != null and fabrica.baus.has(id) and esperando(id) < int(c.get("guarda", 20)):
			fabrica.baus[id][item] = esperando(id) + 1          # sem receptor: espera no estoque da colônia


func _chegar(v: Dictionary) -> void:
	var rid := int(v.receptor)
	if not mapa.estruturas.has(rid) or not eh_receptor(mapa.estruturas[rid].nome) or _total(recebido(rid)) >= capacidade(rid):
		eventos.append({"tipo": "capsula_perdida", "receptor": rid})
		return
	var r := recebido(rid)
	r[v.item] = int(r.get(v.item, 0)) + 1
	_chegou[rid] = 0.0
	eventos.append({"tipo": "capsula_chegou", "receptor": rid})


func estado() -> Dictionary:
	return {"voos": voos.map(func(v): return (v as Dictionary).duplicate())}


func restaurar(d: Dictionary) -> void:
	voos.clear()
	_chegou.clear()
	for v in d.get("voos", []):
		voos.append((v as Dictionary).duplicate())
