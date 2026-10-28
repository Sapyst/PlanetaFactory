class_name Braco
extends RefCounted
## Braço mecânico: pega do tile de trás e solta no da frente. Ciclo = ida (girar até a origem, descer, pegar)
## + volta (girar até o destino, soltar). Origem/destino são qualquer objeto com a interface:
##   origem:  func pegar_para_braco(filtro: String) -> String   ("" se não tem)
##            ou func pegar_se(aceito: Callable) -> String           (escolhe um item que o destino aceita)
##   destino: func aceita(item: String) -> bool  e  func receber(item: String) -> bool
## O animador lê `fase()` (0..1) e `segurando` para posar o braço.

enum Estado { ESPERANDO_ITEM, INDO_SOLTAR, ESPERANDO_DESTINO, VOLTANDO }

var ciclo_s := 0.83
var origem: Object
var destino: Object
var filtro := ""
var segurando := ""
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
				item = origem.pegar_se(func(i: String) -> bool: return (filtro == "" or i == filtro) and destino.aceita(i))
			elif destino.aceita(_previsto()):
				item = origem.pegar_para_braco(filtro)
			if item != "":
				segurando = item
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
	if destino.receber(segurando):
		segurando = ""
		entregues += 1
		estado = Estado.VOLTANDO
		t = 0.0


func _previsto() -> String:
	return filtro if filtro != "" else "*"
