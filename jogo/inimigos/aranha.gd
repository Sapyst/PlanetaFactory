class_name Aranha
extends Node3D
## Aranha mecânica visível: corpo + 6 pernas (fêmur e tíbia soltos) posadas por MarchaAranha + IK a cada quadro.
## A lógica de passo (e a garantia de não deslizar) está em marcha_aranha.gd, testada em testes/test_aranha.gd.

const CORPO := preload("res://assets/modelos/inimigos/aranha/aranha_corpo.glb")
const FEMUR := preload("res://assets/modelos/inimigos/aranha/aranha_femur.glb")
const TIBIA := preload("res://assets/modelos/inimigos/aranha/aranha_tibia.glb")

var marcha: MarchaAranha
var destino := Vector3.ZERO
var rumo_desejado := 0.0
var atacando := false             ## golpeia com o par da frente (no ar: não conta como pé plantado)
var alvo_golpe := Vector3.ZERO
var _morta := false
var _corpo: Node3D
var _femures: Array[Node3D] = []
var _tibias: Array[Node3D] = []


func _ready() -> void:
	marcha = MarchaAranha.new(global_position, rotation.y)
	destino = global_position
	_corpo = CORPO.instantiate()
	add_child(_corpo)
	Materiais.converter(_corpo)
	for i in 6:
		var f: Node3D = FEMUR.instantiate()
		var t: Node3D = TIBIA.instantiate()
		Materiais.converter(f)
		Materiais.converter(t)
		f.top_level = true
		t.top_level = true
		add_child(f)
		add_child(t)
		_femures.append(f)
		_tibias.append(t)


func ir_para(p: Vector3) -> void:
	destino = p
	var d := p - marcha.posicao
	if Vector2(d.x, d.z).length() > 0.1:
		rumo_desejado = atan2(-d.x, -d.z)


## Encara um ponto (para atacar) sem sair do lugar.
func encarar(p: Vector3) -> void:
	var d := p - marcha.posicao
	if Vector2(d.x, d.z).length() > 0.1:
		rumo_desejado = atan2(-d.x, -d.z)


## Morte: as pernas cedem, o corpo afunda e some (faíscas ficam por conta de quem chamou).
func morrer() -> void:
	if _morta:
		return
	_morta = true
	set_process(false)
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_corpo, "position:y", -0.45, 0.6).set_ease(Tween.EASE_IN)
	tw.tween_property(_corpo, "rotation:z", 0.5, 0.6)
	for n in _femures + _tibias:
		tw.tween_property(n, "global_position:y", 0.05, 0.5)
	tw.chain().tween_callback(queue_free)


func _process(delta: float) -> void:
	marcha.tick(delta, destino, rumo_desejado)
	global_position = marcha.posicao
	rotation.y = marcha.rumo
	# leve sobe-e-desce do corpo enquanto anda
	_corpo.position.y = sin(Time.get_ticks_msec() * 0.012) * 0.02 * minf(marcha.velocidade.length(), 1.0)
	var t := Time.get_ticks_msec() / 1000.0
	for i in 6:
		var q := marcha.quadril(i)
		var pe := marcha.pes[i]
		if atacando and i < 2:
			# golpe: o par da frente sobe e desce alternado na direção do alvo
			var frente := (marcha.base() * Vector3(0, 0, -1)).normalized()
			var lado := (marcha.base() * Vector3(MarchaAranha.QUADRIS[i].x, 0, 0)).normalized()
			var f := 0.5 + 0.5 * sin(t * 13.0 + i * PI)
			pe = Vector3(q.x, 0, q.z) + frente * (0.95 + 0.25 * f) + lado * 0.25 + Vector3.UP * (0.15 + 0.55 * (1.0 - f))
		var ik := MarchaAranha.resolver_ik(q, pe)
		_femures[i].global_transform = _segmento(q, ik.joelho)
		_tibias[i].global_transform = _segmento(ik.joelho, pe)


## Transform de um segmento modelado ao longo de +X com origem na articulação.
static func _segmento(a: Vector3, b: Vector3) -> Transform3D:
	var x := (b - a).normalized()
	var z := x.cross(Vector3.UP)
	if z.length() < 1e-4:
		z = Vector3.BACK
	z = z.normalized()
	var y := z.cross(x).normalized()
	return Transform3D(Basis(x, y, z), a)
