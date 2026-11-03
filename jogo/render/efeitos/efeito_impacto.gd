class_name EfeitoImpacto
extends "res://render/efeitos/efeito_base.gd"
## Efeito de impacto no alvo por arma (nos 3 alvos: aranha, chao, estrutura) e explosões/pulsos especiais.
## Respeita os limites rígidos: <= 200 partículas por impacto, <= 500 para explosão grande.
## Sem luz dinâmica em efeito pequeno; apenas explosões grandes usam OmniLight3D curta e sem sombra.

@export_enum(
	"metralhadora", "torre_energia", "lanca_foguetes", "foguete_enxame",
	"artilharia", "municao_perfurante", "municao_carregada", "drone_combate",
	"explosao_foguete", "explosao_artilharia", "disparo_mina_pulso"
)
var tipo_impacto: String = "metralhadora"

@export_enum("todos", "aranha", "chao", "estrutura")
var alvo_padrao: String = "todos"

var _props_alvos: Array[Node3D] = []
var _ondas_choque: Array[MeshInstance3D] = []
var _bolas_fogo: Array[MeshInstance3D] = []
var _mmi_primario: MultiMeshInstance3D
var _mmi_secundario: MultiMeshInstance3D
var _mmi_terciario: MultiMeshInstance3D
var _luz_explosao: OmniLight3D


func _eh_explosao_especial() -> bool:
	return tipo_impacto in ["explosao_foguete", "explosao_artilharia", "disparo_mina_pulso"]


func _criar_prop_aranha(pos: Vector3) -> Node3D:
	var raiz := Node3D.new()
	raiz.position = pos
	# Corpo quitinoso/metálico escuro + olho vermelho + 4 pernas articuladas
	var corpo := MeshInstance3D.new()
	corpo.mesh = malha_octaedro(0.32, 0.72)
	corpo.position = Vector3(0, 0.26, 0)
	corpo.material_override = criar_mat_solido(Color(0.18, 0.14, 0.22), 0.42, 0.65)
	raiz.add_child(corpo)
	for i in range(4):
		var ang: float = -0.9 + float(i) * 0.6
		for sgn in [-1.0, 1.0]:
			var perna := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.025
			cm.bottom_radius = 0.015
			cm.height = 0.42
			perna.mesh = cm
			perna.position = Vector3(sgn * 0.28, 0.18, sin(ang) * 0.22)
			perna.rotation_degrees = Vector3(0, 0, sgn * -38.0)
			perna.material_override = criar_mat_solido(Color(0.24, 0.20, 0.28), 0.45, 0.60)
			raiz.add_child(perna)
	add_child(raiz)
	return raiz


func _criar_prop_chao(pos: Vector3) -> Node3D:
	var raiz := Node3D.new()
	raiz.position = pos
	var monte := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.42
	cm.bottom_radius = 0.56
	cm.height = 0.14
	monte.mesh = cm
	monte.position = Vector3(0, 0.07, 0)
	monte.material_override = criar_mat_solido(Color(0.30, 0.23, 0.16), 0.92, 0.0)
	raiz.add_child(monte)
	add_child(raiz)
	return raiz


func _criar_prop_estrutura(pos: Vector3) -> Node3D:
	var raiz := Node3D.new()
	raiz.position = pos
	var chapa := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.72, 0.54, 0.22)
	chapa.mesh = bm
	chapa.position = Vector3(0, 0.27, 0)
	chapa.material_override = criar_mat_solido(Color(0.32, 0.36, 0.40), 0.48, 0.78)
	raiz.add_child(chapa)
	add_child(raiz)
	return raiz


func _cor_arma() -> Color:
	match tipo_impacto:
		"metralhadora": return Color(1.0, 0.78, 0.25)
		"torre_energia": return Color(0.22, 0.88, 1.0)
		"lanca_foguetes": return Color(1.0, 0.48, 0.14)
		"foguete_enxame": return Color(1.0, 0.68, 0.20)
		"artilharia": return Color(1.0, 0.38, 0.10)
		"municao_perfurante": return Color(1.0, 0.90, 0.62)
		"municao_carregada": return Color(0.35, 0.72, 1.0)
		"drone_combate": return Color(1.0, 0.28, 0.48)
	return Color(1.0, 0.65, 0.25)


func _construir_efeito() -> void:
	_total_particulas = 0
	_props_alvos.clear()
	_ondas_choque.clear()
	_bolas_fogo.clear()

	if tipo_impacto == "explosao_foguete":
		duracao = 1.25
		intervalo_loop = 1.60
		_props_alvos.append(_criar_prop_chao(Vector3.ZERO))
		# Bola de fogo central + anel de choque no chão + 120 estilhaços incandescentes + 140 nuvens de fumaça = 260 partículas (<= 500)
		var bf := MeshInstance3D.new()
		bf.mesh = malha_octaedro(0.45, 0.9)
		bf.material_override = criar_mat_feixe(Color(1.0, 0.95, 0.70), Color(1.0, 0.38, 0.08), 6.2, 5.0, 14.0)
		add_child(bf)
		_bolas_fogo.append(bf)

		var anel := MeshInstance3D.new()
		anel.mesh = malha_anel(0.55, 0.78)
		anel.material_override = criar_mat_feixe(Color(1.0, 0.82, 0.42), Color(1.0, 0.35, 0.08), 4.8, 6.0, 12.0)
		add_child(anel)
		_ondas_choque.append(anel)

		_mmi_primario = criar_multimesh_particulas(120, malha_lasca(Vector3(0.045, 0.045, 0.16)),
			criar_mat_particula(Color(1.0, 0.88, 0.35), Color(1.0, 0.28, 0.05), 5.5, 0.25))
		_mmi_secundario = criar_multimesh_particulas(140, malha_octaedro(0.22, 0.95),
			criar_mat_particula(Color(0.95, 0.48, 0.16), Color(0.22, 0.20, 0.19), 2.2, 0.88, 4.5))
		_luz_explosao = criar_luz_curta(Color(1.0, 0.58, 0.18), 7.5)
		return

	if tipo_impacto == "explosao_artilharia":
		duracao = 1.50
		intervalo_loop = 1.85
		_props_alvos.append(_criar_prop_chao(Vector3.ZERO))
		# Dupla cúpula térmica + 2 anéis sísmicos + 180 ejeções balísticas de escória/terra + 220 colunas de fumaça = 400 partículas (<= 500)
		for i in range(2):
			var bf := MeshInstance3D.new()
			bf.mesh = malha_octaedro(0.62 if i == 0 else 0.42, 0.85 + float(i) * 0.35)
			bf.material_override = criar_mat_feixe(Color(1.0, 0.96, 0.78), Color(1.0, 0.32, 0.06), 6.8, 6.0, 16.0)
			add_child(bf)
			_bolas_fogo.append(bf)
			var anel := MeshInstance3D.new()
			anel.mesh = malha_anel(0.65, 0.92)
			anel.material_override = criar_mat_feixe(Color(1.0, 0.78, 0.38), Color(0.92, 0.28, 0.06), 5.0, 8.0, 14.0)
			add_child(anel)
			_ondas_choque.append(anel)

		_mmi_primario = criar_multimesh_particulas(180, malha_lasca(Vector3(0.06, 0.05, 0.18)),
			criar_mat_particula(Color(1.0, 0.85, 0.32), Color(0.45, 0.22, 0.10), 5.2, 0.35))
		_mmi_secundario = criar_multimesh_particulas(220, malha_octaedro(0.28, 1.0),
			criar_mat_particula(Color(1.0, 0.45, 0.12), Color(0.18, 0.16, 0.15), 2.5, 0.90, 4.0))
		_luz_explosao = criar_luz_curta(Color(1.0, 0.52, 0.15), 9.5)
		return

	if tipo_impacto == "disparo_mina_pulso":
		duracao = 1.20
		intervalo_loop = 1.55
		# Mina de pulso enterrada no centro + 3 aranhas ao redor que ficam paralisadas quando o anel no chão passa por elas
		var mina := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.22
		cm.bottom_radius = 0.28
		cm.height = 0.10
		mina.mesh = cm
		mina.position = Vector3(0, 0.05, 0)
		mina.material_override = criar_mat_solido(Color(0.20, 0.25, 0.32), 0.4, 0.7, Color(0.20, 0.88, 1.0), 3.5)
		add_child(mina)
		_props_alvos.append(mina)
		for i in range(3):
			var ang: float = float(i) * (TAU / 3.0) + 0.35
			_props_alvos.append(_criar_prop_aranha(Vector3(cos(ang) * 1.55, 0.0, sin(ang) * 1.55)))

		for i in range(2):
			var anel := MeshInstance3D.new()
			anel.mesh = malha_anel(0.78, 0.96)
			anel.material_override = criar_mat_feixe(Color(0.85, 0.98, 1.0), Color(0.15, 0.75, 1.0), 6.2, 12.0, 22.0)
			add_child(anel)
			_ondas_choque.append(anel)

		# 150 partículas elétricas (arco rasante no solo + estática paralisante nas aranhas atingidas, <= 200)
		_mmi_primario = criar_multimesh_particulas(150, malha_lasca(Vector3(0.035, 0.035, 0.16)),
			criar_mat_particula(Color(0.55, 0.96, 1.0), Color(0.20, 0.45, 1.0), 6.0, 0.2))
		return

	# Impacto das 8 armas nos 3 alvos físicos:
	# - Esquerda (-1.75, 0, 0): Aranha (faíscas metálicas/quitina e fragmentos escuros)
	# - Centro   ( 0.00, 0, 0): Chão   (torrões de terra e nuvem de poeira levantada)
	# - Direita  (+1.75, 0, 0): Estrutura (fagulhas quentes na chapa blindada e anel térmico)
	duracao = 0.85
	intervalo_loop = 1.15
	_props_alvos.append(_criar_prop_aranha(Vector3(-1.75, 0.0, 0.0)))
	_props_alvos.append(_criar_prop_chao(Vector3(0.0, 0.0, 0.0)))
	_props_alvos.append(_criar_prop_estrutura(Vector3(1.75, 0.0, 0.0)))

	var c_arma: Color = _cor_arma()
	for i in range(3):
		var anel := MeshInstance3D.new()
		anel.mesh = malha_anel(0.32, 0.46)
		anel.material_override = criar_mat_feixe(c_arma.lightened(0.45), c_arma, 4.8, 6.0, 16.0)
		add_child(anel)
		_ondas_choque.append(anel)

	# 56 partículas para Aranha + 56 para Chão + 56 para Estrutura = 168 partículas totais (<= 200!)
	_mmi_primario = criar_multimesh_particulas(56, malha_lasca(Vector3(0.04, 0.035, 0.14)),
		criar_mat_particula(c_arma.lightened(0.25), Color(0.35, 0.18, 0.42), 4.8, 0.30))
	_mmi_secundario = criar_multimesh_particulas(56, malha_octaedro(0.11, 0.9),
		criar_mat_particula(Color(0.52, 0.40, 0.28), Color(0.26, 0.20, 0.14), 0.6, 0.92, 6.0))
	_mmi_terciario = criar_multimesh_particulas(56, malha_lasca(Vector3(0.035, 0.035, 0.16)),
		criar_mat_particula(Color(1.0, 0.86, 0.40), c_arma, 5.6, 0.22))


func _ao_reiniciar_ciclo() -> void:
	if dentro_do_jogo or (get_parent() != null and get_parent() != get_tree().root):
		for p in _props_alvos:
			if is_instance_valid(p):
				p.visible = false
	for o in _ondas_choque:
		o.visible = true
	for b in _bolas_fogo:
		b.visible = true
	if _mmi_primario != null: _mmi_primario.visible = true
	if _mmi_secundario != null: _mmi_secundario.visible = true
	if _mmi_terciario != null: _mmi_terciario.visible = true


func _ao_terminar() -> void:
	for o in _ondas_choque:
		o.visible = false
	for b in _bolas_fogo:
		b.visible = false
	if _mmi_primario != null: _mmi_primario.visible = false
	if _mmi_secundario != null: _mmi_secundario.visible = false
	if _mmi_terciario != null: _mmi_terciario.visible = false
	if _luz_explosao != null:
		_luz_explosao.light_energy = 0.0



func _atualizar_quadro(u: float) -> void:
	if tipo_impacto == "explosao_foguete":
		var u_fogo: float = clampf(u * 2.2, 0.0, 1.0)
		_bolas_fogo[0].position = Vector3(0, 0.35 + u * 0.45, 0)
		var esc_bf: float = (0.4 + u_fogo * 1.9) * maxf(0.01, 1.0 - u * 1.15)
		_bolas_fogo[0].scale = Vector3.ONE * esc_bf

		_ondas_choque[0].position = Vector3(0, 0.08, 0)
		var esc_an: float = 0.3 + u * 2.8
		_ondas_choque[0].scale = Vector3(esc_an, maxf(0.02, (1.0 - u) * 0.5), esc_an)

		if _luz_explosao != null:
			_luz_explosao.position = Vector3(0, 0.8, 0)
			_luz_explosao.light_energy = maxf(0.0, 1.0 - u * 2.2) * 5.5

		var mm1 := _mmi_primario.multimesh
		for i in range(mm1.instance_count):
			var s: float = hash_det(i * 17 + 3)
			var v0: Vector3 = dir_esfera_det(i, 1.25, Vector3.UP) * (2.2 + s * 2.8)
			var pos: Vector3 = Vector3(0, 0.18, 0) + v0 * u + Vector3(0, -4.8 * u * u, 0)
			pos.y = maxf(0.03, pos.y)
			var esc: float = maxf(0.001, (1.0 - u * 0.85) * (0.7 + s * 0.7))
			mm1.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm1.set_instance_color(i, Color(1.0, 0.82, 0.32, 1.0 - u))
			mm1.set_instance_custom_data(i, Color(u, 1.0 - u * 0.7, 0.3, s))

		var mm2 := _mmi_secundario.multimesh
		for i in range(mm2.instance_count):
			var s: float = hash_det(i * 29 + 11)
			var dir_c: Vector3 = dir_esfera_det(i, 0.95, Vector3.UP)
			var pos: Vector3 = Vector3(0, 0.15, 0) + dir_c * (u * (1.2 + s * 1.6)) + Vector3(0, u * 1.15, 0)
			var esc: float = (0.55 + u * 1.65) * (1.0 - u * 0.35)
			mm2.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm2.set_instance_color(i, Color(1.0, 1.0, 1.0, 1.0 - u * 0.75))
			mm2.set_instance_custom_data(i, Color(u, maxf(0.0, 1.0 - u * 2.0), 1.0, s))
		return

	if tipo_impacto == "explosao_artilharia":
		for k in range(_bolas_fogo.size()):
			var uk: float = clampf((u - float(k) * 0.08) * 1.8, 0.0, 1.0)
			_bolas_fogo[k].position = Vector3(0, 0.45 + uk * (0.65 + float(k) * 0.55), 0)
			var esc_bf: float = (0.5 + uk * 2.4) * maxf(0.01, 1.0 - u * 1.05)
			_bolas_fogo[k].scale = Vector3.ONE * esc_bf

			_ondas_choque[k].position = Vector3(0, 0.08 + float(k) * 0.18, 0)
			var esc_an: float = 0.4 + uk * (3.6 - float(k) * 0.8)
			_ondas_choque[k].scale = Vector3(esc_an, maxf(0.02, (1.0 - uk) * 0.6), esc_an)

		if _luz_explosao != null:
			_luz_explosao.position = Vector3(0, 1.2, 0)
			_luz_explosao.light_energy = maxf(0.0, 1.0 - u * 1.8) * 7.2

		var mm1 := _mmi_primario.multimesh
		for i in range(mm1.instance_count):
			var s: float = hash_det(i * 19 + 5)
			var v0: Vector3 = dir_esfera_det(i, 1.35, Vector3.UP) * (2.8 + s * 3.6)
			var pos: Vector3 = Vector3(0, 0.20, 0) + v0 * u + Vector3(0, -5.8 * u * u, 0)
			pos.y = maxf(0.03, pos.y)
			var esc: float = maxf(0.001, (1.0 - u * 0.8) * (0.8 + s * 0.8))
			mm1.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm1.set_instance_color(i, Color(1.0, 0.78, 0.28, 1.0 - u))
			mm1.set_instance_custom_data(i, Color(u, 1.0 - u * 0.65, 0.4, s))

		var mm2 := _mmi_secundario.multimesh
		for i in range(mm2.instance_count):
			var s: float = hash_det(i * 37 + 9)
			var eh_coluna: bool = (i < 110)
			var dir_c: Vector3 = dir_esfera_det(i, 0.55 if eh_coluna else 1.4, Vector3.UP)
			var pos: Vector3 = Vector3(0, 0.20, 0) + dir_c * (u * (1.4 + s * 1.9)) + Vector3(0, u * (2.1 if eh_coluna else 0.55), 0)
			var esc: float = (0.65 + u * 1.95) * (1.0 - u * 0.30)
			mm2.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm2.set_instance_color(i, Color(1.0, 1.0, 1.0, 1.0 - u * 0.7))
			mm2.set_instance_custom_data(i, Color(u, maxf(0.0, 1.0 - u * 1.7), 1.0, s))
		return

	if tipo_impacto == "disparo_mina_pulso":
		var raio_onda: float = 0.25 + u * 2.35
		for k in range(_ondas_choque.size()):
			var uk: float = clampf((u - float(k) * 0.12) * 1.15, 0.0, 1.0)
			_ondas_choque[k].position = Vector3(0, 0.08 + float(k) * 0.05, 0)
			var r_an: float = 0.25 + uk * 2.35
			_ondas_choque[k].scale = Vector3(r_an, maxf(0.02, (1.0 - uk) * 0.35), r_an)
			var sm := _ondas_choque[k].material_override as ShaderMaterial
			if sm != null:
				sm.set_shader_parameter("progresso", 1.0 - uk * 0.7)

		var mm := _mmi_primario.multimesh
		for i in range(mm.instance_count):
			var s: float = hash_det(i * 23 + 7)
			var pos: Vector3
			if i < 75:
				# Partículas acompanhando a frente do anel no chão
				var ang: float = float(i) / 75.0 * TAU + u * 2.5
				var r_p: float = raio_onda + (s - 0.5) * 0.22
				pos = Vector3(cos(ang) * r_p, 0.08 + 0.14 * sin(u * TAU * 3.0 + float(i)), sin(ang) * r_p)
			else:
				# Arcos elétricos paralisando as 3 aranhas quando a onda as alcança (u >= 0.35)
				var idx_ar: int = (i - 75) % 3
				var ang_ar: float = float(idx_ar) * (TAU / 3.0) + 0.35
				var centro_ar := Vector3(cos(ang_ar) * 1.55, 0.24, sin(ang_ar) * 1.55)
				var ativo_ar: float = clampf((u - 0.32) * 2.2, 0.0, 1.0)
				pos = centro_ar + dir_esfera_det(i, 1.1, Vector3.UP) * (0.38 * ativo_ar)
			var esc: float = maxf(0.001, (1.0 - u * 0.7) * (0.65 + s * 0.65))
			mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm.set_instance_color(i, Color(0.55, 0.96, 1.0, 1.0 - u * 0.75))
			mm.set_instance_custom_data(i, Color(u, 1.0, 0.3, s))
		return

	# Atualização dos impactos das 8 armas nos 3 alvos (Aranha, Chão, Estrutura)
	var alvo_str: String = String(extra_atual) if extra_atual != null else "todos"
	var centros := [Vector3(-1.75, 0.32, 0.0), Vector3(0.0, 0.14, 0.0), Vector3(1.75, 0.32, 0.0)]
	if dentro_do_jogo and alvo_str != "todos":
		centros = [Vector3(0.0, 0.25, 0.0), Vector3(0.0, 0.08, 0.0), Vector3(0.0, 0.25, 0.0)]

	var escala_arma: float = 1.0
	if tipo_impacto in ["lanca_foguetes", "artilharia"]:
		escala_arma = 1.45
	elif tipo_impacto in ["municao_perfurante", "municao_carregada"]:
		escala_arma = 1.25

	for idx_c in range(3):
		var vis_anel: bool = true
		if dentro_do_jogo and alvo_str != "todos":
			vis_anel = (alvo_str == "aranha" and idx_c == 0) or (alvo_str == "chao" and idx_c == 1) or (alvo_str == "estrutura" and idx_c == 2)
		_ondas_choque[idx_c].visible = vis_anel
		if vis_anel:
			_ondas_choque[idx_c].position = centros[idx_c] + Vector3(0, 0.04, 0)
			var r_a: float = (0.22 + u * 1.05 * escala_arma) * (1.0 - u * 0.4)
			_ondas_choque[idx_c].scale = Vector3(r_a, maxf(0.02, (1.0 - u) * 0.45), r_a)

	var usa_ar: bool = (not dentro_do_jogo) or (alvo_str in ["todos", "aranha"])
	var usa_ch: bool = (not dentro_do_jogo) or (alvo_str in ["todos", "chao"])
	var usa_es: bool = (not dentro_do_jogo) or (alvo_str in ["todos", "estrutura"])

	# 1. Alvo Aranha (faíscas metálicas/quitina saltando da carapaça)
	_mmi_primario.visible = usa_ar
	if usa_ar:
		var mm_ar := _mmi_primario.multimesh
		for i in range(mm_ar.instance_count):
			var s: float = hash_det(i * 13 + 1)
			var v0: Vector3 = dir_esfera_det(i, 1.1, Vector3(-0.2, 1.0, 0.0).normalized()) * (1.1 + s * 1.5) * escala_arma
			var pos: Vector3 = centros[0] + v0 * u + Vector3(0, -3.6 * u * u, 0)
			pos.y = maxf(0.04, pos.y)
			var esc: float = maxf(0.001, (1.0 - u * 0.85) * (0.65 + s * 0.65) * escala_arma)
			mm_ar.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm_ar.set_instance_color(i, Color(1.0, 0.9, 0.7, 1.0 - u))
			mm_ar.set_instance_custom_data(i, Color(u, 1.0 - u * 0.5, 0.35, s))

	# 2. Alvo Chão (torrões de terra e nuvem de poeira subindo)
	_mmi_secundario.visible = usa_ch
	if usa_ch:
		var mm_ch := _mmi_secundario.multimesh
		for i in range(mm_ch.instance_count):
			var s: float = hash_det(i * 19 + 7)
			var v0: Vector3 = dir_esfera_det(i, 1.2, Vector3.UP) * (0.85 + s * 1.15) * escala_arma
			var pos: Vector3 = centros[1] + v0 * u + Vector3(0, -2.2 * u * u, 0)
			pos.y = maxf(0.05, pos.y)
			var esc: float = (0.45 + u * 1.15) * (1.0 - u * 0.55) * escala_arma
			mm_ch.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * maxf(0.001, esc)), pos))
			mm_ch.set_instance_color(i, Color(1.0, 0.95, 0.90, 1.0 - u * 0.8))
			mm_ch.set_instance_custom_data(i, Color(u, maxf(0.0, 0.6 - u), 1.0, s))

	# 3. Alvo Estrutura (chuva de fagulhas quentes reboteando na chapa metálica)
	_mmi_terciario.visible = usa_es
	if usa_es:
		var mm_es := _mmi_terciario.multimesh
		for i in range(mm_es.instance_count):
			var s: float = hash_det(i * 31 + 9)
			var v0: Vector3 = dir_esfera_det(i, 0.95, Vector3(0.0, 0.85, -0.5).normalized()) * (1.25 + s * 1.65) * escala_arma
			var pos: Vector3 = centros[2] + v0 * u + Vector3(0, -4.2 * u * u, 0)
			pos.y = maxf(0.03, pos.y)
			var esc: float = maxf(0.001, (1.0 - u * 0.85) * (0.7 + s * 0.65) * escala_arma)
			mm_es.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * esc), pos))
			mm_es.set_instance_color(i, Color(1.0, 0.88, 0.45, 1.0 - u))
			mm_es.set_instance_custom_data(i, Color(u, 1.0 - u * 0.4, 0.2, s))

