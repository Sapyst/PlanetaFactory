extends Caso
## Esteiras e braços vindos dos estudos (arte/estudos/conv_esteiras_bracos.py): o que o jogo usa deles.
##  - esteiras em lote: uma malha só; lona "P_Esteira" rolando pelo shader, com UV no 1º canal, chegando às portas
##    ITEM na altura do item (0,16) e com o passo das ranhuras casando na borda com a vizinha;
##  - braços: partes e pivôs da IK — o pulso chega aonde o Animador manda (atrás e na frente), a garra fica de pé,
##    o braço longo estica o braço 2 e os pistões da lança seguem alinhados.

const LOTE := ["esteira_reta", "esteira_curva_dir", "esteira_curva_esq", "esteira_inicio", "esteira_fim",
		"esteira_juncao", "esteira_rampa", "esteira_tunel_entrada", "esteira_tunel_saida"]


func _cena(nome: String) -> Node3D:
	return (load(Registro.modelos[nome].modelo) as PackedScene).instantiate() as Node3D


func test_esteiras_uma_malha_com_lona() -> void:
	for nome in LOTE:
		var c := _cena(nome)
		igual(c.find_children("*", "MeshInstance3D", true, false).size(), 1, "%s: uma malha só (lote)" % nome)
		c.free()
		var m := Materiais.malha_de(load(Registro.modelos[nome].modelo))
		var lona := -1
		for s in m.get_surface_count():
			var mat := m.surface_get_material(s) as ShaderMaterial
			if mat != null and mat.resource_name == "P_Esteira":
				lona = s
		if not verificar(lona >= 0, "%s: tem a lona P_Esteira" % nome):
			continue
		var mat := m.surface_get_material(lona) as ShaderMaterial
		perto(float(mat.get_shader_parameter("rolagem")), Materiais.VELOCIDADE_ESTEIRA, 1e-4, "%s: lona rola" % nome)
		verificar((m.surface_get_format(lona) & Mesh.ARRAY_FORMAT_TEX_UV2) == 0, "%s: UV da lona no 1º canal" % nome)
		var arr := m.surface_get_arrays(lona)
		var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
		for p in Registro.modelos[nome].portas:
			if p.tipo != "ITEM" or (nome == "esteira_juncao" and p.io == "SAI"):
				continue
			var alvo := Vector3(p.pos[0], p.pos[2] - 0.004, -p.pos[1])    # Blender (x, y, z) → Godot (x, z, −y)
			var achou := false
			for i in vs.size():
				var d := vs[i] - alvo
				if absf(d.x * p.dir[0]) + absf(d.z * p.dir[1]) < 0.012 and absf(d.y) < 0.012:
					achou = true
					# 4 ranhuras por metro: na borda a fase é inteira (casa com a peça vizinha)
					var fase := fposmod(uvs[i].y * 4.0 + 0.5, 1.0) - 0.5
					perto(fase, 0.0, 0.02, "%s: ranhura casa na porta %s" % [nome, p.nome])
					break
			verificar(achou, "%s: lona chega na porta %s a 0,16" % [nome, p.nome])


func _global(n: Node3D) -> Transform3D:
	var t := n.transform
	var p := n.get_parent()
	while p is Node3D:
		t = (p as Node3D).transform * t
		p = p.get_parent()
	return t


func _parte(c: Node3D, nome: String, parte: String) -> Node3D:
	return c.find_child("%s_%s" % [nome, parte], true, false) as Node3D


func test_bracos_ik() -> void:
	for nome in ["braco", "braco_rapido", "braco_longo"]:
		var c := _cena(nome)
		for p in ["base", "giro", "braco1", "braco2", "garra"]:
			verificar(_parte(c, nome, p) != null, "%s: parte %s" % [nome, p])
		var a := Animador.new()
		a.modelo = nome
		var alc := float(Registro.estruturas.get(nome, {}).get("alcance", 1))
		a.pega = Vector2(alc, 0.42)
		a.solta = Vector2(alc, 0.62)
		c.add_child(a)
		a._ready()
		var dz := float(Registro.modelos[nome].get("garra", {}).get("pulso_dz", 0.0))
		var g := _parte(c, nome, "garra")
		var camisa := _parte(c, nome, "camisa")
		var haste := _parte(c, nome, "haste")
		var desvio := 0.0
		if camisa != null:
			var eixo0 := _global(camisa).basis * Vector3.FORWARD
			desvio = eixo0.signed_angle_to(_global(haste).origin - _global(camisa).origin, Vector3.RIGHT)
		for caso in [[0.0, a.pega, 1.0], [0.5, a.solta, -1.0]]:
			a.fase_braco = caso[0]
			a._braco_mecanico()
			var w := _global(g)
			var alvo: Vector2 = caso[1]
			# fase 0: pulso atrás (sul, +z no Godot); fase 0,5: na frente (norte, −z)
			perto(w.origin.z * caso[2], alvo.x, 0.02, "%s fase %.1f: pulso na distância" % [nome, caso[0]])
			perto(w.origin.x, 0.0, 0.01, "%s fase %.1f: pulso no eixo" % [nome, caso[0]])
			perto(w.origin.y, alvo.y + dz, 0.02, "%s fase %.1f: pulso na altura" % [nome, caso[0]])
			perto(w.basis.y.dot(Vector3.UP), 1.0, 0.01, "%s fase %.1f: garra de pé" % [nome, caso[0]])
			if camisa != null:
				var eixo := _global(camisa).basis * Vector3.FORWARD
				var ang := eixo.signed_angle_to(_global(haste).origin - _global(camisa).origin, _global(camisa).basis.x)
				perto(ang, desvio, 0.02, "%s fase %.1f: camisa mira a haste" % [nome, caso[0]])
		if nome == "braco_longo":
			verificar(_parte(c, nome, "estagio2").position.length() > 0.2, "braço longo: braço 2 esticado no alcance de 2")
		c.free()
