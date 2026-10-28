class_name Maquina
extends RefCounted
## Máquina de receita (fornalha, montadora, refinador, extrator…). Estados explícitos para a interface e o animador.
## Dorme quando não pode trabalhar: `tick` sai cedo e só acorda quando recebe insumo ou alguém tira produto.

enum Estado { SEM_RECEITA, SEM_INSUMO, SAIDA_CHEIA, SEM_ENERGIA, SEM_JAZIDA, TRABALHANDO }

const LIMITE_SAIDA := 2      ## em "receitas": acumula até 2× a saída antes de travar
const LIMITE_ENTRADA := 2    ## aceita até 2× cada insumo

var nome := ""
var receita_id := ""
var receita: Dictionary = {}
var velocidade := 1.0
var energia := 1.0           ## satisfação 0..1
var entradas: Dictionary = {}
var saidas: Dictionary = {}
var fluidos: Dictionary = {}     ## fluido → unidades no tanque interno (refinador)
var progresso := 0.0         ## 0..1
var estado := Estado.SEM_RECEITA
var jazida_restante := -1    ## -1 = não usa jazida
var produzidos := 0
var _dormindo := false


func _init(p_nome := "", p_velocidade := 1.0) -> void:
	nome = p_nome
	velocidade = p_velocidade


func definir_receita(id: String, dados: Dictionary) -> void:
	receita_id = id
	receita = dados
	progresso = 0.0
	_acordar()


func acordar() -> void:
	_acordar()


func _acordar() -> void:
	_dormindo = false


func aceita(item: String) -> bool:
	var precisa: Dictionary = receita.get("entradas", {})
	if item == "*":
		return not precisa.is_empty()
	return precisa.has(item) and int(entradas.get(item, 0)) < int(precisa[item]) * LIMITE_ENTRADA


func receber(item: String) -> bool:
	if not aceita(item):
		return false
	entradas[item] = int(entradas.get(item, 0)) + 1
	_acordar()
	return true


## Interface de origem para braços.
func pegar_para_braco(filtro := "") -> String:
	for item in saidas:
		if int(saidas[item]) > 0 and (filtro == "" or filtro == item):
			saidas[item] = int(saidas[item]) - 1
			_acordar()
			return item
	return ""


## Quanto do fluido ainda cabe no tanque interno (até 2× a receita).
func falta_fluido(f: String) -> float:
	var precisa: Dictionary = receita.get("entradas_fluido", {})
	if not precisa.has(f):
		return 0.0
	return maxf(0.0, float(precisa[f]) * LIMITE_ENTRADA - float(fluidos.get(f, 0.0)))


func receber_fluido(f: String, q: float) -> void:
	fluidos[f] = float(fluidos.get(f, 0.0)) + q
	_acordar()


func _tem_insumos() -> bool:
	var precisa_f: Dictionary = receita.get("entradas_fluido", {})
	for f in precisa_f:
		if float(fluidos.get(f, 0.0)) < float(precisa_f[f]):
			return false
	var precisa: Dictionary = receita.get("entradas", {})
	for item in precisa:
		if int(entradas.get(item, 0)) < int(precisa[item]):
			return false
	return true


func _saida_cheia() -> bool:
	var vai_f: Dictionary = receita.get("saidas_fluido", {})
	for f in vai_f:
		if float(fluidos.get(f, 0.0)) + float(vai_f[f]) > float(vai_f[f]) * LIMITE_SAIDA:
			return true
	var vai: Dictionary = receita.get("saidas", {})
	for item in vai:
		if int(saidas.get(item, 0)) + int(vai[item]) > int(vai[item]) * LIMITE_SAIDA:
			return true
	return false


func tick(dt: float) -> void:
	if _dormindo:
		return
	if receita.is_empty():
		estado = Estado.SEM_RECEITA
		_dormindo = true
		return
	if jazida_restante == 0:
		estado = Estado.SEM_JAZIDA
		_dormindo = true
		return
	if _saida_cheia():
		estado = Estado.SAIDA_CHEIA
		_dormindo = true
		return
	if progresso <= 0.0 and not _tem_insumos():
		estado = Estado.SEM_INSUMO
		_dormindo = true
		return
	if energia <= 0.0:
		estado = Estado.SEM_ENERGIA
		return
	if progresso <= 0.0:   # começa um ciclo: consome os insumos
		var precisa: Dictionary = receita.get("entradas", {})
		for item in precisa:
			entradas[item] = int(entradas[item]) - int(precisa[item])
		var precisa_f: Dictionary = receita.get("entradas_fluido", {})
		for f in precisa_f:
			fluidos[f] = float(fluidos[f]) - float(precisa_f[f])
	estado = Estado.TRABALHANDO
	progresso += dt * velocidade * energia / float(receita.get("tempo", 1.0))
	if progresso >= 1.0:
		progresso = 0.0
		var vai: Dictionary = receita.get("saidas", {})
		for item in vai:
			saidas[item] = int(saidas.get(item, 0)) + int(vai[item])
		var vai_f: Dictionary = receita.get("saidas_fluido", {})
		for f in vai_f:
			fluidos[f] = float(fluidos.get(f, 0.0)) + float(vai_f[f])
		produzidos += 1
		if jazida_restante > 0:
			jazida_restante -= 1


func dormindo() -> bool:
	return _dormindo
