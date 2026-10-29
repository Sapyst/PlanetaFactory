class_name Montagem
extends Node
## Animação de construção (só peças novas, ~1,6 s): a base sobe do chão, cada parte desce e encaixa em sequência
## (de baixo para cima, com um leve quique), os pistões batem até o fundo e travam, e no fim o Animador assume.
## Pura transformação dos nós do modelo (não cria malha nova: nada sobrepõe).

const DURACAO_BASE := 0.45
const PASSO := 0.16          ## atraso entre uma parte e a próxima
const QUEDA := 0.55          ## de quanto acima cada parte vem

var animador: Animador
var _t := 0.0
var _raiz: Node3D
var _pecas: Array[Dictionary] = []      ## {no, base: Transform3D, ini: float, pistao}
var _fim := 0.0


func _ready() -> void:
	_raiz = get_parent() as Node3D
	var nos: Array[Node3D] = []
	_coletar(_raiz, nos)
	nos.sort_custom(func(a, b): return a.global_position.y < b.global_position.y)
	var k := 0
	for n in nos:
		var pistao := n.name.contains("pistao")
		_pecas.append({"no": n, "base": n.transform, "ini": DURACAO_BASE * 0.6 + k * PASSO + (0.25 if pistao else 0.0), "pistao": pistao})
		k += 1
	_fim = DURACAO_BASE
	for p in _pecas:
		_fim = maxf(_fim, p.ini + 0.5)
	if animador != null:
		animador.process_mode = Node.PROCESS_MODE_DISABLED
	_aplicar()


## Partes móveis do modelo (filhos do corpo); o corpo é a base.
func _coletar(n: Node, out: Array[Node3D]) -> void:
	for c in n.get_children():
		if c is Node3D and c != _raiz and not (c is Animador):
			var mi := c as Node3D
			if mi.get_parent() != _raiz:
				out.append(mi)
			_coletar(c, out)


func _process(delta: float) -> void:
	_t += delta
	_aplicar()
	if _t >= _fim:
		_raiz.scale = Vector3.ONE
		for p in _pecas:
			(p.no as Node3D).transform = p.base
		if animador != null:
			animador.process_mode = Node.PROCESS_MODE_INHERIT
		queue_free()


func _aplicar() -> void:
	# base: sobe do chão (escala em y com quique)
	var u := clampf(_t / DURACAO_BASE, 0.0, 1.0)
	var sy := _volta(u)
	_raiz.scale = Vector3(lerpf(0.85, 1.0, u), maxf(0.02, sy), lerpf(0.85, 1.0, u))
	for p in _pecas:
		var no: Node3D = p.no
		var b: Transform3D = p.base
		var v := clampf((_t - float(p.ini)) / 0.45, 0.0, 1.0)
		if v <= 0.0:
			no.visible = false
			continue
		no.visible = true
		if p.pistao:
			# o pistão desce de cima, bate no fundo e volta a meio curso (trava)
			var bate := -0.15 * sin(v * PI) if v > 0.5 else 0.0
			no.transform = Transform3D(b.basis, b.origin + Vector3(0, (1.0 - _volta(v)) * QUEDA * 0.6 + bate, 0))
		else:
			var gira := (1.0 - v) * 0.9
			no.transform = Transform3D(Basis(Vector3.UP, gira) * b.basis, b.origin + Vector3(0, (1.0 - _volta(v)) * QUEDA, 0))


## 0→1 com um leve passar do ponto e voltar (encaixe).
static func _volta(x: float) -> float:
	var c1 := 1.7
	var c3 := c1 + 1.0
	return 1.0 + c3 * pow(x - 1.0, 3.0) + c1 * pow(x - 1.0, 2.0)
