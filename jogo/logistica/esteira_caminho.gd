class_name EsteiraCaminho
extends RefCounted
## Uma linha contínua de esteira (vários tiles) simulada como UM objeto — o custo não cresce com o comprimento.
## Itens guardados pelos espaços entre eles (em metros), a partir da saída:
##   espacos[0] = distância da saída até o 1º item; espacos[i] = distância entre o item i−1 e o item i.
## Posição 0 = centro do item encostado na saída; o último centro possível fica em comprimento − ESPACO
## (assim cabem exatamente 4 itens por tile). Andar = encolher UM espaço (o primeiro que ainda não está no mínimo) e crescer o espaço livre do fim.
## Tudo atrás desse espaço anda junto; tudo à frente está parado (fila comprimida). Sem laço por item no caso comum.

const ESPACO := 0.25          ## distância mínima entre itens (4 por tile)

var comprimento := 1.0        ## m (= nº de tiles, curvas contam como 1)
var velocidade := 1.875       ## m/s
var itens: Array[String] = []
var espacos := PackedFloat32Array()
var livre_fim := 1.0          ## distância do último item até a entrada
var proximo: EsteiraCaminho = null   ## para onde os itens saem (outra esteira); se nulo, `saida` decide
var saida: Callable           ## func(item) -> bool: entrega a máquina/braço; true se aceitou
var _primeiro_movel := 0      ## índice do primeiro espaço que pode encolher (cache)


func _init(p_comprimento := 1.0, p_velocidade := 1.875) -> void:
	comprimento = p_comprimento
	velocidade = p_velocidade
	livre_fim = util()


## Faixa útil para os centros dos itens.
func util() -> float:
	return comprimento - ESPACO


func quantidade() -> int:
	return itens.size()


## Pode entrar item na entrada?
func cabe_na_entrada() -> bool:
	return itens.is_empty() or livre_fim >= ESPACO


func inserir_na_entrada(item: String) -> bool:
	if not cabe_na_entrada():
		return false
	if itens.is_empty():
		espacos.append(util())
		livre_fim = 0.0
	elif livre_fim < 2.0 * ESPACO:
		# fila contínua: o item entra colado no anterior e a sobra do tick fica no fim (sem ela, a esteira expressa,
		# que anda 0,1875 m por tick a 30 quadros/s, só aceitaria 1 item a cada 2 ticks: 2× em vez de 3×)
		espacos.append(ESPACO)
		livre_fim -= ESPACO
	else:
		espacos.append(livre_fim)
		livre_fim = 0.0
	itens.append(item)
	return true


## Insere num ponto qualquer (braço soltando no meio). `pos` = distância a partir da saída.
func inserir_em(item: String, pos: float) -> bool:
	pos = clampf(pos, 0.0, util())
	var acum := 0.0
	for i in itens.size():
		var p := acum + espacos[i]
		if pos < p:
			var antes := pos - acum           # espaço entre o item anterior (ou saída) e o novo
			var depois := p - pos             # espaço entre o novo e o item i
			if (i > 0 and antes < ESPACO) or depois < ESPACO:
				return false
			itens.insert(i, item)
			espacos.insert(i, antes)
			espacos[i + 1] = depois
			_primeiro_movel = 0
			return true
		acum = p
	var resto := pos - acum
	if not itens.is_empty() and resto < ESPACO:
		return false
	itens.append(item)
	espacos.append(resto)
	livre_fim = util() - pos
	_primeiro_movel = 0
	return true


## Posição (distância da saída) de cada item — para desenhar e para braços acharem item.
func posicoes() -> PackedFloat32Array:
	var out := PackedFloat32Array()
	var acum := 0.0
	for e in espacos:
		acum += e
		out.append(acum)
	return out


## Retira o item mais perto de `pos` (até `raio`). Devolve "" se não houver.
func retirar_perto(pos: float, raio := 0.5) -> String:
	var ps := posicoes()
	var melhor := -1
	for i in ps.size():
		if absf(ps[i] - pos) <= raio and (melhor < 0 or absf(ps[i] - pos) < absf(ps[melhor] - pos)):
			melhor = i
	if melhor < 0:
		return ""
	var item := itens[melhor]
	if melhor + 1 < itens.size():
		espacos[melhor + 1] += espacos[melhor]
	else:
		livre_fim += espacos[melhor]
	itens.remove_at(melhor)
	espacos.remove_at(melhor)
	_primeiro_movel = 0
	return item


func tick(dt: float) -> void:
	if itens.is_empty():
		return
	var anda := velocidade * dt
	# entrega o item da saída e anda; se a fila inteira encostou e ainda sobra caminho no tick, o próximo item
	# chega à saída no mesmo tick e sai também (sem isso a sobra se perde: a expressa, 0,1875 m por tick a 30
	# quadros/s, entregaria 1 item a cada 2 ticks — 2× em vez de 3×)
	for volta in 8:
		if espacos[0] <= 1e-6:
			var e0 := espacos[0]
			if _entregar():
				itens.remove_at(0)
				espacos.remove_at(0)
				if itens.is_empty():
					livre_fim = util()
					_primeiro_movel = 0
					return
				espacos[0] += e0
				_primeiro_movel = 0
			elif volta > 0:
				return
		anda = _andar(anda)
		if anda <= 1e-6:
			return


func _entregar() -> bool:
	if proximo != null:
		return proximo.inserir_na_entrada(itens[0])
	if saida.is_valid():
		return saida.call(itens[0])
	return false


## Encolhe espaços a partir do primeiro móvel até gastar `anda`; devolve o que sobrou (fila toda encostada).
func _andar(anda: float) -> float:
	var i := _primeiro_movel
	while anda > 0.0 and i < espacos.size():
		var minimo := 0.0 if i == 0 else ESPACO
		var folga := espacos[i] - minimo
		if folga > 1e-6:
			var mv := minf(anda, folga)
			espacos[i] -= mv
			livre_fim += mv
			anda -= mv
			if espacos[i] - minimo <= 1e-6:
				i += 1
			else:
				break
		else:
			i += 1
	_primeiro_movel = mini(i, maxi(espacos.size() - 1, 0))
	return anda
