class_name Descoberta
extends RefCounted
## Mapa descoberto: tudo o que já passou dentro do oval de visão (Visao). Células de 2×2 tiles, um byte por célula,
## guardadas por chunk (só os chunks já vistos existem). O que nunca foi visto fica quase preto; o que já foi visto e
## saiu da tela fica escurecido. Vai no save.

const CEL := 2
const POR_CHUNK := 16                  ## células por lado de um chunk (32 tiles)

var celulas: Dictionary = {}           ## chunk → PackedByteArray(16·16): 255 = descoberto
var versao := 0                        ## muda quando algo novo é descoberto (o desenho refaz a textura)


func descoberto(t: Vector2i) -> bool:
	var k := Grade.chunk_de(t)
	if not celulas.has(k):
		return false
	var l := t - k * Grade.TAM_CHUNK
	return (celulas[k] as PackedByteArray)[(l.y / CEL) * POR_CHUNK + l.x / CEL] > 0


## Marca as células dentro do oval atual (Visao). Devolve quantas eram novas.
func marcar_oval(margem := 1.0) -> int:
	if not Visao.ativa:
		return 0
	var r := maxf(Visao.rx, Visao.rz) * margem
	var c := Visao.centro
	var novas := 0
	for cy in range(floori((c.y - r) / CEL), ceili((c.y + r) / CEL) + 1):
		for cx in range(floori((c.x - r) / CEL), ceili((c.x + r) / CEL) + 1):
			var p := Vector2(cx * CEL + CEL * 0.5, cy * CEL + CEL * 0.5)
			if Visao.e(p) > margem:
				continue
			var t := Vector2i(cx * CEL, cy * CEL)
			var k := Grade.chunk_de(t)
			if not celulas.has(k):
				var nova := PackedByteArray()
				nova.resize(POR_CHUNK * POR_CHUNK)
				celulas[k] = nova
			var l := t - k * Grade.TAM_CHUNK
			var i := (l.y / CEL) * POR_CHUNK + l.x / CEL
			var arr: PackedByteArray = celulas[k]
			if arr[i] == 0:
				arr[i] = 255
				celulas[k] = arr
				novas += 1
	if novas > 0:
		versao += 1
	return novas


## Imagem L8 (1 pixel por célula) de `lado` células a partir da célula `origem` (grade de células).
func imagem(origem: Vector2i, lado: int) -> Image:
	var img := Image.create(lado, lado, false, Image.FORMAT_L8)
	var dados := PackedByteArray()
	dados.resize(lado * lado)
	for ck in celulas:
		var base: Vector2i = ck * POR_CHUNK - origem
		if base.x >= lado or base.y >= lado or base.x + POR_CHUNK <= 0 or base.y + POR_CHUNK <= 0:
			continue
		var arr: PackedByteArray = celulas[ck]
		for y in POR_CHUNK:
			var py := base.y + y
			if py < 0 or py >= lado:
				continue
			for x in POR_CHUNK:
				var px := base.x + x
				if px >= 0 and px < lado:
					dados[py * lado + px] = arr[y * POR_CHUNK + x]
	img.set_data(lado, lado, false, Image.FORMAT_L8, dados)
	return img


func estado() -> Dictionary:
	return celulas


func restaurar(d: Dictionary) -> void:
	celulas = d.duplicate()
	versao += 1
