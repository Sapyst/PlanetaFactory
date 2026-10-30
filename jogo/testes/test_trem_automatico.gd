extends Caso
## Trem automático (pesquisa trem_automatico, lote 16): sinal em cadeia (o trem só passa se a saída do cruzamento —
## o bloco depois do próximo sinal comum — também estiver livre) e rotas com condição por estação ("tempo", "cheio",
## "vazio"; esperando, o trem troca carga de novo a cada segundo pelo `retroca`).

const CARROS: Array[String] = ["locomotiva", "vagao_carga", "vagao_carga", "locomotiva"]


func _por(c: Construtor, nome: String, t: Vector2i, rot: int) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


## Linha norte–sul x = 0, y −30..30; sinal (comum ou em cadeia) na borda y = 0, sinal comum na y = 4 (o "cruzamento"
## é o bloco 0..4) e estação a leste lá no norte (parada em y 21,5).
func _linha(primeiro: String) -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 5):
		for y in range(-33, 34):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	_por(c, "trilho_fim", Vector2i(0, -31), 2)
	for y in range(-30, 31):
		_por(c, "trilho_reto", Vector2i(0, y), 0)
	_por(c, "trilho_fim", Vector2i(0, 31), 0)
	_por(c, primeiro, Vector2i(-1, 0), 0)
	_por(c, "sinal_trem", Vector2i(-1, 4), 0)
	_por(c, "estacao", Vector2i(1, 20), 0)
	return c


func _trem(g: GrafoTrilhos, id: int, y: int) -> Trem:
	var r := g.peca_no_ponto(Vector2(0.5, y + 0.5), 0.1)
	var t := Trem.new(id, g, CARROS.duplicate())
	verificar(t.colocar(r.peca, g.pecas[r.peca].a), "trem %d coube em y %d" % [id, y])
	return t


func _rodar(trens: Array[Trem], estoques: Dictionary, segundos: float) -> void:
	var dt := 1.0 / 30.0
	for i in int(segundos / dt):
		for t in trens:
			t.tick(dt)
			if t.chegada >= 0:
				if not estoques.has(t.chegada):
					estoques[t.chegada] = {"enviar": {}, "recebido": {}}
				t.trocar_carga(estoques[t.chegada], t.chegada)
				t.chegada = -1
			if t.retroca >= 0:
				t.trocar_carga(estoques[t.retroca], t.retroca)
				t.retroca = -1


func _frente(t: Trem) -> float:
	return t.ponto_em(t.s).pos.y


func test_dados() -> void:
	verificar(Registro.modelos.has("sinal_cadeia"), "modelo do sinal em cadeia (estudo_sinal_cadeia.py)")
	igual(Registro.modelos.sinal_cadeia.get("estudo", ""), "estudo_sinal_cadeia.py")
	igual(Registro.area("sinal_cadeia"), Vector2i(1, 1), "1×1 (árvore)")
	igual(Registro.estruturas.sinal_cadeia.grupo, "sinal")
	verificar(Registro.menu.categorias.any(func(cat): return "sinal_cadeia" in cat.pecas), "no menu dos trilhos")
	verificar(Registro.menu.rotulos.has("sinal_cadeia"), "rótulo")
	verificar(ResourceLoader.exists("res://assets/icones/sinal_cadeia.png"), "ícone")
	verificar(not Construtor.custo_de("sinal_cadeia").is_empty(), "tem custo")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("trem_automatico"), "Trem automático é jogável")
	igual(Registro.progressao.pesquisas.trem_automatico.requer, ["ferrovia", "automacao"], "pré-requisitos da árvore")
	igual(p.custo("trem_automatico"), {"pacote_pesquisa": 40, "pacote_automacao": 40}, "básico × 40 + automação × 40")
	verificar(not p.peca_liberada("sinal_cadeia"), "travado no início")
	verificar(not p.modo_liberado("trem_condicao"), "rotas com condição travadas no início")
	p.concluidas = {"ferrovia": true, "automacao": true}
	verificar(p.disponivel("trem_automatico"), "com ferrovia e automação dá para pesquisar")
	p.concluidas["trem_automatico"] = true
	verificar(p.peca_liberada("sinal_cadeia"), "libera o sinal em cadeia")
	verificar(p.modo_liberado("trem_condicao"), "libera as rotas com condição")
	p.concluidas["fluidos"] = true
	verificar(p.disponivel("vagao_tanque"), "e com ele o vagão-tanque fica pesquisável")
	verificar(Pesquisa.new(true).modo_liberado("trem_condicao"), "modo demonstração tem tudo")


func test_grafo_marca_a_cadeia() -> void:
	var g := GrafoTrilhos.de_mapa(_linha("sinal_cadeia").mapa)
	igual(g.sinais.size(), 2, "dois sinais")
	igual(g.cadeia.size(), 1, "um em cadeia")
	verificar(g.cadeia.has(GrafoTrilhos.chave(Vector2(0.5, 0.0))), "na borda y = 0")
	var g2 := GrafoTrilhos.de_mapa(_linha("sinal_trem").mapa)
	verificar(g2.cadeia.is_empty(), "sinal comum não é cadeia")
	igual(g.calcular_blocos(), g2.calcular_blocos(), "divide os blocos igual ao sinal comum")


## Trem A parado na saída (bloco depois do sinal y = 4); trem B vem do sul. Com sinal comum, B entra no cruzamento e
## para dentro dele (diante do sinal y = 4); com sinal em cadeia, para ANTES (y = 0) e o cruzamento fica livre.
func test_cadeia_segura_antes_do_cruzamento() -> void:
	for primeiro in ["sinal_trem", "sinal_cadeia"]:
		var g := GrafoTrilhos.de_mapa(_linha(primeiro).mapa)
		var a := _trem(g, 1, 6)
		var b := _trem(g, 2, -25)
		var trens: Array[Trem] = [a, b]
		_rodar(trens, {}, 25.0)
		var fb := _frente(b)
		if primeiro == "sinal_trem":
			verificar(fb > 1.0 and fb < 4.0, "sinal comum: B entra no cruzamento e para no meio dele (frente %.2f)" % fb)
		else:
			verificar(fb < 0.0 and fb > -1.5, "sinal em cadeia: B para antes do cruzamento (frente %.2f)" % fb)
			igual(b.estado, Trem.Estado.ESPERANDO_BLOCO, "esperando a saída")
			var bl_x := -1
			for pc in g.pecas.size():
				if g.pecas[pc].nome == "trilho_reto" and is_equal_approx(g.pecas[pc].a.y, 2.0):
					bl_x = g.pecas[pc].bloco
			verificar(bl_x >= 0 and not g.reserva.has(bl_x), "o cruzamento fica livre")
			# a saída libera: A some (desmontado) — B passa direto pelo cruzamento
			trens.erase(a)
			g.liberar(a.id)
			_rodar(trens, {}, 25.0)
			verificar(_frente(b) > 6.0, "saída livre: B atravessa (frente %.2f)" % _frente(b))


## Dois trens em sentidos contrários não travam por causa da cadeia (cada um espera a saída inteira).
func test_cadeia_nao_reserva_meio_bloco() -> void:
	var g := GrafoTrilhos.de_mapa(_linha("sinal_cadeia").mapa)
	var b := _trem(g, 2, -25)
	var trens: Array[Trem] = [b]
	_rodar(trens, {}, 40.0)
	igual(b.estado, Trem.Estado.PARADO, "sozinho, passa pela cadeia e chega à estação")
	verificar(absf(b.ponto_em(b.s - b.comprimento() / 2.0).pos.y - 21.5) < 0.2, "meio do trem na parada")


## Duas estações (A ao norte, B ao sul) e a rota A → B.
func _duas() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 5):
		for y in range(-18, 19):
			m.limpar_obstaculo(Vector2i(x, y))
	var c := Construtor.new(m)
	_por(c, "trilho_fim", Vector2i(0, -16), 2)
	for y in range(-15, 16):
		_por(c, "trilho_reto", Vector2i(0, y), 0)
	_por(c, "trilho_fim", Vector2i(0, 16), 0)
	var a := _por(c, "estacao", Vector2i(1, 8), 0)
	var b := _por(c, "estacao", Vector2i(1, -12), 0)
	var g := GrafoTrilhos.de_mapa(m)
	var t := _trem(g, 1, 0)
	t.rota = [a, b]
	return {"g": g, "t": t, "a": a, "b": b, "est": {a: {"enviar": {}, "recebido": {}}, b: {"enviar": {}, "recebido": {}}}}


func test_condicao_cheio() -> void:
	var d := _duas()
	var t: Trem = d.t
	t.condicoes[str(d.a)] = "cheio"
	var trens: Array[Trem] = [t]
	_rodar(trens, d.est, 20.0)
	igual(t.estado, Trem.Estado.PARADO, "parado em A")
	igual(t.parado_em, d.a, "na estação A")
	_rodar(trens, d.est, 10.0)
	igual(t.estado, Trem.Estado.PARADO, "sem carga para levar, segue esperando encher (passou dos 4 s)")
	d.est[d.a].enviar["placa_ferro"] = 50
	_rodar(trens, d.est, 2.0)
	igual(t.total_carga(), 50, "troca de novo enquanto espera (retroca)")
	igual(t.estado, Trem.Estado.PARADO, "50 de 80: ainda não encheu")
	d.est[d.a].enviar["placa_ferro"] = 40
	_rodar(trens, d.est, 3.0)
	igual(t.total_carga(), t.capacidade(), "encheu (2 vagões × 40)")
	verificar(t.estado != Trem.Estado.PARADO or t.parado_em != d.a, "cheio: segue viagem")
	_rodar(trens, d.est, 30.0)
	igual(int(d.est[d.b].recebido.get("placa_ferro", 0)), 80, "levou tudo para B")


func test_condicao_tempo() -> void:
	var d := _duas()
	var t: Trem = d.t
	t.condicoes[str(d.a)] = "tempo"
	var trens: Array[Trem] = [t]
	for i in 40:
		_rodar(trens, d.est, 0.5)
		if t.parado_em == d.a:
			break
	igual(t.parado_em, d.a, "chegou em A")
	_rodar(trens, d.est, 15.0)
	igual(t.estado, Trem.Estado.PARADO, "espera mais que a parada curta")
	_rodar(trens, d.est, Trem.ESPERA_TEMPO - 15.0 + 1.0)
	verificar(t.parado_em != d.a, "depois de %d s segue" % int(Trem.ESPERA_TEMPO))


func test_condicao_vazio() -> void:
	var t := Trem.new(1, GrafoTrilhos.new(), CARROS.duplicate())
	t.parado_em = 7
	t.condicoes["7"] = "vazio"
	t.carga = {"pedra": 3}
	verificar(not t.condicao_cumprida(), "com carga não está vazio")
	t.carga = {}
	verificar(t.condicao_cumprida(), "vazio")
	var tq: Array[String] = ["locomotiva", "vagao_tanque", "vagao_tanque", "locomotiva"]
	var f := Trem.new(2, GrafoTrilhos.new(), tq)
	f.parado_em = 7
	f.condicoes["7"] = "vazio"
	f.fluido = "agua"
	f.fluido_qtd = 10.0
	verificar(not f.condicao_cumprida(), "trem-tanque com fluido não está vazio")
	f.condicoes["7"] = "cheio"
	verificar(not f.condicao_cumprida(), "10 de 50.000 não está cheio")
	f.fluido_qtd = 50000.0
	verificar(f.condicao_cumprida(), "cheio de fluido")
	f.condicoes.erase("7")
	verificar(f.condicao_cumprida(), "sem condição: parada curta")


func test_salva_condicoes() -> void:
	var d := _duas()
	var t: Trem = d.t
	t.condicoes[str(d.a)] = "cheio"
	var trens: Array[Trem] = [t]
	_rodar(trens, d.est, 20.0)
	var salvo: Dictionary = str_to_var(var_to_str(t.para_salvar()))          # como vai para o arquivo
	var t2 := Trem.de_salvo(salvo, d.g)
	verificar(t2 != null, "volta do salvo")
	igual(t2.condicao(d.a), "cheio", "condição salva")
	igual(t2.parado_em, d.a, "parado na estação certa")
	var antigo := t.para_salvar()
	antigo.erase("condicoes")
	antigo.erase("parado_em")
	var t3 := Trem.de_salvo(str_to_var(var_to_str(antigo)), d.g)
	verificar(t3 != null and t3.condicoes.is_empty(), "salvo antigo sem condições")
