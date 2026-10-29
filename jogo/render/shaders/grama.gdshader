// Grama em massa (uma MultiMesh = uma chamada de desenho): cada instância é um tufo de folhas finas. O vento é todo
// na GPU: uma onda rítmica que atravessa o campo (rajadas em faixas) + tremor fino por folha; dobra mais na ponta.
// Cor: base escura (sombra do tufo) → ponta clara, variando por instância (COLOR do MultiMesh).
shader_type spatial;
render_mode cull_disabled, diffuse_lambert, specular_disabled;

uniform vec3 cor_base : source_color = vec3(0.16, 0.24, 0.10);
uniform vec3 cor_ponta : source_color = vec3(0.47, 0.58, 0.28);
uniform vec2 vento_dir = vec2(0.8, 0.6);
uniform float forca = 0.35;
uniform sampler2D mapa_fabrica : filter_nearest, hint_default_black;   // do chunk: R = piso, B = aplainado
uniform vec2 origem_mapa;
uniform sampler2D mapa_ambiente : filter_linear, hint_default_transparent;   // A = queimado, R = sujeira
uniform float raio_vista = 38.0;
global uniform vec3 alvo_camera;

varying float altura;
varying float queimando;
varying vec3 tom;

void vertex() {
	altura = UV.y;                                        // 0 = pé, 1 = ponta
	tom = COLOR.rgb;
	// tufo some (encolhe) sob construção/piso de fábrica — acompanha o piso crescendo — e longe do ponto olhado
	vec3 o = MODEL_MATRIX[3].xyz;
	ivec2 px = clamp(ivec2(floor(vec2(o.x, -o.z) - origem_mapa)), ivec2(0), ivec2(33));
	vec3 fb = texelFetch(mapa_fabrica, px, 0).rgb;
	vec4 amb = texelFetch(mapa_ambiente, px, 0);                      // o tile do próprio tufo (exato)
	float some = smoothstep(0.12, 0.35, max(fb.r, fb.b));
	// queima: só o tufo do tile que queima — escurece e encolhe enquanto o fogo come, some quando acaba
	float q = amb.a;
	queimando = smoothstep(0.51, 0.7, amb.b) * (1.0 - smoothstep(0.6, 0.9, q));   // B ≥ 0,5 = brasa (abaixo é água suja)
	some = max(some, smoothstep(0.1, 0.7, q));
	tom *= mix(vec3(1.0), vec3(0.18, 0.12, 0.08), smoothstep(0.0, 0.25, q));
	tom *= mix(vec3(1.0), vec3(0.72, 0.62, 0.42), smoothstep(0.1, 0.6, amb.r));   // suja: amarelada
	some = max(some, smoothstep(raio_vista - 6.0, raio_vista, distance(o.xz, alvo_camera.xz)));
	VERTEX *= 1.0 - some;
	vec3 mundo = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec2 d = normalize(vento_dir);
	float fase = dot(mundo.xz, d) * 0.35 - TIME * 1.9;
	// rajada: faixas que passam pelo campo; respiração lenta por cima
	float rajada = pow(0.5 + 0.5 * sin(fase), 3.0) * (0.75 + 0.25 * sin(TIME * 0.37 + mundo.x * 0.05));
	float tremor = sin(TIME * 7.0 + mundo.x * 3.1 + mundo.z * 2.3) * 0.08;
	float curva = altura * altura;
	vec2 empurra = d * (rajada * forca + 0.06) * curva + vec2(tremor, -tremor) * curva * 0.5;
	VERTEX.x += (inverse(mat3(MODEL_MATRIX)) * vec3(empurra.x, 0.0, empurra.y)).x;
	VERTEX.z += (inverse(mat3(MODEL_MATRIX)) * vec3(empurra.x, 0.0, empurra.y)).z;
	VERTEX.y -= length(empurra) * 0.35 * curva;           // dobra: a ponta abaixa
	NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.65));
}

void fragment() {
	vec3 c = mix(cor_base, cor_ponta, smoothstep(0.0, 1.0, altura)) * tom;
	ALBEDO = c;
	ROUGHNESS = 0.9;
	BACKLIGHT = vec3(0.25, 0.32, 0.12) * altura;          // luz atravessando a folha
	if (queimando > 0.0) {
		// a frente de fogo sobe pela folha: ponta em brasa, meio laranja, pé ainda escuro
		// cada tufo pega fogo no seu tempo (não acende o tile inteiro de uma vez); a chama sobe pela folha e treme
		float sorte = fract(tom.r * 37.1 + tom.g * 13.7);
		float aceso = smoothstep(sorte * 0.7, sorte * 0.7 + 0.15, queimando);
		float fl = 0.55 + 0.45 * sin(TIME * 14.0 + sorte * 40.0 + altura * 7.0);
		float chama = smoothstep(0.35, 0.95, altura) * aceso * fl;
		vec3 c2 = mix(vec3(0.65, 0.07, 0.01), vec3(1.0, 0.36, 0.04), smoothstep(0.55, 1.0, altura));
		EMISSION = c2 * chama * 1.3;
		ALBEDO *= 1.0 - 0.85 * aceso;
	}
}
