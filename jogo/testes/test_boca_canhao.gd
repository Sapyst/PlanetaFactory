extends Caso
## Tiro sai da ponta do cano (Animador.boca): rastro, traçado, som e projétil partem dela, girando com o canhão.
## Antes o rastro saía do centro da torre a 1,25 m (na artilharia, ~3 m abaixo da boca, onde fica a fumaça).


func _torre(nome: String) -> Array:
	var n: Node3D = (load(Registro.modelos[nome].modelo) as PackedScene).instantiate()
	var a := Animador.new()
	a.modelo = nome
	n.add_child(a)
	(Engine.get_main_loop() as SceneTree).root.add_child(n)
	if a._partes.is_empty():
		a._ready()                                  # fora do laço principal o _ready pode não ter rodado ainda
	return [n, a]


func test_boca_na_ponta_e_girando() -> void:
	for nome in ["artilharia", "torre_defesa", "torre_foguetes", "torre_metralhadora"]:
		var par := _torre(nome)
		var n: Node3D = par[0]
		var a: Animador = par[1]
		var giro := a._partes["giro"] as Node3D
		var b0 := Vector3.INF
		for k in 4:
			a._gira("giro", k * PI / 2.0)
			var b := a.boca()
			verificar(b != Vector3.INF, "%s: tem boca" % nome)
			if b == Vector3.INF:
				break
			var eixo := Animador._global(giro).origin            # fora do laço principal o global_transform não se atualiza
			var frente := -Animador._global(a._partes["canhao"] as Node3D).basis.z
			frente.y = 0.0
			var lado := Vector2(b.x - eixo.x, b.z - eixo.z)
			verificar(lado.dot(Vector2(frente.x, frente.z).normalized()) > 0.2, "%s: boca à frente do eixo, na direção do cano (giro %d)" % [nome, k])
			verificar(b.y > 0.7, "%s: boca acima do chão (%.2f m)" % [nome, b.y])
			if k == 0:
				b0 = b
			elif k == 2:
				verificar(b0.distance_to(b) > 0.3, "%s: meia volta leva a boca para o outro lado" % nome)
		if nome == "artilharia":
			verificar(a.boca().y > 3.0, "artilharia: a boca fica no alto do cano (%.2f m), não a 1,25 m" % a.boca().y)
		n.queue_free()
