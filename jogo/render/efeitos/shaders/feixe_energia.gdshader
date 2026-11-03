shader_type spatial;
render_mode unshaded, cull_disabled, blend_add, depth_draw_never;

// Shader procedural para feixes de energia, traçantes, arcos de plasma e anéis de onda de choque no mundo.

uniform vec4 cor_nucleo : source_color = vec4(0.95, 0.98, 1.0, 1.0);
uniform vec4 cor_borda : source_color = vec4(0.20, 0.78, 1.0, 1.0);
uniform float intensidade : hint_range(0.0, 12.0) = 3.5;
uniform float frequencia : hint_range(0.5, 30.0) = 8.0;
uniform float velocidade : hint_range(0.0, 30.0) = 12.0;
uniform float progresso : hint_range(0.0, 1.0) = 0.5;

void fragment() {
	float pulso = 0.75 + 0.25 * sin(UV.y * frequencia * 6.28318 - TIME * velocidade);
	float borda = 1.0 - abs(UV.x * 2.0 - 1.0);
	borda = pow(clamp(borda, 0.0, 1.0), 1.35);
	float env = sin(clamp(progresso, 0.0, 1.0) * 3.14159);
	vec3 cor = mix(cor_borda.rgb, cor_nucleo.rgb, pow(borda, 2.2));
	ALBEDO = cor * intensidade * pulso * COLOR.rgb;
	ALPHA = clamp(borda * pulso * COLOR.a * max(0.25, env), 0.0, 1.0);
}
