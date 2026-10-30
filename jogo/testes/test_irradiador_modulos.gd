extends Caso
## Irradiador de módulos (irradiador_modulos, lote 11): com energia, cada módulo encaixado (2 encaixes, só velocidade e
## eficiência) vale 50% nas máquinas e laboratórios a até 3 tiles da borda dele. Vários somam.


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("irradiador_modulos", {})
	igual(int(r.irradiador.encaixes), 2, "2 módulos (árvore)")
	igual(int(r.irradiador.raio), 3, "3 tiles (árvore)")
	igual(Fabrica.encaixes("irradiador_modulos"), 2, "encaixes")
	igual(Fiacao.papel("irradiador_modulos"), "consumo", "precisa de energia")
	UtilLote11.modelo(self, "irradiador_modulos", [])


func _base() -> Array:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var o := UtilLote11.chao(m, 30)
	verificar(o.x != 9999, "achou chão")
	UtilLote11.energia(m, o)
	return [m, o]


func test_divide_o_efeito_com_o_vizinho() -> void:
	var b := _base()
	var m: MapaOcupacao = b[0]
	var o: Vector2i = b[1]
	var ir := m.colocar("irradiador_modulos", o + Vector2i(8, 6), 0)
	var perto_a := m.colocar("montadora", o + Vector2i(13, 6), 0)    # borda a 2 tiles (x: 10 → 13)
	var lab := m.colocar("laboratorio", o + Vector2i(8, 11), 0)      # 2 tiles ao norte
	var longe := m.colocar("montadora", o + Vector2i(18, 6), 0)      # longe demais
	m.colocar("poste_energia", o + Vector2i(11, 9), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.tick(0.05)
	f.estoque_nucleo = {"modulo_velocidade_1": 2, "modulo_produtividade_1": 1}
	verificar(f.energia(ir) > 0.0, "irradiador com energia")
	verificar(not f.aceita_modulo(ir, "modulo_produtividade_1"), "produtividade não vai no irradiador")
	verificar(f.por_modulo(ir, "modulo_velocidade_1"), "encaixa")
	verificar(f.por_modulo(ir, "modulo_velocidade_1"), "encaixa o 2º")
	verificar(not f.aceita_modulo(ir, "modulo_velocidade_1"), "2 encaixes só")
	f.tick(0.05)
	perto(f.maquinas[perto_a].velocidade, 0.75 * 1.2, 1e-6, "vizinha: 2 módulos a 50% = +20%")
	perto(float(f.efeito_modulos(perto_a).energia), 1.5, 1e-6, "energia +50% (2 × 50% de +50%)")
	perto(f.kw_de(perto_a), 150.0 * 1.5, 1e-3, "consumo acompanha")
	perto(f.maquinas[longe].velocidade, 0.75, 1e-6, "longe: nada")
	perto(float(f.efeito_modulos(lab).velocidade), 1.2, 1e-6, "laboratório perto também")
	igual(f.tirar_modulo(ir, 0), "modulo_velocidade_1", "tira")
	f.tick(0.05)
	perto(f.maquinas[perto_a].velocidade, 0.75 * 1.1, 1e-6, "1 módulo: +10%")
	# sem energia não irradia
	m.estruturas[ir]["desligada"] = true
	f.tick(0.05)
	f.tick(0.05)
	perto(f.maquinas[perto_a].velocidade, 0.75, 1e-6, "desligado: sem efeito")


func test_pesquisa() -> void:
	UtilLote11.pesquisa(self, "irradiador_modulos", "irradiador_modulos")
