class_name DesenhoPlantas
extends Node3D
## Mudas e árvores plantadas pelo viveiro (AmbienteVivo.plantas): um MultiMesh por modelo de vegetação, cada
## planta no tamanho do seu crescimento (muda pequena → árvore inteira), giro e deslocamento próprios por tile.
## Refeito só quando `versao_plantas` muda (nasce, cai ou cresce um degrau).

var ambiente: AmbienteVivo
var _versao := -1
var _mm: Dictionary = {}          ## modelo → MultiMeshInstance3D


func _process(_d: float) -> void:
	if ambiente == null or ambiente.versao_plantas == _versao:
		return
	_versao = ambiente.versao_plantas
	_refazer()


func _refazer() -> void:
	var modelos: Array = Registro.ambiente.get("plantas", {}).get("modelos", ["arvore_campina_a"])
	var lista := {}
	for m in modelos:
		lista[m] = []
	var g := ambiente.gerador
	for t: Vector2i in ambiente.plantas:
		var cresc: float = ambiente.plantas[t]
		var modelo: String = modelos[int(Distribuicao.h(t.x, t.y, 901) * modelos.size()) % modelos.size()]
		var off := Vector2(Distribuicao.h(t.x, t.y, 902) - 0.5, Distribuicao.h(t.x, t.y, 903) - 0.5) * 0.4
		var p := Vector2(t) + Vector2(0.5, 0.5) + off
		var esc := (0.15 + 0.85 * smoothstep(0.0, 1.0, cresc)) * (0.85 + 0.3 * Distribuicao.h(t.x, t.y, 904))
		var b := Basis(Vector3.UP, Distribuicao.h(t.x, t.y, 905) * TAU).scaled(Vector3(esc, esc, esc))
		(lista[modelo] as Array).append(Transform3D(b, Grade.ponto_mundo(p, g.micro_em(p - Vector2(0.5, 0.5)))))
	for modelo in lista:
		var xs: Array = lista[modelo]
		var mmi: MultiMeshInstance3D = _mm.get(modelo)
		if mmi == null:
			if xs.is_empty():
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = DesenhoChunk.malha(modelo, 1.0)
			mmi = MultiMeshInstance3D.new()
			mmi.multimesh = mm
			add_child(mmi)
			_mm[modelo] = mmi
		mmi.multimesh.instance_count = xs.size()
		for i in xs.size():
			mmi.multimesh.set_instance_transform(i, xs[i])
