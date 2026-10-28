class_name RelogioSim
extends RefCounted
## Passo fixo da simulação, independente do FPS. A tela interpola com `fracao()`.
## Celular pode usar menos ticks por segundo sem mudar o resultado por segundo de jogo.

var ticks_por_segundo := 30
var acumulado := 0.0
var tick_atual := 0
var max_ticks_por_quadro := 8   ## evita a espiral da morte quando o aparelho engasga


func dt() -> float:
	return 1.0 / ticks_por_segundo


## Devolve quantos ticks rodar neste quadro.
func avancar(delta: float) -> int:
	acumulado += delta
	var n := int(acumulado / dt())
	if n > max_ticks_por_quadro:
		n = max_ticks_por_quadro
		acumulado = 0.0
	else:
		acumulado -= n * dt()
	tick_atual += n
	return n


func fracao() -> float:
	return acumulado / dt()
