// Material único do jogo (low-poly facetado, sem textura). Um só shader → menos trocas de estado na GPU.
// Efeitos ligados por uniform (por material compartilhado, não por objeto):
//   vento   : balança a vegetação (proporcional à altura do vértice)
//   rolagem : lona da esteira andando (UV.y = distância percorrida)
//   pulso   : brilho pulsando (cristais, luzes de status)
//   boiar   : sobe e desce na água (vitória-régia)
shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_schlick_ggx;

uniform vec4 cor : source_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform float aspereza = 0.7;
uniform float metal = 0.0;
uniform vec4 cor_emissao : source_color = vec4(0.0);
uniform float forca_emissao = 0.0;
uniform float vento = 0.0;
uniform float rolagem = 0.0;      // m/s (0 = parada)
uniform float pulso = 0.0;
uniform float boiar = 0.0;

varying float v_dist;

void vertex() {
	vec3 mundo = NODE_POSITION_WORLD;
	float fase = mundo.x * 0.37 + mundo.z * 0.61;
	if (vento > 0.0) {
		float h = max(VERTEX.y, 0.0);
		float s = sin(TIME * 1.6 + fase) * 0.6 + sin(TIME * 3.7 + fase * 2.1) * 0.25;
		VERTEX.x += s * h * h * 0.06 * vento;
		VERTEX.z += cos(TIME * 1.3 + fase) * h * h * 0.03 * vento;
	}
	if (boiar > 0.0) {
		VERTEX.y += sin(TIME * 1.2 + fase) * 0.015 * boiar;
	}
	v_dist = UV.y;
}

void fragment() {
	vec3 base = cor.rgb;
	if (rolagem != 0.0) {
		// ranhuras transversais andando no sentido do fluxo (4 por metro)
		float r = fract((v_dist - TIME * rolagem) * 4.0);
		base *= mix(1.0, 1.9, step(0.82, r));
	}
	ALBEDO = base;
	ROUGHNESS = aspereza;
	METALLIC = metal;
	float e = forca_emissao;
	if (pulso > 0.0) {
		e *= 0.65 + 0.35 * sin(TIME * 2.4 + NODE_POSITION_WORLD.x);
	}
	EMISSION = cor_emissao.rgb * e * 0.25;
}
