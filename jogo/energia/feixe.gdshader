shader_type spatial;
// Ligação sem fio: feixe ciano tracejado; os traços correm ao longo da ligação.
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

void fragment() {
	float traco = step(0.45, fract(UV.x * 1.2 - TIME * 2.0));
	float borda = 1.0 - abs(UV.y * 2.0 - 1.0);
	ALBEDO = vec3(0.35, 0.95, 1.0) * (0.35 + 0.65 * traco) * borda;
	ALPHA = 1.0;
}
