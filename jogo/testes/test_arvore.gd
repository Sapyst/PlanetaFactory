extends Caso
## Árvore de tecnologia completa (dados/arvore.json, gerada de docs/ARVORE_TECNOLOGIA.mmd) e sua ligação com as
## pesquisas jogáveis (progressao.json).


func test_estrutura() -> void:
	var p := Pesquisa.new()
	var nos := p.arvore()
	igual(nos.size(), 166, "166 tecnologias")
	igual(p.eras().size(), 3, "três eras")
	var eras := {}
	for e in p.eras():
		eras[e.id] = 0
	for id in nos:
		var n: Dictionary = nos[id]
		verificar(eras.has(n.era), "era conhecida: " + id)
		eras[n.era] = eras.get(n.era, 0) + 1
		for r in n.requer:
			verificar(nos.has(r), "pré-requisito existe: %s → %s" % [r, id])
		verificar(n.has("tempo"), "tem custo: " + id)
	igual(eras.base, 35, "era base")
	igual(eras.meio, 60, "era do meio")
	igual(eras.avancada, 71, "era super avançada")
	verificar(nos.foguete_proliferacao.get("objetivo", false), "foguete é o objetivo final")


func test_jogaveis_na_arvore() -> void:
	var p := Pesquisa.new()
	for id in p.pesquisas():
		verificar(p.arvore().has(id), "pesquisa jogável está na árvore: " + id)
		verificar(p.jogavel(id), "jogável: " + id)
		var a: Array = (p.pesquisas()[id].get("requer", []) as Array).duplicate()
		var b: Array = (p.arvore()[id].requer as Array).duplicate()
		a.sort()
		b.sort()
		igual(a, b, "mesmos pré-requisitos no jogo e na árvore: " + id)
		verificar(p.arvore()[id].get("existente", false), "marcada como existente: " + id)
	verificar(not p.jogavel("escavar_canal"), "escavação de canal ainda é em breve")
	p.concluidas = {"fluidos": true, "automacao": true, "bomba_agua": true}
	verificar(not p.disponivel("escavar_canal"), "em breve não se pesquisa")


func test_sem_ciclos() -> void:
	var p := Pesquisa.new()
	var nos := p.arvore()
	var feito := {}
	var faltam: Array = nos.keys()
	var voltas := 0
	while not faltam.is_empty() and voltas < 400:
		voltas += 1
		var resto: Array = []
		for id in faltam:
			var ok := true
			for r in nos[id].requer:
				if not feito.has(r):
					ok = false
			if ok:
				feito[id] = true
			else:
				resto.append(id)
		faltam = resto
	verificar(faltam.is_empty(), "todos alcançáveis, sem ciclo")


## Toda chave de "bonus" em progressao.json tem quem a use no jogo (senão a pesquisa não faria nada).
const BONUS_USADOS := ["dano_torre_energia", "dano_bala", "velocidade_pesquisa", "produtividade_mineracao",
		"cadencia_torre_energia", "economia_tiro_torre", "cadencia_bala"]


func test_melhorias() -> void:
	var p := Pesquisa.new()
	for id in p.pesquisas():
		for k in p.pesquisas()[id].get("bonus", {}):
			verificar(k in BONUS_USADOS, "bônus %s de %s é lido por algum sistema" % [k, id])
		if not p.pesquisas()[id].get("bonus", {}).is_empty():
			igual(p.arvore()[id].tipo, "infinita" if p.infinita(id) else "melhoria", "pesquisa com bônus é melhoria na árvore: " + id)
	perto(p.bonus("dano_torre_energia"), 0.0, 1e-6, "sem pesquisa, sem bônus")
	p.concluidas = {"defesa": true, "dano_energia_1": true}
	perto(p.bonus("dano_torre_energia"), 0.2, 1e-6, "dano 1: +20%")
	p.ativa = "logistica"
	var base := float(p.pesquisas().logistica.tempo)
	perto(p.tempo_por_pacote(), base, 1e-6, "sem melhoria de laboratório, tempo normal")
