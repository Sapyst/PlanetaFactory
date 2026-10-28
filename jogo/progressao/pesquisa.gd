class_name Pesquisa
extends RefCounted
## Árvore de pesquisa (dados/progressao.json). Laboratórios consomem pacotes de pesquisa na pesquisa ativa;
## completou os pacotes, libera peças e receitas. `livre` = modo demonstração: tudo liberado.

var livre := false
var concluidas: Dictionary = {}
var ativa := ""
var feitos := 0                  ## pacotes já gastos na ativa
var _d: Dictionary


func _init(p_livre := false) -> void:
	livre = p_livre
	_d = Registro.progressao


func pesquisas() -> Dictionary:
	return _d.get("pesquisas", {})


func disponivel(id: String) -> bool:
	if concluidas.has(id) or not pesquisas().has(id):
		return false
	for r in pesquisas()[id].get("requer", []):
		if not concluidas.has(r):
			return false
	return true


func escolher(id: String) -> void:
	if disponivel(id) and id != ativa:
		ativa = id
		feitos = 0


func pacotes_faltando() -> int:
	return int(pesquisas()[ativa].pacotes) - feitos if ativa != "" else 0


## Segundos de laboratório por pacote na pesquisa ativa.
func tempo_por_pacote() -> float:
	return float(pesquisas()[ativa].get("tempo", 5)) if ativa != "" else 0.0


## Um pacote consumido. Devolve o id concluído (ou "").
func avancar() -> String:
	if ativa == "":
		return ""
	feitos += 1
	if feitos >= int(pesquisas()[ativa].pacotes):
		var fim := ativa
		concluidas[fim] = true
		ativa = ""
		feitos = 0
		return fim
	return ""


func peca_liberada(nome: String) -> bool:
	if livre or nome in _d.get("liberado_inicio", []):
		return true
	for id in concluidas:
		if nome in pesquisas()[id].get("libera", []):
			return true
	return false


func receita_liberada(r: String) -> bool:
	if livre or r in _d.get("receitas_inicio", []) or Registro.receitas.get(r, {}).get("maquina", "") in ["extrator", "broca", "bomba"]:
		return true
	for id in concluidas:
		if r in pesquisas()[id].get("receitas", []):
			return true
	return false


## Que pesquisa libera esta peça (para a dica "precisa pesquisar …").
func quem_libera(nome: String) -> String:
	for id in pesquisas():
		if nome in pesquisas()[id].get("libera", []):
			return pesquisas()[id].nome
	return ""


func estado() -> Dictionary:
	return {"livre": livre, "concluidas": concluidas.keys(), "ativa": ativa, "feitos": feitos}


func restaurar(d: Dictionary) -> void:
	livre = d.livre
	concluidas.clear()
	for c in d.concluidas:
		concluidas[c] = true
	ativa = d.ativa
	feitos = d.feitos
