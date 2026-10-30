class_name Transportador
extends RefCounted
## Transportador quântico (proliferação; pesquisa "transportador_quantico", regra "transportador"). Lógica pura:
##  - o braço põe itens na `entrada` (até 20) e tira da `saida` (até 200); as duas ficam na própria estrutura do mapa
##    (Fabrica.campo; vão no salvamento);
##  - com energia, manda `taxa` itens/s (× energia) da entrada para a saída de outro transportador do mesmo canal
##    (A–D, escolhido no painel) com lugar — em rodízio entre os destinos —, sem trilho e a qualquer distância
##    (entre colônias). Sem destino com lugar, a entrada enche e o braço espera.

const ATIVO_S := 1.0                          ## anima por este tempo depois de mandar/receber

var mapa: MapaOcupacao
var energia: Callable                         ## func(id) -> 0..1 (Fabrica.energia); sem ela, energia plena
var _acc: Dictionary = {}                     ## id → itens acumulados para mandar (fração)
var _vez: Dictionary = {}                     ## id → índice do rodízio
var _ativo: Dictionary = {}                   ## id → s desde a última troca
var enviados: Dictionary = {}                 ## id → total mandado (painel)


func _init(p_mapa: MapaOcupacao) -> void:
	mapa = p_mapa


static func regra(nome: String) -> Dictionary:
	return Registro.estruturas.get(nome, {}).get("transportador", {})


static func eh_transportador(nome: String) -> bool:
	return not regra(nome).is_empty()


func canal(id: int) -> String:
	return String(mapa.estruturas[id].get("canal", "A"))


func mudar_canal(id: int, c: String) -> void:
	mapa.estruturas[id]["canal"] = c


func entrada(id: int) -> Dictionary:
	return Fabrica.campo(mapa.estruturas[id], "entrada")


func saida(id: int) -> Dictionary:
	return Fabrica.campo(mapa.estruturas[id], "saida")


static func total(d: Dictionary) -> int:
	var n := 0
	for k in d:
		n += int(d[k])
	return n


func energia_de(id: int) -> float:
	if not mapa.estruturas.has(id) or mapa.estruturas[id].get("desligada", false):
		return 0.0
	return clampf(float(energia.call(id)), 0.0, 1.0) if energia.is_valid() else 1.0


func todos() -> Array[int]:
	var out: Array[int] = []
	for id in mapa.estruturas:
		if eh_transportador(mapa.estruturas[id].nome):
			out.append(id)
	out.sort()
	return out


## Os outros transportadores do mesmo canal (destinos possíveis).
func pares(id: int) -> Array[int]:
	var c := canal(id)
	return todos().filter(func(o): return o != id and canal(o) == c)


func trabalhando(id: int) -> bool:
	return _ativo.has(id) and float(_ativo[id]) < ATIVO_S


func tick(dt: float) -> void:
	for k in _ativo.keys():
		_ativo[k] = float(_ativo[k]) + dt
	for id in todos():
		var r := regra(mapa.estruturas[id].nome)
		var ent := entrada(id)
		var en := energia_de(id)
		if en <= 0.0 or total(ent) <= 0:
			_acc[id] = 0.0
			continue
		_acc[id] = minf(float(_acc.get(id, 0.0)) + float(r.get("taxa", 5)) * dt * en, float(r.get("taxa", 5)))
		var ps := pares(id)
		while float(_acc[id]) >= 1.0 and total(ent) > 0 and not ps.is_empty():
			var dest := -1
			for i in ps.size():
				var o: int = ps[(int(_vez.get(id, 0)) + i) % ps.size()]
				if total(saida(o)) < int(regra(mapa.estruturas[o].nome).get("saida", 200)):
					dest = o
					_vez[id] = (int(_vez.get(id, 0)) + i + 1) % ps.size()
					break
			if dest < 0:
				break
			var item := ""
			for k in ent:
				if int(ent[k]) > 0:
					item = k
					break
			ent[item] = int(ent[item]) - 1
			if int(ent[item]) <= 0:
				ent.erase(item)
			var sa := saida(dest)
			sa[item] = int(sa.get(item, 0)) + 1
			_acc[id] = float(_acc[id]) - 1.0
			enviados[id] = int(enviados.get(id, 0)) + 1
			_ativo[id] = 0.0
			_ativo[dest] = 0.0
