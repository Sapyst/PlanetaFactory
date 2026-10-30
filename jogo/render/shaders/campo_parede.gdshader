shader_type spatial;
// Parede do muro de campo: o mesmo campo da bolha (campo.gdshaderinc), visível dos dois lados.
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled, blend_add;
#include "res://render/shaders/campo.gdshaderinc"
