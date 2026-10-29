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
var pocas := 0.0          ## 0..1: quanto as baixadas já encheram (enche devagar com chuva forte, seca mais devagar ainda)
var deslocamento := Vector2.ZERO
var direcao_vento := Vector2(1, 0.35).normalized()
var restante := 120.0
var tempo_real := false             ## jogo: estação pelo relógio de verdade (7 dias reais cada); testes usam o tempo simulado
var estacao := 0                    ## índice em clima.json "estacoes"
var t_estacao := 0.0
var ciclo := true                    ## false = relógio parado (fotos)
var hora := 0.3                     ## 0..1 do dia (0 = meia-noite, 0,5 = meio-dia); ciclo de clima.json "dia_s"
var poluicao_total := 0.0            ## vem do mundo: ar sujo deixa tufão mais provável
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
		pocas = 0.85 if valores.chuva > 0.25 else 0.0


func nome_estacao() -> String:
	var es: Array = _d.get("estacoes", [])
	return es[estacao].nome if not es.is_empty() else ""


## 0..1: quão seco está (estação, menos o chão molhado): incêndio pega e espalha mais.
func secura() -> float:
	var es: Array = _d.get("estacoes", [])
	var s: float = es[estacao].secura if not es.is_empty() else 0.4
	return clampf(s * (1.0 - molhado) * (1.0 - valores.chuva), 0.0, 1.0)


func eh_tufao() -> bool:
	return bool(_d.estados[atual].get("tufao", false)) and ativo


## Altura do sol: −1 meia-noite … +1,2 meio-dia (o dia é um pouco mais longo que a noite); o verão alonga o dia,
## o inverno encurta (estação "dia_extra", passando suave da anterior no primeiro quarto da estação).
func altura_sol() -> float:
	return -cos(hora * TAU) + 0.2 + dia_extra()


func dia_extra() -> float:
	var es: Array = _d.get("estacoes", [])
	if es.is_empty():
		return 0.0
	var antes := float(es[(estacao + es.size() - 1) % es.size()].get("dia_extra", 0.0))
	var agora := float(es[estacao].get("dia_extra", 0.0))
	return lerpf(antes, agora, smoothstep(0.0, 0.25, t_estacao / float(_d.get("estacao_s", 604800))))


## 0 = noite, 1 = dia claro; amanhecer e entardecer no meio. Rende o painel solar e acende o mundo.
func luz_dia() -> float:
	return smoothstep(-0.15, 0.35, altura_sol())


## "06:40" no relógio do planeta.
func relogio() -> String:
	var m := int(hora * 1440.0)
	return "%02d:%02d" % [m / 60, m % 60]


func periodo() -> String:
	var a := altura_sol()
	if a > 0.35:
		return "Dia"
	if a < -0.15:
		return "Noite"
	return "Amanhecer" if hora < 0.5 else "Entardecer"


func tick(dt: float) -> void:
	if ciclo:
		hora = fposmod(hora + dt / float(_d.get("dia_s", 720)), 1.0)
	var dur_e: float = _d.get("estacao_s", 604800)
	if tempo_real and not _d.get("estacoes", []).is_empty():
		var agora := Time.get_unix_time_from_system()
		estacao = int(floor(agora / dur_e)) % _d.estacoes.size()
		t_estacao = fmod(agora, dur_e)
	else:
		t_estacao += dt
	if t_estacao >= dur_e and not _d.get("estacoes", []).is_empty():
		t_estacao -= dur_e
		estacao = (estacao + 1) % _d.estacoes.size()
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
	# poças: só chuva de verdade enche; secam do raso para o fundo (o mais fundo some por último)
	if valores.chuva > 0.25:
		pocas = minf(1.0, pocas + dt * 0.012 * valores.chuva)
	else:
		pocas = maxf(0.0, pocas - dt * 0.0035)
	direcao_vento = direcao_vento.rotated(_rng.randf_range(-0.02, 0.02) * dt).normalized()
	deslocamento += direcao_vento * (1.5 + 6.0 * valores.vento) * dt
	if _d.estados[atual].get("raios", false) and ativo and _rng.randf() < dt * 0.07:
		if eventos.size() < 4:
			eventos.append("raio")


## Próximo estado: pesos do estado × pesos da estação; tufão cresce com a poluição do ar (causa e efeito).
func _sortear(pesos: Dictionary) -> String:
	var es: Array = _d.get("estacoes", [])
	var mult: Dictionary = es[estacao].pesos if not es.is_empty() else {}
	var p := {}
	var total := 0.0
	for k in pesos:
		var w := float(pesos[k]) * float(mult.get(k, 1.0))
		if k == "tufao":
			w *= 1.0 + poluicao_total * float(_d.get("tufao_poluicao", 0.0))
		p[k] = w
		total += w
	var r := _rng.randf() * total
	for k in p:
		r -= float(p[k])
		if r <= 0.0:
			return k
	return pesos.keys()[0]


func estado() -> Dictionary:
	return {"atual": atual, "valores": valores, "molhado": molhado, "pocas": pocas, "deslocamento": deslocamento, "restante": restante,
			"vento": direcao_vento, "rng": _rng.state, "estacao": estacao, "t_estacao": t_estacao, "hora": hora}


func restaurar(d: Dictionary) -> void:
	atual = d.atual
	valores = d.valores
	molhado = d.molhado
	pocas = d.get("pocas", 0.0)
	deslocamento = d.deslocamento
	restante = d.restante
	direcao_vento = d.vento
	_rng.state = d.rng
	estacao = d.get("estacao", 0)
	t_estacao = d.get("t_estacao", 0.0)
	hora = d.get("hora", 0.3)
