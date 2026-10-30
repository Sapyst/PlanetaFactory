class_name DesenhoFarol
extends Node3D
## Luz dos faróis de cristal (Farol) à noite: uma luz âmbar de 10 m em cada farol aceso — os mais perto do centro da
## vista (limite fixo de luzes, reaproveitadas). A força segue `Farol.forca` (escuro e energia) e pisca de leve como
## a lâmpada do estudo. Só lê o Farol.

const MAX_LUZES := 8
const COR := Color(1.0, 0.72, 0.30)
const ALTURA := 2.6                   ## m acima do chão (a gaiola do cristal no alto da torre)

var farol: Farol
var _luzes: Array[OmniLight3D] = []
var _t := 0.0


func _criar_luzes() -> void:
	for i in MAX_LUZES:
		var l := OmniLight3D.new()
		l.light_color = COR
		l.omni_attenuation = 1.4
		l.shadow_enabled = false
		l.visible = false
		add_child(l)
		_luzes.append(l)


func _process(delta: float) -> void:
	if farol == null:
		return
	if _luzes.is_empty():
		_criar_luzes()
	_t += delta
	var lista: Array = []
	for id in farol.acesos():
		var c := farol.centro(id)
		lista.append([c.distance_squared_to(Visao.centro), id, c])
	lista.sort()
	for i in MAX_LUZES:
		var l := _luzes[i]
		if i >= lista.size():
			l.visible = false
			continue
		var id: int = lista[i][1]
		l.visible = true
		l.position = Grade.ponto_mundo(lista[i][2], ALTURA)         # o desenho fica na origem do mundo
		l.omni_range = farol.raio(id)
		l.light_energy = 2.2 * farol.forca(id) * (0.92 + 0.08 * sin(_t * 5.0 + id))


## Quantas luzes estão acesas agora (testes e roteiro).
func acesas() -> int:
	return _luzes.filter(func(l: OmniLight3D): return l.visible).size()
