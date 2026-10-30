class_name Poluicao
extends RefCounted
## Poluição por chunk (32×32), lógica pura. Máquinas emitem no chunk onde estão; a cada segundo:
##  - o chão absorve (fração do que tem × multiplicador do bioma, mais um mínimo fixo) — floresta limpa mais, deserto menos;
##  - o que passa de `minimo_espalhar` vaza uma fração para os 4 chunks vizinhos (a nuvem se alastra) — com vento,
##    a maior parte vai vento abaixo (`vento_a_favor`, 70%) e o resto se divide pelos 4 lados;
##  - ninhos (Colonia) também absorvem — e é isso que vira aranha;
##  - no raio de um defletor de vento a nuvem vaza para onde ele aponta (`vento_chunks`; regulador: sem vento).
## Só chunks com poluição existem no dicionário: o custo é proporcional à nuvem, não ao mapa.

const PASSO := 1.0

var valores: Dictionary = {}          ## chunk → pontos
var chuva := 0.0                      ## 0..1, vem do clima: chuva lava o ar (chão absorve mais)
var vento := Vector2.ZERO             ## do clima: direção (para onde sopra, grade) × força 0..1
var vento_chunks: Dictionary = {}     ## chunk → vento forçado ali (defletor de vento: ClimaLocal.vento_chunks)
var gerador: GeradorMundo
var _mult: Dictionary = {}            ## chunk → multiplicador de absorção (cache)
var _acum := 0.0
var _d: Dictionary


var fator := 1.0                ## Simbiose: −50% de poluição em todo o planeta (o mundo põe)


func _init(p_gerador: GeradorMundo) -> void:
	gerador = p_gerador
	_d = Registro.inimigos.get("poluicao", {})


func emitir(tile: Vector2i, pontos: float) -> void:
	var k := Grade.chunk_de(tile)
	valores[k] = float(valores.get(k, 0.0)) + pontos * fator


func em_chunk(k: Vector2i) -> float:
	return float(valores.get(k, 0.0))


func em(tile: Vector2i) -> float:
	return em_chunk(Grade.chunk_de(tile))


## Tira até `pontos` do chunk (ninho absorvendo). Devolve quanto tirou.
func absorver(k: Vector2i, pontos: float) -> float:
	var tem := em_chunk(k)
	var tira := minf(tem, pontos)
	if tira > 0.0:
		valores[k] = tem - tira
	return tira


func total() -> float:
	var t := 0.0
	for k in valores:
		t += valores[k]
	return t


func tick(dt: float) -> void:
	_acum += dt
	while _acum >= PASSO:
		_acum -= PASSO
		_passo()


func _passo() -> void:
	var difusao: float = _d.get("difusao", 0.035)
	var minimo: float = _d.get("minimo_espalhar", 0.6)
	var absorcao: float = _d.get("absorcao", 0.004)
	var fixa: float = _d.get("absorcao_fixa", 0.02)
	var lava := 1.0 + float(Registro.clima.get("chuva_absorcao", 0.0)) * chuva
	var pesos := pesos_vento()
	var novo := {}
	for k in valores:
		var v: float = valores[k]
		v -= (v * absorcao + fixa) * _multiplicador(k) * lava * PASSO
		if v <= 0.0:
			continue
		if v > minimo:
			var vaza := v * difusao * PASSO * 4.0
			var pk: Array[float] = pesos if not vento_chunks.has(k) else pesos_vento(vento_chunks[k])
			for i in Grade.DIRECOES.size():
				var d: Vector2i = Grade.DIRECOES[i]
				novo[k + d] = float(novo.get(k + d, 0.0)) + vaza * pk[i]
			v -= vaza
		novo[k] = float(novo.get(k, 0.0)) + v
	valores.clear()
	for k in novo:
		if novo[k] > 0.01:
			valores[k] = novo[k]


## Fração do que vaza que vai para cada vizinho (Grade.DIRECOES): sem vento, 1/4 para cada; com vento forte,
## `vento_a_favor` vai para os lados a favor (pelo ângulo) e o resto se divide igual pelos 4.
func pesos_vento(v: Variant = null) -> Array[float]:
	var w: Vector2 = vento if v == null else v
	var r: Array[float] = []
	var forca := clampf(w.length(), 0.0, 1.0)
	var dir := w.normalized() if forca > 1e-4 else Vector2.ZERO
	var favor := float(_d.get("vento_a_favor", 0.7))
	var soma := 0.0
	for d in Grade.DIRECOES:
		soma += maxf(0.0, Vector2(d).dot(dir))
	for d in Grade.DIRECOES:
		var a := maxf(0.0, Vector2(d).dot(dir)) / soma if soma > 1e-4 else 0.25
		r.append(lerpf(0.25, favor * a + (1.0 - favor) * 0.25, forca))
	return r


## Absorção do chão do chunk: bioma do centro (água conta como água).
func _multiplicador(k: Vector2i) -> float:
	if not _mult.has(k):
		var t := k * Grade.TAM_CHUNK + Vector2i(Grade.TAM_CHUNK / 2, Grade.TAM_CHUNK / 2)
		var tab: Dictionary = _d.get("absorcao_bioma", {})
		var m := 1.0
		if gerador.eh_agua(gerador.terreno(t)):
			m = tab.get("_agua", 0.3)
		else:
			m = tab.get(gerador.bioma(t), 1.0)
		_mult[k] = m
	return _mult[k]
