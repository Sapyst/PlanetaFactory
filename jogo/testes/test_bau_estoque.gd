extends Caso
## Baú de estoque (pesquisa drones_logisticos, lote 16): baú 1×1 de papel fixo "estoque" na rede dos drones
## logísticos — a sobra da garra (o requisitante encheu) vem para o estoque mais perto com lugar, em vez de voltar ao
## núcleo; o requisitante que nenhum provedor atende é servido do estoque. Braços põem e tiram como num baú comum.

const DT := 1.0 / 30.0


func _base() -> Dictionary:
	var g := GeradorMundo.new(1337)
	var m := MapaOcupacao.new(g)
	for x in range(-40, 80):
		for y in range(-40, 60):
			m.limpar_obstaculo(Vector2i(x, y))
	var f := Fabrica.new(m)
	var col := Colonia.new(m, Poluicao.new(g), 3)
	var dr := Drones.new(m, f, col)
	dr.logistica_ok = func() -> bool: return true
	var nu := m.colocar("nucleo", Vector2i(0, 0), 0)
	var est := m.colocar(Drones.ESTACAO, Vector2i(m.estruturas[nu].minimo.x + 4, m.estruturas[nu].minimo.y), 0)
	verificar(est >= 0, "estação coube")
	m.estruturas[est]["drones_tipo"] = "logistico"
	f.reconstruir()
	f.tick(DT)
	for i in 2:
		var id := dr.novo(est)
		dr.drones[id].e = Drones.E.HANGAR
	return {"m": m, "f": f, "col": col, "dr": dr, "est": est}


func _rodar(b: Dictionary, s: float) -> void:
	for i in int(s / DT):
		(b.f as Fabrica).tick(DT)
		(b.dr as Drones).tick(DT)


func test_dados() -> void:
	verificar(Registro.modelos.has("bau_estoque"), "modelo (estudo_bau_estoque.py)")
	igual(Registro.modelos.bau_estoque.get("estudo", ""), "estudo_bau_estoque.py")
	igual(Registro.area("bau_estoque"), Vector2i(1, 1), "1×1 (árvore)")
	igual(Registro.estruturas.bau_estoque.grupo, "armazem", "é um baú (braços põem e tiram)")
	igual(int(Registro.estruturas.bau_estoque.capacidade_itens), 1600)
	verificar(Registro.menu.categorias.any(func(cat): return "bau_estoque" in cat.pecas), "no menu")
	verificar(Registro.menu.rotulos.has("bau_estoque"), "rótulo")
	verificar(ResourceLoader.exists("res://assets/icones/bau_estoque.png"), "ícone")
	verificar(not Construtor.custo_de("bau_estoque").is_empty(), "custo")
	var p := Pesquisa.new()
	verificar(not p.peca_liberada("bau_estoque"), "travado no início")
	p.concluidas["drones_logisticos"] = true
	verificar(p.peca_liberada("bau_estoque"), "drones logísticos liberam o estoque (árvore)")


func test_papel_fixo() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var e := m.colocar("bau_estoque", Vector2i(12, 8), 0)
	(b.f as Fabrica).reconstruir()
	igual((b.dr as Drones).papel(e), "estoque", "estoque sempre")
	m.estruturas[e]["logistica"] = "provedor"
	igual((b.dr as Drones).papel(e), "estoque", "não vira provedor")
	verificar((b.f as Fabrica).baus.has(e), "guarda itens como baú")


## Requisitante pedindo engrenagem; ninguém é provedor; o estoque tem: o drone leva do estoque.
func test_estoque_serve_o_requisitante() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var f: Fabrica = b.f
	var dr: Drones = b.dr
	var est: int = b.est
	var e := m.colocar("bau_estoque", Vector2i(-8, 12), 0)
	var req := m.colocar("bau", Vector2i(14, -6), 0)
	f.reconstruir()
	m.estruturas[req]["logistica"] = "requisitante"
	m.estruturas[req]["pede_item"] = "engrenagem"
	m.estruturas[req]["pede_qtd"] = 3
	f.baus[e]["engrenagem"] = 10
	var t := dr.tarefa_logistica(est)
	igual(t.get("de", -1), e, "sem provedor: tira do estoque")
	_rodar(b, 40.0)
	igual(int(f.baus[req].get("engrenagem", 0)), 3, "trouxe do estoque")
	igual(int(f.baus[e].get("engrenagem", 0)), 7, "o estoque baixou")
	# com provedor, o provedor vem primeiro
	var prov := m.colocar("bau", Vector2i(10, 10), 0)
	f.reconstruir()
	m.estruturas[prov]["logistica"] = "provedor"
	f.baus[prov]["engrenagem"] = 5
	m.estruturas[req]["pede_qtd"] = 6
	igual(dr.tarefa_logistica(est).get("de", -1), prov, "provedor antes do estoque")


## A sobra que não coube no requisitante vai para o estoque (antes voltava ao núcleo).
func test_sobra_vai_para_o_estoque() -> void:
	var b := _base()
	var m: MapaOcupacao = b.m
	var f: Fabrica = b.f
	var dr: Drones = b.dr
	var e := m.colocar("bau_estoque", Vector2i(-8, 12), 0)
	var req := m.colocar("bau", Vector2i(14, -6), 0)
	f.reconstruir()
	dr.bonus = func(k: String) -> float: return {"drones_carga": 3.0}.get(k, 0.0)    # 4 por viagem
	var d_id := dr.novo(b.est)
	var d: Dictionary = dr.drones[d_id]
	d.tipo = "logistico"
	d.e = Drones.E.INDO
	d.fase = "levar"
	d.de = -1
	d.para = req
	d.item = "pedra"
	d.n = 4
	m.estruturas[req]["limite"] = 1.0
	f.baus[req]["minerio_ferro"] = f.capacidade_bau(req) - 1              # só cabe 1
	_rodar(b, 40.0)
	igual(int(f.baus[req].get("pedra", 0)), 1, "coube 1 no requisitante")
	igual(int(f.baus[e].get("pedra", 0)), 3, "os outros 3 foram para o estoque")
	igual(dr.estoque_livre(b.est, Vector2(0, 0), 2000), -1, "estoque não aceita mais do que cabe")
