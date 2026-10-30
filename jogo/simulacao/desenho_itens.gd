class_name DesenhoItens
extends Node3D
## Itens nas esteiras (e o que cada braço segura): um MultiMesh por tipo de item, refeito a cada quadro a partir
## da Fabrica. Para caber no celular:
##  - só os caminhos cuja caixa encosta na área vista pela câmera;
##  - com a câmera longe (> DIST_ESCONDE) os itens nem são desenhados (seriam pontinhos);
##  - só refaz quando a simulação andou (30 Hz) ou a câmera mexeu — a tela pode rodar a 60+;
##  - posição calculada direto num buffer de floats (uma chamada por tipo de item).

const DIST_ESCONDE := 50.0

var fabrica: Fabrica
var mapa: MapaOcupacao
var garra: Callable              ## id do braço → ponto da garra no mundo (o item segue o modelo animado)
var _mm: Dictionary = {}          ## item → MultiMeshInstance3D
var custo_us := 0                 ## tempo do último quadro (medição)
var _ultimo := ""                 ## passo da simulação + câmera do último desenho


func _process(_d: float) -> void:
	var cam := get_viewport().get_camera_3d() as CameraJogo
	var chave := "%d|%s|%s|%d" % [fabrica.passos if fabrica != null else 0, cam.alvo if cam else "", cam.distancia if cam else "",
			Engine.get_process_frames() if fabrica != null and not fabrica.bracos.is_empty() else 0]   # garra anda a cada quadro
	if chave == _ultimo:
		return
	_ultimo = chave
	var t0 := Time.get_ticks_usec()
	_desenhar()
	custo_us = Time.get_ticks_usec() - t0


func _desenhar() -> void:
	if fabrica == null:
		return
	var cam := get_viewport().get_camera_3d() as CameraJogo
	# 1ª passada: posição (x, y, z) e tipo de cada item visível, em vetores locais (sem cópia)
	var pos := PackedFloat32Array()
	var tipo := PackedInt32Array()
	var tipos: Array[String] = []
	var indice := {}
	if cam == null or cam.distancia <= DIST_ESCONDE:
		var vista := _area_vista(cam)
		var vel := float(Registro.estruturas["esteira_reta"].velocidade)
		for ci in fabrica.caminhos.size():
			var c: Dictionary = fabrica.caminhos[ci]
			if vista.has_area() and not vista.intersects(c.caixa):
				continue
			var est: EsteiraCaminho = c.esteira
			var n: int = c.tiles.size()
			var oculto: Array = c.get("oculto", [])
			var papel: Array = c.get("papel", [])
			var lat := _laterais(ci, vel)
			var acum := 0.0
			for i in est.itens.size():
				acum += est.espacos[i]
				var bruto := est.comprimento - acum - EsteiraCaminho.ESPACO * 0.5
				var s := clampf(bruto, 0.0, float(n) - 1e-4)
				var k := int(s)
				var f := s - k
				if not oculto.is_empty() and (oculto[k] or (papel[k] == "entrada" and f > 0.52) or (papel[k] == "saida" and f < 0.48)):
					continue                                  # debaixo da terra (ou dentro do pórtico)
				var t: Vector2i = c.tiles[k]
				var entra: int = c.entra[k]
				var sai: int = c.sai[k]
				var p: Vector2
				var sobe := 0.0
				if bruto > float(n):
					# rampa de junção: passa da borda, sobe por cima do trilho da vizinha e deita nela
					var e := bruto - float(n)
					p = Vector2(t.x + 0.5, t.y + 0.5) + Vector2(Grade.DIRECOES[sai]) * (0.5 + e)
					sobe = Fabrica.altura_calha(e)
				elif sai < 0:
					# fim de linha: o item para encostado no para-choque (lado de dentro), não por cima dele
					p = Vector2(t.x + 0.5, t.y + 0.5) + Vector2(Grade.DIRECOES[entra]) * (f * 0.74 - 0.5)
				elif sai == entra:
					p = Vector2(t.x + 0.5, t.y + 0.5) + Vector2(Grade.DIRECOES[entra]) * (f - 0.5)
				else:
					p = Fabrica.ponto_no_tile(t, entra, sai, f)
				for j in lat:
					if absf(acum - j.x) < 0.12:
						p += j.dir * j.y                          # acabou de entrar pela lateral: termina de deslizar
						break
				var nv: Vector2i = c.niveis[k]
				var item: String = est.itens[i]
				if not indice.has(item):
					indice[item] = tipos.size()
					tipos.append(item)
				tipo.append(indice[item])
				pos.append(p.x)
				pos.append(0.16 + sobe + lerpf(nv.x, nv.y, f) * 0.5 + Grade.altura_chao(t))
				pos.append(-p.y)
		for id in fabrica.bracos:
			var b: Braco = fabrica.bracos[id]
			if b.segurando == "" or not mapa.estruturas.has(id):
				continue
			var e: Dictionary = mapa.estruturas[id]
			# o item vai preso na garra (posição real do modelo animado)
			var g: Vector3 = garra.call(id) if garra.is_valid() else Vector3.INF
			if g == Vector3.INF:
				var fr := Vector2(Grade.DIRECOES[Construtor.fluxo_da_rot(e.rot)])
				var cc := Vector2(e.minimo) + Vector2(0.5, 0.5)
				var a := clampf(b.fase() * 2.0, 0.0, 1.0)
				var p := (cc - fr * 0.75).lerp(cc + fr * 0.75, a)
				g = Grade.ponto_mundo(p, 0.55 + 0.25 * sin(a * PI))
			if not indice.has(b.segurando):
				indice[b.segurando] = tipos.size()
				tipos.append(b.segurando)
			tipo.append(indice[b.segurando])
			pos.append(g.x)
			pos.append(g.y - 0.11)
			pos.append(g.z)
	# 2ª passada: um buffer por tipo
	for item in _mm:
		if not indice.has(item):
			(_mm[item] as MultiMeshInstance3D).multimesh.visible_instance_count = 0
	for ti in tipos.size():
		var mmi := _instancia(tipos[ti])
		if mmi == null:
			continue
		var n := tipo.count(ti)
		var mm := mmi.multimesh
		if mm.instance_count < n:
			mm.instance_count = n * 2
		var buf := PackedFloat32Array()
		buf.resize(mm.instance_count * 12)
		var w := 0
		for i in tipo.size():
			if tipo[i] != ti:
				continue
			buf[w] = 1.0
			buf[w + 3] = pos[i * 3]
			buf[w + 5] = 1.0
			buf[w + 7] = pos[i * 3 + 1]
			buf[w + 10] = 1.0
			buf[w + 11] = pos[i * 3 + 2]
			w += 12
		mm.buffer = buf
		mm.visible_instance_count = n


## Itens que entraram pela lateral deste caminho há pouco: (posição esperada agora, recuo lateral restante) + direção.
## O item foi posto no eixo da esteira, mas o desenho o mostra ainda vindo da rampa e desliza até o eixo em ~0,13 s.
func _laterais(ci: int, vel: float) -> Array:
	var out := []
	for j in fabrica.juncoes:
		if j.caminho != ci:
			continue
		var dt := float(fabrica.passos - int(j.passo)) / 30.0
		var resto := 0.25 - vel * dt
		if resto > 0.0:
			out.append({"x": float(j.pos) - vel * dt, "y": resto, "dir": -(j.lado as Vector2)})
	return out


## Quadrado (plano da grade) que cobre o que a câmera vê, com folga.
func _area_vista(cam: CameraJogo) -> Rect2:
	if cam == null:
		return Rect2()
	var tam := get_viewport().get_visible_rect().size
	var meia_alt := cam.distancia * tan(deg_to_rad(cam.fov) / 2.0) / maxf(sin(cam.inclinacao()), 0.3)
	var raio := Vector2(meia_alt * tam.x / maxf(tam.y, 1.0), meia_alt).length() * 1.15
	var c := Vector2(cam.alvo.x, -cam.alvo.z)
	return Rect2(c - Vector2(raio, raio), Vector2(raio, raio) * 2.0)


## Troca o matiz da parte colorida (cristal/tijolo) mantendo saturação e brilho: pacote de automação = frasco do
## pacote de pesquisa com líquido âmbar; briquete = tijolos na cor da biomassa (o ícone é derivado do mesmo jeito,
## ferramentas/derivar_icone.gd).
static func _tingir(malha: Mesh, matiz: float) -> void:
	for s in malha.get_surface_count():
		var m := malha.surface_get_material(s) as ShaderMaterial
		if m == null or not m.resource_name.begins_with("P_Cristal") and not m.resource_name.begins_with("P_Tijolo"):
			continue
		m = m.duplicate()
		var c: Color = m.get_shader_parameter("cor")
		m.set_shader_parameter("cor", Color.from_hsv(matiz, c.s, c.v, c.a))
		var e = m.get_shader_parameter("cor_emissao")
		if e is Color:
			m.set_shader_parameter("cor_emissao", Color.from_hsv(matiz, e.s, e.v, e.a))
		malha.surface_set_material(s, m)


func _instancia(item: String) -> MultiMeshInstance3D:
	if _mm.has(item):
		return _mm[item]
	var info: Dictionary = Registro.itens.get(item, {})
	var base: String = info.get("modelo_de", item)          # item sem modelo próprio usa o de outro (com outra cor)
	if not Registro.modelos.has(base):
		return null
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = Materiais.malha_de(load(Registro.modelos[base].modelo))
	if info.has("matiz"):
		_tingir(mm.mesh, float(info.matiz))
	mm.instance_count = 64
	mm.visible_instance_count = 0
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF   # sombra de item miúdo não compensa
	add_child(mmi)
	_mm[item] = mmi
	return mmi
