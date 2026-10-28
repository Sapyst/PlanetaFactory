extends Caso
## Fios automáticos: poste liga no gerador, em outro poste (até 9 m) e em máquina sem energia (até 5 m da borda);
## máquina já ligada não troca de poste; aceitar mais fontes; remover poste religa os órfãos; torre sem fio.

func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-30, 40):
		for y in range(-12, 14):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i) -> int:
	var antes := c.mapa._prox_id
	c.executar(c.plano_peca(nome, t, 0))
	verificar(c.mapa.estruturas.has(antes), "coube %s em %s" % [nome, t])
	return antes


func _ligados(c: Construtor, a: int, b: int) -> bool:
	return c.mapa.estruturas[a].get("fios", []).has(b) and c.mapa.estruturas[b].get("fios", []).has(a)


func test_postes_ligam_sozinhos() -> void:
	var c := _c()
	var g := _por(c, "gerador", Vector2i(0, 0))           # 2×2 em (0..1, 0..1)
	var p1 := _por(c, "poste_energia", Vector2i(4, 0))    # 3 m da borda do gerador
	verificar(_ligados(c, g, p1), "poste perto do gerador ganha fio")
	var p2 := _por(c, "poste_energia", Vector2i(12, 0))   # 8 m do primeiro
	verificar(_ligados(c, p1, p2), "poste a 8 m liga no anterior")
	var p_longe := _por(c, "poste_energia", Vector2i(26, 0))   # 14 m: longe demais
	igual(c.mapa.estruturas[p_longe].fios.size(), 0, "poste a 14 m fica solto")
	var maq := _por(c, "montadora", Vector2i(14, 4))      # 3×3 perto do p2
	verificar(_ligados(c, p2, maq), "máquina posta perto de poste se liga")
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	verificar(f.rede.tem_fonte(maq), "a montadora está na rede do gerador pelos fios")


func test_maquina_ligada_nao_troca_de_poste() -> void:
	var c := _c()
	var p1 := _por(c, "poste_energia", Vector2i(0, 0))
	var maq := _por(c, "montadora", Vector2i(3, 0))
	verificar(_ligados(c, p1, maq))
	var p2 := _por(c, "poste_energia", Vector2i(7, 0))     # também alcança a montadora
	verificar(not _ligados(c, p2, maq), "já tinha energia: não pega o poste novo")
	verificar(_ligados(c, p1, p2), "mas os postes se ligam entre si")
	Fiacao.mudar_vagas(c.mapa, maq, 2)
	verificar(_ligados(c, p2, maq), "aceitando 2 fontes, liga no segundo poste")
	Fiacao.mudar_vagas(c.mapa, maq, 1)
	igual(Fiacao.ligacoes(c.mapa, c.mapa.estruturas[maq]), 1, "voltou a 1 fonte")


func test_remover_poste_religa() -> void:
	var c := _c()
	var p1 := _por(c, "poste_energia", Vector2i(0, 0))
	var maq := _por(c, "montadora", Vector2i(3, 0))
	var p2 := _por(c, "poste_energia", Vector2i(7, 0))
	verificar(not _ligados(c, p2, maq))
	c.executar(c.plano_remocao(Vector2i(0, 0), Vector2i(0, 0)))
	verificar(_ligados(c, p2, maq), "sem o poste 1, a montadora passa para o poste 2")
	c.desfazer()
	verificar(c.mapa.estruturas[maq].fios.size() >= 1, "desfazer não deixa a máquina solta")


func test_torre_sem_fio() -> void:
	var c := _c()
	c.cobrar = false
	var g := _por(c, "gerador", Vector2i(-20, 0))
	var t1 := _por(c, "torre_sem_fio", Vector2i(-16, 0))
	var t2 := _por(c, "torre_sem_fio", Vector2i(16, 0))          # 32 m: só torre alcança
	verificar(_ligados(c, t1, t2), "torres se ligam a 32 m, sem fio")
	var maq := _por(c, "montadora", Vector2i(26, 0))            # ~8 m da torre 2
	verificar(_ligados(c, t2, maq), "máquina a 8 m da torre recebe")
	verificar(_ligados(c, g, t1))
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	f.combustivel[g] = 20.0
	f.tick(1.0 / 30.0)
	perto(f.rede.satisfacao(maq), 1.0, 1e-3, "energia chegou a 42 m do gerador sem fio")
