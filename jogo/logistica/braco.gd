class_name Braco
extends RefCounted
## Braço mecânico: pega do tile de trás e solta no da frente. Ciclo = ida (girar até a origem, descer, pegar)
## + volta (girar até o destino, soltar). Origem/destino são qualquer objeto com a interface:
##   origem:  func pegar_para_braco(filtro: String) -> String   ("" se não tem)
##            ou func pegar_se(aceito: Callable) -> String           (escolhe um item que o destino aceita)
##   destino: func aceita(item: String) -> bool  e  func receber(item: String) -> bool
## O animador lê `fase()` (0..1) e `segurando` para posar o braço.
## Braço empilhador (pilha_max 4): na origem pega, de uma vez, até pilha_max itens IGUAIS ao primeiro (os que estão lá
## agora e que o destino aceita); no destino solta um por vez até a garra esvaziar.

enum Estado { ESPERANDO_ITEM, INDO_SOLTAR, ESPERANDO_DESTINO, VOLTANDO }

var ciclo_s := 0.83
var origem: Object
var destino: Object
var filtro := ""
## Itens que o braço pega (vazio = Auto: o que vier). Sempre esperto: só pega o que o destino aceita agora.
var filtros: Array = []
var segurando := ""
var qtd := 0                  ## quantos `segurando` na garra (1; até pilha_max no empilhador)
var pilha_max := 1
var estado := Estado.ESPERANDO_ITEM
var t := 0.0
var energia := 1.0            ## 0..1 (satisfação da rede); 0 = parado
var entregues := 0


func _init(p_ciclo := 0.83) -> void:
	ciclo_s = p_ciclo


## 0 = garra sobre a origem, 0,5 = sobre o destino, 1 = de volta à origem.
func fase() -> float:
	match estado:
		Estado.INDO_SOLTAR: return 0.5 * t / (ciclo_s * 0.5)
		Estado.ESPERANDO_DESTINO: return 0.5
		Estado.VOLTANDO: return 0.5 + 0.5 * t / (ciclo_s * 0.5)
	return 0.0


func tick(dt: float) -> void:
	var passo := dt * energia
	match estado:
		Estado.ESPERANDO_ITEM:
			if origem == null or destino == null:
				return
			var item := ""
			if origem.has_method("pegar_se"):
				# origem escolhe um item que o destino aceita (não pega o que vai ficar preso na garra)
				item = origem.pegar_se(func(i: String) -> bool: return passa(i) and destino.aceita(i))
			elif destino.aceita(_previsto()):
				item = origem.pegar_para_braco(filtro)
			if item != "":
				segurando = item
				qtd = 1
				while qtd < pilha_max:              # empilhador: mais iguais, se já estão na origem
					var mais := ""
					if origem.has_method("pegar_se"):
						mais = origem.pegar_se(func(i: String) -> bool: return i == item)
					else:
						mais = origem.pegar_para_braco(item)
					if mais == "":
						break
					if mais != item:                # origem sem filtro devolveu outro: devolve se der
						if origem.has_method("devolver"):
							origem.devolver(mais)
						break
					qtd += 1
				estado = Estado.INDO_SOLTAR
				t = 0.0
		Estado.INDO_SOLTAR:
			t += passo
			if t >= ciclo_s * 0.5:
				t = ciclo_s * 0.5
				estado = Estado.ESPERANDO_DESTINO
				_tentar_soltar()
		Estado.ESPERANDO_DESTINO:
			_tentar_soltar()
		Estado.VOLTANDO:
			t += passo
			if t >= ciclo_s * 0.5:
				t = 0.0
				estado = Estado.ESPERANDO_ITEM


func _tentar_soltar() -> void:
	if destino == null:            # o que estava na frente saiu com o braço segurando: espera um destino novo
		return
	qtd = maxi(qtd, 1)
	while qtd > 0 and destino.receber(segurando):
		qtd -= 1
		entregues += 1
	if qtd <= 0:
		qtd = 0
		segurando = ""
		estado = Estado.VOLTANDO
		t = 0.0


func passa(i: String) -> bool:
	return filtros.is_empty() or i in filtros


func _previsto() -> String:
	return filtro if filtro != "" else "*"
