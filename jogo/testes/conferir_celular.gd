extends SceneTree
## Monta a interface no perfil celular (rodar com `-- celular`) e compara cada controle com testes/medidas_celular.json, gravado do
## jogo ANTES de existir o perfil PC. Sai com 1 se algo mudou. O que se espera que mude fica de fora (FAIXA_MOVE: item 8, desvia dos painéis).
## O script real é carregado depois do mundo pronto (os autoloads só existem aí).

var _i


func _initialize() -> void:
	_i = load("res://testes/conferir_celular_interno.gd").new()
	_i.rodar.call_deferred(self)
