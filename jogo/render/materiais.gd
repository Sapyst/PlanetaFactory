class_name Materiais
## Troca os StandardMaterial3D que vêm do .glb pelo material único do jogo (material_pf.gdshader),
## mantendo cor/emissão e ligando o efeito certo pelo nome do material (P_Esteira rola, P_Cristal pulsa…).
## Materiais iguais são compartilhados (cache) — essencial para o desenho em lote no celular.

const SHADER := preload("res://render/shaders/material_pf.gdshader")
const VELOCIDADE_ESTEIRA := 1.875

static var _cache: Dictionary = {}


## `uv2` = a malha tem 2º canal de UV (modelo texturizado: a lona da esteira rola por ele).
static func material(origem: Material, vento := 0.0, boiar := 0.0, uv2 := false) -> Material:
	if not (origem is BaseMaterial3D):
		return origem
	var nome := origem.resource_name
	var b := origem as BaseMaterial3D
	var tex := b.albedo_texture
	var chave := "%s|%.2f|%.2f|%s|%d" % [nome, vento, boiar, uv2, tex.get_instance_id() if tex != null else 0]
	if _cache.has(chave):
		return _cache[chave]
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.resource_name = nome
	m.set_shader_parameter("cor", b.albedo_color)
	m.set_shader_parameter("aspereza", b.roughness)
	m.set_shader_parameter("metal", b.metallic)
	if b.emission_enabled:
		m.set_shader_parameter("cor_emissao", b.emission)
		m.set_shader_parameter("forca_emissao", maxf(b.emission_energy_multiplier, 1.0))
	if nome == "P_Esteira":
		m.set_shader_parameter("rolagem", VELOCIDADE_ESTEIRA)
	if nome in ["P_Cristal", "P_Biomassa", "P_OlhoInimigo", "P_Fogo", "P_Seiva"]:
		m.set_shader_parameter("pulso", 1.0)
	# vegetação: o material assado ("<modelo>_Tex") também balança e queima (antes só os de nome P_Folha…)
	if vento > 0.0 and (nome in ["P_Folha", "P_FolhaClara", "P_Biomassa", "P_Lodo", "P_Malaquita", "P_Cristal", "P_FungoCaule"] or nome.ends_with("_Tex")):
		m.set_shader_parameter("vento", vento)
	m.set_shader_parameter("boiar", boiar)
	if tex != null:
		m.set_shader_parameter("textura", tex)
		m.set_shader_parameter("tem_textura", true)
		m.set_shader_parameter("cor", Color.WHITE)
	if uv2 and nome == "P_Esteira":
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
static func malha_de(cena: PackedScene, vento := 0.0, boiar := 0.0) -> Mesh:
	var inst := cena.instantiate()
	var mis := inst.find_children("*", "MeshInstance3D", true, false)
	if mis.is_empty():
		inst.free()
		return null
	var orig: Mesh = (mis[0] as MeshInstance3D).mesh
	var copia := orig.duplicate() as Mesh
	for s in copia.get_surface_count():
		var uv2: bool = (copia.surface_get_format(s) & Mesh.ARRAY_FORMAT_TEX_UV2) != 0
		copia.surface_set_material(s, material(orig.surface_get_material(s), vento, boiar, uv2))
	inst.free()
	return copia
