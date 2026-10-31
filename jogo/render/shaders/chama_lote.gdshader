// Labareda das máquinas (DesenhoLuzes), em lote: a mesma forma de chama.gdshader, sem partícula. INSTANCE_CUSTOM:
// x = semente, y = força 0..1, z = 1 para labareda de alívio (chaminé: quase apagada, sobe de tempos em tempos, como no estudo).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D ruido : filter_linear_mipmap, repeat_enable;

varying float forca;
varying float semente;

void vertex() {
	semente = INSTANCE_CUSTOM.x;
	float alivio = INSTANCE_CUSTOM.z > 0.5 ? pow(max(sin(TIME * 0.8 + semente * 6.28), 0.0), 12.0) : 0.8 + 0.2 * sin(TIME * 3.1 + semente * 9.0);
	forca = INSTANCE_CUSTOM.y * alivio;
	vec3 o = MODEL_MATRIX[3].xyz;
	float esc = length(MODEL_MATRIX[0].xyz) * (0.45 + 0.55 * alivio);
	vec3 p = o + INV_VIEW_MATRIX[0].xyz * VERTEX.x * esc + INV_VIEW_MATRIX[1].xyz * VERTEX.y * esc;
	POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(p, 1.0));
}

void fragment() {
	if (forca < 0.01) {
		discard;
	}
	float t = 1.0 - UV.y;
	float x = UV.x * 2.0 - 1.0;
	vec2 q = vec2(UV.x * 0.7 + semente * 9.0, t * 1.1 - TIME * 1.7 - semente * 4.0);
	float n1 = texture(ruido, q).r;
	float n2 = texture(ruido, q * 2.4 + vec2(0.31, -TIME * 1.1)).r;
	x += ((n1 - 0.5) * 0.6 + (n2 - 0.5) * 0.3) * t;
	float larg = mix(0.95, 0.06, pow(t, 0.7));
	float corpo = (1.0 - smoothstep(larg * 0.15, larg, abs(x))) * smoothstep(0.0, 0.1, t);
	float topo = 1.0 - smoothstep(0.45, 1.0, t + (n1 - 0.5) * 0.6 + 0.1);
	float a = corpo * topo * smoothstep(0.12, 0.5, n2 + (1.0 - t) * 0.65) * forca;
	float temp = a * (1.0 - t * 0.75) * (1.0 - abs(x) * 0.7);
	vec3 cor = mix(vec3(0.22, 0.015, 0.0), vec3(0.95, 0.22, 0.02), smoothstep(0.05, 0.4, temp));
	cor = mix(cor, vec3(1.0, 0.66, 0.16), smoothstep(0.3, 0.6, temp));
	cor = mix(cor, vec3(1.0, 0.95, 0.72), smoothstep(0.6, 0.9, temp));
	ALBEDO = cor * a * 1.25;
}
