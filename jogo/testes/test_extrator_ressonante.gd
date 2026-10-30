extends Caso
## Extrator ressonante (extrator_ressonante, lote 11): 2× o extrator no cristal; despeja na esteira ao sul.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("extrator_ressonante", {})
	var r1: Dictionary = Registro.estruturas.extrator_cristal
	igual(r.get("maquina", ""), "extrator", "extrai como o extrator")
	igual(r.get("requer_jazida", []), r1.requer_jazida, "a mesma jazida")
	perto(float(r.velocidade) / float(r1.velocidade), 2.0, 1e-6, "2× (árvore)")
	verificar("extrator_ressonante" in Fabrica.DESPEJA_NA_ESTEIRA, "despeja na esteira")
	UtilLote11.modelo(self, "extrator_ressonante", ["PORTA_ITEM_SAI_S1", "PORTA_FLUIDO_ENT_O1"])


func test_extrai_e_despeja() -> void:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.jazida(m, "extrator_ressonante")
	verificar(o.x != 9999, "achou jazida de cristal")
	var c := Construtor.new(m)
	var b := m.colocar("extrator_ressonante", o, 0)
	verificar(b >= 0, "colocou")
	var e: Dictionary = m.estruturas[b]
	var pm := Grade.porta_no_mundo(Registro.modelos.extrator_ressonante.portas.filter(func(p): return p.tipo == "ITEM")[0], e.minimo, e.area, e.rot)
	c.executar(c.plano_linha("esteira", pm.tile_fora, pm.tile_fora + pm.dir * 3, Construtor.rot_do_fluxo(Grade.DIRECOES.find(pm.dir))))
	var ge := m.colocar("gerador", o + Vector2i(5, 0), 0)
	m.colocar("poste_energia", o + Vector2i(4, 1), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.combustivel[ge] = 40.0
	igual(f.maquinas[b].receita_id, "extrair_cristal", "extrai cristal")
	for i in 40:
		f.tick(0.25)
	verificar(f.caminhos[0].esteira.itens.size() > 0, "o cristal foi para a esteira sem braço")
	verificar(f.maquinas[b].produzidos >= 8, "2× : ~10 em 10 s (%d)" % f.maquinas[b].produzidos)


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "extrator_2", "extrator_ressonante")
