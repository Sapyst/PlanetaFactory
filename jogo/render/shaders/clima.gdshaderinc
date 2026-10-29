// Clima (parâmetros globais, escritos por Clima/DesenhoClima): sombra das nuvens correndo com o vento e chão molhado.
global uniform sampler2D nuvem_ruido : filter_linear_mipmap, repeat_enable;
global uniform sampler2D nuvem_mapa : filter_linear_mipmap, repeat_enable;   // R = nuvens, G = rasgos
global uniform float nuvem_cobertura;
global uniform vec2 nuvem_deslocamento;
global uniform float molhado;
global uniform float pocas;           // 0..1: quanto as baixadas já encheram de água da chuva
global uniform float chuva_agora;     // 0..1: força da chuva neste instante (anéis das gotas na água)
global uniform float visao_recursos;  // 0..1: visão de recursos ligada (mapa apagado, jazidas em destaque)
global uniform vec3 sol_dir;          // direção PARA o sol (mundo, normalizada)
const float ALTURA_NUVENS = 90.0;      // camada bem acima do chão

// 0 = sol direto, 1 = nenhuma luz direta. A nuvem é uma camada alta com espessura variável: onde é grossa a luz não
// passa; nas partes finas passa só uma parte (transmissão cai com a espessura); nos rasgos o sol entra direto.
// O ponto é levado até a camada na direção do sol: a sombra cai inclinada como a luz, e os raios de sol
// (raios_sol.gdshader) descem exatamente sobre as manchas claras.
float sombra_nuvem(vec3 p) {
	if (nuvem_cobertura <= 0.01) { return 0.0; }
	vec2 nuvem = p.xz + sol_dir.xz / max(sol_dir.y, 0.2) * (ALTURA_NUVENS - p.y);
	vec2 q = (nuvem - nuvem_deslocamento) * 0.005;          // o mapa repete a cada 200 m
	vec2 m = texture(nuvem_mapa, q).rg;
	float n = m.r + (texture(nuvem_ruido, q * 9.0).r - 0.5) * 0.1;    // franja e fiapos
	// espessura: 0 fora da nuvem, sobe da borda para o miolo; cobertura alta engrossa tudo
	float esp = clamp((n - (1.0 - nuvem_cobertura)) / 0.3, 0.0, 1.0) + max(nuvem_cobertura - 0.75, 0.0) * 2.0;
	float transmite = exp(-3.2 * esp);
	// rasgos: passagem direta (céu quase fechado; some na chuva forte)
	float rasgo = m.g * smoothstep(0.6, 0.72, nuvem_cobertura) * (1.0 - smoothstep(0.86, 0.94, nuvem_cobertura));
	return 1.0 - mix(transmite, 1.0, rasgo);
}

// Visão de recursos: tira a cor e escurece (o que importa — jazidas e nomes — fica por cima).
vec3 apagar_visao(vec3 c, float quanto) {
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	return mix(c, vec3(l * 0.6 + 0.04), visao_recursos * quanto);
}


float _hash_gota(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

// Anéis das gotas batendo na água (poça, rio, lago): em cada célula de ~30 cm uma gota cai em hora sorteada e o
// anel abre e some. Duas grades defasadas para não parecer padrão. Devolve o brilho do anel (0..1).
float aneis_chuva(vec2 p, float t) {
	float s = 0.0;
	for (int k = 0; k < 2; k++) {
		vec2 q = p * 3.3 + float(k) * vec2(0.5, 0.37);
		vec2 cel = floor(q);
		vec2 f = fract(q) - 0.5;
		float h = _hash_gota(cel + float(k) * 17.0);
		float fase = fract(t * (1.1 + 0.5 * h) + h * 7.0);
		vec2 o = vec2(_hash_gota(cel + 3.1), _hash_gota(cel + 9.7)) - 0.5;
		float r = length(f - o * 0.45);
		float anel = 1.0 - smoothstep(0.0, 0.035, abs(r - fase * 0.4));
		s = max(s, anel * (1.0 - fase) * step(0.6, h));
	}
	return s;
}

// Vento (grade: +x leste, +y norte; mundo = (x, −z)). vento_dir = direção × (0,4 + força). rajada = frente da onda
// ao longo do vento (m), amplitude, largura (m): uma faixa de vento mais forte que atravessa o mapa.
global uniform vec2 vento_dir;
global uniform vec3 rajada;
float rajada_em(vec3 mundo) {
	vec2 d = length(vento_dir) > 0.01 ? normalize(vento_dir) : vec2(1.0, 0.0);
	float x = dot(vec2(mundo.x, -mundo.z), d) - rajada.x;
	return rajada.y * exp(-x * x / (rajada.z * rajada.z));
}
// direção do vento no mundo (x, z), unitária
vec2 vento_mundo() {
	vec2 d = length(vento_dir) > 0.01 ? normalize(vento_dir) : vec2(1.0, 0.0);
	return vec2(d.x, -d.y);
}

// Estação para a folhagem: índice (0 primavera, 1 verão, 2 outono, 3 inverno) + fração já passada dela.
global uniform float estacao_atual;
