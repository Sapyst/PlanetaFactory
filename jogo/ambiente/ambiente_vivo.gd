class_name AmbienteVivo
extends RefCounted
## Ambiente vivo (lógica pura, passo de 1 s): o que a fábrica faz com o planeta sem o jogador querer.
##  - sujeira: máquinas que poluem sujam o chão em volta; a chuva lava devagar; o resto some muito devagar
##    (o ambiente tende a sujar com o tempo);
##  - óleo: vazamentos ao acaso de máquinas trabalhando (manchas que demoram a sumir);
##  - água suja: despejo de máquinas perto de água; corre rio abaixo (fluxo da hidrologia) e se espalha no lago;
##  - fogo: máquinas quentes podem acender a vegetação seca em volta (estação + chão seco); o fogo anda com o vento,
##    queima o tile (vira chão queimado), machuca construção encostada e apaga com chuva;
##  - tufão: vento extremo — espalha fogo e sujeira e danifica estruturas frágeis.
## Os valores são por tile (dado de simulação); o desenho é contínuo (mistura suave + ruído, nunca em quadrados).
## Só existem chunks com algum valor: o custo segue a sujeira, não o tamanho do mapa.

const CANAIS := 4            ## sujeira, óleo, água suja, queimado
const SUJ := 0
const OLEO := 1
const AGUA := 2
const QUEIM := 3
const T := Grade.TAM_CHUNK

var gerador: GeradorMundo
var mapa: MapaOcupacao
var dados: Dictionary = {}           ## chunk → PackedFloat32Array(32·32·4)
var fogo: Dictionary = {}            ## tile → segundos restantes queimando
var sujos: Dictionary = {}           ## chunks mudados desde o último desenho
var eventos: Array[Dictionary] = []  ## {tipo: "fogo_inicio"|"dano", ...}
var dano: Callable                   ## func(id, pontos): o mundo aplica (pode destruir)
var _rng := RandomNumberGenerator.new()
var _acum := 0.0
var _d: Dictionary
var _agua_perto := {}                ## id da máquina → tile de água mais perto (ou nulo)


func _init(p_gerador: GeradorMundo, p_mapa: MapaOcupacao, semente := 9) -> void:
	gerador = p_gerador
	mapa = p_mapa
	_rng.seed = semente
	_d = Registro.ambiente


# ------------------------------------------------------------------ leitura/escrita por tile
func valor(t: Vector2i, canal: int) -> float:
	var a: Variant = dados.get(Grade.chunk_de(t))
	if a == null:
		return 0.0
	var l := Grade.local_de(t)
	return (a as PackedFloat32Array)[(l.y * T + l.x) * CANAIS + canal]


func somar(t: Vector2i, canal: int, v: float) -> void:
	var k := Grade.chunk_de(t)
	var a: PackedFloat32Array = dados.get(k, PackedFloat32Array())
	if a.is_empty():
		if v <= 0.0:
			return
		a.resize(T * T * CANAIS)
	var l := Grade.local_de(t)
	var i := (l.y * T + l.x) * CANAIS + canal
	a[i] = clampf(a[i] + v, 0.0, 1.0)
	dados[k] = a
	sujos[k] = true


func _mancha(c: Vector2, raio: float, canal: int, v: float) -> void:
	var r := int(ceil(raio))
	for y in range(floori(c.y) - r, floori(c.y) + r + 1):
		for x in range(floori(c.x) - r, floori(c.x) + r + 1):
			var d := (Vector2(x, y) + Vector2(0.5, 0.5)).distance_to(c)
			if d < raio:
				somar(Vector2i(x, y), canal, v * (1.0 - d / raio))


# ------------------------------------------------------------------ passo
func tick(dt: float, fabrica: Fabrica, clima: Clima) -> void:
	_acum += dt
	while _acum >= 1.0:
		_acum -= 1.0
		_passo(fabrica, clima)


func _passo(fabrica: Fabrica, clima: Clima) -> void:
	var chuva: float = clima.valores.chuva if clima != null else 0.0
	var vento: Vector2 = clima.direcao_vento * (0.4 + clima.valores.vento) if clima != null else Vector2.ZERO
	var tufao := clima != null and clima.eh_tufao()
	var secura := clima.secura() if clima != null else 0.0
	# fontes: quem trabalhou neste passo
	for id in fabrica.emissao:
		if not mapa.estruturas.has(id):
			continue
		var e: Dictionary = mapa.estruturas[id]
		var c := Grade.centro_da_area(e.minimo, e.area, e.rot)
		var raio: float = float(_d.sujeira_raio) + 0.5 * maxf(e.area.x, e.area.y)
		_mancha(c, raio, SUJ, float(fabrica.emissao[id]) * float(_d.sujeira_por_ponto))
		var ch: float = _d.oleo_chance.get(e.nome, 0.0)
		if ch > 0.0 and _rng.randf() < ch:
			var p: Vector2 = c + Vector2(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1)) * (0.6 + 0.5 * e.area.x)
			_mancha(p, _rng.randf_range(0.9, 1.8), OLEO, 0.8)
		var desp: float = _d.despejo.get(e.nome, 0.0)
		if desp > 0.0:
			var w: Variant = _agua_mais_perto(id, c)
			if w != null:
				somar(w, AGUA, desp)
		# fogo: máquina quente acende vegetação seca em volta
		if e.nome in _d.fogo.maquinas_quentes and secura > 0.3 and _rng.randf() < float(_d.fogo.chance_maquina) * secura:
			var alvo: Vector2i = Vector2i((c + Vector2.from_angle(_rng.randf() * TAU) * (1.2 + 0.5 * e.area.x)).floor())
			if _inflamavel(alvo):
				_acender(alvo)
	_agua()
	_fogo(chuva, vento, secura, tufao)
	if tufao:
		_tufao(vento)
	_decair(chuva)


func _agua_mais_perto(id: int, c: Vector2) -> Variant:
	if _agua_perto.has(id):
		return _agua_perto[id]
	var melhor: Variant = null
	var md := INF
	var r: int = _d.despejo_raio
	for y in range(floori(c.y) - r, floori(c.y) + r + 1):
		for x in range(floori(c.x) - r, floori(c.x) + r + 1):
			var t := Vector2i(x, y)
			if gerador.eh_agua(gerador.terreno(t)):
				var d := Vector2(t).distance_squared_to(c)
				if d < md:
					md = d
					melhor = t
	_agua_perto[id] = melhor
	return melhor


## Água suja: rio leva para o tile rio abaixo; lago espalha para os vizinhos de água.
func _agua() -> void:
	var muda := {}
	for k in dados:
		var a: PackedFloat32Array = dados[k]
		var base: Vector2i = k * T
		for i in T * T:
			var v := a[i * CANAIS + AGUA]
			if v < 0.002:
				continue
			var t := base + Vector2i(i % T, i / T)
			var ter := gerador.terreno(t)
			if ter == GeradorMundo.Terreno.RIO:
				var f := gerador.direcao_rio(t)
				if f != Vector2.ZERO:
					var prox := Vector2i((Vector2(t) + Vector2(0.5, 0.5) + f).floor())
					var q: float = v * float(_d.agua_corre)
					muda[t] = float(muda.get(t, 0.0)) - q
					muda[prox] = float(muda.get(prox, 0.0)) + q
			else:
				var q: float = v * float(_d.agua_espalha)
				for d in Grade.DIRECOES:
					var n: Vector2i = t + d
					if gerador.eh_agua(gerador.terreno(n)):
						muda[t] = float(muda.get(t, 0.0)) - q
						muda[n] = float(muda.get(n, 0.0)) + q
	for t in muda:
		somar(t, AGUA, muda[t])


## Árvore/arbusto/cogumelo no tile queima mais tempo (é combustível); 1 = só grama.
func _madeira(t: Vector2i) -> float:
	if mapa.limpos.has(t):
		return 1.0
	var o := gerador.distribuicao.obstaculo(t)
	if o.is_empty():
		return 1.0
	return float(_d.fogo.get("madeira", {}).get(o.nome, 1.0))


func _inflamavel(t: Vector2i) -> bool:
	if not mapa.limpos.has(t):
		var o := gerador.distribuicao.obstaculo(t)
		if not o.is_empty() and float(_d.fogo.get("madeira", {}).get(o.nome, 1.0)) <= 0.0:
			return false
	if fogo.has(t) or mapa.tiles.has(t) or gerador.terreno(t) != GeradorMundo.Terreno.TERRA:
		return false
	if not gerador.distribuicao.jazida(t).is_empty() or valor(t, QUEIM) > 0.6:
		return false
	return gerador.bioma(t) in _d.fogo.inflamavel


func _acender(t: Vector2i) -> void:
	if fogo.size() >= int(_d.fogo.max_focos):
		return
	var dur: Array = _d.fogo.duracao_s
	fogo[t] = _rng.randf_range(dur[0], dur[1]) * _madeira(t)
	if fogo.size() == 1:
		eventos.append({"tipo": "fogo_inicio", "tile": t})


func _fogo(chuva: float, vento: Vector2, secura: float, tufao: bool) -> void:
	if fogo.is_empty():
		return
	var novos: Array[Vector2i] = []
	var apagar: Array[Vector2i] = []
	var esp: float = float(_d.fogo.espalha) * (0.3 + secura) * (3.0 if tufao else 1.0)
	for t in fogo:
		fogo[t] -= 1.0 + chuva * float(_d.fogo.chuva_apaga) * 10.0
		somar(t, QUEIM, 0.22)
		if fogo[t] <= 0.0:
			apagar.append(t)
			continue
		for d in Grade.DIRECOES:
			var n: Vector2i = t + d
			var a_favor := maxf(0.0, Vector2(d).dot(vento))
			if _rng.randf() < esp * (1.0 + a_favor * float(_d.fogo.vento_mult)) * (1.0 - chuva):
				if _inflamavel(n):
					novos.append(n)
			var id: int = mapa.tiles.get(n, -1)
			if id >= 0 and dano.is_valid():
				dano.call(id, float(_d.fogo.dano_estrutura))
	for t in apagar:
		fogo.erase(t)
		somar(t, QUEIM, 1.0)
		# a vegetação do tile virou cinza: árvore/arbusto some do mapa (o mundo redesenha o chunk)
		if not mapa.limpos.has(t):
			var o := gerador.distribuicao.obstaculo(t)
			if not o.is_empty():
				mapa.limpar_obstaculo(t)
				_mancha(Vector2(t) + Vector2(0.5, 0.5), 1.8, QUEIM, 0.8)
				eventos.append({"tipo": "vegetacao_queimada", "tile": t, "tiles": Grade.tiles_da_area(o.ancora, o.area, 0)})
	for t in novos:
		_acender(t)


## Tufão: estruturas frágeis apanham; a sujeira das áreas sujas é arrastada vento abaixo.
func _tufao(vento: Vector2) -> void:
	var frageis: Array = _d.tufao.frageis
	for id in mapa.estruturas.keys():
		if mapa.estruturas.has(id) and mapa.estruturas[id].nome in frageis and dano.is_valid():
			dano.call(id, float(_d.tufao.dano))
	var leva: float = _d.tufao.espalha_sujeira
	var passo := Vector2i(Vector2(vento.normalized() * 2.0).round())
	for k in dados.keys():
		var a: PackedFloat32Array = dados[k]
		var base: Vector2i = k * T
		for i in T * T:
			var v := a[i * CANAIS + SUJ]
			if v > 0.05:
				var t := base + Vector2i(i % T, i / T)
				somar(t, SUJ, -v * leva)
				somar(t + passo, SUJ, v * leva)


func _decair(chuva: float) -> void:
	var s_suj: float = float(_d.sujeira_some) + float(_d.chuva_lava) * chuva
	var vazios: Array = []
	for k in dados:
		var a: PackedFloat32Array = dados[k]
		var soma := 0.0
		for i in T * T:
			var j := i * CANAIS
			a[j] = maxf(0.0, a[j] - s_suj)
			a[j + 1] = maxf(0.0, a[j + 1] - float(_d.oleo_some))
			a[j + 2] = maxf(0.0, a[j + 2] - float(_d.agua_some))
			a[j + 3] = maxf(0.0, a[j + 3] - float(_d.queimado_some))
			soma += a[j] + a[j + 1] + a[j + 2] + a[j + 3]
		dados[k] = a
		if soma <= 0.0:
			vazios.append(k)
		sujos[k] = true
	for k in vazios:
		dados.erase(k)


## Imagem RGBA8 34×34 do chunk (com 1 tile de margem) para o shader do chão: R sujeira, G óleo, B água, A queimado.
func imagem(k: Vector2i) -> Image:
	var img := Image.create(T + 2, T + 2, false, Image.FORMAT_RGBA8)
	var base: Vector2i = k * T - Vector2i.ONE
	for j in T + 2:
		for i in T + 2:
			var t := base + Vector2i(i, j)
			var a: Variant = dados.get(Grade.chunk_de(t))
			if a == null:
				continue
			var l := Grade.local_de(t)
			var o := (l.y * T + l.x) * CANAIS
			var arr: PackedFloat32Array = a
			# em terra o canal da água suja não é usado: ali vai a brasa (tile queimando agora, 0..1 pelo fogo restante)
			var b := arr[o + 2]
			if fogo.has(t):
				b = clampf(float(fogo[t]) / 4.5, 0.0, 1.0)       # recém-aceso = 1, quase apagando = 0 (faixa estreita: a frente)
			img.set_pixel(i, j, Color(arr[o], arr[o + 1], b, arr[o + 3]))
	return img


func estado() -> Dictionary:
	return {"dados": dados, "fogo": fogo, "rng": _rng.state}


func restaurar(d: Dictionary) -> void:
	dados = d.get("dados", {})
	fogo = d.get("fogo", {})
	_rng.state = d.get("rng", _rng.state)
	for k in dados:
		sujos[k] = true
