class_name DesenhoFluxo
extends MeshInstance3D
## Modo construção (peça na mão): por cima de cada esteira, uma faixa colorida seguindo o caminho (reta, curva,
## rampa) com setas correndo no sentido do fluxo. Cor por nível (chão, 0,5 m, 1,0 m) para ler a malha elevada.
## Refaz a malha só quando o mapa muda; acende e apaga suave.

const CORES: Array[Color] = [Color(1.0, 0.82, 0.25), Color(0.35, 0.95, 0.55), Color(0.95, 0.45, 0.95)]
const LARGURA := 0.34
const ALTURA := 0.25               ## topo da lona acima do nível
const PASSOS_CURVA := 6

var mapa: MapaOcupacao
var ligado := false
var _versao := -1
var _forca := 0.0
var _mat: ShaderMaterial


func _ready() -> void:
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://render/shaders/fluxo.gdshader")
	_mat.render_priority = 1
	material_override = _mat
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	visible = false


func _process(delta: float) -> void:
	_forca = move_toward(_forca, 1.0 if ligado else 0.0, delta * 6.0)
	visible = _forca > 0.0
	if not visible:
		return
	_mat.set_shader_parameter("forca", _forca)
	if mapa.versao != _versao:
		_versao = mapa.versao
		mesh = construir(mapa)


## Malha de todas as esteiras do mapa (estática: dá para testar sem janela).
static func construir(m: MapaOcupacao) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 0
	for id in m.estruturas:
		var e: Dictionary = m.estruturas[id]
		var no := Construtor.no_esteira(e)
		if no.is_empty():
			continue
		_faixa(st, e, no)
		n += 1
	if n == 0:
		return null
	return st.commit()


## Linha central da peça em coordenadas da grade (da borda de entrada à borda de saída) + altura em cada ponto.
static func _faixa(st: SurfaceTool, e: Dictionary, no: Dictionary) -> void:
	var c := Vector2(e.minimo) + Vector2(0.5, 0.5)
	var d_in := Vector2(Grade.DIRECOES[no.entra])
	var sai: int = no.sai if no.sai >= 0 else no.entra
	var d_out := Vector2(Grade.DIRECOES[sai])
	var pts: Array[Vector2] = []
	if sai == no.entra:
		pts = [c - d_in * 0.5, c + d_out * 0.5]
	else:
		var canto := c - d_in * 0.5 + d_out * 0.5             # centro do arco (canto interno)
		var a0 := (c - d_in * 0.5 - canto).angle()
		var a1 := (c + d_out * 0.5 - canto).angle()
		var da := wrapf(a1 - a0, -PI, PI)
		for k in PASSOS_CURVA + 1:
			pts.append(canto + Vector2.from_angle(a0 + da * k / PASSOS_CURVA) * 0.5)
	var h0: float = no.n_in * 0.5 + ALTURA
	var h1: float = no.n_out * 0.5 + ALTURA
	var cor: Color = CORES[clampi(maxi(no.n_in, no.n_out), 0, CORES.size() - 1)]
	var total := 0.0
	for k in range(1, pts.size()):
		total += pts[k].distance_to(pts[k - 1])
	var anda := 0.0
	for k in range(pts.size() - 1):
		var p := pts[k]
		var q := pts[k + 1]
		var lado := (q - p).normalized().orthogonal() * LARGURA * 0.5
		var s0 := anda / total
		anda += p.distance_to(q)
		var s1 := anda / total
		var a := Grade.ponto_mundo(p + lado, lerpf(h0, h1, s0))
		var b := Grade.ponto_mundo(p - lado, lerpf(h0, h1, s0))
		var cc := Grade.ponto_mundo(q + lado, lerpf(h0, h1, s1))
		var dd := Grade.ponto_mundo(q - lado, lerpf(h0, h1, s1))
		# UV.y em "tiles" ao longo do caminho: 0..1 por peça, então as setas emendam entre peças vizinhas
		for v in [[a, Vector2(0, s0)], [b, Vector2(1, s0)], [cc, Vector2(0, s1)], [b, Vector2(1, s0)], [dd, Vector2(1, s1)], [cc, Vector2(0, s1)]]:
			st.set_color(cor)
			st.set_uv(v[1])
			st.add_vertex(v[0])
