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
