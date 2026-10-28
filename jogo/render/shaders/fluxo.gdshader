// Caminho das esteiras no modo construção: faixa colorida no meio da esteira com setas (chevrons) correndo no
// sentido do fluxo. UV.x = atravessado (0..1), UV.y = distância ao longo do caminho (1 por tile, contínua entre peças).
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, shadows_disabled, fog_disabled, depth_draw_never;

uniform float forca = 1.0;
uniform float velocidade = 1.2;    // tiles por segundo

void fragment() {
	float u = UV.x * 2.0 - 1.0;                       // -1..1 através da faixa
	float bordas = smoothstep(1.0, 0.8, abs(u));
	float linha = smoothstep(0.32, 0.18, abs(u));     // núcleo da faixa
	// chevron apontando para frente: a ponta adianta no centro
	float f = fract(UV.y * 2.0 - TIME * velocidade * 2.0 + abs(u) * 0.45);
	float seta = smoothstep(0.0, 0.06, f) * smoothstep(0.34, 0.26, f) * smoothstep(0.95, 0.75, abs(u));
	vec3 c = COLOR.rgb;
	ALBEDO = mix(c * 0.9, vec3(1.0), seta * 0.75);
	ALPHA = forca * bordas * clamp(0.35 + 0.35 * linha + 0.6 * seta, 0.0, 1.0);
}
