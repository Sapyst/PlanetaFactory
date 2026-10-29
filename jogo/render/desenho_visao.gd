class_name DesenhoVisao
extends Node
## Mantém o oval de visão (Visao) e a névoa: a cada quadro passa o oval aos shaders; 4×/s marca o que foi descoberto,
## refaz a textura do descoberto (só quando muda ou a câmera sai da área dela) e esconde os objetos dos chunks que
## estão fora do oval (árvores, pedras, enfeites — o chão fica, escurecido pelo shader). A grama de cada quadrante
## é religada logo depois do oval, quando ele anda meio metro ou muda de tamanho.

const LADO_CEL := 128                  ## textura: 128×128 células de 2×2 tiles = 256×256 tiles em volta da câmera
const MARGEM_OBJ := 1.25               ## chunk com objetos até este tanto além do oval (em raios): sem pipoco na borda

var camera: CameraJogo
var descoberta: Descoberta
var chunks: Dictionary                 ## o dicionário de chunks do mundo
var _tex: ImageTexture
var _origem := Vector2i(1 << 30, 0)   ## célula do canto da textura
var _versao := -1
var _t := 0.0
var _grama_em := Vector4.INF            ## (centro, rx, rz) da última religada da grama
var _sem_grama := false


func _process(delta: float) -> void:
	if camera == null:
		return
	Visao.atualizar(camera, camera.distancia, camera.inclinacao(), camera.alvo)
	RenderingServer.global_shader_parameter_set("visao_oval", Vector4(Visao.centro.x, Visao.centro.y, Visao.eixo.x, Visao.eixo.y))
	RenderingServer.global_shader_parameter_set("visao_raios", Vector2(Visao.rx, Visao.rz))
	# grama: some de longe (zoom acima de 80 m: vira ruído) e quando desligada nas configurações
	var sem := camera.distancia >= 80.0 or not bool(Sessao.config.get("grama", true))
	var g := Vector4(Visao.centro.x, Visao.centro.y, Visao.rx, Visao.rz)
	if sem != _sem_grama or Vector2(g.x, g.y).distance_to(Vector2(_grama_em.x, _grama_em.y)) > 0.5 or absf(g.z - _grama_em.z) > 0.02 * g.z or absf(g.w - _grama_em.w) > 0.02 * g.w:
		_grama_em = g
		_sem_grama = sem
		for k in chunks:
			(chunks[k] as DesenhoChunk).ajustar_grama(Visao.centro, sem)
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.25
	descoberta.marcar_oval()
	var c := Vector2i((Visao.centro / Descoberta.CEL).floor())
	var origem := c - Vector2i(LADO_CEL / 2, LADO_CEL / 2)
	origem = Vector2i(snappedi(origem.x, 8), snappedi(origem.y, 8))
	if descoberta.versao != _versao or origem != _origem:
		_versao = descoberta.versao
		_origem = origem
		var img := descoberta.imagem(origem, LADO_CEL)
		if _tex == null or _tex.get_width() != LADO_CEL:
			_tex = ImageTexture.create_from_image(img)
			RenderingServer.global_shader_parameter_set("visao_mapa", _tex)
		else:
			_tex.update(img)
		RenderingServer.global_shader_parameter_set("visao_mapa_origem", Vector3(origem.x * Descoberta.CEL, origem.y * Descoberta.CEL, LADO_CEL * Descoberta.CEL))
	for k in chunks:
		var r := Rect2(Vector2(k * Grade.TAM_CHUNK), Vector2(Grade.TAM_CHUNK, Grade.TAM_CHUNK))
		(chunks[k] as DesenhoChunk).mostrar_objetos(Visao.toca(r, MARGEM_OBJ))
