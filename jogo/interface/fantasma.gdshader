shader_type spatial;
// Fantasma de construção = holograma do modelo 3D (não é imagem): corpo translúcido da cor do estado, borda acesa
// (fresnel), linhas de varredura subindo pelo modelo, uma faixa de "impressão" passando de baixo para cima e um
// leve tremor de sinal. Verde = pode, vermelho = não pode, cinza = já está igual.
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec4 cor : source_color = vec4(0.35, 1.0, 0.55, 1.0);
uniform float base = 0.38;

varying vec3 mundo;

void vertex() {
	mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float borda = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 2.2);
	float linhas = 0.55 + 0.45 * smoothstep(0.35, 0.5, abs(fract(mundo.y * 14.0 - TIME * 1.6) - 0.5));
	float faixa = smoothstep(0.12, 0.0, abs(fract(TIME * 0.45) * 2.2 - 0.1 - (mundo.y - NODE_POSITION_WORLD.y)));
	float sinal = 0.88 + 0.12 * step(0.97, fract(sin(floor(TIME * 18.0)) * 43758.5));
	float a = (base * 0.55 * linhas + borda * 0.9 + faixa * 0.6) * sinal;
	ALBEDO = cor.rgb * a * 1.4;
	ALPHA = clamp(a, 0.0, 1.0) * cor.a;
}
