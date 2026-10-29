class_name Visao
extends RefCounted
## Oval de visão: a área que a tela mostra, vista como um oval deitado no chão (eixo maior = horizontal da tela),
## centrado no ponto olhado e do tamanho do zoom. Dentro, tudo desenha e anima; na borda, degradê; fora, o mundo
## escurece (névoa) e os desenhos se simplificam: sem grama, objetos miúdos, animações e efeitos. A simulação não
## muda — é só desenho. O mundo atualiza a cada quadro (atualizar); quem desenha pergunta `dentro`.
## Desligada (testes, ferramentas) = tudo dentro.

const BORDA_INI := 0.78                ## degradê da borda (em raios do oval)
const BORDA_FIM := 1.05

static var ativa := false
static var centro := Vector2.ZERO      ## grade
static var eixo := Vector2.RIGHT       ## horizontal da tela no chão (grade, unitário)
static var rx := 1.0e6
static var rz := 1.0e6


static func atualizar(cam: Camera3D, distancia: float, inclinacao: float, alvo: Vector3) -> void:
	var vp := cam.get_viewport().get_visible_rect().size
	var aspecto := vp.x / maxf(vp.y, 1.0)
	var meio := distancia * tan(deg_to_rad(cam.fov) / 2.0)
	centro = Vector2(alvo.x, -alvo.z)
	var dx := cam.global_basis.x
	eixo = Vector2(dx.x, -dx.z).normalized() if Vector2(dx.x, dx.z).length() > 1e-4 else Vector2.RIGHT
	rx = meio * aspecto * 1.02
	rz = meio / maxf(sin(inclinacao), 0.3) * 1.02
	ativa = true


## Distância "em raios do oval": 0 no centro, 1 na borda.
static func e(p: Vector2) -> float:
	if not ativa:
		return 0.0
	var d := p - centro
	return Vector2(d.dot(eixo) / rx, d.dot(Vector2(-eixo.y, eixo.x)) / rz).length()


static func dentro(p: Vector2, margem := 1.0) -> bool:
	return e(p) <= margem


## Retângulo (grade) que encosta no oval (com margem, em raios).
static func toca(r: Rect2, margem := 1.0) -> bool:
	if not ativa:
		return true
	var raio_ret := r.size.length() * 0.5
	return e(r.get_center()) - raio_ret / minf(rx, rz) <= margem
