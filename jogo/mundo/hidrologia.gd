class_name Hidrologia
extends RefCounted
## Água da geração, com lógica de relevo (calculada uma vez, determinística, sem simulação em jogo):
##  - nascentes nas partes altas e úmidas; de cada uma o rio desce pelo caminho mais íngreme do relevo (grade grossa
##    de células de 8 tiles) até o mar ou até uma depressão;
##  - na depressão o rio vira lago: enche o fundo (tiles no nível mais baixo, ligados) e NÃO transborda;
##  - depressões úmidas sem rio enchem de chuva (lagoa), também sem transbordar;
##  - o rio nunca sobe: o nível do leito é o menor nível visto desde a nascente (cava um vale nas subidas); onde o
##    leito desce um nível, cachoeira;
##  - a área do início fica seca.
## Mundo infinito: tudo por região de 256 tiles, olhando as nascentes das regiões vizinhas (um rio tem no máximo
## MAX_PASSOS células). Caches com trava: chunks são gerados em threads.

const REGIAO := 256
const CEL := 8
const MAX_PASSOS := 60
const RAIO_SECO := 44.0            ## em volta do início não corre água
const CHANCE_NASCENTE := 0.06
const VIZ8: Array[Vector2i] = [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1),
		Vector2i(1, 1), Vector2i(-1, 1), Vector2i(1, -1), Vector2i(-1, -1)]

var g: GeradorMundo
var _altura := {}                  ## célula → altura grossa
var _rios := {}                    ## célula da nascente → {celulas, pontos, niveis, fim, lago}
var _regioes := {}                 ## região → {tile → {tipo, nivel, fluxo}}
var _fontes := {}                  ## região → Array[Vector2i] das células com nascente
var _bruto := {}                   ## tile → nível do relevo (sem água), já consultado
var _trava := Mutex.new()


func _init(p_g: GeradorMundo) -> void:
	g = p_g


## Água neste tile: {tipo: Terreno.RIO | LAGO | LAGOA, nivel, fluxo: Vector2} ou {}.
func agua_em(t: Vector2i) -> Dictionary:
	var r := Vector2i(floori(t.x / float(REGIAO)), floori(t.y / float(REGIAO)))
	_trava.lock()
	var reg: Variant = _regioes.get(r)
	_trava.unlock()
	if reg == null:
		reg = _montar_regiao(r)
		_trava.lock()
		if _regioes.size() > 64:
			_regioes.clear()
		_regioes[r] = reg
		_trava.unlock()
	return reg.get(t, {})


# ------------------------------------------------------------------ relevo grosso
func _centro(c: Vector2i) -> Vector2:
	return Vector2(c * CEL) + Vector2(CEL, CEL) * 0.5


## Altura da célula: o relevo contínuo + um empurrão da elevação continental (perto do início o relevo é plano;
## a elevação garante que a água ainda ache o caminho do mar).
func altura(c: Vector2i) -> float:
	return _celula(c).x


## (altura grossa, elevação continental) da célula, guardadas juntas (dois ruídos por célula, uma vez só).
func _celula(c: Vector2i) -> Vector2:
	_trava.lock()
	var h: Variant = _altura.get(c)
	_trava.unlock()
	if h != null:
		return h
	var p := _centro(c)
	var ce := g.campos_em(p)
	var v := Vector2(ce.x + ce.y * 1.5, ce.y)
	if p.length() < RAIO_SECO + CEL:
		v.x += 50.0                                   # o início é "alto" para a água: ela contorna
	_trava.lock()
	if _altura.size() > 400000:
		_altura.clear()
	_altura[c] = v
	_trava.unlock()
	return v


## Nível do relevo do tile, guardado (rios e lagos consultam muito os mesmos tiles).
func bruto(t: Vector2i) -> int:
	_trava.lock()
	var n: Variant = _bruto.get(t)
	_trava.unlock()
	if n != null:
		return n
	var v := g.nivel_bruto(t)
	_trava.lock()
	if _bruto.size() > 300000:
		_bruto.clear()
	_bruto[t] = v
	_trava.unlock()
	return v


func _mar(c: Vector2i) -> bool:
	return _celula(c).y < -0.18


func _nascente(c: Vector2i) -> bool:
	var p := _centro(c)
	if p.length() < RAIO_SECO * 2.5 or Distribuicao.h(c.x, c.y, 301) > CHANCE_NASCENTE:
		return false
	if _mar(c) or _celula(c).x - _celula(c).y * 1.5 < 0.6:
		return false                                  # nasce no alto (relevo da célula)
	return g.clima(Vector2i(p)).y > 0.42                # e onde é úmido (deserto quase não tem)


# ------------------------------------------------------------------ rios
func _rio(c: Vector2i) -> Dictionary:
	_trava.lock()
	var r: Variant = _rios.get(c)
	_trava.unlock()
	if r != null:
		return r
	var cels: Array[Vector2i] = [c]
	var vistos := {c: true}
	var fim := "seco"
	var atual := c
	for passo in MAX_PASSOS:
		var melhor := atual
		var hm := altura(atual)
		for d in VIZ8:
			var v: Vector2i = atual + d
			if vistos.has(v):
				continue
			var hv := altura(v)
			if hv < hm - 1e-4:
				hm = hv
				melhor = v
		if melhor == atual:
			fim = "lago"                               # depressão: o rio para e enche o fundo
			break
		cels.append(melhor)
		vistos[melhor] = true
		atual = melhor
		if _mar(melhor):
			fim = "mar"
			break
	# linha do rio: centro de cada célula com um desvio próprio (curvas naturais), amostrada a cada meio tile
	var pontos: Array[Vector2] = []
	var niveis: Array[int] = []
	var nivel := 99
	var ultimo := Vector2i(1 << 30, 0)
	for i in cels.size() - 1:
		# curva suave (Catmull-Rom) passando pelos pontos das células: sem quina a cada célula
		var p0 := _ponto(cels[maxi(i - 1, 0)])
		var a := _ponto(cels[i])
		var b := _ponto(cels[i + 1])
		var p3 := _ponto(cels[mini(i + 2, cels.size() - 1)])
		var n := maxi(2, int(a.distance_to(b) * 1.2))
		for k in n:
			var p := a.cubic_interpolate(b, p0, p3, float(k) / n)
			pontos.append(p)
			var tp := Vector2i(p.floor())
			if tp != ultimo:
				ultimo = tp
				nivel = mini(nivel, bruto(tp))
			niveis.append(nivel)
	var out := {"celulas": cels, "pontos": pontos, "niveis": niveis, "fim": fim}
	if fim == "lago":
		out["lago"] = _encher(Vector2i(_ponto(atual).floor()), 14, 900)
	elif fim == "seco":
		out["lago"] = _encher(Vector2i(_ponto(atual).floor()), 7, 300)    # rio longo: acaba numa poça, nunca no seco
	_trava.lock()
	_rios[c] = out
	_trava.unlock()
	return out


func _ponto(c: Vector2i) -> Vector2:
	return _centro(c) + Vector2(Distribuicao.h(c.x, c.y, 311) - 0.5, Distribuicao.h(c.x, c.y, 312) - 0.5) * (CEL * 0.6)


## Enche o fundo de uma depressão a partir de um tile: só os tiles ligados no nível mais baixo — a água fica no
## fundo e não sobe a borda (não transborda). Onde o fundo é largo, o lago para num contorno irregular (raio
## variando com ruído), nunca na forma da busca.
func _encher(ini: Vector2i, raio: int, maximo: int) -> Dictionary:
	var base := bruto(ini)
	var fila: Array[Vector2i] = [ini]
	var dentro := {ini: true}
	var fora := {}                                    # já recusado: não reavalia
	var fase := Vector2(Distribuicao.h(ini.x, ini.y, 331), Distribuicao.h(ini.x, ini.y, 332)) * 500.0
	while not fila.is_empty() and dentro.size() < maximo:
		var t: Vector2i = fila.pop_front()
		for d in VIZ8:
			var v: Vector2i = t + d
			if dentro.has(v) or fora.has(v) or Vector2(v).length() < RAIO_SECO:
				continue
			var q := Vector2(v) * 0.09 + fase
			var lim := raio * (0.62 + 0.45 * (g._distorcao.get_noise_2d(q.x * 11.0, q.y * 11.0) * 0.5 + 0.5))
			if Vector2(v - ini).length() > lim or bruto(v) > base or g.elevacao(v) < -0.14:
				fora[v] = true
				continue
			dentro[v] = true
			fila.append(v)
	return {"tiles": dentro.keys(), "nivel": base}


# ------------------------------------------------------------------ região
func _montar_regiao(r: Vector2i) -> Dictionary:
	var out := {}
	var ini := r * REGIAO
	var fim := ini + Vector2i(REGIAO, REGIAO)
	var cel_regiao := REGIAO / CEL
	# rios: nascentes desta região e das vizinhas (um rio anda no máximo MAX_PASSOS células)
	var alcance := int(ceil(float(MAX_PASSOS) / cel_regiao))
	for ry in range(r.y - alcance, r.y + alcance + 1):
		for rx in range(r.x - alcance, r.x + alcance + 1):
			for c in _nascentes_da(Vector2i(rx, ry)):
				_riscar(out, _rio(c), ini, fim)
	# lagoas de chuva: células mais baixas que as 8 vizinhas, onde é úmido
	for cy in range(ini.y / CEL - 2, fim.y / CEL + 2):
		for cx in range(ini.x / CEL - 2, fim.x / CEL + 2):
			var c := Vector2i(cx, cy)
			if Distribuicao.h(c.x, c.y, 321) > 0.55 or _mar(c):
				continue
			var h := altura(c)
			var fundo := true
			for d in VIZ8:
				if altura(c + d) <= h:
					fundo = false
					break
			if not fundo or g.clima(Vector2i(_centro(c))).y < 0.5:
				continue
			var lg := _encher(Vector2i(_ponto(c).floor()), 8, 400)
			for t in lg.tiles:
				if t.x >= ini.x and t.y >= ini.y and t.x < fim.x and t.y < fim.y and not out.has(t):
					out[t] = {"tipo": GeradorMundo.Terreno.LAGOA, "nivel": lg.nivel, "fluxo": Vector2.ZERO}
	return out


## Nascentes de uma região (guardadas: as regiões vizinhas consultam as mesmas).
func _nascentes_da(r: Vector2i) -> Array:
	_trava.lock()
	var f: Variant = _fontes.get(r)
	_trava.unlock()
	if f != null:
		return f
	var lista: Array = []
	var cel_regiao := REGIAO / CEL
	for cy in range(r.y * cel_regiao, (r.y + 1) * cel_regiao):
		for cx in range(r.x * cel_regiao, (r.x + 1) * cel_regiao):
			if _nascente(Vector2i(cx, cy)):
				lista.append(Vector2i(cx, cy))
	_trava.lock()
	_fontes[r] = lista
	_trava.unlock()
	return lista


## Pinta o rio (e o lago do fim) nos tiles desta região. Largura cresce rio abaixo.
func _riscar(out: Dictionary, rio: Dictionary, ini: Vector2i, fim: Vector2i) -> void:
	var pts: Array = rio.pontos
	for i in pts.size():
		var p: Vector2 = pts[i]
		if p.x < ini.x - 4 or p.y < ini.y - 4 or p.x > fim.x + 4 or p.y > fim.y + 4:
			continue
		var meia := 1.0 + minf(1.6, i * 0.012)
		var dir: Vector2 = ((pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]) as Vector2).normalized()
		var nv: int = rio.niveis[i]
		var rr := int(ceil(meia))
		for y in range(floori(p.y) - rr, floori(p.y) + rr + 1):
			for x in range(floori(p.x) - rr, floori(p.x) + rr + 1):
				var t := Vector2i(x, y)
				if t.x < ini.x or t.y < ini.y or t.x >= fim.x or t.y >= fim.y:
					continue
				if (Vector2(t) + Vector2(0.5, 0.5)).distance_to(p) > meia or Vector2(t).length() < RAIO_SECO:
					continue
				var ja: Dictionary = out.get(t, {})
				if ja.is_empty() or int(ja.nivel) > nv:
					out[t] = {"tipo": GeradorMundo.Terreno.RIO, "nivel": nv, "fluxo": dir}
	if rio.has("lago"):
		var lg: Dictionary = rio.lago
		for t in lg.tiles:
			if t.x >= ini.x and t.y >= ini.y and t.x < fim.x and t.y < fim.y and not out.has(t):
				out[t] = {"tipo": GeradorMundo.Terreno.LAGO, "nivel": lg.nivel, "fluxo": Vector2.ZERO}
