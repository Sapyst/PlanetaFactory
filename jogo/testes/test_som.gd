extends Caso
## Testes do sistema de som: síntese procedural a 44,1 kHz, limites de vozes, barramentos e configurações.


func test_sons_existem() -> void:
	var sons_esperados := [
		"clique", "construir", "remover", "alerta", "pesquisa", "derrota",
		"tiro", "tiro_metralhadora", "tiro_energia", "tiro_foguete", "tiro_enxame",
		"tiro_artilharia", "tiro_perfurante", "tiro_carregada", "tiro_drone",
		"impacto", "impacto_aranha", "impacto_chao", "impacto_estrutura",
		"explosao", "explosao_grande", "mina_pulso",
		"maq_fornalha", "maq_montadora", "maq_broca", "maq_esteira",
		"apito_trem", "trem_trilho",
		"chuva", "trovao", "vento_forte",
		"aranha_passo", "aranha_morre",
		"reentrada", "fogo", "faisca"
	]
	for nome in sons_esperados:
		verificar(Som.tem_som(nome), "Som %s deve estar carregado" % nome)


func test_taxa_amostragem_44100() -> void:
	for k in Som._sons.keys():
		var stream = Som._sons[k]
		if stream is AudioStreamWAV:
			var wav: AudioStreamWAV = stream
			igual(wav.mix_rate, 44100, "Som %s deve ser WAV 44,1 kHz" % k)


func test_barramentos_e_roteamento() -> void:
	igual(Som.barramento_do_som("chuva"), "Ambiente", "chuva roteada para Ambiente")
	igual(Som.barramento_do_som("trovao"), "Ambiente", "trovao roteado para Ambiente")
	igual(Som.barramento_do_som("vento_forte"), "Ambiente", "vento_forte roteado para Ambiente")
	igual(Som.barramento_do_som("tiro_metralhadora"), "Efeitos", "tiro roteado para Efeitos")
	igual(Som.barramento_do_som("maq_broca"), "Efeitos", "máquina roteada para Efeitos")
	igual(Som.barramento_do_som("clique"), "Efeitos", "clique roteado para Efeitos")


func test_limites_e_intervalos() -> void:
	verificar(Som.INTERVALO.has("tiro_metralhadora"), "intervalo para tiro_metralhadora")
	verificar(Som.INTERVALO.has("maq_broca"), "intervalo para maq_broca")
	verificar(Som.INTERVALO.has("aranha_passo"), "intervalo para aranha_passo")
	verificar(Som.MAX_VOZES.has("maq_fornalha"), "limite de vozes para maq_fornalha")
	verificar(Som.MAX_VOZES.has("maq_broca"), "limite de vozes para maq_broca")
	verificar(int(Som.MAX_VOZES["maq_broca"]) <= 3, "máquinas com limite de até 3 vozes simultâneas")


func test_configuracoes_volume() -> void:
	var backup_config := Sessao.config.duplicate()
	Sessao.config.volume_geral = 0.5
	Sessao.config.volume = 0.4
	Sessao.config.volume_ambiente = 0.3
	Sessao.aplicar()
	var idx_master := AudioServer.get_bus_index("Master")
	var idx_efeitos := AudioServer.get_bus_index("Efeitos")
	var idx_ambiente := AudioServer.get_bus_index("Ambiente")
	verificar(idx_master >= 0, "barramento Master existe")
	verificar(idx_efeitos >= 0, "barramento Efeitos existe")
	verificar(idx_ambiente >= 0, "barramento Ambiente existe")
	perto(db_to_linear(AudioServer.get_bus_volume_db(idx_master)), 0.5, 0.05, "volume Master aplicado")
	perto(db_to_linear(AudioServer.get_bus_volume_db(idx_efeitos)), 0.4, 0.05, "volume Efeitos aplicado")
	perto(db_to_linear(AudioServer.get_bus_volume_db(idx_ambiente)), 0.3, 0.05, "volume Ambiente aplicado")
	Sessao.config = backup_config
	Sessao.aplicar()
