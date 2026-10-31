extends RefCounted

const FAIXA_MOVE := "barra/0/3/0/0"      ## texto da faixa: a largura agora vem do vão livre


func _dump(n: Node, cam: String, out: Dictionary) -> void:
	if n is Control:
		var c: Control = n
		var fs := -1
		if c is Label or c is Button or c is OptionButton:
			fs = c.get_theme_font_size("font_size")
		out[cam] = {"cl": c.get_class(), "min": [c.custom_minimum_size.x, c.custom_minimum_size.y], "fs": fs}
	var i := 0
	for f in n.get_children():
		if not f.name.begins_with("_"):
			_dump(f, cam + "/%d" % i, out)
		i += 1


func _q(a: SceneTree, n: int) -> void:
	for i in n:
		await a.process_frame


func rodar(a: SceneTree) -> void:
	if Tema.pc:
		print("CELULAR ERRO: rode com -- celular")
		a.quit(1)
		return
	Salvamento.pasta = "user://testes_salvos"
	var raiz := a.root
	var sess = raiz.get_node("Sessao")
	sess.config.texto = 1.35                    # como no aparelho, sem olhar a configuração de quem está jogando (nada é gravado)
	sess.aplicar()
	await _q(a, 3)
	var novo := {}
	var barra := BarraConstrucao.new()
	raiz.add_child(barra)
	await _q(a, 3)
	var d := {}
	_dump(barra, "barra", d)
	novo["barra"] = d
	barra._tocar_categoria(3)
	barra.acoes_em(Vector2(600, 300), true, false)
	barra.modo_construcao("Construindo: Fornalha — toque no chão · clique direito ou Sair para parar")
	barra.dica("Fornalha — clique para pôr · custo: 5 pedra (tem 10) · R gira")
	barra.situacao("Dia 08:00 · Verão · Limpo · Vento 30% N\nPoluição aqui: 0.0\nNinhos: 1\nPesquisa: A 1/3", "")
	barra.estoque({"placa_ferro": 12, "pedra": 3})
	barra.detalhe("Montadora", "Integridade: 100 de 100\nEstado: sem energia", [{"texto": "Ligada", "ligado": true, "acao": func(): pass}, {"titulo": "Grupo"}, {"texto": "Item", "icone": TelaPesquisa._tex_item("pedra"), "acao": func(): pass}, {"texto": "Receita X", "acao": func(): pass}])
	barra.detalhe_maquina({"icone": TelaPesquisa._tex_peca("montadora"), "entradas": [{"tex": TelaPesquisa._tex_item("pedra"), "n": 1, "dica": "x", "falta": true}], "saidas": [{"tex": TelaPesquisa._tex_item("pedra"), "n": 1, "dica": "x"}], "progresso": 0.5, "energia": 0.5})
	await _q(a, 4)
	d = {}
	_dump(barra, "barra", d)
	novo["barra_aberta"] = d
	barra.visible = false
	var pq := Pesquisa.new()
	var tela := TelaPesquisa.new()
	tela.pesquisa = pq
	tela.tema = barra._tema
	raiz.add_child(tela)
	await _q(a, 2)
	tela._sel = "automacao" if pq.pesquisas().has("automacao") else pq.pesquisas().keys()[0]
	tela.abrir()
	await _q(a, 4)
	d = {}
	_dump(tela, "tela", d)
	novo["pesquisa"] = d
	tela.fechar()
	var mp := MenuPausa.new()
	raiz.add_child(mp)
	await _q(a, 2)
	mp.abrir()
	a.paused = false
	await _q(a, 3)
	d = {}
	_dump(mp, "pausa", d)
	novo["pausa"] = d
	mp._caixa.visible = false
	mp._config.visible = true
	await _q(a, 3)
	d = {}
	_dump(mp, "pausa", d)
	novo["config"] = d
	var antes: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testes/medidas_celular.json"))
	var total := 0
	var dif := 0
	for k in antes:
		for x in antes[k]:
			total += 1
			if x.p == FAIXA_MOVE:
				continue
			var y = (novo[k] as Dictionary).get(x.p)
			if y == null or y.cl != x.cl or int(y.fs) != int(x.fs) or absf(y.min[0] - x.min[0]) > 0.02 or absf(y.min[1] - x.min[1]) > 0.02:
				dif += 1
				print("CELULAR mudou %s %s %s: antes %s %s, agora %s" % [k, x.p, x.cl, x.min, x.fs, y])
	print("CELULAR %s: %d controles comparados, %d diferentes" % ["OK" if dif == 0 and total > 400 else "FALHA", total, dif])
	a.quit(0 if dif == 0 else 1)
