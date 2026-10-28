// Clima (parâmetros globais, escritos por Clima/DesenhoClima): sombra das nuvens correndo com o vento e chão molhado.
global uniform sampler2D nuvem_ruido : filter_linear_mipmap, repeat_enable;
global uniform sampler2D nuvem_mapa : filter_linear_mipmap, repeat_enable;   // R = nuvens, G = rasgos
global uniform float nuvem_cobertura;
global uniform vec2 nuvem_deslocamento;
global uniform float molhado;
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
