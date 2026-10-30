extends Caso
## Silo de granel (silo_granel, fase 2.2b): 3×3, 20.000 itens de UM tipo só (o primeiro que entra; vazio aceita outro).
## Modelo do estudo_silo.py (arte/estudos/conv_logistica_base.py). Braços põem e tiram por qualquer lado.


func _c() -> Construtor:
	var m := MapaOcupacao.new(GeradorMundo.new(1337))
	for x in range(-8, 14):
		for y in range(-8, 12):
			m.limpar_obstaculo(Vector2i(x, y))
	return Construtor.new(m)


func _por(c: Construtor, nome: String, t: Vector2i, rot := 0) -> int:
	var id := c.mapa.colocar(nome, t, rot)
	verificar(id >= 0, "coube %s em %s (%s)" % [nome, t, c.mapa.motivo_bloqueio(nome, t, rot)])
	return id


func test_dados_e_modelo() -> void:
	var r: Dictionary = Registro.estruturas.get("silo_granel", {})
	igual(r.get("grupo", ""), "armazem", "armazém (braços põem e tiram)")
	igual(int(r.get("capacidade_itens", 0)), 20000, "20.000 itens (árvore)")
	verificar(r.get("um_tipo", false), "um tipo só")
	igual(Registro.area("silo_granel"), Vector2i(3, 3), "3×3")
	var md: Dictionary = Registro.modelos.silo_granel
	igual(md.get("estudo", ""), "estudo_silo.py", "convertido do estudo")
	verificar(md.get("anima", false), "canecas, rosca e comporta animadas")
	verificar(int(md.get("tris", 99999)) <= 12000, "leve (%d triângulos)" % md.get("tris", 0))
	var d: Array = md.dims
	verificar(float(d[0]) <= 3.0 and float(d[1]) <= 3.0, "dentro dos 3×3 (%s)" % str(d))
	verificar(ResourceLoader.exists("res://assets/icones/silo_granel.png"), "ícone")
	verificar(Registro.menu.categorias.any(func(cat): return "silo_granel" in cat.pecas), "no menu")
	verificar(not Construtor.custo_de("silo_granel").is_empty(), "tem custo")


func test_pesquisa() -> void:
	var p := Pesquisa.new()
	verificar(p.jogavel("silo_granel"), "jogável")
	verificar(not p.peca_liberada("silo_granel"), "travado no início")
	p.concluidas = {"aco": true, "armazenagem": true, "eletronica": true}
	verificar(not p.disponivel("silo_granel"), "precisa de automação")
	p.concluidas["automacao"] = true
	verificar(p.disponivel("silo_granel"), "armazenagem + automação")
	igual(p.custo("silo_granel"), {"pacote_pesquisa": 30, "pacote_automacao": 30}, "básico × 30 + automação × 30 (árvore)")
	p.concluidas["silo_granel"] = true
	verificar(p.peca_liberada("silo_granel"), "libera o silo")


func test_um_tipo_so() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	var s := _por(c, "silo_granel", Vector2i(0, 0))
	f.reconstruir()
	igual(f.capacidade_bau(s), 20000)
	var dest: Object = f.destino_em(Vector2i(1, 1))
	verificar(dest.aceita("pedra"), "vazio aceita qualquer coisa")
	verificar(dest.receber("pedra"), "entrou pedra")
	verificar(not dest.aceita("carvao"), "com pedra dentro não aceita carvão")
	verificar(not dest.receber("carvao"), "e não recebe")
	verificar(dest.aceita("pedra"), "mais pedra, sim")
	# o outro canto do 3×3 é o mesmo silo
	verificar(not f.destino_em(Vector2i(2, 2)).aceita("carvao"), "qualquer tile do silo")
	# esvaziou: aceita outro tipo
	var ori: Object = f.origem_em(Vector2i(0, 0))
	igual(ori.pegar_para_braco(""), "pedra", "tira a pedra")
	verificar(f.destino_em(Vector2i(1, 1)).aceita("carvao"), "vazio de novo: aceita carvão")
	# cheio
	f.baus[s]["pedra"] = 20000
	verificar(not f.destino_em(Vector2i(1, 1)).aceita("pedra"), "cheio com 20.000")
	igual(Fabrica.tipo_guardado(f.baus[s]), "pedra")
	# baú comum continua aceitando de tudo
	var b := _por(c, "bau", Vector2i(6, 0))
	f.reconstruir()
	f.baus[b]["pedra"] = 1
	verificar(f.destino_em(Vector2i(6, 0)).aceita("carvao"), "baú comum mistura")


## Braço enche o silo com o que vem da esteira (pedra e carvão misturados): só entra o primeiro tipo; o outro
## segue na esteira. Depois outro braço tira do silo para um baú.
func test_bracos_poem_e_tiram() -> void:
	var c := _c()
	var f := Fabrica.new(c.mapa)
	_por(c, "gerador", Vector2i(8, 6))
	_por(c, "poste_energia", Vector2i(5, 4))
	_por(c, "poste_energia", Vector2i(11, 6))
	_por(c, "poste_energia", Vector2i(4, -1))
	c.executar(c.plano_linha("esteira", Vector2i(-6, -3), Vector2i(8, -3), 0))   # passa ao sul do silo
	var s := _por(c, "silo_granel", Vector2i(0, -1))                              # ocupa (0..2, -1..1)
	_por(c, "braco", Vector2i(1, -2), 0)                                         # pega da esteira (sul) → silo (norte)
	f.reconstruir()
	for id in f.combustivel: f.combustivel[id] = 30.0
	var tipos := ["pedra", "carvao"]
	var rodar := func(seg: float) -> void:
		var e: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(-6, -3)][0]].esteira
		for i in int(30 * seg):
			if i % 30 == 0:
				e.inserir_na_entrada(tipos[(i / 30) % 2])
			f.tick(1.0 / 30.0)
	rodar.call(30.0)
	var t := Fabrica.tipo_guardado(f.baus[s])
	verificar(t != "", "algo entrou no silo")
	var outro: String = "carvao" if t == "pedra" else "pedra"
	verificar(int(f.baus[s].get(t, 0)) >= 8, "o primeiro tipo foi enchendo o silo (%s)" % f.baus[s])
	igual(int(f.baus[s].get(outro, 0)), 0, "o outro tipo não entrou (segue na esteira)")
	var fim: EsteiraCaminho = f.caminhos[f._no_tile[Vector2i(8, -3)][0]].esteira
	verificar(fim.itens.has(outro), "o outro tipo chegou ao fim da esteira")
	# braço de saída: do silo (sul) para o baú (norte)
	_por(c, "braco", Vector2i(1, 2), 0)
	var bau := _por(c, "bau", Vector2i(1, 3))
	f.reconstruir()
	for i in 30 * 10:
		f.tick(1.0 / 30.0)
	verificar(int(f.baus[bau].get(t, 0)) > 3, "saiu do silo para o baú (%s)" % f.baus[bau])
	igual(int(f.baus[bau].get(outro, 0)), 0)
