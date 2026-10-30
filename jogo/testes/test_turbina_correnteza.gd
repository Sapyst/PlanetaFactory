extends Caso
## Turbina de correnteza (turbina_correnteza, lote 13 — energia I): modelo do estudo (estudo_turbina_correnteza.py,
## do Antigravity; arte/estudos/conv_lote13.py) com o rotor e a boia do estudo; pesquisa turbina_rio (bomba d'água +
## renovável; básico/automação × 30, 6 s). Vai no rio (pelo menos metade da área em água corrente; flutua, sem
## plataforma) e dá até 150 kW × a vazão do rio (Clima.vazao_rio: cheia na primavera, seca no verão, + chuva).


## Um 2×2 todo em tile de rio e um 2×2 em terra firme.
func _lugares(g: GeradorMundo, m: MapaOcupacao) -> Dictionary:
	var out := {}
	for x in range(-300, 300, 2):
		for y in range(-300, 300, 2):
			var t := Vector2i(x, y)
			if not out.has("rio") and m.motivo_bloqueio("turbina_correnteza", t, 0) == "":
				var todo := true
				for dx in 2:
					for dy in 2:
						todo = todo and g.terreno(t + Vector2i(dx, dy)) == GeradorMundo.Terreno.RIO
				if todo:
					out["rio"] = t
			if not out.has("terra") and g.terreno(t) == GeradorMundo.Terreno.TERRA and g.terreno(t + Vector2i(1, 1)) == GeradorMundo.Terreno.TERRA \
					and t.length() > 60:
				for dx in 2:
					for dy in 2:
						m.limpar_obstaculo(t + Vector2i(dx, dy))
				if m.motivo_bloqueio("gerador", t, 0) == "":
					out["terra"] = t
			if out.size() == 2:
				return out
	return out


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("turbina_correnteza", {})
	igual(Fiacao.papel("turbina_correnteza"), "fonte", "fonte de energia")
	perto(float(r.energia_kw), -150.0, 1e-6, "150 kW (árvore)")
	igual(r.get("renovavel", ""), "rio", "renovável do rio")
	verificar(bool(r.get("no_rio", false)) and bool(r.get("flutua", false)), "vai no rio, flutuando")
	var md: Dictionary = Registro.modelos.get("turbina_correnteza", {})
	igual(Registro.area("turbina_correnteza"), Vector2i(2, 2), "2×2")
	igual(md.get("estudo", ""), "estudo_turbina_correnteza.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (rotor e boia do estudo)")
	verificar(float(md.dims[0]) <= 2.1 and float(md.dims[1]) <= 2.1, "cabe na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 6000, "leve (%d triângulos)" % md.tris)
	verificar(md.get("portas", []).is_empty(), "sem bocas")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/turbina_correnteza.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Energia" and "turbina_correnteza" in cat.pecas), "no menu (Energia)")
	verificar(not Registro.progressao.custos.get("turbina_correnteza", {}).is_empty(), "custo de construção")
	verificar(Registro.menu.motivos.has("fora_do_rio"), "motivo explicado na barra")


func test_modelo_gira_o_rotor() -> void:
	var cena: PackedScene = load(str(Registro.modelos.turbina_correnteza.modelo))
	var raiz := cena.instantiate()
	var ap: AnimationPlayer = null
	for p in raiz.find_children("*", "AnimationPlayer", true, false):
		ap = p
	verificar(ap != null and ap.has_animation("trabalho"), "laço 'trabalho' do estudo")
	if ap != null and ap.has_animation("trabalho"):
		var an := ap.get_animation("trabalho")
		perto(an.length, 4.0, 0.1, "laço de 4 s")
		verificar(an.get_track_count() >= 3, "rotor, boia e luzes animados (%d trilhas)" % an.get_track_count())
	raiz.free()


func test_so_no_rio() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var l := _lugares(g, m)
	verificar(l.has("rio") and l.has("terra"), "achou rio e terra (%s)" % str(l))
	if l.size() < 2:
		return
	igual(m.motivo_bloqueio("turbina_correnteza", l.terra, 0), "fora_do_rio", "em terra firme não vai")
	var id := m.colocar("turbina_correnteza", l.rio, 0)
	verificar(id >= 0, "no rio vai")
	verificar(m.estruturas[id].get("sobre_agua", false), "fica sobre a água (não barra o rio)")


func test_rende_com_a_vazao() -> void:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	var l := _lugares(g, m)
	if not l.has("rio"):
		verificar(false, "sem rio no mapa de teste")
		return
	var t := m.colocar("turbina_correnteza", l.rio, 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.rio = 1.0
	perto(-f.kw_de(t), 150.0, 1e-3, "rio cheio: 150 kW")
	f.rio = 0.35
	perto(-f.kw_de(t), 52.5, 1e-3, "na seca: cai junto com a vazão")
	f.rio = 0.0
	perto(-f.kw_de(t), 0.0, 1e-6, "rio parado: nada")


func test_vazao_do_clima() -> void:
	var c := Clima.new(3)
	var nomes := {}
	for i in Registro.clima.estacoes.size():
		c.estacao = i
		c.valores["chuva"] = 0.0
		nomes[c.nome_estacao()] = c.vazao_rio()
	verificar(float(nomes["Verão"]) < 0.5, "seca no verão (%.2f)" % float(nomes["Verão"]))
	perto(float(nomes["Primavera"]), 1.0, 1e-6, "cheia na primavera")
	c.estacao = 1
	var seco := c.vazao_rio()
	c.valores["chuva"] = 1.0
	verificar(c.vazao_rio() > seco, "a chuva engrossa o rio")
	verificar(c.vazao_rio() <= 1.0, "até a vazão cheia")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("turbina_rio"), "Turbina de correnteza ligada no jogo")
	verificar(not p.em_desenvolvimento("turbina_rio"), "fora do em desenvolvimento")
	igual(p.custo("turbina_rio"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "custo da árvore")
	verificar(not p.peca_liberada("turbina_correnteza"), "começa travada")
	p.concluidas = {"bomba_agua": true, "renovavel": true}
	verificar(p.disponivel("turbina_rio"), "com bomba d'água e renovável: pesquisável")
	p.concluidas["turbina_rio"] = true
	verificar(p.peca_liberada("turbina_correnteza"), "libera a turbina")
