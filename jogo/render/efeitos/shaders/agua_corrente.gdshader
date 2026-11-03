shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

// Shader procedural de água corrente com ondulação de correnteza, espuma ao redor de obstáculos e reflexo solar/lunar.

uniform vec4 cor_agua_rasa : source_color = vec4(0.12, 0.42, 0.48, 1.0);
uniform vec4 cor_agua_funda : source_color = vec4(0.06, 0.22, 0.32, 1.0);
uniform vec4 cor_reflexo : source_color = vec4(0.85, 0.95, 1.0, 1.0);
uniform float velocidade_corrente : hint_range(0.1, 5.0) = 1.6;
uniform float fase_manual : hint_range(0.0, 10.0) = 0.0;

float hash21(vec2 p) {
	p = fract(p * vec2(234.34, 435.345));
	p += dot(p, p + 34.23);
	return fract(p.x * p.y);
}

float ruido2d(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(hash21(i), hash21(i + vec2(1.0, 0.0)), f.x),
		mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), f.x),
		f.y
	);
}

void vertex() {
	float t = TIME * velocidade_corrente + fase_manual;
	float onda = sin(VERTEX.x * 3.5 - t * 2.4) * 0.025 + cos(VERTEX.z * 4.2 + t * 1.8) * 0.018;
	VERTEX.y += onda;
}

void fragment() {
	float t = TIME * velocidade_corrente + fase_manual;
	vec2 uv_corr = UV * vec2(6.0, 4.0) + vec2(-t * 0.85, t * 0.15);
	float n1 = ruido2d(uv_corr);
	float n2 = ruido2d(uv_corr * 2.3 + vec2(t * 0.5, -t * 0.35));
	float crista = smoothstep(0.62, 0.84, n1 * 0.6 + n2 * 0.4);
	// Esteira espumosa perto dos seixos centrais
	float dist_pedra1 = length(UV - vec2(0.45, 0.50));
	float dist_pedra2 = length(UV - vec2(0.62, 0.42));
	float espuma_pedra = smoothstep(0.16, 0.07, dist_pedra1) + smoothstep(0.13, 0.05, dist_pedra2);
	float reflexo = clamp(crista + espuma_pedra * 0.75, 0.0, 1.0);

	vec3 base = mix(cor_agua_funda.rgb, cor_agua_rasa.rgb, n1);
	ALBEDO = mix(base, cor_reflexo.rgb, reflexo * 0.78);
	ROUGHNESS = mix(0.14, 0.04, reflexo);
	METALLIC = 0.25;
	EMISSION = cor_reflexo.rgb * (reflexo * 0.65);
}
