extends Caso
## Testes do Antisserrilhado (Pedido 4 — Tarefa 4):
## - Configuração com 3 modos: Desligado, Leve (padrão) e Alto.
## - Renderizador Mobile: Leve usa FXAA (screen_space_aa) sem alocação pesada de buffers multisample.
## - Alto combina MSAA 4X e FXAA para máxima nitidez de geometria e shaders.
## - Integração com Sessao.aplicar_antialiasing(), persistência de configuração e PainelConfig.


func test_configuracao_padrao_e_modos() -> void:
	verificar(Sessao.config.has("antialiasing"), "Sessao possui chave antialiasing")
	var vp := SubViewport.new()

	# 1. Modo Desligado
	Sessao.aplicar_antialiasing(vp, "desligado")
	igual(vp.msaa_3d, Viewport.MSAA_DISABLED, "desligado: MSAA 3D desativado")
	igual(vp.screen_space_aa, Viewport.SCREEN_SPACE_AA_DISABLED, "desligado: FXAA desativado")

	# 2. Modo Leve (padrão recomendado para Mobile e PC)
	Sessao.aplicar_antialiasing(vp, "leve")
	igual(vp.msaa_3d, Viewport.MSAA_DISABLED, "leve: MSAA 3D desativado para economia no mobile")
	igual(vp.screen_space_aa, Viewport.SCREEN_SPACE_AA_FXAA, "leve: FXAA ativado")

	# 3. Modo Alto
	Sessao.aplicar_antialiasing(vp, "alto")
	igual(vp.msaa_3d, Viewport.MSAA_4X, "alto: MSAA 4X ativado")
	igual(vp.screen_space_aa, Viewport.SCREEN_SPACE_AA_FXAA, "alto: FXAA ativado junto")

	# 4. Fallback padrão para valor desconhecido
	Sessao.aplicar_antialiasing(vp, "invalido")
	igual(vp.msaa_3d, Viewport.MSAA_DISABLED, "fallback: MSAA desativado")
	igual(vp.screen_space_aa, Viewport.SCREEN_SPACE_AA_FXAA, "fallback: FXAA ativado")

	vp.free()


func test_painel_config_opcoes_antialiasing() -> void:
	var painel := PainelConfig.new()
	painel._ready()
	var encontrou_seletor := false
	var op_aa: OptionButton = null

	# Percorrer os filhos do corpo para encontrar o OptionButton com as 3 opções
	for c in painel._corpo.get_children():
		if c is HBoxContainer:
			for f in c.get_children():
				if f is OptionButton and f.item_count == 3:
					if f.get_item_text(0) == "Desligado" and f.get_item_text(1) == "Leve" and f.get_item_text(2) == "Alto":
						encontrou_seletor = true
						op_aa = f
						break

	verificar(encontrou_seletor, "encontrou o OptionButton de Antisserrilhado no PainelConfig")
	verificar(op_aa != null, "seletor de antisserrilhado instanciado")
	if op_aa != null:
		igual(op_aa.item_count, 3, "três opções: Desligado, Leve, Alto")
		igual(op_aa.get_item_text(0), "Desligado", "opção 0 é Desligado")
		igual(op_aa.get_item_text(1), "Leve", "opção 1 é Leve")
		igual(op_aa.get_item_text(2), "Alto", "opção 2 é Alto")

	painel.free()


func test_persistencia_antialiasing() -> void:
	var arq_antigo := Sessao.arq_config
	var arq_teste := "user://test_antialiasing_%d.cfg" % randi()
	Sessao.arq_config = arq_teste

	var val_antigo = Sessao.config.get("antialiasing", "leve")
	Sessao.config["antialiasing"] = "alto"
	Sessao.salvar_config()

	var cf := ConfigFile.new()
	var err := cf.load(arq_teste)
	igual(err, OK, "salvou arquivo de configuração de teste")
	igual(cf.get_value("jogo", "antialiasing", ""), "alto", "leu chave antialiasing gravada como alto")

	# Limpar e restaurar
	DirAccess.remove_absolute(ProjectSettings.globalize_path(arq_teste))
	Sessao.config["antialiasing"] = val_antigo
	Sessao.arq_config = arq_antigo
