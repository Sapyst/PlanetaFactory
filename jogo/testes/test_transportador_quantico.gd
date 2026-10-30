extends Caso
## Transportador quântico (transportador_quantico, lote 17): modelo do estudo (estudo_transportador_quantico.py, do
## Antigravity; arte/estudos/conv_lote17.py) com os anéis em contra-rotação; o braço põe na entrada (sul) e os itens
## saem, sem trilho, na saída (norte) de outro transportador do mesmo canal, 5 por segundo com energia. A pesquisa
## (colônias + computação quântica; pede o pacote quântico) está ligada mas segue "em desenvolvimento".


func _mapa() -> MapaOcupacao:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(190, 260):
		for y in range(-8, 8):
			m.limpar_obstaculo(Vector2i(x, y))
	return m


func test_dados_e_modelo() -> void:
	var r := Transportador.regra("transportador_quantico")
	verificar(Transportador.eh_transportador("transportador_quantico"), "regra do transportador")
	igual(Fiacao.papel("transportador_quantico"), "consumo", "precisa de energia")
	verificar(int(r.taxa) > 0, "taxa de itens/s")
	var md: Dictionary = Registro.modelos.get("transportador_quantico", {})
	igual(Registro.area("transportador_quantico"), Vector2i(3, 3), "3×3")
	igual(md.get("estudo", ""), "estudo_transportador_quantico.py", "convertido do estudo do Antigravity")
	verificar(bool(md.get("anima", false)), "anima (anéis em contra-rotação)")
	verificar(float(md.dims[0]) <= 3.0 and float(md.dims[1]) <= 3.0, "na área (%s)" % str(md.dims))
	verificar(int(md.tris) <= 9000, "leve (%d triângulos)" % md.tris)
	var io := {}
	for p in md.get("portas", []):
		io[p.io] = p.dir
	verificar(io.has("ENT") and io.ENT[1] < 0 and io.has("SAI") and io.SAI[1] > 0, "entra ao sul, sai ao norte")
	verificar(ResourceLoader.exists(str(md.get("modelo", ""))), "modelo .glb no jogo")
	verificar(ResourceLoader.exists("res://assets/icones/transportador_quantico.png"), "ícone na barra")
	verificar(Registro.menu.categorias.any(func(cat): return cat.nome == "Proliferação" and "transportador_quantico" in cat.pecas), "no menu (Proliferação)")
	var raiz: Node = (load(str(md.modelo)) as PackedScene).instantiate()
	for n in raiz.find_children("*", "Node3D", true, false):
		var i := String(n.name).rfind("_")
		var suf := String(n.name).substr(i + 1) if i > 0 else ""
		verificar(not suf in ["giro", "antena", "cristal", "canhao", "rotor", "haste", "camisa"], "nome neutro: " + n.name)
	raiz.free()


func test_pesquisa_em_desenvolvimento() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("transportador_quantico"), "ligada no jogo")
	verificar(p.arvore().transportador_quantico.get("existente", false), "marcada como existente na árvore")
	verificar(p.em_desenvolvimento("transportador_quantico"), "em desenvolvimento")
	verificar(not Registro.itens.has("pacote_quantico"), "o pacote quântico (forja quântica) ainda não existe")
	verificar(p.motivo_desenvolvimento("transportador_quantico").contains("quântico"), "o motivo diz o pacote (%s)" % p.motivo_desenvolvimento("transportador_quantico"))
	verificar(p.peca_em_desenvolvimento("transportador_quantico"), "em cinza fora da demonstração")
	verificar(not Pesquisa.new(true).peca_em_desenvolvimento("transportador_quantico"), "na demonstração se constrói")


func test_troca_itens_pelo_canal() -> void:
	var m := _mapa()
	var a := m.colocar("transportador_quantico", Vector2i(200, 0), 0)
	var b := m.colocar("transportador_quantico", Vector2i(240, 0), 0)
	var c := m.colocar("transportador_quantico", Vector2i(220, 0), 0)
	verificar(a >= 0 and b >= 0 and c >= 0, "couberam")
	var en := [1.0]
	var t := Transportador.new(m)
	t.energia = func(_id: int) -> float: return en[0]
	t.mudar_canal(c, "B")
	igual(t.pares(a), [b] as Array[int], "A: só o outro do canal A")
	var f := Fabrica.new(m)
	f.reconstruir()
	var dest: Object = f.destino_em(Vector2i(201, 1))
	for i in 25:
		dest.receber("engrenagem")
	igual(Transportador.total(t.entrada(a)), 20, "entrada cabe 20")
	t.tick(1.0)
	igual(int(t.saida(b).get("engrenagem", 0)), 5, "5 itens/s chegaram no outro")
	igual(Transportador.total(t.saida(c)), 0, "o do canal B não recebe")
	verificar(t.trabalhando(a) and t.trabalhando(b), "os dois animam")
	en[0] = 0.5
	t.tick(1.0)
	igual(int(t.saida(b).get("engrenagem", 0)), 7, "meia energia: 2,5/s")
	en[0] = 0.0
	t.tick(1.0)
	igual(int(t.saida(b).get("engrenagem", 0)), 7, "sem energia: para")
	var orig: Object = f.origem_em(Vector2i(241, 1))
	igual(orig.pegar_para_braco(""), "engrenagem", "o braço tira da saída")
	verificar(f.origem_em(Vector2i(201, 1)).pegar_para_braco("") == "", "a saída do primeiro está vazia (a entrada não sai por braço)")


func test_sem_par_ou_saida_cheia_espera() -> void:
	var m := _mapa()
	var a := m.colocar("transportador_quantico", Vector2i(200, 0), 0)
	var b := m.colocar("transportador_quantico", Vector2i(240, 0), 0)
	var t := Transportador.new(m)
	t.mudar_canal(b, "C")
	t.entrada(a)["pedra"] = 10
	t.tick(2.0)
	igual(int(t.entrada(a).get("pedra", 0)), 10, "sem par no canal: a entrada espera")
	t.mudar_canal(b, "A")
	t.saida(b)["placa_ferro"] = 199
	t.tick(2.0)
	igual(Transportador.total(t.saida(b)), 200, "só até encher a saída (200)")
	igual(int(t.entrada(a).get("pedra", 0)), 9, "o resto espera")
