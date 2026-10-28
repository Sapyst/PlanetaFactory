extends Caso
## Ferramenta de construção do jogador: peça solta, arrasto de esteira/cano em L, pontas automáticas,
## troca por cima, remoção em retângulo, limpar obstáculo e desfazer.

func _c() -> Construtor:
	return Construtor.new(MapaOcupacao.new(GeradorMundo.new(1337)))


func _nomes(plano: Array[Dictionary]) -> Array[String]:
	var out: Array[String] = []
	for it in plano:
		out.append(it.nome)
	return out


## Primeiro tile fora do raio livre do spawn que tem obstáculo natural 1×1.
func _obstaculo_perto(c: Construtor) -> Vector2i:
	for r in range(8, 40):
		for x in range(-r, r + 1):
			var t := Vector2i(x, r)
			var o := c.mapa.gerador.distribuicao.obstaculo(t)
			if not o.is_empty() and o.area == Vector2i(1, 1):
				return t
	return Vector2i(9999, 9999)


func test_rotacao_e_fluxo() -> void:
	for d in 4:
		igual(Construtor.fluxo_da_rot(Construtor.rot_do_fluxo(d)), d, "ida e volta d=%d" % d)
		# a porta de saída da esteira reta girada aponta mesmo para d
		var porta: Dictionary = Registro.modelos["esteira_reta"].portas[1]
		var pm := Grade.porta_no_mundo(porta, Vector2i.ZERO, Vector2i.ONE, Construtor.rot_do_fluxo(d))
		igual(pm.dir, Grade.DIRECOES[d], "saída da reta aponta para o fluxo d=%d" % d)


func test_caminho_l() -> void:
	var cam := Construtor.caminho_l(Vector2i(0, 0), Vector2i(3, -2))
	igual(cam.size(), 6, "3 + 2 passos + início")
	igual(cam[3], Vector2i(3, 0), "eixo maior primeiro")
	igual(cam[5], Vector2i(3, -2))
	for i in range(1, cam.size()):
		igual((cam[i] - cam[i - 1]).abs().x + (cam[i] - cam[i - 1]).abs().y, 1, "passos vizinhos")
	igual(Construtor.caminho_l(Vector2i(2, 2), Vector2i(2, 2)).size(), 1)
	var reto := Construtor.caminho_reto(Vector2i(0, 0), Vector2i(1, 5))
	igual(reto[-1], Vector2i(0, 5), "linha reta projeta no eixo dominante")


func test_arrasto_esteira_com_curva() -> void:
	var c := _c()
	# leste 3 tiles, depois norte 2: início, reta, reta, curva à esquerda, reta, fim
	var p := c.plano_linha("esteira", Vector2i(-4, -4), Vector2i(-1, -2), 0)
	igual(_nomes(p), ["esteira_inicio", "esteira_reta", "esteira_reta", "esteira_curva_esq", "esteira_reta", "esteira_fim"] as Array[String])
	verificar(Construtor.pode_tudo(p), "spawn livre: tudo verde")
	igual(p[0].rot, Construtor.rot_do_fluxo(1), "flui para leste")
	igual(p[4].rot, Construtor.rot_do_fluxo(0), "depois da curva flui para o norte")
	# curva: a saída real da peça girada aponta para o norte
	var cv: Dictionary = p[3]
	var sai: Dictionary = Registro.modelos["esteira_curva_esq"].portas[1]
	igual(Grade.porta_no_mundo(sai, cv.minimo, Vector2i.ONE, cv.rot).dir, Grade.DIRECOES[0], "curva esquerda sai para o norte")
	# virando para a direita
	var q := c.plano_linha("esteira", Vector2i(0, 0), Vector2i(2, -2), 0)
	igual(q[2].nome, "esteira_curva_dir", "leste → sul é curva à direita")
	var sai_d: Dictionary = Registro.modelos["esteira_curva_dir"].portas[1]
	igual(Grade.porta_no_mundo(sai_d, q[2].minimo, Vector2i.ONE, q[2].rot).dir, Grade.DIRECOES[2], "curva direita sai para o sul")


func test_juncoes_do_caminho_batem() -> void:
	# em qualquer arrasto, a saída de cada peça encosta na entrada da próxima
	var c := _c()
	for alvo in [Vector2i(5, 3), Vector2i(-4, 6), Vector2i(3, -5), Vector2i(-6, -2), Vector2i(0, 4)]:
		var p := c.plano_linha("esteira", Vector2i.ZERO, alvo, 0)
		for i in p.size() - 1:
			var a: Dictionary = p[i]
			var b: Dictionary = p[i + 1]
			var sai := _porta(a, "SAI")
			var ent := _porta(b, "ENT")
			if not verificar(not sai.is_empty() and not ent.is_empty(), "peças do meio têm entrada e saída (%s→%s)" % [a.nome, b.nome]):
				continue
			perto(sai.pos.distance_to(ent.pos), 0.0, 1e-5, "saída de %s encosta na entrada de %s (alvo %s)" % [a.nome, b.nome, alvo])
			igual(sai.dir, -ent.dir, "portas de frente uma para a outra")


func _porta(it: Dictionary, io: String) -> Dictionary:
	for p in Registro.modelos[it.nome].portas:
		if p.io == io:
			return Grade.porta_no_mundo(p, it.minimo, Vector2i.ONE, it.rot)
	return {}


func test_pontas_conforme_vizinhos() -> void:
	var c := _c()
	igual(c.plano_peca("esteira", Vector2i(0, 0), 0)[0].nome, "esteira_reta", "tile solto sem vizinho = reta")
	# esteira saindo do extrator (saída no meio da borda sul): começa como reta, não como início
	c.executar(c.plano_peca("extrator_cristal", Vector2i(15, 5), 0))
	var p := c.plano_linha("esteira", Vector2i(15, 3), Vector2i(15, 0), 0)
	igual(p[0].nome, "esteira_reta", "alimentada pela máquina")
	igual(p[-1].nome, "esteira_fim", "termina em para-choque")
	c.executar(p)
	# continuar a partir do fim: o fim vira reta sozinho
	var q := c.plano_linha("esteira", Vector2i(15, -1), Vector2i(15, -3), 2)
	igual(q[0].nome, "esteira_reta", "continua uma esteira existente")
	var rel := c.executar(q)
	igual(c._estrutura_em(Vector2i(15, 0)).nome, "esteira_reta", "o fim antigo virou reta")
	igual(rel.removidos.size(), 1, "relatório traz a troca")
	igual(c._estrutura_em(Vector2i(15, -3)).nome, "esteira_fim", "a nova ponta é fim")
	# braço na frente: a esteira termina em fim (o braço pega do para-choque)
	c.executar(c.plano_peca("braco", Vector2i(15, -5), 2))
	var r := c.plano_linha("esteira", Vector2i(15, -4), Vector2i(15, -4), 2)
	igual(r[0].nome, "esteira_fim", "antes do braço = fim")


func test_remover_fecha_as_pontas() -> void:
	var c := _c()
	c.executar(c.plano_linha("esteira", Vector2i(0, 0), Vector2i(6, 0), 0))
	igual(c._estrutura_em(Vector2i(0, 0)).nome, "esteira_inicio")
	igual(c._estrutura_em(Vector2i(6, 0)).nome, "esteira_fim")
	c.executar(c.plano_remocao(Vector2i(3, 0), Vector2i(3, 0)))
	igual(c._estrutura_em(Vector2i(2, 0)).nome, "esteira_fim", "antes do buraco vira fim")
	igual(c._estrutura_em(Vector2i(4, 0)).nome, "esteira_inicio", "depois do buraco vira início")
	c.desfazer()
	igual(c._estrutura_em(Vector2i(2, 0)).nome, "esteira_reta", "desfazer religa")
	igual(c._estrutura_em(Vector2i(3, 0)).nome, "esteira_reta")
	igual(c._estrutura_em(Vector2i(4, 0)).nome, "esteira_reta")
	# máquina que recebia some → a esteira fecha em fim
	c.executar(c.plano_peca("fornalha", Vector2i(10, 2), 0))     # entrada na borda sul do tile (11, 2) → esteira em (11, 1)
	c.executar(c.plano_linha("esteira", Vector2i(11, -3), Vector2i(11, 1), 0))
	igual(c._estrutura_em(Vector2i(11, 1)).nome, "esteira_reta", "entrega na porta da fornalha")
	c.executar(c.plano_remocao(Vector2i(11, 2), Vector2i(11, 2)))
	igual(c._estrutura_em(Vector2i(11, 1)).nome, "esteira_fim", "sem a fornalha vira fim")


func test_trocar_por_cima() -> void:
	var c := _c()
	c.executar(c.plano_linha("esteira", Vector2i(0, 0), Vector2i(4, 0), 0))
	var p := c.plano_linha("esteira", Vector2i(2, 0), Vector2i(2, 3), 0)
	igual(p[0].acao, "substituir", "arrastar por cima troca a peça")
	verificar(p[0].nome.begins_with("esteira_curva"), "começar no meio de uma esteira desvia o fluxo para o traço novo")
	verificar(Construtor.pode_tudo(p), "trocar não é bloqueio")
	var igual_p := c.plano_linha("esteira", Vector2i(1, 0), Vector2i(3, 0), 0)
	igual(igual_p[1].acao, "igual", "mesma peça e direção: nada a fazer")
	igual(Construtor.contar(igual_p).ok, 0, "redesenhar a mesma esteira não muda nada")


func test_bloqueios_mostram_motivo() -> void:
	var c := _c()
	c.executar(c.plano_peca("fornalha", Vector2i(0, 0), 0))
	# o traço desvia da fornalha sozinho; terminar em cima dela deixa a ponta vermelha
	var p := c.plano_linha("esteira", Vector2i(-3, 0), Vector2i(3, 0), 0)
	verificar(Construtor.pode_tudo(p), "contorna a fornalha: tudo verde")
	var q := c.plano_linha("esteira", Vector2i(-3, 0), Vector2i(0, 0), 0)
	var motivos := {}
	for it in q:
		motivos[it.motivo] = true
	verificar(motivos.has("ocupado"), "ponta em cima da fornalha: vermelho")
	verificar(motivos.has(""), "o resto continua verde")
	igual(c.plano_peca("extrator_cristal", Vector2i(-5, -5), 0)[0].motivo, "sem_jazida")
	var t := _obstaculo_perto(c)
	igual(c.plano_peca("bau", t, 0)[0].motivo, "obstaculo", "obstáculo natural bloqueia")


func test_peca_grande_centrada_no_cursor() -> void:
	igual(Construtor.minimo_no_cursor("extrator_cristal", Vector2i(10, 10), 0), Vector2i(9, 9), "3×3: cursor no meio")
	igual(Construtor.minimo_no_cursor("fornalha", Vector2i(10, 10), 0), Vector2i(10, 10), "2×2: cursor no tile sudoeste do meio")
	igual(Construtor.minimo_no_cursor("estacao", Vector2i(10, 10), 1), Vector2i(9, 10), "2×3 girada vira 3×2")


func test_linha_reta_e_postes() -> void:
	var c := _c()
	var p := c.plano_linha("trilho_reto", Vector2i(0, 0), Vector2i(1, 6), 0)
	igual(p.size(), 7, "trilho segue o eixo dominante")
	igual(p[-1].minimo, Vector2i(0, 6))
	var q := c.plano_linha("poste_energia", Vector2i(-6, 0), Vector2i(6, 0), 0)
	igual(q.size(), 3, "poste a cada 6 tiles + o último")
	var m := c.plano_linha("muro_centro", Vector2i(0, 0), Vector2i(-3, 0), 0)
	igual(m.size(), 4, "muro arrastado")


func test_cano_curva() -> void:
	var c := _c()
	for alvo in [Vector2i(3, 2), Vector2i(-3, 2), Vector2i(3, -2), Vector2i(-2, -3)]:
		var p := c.plano_linha("cano", Vector2i.ZERO, alvo, 0)
		for i in p.size() - 1:
			# o lado de saída de cada cano encosta num lado aberto do próximo
			var a: Dictionary = p[i]
			var b: Dictionary = p[i + 1]
			var d := Construtor.direcao(a.minimo, b.minimo)
			verificar(_lado_aberto(a, d), "%s em %s abre para %d (alvo %s)" % [a.nome, a.minimo, d, alvo])
			verificar(_lado_aberto(b, posmod(d + 2, 4)), "%s em %s abre para %d (alvo %s)" % [b.nome, b.minimo, posmod(d + 2, 4), alvo])


func _lado_aberto(it: Dictionary, d: int) -> bool:
	for p in Registro.modelos[it.nome].portas:
		var pm := Grade.porta_no_mundo(p, it.minimo, Vector2i.ONE, it.rot)
		if pm.dir == Grade.DIRECOES[d]:
			return true
	return false


func test_remover_limpar_desfazer() -> void:
	var c := _c()
	c.executar(c.plano_peca("fornalha", Vector2i(0, 0), 0))
	c.executar(c.plano_linha("esteira", Vector2i(-3, -2), Vector2i(3, -2), 0))
	var n0 := c.mapa.estruturas.size()
	# retângulo pegando só um tile da fornalha remove a fornalha inteira
	var p := c.plano_remocao(Vector2i(1, 1), Vector2i(1, -2))
	var nomes := _nomes(p)
	verificar(nomes.has("fornalha"), "fornalha entra no plano")
	igual(nomes.count("fornalha"), 1, "uma vez só")
	var rel := c.executar(p)
	igual(c.mapa.estruturas.size(), n0 - 2, "fornalha + 1 tile de esteira")
	verificar(rel.removidos.size() >= 2, "relatório traz as remoções (e as pontas trocadas)")
	c.desfazer()
	igual(c.mapa.estruturas.size(), n0, "desfazer devolve")
	igual(c.plano_peca("fornalha", Vector2i(0, 0), 0)[0].motivo, "ocupado", "fornalha de volta no lugar")
	# obstáculo natural: limpar e desfazer
	var t := _obstaculo_perto(c)
	var pl := c.plano_remocao(t, t)
	igual(pl.size(), 1)
	igual(pl[0].acao, "limpar")
	c.executar(pl)
	igual(c.plano_peca("bau", t, 0)[0].motivo, "", "limpo: dá para construir")
	c.desfazer()
	igual(c.plano_peca("bau", t, 0)[0].motivo, "obstaculo", "desfazer põe a árvore de volta")
	# desfazer a construção da esteira
	c.desfazer()
	igual(c.plano_peca("bau", Vector2i(-3, -2), 0)[0].motivo, "", "esteira desfeita")
	verificar(c.pode_desfazer(), "ainda resta a fornalha no histórico")


func test_trem_e_destruir() -> void:
	var c := _c()
	igual(c.plano_peca("trem", Vector2i(0, 0), 0)[0].motivo, "sem_trilho", "trem fora do trilho: vermelho")
	c.executar(c.plano_linha("trilho_reto", Vector2i(0, -6), Vector2i(0, 6), 0))
	var p := c.plano_peca("trem", Vector2i(0, 0), 0)
	igual(p[0].motivo, "", "em cima do trilho reto: verde")
	var rel := c.executar(p)
	igual(rel.trens.size(), 1, "o relatório pede o trem ao mundo")
	# aranha derrubou um pedaço de esteira: as pontas se fecham, e isso não vai para o desfazer
	var c2 := _c()
	c2.executar(c2.plano_linha("esteira", Vector2i(0, 2), Vector2i(6, 2), 0))
	var n := c2._historico.size()
	var id: int = c2.mapa.tiles[Vector2i(3, 2)]
	c2.destruir(id)
	igual(c2._estrutura_em(Vector2i(2, 2)).nome, "esteira_fim", "ponta fechada após destruição")
	igual(c2._historico.size(), n, "destruição não entra no desfazer")


func test_rota_desvia_obstaculos() -> void:
	var c := _c()
	c.executar(c.plano_peca("fornalha", Vector2i(0, 0), 0))
	var p := c.plano_linha("esteira", Vector2i(-4, 0), Vector2i(4, 0), 0)
	verificar(Construtor.pode_tudo(p), "tudo verde")
	var tiles := {}
	for it in p:
		tiles[it.minimo] = true
		verificar(c.mapa.motivo_bloqueio("esteira_reta", it.minimo, 0) == "", "tile %s livre" % it.minimo)
	igual(tiles.size(), p.size(), "sem tile repetido")
	var curvas := 0
	for it in p:
		if it.nome.begins_with("esteira_curva"):
			curvas += 1
	verificar(curvas <= 4, "desvio limpo (%d curvas)" % curvas)
	igual(p[1].minimo, Vector2i(-3, 0), "segue reto até perto da fornalha")
	igual(p[0].minimo, Vector2i(-4, 0))
	igual(p[-1].minimo, Vector2i(4, 0))
	var rel := c.executar(p)
	igual(rel.colocados.size(), p.size(), "tudo construído")


func test_fim_existente_vira_curva_para_o_traco() -> void:
	var c := _c()
	c.executar(c.plano_linha("esteira", Vector2i(0, 0), Vector2i(3, 0), 0))     # leste, termina em fim em (3,0)
	igual(c._estrutura_em(Vector2i(3, 0)).nome, "esteira_fim")
	# começa ao lado do fim (não na frente): o fim vira curva para o novo traço
	var p := c.plano_linha("esteira", Vector2i(3, 1), Vector2i(3, 4), 0)
	igual(p[0].nome, "esteira_reta", "o primeiro já nasce alimentado")
	c.executar(p)
	var antigo := c._estrutura_em(Vector2i(3, 0))
	verificar(antigo.nome.begins_with("esteira_curva"), "o fim antigo virou curva (%s)" % antigo.nome)
	var no := Construtor.no_esteira(antigo)
	igual(no.sai, Construtor.direcao(Vector2i(3, 0), Vector2i(3, 1)), "a curva entrega no traço novo")


func test_ponta_vira_para_quem_recebe() -> void:
	var c := _c()
	c.executar(c.plano_linha("esteira", Vector2i(0, 3), Vector2i(4, 3), 0))     # linha leste em y = 3
	# traço rumo ao norte terminando ao lado do início da linha: o início vira curva e recebe dele
	var p := c.plano_linha("esteira", Vector2i(-1, 0), Vector2i(-1, 3), 0)
	igual(p[3].nome, "esteira_curva_dir" if Construtor.direcao(Vector2i(-1, 2), Vector2i(-1, 3)) == 0 else p[3].nome, "último tile vira para a linha")
	c.executar(p)
	var ini := c._estrutura_em(Vector2i(0, 3))
	igual(ini.nome, "esteira_reta", "o início da linha agora é alimentado")
	# sem nada ao lado: termina em fim
	var q := c.plano_linha("esteira", Vector2i(-6, -6), Vector2i(-6, -3), 0)
	igual(q[-1].nome, "esteira_fim")


func test_rota_rapida() -> void:
	var c := _c()
	for x in range(-10, 11, 2):
		c.executar(c.plano_peca("bau", Vector2i(x, 0), 0))
	var t0 := Time.get_ticks_usec()
	var p := c.plano_linha("esteira", Vector2i(-12, -4), Vector2i(12, 4), 0)
	var ms := (Time.get_ticks_usec() - t0) / 1000.0
	verificar(Construtor.pode_tudo(p), "acha a passagem entre os baús")
	verificar(ms < 40.0, "rota em %.1f ms" % ms)
	print("      rota com desvio: %.1f ms" % ms)
