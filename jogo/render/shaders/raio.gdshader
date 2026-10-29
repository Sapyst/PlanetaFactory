// Raio (faísca do acumulador, relâmpago): sem luz, somado (aditivo), cor acima de 1 para o bloom pegar.
// A geometria traz duas camadas na cor do vértice: núcleo branco (alfa 1) e halo ciano largo (alfa baixo) —
// o halo é malha de verdade, então o raio brilha mesmo onde o bloom está desligado (celular).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform float forca = 6.0;

void fragment() {
	ALBEDO = COLOR.rgb * forca * COLOR.a;
}
