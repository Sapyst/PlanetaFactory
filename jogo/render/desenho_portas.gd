class_name DesenhoPortas
extends Node3D
## Aviso de porta solta nas estruturas já construídas: onde uma entrada ou saída de item/fluido não tem nada ligado
## (esteira, cano, braço, baú ou outra máquina), uma placa pulsa sobre a porta — "falta entrada" (vermelho) ou
## "falta saída" (âmbar). Refaz quando o mapa muda (mapa.versao) e mostra só o que está no oval de visão.

const COR_ENT := Color(1.0, 0.32, 0.26)
const COR_SAI := Color(1.0, 0.72, 0.2)

var mapa: MapaOcupacao
var _versao := -1
var _t := 0.0
var _avisos: Array[Dictionary] = []      ## {pos: Vector3, io}
var _placas: Array[Label3D] = []


func _process(delta: float) -> void:
	if mapa == null:
		return
	_t -= delta
	if mapa.versao != _versao or _t <= 0.0:
		_versao = mapa.versao
		_t = 1.5
		_refazer()
	var brilho := 0.65 + 0.35 * sin(Time.get_ticks_msec() / 1000.0 * 4.0)
	var n := 0
	for a in _avisos:
		if not Visao.dentro(Vector2(a.pos.x, -a.pos.z), 1.0):
			continue
		var p := _placa(n)
		n += 1
		p.position = a.pos
		p.text = "▼ falta entrada" if a.io == "ENT" else "▲ falta saída"
		var c: Color = COR_ENT if a.io == "ENT" else COR_SAI
		p.modulate = Color(c, brilho)
		p.visible = true
	for i in range(n, _placas.size()):
		_placas[i].visible = false


func _refazer() -> void:
	_avisos.clear()
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if not Portas.mostra_aviso(e.nome) or Registro.modelos.get(e.nome, {}).get("portas", []).is_empty():
			continue
		for s in Portas.soltas(mapa, id):
			var p2: Vector2 = s.pos - Vector2(s.dir) * 0.15
			_avisos.append({"pos": Grade.ponto_mundo(p2, s.z + 0.55), "io": s.io})


func _placa(i: int) -> Label3D:
	while _placas.size() <= i:
		var l := Label3D.new()
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.fixed_size = true
		l.pixel_size = 0.0011
		l.font_size = 30
		l.outline_size = 10
		l.outline_modulate = Color(0, 0, 0, 0.85)
		l.render_priority = 5
		add_child(l)
		_placas.append(l)
	return _placas[i]
