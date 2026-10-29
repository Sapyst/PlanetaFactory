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
##   _helice   gira no eixo da nacele (turbina eólica; `ritmo` = vento)
##   _nacele   vira devagar até a hélice encarar o vento (`rumo_vento`: para onde o vento sopra, na grade)
## Cristais (P_Cristal) brilham fraco pelo `brilho` (0..1; negativo = segue `ativo`), suavizado.

@export var ativo := true
@export var ritmo := 1.0
var fase_braco := 0.0
## Braço: modelo (para ler os pivôs do braço em modelos.json) e onde pegar/soltar — distância (m) e altura do
## pulso em cada ponta (esteira baixa; máquina/baú mais alto). O mundo preenche.
var modelo := ""
var alcance := 1.0
var pega := Vector2(1.0, 0.42)        ## (distância, altura do pulso) na origem
var solta := Vector2(1.0, 0.42)       ## idem no destino
var _ik := {}
var alvo: Node3D = null
var ponto_alvo := Vector3.INF      ## alternativa a `alvo`: mira um ponto do mundo
var tempo := 0.0
var rumo_vento := Vector2.ZERO
var _guinada := INF
var brilho := -1.0
var _brilho := -1.0
var _brilho_posto := -1.0
var _malhas: Array[GeometryInstance3D] = []
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
	for g in dono.find_children("*", "GeometryInstance3D", true, false):
		_malhas.append(g)


func tem(parte: String) -> bool:
	return _partes.has(parte)


func _process(delta: float) -> void:
	var dono := get_parent() as Node3D
	if dono != null and not Visao.dentro(Vector2(dono.global_position.x, -dono.global_position.z), 1.1):
		return                                       # fora do oval de visão: parada (só desenho; a fábrica segue)
	if ativo:
		tempo += delta * ritmo
	var alvo_b := brilho if brilho >= 0.0 else (1.0 if ativo else 0.0)
	_brilho = alvo_b if _brilho < 0.0 else move_toward(_brilho, alvo_b, delta * 1.2)
	if absf(_brilho - _brilho_posto) > 0.01:
		_brilho_posto = _brilho
		for g in _malhas:
			if is_instance_valid(g):
				g.set_instance_shader_parameter("trabalho", _brilho)
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
	if tem("nacele") and rumo_vento.length() > 1e-4:
		# a hélice fica no −Y do Blender (+Z local): +Z tem de apontar para de onde o vento vem (mundo = (−x, +y da grade))
		var alvo_g := atan2(-rumo_vento.x, rumo_vento.y) - (get_parent() as Node3D).global_rotation.y
		_guinada = alvo_g if _guinada == INF else rotate_toward(_guinada, alvo_g, delta * 0.35)
		_gira("nacele", _guinada)
	if tem("helice"):
		var b: Transform3D = _base["helice"]
		(_partes["helice"] as Node3D).transform = Transform3D(Basis(Vector3(0, 0, 1), t * 3.0) * b.basis, b.origin)
	if tem("cabecote"):
		_desloca("cabecote", Vector3(0, absf(sin(t * 4.0)) * 0.10 if ativo else 0.0, 0))
	if tem("braco") and not tem("braco1"):
		_gira("braco", sin(t * 1.7) * 0.9)
	if tem("braco1"):
		_braco_mecanico()
	# pistões: comprimem e descomprimem em fases alternadas (só trabalhando)
	var k := 0
	while tem("pistao%d" % k):
		var c := 0.5 - 0.5 * cos(t * 5.5 + k * PI) if ativo else 0.0
		_desloca("pistao%d" % k, Vector3(0, -0.15 * c, 0))
		k += 1
	if tem("canhao") and (alvo != null or ponto_alvo != Vector3.INF):
		_mirar()


func _desloca(parte: String, d: Vector3) -> void:
	var b: Transform3D = _base[parte]
	(_partes[parte] as Node3D).transform = Transform3D(b.basis, b.origin + d)


func _gira(parte: String, ang: float) -> void:
	var b: Transform3D = _base[parte]
	(_partes[parte] as Node3D).transform = Transform3D(Basis(Vector3.UP, ang) * b.basis, b.origin)


## Braço mecânico com cinemática inversa de 2 elos: a garra vai de verdade até o item — desce, pega, sobe, gira
## meia volta, desce e solta no destino, sobe e volta. fase 0 = garra na origem (atrás), 0,5 = no destino.
func _braco_mecanico() -> void:
	if _ik.is_empty():
		_preparar_ik()
	var f := fase_braco
	var ida := f < 0.5
	var x := (f if ida else f - 0.5) * 2.0
	var de: Vector2 = pega if ida else solta
	var para: Vector2 = solta if ida else pega
	var alto := maxf(de.y, para.y) + 0.2
	var sobe := smoothstep(0.0, 0.2, x)
	var desce := smoothstep(0.8, 1.0, x)
	var gira := smoothstep(0.15, 0.85, x)
	var h := lerpf(de.y, alto, sobe) if x < 0.5 else lerpf(alto, para.y, desce)
	var r := lerpf(de.x, para.x, gira)
	# giro: origem fica atrás (π), destino na frente (0); a volta desfaz o mesmo caminho
	var ang := PI * (1.0 - gira) if ida else PI * gira
	_gira("giro", ang)
	var sol := _resolver(r, h)
	var b1: Transform3D = _base["braco1"]
	(_partes["braco1"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, sol.x) * b1.basis, b1.origin)
	var b2: Transform3D = _base["braco2"]
	(_partes["braco2"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, sol.y) * b2.basis, b2.origin)
	if tem("garra"):
		var bg: Transform3D = _base["garra"]
		(_partes["garra"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, -(sol.x + sol.y)) * bg.basis, bg.origin)


## Pivôs do modelo (Blender: y = frente, z = cima): ombro, cotovelo, pulso → comprimentos e ângulos de repouso.
func _preparar_ik() -> void:
	var piv := {}
	for p in Registro.modelos.get(modelo, {}).get("partes", []):
		piv[p.nome] = Vector2(float(p.pivo[1]), float(p.pivo[2]))
	var sh: Vector2 = piv.get("braco1", Vector2(0, 0.36))
	var el: Vector2 = piv.get("braco2", Vector2(0.1, 0.66))
	var wr: Vector2 = piv.get("garra", Vector2(0.3, 0.32))
	_ik = {"ombro": sh, "l1": (el - sh).length(), "l2": (wr - el).length(), "f1": (el - sh).angle(), "f2": (wr - el).angle()}


## Ângulos (rot. do elo 1, rot. relativa do elo 2) para o pulso ir a (distância, altura); cotovelo para cima.
func _resolver(r: float, h: float) -> Vector2:
	var t := Vector2(r, h) - (_ik.ombro as Vector2)
	var l1: float = _ik.l1
	var l2: float = _ik.l2
	var d := clampf(t.length(), absf(l1 - l2) + 0.01, l1 + l2 - 0.005)
	var a1 := t.angle() + acos(clampf((l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d), -1.0, 1.0))
	var a2 := a1 - (PI - acos(clampf((l1 * l1 + l2 * l2 - d * d) / (2.0 * l1 * l2), -1.0, 1.0)))
	var r1 := a1 - float(_ik.f1)
	var r2abs := a2 - float(_ik.f2)
	return Vector2(r1, r2abs - r1)


## Onde o item fica preso: entre os dedos da garra (mundo). INF se não é braço.
func ponto_garra() -> Vector3:
	if not tem("garra"):
		return Vector3.INF
	return (_partes["garra"] as Node3D).global_transform * Vector3(0, -0.06, 0)


func _mirar() -> void:
	var g := _partes["giro"] as Node3D
	var p := g.global_position
	var m := alvo.global_position if alvo != null else ponto_alvo
	var a := atan2(-(m.x - p.x), -(m.z - p.z))
	_gira("giro", a - (get_parent() as Node3D).global_rotation.y)   # giro é local à torre
