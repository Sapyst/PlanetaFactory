extends Caso
## O que passa por Materiais.malha_de (lotes de esteira/cano/trilho, itens, mapa) é desenhado no lugar da peça:
## mesma caixa que a cena dá (com a translação do nó), dentro da área dela e com as bocas de cano nas portas.
## Mais o piso de fábrica sob a rampa e o limite de instance uniforms.

const FOLGA_AREA := 0.26      ## esteira_juncao passa 0,25 m do tile de propósito (a garganta encosta na vizinha)


func _cena(nome: String) -> Node3D:
	return (load(Registro.modelos[nome].modelo) as PackedScene).instantiate() as Node3D


## Caixa da 1ª malha da cena, com a transformação dos nós (sem a raiz: quem instancia a cena põe a posição nela).
func _caixa_na_cena(c: Node3D) -> AABB:
	var mi := c.find_children("*", "MeshInstance3D", true, false)[0] as MeshInstance3D
	var t := Transform3D.IDENTITY
	var n: Node = mi
	while n != c:
		t = (n as Node3D).transform * t
		n = n.get_parent()
	return t * mi.mesh.get_aabb()


func _passa_por_malha_de(nome: String) -> bool:
	var m: Dictionary = Registro.modelos[nome]
	if nome in ["nucleo_queda"]:
		return false
	return DesenhoLotes.aceita(nome) or m.get("tipo", "") in ["item", "deco"] or str(m.get("categoria", "")).begins_with("mapa/") \
			or nome in ["plataforma_agua", "ponte_agua"]


func test_todos_os_modelos_igual_a_cena() -> void:
	var usados := 0
	for nome in Registro.modelos:
		if not _passa_por_malha_de(nome):
			continue
		usados += 1
		var c := _cena(nome)
		igual(c.find_children("*", "MeshInstance3D", true, false).size(), 1, "%s: uma parte só (malha_de só pega a primeira)" % nome)
		var cx := _caixa_na_cena(c)
		c.free()
		var b: AABB = Materiais.malha_de(load(Registro.modelos[nome].modelo)).get_aabb()
		verificar(b.position.distance_to(cx.position) < 0.01 and b.size.distance_to(cx.size) < 0.01, "%s: malha %s, cena %s" % [nome, b, cx])
		if not Registro.modelos[nome].get("tipo", "") == "item":
			var meia: Vector2 = Vector2(Registro.area(nome)) / 2.0 if Registro.area(nome) != Vector2i.ZERO else Vector2(0.5, 0.5)
			var cen := b.get_center()
			verificar(absf(cen.x) <= meia.x and absf(cen.z) <= meia.y, "%s: centro %s fora da área %s" % [nome, cen, Registro.area(nome)])
	verificar(usados > 80, "achou os modelos (%d)" % usados)


func test_lotes_dentro_do_tile() -> void:
	for nome in Registro.modelos:
		if not DesenhoLotes.aceita(nome):
			continue
		var b: AABB = Materiais.malha_de(load(Registro.modelos[nome].modelo)).get_aabb()
		var a: Vector2i = Registro.area(nome)
		var mx := a.x / 2.0 + FOLGA_AREA
		var mz := a.y / 2.0 + FOLGA_AREA
		verificar(b.position.x >= -mx and b.end.x <= mx and b.position.z >= -mz and b.end.z <= mz, "%s: caixa %s além da área %s" % [nome, b, a])
		verificar(b.position.y > -0.1 and b.position.y < 0.6, "%s: pé em %.2f m" % [nome, b.position.y])


func test_bocas_de_cano_nas_portas() -> void:
	for nome in Registro.modelos:
		if not nome.begins_with("cano_"):
			continue
		var m := Materiais.malha_de(load(Registro.modelos[nome].modelo))
		for p in Registro.modelos[nome].get("portas", []):
			var alvo := Vector3(p.pos[0], p.pos[2], -p.pos[1])              # Blender (x, y, z) → Godot (x, z, −y)
			var d := Vector3(p.dir[0], 0, -p.dir[1])
			var boca := AABB()
			var tem := false
			for s in m.get_surface_count():
				for v: Vector3 in m.surface_get_arrays(s)[Mesh.ARRAY_VERTEX]:
					if absf((v - alvo).dot(d)) < 0.03:
						boca = boca.expand(v) if tem else AABB(v, Vector3.ZERO)
						tem = true
			if verificar(tem, "%s: nada na porta %s" % [nome, p.nome]):
				verificar((boca.get_center() - alvo).slide(d).length() < 0.03, "%s: boca %s fora da porta %s (%s)" % [nome, boca.get_center(), p.nome, alvo])


func test_assada_mantem_uv_e_materiais() -> void:
	var m := Materiais.malha_de(load(Registro.modelos.cano_t.modelo))
	igual(m.get_surface_count(), 2, "cano_t: 2 superfícies")
	verificar((m.surface_get_material(0) as ShaderMaterial).get_shader_parameter("tem_textura") == true, "cano_t segue com a textura")
	var arr := m.surface_get_arrays(0)
	verificar((arr[Mesh.ARRAY_TEX_UV] as PackedVector2Array).size() == (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size(), "cano_t com UV")


func _chunk_com(c: Construtor, k: Vector2i) -> DesenhoChunk:
	DesenhoChunk.preparar(c.mapa.gerador)
	var d := DesenhoChunk.new()
	d.montar(DesenhoChunk.preparar_dados(k, c.mapa.gerador), c.mapa)
	return d


func _construtor() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	return Construtor.new(m)


## Uma construção faz o piso crescer por 1,6 s; o que entra nesse meio-tempo (rampa logo depois do trecho alto) não
## pode sumir quando a mistura termina.
func test_piso_de_quem_entra_enquanto_o_piso_cresce() -> void:
	var c := _construtor()
	var t0 := Vector2i(20, 20)
	var chunk := _chunk_com(c, Grade.chunk_de(t0))
	var base: Vector2i = Grade.chunk_de(t0) * Grade.TAM_CHUNK
	c.mapa.colocar("bau", t0, 0)
	chunk.atualizar(c.mapa, [Vector2(t0)])
	var longe := t0 + Vector2i(9, 0)                # além do raio do crescimento
	var perto := t0 + Vector2i(3, 0)
	c.mapa.colocar("esteira_rampa", perto, 0)
	chunk.atualizar(c.mapa)
	c.mapa.colocar("esteira_rampa", longe, 0)
	chunk.atualizar(c.mapa)
	for i in 80:
		chunk._process(0.05)
	for t in [t0, perto, longe]:
		perto_piso(chunk, t - base)
	chunk.free()


func perto_piso(chunk: DesenhoChunk, px: Vector2i) -> void:
	perto(chunk._img_fabrica.get_pixel(px.x + 1, px.y + 1).r, 1.0, 0.01, "piso no tile %s do chunk" % px)


func test_instance_uniform_so_no_cristal() -> void:
	verificar(not Materiais.SHADER.code.contains("TRABALHO_POR_OBJETO"), "o shader comum não liga o uniform por objeto")
	verificar(Materiais.SHADER_CRISTAL.code.contains("#define TRABALHO_POR_OBJETO"), "o do cristal liga")
	var props := Materiais.SHADER.get_shader_uniform_list()
	var cristal := StandardMaterial3D.new()
	cristal.resource_name = "P_Cristal"
	var outro := StandardMaterial3D.new()
	outro.resource_name = "P_Metal"
	igual((Materiais.material(cristal) as ShaderMaterial).shader, Materiais.SHADER_CRISTAL, "P_Cristal na variante")
	igual((Materiais.material(outro) as ShaderMaterial).shader, Materiais.SHADER, "o resto no comum")
	verificar(props.size() > 5, "shader comum com os uniforms de sempre")
	# cada objeto com o uniform reserva 16 vec4 do buffer global; o pior caso é o extrator de cristal (29 objetos)
	var maior := 0
	for nome in Registro.modelos:
		if Registro.modelos[nome].get("tipo", "") != "estrutura":
			continue
		var c := _cena(nome)
		Materiais.converter(c)
		var n := 0
		for g in c.find_children("*", "GeometryInstance3D", true, false):
			if Materiais.usa_trabalho(g):
				n += 1
		maior = maxi(maior, n)
		c.free()
	var cabem: int = int(ProjectSettings.get_setting("rendering/limits/global_shader_variables/buffer_size")) / 16
	verificar(cabem >= maior * 500, "o buffer aguenta 500 máquinas da pior peça (%d objetos cada, cabem %d)" % [maior, cabem])


## Encardido: é por tile (canal R de fogo_mapa), não por objeto; continua no corpo comum dos dois shaders.
func test_encardido_nos_dois_shaders() -> void:
	var inc := FileAccess.get_file_as_string("res://render/shaders/material_pf.gdshaderinc")
	verificar(inc.contains("uniform sampler2D fogo_mapa") and inc.contains("grude"), "fogo_mapa e o encardido no corpo comum")
	for sh: Shader in [Materiais.SHADER, Materiais.SHADER_CRISTAL]:
		verificar(sh.code.contains("material_pf.gdshaderinc"), "%s inclui o corpo" % sh.resource_path)
