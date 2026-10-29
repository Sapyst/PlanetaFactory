class_name DesenhoLotes
extends Node3D
## Peças miúdas e numerosas (esteira, cano, trilho) não viram um nó cada: vão para um MultiMesh por
## (chunk, modelo). Mil esteiras num chunk = uma chamada de desenho. Mudou algo → o lote daquele chunk é refeito
## uma vez no fim do quadro.

const PREFIXOS := ["esteira_", "cano_", "trilho_"]

var _por_id: Dictionary = {}     ## id → chave do lote
var _lotes: Dictionary = {}      ## chave → {ids: {id: Transform3D}, nome, mmi, sujo}


static func aceita(nome: String) -> bool:
	for p in PREFIXOS:
		if nome.begins_with(p):
			return true
	return false


func adicionar(id: int, nome: String, t: Transform3D) -> void:
	var k := Grade.chunk_de(Grade.tile_de_mundo(t.origin))
	var chave := "%d|%d|%s" % [k.x, k.y, nome]
	if not _lotes.has(chave):
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = MultiMesh.new()
		mmi.multimesh.transform_format = MultiMesh.TRANSFORM_3D
		mmi.multimesh.mesh = _malha(nome)
		add_child(mmi)
		_lotes[chave] = {"ids": {}, "mmi": mmi, "sujo": true}
	_lotes[chave].ids[id] = t
	_lotes[chave].sujo = true
	_por_id[id] = chave


## "nome#desce": a rampa usada de descida é o modelo girado 180° — a lona tem de andar ao contrário.
static var _invertidas := {}


static func _malha(nome: String) -> Mesh:
	if not nome.ends_with("#desce"):
		return DesenhoChunk.malha(nome)
	if not _invertidas.has(nome):
		var base: Mesh = DesenhoChunk.malha(nome.trim_suffix("#desce"))
		var m := base.duplicate() as ArrayMesh
		for s in m.get_surface_count():
			var mat := m.surface_get_material(s)
			if mat is ShaderMaterial and float((mat as ShaderMaterial).get_shader_parameter("rolagem")) != 0.0:
				var c := (mat as ShaderMaterial).duplicate() as ShaderMaterial
				c.set_shader_parameter("rolagem", -float(c.get_shader_parameter("rolagem")))
				m.surface_set_material(s, c)
		_invertidas[nome] = m
	return _invertidas[nome]


## false se o id não estava num lote (então é nó comum).
func remover(id: int) -> bool:
	if not _por_id.has(id):
		return false
	var chave: String = _por_id[id]
	_por_id.erase(id)
	_lotes[chave].ids.erase(id)
	_lotes[chave].sujo = true
	return true


func tem(id: int) -> bool:
	return _por_id.has(id)


func _process(_d: float) -> void:
	for chave in _lotes:
		var l: Dictionary = _lotes[chave]
		if not l.sujo:
			continue
		l.sujo = false
		var mm: MultiMesh = l.mmi.multimesh
		mm.instance_count = l.ids.size()
		var i := 0
		for id in l.ids:
			mm.set_instance_transform(i, l.ids[id])
			i += 1
