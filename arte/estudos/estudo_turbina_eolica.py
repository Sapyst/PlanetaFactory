"""Estudo isolado (fora do jogo): turbina eólica da IA, 2×2 tiles, sem portas (catálogo: turbina_eolica, 200 kW).
Laje com pedestal octogonal, chapa de base aparafusada (porcas enferrujadas) e quatro estais com esticadores presos em
blocos de ancoragem. Torre tubular octogonal afilada, flanges aparafusadas, colar dos estais e eletrocalha com três
cabos que descem até o armário inversor ao pé da torre. No topo: coroa dentada fixa e dois motores de guinada cujos
pinhões rolam na coroa e giram a nacele. Nacele amarela gasta com painel lateral asa-de-gaivota aberto (amortecedores a
gás) e escotilha de teto aberta para drone; dentro: mancal principal, multiplicadora planetária, freio a disco com
pinça, acoplamento e gerador aletado com caixa de ligação e cabos descendo ao centro. Radiador de óleo com ventoinha
no teto, mangueiras até a multiplicadora. Mastro com anemômetro de conchas e cata-vento. Hélice de 3 pás de compósito
gasto (borda de ataque erodida, lascas, manchas) com fita de campo violeta na borda de fuga. Óleo escorrendo da
vedação de guinada pela torre e ferrugem nos parafusos.
Partes animadas: nacele (guinada lenta), helice (gira), anemometro, catavento, pinhões de guinada.
Uso: blender -b --python estudo_turbina_eolica.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
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


def suave_tudo(o):
    for pg in o.data.polygons:
        pg.use_smooth = True
    return o


def toro(bm, centro, R, r, eixo=(0, 0, 1), nR=40, nr=10):
    """Anel tubular contínuo em volta de 'eixo'."""
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + q @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def bloco(bm, centro, ex, ey, ez, tam):
    """Caixa orientada pelos eixos ex, ey, ez (unitários)."""
    rot = Matrix((Vector(ex), Vector(ey), Vector(ez))).transposed()
    caixa(bm, centro, tam, rot)


def octo(bm, z0, z1, r0, r1, c=(0.0, 0.0)):
    """Prisma octogonal (raio de vértice r0 embaixo, r1 em cima); faces centradas nos ângulos k·45°."""
    angs = [k * PI / 4 + PI / 8 for k in range(8)]
    vb = [bm.verts.new((c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a), z0)) for a in angs]
    vt = [bm.verts.new((c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a), z1)) for a in angs]
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    for k in range(8):
        bm.faces.new((vb[k], vb[(k + 1) % 8], vt[(k + 1) % 8], vt[k]))


def revolver(bm, perfil, lados=32, eixo='X'):
    """Sólido de revolução em volta de X a partir de [(x, r), ...]."""
    aneis = []
    for x, r in perfil:
        anel = []
        for i in range(lados):
            a = i * 2 * PI / lados
            if r < 1e-5:
                anel = [bm.verts.new((x, 0, 0))]
                break
            anel.append(bm.verts.new((x, r * math.cos(a), r * math.sin(a))))
        aneis.append(anel)
    for A, B in zip(aneis, aneis[1:]):
        if len(B) == 1:
            for i in range(lados):
                bm.faces.new((A[i], A[(i + 1) % lados], B[0]))
        elif len(A) == 1:
            for i in range(lados):
                bm.faces.new((A[0], B[(i + 1) % lados], B[i]))
        else:
            for i in range(lados):
                bm.faces.new((A[i], A[(i + 1) % lados], B[(i + 1) % lados], B[i]))
    if len(aneis[0]) > 1:
        bm.faces.new(list(reversed(aneis[0])))


def vazio(nome, loc, pai=None):
    o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(o)
    o.location = loc
    o.rotation_mode = 'XYZ'
    if pai is not None:
        o.parent = pai
    return o


# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def campo_mat():
    """Fita de campo da IA: violeta, emissiva e meio transparente."""
    m = bpy.data.materials.new('Campo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.42, 0.06, 1.0, 1)
    em.inputs['Strength'].default_value = 5.0
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.7
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.85, ferrugem=0.25),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'torre': mats.material('Torre', (0.56, 0.56, 0.53), 0, 0.5, desgaste=0.75, sujeira=0.9, ferrugem=0.4),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'parafuso': mats.material('Parafuso', (0.22, 0.10, 0.04), 0.5, 0.8, pintura=False, ferrugem=1.0, sujeira=0.8),
    'disco': mats.material('Disco de freio', (0.50, 0.48, 0.47), 1.0, 0.3, pintura=False, ferrugem=0.5, sujeira=0.4,
                           escovado=True),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.03, 0.03, 0.03), 0, 0.75, pintura=False, sujeira=0.4, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.025, 0.025, 0.028), 0, 0.55, pintura=False, sujeira=0.5, desgaste=0.0),
    'cabo_aco': mats.material('Cabo de aço', (0.32, 0.31, 0.29), 1.0, 0.45, pintura=False, ferrugem=0.5, sujeira=0.7),
    'pa': mats.material('Compósito', (0.66, 0.66, 0.62), 0, 0.45, desgaste=0.9, sujeira=0.75, ferrugem=0.22),
    'pa_gasta': mats.material('Compósito erodido', (0.34, 0.32, 0.28), 0, 0.85, pintura=False, sujeira=0.9,
                              desgaste=0.0, ferrugem=0.3),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.014, 0.010, 0.006), 0, 0.07, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem_mancha': mats.material('Mancha de ferrugem', (0.28, 0.10, 0.03), 0, 0.85, pintura=False, sujeira=0.0,
                                     desgaste=0.0),
    'terra': mats.material('Terra', (0.16, 0.12, 0.08), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'violeta': luz_mat('Violeta', (0.55, 0.16, 1.0), 7.0),
    'ambar_pisca': luz_mat('Âmbar pisca', (1.0, 0.45, 0.05), 6.0),
    'campo': campo_mat(),
})

# ------------------------------------------------------------------ medidas
Z_LAJE = 0.08
Z_PED = 0.22                 # topo do pedestal de concreto
Z_CHAPA = 0.25               # topo da chapa de base
Z_T0, Z_TOP = 0.29, 2.55     # torre
DZ = -0.15                   # a nacele é desenhada com o topo em 2,70 e descida DZ
R0, R1 = 0.20, 0.12          # raio de vértice embaixo / em cima
Z_ANEL = 2.79                # topo da coroa dentada
Z_HUB = 2.96                 # eixo do rotor
X_HUB = 0.50                 # balanço do rotor à frente do eixo da torre
R_PA = 0.95
Y0 = math.radians(-35)       # guinada média (vento vindo de leste-sudeste)
COS8 = math.cos(PI / 8)


def rt(z):
    return R0 + (R1 - R0) * (z - Z_T0) / (Z_TOP - Z_T0)


def apo(z):
    return rt(z) * COS8


def face(k):
    """Direção para fora e tangente da face k da torre."""
    a = k * PI / 4
    return Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))


# ------------------------------------------------------------------ laje, pedestal e chapa de base
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z_LAJE))
obj('laje', bm, 'concreto')
bm = bmesh.new()
caixa_de(bm, (-0.985, -0.985, 0.0), (0.985, -0.965, Z_LAJE + 0.002))
caixa_de(bm, (-0.985, 0.965, 0.0), (0.985, 0.985, Z_LAJE + 0.002))
obj('laje_listras', bm, 'listras')
bm = bmesh.new()
octo(bm, Z_LAJE, Z_PED, 0.42, 0.40)
obj('pedestal', bm, 'concreto')
bm = bmesh.new()
octo(bm, Z_PED, Z_CHAPA, 0.32, 0.32)
octo(bm, Z_CHAPA, Z_T0, R0 + 0.06, R0 + 0.06)                            # flange da base da torre
for k in range(8):                                                       # mãos-francesas (nervuras soldadas)
    d, t = face(k)
    for s in (-0.35, 0.35):
        p = d * (apo(Z_T0) + 0.05) + t * s * 0.11
        p0 = d * (apo(Z_T0) - 0.01) + t * s * 0.11
        bloco(bm, (p + p0) / 2 + Vector((0, 0, Z_T0 + 0.05)), d, t, Vector((0, 0, 1)), (0.06, 0.012, 0.1))
obj('chapa_base', bm, 'grafite')
bm = bmesh.new()                                                         # chumbadores com porca e arruela
bf = bmesh.new()
for k in range(8):
    d, t = face(k)
    for s in (-0.45, 0.45):
        a = math.atan2(d.y, d.x) + s * 0.38
        p = Vector((math.cos(a), math.sin(a), 0)) * 0.285
        cil(bm, p + Vector((0, 0, Z_CHAPA + 0.002)), 0.022, 0.004, lados=12)
        cil(bm, p + Vector((0, 0, Z_CHAPA + 0.011)), 0.018, 0.014, lados=6)
        cil(bm, p + Vector((0, 0, Z_CHAPA + 0.03)), 0.009, 0.026, lados=10)
        mancha(bf, p * 1.04, 0.035, Z_CHAPA + 0.0008)
        mancha(bf, p * 1.08 + Vector((0, 0, 0)), 0.02, Z_CHAPA + 0.0008)
obj('chumbadores', bm, 'parafuso')
obj('ferrugem_base', bf, 'ferrugem_mancha')

# ------------------------------------------------------------------ torre
bm = bmesh.new()
octo(bm, Z_T0, Z_TOP, R0, R1)
obj('torre', bm, 'torre')
bm = bmesh.new()
bp = bmesh.new()
bf = bmesh.new()
for zf in (1.15, 2.0):
    r = rt(zf)
    octo(bm, zf - 0.022, zf + 0.022, r + 0.032, r + 0.032)
    for k in range(8):
        d, t = face(k)
        hw = r * math.sin(PI / 8)
        for s in (-0.45, 0.45):
            p = d * (apo(zf) + 0.017) + t * s * hw
            cil(bp, p + Vector((0, 0, zf + 0.029)), 0.008, 0.014, lados=6)
            cil(bp, p + Vector((0, 0, zf - 0.029)), 0.008, 0.014, lados=6)
            cil(bp, p + Vector((0, 0, zf + 0.042)), 0.0045, 0.012, lados=8)
        # escorrido de ferrugem abaixo da flange
        for s in (-0.45, 0.45):
            if random.random() < 0.6:
                h = random.uniform(0.05, 0.16)
                z1 = zf - 0.024
                p = d * (apo(z1 - h / 2) + 0.0012) + t * s * hw
                bloco(bf, p + Vector((0, 0, z1 - h / 2)), d, t, Vector((0, 0, 1)), (0.001, 0.012, h))
octo(bm, 1.60 - 0.035, 1.60 + 0.035, rt(1.6) + 0.014, rt(1.6) + 0.014)  # colar dos estais
obj('flanges', bm, 'grafite')
obj('parafusos_flange', bp, 'parafuso')
obj('ferrugem_flange', bf, 'ferrugem_mancha')

# ------------------------------------------------------------------ óleo escorrendo da vedação de guinada pela torre
bm = bmesh.new()
for k, comp, w0 in ((1, 1.55, 0.026), (2, 0.85, 0.018), (6, 2.05, 0.03), (7, 0.55, 0.014), (3, 1.25, 0.02)):
    d, t = face(k)
    u0 = random.uniform(-0.02, 0.02)
    fase = random.uniform(0, 6)
    zs = []
    z = Z_TOP - 0.005
    while z > Z_TOP - comp:
        zs.append(z)
        z -= 0.012
    pts = []
    for i, z in enumerate(zs):
        fr = i / (len(zs) - 1)
        w = w0 * (0.65 + 0.35 * math.sin(z * 23 + fase)) * (1 - fr ** 3) + 0.002
        u = u0 + 0.008 * math.sin(z * 7 + fase)
        afast = apo(z) + 0.0015
        for zf in (1.15, 2.0, 1.6):                                      # passa por cima das flanges e do colar
            r_f = rt(zf) + (0.032 if zf != 1.6 else 0.014)
            if abs(z - zf) < (0.026 if zf != 1.6 else 0.039):
                afast = r_f * COS8 + 0.0015
        c = d * afast + t * u + Vector((0, 0, z))
        pts.append((bm.verts.new(c - t * w / 2), bm.verts.new(c + t * w / 2)))
    for (a0, a1), (b0, b1) in zip(pts, pts[1:]):
        bm.faces.new((a0, a1, b1, b0))
obj('oleo_torre', bm, 'oleo')
bm = bmesh.new()                                                         # poça na chapa de base e no pedestal
mancha(bm, face(6)[0] * 0.26, 0.09, Z_CHAPA + 0.0012)
mancha(bm, face(1)[0] * 0.26, 0.06, Z_CHAPA + 0.0012)
mancha(bm, face(6)[0] * 0.43 + Vector((0.03, 0, 0)), 0.11, Z_LAJE + 0.001)
obj('oleo_poca', bm, 'oleo')

# ------------------------------------------------------------------ estais com esticadores
bm_bloco, bm_aco, bm_cabo, bm_par = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
bt = bmesh.new()
for k in (1, 3, 5, 7):
    d, t = face(k)
    canto = Vector((d.x, d.y, 0)) * 1.13                                  # (±0,80, ±0,80)
    caixa(bm_bloco, canto + Vector((0, 0, Z_LAJE + 0.05)), (0.18, 0.18, 0.1),
          Matrix.Rotation(k * PI / 4, 3, 'Z'))
    for s in (-1, 1):                                                    # parafusos do olhal no bloco
        for s2 in (-1, 1):
            p = canto + d * 0.04 * s2 + t * 0.045 * s + Vector((0, 0, Z_LAJE + 0.1))
            cil(bm_par, p + Vector((0, 0, 0.007)), 0.008, 0.014, lados=6)
    mancha(bt, canto - d * 0.02, 0.17, Z_LAJE + 0.001)
    # olhal no bloco
    A = canto + Vector((0, 0, Z_LAJE + 0.1))
    bloco(bm_aco, A + Vector((0, 0, 0.004)), d, t, Vector((0, 0, 1)), (0.12, 0.08, 0.008))
    lug = A + Vector((0, 0, 0.045))
    # ponto no colar
    L = d * (apo(1.6) + 0.014 * COS8 + 0.06) + Vector((0, 0, 1.6))
    u = (L - lug).normalized()
    lado = t
    nrm = u.cross(lado).normalized()
    bloco(bm_aco, lug - Vector((0, 0, 0.02)), d, t, Vector((0, 0, 1)), (0.05, 0.012, 0.05))      # orelha do olhal
    bloco(bm_aco, d * (apo(1.6) + 0.03) + Vector((0, 0, 1.6)), d, t, Vector((0, 0, 1)), (0.075, 0.012, 0.06))
    cil(bm_par, d * (apo(1.6) + 0.055) + Vector((0, 0, 1.6)), 0.009, 0.03, t, lados=10)  # pino no colar
    cil(bm_par, lug - Vector((0, 0, 0.01)), 0.009, 0.03, t, lados=10)                      # pino no olhal
    toro(bm_aco, lug + u * 0.012, 0.016, 0.004, t, nR=20, nr=6)          # manilha
    # esticador: corpo aberto com duas barras e bossas, varões rosqueados
    e0 = lug + u * 0.05
    e1 = e0 + u * 0.15
    tubo(bm_par, lug + u * 0.022, e0 + u * 0.01, 0.006, 10)
    tubo(bm_par, e1 - u * 0.01, e1 + u * 0.045, 0.006, 10)
    for e in (e0, e1):
        cil(bm_aco, e, 0.012, 0.022, u, lados=12)
    for s in (-1, 1):
        tubo(bm_aco, e0 + nrm * 0.011 * s, e1 + nrm * 0.011 * s, 0.0045, 8)
    # cabo de aço até o colar
    tubo(bm_cabo, e1 + u * 0.04, L - u * 0.005, 0.0045, 8)
    toro(bm_cabo, L - u * 0.012, 0.012, 0.004, t, nR=16, nr=6)           # sapatilha do cabo no colar
    for i in range(3):                                                   # grampos do cabo
        cil(bm_par, e1 + u * (0.08 + 0.03 * i), 0.008, 0.012, u, lados=6)
    for _ in range(4):
        random_p = canto + Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), Z_LAJE))
        pedra(bt, random_p, random.uniform(0.012, 0.025))
obj('blocos_ancoragem', bm_bloco, 'concreto')
suavizar(obj('estais_ferragens', bm_aco, 'aco'))
suavizar(obj('estais_cabos', bm_cabo, 'cabo_aco'))
suavizar(obj('estais_parafusos', bm_par, 'parafuso'))
obj('terra_estais', bt, 'terra')

# ------------------------------------------------------------------ eletrocalha na face oeste com cabos até o armário inversor
KC = 4
d, t = face(KC)
Z_C0, Z_C1 = 0.45, 2.33
bm_calha, bm_cab, bm_supo = bmesh.new(), bmesh.new(), bmesh.new()


def na_calha(z, off, u=0.0):
    return d * (apo(z) + off) + t * u + Vector((0, 0, z))


a, b = na_calha(Z_C0, 0.0), na_calha(Z_C1, 0.0)
ez = (b - a).normalized()
ex = d
ey = t
n = 0
for (o0, o1, u0, u1) in ((0.052, 0.058, -0.04, 0.04), (0.058, 0.09, -0.04, -0.034), (0.058, 0.09, 0.034, 0.04)):
    p0 = (na_calha(Z_C0, (o0 + o1) / 2, (u0 + u1) / 2) + na_calha(Z_C1, (o0 + o1) / 2, (u0 + u1) / 2)) / 2
    L = (na_calha(Z_C1, 0) - na_calha(Z_C0, 0)).length
    bloco(bm_calha, p0, ex, ey, ez, (o1 - o0, u1 - u0, L))
obj('eletrocalha', bm_calha, 'grafite')
z = Z_C0 + 0.12
while z < Z_C1:
    sk = any(abs(z - zf) < 0.06 for zf in (1.15, 2.0, 1.6))
    if not sk:
        bloco(bm_supo, na_calha(z, 0.026), ex, ey, ez, (0.052, 0.05, 0.03))                  # suporte (mão)
        bloco(bm_supo, na_calha(z, 0.084), ex, ey, ez, (0.004, 0.084, 0.012))                 # abraçadeira
    z += 0.3
obj('eletrocalha_suportes', bm_supo, 'aco')
bm_supo = bmesh.new()
for u in (-0.02, 0.0, 0.02):
    tubo(bm_cab, na_calha(Z_C0, 0.069, u), na_calha(Z_C1, 0.069, u), 0.0085, 10)
# caixa de junção no alto, com prensa-cabo entrando na torre
cj = na_calha(Z_C1 + 0.07, 0.07)
bm = bmesh.new()
bloco(bm, cj, ex, ey, Vector((0, 0, 1)), (0.075, 0.12, 0.16))
bloco(bm, na_calha(Z_C1 + 0.09, 0.02), ex, ey, Vector((0, 0, 1)), (0.04, 0.05, 0.04))  # conduto até a parede da torre
obj('caixa_juncao', bm, 'grafite')
bm = bmesh.new()
caixa(bm, cj + d * 0.039 + Vector((0, 0, 0.04)), (0.004, 0.02, 0.01), Matrix.Rotation(KC * PI / 4, 3, 'Z'))
obj('led_juncao', bm, 'ambar_pisca')
# armário inversor ao pé da torre (oeste)
ARM0, ARM1 = Vector((-0.93, -0.17, Z_LAJE + 0.03)), Vector((-0.63, 0.17, 0.60))
bm = bmesh.new()
caixa_de(bm, ARM0, ARM1)
for yy in (-0.12, 0.12):
    caixa_de(bm, (ARM0.x + 0.02, yy - 0.03, Z_LAJE), (ARM1.x - 0.02, yy + 0.03, Z_LAJE + 0.03))     # pés
obj('armario', bm, 'grafite')
bm = bmesh.new()
for i in range(9):                                                       # aletas do dissipador no topo
    x = ARM0.x + 0.03 + i * 0.03
    caixa_de(bm, (x - 0.004, -0.15, 0.60), (x + 0.004, 0.15, 0.66))
obj('armario_aletas', bm, 'aco')
bm = bmesh.new()
for yy in (-0.171, 0.171):
    for i in range(4):
        caixa(bm, (ARM0.x + 0.07, yy, 0.50 - i * 0.04), (0.02, 0.004, 0.014))
obj('armario_leds', bm, 'violeta')
bm = bmesh.new()
caixa(bm, (ARM0.x + 0.18, -0.171, 0.30), (0.12, 0.003, 0.08))
obj('armario_aviso', bm, 'listras')
# cabos: fundo da calha → lateral do armário (prensa-cabos)
for i, u in enumerate((-0.02, 0.0, 0.02)):
    p0 = na_calha(Z_C0, 0.069, u)
    p3 = Vector((ARM1.x + 0.01, u * 2.5, 0.40 - i * 0.04))
    pts = bezier(p0, p0 - ez * 0.18, p3 + Vector((0.15, 0, 0)), p3, 14)
    mangueira(bm_cab, pts, 0.0085)
    cil(bm_supo, p3 + Vector((0.005, 0, 0)), 0.014, 0.018, Vector((1, 0, 0)), lados=6)
# saída para a rede: conduto do armário descendo para a laje (borda oeste)
p0 = Vector((ARM0.x + 0.06, 0.0, ARM0.z))
tubo(bm_supo, Vector((ARM0.x - 0.03, 0.0, 0.2)), Vector((ARM0.x, 0.0, 0.2)), 0.02, 12)
mangueira(bm_cab, bezier((ARM0.x - 0.02, 0, 0.2), (ARM0.x - 0.05, 0, 0.2), (-0.975, 0, 0.14), (-0.975, 0, Z_LAJE - 0.02), 8), 0.016)
suavizar(obj('cabos_torre', bm_cab, 'cabo'))
obj('prensa_cabos', bm_supo, 'aco')

# ------------------------------------------------------------------ topo da torre: adaptador e coroa dentada fixa
bm = bmesh.new()
cil(bm, (0, 0, Z_TOP + 0.015), 0.17, 0.03, lados=32)
cil(bm, (0, 0, Z_ANEL + DZ - 0.03), 0.19, 0.06, lados=48)
N_COROA = 44
for j in range(N_COROA):
    a = j * 2 * PI / N_COROA
    caixa(bm, (0.196 * math.cos(a), 0.196 * math.sin(a), Z_ANEL + DZ - 0.03), (0.013, 0.012, 0.058),
          Matrix.Rotation(a, 3, 'Z'))
obj('coroa_dentada', bm, 'ferro')
bm = bmesh.new()
for j in range(16):
    a = j * 2 * PI / 16 + 0.1
    cil(bm, (0.155 * math.cos(a), 0.155 * math.sin(a), Z_TOP + 0.036), 0.009, 0.012, lados=6)
obj('parafusos_topo', bm, 'parafuso')

# ------------------------------------------------------------------ nacele (gira em Z no eixo da torre)
nacele = vazio('nacele', (0, 0, 0))
XR, XF, YW, ZB, ZT = -0.48, 0.30, 0.17, 2.84, 3.10
bm = bmesh.new()                                                         # chassi (bedplate): disco + viga
cil(bm, (0, 0, Z_ANEL + 0.025), 0.22, 0.05, lados=40)
caixa_de(bm, (XR + 0.02, -0.155, 2.80), (0.32, 0.155, ZB))
obj('chassi', bm, 'ferro', nacele)

# motores de guinada: pinhões rolam na coroa
R_PRIM = 0.196
R_PIN = R_PRIM * 8 / N_COROA
D_PIN = R_PRIM + R_PIN
passo = 2 * PI / N_COROA
pinhoes = []
for b_alvo in (math.radians(100), math.radians(-100)):
    j = round((b_alvo + Y0) / passo - 0.5)
    beta = (j + 0.5) * passo - Y0
    c = Vector((math.cos(beta), math.sin(beta), 0)) * D_PIN
    lado = 1 if c.y > 0 else -1
    bm = bmesh.new()
    caixa(bm, c * 0.8 + Vector((0, 0, Z_ANEL + 0.02)), (0.11, 0.1, 0.04), Matrix.Rotation(beta, 3, 'Z'))  # braço
    cil(bm, c + Vector((0, 0, Z_ANEL + 0.07)), 0.04, 0.06, lados=20)     # redutor
    obj('redutor_guinada_%d' % len(pinhoes), bm, 'grafite', nacele)
    bm = bmesh.new()
    cil(bm, c + Vector((0, 0, Z_ANEL + 0.155)), 0.034, 0.11, lados=20)   # motor
    cil(bm, c + Vector((0, 0, Z_ANEL + 0.215)), 0.03, 0.01, lados=20)
    obj('motor_guinada_%d' % len(pinhoes), bm, 'amarelo', nacele)
    bm = bmesh.new()
    for i in range(10):                                                  # aletas do motor
        a = i * 2 * PI / 10
        caixa(bm, c + Vector((0.038 * math.cos(a), 0.038 * math.sin(a), Z_ANEL + 0.155)), (0.009, 0.003, 0.1),
              Matrix.Rotation(a, 3, 'Z'))
    for i in range(6):                                                   # parafusos da flange do redutor
        a = i * PI / 3
        cil(bm, c + Vector((0.034 * math.cos(a), 0.034 * math.sin(a), Z_ANEL + 0.104)), 0.005, 0.008, lados=6)
    obj('motor_guinada_aletas_%d' % len(pinhoes), bm, 'parafuso', nacele)
    # caixa de ligação e cabo até a lateral do chassi
    cxl = c + Vector((0, 0, Z_ANEL + 0.17)) - Vector((c.x, c.y, 0)).normalized() * 0.04 + Vector((0.035, 0, 0))
    bm = bmesh.new()
    caixa(bm, cxl, (0.03, 0.02, 0.035))
    obj('motor_guinada_caixa_%d' % len(pinhoes), bm, 'grafite', nacele)
    bm = bmesh.new()
    p0 = cxl + Vector((0.018, 0, -0.005))
    p3 = Vector((p0.x + 0.06, lado * 0.157, 2.82))
    mangueira(bm, bezier(p0, p0 + Vector((0.04, 0, 0)), p3 + Vector((0, lado * 0.04, 0.02)), p3, 8), 0.006)
    cil(bm, p3, 0.01, 0.01, Vector((0, 1, 0)), lados=6)
    suavizar(obj('motor_guinada_cabo_%d' % len(pinhoes), bm, 'cabo', nacele))
    # pinhão (objeto próprio, gira enquanto a nacele guina)
    pin = vazio('pinhao_%d' % len(pinhoes), c + Vector((0, 0, Z_ANEL - 0.03)), nacele)
    bm = bmesh.new()
    cil(bm, (0, 0, 0), R_PIN - 0.006, 0.058, lados=16)
    for i in range(8):
        a = i * PI / 4
        caixa(bm, ((R_PIN + 0.0005) * math.cos(a), (R_PIN + 0.0005) * math.sin(a), 0), (0.012, 0.011, 0.056),
              Matrix.Rotation(a, 3, 'Z'))
    obj('pinhao_dentes_%d' % len(pinhoes), bm, 'aco', pin)
    pinhoes.append((pin, beta))

# carenagem: paredes, trilhos e cantoneiras
bm = bmesh.new()
caixa_de(bm, (XR, -YW, ZB), (XR + 0.015, YW, ZT))                         # traseira
caixa_de(bm, (XF - 0.015, -YW, ZB), (XF, YW, Z_HUB - 0.06))               # frente (com passagem do eixo)
caixa_de(bm, (XF - 0.015, -YW, Z_HUB + 0.06), (XF, YW, ZT))
caixa_de(bm, (XF - 0.015, -YW, Z_HUB - 0.06), (XF, -0.06, Z_HUB + 0.06))
caixa_de(bm, (XF - 0.015, 0.06, Z_HUB - 0.06), (XF, YW, Z_HUB + 0.06))
caixa_de(bm, (XR, YW - 0.015, ZB), (XF, YW, ZT))                          # lateral +y fixa
caixa_de(bm, (XR, -YW, ZT - 0.015), (-0.08, YW, ZT))                      # teto traseiro fixo
obj('carenagem', bm, 'amarelo', nacele)
bm = bmesh.new()
for y0 in (-YW, YW - 0.022):                                              # trilhos superiores
    caixa_de(bm, (XR, y0, ZT - 0.02), (XF, y0 + 0.022, ZT + 0.006))
caixa_de(bm, (XF - 0.02, -YW, ZT - 0.02), (XF, YW, ZT + 0.006))
caixa_de(bm, (-0.1, -YW, ZT - 0.02), (-0.08, YW, ZT + 0.006))
for x0 in (XR, XF - 0.02):                                                # montantes do lado aberto
    caixa_de(bm, (x0, -YW, ZB), (x0 + 0.02, -YW + 0.02, ZT))
caixa_de(bm, (XR, -YW, ZB), (XF, -YW + 0.02, ZB + 0.02))                  # soleira
obj('carenagem_quadro', bm, 'grafite', nacele)
bm = bmesh.new()                                                          # moldura de perigo na abertura do teto
caixa_de(bm, (-0.1, -YW, ZT + 0.006), (-0.08, YW, ZT + 0.008))
caixa_de(bm, (XF - 0.02, -YW, ZT + 0.006), (XF, YW, ZT + 0.008))
obj('teto_listras', bm, 'listras', nacele)
bm = bmesh.new()                                                          # luzes-guia do drone nos cantos
for x in (-0.09, XF - 0.01):
    for y in (-YW + 0.01, YW - 0.01):
        cil(bm, (x, y, ZT + 0.012), 0.007, 0.01, lados=10)
obj('luzes_drone', bm, 'ambar_pisca', nacele)
bm = bmesh.new()                                                          # venezianas na lateral +y
for i in range(5):
    z = ZB + 0.06 + i * 0.03
    bloco(bm, Vector((-0.30, YW + 0.006, z)), Vector((1, 0, 0)), Vector((0, math.cos(0.6), -math.sin(0.6))),
          Vector((0, math.sin(0.6), math.cos(0.6))), (0.16, 0.022, 0.003))
caixa_de(bm, (-0.385, YW, ZB + 0.04), (-0.215, YW + 0.004, ZB + 0.05))
caixa_de(bm, (-0.385, YW, ZB + 0.19), (-0.215, YW + 0.004, ZB + 0.20))
obj('venezianas', bm, 'grafite', nacele)
bm = bmesh.new()
caixa_de(bm, (0.0, YW, ZT - 0.05), (0.26, YW + 0.003, ZT - 0.042))       # faixa de status da IA
obj('faixa_status', bm, 'violeta', nacele)
bm = bmesh.new()                                                          # olhais de içamento no teto traseiro
for y in (-0.12, 0.12):
    toro(bm, (-0.43, y, ZT + 0.018), 0.014, 0.004, (0, 1, 0), nR=16, nr=6)
obj('olhais', bm, 'aco', nacele)
bm = bmesh.new()                                                          # óleo: lateral +y e embaixo do chassi
for x0, h in ((-0.28, 0.12), (0.12, 0.2), (0.22, 0.09)):
    caixa_de(bm, (x0, YW + 0.0008, ZB + 0.002), (x0 + 0.012, YW + 0.0015, ZB + h))
    caixa_de(bm, (x0 - 0.003, YW + 0.0008, ZB + 0.002), (x0 + 0.015, YW + 0.0015, ZB + 0.02))
mancha(bm, (0.03, 0.0, ZB + 0.0008), 0.07, ZB + 0.0008)
obj('oleo_nacele', bm, 'oleo', nacele)

# painel lateral -y aberto (asa de gaivota) com amortecedores a gás
DOB = (0, -0.866, 0.5)
ESP = (0, 0.5, 0.866)
dob, esp = Vector(DOB), Vector(ESP)
H = Vector((0, -YW, ZT))
bm = bmesh.new()
bloco(bm, H + dob * 0.13 + esp * 0.007 + Vector((-0.09, 0, 0)), (1, 0, 0), dob, esp, (0.74, 0.26, 0.012))
obj('painel_lateral', bm, 'amarelo', nacele)
bm = bmesh.new()
for x in (-0.40, -0.09, 0.22):                                           # dobradiças
    cil(bm, H + Vector((x, -0.004, 0.004)), 0.009, 0.05, Vector((1, 0, 0)), lados=10)
bloco(bm, H + dob * 0.13 - esp * 0.004 + Vector((-0.09, 0, 0)), (1, 0, 0), dob, esp, (0.7, 0.012, 0.01))  # nervura
obj('painel_lateral_ferragens', bm, 'grafite', nacele)
bm = bmesh.new()
bh = bmesh.new()
for x in (-0.36, 0.18):
    p0 = Vector((x, -YW + 0.002, ZB + 0.03))
    p1 = H + dob * 0.17 - esp * 0.005 + Vector((x - H.x, 0, 0))
    u = (p1 - p0).normalized()
    m = p0 + (p1 - p0) * 0.55
    tubo(bm, p0 + u * 0.01, m, 0.011, 12)                                 # cilindro
    tubo(bh, m - u * 0.01, p1 - u * 0.008, 0.0055, 10)                   # haste cromada
    cil(bm, p0, 0.012, 0.024, Vector((1, 0, 0)), lados=10)               # olhal de baixo
    cil(bm, p1, 0.01, 0.022, Vector((1, 0, 0)), lados=10)                # olhal de cima
suavizar(obj('amortecedores', bm, 'grafite', nacele))
suavizar(obj('amortecedores_hastes', bh, 'disco', nacele))

# escotilha do teto aberta (articulada no trilho +y) — acesso do drone
DOB2 = Vector((0, 0.574, 0.819))
ESP2 = Vector((0, -0.819, 0.574))
H2 = Vector((0.1, YW, ZT + 0.006))
bm = bmesh.new()
bloco(bm, H2 + DOB2 * 0.17 - ESP2 * 0.007, (1, 0, 0), DOB2, ESP2, (0.36, 0.34, 0.012))
obj('escotilha', bm, 'amarelo', nacele)
bm = bmesh.new()
bloco(bm, H2 + DOB2 * 0.17 + ESP2 * 0.0005, (1, 0, 0), DOB2, ESP2, (0.30, 0.28, 0.002))   # alvo de pouso no interno
obj('escotilha_alvo', bm, 'listras', nacele)
bm = bmesh.new()
for x in (-0.03, 0.23):
    cil(bm, H2 + Vector((x - H2.x, 0.004, 0.0)), 0.009, 0.05, Vector((1, 0, 0)), lados=10)
obj('escotilha_dobradicas', bm, 'grafite', nacele)

# trem de força: eixo, mancal, multiplicadora, freio, acoplamento, gerador
bm = bmesh.new()
tubo(bm, (0.20, 0, Z_HUB), (X_HUB - 0.06, 0, Z_HUB), 0.04, 24)
obj('eixo_principal', bm, 'aco', nacele)
bm = bmesh.new()
cil(bm, (XF - 0.008, 0, Z_HUB), 0.058, 0.03, Vector((1, 0, 0)), lados=24)  # vedação na frente
obj('vedacao', bm, 'borracha', nacele)
bm = bmesh.new()
caixa_de(bm, (0.215, -0.09, ZB), (0.275, 0.09, Z_HUB - 0.03))             # mancal principal
cil(bm, (0.245, 0, Z_HUB), 0.065, 0.06, Vector((1, 0, 0)), lados=24)
caixa_de(bm, (-0.02, -0.11, ZB + 0.02), (0.14, 0.11, 3.06))               # multiplicadora
cil(bm, (0.17, 0, Z_HUB), 0.09, 0.06, Vector((1, 0, 0)), lados=28)        # estágio planetário
for s in (-1, 1):                                                         # braços de torque
    caixa_de(bm, (0.03, s * 0.11, Z_HUB - 0.02), (0.09, s * 0.15, Z_HUB + 0.02))
    caixa_de(bm, (0.035, s * 0.12 - 0.015, ZB), (0.085, s * 0.12 + 0.015, Z_HUB - 0.03))
caixa_de(bm, (-0.03, -0.035, 2.955), (-0.02, 0.035, 3.025))               # tampa da saída rápida
obj('multiplicadora', bm, 'grafite', nacele)
bm = bmesh.new()
for s in (-1, 1):
    cil(bm, (0.06, s * 0.13, Z_HUB), 0.018, 0.05, Vector((0, 0, 1)), lados=14)   # buchas de borracha
obj('buchas', bm, 'borracha', nacele)
bm = bmesh.new()
for i in range(12):                                                       # parafusos da carcaça planetária
    a = i * PI / 6
    cil(bm, (0.2, 0.08 * math.cos(a), Z_HUB + 0.08 * math.sin(a)), 0.006, 0.008, Vector((1, 0, 0)), lados=6)
for x in (0.0, 0.06, 0.12):
    for y in (-0.105, 0.105):
        cil(bm, (x, y, 3.064), 0.006, 0.008, lados=6)
cil(bm, (0.04, -0.09, 3.07), 0.01, 0.02, lados=10)                        # bujões das mangueiras
cil(bm, (0.04, 0.06, 3.07), 0.01, 0.02, lados=10)
obj('multiplicadora_parafusos', bm, 'parafuso', nacele)
Z_HSS = 2.99
bm = bmesh.new()
tubo(bm, (-0.15, 0, Z_HSS), (-0.03, 0, Z_HSS), 0.018, 16)                 # eixo rápido
obj('eixo_rapido', bm, 'aco', nacele)
bm = bmesh.new()
cil(bm, (-0.055, 0, Z_HSS), 0.066, 0.012, Vector((1, 0, 0)), lados=40)
obj('disco_freio', bm, 'disco', nacele)
bm = bmesh.new()
for x in (-0.067, -0.043):                                                # pastilhas dos dois lados do disco
    caixa(bm, (x, 0, Z_HSS + 0.052), (0.008, 0.036, 0.026))
caixa_de(bm, (-0.075, -0.02, Z_HSS + 0.063), (-0.02, 0.02, Z_HSS + 0.085))   # ponte da pinça presa à multiplicadora
obj('pinca_freio', bm, 'amarelo', nacele)
bm = bmesh.new()
mangueira(bm, bezier((-0.075, 0.012, Z_HSS + 0.078), (-0.11, 0.03, Z_HSS + 0.085), (-0.12, 0.09, 3.0), (-0.1, 0.13, ZB + 0.02), 10), 0.004)
obj('mangueira_freio', bm, 'borracha', nacele)
bm = bmesh.new()
cil(bm, (-0.105, 0, Z_HSS), 0.034, 0.02, Vector((1, 0, 0)), lados=20)      # acoplamento flexível
cil(bm, (-0.125, 0, Z_HSS), 0.03, 0.012, Vector((1, 0, 0)), lados=20)
obj('acoplamento', bm, 'borracha', nacele)
bm = bmesh.new()
for i in range(6):
    a = i * PI / 3
    cil(bm, (-0.105, 0.026 * math.cos(a), Z_HSS + 0.026 * math.sin(a)), 0.005, 0.03, Vector((1, 0, 0)), lados=6)
obj('acoplamento_parafusos', bm, 'parafuso', nacele)
X_G0, X_G1 = -0.15, -0.43
R_GEN = 0.07
bm = bmesh.new()
cil(bm, ((X_G0 + X_G1) / 2, 0, Z_HSS), R_GEN, X_G0 - X_G1, Vector((1, 0, 0)), lados=32)
cil(bm, (X_G1 - 0.012, 0, Z_HSS), 0.06, 0.024, Vector((1, 0, 0)), lados=28)   # tampa traseira (ventilador)
for xx in (X_G0 - 0.04, X_G1 + 0.04):                                     # pés
    caixa_de(bm, (xx - 0.02, -0.075, ZB), (xx + 0.02, 0.075, Z_HSS - 0.05))
obj('gerador', bm, 'grafite', nacele)
bm = bmesh.new()
for i in range(20):                                                       # aletas radiais
    a = i * 2 * PI / 20 + PI / 20
    if math.sin(a) < -0.75:
        continue
    caixa(bm, ((X_G0 + X_G1) / 2, (R_GEN + 0.007) * math.cos(a), Z_HSS + (R_GEN + 0.007) * math.sin(a)),
          (X_G0 - X_G1 - 0.03, 0.014, 0.003), Matrix.Rotation(a, 3, 'X'))
obj('gerador_aletas', bm, 'aco', nacele)
bm = bmesh.new()
caixa_de(bm, (-0.33, 0.077, 2.95), (-0.25, 0.115, 3.02))                  # caixa de ligação
obj('gerador_caixa', bm, 'amarelo', nacele)
bm = bmesh.new()
bp = bmesh.new()
for i, dz in enumerate((-0.012, 0.0, 0.012)):
    p0 = Vector((-0.29 + dz, 0.105, 2.95))
    p3 = Vector((-0.07 + dz, 0.12, ZB + 0.01))
    mangueira(bm, bezier(p0, p0 - Vector((0, 0, 0.06)), p3 + Vector((-0.08, 0, 0.04)), p3, 12), 0.0065)
cil(bp, (-0.07, 0.12, ZB + 0.008), 0.03, 0.016, lados=16)                 # prensa-cabo no chassi (desce pela torre)
obj('cabos_gerador', bm, 'cabo', nacele)
obj('prensa_cabo_chassi', bp, 'aco', nacele)

bm = bmesh.new()                                                          # barra de luz interna (visão do drone)
caixa_de(bm, (-0.44, -0.01, ZT - 0.02), (-0.12, 0.01, ZT - 0.015))
obj('luz_interna', bm, 'lampada', nacele)
li = bpy.data.lights.new('Luz interna', 'POINT')
li.color = (1.0, 0.7, 0.4)
li.energy = 2.5
li.shadow_soft_size = 0.05
lio = bpy.data.objects.new('Luz interna', li)
sc.collection.objects.link(lio)
lio.parent = nacele
lio.location = (-0.15, -0.05, ZT - 0.05)

# radiador de óleo no teto com ventoinha e mangueiras até a multiplicadora
bm = bmesh.new()
caixa_de(bm, (-0.30, -0.15, ZT), (-0.10, 0.09, ZT + 0.055))
obj('radiador', bm, 'grafite', nacele)
bm = bmesh.new()
for i in range(16):
    x = -0.29 + i * 0.0125
    caixa_de(bm, (x, -0.152, ZT + 0.006), (x + 0.004, 0.092, ZT + 0.05))
obj('radiador_aletas', bm, 'aco', nacele)
bm = bmesh.new()
toro(bm, (-0.2, -0.03, ZT + 0.065), 0.07, 0.008, nR=32, nr=8)
for i in range(5):
    a = i * 2 * PI / 5
    d2 = Vector((math.cos(a), math.sin(a), 0))
    bloco(bm, Vector((-0.2, -0.03, ZT + 0.065)) + d2 * 0.035, d2, Vector((-d2.y, d2.x, 0)).normalized(),
          Vector((0, 0, 1)), (0.06, 0.025, 0.004))
cil(bm, (-0.2, -0.03, ZT + 0.065), 0.014, 0.02, lados=12)
for i in range(4):
    a = i * PI / 2 + PI / 4
    tubo(bm, Vector((-0.2 + 0.073 * math.cos(a), -0.03 + 0.073 * math.sin(a), ZT + 0.055)),
         Vector((-0.2 + 0.073 * math.cos(a), -0.03 + 0.073 * math.sin(a), ZT + 0.066)), 0.005, 6)
suavizar(obj('ventoinha', bm, 'grafite', nacele))
bm = bmesh.new()
for y, yf in ((-0.12, -0.09), (0.06, 0.06)):
    p0 = Vector((-0.10, y, ZT + 0.03))
    p3 = Vector((0.04, yf, 3.08))
    mangueira(bm, bezier(p0, p0 + Vector((0.07, 0, 0.03)), p3 + Vector((0, 0, 0.08)), p3, 12), 0.009)
suavizar(obj('mangueiras_oleo', bm, 'borracha', nacele))
bm = bmesh.new()
mancha(bm, (-0.06, -0.10, ZT + 0.001), 0.03, ZT + 0.0008)
caixa_de(bm, (-0.092, -0.125, ZT - 0.06), (-0.088, -0.115, ZT))          # escorrido no trilho
obj('oleo_radiador', bm, 'oleo', nacele)

# mastro: anemômetro de conchas e cata-vento
MX, MY = -0.42, 0.08
Z_M = 3.34
bm = bmesh.new()
cil(bm, (MX, MY, ZT + 0.005), 0.03, 0.01, lados=16)
tubo(bm, (MX, MY, ZT), (MX, MY, Z_M + 0.01), 0.011, 14)
tubo(bm, (MX, -0.05, Z_M), (MX, 0.21, Z_M), 0.007, 10)
tubo(bm, (MX, 0.20, Z_M), (MX, 0.20, Z_M + 0.05), 0.005, 8)
tubo(bm, (MX, -0.04, Z_M), (MX, -0.04, Z_M + 0.04), 0.005, 8)
suavizar(obj('mastro', bm, 'aco', nacele))
bm = bmesh.new()
cil(bm, (MX, MY, Z_M + 0.02), 0.012, 0.016, lados=12)
obj('sensor_mastro', bm, 'lampada', nacele)
bm = bmesh.new()
mangueira(bm, bezier((MX, MY + 0.012, Z_M - 0.02), (MX, MY + 0.02, 3.2), (MX + 0.01, MY + 0.03, ZT + 0.04), (MX + 0.03, MY + 0.04, ZT + 0.002), 8), 0.004)
obj('cabo_mastro', bm, 'cabo', nacele)
anemo = vazio('anemometro', (MX, 0.20, Z_M + 0.055), nacele)
bm = bmesh.new()
cil(bm, (0, 0, 0), 0.012, 0.016, lados=12)
bc = bmesh.new()
for i in range(3):
    a = i * 2 * PI / 3
    dr = Vector((math.cos(a), math.sin(a), 0))
    tg = Vector((-math.sin(a), math.cos(a), 0))
    tubo(bm, dr * 0.01, dr * 0.055, 0.0035, 6)
    res = bmesh.ops.create_uvsphere(bc, u_segments=14, v_segments=8, radius=0.019)
    vs = [v for v in res['verts'] if v.co.z > 0.001]
    bmesh.ops.delete(bc, geom=vs, context='VERTS')
    q = tg.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    novos = [v for v in bc.verts if not v.tag]
    bmesh.ops.transform(bc, matrix=Matrix.Translation(dr * 0.06) @ q, verts=novos)
    for v in novos:
        v.tag = True
suavizar(obj('anemometro_eixo', bm, 'aco', anemo))
suave_tudo(obj('anemometro_conchas', bc, 'grafite', anemo))
cata = vazio('catavento', (MX, -0.04, Z_M + 0.045), nacele)
bm = bmesh.new()
cil(bm, (0, 0, 0), 0.01, 0.014, lados=12)
tubo(bm, (0.05, 0, 0), (-0.11, 0, 0), 0.0035, 6)
cil(bm, (0.055, 0, 0), 0.008, 0.02, Vector((1, 0, 0)), lados=10, r2=0.0)
obj('catavento_haste', bm, 'aco', cata)
bm = bmesh.new()
caixa_de(bm, (-0.12, -0.0015, -0.015), (-0.065, 0.0015, 0.03))
obj('catavento_aleta', bm, 'amarelo', cata)

# ------------------------------------------------------------------ hélice (gira em X local, no cubo)
helice = vazio('helice', (X_HUB, 0, Z_HUB), nacele)
bm = bmesh.new()
revolver(bm, [(-0.06, 0.098), (-0.06, 0.112), (-0.02, 0.12), (0.03, 0.118), (0.075, 0.1), (0.115, 0.07),
              (0.145, 0.04), (0.162, 0.015), (0.166, 0.0)], lados=36)
suavizar(obj('girador', bm, 'amarelo', helice))
bm = bmesh.new()
cil(bm, (-0.068, 0, 0), 0.08, 0.016, Vector((1, 0, 0)), lados=28)         # flange do cubo no eixo
for i in range(12):
    a = i * PI / 6
    cil(bm, (-0.068, 0.068 * math.cos(a), 0.068 * math.sin(a)), 0.006, 0.024, Vector((1, 0, 0)), lados=6)
obj('cubo_flange', bm, 'parafuso', helice)
bm = bmesh.new()
cil(bm, (0.163, 0, 0), 0.012, 0.012, Vector((1, 0, 0)), lados=12)
obj('girador_ponta', bm, 'violeta', helice)


def corda(r):
    if r < 0.14:
        c = 0.06
    elif r < 0.24:
        c = 0.06 + (0.15 - 0.06) * (r - 0.14) / 0.10
    else:
        c = 0.15 + (0.04 - 0.15) * (r - 0.24) / (R_PA - 0.24)
    if r > R_PA - 0.05:
        c *= math.sqrt(max(0.08, (R_PA + 0.02 - r) / 0.07))
    return c


def suave01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


NS, NP = 48, 24
bm_pa = bmesh.new()
bm_rib = bmesh.new()
bm_no = bmesh.new()
bm_col = bmesh.new()
for kb in range(3):
    alfa = math.radians(105 + 120 * kb)
    dd = Vector((0, math.cos(alfa), math.sin(alfa)))
    T = Vector((0, -math.sin(alfa), math.cos(alfa)))
    X = Vector((1, 0, 0))
    lascas = {}
    for i in random.sample(range(int(NS * 0.45), NS - 2), 5):
        lascas[i] = random.choice(('ataque', 'ataque', 'fuga'))
    secoes, chs, cs_sec = [], [], []
    for i in range(NS):
        r = 0.09 + i * (R_PA - 0.09) / (NS - 1)
        C = corda(r)
        w = suave01((r - 0.14) / 0.08)
        tr = 0.30 + (0.14 - 0.30) * suave01((r - 0.24) / (R_PA - 0.24))
        th = math.radians(22 + (3 - 22) * max(0.0, (r - 0.14) / (R_PA - 0.14)))
        ch = -T * math.cos(th) - X * math.sin(th)
        nn = X * math.cos(th) - T * math.sin(th)
        anel, cs = [], []
        D = 0.06
        for j in range(NP):
            ph = 2 * PI * j / NP
            c = (1 - math.cos(ph)) / 2
            sg = 1 if math.sin(ph) >= 0 else -1
            xc, yc = D * c - D / 2, D / 2 * math.sin(ph)
            yt = 5 * (0.2969 * math.sqrt(c) - 0.126 * c - 0.3516 * c * c + 0.2843 * c ** 3 - 0.1036 * c ** 4)
            xa, ya = C * c - 0.3 * C, C * tr * yt * sg + C * 0.03 * math.sin(PI * c)
            x, y = xc * (1 - w) + xa * w, yc * (1 - w) + ya * w
            if i in lascas:                                               # lascas na borda
                if lascas[i] == 'ataque' and c < 0.14:
                    x += (0.14 - c) * C * 0.5
                    y *= 0.75
                if lascas[i] == 'fuga' and c > 0.82:
                    x -= (c - 0.82) * C * 0.6
            anel.append(bm_pa.verts.new(dd * r + ch * x + nn * y))
            cs.append(c)
        secoes.append(anel)
        chs.append((r, ch, C, w))
        cs_sec.append(cs)
    for i in range(NS - 1):
        r = chs[i][0]
        for j in range(NP):
            f = bm_pa.faces.new((secoes[i][j], secoes[i][(j + 1) % NP], secoes[i + 1][(j + 1) % NP],
                                 secoes[i + 1][j]))
            cj_ = cs_sec[i]
            if r > 0.3 and (cj_[j] < 0.09 or cj_[(j + 1) % NP] < 0.09):
                f.material_index = 1
    bm_pa.faces.new(list(reversed(secoes[0])))
    bm_pa.faces.new(secoes[-1])
    # colar de vedação da raiz no girador
    toro(bm_col, dd * 0.118, 0.036, 0.008, dd, nR=24, nr=8)
    # fita de campo na borda de fuga (metade externa) e emissores
    jte = NP // 2
    fita = []
    for i in range(NS):
        r, ch, C, w = chs[i]
        if r < 0.5:
            continue
        te = secoes[i][jte].co.copy()
        larg = 0.01 + 0.035 * (r - 0.5) / (R_PA - 0.5)
        fita.append((bm_rib.verts.new(te + ch * 0.004), bm_rib.verts.new(te + ch * (0.004 + larg))))
    for (a0, a1), (b0, b1) in zip(fita, fita[1:]):
        bm_rib.faces.new((a0, a1, b1, b0))
    for rr in (0.53, 0.66, 0.79):
        i = min(range(NS), key=lambda k: abs(chs[k][0] - rr))
        r, ch, C, w = chs[i]
        te = secoes[i][jte].co
        bloco(bm_no, te + ch * 0.002, ch, dd, ch.cross(dd).normalized(), (0.012, 0.012, 0.007))
    ponta = secoes[-1]
    pc = sum((v.co for v in ponta), Vector()) / NP
    cil(bm_no, pc + dd * 0.004, 0.008, 0.008, dd, lados=10)              # emissor da ponta
bmesh.ops.recalc_face_normals(bm_pa, faces=bm_pa.faces)
pas = obj('pas', bm_pa, 'pa', helice)
pas.data.materials.append(base3d.M['pa_gasta'])
suavizar(pas)
obj('pas_colares', bm_col, 'borracha', helice)
obj('pas_campo', bm_rib, 'campo', helice)
obj('pas_emissores', bm_no, 'violeta', helice)
luz_campo = []
for kb in range(3):
    alfa = math.radians(105 + 120 * kb)
    ld = bpy.data.lights.new('Luz campo %d' % kb, 'POINT')
    ld.color = (0.6, 0.25, 1.0)
    ld.energy = 3.0
    ld.shadow_soft_size = 0.1
    lo = bpy.data.objects.new('Luz campo %d' % kb, ld)
    sc.collection.objects.link(lo)
    lo.parent = helice
    lo.location = Vector((-0.03, math.cos(alfa), math.sin(alfa))) * 0.75
    lo.location.x = -0.03
    luz_campo.append(ld)

nacele.location.z = DZ                                                   # desce a nacele inteira para o topo da torre

# pedrinhas e pó em volta
bm = bmesh.new()
for _ in range(26):
    a = random.uniform(0, 2 * PI)
    rr = random.uniform(0.45, 0.95)
    p = Vector((math.cos(a) * rr, math.sin(a) * rr, Z_LAJE))
    if abs(p.x) < 0.97 and abs(p.y) < 0.97 and not (ARM0.x - 0.02 < p.x < ARM1.x + 0.02 and abs(p.y) < 0.2):
        pedra(bm, p, random.uniform(0.008, 0.02))
obj('pedrinhas', bm, 'terra')
bm = bmesh.new()
for _ in range(6):
    a = random.uniform(0, 2 * PI)
    mancha(bm, (math.cos(a) * 0.6, math.sin(a) * 0.6), random.uniform(0.08, 0.16), Z_LAJE + 0.0006)
obj('po_laje', bm, 'terra')

# ------------------------------------------------------------------ animação (laço de 4 s)
mat_campo = base3d.M['campo'].node_tree.nodes['Emission'].inputs['Strength']
mat_pisca = base3d.M['ambar_pisca'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 2):
    fr = (q - 1) / QUADROS
    psi = Y0 + 0.2 * math.sin(2 * PI * fr)
    nacele.rotation_euler = (0, 0, psi)
    nacele.keyframe_insert('rotation_euler', frame=q)
    helice.rotation_euler = (2 * PI * 2 * fr, 0, 0)                      # 2 voltas por laço (30 rpm)
    helice.keyframe_insert('rotation_euler', frame=q)
    for pin, beta in pinhoes:
        pin.rotation_euler = (0, 0, beta + PI + (N_COROA / 8) * (psi - Y0))
        pin.keyframe_insert('rotation_euler', frame=q)
    anemo.rotation_euler = (0, 0, 2 * PI * 6 * fr)
    anemo.keyframe_insert('rotation_euler', frame=q)
    cata.rotation_euler = (0, 0, 0.12 * math.sin(2 * PI * 3 * fr))
    cata.keyframe_insert('rotation_euler', frame=q)
    mat_campo.default_value = 5.0 + 1.5 * math.sin(2 * PI * 4 * fr)
    mat_campo.keyframe_insert('default_value', frame=q)
    for ld in luz_campo:
        ld.energy = 3.0 + 1.0 * math.sin(2 * PI * 4 * fr)
        ld.keyframe_insert('energy', frame=q)
    mat_pisca.default_value = 7.0 if (fr * 4) % 1.0 < 0.5 else 0.6
    mat_pisca.keyframe_insert('default_value', frame=q)


def linear(idb):
    ad = getattr(idb, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


for o in list(sc.objects) + luz_campo + [base3d.M['campo'].node_tree, base3d.M['ambar_pisca'].node_tree]:
    linear(o)

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


ALVO = (0.0, 0.0, 1.8)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
if modo in ('foto', 'perto'):
    sc.cycles.samples = 128
    sc.frame_set(1)
    if modo == 'foto':
        sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
        for i, (ang, alt) in enumerate(((300, 1.2), (210, 1.6), (120, 1.8), (30, 1.0))):
            a = math.radians(ang)
            mirar(Vector(ALVO) + Vector((math.cos(a) * 6.2, math.sin(a) * 6.2, alt)), ALVO, 36)
            sc.render.filepath = os.path.join(AQUI, 'turbina_eolica_%d.png' % i)
            bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
    # de perto: lado aberto da nacele (painel asa de gaivota), trem de força, motor de guinada
    R = Matrix.Rotation(Y0, 3, 'Z')
    centro = R @ Vector((-0.08, 0.0, 2.97 + DZ))
    fora = R @ Vector((0.25, -1.0, 0.0))
    mirar(centro + fora.normalized() * 1.45 + Vector((0, 0, 0.32)), centro + Vector((0, 0, -0.03)), 32)
    sc.render.filepath = os.path.join(AQUI, 'turbina_eolica_perto.png')
    bpy.ops.render.render(write_still=True)
print('TURBINA ok')
