class_name RedeEnergia
extends RefCounted
## Postes ligam-se entre si até `raio_fio`; cada poste alimenta o que estiver no quadrado de `raio_cobertura`.
## Cada rede (componente conexo) divide a geração entre o consumo: satisfação = min(1, geração / demanda).
## Geradores queimam combustível do próprio estoque (MJ); sem combustível não geram.

var postes: Array[Dictionary] = []          ## {pos: Vector2, raio_fio, raio_cobertura}
var membros: Array[Dictionary] = []         ## {pos: Vector2, kw (+consome / −gera), obj, combustivel_mj}
var satisfacao_por_rede: Dictionary = {}
var _rede_do_poste := PackedInt32Array()


func adicionar_poste(pos: Vector2, raio_fio := 7.5, raio_cobertura := 2.5) -> void:
	postes.append({"pos": pos, "raio_fio": raio_fio, "raio_cobertura": raio_cobertura})
	_recalcular_redes()


func adicionar_membro(pos: Vector2, kw: float, obj: Object = null, combustivel_mj := 0.0) -> Dictionary:
	var m := {"pos": pos, "kw": kw, "obj": obj, "combustivel_mj": combustivel_mj, "rede": -1}
	membros.append(m)
	_ligar(m)
	return m


func _recalcular_redes() -> void:
	var n := postes.size()
	var pai := PackedInt32Array()
	pai.resize(n)
	for i in n:
		pai[i] = i
	for i in n:
		for j in range(i + 1, n):
			var r: float = minf(postes[i].raio_fio, postes[j].raio_fio)
			if (postes[i].pos as Vector2).distance_to(postes[j].pos) <= r:
				var a := _raiz(pai, i)
				var b := _raiz(pai, j)
				if a != b:
					pai[a] = b
	_rede_do_poste.resize(n)
	for i in n:
		_rede_do_poste[i] = _raiz(pai, i)
	for m in membros:
		_ligar(m)


func _raiz(pai: PackedInt32Array, i: int) -> int:
	while pai[i] != i:
		pai[i] = pai[pai[i]]
		i = pai[i]
	return i


func _ligar(m: Dictionary) -> void:
	m.rede = -1
	for i in postes.size():
		var d: Vector2 = ((m.pos as Vector2) - (postes[i].pos as Vector2)).abs()
		var rc: float = postes[i].raio_cobertura
		if d.x <= rc and d.y <= rc:
			m.rede = _rede_do_poste[i]
			return


## dt em s. Atualiza satisfação de cada rede e o `energia` dos objetos ligados.
func tick(dt: float) -> void:
	var geracao := {}
	var demanda := {}
	for m in membros:
		if m.rede < 0:
			continue
		if m.kw < 0.0:
			var disponivel: float = m.combustivel_mj * 1000.0 / dt if dt > 0 else 0.0   # kW que o estoque aguenta neste passo
			geracao[m.rede] = float(geracao.get(m.rede, 0.0)) + minf(-m.kw, disponivel)
		else:
			demanda[m.rede] = float(demanda.get(m.rede, 0.0)) + m.kw
	satisfacao_por_rede.clear()
	for r in demanda:
		satisfacao_por_rede[r] = clampf(float(geracao.get(r, 0.0)) / demanda[r], 0.0, 1.0) if demanda[r] > 0 else 1.0
	# geradores gastam só o que a rede usou
	for m in membros:
		if m.rede < 0:
			if m.obj != null and m.kw > 0: m.obj.set("energia", 0.0)
			continue
		if m.kw < 0.0:
			var usado: float = float(demanda.get(m.rede, 0.0)) * float(satisfacao_por_rede.get(m.rede, 0.0))
			var ger_total: float = maxf(float(geracao.get(m.rede, 0.0)), 1e-9)
			var minha: float = minf(-m.kw, m.combustivel_mj * 1000.0 / dt)
			m.combustivel_mj = maxf(0.0, m.combustivel_mj - usado * (minha / ger_total) * dt / 1000.0)
		elif m.obj != null:
			m.obj.set("energia", float(satisfacao_por_rede.get(m.rede, 0.0)))
