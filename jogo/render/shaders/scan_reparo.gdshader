shader_type spatial;
// Scan vermelho do drone de reparo sobre a estrutura (sobreposição, material_overlay): uma faixa de laser que corre
// de cima a baixo na altura `altura` (mundo) com uma trama fraca de grade; o resto da peça fica como está.
render_mode unshaded, cull_back, depth_draw_never, shadows_disabled, blend_add;

uniform vec4 cor : source_color = vec4(1.0, 0.05, 0.02, 1.0);
uniform float altura = 0.0;
uniform float forca = 1.0;
uniform float largura = 0.05;

varying vec3 pm;

void vertex() {
	pm = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float d = abs(pm.y - altura);
	float faixa = smoothstep(largura, 0.0, d);
	float rastro = smoothstep(0.6, 0.0, d) * 0.12;
	vec2 g = abs(fract(pm.xz * 6.0) - 0.5);
	float grade = smoothstep(0.47, 0.5, max(g.x, g.y)) * smoothstep(0.5, 0.0, d) * 0.35;
	ALBEDO = cor.rgb * (faixa * 2.2 + rastro + grade) * forca;
}
