class_name PoolEfeitos
extends Node3D
## Gerenciador de conjunto reaproveitado de instâncias de efeitos (PoolEfeitos).
## Cumpre as regras do Pedido 4:
## 1) Nunca instancia cena por tiro (todas as instâncias são pré-alocadas no _ready).
## 2) Teto global de efeitos simultâneos para manter taxa de quadros estável.
## 3) Rajada degrada pulando efeito visual quando a cadência for muito alta ou o pool encher.
## 4) Cápsulas ejetadas já existentes continuam funcionando no jogo.

const MAX_RASTROS_ATIVOS := 24
const MAX_IMPACTOS_ATIVOS := 24
const MAX_EXPLOSOES_ATIVAS := 8
const MAX_PULSOS_ATIVOS := 4
const INTERVALO_MIN_RAJADA := 0.065   ## s: abaixo disso a rajada pula traçante para não sobrecarregar

const CENAS_RASTRO := {
	"metralhadora": preload("res://render/efeitos/rastro_metralhadora.tscn"),
	"torre_energia": preload("res://render/efeitos/rastro_torre_energia.tscn"),
	"lanca_foguetes": preload("res://render/efeitos/rastro_lanca_foguetes.tscn"),
	"foguete_enxame": preload("res://render/efeitos/rastro_foguete_enxame.tscn"),
	"artilharia": preload("res://render/efeitos/rastro_artilharia.tscn"),
	"municao_perfurante": preload("res://render/efeitos/rastro_municao_perfurante.tscn"),
	"municao_carregada": preload("res://render/efeitos/rastro_municao_carregada.tscn"),
	"drone_combate": preload("res://render/efeitos/rastro_drone_combate.tscn"),
}

const CENAS_IMPACTO := {
	"metralhadora": preload("res://render/efeitos/impacto_metralhadora.tscn"),
	"torre_energia": preload("res://render/efeitos/impacto_torre_energia.tscn"),
	"lanca_foguetes": preload("res://render/efeitos/impacto_lanca_foguetes.tscn"),
	"foguete_enxame": preload("res://render/efeitos/impacto_foguete_enxame.tscn"),
	"artilharia": preload("res://render/efeitos/impacto_artilharia.tscn"),
	"municao_perfurante": preload("res://render/efeitos/impacto_municao_perfurante.tscn"),
	"municao_carregada": preload("res://render/efeitos/impacto_municao_carregada.tscn"),
	"drone_combate": preload("res://render/efeitos/impacto_drone_combate.tscn"),
}

const CENA_EXPLOSAO_FOGUETE := preload("res://render/efeitos/explosao_foguete.tscn")
const CENA_EXPLOSAO_ARTILHARIA := preload("res://render/efeitos/explosao_artilharia.tscn")
const CENA_DISPARO_MINA_PULSO := preload("res://render/efeitos/disparo_mina_pulso.tscn")

const CENAS_AMBIENTE := {
	"brilho_jazida_cristal": preload("res://render/efeitos/amb_brilho_jazida_cristal.tscn"),
	"faisca_fungo_noite": preload("res://render/efeitos/amb_faisca_fungo_noite.tscn"),
	"esporos_cogumelo": preload("res://render/efeitos/amb_esporos_cogumelo.tscn"),
	"vagalumes_flor": preload("res://render/efeitos/amb_vagalumes_flor.tscn"),
	"reflexo_agua": preload("res://render/efeitos/amb_reflexo_agua.tscn"),
	"poeira_vento": preload("res://render/efeitos/amb_poeira_vento.tscn"),
	"vapor_seiva": preload("res://render/efeitos/amb_vapor_seiva.tscn"),
	"brasa_queimado": preload("res://render/efeitos/amb_brasa_queimado.tscn"),
	"geiser_termico": preload("res://render/efeitos/amb_geiser_termico.tscn"),
}

var _pool_rastros: Dictionary = {}      ## tipo_arma -> Array[EfeitoBase]
var _pool_impactos: Dictionary = {}     ## tipo_arma -> Array[EfeitoBase]
var _pool_explosoes_fog: Array[EfeitoBase] = []
var _pool_explosoes_art: Array[EfeitoBase] = []
var _pool_pulsos: Array[EfeitoBase] = []
var _pool_ambientes: Dictionary = {}    ## tipo_amb -> Array[EfeitoBase]

var _ultimo_tempo_tiro: Dictionary = {} ## tipo_arma -> float (s)
var _tempo_total: float = 0.0


func _ready() -> void:
	if _pool_rastros.is_empty():
		_criar_pools()


func _process(delta: float) -> void:
	_tempo_total += delta


func _garantir_pools() -> void:
	if _pool_rastros.is_empty():
		_criar_pools()


func _criar_pools() -> void:
	# 1. Rastros
	for tipo in CENAS_RASTRO:
		_pool_rastros[tipo] = []
		var qtd: int = 6 if tipo in ["metralhadora", "municao_perfurante", "drone_combate"] else 4
		for i in qtd:
			var inst: EfeitoBase = CENAS_RASTRO[tipo].instantiate() as EfeitoBase
			inst.dentro_do_jogo = true
			inst.repetir_em_loop = false
			inst.visible = false
			inst._ativo = false
			add_child(inst)
			inst.garantir_construido()
			inst._ao_terminar()
			_pool_rastros[tipo].append(inst)

	# 2. Impactos
	for tipo in CENAS_IMPACTO:
		_pool_impactos[tipo] = []
		var qtd: int = 5 if tipo in ["metralhadora", "drone_combate"] else 3
		for i in qtd:
			var inst: EfeitoBase = CENAS_IMPACTO[tipo].instantiate() as EfeitoBase
			inst.dentro_do_jogo = true
			inst.repetir_em_loop = false
			inst.visible = false
			inst._ativo = false
			add_child(inst)
			inst.garantir_construido()
			inst._ao_terminar()
			_pool_impactos[tipo].append(inst)

	# 3. Explosões
	for i in 6:
		var inst_f: EfeitoBase = CENA_EXPLOSAO_FOGUETE.instantiate() as EfeitoBase
		inst_f.dentro_do_jogo = true
		inst_f.repetir_em_loop = false
		inst_f.visible = false
		inst_f._ativo = false
		add_child(inst_f)
		inst_f.garantir_construido()
		inst_f._ao_terminar()
		_pool_explosoes_fog.append(inst_f)

	for i in 4:
		var inst_a: EfeitoBase = CENA_EXPLOSAO_ARTILHARIA.instantiate() as EfeitoBase
		inst_a.dentro_do_jogo = true
		inst_a.repetir_em_loop = false
		inst_a.visible = false
		inst_a._ativo = false
		add_child(inst_a)
		inst_a.garantir_construido()
		inst_a._ao_terminar()
		_pool_explosoes_art.append(inst_a)

	# 4. Pulsos
	for i in MAX_PULSOS_ATIVOS:
		var inst_p: EfeitoBase = CENA_DISPARO_MINA_PULSO.instantiate() as EfeitoBase
		inst_p.dentro_do_jogo = true
		inst_p.repetir_em_loop = false
		inst_p.visible = false
		inst_p._ativo = false
		add_child(inst_p)
		inst_p.garantir_construido()
		inst_p._ao_terminar()
		_pool_pulsos.append(inst_p)

	# 5. Ambientes
	for tipo in CENAS_AMBIENTE:
		_pool_ambientes[tipo] = []
		var qtd: int = 3 if tipo in ["brilho_jazida_cristal", "esporos_cogumelo", "faisca_fungo_noite", "vagalumes_flor"] else 2
		for i in qtd:
			var inst_amb: EfeitoBase = CENAS_AMBIENTE[tipo].instantiate() as EfeitoBase
			inst_amb.dentro_do_jogo = true
			inst_amb.repetir_em_loop = true
			inst_amb.visible = false
			inst_amb._ativo = false
			add_child(inst_amb)
			inst_amb.garantir_construido()
			inst_amb._ao_terminar()
			_pool_ambientes[tipo].append(inst_amb)


func _perto_da_visao(p: Vector3) -> bool:
	var p2 := Vector2(p.x, -p.z)
	if Visao.ativa:
		return Visao.dentro(p2, 1.25)
	var cam := get_viewport().get_camera_3d() as CameraJogo if get_viewport() != null else null
	if cam == null:
		return true
	return p2.distance_to(Vector2(cam.alvo.x, -cam.alvo.z)) < cam.distancia * 1.35 + 14.0


## Dispara rastro com reaproveitamento estrito de instância e degradação suave em rajada.
func disparar_rastro(tipo_arma: String, origem: Vector3, destino: Vector3, cor: Color = Color.WHITE) -> void:
	if not _perto_da_visao(origem) and not _perto_da_visao(destino):
		return
	_garantir_pools()
	if not _pool_rastros.has(tipo_arma):
		tipo_arma = "metralhadora"

	# Degradação em rajada: se a mesma arma atirou rápido demais, pula o efeito visual do traçante
	var ult: float = float(_ultimo_tempo_tiro.get(tipo_arma, -1.0))
	if ult >= 0.0 and (_tempo_total - ult) < INTERVALO_MIN_RAJADA:
		return
	_ultimo_tempo_tiro[tipo_arma] = _tempo_total

	var pool: Array = _pool_rastros[tipo_arma]
	var inst: EfeitoBase = null
	for item in pool:
		var ef := item as EfeitoBase
		if not ef.esta_ativo():
			inst = ef
			break

	if inst == null:
		# Se todas estiverem ocupadas, não aloca nova cena (teto global)
		return

	if inst.is_inside_tree():
		inst.global_position = Vector3.ZERO
	else:
		inst.position = Vector3.ZERO
	inst.tocar(origem, destino, cor)


## Dispara impacto com tipo de alvo: "aranha", "chao", "estrutura".
func disparar_impacto(tipo_arma: String, pos: Vector3, alvo: String = "aranha", cor: Color = Color.WHITE) -> void:
	if not _perto_da_visao(pos):
		return
	_garantir_pools()
	if not _pool_impactos.has(tipo_arma):
		tipo_arma = "metralhadora"

	var pool: Array = _pool_impactos[tipo_arma]
	var inst: EfeitoBase = null
	for item in pool:
		var ef := item as EfeitoBase
		if not ef.esta_ativo():
			inst = ef
			break

	if inst == null:
		return

	if inst.is_inside_tree():
		inst.global_position = pos
	else:
		inst.position = pos
	inst.tocar(pos, pos, cor, alvo)


## Dispara explosão (foguete ou artilharia) na posição.
func disparar_explosao(pos: Vector3, raio: float, eh_artilharia: bool = false) -> void:
	if not _perto_da_visao(pos):
		return
	_garantir_pools()
	var pool: Array = _pool_explosoes_art if (eh_artilharia or raio >= 3.0) else _pool_explosoes_fog
	var inst: EfeitoBase = null
	for item in pool:
		var ef := item as EfeitoBase
		if not ef.esta_ativo():
			inst = ef
			break

	if inst == null:
		return

	if inst.is_inside_tree():
		inst.global_position = pos
	else:
		inst.position = pos
	inst.tocar(pos, pos, Color.WHITE, raio)


## Dispara anel de pulso eletromagnético da mina.
func disparar_pulso_mina(pos: Vector3, raio: float) -> void:
	if not _perto_da_visao(pos):
		return
	_garantir_pools()
	var inst: EfeitoBase = null
	for item in _pool_pulsos:
		var ef := item as EfeitoBase
		if not ef.esta_ativo():
			inst = ef
			break

	if inst == null:
		return

	if inst.is_inside_tree():
		inst.global_position = pos
	else:
		inst.position = pos
	inst.tocar(pos, pos, Color.WHITE, raio)


## Pega uma instância de ambiente do pool para fixar em um local onde a coisa existe.
func alocar_ambiente(tipo: String) -> EfeitoBase:
	_garantir_pools()
	if not _pool_ambientes.has(tipo):
		return null
	for item in _pool_ambientes[tipo]:
		var ef := item as EfeitoBase
		if not ef.visible:
			return ef
	return null



## Libera todas as instâncias de ambiente para repor no próximo ciclo da câmera.
func desativar_ambientes() -> void:
	for tipo in _pool_ambientes:
		for item in _pool_ambientes[tipo]:
			var ef := item as EfeitoBase
			ef.visible = false
			ef._ativo = false
