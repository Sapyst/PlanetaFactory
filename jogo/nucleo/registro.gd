extends Node
## Autoload: carrega os dados do jogo (dados/*.json). Tudo que é número de jogo mora nos JSON, não no código.

var itens: Dictionary = {}
var receitas: Dictionary = {}
var estruturas: Dictionary = {}   ## regras de jogo + dados do modelo (área, portas, partes) mesclados
var modelos: Dictionary = {}      ## tudo que a arte exporta (inclui mapa, inimigos, veículos)
var biomas: Dictionary = {}
var agua: Dictionary = {}
var nomes_biomas: Array[String] = []
var menu: Dictionary = {}         ## barra de construção (categorias, rótulos, textos de bloqueio)
var inimigos: Dictionary = {}     ## poluição, ninhos, aranhas, expansão
var progressao: Dictionary = {}   ## custos, kit inicial, pesquisas
var clima: Dictionary = {}        ## estados do clima dinâmico
var recursos: Dictionary = {}     ## nomes e cores da visão de recursos
var ambiente: Dictionary = {}     ## sujeira, óleo, despejo, fogo, tufão


func _init() -> void:
	carregar()


func carregar(pasta := "res://dados") -> void:
	itens = _ler(pasta + "/itens.json")
	receitas = _sem_notas(_ler(pasta + "/receitas.json"))
	modelos = _ler(pasta + "/modelos.json")
	menu = _ler(pasta + "/menu_construcao.json")
	inimigos = _ler(pasta + "/inimigos.json")
	progressao = _ler(pasta + "/progressao.json")
	clima = _ler(pasta + "/clima.json")
	recursos = _ler(pasta + "/recursos.json")
	ambiente = _ler(pasta + "/ambiente.json")
	var regras := _sem_notas(_ler(pasta + "/estruturas.json"))
	estruturas.clear()
	for nome in regras:
		var d: Dictionary = (modelos.get(nome, {}) as Dictionary).duplicate(true)
		d.merge(regras[nome], true)
		d["nome"] = nome
		estruturas[nome] = d
	var b := _ler(pasta + "/biomas.json")
	agua = b.get("_agua", {})
	biomas = _sem_notas(b)
	biomas.erase("_agua")
	nomes_biomas.clear()
	for n in biomas:
		nomes_biomas.append(n)


## Área (w, d) em tiles; 1×1 se o modelo não tiver.
func area(nome: String) -> Vector2i:
	var m: Dictionary = modelos.get(nome, {})
	var a: Array = m.get("area", [1, 1])
	return Vector2i(int(a[0]), int(a[1]))


func receitas_da_maquina(maquina: String) -> Array[String]:
	var out: Array[String] = []
	for k in receitas:
		if receitas[k].get("maquina", "") == maquina:
			out.append(k)
	return out


func _ler(caminho: String) -> Dictionary:
	if not FileAccess.file_exists(caminho):
		push_warning("Registro: faltando " + caminho)
		return {}
	var dados = JSON.parse_string(FileAccess.get_file_as_string(caminho))
	return dados if dados is Dictionary else {}


func _sem_notas(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		if not String(k).begins_with("_"):
			out[k] = d[k]
	return out
