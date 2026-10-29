extends Caso
## Oval de visão (Visao) e mapa descoberto (Descoberta).


func _oval(c: Vector2, rx: float, rz: float) -> void:
	Visao.ativa = true
	Visao.centro = c
	Visao.eixo = Vector2.RIGHT
	Visao.rx = rx
	Visao.rz = rz


func _desligar() -> void:
	Visao.ativa = false


func test_oval() -> void:
	_oval(Vector2(10, 0), 40.0, 20.0)
	perto(Visao.e(Vector2(10, 0)), 0.0, 1e-6, "centro")
	perto(Visao.e(Vector2(50, 0)), 1.0, 1e-6, "borda no eixo maior")
	perto(Visao.e(Vector2(10, 20)), 1.0, 1e-6, "borda no eixo menor")
	verificar(Visao.dentro(Vector2(40, 10)), "dentro")
	verificar(not Visao.dentro(Vector2(10, 30)), "fora (o oval é deitado)")
	verificar(Visao.toca(Rect2(45, -5, 16, 16)), "retângulo que encosta na borda")
	verificar(not Visao.toca(Rect2(200, 200, 16, 16)), "retângulo longe")
	_desligar()
	verificar(Visao.dentro(Vector2(9999, 9999)), "desligada: tudo dentro (testes, ferramentas)")


func test_descoberta() -> void:
	var d := Descoberta.new()
	verificar(not d.descoberto(Vector2i(0, 0)), "começa tudo escuro")
	_oval(Vector2(0, 0), 20.0, 12.0)
	var n := d.marcar_oval()
	verificar(n > 100, "marcou o oval (%d células)" % n)
	verificar(d.descoberto(Vector2i(0, 0)) and d.descoberto(Vector2i(18, 0)) and d.descoberto(Vector2i(-5, -9)), "dentro descoberto")
	verificar(not d.descoberto(Vector2i(0, 16)) and not d.descoberto(Vector2i(30, 0)), "fora não")
	var v := d.versao
	igual(d.marcar_oval(), 0, "de novo no mesmo lugar: nada novo")
	igual(d.versao, v, "versão não muda")
	_oval(Vector2(60, 0), 20.0, 12.0)
	d.marcar_oval()
	verificar(d.descoberto(Vector2i(0, 0)) and d.descoberto(Vector2i(60, 0)), "o que foi visto fica descoberto")
	var img := d.imagem(Vector2i(-16, -16), 64)
	verificar(img.get_pixel(16, 16).r > 0.9, "textura: célula da origem clara")
	verificar(img.get_pixel(16, 40).r < 0.1, "textura: não visto escuro")
	var d2 := Descoberta.new()
	d2.restaurar(d.estado())
	verificar(d2.descoberto(Vector2i(60, 0)) and not d2.descoberto(Vector2i(0, 40)), "volta do save")
	_desligar()
