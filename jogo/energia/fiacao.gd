class_name Fiacao
## Ligações elétricas automáticas (QoL): o jogador só põe postes; os fios aparecem sozinhos, com alcance limitado.
##   poste ↔ poste ........ até `raio_fio` (9 m, centro a centro), no máximo 5 vizinhos (os mais perto)
##   poste ↔ gerador ...... até `raio_ligacao` (5 m da borda do gerador)
##   poste ↔ máquina ...... até `raio_ligacao`, só se a máquina ainda tem vaga de fonte (padrão: 1)
##   torre sem fio ........ o mesmo, sem fio visível e com alcance maior (dados/estruturas.json)
## Máquina já ligada NÃO troca de poste quando aparece um novo — a não ser que o jogador aceite mais fontes
## (painel da máquina: "fontes"). Removeu um poste: quem ficou sem fonte procura outro dentro do alcance.
## As ligações moram no mapa (campo "fios" de cada estrutura): vão no salvamento e o desenho só lê.

const MAX_POSTES := 5


## Papel elétrico: "poste" (poste/torre: liga coisas), "fonte" (gerador), "consumo" (precisa de energia) ou "".
static func papel(nome: String) -> String:
	var r: Dictionary = Registro.estruturas.get(nome, {})
	if r.get("grupo", "") == "poste":
		return "poste"
	if nome == "gerador":
		return "fonte"
	if float(r.get("energia_kw", 0.0)) > 0.0:
		return "consumo"
	return ""


static func eh_sem_fio(nome: String) -> bool:
	return bool(Registro.estruturas.get(nome, {}).get("sem_fio", false))


## Quantas fontes a estrutura aceita (máquina: escolha do jogador; gerador: postes ilimitados na prática).
static func vagas(e: Dictionary) -> int:
	match papel(e.nome):
		"consumo": return int(e.get("fontes", 1))
		"fonte": return 3
	return 99


static func centro(e: Dictionary) -> Vector2:
	return Grade.centro_da_area(e.minimo, e.area, e.rot)


## Distância do poste até a estrutura (até a borda da área; entre postes, centro a centro).
static func distancia(poste: Dictionary, e: Dictionary) -> float:
	var c := centro(poste)
	if papel(e.nome) == "poste":
		return c.distance_to(centro(e))
	return Colonia._dist_estrutura(c, e)


static func alcance(poste: Dictionary, outro: Dictionary) -> float:
	var r: Dictionary = Registro.estruturas.get(poste.nome, {})
	if papel(outro.nome) == "poste":
		var r2: Dictionary = Registro.estruturas.get(outro.nome, {})
		return minf(float(r.get("raio_fio", 9)), float(r2.get("raio_fio", 9)))
	return float(r.get("raio_ligacao", 5))


static func fios(e: Dictionary) -> Array:
	if not e.has("fios"):
		e["fios"] = []
	return e.fios


static func ligar(mapa: MapaOcupacao, a: int, b: int) -> void:
	var ea: Dictionary = mapa.estruturas[a]
	var eb: Dictionary = mapa.estruturas[b]
	if not fios(ea).has(b):
		ea.fios.append(b)
	if not fios(eb).has(a):
		eb.fios.append(a)


## Fontes atuais de uma máquina/gerador (quantos postes ligados).
static func ligacoes(mapa: MapaOcupacao, e: Dictionary) -> int:
	var n := 0
	for o in fios(e):
		if mapa.estruturas.has(o) and papel(mapa.estruturas[o].nome) == "poste":
			n += 1
	return n


## Quem um poste novo ligaria (usado também pela prévia do fantasma, com o poste ainda não construído).
## Devolve Array de ids.
static func alvos_do_poste(mapa: MapaOcupacao, poste: Dictionary, proprio := -1) -> Array[int]:
	var postes: Array = []
	var outros: Array = []
	var c := centro(poste)
	var maior := maxf(float(Registro.estruturas.get(poste.nome, {}).get("raio_fio", 9)), float(Registro.estruturas.get(poste.nome, {}).get("raio_ligacao", 5))) + 6.0
	for id in _perto(mapa, c, maior):
		if id == proprio:
			continue
		var e: Dictionary = mapa.estruturas[id]
		var p := papel(e.nome)
		if p == "":
			continue
		var d := distancia(poste, e)
		if d > alcance(poste, e):
			continue
		if p == "poste":
			postes.append([d, id])
		elif ligacoes(mapa, e) < vagas(e):
			outros.append([d, id])
	postes.sort_custom(func(a, b): return a[0] < b[0])
	var out: Array[int] = []
	for i in mini(MAX_POSTES, postes.size()):
		out.append(postes[i][1])
	for o in outros:
		out.append(o[1])
	return out


## Estrutura recém-posta: liga conforme o papel.
static func ligar_novo(mapa: MapaOcupacao, id: int) -> void:
	var e: Dictionary = mapa.estruturas[id]
	fios(e)
	match papel(e.nome):
		"poste":
			for alvo in alvos_do_poste(mapa, e, id):
				ligar(mapa, id, alvo)
		"consumo", "fonte":
			_procurar_fontes(mapa, id)


## Máquina/gerador com vaga: liga aos postes mais perto que alcançam.
static func _procurar_fontes(mapa: MapaOcupacao, id: int) -> void:
	var e: Dictionary = mapa.estruturas[id]
	var vaga := vagas(e) - ligacoes(mapa, e)
	if vaga <= 0:
		return
	var cand: Array = []
	for pid in _perto(mapa, centro(e), 30.0):
		var p: Dictionary = mapa.estruturas[pid]
		if papel(p.nome) != "poste" or fios(e).has(pid):
			continue
		var d := distancia(p, e)
		if d <= alcance(p, e):
			cand.append([d, pid])
	cand.sort_custom(func(a, b): return a[0] < b[0])
	for i in mini(vaga, cand.size()):
		ligar(mapa, id, cand[i][1])


## Estrutura saindo: tira os fios dela e os órfãos procuram outro poste.
static func desligar(mapa: MapaOcupacao, id: int) -> void:
	if not mapa.estruturas.has(id):
		return
	var e: Dictionary = mapa.estruturas[id]
	var vizinhos: Array = fios(e).duplicate()
	e.fios = []
	for v in vizinhos:
		if mapa.estruturas.has(v):
			fios(mapa.estruturas[v]).erase(id)
	for v in vizinhos:
		if mapa.estruturas.has(v) and papel(mapa.estruturas[v].nome) in ["consumo", "fonte"]:
			_procurar_fontes_sem(mapa, v, id)


static func _procurar_fontes_sem(mapa: MapaOcupacao, id: int, saindo: int) -> void:
	var tinha: Variant = mapa.estruturas.get(saindo)
	if tinha != null:
		mapa.estruturas.erase(saindo)          # não religa no que está saindo
		_procurar_fontes(mapa, id)
		mapa.estruturas[saindo] = tinha
	else:
		_procurar_fontes(mapa, id)


## Jogador mudou quantas fontes a máquina aceita: sobrou → solta as mais longe; faltou → procura mais.
static func mudar_vagas(mapa: MapaOcupacao, id: int, n: int) -> void:
	var e: Dictionary = mapa.estruturas[id]
	e["fontes"] = n
	var postes: Array = []
	for o in fios(e):
		if mapa.estruturas.has(o) and papel(mapa.estruturas[o].nome) == "poste":
			postes.append([distancia(mapa.estruturas[o], e), o])
	postes.sort_custom(func(a, b): return a[0] < b[0])
	for i in range(n, postes.size()):
		fios(e).erase(postes[i][1])
		fios(mapa.estruturas[postes[i][1]]).erase(id)
	_procurar_fontes(mapa, id)


## Para mapas sem fios ainda (demo montada direto, salvos antigos, testes): liga quem nunca foi ligado.
static func completar(mapa: MapaOcupacao) -> void:
	var ids := mapa.estruturas.keys()
	ids.sort()
	var novos: Array[int] = []          # junta antes: ligar um poste cria "fios" no vizinho, que também é novo
	for id in ids:
		var e: Dictionary = mapa.estruturas[id]
		if not e.has("fios") and papel(e.nome) != "":
			novos.append(id)
	for id in novos:
		ligar_novo(mapa, id)


## Onde o fio prende: no topo do poste; na máquina, na borda virada para o poste, a meia altura.
static func ponto_fio(e: Dictionary, para: Vector2) -> Vector3:
	var dims: Array = Registro.modelos.get(e.nome, {}).get("dims", [1, 1, 1])
	if papel(e.nome) == "poste":
		return Grade.ponto_mundo(centro(e), float(dims[2]) - 0.12)
	var a := Vector2(e.minimo)
	var r := Rect2(a, Vector2(Grade.area_girada(e.area, e.rot)))
	var q := Vector2(clampf(para.x, r.position.x + 0.15, r.end.x - 0.15), clampf(para.y, r.position.y + 0.15, r.end.y - 0.15))
	return Grade.ponto_mundo(q, minf(float(dims[2]) * 0.7, 1.4))


## Estruturas com centro a até `raio` (busca simples; o mapa de um jogo tem poucas centenas de nós elétricos).
static func _perto(mapa: MapaOcupacao, c: Vector2, raio: float) -> Array[int]:
	var out: Array[int] = []
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if e.nome == "pilar":
			continue
		if centro(e).distance_to(c) <= raio + 3.0:
			out.append(id)
	return out
