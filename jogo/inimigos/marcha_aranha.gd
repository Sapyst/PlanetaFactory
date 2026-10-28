class_name MarchaAranha
extends RefCounted
## Marcha procedural da aranha mecânica (6 pernas, trípode alternado). Lógica pura, sem nós — testável.
##
## Por que não desliza: um pé PLANTADO nunca muda de posição no mundo. Só o pé em passo (no ar) se move.
## O corpo anda; quando os pés de um trípode ficam longe demais da posição de repouso, o trípode inteiro
## levanta e pousa ADIANTE (previsão pela velocidade), enquanto o outro trípode segura o corpo.
## Pernas não embaralham: cada pé só mira a própria "casa" (quadril + direção radial) e os trípodes nunca
## estão no ar ao mesmo tempo. A IK de 2 ossos (joelho para cima) dá a pose de cada perna.
##
## Medidas iguais às do modelo (arte/blender_scripts/inimigos.py).

const QUADRIL_Z := 0.55
const FEMUR := 0.70
const TIBIA := 0.90
const QUADRIS: Array[Vector2] = [Vector2(0.42, 0.35), Vector2(-0.42, 0.35), Vector2(0.42, 0.0),
								 Vector2(-0.42, 0.0), Vector2(0.42, -0.35), Vector2(-0.42, -0.35)]   ## (x, frente) no corpo
const TRIPODES := [[0, 3, 4], [1, 2, 5]]
const ALCANCE_REPOUSO := 1.0     ## distância horizontal quadril → pé em repouso
const LIMIAR_PASSO := 0.30       ## m de afastamento da casa que dispara o passo
const DURACAO_PASSO := 0.22      ## s
const ALTURA_PASSO := 0.25       ## m
const VEL_MAX := 1.6             ## m/s: acima disso o passo não acompanha
const ATRASO_FREIO := 0.55       ## m: pé plantado tão atrás da casa faz o corpo frear (garante alcance da IK)

var posicao := Vector3.ZERO      ## corpo no chão (y = 0); o corpo desenhado fica em y = QUADRIL_Z
var rumo := 0.0                  ## rad em torno de +Y; frente = −Z rotacionado
var velocidade := Vector3.ZERO
var pes: Array[Vector3] = []
var plantado: Array[bool] = []
var _ini: Array[Vector3] = []
var _alvo: Array[Vector3] = []
var _t_passo := 0.0
var _no_ar := -1                 ## índice do trípode no ar (−1 = todos no chão)


func _init(pos := Vector3.ZERO, p_rumo := 0.0) -> void:
	posicao = pos
	rumo = p_rumo
	for i in 6:
		pes.append(casa(i))
		plantado.append(true)
		_ini.append(Vector3.ZERO)
		_alvo.append(Vector3.ZERO)


func base() -> Basis:
	return Basis(Vector3.UP, rumo)


## Quadril no mundo.
func quadril(i: int) -> Vector3:
	var q := QUADRIS[i]
	return posicao + base() * Vector3(q.x, QUADRIL_Z, -q.y)


## Onde o pé i gosta de ficar (no chão), para o corpo na pose atual.
func casa(i: int) -> Vector3:
	var q := QUADRIS[i]
	var radial := Vector3(q.x, 0, -q.y).normalized()
	return posicao + base() * (Vector3(q.x, 0, -q.y) + radial * ALCANCE_REPOUSO)


## Avança a marcha. `nova_pos`/`novo_rumo` = para onde a IA quer levar o corpo neste passo.
func tick(dt: float, nova_pos: Vector3, novo_rumo: float) -> void:
	var d := nova_pos - posicao
	var vmax := VEL_MAX * dt
	if _atraso_max() > ATRASO_FREIO:
		vmax *= 0.25                               # freia: espera as pernas alcançarem
	if d.length() > vmax:
		d = d.normalized() * vmax
	velocidade = d / dt if dt > 0 else Vector3.ZERO
	posicao += d
	rumo = rotate_toward(rumo, novo_rumo, 2.5 * dt)
	if _no_ar >= 0:
		_t_passo += dt / DURACAO_PASSO
		var f := minf(_t_passo, 1.0)
		var s := f * f * (3.0 - 2.0 * f)          # suave para pousar sem tranco
		for i in TRIPODES[_no_ar]:
			var p := _ini[i].lerp(_alvo[i], s)
			p.y = sin(f * PI) * ALTURA_PASSO
			pes[i] = p
		if _t_passo >= 1.0:
			for i in TRIPODES[_no_ar]:
				pes[i] = _alvo[i]
				pes[i].y = 0.0
				plantado[i] = true
			_no_ar = -1
	if _no_ar < 0:
		# levanta o trípode mais afastado da casa (não alterna às cegas)
		var a := _afastamento(0)
		var b := _afastamento(1)
		var tri := 0 if a >= b else 1
		var pior := maxf(a, b)
		var giro := absf(angle_difference(rumo, novo_rumo))
		var parado := velocidade.length() < 0.05
		if pior > LIMIAR_PASSO or (pior > 0.08 and giro > 0.05) or (parado and pior > 0.06):
			_comecar_passo(tri)


func _afastamento(tri: int) -> float:
	var pior := 0.0
	for i in TRIPODES[tri]:
		pior = maxf(pior, Vector2(pes[i].x - casa(i).x, pes[i].z - casa(i).z).length())
	return pior


func _atraso_max() -> float:
	var m := 0.0
	for i in 6:
		if plantado[i]:
			m = maxf(m, Vector2(pes[i].x - casa(i).x, pes[i].z - casa(i).z).length())
	return m


func _comecar_passo(tri: int) -> void:
	_no_ar = tri
	_t_passo = 0.0
	for i in TRIPODES[tri]:
		plantado[i] = false
		_ini[i] = pes[i]
		_alvo[i] = casa(i) + velocidade * DURACAO_PASSO * 1.2   # pousa um pouco à frente da casa
		_alvo[i].y = 0.0


func pes_no_chao() -> int:
	var n := 0
	for p in plantado:
		if p: n += 1
	return n


## IK de 2 ossos no plano vertical que contém quadril e pé, joelho para cima.
## Devolve {joelho: Vector3, alcancou: bool}.
static func resolver_ik(q: Vector3, pe: Vector3) -> Dictionary:
	var alvo := pe - q
	var dist := alvo.length()
	var max_d := FEMUR + TIBIA - 0.001
	var alcancou := dist <= max_d and dist >= absf(FEMUR - TIBIA)
	dist = clampf(dist, absf(FEMUR - TIBIA) + 0.001, max_d)
	var horiz := Vector3(alvo.x, 0, alvo.z)
	var dh := horiz.normalized() if horiz.length() > 1e-6 else Vector3.RIGHT
	var cos_a := clampf((FEMUR * FEMUR + dist * dist - TIBIA * TIBIA) / (2.0 * FEMUR * dist), -1.0, 1.0)
	var elev := atan2(alvo.y, horiz.length()) + acos(cos_a)
	var joelho := q + dh * FEMUR * cos(elev) + Vector3.UP * FEMUR * sin(elev)
	return {"joelho": joelho, "alcancou": alcancou}
