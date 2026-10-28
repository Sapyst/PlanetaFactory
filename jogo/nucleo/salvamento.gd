class_name Salvamento
## Salva e carrega a partida inteira num arquivo de texto (var_to_str: aceita Vector2/Vector2i e dicionários).
## Grava num arquivo temporário e troca no fim — se o jogo fechar no meio, o salvo anterior continua inteiro.

const PASTA := "user://salvos"
const ARQUIVO := "user://salvos/partida.sav"
const VERSAO := 1


static func existe() -> bool:
	return FileAccess.file_exists(ARQUIVO)


static func gravar(dados: Dictionary) -> bool:
	DirAccess.make_dir_recursive_absolute(PASTA)
	dados["versao"] = VERSAO
	dados["salvo_em"] = Time.get_datetime_string_from_system()
	var tmp := ARQUIVO + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(var_to_str(dados))
	f.close()
	return DirAccess.rename_absolute(tmp, ARQUIVO) == OK


static func ler() -> Dictionary:
	if not existe():
		return {}
	var v = str_to_var(FileAccess.get_file_as_string(ARQUIVO))
	if not (v is Dictionary) or int(v.get("versao", 0)) != VERSAO:
		return {}
	return v


static func apagar() -> void:
	if existe():
		DirAccess.remove_absolute(ARQUIVO)
