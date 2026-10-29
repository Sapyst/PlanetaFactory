class_name Colonia
extends RefCounted
## As aranhas do planeta, lógica pura (o desenho fica em DesenhoColonia). O planeta reage à poluição:
##
##  ninhos   nascem do mapa (um sorteio por célula de 48×48, longe do spawn) e são estruturas no MapaOcupacao.
##           Cada ninho absorve a poluição do próprio chunk; essa "raiva" vira aranha (custo_aranha).
##  ataque   juntou grupo_ataque aranhas paradas → o grupo marcha até a fonte de poluição mais perto do ninho.
##           No caminho, estrutura alta (muro, máquina) que barra a passagem é atacada; esteira e trilho, baixos,
##           ficam por baixo das pernas. Água desvia. Sem alvo perto, voltam para o ninho.
##  expansão de tempos em tempos um ninho que absorveu poluição manda construtoras a 14–30 tiles, a 26+ de qualquer estrutura; elas erguem um
##           ninho novo (obra de 10 s) que depois produz aranhas como os outros.
##  torres   atiram na aranha mais perto (ou no ninho, se não houver aranha) dentro do alcance, gastando munição.
##
## Tudo que o desenho precisa saber sai em `eventos` (tiro, morte, ninho novo, estrutura destruída) a cada tick.

enum E { PARADA, ATACANDO, VOLTANDO, CONSTRUINDO, OBRA }

var mapa: MapaOcupacao
var poluicao: Poluicao
var ninhos: Dictionary = {}       ## id da estrutura → {id, centro: Vector2, vida, raiva, obra (0..1; 1 = pronto)}
var aranhas: Dictionary = {}      ## id → {id, pos: Vector2, vida, ninho, estado, alvo (id estrutura), destino: Vector2, mordendo}
var torres: Dictionary = {}       ## id da estrutura → {municao, recarga, mira: Vector2, mirando}
var vida: Dictionary = {}         ## id da estrutura → vida atual (só as que levaram dano)
var eventos: Array[Dictionary] = []
## Quem tira do mapa a estrutura que as aranhas derrubaram (o mundo troca por Construtor.destruir + desenho).
var destruir: Callable
var _celulas: Dictionary = {}
var _prox := 1
var _rng := RandomNumberGenerator.new()
var _lista_torres: Array[int] = []      ## cache: refeito só quando o mapa muda de tamanho
var _tamanho_mapa := -1                 ## versão do mapa da última lista
var _t_expansao := 0.0
var _n: Dictionary
var _a: Dictionary
var _x: Dictionary


func _init(p_mapa: MapaOcupacao, p_poluicao: Poluicao, semente := 7) -> void:
	mapa = p_mapa
	poluicao = p_poluicao
	_rng.seed = semente
	_n = Registro.inimigos.get("ninho", {})
	_a = Registro.inimigos.get("aranha", {})
	_x = Registro.inimigos.get("expansao", {})
	_t_expansao = _x.get("intervalo_s", 150.0)
	destruir = func(id: int) -> void: mapa.remover(id)


# ------------------------------------------------------------------ ninhos do mapa
## Garante os ninhos das células que tocam o chunk (chamado quando o chunk aparece). Determinístico pela semente.
func descobrir_chunk(k: Vector2i) -> void:
	var cel: int = _n.get("celula", 48)
	var a := Vector2(k * Grade.TAM_CHUNK) / cel
	var b := Vector2((k + Vector2i.ONE) * Grade.TAM_CHUNK) / cel
	for cx in range(floori(a.x), ceili(b.x)):
		for cy in range(floori(a.y), ceili(b.y)):
			var c := Vector2i(cx, cy)
			if _celulas.has(c):
				continue
			_celulas[c] = true
			_ninho_da_celula(c, cel)


func _ninho_da_celula(c: Vector2i, cel: int) -> void:
	var centro := (Vector2(c) + Vector2(0.5, 0.5)) * cel
	var dist := centro.length()
	var raio: float = _n.get("raio_sem_ninho", 52)
	if dist < raio:
		return
	var chance: float = _n.get("chance", 0.6) if dist < raio * 2.0 else _n.get("chance_longe", 0.9)
	if Distribuicao.h(c.x, c.y, 501) > chance:
		return
	for tentativa in 8:
		var off := Vector2i(int(Distribuicao.h(c.x, c.y, 510 + tentativa) * (cel - 8)) + 2,
				int(Distribuicao.h(c.x, c.y, 520 + tentativa) * (cel - 8)) + 2)
		var minimo := c * cel + off
		if (Vector2(minimo) + Vector2(1.5, 1.5)).length() < raio:
			continue
		if mapa.motivo_bloqueio("ninho_aranha", minimo, 0) == "":
			var id := _criar_ninho(minimo, 1.0)
			for i in int(_n.get("aranhas_iniciais", 2)):
				_nova_aranha(id)
			return


func _criar_ninho(minimo: Vector2i, obra: float) -> int:
	var id := mapa.colocar("ninho_aranha", minimo, 0)
	if id < 0:
		return -1
	ninhos[id] = {"id": id, "centro": Vector2(minimo) + Vector2(1.5, 1.5), "vida": float(_n.get("vida", 400)),
			"raiva": 0.0, "obra": obra, "absorvido": 0.0}
	eventos.append({"tipo": "ninho_novo", "id": id, "obra": obra})
	return id


func _nova_aranha(ninho: int) -> int:
	var n: Dictionary = ninhos[ninho]
	var id := _prox
	_prox += 1
	var ang := _rng.randf() * TAU
	aranhas[id] = {"id": id, "pos": n.centro + Vector2.from_angle(ang) * 2.4, "vida": float(_a.get("vida", 60)),
			"ninho": ninho, "estado": E.PARADA, "alvo": -1, "destino": n.centro + Vector2.from_angle(ang) * 2.4,
			"mordendo": false, "t": _rng.randf() * 5.0, "preso": 0.0}
	eventos.append({"tipo": "aranha_nova", "id": id})
	return id


func aranhas_do_ninho(ninho: int, estado := -1) -> Array[int]:
	var out: Array[int] = []
	for id in aranhas:
		var ar: Dictionary = aranhas[id]
		if ar.ninho == ninho and (estado < 0 or ar.estado == estado):
			out.append(id)
	return out


# ------------------------------------------------------------------ tick
## fontes: [{id (estrutura), pos: Vector2}] — quem polui (alvo dos ataques).
func tick(dt: float, fontes: Array[Dictionary]) -> void:
	eventos.clear()
	_ninhos(dt, fontes)
	_obras(dt)
	for id in aranhas.keys():
		if aranhas.has(id):
			_aranha(aranhas[id], dt)
	_separar()
	_torres(dt)
	_expandir(dt)


func _ninhos(dt: float, fontes: Array[Dictionary]) -> void:
	var custo: float = _n.get("custo_aranha", 16)
	var maximo: int = _n.get("max_aranhas", 8)
	var grupo: int = _n.get("grupo_ataque", 4)
	for id in ninhos.keys():
		var n: Dictionary = ninhos[id]
		if not mapa.estruturas.has(id):
			ninhos.erase(id)
			continue
		if n.obra < 1.0:
			continue
		var k := Grade.chunk_de(Vector2i(n.centro.floor()))
		var tirou := poluicao.absorver(k, poluicao.em_chunk(k) * float(_n.get("taxa_absorcao", 0.06)) * dt)
		n.raiva += tirou
		n.absorvido += tirou
		if n.raiva >= custo and aranhas_do_ninho(id).size() < maximo:
			n.raiva -= custo
			_nova_aranha(id)
		var paradas := aranhas_do_ninho(id, E.PARADA)
		if paradas.size() >= grupo:
			var alvo := _fonte_mais_perto(n.centro, fontes)
			if alvo >= 0:
				for a in paradas.slice(0, grupo):
					aranhas[a].estado = E.ATACANDO
					aranhas[a].alvo = alvo
				eventos.append({"tipo": "ataque", "ninho": id, "alvo": alvo})


func _fonte_mais_perto(p: Vector2, fontes: Array[Dictionary]) -> int:
	var melhor := -1
	var md: float = _n.get("raio_ataque", 160)
	for f in fontes:
		if not mapa.estruturas.has(f.id):
			continue
		var d: float = p.distance_to(f.pos)
		if d < md:
			md = d
			melhor = f.id
	return melhor


func _aranha(ar: Dictionary, dt: float) -> void:
	ar.mordendo = false
	ar.t += dt
	# presa (água no caminho, sem saída): desiste da obra/ataque; presa voltando, some no chão de volta ao ninho
	if ar.preso > 15.0 and ar.estado in [E.ATACANDO, E.CONSTRUINDO, E.VOLTANDO]:
		ar.preso = 0.0
		if ar.estado == E.VOLTANDO or not ninhos.has(ar.ninho):
			aranhas.erase(ar.id)
			eventos.append({"tipo": "aranha_sumiu", "id": ar.id})
			return
		if ar.estado in [E.ATACANDO, E.CONSTRUINDO]:
			ar.estado = E.VOLTANDO
	match ar.estado:
		E.PARADA:
			if not ninhos.has(ar.ninho):
				ar.estado = E.ATACANDO                      # ninho caiu: as que sobraram vão à luta
				ar.alvo = _estrutura_perto(ar.pos, float(_a.get("raio_procura", 20)) * 3.0)
				return
			# rondando o ninho
			if ar.pos.distance_to(ar.destino) < 0.3:
				var n: Dictionary = ninhos[ar.ninho]
				ar.destino = n.centro + Vector2.from_angle(_rng.randf() * TAU) * (2.2 + _rng.randf() * 1.6)
			_mover(ar, ar.destino, dt, 0.35)
		E.ATACANDO:
			if not mapa.estruturas.has(ar.alvo):
				ar.alvo = _estrutura_perto(ar.pos, float(_a.get("raio_procura", 20)))
				if ar.alvo < 0:
					ar.estado = E.VOLTANDO
					return
			var e: Dictionary = mapa.estruturas[ar.alvo]
			if _dist_estrutura(ar.pos, e) <= float(_a.get("alcance", 1.2)):
				_morder(ar, ar.alvo, dt)
			else:
				_mover(ar, Grade.centro_da_area(e.minimo, e.area, e.rot), dt, 1.0)
		E.VOLTANDO:
			if not ninhos.has(ar.ninho):
				ar.estado = E.ATACANDO
				return
			var n: Dictionary = ninhos[ar.ninho]
			if ar.pos.distance_to(n.centro) < 2.6:
				ar.estado = E.PARADA
				ar.destino = ar.pos
			else:
				_mover(ar, n.centro, dt, 1.0)
		E.CONSTRUINDO:
			if ar.pos.distance_to(ar.destino) < 0.6:
				_chegou_obra(ar)
			else:
				_mover(ar, ar.destino, dt, 1.0)
		E.OBRA:
			if not ninhos.has(ar.ninho):
				ar.estado = E.ATACANDO
				ar.alvo = -1
				return
			var n: Dictionary = ninhos[ar.ninho]
			if n.obra >= 1.0:
				ar.estado = E.PARADA
				ar.destino = ar.pos
				return
			var ang: float = ar.t * 0.8 + ar.id
			_mover(ar, n.centro + Vector2.from_angle(ang) * 2.3, dt, 0.5)
			ar.mordendo = true                              # pernas trabalhando na obra


## Anda em linha reta; água desvia (tenta ângulos maiores); estrutura alta no caminho vira alvo de mordida.
func _mover(ar: Dictionary, para: Vector2, dt: float, ritmo: float) -> void:
	var d: Vector2 = para - ar.pos
	if d.length() < 0.05:
		return
	# "presa" = não chega mais perto do destino (andar em círculo num cercado também conta)
	if ar.get("para_ant", Vector2.INF) != para:
		ar.para_ant = para
		ar.melhor = INF
		ar.preso = 0.0
	if d.length() < ar.melhor - 0.3:
		ar.melhor = d.length()
		ar.preso = 0.0
	else:
		ar.preso += dt
	var dir := d.normalized()
	var passo: float = minf(float(_a.get("velocidade", 1.4)) * ritmo * dt, d.length())
	for ang in [0.0, 0.6, -0.6, 1.2, -1.2, 1.9, -1.9, 2.6, -2.6]:
		var tent := dir.rotated(ang)
		var novo: Vector2 = ar.pos + tent * passo
		if mapa.gerador.eh_agua(mapa.gerador.terreno(Vector2i((ar.pos + tent * 0.7).floor()))):
			continue
		# corpo com raio: nenhuma parte da aranha entra numa construção (nem no alvo: morde pela borda)
		var bloq := _corpo_bloqueado(novo)
		if bloq >= 0 and ar.estado == E.ATACANDO and ang == 0.0:
			_morder(ar, bloq, dt)                        # no caminho (ou é o alvo): morde dali
			return
		if bloq >= 0:
			continue
		ar.pos = novo
		return


const RAIO_CORPO := 0.55     ## aranha + pernas no chão: distância mínima de qualquer construção que barra


## Construção que o corpo da aranha tocaria nesta posição (−1 = livre).
func _corpo_bloqueado(p: Vector2) -> int:
	for o in [Vector2.ZERO, Vector2(RAIO_CORPO, 0), Vector2(-RAIO_CORPO, 0), Vector2(0, RAIO_CORPO), Vector2(0, -RAIO_CORPO),
			Vector2(0.39, 0.39), Vector2(-0.39, 0.39), Vector2(0.39, -0.39), Vector2(-0.39, -0.39)]:
		var b := _bloqueio(Vector2i((p + o).floor()))
		if b >= 0:
			return b
	return -1


## Estrutura que barra a passagem neste tile (alta o bastante); ninho não barra aranha.
func _bloqueio(t: Vector2i) -> int:
	var id: int = mapa.tiles.get(t, -1)
	if id < 0:
		return -1
	var nome: String = mapa.estruturas[id].nome
	if nome == "ninho_aranha":
		return -1
	var dims: Array = Registro.modelos.get(nome, {}).get("dims", [0, 0, 0])
	return id if float(dims[2]) > float(_a.get("altura_que_bloqueia", 0.5)) else -1


func _morder(ar: Dictionary, id: int, dt: float) -> void:
	ar.mordendo = true
	ar.preso = 0.0                                    # mordendo está fazendo progresso
	if not mapa.estruturas.has(id):
		return
	var em: Dictionary = mapa.estruturas[id]
	ar.mordida = Grade.centro_da_area(em.minimo, em.area, em.rot)       # para onde as pernas golpeiam (desenho)
	var nome: String = mapa.estruturas[id].nome
	var v: float = vida.get(id, float(Registro.estruturas.get(nome, {}).get("vida", 100)))
	v -= float(_a.get("dano", 15)) * dt
	vida[id] = v
	if v <= 0.0:
		vida.erase(id)
		var e: Dictionary = mapa.estruturas[id]
		eventos.append({"tipo": "destruida", "id": id, "nome": nome, "centro": Grade.centro_da_area(e.minimo, e.area, e.rot)})
		destruir.call(id)


func _estrutura_perto(p: Vector2, raio: float) -> int:
	var melhor := -1
	var md := raio
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if e.nome == "ninho_aranha" or e.nome == "pilar":
			continue
		var d := _dist_estrutura(p, e)
		if d < md:
			md = d
			melhor = id
	return melhor


static func _dist_estrutura(p: Vector2, e: Dictionary) -> float:
	var a := Vector2(e.minimo)
	var r := Rect2(a, Vector2(Grade.area_girada(e.area, e.rot)))
	var q := Vector2(clampf(p.x, r.position.x, r.end.x), clampf(p.y, r.position.y, r.end.y))
	return p.distance_to(q)


## Aranhas não se empilham (empurrão leve entre vizinhas).
func _separar() -> void:
	var lista := aranhas.values()
	for i in lista.size():
		for j in range(i + 1, lista.size()):
			var d: Vector2 = lista[j].pos - lista[i].pos
			var l := d.length()
			if l < 1.4 and l > 1e-4:
				var em := d / l * (1.4 - l) * 0.25
				# o empurrão nunca joga uma aranha para dentro de uma construção
				if _corpo_bloqueado(lista[i].pos - em) < 0:
					lista[i].pos -= em
				if _corpo_bloqueado(lista[j].pos + em) < 0:
					lista[j].pos += em


# ------------------------------------------------------------------ torres
func _torres(dt: float) -> void:
	if mapa.versao != _tamanho_mapa:
		_tamanho_mapa = mapa.versao
		_lista_torres.clear()
		for id in mapa.estruturas:
			if mapa.estruturas[id].nome == "torre_defesa":
				_lista_torres.append(id)
	for id in _lista_torres:
		if not mapa.estruturas.has(id):
			continue
		var e: Dictionary = mapa.estruturas[id]
		_garantir_torre(id)
		var t: Dictionary = torres[id]
		t.recarga -= dt
		var regra: Dictionary = Registro.estruturas["torre_defesa"]
		var c := Grade.centro_da_area(e.minimo, e.area, e.rot)
		var alcance: float = regra.get("alcance", 18)
		var alvo := -1
		var md := alcance
		for a in aranhas:
			var d: float = c.distance_to(aranhas[a].pos)
			if d < md:
				md = d
				alvo = a
		var ninho := -1
		if alvo < 0:
			for n in ninhos:
				var d: float = c.distance_to(ninhos[n].centro)
				if d < md:
					md = d
					ninho = n
		t.mirando = alvo >= 0 or ninho >= 0
		if not t.mirando:
			continue
		t.mira = aranhas[alvo].pos if alvo >= 0 else ninhos[ninho].centro
		if t.recarga > 0.0 or t.municao <= 0:
			continue
		t.recarga = 1.0 / float(regra.get("cadencia", 3))
		t.municao -= 1
		var dano: float = regra.get("dano", 8)
		eventos.append({"tipo": "tiro", "torre": id, "de": c, "para": t.mira, "aranha": alvo, "ninho": ninho})
		if alvo >= 0:
			aranhas[alvo].vida -= dano
			if aranhas[alvo].vida <= 0.0:
				eventos.append({"tipo": "aranha_morta", "id": alvo, "pos": aranhas[alvo].pos})
				aranhas.erase(alvo)
		else:
			ninhos[ninho].vida -= dano
			if ninhos[ninho].vida <= 0.0:
				eventos.append({"tipo": "ninho_destruido", "id": ninho, "pos": ninhos[ninho].centro})
				ninhos.erase(ninho)
				mapa.remover(ninho)


## Munição que chegou à torre (braço/esteira, via Fabrica).
func carregar_torre(id: int, tiros: int) -> void:
	_garantir_torre(id)
	torres[id].municao += tiros


func _garantir_torre(id: int) -> void:
	if not torres.has(id):
		torres[id] = {"municao": int(Registro.inimigos.get("torre", {}).get("municao_inicial", 60)), "recarga": 0.0,
				"mira": Vector2.ZERO, "mirando": false}


# ------------------------------------------------------------------ salvamento
func estado() -> Dictionary:
	return {"ninhos": ninhos, "aranhas": aranhas, "torres": torres, "vida": vida, "celulas": _celulas.keys(),
			"prox": _prox, "t_expansao": _t_expansao, "rng": _rng.state}


func restaurar(d: Dictionary) -> void:
	ninhos = d.ninhos
	aranhas = d.aranhas
	torres = d.torres
	vida = d.vida
	_celulas.clear()
	for c in d.celulas:
		_celulas[c] = true
	_prox = d.prox
	_t_expansao = d.t_expansao
	_rng.state = d.rng


# ------------------------------------------------------------------ expansão
func _expandir(dt: float) -> void:
	_t_expansao -= dt
	if _t_expansao > 0.0:
		return
	_t_expansao = _x.get("intervalo_s", 150.0)
	var prontos := []
	for id in ninhos:
		# só expande quem está sendo "irritado" pela poluição (absorveu o bastante desde a última vez)
		if ninhos[id].obra >= 1.0 and ninhos[id].absorvido >= float(_x.get("poluicao_para_expandir", 30)) \
				and aranhas_do_ninho(id, E.PARADA).size() >= int(_x.get("construtoras", 3)):
			prontos.append(id)
	if prontos.is_empty():
		return
	var origem: int = prontos[_rng.randi() % prontos.size()]
	ninhos[origem].absorvido = 0.0
	var lugar := _lugar_de_ninho(ninhos[origem].centro)
	if lugar == Vector2i(-99999, -99999):
		return
	for a in aranhas_do_ninho(origem, E.PARADA).slice(0, int(_x.get("construtoras", 3))):
		aranhas[a].estado = E.CONSTRUINDO
		aranhas[a].destino = Vector2(lugar) + Vector2(1.5, 1.5)
		aranhas[a].obra_em = lugar
	eventos.append({"tipo": "expansao", "de": origem, "para": lugar})


func _lugar_de_ninho(perto: Vector2) -> Vector2i:
	var livre: float = _x.get("livre_de_estruturas", 14)
	for tentativa in 20:
		var d := _rng.randf_range(_x.get("dist_min", 14), _x.get("dist_max", 30))
		var p := perto + Vector2.from_angle(_rng.randf() * TAU) * d
		var minimo := Vector2i(p.floor()) - Vector2i(1, 1)
		if mapa.motivo_bloqueio("ninho_aranha", minimo, 0) != "":
			continue
		if _estrutura_perto(p, livre) >= 0 or p.length() < float(_x.get("longe_do_spawn", 40)):
			continue
		var perto_ninho := false
		for n in ninhos:
			if ninhos[n].centro.distance_to(p) < 8.0:
				perto_ninho = true
		if not perto_ninho:
			return minimo
	return Vector2i(-99999, -99999)


func _chegou_obra(ar: Dictionary) -> void:
	var lugar: Vector2i = ar.obra_em
	var c := Vector2(lugar) + Vector2(1.5, 1.5)
	# outra construtora já começou a obra?
	for n in ninhos:
		if ninhos[n].centro == c:
			ar.ninho = n
			ar.estado = E.OBRA
			return
	var id := _criar_ninho(lugar, 0.0)
	if id < 0:
		ar.estado = E.VOLTANDO                             # alguém construiu ali antes
		return
	ar.ninho = id
	ar.estado = E.OBRA


## Obra de ninho: 10 s com 3 operárias (mais devagar com menos).
func _obras(dt: float) -> void:
	var tempo: float = _x.get("tempo_obra", 10)
	for id in ninhos:
		var n: Dictionary = ninhos[id]
		if n.obra < 1.0:
			var operarias := aranhas_do_ninho(id, E.OBRA).size()
			n.obra = minf(1.0, n.obra + dt / tempo * mini(operarias, 3) / 3.0)
			if n.obra >= 1.0:
				eventos.append({"tipo": "ninho_pronto", "id": id})
