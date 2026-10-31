extends Caso
## Os 5 modelos do pedido 2 (arte/estudos/conv_antigos.py; docs/BRIEF_ANTIGRAVITY_2.md): peso, medidas e encaixes de que
## o jogo depende (emenda da plataforma, quadris e pernas da aranha).


func _malhas(nome: String) -> Array:
	var c: Node3D = (load(Registro.modelos[nome].modelo) as PackedScene).instantiate()
	var saida := []
	for m in c.find_children("*", "MeshInstance3D", true, false):
		saida.append(_no_modelo(m, c) * (m as MeshInstance3D).mesh.get_faces())
	var mats := []
	for m in c.find_children("*", "MeshInstance3D", true, false):
		for s in (m as MeshInstance3D).mesh.get_surface_count():
			mats.append((m as MeshInstance3D).mesh.surface_get_material(s).resource_name)
	c.free()
	return [saida, mats]


func _no_modelo(n: Node, raiz: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	while n != raiz:
		t = (n as Node3D).transform * t
		n = n.get_parent()
	return t


func _pontos(nome: String) -> PackedVector3Array:
	var p := PackedVector3Array()
	for f in _malhas(nome)[0]:
		p.append_array(f)
	return p


func _caixa(p: PackedVector3Array) -> AABB:
	var b := AABB(p[0], Vector3.ZERO)
	for v in p:
		b = b.expand(v)
	return b


func test_peso_pedido() -> void:
	for par in [["plataforma_agua", 600], ["ponte_agua", 400], ["poca_seiva", 300], ["aranha_corpo", 1500], ["aranha_femur", 200], ["aranha_tibia", 150], ["ninho_aranha", 5000]]:
		var n := _pontos(par[0]).size() / 3
		verificar(n <= par[1], "%s: %d tris, limite %d" % [par[0], n, par[1]])
		igual(int(Registro.modelos[par[0]].tris), n, "%s: json bate com o .glb" % par[0])
		verificar(str(Registro.modelos[par[0]].get("estudo", "")).begins_with("estudo_"), "%s: veio do estudo" % par[0])


func test_plataforma_emenda() -> void:
	var b := _caixa(_pontos("plataforma_agua"))
	perto(b.position.y, 0.0, 0.001, "pés no leito")
	perto(b.end.y, DesenhoPlataformas.ERGUIDO, 0.001, "topo do deque em ERGUIDO: chão da construção")
	for eixo in [0, 2]:
		perto(b.position[eixo], -0.5, 0.001, "encosta na vizinha (−)")
		perto(b.end[eixo], 0.5, 0.001, "encosta na vizinha (+)")
	var cantos := 0
	for v in _pontos("plataforma_agua"):
		if absf(v.y - DesenhoPlataformas.ERGUIDO) < 0.001 and absf(absf(v.x) - 0.5) < 0.001 and absf(absf(v.z) - 0.5) < 0.001:
			cantos += 1
	verificar(cantos >= 4, "o topo vai até os 4 cantos: sem fresta (%d)" % cantos)


func test_ponte_emenda_no_fluxo() -> void:
	var p := _pontos("ponte_agua")
	var b := _caixa(p)
	perto(b.position.z, -0.5, 0.001, "emenda ao sul")
	perto(b.end.z, 0.5, 0.001, "emenda ao norte")
	perto(b.position.y, 0.0, 0.001, "pés no leito")
	var deque := 0
	for v in p:
		if absf(absf(v.x) - 0.47) < 0.001 and absf(v.y - DesenhoPlataformas.ERGUIDO) < 0.001 and absf(absf(v.z) - 0.5) < 0.001:
			deque += 1
	verificar(deque >= 4, "deque, onde a esteira passa, no chão (%d cantos)" % deque)


func test_poca_rasa() -> void:
	var b := _caixa(_pontos("poca_seiva"))
	verificar(b.size.y <= 0.09, "bomba senta nela: %.3f m" % b.size.y)
	verificar(b.size.x <= 0.9 and b.size.z <= 0.9, "menor que o tile: %s" % b.size)
	verificar("P_Seiva" in _malhas("poca_seiva")[1], "seiva com material próprio (brilho molhado)")


func test_quadris_no_corpo() -> void:
	var p := _pontos("aranha_corpo")
	for q in MarchaAranha.QUADRIS:
		var ponto := Vector3(q.x, MarchaAranha.QUADRIL_Z, -q.y)
		var d := INF
		for v in p:
			d = minf(d, Vector2(v.x, v.z).distance_to(Vector2(ponto.x, ponto.z)) + absf(v.y - ponto.y) * 0.5)
		verificar(d < 0.12, "mancal no quadril %s (%.3f m)" % [q, d])
	verificar("P_OlhoInimigo" in _malhas("aranha_corpo")[1], "olhos que a fúria acha pelo nome")
	var b := _caixa(p)
	verificar(b.position.y >= -0.01 and b.position.y < MarchaAranha.QUADRIL_Z, "origem no chão, sob o centro")
	verificar(b.end.z - b.position.z < 2.0 and b.end.x - b.position.x < 1.1, "tamanho do pedido: %s" % b.size)


func test_pernas_nao_descolam() -> void:
	var f := _caixa(_pontos("aranha_femur"))
	verificar(f.position.x < 0.0 and f.end.x > MarchaAranha.FEMUR, "fêmur cobre do quadril ao joelho: %s" % f)
	var pt := _pontos("aranha_tibia")
	var t := _caixa(pt)
	verificar(t.position.x < 0.0, "tíbia começa no joelho")
	perto(t.end.x, MarchaAranha.TIBIA, 0.005, "ponta da tíbia é o pé")
	var ponta := 0.0
	var meio := 0.0
	for v in pt:
		if v.x > MarchaAranha.TIBIA - 0.01:
			ponta = maxf(ponta, Vector2(v.y, v.z).length())
		elif v.x > 0.5:
			meio = maxf(meio, Vector2(v.y, v.z).length())
	verificar(ponta < 0.02 and ponta < meio, "o pé é a agulha fina, não a base do cone: %.3f" % ponta)


func test_aranha_montada_coerente() -> void:
	var soma := 6 * (int(Registro.modelos.aranha_femur.tris) + int(Registro.modelos.aranha_tibia.tris)) + int(Registro.modelos.aranha_corpo.tris)
	igual(int(Registro.modelos.aranha_montada.tris), soma, "prévia = corpo + 6 pernas")


func test_ninho_cabe_e_anima() -> void:
	var md: Dictionary = Registro.modelos["ninho_aranha"]
	var b := _caixa(_pontos("ninho_aranha"))
	verificar(b.position.x >= -1.5 and b.end.x <= 1.5 and b.position.z >= -1.5 and b.end.z <= 1.5, "dentro dos 3×3: %s" % b)
	verificar(b.size.y >= 2.0 and b.size.y <= 3.0, "altura de 2 a 3 m: %.2f" % b.size.y)
	verificar(md.get("anima", false), "tem animação")
	var c: Node3D = (load(md.modelo) as PackedScene).instantiate()
	var tem := false
	for p in c.find_children("*", "AnimationPlayer", true, false):
		tem = tem or (p as AnimationPlayer).has_animation("trabalho")
	c.free()
	verificar(tem, "laço de 4 s para o Animador")
