class_name Bloqueios
## Por que uma peça do plano não pode ser posta, em palavras curtas e tile a tile (o fantasma realça esses tiles): "rocha",
## "árvore", "ocupado: Baú", "água", "sem pesquisa", "falta material"... Lê o motivo que o Construtor/MapaOcupacao já deu;
## aqui só se traduz e se descobre QUAIS tiles atrapalham. Motivo que não é de um tile (pesquisa, material, jazida): a pegada inteira.

const CURTOS := {
	"agua": "água", "desnivel": "desnível", "sem_jazida": "sem jazida", "sem_terraplenagem": "sem terraplenagem", "pilar_no_canto": "pilar no canto",
	"inimigo": "ninho", "nucleo": "núcleo", "sem_recursos": "falta material", "bloqueado": "sem pesquisa", "sem_pesquisa_canal": "sem pesquisa",
	"esteira_em_cima": "esteira em cima", "estrutura_alta_embaixo": "algo alto embaixo", "sem_apoio": "sem apoio", "nivel_fora_do_degrau": "nível inválido",
	"nivel_chao": "já no chão", "nivel_maximo": "nível máximo", "longe_da_agua": "longe da água", "sem_trilho": "sem trilho", "tomada_seca": "tomada seca",
	"fora_do_rio": "fora do rio", "em_desenvolvimento": "em desenvolvimento", "estrutura desconhecida": "peça desconhecida", "obstaculo": "obstáculo", "ocupado": "ocupado"}


## Motivo curto de um elemento natural pelo nome do modelo.
static func nome_obstaculo(nome: String) -> String:
	if nome.begins_with("arv_"):
		return "árvore"
	for par in [["rocha", "rocha"], ["pedregulho", "rocha"], ["montanha", "rocha"], ["seixos", "rocha"], ["arbusto", "arbusto"], ["cogumelo", "cogumelo"], ["cacto", "cacto"]]:
		if nome.contains(par[0]):
			return par[1]
	return "obstáculo"


## Nome da estrutura como o jogador lê: o rótulo do menu; variante (esteira_curva...) cai no rótulo da família.
static func nome_peca(nome: String) -> String:
	var rot: Dictionary = Registro.menu.get("rotulos", {})
	if rot.has(nome):
		return rot[nome]
	var i := nome.rfind("_")
	while i > 0:
		var base := nome.substr(0, i)
		if rot.has(base):
			return rot[base]
		i = base.rfind("_")
	return nome.replace("_", " ").capitalize()


## Quem atrapalha o item: [{tile, texto}]. Vazio se o item pode.
static func do_item(mapa: MapaOcupacao, it: Dictionary) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var motivo: String = it.get("motivo", "")
	if motivo == "":
		return out
	var tiles: Array[Vector2i] = []
	if it.get("acao", "") == "aplainar" or it.has("tile"):
		tiles.append(it.tile)
	else:
		tiles = Grade.tiles_da_area(it.minimo, Registro.area(it.nome), it.rot)
	var ger := mapa.gerador
	var nivel0 := ger.nivel(tiles[0])
	for t in tiles:
		match motivo:
			"ocupado", "inimigo", "nucleo":
				for id in mapa.ids_no_tile(t):
					var nome: String = mapa.estruturas[id].nome
					out.append({"tile": t, "texto": "ocupado: " + nome_peca(nome) if motivo == "ocupado" else CURTOS[motivo]})
					break
			"obstaculo":
				if not mapa.limpos.has(t):
					var o := ger.distribuicao.obstaculo(t)
					if not o.is_empty():
						out.append({"tile": t, "texto": nome_obstaculo(String(o.nome))})
			"agua":
				if ger.eh_agua(ger.terreno(t)):
					out.append({"tile": t, "texto": CURTOS.agua})
			"desnivel":
				if ger.nivel(t) != nivel0:
					out.append({"tile": t, "texto": CURTOS.desnivel})
			_:
				out.append({"tile": t, "texto": CURTOS.get(motivo, motivo)})
	if out.is_empty():                                # o motivo veio de outra regra (traço, nível): a pegada inteira
		for t in tiles:
			out.append({"tile": t, "texto": CURTOS.get(motivo, motivo)})
	return out


## O plano inteiro, por motivo: [{texto, tiles}], na ordem em que aparecem; cada tile só uma vez.
static func resumo(mapa: MapaOcupacao, plano: Array[Dictionary]) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var por_texto := {}
	var vistos := {}
	for it in plano:
		for b in do_item(mapa, it):
			if vistos.has(b.tile):
				continue
			vistos[b.tile] = true
			if not por_texto.has(b.texto):
				por_texto[b.texto] = {"texto": b.texto, "tiles": [] as Array[Vector2i]}
				out.append(por_texto[b.texto])
			por_texto[b.texto].tiles.append(b.tile)
	return out
