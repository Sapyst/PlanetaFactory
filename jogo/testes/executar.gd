extends SceneTree
## Roda todos os testes sem janela:
##   godot --headless --path jogo -s res://testes/executar.gd            (todos)
##   godot --headless --path jogo -s res://testes/executar.gd -- mundo   (só arquivos que contêm "mundo")
## Sai com código 1 se algo falhar.

func _initialize() -> void:
	# testes nunca gravam no save nem na configuração de quem está jogando
	Salvamento.pasta = "user://testes_salvos"
	load("res://nucleo/sessao.gd").arq_config = "user://testes_configuracoes.cfg"
	var filtro := ""
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		filtro = args[0]
	var total_falhas := 0
	var total_ver := 0
	var arquivos := DirAccess.get_files_at("res://testes")
	arquivos.sort()
	for f in arquivos:
		if not (f.begins_with("test_") and f.ends_with(".gd")) or (filtro != "" and not f.contains(filtro)):
			continue
		var script: GDScript = load("res://testes/" + f)
		if script == null or not script.can_instantiate():
			print("FALHA %s  (não compila)" % f)
			total_falhas += 1
			continue
		var caso: Caso = script.new()
		var t0 := Time.get_ticks_msec()
		for m in caso.get_method_list():
			var nome: String = m.name
			if nome.begins_with("test_"):
				caso._atual = nome
				caso.call(nome)
		total_falhas += caso.falhas.size()
		total_ver += caso.verificacoes
		print("%s %s  (%d verificações, %d ms)" % ["OK  " if caso.falhas.is_empty() else "FALHA", f, caso.verificacoes, Time.get_ticks_msec() - t0])
		for x in caso.falhas:
			print("      - ", x)
	print("TOTAL: %d verificações, %d falhas" % [total_ver, total_falhas])
	quit(1 if total_falhas > 0 else 0)
