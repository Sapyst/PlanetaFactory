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
const LAB_MAX := 10              ## pacotes de cada tipo que o laboratório guarda
## Modo de trabalho (opção interna de máquina elétrica): [velocidade, energia, poluição].
const MODOS := {"eco": [0.5, 0.4, 0.6], "normal": [1.0, 1.0, 1.0], "turbo": [1.5, 2.0, 1.6]}

var mapa: MapaOcupacao
var rede := RedeEnergia.new()
var caminhos: Array[Dictionary] = []   ## {esteira: EsteiraCaminho, tiles: Array[Vector2i], entra: Array[int], sai: Array[int]}
var maquinas: Dictionary = {}          ## id → Maquina
var bracos: Dictionary = {}            ## id → Braco
var baus: Dictionary = {}              ## id → {item: n}
var combustivel: Dictionary = {}       ## id (fornalha/gerador) → MJ guardado
var fator_fogo: Dictionary = {}        ## id → poluição do que está queimando (média pelos MJ; briquete 0,7, carvão 1)
var estoques: Dictionary = {}          ## id da estação → {enviar, recebido} (o mundo passa o mesmo dicionário dos trens)
var torre_receber: Callable            ## func(id, tiros) — a colônia guarda a munição das torres
var torre_aceita: Callable             ## (opcional) func(id) -> bool: cabe mais munição? (metralhadora cheia recusa)
var emissao: Dictionary = {}           ## id → pontos de poluição emitidos no último tick
var estoque_nucleo: Dictionary = {}    ## o mesmo dicionário do inventário do Construtor (tudo que entra no núcleo)
var pesquisa: Pesquisa = null
var laboratorios: Dictionary = {}      ## id → {pacotes: {item: n}, t, energia}
var concluidas: Array[String] = []     ## pesquisas terminadas no último tick (o mundo avisa)
var passos := 0                        ## quantos ticks já rodaram (o desenho só refaz quando muda)
var redes_fluido: Array[Dictionary] = []    ## {fluido, qtd, cap, membros: Array[int]}
var _rede_do: Dictionary = {}          ## id (cano/tanque) → índice da rede
var _ligacoes_fluido: Array[Dictionary] = []  ## {id (máquina), io, rede}
var _estacoes_fluido: Array[Dictionary] = []  ## {id (estação), rede, bomba}: bomba de estação encostada nela
var bombeando: Dictionary = {}         ## id da bomba de estação → true se moveu fluido no último tick
var _trilho_grupo: Dictionary = {}     ## id do trilho energizado → índice do trecho (peças encostadas)
var _trechos: Array = []               ## índice do trecho → Array de ids
var demanda_trilho: Dictionary = {}    ## índice do trecho → kW que os trens elétricos pediram (o mundo põe; gasto no tick)
# rede lógica (pesquisa rede_logica): sensores mandam um valor por canal; o comparador liga/desliga os vizinhos
const CANAIS := ["A", "B", "C", "D"]
var canais: Dictionary = {}            ## canal → soma dos valores dos sensores dele (último tick)
var logica_off: Dictionary = {}        ## id → true: desligado por um comparador encostado
var sensores: Dictionary = {}          ## id do sensor de esteira → {total, janela: Array (itens por segundo), seg, t} (salvo)
var _sens_esteira: Array[Dictionary] = []   ## {id, caminho (índice), marca (m da saída), antes, saidos}
var _comparadores: Array[Dictionary] = []   ## {id, vizinhos: Array[int]}
var _comandados: Dictionary = {}       ## id → true: encostado num comparador (kW refeito a cada tick)
var _valvulas: Array[Dictionary] = []  ## {id, ent: rede, sai: rede}
var valvula_passou: Dictionary = {}    ## id da válvula → true se passou fluido no último tick
var _pontas_fluido: Dictionary = {}    ## "tile_dentro|dir" → id do cano (montado em _montar_fluidos)
var distribuidores: Dictionary = {}    ## id (divisor/junção) → {buffer: Array[String], vez: int}
var _saidas_dist: Dictionary = {}      ## id → Array[{caminho, idx}]
var _no_tile: Dictionary = {}          ## tile → [caminho, índice do tile no caminho] (só esteira no chão)
var _no_nivel: Dictionary = {}         ## Vector3i(x, y, nível de entrada) → [caminho, índice]
var _saidas_portas: Array[Dictionary] = []   ## {origem: Object, tile: Vector2i}
var _membros: Dictionary = {}          ## id → membro da rede (dict)
var acumulado: Dictionary = {}         ## id do acumulador → MJ guardados
var carga_torre: Dictionary = {}       ## id da torre de defesa → MJ guardados para atirar (puxa da rede até encher)
var energia_rede: Dictionary = {}      ## id de quem consome → satisfação da rede (0..1) no último tick
var sol := 1.0                         ## 0..1: quanto os painéis solares rendem agora (o mundo passa do clima)
var vento := 0.5                       ## força do vento (0..~1,6) para turbina sem valor próprio
var vento_turbina: Dictionary = {}     ## id da turbina → vento no lugar dela (clima × VentoLocal × rajada), o mundo passa
var juncoes: Array[Dictionary] = []    ## itens que acabaram de entrar pela lateral: {caminho, pos, lado, passo} (desenho desliza)
var _melhorias_de := ""                ## assinatura das pesquisas já aplicadas nas máquinas (refaz quando muda)
var chuva := 0.0                       ## 0..1: chuva do clima de agora (coletor de chuva; o mundo passa)
var neblina := 0.0                     ## 0..1: neblina do clima de agora (condensador; o mundo passa)
var jatos: Dictionary = {}             ## id do supressor → ponto (grade) do fogo que ele está molhando (o ambiente põe)
var chuva_maq: Dictionary = {}         ## id do coletor de chuva → chuva no lugar dele (semeador/regulador; o mundo passa)
var raio_em: Dictionary = {}           ## id do captador → s de animação que restam depois do raio (descarga nos eletrodos)

const DISTRIBUIDORES := ["divisor", "juncao", "divisor_filtro"]
## Saídas do divisor pelo lado do modelo (porta PORTA_ITEM_SAI_<lado>): o item entra pelo sul e segue para o norte.
const LADOS_DIVISOR := {"N": "Frente", "L": "Direita", "O": "Esquerda"}
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
	for d in [maquinas, bracos, baus, combustivel, fator_fogo, laboratorios, distribuidores, acumulado, carga_torre, energia_rede]:
		for id in d.keys():
			if not vivos.has(id):
				d.erase(id)
	_montar_esteiras()
	_montar_maquinas()
	_montar_energia()
	_montar_trilhos_energizados()
	_ligar_pontas()
	_montar_portas()
	_montar_bracos()
	_montar_fluidos()
	_montar_logica()
	_restaurar_fluidos(fluido_salvo)
	_restaurar_itens(guardados)


## Nós de esteira chaveados por (tile, nível de entrada): esteira elevada e rampa (sobe/desce) entram na mesma
## conta — um caminho pode subir e descer. `_no_tile` (braços, portas) só vê o que está no chão.
## Classes diferentes (básica → rápida) não se juntam num caminho só: cada trecho anda na velocidade da sua classe e o
## fim de um entrega na entrada do outro (`elos`). A passagem subterrânea só liga entrada e saída da mesma classe.
func _montar_esteiras() -> void:
	var cinta := {}       # Vector3i(x, y, n_entrada) → {tile, entra, sai, n_in, n_out, chao, classe}
	var elos := {}        # chave do último tile de um trecho → chave do primeiro do trecho seguinte (troca de classe)
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
			# passagem subterrânea: liga na primeira saída alinhada à frente, da mesma classe, até `alcance` tiles
			var alc := int(Construtor.regra_esteira("esteira_tunel_entrada", no.classe).get("alcance", 5))
			for i in range(1, alc + 1):
				var tt: Vector2i = no.tile + Grade.DIRECOES[no.sai] * i
				var kk := Vector3i(tt.x, tt.y, no.n_out)
				if cinta.has(kk) and cinta[kk].get("tunel", "") == "saida" and cinta[kk].entra == no.sai \
						and cinta[kk].classe == no.classe:
					return kk
			return Vector3i(0, 0, -1)
		var t: Vector2i = no.tile + Grade.DIRECOES[no.sai]
		var n := Vector3i(t.x, t.y, no.n_out)
		if cinta.has(n) and cinta[n].entra == no.sai and cinta[n].get("tunel", "") != "saida" \
				and mapa.gerador.nivel(t) == mapa.gerador.nivel(no.tile):
			if cinta[n].classe != no.classe:
				elos[k] = n                   # outra velocidade: outro caminho, ligado pela ponta
				return Vector3i(0, 0, -1)
			return n
		return Vector3i(0, 0, -1)
	var tem_antes := {}
	for k in cinta:
		var n: Vector3i = proximo.call(k)
		if n.z >= 0:
			tem_antes[n] = true
	var visto := {}
	var comeco := {}      # chave do 1º tile → índice do caminho
	var final := {}       # chave do último tile → índice do caminho
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
					float(Construtor.regra_esteira("esteira_reta", cinta[k0].classe).get("velocidade", 1.875)))
			comeco[k0] = caminhos.size()
			final[k] = caminhos.size()
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
			c["classe"] = cinta[k0].classe
			caminhos.append(c)
	for k in elos:
		if final.has(k) and comeco.has(elos[k]):
			caminhos[final[k]].esteira.proximo = caminhos[comeco[elos[k]]].esteira


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
				"bomba_agua":
					m.definir_receita("bombear_agua", Registro.receitas["bombear_agua"])
				"coletor_chuva":
					m.definir_receita("coletar_chuva", Registro.receitas["coletar_chuva"])
				"condensador":
					m.definir_receita("condensar_neblina", Registro.receitas["condensar_neblina"])
				"supressor":
					m.definir_receita("borrifar_agua", Registro.receitas["borrifar_agua"])
				"captador":
					m.definir_receita("carregar_cristal", Registro.receitas["carregar_cristal"])
				"filtro":
					m.definir_receita("filtrar_agua", Registro.receitas["filtrar_agua"])
				"coletor":
					m.definir_receita("coletar_lixo", Registro.receitas["coletar_lixo"])
				"viveiro":
					m.definir_receita("plantar_muda", Registro.receitas["plantar_muda"])
				"purificador":
					m.definir_receita("purificar_ar", Registro.receitas["purificar_ar"])
				"biodigestor":
					m.definir_receita("biodigerir", Registro.receitas["biodigerir"])
				"tratamento":
					m.definir_receita("tratar_agua", Registro.receitas["tratar_agua"])
				"semeador_bioma":
					m.definir_receita("restaurar_bioma", Registro.receitas["restaurar_bioma"])
				"estacao_drones":
					m.definir_receita("fabricar_drone", Registro.receitas["fabricar_drone"])
					m.retem = ["drone"]                 # o drone pronto entra na frota (Drones), não vai para braço
		maquinas[id].velocidade = float(r.get("velocidade", 1.0)) * float(modo(id)[0])
		maquinas[id].tanque_fluido = float(r.get("tanque_fluido", 0.0))
		maquinas[id].transborda = bool(r.get("transborda", false))
		if r.get("combustivel", false) and not combustivel.has(id):
			combustivel[id] = 0.0
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if Registro.estruturas.get(e.nome, {}).get("grupo", "") == "armazem" and not baus.has(id):
			baus[id] = {}
		if e.nome == "gerador" and not combustivel.has(id):
			combustivel[id] = 0.0
		if e.nome == "laboratorio" and not laboratorios.has(id):
			laboratorios[id] = {"pacotes": {}, "t": 0.0, "energia": 0.0}
		if e.nome in DISTRIBUIDORES and not distribuidores.has(id):
			distribuidores[id] = {"buffer": [], "vez": 0}
		if Registro.estruturas.get(e.nome, {}).has("acumula_mj") and not acumulado.has(id):
			acumulado[id] = 0.0
		if Registro.estruturas.get(e.nome, {}).has("carga_mj") and not carga_torre.has(id):
			carga_torre[id] = 0.0


## Carga máxima (MJ) da torre de energia / gerador de escudo, com as melhorias (escudo 2: "escudo_carga").
func carga_max(id: int) -> float:
	var regra: Dictionary = Registro.estruturas.get(mapa.estruturas[id].nome, {})
	var cap := float(regra.get("carga_mj", 1.0))
	if regra.has("escudo"):
		cap *= 1.0 + _bonus("escudo_carga")
	return cap


func _bonus(chave: String) -> float:
	return pesquisa.bonus(chave) if pesquisa != null else 0.0


## Energia de um raio (para-raios, captador, cúpula) entrando na rede de `id`: vai para os acumuladores dela, cada um
## pelo espaço livre que tem (sem limite de potência: é um pulso). Devolve quanto coube (MJ); o resto se perde.
func injetar(id: int, mj: float) -> float:
	if not _membros.has(id) or mj <= 0.0:
		return 0.0
	var r: int = _membros[id].rede
	var livres: Array = []
	var cabe := 0.0
	for k in _membros:
		var a: Dictionary = _membros[k]
		if a.rede == r and a.acum_cap > 0.0 and ligada(k):
			livres.append(k)
			cabe += a.acum_cap - a.acum_mj
	if cabe <= 0.0:
		return 0.0
	var poe := minf(mj, cabe)
	for k in livres:
		var a: Dictionary = _membros[k]
		a.acum_mj = minf(a.acum_cap, a.acum_mj + poe * (a.acum_cap - a.acum_mj) / cabe)
		acumulado[k] = a.acum_mj
	return poe


## Raio no captador de carga: um ciclo na hora (1 cristal lapidado + 30 de água → 1 carregado) se tiver insumo e
## lugar na saída. A descarga anima os eletrodos por alguns segundos.
func raio_no_captador(id: int) -> bool:
	var m: Maquina = maquinas.get(id)
	if m == null:
		return false
	raio_em[id] = float(Registro.estruturas.get(mapa.estruturas[id].nome, {}).get("capta_raio", {}).get("anima_s", 4.0))
	return m.ciclo_agora()


## Energia que chega na estrutura agora (0..1: satisfação da rede dela; 0 se não está ligada a nada).
func energia(id: int) -> float:
	return float(energia_rede.get(id, 0.0))


## Torre de defesa atira com a energia guardada: gasta `mj` se tiver (a colônia chama a cada tiro).
func gastar_torre(id: int, mj: float) -> bool:
	if float(carga_torre.get(id, 0.0)) + 1e-6 < mj:
		return false
	carga_torre[id] = float(carga_torre[id]) - mj
	return true


## Opções internas guardadas na própria estrutura do mapa (vão junto no salvamento).
func modo(id: int) -> Array:
	return MODOS.get(mapa.estruturas[id].get("modo", "normal"), MODOS.normal) if mapa.estruturas.has(id) else MODOS.normal


func ligada(id: int) -> bool:
	return mapa.estruturas.has(id) and not mapa.estruturas[id].get("desligada", false) and not logica_off.has(id)


## Quantos itens cabem no baú (capacidade do modelo × limite escolhido pelo jogador).
func capacidade_bau(id: int) -> int:
	var e: Dictionary = mapa.estruturas[id]
	return int(float(Registro.estruturas.get(e.nome, {}).get("capacidade_itens", BAU_MAX)) * float(e.get("limite", 1.0)))


## Silo de granel: guarda um tipo de item só (o primeiro que entra; esvaziou, aceita outro).
func um_tipo(id: int) -> bool:
	return mapa.estruturas.has(id) and bool(Registro.estruturas.get(mapa.estruturas[id].nome, {}).get("um_tipo", false))


## O item que está no armazém agora ("" se vazio) — para o silo, que é de um tipo só.
static func tipo_guardado(b: Dictionary) -> String:
	for k in b:
		if int(b[k]) > 0:
			return k
	return ""


## Consumo (+) ou geração máxima (−) de agora, em kW, já com modo e liga/desliga.
func kw_de(id: int) -> float:
	var e: Dictionary = mapa.estruturas[id]
	var regra: Dictionary = Registro.estruturas.get(e.nome, {})
	var kw := float(regra.get("energia_kw", 0.0))
	if not ligada(id):
		return 0.0
	if kw > 0.0:
		kw *= float(modo(id)[1])
		if regra.has("escudo"):
			kw *= 1.0 + _bonus("escudo_recarga")          # escudo 2: recarga 2×
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


## Trilho energizado (trem_eletrico): peças encostadas formam um trecho; o terceiro trilho conduz, então basta uma
## peça do trecho ligada a um poste para o trecho todo ter energia.
func _montar_trilhos_energizados() -> void:
	_trilho_grupo.clear()
	_trechos.clear()
	for id in mapa.estruturas:
		if mapa.estruturas[id].nome != "trilho_energizado" or _trilho_grupo.has(id):
			continue
		var g := _trechos.size()
		var lista: Array[int] = [id]
		_trilho_grupo[id] = g
		var i := 0
		while i < lista.size():
			var t: Vector2i = mapa.estruturas[lista[i]].minimo
			for d in Grade.DIRECOES:
				var o: int = mapa.tiles.get(t + d, -1)
				if o >= 0 and not _trilho_grupo.has(o) and mapa.estruturas.has(o) and mapa.estruturas[o].nome == "trilho_energizado":
					_trilho_grupo[o] = g
					lista.append(o)
			i += 1
		_trechos.append(lista)


## Energia (0..1) do trecho de trilho energizado da estrutura `id`: a melhor entre as peças dele ligadas a poste.
## -1 se `id` não é trilho energizado.
func energia_trilho(id: int) -> float:
	if not _trilho_grupo.has(id):
		return -1.0
	var m := 0.0
	for k in _trechos[_trilho_grupo[id]]:
		m = maxf(m, energia(k))
	return m


## Trem elétrico andando sobre o trilho `id`: soma `kw` na conta do trecho (gasto no próximo tick, repartido entre as
## peças ligadas a poste).
func pedir_trilho(id: int, kw: float) -> void:
	if _trilho_grupo.has(id):
		var g: int = _trilho_grupo[id]
		demanda_trilho[g] = float(demanda_trilho.get(g, 0.0)) + kw


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
				lista.append({"caminho": caminhos[a[0]], "idx": a[1], "lado": String(p.nome).trim_prefix("PORTA_ITEM_SAI_").left(1)})
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
		var d := Grade.DIRECOES[Construtor.fluxo_da_rot(e.rot)]
		b.pilha_max = int(r.get("pilha", 1))
		b.filtros = Fabrica.filtros_de(e)
		b.filtro = b.filtros[0] if b.filtros.size() == 1 else ""
		b.origem = origem_em(e.minimo - d * alcance_origem(e))
		b.destino = destino_em(e.minimo + d * (1 if r.has("alcance_max") else int(r.get("alcance", 1))))
		if b.destino == null and b.segurando == "":
			b.estado = Braco.Estado.ESPERANDO_ITEM


## Até onde o braço alcança atrás (a origem): o fixo do modelo ou, no braço quântico ("alcance_max"), o escolhido no
## painel (campo "alcance" da estrutura, 1 a alcance_max); a frente dele é sempre o tile vizinho.
static func alcance_origem(e: Dictionary) -> int:
	var r: Dictionary = Registro.estruturas.get(e.nome, {})
	if r.has("alcance_max"):
		return clampi(int(e.get("alcance", r.get("alcance", 1))), 1, int(r.alcance_max))
	return int(r.get("alcance", 1))


## Itens que o braço pega. O Braço com filtro escolhe até `filtro_max` (estruturas.json); os outros braços pegam o
## que o destino aceitar (Auto) — filtro que um braço comum já tinha de salvo antigo continua valendo.
static func filtros_de(e: Dictionary) -> Array:
	var fl: Array = e.get("filtros", [])
	var mx := int(Registro.estruturas.get(e.nome, {}).get("filtro_max", 0))
	return fl.slice(0, mx) if mx > 0 and fl.size() > mx else fl


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
		return _NoBau.new(baus[id], capacidade_bau(id), um_tipo(id))
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
		return _NoBau.new(baus[id], capacidade_bau(id), um_tipo(id))
	if estoques.has(id):
		return _NaEstacao.new(estoques[id])
	if Registro.estruturas.get(nome, {}).get("grupo", "") == "defesa":      # torre de energia e metralhadora
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


## Põe um item de combustível no estoque de fogo (fornalha/gerador). A poluição de quem queima segue a média do
## que está guardado, pesada pelos MJ (`poluicao_queima` em itens.json: briquete 0,7 = −30%; sem campo = 1).
func por_combustivel(id: int, item: String) -> void:
	var mj := valor_combustivel(item)
	var antes := float(combustivel.get(id, 0.0))
	var f_antes := float(fator_fogo.get(id, 1.0))
	var f_item := float(Registro.itens.get(item, {}).get("poluicao_queima", 1.0))
	combustivel[id] = antes + mj
	fator_fogo[id] = (f_antes * antes + f_item * mj) / maxf(antes + mj, 1e-6)


## Melhorias pesquisadas que mudam números das máquinas: produtividade de mineração na broca e no extrator.
## Barato de conferir a cada tick (só refaz quando a lista de concluídas muda ou as máquinas mudam).
func _aplicar_melhorias() -> void:
	var assin := "%d|%d|%s" % [maquinas.size(), mapa.versao, pesquisa.assinatura() if pesquisa != null else ""]
	if assin == _melhorias_de:
		return
	_melhorias_de = assin
	var prod := pesquisa.bonus("produtividade_mineracao") if pesquisa != null else 0.0
	# filtro que devolve água (pesquisa filtro_agua_limpa): a mesma limpeza, soltando água limpa pelo cano
	var filtro := "filtrar_agua_limpa" if pesquisa != null and pesquisa.receita_liberada("filtrar_agua_limpa") else "filtrar_agua"
	for id in maquinas:
		var tipo: String = Registro.estruturas.get(mapa.estruturas[id].nome, {}).get("maquina", "") if mapa.estruturas.has(id) else ""
		(maquinas[id] as Maquina).produtividade = prod if tipo in ["broca", "extrator"] else 0.0
		if tipo == "filtro" and maquinas[id].receita_id != filtro:
			maquinas[id].definir_receita(filtro, Registro.receitas[filtro])


# ------------------------------------------------------------------ tick
func tick(dt: float) -> void:
	passos += 1
	_aplicar_melhorias()
	while not juncoes.is_empty() and passos - int(juncoes[0].passo) > 6:
		juncoes.pop_front()
	emissao.clear()
	_tick_comparadores()
	for id in _membros:
		var mb: Dictionary = _membros[id]
		if mb.livre:
			mb.kw = kw_de(id)                   # renovável: rende conforme o sol/vento de agora
		elif mb.kw < 0.0:
			mb.combustivel_mj = combustivel.get(id, 0.0)
		if carga_torre.has(id):                 # torre: puxa da rede só enquanto não está cheia
			var cap := carga_max(id)
			mb.kw = kw_de(id) if float(carga_torre[id]) < cap - 1e-4 else 0.0
		elif _comandados.has(id) and not mb.livre and mb.kw >= 0.0 and mb.acum_cap <= 0.0:
			mb.kw = kw_de(id)                   # comparador ligou/desligou: o consumo acompanha
	for g in _trechos.size():                   # trens elétricos puxando do trilho energizado
		var ligados: Array = _trechos[g].filter(func(k): return _membros.has(k))
		var extra := float(demanda_trilho.get(g, 0.0)) / maxf(ligados.size(), 1)
		for k in ligados:
			_membros[k].kw = kw_de(k) + extra
	demanda_trilho.clear()
	rede.tick(dt)
	for id in carga_torre:
		if _membros.has(id) and float(_membros[id].kw) > 0.0:
			var cap := carga_max(id)
			carga_torre[id] = minf(cap, float(carga_torre[id]) + float(_membros[id].kw) * rede.satisfacao(id) * dt / 1000.0)
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
			energia_rede[id] = en
			var o: Object = maquinas.get(id, bracos.get(id))
			if o != null:
				o.set("energia", en)
			elif laboratorios.has(id):
				laboratorios[id].energia = en
	for id in maquinas:
		var m: Maquina = maquinas[id]
		if combustivel.has(id):
			m.energia = 1.0 if combustivel[id] > 0.0 and ligada(id) else 0.0
		match m.receita_id:
			"coletar_chuva":
				m.clima = float(chuva_maq.get(id, chuva)) if ligada(id) else 0.0
			"condensar_neblina":
				m.clima = neblina
			"borrifar_agua":
				continue                        # supressor: o ambiente decide quando borrifa (há fogo no raio?)
			"carregar_cristal":                 # captador: só trabalha quando um raio cai nele (Raios)
				var t := float(raio_em.get(id, 0.0))
				if t > 0.0:
					raio_em[id] = t - dt
					m.estado = Maquina.Estado.TRABALHANDO
				else:
					raio_em.erase(id)
					m.estado = Maquina.Estado.PRONTIDAO if m.pronta() else (Maquina.Estado.SAIDA_CHEIA if m.saida_cheia() else Maquina.Estado.SEM_INSUMO)
				continue
		m.tick(dt)
		if m.estado == Maquina.Estado.TRABALHANDO:
			_emitir(id, dt * m.energia)
			if combustivel.has(id):
				combustivel[id] = maxf(0.0, combustivel[id] - FOGO_KW / 1000.0 * dt)
	_tick_fluidos(dt)
	_tick_estacoes_fluido(dt)
	_tick_valvulas(dt)
	for id in distribuidores:
		var d: Dictionary = distribuidores[id]
		var saidas: Array = _saidas_dist.get(id, [])
		if d.buffer.is_empty() or saidas.is_empty():
			continue
		# divisor reparte em rodízio; junção tem uma saída só; divisor com filtro escolhe pelo item e pela prioridade
		for k in ordem_saidas(id, d.buffer[0], saidas, int(d.vez)):
			var s: Dictionary = saidas[k]
			var est: EsteiraCaminho = s.caminho.esteira
			var ok := est.inserir_na_entrada(d.buffer[0]) if s.idx == 0 else est.inserir_em(d.buffer[0], s.caminho.esteira.comprimento - s.idx - 0.5)
			if ok:
				d.buffer.pop_front()
				d.vez = (k + 1) % saidas.size()
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
		if pesquisa == null or pesquisa.ativa == "" or not lab_tem_unidade(lab) or lab.energia <= 0.0:
			continue
		lab.t += dt * lab.energia
		if lab.t >= pesquisa.tempo_por_pacote():
			lab.t = 0.0
			for t in pesquisa.tipos_ativa():          # uma unidade: 1 pacote de cada tipo
				lab.pacotes[t] = int(lab.pacotes[t]) - 1
			var fim := pesquisa.avancar()
			if fim != "":
				concluidas.append(fim)
	for id in bracos:
		bracos[id].tick(dt)
	for s in _sens_esteira:                     # sensor de esteira: quantos estavam além da marca antes de andar
		var est: EsteiraCaminho = caminhos[s.caminho].esteira
		s.antes = est.a_frente(s.marca)
		s.saidos = est.saidos
	for c in caminhos:
		c.esteira.tick(dt)
	_tick_sensores(dt)


## Em que ordem o distribuidor tenta as saídas (índices de `saidas`) para `item`. Rodízio a partir de `vez`; no
## divisor com filtro (opções guardadas na estrutura: filtro_item, saida_filtro, prioridade — lados N/L/O do modelo):
## o item filtrado só sai pela saída do filtro (espera se ela estiver cheia); o resto nunca vai por ela e tenta
## primeiro a saída de prioridade, depois as outras em rodízio.
func ordem_saidas(id: int, item: String, saidas: Array, vez: int) -> Array[int]:
	var n := saidas.size()
	var roda: Array[int] = []
	for t in n:
		roda.append((vez + t) % n)
	var e: Dictionary = mapa.estruturas.get(id, {})
	if e.get("nome", "") != "divisor_filtro":
		return roda
	var filtro: String = e.get("filtro_item", "")
	var lado_f: String = e.get("saida_filtro", "L")
	var prio: String = e.get("prioridade", "")
	var out: Array[int] = []
	if filtro != "" and item == filtro:
		for k in roda:
			if saidas[k].lado == lado_f:
				out.append(k)
		return out
	for k in roda:
		if filtro != "" and saidas[k].lado == lado_f:
			continue
		if prio != "" and saidas[k].lado == prio:
			out.push_front(k)
		else:
			out.append(k)
	return out


## O laboratório tem 1 pacote de cada tipo que a pesquisa ativa pede?
func lab_tem_unidade(lab: Dictionary) -> bool:
	for t in pesquisa.tipos_ativa():
		if int(lab.pacotes.get(t, 0)) <= 0:
			return false
	return true


## Pacotes que o laboratório aceita: o básico sempre; os outros quando a pesquisa ativa pede ou quando a receita
## do pacote já está liberada (dá para estocar antes de escolher a próxima pesquisa).
func lab_aceita(lab: Dictionary, item: String) -> bool:
	var ok := item == "pacote_pesquisa" or (pesquisa != null and (item in pesquisa.tipos_ativa() or pesquisa.pacote_liberado(item)))
	return ok and int(lab.pacotes.get(item, 0)) < LAB_MAX


## Salvos antigos guardavam só um número (pacotes básicos).
static func _lab_normalizar(lab: Dictionary) -> void:
	if not lab.pacotes is Dictionary:
		lab.pacotes = {"pacote_pesquisa": int(lab.pacotes)} if int(lab.pacotes) > 0 else {}


## Pontos de poluição: `poluicao` de estruturas.json é por minuto de trabalho.
func _emitir(id: int, segundos: float) -> void:
	var nome: String = mapa.estruturas[id].nome
	var p := float(Registro.estruturas.get(nome, {}).get("poluicao", 0.0)) * float(fator_fogo.get(id, 1.0))
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
		if nome.begins_with("cano") or nome == "tanque" or nome == "sensor_tanque":
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
		var par := par_subterraneo(id)
		if par >= 0:
			pai[raiz.call(id)] = raiz.call(par)
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
	_pontas_fluido = pontas
	# máquinas com porta de fluido encostada num cano que abre para elas
	for id in maquinas:
		for p in _portas(id):
			if p.tipo != "FLUIDO":
				continue
			var cano: int = pontas.get("%s|%s" % [p.tile_fora, -p.dir], -1)
			if cano >= 0:
				_ligacoes_fluido.append({"id": id, "io": p.io, "rede": _rede_do[cano]})
	# estações (vagão-tanque): a bomba de estação encosta na estação pelo lado de trás (o do braço de carga) e liga o
	# tanque dela à rede do cano que encosta na boca da frente da bomba (sem cano, a bomba fica sem rede)
	_estacoes_fluido.clear()
	for id in mapa.estruturas:
		if mapa.estruturas[id].nome != "bomba_estacao":
			continue
		for p in _portas(id):
			if p.tipo != "FLUIDO":
				continue
			var est: int = mapa.tiles.get(p.tile_dentro - p.dir, -1)
			if est < 0 or not mapa.estruturas.has(est) or mapa.estruturas[est].nome != "estacao":
				continue
			var cano: int = pontas.get("%s|%s" % [p.tile_fora, -p.dir], -1)
			_estacoes_fluido.append({"id": est, "rede": _rede_do[cano] if cano >= 0 else -1, "bomba": id})


## Tanque da estação (vagão-tanque): {modo: "desligado" | "carregar" | "descarregar", f, qtd}. Cria se faltar
## (estação de salvo antigo).
static func tanque_estacao(es: Dictionary) -> Dictionary:
	if not es.has("fluido"):
		es["fluido"] = {"modo": "desligado", "f": "", "qtd": 0.0}
	return es.fluido


## Estações com bomba de estação encostada (o painel da estação mostra o modo só nelas).
func estacao_tem_bomba(id: int) -> bool:
	return _estacoes_fluido.any(func(l): return l.id == id)


## A bomba de estação moveu fluido no último tick? (o desenho toca a animação dela)
func bomba_ativa(id: int) -> bool:
	return bool(bombeando.get(id, false))


## Modo "carregar": a bomba puxa da rede para o tanque da estação (o trem enche ao chegar); "descarregar": o tanque
## (enchido pelo trem) volta para a rede. Tanque em estruturas.json (estacao.tanque_fluido); vazão na bomba de
## estação (bomba_estacao.vazao × energia dela: sem energia ou desligada não bombeia).
func _tick_estacoes_fluido(dt: float) -> void:
	var cap := float(Registro.estruturas.get("estacao", {}).get("tanque_fluido", 25000.0))
	var vaz0 := float(Registro.estruturas.get("bomba_estacao", {}).get("vazao", 1000.0)) * dt
	bombeando.clear()
	for l in _estacoes_fluido:
		if not estoques.has(l.id) or l.rede < 0:
			continue
		var vaz := vaz0 * (energia(l.bomba) if ligada(l.bomba) else 0.0)
		if vaz <= 0.0:
			continue
		var tq := tanque_estacao(estoques[l.id])
		var rede: Dictionary = redes_fluido[l.rede]
		var antes := float(tq.qtd)
		match String(tq.get("modo", "desligado")):
			"carregar":
				if rede.qtd > 0.0 and (tq.f == "" or tq.f == rede.fluido):
					var vem := minf(minf(float(rede.qtd), vaz), cap - float(tq.qtd))
					if vem > 0.0:
						tq.f = rede.fluido
						tq.qtd = float(tq.qtd) + vem
						rede.qtd -= vem
			"descarregar":
				if float(tq.qtd) > 0.0 and (rede.fluido == "" or rede.fluido == tq.f):
					var vai := minf(minf(float(tq.qtd), vaz), float(rede.cap) - float(rede.qtd))
					if vai > 0.0:
						rede.fluido = tq.f
						rede.qtd += vai
						tq.qtd = float(tq.qtd) - vai
		if absf(float(tq.qtd) - antes) > 1e-6:
			bombeando[l.bomba] = true
		if float(tq.qtd) <= 0.001:
			tq.qtd = 0.0
			tq.f = ""
		if rede.qtd <= 0.001:
			rede.qtd = 0.0
			rede.fluido = ""


## Cano subterrâneo: a entrada liga na primeira saída alinhada à frente (mesma rotação), até `alcance` tiles — o
## fluido passa por baixo da terra (os tiles do meio ficam livres). -1 se não tem par.
func par_subterraneo(id: int) -> int:
	var e: Dictionary = mapa.estruturas[id]
	if e.nome != "cano_subterraneo_entrada":
		return -1
	var d := Construtor.fluxo_da_rot(e.rot)
	for i in range(1, int(Registro.estruturas.get(e.nome, {}).get("alcance", 10)) + 1):
		var o: int = mapa.tiles.get(Vector2i(e.minimo) + Grade.DIRECOES[d] * i, -1)
		if o >= 0 and mapa.estruturas[o].nome == "cano_subterraneo_saida" and int(mapa.estruturas[o].rot) == int(e.rot):
			return o
	return -1


## Saída de fluido de máquina cuja receita não solta fluido vira 2ª entrada (refinador com resina: seiva por uma
## boca, água pela outra — cada rede leva um fluido só). Água limpa serve onde a receita pede água.
func _tick_fluidos(dt: float) -> void:
	for l in _ligacoes_fluido:
		var rede: Dictionary = redes_fluido[l.rede]
		var m: Maquina = maquinas[l.id]
		var sai_fluido: Dictionary = m.receita.get("saidas_fluido", {})
		if l.io == "SAI" and not sai_fluido.is_empty():
			for f in sai_fluido:
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
				if Registro.fluido_serve(rede.fluido, f) and rede.qtd > 0.0:
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


# ------------------------------------------------------------------ rede lógica
## Sensor de esteira: a cabeça olha o tile da frente (só esteira no chão). Comparador: os vizinhos que ele comanda
## são as estruturas dos 4 tiles encostados. Válvula: duas redes de cano (a da boca de entrada e a da saída).
func _montar_logica() -> void:
	_sens_esteira.clear()
	_comparadores.clear()
	_comandados.clear()
	_valvulas.clear()
	for id in sensores.keys():
		if not mapa.estruturas.has(id):
			sensores.erase(id)
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		match e.nome:
			"sensor_esteira":
				if not sensores.has(id):
					sensores[id] = {"total": 0, "janela": [], "seg": 0, "t": 0.0}
				var t: Vector2i = e.minimo + Grade.DIRECOES[Construtor.fluxo_da_rot(e.rot)]
				if _no_tile.has(t):
					var a: Array = _no_tile[t]
					_sens_esteira.append({"id": id, "caminho": a[0], "marca": caminhos[a[0]].esteira.comprimento - a[1] - 0.5,
							"antes": 0, "saidos": 0})
			"comparador":
				var viz: Array[int] = []
				for d in Grade.DIRECOES:
					var o: int = mapa.tiles.get(e.minimo + d, -1)
					if o >= 0 and o != id and not viz.has(o) and mapa.estruturas.has(o) and mapa.estruturas[o].nome != "comparador":
						viz.append(o)
						_comandados[o] = true
				_comparadores.append({"id": id, "vizinhos": viz})
			"valvula":
				var redes := {}
				for p in _portas(id):
					var cano: int = _pontas_fluido.get("%s|%s" % [p.tile_fora, -p.dir], -1)
					if cano >= 0 and _rede_do.has(cano):
						redes[p.io] = _rede_do[cano]
				_valvulas.append({"id": id, "ent": redes.get("ENT", -1), "sai": redes.get("SAI", -1)})


## Valor que o sensor manda pelo canal: sensor de esteira = itens por minuto (média dos últimos `janela_s` s);
## sensor de tanque = nível da rede dele em % (0–100). -1 se não é sensor.
func valor_sensor(id: int) -> float:
	if not mapa.estruturas.has(id):
		return -1.0
	match mapa.estruturas[id].nome:
		"sensor_esteira":
			var s: Dictionary = sensores.get(id, {})
			var soma := 0
			for n in s.get("janela", []):
				soma += int(n)
			var jan := float(Registro.estruturas.get("sensor_esteira", {}).get("janela_s", 10))
			return float(soma) * 60.0 / jan
		"sensor_tanque":
			var r := rede_de(id)
			return 100.0 * float(r.qtd) / float(r.cap) if not r.is_empty() and float(r.cap) > 0.0 else 0.0
	return -1.0


static func canal_de(e: Dictionary) -> String:
	return String(e.get("canal", "A"))


## Condição do comparador agora (o canal dele contra o número escolhido).
func condicao_comparador(id: int) -> bool:
	var e: Dictionary = mapa.estruturas[id]
	var v := float(canais.get(canal_de(e), 0.0))
	var n := float(e.get("numero", 50))
	return v < n if String(e.get("op", ">")) == "<" else v > n


func _tick_comparadores() -> void:
	canais.clear()
	for c in CANAIS:
		canais[c] = 0.0
	for id in mapa.estruturas:
		var nome: String = mapa.estruturas[id].nome
		if nome == "sensor_esteira" or nome == "sensor_tanque":
			var k := canal_de(mapa.estruturas[id])
			canais[k] = float(canais.get(k, 0.0)) + valor_sensor(id)
	logica_off.clear()
	for c in _comparadores:
		if not mapa.estruturas.has(c.id) or mapa.estruturas[c.id].get("desligada", false):
			continue                            # comparador desligado não manda em ninguém
		if not condicao_comparador(c.id):
			for v in c.vizinhos:
				logica_off[v] = true


func _tick_sensores(dt: float) -> void:
	for s in _sens_esteira:
		var est: EsteiraCaminho = caminhos[s.caminho].esteira
		var passou := maxi(0, est.a_frente(s.marca) - int(s.antes) + est.saidos - int(s.saidos))
		var sd: Dictionary = sensores[s.id]
		sd.total = int(sd.total) + passou
		sd.seg = int(sd.seg) + passou
	var jan := int(Registro.estruturas.get("sensor_esteira", {}).get("janela_s", 10))
	for id in sensores:
		var sd: Dictionary = sensores[id]
		sd.t = float(sd.t) + dt
		while float(sd.t) >= 1.0:
			sd.t = float(sd.t) - 1.0
			(sd.janela as Array).append(int(sd.seg))
			sd.seg = 0
			while (sd.janela as Array).size() > jan:
				(sd.janela as Array).pop_front()


## O sensor de esteira contou item nos últimos 2 s? (o desenho anima a cabeça)
func sensor_contando(id: int) -> bool:
	var j: Array = sensores.get(id, {}).get("janela", [])
	return int(sensores.get(id, {}).get("seg", 0)) > 0 or (not j.is_empty() and int(j[-1]) > 0)


## Válvula: passa da rede de entrada para a de saída (vazão de estruturas.json) quando ligada (pelo jogador e pelo
## comparador) e a condição dela vale: "acima" = entrada acima do nível, "abaixo" = saída abaixo do nível,
## "sempre" = aberta. Um fluido só de cada lado.
func valvula_abre(id: int) -> bool:
	var v: Dictionary = {}
	for x in _valvulas:
		if x.id == id:
			v = x
	if v.is_empty() or v.ent < 0 or v.sai < 0 or not ligada(id):
		return false
	var e: Dictionary = mapa.estruturas[id]
	var nivel := float(e.get("nivel_valvula", 50)) / 100.0
	var ent: Dictionary = redes_fluido[v.ent]
	var sai: Dictionary = redes_fluido[v.sai]
	match String(e.get("modo_valvula", "acima")):
		"acima":
			return float(ent.cap) > 0.0 and float(ent.qtd) / float(ent.cap) > nivel
		"abaixo":
			return float(sai.cap) > 0.0 and float(sai.qtd) / float(sai.cap) < nivel
	return true


func _tick_valvulas(dt: float) -> void:
	valvula_passou.clear()
	var vaz := float(Registro.estruturas.get("valvula", {}).get("vazao", 1000.0)) * dt
	for v in _valvulas:
		if v.ent == v.sai or not valvula_abre(v.id):
			continue
		var ent: Dictionary = redes_fluido[v.ent]
		var sai: Dictionary = redes_fluido[v.sai]
		if float(ent.qtd) <= 0.0 or (sai.fluido != "" and sai.fluido != ent.fluido):
			continue
		var e: Dictionary = mapa.estruturas[v.id]
		var limite := float(sai.cap) - float(sai.qtd)
		if String(e.get("modo_valvula", "acima")) == "acima":     # não deixa a entrada cair abaixo do nível
			limite = minf(limite, float(ent.qtd) - float(ent.cap) * float(e.get("nivel_valvula", 50)) / 100.0)
		elif String(e.get("modo_valvula", "")) == "abaixo":       # nem encher a saída além dele
			limite = minf(limite, float(sai.cap) * float(e.get("nivel_valvula", 50)) / 100.0 - float(sai.qtd))
		var vai := minf(minf(vaz, float(ent.qtd)), limite)
		if vai <= 0.0:
			continue
		sai.fluido = ent.fluido
		sai.qtd = float(sai.qtd) + vai
		ent.qtd = float(ent.qtd) - vai
		if float(ent.qtd) <= 0.001:
			ent.qtd = 0.0
			ent.fluido = ""
		valvula_passou[v.id] = true


# ------------------------------------------------------------------ salvamento
func estado() -> Dictionary:
	var maq := {}
	for id in maquinas:
		var m: Maquina = maquinas[id]
		maq[id] = {"receita": m.receita_id, "entradas": m.entradas, "saidas": m.saidas, "progresso": m.progresso,
				"produzidos": m.produzidos, "fluidos": m.fluidos, "extra": m.extra}
	var br := {}
	for id in bracos:
		var b: Braco = bracos[id]
		br[id] = {"segurando": b.segurando, "estado": b.estado, "t": b.t, "qtd": b.qtd}
	return {"maquinas": maq, "bracos": br, "baus": baus, "combustivel": combustivel, "fator_fogo": fator_fogo, "laboratorios": laboratorios, "acumulado": acumulado,
			"distribuidores": distribuidores, "fluidos": _guardar_fluidos(), "itens": _guardar_itens(), "carga_torre": carga_torre,
			"sensores": sensores}


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
		m.extra = float(s.get("extra", 0.0))
		m.acordar()
	for id in d.get("bracos", {}):
		if bracos.has(id):
			var b: Braco = bracos[id]
			b.segurando = d.bracos[id].segurando
			b.qtd = int(d.bracos[id].get("qtd", 1 if b.segurando != "" else 0))
			b.estado = d.bracos[id].estado
			b.t = d.bracos[id].t
	for id in d.get("baus", {}):
		if baus.has(id):
			baus[id].merge(d.baus[id], true)
	for id in d.get("combustivel", {}):
		combustivel[id] = d.combustivel[id]
	for id in d.get("fator_fogo", {}):
		if combustivel.has(id):
			fator_fogo[id] = d.fator_fogo[id]
	for id in d.get("carga_torre", {}):
		if carga_torre.has(id):
			carga_torre[id] = d.carga_torre[id]
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
			_lab_normalizar(laboratorios[id])
	for id in d.get("sensores", {}):
		if sensores.has(id):
			sensores[id].merge(d.sensores[id], true)
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
			f.por_combustivel(id, i)
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
			if int(m.saidas[item]) > 0 and not item in m.retem and aceito.call(item):
				return m.pegar_para_braco(item)
		return ""
	func devolver(i: String) -> void:
		m.saidas[i] = int(m.saidas.get(i, 0)) + 1


class _NoBau:
	var b: Dictionary
	var cap: int
	var unico := false            ## silo de granel: só um tipo de item
	func _init(p_b: Dictionary, p_cap: int, p_unico := false) -> void:
		b = p_b
		cap = p_cap
		unico = p_unico
	func _total() -> int:
		var n := 0
		for k in b: n += int(b[k])
		return n
	func aceita(i: String) -> bool:
		if unico:
			var t := Fabrica.tipo_guardado(b)
			if t != "" and t != i:
				return false
		return _total() < cap
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
	func aceita(i: String) -> bool:
		return f.mapa.estruturas.has(id) and i == Colonia.item_municao(f.mapa.estruturas[id].nome) \
				and f.torre_receber.is_valid() and (not f.torre_aceita.is_valid() or f.torre_aceita.call(id))
	func receber(i: String) -> bool:
		if not aceita(i): return false
		f.torre_receber.call(id, Colonia.tiros_por_item(f.mapa.estruturas[id].nome))
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
		f.por_combustivel(id, i)
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
	func aceita(i: String) -> bool: return f.lab_aceita(lab, i)
	func receber(i: String) -> bool:
		if not aceita(i): return false
		lab.pacotes[i] = int(lab.pacotes.get(i, 0)) + 1
		return true


class _NoDistribuidor:
	var d: Dictionary
	func _init(p: Dictionary) -> void: d = p
	func aceita(_i: String) -> bool: return d.buffer.size() < 2
	func receber(i: String) -> bool:
		if not aceita(i): return false
		d.buffer.append(i)
		return true
