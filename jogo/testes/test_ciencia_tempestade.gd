extends Caso
## Ciência de tempestade (fase 2.5): pacote de tempestade (1 cristal carregado + 1 módulo de controle + 1 liga leve → 2,
## 15 s; na montadora — a montadora 2 da árvore ainda não existe) e as pesquisas que ele destrava: dano de energia 4,
## cadência de energia 2, escudo 2 (bolha de 12 m, 1.000 de dano, recarga 2×) e com ele o muro de campo, mais as
## melhorias de bala, foguete e artilharia.


func _int(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = int(d[k])
	return out


const T6 := {"pacote_pesquisa": 150, "pacote_automacao": 150, "pacote_militar": 150, "pacote_quimico": 150, "pacote_ecologico": 150, "pacote_tempestade": 150}


func test_pacote() -> void:
	verificar(Registro.itens.has("pacote_tempestade"), "item")
	igual(Registro.itens.pacote_tempestade.nome, "Pacote de tempestade")
	verificar(ResourceLoader.exists("res://assets/icones/itens/pacote_tempestade.png"), "ícone")
	verificar(Registro.modelos.has(Registro.itens.pacote_tempestade.get("modelo_de", "")), "modelo (derivado) na esteira")
	var r: Dictionary = Registro.receitas.pacote_tempestade
	igual(r.maquina, "montadora")
	igual(_int(r.entradas), {"cristal_carregado": 1, "modulo_controle": 1, "liga_leve": 1}, "receita da árvore")
	igual(_int(r.saidas), {"pacote_tempestade": 2}, "→ 2")
	perto(float(r.tempo), 15.0, 1e-6, "15 s")
	igual(Pesquisa.TIPOS_PACOTE.tempestade, "pacote_tempestade", "tipo 'tempestade' da árvore")
	# a montadora faz
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 6):
		for y in range(-2, 6):
			m.limpar_obstaculo(Vector2i(x, y))
	var id := m.colocar("montadora", Vector2i(0, 0), 0)
	var f := Fabrica.new(m)
	f.reconstruir()
	f.escolher_receita(id, "pacote_tempestade")
	var mq: Maquina = f.maquinas[id]
	for it in ["cristal_carregado", "modulo_controle", "liga_leve"]:
		verificar(mq.receber(it), "aceita " + it)
	mq.energia = 1.0
	for i in 22 * 10:
		mq.tick(0.1)
	igual(int(mq.saidas.get("pacote_tempestade", 0)), 2, "2 pacotes em 20 s (velocidade 0,75)")


func test_ciencia() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("ciencia_tempestade"), "jogável")
	p.concluidas = {"captador_carga": true, "processador": true, "liga_leve": true}
	verificar(not p.disponivel("ciencia_tempestade"), "espera a bioquímica")
	p.concluidas["bioquimica"] = true
	verificar(p.disponivel("ciencia_tempestade"), "captador + processador + liga leve + bioquímica")
	igual(p.custo("ciencia_tempestade"), {"pacote_pesquisa": 100, "pacote_automacao": 100, "pacote_quimico": 100, "pacote_ecologico": 100}, "custo da árvore")
	verificar(not p.pacote_liberado("pacote_tempestade"), "laboratório ainda não estoca o de tempestade")
	verificar(not p.receita_liberada("pacote_tempestade"), "receita travada antes")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.receita_liberada("pacote_tempestade"), "libera a receita")
	verificar(p.pacote_liberado("pacote_tempestade"), "e o laboratório passa a aceitar o pacote")


func test_destrava_energia_4_e_cadencia_2() -> void:
	var p := Pesquisa.new()
	p.concluidas = {"dano_energia_3": true, "cadencia_energia_1": true}
	verificar(not p.disponivel("dano_energia_4") and not p.disponivel("cadencia_energia_2"), "sem tempestade, travadas")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("dano_energia_4"), "dano de energia 4 pesquisável")
	verificar(p.disponivel("cadencia_energia_2"), "cadência de energia 2 pesquisável")
	igual(p.custo("dano_energia_4"), T6, "custo da árvore (6 tipos × 150)")
	igual(p.custo("cadencia_energia_2"), T6, "custo da árvore")
	var antes := p.bonus("dano_torre_energia")
	p.concluidas["dano_energia_4"] = true
	perto(p.bonus("dano_torre_energia") - antes, 0.3, 1e-6, "+30% de dano")
	var c0 := p.bonus("cadencia_torre_energia")
	p.concluidas["cadencia_energia_2"] = true
	perto(p.bonus("cadencia_torre_energia") - c0, 0.2, 1e-6, "+20% de tiros")
	# e chega na torre de verdade
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	var col := Colonia.new(m, Poluicao.new(m.gerador), 3)
	col.bonus = p.bonus
	perto(col._bonus("dano_torre_energia"), p.bonus("dano_torre_energia"), 1e-6, "a colônia lê o bônus")


func test_melhorias_de_tempestade() -> void:
	var p := Pesquisa.new()
	for par in [["dano_bala_4", "dano_bala_3", "dano_bala", 0.2], ["cadencia_bala_3", "cadencia_bala_2", "cadencia_bala", 0.2],
			["dano_foguete_2", "dano_foguete_1", "dano_foguete", 0.3], ["cadencia_foguete_2", "cadencia_foguete_1", "cadencia_foguete", 0.2],
			["dano_artilharia_1", "artilharia", "dano_artilharia", 0.3], ["alcance_artilharia_1", "artilharia", "alcance_artilharia", 0.2]]:
		verificar(p.jogavel(par[0]), "jogável: " + par[0])
		p.concluidas = {par[1]: true}
		verificar(not p.disponivel(par[0]), "espera a tempestade: " + par[0])
		p.concluidas["ciencia_tempestade"] = true
		verificar(p.disponivel(par[0]), "pesquisável: " + par[0])
		igual(p.custo(par[0]), T6, "custo da árvore: " + par[0])
		var antes := p.bonus(par[2])
		p.concluidas[par[0]] = true
		perto(p.bonus(par[2]) - antes, par[3], 1e-6, "bônus: " + par[0])


func test_escudo_2() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("escudo_2"), "jogável")
	p.concluidas = {"escudo_1": true}
	verificar(not p.disponivel("escudo_2"), "espera a tempestade")
	p.concluidas["ciencia_tempestade"] = true
	verificar(p.disponivel("escudo_2"), "escudo 1 + ciência de tempestade")
	igual(p.custo("escudo_2"), T6, "custo da árvore")
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-2, 14):
		for y in range(-2, 10):
			m.limpar_obstaculo(Vector2i(x, y))
	var col := Colonia.new(m, Poluicao.new(m.gerador), 3)
	col.bonus = p.bonus
	var f := Fabrica.new(m)
	f.pesquisa = p
	var g := m.colocar("gerador", Vector2i(8, 4), 0)
	m.colocar("poste_energia", Vector2i(5, 3), 0)
	var esc := m.colocar("gerador_escudo", Vector2i(2, 2), 0)
	f.reconstruir()
	f.combustivel[g] = 200.0
	perto(col.raio_escudo("gerador_escudo"), 8.0, 1e-6, "sem o escudo 2: 8 m")
	perto(f.carga_max(esc), 8.0, 1e-6, "8 MJ")
	perto(f.kw_de(esc), 200.0, 1e-6, "200 kW")
	p.concluidas["escudo_2"] = true
	perto(col.raio_escudo("gerador_escudo"), 12.0, 1e-6, "escudo 2: bolha de 12 m (árvore)")
	perto(f.carga_max(esc) / float(Registro.estruturas.gerador_escudo.escudo.mj_por_dano), 1000.0, 1e-3, "1.000 de dano (árvore)")
	perto(f.kw_de(esc), 400.0, 1e-6, "recarga 2× (árvore)")
	for i in 30 * 51:
		f.tick(1.0 / 30.0)
	perto(float(f.carga_torre[esc]), 20.0, 1e-3, "20 MJ em 50 s a 400 kW, e para de puxar")
	# a bolha maior protege uma fornalha a 10 m
	var forn := m.colocar("fornalha", Vector2i(12, 0), 0)
	verificar(forn >= 0, "fornalha a ~10 m")
	col.torre_energia = f.gastar_torre
	col.tick(1.0 / 30.0, [])
	verificar(col._escudo_absorve(forn, 10.0, Vector2(13, 1)), "dentro da bolha de 12 m")
	p.concluidas.erase("escudo_2")
	verificar(not col._escudo_absorve(forn, 10.0, Vector2(13, 1)), "na de 8 m, não")
	# muro de campo
	p.concluidas.merge({"muro_liga": true, "escudo_2": true})
	verificar(p.disponivel("muro_escudo"), "com o escudo 2 o muro de campo fica pesquisável")
