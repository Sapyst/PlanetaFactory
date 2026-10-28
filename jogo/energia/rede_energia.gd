class_name RedeEnergia
extends RefCounted
## Rede elétrica como grafo de FIOS: nós = postes, torres sem fio, geradores e máquinas; arestas = ligações
## (mapa: "fios" de cada estrutura, criadas pela Fiacao). Cada pedaço ligado (componente conexo) divide a geração
## entre o consumo: satisfação = min(1, geração / demanda). Geradores queimam combustível do próprio estoque (MJ);
## sem combustível não geram. Máquina com mais de uma fonte junta as redes (é o mesmo circuito).

var nos: Dictionary = {}                    ## id → {kw (+consome / −gera), combustivel_mj, rede}
var _arestas: Dictionary = {}               ## id → Array[int]
var satisfacao_por_rede: Dictionary = {}


func adicionar(id: int, kw: float, combustivel_mj := 0.0) -> Dictionary:
	var n := {"kw": kw, "combustivel_mj": combustivel_mj, "rede": -1}
	nos[id] = n
	if not _arestas.has(id):
		_arestas[id] = []
	return n


func ligar(a: int, b: int) -> void:
	if not nos.has(a) or not nos.has(b) or a == b:
		return
	_arestas[a].append(b)
	_arestas[b].append(a)


## Componentes conexos (busca em largura).
func calcular() -> void:
	for id in nos:
		nos[id].rede = -1
	var n := 0
	for id in nos:
		if nos[id].rede >= 0:
			continue
		var fila: Array[int] = [id]
		nos[id].rede = n
		while not fila.is_empty():
			var x: int = fila.pop_back()
			for y in _arestas[x]:
				if nos[y].rede < 0:
					nos[y].rede = n
					fila.append(y)
		n += 1


func satisfacao(id: int) -> float:
	if not nos.has(id):
		return 0.0
	return float(satisfacao_por_rede.get(nos[id].rede, 0.0))


## Ligado a algum gerador (mesmo que sem combustível)?
func tem_fonte(id: int) -> bool:
	if not nos.has(id):
		return false
	var r: int = nos[id].rede
	for x in nos:
		if nos[x].rede == r and nos[x].kw < 0.0:
			return true
	return false


## dt em s. Atualiza a satisfação de cada rede e gasta o combustível dos geradores na medida do uso.
func tick(dt: float) -> void:
	var geracao := {}
	var demanda := {}
	for id in nos:
		var m: Dictionary = nos[id]
		if m.kw < 0.0:
			var disponivel: float = m.combustivel_mj * 1000.0 / dt if dt > 0 else 0.0   # kW que o estoque aguenta neste passo
			geracao[m.rede] = float(geracao.get(m.rede, 0.0)) + minf(-m.kw, disponivel)
		elif m.kw > 0.0:
			demanda[m.rede] = float(demanda.get(m.rede, 0.0)) + m.kw
	satisfacao_por_rede.clear()
	for r in demanda:
		satisfacao_por_rede[r] = clampf(float(geracao.get(r, 0.0)) / demanda[r], 0.0, 1.0) if demanda[r] > 0 else 1.0
	for id in nos:
		var m: Dictionary = nos[id]
		if m.kw >= 0.0:
			continue
		var usado: float = float(demanda.get(m.rede, 0.0)) * float(satisfacao_por_rede.get(m.rede, 0.0))
		var ger_total: float = maxf(float(geracao.get(m.rede, 0.0)), 1e-9)
		var minha: float = minf(-m.kw, m.combustivel_mj * 1000.0 / dt)
		m.combustivel_mj = maxf(0.0, m.combustivel_mj - usado * (minha / ger_total) * dt / 1000.0)
