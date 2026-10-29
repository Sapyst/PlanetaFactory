class_name DesenhoPlataformas
extends Node3D
## Debaixo de cada tile de construção sobre a água (rio, lago ou buraco cheio): plataforma com 4 pilares; esteira
## e cano ganham ponte (vão estreito no sentido do fluxo, 2 pilares). Um MultiMesh por modelo; refeito quando o mapa
## ou a água mudam. O modelo vem erguido 1,9 m: desce isso para o topo do deque ficar no chão da peça.

const ERGUIDO := 1.9

var mapa: MapaOcupacao
var agua: AguaJogo
var _chave := ""
var _mm: Dictionary = {}          ## modelo → MultiMeshInstance3D


func _process(_d: float) -> void:
	var chave := "%d|%d" % [mapa.versao, agua.versao if agua != null else 0]
	if chave == _chave:
		return
	_chave = chave
	_refazer()


func _na_agua(t: Vector2i) -> bool:
	return mapa.gerador.eh_agua(mapa.gerador.terreno(t)) or mapa.gerador.superficie_em(t) != null


func _refazer() -> void:
	var lista := {"plataforma_agua": [], "ponte_agua": []}
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		if not e.get("sobre_agua", false) or e.get("nivel", 0) > 0:
			continue
		var nome: String = e.nome
		var ponte := nome.begins_with("esteira_") or nome.begins_with("cano_") or nome == "trilho_reto"
		for t in Grade.tiles_da_area(e.minimo, e.area, e.rot):
			if not _na_agua(t):
				continue
			var pos := Grade.centro_mundo(t, -ERGUIDO)
			var b := Basis(Vector3.UP, Grade.angulo(e.rot)) if ponte else Basis()
			(lista["ponte_agua" if ponte else "plataforma_agua"] as Array).append(Transform3D(b, pos))
	for modelo in lista:
		var xs: Array = lista[modelo]
		var mmi: MultiMeshInstance3D = _mm.get(modelo)
		if mmi == null:
			if xs.is_empty():
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = DesenhoChunk.malha(modelo)
			mmi = MultiMeshInstance3D.new()
			mmi.multimesh = mm
			add_child(mmi)
			_mm[modelo] = mmi
		mmi.multimesh.instance_count = xs.size()
		for i in xs.size():
			mmi.multimesh.set_instance_transform(i, xs[i])
