"""Estudo isolado (fora do jogo): extrator de cristal 3×3, saída de item pelo sul (meio, S1), como no jogo.
Laje com poço octogonal aberto sobre a jazida: rocha rachada com veios que brilham e cristais brotando (alguns
quebrados). Quatro pilones amarelos seguram a coroa; no centro dela pende o emissor de ressonância (prisma violeta,
bobinas de cobre, camisa de refrigeração). O anel de extração corre nos trilhos dos pilones, erguido por quatro
pistões telescópicos; dele pendem quatro ventosas que agarram o cristal que a ressonância empurra para fora do chão.
No alto, uma calha basculante (dois pistões) entra por baixo, o cristal cai nela, escorrega até a esteira e sai
pela boca sul com cortina de borracha. Unidade de refrigeração (radiador com ventoinha, bomba, vaso de expansão,
canos de cobre com flanges), transformador com feixe de cabos em eletrocalha até o emissor, unidade hidráulica com
mangueiras até os pistões. Fenômeno da IA: halos de luz perfeitos flutuando sob o prisma e sobre a fenda, lascas levitando em órbita no poço.
Poeira de cristal no chão e no ar, óleo, ferrugem, listras de perigo. Nada feito para gente (sem cabine, escada, guarda-corpo).
Uso: blender -b --python estudo_extrator_cristal.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço: um cristal arrancado por laço
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=64, nr=16):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r):
    """Cano rígido por pontos: trechos retos, cotovelos redondos e flanges perto de cada curva."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        for c in (a + u * 0.06, b - u * 0.06):
            tubo(bf, c - u * 0.009, c + u * 0.009, r * 1.55, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def feixe(bc, ba, pts, lat, n=3, r=0.014, passo=4):
    """Cabos paralelos (deslocados em `lat`) seguindo a mesma curva, com abraçadeiras a cada `passo` pontos."""
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 0.6), 12)


def quadro(eixo):
    z = Vector(eixo).normalized()
    a = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 1, 0))
    x = (a - z * a.dot(z)).normalized()
    return x, z.cross(x), z


def prisma(bm, base, eixo, r, h, ponta, giro=0.0, afina=0.88, irreg=0.12):
    """Cristal: prisma hexagonal com ponta piramidal (base em `base`, crescendo em `eixo`)."""
    x, y, z = quadro(eixo)
    base = Vector(base)
    rr = [r * (1 + random.uniform(-irreg, irreg)) for _ in range(6)]
    angs = [giro + k * PI / 3 for k in range(6)]
    b0 = [bm.verts.new(base + (x * math.cos(a) + y * math.sin(a)) * rr[k]) for k, a in enumerate(angs)]
    b1 = [bm.verts.new(base + z * h + (x * math.cos(a) + y * math.sin(a)) * rr[k] * afina) for k, a in enumerate(angs)]
    tip = bm.verts.new(base + z * (h + ponta) + (x * random.uniform(-1, 1) + y * random.uniform(-1, 1)) * r * irreg * 0.6)
    bm.faces.new(list(reversed(b0)))
    for k in range(6):
        bm.faces.new((b0[k], b0[(k + 1) % 6], b1[(k + 1) % 6], b1[k]))
        bm.faces.new((b1[k], b1[(k + 1) % 6], tip))


def octo(bm, c, apo, z0, z1):
    """Prisma octogonal com faces planas viradas para os eixos."""
    R = apo / math.cos(PI / 8)
    vs0 = [bm.verts.new((c.x + R * math.cos(PI / 8 + k * PI / 4), c.y + R * math.sin(PI / 8 + k * PI / 4), z0)) for k in range(8)]
    vs1 = [bm.verts.new((v.co.x, v.co.y, z1)) for v in vs0]
    bm.faces.new(list(reversed(vs0)))
    bm.faces.new(vs1)
    for k in range(8):
        bm.faces.new((vs0[k], vs0[(k + 1) % 8], vs1[(k + 1) % 8], vs1[k]))


def rot_dir(d):
    """Matriz 3×3 com x tangencial, y = d (radial) e z para cima."""
    d = Vector((d.x, d.y, 0)).normalized()
    return Matrix((Vector((d.y, -d.x, 0)), d, Vector((0, 0, 1)))).transposed()


# ------------------------------------------------------------------ materiais
def cristal_mat(nome, forca):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.26, 0.05, 0.55, 1)
    b.inputs['Roughness'].default_value = 0.16
    b.inputs['IOR'].default_value = 1.55
    b.inputs['Transmission Weight'].default_value = 0.85
    b.inputs['Emission Color'].default_value = (0.42, 0.08, 1.0, 1)
    b.inputs['Emission Strength'].default_value = forca
    ru = mats.no(nt, 'ShaderNodeTexNoise', **{'Scale': 25.0, 'Detail': 6.0})      # nuvens e trincas internas
    bump = mats.no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def brilho_mat(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def borracha_mat():
    return mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0)


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'rocha': mats.material('Rocha', (0.10, 0.09, 0.10), 0.0, 0.85, pintura=False, sujeira=0.9, desgaste=0.0, ferrugem=0.25),
    'pedra': mats.material('Pedra', (0.16, 0.15, 0.15), 0.0, 0.8, pintura=False, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'po': mats.material('Pó de cristal', (0.36, 0.31, 0.40), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'po_escuro': mats.material('Pó na rocha', (0.17, 0.14, 0.19), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'fenda': mats.material('Fenda', (0.01, 0.008, 0.012), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'porcelana': mats.material('Porcelana', (0.45, 0.2, 0.1), 0, 0.2, pintura=False, sujeira=0.5, desgaste=0.0),
    'borracha': borracha_mat(),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'cristal': cristal_mat('Cristal', 0.6),
    'cristal_chao': cristal_mat('Cristal da jazida', 0.4),
    'prisma': brilho_mat('Prisma', (0.45, 0.1, 1.0), 6.0),
    'veio': brilho_mat('Veio', (0.4, 0.06, 1.0), 3.0),
    'faisca': brilho_mat('Poeira brilhante', (0.8, 0.6, 1.0), 25.0),
    'poeira': base3d.volume_mat('Poeira', (0.62, 0.56, 0.66), 2.2, 0.02, 0.9),
})

P = Vector((0.0, 0.3, 0.0))     # centro do poço (jazida)
AP = 0.85                       # apótema do poço octogonal
LAJE = 0.12
DIAG = [Vector((math.cos(a), math.sin(a), 0)) for a in (PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)]   # NE, NO, SO, SE
D_PIL = 0.85 * math.sqrt(2)     # do centro do poço ao eixo do pilone
Z_COROA = 2.36                  # topo dos pilones / fundo da coroa
R_ANEL = 0.62
H_BRACO = 0.5                   # do anel até as ventosas
ZC0 = 0.14                      # centro do cristal ainda preso no chão
Z_ANEL_BAIXO = ZC0 + H_BRACO
Z_ANEL_ALTO = 1.80
Z_CAMISA = 1.93                 # fundo da camisa dos pistões telescópicos (topo em 2,33)
CR, CH, CP = 0.1, 0.23, 0.09    # cristal arrancado: raio, corpo, ponta
MEIO = (CH + CP) / 2
APO_C = CR * math.cos(PI / 6)


def h_chao(x, y):
    """Altura da rocha no poço."""
    return 0.018 + 0.010 * math.sin(x * 9.0 + 1.3) * math.cos(y * 7.0) + 0.006 * math.sin(x * 23 + y * 17)


# ------------------------------------------------------------------ laje com poço, meio-fio listrado
bm = bmesh.new()
caixa_de(bm, (-1.5, -1.5, 0), (1.5, 1.5, LAJE))
laje = obj('laje', bm, 'concreto')
bm = bmesh.new()
octo(bm, P, AP, -0.1, 0.3)
corte = obj('laje_corte', bm, 'concreto')
corte.hide_render = True
corte.hide_viewport = True
bo = laje.modifiers.new('poço', 'BOOLEAN')
bo.operation, bo.object = 'DIFFERENCE', corte
bm = bmesh.new()
caixa_de(bm, (-1.505, -1.505, 0.0), (1.505, -1.49, LAJE))
caixa_de(bm, (-1.505, 1.49, 0.0), (1.505, 1.505, LAJE))
caixa_de(bm, (-1.505, -1.505, 0.0), (-1.49, 1.505, LAJE))
caixa_de(bm, (1.49, -1.505, 0.0), (1.505, 1.505, LAJE))
L_LADO = 2 * (AP + 0.05) * math.tan(PI / 8) + 0.02
for k in range(8):                                                        # meio-fio do poço (aço com listras)
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, P + d * (AP + 0.02) + Vector((0, 0, 0.08)), (L_LADO, 0.06, 0.2), rot_dir(d))
obj('listras', bm, 'listras')
bm = bmesh.new()                                                          # chapa de topo do meio-fio
for k in range(8):
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, P + d * (AP + 0.02) + Vector((0, 0, 0.187)), (L_LADO, 0.075, 0.012), rot_dir(d))
obj('meio_fio', bm, 'aco')

# ------------------------------------------------------------------ jazida: rocha rachada, veios brilhando, cristais
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=46, y_segments=46, size=AP + 0.08)
for v in bm.verts:
    v.co += P
    v.co.z = h_chao(v.co.x, v.co.y)
fora = []
for f in bm.faces:
    c = f.calc_center_median() - P
    if any(c.x * math.cos(k * PI / 4) + c.y * math.sin(k * PI / 4) > AP + 0.03 for k in range(8)):
        fora.append(f)
bmesh.ops.delete(bm, geom=fora, context='FACES')
suavizar(obj('jazida', bm, 'rocha'))

FENDAS = []
bf, bv = bmesh.new(), bmesh.new()
for k in range(9):                                                        # fendas que irradiam do centro
    a = k * 2 * PI / 9 + random.uniform(-0.2, 0.2)
    p = P + Vector((math.cos(a), math.sin(a), 0)) * 0.12
    for s in range(7):
        a += random.uniform(-0.5, 0.5)
        q = p + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.07, 0.11)
        if (q - P).length > AP - 0.05:
            break
        larg = 0.028 * (1 - s / 8)
        dd = (q - p)
        rr = rot_dir(Vector((-dd.y, dd.x, 0)))
        za = h_chao((p.x + q.x) / 2, (p.y + q.y) / 2)
        caixa(bf, (p + q) / 2 + Vector((0, 0, za + 0.001)), (dd.length + larg, larg, 0.01), rr)
        caixa(bv, (p + q) / 2 + Vector((0, 0, za + 0.004)), (dd.length + larg * 0.3, larg * 0.28, 0.006), rr)
        FENDAS.append((p + q) / 2)
        p = q
cil(bf, P + Vector((0, 0, 0.02)), 0.13, 0.012, lados=14)                  # boca da fenda onde o cristal brota
obj('fendas', bf, 'fenda')
obj('veios', bv, 'veio')

# cristais da jazida: em setores livres (fora das diagonais das ventosas e do lado da calha)
bc, bq = bmesh.new(), bmesh.new()
for k in range(26):
    while True:
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.3, 0.78)
        diag = min(abs(((a - PI / 4) + PI / 4) % (PI / 2) - PI / 4), 9)
        sul = abs(((a - 1.5 * PI) + PI) % (2 * PI) - PI)
        if diag > 0.38 and sul > 0.6:
            break
    c = P + Vector((math.cos(a), math.sin(a), 0)) * r
    c.z = h_chao(c.x, c.y) - 0.03
    tam = random.uniform(0.6, 1.25)
    eixo = Vector((random.uniform(-0.45, 0.45), random.uniform(-0.45, 0.45), 1)) + (c - P).normalized() * 0.3
    if random.random() < 0.25:                                            # quebrado: toco + ponta caída ao lado
        prisma(bc, c, eixo, 0.04 * tam, 0.06 * tam, 0.012, random.uniform(0, 1), afina=1.0)
        lado = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)).normalized()
        cq = c + lado * 0.09 * tam
        cq.z = h_chao(cq.x, cq.y) + 0.03 * tam
        prisma(bq, cq - Vector((lado.y, -lado.x, 0)) * 0.05 * tam, Vector((lado.y, -lado.x, 0.15)), 0.035 * tam, 0.06 * tam, 0.05 * tam, random.uniform(0, 1))
    else:
        prisma(bc, c, eixo, 0.04 * tam, 0.12 * tam, 0.05 * tam, random.uniform(0, 1))
        if random.random() < 0.6:                                         # cristal menor ao pé
            e2 = eixo + Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), 0))
            prisma(bc, c + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0)), e2, 0.022 * tam, 0.06 * tam, 0.03 * tam, random.uniform(0, 1))
for k in range(22):                                                       # lascas soltas pelo poço
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.18, 0.8)
    c = P + Vector((math.cos(a), math.sin(a), 0)) * r
    c.z = h_chao(c.x, c.y) + 0.004
    prisma(bq, c, Vector((math.cos(a + 1.5), math.sin(a + 1.5), random.uniform(0, 0.3))), random.uniform(0.008, 0.016),
           random.uniform(0.02, 0.04), 0.01, random.uniform(0, 1))
bmesh.ops.recalc_face_normals(bc, faces=bc.faces)
bmesh.ops.recalc_face_normals(bq, faces=bq.faces)
obj('cristais_jazida', bc, 'cristal_chao')
obj('lascas', bq, 'cristal')
bm = bmesh.new()
for k in range(30):                                                       # pedras soltas
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.2, 0.82)
    c = P + Vector((math.cos(a), math.sin(a), 0)) * r
    pedra(bm, c + Vector((0, 0, h_chao(c.x, c.y) + 0.008)), random.uniform(0.012, 0.03), 0.5)
obj('pedras', bm, 'pedra')

# ------------------------------------------------------------------ pilones com trilho e coroa
PIL = [P + d * D_PIL for d in DIAG]
bm, bt = bmesh.new(), bmesh.new()
for d, c in zip(DIAG, PIL):
    rz = Matrix.Rotation(math.atan2(d.y, d.x) + PI / 2, 3, 'Z')
    caixa(bm, c + Vector((0, 0, (LAJE + Z_COROA) / 2)), (0.16, 0.16, Z_COROA - LAJE), rz)
    caixa(bm, c + Vector((0, 0, LAJE + 0.015)), (0.3, 0.3, 0.03), rz)                 # sapata
    for s in range(4):                                                    # mãos-francesas da sapata
        e = rz @ Vector((math.cos(s * PI / 2), math.sin(s * PI / 2), 0))
        caixa(bm, c + e * 0.11 + Vector((0, 0, LAJE + 0.08)), (0.02, 0.06, 0.1), rot_dir(e) @ Matrix.Rotation(0, 3, 'Z'))
    caixa(bt, c - d * 0.1 + Vector((0, 0, (0.2 + Z_COROA - 0.04) / 2)), (0.04, 0.04, Z_COROA - 0.24), rz)   # trilho
    for s in range(4):                                                    # chumbadores
        e = rz @ Vector((math.cos(s * PI / 2 + PI / 4), math.sin(s * PI / 2 + PI / 4), 0))
        cil(bt, c + e * 0.18 + Vector((0, 0, LAJE + 0.04)), 0.012, 0.03, lados=6)
obj('pilones', bm, 'amarelo')
obj('trilhos', bt, 'aco')

bm = bmesh.new()                                                          # coroa: quadro + diagonais
X0, X1, Y0, Y1 = -0.85, 0.85, P.y - 0.85, P.y + 0.85
ZC1 = Z_COROA + 0.14
caixa_de(bm, (X0 - 0.07, Y0 - 0.07, Z_COROA), (X1 + 0.07, Y0 + 0.07, ZC1))
caixa_de(bm, (X0 - 0.07, Y1 - 0.07, Z_COROA), (X1 + 0.07, Y1 + 0.07, ZC1))
caixa_de(bm, (X0 - 0.07, Y0 + 0.07, Z_COROA), (X0 + 0.07, Y1 - 0.07, ZC1))
caixa_de(bm, (X1 - 0.07, Y0 + 0.07, Z_COROA), (X1 + 0.07, Y1 - 0.07, ZC1))
for d in DIAG:
    a, b = P + d * 0.27, P + d * (D_PIL - 0.08)
    caixa(bm, (a + b) / 2 + Vector((0, 0, Z_COROA + 0.06)), (0.1, (b - a).length, 0.12), rot_dir(d))
obj('coroa', bm, 'amarelo')
bm = bmesh.new()
octo(bm, P, 0.28, Z_COROA - 0.03, ZC1)                                    # cubo central
obj('cubo', bm, 'grafite')
bm = bmesh.new()                                                          # chapas de reforço nos cantos da coroa
for c in PIL:
    caixa(bm, c + Vector((0, 0, ZC1 + 0.006)), (0.2, 0.2, 0.012))
    for s in range(6):
        cil(bm, c + Vector((math.cos(s) * 0.07, math.sin(s) * 0.07, ZC1 + 0.016)), 0.01, 0.012, lados=6)
obj('coroa_chapas', bm, 'aco')

# ------------------------------------------------------------------ emissor de ressonância (pendurado no cubo)
Z_EM0, Z_EM1 = 1.98, Z_COROA - 0.03
bm = bmesh.new()
cil(bm, P + Vector((0, 0, (Z_EM0 + Z_EM1) / 2)), 0.2, Z_EM1 - Z_EM0, lados=28)
cil(bm, P + Vector((0, 0, Z_EM0 - 0.04)), 0.2, 0.08, lados=28, r2=0.11)   # redução até o porta-prisma
obj('emissor', bm, 'grafite')
bm = bmesh.new()
for z in (2.07, 2.13, 2.19, 2.25):                                        # bobinas de cobre
    toro(bm, P + Vector((0, 0, z)), 0.215, 0.022, 48, 10)
suavizar(obj('bobinas', bm, 'cobre'))
bm = bmesh.new()
cil(bm, P + Vector((0, 0, 2.30)), 0.225, 0.04, lados=28)                  # camisa d'água (colar de cima)
cil(bm, P + Vector((0, 0, 2.005)), 0.225, 0.04, lados=28)
for s in range(8):                                                        # tirantes entre os colares
    a = s * PI / 4 + PI / 8
    cil(bm, P + Vector((math.cos(a) * 0.235, math.sin(a) * 0.235, 2.155)), 0.008, 0.3, lados=6)
cil(bm, P + Vector((0, 0, Z_EM0 - 0.1)), 0.075, 0.04, lados=16)           # porta-prisma
for s in range(3):                                                        # garras do prisma
    a = s * 2 * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(bm, P + d * 0.07 + Vector((0, 0, Z_EM0 - 0.11)), P + d * 0.055 + Vector((0, 0, Z_EM0 - 0.2)), 0.018)
obj('emissor_aco', bm, 'aco')
prisma_em = bpy.data.objects.new('prisma_giro', None)
sc.collection.objects.link(prisma_em)
prisma_em.location = P + Vector((0, 0, Z_EM0 - 0.12))
bm = bmesh.new()
random.seed(3)
prisma(bm, Vector((0, 0, 0.0)), Vector((0, 0, -1)), 0.058, 0.1, 0.07, 0.0, afina=0.92, irreg=0.0)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('prisma', bm, 'prisma', prisma_em)
random.seed(8)
luz_res = bpy.data.lights.new('Ressonância', 'POINT')
luz_res.color = (0.62, 0.3, 1.0)
luz_res.shadow_soft_size = 0.12
lr = bpy.data.objects.new('Ressonância', luz_res)
sc.collection.objects.link(lr)
lr.location = P + Vector((0, 0, Z_EM0 - 0.35))
luz_poco = bpy.data.lights.new('Jazida', 'POINT')
luz_poco.color = (0.6, 0.25, 1.0)
luz_poco.shadow_soft_size = 0.4
lpo = bpy.data.objects.new('Jazida', luz_poco)
sc.collection.objects.link(lpo)
lpo.location = P + Vector((0, 0, 0.25))
bm = bmesh.new()                                                          # giroflex âmbar no cubo
cil(bm, P + Vector((0.12, -0.12, ZC1 + 0.04)), 0.035, 0.08, lados=12)
obj('giroflex_base', bm, 'grafite')
bm = bmesh.new()
cil(bm, P + Vector((0.12, -0.12, ZC1 + 0.1)), 0.03, 0.05, lados=12)
obj('giroflex', bm, 'lampada')

# ------------------------------------------------------------------ pistões telescópicos (camisa presa na diagonal da coroa)
bm, bcr = bmesh.new(), bmesh.new()
for d in DIAG:
    c = P + d * R_ANEL
    t = Vector((d.y, -d.x, 0))
    cil(bm, c + Vector((0, 0, (Z_CAMISA + 2.33) / 2)), 0.065, 2.33 - Z_CAMISA, lados=20)
    for z in (Z_CAMISA + 0.015, 2.31):
        cil(bm, c + Vector((0, 0, z)), 0.077, 0.03, lados=20)
    caixa(bm, c + Vector((0, 0, 2.345)), (0.12, 0.12, 0.03), rot_dir(d))   # olhal na viga
    cil(bm, c + t * 0.07 + Vector((0, 0, 2.27)), 0.018, 0.03, t, lados=10)  # porta de óleo (lado)
    cil(bm, c + t * 0.07 + Vector((0, 0, 1.98)), 0.018, 0.03, t, lados=10)
suavizar(obj('pistao_camisas', bm, 'grafite'))
ESTAGIOS = []
for i, (r, mat) in enumerate(((0.055, 'cromo'), (0.046, 'cromo'), (0.038, 'cromo'), (0.03, 'cromo'))):
    lista = []
    for d in DIAG:
        e = bpy.data.objects.new('estagio', None)
        sc.collection.objects.link(e)
        e.location = P + d * R_ANEL
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.2)), r, 0.4, lados=18)
        cil(bm, Vector((0, 0, 0.012)), r + 0.006, 0.024, lados=18)        # anel-guia de cada estágio
        if i == 3:
            caixa(bm, Vector((0, 0, -0.02)), (0.05, 0.03, 0.05))          # garfo da haste
        suavizar(obj('estagio%d' % i, bm, mat, e))
        lista.append(e)
    ESTAGIOS.append(lista)

# ------------------------------------------------------------------ anel de extração com guias e ventosas
anel = bpy.data.objects.new('anel', None)
sc.collection.objects.link(anel)
anel.location = P
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), R_ANEL, 0.045, 64, 14)
suavizar(obj('anel_tubo', bm, 'amarelo', anel))
bm, bs = bmesh.new(), bmesh.new()
for d in DIAG:
    rr = rot_dir(d)
    t = Vector((d.y, -d.x, 0))
    caixa(bm, d * R_ANEL, (0.12, 0.12, 0.13), rr)                         # abraçadeira do anel (olhal do pistão)
    caixa(bm, d * R_ANEL + Vector((0, 0, 0.085)), (0.04, 0.06, 0.04), rr)
    viga(bm, d * (R_ANEL + 0.05), d * (D_PIL - 0.2), 0.055)               # braço-guia até o trilho
    viga(bm, d * (R_ANEL + 0.05) + Vector((0, 0, -0.06)), d * (D_PIL - 0.32), 0.03)   # escora
    caixa(bs, d * (D_PIL - 0.185), (0.12, 0.03, 0.14), rr)                 # sapata deslizante
    for s in (-1, 1):
        caixa(bs, d * (D_PIL - 0.135) + t * s * 0.0325, (0.025, 0.07, 0.14), rr)
    viga(bm, d * R_ANEL + Vector((0, 0, -0.06)), d * R_ANEL + Vector((0, 0, -H_BRACO)), 0.04)   # pendural da ventosa
    c0 = d * 0.38 + Vector((0, 0, -H_BRACO))
    c1 = d * 0.62 + Vector((0, 0, -H_BRACO))
    cil(bm, (c0 + c1) / 2, 0.035, 0.24, d, lados=14)                      # cilindro da ventosa
    cil(bm, c1, 0.042, 0.02, d, lados=14)
obj('anel_estrutura', bm, 'amarelo', anel)
obj('anel_sapatas', bs, 'ferro', anel)
bm = bmesh.new()                                                          # mangueira de vácuo de cada ventosa
for d in DIAG:
    t = Vector((d.y, -d.x, 0))
    mangueira(bm, bezier(d * 0.6 + t * 0.03 + Vector((0, 0, -H_BRACO + 0.03)), d * 0.7 + Vector((0, 0, -H_BRACO + 0.1)),
                         d * 0.7 + Vector((0, 0, -0.25)), d * 0.665 + t * 0.03 + Vector((0, 0, -0.07)), 8), 0.012)
suavizar(obj('anel_mangueiras', bm, 'borracha', anel))
VENTOSAS = []
for k, d in enumerate(DIAG):
    v = bpy.data.objects.new('ventosa', None)
    sc.collection.objects.link(v)
    v.parent = anel
    bm = bmesh.new()
    cil(bm, d * (0.03 + 0.17), 0.02, 0.34, d, lados=12)                   # haste
    obj('ventosa_haste', bm, 'cromo', v)
    bm = bmesh.new()
    cil(bm, d * 0.015, 0.048, 0.03, d, lados=16, r2=0.03)                 # copo de borracha (boca para dentro)
    obj('ventosa_copo', bm, 'borracha', v)
    VENTOSAS.append((v, d))

# ------------------------------------------------------------------ cristal arrancado
cr = bpy.data.objects.new('cristal_arrancado', None)
sc.collection.objects.link(cr)
cr.rotation_mode = 'QUATERNION'
bm = bmesh.new()
prisma(bm, Vector((0, 0, -MEIO)), Vector((0, 0, 1)), CR, CH, CP, PI / 12, afina=1.0, irreg=0.0)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('cristal_arrancado_malha', bm, 'cristal', cr)

# ------------------------------------------------------------------ calha basculante e seus pistões
PV = Vector((0, -0.62, 0.5))
ALVO_C = Vector((0, P.y, 0.88))
TH_IN = math.atan2(ALVO_C.z - PV.z, ALVO_C.y - PV.y)
TH_OUT = math.radians(92)
S_FIM = 1.0
calha = bpy.data.objects.new('calha', None)
sc.collection.objects.link(calha)
calha.location = PV
bm = bmesh.new()
caixa_de(bm, (-0.15, -0.06, 0.0), (0.15, S_FIM, 0.03))                    # fundo
for s in (-1, 1):                                                         # paredes (baixam na ponta de cima)
    vs = [bm.verts.new((s * 0.158, y, z)) for y, z in ((-0.06, 0.0), (S_FIM - 0.2, 0.0), (S_FIM, 0.0), (S_FIM, 0.05), (S_FIM - 0.2, 0.13), (-0.06, 0.13))]
    ws = [bm.verts.new((s * 0.172, v.co.y, v.co.z)) for v in vs]
    bm.faces.new(vs)
    bm.faces.new(list(reversed(ws)))
    for i in range(6):
        bm.faces.new((vs[i], vs[(i + 1) % 6], ws[(i + 1) % 6], ws[i]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for y in (0.15, 0.45, 0.75):                                              # nervuras por baixo
    caixa(bm, (0, y, -0.02), (0.3, 0.025, 0.04))
for s in (-1, 1):                                                         # olhais dos pistões e mancal do pino
    caixa_de(bm, (s * 0.172, 0.31, -0.08), (s * 0.215, 0.39, 0.03))
    cil(bm, Vector((s * 0.19, 0.0, 0.0)), 0.035, 0.04, Vector((1, 0, 0)), lados=12)
obj('calha_corpo', bm, 'amarelo', calha)
bm = bmesh.new()
caixa_de(bm, (-0.135, -0.05, 0.03), (0.135, S_FIM - 0.02, 0.034))         # chapa de desgaste
obj('calha_chapa', bm, 'aco', calha)
LUG = Vector((0, 0.35, -0.06))
bm = bmesh.new()
for s in (-1, 1):                                                         # cavaletes do pino
    caixa_de(bm, (s * 0.26 - 0.025, PV.y - 0.04, LAJE), (s * 0.26 + 0.025, PV.y + 0.04, PV.z + 0.04))
    caixa_de(bm, (s * 0.26 - 0.06, PV.y - 0.08, LAJE), (s * 0.26 + 0.06, PV.y + 0.08, LAJE + 0.02))
cil(bm, PV, 0.016, 0.6, Vector((1, 0, 0)), lados=10)
obj('calha_cavaletes', bm, 'grafite')
ANC = [Vector((s * 0.2, -0.15, 0.1)) for s in (-1, 1)]
bm = bmesh.new()
for a in ANC:                                                             # base dos pistões da calha no poço
    caixa_de(bm, (a.x - 0.05, a.y - 0.06, 0.0), (a.x + 0.05, a.y + 0.06, 0.06))
    for s in (-1, 1):
        caixa_de(bm, (a.x + s * 0.04 - 0.008, a.y - 0.03, 0.06), (a.x + s * 0.04 + 0.008, a.y + 0.03, a.z + 0.03))
    cil(bm, a, 0.012, 0.1, Vector((1, 0, 0)), lados=8)
obj('calha_bases', bm, 'ferro')
CAM_C, HASTE_C = 0.46, 0.45
PIST_C = []
for a in ANC:
    cm = bpy.data.objects.new('pc_camisa', None)
    sc.collection.objects.link(cm)
    cm.rotation_mode = 'QUATERNION'
    cm.location = a
    bm = bmesh.new()
    cil(bm, Vector((0, 0, CAM_C / 2)), 0.032, CAM_C, lados=16)
    cil(bm, Vector((0, 0, 0.0)), 0.03, 0.05, Vector((1, 0, 0)), lados=10)
    cil(bm, Vector((0, 0, CAM_C - 0.01)), 0.038, 0.02, lados=16)
    cil(bm, Vector((0.032, 0, 0.06)), 0.012, 0.025, Vector((1, 0, 0)), lados=8)   # porta de óleo
    suavizar(obj('pc_camisa_malha', bm, 'grafite', cm))
    hs = bpy.data.objects.new('pc_haste', None)
    sc.collection.objects.link(hs)
    hs.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, HASTE_C / 2)), 0.018, HASTE_C, lados=12)
    caixa(bm, Vector((0, 0, 0.0)), (0.04, 0.04, 0.03))
    suavizar(obj('pc_haste_malha', bm, 'cromo', hs))
    PIST_C.append((a, cm, hs))


def ponto_calha(th, s, n=0.0, x=0.0):
    u = Vector((0, math.cos(th), math.sin(th)))
    nv = Vector((0, -math.sin(th), math.cos(th)))
    return PV + u * s + nv * n + Vector((x, 0, 0))


for th in (TH_IN, TH_OUT):
    lg = ponto_calha(th, LUG.y, LUG.z)
    print('calha %.1f°: pistão %.3f m (mín %.3f, máx %.3f)' % (math.degrees(th), (lg - Vector((0, ANC[0].y, ANC[0].z))).length,
                                                              HASTE_C + 0.02, CAM_C + HASTE_C - 0.04))

# ------------------------------------------------------------------ esteira até a boca sul
YE0, YE1, ZE = -1.5, -0.5, 0.30
V_EST = 0.4                     # metros por laço
RD = V_EST / (2 * PI)           # raio do tambor: 1 volta por laço
bm = bmesh.new()
for s in (-1, 1):
    caixa_de(bm, (s * 0.2 - 0.012, YE0 + 0.02, ZE - 0.12), (s * 0.2 + 0.012, YE1, ZE + 0.06))   # longarinas com aba-guia
    for y in (YE0 + 0.12, -1.0, YE1 - 0.1):
        caixa_de(bm, (s * 0.2 - 0.02, y - 0.02, LAJE), (s * 0.2 + 0.02, y + 0.02, ZE - 0.12))
for y in (YE0 + 0.12, -1.0, YE1 - 0.1):
    caixa_de(bm, (-0.2, y - 0.015, ZE - 0.12), (0.2, y + 0.015, ZE - 0.1))
obj('esteira_quadro', bm, 'amarelo')
bm = bmesh.new()
caixa_de(bm, (-0.165, YE0 + 0.06, ZE - 0.006), (0.165, YE1 - 0.05, ZE))
caixa_de(bm, (-0.165, YE0 + 0.06, ZE - 2 * RD - 0.006), (0.165, YE1 - 0.05, ZE - 2 * RD))
for y in [YE0 + 0.1 + k * 0.07 for k in range(13)]:                       # taliscas
    caixa_de(bm, (-0.16, y - 0.006, ZE), (0.16, y + 0.006, ZE + 0.008))
obj('esteira_lona', bm, 'borracha')
TAMBORES = []
for y in (YE0 + 0.06, YE1 - 0.05):
    e = bpy.data.objects.new('tambor', None)
    sc.collection.objects.link(e)
    e.location = (0, y, ZE - RD)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), RD - 0.004, 0.33, Vector((1, 0, 0)), lados=16)
    for s in (-1, 1):
        for k in range(4):
            a = k * PI / 2
            cil(bm, Vector((s * 0.172, math.cos(a) * 0.02, math.sin(a) * 0.02)), 0.005, 0.012, Vector((1, 0, 0)), lados=6)
    suavizar(obj('tambor_malha', bm, 'aco', e))
    TAMBORES.append(e)
bm = bmesh.new()                                                          # motorredutor no tambor sul (leste)
cil(bm, Vector((0.27, YE0 + 0.06, ZE - RD)), 0.05, 0.1, Vector((1, 0, 0)), lados=14)
caixa(bm, Vector((0.37, YE0 + 0.06, ZE - RD - 0.01)), (0.1, 0.12, 0.12))
cil(bm, Vector((0.37, YE0 + 0.2, ZE - RD - 0.01)), 0.055, 0.18, Vector((0, 1, 0)), lados=14)
for k in range(5):
    cil(bm, Vector((0.37, YE0 + 0.13 + k * 0.035, ZE - RD - 0.01)), 0.063, 0.008, Vector((0, 1, 0)), lados=14)
caixa_de(bm, (0.3, YE0 + 0.0, LAJE), (0.44, YE0 + 0.3, ZE - RD - 0.07))
obj('esteira_motor', bm, 'grafite')
bm = bmesh.new()                                                          # boca sul: pórtico com cortina de borracha
for s in (-1, 1):
    caixa_de(bm, (s * 0.26 - 0.03, -1.49, LAJE), (s * 0.26 + 0.03, -1.43, 0.7))
caixa_de(bm, (-0.29, -1.49, 0.64), (0.29, -1.43, 0.72))
obj('boca', bm, 'listras')
bm = bmesh.new()
for k in range(7):
    x = -0.19 + k * 0.063
    caixa_de(bm, (x - 0.028, -1.462, 0.5), (x + 0.028, -1.456, 0.64))
obj('cortina', bm, 'borracha')

ITENS = []
for k in range(4):
    e = bpy.data.objects.new('item', None)
    sc.collection.objects.link(e)
    e.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    prisma(bm, Vector((0, 0, -MEIO)), Vector((0, 0, 1)), CR, CH, CP, PI / 12, afina=1.0, irreg=0.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj('item_cristal', bm, 'cristal', e)
    ITENS.append(e)

# ------------------------------------------------------------------ unidade de refrigeração (leste): radiador, ventoinha, bomba
RX0, RX1, RY0, RY1, RZ1 = 1.08, 1.42, -0.38, 0.3, 1.0
bm = bmesh.new()
for x in (RX0, RX1):                                                      # montantes
    for y in (RY0, RY1):
        caixa_de(bm, (x - 0.025, y - 0.025, LAJE), (x + 0.025, y + 0.025, RZ1 + 0.06))
caixa_de(bm, (RX0, RY0, RZ1 - 0.08), (RX1, RY1, RZ1 + 0.04))              # caixa d'água de cima
caixa_de(bm, (RX0, RY0, LAJE + 0.08), (RX1, RY1, LAJE + 0.18))            # de baixo
obj('radiador_quadro', bm, 'grafite')
bm = bmesh.new()
for k in range(30):                                                       # aletas
    y = RY0 + 0.03 + k * (RY1 - RY0 - 0.06) / 29
    caixa_de(bm, (RX0 + 0.03, y - 0.003, LAJE + 0.18), (RX1 - 0.04, y + 0.003, RZ1 - 0.08))
for z in (0.35, 0.6, 0.85):                                               # tubos do núcleo
    caixa_de(bm, (RX0 + 0.03, RY0 + 0.02, z - 0.01), (RX1 - 0.04, RY1 - 0.02, z + 0.01))
obj('radiador_aletas', bm, 'aco')
FAN_C = Vector((1.455, (RY0 + RY1) / 2, 0.58))
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.3, radius2=0.3, depth=0.07,
                      matrix=Matrix.Translation(FAN_C) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
caixa_de(bm, (RX1 - 0.04, RY0, 0.24), (RX1 + 0.0, RY1, 0.92))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.x) > 0.9 and f.calc_center_median().x < RX1 + 0.001 and f.calc_center_median().x > RX1 - 0.002], context='FACES_ONLY')
for k in range(-6, 7):                                                    # grade
    caixa(bm, FAN_C + Vector((0.04, k * 0.045, 0)), (0.006, 0.006, 2 * math.sqrt(max(0.3 ** 2 - (k * 0.045) ** 2, 0.0004))))
caixa(bm, FAN_C + Vector((0.04, 0, 0)), (0.006, 0.6, 0.008))
obj('ventoinha_aro', bm, 'grafite')
ventoinha = bpy.data.objects.new('ventoinha', None)
sc.collection.objects.link(ventoinha)
ventoinha.location = FAN_C
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.06, 0.06, Vector((1, 0, 0)), lados=14)
for k in range(7):
    a = k * 2 * PI / 7
    caixa(bm, Matrix.Rotation(a, 3, 'X') @ Vector((0, 0, 0.16)), (0.012, 0.11, 0.22),
          Matrix.Rotation(a, 3, 'X') @ Matrix.Rotation(0.5, 3, 'Z'))
obj('ventoinha_pas', bm, 'aco', ventoinha)
bm = bmesh.new()                                                          # bomba e vaso de expansão
caixa_de(bm, (1.1, 0.78, LAJE), (1.44, 1.08, LAJE + 0.05))
cil(bm, Vector((1.36, 0.93, 0.32)), 0.085, 0.24, Vector((1, 0, 0)), lados=16)   # motor
for k in range(5):
    cil(bm, Vector((1.3 + k * 0.03, 0.93, 0.32)), 0.095, 0.008, Vector((1, 0, 0)), lados=16)
caixa(bm, Vector((1.36, 0.93, 0.205)), (0.18, 0.16, 0.04))
obj('bomba_motor', bm, 'grafite')
bm = bmesh.new()
cil(bm, Vector((1.2, 0.93, 0.32)), 0.11, 0.09, Vector((1, 0, 0)), lados=20)     # caracol da bomba
cil(bm, Vector((1.2, 0.93, 0.205)), 0.07, 0.05, lados=12)
obj('bomba_corpo', bm, 'amarelo')
bm = bmesh.new()
cil(bm, Vector((1.3, 1.3, 0.5)), 0.11, 0.62, lados=20)
curva(bm, Vector((1.3, 1.3, 0.81)), 0.11, 20)
for z in (0.3, 0.7):
    cil(bm, Vector((1.3, 1.3, z)), 0.118, 0.03, lados=20)
for s in range(3):
    a = s * 2 * PI / 3
    viga(bm, Vector((1.3 + math.cos(a) * 0.1, 1.3 + math.sin(a) * 0.1, 0.25)), Vector((1.3 + math.cos(a) * 0.15, 1.3 + math.sin(a) * 0.15, LAJE)), 0.025)
suavizar(obj('vaso_expansao', bm, 'amarelo'))
bm, bf = bmesh.new(), bmesh.new()
rP = 0.2
Z_RET, Z_SUP = 2.22, 2.1
y_ret, y_sup = 0.15, 0.45
x_ret = math.sqrt(0.225 ** 2 - (y_ret - P.y) ** 2)
x_sup = math.sqrt(0.225 ** 2 - (y_sup - P.y) ** 2)
cano(bm, bf, [(x_ret, y_ret, Z_RET), (1.2, y_ret, Z_RET), (1.2, y_ret, RZ1 + 0.04)], 0.032)            # retorno quente → radiador
cano(bm, bf, [(1.2, 0.84, 0.32), (1.2, 0.45, 0.32), (1.2, 0.45, Z_SUP), (x_sup, y_sup, Z_SUP)], 0.032)  # bomba → emissor
cano(bm, bf, [(1.25, RY1, 0.2), (1.25, 0.6, 0.2), (1.25, 0.6, 0.12 + 0.12), (1.2, 0.84, 0.24)], 0.026)  # radiador → bomba
cano(bm, bf, [(1.3, 1.3, 0.2), (1.3, 1.1, 0.2), (1.25, 1.02, 0.25)], 0.016)                              # vaso → bomba
suavizar(obj('canos_agua', bm, 'cobre'))
obj('canos_flanges', bf, 'aco')
bm = bmesh.new()                                                          # suportes dos canos na coroa
for y in (y_ret, y_sup):
    for x in (X1, 0.55):
        z = Z_RET if y == y_ret else Z_SUP
        viga(bm, (x, y, Z_COROA), (x, y, z + 0.035), 0.02)
        toro(bm, Vector((x, y, z)), 0.04, 0.008, 16, 6) if False else cil(bm, Vector((x, y, z)), 0.042, 0.03, Vector((1, 0, 0)), lados=14)
for z in (0.5, 1.4):                                                      # abraçadeira do cano vertical num poste
    viga(bm, (1.2, 0.45, z), (1.42, 0.45, z), 0.025)
caixa_de(bm, (1.4, 0.42, LAJE), (1.44, 0.48, 1.6))
obj('canos_suportes', bm, 'ferro')
bm = bmesh.new()
cil(bm, Vector((1.2, 0.5, 1.2)), 0.04, 0.015, Vector((0, 1, 0)), lados=16)       # termômetro / manômetro
cil(bm, Vector((1.2, 0.47, 1.2)), 0.012, 0.03, Vector((0, 1, 0)), lados=8)
obj('manometro', bm, 'cromo')

# ------------------------------------------------------------------ transformador (oeste) e feixe de cabos até o emissor
TX0, TX1, TY0, TY1, TZ1 = -1.45, -1.08, -0.05, 0.75, 0.88
bm = bmesh.new()
caixa_de(bm, (TX0, TY0, LAJE), (TX1, TY1, TZ1))
for k in range(9):                                                        # aletas de resfriamento
    y = TY0 + 0.08 + k * (TY1 - TY0 - 0.16) / 8
    caixa_de(bm, (TX1, y - 0.006, LAJE + 0.08), (TX1 + 0.05, y + 0.006, TZ1 - 0.1))
caixa_de(bm, (TX0 - 0.02, TY0 - 0.02, TZ1), (TX1 + 0.02, TY1 + 0.02, TZ1 + 0.03))
caixa_de(bm, (TX0 + 0.04, TY0 - 0.04, LAJE), (TX1 - 0.04, TY0, 0.55))     # caixa de ligação
obj('transformador', bm, 'grafite')
bm = bmesh.new()
ISOL = []
for k in range(3):                                                        # isoladores
    c = Vector(((TX0 + TX1) / 2, 0.15 + k * 0.2, TZ1 + 0.03))
    for j in range(4):
        cil(bm, c + Vector((0, 0, 0.025 + j * 0.035)), 0.04 - j * 0.004, 0.012, lados=14)
    cil(bm, c + Vector((0, 0, 0.08)), 0.02, 0.16, lados=10)
    ISOL.append(c + Vector((0, 0, 0.17)))
obj('isoladores', bm, 'porcelana')
bm = bmesh.new()
caixa_de(bm, ((TX0 + TX1) / 2 - 0.08, TY0 - 0.006, 0.6), ((TX0 + TX1) / 2 + 0.08, TY0, 0.7))
obj('placa_perigo', bm, 'listras')

e_no = DIAG[1]                                                            # pilone noroeste
PNO = PIL[1]
Q = PNO - e_no * 0.17                                                     # face de fora do pilone
Z_BAND = ZC1 + 0.03


def bandeja(bm, a, b, up, larg=0.13, aba=0.05):
    """Eletrocalha em U de a até b; `up` é a normal do fundo (lado aberto)."""
    a, b = Vector(a), Vector(b)
    f = (b - a).normalized()
    up = (up - f * up.dot(f)).normalized()
    lat = f.cross(up)
    rot = Matrix((lat, f, up)).transposed()
    L = (b - a).length
    caixa(bm, (a + b) / 2, (larg, L, 0.006), rot)
    for s in (-1, 1):
        caixa(bm, (a + b) / 2 + lat * s * larg / 2 + up * aba / 2, (0.006, L, aba), rot)


bm = bmesh.new()
H0 = Vector(((TX0 + TX1) / 2, TY1 + 0.08, TZ1 + 0.2))
H1 = Vector((Q.x, Q.y, H0.z))
bandeja(bm, H0, H1, Vector((0, 0, 1)))                                    # do transformador até o pilone
bandeja(bm, Vector((Q.x, Q.y, H0.z - 0.03)), Vector((Q.x, Q.y, Z_BAND + 0.03)), -e_no)   # sobe pela face de fora
T_FIM = P + e_no * 0.33
bandeja(bm, Vector((Q.x, Q.y, Z_BAND)), Vector((T_FIM.x, T_FIM.y, Z_BAND)), Vector((0, 0, 1)))   # por cima da diagonal
for z in (0.6, 1.2, 1.8):                                                 # mãos-francesas no pilone
    viga(bm, PNO - e_no * 0.08 + Vector((0, 0, z)), Q + e_no * 0.0 + Vector((0, 0, z)), 0.03)
caixa_de(bm, (H0.x - 0.02, H0.y - 0.02, TZ1 + 0.03), (H0.x + 0.02, H0.y + 0.02, H0.z))   # pé da calha no transformador
for t in (0.3, 0.7):
    p = PNO.lerp(P + e_no * 0.33, t)
    caixa(bm, Vector((p.x, p.y, (Z_COROA + 0.12 + Z_BAND) / 2)), (0.05, 0.05, Z_BAND - Z_COROA - 0.12))
obj('eletrocalha', bm, 'aco')
bm = bmesh.new()                                                          # prensa-cabos no cubo
caixa(bm, P + e_no * 0.17 + Vector((0, 0, ZC1 + 0.04)), (0.12, 0.12, 0.08), rot_dir(e_no))
obj('prensa_cabos', bm, 'grafite')
bc, ba = bmesh.new(), bmesh.new()
lat_h = Vector((1, 0, 0)) if abs((H1 - H0).normalized().y) > 0.7 else Vector((0, 1, 0))
pts = []
pts += bezier(ISOL[2], ISOL[2] + Vector((0, 0, 0.1)), H0 + Vector((0, -0.15, 0.03)), H0 + Vector((0, 0, 0.025)), 5)
pts += bezier(H0 + Vector((0, 0, 0.025)), H0.lerp(H1, 0.5) + Vector((0, 0, 0.025)), H1 + Vector((0, 0, 0.025)) + e_no * 0.0,
              Vector((Q.x, Q.y, H0.z)) - e_no * 0.025 + Vector((0, 0, 0.08)), 6)[1:]
pts += [Vector((Q.x, Q.y, z)) - e_no * 0.025 for z in [H0.z + 0.08 + k * (Z_BAND - 0.08 - H0.z - 0.08) / 10 for k in range(11)]][1:]
pts += bezier(Vector((Q.x, Q.y, Z_BAND - 0.08)) - e_no * 0.025, Vector((Q.x, Q.y, Z_BAND + 0.025)) - e_no * 0.025,
              Vector((Q.x, Q.y, Z_BAND + 0.025)) + e_no * 0.08, Vector((Q.x, Q.y, Z_BAND + 0.025)) + e_no * 0.2, 5)[1:]
pfim = Vector((T_FIM.x, T_FIM.y, Z_BAND + 0.025))
pts += [Vector((Q.x, Q.y, Z_BAND + 0.025)).lerp(pfim, k / 6) for k in range(1, 7)][1:]
pts += bezier(pfim, pfim + e_no * -0.06, P + e_no * 0.17 + Vector((0, 0, ZC1 + 0.18)), P + e_no * 0.17 + Vector((0, 0, ZC1 + 0.08)), 5)[1:]
feixe(bc, ba, pts, Vector((-e_no.y, e_no.x, 0)), n=3, r=0.014, passo=3)
for c in ISOL[:2]:                                                        # os outros dois isoladores entram no feixe
    mangueira(bc, bezier(c, c + Vector((0, 0, 0.12)), H0 + Vector((0, -0.25, 0.1)), H0 + Vector((0.03, -0.02, 0.03)), 6), 0.012)
suavizar(obj('cabos', bc, 'borracha'))
suavizar(obj('cabos_abracadeiras', ba, 'aco'))

# ------------------------------------------------------------------ unidade hidráulica (sudoeste) e mangueiras
HX0, HX1, HY0, HY1 = -1.45, -1.02, -1.45, -0.95
bm = bmesh.new()
caixa_de(bm, (HX0, HY0, LAJE), (HX1, HY1, 0.5))                           # tanque de óleo
caixa_de(bm, (HX0 - 0.01, HY0 - 0.01, 0.5), (HX1 + 0.01, HY1 + 0.01, 0.52))
obj('hpu_tanque', bm, 'amarelo')
bm = bmesh.new()
cil(bm, Vector((-1.26, -1.28, 0.62)), 0.08, 0.26, Vector((0, 1, 0)), lados=16)   # motor
for k in range(6):
    cil(bm, Vector((-1.26, -1.36 + k * 0.032, 0.62)), 0.09, 0.008, Vector((0, 1, 0)), lados=16)
caixa(bm, Vector((-1.26, -1.28, 0.535)), (0.16, 0.22, 0.03))
cil(bm, Vector((-1.26, -1.1, 0.62)), 0.06, 0.1, Vector((0, 1, 0)), lados=12)    # bomba
caixa(bm, Vector((-1.12, -1.05, 0.58)), (0.12, 0.08, 0.1))                # bloco de válvulas
cil(bm, Vector((-1.4, -1.0, 0.62)), 0.04, 0.18, lados=12)                 # filtro
obj('hpu_motor', bm, 'grafite')
bm = bmesh.new()
cil(bm, Vector((-1.38, -0.86, 0.4)), 0.07, 0.5, lados=18)                 # acumulador
curva(bm, Vector((-1.38, -0.86, 0.65)), 0.07, 18)
caixa_de(bm, (-1.45, -0.93, LAJE), (-1.31, -0.79, LAJE + 0.03))
suavizar(obj('hpu_acumulador', bm, 'cromo'))
bm = bmesh.new()
cil(bm, Vector((-1.12, -1.096, 0.6)), 0.03, 0.012, Vector((0, -1, 0)), lados=14)
obj('hpu_manometro', bm, 'cromo')

e_so = DIAG[2]
PSO = PIL[2]
QS = PSO - e_so * 0.13
bh, ba = bmesh.new(), bmesh.new()
lat_so = Vector((-e_so.y, e_so.x, 0))
for s in (-1, 1):                                                         # pressão e retorno: bloco → pilone → coroa → cubo
    o = lat_so * s * 0.035
    pts = bezier(Vector((-1.12 + s * 0.03, -1.05, 0.63)), Vector((-1.12 + s * 0.03, -1.0, 0.9)), QS + o + Vector((0, 0, 0.6)),
                 QS + o + Vector((0, 0, 1.0)), 8)
    pts += [QS + o + Vector((0, 0, z)) for z in (1.4, 1.8, 2.2)]
    pts += bezier(QS + o + Vector((0, 0, 2.2)), QS + o + Vector((0, 0, ZC1 + 0.03)), PSO + o + e_so * 0.05 + Vector((0, 0, ZC1 + 0.03)),
                  PSO + o + e_so * 0.25 + Vector((0, 0, ZC1 + 0.025)), 6)[1:]
    pts += bezier(PSO + o + e_so * 0.25 + Vector((0, 0, ZC1 + 0.025)), P + o + e_so * 0.45 + Vector((0, 0, ZC1 + 0.025)),
                  P + o + e_so * 0.25 + Vector((0, 0, ZC1 + 0.05)), P + o * 0.6 + e_so * 0.1 + Vector((0, 0, ZC1 + 0.06)), 6)[1:]
    mangueira(bh, pts, 0.016)
for z in (0.9, 1.4, 1.9):                                                 # abraçadeiras no pilone
    tubo(ba, QS + Vector((0, 0, z - 0.015)), QS + Vector((0, 0, z + 0.015)), 0.035, 12)
    viga(ba, QS + Vector((0, 0, z)), PSO - e_so * 0.08 + Vector((0, 0, z)), 0.02)
MAN = P + e_so * 0.04 + Vector((0, 0, ZC1 + 0.05))
caixa(ba, MAN, (0.14, 0.14, 0.08))                                        # distribuidor no cubo
for d in DIAG:                                                            # do distribuidor a cada pistão (pela lateral da viga)
    t = Vector((d.y, -d.x, 0))
    c = P + d * R_ANEL
    for s, zp in ((1, 2.27), (-1, 1.98)):
        tt = t * (0.07 if s > 0 else 0.07)
        a0 = MAN + d * 0.07 + t * 0.03 * s
        pts = bezier(a0, a0 + d * 0.12, P + d * 0.3 + t * 0.075 + Vector((0, 0, Z_COROA + 0.1)), P + d * 0.45 + t * 0.075 + Vector((0, 0, Z_COROA + 0.06)), 6)
        porta = c + t * 0.085 + Vector((0, 0, zp))
        pts += bezier(P + d * 0.45 + t * 0.075 + Vector((0, 0, Z_COROA + 0.06)), P + d * 0.55 + t * 0.1 + Vector((0, 0, Z_COROA + 0.02)),
                      porta + t * 0.08 + Vector((0, 0, 0.1 if s > 0 else 0.2)), porta + t * 0.0, 6)[1:]
        mangueira(bh, pts, 0.011)
for a in ANC:                                                             # da unidade hidráulica aos pistões da calha (pelo chão)
    porta = a + Vector((0.045 * (1 if a.x > 0 else 1), 0, 0.06))
    for s in (-1, 1):
        pts = bezier(Vector((-1.02, -1.0 + s * 0.03, 0.4)), Vector((-0.7, -1.0 + s * 0.03, LAJE + 0.02)),
                     Vector((a.x - 0.2, -0.6 + s * 0.03, LAJE + 0.02)), Vector((a.x - 0.05, -0.3 + s * 0.03, 0.3)), 10)
        pts += bezier(Vector((a.x - 0.05, -0.3 + s * 0.03, 0.3)), Vector((a.x - 0.03, -0.2 + s * 0.02, 0.15)),
                      Vector((a.x - 0.07, a.y - 0.03 + s * 0.02, 0.06)), Vector((a.x - 0.05, a.y + s * 0.02, 0.07)), 5)[1:]
        mangueira(bh, pts, 0.01)
suavizar(obj('mangueiras', bh, 'borracha'))
suavizar(obj('mangueiras_abracadeiras', ba, 'aco'))

# ------------------------------------------------------------------ sujeira: pó de cristal, óleo, lascas, escorridos
bm = bmesh.new()
for k in range(26):                                                       # pó de cristal em volta do poço
    a = random.uniform(0, 2 * PI)
    r = random.uniform(AP + 0.1, AP + 0.4)
    c = P + Vector((math.cos(a), math.sin(a), 0)) * r
    if abs(c.x) < 1.45 and abs(c.y) < 1.45:
        mancha(bm, (c.x, c.y), random.uniform(0.06, 0.16), LAJE + 0.001)
for k in range(8):                                                        # ao longo da esteira e sob a boca
    mancha(bm, (random.uniform(-0.35, 0.35), random.uniform(-1.45, -0.6)), random.uniform(0.05, 0.12), LAJE + 0.0012)
obj('po_cristal', bm, 'po')
bm = bmesh.new()
for k in range(14):                                                       # pó dentro do poço, sobre a rocha
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.15, 0.75)
    c = P + Vector((math.cos(a), math.sin(a), 0)) * r
    mancha(bm, (c.x, c.y), random.uniform(0.04, 0.1), h_chao(c.x, c.y) + 0.012)
obj('po_poco', bm, 'po_escuro')
bm = bmesh.new()
for c, r in (((-1.2, -0.8), 0.12), ((-1.0, -1.25), 0.08), ((1.25, 0.95), 0.09), ((-0.7, -0.6), 0.05), ((0.55, 1.0), 0.06)):
    mancha(bm, c, r, LAJE + 0.0018)
obj('oleo_chao', bm, 'oleo')
bm = bmesh.new()                                                          # óleo escorrendo do tanque e das camisas
for x in (-1.3, -1.15):
    caixa_de(bm, (x - 0.01, HY1 + 0.001, LAJE + 0.02), (x + 0.012, HY1 + 0.004, random.uniform(0.3, 0.48)))
for d in DIAG[:3]:
    c = P + d * R_ANEL + d * 0.066
    caixa(bm, c + Vector((0, 0, 2.08)), (0.022, 0.004, random.uniform(0.12, 0.25)), rot_dir(d))
obj('oleo_escorrido', bm, 'oleo')
bm = bmesh.new()
for k in range(30):                                                       # lascas de cristal na laje e na esteira
    if k < 18:
        a = random.uniform(0, 2 * PI)
        c = P + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(AP + 0.1, AP + 0.35)
        if abs(c.x) > 1.45 or abs(c.y) > 1.45:
            continue
        z = LAJE + 0.004
    else:
        c = Vector((random.uniform(-0.38, 0.38), random.uniform(-1.4, -0.65), 0))
        if abs(c.x) < 0.22:
            continue
        z = LAJE + 0.004
    prisma(bm, Vector((c.x, c.y, z)), Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0.15)), random.uniform(0.008, 0.015),
           random.uniform(0.02, 0.035), 0.01, random.uniform(0, 1))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('lascas_laje', bm, 'cristal')
bm = bmesh.new()                                                          # trincas no concreto em volta do poço
for k in range(7):
    a = random.uniform(0, 2 * PI)
    p = P + Vector((math.cos(a), math.sin(a), 0)) * (AP + 0.06)
    for s in range(4):
        a += random.uniform(-0.6, 0.6)
        q = p + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.05, 0.09)
        if abs(q.x) > 1.45 or abs(q.y) > 1.45:
            break
        dd = q - p
        caixa(bm, (p + q) / 2 + Vector((0, 0, LAJE + 0.0005)), (dd.length, 0.006, 0.002), rot_dir(Vector((-dd.y, dd.x, 0))))
        p = q
obj('trincas', bm, 'fenda')


# ------------------------------------------------------------------ fenômeno da IA: halos perfeitos e lascas levitando
bm = bmesh.new()
toro(bm, P + Vector((0, 0, 1.62)), 0.16, 0.006, 96, 8)                    # halo sob o prisma (não toca em nada)
toro(bm, P + Vector((0, 0, 0.06)), 0.2, 0.006, 96, 8)                     # halo flutuando sobre a fenda
toro(bm, P + Vector((0, 0, 0.075)), 0.235, 0.003, 96, 6)
obj('halos', bm, 'prisma')
random.seed(12)
bm0 = bmesh.new()
prisma(bm0, Vector((0, 0, -0.03)), Vector((0, 0, 1)), 0.016, 0.035, 0.022, 0.0, irreg=0.0)
bmesh.ops.recalc_face_normals(bm0, faces=bm0.faces)
me_lasca = bpy.data.meshes.new('lasca_levita')
bm0.to_mesh(me_lasca)
bm0.free()
me_lasca.materials.append(base3d.M['cristal'])
levitas = []
for k in range(6):
    o = bpy.data.objects.new('lasca_levita', me_lasca)
    sc.collection.objects.link(o)
    levitas.append(o)

# ------------------------------------------------------------------ poeira de cristal no ar
brilhos = []
for k in range(26):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.006)
    brilhos.append(obj('brilho', bm, 'faisca'))
fase_b = [(random.uniform(0, 1), random.uniform(0.05, 0.55), random.uniform(0, 2 * PI), random.uniform(0.3, 1.1)) for _ in brilhos]
nuvens = []
for k in range(6):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    nuvens.append(obj('poeira', bm, 'poeira'))
fase_n = [(k / 6, random.uniform(0, 2 * PI), random.uniform(0.1, 0.45)) for k in range(6)]


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def faixa(fr, a, b):
    return suave((fr - a) / (b - a))


Q_PE = Quaternion()
Q_DEITA = Quaternion((1, 0, 0), -PI / 2) @ Quaternion((0, 0, 1), -PI / 12)   # deitado com uma face para baixo, ponta para o norte


def q_calha(th):
    return Quaternion((1, 0, 0), th) @ Q_DEITA


Y_POUSO = -0.86


def angulo_calha(fr):
    if fr < 0.52:
        return TH_OUT
    if fr < 0.62:
        return TH_OUT + (TH_IN - TH_OUT) * faixa(fr, 0.52, 0.62)
    if fr < 0.80:
        return TH_IN
    if fr < 0.90:
        return TH_IN + (TH_OUT - TH_IN) * faixa(fr, 0.80, 0.90)
    return TH_OUT


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # anel: desce (0–0,2), agarra (0,2–0,28), sobe (0,28–0,52), fica no alto
    if fr < 0.2:
        za = Z_ANEL_ALTO + (Z_ANEL_BAIXO - Z_ANEL_ALTO) * faixa(fr, 0.0, 0.2)
    elif fr < 0.28:
        za = Z_ANEL_BAIXO
    else:
        za = Z_ANEL_BAIXO + (Z_ANEL_ALTO - Z_ANEL_BAIXO) * faixa(fr, 0.28, 0.52)
    anel.location = P + Vector((0, 0, za))
    anel.keyframe_insert('location', frame=q)
    L = Z_CAMISA - (za + 0.105)
    for i, lista in enumerate(ESTAGIOS):
        for e in lista:
            e.location.z = Z_CAMISA - (i + 1) * L / 4
            e.keyframe_insert('location', frame=q)
    fecha = faixa(fr, 0.2, 0.27) * (1 - faixa(fr, 0.66, 0.70))
    for k, (v, d) in enumerate(VENTOSAS):
        enc = APO_C if k % 2 == 0 else CR
        rp = 0.22 + (enc - 0.22) * fecha
        v.location = d * rp + Vector((0, 0, -H_BRACO))
        v.keyframe_insert('location', frame=q)
    # calha basculante e seus pistões
    th = angulo_calha(fr)
    calha.rotation_euler = (th, 0, 0)
    calha.keyframe_insert('rotation_euler', frame=q)
    for a, cm, hs in PIST_C:
        lg = ponto_calha(th, LUG.y, LUG.z, a.x)
        dv = lg - a
        cm.rotation_quaternion = dv.normalized().to_track_quat('Z', 'Y')
        hs.location = lg
        hs.rotation_quaternion = (-dv).normalized().to_track_quat('Z', 'Y')
        cm.keyframe_insert('rotation_quaternion', frame=q)
        hs.keyframe_insert('location', frame=q)
        hs.keyframe_insert('rotation_quaternion', frame=q)
    # cristal arrancado
    vis = True
    if fr < 0.28:
        pos, rot = P + Vector((0, 0, ZC0)), Q_PE
    elif fr < 0.66:
        pos, rot = P + Vector((0, 0, za - H_BRACO)), Q_PE
    elif fr < 0.70:
        x = faixa(fr, 0.66, 0.70)
        alvo = ponto_calha(TH_IN, 0.8, 0.034 + APO_C)
        topo = P + Vector((0, 0, Z_ANEL_ALTO - H_BRACO))
        pos = topo.lerp(alvo, x * x)
        rot = Q_PE.slerp(q_calha(TH_IN), x)
    elif fr < 0.78:
        x = (fr - 0.70) / 0.08
        pos, rot = ponto_calha(TH_IN, 0.8 - 0.9 * x * x, 0.034 + APO_C), q_calha(TH_IN)
    elif fr < 0.82:
        x = (fr - 0.78) / 0.04
        a0 = ponto_calha(TH_IN, -0.1, 0.034 + APO_C)
        a1 = Vector((0, Y_POUSO, ZE + APO_C))
        pos = a0.lerp(a1, x) + Vector((0, 0, 0.04 * math.sin(PI * x)))
        rot = q_calha(TH_IN).slerp(Q_DEITA, x)
    elif fr < 0.85:
        vis, pos, rot = False, P + Vector((0, 0, -0.3)), Q_PE
    else:
        pos, rot = P + Vector((0, 0, -0.26 + (ZC0 + 0.26) * faixa(fr, 0.85, 1.0))), Q_PE   # a ressonância empurra o próximo
    cr.location, cr.rotation_quaternion = pos, rot
    cr.scale = [1.0 if vis else 0.001] * 3
    for c in ('location', 'rotation_quaternion', 'scale'):
        cr.keyframe_insert(c, frame=q)
    # cristais na esteira até a boca sul
    for k, e in enumerate(ITENS):
        u = k + fr
        y = Y_POUSO - V_EST * (u - 0.82)
        ok = u >= 0.82 and y > -1.5
        e.location = (0, y, ZE + APO_C)
        e.rotation_quaternion = Q_DEITA
        e.scale = [1.0 if ok else 0.001] * 3
        for c in ('location', 'rotation_quaternion', 'scale'):
            e.keyframe_insert(c, frame=q)
    for e in TAMBORES:
        e.rotation_euler = (-2 * PI * fr, 0, 0)
        e.keyframe_insert('rotation_euler', frame=q)
    ventoinha.rotation_euler = (2 * PI * 10 * fr, 0, 0)
    ventoinha.keyframe_insert('rotation_euler', frame=q)
    prisma_em.rotation_euler = (0, 0, PI / 3 * fr)
    prisma_em.keyframe_insert('rotation_euler', frame=q)
    # ressonância: pulsa sempre, forte enquanto puxa o cristal
    ativo = faixa(fr, 0.12, 0.2) * (1 - faixa(fr, 0.5, 0.58)) + faixa(fr, 0.86, 0.9) * 0.6 * (1 - faixa(fr, 0.97, 1.0))
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 8 * fr)
    forca = 0.35 + 0.15 * math.sin(2 * PI * 2 * fr) + ativo * (0.5 + 0.5 * pulso)
    for nome, base in (('prisma', 7.0), ('veio', 3.0), ('cristal_chao', 1.5)):
        n = base3d.M[nome].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        n.default_value = base * forca
        n.keyframe_insert('default_value', frame=q)
    luz_res.energy = 140 * forca
    luz_res.keyframe_insert('energy', frame=q)
    luz_poco.energy = 28 * forca
    luz_poco.keyframe_insert('energy', frame=q)
    gf = base3d.M['lampada'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    gf.default_value = 8.0 if (fr * 4) % 1.0 < 0.5 else 0.3
    gf.keyframe_insert('default_value', frame=q)
    for k, o in enumerate(levitas):                                       # órbita lenta: 60° por laço (6 iguais, laço perfeito)
        a = k * PI / 3 + PI / 3 * fr + 0.3
        o.location = P + Vector((math.cos(a) * 0.72, math.sin(a) * 0.72, 0.35 + 0.04 * math.sin(2 * PI * fr + k * PI / 3 * 2)))
        o.rotation_euler = (0.6, 0.3, 2 * PI * fr + k)
        for c in ('location', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
    # poeira de cristal: brilhos subindo e girando em volta do poço; nuvens baixas que se desfazem
    for k, o in enumerate(brilhos):
        f0, r0, a0, vz = fase_b[k]
        u = (f0 + fr) % 1.0
        a = a0 + u * 1.5
        o.location = P + Vector((math.cos(a) * (r0 + 0.1 * u), math.sin(a) * (r0 + 0.1 * u), 0.05 + vz * 1.4 * u))
        o.scale = [max(0.001, math.sin(PI * u))] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    for k, o in enumerate(nuvens):
        f0, a0, r0 = fase_n[k]
        u = (f0 + fr) % 1.0
        o.location = P + Vector((math.cos(a0) * r0, math.sin(a0) * r0, 0.06 + 0.45 * u))
        o.scale = [0.12 + 0.22 * u] * 3
        o.rotation_euler = (k, u * 2, k * 0.7)
        for c in ('location', 'scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)

for o in list(sc.objects) + [luz_res, luz_poco] + list(bpy.data.materials):
    ad = getattr(o, 'animation_data', None)
    if o.__class__.__name__ == 'Material' and o.node_tree is not None:
        ad = o.node_tree.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
gfc = base3d.M['lampada'].node_tree.animation_data
if gfc and gfc.action:
    for fc in getattr(gfc.action, 'fcurves', []):
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.55
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
sc.view_settings.exposure = -0.5
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 0.95)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_uma = (len(sys.argv) > sys.argv.index('--') + 2 if '--' in sys.argv else False) and modo == 'foto'
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1200
    sc.frame_set(int(QUADROS * 0.63) + 1)                                 # anel no alto com o cristal, calha entrando por baixo
    vistas = ((300, 3.0), (215, 2.8), (120, 3.2), (35, 2.6))
    for i, (ang, alt) in enumerate(vistas):
        if so_uma and str(i) != sys.argv[-1]:
            continue
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 5.3, math.sin(a) * 5.3, alt)), ALVO, 33)
        sc.render.filepath = os.path.join(AQUI, 'extrator_cristal_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if not so_uma or sys.argv[-1] == 'perto':
        sc.frame_set(int(QUADROS * 0.31) + 1)                             # ventosas arrancando o cristal da fenda
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((0.15, 2.75, 1.05), (0.0, 0.3, 0.42), 30)
        sc.render.filepath = os.path.join(AQUI, 'extrator_cristal_perto.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':                                                       # câmera livre: -- teste x y z ax ay az lente fr
    v = [float(x) for x in sys.argv[sys.argv.index('--') + 2:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'extrator_teste.png')
    bpy.ops.render.render(write_still=True)
print('EXTRATOR ok')
