class_name Toque
extends RefCounted
## Medidas de toque em milímetros reais (a tela base tem 720 de altura: em pixel de tela, um limite fixo fica
## minúsculo num celular de alta densidade e qualquer tremida do dedo vira arrasto).

const LIMIAR_MM := 3.2                 ## dedo andou menos que isto = toque; mais = arrasto


## Limiar de arrasto em unidades do viewport (as das posições dos eventos e dos Controls).
static func limiar(vp: Viewport) -> float:
	return mm_em_unidades(vp, LIMIAR_MM)


static func mm_em_unidades(vp: Viewport, mm: float) -> float:
	var dpi := float(DisplayServer.screen_get_dpi())
	if dpi <= 0.0:
		dpi = 160.0
	var px := mm / 25.4 * dpi                                     # pixels físicos
	var janela := float(DisplayServer.window_get_size().y)
	var unidades := vp.get_visible_rect().size.y if vp != null else 720.0
	return maxf(px * unidades / maxf(janela, 1.0), 10.0)


## Há interface de verdade nesta posição (unidades do viewport)? Vale para qualquer painel, menu ou lista, sem cada um
## se registrar: anda pelos CanvasLayer visíveis atrás de um Control que recebe mouse. Existe porque o Godot deixa a roda
## passar pelos Controls (mouse_force_pass_scroll_events ligado de fábrica; a lista no fim da rolagem também não a
## consome), e ela chegava ao _unhandled_input como se o ponteiro estivesse no mapa.
static func sobre_ui(arvore: SceneTree, pos: Vector2) -> bool:
	for c in arvore.root.find_children("*", "CanvasLayer", true, false):
		if c.visible:
			for f in c.get_children():
				if _ui_em(f, pos):
					return true
	return false


static func _ui_em(no: Node, pos: Vector2) -> bool:
	if no is CanvasItem and not (no as CanvasItem).visible:
		return false
	var ct := no as Control
	if ct != null and ct.clip_contents and not ct.get_global_rect().has_point(pos):
		return false                      # fora da área visível da lista: os filhos cortados não contam
	for f in no.get_children():
		if _ui_em(f, pos):
			return true
	return ct != null and ct.mouse_filter != Control.MOUSE_FILTER_IGNORE and ct.get_global_rect().has_point(pos)
