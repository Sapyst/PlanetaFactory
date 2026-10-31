extends Caso
## Salvar automático: relógio (AutoSalvar) e escrita atômica, também em segundo plano. Roda na pasta de testes.


func test_nao_toca_no_save_real() -> void:
	verificar(Salvamento.pasta != "user://salvos", "testes usam outra pasta")
	verificar(Sessao.arq_config != "user://configuracoes.cfg", "e outra configuração")


func test_relogio() -> void:
	var a := AutoSalvar.new()
	verificar(not a.avancar(10.0, 60.0, true), "ainda não")
	verificar(not a.avancar(49.0, 60.0, true), "59 s: ainda não")
	verificar(a.avancar(2.0, 60.0, true), "passou de 60 s")
	verificar(not a.avancar(1.0, 60.0, true), "recomeçou a contar")
	var d := AutoSalvar.new()
	for i in 100:
		verificar(not d.avancar(60.0, 0.0, true), "desligado nunca salva")
	verificar(not d.avancar(60.0, 300.0, true), "religou: conta do zero")
	verificar(d.avancar(241.0, 300.0, true), "e salva no novo intervalo")


func test_abertura_segura() -> void:
	var a := AutoSalvar.new()
	verificar(not a.avancar(100.0, 60.0, false), "na abertura não salva, mesmo vencido")
	verificar(not a.avancar(100.0, 60.0, false), "segue segurando")
	verificar(a.avancar(0.1, 60.0, true), "acabou a abertura: salva")


func test_encurtar_intervalo_vale_na_hora() -> void:
	var a := AutoSalvar.new()
	verificar(not a.avancar(10.0, 1800.0, true), "30 min")
	verificar(not a.avancar(10.0, 60.0, true), "trocou para 1 min")
	verificar(a.avancar(51.0, 60.0, true), "vale o novo")


func test_escrita_atomica() -> void:
	Salvamento.apagar()
	verificar(Salvamento.gravar({"marca": 1, "v": Vector2i(2, 3)}), "grava")
	igual(Salvamento.ler().get("marca"), 1, "lê")
	igual(Salvamento.ler().get("v"), Vector2i(2, 3), "tipos do Godot voltam iguais")
	verificar(not FileAccess.file_exists(Salvamento.arquivo() + ".tmp"), "sem temporário largado")
	# temporário impossível de criar (uma pasta no lugar dele): falha e o salvo anterior fica inteiro
	DirAccess.make_dir_absolute(Salvamento.arquivo() + ".tmp")
	verificar(not Salvamento.gravar({"marca": 2}), "avisa que falhou")
	igual(Salvamento.ler().get("marca"), 1, "o anterior continua")
	DirAccess.remove_absolute(Salvamento.arquivo() + ".tmp")


func test_segundo_plano() -> void:
	Salvamento.apagar()
	var estruturas := {1: {"nome": "braco", "filtros": ["carvao"]}}
	var dados := {"marca": 1, "mapa": {"estruturas": estruturas}, "grande": []}
	for i in 20000:
		dados.grande.append(Vector2i(i, i))
	verificar(Salvamento.gravar_em_segundo_plano(dados), "começou")
	estruturas[1]["filtros"] = ["mudou_depois"]      # a partida segue: o save é a foto do momento
	dados["marca"] = 99
	verificar(Salvamento.concluir(), "terminou bem")
	var lido := Salvamento.ler()
	igual(lido.get("marca"), 1, "gravou a foto do momento")
	igual(lido.mapa.estruturas[1].filtros, ["carvao"], "cópia profunda")
	igual(lido.grande.size(), 20000, "inteiro")
	# em cima de uma em andamento: Salvar agora espera a automática; quem fica é o mais novo
	verificar(Salvamento.gravar_em_segundo_plano({"marca": 2, "grande": dados.grande}), "outra")
	verificar(Salvamento.gravar({"marca": 3}), "manual espera")
	igual(Salvamento.ler().get("marca"), 3, "o mais novo fica")
	Salvamento.apagar()
	verificar(not Salvamento.existe(), "apagou")


func test_opcoes_na_config() -> void:
	igual(PainelConfig.AUTOSALVAR, [0, 60, 120, 300, 600, 900, 1800], "desligado, 1, 2, 5, 10, 15, 30 min")
	igual(PainelConfig._indice_autosalvar(120), 2, "2 min")
	igual(PainelConfig._indice_autosalvar(0), 0, "desligado")
	igual(PainelConfig._indice_autosalvar(1790), 6, "valor fora da lista: o mais perto")


func test_escala_da_interface() -> void:
	perto(Sessao.TEXTO_PADRAO, 0.8, 0.001, "antigo mínimo é o padrão")
	perto(Sessao.TEXTO_MAX, 1.6, 0.001, "máximo igual")
	verificar(Sessao.TEXTO_MIN < Sessao.TEXTO_PADRAO, "mínimo abaixo do padrão")
	perto(Sessao.TEXTO_MIN / Sessao.TEXTO_PADRAO, 0.85, 0.01, "uns 15% menor")
	perto(Sessao.texto_migrado(1.0, true, false, false), 0.8, 0.001, "nunca mexeu: padrão novo")
	perto(Sessao.texto_migrado(1.3, true, false, false), 1.3, 0.001, "escolheu outro: fica")
	perto(Sessao.texto_migrado(0.8, true, false, false), 0.8, 0.001, "já estava no mínimo: fica")
	perto(Sessao.texto_migrado(1.0, true, true, false), 1.0, 0.001, "depois de migrar, 100% é escolha: fica")
	perto(Sessao.texto_migrado(1.0, true, false, true), 1.0, 0.001, "celular não entra nisso")
