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
var _mm: Dictionary = {}          ## item → MultiMeshInstance3D
var custo_us := 0                 ## tempo do último quadro (medição)
var _ultimo := ""                 ## passo da simulação + câmera do último desenho


func _process(_d: float) -> void:
	var cam := get_viewport().get_camera_3d() as CameraJogo
	var chave := "%d|%s|%s" % [fabrica.passos if fabrica != null else 0, cam.alvo if cam else "", cam.distancia if cam else ""]
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
		for c in fabrica.caminhos:
			if vista.has_area() and not vista.intersects(c.caixa):
				continue
			var est: EsteiraCaminho = c.esteira
			var n: int = c.tiles.size()
			var acum := 0.0
			for i in est.itens.size():
				acum += est.espacos[i]
				var s := clampf(float(n) - acum - EsteiraCaminho.ESPACO * 0.5, 0.0, float(n) - 1e-4)
				var k := int(s)
				var f := s - k
				var t: Vector2i = c.tiles[k]
				var entra: int = c.entra[k]
				var sai: int = c.sai[k]
				var p: Vector2
				if sai < 0 or sai == entra:
					p = Vector2(t.x + 0.5, t.y + 0.5) + Vector2(Grade.DIRECOES[entra]) * (f - 0.5)
				else:
					p = Fabrica.ponto_no_tile(t, entra, sai, f)
				var nv: Vector2i = c.niveis[k]
				var item: String = est.itens[i]
				if not indice.has(item):
					indice[item] = tipos.size()
					tipos.append(item)
				tipo.append(indice[item])
				pos.append(p.x)
				pos.append(0.16 + lerpf(nv.x, nv.y, f) * 0.5)
				pos.append(-p.y)
		for id in fabrica.bracos:
			var b: Braco = fabrica.bracos[id]
			if b.segurando == "" or not mapa.estruturas.has(id):
				continue
			var e: Dictionary = mapa.estruturas[id]
			var fr := Vector2(Grade.DIRECOES[Construtor.fluxo_da_rot(e.rot)])
			var cc := Vector2(e.minimo) + Vector2(0.5, 0.5)
			var a := clampf(b.fase() * 2.0, 0.0, 1.0)
			var p := (cc - fr * 0.75).lerp(cc + fr * 0.75, a)
			if not indice.has(b.segurando):
				indice[b.segurando] = tipos.size()
				tipos.append(b.segurando)
			tipo.append(indice[b.segurando])
			pos.append(p.x)
			pos.append(0.55 + 0.25 * sin(a * PI))
			pos.append(-p.y)
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


## Quadrado (plano da grade) que cobre o que a câmera vê, com folga.
func _area_vista(cam: CameraJogo) -> Rect2:
	if cam == null:
		return Rect2()
	var tam := get_viewport().get_visible_rect().size
	var meia_alt := cam.distancia * tan(deg_to_rad(cam.fov) / 2.0) / maxf(sin(cam.inclinacao()), 0.3)
	var raio := Vector2(meia_alt * tam.x / maxf(tam.y, 1.0), meia_alt).length() * 1.15
	var c := Vector2(cam.alvo.x, -cam.alvo.z)
	return Rect2(c - Vector2(raio, raio), Vector2(raio, raio) * 2.0)


func _instancia(item: String) -> MultiMeshInstance3D:
	if _mm.has(item):
		return _mm[item]
	if not Registro.modelos.has(item):
		return null
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = Materiais.malha_de(load(Registro.modelos[item].modelo))
	mm.instance_count = 64
	mm.visible_instance_count = 0
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF   # sombra de item miúdo não compensa
	add_child(mmi)
	_mm[item] = mmi
	return mmi
