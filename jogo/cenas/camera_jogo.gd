class_name CameraJogo
extends Camera3D
## Câmera de cima, olhando um ponto do chão. Quem decide QUANDO mover é o ControleConstrucao (ele separa
## gesto de construção de gesto de câmera); aqui só fica o "como": arrastar, zoom, girar, WASD e raio no chão.
##
## Ângulo entre o isométrico e o top-down: a inclinação vai de 56° (zoom perto: dá para ver a lateral das peças)
## a 74° (zoom longe: quase de cima, lê o mapa como planta). Lente fechada (FOV 38°) achata a perspectiva.

const DIST_MIN := 8.0
const DIST_MAX := 150.0
const DIST_PADRAO := 44.0
const INCL_PERTO := 56.0      ## graus acima do horizonte
const INCL_LONGE := 74.0
const FOV := 38.0
const VEL_TECLADO := 1.2      ## fração da distância por segundo

## Ponto olhado. Atribuir `alvo` pula direto (roteiros, carregar); o dedo/mouse mexe em `destino` e a câmera
## desliza até lá (suave mesmo quando o toque chega em menos quadros que a tela), com inércia ao soltar.
var alvo := Vector3(8, 0, -1):
	set(v):
		alvo = v
		destino = v
		_vel = Vector3.ZERO
var destino := Vector3(8, 0, -1)
var _vel := Vector3.ZERO              ## m/s do arrasto (para a inércia)
var _ultimo_arrasto := 0
var _quadro_arrasto := 0
var segurando := false                ## dedo na tela: sem inércia (em quadro lento ela entrava entre dois arrastos)
var distancia := DIST_PADRAO
var angulo := 0.6


func _ready() -> void:
	fov = FOV
	far = 600.0
	posicionar()


func _process(delta: float) -> void:
	var v := Vector2(Input.get_axis("ui_left", "ui_right"), Input.get_axis("ui_up", "ui_down"))
	if Input.is_physical_key_pressed(KEY_A): v.x -= 1
	if Input.is_physical_key_pressed(KEY_D): v.x += 1
	if Input.is_physical_key_pressed(KEY_W): v.y -= 1
	if Input.is_physical_key_pressed(KEY_S): v.y += 1
	# zoom pelo teclado: + / − (segurar)
	if Input.is_physical_key_pressed(KEY_EQUAL) or Input.is_physical_key_pressed(KEY_KP_ADD): zoom(1.0 - 1.5 * delta)
	if Input.is_physical_key_pressed(KEY_MINUS) or Input.is_physical_key_pressed(KEY_KP_SUBTRACT): zoom(1.0 + 1.5 * delta)
	if v != Vector2.ZERO:
		destino += Vector3(v.x, 0, v.y).limit_length(1.0).rotated(Vector3.UP, angulo) * distancia * VEL_TECLADO * delta
	# inércia: soltou o dedo com a câmera em movimento → continua e freia
	if not segurando and Time.get_ticks_msec() - _ultimo_arrasto > 60 and _vel.length() > 0.05:
		destino += _vel * delta
		_vel *= exp(-4.5 * delta)
	if alvo.distance_squared_to(destino) > 1e-6:
		var a := destino - alvo
		_suave(alvo + a * (1.0 - exp(-20.0 * delta)))


## Inclinação (rad) para a distância atual — interpolada em escala log (o zoom é multiplicativo).
func inclinacao() -> float:
	var t := clampf(log(distancia / DIST_MIN) / log(DIST_MAX / DIST_MIN), 0.0, 1.0)
	return deg_to_rad(lerpf(INCL_PERTO, INCL_LONGE, t))


func _suave(p: Vector3) -> void:
	var d := destino
	var v := _vel
	alvo = p                              # o setter zera destino/vel: devolve
	destino = d
	_vel = v
	posicionar()


func posicionar() -> void:
	var el := inclinacao()
	var dir := Vector3(sin(angulo) * cos(el), sin(el), cos(angulo) * cos(el))
	position = alvo + dir * distancia
	look_at(alvo)


## Arrastar o mundo junto com o dedo/mouse (pixels de tela).
func arrastar(rel: Vector2) -> void:
	# metros por pixel no centro da tela: o chão acompanha o dedo em qualquer zoom
	var mpp := 2.0 * distancia * tan(deg_to_rad(fov) / 2.0) / maxf(get_viewport().get_visible_rect().size.y, 1.0)
	var r := rel * mpp
	r.y /= sin(inclinacao())                # no eixo da profundidade o chão aparece encurtado
	var passo := Vector3(-r.x, 0, -r.y).rotated(Vector3.UP, angulo)
	destino += passo
	var agora := Time.get_ticks_msec()
	var dt := maxf((agora - _ultimo_arrasto) / 1000.0, 1.0 / 120.0)
	_vel = _vel.lerp(passo / dt, 0.5) if dt < 0.1 else Vector3.ZERO
	_ultimo_arrasto = agora


func zoom(fator: float) -> void:
	distancia = clampf(distancia * fator, DIST_MIN, DIST_MAX)
	posicionar()


## Toque: arrasta o chão preso embaixo do dedo (o ponto que estava sob `de` fica sob `para`), sem atraso.
func arrastar_tela(de: Vector2, para: Vector2) -> void:
	var a := no_chao(de)
	var b := no_chao(para)
	if a == Vector3.INF or b == Vector3.INF:
		arrastar(para - de)
		return
	var passo := Vector3(a.x - b.x, 0, a.z - b.z)
	destino += passo
	var agora := Time.get_ticks_msec()
	var dt := maxf((agora - _ultimo_arrasto) / 1000.0, 1.0 / 120.0)
	_vel = _vel.lerp(passo / dt, 0.5) if dt < 0.1 else Vector3.ZERO
	_ultimo_arrasto = agora
	_quadro_arrasto = Engine.get_process_frames()
	_suave(destino)                       # no dedo, a câmera vai junto na hora (a suavização é para o teclado)


## Dedo saiu da tela: se estava parado antes de soltar, sem embalo.
func soltar() -> void:
	segurando = false
	if Time.get_ticks_msec() - _ultimo_arrasto > 60 or Engine.get_process_frames() - _quadro_arrasto > 2:
		_vel = Vector3.ZERO


## Pinça: zoom em volta do ponto entre os dedos (o que está ali fica ali).
func zoom_em(fator: float, tela: Vector2) -> void:
	var antes := no_chao(tela)
	zoom(fator)
	var depois := no_chao(tela)
	if antes != Vector3.INF and depois != Vector3.INF:
		destino += Vector3(antes.x - depois.x, 0, antes.z - depois.z)
		_suave(destino)
	_vel = Vector3.ZERO


func girar(d: float) -> void:
	angulo += d
	posicionar()


## Ponto do chão sob a posição de tela (no relevo: acerta o plano do nível do tile em poucas voltas);
## Vector3.INF se o raio não bate no chão.
func no_chao(tela: Vector2) -> Vector3:
	var o := project_ray_origin(tela)
	var n := project_ray_normal(tela)
	if absf(n.y) < 1e-4:
		return Vector3.INF
	var h := 0.0
	var p := Vector3.INF
	for i in 4:
		var t := (h - o.y) / n.y
		if t <= 0.0:
			return Vector3.INF
		p = o + n * t
		var h2 := Grade.altura_em(Vector2(p.x, -p.z))
		if is_equal_approx(h2, h):
			break
		h = h2
	return p
