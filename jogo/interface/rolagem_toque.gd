class_name RolagemToque
extends Node
## Rolagem por toque de uma lista (filho de um ScrollContainer): arrastar em qualquer ponto da lista rola — também
## começando em cima de um botão —, com embalo ao soltar. Arrasto que passou do limite (Toque.limiar) não aperta o
## botão embaixo do dedo: os botões da lista se ligam por `RolagemToque.so_clique(cb)`.
## A rolagem nativa do ScrollContainer por arrasto fica desligada (senão rolaria em dobro onde não há botão).
## Rola nas duas direções quando o ScrollContainer permite (árvore de pesquisa); listas só na vertical.

static var arrastou := false             ## o toque atual (ou o último) virou arrasto de lista

var _rol: ScrollContainer
var _dedo := -1
var _ini := Vector2.ZERO
var _arrastando := false
var _pos := Vector2.ZERO                 ## rolagem em float (scroll_* são inteiros)
var _vel := Vector2.ZERO                 ## px/s para o embalo
var _t_ultimo := 0


## Botão de lista: só age se o toque não virou arrasto.
static func so_clique(cb: Callable) -> Callable:
	return func():
		if not arrastou:
			cb.call()


func _ready() -> void:
	_rol = get_parent() as ScrollContainer
	_rol.scroll_deadzone = 100000                  # nativa desligada: quem rola é este nó


func _input(e: InputEvent) -> void:
	if e is InputEventScreenTouch:
		if e.pressed:
			if _dedo < 0 and _rol.is_visible_in_tree() and _rol.get_global_rect().has_point(e.position):
				_dedo = e.index
				_ini = e.position
				_arrastando = false
				arrastou = false
				_vel = Vector2.ZERO
				_pos = Vector2(_rol.scroll_horizontal, _rol.scroll_vertical)
		elif e.index == _dedo:
			_dedo = -1
			if _arrastando:
				arrastou = true                    # o botão que receber este soltar não age
				if Time.get_ticks_msec() - _t_ultimo > 60:
					_vel = Vector2.ZERO              # dedo parado antes de soltar: sem embalo
			_arrastando = false
	elif e is InputEventScreenDrag and e.index == _dedo:
		var d: Vector2 = e.position - _ini
		if not _horizontal():
			d.x = 0.0
		if not _arrastando and d.length() > Toque.limiar(get_viewport()):
			_arrastando = true
			arrastou = true
			_pos = Vector2(_rol.scroll_horizontal, _rol.scroll_vertical)
		if _arrastando:
			var agora := Time.get_ticks_msec()
			var dt := maxf((agora - _t_ultimo) / 1000.0, 1.0 / 120.0)
			var rel: Vector2 = -e.relative
			if not _horizontal():
				rel.x = 0.0
			_vel = _vel.lerp(rel / dt, 0.5) if dt < 0.1 else Vector2.ZERO
			_t_ultimo = agora
			_rolar(rel)
			get_viewport().set_input_as_handled()
	elif e is InputEventMouseMotion and e.device == InputEvent.DEVICE_ID_EMULATION and _arrastando:
		get_viewport().set_input_as_handled()        # a interface não vê o dedo andando sobre os botões


func _horizontal() -> bool:
	return _rol.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED


func _process(delta: float) -> void:
	if _dedo >= 0 or _vel.length() < 20.0:
		return
	_rolar(_vel * delta)
	_vel *= exp(-4.0 * delta)


func _rolar(d: Vector2) -> void:
	var lim := Vector2(maxf(0.0, _rol.get_h_scroll_bar().max_value - _rol.size.x), maxf(0.0, _rol.get_v_scroll_bar().max_value - _rol.size.y))
	var antes := _pos
	_pos = (_pos + d).clamp(Vector2.ZERO, lim)
	_rol.scroll_vertical = int(round(_pos.y))
	if _horizontal():
		_rol.scroll_horizontal = int(round(_pos.x))
	if _pos.x == antes.x:
		_vel.x = 0.0
	if _pos.y == antes.y:
		_vel.y = 0.0
