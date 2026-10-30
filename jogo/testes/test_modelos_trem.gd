extends Caso
## Modelos da ferrovia vindos dos estudos (arte/estudos/conv_trilhos.py): o que o jogo procura neles pelo nome.
##  - carro: truque0 atrás (−Z no Godot = frente) e truque1 à frente, a ±0,85 m; vagão de carga com a "pilha";
##  - trilhos: uma malha só (DesenhoLotes usa a 1ª malha), boleto em 0,14 (onde a roda apoia), dentro do tile.


func _cena(nome: String) -> Node3D:
	return (load(Registro.modelos[nome].modelo) as PackedScene).instantiate() as Node3D


func test_carros_tem_truques() -> void:
	for nome in ["locomotiva", "vagao_carga", "vagao_tanque"]:
		var c := _cena(nome)
		for k in 2:
			var tr := c.find_child("*truque%d" % k, true, false) as Node3D
			if verificar(tr != null, "%s tem truque%d" % [nome, k]):
				perto(tr.position.z, 0.85 if k == 0 else -0.85, 0.01, "%s: truque%d a ±0,85 m do centro" % [nome, k])
				perto(tr.position.x, 0.0, 0.01, "%s: truque%d no eixo" % [nome, k])
		c.free()


func test_vagao_mostra_pilha() -> void:
	var d := DesenhoTrens.new()
	var t := Trem.new(1, GrafoTrilhos.new(), ["locomotiva", "vagao_carga", "vagao_tanque"] as Array[String])
	d._criar(t)
	var carros: Array = d._carros[1]
	verificar(carros[0].get_node_or_null("pilha") == null, "locomotiva sem pilha")
	verificar(carros[1].get_node_or_null("pilha") != null, "vagão de carga com pilha")
	verificar(carros[2].get_node_or_null("pilha") == null, "vagão-tanque sem pilha")
	d.free()


func test_trilhos_numa_malha() -> void:
	for nome in ["trilho_reto", "trilho_curva", "trilho_fim"]:
		var c := _cena(nome)
		var mis := c.find_children("*", "MeshInstance3D", true, false)
		igual(mis.size(), 1, "%s: uma malha só (lote)" % nome)
		if mis.size() > 0:
			var mi := mis[0] as MeshInstance3D
			var caixa := mi.get_aabb()
			var area: Vector2i = Registro.area(nome)
			perto(caixa.end.y if nome != "trilho_fim" else 0.14, 0.14, 0.012, "%s: boleto em 0,14" % nome)
			verificar(absf(caixa.position.x) <= area.x / 2.0 + 0.001 and absf(caixa.position.z) <= area.y / 2.0 + 0.001,
				"%s dentro do tile" % nome)
		c.free()
