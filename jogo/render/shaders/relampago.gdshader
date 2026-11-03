// Relâmpago da tempestade (DesenhoClima): fita virada para a câmera, UV.x atravessa a fita (0 e 1 nas bordas).
// Núcleo branco fino no eixo e halo azulado largo caindo em gaussiana — nada de borda dura nem alfa chapado:
// o brilho é malha, então aparece igual no celular (sem bloom); no PC a cor acima de 1 ainda acende o bloom.
// Somado (aditivo), sem luz, sem escrever profundidade. `brilho` apaga o golpe (0..1); COLOR.a = força do ramo.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform float brilho = 1.0;
uniform float forca = 3.2;
uniform vec3 cor_halo : source_color = vec3(0.42, 0.58, 1.0);

void fragment() {
	float d = abs(UV.x - 0.5) * 2.0;             // 0 no eixo, 1 na borda da fita
	float nucleo = exp(-d * d * 90.0);
	float halo = exp(-d * d * 4.5) * 0.2;
	vec3 cor = mix(cor_halo, vec3(1.0), nucleo);
	ALBEDO = cor * (nucleo + halo) * COLOR.a * brilho * forca;
}
