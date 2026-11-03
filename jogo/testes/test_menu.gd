extends Caso
## Testes do Menu Principal e do Fundo Abstrato geométrico.

const MENU_SCN := preload("res://cenas/menu.tscn")
const FundoAbstrato = preload("res://cenas/fundo_abstrato.gd")


func _raiz() -> Node:
	var st := Engine.get_main_loop() as SceneTree
	return st.root if st != null else null


func test_fundo_abstrato_formas_e_movimento() -> void:
	var fundo := FundoAbstrato.new()
	fundo.size = Vector2(1280, 720)
	var raiz := _raiz()
	if raiz != null:
		raiz.add_child(fundo)
	verificar(fundo.formas.size() >= 15, "fundo possui pelo menos 15 formas geométricas")
	var f0: Dictionary = fundo.formas[0]
	var pos_ini: Vector2 = f0.pos
	var rot_ini: float = float(f0.rot)

	# Avança 2 segundos no tempo
	fundo.avancar(2.0)
	verificar(f0.pos != pos_ini, "forma translada com o tempo")
	verificar(absf(float(f0.rot) - rot_ini) > 1e-5, "forma rotaciona com o tempo")

	# Wrap-around nas bordas
	f0.pos = Vector2(-200.0, 360.0)
	fundo.avancar(0.1)
	verificar(f0.pos.x > 0.0, "wrap-around quando sai pela esquerda")

	f0.pos = Vector2(1600.0, 360.0)
	fundo.avancar(0.1)
	verificar(f0.pos.x < 1280.0, "wrap-around quando sai pela direita")

	if raiz != null:
		fundo.queue_free()


func test_menu_instanciacao_e_componentes() -> void:
	var menu: Control = MENU_SCN.instantiate()
	menu._ready()
	# Verifica que possui FundoAbstrato
	var tem_fundo := false
	for f in menu.get_children():
		if f is FundoAbstrato:
			tem_fundo = true
			break
	verificar(tem_fundo, "menu principal contém nó FundoAbstrato")

	# Verifica que possui os botões principais
	var botoes: Array[String] = []
	for b in menu.find_children("*", "Button", true, false):
		botoes.append((b as Button).text)
	verificar(botoes.has("Novo jogo"), "botão Novo jogo presente")
	verificar(botoes.has("Demonstração (fábrica pronta, construção livre)"), "botão Demonstração presente")
	verificar(botoes.has("Configurações"), "botão Configurações presente")

	menu.free()
