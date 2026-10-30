class_name VentoLocal
extends RefCounted
## Fator do vento em cada tile (multiplica a força do clima): o lugar importa para a turbina.
##  - alto: cada nível acima da média do entorno (raio 6) sopra mais; baixada abrigada sopra menos;
##  - campo aberto (campina, deserto, planalto, campo de cristal), praia e beira-mar: mais;
##  - floresta e pântano, e árvores plantadas em volta: menos;
##  - a sotavento de construção alta e larga (até 3 tiles vento acima): menos.
## Números em dados/ambiente.json "vento_local". A parte do terreno é guardada por tile (não muda).

var gerador: GeradorMundo
var mapa: MapaOcupacao
var ambiente: AmbienteVivo
var _terreno: Dictionary = {}
var _d: Dictionary


func _init(p_gerador: GeradorMundo, p_mapa: MapaOcupacao = null, p_ambiente: AmbienteVivo = null) -> void:
	gerador = p_gerador
	mapa = p_mapa
	ambiente = p_ambiente
	_d = Registro.ambiente.get("vento_local", {})


## Fator total no tile com o vento soprando para `dir` (0,4..1,6).
## `niveis_extra`: peça alta (turbina alta: "altura_vento" em estruturas.json) conta como se o chão fosse mais alto,
## até o mesmo limite do alto de morro.
func fator(t: Vector2i, dir := Vector2.ZERO, niveis_extra := 0.0) -> float:
	var f := 1.0 + terreno(t) + _abrigo_plantas(t) + sotavento(t, dir)
	if niveis_extra != 0.0:
		var dif := _desnivel(t)
		f += _efeito_nivel(dif + niveis_extra) - _efeito_nivel(dif)
	return clampf(f, float(_d.get("minimo", 0.4)), float(_d.get("maximo", 1.6)))


func terreno(t: Vector2i) -> float:
	if _terreno.has(t):
		return _terreno[t]
	var f := _efeito_nivel(_desnivel(t))
	var b := gerador.bioma(t)
	if b in _d.get("abertos", []) or gerador.terreno(t) == GeradorMundo.Terreno.PRAIA or _perto_do_mar(t):
		f += float(_d.get("aberto", 0.15))
	elif b in _d.get("fechados", []):
		f -= float(_d.get("floresta", 0.3))
	_terreno[t] = f
	return f


## Quantos níveis o tile está acima (+) ou abaixo (−) da média do entorno (raio 6).
func _desnivel(t: Vector2i) -> float:
	var soma := 0.0
	for k in 8:
		var p := Vector2i((Vector2(t) + Vector2.from_angle(k * TAU / 8.0) * 6.0).round())
		soma += gerador.nivel(p)
	return float(gerador.nivel(t)) - soma / 8.0


func _efeito_nivel(dif: float) -> float:
	return clampf(dif * float(_d.get("por_nivel", 0.12)), -float(_d.get("baixada_max", 0.24)), float(_d.get("alto_max", 0.36)))


func _perto_do_mar(t: Vector2i) -> bool:
	for r in [4.0, 8.0]:
		for k in 8:
			var p := Vector2i((Vector2(t) + Vector2.from_angle(k * TAU / 8.0) * r).round())
			var ter := gerador.terreno(p)
			if ter == GeradorMundo.Terreno.MAR or ter == GeradorMundo.Terreno.OCEANO:
				return true
	return false


## Árvores plantadas (crescidas) até 3 tiles: cada uma abriga um pouco, até o mesmo limite da floresta.
func _abrigo_plantas(t: Vector2i) -> float:
	if ambiente == null:
		return 0.0
	var n := 0
	for y in range(-3, 4):
		for x in range(-3, 4):
			if float(ambiente.plantas.get(t + Vector2i(x, y), 0.0)) > 0.5:
				n += 1
	return -minf(n * float(_d.get("por_arvore", 0.06)), float(_d.get("floresta", 0.3)))


## Construção alta e larga até 3 tiles vento acima (não a do próprio tile): sombra de vento.
func sotavento(t: Vector2i, dir: Vector2) -> float:
	if mapa == null or dir.length() < 1e-4:
		return 0.0
	var proprio: int = mapa.tiles.get(t, -1)
	var d := dir.normalized()
	for k in range(1, 4):
		var id: int = mapa.tiles.get(Vector2i((Vector2(t) + Vector2(0.5, 0.5) - d * k).floor()), -1)
		if id < 0 or id == proprio:
			continue
		var dims: Array = Registro.modelos.get(mapa.estruturas[id].nome, {}).get("dims", [1, 1, 0])
		if float(dims[2]) >= float(_d.get("altura_abrigo", 1.5)) and minf(float(dims[0]), float(dims[1])) >= 1.5:
			return -float(_d.get("sotavento", 0.2))
	return 0.0
