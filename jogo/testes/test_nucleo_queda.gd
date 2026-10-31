extends Caso
## Chegada do núcleo (fase 2.6; estudo_nucleo_queda.py via arte/estudos/conv_nucleo.py): a cápsula de reentrada da
## abertura do jogo novo, com a animação "chegada" do estudo (10 s; impacto no quadro 60; no fim, a pose do laço do
## núcleo do jogo). A descida em si é da abertura (cenas/abertura.gd), por isso a cápsula fica na origem do modelo.


func test_modelo_da_chegada() -> void:
	var md: Dictionary = Registro.modelos.get("nucleo_queda", {})
	verificar(not md.is_empty(), "modelo da chegada sincronizado")
	if md.is_empty():
		return
	igual(md.get("estudo", ""), "estudo_nucleo_queda.py", "convertido do estudo da queda")
	igual(md.get("tipo", ""), "deco", "não é peça de construir (só a abertura usa)")
	igual(Registro.area("nucleo_queda"), Registro.area("nucleo"), "mesma área do núcleo")
	verificar(md.get("anima", false), "tem peças móveis")
	verificar(not Registro.estruturas.has("nucleo_queda"), "não entra nas regras de estrutura")
	var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
	var ap: AnimationPlayer = null
	for p in cena.find_children("*", "AnimationPlayer", true, false):
		if (p as AnimationPlayer).has_animation("chegada"):
			ap = p
	verificar(ap != null, "animação chegada")
	if ap != null:
		perto(ap.get_animation("chegada").length, 10.0, 0.1, "10 s (240 quadros a 24 qps)")
		verificar(not ap.has_animation("trabalho"), "não é laço de máquina")
	verificar(float(md.dims[2]) < 4.0, "cápsula parada na origem (sem a trajetória de 38 m): altura %.2f" % md.dims[2])
	cena.free()


func test_abertura_usa_a_capsula() -> void:
	var ab := Abertura.new()
	var q := ab._instancia_queda()
	verificar(not q.is_empty(), "a abertura acha a cápsula")
	if not q.is_empty():
		verificar(q[1] is AnimationPlayer, "com o tocador da animação")
		(q[0] as Node).free()
	verificar(Abertura.T_FIM > Abertura.T_CHAO + 7.5, "a abertura dura até a cápsula virar núcleo (impacto + 7,5 s)")
	perto(Abertura.Q_IMPACTO_S, 59.0 / 24.0, 1e-6, "impacto no quadro 60 do estudo")
	ab.free()


## Caixa de um modelo numa pose da animação, amostrando as trilhas (os testes rodam fora da árvore de cena). O que a escala
## quase zero esconde fica de fora.
func _caixa_pose(nome: String, anim: String, tempo: float) -> AABB:
	var cena: Node3D = (load(Registro.modelos[nome].modelo) as PackedScene).instantiate()
	for p in cena.find_children("*", "AnimationPlayer", true, false):
		var ap := p as AnimationPlayer
		if not ap.has_animation(anim):
			continue
		var a := ap.get_animation(anim)
		var raiz := ap.get_node(ap.root_node)
		for k in a.get_track_count():
			var no := raiz.get_node_or_null(NodePath(str(a.track_get_path(k)).get_slice(":", 0))) as Node3D
			if no == null:
				continue
			match a.track_get_type(k):
				Animation.TYPE_POSITION_3D:
					no.position = a.position_track_interpolate(k, tempo)
				Animation.TYPE_ROTATION_3D:
					no.quaternion = a.rotation_track_interpolate(k, tempo)
				Animation.TYPE_SCALE_3D:
					no.scale = a.scale_track_interpolate(k, tempo)
	var cx := AABB()
	var vazia := true
	for g in cena.find_children("*", "MeshInstance3D", true, false):
		var mi := g as MeshInstance3D
		var t := Transform3D.IDENTITY
		var n: Node = mi
		while n != cena:
			t = (n as Node3D).transform * t
			n = n.get_parent()
		if t.basis.get_scale().length() < 0.01:
			continue
		var b: AABB = t * mi.get_aabb()
		cx = b if vazia else cx.merge(b)
		vazia = false
	cena.free()
	return cx


func test_corpo_assado_nao_chapado() -> void:
	var cena: Node3D = (load(Registro.modelos.nucleo_queda.modelo) as PackedScene).instantiate()
	for g in cena.find_children("*", "MeshInstance3D", true, false):
		var mi := g as MeshInstance3D
		var nome: String = mi.mesh.surface_get_material(0).resource_name
		if nome.begins_with("P_Fogo"):
			verificar(mi.mesh.get_faces().size() / 3 < 400, "%s: luz pequena; o corpo da cápsula é assado (%d)" % [mi.name, mi.mesh.get_faces().size() / 3])
	cena.free()


func test_sem_pulo_na_troca() -> void:
	var cap := _caixa_pose("nucleo_queda", "chegada", 9.99)
	var nuc := _caixa_pose("nucleo", "trabalho", 0.0)
	verificar(cap.position.distance_to(nuc.position) < 0.15 and cap.end.distance_to(nuc.end) < 0.15,
			"último quadro da cápsula %s bate com o núcleo %s" % [cap, nuc])
	var fechada := _caixa_pose("nucleo_queda", "chegada", Abertura.Q_FECHADA_S)
	verificar(fechada.size.x < 4.0 and fechada.size.y < 4.0, "fechada, nada espalhado em volta: %s" % fechada)
	var ogiva_fora := _caixa_pose("nucleo_queda", "chegada", 6.0)
	verificar(ogiva_fora.end.y < 3.5, "a ogiva ejetada não fica parada no ar: %s" % ogiva_fora)
