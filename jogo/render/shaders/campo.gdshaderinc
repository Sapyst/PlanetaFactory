// Campo de energia da IA (código comum da bolha do escudo e da parede do muro de campo).

uniform float forca : hint_range(0.0, 1.0) = 1.0;
uniform float impacto : hint_range(0.0, 1.0) = 0.0;
uniform float escala_hex = 3.0;
uniform vec3 cor : source_color = vec3(0.55, 0.32, 1.0);
uniform vec3 cor_impacto : source_color = vec3(1.0, 0.62, 0.22);

float hex_borda(vec2 p) {
	p *= escala_hex;
	vec2 r = vec2(1.0, 1.7320508);
	vec2 h = r * 0.5;
	vec2 a = mod(p, r) - h;
	vec2 b = mod(p - h, r) - h;
	vec2 g = dot(a, a) < dot(b, b) ? a : b;
	vec2 q = abs(g);
	float d = max(dot(q, normalize(vec2(1.0, 1.7320508))), q.x);
	return smoothstep(0.43, 0.5, d);
}

void fragment() {
	float fr = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 2.5);
	float hex = hex_borda(UV * vec2(6.0, 3.0));
	float onda = 0.5 + 0.5 * sin(UV.y * 18.0 - TIME * 1.6 + UV.x * 6.2831);
	float a = forca * (0.05 + 0.55 * fr + 0.10 * hex * (0.6 + 0.4 * onda));
	vec3 c = mix(cor, cor_impacto, impacto);
	ALBEDO = c * a * (1.0 + 2.0 * impacto);
}
