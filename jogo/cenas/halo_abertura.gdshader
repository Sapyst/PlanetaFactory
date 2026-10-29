// Halo da atmosfera em volta do planeta (esfera um pouco maior, só a borda brilha, somando luz).
shader_type spatial;
render_mode unshaded, blend_add, cull_back, depth_draw_never;

uniform vec3 sol_dir = vec3(0.3, 0.35, -0.9);
varying vec3 n_mundo;

void vertex() {
	n_mundo = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	float borda = pow(1.0 - abs(dot(NORMAL, VIEW)), 9.0);
	float luz = clamp(dot(n_mundo, normalize(sol_dir)) * 1.5 + 0.35, 0.05, 1.2);
	ALBEDO = vec3(0.35, 0.62, 1.0) * borda * luz * 1.6;
}
