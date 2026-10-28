extends Node3D
## Cena de demonstração: mundo procedural em streaming por chunks; mini-fábrica perto do spawn
## (extrator → esteira → braço → estação A → trem → estação B); a poluição dela se espalha, ninhos de aranha
## absorvem e mandam ataques; a torre defende; o jogador constrói (controles em interface/controle_construcao.gd).
## Argumentos: -- camera X Z DIST · acelerar N (tempo N×) · roteiro <nome> · clima <estado>
## Teste sem janela: godot --headless --path jogo --quit-after 600   (o jogo roda e sai)
## Roteiro visual automático: ... -- roteiro construir   (ver interface/roteiro_teste.gd)

const RAIO_MIN := 2                 ## chunks em volta do centro da câmera (cresce com o zoom, até RAIO_MAX)
const RAIO_MAX := 5
const SEMENTE := 1337               ## demonstração e testes; jogo novo sorteia a sua
const NUCLEO_EM := Vector2i(-1, -1)  ## núcleo 3×3 em volta do spawn (modo novo)

var gerador: GeradorMundo
var mapa: MapaOcupacao
var relogio := RelogioSim.new()
var chunks: Dictionary = {}
var fabrica: Fabrica
var _desenho_itens: DesenhoItens
var _fabrica_suja := false
var poluicao: Poluicao
var clima: Clima
var colonia: Colonia
var grafo := GrafoTrilhos.new()
var trens: Array[Trem] = []
var estoques: Dictionary = {}       ## id da estação → {enviar: {item: n}, recebido: {item: n}}
var _prox_trem := 1
var _poluiu_em: Dictionary = {}     ## id → instante (s) da última emissão: quem poluiu há pouco é alvo das aranhas
var _eventos: Array[Dictionary] = []
var _desenho_colonia: DesenhoColonia
var _desenho_trens: DesenhoTrens
var _desenho_poluicao: DesenhoPoluicao
var _visao: VisaoRecursos
var _fluxo: DesenhoFluxo
var _rotulos: Dictionary = {}       ## id da estação → Label3D
var _t_hud := 0.0
var _sel := {}                       ## selecionado: {trem: id} ou {estrutura: id}
var _relatorio := false              ## -- relatorio: imprime o estado a cada 30 s de jogo (para calibrar números)
var _t_rel := 0.0
var _tempo := 0.0
var modo := "demo"
var semente := SEMENTE
var inventario: Dictionary = {}     ## estoque do núcleo (o mesmo dicionário no Construtor e na Fabrica)
var pesquisa: Pesquisa
var pausa: MenuPausa
var _salvar_em := 0.0
var _autosalvar := true
var construtor: Construtor
var controle: ControleConstrucao
var _nos: Dictionary = {}           ## id da estrutura → Node3D (peças miúdas vão para _lotes)
var _lotes: DesenhoLotes
var _efeitos: Efeitos
var _fios: DesenhoFios

@onready var camera: CameraJogo = $Camera3D


func _ready() -> void:
	# câmera por argumento (fotos automáticas): -- camera <x> <z> <distância>
	var args := OS.get_cmdline_user_args()
	var i := args.find("camera")
	if i >= 0 and args.size() > i + 3:
		camera.alvo = Vector3(float(args[i + 1]), 0, float(args[i + 2]))
		camera.distancia = float(args[i + 3])
	camera.posicionar()
	_relatorio = args.has("relatorio")
	var ac := args.find("acelerar")
	if ac >= 0 and args.size() > ac + 1:
		Engine.time_scale = float(args[ac + 1])
	# modo da partida: o menu decide (Sessao); rodando a cena direto (testes), é a demonstração
	modo = Sessao.modo
	var dados := {}
	if modo == "continuar":
		dados = Salvamento.ler()
		modo = dados.get("modo", "novo") if not dados.is_empty() else "novo"
	_autosalvar = modo != "demo" and not args.has("roteiro") and not _relatorio
	if not dados.is_empty():
		semente = dados.semente
	elif modo == "novo":
		semente = randi() % 1000000
	gerador = GeradorMundo.new(semente)
	mapa = MapaOcupacao.new(gerador)
	DesenhoChunk.preparar(gerador)
	DesenhoChunk.aquecer()
	poluicao = Poluicao.new(gerador)
	clima = Clima.new(semente)
	colonia = Colonia.new(mapa, poluicao, semente)
	pesquisa = Pesquisa.new(modo == "demo")
	fabrica = Fabrica.new(mapa)
	fabrica.estoques = estoques
	fabrica.estoque_nucleo = inventario
	fabrica.pesquisa = pesquisa
	fabrica.torre_receber = func(id: int, n: int) -> void: colonia.carregar_torre(id, n)
	_lotes = DesenhoLotes.new()
	add_child(_lotes)
	_criar_construcao()
	construtor.cobrar = modo != "demo"
	construtor.inventario = inventario
	construtor.pesquisa = pesquisa
	colonia.destruir = func(id: int) -> void: _destruido(id)
	if not dados.is_empty():
		_carregar(dados)
	elif modo == "demo":
		_montar_fabrica()
	else:
		_comecar_novo()
	_criar_desenhos()
	pausa = MenuPausa.new()
	pausa.pode_salvar = modo != "demo"
	pausa.pediu_salvar.connect(salvar)
	add_child(pausa)
	_salvar_em = float(Sessao.config.autosalvar_s)
	Sessao.aplicar.call_deferred()
	Som.musica(true)
	var ci := args.find("clima")
	if ci >= 0 and args.size() > ci + 1:
		clima.forcar(args[ci + 1], true)
	_atualizar_chunks()
	var r := args.find("roteiro")
	if r >= 0 and args.size() > r + 1:
		var rt := RoteiroTeste.new()
		rt.roteiro = args[r + 1]
		rt.cena = self
		add_child(rt)


## Jogo novo: núcleo no spawn, kit inicial de itens, pesquisa do zero.
func _comecar_novo() -> void:
	for x in range(-4, 3):
		for y in range(-4, 3):
			mapa.limpar_obstaculo(NUCLEO_EM + Vector2i(x, y))
	_instanciar("nucleo", NUCLEO_EM, 0)
	inventario.merge(Registro.progressao.get("kit_inicial", {}))
	fabrica.reconstruir()
	camera.alvo = Grade.ponto_mundo(Vector2(NUCLEO_EM) + Vector2(1.5, 1.5))
	camera.posicionar()


## Estrutura derrubada pelas aranhas. Núcleo caído = derrota.
func _destruido(id: int) -> void:
	var era_nucleo: bool = mapa.estruturas.has(id) and mapa.estruturas[id].nome == "nucleo"
	sincronizar(construtor.destruir(id))
	if era_nucleo:
		Som.tocar("derrota")
		Salvamento.apagar()
		pausa.abrir(true)


# ------------------------------------------------------------------ salvar / carregar
func salvar() -> void:
	if modo == "demo":
		return
	var ok := Salvamento.gravar({"modo": modo, "semente": semente, "tempo": _tempo,
			"camera": [camera.alvo, camera.distancia, camera.angulo],
			"mapa": {"estruturas": mapa.estruturas, "limpos": mapa.limpos.keys(), "prox": mapa._prox_id},
			"fabrica": fabrica.estado(), "colonia": colonia.estado(), "poluicao": poluicao.valores, "clima": clima.estado(),
			"estoques": estoques, "inventario": inventario, "pesquisa": pesquisa.estado(),
			"trens": trens.map(func(t: Trem): return t.para_salvar()), "prox_trem": _prox_trem})
	if ok and is_instance_valid(controle):
		controle._avisar("Jogo salvo")


func _carregar(d: Dictionary) -> void:
	mapa.restaurar(d.mapa.estruturas, d.mapa.limpos, d.mapa.prox)
	inventario.merge(d.inventario, true)
	pesquisa.restaurar(d.pesquisa)
	for id in d.estoques:
		estoques[id] = d.estoques[id]
	poluicao.valores = d.poluicao
	if d.has("clima"):
		clima.restaurar(d.clima)
	colonia.restaurar(d.colonia)
	for id in mapa.estruturas:
		var nome: String = mapa.estruturas[id].nome
		if nome != "ninho_aranha" and nome != "pilar":
			_criar_no(id)
	for id in mapa.estruturas:
		if mapa.estruturas[id].nome == "muro_centro":
			_ligar_muro(mapa.estruturas[id].minimo)
	fabrica.restaurar(d.fabrica)
	_remontar_trilhos()
	for td in d.trens:
		var t := Trem.de_salvo(td, grafo)
		if t != null:
			trens.append(t)
	_prox_trem = d.prox_trem
	_tempo = d.tempo
	camera.alvo = d.camera[0]
	camera.distancia = d.camera[1]
	camera.angulo = d.camera[2]
	camera.posicionar()


func _notification(what: int) -> void:
	# fechar a janela / celular mandar o app para o fundo: salva antes
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED:
		if _autosalvar:
			salvar()


func abrir_pausa() -> void:
	pausa.abrir()


func abrir_pesquisa() -> void:
	_sel = {} if _sel.has("pesquisa") else {"pesquisa": true}
	_detalhe()


func _criar_desenhos() -> void:
	_desenho_colonia = DesenhoColonia.new()
	_desenho_colonia.colonia = colonia
	_desenho_colonia.mapa = mapa
	_desenho_colonia.animadores_torre = _animador
	add_child(_desenho_colonia)
	_desenho_trens = DesenhoTrens.new()
	add_child(_desenho_trens)
	_desenho_itens = DesenhoItens.new()
	_desenho_itens.fabrica = fabrica
	_desenho_itens.mapa = mapa
	add_child(_desenho_itens)
	_fios = DesenhoFios.new()
	_fios.mapa = mapa
	add_child(_fios)
	_efeitos = Efeitos.new()
	_efeitos.fabrica = fabrica
	_efeitos.mapa = mapa
	add_child(_efeitos)
	_desenho_poluicao = DesenhoPoluicao.new()
	_desenho_poluicao.poluicao = poluicao
	add_child(_desenho_poluicao)
	_fluxo = DesenhoFluxo.new()
	_fluxo.mapa = mapa
	add_child(_fluxo)
	_visao = VisaoRecursos.new()
	_visao.gerador = gerador
	_visao.mapa = mapa
	_visao.camera = camera
	_visao.areas_interface = func() -> Array[Rect2]: return controle.barra.areas_ocupadas()
	add_child(_visao)
	var dc := DesenhoClima.new()
	dc.clima = clima
	dc.camera = camera
	dc.ambiente = $Ambiente
	dc.sol = $Sol
	dc.fontes_calor = _fontes_calor
	add_child(dc)


func alternar_recursos() -> bool:
	return _visao.alternar()


func alternar_poluicao() -> bool:
	_desenho_poluicao.visible = not _desenho_poluicao.visible
	return _desenho_poluicao.visible


func _criar_construcao() -> void:
	construtor = Construtor.new(mapa)
	var fantasma := Fantasma.new()
	add_child(fantasma)
	var barra := BarraConstrucao.new()
	add_child(barra)
	controle = ControleConstrucao.new()
	add_child(controle)
	barra.liberado = func(nome: String) -> bool: return pesquisa == null or pesquisa.peca_liberada(nome)
	controle.configurar(construtor, camera, barra, fantasma, self)


# ------------------------------------------------------------------ mundo
## Streaming do mapa sem travar a câmera:
##  - quer os chunks no raio da vista + 1 de folga (pré-carrega antes de aparecer);
##  - gerar e calcular a malha vai para a fila de trabalho em segundo plano (até TAREFAS ao mesmo tempo, os mais
##    perto do centro primeiro);
##  - na linha principal só monta o que ficou pronto: 1 chunk por quadro;
##  - descarrega só quando passa 2 chunks da vista (ir e voltar não recarrega).
const TAREFAS := 3

var _fila_pronta: Dictionary = {}      ## chunk → dados prontos (escrito pelas tarefas de fundo)
var _em_preparo: Dictionary = {}       ## chunk → id da tarefa
var _trava := Mutex.new()


func _atualizar_chunks() -> void:
	var c := Grade.chunk_de(Grade.tile_de_mundo(camera.alvo))
	var raio := clampi(ceili(camera.distancia * 0.75 / Grade.TAM_CHUNK) + 1, RAIO_MIN, RAIO_MAX - (1 if OS.has_feature("mobile") else 0))
	# descarrega o que ficou bem para trás
	for k in chunks.keys():
		if maxi(absi(k.x - c.x), absi(k.y - c.y)) > raio + 2:
			chunks[k].queue_free()
			chunks.erase(k)
	# monta 1 chunk pronto por quadro (o mais perto)
	_trava.lock()
	var prontos := _fila_pronta.keys()
	_trava.unlock()
	if not prontos.is_empty():
		prontos.sort_custom(func(a, b): return (a - c).length_squared() < (b - c).length_squared())
		var k: Vector2i = prontos[0]
		_trava.lock()
		var dados: Dictionary = _fila_pronta[k]
		_fila_pronta.erase(k)
		_trava.unlock()
		WorkerThreadPool.wait_for_task_completion(_em_preparo[k])
		_em_preparo.erase(k)
		if maxi(absi(k.x - c.x), absi(k.y - c.y)) <= raio + 2:
			if chunks.has(k):
				chunks[k].queue_free()            # redesenho: troca o velho pelo novo
			colonia.descobrir_chunk(k)
			var d := DesenhoChunk.new()
			add_child(d)
			d.montar(dados, mapa)
			chunks[k] = d
	# encomenda os que faltam, do centro para fora
	if _em_preparo.size() >= TAREFAS:
		return
	var faltam: Array[Vector2i] = []
	for dx in range(-raio - 1, raio + 2):
		for dy in range(-raio - 1, raio + 2):
			var k := c + Vector2i(dx, dy)
			if not chunks.has(k) and not _em_preparo.has(k):
				faltam.append(k)
	faltam.sort_custom(func(a, b): return (a - c).length_squared() < (b - c).length_squared())
	for k in faltam.slice(0, TAREFAS - _em_preparo.size()):
		_encomendar(k)


func _encomendar(k: Vector2i) -> void:
	var g := gerador
	_em_preparo[k] = WorkerThreadPool.add_task(func():
		var dados := DesenhoChunk.preparar_dados(k, g)
		_trava.lock()
		_fila_pronta[k] = dados
		_trava.unlock())


## Redesenha um chunk já visível (obstáculo limpo ou devolvido): o novo é preparado no fundo e troca o velho.
func _redesenhar_chunk(k: Vector2i) -> void:
	if chunks.has(k) and not _em_preparo.has(k):
		_encomendar(k)


func _exit_tree() -> void:
	for k in _em_preparo:
		WorkerThreadPool.wait_for_task_completion(_em_preparo[k])


# ------------------------------------------------------------------ construção → desenho
## Desenha o que o Construtor mudou no mapa (relatório de executar/desfazer).
func sincronizar(rel: Dictionary) -> void:
	var muros := {}
	for e in rel.removidos:
		if _nos.has(e.id):
			_nos[e.id].queue_free()
			_nos.erase(e.id)
		_lotes.remover(e.id)
		if e.nome == "muro_centro":
			muros[e.minimo] = true
	for id in rel.colocados:
		_criar_no(id, true)
		if mapa.estruturas[id].nome == "muro_centro":
			muros[mapa.estruturas[id].minimo] = true
	var redesenhar := {}
	for l in rel.limpos + rel.restaurados:
		for t in l.tiles:
			redesenhar[Grade.chunk_de(t)] = true
	for k in redesenhar:
		_redesenhar_chunk(k)
	# piso de fábrica e objetos naturais debaixo de construção: só os chunks tocados (com 1 tile de margem)
	var tocados := {}
	var areas: Array = rel.removidos.duplicate()
	for id in rel.colocados:
		if mapa.estruturas.has(id):
			areas.append(mapa.estruturas[id])
	for e in areas:
		if e.nome == "pilar":
			continue
		for t in Grade.tiles_da_area(e.minimo, Registro.area(e.nome), e.rot):
			for d in [Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)]:
				tocados[Grade.chunk_de(t + d)] = true
	for k in tocados:
		if chunks.has(k) and not redesenhar.has(k):
			chunks[k].atualizar(mapa)
	var religar := {}
	for t in muros:
		for d in [Vector2i.ZERO] + Array(Grade.DIRECOES):
			religar[t + d] = true
	for t in religar:
		_ligar_muro(t)
	var malha_mudou := false
	for e in rel.removidos:
		malha_mudou = malha_mudou or _eh_ferrovia(e.nome)
	for id in rel.colocados:
		malha_mudou = malha_mudou or _eh_ferrovia(mapa.estruturas[id].nome)
	if malha_mudou:
		_remontar_trilhos()
	if not (rel.colocados.is_empty() and rel.removidos.is_empty()):
		_fabrica_suja = true                    # remonta uma vez no próximo tick (vários eventos no mesmo quadro)
	for t in rel.trens:
		if not criar_trem(t.tile):
			construtor.devolver("trem")
			controle._avisar("Não coube: o trem precisa de 12 m de trilho livre (bloco sem outro trem)")


## Nó visual de uma estrutura do mapa. `nova` = posta agora pelo jogador (anima a entrada; máquina parada até
## a simulação dela existir).
func _criar_no(id: int, nova := false) -> Node3D:
	var e: Dictionary = mapa.estruturas[id]
	if e.nome == "pilar":
		return _criar_pilar(id)
	var pos := Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot), e.get("nivel", 0) * 0.5)
	# rampa de descida: o mesmo modelo virado (a ponta alta fica atrás, de onde vem o item)
	var ang := Grade.angulo(e.rot) + (PI if e.get("desce", false) else 0.0)
	if DesenhoLotes.aceita(e.nome):
		_lotes.adicionar(id, e.nome, Transform3D(Basis(Vector3.UP, ang), pos))
		return null
	var cena: PackedScene = load(Registro.modelos[e.nome].modelo)
	var n: Node3D = cena.instantiate()
	add_child(n)
	Materiais.converter(n)
	n.position = pos
	n.rotation.y = ang
	if Registro.modelos[e.nome].get("partes", []).size() > 1:      # só quem tem peça móvel (esteira não)
		var a := Animador.new()
		a.ativo = not nova
		n.add_child(a)
	_nos[id] = n
	if nova:
		n.scale = Vector3(1.0, 0.2, 1.0)
		var tw := n.create_tween()
		tw.tween_property(n, "scale", Vector3.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	return n


## Pilar de esteira elevada no canto da grade: base + n segmentos de 0,5 m + topo (que segura a esteira).
func _criar_pilar(id: int) -> Node3D:
	var e: Dictionary = mapa.estruturas[id]
	var raiz := Node3D.new()
	raiz.position = Grade.ponto_mundo(Vector2(e.minimo))
	add_child(raiz)
	var k := EsteiraElevada.segmentos(e.altura)
	var pecas: Array = [["pilar_base", 0.0]]
	for i in k:
		pecas.append(["pilar_segmento", i * 0.5])
	pecas.append(["pilar_topo", k * 0.5])
	for p in pecas:
		var no: Node3D = (load(Registro.modelos[p[0]].modelo) as PackedScene).instantiate()
		no.position.y = p[1]
		raiz.add_child(no)
		Materiais.converter(no)
	_nos[id] = raiz
	return raiz


## Muro: o pilar do tile ganha um pano (muro_lado) para cada vizinho que também é muro.
func _ligar_muro(t: Vector2i) -> void:
	var id: int = mapa.tiles.get(t, -1)
	if id < 0 or mapa.estruturas[id].nome != "muro_centro" or not _nos.has(id):
		return
	var n: Node3D = _nos[id]
	for c in n.get_children():
		if c.has_meta("muro_lado"):
			n.remove_child(c)
			c.queue_free()
	for d in 4:
		var v: int = mapa.tiles.get(t + Grade.DIRECOES[d], -1)
		if v < 0 or mapa.estruturas[v].nome != "muro_centro":
			continue
		var lado: Node3D = (load(Registro.modelos["muro_lado"].modelo) as PackedScene).instantiate()
		lado.set_meta("muro_lado", d)
		n.add_child(lado)
		Materiais.converter(lado)
		lado.rotation.y = Grade.angulo(Construtor.rot_do_fluxo(d)) - n.rotation.y


# ------------------------------------------------------------------ trens
static func _eh_ferrovia(nome: String) -> bool:
	return nome.begins_with("trilho") or nome == "sinal_trem" or nome == "estacao"


## Remonta o grafo depois de mudança na malha; trem sem trilho embaixo some (descarrilou).
func _remontar_trilhos() -> void:
	grafo = GrafoTrilhos.de_mapa(mapa)
	for est in grafo.estacoes:
		if not estoques.has(est.estrutura):
			estoques[est.estrutura] = {"enviar": {}, "recebido": {}}
		if not _rotulos.has(est.estrutura):
			_rotulo_estacao(est.estrutura)
	for t in trens.duplicate():
		if not t.reancorar(grafo):
			trens.erase(t)
			_desenho_colonia._faiscas(Grade.ponto_mundo(t.ponto_em(t.s - t.comprimento() / 2.0).pos, 0.6), 50)


## Põe um trem (locomotiva + 2 vagões + locomotiva) no trilho reto do tile, com a cauda na ponta sul/oeste.
func criar_trem(tile: Vector2i) -> bool:
	var r := grafo.peca_no_ponto(Vector2(tile) + Vector2(0.5, 0.5), 0.1)
	if r.is_empty():
		return false
	var t := Trem.new(_prox_trem, grafo, ["locomotiva", "vagao_carga", "vagao_carga", "locomotiva"] as Array[String])
	if not t.colocar(r.peca, grafo.pecas[r.peca].a):
		return false
	_prox_trem += 1
	trens.append(t)
	return true


func _rotulo_estacao(id: int) -> void:
	var e: Dictionary = mapa.estruturas[id]
	var l := Label3D.new()
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.font_size = 30
	l.outline_size = 10
	l.fixed_size = true                 # mesmo tamanho na tela de perto ou de longe
	l.pixel_size = 0.0011
	l.no_depth_test = true
	l.position = Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot), 2.7)
	add_child(l)
	_rotulos[id] = l


func _atualizar_rotulos() -> void:
	for id in _rotulos.keys():
		if not estoques.has(id) or not mapa.estruturas.has(id):
			_rotulos[id].queue_free()
			_rotulos.erase(id)
			continue
		var es: Dictionary = estoques[id]
		var linhas: Array[String] = []
		var env := _soma(es.enviar)
		var rec := _soma(es.recebido)
		if env > 0: linhas.append("Para enviar: %d" % env)
		if rec > 0: linhas.append("Recebido: %d" % rec)
		_rotulos[id].text = "Estação %d" % _numero_estacao(id) + ("\n" + "\n".join(linhas) if not linhas.is_empty() else "")


static func _soma(d: Dictionary) -> int:
	var n := 0
	for k in d:
		n += int(d[k])
	return n




# ------------------------------------------------------------------ fábrica de demonstração
## Procura, em espiral, o lugar livre mais perto de `perto` (para a demo não cair em cima de árvore).
func _achar_lugar(nome: String, perto: Vector2i, rot := 0) -> Vector2i:
	for r in 12:
		for dx in range(-r, r + 1):
			for dy in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) == r and mapa.motivo_bloqueio(nome, perto + Vector2i(dx, dy), rot) == "":
					return perto + Vector2i(dx, dy)
	return perto


func _instanciar(nome: String, minimo: Vector2i, rot: int, procurar := false) -> Node3D:
	if procurar:
		minimo = _achar_lugar(nome, minimo, rot)
	# a demo limpa os obstáculos da área e de 1 tile em volta (no jogo, quem limpa é o jogador)
	var ar := Grade.area_girada(Registro.area(nome), rot)
	for dx in range(-1, ar.x + 1):
		for dy in range(-1, ar.y + 1):
			mapa.limpar_obstaculo(minimo + Vector2i(dx, dy))
	var motivo := mapa.motivo_bloqueio(nome, minimo, rot)
	var id := mapa.colocar(nome, minimo, rot)
	if id < 0:
		push_warning("demo: não coube %s em %s (%s)" % [nome, minimo, motivo])
		return null
	return _criar_no(id)


## Igual a _instanciar, mas devolve o id da estrutura (−1 se não coube).
func _instanciar_id(nome: String, minimo: Vector2i, rot: int, procurar := false) -> int:
	var id := mapa._prox_id
	_instanciar(nome, minimo, rot, procurar)
	return id if mapa.estruturas.has(id) else -1


## Mini-fábrica pronta, montada só com peças do mapa — quem faz funcionar é a mesma Fabrica que roda o que o
## jogador constrói: extrator → esteira → braço → estação A → trem → estação B; gerador + postes; torre abastecida
## por braço a partir de um baú de munição.
func _montar_fabrica() -> void:
	_instanciar("extrator_cristal", Vector2i(14, 4), 0)
	var porta := Grade.porta_no_mundo(Registro.estruturas["extrator_cristal"].portas[0], Vector2i(14, 4), Vector2i(3, 3), 0)
	var t0: Vector2i = porta.tile_fora
	var tb := t0 + Vector2i(0, -5)
	for k in 5:
		mapa.limpar_obstaculo(t0 + Vector2i(0, -k))
	sincronizar(construtor.executar(construtor.plano_linha("esteira", t0, t0 + Vector2i(0, -4), 2)))
	_instanciar("braco", tb, 2)
	_instanciar("estacao", tb + Vector2i(-1, -3), 0)
	# ferrovia norte–sul encostada a oeste das estações: A (carrega) e B, 18 tiles ao sul
	var xl := tb.x - 2
	_instanciar("trilho_fim", Vector2i(xl, tb.y + 5), 0)
	for y in range(tb.y - 26, tb.y + 5):
		_instanciar("trilho_reto", Vector2i(xl, y), 0)
	_instanciar("trilho_fim", Vector2i(xl, tb.y - 27), 2)
	_instanciar("estacao", tb + Vector2i(-1, -22), 0)
	_remontar_trilhos()
	criar_trem(Vector2i(xl, tb.y - 14))
	# energia: gerador (com carvão para começar) e postes até o extrator e os braços
	var g := _instanciar_id("gerador", Vector2i(8, 6), 0)
	for p in [Vector2i(11, 6), Vector2i(17, 3), Vector2i(17, -2)]:
		_instanciar("poste_energia", p, 0)
	# defesa: torre com braço trazendo munição de um baú; outra torre só com a munição inicial
	_instanciar("torre_defesa", Vector2i(18, -6), 0)
	var bau := _instanciar_id("bau", Vector2i(19, -3), 0)
	_instanciar("braco", Vector2i(19, -4), 2)
	_instanciar("torre_defesa", Vector2i(4, -2), 0, true)
	_instanciar("fornalha", Vector2i(9, -4), 0, true)
	fabrica.reconstruir()
	_fabrica_suja = false
	construtor._historico.clear()                 # a demo não entra no desfazer do jogador
	if g >= 0:
		fabrica.combustivel[g] = 300.0
	if bau >= 0:
		fabrica.baus[bau]["municao"] = 30


# ------------------------------------------------------------------ simulação
func _process(delta: float) -> void:
	if _autosalvar:
		_salvar_em -= delta / maxf(Engine.time_scale, 0.001)
		if _salvar_em <= 0.0:
			_salvar_em = float(Sessao.config.autosalvar_s)
			salvar()
	for i in relogio.avancar(delta):
		_tick_mundo(relogio.dt())
	_animar_estruturas()
	# modo construção (peça na mão): caminho e sentido das esteiras em destaque
	_fluxo.ligado = controle != null and controle.peca != ""
	# letreiros só de perto (a névoa por zoom e clima fica no DesenhoClima)
	($Sol as DirectionalLight3D).directional_shadow_max_distance = clampf(camera.distancia * 1.6, 30.0, 110.0)
	for l in _rotulos.values():
		l.visible = camera.distancia < 75.0 and not _visao.ligada     # na visão de recursos só os nomes do mapa
	_desenho_trens.sincronizar(trens)
	for ev in _eventos:
		match ev.tipo:
			"destruida":
				_efeitos.marcar_destruicao(ev.centro, Registro.area(ev.nome).x)
				Som.tocar("aranha_morre", Grade.ponto_mundo(ev.centro), -4.0)
			"tiro":
				Som.tocar("tiro", Grade.ponto_mundo(ev.de, 1.2), -6.0)
			"aranha_morta":
				Som.tocar("aranha_morre", Grade.ponto_mundo(ev.pos))
			"ataque":
				Som.tocar("alerta")
	_desenho_colonia.atualizar(_eventos, delta)
	_eventos.clear()
	_t_hud -= delta
	if _t_hud <= 0.0:
		_t_hud = 0.25
		_atualizar_rotulos()
		_hud()
	_atualizar_chunks()


## Onde a neblina abre: máquinas queimando/trabalhando (as que poluíram neste passo) e trens. (x, z do mundo, raio)
func _fontes_calor() -> Array:
	var r: Array = []
	for id in fabrica.emissao:
		var e: Dictionary = mapa.estruturas.get(id, {})
		if e.is_empty():
			continue
		var p := Grade.ponto_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot))
		r.append(Vector3(p.x, p.z, 3.0 + 0.8 * maxf(e.area.x, e.area.y)))
	for t in trens:
		var p := Grade.ponto_mundo(t.ponto_em(t.s).pos)
		r.append(Vector3(p.x, p.z, 4.0))
	return r


## Animação segue a simulação: máquina mexe só trabalhando; braço pela fase do ciclo.
func _animar_estruturas() -> void:
	for id in fabrica.maquinas:
		var a := _animador(id)
		if a != null:
			a.ativo = fabrica.maquinas[id].estado == Maquina.Estado.TRABALHANDO
	for id in fabrica.bracos:
		var a := _animador(id)
		if a != null:
			a.fase_braco = fabrica.bracos[id].fase()


func _animador(id: int) -> Animador:
	var n: Node3D = _nos.get(id)
	if n == null:
		return null
	for c in n.get_children():
		if c is Animador:
			return c
	return null


## Poluição, aranhas e trens (rodam mesmo se a mini-fábrica parar).
func _tick_mundo(dt: float) -> void:
	if _fabrica_suja:
		fabrica.reconstruir()
		_fabrica_suja = false
	fabrica.tick(dt)
	for id in fabrica.concluidas:
		controle._avisar("Pesquisa concluída: %s" % pesquisa.pesquisas()[id].nome)
		Som.tocar("pesquisa")
		controle.barra.atualizar_bloqueios()
	# quem trabalhou polui no próprio chunk e vira alvo das aranhas por 60 s
	var fontes_vivas: Array[Dictionary] = []
	for id in fabrica.emissao:
		var e: Dictionary = mapa.estruturas[id]
		poluicao.emitir(e.minimo, fabrica.emissao[id])
		_poluiu_em[id] = _tempo
	for id in _poluiu_em.keys():
		if not mapa.estruturas.has(id) or _tempo - _poluiu_em[id] > 60.0:
			_poluiu_em.erase(id)
			continue
		var e: Dictionary = mapa.estruturas[id]
		fontes_vivas.append({"id": id, "pos": Grade.centro_da_area(e.minimo, e.area, e.rot)})
	clima.tick(dt)
	poluicao.chuva = clima.valores.chuva
	poluicao.tick(dt)
	colonia.tick(dt, fontes_vivas)
	_eventos.append_array(colonia.eventos)
	_tempo += dt
	if _relatorio:
		_t_rel -= dt
		if _t_rel <= 0.0:
			_t_rel = 30.0
			var est := {}
			for a in colonia.aranhas.values():
				est[a.estado] = int(est.get(a.estado, 0)) + 1
			var perto := INF
			for n in colonia.ninhos.values():
				perto = minf(perto, n.centro.distance_to(Vector2(15, 0)))
			var maq := {}
			for id in fabrica.maquinas:
				maq[mapa.estruturas[id].nome] = Maquina.Estado.keys()[fabrica.maquinas[id].estado]
			print("t=%4.0fs  polu=%.0f (chunks %d)  ninhos=%d (mais perto %.0f)  aranhas=%s  trens=%s  municao=%s  estruturas=%d  maq=%s  comb=%s  estoques=%s" % [
					_tempo, poluicao.total(), poluicao.valores.size(), colonia.ninhos.size(), perto, est,
					trens.map(func(t): return "%s/%d" % [Trem.Estado.keys()[t.estado], t.total_carga()]),
					colonia.torres.values().map(func(t): return t.municao), mapa.estruturas.size(), maq,
					fabrica.combustivel.values().map(func(v): return snappedf(v, 0.1)), estoques.values()])
	for t in trens:
		t.tick(dt)
		if t.chegada >= 0:
			Som.tocar("apito_trem", Grade.ponto_mundo(t.ponto_em(t.s).pos), -3.0)
			if estoques.has(t.chegada):
				t.trocar_carga(estoques[t.chegada], t.chegada)
			t.chegada = -1


# ------------------------------------------------------------------ seleção (painel de detalhe)
const NOMES_ESTADO := {Maquina.Estado.SEM_RECEITA: "sem receita — escolha abaixo", Maquina.Estado.SEM_INSUMO: "esperando insumo",
		Maquina.Estado.SAIDA_CHEIA: "saída cheia (tire os produtos)", Maquina.Estado.SEM_ENERGIA: "sem energia",
		Maquina.Estado.SEM_JAZIDA: "jazida esgotada", Maquina.Estado.TRABALHANDO: "trabalhando"}


## Clique/toque de mão vazia: trem perto do ponto, senão a estrutura do tile. Vector2.INF fecha.
func selecionar(p: Vector2) -> void:
	_sel = {}
	if p != Vector2.INF:
		for t in trens:
			for pose in t.poses():
				if pose.pos.distance_to(p) < 1.6:
					_sel = {"trem": t.id}
		if _sel.is_empty():
			var id: int = mapa.tiles.get(Vector2i(p.floor()), -1)
			if id >= 0 and mapa.estruturas[id].nome != "ninho_aranha":
				_sel = {"estrutura": id}
	_detalhe()


func _nome_item(i: String) -> String:
	return Registro.itens.get(i, {}).get("nome", i)


func _lista_itens(d: Dictionary) -> String:
	var partes: Array[String] = []
	for k in d:
		if int(d[k]) > 0:
			partes.append("%d %s" % [d[k], _nome_item(k)])
	return ", ".join(partes) if not partes.is_empty() else "—"


func _numero_estacao(id: int) -> int:
	for i in grafo.estacoes.size():
		if grafo.estacoes[i].estrutura == id:
			return i + 1
	return 0


func _detalhe() -> void:
	var barra := controle.barra
	if _sel.has("pesquisa"):
		_detalhe_pesquisa()
		return
	if _sel.has("trem"):
		var t: Trem = null
		for x in trens:
			if x.id == _sel.trem: t = x
		if t == null:
			_sel = {}
		else:
			var est := {Trem.Estado.ANDANDO: "andando", Trem.Estado.PARADO: "parado na estação",
					Trem.Estado.ESPERANDO_BLOCO: "esperando sinal", Trem.Estado.SEM_ROTA: "sem rota"}
			var texto := "Estado: %s\nCarga: %s (%d de %d)\nRota: toque nas estações para ligar/desligar.\nSem nenhuma ligada, passa por todas." % [
					est[t.estado], _lista_itens(t.carga), t.total_carga(), t.capacidade()]
			var botoes := []
			for e in grafo.estacoes:
				var id: int = e.estrutura
				var na_rota := t.rota.has(id)
				var ordem := t.rota.find(id) + 1
				botoes.append({"texto": "Estação %d%s" % [_numero_estacao(id), "  (parada %d)" % ordem if na_rota else ""],
						"ligado": na_rota, "acao": func():
							if t.rota.has(id): t.rota.erase(id)
							else: t.rota.append(id)
							t.proxima = 0
							t.planejar()
							_detalhe()})
			botoes.append({"texto": "Desmontar trem (devolve o material)", "acao": func():
				trens.erase(t)
				grafo.liberar(t.id)
				construtor.devolver("trem")
				_sel = {}
				_detalhe()})
			barra.detalhe("Trem %d" % t.id, texto, botoes)
			return
	if _sel.has("estrutura") and not mapa.estruturas.has(_sel.estrutura):
		_sel = {}
	if _sel.is_empty():
		barra.fechar_detalhe()
		return
	var id: int = _sel.estrutura
	var e: Dictionary = mapa.estruturas[id]
	var titulo: String = controle.barra.rotulo(e.nome)
	var linhas: Array[String] = []
	var botoes := []
	var vida_max: float = Registro.estruturas.get(e.nome, {}).get("vida", 0)
	if colonia.vida.has(id):
		linhas.append("Vida: %d de %d" % [colonia.vida[id], vida_max])
	if fabrica.maquinas.has(id):
		var m: Maquina = fabrica.maquinas[id]
		linhas.append("Estado: %s" % NOMES_ESTADO[m.estado])
		if m.receita_id != "":
			linhas.append("Receita: %s → %s" % [_lista_itens(m.receita.get("entradas", {})), _lista_itens(m.receita.get("saidas", {}))])
		linhas.append("Dentro: %s\nPronto: %s" % [_lista_itens(m.entradas), _lista_itens(m.saidas)])
		if fabrica.combustivel.has(id):
			linhas.append("Combustível: %.1f MJ" % fabrica.combustivel[id])
		for fl in m.fluidos:
			linhas.append("%s: %.0f" % [fl.capitalize(), m.fluidos[fl]])
		var tipo: String = Registro.estruturas[e.nome].get("maquina", "")
		if tipo in ["montadora", "refinador", "fornalha"]:
			for r in Registro.receitas_da_maquina(tipo):
				if not pesquisa.receita_liberada(r):
					continue
				var rec: Dictionary = Registro.receitas[r]
				botoes.append({"texto": "%s  ←  %s" % [_lista_itens(rec.get("saidas", {})), _lista_itens(rec.get("entradas", {}))],
						"ligado": m.receita_id == r, "acao": func(): fabrica.escolher_receita(id, r); _detalhe()})
	elif e.nome == "nucleo":
		var linhas_n: Array[String] = []
		var chaves := inventario.keys()
		chaves.sort()
		for k in chaves:
			if int(inventario[k]) > 0:
				linhas_n.append("%s: %d" % [_nome_item(k), inventario[k]])
		linhas.append("Estoque (o que entra pelas bocas vira material de construção):")
		linhas.append("\n".join(linhas_n) if not linhas_n.is_empty() else "vazio")
	elif not fabrica.rede_de(id).is_empty():
		var r: Dictionary = fabrica.rede_de(id)
		linhas.append("Rede de canos: %s %.0f de %.0f" % [r.fluido if r.fluido != "" else "vazia", r.qtd, r.cap])
	elif fabrica.distribuidores.has(id):
		linhas.append("Passando: %s" % (", ".join(fabrica.distribuidores[id].buffer.map(_nome_item)) if not fabrica.distribuidores[id].buffer.is_empty() else "nada"))
	elif fabrica.laboratorios.has(id):
		linhas.append("Pacotes de pesquisa: %d de 10\nEnergia: %d%%" % [fabrica.laboratorios[id].pacotes, fabrica.laboratorios[id].energia * 100])
	elif fabrica.baus.has(id):
		linhas.append("Conteúdo: %s" % _lista_itens(fabrica.baus[id]))
	elif e.nome == "gerador":
		linhas.append("Combustível: %.1f MJ (carvão ou biomassa pela porta sul ou por braço)" % fabrica.combustivel.get(id, 0.0))
	elif e.nome == "torre_defesa":
		var t: Dictionary = colonia.torres.get(id, {})
		linhas.append("Munição: %d tiros (cada munição que chega por braço/esteira = %d)" % [t.get("municao", 0), Fabrica.TIROS_POR_MUNICAO])
	elif estoques.has(id):
		titulo = "Estação %d" % _numero_estacao(id)
		linhas.append("Para enviar: %s\nRecebido: %s" % [_lista_itens(estoques[id].enviar), _lista_itens(estoques[id].recebido)])
	elif fabrica.bracos.has(id):
		var b: Braco = fabrica.bracos[id]
		linhas.append("Segurando: %s\nEnergia: %d%%\nEntregues: %d" % [_nome_item(b.segurando) if b.segurando != "" else "nada", b.energia * 100, b.entregues])
	match Fiacao.papel(e.nome):
		"consumo":
			var fontes := Fiacao.ligacoes(mapa, e)
			linhas.append("Energia: %d%% · ligada a %d poste(s)" % [fabrica.rede.satisfacao(id) * 100, fontes] if fontes > 0 else "Energia: SEM FIO — ponha um poste a até 5 m")
			for n in [1, 2, 3]:
				botoes.append({"texto": "Aceitar %d fonte(s) de energia" % n, "ligado": int(e.get("fontes", 1)) == n,
						"acao": func(): Fiacao.mudar_vagas(mapa, id, n); _fabrica_suja = true; _detalhe()})
		"poste":
			var r: Dictionary = Registro.estruturas[e.nome]
			linhas.append("Fios: %d · alcance %d m até outro poste, %d m até máquinas%s" % [e.get("fios", []).size(), r.raio_fio, r.raio_ligacao,
					" (sem fio)" if Fiacao.eh_sem_fio(e.nome) else ""])
			linhas.append("Na rede: %s" % ("gerador ligado" if fabrica.rede.tem_fonte(id) else "nenhum gerador"))
	if linhas.is_empty():
		linhas.append(Registro.modelos.get(e.nome, {}).get("descricao", ""))
	barra.detalhe(titulo, "\n".join(linhas), botoes)


func _detalhe_pesquisa() -> void:
	var linhas: Array[String] = []
	var botoes := []
	if pesquisa.livre:
		linhas.append("Demonstração: tudo já está liberado.")
	else:
		if pesquisa.ativa != "":
			var at: Dictionary = pesquisa.pesquisas()[pesquisa.ativa]
			linhas.append("Pesquisando: %s — %d de %d pacotes" % [at.nome, pesquisa.feitos, at.pacotes])
		else:
			linhas.append("Escolha o que pesquisar.")
		linhas.append("Laboratório (com energia) gasta pacotes de pesquisa.\nPacote: montadora com 1 cristal lapidado + 1 engrenagem.")
		for id in pesquisa.pesquisas():
			var pq: Dictionary = pesquisa.pesquisas()[id]
			var libera: Array[String] = []
			for n in pq.get("libera", []):
				libera.append(controle.barra.rotulo(n))
			for r in pq.get("receitas", []):
				libera.append(_lista_itens(Registro.receitas[r].get("saidas", {})).trim_prefix("1 "))
			var resumo := ", ".join(libera)
			if pesquisa.concluidas.has(id):
				linhas.append("Feita: %s" % pq.nome)
			elif pesquisa.disponivel(id):
				botoes.append({"texto": "%s (%d pacotes) — %s" % [pq.nome, pq.pacotes, resumo], "ligado": pesquisa.ativa == id,
						"acao": func(): pesquisa.escolher(id); _detalhe()})
			else:
				var falta: Array[String] = []
				for rq in pq.get("requer", []):
					if not pesquisa.concluidas.has(rq):
						falta.append(pesquisa.pesquisas()[rq].nome)
				linhas.append("Depois de %s: %s" % [" e ".join(falta), pq.nome])
	controle.barra.detalhe("Pesquisa", "\n".join(linhas), botoes)


func _hud() -> void:
	if not _sel.is_empty():
		_detalhe()
	var atacando := 0
	for a in colonia.aranhas.values():
		if a.estado == Colonia.E.ATACANDO:
			atacando += 1
	var municao := 0
	for t in colonia.torres.values():
		municao += t.municao
	var aqui := poluicao.em(Grade.tile_de_mundo(camera.alvo))
	var texto := "Clima: %s\nPoluição aqui: %.1f   ·   total: %.0f\nNinhos: %d   ·   aranhas: %d\nMunição nas torres: %d   ·   trens: %d" % [
			clima.nome(), aqui, poluicao.total(), colonia.ninhos.size(), colonia.aranhas.size(), municao, trens.size()]
	if modo != "demo":
		var principais: Array[String] = []
		for k in ["placa_ferro", "engrenagem", "placa_cobre", "pedra"]:
			principais.append("%d %s" % [int(inventario.get(k, 0)), _nome_item(k).to_lower()])
		texto += "\nNúcleo: " + ", ".join(principais)
		if pesquisa.ativa != "":
			texto += "\nPesquisa: %s %d/%d" % [pesquisa.pesquisas()[pesquisa.ativa].nome, pesquisa.feitos, pesquisa.pesquisas()[pesquisa.ativa].pacotes]
	controle.barra.situacao(texto, "Ataque! %d aranha(s) vindo" % atacando if atacando > 0 else "")
