// Raios de sol passando pelas nuvens (crepusculares), sem pós-processo: pilha de fatias horizontais somando luz.
// Cada ponto de cada fatia pergunta "a linha daqui até o sol passa por um buraco na nuvem?" (mesma conta da sombra
// das nuvens) — empilhadas, as respostas viram feixes inclinados na direção do sol que descem e acendem as manchas
// claras do chão. Poeira fina dá textura ao feixe; somem nas pontas da pilha e na borda do quad.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://render/shaders/clima.gdshaderinc"

uniform float forca = 0.0;           // por fatia
uniform float topo = 18.0;
uniform vec3 cor : source_color = vec3(1.0, 0.92, 0.75);

varying vec3 mundo;

void vertex() {
	mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float h = clamp(mundo.y / topo, 0.0, 1.0);
	float luz = 1.0 - sombra_nuvem(mundo);
	luz = luz * luz * luz;      // só a passagem direta vira feixe; luz filtrada pela nuvem fina quase não aparece
	// poeira/umidade no ar: o feixe não é liso
	vec2 q = (mundo.xz + sol_dir.xz * mundo.y) * 0.07 + vec2(TIME * 0.01, 0.0);
	float poeira = 0.65 + 0.7 * texture(nuvem_ruido, q).r;
	float pontas = smoothstep(0.0, 0.12, h) * smoothstep(1.0, 0.3, h);
	float borda = smoothstep(0.5, 0.3, max(abs(UV.x - 0.5), abs(UV.y - 0.5)));
	ALBEDO = cor * luz * poeira * pontas * borda * forca;
}
