shader_type spatial;
// Fantasma de construção: translúcido, sem luz, borda mais forte (fresnel) e um brilho que respira.
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;

uniform vec4 cor : source_color = vec4(0.35, 1.0, 0.55, 1.0);
uniform float base = 0.38;

void fragment() {
	float borda = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 2.0);
	float respira = 0.06 * sin(TIME * 5.0);
	ALBEDO = cor.rgb;
	ALPHA = clamp(base + borda * 0.45 + respira, 0.0, 1.0) * cor.a;
}
