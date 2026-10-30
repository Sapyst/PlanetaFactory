"""Estudo isolado (fora do jogo): o NÚCLEO, a unidade semeadora da IA que caiu do espaço, 3×3 tiles.
A cápsula de reentrada se abriu como flor: quatro pétalas de escudo térmico (placas ablativas chamuscadas, emendas,
rebites, bordas lascadas) cravadas no chão, cada uma aberta por dois pistões (camisa presa no corpo, haste no
suporte da pétala). Cratera rasa com chão rachado, terra revirada, pedras ejetadas e queimado radial. Corpo central
blindado com frestas de luz, gargantas nas quatro bocas (meio de cada lado) com esteira curta engolindo minério,
cabos grossos que descem por cima das pétalas e mergulham no chão como raízes. Garras no topo seguram um monólito de
cristal que flutua e pulsa; três anéis giram em eixos diferentes, fragmentos de cristal orbitam, arcos de energia
saltam das garras, e calor sobe dos respiros.
Uso: blender -b --python estudo_nucleo.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(23)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=64, nr=16, rot=Matrix.Identity(3)):
    """Anel tubular contínuo (sem emendas), no plano xy local girado por `rot`."""
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


def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat():
    """Cristal da IA: vidro violeta translúcido com brilho interno (a força é animada: pulsa)."""
    m = bpy.data.materials.new('Cristal')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Transmission Weight'].default_value = 0.35
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 2.0
    return m


def manta_mat():
    """Manta térmica dourada (MLI) amassada, com fuligem: a face de dentro da cápsula, exposta ao abrir."""
    m = bpy.data.materials.new('Manta')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Metallic'].default_value = 1.0
    tc = no(nt, 'ShaderNodeTexCoord')
    vor = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 75.0})
    nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.4, 'Distance': 0.01})
    nt.links.new(vor.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    suj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.7})
    nt.links.new(ru.outputs['Fac'], suj.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.78, 0.5, 0.16, 1)
    mix.inputs[7].default_value = (0.05, 0.035, 0.025, 1)
    nt.links.new(suj.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.22, 'To Max': 0.75})
    nt.links.new(suj.outputs['Result'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    return m


VIOLETA = (0.66, 0.42, 1.0)
base3d.M.update({
    'casco': mats.material('Casco', (0.11, 0.115, 0.125), 0, 0.45, desgaste=0.85, sujeira=0.9),
    'ablativo': mats.material('Ablativo', (0.085, 0.072, 0.064), 0, 0.85, desgaste=1.0, sujeira=1.0),
    'fuligem': mats.material('Fuligem', (0.015, 0.013, 0.012), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'chamusco': mats.material('Chamusco', (0.05, 0.04, 0.034), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'queimado': mats.material('Queimado', (0.22, 0.12, 0.06), 0.6, 0.6, pintura=False, ferrugem=0.8, sujeira=0.9),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.7, sujeira=0.8, escovado=True),
    'aneis': mats.material('Anéis', (0.3, 0.3, 0.32), 1.0, 0.3, pintura=False, ferrugem=0.3, sujeira=0.6, escovado=True),
    'grafite': mats.material('Grafite', (0.06, 0.065, 0.07), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.8),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.3, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.04, 0.04, 0.045), 0, 0.6, pintura=False, sujeira=0.6, desgaste=0.0),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'terra': mats.material('Terra', (0.12, 0.09, 0.07), 0, 0.95, sujeira=0.4, desgaste=0.0),
    'rocha': mats.material('Rocha', (0.2, 0.18, 0.16), 0, 0.9, sujeira=0.5, desgaste=0.0),
    'minerio': mats.material('Minério', (0.30, 0.13, 0.07), 0.2, 0.7, pintura=False, sujeira=0.5, ferrugem=0.5),
    'escuro': mats.material('Garganta', (0.004, 0.004, 0.005), 0, 1.0, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'fresta': emissivo('Fresta', VIOLETA, 6.0),
    'emissor': emissivo('Emissor', (0.5, 0.2, 1.0), 1.2, (0.12, 0.04, 0.3)),
    'arco': emissivo('Arco', (0.75, 0.6, 1.0), 25.0),
    'manta': manta_mat(),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 12.0),
    'led_ambar': emissivo('Led âmbar', (1.0, 0.5, 0.05), 12.0),
    'garganta_luz': emissivo('Garganta luz', VIOLETA, 0.6, (0.02, 0.01, 0.03)),
    'cristal': cristal_mat(),
    'calor': base3d.volume_mat('Calor', (0.85, 0.83, 0.9), 2.2, 0.8, 1.6),
})

R_CORPO, Z_CORPO = 0.62, 0.78
BOCAS = [0.0, PI / 2, PI, 3 * PI / 2]              # leste, norte, oeste, sul (meio de cada lado)
PETALAS = [PI / 4 + k * PI / 2 for k in range(4)]  # nas diagonais, entre as bocas
CM = Vector((0, 0, 1.9))                          # centro do monólito e dos anéis


def d_de(a):
    return Vector((math.cos(a), math.sin(a), 0))


# ------------------------------------------------------------------ cratera: terra revirada, borda, rachaduras, queimado
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.75)
for v in bm.verts:
    a = math.atan2(v.co.y, v.co.x)
    v.co *= 1 + 0.06 * math.sin(a * 5 + 1) + 0.04 * math.sin(a * 11)
    v.co.z = 0.003
obj('cratera', bm, 'terra')
bm = bmesh.new()                                                     # borda levantada (terra empurrada pela queda)
n = 56
for i in range(n):
    a = i * 2 * PI / n
    R = 1.62 * (1 + 0.06 * math.sin(a * 5 + 1) + 0.04 * math.sin(a * 11))
    if min(abs(math.remainder(a - b, 2 * PI)) for b in BOCAS) < 0.22:
        continue                                                     # esteiras passam: borda pisada
    pedra(bm, d_de(a) * R, random.uniform(0.09, 0.15), 0.35)
for k in range(70):                                                  # torrões e pedras ejetadas
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.6, 2.8)
    if min(abs(math.remainder(a - b, 2 * PI)) for b in BOCAS) < 0.12 and r < 2.4:
        continue
    pedra(bm, d_de(a) * r + Vector((0, 0, 0.01)), random.uniform(0.02, 0.07) * (2.2 / r), 0.6)
obj('torroes', bm, 'terra')
bm = bmesh.new()
for k in range(26):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.7, 3.0)
    pedra(bm, d_de(a) * r + Vector((0, 0, 0.015)), random.uniform(0.03, 0.08), 0.7)
obj('pedras', bm, 'rocha')


def fita(bm, pts, larg, alto=0.004):
    """Faixa fina sobre uma polilinha (rachadura, emenda, escorrido): normal para cima."""
    vs = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        lado = Vector((0, 0, 1)).cross(t).normalized() * larg / 2
        vs.append((bm.verts.new(p + lado + Vector((0, 0, alto))), bm.verts.new(p - lado + Vector((0, 0, alto)))))
    for (a0, a1), (b0, b1) in zip(vs, vs[1:]):
        bm.faces.new((a0, a1, b1, b0))


bm = bmesh.new()
for k in range(22):                                                  # rachaduras em zigue-zague, saindo da cratera
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.3, 1.6)
    p = d_de(a) * r
    pts = [p.copy()]
    for i in range(random.randint(4, 8)):
        a += random.uniform(-0.25, 0.25)
        p = p + d_de(a) * random.uniform(0.08, 0.18)
        pts.append(p.copy())
    fita(bm, pts, random.uniform(0.008, 0.02), 0.006)
obj('rachaduras', bm, 'escuro')
bm = bmesh.new()
for k in range(18):                                                  # queimado radial (raios de fuligem)
    a = random.uniform(0, 2 * PI)
    r0 = random.uniform(1.3, 1.7)
    comp = random.uniform(0.4, 1.2)
    pts = [d_de(a) * (r0 + comp * i / 6) for i in range(7)]
    larg = random.uniform(0.05, 0.16)
    vs = []
    for i, p in enumerate(pts):
        lado = Vector((0, 0, 1)).cross(d_de(a)) * larg * (1 - i / 7) / 2
        vs.append((bm.verts.new(p + lado + Vector((0, 0, 0.005))), bm.verts.new(p - lado + Vector((0, 0, 0.005)))))
    for (a0, a1), (b0, b1) in zip(vs, vs[1:]):
        bm.faces.new((a0, a1, b1, b0))
obj('queimado_chao', bm, 'chamusco')

# ------------------------------------------------------------------ corpo central blindado
bm = bmesh.new()
cil(bm, Vector((0, 0, Z_CORPO / 2)), R_CORPO, Z_CORPO, lados=24)
obj('corpo', bm, 'casco')
suavizar(bpy.data.objects['corpo'])
bm = bmesh.new()
toro(bm, Vector((0, 0, 0.1)), R_CORPO + 0.02, 0.055, 64, 14)         # anel estrutural da base (dobradiças)
toro(bm, Vector((0, 0, Z_CORPO)), R_CORPO - 0.02, 0.05, 64, 14)      # anel do topo
toro(bm, Vector((0, 0, 0.46)), R_CORPO + 0.008, 0.022, 64, 10)       # cinta do meio
suavizar(obj('aneis_corpo', bm, 'aco'))
bm, bf = bmesh.new(), bmesh.new()
for k in range(24):                                                  # nervuras verticais e frestas de luz
    a = k * 2 * PI / 24
    d = d_de(a)
    perto_boca = min(abs(math.remainder(a - b, 2 * PI)) for b in BOCAS) < 0.36
    caixa(bm, d * (R_CORPO + 0.012) + Vector((0, 0, 0.45)), (0.012, 0.035, 0.6), Matrix.Rotation(a, 3, 'Z'))
    if not perto_boca and k % 2:
        caixa(bf, d * (R_CORPO + 0.004) + Vector((0, 0, 0.6)), (0.008, 0.018, 0.2), Matrix.Rotation(a, 3, 'Z'))
        caixa(bf, d * (R_CORPO + 0.004) + Vector((0, 0, 0.29)), (0.008, 0.018, 0.1), Matrix.Rotation(a, 3, 'Z'))
obj('nervuras', bm, 'grafite')
obj('frestas', bf, 'fresta')
bm = bmesh.new()                                                     # andar de cima: tronco de cone com aletas
cil(bm, Vector((0, 0, Z_CORPO + 0.11)), R_CORPO - 0.05, 0.22, lados=24, r2=0.42)
obj('corpo_cone', bm, 'casco')
suavizar(bpy.data.objects['corpo_cone'])
bm = bmesh.new()
for k in range(32):
    a = k * 2 * PI / 32
    if min(abs(math.remainder(a - b, 2 * PI)) for b in PETALAS) < 0.18:
        continue                                                     # garras saem aqui
    d = d_de(a)
    v0 = d * (R_CORPO - 0.04) + Vector((0, 0, Z_CORPO + 0.01))
    v1 = d * 0.43 + Vector((0, 0, Z_CORPO + 0.21))
    viga(bm, v0 + d * 0.025, v1 + d * 0.025, 0.012)
obj('aletas', bm, 'aco')
Z_CORPO += 0.22
bm = bmesh.new()                                                     # tampa do topo, rebaixada, com respiros
cil(bm, Vector((0, 0, Z_CORPO + 0.02)), 0.43, 0.04, lados=24)
cil(bm, Vector((0, 0, Z_CORPO + 0.07)), 0.24, 0.08, lados=16)        # pedestal do emissor
obj('tampa', bm, 'grafite')
bm = bmesh.new()
cil(bm, Vector((0, 0, Z_CORPO + 0.115)), 0.17, 0.01, lados=16)       # emissor (luz sobe para o monólito)
obj('emissor', bm, 'emissor')
RESPIROS = []
bm, bg = bmesh.new(), bmesh.new()
for a in BOCAS:                                                      # respiros com grade, de onde sobe calor
    d = d_de(a)
    c = d * 0.34 + Vector((0, 0, Z_CORPO + 0.05))
    cil(bm, c, 0.06, 0.05, lados=14)
    for j in range(-2, 3):
        caixa(bg, c + Vector((0, 0, 0.027)) + Matrix.Rotation(a, 3, 'Z') @ Vector((0, j * 0.02, 0)), (0.1, 0.007, 0.006), Matrix.Rotation(a, 3, 'Z'))
    RESPIROS.append(c + Vector((0, 0, 0.04)))
obj('respiros', bm, 'aco')
obj('respiros_grade', bg, 'grafite')
bm = bmesh.new()                                                     # brilho no fundo dos respiros
for c in RESPIROS:
    cil(bm, c - Vector((0, 0, 0.005)), 0.05, 0.004, lados=14)
obj('respiros_luz', bm, 'garganta_luz')
bm, bl = bmesh.new(), bmesh.new()                                    # antenas pequenas e um prato no anel do topo
for k, a in enumerate((PI / 4 + 0.35, 3 * PI / 4 + 0.35, 5 * PI / 4 + 0.35)):
    p = d_de(a) * (R_CORPO - 0.03) + Vector((0, 0, Z_CORPO - 0.22 + 0.04))
    h = 0.25 + 0.12 * k
    tubo(bm, p, p + Vector((0, 0, h)), 0.008, 6)
    cil(bm, p + Vector((0, 0, 0.02)), 0.022, 0.04, lados=8)
    bmesh.ops.create_uvsphere(bl, u_segments=8, v_segments=6, radius=0.016, matrix=Matrix.Translation(p + Vector((0, 0, h))))
pp = d_de(7 * PI / 4 + 0.35) * (R_CORPO - 0.03) + Vector((0, 0, Z_CORPO - 0.22 + 0.04))
tubo(bm, pp, pp + Vector((0, 0, 0.12)), 0.012, 8)
cil(bm, pp + Vector((0, 0, 0.16)), 0.09, 0.015, d_de(7 * PI / 4 + 0.35) + Vector((0, 0, 0.8)), lados=16, r2=0.03)
obj('antenas', bm, 'aco')
obj('antenas_luz', bl, 'led_ambar')

# ------------------------------------------------------------------ bocas: garganta no corpo + esteira curta chegando
Z_ESTEIRA = 0.2
itens_esteira = []
calhas = []
for a in BOCAS:
    rot = Matrix.Rotation(a, 3, 'Z')
    d = d_de(a)
    bm, bs = bmesh.new(), bmesh.new()
    gc = d * (R_CORPO + 0.07) + Vector((0, 0, 0.3))                  # caixa da garganta (moldura em U em volta da boca)
    caixa(bm, gc + Vector((0, 0, 0.16)), (0.16, 0.48, 0.05), rot)                       # teto
    for sy in (-1, 1):
        caixa(bm, gc + rot @ Vector((0, sy * 0.215, 0.0)), (0.16, 0.05, 0.37), rot)      # laterais
    caixa(bm, gc + rot @ Vector((0.0, 0, -0.165)), (0.16, 0.48, 0.04), rot)             # soleira
    obj('garganta', bm, 'casco')
    for sy in (-1, 1):                                                                   # listras em volta da boca
        caixa(bs, gc + rot @ Vector((0.081, sy * 0.215, 0.0)), (0.003, 0.05, 0.37), rot)
    caixa(bs, gc + rot @ Vector((0.081, 0, 0.16)), (0.003, 0.48, 0.05), rot)
    obj('garganta_listras', bs, 'listras')
    bm = bmesh.new()
    caixa(bm, d * (R_CORPO + 0.005) + Vector((0, 0, 0.3)), (0.01, 0.38, 0.29), rot)    # fundo escuro que engole
    obj('garganta_fundo', bm, 'garganta_luz')
    bm = bmesh.new()
    for sy in (-1, 1):                                                                   # luzes de status na moldura
        cil(bm, gc + rot @ Vector((0.085, sy * 0.215, 0.12)), 0.012, 0.01, d, lados=8)
    obj('led', bm, 'led_verde' if a != PI else 'led_ambar')
    # esteira curta: da borda do tile (r 1,5) até a soleira da garganta
    r0, r1 = R_CORPO + 0.15, 1.5
    bm, bb = bmesh.new(), bmesh.new()
    meio = d * ((r0 + r1) / 2)
    caixa(bb, meio + Vector((0, 0, Z_ESTEIRA - 0.012)), (r1 - r0, 0.3, 0.024), rot)       # correia
    for sy in (-1, 1):
        caixa(bm, meio + rot @ Vector((0, sy * 0.17, Z_ESTEIRA - 0.03)), (r1 - r0, 0.025, 0.08), rot)   # laterais
        for r in (r0 + 0.08, r1 - 0.06):
            p = d * r + rot @ Vector((0, sy * 0.17, 0))
            caixa(bm, Vector((p.x, p.y, (Z_ESTEIRA - 0.07) / 2)), (0.035, 0.035, Z_ESTEIRA - 0.07), rot)  # pernas
            caixa(bm, Vector((p.x, p.y, 0.008)), (0.07, 0.07, 0.016), rot)
    for r in (r0 + 0.02, r1 - 0.02):
        cil(bm, d * r + Vector((0, 0, Z_ESTEIRA - 0.035)), 0.03, 0.32, rot @ Vector((0, 1, 0)), lados=12)   # rolos
    obj('esteira', bm, 'grafite')
    obj('correia', bb, 'borracha')
    bm = bmesh.new()
    for sy in (-1, 1):
        caixa(bm, meio + rot @ Vector((0, sy * 0.183, Z_ESTEIRA + 0.0)), (r1 - r0, 0.004, 0.025), rot)
    obj('esteira_listras', bm, 'listras')
    for k in range(3):                                                                   # minério chegando
        bm = bmesh.new()
        pedra(bm, (0, 0, 0), random.uniform(0.035, 0.05), 0.75)
        o = obj('minerio_boca', bm, 'minerio')
        itens_esteira.append((o, a, k))

# ------------------------------------------------------------------ pétalas de escudo térmico (abertas como flor)
L_P = 0.86                      # comprimento radial da pétala
HW0, HW1 = 0.29, 0.64           # meia-largura na dobradiça e na ponta
Z_DOBRA = 0.1
QUEDA = 0.2                     # quanto a pétala desce até cravar no chão


def sup(x, y):
    """Altura da face de cima da pétala (local: x radial a partir da dobradiça, y lateral)."""
    hw = HW0 + (HW1 - HW0) * x / L_P
    t = x / L_P
    return 0.46 * t * (1 - t) - 0.15 * t * t + 0.04 * (y / hw) ** 2     # sobe, cai e crava; bordas levantadas (concha)


petalas = []
for ip, a in enumerate(PETALAS):
    pv = bpy.data.objects.new('petala_%d' % ip, None)                  # pivô na dobradiça
    sc.collection.objects.link(pv)
    pv.location = d_de(a) * (R_CORPO + 0.05) + Vector((0, 0, Z_DOBRA))
    pv.rotation_mode = 'QUATERNION'
    pv.rotation_quaternion = Quaternion((0, 0, 1), a)
    nx, ny = 12, 8
    bm = bmesh.new()
    topo, fundo = [], []
    for i in range(nx + 1):
        x = L_P * i / nx
        hw = HW0 + (HW1 - HW0) * x / L_P
        lt, lf = [], []
        for j in range(ny + 1):
            y = -hw + 2 * hw * j / ny
            xx, yy = x, y
            if i == nx:                                              # ponta lascada
                xx -= random.uniform(0.0, 0.07) * (1 if random.random() < 0.6 else 0.3)
            if j in (0, ny):                                         # bordas laterais irregulares
                yy -= math.copysign(random.uniform(0.0, 0.025), y)
            z = sup(xx, yy)
            lt.append(bm.verts.new((xx, yy, z)))
            lf.append(bm.verts.new((xx, yy, z - 0.035)))
        topo.append(lt)
        fundo.append(lf)
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((topo[i][j], topo[i + 1][j], topo[i + 1][j + 1], topo[i][j + 1]))
            bm.faces.new((fundo[i][j], fundo[i][j + 1], fundo[i + 1][j + 1], fundo[i + 1][j]))
    for i in range(nx):                                              # laterais
        for j in (0, ny):
            bm.faces.new((topo[i][j], fundo[i][j], fundo[i + 1][j], topo[i + 1][j]))
    for j in range(ny):                                              # dobradiça e ponta
        for i in (0, nx):
            bm.faces.new((topo[i][j], topo[i][j + 1], fundo[i][j + 1], fundo[i][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj('petala_placa', bm, 'ablativo', pv)
    # face de dentro: manta térmica dourada amassada, recuada da borda (a borda chamuscada fica à mostra)
    bm = bmesh.new()
    mx, my = 16, 10
    gr = []
    for i in range(mx + 1):
        x = 0.05 + (L_P - 0.14) * i / mx
        hw = HW0 + (HW1 - HW0) * x / L_P - 0.05
        gr.append([bm.verts.new((x, -hw + 2 * hw * j / my, sup(x, -hw + 2 * hw * j / my) + 0.004 + random.uniform(0, 0.006)))
                   for j in range(my + 1)])
    for i in range(mx):
        for j in range(my):
            bm.faces.new((gr[i][j], gr[i + 1][j], gr[i + 1][j + 1], gr[i][j + 1]))
    obj('petala_manta', bm, 'manta', pv)
    # emendas das placas ablativas (quadriculado em relevo baixo) e escorridos de fuligem/queimado
    bm, bq, bn = bmesh.new(), bmesh.new(), bmesh.new()
    for i in range(1, 6):
        x = L_P * i / 6
        hw = HW0 + (HW1 - HW0) * x / L_P - 0.03
        fita(bm, [Vector((x, -hw + 2 * hw * j / 10, sup(x, -hw + 2 * hw * j / 10))) for j in range(11)], 0.012, 0.012)
    for j in range(1, 4):
        f = -1 + 2 * j / 4
        fita(bm, [Vector((L_P * i / 12, f * (HW0 + (HW1 - HW0) * i / 12 - 0.03), sup(L_P * i / 12, f * (HW0 + (HW1 - HW0) * i / 12 - 0.03)))) for i in range(13)], 0.012, 0.012)
    for k in range(5):                                               # escorridos de queimado da reentrada
        y0 = random.uniform(-0.2, 0.2)
        x0, x1 = random.uniform(0.05, 0.25), random.uniform(0.5, 0.78)
        pts = [Vector((x0 + (x1 - x0) * i / 8, y0 + 0.03 * math.sin(i), 0)) for i in range(9)]
        for p in pts:
            p.z = sup(p.x, p.y)
        fita(bn if k % 2 else bq, pts, random.uniform(0.03, 0.08), 0.0135)
    obj('petala_emendas', bm, 'aco', pv)
    obj('petala_queimado', bq, 'queimado', pv)
    obj('petala_fuligem', bn, 'fuligem', pv)
    bm = bmesh.new()                                                 # rebites nas bordas e dobradiça
    for i in range(1, 12):
        x = L_P * i / 12
        hw = HW0 + (HW1 - HW0) * x / L_P - 0.035
        for y in (-hw, hw):
            cil(bm, Vector((x, y, sup(x, y) + 0.012)), 0.009, 0.014, lados=6)
    obj('petala_rebites', bm, 'aco', pv)
    bm = bmesh.new()
    for y in (-0.2, 0.0, 0.2):                                       # dobradiças (juntas ao anel da base)
        cil(bm, Vector((-0.02, y, 0.0)), 0.04, 0.1, Vector((0, 1, 0)), lados=12)
        caixa(bm, Vector((-0.045, y, 0.0)), (0.05, 0.08, 0.06))
    cil(bm, Vector((-0.02, 0, 0)), 0.016, 0.62, Vector((0, 1, 0)), lados=8)
    obj('petala_dobradica', bm, 'aco', pv)
    # suportes dos pistões na pétala
    sup_pts = []
    bm = bmesh.new()
    for sy in (-1, 1):
        x, y = 0.4, sy * 0.24
        p = Vector((x, y, sup(x, y) + 0.04))
        caixa(bm, p - Vector((0, 0, 0.012)), (0.08, 0.06, 0.035))
        for dy in (-0.022, 0.022):
            caixa(bm, p + Vector((0, dy, 0.02)), (0.05, 0.008, 0.05))
        sup_pts.append(p + Vector((0, 0, 0.025)))
    obj('petala_suportes', bm, 'grafite', pv)
    # terra amontoada onde a ponta cravou
    bm = bmesh.new()
    for k in range(18):
        y = random.uniform(-HW1, HW1)
        pedra(bm, Vector((L_P + random.uniform(-0.06, 0.08), y, random.uniform(-0.02, 0.02))), random.uniform(0.04, 0.08), 0.5)
    obj('petala_terra', bm, 'terra', pv)
    petalas.append({'pv': pv, 'a': a, 'sup': sup_pts})

# pistões: camisa presa por olhal no corpo, haste no suporte da pétala (re-orientados a cada quadro)
pistoes = []
for p in petalas:
    for k, sy in enumerate((-1, 1)):
        a = p['a'] + sy * 0.32
        anc = d_de(a) * (R_CORPO + 0.03) + Vector((0, 0, 0.6))
        bm = bmesh.new()
        caixa(bm, anc + d_de(a) * 0.0 - Vector((0, 0, 0.0)), (0.07, 0.07, 0.06), Matrix.Rotation(a, 3, 'Z'))
        obj('pistao_olhal', bm, 'grafite')
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.17)), 0.034, 0.32, lados=14)
        cil(bm, Vector((0, 0, 0.31)), 0.04, 0.03, lados=14)
        cil(bm, Vector((0, 0, 0.02)), 0.028, 0.05, Vector((1, 0, 0)), lados=10)
        camisa = suavizar(obj('pistao_camisa', bm, 'amarelo'))
        camisa.rotation_mode = 'QUATERNION'
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.2)), 0.017, 0.4, lados=12)
        cil(bm, Vector((0, 0, 0.0)), 0.025, 0.045, Vector((1, 0, 0)), lados=10)
        haste = suavizar(obj('pistao_haste', bm, 'cromo'))
        haste.rotation_mode = 'QUATERNION'
        bm = bmesh.new()                                             # mangueira hidráulica do corpo à camisa
        mangueira(bm, bezier(anc + Vector((0, 0, 0.1)), anc + d_de(a) * 0.05 + Vector((0, 0, 0.18)),
                             anc + d_de(a) * 0.12 + Vector((0, 0, 0.12)), anc + d_de(a) * 0.15 + Vector((0, 0, 0.06)), 8), 0.01)
        obj('pistao_mangueira', bm, 'borracha')
        pistoes.append({'anc': anc, 'pet': p, 'k': k, 'camisa': camisa, 'haste': haste})

# cabos-raiz: saem do corpo, passam por cima da pétala com abraçadeiras e mergulham no chão além da ponta
bm, bc, bt = bmesh.new(), bmesh.new(), bmesh.new()
for p in petalas:
    for sy, rr, dz in ((-1, 0.034, 0.0), (1, 0.024, 0.05)):
        a = p['a'] + sy * 0.09
        d = d_de(a)
        pts = bezier(d * (R_CORPO - 0.01) + Vector((0, 0, 0.36 + dz)), d * 1.0 + Vector((0, 0, 0.62 + dz)),
                     d * 1.62 + Vector((0, 0, 0.42)), d * 1.92 + Vector((0, 0, -0.25)), 18)
        mangueira(bm, pts, rr)
        for t in (5, 9, 13):
            u = (pts[t + 1] - pts[t - 1]).normalized()
            tubo(bc, pts[t] - u * 0.012, pts[t] + u * 0.012, rr * 1.45, 12)
    for k in range(10):                                              # terra revolvida onde os cabos entram
        pedra(bt, d_de(p['a']) * 1.9 + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), 0.02)), random.uniform(0.04, 0.07), 0.5)
suavizar(obj('cabos_raiz', bm, 'cabo'))
suavizar(obj('cabos_abracadeiras', bc, 'aco'))
obj('cabos_terra', bt, 'terra')

# ------------------------------------------------------------------ garras do topo, monólito, anéis, fragmentos
garras_pontas = []
bm, bp = bmesh.new(), bmesh.new()
for a in PETALAS:
    d = d_de(a)
    pts = bezier(d * 0.5 + Vector((0, 0, Z_CORPO - 0.1)), d * 0.8 + Vector((0, 0, 1.0)),
                 d * 0.9 + Vector((0, 0, 1.22)), d * 0.74 + Vector((0, 0, 1.3)), 14)
    for i in range(len(pts) - 1):                                    # garra que afina
        r = 0.055 * (1 - 0.6 * i / len(pts))
        u = (pts[i + 1] - pts[i]).normalized()
        tubo(bm, pts[i] - u * r * 0.4, pts[i + 1] + u * r * 0.4, r, 12)
    for i in (3, 7, 11):                                             # juntas da garra
        bmesh.ops.create_uvsphere(bp, u_segments=12, v_segments=8, radius=0.058 * (1 - 0.6 * i / len(pts)) + 0.012,
                                  matrix=Matrix.Translation(pts[i]))
    caixa(bp, d * 0.5 + Vector((0, 0, Z_CORPO - 0.11)), (0.16, 0.13, 0.07), Matrix.Rotation(a, 3, 'Z'))   # base presa no cone
    u = (pts[-1] - pts[-2]).normalized()
    cil(bp, pts[-1] + u * 0.035, 0.024, 0.07, u, lados=10, r2=0.004)                                    # ponta
    garras_pontas.append(pts[-1] + u * 0.07)
suavizar(obj('garras', bm, 'casco'))
suavizar(obj('garras_juntas', bp, 'aco'))
bm = bmesh.new()
for p in garras_pontas:                                              # emissor na ponta de cada garra
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.012, matrix=Matrix.Translation(p))
obj('garras_pontas', bm, 'fresta')

monolito = bpy.data.objects.new('monolito', None)
sc.collection.objects.link(monolito)
monolito.location = CM
bm = bmesh.new()
ALTO_M, R_M = 0.42, 0.17
lados = 6
anel_b, anel_t = [], []
for i in range(lados):
    a = i * 2 * PI / lados
    rr = R_M * (1 + 0.12 * math.sin(i * 2.3))                        # cristal irregular
    anel_b.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, -ALTO_M * 0.45)))
    anel_t.append(bm.verts.new((math.cos(a + 0.2) * rr * 0.9, math.sin(a + 0.2) * rr * 0.9, ALTO_M * 0.55)))
pb = bm.verts.new((0.01, -0.01, -ALTO_M))
pt = bm.verts.new((-0.02, 0.01, ALTO_M))
for i in range(lados):
    j = (i + 1) % lados
    bm.faces.new((anel_b[i], anel_b[j], anel_t[j], anel_t[i]))
    bm.faces.new((anel_b[j], anel_b[i], pb))
    bm.faces.new((anel_t[i], anel_t[j], pt))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('monolito_cristal', bm, 'cristal', monolito)
luz_m = bpy.data.lights.new('Monólito', 'POINT')
luz_m.color = VIOLETA
luz_m.shadow_soft_size = 0.15
lm = bpy.data.objects.new('Monólito luz', luz_m)
sc.collection.objects.link(lm)
lm.location = CM - Vector((0, 0, 0.62))                          # abaixo do cristal: luz dentro do vidro estoura em branco

aneis = []
for nome, R, r, pontos in (('anel_dentro', 0.36, 0.022, 6), ('anel_meio', 0.52, 0.03, 8), ('anel_fora', 0.67, 0.034, 10)):
    o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(o)
    o.location = CM
    o.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), R, r, 72, 14)
    for k in range(pontos):                                          # blocos de sensores no anel
        a = k * 2 * PI / pontos
        caixa(bm, d_de(a) * R, (0.05, 0.05, r * 2.6), Matrix.Rotation(a, 3, 'Z'))
    suavizar(obj(nome + '_aco', bm, 'aneis', o))
    bm = bmesh.new()
    for k in range(pontos):
        a = k * 2 * PI / pontos
        caixa(bm, d_de(a) * (R - 0.026), (0.004, 0.03, r * 1.6), Matrix.Rotation(a, 3, 'Z'))
    obj(nome + '_luz', bm, 'fresta', o)
    aneis.append(o)

fragmentos = []
for k in range(11):
    bm = bmesh.new()
    h = random.uniform(0.04, 0.09)
    rr = h * 0.35
    vs = [bm.verts.new((math.cos(i * 2 * PI / 5) * rr, math.sin(i * 2 * PI / 5) * rr, 0)) for i in range(5)]
    t, b = bm.verts.new((0, 0, h)), bm.verts.new((0, 0, -h * 0.6))
    for i in range(5):
        bm.faces.new((vs[i], vs[(i + 1) % 5], t))
        bm.faces.new((vs[(i + 1) % 5], vs[i], b))
    o = obj('fragmento', bm, 'cristal')
    o.data.materials[0] = base3d.M['cristal']
    o.rotation_mode = 'XYZ'
    fragmentos.append((o, random.uniform(0, 2 * PI), random.uniform(0.9, 1.08), random.uniform(1.6, 2.3),
                       random.choice((1, -1, 2)), random.uniform(0, 2 * PI)))

arcos = []                                                           # arcos de energia: 3 formas por garra, pisca
for ig, p0 in enumerate(garras_pontas):
    alvo = CM + (p0 - CM).xy.to_3d().normalized() * 0.12 + Vector((0, 0, -0.18))
    for v in range(3):
        bm = bmesh.new()
        pts = [p0]
        for i in range(1, 9):
            t = i / 9
            q = p0.lerp(alvo, t) + Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * 0.05 * math.sin(PI * t)
            pts.append(q)
        pts.append(alvo)
        for a, b in zip(pts, pts[1:]):
            tubo(bm, a, b, 0.006, 5)
        o = obj('arco', bm, 'arco')
        arcos.append((o, ig, v))

calores = []
for k in range(8):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    calores.append(obj('calor', bm, 'calor'))

# ------------------------------------------------------------------ animação (laço de 4 s)
cristal_em = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr) ** 2                # dois pulsos por laço
    monolito.location = CM + Vector((0, 0, 0.04 * math.sin(2 * PI * fr)))
    monolito.rotation_euler = (0, 0, 2 * PI * fr / 2 * 2)
    monolito.scale = [1 + 0.03 * pulso] * 3
    for c in ('location', 'rotation_euler', 'scale'):
        monolito.keyframe_insert(c, frame=q)
    cristal_em.default_value = 0.8 + 2.2 * pulso
    cristal_em.keyframe_insert('default_value', frame=q)
    luz_m.energy = 40 + 90 * pulso
    luz_m.keyframe_insert('energy', frame=q)
    # anéis: dentro precessa inclinado; meio vira em x (uma volta); fora inclinado e girando em z
    aneis[0].rotation_quaternion = Quaternion((0, 0, 1), -4 * PI * fr) @ Quaternion((1, 0, 0), math.radians(12))
    aneis[1].rotation_quaternion = Quaternion((0, 0, 1), PI / 4) @ Quaternion((1, 0, 0), 2 * PI * fr)
    aneis[2].rotation_quaternion = Quaternion((0, 0, 1), 2 * PI * fr) @ Quaternion((0, 1, 0), math.radians(24)) @ Quaternion((0, 0, 1), -2 * PI * fr)
    for o in aneis:
        o.keyframe_insert('rotation_quaternion', frame=q)
    for o, a0, r, z, vel, fase in fragmentos:
        a = a0 + vel * 2 * PI * fr
        o.location = Vector((math.cos(a) * r, math.sin(a) * r, z + 0.05 * math.sin(2 * PI * fr + fase)))
        o.rotation_euler = (fase + 2 * PI * fr, fase * 0.5, 4 * PI * fr)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)
    # pétalas respiram (descem ~1°) e os pistões acompanham
    for ip, p in enumerate(petalas):
        ang = -math.radians(0.9) * (0.5 + 0.5 * math.sin(2 * PI * fr + ip * PI / 2))
        p['pv'].rotation_quaternion = Quaternion((0, 0, 1), p['a']) @ Quaternion((0, 1, 0), -ang)
        p['pv'].keyframe_insert('rotation_quaternion', frame=q)
    bpy.context.view_layer.update()
    for ps in pistoes:
        pv = ps['pet']['pv']
        m = Matrix.Translation(pv.location) @ pv.rotation_quaternion.to_matrix().to_4x4()
        ponta = m @ ps['pet']['sup'][ps['k']]
        d = (ponta - ps['anc']).normalized()
        ps['camisa'].location = ps['anc']
        ps['camisa'].rotation_quaternion = d.to_track_quat('Z', 'Y')
        ps['haste'].location = ponta
        ps['haste'].rotation_quaternion = (-d).to_track_quat('Z', 'Y')
        for o in (ps['camisa'], ps['haste']):
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
    # arcos: cada garra solta um arco curto em momentos diferentes, trocando a forma
    for o, ig, v in arcos:
        janela = (fr * 4 + ig * 0.37) % 1.0
        visivel = janela < 0.22 and int(janela / 0.075) == v
        o.hide_render = not visivel
        o.hide_viewport = not visivel
        o.keyframe_insert('hide_render', frame=q)
        o.keyframe_insert('hide_viewport', frame=q)
    # calor saindo dos respiros
    for k, o in enumerate(calores):
        c = RESPIROS[k % 4]
        u = ((k // 4) / 2 + fr * 2 + k * 0.11) % 1.0
        o.location = c + Vector((0.04 * math.sin(k + u * 6), 0.04 * math.cos(k + u * 5), 0.55 * u + 0.03))
        o.scale = [0.05 + 0.13 * u] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    # minério nas esteiras entra na garganta
    for o, a, k in itens_esteira:
        u = (k / 3 + fr) % 1.0
        r = 1.45 - u * (1.45 - 0.5)
        o.location = d_de(a) * r + Vector((0, 0, Z_ESTEIRA + 0.035))
        o.rotation_euler = (0, 0, k * 2.0)
        o.keyframe_insert('location', frame=q)

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.6
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.5, 0.56, 0.7, 1)
bg.inputs['Strength'].default_value = 0.5
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
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1200
    sc.frame_set(9)                                                  # um arco aceso, pulso alto
    for i, (ang, alt) in enumerate(((300, 2.6), (210, 2.2), (120, 3.0), (30, 1.6))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.7, math.sin(a) * 4.7, alt)), ALVO, 33)
        sc.render.filepath = os.path.join(AQUI, 'nucleo_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
    mirar((2.0, -2.1, 1.25), (0.45, -0.45, 0.45), 30)                 # de perto: pétala, pistões, garganta, raízes
    sc.render.filepath = os.path.join(AQUI, 'nucleo_perto.png')
    bpy.ops.render.render(write_still=True)
if modo == 'video':
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(300)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 6.6, math.sin(a) * 6.6, 2.4)), ALVO, 32)
    if hasattr(sc.render.image_settings, 'media_type'):
        sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(AQUI, 'nucleo_video.mp4')
    bpy.ops.render.render(animation=True)
print('NUCLEO ok')
