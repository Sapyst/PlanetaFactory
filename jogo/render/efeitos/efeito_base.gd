class_name EfeitoBase
extends Node3D
## Base comum para todos os efeitos do estudo (Parte B — PlanetaFactory).
## Garante que cada efeito:
## 1) Aconteça fisicamente num ponto do mundo com uma causa visível (nunca filtro de tela).
## 2) Possa ser disparado facilmente do jogo via `tocar(origem, destino, cor, extra)` sem depender do código do jogo.
## 3) Repita em loop automático quando aberto isoladamente e permita captura determinística de 4 quadros.

@export var duracao: float = 1.1
@export var intervalo_loop: float = 1.45
@export var repetir_em_loop: bool = true
@export var modo_noturno: bool = false

var origem_atual: Vector3 = Vector3(-2.2, 0.65, 0.0)
var destino_atual: Vector3 = Vector3(2.2, 0.55, 0.0)
var cor_atual: Color = Color.WHITE
var extra_atual: Variant = null

var _tempo: float = 0.0
var _ativo: bool = true
var _total_particulas: int = 0
var _usa_luz_dinamica: bool = false
var _ciclo_atual: int = 0

const SH_PARTICULA := preload("res://render/efeitos/shaders/particula_proc.gdshader")
const SH_FEIXE := preload("res://render/efeitos/shaders/feixe_energia.gdshader")
const SH_AGUA := preload("res://render/efeitos/shaders/agua_corrente.gdshader")


var dentro_do_jogo: bool = false
var _construido: bool = false


func garantir_construido() -> void:
	if not _construido:
		_construido = true
		_construir_efeito()


func _enter_tree() -> void:
	if has_node("PalcoNeutro") and (get_tree() == null or get_parent() != get_tree().root):
		var palco := get_node("PalcoNeutro")
		remove_child(palco)
		palco.free()
	if get_parent() != null and (get_tree() == null or get_parent() != get_tree().root):
		dentro_do_jogo = true
		repetir_em_loop = false
		_ativo = false
		visible = false


func _ready() -> void:
	garantir_construido()
	if has_node("PalcoNeutro"):
		_aplicar_clima_palco(modo_noturno)
	if get_parent() != null and (get_tree() == null or get_parent() != get_tree().root):
		dentro_do_jogo = true
		_ativo = false
		visible = false
	if not dentro_do_jogo:
		tocar(origem_atual, destino_atual, cor_atual, extra_atual)



func _aplicar_clima_palco(noite: bool) -> void:
	if not has_node("PalcoNeutro"):
		return
	var sol := get_node_or_null("PalcoNeutro/Sol") as DirectionalLight3D
	if sol != null:
		sol.light_energy = 0.22 if noite else 1.25
		sol.light_color = Color(0.55, 0.68, 0.95) if noite else Color(1.0, 0.97, 0.90)
	var amb := get_node_or_null("PalcoNeutro/Ambiente") as WorldEnvironment
	if amb != null and amb.environment != null:
		amb.environment.background_color = Color(0.05, 0.06, 0.09) if noite else Color(0.18, 0.20, 0.23)
		amb.environment.ambient_light_color = Color(0.14, 0.18, 0.28) if noite else Color(0.45, 0.48, 0.52)
		amb.environment.ambient_light_energy = 0.45 if noite else 0.85


func _process(delta: float) -> void:
	if not _ativo:
		return
	_tempo += delta
	if _tempo >= duracao:
		if repetir_em_loop:
			if _tempo >= intervalo_loop:
				_tempo = fmod(_tempo, intervalo_loop)
				_ciclo_atual += 1
				if has_node("PalcoNeutro"):
					_aplicar_clima_palco((_ciclo_atual % 2 == 1) != modo_noturno)
				_ao_reiniciar_ciclo()
		else:
			_tempo = duracao
			_ativo = false
			visible = false
			_ao_terminar()
			return
	var u: float = clampf(_tempo / maxf(0.05, duracao), 0.0, 1.0)
	_atualizar_quadro(u)


## Função pública curta para o jogo chamar sem depender de mais nada.
func tocar(origem: Vector3 = Vector3(-2.2, 0.65, 0.0), destino: Vector3 = Vector3(2.2, 0.55, 0.0),
		cor: Color = Color.WHITE, extra: Variant = null) -> void:
	garantir_construido()
	origem_atual = origem
	destino_atual = destino
	cor_atual = cor
	extra_atual = extra
	_tempo = 0.0
	_ativo = true
	visible = true
	_ao_reiniciar_ciclo()
	_atualizar_quadro(0.01)


## Posiciona o efeito num instante normalizado u in [0.0 .. 1.0] (para captura de folha de 4 quadros).
func definir_progresso(u: float) -> void:
	garantir_construido()
	_tempo = clampf(u, 0.0, 1.0) * duracao
	_atualizar_quadro(clampf(u, 0.0, 1.0))


func contagem_particulas() -> int:
	return _total_particulas


func usa_luz_dinamica() -> bool:
	return _usa_luz_dinamica


func esta_ativo() -> bool:
	return _ativo


# Métodos sobrescritos por cada efeito específico
func _construir_efeito() -> void:
	pass


func _ao_reiniciar_ciclo() -> void:
	pass


func _ao_terminar() -> void:
	pass


func _atualizar_quadro(_u: float) -> void:
	pass


# ================================================================== UTILITÁRIOS PROCEDURAIS 3D
func criar_mat_particula(c1: Color, c2: Color, emissao: float = 2.8, rug: float = 0.7, esc_ruido: float = 5.0) -> ShaderMaterial:
	var sm := ShaderMaterial.new()
	sm.shader = SH_PARTICULA
	sm.set_shader_parameter("cor_base", c1)
	sm.set_shader_parameter("cor_secundaria", c2)
	sm.set_shader_parameter("forca_emissao", emissao)
	sm.set_shader_parameter("rugosidade", rug)
	sm.set_shader_parameter("escala_ruido", esc_ruido)
	return sm


func criar_mat_feixe(c_nucleo: Color, c_borda: Color, intens: float = 4.0, freq: float = 8.0, vel: float = 14.0) -> ShaderMaterial:
	var sm := ShaderMaterial.new()
	sm.shader = SH_FEIXE
	sm.set_shader_parameter("cor_nucleo", c_nucleo)
	sm.set_shader_parameter("cor_borda", c_borda)
	sm.set_shader_parameter("intensidade", intens)
	sm.set_shader_parameter("frequencia", freq)
	sm.set_shader_parameter("velocidade", vel)
	return sm


func criar_mat_solido(cor: Color, rug: float = 0.85, metal: float = 0.0, emissao: Color = Color.BLACK, f_em: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = cor
	m.roughness = rug
	m.metallic = metal
	if f_em > 0.0:
		m.emission_enabled = true
		m.emission = emissao
		m.emission_energy_multiplier = f_em
	return m


func criar_multimesh_particulas(qtd: int, malha: Mesh, mat: Material) -> MultiMeshInstance3D:
	_total_particulas += qtd
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.use_custom_data = true
	mm.mesh = malha
	mm.instance_count = qtd
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi


func malha_octaedro(raio: float = 0.08, alongar_z: float = 1.0) -> SphereMesh:
	var sm := SphereMesh.new()
	sm.radius = raio
	sm.height = raio * 2.0 * alongar_z
	sm.radial_segments = 6
	sm.rings = 3
	return sm


func malha_lasca(tam: Vector3 = Vector3(0.06, 0.04, 0.14)) -> PrismMesh:
	var pm := PrismMesh.new()
	pm.size = tam
	return pm


func malha_anel(r_int: float = 0.65, r_ext: float = 1.0) -> TorusMesh:
	var tm := TorusMesh.new()
	tm.inner_radius = r_int
	tm.outer_radius = r_ext
	tm.rings = 18
	tm.ring_segments = 8
	return tm


func criar_luz_curta(cor: Color, alcance: float = 5.5) -> OmniLight3D:
	_usa_luz_dinamica = true
	var l := OmniLight3D.new()
	l.light_color = cor
	l.omni_range = alcance
	l.omni_attenuation = 1.4
	l.shadow_enabled = false
	l.light_energy = 0.0
	add_child(l)
	return l


func hash_det(semente: int) -> float:
	var x: int = (semente * 1664525 + 1013904223) & 0x7fffffff
	return float(x % 10000) / 10000.0


func dir_esfera_det(idx: int, abertura: float = 1.0, eixo: Vector3 = Vector3.UP) -> Vector3:
	var a: float = hash_det(idx * 17 + 3) * TAU
	var r: float = (0.18 + 0.82 * hash_det(idx * 31 + 7)) * abertura
	var base_b1: Vector3 = eixo.cross(Vector3.RIGHT if absf(eixo.x) < 0.8 else Vector3.FORWARD).normalized()
	var base_b2: Vector3 = eixo.cross(base_b1).normalized()
	return (eixo + (base_b1 * cos(a) + base_b2 * sin(a)) * r).normalized()
