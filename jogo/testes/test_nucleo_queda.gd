extends Caso
## Chegada do núcleo (fase 2.6; estudo_nucleo_queda.py via arte/estudos/conv_nucleo.py): a cápsula de reentrada da
## abertura do jogo novo, com a animação "chegada" do estudo (10 s; impacto no quadro 60; no fim, a pose do laço do
## núcleo do jogo). A descida em si é da abertura (cenas/abertura.gd), por isso a cápsula fica na origem do modelo.


func test_modelo_da_chegada() -> void:
	var md: Dictionary = Registro.modelos.get("nucleo_queda", {})
	verificar(not md.is_empty(), "modelo da chegada sincronizado")
	if md.is_empty():
		return
	igual(md.get("estudo", ""), "estudo_nucleo_queda.py", "convertido do estudo da queda")
	igual(md.get("tipo", ""), "deco", "não é peça de construir (só a abertura usa)")
	igual(Registro.area("nucleo_queda"), Registro.area("nucleo"), "mesma área do núcleo")
	verificar(md.get("anima", false), "tem peças móveis")
	verificar(not Registro.estruturas.has("nucleo_queda"), "não entra nas regras de estrutura")
	var cena: Node3D = (load(md.modelo) as PackedScene).instantiate()
	var ap: AnimationPlayer = null
	for p in cena.find_children("*", "AnimationPlayer", true, false):
		if (p as AnimationPlayer).has_animation("chegada"):
			ap = p
	verificar(ap != null, "animação chegada")
	if ap != null:
		perto(ap.get_animation("chegada").length, 10.0, 0.1, "10 s (240 quadros a 24 qps)")
		verificar(not ap.has_animation("trabalho"), "não é laço de máquina")
	verificar(float(md.dims[2]) < 4.0, "cápsula parada na origem (sem a trajetória de 38 m): altura %.2f" % md.dims[2])
	cena.free()


func test_abertura_usa_a_capsula() -> void:
	var ab := Abertura.new()
	var q := ab._instancia_queda()
	verificar(not q.is_empty(), "a abertura acha a cápsula")
	if not q.is_empty():
		verificar(q[1] is AnimationPlayer, "com o tocador da animação")
		(q[0] as Node).free()
	verificar(Abertura.T_FIM > Abertura.T_CHAO + 7.5, "a abertura dura até a cápsula virar núcleo (impacto + 7,5 s)")
	perto(Abertura.Q_IMPACTO_S, 59.0 / 24.0, 1e-6, "impacto no quadro 60 do estudo")
	ab.free()
