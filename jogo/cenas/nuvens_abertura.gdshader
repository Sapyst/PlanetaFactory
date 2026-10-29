// Camada de nuvens do planeta da abertura (por cima da superfície, girando devagar, iluminada pelo sol).
shader_type spatial;
render_mode unshaded, blend_mix, cull_back, depth_draw_never;

uniform sampler2D mapa : source_color, filter_linear_mipmap, repeat_enable;
uniform vec3 sol_dir = vec3(0.3, 0.35, -0.9);
uniform float gira = 0.0;
varying vec3 n_mundo;

void vertex() {
	n_mundo = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = n_mundo;
	float c = cos(1.15), s = sin(1.15);
	vec3 r = vec3(n.x, n.y * c - n.z * s, n.y * s + n.z * c);
	vec2 uv = vec2(atan(r.z, r.x) / 6.2832 + 0.5 + TIME * gira, acos(clamp(r.y, -1.0, 1.0)) / 3.1416);
	vec4 t = texture(mapa, uv);
	float luz = clamp(dot(n, normalize(sol_dir)) * 1.3 + 0.12, 0.02, 1.0);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	ALBEDO = vec3(0.95, 0.96, 0.98) * (0.08 + 0.95 * luz);
	ALPHA = t.a * 0.8;
}
