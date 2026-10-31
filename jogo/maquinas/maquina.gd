class_name Maquina
extends RefCounted
## Máquina de receita (fornalha, montadora, refinador, extrator…). Estados explícitos para a interface e o animador.
## Dorme quando não pode trabalhar: `tick` sai cedo e só acorda quando recebe insumo ou alguém tira produto.

## ESPERANDO_CLIMA: coletor de chuva / condensador parados porque não chove / não há neblina (`clima` = 0).
## PRONTIDAO: supressor com água, vigiando (só trabalha quando há fogo no raio).
## DESLIGADA: desligada pelo jogador ou pelo comparador; quem marca é a Fabrica (nada anda nem consome).
enum Estado { SEM_RECEITA, SEM_INSUMO, SAIDA_CHEIA, SEM_ENERGIA, SEM_JAZIDA, TRABALHANDO, ESPERANDO_CLIMA, PRONTIDAO, DESLIGADA }

const LIMITE_SAIDA := 2      ## em "receitas": acumula até 2× a saída antes de travar
const LIMITE_ENTRADA := 2    ## aceita até 2× cada insumo
const RITMO_JANELA := 30.0   ## segundos

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
var produtividade := 0.0     ## fração extra de produto por ciclo (melhoria de mineração: 0,1 = +10%)
var extra := 0.0             ## barra de produtividade: ao passar de 1, sai um ciclo de graça
var tanque_fluido := 0.0     ## tanque interno maior que 2× a receita (coletor de chuva 2.000, supressor 200…)
var transborda := false      ## fluido que não sai pelo cano não trava a máquina (filtro: a sobra volta ao rio)
var clima := 1.0             ## fator do clima de agora (coletor: chuva, condensador: neblina); 0 = espera
var retem: Array = []        ## produtos que não saem por braço (estação de drones: o drone vai para a frota)
var rende_esgotada := 0.0    ## broca de núcleo: fração do ritmo com a jazida esgotada (0,1 = 10% para sempre)
var desligada := false       ## quem muda é a Fabrica (ligada/desligada pelo jogador ou pelo comparador)
var tempo_total := 0.0       ## segundos desde que foi posta (vai no save)
var tempo_ativo := 0.0       ## segundos trabalhando
var ciclos_min := 0.0        ## ciclos por minuto, medidos na última janela de RITMO_JANELA
var _ritmo_t := 0.0
var _ritmo_n := 0
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
		if int(saidas[item]) > 0 and (filtro == "" or filtro == item) and not item in retem:
			saidas[item] = int(saidas[item]) - 1
			_acordar()
			return item
	return ""


## Quanto do fluido ainda cabe no tanque interno (até 2× a receita).
func falta_fluido(f: String) -> float:
	var precisa: Dictionary = receita.get("entradas_fluido", {})
	if not precisa.has(f):
		return 0.0
	return maxf(0.0, maxf(float(precisa[f]) * LIMITE_ENTRADA, tanque_fluido) - float(fluidos.get(f, 0.0)))


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
	var vai_f: Dictionary = receita.get("saidas_fluido", {}) if not transborda else {}
	for f in vai_f:
		if float(fluidos.get(f, 0.0)) + float(vai_f[f]) > limite_fluido(f):
			return true
	var vai: Dictionary = receita.get("saidas", {})
	for item in vai:
		if int(saidas.get(item, 0)) + int(vai[item]) > int(vai[item]) * LIMITE_SAIDA:
			return true
	return false


## Quanto do fluido de saída a máquina guarda antes de travar (2× a receita, ou o tanque interno).
func limite_fluido(f: String) -> float:
	return maxf(float(receita.get("saidas_fluido", {}).get(f, 0.0)) * LIMITE_SAIDA, tanque_fluido)


func tick(dt: float) -> void:
	if _dormindo:
		return
	if receita.is_empty():
		estado = Estado.SEM_RECEITA
		_dormindo = true
		return
	if jazida_restante == 0 and rende_esgotada <= 0.0:
		estado = Estado.SEM_JAZIDA
		_dormindo = true
		return
	if _saida_cheia():
		estado = Estado.SAIDA_CHEIA
		_dormindo = true
		return
	# sem energia vem antes de "falta insumo": máquina sem poste e vazia mostrava a caixa laranja e escondia a causa
	# (o braço dela, também sem energia, não traz o insumo)
	if energia <= 0.0:
		estado = Estado.SEM_ENERGIA
		return
	if progresso <= 0.0 and not _tem_insumos():
		estado = Estado.SEM_INSUMO
		_dormindo = true
		return
	if clima <= 0.0:
		estado = Estado.ESPERANDO_CLIMA
		return
	if progresso <= 0.0:   # começa um ciclo: consome os insumos
		var precisa: Dictionary = receita.get("entradas", {})
		for item in precisa:
			entradas[item] = int(entradas[item]) - int(precisa[item])
		var precisa_f: Dictionary = receita.get("entradas_fluido", {})
		for f in precisa_f:
			fluidos[f] = float(fluidos[f]) - float(precisa_f[f])
	estado = Estado.TRABALHANDO
	var ritmo := rende_esgotada if jazida_restante == 0 else 1.0
	progresso += dt * velocidade * energia * clima * ritmo / float(receita.get("tempo", 1.0))
	if progresso >= 1.0:
		progresso = 0.0
		var vai: Dictionary = receita.get("saidas", {})
		for item in vai:
			saidas[item] = int(saidas.get(item, 0)) + int(vai[item])
		var vai_f: Dictionary = receita.get("saidas_fluido", {})
		for f in vai_f:
			fluidos[f] = float(fluidos.get(f, 0.0)) + float(vai_f[f])
			if transborda:
				fluidos[f] = minf(float(fluidos[f]), limite_fluido(f))    # a sobra volta ao rio
		produzidos += 1
		if jazida_restante > 0:
			jazida_restante -= 1
		extra += produtividade                  # produtividade: produto a mais sem gastar insumo nem jazida
		while extra >= 1.0 - 1e-6:
			extra -= 1.0
			for item in vai:
				saidas[item] = int(saidas.get(item, 0)) + int(vai[item])
			for f in vai_f:
				fluidos[f] = minf(float(fluidos.get(f, 0.0)) + float(vai_f[f]), limite_fluido(f) if transborda else INF)


## Estatística do painel: tempo trabalhando e ritmo. Fica fora do tick porque o tick sai cedo quando dorme.
func contar(dt: float) -> void:
	tempo_total += dt
	if estado == Estado.TRABALHANDO:
		tempo_ativo += dt
	_ritmo_t += dt
	if _ritmo_t >= RITMO_JANELA:
		ciclos_min = (produzidos - _ritmo_n) * 60.0 / _ritmo_t
		_ritmo_n = produzidos
		_ritmo_t = 0.0


## Itens que sai por minuto, no ritmo medido (antes da 1ª janela fechar, o que já fez até agora).
func itens_por_minuto() -> float:
	var ciclos := ciclos_min
	if tempo_total < RITMO_JANELA and tempo_total > 0.0:
		ciclos = (produzidos - _ritmo_n) * 60.0 / tempo_total
	var por_ciclo := 0
	for it in receita.get("saidas", {}):
		por_ciclo += int(receita.saidas[it])
	return ciclos * por_ciclo


## Tem insumo para um ciclo e lugar na saída (captador esperando raio).
func pronta() -> bool:
	return not receita.is_empty() and _tem_insumos() and not _saida_cheia()


func saida_cheia() -> bool:
	return _saida_cheia()


## Um ciclo inteiro na hora, sem tempo nem energia (captador de carga: o raio faz o trabalho). false = não pôde.
func ciclo_agora() -> bool:
	if not pronta():
		return false
	var precisa: Dictionary = receita.get("entradas", {})
	for item in precisa:
		entradas[item] = int(entradas[item]) - int(precisa[item])
	var precisa_f: Dictionary = receita.get("entradas_fluido", {})
	for f in precisa_f:
		fluidos[f] = float(fluidos[f]) - float(precisa_f[f])
	var vai: Dictionary = receita.get("saidas", {})
	for item in vai:
		saidas[item] = int(saidas.get(item, 0)) + int(vai[item])
	produzidos += 1
	_acordar()
	return true


func dormindo() -> bool:
	return _dormindo
