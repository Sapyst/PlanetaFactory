extends Caso
## Roda do mouse sobre a interface não dá zoom no mundo: Toque.sobre_ui (checagem central usada pelo ControleConstrucao).
## O teste com a cena inteira e eventos de verdade é o roteiro: godot --headless --path jogo -- modo demo roteiro roda_ui


func test_sobre_ui() -> void:
	var arvore: SceneTree = Engine.get_main_loop()
	var camada := CanvasLayer.new()
	arvore.root.add_child(camada)
	var raiz := Control.new()                     # como a raiz da barra: ocupa a tela, mas não recebe mouse
	raiz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	raiz.position = Vector2.ZERO
	raiz.size = Vector2(1000, 1000)
	camada.add_child(raiz)
	var painel := PanelContainer.new()
	painel.position = Vector2(10, 10)
	painel.size = Vector2(100, 100)
	raiz.add_child(painel)
	var rolagem := Control.new()                  # lista que corta o conteúdo
	rolagem.clip_contents = true
	rolagem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rolagem.position = Vector2(200, 10)
	rolagem.size = Vector2(100, 100)
	raiz.add_child(rolagem)
	var longo := Button.new()
	longo.position = Vector2.ZERO
	longo.size = Vector2(100, 500)
	rolagem.add_child(longo)
	var rotulo := Label.new()                     # texto solto não segura a roda (mouse_filter IGNORE de fábrica)
	rotulo.position = Vector2(400, 10)
	rotulo.size = Vector2(100, 100)
	raiz.add_child(rotulo)

	verificar(Toque.sobre_ui(arvore, Vector2(50, 50)), "painel")
	verificar(not Toque.sobre_ui(arvore, Vector2(150, 50)), "fora: é mapa")
	verificar(Toque.sobre_ui(arvore, Vector2(250, 50)), "botão dentro da lista")
	verificar(not Toque.sobre_ui(arvore, Vector2(250, 300)), "botão cortado pela lista não conta")
	verificar(not Toque.sobre_ui(arvore, Vector2(450, 50)), "rótulo não segura a roda")
	painel.visible = false
	verificar(not Toque.sobre_ui(arvore, Vector2(50, 50)), "painel escondido não conta")
	painel.visible = true
	camada.visible = false
	verificar(not Toque.sobre_ui(arvore, Vector2(50, 50)), "camada escondida não conta")
	camada.free()
