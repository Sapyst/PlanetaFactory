// Chão por chunk: cada tile escolhe uma camada do Texture2DArray (bioma, jazida, praia, água).
// Texturas em loop (geradas sem emenda) repetem a cada 4 m; ruído de detalhe quebra a repetição.
// Bordas orgânicas: em terra, a camada é lida do mapa 34×34 do chunk numa posição deformada por ruído, e duas
// leituras com deformações diferentes se misturam — a troca de bioma vira uma faixa irregular e suave, não degrau.
// Água: camadas ≥ 'primeira_agua' ondulam e brilham; rio corre na direção da correnteza (COLOR.gb).
shader_type spatial;
render_mode cull_back, diffuse_lambert;

uniform sampler2DArray texturas : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D detalhe : filter_linear_mipmap, repeat_enable;
uniform sampler2D mapa_camadas : filter_nearest;
uniform vec2 origem_mapa;          // tile (grade) do pixel (0, 0) do mapa de camadas
uniform sampler2D mapa_fabrica : filter_nearest;   // 1 = tile com construção (mesma grade do mapa de camadas)
uniform float camada_piso = 9.0;
uniform float camada_jazida = 7.0;  // zona de minério nunca vira piso
uniform float primeira_agua = 8.0;
uniform float escala = 0.25;
#include "res://render/shaders/clima.gdshaderinc"

varying flat float camada;
varying flat vec3 fluxo;           // xy = direção da correnteza (grade), z = 1 se rio
varying vec3 mundo;

void vertex() {
	camada = floor(COLOR.r * 255.0 + 0.5);
	fluxo = vec3(COLOR.g * 2.0 - 1.0, COLOR.b * 2.0 - 1.0, COLOR.a);
	mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (camada >= primeira_agua) {
		VERTEX.y += sin(TIME * 0.9 + mundo.x * 0.7 + mundo.z * 0.5) * 0.02;
	}
}

float fabrica_em(vec2 grade) {
	ivec2 px = clamp(ivec2(floor(grade - origem_mapa)), ivec2(0), ivec2(33));
	return texelFetch(mapa_fabrica, px, 0).r;
}

float camada_em(vec2 grade) {
	ivec2 px = clamp(ivec2(floor(grade - origem_mapa)), ivec2(0), ivec2(33));
	return floor(texelFetch(mapa_camadas, px, 0).r * 255.0 + 0.5);
}

void fragment() {
	vec2 grade = vec2(mundo.x, -mundo.z);
	vec2 uv = mundo.xz * escala;
	float d = texture(detalhe, mundo.xz * 0.031).r;
	vec3 c;
	if (camada >= primeira_agua) {
		vec2 corre = fluxo.z > 0.5 ? vec2(fluxo.x, -fluxo.y) * 0.35 : vec2(0.02, 0.013);
		uv += corre * TIME;
		c = texture(texturas, vec3(uv, camada)).rgb;
	} else {
		// duas leituras deformadas (ruído) do mapa de camadas; água vizinha não invade a terra
		vec2 w1 = vec2(texture(detalhe, grade * 0.06).r, texture(detalhe, grade * 0.06 + vec2(0.37, 0.71)).r) - 0.5;
		vec2 w2 = vec2(texture(detalhe, grade * 0.17 + vec2(0.53, 0.19)).r, texture(detalhe, grade * 0.17 + vec2(0.11, 0.83)).r) - 0.5;
		float a = camada_em(grade + w1 * 2.6 + w2 * 0.6);
		float b = camada_em(grade + w2 * 1.6);
		if (a >= primeira_agua) { a = camada; }
		if (b >= primeira_agua) { b = camada; }
		vec3 ca = texture(texturas, vec3(uv, a)).rgb;
		vec3 cb = texture(texturas, vec3(uv, b)).rgb;
		c = mix(ca, cb, 0.45);
		// piso de fábrica: o mapa já vem espalhado 2 tiles em volta das construções (forte perto, fraco longe);
		// 4 leituras deformadas dão a borda irregular e suave. Jazida nunca vira piso.
		float f = fabrica_em(grade + w1 * 1.3) + fabrica_em(grade + w2 * 1.0)
				+ fabrica_em(grade + vec2(w2.y, -w1.x) * 1.4) + fabrica_em(grade);
		f = smoothstep(0.18, 0.55, f * 0.25);
		if (camada == camada_jazida || a == camada_jazida) { f = 0.0; }   // recurso fica à vista
		if (f > 0.0) {
			vec3 piso = texture(texturas, vec3(grade * vec2(0.25, -0.25), camada_piso)).rgb;
			c = mix(c, piso, f);
		}
	}
	c *= 0.88 + 0.24 * d;
	float poca = 0.0;
	if (camada < primeira_agua && molhado > 0.0) {
		// chão molhado escurece; nas partes baixas do ruído junta poça (lisa, reflete o céu)
		poca = smoothstep(0.62, 0.70, 1.0 - d) * smoothstep(0.35, 1.0, molhado);
		c *= 1.0 - 0.30 * molhado - 0.15 * poca;
	}
	c *= 1.0 - 0.6 * sombra_nuvem(mundo);
	if (visao_recursos > 0.0) {
		c = apagar_visao(c, camada == camada_jazida ? 0.0 : 0.85);
	}
	ALBEDO = c;
	if (camada >= primeira_agua) {
		ROUGHNESS = 0.08;
		SPECULAR = 0.8;
		vec2 corre_onda = fluxo.z > 0.5 ? vec2(fluxo.x, -fluxo.y) * 0.12 : vec2(0.05, 0.0);
		float onda = texture(detalhe, mundo.xz * 0.12 + corre_onda * TIME).r;
		ALBEDO = c * (0.9 + 0.25 * onda);
	} else {
		ROUGHNESS = mix(mix(0.92, 0.55, molhado), 0.06, poca);
		SPECULAR = 0.5 + 0.4 * poca;
	}
}
