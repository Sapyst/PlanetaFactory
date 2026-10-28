class_name DesenhoChunk
extends Node3D
## Desenha um chunk: chão (1 malha, 1 quad por tile) + obstáculos, jazidas e enfeites em MultiMesh
## (uma chamada de desenho por tipo de modelo por chunk, não importa quantos).

const CAMADAS_AGUA := ["jazida", "praia", "agua_rasa", "agua_funda"]   ## agua_* sempre por último (shader)

static var _texturas: Texture2DArray
static var _material_chao: ShaderMaterial
static var _malhas: Dictionary = {}    ## nome → Mesh (convertida)
static var _camadas: Array[String] = []


static func preparar(gerador: GeradorMundo) -> void:
	if _material_chao != null:
		return
	_camadas.clear()
	for b in gerador.nomes_biomas():
		_camadas.append(gerador.dados_bioma(b).get("textura", b))
	_camadas.append_array(CAMADAS_AGUA)
	var imgs: Array[Image] = []
	for nome in _camadas:
		var tex: Texture2D = load("res://assets/texturas/%s.png" % nome)
		var img := tex.get_image()
		img.decompress()
		img.convert(Image.FORMAT_RGBA8)
		img.generate_mipmaps()
		imgs.append(img)
	_texturas = Texture2DArray.new()
	_texturas.create_from_images(imgs)
	_material_chao = ShaderMaterial.new()
	_material_chao.shader = preload("res://render/shaders/terreno.gdshader")
	_material_chao.set_shader_parameter("texturas", _texturas)
	_material_chao.set_shader_parameter("detalhe", load("res://assets/texturas/ruido_detalhe.png"))
	_material_chao.set_shader_parameter("primeira_agua", float(_camadas.find("agua_rasa")))


static func malha(nome: String, vento := 0.0, boiar := 0.0) -> Mesh:
	if not _malhas.has(nome):
		var m: Dictionary = Registro.modelos.get(nome, {})
		if m.is_empty():
			return null
		_malhas[nome] = Materiais.malha_de(load(m.modelo), vento, boiar)
	return _malhas[nome]


func construir(c: ChunkDados, gerador: GeradorMundo, mapa: MapaOcupacao = null) -> void:
	name = "chunk_%d_%d" % [c.coord.x, c.coord.y]
	_chao(c, gerador)
	var grupos := {}   # nome → Array[Transform3D]
	for t in c.obstaculos:
		if mapa != null and mapa.limpos.has(t):
			continue   # já foi limpo para construir
		var o: Dictionary = c.obstaculos[t]
		var centro := Grade.centro_da_area(o.ancora, o.area, 0)
		_add(grupos, o.nome, Transform3D(Basis(Vector3.UP, Grade.angulo(o.rot)), Grade.ponto_mundo(centro)))
	for t in c.jazidas:
		var j: Dictionary = c.jazidas[t]
		# manchas contínuas: cada tile maior que o tile (encosta nos vizinhos), giro e deslocamento próprios
		var r := Distribuicao.h(t.x, t.y, 77) * TAU
		var esc := 1.15 + 0.25 * Distribuicao.h(t.x, t.y, 78)
		var off := Vector3(Distribuicao.h(t.x, t.y, 79) - 0.5, 0, Distribuicao.h(t.x, t.y, 80) - 0.5) * 0.3
		_add(grupos, j.tipo, Transform3D(Basis(Vector3.UP, r).scaled(Vector3(esc, 1.0, esc)), Grade.centro_mundo(t) + off))
	for d in c.decos:
		_add(grupos, d.nome, Transform3D(Basis(Vector3.UP, d.rot), Grade.ponto_mundo(d.pos, 0.0 if d.nome != "vitoria_regia" else -0.12)))
	for nome in grupos:
		var vegetal: bool = Registro.modelos.get(nome, {}).get("categoria", "") == "mapa/vegetacao"
		var me := malha(nome, 1.0 if vegetal else 0.0, 1.0 if nome == "vitoria_regia" else 0.0)
		if me == null:
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = me
		var lista: Array = grupos[nome]
		mm.instance_count = lista.size()
		for i in lista.size():
			mm.set_instance_transform(i, lista[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = nome
		mmi.multimesh = mm
		if Registro.modelos.get(nome, {}).get("tipo", "") == "deco":
			# enfeite miúdo (grama, seixo, flor) some com a câmera longe: vira só ruído e custa desenho
			mmi.visibility_range_end = 80.0
			mmi.visibility_range_end_margin = 12.0
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		add_child(mmi)


func _add(grupos: Dictionary, nome: String, t: Transform3D) -> void:
	if not grupos.has(nome):
		grupos[nome] = []
	grupos[nome].append(t)


## Camada do Texture2DArray de um tile qualquer (também fora do chunk: a margem do mapa de camadas).
static func camada_de(t: Vector2i, gerador: GeradorMundo) -> int:
	match gerador.terreno(t):
		GeradorMundo.Terreno.PRAIA: return _camadas.find("praia")
		GeradorMundo.Terreno.OCEANO: return _camadas.find("agua_funda")
		GeradorMundo.Terreno.TERRA:
			if not gerador.distribuicao.jazida(t).is_empty():
				return _camadas.find("jazida")
			return gerador.nomes_biomas().find(gerador.bioma(t))
	return _camadas.find("agua_rasa")


## Chão: 1 quad por tile (camada em COLOR.r; correnteza do rio em COLOR.gb/a) e um mapinha 34×34 das camadas
## (chunk + 1 tile de margem) que o shader lê com a posição deformada por ruído — a troca de bioma deixa de ser
## degrau de tile e vira borda orgânica, sem costura entre chunks.
func _chao(c: ChunkDados, gerador: GeradorMundo) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := Grade.TAM_CHUNK
	var base := c.coord * n
	var img := Image.create(n + 2, n + 2, false, Image.FORMAT_R8)
	for j in n + 2:
		for i in n + 2:
			var t := base + Vector2i(i - 1, j - 1)
			var cam: int
			if i >= 1 and j >= 1 and i <= n and j <= n:
				var k := (j - 1) * n + (i - 1)
				cam = _camada_local(c, k, base + Vector2i(i - 1, j - 1))
			else:
				cam = camada_de(t, gerador)
			img.set_pixel(i, j, Color(cam / 255.0, 0, 0))
	for j in n:
		for i in n:
			var k := j * n + i
			var ter := c.terreno[k]
			var t := base + Vector2i(i, j)
			var camada := _camada_local(c, k, t)
			var h := -0.12 if gerador.eh_agua(ter) else 0.0
			var fluxo := Vector2.ZERO
			if ter == GeradorMundo.Terreno.RIO:
				fluxo = gerador.direcao_rio(t)
			var cor := Color(camada / 255.0, 0.5 + 0.5 * fluxo.x, 0.5 + 0.5 * fluxo.y, 1.0 if ter == GeradorMundo.Terreno.RIO else 0.0)
			var x := float(t.x)
			var y := float(t.y)
			var v := [Vector3(x, h, -y), Vector3(x + 1, h, -y), Vector3(x + 1, h, -y - 1), Vector3(x, h, -y - 1)]
			for idx in [0, 2, 1, 0, 3, 2]:
				st.set_color(cor)
				st.set_normal(Vector3.UP)
				st.add_vertex(v[idx])
	var mi := MeshInstance3D.new()
	mi.name = "chao"
	mi.mesh = st.commit()
	var mat := _material_chao.duplicate() as ShaderMaterial
	mat.set_shader_parameter("mapa_camadas", ImageTexture.create_from_image(img))
	mat.set_shader_parameter("origem_mapa", Vector2(base - Vector2i.ONE))
	mi.material_override = mat
	add_child(mi)


func _camada_local(c: ChunkDados, k: int, t: Vector2i) -> int:
	match c.terreno[k]:
		GeradorMundo.Terreno.PRAIA: return _camadas.find("praia")
		GeradorMundo.Terreno.OCEANO: return _camadas.find("agua_funda")
		GeradorMundo.Terreno.TERRA: return _camadas.find("jazida") if c.jazidas.has(t) else c.bioma[k]
	return _camadas.find("agua_rasa")
