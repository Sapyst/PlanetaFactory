class_name Caso
extends RefCounted
## Base dos testes: cada função test_* é chamada pelo executor. Use verificar()/igual()/perto().

var falhas: Array[String] = []
var verificacoes := 0
var _atual := ""


func verificar(cond: bool, msg := "") -> bool:
	verificacoes += 1
	if not cond:
		falhas.append("%s: %s" % [_atual, msg])
	return cond


func igual(a, b, msg := "") -> bool:
	return verificar(a == b, "%s (esperado %s, veio %s)" % [msg, str(b), str(a)])


func perto(a: float, b: float, tol: float, msg := "") -> bool:
	return verificar(absf(a - b) <= tol, "%s (esperado %.4f ± %.4f, veio %.4f)" % [msg, b, tol, a])
