class_name Animador
extends Node
## Anima as peças móveis de uma estrutura pelo NOME das partes exportadas da arte
## (<modelo>_<parte>, ver "partes" em modelos.json). Não sabe de regra de jogo: quem manda é `ativo`,
## `ritmo` (0..1, ex.: energia) e, nos braços, `fase_braco` (Braco.fase()).
##
##   _hastes   sobe/desce (extrator)        _rotor    gira em Y (broca)
##   _cristal  pulsa em escala (extrator)   _braco    vai e volta em Y (montadora)
##   _antena   gira (laboratório)           _cabecote sobe/desce (bomba)
##   _giro/_braco1/_braco2/_garra           braço mecânico (pega atrás, solta na frente)
##   _giro/_canhao                          torre (mira `alvo`)

@export var ativo := true
@export var ritmo := 1.0
var fase_braco := 0.0
var alvo: Node3D = null
var ponto_alvo := Vector3.INF      ## alternativa a `alvo`: mira um ponto do mundo
var tempo := 0.0
var _partes: Dictionary = {}
var _base: Dictionary = {}


func _ready() -> void:
	var dono := get_parent()
	for n in dono.find_children("*", "Node3D", true, false):
		var nome: String = n.name
		var i := nome.rfind("_")
		if i > 0:
			var parte := nome.substr(i + 1)
			_partes[parte] = n
			_base[parte] = (n as Node3D).transform


func tem(parte: String) -> bool:
	return _partes.has(parte)


func _process(delta: float) -> void:
	if ativo:
		tempo += delta * ritmo
	var t := tempo
	if tem("hastes"):
		_desloca("hastes", Vector3(0, (sin(t * 6.0) * 0.5 + 0.5) * 0.18 if ativo else 0.0, 0))
	if tem("cristal"):
		var s := 1.0 + (0.06 * sin(t * 3.0) if ativo else 0.0)
		(_partes["cristal"] as Node3D).transform = _base["cristal"].scaled_local(Vector3(s, s, s))
	if tem("rotor"):
		_gira("rotor", t * 2.5)
	if tem("antena"):
		_gira("antena", t * 0.8)
	if tem("cabecote"):
		_desloca("cabecote", Vector3(0, absf(sin(t * 4.0)) * 0.10 if ativo else 0.0, 0))
	if tem("braco") and not tem("braco1"):
		_gira("braco", sin(t * 1.7) * 0.9)
	if tem("braco1"):
		_braco_mecanico()
	if tem("canhao") and (alvo != null or ponto_alvo != Vector3.INF):
		_mirar()


func _desloca(parte: String, d: Vector3) -> void:
	var b: Transform3D = _base[parte]
	(_partes[parte] as Node3D).transform = Transform3D(b.basis, b.origin + d)


func _gira(parte: String, ang: float) -> void:
	var b: Transform3D = _base[parte]
	(_partes[parte] as Node3D).transform = Transform3D(Basis(Vector3.UP, ang) * b.basis, b.origin)


## fase 0 = garra no tile de trás (sul = +Z local), 0,5 = no da frente (norte = −Z local), 1 = volta.
func _braco_mecanico() -> void:
	var f := fase_braco
	var giro := PI * (1.0 - absf(1.0 - 2.0 * f))     # 0 → π → 0 (meia-volta e retorno)
	_gira("giro", giro + PI)                           # repouso virado para trás (onde pega)
	var mergulho := pow(cos(f * TAU), 8.0)             # desce a garra nos extremos (pegar/soltar)
	var b1: Transform3D = _base["braco1"]
	(_partes["braco1"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, -0.35 * mergulho) * b1.basis, b1.origin)
	var b2: Transform3D = _base["braco2"]
	(_partes["braco2"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, -0.45 * mergulho) * b2.basis, b2.origin)


func _mirar() -> void:
	var g := _partes["giro"] as Node3D
	var p := g.global_position
	var m := alvo.global_position if alvo != null else ponto_alvo
	var a := atan2(-(m.x - p.x), -(m.z - p.z))
	_gira("giro", a - (get_parent() as Node3D).global_rotation.y)   # giro é local à torre
