class_name AguaJogo
extends RefCounted
## Água em jogo (lógica pura): buraco ou canal escavado abaixo do nível de um rio/lago ENCHE a partir da água
## natural encostada — um anel de tiles por passo, como um autômato (estilo Minecraft, sem volume).
##  - nunca transborda: só enche tile cujo fundo (nível escavado) fica ABAIXO da superfície da água que chega;
##    a superfície é a da fonte (o nível do leito do rio/lago) e não sobe;
##  - construção feita no seco barra a água (dique); construção feita sobre a água (plataforma/ponte) deixa passar;
##  - aterrar (aplainar para cima) ou fechar a ligação com um dique seca o que ficou sem fonte.
## Só olha tiles escavados (Terraplenagem): o relevo natural nunca muda sozinho. O desenho é do próprio chão
## (DesenhoChunk: canal A do mapa da fábrica) — a água de jogo é igual à natural: margem curva, ondas, chuva.

const PASSO_S := 0.3          ## segundos por anel de enchimento

var gerador: GeradorMundo
var mapa: MapaOcupacao
var cheios: Dictionary = {}   ## tile → nível da superfície (enchido)
var versao := 0               ## muda quando algum tile enche ou seca (o desenho refaz)
var mudados: Dictionary = {}  ## tiles que encheram/secaram desde que o desenho olhou (ele limpa)
var _alvo: Dictionary = {}    ## tile → [superfície, distância da fonte] (onde a água vai chegar)
var _onda := 0                ## distância já alcançada pelo enchimento em curso
var _acum := 0.0


func _init(p_gerador: GeradorMundo, p_mapa: MapaOcupacao) -> void:
	gerador = p_gerador
	mapa = p_mapa


## Fundo do tile escavado (nível) ou null se não foi escavado.
func _fundo(t: Vector2i) -> Variant:
	return gerador.aplainado_em(t)


## Construção no seco barra a água; sobre a água (plataforma, ponte) não.
func _barrado(t: Vector2i) -> bool:
	var id: int = mapa.tiles.get(t, -1)
	return id >= 0 and not mapa.estruturas[id].get("sobre_agua", false)


func eh_agua(t: Vector2i) -> bool:
	return cheios.has(t) or gerador.eh_agua(gerador.terreno(t))


## Refaz para onde a água vai (depois de escavar, aterrar, construir ou remover). Seca na hora o que perdeu a
## fonte; o que ganhou fonte enche aos poucos a partir da margem.
func recalcular() -> void:
	var escavados := gerador.aplainados()
	var novo := {}
	var fila: Array[Vector2i] = []
	for t in escavados:
		if _barrado(t):
			continue
		for d in Grade.DIRECOES:
			var w: Vector2i = t + d
			if gerador.eh_agua(gerador.terreno(w)):
				var s: int = gerador.nivel(w)                  # nível do leito da água natural
				if int(escavados[t]) < s and (not novo.has(t) or int(novo[t][0]) < s):
					novo[t] = [s, 1]
					fila.append(t)
	var i := 0
	while i < fila.size():
		var t := fila[i]
		i += 1
		var s: int = novo[t][0]
		var dist: int = novo[t][1]
		for d in Grade.DIRECOES:
			var n: Vector2i = t + d
			if not escavados.has(n) or _barrado(n) or int(escavados[n]) >= s:
				continue
			if novo.has(n) and (int(novo[n][0]) > s or (int(novo[n][0]) == s and int(novo[n][1]) <= dist + 1)):
				continue
			novo[n] = [s, dist + 1]
			fila.append(n)
	_alvo = novo
	# seca o que não tem mais fonte (ou mudou de nível)
	for t in cheios.keys():
		if not _alvo.has(t) or int(_alvo[t][0]) != int(cheios[t]):
			cheios.erase(t)
			gerador.inundar(t, null)
			mudados[t] = true
			versao += 1
	_onda = 0
	for t in cheios:
		_onda = maxi(_onda, int(_alvo[t][1]))


## Enche mais um anel a cada PASSO_S. Devolve true se mudou algo.
func tick(dt: float) -> bool:
	if cheios.size() >= _alvo.size():
		return false
	_acum += dt
	var mudou := false
	while _acum >= PASSO_S:
		_acum -= PASSO_S
		_onda += 1
		for t in _alvo:
			if not cheios.has(t) and int(_alvo[t][1]) <= _onda:
				cheios[t] = int(_alvo[t][0])
				gerador.inundar(t, cheios[t])
				mudados[t] = true
				mudou = true
	if mudou:
		versao += 1
	return mudou


## Enche tudo de uma vez (carregar jogo, testes).
func encher_tudo() -> void:
	for t in _alvo:
		if not cheios.has(t):
			cheios[t] = int(_alvo[t][0])
			gerador.inundar(t, cheios[t])
			mudados[t] = true
	versao += 1


func estado() -> Dictionary:
	return {"cheios": cheios}


func restaurar(d: Dictionary) -> void:
	for t in d.get("cheios", {}):
		cheios[t] = int(d.cheios[t])
		gerador.inundar(t, cheios[t])
		mudados[t] = true
	versao += 1
