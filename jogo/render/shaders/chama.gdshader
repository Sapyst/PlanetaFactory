// Chama procedural (partícula): quad de pé virado para a câmera só em Y. Forma de labareda — base larga afunilando
// no topo —, distorcida por dois ruídos subindo (tremor de calor) e dobrada pelo vento na ponta; bordas comidas pelo
// ruído (línguas). Cor por "temperatura": miolo da base branco-amarelo → laranja → vermelho → escuro na ponta.
// Mistura ADITIVA: chamas que se juntam somam luz, então o aglomerado fica mais quente/claro, como fogo de verdade.
// COLOR (do degradê da partícula): r = vida 0..1, a = força.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D ruido : filter_linear_mipmap, repeat_enable;
uniform vec2 vento = vec2(0.0);      // direção × força no plano (mundo xz)

varying float vida;
varying float forca;
varying float semente;

void vertex() {
	vida = COLOR.r;
	forca = COLOR.a;
	vec3 o = MODEL_MATRIX[3].xyz;
	semente = fract(sin(dot(o.xz + vec2(o.y), vec2(12.9898, 78.233))) * 43758.5453);
	float esc = length(MODEL_MATRIX[0].xyz);
	// de frente para a câmera (vista de cima a chama não achata); "cima" da chama = cima da tela
	vec3 lado = INV_VIEW_MATRIX[0].xyz;
	vec3 cima = INV_VIEW_MATRIX[1].xyz;
	float t = 1.0 - UV.y;                                  // 0 = base, 1 = ponta
	vec3 p = o + lado * VERTEX.x * esc + cima * VERTEX.y * esc;
	vec3 w3 = vec3(vento.x, 0.0, vento.y);
	p += (lado * dot(w3, lado) + cima * dot(w3, cima) * 0.5) * t * t * 0.5 * esc;   // o vento deita a ponta
	POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(p, 1.0));
}

void fragment() {
	float t = 1.0 - UV.y;
	float x = UV.x * 2.0 - 1.0;
	vec2 q = vec2(UV.x * 0.7 + semente * 9.0, t * 1.1 - TIME * 1.7 - semente * 4.0);
	float n1 = texture(ruido, q).r;
	float n2 = texture(ruido, q * 2.4 + vec2(0.31, -TIME * 1.1)).r;
	x += ((n1 - 0.5) * 0.6 + (n2 - 0.5) * 0.3) * t;           // tremor cresce para cima
	float larg = mix(0.95, 0.06, pow(t, 0.7));
	float corpo = 1.0 - smoothstep(larg * 0.15, larg, abs(x));
	corpo *= smoothstep(0.0, 0.1, t);
	float topo = 1.0 - smoothstep(0.45, 1.0, t + (n1 - 0.5) * 0.6 + vida * 0.35);
	float a = corpo * topo * smoothstep(0.12, 0.5, n2 + (1.0 - t) * 0.65) * forca;
	float temp = a * (1.0 - t * 0.75) * (1.0 - abs(x) * 0.7) * (1.0 - vida * 0.5);
	vec3 cor = mix(vec3(0.22, 0.015, 0.0), vec3(0.95, 0.22, 0.02), smoothstep(0.05, 0.4, temp));
	cor = mix(cor, vec3(1.0, 0.66, 0.16), smoothstep(0.3, 0.6, temp));
	cor = mix(cor, vec3(1.0, 0.95, 0.72), smoothstep(0.6, 0.9, temp));
	ALBEDO = cor * a * 1.25;
	ALPHA = a;
}
