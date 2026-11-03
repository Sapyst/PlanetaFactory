extends Caso
## Os 67 modelos de ambiente do pedido 4 (arte/estudos/estudo_amb_*.py; docs/BRIEF_ANTIGRAVITY_4.md): todos existem,
## cada um é uma malha só, a origem fica no centro da base (pé em y = 0), o .glb bate com o json e cabe no limite de
## triângulos de cada estudo (os limites são os do brief; nenhum foi subido).

const LIMITES := {"estudo_amb_arvores.py": 500, "estudo_amb_arvores_soltas.py": 400, "estudo_amb_plantas.py": 200,
		"estudo_amb_cogumelos.py": 600, "estudo_amb_rochas.py": 250, "estudo_amb_montanhas.py": 1200,
		"estudo_amb_jazidas.py": 300, "estudo_amb_itens.py": 120}
const TOTAL := 67
const FOLGA_PE := 0.02            ## m: a base pode ter uma lasca abaixo de zero (seixos, raízes), não mais que isso


func _ambiente() -> Array[String]:
	var out: Array[String] = []
	for nome in Registro.modelos:
		if str(Registro.modelos[nome].get("estudo", "")).begins_with("estudo_amb_"):
			out.append(nome)
	out.sort()
	return out


## Caixa e triângulos da primeira malha, com a transformação dos nós até a raiz (a raiz fica de fora, como no jogo).
func _malha(nome: String) -> Dictionary:
	var c: Node3D = (load(Registro.modelos[nome].modelo) as PackedScene).instantiate()
	var mis := c.find_children("*", "MeshInstance3D", true, false)
	var mi := mis[0] as MeshInstance3D
	var t := Transform3D.IDENTITY
	var n: Node = mi
	while n != c:
		t = (n as Node3D).transform * t
		n = n.get_parent()
	var tris := 0
	for s in mi.mesh.get_surface_count():
		tris += (mi.mesh.surface_get_arrays(s)[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
	var saida := {"malhas": mis.size(), "caixa": t * mi.mesh.get_aabb(), "tris": tris}
	c.free()
	return saida


func test_os_67_existem() -> void:
	var nomes := _ambiente()
	igual(nomes.size(), TOTAL, "67 modelos vindos dos estudos de ambiente")
	var estudos := {}
	for nome in nomes:
		var m: Dictionary = Registro.modelos[nome]
		verificar(ResourceLoader.exists(m.modelo), "%s: .glb existe (%s)" % [nome, m.modelo])
		verificar(LIMITES.has(m.estudo), "%s: estudo conhecido (%s)" % [nome, m.estudo])
		estudos[m.estudo] = true
		verificar(not bool(m.get("anima", false)), "%s: ambiente não anima" % nome)
	igual(estudos.size(), LIMITES.size(), "os 8 estudos estão representados")


func test_malha_unica_origem_na_base_e_triangulos() -> void:
	for nome in _ambiente():
		var m: Dictionary = Registro.modelos[nome]
		var d := _malha(nome)
		igual(d.malhas, 1, "%s: uma malha só" % nome)
		var b: AABB = d.caixa
		verificar(b.position.y >= -FOLGA_PE and b.position.y <= FOLGA_PE, "%s: pé em y = %.3f (origem na base)" % [nome, b.position.y])
		verificar(b.end.y > 0.05, "%s: tem altura (%.3f)" % [nome, b.end.y])
		var c := b.get_center()
		verificar(absf(c.x) < b.size.x * 0.25 + 0.01 and absf(c.z) < b.size.z * 0.25 + 0.01, "%s: origem no centro da base (centro em %.2f, %.2f)" % [nome, c.x, c.z])
		igual(int(m.tris), d.tris, "%s: json bate com o .glb" % nome)
		verificar(d.tris <= int(LIMITES[m.estudo]), "%s: %d tris, limite %d" % [nome, d.tris, LIMITES[m.estudo]])
		var dims: Array = m.get("dims", [])
		if igual(dims.size(), 3, "%s: dims no json" % nome):
			perto(float(dims[2]), b.size.y, 0.02, "%s: altura do json bate com a malha" % nome)
