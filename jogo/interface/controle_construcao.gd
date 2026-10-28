class_name ControleConstrucao
extends Node
## Roteia toda a entrada do jogo (é o único lugar que decide se um gesto constrói ou mexe na câmera):
##
##  PC      peça na mão: passar o mouse = fantasma; clicar = pôr; arrastar = traçar (esteira/cano/trilho/muro/poste)
##          botão direito: cancela (clique) ou move a câmera (arrasto); meio ou esquerdo sem peça = move a câmera
##          roda = zoom; Q/E = gira a câmera; WASD/setas = anda; R = girar peça (Shift+R ao contrário)
##          X = remover; Ctrl+Z = desfazer; Esc = cancelar; 1..9 = peça da aba; Tab = próxima aba
##  Toque   1 dedo com peça na mão: o fantasma segue o dedo e a peça é posta ao soltar (arrastar = traçar)
##          1 dedo sem peça = move a câmera; 2 dedos = move + pinça (zoom) e cancelam o traço em andamento
##
## O mundo só precisa de `sincronizar(relatorio)` para desenhar o que o Construtor mudou no mapa.

var construtor: Construtor
var camera: CameraJogo
var barra: BarraConstrucao
var fantasma: Fantasma
var mundo: Node                     ## precisa de sincronizar(rel: Dictionary)

var peca := ""                      ## "" = mão vazia
var removendo := false
var rot := 0

var _plano: Array[Dictionary] = []
var _chave_plano := ""
var _cursor := Vector2i.ZERO
var _cursor_valido := false
var _gesto := false                 ## traço/colocação em andamento (botão ou dedo pressionado)
var _inicio := Vector2i.ZERO
var _arrasto_camera := false
var _botao_dir := false
var _dir_moveu := 0.0
var _toques: Dictionary = {}        ## índice → posição
var _dedo := -1                     ## dedo do gesto de construção
var _pinca := 0.0
var _por_toque := false
var _aviso := ""
var _aviso_ate := 0
var _clique_ini := Vector2.INF        ## onde começou um clique/toque de mão vazia (se não arrastar, seleciona)


func configurar(p_construtor: Construtor, p_camera: CameraJogo, p_barra: BarraConstrucao, p_fantasma: Fantasma, p_mundo: Node) -> void:
	construtor = p_construtor
	camera = p_camera
	barra = p_barra
	fantasma = p_fantasma
	mundo = p_mundo
	barra.peca_escolhida.connect(escolher)
	barra.ferramenta.connect(_ferramenta)
	barra.fechar_detalhe_pedido.connect(func(): mundo.selecionar(Vector2.INF))
	barra.pode_desfazer(false)
	barra.mostrar_nivel(construtor.nivel)
	_atualizar()


# ------------------------------------------------------------------ ações
func escolher(nome: String) -> void:
	if peca == nome and not removendo:
		nome = ""                          # tocar de novo na peça solta ela
	peca = nome
	removendo = false
	_cancelar_gesto()
	barra.marcar(peca, removendo)
	_atualizar()


func girar(passo := -1) -> void:
	if peca == "":
		return
	rot = posmod(rot + passo, 4)           # −1 = horário (como o jogador espera do botão)
	_atualizar()


func alternar_remover() -> void:
	removendo = not removendo
	peca = ""
	_cancelar_gesto()
	barra.marcar(peca, removendo)
	_atualizar()


## Nível da esteira (0 chão, 1 = 0,5 m, 2 = 1,0 m). `ciclo` = volta ao chão depois do último.
func mudar_nivel(passo: int, ciclo := false) -> void:
	var n := construtor.nivel + passo
	n = posmod(n, MapaOcupacao.NIVEIS + 1) if ciclo else clampi(n, 0, MapaOcupacao.NIVEIS)
	construtor.nivel = n
	barra.mostrar_nivel(n)
	_chave_plano = ""
	_atualizar()


func alternar_poluicao() -> void:
	if mundo.has_method("alternar_poluicao"):
		barra.ligar_poluicao(mundo.alternar_poluicao())


func cancelar() -> void:
	if _gesto:
		_cancelar_gesto()
	else:
		peca = ""
		removendo = false
		barra.marcar(peca, removendo)
	_atualizar()


func desfazer() -> void:
	if not construtor.pode_desfazer():
		return
	mundo.sincronizar(construtor.desfazer())
	_avisar("Desfeito")
	_chave_plano = ""
	_atualizar()


func _ferramenta(nome: String) -> void:
	match nome:
		"girar": girar()
		"remover": alternar_remover()
		"desfazer": desfazer()
		"cancelar": cancelar()
		"poluicao": alternar_poluicao()
		"nivel": mudar_nivel(1, true)
		"pesquisa": mundo.abrir_pesquisa()
		"menu": mundo.abrir_pausa()


func _ativo() -> bool:
	return peca != "" or removendo


func _confirmar() -> void:
	if _plano.is_empty():
		return
	var n := Construtor.contar(_plano)
	var rel := construtor.executar(_plano)
	mundo.sincronizar(rel)
	if n.ok > 0 and peca == "esteira_rampa":
		mudar_nivel(1)                        # subiu: o próximo traço já é no alto
	elif n.ok > 0 and peca == "rampa_desce":
		mudar_nivel(-1)
	if removendo:
		_avisar("Removido: %d" % _plano.size())
		Som.tocar("remover")
	elif n.ok > 0:
		Som.tocar("construir")
		_avisar("Construído: %d%s" % [n.ok, "  ·  %d bloqueada(s)" % n.bloqueados if n.bloqueados > 0 else ""])
	_chave_plano = ""


func _cancelar_gesto() -> void:
	_gesto = false
	_dedo = -1


func _avisar(t: String) -> void:
	_aviso = t
	_aviso_ate = Time.get_ticks_msec() + 1600


# ------------------------------------------------------------------ entrada
func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey:
		_tecla(e)
	elif e is InputEventMouse and e.device == InputEvent.DEVICE_ID_EMULATION:
		return                                  # toque já tratado como toque
	elif e is InputEventMouseButton:
		_mouse_botao(e)
	elif e is InputEventMouseMotion:
		_mouse_moveu(e)
	elif e is InputEventScreenTouch:
		_toque(e)
	elif e is InputEventScreenDrag:
		_toque_arrastou(e)
	elif e is InputEventMagnifyGesture:
		camera.zoom(1.0 / e.factor)
	elif e is InputEventPanGesture:
		camera.arrastar(-e.delta * 8.0)


func _tecla(e: InputEventKey) -> void:
	if not e.pressed or e.echo:
		return
	match e.keycode:
		KEY_R: girar(1 if e.shift_pressed else -1)
		KEY_X: alternar_remover()
		KEY_P: alternar_poluicao()
		KEY_N: mudar_nivel(1, true)
		KEY_PAGEUP: mudar_nivel(1)
		KEY_PAGEDOWN: mudar_nivel(-1)
		KEY_ESCAPE:
			if _ativo() or _gesto: cancelar()
			else: mundo.abrir_pausa()
		KEY_T: mundo.abrir_pesquisa()
		KEY_Q: camera.girar(-0.3)
		KEY_E: camera.girar(0.3)
		KEY_TAB: barra.proxima_categoria(-1 if e.shift_pressed else 1)
		KEY_Z:
			if e.ctrl_pressed or e.meta_pressed: desfazer()
		_:
			var n: int = e.keycode - KEY_1
			var lista := barra.pecas_da_categoria()
			if n >= 0 and n < mini(9, lista.size()):
				escolher(lista[n])
	_atualizar()


func _mouse_botao(e: InputEventMouseButton) -> void:
	_por_toque = false
	match e.button_index:
		MOUSE_BUTTON_WHEEL_UP: camera.zoom(0.9)
		MOUSE_BUTTON_WHEEL_DOWN: camera.zoom(1.1)
		MOUSE_BUTTON_MIDDLE: _arrasto_camera = e.pressed
		MOUSE_BUTTON_RIGHT:
			_botao_dir = e.pressed
			if e.pressed:
				_dir_moveu = 0.0
			elif _dir_moveu < 6.0:
				cancelar()
		MOUSE_BUTTON_LEFT:
			if e.pressed:
				if barra.sobre_interface(e.position):
					return
				if _ativo():
					_mirar(e.position)
					_gesto = true
					_inicio = _cursor
				else:
					_arrasto_camera = true
					_clique_ini = e.position
			else:
				if _clique_ini != Vector2.INF and _clique_ini.distance_to(e.position) < 8.0:
					_selecionar(e.position)
				_clique_ini = Vector2.INF
				if _gesto:
					_mirar(e.position)
					_atualizar()
					_confirmar()
					_gesto = false
				_arrasto_camera = false
	_atualizar()


func _mouse_moveu(e: InputEventMouseMotion) -> void:
	_por_toque = false
	if _botao_dir:
		_dir_moveu += e.relative.length()
		camera.arrastar(e.relative)
	elif _arrasto_camera:
		camera.arrastar(e.relative)
	_mirar(e.position)
	_atualizar()


func _toque(e: InputEventScreenTouch) -> void:
	_por_toque = true
	if e.pressed:
		if _toques.is_empty() and barra.sobre_interface(e.position):
			return
		_toques[e.index] = e.position
		if _toques.size() == 1 and _ativo():
			_dedo = e.index
			_gesto = true
			_mirar(e.position)
			_inicio = _cursor
		elif _toques.size() == 1:
			_clique_ini = e.position
		elif _toques.size() >= 2:
			_clique_ini = Vector2.INF
			_cancelar_gesto()                   # segundo dedo = câmera
			_pinca = _distancia_dedos()
	else:
		if not _toques.has(e.index):
			return
		_toques.erase(e.index)
		if _clique_ini != Vector2.INF and _toques.is_empty() and _clique_ini.distance_to(e.position) < 14.0:
			_selecionar(e.position)                 # toque curto de mão vazia = ver a peça/trem
		_clique_ini = Vector2.INF
		if _gesto and e.index == _dedo:
			_mirar(e.position)
			_atualizar()
			_confirmar()
			_cancelar_gesto()
		if _toques.size() < 2:
			_pinca = 0.0
		if _toques.is_empty():
			_cursor_valido = false        # sem "hover" no toque: o fantasma some ao soltar
	_atualizar()


func _toque_arrastou(e: InputEventScreenDrag) -> void:
	_por_toque = true
	if not _toques.has(e.index):
		return
	_toques[e.index] = e.position
	if _toques.size() >= 2:
		camera.arrastar(e.relative / float(_toques.size()))
		var d := _distancia_dedos()
		if _pinca > 0.0 and d > 0.0:
			camera.zoom(_pinca / d)
		_pinca = d
	elif _gesto and e.index == _dedo:
		_mirar(e.position)
	elif not _gesto:
		camera.arrastar(e.relative)
		if _clique_ini != Vector2.INF and _clique_ini.distance_to(e.position) >= 14.0:
			_clique_ini = Vector2.INF
	_atualizar()


func _selecionar(tela: Vector2) -> void:
	var p := camera.no_chao(tela)
	if p != Vector3.INF and mundo.has_method("selecionar"):
		mundo.selecionar(Vector2(p.x, -p.z))


func _distancia_dedos() -> float:
	var ps := _toques.values()
	return (ps[0] as Vector2).distance_to(ps[1]) if ps.size() >= 2 else 0.0


func _mirar(tela: Vector2) -> void:
	if barra.sobre_interface(tela) and not _gesto:
		_cursor_valido = false
		return
	var p := camera.no_chao(tela)
	_cursor_valido = p != Vector3.INF
	if _cursor_valido:
		_cursor = Grade.tile_de_mundo(p)


# ------------------------------------------------------------------ plano + fantasma + dica
func _atualizar() -> void:
	barra.pode_desfazer(construtor.pode_desfazer())
	var mostrar := _ativo() and _cursor_valido and (_gesto or not _por_toque)
	if not mostrar:
		fantasma.limpar()
		_plano.clear()
		_chave_plano = ""
		barra.dica(_dica_parada(), false)
		return
	var chave := "%s|%s|%d|%s|%s|%s|%d" % [peca, removendo, rot, _inicio, _cursor, _gesto, construtor.nivel]
	if chave != _chave_plano:
		_chave_plano = chave
		var a := _inicio if _gesto else _cursor
		if removendo:
			_plano = construtor.plano_remocao(a, _cursor)
		elif Construtor.arrastavel(peca):
			_plano = construtor.plano_linha(peca, a, _cursor, rot)
		else:
			_plano = construtor.plano_peca(peca, _cursor, rot)
		fantasma.mostrar(_plano, removendo)
		_previa_fios()
	_dica_do_plano()


## Poste/torre/máquina no fantasma: mostra os fios que vão aparecer e o alcance do poste.
func _previa_fios() -> void:
	var pares := []
	var anel := 0.0
	var centro := Vector3.ZERO
	if not removendo and _plano.size() >= 1:
		for it in _plano:
			if it.motivo != "" or Fiacao.papel(it.nome) == "":
				continue
			var e := {"nome": it.nome, "minimo": it.minimo, "rot": it.rot, "area": Registro.area(it.nome), "fios": []}
			if Fiacao.papel(it.nome) == "poste":
				for alvo in Fiacao.alvos_do_poste(construtor.mapa, e):
					var o: Dictionary = construtor.mapa.estruturas[alvo]
					pares.append([Fiacao.ponto_fio(e, Fiacao.centro(o)), Fiacao.ponto_fio(o, Fiacao.centro(e))])
				anel = float(Registro.estruturas[it.nome].raio_fio)
				centro = Grade.ponto_mundo(Fiacao.centro(e), 0.05)
			else:
				var melhor := -1
				var md := INF
				for pid in construtor.mapa.estruturas:
					var p: Dictionary = construtor.mapa.estruturas[pid]
					if Fiacao.papel(p.nome) == "poste":
						var d := Fiacao.distancia(p, e)
						if d <= Fiacao.alcance(p, e) and d < md:
							md = d
							melhor = pid
				if melhor >= 0:
					var p: Dictionary = construtor.mapa.estruturas[melhor]
					pares.append([Fiacao.ponto_fio(p, Fiacao.centro(e)), Fiacao.ponto_fio(e, Fiacao.centro(p))])
	fantasma.mostrar_fios(pares, centro, anel)


func _dica_parada() -> String:
	if Time.get_ticks_msec() < _aviso_ate:
		return _aviso
	if removendo:
		return "Remover — %s numa peça ou árvore · arraste para um retângulo" % ("toque" if _por_toque else "clique")
	if peca == "":
		return ""
	return _dica_peca()


func _dica_peca() -> String:
	var acao := "toque" if _por_toque else "clique"
	var t := "%s — %s para pôr" % [barra.rotulo(peca), acao]
	if construtor.cobrar:
		if construtor.pesquisa != null and not construtor.pesquisa.peca_liberada(peca):
			return "%s — precisa pesquisar: %s (botão Pesquisa)" % [barra.rotulo(peca), construtor.pesquisa.quem_libera(peca)]
		var partes: Array[String] = []
		var c := Construtor.custo_de("esteira_reta" if peca == "esteira" else ("cano_reto" if peca == "cano" else peca))
		for k in c:
			partes.append("%d %s (tem %d)" % [c[k], Registro.itens.get(k, {}).get("nome", k).to_lower(), int(construtor.inventario.get(k, 0))])
		t += " · custo: " + ", ".join(partes)
	if Construtor.arrastavel(peca):
		t += " · arraste para traçar"
	return t + ("" if _por_toque else " · R gira")


func _dica_do_plano() -> void:
	if Time.get_ticks_msec() < _aviso_ate:
		barra.dica(_aviso, false)
		return
	if removendo:
		var n := _plano.size()
		barra.dica("Remover %d" % n if n > 0 else "Nada para remover aqui", false)
		return
	var c := Construtor.contar(_plano)
	var bloqueio := ""
	for it in _plano:
		if it.motivo != "":
			bloqueio = _motivo_legivel(it)
			break
	if bloqueio == "":
		var extra := "  ·  %d peças" % c.ok if c.ok > 1 else ""
		barra.dica(_dica_peca() + extra, false)
	elif c.ok > 0:
		barra.dica("%d ok · %d bloqueada(s): %s" % [c.ok, c.bloqueados, bloqueio], true)
	else:
		barra.dica(bloqueio, true)


func _motivo_legivel(it: Dictionary) -> String:
	if it.motivo == "sem_jazida":
		var nomes: Array[String] = []
		for j in Registro.estruturas.get(it.nome, {}).get("requer_jazida", []):
			nomes.append(Registro.menu.get("jazidas", {}).get(j, j))
		return "Precisa ficar sobre jazida de " + ", ".join(nomes)
	return barra.texto_motivo(it.motivo)


func _process(_d: float) -> void:
	# o aviso ("Construído: 5") some sozinho
	if _aviso != "" and Time.get_ticks_msec() >= _aviso_ate:
		_aviso = ""
		_atualizar()
