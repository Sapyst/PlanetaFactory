class_name FundoAbstrato
extends Control
## Fundo abstrato procedural para o menu principal: formas geométricas lentas
## flutuando suavemente com as cores da interface de fábrica. Ultra leve para celular.

const NUM_FORMAS := 22
const COR_FUNDO := Color(0.08, 0.09, 0.11)
const COR_GRADE := Color(0.25, 0.28, 0.35, 0.07)

var formas: Array[Dictionary] = []
var _rng := RandomNumberGenerator.new()


func _init() -> void:
	_rng.seed = 42
	_criar_formas()


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if formas.is_empty():
		_rng.seed = 42
		_criar_formas()


func _criar_formas() -> void:
	formas.clear()
	var paleta := [
		Color(0.96, 0.74, 0.24, 0.09),   # destaque / âmbar
		Color(0.55, 0.45, 0.30, 0.11),   # filete / cobre
		Color(0.70, 0.74, 0.78, 0.08),   # info / aço
		Color(1.00, 0.82, 0.25, 0.08),   # ouro / energia
		Color(0.68, 0.60, 0.98, 0.07),   # pesquisa / violeta
		Color(0.42, 0.72, 0.96, 0.08),   # água / azul
		Color(0.50, 0.85, 0.42, 0.07),   # sucesso / verde
	]
	var tipos_lados := [3, 4, 6, 8]
	var tam_ref := size if size.x > 100.0 else Vector2(1280, 720)
	for i in NUM_FORMAS:
		var lados: int = tipos_lados[i % tipos_lados.size()]
		var raio := _rng.randf_range(28.0, 130.0)
		var p := Vector2(_rng.randf_range(0.0, tam_ref.x), _rng.randf_range(0.0, tam_ref.y))
		var ang_vel := _rng.randf_range(0.0, TAU)
		var v_vel := _rng.randf_range(4.0, 12.0)
		var vel := Vector2(cos(ang_vel), sin(ang_vel)) * v_vel
		var rot := _rng.randf_range(0.0, TAU)
		var w_rot := _rng.randf_range(-0.04, 0.04)
		var cor: Color = paleta[i % paleta.size()]
		var preenchido := (i % 3 != 0)
		formas.append({
			"lados": lados,
			"raio": raio,
			"pos": p,
			"vel": vel,
			"rot": rot,
			"w_rot": w_rot,
			"cor": cor,
			"preenchido": preenchido,
		})


func _process(delta: float) -> void:
	avancar(delta)
	queue_redraw()


## Atualiza o movimento das formas geométricas com wrap-around suave nas bordas.
func avancar(dt: float) -> void:
	var tam := size if size.x > 100.0 else Vector2(1280, 720)
	var margem := 150.0
	for f in formas:
		f.pos += f.vel * dt
		f.rot += f.w_rot * dt
		if f.pos.x < -margem:
			f.pos.x = tam.x + margem
		elif f.pos.x > tam.x + margem:
			f.pos.x = -margem
		if f.pos.y < -margem:
			f.pos.y = tam.y + margem
		elif f.pos.y > tam.y + margem:
			f.pos.y = -margem


func _draw() -> void:
	var ret := Rect2(Vector2.ZERO, size)
	draw_rect(ret, COR_FUNDO)

	# Grade geométrica de apoio industrial suave
	var passo := 75.0
	var x := 0.0
	while x < size.x:
		draw_line(Vector2(x, 0), Vector2(x, size.y), COR_GRADE, 1.0)
		x += passo
	var y := 0.0
	while y < size.y:
		draw_line(Vector2(0, y), Vector2(size.x, y), COR_GRADE, 1.0)
		y += passo

	# Formas geométricas flutuantes
	for f in formas:
		var pts := PackedVector2Array()
		var n: int = int(f.lados)
		var r: float = float(f.raio)
		var ang_ini: float = float(f.rot)
		for i in n:
			var a := ang_ini + i * TAU / n
			pts.append(f.pos + Vector2(cos(a), sin(a)) * r)
		if f.preenchido:
			draw_colored_polygon(pts, f.cor)
		var fechado := pts.duplicate()
		fechado.append(pts[0])
		var cor_borda: Color = f.cor
		cor_borda.a = clampf(cor_borda.a * 2.2, 0.12, 0.35)
		draw_polyline(fechado, cor_borda, 1.5, true)
