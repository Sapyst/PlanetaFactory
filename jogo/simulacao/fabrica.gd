class_name Fabrica
extends RefCounted
## Simula o que está construído no mapa (lógica pura, testável): esteiras, braços, máquinas, baús, energia,
## combustível, torres e estações. É remontada do MapaOcupacao sempre que algo entra ou sai
## (`reconstruir`), guardando o estado de quem continua: itens nas esteiras (pelo tile), conteúdo de máquinas,
## baús, combustível, braço segurando item.
##
##  esteiras  tiles ligados de trás para a frente viram UMA EsteiraCaminho; ponta que dá na lateral de outra esteira
##            entra nela no meio (carga lateral); ponta que dá numa porta de entrada entrega à máquina.
##  portas    saída de máquina/estação empurra itens para a esteira do tile em frente à porta.
##  braços    pegam do tile de trás e soltam no da frente (esteira, máquina, baú, torre, gerador, estação);
##            só pegam item que o destino aceita. Consomem energia.
##  máquinas  extrator/broca mineram a jazida embaixo; fornalha escolhe a receita pelo minério que chega e queima
##            carvão/biomassa; montadora e refinador usam a receita escolhida pelo jogador. Elétricas dependem
##            dos fios (Fiacao + RedeEnergia); gerador queima combustível que braço/esteira põe nele.
##  poluição  quem trabalhou neste tick fica em `emissao` (id → pontos), e o mundo joga na Poluicao.

const FOGO_KW := 90.0            ## consumo da fornalha a combustão
const ESTOQUE_FOGO_MJ := 8.0     ## aceita combustível até ter isso guardado
const ESTOQUE_GERADOR_MJ := 40.0
const TIROS_POR_MUNICAO := 10
const BAU_MAX := 1600
## Modo de trabalho (opção interna de máquina elétrica): [velocidade, energia, poluição].
const MODOS := {"eco": [0.5, 0.4, 0.6], "normal": [1.0, 1.0, 1.0], "turbo": [1.5, 2.0, 1.6]}

var mapa: MapaOcupacao
var rede := RedeEnergia.new()
var caminhos: Array[Dictionary] = []   ## {esteira: EsteiraCaminho, tiles: Array[Vector2i], entra: Array[int], sai: Array[int]}
var maquinas: Dictionary = {}          ## id → Maquina
var bracos: Dictionary = {}            ## id → Braco
var baus: Dictionary = {}              ## id → {item: n}
var combustivel: Dictionary = {}       ## id (fornalha/gerador) → MJ guardado
var estoques: Dictionary = {}          ## id da estação → {enviar, recebido} (o mundo passa o mesmo dicionário dos trens)
var torre_receber: Callable            ## func(id, tiros) — a colônia guarda a munição das torres
var emissao: Dictionary = {}           ## id → pontos de poluição emitidos no último tick
var estoque_nucleo: Dictionary = {}    ## o mesmo dicionário do inventário do Construtor (tudo que entra no núcleo)
var pesquisa: Pesquisa = null
var laboratorios: Dictionary = {}      ## id → {pacotes, t, energia}
var concluidas: Array[String] = []     ## pesquisas terminadas no último tick (o mundo avisa)
var passos := 0                        ## quantos ticks já rodaram (o desenho só refaz quando muda)
var redes_fluido: Array[Dictionary] = []    ## {fluido, qtd, cap, membros: Array[int]}
var _rede_do: Dictionary = {}          ## id (cano/tanque) → índice da rede
var _ligacoes_fluido: Array[Dictionary] = []  ## {id (máquina), io, rede}
var distribuidores: Dictionary = {}    ## id (divisor/junção) → {buffer: Array[String], vez: int}
var _saidas_dist: Dictionary = {}      ## id → Array[{caminho, idx}]
var _no_tile: Dictionary = {}          ## tile → [caminho, índice do tile no caminho] (só esteira no chão)
var _no_nivel: Dictionary = {}         ## Vector3i(x, y, nível de entrada) → [caminho, índice]
var _saidas_portas: Array[Dictionary] = []   ## {origem: Object, tile: Vector2i}
var _membros: Dictionary = {}          ## id → membro da rede (dict)
var acumulado: Dictionary = {}         ## id do acumulador → MJ guardados
var sol := 1.0                         ## 0..1: quanto os painéis solares rendem agora (o mundo passa do clima)
var vento := 0.5                       ## força do vento (0..~1,6) para turbina sem valor próprio
var vento_turbina: Dictionary = {}     ## id da turbina → vento no lugar dela (clima × VentoLocal × rajada), o mundo passa
var juncoes: Array[Dictionary] = []    ## itens que acabaram de entrar pela lateral: {caminho, pos, lado, passo} (desenho desliza)

const EXTRA_JUNCAO := 0.375            ## m além da borda na rampa de junção (o item para a 0,25 m do eixo da vizinha)


func _init(p_mapa: MapaOcupacao) -> void:
	mapa = p_mapa


# ------------------------------------------------------------------ montar
func reconstruir() -> void:
	var guardados := _guardar_itens()
	var fluido_salvo := _guardar_fluidos()
	caminhos.clear()
	_no_tile.clear()
	_no_nivel.clear()
	_saidas_portas.clear()
	_membros.clear()
	juncoes.clear()
	rede = RedeEnergia.new()
	var vivos := {}
	for id in mapa.estruturas:
		vivos[id] = true
	for d in [maquinas, bracos, baus, combustivel, laboratorios, distribuidores, acumulado]:
		for id in d.keys():
			if not vivos.has(id):
				d.erase(id)
	_montar_esteiras()
	_montar_maquinas()
	_montar_energia()
	_ligar_pontas()
	_montar_portas()
	_montar_bracos()
	_montar_fluidos()
	_restaurar_fluidos(fluido_salvo)
	_restaurar_itens(guardados)


## Nós de esteira chaveados por (tile, nível de entrada): esteira elevada e rampa (sobe/desce) entram na mesma
## conta — um caminho pode subir e descer. `_no_tile` (braços, portas) só vê o que está no chão.
func _montar_esteiras() -> void:
	var cinta := {}       # Vector3i(x, y, n_entrada) → {tile, entra, sai, n_in, n_out, chao}
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		var no := Construtor.no_esteira(e)
		if no.is_empty():
			continue
		no["tile"] = e.minimo
		no["nome"] = e.nome
		no["chao"] = e.get("nivel", 0) == 0
		cinta[Vector3i(e.minimo.x, e.minimo.y, no.n_in)] = no
	var proximo := func(k: Vector3i) -> Vector3i:
		var no: Dictionary = cinta[k]
		if no.sai < 0:
			return Vector3i(0, 0, -1)
		if no.get("tunel", "") == "entrada":
			# passagem subterrânea: liga na primeira saída alinhada à frente, até `alcance` tiles
			for i in range(1, int(Registro.estruturas["esteira_tunel_entrada"].get("alcance", 5)) + 1):
				var tt: Vector2i = no.tile + Grade.DIRECOES[no.sai] * i
				var kk := Vector3i(tt.x, tt.y, no.n_out)
				if cinta.has(kk) and cinta[kk].get("tunel", "") == "saida" and cinta[kk].entra == no.sai:
					return kk
			return Vector3i(0, 0, -1)
		var t: Vector2i = no.tile + Grade.DIRECOES[no.sai]
		var n := Vector3i(t.x, t.y, no.n_out)
		if cinta.has(n) and cinta[n].entra == no.sai and cinta[n].get("tunel", "") != "saida" \
				and mapa.gerador.nivel(t) == mapa.gerador.nivel(no.tile):
			return n
		return Vector3i(0, 0, -1)
	var tem_antes := {}
	for k in cinta:
		var n: Vector3i = proximo.call(k)
		if n.z >= 0:
			tem_antes[n] = true
	var visto := {}
	for passada in 2:                     # primeiro os começos; o que sobrar é volta fechada
		for k0 in cinta:
			if visto.has(k0) or (passada == 0 and tem_antes.has(k0)):
				continue
			var tiles: Array[Vector2i] = []
			var entra: Array[int] = []
			var sai: Array[int] = []
			var niveis: Array[Vector2i] = []
			var chao: Array[bool] = []
			var oculto: Array[bool] = []
			var papel: Array[String] = []          # "entrada"/"saida" nas pontas da passagem subterrânea
			var k: Vector3i = k0
			var fechada := false
			while true:
				visto[k] = true
				var no: Dictionary = cinta[k]
				tiles.append(no.tile)
				entra.append(no.entra)
				sai.append(no.sai)
				niveis.append(Vector2i(no.n_in, no.n_out))
				chao.append(no.chao)
				oculto.append(false)
				papel.append(no.get("tunel", ""))
				var n: Vector3i = proximo.call(k)
				if n.z < 0:
					break
				if no.get("tunel", "") == "entrada":
					# trecho debaixo da terra: tiles de passagem que só contam distância (não aparecem, braço não alcança)
					var dist := absi(n.x - no.tile.x) + absi(n.y - no.tile.y)
					for i in range(1, dist):
						tiles.append(no.tile + Grade.DIRECOES[no.sai] * i)
						entra.append(no.sai)
						sai.append(no.sai)
						niveis.append(Vector2i(no.n_out, no.n_out))
						chao.append(false)
						oculto.append(true)
						papel.append("")
				if visto.has(n):
					fechada = n == k0
					break
				k = n
			# rampa de junção: o caminho segue EXTRA_JUNCAO além da borda, por cima do trilho da vizinha
			var lateral: bool = cinta[k].nome == "esteira_juncao"
			var est := EsteiraCaminho.new(float(tiles.size()) + (EXTRA_JUNCAO if lateral else 0.0),
					float(Registro.estruturas["esteira_reta"].velocidade))
			var caixa := Rect2(Vector2(tiles[0]), Vector2.ONE)
			for t in tiles:
				caixa = caixa.expand(Vector2(t)).expand(Vector2(t) + Vector2.ONE)
			var c := {"esteira": est, "tiles": tiles, "entra": entra, "sai": sai, "niveis": niveis, "caixa": caixa,
					"oculto": oculto, "papel": papel, "lateral": lateral}
			if fechada:
				est.proximo = est
			for i in tiles.size():
				if oculto[i]:
					continue
				if chao[i]:
					_no_tile[tiles[i]] = [caminhos.size(), i]
				_no_nivel[Vector3i(tiles[i].x, tiles[i].y, niveis[i].x)] = [caminhos.size(), i]
			caminhos.append(c)


func _montar_maquinas() -> void:
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		var r: Dictionary = Registro.estruturas.get(e.nome, {})
		if r.get("grupo", "") != "maquina":
			continue
		if not maquinas.has(id):
			var m := Maquina.new(e.nome, float(r.get("velocidade", 1.0)))
			maquinas[id] = m
			match r.get("maquina", ""):
				"extrator":
					m.definir_receita("extrair_cristal", Registro.receitas["extrair_cristal"])
				"broca":
					var rec := _receita_da_jazida(e)
					if rec != "":
						m.definir_receita(rec, Registro.receitas[rec])
				"bomba":
					m.definir_receita("bombear_seiva", Registro.receitas["bombear_seiva"])
				"filtro":
					m.definir_receita("filtrar_agua", Registro.receitas["filtrar_agua"])
				"coletor":
					m.definir_receita("coletar_lixo", Registro.receitas["coletar_lixo"])
				"viveiro":
					m.definir_receita("plantar_muda", Registro.receitas["plantar_muda"])
		maquinas[id].velocidade = float(r.get("velocidade", 1.0)) * float(modo(id)[0])
		if r.get("combustivel", false) and not combustivel.has(id):
			combustivel[id] = 0.0
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if Registro.estruturas.get(e.nome, {}).get("grupo", "") == "armazem" and not baus.has(id):
			baus[id] = {}
		if e.nome == "gerador" and not combustivel.has(id):
			combustivel[id] = 0.0
		if e.nome == "laboratorio" and not laboratorios.has(id):
			laboratorios[id] = {"pacotes": 0, "t": 0.0, "energia": 0.0}
		if (e.nome == "divisor" or e.nome == "juncao") and not distribuidores.has(id):
			distribuidores[id] = {"buffer": [], "vez": 0}
		if Registro.estruturas.get(e.nome, {}).has("acumula_mj") and not acumulado.has(id):
			acumulado[id] = 0.0


## Opções internas guardadas na própria estrutura do mapa (vão junto no salvamento).
func modo(id: int) -> Array:
	return MODOS.get(mapa.estruturas[id].get("modo", "normal"), MODOS.normal) if mapa.estruturas.has(id) else MODOS.normal


func ligada(id: int) -> bool:
	return mapa.estruturas.has(id) and not mapa.estruturas[id].get("desligada", false)


## Quantos itens cabem no baú (capacidade do modelo × limite escolhido pelo jogador).
func capacidade_bau(id: int) -> int:
	var e: Dictionary = mapa.estruturas[id]
	return int(float(Registro.estruturas.get(e.nome, {}).get("capacidade_itens", BAU_MAX)) * float(e.get("limite", 1.0)))


## Consumo (+) ou geração máxima (−) de agora, em kW, já com modo e liga/desliga.
func kw_de(id: int) -> float:
	var e: Dictionary = mapa.estruturas[id]
	var regra: Dictionary = Registro.estruturas.get(e.nome, {})
	var kw := float(regra.get("energia_kw", 0.0))
	if not ligada(id):
		return 0.0
	if kw > 0.0:
		kw *= float(modo(id)[1])
	match regra.get("renovavel", ""):
		"sol": kw *= sol
		"vento": kw *= curva_turbina(float(vento_turbina.get(id, vento)))
	return kw


## Fração da potência da turbina pelo vento do lugar: parada abaixo do corte, sobe até o nominal, plena até a
## proteção; em ventania põe as pás em bandeira e rende pouco (não quebra).
static func curva_turbina(v: float) -> float:
	var c: Dictionary = Registro.ambiente.get("turbina", {})
	var corte := float(c.get("corte", 0.25))
	var nominal := float(c.get("nominal", 0.85))
	if v > float(c.get("protecao", 1.15)):
		return float(c.get("so_protecao", 0.4))
	return clampf((v - corte) / (nominal - corte), 0.0, 1.0)


func em_protecao(id: int) -> bool:
	return float(vento_turbina.get(id, vento)) > float(Registro.ambiente.get("turbina", {}).get("protecao", 1.15))


## Broca: a jazida que mais aparece debaixo dela.
func _receita_da_jazida(e: Dictionary) -> String:
	var conta := {}
	for t in Grade.tiles_da_area(e.minimo, e.area, e.rot):
		var j := mapa.gerador.distribuicao.jazida(t)
		if not j.is_empty():
			conta[j.tipo] = int(conta.get(j.tipo, 0)) + 1
	var melhor := ""
	for tipo in conta:
		if melhor == "" or conta[tipo] > conta[melhor]:
			melhor = tipo
	for k in Registro.receitas:
		if Registro.receitas[k].get("maquina", "") == "broca" and Registro.receitas[k].get("jazida", "") == melhor:
			return k
	return ""


## Rede elétrica pelos fios do mapa (Fiacao): postes, torres, geradores e quem consome.
func _montar_energia() -> void:
	Fiacao.completar(mapa)
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		var papel := Fiacao.papel(e.nome)
		if papel == "":
			continue
		var regra: Dictionary = Registro.estruturas.get(e.nome, {})
		var mj := float(combustivel.get(id, 0.0)) if papel == "fonte" else 0.0
		# núcleo (fonte própria, pouca potência) e renováveis não gastam nada
		var livre: bool = regra.get("inesgotavel", false) or regra.has("renovavel")
		_membros[id] = rede.adicionar(id, kw_de(id), 1.0e12 if livre else mj, livre)
		if regra.has("acumula_mj"):
			var a: Dictionary = _membros[id]
			a.acum_cap = float(regra.acumula_mj)
			a.acum_kw = float(regra.acumula_kw) if ligada(id) else 0.0
			a.acum_mj = float(acumulado.get(id, 0.0))
	for id in _membros:
		for o in mapa.estruturas[id].get("fios", []):
			if o > id:
				rede.ligar(id, o)
	rede.calcular()


## Ponta de caminho: lateral de outra esteira (carga lateral) ou porta de entrada de máquina/estação/torre.
## Só extratores (broca, extrator de cristal) despejam direto na esteira em frente — como uma broca de verdade.
## Toda outra construção recebe e entrega itens um a um pelas mãos de um braço (nada entra ou sai sozinho).
const DESPEJA_NA_ESTEIRA := ["broca_minerio", "extrator_cristal"]


func _ligar_pontas() -> void:
	for c in caminhos:
		var est: EsteiraCaminho = c.esteira
		if est.proximo != null:
			continue
		var k: int = c.tiles.size() - 1
		var d: int = c.sai[k]
		if d < 0:
			continue
		var t: Vector2i = c.tiles[k]
		var n: Vector2i = t + Grade.DIRECOES[d]
		var nv: int = c.niveis[k].y
		if _no_nivel.has(Vector3i(n.x, n.y, nv)):
			var alvo: Array = _no_nivel[Vector3i(n.x, n.y, nv)]
			var c2: Dictionary = caminhos[alvo[0]]
			if c2.entra[alvo[1]] == posmod(d + 2, 4):
				continue                                   # de frente: não passa
			if Construtor.TUNEIS.has(mapa.estruturas[mapa.tiles.get(n, -1)].nome if mapa.tiles.has(n) else ""):
				continue                                   # passagem subterrânea só recebe por trás
			var e2: EsteiraCaminho = c2.esteira
			var pos: float = e2.comprimento - alvo[1] - 0.5
			var ic: int = alvo[0]
			var lado := Vector2(Grade.DIRECOES[d])
			est.saida = func(item: String) -> bool:
				if not e2.inserir_em(item, pos):
					return false
				juncoes.append({"caminho": ic, "pos": pos, "lado": lado, "passo": passos})
				return true
			continue
		# esteira não enfia item em construção (o fim para o item; um braço pega dali) — só em peça de esteira
		# (divisor/junção), que é esteira também
		var id: int = mapa.tiles.get(n, -1)
		if nv > 0 or id < 0 or not distribuidores.has(id):
			continue
		for p in _portas(id):
			if p.io == "ENT" and p.tipo == "ITEM" and p.tile_fora == t and p.dir == -Grade.DIRECOES[d]:
				var dest: Object = destino_em(n)
				if dest != null:
					est.saida = func(item: String) -> bool: return dest.aceita(item) and dest.receber(item)
				break


## Saídas de máquina/estação pelas portas empurram para a esteira em frente.
func _montar_portas() -> void:
	_saidas_dist.clear()
	for id in distribuidores:
		var lista: Array[Dictionary] = []
		for p in _portas(id):
			if p.io == "SAI" and _no_tile.has(p.tile_fora):
				var a: Array = _no_tile[p.tile_fora]
				lista.append({"caminho": caminhos[a[0]], "idx": a[1]})
		_saidas_dist[id] = lista
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if not (maquinas.has(id) or e.nome == "estacao"):
			continue
		if not e.nome in DESPEJA_NA_ESTEIRA:
			continue
		for p in _portas(id):
			if p.io == "SAI" and p.tipo == "ITEM" and _no_tile.has(p.tile_fora):
				_saidas_portas.append({"origem": origem_em(p.tile_dentro), "tile": p.tile_fora})


func _montar_bracos() -> void:
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if not e.nome.begins_with("braco"):
			continue
		var r: Dictionary = Registro.estruturas[e.nome]
		var b: Braco = bracos.get(id)
		if b == null:
			b = Braco.new(float(r.ciclo_s))
			bracos[id] = b
		var f := Grade.DIRECOES[Construtor.fluxo_da_rot(e.rot)] * int(r.get("alcance", 1))
		b.filtros = e.get("filtros", [])
		b.filtro = b.filtros[0] if b.filtros.size() == 1 else ""
		b.origem = origem_em(e.minimo - f)
		b.destino = destino_em(e.minimo + f)
		if b.destino == null and b.segurando == "":
			b.estado = Braco.Estado.ESPERANDO_ITEM


func _portas(id: int) -> Array[Dictionary]:
	var e: Dictionary = mapa.estruturas[id]
	var out: Array[Dictionary] = []
	for p in Registro.modelos.get(e.nome, {}).get("portas", []):
		out.append(Grade.porta_no_mundo(p, e.minimo, e.area, e.rot))
	return out


## Receita escolhida pelo jogador (montadora, refinador, fornalha). O que estava dentro volta para o núcleo.
func escolher_receita(id: int, receita: String) -> void:
	if maquinas.has(id) and Registro.receitas.has(receita):
		var m: Maquina = maquinas[id]
		# o que estava dentro volta para o núcleo (no modo livre, sem núcleo, some)
		for d in [m.entradas, m.saidas]:
			for k in d:
				estoque_nucleo[k] = int(estoque_nucleo.get(k, 0)) + int(d[k])
		m.entradas.clear()
		m.saidas.clear()
		m.progresso = 0.0
		m.definir_receita(receita, Registro.receitas[receita])


# ------------------------------------------------------------------ quem está no tile (interfaces de braço)
func origem_em(t: Vector2i) -> Object:
	if _no_tile.has(t):
		var a: Array = _no_tile[t]
		return _NaEsteira.new(caminhos[a[0]].esteira, caminhos[a[0]].esteira.comprimento - a[1] - 0.5)
	var id: int = mapa.tiles.get(t, -1)
	if id < 0:
		return null
	if maquinas.has(id):
		return _NaMaquina.new(self, id)
	if baus.has(id):
		return _NoBau.new(baus[id], capacidade_bau(id))
	if estoques.has(id):
		return _NaEstacao.new(estoques[id])
	return null


func destino_em(t: Vector2i) -> Object:
	if _no_tile.has(t):
		var a: Array = _no_tile[t]
		return _NaEsteira.new(caminhos[a[0]].esteira, caminhos[a[0]].esteira.comprimento - a[1] - 0.5)
	var id: int = mapa.tiles.get(t, -1)
	if id < 0:
		return null
	var nome: String = mapa.estruturas[id].nome
	if maquinas.has(id):
		return _NaMaquina.new(self, id)
	if baus.has(id):
		return _NoBau.new(baus[id], capacidade_bau(id))
	if estoques.has(id):
		return _NaEstacao.new(estoques[id])
	if nome == "torre_defesa":
		return _NaTorre.new(self, id)
	if nome == "gerador":
		return _NoGerador.new(self, id)
	if nome == "nucleo":
		return _NoNucleo.new(estoque_nucleo)
	if distribuidores.has(id):
		return _NoDistribuidor.new(distribuidores[id])
	if laboratorios.has(id):
		return _NoLab.new(self, laboratorios[id])
	return null


static func valor_combustivel(item: String) -> float:
	return float(Registro.itens.get(item, {}).get("combustivel_mj", 0.0))


# ------------------------------------------------------------------ tick
func tick(dt: float) -> void:
	passos += 1
	while not juncoes.is_empty() and passos - int(juncoes[0].passo) > 6:
		juncoes.pop_front()
	emissao.clear()
	for id in _membros:
		var mb: Dictionary = _membros[id]
		if mb.livre:
			mb.kw = kw_de(id)                   # renovável: rende conforme o sol/vento de agora
		elif mb.kw < 0.0:
			mb.combustivel_mj = combustivel.get(id, 0.0)
	rede.tick(dt)
	for id in _membros:
		var m: Dictionary = _membros[id]
		if m.acum_cap > 0.0:
			acumulado[id] = m.acum_mj
		if m.livre or m.acum_cap > 0.0:
			continue
		if m.kw < 0.0:
			var antes: float = combustivel.get(id, 0.0)
			combustivel[id] = m.combustivel_mj
			if m.combustivel_mj < antes:
				_emitir(id, (antes - m.combustivel_mj) / (-m.kw / 1000.0))   # segundos equivalentes a plena carga
		else:
			var en: float = rede.satisfacao_por_rede.get(m.rede, 0.0) if m.rede >= 0 and ligada(id) else 0.0
			var o: Object = maquinas.get(id, bracos.get(id))
			if o != null:
				o.set("energia", en)
			elif laboratorios.has(id):
				laboratorios[id].energia = en
	for id in maquinas:
		var m: Maquina = maquinas[id]
		if combustivel.has(id):
			m.energia = 1.0 if combustivel[id] > 0.0 and ligada(id) else 0.0
		m.tick(dt)
		if m.estado == Maquina.Estado.TRABALHANDO:
			_emitir(id, dt * m.energia)
			if combustivel.has(id):
				combustivel[id] = maxf(0.0, combustivel[id] - FOGO_KW / 1000.0 * dt)
	_tick_fluidos(dt)
	for id in distribuidores:
		var d: Dictionary = distribuidores[id]
		var saidas: Array = _saidas_dist.get(id, [])
		if d.buffer.is_empty() or saidas.is_empty():
			continue
		# divisor reparte em rodízio; junção tem uma saída só
		for tentativa in saidas.size():
			var s: Dictionary = saidas[(d.vez + tentativa) % saidas.size()]
			var est: EsteiraCaminho = s.caminho.esteira
			var ok := est.inserir_na_entrada(d.buffer[0]) if s.idx == 0 else est.inserir_em(d.buffer[0], s.caminho.esteira.comprimento - s.idx - 0.5)
			if ok:
				d.buffer.pop_front()
				d.vez = (d.vez + tentativa + 1) % saidas.size()
				break
	for s in _saidas_portas:
		if s.origem == null:
			continue
		var a: Array = _no_tile[s.tile]
		var c: Dictionary = caminhos[a[0]]
		var est: EsteiraCaminho = c.esteira
		if a[1] == 0 and not est.cabe_na_entrada():
			continue
		var item: String = s.origem.pegar_para_braco("")
		if item == "":
			continue
		var ok := est.inserir_na_entrada(item) if a[1] == 0 else est.inserir_em(item, est.comprimento - a[1] - 0.5)
		if not ok:
			s.origem.devolver(item)
	concluidas.clear()
	for id in laboratorios:
		var lab: Dictionary = laboratorios[id]
		if pesquisa == null or pesquisa.ativa == "" or lab.pacotes <= 0 or lab.energia <= 0.0:
			continue
		lab.t += dt * lab.energia
		if lab.t >= pesquisa.tempo_por_pacote():
			lab.t = 0.0
			lab.pacotes -= 1
			var fim := pesquisa.avancar()
			if fim != "":
				concluidas.append(fim)
	for id in bracos:
		bracos[id].tick(dt)
	for c in caminhos:
		c.esteira.tick(dt)


## Pontos de poluição: `poluicao` de estruturas.json é por minuto de trabalho.
func _emitir(id: int, segundos: float) -> void:
	var nome: String = mapa.estruturas[id].nome
	var p := float(Registro.estruturas.get(nome, {}).get("poluicao", 0.0))
	if p > 0.0:
		emissao[id] = float(emissao.get(id, 0.0)) + p / 60.0 * segundos * float(modo(id)[2])


## Ponto do mundo (plano da grade) de um item na esteira: `pos` = distância da saída do caminho.
func ponto_do_item(c: Dictionary, pos: float) -> Vector2:
	var n: int = c.tiles.size()
	var s := clampf(c.esteira.comprimento - pos, 0.0, float(n) - 1e-4)
	var k := int(s)
	return ponto_no_tile(c.tiles[k], c.entra[k], c.sai[k], s - k)


## Altura (m) do item na esteira: segue o nível de cada tile (rampa sobe/desce no meio do tile).
func altura_do_item(c: Dictionary, pos: float) -> float:
	var n: int = c.tiles.size()
	var s := clampf(c.esteira.comprimento - pos, 0.0, float(n) - 1e-4)
	var k := int(s)
	var nv: Vector2i = c.niveis[k]
	return lerpf(nv.x, nv.y, s - k) * 0.5


## Caminho dentro de um tile: da borda de entrada (f = 0) à de saída (f = 1); curva = quarto de círculo.
static func ponto_no_tile(t: Vector2i, entra: int, sai: int, f: float) -> Vector2:
	var centro := Vector2(t) + Vector2(0.5, 0.5)
	var din := Vector2(Grade.DIRECOES[entra])
	var a := centro - din * 0.5
	if sai < 0 or sai == entra:
		return a + din * f
	var dout := Vector2(Grade.DIRECOES[sai])
	var b := centro + dout * 0.5
	var canto := a + dout * 0.5               # centro do arco (canto do tile)
	var ang0 := (a - canto).angle()
	var ang1 := (b - canto).angle()
	return canto + Vector2.from_angle(ang0 + angle_difference(ang0, ang1) * f) * 0.5


## Altura extra do item na calha da rampa de junção, `e` m além da borda (mesmo perfil do modelo esteira_juncao):
## sobe por cima do trilho da vizinha e desce até a lona dela.
static func altura_calha(e: float) -> float:
	var y := 0.5 + e
	if y < 0.57:
		return maxf(0.0, (y - 0.42) / 0.15 * 0.085)
	return maxf(0.0, 0.085 - (y - 0.57) / 0.18 * 0.075)


# ------------------------------------------------------------------ fluidos
## Canos ligados (portas de fluido frente a frente) formam uma rede: um volume só, um fluido só, capacidade =
## soma das peças (cano 100, tanque 25 000). Bomba sobre poça de seiva enche a rede; refinador bebe dela.
func _montar_fluidos() -> void:
	redes_fluido.clear()
	_rede_do.clear()
	_ligacoes_fluido.clear()
	var pontas := {}          # tile_dentro|dir → id (cano/tanque)
	var canos: Array[int] = []
	for id in mapa.estruturas:
		var nome: String = mapa.estruturas[id].nome
		if nome.begins_with("cano") or nome == "tanque":
			canos.append(id)
			for p in _portas(id):
				if p.tipo == "FLUIDO":
					pontas["%s|%s" % [p.tile_dentro, p.dir]] = id
	var pai := {}
	for id in canos:
		pai[id] = id
	var raiz := func(x: int) -> int:
		while pai[x] != x:
			x = pai[x]
		return x
	for id in canos:
		for p in _portas(id):
			if p.tipo != "FLUIDO":
				continue
			var outro: int = pontas.get("%s|%s" % [p.tile_fora, -p.dir], -1)
			if outro >= 0:
				pai[raiz.call(id)] = raiz.call(outro)
	var idx := {}
	for id in canos:
		var r: int = raiz.call(id)
		if not idx.has(r):
			idx[r] = redes_fluido.size()
			redes_fluido.append({"fluido": "", "qtd": 0.0, "cap": 0.0, "membros": [] as Array[int]})
		var rede: Dictionary = redes_fluido[idx[r]]
		rede.cap += float(Registro.estruturas.get(mapa.estruturas[id].nome, {}).get("capacidade", 100))
		rede.membros.append(id)
		_rede_do[id] = idx[r]
	# máquinas com porta de fluido encostada num cano que abre para elas
	for id in maquinas:
		for p in _portas(id):
			if p.tipo != "FLUIDO":
				continue
			var cano: int = pontas.get("%s|%s" % [p.tile_fora, -p.dir], -1)
			if cano >= 0:
				_ligacoes_fluido.append({"id": id, "io": p.io, "rede": _rede_do[cano]})


func _tick_fluidos(dt: float) -> void:
	for l in _ligacoes_fluido:
		var rede: Dictionary = redes_fluido[l.rede]
		var m: Maquina = maquinas[l.id]
		if l.io == "SAI":
			for f in m.receita.get("saidas_fluido", {}):
				var q := float(m.fluidos.get(f, 0.0))
				if q > 0.0 and (rede.fluido == "" or rede.fluido == f):
					var vai := minf(q, rede.cap - rede.qtd)
					rede.qtd += vai
					rede.fluido = f
					m.fluidos[f] = q - vai
					if vai > 0.0:
						m.acordar()
		else:
			for f in m.receita.get("entradas_fluido", {}):
				if rede.fluido == f and rede.qtd > 0.0:
					var vem := minf(rede.qtd, m.falta_fluido(f))
					if vem > 0.0:
						rede.qtd -= vem
						m.receber_fluido(f, vem)
		if rede.qtd <= 0.001:
			rede.qtd = 0.0
			rede.fluido = ""


func rede_de(id: int) -> Dictionary:
	return redes_fluido[_rede_do[id]] if _rede_do.has(id) else {}


## Antes de remontar: quanto fluido cada cano/tanque tinha (fatia proporcional da rede).
func _guardar_fluidos() -> Dictionary:
	var out := {}
	for rede in redes_fluido:
		if rede.qtd <= 0.0:
			continue
		for id in rede.membros:
			if mapa.estruturas.has(id):
				var cap := float(Registro.estruturas.get(mapa.estruturas[id].nome, {}).get("capacidade", 100))
				out[id] = [rede.fluido, rede.qtd * cap / rede.cap]
	return out


func _restaurar_fluidos(salvo: Dictionary) -> void:
	for id in salvo:
		if _rede_do.has(id):
			var rede: Dictionary = redes_fluido[_rede_do[id]]
			if rede.fluido == "" or rede.fluido == salvo[id][0]:
				rede.fluido = salvo[id][0]
				rede.qtd = minf(rede.cap, rede.qtd + float(salvo[id][1]))


# ------------------------------------------------------------------ salvamento
func estado() -> Dictionary:
	var maq := {}
	for id in maquinas:
		var m: Maquina = maquinas[id]
		maq[id] = {"receita": m.receita_id, "entradas": m.entradas, "saidas": m.saidas, "progresso": m.progresso,
				"produzidos": m.produzidos, "fluidos": m.fluidos}
	var br := {}
	for id in bracos:
		var b: Braco = bracos[id]
		br[id] = {"segurando": b.segurando, "estado": b.estado, "t": b.t}
	return {"maquinas": maq, "bracos": br, "baus": baus, "combustivel": combustivel, "laboratorios": laboratorios, "acumulado": acumulado,
			"distribuidores": distribuidores, "fluidos": _guardar_fluidos(), "itens": _guardar_itens()}


## Depois de mapa restaurado: remonta e devolve o conteúdo de cada um (os dicionários de baú são preenchidos
## no lugar, porque os braços já guardam a referência).
func restaurar(d: Dictionary) -> void:
	reconstruir()
	for id in d.get("maquinas", {}):
		if not maquinas.has(id):
			continue
		var s: Dictionary = d.maquinas[id]
		var m: Maquina = maquinas[id]
		if s.receita != "" and Registro.receitas.has(s.receita):
			m.definir_receita(s.receita, Registro.receitas[s.receita])
		m.entradas = s.entradas
		m.saidas = s.saidas
		m.progresso = s.progresso
		m.produzidos = s.produzidos
		m.fluidos = s.get("fluidos", {})
		m.acordar()
	for id in d.get("bracos", {}):
		if bracos.has(id):
			var b: Braco = bracos[id]
			b.segurando = d.bracos[id].segurando
			b.estado = d.bracos[id].estado
			b.t = d.bracos[id].t
	for id in d.get("baus", {}):
		if baus.has(id):
			baus[id].merge(d.baus[id], true)
	for id in d.get("combustivel", {}):
		combustivel[id] = d.combustivel[id]
	for id in d.get("acumulado", {}):
		if acumulado.has(id):
			acumulado[id] = d.acumulado[id]
			if _membros.has(id):
				_membros[id].acum_mj = d.acumulado[id]
	for id in d.get("distribuidores", {}):
		if distribuidores.has(id):
			distribuidores[id].merge(d.distribuidores[id], true)
	_restaurar_fluidos(d.get("fluidos", {}))
	for id in d.get("laboratorios", {}):
		if laboratorios.has(id):
			laboratorios[id].merge(d.laboratorios[id], true)
	var itens: Array[Dictionary] = []
	itens.assign(d.get("itens", []))
	_restaurar_itens(itens)


# ------------------------------------------------------------------ guardar/restaurar itens das esteiras
func _guardar_itens() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for c in caminhos:
		var est: EsteiraCaminho = c.esteira
		var ps := est.posicoes()
		var n: int = c.tiles.size()
		for i in ps.size():
			var s := est.comprimento - ps[i]
			var k := clampi(int(s), 0, n - 1)
			while k > 0 and c.oculto[k]:
				k -= 1                                    # debaixo da terra: guarda a partir da entrada da passagem
			out.append({"tile": Vector3i(c.tiles[k].x, c.tiles[k].y, c.niveis[k].x), "f": s - k, "item": est.itens[i]})
	return out


func _restaurar_itens(guardados: Array[Dictionary]) -> void:
	for g in guardados:
		if not _no_nivel.has(g.tile):
			continue
		var a: Array = _no_nivel[g.tile]
		var c: Dictionary = caminhos[a[0]]
		c.esteira.inserir_em(g.item, c.esteira.comprimento - (a[1] + g.f))


# ------------------------------------------------------------------ interfaces
class _NaEsteira:
	var e: EsteiraCaminho
	var pos: float
	func _init(p_e: EsteiraCaminho, p_pos: float) -> void:
		e = p_e
		pos = p_pos
	func pegar_para_braco(_f: String) -> String: return e.retirar_perto(pos, 0.5)
	func pegar_se(aceito: Callable) -> String:
		# alcance: pega o primeiro que estiver dentro do tile em frente (passando ou parado), não só no fim
		var ps := e.posicoes()
		for i in ps.size():
			# passando: só quando está bem embaixo da garra (não "teleporta"); parado no fim da linha: alcança
			var perto := absf(ps[i] - pos) <= 0.3 or (ps[i] < 0.02 and absf(ps[i] - pos) <= 0.55)
			if perto and aceito.call(e.itens[i]):
				return e.retirar_perto(ps[i], 0.01)
		return ""
	func aceita(_i: String) -> bool: return true
	func receber(i: String) -> bool:
		if pos >= e.util() - 0.5:
			return e.inserir_na_entrada(i) or e.inserir_em(i, pos)
		return e.inserir_em(i, pos)
	func devolver(_i: String) -> void: pass


class _NaMaquina:
	var f: Fabrica
	var id: int
	var m: Maquina
	func _init(p_f: Fabrica, p_id: int) -> void:
		f = p_f
		id = p_id
		m = f.maquinas[id]
	func _combustivel(i: String) -> bool:
		return f.combustivel.has(id) and Fabrica.valor_combustivel(i) > 0.0
	func aceita(i: String) -> bool:
		if _combustivel(i):
			return f.combustivel[id] < Fabrica.ESTOQUE_FOGO_MJ
		if m.receita.is_empty() and m.nome == "fornalha":
			return _receita_para(i) != ""           # fornalha escolhe a receita pelo que chega
		return m.aceita(i)
	func receber(i: String) -> bool:
		if not aceita(i):
			return false
		if _combustivel(i):
			f.combustivel[id] += Fabrica.valor_combustivel(i)
			m.acordar()
			return true
		if m.receita.is_empty():
			var r := _receita_para(i)
			m.definir_receita(r, Registro.receitas[r])
		return m.receber(i)
	func _receita_para(i: String) -> String:
		for k in Registro.receitas_da_maquina("fornalha"):
			if Registro.receitas[k].get("entradas", {}).has(i):
				return k
		return ""
	func pegar_para_braco(filtro: String) -> String: return m.pegar_para_braco(filtro)
	func pegar_se(aceito: Callable) -> String:
		for item in m.saidas:
			if int(m.saidas[item]) > 0 and aceito.call(item):
				return m.pegar_para_braco(item)
		return ""
	func devolver(i: String) -> void:
		m.saidas[i] = int(m.saidas.get(i, 0)) + 1


class _NoBau:
	var b: Dictionary
	var cap: int
	func _init(p_b: Dictionary, p_cap: int) -> void:
		b = p_b
		cap = p_cap
	func _total() -> int:
		var n := 0
		for k in b: n += int(b[k])
		return n
	func aceita(_i: String) -> bool: return _total() < cap
	func receber(i: String) -> bool:
		if not aceita(i): return false
		b[i] = int(b.get(i, 0)) + 1
		return true
	func pegar_para_braco(filtro: String) -> String:
		return pegar_se(func(i: String) -> bool: return filtro == "" or i == filtro)
	func pegar_se(aceito: Callable) -> String:
		for i in b:
			if int(b[i]) > 0 and aceito.call(i):
				b[i] = int(b[i]) - 1
				return i
		return ""
	func devolver(i: String) -> void: b[i] = int(b.get(i, 0)) + 1


class _NaEstacao:
	var es: Dictionary
	func _init(p: Dictionary) -> void: es = p
	func aceita(i: String) -> bool: return int(es.enviar.get(i, 0)) < 400
	func receber(i: String) -> bool:
		if not aceita(i): return false
		es.enviar[i] = int(es.enviar.get(i, 0)) + 1
		return true
	func pegar_para_braco(filtro: String) -> String:
		return pegar_se(func(i: String) -> bool: return filtro == "" or i == filtro)
	func pegar_se(aceito: Callable) -> String:
		for i in es.recebido:
			if int(es.recebido[i]) > 0 and aceito.call(i):
				es.recebido[i] = int(es.recebido[i]) - 1
				return i
		return ""
	func devolver(i: String) -> void: es.recebido[i] = int(es.recebido.get(i, 0)) + 1


class _NaTorre:
	var f: Fabrica
	var id: int
	func _init(p_f: Fabrica, p_id: int) -> void:
		f = p_f
		id = p_id
	func aceita(i: String) -> bool: return i == "municao" and f.torre_receber.is_valid()
	func receber(i: String) -> bool:
		if not aceita(i): return false
		f.torre_receber.call(id, Fabrica.TIROS_POR_MUNICAO)
		return true


class _NoGerador:
	var f: Fabrica
	var id: int
	func _init(p_f: Fabrica, p_id: int) -> void:
		f = p_f
		id = p_id
	func aceita(i: String) -> bool:
		return Fabrica.valor_combustivel(i) > 0.0 and f.combustivel.get(id, 0.0) < Fabrica.ESTOQUE_GERADOR_MJ
	func receber(i: String) -> bool:
		if not aceita(i): return false
		f.combustivel[id] = f.combustivel.get(id, 0.0) + Fabrica.valor_combustivel(i)
		return true


class _NoNucleo:
	var e: Dictionary
	func _init(p: Dictionary) -> void: e = p
	func aceita(_i: String) -> bool: return true
	func receber(i: String) -> bool:
		e[i] = int(e.get(i, 0)) + 1
		return true


class _NoLab:
	var f: Fabrica
	var lab: Dictionary
	func _init(p_f: Fabrica, p_lab: Dictionary) -> void:
		f = p_f
		lab = p_lab
	func aceita(i: String) -> bool: return i == "pacote_pesquisa" and lab.pacotes < 10
	func receber(i: String) -> bool:
		if not aceita(i): return false
		lab.pacotes += 1
		return true


class _NoDistribuidor:
	var d: Dictionary
	func _init(p: Dictionary) -> void: d = p
	func aceita(_i: String) -> bool: return d.buffer.size() < 2
	func receber(i: String) -> bool:
		if not aceita(i): return false
		d.buffer.append(i)
		return true
