extends Caso
## Locomotiva elétrica (pesquisa trem_eletrico, lote 16): trilho energizado (trilho reto com terceiro trilho; peças
## encostadas formam um trecho e uma ligada a poste energiza o trecho todo) e o trem elétrico (2 locomotivas
## elétricas + 2 vagões): no trilho energizado com energia anda no dobro, fora dele só na bateria de manobra; puxa
## energia do trecho andando; não polui (a diesel polui andando).

const ELETRICO: Array[String] = ["locomotiva_eletrica", "vagao_carga", "vagao_carga", "locomotiva_eletrica"]
const DIESEL: Array[String] = ["locomotiva", "vagao_carga", "vagao_carga", "locomotiva"]


func _por(c: Construtor, nome: String, t: Vector2i, rot: int) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


## Linha norte–sul x = 0 de y −30 a 40: energizada de `de` a `ate` (o resto trilho comum), estação no norte (y 36).
func _linha(de := -30, ate := 30) -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-3, 10):
		for y in range(-33, 44):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	_por(c, "trilho_fim", Vector2i(0, -31), 2)
	for y in range(-30, 41):
		_por(c, "trilho_energizado" if y >= de and y <= ate else "trilho_reto", Vector2i(0, y), 0)
	_por(c, "trilho_fim", Vector2i(0, 41), 0)
	_por(c, "estacao", Vector2i(1, 36), 0)
	return c


func _trem(g: GrafoTrilhos, carros: Array[String], y := -28) -> Trem:
	var r := g.peca_no_ponto(Vector2(0.5, y + 0.5), 0.1)
	var t := Trem.new(1, g, carros.duplicate())
	verificar(t.colocar(r.peca, g.pecas[r.peca].a), "trem coube")
	return t


func test_dados() -> void:
	for n in ["trilho_energizado", "locomotiva_eletrica"]:
		verificar(Registro.modelos.has(n), "modelo: " + n)
	igual(Registro.modelos.trilho_energizado.get("estudo", ""), "estudo_trilho_energizado.py")
	igual(Registro.modelos.locomotiva_eletrica.get("estudo", ""), "estudo_locomotiva_eletrica.py")
	igual(Registro.modelos.locomotiva_eletrica.partes.map(func(p): return p.nome), ["corpo", "truque0", "truque1"],
			"truques que giram nas curvas")
	igual(Registro.modelos.trilho_energizado.portas.size(), 2, "portas de trilho como o reto")
	verificar(not Registro.modelos.trilho_energizado.get("terminais", []).is_empty(), "terminal do fio no eletroduto")
	igual(Trem.COMPOSICOES.trem_eletrico, ELETRICO)
	verificar(DesenhoLotes.aceita("trilho_energizado"), "desenhado em lote, como os trilhos")
	igual(Fiacao.papel("trilho_energizado"), "consumo", "poste liga nele")
	for n in ["trilho_energizado", "trem_eletrico"]:
		verificar(Registro.menu.categorias.any(func(cat): return n in cat.pecas), "no menu: " + n)
		verificar(Registro.menu.rotulos.has(n), "rótulo: " + n)
		verificar(not Construtor.custo_de(n).is_empty(), "custo: " + n)
	verificar(ResourceLoader.exists("res://assets/icones/trilho_energizado.png"), "ícone do trilho")
	verificar(ResourceLoader.exists("res://assets/icones/%s.png" % Registro.menu.icones.trem_eletrico), "ícone do trem")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("trem_eletrico"), "jogável")
	igual(Registro.progressao.pesquisas.trem_eletrico.requer, ["trem_automatico", "liga_leve"], "pré-requisitos da árvore")
	igual(p.custo("trem_eletrico"), {"pacote_pesquisa": 60, "pacote_automacao": 60, "pacote_quimico": 60})
	verificar(not p.peca_liberada("trilho_energizado"), "travado no início")
	p.concluidas = {"trem_automatico": true, "liga_leve": true}
	verificar(p.disponivel("trem_eletrico"), "com trem automático e liga leve dá para pesquisar")
	p.concluidas["trem_eletrico"] = true
	verificar(p.peca_liberada("trilho_energizado") and p.peca_liberada("trem_eletrico"), "libera trilho e trem")


func test_grafo_e_construtor() -> void:
	var c := _linha(-5, 5)
	var g := GrafoTrilhos.de_mapa(c.mapa)
	igual(g.calcular_blocos(), 1, "trilho energizado emenda com o comum: uma malha só")
	verificar(not g.rota(GrafoTrilhos.chave(Vector2(0.5, -30)), GrafoTrilhos.chave(Vector2(0.5, 40))).is_empty(), "rota passa por ele")
	_por(c, "sinal_trem", Vector2i(-1, 0), 0)
	igual(GrafoTrilhos.de_mapa(c.mapa).sinais.size(), 1, "sinal encosta no trilho energizado")
	var pl := c.plano_peca("trem_eletrico", Vector2i(0, 0), 0)
	igual(pl[0].motivo, "", "trem se põe no trilho energizado")
	igual(pl[0].nome, "trem_eletrico")
	var linha := c.plano_linha("trilho_energizado", Vector2i(5, 0), Vector2i(5, 6), 0)
	igual(linha.size(), 7, "arrasta em linha reta como o trilho")
	igual(int(linha[0].rot), Construtor.rot_do_fluxo(0), "no sentido do arraste")


func test_velocidade() -> void:
	var g := GrafoTrilhos.de_mapa(_linha().mapa)
	var cheio := func(id: int) -> float: return 1.0 if id >= 0 else -1.0
	var nada := func(_id: int) -> float: return 0.0
	var e := _trem(g, ELETRICO)
	verificar(e.energizar(cheio) >= 0, "em cima do trilho energizado")
	perto(e.vel_max, Trem.VEL_MAX * 2.0, 1e-6, "com energia: 2× (árvore)")
	e.energizar(nada)
	perto(e.vel_max, Trem.VEL_BATERIA, 1e-6, "sem energia: bateria de manobra")
	var d := _trem(g, DIESEL)
	igual(d.energizar(cheio), -1, "diesel não puxa do trilho")
	perto(d.vel_max, Trem.VEL_MAX, 1e-6)
	# fora do trilho energizado
	var g2 := GrafoTrilhos.de_mapa(_linha(30, 30).mapa)
	var e2 := _trem(g2, ELETRICO)
	igual(e2.energizar(func(id): return 1.0 if g2.pecas.any(func(p): return p.estrutura == id and p.nome == "trilho_energizado") else -1.0), -1,
			"trilho comum não alimenta")
	perto(e2.vel_max, Trem.VEL_BATERIA, 1e-6)
	igual(e.peca(), "trem_eletrico", "desmonta devolvendo o trem elétrico")
	igual(e.locomotivas_diesel(), 0, "elétrica não polui")
	igual(d.locomotivas_diesel(), 2, "diesel polui pelas duas locomotivas")


## Viagem: na linha toda energizada o elétrico chega bem antes do diesel.
func test_chega_mais_rapido() -> void:
	var tempos := {}
	for nome in ["eletrico", "diesel"]:
		var g := GrafoTrilhos.de_mapa(_linha().mapa)
		var t := _trem(g, ELETRICO if nome == "eletrico" else DIESEL)
		var ok := func(id: int) -> float: return 1.0 if id >= 0 else -1.0
		var dt := 1.0 / 30.0
		var tempo := 0.0
		var vmax := 0.0
		while tempo < 60.0 and t.estado != Trem.Estado.PARADO:
			t.energizar(ok)
			t.tick(dt)
			vmax = maxf(vmax, t.v)
			tempo += dt
		tempos[nome] = tempo
		if nome == "eletrico":
			verificar(vmax > Trem.VEL_MAX + 1.0, "passa da velocidade do diesel (%.1f m/s)" % vmax)
		else:
			verificar(vmax <= Trem.VEL_MAX + 1e-3, "diesel até 6 m/s")
	verificar(tempos.eletrico < tempos.diesel * 0.75, "elétrico chega antes (%.1f s × %.1f s)" % [tempos.eletrico, tempos.diesel])


## Trecho: só uma peça ligada ao poste e o trecho todo tem energia; o trem andando puxa energia dele.
func test_trecho_energizado() -> void:
	var c := _linha(-10, 10)
	var gen := _por(c, "gerador", Vector2i(4, -2), 0)
	var poste := _por(c, "poste_energia", Vector2i(2, 0), 0)
	var f := Fabrica.new(c.mapa)
	f.reconstruir()
	f.combustivel[gen] = 1.0e6
	f.tick(0.1)
	var longe: int = c.mapa.tiles[Vector2i(0, 9)]
	var perto_p: int = c.mapa.tiles[Vector2i(0, 0)]
	verificar(c.mapa.estruturas[perto_p].get("fios", []).has(poste), "o poste ligou no trilho perto dele")
	verificar(not c.mapa.estruturas[longe].get("fios", []).has(poste), "o de longe não tem fio")
	perto(f.energia_trilho(longe), 1.0, 1e-6, "mas está no mesmo trecho: tem energia")
	var comum: int = c.mapa.tiles[Vector2i(0, 15)]
	perto(f.energia_trilho(comum), -1.0, 1e-6, "trilho comum não é energizado")
	f.pedir_trilho(longe, Trem.KW_ELETRICA)
	f.tick(0.1)
	var ligados: Array = f._trechos[f._trilho_grupo[longe]].filter(func(k): return f._membros.has(k))
	var soma := 0.0
	for k in ligados:
		soma += float(f._membros[k].kw)
	perto(soma, Trem.KW_ELETRICA + 5.0 * ligados.size(), 1e-3, "o trem puxa %d kW do trecho" % int(Trem.KW_ELETRICA))
	f.combustivel[gen] = 0.0
	f.tick(0.1)
	f.tick(0.1)
	perto(f.energia_trilho(longe), 0.0, 1e-6, "gerador parado: trecho sem energia")
	# trecho separado (sem peça encostada) não pega energia
	_por(c, "trilho_energizado", Vector2i(8, 20), 0)
	f.reconstruir()
	f.combustivel[gen] = 1.0e6
	f.tick(0.1)
	perto(f.energia_trilho(c.mapa.tiles[Vector2i(8, 20)]), 0.0, 1e-6, "peça solta, longe do poste: sem energia")
