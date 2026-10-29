class_name VisaoRecursos
extends Node3D
## Visão de recursos (tecla V / botão "Recursos"): o mapa perde a cor e o que importa para planejar aparece por cima.
##  - jazidas: cada tile pintado com a cor do recurso + nome, quanto tem e qual máquina extrai (dados/recursos.json);
##  - zonas: nome de cada bioma e de cada água no meio da mancha (grade grossa + agrupamento por vizinhança);
##  - ficha do tile sob o mouse/dedo: zona, jazida, elemento natural (e o que rende ao limpar) ou construção;
##  - camada **vento** (V de novo): mapa de calor do vento médio de cada lugar (média medida × fator do lugar,
##    VentoLocal) e setas no chão na direção média; a ficha mostra o vento médio do tile.
## Só lê o gerador e o mapa; refaz o que está na vista quando a câmera anda ou muda de zoom.

const FADE := 5.0
const MAX_ROTULOS := 40

var gerador: GeradorMundo
var mapa: MapaOcupacao
var camera: CameraJogo
var ligada := false
var camada := "recursos"              ## "recursos" ou "vento"
var clima: Clima
var vento_local: VentoLocal
var _setas: MultiMeshInstance3D
var areas_interface: Callable          ## → Array[Rect2] da interface (rótulo não fica embaixo)

var _forca := 0.0
var _tiles: MultiMeshInstance3D
var _rotulos: Array[Label3D] = []
var _marca: MeshInstance3D
var _ficha: PanelContainer
var _ficha_texto: Label
var _camada: CanvasLayer
var _feito_em := Vector3.INF          ## (x, z, distância) da última montagem
var _manchas := {}                    ## chave da mancha → {tipo, centro, tiles: Array[Vector2i], total}
var _d: Dictionary
var _ativos: Array[Dictionary] = []   ## rótulos montados: {titulo, sub, prio, mundo}


func _ready() -> void:
	_d = Registro.recursos
	var q := PlaneMesh.new()
	q.size = Vector2(0.96, 0.96)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.vertex_color_use_as_albedo = true
	q.material = m
	_tiles = MultiMeshInstance3D.new()
	_tiles.multimesh = MultiMesh.new()
	_tiles.multimesh.transform_format = MultiMesh.TRANSFORM_3D
	_tiles.multimesh.use_colors = true
	_tiles.multimesh.mesh = q
	_tiles.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_tiles)
	_setas = MultiMeshInstance3D.new()                 # setas deitadas no chão (direção média do vento)
	_setas.multimesh = MultiMesh.new()
	_setas.multimesh.transform_format = MultiMesh.TRANSFORM_3D
	_setas.multimesh.mesh = _malha_seta(m)
	_setas.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_setas)
	# marca do tile sob o cursor: moldura branca
	var mq := PlaneMesh.new()
	mq.size = Vector2.ONE
	var mm := StandardMaterial3D.new()
	mm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mm.albedo_texture = _textura_moldura()
	mm.no_depth_test = true
	mq.material = mm
	_marca = MeshInstance3D.new()
	_marca.mesh = mq
	_marca.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_marca)
	_criar_ficha()
	visible = false


## Desligada → recursos → vento (se houver clima) → desligada.
func alternar() -> bool:
	if not ligada:
		ligada = true
		camada = "recursos"
	elif camada == "recursos" and clima != null and vento_local != null:
		camada = "vento"
	else:
		ligada = false
	_feito_em = Vector3.INF
	return ligada


func _process(delta: float) -> void:
	_forca = move_toward(_forca, 1.0 if ligada else 0.0, delta * FADE)
	RenderingServer.global_shader_parameter_set("visao_recursos", _forca)
	visible = _forca > 0.0
	_ficha.visible = ligada
	if not visible:
		return
	var aqui := Vector3(camera.alvo.x, camera.alvo.z, camera.distancia)
	var passo := maxf(6.0, camera.distancia * 0.2)
	if Vector2(aqui.x, aqui.y).distance_to(Vector2(_feito_em.x, _feito_em.y)) > passo \
			or absf(log(aqui.z / maxf(_feito_em.z, 0.01))) > 0.2:
		_feito_em = aqui
		_montar()
	_arrumar_rotulos()
	for r in _rotulos:
		r.transparency = 1.0 - _forca
	(_tiles.multimesh.mesh.surface_get_material(0) as StandardMaterial3D).albedo_color.a = _forca
	(_setas.multimesh.mesh.surface_get_material(0) as StandardMaterial3D).albedo_color.a = _forca
	_atualizar_ficha()


# ------------------------------------------------------------------ montagem do que está na vista
## Retângulo (em tiles) que a câmera enxerga, com folga.
func _vista() -> Rect2i:
	var c := Grade.tile_de_mundo(camera.alvo)
	var r := int(camera.distancia * 1.1) + 8
	return Rect2i(c - Vector2i(r, r), Vector2i(2 * r, 2 * r))


func _montar() -> void:
	var v := _vista()
	_setas.visible = camada == "vento"
	if camada == "vento":
		_montar_vento(v)
		return
	var rotulos: Array[Dictionary] = []
	# jazidas: manchas das células que tocam a vista (e as fixas do spawn)
	var cel := Distribuicao.CEL_JAZIDA
	var vistas: Array[Dictionary] = []
	for cy in range(floori(v.position.y / float(cel)), floori(v.end.y / float(cel)) + 1):
		for cx in range(floori(v.position.x / float(cel)), floori(v.end.x / float(cel)) + 1):
			var m := gerador.distribuicao.mancha_da_celula(Vector2i(cx, cy))
			if not m.is_empty():
				vistas.append(_mancha(str(Vector2i(cx, cy)), m))
	for i in Distribuicao.SPAWN.size():
		vistas.append(_mancha("spawn%d" % i, Distribuicao.SPAWN[i]))
	var cores: Array[Color] = []
	var pos: Array[Vector2i] = []
	for m in vistas:
		if m.tiles.is_empty() or not v.has_point(Vector2i(m.centro.floor())):
			continue
		var info: Dictionary = _d.jazidas.get(m.tipo, {"nome": m.tipo, "cor": "#ffffff", "extrator": ""})
		var cor := Color(info.cor)
		for t in m.tiles:
			pos.append(t)
			cores.append(Color(cor, 0.62))
		rotulos.append({"texto": "%s  ≈ %s" % [info.nome, _quantidade(m.total)], "pos": m.centro, "cor": cor.lightened(0.35),
				"tam": 1.0, "sub": "extrair com " + info.extrator, "prio": 0})
	var mm := _tiles.multimesh
	mm.instance_count = pos.size()
	for i in pos.size():
		mm.set_instance_transform(i, Transform3D(Basis(), Grade.centro_mundo(pos[i]) + Vector3(0, 0.05, 0)))
		mm.set_instance_color(i, cores[i])
	rotulos.append_array(_rotulos_zonas(v))
	_desenhar_rotulos(rotulos)


## Vento médio de um tile: média medida (força) × fator do lugar com o vento vindo da direção média.
func vento_medio_em(t: Vector2i) -> float:
	return clima.vento_medio.length() * vento_local.fator(t, clima.vento_medio)


## Calor do vento: azul (calmo) → verde → amarelo → vermelho (ventania), em blocos (maiores com zoom longe).
static func cor_vento(v: float) -> Color:
	var paradas := [[0.0, Color(0.15, 0.3, 0.75)], [0.3, Color(0.2, 0.65, 0.7)], [0.55, Color(0.35, 0.8, 0.3)],
			[0.8, Color(0.95, 0.85, 0.2)], [1.1, Color(0.95, 0.35, 0.15)]]
	for i in range(1, paradas.size()):
		if v <= paradas[i][0]:
			var a: Array = paradas[i - 1]
			return (a[1] as Color).lerp(paradas[i][1], (v - a[0]) / (paradas[i][0] - a[0]))
	return paradas[-1][1]


func _montar_vento(v: Rect2i) -> void:
	var passo := maxi(1, int(camera.distancia / 22.0))
	var mm := _tiles.multimesh
	var n := ceili(v.size.x / float(passo)) * ceili(v.size.y / float(passo))
	mm.instance_count = n
	var i := 0
	var esc := Basis().scaled(Vector3(passo, 1, passo))
	for y in range(v.position.y, v.end.y, passo):
		for x in range(v.position.x, v.end.x, passo):
			var t := Vector2i(x, y)
			mm.set_instance_transform(i, Transform3D(esc, Grade.ponto_mundo(Vector2(t) + Vector2(passo, passo) * 0.5, 0.05)))
			mm.set_instance_color(i, Color(cor_vento(vento_medio_em(t)), 0.7))
			i += 1
	mm.instance_count = i
	# setas a cada 8 tiles (mais espaçadas de longe), deitadas, apontando para onde o vento médio sopra
	var dir := clima.vento_medio.normalized() if clima.vento_medio.length() > 1e-4 else clima.direcao_vento
	var ang := atan2(dir.y, dir.x)                                     # giro em Y: +x vai a (cos, 0, −sen) = mundo da grade
	var ps := 8 * passo
	var sm := _setas.multimesh
	sm.instance_count = 0
	var setas: Array[Transform3D] = []
	for y in range(snappedi(v.position.y, ps), v.end.y, ps):
		for x in range(snappedi(v.position.x, ps), v.end.x, ps):
			setas.append(Transform3D(Basis(Vector3.UP, ang).scaled(Vector3.ONE * passo), Grade.ponto_mundo(Vector2(x, y) + Vector2(0.5, 0.5), 0.1)))
	sm.instance_count = setas.size()
	for k in setas.size():
		sm.set_instance_transform(k, setas[k])
	var centro := Vector2(Grade.tile_de_mundo(camera.alvo))
	_desenhar_rotulos([{"texto": "Vento médio %d%% %s" % [clima.vento_medio.length() * 100, Clima.nome_rumo(clima.vento_medio)],
			"pos": centro, "cor": Color(0.85, 0.95, 1.0), "tam": 1.0,
			"sub": "predomina %s nesta estação · cor = vento do lugar" % Clima.nome_rumo(clima.rumo_atual()), "prio": 0}])


## Seta plana (haste + ponta) deitada no chão, apontando para +x.
func _malha_seta(mat: Material) -> ArrayMesh:
	var p := PackedVector3Array([
		Vector3(-1.2, 0, -0.12), Vector3(0.4, 0, -0.12), Vector3(0.4, 0, 0.12),
		Vector3(-1.2, 0, -0.12), Vector3(0.4, 0, 0.12), Vector3(-1.2, 0, 0.12),
		Vector3(0.4, 0, -0.45), Vector3(1.3, 0, 0), Vector3(0.4, 0, 0.45)])
	var c := PackedColorArray()
	for k in p.size():
		c.append(Color(0.95, 0.97, 1.0, 0.9))
	var a := []
	a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = p
	a[Mesh.ARRAY_COLOR] = c
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	var mm := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
	mm.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.surface_set_material(0, mm)
	return mesh


func _mancha(chave: String, m: Dictionary) -> Dictionary:
	if _manchas.has(chave):
		return _manchas[chave]
	var tiles: Array[Vector2i] = []
	var total := 0
	var r := int(ceil(m.raio)) + 1
	var c: Vector2 = m.centro
	for y in range(floori(c.y) - r, floori(c.y) + r + 1):
		for x in range(floori(c.x) - r, floori(c.x) + r + 1):
			var j := gerador.distribuicao.jazida(Vector2i(x, y))
			if not j.is_empty() and j.tipo == m.tipo:
				tiles.append(Vector2i(x, y))
				total += int(j.quantidade)
	var out := {"tipo": m.tipo, "centro": c, "tiles": tiles, "total": total}
	_manchas[chave] = out
	return out


static func _quantidade(n: int) -> String:
	if n >= 1000:
		return "%d mil" % roundi(n / 1000.0)
	return str(n)


## Nome de cada zona: amostra a vista numa grade grossa, junta amostras vizinhas da mesma zona e põe o nome no meio.
func _rotulos_zonas(v: Rect2i) -> Array[Dictionary]:
	var passo := maxi(6, roundi(camera.distancia / 5.0))
	var w := v.size.x / passo + 1
	var h := v.size.y / passo + 1
	var zona := {}
	for gy in h:
		for gx in w:
			zona[Vector2i(gx, gy)] = _zona(v.position + Vector2i(gx, gy) * passo)
	var visto := {}
	var out: Array[Dictionary] = []
	for k in zona:
		if visto.has(k):
			continue
		var z: String = zona[k]
		var fila: Array[Vector2i] = [k]
		var soma := Vector2.ZERO
		var n := 0
		visto[k] = true
		while not fila.is_empty():
			var a: Vector2i = fila.pop_back()
			soma += Vector2(a)
			n += 1
			for d in Grade.DIRECOES:
				var b: Vector2i = a + d
				if zona.has(b) and not visto.has(b) and zona[b] == z:
					visto[b] = true
					fila.append(b)
		if n < (1 if z.begins_with("agua") else 4):
			continue
		var centro := Vector2(v.position) + soma / n * passo
		var agua := z.begins_with("agua")
		var nome: String = (_d.agua if agua else _d.biomas).get(z.get_slice(":", 1), z)
		out.append({"texto": nome, "pos": centro, "cor": Color(0.62, 0.82, 1.0) if agua else Color(0.95, 0.95, 0.92),
				"tam": 0.8, "sub": "", "prio": 1 if agua else 2})
	return out


func _zona(t: Vector2i) -> String:
	var ter := gerador.terreno(t)
	if ter != GeradorMundo.Terreno.TERRA:
		return "agua:" + GeradorMundo.Terreno.keys()[ter]
	return "bio:" + gerador.bioma(t)


## Cada rótulo = nome (maior) + detalhe embaixo (menor). Tamanho fixo na tela em qualquer zoom.
func _desenhar_rotulos(lista: Array[Dictionary]) -> void:
	lista = lista.slice(0, MAX_ROTULOS)
	while _rotulos.size() < lista.size() * 2:
		var l := Label3D.new()
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.fixed_size = true
		l.no_depth_test = true
		l.render_priority = 3
		l.outline_render_priority = 2
		l.outline_modulate = Color(0.04, 0.04, 0.05)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.pixel_size = 0.00042
		add_child(l)
		_rotulos.append(l)
	for i in _rotulos.size():
		_rotulos[i].visible = false
	_ativos.clear()
	for i in lista.size():
		var r: Dictionary = lista[i]
		var cor: Color = r.cor
		if cor.get_luminance() < 0.35:
			cor = Color(0.86, 0.86, 0.88)               # carvão: texto claro (a cor fica nos tiles)
		var titulo := _rotulos[2 * i]
		titulo.text = r.texto
		titulo.font_size = int(52 * r.tam)
		titulo.outline_size = 14
		titulo.modulate = cor
		titulo.position = Grade.ponto_mundo(r.pos, 1.2)
		titulo.offset = Vector2(0, 14)
		titulo.visible = true
		if r.sub != "":
			var sub := _rotulos[2 * i + 1]
			sub.text = r.sub
			sub.font_size = 30
			sub.outline_size = 10
			sub.modulate = Color(0.9, 0.9, 0.9)
			sub.position = titulo.position
			sub.offset = Vector2(0, -36)
			sub.visible = true
		_ativos.append({"titulo": titulo, "sub": _rotulos[2 * i + 1] if r.sub != "" else null, "prio": r.prio,
				"mundo": titulo.position})


## Textos nunca se atrapalham: em ordem de importância (jazida, água, bioma; mais perto do centro primeiro), cada
## rótulo procura um lugar livre na tela — no ponto, logo acima ou logo abaixo; se não couber, some.
func _arrumar_rotulos() -> void:
	var tela := get_viewport().get_visible_rect().size
	var k := 0.00042 * tela.y / (2.0 * tan(deg_to_rad(camera.fov) / 2.0))     # pixel do rótulo → pixel da tela
	var fonte := ThemeDB.fallback_font
	var meio := tela / 2.0
	var lista := _ativos.duplicate()
	for a in lista:
		a["tela"] = camera.unproject_position(a.mundo)
	lista.sort_custom(func(a, b): return a.prio < b.prio or (a.prio == b.prio and a.tela.distance_squared_to(meio) < b.tela.distance_squared_to(meio)))
	var ocupados: Array[Rect2] = []
	if areas_interface.is_valid():
		ocupados.append_array(areas_interface.call())
	if _ficha.visible:
		ocupados.append(_ficha.get_global_rect().grow(6.0))
	var dentro := Rect2(Vector2.ZERO, tela).grow(-6.0)
	for a in lista:
		var t: Label3D = a.titulo
		var sub: Label3D = a.sub
		var p: Vector2 = a.tela
		var tw := fonte.get_string_size(t.text, HORIZONTAL_ALIGNMENT_LEFT, -1, t.font_size).x * k
		var th := t.font_size * 1.15 * k
		var sw := 0.0 if sub == null else fonte.get_string_size(sub.text, HORIZONTAL_ALIGNMENT_LEFT, -1, sub.font_size).x * k
		var topo := p.y - 14.0 * k - th / 2.0
		var base := p.y + (36.0 * k + sub.font_size * 0.6 * k if sub != null else -14.0 * k + th / 2.0)
		var bloco := Rect2(p.x - maxf(tw, sw) / 2.0, topo, maxf(tw, sw), base - topo).grow(4.0)
		var achou := false
		for dy in [0.0, -bloco.size.y, bloco.size.y]:
			var r := Rect2(bloco.position + Vector2(0, dy), bloco.size)
			var livre := camera.is_position_in_frustum(a.mundo) and dentro.encloses(r)
			for o in ocupados:
				if livre and o.intersects(r):
					livre = false
			if livre:
				ocupados.append(r)
				t.offset.y = 14.0 - dy / k
				if sub != null:
					sub.offset.y = -36.0 - dy / k
				achou = true
				break
		t.visible = achou
		if sub != null:
			sub.visible = achou


# ------------------------------------------------------------------ ficha do tile sob o cursor/dedo
func _criar_ficha() -> void:
	_camada = CanvasLayer.new()
	_camada.layer = 20
	add_child(_camada)
	_ficha = PanelContainer.new()
	_ficha.set_anchors_preset(Control.PRESET_TOP_LEFT)          # posição: _posicionar_ficha (abaixo da interface)
	_ficha.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.08, 0.1, 0.86)
	sb.set_corner_radius_all(8)
	sb.set_content_margin_all(10)
	_ficha.add_theme_stylebox_override("panel", sb)
	_ficha_texto = Label.new()
	_ficha_texto.add_theme_font_size_override("font_size", 17)
	_ficha_texto.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_ficha.add_child(_ficha_texto)
	_camada.add_child(_ficha)
	_ficha.visible = false


func _atualizar_ficha() -> void:
	var p := camera.no_chao(get_viewport().get_mouse_position())
	if p == Vector3.INF:
		_marca.visible = false
		return
	var t := Grade.tile_de_mundo(p)
	_marca.visible = ligada
	_marca.position = Grade.centro_mundo(t) + Vector3(0, 0.08, 0)
	_ficha_texto.text = descrever(t)
	_posicionar_ficha()


## Centro, no alto, mas logo abaixo de qualquer peça da interface que estiver ali (barra de ferramentas): nunca por cima.
func _posicionar_ficha() -> void:
	var vp := get_viewport().get_visible_rect().size
	var tam := _ficha.get_combined_minimum_size()
	_ficha.size = tam
	var x := (vp.x - tam.x) * 0.5
	var y := 12.0
	var areas: Array = areas_interface.call() if areas_interface.is_valid() else []
	for volta in 4:
		var mexeu := false
		for r: Rect2 in areas:
			if Rect2(x, y, tam.x, tam.y).intersects(r):
				y = r.end.y + 8.0
				mexeu = true
		if not mexeu:
			break
	_ficha.position = Vector2(x, y)


## Texto da ficha de um tile (também usado nos testes).
func descrever(t: Vector2i) -> String:
	var linhas: Array[String] = []
	var ter := gerador.terreno(t)
	if ter != GeradorMundo.Terreno.TERRA:
		linhas.append(_d.agua.get(GeradorMundo.Terreno.keys()[ter], "Água"))
	else:
		linhas.append(_d.biomas.get(gerador.bioma(t), gerador.bioma(t)))
	if clima != null and vento_local != null:
		var lugar := vento_local.fator(t, clima.vento_medio)
		linhas.append("Vento médio aqui: %d%% %s (o lugar dá %+d%%)" % [vento_medio_em(t) * 100, Clima.nome_rumo(clima.vento_medio), (lugar - 1.0) * 100])
	var j := gerador.distribuicao.jazida(t)
	if not j.is_empty():
		var info: Dictionary = _d.jazidas.get(j.tipo, {"nome": j.tipo, "extrator": ""})
		linhas.append("Jazida de %s — %d neste tile · extrair com %s" % [info.nome.to_lower(), int(j.quantidade), info.extrator])
	var id: int = mapa.tiles.get(t, -1)
	if id >= 0:
		var nome: String = mapa.estruturas[id].nome
		linhas.append("Construção: %s" % Registro.estruturas.get(nome, {}).get("nome", nome.replace("_", " ")))
	elif not mapa.limpos.has(t):
		var o := gerador.distribuicao.obstaculo(t)
		if not o.is_empty():
			if mapa.arvores.has(t):
				o = o.duplicate()
				o["estado"] = mapa.arvores[t].e
			var drops: Dictionary = MapaOcupacao.drops_de(o)
			var rende: Array[String] = []
			for k in drops:
				rende.append("%d %s" % [int(drops[k]), Registro.itens.get(k, {}).get("nome", k).to_lower()])
			var txt: String = _d.elementos.get(o.nome, _d.elementos.get(Distribuicao.especie(o.nome), o.nome))
			txt += {"queimada": " (queimada)", "caida": " (caída, carbonizada)"}.get(o.get("estado", ""), "")
			if not rende.is_empty():
				txt += " — remover rende " + ", ".join(rende)
			linhas.append(txt)
	return "\n".join(linhas)


func _textura_moldura() -> Texture2D:
	var img := Image.create(32, 32, false, Image.FORMAT_RGBA8)
	for y in 32:
		for x in 32:
			var borda := mini(mini(x, 31 - x), mini(y, 31 - y))
			img.set_pixel(x, y, Color(1, 1, 1, 0.95) if borda < 3 else Color(1, 1, 1, 0.08))
	return ImageTexture.create_from_image(img)
