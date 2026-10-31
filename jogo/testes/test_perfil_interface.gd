extends Caso
## Perfis da interface (tabela Tema.MEDIDAS): textura e tema do celular são os de sempre; o PC é menor e mais fino de verdade.
## A comparação de cada controle com as medidas gravadas antes do perfil PC precisa de árvore rodando: testes/conferir_celular.gd,
## que o ferramentas/testar.sh chama com `-- celular`.


func _depois() -> void:
	Tema.pc = Tema.detectar_pc()


func test_tema_celular_textura_de_sempre() -> void:
	Tema.pc = false
	var c := Tema.chapa_estilo()
	igual(int(c.texture_margin_left), 18, "chapa grossa")
	igual(int(c.content_margin_left), 14, "margem")
	igual(c.texture.get_width(), 96, "textura de sempre")
	igual(Tema.botao_estilo("normal").texture.get_width(), 48, "placa de sempre")
	igual(Tema.criar().default_font_size, 18, "fonte")
	_depois()


func test_pc_e_menor_em_tudo() -> void:
	for k in Tema.MEDIDAS:
		var par: Array = Tema.MEDIDAS[k]
		if k in ["zoom_ref"]:
			continue
		if par[0] is Vector2:
			verificar((par[1] as Vector2).x <= (par[0] as Vector2).x and (par[1] as Vector2).y <= (par[0] as Vector2).y, k + " não cresce no PC")
		elif k not in ["largura_estreita"]:
			verificar(float(par[1]) <= float(par[0]), k + " não cresce no PC")
	Tema.pc = true
	igual(Tema.chapa_estilo().texture.get_width(), 48, "chapa fina")
	verificar(Tema.botao_estilo("normal").texture.get_width() < 48, "placa fina")
	verificar(Tema.n("f_peq") >= 11, "letra de texto legível")
	igual(Tema.com_atalho("✕ Remover", "X"), "✕ Remover [X]", "atalho à vista")
	Tema.pc = false
	igual(Tema.com_atalho("✕ Remover", "X"), "✕ Remover", "celular sem atalho")
	_depois()


func test_escala_nao_fica_pequena_duas_vezes() -> void:
	# 100% no PC: 1 ponto = 1 pixel até 1600×900; acima, tela lógica de 1600×900
	var efetivo := func(jan: Vector2, txt: float) -> float:
		return Sessao.fator_escala(txt, jan, false) * minf(jan.x / 1280.0, jan.y / 720.0)
	perto(efetivo.call(Vector2(1280, 720), 1.0), 1.0, 1e-4, "720p: 1:1")
	perto(efetivo.call(Vector2(1920, 1080), 1.0), 1.2, 1e-4, "1080p: 1,2")
	perto(efetivo.call(Vector2(2560, 1440), 1.0), 1.6, 1e-4, "1440p: 1,6")
	perto(efetivo.call(Vector2(1920, 1080), 1.6), 1.92, 1e-4, "a escala vale por cima")
	perto(efetivo.call(Vector2(1920, 1080), 0.68), 0.816, 1e-4, "68%")
	perto(Sessao.fator_escala(0.8, Vector2(64, 64), false), 0.8, 1e-6, "sem janela de verdade: a escala pura")
