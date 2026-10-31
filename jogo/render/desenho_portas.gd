class_name DesenhoPortas
extends Node3D
## Aviso de porta solta nas estruturas já construídas: onde uma entrada ou saída de item/fluido não tem nada ligado,
## um marcador de listras vermelhas pintado no chão, no tile exato da porta, com a seta do sentido do fluxo (MarcadorPortas).
## Atendida (esteira, cano, braço por qualquer lado, baú ou outra máquina), some. Quem decide é Portas.soltas. Refaz quando o mapa
## muda (mapa.versao) e a cada 1,5 s; o corte do oval de visão e o pulso são do shader, sem custo por quadro aqui.

var mapa: MapaOcupacao
var _versao := -1
var _t := 0.0
var _marcador: MarcadorPortas


func _ready() -> void:
	_marcador = MarcadorPortas.new()
	add_child(_marcador)


func _process(delta: float) -> void:
	if mapa == null:
		return
	_t -= delta
	if mapa.versao != _versao or _t <= 0.0:
		_versao = mapa.versao
		_t = 1.5
		_marcador.definir(avisos(mapa))


## Portas soltas de todas as estruturas, prontas para o marcador.
static func avisos(m: MapaOcupacao) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for id in m.estruturas:
		out.append_array(Portas.soltas(m, id))
	return out
