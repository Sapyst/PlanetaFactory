// Marcador de porta pintado no chão (estruturas prontas e fantasma): listras de construção na cor da instância, moldura
// e uma seta discreta no sentido do fluxo. Uma MultiMesh = uma chamada de desenho; tudo aqui, nada por quadro no script.
// A seta aponta para −Z local (o script gira a instância); INSTANCE_CUSTOM.r = 1 → fluido (seta azulada, item = clara).
// Não briga com o chão: fica 5 cm acima e o depth é puxado para a câmera no vertex, o que também cobre emendas de encosta.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, shadows_disabled, fog_disabled, depth_draw_never;

#include "res://render/shaders/clima.gdshaderinc"

uniform float vies_prof = 0.00025;

varying vec3 v_cor;
varying float v_fluido;
varying vec3 v_mundo;

void vertex() {
	v_cor = COLOR.rgb;
	v_fluido = INSTANCE_CUSTOM.r;
	v_mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec4 p = PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	p.z += vies_prof * p.w;                               // Godot usa Z invertido: somar aproxima da câmera
	POSITION = p;
}

// Seta em −Z: haste + ponta, em coordenadas −1..1.
float seta(vec2 q) {
	float ponta = max(abs(q.x) - 0.655 * (q.y + 0.60), q.y + 0.02);
	float haste = max(abs(q.x) - 0.11, abs(q.y - 0.25) - 0.27);
	return min(ponta, haste);
}

void fragment() {
	vec2 q = UV * 2.0 - 1.0;
	float pulso = 0.82 + 0.18 * sin(TIME * 3.2);
	float borda = max(abs(q.x), abs(q.y));
	float fora = smoothstep(1.0, 0.97, borda);
	float moldura = smoothstep(0.80, 0.84, borda);
	float s = fract((UV.x + UV.y) * 2.75);
	float faixa = smoothstep(0.46, 0.5, s) * smoothstep(1.0, 0.96, s);          // listra escura
	vec3 cor = mix(v_cor, v_cor * 0.10, faixa * (1.0 - moldura));
	float d = seta(q / 0.78) * 0.78;                                            // seta discreta: as listras é que chamam
	float seta_miolo = smoothstep(0.012, -0.012, d);
	float seta_contorno = smoothstep(0.06, 0.04, d);
	vec3 cor_seta = mix(vec3(0.82, 0.80, 0.72), vec3(0.36, 0.70, 1.0), v_fluido);
	cor = mix(cor, vec3(0.03), seta_contorno * 0.9);
	cor = mix(cor, cor_seta, seta_miolo);
	ALBEDO = cor * (0.75 + 0.25 * pulso);
	ALPHA = fora * mix(0.62 + 0.14 * pulso, 0.95, max(moldura, seta_contorno)) * visao_dentro(v_mundo);
}
