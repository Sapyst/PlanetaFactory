class_name Trem
extends RefCounted
## Um trem na malha. Lógica pura (testável): a composição anda sobre uma "trilha" — a polilinha do caminho já
## planejado, inclusive o trecho embaixo e atrás do trem — e `s` é a distância da FRENTE ao longo dela.
##  - Rota: A* até a próxima estação da lista (todas as estações da malha, em ordem), sempre para a frente;
##    só inverte (há locomotiva nas duas pontas) quando não existe caminho à frente — vai-e-vem em linha com
##    fim de linha. Assim, numa volta, todos os trens rodam no mesmo sentido e não se encaram.
##  - Sinais: antes de entrar numa peça de outro bloco, reserva o bloco; se outro trem tem, freia antes da divisa.
##    Blocos que ficaram para trás da cauda são liberados.
##  - Trens que se encaram (cada um esperando o bloco do outro) se resolvem: depois de um tempo parado, que
##    depende do id para não virarem juntos, o trem tenta a rota pelo outro lado.
##  - Estação: para com o meio do trem na parada, espera, troca carga (descarrega o que trouxe de outra estação,
##    carrega o que está para enviar) e segue para a próxima.

const CARRO := 3.0            ## m por carro (engate a engate)
const TRUQUE := 0.85          ## truques a ±0,85 m do centro do carro (modelo)
const VEL_MAX := 6.0          ## m/s
const ACEL := 1.5
const FREIO := 2.5
const PARADA_S := 4.0
const CAPACIDADE_VAGAO := 40
const FOLGA_SINAL := 0.3

enum Estado { ANDANDO, PARADO, ESPERANDO_BLOCO, SEM_ROTA }

var id := 0
var carros: Array[String] = []
var grafo: GrafoTrilhos
var pontos := PackedVector2Array()
var acum := PackedFloat64Array()
var segs: Array[Dictionary] = []      ## {peca, s0, s1, i0, i1, de: Vector2, para: Vector2}
var s := 0.0
var v := 0.0
var estado := Estado.SEM_ROTA
var s_alvo := 0.0
var proxima := 0                      ## índice na lista de paradas
var rota: Array[int] = []             ## estações (id da estrutura) escolhidas pelo jogador, em ordem; vazia = todas
var _esperando := 0.0                 ## tempo parado diante de bloco ocupado (destrava trens que se encaram)
var espera := 0.0
var carga: Dictionary = {}            ## item → quantidade
var origem_carga := -1                ## estrutura da estação onde carregou
var chegada := -1                     ## estrutura da estação onde acabou de parar (o mundo lê e zera)
var _tentar := 0.0


func _init(p_id: int, p_grafo: GrafoTrilhos, p_carros: Array[String]) -> void:
	id = p_id
	grafo = p_grafo
	carros = p_carros


func comprimento() -> float:
	return carros.size() * CARRO


func capacidade() -> int:
	return carros.count("vagao_carga") * CAPACIDADE_VAGAO


func total_carga() -> int:
	var n := 0
	for k in carga:
		n += carga[k]
	return n


# ------------------------------------------------------------------ salvamento
const CAMPOS := ["carros", "pontos", "acum", "segs", "s", "v", "s_alvo", "proxima", "espera", "carga", "origem_carga", "rota"]


func para_salvar() -> Dictionary:
	var d := {"id": id, "estado": estado}
	for k in CAMPOS:
		d[k] = get(k)
	return d


## Trem de um salvamento: recoloca a trilha e religa às peças da malha (reancorar), que replaneja e reserva.
static func de_salvo(d: Dictionary, g: GrafoTrilhos) -> Trem:
	var cs: Array[String] = []
	cs.assign(d.carros)
	var t := Trem.new(d.id, g, cs)
	for k in CAMPOS:
		if k == "carros":
			continue
		if k in ["segs", "rota"]:
			t.get(k).assign(d[k])
		else:
			t.set(k, d[k])
	var parado: bool = d.estado == Estado.PARADO
	if not t.reancorar(g):
		return null
	if parado:
		t.estado = Estado.PARADO
		t.espera = d.espera
	return t


# ------------------------------------------------------------------ colocar
## Põe o trem com a cauda na ponta `de` da peça, olhando para dentro dela. Falha se não couber ou se o bloco
## estiver ocupado.
func colocar(peca: int, de: Vector2) -> bool:
	pontos.clear()
	acum.clear()
	segs.clear()
	_anexar(peca, de)
	if not _estender(comprimento() + 0.01):
		return false
	s = comprimento()
	for sg in segs:
		if sg.s0 < s and not grafo.reservar(id, [sg.peca] as Array[int]):
			grafo.liberar(id)
			return false
	estado = Estado.SEM_ROTA
	_tentar = 0.0
	return true


# ------------------------------------------------------------------ tick
func tick(dt: float) -> void:
	match estado:
		Estado.PARADO:
			espera -= dt
			if espera <= 0.0:
				proxima += 1
				planejar()
		Estado.SEM_ROTA:
			_tentar -= dt
			if _tentar <= 0.0:
				_tentar = 2.0
				planejar()
		_:
			_andar(dt)
			if estado == Estado.ESPERANDO_BLOCO:
				_esperando += dt
				if _esperando > 8.0 + 3.0 * (id % 4):
					_esperando = 0.0
					planejar(true)
			else:
				_esperando = 0.0
	_aparar()


## Paradas na ordem: a rota do jogador (só as que existem) ou todas as estações da malha.
func paradas() -> Array[Dictionary]:
	if rota.is_empty():
		return grafo.estacoes
	var out: Array[Dictionary] = []
	for id in rota:
		for e in grafo.estacoes:
			if e.estrutura == id:
				out.append(e)
	return out


func _andar(dt: float) -> void:
	var L := comprimento()
	var olhar := v * v / (2.0 * FREIO) + 2.0
	var limite := s_alvo
	var precisa := {}
	for sg in segs:
		if sg.s1 <= s - L:
			continue
		if sg.s0 > s + olhar:
			break
		if sg.peca < 0:
			limite = minf(limite, sg.s0 - FOLGA_SINAL)
			break
		var b: int = grafo.pecas[sg.peca].bloco
		if precisa.has(b) or grafo.reserva.get(b, -1) == id:
			precisa[b] = true
			continue
		if sg.s0 > s and not grafo.reservar(id, [sg.peca] as Array[int]):
			limite = minf(limite, sg.s0 - FOLGA_SINAL)
			break
		precisa[b] = true
	for b in grafo.reserva.keys():
		if grafo.reserva[b] == id and not precisa.has(b):
			grafo.reserva.erase(b)
	var livre := maxf(limite - s, 0.0)
	var vmax := minf(VEL_MAX, sqrt(2.0 * FREIO * livre))
	v = move_toward(v, vmax, (ACEL if vmax > v else FREIO * 2.0) * dt)
	s = minf(s + v * dt, maxf(limite, s))
	if limite - s <= 0.001:
		v = 0.0
	if s_alvo - s < 0.05 and v < 0.3:
		_chegar()
	elif limite < s_alvo and limite - s < 0.5:
		estado = Estado.ESPERANDO_BLOCO
	else:
		estado = Estado.ANDANDO


func _chegar() -> void:
	v = 0.0
	estado = Estado.PARADO
	espera = PARADA_S
	var ps := paradas()
	if not ps.is_empty():
		chegada = ps[proxima % ps.size()].estrutura


## Troca de carga numa estação. `estoque` = {enviar: {item: n}, recebido: {item: n}} da estação.
func trocar_carga(estoque: Dictionary, estacao: int) -> void:
	if not carga.is_empty() and origem_carga != estacao:
		for k in carga:
			estoque.recebido[k] = int(estoque.recebido.get(k, 0)) + carga[k]
		carga.clear()
		origem_carga = -1
	var cabe := capacidade() - total_carga()
	for k in estoque.enviar.keys():
		if cabe <= 0:
			break
		var n := mini(cabe, int(estoque.enviar[k]))
		if n <= 0:
			continue
		carga[k] = int(carga.get(k, 0)) + n
		estoque.enviar[k] -= n
		cabe -= n
		origem_carga = estacao


# ------------------------------------------------------------------ rota
## Planeja até a próxima estação. Devolve false (e fica SEM_ROTA) se não há caminho.
## `pelo_outro_lado` = destravar: prefere inverter (se der caminho por trás).
func planejar(pelo_outro_lado := false) -> bool:
	estado = Estado.SEM_ROTA
	var ps := paradas()
	var n := ps.size()
	if n == 0 or segs.is_empty():
		return false
	var est: Dictionary = {}
	for k in n:                      # pula estações fora da linha
		var e: Dictionary = ps[(proxima + k) % n]
		if e.peca >= 0:
			proxima = (proxima + k) % n
			est = e
			break
	if est.is_empty():
		return false
	_cortar_frente()
	# a parada já está debaixo do trem (ou na peça da frente), adiante do ponto de centrar: só ajusta o alvo
	for sg in segs:
		if sg.peca == est.peca:
			var s_parada: float = sg.s0 + _deslocamento(est.peca, sg.de, est.ponto)
			if s_parada + comprimento() / 2.0 >= s - 0.01:
				return _fixar_alvo(s_parada)
	var melhor := _candidato(est, pelo_outro_lado)
	if melhor.is_empty():
		melhor = _candidato(est, not pelo_outro_lado)
	if melhor.is_empty():
		return false
	if melhor.inverter:
		_inverter()
		_cortar_frente()
	var p_est: int = est.peca
	var s_parada := -1.0
	var k_frente := _seg_em(s)
	if melhor.rota.is_empty() and segs[k_frente].peca == p_est:
		s_parada = segs[k_frente].s0 + _deslocamento(p_est, segs[k_frente].de, est.ponto)
	else:
		var ponta: Vector2 = segs[-1].para
		for peca in melhor.rota:
			_anexar(peca, ponta)
			ponta = segs[-1].para
			if peca == p_est:
				break
		if segs[-1].peca != p_est:
			_anexar(p_est, ponta)
		s_parada = segs[-1].s0 + _deslocamento(p_est, segs[-1].de, est.ponto)
	return _fixar_alvo(s_parada)


## Alvo da frente = parada + meio trem (estende a trilha o que der; perto do para-choque, para antes).
func _fixar_alvo(s_parada: float) -> bool:
	s_alvo = s_parada + comprimento() / 2.0
	_estender(s_alvo + 0.01)
	s_alvo = maxf(minf(s_alvo, acum[-1] - 0.05), s)
	estado = Estado.ANDANDO
	return true


## Caminho a partir da frente (ou da cauda, se `inverter`) até a peça da estação. {dist, rota, inverter} ou {}.
func _candidato(est: Dictionary, inverter: bool) -> Dictionary:
	var L := comprimento()
	var k: int
	var e: Vector2
	var d0: float
	if inverter:
		k = _seg_em(s - L)
		e = segs[k].de
		d0 = (s - L) - segs[k].s0
	else:
		k = _seg_em(s)
		e = segs[k].para
		d0 = segs[k].s1 - s
	var atual: int = segs[k].peca
	var p_est: int = est.peca
	var pc: Dictionary = grafo.pecas[p_est]
	# a estação está na própria peça da ponta, adiante
	if atual == p_est:
		var de_ponta: Vector2 = segs[k].para if inverter else segs[k].de
		var off := _deslocamento(p_est, de_ponta, est.ponto)
		var pos: float = (segs[k].s1 - off) if inverter else (segs[k].s0 + off)
		var dist: float = ((s - L) - pos) if inverter else (pos - s)
		if dist >= -0.01:
			return {"dist": dist, "rota": [] as Array[int], "inverter": inverter}
	var melhor := {}
	for x in [pc.a, pc.b]:
		var rota: Array[int] = []
		if e != x:
			rota = grafo.rota(e, x, atual)              # sem meia-volta em cima do próprio trem
		if rota.is_empty() and e != x:
			continue
		var dist := d0
		var cortada: Array[int] = []
		for peca in rota:
			cortada.append(peca)
			if peca == p_est:
				break
			dist += grafo.pecas[peca].comprimento
		var entrada: Vector2 = x
		if cortada.has(p_est):
			# a rota atravessa a estação antes de chegar em x: entra pela outra ponta
			entrada = grafo.outra_ponta(p_est, x)
		elif atual == p_est:
			continue
		dist += _deslocamento(p_est, entrada, est.ponto)
		if melhor.is_empty() or dist < melhor.dist:
			melhor = {"dist": dist, "rota": cortada, "inverter": inverter}
	return melhor


## Distância da ponta `de` da peça até o ponto (no eixo).
func _deslocamento(peca: int, de: Vector2, p: Vector2) -> float:
	var r := grafo.peca_no_ponto(p, 0.1)
	var sa: float = r.get("s", 0.0)
	return sa if de == grafo.pecas[peca].a else grafo.pecas[peca].comprimento - sa


# ------------------------------------------------------------------ trilha
func _anexar(peca: int, de: Vector2) -> void:
	var pts := grafo.pontos_a_partir(peca, de)
	var s0 := 0.0 if acum.is_empty() else acum[-1]
	var i0 := maxi(pontos.size() - 1, 0)
	for k in pts.size():
		if k == 0 and not pontos.is_empty():
			continue
		if not pontos.is_empty():
			acum.append(acum[-1] + pontos[-1].distance_to(pts[k]))
		else:
			acum.append(0.0)
		pontos.append(pts[k])
	segs.append({"peca": peca, "s0": s0, "s1": acum[-1], "i0": i0, "i1": pontos.size() - 1,
			"de": de, "para": grafo.outra_ponta(peca, de)})


## Estende a trilha pela frente (sem voltar pela mesma peça, preferindo seguir reto) até ter `total` metros.
func _estender(total: float) -> bool:
	while acum[-1] < total:
		var ult: Dictionary = segs[-1]
		var dir := (pontos[-1] - pontos[-2]).normalized()
		var melhor := -1
		var melhor_cos := -2.0
		for ar in grafo.arestas.get(ult.para, []):
			if ar.peca == ult.peca:
				continue
			var pts := grafo.pontos_a_partir(ar.peca, ult.para)
			var c := dir.dot((pts[1] - pts[0]).normalized())
			if c > melhor_cos:
				melhor_cos = c
				melhor = ar.peca
		if melhor < 0:
			return false
		_anexar(melhor, ult.para)
	return true


## Joga fora a trilha planejada além da peça onde está a frente.
func _cortar_frente() -> void:
	var k := _seg_em(s)
	if k < 0:
		return
	segs.resize(k + 1)
	pontos.resize(segs[k].i1 + 1)
	acum.resize(segs[k].i1 + 1)
	s_alvo = minf(s_alvo, acum[-1])


## Vira o trem: a cauda passa a ser a frente.
func _inverter() -> void:
	var T: float = acum[-1]
	var L := comprimento()
	pontos.reverse()
	var novo_acum := PackedFloat64Array()
	novo_acum.resize(acum.size())
	var ult := acum.size() - 1
	for i in acum.size():
		novo_acum[i] = T - acum[ult - i]
	acum = novo_acum
	segs.reverse()
	for sg in segs:
		var s0: float = sg.s0
		var i0: int = sg.i0
		sg.s0 = T - sg.s1
		sg.s1 = T - s0
		sg.i0 = ult - sg.i1
		sg.i1 = ult - i0
		var de: Vector2 = sg.de
		sg.de = sg.para
		sg.para = de
	s = T - (s - L)
	carros.reverse()


## Descarta o que ficou bem para trás da cauda (a trilha não cresce para sempre).
func _aparar() -> void:
	var L := comprimento()
	var corta := 0
	while corta < segs.size() - 1 and segs[corta].s1 < s - L - 1.0:
		corta += 1
	if corta == 0:
		return
	var off_s: float = segs[corta].s0
	var off_i: int = segs[corta].i0
	segs = segs.slice(corta)
	pontos = pontos.slice(off_i)
	acum = acum.slice(off_i)
	for i in acum.size():
		acum[i] -= off_s
	for sg in segs:
		sg.s0 -= off_s
		sg.s1 -= off_s
		sg.i0 -= off_i
		sg.i1 -= off_i
	s -= off_s
	s_alvo -= off_s


func _seg_em(d: float) -> int:
	for k in segs.size():
		if d <= segs[k].s1 + 1e-6:
			return k
	return segs.size() - 1


## Ponto e direção da trilha à distância d.
func ponto_em(d: float) -> Dictionary:
	d = clampf(d, 0.0, acum[-1])
	var lo := 0
	var hi := acum.size() - 1
	while hi - lo > 1:
		var m := (lo + hi) / 2
		if acum[m] <= d: lo = m
		else: hi = m
	var seg_len := acum[hi] - acum[lo]
	var f := (d - acum[lo]) / seg_len if seg_len > 0 else 0.0
	return {"pos": pontos[lo].lerp(pontos[hi], f), "dir": (pontos[hi] - pontos[lo]).normalized()}


## Pose de cada carro: {nome, pos (centro, plano da grade), dir (frente), truques: [pos frente, pos trás]}.
func poses() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for i in carros.size():
		var c := s - i * CARRO - CARRO / 2.0
		var f: Dictionary = ponto_em(c + TRUQUE)
		var t: Dictionary = ponto_em(c - TRUQUE)
		var dir: Vector2 = (f.pos - t.pos).normalized()
		out.append({"nome": carros[i], "pos": (f.pos + t.pos) / 2.0, "dir": dir, "truques": [f, t]})
	return out


## Depois que a malha mudou: religa a trilha às peças novas (pela posição) e replaneja.
## Devolve false se o chão sumiu debaixo do trem.
func reancorar(novo: GrafoTrilhos) -> bool:
	grafo = novo
	var L := comprimento()
	for sg in segs:
		var meio: Dictionary = ponto_em((sg.s0 + sg.s1) / 2.0)
		sg.peca = novo.peca_no_ponto(meio.pos, 0.1).get("peca", -1)
		if sg.peca >= 0:
			var pc: Dictionary = novo.pecas[sg.peca]
			# a ponta de entrada pode ter trocado de nome (a/b) na peça nova
			var ini: Vector2 = GrafoTrilhos.chave(pontos[sg.i0])
			sg.de = pc.a if ini == pc.a or pontos[sg.i0].distance_to(pc.a) < pontos[sg.i0].distance_to(pc.b) else pc.b
			sg.para = novo.outra_ponta(sg.peca, sg.de)
	for sg in segs:
		if sg.s1 > s - L and sg.s0 < s and sg.peca < 0:
			return false
	# corta no primeiro buraco à frente
	for k in segs.size():
		if segs[k].peca < 0 and segs[k].s0 >= s:
			segs.resize(k)
			pontos.resize(segs[k - 1].i1 + 1)
			acum.resize(segs[k - 1].i1 + 1)
			break
	for sg in segs:
		if sg.s1 > s - L and sg.s0 < s:
			novo.reservar(id, [sg.peca] as Array[int])
	planejar()
	return true
