class_name RedeEnergia
extends RefCounted
## Rede elétrica como grafo de FIOS: nós = postes, torres sem fio, geradores e máquinas; arestas = ligações
## (mapa: "fios" de cada estrutura, criadas pela Fiacao). Cada pedaço ligado (componente conexo) divide a geração
## entre o consumo: satisfação = min(1, geração / demanda). Geradores queimam combustível do próprio estoque (MJ);
## sem combustível não geram. Máquina com mais de uma fonte junta as redes (é o mesmo circuito).
## Fonte `livre` (núcleo, painel solar, turbina eólica) não gasta nada e é usada primeiro; o combustível só cobre o
## que faltar. Acumulador guarda a sobra (até acum_kw de carga) e devolve quando falta.
## De quem vem a energia (cor dos postes e cabos): por rede, quem ENTREGOU mais kW domina sem mistura: "base" (núcleo)
## ou "geradores" (todo o resto que gera, inclusive acumulador descarregando). Só desenho: não muda nenhuma conta.

const BASE := "base"
const GERADORES := "geradores"
const HISTERESE := 0.10                     ## o outro lado precisa passar 10% para virar (não pisca quando empatam)

var nos: Dictionary = {}                    ## id → {kw (+consome / −gera), combustivel_mj, rede, livre, acum_cap, acum_mj, acum_kw}
var _arestas: Dictionary = {}               ## id → Array[int]
var satisfacao_por_rede: Dictionary = {}
var origem_por_rede: Dictionary = {}        ## rede → BASE ou GERADORES; sem energia passando, a rede não aparece aqui
var _ultima_origem: Dictionary = {}         ## rede → última origem (segura a histerese quando a energia para e volta)
var _fluxo: Dictionary = {}                 ## id → true: passa energia por aqui (ver atualizar_fluxo)
var _tempo_fluxo := INF
var estat: Dictionary = {}                  ## rede → {gera_max, gera, consumo, demanda, carga (+ carregando / − descarregando), acum, acum_cap} em kW / MJ


func adicionar(id: int, kw: float, combustivel_mj := 0.0, livre := false) -> Dictionary:
	var n := {"kw": kw, "combustivel_mj": combustivel_mj, "rede": -1, "livre": livre, "base": false, "acum_cap": 0.0, "acum_mj": 0.0, "acum_kw": 0.0}
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
	var por_no := {}                        # a numeração das redes pode mudar: a histerese fica presa aos nós
	if not _ultima_origem.is_empty():
		for id in nos:
			if _ultima_origem.has(nos[id].rede):
				por_no[id] = _ultima_origem[nos[id].rede]
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
	_ultima_origem.clear()
	for id in por_no:
		_ultima_origem[nos[id].rede] = por_no[id]


## Rede refeita do zero (obra no mapa): herda a origem de quem já existia, para a cor não piscar a cada peça posta.
func herdar_origem(antiga: RedeEnergia) -> void:
	for id in nos:
		var o := antiga.ultima_origem_de(id)
		if o != "":
			_ultima_origem[nos[id].rede] = o


func ultima_origem_de(id: int) -> String:
	return str(_ultima_origem.get(nos[id].rede, "")) if nos.has(id) else ""


## "" (sem energia passando), BASE ou GERADORES.
func origem_de(id: int) -> String:
	return str(origem_por_rede.get(nos[id].rede, "")) if nos.has(id) else ""


## Regra de Sapyst: a maior potência entregue domina, sem mistura. `ultima` segura a cor até o outro passar a margem.
static func decidir_origem(base_kw: float, geradores_kw: float, ultima := "") -> String:
	if base_kw + geradores_kw <= 1e-6:
		return ""
	if ultima == BASE:
		return GERADORES if geradores_kw > base_kw * (1.0 + HISTERESE) else BASE
	if ultima == GERADORES:
		return BASE if base_kw > geradores_kw * (1.0 + HISTERESE) else GERADORES
	return GERADORES if geradores_kw > base_kw else BASE


## Passa energia por aqui? Falso em ramal morto: poste na ponta sem nada, máquina desligada, gerador sem combustível.
func fluxo_em(id: int) -> bool:
	return _fluxo.has(id)


## Tira as pontas que não puxam nem dão energia até sobrar só o caminho de verdade (um pedaço com energia entregue).
func atualizar_fluxo() -> void:
	_fluxo.clear()
	_tempo_fluxo = 0.0
	var viz := {}
	var fila: Array[int] = []
	for id in nos:
		if float(estat.get(nos[id].rede, {}).get("gera", 0.0)) <= 0.0:
			continue
		var v := {}
		for o in _arestas[id]:
			v[o] = true
		viz[id] = v
	for id in viz:
		if viz[id].size() <= 1 and not _no_ativo(id):
			fila.append(id)
	while not fila.is_empty():
		var x: int = fila.pop_back()
		if not viz.has(x):
			continue
		var vs: Dictionary = viz[x]
		viz.erase(x)
		for o in vs:
			if viz.has(o):
				viz[o].erase(x)
				if viz[o].size() <= 1 and not _no_ativo(o):
					fila.append(o)
	for id in viz:
		_fluxo[id] = true


func _no_ativo(id: int) -> bool:
	var m: Dictionary = nos[id]
	if m.kw > 0.0:
		return true
	if m.kw < 0.0 and (m.livre or m.combustivel_mj > 0.0):
		return true
	return m.acum_cap > 0.0 and absf(float(estat.get(m.rede, {}).get("carga", 0.0))) > 0.0


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
		if nos[x].rede == r and (nos[x].kw < 0.0 or nos[x].acum_cap > 0.0):
			return true
	return false


## Números da rede onde está `id` (vazio se não está em rede nenhuma).
func estat_de(id: int) -> Dictionary:
	return estat.get(nos[id].rede, {}) if nos.has(id) else {}


## dt em s. Por rede: fontes livres primeiro, depois combustível (proporcional ao que cada gerador aguenta);
## sobra carrega acumuladores, falta descarrega. Atualiza a satisfação e gasta combustível na medida do uso.
func tick(dt: float) -> void:
	if dt <= 0.0:
		return
	var redes := {}
	for id in nos:
		var m: Dictionary = nos[id]
		if not redes.has(m.rede):
			redes[m.rede] = {"livre": 0.0, "livre_base": 0.0, "comb": 0.0, "demanda": 0.0, "acum": [], "geradores": []}
		var r: Dictionary = redes[m.rede]
		if m.kw < 0.0:
			if m.livre:
				r.livre += -m.kw
				if m.base:
					r.livre_base += -m.kw
			else:
				var pode := minf(-m.kw, m.combustivel_mj * 1000.0 / dt)    # kW que o estoque aguenta neste passo
				r.comb += pode
				r.geradores.append([m, pode])
		elif m.kw > 0.0:
			r.demanda += m.kw
		if m.acum_cap > 0.0:
			r.acum.append(m)
	satisfacao_por_rede.clear()
	origem_por_rede.clear()
	estat.clear()
	for k in redes:
		var r: Dictionary = redes[k]
		var g: float = r.livre + r.comb
		var d: float = r.demanda
		var carga := 0.0                      # kW: + entra nos acumuladores, − sai deles
		var usado := 0.0                      # kW tirado das fontes
		if g >= d:
			var cabe := 0.0
			for a in r.acum:
				cabe += minf(a.acum_kw, (a.acum_cap - a.acum_mj) * 1000.0 / dt)
			carga = minf(g - d, cabe)
			usado = d + carga
			if d > 0.0:
				satisfacao_por_rede[k] = 1.0
		else:
			var tem := 0.0
			for a in r.acum:
				tem += minf(a.acum_kw, a.acum_mj * 1000.0 / dt)
			var sai := minf(d - g, tem)
			carga = -sai
			usado = g
			satisfacao_por_rede[k] = clampf((g + sai) / d, 0.0, 1.0)
		# acumuladores repartem a carga/descarga pela capacidade de cada um
		if carga != 0.0:
			var total := 0.0
			for a in r.acum:
				total += minf(a.acum_kw, ((a.acum_cap - a.acum_mj) if carga > 0.0 else a.acum_mj) * 1000.0 / dt)
			for a in r.acum:
				var parte := minf(a.acum_kw, ((a.acum_cap - a.acum_mj) if carga > 0.0 else a.acum_mj) * 1000.0 / dt)
				if total > 0.0:
					a.acum_mj = clampf(a.acum_mj + carga * parte / total * dt / 1000.0, 0.0, a.acum_cap)
		# combustível só cobre o que as fontes livres não deram
		var do_comb := maxf(0.0, usado - r.livre)
		if r.comb > 0.0:
			for gp in r.geradores:
				var gm: Dictionary = gp[0]
				gm.combustivel_mj = maxf(0.0, gm.combustivel_mj - do_comb * (gp[1] / r.comb) * dt / 1000.0)
		# de quem veio: as fontes livres entregam na proporção de cada uma; combustível e descarga são de geradores
		var de_livre := minf(usado, r.livre)
		var de_base: float = de_livre * r.livre_base / r.livre if r.livre > 0.0 else 0.0
		var origem := decidir_origem(de_base, usado - de_base - minf(carga, 0.0), str(_ultima_origem.get(k, "")))
		if origem != "":
			origem_por_rede[k] = origem
			_ultima_origem[k] = origem
		var acum := 0.0
		var cap := 0.0
		for a in r.acum:
			acum += a.acum_mj
			cap += a.acum_cap
		estat[k] = {"gera_max": g, "gera": usado, "demanda": d, "consumo": d * float(satisfacao_por_rede.get(k, 0.0)),
				"carga": carga, "acum": acum, "acum_cap": cap}
	_tempo_fluxo += dt
	if _tempo_fluxo >= 1.0:
		atualizar_fluxo()
