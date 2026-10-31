// Contorno da estrutura selecionada: âmbar, pulsa de leve e aparece mesmo atrás de outra peça (mais fraco).
shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

void fragment() {
	ALBEDO = vec3(1.0, 0.56, 0.08);
	ALPHA = 0.72 + 0.22 * sin(TIME * 4.0);
}
