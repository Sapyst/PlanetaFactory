"""Estudo isolado (fora do jogo): acessórios da esteira aprovada (estudo_esteira.py) — mesmo leito de placas de metal
com folga igual, laterais em perfil U com listras, catracas, motor com corrente, cavaletes, mesma altura (0,20 m) e
largura. Portas iguais ao CATALOGO.md (x leste, y norte, 1 tile = 1 m).

  esteira_tunel_entrada / esteira_tunel_saida (1×1): pórtico blindado de concreto e aço meio enterrado, cortina de
      lamelas de borracha que o item empurra, rampa interna (a própria esteira mergulha) visível pela boca com luz
      interna, fotocélula com feixe na boca, giroflex de status, tampa de inspeção aparafusada com olhais, exaustor
      girando, terra em volta e por cima; o item segue por baixo da terra (2 tiles livres no estudo, até 4 no jogo).
  divisor (1×1): entra S, sai N/L/O. Mesa de roletes direcionais (cada braço da cruz gira para o seu lado), batente
      que sobe entre os roletes, garfo de duas palhetas (pistões verticais) num carro sobre atuador linear com
      esteira porta-cabos, fotocélula de entrada, olho de filtro (violeta), motor com corrente, caixa de controle,
      bloco de válvulas, mangueiras e eletrocalhas.
  juncao (1×1): entra S/L/O, sai N. Roletes convergentes em V, comportas de prioridade (lâmina guilhotina erguida por
      dois pistões) nas entradas laterais, fotocélulas em cada entrada, lâmpadas de comporta, motor com corrente.

Itens (minério e chapas) andam casados com as placas e os roletes; laço de 4 s (96 quadros a 24 qps).
Uso: blender -b --python estudo_esteira_acessorios.py -- <tunel|divisor|juncao|linha> [foto]"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
H = 0.20            # topo do leito
W = 0.60            # largura das placas
PASSO = 0.10
VEL = 0.5
FPS = 24
QUADROS = 96        # 4 s em laço
DURACAO = QUADROS / FPS
ZI = H + 0.012      # fundo do item (em cima das nervuras / dos roletes)

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CENA = args[0] if args else 'linha'
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'


def emissivo(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def lente_mat():
    m = bpy.data.materials.new('Lente')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1)
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Coat Weight'].default_value = 1.0
    return m


M = {
    'placa': mats.material('Placa', (0.40, 0.41, 0.42), 1.0, 0.5, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.5),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.8, sujeira=0.7),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'lamela': mats.material('Lamela', (0.03, 0.03, 0.03), 0, 0.7, pintura=False, sujeira=0.9, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.36, 0.35, 0.33), 0, 0.92, pintura=False, sujeira=0.9, desgaste=0.0),
    'terra': mats.material('Terra', (0.15, 0.095, 0.06), 0, 0.97, pintura=False, sujeira=0.5, desgaste=0.0),
    'cascalho': mats.material('Cascalho', (0.22, 0.2, 0.18), 0, 0.9, pintura=False, sujeira=0.4, desgaste=0.0),
    'minerio': mats.material('Minério', (0.17, 0.075, 0.045), 0.35, 0.62, pintura=False, sujeira=0.9, ferrugem=0.8),
    'chapa': mats.material('Chapa', (0.58, 0.59, 0.61), 1.0, 0.28, pintura=False, ferrugem=0.15, sujeira=0.4, escovado=True),
    'rolo': mats.material('Rolo', (0.55, 0.55, 0.56), 1.0, 0.42, pintura=False, ferrugem=0.7, sujeira=1.0, escovado=True),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'laranja': mats.material('Cabo laranja', (0.75, 0.22, 0.03), 0, 0.5, sujeira=0.4, desgaste=0.1),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'lente': lente_mat(),
    'feixe': emissivo('Feixe', (1.0, 0.04, 0.02), 30.0),
    'olho': emissivo('Olho', (0.55, 0.15, 1.0), 14.0),
    'led_verde': emissivo('LED verde', (0.15, 1.0, 0.2), 8.0),
    'led_ambar': emissivo('LED âmbar', (1.0, 0.45, 0.04), 8.0),
    'luz_int': emissivo('Luz interna', (1.0, 0.72, 0.42), 25.0),
    'zarcao': mats.material('Zarcão', (0.36, 0.085, 0.04), 0, 0.62, desgaste=0.9, sujeira=0.8),
    'primer': mats.material('Primer cinza', (0.30, 0.31, 0.30), 0, 0.7, desgaste=0.8, sujeira=0.8),
    'rolo_novo': mats.material('Rolo novo', (0.74, 0.75, 0.77), 1.0, 0.22, pintura=False, sujeira=0.25),
    'lamela_cinza': mats.material('Lamela cinza', (0.13, 0.13, 0.12), 0, 0.75, pintura=False, sujeira=0.9, desgaste=0.0),
    'ferrugem': emissivo('Ferrugem escorrida', (0.075, 0.032, 0.014), 0.0),
    'fuligem': mats.material('Fuligem', (0.018, 0.017, 0.016), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.11, 0.075, 0.045), 0, 0.55, pintura=False, sujeira=0.3, desgaste=0.0),
    'poeira': mats.material('Poeira', (0.28, 0.25, 0.21), 0, 0.97, pintura=False, sujeira=0.2, desgaste=0.0),
    'po_minerio': mats.material('Pó de minério', (0.24, 0.10, 0.05), 0, 0.95, pintura=False, sujeira=0.3, desgaste=0.0),
}
base3d.M = M
LAMPADAS = []          # (material, função t → (cor, força))


def lampada(nome, fn):
    m = emissivo(nome, (0.1, 1.0, 0.2), 6.0)
    M[nome] = m
    LAMPADAS.append((m, fn))
    return nome


def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, eixo=Z, nR=24, nr=8):
    rot = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def prisma_yz(bm, pts, x0, x1):
    """Polígono no plano y-z extrudado de x0 a x1."""
    a = [bm.verts.new((x0, y, z)) for y, z in pts]
    b = [bm.verts.new((x1, y, z)) for y, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        bm.faces.new((a[(i + 1) % n], a[i], b[i], b[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def feixe(bc, ba, pts, n=3, r=0.006, passo=4, lado=X):
    for i in range(n):
        off = lado * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.008, pts[j] + u * 0.008, r * (n + 1.0), 10)


# ------------------------------------------------------------------ desgaste: nada sai enxuto
def envelhecer(m, poeira=0.75, lama=0.85, z_lama=0.13):
    """Poeira assentada nas faces de cima e lama respingada embaixo (pela altura no mundo), por cima do material."""
    nt = m.node_tree
    b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    ent = b.inputs['Base Color']
    src = ent.links[0].from_socket if ent.links else None
    cor0 = tuple(ent.default_value)
    N = lambda t: nt.nodes.new(t)
    coord, geo = N('ShaderNodeTexCoord'), N('ShaderNodeNewGeometry')
    sn, sp = N('ShaderNodeSeparateXYZ'), N('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    topo = N('ShaderNodeMapRange')
    topo.inputs['From Min'].default_value, topo.inputs['From Max'].default_value = 0.45, 0.95
    nt.links.new(sn.outputs['Z'], topo.inputs['Value'])
    ru = N('ShaderNodeTexNoise')
    ru.inputs['Scale'].default_value, ru.inputs['Detail'].default_value = 7.0, 8.0
    nt.links.new(coord.outputs['Object'], ru.inputs['Vector'])
    rm = N('ShaderNodeMapRange')
    rm.inputs['From Min'].default_value, rm.inputs['From Max'].default_value = 0.40, 0.62
    rm.inputs['To Max'].default_value = poeira
    nt.links.new(ru.outputs['Fac'], rm.inputs['Value'])
    mk = N('ShaderNodeMath'); mk.operation = 'MULTIPLY'
    nt.links.new(topo.outputs['Result'], mk.inputs[0]); nt.links.new(rm.outputs['Result'], mk.inputs[1])
    c1 = N('ShaderNodeMix'); c1.data_type = 'RGBA'
    if src is not None:
        nt.links.new(src, c1.inputs[6])
    else:
        c1.inputs[6].default_value = cor0
    c1.inputs[7].default_value = (0.36, 0.30, 0.22, 1)
    nt.links.new(mk.outputs['Value'], c1.inputs[0])
    baixo = N('ShaderNodeMapRange')
    baixo.inputs['From Min'].default_value, baixo.inputs['From Max'].default_value = z_lama, 0.0
    nt.links.new(sp.outputs['Z'], baixo.inputs['Value'])
    ru2 = N('ShaderNodeTexNoise')
    ru2.inputs['Scale'].default_value, ru2.inputs['Detail'].default_value = 24.0, 6.0
    nt.links.new(geo.outputs['Position'], ru2.inputs['Vector'])
    rm2 = N('ShaderNodeMapRange')
    rm2.inputs['From Min'].default_value, rm2.inputs['From Max'].default_value = 0.30, 0.58
    rm2.inputs['To Max'].default_value = lama
    nt.links.new(ru2.outputs['Fac'], rm2.inputs['Value'])
    mk2 = N('ShaderNodeMath'); mk2.operation = 'MULTIPLY'
    nt.links.new(baixo.outputs['Result'], mk2.inputs[0]); nt.links.new(rm2.outputs['Result'], mk2.inputs[1])
    c2 = N('ShaderNodeMix'); c2.data_type = 'RGBA'
    nt.links.new(c1.outputs[2], c2.inputs[6])
    c2.inputs[7].default_value = (0.10, 0.068, 0.04, 1)
    nt.links.new(mk2.outputs['Value'], c2.inputs[0])
    nt.links.new(c2.outputs[2], ent)
    rin = b.inputs['Roughness']
    soma = N('ShaderNodeMath'); soma.operation = 'ADD'
    nt.links.new(mk.outputs['Value'], soma.inputs[0]); nt.links.new(mk2.outputs['Value'], soma.inputs[1])
    mx = N('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    if rin.links:
        nt.links.new(rin.links[0].from_socket, mx.inputs[0])
    else:
        mx.inputs[0].default_value = rin.default_value
    nt.links.new(soma.outputs['Value'], mx.inputs[1])
    nt.links.new(mx.outputs['Value'], rin)
    if not b.inputs['Metallic'].links and b.inputs['Metallic'].default_value > 0.5:
        mt = N('ShaderNodeMath'); mt.operation = 'SUBTRACT'
        mt.inputs[0].default_value = b.inputs['Metallic'].default_value
        nt.links.new(soma.outputs['Value'], mt.inputs[1])
        nt.links.new(mt.outputs['Value'], b.inputs['Metallic'])


def serie_mat():
    """Tinta de estêncil branca, meio raspada (alfa por ruído): números de série apagados."""
    m = bpy.data.materials.new('Estêncil')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.62, 0.6, 0.55, 1)
    b.inputs['Roughness'].default_value = 0.8
    ru = nt.nodes.new('ShaderNodeTexNoise')
    ru.inputs['Scale'].default_value, ru.inputs['Detail'].default_value = 60.0, 8.0
    co = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(co.outputs['Object'], ru.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.47, 0.56
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = 0.0, 0.75
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], b.inputs['Alpha'])
    return m


def serie(texto, loc, normal, cima=Z, tam=0.03, pai=None):
    """Número de série em estêncil colado na face com `normal` (texto de pé, para `cima`)."""
    cu = bpy.data.curves.new('serie', 'FONT')
    cu.body = texto
    cu.size = tam
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    o = bpy.data.objects.new('serie', cu)
    sc.collection.objects.link(o)
    o.data.materials.append(M['serie'])
    n = Vector(normal).normalized()
    up = (Vector(cima) - n * Vector(cima).dot(n)).normalized()
    dx = up.cross(n)
    o.rotation_euler = Matrix((dx, up, n)).transposed().to_euler()
    o.location = Vector(loc) + n * 0.0012
    if pai is not None:
        o.parent = pai
    return o


M['serie'] = serie_mat()


def amassar(o, mossas, cortes=10):
    """Amassados: subdivide e afunda a malha (ao longo da normal) em volta de cada ponto (mundo)."""
    bpy.context.view_layer.update()
    bm = bmesh.new()
    bm.from_mesh(o.data)
    if cortes:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cortes, use_grid_fill=True)
    bm.normal_update()
    inv = o.matrix_world.inverted()
    for c, r, d in mossas:
        cl = inv @ Vector(c)
        for v in bm.verts:
            dist = (v.co - cl).length
            if dist < r:
                v.co -= v.normal * d * (1 - (dist / r) ** 2) ** 2
    bm.to_mesh(o.data)
    bm.free()


def eixos_face(n):
    n = Vector(n).normalized()
    a = Z if abs(n.z) < 0.9 else X
    u = a.cross(n).normalized()
    v = n.cross(u).normalized()
    return u, v, n


def remendo(bm, bp, c, n, w, h, giro=0.0):
    """Chapa de remendo aparafusada sobre a face (n), meio torta, com parafusos nos cantos e no meio."""
    u, v, n = eixos_face(n)
    rot = Matrix.Rotation(giro, 3, n)
    u, v = rot @ u, rot @ v
    m = Matrix((u, v, n)).transposed()
    c = Vector(c) + n * 0.0025
    caixa(bm, c, (w, h, 0.004), m)
    for su in (-1, 0, 1):
        for sv in (-1, 1):
            if su == 0 and w < 0.08:
                continue
            cil(bp, c + u * su * (w / 2 - 0.009) + v * sv * (h / 2 - 0.009) + n * 0.003, 0.0045, 0.004, n, lados=6)


def escorrido(bm, c, n, comp, larg):
    """Escorrido (ferrugem, óleo, fuligem) descendo pela face a partir de c: faixa que afina."""
    u, v, n = eixos_face(n)
    c = Vector(c) + n * 0.0008
    k = 4
    for i in range(k):
        f = 1 - i / k
        caixa(bm, c - Z * (comp * (i + 0.5) / k), (larg * (0.6 + 0.6 * f), 0.0005, comp / k + 0.002) if abs(n.y) > 0.5 else (0.0005, larg * (0.6 + 0.6 * f), comp / k + 0.002))


def fio_exposto(bc, bcu, pts, r=0.004):
    """Cabo solto com a capa cortada na ponta e os fios de cobre abertos."""
    pts = [Vector(p) for p in pts]
    mangueira(bc, pts, r)
    fim, d = pts[-1], (pts[-1] - pts[-2]).normalized()
    u, v, _ = eixos_face(d)
    for k in range(4):
        a = k * PI / 2 + 0.3
        q = fim + d * 0.025 + (u * math.cos(a) + v * math.sin(a)) * 0.006
        mangueira(bcu, [fim - d * 0.002, fim + d * 0.012, q], 0.0011)


def montinhos(bm, pontos, n=6, r=(0.004, 0.012)):
    """Pó/farelo de minério acumulado (montinhos chatos) em volta de cada ponto."""
    for p in pontos:
        p = Vector(p)
        for k in range(n):
            pedra(bm, p + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0)), random.uniform(*r), 0.35)


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def janela(t, a, b, sobe, desce):
    """0 → 1 a partir de a (em `sobe` s), volta a 0 a partir de b (em `desce` s); periódico no laço."""
    v = 0.0
    for k in (-3, -2, -1, 0, 1, 2, 3):
        tt = t + k * DURACAO
        v = max(v, suave((tt - a) / sobe) * (1 - suave((tt - b) / desce)))
    return v


def girar(o, total, idx=0):
    o.rotation_euler[idx] = 0.0
    o.keyframe_insert('rotation_euler', index=idx, frame=1)
    o.rotation_euler[idx] = total
    o.keyframe_insert('rotation_euler', index=idx, frame=QUADROS + 1)


def girante(nome, bm, mat, c, eixo, total, pai=None):
    """Malha feita com o eixo em X; o objeto gira em X (local) e é virado para `eixo` (horizontal) por guinada."""
    o = obj(nome, bm, mat, pai)
    e = Vector(eixo).normalized()
    o.location = c
    o.rotation_mode = 'XYZ'
    o.rotation_euler = (0, -math.asin(max(-1, min(1, e.z))), math.atan2(e.y, e.x))
    girar(o, total)
    return o


def roda_mesh(bm, r, dentes, esp, c=Vector()):
    cil(bm, c, r * 0.82, esp, X, lados=dentes * 2)
    for k in range(dentes):
        rot = Matrix.Rotation(k * 2 * PI / dentes, 3, 'X')
        caixa(bm, c + rot @ Vector((0, 0, r * 0.9)), (esp * 0.9, r * 0.22, r * 0.26), rot)
    cil(bm, c, r * 0.3, esp * 1.6, X, lados=8)


# ================================================================== esteira aprovada (copiada de estudo_esteira.py)
RHO = 0.066
FOLGA = 0.014
M_MIN = RHO + 0.006
VEL_R = round(VEL * DURACAO / PASSO) * PASSO / DURACAO
GIRO = PI * round(VEL_R * DURACAO / RHO / PI)


def caminho_seg(a, b):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    d = (b - a) / L
    return L, lambda s: (a + d * s, d), 0.0


def caminho_curva(R=0.5, sentido=1):
    """sentido +1: entra pelo oeste indo +x e vira à esquerda (sai ao norte); −1: vira à direita (sai ao sul)."""
    L = R * PI / 2
    c = Vector((-0.5, 0.5 * sentido, 0))
    def f(s):
        a = -sentido * PI / 2 + sentido * s / R
        return (Vector((c.x + R * math.cos(a), c.y + R * math.sin(a), H)),
                Vector((-math.sin(a) * sentido, math.cos(a) * sentido, 0)))
    return L, f, sentido / R


def varrer(bm, f, L, n, perfil):
    aneis = []
    for i in range(n + 1):
        p, d = f(L * i / n)
        m = base(d)
        aneis.append([bm.verts.new(p + m @ Vector((0, y, z))) for y, z in perfil])
    k = len(perfil)
    for i in range(n):
        a, b = aneis[i], aneis[i + 1]
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])


def ret(y0, y1, z0, z1):
    return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]


def placa_trapezio(bm, passo, curv, y0, y1, z0, z1):
    vs = []
    for z in (z0, z1):
        for y, sx in ((y0, -1), (y0, 1), (y1, 1), (y1, -1)):
            hx = (passo * (1.0 - curv * y) - FOLGA) / 2.0
            vs.append(bm.verts.new(Vector((sx * hx, y, z))))
    b0, b1 = vs[:4], vs[4:]
    bm.faces.new(list(reversed(b0)))
    bm.faces.new(b1)
    for j in range(4):
        bm.faces.new((b0[j], b0[(j + 1) % 4], b1[(j + 1) % 4], b1[j]))


def base(dirc):
    lado = Vector((0, 0, 1)).cross(dirc).normalized()
    cima = dirc.cross(lado).normalized()
    return Matrix((dirc, lado, cima)).transposed()


def catraca(nome, centro, eixo, r, dentes, esp, mat, pai):
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), r * 0.82, esp, Vector((0, 0, 1)), lados=dentes * 2)
    for k in range(dentes):
        a = k * 2 * PI / dentes
        rot = Matrix.Rotation(a, 3, 'Z')
        caixa(bm, rot @ Vector((r * 0.9, 0, 0)), (r * 0.26, r * 0.22, esp * 0.9), rot)
    cil(bm, Vector((0, 0, 0)), r * 0.3, esp * 1.6, lados=8)
    o = obj(nome, bm, mat, pai)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(eixo).normalized().to_track_quat('Z', 'Y')
    o.location = centro
    return o


ESTEIRAS = []


def esteira(nome, caminho, origem=Vector(), rot_z=0.0, motor=True, pernas=True):
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    raiz.location = origem
    raiz.rotation_euler.z = rot_z
    L, f, curv = caminho
    n_seg = max(8, int(L / 0.03))
    for lado_s in (-1, 1):
        y = lado_s * (W / 2 + 0.03)
        bm, bl = bmesh.new(), bmesh.new()
        varrer(bm, f, L, n_seg, ret(y - 0.009, y + 0.009, -0.105, 0.015))
        for z in (0.006, -0.106):
            varrer(bm, f, L, n_seg, ret(min(y, y - lado_s * 0.045), max(y, y - lado_s * 0.045), z, z + 0.012))
        yf = y + lado_s * 0.0105
        varrer(bl, f, L, n_seg, ret(yf - 0.0015, yf + 0.0015, -0.065, -0.015))
        obj(nome + '_lateral', bm, 'grafite', raiz)
        obj(nome + '_faixa', bl, 'listras', raiz)
    if pernas:
        bm = bmesh.new()
        n_cav = max(2, int(round(L / 0.5)) + 1)
        for i in range(n_cav):
            s_c = 0.07 + (L - 0.14) * i / (n_cav - 1)
            p, d = f(s_c)
            m = base(d)
            dh = Vector((d.x, d.y, 0)).normalized()
            mh = base(dh)
            pes = []
            for lado_s in (-1, 1):
                topo = p + m @ Vector((0, lado_s * (W / 2 + 0.03), -0.112))
                pes.append(topo)
                caixa(bm, Vector((topo.x, topo.y, topo.z / 2)), (0.04, 0.04, topo.z), mh)
                caixa(bm, Vector((topo.x, topo.y, 0.008)), (0.1, 0.09, 0.016), mh)
                for dx in (-0.032, 0.032):
                    cil(bm, Vector((topo.x, topo.y, 0.02)) + mh @ Vector((dx, 0, 0)), 0.008, 0.012, lados=6)
            a0, a1 = pes
            zt = min(a0.z, a1.z) - 0.03
            caixa(bm, Vector(((a0.x + a1.x) / 2, (a0.y + a1.y) / 2, zt)), (0.035, (a1 - a0).length + 0.04, 0.03), mh)
            d0 = Vector((a0.x, a0.y, 0.06))
            d1 = Vector((a1.x, a1.y, zt - 0.02))
            e = (d1 - d0)
            q = e.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((d0 + d1) / 2) @ q @ Matrix.Diagonal((0.022, 0.022, e.length, 1)))
        obj(nome + '_cavaletes', bm, 'aco', raiz)
    n_placas = int((2.0 * (L - 2.0 * M_MIN) + 2.0 * PI * RHO) / PASSO)
    Lr = (n_placas * PASSO - 2.0 * PI * RHO) / 2.0
    m = (L - Lr) / 2.0
    total = n_placas * PASSO
    rodas = []
    for s in (m, L - m):
        p, d = f(s)
        mr = base(d)
        lado = mr @ Vector((0, 1, 0))
        for lado_s in (-1, 1):
            rodas.append((catraca(nome + '_catraca', p + mr @ Vector((0, lado_s * (W / 2 - 0.08), -RHO)), lado, 0.055, 10, 0.025, 'aco', raiz), 1.0))
        bm = bmesh.new()
        cil(bm, p + mr @ Vector((0, 0, -RHO)), 0.012, W + 0.02, lado, lados=8)
        obj(nome + '_eixo', bm, 'cromo', raiz)
    correntes = []
    y_fora = -(W / 2 + 0.075)
    if motor:
        pe_, de_ = f(L - m)
        mm = base(de_)
        lado = mm @ Vector((0, 1, 0))
        eixo_c = pe_ + mm @ Vector((0, 0, -RHO))
        coroa_c = eixo_c + mm @ Vector((0, y_fora, 0))
        pinhao_c = coroa_c + mm @ Vector((-0.02, 0, -0.17))
        bm = bmesh.new()
        cil(bm, eixo_c + mm @ Vector((0, y_fora * 0.93, 0)), 0.012, 0.09, lado, lados=8)
        caixa(bm, pinhao_c + mm @ Vector((-0.0, 0.03, -0.0)), (0.11, 0.07, 0.085), mm)
        cil(bm, pinhao_c + mm @ Vector((-0.09, 0.03, 0)), 0.038, 0.07, mm @ Vector((1, 0, 0)), lados=12)
        for k in range(4):
            cil(bm, pinhao_c + mm @ Vector((-0.065 - 0.018 * k, 0.03, 0)), 0.045, 0.006, mm @ Vector((1, 0, 0)), lados=12)
        obj(nome + '_motor', bm, 'amarelo', raiz)
        bm = bmesh.new()
        caixa(bm, pinhao_c + mm @ Vector((0.0, 0.075, -0.0)), (0.13, 0.012, 0.11), mm)
        perna = pe_ + mm @ Vector((0, -(W / 2 + 0.03), -0.112))
        caixa(bm, (pinhao_c + mm @ Vector((0.03, 0.075, 0)) + Vector((perna.x, perna.y, pinhao_c.z))) / 2, (0.05, 0.02, 0.05), mm)
        obj(nome + '_suporte', bm, 'grafite', raiz)
        rodas.append((catraca(nome + '_pinhao', pinhao_c, lado, 0.03, 8, 0.02, 'cromo', raiz), 12 / 8))
        rodas.append((catraca(nome + '_coroa', coroa_c, lado, 0.05, 12, 0.02, 'aco', raiz), 1.0))
        correntes.append(corrente(nome, (pinhao_c, 0.03 * 0.95, coroa_c, 0.05 * 0.95, lado), raiz))
        bm = bmesh.new()                                                       # pinga óleo embaixo do motor
        pm = Matrix.Translation(origem) @ Matrix.Rotation(rot_z, 4, 'Z') @ pinhao_c
        mancha(bm, (pm.x, pm.y), 0.07, 0.0015)
        obj(nome + '_oleo', bm, 'oleo')
    placas = []
    for k in range(n_placas):
        bm = bmesh.new()
        placa_trapezio(bm, PASSO, curv, -W / 2, W / 2, -0.006, 0.006)
        for dy in (-W / 4, W / 4):
            placa_trapezio(bm, 0.012 + FOLGA, 0.0, dy - (W / 4 - 0.03), dy + (W / 4 - 0.03), 0.006, 0.012)
        placas.append(obj(nome + '_placa', bm, 'placa', raiz))
    for r, _ in rodas:
        r['_q0'] = list(r.rotation_quaternion)
    mundo = Matrix.Translation(origem) @ Matrix.Rotation(rot_z, 4, 'Z')
    e = {'f': f, 'L': L, 'm': m, 'Lr': Lr, 'total': total, 'placas': placas, 'rodas': rodas,
         'correntes': correntes, 'mundo': mundo}
    ESTEIRAS.append(e)
    return e


def reta(nome, a, b, **kw):
    """Esteira reta entre dois pontos do chão (a → b), no nível do leito."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    d = b - a
    return esteira(nome, caminho_seg(Vector((-d.length / 2, 0, H)), Vector((d.length / 2, 0, H))), (a + b) / 2,
                   math.atan2(d.y, d.x), **kw)


def corrente(nome, laco, pai, passo_elo=0.026):
    n = max(8, int(round(comprimento_laco(laco) / passo_elo)))
    elos = []
    for k in range(n):
        bm = bmesh.new()
        caixa(bm, Vector((0, 0, 0)), (0.016, 0.012, 0.008))
        o = obj(nome + '_elo', bm, 'grafite', pai)
        o.rotation_mode = 'QUATERNION'
        elos.append(o)
    return {'laco': laco, 'elos': elos}


def comprimento_laco(laco):
    pc, rp, cc, rc, lado = laco
    cima = (cc - pc).normalized()
    frente = cima.cross(lado).normalized()
    return 2 * ((cc + frente * rc) - (pc + frente * rp)).length + PI * (rp + rc)


def ponto_laco(laco, d):
    pc, rp, cc, rc, lado = laco
    cima = (cc - pc).normalized()
    frente = cima.cross(lado).normalized()
    a0, a1 = pc + frente * rp, cc + frente * rc
    b0, b1 = cc - frente * rc, pc - frente * rp
    reta_ = (a1 - a0).length
    d %= comprimento_laco(laco)
    if d < reta_:
        return a0 + (a1 - a0) * (d / reta_)
    d -= reta_
    if d < PI * rc:
        a = d / rc
        return cc + frente * (rc * math.cos(a)) + cima * (rc * math.sin(a))
    d -= PI * rc
    if d < reta_:
        return b0 + (b1 - b0) * (d / reta_)
    d -= reta_
    a = PI + d / rp
    return pc + frente * (rp * math.cos(a)) + cima * (rp * math.sin(a))


def no_laco(f, m, Lr, u):
    meia = PI * RHO
    if u < Lr:
        p, d = f(m + u)
        return p, base(d).to_quaternion()
    u -= Lr
    if u < meia:
        p, d = f(m + Lr)
        mb = base(d)
        a = u / RHO
        return p + mb @ Vector((RHO * math.sin(a), 0, RHO * math.cos(a) - RHO)), mb.to_quaternion() @ Quaternion((0, 1, 0), a)
    u -= meia
    if u < Lr:
        p, d = f(m + Lr - u)
        mb = base(d)
        return p + mb @ Vector((0, 0, -2 * RHO)), mb.to_quaternion() @ Quaternion((0, 1, 0), PI)
    u -= Lr
    p, d = f(m)
    mb = base(d)
    a = PI + u / RHO
    return p + mb @ Vector((RHO * math.sin(a), 0, RHO * math.cos(a) - RHO)), mb.to_quaternion() @ Quaternion((0, 1, 0), a)


def animar_corrente(c, giro_raio):
    comp = comprimento_laco(c['laco'])
    n = len(c['elos'])
    elo = comp / n
    desloc = round(giro_raio / elo) * elo
    lado = c['laco'][4]
    for q in range(1, QUADROS + 1):
        t = (q - 1) / FPS
        for k, o in enumerate(c['elos']):
            d = k * elo + desloc * t / DURACAO
            p = ponto_laco(c['laco'], d)
            tg = (ponto_laco(c['laco'], d + 0.002) - p).normalized()
            o.location = p
            o.rotation_quaternion = Matrix((tg, lado, tg.cross(lado))).transposed().to_quaternion()
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)


def animar_esteira(e, fase=0.0):
    f, m, Lr, total = e['f'], e['m'], e['Lr'], e['total']
    for q in range(1, QUADROS + 1):
        t = (q - 1) / FPS
        for k, o in enumerate(e['placas']):
            p, qr = no_laco(f, m, Lr, (k * PASSO + VEL_R * t + fase) % total)
            o.location = p
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = qr
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
        for r, razao in e['rodas']:
            r.rotation_quaternion = Quaternion(r['_q0']) @ Quaternion((0, 0, 1), GIRO * razao * t / DURACAO)
            r.keyframe_insert('rotation_quaternion', frame=q)
    for c in e['correntes']:
        animar_corrente(c, GIRO * c['laco'][3])


def ponta(e, qual):
    """Ponto (mundo) no plano das placas onde o laço vira: 'ini' (pé) ou 'fim' (cabeceira)."""
    p, d = e['f'](e['m'] if qual == 'ini' else e['L'] - e['m'])
    return e['mundo'] @ p


def ponte(pa, pb, larg=W - 0.01):
    """Chapa de transferência fixa sobre o vão entre duas peças (do topo de uma ao topo da outra)."""
    bm = bmesh.new()
    d = pb - pa
    mb = base(d.normalized())
    caixa(bm, (pa + pb) / 2 + mb @ Vector((0, 0, 0.004)), (d.length + 0.03, larg, 0.008), mb)
    for y in (-larg / 2 + 0.025, larg / 2 - 0.025):
        for x in (-0.3, 0.3):
            cil(bm, (pa + pb) / 2 + mb @ Vector((x * d.length, y, 0.009)), 0.007, 0.003, mb @ Vector((0, 0, 1)), lados=6)
    obj('ponte', bm, 'aco')


def ponte_borda(e, qual, borda):
    """Chapa da ponta da esteira até a borda da peça vizinha (mesa de roletes ou rampa)."""
    pa = ponta(e, qual)
    ponte(pa, Vector((borda[0], borda[1], H)))


# ================================================================== itens e rotas
def item_obj(tipo, nome):
    bm = bmesh.new()
    if tipo == 'minerio':
        res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.062)
        sem = Vector((random.uniform(0, 50), random.uniform(0, 50), random.uniform(0, 50)))
        for v in res['verts']:
            n = noise.noise(v.co * 14 + sem)
            k = 1 + 0.32 * n + 0.10 * noise.noise(v.co * 30 + sem) + 0.05 * noise.noise(v.co * 90 + sem)
            v.co = Vector((v.co.x * 1.2 * k, v.co.y * 1.0 * k, v.co.z * 0.78 * k))
        zmin = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.z -= zmin
        return obj(nome, bm, 'minerio')
    caixa(bm, (0, 0, 0.0125), (0.21, 0.16, 0.025))
    caixa(bm, (0.008, -0.004, 0.0375), (0.21, 0.16, 0.025), Matrix.Rotation(0.07, 3, 'Z'))
    caixa(bm, (-0.004, 0.003, 0.0625), (0.21, 0.16, 0.025), Matrix.Rotation(-0.05, 3, 'Z'))
    return obj(nome, bm, 'chapa')


def ang(a):
    return (a + PI) % (2 * PI) - PI


class Rota:
    """Trajeto de um item no tempo: trechos de esteira (casados com as placas), retas sobre roletes, paradas,
    empurrões. Cada trecho é (início, duração, função τ → (posição, guinada, normal do apoio))."""
    def __init__(self, t0, tipo):
        self.t0, self.tipo = t0, tipo
        self.seg, self.T = [], 0.0
        self.pos, self.yaw, self.up = None, random.uniform(-0.3, 0.3), Z.copy()
        self.marcas = {}

    def _add(self, dur, fn):
        dur = max(dur, 1e-4)
        self.seg.append((self.T, dur, fn))
        self.T += dur
        self.pos, self.yaw, self.up = fn(dur)

    def agora(self):
        return self.t0 + self.T

    def esteira(self, e, s0=None, s1=None):
        f, mw = e['f'], e['mundo']
        R = mw.to_3x3()
        s0 = 0.0 if s0 is None else s0
        s1 = e['L'] if s1 is None else s1
        def pt(x):
            p, d = f(x)
            up = (R @ base(d).col[2]).normalized()
            hd = R @ d
            return mw @ p + up * 0.012, math.atan2(hd.y, hd.x), up
        h0 = pt(s0)[1]
        y0 = self.yaw
        dur = abs(s1 - s0) / VEL_R
        def fn(tau):
            p, h, u = pt(s0 + (s1 - s0) * min(1.0, tau / dur))
            return p, y0 + ang(h - h0), u
        self._add(dur, fn)

    def linha(self, p1, vel=None):
        p0, p1 = self.pos.copy(), Vector(p1)
        dur = (p1 - p0).length / (vel or VEL_R)
        y = self.yaw
        self._add(dur, lambda tau: (p0.lerp(p1, min(1.0, tau / dur)), y, Z))

    def curva(self, pts):
        for p in pts[1:]:
            self.linha(p)

    def pausa(self, dur):
        p, y, u = self.pos.copy(), self.yaw, self.up.copy()
        self._add(dur, lambda tau: (p, y, u))

    def ate(self, t_abs):
        if t_abs > self.agora() + 1e-4:
            self.pausa(t_abs - self.agora())

    def empurra(self, p1, dur):
        p0, p1 = self.pos.copy(), Vector(p1)
        y = self.yaw
        self._add(dur, lambda tau: (p0.lerp(p1, suave(tau / dur)), y, Z))

    def em(self, idade):
        for t_i, dur, fn in self.seg:
            if idade <= t_i + dur:
                return fn(idade - t_i)
        return self.seg[-1][2](self.seg[-1][1])


ROTAS = []
POS_ITENS = {}          # quadro → [posições dos itens visíveis]


def animar_itens():
    for q in range(1, QUADROS + 1):
        POS_ITENS[q] = []
    for i, r in enumerate(ROTAS):
        for j in range(-8, 12):
            a0 = -r.t0 + DURACAO * j                       # idade no instante 0
            if a0 + DURACAO < 0 or a0 > r.T:
                continue
            o = item_obj(r.tipo, 'item_%s' % r.tipo)
            o.rotation_mode = 'QUATERNION'
            for q in range(1, QUADROS + 1):
                idade = (q - 1) / FPS + a0
                vis = 0.0 <= idade <= r.T
                p, yaw, up = r.em(min(max(idade, 0.0), r.T))
                o.location = p
                o.rotation_quaternion = Z.rotation_difference(up) @ Quaternion(Z, yaw)
                o.scale = (1, 1, 1) if vis else (0.001, 0.001, 0.001)
                if vis:
                    POS_ITENS[q].append(p.copy())
                for c in ('location', 'rotation_quaternion', 'scale'):
                    o.keyframe_insert(c, frame=q)


FEIXES = []


def feixe_obj(nome, a, b):
    """Feixe da fotocélula (origem no emissor, ao longo de +Z local): encurta até o item que o corta."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    bm = bmesh.new()
    cil(bm, Vector((0, 0, L / 2)), 0.0012, L, lados=6)
    o = obj(nome, bm, 'feixe')
    o.location = a
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
    FEIXES.append((o, a, b))
    return o


def animar_feixes():
    for o, a, b in FEIXES:
        L = (b - a).length
        d = (b - a) / L
        for q in range(1, QUADROS + 1):
            corte = L
            for p in POS_ITENS[q]:
                if not (p.z - 0.01 < a.z < p.z + 0.13):
                    continue
                t = (p - a).dot(d)
                lat = ((p - a) - d * t)
                lat.z = 0
                if 0 < t < L and lat.length < 0.07:
                    corte = min(corte, max(0.01, t - 0.07))
            o.scale = (1, 1, corte / L)
            o.keyframe_insert('scale', index=2, frame=q)


def tem_item(q, centro, raio, dz=(-0.05, 0.2)):
    """Algum item perto do ponto (no plano) e na faixa de altura — usado pelos sensores."""
    for p in POS_ITENS[q]:
        if (Vector((p.x, p.y)) - Vector((centro[0], centro[1]))).length < raio and dz[0] <= p.z - centro[2] + 0.1 <= dz[1] + 0.1:
            return True
    return False


# ================================================================== roletes (mesas do divisor e da junção)
R_ROL = VEL_R * DURACAO / (2 * PI * 13)          # 13 voltas por laço: superfície anda casada com as placas
Z_ROL = ZI - R_ROL


def rolete(nome, c, v, comp, roda=None, mat='rolo'):
    """Rolete com eixo na horizontal; `v` = sentido em que leva o item (o topo anda para v)."""
    v = Vector(v).normalized()
    e = Z.cross(v)
    bm = bmesh.new()
    cil(bm, Vector(), R_ROL, comp, X, lados=20)
    for sx in (-1, 1):
        cil(bm, Vector((sx * (comp / 2 - 0.012), 0, 0)), R_ROL + 0.0015, 0.006, X, lados=20)      # aro
        cil(bm, Vector((sx * (comp / 2 + 0.006), 0, 0)), 0.007, 0.014, X, lados=8)               # ponta do eixo
    if roda is not None:                                                                         # eixo longo + catraca
        sx, x_r, r_r = roda
        cil(bm, Vector((sx * (comp / 2 + x_r / 2), 0, 0)), 0.008, x_r + 0.01, X, lados=8)
        roda_mesh(bm, r_r, 12, 0.012, Vector((sx * (comp / 2 + x_r), 0, 0)))
    o = obj(nome, bm, mat)
    suavizar(o)
    o.location = c
    o.rotation_mode = 'XYZ'
    o.rotation_euler = (0, 0, math.atan2(e.y, e.x))
    girar(o, 2 * PI * 13)
    return o, e


def anel_o(bm, c1, c2, e, a):
    """Correia redonda (anel O) entre dois roletes vizinhos, no canal a `a` m do centro ao longo do eixo e."""
    c1, c2 = c1 + e * a, c2 + e * a
    u = (c2 - c1).normalized()
    w = e.cross(u).normalized()
    rr = R_ROL - 0.001
    pts = []
    for k in range(9):
        t = PI / 2 + PI * k / 8
        pts.append(c1 + (u * math.cos(t) + w * math.sin(t)) * rr)
    for k in range(9):
        t = -PI / 2 + PI * k / 8
        pts.append(c2 + (u * math.cos(t) + w * math.sin(t)) * rr)
    pts.append(pts[0])
    mangueira(bm, pts, 0.0028)


def trilho(bm, bl, a, b, fora, alto=True):
    """Perfil U da lateral da esteira entre a e b (no nível H), com faixa listrada do lado `fora`."""
    a, b = Vector((a[0], a[1], H)), Vector((b[0], b[1], H))
    L = (b - a).length
    d = (b - a) / L
    f = lambda s: (a + d * s, d)
    lado = Z.cross(d)
    sg = 1 if lado.dot(Vector(fora)) > 0 else -1
    if alto:
        varrer(bm, f, L, 2, ret(-0.009, 0.009, -0.105, 0.015))
        for z in (0.006, -0.106):
            varrer(bm, f, L, 2, ret(min(0, -sg * 0.045), max(0, -sg * 0.045), z, z + 0.012))
        varrer(bl, f, L, 2, ret(sg * 0.0105 - 0.0015, sg * 0.0105 + 0.0015, -0.065, -0.015))
    else:
        varrer(bm, f, L, 2, ret(-0.008, 0.008, -0.075, -0.005))


def pes_mesa(bm, o, pontos):
    for (x, y) in pontos:
        p = o + Vector((x, y, 0))
        caixa(bm, p + Vector((0, 0, 0.0475)), (0.036, 0.036, 0.095))
        caixa(bm, p + Vector((0, 0, 0.008)), (0.06, 0.06, 0.016))
        for dx, dy in ((-0.03, -0.03), (0.03, 0.03), (-0.03, 0.03), (0.03, -0.03)):
            cil(bm, p + Vector((dx, dy, 0.02)), 0.007, 0.012, lados=6)


def mesa_cruz(nome, o, sentidos, centro_v=True):
    """Mesa 1×1 em cruz: braços N/S/L/O com laterais altas (perfil U listrado) e o centro com trilhos baixos
    (o item atravessa por cima). `sentidos`: dict braço → vetor de transporte dos roletes do braço."""
    bm, bl, bb = bmesh.new(), bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            trilho(bm, bl, (sx * 0.33, sy * 0.321), (sx * 0.33, sy * 0.5), (sx, 0, 0))        # braços N/S
            trilho(bm, bl, (sx * 0.321, sy * 0.33), (sx * 0.5, sy * 0.33), (0, sy, 0))        # braços L/O
    if centro_v:
        for sx in (-1, 1):
            trilho(bm, bl, (sx * 0.305, -0.30), (sx * 0.305, 0.30), (sx, 0, 0), alto=False)
    obj(nome + '_laterais', bm, 'grafite')
    obj(nome + '_faixas', bl, 'listras')
    bm = bmesh.new()
    pes_mesa(bm, o, [(sx * 0.33, sy * 0.33) for sx in (-1, 1) for sy in (-1, 1)] +
             [(sx * 0.33, sy * 0.47) for sx in (-1, 1) for sy in (-1, 1)] +
             [(sx * 0.47, sy * 0.33) for sx in (-1, 1) for sy in (-1, 1)])
    for sy in (-1, 1):                                                           # travessas sob o centro
        caixa_de(bm, o + Vector((-0.33, sy * 0.30 - 0.015, 0.098)), o + Vector((0.33, sy * 0.30 + 0.015, 0.125)))
        caixa_de(bm, o + Vector((sy * 0.33 - 0.015, -0.30, 0.098)), o + Vector((sy * 0.33 + 0.015, 0.30, 0.125)))
    for sx in (-1, 1):                                                           # mãos-francesas nos pés de canto
        for sy in (-1, 1):
            viga(bm, o + Vector((sx * 0.33, sy * 0.33, 0.05)), o + Vector((sx * 0.33, sy * 0.18, 0.098)), 0.018)
    obj(nome + '_estrutura', bm, 'aco')
    # roletes dos braços
    rolos = {}
    for braco, v in sentidos.items():
        v = Vector(v)
        dirb = {'N': Y, 'S': -Y, 'L': X, 'O': -X}[braco]
        lista = []
        for k, dist in enumerate((0.345, 0.405, 0.465)):
            c = o + dirb * dist + Vector((0, 0, Z_ROL))
            lista.append(rolete(nome + '_rolo_' + braco, c, v, 0.60)[0])
        rolos[braco] = lista
    bm = bmesh.new()                                                             # anéis O entre vizinhos
    for braco, lista in rolos.items():
        e = Z.cross(Vector(sentidos[braco])).normalized()
        for a_, b_ in zip(lista, lista[1:]):
            anel_o(bm, a_.location, b_.location, e, 0.27 if braco in 'NL' else -0.27)
    suavizar(obj(nome + '_aneis', bm, 'borracha'))
    return rolos


def motor_rolos(nome, o, x_pl, y_rolo, sx, sy):
    """Motorredutor amarelo embaixo do canto, pinhão e corrente de rolos até a catraca do eixo de um rolete."""
    pin = o + Vector((x_pl, y_rolo - sy * 0.015, 0.072))
    bm = bmesh.new()
    xa, xb = x_pl + sx * 0.03, x_pl + sx * 0.135
    caixa_de(bm, o + Vector((min(xa, xb), y_rolo - sy * 0.015 - 0.03, 0.035)), o + Vector((max(xa, xb), y_rolo - sy * 0.015 + 0.03, 0.11)))
    cil(bm, Vector(((o.x + xb + sx * 0.0), pin.y, 0.072)), 0.034, 0.03, X, lados=14)
    for k in range(4):
        cil(bm, Vector((o.x + xa + sx * (0.02 + 0.022 * k), pin.y, 0.072)), 0.045, 0.005, X, lados=14)
    obj(nome + '_motor', bm, 'amarelo')
    bm = bmesh.new()
    caixa_de(bm, o + Vector((min(xa, xb) - 0.01, y_rolo - sy * 0.015 - 0.045, 0.0)), o + Vector((max(xa, xb) + 0.01, y_rolo - sy * 0.015 + 0.045, 0.035)))
    tubo(bm, pin, pin + Vector((sx * 0.03, 0, 0)), 0.009, 8)
    obj(nome + '_base_motor', bm, 'grafite')
    bm = bmesh.new()
    mancha(bm, (pin.x + sx * 0.06, pin.y), 0.06, 0.0015)
    obj(nome + '_oleo', bm, 'oleo')
    giro_rolo = 2 * PI * 13
    bm = bmesh.new()
    roda_mesh(bm, 0.02, 8, 0.012)
    e = Z.cross(Vector((0, sy, 0))) if False else None
    return pin, giro_rolo


def caixa_controle(nome, o, a, b, antena=True):
    """Caixa de controle selada da IA: aletas de dissipação, fileira de LEDs, antena, prensa-cabos embaixo."""
    a, b = o + Vector(a), o + Vector(b)
    bm = bmesh.new()
    caixa_de(bm, a, b)
    obj(nome, bm, 'grafite')
    bm = bmesh.new()
    n = 6
    for k in range(n):                                                           # aletas no lado de cima
        x = a.x + (b.x - a.x) * (k + 0.5) / n
        caixa_de(bm, (x - 0.002, a.y + 0.008, b.z), (x + 0.002, b.y - 0.008, b.z + 0.018))
    for x in (a.x + 0.015, b.x - 0.015):
        cil(bm, Vector((x, (a.y + b.y) / 2, a.z - 0.008)), 0.008, 0.016, lados=8)
    obj(nome + '_aletas', bm, 'aco')
    if antena:
        bm = bmesh.new()
        tubo(bm, (b.x - 0.012, b.y - 0.012, b.z), (b.x - 0.012, b.y - 0.012, b.z + 0.09), 0.003, 6)
        cil(bm, Vector((b.x - 0.012, b.y - 0.012, b.z + 0.09)), 0.006, 0.01, lados=8)
        obj(nome + '_antena', bm, 'cromo')
    return a, b


# ================================================================== pórtico do túnel
def topo_teto(y):
    return 0.47 if y <= -0.38 else 0.47 - (y + 0.38) * (0.40 / 0.86)


ALFA = math.atan(0.40 / 0.86)
PORTICOS = []


def portico(nome, c, rot, entrada=True):
    """Pórtico 1×1 com a boca no −y local (entrada: boca ao sul; saída: rot = π, boca ao norte)."""
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    raiz.location = c
    raiz.rotation_euler.z = rot
    mw = Matrix.Translation(c) @ Matrix.Rotation(rot, 4, 'Z')
    P = raiz
    # concreto: paredes laterais (descem até o fundo do poço), laje inclinada, verga de trás, soleira, fundo
    bm = bmesh.new()
    for sx in (-1, 1):
        prisma_yz(bm, [(-0.46, -0.62), (0.48, -0.62), (0.48, topo_teto(0.48)), (-0.38, 0.47), (-0.46, 0.47)],
                  sx * 0.355, sx * 0.40)
    prisma_yz(bm, [(-0.46, 0.40), (-0.38, 0.40), (0.48, topo_teto(0.48) - 0.07), (0.48, topo_teto(0.48)),
                   (-0.38, 0.47), (-0.46, 0.47)], -0.355, 0.355)
    caixa_de(bm, (-0.355, 0.44, -0.07), (0.355, 0.48, 0.0))
    caixa_de(bm, (-0.355, 0.44, -0.62), (0.355, 0.48, -0.57))
    caixa_de(bm, (-0.40, -0.46, -0.66), (0.40, 0.48, -0.62))
    caixa_de(bm, (-0.355, -0.48, -0.62), (0.355, -0.44, -0.004))
    concreto = obj(nome + '_concreto', bm, 'concreto', P)
    # moldura de aço da boca: colunas em I, verga em I com chapa listrada, chapas de base aparafusadas
    bm, bl, bp = bmesh.new(), bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        x0 = sx * 0.3775
        caixa(bm, (x0, -0.47, 0.20), (0.045, 0.008, 0.40))                      # aba de fora
        caixa(bm, (x0, -0.488, 0.20), (0.045, 0.008, 0.40))
        caixa(bm, (x0, -0.479, 0.20), (0.008, 0.018, 0.40))                     # alma
        caixa(bm, (x0, -0.475, 0.006), (0.07, 0.04, 0.012))                     # chapa de base
        for dz in (0.08, 0.16, 0.24, 0.32):
            for dx in (-0.015, 0.015):
                cil(bp, Vector((x0 + dx, -0.4935, dz)), 0.005, 0.004, -Y, lados=6)
    caixa(bm, (0, -0.47, 0.435), (0.84, 0.008, 0.07))
    caixa(bm, (0, -0.479, 0.435), (0.84, 0.018, 0.012))
    caixa(bm, (0, -0.479, 0.403), (0.84, 0.026, 0.008))
    caixa(bm, (0, -0.479, 0.467), (0.84, 0.026, 0.008))
    caixa(bl, (0, -0.4895, 0.435), (0.80, 0.003, 0.05))
    for x in (-0.39, -0.2, 0.0, 0.2, 0.39):
        cil(bp, Vector((x, -0.4935, 0.455)), 0.005, 0.004, -Y, lados=6)
    caixa(bm, (0, -0.44, 0.395), (0.70, 0.02, 0.012))                           # barra das lamelas
    moldura = obj(nome + '_moldura', bm, 'grafite', P)
    obj(nome + '_moldura_listras', bl, 'listras', P)
    obj(nome + '_parafusos', bp, 'aco', P)
    # lamelas de borracha (cada uma gira na barra de cima)
    lamelas = []
    n_l = 11
    for k in range(n_l):
        x = -0.35 + 0.7 * (k + 0.5) / n_l
        bm = bmesh.new()
        caixa(bm, (0, 0, -0.0875), (0.7 / n_l - 0.004, 0.006, 0.175))
        caixa(bm, (0, 0, -0.008), (0.7 / n_l - 0.004, 0.012, 0.016))             # dobra presa na barra
        if k == 8:                                                               # lamela rasgada, mais curta
            bm.free()
            bm = bmesh.new()
            caixa(bm, (0, 0, -0.06), (0.7 / n_l - 0.004, 0.006, 0.12))
            caixa(bm, (0.012, 0, -0.135), (0.7 / n_l - 0.03, 0.006, 0.03), Matrix.Rotation(0.25, 3, 'Y'))
            caixa(bm, (0, 0, -0.008), (0.7 / n_l - 0.004, 0.012, 0.016))
        lo = obj(nome + '_lamela', bm, 'lamela_cinza' if k == 3 else 'lamela', P)
        lo.location = (x, -0.44, 0.389)
        lo.rotation_mode = 'XYZ'
        lamelas.append(lo)
    # fotocélula da boca (emissor e receptor nas colunas, feixe vermelho)
    bm, bf = bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        caixa(bm, (sx * 0.347, -0.476, 0.272), (0.018, 0.026, 0.04))
        cil(bm, Vector((sx * 0.337, -0.476, 0.272)), 0.007, 0.004, X, lados=10)
    obj(nome + '_fotocelula', bm, 'amarelo', P)
    feixe_obj(nome + '_feixe', mw @ Vector((-0.335, -0.476, 0.272)), mw @ Vector((0.335, -0.476, 0.272)))
    # giroflex de status (verde parado, âmbar piscando quando a fotocélula vê item)
    def status(t, nome_=nome):
        q = int(round(t * FPS)) % QUADROS + 1
        cw = mw.inverted()
        visto = any(abs((cw @ p).y + 0.476) < 0.09 and abs((cw @ p).x) < 0.3 for p in POS_ITENS.get(q, []))
        if visto:
            pisca = 0.5 + 0.5 * math.cos(t * 2 * PI * 4)
            return (1.0, 0.42, 0.04), 4 + 10 * pisca
        return (0.15, 1.0, 0.2), 5.0
    mat_g = lampada(nome + '_giroflex', status)
    gx = 0.30
    bm = bmesh.new()
    cil(bm, Vector((gx, -0.465, 0.481)), 0.032, 0.022, lados=16)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        tubo(bm, (gx + 0.03 * math.cos(a), -0.465 + 0.03 * math.sin(a), 0.49), (gx + 0.03 * math.cos(a), -0.465 + 0.03 * math.sin(a), 0.545), 0.0025, 6)
    toro(bm, Vector((gx, -0.465, 0.545)), 0.03, 0.003, nR=20, nr=6)
    toro(bm, Vector((gx, -0.465, 0.515)), 0.03, 0.003, nR=20, nr=6)
    obj(nome + '_giroflex_base', bm, 'grafite', P)
    bm = bmesh.new()
    cil(bm, Vector((gx, -0.465, 0.513)), 0.022, 0.044, lados=16)
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.022, matrix=Matrix.Translation((gx, -0.465, 0.535)))
    obj(nome + '_giroflex', bm, mat_g, P)
    # caixa de controle selada no teto, eletrodutos para o giroflex, a fotocélula e o exaustor
    caixa_controle(nome + '_caixa', Vector(), (-0.33, -0.455, 0.47), (-0.17, -0.395, 0.56))
    for o_ in sc.objects:
        if o_.name.startswith(nome + '_caixa') and o_.parent is None:
            o_.parent = P
    bm, ba = bmesh.new(), bmesh.new()
    pts = [Vector((-0.17, -0.43, 0.49)), Vector((0.26, -0.43, 0.49)), Vector((0.268, -0.455, 0.49))]
    mangueira(bm, pts, 0.008)
    for x in (-0.05, 0.12):
        tubo(ba, (x - 0.008, -0.43, 0.49), (x + 0.008, -0.43, 0.49), 0.012, 10)
    for sx in (-1, 1):                                                           # descida pela coluna até a fotocélula
        x_d = sx * 0.405
        topo_d = Vector((x_d, -0.476, 0.47)) if sx < 0 else Vector((x_d, -0.476, 0.47))
        pts = [Vector((sx * 0.33 if sx < 0 else 0.26, -0.43, 0.49)), Vector((x_d, -0.43, 0.49)), Vector((x_d, -0.476, 0.47)),
               Vector((x_d, -0.476, 0.272)), Vector((sx * 0.356, -0.476, 0.272))]
        mangueira(bm, pts, 0.006)
        for z in (0.32, 0.4):
            tubo(ba, (x_d, -0.476, z - 0.007), (x_d, -0.476, z + 0.007), 0.01, 10)
    suavizar(obj(nome + '_eletrodutos', bm, 'grafite', P))
    obj(nome + '_abracadeiras', ba, 'aco', P)
    # tampa de inspeção aparafusada no teto inclinado, com olhais de içamento (para drone) e dobradiças
    rt = Matrix.Rotation(-ALFA, 3, 'X')
    cy = -0.12
    ct = Vector((-0.12, cy, topo_teto(cy)))
    bm = bmesh.new()
    caixa(bm, ct + rt @ Vector((0, 0, 0.006)), (0.30, 0.26, 0.012), rt)
    caixa(bm, ct + rt @ Vector((0, 0, 0.0135)), (0.26, 0.22, 0.004), rt)
    obj(nome + '_tampa', bm, 'amarelo', P)
    bm = bmesh.new()
    for k in range(12):
        u = k / 12
        if u < 0.25:
            q = Vector((-0.13 + 1.04 * u, -0.115, 0))
        elif u < 0.5:
            q = Vector((0.13, -0.115 + 0.92 * (u - 0.25), 0))
        elif u < 0.75:
            q = Vector((0.13 - 1.04 * (u - 0.5), 0.115, 0))
        else:
            q = Vector((-0.13, 0.115 - 0.92 * (u - 0.75), 0))
        cil(bm, ct + rt @ (q + Vector((0, 0, 0.0145))), 0.0065, 0.006, rt @ Z, lados=6)
    for sx in (-0.07, 0.07):
        toro(bm, ct + rt @ Vector((sx, 0.02, 0.03)), 0.014, 0.0035, rt @ Y, nR=14, nr=6)
        caixa(bm, ct + rt @ Vector((sx, 0.02, 0.016)), (0.03, 0.012, 0.008), rt)
    for sx in (-0.09, 0.09):
        cil(bm, ct + rt @ Vector((sx, -0.135, 0.012)), 0.009, 0.05, X, lados=10)
    obj(nome + '_tampa_ferragens', bm, 'aco', P)
    # exaustor no teto: duto embutido na laje, grade e hélice girando
    cf = Vector((0.20, -0.13, 0))
    zt = topo_teto(cf.y - 0.09) + 0.05
    bm = bmesh.new()
    cil(bm, Vector((cf.x, cf.y, (topo_teto(cf.y + 0.09) - 0.04 + zt) / 2)), 0.085, zt - topo_teto(cf.y + 0.09) + 0.04, lados=24)
    obj(nome + '_exaustor', bm, 'grafite', P)
    bm = bmesh.new()
    toro(bm, Vector((cf.x, cf.y, zt)), 0.083, 0.005, nR=24, nr=6)
    for k in range(-3, 4):
        tubo(bm, (cf.x + k * 0.022, cf.y - math.sqrt(max(0, 0.083 ** 2 - (k * 0.022) ** 2)), zt + 0.004),
             (cf.x + k * 0.022, cf.y + math.sqrt(max(0, 0.083 ** 2 - (k * 0.022) ** 2)), zt + 0.004), 0.0025, 6)
    obj(nome + '_grade', bm, 'aco', P)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.018, 0.02, lados=10)
    for k in range(5):
        rot = Matrix.Rotation(k * 2 * PI / 5, 3, 'Z') @ Matrix.Rotation(0.5, 3, 'X')
        caixa(bm, rot @ Vector((0, 0.045, 0)), (0.03, 0.055, 0.004), rot)
    he = obj(nome + '_helice', bm, 'aco', P)
    he.location = (cf.x, cf.y, zt - 0.025)
    girar(he, 2 * PI * 12, idx=2)
    # luz interna (luminária com grade presa na laje) — ilumina a rampa vista pela boca
    bm = bmesh.new()
    zl = topo_teto(-0.28) - 0.07
    caixa(bm, (0, -0.28, zl - 0.012), (0.16, 0.05, 0.024))
    obj(nome + '_luminaria', bm, 'grafite', P)
    bm = bmesh.new()
    cil(bm, Vector((0, -0.28, zl - 0.03)), 0.012, 0.13, X, lados=10)
    obj(nome + '_lampada', bm, 'luz_int', P)
    ld = bpy.data.lights.new(nome + '_luz', 'POINT')
    ld.energy = 6.0
    ld.color = (1.0, 0.75, 0.5)
    ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(nome + '_luz', ld)
    sc.collection.objects.link(lo)
    lo.parent = P
    lo.location = (0, -0.26, zl - 0.06)
    # escorridos de umidade/fuligem no concreto e lama na soleira
    bm = bmesh.new()
    for sx in (-1, 1):
        for k in range(4):
            y = random.uniform(-0.35, 0.3)
            zt_ = topo_teto(y)
            caixa(bm, (sx * 0.4015, y, zt_ - 0.09), (0.002, 0.012, 0.16))
    obj(nome + '_escorridos', bm, 'oleo', P)
    # ---- desgaste: lascas no concreto, amassados na moldura, remendos, ferrugem, fuligem, fios, estêncil
    amassar(concreto, [(mw @ Vector((sx * 0.40, -0.46, 0.47)), 0.06, 0.025) for sx in (-1, 1)] +
            [(mw @ Vector((0.2, -0.46, 0.47)), 0.05, 0.02), (mw @ Vector((-0.40, 0.1, topo_teto(0.1))), 0.07, 0.03)], cortes=5)
    amassar(moldura, [(mw @ Vector((-0.12, -0.49, 0.44)), 0.05, 0.008), (mw @ Vector((0.3775, -0.49, 0.12)), 0.05, 0.01)], cortes=14)
    bm, bp, bf_, bs = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    remendo(bm, bp, (-0.3775, -0.492, 0.16), -Y, 0.05, 0.10, 0.05)
    remendo(bm, bp, (0.05, 0.25, topo_teto(0.25) - 0.004), rt @ Z, 0.16, 0.12, -0.12)
    obj(nome + '_remendos', bm, 'primer', P)
    obj(nome + '_remendos_paraf', bp, 'aco', P)
    for x in (-0.39, -0.2, 0.0, 0.2, 0.39):
        escorrido(bf_, (x, -0.4935, 0.45), -Y, random.uniform(0.03, 0.06), 0.008)
    for sx in (-1, 1):
        for dz in (0.24, 0.32):
            escorrido(bf_, (sx * 0.3775 + 0.015, -0.4935, dz), -Y, random.uniform(0.04, 0.09), 0.007)
    obj(nome + '_ferrugem', bf_, 'ferrugem', P)
    mancha(bs, (0, 0), 0.13, 0.0)                                                 # fuligem em volta do exaustor
    for k in range(3):
        a_ = random.uniform(-0.5, 0.5)
        caixa(bs, (0.09 * math.sin(a_), 0.11 + 0.05 * k, 0), (0.03 - 0.008 * k, 0.07, 0.0005))
    bmesh.ops.transform(bs, verts=bs.verts[:], matrix=Matrix.Translation((cf.x, cf.y, topo_teto(cf.y) + 0.002)) @ rt.to_4x4())
    obj(nome + '_fuligem', bs, 'fuligem', P)
    bc, bcu = bmesh.new(), bmesh.new()
    fio_exposto(bc, bcu, [Vector((-0.20, -0.44, 0.50)), Vector((-0.15, -0.475, 0.49)), Vector((-0.14, -0.497, 0.455)), Vector((-0.135, -0.50, 0.40))], 0.0035)
    fio_exposto(bc, bcu, [Vector((-0.21, -0.44, 0.50)), Vector((-0.17, -0.48, 0.49)), Vector((-0.17, -0.499, 0.43))], 0.003)
    suavizar(obj(nome + '_fios', bc, 'laranja', P))
    obj(nome + '_fios_cobre', bcu, 'cobre', P)
    serie('TN-0091', ct + rt @ Vector((0.0, 0.045, 0.016)), rt @ Z, rt @ -Y, 0.032, P)
    serie('IA·7 0091', Vector((-0.25, -0.4552, 0.515)), -Y, Z, 0.018, P)
    serie('Nº 44-1', Vector((0.3775, -0.4935, 0.36)), -Y, Z, 0.012, P)
    PORTICOS.append({'nome': nome, 'lamelas': lamelas, 'mw': mw, 'entrada': entrada})
    return raiz


def animar_lamelas():
    for pt in PORTICOS:
        cw = pt['mw'].inverted()
        sinal = 1.0 if pt['entrada'] else -1.0                 # entrada: item vai para +y local; saída: para −y
        for lo in pt['lamelas']:
            xl = lo.location.x
            for q in range(1, QUADROS + 1):
                ang_ = 0.0
                for p in POS_ITENS[q]:
                    pl = cw @ p
                    if abs(pl.x - xl) > 0.11:
                        continue
                    d = (pl.y - (-0.44)) * sinal                    # quanto o centro do item passou da cortina
                    if -0.09 < d < 0.16:
                        a = math.asin(min(1.0, max(0.0, (d + 0.09)) / 0.19)) * 0.9
                        a *= 1.0 - suave((d - 0.06) / 0.10)
                        ang_ = max(ang_, a)
                lo.rotation_euler.x = ang_ * sinal
                lo.keyframe_insert('rotation_euler', index=0, frame=q)


def terra_tunel(x0, y_ent, y_sai):
    """Terra amontoada nas laterais e por cima dos pórticos e uma faixa de terra revolvida sobre o túnel."""
    nx, ny = 34, int((y_sai - y_ent + 1.0) / 0.03)
    def h(x, y):
        best = None
        for yc, sg in ((y_ent, 1), (y_sai, -1)):
            yl = (y - yc) * sg
            xl = abs(x - x0)
            if abs(yl) <= 0.5:
                if xl <= 0.40 and yl <= 0.48:
                    if yl >= 0.05:
                        t = 0.05 * math.sin(PI * min(1.0, (yl - 0.05) / 0.45)) + 0.006
                        v = topo_teto(yl) + t
                    else:
                        return None
                elif xl <= 0.40:
                    v = 0.07 + 0.01
                else:
                    tp = topo_teto(max(-0.46, min(0.48, yl))) * 0.5 + 0.03
                    v = tp * (1 - ((xl - 0.40) / 0.10)) ** 1.1
                    if yl < -0.44:
                        v *= max(0.0, 1 - (-0.44 - yl) / 0.06)
                best = v if best is None else max(best, v)
        if best is None:
            if y_ent + 0.5 < y < y_sai - 0.5:
                xl = abs(x - x0)
                best = 0.075 * max(0.0, 1 - (xl / 0.5) ** 2)
            else:
                return None
        return (best + 0.022 * noise.noise(Vector((x * 3.5, y * 3.5, 0.3))) + 0.008 * noise.noise(Vector((x * 11, y * 11, 1.7)))
                + 0.003 * noise.noise(Vector((x * 35, y * 35, 4.1))) + 0.012)
    bm = bmesh.new()
    grade = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = x0 - 0.5 + i / nx
            y = y_ent - 0.5 + j * (y_sai - y_ent + 1.0) / ny
            v = h(x, y)
            if v is not None:
                grade[i, j] = bm.verts.new((x, y, max(0.002, v)))
    for i in range(nx):
        for j in range(ny):
            vs = [grade.get(k) for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            if all(vs):
                bm.faces.new(vs)
    o = obj('terra', bm, 'terra')
    for pg in o.data.polygons:
        pg.use_smooth = True
    bm = bmesh.new()                                                             # torrões e pedras na terra
    for k in range(70):
        x = x0 + random.uniform(-0.48, 0.48)
        y = random.uniform(y_ent - 0.1, y_sai + 0.1)
        v = h(x, y)
        if v is None:
            continue
        pedra(bm, Vector((x, y, v)), random.uniform(0.008, 0.022), 0.6)
    obj('pedras_terra', bm, 'cascalho')
    bm = bmesh.new()                                                             # torrões de terra
    for k in range(90):
        x = x0 + random.uniform(-0.49, 0.49)
        y = random.uniform(y_ent - 0.2, y_sai + 0.2)
        v = h(x, y)
        if v is None:
            continue
        pedra(bm, Vector((x, y, v - 0.004)), random.uniform(0.015, 0.04), 0.45)
    o = obj('torroes', bm, 'terra')
    for pg in o.data.polygons:
        pg.use_smooth = True
    bm, bl = bmesh.new(), bmesh.new()                                            # marcos de concreto sobre o túnel
    for sx, yy in ((-0.42, (y_ent + y_sai) / 2 - 0.4), (0.42, (y_ent + y_sai) / 2 + 0.4)):
        caixa(bm, (x0 + sx, yy, 0.09), (0.05, 0.05, 0.18))
        caixa(bl, (x0 + sx, yy, 0.165), (0.052, 0.052, 0.03))
    obj('marcos', bm, 'concreto')
    obj('marcos_listras', bl, 'listras')


def tunel(nome, x0, y_ent, y_sai):
    """Pórtico de entrada em (x0, y_ent), saída em (x0, y_sai). Rampas internas e esteira subterrânea."""
    portico(nome + '_entrada', Vector((x0, y_ent, 0)), 0.0, True)
    portico(nome + '_saida', Vector((x0, y_sai, 0)), PI, False)
    zf = H - 0.45
    r1 = esteira(nome + '_rampa_desce', caminho_seg((x0, y_ent - 0.5, H), (x0, y_ent + 0.40, zf)), motor=False, pernas=False)
    sub = esteira(nome + '_subterranea', caminho_seg((x0, y_ent + 0.40, zf), (x0, y_sai - 0.40, zf)), motor=False, pernas=False)
    r2 = esteira(nome + '_rampa_sobe', caminho_seg((x0, y_sai - 0.40, zf), (x0, y_sai + 0.5, H)), motor=False, pernas=False)
    ponte(ponta(r1, 'fim'), ponta(sub, 'ini'))
    ponte(ponta(sub, 'fim'), ponta(r2, 'ini'))
    terra_tunel(x0, y_ent, y_sai)
    cortes = [((x0 - 0.40, y_ent - 0.48, -0.66), (x0 + 0.40, y_ent + 0.48, 0.05)),
              ((x0 - 0.40, y_sai - 0.48, -0.66), (x0 + 0.40, y_sai + 0.48, 0.05)),
              ((x0 - 0.355, y_ent + 0.40, -0.60), (x0 + 0.355, y_sai - 0.40, -0.07))]
    return {'rampa1': r1, 'sub': sub, 'rampa2': r2, 'cortes': cortes}


# ================================================================== divisor
FORK_Y = 0.035            # centro do item parado no divisor
DIVISORES = []


def divisor(nome, o):
    P = lambda x, y, z: o + Vector((x, y, z))
    rolos = mesa_cruz(nome, o, {'S': Y, 'N': Y, 'L': X, 'O': -X})
    # roletes do centro (levam para o norte); o 7º e o 8º deixam a fresta do batente
    bm = bmesh.new()
    centro = []
    for k in range(10):
        y = -0.27 + 0.06 * k
        centro.append(rolete(nome + '_rolo_c', P(0, y, Z_ROL), Y, 0.58, mat='rolo_novo' if k == 3 else 'rolo')[0])
    for a_, b_ in zip(centro, centro[1:]):
        anel_o(bm, a_.location, b_.location, -X, -0.255)
    anel_o(bm, centro[-1].location, rolos['N'][0].location, -X, -0.255)
    anel_o(bm, rolos['S'][0].location, centro[0].location, -X, -0.255)
    suavizar(obj(nome + '_aneis_c', bm, 'borracha'))
    # rolete motorizado no braço N com catraca fora da lateral oeste + motorredutor e corrente
    rolos['N'][1].hide_render = True
    rolos['N'][1].hide_viewport = True
    rm, e = rolete(nome + '_rolo_motor', rolos['N'][1].location.copy(), Y, 0.60, roda=(1, 0.055, 0.03))
    pin, giro = motor_rolos(nome, o, -0.355, 0.405, -1, 1)
    sprk = P(-0.355, 0.405, Z_ROL)
    bm = bmesh.new()
    roda_mesh(bm, 0.02, 8, 0.012)
    girante(nome + '_pinhao', bm, 'cromo', pin, -X, giro * 0.03 / 0.02)
    c = corrente(nome + '_corr', (pin, 0.02 * 0.95, sprk, 0.03 * 0.95, -X), None)
    animar_corrente(c, giro * 0.03 * 0.95)
    # pórtico: 4 colunas, travessas, viga do atuador linear (carro com garfo), calha da porta-cabos
    bm, ba = bmesh.new(), bmesh.new()
    bz = bmesh.new()                                                              # coluna NE trocada: zarcão
    for sx in (-1, 1):
        for sy in (-1, 1):
            caixa_de(bz if (sx, sy) == (1, 1) else bm, P(sx * 0.45 - 0.02, sy * 0.45 - 0.02, 0.0), P(sx * 0.45 + 0.02, sy * 0.45 + 0.02, 0.534))
            caixa_de(ba, P(sx * 0.45 - 0.04, sy * 0.45 - 0.04, 0.0), P(sx * 0.45 + 0.04, sy * 0.45 + 0.04, 0.014))
        caixa_de(bm, P(sx * 0.45 - 0.02, -0.47, 0.535), P(sx * 0.45 + 0.02, 0.47, 0.575))
    caixa_de(bm, P(-0.47, -0.47, 0.535), P(0.47, -0.43, 0.575))                  # travessa sul (leva o olho)
    pg = obj(nome + '_portico', bm, 'amarelo')
    pz = obj(nome + '_coluna_zarcao', bz, 'zarcao')
    obj(nome + '_sapatas', ba, 'grafite')
    amassar(pg, [(P(-0.47, -0.45, 0.30), 0.045, 0.008), (P(0.1, -0.47, 0.555), 0.05, 0.007), (P(0.45, -0.3, 0.575), 0.05, 0.008),
                 (P(-0.45, 0.47, 0.18), 0.04, 0.007)], cortes=12)
    amassar(pz, [(P(0.47, 0.45, 0.22), 0.04, 0.008)], cortes=12)
    bm, bc = bmesh.new(), bmesh.new()
    caixa_de(bm, P(-0.43, 0.075, 0.53), P(0.43, 0.125, 0.575))                     # perfil do atuador
    for sx in (-1, 1):
        caixa_de(bc, P(sx * 0.43 - (0.02 if sx > 0 else 0), 0.07, 0.522), P(sx * 0.43 + (0.02 if sx < 0 else 0), 0.13, 0.583))
    caixa_de(bm, P(-0.43, 0.14, 0.565), P(0.43, 0.185, 0.57))                       # calha da porta-cabos
    caixa_de(bm, P(-0.43, 0.14, 0.57), P(0.43, 0.143, 0.585))
    caixa_de(bm, P(-0.43, 0.182, 0.57), P(0.43, 0.185, 0.585))
    obj(nome + '_atuador', bm, 'aco')
    obj(nome + '_atuador_tampas', bc, 'grafite')
    # carro, garfo e pistões verticais (camisa no garfo, haste na palheta)
    carro = bpy.data.objects.new(nome + '_carro', None)
    sc.collection.objects.link(carro)
    carro.location = P(0, 0, 0)
    bm = bmesh.new()
    caixa_de(bm, (-0.045, 0.065, 0.52), (0.045, 0.135, 0.59))
    caixa_de(bm, (-0.16, 0.0, 0.565), (0.16, 0.07, 0.58))
    caixa_de(bm, (-0.012, 0.135, 0.59), (0.012, 0.165, 0.60))                     # orelha da porta-cabos
    obj(nome + '_carro_corpo', bm, 'amarelo', carro)
    bm = bmesh.new()
    for sx in (-1, 1):
        cil(bm, Vector((sx * 0.13, FORK_Y, 0.495)), 0.018, 0.14, lados=16)
        cil(bm, Vector((sx * 0.13, FORK_Y, 0.428)), 0.021, 0.008, lados=16)
        cil(bm, Vector((sx * 0.13, FORK_Y, 0.56)), 0.021, 0.008, lados=16)
        cil(bm, Vector((sx * 0.13 + 0.02, FORK_Y, 0.55)), 0.005, 0.012, X, lados=8)   # conexões de ar
        cil(bm, Vector((sx * 0.13 + 0.02, FORK_Y, 0.44)), 0.005, 0.012, X, lados=8)
    suavizar(obj(nome + '_camisas', bm, 'grafite', carro))
    bm = bmesh.new()
    for sx in (-1, 1):
        escorrido(bm, Vector((sx * 0.13, FORK_Y - 0.0185, 0.47)), -Y, 0.04, 0.008)
    obj(nome + '_oleo_camisas', bm, 'oleo', carro)
    bm = bmesh.new()
    for sx in (-1, 1):
        mangueira(bm, bezier(Vector((sx * 0.13 + 0.026, FORK_Y, 0.55)), Vector((sx * 0.13 + 0.05, FORK_Y, 0.55)),
                             Vector((sx * 0.05, 0.08, 0.6)), Vector((0, 0.15, 0.6)), 6), 0.004)
        mangueira(bm, bezier(Vector((sx * 0.13 + 0.026, FORK_Y, 0.44)), Vector((sx * 0.13 + 0.06, FORK_Y, 0.44)),
                             Vector((sx * 0.06, 0.09, 0.59)), Vector((0, 0.15, 0.6)), 6), 0.004)
    suavizar(obj(nome + '_mangueiras_carro', bm, 'borracha', carro))
    palhetas = []
    for sx in (-1, 1):
        pa = bpy.data.objects.new(nome + '_palheta', None)
        sc.collection.objects.link(pa)
        pa.parent = carro
        pa.location = (sx * 0.13, FORK_Y, 0.0)
        bm = bmesh.new()
        caixa_de(bm, (-0.008, -0.10, 0.36), (0.008, 0.10, 0.43))
        caixa_de(bm, (-0.012, -0.02, 0.415), (0.012, 0.02, 0.43))
        obj(nome + '_palheta_aco', bm, 'aco', pa)
        bm = bmesh.new()
        caixa_de(bm, (-sx * 0.008 - 0.004, -0.098, 0.362), (-sx * 0.008 + 0.004, 0.098, 0.428))
        obj(nome + '_palheta_borracha', bm, 'borracha', pa)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.50)), 0.008, 0.14, lados=10)
        suavizar(obj(nome + '_haste', bm, 'cromo', pa))
        palhetas.append(pa)
    # esteira porta-cabos (elos animados) na calha ao norte da viga
    elos_pc = []
    for k in range(32):
        bm = bmesh.new()
        caixa(bm, Vector(), (0.022, 0.034, 0.012))
        caixa(bm, Vector((0, -0.016, 0)), (0.018, 0.003, 0.016))
        caixa(bm, Vector((0, 0.016, 0)), (0.018, 0.003, 0.016))
        oo = obj(nome + '_porta_cabos', bm, 'grafite')
        oo.rotation_mode = 'XYZ'
        elos_pc.append(oo)
    # batente que sobe entre o 7º e o 8º rolete (para o item no centro), com pistão embaixo
    bat = bpy.data.objects.new(nome + '_batente', None)
    sc.collection.objects.link(bat)
    bat.location = P(0, 0.12, 0)
    bm = bmesh.new()
    caixa_de(bm, (-0.20, -0.004, 0.14), (0.20, 0.004, 0.20))
    obj(nome + '_batente_lamina', bm, 'amarelo', bat)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.14 - 0.065)), 0.007, 0.13, lados=10)
    caixa_de(bm, (-0.02, -0.006, 0.13), (0.02, 0.006, 0.145))
    obj(nome + '_batente_haste', bm, 'cromo', bat)
    bm = bmesh.new()
    cil(bm, P(0, 0.12, 0.058), 0.02, 0.09, lados=14)
    caixa_de(bm, P(-0.04, 0.09, 0.0), P(0.04, 0.15, 0.012))
    cil(bm, P(0.025, 0.12, 0.03), 0.005, 0.014, X, lados=8)
    suavizar(obj(nome + '_batente_camisa', bm, 'grafite'))
    # fotocélula de entrada (sobre as laterais do braço sul) e olho do filtro (violeta) na travessa sul
    bm = bmesh.new()
    for sx in (-1, 1):
        caixa(bm, P(sx * 0.333, -0.46, 0.24), (0.024, 0.03, 0.05))
        cil(bm, P(sx * 0.32, -0.46, 0.245), 0.007, 0.004, X, lados=10)
    obj(nome + '_fotocelula', bm, 'amarelo')
    feixe_obj(nome + '_feixe', P(-0.318, -0.46, 0.245), P(0.318, -0.46, 0.245))
    bm = bmesh.new()
    caixa_de(bm, P(-0.05, -0.475, 0.47), P(0.05, -0.425, 0.535))
    cil(bm, P(0, -0.42, 0.495), 0.026, 0.02, Vector((0, 1, -0.6)), lados=18)
    obj(nome + '_olho_corpo', bm, 'grafite')
    bm = bmesh.new()
    cil(bm, P(0, -0.411, 0.489), 0.017, 0.006, Vector((0, 1, -0.6)), lados=18)
    obj(nome + '_olho', bm, 'olho')
    # caixa de controle (no pé NE), bloco de válvulas (no pé NO), eletrocalha e cabos, mangueiras
    caixa_controle(nome + '_controle', o, (0.355, 0.355, 0.20), (0.43, 0.47, 0.40))
    bm = bmesh.new()
    caixa_de(bm, P(-0.428, 0.36, 0.42), P(-0.36, 0.44, 0.50))
    obj(nome + '_valvulas', bm, 'amarelo')
    bm = bmesh.new()
    for k in range(3):
        cil(bm, P(-0.394 + (k - 1) * 0.02, 0.36, 0.48), 0.007, 0.03, Y, lados=8)
        cil(bm, P(-0.394 + (k - 1) * 0.02, 0.4, 0.51), 0.008, 0.02, lados=8)
    obj(nome + '_valvulas_bobinas', bm, 'grafite')
    bm, bc, ba = bmesh.new(), bmesh.new(), bmesh.new()
    caixa_de(bm, P(-0.47, 0.475, 0.0), P(0.47, 0.5, 0.02))                        # eletrocalha no chão (norte)
    caixa_de(bm, P(0.475, -0.47, 0.0), P(0.5, 0.5, 0.02))                         # eletrocalha (leste)
    obj(nome + '_eletrocalha', bm, 'aco')
    for k in range(3):
        mangueira(bc, [P(-0.44, 0.482 + k * 0.006, 0.012), P(0.44, 0.482 + k * 0.006, 0.012)], 0.004)
        mangueira(bc, [P(0.482 + k * 0.006, -0.45, 0.012), P(0.482 + k * 0.006, 0.47, 0.012)], 0.004)
    feixe(bc, ba, bezier(P(0.39, 0.42, 0.2), P(0.39, 0.42, 0.06), P(0.39, 0.48, 0.03), P(0.30, 0.488, 0.015), 8), n=3, r=0.004, lado=X)
    feixe(bc, ba, bezier(P(-0.39, 0.40, 0.42), P(-0.39, 0.46, 0.25), P(-0.40, 0.49, 0.05), P(-0.34, 0.488, 0.015), 8), n=2, r=0.004, lado=X)
    feixe(bc, ba, bezier(P(-0.40, 0.40, 0.045), P(-0.40, 0.46, 0.03), P(-0.38, 0.488, 0.02), P(-0.30, 0.488, 0.015), 6), n=2, r=0.004, lado=X)
    feixe(bc, ba, bezier(P(0.488, -0.44, 0.015), P(0.46, -0.46, 0.05), P(0.36, -0.46, 0.15), P(0.345, -0.46, 0.22), 8), n=1, r=0.004)
    feixe(bc, ba, bezier(P(0.47, -0.45, 0.30), P(0.47, -0.45, 0.45), P(0.3, -0.45, 0.58), P(0.04, -0.45, 0.576), 8), n=2, r=0.004, lado=Y)
    feixe(bc, ba, bezier(P(0.41, 0.36, 0.26), P(0.41, 0.25, 0.26), P(0.38, 0.0, 0.15), P(0.47, -0.2, 0.015), 8), n=1, r=0.004)
    mangueira(bc, bezier(P(-0.405, 0.36, 0.48), P(-0.40, 0.25, 0.48), P(-0.43, 0.12, 0.555), P(-0.43, 0.10, 0.555), 8), 0.005)
    mangueira(bc, bezier(P(-0.36, 0.40, 0.47), P(-0.30, 0.20, 0.6), P(-0.43, 0.165, 0.58), P(-0.40, 0.162, 0.585), 8), 0.005)
    mangueira(bc, bezier(P(-0.38, 0.36, 0.43), P(-0.38, 0.30, 0.2), P(-0.1, 0.12, 0.03), P(0.03, 0.12, 0.03), 10), 0.004)
    suavizar(obj(nome + '_cabos', bc, 'borracha'))
    obj(nome + '_abracadeiras', ba, 'aco')
    bm = bmesh.new()
    mangueira(bm, bezier(P(0.43, 0.10, 0.555), P(0.45, 0.10, 0.5), P(0.45, 0.2, 0.62), P(0.43, 0.162, 0.585), 6), 0.005)
    suavizar(obj(nome + '_mangueira_l', bm, 'laranja'))
    # sujeira: farelo de minério e pó embaixo da mesa
    bm = bmesh.new()
    for k in range(30):
        pedra(bm, P(random.uniform(-0.45, 0.45), random.uniform(-0.45, 0.45), 0.004), random.uniform(0.005, 0.013), 0.5)
    obj(nome + '_farelo', bm, 'minerio')
    bm = bmesh.new()
    for k in range(5):
        mancha(bm, (o.x + random.uniform(-0.3, 0.3), o.y + random.uniform(-0.3, 0.3)), random.uniform(0.05, 0.11), 0.0012)
    obj(nome + '_po', bm, 'oleo')
    # ---- desgaste: remendos, ferrugem, óleo, fios expostos, estêncil, pó de minério e lama
    bm, bp, bf_, bo, bl_ = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    remendo(bm, bp, P(-0.45, -0.471, 0.25), -Y, 0.034, 0.09, 0.04)
    remendo(bm, bp, P(-0.2, -0.471, 0.555), -Y, 0.11, 0.034, -0.03)
    remendo(bm, bp, P(0.471, 0.0, 0.555), X, 0.14, 0.034, 0.02)
    obj(nome + '_remendos', bm, 'aco')
    obj(nome + '_remendos_paraf', bp, 'grafite')
    for x_ in (-0.24, -0.16):
        escorrido(bf_, P(x_, -0.4715, 0.571), -Y, 0.034, 0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            escorrido(bf_, P(sx * 0.45, sy * 0.45 - sy * 0.0205, 0.53), Vector((0, -sy, 0)), random.uniform(0.08, 0.2), 0.012)
    escorrido(bf_, P(0.471, 0.06, 0.572), X, 0.035, 0.01)
    obj(nome + '_ferrugem', bf_, 'ferrugem')
    escorrido(bo, P(0.0, 0.0995, 0.10), -Y, 0.07, 0.01)                          # óleo do pistão do batente
    escorrido(bo, P(-0.36, 0.40, 0.42), -X, 0.1, 0.012)                         # óleo do bloco de válvulas
    for c_, r_ in ((P(0.0, 0.12, 0), 0.05), (P(-0.39, 0.40, 0), 0.06), (P(-0.43, 0.39, 0), 0.04)):
        mancha(bo, (c_.x, c_.y), r_, 0.0016)
    obj(nome + '_oleo2', bo, 'oleo')
    for sx in (-1, 1):                                                           # lama em volta dos pés
        for sy in (-1, 1):
            mancha(bl_, (o.x + sx * 0.4, o.y + sy * 0.4), random.uniform(0.06, 0.1), 0.0013)
    obj(nome + '_lama', bl_, 'lama')
    bc, bcu = bmesh.new(), bmesh.new()
    fio_exposto(bc, bcu, [P(0.37, 0.40, 0.20), P(0.36, 0.38, 0.13), P(0.35, 0.39, 0.08), P(0.355, 0.42, 0.05)], 0.0035)
    fio_exposto(bc, bcu, [P(0.40, 0.40, 0.20), P(0.40, 0.37, 0.15), P(0.39, 0.36, 0.12)], 0.003)
    suavizar(obj(nome + '_fios', bc, 'laranja'))
    obj(nome + '_fios_cobre', bcu, 'cobre')
    bm = bmesh.new()
    montinhos(bm, [P(sx * 0.33, sy * 0.33, 0.216) for sx in (-1, 1) for sy in (-1, 1)] +
              [P(sx * 0.33, sy * 0.45, 0.216) for sx in (-1, 1) for sy in (-1, 1)] +
              [P(sx * 0.45, -0.45, 0.576) for sx in (-1, 1)] + [P(0.0, -0.45, 0.576), P(0.3, 0.1, 0.576)], n=5)
    montinhos(bm, [P(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0.0) for k in range(6)], n=8, r=(0.006, 0.016))
    obj(nome + '_po_minerio', bm, 'po_minerio')
    serie('DV-0417', P(0.22, -0.4705, 0.555), -Y, Z, 0.022)
    serie('C17', P(0.392, 0.354, 0.33), -Y, Z, 0.022)
    serie('03', P(-0.45, -0.4705, 0.42), -Y, Z, 0.028)
    d = {'o': o, 'carro': carro, 'palhetas': palhetas, 'batente': bat, 'elos_pc': elos_pc, 'eventos': []}
    DIVISORES.append(d)
    return d


def animar_divisor(d):
    o = d['o']
    for q in range(1, QUADROS + 1):
        t = (q - 1) / FPS
        xc, baixa, bat = 0.0, 0.0, 0.0
        for t_a, sx in d['eventos']:
            xc += sx * 0.26 * janela(t, t_a + 0.2, t_a + 0.8, 0.45, 0.35)
            baixa = max(baixa, janela(t, t_a, t_a + 0.65, 0.18, 0.15))
            bat = max(bat, janela(t, t_a - 0.55, t_a + 0.3, 0.15, 0.15))
        d['carro'].location = o + Vector((xc, 0, 0))
        d['carro'].keyframe_insert('location', frame=q)
        for pa in d['palhetas']:
            pa.location.z = -0.135 * baixa
            pa.keyframe_insert('location', index=2, frame=q)
        d['batente'].location.z = 0.05 * bat
        d['batente'].keyframe_insert('location', index=2, frame=q)
        # porta-cabos: ponta fixa em x = −0.43 (baixo), curva de raio r, ponta móvel no carro (em cima)
        r_c, Lc, xf = 0.012, 0.80, -0.43
        xb = (Lc - PI * r_c + xf + xc) / 2
        zb, yb = 0.5815, 0.1625
        n = len(d['elos_pc'])
        for k, oo in enumerate(d['elos_pc']):
            s = (k + 0.5) * Lc / n
            if s < xb - xf:
                p, a = Vector((xf + s, yb, zb)), 0.0
            elif s < xb - xf + PI * r_c:
                th = (s - (xb - xf)) / r_c
                p, a = Vector((xb + r_c * math.sin(th), yb, zb + r_c - r_c * math.cos(th))), -th
            else:
                s2 = s - (xb - xf) - PI * r_c
                p, a = Vector((xb - s2, yb, zb + 2 * r_c)), -PI
            oo.location = o + p
            oo.rotation_euler = (0, -a, 0)
            oo.keyframe_insert('location', frame=q)
            oo.keyframe_insert('rotation_euler', frame=q)


def rota_divisor(r, d, saida, saidas):
    """Do sul do divisor até a esteira de saída. saidas: dict 'N'/'L'/'O' → esteira."""
    o = d['o']
    P = lambda x, y: o + Vector((x, y, ZI))
    if saida == 'N':
        r.linha(P(0, 0.5))
    else:
        sx = 1 if saida == 'L' else -1
        r.linha(P(0, FORK_Y))
        d['eventos'].append((r.agora(), sx))
        r.pausa(0.2)
        r.empurra(P(sx * 0.26, 0.0), 0.45)
        r.pausa(0.15)
        r.linha(P(sx * 0.5, 0.0))
    r.esteira(saidas[saida])


# ================================================================== junção
JUNCOES = []


def juncao(nome, o):
    P = lambda x, y, z: o + Vector((x, y, z))
    mesa_cruz(nome, o, {'S': Y, 'N': Y, 'L': -X, 'O': X}, centro_v=False)
    # roletes convergentes em V no centro (metade oeste empurra para NE, metade leste para NO)
    bm = bmesh.new()
    for sx in (-1, 1):
        v = Vector((-sx * 0.5, 0.866, 0))
        e = Z.cross(v).normalized()
        lista = []
        for k in range(9):
            y = -0.24 + 0.06 * k
            lista.append(rolete(nome + '_rolo_v', P(sx * 0.15, y, Z_ROL), v, 0.24, mat='rolo_novo' if (sx, k) == (1, 5) else 'rolo')[0])
        for a_, b_ in zip(lista, lista[1:]):
            anel_o(bm, a_.location, b_.location, e, 0.085)
    suavizar(obj(nome + '_aneis_v', bm, 'borracha'))
    bm = bmesh.new()                                                             # trilhos baixos dos roletes em V
    for x in (-0.275, -0.025, 0.025, 0.275):
        caixa_de(bm, P(x - 0.007, -0.30, 0.125), P(x + 0.007, 0.30, 0.175))
    for sy in (-1, 1):
        caixa_de(bm, P(-0.33, sy * 0.30 - 0.015, 0.098), P(0.33, sy * 0.30 + 0.015, 0.125))
    obj(nome + '_trilhos_v', bm, 'grafite')
    # motor + corrente no braço sul (catraca fora da lateral oeste)
    # (o rolete do meio do braço sul vira rolete com catraca)
    alvo = None
    for ob in list(sc.objects):
        if ob.name.startswith(nome + '_rolo_S') and abs(ob.location.y - (o.y - 0.405)) < 1e-3:
            alvo = ob
    alvo.hide_render = True
    alvo.hide_viewport = True
    rolete(nome + '_rolo_motor', alvo.location.copy(), Y, 0.60, roda=(1, 0.055, 0.03))
    pin, giro = motor_rolos(nome, o, -0.355, -0.405, -1, -1)
    sprk = P(-0.355, -0.405, Z_ROL)
    bm = bmesh.new()
    roda_mesh(bm, 0.02, 8, 0.012)
    girante(nome + '_pinhao', bm, 'cromo', pin, -X, giro * 0.03 / 0.02)
    c = corrente(nome + '_corr', (pin, 0.02 * 0.95, sprk, 0.03 * 0.95, -X), None)
    animar_corrente(c, giro * 0.03 * 0.95)
    # comportas de prioridade nas entradas L e O: duas colunas com trilho-guia, travessa, lâmina guilhotina
    # que desce na fresta entre roletes, dois pistões (camisa na coluna, haste na orelha da lâmina)
    comportas = {}
    for lado, sx in (('L', 1), ('O', -1)):
        xg = sx * 0.375
        bm, bp = bmesh.new(), bmesh.new()
        for sy in (-1, 1):
            caixa_de(bm, P(xg - 0.0175, sy * 0.37 - 0.02, 0.0), P(xg + 0.0175, sy * 0.37 + 0.02, 0.56))
            caixa_de(bm, P(xg - 0.028, min(sy * 0.355, sy * 0.43), 0.0), P(xg + 0.028, max(sy * 0.355, sy * 0.43), 0.012))
        bt = bmesh.new()
        caixa_de(bt if lado == 'O' else bm, P(xg - 0.02, -0.39, 0.52), P(xg + 0.02, 0.39, 0.56))
        col = obj(nome + '_comporta_' + lado + '_colunas', bm, 'amarelo')
        if lado == 'O':
            trv = obj(nome + '_travessa_zarcao', bt, 'zarcao')
            amassar(trv, [(P(xg, 0.1, 0.56), 0.05, 0.008)], cortes=14)
        amassar(col, [(P(xg + sx * 0.0175, -0.37, 0.22), 0.04, 0.007), (P(xg, 0.37, 0.45), 0.04, 0.006)], cortes=12)
        bm = bmesh.new()
        for sy in (-1, 1):
            cil(bm, P(xg, sy * 0.41, 0.20), 0.016, 0.20, lados=14)
            cil(bm, P(xg, sy * 0.41, 0.102), 0.019, 0.008, lados=14)
            cil(bm, P(xg, sy * 0.41, 0.298), 0.019, 0.008, lados=14)
            caixa_de(bm, P(xg - 0.012, sy * 0.39 - 0.002, 0.12), P(xg + 0.012, sy * 0.395, 0.28))
            cil(bm, P(xg + sx * 0.018, sy * 0.41, 0.12), 0.005, 0.012, X, lados=8)
            cil(bm, P(xg + sx * 0.018, sy * 0.41, 0.28), 0.005, 0.012, X, lados=8)
        suavizar(obj(nome + '_comporta_' + lado + '_camisas', bm, 'grafite'))
        lam = bpy.data.objects.new(nome + '_lamina_' + lado, None)
        sc.collection.objects.link(lam)
        lam.location = P(xg, 0, 0)
        bm = bmesh.new()
        caixa_de(bm, (-0.004, -0.315, 0.19), (0.004, 0.315, 0.31))
        for sy in (-1, 1):
            caixa_de(bm, (-0.006, sy * 0.30, 0.29), (0.006, sy * 0.43, 0.31))
        obj(nome + '_lamina', bm, 'aco', lam)
        bm = bmesh.new()
        caixa_de(bm, (-0.0045, -0.30, 0.25), (0.0045, 0.30, 0.27))
        obj(nome + '_lamina_listra', bm, 'listras', lam)
        bm = bmesh.new()
        for sy in (-1, 1):
            cil(bm, Vector((0, sy * 0.41, 0.29 - 0.09)), 0.007, 0.18, lados=10)
        suavizar(obj(nome + '_hastes', bm, 'cromo', lam))
        # lâmpada da comporta no topo da coluna norte (verde aberta, vermelha fechada)
        def cor_comp(t, ln=lado):
            ab = JUNCOES[-1]['abre'][ln](t) if JUNCOES else 0.0
            return ((0.15, 1.0, 0.2), 6.0) if ab > 0.5 else ((1.0, 0.05, 0.02), 6.0)
        ml = lampada(nome + '_lamp_' + lado, cor_comp)
        bm = bmesh.new()
        cil(bm, P(xg, 0.37, 0.578), 0.016, 0.036, lados=14)
        obj(nome + '_lamp_' + lado, bm, ml)
        bm = bmesh.new()
        cil(bm, P(xg, 0.37, 0.562), 0.02, 0.006, lados=14)
        cil(bm, P(xg, 0.37, 0.597), 0.019, 0.004, lados=14)
        obj(nome + '_lamp_aro_' + lado, bm, 'grafite')
        comportas[lado] = lam
    # fotocélulas nas 3 entradas (sobre as laterais)
    bm, bf = bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        caixa(bm, P(sx * 0.333, -0.47, 0.24), (0.024, 0.03, 0.05))
        caixa(bm, P(0.47 * sx, -0.333, 0.24), (0.03, 0.024, 0.05))
        caixa(bm, P(0.47 * sx, 0.333, 0.24), (0.03, 0.024, 0.05))
    obj(nome + '_fotocelulas', bm, 'amarelo')
    feixe_obj(nome + '_feixe_S', P(-0.318, -0.47, 0.245), P(0.318, -0.47, 0.245))
    for sx in (-1, 1):
        feixe_obj(nome + '_feixe_%d' % sx, P(0.47 * sx, -0.318, 0.245), P(0.47 * sx, 0.318, 0.245))
    # caixa de controle (NE), bloco de válvulas (NO), mangueiras até os pistões, cabos
    caixa_controle(nome + '_controle', o, (0.35, 0.437, 0.05), (0.49, 0.497, 0.30))
    bm = bmesh.new()
    caixa_de(bm, P(-0.49, 0.437, 0.03), P(-0.36, 0.497, 0.13))
    obj(nome + '_valvulas', bm, 'amarelo')
    bm = bmesh.new()
    for k in range(4):
        cil(bm, P(-0.47 + k * 0.03, 0.46, 0.145), 0.008, 0.03, lados=8)
    obj(nome + '_valvulas_bobinas', bm, 'grafite')
    bm, bc, ba = bmesh.new(), bmesh.new(), bmesh.new()
    caixa_de(bm, P(-0.36, 0.475, 0.0), P(0.35, 0.5, 0.02))
    obj(nome + '_eletrocalha', bm, 'aco')
    for k in range(3):
        mangueira(bc, [P(-0.36, 0.482 + k * 0.006, 0.012), P(0.35, 0.482 + k * 0.006, 0.012)], 0.004)
    feixe(bc, ba, bezier(P(0.36, 0.46, 0.05), P(0.36, 0.47, 0.02), P(0.33, 0.488, 0.015), P(0.30, 0.488, 0.015), 5), n=3, r=0.004, lado=Y)
    feixe(bc, ba, bezier(P(0.47, 0.425, 0.12), P(0.47, 0.38, 0.1), P(0.47, 0.35, 0.2), P(0.47, 0.345, 0.218), 6), n=1, r=0.004)
    feixe(bc, ba, bezier(P(-0.36, 0.46, 0.05), P(-0.34, 0.47, 0.02), P(-0.32, 0.488, 0.015), P(-0.30, 0.488, 0.015), 5), n=2, r=0.004, lado=Y)
    suavizar(obj(nome + '_cabos', bc, 'borracha'))
    obj(nome + '_abracadeiras', ba, 'aco')
    bm = bmesh.new()
    for lado, sx in (('L', 1), ('O', -1)):
        xg = sx * 0.375
        for sy in (-1, 1):
            for zz in (0.12, 0.28):
                a = P(xg + sx * 0.024, sy * 0.41, zz)
                v0 = P(-0.40 + (0.02 if zz > 0.2 else 0) + (0.04 if sy > 0 else 0), 0.425, 0.08)
                mangueira(bm, bezier(a, a + Vector((sx * 0.05, 0, -0.02)), Vector((a.x + sx * 0.06, o.y + 0.45 * sy, 0.03)),
                                     v0 + Vector((0, 0, -0.04)), 10), 0.0045)
    suavizar(obj(nome + '_mangueiras', bm, 'laranja'))
    bm = bmesh.new()
    for k in range(25):
        pedra(bm, P(random.uniform(-0.45, 0.45), random.uniform(-0.45, 0.45), 0.004), random.uniform(0.005, 0.012), 0.5)
    obj(nome + '_farelo', bm, 'minerio')
    # ---- desgaste
    bm, bp, bf_, bo, bl_ = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    remendo(bm, bp, P(0.395, 0.37, 0.30), X, 0.034, 0.10, 0.03)
    remendo(bm, bp, P(0.395, -0.12, 0.54), X, 0.13, 0.032, -0.02)
    obj(nome + '_remendos', bm, 'aco')
    obj(nome + '_remendos_paraf', bp, 'grafite')
    for sx in (-1, 1):
        for sy in (-1, 1):
            escorrido(bf_, P(sx * 0.375 + sx * 0.0178, sy * 0.37, 0.50), Vector((sx, 0, 0)), random.uniform(0.08, 0.22), 0.012)
    escorrido(bf_, P(0.396, -0.08, 0.557), X, 0.035, 0.01)
    obj(nome + '_ferrugem', bf_, 'ferrugem')
    for sx in (-1, 1):
        for sy in (-1, 1):
            escorrido(bo, P(sx * 0.375 + sx * 0.0162, sy * 0.41, 0.12), Vector((sx, 0, 0)), 0.05, 0.008)
    for c_, r_ in ((P(-0.42, 0.46, 0), 0.07), (P(-0.44, -0.41, 0), 0.06), (P(0.375, -0.41, 0), 0.04)):
        mancha(bo, (c_.x, c_.y), r_, 0.0016)
    obj(nome + '_oleo2', bo, 'oleo')
    for sx in (-1, 1):
        for sy in (-1, 1):
            mancha(bl_, (o.x + sx * 0.42, o.y + sy * 0.25), random.uniform(0.06, 0.1), 0.0013)
    obj(nome + '_lama', bl_, 'lama')
    bc, bcu = bmesh.new(), bmesh.new()
    fio_exposto(bc, bcu, [P(0.36, 0.45, 0.05), P(0.33, 0.44, 0.04), P(0.31, 0.42, 0.06), P(0.30, 0.40, 0.055)], 0.0035)
    fio_exposto(bc, bcu, [P(0.48, 0.44, 0.06), P(0.49, 0.42, 0.03)], 0.003)
    suavizar(obj(nome + '_fios', bc, 'laranja'))
    obj(nome + '_fios_cobre', bcu, 'cobre')
    bm = bmesh.new()
    montinhos(bm, [P(sx * 0.33, sy * 0.33, 0.216) for sx in (-1, 1) for sy in (-1, 1)] +
              [P(sx * 0.375, sy * 0.37, 0.561) for sx in (-1, 1) for sy in (-1, 1)] + [P(0.33, 0.45, 0.216), P(-0.45, -0.33, 0.216)], n=5)
    montinhos(bm, [P(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0.0) for k in range(6)], n=8, r=(0.006, 0.016))
    obj(nome + '_po_minerio', bm, 'po_minerio')
    serie('JN-2208', P(0.3955, 0.15, 0.54), X, Z, 0.02)
    serie('C09', P(0.42, 0.4365, 0.2), -Y, Z, 0.022)
    serie('B', P(-0.3955, 0.37, 0.4), -X, Z, 0.03)
    j = {'o': o, 'comportas': comportas, 'abre': {}, 'janelas': {'L': [], 'O': []}, 'reservas': [], 'pend': []}
    j['abre']['L'] = lambda t, jj=j: max([janela(t, a - 0.3, a + 0.45, 0.22, 0.2) for a in jj['janelas']['L']] + [0.0])
    j['abre']['O'] = lambda t, jj=j: max([janela(t, a - 0.3, a + 0.45, 0.22, 0.2) for a in jj['janelas']['O']] + [0.0])
    JUNCOES.append(j)
    return j


def livre(T, reservas, folga=0.75):
    return all(abs(((T - x + DURACAO / 2) % DURACAO) - DURACAO / 2) >= folga for x in reservas)


def rota_juncao_ate(r, j, entrada):
    """Leva o item até a espera (comporta) ou, se vem do sul, reserva a passagem: o sul tem prioridade."""
    o = j['o']
    P = lambda x, y: o + Vector((x, y, ZI))
    if entrada == 'S':
        j['reservas'].append(r.agora() + 0.6 / VEL_R)
        r.linha(P(0, 0.5))
        return
    sx = 1 if entrada == 'L' else -1
    r.linha(P(sx * 0.478, 0.0))
    j['pend'].append((r, entrada))


def rota_juncao_resolver(j, saida):
    o = j['o']
    P = lambda x, y: o + Vector((x, y, ZI))
    for r, entrada in sorted(j['pend'], key=lambda x: x[0].agora()):
        sx = 1 if entrada == 'L' else -1
        pts = bezier(P(sx * 0.478, 0), P(sx * 0.2, 0.0), P(0, 0.02), P(0, 0.25), 8)
        l_m = sum((b - a).length for a, b in zip(pts, pts[1:])) - 0.1
        t = r.agora()
        while not livre(t + l_m / VEL_R, j['reservas']):
            t += 0.02
        j['reservas'].append(t + l_m / VEL_R)
        j['janelas'][entrada].append(t)
        r.ate(t)
        r.curva(pts)
        r.linha(P(0, 0.5))
        r.esteira(saida)


def animar_juncao(j):
    for lado, lam in j['comportas'].items():
        for q in range(1, QUADROS + 1):
            t = (q - 1) / FPS
            lam.location.z = 0.145 * j['abre'][lado](t)
            lam.keyframe_insert('location', index=2, frame=q)


# ================================================================== cena
def chao(cortes=()):
    bm = bmesh.new()
    caixa(bm, (0, 0, -0.5), (30, 30, 1.0))
    g = obj('chao', bm, 'chao')
    for k, (a, b) in enumerate(cortes):
        bm = bmesh.new()
        caixa_de(bm, a, b)
        ct = obj('corte_%d' % k, bm, 'chao')
        ct.hide_render = True
        ct.display_type = 'WIRE'
        md = g.modifiers.new('corte_%d' % k, 'BOOLEAN')
        md.operation = 'DIFFERENCE'
        md.object = ct
        md.solver = 'EXACT'
    bm, bl = bmesh.new(), bmesh.new()                                            # poeira e lama no chão
    for k in range(40):
        mancha(bm, (random.uniform(-3, 3), random.uniform(-3.5, 6.5)), random.uniform(0.1, 0.35), 0.0008)
    for k in range(14):
        mancha(bl, (random.uniform(-2.5, 2.5), random.uniform(-3.5, 6.5)), random.uniform(0.03, 0.07), 0.0011)
    obj('poeira_chao', bm, 'poeira')
    obj('lama_chao', bl, 'lama')
    bm = bmesh.new()
    for k in range(120):
        pedra(bm, Vector((random.uniform(-3, 3), random.uniform(-3.5, 6.5), 0.0)), random.uniform(0.004, 0.014), 0.5)
    obj('cascalho_chao', bm, 'cascalho')


def luz_camera():
    sol = bpy.data.lights.new('Sol', 'SUN')
    sol.energy = 4.5
    sol.angle = math.radians(2.5)
    so = bpy.data.objects.new('Sol', sol)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(48), 0, math.radians(35))
    mundo = bpy.data.worlds.new('Mundo')
    sc.world = mundo
    bg = mundo.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
    bg.inputs['Strength'].default_value = 0.6
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences
        pr.compute_device_type = 'OPTIX'
        pr.get_devices()
        for dv in pr.devices:
            dv.use = True
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -0.4
    cam_d = bpy.data.cameras.new('Cam')
    cam = bpy.data.objects.new('Cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam, cam_d


def animar_lampadas():
    for m, fn in LAMPADAS:
        b = m.node_tree.nodes['Principled BSDF']
        for q in range(1, QUADROS + 1):
            cor, forca = fn((q - 1) / FPS)
            b.inputs['Emission Color'].default_value = (*cor, 1)
            b.inputs['Base Color'].default_value = (*cor, 1)
            b.inputs['Emission Strength'].default_value = forca
            b.inputs['Emission Color'].keyframe_insert('default_value', frame=q)
            b.inputs['Base Color'].keyframe_insert('default_value', frame=q)
            b.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)


Q3 = DURACAO / 3
FOTOS = []            # (arquivo, quadro, pos, alvo, lente, (larg, alt))
cortes = []

if CENA == 'tunel':
    T = tunel('tunel', 0.0, 0.0, 3.0)
    cortes = T['cortes']
    alim = reta('alim', (0, -2.6), (0, -0.5))
    sai = reta('sai', (0, 3.5), (0, 5.4))
    ponte(ponta(alim, 'fim'), ponta(T['rampa1'], 'ini'))
    ponte(ponta(T['rampa2'], 'fim'), ponta(sai, 'ini'))
    for k in range(3):
        r = Rota(k * Q3, 'minerio' if k != 1 else 'chapa')
        r.esteira(alim)
        r.esteira(T['rampa1'])
        r.esteira(T['sub'])
        r.esteira(T['rampa2'])
        r.esteira(sai)
        ROTAS.append(r)
    t_boca = ROTAS[0].t0 + alim['L'] / VEL_R + 0.12 / VEL_R
    qf = int(round(t_boca * FPS)) % QUADROS + 1
    FOTOS += [('esteira_tunel.png', qf, (2.3, -2.6, 1.55), (0.0, 0.9, 0.12), 30, (1400, 900)),
              ('esteira_tunel_perto.png', qf, (0.55, -1.45, 0.55), (0.0, -0.3, 0.22), 35, (1400, 900)),
              ('esteira_tunel_saida.png', int(round((t_boca + 1.2) * FPS)) % QUADROS + 1, (-1.4, 5.6, 1.2), (0.0, 3.0, 0.2), 32, (1400, 900))]

elif CENA == 'divisor':
    D = divisor('divisor', Vector((0, 0, 0)))
    alim = reta('alim', (0, -2.5), (0, -0.5))
    sN = reta('saiN', (0, 0.5), (0, 2.0))
    sL = reta('saiL', (0.5, 0), (2.0, 0))
    sO = reta('saiO', (-0.5, 0), (-2.0, 0))
    ponte_borda(alim, 'fim', (0, -0.485))
    ponte_borda(sN, 'ini', (0, 0.485))
    ponte_borda(sL, 'ini', (0.485, 0))
    ponte_borda(sO, 'ini', (-0.485, 0))
    for k, (tipo, s) in enumerate((('minerio', 'L'), ('chapa', 'N'), ('minerio', 'O'))):
        r = Rota(k * Q3, tipo)
        r.esteira(alim)
        rota_divisor(r, D, s, {'N': sN, 'L': sL, 'O': sO})
        ROTAS.append(r)
    t_a = D['eventos'][0][0]
    qf = int(round((t_a + 0.45) * FPS)) % QUADROS + 1
    FOTOS += [('esteira_divisor.png', qf, (1.55, -1.75, 1.35), (0.0, 0.0, 0.25), 32, (1400, 1000)),
              ('esteira_divisor_perto.png', qf, (-0.95, -1.05, 0.75), (0.05, 0.1, 0.3), 32, (1400, 1000))]

elif CENA == 'juncao':
    J = juncao('juncao', Vector((0, 0, 0)))
    eS = reta('entS', (0, -2.5), (0, -0.5))
    eL = reta('entL', (2.5, 0), (0.5, 0))
    eO = reta('entO', (-2.5, 0), (-0.5, 0))
    sN = reta('saiN', (0, 0.5), (0, 2.2))
    ponte_borda(eS, 'fim', (0, -0.485))
    ponte_borda(eL, 'fim', (0.485, 0))
    ponte_borda(eO, 'fim', (-0.485, 0))
    ponte_borda(sN, 'ini', (0, 0.485))
    rS = Rota(0.0, 'chapa'); rS.esteira(eS); rota_juncao_ate(rS, J, 'S'); rS.esteira(sN)
    rL = Rota(0.25, 'minerio'); rL.esteira(eL); rota_juncao_ate(rL, J, 'L')
    rO = Rota(0.5, 'minerio'); rO.esteira(eO); rota_juncao_ate(rO, J, 'O')
    rota_juncao_resolver(J, sN)
    ROTAS += [rS, rL, rO]
    qf = int(round((J['reservas'][0] - 0.1) * FPS)) % QUADROS + 1
    FOTOS += [('esteira_juncao.png', qf, (1.6, -1.7, 1.35), (0.0, 0.05, 0.25), 32, (1400, 1000)),
              ('esteira_juncao_perto.png', qf, (1.05, 0.95, 0.75), (0.1, -0.05, 0.25), 32, (1400, 1000))]

else:   # linha montada: alimentação → divisor → (N) túnel → junção; (L/O) ramais em volta → junção → saída
    D = divisor('divisor', Vector((0, -1, 0)))
    T = tunel('tunel', 0.0, 0.0, 3.0)
    J = juncao('juncao', Vector((0, 4, 0)))
    cortes = T['cortes']
    alim = reta('alim', (0, -3.6), (0, -1.5))
    ponte_borda(alim, 'fim', (0, -1.485))
    ponte(Vector((0, -0.515, H)), ponta(T['rampa1'], 'ini'))
    ponte(ponta(T['rampa2'], 'fim'), Vector((0, 3.515, H)))
    ramos = {}
    for sx, lado in ((1, 'L'), (-1, 'O')):
        a = reta('r%s_1' % lado, (sx * 0.5, -1), (sx * 1.5, -1))
        c1 = esteira('r%s_c1' % lado, caminho_curva(0.5, sx), Vector((sx * 2, -1, 0)), 0.0 if sx > 0 else PI)
        b = reta('r%s_2' % lado, (sx * 2, -0.5), (sx * 2, 3.5))
        c2 = esteira('r%s_c2' % lado, caminho_curva(0.5, sx), Vector((sx * 2, 4, 0)), PI / 2)
        d_ = reta('r%s_3' % lado, (sx * 1.5, 4), (sx * 0.5, 4))
        ponte_borda(a, 'ini', (sx * 0.485, -1))
        for p_, n_ in ((a, c1), (c1, b), (b, c2), (c2, d_)):
            ponte(ponta(p_, 'fim'), ponta(n_, 'ini'))
        ponte_borda(d_, 'fim', (sx * 0.485, 4))
        ramos[lado] = [a, c1, b, c2, d_]
    sN = reta('saiN', (0, 4.5), (0, 6.6))
    ponte_borda(sN, 'ini', (0, 4.485))
    rotas_l = []
    for k, (tipo, s) in enumerate((('minerio', 'L'), ('chapa', 'N'), ('minerio', 'O'))):
        r = Rota(k * Q3, tipo)
        r.esteira(alim)
        if s == 'N':
            rota_divisor(r, D, 'N', {'N': T['rampa1']})
            r.esteira(T['sub'])
            r.esteira(T['rampa2'])
            rota_juncao_ate(r, J, 'S')
            r.esteira(sN)
        else:
            rota_divisor(r, D, s, {s: ramos[s][0]})
            for e_ in ramos[s][1:]:
                r.esteira(e_)
            rota_juncao_ate(r, J, s)
        ROTAS.append(r)
    rota_juncao_resolver(J, sN)
    t_a = D['eventos'][0][0]
    qf = int(round((t_a + 0.45) * FPS)) % QUADROS + 1
    FOTOS += [('esteira_acessorios_linha.png', qf, (4.3, -4.2, 3.6), (0.0, 1.4, 0.0), 36, (1500, 1100)),
              ('esteira_acessorios_linha_baixa.png', qf, (-3.4, -4.4, 1.5), (0.2, 0.5, 0.2), 28, (1500, 1000))]

chao(cortes)
for e in ESTEIRAS:
    animar_esteira(e)
animar_itens()
for d in DIVISORES:
    animar_divisor(d)
for j in JUNCOES:
    animar_juncao(j)
animar_lamelas()
animar_lampadas()
animar_feixes()
for k_ in ('grafite', 'aco', 'amarelo', 'concreto', 'rolo', 'rolo_novo', 'placa', 'zarcao', 'primer', 'lamela', 'lamela_cinza', 'cromo'):
    envelhecer(M[k_], poeira=0.3 if k_ in ('cromo', 'rolo', 'rolo_novo', 'placa') else 0.75)
cam, cam_d = luz_camera()


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


so_uma = args[2] if len(args) > 2 else None
if len(args) > 1 and args[1] == 'foto':
    sc.cycles.samples = 128
    for arq, qf, pos, alvo, lente, (rx, ry) in FOTOS:
        if so_uma and so_uma not in arq:
            continue
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        sc.frame_set(qf)
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, arq)
        bpy.ops.render.render(write_still=True)
print('ACESSORIOS ok', CENA)
