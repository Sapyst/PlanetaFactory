extends Caso
## Estoque do núcleo na tela: o que aparece, em que ordem, números curtos e como reparte no espaço.


func test_itens_visiveis() -> void:
	var est := {"carvao": 3, "placa_cobre": 7, "pedra": 0, "placa_ferro": 1}
	var l := PainelRecursos.itens_visiveis(est, false)
	igual(l.slice(0, 2), ["placa_ferro", "placa_cobre"], "principais primeiro")
	verificar(l.has("carvao"), "o resto do estoque aparece")
	verificar(not l.has("pedra"), "zerado some")
	igual(PainelRecursos.itens_visiveis(est, true), PainelRecursos.PRINCIPAIS, "resumo: só os principais, mesmo zerados")
	igual(PainelRecursos.itens_visiveis({"item_de_save_antigo": 2}, false), ["item_de_save_antigo"], "item desconhecido não some")


func test_numero_curto() -> void:
	igual(PainelRecursos.numero_curto(0), "0")
	igual(PainelRecursos.numero_curto(9999), "9999")
	igual(PainelRecursos.numero_curto(12345), "12k")
	igual(PainelRecursos.numero_curto(1234567), "1,2M")
	verificar(PainelRecursos.numero_curto(99999999).length() <= 5, "cabe na casa")


func test_colunas() -> void:
	var h := PainelRecursos.ALTURA_CASA + PainelRecursos.SEPARACAO
	igual(PainelRecursos.colunas_para(10, false, 600.0), 1, "cabe em uma coluna")
	igual(PainelRecursos.colunas_para(40, false, h * 15.0), 3, "transborda para mais colunas")
	igual(PainelRecursos.colunas_para(0, false, 600.0), 1, "vazio não quebra")
	var l := PainelRecursos.LARGURA_CASA + PainelRecursos.SEPARACAO + 2
	igual(PainelRecursos.colunas_para(10, true, l * 4.0), 4, "em linha: as que couberem")
	igual(PainelRecursos.colunas_para(3, true, l * 40.0), 3, "em linha: não mais que as casas")
	igual(PainelRecursos.colunas_para(3, true, 1.0), 1, "sem espaço: ao menos uma")


func test_config_padrao() -> void:
	igual(Sessao.config.get("recursos_orientacao"), "vertical", "padrão vertical")


func test_todo_item_tem_icone() -> void:
	for k in Registro.itens:
		verificar(TelaPesquisa._tex_item(k) != null, "ícone de %s" % k)
