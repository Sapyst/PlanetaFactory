class_name Pesquisa
extends RefCounted
## Árvore de pesquisa (dados/progressao.json). Laboratórios consomem pacotes de pesquisa na pesquisa ativa;
## completou os pacotes, libera peças e receitas. `livre` = modo demonstração: tudo liberado.
##
## Infinitas ("infinita": true): nunca entram em `concluidas`; cada vez que termina sobe um nível (`niveis`), o
## bônus soma de novo, o custo do próximo nível é × CUSTO_NIVEL e a pesquisa continua sozinha no nível seguinte.
##
## Custo por tipo (como no Factorio): "pacotes" é o número de unidades e "tipos" os itens de pacote que cada
## unidade gasta, 1 de cada (sem "tipos" = só o básico). Ex.: pacotes 30 + tipos [básico, automação] =
## básico × 30 + automação × 30 na tabela de docs/ARVORE_TECNOLOGIA.md.

const CUSTO_NIVEL := 1.5          ## infinitas: custo × 1,5 a cada nível

## Tipo de pacote da árvore (arvore.json) → item.
const TIPOS_PACOTE := {"básico": "pacote_pesquisa", "automação": "pacote_automacao", "militar": "pacote_militar",
		"químico": "pacote_quimico", "ecológico": "pacote_ecologico", "tempestade": "pacote_tempestade",
		"quântico": "pacote_quantico", "gênese": "pacote_genese"}

var livre := false
var concluidas: Dictionary = {}
var ativa := ""
var feitos := 0                  ## pacotes já gastos na ativa
var niveis: Dictionary = {}      ## pesquisa infinita → níveis já feitos (cada nível soma o "bonus" de novo)
var _d: Dictionary


func _init(p_livre := false) -> void:
	livre = p_livre
	_d = Registro.progressao


func pesquisas() -> Dictionary:
	return _d.get("pesquisas", {})


## Árvore completa (dados/arvore.json): id → {nome, era, requer, pacotes [[tipo, n]], tempo, libera (texto)}.
## Inclui as pesquisas jogáveis e as que ainda não existem no jogo ("em breve").
func arvore() -> Dictionary:
	return Registro.arvore.get("nos", {})


func eras() -> Array:
	return Registro.arvore.get("eras", [])


## Pesquisa que já existe no jogo (está em progressao.json); o resto da árvore aparece como "em breve".
func jogavel(id: String) -> bool:
	return pesquisas().has(id)


func infinita(id: String) -> bool:
	return bool(pesquisas().get(id, {}).get("infinita", false))


## Nível já feito de uma infinita (0 = nunca).
func nivel(id: String) -> int:
	return int(niveis.get(id, 0))


func disponivel(id: String) -> bool:
	if concluidas.has(id) or not pesquisas().has(id):
		return false
	for r in pesquisas()[id].get("requer", []):
		if not concluidas.has(r):
			return false
	for t in tipos(id):                      # pacote que ainda não existe no jogo (químico, militar…)
		if not Registro.itens.has(t):
			return false
	return true


func escolher(id: String) -> void:
	if disponivel(id) and id != ativa:
		ativa = id
		feitos = 0


## Unidades de pesquisa (cada uma gasta 1 pacote de cada tipo). Infinita: base × 1,5^nível já feito.
func unidades(id: String) -> int:
	var n := int(pesquisas().get(id, {}).get("pacotes", 0))
	return roundi(n * pow(CUSTO_NIVEL, nivel(id))) if infinita(id) else n


## Itens de pacote que cada unidade da pesquisa gasta (1 de cada).
func tipos(id: String) -> Array:
	return pesquisas().get(id, {}).get("tipos", ["pacote_pesquisa"])


## Custo total por item: {"pacote_pesquisa": 30, "pacote_automacao": 30}.
func custo(id: String) -> Dictionary:
	var c := {}
	for t in tipos(id):
		c[t] = unidades(id)
	return c


## Nome curto do tipo de pacote ("básico", "automação"…) a partir do item.
static func nome_tipo(item: String) -> String:
	for k in TIPOS_PACOTE:
		if TIPOS_PACOTE[k] == item:
			return k
	return item


## "básico × 30 + automação × 30"
func custo_texto(id: String) -> String:
	var partes: Array[String] = []
	for t in tipos(id):
		partes.append("%s × %d" % [nome_tipo(t), unidades(id)])
	return " + ".join(partes)


## Pacote cuja receita já foi liberada (ex.: automação depois da pesquisa Automação): o laboratório pode estocar.
func pacote_liberado(item: String) -> bool:
	if item == "pacote_pesquisa":
		return true
	if not item in TIPOS_PACOTE.values():
		return false
	for r in Registro.receitas:
		if Registro.receitas[r].get("saidas", {}).has(item) and receita_liberada(r):
			return true
	return false


## Pacotes que a pesquisa ativa gasta por unidade (o laboratório aceita estes).
func tipos_ativa() -> Array:
	return tipos(ativa) if ativa != "" else []


func pacotes_faltando() -> int:
	return unidades(ativa) - feitos if ativa != "" else 0


## Segundos de laboratório por pacote na pesquisa ativa (a melhoria "velocidade_pesquisa" encurta).
func tempo_por_pacote() -> float:
	return float(pesquisas()[ativa].get("tempo", 5)) / (1.0 + bonus("velocidade_pesquisa")) if ativa != "" else 0.0


## Melhorias: soma do campo "bonus" das pesquisas concluídas (ex.: "dano_torre_energia" 0,2 = +20%).
## Quem usa a melhoria pergunta aqui; pesquisa que só libera peça ou receita não tem "bonus".
func bonus(chave: String) -> float:
	var s := 0.0
	for id in concluidas:
		s += float(pesquisas().get(id, {}).get("bonus", {}).get(chave, 0.0))
	for id in niveis:                        # infinitas: bônus × nível
		s += float(pesquisas().get(id, {}).get("bonus", {}).get(chave, 0.0)) * int(niveis[id])
	return s


## Muda sempre que alguma melhoria muda (quem aplica bônus em cache refaz).
func assinatura() -> String:
	return "%s|%s" % [concluidas.keys(), niveis]


## Um pacote consumido. Devolve o id concluído (ou "").
func avancar() -> String:
	if ativa == "":
		return ""
	feitos += 1
	if feitos >= unidades(ativa) and infinita(ativa):     # sobe de nível e segue no próximo (mais caro)
		niveis[ativa] = nivel(ativa) + 1
		feitos = 0
		return ativa
	if feitos >= unidades(ativa):
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


## Modo/opção que depende de pesquisa ("modos" em progressao.json; ex.: "trem_condicao", "drones_logistico").
func modo_liberado(m: String) -> bool:
	if livre:
		return true
	for id in concluidas:
		if m in pesquisas().get(id, {}).get("modos", []):
			return true
	return false


## Camada da visão de recursos que depende de pesquisa ("camadas" em progressao.json; ex.: "poluicao").
func camada_liberada(nome: String) -> bool:
	if livre:
		return true
	for id in concluidas:
		if nome in pesquisas().get(id, {}).get("camadas", []):
			return true
	return false


## Que pesquisa libera esta peça (para a dica "precisa pesquisar …").
func quem_libera(nome: String) -> String:
	for id in pesquisas():
		if nome in pesquisas()[id].get("libera", []):
			return pesquisas()[id].nome
	return ""


func estado() -> Dictionary:
	return {"livre": livre, "concluidas": concluidas.keys(), "ativa": ativa, "feitos": feitos, "niveis": niveis.duplicate()}


func restaurar(d: Dictionary) -> void:
	livre = d.livre
	concluidas.clear()
	for c in d.concluidas:
		concluidas[c] = true
	ativa = d.ativa
	feitos = int(d.feitos)
	niveis.clear()
	for k in d.get("niveis", {}):            # salvos antigos não têm níveis
		niveis[k] = int(d.niveis[k])
