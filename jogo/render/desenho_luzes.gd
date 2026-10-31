class_name DesenhoLuzes
extends Node3D
## Luz das estruturas e dos postes à noite. Só lê a simulação (dados em dados/luzes.json):
##  - fonte por estrutura: fogo âmbar que treme, cristal violeta que pulsa, choque em flash curto, lâmpada constante;
##    acende só com a máquina ativa (sem energia ou desligada, apaga);
##  - poste: na cor da rede (RedeEnergia.origem_de), força pela carga, só com energia passando por ele;
##  - luz de verdade (OmniLight3D sem sombra, conjunto reaproveitado) só nas fontes mais perto do ponto olhado, com troca
##    suave: o Mobile limita luzes por objeto. O resto vira brilho falso no chão, em lote (MultiMesh aditivo);
##  - labaredas (de dia também) e arcos dos estudos, que a conversão tirou dos modelos: leves, em lote, só no oval de visão.
## A hora e o tempo entram por `fator_escuro`: de dia nada disso ilumina.

const PERIODO := 0.25                 ## s entre reavaliar quem está aceso e refazer os lotes
const TROCA_S := 0.6                  ## s da troca suave entre luz de verdade e brilho falso
const TIPO_SHADER := {"fogo": 0, "cristal": 1, "choque": 2, "lampada": 3, "poste": 3}
const ALTURA_HALO := 0.09             ## m acima da base da peça

var mapa: MapaOcupacao
var fabrica: Fabrica
var clima: Clima
var farol: Farol                      ## os faróis têm luz própria: o conjunto daqui cede lugar a eles
var nos: Dictionary = {}              ## id → Node3D (o mundo passa o dele)
var arcos: ArcosEletricos
var animar_tudo := func() -> bool: return false
var forcar_tudo := false              ## medição (roteiro carga): tudo aceso, como pior caso; postes alternam a cor
var desligado := false                ## medição sem as luzes novas

var _fontes: Array[Dictionary] = []
var _versao := -1
var _espera := 0.0
var _t := 0.0
var _escuro := 0.0
var _rng := RandomNumberGenerator.new()
var _d: Dictionary
var _lim: Dictionary
var _luzes: Array[OmniLight3D] = []
var _slot_fonte: Array = []           ## slot → fonte (Dictionary) ou null
var _desejadas: Array = []            ## fontes que deviam ter luz de verdade agora
var _choques: Array = []              ## choques acesos e visíveis
var _halos: MultiMeshInstance3D
var _pontas: MultiMeshInstance3D
var _chamas: MultiMeshInstance3D
var _cor_tipo := {}
var _cor_base := Color.WHITE
var _cor_geradores := Color.WHITE


func _ready() -> void:
	_d = Registro.luzes
	_lim = _d.get("celular" if Sessao.eh_celular() else "pc", {})
	for k in _d.cores:
		var c: Array = _d.cores[k]
		_cor_tipo[k] = Color(c[0], c[1], c[2])
	_cor_base = _cor_tipo.base
	_cor_geradores = _cor_tipo.geradores
	for i in int(_lim.luzes):
		var l := OmniLight3D.new()
		l.shadow_enabled = false
		l.omni_attenuation = 1.3
		l.light_specular = 0.25
		l.visible = false
		add_child(l)
		_luzes.append(l)
		_slot_fonte.append(null)
	_halos = _criar_lote(int(_lim.halos), preload("res://render/shaders/luz_halo.gdshader"), 2.0, Vector3.ZERO, true)
	_pontas = _criar_lote(int(_lim.halos), preload("res://render/shaders/luz_halo.gdshader"), 1.0, Vector3.ZERO, false)
	(_pontas.material_override as ShaderMaterial).set_shader_parameter("de_pe", true)
	_chamas = _criar_lote(int(_lim.chamas), preload("res://render/shaders/chama_lote.gdshader"), 1.0, Vector3(0.0, 0.5, 0.0), false)
	(_chamas.material_override as ShaderMaterial).set_shader_parameter("ruido", load("res://assets/texturas/ruido_detalhe.png"))


## Lote aditivo: quad deitado (halo no chão) ou de pé (o shader vira para a câmera).
func _criar_lote(n: int, shader: Shader, lado: float, centro: Vector3, deitado: bool) -> MultiMeshInstance3D:
	var q := QuadMesh.new()
	q.size = Vector2(lado, lado)
	q.center_offset = centro
	if deitado:
		q.orientation = PlaneMesh.FACE_Y
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.use_custom_data = true
	mm.instance_count = n
	mm.visible_instance_count = 0
	mm.mesh = q
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	var m := ShaderMaterial.new()
	m.shader = shader
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.extra_cull_margin = 1.0e4
	add_child(mi)
	return mi


## 0 = dia claro, 1 = noite fechada; céu carregado escurece mais cedo. `luz_clima` = Clima.valores.luz.
static func fator_escuro(dia: float, luz_clima := 1.0) -> float:
	return 1.0 - smoothstep(0.05, 0.45, dia * lerpf(0.5, 1.0, clampf(luz_clima, 0.0, 1.0)))


## Fontes que ganham luz de verdade: as `n` mais perto de `centro`. Já acesas têm 25% de folga, para não trocar à toa
## quando a câmera anda devagar. `lista`: [{p (grade), w}, …].
static func escolher(lista: Array, centro: Vector2, n: int) -> Array:
	var ord := []
	for f in lista:
		var d: float = centro.distance_squared_to(f.p)
		ord.append([d * (0.56 if float(f.get("w", 0.0)) > 0.0 else 1.0), ord.size()])
	ord.sort()
	var saida := []
	for i in mini(n, ord.size()):
		saida.append(lista[ord[i][1]])
	return saida


## 0..1 por tipo no tempo `t`; o choque é fraco no resto do tempo (quem dá o flash é o arco).
static func pulso(tipo: String, t: float, fase: float) -> float:
	match tipo:
		"fogo": return 0.80 + 0.14 * sin(t * 11.0 + fase * 7.0) * sin(t * 6.7 + fase * 3.0) + 0.06 * sin(t * 23.0 + fase)
		"cristal": return 0.86 + 0.14 * sin(t * 1.5 + fase * 6.28)
		"choque": return 0.15
	return 1.0


func _process(delta: float) -> void:
	if mapa == null or fabrica == null or desligado:
		if desligado:
			_apagar_tudo()
		return
	_t += delta
	if _versao != mapa.versao:
		_versao = mapa.versao
		_refazer_fontes()
	_espera -= delta
	if _espera <= 0.0:
		_espera = PERIODO
		_avaliar()
	_atualizar_luzes(delta)
	_disparar_arcos(delta)


func _apagar_tudo() -> void:
	for l in _luzes:
		l.visible = false
	for mi in [_halos, _pontas, _chamas]:
		mi.multimesh.visible_instance_count = 0


func _refazer_fontes() -> void:
	var antes := {}
	for f in _fontes:
		antes[f.id] = f
	_fontes.clear()
	for id in mapa.estruturas:
		var e: Dictionary = mapa.estruturas[id]
		var def: Dictionary = _d.maquinas.get(e.nome, {})
		var eh_poste: bool = _d.postes.has(e.nome)
		if not eh_poste and def.is_empty():
			continue
		if not nos.has(id) or not is_instance_valid(nos[id]):
			continue
		var no: Node3D = nos[id]
		var d: Dictionary = _d.postes[e.nome] if eh_poste else def
		var ctr := Grade.centro_da_area(e.minimo, e.area, e.rot)
		var a := Array(d.pos)
		var f: Dictionary = antes.get(id, {})
		f.merge({"id": id, "no": no, "nome": e.nome, "tipo": "poste" if eh_poste else str(def.tipo), "raio": float(d.raio), "forca": float(d.forca),
				"p": ctr, "f": 0.0, "w": 0.0, "fase": fmod(float(id) * 0.618, 1.0), "flash": 0.0, "cor": Color.WHITE,
				"regra": Registro.estruturas.get(e.nome, {})}, false)
		f.pos = no.global_transform * Vector3(a[0], a[1], a[2])
		f.chao = no.global_position.y + ALTURA_HALO
		f.chamas = def.get("chamas", [])
		f.arcos = def.get("arcos", [])
		_fontes.append(f)
	for i in _slot_fonte.size():
		var s = _slot_fonte[i]
		if s != null:
			_slot_fonte[i] = null if not antes.has(s.id) or not mapa.estruturas.has(s.id) else s


## Força de 0 a 1 que a fonte quer agora.
func forca_alvo(f: Dictionary) -> float:
	if forcar_tudo:
		return 1.0
	var id: int = f.id
	if not fabrica.ligada(id):
		return 0.0
	var tudo: bool = animar_tudo.call()
	if f.tipo == "poste":
		if not fabrica.rede.fluxo_em(id) or fabrica.rede.origem_de(id) == "":
			return 0.0
		var est: Dictionary = fabrica.rede.estat_de(id)
		return clampf(0.3 + 0.7 * float(est.get("gera", 0.0)) / maxf(float(est.get("gera_max", 1.0)), 1.0), 0.0, 1.0)
	var r: Dictionary = f.regra
	if r.has("capta_raio"):                    # para-raios e captador: acordam em tempestade
		return 1.0 if tudo or (clima != null and float(clima.valores.get("chuva", 0.0)) > 0.4) else 0.0
	if r.has("acumula_mj"):
		var cap := float(r.acumula_mj)
		return 1.0 if tudo else clampf(float(fabrica.acumulado.get(id, 0.0)) / maxf(cap, 0.001), 0.0, 1.0)
	if float(r.get("energia_kw", 0.0)) < 0.0:    # gerador e núcleo: entregando para a rede
		if bool(r.get("inesgotavel", false)):
			return 1.0
		return 1.0 if tudo or (fabrica.transmitindo(id) and float(fabrica.combustivel.get(id, 0.0)) > 0.0 and fabrica.kw_de(id) < 0.0) else 0.0
	if r.has("escudo") or fabrica.carga_torre.has(id):
		return 1.0 if tudo else clampf(float(fabrica.carga_torre.get(id, 0.0)) / maxf(fabrica.carga_max(id), 0.001), 0.0, 1.0)
	if tudo or fabrica.trabalhando(id) or fabrica.lab_trabalhando(id):
		return 1.0
	# parada com energia: o cristal fica em espera, fraco; fogo e choque só trabalhando
	if f.tipo == "cristal" and fabrica.energia(id) > 0.0:
		return float(_d.ocioso_cristal)
	if fabrica.maquinas.has(id) or fabrica.laboratorios.has(id):
		return 0.0
	return 1.0 if fabrica.energia(id) > 0.0 else 0.0


func _cor_da(f: Dictionary) -> Color:
	if f.tipo != "poste":
		return _cor_tipo[f.tipo]
	if forcar_tudo:
		return _cor_base if int(f.id) % 2 == 0 else _cor_geradores
	match fabrica.rede.origem_de(f.id):
		RedeEnergia.BASE: return _cor_base
		RedeEnergia.GERADORES: return _cor_geradores
	return f.cor                                 # sem energia: apaga na cor que estava


func _avaliar() -> void:
	var v: Dictionary = clima.valores if clima != null else {}
	var dia := clima.luz_dia() if clima != null else 1.0
	_escuro = fator_escuro(dia, float(v.get("luz", 1.0)))
	Fumaca.noite(_escuro)
	var ativas := []
	_choques.clear()
	var buf_h := PackedFloat32Array()
	var buf_p := PackedFloat32Array()
	var buf_c := PackedFloat32Array()
	var n_h := 0
	var n_p := 0
	var n_c := 0
	var max_h := int(_lim.halos)
	var max_c := int(_lim.chamas)
	var fh: Dictionary = _d.forca_halo
	for f in _fontes:
		var alvo := forca_alvo(f)
		f.f = move_toward(f.f, alvo, PERIODO * 2.0)
		f.cor = (f.cor as Color).lerp(_cor_da(f), 0.35) if f.f > 0.0 else _cor_da(f)
		if f.f <= 0.01:
			continue
		var dentro := Visao.dentro(f.p, 1.05)
		if not dentro:
			continue
		if f.tipo == "choque" or not (f.arcos as Array).is_empty():
			_choques.append(f)
		if not (f.chamas as Array).is_empty() and n_c < max_c and f.tipo == "fogo":
			var t: Transform3D = (f.no as Node3D).global_transform
			for ch in f.chamas:
				if n_c >= max_c:
					break
				var pc: Vector3 = t * Vector3(ch[0], ch[1], ch[2])
				_escrever(buf_c, pc, float(ch[3]), Color(1, 1, 1, 1), f.fase + 0.37 * n_c, f.f, float(ch[4]))
				n_c += 1
		if _escuro <= 0.01:
			continue
		ativas.append(f)
		var a: float = float(fh[f.tipo]) * f.forca * f.f * _escuro
		if a > 0.004 and n_h < max_h and f.w < 0.99:
			var cor: Color = f.cor
			cor.a = a * (1.0 - f.w)
			_escrever(buf_h, Vector3(f.pos.x, f.chao, f.pos.z), f.raio, cor, f.fase, float(TIPO_SHADER[f.tipo]), 0.0)
			n_h += 1
		if f.tipo == "poste" and n_p < max_h:
			var cor: Color = f.cor
			cor.a = 0.5 * f.f * _escuro
			_escrever(buf_p, f.pos, 0.42 + f.raio * 0.05, cor, f.fase, 3.0, 0.0)
			n_p += 1
	_enviar(_halos, buf_h, n_h)
	_enviar(_pontas, buf_p, n_p)
	_enviar(_chamas, buf_c, n_c)
	var limite := int(_lim.luzes)
	if farol != null:
		limite = maxi(2, limite - farol.acesos().size())
	_desejadas = escolher(ativas, Visao.centro, limite)


## Uma instância no buffer do MultiMesh: 12 da base+origem, 4 da cor, 4 de dados.
func _escrever(buf: PackedFloat32Array, p: Vector3, escala: float, cor: Color, a: float, b: float, c: float) -> void:
	buf.append_array([escala, 0.0, 0.0, p.x, 0.0, escala, 0.0, p.y, 0.0, 0.0, escala, p.z, cor.r, cor.g, cor.b, cor.a, a, b, c, 0.0])


func _enviar(mi: MultiMeshInstance3D, buf: PackedFloat32Array, n: int) -> void:
	var mm := mi.multimesh
	if n > 0:
		buf.resize(mm.instance_count * 20)         # o buffer tem de ter o tamanho do lote inteiro
		mm.buffer = buf
	mm.visible_instance_count = n


## Luz de verdade: quem não está mais na lista apaga devagar e libera o lugar; a parte que falta sobra para o brilho falso.
func _atualizar_luzes(delta: float) -> void:
	var quer := {}
	for f in _desejadas:
		quer[f.id] = f
	var passo := delta / TROCA_S
	for i in _luzes.size():
		var s = _slot_fonte[i]
		if s == null:
			continue
		var mantem: bool = quer.has(s.id) and _escuro > 0.01
		s.w = move_toward(s.w, 1.0 if mantem else 0.0, passo)
		quer.erase(s.id)
		if s.w <= 0.0:
			_slot_fonte[i] = null
	for i in _luzes.size():
		if _slot_fonte[i] == null and not quer.is_empty():
			var id: int = quer.keys()[0]
			_slot_fonte[i] = quer[id]
			quer.erase(id)
		var s = _slot_fonte[i]
		var l := _luzes[i]
		if s == null:
			l.visible = false
			continue
		s.flash = maxf(0.0, s.flash - delta * 9.0)
		var e: float = float(_d.forca_real[s.tipo]) * s.forca * s.f * _escuro * s.w * pulso(s.tipo, _t, s.fase)
		e += float(s.flash) * float(_d.flash_choque) * s.forca * _escuro
		l.visible = e > 0.003
		l.position = s.pos
		l.omni_range = s.raio
		l.light_color = s.cor
		l.light_energy = e


## Arcos do choque: poucos por segundo no total, um por vez em máquina sorteada; é o que dá o flash.
func _disparar_arcos(delta: float) -> void:
	if arcos == null or _choques.is_empty():
		return
	if _rng.randf() > delta * minf(5.0, 0.7 * _choques.size()):
		return
	var f: Dictionary = _choques[_rng.randi() % _choques.size()]
	if not is_instance_valid(f.no):
		return
	f.flash = 1.0
	if not (f.arcos as Array).is_empty():
		var par: Array = f.arcos[_rng.randi() % f.arcos.size()]
		arcos.disparar(f.no, Vector3(par[0][0], par[0][1], par[0][2]), Vector3(par[1][0], par[1][1], par[1][2]))


## Quantas luzes de verdade estão acesas agora (testes e roteiro).
func luzes_acesas() -> int:
	return _luzes.filter(func(l: OmniLight3D): return l.visible).size()


func halos_visiveis() -> int:
	return _halos.multimesh.visible_instance_count


func chamas_visiveis() -> int:
	return _chamas.multimesh.visible_instance_count
