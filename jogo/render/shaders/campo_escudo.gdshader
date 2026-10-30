shader_type spatial;
// Campo de energia da IA (bolha do gerador de escudo e parede do muro de campo): quase invisível de frente, com a
// borda (fresnel) e uma trama hexagonal fraca em violeta; ondas lentas correm por ela. `forca` 0..1 = carga.
// `impacto` (0..1) acende tudo em âmbar por um instante.
render_mode unshaded, cull_back, depth_draw_never, shadows_disabled, blend_add;
#include "res://render/shaders/campo.gdshaderinc"
