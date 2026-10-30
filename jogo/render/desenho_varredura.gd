class_name DesenhoVarredura
extends Node3D
## Marcas do sensor de varredura (Varredura) no mapa: cada ninho marcado ganha um alfinete vermelho (haste de luz +
## "⚠ Ninho" sempre por cima, do tamanho fixo na tela: dá para achar de longe, inclusive na névoa) e, com a Varredura
## profunda, cada jazida medida mostra o tipo, o total e a riqueza na cor do recurso. Só lê a Varredura; refaz a cada
## meio segundo quando algo muda.

const COR_NINHO := Color(0.95, 0.30, 0.24)
const ALTURA := 6.0                   ## m acima do chão onde fica o texto

var varredura: Varredura
var _t := 0.0
var _assinatura := ""
var _marcas: Array[Node3D] = []
var _mat_haste: StandardMaterial3D


func _ready() -> void:
	_mat_haste = StandardMaterial3D.new()
	_mat_haste.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat_haste.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat_haste.albedo_color = Color(COR_NINHO, 0.55)
	_mat_haste.cull_mode = BaseMaterial3D.CULL_DISABLED


func _process(delta: float) -> void:
	if varredura == null:
		return
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.5
	var ninhos := varredura.ninhos_marcados()
	var jaz: Array = []
	if varredura.e_profunda():
		for id in varredura.sensores:
			jaz.append_array(varredura.jazidas(id))
	var assin := "%s|%s" % [ninhos, jaz.map(func(j): return [j.tipo, j.centro])]
	if assin == _assinatura:
		return
	_assinatura = assin
	_refazer(ninhos, jaz)


## Quantas marcas há agora: {ninhos, jazidas} (testes).
func contagem() -> Dictionary:
	var c := {"ninhos": 0, "jazidas": 0}
	for m in _marcas:
		c[m.get_meta("tipo")] += 1
	return c


func _refazer(ninhos: Array[int], jaz: Array) -> void:
	for m in _marcas:
		m.queue_free()
	_marcas.clear()
	for n in ninhos:
		var c: Vector2 = varredura.colonia.ninhos[n].centro
		var m := Node3D.new()
		m.set_meta("tipo", "ninhos")
		m.position = Grade.ponto_mundo(c)
		var haste := MeshInstance3D.new()
		var cil := CylinderMesh.new()
		cil.top_radius = 0.06
		cil.bottom_radius = 0.06
		cil.height = ALTURA - 0.6
		cil.radial_segments = 6
		cil.rings = 1
		cil.material = _mat_haste
		haste.mesh = cil
		haste.position = Vector3(0, (ALTURA - 0.6) * 0.5 + 0.3, 0)
		haste.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m.add_child(haste)
		m.add_child(_rotulo("⚠ Ninho", COR_NINHO, 46))
		add_child(m)
		_marcas.append(m)
	var rec: Dictionary = Registro.recursos.get("jazidas", {})
	for j in jaz:
		var info: Dictionary = rec.get(j.tipo, {"nome": j.tipo, "cor": "#ffffff"})
		var cor := Color(info.cor)
		if cor.get_luminance() < 0.35:
			cor = Color(0.86, 0.86, 0.88)
		var m := Node3D.new()
		m.set_meta("tipo", "jazidas")
		m.position = Grade.ponto_mundo(j.centro)
		m.add_child(_rotulo("%s ≈ %s · %s" % [info.nome, VisaoRecursos._quantidade(int(j.total)), j.nivel], cor, 38))
		add_child(m)
		_marcas.append(m)


func _rotulo(texto: String, cor: Color, tam: int) -> Label3D:
	var l := Label3D.new()
	l.text = texto
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.fixed_size = true
	l.no_depth_test = true
	l.render_priority = 3
	l.outline_render_priority = 2
	l.outline_modulate = Color(0.04, 0.04, 0.05)
	l.outline_size = 12
	l.font_size = tam
	l.modulate = cor
	l.pixel_size = 0.00042
	l.position = Vector3(0, ALTURA, 0)
	return l
