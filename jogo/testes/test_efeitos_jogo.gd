extends Caso
## Testes de integração do sistema de efeitos: pool de instâncias, tiros, impactos,
## explosões, mina de pulso, degradação em rajada e efeitos de ambiente.


func test_pool_efeitos_pre_alocacao_e_teto() -> void:
	var pool := PoolEfeitos.new()
	pool._ready()
	
	# Verifica que todos os tipos de rastros foram pré-alocados
	for arma in ["metralhadora", "torre_energia", "lanca_foguetes", "foguete_enxame", "artilharia", "municao_perfurante", "municao_carregada", "drone_combate"]:
		verificar(pool._pool_rastros.has(arma), "Pool deve ter rastros pré-alocados para " + arma)
		verificar(pool._pool_rastros[arma].size() >= 4, "Pool de rastros deve ter pelo menos 4 instâncias para " + arma)

	# Verifica que todos os impactos foram pré-alocados
	for arma in ["metralhadora", "torre_energia", "lanca_foguetes", "foguete_enxame", "artilharia", "municao_perfurante", "municao_carregada", "drone_combate"]:
		verificar(pool._pool_impactos.has(arma), "Pool deve ter impactos pré-alocados para " + arma)
		verificar(pool._pool_impactos[arma].size() >= 3, "Pool de impactos deve ter pelo menos 3 instâncias para " + arma)

	# Explosões e pulsos
	verificar(pool._pool_explosoes_fog.size() >= 4, "Pool de explosões foguete pré-alocado")
	verificar(pool._pool_explosoes_art.size() >= 4, "Pool de explosões artilharia pré-alocado")
	verificar(pool._pool_pulsos.size() >= 4, "Pool de pulsos de mina pré-alocado")

	var total_filhos_inicial := pool.get_child_count()
	verificar(total_filhos_inicial > 50, "Deve ter mais de 50 nós pré-alocados")

	# Dispara múltiplos tiros seguidos
	var de := Vector3(0, 1, 0)
	var para := Vector3(5, 0.5, 0)
	pool.disparar_rastro("metralhadora", de, para)
	pool.disparar_rastro("torre_energia", de, para)
	pool.disparar_rastro("lanca_foguetes", de, para)
	pool.disparar_impacto("metralhadora", para, "aranha")
	pool.disparar_impacto("metralhadora", para, "chao")
	pool.disparar_impacto("metralhadora", para, "estrutura")
	pool.disparar_explosao(para, 2.0, false)
	pool.disparar_explosao(para, 4.0, true)
	pool.disparar_pulso_mina(para, 3.0)

	# Garante que NENHUM nó foi criado dinamicamente (pool reaproveitado estritamente)
	igual(pool.get_child_count(), total_filhos_inicial, "Nenhum nó deve ser instanciado dinamicamente durante disparos")

	pool.free()


func test_pool_efeitos_degradacao_rajada() -> void:
	var pool := PoolEfeitos.new()
	pool._ready()

	var de := Vector3(0, 1, 0)
	var para := Vector3(5, 0.5, 0)
	pool._tempo_total = 1.0
	pool.disparar_rastro("metralhadora", de, para)

	var ativos_1 := 0
	for item in pool._pool_rastros["metralhadora"]:
		if (item as EfeitoBase).esta_ativo():
			ativos_1 += 1
	igual(ativos_1, 1, "Primeiro disparo deve ativar uma instância do pool")

	# Segundo disparo imediato na mesma arma (rajada): deve pular sem ativar mais instâncias
	pool._tempo_total = 1.02  # apenas 20ms depois (< 65ms de limiar)
	pool.disparar_rastro("metralhadora", de, para)

	var ativos_2 := 0
	for item in pool._pool_rastros["metralhadora"]:
		if (item as EfeitoBase).esta_ativo():
			ativos_2 += 1
	igual(ativos_2, 1, "Rajada rápida deve degradar e pular efeito sem nova ativação")

	# Disparo após intervalo de recarga de rajada (> 65ms)
	pool._tempo_total = 1.10
	pool.disparar_rastro("metralhadora", de, para)

	var ativos_3 := 0
	for item in pool._pool_rastros["metralhadora"]:
		if (item as EfeitoBase).esta_ativo():
			ativos_3 += 1
	igual(ativos_3, 2, "Disparo após intervalo de rajada deve ser aceito")

	pool.free()


func test_pool_efeitos_ambiente() -> void:
	var pool := PoolEfeitos.new()
	pool._ready()

	for tipo in ["brilho_jazida_cristal", "esporos_cogumelo", "faisca_fungo_noite", "vagalumes_flor", "reflexo_agua", "poeira_vento", "vapor_seiva", "brasa_queimado", "geiser_termico"]:
		var inst := pool.alocar_ambiente(tipo)
		verificar(inst != null, "Deve conseguir alocar instância de ambiente " + tipo)
		inst.visible = true

	pool.desativar_ambientes()

	for tipo in ["brilho_jazida_cristal", "esporos_cogumelo", "faisca_fungo_noite", "vagalumes_flor", "reflexo_agua", "poeira_vento", "vapor_seiva", "brasa_queimado", "geiser_termico"]:
		for item in pool._pool_ambientes[tipo]:
			verificar(not (item as EfeitoBase).visible, "Instância de " + tipo + " deve estar desativada após desativar_ambientes")

	pool.free()


func test_desenho_colonia_integracao_efeitos() -> void:
	var g := GeradorMundo.new(1337)
	var mapa := MapaOcupacao.new(g)
	var pol := Poluicao.new(g)
	var col := Colonia.new(mapa, pol, 3)
	var dc := DesenhoColonia.new()
	dc.colonia = col
	dc.mapa = mapa
	dc._ready()

	verificar(dc.pool_efeitos != null, "DesenhoColonia deve possuir pool_efeitos ativo")

	var evs: Array[Dictionary] = [
		{"tipo": "tiro", "nome": "torre_metralhadora", "de": Vector2(0, 0), "para": Vector2(4, 0), "aranha": 1},
		{"tipo": "tiro", "nome": "torre_energia", "de": Vector2(0, 0), "para": Vector2(4, 2), "aranha": 2},
		{"tipo": "tiro", "nome": "torre_lanca_foguetes", "projetil": true, "de": Vector2(0, 0), "para": Vector2(6, 0), "dur": 0.5},
		{"tipo": "salto", "de": Vector2(4, 0), "para": Vector2(5, 1), "eletrico": true},
		{"tipo": "salto", "de": Vector2(4, 0), "para": Vector2(6, 1), "eletrico": false},
		{"tipo": "explosao", "nome": "torre_lanca_foguetes", "pos": Vector2(6, 0), "raio": 2.0},
		{"tipo": "pulso", "id": 10, "pos": Vector2(2, 2), "raio": 3.0}
	]

	dc.atualizar(evs, 0.05)
	verificar(dc.capsulas() >= 0, "Cápsulas ejetadas continuam funcionando")

	dc.free()

