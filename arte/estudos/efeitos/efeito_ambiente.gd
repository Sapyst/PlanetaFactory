class_name EfeitoAmbiente
extends "res://efeito_base.gd"
## Efeitos de brilho e ambiente com lógica de conceito físico no mundo (Parte B — PlanetaFactory).
## Cada efeito nasce de uma fonte física visível no cenário (jazida, fungo, cogumelo, flor, água, solo seco,
## poça de seiva, toco queimado ou fissura térmica) — nunca parecendo filtro colado na tela.

@export_enum(
	"brilho_jazida_cristal",
	"faisca_fungo_noite",
	"esporos_cogumelo",
	"vagalumes_flor",
	"reflexo_agua",
	"poeira_vento",
	"vapor_seiva",
	"brasa_queimado",
	"geiser_termico"
)
var tipo_ambiente: String = "brilho_jazida_cristal"

var _prop_fonte: Node3D
var _mmi_a: MultiMeshInstance3D
var _mmi_b: MultiMeshInstance3D
var _malha_agua: MeshInstance3D


func RazaoConceito() -> String:
	match tipo_ambiente:
		"brilho_jazida_cristal":
			return "A jazida de cristal exposta refrata a luz do sol/lua pelas faces do geodo e desprende micro-prismas luminosos pelo calor do solo."
		"faisca_fungo_noite":
			return "À noite, o resfriamento do ar faz as drusas de cristal no chapéu do fungo descarregarem eletricidade estática para as raízes."
		"esporos_cogumelo":
			return "O chapéu aquecido do cogumelo gigante libera nuvens lentas de esporos bioluminescentes pelas lamelas inferiores para dispersão pelo vento."
		"vagalumes_flor":
			return "Ao anoitecer, o cálice bioluminescente da flor luminosa atrai enxames de vaga-lumes que orbitam as pétalas em busca de néctar."
		"reflexo_agua":
			return "A água rasa corrente colide contra seixos e rochas de margem, criando cristas onduladas e esteiras de espuma que refletem a luz."
		"poeira_vento":
			return "Rajadas de vento rasante varrem a crosta seca do deserto e arrancam grãos de areia e redemoinhos de poeira ao redor dos pedregulhos."
		"vapor_seiva":
			return "A decomposição orgânica no fundo da poça de seiva aquece o líquido viscoso, formando bolhas que estouram em fiapos de vapor verde-dourado."
		"brasa_queimado":
			return "Tocos carbonizados e cinzas quentes no mato recém-queimado ainda guardam calor interno, soltando fagulhas vivas e fumaça fina quando o vento sopra."
		"geiser_termico":
			return "Fissuras geológicas ao pé das montanhas acumulam pressão subterrânea e sopram jatos periódicos de vapor mineral quente e cascalho."
	return ""


func _construir_efeito() -> void:
	_total_particulas = 0
	duracao = 1.6
	intervalo_loop = 1.6

	_prop_fonte = Node3D.new()
	add_child(_prop_fonte)

	match tipo_ambiente:
		"brilho_jazida_cristal":
			# Geodo físico de cristal com 6 pontas turquesa no chão
			for i in range(6):
				var cr := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.01
				cm.bottom_radius = 0.09 - float(i) * 0.008
				cm.height = 0.48 - float(i) * 0.04
				cr.mesh = cm
				var ang: float = float(i) * (TAU / 6.0)
				cr.position = Vector3(cos(ang) * 0.22, 0.18, sin(ang) * 0.22)
				cr.rotation_degrees = Vector3(sin(ang) * 24.0, 0.0, -cos(ang) * 24.0)
				cr.material_override = criar_mat_solido(Color(0.22, 0.85, 0.92), 0.18, 0.2, Color(0.25, 0.92, 1.0), 2.8)
				_prop_fonte.add_child(cr)
			_mmi_a = criar_multimesh_particulas(48, malha_lasca(Vector3(0.045, 0.045, 0.09)),
				criar_mat_particula(Color(0.55, 0.98, 1.0), Color(0.18, 0.65, 0.95), 5.2, 0.15))

		"faisca_fungo_noite":
			modo_noturno = true
			# Estipe e chapéu de fungo-cristal físico + drusas no topo
			var caule := MeshInstance3D.new()
			var cc := CylinderMesh.new()
			cc.top_radius = 0.10
			cc.bottom_radius = 0.16
			cc.height = 1.35
			caule.mesh = cc
			caule.position = Vector3(0, 0.67, 0)
			caule.material_override = criar_mat_solido(Color(0.36, 0.28, 0.42), 0.80, 0.0)
			_prop_fonte.add_child(caule)
			var chap := MeshInstance3D.new()
			chap.mesh = malha_octaedro(0.52, 0.48)
			chap.position = Vector3(0, 1.38, 0)
			chap.material_override = criar_mat_solido(Color(0.28, 0.16, 0.40), 0.65, 0.1, Color(0.20, 0.55, 0.75), 0.8)
			_prop_fonte.add_child(chap)
			_mmi_a = criar_multimesh_particulas(54, malha_lasca(Vector3(0.035, 0.035, 0.15)),
				criar_mat_particula(Color(0.45, 0.95, 1.0), Color(0.55, 0.25, 1.0), 6.0, 0.2))

		"esporos_cogumelo":
			# Cogumelo gigante físico liberando esporos por baixo do chapéu
			var caule := MeshInstance3D.new()
			var cc := CylinderMesh.new()
			cc.top_radius = 0.12
			cc.bottom_radius = 0.18
			cc.height = 1.25
			caule.mesh = cc
			caule.position = Vector3(0, 0.62, 0)
			caule.material_override = criar_mat_solido(Color(0.55, 0.48, 0.58), 0.82, 0.0)
			_prop_fonte.add_child(caule)
			var chap := MeshInstance3D.new()
			chap.mesh = malha_octaedro(0.58, 0.45)
			chap.position = Vector3(0, 1.28, 0)
			chap.material_override = criar_mat_solido(Color(0.45, 0.20, 0.42), 0.72, 0.0, Color(0.42, 0.85, 0.25), 1.2)
			_prop_fonte.add_child(chap)
			_mmi_a = criar_multimesh_particulas(64, malha_octaedro(0.055, 1.0),
				criar_mat_particula(Color(0.65, 0.95, 0.30), Color(0.85, 0.45, 0.95), 3.8, 0.4, 6.0))

		"vagalumes_flor":
			modo_noturno = true
			# 3 flores luminosas físicas no solo
			for i in range(3):
				var ang: float = float(i) * (TAU / 3.0) + 0.2
				var haste := MeshInstance3D.new()
				var ch := CylinderMesh.new()
				ch.top_radius = 0.02
				ch.bottom_radius = 0.035
				ch.height = 0.42
				haste.mesh = ch
				haste.position = Vector3(cos(ang) * 0.35, 0.21, sin(ang) * 0.35)
				haste.material_override = criar_mat_solido(Color(0.22, 0.45, 0.18), 0.8, 0.0)
				_prop_fonte.add_child(haste)
				var bulbo := MeshInstance3D.new()
				bulbo.mesh = malha_octaedro(0.09, 1.1)
				bulbo.position = Vector3(cos(ang) * 0.35, 0.44, sin(ang) * 0.35)
				bulbo.material_override = criar_mat_solido(Color(0.35, 0.95, 0.85), 0.2, 0.0, Color(0.35, 0.98, 0.85), 3.5)
				_prop_fonte.add_child(bulbo)
			_mmi_a = criar_multimesh_particulas(40, malha_octaedro(0.042, 1.2),
				criar_mat_particula(Color(0.65, 1.0, 0.35), Color(0.20, 0.95, 0.85), 5.8, 0.2))

		"reflexo_agua":
			# Leito de água corrente com shader de ondas/reflexo + 2 rochas de margem no meio da correnteza
			_malha_agua = MeshInstance3D.new()
			var pm := PlaneMesh.new()
			pm.size = Vector2(4.2, 2.8)
			pm.subdivide_width = 32
			pm.subdivide_depth = 24
			_malha_agua.mesh = pm
			_malha_agua.position = Vector3(0, 0.04, 0)
			var sm_agua := ShaderMaterial.new()
			sm_agua.shader = SH_AGUA
			_malha_agua.material_override = sm_agua
			_prop_fonte.add_child(_malha_agua)
			for p_rocha in [Vector3(-0.35, 0.12, 0.0), Vector3(0.48, 0.10, -0.22)]:
				var ro := MeshInstance3D.new()
				ro.mesh = malha_octaedro(0.26, 0.55)
				ro.position = p_rocha
				ro.material_override = criar_mat_solido(Color(0.22, 0.24, 0.22), 0.35, 0.2)
				_prop_fonte.add_child(ro)
			_mmi_a = criar_multimesh_particulas(44, malha_lasca(Vector3(0.06, 0.02, 0.14)),
				criar_mat_particula(Color(0.90, 0.98, 1.0), Color(0.35, 0.82, 0.95), 3.6, 0.15))

		"poeira_vento":
			# Pedregulhos secos de deserto + nuvem rasteira de poeira e grãos de areia varridos pelo vento
			for p_r in [Vector3(-0.65, 0.16, -0.2), Vector3(0.45, 0.12, 0.25)]:
				var ro := MeshInstance3D.new()
				ro.mesh = malha_octaedro(0.28, 0.65)
				ro.position = p_r
				ro.material_override = criar_mat_solido(Color(0.55, 0.44, 0.28), 0.90, 0.0)
				_prop_fonte.add_child(ro)
			_mmi_a = criar_multimesh_particulas(72, malha_octaedro(0.13, 0.65),
				criar_mat_particula(Color(0.82, 0.68, 0.42), Color(0.52, 0.42, 0.26), 0.4, 0.92, 5.0))

		"vapor_seiva":
			# Poça brilhante de seiva orgânica no chão + bolhas e colunas suaves de vapor
			var poca := MeshInstance3D.new()
			var cp := CylinderMesh.new()
			cp.top_radius = 0.85
			cp.bottom_radius = 0.90
			cp.height = 0.05
			poca.mesh = cp
			poca.position = Vector3(0, 0.025, 0)
			poca.material_override = criar_mat_solido(Color(0.38, 0.78, 0.22), 0.15, 0.1, Color(0.42, 0.88, 0.20), 2.2)
			_prop_fonte.add_child(poca)
			_mmi_a = criar_multimesh_particulas(52, malha_octaedro(0.11, 1.05),
				criar_mat_particula(Color(0.62, 0.95, 0.35), Color(0.25, 0.52, 0.22), 2.2, 0.65, 5.5))

		"brasa_queimado":
			# Tocos queimados e leito de cinza incandescente soltando brasas vivas e fumaça fina
			for i in range(2):
				var toco := MeshInstance3D.new()
				var ct := CylinderMesh.new()
				ct.top_radius = 0.14 - float(i) * 0.03
				ct.bottom_radius = 0.22 - float(i) * 0.04
				ct.height = 0.48 - float(i) * 0.12
				toco.mesh = ct
				toco.position = Vector3(-0.28 + float(i) * 0.58, 0.22, -0.1 + float(i) * 0.2)
				toco.material_override = criar_mat_solido(Color(0.12, 0.10, 0.10), 0.92, 0.0, Color(0.95, 0.28, 0.05), 1.4)
				_prop_fonte.add_child(toco)
			_mmi_a = criar_multimesh_particulas(40, malha_lasca(Vector3(0.035, 0.035, 0.08)),
				criar_mat_particula(Color(1.0, 0.78, 0.22), Color(0.95, 0.22, 0.04), 5.5, 0.3))
			_mmi_b = criar_multimesh_particulas(28, malha_octaedro(0.12, 1.1),
				criar_mat_particula(Color(0.32, 0.28, 0.26), Color(0.15, 0.14, 0.14), 0.3, 0.92, 5.5))

		"geiser_termico":
			# Fissura cônica rochosa ao pé da montanha soprando jato periódico de vapor mineral quente
			var cone := MeshInstance3D.new()
			var cc := CylinderMesh.new()
			cc.top_radius = 0.22
			cc.bottom_radius = 0.52
			cc.height = 0.36
			cone.mesh = cc
			cone.position = Vector3(0, 0.18, 0)
			cone.material_override = criar_mat_solido(Color(0.24, 0.22, 0.20), 0.88, 0.1, Color(0.95, 0.45, 0.12), 0.8)
			_prop_fonte.add_child(cone)
			_mmi_a = criar_multimesh_particulas(64, malha_octaedro(0.14, 1.15),
				criar_mat_particula(Color(0.88, 0.94, 0.98), Color(0.45, 0.52, 0.58), 1.4, 0.82, 5.0))


func _atualizar_quadro(u: float) -> void:
	var mm := _mmi_a.multimesh

	match tipo_ambiente:
		"brilho_jazida_cristal":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 17 + 3)
				var fase: float = fmod(u + s, 1.0)
				var ang: float = float(i) * 0.52 + fase * 2.2
				var r: float = (0.12 + 0.38 * hash_det(i * 7)) * (1.0 - fase * 0.35)
				var pos := Vector3(cos(ang) * r, 0.15 + fase * 1.15, sin(ang) * r)
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.55 + 0.65 * s))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(0.55, 0.98, 1.0, pulso))
				mm.set_instance_custom_data(i, Color(fase, pulso, 0.2, s))

		"faisca_fungo_noite":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 23 + 5)
				var fase: float = fmod(u * 1.5 + s, 1.0)
				var ang: float = float(i) * (TAU / 9.0) + sin(fase * TAU) * 0.35
				# Arco bioelétrico descendo da borda do chapéu (y=1.35) para as raízes (y=0.10)
				var r: float = 0.48 * sin(fase * PI) + 0.14
				var pos := Vector3(cos(ang) * r, lerpf(1.38, 0.12, fase), sin(ang) * r)
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.65 + 0.6 * s))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(0.45, 0.95, 1.0, pulso))
				mm.set_instance_custom_data(i, Color(fase, pulso, 0.3, s))

		"esporos_cogumelo":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 19 + 11)
				var fase: float = fmod(u + s, 1.0)
				var ang: float = float(i) * 0.48 + fase * 1.8
				var r: float = 0.28 + fase * 0.65 * (0.6 + 0.6 * hash_det(i * 13))
				var pos := Vector3(cos(ang) * r, 1.12 - 0.18 * sin(fase * PI) + fase * 0.55, sin(ang) * r)
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.6 + 0.6 * s))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(0.75, 0.98, 0.42, pulso))
				mm.set_instance_custom_data(i, Color(fase, pulso, 0.8, s))

		"vagalumes_flor":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 31 + 7)
				var fase: float = fmod(u + s, 1.0)
				var ang: float = float(i) * 0.65 + u * TAU + sin(fase * TAU) * 0.6
				var r: float = 0.22 + 0.58 * hash_det(i * 11)
				var pos := Vector3(cos(ang) * r, 0.25 + 0.55 * hash_det(i * 17) + 0.14 * sin(u * TAU * 2.0 + float(i)), sin(ang) * r)
				var pisca: float = 0.35 + 0.65 * pow(0.5 + 0.5 * sin(u * TAU * 2.0 + s * TAU), 2.0)
				var esc: float = (0.55 + 0.55 * s) * pisca
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(0.65, 1.0, 0.40, pisca))
				mm.set_instance_custom_data(i, Color(fase, pisca, 0.2, s))

		"reflexo_agua":
			if _malha_agua != null:
				var sm := _malha_agua.material_override as ShaderMaterial
				if sm != null:
					sm.set_shader_parameter("fase_manual", u * TAU)
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 13 + 9)
				var fase: float = fmod(u + s, 1.0)
				var x: float = lerpf(-1.7, 1.7, fase)
				var z: float = (hash_det(i * 29) - 0.5) * 1.6 + 0.15 * sin(fase * TAU * 2.0 + float(i))
				var pulso: float = sin(fase * PI)
				var pos := Vector3(x, 0.07 + 0.03 * pulso, z)
				var esc: float = maxf(0.001, pulso * (0.65 + 0.65 * s))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(esc * 1.8, esc * 0.4, esc)), pos))
				mm.set_instance_color(i, Color(0.90, 0.98, 1.0, pulso))
				mm.set_instance_custom_data(i, Color(fase, pulso, 0.2, s))

		"poeira_vento":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 17 + 5)
				var fase: float = fmod(u + s, 1.0)
				var x: float = lerpf(-2.0, 2.0, fase)
				var z: float = (hash_det(i * 23) - 0.5) * 1.8 + 0.28 * sin(fase * TAU + float(i))
				var y: float = 0.08 + 0.35 * sin(fase * PI) * hash_det(i * 7)
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.7 + 0.9 * s))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(esc * 1.5, esc * 0.6, esc)), Vector3(x, y, z)))
				mm.set_instance_color(i, Color(0.85, 0.72, 0.48, pulso * 0.85))
				mm.set_instance_custom_data(i, Color(fase, 0.4, 1.0, s))

		"vapor_seiva":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 29 + 3)
				var fase: float = fmod(u + s, 1.0)
				var ang: float = float(i) * 0.7 + fase * 1.2
				var r: float = 0.68 * sqrt(hash_det(i * 11))
				var eh_bolha: bool = (fase < 0.28)
				var y: float = 0.06 + (fase * 0.25 if eh_bolha else (fase - 0.28) * 1.35)
				var pos := Vector3(cos(ang) * r, y, sin(ang) * r)
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.55 if eh_bolha else (0.65 + fase * 0.85)))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(0.65, 0.96, 0.38, pulso))
				mm.set_instance_custom_data(i, Color(fase, 1.0 - fase * 0.6, 0.75, s))

		"brasa_queimado":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 19 + 1)
				var fase: float = fmod(u + s, 1.0)
				var centro_t := Vector3(-0.28 if (i % 2 == 0) else 0.30, 0.15, -0.1 if (i % 2 == 0) else 0.1)
				var pos: Vector3 = centro_t + Vector3(
					(hash_det(i * 7) - 0.5) * 0.45 + fase * 0.35,
					fase * (0.85 + s * 0.55),
					(hash_det(i * 13) - 0.5) * 0.45 + 0.12 * sin(fase * TAU * 2.0)
				)
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.55 + 0.6 * s))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(1.0, 0.75, 0.22, pulso))
				mm.set_instance_custom_data(i, Color(fase, 1.0 - fase * 0.4, 0.3, s))

			var mm_f := _mmi_b.multimesh
			for i in range(mm_f.instance_count):
				var s: float = hash_det(i * 23 + 9)
				var fase: float = fmod(u + s, 1.0)
				var centro_t := Vector3(-0.28 if (i % 2 == 0) else 0.30, 0.32, 0.0)
				var pos: Vector3 = centro_t + Vector3(fase * 0.45 + (s - 0.5) * 0.3, fase * 1.35, (hash_det(i * 11) - 0.5) * 0.35)
				var esc: float = sin(fase * PI) * (0.5 + fase * 0.95)
				mm_f.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.001, esc)), pos))
				mm_f.set_instance_color(i, Color(1.0, 1.0, 1.0, sin(fase * PI) * 0.75))
				mm_f.set_instance_custom_data(i, Color(fase, 0.2, 1.0, s))

		"geiser_termico":
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 17 + 13)
				var fase: float = fmod(u * 1.25 + s * 0.75, 1.0)
				var dir_j: Vector3 = dir_esfera_det(i, 0.38, Vector3.UP)
				var pos: Vector3 = Vector3(0, 0.32, 0) + dir_j * (fase * (1.45 + s * 0.85))
				var pulso: float = sin(fase * PI)
				var esc: float = maxf(0.001, pulso * (0.45 + fase * 1.25))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
				mm.set_instance_color(i, Color(0.92, 0.96, 1.0, pulso * 0.85))
				mm.set_instance_custom_data(i, Color(fase, maxf(0.0, 0.8 - fase), 0.95, s))
