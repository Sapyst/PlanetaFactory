extends SceneTree
## Medição sem janela (checkup): tempo de abertura (motor + autoloads, menu, partida), ms por quadro (média, p95, pior,
## quadros acima de 33 ms e onde caíram), tempo de _process/_physics, memória, nós e objetos.
##   godot --headless --audio-driver Dummy --path jogo -s res://ferramentas/medir.gd -- [novo] [quadros N] [camera X Z D]
## Sem janela não há GPU: os números são só da CPU. "quadro (relógio)" é o tempo entre quadros (sem janela o motor
## segura em ~7 ms, então só os picos dizem algo); "scripts no quadro" é do primeiro ao último _process (o que o
## código do jogo custa de verdade). Grava em user://testes_salvos (nunca no save de quem joga).

const QUADROS_PADRAO := 600
const ENGASGO_MS := 33.0


func _initialize() -> void:
	Salvamento.pasta = "user://testes_salvos"
	load("res://nucleo/sessao.gd").arq_config = "user://testes_configuracoes.cfg"
	_medir.call_deferred()


func _medir() -> void:
	var args := OS.get_cmdline_user_args()
	var quadros := QUADROS_PADRAO
	var qi := args.find("quadros")
	if qi >= 0 and args.size() > qi + 1:
		quadros = int(args[qi + 1])
	var t_motor := Time.get_ticks_msec()
	print("MEDIR motor + autoloads (Registro, Sessao, Som): %d ms" % t_motor)
	# menu: monta a interface e carrega a foto de fundo; fica 1 s na tela (como quem lê) e "clica"
	var t0 := Time.get_ticks_usec()
	var menu: Node = (load("res://cenas/menu.tscn") as PackedScene).instantiate()
	root.add_child(menu)
	await process_frame
	var t_menu := (Time.get_ticks_usec() - t0) / 1000.0
	await create_timer(1.0).timeout
	var pronta := ResourceLoader.load_threaded_get_status("res://cenas/mundo_demo.tscn") == ResourceLoader.THREAD_LOAD_LOADED
	t0 = Time.get_ticks_usec()
	menu._ir("novo" if args.has("novo") else "demo")        # o botão do menu: troca de cena do motor (current_scene certo)
	await process_frame
	while current_scene == null or current_scene == menu:
		await process_frame
	var t_ready := (Time.get_ticks_usec() - t0) / 1000.0
	var cena: Node = current_scene
	t0 = Time.get_ticks_usec()
	await process_frame
	var t_q1 := (Time.get_ticks_usec() - t0) / 1000.0
	print("MEDIR abertura: menu %.0f ms · cena do jogo compilada durante o menu: %s · clique → jogo pronto (instanciar + _ready%s) %.0f ms · 1º quadro %.0f ms · total até jogar (menos o 1 s no menu) %.0f ms" % [
			t_menu, "sim" if pronta else "não", "" if pronta else " + carregar", t_ready, t_q1, Time.get_ticks_msec() - 1000])
	var tempos: PackedFloat32Array = []
	var ini := _Marco.new()                    # primeiro e último _process do quadro: o que os scripts custam
	ini.process_priority = -100000
	var fim := _Marco.new()
	fim.process_priority = 100000
	root.add_child(ini)
	root.add_child(fim)
	var scripts: PackedFloat32Array = []
	var nos_ini: int = Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	var t_ant := Time.get_ticks_usec()
	for i in quadros:
		await process_frame
		var ag := Time.get_ticks_usec()
		tempos.append((ag - t_ant) / 1000.0)
		t_ant = ag
		scripts.append((fim.marca - ini.marca) / 1000.0)
	_relatorio("quadro (relógio)", tempos)
	_relatorio("scripts no quadro", scripts)
	print("MEDIR memória: estática %.1f MB · nós %d (eram %d no 1º quadro) · objetos %d · recursos %d · órfãos %d" % [
			Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0,
			Performance.get_monitor(Performance.OBJECT_NODE_COUNT), nos_ini,
			Performance.get_monitor(Performance.OBJECT_COUNT), Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),
			Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)])
	if cena.get("mapa") != null:
		print("MEDIR mundo: %d estruturas · %d chunks" % [cena.mapa.estruturas.size(), cena.chunks.size()])
	quit(0)


func _relatorio(nome: String, v: PackedFloat32Array) -> void:
	var ord := v.duplicate()
	ord.sort()
	var soma := 0.0
	var picos: Array[String] = []
	for i in v.size():
		soma += v[i]
		if v[i] > ENGASGO_MS and picos.size() < 12:
			picos.append("%d:%.0f" % [i, v[i]])
	var acima := 0
	for x in v:
		if x > ENGASGO_MS:
			acima += 1
	print("MEDIR %s (%d quadros): média %.2f ms · p95 %.2f · p99 %.2f · pior %.1f · >%d ms: %d quadros%s" % [
			nome, v.size(), soma / v.size(), ord[int(ord.size() * 0.95)], ord[int(ord.size() * 0.99)], ord[-1], int(ENGASGO_MS), acima,
			"" if picos.is_empty() else " (quadro:ms " + " ".join(picos) + ")"])


## Nó que só anota o instante do seu _process (um com prioridade mínima, outro com máxima).
class _Marco extends Node:
	var marca := 0
	func _process(_d: float) -> void:
		marca = Time.get_ticks_usec()
