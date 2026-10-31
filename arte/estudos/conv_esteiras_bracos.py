"""Entradas do para_jogo.py para as ESTEIRAS e os BRAÇOS.

Esteiras (desenhadas em lote: DesenhoLotes, MultiMesh com a 1ª malha do .glb → uma malha só, sem animação):
- Este arquivo também serve de script (rodado pelo conversor como __main__ com o nome da peça): roda o estudo aprovado
  (estudo_esteira.py), apaga a cena dele e monta a peça do jogo com as funções e os materiais do próprio estudo
  (esteira(): laterais em perfil U com faixa listrada, catracas, motor com corrente) no caminho do tile do jogo
  (fluxo entra pelo sul, +y). Leito mais baixo que o do estudo (topo das placas 0,156 m, o item do jogo anda a 0,16 m);
  cavaletes curtos com sapatas (os da rampa crescem com a altura, com travessa e mão-francesa).
- As placas do estudo andam por animação; no jogo a lona anda pelo shader: `antes_de_exportar` troca as placas por uma
  lona de material "P_Esteira" (cor lisa de placa de aço) com UV.v = fração do tile no sentido do fluxo (0 na entrada,
  1 na saída — casa com a vizinha e com o passo dos itens); as cabeceiras (início, fim, rampa de junção) ganham a volta
  da lona no tambor e o retorno por baixo. Tudo (assado + lona + luzes) vira uma malha só.
- Início: motor e tambor no sul (o motor do estudo, girado em volta do eixo da coroa para não ficar enterrado);
  fim: tambor e para-choque listrado no norte; rampa de junção: tambor e calha que passa por cima da vizinha.

Braços: ver a seção BRAÇOS no fim do arquivo."""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))
PI = math.pi

# ------------------------------------------------------------------ medidas da esteira no jogo
H = 0.15             # topo do leito (o estudo usa 0,20; aqui o topo das placas fica em H + 0,006)
TOPO = H + 0.006     # superfície da lona
W = 0.60             # largura das placas (igual ao estudo)
RHO = 0.066          # raio da volta das placas no tambor (igual ao estudo)
PASSO, M_MIN = 0.10, RHO + 0.006


def margem_tambor(L):
    """Mesma conta do estudo: onde fica o eixo do tambor (m a partir da ponta) para um laço de placas inteiras."""
    n = int((2.0 * (L - 2.0 * M_MIN) + 2.0 * PI * RHO) / PASSO)
    lr = (n * PASSO - 2.0 * PI * RHO) / 2.0
    return (L - lr) / 2.0


def caminho(peca):
    """(L, f(s) → (ponto, direção), curvatura) no tile do jogo (x leste, y norte; o item entra pelo sul)."""
    from mathutils import Vector
    if peca in ('esteira_curva_esq', 'esteira_curva_dir'):
        R = 0.5
        if peca == 'esteira_curva_esq':
            c = Vector((-0.5, -0.5, 0))
            f = lambda s: (c + Vector((R * math.cos(s / R), R * math.sin(s / R), H)),
                           Vector((-math.sin(s / R), math.cos(s / R), 0)))
            return R * PI / 2, f, 1 / R
        c = Vector((0.5, -0.5, 0))
        f = lambda s: (c + Vector((R * math.cos(PI - s / R), R * math.sin(PI - s / R), H)),
                       Vector((math.sin(PI - s / R), -math.cos(PI - s / R), 0)))
        return R * PI / 2, f, -1 / R
    if peca == 'esteira_rampa':
        L = math.hypot(1.0, 0.5)
        d = Vector((0, 1.0, 0.5)).normalized()
        return L, lambda s: (Vector((0, -0.5 + s / L, H + 0.5 * s / L)), d), 0.0
    if peca == 'esteira_inicio':                 # percorrida ao contrário: a cabeceira (motor) do estudo fica no sul
        return 1.0, lambda s: (Vector((0, 0.5 - s, H)), Vector((0, -1, 0))), 0.0
    if peca == 'esteira_juncao':                 # a esteira acaba antes da borda: a calha leva o item adiante
        return 0.92, lambda s: (Vector((0, -0.5 + s, H)), Vector((0, 1, 0))), 0.0
    return 1.0, lambda s: (Vector((0, -0.5 + s, H)), Vector((0, 1, 0))), 0.0


def tambor(peca):
    """Onde a lona dá a volta: (y do eixo, lado da volta −1 sul / +1 norte) ou None (peça do meio da linha)."""
    if peca == 'esteira_inicio':
        return -0.5 + margem_tambor(1.0), -1
    if peca == 'esteira_fim':
        return 0.5 - margem_tambor(1.0), 1
    if peca == 'esteira_juncao':
        return -0.5 + 0.92 - margem_tambor(0.92), 1
    return None


ESTEIRAS = ('esteira_reta', 'esteira_curva_esq', 'esteira_curva_dir', 'esteira_rampa', 'esteira_inicio',
            'esteira_fim', 'esteira_juncao')


# ------------------------------------------------------------------ como script: monta a peça com o estudo
def _cavaletes(g, f, ss, nome):
    """Cavaletes do estudo (perna, sapata aparafusada; travessa e mão-francesa quando a perna é alta)."""
    import bmesh
    from mathutils import Vector, Matrix
    caixa, cil, base = g['caixa'], g['cil'], g['base']
    bm = bmesh.new()
    for s_c in ss:
        p, d = f(s_c)
        m = base(d)
        mh = base(Vector((d.x, d.y, 0)).normalized())
        pes = []
        for lado_s in (-1, 1):
            topo = p + m @ Vector((0, lado_s * (W / 2 + 0.03), -0.112))
            pes.append(topo)
            caixa(bm, Vector((topo.x, topo.y, topo.z / 2)), (0.04, 0.04, topo.z), mh)
            caixa(bm, Vector((topo.x, topo.y, 0.008)), (0.1, 0.09, 0.016), mh)
            for dx in (-0.032, 0.032):
                cil(bm, Vector((topo.x, topo.y, 0.02)) + mh @ Vector((dx, 0, 0)), 0.008, 0.012, lados=6)
        a0, a1 = pes
        if min(a0.z, a1.z) > 0.15:
            zt = min(a0.z, a1.z) - 0.03
            caixa(bm, Vector(((a0.x + a1.x) / 2, (a0.y + a1.y) / 2, zt)), (0.035, (a1 - a0).length + 0.04, 0.03), mh)
            d0, d1 = Vector((a0.x, a0.y, 0.06)), Vector((a1.x, a1.y, zt - 0.02))
            e = d1 - d0
            q = e.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((d0 + d1) / 2) @ q @ Matrix.Diagonal((0.022, 0.022, e.length, 1)))
    return g['obj'](nome + '_cavaletes', bm, 'aco')


def _motor_de_pe(e, nome, f, L):
    """O motor do estudo pende 0,17 m abaixo da coroa (com o leito do jogo ficaria enterrado): gira o conjunto em
    volta do eixo da coroa até o motor deitar ao lado da esteira, para dentro do tile."""
    import bpy
    from mathutils import Vector, Matrix
    m = e['m']
    pe_, de_ = f(L - m)
    lado = Vector((0, 0, 1)).cross(de_).normalized()
    coroa = pe_ + Vector((0, 0, -RHO)) - lado * (W / 2 + 0.075)
    grupo = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name.split('.')[0] in
             (nome + '_motor', nome + '_pinhao', nome + '_coroa', nome + '_elo')]
    pinhao = bpy.data.objects[nome + '_pinhao'].matrix_world.translation.copy()
    melhor = None
    for ang in [math.radians(a) for a in range(-180, 181, 5)]:
        R = Matrix.Translation(coroa) @ Matrix.Rotation(ang, 4, lado) @ Matrix.Translation(-coroa)
        p = R @ pinhao
        dentro = (p - pe_).dot(de_) < -0.05            # para dentro do tile (atrás da cabeceira)
        if dentro and (melhor is None or abs(p.z - 0.075) < melhor[1]):   # deitado, rente ao chão
            melhor = (R, abs(p.z - 0.075))
    for o in grupo:
        o.matrix_world = melhor[0] @ o.matrix_world


def _parachoque(g, nome, y):
    import bmesh
    from mathutils import Vector
    caixa = g['caixa']
    bm, bl = bmesh.new(), bmesh.new()
    caixa(bm, Vector((0, y, TOPO + 0.045)), (W + 0.02, 0.025, 0.07))               # lâmina
    for sx in (-1, 1):                                                               # mãos presas na lateral
        caixa(bm, Vector((sx * (W / 2 + 0.03), y, TOPO + 0.03)), (0.03, 0.06, 0.06))
    caixa(bl, Vector((0, y - 0.0135, TOPO + 0.045)), (W - 0.02, 0.002, 0.05))     # face listrada para o item
    g['obj'](nome + '_parachoque', bm, 'grafite')
    g['obj'](nome + '_parachoque_listras', bl, 'listras')


CALHA = ((0.34, TOPO + 0.012), (0.57, 0.245), (0.75, 0.17))      # (y, topo) — o item sobe por Fabrica.altura_calha


def _calha(g, nome):
    """Calha da rampa de junção: chapa de aço por cima do tambor e do trilho da vizinha, guias laterais, mãos."""
    import bmesh
    from mathutils import Vector
    pts = []
    for (y0, z0), (y1, z1) in zip(CALHA, CALHA[1:]):
        for k in range(4):
            t = k / 4
            pts.append((y0 + (y1 - y0) * t, z0 + (z1 - z0) * t))
    pts.append(CALHA[-1])
    bm, bg = bmesh.new(), bmesh.new()

    def tira(alvo, x0, x1, dz0, dz1):
        an = [[alvo.verts.new(Vector((x, y, z + dz))) for x, dz in ((x0, dz0), (x1, dz0), (x1, dz1), (x0, dz1))]
              for y, z in pts]
        for a, b in zip(an, an[1:]):
            for j in range(4):
                alvo.faces.new((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]))
        alvo.faces.new(list(reversed(an[0])))
        alvo.faces.new(an[-1])
    tira(bm, -0.25, 0.25, -0.012, 0.0)                                             # chapa
    for x0, x1 in ((0.25, 0.27), (-0.27, -0.25)):
        tira(bg, x0, x1, -0.012, 0.07)                                             # guias
    for sx in (-1, 1):                                                              # mãos até a lateral
        g['caixa'](bg, Vector((sx * 0.30, 0.40, TOPO + 0.02)), (0.07, 0.03, 0.05))
    g['obj'](nome + '_calha', bm, 'aco')
    g['obj'](nome + '_calha_guias', bg, 'amarelo')


def _montar_esteira(peca):
    import bpy
    estudo = os.path.join(AQUI, 'estudo_esteira.py')
    sys.argv = [sys.argv[0], '--python', estudo, '--', 'nada']
    g = {'__name__': '__main__', '__file__': estudo}
    exec(compile(open(estudo, encoding='utf-8').read(), estudo, 'exec'), g)
    for o in list(bpy.data.objects):                   # só os materiais e as funções do estudo ficam
        bpy.data.objects.remove(o, do_unlink=True)
    nome = 'est'
    L, f, curv = caminho(peca)
    e = g['esteira'](nome, (L, f, curv), g['Vector']((0, 0, 0)), motor=(peca == 'esteira_inicio'))
    if peca == 'esteira_inicio':
        sc = bpy.context.scene
        for c in e['correntes']:
            g['animar_corrente'](c, g['GIRO'] * c['laco'][3])
        sc.frame_set(1)
        for o in [o for o in sc.objects if o.animation_data]:
            mw = o.matrix_world.copy()
            o.animation_data_clear()
            o.matrix_world = mw
        bpy.data.objects.remove(bpy.data.objects[nome + '_suporte'], do_unlink=True)
        _motor_de_pe(e, nome, f, L)
    for o in list(bpy.context.scene.objects):          # placas → lona do shader; tambores ficam dentro da volta da lona
        if o.type == 'MESH' and o.name.split('.')[0] in (nome + '_placa', nome + '_catraca', nome + '_eixo', nome + '_cavaletes'):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.context.scene.objects:
        if o.animation_data:
            o.animation_data_clear()
    if peca == 'esteira_rampa':
        ss = (0.12, L / 2, L - 0.12)
    elif peca == 'esteira_inicio':
        ss = (0.3, 0.72)
    elif peca == 'esteira_juncao':
        ss = (0.25, 0.65)
    else:
        ss = (L * 0.25, L * 0.75)
    _cavaletes(g, f, ss, nome)
    if peca == 'esteira_fim':
        _parachoque(g, nome, 0.40)
    if peca == 'esteira_juncao':
        _calha(g, nome)


# ------------------------------------------------------------------ lona (P_Esteira) e malha única
def _lona_bm(peca):
    """Superfície das placas (material P_Esteira) com UV.v = fração do tile no sentido do fluxo."""
    import bmesh
    from mathutils import Vector
    L, f, _ = caminho(peca)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')

    def tira(pontos):
        """pontos: [(centro, lado unitário, v)] → faixa de largura W."""
        an = [(bm.verts.new(c - l * W / 2), bm.verts.new(c + l * W / 2), v) for c, l, v in pontos]
        for (a0, a1, va), (b0, b1, vb) in zip(an, an[1:]):
            fc = bm.faces.new((a0, b0, b1, a1))
            for lp in fc.loops:
                lp[uv].uv = (0.0 if lp.vert in (a0, b0) else 1.0, va if lp.vert in (a0, a1) else vb)
    if peca.startswith('esteira_tunel'):              # rampa do pórtico: da borda até sumir no chão (o terreno do jogo)
        x = Vector((1, 0, 0))
        yz = lambda y: Vector((0, y, TOPO - 0.45 * (y + 0.5 if 'entrada' in peca else 0.5 - y) / 0.9))
        ys = (-0.5, -0.5 + 0.9 * TOPO / 0.45) if 'entrada' in peca else (0.5 - 0.9 * TOPO / 0.45, 0.5)
        tira([(yz(y), x, y + 0.5) for y in ys])
        return bm
    n = 12 if 'curva' in peca else 1
    tb = tambor(peca)
    pts = []
    for i in range(n + 1):
        s = L * i / n
        p, d = f(s)
        lado = Vector((0, 0, 1)).cross(d).normalized()
        cima = d.cross(lado).normalized()
        frac = (p.y + 0.5) if peca in ('esteira_inicio', 'esteira_fim', 'esteira_juncao') else s / L
        pts.append((p + cima * 0.006, -lado, frac))      # −lado: a 1ª borda (u=0) fica à esquerda… a ordem da face sobe
    if peca == 'esteira_inicio':
        pts.reverse()                                     # caminho do estudo vai de norte a sul
    if tb is None:
        tira(pts)
    else:
        y0, sentido = tb
        x = Vector((1, 0, 0))
        r = RHO + 0.006
        zc = H - RHO
        if sentido > 0:                                   # volta no norte: topo até o tambor, volta, retorno até o sul
            topo = [(Vector((0, y, TOPO)), x, y + 0.5) for y in (-0.5, y0)]
            v0 = y0 + 0.5
            volta = [(Vector((0, y0 + r * math.sin(a), zc + r * math.cos(a))), x, v0 + r * a) for a in
                     [PI * k / 8 for k in range(9)]]
            v1 = v0 + r * PI
            ret = [(Vector((0, y, zc - r)), x, v1 + (y0 - y)) for y in (y0, -0.5)]
            tira(topo)
            tira(volta)
            tira(ret)
        else:                                             # volta no sul (início)
            v0 = y0 + 0.5
            ret = [(Vector((0, y, zc - r)), x, v0 - r * PI - (y - y0)) for y in (0.5, y0)]
            volta = [(Vector((0, y0 - r * math.sin(a), zc - r * math.cos(a))), x, v0 - r * PI + r * a) for a in
                     [PI * k / 8 for k in range(9)]]
            topo = [(Vector((0, y, TOPO)), x, y + 0.5) for y in (y0, 0.5)]
            tira(ret)
            tira(volta)
            tira(topo)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for fc in bm.faces:                                    # lona de cima e volta: normal para fora (cima / fora do tambor)
        c = fc.calc_center_median()
        if tb is not None and abs(c.y - tb[0]) < RHO + 0.02 and abs(c.z - (H - RHO)) < RHO + 0.02:
            fora = (c - Vector((0, tb[0], H - RHO))).normalized()
            if fc.normal.dot(fora) < 0:
                fc.normal_flip()
        elif fc.normal.z < 0:
            fc.normal_flip()
    return bm


def _material_lona():
    import bpy
    m = bpy.data.materials.get('P_Esteira') or bpy.data.materials.new('P_Esteira')
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (0.16, 0.165, 0.17, 1)     # aço das placas (o shader acende as nervuras)
    p.inputs['Metallic'].default_value = 0.0
    p.inputs['Roughness'].default_value = 0.55
    return m


def _uma_malha(peca):
    """antes_de_exportar: lona P_Esteira + tudo numa malha só (o lote usa a 1ª malha do .glb)."""
    def f(sc, raiz, dados):
        import bpy
        malhas = [o for o in sc.objects if o.type == 'MESH']
        corpo = next(o for o in malhas if o.name.endswith('_corpo'))
        uvn = corpo.data.uv_layers.active.name if corpo.data.uv_layers else 'UVMap'
        bm = _lona_bm(peca)
        me = bpy.data.meshes.new('lona')
        bm.to_mesh(me)
        bm.free()
        me.uv_layers[0].name = uvn
        me.materials.append(_material_lona())
        lona = bpy.data.objects.new('lona', me)
        sc.collection.objects.link(lona)
        bpy.ops.object.select_all(action='DESELECT')
        for o in malhas + [lona]:
            o.select_set(True)
        bpy.context.view_layer.objects.active = corpo
        bpy.ops.object.join()
        # o lote lê só a malha (sem a transformação do nó): vértices no espaço da raiz, nó na origem
        corpo.data.transform(raiz.matrix_world.inverted() @ corpo.matrix_world)
        corpo.parent = raiz
        corpo.matrix_parent_inverse.identity()
        corpo.matrix_basis.identity()
        for o in list(sc.objects):                         # vazios que sobraram (pais das luzes juntadas)
            if o.type == 'EMPTY' and o is not raiz and not o.name.startswith('PORTA_') and not o.children:
                bpy.data.objects.remove(o, do_unlink=True)
    return f


# ------------------------------------------------------------------ acessórios (estudo_esteira_acessorios.py)
def _recortar(sc, x0, x1, y0, y1, z0=0.0, dz=H - 0.20, aplicar=True):
    """Leito do estudo (0,20 m) desce para o do jogo; corta o que passa da área (terra e esteiras dos tiles vizinhos)
    e o que fica abaixo do chão (no jogo o terreno cobre: o pórtico afunda nele)."""
    import bpy, bmesh
    from mathutils import Vector, Matrix
    base = sc.objects.get('_base')
    if base is None:
        base = bpy.data.objects.new('_base', None)
        sc.collection.objects.link(base)
        for o in list(sc.objects):
            if o is not base and o.parent is None:
                o.parent = base
    base.matrix_world = Matrix.Translation((0, 0, dz)) @ base.matrix_world
    bpy.context.view_layer.update()
    for o in [o for o in sc.objects if o.type == 'MESH']:
        if o.data.users > 1:
            o.data = o.data.copy()
        if o.modifiers and aplicar:
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            for m in list(o.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=m.name)
                except RuntimeError:
                    o.modifiers.remove(m)
        mw = o.matrix_world.copy()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(mw)
        for co, no in (((x1, 0, 0), (1, 0, 0)), ((x0, 0, 0), (-1, 0, 0)), ((0, y1, 0), (0, 1, 0)),
                       ((0, y0, 0), (0, -1, 0)), ((0, 0, z0), (0, 0, -1))):
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(co),
                                   plane_no=Vector(no), clear_outer=True)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        if not bm.faces:
            bm.free()
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        bm.transform(mw.inverted())
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()


def _acessorio(x0=-0.47, x1=0.47, y0=-0.5, y1=0.5, animados=()):
    """depois_de_montar: congela tudo no quadro 1 (menos os conjuntos `animados`, que seguem com a animação do
    estudo) e recorta."""
    def f(sc):
        import bpy
        sc.frame_set(1)
        for o in sc.objects:
            if o.animation_data and not any(a in o.name for a in animados):
                mw = o.matrix_world.copy()
                o.animation_data_clear()
                o.matrix_world = mw
        _recortar(sc, x0, x1, y0, y1)
    return f


VIZINHOS = ['alim', 'sai_', 'saiN', 'saiL', 'saiO', 'entS', 'entL', 'entO', 'item_', 'ponte', 'corte', 'subterranea',
            'marcos', '_placa', '_catraca', 'cascalho', 'lama_chao', 'poeira_chao']


CONFIG = {p: dict(script='conv_esteiras_bracos.py', args=[p], cat='logistica/esteira', tris=t, tex=512, anima=False,
                  tirar=[], antes_de_exportar=_uma_malha(p))
          for p, t in (('esteira_reta', 700), ('esteira_curva_esq', 1100), ('esteira_curva_dir', 1100),
                       ('esteira_rampa', 900), ('esteira_inicio', 1200), ('esteira_fim', 1000), ('esteira_juncao', 1100))}
for _p, _c in (('esteira_tunel_entrada', (0.0, 0.0, 0.0)), ('esteira_tunel_saida', (0.0, 3.0, 0.0))):
    CONFIG[_p] = dict(script='estudo_esteira_acessorios.py', args=['tunel'], cat='logistica/esteira', tris=2000, tex=1024,
                      anima=False, centro=_c, tirar=VIZINHOS + ['rampa_sobe' if 'entrada' in _p else 'rampa_desce'],
                      depois_de_montar=_acessorio(), antes_de_exportar=_uma_malha(_p))
# divisor e junção: nós comuns (não vão em lote); só o mecanismo segue com a animação do estudo (garfo/batente do
# divisor, comportas da junção) — roletes, correntes e porta-cabos congelam (dezenas de nós a menos por peça)
CONFIG['divisor'] = dict(script='estudo_esteira_acessorios.py', args=['divisor'], cat='logistica/esteira', tris=3500,
                         tex=1024, tirar=list(VIZINHOS),
                         depois_de_montar=_acessorio(-0.5, 0.5, -0.5, 0.5, ('batente', 'carro', 'palheta')))
CONFIG['juncao'] = dict(script='estudo_esteira_acessorios.py', args=['juncao'], cat='logistica/esteira', tris=3500,
                        tex=1024, tirar=list(VIZINHOS), depois_de_montar=_acessorio(-0.5, 0.5, -0.5, 0.5, ('lamina_',)))


# ================================================================== BRAÇOS
# Partes que o jogo mexe (Animador._braco_mecanico): giro (gira em Z), braco1/braco2 (giram em X no pivô do ombro e do
# cotovelo), garra (fica de pé); no longo também estagio2/estagio3 (o braço 2 telescópico estica no eixo dele) e os
# pistões de elevação (camisa presa no giro, haste presa na lança: miram um no outro). Tudo sai em REPOUSO (braço 1 de
# pé, braço 2 adiante) sem a animação do estudo; o .json leva os pivôs e o quanto o pulso desce para a garra pegar.
#   braco         ← estudo_braco.py (lib_pf: já vem com as partes base/giro/braco1/braco2/garra)
#   braco_rapido  ← estudo_braco_variantes.py (sem a laje de 5 cm: tudo desce Z0)
#   braco_longo   ← idem
Z0 = 0.05
L2MIN = 0.64
PIV = {
    'braco': dict(giro=(0, 0, 0.225), braco1=(0, 0, 0.37), braco2=(0, 0.10, 0.92), garra=(0, 0.286, 0.3305)),
    'braco_rapido': dict(giro=(0, 0, 0.225), braco1=(0, 0, 0.40), braco2=(0, 0, 0.95), garra=(0, 0.62, 0.95)),
    'braco_longo': dict(giro=(0, 0, 0.36), braco1=(0, 0, 0.57), braco2=(0, 0.20, 1.33), estagio2=(0, 0.20, 1.33),
                        estagio3=(0, 0.20, 1.33), garra=(0, 0.20 + L2MIN, 1.33), camisa=(0, 0.16, 0.45),
                        haste=(0, -0.10, 1.05)),
}
PAI = dict(giro='base', braco1='giro', braco2='braco1', estagio2='braco2', estagio3='estagio2', camisa='giro',
           haste='braco1')
# quanto o pulso desce do alvo do jogo (que é a altura do pulso da garra antiga) e onde o item fica preso abaixo do
# pulso: dedos do normal até 0,196 m, eletroímã do rápido a 0,115 m (o item pende embaixo), dedos do longo a 0,18 m
GARRA = {'braco': (-0.044, 0.086), 'braco_rapido': (-0.045, 0.105), 'braco_longo': (-0.06, 0.07)}


def _partes_braco(peca):
    piv = PIV[peca]
    ps = {}
    for pn, p in piv.items():
        pai = PAI.get(pn, 'braco2' if pn == 'garra' and peca != 'braco_longo' else 'estagio3')
        alvo = ['_' + pn] if peca == 'braco' else ['q%sq' % pn]
        ps[pn] = dict(objetos=alvo, pivo=p, pai=pai, tris=dict(giro=500, braco1=450, braco2=300, garra=250,
                                                                  estagio2=150, estagio3=150, camisa=250, haste=100)[pn])
    return ps


def _braco_rustico():
    """O braço normal vem da lib_pf, em cor lisa: destoava dos outros dois (assados da sujeira do estudo). Aqui ganha as
    tintas sujas do estudo_braco_variantes e uma chapa de chão levando o terminal de energia, que ficava solto no canto do
    tile, fora da base (no jogo parecia uma bola laranja largada no chão)."""
    import bpy, bmesh
    from mathutils import Vector
    sys.path.insert(0, AQUI)
    import mats
    from base3d import caixa, tubo
    tintas = {
        'P_Faixa': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, ferrugem=0.5, desgaste=0.95, sujeira=0.9),
        'P_Escuro': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, ferrugem=0.4, desgaste=0.75, sujeira=0.8),
        'P_Aco': mats.material('Placa de ferro', (0.30, 0.29, 0.28), 1.0, 0.45, pintura=False, ferrugem=0.9, sujeira=0.7),
        'P_Metal': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
        'P_Cobre': mats.material('Cobre velho', (0.40, 0.21, 0.11), 1.0, 0.5, pintura=False, ferrugem=0.3, sujeira=1.0),
    }
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        for s in o.material_slots:
            if s.material is not None and s.material.name.split('.')[0] in tintas:
                s.material = tintas[s.material.name.split('.')[0]]
    bm = bmesh.new()
    caixa(bm, Vector((0.295, -0.295, 0.02)), (0.21, 0.21, 0.04))           # chapa do terminal, encostada na base
    tubo(bm, Vector((0.17, -0.13, 0.07)), Vector((0.29, -0.30, 0.05)), 0.012, 8)   # conduíte da caixa de ligação até a chapa
    me = bpy.data.meshes.new('chapa_terminal')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(tintas['P_Aco'])
    ch = bpy.data.objects.new('braco_chapa_terminal', me)
    bpy.context.scene.collection.objects.link(ch)


def _montar_braco(peca):
    import bpy
    if peca == 'braco':
        estudo = os.path.join(AQUI, 'estudo_braco.py')
        g = {'__name__': 'estudo_braco', '__file__': estudo}       # sem o rodar(): só monta, sem prévia nem export
        exec(compile(open(estudo, encoding='utf-8').read(), estudo, 'exec'), g)
        g['lib_pf'].preparar_cena()
        m = g['braco_detalhado']()
        m.montar()
        for o in [o for o in bpy.data.objects if o.name.startswith('PORTA_')]:
            bpy.data.objects.remove(o, do_unlink=True)
        _braco_rustico()
        return
    estudo = os.path.join(AQUI, 'estudo_braco_variantes.py')
    sys.argv = [sys.argv[0], '--python', estudo, '--', 'nada']
    g = {'__name__': '__main__', '__file__': estudo}
    codigo = open(estudo, encoding='utf-8').read().split('# ------------------------------------------------------------------ braço normal aprovado')[0]
    exec(compile(codigo, estudo, 'exec'), g)
    eu, outro = ('rapido', 'longo') if peca == 'braco_rapido' else ('longo', 'rapido')
    sc = bpy.context.scene
    for o in sc.objects:                                   # sem a animação do estudo
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys:
            o.data.shape_keys.animation_data_clear()
    for mt in bpy.data.materials:
        if mt.node_tree and mt.node_tree.animation_data:
            mt.node_tree.animation_data_clear()
    bob = g['M']['bobina'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    bob.default_value = 0.0                                 # eletroímã apagado (só acende segurando)
    A = g['rap'] if eu == 'rapido' else g['lon']
    g['posar'](A, 0.0, A['delta'], 0.0, L2MIN, 1.0)        # repouso: braço 1 de pé, braço 2 adiante, garra de pé
    tira = ('_esteiras', '_item', '_espiral')
    sai = set()
    for o in list(sc.objects):
        n = o.name
        laje = o.type == 'MESH' and o.parent is not None and o.parent.name == eu + '_raiz'
        if n.startswith(outro + '_') or any(t in n for t in tira) or laje:
            sai |= {o.name} | {c.name for c in o.children_recursive}      # estêncil (texto) do outro braço junto
    for n in sai:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    raiz = bpy.data.objects[eu + '_raiz']
    raiz.location = (0, 0, -Z0)
    bpy.context.view_layer.update()
    # cada malha leva o nome da parte do jogo a que pertence (pelo empty mais próximo acima dela)
    mapa = {'giro': 'giro', 'pinhao': 'giro', 'braco1': 'braco1', 'braco2': 'braco2', 'garra': 'garra',
            'estagio2': 'estagio2', 'estagio3': 'estagio3', 'camisa': 'camisa', 'haste': 'haste'}
    for k, o in enumerate([o for o in sc.objects if o.type in ('MESH', 'FONT')]):
        p = o.parent
        while p is not None:
            chave = p.name[len(eu) + 1:].split('_')[0]
            if p.type == 'EMPTY' and chave in mapa:
                o.name = 'q%sq_%d' % (mapa[chave], k)
                break
            p = p.parent


def _braco_json(peca):
    """antes_de_exportar: pulso/garra para o Animador e o terminal de energia em cima da peça que está no lugar dele."""
    def f(sc, raiz, dados):
        dz, item = GARRA[peca]
        dados['garra'] = {'pulso_dz': dz, 'item': item}
        corpo = next(o for o in sc.objects if o.type == 'MESH' and o.name.endswith('_base'))
        novos = []
        for t in dados.get('terminais', []):
            zs = [(corpo.matrix_world @ v.co).z for v in corpo.data.vertices
                  if math.hypot((corpo.matrix_world @ v.co).x - t[0], (corpo.matrix_world @ v.co).y - t[1]) < 0.12]
            novos.append([t[0], t[1], round(max(zs), 3) if zs else t[2]])
        if novos:
            dados['terminais'] = novos
    return f


for _p, _t in (('braco', 2000), ('braco_rapido', 2400), ('braco_longo', 2400)):
    # margem: em repouso a garra fica adiante do tile (o longo a 0,84 m do centro); a cena só tem o braço
    CONFIG[_p] = dict(script='conv_esteiras_bracos.py', args=[_p], cat='logistica/bracos', tris=_t, tex=1024, anima=False,
                      margem=1.0, depois_de_montar=None if _p == 'braco' else (lambda sc: _recortar(sc, -0.5, 0.5, -0.5, 2.0, 0.0, 0.0, False)),
                      corpo='base', tirar=[], partes=_partes_braco(_p), antes_de_exportar=_braco_json(_p))


if __name__ == '__main__':
    _peca = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''
    if _peca in ESTEIRAS:
        _montar_esteira(_peca)
    elif _peca in PIV:
        _montar_braco(_peca)
