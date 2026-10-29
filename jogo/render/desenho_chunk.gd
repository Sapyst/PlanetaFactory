class_name DesenhoChunk
extends Node3D
## Desenha um chunk: chão (1 malha com relevo) + obstáculos, jazidas e enfeites em MultiMesh
## (uma chamada de desenho por tipo de modelo por chunk, não importa quantos).

const CAMADAS_AGUA := ["jazida", "piso_fabrica", "praia", "agua_rasa", "agua_funda"]   ## agua_* sempre por último (shader)
const CAMADA_MAR := 250    ## mar/oceano no mapa de camadas: o desenho do mar vem do campo contínuo (UV2), não do tile

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
	_material_chao.set_shader_parameter("camada_rocha", float(_camadas.find("planalto_rochoso")))


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
		var tt := Vector2i(dc.pos.floor())
		var nv0 := gerador.nivel(tt)
		var barranco := false
		for dd in Grade.DIRECOES:
			barranco = barranco or gerador.nivel(tt + dd) != nv0
		if barranco:
			continue                                   # enfeite não fica pendurado na encosta
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
		GeradorMundo.Terreno.OCEANO, GeradorMundo.Terreno.MAR: return CAMADA_MAR
		GeradorMundo.Terreno.TERRA:
			if not gerador.distribuicao.jazida(t).is_empty():
				return _camadas.find("jazida")
			return gerador.nomes_biomas().find(gerador.bioma(t))
	return _camadas.find("agua_rasa")


const SUB := 3              ## vértices por tile no chão (o relevo precisa de meio tile para a encosta)


## Chão do chunk: grade de (32·SUB+1)² vértices compartilhados (malha indexada). Altura de cada vértice:
##  - o relevo contínuo do gerador em patamares (GeradorMundo.patamar): plano no meio do patamar, encosta onde o
##    ruído cruza meio nível — acompanha a curva do terreno, nunca a grade (a grade 1×1 só decide em que nível
##    cada construção fica; no patamar o desenho bate com esse nível);
##  - água afunda 0,12 m conforme a fração de água em volta (margem inclinada, sem rachar).
## COLOR = (fração de água, correnteza x, correnteza y, 1 se rio). Normais pelas diferenças (luz nas encostas).
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
	# níveis e água dos tiles do chunk + 3 de margem (as leituras deslocadas passam da borda)
	var mg := 3
	var lado := n + 2 * mg
	var nv := PackedInt32Array()
	nv.resize(lado * lado)
	var ag := PackedFloat32Array()
	ag.resize(lado * lado)
	var rio := {}
	for j in lado:
		for i in lado:
			var t := base + Vector2i(i - mg, j - mg)
			nv[j * lado + i] = gerador.nivel(t)
			var dentro := i >= mg and j >= mg and i < n + mg and j < n + mg
			var ter: int = c.terreno[(j - mg) * n + (i - mg)] if dentro else gerador.terreno(t)
			# rio e lago pelo tile; mar pelo campo contínuo (costa natural, praia em rampa)
			ag[j * lado + i] = 1.0 if gerador.eh_agua(ter) and ter != GeradorMundo.Terreno.MAR and ter != GeradorMundo.Terreno.OCEANO else 0.0
			if ter == GeradorMundo.Terreno.RIO:
				rio[t] = gerador.direcao_rio(t)
	# relevo e elevação contínuos: variam devagar (ruídos de baixa frequência) — calculados uma vez por canto de
	# tile e interpolados nos vértices (igual ao cálculo direto a olho, ~9× menos ruído)
	var lc := n + 5
	var campo := PackedVector2Array()
	campo.resize(lc * lc)
	for j in lc:
		for i in lc:
			campo[j * lc + i] = gerador.campos_em(Vector2(base + Vector2i(i - 2, j - 2)))
	var v := n * SUB + 1
	var alt := PackedFloat32Array()            # (v + 2)²: uma volta a mais para as normais
	alt.resize((v + 2) * (v + 2))
	var agua_v := PackedFloat32Array()
	agua_v.resize((v + 2) * (v + 2))
	var mar_v := PackedVector2Array()           # (fração de mar, fração de fundo) por vértice
	mar_v.resize((v + 2) * (v + 2))
	var relevo := gerador.relevo_ativo
	for vj in v + 2:
		for vi in v + 2:
			var g := Vector2(base) + Vector2(vi - 1, vj - 1) / float(SUB)
			# campo contínuo no ponto (o tile (i, j) usa o valor do seu canto, por isso −0,5)
			var s := g - Vector2(0.5, 0.5) - Vector2(base) + Vector2(2, 2)
			var ci := clampi(floori(s.x), 0, lc - 2)
			var cj := clampi(floori(s.y), 0, lc - 2)
			var fx := s.x - ci
			var fy := s.y - cj
			var cp := campo[cj * lc + ci].lerp(campo[cj * lc + ci + 1], fx).lerp(campo[(cj + 1) * lc + ci].lerp(campo[(cj + 1) * lc + ci + 1], fx), fy)
			var h := GeradorMundo.patamar(cp.x)
			var e := cp.y
			# água de rio/lago pelo tile: fração bilinear (suavizada) dos 4 centros em volta
			var q := g - Vector2(0.5, 0.5) - Vector2(base) + Vector2(mg, mg)
			var i0 := clampi(floori(q.x), 0, lado - 2)
			var j0 := clampi(floori(q.y), 0, lado - 2)
			var ux := clampf(q.x - i0, 0.0, 1.0)
			var uy := clampf(q.y - j0, 0.0, 1.0)
			ux = ux * ux * (3.0 - 2.0 * ux)
			uy = uy * uy * (3.0 - 2.0 * uy)
			var k00 := j0 * lado + i0
			var a0 := ag[k00]
			var a1 := ag[k00 + 1]
			var a2 := ag[k00 + lado]
			var a3 := ag[k00 + lado + 1]
			var wa := 0.0
			if a0 + a1 + a2 + a3 > 0.0:
				var w0 := (1.0 - ux) * (1.0 - uy) * a0
				var w1 := ux * (1.0 - uy) * a1
				var w2 := (1.0 - ux) * uy * a2
				var w3 := ux * uy * a3
				wa = w0 + w1 + w2 + w3
				# superfície = nível dos tiles de água em volta (leito do rio, fundo do lago)
				var sl := w0 * nv[k00] + w1 * nv[k00 + 1] + w2 * nv[k00 + lado] + w3 * nv[k00 + lado + 1]
				h = lerpf(h, sl / wa, smoothstep(0.0, 0.6, wa))
			# mar: costa pela elevação contínua (e baixada abaixo do nível do mar perto da costa); praia em rampa
			var baixada := 0.0
			if e < 0.02 and relevo:
				baixada = smoothstep(-1.42, -1.58, cp.x) * smoothstep(0.02, -0.02, e)
			var mar := maxf(smoothstep(-0.165, -0.195, e), baixada)
			var rampa := maxf(smoothstep(-0.10, -0.18, e), baixada)
			if rampa > 0.0 and relevo:
				h = lerpf(h, float(GeradorMundo.NIVEL_MAR), rampa)
			var kk := vj * (v + 2) + vi
			mar_v[kk] = Vector2(mar, smoothstep(-0.27, -0.36, e))
			wa = maxf(wa, mar)
			agua_v[kk] = wa
			alt[kk] = h * Grade.ALT_NIVEL - 0.12 * wa * sqrt(wa)
	var verts := PackedVector3Array()
	var normais := PackedVector3Array()
	var cores := PackedColorArray()
	var oclusao := PackedVector2Array()
	oclusao.resize(v * v)
	var mar_out := PackedVector2Array()
	mar_out.resize(v * v)
	verts.resize(v * v)
	normais.resize(v * v)
	cores.resize(v * v)
	var passo := 1.0 / SUB
	for vj in v:
		for vi in v:
			var k := (vj + 1) * (v + 2) + (vi + 1)
			var g := Vector2(base) + Vector2(vi, vj) * passo
			verts[vj * v + vi] = Vector3(g.x, alt[k], -g.y)
			var dx := (alt[k + 1] - alt[k - 1]) / (2.0 * passo)
			var dy := (alt[k + (v + 2)] - alt[k - (v + 2)]) / (2.0 * passo)
			normais[vj * v + vi] = Vector3(-dx, 1.0, dy).normalized()
			# pé de barranco escurece: quanto o terreno a ~2/3 de tile em volta é mais alto que aqui
			var hk := alt[k]
			var l2 := maxi(vi - 1, 0) + (vj + 1) * (v + 2)
			var r2 := mini(vi + 3, v + 1) + (vj + 1) * (v + 2)
			var d2 := (vi + 1) + maxi(vj - 1, 0) * (v + 2)
			var u2 := (vi + 1) + mini(vj + 3, v + 1) * (v + 2)
			var oc := maxf(0.0, alt[l2] - hk) + maxf(0.0, alt[r2] - hk) + maxf(0.0, alt[d2] - hk) + maxf(0.0, alt[u2] - hk)
			oclusao[vj * v + vi] = Vector2(clampf(oc * 0.42, 0.0, 1.0), 0.0)
			mar_out[vj * v + vi] = mar_v[k]
			var t := Vector2i(floori(g.x - 0.001 if vi == v - 1 else g.x), floori(g.y - 0.001 if vj == v - 1 else g.y))
			var fl: Vector2 = rio.get(t, Vector2.ZERO)
			cores[vj * v + vi] = Color(agua_v[k], 0.5 + 0.5 * fl.x, 0.5 + 0.5 * fl.y, 1.0 if rio.has(t) else 0.0)
	var idx := PackedInt32Array()
	idx.resize((v - 1) * (v - 1) * 6)
	var w := 0
	for vj in v - 1:
		for vi in v - 1:
			var a := vj * v + vi
			for o in [a, a + v + 1, a + 1, a, a + v, a + v + 1]:
				idx[w] = o
				w += 1
	return {"verts": verts, "cores": cores, "normais": normais, "uv": oclusao, "uv2": mar_out, "indices": idx, "img": img, "origem": Vector2(base - Vector2i.ONE)}


## Chão: malha indexada com relevo + um mapinha 34×34 das camadas (chunk + 1 tile de margem) que o shader lê com a
## posição deformada por ruído — troca de bioma e margem de água viram borda orgânica, sem costura entre chunks.
func _montar_chao(d: Dictionary) -> void:
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = d.verts
	arr[Mesh.ARRAY_NORMAL] = d.normais
	arr[Mesh.ARRAY_COLOR] = d.cores
	arr[Mesh.ARRAY_INDEX] = d.indices
	arr[Mesh.ARRAY_TEX_UV] = d.uv
	arr[Mesh.ARRAY_TEX_UV2] = d.uv2
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
		GeradorMundo.Terreno.OCEANO, GeradorMundo.Terreno.MAR: return CAMADA_MAR
		GeradorMundo.Terreno.TERRA: return _camadas.find("jazida") if c.jazidas.has(t) else c.bioma[k]
	return _camadas.find("agua_rasa")
