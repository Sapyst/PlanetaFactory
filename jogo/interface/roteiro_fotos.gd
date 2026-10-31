class_name RoteiroFotos
extends Node
## Fase 5 do PLANO_INTEGRACAO: fotos de TODAS as peças do menu dentro do jogo (uma a uma, mesmo lugar, câmera e luz de
## dia, com as animações ligadas) + dados por modelo (triângulos, tamanho, textura) para o painel único.
##   xvfb-run godot --path jogo --resolution 960x720 --fixed-fps 30 -- modo demo roteiro fotos_finais [so <peça>]
## Medição de desempenho, numa fábrica grande:
##   xvfb-run godot --path jogo --resolution 1280x720 -- modo demo roteiro carga mostruario|patio
## Quem junta tudo: arte/estudos/painel_final.py.
## Interface e marcadores (`-- modo demo roteiro ui_pc`): arte/estudos/fotos/ui_pc/, folha montada à parte.

const ELEVACAO := 50.0                  ## graus acima do horizonte (a mesma em todas as fotos)
const ANGULO := 0.6
const ESPERA := 45                      ## quadros depois de posta (chão redesenhado, animação no meio)
const EXTRAS := ["nucleo", "ninho_aranha", "plataforma_agua", "ponte_agua", "plataforma_grade", "plataforma_rio", "poca_seiva", "nucleo_queda", "nucleo_queda_fim",
		"aranha_montada", "drone_reparo", "drone_defesa", "drone_logistico"]
const TRENS := ["locomotiva", "locomotiva_eletrica", "vagao_carga", "vagao_tanque"]

var rt: RoteiroTeste
var cena: Node
var con: Construtor
var saida := ""
var _o := Vector2i.ZERO
var _fixa := false
var _alvo := Vector3.ZERO
var _d := 20.0                          ## distância da câmera na foto


func _ready() -> void:
	cena = rt.cena
	process_priority = 1000                   # por último no quadro: a câmera da foto vale sobre qualquer outra
	cena.camera.set_process(false)
	cena.controle.process_mode = Node.PROCESS_MODE_DISABLED
	Sessao.config.fps = false
	cena.animar_tudo = true
	cena._efeitos.mostrar_icones = false
	con = cena.construtor
	var args := OS.get_cmdline_user_args()
	saida = ProjectSettings.globalize_path("res://").path_join("../arte/estudos/fotos/final")
	DirAccess.make_dir_recursive_absolute(saida)
	for i in 3:
		await get_tree().process_frame
	if rt.roteiro == "ui_pc":
		saida = ProjectSettings.globalize_path("res://").path_join("../arte/estudos/fotos/ui_pc")
		DirAccess.make_dir_recursive_absolute(saida)
		await _ui_pc()
		get_tree().quit()
		return
	_sem_hud()
	if rt.roteiro == "carga":
		await _carga(args[args.find("carga") + 1])
	else:
		await _fotos_finais(args)
	get_tree().quit()


func _process(_delta: float) -> void:
	if rt.roteiro in ["fotos_finais", "ui_pc"] and _fixa:
		_camera_fixa()


func _sem_hud() -> void:
	for n in cena.find_children("*", "CanvasLayer", true, false):
		n.visible = false
	for c in cena.get_children():
		if c is DesenhoPortas:                    # marcadores de porta solta: aqui as peças estão soltas de propósito
			c.process_mode = Node.PROCESS_MODE_DISABLED
			for f in c.get_children():
				if f is Node3D:
					f.visible = false
			if c is Node3D:
				c.visible = false


func _quadros(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _sem_perigo() -> void:
	cena.clima.forcar("limpo", true)
	var col: Colonia = cena.colonia
	for id in col.ninhos.keys():
		for ar in col.aranhas_do_ninho(id):
			col.aranhas.erase(ar)
		col.ninhos.erase(id)
		cena.sincronizar(con.destruir(id))
		var dc: DesenhoColonia = cena._desenho_colonia
		if dc._ninhos.has(id):
			dc._ninhos[id].queue_free()
			dc._ninhos.erase(id)


## Terreno plano e seco de w×h em volta de `perto`, longe de construção.
func _plano(perto: Vector2i, w: int, h: int) -> Vector2i:
	var g: GeradorMundo = cena.gerador
	for r in range(0, 400, 4):
		for dx in range(-r, r + 1, 4):
			for dy in range(-r, r + 1, 4):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var c := perto + Vector2i(dx, dy)
				var ok := true
				var n0 := g.nivel(c)
				for x in range(-w / 2, w / 2 + 1, 2):
					for y in range(-h / 2, h / 2 + 1, 2):
						var t := c + Vector2i(x, y)
						if g.nivel(t) != n0 or g.eh_agua(g.terreno(t)) or cena.mapa.tiles.has(t) or not g.distribuicao.jazida(t).is_empty():
							ok = false
							break
					if not ok:
						break
				if ok:
					return c
	return perto


func _limpar(c: Vector2i, w: int, h: int) -> void:
	var chunks := {}
	for x in range(-w / 2, w / 2 + 1):
		for y in range(-h / 2, h / 2 + 1):
			var t := c + Vector2i(x, y)
			cena.mapa.limpar_obstaculo(t)
			chunks[Grade.chunk_de(t)] = true
	for k in chunks:
		cena.descoberta.marcar_chunk(k)
		if cena.chunks.has(k):
			cena._redesenhar_chunk(k)


## Lugar válido para peça com regra de lugar (jazida, água, rio): o mais perto do pátio.
func _lugar_com_regra(nome: String) -> Vector2i:
	var m: MapaOcupacao = cena.mapa
	for r in range(0, 900, 2):
		for dx in range(-r, r + 1, 2):
			for dy in [-r, r] if absi(dx) != r else range(-r, r + 1, 2):
				var t: Vector2i = _o + Vector2i(dx, dy)
				if _tem_construcao_perto(t, 12):          # poste da base de demo ligaria um cabo na peça da foto (o traço preto)
					continue
				var mi := con.minimo_no_cursor(nome, t, 0)
				var mot := m.motivo_bloqueio(nome, mi, 0)
				if mot == "":
					return t
				if mot == "obstaculo":          # o obstáculo vem antes das outras regras: testa como se já estivesse limpo
					var novos: Array[Vector2i] = []
					for q in Grade.tiles_da_area(mi, Registro.area(nome), 0):
						if not m.limpos.has(q):
							m.limpos[q] = true
							novos.append(q)
					var ok := m.motivo_bloqueio(nome, mi, 0) == ""
					for q in novos:
						m.limpos.erase(q)
					if ok:
						return t
	return Vector2i(999999, 0)


func _tem_construcao_perto(t: Vector2i, r: int) -> bool:
	for id in cena.mapa.estruturas:
		var mi: Vector2i = cena.mapa.estruturas[id].minimo
		if absi(mi.x - t.x) <= r and absi(mi.y - t.y) <= r:
			return true
	return false


func _p(pl: Array[Dictionary]) -> String:
	var mot := ""
	for it in pl:
		if it.motivo != "":
			mot = it.motivo
	cena.sincronizar(con.executar(pl))
	return mot


## Põe a cena da peça em volta de o. Devolve {motivo, foco?: Rect2 em tiles, h: altura do enquadramento, itens}.
func _montar(nome: String, o: Vector2i) -> Dictionary:
	var sc := Construtor.separar_classe(nome)
	var base: String = sc[0]
	var suf := nome.substr(base.length()) if nome.begins_with(base) else ""
	var est := "esteira" + suf
	var leste := Construtor.rot_do_fluxo(1)
	var r := {"motivo": "", "h": 1.6, "itens": false}
	var v := func(x: int, y := 0) -> Vector2i: return o + Vector2i(x, y)
	match base:
		"esteira":
			r.motivo = _p(con.plano_linha(nome, v.call(-3, -1), v.call(2, 1), 0))
			r.foco = Rect2(Vector2(o) + Vector2(-3, -1), Vector2(6, 3))
			r.itens = true
		"cano":
			r.motivo = _p(con.plano_linha("cano", v.call(-2, -1), v.call(2, 1), 0))
			r.foco = Rect2(Vector2(o) + Vector2(-2, -1), Vector2(5, 3))
		"esteira_rampa", "rampa_desce":
			_p(con.plano_linha(est, v.call(-6), v.call(-4), 0))
			var q := v.call(-3) as Vector2i
			r.motivo = _p(con.plano_peca("esteira_rampa" + suf, q, leste))
			con.nivel = 1
			_p(con.plano_linha(est, v.call(-2), v.call(-1), 0))
			var m2 := _p(con.plano_peca("rampa_desce" + suf, o, leste))
			con.nivel = 0
			if m2 != "":
				r.motivo = m2
			_p(con.plano_linha(est, v.call(1), v.call(3), 0))
			var cx := -3 if base == "esteira_rampa" else 0
			r.foco = Rect2(Vector2(o) + Vector2(cx - 2, -1), Vector2(5, 3))
			r.itens = true
		"esteira_tunel_entrada", "esteira_tunel_saida":
			_p(con.plano_linha(est, v.call(-3), v.call(-1), 0))
			r.motivo = _p(con.plano_peca("esteira_tunel_entrada" + suf, o, leste))
			var m3 := _p(con.plano_peca("esteira_tunel_saida" + suf, v.call(3), leste))
			if m3 != "":
				r.motivo = m3
			_p(con.plano_linha(est, v.call(4), v.call(6), 0))
			var cy := 0 if base == "esteira_tunel_entrada" else 3
			r.foco = Rect2(Vector2(o) + Vector2(cy - 2, -1), Vector2(5, 3))
			r.itens = true
		"muro_centro", "muro_tijolo", "muro_liga", "muro_escudo":
			r.motivo = _p(con.plano_linha(nome, v.call(-2), v.call(2), 0))
		"trilho_reto", "trilho_energizado":
			for y in range(-3, 4):
				r.motivo = _p(con.plano_peca(nome, v.call(0, y), 0))
		"trilho_fim":
			for y in range(-3, 0):
				_p(con.plano_peca("trilho_reto", v.call(0, y), 0))
			r.motivo = _p(con.plano_peca(nome, o, 0))
		"trem", "trem_tanque", "trem_eletrico":
			var tr := "trilho_energizado" if base == "trem_eletrico" else "trilho_reto"
			for y in range(-16, 17):
				_p(con.plano_peca(tr, v.call(0, y), 0))
			await _quadros(2)
			r.motivo = _p(con.plano_peca(nome, o, 0))
			r.foco = Rect2(Vector2(o) + Vector2(-1, -6), Vector2(3, 13))
			r.h = 1.5
		_:
			r.motivo = _p(con.plano_peca(nome, o, 0))
	return r


func _terminar_montagem() -> void:
	for id in cena._nos:
		for c in cena._nos[id].get_children():
			if c is Montagem:
				c._t = c._fim


## Caixa do desenho de um nó (mundo).
func _caixa(n: Node3D) -> AABB:
	var cx := AABB()
	var vazia := true
	for g in n.find_children("*", "VisualInstance3D", true, false):
		var b: AABB = g.global_transform * (g as VisualInstance3D).get_aabb()
		cx = b if vazia else cx.merge(b)
		vazia = false
	return cx


func _enquadrar(cx: AABB) -> void:
	var cam: CameraJogo = cena.camera
	var r := cx.size.length() * 0.5
	var d := maxf(r / sin(deg_to_rad(CameraJogo.FOV) * 0.5) * 0.92, 1.3)
	_alvo = cx.get_center()
	cam.alvo = _alvo
	_fixa = true
	_d = d
	cam.distancia = maxf(d, 34.0)                 # o oval de visão e os chunks seguem um zoom normal; a foto chega perto
	cam.angulo = ANGULO
	_camera_fixa()


func _camera_fixa() -> void:
	var cam: CameraJogo = cena.camera
	var el := deg_to_rad(ELEVACAO)
	cam.position = _alvo + Vector3(sin(ANGULO) * cos(el), sin(el), cos(ANGULO) * cos(el)) * _d
	cam.look_at(_alvo)


func _foto(nome: String) -> String:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var caminho := saida.path_join(nome + ".jpg")
	img.save_jpg(caminho, 0.93)
	return caminho


func _fotos_finais(args: PackedStringArray) -> void:
	var dados := {"pecas": {}, "modelos": _dados_modelos(), "elevacao": ELEVACAO, "lotes": _dados_lotes()}
	var so := args[args.find("so") + 1] if args.has("so") else ""
	_o = _plano(Vector2i(-30, 0), 26, 26)
	_sem_perigo()
	_limpar(_o, 44, 44)
	var lista: Array = []
	var depois: Array = []
	for c in Registro.menu.categorias:
		for p in c.pecas:
			if p in Trem.COMPOSICOES:
				depois.append(p)
			else:
				lista.append(p)
	cena.camera.alvo = Grade.ponto_mundo(Vector2(_o))
	cena.camera.distancia = 20.0
	await _quadros(60)
	for nome in lista + depois:
		if so != "" and nome != so:
			continue
		await _foto_peca(nome, dados)
	for nome in EXTRAS:
		if so != "" and nome != so:
			continue
		await _foto_extra(nome, dados)
	var f := FileAccess.open(saida.path_join("dados.json" if so == "" else "dados_%s.json" % so), FileAccess.WRITE)
	f.store_string(JSON.stringify(dados, " "))
	f.close()


func _foto_peca(nome: String, dados: Dictionary) -> void:
	_sem_perigo()
	var o := _o
	var def: Dictionary = Registro.estruturas.get(nome, {})
	if not def.get("requer_jazida", []).is_empty() or def.get("perto_agua", false) or def.get("tomada_agua", false) or def.get("no_rio", false):
		o = _lugar_com_regra(nome)
		_limpar(o, 16, 16)
	elif nome in Trem.COMPOSICOES:
		o = _plano(_o + Vector2i(0, 40), 8, 38)
		_limpar(o, 16, 40)
	elif cena.mapa.motivo_bloqueio(nome, con.minimo_no_cursor(nome, o, 0), 0) not in ["", "estrutura desconhecida"]:
		var mot0: String = cena.mapa.motivo_bloqueio(nome, con.minimo_no_cursor(nome, o, 0), 0)
		print("FOTO %s: pátio recusou (%s)" % [nome, mot0])
	var antes: Dictionary = cena.mapa.estruturas.duplicate()
	var r: Dictionary = await _montar(nome, o)
	await _quadros(2)
	_terminar_montagem()
	await _quadros(3)
	var cx := AABB()
	var vazia := true
	var ids: Array = []
	for id in cena.mapa.estruturas:
		if antes.has(id):
			continue
		ids.append(id)
		if cena._nos.has(id):
			var b := _caixa(cena._nos[id])
			cx = b if vazia else cx.merge(b)
			vazia = false
	if r.has("foco"):
		var fo: Rect2 = r.foco
		var a := Grade.ponto_mundo(fo.position)
		var b2 := Grade.ponto_mundo(fo.end, r.h)
		cx = AABB(Vector3(minf(a.x, b2.x), minf(a.y, b2.y), minf(a.z, b2.z)), Vector3(absf(b2.x - a.x), absf(b2.y - a.y), absf(b2.z - a.z)))
	elif vazia:                                  # peça desenhada em lote: tile + altura baixa
		var a := Grade.ponto_mundo(Vector2(o) + Vector2(0.5, 0.5))
		cx = AABB(a + Vector3(-1.2, 0, -1.2), Vector3(2.4, 1.0, 2.4))
	_enquadrar(cx)
	if r.itens:
		await _quadros(8)
		rt._encher_esteiras()
	var k := Grade.chunk_de(o)
	for i in 240:
		if cena.chunks.has(k):
			break
		await get_tree().process_frame
	await _quadros(ESPERA)
	_camera_fixa()
	await _foto(nome)
	dados.pecas[nome] = {"motivo": r.motivo, "n": ids.size(), "tile": [o.x, o.y], "caixa": [cx.size.x, cx.size.y, cx.size.z]}
	print("FOTO %-34s %s peças=%d tile=%s caixa=%s centro=%s d=%.1f cam=%s" % [nome, ("RECUSADA:" + r.motivo) if r.motivo != "" else "ok", ids.size(), o, cx.size, cx.get_center(), _d, cena.camera.position])
	for id in ids:
		if cena.mapa.estruturas.has(id):
			cena.sincronizar(con.destruir(id))
	con._historico.clear()
	if nome in Trem.COMPOSICOES:
		cena.trens.clear()
		cena._remontar_trilhos()
	await _quadros(2)


## Plataformas e ponte de esteira em água de verdade: baús e uma esteira construídos sobre o rio.
func _foto_rio(dados: Dictionary) -> void:
	_sem_perigo()
	var g: GeradorMundo = cena.gerador
	var w := Vector2i(999999, 0)
	for r in range(6, 400, 2):
		for k in 96:
			var t := _o + Vector2i((Vector2.from_angle(k * TAU / 96.0) * r).round())
			var ok := true
			for i in 7:
				for j in 5:
					ok = ok and g.eh_agua(g.terreno(t + Vector2i(i, j))) and cena.mapa.motivo_bloqueio("bau", t + Vector2i(i, j), 0) == ""
			if ok:
				w = t
				break
		if w.x != 999999:
			break
	var antes: Dictionary = cena.mapa.estruturas.duplicate()
	var mot := ""
	for i in 4:
		for j in 3:
			var m1 := _p(con.plano_peca("bau", w + Vector2i(i, j + 1), 0))
			mot = m1 if m1 != "" else mot
	var m2 := _p(con.plano_linha("esteira", w + Vector2i(5, 0), w + Vector2i(5, 4), 0))
	mot = m2 if m2 != "" else mot
	await _quadros(2)
	_terminar_montagem()
	var a := Grade.ponto_mundo(Vector2(w) + Vector2(-0.5, -0.5))
	_enquadrar(AABB(a + Vector3(0, -1, -5), Vector3(7, 2, 5)))
	var k2 := Grade.chunk_de(w)
	for i in 240:
		if cena.chunks.has(k2):
			break
		await get_tree().process_frame
	await _quadros(ESPERA)
	_camera_fixa()
	await _foto("plataforma_rio")
	dados.pecas["plataforma_rio"] = {"motivo": mot, "n": 13, "tile": [w.x, w.y], "caixa": [7, 2, 5], "extra": true}
	print("FOTO %-34s extra motivo=%s tile=%s" % ["plataforma_rio", mot, w])
	for id in cena.mapa.estruturas.keys():
		if not antes.has(id):
			cena.sincronizar(con.destruir(id))
	con._historico.clear()
	await _quadros(2)


## Plataformas lado a lado + uma fileira de pontes, com a malha do lote: mostra a emenda (no chão, sem a descida de ERGUIDO).
func _grade_plataformas() -> Node3D:
	var g := Node3D.new()
	for x in 3:
		for z in 4:
			var mi := MeshInstance3D.new()
			mi.mesh = DesenhoChunk.malha("ponte_agua" if z == 3 else "plataforma_agua")
			mi.position = Vector3(4.0, 0, x) if z == 3 else Vector3(x, 0, z)
			g.add_child(mi)
	return g


func _foto_extra(nome: String, dados: Dictionary) -> void:
	_sem_perigo()
	var pos: Vector3 = Grade.ponto_mundo(Vector2(_o) + Vector2(0.5, 0.5))
	var n: Node3D
	if nome == "aranha_montada":              # a aranha de verdade (Aranha + MarchaAranha + IK), não a prévia
		n = Aranha.new()
		n.position = pos
	elif nome == "plataforma_grade":
		n = _grade_plataformas()
	elif nome == "plataforma_rio":
		await _foto_rio(dados)
		return
	elif nome == "poca_seiva":
		n = Node3D.new()                      # a jazida de verdade, no mapa (as poças são do chunk)
		pos = Grade.centro_mundo(_lugar_com_regra("bomba"), 0.0)
	else:
		n = load(Registro.modelos[nome.trim_suffix("_fim")].modelo).instantiate()
	var id_ninho := -1
	if nome == "ninho_aranha":                # registrado no mapa, como no jogo: é o que tira o capim da base
		id_ninho = cena.mapa.colocar("ninho_aranha", _o + Vector2i(-1, -1), 0)
		for k in cena.chunks:
			(cena.chunks[k] as DesenhoChunk).atualizar_fabrica()
	cena.add_child(n)
	if not nome in ["aranha_montada", "plataforma_grade", "poca_seiva"]:   # (a malha do lote já vem convertida)
		Materiais.converter(n)
	n.position = pos + (Vector3(0, 1.0, 0) if nome.begins_with("drone") else Vector3.ZERO)
	if nome.begins_with("nucleo_queda"):      # fechada, como desce; e aberta, no último quadro (a pose que vira o núcleo)
		for p in n.find_children("*", "AnimationPlayer", true, false):
			(p as AnimationPlayer).play("chegada")
			(p as AnimationPlayer).seek(9.99 if nome.ends_with("_fim") else Abertura.Q_FECHADA_S, true)
			(p as AnimationPlayer).pause()
	elif Registro.modelos.has(nome) and (Registro.modelos[nome].get("partes", []).size() > 1 or Registro.modelos[nome].get("anima", false)):
		var a := Animador.new()
		a.ativo = true
		a.modelo = nome
		n.add_child(a)
	await _quadros(2)
	var cx := AABB(pos - Vector3(1.6, 0, 1.6), Vector3(3.2, 0.2, 3.2)) if nome == "poca_seiva" else _caixa(n)
	_enquadrar(cx)
	await _quadros(ESPERA)
	_camera_fixa()
	await _foto(nome)
	dados.pecas[nome] = {"motivo": "", "n": 1, "tile": [_o.x, _o.y], "caixa": [cx.size.x, cx.size.y, cx.size.z], "extra": true}
	print("FOTO %-34s extra caixa=%s" % [nome, cx.size])
	n.queue_free()
	if id_ninho >= 0:
		cena.mapa.remover(id_ninho)
		for k in cena.chunks:
			(cena.chunks[k] as DesenhoChunk).atualizar_fabrica()
	await _quadros(2)


## Malha que o lote desenha de verdade (esteira, cano, trilho): tem de bater com o modelo em volta da origem.
func _dados_lotes() -> Dictionary:
	var out := {}
	for k in Registro.modelos:
		if DesenhoLotes.aceita(k):
			var b: AABB = DesenhoChunk.malha(k).get_aabb()
			out[k] = {"min": [b.position.x, b.position.y, b.position.z], "tam": [b.size.x, b.size.y, b.size.z]}
	return out


## Triângulos, tamanho e materiais de cada modelo de estrutura (do arquivo, antes de qualquer conversão).
func _dados_modelos() -> Dictionary:
	var out := {}
	var nomes: Array = EXTRAS + TRENS
	for k in Registro.estruturas:
		if Registro.modelos.has(k):
			nomes.append(k)
	var lum_cache := {}
	for nome in nomes:
		if out.has(nome) or not Registro.modelos.has(nome):
			continue
		var n: Node3D = load(Registro.modelos[nome].modelo).instantiate()
		add_child(n)
		var tris := 0
		var nos := 0
		var sup := 0
		var sem_tex: Array = []
		var escuros: Array = []
		var mats := {}
		var tris_escuros := 0
		for g in n.find_children("*", "MeshInstance3D", true, false):
			var mi := g as MeshInstance3D
			nos += 1
			var me := mi.mesh
			if me == null:
				continue
			for s in me.get_surface_count():
				sup += 1
				var ts := rt._tris_superficie(me, s)
				tris += ts
				var mt := mi.get_active_material(s)
				if mt == null:
					mt = me.surface_get_material(s)
				if not (mt is BaseMaterial3D):
					continue
				var bm := mt as BaseMaterial3D
				mats[bm.resource_name] = true
				var tex := bm.albedo_texture
				if tex == null:
					sem_tex.append(bm.resource_name)
				var lum := bm.albedo_color.get_luminance()
				if tex != null:
					if not lum_cache.has(tex):
						var im := tex.get_image()
						if im != null:
							if im.is_compressed():
								im.decompress()
							im.convert(Image.FORMAT_RGBA8)
							im.resize(8, 8, Image.INTERPOLATE_BILINEAR)
							var s2 := 0.0
							for yy in 8:
								for xx in 8:
									s2 += im.get_pixel(xx, yy).get_luminance()
							lum_cache[tex] = s2 / 64.0
						else:
							lum_cache[tex] = -1.0
					lum *= float(lum_cache[tex])
				if lum >= 0.0 and lum < 0.03:
					tris_escuros += ts
					escuros.append(bm.resource_name)
		var cx := _caixa(n)
		out[nome] = {"tris": tris, "nos": nos, "superficies": sup, "materiais": mats.size(),
				"min": [cx.position.x, cx.position.y, cx.position.z], "tam": [cx.size.x, cx.size.y, cx.size.z],
				"area": [Registro.area(nome).x, Registro.area(nome).y], "sem_textura": sem_tex, "escuros": escuros, "tris_escuros": tris_escuros}
		n.free()
	return out


## ---------------------------------------------------------------- desempenho
func _carga(tipo: String) -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	_sem_perigo()
	var cam: CameraJogo = cena.camera
	var centro := Vector3.ZERO
	var d_padrao := 44.0
	if tipo == "mostruario":
		rt._montar_mostruario()
		await _quadros(14)
		rt._encher_esteiras()
		centro = Grade.ponto_mundo(Vector2(-24, 0))
	else:
		var c := _plano(Vector2i(-60, 0), 60, 60)
		_limpar(c, 110, 110)
		await _montar_patio(c)
		centro = Grade.ponto_mundo(Vector2(c))
	_terminar_montagem()
	await _quadros(4)
	var total := 0
	var por := {}
	var cache := {}
	for id in cena.mapa.estruturas:
		var nome: String = cena.mapa.estruturas[id].nome
		if nome == "pilar":
			nome = "pilar_segmento"
		var mdl := Construtor.modelo_de(cena.mapa.estruturas[id]) if cena.mapa.estruturas[id].has("classe") else nome
		if not cache.has(mdl):
			cache[mdl] = _tris_modelo(mdl)
		total += int(cache[mdl])
		por[nome] = int(por.get(nome, 0)) + 1
	print("CARGA %s: %d estruturas, %d mil triângulos somando todas as estruturas, %d nós" % [tipo, cena.mapa.estruturas.size(), total / 1000, Performance.get_monitor(Performance.OBJECT_NODE_COUNT)])
	var ts0 := Time.get_ticks_usec()
	var dados: Dictionary = cena._dados_salvar()
	var ts1 := Time.get_ticks_usec()
	var copia := dados.duplicate(true)
	var ts2 := Time.get_ticks_usec()
	var txt := var_to_str(copia)
	print("SALVAR %s: montar %.1f ms + copiar %.1f ms no quadro; texto em outra thread %.1f ms, %d KB" % [tipo, (ts1 - ts0) / 1000.0, (ts2 - ts1) / 1000.0, (Time.get_ticks_usec() - ts2) / 1000.0, txt.length() / 1024])
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	for d in [d_padrao, 25.0, 90.0]:
		cam.alvo = centro
		cam.distancia = d
		cam.posicionar()
		_sem_perigo()
		await _quadros(90)
		var vp := get_viewport().get_viewport_rid()
		var tempos: PackedFloat32Array = []
		var gpu := 0.0
		var cpu := 0.0
		var prim := 0.0
		var draw := 0.0
		var objs := 0.0
		var t0 := Time.get_ticks_usec()
		for i in 240:
			await get_tree().process_frame
			var ag := Time.get_ticks_usec()
			tempos.append((ag - t0) / 1000.0)
			t0 = ag
			gpu += RenderingServer.viewport_get_measured_render_time_gpu(vp)
			cpu += RenderingServer.viewport_get_measured_render_time_cpu(vp)
			prim += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
			draw += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
			objs += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)
		var ord := tempos.duplicate()
		ord.sort()
		var media := 0.0
		for v in tempos:
			media += v
		media /= tempos.size()
		print("CARGA %s d=%.0f: %.0f fps · quadro média %.1f ms · p95 %.1f ms · pior %.1f ms · gpu %.2f ms · cpu render %.2f ms · %d mil tris desenhados · %d chamadas · %d objetos" % [tipo, d, 1000.0 / media, media, ord[int(ord.size() * 0.95)], ord[-1], gpu / 240.0, cpu / 240.0, int(prim / 240.0 / 1000.0), int(draw / 240.0), int(objs / 240.0)])
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_jpg(saida.path_join("carga_%s.jpg" % tipo), 0.9)
	rt._inventario()


func _tris_modelo(nome: String) -> int:
	if not Registro.modelos.has(nome):
		return 0
	var n: Node3D = load(Registro.modelos[nome].modelo).instantiate()
	var t := 0
	for g in n.find_children("*", "MeshInstance3D", true, false):
		t += rt._tris((g as MeshInstance3D).mesh)
	n.free()
	return t


## Pátio: 4 de cada peça que não tem regra de lugar, em grade; 30 linhas de esteira cheias passando no meio.
func _montar_patio(c: Vector2i) -> void:
	var x := -48
	var y := -48
	var alt := 0
	var n := 0
	for rep in 4:
		for cat in Registro.menu.categorias:
			for p in cat.pecas:
				var def: Dictionary = Registro.estruturas.get(p, {})
				if not def.has("grupo") and not Registro.modelos.has(p):
					continue
				if p.begins_with("esteira") or p.begins_with("rampa") or p.begins_with("trilho") or not def.get("requer_jazida", []).is_empty() or def.get("perto_agua", false) or def.get("tomada_agua", false) or def.get("no_rio", false):
					continue
				var a := Registro.area(p)
				if x + a.x > 48:
					x = -48
					y += alt + 1
					alt = 0
				if _p(con.plano_peca(p, c + Vector2i(x + a.x / 2, y + a.y / 2), 0)) == "":
					n += 1
				x += a.x + 1
				alt = maxi(alt, a.y)
	y += alt + 2
	var linhas := 0
	while y < 50 and linhas < 30:
		_p(con.plano_linha("esteira", c + Vector2i(-48, y), c + Vector2i(48, y), 0))
		y += 2
		linhas += 1
	print("PÁTIO %d máquinas, %d linhas de esteira, fundo em y=%d" % [n, linhas, y])
	await _quadros(14)
	rt._encher_esteiras()


# ------------------------------------------------------------------ interface PC, marcadores e fantasma
func _so_3d(sim: bool) -> void:
	cena.controle.barra.visible = not sim
	for n in cena.find_children("*", "VisaoRecursos", true, false):
		n.visible = false


func _olhar(c: Vector2, d: float) -> void:
	_fixa = true
	_alvo = Grade.ponto_mundo(c)
	_d = d
	cena.camera.alvo = _alvo
	cena.camera.distancia = d


func _ui_pc() -> void:
	Sessao.config.grama = true
	_sem_perigo()
	_o = _plano(Vector2i(-30, 0), 30, 30)
	_limpar(_o, 50, 50)
	await _quadros(30)
	var so_ui := OS.get_cmdline_user_args().has("so_ui")
	if not so_ui:
		await _ui_marcadores()
		await _ui_fantasma()
	if OS.get_cmdline_user_args().has("itens"):
		await _ui_itens()
		return
	await _ui_telas(str(get_viewport().get_window().size.y))
	print("FOTO ui_pc pronto ", saida)


## Estrutura pronta: portas soltas × atendidas, item e fluido.
func _ui_marcadores() -> void:
	var a := _o + Vector2i(-9, 0)
	_p(con.plano_peca("fornalha", a, 0))                        # solta: duas portas vermelhas
	var b := _o + Vector2i(-3, 0)
	_p(con.plano_peca("fornalha", b, 0))                        # uma atendida: a saída tem esteira
	var e: Dictionary = cena.mapa.estruturas[cena.mapa.tiles[b]]
	for s in Portas.estados(cena.mapa, e):
		if s.io == "SAI":
			_p(con.plano_linha("esteira", s.tile_fora, s.tile_fora + Vector2i(s.dir) * 2, 0))
	var r := _o + Vector2i(3, -1)
	_p(con.plano_peca("refinador", r, 0))                       # fluido + item
	_so_3d(true)
	_olhar(Vector2(_o) + Vector2(0.5, 1.0), 16.0)
	await _quadros(50)
	print("FOTO ", await _foto("marcadores"))
	_olhar(Vector2(a) + Vector2(1.0, 1.0), 6.5)
	await _quadros(20)
	print("FOTO ", await _foto("marcador_perto"))


## Fantasma: verde onde encaixa, vermelho onde falta; vermelho-escuro com o motivo onde não pode.
func _ui_fantasma() -> void:
	var f: Fantasma = cena.controle.fantasma
	var base := _o + Vector2i(-3, 8)
	var pl := con.plano_peca("fornalha", base, 0)
	var e0 := {"nome": "fornalha", "minimo": pl[0].minimo, "rot": pl[0].rot, "area": Registro.area("fornalha")}
	for s in Portas.estados(cena.mapa, e0):                     # uma esteira já no lugar da saída
		if s.io == "SAI":
			_p(con.plano_linha("esteira", s.tile_fora, s.tile_fora + Vector2i(s.dir) * 2, 0))
	f.mostrar(con.plano_peca("fornalha", base, 0))
	_olhar(Vector2(base) + Vector2(1.0, 1.0), 7.5)
	await _quadros(20)
	print("FOTO ", await _foto("fantasma_encaixe"))
	# ocupado: em cima de um baú
	var o2 := _o + Vector2i(6, 9)
	_p(con.plano_peca("bau", o2 + Vector2i(1, 1), 0))
	f.mostrar(con.plano_peca("fornalha", o2, 0))
	_olhar(Vector2(o2) + Vector2(1.0, 1.0), 7.5)
	await _quadros(20)
	print("FOTO ", await _foto("fantasma_ocupado"))
	# obstáculos de verdade: procura árvore e rocha perto
	for tipo in ["árvore", "rocha"]:
		var t := _achar_obstaculo(tipo)
		if t != Vector2i(999999, 0):
			f.mostrar(con.plano_peca("fornalha", t - Vector2i(1, 1), 0))
			_olhar(Vector2(t), 8.0)
			await _quadros(40)
			print("FOTO ", await _foto("fantasma_" + tipo.replace("á", "a")))
	var at := _achar_agua()
	if at != Vector2i(999999, 0):
		f.mostrar(con.plano_peca("fornalha", at, 0))
		_olhar(Vector2(at), 8.0)
		await _quadros(40)
		print("FOTO ", await _foto("fantasma_agua"))
	# sem material / sem pesquisa: mesma peça, regras ligadas
	var o3 := _o + Vector2i(-10, 9)
	var cob: bool = con.cobrar
	con.cobrar = true
	var inv: Dictionary = con.inventario
	con.inventario = {}
	f.mostrar(con.plano_peca("fornalha", o3, 0))
	_olhar(Vector2(o3) + Vector2(1.0, 1.0), 7.5)
	await _quadros(20)
	print("FOTO ", await _foto("fantasma_material"))
	con.inventario = inv
	con.cobrar = cob
	f.limpar()


## A interface em cada estado, com a fábrica de demonstração atrás.
func _ui_telas(sufixo: String) -> void:
	var barra: BarraConstrucao = cena.controle.barra
	var ctl: ControleConstrucao = cena.controle
	_so_3d(false)
	_olhar(Vector2(4, 6), 34.0)
	barra.estoque({"placa_ferro": 412, "placa_cobre": 96, "engrenagem": 38, "pedra": 1250, "minerio_ferro": 77, "carvao": 15})
	await _quadros(40)
	print("FOTO ", await _foto("hud_" + sufixo))
	barra._tocar_categoria(3)
	await _quadros(5)
	print("FOTO ", await _foto("pecas_" + sufixo))
	ctl.escolher("fornalha")
	barra.fechar_pecas()
	var perto := _plano(Vector2i(-6, 6), 6, 6)
	ctl._pendente = true
	ctl._tile_pend = perto
	ctl._cursor = perto
	ctl._cursor_valido = true
	await _quadros(5)
	ctl._chave_plano = ""
	ctl._atualizar()
	await _quadros(5)
	print("FOTO ", await _foto("construindo_" + sufixo))
	ctl.sair_do_modo()
	cena.abrir_pesquisa()
	await _quadros(8)
	print("FOTO ", await _foto("pesquisa_" + sufixo))
	cena._tela_pesquisa.fechar()
	await _ui_paineis(sufixo)
	cena.abrir_pausa()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	print("FOTO ", await _foto("pausa_" + sufixo))
	var mp: MenuPausa = cena.find_children("*", "MenuPausa", true, false)[0]
	mp._caixa.visible = false
	mp._config.visible = true
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	print("FOTO ", await _foto("config_" + sufixo))
	get_tree().paused = false


## Painel de estrutura construída e inventário, com a seleção à vista no mundo.
func _ui_paineis(sufixo: String) -> void:
	var c := Vector2i(int(cena.camera.alvo.x), int(-cena.camera.alvo.z))
	var o := _plano(c + Vector2i(-6, 3), 18, 12)
	_limpar(o, 22, 14)
	var mo := o + Vector2i(-4, 0)
	_p(con.plano_peca("montadora", mo, 0))
	var bau := o + Vector2i(4, 0)
	_p(con.plano_peca("bau", bau, 0))
	cena._fabrica_suja = true
	await _quadros(4)
	_olhar(Vector2(o) + Vector2(1, 1), 13.0)
	await _quadros(30)
	var id: int = cena.mapa.tiles[mo]
	cena.fabrica.escolher_receita(id, "engrenagem" if Registro.receitas.has("engrenagem") else Registro.receitas_da_maquina("montadora")[0])
	cena.fabrica.maquinas[id].tempo_total = 120.0
	cena.fabrica.maquinas[id].tempo_ativo = 96.0
	cena.selecionar(Vector2(mo) + Vector2(0.5, 0.5))
	await _quadros(6)
	print("FOTO ", await _foto("painel_maquina_" + sufixo))
	var ref: int = -1
	for mid in cena.fabrica.maquinas:
		if Registro.estruturas[cena.mapa.estruturas[mid].nome].get("maquina", "") == "refinador":
			ref = mid
	var bid: int = cena.mapa.tiles[bau]
	cena.fabrica.baus[bid].merge({"placa_ferro": 240, "engrenagem": 77, "pedra": 512, "carvao": 8, "circuito": 31, "tijolo": 120, "motor": 4, "minerio_ferro": 1200})
	cena.mapa.estruturas[bid]["aceita"] = ["placa_ferro", "engrenagem", "circuito"]
	cena.selecionar(Vector2(bau) + Vector2(0.5, 0.5))
	await _quadros(6)
	print("FOTO ", await _foto("painel_bau_" + sufixo))
	cena.mapa.estruturas[bid]["ordem"] = "qtd"
	cena._detalhe()
	await _quadros(4)
	print("FOTO ", await _foto("painel_bau_qtd_" + sufixo))
	cena.mapa.estruturas[id]["desligada"] = true
	cena._fabrica_suja = true
	await _quadros(4)
	cena.selecionar(Vector2(mo) + Vector2(0.5, 0.5))
	await _quadros(6)
	print("FOTO ", await _foto("painel_desligada_" + sufixo))
	if ref >= 0:
		_olhar(Vector2(cena.mapa.estruturas[ref].minimo) + Vector2(2, 2), 18.0)
		await _quadros(10)
		cena._sel = {"estrutura": ref}
		cena._detalhe()
		await _quadros(6)
		print("FOTO ", await _foto("painel_refinador_" + sufixo))
	# braço Radial: a origem à esquerda dele, painel com o modo; a garra vai até o lado (animar_tudo faz o ciclo)
	var tb := o + Vector2i(0, 5)
	_limpar(tb, 8, 8)
	_p(con.plano_peca("braco", tb, 0))
	var ibr: int = cena.mapa.tiles[tb]
	var eb: Dictionary = cena.mapa.estruturas[ibr]
	eb["modo_braco"] = "radial"
	var lados := Portas.origens_braco(eb)
	_p(con.plano_peca("bau", lados[1], 0))
	_p(con.plano_peca("bau", Portas.frente_braco(eb), 0))
	cena._fabrica_suja = true
	await _quadros(4)
	cena.fabrica.bracos[ibr].origem_i = 1
	_olhar(Vector2(tb) + Vector2(0.5, 0.5), 7.0)
	cena.selecionar(Vector2(tb) + Vector2(0.5, 0.5))
	var ani = cena._animador(ibr)
	for k in 240:
		await get_tree().process_frame
		if ani != null and ani.fase_braco < 0.08:
			break
	print("FOTO ", await _foto("braco_radial_" + sufixo), " giro ", ani.giro_origem if ani != null else "?")
	cena.selecionar(Vector2.INF)
	await _quadros(4)
	print("FOTO ", await _foto("selecao_fechada_" + sufixo))
	# faixa: lista fechada e aberta (ela desliza para o vão livre)
	var ctl: ControleConstrucao = cena.controle
	var barra: BarraConstrucao = ctl.barra
	_olhar(Vector2(4, 6), 34.0)
	ctl.escolher("braco")
	await _quadros(20)
	print("FOTO ", await _foto("faixa_fechada_" + sufixo))
	barra._tocar_categoria(1)
	await _quadros(4)
	print("FOTO ", await _foto("faixa_no_meio_" + sufixo))
	await _quadros(30)
	print("FOTO ", await _foto("faixa_aberta_" + sufixo))
	var abertos: Array[Rect2] = []
	for pn in [barra._canto, barra._recursos, barra._painel_pecas, barra._abas.get_parent(), barra._ferr.get_parent()]:
		if pn.is_visible_in_tree():
			abertos.append(pn.get_global_rect())
	var cobre := false
	for r in abertos:
		cobre = cobre or barra._faixa.get_global_rect().intersects(r)
	print("FAIXA retangulo ", barra._faixa.get_global_rect(), " cobre painel: ", cobre)
	ctl.sair_do_modo()
	barra.fechar_pecas()


## Esteira de amostra: todo item, parado, de perto e de longe. Câmera fixa, sem interface.
func _ui_itens() -> void:
	_so_3d(true)
	var lista: Array = Registro.itens.keys()
	var o := _plano(Vector2i(40, 0), maxi(lista.size() * 2, 30), 14)
	_limpar(o, lista.size() * 2 + 24, 14)
	var ini := o + Vector2i(-lista.size() / 2, 0)
	_p(con.plano_linha("esteira", ini, ini + Vector2i(lista.size() + 1, 0), Construtor.rot_do_fluxo(1)))
	cena._fabrica_suja = true
	await _quadros(4)
	var f: Fabrica = cena.fabrica
	var est: EsteiraCaminho = null
	for c2 in f.caminhos:
		if (c2.tiles as Array).has(ini):
			est = c2.esteira
	var ids: Array = []
	if est != null:
		for it in lista:
			if Registro.modelos.has(Registro.itens[it].get("modelo_de", it)):
				ids.append(it)
		est.itens.clear()
		est.espacos.clear()
		var folga := est.comprimento - ids.size() * 1.0
		for i in ids.size():
			est.itens.append(ids[i])
			est.espacos.append(maxf(folga * 0.5, 0.0) + 0.25 if i == 0 else 1.0)
		est.velocidade = 0.0
	print("FOTO itens na esteira: ", ids)
	f.set("ativo", false)
	var meio := Vector2(ini) + Vector2(float(ids.size()) * 0.5, 0.5)
	var n := 0
	for pars in [[meio, 26.0, "itens_longe"], [Vector2(ini) + Vector2(5, 0.5), 7.0, "itens_a"], [Vector2(ini) + Vector2(13, 0.5), 7.0, "itens_b"], [Vector2(ini) + Vector2(21, 0.5), 7.0, "itens_c"], [Vector2(ini) + Vector2(29, 0.5), 7.0, "itens_d"]]:
		_olhar(pars[0], pars[1])
		await _quadros(25)
		print("FOTO ", await _foto(pars[2]))
		n += 1
	# de perto, a engrenagem
	var i_e := ids.find("engrenagem")
	if i_e >= 0:
		var ponto := Vector2(ini) + Vector2(est.comprimento - 0.5 - (maxf(est.comprimento - ids.size(), 0.0) * 0.5 + 0.25 + float(i_e)), 0.5)
		for pars in [[1.6, "engrenagem_perto"], [4.0, "engrenagem_media"], [12.0, "engrenagem_longe"], [24.0, "engrenagem_mais_longe"]]:
			_olhar(ponto, pars[0])
			await _quadros(15)
			print("FOTO ", await _foto(pars[1]))
		# a mesma distância de jogo, com o 3D em 100% e em 50% (como no menu Resolução), andando 1/4 de pixel por foto
		for res in [1.0, 0.5]:
			Sessao.config.resolucao = res
			Sessao.aplicar()
			await _quadros(5)
			for k in 3:
				_olhar(ponto + Vector2(k * 0.012, -k * 0.009), 22.0)
				await _quadros(4)
				print("FOTO ", await _foto("engrenagem_res%d_%d" % [roundi(res * 100), k]))
		Sessao.config.resolucao = 1.0
		Sessao.aplicar()
	print("FOTO ui_pc pronto ", saida)


func _achar_obstaculo(tipo: String) -> Vector2i:
	var g: GeradorMundo = cena.gerador
	for r in range(10, 300, 3):
		for dx in range(-r, r + 1, 3):
			for dy in [-r, r]:
				var t: Vector2i = _o + Vector2i(dx, dy)
				var ob := g.distribuicao.obstaculo(t)
				if not ob.is_empty() and Bloqueios.nome_obstaculo(String(ob.nome)) == tipo and not cena.mapa.limpos.has(t) and not cena.mapa.tiles.has(t) and not _tem_construcao_perto(t, 14):
					return t
	return Vector2i(999999, 0)


func _achar_agua() -> Vector2i:
	var g: GeradorMundo = cena.gerador
	for r in range(10, 600, 4):
		for dx in range(-r, r + 1, 4):
			for dy in [-r, r]:
				var t: Vector2i = _o + Vector2i(dx, dy)
				if cena.mapa.motivo_bloqueio("fornalha", t, 0) == "agua":
					return t
	return Vector2i(999999, 0)
