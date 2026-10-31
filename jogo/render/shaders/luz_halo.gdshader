// Brilho falso em lote (DesenhoLuzes): halo redondo no chão onde a luz real do conjunto não chega, e brilho pequeno de pé
// na ponta do poste. Local e somado: não mexe no resto da imagem. INSTANCE_CUSTOM: x = fase, y = tipo (0 fogo, 1 cristal,
// 2 choque, 3 constante). A cor de instância já traz força e hora.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform bool de_pe = false;      // virado para a câmera (ponta do poste)

varying float pulso;

void vertex() {
	float fase = INSTANCE_CUSTOM.x;
	int tipo = int(INSTANCE_CUSTOM.y + 0.5);
	if (tipo == 0) {
		pulso = 0.84 + 0.16 * sin(TIME * 9.0 + fase * 7.0) * sin(TIME * 5.3 + fase * 3.0);
	} else if (tipo == 1) {
		pulso = 0.88 + 0.12 * sin(TIME * 1.5 + fase * 6.28);
	} else if (tipo == 2) {
		float s = fract(TIME * 0.45 + fase);        // flash curto, um a cada ~2 s
		pulso = 0.25 + 2.2 * exp(-s * 40.0);
	} else {
		pulso = 1.0;
	}
	if (de_pe) {
		vec3 o = MODEL_MATRIX[3].xyz;
		float esc = length(MODEL_MATRIX[0].xyz);
		vec3 p = o + INV_VIEW_MATRIX[0].xyz * VERTEX.x * esc + INV_VIEW_MATRIX[1].xyz * VERTEX.y * esc;
		POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(p, 1.0));
	}
}

void fragment() {
	float r = length(UV * 2.0 - 1.0);
	float a = 1.0 - smoothstep(0.0, 1.0, r);
	ALBEDO = COLOR.rgb * COLOR.a * a * a * pulso;
}
