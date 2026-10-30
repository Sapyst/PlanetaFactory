class_name Materiais
## Troca os StandardMaterial3D que vêm do .glb pelo material único do jogo (material_pf.gdshader),
## mantendo cor/emissão e ligando o efeito certo pelo nome do material (P_Esteira rola, P_Cristal pulsa…).
## Materiais iguais são compartilhados (cache) — essencial para o desenho em lote no celular.

const SHADER := preload("res://render/shaders/material_pf.gdshader")
const VELOCIDADE_ESTEIRA := 1.875
## Lona que rola pelo shader (m/s = tiles/s, igual à velocidade da esteira da classe): básica, rápida (logistica_3),
## expressa (logistica_4) e quântica (logistica_5).
const ROLAGEM := {"P_Esteira": VELOCIDADE_ESTEIRA, "P_EsteiraRapida": VELOCIDADE_ESTEIRA * 2.0,
		"P_EsteiraExpressa": VELOCIDADE_ESTEIRA * 3.0, "P_EsteiraQuantica": VELOCIDADE_ESTEIRA * 4.0}

static var _cache: Dictionary = {}

## Folhagem das árvores por receita: perfil da estação no shader (0 perene, 1 caduca laranja, 2 salgueiro,
## 3 acácia, 4 caduca amarela).
const PERFIL_FOLHA := {"P_FolhaPerene": 0, "P_FolhaCaduca": 1, "P_FolhaSalgueiro": 2, "P_FolhaSeca": 3, "P_FolhaBetula": 4}


## `uv2` = a malha tem 2º canal de UV (modelo texturizado: a lona da esteira rola por ele).
## `carbonizada` = versão queimada (árvore em pé carbonizada ou caída): tudo carvão, sem folha.
static func material(origem: Material, vento := 0.0, boiar := 0.0, uv2 := false, carbonizada := false) -> Material:
	if not (origem is BaseMaterial3D):
		return origem
	var nome := origem.resource_name
	var cor_nome := nome
	nome = nome.get_slice(".", 0)          # P_Fogo.001 (paleta do conversor: um material por cor) → efeito de P_Fogo
	var b := origem as BaseMaterial3D
	var tex := b.albedo_texture
	# a cor entra na chave: P_Fogo de modelos diferentes pode ter cor diferente com o mesmo nome
	var chave := "%s|%s|%.2f|%.2f|%s|%d|%s" % [cor_nome, b.albedo_color.to_html(), vento, boiar, uv2, tex.get_instance_id() if tex != null else 0, carbonizada]
	if _cache.has(chave):
		return _cache[chave]
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.resource_name = cor_nome
	m.set_shader_parameter("cor", b.albedo_color)
	m.set_shader_parameter("aspereza", b.roughness)
	m.set_shader_parameter("metal", b.metallic)
	if b.emission_enabled:
		m.set_shader_parameter("cor_emissao", b.emission)
		m.set_shader_parameter("forca_emissao", maxf(b.emission_energy_multiplier, 1.0))
	if ROLAGEM.has(nome):
		m.set_shader_parameter("rolagem", ROLAGEM[nome])
	if nome in ["P_Cristal", "P_Biomassa", "P_OlhoInimigo", "P_Fogo", "P_Seiva"]:
		m.set_shader_parameter("pulso", 1.0)
	if nome == "P_Cristal":
		m.set_shader_parameter("por_trabalho", true)
	# vegetação: o material assado ("<modelo>_Tex") também balança e queima (antes só os de nome P_Folha…)
	if vento > 0.0 and (nome in ["P_Folha", "P_FolhaClara", "P_Biomassa", "P_Lodo", "P_Malaquita", "P_Cristal", "P_FungoCaule"] or nome.ends_with("_Tex") or PERFIL_FOLHA.has(nome)):
		m.set_shader_parameter("vento", vento)
	if PERFIL_FOLHA.has(nome):
		m.set_shader_parameter("perfil_folha", PERFIL_FOLHA[nome])
	if carbonizada:
		m.set_shader_parameter("carbonizada", true)
	m.set_shader_parameter("boiar", boiar)
	if tex != null:
		m.set_shader_parameter("textura", tex)
		m.set_shader_parameter("tem_textura", true)
		m.set_shader_parameter("cor", Color.WHITE)
	if uv2 and ROLAGEM.has(nome):
		m.set_shader_parameter("rolagem_uv2", true)
	_cache[chave] = m
	return m


## Aplica em todas as malhas de uma cena instanciada.
static func converter(raiz: Node, vento := 0.0, boiar := 0.0) -> void:
	for n in raiz.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh == null:
			continue
		for s in mi.mesh.get_surface_count():
			var uv2: bool = (mi.mesh.surface_get_format(s) & Mesh.ARRAY_FORMAT_TEX_UV2) != 0
			mi.set_surface_override_material(s, material(mi.mesh.surface_get_material(s), vento, boiar, uv2))


## Malha única de um .glb de uma parte só (para MultiMesh), já com materiais convertidos.
static func malha_de(cena: PackedScene, vento := 0.0, boiar := 0.0, carbonizada := false) -> Mesh:
	var inst := cena.instantiate()
	var mis := inst.find_children("*", "MeshInstance3D", true, false)
	if mis.is_empty():
		inst.free()
		return null
	var orig: Mesh = (mis[0] as MeshInstance3D).mesh
	var copia := orig.duplicate() as Mesh
	for s in copia.get_surface_count():
		var uv2: bool = (copia.surface_get_format(s) & Mesh.ARRAY_FORMAT_TEX_UV2) != 0
		copia.surface_set_material(s, material(orig.surface_get_material(s), vento, boiar, uv2, carbonizada))
	inst.free()
	return copia
