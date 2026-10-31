class_name Portas
## Ligação das portas de uma estrutura: se cada entrada e saída de item/fluido tem algo encostado (esteira, cano,
## braço, baú ou a porta de outra máquina). O fantasma pinta a seta pelo resultado e o mundo avisa, numa estrutura
## já construída, onde falta ligar.

const ESTEIRAS := ["esteira", "esteira_rampa", "rampa_desce", "esteira_tunel_entrada", "esteira_tunel_saida", "divisor", "juncao", "divisor_filtro"]


static func eh_esteira(nome: String) -> bool:
	return nome in ESTEIRAS or nome.begins_with("esteira")


static func eh_braco(nome: String) -> bool:
	return nome.begins_with("braco")


static func eh_cano(nome: String) -> bool:
	return nome.begins_with("cano") or nome in ["bomba", "tanque", "sensor_tanque", "valvula"]


## Quem tem aviso de porta solta: máquinas e o que recebe/entrega (não as próprias esteiras, canos, trilhos, braços).
static func mostra_aviso(nome: String) -> bool:
	# torre de energia: a entrada de munição é só reserva para quando falta energia, não é obrigatória
	# núcleo: já começa com kit e energia própria; as entradas dele são opcionais
	return not (eh_esteira(nome) or eh_braco(nome) or eh_cano(nome) or nome.begins_with("trilho")
			or nome in ["pilar", "bau", "bau_grande", "torre_defesa", "nucleo"])


## Frente e costas do braço (onde solta e onde pega): tile da frente = minimo + direção da rotação × alcance.
static func frente_braco(e: Dictionary) -> Vector2i:
	return Vector2i(e.minimo) + Grade.girar_i(Vector2i(0, 1), int(e.rot)) * _alcance(e.nome)


static func costas_braco(e: Dictionary) -> Vector2i:
	if Registro.estruturas.get(e.nome, {}).has("alcance_max"):          # braço quântico: alcance escolhido atrás
		return Vector2i(e.minimo) - Grade.girar_i(Vector2i(0, 1), int(e.rot)) * Fabrica.alcance_origem(e)
	return Vector2i(e.minimo) - Grade.girar_i(Vector2i(0, 1), int(e.rot)) * _alcance(e.nome)


## Modo Radial (pega de 3 lados): só para braço com alcance fixo; o quântico estica a lança para trás, e fica Linear.
static func braco_radial(e: Dictionary) -> bool:
	return e.get("modo_braco", "") == "radial" and not Registro.estruturas.get(e.nome, {}).has("alcance_max")


## Tiles de onde o braço pega: atrás; no Radial, também os dois lados (mesmo alcance).
static func origens_braco(e: Dictionary) -> Array[Vector2i]:
	var out: Array[Vector2i] = [costas_braco(e)]
	if braco_radial(e):
		var d := Grade.girar_i(Vector2i(0, 1), int(e.rot)) * _alcance(e.nome)
		out.append(Vector2i(e.minimo) + Vector2i(-d.y, d.x))
		out.append(Vector2i(e.minimo) + Vector2i(d.y, -d.x))
	return out


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
					if not eh_braco(o.nome):
						continue
					if entrada and dentro.has(frente_braco(o)):
						return true
					if not entrada:
						for q in origens_braco(o):
							if dentro.has(q):
								return true
	return false


## Situação de cada porta de item/fluido de `e` (no mapa ou ainda fantasma): [{pos, dir, io, tipo, z, tile_fora, tile_dentro,
## ok}]. ok = encaixada em algo certo, ou braço servindo aquele sentido por qualquer lado (braço só carrega item, não fluido).
## É a mesma regra para o fantasma (verde/vermelho) e para o aviso da estrutura pronta.
static func estados(mapa: MapaOcupacao, e: Dictionary) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var area: Vector2i = e.get("area", Registro.area(e.nome))
	var serve := {}                                       # "ENT"/"SAI" → bool (só calcula se alguma porta de item precisar)
	for porta in Registro.modelos.get(e.nome, {}).get("portas", []):
		if porta.tipo == "TRILHO":
			continue
		var ok := ligada(mapa, e, porta)
		if not ok and porta.tipo == "ITEM":
			if not serve.has(porta.io):
				serve[porta.io] = braco_serve(mapa, e, porta.io == "ENT")
			ok = serve[porta.io]
		var pm := Grade.porta_no_mundo(porta, e.minimo, area, e.rot)
		out.append({"pos": pm.pos, "dir": pm.dir, "io": porta.io, "tipo": porta.tipo, "z": float(porta.pos[2]),
				"tile_fora": pm.tile_fora, "tile_dentro": pm.tile_dentro, "ok": ok})
	return out


## Portas soltas de uma estrutura do mapa (formato de `estados`) — vazio se tudo ligado ou se ela não tem aviso.
static func soltas(mapa: MapaOcupacao, id: int) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var e: Dictionary = mapa.estruturas[id]
	if not mostra_aviso(e.nome):
		return out
	for s in estados(mapa, e):
		if not s.ok:
			out.append(s)
	return out
