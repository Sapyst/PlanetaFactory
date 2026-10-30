extends Caso
## Broca de núcleo (broca_nucleo, lote 11): as jazidas da broca; jazida esgotada continua rendendo 10% para sempre.
## Hoje as jazidas do jogo não se esgotam (a Maquina tem o contador, ninguém o liga): o efeito está testado na máquina.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("broca_nucleo", {})
	igual(r.get("maquina", ""), "broca", "minera como a broca")
	igual(r.get("requer_jazida", []), Registro.estruturas.broca_minerio.requer_jazida, "as mesmas jazidas")
	perto(float(r.rende_esgotada), 0.1, 1e-6, "10% (árvore)")
	verificar("broca_nucleo" in Fabrica.DESPEJA_NA_ESTEIRA, "despeja na esteira")
	UtilLote11.modelo(self, "broca_nucleo", ["PORTA_ITEM_SAI_S1", "PORTA_FLUIDO_ENT_O1"])


func test_jazida_esgotada_rende_10_por_cento() -> void:
	var comum := Maquina.new("broca_grande", 1.0)
	var nucleo := Maquina.new("broca_nucleo", 1.0)
	nucleo.rende_esgotada = 0.1
	var cheia := Maquina.new("broca_nucleo", 1.0)
	cheia.rende_esgotada = 0.1
	var n := {}
	for q in [comum, nucleo, cheia]:
		q.definir_receita("minerar_ferro", Registro.receitas.minerar_ferro)
		q.energia = 1.0
		q.jazida_restante = 0 if q != cheia else 100000
		var k := 0
		for i in 2000:                           # 100 s; o ciclo é de 2 s
			q.tick(0.05)
			k += int(q.saidas.get("minerio_ferro", 0))
			q.saidas.erase("minerio_ferro")
			q.acordar()
		n[q] = k
	igual(n[comum], 0, "broca comum para com a jazida esgotada")
	igual(comum.estado, Maquina.Estado.SEM_JAZIDA, "e diz por quê")
	verificar(n[nucleo] >= 4 and n[nucleo] <= 5, "núcleo: 10%% do ritmo (%d em 100 s)" % n[nucleo])
	verificar(n[cheia] >= 49, "jazida cheia: ritmo normal (%d)" % n[cheia])
	igual(nucleo.jazida_restante, 0, "não consome")
	igual(nucleo.estado, Maquina.Estado.TRABALHANDO, "segue trabalhando para sempre")


func test_minera_na_fabrica() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.jazida(m, "broca_nucleo")
	verificar(o.x != 9999, "achou jazida")
	var id := m.colocar("broca_nucleo", o, 0)
	var ge := m.colocar("gerador", o + Vector2i(5, 0), 0)
	m.colocar("poste_energia", o + Vector2i(4, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[ge] = 40.0
	perto(f.maquinas[id].rende_esgotada, 0.1, 1e-6, "a regra chega na máquina")
	verificar(f.maquinas[id].receita_id.begins_with("minerar_"), "receita da jazida embaixo")
	f.tick(0.1)
	perto(f.maquinas[id].velocidade, 2.0, 1e-6, "velocidade")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "broca_profunda", "broca_nucleo")
