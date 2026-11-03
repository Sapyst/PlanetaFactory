shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

// Shader procedural para partículas 3D (faíscas, fumaça, poeira, esporos, brasas, vaga-lumes).
// Usa COLOR (albedo + intensidade de emissão no canal A) e INSTANCE_CUSTOM (x=fase, y=temperatura/brilho, z=erosao, w=semente).

uniform vec4 cor_base : source_color = vec4(1.0, 0.7, 0.3, 1.0);
uniform vec4 cor_secundaria : source_color = vec4(0.25, 0.22, 0.20, 1.0);
uniform float forca_emissao : hint_range(0.0, 16.0) = 2.5;
uniform float rugosidade : hint_range(0.0, 1.0) = 0.75;
uniform float escala_ruido : hint_range(0.5, 20.0) = 5.0;

varying vec4 v_custom;
varying vec3 v_pos_local;

float hash31(vec3 p) {
	p = fract(p * vec3(443.897, 441.423, 437.195));
	p += dot(p, p.yzx + 19.19);
	return fract((p.x + p.y) * p.z);
}

float ruido3d(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(hash31(i), hash31(i + vec3(1, 0, 0)), f.x),
		    mix(hash31(i + vec3(0, 1, 0)), hash31(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash31(i + vec3(0, 0, 1)), hash31(i + vec3(1, 0, 1)), f.x),
		    mix(hash31(i + vec3(0, 1, 1)), hash31(i + vec3(1, 1, 1)), f.x), f.y),
		f.z
	);
}

void vertex() {
	v_custom = INSTANCE_CUSTOM;
	v_pos_local = VERTEX;
	// Deformação orgânica leve por partícula para fumaça/terra/esporos não parecerem esferas perfeitas
	float n = ruido3d(VERTEX * escala_ruido + vec3(v_custom.w * 13.7));
	VERTEX += NORMAL * ((n - 0.5) * 0.22 * v_custom.z);
}

void fragment() {
	float n = ruido3d(v_pos_local * escala_ruido + vec3(v_custom.w * 7.3));
	float mistura = clamp(v_custom.y + (n - 0.5) * 0.28, 0.0, 1.0);
	vec3 col = mix(cor_secundaria.rgb, cor_base.rgb, mistura) * COLOR.rgb;
	ALBEDO = col;
	ROUGHNESS = rugosidade;
	float em_fator = forca_emissao * v_custom.y * COLOR.a;
	EMISSION = col * em_fator;
}
