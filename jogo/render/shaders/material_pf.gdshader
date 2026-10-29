// Material único do jogo (low-poly facetado). Um só shader → menos trocas de estado na GPU.
// Estruturas trazem uma textura assada (pintura gasta, ferrugem, sujeira: arte/blender_scripts/texturizar.py) no UV;
// o resto da paleta (itens, mapa) continua cor lisa.
// Efeitos ligados por uniform (por material compartilhado, não por objeto):
//   vento   : balança a vegetação (proporcional à altura do vértice), inclinando para onde o vento sopra; mais com
//             vento forte e quando a rajada passa (vento_dir e rajada globais, clima.gdshaderinc)
//   rolagem : lona da esteira andando (UV.y = distância percorrida)
//   pulso   : brilho pulsando (cristais, luzes de status)
//   boiar   : sobe e desce na água (vitória-régia)
//   perfil_folha : folhagem das árvores por receita — cor e queda pela estação (estacao_atual), cada árvore no seu
//             tempo (sorte por instância + onda pelo mapa); copa some com o fogo antes do tronco
//   carbonizada : árvore queimada (de pé ou caída): tudo carvão, sem folha
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
uniform int perfil_folha = -1;      // -1 não é folha; 0 perene, 1 caduca laranja, 2 salgueiro, 3 acácia, 4 caduca amarela
uniform bool carbonizada = false;
instance uniform float trabalho = 1.0;   // 0 = parada (cristal quase apagado) .. 1 = trabalhando
#include "res://render/shaders/clima.gdshaderinc"
global uniform sampler2D fogo_mapa : filter_linear, hint_default_transparent;   // 96×96 tiles em volta da câmera: B queimando, A queimado
global uniform vec2 fogo_origem;

varying float v_dist;
varying vec3 v_mundo;
varying float v_alt;
varying float v_sorte;            // 0..1 por instância (cada árvore muda de folha no seu tempo)              // altura do vértice no modelo (vegetação: base 0 → copa)

void vertex() {
	vec3 mundo = MODEL_MATRIX[3].xyz;                     // por instância (MultiMesh) ou por objeto
	float fase = mundo.x * 0.37 + mundo.z * 0.61;
	if (vento > 0.0) {
		float h = max(VERTEX.y, 0.0);
		float intensidade = clamp(length(vento_dir) - 0.4, 0.0, 1.0);
		float raj = rajada_em(mundo);
		// balanço próprio (cresce com o vento) + inclinação a favor do vento (sutil na brisa, forte na rajada)
		float s = sin(TIME * (1.2 + 1.2 * intensidade) + fase) * 0.6 + sin(TIME * 3.7 + fase * 2.1) * 0.25;
		VERTEX.x += s * h * h * 0.06 * vento * (0.5 + intensidade);
		VERTEX.z += cos(TIME * 1.3 + fase) * h * h * 0.03 * vento * (0.5 + intensidade);
		vec2 dw = vento_mundo();
		float inclina = (0.01 + 0.035 * intensidade + 0.09 * raj) * (0.85 + 0.15 * sin(TIME * 2.3 + fase)) * h * h * vento;
		VERTEX += inverse(mat3(MODEL_MATRIX)) * vec3(dw.x, 0.0, dw.y) * inclina;
	}
	if (boiar > 0.0) {
		VERTEX.y += sin(TIME * 1.2 + fase) * 0.015 * boiar;
	}
	v_dist = rolagem_uv2 ? UV2.y : UV.y;
	v_alt = VERTEX.y;
	v_sorte = fract(sin(dot(mundo.xz, vec2(12.9898, 78.233))) * 43758.5453);
	v_mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// Folhagem pela estação: x = quanto amarelou/secou, y = quanto caiu, z = broto (verde-claro da primavera).
vec3 folhagem(int perfil, float e, float sorte, vec3 p) {
	int est = int(floor(mod(e, 4.0)));
	float f = clamp(fract(e) - sorte * 0.2 + 0.1 + (p.x * 0.0011 - p.z * 0.0007), 0.0, 1.0);
	vec3 r = vec3(0.0);
	if (perfil == 1 || perfil == 4) {               // caduca: outono amarela e cai; inverno nua; primavera brota
		if (est == 2) { r.x = smoothstep(0.05, 0.55, f); r.y = smoothstep(0.6, 0.98, f); }
		else if (est == 3) { r.x = 1.0; r.y = 1.0; }
		else if (est == 0) { r.y = 1.0 - smoothstep(0.02, 0.3, f); r.z = 1.0 - smoothstep(0.25, 0.6, f); }
	} else if (perfil == 2) {                       // salgueiro: amarelado no inverno, perde um pouco
		if (est == 2) { r.x = 0.3 * smoothstep(0.5, 1.0, f); }
		else if (est == 3) { r.x = 0.3 + 0.35 * smoothstep(0.0, 0.3, f); r.y = 0.3 * smoothstep(0.0, 0.3, f); }
		else if (est == 0) { r.x = 0.65 * (1.0 - smoothstep(0.0, 0.25, f)); r.y = 0.3 * (1.0 - smoothstep(0.0, 0.25, f)); }
	} else if (perfil == 3) {                       // acácia: seca e perde metade no verão
		if (est == 1) { r.x = 0.7 * smoothstep(0.1, 0.5, f); r.y = 0.5 * smoothstep(0.2, 0.6, f); }
		else if (est == 2) { r.x = 0.7 * (1.0 - smoothstep(0.0, 0.3, f)); r.y = 0.5 * (1.0 - smoothstep(0.0, 0.3, f)); }
	}
	return r;
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
	float folha_fogo = 0.0;
	if (vento > 0.0) {
		// vegetação: o fogo do tile sobe pela planta (brasa de baixo para cima) e o que queimou vira carvão
		vec4 fg = texture(fogo_mapa, (vec2(v_mundo.x, -v_mundo.z) - fogo_origem) / 96.0);
		float h = clamp(v_alt / 2.2, 0.0, 1.0);
		float queima = smoothstep(0.02, 0.5, fg.b);
		float carvao = max(fg.a * 0.9, queima * smoothstep(h, h + 0.4, 1.0 - fg.b));
		base = mix(base, vec3(0.05, 0.04, 0.035), clamp(carvao, 0.0, 1.0));
		float fl = 0.6 + 0.4 * sin(TIME * 12.0 + v_mundo.x * 5.0 + v_mundo.z * 3.0);
		EMISSION += vec3(1.0, 0.32, 0.04) * queima * smoothstep(0.25, 0.0, abs(h - (1.0 - fg.b))) * fl * 1.6;
		folha_fogo = clamp(fg.a * 1.4 + smoothstep(0.15, 0.6, fg.b), 0.0, 1.0);   // a copa queima primeiro
	}
	if (carbonizada) {
		base = vec3(0.06, 0.05, 0.045) * (0.8 + 0.4 * fract(sin(dot(floor(v_mundo.xz * 6.0), vec2(7.1, 3.7))) * 143.7));
		if (perfil_folha >= 0) {
			discard;
		}
	}
	if (perfil_folha >= 0) {
		// folha é cor lisa e chega em sRGB (as copas antigas têm cor e sombra assadas na textura): passa para linear,
		// escurece embaixo da copa e varia o tom por árvore, para casar com o resto da vegetação
		float por_baixo = smoothstep(-0.6, 0.6, (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y);
		base = pow(base, vec3(2.2)) * (0.62 + 0.3 * por_baixo) * (0.85 + 0.3 * v_sorte);
		vec3 fo = folhagem(perfil_folha, estacao_atual, v_sorte, v_mundo);
		vec3 seca = perfil_folha == 1 ? mix(vec3(0.55, 0.32, 0.03), vec3(0.50, 0.08, 0.02), v_sorte)    // linear
				: perfil_folha == 4 ? vec3(0.66, 0.46, 0.04) : perfil_folha == 2 ? vec3(0.38, 0.34, 0.08) : vec3(0.36, 0.28, 0.07);
		base = mix(base, base * 1.25 + vec3(0.06, 0.1, 0.0), fo.z);
		base = mix(base, seca * (0.62 + 0.3 * por_baixo), fo.x);
		float ruido = fract(sin(dot(floor(v_mundo * 7.0), vec3(12.99, 78.23, 37.71))) * 43758.55);
		if (ruido < max(fo.y, folha_fogo)) {
			discard;                                   // folhas caindo/queimando: a copa vai abrindo até sobrar o galho
		}
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
