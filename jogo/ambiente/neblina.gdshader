// Neblina de chão "de verdade" (sem névoa volumétrica, que o renderizador Mobile não tem): uma pilha de fatias
// horizontais finas (uma malha só, um draw) amostrando um campo de densidade pseudo-3D — cada altura lê o ruído
// num deslocamento diferente, então a névoa tem corpo: grossa rente ao chão, topo irregular, e máquinas, árvores
// e trens saem de dentro dela (a base some, o topo fica limpo).
// Dinâmica: dois ruídos correndo em direções/velocidades diferentes (o vento e uma contracorrente) fazem a névoa
// mudar de forma enquanto anda; um ruído largo abre bancos e clareiras.
// Responsiva: calor (máquinas trabalhando, trens) abre buracos que fecham quando a fonte para; sombra das nuvens
// escurece; relâmpago acende por dentro.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://render/shaders/clima.gdshaderinc"

uniform float alfa_fatia = 0.0;      // opacidade de cada fatia (a pilha soma)
uniform float topo = 3.2;            // altura máxima da névoa (m)
uniform vec3 cor_luz : source_color = vec3(0.78, 0.80, 0.82);
uniform vec3 cor_base : source_color = vec3(0.52, 0.56, 0.60);
uniform float flash = 0.0;
uniform vec4 claros[16];             // xy = ponto (mundo xz), z = raio, w = força (0..1)
uniform int n_claros = 0;

varying vec3 mundo;

void vertex() {
	mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float h = clamp(mundo.y / topo, 0.0, 1.0);
	vec2 v = nuvem_deslocamento;
	vec2 q1 = (mundo.xz - v * 0.8) * 0.045 + vec2(h * 0.31, h * 0.17);
	vec2 q2 = (mundo.xz - v * 0.45 + vec2(TIME * 0.35, -TIME * 0.22)) * 0.11 + vec2(-h * 0.43, h * 0.23);
	float n = texture(nuvem_ruido, q1).r * 0.62 + texture(nuvem_ruido, q2).r * 0.38;
	float largo = texture(nuvem_ruido, (mundo.xz - v * 0.3) * 0.007 + vec2(0.13, 0.57)).r;
	float dens = smoothstep(0.0, 0.32, n * 0.8 + largo * 0.65 - 0.42 - h * 0.62);
	for (int i = 0; i < n_claros; i++) {
		float d = distance(mundo.xz, claros[i].xy);
		dens *= mix(1.0, smoothstep(claros[i].z * 0.35, claros[i].z, d), claros[i].w);
	}
	float borda = smoothstep(0.5, 0.32, max(abs(UV.x - 0.5), abs(UV.y - 0.5)));
	vec3 c = mix(cor_base, cor_luz, 0.3 + 0.7 * h);
	c *= 1.0 - 0.3 * sombra_nuvem(mundo);
	c += flash * vec3(0.55, 0.6, 0.72);
	ALBEDO = c;
	ALPHA = dens * alfa_fatia * borda;
}
