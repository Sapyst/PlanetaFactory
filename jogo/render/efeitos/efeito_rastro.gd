class_name EfeitoRastro
extends "res://render/efeitos/efeito_base.gd"
## Efeito de rastro de tiro no mundo (8 armas do PlanetaFactory).
## Causa física: cada disparo sai do cano/bobina da arma na origem e viaja fisicamente até o alvo no destino.
## Cápsulas ejetadas já existem no jogo — portanto o bocal usa sopro curto sem cobrir a arma de fumaça.

@export_enum("metralhadora", "torre_energia", "lanca_foguetes", "foguete_enxame", "artilharia", "municao_perfurante", "municao_carregada", "drone_combate")
var tipo_arma: String = "metralhadora"

var _cano_prop: MeshInstance3D
var _alvo_prop: MeshInstance3D
var _projeteis: Array[MeshInstance3D] = []
var _feixes: Array[MeshInstance3D] = []
var _aneis_mach: Array[MeshInstance3D] = []
var _mmi_faiscas: MultiMeshInstance3D
var _mmi_fumaca: MultiMeshInstance3D
var _luz_bocal: OmniLight3D


func _construir_efeito() -> void:
	_total_particulas = 0
	_projeteis.clear()
	_feixes.clear()
	_aneis_mach.clear()

	origem_atual = Vector3(-2.35, 0.72, 0.0)
	destino_atual = Vector3(2.35, 0.58, 0.0)
	if tipo_arma == "drone_combate":
		origem_atual = Vector3(-2.15, 1.85, 0.0)

	# Prop físico na origem (cano da torreta ou chassi do drone) e alvo físico no destino
	_cano_prop = MeshInstance3D.new()
	var malha_c := CylinderMesh.new()
	malha_c.top_radius = 0.14
	malha_c.bottom_radius = 0.18
	malha_c.height = 0.55
	_cano_prop.mesh = malha_c
	_cano_prop.material_override = criar_mat_solido(Color(0.24, 0.27, 0.30), 0.55, 0.65)
	add_child(_cano_prop)

	_alvo_prop = MeshInstance3D.new()
	var malha_a := SphereMesh.new()
	malha_a.radius = 0.28
	malha_a.height = 0.48
	malha_a.radial_segments = 8
	malha_a.rings = 4
	_alvo_prop.mesh = malha_a
	_alvo_prop.material_override = criar_mat_solido(Color(0.28, 0.18, 0.22), 0.65, 0.35)
	add_child(_alvo_prop)

	if dentro_do_jogo or (get_parent() != null and get_parent() != get_tree().root):
		_cano_prop.visible = false
		_alvo_prop.visible = false


	match tipo_arma:
		"metralhadora":
			duracao = 0.45
			intervalo_loop = 0.65
			# 2 traçantes finos e rápidos em rajada + sopro leve no bocal (28 partículas)
			for i in range(2):
				var tr := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.018
				cm.bottom_radius = 0.028
				cm.height = 0.95
				tr.mesh = cm
				tr.material_override = criar_mat_feixe(Color(1.0, 0.96, 0.75), Color(1.0, 0.62, 0.12), 5.5, 4.0, 18.0)
				add_child(tr)
				_projeteis.append(tr)
			_mmi_faiscas = criar_multimesh_particulas(28, malha_lasca(Vector3(0.03, 0.03, 0.11)),
				criar_mat_particula(Color(1.0, 0.82, 0.30), Color(1.0, 0.40, 0.08), 4.5, 0.3))
			_luz_bocal = criar_luz_curta(Color(1.0, 0.78, 0.35), 3.8)

		"torre_energia":
			duracao = 0.85
			intervalo_loop = 1.15
			# Feixe energético central + espiral externa + 36 partículas ionizadas ao longo do feixe
			for i in range(2):
				var fx := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.045 if i == 0 else 0.095
				cm.bottom_radius = cm.top_radius
				cm.height = 1.0
				fx.mesh = cm
				var c_n := Color(0.90, 0.98, 1.0) if i == 0 else Color(0.20, 0.82, 1.0)
				var c_b := Color(0.15, 0.72, 1.0) if i == 0 else Color(0.08, 0.38, 0.95)
				fx.material_override = criar_mat_feixe(c_n, c_b, 6.0 if i == 0 else 3.2, 10.0 + i * 6.0, 20.0)
				add_child(fx)
				_feixes.append(fx)
			_mmi_faiscas = criar_multimesh_particulas(36, malha_octaedro(0.045, 1.6),
				criar_mat_particula(Color(0.45, 0.95, 1.0), Color(0.12, 0.50, 1.0), 5.0, 0.2))

		"lanca_foguetes":
			duracao = 0.95
			intervalo_loop = 1.30
			# Corpo do foguete + cone de chama + esteira densa de fumaça (48) e fagulhas de propelente (24) = 72 partículas
			var fog := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.025
			cm.bottom_radius = 0.065
			cm.height = 0.38
			fog.mesh = cm
			fog.material_override = criar_mat_solido(Color(0.75, 0.26, 0.18), 0.45, 0.4, Color(1.0, 0.55, 0.15), 2.5)
			add_child(fog)
			_projeteis.append(fog)
			_mmi_fumaca = criar_multimesh_particulas(48, malha_octaedro(0.13, 1.0),
				criar_mat_particula(Color(0.85, 0.52, 0.22), Color(0.32, 0.30, 0.28), 1.8, 0.88, 6.0))
			_mmi_faiscas = criar_multimesh_particulas(24, malha_lasca(Vector3(0.04, 0.04, 0.12)),
				criar_mat_particula(Color(1.0, 0.85, 0.35), Color(1.0, 0.35, 0.08), 5.2, 0.25))
			_luz_bocal = criar_luz_curta(Color(1.0, 0.60, 0.20), 4.5)

		"foguete_enxame":
			duracao = 1.0
			intervalo_loop = 1.35
			# 5 micro-foguetes serpenteando em espiral + 60 puffs de fumaça/chama (12 por míssil)
			for i in range(5):
				var mf := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.016
				cm.bottom_radius = 0.042
				cm.height = 0.24
				mf.mesh = cm
				mf.material_override = criar_mat_solido(Color(0.95, 0.65, 0.18), 0.4, 0.3, Color(1.0, 0.72, 0.20), 3.2)
				add_child(mf)
				_projeteis.append(mf)
			_mmi_fumaca = criar_multimesh_particulas(60, malha_octaedro(0.085, 1.0),
				criar_mat_particula(Color(1.0, 0.72, 0.28), Color(0.38, 0.36, 0.34), 2.4, 0.82, 7.0))

		"artilharia":
			duracao = 1.15
			intervalo_loop = 1.50
			# Granada pesada em arco balístico alto + anel de disparo no canhão + 56 partículas na trajetória parabólica
			var gran := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.045
			cm.bottom_radius = 0.085
			cm.height = 0.42
			gran.mesh = cm
			gran.material_override = criar_mat_solido(Color(0.35, 0.32, 0.28), 0.5, 0.6, Color(1.0, 0.48, 0.12), 2.8)
			add_child(gran)
			_projeteis.append(gran)
			_mmi_fumaca = criar_multimesh_particulas(40, malha_octaedro(0.14, 1.0),
				criar_mat_particula(Color(0.92, 0.58, 0.24), Color(0.28, 0.26, 0.25), 1.6, 0.90, 5.5))
			_mmi_faiscas = criar_multimesh_particulas(20, malha_lasca(Vector3(0.045, 0.045, 0.14)),
				criar_mat_particula(Color(1.0, 0.80, 0.30), Color(0.95, 0.32, 0.08), 4.8, 0.3))
			_luz_bocal = criar_luz_curta(Color(1.0, 0.65, 0.22), 5.2)

		"municao_perfurante":
			duracao = 0.55
			intervalo_loop = 0.80
			# Dardo cinético hipersônico + 3 anéis de choque de Mach no ar + 36 faíscas de atrito
			var dardo := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.008
			cm.bottom_radius = 0.038
			cm.height = 1.15
			dardo.mesh = cm
			dardo.material_override = criar_mat_feixe(Color(1.0, 0.95, 0.85), Color(1.0, 0.48, 0.15), 6.2, 3.0, 22.0)
			add_child(dardo)
			_projeteis.append(dardo)
			for i in range(3):
				var anel := MeshInstance3D.new()
				anel.mesh = malha_anel(0.18, 0.24)
				anel.material_override = criar_mat_feixe(Color(1.0, 0.88, 0.65), Color(1.0, 0.52, 0.18), 4.2, 4.0, 12.0)
				add_child(anel)
				_aneis_mach.append(anel)
			_mmi_faiscas = criar_multimesh_particulas(36, malha_lasca(Vector3(0.028, 0.028, 0.15)),
				criar_mat_particula(Color(1.0, 0.92, 0.60), Color(1.0, 0.45, 0.10), 5.5, 0.2))

		"municao_carregada":
			duracao = 0.78
			intervalo_loop = 1.05
			# Esfera de plasma sobrecarregada + feixe helicoidal + 44 descargas elétricas orbitando o tiro
			var nucleo := MeshInstance3D.new()
			nucleo.mesh = malha_octaedro(0.13, 1.35)
			nucleo.material_override = criar_mat_feixe(Color(0.92, 0.98, 1.0), Color(0.25, 0.68, 1.0), 6.5, 8.0, 24.0)
			add_child(nucleo)
			_projeteis.append(nucleo)
			var trilha := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.032
			cm.bottom_radius = 0.055
			cm.height = 1.0
			trilha.mesh = cm
			trilha.material_override = criar_mat_feixe(Color(0.65, 0.92, 1.0), Color(0.22, 0.48, 1.0), 4.2, 14.0, 25.0)
			add_child(trilha)
			_feixes.append(trilha)
			_mmi_faiscas = criar_multimesh_particulas(44, malha_lasca(Vector3(0.035, 0.035, 0.14)),
				criar_mat_particula(Color(0.55, 0.95, 1.0), Color(0.25, 0.42, 1.0), 5.8, 0.2))

		"drone_combate":
			duracao = 0.60
			intervalo_loop = 0.85
			# Rajada dupla de pulsos leves saindo do drone no alto em direção ao alvo no solo + 28 partículas
			for i in range(2):
				var pulso := MeshInstance3D.new()
				var cm := CylinderMesh.new()
				cm.top_radius = 0.022
				cm.bottom_radius = 0.032
				cm.height = 0.75
				pulso.mesh = cm
				pulso.material_override = criar_mat_feixe(Color(1.0, 0.92, 0.95), Color(1.0, 0.25, 0.42), 5.8, 6.0, 20.0)
				add_child(pulso)
				_projeteis.append(pulso)
			_mmi_faiscas = criar_multimesh_particulas(28, malha_octaedro(0.04, 1.5),
				criar_mat_particula(Color(1.0, 0.45, 0.55), Color(0.25, 0.85, 1.0), 4.8, 0.25))


func _orientar_cilindro(no: Node3D, p_ini: Vector3, p_fim: Vector3, compr_escala: float = 1.0) -> void:
	var delta: Vector3 = p_fim - p_ini
	var dist: float = maxf(0.001, delta.length())
	var dir: Vector3 = delta / dist
	var pos_meio: Vector3 = (p_ini + p_fim) * 0.5
	var up_ref: Vector3 = Vector3.UP if absf(dir.dot(Vector3.UP)) < 0.95 else Vector3.FORWARD
	var eixo_x: Vector3 = dir.cross(up_ref).normalized()
	var eixo_z: Vector3 = eixo_x.cross(dir).normalized()
	no.global_transform = Transform3D(Basis(eixo_x, dir * compr_escala, eixo_z), pos_meio)


func _pos_arco(p0: Vector3, p1: Vector3, t: float, alt_arco: float) -> Vector3:
	var p: Vector3 = p0.lerp(p1, t)
	p.y += 4.0 * alt_arco * t * (1.0 - t)
	return p


func _ao_reiniciar_ciclo() -> void:
	if dentro_do_jogo or (get_parent() != null and get_parent() != get_tree().root):
		if _cano_prop != null: _cano_prop.visible = false
		if _alvo_prop != null: _alvo_prop.visible = false
	if _mmi_faiscas != null:
		_mmi_faiscas.visible = true
	if _mmi_fumaca != null:
		_mmi_fumaca.visible = true


func _ao_terminar() -> void:
	for p in _projeteis:
		p.visible = false
	for f in _feixes:
		f.visible = false
	for a in _aneis_mach:
		a.visible = false
	if _mmi_faiscas != null:
		_mmi_faiscas.visible = false
	if _mmi_fumaca != null:
		_mmi_fumaca.visible = false
	if _luz_bocal != null:
		_luz_bocal.light_energy = 0.0


func _atualizar_quadro(u: float) -> void:
	var gp: Vector3 = global_position if is_inside_tree() else position
	var p0: Vector3 = origem_atual if dentro_do_jogo else gp + origem_atual
	var p1: Vector3 = destino_atual if dentro_do_jogo else gp + destino_atual
	var dir_tiro: Vector3 = (p1 - p0).normalized()

	# Posiciona os props físicos de origem e destino se estiver na vitrine
	if not dentro_do_jogo:
		_orientar_cilindro(_cano_prop, p0 - dir_tiro * 0.45, p0 + dir_tiro * 0.05, 1.0)
		if _alvo_prop.is_inside_tree():
			_alvo_prop.global_position = p1
		else:
			_alvo_prop.position = p1

	if _luz_bocal != null:
		if _luz_bocal.is_inside_tree():
			_luz_bocal.global_position = p0 + dir_tiro * 0.25
		else:
			_luz_bocal.position = p0 + dir_tiro * 0.25
		_luz_bocal.light_energy = maxf(0.0, 1.0 - u * 4.2) * 3.8

	match tipo_arma:
		"metralhadora":
			for i in range(_projeteis.size()):
				var ui: float = clampf((u - float(i) * 0.18) * 1.35, 0.0, 1.0)
				var pa: Vector3 = p0.lerp(p1, clampf(ui - 0.12, 0.0, 1.0))
				var pb: Vector3 = p0.lerp(p1, clampf(ui + 0.12, 0.0, 1.0))
				_projeteis[i].visible = (ui > 0.01 and ui < 0.99)
				_orientar_cilindro(_projeteis[i], pa, pb, 1.0)
			var mm := _mmi_faiscas.multimesh
			for i in range(mm.instance_count):
				var s: float = hash_det(i * 13 + 5)
				var na_chegada: bool = (i >= 14)
				var base_p: Vector3 = p1 if na_chegada else p0
				var tu: float = clampf((u - (0.35 if na_chegada else 0.0)) * 1.6, 0.0, 1.0)
				var v_dir: Vector3 = dir_esfera_det(i, 0.65, -dir_tiro if na_chegada else dir_tiro)
				var pos: Vector3 = base_p + v_dir * (tu * (0.55 + s * 0.85))
				var esc: float = maxf(0.001, (1.0 - tu) * (0.7 + s * 0.6))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos - gp))
				mm.set_instance_color(i, Color(1.0, 0.85, 0.35, 1.0 - tu))
				mm.set_instance_custom_data(i, Color(tu, 1.0 - tu * 0.6, 0.3, s))

		"torre_energia":
			var dist: float = p0.distance_to(p1)
			var vis_fx: bool = (u > 0.01 and u < 0.96)
			for i in range(_feixes.size()):
				_feixes[i].visible = vis_fx
				_orientar_cilindro(_feixes[i], p0, p1, dist)
				var sm := _feixes[i].material_override as ShaderMaterial
				if sm != null:
					sm.set_shader_parameter("progresso", u)
			var mm := _mmi_faiscas.multimesh
			_mmi_faiscas.visible = vis_fx
			for i in range(mm.instance_count):
				var frac: float = fmod(float(i) / float(mm.instance_count) + u * 1.4, 1.0)
				var ang: float = frac * TAU * 4.0 + float(i) * 0.7
				var raio_orb: float = 0.08 + 0.10 * sin(u * PI) * hash_det(i * 19)
				var ort1: Vector3 = dir_tiro.cross(Vector3.UP).normalized()
				var ort2: Vector3 = dir_tiro.cross(ort1).normalized()
				var pos: Vector3 = p0.lerp(p1, frac) + (ort1 * cos(ang) + ort2 * sin(ang)) * raio_orb
				var esc: float = sin(u * PI) * (0.7 + 0.5 * hash_det(i * 7))
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.01, esc)), pos - gp))
				mm.set_instance_color(i, Color(0.45, 0.95, 1.0, sin(u * PI)))
				mm.set_instance_custom_data(i, Color(frac, sin(u * PI), 0.4, hash_det(i)))

		"lanca_foguetes":
			var p_fog: Vector3 = _pos_arco(p0, p1, u, 0.35)
			var p_ant: Vector3 = _pos_arco(p0, p1, maxf(0.0, u - 0.04), 0.35)
			_projeteis[0].visible = (u > 0.01 and u < 0.98)
			_orientar_cilindro(_projeteis[0], p_ant, p_fog + (p_fog - p_ant).normalized() * 0.35, 1.0)
			var mm_f := _mmi_fumaca.multimesh
			for i in range(mm_f.instance_count):
				var t_nasc: float = float(i) / float(mm_f.instance_count) * 0.88
				var idade: float = clampf((u - t_nasc) / maxf(0.15, 1.0 - t_nasc), 0.0, 1.0)
				var vis: float = 1.0 if u >= t_nasc else 0.0
				var p_trilha: Vector3 = _pos_arco(p0, p1, t_nasc, 0.35) + dir_esfera_det(i, 0.9, Vector3.UP) * (idade * 0.42)
				var esc: float = vis * (0.45 + idade * 1.45) * (1.0 - idade * 0.45)
				mm_f.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.001, esc)), p_trilha - gp))
				mm_f.set_instance_color(i, Color(1.0, 1.0, 1.0, vis * (1.0 - idade * 0.85)))
				mm_f.set_instance_custom_data(i, Color(idade, maxf(0.0, 1.0 - idade * 2.2), 1.0, hash_det(i)))
			var mm_s := _mmi_faiscas.multimesh
			for i in range(mm_s.instance_count):
				var s: float = hash_det(i * 23 + 1)
				var atraso: float = fmod(u * 3.0 + s, 1.0)
				var pos_s: Vector3 = p_fog - dir_tiro * (atraso * 0.65) + dir_esfera_det(i, 0.8, -dir_tiro) * (atraso * 0.28)
				var esc_s: float = (1.0 - atraso) * 0.9
				mm_s.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.001, esc_s)), pos_s - gp))
				mm_s.set_instance_color(i, Color(1.0, 0.82, 0.32, 1.0 - atraso))
				mm_s.set_instance_custom_data(i, Color(atraso, 1.0 - atraso, 0.2, s))

		"foguete_enxame":
			var ort1: Vector3 = dir_tiro.cross(Vector3.UP).normalized()
			var ort2: Vector3 = dir_tiro.cross(ort1).normalized()
			var mm_f := _mmi_fumaca.multimesh
			for m_idx in range(_projeteis.size()):
				var u_m: float = clampf((u - float(m_idx) * 0.04) * 1.15, 0.0, 1.0)
				_projeteis[m_idx].visible = (u_m > 0.01 and u_m < 0.98)
				var ang_m: float = u_m * TAU * 1.8 + float(m_idx) * (TAU / 5.0)
				var raio_esp: float = sin(u_m * PI) * (0.28 + 0.08 * float(m_idx % 2))
				var p_m: Vector3 = _pos_arco(p0, p1, u_m, 0.45) + (ort1 * cos(ang_m) + ort2 * sin(ang_m)) * raio_esp
				var p_m0: Vector3 = _pos_arco(p0, p1, maxf(0.0, u_m - 0.05), 0.45) + (ort1 * cos(ang_m - 0.3) + ort2 * sin(ang_m - 0.3)) * raio_esp
				_orientar_cilindro(_projeteis[m_idx], p_m0, p_m + (p_m - p_m0).normalized() * 0.22, 1.0)
				for k in range(12):
					var p_id: int = m_idx * 12 + k
					var tk: float = float(k) / 12.0 * u_m
					var ak: float = tk * TAU * 1.8 + float(m_idx) * (TAU / 5.0)
					var rk: float = sin(tk * PI) * (0.28 + 0.08 * float(m_idx % 2))
					var pos_k: Vector3 = _pos_arco(p0, p1, tk, 0.45) + (ort1 * cos(ak) + ort2 * sin(ak)) * rk
					var idade_k: float = clampf(u_m - tk, 0.0, 1.0)
					var esc_k: float = (0.4 + idade_k * 0.9) * (1.0 - idade_k * 0.65)
					mm_f.set_instance_transform(p_id, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.001, esc_k)), pos_k - gp))
					mm_f.set_instance_color(p_id, Color(1.0, 0.9, 0.7, 1.0 - idade_k))
					mm_f.set_instance_custom_data(p_id, Color(idade_k, maxf(0.0, 1.0 - idade_k * 1.8), 0.9, hash_det(p_id)))

		"artilharia":
			var p_g: Vector3 = _pos_arco(p0, p1, u, 2.15)
			var p_g0: Vector3 = _pos_arco(p0, p1, maxf(0.0, u - 0.04), 2.15)
			_projeteis[0].visible = (u > 0.01 and u < 0.98)
			_orientar_cilindro(_projeteis[0], p_g0, p_g + (p_g - p_g0).normalized() * 0.38, 1.0)
			var mm_f := _mmi_fumaca.multimesh
			for i in range(mm_f.instance_count):
				var tn: float = float(i) / float(mm_f.instance_count) * u
				var id_f: float = clampf(u - tn, 0.0, 1.0)
				var pos_f: Vector3 = _pos_arco(p0, p1, tn, 2.15) + dir_esfera_det(i, 0.6, Vector3.UP) * (id_f * 0.35)
				var esc_f: float = (0.5 + id_f * 1.3) * (1.0 - id_f * 0.55)
				mm_f.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.001, esc_f)), pos_f - gp))
				mm_f.set_instance_color(i, Color(1.0, 0.95, 0.85, 1.0 - id_f * 0.8))
				mm_f.set_instance_custom_data(i, Color(id_f, maxf(0.0, 1.0 - id_f * 2.5), 1.0, hash_det(i)))
			var mm_s := _mmi_faiscas.multimesh
			for i in range(mm_s.instance_count):
				var s: float = hash_det(i * 19 + 3)
				var pos_s: Vector3 = p0 + dir_esfera_det(i, 0.75, dir_tiro) * (u * (0.9 + s * 1.1))
				var esc_s: float = maxf(0.001, (1.0 - u) * 1.1)
				mm_s.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc_s), pos_s - gp))
				mm_s.set_instance_color(i, Color(1.0, 0.78, 0.28, 1.0 - u))
				mm_s.set_instance_custom_data(i, Color(u, 1.0 - u, 0.3, s))

		"municao_perfurante":
			var pa: Vector3 = p0.lerp(p1, clampf(u - 0.18, 0.0, 1.0))
			var pb: Vector3 = p0.lerp(p1, clampf(u + 0.12, 0.0, 1.0))
			_projeteis[0].visible = (u > 0.01 and u < 0.98)
			_orientar_cilindro(_projeteis[0], pa, pb, 1.0)
			for i in range(_aneis_mach.size()):
				var t_anel: float = 0.22 + float(i) * 0.28
				var idade_a: float = clampf((u - t_anel * 0.6) * 1.6, 0.0, 1.0)
				_aneis_mach[i].visible = (idade_a > 0.01 and idade_a < 0.98)
				var p_anel: Vector3 = p0.lerp(p1, t_anel)
				_orientar_cilindro(_aneis_mach[i], p_anel - dir_tiro * 0.05, p_anel + dir_tiro * 0.05, 1.0)
				var esc_a: float = (0.35 + idade_a * 1.65) * sin(clampf(idade_a, 0.0, 1.0) * PI)
				_aneis_mach[i].scale = Vector3(esc_a, 0.4, esc_a)
			var mm := _mmi_faiscas.multimesh
			for i in range(mm.instance_count):
				var frac: float = float(i) / float(mm.instance_count) * u
				var pos: Vector3 = p0.lerp(p1, frac) + dir_esfera_det(i, 0.85, -dir_tiro) * ((u - frac) * 0.48)
				var esc: float = maxf(0.001, (1.0 - (u - frac)) * 0.95)
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos - gp))
				mm.set_instance_color(i, Color(1.0, 0.9, 0.55, 1.0 - (u - frac)))
				mm.set_instance_custom_data(i, Color(u, 1.0 - (u - frac) * 0.7, 0.2, hash_det(i)))

		"municao_carregada":
			var p_orb: Vector3 = p0.lerp(p1, u)
			_projeteis[0].visible = (u > 0.01 and u < 0.98)
			if _projeteis[0].is_inside_tree():
				_projeteis[0].global_position = p_orb
			else:
				_projeteis[0].position = p_orb
			_projeteis[0].scale = Vector3.ONE * (0.9 + 0.25 * sin(u * TAU * 4.0))
			var p_ini_tr: Vector3 = p0.lerp(p1, maxf(0.0, u - 0.45))
			_feixes[0].visible = (u > 0.04 and u < 0.98)
			_orientar_cilindro(_feixes[0], p_ini_tr, p_orb, p_ini_tr.distance_to(p_orb))
			var ort1: Vector3 = dir_tiro.cross(Vector3.UP).normalized()
			var ort2: Vector3 = dir_tiro.cross(ort1).normalized()
			var mm := _mmi_faiscas.multimesh
			for i in range(mm.instance_count):
				var frac: float = float(i) / float(mm.instance_count) * u
				var ang: float = frac * TAU * 5.0 + u * 12.0 + float(i)
				var r_el: float = 0.14 + 0.18 * hash_det(i * 11)
				var pos: Vector3 = p0.lerp(p1, frac) + (ort1 * cos(ang) + ort2 * sin(ang)) * r_el
				var id_e: float = clampf(u - frac, 0.0, 1.0)
				var esc: float = maxf(0.001, (1.0 - id_e * 0.75) * 0.95)
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos - gp))
				mm.set_instance_color(i, Color(0.55, 0.95, 1.0, 1.0 - id_e))
				mm.set_instance_custom_data(i, Color(id_e, 1.0 - id_e * 0.5, 0.4, hash_det(i)))

		"drone_combate":
			var sep: Vector3 = dir_tiro.cross(Vector3.UP).normalized() * 0.16
			for i in range(_projeteis.size()):
				var sgn: float = -1.0 if i == 0 else 1.0
				var ui: float = clampf((u - float(i) * 0.14) * 1.25, 0.0, 1.0)
				_projeteis[i].visible = (ui > 0.01 and ui < 0.98)
				var pa: Vector3 = (p0 + sep * sgn).lerp(p1 + sep * sgn * 0.3, clampf(ui - 0.15, 0.0, 1.0))
				var pb: Vector3 = (p0 + sep * sgn).lerp(p1 + sep * sgn * 0.3, clampf(ui + 0.15, 0.0, 1.0))
				_orientar_cilindro(_projeteis[i], pa, pb, 1.0)
			var mm := _mmi_faiscas.multimesh
			for i in range(mm.instance_count):
				var frac: float = float(i) / float(mm.instance_count) * u
				var pos: Vector3 = p0.lerp(p1, frac) + dir_esfera_det(i, 0.7, -dir_tiro) * 0.22
				var esc: float = maxf(0.001, (1.0 - (u - frac)) * 0.85)
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos - gp))
				mm.set_instance_color(i, Color(1.0, 0.45, 0.65, 1.0 - (u - frac)))
				mm.set_instance_custom_data(i, Color(u, 1.0, 0.3, hash_det(i)))

