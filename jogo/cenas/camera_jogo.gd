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

var alvo := Vector3(8, 0, -1)
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
		alvo += Vector3(v.x, 0, v.y).limit_length(1.0).rotated(Vector3.UP, angulo) * distancia * VEL_TECLADO * delta
		posicionar()


## Inclinação (rad) para a distância atual — interpolada em escala log (o zoom é multiplicativo).
func inclinacao() -> float:
	var t := clampf(log(distancia / DIST_MIN) / log(DIST_MAX / DIST_MIN), 0.0, 1.0)
	return deg_to_rad(lerpf(INCL_PERTO, INCL_LONGE, t))


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
	alvo += Vector3(-r.x, 0, -r.y).rotated(Vector3.UP, angulo)
	posicionar()


func zoom(fator: float) -> void:
	distancia = clampf(distancia * fator, DIST_MIN, DIST_MAX)
	posicionar()


func girar(d: float) -> void:
	angulo += d
	posicionar()


## Ponto do chão (y = 0) sob a posição de tela; Vector3.INF se o raio não bate no chão.
func no_chao(tela: Vector2) -> Vector3:
	var o := project_ray_origin(tela)
	var n := project_ray_normal(tela)
	if absf(n.y) < 1e-4:
		return Vector3.INF
	var t := -o.y / n.y
	return o + n * t if t > 0.0 else Vector3.INF
