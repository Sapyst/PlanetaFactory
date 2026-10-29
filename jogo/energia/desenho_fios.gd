class_name DesenhoFios
extends Node3D
## Desenha as ligações elétricas do mapa: cabo escuro que verga (catenária simples) entre poste ↔ poste e
## poste ↔ máquina; ligação de torre sem fio = feixe ciano tracejado que corre na direção da energia.
## Fita deitada (larga vista de cima, a câmera é quase top-down). Refaz só quando o mapa ou os fios mudam.

const SEGMENTOS := 10
const LARGURA := 0.05

var mapa: MapaOcupacao
var _cabos: MeshInstance3D
var _feixes: MeshInstance3D
var _assinatura := ""


func _ready() -> void:
	_cabos = MeshInstance3D.new()
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.07, 0.07, 0.08)
	m.roughness = 0.6
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	_cabos.material_override = m
	_cabos.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_cabos)
	_feixes = MeshInstance3D.new()
	var sm := ShaderMaterial.new()
	sm.shader = preload("res://energia/feixe.gdshader")
	_feixes.material_override = sm
	_feixes.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_feixes)


func _process(_d: float) -> void:
	if mapa == null:
		return
	var n := 0
	for id in mapa.estruturas:
		n += mapa.estruturas[id].get("fios", []).size()
	var ass := "%d|%d" % [mapa.versao, n]
	if ass == _assinatura:
		return
	_assinatura = ass
	refazer()


func refazer() -> void:
	var cabos := SurfaceTool.new()
	cabos.begin(Mesh.PRIMITIVE_TRIANGLES)
	var feixes := SurfaceTool.new()
	feixes.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tem_cabo := false
	var tem_feixe := false
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		for o in e.get("fios", []):
			if o <= id or not mapa.estruturas.has(o):
				continue
			var f: Dictionary = mapa.estruturas[o]
			var a := Fiacao.ponto_fio(e, Fiacao.centro(f))
			var b := Fiacao.ponto_fio(f, Fiacao.centro(e))
			if Fiacao.liga_sem_cabo(e, f):
				_fita(feixes, a, b, 0.0, 0.10, true)
				tem_feixe = true
			else:
				_fita(cabos, a, b, minf(0.06 * a.distance_to(b), 0.7), LARGURA, false)
				tem_cabo = true
	_cabos.mesh = cabos.commit() if tem_cabo else null
	_feixes.mesh = feixes.commit() if tem_feixe else null


## Fita de a até b em SEGMENTOS pedaços; `flecha` = quanto verga no meio; UV.x = metros ao longo (para o feixe correr).
func _fita(st: SurfaceTool, a: Vector3, b: Vector3, flecha: float, largura: float, uv: bool) -> void:
	var dir := (b - a)
	var lado := Vector3(-dir.z, 0, dir.x).normalized() * largura * 0.5
	if lado.length() < 1e-5:
		lado = Vector3(largura * 0.5, 0, 0)
	var comp := dir.length()
	var pts: Array[Vector3] = []
	for i in SEGMENTOS + 1:
		var t := float(i) / SEGMENTOS
		pts.append(a.lerp(b, t) - Vector3.UP * flecha * 4.0 * t * (1.0 - t))
	for i in SEGMENTOS:
		var p0 := pts[i]
		var p1 := pts[i + 1]
		var u0 := comp * i / SEGMENTOS
		var u1 := comp * (i + 1) / SEGMENTOS
		var v := [[p0 - lado, Vector2(u0, 0)], [p0 + lado, Vector2(u0, 1)], [p1 + lado, Vector2(u1, 1)], [p1 - lado, Vector2(u1, 0)]]
		for k in [0, 1, 2, 0, 2, 3]:
			st.set_normal(Vector3.UP)
			if uv:
				st.set_uv(v[k][1])
			st.add_vertex(v[k][0])
