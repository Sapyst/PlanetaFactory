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
##   _estagio2/_estagio3                    braço 2 telescópico (braço longo: estica no eixo dele)
##   _camisa/_haste                         pistão de elevação da lança (camisa no giro, haste no braço 1)
##   _lanca1.._lanca4/_ponta/_cabo/_carretel/_anel1..  braço quântico: a lança telescópica estica até a origem
##             (`alcance` 1 a 3 tiles: cada seção k anda k·e, a ponta 4e, o cabo estica, o carretel gira, os anéis
##             do rastro aparecem quando a ponta passa); o item voa pelo campo (ponto_garra segue `fase_braco`)
##   _giro/_canhao                          torre (mira `alvo`)
##   _tambor   feixe de canos da metralhadora: gira no eixo dele ("eixo_tambor" em modelos.json) durante a
##             `rajada` (s) que o desenho dos tiros acende; acelera e desacelera
##   _helice   gira no eixo da nacele (turbina eólica; `ritmo` = vento)
##   _nacele   vira devagar até a hélice encarar o vento (`rumo_vento`: para onde o vento sopra, na grade)
## Cristais (P_Cristal) brilham fraco pelo `brilho` (0..1; negativo = segue `ativo`), suavizado.
## Modelo convertido de estudo (arte/estudos/para_jogo.py, "anima" em modelos.json): traz a animação "trabalho"
## (laço de 4 s) num AnimationPlayer; toca em laço enquanto `ativo`, na velocidade de `ritmo`; parada, congela.

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
var rajada := 0.0                   ## metralhadora: segundos de tiro pela frente (o tambor gira enquanto > 0)
var _w_tambor := 0.0
var _a_tambor := 0.0
var _eixo_tambor := Vector3.ZERO
var _brilho := -1.0
var _brilho_posto := -1.0
var _malhas: Array[GeometryInstance3D] = []
var _partes: Dictionary = {}
var _base: Dictionary = {}
var _player: AnimationPlayer = null


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
	for p in dono.find_children("*", "AnimationPlayer", true, false):
		var ap := p as AnimationPlayer
		if ap.has_animation("trabalho"):
			_player = ap
			ap.get_animation("trabalho").loop_mode = Animation.LOOP_LINEAR
			ap.play("trabalho")
			ap.seek(randf() * ap.get_animation("trabalho").length, true)   # cada máquina no seu tempo
			break


func tem(parte: String) -> bool:
	return _partes.has(parte)


func _process(delta: float) -> void:
	var dono := get_parent() as Node3D
	var visivel := dono == null or Visao.dentro(Vector2(dono.global_position.x, -dono.global_position.z), 1.1)
	if _player != null:
		_player.speed_scale = clampf(ritmo, 0.0, 2.0) if ativo and visivel else 0.0   # fora da visão: parada
	if not visivel:
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
	if tem("lanca1"):
		_lanca_quantica(delta)
	# pistões: comprimem e descomprimem em fases alternadas (só trabalhando)
	var k := 0
	while tem("pistao%d" % k):
		var c := 0.5 - 0.5 * cos(t * 5.5 + k * PI) if ativo else 0.0
		_desloca("pistao%d" % k, Vector3(0, -0.15 * c, 0))
		k += 1
	if tem("canhao") and (alvo != null or ponto_alvo != Vector3.INF):
		_mirar()
	if tem("tambor"):
		_girar_tambor(delta)


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
	h += float(_ik.dz)
	var sol := _resolver_telescopico(r, h) if tem("estagio2") else _resolver(r, h)
	var b1: Transform3D = _base["braco1"]
	(_partes["braco1"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, sol.x) * b1.basis, b1.origin)
	var b2: Transform3D = _base["braco2"]
	(_partes["braco2"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, sol.y) * b2.basis, b2.origin)
	if tem("estagio2"):
		# cada estágio corre metade da extensão para a frente do braço 2 (Blender +y = −z local)
		var ext := (float(_ik.l2_atual) - float(_ik.l2)) * 0.5
		for st in ["estagio2", "estagio3"]:
			if tem(st):
				_desloca(st, Vector3(0, 0, -ext))
	if tem("camisa") and tem("haste"):
		# pistão da lança: o olhal da haste anda com o braço 1; camisa e haste miram uma na outra
		var sh: Vector2 = _ik.ombro
		var olhal: Vector2 = _ik.olhal
		var pino: Vector2 = _ik.pino
		var p: Vector2 = sh + (olhal - sh).rotated(sol.x)
		var th := (p - pino).angle() - float(_ik.th0)
		var bc: Transform3D = _base["camisa"]
		(_partes["camisa"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, th) * bc.basis, bc.origin)
		var bh: Transform3D = _base["haste"]
		(_partes["haste"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, th - sol.x) * bh.basis, bh.origin)
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
	_ik.l2_atual = _ik.l2
	# garra do modelo: quanto o pulso desce do alvo (o alvo é a altura do pulso da garra antiga) e onde o item fica
	var g: Dictionary = Registro.modelos.get(modelo, {}).get("garra", {})
	_ik.dz = float(g.get("pulso_dz", 0.0))
	_ik.item = float(g.get("item", 0.06))
	if piv.has("camisa") and piv.has("haste"):
		var pino: Vector2 = piv.camisa
		var olhal: Vector2 = piv.haste
		_ik.pino = pino
		_ik.olhal = olhal
		_ik.th0 = (olhal - pino).angle()


## Braço longo (braço 2 telescópico): a lança deita conforme a distância (85° perto → 15° no alcance de 2 tiles) e o
## braço 2 estica o que falta até o pulso (de l2 recolhido até l2 + 2 estágios de EXT_ESTAGIO).
const EXT_ESTAGIO := 0.40


func _resolver_telescopico(r: float, h: float) -> Vector2:
	var sh: Vector2 = _ik.ombro
	var l1: float = _ik.l1
	var f1 := lerpf(deg_to_rad(85.0), deg_to_rad(15.0), clampf((r - 0.36) / 1.64, 0.0, 1.0))
	var el := sh + Vector2(cos(f1), sin(f1)) * l1
	var v := Vector2(r, h) - el
	_ik.l2_atual = clampf(v.length(), float(_ik.l2), float(_ik.l2) + 2.0 * EXT_ESTAGIO)
	var r1 := f1 - float(_ik.f1)
	var r2abs := v.angle() - float(_ik.f2)
	return Vector2(r1, r2abs - r1)


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


## Braço quântico: extensão atual de cada estágio (m), andando até a do alcance escolhido.
var _ext := -1.0


func _lanca_quantica(delta: float) -> void:
	var q: Dictionary = Registro.modelos.get(modelo, {}).get("lanca", {})
	var emax := float(q.get("emax", 0.5))
	var alvo_e := clampf((alcance - 1.0) / 4.0, 0.0, emax)
	_ext = alvo_e if _ext < 0.0 else move_toward(_ext, alvo_e, delta * 0.4)
	var e := _ext
	for k in range(1, 5):                          # Blender −y (para a origem) = +z local do Godot
		_desloca("lanca%d" % k, Vector3(0, 0, k * e))
	if tem("ponta"):
		_desloca("ponta", Vector3(0, 0, 4.0 * e))
	if tem("cabo"):
		var l0 := float(q.get("cabo_l0", 0.43))
		var bc: Transform3D = _base["cabo"]
		(_partes["cabo"] as Node3D).transform = Transform3D(bc.basis.scaled(Vector3(1, 1, (l0 + 4.0 * e) / l0)), bc.origin)
	if tem("carretel"):
		var br: Transform3D = _base["carretel"]
		(_partes["carretel"] as Node3D).transform = Transform3D(Basis(Vector3.RIGHT, 4.0 * e / 0.056) * br.basis, br.origin)
	var ponta := float(q.get("ponta_y", 1.0)) + 4.0 * e - 0.12
	var aneis: Array = q.get("aneis", [])
	for i in aneis.size():
		var nome := "anel%d" % (i + 1)
		if not tem(nome):
			continue
		var s := clampf((ponta - float(aneis[i])) / 0.12, 0.0, 1.0)
		var n := _partes[nome] as Node3D
		n.visible = s > 0.03
		var ba: Transform3D = _base[nome]
		n.transform = Transform3D(ba.basis.scaled(Vector3.ONE * maxf(s, 0.02)), ba.origin)


## Caminho do item no braço quântico (modelo, Blender: y para a frente/destino, z para cima): sobe da origem pela
## coluna de campo da ponta, corre por cima da lança, desce em curva e pousa no tile da frente.
func _caminho_quantico() -> PackedVector3Array:
	var q: Dictionary = Registro.modelos.get(modelo, {}).get("lanca", {})
	var e := maxf(_ext, 0.0)
	var yp := float(q.get("ponta_y", 1.0)) + 4.0 * e
	var ez := float(q.get("eixo_z", 1.16))
	var zc := float(q.get("fluxo_z", 1.38))
	var zi := 0.24
	var pts := PackedVector3Array([Vector3(0, -yp, zi), Vector3(0, -yp, ez + 0.12), Vector3(0, -yp + 0.1, zc),
			Vector3(0, 0.2, zc), Vector3(0, 0.62, zc - 0.1), Vector3(0, 0.95, zc - 0.45), Vector3(0, 1.0, zi)])
	return pts


## Onde o item fica preso: entre os dedos da garra (mundo); no braço quântico, no campo (pelo caminho do item, conforme
## a fase do ciclo). INF se não é braço.
func ponto_garra() -> Vector3:
	if tem("lanca1"):
		var pts := _caminho_quantico()
		var tot := 0.0
		for i in pts.size() - 1:
			tot += pts[i].distance_to(pts[i + 1])
		var alvo := clampf(fase_braco * 2.0, 0.0, 1.0) * tot
		var p := pts[0]
		for i in pts.size() - 1:
			var l := pts[i].distance_to(pts[i + 1])
			if alvo <= l:
				p = pts[i].lerp(pts[i + 1], alvo / maxf(l, 1e-6))
				break
			alvo -= l
			p = pts[i + 1]
		var dono := get_parent() as Node3D
		var t := dono.global_transform if dono.is_inside_tree() else dono.transform
		return t * Vector3(p.x, p.z, -p.y)
	if not tem("garra"):
		return Vector3.INF
	if _ik.is_empty():
		_preparar_ik()
	return (_partes["garra"] as Node3D).global_transform * Vector3(0, -float(_ik.item), 0)


## Tambor da metralhadora: 10 tiros/s com 6 canos = 10/6 de volta por segundo; sobe em ~0,3 s, para em ~0,6 s.
func _girar_tambor(delta: float) -> void:
	rajada = maxf(0.0, rajada - delta)
	var alvo_w := (10.0 / 6.0) * TAU if rajada > 0.0 else 0.0
	_w_tambor = move_toward(_w_tambor, alvo_w, delta * (35.0 if rajada > 0.0 else 17.5))
	if _w_tambor <= 0.0:
		return
	if _eixo_tambor == Vector3.ZERO:
		var e: Array = Registro.modelos.get(modelo, {}).get("eixo_tambor", [0.0, 1.0, 0.0])
		_eixo_tambor = Vector3(e[0], e[2], -e[1]).normalized()      # Blender → Godot
	_a_tambor = fmod(_a_tambor + _w_tambor * delta, TAU)
	var b: Transform3D = _base["tambor"]
	(_partes["tambor"] as Node3D).transform = Transform3D(Basis(_eixo_tambor, _a_tambor) * b.basis, b.origin)


## Saída das cápsulas da torre no mundo e a velocidade com que a cápsula sai: [pos, vel] (vazio se o modelo não diz).
## modelos.json: "ejecao" = ponto (Blender, com o giro em 0 e o canhão para +Y); "vel_ejecao" = (frente, esquerda,
## cima) em m/s no referencial do canhão.
func ejecao() -> Array:
	var m: Dictionary = Registro.modelos.get(modelo, {})
	if not m.has("ejecao") or not tem("canhao"):
		return []
	var piv := Vector3.ZERO
	for p in m.get("partes", []):
		if p.nome == "canhao":
			piv = Vector3(p.pivo[0], p.pivo[1], p.pivo[2])
	var e: Array = m.ejecao
	var g := _global(_partes["canhao"] as Node3D)
	var pos := g * Vector3(e[0] - piv.x, e[2] - piv.z, -(e[1] - piv.y))
	var v: Array = m.get("vel_ejecao", [0.0, 0.7, 1.5])
	var b := g.basis.orthonormalized()
	var vel := -b.z * float(v[0]) - b.x * float(v[1]) + Vector3.UP * float(v[2])
	return [pos, vel]


## Boca da arma no mundo ("boca" em modelos.json, Blender com o giro em 0), girando com o canhão; INF se não há.
func boca() -> Vector3:
	var m: Dictionary = Registro.modelos.get(modelo, {})
	if not m.has("boca") or not tem("canhao"):
		return Vector3.INF
	var piv := Vector3.ZERO
	for p in m.get("partes", []):
		if p.nome == "canhao":
			piv = Vector3(p.pivo[0], p.pivo[1], p.pivo[2])
	var e: Array = m.boca
	return _global(_partes["canhao"] as Node3D) * Vector3(e[0] - piv.x, e[2] - piv.z, -(e[1] - piv.y))


## Transform no mundo somando os pais (funciona também fora da árvore de cena).
static func _global(n: Node3D) -> Transform3D:
	var t := n.transform
	var p := n.get_parent()
	while p is Node3D:
		t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


func _mirar() -> void:
	var g := _partes["giro"] as Node3D
	var p := g.global_position
	var m := alvo.global_position if alvo != null else ponto_alvo
	var a := atan2(-(m.x - p.x), -(m.z - p.z))
	_gira("giro", a - (get_parent() as Node3D).global_rotation.y)   # giro é local à torre
