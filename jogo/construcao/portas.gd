class_name Portas
## Ligação das portas de uma estrutura: se cada entrada e saída de item/fluido tem algo encostado (esteira, cano,
## braço, baú ou a porta de outra máquina). O fantasma pinta a seta pelo resultado e o mundo avisa, numa estrutura
## já construída, onde falta ligar.

const ESTEIRAS := ["esteira", "esteira_rampa", "rampa_desce", "esteira_tunel_entrada", "esteira_tunel_saida", "divisor", "juncao"]


static func eh_esteira(nome: String) -> bool:
	return nome in ESTEIRAS or nome.begins_with("esteira")


static func eh_braco(nome: String) -> bool:
	return nome.begins_with("braco")


static func eh_cano(nome: String) -> bool:
	return nome.begins_with("cano") or nome in ["bomba", "tanque"]


## Quem tem aviso de porta solta: máquinas e o que recebe/entrega (não as próprias esteiras, canos, trilhos, braços).
static func mostra_aviso(nome: String) -> bool:
	return not (eh_esteira(nome) or eh_braco(nome) or eh_cano(nome) or nome.begins_with("trilho") or nome in ["pilar", "bau", "bau_grande"])


## Frente e costas do braço (onde solta e onde pega): tile da frente = minimo + direção da rotação × alcance.
static func frente_braco(e: Dictionary) -> Vector2i:
	return Vector2i(e.minimo) + Grade.girar_i(Vector2i(0, 1), int(e.rot)) * _alcance(e.nome)


static func costas_braco(e: Dictionary) -> Vector2i:
	return Vector2i(e.minimo) - Grade.girar_i(Vector2i(0, 1), int(e.rot)) * _alcance(e.nome)


static func _alcance(nome: String) -> int:
	return 2 if nome == "braco_longo" else 1


## A porta `porta` (de modelos.json) da estrutura `e` tem algo ligado? `e` pode ainda não estar no mapa (fantasma).
static func ligada(mapa: MapaOcupacao, e: Dictionary, porta: Dictionary) -> bool:
	if porta.tipo == "TRILHO":
		return true
	var area: Vector2i = e.get("area", Registro.area(e.nome))
	var pm := Grade.porta_no_mundo(porta, e.minimo, area, e.rot)
	for id in mapa.ids_no_tile(pm.tile_fora):
		var o: Dictionary = mapa.estruturas[id]
		if porta.tipo == "ITEM" and (eh_esteira(o.nome) or eh_braco(o.nome) or o.nome in ["bau", "bau_grande"]):
			return true
		if porta.tipo == "FLUIDO" and eh_cano(o.nome):
			return true
		for p2 in Registro.modelos.get(o.nome, {}).get("portas", []):          # porta de outra máquina encostada
			if p2.tipo == porta.tipo and p2.io != porta.io:
				var q := Grade.porta_no_mundo(p2, o.minimo, o.area, o.rot)
				if q.tile_fora == pm.tile_dentro and q.tile_dentro == pm.tile_fora:
					return true
	return false


## Algum braço em volta põe itens dentro (entrada) ou tira (saída) da estrutura? O braço serve por qualquer lado.
static func braco_serve(mapa: MapaOcupacao, e: Dictionary, entrada: bool) -> bool:
	var area: Vector2i = e.get("area", Registro.area(e.nome))
	var dentro := {}
	for t in Grade.tiles_da_area(e.minimo, area, e.rot):
		dentro[t] = true
	for t in dentro:
		for d in Grade.DIRECOES:
			for k in [1, 2]:
				for id in mapa.ids_no_tile(t + d * k):
					var o: Dictionary = mapa.estruturas[id]
					if eh_braco(o.nome) and dentro.has(frente_braco(o) if entrada else costas_braco(o)):
						return true
	return false


## Portas soltas de uma estrutura do mapa: [{pos (grade), dir, io}] — vazio se tudo ligado.
static func soltas(mapa: MapaOcupacao, id: int) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var e: Dictionary = mapa.estruturas[id]
	if not mostra_aviso(e.nome):
		return out
	var ent := -1
	var sai := -1
	for porta in Registro.modelos.get(e.nome, {}).get("portas", []):
		if porta.tipo == "TRILHO" or ligada(mapa, e, porta):
			continue
		if porta.io == "ENT":
			if ent == -1:
				ent = 1 if braco_serve(mapa, e, true) else 0
			if ent == 1:
				continue
		else:
			if sai == -1:
				sai = 1 if braco_serve(mapa, e, false) else 0
			if sai == 1:
				continue
		var pm := Grade.porta_no_mundo(porta, e.minimo, e.area, e.rot)
		out.append({"pos": pm.pos, "dir": pm.dir, "io": porta.io, "z": float(porta.pos[2])})
	return out
