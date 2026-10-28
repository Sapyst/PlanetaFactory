extends Caso
## Construção, esteiras, braços, máquinas, energia e trilhos.

func _mapa() -> MapaOcupacao:
	return MapaOcupacao.new(GeradorMundo.new(1337))


func test_colocacao_basica() -> void:
	var m := _mapa()
	var a := m.colocar("fornalha", Vector2i(-3, -3), 0)
	verificar(a > 0, "fornalha cabe no spawn")
	igual(m.motivo_bloqueio("fornalha", Vector2i(-2, -2), 0), "ocupado", "sobreposição recusada")
	igual(m.motivo_bloqueio("extrator_cristal", Vector2i(-3, 3), 0), "sem_jazida", "extrator longe do cristal")
	# extrator em cima da jazida de cristal do spawn (centro (15,5))
	igual(m.motivo_bloqueio("extrator_cristal", Vector2i(14, 4), 0), "", "extrator sobre o cristal")
	m.remover(a)
	igual(m.motivo_bloqueio("fornalha", Vector2i(-2, -2), 0), "", "removida libera o espaço")


func test_cantos_e_pilares() -> void:
	var m := _mapa()
	var id := m.colocar("muro_centro", Vector2i(0, 0), 0)      # muro ocupa canto
	verificar(id > 0)
	verificar(not m.canto_livre(Vector2i(1, 1)), "canto do muro não aceita pilar")
	verificar(m.reservar_pilar(Vector2i(3, 3), 1.0) > 0, "pilar em canto livre")
	igual(m.motivo_bloqueio("muro_centro", Vector2i(2, 2), 0), "pilar_no_canto", "muro não cobre pilar")
	verificar(m.colocar("fornalha", Vector2i(2, 2), 0) > 0, "máquina comum convive com pilar no canto (cantos livres)")


func test_esteira_elevada_sobre_baus() -> void:
	var m := _mapa()
	var caminho: Array[Vector2i] = []
	var dirs: Array[int] = []
	var niveis: Array[float] = []
	for i in 10:
		caminho.append(Vector2i(i - 5, 2))
		dirs.append(1)
		niveis.append(1.0)
	m.colocar("bau", Vector2i(-2, 2), 0)                         # baú (0,62 m) embaixo: passa a 1,0 m
	var r := EsteiraElevada.planejar(m, caminho, dirs, niveis)
	verificar(r.ok, "trecho elevado sobre baú é aceito (%s)" % r.erro)
	verificar(r.pilares.size() >= 6, "tem pórticos ao longo do trecho")
	for p in r.pilares:
		verificar(m.canto_livre(p.canto), "pilar só em canto livre")
	m.colocar("fornalha", Vector2i(1, 1), 0)                     # fornalha (2,26 m) embaixo: não passa
	r = EsteiraElevada.planejar(m, caminho, dirs, niveis)
	igual(r.erro, "estrutura_alta_embaixo")


func test_esteira_anda_e_comprime() -> void:
	var e := EsteiraCaminho.new(4.0, 2.0)
	verificar(e.inserir_na_entrada("pedra"))
	verificar(not e.inserir_na_entrada("pedra"), "sem espaço logo atrás")
	for i in 30:
		e.tick(1.0 / 30.0)
		e.inserir_na_entrada("pedra")
	var ps := e.posicoes()
	for i in range(1, ps.size()):
		verificar(ps[i] - ps[i - 1] >= EsteiraCaminho.ESPACO - 1e-4, "itens nunca se sobrepõem")
	# sem saída: tudo comprime contra o fim, 4 itens por metro
	for i in 300:
		e.tick(1.0 / 30.0)
		e.inserir_na_entrada("pedra")
	igual(e.quantidade(), 16, "4 m × 4 itens por metro")
	perto(e.posicoes()[0], 0.0, 1e-4, "primeiro encostado na saída")


func test_esteira_vazao() -> void:
	# entrega na velocidade nominal: 1,875 m/s ÷ 0,25 m = 7,5 itens/s
	var e := EsteiraCaminho.new(3.0, 1.875)
	var saiu := [0]
	e.saida = func(_i: String) -> bool:
		saiu[0] += 1
		return true
	for i in 30 * 20:
		e.inserir_na_entrada("ferro")
		e.tick(1.0 / 30.0)
	perto(saiu[0] / 20.0, 7.5, 0.6, "itens/s na saída")


func test_esteira_encadeada() -> void:
	var a := EsteiraCaminho.new(2.0)
	var b := EsteiraCaminho.new(2.0)
	a.proximo = b
	for i in 200:
		a.inserir_na_entrada("cobre")
		a.tick(1.0 / 30.0)
		b.tick(1.0 / 30.0)
	igual(b.quantidade(), 8, "segunda esteira cheia")
	igual(a.quantidade(), 8, "primeira também (fila parada)")


func test_braco_maquina_esteira() -> void:
	var f := Maquina.new("fornalha", 1.0)
	f.definir_receita("fundir_ferro", Registro.receitas["fundir_ferro"])
	var ent := EsteiraCaminho.new(1.0)
	ent.saida = func(item: String) -> bool: return f.receber(item)
	var sai := EsteiraCaminho.new(1.0)
	var br := Braco.new(0.83)
	br.origem = f
	br.destino = _DestinoEsteira.new(sai)
	for i in 30 * 40:
		ent.inserir_na_entrada("minerio_ferro")
		ent.tick(1.0 / 30.0)
		f.tick(1.0 / 30.0)
		br.tick(1.0 / 30.0)
		sai.tick(1.0 / 30.0)
		if sai.posicoes().size() > 0 and sai.posicoes()[0] <= 0.0:
			sai.retirar_perto(0.0)
	# 40 s / 3,2 s por placa ≈ 12 placas
	verificar(f.produzidos >= 11 and f.produzidos <= 13, "fornalha produziu ~12 (veio %d)" % f.produzidos)
	verificar(br.entregues >= f.produzidos - 2, "braço levou quase tudo")


func test_maquina_dorme() -> void:
	var f := Maquina.new("montadora", 1.0)
	f.definir_receita("engrenagem", Registro.receitas["engrenagem"])
	f.tick(0.1)
	igual(f.estado, Maquina.Estado.SEM_INSUMO)
	verificar(f.dormindo(), "dorme sem insumo")
	f.receber("placa_ferro"); f.receber("placa_ferro")
	verificar(not f.dormindo(), "acorda ao receber")
	for i in 40: f.tick(0.1)
	igual(f.produzidos, 1)
	verificar(not f.aceita("cobre"), "recusa item fora da receita")


func test_energia() -> void:
	var r := RedeEnergia.new()
	for id in [1, 2, 3]:
		r.adicionar(id, 0.0)                     # postes
	r.adicionar(10, 450.0)
	r.adicionar(11, 450.0)
	r.adicionar(12, 100.0)                       # longe: rede sem gerador
	var g := r.adicionar(20, -450.0, 10.0)
	r.ligar(1, 2)
	r.ligar(1, 10)
	r.ligar(2, 11)
	r.ligar(1, 20)
	r.ligar(3, 12)
	r.calcular()
	r.tick(1.0)
	perto(r.satisfacao(10), 0.5, 1e-3, "450 kW para 900 kW de demanda = 50%")
	perto(r.satisfacao(11), 0.5, 1e-3, "poste ligado por fio = mesma rede")
	perto(r.satisfacao(12), 0.0, 1e-3, "poste sem fio até o gerador: sem energia")
	perto(g.combustivel_mj, 10.0 - 0.45, 1e-3, "gastou 450 kJ")
	verificar(not r.tem_fonte(12) and r.tem_fonte(11))


func test_trilhos_rota_e_blocos() -> void:
	var g := GrafoTrilhos.new()
	for i in 10:
		g.adicionar_peca("trilho_reto", Vector2(0.5, i), Vector2(0.5, i + 1), 1.0)
	for i in 5:
		g.adicionar_peca("trilho_reto", Vector2(0.5 + i, 10), Vector2(1.5 + i, 10), 1.0)
	g.adicionar_peca("trilho_reto", Vector2(9.5, 0), Vector2(9.5, 1), 1.0)   # ilha solta
	g.adicionar_sinal(Vector2(0.5, 5))
	var blocos := g.calcular_blocos()
	igual(blocos, 3, "sinal divide a linha em 2 blocos + a ilha")
	var r := g.rota(Vector2(0.5, 0), Vector2(5.5, 10))
	igual(r.size(), 15, "rota percorre as 15 peças")
	igual(g.rota(Vector2(0.5, 0), Vector2(9.5, 1)).size(), 0, "sem caminho para a ilha")
	verificar(g.reservar(1, r.slice(0, 3)), "trem 1 reserva o primeiro bloco")
	verificar(not g.reservar(2, r.slice(2, 4)), "trem 2 não entra no bloco ocupado")
	verificar(g.reservar(2, r.slice(7, 9)), "mas entra no bloco depois do sinal")
	g.liberar(1)
	verificar(g.reservar(2, r.slice(0, 2)), "liberado, o trem 2 entra")


class _DestinoEsteira:
	var e: EsteiraCaminho
	func _init(p: EsteiraCaminho) -> void: e = p
	func aceita(_i: String) -> bool: return e.cabe_na_entrada()
	func receber(i: String) -> bool: return e.inserir_na_entrada(i)
