class_name Construtor
extends RefCounted
## O que o jogador faz com a ferramenta de construção, sem desenho nenhum (testável sem janela):
##  - planejar uma peça solta, uma linha arrastada (esteira/cano fazem curva em L sozinhos) ou uma remoção em retângulo;
##  - cada item do plano diz se pode (motivo "") ou por que não — é isso que pinta o fantasma de verde/vermelho;
##  - executar o plano no MapaOcupacao e devolver um Relatório (o que entrou, saiu e foi limpo) para o desenho sincronizar;
##  - desfazer (histórico de relatórios).
##
## Peças "virtuais" do menu: "esteira" e "cano" escolhem sozinhas reta/curva/início/fim pelo caminho e pelos vizinhos.

const FAMILIA_ESTEIRA := ["esteira_reta", "esteira_curva_dir", "esteira_curva_esq", "esteira_inicio", "esteira_fim"]
const FAMILIA_CANO := ["cano_reto", "cano_curva"]
## Peças que se arrastam em linha reta (uma por tile, mesma rotação).
const LINHA_RETA := ["muro_centro", "trilho_reto", "poste_energia"]
const PASSO_POSTE := 6     ## poste arrastado: um a cada N tiles (raio do fio 7,5)
const HISTORICO := 50

var mapa: MapaOcupacao
var _historico: Array[Dictionary] = []
## Progressão (modo "novo"): construir custa itens do núcleo; remover devolve; limpar obstáculo rende material.
## `cobrar` = false no modo livre (demonstração e testes antigos).
var cobrar := false
var inventario: Dictionary = {}
var pesquisa: Pesquisa = null
## Nível em que se constrói esteira (0 = chão, 1 = 0,5 m, 2 = 1,0 m). Rampa ↑ sobe do nível atual; ↓ desce dele.
var nivel := 0


func _init(p_mapa: MapaOcupacao) -> void:
	mapa = p_mapa


# ------------------------------------------------------------------ rotação e fluxo
## Rotação (quartos anti-horários) que faz uma peça "sul → norte" fluir na direção d (0 N, 1 L, 2 S, 3 O).
static func rot_do_fluxo(d: int) -> int:
	return posmod(-d, 4)


static func fluxo_da_rot(r: int) -> int:
	return posmod(-r, 4)


## Direção (0..3) de a para o vizinho b.
static func direcao(a: Vector2i, b: Vector2i) -> int:
	return Grade.DIRECOES.find(b - a)


static func arrastavel(nome: String) -> bool:
	return nome in ["esteira", "cano"] or nome in LINHA_RETA


## Tile do cursor → canto sudoeste da área (o cursor fica no meio da peça).
static func minimo_no_cursor(nome: String, tile: Vector2i, rot: int) -> Vector2i:
	var a := Grade.area_girada(Registro.area(_modelo_base(nome)), rot)
	return tile - Vector2i((a.x - 1) / 2, (a.y - 1) / 2)


static func _modelo_base(nome: String) -> String:
	match nome:
		"esteira": return "esteira_reta"
		"cano": return "cano_reto"
	return nome


# ------------------------------------------------------------------ caminhos
## Caminho em L de a até b, sem repetir tile. O primeiro trecho segue o eixo de maior distância.
static func caminho_l(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var out: Array[Vector2i] = [a]
	var d := b - a
	var passos: Array[Vector2i] = []
	var px := Vector2i(signi(d.x), 0)
	var py := Vector2i(0, signi(d.y))
	if absi(d.x) >= absi(d.y):
		for i in absi(d.x): passos.append(px)
		for i in absi(d.y): passos.append(py)
	else:
		for i in absi(d.y): passos.append(py)
		for i in absi(d.x): passos.append(px)
	var t := a
	for p in passos:
		t += p
		out.append(t)
	return out


## Linha reta de a no eixo dominante até a projeção de b.
static func caminho_reto(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var d := b - a
	var fim := Vector2i(b.x, a.y) if absi(d.x) >= absi(d.y) else Vector2i(a.x, b.y)
	return caminho_l(a, fim)


# ------------------------------------------------------------------ planos
## Item de plano: {nome, minimo, rot, motivo ("" = pode), acao ("colocar" | "substituir" | "igual"), id_antigo}.
func plano_peca(nome: String, tile: Vector2i, rot: int) -> Array[Dictionary]:
	return _cobrar_plano(_plano_peca(nome, tile, rot), nome)


func _plano_peca(nome: String, tile: Vector2i, rot: int) -> Array[Dictionary]:
	if nome == "esteira_rampa" or nome == "rampa_desce":
		return [_item_rampa(nome == "rampa_desce", tile, rot)]
	if nome == "trem":
		return [_item_trem(tile)]
	if nome in ["esteira", "cano"]:
		return _plano_linha(nome, tile, tile, rot)
	var minimo := minimo_no_cursor(nome, tile, rot)
	return [_item(nome, minimo, rot)]


## Arrasto de a até b. `rot` só vale quando a == b (sem direção de arrasto).
func plano_linha(nome: String, a: Vector2i, b: Vector2i, rot: int) -> Array[Dictionary]:
	return _cobrar_plano(_plano_linha(nome, a, b, rot), nome)


func _plano_linha(nome: String, a: Vector2i, b: Vector2i, rot: int) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	if nome == "esteira" or nome == "cano":
		var cam := caminho_l(a, b)
		var dirs := _direcoes(cam, fluxo_da_rot(rot))
		for i in cam.size():
			var d_in: int = dirs[i - 1] if i > 0 else dirs[0]
			var d_out: int = dirs[i]
			var p := _peca_esteira(cam, dirs, i, nivel) if nome == "esteira" else _peca_cano(d_in, d_out)
			out.append(_item_trocavel(p.nome, cam[i], p.rot, nivel if nome == "esteira" else 0))
		if nome == "esteira" and nivel > 0:
			_planejar_pilares(out, cam, dirs)
		return out
	if not nome in LINHA_RETA or a == b:
		return _plano_peca(nome, a, rot)
	var cam := caminho_reto(a, b)
	var d := direcao(cam[0], cam[1])
	var r := rot_do_fluxo(d) if nome == "trilho_reto" else rot
	for i in cam.size():
		if nome == "poste_energia" and i % PASSO_POSTE != 0 and i != cam.size() - 1:
			continue
		out.append(_item(nome, cam[i], r))
	return out


## Remoção em retângulo: estruturas inteiras que encostam no retângulo + obstáculos naturais.
## Itens: {acao: "remover", id, nome, minimo, rot} ou {acao: "limpar", tile, nome, minimo, rot}.
func plano_remocao(a: Vector2i, b: Vector2i) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var vistos := {}
	for x in range(mini(a.x, b.x), maxi(a.x, b.x) + 1):
		for y in range(mini(a.y, b.y), maxi(a.y, b.y) + 1):
			var t := Vector2i(x, y)
			for id in mapa.ids_no_tile(t):
				if not vistos.has(id):
					vistos[id] = true
					var e: Dictionary = mapa.estruturas[id]
					var motivo := "inimigo" if e.nome == "ninho_aranha" else ""      # ninho só cai na bala
					if e.nome == "nucleo":
						motivo = "nucleo"
					out.append({"acao": "remover", "id": id, "nome": e.nome, "minimo": e.minimo, "rot": e.rot, "motivo": motivo,
							"nivel": e.get("nivel", 0), "desce": e.get("desce", false)})
			if mapa.tiles.has(t):
				continue
			if mapa.limpos.has(t):
				continue
			var o := mapa.gerador.distribuicao.obstaculo(t)
			if not o.is_empty() and not vistos.has(o.ancora):
				vistos[o.ancora] = true
				out.append({"acao": "limpar", "tile": t, "nome": o.nome, "minimo": o.ancora, "rot": o.rot, "motivo": ""})
	return out


# ------------------------------------------------------------------ custos
## Chave de custo: as peças de esteira/cano escolhidas sozinhas custam como "esteira"/"cano".
static func chave_custo(nome: String) -> String:
	if nome == "rampa_desce": return "esteira_rampa"
	if nome in FAMILIA_ESTEIRA: return "esteira"
	if nome in FAMILIA_CANO: return "cano"
	return nome


static func custo_de(nome: String) -> Dictionary:
	return Registro.progressao.get("custos", {}).get(chave_custo(nome), {})


## Marca "bloqueado" (falta pesquisa) e "sem_recursos" (o estoque acaba no meio do traço: o que cabe fica verde).
func _cobrar_plano(plano: Array[Dictionary], escolhido: String) -> Array[Dictionary]:
	if not cobrar:
		return plano
	if pesquisa != null and not pesquisa.peca_liberada(escolhido):
		for it in plano:
			it.motivo = "bloqueado"
		return plano
	var gasto := {}
	for it in plano:
		if it.motivo != "" or not it.get("acao", "colocar") in ["colocar", "trem"]:
			continue
		var c := custo_de(it.nome)
		var cabe := true
		for k in c:
			if int(gasto.get(k, 0)) + int(c[k]) > int(inventario.get(k, 0)):
				cabe = false
		if not cabe:
			it.motivo = "sem_recursos"
			continue
		for k in c:
			gasto[k] = int(gasto.get(k, 0)) + int(c[k])
	return plano


## Soma (ou tira, com sinal −1) itens no estoque e anota no relatório (para o desfazer devolver).
func _mexer_estoque(itens: Dictionary, sinal: int, rel: Dictionary) -> void:
	if not cobrar:
		return
	for k in itens:
		var n := int(itens[k]) * sinal
		inventario[k] = maxi(0, int(inventario.get(k, 0)) + n)
		rel.estoque[k] = int(rel.estoque.get(k, 0)) + n


## Devolve o custo de algo que o mundo não conseguiu pôr (trem sem espaço).
func devolver(nome: String) -> void:
	_mexer_estoque(custo_de(nome), 1, _relatorio_vazio())


static func pode_tudo(plano: Array[Dictionary]) -> bool:
	for it in plano:
		if it.motivo != "":
			return false
	return true


## Quantos itens do plano fazem alguma coisa (para o texto da interface).
static func contar(plano: Array[Dictionary]) -> Dictionary:
	var ok := 0
	var bloq := 0
	for it in plano:
		if it.get("acao", "") == "igual":
			continue
		if it.motivo == "": ok += 1
		else: bloq += 1
	return {"ok": ok, "bloqueados": bloq}


# ------------------------------------------------------------------ executar / desfazer
## Executa o que pode do plano (itens bloqueados são pulados). Relatório:
## {colocados: [id], removidos: [{id, nome, minimo, rot}], limpos: [{tile, area_tiles}]}.
func executar(plano: Array[Dictionary]) -> Dictionary:
	var rel := _relatorio_vazio()
	for it in plano:
		if it.motivo != "":
			continue
		match it.get("acao", "colocar"):
			"igual":
				pass
			"trem":
				rel.trens.append({"tile": it.minimo, "rot": it.rot})      # o mundo põe o trem na malha
				_mexer_estoque(custo_de("trem"), -1, rel)
			"limpar":
				var o := mapa.limpar_obstaculo(it.tile)
				if not o.is_empty():
					rel.limpos.append({"tile": it.tile, "tiles": Grade.tiles_da_area(o.ancora, o.area, 0)})
					_mexer_estoque(Registro.progressao.get("drops", {}).get(o.nome, {}), 1, rel)
			"remover":
				if mapa.estruturas.has(it.id):
					_mexer_estoque(custo_de(mapa.estruturas[it.id].nome), 1, rel)
				_remover(it.id, rel)
			"substituir":
				_remover(it.id_antigo, rel)
				_colocar(it, rel)
			_:
				if _colocar(it, rel):
					_mexer_estoque(custo_de(it.nome), -1, rel)
	_recalcular_pontas(rel)
	if not _relatorio_vazio_de_fato(rel) or not rel.estoque.is_empty():
		_historico.append(rel)
		if _historico.size() > HISTORICO:
			_historico.pop_front()
	return rel


## Estrutura destruída (aranha): sai do mapa e as pontas de esteira em volta se ajustam. Não entra no desfazer.
func destruir(id: int) -> Dictionary:
	var rel := _relatorio_vazio()
	_remover(id, rel)
	_recalcular_pontas(rel)
	return rel


func pode_desfazer() -> bool:
	return not _historico.is_empty()


## Desfaz a última execução. Devolve o relatório do que mudou agora (mesmo formato).
func desfazer() -> Dictionary:
	var rel := _relatorio_vazio()
	if _historico.is_empty():
		return rel
	var h: Dictionary = _historico.pop_back()
	for id in h.colocados:
		_remover(id, rel)
	for i in range(h.removidos.size() - 1, -1, -1):
		var e: Dictionary = h.removidos[i]
		if e.nome == "pilar":
			continue                        # volta junto com a esteira dona dele
		var it := {"nome": e.nome, "minimo": e.minimo, "rot": e.rot}
		it.merge(e.get("extras", {}))
		_colocar(it, rel)
	for l in h.limpos:
		for t in l.tiles:
			mapa.limpos.erase(t)
		rel.restaurados.append(l)
	_mexer_estoque(h.estoque, -1, rel)
	return rel


func _relatorio_vazio() -> Dictionary:
	return {"colocados": [] as Array[int], "removidos": [] as Array[Dictionary], "limpos": [] as Array[Dictionary],
			"restaurados": [] as Array[Dictionary], "trens": [] as Array[Dictionary], "estoque": {}}


func _relatorio_vazio_de_fato(r: Dictionary) -> bool:
	return r.colocados.is_empty() and r.removidos.is_empty() and r.limpos.is_empty()


func _colocar(it: Dictionary, rel: Dictionary) -> bool:
	var extras := {}
	if it.get("nivel", 0) > 0: extras["nivel"] = it.nivel
	if it.get("desce", false): extras["desce"] = true
	if not it.get("pilares", []).is_empty(): extras["pilares"] = it.pilares
	var id := mapa.colocar(it.nome, it.minimo, it.rot, extras)
	if id < 0:
		return false
	rel.colocados.append(id)
	for p in it.get("pilares", []):
		var pid := mapa.reservar_pilar(p[0], p[1])
		if pid >= 0:
			rel.colocados.append(pid)
	return true


func _remover(id: int, rel: Dictionary) -> void:
	if not mapa.estruturas.has(id):
		return
	var e: Dictionary = mapa.estruturas[id]
	rel.removidos.append(_registro(id))
	rel.colocados.erase(id)
	# os pilares desta esteira elevada saem junto (voltam com ela no desfazer)
	for p in e.get("pilares", []):
		var pid: int = mapa.cantos.get(p[0], -1)
		if pid >= 0 and mapa.estruturas[pid].nome == "pilar":
			rel.removidos.append(_registro(pid))
			rel.colocados.erase(pid)
			mapa.remover(pid)
	mapa.remover(id)


func _registro(id: int) -> Dictionary:
	var e: Dictionary = mapa.estruturas[id]
	var extras := {}
	for k in ["nivel", "desce", "pilares"]:
		if e.has(k):
			extras[k] = e[k]
	return {"id": id, "nome": e.nome, "minimo": e.minimo, "rot": e.rot, "extras": extras}


## Troca a peça no lugar (mesmo id, mesmo nível e pilares) — pontas automáticas.
func _trocar_nome(id: int, novo: String, rel: Dictionary) -> void:
	if rel.colocados.has(id):
		mapa.estruturas[id].nome = novo      # posta agora mesmo: só acerta a peça
		return
	rel.removidos.append(_registro(id))
	mapa.estruturas[id].nome = novo
	rel.colocados.append(id)


## Pontas automáticas: em volta de tudo que entrou ou saiu, cada esteira reta/início/fim vira a peça certa —
## "início" se ninguém a alimenta por trás, "fim" se nada recebe na frente, "reta" se as duas pontas estão ligadas.
## (Continuar um traço a partir de um fim o transforma em reta; remover um pedaço fecha a ponta que sobrou.)
func _recalcular_pontas(rel: Dictionary) -> void:
	var tiles := {}
	var areas: Array[Dictionary] = []
	for id in rel.colocados:
		if mapa.estruturas.has(id):
			areas.append(mapa.estruturas[id])
	areas.append_array(rel.removidos)
	for e in areas:
		for t in Grade.tiles_da_area(e.minimo, Registro.area(e.nome), e.rot):
			tiles[t] = true
			for d in Grade.DIRECOES:
				tiles[t + d] = true
	for t in tiles:
		for id in mapa.ids_no_tile(t):
			var e: Dictionary = mapa.estruturas[id]
			if not e.nome in ["esteira_reta", "esteira_inicio", "esteira_fim"]:
				continue
			var d := fluxo_da_rot(e.rot)
			var n: int = e.get("nivel", 0)
			var alimentado := _alimenta(t, d, n)
			var escoa := _recebe(t, d, n)
			var certo: String = e.nome
			if alimentado and escoa: certo = "esteira_reta"
			elif alimentado: certo = "esteira_fim"
			elif escoa: certo = "esteira_inicio"
			if certo != e.nome:
				_trocar_nome(id, certo, rel)


# ------------------------------------------------------------------ escolha das peças
## Direção de fluxo de cada tile do caminho (o último repete o anterior; caminho de 1 tile usa `padrao`).
static func _direcoes(cam: Array[Vector2i], padrao: int) -> Array[int]:
	var out: Array[int] = []
	for i in cam.size():
		if i + 1 < cam.size():
			out.append(direcao(cam[i], cam[i + 1]))
		elif i > 0:
			out.append(out[i - 1])
		else:
			out.append(padrao)
	return out


func _peca_esteira(cam: Array[Vector2i], dirs: Array[int], i: int, n := 0) -> Dictionary:
	var d_out: int = dirs[i]
	var d_in: int = dirs[i - 1] if i > 0 else d_out
	var r := rot_do_fluxo(d_in)
	if d_out == posmod(d_in + 1, 4):
		return {"nome": "esteira_curva_dir", "rot": r}
	if d_out == posmod(d_in - 1, 4):
		return {"nome": "esteira_curva_esq", "rot": r}
	var primeiro := i == 0
	var ultimo := i == cam.size() - 1
	var alimentado := not primeiro or _alimenta(cam[i], d_in, n)
	var escoa := not ultimo or _recebe(cam[i], d_out, n)
	if not alimentado and escoa:
		return {"nome": "esteira_inicio", "rot": r}
	if alimentado and not escoa:
		return {"nome": "esteira_fim", "rot": r}
	if not alimentado and not escoa and cam.size() > 1:
		return {"nome": "esteira_inicio", "rot": r}
	return {"nome": "esteira_reta", "rot": r}


## Cano: reto na mesma direção; curva liga o lado de trás (oposto a d_in) ao lado de saída.
static func _peca_cano(d_in: int, d_out: int) -> Dictionary:
	if d_in == d_out:
		return {"nome": "cano_reto", "rot": rot_do_fluxo(d_in)}
	var lados := [posmod(d_in + 2, 4), d_out]
	for r in 4:
		# cano_curva em r = 0 liga S (2) e L (1); girar r anti-horário leva o lado s em s − r
		var l := [posmod(2 - r, 4), posmod(1 - r, 4)]
		if l.has(lados[0]) and l.has(lados[1]):
			return {"nome": "cano_curva", "rot": r}
	return {"nome": "cano_reto", "rot": rot_do_fluxo(d_out)}


## Nó de esteira de uma estrutura (reta, curva, início, fim, rampa): direções e níveis de entrada/saída.
## {} se não é esteira. Rampa guarda o nível de baixo; sobe (entra em n, sai em n+1) ou desce (o contrário).
static func no_esteira(e: Dictionary) -> Dictionary:
	var nome: String = e.nome
	if not (nome in FAMILIA_ESTEIRA or nome == "esteira_rampa"):
		return {}
	var d := fluxo_da_rot(e.rot)
	var s := d
	match nome:
		"esteira_curva_dir": s = posmod(d + 1, 4)
		"esteira_curva_esq": s = posmod(d - 1, 4)
		"esteira_fim": s = -1
	var n: int = e.get("nivel", 0)
	var n_in := n
	var n_out := n
	if nome == "esteira_rampa":
		if e.get("desce", false): n_in = n + 1
		else: n_out = n + 1
	return {"entra": d, "sai": s, "n_in": n_in, "n_out": n_out}


## Alguma coisa entrega itens neste tile (no nível n) vindo de trás (fluxo d)? Esteira/rampa ou porta de máquina.
func _alimenta(tile: Vector2i, d: int, n := 0) -> bool:
	var t_atras := tile - Grade.DIRECOES[d]
	for id in mapa.ids_no_tile(t_atras):
		var e: Dictionary = mapa.estruturas[id]
		var no := no_esteira(e)
		if no.is_empty() or no.n_out != n:
			continue
		if no.sai == d or (e.nome == "esteira_fim" and no.entra == d):
			return true                           # fim apontando para cá vira reta no recálculo
	if n > 0:
		return false
	var atras := _estrutura_em(t_atras)
	if atras.is_empty() or atras.nome.begins_with("braco") or not no_esteira(atras).is_empty():
		return false
	for p in _portas(atras):
		if p.io == "SAI" and p.tipo == "ITEM" and p.tile_fora == tile and p.dir == Grade.DIRECOES[d]:
			return true
	return false


## O tile da frente recebe itens no nível n? Esteira (que não venha de frente) ou porta de entrada de máquina.
## Braço não conta: a esteira termina em "fim" (para-choque) para o braço pegar.
func _recebe(tile: Vector2i, d: int, n := 0) -> bool:
	var t_frente := tile + Grade.DIRECOES[d]
	for id in mapa.ids_no_tile(t_frente):
		var no := no_esteira(mapa.estruturas[id])
		if not no.is_empty() and no.n_in == n and no.entra != posmod(d + 2, 4):
			return true
	if n > 0:
		return false
	var frente := _estrutura_em(t_frente)
	if frente.is_empty() or frente.nome.begins_with("braco") or not no_esteira(frente).is_empty():
		return false
	for p in _portas(frente):
		if p.io == "ENT" and p.tipo == "ITEM" and p.tile_fora == tile and p.dir == -Grade.DIRECOES[d]:
			return true
	return false


## Estrutura no tile, no chão (n = 0) ou num nível de cima.
func _estrutura_em(t: Vector2i, n := 0) -> Dictionary:
	var id: int = mapa.tiles.get(t, -1) if n == 0 else mapa.altos.get(Vector3i(t.x, t.y, n), -1)
	if id < 0:
		return {}
	var e: Dictionary = mapa.estruturas[id].duplicate()
	e["id"] = id
	return e


## Pilares do traço elevado (EsteiraElevada): cada pilar fica com o tile cujo canto de entrada ele usa.
func _planejar_pilares(itens: Array[Dictionary], cam: Array[Vector2i], dirs: Array[int]) -> void:
	var entradas: Array[int] = []
	var niveis: Array[float] = []
	for i in cam.size():
		entradas.append(dirs[i - 1] if i > 0 else dirs[0])
		niveis.append(nivel * 0.5)
	var plano := EsteiraElevada.planejar(mapa, cam, entradas, niveis)
	if not plano.ok:
		for it in itens:
			if it.minimo == plano.tile and it.motivo == "":
				it.motivo = plano.erro
		return
	for p in plano.pilares:
		for k in cam.size():
			if p.canto in EsteiraElevada.cantos_de_entrada(cam[k], entradas[k]) and itens[k].acao != "igual":
				if not itens[k].has("pilares"):
					itens[k]["pilares"] = []
				itens[k].pilares.append([p.canto, p.altura])
				break


## Rampa: ↑ sobe do nível atual para o próximo; ↓ desce do nível atual. Rampa no alto também precisa de pilar.
func _item_rampa(desce: bool, tile: Vector2i, rot: int) -> Dictionary:
	var baixo := nivel - 1 if desce else nivel
	var it := {"nome": "esteira_rampa", "minimo": tile, "rot": rot, "acao": "colocar", "id_antigo": -1,
			"nivel": baixo, "desce": desce, "motivo": ""}
	if baixo < 0:
		it.motivo = "nivel_chao"
	elif baixo + 1 > MapaOcupacao.NIVEIS:
		it.motivo = "nivel_maximo"
	elif baixo == 0:
		it.motivo = mapa.motivo_bloqueio("esteira_rampa", tile, rot)
	else:
		it.motivo = mapa.motivo_alto(tile, baixo)
		if it.motivo == "":
			var d := fluxo_da_rot(rot)
			var pl := EsteiraElevada.planejar(mapa, [tile] as Array[Vector2i], [d] as Array[int], [baixo * 0.5 + 0.5] as Array[float])
			if not pl.ok:
				it.motivo = pl.erro
			else:
				it["pilares"] = pl.pilares.map(func(p): return [p.canto, p.altura])
	return it


func _portas(e: Dictionary) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for p in Registro.modelos.get(e.nome, {}).get("portas", []):
		out.append(Grade.porta_no_mundo(p, e.minimo, e.area, e.rot))
	return out


## Trem: vai em cima de um trilho reto já construído (fica na direção do trilho).
func _item_trem(tile: Vector2i) -> Dictionary:
	var e := _estrutura_em(tile)
	var ok: bool = not e.is_empty() and e.nome == "trilho_reto"
	return {"nome": "trem", "minimo": tile, "rot": e.rot if ok else 0, "motivo": "" if ok else "sem_trilho",
			"acao": "trem", "id_antigo": -1}


func _item(nome: String, minimo: Vector2i, rot: int, n := 0) -> Dictionary:
	if n > 0:
		return {"nome": nome, "minimo": minimo, "rot": rot, "motivo": mapa.motivo_alto(minimo, n), "acao": "colocar",
				"id_antigo": -1, "nivel": n}
	return {"nome": nome, "minimo": minimo, "rot": rot, "motivo": mapa.motivo_bloqueio(nome, minimo, rot),
			"acao": "colocar", "id_antigo": -1}


## Em cima de esteira/cano já existente da mesma família: troca a peça (ou nada, se for igual).
func _item_trocavel(nome: String, tile: Vector2i, rot: int, n := 0) -> Dictionary:
	var atual := _estrutura_em(tile, n)
	var familia := FAMILIA_ESTEIRA if nome in FAMILIA_ESTEIRA else FAMILIA_CANO
	if not atual.is_empty() and atual.nome in familia:
		var acao := "igual" if atual.nome == nome and atual.rot == rot else "substituir"
		var it := {"nome": nome, "minimo": tile, "rot": rot, "motivo": "", "acao": acao, "id_antigo": atual.id, "nivel": n}
		if atual.has("pilares"):
			it["pilares"] = atual.pilares            # troca mantém os pilares que já estão lá
		return it
	return _item(nome, tile, rot, n)
