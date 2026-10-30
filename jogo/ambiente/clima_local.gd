class_name ClimaLocal
extends RefCounted
## Máquinas de clima (fase 2.5, lógica pura): cada uma, ligada e com energia, muda o clima num raio em volta dela
## (regra "clima_local" em estruturas.json). O clima do planeta (Clima) continua o mesmo; quem pergunta "como está o
## tempo aqui?" (coletor de chuva, fogo, turbina, raio, tufão, poluição) passa por aqui.
##  - chuva     (semeador de nuvens): chove pelo menos `chuva` no raio (apaga fogo, enche coletores, molha o chão);
##  - vento     (defletor de vento): o vento do raio sopra para a frente da peça (o jogador gira) e não passa de
##              `vento_max` (sem ventania: tufão não machuca; turbinas não entram em proteção); a poluição dos
##              chunks cobertos vaza para lá;
##  - cupula    (cúpula contra raios): nenhum raio cai no raio — a cúpula pega a descarga (Raios);
##  - regulador (regulador climático): escolhe o clima do raio — "firme" (sem chuva, sem raio, vento manso) ou
##              "chuva" (chuva mansa, sem raio); nos dois, nada de tufão.
## Grade: +x leste, +y norte; vento = para onde sopra.

var mapa: MapaOcupacao
var energia: Callable                 ## func(id) -> 0..1 (Fabrica.energia); sem ela, toda máquina conta como ligada
var zonas: Array[Dictionary] = []     ## {id, tipo, centro: Vector2, raio, dir: Vector2, modo, regra}
var _versao := -1
var _lista: Array[int] = []           ## máquinas de clima do mapa (refeito quando o mapa muda)


func _init(p_mapa: MapaOcupacao) -> void:
	mapa = p_mapa


## Refaz as zonas ativas (chamar a cada passo: a energia muda).
func atualizar() -> void:
	if mapa.versao != _versao:
		_versao = mapa.versao
		_lista.clear()
		for id in mapa.estruturas:
			if Registro.estruturas.get(mapa.estruturas[id].nome, {}).has("clima_local"):
				_lista.append(id)
	zonas.clear()
	for id in _lista:
		if not mapa.estruturas.has(id):
			continue
		var e: Dictionary = mapa.estruturas[id]
		if e.get("desligada", false):
			continue
		if energia.is_valid() and float(energia.call(id)) <= 0.0:
			continue
		var cl: Dictionary = Registro.estruturas[e.nome].clima_local
		zonas.append({"id": id, "tipo": String(cl.tipo), "centro": Grade.centro_da_area(e.minimo, e.area, e.rot),
				"raio": float(cl.get("raio", 40.0)), "dir": Grade.girar(Vector2(0, 1), int(e.rot)),
				"modo": String(e.get("modo_clima", cl.get("modo", ""))), "regra": cl})


## Zona de um tipo que cobre o ponto (a primeira; vazio = nenhuma).
func zona_em(p: Vector2, tipo: String) -> Dictionary:
	for z in zonas:
		if z.tipo == tipo and p.distance_to(z.centro) <= float(z.raio):
			return z
	return {}


## Chuva (0..1) no ponto: a do planeta, mais a do semeador; o regulador manda no raio dele.
func chuva_em(p: Vector2, global: float) -> float:
	var r := zona_em(p, "regulador")
	if not r.is_empty():
		return float(r.regra.get("chuva", 0.4)) if r.modo == "chuva" else 0.0
	var s := zona_em(p, "chuva")
	if not s.is_empty():
		return maxf(global, float(s.regra.get("chuva", 0.75)))
	return global


## Vento no ponto: direção (para onde sopra) × força. Defletor fixa a direção e corta a ventania; o regulador acalma.
func vento_em(p: Vector2, dir: Vector2, forca: float) -> Vector2:
	var r := zona_em(p, "regulador")
	if not r.is_empty():
		return dir * minf(forca, float(r.regra.get("vento_max", 0.4)))
	var d := zona_em(p, "vento")
	if not d.is_empty():
		return (d.dir as Vector2) * minf(maxf(forca, float(d.regra.get("vento_min", 0.3))), float(d.regra.get("vento_max", 0.8)))
	return dir * forca


## Força do vento no ponto (turbina).
func forca_vento_em(p: Vector2, forca: float) -> float:
	return vento_em(p, Vector2.RIGHT, forca).length()


## Tufão não machuca aqui (defletor corta a ventania, regulador acalma).
func sem_tufao(p: Vector2) -> bool:
	return not zona_em(p, "vento").is_empty() or not zona_em(p, "regulador").is_empty()


## Regulador que não deixa cair raio aqui (céu firme ou chuva mansa).
func sem_raio(p: Vector2) -> bool:
	return not zona_em(p, "regulador").is_empty()


## Chunks da poluição cobertos por um defletor → vento forçado (direção × força), para a Poluicao.
func vento_chunks() -> Dictionary:
	var out := {}
	for z in zonas:
		if z.tipo != "vento" and z.tipo != "regulador":
			continue
		var r := float(z.raio)
		var k0 := Grade.chunk_de(Vector2i((z.centro - Vector2(r, r)).floor()))
		var k1 := Grade.chunk_de(Vector2i((z.centro + Vector2(r, r)).floor()))
		for kx in range(k0.x, k1.x + 1):
			for ky in range(k0.y, k1.y + 1):
				var meio := (Vector2(kx, ky) + Vector2(0.5, 0.5)) * Grade.TAM_CHUNK
				if meio.distance_to(z.centro) <= r + Grade.TAM_CHUNK * 0.35:
					out[Vector2i(kx, ky)] = (z.dir as Vector2) * 1.0 if z.tipo == "vento" else Vector2.ZERO
	return out
