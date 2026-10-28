extends Caso
## A marcha da aranha: pés plantados não deslizam, trípodes alternam, IK sempre alcança.

const DT := 1.0 / 60.0


func _andar(m: MarchaAranha, segundos: float, alvo_fn: Callable) -> Dictionary:
	var desliz := 0.0
	var min_no_chao := 6
	var ik_falhas := 0
	var dois_no_ar := 0
	var ultimo_plantado: Array[Vector3] = []
	for i in 6: ultimo_plantado.append(m.pes[i])
	var t := 0.0
	while t < segundos:
		var antes: Array[bool] = m.plantado.duplicate()
		var a: Array = alvo_fn.call(t, m)
		m.tick(DT, a[0], a[1])
		t += DT
		for i in 6:
			if antes[i] and m.plantado[i]:
				desliz = maxf(desliz, m.pes[i].distance_to(ultimo_plantado[i]))
			if m.plantado[i]:
				ultimo_plantado[i] = m.pes[i]
			if not MarchaAranha.resolver_ik(m.quadril(i), m.pes[i]).alcancou:
				ik_falhas += 1
		min_no_chao = mini(min_no_chao, m.pes_no_chao())
		var no_ar := 0
		for tri in MarchaAranha.TRIPODES:
			var algum := false
			for i in tri:
				if not m.plantado[i]: algum = true
			if algum: no_ar += 1
		if no_ar > 1: dois_no_ar += 1
	return {"desliz": desliz, "min_no_chao": min_no_chao, "ik_falhas": ik_falhas, "dois_no_ar": dois_no_ar}


func test_reta_sem_deslizar() -> void:
	var m := MarchaAranha.new()
	var r := _andar(m, 10.0, func(t: float, _m) -> Array: return [Vector3(0, 0, -t * 2.0), 0.0])
	igual(r.desliz, 0.0, "pé plantado nunca se move")
	verificar(r.min_no_chao >= 3, "sempre 3+ pés no chão (veio %d)" % r.min_no_chao)
	igual(r.dois_no_ar, 0, "trípodes nunca no ar juntos")
	igual(r.ik_falhas, 0, "IK sempre alcança o pé")
	verificar(m.posicao.length() > 10.0, "andou (%.1f m)" % m.posicao.length())


func test_curva_sem_deslizar() -> void:
	var m := MarchaAranha.new()
	var r := _andar(m, 12.0, func(t: float, _m) -> Array:
		var a := t * 0.5
		return [Vector3(sin(a) * 4.0, 0, -cos(a) * 4.0 + 4.0), -a])
	igual(r.desliz, 0.0, "pé plantado nunca se move na curva")
	igual(r.dois_no_ar, 0)
	igual(r.ik_falhas, 0, "IK alcança também girando")


func test_parada_assenta_pes() -> void:
	var m := MarchaAranha.new()
	_andar(m, 2.0, func(t: float, _m) -> Array: return [Vector3(0, 0, -t * 2.0), 0.0])
	var parado := m.posicao
	_andar(m, 2.0, func(_t: float, _m) -> Array: return [parado, 0.0])
	igual(m.pes_no_chao(), 6, "parada: todos os pés no chão")
	for i in 6:
		var c := m.casa(i)
		verificar(Vector2(m.pes[i].x - c.x, m.pes[i].z - c.z).length() <= MarchaAranha.LIMIAR_PASSO + 0.01, "pé perto da casa ao parar")


func test_ik_geometria() -> void:
	var q := Vector3(0, 0.55, 0)
	var pe := Vector3(1.2, 0, 0.3)
	var r := MarchaAranha.resolver_ik(q, pe)
	perto(q.distance_to(r.joelho), MarchaAranha.FEMUR, 1e-4, "fêmur com o comprimento certo")
	perto((r.joelho as Vector3).distance_to(pe), MarchaAranha.TIBIA, 1e-4, "tíbia com o comprimento certo")
	verificar(r.joelho.y > q.y, "joelho para cima")
