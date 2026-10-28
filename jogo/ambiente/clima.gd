class_name Clima
extends RefCounted
## Clima dinâmico (lógica pura): estados de dados/clima.json trocando sozinhos (pesos do "proximo"), com transição
## suave dos valores. `valores` = o que o desenho usa agora (nuvens, neblina, chuva, luz, vento); `molhado` sobe com
## chuva e seca devagar; `deslocamento` = quanto as nuvens já andaram com o vento (sombra no chão).
## Tempestade solta raios (eventos). Desligado (`ativo` = false) fica em céu limpo.

var ativo := true
var atual := "limpo"
var valores: Dictionary = {}
var molhado := 0.0
var deslocamento := Vector2.ZERO
var direcao_vento := Vector2(1, 0.35).normalized()
var restante := 120.0
var eventos: Array[String] = []     ## acumula ("raio"); quem desenha consome e limpa
var _rng := RandomNumberGenerator.new()
var _d: Dictionary


func _init(semente := 1) -> void:
	_rng.seed = semente
	_d = Registro.clima
	valores = _alvo().duplicate()


func nome() -> String:
	return _d.get("nomes", {}).get(atual, atual)


func _alvo() -> Dictionary:
	var e: Dictionary = _d.estados[atual if ativo else "limpo"]
	return {"nuvens": float(e.nuvens), "neblina": float(e.neblina), "chuva": float(e.chuva), "luz": float(e.luz), "vento": float(e.vento)}


## Força um estado (testes, roteiros de foto). `instantaneo` pula a transição.
func forcar(estado: String, instantaneo := false) -> void:
	atual = estado
	var dur: Array = _d.estados[estado].duracao_s
	restante = _rng.randf_range(dur[0], dur[1])
	if instantaneo:
		valores = _alvo().duplicate()
		molhado = 1.0 if valores.chuva > 0.0 else 0.0


func tick(dt: float) -> void:
	restante -= dt
	if restante <= 0.0 and ativo:
		forcar(_sortear(_d.estados[atual].proximo))
	# aproxima os valores do alvo (transição suave)
	var k := clampf(dt / float(_d.get("transicao_s", 25)), 0.0, 1.0)
	var alvo := _alvo()
	for chave in alvo:
		valores[chave] = lerpf(valores[chave], alvo[chave], k * 3.0)
	# chão molha com a chuva e seca devagar
	if valores.chuva > 0.15:
		molhado = minf(1.0, molhado + dt * 0.05 * valores.chuva)
	else:
		molhado = maxf(0.0, molhado - dt * 0.008)
	direcao_vento = direcao_vento.rotated(_rng.randf_range(-0.02, 0.02) * dt).normalized()
	deslocamento += direcao_vento * (1.5 + 6.0 * valores.vento) * dt
	if _d.estados[atual].get("raios", false) and ativo and _rng.randf() < dt * 0.07:
		if eventos.size() < 4:
			eventos.append("raio")


func _sortear(pesos: Dictionary) -> String:
	var total := 0.0
	for k in pesos:
		total += float(pesos[k])
	var r := _rng.randf() * total
	for k in pesos:
		r -= float(pesos[k])
		if r <= 0.0:
			return k
	return pesos.keys()[0]


func estado() -> Dictionary:
	return {"atual": atual, "valores": valores, "molhado": molhado, "deslocamento": deslocamento, "restante": restante,
			"vento": direcao_vento, "rng": _rng.state}


func restaurar(d: Dictionary) -> void:
	atual = d.atual
	valores = d.valores
	molhado = d.molhado
	deslocamento = d.deslocamento
	restante = d.restante
	direcao_vento = d.vento
	_rng.state = d.rng
