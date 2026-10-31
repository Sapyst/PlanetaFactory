shader_type spatial;
// Fantasma de quem não pode construir: tinge de vermelho-escuro por cima do mundo (mistura normal, porque o aditivo do
// fantasma.gdshader só clareia). Borda um pouco mais forte, varredura lenta. realce = tile que atrapalha: chapado,
// com hachura e pulso, para saltar da pegada.
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec4 cor : source_color = vec4(0.17, 0.006, 0.005, 0.78);
uniform bool realce = false;

varying vec3 mundo;

void vertex() {
	mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (realce) {
		float s = fract((mundo.x - mundo.z) * 3.0);
		float hachura = 0.70 + 0.30 * step(0.5, s);
		ALBEDO = cor.rgb * hachura * (0.8 + 0.2 * sin(TIME * 5.0));
		ALPHA = cor.a;
	} else {
		float borda = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 2.0);
		float linhas = 0.85 + 0.15 * smoothstep(0.35, 0.5, abs(fract(mundo.y * 10.0 - TIME * 0.8) - 0.5));
		ALBEDO = mix(cor.rgb, cor.rgb * 3.5, borda) * linhas;
		ALPHA = clamp(cor.a * (0.72 + 0.5 * borda), 0.0, 1.0);
	}
}
