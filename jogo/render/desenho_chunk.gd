class_name DesenhoChunk
extends Node3D
## Desenha um chunk: chão (1 malha, 1 quad por tile) + obstáculos, jazidas e enfeites em MultiMesh
## (uma chamada de desenho por tipo de modelo por chunk, não importa quantos).

const CAMADAS_AGUA := ["jazida", "piso_fabrica", "praia", "agua_rasa", "agua_funda"]   ## agua_* sempre por último (shader)

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
	_material_chao.set_shader_parameter("camada_piso", float(_camadas.find("piso_fabrica")))
	_material_chao.set_shader_parameter("camada_jazida", float(_camadas.find("jazida")))


static func malha(nome: String, vento := 0.0, boiar := 0.0) -> Mesh:
	if not _malhas.has(nome):
		var m: Dictionary = Registro.modelos.get(nome, {})
		if m.is_empty():
			return null
		_malhas[nome] = Materiais.malha_de(load(m.modelo), vento, boiar)
	return _malhas[nome]


## Em duas etapas, para o mapa carregar sem travar a câmera:
##   preparar_dados() — pura, roda numa linha de execução de fundo: gera o chunk, a malha do chão (arrays), o mapa
##                      de camadas e a lista de objetos com suas transformações;
##   montar()         — na linha principal: só cria a malha, a textura e os MultiMesh (rápido).
## construir() faz as duas na hora (redesenho pontual e testes).
static func preparar_dados(k: Vector2i, gerador: GeradorMundo) -> Dictionary:
	var c := gerador.gerar_chunk(k)
	var d := {"coord": k, "chao": _chao_dados(c, gerador), "obst": [], "grupos": {}, "tiles": {}}
	for t in c.obstaculos:
		var o: Dictionary = c.obstaculos[t]
		var centro := Grade.centro_da_area(o.ancora, o.area, 0)
		d.obst.append([o.nome, Transform3D(Basis(Vector3.UP, Grade.angulo(o.rot)), Grade.ponto_mundo(centro)), t])
	for t in c.jazidas:
		var j: Dictionary = c.jazidas[t]
		# manchas contínuas: cada tile maior que o tile (encosta nos vizinhos), giro e deslocamento próprios
		var r := Distribuicao.h(t.x, t.y, 77) * TAU
		var esc := 1.15 + 0.25 * Distribuicao.h(t.x, t.y, 78)
		var off := Vector3(Distribuicao.h(t.x, t.y, 79) - 0.5, 0, Distribuicao.h(t.x, t.y, 80) - 0.5) * 0.3
		_add(d.grupos, j.tipo, Transform3D(Basis(Vector3.UP, r).scaled(Vector3(esc, 1.0, esc)), Grade.centro_mundo(t) + off))
		_add(d.tiles, j.tipo, t)
	for dc in c.decos:
		_add(d.grupos, dc.nome, Transform3D(Basis(Vector3.UP, dc.rot), Grade.ponto_mundo(dc.pos, 0.0 if dc.nome != "vitoria_regia" else -0.12)))
		_add(d.tiles, dc.nome, Vector2i(dc.pos.floor()))
	# já no formato do MultiMesh (12 floats por instância): a linha principal só entrega o buffer
	var bufs := {}
	for nome in d.grupos:
		bufs[nome] = _buffer(d.grupos[nome])
	d["transf"] = d.grupos            # lista crua (para filtrar o que ficou debaixo de construção)
	d.grupos = bufs
	return d


static func _buffer(lista: Array) -> PackedFloat32Array:
	var b := PackedFloat32Array()
	b.resize(lista.size() * 12)
	var w := 0
	for t: Transform3D in lista:
		var x := t.basis.x
		var y := t.basis.y
		var z := t.basis.z
		var o := t.origin
		b[w] = x.x; b[w + 1] = y.x; b[w + 2] = z.x; b[w + 3] = o.x
		b[w + 4] = x.y; b[w + 5] = y.y; b[w + 6] = z.y; b[w + 7] = o.y
		b[w + 8] = x.z; b[w + 9] = y.z; b[w + 10] = z.z; b[w + 11] = o.z
		w += 12
	return b


func construir(c: ChunkDados, gerador: GeradorMundo, mapa: MapaOcupacao = null) -> void:
	montar(preparar_dados(c.coord, gerador), mapa)


const ESPALHA := 2                 ## tiles de piso de fábrica em volta de cada construção
var _dados: Dictionary
var _mapa: MapaOcupacao
var _img_fabrica: Image
var _tex_fabrica: ImageTexture
var _objetos: Array[Node] = []


func montar(d: Dictionary, mapa: MapaOcupacao = null) -> void:
	name = "chunk_%d_%d" % [d.coord.x, d.coord.y]
	_dados = d
	_mapa = mapa
	_montar_chao(d.chao)
	atualizar_fabrica()
	refazer_objetos()


## Construção mudou neste chunk: piso de fábrica e objetos naturais escondidos.
func atualizar(mapa: MapaOcupacao) -> void:
	_mapa = mapa
	atualizar_fabrica()
	refazer_objetos()


## Mapa 34×34 (chunk + margem): 1 onde há construção no chão (o shader espalha o piso de fábrica a partir daí).
## Máquina de jazida (extrator, broca, bomba) deixa o chão de minério à mostra.
func atualizar_fabrica() -> void:
	var n := Grade.TAM_CHUNK
	var base: Vector2i = _dados.coord * n
	if _img_fabrica == null:
		_img_fabrica = Image.create(n + 2, n + 2, false, Image.FORMAT_R8)
	_img_fabrica.fill(Color(0, 0, 0))
	if _mapa != null:
		# espalha 2 tiles em volta de cada construção, enfraquecendo com a distância (o shader deforma a borda)
		var valor := PackedFloat32Array()
		valor.resize((n + 2) * (n + 2))
		for j in range(-ESPALHA, n + 2 + ESPALHA):
			for i in range(-ESPALHA, n + 2 + ESPALHA):
				var id: int = _mapa.tiles.get(base + Vector2i(i - 1, j - 1), -1)
				if id < 0:
					continue
				var nome: String = _mapa.estruturas[id].nome
				if nome == "ninho_aranha" or Registro.estruturas.get(nome, {}).has("requer_jazida"):
					continue
				for dj in range(-ESPALHA, ESPALHA + 1):
					for di in range(-ESPALHA, ESPALHA + 1):
						var x := i + di
						var y := j + dj
						if x < 0 or y < 0 or x > n + 1 or y > n + 1:
							continue
						var v := 1.0 - Vector2(di, dj).length() / (ESPALHA + 1.0)
						var k := y * (n + 2) + x
						if v > valor[k]:
							valor[k] = v
		for j in n + 2:
			for i in n + 2:
				var v := valor[j * (n + 2) + i]
				if v > 0.0:
					_img_fabrica.set_pixel(i, j, Color(v, 0, 0))
	if _tex_fabrica == null:
		_tex_fabrica = ImageTexture.create_from_image(_img_fabrica)
		(get_node("chao") as MeshInstance3D).material_override.set_shader_parameter("mapa_fabrica", _tex_fabrica)
	else:
		_tex_fabrica.update(_img_fabrica)


## MultiMesh dos objetos naturais; o que fica em tile ocupado por construção (ou limpo) não aparece.
func refazer_objetos() -> void:
	for o in _objetos:
		o.queue_free()
	_objetos.clear()
	var d := _dados
	var mapa := _mapa
	var grupos: Dictionary = d.grupos.duplicate()
	if mapa != null:
		var n := Grade.TAM_CHUNK
		var base: Vector2i = d.coord * n
		var ocupado := _img_fabrica != null and not _img_fabrica.is_invisible()
		if not ocupado:
			for t in mapa.tiles:
				if Grade.chunk_de(t) == d.coord:
					ocupado = true
					break
		if ocupado:
			for nome in d.tiles:
				var enfeite: bool = Registro.modelos.get(nome, {}).get("tipo", "") == "deco"
				var ts: Array = d.tiles[nome]
				var lista: Array = []
				for i in ts.size():
					var t: Vector2i = ts[i]
					if mapa.tiles.has(t):
						continue
					# grama/flor/seixo não ficam em cima do piso de fábrica
					if enfeite and _img_fabrica != null and _img_fabrica.get_pixel(t.x - base.x + 1, t.y - base.y + 1).r > 0.45:
						continue
					lista.append(d.transf[nome][i])
				grupos[nome] = _buffer(lista)
	var obst := {}
	for o in d.obst:
		if mapa != null and mapa.limpos.has(o[2]):
			continue   # já foi limpo para construir
		_add(obst, o[0], o[1])
	for nome in obst:
		grupos[nome] = _buffer(obst[nome])
	for nome in grupos:
		var vegetal: bool = Registro.modelos.get(nome, {}).get("categoria", "") == "mapa/vegetacao"
		var me := malha(nome, 1.0 if vegetal else 0.0, 1.0 if nome == "vitoria_regia" else 0.0)
		if me == null:
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = me
		var buf: PackedFloat32Array = grupos[nome]
		mm.instance_count = buf.size() / 12
		mm.buffer = buf
		var mmi := MultiMeshInstance3D.new()
		mmi.name = nome
		mmi.multimesh = mm
		_objetos.append(mmi)
		if Registro.modelos.get(nome, {}).get("tipo", "") == "deco":
			# enfeite miúdo (grama, seixo, flor) some com a câmera longe: vira só ruído e custa desenho
			mmi.visibility_range_end = 80.0
			mmi.visibility_range_end_margin = 12.0
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		add_child(mmi)


## Carrega antes as malhas de tudo que o mapa pode ter (o primeiro chunk com uma árvore nova não engasga).
static func aquecer() -> void:
	for nome in Registro.modelos:
		var cat: String = Registro.modelos[nome].get("categoria", "")
		if cat.begins_with("mapa"):
			malha(nome, 1.0 if cat == "mapa/vegetacao" else 0.0, 1.0 if nome == "vitoria_regia" else 0.0)


static func _add(grupos: Dictionary, nome: String, t: Variant) -> void:
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
static func _chao_dados(c: ChunkDados, gerador: GeradorMundo) -> Dictionary:
	var n := Grade.TAM_CHUNK
	var base := c.coord * n
	var img := Image.create(n + 2, n + 2, false, Image.FORMAT_R8)
	for j in n + 2:
		for i in n + 2:
			var cam: int
			if i >= 1 and j >= 1 and i <= n and j <= n:
				var k := (j - 1) * n + (i - 1)
				cam = _camada_local(c, k, base + Vector2i(i - 1, j - 1))
			else:
				cam = camada_de(base + Vector2i(i - 1, j - 1), gerador)
			img.set_pixel(i, j, Color(cam / 255.0, 0, 0))
	var verts := PackedVector3Array()
	var cores := PackedColorArray()
	verts.resize(n * n * 6)
	cores.resize(n * n * 6)
	var w := 0
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
				verts[w] = v[idx]
				cores[w] = cor
				w += 1
	var normais := PackedVector3Array()
	normais.resize(verts.size())
	normais.fill(Vector3.UP)
	return {"verts": verts, "cores": cores, "normais": normais, "img": img, "origem": Vector2(base - Vector2i.ONE)}


## Chão: 1 quad por tile (camada em COLOR.r; correnteza do rio em COLOR.gb/a) e um mapinha 34×34 das camadas
## (chunk + 1 tile de margem) que o shader lê com a posição deformada por ruído — a troca de bioma deixa de ser
## degrau de tile e vira borda orgânica, sem costura entre chunks.
func _montar_chao(d: Dictionary) -> void:
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = d.verts
	arr[Mesh.ARRAY_NORMAL] = d.normais
	arr[Mesh.ARRAY_COLOR] = d.cores
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi := MeshInstance3D.new()
	mi.name = "chao"
	mi.mesh = am
	var mat := _material_chao.duplicate() as ShaderMaterial
	mat.set_shader_parameter("mapa_camadas", ImageTexture.create_from_image(d.img))
	mat.set_shader_parameter("origem_mapa", d.origem)
	mi.material_override = mat
	add_child(mi)


static func _camada_local(c: ChunkDados, k: int, t: Vector2i) -> int:
	match c.terreno[k]:
		GeradorMundo.Terreno.PRAIA: return _camadas.find("praia")
		GeradorMundo.Terreno.OCEANO: return _camadas.find("agua_funda")
		GeradorMundo.Terreno.TERRA: return _camadas.find("jazida") if c.jazidas.has(t) else c.bioma[k]
	return _camadas.find("agua_rasa")
