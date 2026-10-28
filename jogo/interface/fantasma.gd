class_name Fantasma
extends Node3D
## Desenha um plano do Construtor: cada peça translúcida (verde = pode, vermelho = não pode, cinza = já está igual),
## a pegada no chão tile a tile e setas nas portas (entrada aponta para dentro, saída para fora) — é assim que se lê
## a direção de uma esteira/braço antes de construir. Tudo vem de pools: nada é criado de novo a cada quadro.

const VERDE := Color(0.35, 1.0, 0.55)
const VERMELHO := Color(1.0, 0.30, 0.25)
const CINZA := Color(0.75, 0.78, 0.85, 0.6)
const AMARELO := Color(1.0, 0.85, 0.3)

var _mat: Dictionary = {}                 ## cor (html) → ShaderMaterial
var _modelos: Dictionary = {}             ## nome → Array[Node3D] (pool)
var _usados: Dictionary = {}              ## nome → quantos em uso neste desenho
var _pegadas: Array[MeshInstance3D] = []
var _setas: Array[MeshInstance3D] = []
var _malha_pegada: PlaneMesh
var _malha_seta: ArrayMesh


func _ready() -> void:
	_malha_pegada = PlaneMesh.new()
	_malha_pegada.size = Vector2(0.94, 0.94)
	_malha_seta = _criar_seta()


## plano: itens do Construtor. remover = true pinta tudo de vermelho (o que vai sumir).
func mostrar(plano: Array[Dictionary], remover := false) -> void:
	_usados.clear()
	var np := 0
	var ns := 0
	for it in plano:
		var cor := _cor(it, remover)
		var nome: String = it.nome
		var area := Registro.area(nome)
		var no := _pegar_modelo(Registro.menu.get("icones", {}).get(nome, nome) if nome == "trem" else nome)
		var alt: float = it.get("nivel", 0) * 0.5
		if no != null:
			no.position = Grade.ponto_mundo(Grade.centro_da_area(it.minimo, area, it.rot), 0.01 + alt)
			no.rotation = Vector3(0, Grade.angulo(it.rot) + (PI if it.get("desce", false) else 0.0), 0)
			no.scale = Vector3.ONE
			_pintar(no, cor)
		# pilares planejados para o trecho elevado
		for p in it.get("pilares", []):
			var pl := _pegar_modelo("pilar_segmento")
			pl.position = Grade.ponto_mundo(Vector2(p[0]))
			pl.rotation = Vector3.ZERO
			pl.scale = Vector3(1.6, float(p[1]) / 0.5, 1.6)
			_pintar(pl, cor)
		for t in Grade.tiles_da_area(it.minimo, area, it.rot):
			var p := _pegada(np)
			np += 1
			p.position = Grade.centro_mundo(t, 0.03)
			p.material_override = _material(Color(cor, 0.5))
		if remover:
			continue
		for porta in Registro.modelos.get(nome, {}).get("portas", []):
			if porta.tipo == "TRILHO":
				continue
			var pm := Grade.porta_no_mundo(porta, it.minimo, area, it.rot)
			var s := _seta(ns)
			ns += 1
			var d := Vector2(pm.dir) * (1.0 if porta.io == "SAI" else -1.0)
			var p2: Vector2 = pm.pos - Vector2(pm.dir) * 0.22       # um pouco para dentro da peça
			s.position = Grade.ponto_mundo(p2, float(porta.pos[2]) + 0.30 + alt)
			s.rotation = Vector3(0, atan2(-d.x, d.y), 0)            # −Z da seta → direção d da grade
			s.material_override = _material(AMARELO if porta.io == "SAI" else Color.WHITE)
	_esconder_resto(np, ns)


func limpar() -> void:
	_usados.clear()
	_esconder_resto(0, 0)


func _cor(it: Dictionary, remover: bool) -> Color:
	if remover: return VERMELHO
	if it.get("acao", "") == "igual": return CINZA
	return VERDE if it.motivo == "" else VERMELHO


func _pegar_modelo(nome: String) -> Node3D:
	if not Registro.modelos.has(nome):
		return null
	var lista: Array = _modelos.get(nome, [])
	var i: int = _usados.get(nome, 0)
	_usados[nome] = i + 1
	if i < lista.size():
		lista[i].visible = true
		return lista[i]
	var cena: PackedScene = load(Registro.modelos[nome].modelo)
	var no: Node3D = cena.instantiate()
	add_child(no)
	lista.append(no)
	_modelos[nome] = lista
	return no


func _pintar(no: Node3D, cor: Color) -> void:
	var m := _material(cor)
	for mi in no.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = m
		(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _material(cor: Color) -> ShaderMaterial:
	var k := cor.to_html()
	if not _mat.has(k):
		var m := ShaderMaterial.new()
		m.shader = preload("res://interface/fantasma.gdshader")
		m.set_shader_parameter("cor", cor)
		m.render_priority = 1
		_mat[k] = m
	return _mat[k]


func _pegada(i: int) -> MeshInstance3D:
	while _pegadas.size() <= i:
		var p := MeshInstance3D.new()
		p.mesh = _malha_pegada
		p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(p)
		_pegadas.append(p)
	_pegadas[i].visible = true
	return _pegadas[i]


func _seta(i: int) -> MeshInstance3D:
	while _setas.size() <= i:
		var s := MeshInstance3D.new()
		s.mesh = _malha_seta
		s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(s)
		_setas.append(s)
	_setas[i].visible = true
	return _setas[i]


func _esconder_resto(np: int, ns: int) -> void:
	for nome in _modelos:
		var lista: Array = _modelos[nome]
		for i in range(_usados.get(nome, 0), lista.size()):
			lista[i].visible = false
	for i in range(np, _pegadas.size()):
		_pegadas[i].visible = false
	for i in range(ns, _setas.size()):
		_setas[i].visible = false


## Seta chata (ponta + haste) apontando para −Z, deitada no plano XZ, 0,32 m de comprimento.
func _criar_seta() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := [Vector3(0, 0, -0.16), Vector3(0.12, 0, -0.02), Vector3(-0.12, 0, -0.02),
			Vector3(0.045, 0, -0.02), Vector3(0.045, 0, 0.16), Vector3(-0.045, 0, 0.16), Vector3(-0.045, 0, -0.02)]
	for idx in [0, 1, 2, 3, 4, 5, 3, 5, 6]:
		st.set_normal(Vector3.UP)
		st.add_vertex(pts[idx])
	for idx in [0, 2, 1, 3, 5, 4, 3, 6, 5]:     # verso (visível de baixo também)
		st.set_normal(Vector3.DOWN)
		st.add_vertex(pts[idx])
	return st.commit()
