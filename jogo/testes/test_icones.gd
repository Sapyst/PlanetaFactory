extends Caso
## Toda peça do menu de construção, toda categoria e todo item têm ícone de verdade (arquivo importado, não vazio).
## Os ícones de peça saem de arte/blender_scripts/icones.py; os de item de lá ou de ferramentas/derivar_icone.gd.

const MIN_COBERTURA := 0.03                     # fração mínima de pixels visíveis: menos que isso é ícone vazio


func _cobertura(caminho: String) -> float:
	var img := Image.load_from_file(ProjectSettings.globalize_path(caminho))
	if img == null or img.is_empty():
		return 0.0
	img.convert(Image.FORMAT_RGBA8)
	var n := 0
	for y in img.get_height():
		for x in img.get_width():
			if img.get_pixel(x, y).a > 0.5:
				n += 1
	return float(n) / (img.get_width() * img.get_height())


func _caminho_peca(nome: String) -> String:
	return "res://assets/icones/%s.png" % str(Registro.menu.get("icones", {}).get(nome, nome))


func test_toda_peca_do_menu_tem_icone() -> void:
	var cats: Array = Registro.menu.categorias
	verificar(cats.size() > 0, "menu tem categorias")
	for c in cats:
		for nome in c.pecas:
			var p := _caminho_peca(nome)
			if verificar(ResourceLoader.exists(p), "%s: sem ícone (%s)" % [nome, p]):
				verificar(load(p) is Texture2D, "%s: ícone não carrega" % nome)
				verificar(_cobertura(p) >= MIN_COBERTURA, "%s: ícone vazio" % nome)


func test_toda_categoria_tem_icone() -> void:
	var icc: Dictionary = Registro.menu.get("icones_categoria", {})
	for c in Registro.menu.categorias:
		verificar(icc.has(c.nome), "categoria %s: sem ícone próprio" % c.nome)
		verificar(ResourceLoader.exists("res://assets/icones/%s.svg" % icc.get(c.nome, "?")), "categoria %s: sem .svg" % c.nome)


func test_todo_item_tem_icone() -> void:
	for it in Registro.itens:
		var p := "res://assets/icones/itens/%s.png" % it
		if verificar(ResourceLoader.exists(p), "item %s: sem ícone" % it):
			verificar(load(p) is Texture2D, "item %s: ícone não carrega" % it)
			verificar(_cobertura(p) >= MIN_COBERTURA, "item %s: ícone vazio" % it)


func test_icone_da_pesquisa_acha_toda_peca() -> void:
	var pesquisas: Dictionary = Registro.progressao.get("pesquisas", {})
	for id in pesquisas:
		for nome in pesquisas[id].get("libera", []):
			verificar(TelaPesquisa._tex_peca(nome) != null, "%s libera %s: sem ícone" % [id, nome])


## Sobe e desce, e os níveis de esteira, não podem repetir o mesmo desenho; nem os módulos 1/2/3.
func test_variantes_tem_icone_proprio() -> void:
	for sufixo in ["", "_rapida", "_expressa", "_quantica"]:
		var a := FileAccess.get_md5(_caminho_peca("esteira_rampa" + sufixo))
		igual(a != FileAccess.get_md5(_caminho_peca("rampa_desce" + sufixo)), true, "rampa%s: sobe ≠ desce" % sufixo)
	var vistos := {}
	for peca in ["esteira", "esteira_rapida", "esteira_expressa", "esteira_quantica"]:
		var m := FileAccess.get_md5(_caminho_peca(peca))
		verificar(not vistos.has(m), "%s repete o ícone de outro nível" % peca)
		vistos[m] = true
	for tipo in ["velocidade", "eficiencia", "produtividade"]:
		var a := FileAccess.get_md5("res://assets/icones/itens/modulo_%s_1.png" % tipo)
		var b := FileAccess.get_md5("res://assets/icones/itens/modulo_%s_2.png" % tipo)
		var c := FileAccess.get_md5("res://assets/icones/itens/modulo_%s_3.png" % tipo)
		verificar(a != b and b != c and a != c, "módulo %s: níveis iguais" % tipo)
