extends Caso
## Painel de estrutura: ligar/desligar, estado com causa, estatística, copiar/colar, filtro e inventário do baú, modos do braço, faixa.


func _base() -> Dictionary:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-12, 24):
		for y in range(-12, 24):
			m.limpar_obstaculo(Vector2i(x, y))
	var f := Fabrica.new(m)
	return {"m": m, "f": f}


func test_estado_com_causa() -> void:
	var m := Maquina.new("montadora", 1.0)
	igual(Fabrica.causa_maquina(m), "sem receita", "começa sem receita")
	var rid: String = Registro.receitas_da_maquina("montadora")[0]
	m.definir_receita(rid, Registro.receitas[rid])
	m.energia = 1.0
	m.tick(0.1)
	var it: String = Registro.receitas[rid].entradas.keys()[0]
	verificar(Fabrica.causa_maquina(m).begins_with("falta "), "sem insumo diz o que falta: " + Fabrica.causa_maquina(m))
	verificar(Fabrica.causa_maquina(m).contains(Registro.itens[it].nome), "nomeia o insumo")
	m.energia = 0.0
	m.acordar()
	m.tick(0.1)
	igual(Fabrica.causa_maquina(m), "sem energia", "sem energia")
	m.estado = Maquina.Estado.SAIDA_CHEIA
	verificar(Fabrica.causa_maquina(m).begins_with("saída cheia"), "saída cheia")
	m.estado = Maquina.Estado.DESLIGADA
	igual(Fabrica.causa_maquina(m), "desligada", "desligada")
	igual(Fabrica.causa_maquina(m, true), "desligada pelo comparador", "comparador")


func test_ligar_desligar() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	f.reconstruir()
	f.combustivel[id] = 50.0
	var mq: Maquina = f.maquinas[id]
	var rid := "fundir_ferro" if Registro.receitas.has("fundir_ferro") else Registro.receitas_da_maquina("fornalha")[0]
	f.escolher_receita(id, rid)
	for k in Registro.receitas[rid].entradas:
		mq.entradas[k] = int(Registro.receitas[rid].entradas[k]) * 2
	mq.acordar()
	f.tick(0.1)
	igual(mq.estado, Maquina.Estado.TRABALHANDO, "ligada trabalha")
	var prog := mq.progresso
	m.estruturas[id]["desligada"] = true
	var comb: float = f.combustivel[id]
	for i in 10:
		f.tick(0.1)
	igual(mq.estado, Maquina.Estado.DESLIGADA, "estado próprio")
	perto(mq.progresso, prog, 1e-5, "desligada não anda")
	perto(f.combustivel[id], comb, 1e-5, "desligada não queima combustível")
	igual(Fabrica.causa_maquina(mq), "desligada", "palavra certa")
	m.estruturas[id].erase("desligada")
	for i in 3:
		f.tick(0.1)
	igual(mq.estado, Maquina.Estado.TRABALHANDO, "religada volta")
	verificar(mq.progresso > prog, "religada anda")


## Ela dormia (sem insumo) quando foi desligada: ao religar, não pode ficar presa em "desligada".
func test_religar_acorda_quem_dormia() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var id: int = (b.m as MapaOcupacao).colocar("fornalha", Vector2i(2, 2), 0)
	f.reconstruir()
	f.combustivel[id] = 50.0
	f.escolher_receita(id, Registro.receitas_da_maquina("fornalha")[0])
	f.tick(0.1)
	verificar(f.maquinas[id].dormindo(), "dormiu sem insumo")
	(b.m as MapaOcupacao).estruturas[id]["desligada"] = true
	f.tick(0.1)
	(b.m as MapaOcupacao).estruturas[id].erase("desligada")
	f.tick(0.1)
	igual(f.maquinas[id].estado, Maquina.Estado.SEM_INSUMO, "acordou e voltou ao que era")


func test_salvar_guarda_o_novo() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	var bau := m.colocar("bau", Vector2i(8, 2), 0)
	var br := m.colocar("braco", Vector2i(12, 2), 0)
	m.estruturas[id]["desligada"] = true
	m.estruturas[bau]["aceita"] = ["pedra"]
	m.estruturas[bau]["aceita_limite"] = 100
	m.estruturas[bau]["ordem"] = "qtd"
	m.estruturas[br]["modo_braco"] = "radial"
	f.reconstruir()
	f.maquinas[id].tempo_total = 90.0
	f.maquinas[id].tempo_ativo = 45.0
	f.maquinas[id].produzidos = 7
	var texto := var_to_str({"e": m.estruturas, "f": f.estado()})       # como o save
	var d: Dictionary = str_to_var(texto)
	var m2 := MapaOcupacao.new(GeradorMundo.new(1337))
	m2.restaurar(d.e, m.limpos.keys(), m._prox_id, {})
	var f2 := Fabrica.new(m2)
	f2.restaurar(d.f)
	verificar(m2.estruturas[id].get("desligada", false), "desligada volta")
	f2.tick(0.1)
	igual(f2.maquinas[id].estado, Maquina.Estado.DESLIGADA, "e segue desligada")
	perto(f2.maquinas[id].tempo_total, 90.1, 0.01, "tempo total")
	perto(f2.maquinas[id].tempo_ativo, 45.0, 0.01, "tempo trabalhando")
	igual(f2.maquinas[id].produzidos, 7, "ciclos")
	igual(m2.estruturas[bau].aceita, ["pedra"], "filtro do baú")
	igual(int(m2.estruturas[bau].aceita_limite), 100, "limite por tipo")
	igual(m2.estruturas[bau].ordem, "qtd", "ordem")
	verificar(Portas.braco_radial(m2.estruturas[br]), "modo do braço")
	igual(f2.bracos[br].origens.size(), 3, "volta com as 3 origens")
	# save antigo, sem o campo: estatística começa do zero
	var sem: Dictionary = d.f.duplicate(true)
	sem.maquinas[id].erase("tempo")
	var f3 := Fabrica.new(m2)
	f3.restaurar(sem)
	perto(f3.maquinas[id].tempo_total, 0.0, 1e-6, "save antigo")


func test_estatistica() -> void:
	var m := Maquina.new("fornalha", 1.0)
	var rid: String = Registro.receitas_da_maquina("fornalha")[0]
	m.definir_receita(rid, Registro.receitas[rid])
	m.estado = Maquina.Estado.TRABALHANDO
	m.contar(10.0)
	m.estado = Maquina.Estado.SEM_INSUMO
	m.contar(10.0)
	perto(m.tempo_ativo, 10.0, 1e-6, "só o tempo trabalhando")
	perto(m.tempo_total, 20.0, 1e-6, "tempo todo")
	m.produzidos = 4
	var por_ciclo := 0
	for k in Registro.receitas[rid].saidas:
		por_ciclo += int(Registro.receitas[rid].saidas[k])
	perto(m.itens_por_minuto(), 4.0 * 60.0 / 20.0 * por_ciclo, 1e-4, "ritmo antes da janela fechar")
	m.contar(10.0)                                              # 30 s: fecha a janela
	perto(m.ciclos_min, 4.0 * 2.0, 1e-4, "ciclos por minuto")
	m.contar(30.0)
	perto(m.ciclos_min, 0.0, 1e-4, "janela seguinte sem produzir")


func test_copiar_colar() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var a := m.colocar("montadora", Vector2i(0, 0), 0)
	var c := m.colocar("montadora", Vector2i(6, 0), 0)
	var fo := m.colocar("fornalha", Vector2i(12, 0), 0)
	f.reconstruir()
	var rs: Array[String] = Registro.receitas_da_maquina("montadora")
	f.escolher_receita(a, rs[0])
	m.estruturas[a]["modo"] = "turbo"
	m.estruturas[a]["desligada"] = true
	var cfg := f.copiar_config(a)
	verificar(f.tem_config(a), "tem o que copiar")
	igual(cfg.receita, rs[0], "copiou a receita")
	verificar(not f.pode_colar(fo, cfg), "só em outra igual")
	igual(f.colar_config(fo, cfg).ok, false, "fornalha recusa")
	# receita já escolhida na outra: colar troca
	f.escolher_receita(c, rs[1])
	m.estruturas[c]["limite"] = 0.5                              # o que a origem não tem some na colada
	var r := f.colar_config(c, cfg)
	verificar(r.ok, "colou")
	igual(f.maquinas[c].receita_id, rs[0], "receita igual à de origem")
	igual(m.estruturas[c].modo, "turbo", "modo")
	verificar(r.remontar, "modo muda a velocidade: remonta")
	verificar(not m.estruturas[c].has("limite"), "fica igual: tira o que a origem não tem")
	verificar(not m.estruturas[c].get("desligada", false), "ligada/desligada não é ajuste: não copia")
	# mesma receita: não mexe no que está dentro
	f.maquinas[c].entradas["pedra"] = 3
	f.colar_config(c, cfg)
	igual(int(f.maquinas[c].entradas.get("pedra", 0)), 3, "não esvazia à toa")
	# receita não pesquisada fica de fora, o resto vale
	var c2 := m.colocar("montadora", Vector2i(18, 0), 0)
	f.reconstruir()
	var r2 := f.colar_config(c2, cfg, func(_rc: String) -> bool: return false)
	igual(r2.receita_pulada, rs[0], "avisa a receita de fora")
	igual(f.maquinas[c2].receita_id, "", "sem receita")
	igual(m.estruturas[c2].modo, "turbo", "o resto vale")


func test_copiar_colar_braco_e_bau() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var a := m.colocar("braco", Vector2i(0, 0), 0)
	var c := m.colocar("braco", Vector2i(4, 0), 0)
	var ba := m.colocar("bau", Vector2i(8, 0), 0)
	var bc := m.colocar("bau", Vector2i(10, 0), 0)
	f.reconstruir()
	m.estruturas[a]["filtros"] = ["pedra"]
	m.estruturas[a]["modo_braco"] = "radial"
	var r := f.colar_config(c, f.copiar_config(a))
	verificar(r.ok, "colou")
	igual(f.bracos[c].filtros, ["pedra"], "o braço já obedece")
	igual(f.bracos[c].filtro, "pedra", "filtro único")
	verificar(r.remontar, "modo do braço pede remontar")
	m.estruturas[ba]["aceita"] = ["carvao", "pedra"]
	m.estruturas[ba]["ordem"] = "qtd"
	f.colar_config(bc, f.copiar_config(ba))
	igual(m.estruturas[bc].aceita, ["carvao", "pedra"], "filtro do baú")
	igual(m.estruturas[bc].ordem, "qtd", "ordem do baú")
	m.estruturas[ba].aceita.append("tijolo")
	verificar(not m.estruturas[bc].aceita.has("tijolo"), "cópia é cópia")


# ------------------------------------------------------------------ baú
func test_filtro_do_bau() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var id := m.colocar("bau", Vector2i(4, 4), 0)
	f.reconstruir()
	var dest: Object = f.destino_em(Vector2i(4, 4))
	verificar(dest.aceita("pedra") and dest.aceita("carvao"), "sem filtro: tudo")
	igual(f.quanto_cabe(id, "pedra"), 1600, "cabe a capacidade")
	m.estruturas[id]["aceita"] = ["pedra"]
	dest = f.destino_em(Vector2i(4, 4))
	verificar(dest.aceita("pedra"), "aceita o do filtro")
	verificar(not dest.aceita("carvao"), "recusa o resto")
	igual(f.quanto_cabe(id, "carvao"), 0, "para drone também")
	f.baus[id]["carvao"] = 3                                     # já estava: sai por braço normalmente
	igual(f.origem_em(Vector2i(4, 4)).pegar_para_braco(""), "carvao", "o que estava dentro sai")
	m.estruturas[id]["aceita_limite"] = 10
	f.baus[id]["pedra"] = 9
	igual(f.quanto_cabe(id, "pedra"), 1, "limite por tipo: falta 1")
	verificar(f.destino_em(Vector2i(4, 4)).receber("pedra"), "recebe o último")
	verificar(not f.destino_em(Vector2i(4, 4)).aceita("pedra"), "limite atingido")


## O braço de verdade: do baú de origem só passa o que o baú de destino aceita, nada fica preso na garra.
func test_filtro_do_bau_com_braco() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var de := m.colocar("bau", Vector2i(2, 2), 0)
	var br := m.colocar("braco", Vector2i(2, 3), 0)
	var para := m.colocar("bau", Vector2i(2, 4), 0)
	m.estruturas[br]["rot"] = 0
	m.estruturas[para]["aceita"] = ["pedra"]
	f.reconstruir()
	f.bracos[br].energia = 1.0
	f.baus[de].merge({"carvao": 5, "pedra": 2})
	var fo: Array = [Portas.frente_braco(m.estruturas[br]), Portas.costas_braco(m.estruturas[br])]
	verificar(fo.has(Vector2i(2, 4)) and fo.has(Vector2i(2, 2)), "braço entre os baús")
	if Portas.frente_braco(m.estruturas[br]) != Vector2i(2, 4):       # frente para o destino
		m.estruturas[br].rot = 2
		f.reconstruir()
		f.bracos[br].energia = 1.0
	for i in 300:
		f.bracos[br].tick(0.05)
	igual(int(f.baus[para].get("pedra", 0)), 2, "levou a pedra")
	igual(int(f.baus[para].get("carvao", 0)), 0, "carvão não entrou")
	igual(int(f.baus[de].get("carvao", 0)), 5, "carvão ficou")
	igual(f.bracos[br].segurando, "", "garra vazia")


func test_inventario_ordem() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var id := m.colocar("bau", Vector2i(4, 4), 0)
	f.reconstruir()
	f.baus[id].merge({"tijolo": 5, "pedra": 200, "engrenagem": 40, "carvao": 0})
	var por_qtd := f.conteudo_ordenado(id, "qtd")
	igual(por_qtd, ["pedra", "engrenagem", "tijolo"], "mais primeiro; zerado não aparece")
	var por_tipo := f.conteudo_ordenado(id, "tipo")
	var ordem := Registro.itens.keys()
	verificar(ordem.find(por_tipo[0]) < ordem.find(por_tipo[1]) and ordem.find(por_tipo[1]) < ordem.find(por_tipo[2]), "na ordem do itens.json")
	f.baus[id]["xis_antigo"] = 1
	verificar(f.conteudo_ordenado(id, "tipo").has("xis_antigo"), "item de save antigo não some")


func test_bau_estoque_silo_e_posto_tem_inventario() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	for n in ["bau_grande", "bau_estoque", "silo_granel", "posto_avancado"]:
		var id := m.colocar(n, Vector2i(0, -10) if n == "silo_granel" else Vector2i(10, 4 + ["bau_grande", "bau_estoque", "posto_avancado"].find(n) * 6), 0)
		verificar(id >= 0, "colocou " + n)
		f.reconstruir()
		verificar(f.baus.has(id), n + " guarda")
		m.estruturas[id]["aceita"] = ["pedra"]
		igual(f.quanto_cabe(id, "carvao"), 0, n + ": filtro vale")
		verificar(f.quanto_cabe(id, "pedra") > 0, n + ": aceita")


# ------------------------------------------------------------------ modos do braço
func test_braco_linear_so_pega_atras() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var br := m.colocar("braco", Vector2i(5, 5), 0)
	var fr := Portas.frente_braco(m.estruturas[br])
	var co := Portas.costas_braco(m.estruturas[br])
	var d := fr - Vector2i(5, 5)
	var lado := Vector2i(5, 5) + Vector2i(-d.y, d.x)
	var dst := m.colocar("bau", fr, 0)
	var atras := m.colocar("bau", co, 0)
	var esq := m.colocar("bau", lado, 0)
	f.reconstruir()
	f.bracos[br].energia = 1.0
	f.baus[atras]["pedra"] = 2
	f.baus[esq]["carvao"] = 2
	for i in 200:
		f.bracos[br].tick(0.05)
	igual(int(f.baus[dst].get("pedra", 0)), 2, "linear: pegou atrás")
	igual(int(f.baus[dst].get("carvao", 0)), 0, "linear: não pega do lado")
	igual(f.bracos[br].origens.size(), 0, "linear: sem lista")


func test_braco_radial_rodizio() -> void:
	var b := _base()
	var f: Fabrica = b.f
	var m: MapaOcupacao = b.m
	var br := m.colocar("braco", Vector2i(5, 5), 0)
	m.estruturas[br]["modo_braco"] = "radial"
	var ts := Portas.origens_braco(m.estruturas[br])
	igual(ts.size(), 3, "três lados")
	var fr := Portas.frente_braco(m.estruturas[br])
	verificar(not ts.has(fr), "a frente é destino, não origem")
	var dst := m.colocar("bau", fr, 0)
	var ids := []
	for t in ts:
		ids.append(m.colocar("bau", t, 0))
	f.reconstruir()
	var bra: Braco = f.bracos[br]
	bra.energia = 1.0
	for i in 3:
		f.baus[ids[i]]["pedra"] = 10
	var vistos := []
	var ant := -1
	for i in 2000:
		if bra.segurando != "" and bra.entregues != ant:
			ant = bra.entregues
			vistos.append(bra.origem_i)
		bra.tick(0.02)
		if vistos.size() >= 9:
			break
	igual(vistos.slice(0, 6), [0, 1, 2, 0, 1, 2], "rodízio entre as origens, sem privilegiar")
	# só uma tem o item aceito: vai nela (filtro do braço)
	f.baus[ids[0]].clear()
	f.baus[ids[1]].clear()
	f.baus[ids[1]]["carvao"] = 4
	f.baus[ids[2]].clear()
	for i in 200:
		bra.tick(0.05)
	var d_pedra := int(f.baus[dst].get("pedra", 0))
	igual(int(f.baus[dst].get("carvao", 0)), 4, "foi buscar onde tem")
	igual(bra.origem_i, 1, "o animador sabe o lado")
	bra.filtros = ["pedra"]
	f.baus[ids[1]]["carvao"] = 5
	f.baus[ids[2]]["pedra"] = 1
	for i in 200:
		bra.tick(0.05)
	igual(int(f.baus[dst].get("pedra", 0)), d_pedra + 1, "filtro: pegou a pedra")
	igual(int(f.baus[ids[1]].carvao), 5, "filtro: carvão ficou")
	# destino recusa: não pega o que ficaria preso
	m.estruturas[dst]["aceita"] = ["tijolo"]
	f.reconstruir()
	bra.filtros = []
	f.baus[ids[2]]["pedra"] = 1
	for i in 100:
		bra.tick(0.05)
	igual(bra.segurando, "", "destino não aceita: garra vazia")


func test_braco_quantico_fica_linear() -> void:
	var e := {"nome": "braco_quantico", "minimo": Vector2i(0, 0), "rot": 0, "modo_braco": "radial"}
	verificar(not Portas.braco_radial(e), "quântico não entra no radial")
	igual(Portas.origens_braco(e).size(), 1, "só atrás")


## O aviso de porta entende o Radial: braço que encosta na máquina pelo lado dele tira dela.
func test_radial_atende_porta_de_saida() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var id := m.colocar("fornalha", Vector2i(2, 2), 0)
	var e: Dictionary = m.estruturas[id]
	var fora := Vector2i(2 + e.area.x, 2)                         # encostado a leste
	var br := m.colocar("braco", fora, 1)                         # girado: a fornalha fica de lado para ele?
	var eb: Dictionary = m.estruturas[br]
	var dentro := Grade.tiles_da_area(e.minimo, e.area, e.rot)
	var rot_lado := -1
	for r in 4:
		eb.rot = r
		if not dentro.has(Portas.frente_braco(eb)) and not dentro.has(Portas.costas_braco(eb)):
			rot_lado = r
			break
	verificar(rot_lado >= 0, "há giro com a máquina de lado")
	eb.rot = rot_lado
	verificar(not Portas.braco_serve(m, e, false), "linear de lado: não tira da máquina")
	eb["modo_braco"] = "radial"
	verificar(Portas.braco_serve(m, e, false), "radial de lado: tira")
	verificar(not Portas.braco_serve(m, e, true), "radial não põe (a frente é outra)")


# ------------------------------------------------------------------ faixa
func test_faixa_desvia() -> void:
	var tela := Vector2(1600, 900)
	var ferr := Rect2(1200, 6, 360, 30)
	var cat := Rect2(1560, 200, 34, 400)
	var status := Rect2(6, 6, 330, 50)
	var obst: Array[Rect2] = [ferr, cat, status]
	var livre := BarraConstrucao.lugar_faixa(tela, 40.0, 44.0, obst, 220.0, 440.0)
	verificar(not _toca(livre, obst), "sem lista: nada coberto")
	verificar(livre.end.x > 1400.0, "mora à direita (%s)" % livre)
	var pecas := Rect2(1240, 40, 310, 850)                        # lista aberta: não pode mais ficar lá
	obst.append(pecas)
	var com := BarraConstrucao.lugar_faixa(tela, 40.0, 44.0, obst, 220.0, 440.0)
	verificar(not _toca(com, obst), "lista aberta: não cobre (%s)" % com)
	verificar(com.end.x <= pecas.position.x, "deslizou para a esquerda da lista")
	perto(com.position.y, livre.position.y, 0.01, "mesma altura")
	var gaveta := Rect2(6, 60, 300, 830)
	var estoque := Rect2(312, 60, 90, 300)
	obst.append(gaveta)
	obst.append(estoque)
	var tudo := BarraConstrucao.lugar_faixa(tela, 40.0, 44.0, obst, 220.0, 440.0)
	verificar(not _toca(tudo, obst), "gaveta, estoque e lista: no vão (%s)" % tudo)
	# tela estreita sem vão na altura: desce, sem cobrir
	var estreita := Vector2(800, 600)
	var o2: Array[Rect2] = [Rect2(0, 0, 800, 40), Rect2(0, 40, 300, 200), Rect2(320, 40, 480, 120)]
	var baixo := BarraConstrucao.lugar_faixa(estreita, 40.0, 44.0, o2, 220.0, 440.0)
	verificar(not _toca(baixo, o2), "desceu até caber (%s)" % baixo)
	verificar(Rect2(Vector2.ZERO, estreita).encloses(baixo), "dentro da tela")


func _toca(r: Rect2, obst: Array[Rect2]) -> bool:
	for o in obst:
		if r.intersects(o):
			return true
	return false
