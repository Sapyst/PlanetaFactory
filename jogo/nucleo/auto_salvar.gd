class_name AutoSalvar
extends RefCounted
## Relógio do salvar automático, em tempo real (acelerar o jogo não salva mais vezes; a pausa não chama). Só decide
## quando: quem grava é o mundo.

var _falta := INF


## Chamar a cada quadro. intervalo em segundos (0 = desligado). `pode` falso (abertura, derrota) segura o salvamento,
## que sai assim que puder. true = é a hora, e a contagem recomeça.
func avancar(dt: float, intervalo: float, pode: bool) -> bool:
	if intervalo <= 0.0:
		_falta = INF
		return false
	_falta = minf(_falta, intervalo) - dt      # encurtou na configuração: vale o novo; religou: conta do zero
	if _falta > 0.0 or not pode:
		return false
	_falta = intervalo
	return true
