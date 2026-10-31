class_name Salvamento
## Salva e carrega a partida inteira num arquivo de texto (var_to_str: aceita Vector2/Vector2i e dicionários).
## Grava num arquivo temporário e troca no fim — se o jogo fechar no meio, o salvo anterior continua inteiro.

const VERSAO := 1

static var pasta := "user://salvos"      ## os testes trocam (nunca gravam no save real)
static var _tarefa := -1                 ## gravação em segundo plano em andamento (WorkerThreadPool)
static var _ok_tarefa := true


static func arquivo() -> String:
	return pasta.path_join("partida.sav")


static func existe() -> bool:
	concluir()
	return FileAccess.file_exists(arquivo())


## Grava já (fechar o jogo, Salvar agora). Se há gravação em segundo plano, espera ela: nunca duas no mesmo arquivo.
static func gravar(dados: Dictionary) -> bool:
	concluir()
	return _escrever(dados)


## Salvar automático: quem chama monta os dados no quadro; aqui fica a cópia (a partida segue mudando enquanto isto
## escreve) e o texto + disco vão para outra thread. false = a anterior ainda não acabou; tenta depois.
static func gravar_em_segundo_plano(dados: Dictionary) -> bool:
	if em_andamento():
		return false
	concluir()
	var copia := dados.duplicate(true)
	_tarefa = WorkerThreadPool.add_task(func(): _ok_tarefa = _escrever(copia), true, "salvar partida")
	return true


static func em_andamento() -> bool:
	return _tarefa >= 0 and not WorkerThreadPool.is_task_completed(_tarefa)


## Espera a gravação em segundo plano. Devolve se a última deu certo.
static func concluir() -> bool:
	if _tarefa >= 0:
		WorkerThreadPool.wait_for_task_completion(_tarefa)
		_tarefa = -1
	return _ok_tarefa


## Texto completo num temporário e só no fim troca pelo salvo: erro ou queda no meio deixam o anterior inteiro.
static func _escrever(dados: Dictionary) -> bool:
	DirAccess.make_dir_recursive_absolute(pasta)
	dados["versao"] = VERSAO
	dados["salvo_em"] = Time.get_datetime_string_from_system()
	var tmp := arquivo() + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(var_to_str(dados))
	var erro := f.get_error()
	f.close()
	if erro != OK:
		DirAccess.remove_absolute(tmp)
		return false
	return DirAccess.rename_absolute(tmp, arquivo()) == OK


static func ler() -> Dictionary:
	if not existe():
		return {}
	var v = str_to_var(FileAccess.get_file_as_string(arquivo()))
	if not (v is Dictionary) or int(v.get("versao", 0)) != VERSAO:
		return {}
	return v


static func apagar() -> void:
	if existe():
		DirAccess.remove_absolute(arquivo())
