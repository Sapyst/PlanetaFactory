class_name ChunkDados
extends RefCounted
## Resultado da geração de um chunk (32×32 tiles). Índice local k = j * 32 + i.

var coord := Vector2i.ZERO
var terreno := PackedByteArray()     ## GeradorMundo.Terreno por tile
var bioma := PackedByteArray()       ## índice em GeradorMundo.nomes_biomas()
var jazidas: Dictionary = {}         ## Vector2i tile → {tipo, quantidade}
var obstaculos: Dictionary = {}      ## Vector2i âncora (canto sudoeste) → {nome, ancora, area, rot}
var decos: Array[Dictionary] = []    ## {nome, pos: Vector2 (grade), rot}


func indice(tile: Vector2i) -> int:
	var l := Grade.local_de(tile)
	return l.y * Grade.TAM_CHUNK + l.x
