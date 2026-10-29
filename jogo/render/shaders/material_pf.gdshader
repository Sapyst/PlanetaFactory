// Material único do jogo (low-poly facetado). Um só shader → menos trocas de estado na GPU.
// Estruturas trazem uma textura assada (pintura gasta, ferrugem, sujeira: arte/blender_scripts/texturizar.py) no UV;
// o resto da paleta (itens, mapa) continua cor lisa.
// Efeitos ligados por uniform (por material compartilhado, não por objeto):
//   vento   : balança a vegetação (proporcional à altura do vértice)
//   rolagem : lona da esteira andando (UV.y = distância percorrida)
//   pulso   : brilho pulsando (cristais, luzes de status)
//   boiar   : sobe e desce na água (vitória-régia)
//   por_trabalho : cristal das construções — brilho fraco que acende com `trabalho` (por objeto: o Animador manda)
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
uniform sampler2D textura : source_color, filter_linear_mipmap;
uniform bool tem_textura = false;
uniform bool rolagem_uv2 = false;  // modelo texturizado: o UV da lona foi para o 2º canal
uniform bool por_trabalho = false;
instance uniform float trabalho = 1.0;   // 0 = parada (cristal quase apagado) .. 1 = trabalhando
#include "res://render/shaders/clima.gdshaderinc"
global uniform sampler2D fogo_mapa : filter_linear, hint_default_transparent;   // 96×96 tiles em volta da câmera: B queimando, A queimado
global uniform vec2 fogo_origem;

varying float v_dist;
varying vec3 v_mundo;
varying float v_alt;              // altura do vértice no modelo (vegetação: base 0 → copa)

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
	v_dist = rolagem_uv2 ? UV2.y : UV.y;
	v_alt = VERTEX.y;
	v_mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 base = tem_textura ? texture(textura, UV).rgb : cor.rgb;
	if (rolagem != 0.0) {
		// ranhuras transversais andando no sentido do fluxo (4 por metro)
		// o glTF vira o V do UV (cresce da saída para a entrada): somar o tempo leva as ranhuras rumo à saída
		float r = fract((v_dist + TIME * rolagem) * 4.0);
		base *= mix(1.0, 1.9, step(0.82, r));
	}
	// molhado: superfícies de cima escurecem e brilham (água parada); sombra de nuvem tira o sol
	float m = molhado * smoothstep(0.3, 0.9, (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y);
	base *= 1.0 - 0.28 * m;
	base *= 1.0 - 0.6 * sombra_nuvem(v_mundo);
	if (visao_recursos > 0.0) {
		base = apagar_visao(base, 0.6);
	}
	if (vento > 0.0) {
		// vegetação: o fogo do tile sobe pela planta (brasa de baixo para cima) e o que queimou vira carvão
		vec4 fg = texture(fogo_mapa, (vec2(v_mundo.x, -v_mundo.z) - fogo_origem) / 96.0);
		float h = clamp(v_alt / 2.2, 0.0, 1.0);
		float queima = smoothstep(0.02, 0.5, fg.b);
		float carvao = max(fg.a * 0.9, queima * smoothstep(h, h + 0.4, 1.0 - fg.b));
		base = mix(base, vec3(0.05, 0.04, 0.035), clamp(carvao, 0.0, 1.0));
		float fl = 0.6 + 0.4 * sin(TIME * 12.0 + v_mundo.x * 5.0 + v_mundo.z * 3.0);
		EMISSION += vec3(1.0, 0.32, 0.04) * queima * smoothstep(0.25, 0.0, abs(h - (1.0 - fg.b))) * fl * 1.6;
	}
	ALBEDO = base;
	ROUGHNESS = mix(aspereza, 0.45, m * 0.8);   // sem espelho: faceta molhada não pode estourar de branco
	METALLIC = metal;
	float e = forca_emissao;
	if (pulso > 0.0) {
		e *= 0.65 + 0.35 * sin(TIME * 2.4 + NODE_POSITION_WORLD.x);
	}
	if (por_trabalho) {
		e *= mix(0.1, 0.55, trabalho);
	}
	EMISSION += cor_emissao.rgb * e * 0.25;
}
