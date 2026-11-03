extends Caso
## Testes do Baú (Pedido 4 — Tarefa 3):
## - Inventário visível com opção de enviar tudo ou por item para a central (estoque do núcleo)
## - Remoção de baú com itens pede confirmação com contagem de itens
## - Opções de confirmar: remover e perder, ou enviar à central antes e remover
## - Suporte aos 4 tipos de armazenamento: bau, bau_grande, silo_granel, bau_estoque
## - Baú vazio remove diretamente sem confirmação

var MundoClass = load("res://cenas/mundo_demo.gd")


func _criar_mundo() -> Node:
	var cena = MundoClass.new()
	cena.modo = "teste"
	cena.semente = 1337
	cena.gerador = GeradorMundo.new(1337)
	Grade.gerador = cena.gerador
	cena.mapa = MapaOcupacao.new(cena.gerador)
	for x in range(0, 60):
		for y in range(0, 60):
			cena.mapa.limpar_obstaculo(Vector2i(x, y))
	cena.fabrica = Fabrica.new(cena.mapa)
	cena.construtor = Construtor.new(cena.mapa)
	cena.construtor.cobrar = false
	cena.inventario = {}
	cena.fabrica.estoque_nucleo = cena.inventario
	cena.fabrica.reconstruir()
	return cena


func _limpar_mundo(cena: Node) -> void:
	cena.free()


func test_enviar_tudo_para_central() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa
	var id = m.colocar("bau", Vector2i(10, 10), 0)
	f.reconstruir()
	verificar(f.baus.has(id), "baú registrado na fábrica")
	f.baus[id] = {"placa_ferro": 120, "engrenagem": 45, "circuito": 10}

	var estoque_antes_ferro = int(mundo.inventario.get("placa_ferro", 0))
	var estoque_antes_eng = int(mundo.inventario.get("engrenagem", 0))
	var estoque_antes_circ = int(mundo.inventario.get("circuito", 0))

	var transf = mundo.enviar_bau_para_central(id)
	igual(transf, 175, "transferiu 175 itens no total")
	igual(int(mundo.inventario.get("placa_ferro", 0)), estoque_antes_ferro + 120, "ferro na central")
	igual(int(mundo.inventario.get("engrenagem", 0)), estoque_antes_eng + 45, "engrenagens na central")
	igual(int(mundo.inventario.get("circuito", 0)), estoque_antes_circ + 10, "circuitos na central")
	verificar(f.baus[id].is_empty(), "baú esvaziado")
	_limpar_mundo(mundo)


func test_enviar_por_item_para_central() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa
	var id = m.colocar("bau", Vector2i(12, 10), 0)
	f.reconstruir()
	f.baus[id] = {"placa_ferro": 80, "engrenagem": 30}

	var estoque_antes_eng = int(mundo.inventario.get("engrenagem", 0))
	var transf = mundo.enviar_bau_para_central(id, "engrenagem")
	igual(transf, 30, "transferiu só as 30 engrenagens")
	igual(int(mundo.inventario.get("engrenagem", 0)), estoque_antes_eng + 30, "engrenagem somada ao núcleo")
	igual(int(f.baus[id].get("placa_ferro", 0)), 80, "placa de ferro permaneceu intacta no baú")
	verificar(not f.baus[id].has("engrenagem"), "engrenagem removida do baú")
	_limpar_mundo(mundo)


func test_remocao_pede_confirmacao_nos_quatro_tipos() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa

	var tipos := ["bau", "bau_grande", "silo_granel", "bau_estoque"]
	for i in tipos.size():
		var tipo = tipos[i]
		var pos = Vector2i(10 + i * 6, 10)
		var id = m.colocar(tipo, pos, 0)
		verificar(id >= 0, "colocou %s" % tipo)
		f.reconstruir()
		f.baus[id] = {"cobre": 50 + i * 10}

		verificar(mundo.eh_armazem_com_itens(id), "%s com itens é identificado como armazém com itens" % tipo)
		igual(mundo.total_itens_bau(id), 50 + i * 10, "contagem de itens correta no %s" % tipo)

		# Tentativa de remover sem forçar deve ser recusada e pedir confirmação
		var removido = mundo.remover_estrutura(id, false)
		verificar(not removido, "remoção direta recusada para %s com itens" % tipo)
		igual(mundo._confirmando_remocao_bau, id, "ativou estado de confirmação para %s" % tipo)
		verificar(m.estruturas.has(id), "%s ainda está no mapa" % tipo)

	_limpar_mundo(mundo)


func test_confirmar_remover_e_perder() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa
	var id = m.colocar("bau", Vector2i(20, 20), 0)
	f.reconstruir()
	f.baus[id] = {"ouro": 99}

	var estoque_antes = int(mundo.inventario.get("ouro", 0))
	mundo.pedir_confirmacao_remocao_bau(id)
	igual(mundo._confirmando_remocao_bau, id, "pediu confirmação")

	var ok = mundo.confirmar_remocao_bau(id, false)
	verificar(ok, "remoção confirmada")
	verificar(not m.estruturas.has(id), "baú removido do mapa")
	igual(int(mundo.inventario.get("ouro", 0)), estoque_antes, "itens foram perdidos (não foram para a central)")
	_limpar_mundo(mundo)


func test_confirmar_enviar_central_e_remover() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa
	var id = m.colocar("silo_granel", Vector2i(25, 20), 0)
	f.reconstruir()
	f.baus[id] = {"minerio_ferro": 500}

	var estoque_antes = int(mundo.inventario.get("minerio_ferro", 0))
	mundo.pedir_confirmacao_remocao_bau(id)

	var ok = mundo.confirmar_remocao_bau(id, true)
	verificar(ok, "remoção com envio à central confirmada")
	verificar(not m.estruturas.has(id), "silo removido do mapa")
	igual(int(mundo.inventario.get("minerio_ferro", 0)), estoque_antes + 500, "500 minérios salvos na central")
	_limpar_mundo(mundo)


func test_bau_vazio_remove_direto() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa
	var id = m.colocar("bau_grande", Vector2i(35, 20), 0)
	f.reconstruir()
	verificar(f.baus.has(id) and f.baus[id].is_empty(), "baú grande vazio")

	verificar(not mundo.eh_armazem_com_itens(id), "não é armazém com itens quando vazio")
	var ok = mundo.remover_estrutura(id, false)
	verificar(ok, "removeu direto sem pedir confirmação")
	verificar(not m.estruturas.has(id), "não está mais no mapa")
	igual(mundo._confirmando_remocao_bau, -1, "sem confirmação pendente")
	_limpar_mundo(mundo)


func test_inventario_botoes_central_e_clique() -> void:
	var mundo = _criar_mundo()
	var f = mundo.fabrica
	var m = mundo.mapa
	var id = m.colocar("bau", Vector2i(40, 20), 0)
	f.reconstruir()
	f.baus[id] = {"pedra": 40}

	var botoes := []
	var e = m.estruturas[id]
	mundo._inventario_bau(id, e, botoes)

	var tem_btn_tudo := false
	var btn_item: Dictionary = {}
	for b in botoes:
		if b.get("texto", "").contains("Enviar tudo para a central"):
			tem_btn_tudo = true
		if b.get("chave", "") == "pedra":
			btn_item = b

	verificar(tem_btn_tudo, "botão 'Enviar tudo para a central' presente no inventário")
	verificar(not btn_item.is_empty(), "item pedra listado na grade")
	verificar(not btn_item.get("sem_clique", true), "botão do item é clicável")
	verificar(btn_item.get("acao") is Callable, "botão do item tem Callable de ação")
	_limpar_mundo(mundo)
