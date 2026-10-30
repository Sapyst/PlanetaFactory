class_name DesenhoTrens
extends Node3D
## Desenha os trens: um nó por carro (locomotiva/vagão), posto a cada quadro pela pose do Trem
## (centro entre os truques, frente = truque da frente). Os truques giram sozinhos para seguir a curva.
## Locomotiva da cauda vai virada (as duas olham para fora). Vagão com carga mostra a pilha.

var _carros: Dictionary = {}      ## id do trem → Array[Node3D]


func sincronizar(trens: Array[Trem]) -> void:
	var vivos := {}
	for t in trens:
		vivos[t.id] = true
		if not _carros.has(t.id) or _carros[t.id].size() != t.carros.size():
			_criar(t)
		var nos: Array = _carros[t.id]
		var poses := t.poses()
		for i in poses.size():
			var p: Dictionary = poses[i]
			var no: Node3D = nos[i]
			var dir := Vector3(p.dir.x, 0, -p.dir.y)
			var ang := atan2(-dir.x, -dir.z)
			# a locomotiva do fim olha para trás
			if p.nome == "locomotiva" and i == poses.size() - 1 and poses.size() > 1:
				ang += PI
			no.position = Grade.ponto_mundo(p.pos)
			no.rotation.y = ang
			_truques(no, p, ang)
			var pilha := no.get_node_or_null("pilha") as Node3D
			if pilha != null:
				pilha.visible = t.total_carga() > 0
	for id in _carros.keys():
		if not vivos.has(id):
			for n in _carros[id]:
				n.queue_free()
			_carros.erase(id)


func _criar(t: Trem) -> void:
	if _carros.has(t.id):
		for n in _carros[t.id]:
			n.queue_free()
	var nos: Array[Node3D] = []
	for nome in t.carros:
		var no: Node3D = (load(Registro.modelos[nome].modelo) as PackedScene).instantiate()
		add_child(no)
		Materiais.converter(no)
		# minério do próprio modelo (parte "<vagao>_pilha", dentro da gôndola): vira o nó "pilha" do carro
		var minerio := no.find_child("*_pilha", true, false) as Node3D
		if minerio != null:
			var tf := minerio.transform
			var p := minerio.get_parent() as Node3D
			while p != no:
				tf = p.transform * tf
				p = p.get_parent() as Node3D
			minerio.owner = null
			minerio.get_parent().remove_child(minerio)
			no.add_child(minerio)
			minerio.transform = tf
			minerio.name = "pilha"
		elif nome == "vagao_carga":
			var pilha: Node3D = (load(Registro.modelos["cristal_bruto"].modelo) as PackedScene).instantiate()
			pilha.name = "pilha"
			Materiais.converter(pilha)
			pilha.scale = Vector3(2.4, 1.6, 7.5)
			pilha.position.y = 0.80
			no.add_child(pilha)
		nos.append(no)
	_carros[t.id] = nos


## Cada truque aponta para a tangente da trilha no seu ponto (relativo ao corpo).
func _truques(no: Node3D, p: Dictionary, ang: float) -> void:
	for k in 2:
		var tr := no.find_child("*truque%d" % k, true, false) as Node3D
		if tr == null:
			continue
		var tq: Dictionary = p.truques[1 - k]          # truque0 fica atrás (−Y no modelo)
		var d := Vector3(tq.dir.x, 0, -tq.dir.y)
		var a := atan2(-d.x, -d.z)
		tr.rotation.y = wrapf(a - ang, -PI / 2.0, PI / 2.0)
