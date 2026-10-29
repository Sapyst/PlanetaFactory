class_name RoteiroTeste
extends Node
## Teste visual sem humano: injeta cliques, teclas e toques de verdade (Input.parse_input_event passa pela
## interface e pelo ControleConstrucao como se fosse a pessoa) em quadros fixos. Com --write-movie e --fixed-fps
## cada quadro vira um PNG, então dá para conferir o fantasma verde/vermelho, a peça posta, a remoção etc.
##   godot --path jogo --write-movie /tmp/r/q.png --fixed-fps 30 --quit-after 130 -- camera -1 1 15 roteiro construir
##   ... -- camera -1 1 15 roteiro toque

var roteiro := ""
var cena: Node
var _quadro := 0
var _passos: Array = []      ## [quadro, Callable]


func _ready() -> void:
	# o gerenciador de janelas pode impor outro tamanho; a gravação é 1280×720, então a tela lógica também
	get_window().content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
	match roteiro:
		"construir": _roteiro_pc()
		"toque": _roteiro_toque()
		"trem": _roteiro_trem()
		"ataque": _roteiro_ataque()
		"poluicao": _roteiro_poluicao()
		"painel": _roteiro_painel()
		"salvar": _roteiro_salvar()
		"estresse": _roteiro_estresse()
		"fundo": em(2, func(): cena.controle.barra.visible = false)
		"vitrine": _roteiro_vitrine()
		"panorama": _roteiro_panorama()
		"fios": _roteiro_fios()
		"rota": _roteiro_rota()
		"mostruario": _roteiro_mostruario()
		"encosta": _roteiro_encosta()
		"aplainar": _roteiro_aplainar()
		"aranha": _roteiro_aranha()
		"montagem": _roteiro_montagem()
		"grama": _roteiro_grama()
		"ambiente": _roteiro_ambiente()
		"recursos":
			em(4, func(): cena.controle.alternar_recursos())
			em(6, func(): mover(tela(Vector2i(-15, -9))))
		"vagao_tex": _roteiro_vagao_tex()
		"conferir": print("DIGITAL ", digital(cena))
	print("ROTEIRO ", roteiro, " com ", _passos.size(), " passos; tela ", get_viewport().get_visible_rect().size, " janela ", DisplayServer.window_get_size())


func _process(_d: float) -> void:
	_quadro += 1
	if _voo_ini > 0 and _quadro >= _voo_ini:
		_voar((_quadro - _voo_ini) / 30.0)
	if _grama_ini >= 0:
		var tg := (_quadro - _grama_ini) / 30.0
		var cg: CameraJogo = cena.camera
		cg.alvo = Grade.ponto_mundo(Vector2(-14.0, -14.0))
		cg.distancia = 11.0
		cg.angulo = 0.4 + tg * 0.08
		cg.posicionar()
		if _quadro - _grama_ini == 60:
			_t_ant = Time.get_ticks_usec()
		elif _quadro - _grama_ini > 60:
			var ag := Time.get_ticks_usec()
			_tempos.append((ag - _t_ant) / 1000.0)
			_t_ant = ag
			if _tempos.size() == 300:
				_relatorio_tempos("grama 52 mil tufos")
				get_tree().quit()
	if _aranha != null:
		# anda em volta de um ponto (curvas e reta), a câmera acompanha de perto
		var t := _quadro / 30.0
		var c := Vector2(-6.0, -10.0)          # área livre (sem construção no caminho)
		var p := c + Vector2(cos(t * 0.45), sin(t * 0.45)) * 4.5
		_aranha.ir_para(Grade.ponto_mundo(p))
		var cam: CameraJogo = cena.camera
		cam.alvo = cam.alvo.lerp(_aranha.global_position, 0.08)
		cam.distancia = 8.5
		cam.angulo = 0.6 + t * 0.12
		cam.posicionar()
	for p in _passos:
		if p[0] == _quadro:
			p[1].call()


func em(q: int, f: Callable) -> void:
	_passos.append([q, f])


func tela(t: Vector2i) -> Vector2:
	return (cena.camera as Camera3D).unproject_position(Grade.centro_mundo(t))


func botao(chave: String) -> Vector2:
	return cena.controle.barra.centro_de(chave)


# ------------------------------------------------------------------ eventos
## Os eventos entram em coordenadas da JANELA; o roteiro pensa na tela lógica 1280×720 (a janela pode estar escalada).
func _jan(p: Vector2) -> Vector2:
	return get_viewport().get_final_transform() * p


func mover(p: Vector2) -> void:
	p = _jan(p)
	var e := InputEventMouseMotion.new()
	e.position = p
	e.global_position = p
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) else 0
	Input.parse_input_event(e)


func botao_mouse(p: Vector2, apertado: bool, b := MOUSE_BUTTON_LEFT) -> void:
	p = _jan(p)
	var e := InputEventMouseButton.new()
	e.position = p
	e.global_position = p
	e.button_index = b
	e.pressed = apertado
	Input.parse_input_event(e)


func clicar(p: Vector2) -> void:
	mover(p)
	botao_mouse(p, true)
	botao_mouse(p, false)


func tecla(k: Key, ctrl := false) -> void:
	for apertada in [true, false]:
		var e := InputEventKey.new()
		e.keycode = k
		e.physical_keycode = k
		e.ctrl_pressed = ctrl
		e.pressed = apertada
		Input.parse_input_event(e)


func toque(i: int, p: Vector2, apertado: bool) -> void:
	p = _jan(p)
	var e := InputEventScreenTouch.new()
	e.index = i
	e.position = p
	e.pressed = apertado
	Input.parse_input_event(e)


func arrasto(i: int, de: Vector2, para: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = i
	e.position = _jan(para)
	e.relative = _jan(para) - _jan(de)
	Input.parse_input_event(e)


## Arrasta o mouse (botão esquerdo) de um tile a outro ao longo de n quadros a partir de q.
func traco_mouse(q: int, a: Vector2i, b: Vector2i, n: int) -> void:
	em(q, func(): mover(tela(a)); botao_mouse(tela(a), true))
	for k in range(1, n + 1):
		var f := float(k) / n
		em(q + k, func(): mover(tela(a).lerp(tela(b), f)))


# ------------------------------------------------------------------ roteiros
## PC: escolhe a esteira, traça um L, põe; fornalha em cima (vermelho) e ao lado (verde);
## extrator fora da jazida (vermelho); remove um pedaço com retângulo; desfaz.
func _roteiro_pc() -> void:
	em(4, func(): clicar(botao("esteira")))
	em(6, func(): mover(tela(Vector2i(-6, -3))))
	traco_mouse(8, Vector2i(-6, -3), Vector2i(2, 2), 16)
	# quadro ~30: foto do traço verde
	em(34, func(): botao_mouse(tela(Vector2i(2, 2)), false))
	em(38, func(): clicar(botao("cat:3")))
	em(40, func(): clicar(botao("fornalha")))
	em(42, func(): mover(tela(Vector2i(-2, -3))))
	# quadro ~48: fornalha vermelha em cima da esteira
	em(50, func(): mover(tela(Vector2i(-1, 2))))
	em(52, func(): tecla(KEY_R))
	em(56, func(): clicar(tela(Vector2i(-1, 2))))
	em(60, func(): clicar(botao("extrator_cristal")))
	em(62, func(): mover(tela(Vector2i(-4, 4))))
	# quadro ~68: extrator vermelho (precisa de jazida)
	em(72, func(): tecla(KEY_X))
	traco_mouse(74, Vector2i(-6, -3), Vector2i(-3, -2), 6)
	# quadro ~84: retângulo de remoção vermelho
	em(86, func(): botao_mouse(tela(Vector2i(-3, -2)), false))
	em(92, func(): tecla(KEY_ESCAPE))
	em(96, func(): mover(Vector2(640, 40)))
	# quadro ~100: depois de remover
	em(104, func(): tecla(KEY_Z, true))
	# quadro ~112: desfeito (a esteira volta)
	em(116, func(): clicar(botao("cat:5")))
	em(118, func(): clicar(botao("muro_centro")))
	traco_mouse(120, Vector2i(-7, 5), Vector2i(-2, 5), 5)
	em(126, func(): botao_mouse(tela(Vector2i(-2, 5)), false))
	traco_mouse(128, Vector2i(-2, 4), Vector2i(-2, 1), 4)
	em(133, func(): botao_mouse(tela(Vector2i(-2, 1)), false))
	em(135, func(): tecla(KEY_ESCAPE))
	# quadro ~140: muro em L, panos ligando os pilares


# ------------------------------------------------------------------ mostruário (prints e GIF de apresentação)
## Fábrica lotada a oeste do início (brocas nas jazidas, barramento de esteiras, elevada cruzando, blocos de
## máquinas, energia, muralha com torres), sem interface, tudo animado. `-- roteiro mostruario voo` faz o voo
## de câmera (18 s a partir do quadro 60); sem "voo" a câmera fica onde o argumento `camera` mandar (prints).
const VOO := [  # [segundo, x, z, distância, ângulo]
	[0.0, -2.0, -4.0, 72.0, 0.55], [3.0, -14.0, -8.0, 34.0, 0.85], [6.0, -25.0, -2.0, 15.0, 1.25],
	[9.0, -30.0, -19.0, 21.0, 1.8], [12.0, -29.0, 18.0, 25.0, 2.5], [15.0, -12.0, 8.0, 40.0, 3.0],
	[18.0, 6.0, 0.0, 62.0, 3.35]]
var _voo_ini := 0


func _roteiro_mostruario() -> void:
	Sessao.config.fps = false
	cena.animar_tudo = true
	cena._efeitos.mostrar_icones = false
	em(2, func():
		cena.controle.barra.visible = false
		_montar_mostruario())
	em(14, func(): _encher_esteiras())
	var args := OS.get_cmdline_user_args()
	if args.has("visao"):
		em(20, func(): cena.controle.alternar_recursos())
	if args.has("setas"):
		em(20, func():
			cena.controle.escolher("esteira")
			mover(Vector2(-50, -50)))
	if args.has("voo"):
		_voo_ini = 60
		em(60 + int(VOO[-1][0] * 30.0) + 2, func(): get_tree().quit())


func _voar(t: float) -> void:
	var i := 0
	while i < VOO.size() - 2 and t > VOO[i + 1][0]:
		i += 1
	var k: Array = [VOO[maxi(i - 1, 0)], VOO[i], VOO[i + 1], VOO[mini(i + 2, VOO.size() - 1)]]
	var u := clampf((t - k[1][0]) / (k[2][0] - k[1][0]), 0.0, 1.0)
	u = u * u * (3.0 - 2.0 * u) * 0.35 + u * 0.65                # leve suavização sem parar nos pontos
	var v := []
	for c in range(1, 5):
		var a: float = k[0][c]
		var b: float = k[1][c]
		var cc: float = k[2][c]
		var d: float = k[3][c]
		if c == 3:
			a = log(a); b = log(b); cc = log(cc); d = log(d)
		var r := 0.5 * (2.0 * b + (cc - a) * u + (2.0 * a - 5.0 * b + 4.0 * cc - d) * u * u + (3.0 * b - a - 3.0 * cc + d) * u * u * u)
		v.append(exp(r) if c == 3 else r)
	var cam: CameraJogo = cena.camera
	cam.alvo = Vector3(v[0], 0, v[1])
	cam.distancia = v[2]
	cam.angulo = v[3]
	cam.posicionar()


func _montar_mostruario() -> void:
	var con: Construtor = cena.construtor
	var p := func(plano: Array[Dictionary]) -> void: cena.sincronizar(con.executar(plano))
	for x in range(-42, -8):
		for y in range(-30, 30):
			cena.mapa.limpar_obstaculo(Vector2i(x, y))
	# brocas nas jazidas de ferro (-13, 9) e carvão (-15, -9); cada uma solta um ramal do barramento para oeste
	var saidas: Array[Vector2i] = []
	for base in [Vector2i(-13, 9), Vector2i(-15, -9)]:
		for o in [Vector2i(-2, -2), Vector2i(1, -2), Vector2i(-2, 1), Vector2i(1, 1)]:
			var plano := con.plano_peca("broca_minerio", base + o, 3)
			if plano[0].motivo != "":
				continue
			var rel := con.executar(plano)
			cena.sincronizar(rel)
			for id in rel.colocados:
				var e: Dictionary = cena.mapa.estruturas[id]
				var porta := Grade.porta_no_mundo(Registro.estruturas["broca_minerio"].portas[0], e.minimo, Registro.area("broca_minerio"), e.rot)
				saidas.append(porta.tile_fora)
	var linha := 0
	for t in saidas:
		var y := -6 + linha * 2
		p.call(con.plano_linha("esteira", t, Vector2i(-33, y), 0))
		linha += 1
	# esteira elevada atravessando o barramento (norte–sul em x = −26)
	p.call(con.plano_linha("esteira", Vector2i(-26, -16), Vector2i(-26, -14), 0))
	p.call(con.plano_peca("esteira_rampa", Vector2i(-26, -13), Construtor.rot_do_fluxo(0)))
	con.nivel = 1
	p.call(con.plano_linha("esteira", Vector2i(-26, -12), Vector2i(-26, 14), 0))
	p.call(con.plano_peca("rampa_desce", Vector2i(-26, 15), Construtor.rot_do_fluxo(0)))
	con.nivel = 0
	p.call(con.plano_linha("esteira", Vector2i(-26, 16), Vector2i(-26, 18), 0))
	# blocos de máquinas: norte (montadoras e fornalhas) e sul (refinadores e laboratórios), com braço e baú
	for x in range(-35, -12, 5):
		p.call(con.plano_peca("montadora", Vector2i(x, 22), 0))
		p.call(con.plano_peca("fornalha", Vector2i(x, 17), 0))
		p.call(con.plano_peca("braco", Vector2i(x, 19), 0))
		p.call(con.plano_peca("bau", Vector2i(x + 1, 19), 0))
		p.call(con.plano_peca("refinador", Vector2i(x, -20), 0))
		p.call(con.plano_peca("laboratorio", Vector2i(x, -25), 0))
		p.call(con.plano_peca("braco", Vector2i(x, -17), 2))
		p.call(con.plano_peca("bau", Vector2i(x + 1, -17), 0))
	# energia: geradores e postes (fios automáticos)
	for g in [Vector2i(-35, 13), Vector2i(-31, 13), Vector2i(-35, -12), Vector2i(-31, -12)]:
		p.call(con.plano_peca("gerador", g, 0))
	# miolo do barramento: tanques ligados por canos
	for t in [Vector2i(-21, 0), Vector2i(-17, 0), Vector2i(-21, 4), Vector2i(-17, 4)]:
		p.call(con.plano_peca("tanque", t, 0))
	p.call(con.plano_linha("cano", Vector2i(-23, -2), Vector2i(-23, 7), 0))
	p.call(con.plano_linha("cano", Vector2i(-22, 7), Vector2i(-15, 7), 0))
	for x in range(-35, -10, 6):
		for y in [-22, -14, 10, 20]:
			p.call(con.plano_peca("poste_energia", Vector2i(x, y), 0))
	# muralha com torres nos cantos
	p.call(con.plano_linha("muro_centro", Vector2i(-38, -29), Vector2i(-10, -29), 0))
	p.call(con.plano_linha("muro_centro", Vector2i(-38, 28), Vector2i(-10, 28), 0))
	p.call(con.plano_linha("muro_centro", Vector2i(-38, -28), Vector2i(-38, 27), 0))
	for t in [Vector2i(-35, -26), Vector2i(-35, 25), Vector2i(-12, -26), Vector2i(-12, 25)]:
		p.call(con.plano_peca("torre_defesa", t, 0))
	con._historico.clear()


## Itens já correndo no barramento e na elevada (o vídeo começa com a fábrica em movimento).
func _encher_esteiras() -> void:
	var itens := ["minerio_ferro", "carvao", "minerio_cobre", "pedra"]
	for c in cena.fabrica.caminhos:
		var e: EsteiraCaminho = c.esteira
		var pos := 0.3
		var k := 0
		while pos < e.util() - 0.6:
			e.inserir_em(itens[k % itens.size()], pos)
			pos += 0.85
			k += 1


## Construção numa encosta longe do início: o chão em volta é aplainado no nível de cada peça (foto ~40).
func _roteiro_encosta() -> void:
	em(3, func():
		var con: Construtor = cena.construtor
		var c := Grade.tile_de_mundo(cena.camera.alvo)
		for x in range(c.x - 10, c.x + 11):
			for y in range(c.y - 8, c.y + 9):
				cena.mapa.limpar_obstaculo(Vector2i(x, y))
		var postos := 0
		for x in range(c.x - 8, c.x + 9, 3):
			for y in range(c.y - 6, c.y + 7, 3):
				var rel := con.executar(con.plano_peca("fornalha", Vector2i(x, y), 0))
				postos += rel.colocados.size()
				cena.sincronizar(rel)
		print("ENCOSTA %d fornalhas postas" % postos))


## Terraplenagem: a central no meio, um patamar aplainado em volta (atravessando encostas) e fornalhas em cima.
func _roteiro_aplainar() -> void:
	em(3, func():
		var con: Construtor = cena.construtor
		cena.controle.barra.visible = false
		var c := Grade.tile_de_mundo(cena.camera.alvo)
		cena.sincronizar(con.executar(con.plano_peca("terraplenagem", c, 0)))
		var pl := con.plano_aplainar(c - Vector2i(14, 12), c + Vector2i(14, 12))
		cena.sincronizar(con.executar(pl))
		print("APLAINAR ", Construtor.contar(pl))
		for x in [-6, -3, 3, 6]:
			cena.sincronizar(con.executar(con.plano_peca("fornalha", c + Vector2i(x, 3), 0)))
		print("APLAINAR ok, central: ", cena.mapa.tem_terraplenagem()))


## Animação de construção: três máquinas postas uma depois da outra num chão vazio (a montagem e o piso crescendo).
func _roteiro_montagem() -> void:
	em(2, func():
		cena.controle.barra.visible = false
		Sessao.config.fps = false
		cena.animar_tudo = true
		for x in range(-14, -1):
			for y in range(-16, -6):
				cena.mapa.limpar_obstaculo(Vector2i(x, y)))
	var pecas := [["fornalha", Vector2i(-12, -12)], ["montadora", Vector2i(-8, -13)], ["gerador", Vector2i(-4, -12)]]
	for i in pecas.size():
		var p: Array = pecas[i]
		em(20 + i * 45, func():
			var con: Construtor = cena.construtor
			cena.sincronizar(con.executar(con.plano_peca(p[0], p[1], 0))))


## Ambiente vivo acelerado: verão, 15 min de fábrica trabalhando (sujeira e óleo em volta), e um foco de fogo na
## campina perto da câmera.
func _roteiro_ambiente() -> void:
	em(40, func():
		var c: Clima = cena.clima
		c.estacao = 1
		var a: AmbienteVivo = cena.ambiente
		for i in 900:
			if cena.fabrica.emissao.is_empty():
				cena.fabrica.tick(1.0)
			a._passo(cena.fabrica, c)
			# deixa a emissão da fábrica viva entre os passos acelerados
		cena.controle.barra.visible = false
		Sessao.config.fps = false
		var alvo := Grade.tile_de_mundo(cena.camera.alvo)
		var acesos := 0
		for r in range(0, 8):
			for d in [Vector2i(r, 0), Vector2i(-r, 0), Vector2i(0, r), Vector2i(0, -r)]:
				if acesos < 3 and a._inflamavel(alvo + d):
					a._acender(alvo + d)
					acesos += 1
		print("AMBIENTE chunks=%d fogo=%d" % [a.dados.size(), a.fogo.size()]))


## Bloco de grama em massa (teste isolado): campo 24×24 m ao lado do início, câmera girando devagar em volta.
func _roteiro_grama() -> void:
	em(2, func():
		cena.controle.barra.visible = false
		var g := Grama.new()
		g.position = Grade.ponto_mundo(Vector2(-14.0, -14.0))
		cena.add_child(g)
		_grama_ini = _quadro)


var _grama_ini := -1


## Aranha andando de perto (GIF da animação): uma aranha solta circulando no chão plano do início.
var _aranha: Aranha = null


func _roteiro_aranha() -> void:
	em(2, func():
		cena.controle.barra.visible = false
		Sessao.config.fps = false
		_aranha = Aranha.new()
		_aranha.position = Grade.ponto_mundo(Vector2(-1.5, -10.0))
		cena.add_child(_aranha)
		cena.camera.alvo = _aranha.position)


## Traço inteligente: fornalha no caminho → o fantasma contorna (foto ~30); põe; um traço novo começando ao lado
## do fim vira o fim em curva (foto ~70).
func _roteiro_rota() -> void:
	em(2, func():
		var con: Construtor = cena.construtor
		cena.sincronizar(con.executar(con.plano_peca("fornalha", Vector2i(-2, -1), 0))))
	em(4, func(): clicar(botao("esteira")))
	em(6, func(): mover(tela(Vector2i(-7, -1))))
	traco_mouse(8, Vector2i(-7, -1), Vector2i(2, -1), 16)
	em(34, func(): botao_mouse(tela(Vector2i(2, -1)), false))
	traco_mouse(40, Vector2i(2, 0), Vector2i(2, 3), 8)
	em(52, func(): botao_mouse(tela(Vector2i(2, 3)), false))
	em(56, func(): mover(Vector2(640, 40)))


## Toque: escolhe a esteira tocando no botão, traça com um dedo, solta (põe), e dois dedos fazem pinça.
func _roteiro_toque() -> void:
	em(4, func(): toque(0, botao("esteira"), true))
	em(5, func(): toque(0, botao("esteira"), false))
	var a := Vector2i(-6, 3)
	var b := Vector2i(1, -2)
	em(8, func(): toque(0, tela(a), true))
	for k in range(1, 15):
		var f0 := float(k - 1) / 14
		var f1 := float(k) / 14
		em(8 + k, func(): arrasto(0, tela(a).lerp(tela(b), f0), tela(a).lerp(tela(b), f1)))
	# quadro ~26: traço verde sob o dedo
	em(30, func(): toque(0, tela(b), false))
	# dois dedos: pinça para afastar
	var c := Vector2(640, 360)
	em(40, func(): toque(0, c + Vector2(-120, 0), true); toque(1, c + Vector2(120, 0), true))
	for k in range(1, 11):
		var d0 := 120.0 - (k - 1) * 6.0
		var d1 := 120.0 - k * 6.0
		em(40 + k, func(): arrasto(0, c + Vector2(-d0, 0), c + Vector2(-d1, 0)); arrasto(1, c + Vector2(d0, 0), c + Vector2(d1, 0)))
	em(52, func(): toque(0, c + Vector2(-60, 0), false); toque(1, c + Vector2(60, 0), false))
	# quadro ~60: câmera afastada, nada construído pelo gesto de dois dedos


## Trem: câmera segue a composição saindo da estação A; no fim, o fantasma de um trem novo na aba Trilhos.
func _roteiro_trem() -> void:
	for q in range(2, 200, 2):
		em(q, func():
			if cena.trens.is_empty():
				return
			var t: Trem = cena.trens[0]
			var c: Vector2 = t.ponto_em(t.s - t.comprimento() / 2.0).pos
			cena.camera.alvo = cena.camera.alvo.lerp(Grade.ponto_mundo(c), 0.15)
			cena.camera.posicionar())
	em(150, func(): clicar(botao("cat:6")))
	em(152, func(): clicar(botao("trem")))
	em(154, func(): mover(tela(Vector2i(13, -8))))


## Ataque: um grupo vem para a fábrica pelo leste (torres atiram); outro, fora do alcance, morde um muro a oeste.
func _roteiro_ataque() -> void:
	em(3, func():
		var col: Colonia = cena.colonia
		for x in range(-3, 4):                     # o mapa carrega no fundo: garante os ninhos em volta
			for y in range(-3, 4):
				col.descobrir_chunk(Vector2i(x, y))
		var ninho: int = col.ninhos.keys()[0]
		var alvo := -1
		for id in cena.mapa.estruturas:
			if cena.mapa.estruturas[id].nome == "fornalha": alvo = id
		for k in 5:
			var a := col._nova_aranha(ninho)
			col.aranhas[a].pos = Vector2(34 + (k % 2) * 1.5, -4 + k * 1.3)
			col.aranhas[a].estado = Colonia.E.ATACANDO
			col.aranhas[a].alvo = alvo
		# muro a oeste e 3 aranhas atrás dele
		var con: Construtor = cena.construtor
		for y in range(-8, -1):
			con.mapa.limpar_obstaculo(Vector2i(-24, y))
		cena.sincronizar(con.executar(con.plano_linha("muro_centro", Vector2i(-24, -8), Vector2i(-24, -2), 0)))
		for k in 3:
			var a := col._nova_aranha(ninho)
			col.aranhas[a].pos = Vector2(-29, -6 + k * 1.6)
			col.aranhas[a].estado = Colonia.E.ATACANDO
			col.aranhas[a].alvo = alvo)
	# câmera: primeiro o leste (tiros), depois o muro
	em(4, func(): cena.camera.alvo = Vector3(25, 0, 7); cena.camera.distancia = 15; cena.camera.posicionar())
	em(130, func(): cena.camera.alvo = Vector3(-24, 0, 4); cena.camera.distancia = 11; cena.camera.posicionar())


## Poluição: adianta 6 minutos de emissão (só a nuvem) e liga a camada com a câmera bem afastada.
func _roteiro_poluicao() -> void:
	em(3, func():
		for i in 360:
			cena.poluicao.emitir(Vector2i(15, 5), 40.0 / 60.0)     # ~ a mini-fábrica a pleno
			cena.poluicao.tick(1.0)
		cena.camera.alvo = Vector3(14, 0, 0); cena.camera.distancia = 70; cena.camera.posicionar())
	em(6, func(): tecla(KEY_P))


func _tela_mundo(p: Vector2) -> Vector2:
	return (cena.camera as Camera3D).unproject_position(Grade.ponto_mundo(p, 0.5))


func _botao_detalhe(i: int) -> Vector2:
	var bs: Array = cena.controle.barra._det_botoes.get_children()
	return (bs[i] as Control).get_global_rect().get_center() if i < bs.size() else Vector2(-1, -1)


## Painel: clica no trem (rota: liga a estação 2), depois na fornalha (escolhe receita de tijolo).
func _roteiro_painel() -> void:
	em(3, func(): cena.camera.alvo = Vector3(12, 0, 6); cena.camera.distancia = 16; cena.camera.posicionar())
	em(8, func():
		var t: Trem = cena.trens[0]
		clicar(_tela_mundo(t.poses()[1].pos)))
	em(14, func(): clicar(_botao_detalhe(1)))
	# quadro ~30: painel do trem com a estação 2 na rota
	em(40, func():
		for id in cena.mapa.estruturas:
			if cena.mapa.estruturas[id].nome == "fornalha":
				var e: Dictionary = cena.mapa.estruturas[id]
				clicar(_tela_mundo(Grade.centro_da_area(e.minimo, e.area, e.rot))))
	em(46, func(): clicar(_botao_detalhe(2)))
	# quadro ~60: painel da fornalha com a receita escolhida


## Resumo do estado que tem que sobreviver a salvar + carregar.
static func digital(c: Node) -> String:
	var itens := 0
	for cm in c.fabrica.caminhos:
		itens += cm.esteira.itens.size()
	var inv := 0
	for k in c.inventario:
		inv += int(c.inventario[k])
	var nomes := {}
	for id in c.mapa.estruturas:
		nomes[c.mapa.estruturas[id].nome] = int(nomes.get(c.mapa.estruturas[id].nome, 0)) + 1
	var chaves := nomes.keys()
	chaves.sort()
	return "estr=%d %s inv=%d itens=%d aranhas=%d ninhos=%d polu=%.1f pesq=%s/%d trens=%d limpos=%d sem=%d" % [
			c.mapa.estruturas.size(), ",".join(chaves.map(func(k): return "%s:%d" % [k, nomes[k]])), inv, itens,
			c.colonia.aranhas.size(), c.colonia.ninhos.size(), c.poluicao.total(), c.pesquisa.ativa, c.pesquisa.feitos,
			c.trens.size(), c.mapa.limpos.size(), c.semente]


## Jogo novo: constrói (com custo), escolhe pesquisa, põe itens na esteira, salva e imprime o resumo.
func _roteiro_salvar() -> void:
	em(5, func():
		var con: Construtor = cena.construtor
		cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(-8, 4), Vector2i(-2, 4), 0)))
		cena.sincronizar(con.executar(con.plano_peca("bau", Vector2i(4, 4), 0)))
		cena.sincronizar(con.executar(con.plano_remocao(Vector2i(-12, -12), Vector2i(12, 12))))  # limpa e devolve
		cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(-8, 4), Vector2i(-2, 4), 0)))
		cena.pesquisa.escolher("defesa")
		cena.pesquisa.feitos = 3)
	em(20, func():
		var e: EsteiraCaminho = cena.fabrica.caminhos[0].esteira
		e.inserir_em("pedra", 2.0)
		e.inserir_em("carvao", 4.0))
	em(22, func():
		cena.salvar()
		print("DIGITAL ", digital(cena))
		get_tree().quit())


## Estresse: 2 400 esteiras + 20 torres + itens; mede quadros por segundo e chamadas de desenho na janela real.
func _roteiro_estresse() -> void:
	em(3, func():
		var con: Construtor = cena.construtor
		for x in range(20, 110):
			for y in range(-40, 30):
				cena.mapa.limpar_obstaculo(Vector2i(x, y))
		for i in 40:
			cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(24 + i * 2, -35), Vector2i(24 + i * 2, 24), 0)))
		for i in 20:
			cena.sincronizar(con.executar(con.plano_peca("torre_defesa", Vector2i(24 + i * 4, 27), 0)))
		cena.camera.alvo = Vector3(64, 0, 5)
		cena.camera.distancia = 44.0
		cena.camera.posicionar())
	em(10, func():
		for cm in cena.fabrica.caminhos:
			for k in 200:
				cm.esteira.inserir_em("pedra", k * 0.3))
	for q in [120, 240, 360]:
		em(q, _medir.bind(q))


func _medir(q: int) -> void:
	var tf := Time.get_ticks_usec()
	for i in 10:
		cena.fabrica.tick(1.0 / 30.0)
	var tc := Time.get_ticks_usec()
	for i in 10:
		cena.colonia.tick(1.0 / 30.0, [] as Array[Dictionary])
	print("      itens %.1f ms · fábrica %.2f ms · colônia %.2f ms" % [cena._desenho_itens.custo_us / 1000.0, (tc - tf) / 10000.0, (Time.get_ticks_usec() - tc) / 10000.0])
	print("ESTRESSE quadro %d: %d fps · %.1f ms de processo · %d chamadas de desenho · %d objetos · %d estruturas · %d nós" % [q,
			Engine.get_frames_per_second(), Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), cena.mapa.estruturas.size(),
			Performance.get_monitor(Performance.OBJECT_NODE_COUNT)])


## Vitrine (fotos): esteira elevada com rampas e pilares sobre outra esteira, fumaça e ícones de estado, painel de
## pesquisa, menu de pausa.
func _roteiro_vitrine() -> void:
	em(3, func():
		var con: Construtor = cena.construtor
		for x in range(-14, 2):
			for y in range(-14, -4):
				cena.mapa.limpar_obstaculo(Vector2i(x, y))
		cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(-6, -13), Vector2i(-6, -5), 0)))
		cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(-13, -9), Vector2i(-11, -9), 0)))
		cena.sincronizar(con.executar(con.plano_peca("esteira_rampa", Vector2i(-10, -9), Construtor.rot_do_fluxo(1))))
		con.nivel = 1
		cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(-9, -9), Vector2i(-3, -9), 0)))
		cena.sincronizar(con.executar(con.plano_peca("rampa_desce", Vector2i(-2, -9), Construtor.rot_do_fluxo(1))))
		con.nivel = 0
		cena.sincronizar(con.executar(con.plano_linha("esteira", Vector2i(-1, -9), Vector2i(1, -9), 0)))
		cena.sincronizar(con.executar(con.plano_peca("montadora", Vector2i(-11, -12), 0)))
		cena.camera.alvo = Vector3(-6, 0, 9); cena.camera.distancia = 15; cena.camera.posicionar())
	em(12, func():
		var e: EsteiraCaminho = cena.fabrica.caminhos[cena.fabrica._no_tile[Vector2i(-13, -9)][0]].esteira
		for k in 12:
			e.inserir_em("minerio_ferro", k * 0.6)
		var c2: EsteiraCaminho = cena.fabrica.caminhos[cena.fabrica._no_tile[Vector2i(-6, -13)][0]].esteira
		for k in 10:
			c2.inserir_em("carvao", k * 0.7))
	# quadro ~70: foto da elevada
	em(80, func(): cena.camera.alvo = Vector3(12, 0, -2); cena.camera.distancia = 18; cena.camera.posicionar())
	# quadro ~110: fumaça do gerador/extrator e ícone "sem receita" da fornalha
	em(120, func(): cena.abrir_pesquisa())
	# quadro ~135: painel de pesquisa (na demo: tudo liberado)
	em(140, func(): cena.abrir_pausa())
	# quadro ~150: pausa


## Panorama: arrasta a câmera a 18 m/s por terreno novo durante 12 s (zoom padrão) e depois 6 s afastada;
## mede o tempo de cada quadro na janela real (média, pior 5%, pior caso, quadros acima de 33 ms).
var _tempos: PackedFloat32Array = []
var _t_ant := 0
var _fase := 0
func _roteiro_panorama() -> void:
	em(30, func(): _fase = 1; _t_ant = Time.get_ticks_usec())


func _physics_process(_d: float) -> void:
	pass


func _notification(what: int) -> void:
	if what != NOTIFICATION_PROCESS or _fase == 0:
		return
	var agora := Time.get_ticks_usec()
	var dt := (agora - _t_ant) / 1000.0
	_t_ant = agora
	var cam: CameraJogo = cena.camera
	cam.alvo += Vector3(18.0, 0, 6.0) * dt / 1000.0
	cam.posicionar()
	_tempos.append(dt)
	var total := 0.0
	for t in _tempos: total += t
	if _fase == 1 and total > 12000.0:
		_relatorio_tempos("zoom padrão (44 m)")
		_tempos.clear()
		cam.distancia = 110.0
		_fase = 2
	elif _fase == 2 and total > 6000.0:
		_relatorio_tempos("zoom longe (110 m)")
		_fase = 0
		get_tree().quit()


func _relatorio_tempos(rotulo: String) -> void:
	var v := Array(_tempos)
	v.sort()
	var soma := 0.0
	var acima := 0
	for t in v:
		soma += t
		if t > 33.4: acima += 1
	print("PANORAMA %s: %d quadros · média %.1f ms · pior 5%% %.1f ms · pior %.1f ms · %d acima de 33 ms" % [
			rotulo, v.size(), soma / v.size(), v[int(v.size() * 0.95)], v[-1], acima])


## Fios: a rede da demo (gerador → postes → extrator e braços) e a prévia de um poste novo com o anel de alcance.
func _roteiro_fios() -> void:
	em(3, func(): cena.camera.alvo = Vector3(13, 0, -2); cena.camera.distancia = 17; cena.camera.posicionar())
	em(60, func(): clicar(botao("cat:4")))
	em(62, func(): clicar(botao("poste_energia")))
	em(64, func(): mover(tela(Vector2i(19, 9))))
	# quadro ~75: fios da demo + prévia amarela do poste novo e o anel de 9 m


## Teste de textura: o trem com o vagão texturizado; câmera de perto acompanhando a composição.
func _roteiro_vagao_tex() -> void:
	cena.controle.barra.visible = false
	for q in range(2, 300, 2):
		em(q, func():
			if cena.trens.is_empty():
				return
			var t: Trem = cena.trens[0]
			var c: Vector2 = t.ponto_em(t.s - t.comprimento() / 2.0).pos
			cena.camera.alvo = Grade.ponto_mundo(c)
			cena.camera.distancia = 9.0
			cena.camera.posicionar())
