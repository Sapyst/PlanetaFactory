"""Estudo isolado (fora do jogo): estação de terraplenagem pesada da IA, 3×3 tiles, sem portas de item.
Chassi amarelo sobre duas esteiras de trator (sapatas com garras, roda motriz dentada, roda-guia, roletes) com lama
grudada. Lâmina frontal (sul) curva com faca de aço, braços de empuxo e dois cilindros de levante. Compactador de
impacto (norte): torre-guia com pilão e sapata que sobe pelo cilindro hidráulico e cai socando o chão (poeira).
Unidade hidráulica (oeste): tanque, motor e bomba, bloco de válvulas, acumuladores, radiador de óleo com ventoinha;
mangueiras até cada cilindro. Emissor de levitação no meio: núcleo de cristal violeta pulsando e três hastes que
suspendem um bloco de rocha; pedrinhas orbitam, torrões caem e poeira gira. Mastro de topografia (leste): anel de
sensores girando e laser de varredura que risca o chão. Chão revirado: leira de terra na frente da lâmina, marcas de
esteira, torrões, poça de lama e óleo.
Uso: blender -b --python estudo_terraplenagem.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, pedra, mancha

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


def liso(o):
    for pg in o.data.polygons:
        pg.use_smooth = True
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
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


def tubo_curvo(bm, pts, r, lados=14, tampas=True):
    """Tubo contínuo ao longo de uma polilinha (anéis orientados pela tangente): mangueira/haste curva sem emendas."""
    pts = [Vector(p) for p in pts]
    aneis = []
    u = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if u is None:                                                      # transporte paralelo: sem torção
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            u = t.cross(ref).normalized()
        else:
            u = (u - t * u.dot(t)).normalized()
        v = t.cross(u).normalized()
        aneis.append([bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r)
                      for a in (k * 2 * PI / lados for k in range(lados))])
    for A, B in zip(aneis, aneis[1:]):
        for k in range(lados):
            bm.faces.new((A[k], A[(k + 1) % lados], B[(k + 1) % lados], B[k]))
    if tampas:
        bm.faces.new(list(reversed(aneis[0])))
        bm.faces.new(aneis[-1])


def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Transmission Weight'].default_value = 0.35
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 2.0
    return m


def laser_mat(nome, cor, forca, alfa):
    """Leque de laser: emissão misturada com transparente (vê-se o feixe sem virar parede)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*cor, 1)
    em.inputs['Strength'].default_value = forca
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    mix.inputs[0].default_value = alfa
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def terra_mat(nome, c1, c2, rough, bump=0.4, escala=3.0):
    """Terra: dois tons misturados por ruído, com relevo granulado."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 10.0, 'Roughness': 0.65})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], fino.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*c1, 1)
    mix.inputs[7].default_value = (*c2, 1)
    nt.links.new(mr.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    bp = no(nt, 'ShaderNodeBump', **{'Strength': bump, 'Distance': 0.02})
    nt.links.new(fino.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


VIOLETA = (0.66, 0.42, 1.0)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.9),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'faca': mats.material('Faca', (0.5, 0.5, 0.5), 1.0, 0.3, pintura=False, ferrugem=0.5, sujeira=0.6, escovado=True),
    'ferro': mats.material('Ferro', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'sapata': mats.material('Sapata', (0.17, 0.16, 0.15), 1.0, 0.6, pintura=False, ferrugem=0.9, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.75, pintura=False, sujeira=0.4, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.04, 0.04, 0.045), 0, 0.6, pintura=False, sujeira=0.6, desgaste=0.0),
    'rocha': terra_mat('Rocha', (0.24, 0.2, 0.16), (0.14, 0.12, 0.1), 0.85, 0.5, 4.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': terra_mat('Lama', (0.075, 0.05, 0.032), (0.13, 0.09, 0.055), 0.45, 0.25, 6.0),
    'torrao': terra_mat('Torrão', (0.17, 0.12, 0.075), (0.11, 0.075, 0.05), 0.92, 0.6, 5.0),
    'chao': terra_mat('Chão', (0.25, 0.19, 0.13), (0.17, 0.125, 0.085), 0.95, 0.5, 1.2),
    'sulco': terra_mat('Sulco', (0.07, 0.05, 0.035), (0.1, 0.07, 0.05), 0.97, 0.5, 5.0),
    'revirado': terra_mat('Revirado', (0.13, 0.09, 0.06), (0.19, 0.135, 0.09), 0.9, 0.7, 4.0),
    'agua_lama': mats.material('Água barrenta', (0.2, 0.15, 0.1), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'cristal': cristal_mat(),
    'emissor': emissivo('Emissor', (0.55, 0.25, 1.0), 6.0, (0.12, 0.04, 0.3)),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', (1.0, 0.5, 0.05), 10.0),
    'laser': laser_mat('Laser', (1.0, 0.08, 0.03), 4.0, 0.07),
    'laser_linha': emissivo('Laser no chão', (1.0, 0.1, 0.03), 40.0),
    'poeira': base3d.volume_mat('Poeira', (0.45, 0.36, 0.27), 5.0, 1.3, 2.7),
    'poeira_chao': base3d.volume_mat('Poeira do chão', (0.5, 0.4, 0.3), 9.0, 0.0, 1.0),
})

# ------------------------------------------------------------------ esteiras (x = ±1,12)
XE = 1.12                    # centro de cada esteira
YR = 0.98                    # centro das rodas motriz (norte) e guia (sul)
ZR = 0.265                   # altura do eixo das rodas
R_SAP = 0.23                 # raio do centro da sapata
LS = 2 * YR
TOTAL_S = 2 * LS + 2 * PI * R_SAP
N_S = int(round(TOTAL_S / 0.135))
PASSO_S = TOTAL_S / N_S


def no_laco_s(u):
    """Posição e ângulo (em x) da sapata a u metros do começo do trecho de cima (indo para o norte)."""
    if u < LS:
        return Vector((0, -YR + u, ZR + R_SAP)), 0.0
    u -= LS
    if u < PI * R_SAP:
        a = u / R_SAP
        return Vector((0, YR + R_SAP * math.sin(a), ZR + R_SAP * math.cos(a))), -a
    u -= PI * R_SAP
    if u < LS:
        return Vector((0, YR - u, ZR - R_SAP)), -PI
    u -= LS
    a = PI + u / R_SAP
    return Vector((0, -YR + R_SAP * math.sin(a), ZR + R_SAP * math.cos(a))), -a


for sx in (-1, 1):
    X0 = sx * XE
    bs, bg = bmesh.new(), bmesh.new()
    for k in range(N_S):
        p, ang = no_laco_s(k * PASSO_S)
        rot = Matrix.Rotation(ang, 3, 'X')
        c = Vector((X0, 0, 0)) + p
        caixa(bs, c, (0.4, PASSO_S - 0.012, 0.03), rot)                  # sapata
        caixa(bg, c + rot @ Vector((0, -0.02, 0.028)), (0.4, 0.022, 0.03), rot)    # garra
        for dx in (-0.06, 0.06):                                          # elos da corrente (por dentro)
            caixa(bs, c + rot @ Vector((dx, 0, -0.03)), (0.03, PASSO_S - 0.02, 0.035), rot)
    obj('esteira_sapatas', bs, 'sapata')
    obj('esteira_garras', bg, 'sapata')
    bm = bmesh.new()                                                       # quadro da esteira
    caixa_de(bm, (X0 - 0.06, -YR + 0.12, 0.17), (X0 + 0.06, YR - 0.12, 0.38))
    caixa_de(bm, (X0 - 0.08, -YR + 0.1, 0.36), (X0 + 0.08, YR - 0.1, 0.39))
    obj('esteira_quadro', bm, 'amarelo')
    bm = bmesh.new()
    for y in (-YR, YR):                                                    # rodas guia e motriz (dentada no norte)
        for dx in (-0.1, 0.1):
            cil(bm, Vector((X0 + dx, y, ZR)), 0.2, 0.06, Vector((1, 0, 0)), lados=28)
        cil(bm, Vector((X0, y, ZR)), 0.07, 0.3, Vector((1, 0, 0)), lados=14)
    for k in range(17):                                                    # dentes da motriz
        a = k * 2 * PI / 17
        d = Vector((0, math.cos(a), math.sin(a)))
        caixa(bm, Vector((X0, YR, ZR)) + d * 0.205, (0.07, 0.035, 0.03), Matrix.Rotation(a - PI / 2, 3, 'X'))
    for k in range(5):                                                     # roletes de baixo
        y = -0.7 + k * 0.35
        for dx in (-0.1, 0.1):
            cil(bm, Vector((X0 + dx, y, 0.13)), 0.075, 0.07, Vector((1, 0, 0)), lados=18)
        cil(bm, Vector((X0, y, 0.13)), 0.03, 0.28, Vector((1, 0, 0)), lados=10)
    for y in (-0.4, 0.4):                                                  # roletes de cima
        for dx in (-0.1, 0.1):
            cil(bm, Vector((X0 + dx, y, 0.435)), 0.042, 0.06, Vector((1, 0, 0)), lados=14)
        cil(bm, Vector((X0, y, 0.435)), 0.018, 0.27, Vector((1, 0, 0)), lados=8)
        caixa_de(bm, (X0 - 0.03, y - 0.03, 0.385), (X0 + 0.03, y + 0.03, 0.42))
    suavizar(obj('esteira_rodas', bm, 'ferro'))
    bm = bmesh.new()                                                       # cubos das rodas com parafusos
    for y in (-YR, YR):
        cil(bm, Vector((X0 + sx * 0.16, y, ZR)), 0.09, 0.03, Vector((1, 0, 0)), lados=20)
        for k in range(8):
            a = k * 2 * PI / 8
            cil(bm, Vector((X0 + sx * 0.178, y + 0.06 * math.cos(a), ZR + 0.06 * math.sin(a))), 0.01, 0.012,
                Vector((1, 0, 0)), lados=6)
    obj('esteira_cubos', bm, 'aco')
    bm = bmesh.new()                                                       # travessas do quadro ao chassi
    for y in (-0.55, 0.55):
        caixa_de(bm, (sx * 0.86 if sx > 0 else -XE + 0.06, y - 0.08, 0.26), (XE - 0.06 if sx > 0 else -0.86, y + 0.08, 0.38))
    obj('esteira_travessas', bm, 'grafite')
    bm = bmesh.new()                                                       # lama grudada na esteira
    for k in range(70):
        u = random.uniform(0, TOTAL_S)
        p, ang = no_laco_s(u)
        rot = Matrix.Rotation(ang, 3, 'X')
        c = Vector((X0 + random.uniform(-0.17, 0.17), 0, 0)) + p + rot @ Vector((0, 0, 0.045))
        pedra(bm, c, random.uniform(0.025, 0.06), 0.45)
    for k in range(25):                                                    # no quadro e entre as rodas
        pedra(bm, Vector((X0 + random.uniform(-0.09, 0.09), random.uniform(-0.8, 0.8), random.uniform(0.17, 0.25))),
              random.uniform(0.03, 0.06), 0.6)
    obj('esteira_lama', bm, 'lama')

# ------------------------------------------------------------------ chassi
Z_DECK = 0.62
bm = bmesh.new()
caixa_de(bm, (-0.88, -1.05, 0.40), (0.88, 1.1, Z_DECK))
obj('chassi', bm, 'amarelo')
bm = bmesh.new()
caixa_de(bm, (-0.86, -1.03, 0.30), (0.86, 1.08, 0.40))                    # barriga
for y in (-0.8, -0.2, 0.4, 0.95):
    caixa_de(bm, (-0.88, y - 0.04, 0.3), (0.88, y + 0.04, 0.41))
obj('chassi_barriga', bm, 'grafite')
bm = bmesh.new()
caixa_de(bm, (-0.885, -1.055, 0.43), (0.885, -1.045, 0.6))                # listras no frontal
caixa_de(bm, (-0.885, 1.095, 0.43), (0.885, 1.105, 0.6))
obj('chassi_listras', bm, 'listras')
bm = bmesh.new()                                                           # chapas de piso e olhais de içamento
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(bm, Vector((sx * 0.8, sy * 0.98, Z_DECK + 0.05)), 0.04, 0.012, Vector((1, 0, 0)), lados=12)
        caixa(bm, Vector((sx * 0.8, sy * 0.98, Z_DECK + 0.02)), (0.06, 0.04, 0.04))
obj('olhais', bm, 'ferro')

# ------------------------------------------------------------------ radiador de óleo (frente) com ventoinha
bm = bmesh.new()
caixa_de(bm, (-0.82, -1.04, Z_DECK), (0.82, -0.62, 0.92))
obj('radiador_caixa', bm, 'amarelo')
bm = bmesh.new()
for k in range(16):                                                        # aletas da grade (topo)
    x = -0.3 + k * 0.04
    caixa_de(bm, (x - 0.006, -0.98, 0.92), (x + 0.006, -0.68, 0.945))
toro(bm, Vector((0, -0.83, 0.935)), 0.2, 0.012, 40, 8)
obj('radiador_grade', bm, 'ferro')
bm = bmesh.new()
caixa_de(bm, (-0.29, -0.97, 0.9), (0.29, -0.69, 0.92))
obj('radiador_fundo', bm, 'grafite')
ventoinha = bpy.data.objects.new('ventoinha', None)
sc.collection.objects.link(ventoinha)
ventoinha.location = (0, -0.83, 0.915)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.04, 0.03, lados=12)
for k in range(7):
    a = k * 2 * PI / 7
    caixa(bm, Matrix.Rotation(a, 3, 'Z') @ Vector((0.1, 0, 0)), (0.15, 0.05, 0.006),
          Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(0.5, 3, 'X'))
obj('ventoinha_pas', bm, 'aco', ventoinha)
bm = bmesh.new()                                                           # mancais dos cilindros de levante
for sx in (-1, 1):
    for dx in (-0.06, 0.06):
        caixa_de(bm, (sx * 0.6 + dx - 0.015, -0.82, 0.92), (sx * 0.6 + dx + 0.015, -0.68, 1.06))
    cil(bm, Vector((sx * 0.6, -0.75, 1.02)), 0.025, 0.16, Vector((1, 0, 0)), lados=10)
obj('mancais_levante', bm, 'ferro')

# ------------------------------------------------------------------ lâmina (sul): pivô dos braços em y=-0,2
PIVO_L = Vector((0, -0.2, 0.27))
lamina = bpy.data.objects.new('lamina', None)
sc.collection.objects.link(lamina)
lamina.location = PIVO_L


def perfil(s):
    """Face da lâmina (y, z) para s ∈ [0,1]: côncava para o sul, com a ponta de cima curvada para a frente."""
    return -1.46 + 0.14 * math.sin(PI * s * 0.93), 0.035 + 0.74 * s


NP = 20
XL = 1.45
bm = bmesh.new()
cols = []
for i in range(NP + 1):
    y, z = perfil(i / NP)
    linha = []
    for xx in (-XL, XL):
        for dy in (0.0, 0.035):
            linha.append(bm.verts.new(Vector((xx, y + dy, z)) - PIVO_L))
    cols.append(linha)
for A, B in zip(cols, cols[1:]):
    bm.faces.new((A[0], A[2], B[2], B[0]))                                 # frente
    bm.faces.new((A[1], B[1], B[3], A[3]))                                 # costas
    bm.faces.new((A[0], B[0], B[1], A[1]))                                 # lado oeste
    bm.faces.new((A[2], A[3], B[3], B[2]))                                 # lado leste
for L in (cols[0], cols[-1]):
    bm.faces.new((L[0], L[1], L[3], L[2]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
liso(obj('lamina_chapa', bm, 'amarelo', lamina))
bm = bmesh.new()
for k in range(9):                                                         # nervuras nas costas
    x = -1.3 + k * 0.325
    pts = [Vector((x, perfil(i / 10)[0] + 0.035, perfil(i / 10)[1])) - PIVO_L for i in range(11)]
    for a, b in zip(pts, pts[1:]):
        caixa(bm, (a + b) / 2 + Vector((0, 0.03, 0)), (0.03, 0.06, (b - a).length + 0.01),
              Matrix.Rotation(math.atan2(-(b - a).y, (b - a).z), 3, 'X'))
yb, zb = perfil(0.55)
caixa_de(bm, Vector((-XL + 0.05, yb + 0.03, 0.2)) - PIVO_L, Vector((XL - 0.05, yb + 0.1, zb)) - PIVO_L)   # caixão de reforço
obj('lamina_nervuras', bm, 'amarelo', lamina)
bm = bmesh.new()
for sx in (-1, 1):                                                         # chapas laterais: uma chapa com o perfil curvo
    frente = [perfil(i / 12) for i in range(13)]
    contorno = [(y - 0.02, z) for y, z in frente] + [(frente[-1][0] + 0.17, frente[-1][1] - 0.05), (frente[0][0] + 0.2, frente[0][1])]
    vs = [bm.verts.new(Vector((sx * XL - 0.015, y, z)) - PIVO_L) for y, z in contorno]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=Vector((0.03, 0, 0)), verts=[v for v in ext['geom'] if isinstance(v, bmesh.types.BMVert)])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('lamina_orelhas_laterais', bm, 'amarelo', lamina)
bm = bmesh.new()
y0, z0 = perfil(0)
caixa_de(bm, Vector((-XL, y0 - 0.012, 0.0)) - PIVO_L, Vector((XL, y0 + 0.04, 0.09)) - PIVO_L)          # faca de aço
for sx in (-1, 1):
    caixa_de(bm, Vector((sx * XL - (0.2 if sx > 0 else 0), y0 - 0.02, 0.0)) - PIVO_L,
             Vector((sx * XL + (0 if sx > 0 else 0.2), y0 + 0.04, 0.13)) - PIVO_L)                    # cantos de desgaste
obj('lamina_faca', bm, 'faca', lamina)
bm = bmesh.new()
for k in range(15):                                                        # parafusos da faca
    cil(bm, Vector((-1.35 + k * 0.193, y0 - 0.014, 0.05)) - PIVO_L, 0.012, 0.012, Vector((0, 1, 0)), lados=6)
obj('lamina_parafusos', bm, 'aco', lamina)
yt, zt = perfil(1)
bm = bmesh.new()
caixa_de(bm, Vector((-XL, yt - 0.005, zt - 0.06)) - PIVO_L, Vector((XL, yt + 0.04, zt)) - PIVO_L)      # listra no topo
obj('lamina_listras', bm, 'listras', lamina)
bm = bmesh.new()                                                           # braços de empuxo (fora das esteiras)
for sx in (-1, 1):
    a = Vector((sx * 1.39, -0.2, 0.27)) - PIVO_L
    b = Vector((sx * 1.39, -1.31, 0.2)) - PIVO_L
    viga(bm, a, b, 0.09)
    cil(bm, a, 0.07, 0.12, Vector((1, 0, 0)), lados=16)                    # munhão
    viga(bm, Vector((sx * 1.39, -1.0, 0.24)) - PIVO_L, Vector((sx * 1.39, perfil(0.75)[0] + 0.05, perfil(0.75)[1])) - PIVO_L, 0.06)  # escora
obj('lamina_bracos', bm, 'amarelo', lamina)
bm = bmesh.new()                                                           # mancal do munhão no quadro da esteira
for sx in (-1, 1):                                                         # do quadro (x=1,18) até o munhão (x=1,34)
    caixa_de(bm, (min(sx * 1.17, sx * 1.33), -0.27, 0.21), (max(sx * 1.17, sx * 1.33), -0.13, 0.33))
obj('mancal_bracos', bm, 'ferro')
bm = bmesh.new()                                                           # orelhas das hastes na lâmina
OLHAL_L = []
for sx in (-1, 1):
    p = Vector((sx * 0.6, perfil(0.8)[0] + 0.1, perfil(0.8)[1]))
    OLHAL_L.append(p)
    for dx in (-0.05, 0.05):
        caixa(bm, p - PIVO_L + Vector((dx, -0.03, 0)), (0.02, 0.12, 0.1))
    cil(bm, p - PIVO_L, 0.02, 0.14, Vector((1, 0, 0)), lados=10)
obj('lamina_orelhas', bm, 'ferro', lamina)
bm = bmesh.new()                                                           # terra grudada na lâmina (frente e costas)
for k in range(60):
    s = random.uniform(0.0, 0.45) ** 1.3
    y, z = perfil(s)
    pedra(bm, Vector((random.uniform(-1.4, 1.4), y + 0.01, z)) - PIVO_L, random.uniform(0.025, 0.06), 0.4)
for k in range(18):
    pedra(bm, Vector((random.uniform(-1.4, 1.4), perfil(0.2)[0] + 0.1, random.uniform(0.12, 0.25))) - PIVO_L,
          random.uniform(0.03, 0.05), 0.6)
obj('lamina_lama', bm, 'lama', lamina)

# ------------------------------------------------------------------ cilindros hidráulicos: camisa presa numa peça, haste na outra


def cilindro(nome, r_c, l_c, r_h, l_h, cor='amarelo'):
    """Camisa (origem no pino de trás, ao longo de +z) e haste (origem no olhal, ao longo de +z, entra na camisa)."""
    cam = bpy.data.objects.new(nome + '_camisa', None)
    sc.collection.objects.link(cam)
    cam.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.03 + l_c / 2)), r_c, l_c, lados=20)
    suavizar(obj(nome + '_tubo', bm, cor, cam))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.03 + l_c - 0.02)), r_c + 0.012, 0.05, lados=20)          # cabeçote da camisa
    cil(bm, Vector((0, 0, 0.05)), r_c + 0.01, 0.05, lados=20)                        # fundo
    cil(bm, Vector((0, 0, 0)), 0.03, r_c * 2 + 0.03, Vector((1, 0, 0)), lados=10)    # olhal de trás
    caixa(bm, Vector((0, 0, 0.02)), (0.05, r_c * 1.4, 0.06))
    for z in (0.09, l_c - 0.04):                                                     # portas de óleo
        caixa(bm, Vector((0, -r_c - 0.012, z + 0.03)), (0.04, 0.03, 0.04))
    obj(nome + '_cabecotes', bm, 'ferro', cam)
    hst = bpy.data.objects.new(nome + '_haste', None)
    sc.collection.objects.link(hst)
    hst.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, l_h / 2)), r_h, l_h, lados=16)
    suavizar(obj(nome + '_cromo', bm, 'cromo', hst))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.03, r_h * 2 + 0.04, Vector((1, 0, 0)), lados=10)
    caixa(bm, Vector((0, 0, 0.03)), (0.05, r_h * 2 + 0.02, 0.07))
    obj(nome + '_olhal', bm, 'ferro', hst)
    return cam, hst


def pos_cilindro(cam, hst, a, b, q):
    d = b - a
    cam.location = a
    cam.rotation_quaternion = d.to_track_quat('Z', 'Y')
    hst.location = b
    hst.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    for o in (cam, hst):
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)


ANC_L = [Vector((sx * 0.6, -0.75, 1.02)) for sx in (-1, 1)]
cil_lev = [cilindro('levante%d' % i, 0.065, 0.42, 0.032, 0.4) for i in range(2)]

# ------------------------------------------------------------------ compactador de impacto (norte)
YC = 1.32
XR = 0.3                     # trilhos da torre
Z_TOPO = 2.36
bm = bmesh.new()
for sx in (-1, 1):
    caixa_de(bm, (sx * XR - 0.035, YC - 0.035, 0.02), (sx * XR + 0.035, YC + 0.035, Z_TOPO))     # trilhos
    for z in (0.47, 0.58):                                                 # suportes no chassi (atrás do trilho)
        caixa_de(bm, (sx * XR - 0.03, 1.08, z - 0.03), (sx * XR + 0.03, YC - 0.035, z + 0.03))
    viga(bm, Vector((sx * XR, YC - 0.03, 2.15)), Vector((sx * XR, 0.78, Z_DECK + 0.02)), 0.06)   # escoras diagonais
    caixa(bm, Vector((sx * XR, 0.78, Z_DECK + 0.02)), (0.12, 0.12, 0.03))
    caixa(bm, Vector((sx * XR, YC, 0.03)), (0.14, 0.14, 0.03))             # sapata do trilho no chão
caixa_de(bm, (-XR - 0.06, YC - 0.09, Z_TOPO - 0.1), (XR + 0.06, YC + 0.09, Z_TOPO + 0.02))      # cabeçote da torre
for z in (1.2, 1.75):                                                      # travessas atrás (fora do curso do pilão)
    caixa_de(bm, (-XR, YC + 0.035, z - 0.03), (XR, YC + 0.075, z + 0.03))
obj('torre', bm, 'amarelo')
bm = bmesh.new()
for sx in (-1, 1):
    caixa_de(bm, (sx * XR - 0.04, YC - 0.04, Z_TOPO + 0.02), (sx * XR + 0.04, YC + 0.04, Z_TOPO + 0.06))
cil(bm, Vector((0, YC, Z_TOPO + 0.05)), 0.12, 0.04, lados=20)              # flange da camisa
obj('torre_tampas', bm, 'ferro')
bm = bmesh.new()                                                           # lampada de alerta no topo
cil(bm, Vector((XR, YC, Z_TOPO + 0.12)), 0.04, 0.08, lados=14)
obj('giroflex', bm, 'lampada')

pilao = bpy.data.objects.new('pilao', None)                                # 'cabecote' no jogo
sc.collection.objects.link(pilao)
pilao.location = (0, YC, 0)
bm = bmesh.new()
caixa_de(bm, (-0.21, -0.12, 0.08), (0.21, 0.12, 0.5))                       # corpo (massa)
for sx in (-1, 1):
    caixa_de(bm, (sx * 0.21 - 0.03 if sx > 0 else -0.24, -0.1, 0.12), (0.24 if sx > 0 else -0.21 + 0.03, 0.1, 0.46))  # patins
obj('pilao_corpo', bm, 'amarelo', pilao)
bm = bmesh.new()
caixa_de(bm, (-0.215, -0.125, 0.15), (0.215, 0.125, 0.25))
obj('pilao_listras', bm, 'listras', pilao)
bm = bmesh.new()
caixa_de(bm, (-0.3, -0.17, 0.0), (0.3, 0.17, 0.06))                         # sapata compactadora
caixa_de(bm, (-0.15, -0.1, 0.06), (0.15, 0.1, 0.08))
for sx in (-1, 1):                                                         # mãos-francesas da sapata
    viga(bm, Vector((sx * 0.28, 0, 0.06)), Vector((sx * 0.2, 0, 0.2)), 0.04)
obj('pilao_sapata', bm, 'ferro', pilao)
bm = bmesh.new()
for k in range(22):
    pedra(bm, Vector((random.uniform(-0.29, 0.29), random.uniform(-0.17, 0.17), random.uniform(0.0, 0.07))),
          random.uniform(0.02, 0.045), 0.5)
obj('pilao_lama', bm, 'lama', pilao)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.53)), 0.03, 0.1, Vector((1, 0, 0)), lados=10)
caixa_de(bm, (-0.05, -0.04, 0.5), (0.05, 0.04, 0.56))
obj('pilao_olhal', bm, 'ferro', pilao)
L_CAM_C, L_HST_C = 0.88, 1.1
cam_c, hst_c = cilindro('compactador', 0.09, L_CAM_C, 0.045, L_HST_C, 'grafite')

# ------------------------------------------------------------------ unidade hidráulica (oeste)
XH = -0.7
bm = bmesh.new()
cil(bm, Vector((XH, 0.48, Z_DECK + 0.2)), 0.16, 0.62, Vector((0, 1, 0)), lados=24)   # tanque de óleo
suavizar(obj('hpu_tanque', bm, 'grafite'))
bm = bmesh.new()
for y in (0.25, 0.71):                                                     # berços e cintas do tanque
    caixa_de(bm, (XH - 0.14, y - 0.03, Z_DECK), (XH + 0.14, y + 0.03, Z_DECK + 0.08))
    cil(bm, Vector((XH, y, Z_DECK + 0.2)), 0.168, 0.03, Vector((0, 1, 0)), lados=24)
cil(bm, Vector((XH, 0.4, Z_DECK + 0.37)), 0.04, 0.04, lados=12)            # bocal de enchimento
cil(bm, Vector((XH, 0.4, Z_DECK + 0.4)), 0.05, 0.015, lados=12)
obj('hpu_cintas', bm, 'ferro')
bm = bmesh.new()                                                           # visor de nível
caixa_de(bm, (XH - 0.166, 0.55, Z_DECK + 0.1), (XH - 0.158, 0.58, Z_DECK + 0.3))
obj('hpu_visor', bm, 'cromo')
bm = bmesh.new()
caixa_de(bm, (XH - 0.168, 0.555, Z_DECK + 0.1), (XH - 0.16, 0.575, Z_DECK + 0.21))
obj('hpu_visor_oleo', bm, 'oleo')
bm = bmesh.new()                                                           # motor elétrico com aletas
cil(bm, Vector((XH, -0.05, Z_DECK + 0.15)), 0.12, 0.34, Vector((0, 1, 0)), lados=20)
for k in range(8):
    cil(bm, Vector((XH, -0.18 + k * 0.035, Z_DECK + 0.15)), 0.135, 0.008, Vector((0, 1, 0)), lados=20)
caixa_de(bm, (XH - 0.13, -0.2, Z_DECK), (XH + 0.13, 0.1, Z_DECK + 0.04))
caixa_de(bm, (XH + 0.06, -0.08, Z_DECK + 0.24), (XH + 0.14, 0.02, Z_DECK + 0.32))   # caixa de ligação
suavizar(obj('hpu_motor', bm, 'grafite'))
bm = bmesh.new()                                                           # bomba e acoplamento
cil(bm, Vector((XH, -0.27, Z_DECK + 0.15)), 0.065, 0.1, Vector((0, 1, 0)), lados=16)
cil(bm, Vector((XH, -0.36, Z_DECK + 0.15)), 0.09, 0.09, Vector((0, 1, 0)), lados=16)
caixa_de(bm, (XH - 0.07, -0.42, Z_DECK), (XH + 0.07, -0.3, Z_DECK + 0.06))
obj('hpu_bomba', bm, 'amarelo')
bm = bmesh.new()                                                           # bloco de válvulas
MAN = Vector((XH + 0.02, -0.5, Z_DECK + 0.12))
caixa(bm, MAN, (0.24, 0.1, 0.24))
for k in range(3):
    caixa(bm, MAN + Vector((-0.07 + k * 0.07, -0.08, 0.06)), (0.05, 0.07, 0.06))      # solenoides
obj('hpu_valvulas', bm, 'aco')
bm = bmesh.new()
for k in range(3):
    cil(bm, MAN + Vector((-0.07 + k * 0.07, -0.12, 0.1)), 0.008, 0.01, Vector((0, 1, 0)), lados=8)
obj('hpu_leds', bm, 'led_verde')
bm = bmesh.new()                                                           # acumuladores (garrafas)
for y in (0.92, 1.02):
    cil(bm, Vector((-0.78, y, Z_DECK + 0.26)), 0.05, 0.42, lados=18)
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=8, radius=0.05, matrix=Matrix.Translation((-0.78, y, Z_DECK + 0.47)))
caixa_de(bm, (-0.84, 0.86, Z_DECK + 0.25), (-0.72, 1.08, Z_DECK + 0.28))
suavizar(obj('hpu_acumuladores', bm, 'amarelo'))
bm = bmesh.new()                                                           # manômetros
cil(bm, MAN + Vector((0.13, 0, 0.08)), 0.03, 0.015, Vector((1, 0, 0)), lados=16)
obj('hpu_manometro', bm, 'cromo')

# mangueiras: bloco de válvulas → cilindros (bezier com curvas suaves) e tubulação rígida motor ↔ tanque
bm = bmesh.new()
tubo_curvo(bm, bezier((XH, -0.27, Z_DECK + 0.22), (XH, -0.27, Z_DECK + 0.32), (XH + 0.02, -0.45, Z_DECK + 0.32),
                      MAN + Vector((0, 0, 0.12)), 10), 0.022)
tubo_curvo(bm, bezier((XH, 0.17, Z_DECK + 0.2), (XH, 0.12, Z_DECK + 0.32), (XH + 0.0, -0.3, Z_DECK + 0.35),
                      (XH, -0.36, Z_DECK + 0.24), 10), 0.025)
suavizar(obj('hpu_tubos', bm, 'aco'))
MANG = []
for i, sx in enumerate((-1, 1)):                                           # dois por cilindro de levante
    for j, dz in enumerate((0.0, 0.06)):
        a = MAN + Vector((0.06 * j - 0.03, -0.05, 0.12))
        port = ANC_L[i] + Vector((0, -0.08 - 0.03, 0.05 + 0.03 * j))
        MANG.append(bezier(a, a + Vector((0, 0, 0.18)), port + Vector((-0.05 * sx, 0.15, 0.2)), port, 18))
a = MAN + Vector((0.1, 0.0, 0.12))                                         # para o compactador: pelo convés e torre acima
via = [a, a + Vector((0, 0, 0.08)), Vector((-0.45, 0.0, Z_DECK + 0.08)), Vector((-0.45, 0.85, Z_DECK + 0.05)),
       Vector((-XR - 0.06, 1.1, Z_DECK + 0.05)), Vector((-XR - 0.06, YC - 0.02, 0.8)),
       Vector((-XR - 0.06, YC - 0.02, Z_TOPO - 0.15)), Vector((-0.12, YC - 0.02, Z_TOPO + 0.06)),
       Vector((-0.06, YC, Z_TOPO + 0.09))]
pts = []
for p, q in zip(via, via[1:]):
    n = max(2, int((q - p).length / 0.05))
    pts += [p + (q - p) * (k / n) for k in range(n)]
pts.append(via[-1])
MANG.append(pts)
bm = bmesh.new()
for m in MANG:
    tubo_curvo(bm, m, 0.018, 10)
suavizar(obj('mangueiras', bm, 'borracha'))
bm = bmesh.new()                                                           # abraçadeiras da mangueira da torre
for z in (0.9, 1.3, 1.7, 2.1):
    caixa(bm, Vector((-XR - 0.06, YC - 0.02, z)), (0.05, 0.05, 0.025))
for t in (0.3, 0.6):
    caixa(bm, Vector((-0.45, 0.85 * t, Z_DECK + 0.03)), (0.06, 0.03, 0.06))
obj('abracadeiras', bm, 'ferro')

# ------------------------------------------------------------------ emissor de levitação (meio) e rocha suspensa
CE = Vector((0, 0.1, 0))
Z_ROCHA = 1.92
bm = bmesh.new()
cil(bm, CE + Vector((0, 0, Z_DECK + 0.1)), 0.42, 0.2, lados=8)              # pedestal octogonal
cil(bm, CE + Vector((0, 0, Z_DECK + 0.24)), 0.3, 0.08, lados=8)
obj('emissor_base', bm, 'grafite')
bm = bmesh.new()
toro(bm, CE + Vector((0, 0, Z_DECK + 0.2)), 0.38, 0.025, 48, 10)
obj('emissor_anel', bm, 'aco')
bm = bmesh.new()                                                           # gaiola do cristal
for k in range(6):
    a = k * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(bm, CE + d * 0.2 + Vector((0, 0, Z_DECK + 0.28)), CE + d * 0.14 + Vector((0, 0, Z_DECK + 0.8)), 0.022)
toro(bm, CE + Vector((0, 0, Z_DECK + 0.8)), 0.14, 0.02, 32, 8)
obj('emissor_gaiola', bm, 'ferro')
bm = bmesh.new()                                                           # cristal: drusa de prismas pontudos
for k, (dx, dy, h, r, incl) in enumerate(((0, 0, 0.42, 0.075, 0.0), (0.07, 0.03, 0.26, 0.045, 0.35),
                                          (-0.06, 0.05, 0.22, 0.04, -0.4), (0.0, -0.07, 0.28, 0.045, 0.3))):
    eixo = Vector((math.sin(incl) * (1 if k % 2 else 0), math.sin(incl) * (0 if k % 2 else 1), math.cos(incl))).normalized()
    b0 = CE + Vector((dx, dy, Z_DECK + 0.3))
    cil(bm, b0 + eixo * h * 0.4, r, h * 0.8, eixo, lados=6)
    cil(bm, b0 + eixo * (h * 0.8 + h * 0.12), r, h * 0.24, eixo, lados=6, r2=0.0)
cristal = obj('cristal', bm, 'cristal')
luz_c = bpy.data.lights.new('Cristal', 'POINT')
luz_c.color = VIOLETA
luz_c.shadow_soft_size = 0.15
lc = bpy.data.objects.new('Cristal', luz_c)
sc.collection.objects.link(lc)
lc.location = CE + Vector((0, 0, Z_DECK + 0.95))

PONTAS = []
bm, bf, be = bmesh.new(), bmesh.new(), bmesh.new()
for k in range(3):                                                         # três hastes emissoras
    a = PI / 2 + k * 2 * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    p0 = CE + d * 0.36 + Vector((0, 0, Z_DECK + 0.2))
    p3 = CE + d * 0.52 + Vector((0, 0, 1.42))
    alvo = CE + Vector((0, 0, Z_ROCHA))
    ponta = (alvo - p3).normalized()
    pts = bezier(p0, p0 + d * 0.22 + Vector((0, 0, 0.15)), p3 - ponta * 0.3, p3, 16)
    tubo_curvo(bm, pts, 0.045, 14)
    cil(bf, p0, 0.07, 0.05, lados=14)                                      # base
    for t in (0.35, 0.7):                                                  # colares
        q = pts[int(16 * t)]
        cil(bf, q, 0.058, 0.04, pts[int(16 * t) + 1] - q, lados=14)
    cil(bf, p3 + ponta * 0.03, 0.09, 0.05, ponta, lados=18)                # prato
    toro(be, p3 + ponta * 0.07, 0.065, 0.014, 32, 8, ponta.to_track_quat('Z', 'Y').to_matrix())
    PONTAS.append((p3 + ponta * 0.08, ponta))
    caixa(bf, p0 + Vector((0, 0, -0.06)), (0.1, 0.1, 0.06))
suavizar(obj('emissor_hastes', bm, 'amarelo'))
obj('emissor_colares', bf, 'ferro')
obj('emissor_aneis', be, 'emissor')
bm = bmesh.new()                                                           # cabos do pedestal até as hastes
for k in range(3):
    a = PI / 2 + k * 2 * PI / 3 + 0.35
    d = Vector((math.cos(a), math.sin(a), 0))
    tubo_curvo(bm, bezier(CE + d * 0.3 + Vector((0, 0, Z_DECK + 0.28)), CE + d * 0.4 + Vector((0, 0, Z_DECK + 0.3)),
                          CE + d * 0.42 + Vector((0, 0, Z_DECK + 0.2)), CE + d * 0.42 + Vector((0, 0, Z_DECK + 0.12)), 8), 0.012, 8)
suavizar(obj('emissor_cabos', bm, 'cabo'))

rocha = bpy.data.objects.new('bloco', None)
sc.collection.objects.link(rocha)
rocha.location = CE + Vector((0, 0, Z_ROCHA))
rocha.rotation_mode = 'XYZ'
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.4)
sem = Vector((3.1, 7.7, 1.3))
PLANOS = [(Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.6, 1))).normalized(),
           random.uniform(0.27, 0.34)) for _ in range(9)]                  # faces de fratura (bloco arrancado)
for v in bm.verts:
    n = v.co.normalized()
    d = 0.05 * noise.noise(n * 1.8 + sem) + 0.02 * noise.noise(n * 5 + sem) + 0.008 * noise.noise(n * 14 + sem)
    c = v.co * (1 + d / 0.4)
    for pn, dist in PLANOS:                                               # corta pelos planos
        e = c.dot(pn) - dist
        if e > 0:
            c -= pn * e * 0.92
    v.co = Vector((c.x * 1.12, c.y * 1.0, c.z * 0.85))
o_r = obj('bloco_rocha', bm, 'rocha', rocha)
for pg in o_r.data.polygons:
    pg.use_smooth = False
bm = bmesh.new()                                                           # terra e raízes presas embaixo
for k in range(26):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.0, 0.3)
    pedra(bm, Vector((math.cos(a) * r * 1.1, math.sin(a) * r * 0.9, -0.24 + r * 0.25)), random.uniform(0.04, 0.08), 0.6)
obj('bloco_terra', bm, 'torrao', rocha)
bm = bmesh.new()
for k in range(5):
    a = random.uniform(0, 2 * PI)
    p0 = Vector((math.cos(a) * 0.15, math.sin(a) * 0.12, -0.27))
    tubo_curvo(bm, bezier(p0, p0 + Vector((0.03, 0, -0.06)), p0 + Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, -0.12)),
                          p0 + Vector((math.cos(a) * 0.12, math.sin(a) * 0.1, -0.2)), 6), 0.008, 6)
obj('bloco_raizes', bm, 'lama', rocha)

pedrinhas, orb = [], []
for k in range(14):                                                        # pedrinhas em órbita
    bm = bmesh.new()
    pedra(bm, (0, 0, 0), random.uniform(0.025, 0.05), 0.8)
    o = obj('pedrinha', bm, 'rocha' if k % 3 else 'torrao')
    pedrinhas.append(o)
    orb.append((random.uniform(0.54, 0.62), random.uniform(-0.25, 0.08), random.uniform(0, 2 * PI),
                random.choice((1, 1, 2)) * random.choice((1, -1)) * (1 if k % 2 else 1)))
caindo = []
for k in range(5):                                                         # torrões soltando de baixo da rocha
    bm = bmesh.new()
    pedra(bm, (0, 0, 0), random.uniform(0.015, 0.03), 0.8)
    caindo.append((obj('torrao_caindo', bm, 'torrao'), Vector((random.uniform(-0.2, 0.2), random.uniform(-0.15, 0.15), 0)), k / 5))
poeiras = []
for k in range(7):                                                         # poeira girando em volta da rocha
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    poeiras.append(obj('poeira', bm, 'poeira'))
luz_r = bpy.data.lights.new('Brilho rocha', 'POINT')                       # luz violeta por baixo (rebate na rocha)
luz_r.color = VIOLETA
luz_r.shadow_soft_size = 0.3
lr = bpy.data.objects.new('Brilho rocha', luz_r)
sc.collection.objects.link(lr)
lr.location = CE + Vector((0, 0, 1.35))

# ------------------------------------------------------------------ mastro de topografia (leste): antena e laser
MA = Vector((0.68, 0.72, 0))
bm = bmesh.new()
cil(bm, MA + Vector((0, 0, Z_DECK + 0.03)), 0.12, 0.06, lados=16)
cil(bm, MA + Vector((0, 0, (Z_DECK + 2.05) / 2)), 0.045, 2.05 - Z_DECK, lados=16)
for k in range(3):                                                         # estais
    a = k * 2 * PI / 3 + 0.3
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(bm, MA + Vector((0, 0, 1.2)), MA + d * 0.2 + Vector((0, 0, Z_DECK + 0.02)), 0.015)
caixa(bm, MA + Vector((0, -0.14, Z_DECK + 0.18)), (0.16, 0.1, 0.3))       # caixa de junção
suavizar(obj('mastro', bm, 'grafite'))
bm = bmesh.new()
for z in (1.0, 1.4, 1.8):
    caixa(bm, MA + Vector((0, 0, z)), (0.11, 0.11, 0.02))
obj('mastro_aneis', bm, 'ferro')
bm = bmesh.new()
caixa(bm, MA + Vector((0, -0.195, Z_DECK + 0.26)), (0.012, 0.012, 0.012))
obj('mastro_led', bm, 'led_verde')
bm = bmesh.new()                                                           # eletrocalha: caixa de junção → pedestal
caixa_de(bm, (0.15, 0.48, Z_DECK), (0.62, 0.56, Z_DECK + 0.04))
caixa_de(bm, (0.15, 0.48, Z_DECK), (0.62, 0.49, Z_DECK + 0.06))
caixa_de(bm, (0.15, 0.55, Z_DECK), (0.62, 0.56, Z_DECK + 0.06))
obj('eletrocalha', bm, 'aco')
bm = bmesh.new()
for k in range(3):
    tubo_curvo(bm, bezier(MA + Vector((-0.03 + k * 0.03, -0.19, Z_DECK + 0.1)), MA + Vector((-0.03 + k * 0.03, -0.24, Z_DECK + 0.06)),
                          Vector((0.62, 0.5 + k * 0.02, Z_DECK + 0.045)), Vector((0.4, 0.5 + k * 0.02, Z_DECK + 0.045)), 8), 0.01, 8)
    tubo_curvo(bm, [Vector((0.4, 0.5 + k * 0.02, Z_DECK + 0.045)), Vector((0.24, 0.5 + k * 0.02, Z_DECK + 0.045)),
                    Vector((0.2, 0.46 + k * 0.02, Z_DECK + 0.1))], 0.01, 8)
for k in range(2):                                                         # feixe subindo o mastro
    tubo_curvo(bm, [MA + Vector((-0.05 + 0.02 * k, -0.06, Z_DECK + 0.33)), MA + Vector((-0.05 + 0.02 * k, -0.055, 1.9))], 0.009, 8)
suavizar(obj('cabos_mastro', bm, 'cabo'))
bm = bmesh.new()
for z in (0.95, 1.35, 1.75):
    caixa(bm, MA + Vector((-0.04, -0.05, z)), (0.07, 0.03, 0.02))
obj('cabos_abracadeiras', bm, 'ferro')

antena = bpy.data.objects.new('antena', None)
sc.collection.objects.link(antena)
antena.location = MA + Vector((0, 0, 2.08))
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), 0.2, 0.018, 40, 8)
for k in range(3):
    a = k * 2 * PI / 3
    viga(bm, Vector((0, 0, 0)), Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0)), 0.018)
cil(bm, Vector((0, 0, 0)), 0.05, 0.06, lados=14)
cil(bm, Vector((0, 0, 0.13)), 0.008, 0.22, lados=6)                        # vareta
obj('antena_anel', bm, 'aco', antena)
bm = bmesh.new()
for k in range(6):                                                         # módulos de sensor no anel
    a = k * PI / 3
    caixa(bm, Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.0)), (0.06, 0.045, 0.05), Matrix.Rotation(a, 3, 'Z'))
obj('antena_sensores', bm, 'amarelo', antena)
bm = bmesh.new()
for k in range(6):
    a = k * PI / 3
    caixa(bm, Vector((math.cos(a) * 0.231, math.sin(a) * 0.231, 0.0)), (0.004, 0.03, 0.02), Matrix.Rotation(a, 3, 'Z'))
obj('antena_lentes', bm, 'led_ambar', antena)

Z_LASER = 1.62
scanner = bpy.data.objects.new('scanner', None)
sc.collection.objects.link(scanner)
scanner.location = MA + Vector((0, 0, Z_LASER))
bm = bmesh.new()
caixa(bm, Vector((0.09, 0, 0)), (0.1, 0.09, 0.08))
cil(bm, Vector((0.0, 0, 0)), 0.06, 0.1, lados=14)
obj('scanner_corpo', bm, 'amarelo', scanner)
bm = bmesh.new()
caixa(bm, Vector((0.141, 0, -0.01)), (0.004, 0.06, 0.03))
obj('scanner_janela', bm, 'laser_linha', scanner)
X_CHAO = 2.25 - MA.x                                                       # o feixe cai a leste, fora da esteira
bm = bmesh.new()
o0 = Vector((0.145, 0, -0.01))
v0 = bm.verts.new(o0)
v1 = bm.verts.new(Vector((X_CHAO, -0.32, 0.006 - (MA.z + Z_LASER))))
v2 = bm.verts.new(Vector((X_CHAO, 0.32, 0.006 - (MA.z + Z_LASER))))
bm.faces.new((v0, v1, v2))
obj('laser_leque', bm, 'laser', scanner)
bm = bmesh.new()
caixa(bm, Vector((X_CHAO, 0, 0.006 - Z_LASER)), (0.012, 0.66, 0.004))
obj('laser_risco', bm, 'laser_linha', scanner)
luz_l = bpy.data.lights.new('Laser', 'POINT')
luz_l.color = (1.0, 0.1, 0.03)
luz_l.energy = 6
luz_l.shadow_soft_size = 0.05
ll = bpy.data.objects.new('Laser', luz_l)
sc.collection.objects.link(ll)
ll.parent = scanner
ll.location = (X_CHAO - 0.05, 0, 0.05 - Z_LASER)

# ------------------------------------------------------------------ óleo vazando e sujeira no chassi
bm = bmesh.new()
for c, r in (((XH + 0.05, -0.55), 0.12), ((XH + 0.12, 0.0), 0.08), ((-0.2, -0.6), 0.06)):
    mancha(bm, c, r, Z_DECK + 0.002)
for k in range(5):                                                         # escorridos pela lateral do chassi
    y = random.uniform(-0.7, 0.2)
    caixa_de(bm, (-0.886, y, random.uniform(0.42, 0.5)), (-0.882, y + random.uniform(0.015, 0.03), Z_DECK))
obj('oleo_chassi', bm, 'oleo')
bm = bmesh.new()
for k in range(30):                                                        # torrões e poeira no convés
    pedra(bm, Vector((random.uniform(-0.85, 0.85), random.choice((random.uniform(-1.0, -0.65), random.uniform(0.8, 1.08))),
                      Z_DECK + 0.01)), random.uniform(0.015, 0.035), 0.5)
for k in range(20):                                                        # lama respingada na lateral do chassi
    sx = random.choice((-1, 1))
    pedra(bm, Vector((sx * 0.885, random.uniform(-1.0, 1.05), random.uniform(0.32, 0.45))), random.uniform(0.02, 0.045), 0.5)
obj('chassi_lama', bm, 'lama')
bm = bmesh.new()
for k in range(8):
    mancha(bm, (random.uniform(-0.8, 0.8), random.uniform(-0.6, 1.0)), random.uniform(0.05, 0.12), Z_DECK + 0.0015)
obj('chassi_poeira', bm, 'torrao')

# ------------------------------------------------------------------ chão revirado, leira, marcas de esteira
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (80, 80, 1.0))
obj('chao', bm, 'chao')
bm = bmesh.new()                                                           # leira de terra empurrada pela lâmina
NX, NY = 48, 18
grade = []
for j in range(NY + 1):
    y = -1.47 - 1.0 * j / NY
    linha = []
    for i in range(NX + 1):
        x = -1.9 + 3.8 * i / NX
        fx = max(0.0, 1 - (abs(x) / 1.85) ** 4)
        t = (y + 1.47) / -1.0
        h = 0.3 * fx * math.exp(-((t - 0.18) / 0.28) ** 2) + 0.05 * noise.noise(Vector((x * 3, y * 3, 0.5))) * fx
        if t < 0.04:
            h = max(h, 0.0)
        linha.append(bm.verts.new(Vector((x, y, max(0.0, h) - 0.005))))
    grade.append(linha)
for A, B in zip(grade, grade[1:]):
    for i in range(NX):
        bm.faces.new((A[i], A[i + 1], B[i + 1], B[i]))
liso(obj('leira', bm, 'revirado'))
bm = bmesh.new()
for k in range(90):                                                        # torrões espalhados
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.6, 3.2)
    c = Vector((math.cos(a) * r, math.sin(a) * r * 1.1, 0.01))
    if c.y < -1.5 and abs(c.x) < 1.9 and c.y > -2.5:
        c.z += 0.05
    pedra(bm, c, random.uniform(0.02, 0.09), 0.55)
for k in range(40):                                                        # torrões na crista da leira
    x = random.uniform(-1.6, 1.6)
    pedra(bm, Vector((x, random.uniform(-1.75, -1.55), 0.25 * max(0, 1 - (abs(x) / 1.85) ** 4))), random.uniform(0.03, 0.08), 0.6)
obj('torroes', bm, 'torrao')
bm = bmesh.new()                                                           # marcas de esteira para o norte (por onde veio)
for sx in (-1, 1):
    for k in range(34):
        y = 1.32 + k * 0.135 + 0.02
        x0 = sx * XE + 0.004 * k * sx
        caixa(bm, Vector((x0, y, 0.004)), (0.4, 0.04, 0.008))
    caixa_de(bm, (sx * XE - 0.21, 1.3, 0.0005), (sx * XE + 0.21, 6.0, 0.0015))
obj('marcas_esteira', bm, 'lama')
bm = bmesh.new()
for sx in (-1, 1):                                                         # bordas levantadas da trilha
    for d in (-0.22, 0.22):
        for k in range(30):
            pedra(bm, Vector((sx * XE + d + random.uniform(-0.02, 0.02), 1.4 + k * 0.15, 0.0)), random.uniform(0.02, 0.04), 0.4)
obj('marcas_bordas', bm, 'revirado')
bm = bmesh.new()                                                           # rastro curvo de pneu (outra máquina): blocos da banda
for sx in (-1, 1):
    pts = bezier((4.5, -3.2, 0), (2.7, -2.3, 0), (2.5, 0.5, 0), (3.3, 3.6, 0), 80)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = (b - a).normalized()
        n = Vector((-d.y, d.x, 0))
        rz = Matrix.Rotation(math.atan2(-d.x, d.y), 3, 'Z')
        for lado in (-1, 1):                                               # banda em V (chevron)
            c = (a + b) / 2 + n * (sx * 0.32 + lado * 0.045) + Vector((0, 0, 0.003))
            caixa(bm, c, (0.075, 0.03, 0.002), rz @ Matrix.Rotation(lado * 0.5, 3, 'Z'))
obj('rastro_pneu', bm, 'sulco')
bm = bmesh.new()                                                           # buraco socado pelo compactador
caixa_de(bm, (-0.36, YC - 0.22, -0.002), (0.36, YC + 0.22, 0.002))
obj('chao_socado', bm, 'lama')
bm = bmesh.new()
for k in range(18):
    a = random.uniform(0, 2 * PI)
    pedra(bm, Vector((math.cos(a) * random.uniform(0.38, 0.6), YC + math.sin(a) * random.uniform(0.25, 0.4), 0.0)),
          random.uniform(0.02, 0.05), 0.4)
obj('socado_bordas', bm, 'revirado')
bm = bmesh.new()                                                           # poça de lama e óleo
mancha(bm, (-1.85, 0.6), 0.35, 0.002)
mancha(bm, (2.0, -1.0), 0.25, 0.002)
obj('poca', bm, 'agua_lama')
bm = bmesh.new()
mancha(bm, (-1.0, -0.2), 0.18, 0.003)
mancha(bm, (-1.05, 0.25), 0.1, 0.003)
obj('oleo_chao', bm, 'oleo')
bm = bmesh.new()
for k in range(14):
    mancha(bm, (random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)), random.uniform(0.15, 0.4), 0.001)
obj('chao_revirado', bm, 'revirado')

# poeira: impacto do compactador e lâmina
impactos = []
for k in range(5):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    impactos.append(obj('poeira_impacto', bm, 'poeira_chao'))
poeira_l = []
for k in range(4):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    poeira_l.append(obj('poeira_lamina', bm, 'poeira_chao'))

# ------------------------------------------------------------------ animação (laço de 4 s)


def suave(x):
    return x * x * (3 - 2 * x)


def altura_pilao(h):
    """Meio laço do compactador: parado (0–0,08), sobe (0,08–0,6), segura (0,6–0,86), cai acelerando (0,86–1)."""
    if h < 0.08:
        return 0.0
    if h < 0.6:
        return 0.42 * suave((h - 0.08) / 0.52)
    if h < 0.86:
        return 0.42
    x = (h - 0.86) / 0.14
    return 0.42 * (1 - x * x)


cristal_em = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
emissor_em = base3d.M['emissor'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # lâmina: sobe e desce devagar (1 ciclo)
    ang = -0.07 * (0.5 - 0.5 * math.cos(2 * PI * fr))
    lamina.rotation_euler = (ang, 0, 0)
    lamina.keyframe_insert('rotation_euler', frame=q)
    R = Matrix.Rotation(ang, 3, 'X')
    for i in range(2):
        pos_cilindro(*cil_lev[i], ANC_L[i], PIVO_L + R @ (OLHAL_L[i] - PIVO_L), q)
    # compactador: 2 golpes por laço
    h = (fr * 2) % 1.0
    zp = altura_pilao(h)
    pilao.location = (0, YC, zp)
    pilao.keyframe_insert('location', frame=q)
    pos_cilindro(cam_c, hst_c, Vector((0, YC, Z_TOPO - 0.03)), Vector((0, YC, zp + 0.53)), q)
    for k, o in enumerate(impactos):
        u = (h + k * 0.06) % 1.0
        a = k * 2 * PI / len(impactos)
        ativo = u < 0.5
        o.location = Vector((math.cos(a) * (0.3 + 0.5 * u), YC + math.sin(a) * (0.2 + 0.4 * u), 0.06 + 0.35 * u))
        o.scale = [0.2 + 0.35 * u] * 3
        o.hide_render = not ativo
        o.hide_viewport = o.hide_render
        for c in ('location', 'scale', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
    # poeira na leira (sobe devagar)
    for k, o in enumerate(poeira_l):
        u = (k / len(poeira_l) + fr) % 1.0
        o.location = Vector((-1.2 + k * 0.8, -1.7 - 0.2 * u, 0.25 + 0.5 * u))
        o.scale = [0.15 + 0.3 * u] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # ventoinha do radiador
    ventoinha.rotation_euler = (0, 0, 2 * PI * 10 * fr)
    ventoinha.keyframe_insert('rotation_euler', frame=q)
    # antena: 1 volta; laser varre ±45° a leste
    antena.rotation_euler = (0, 0, 2 * PI * fr)
    antena.keyframe_insert('rotation_euler', frame=q)
    scanner.rotation_euler = (0, 0, math.radians(45) * math.sin(2 * PI * fr))
    scanner.keyframe_insert('rotation_euler', frame=q)
    # cristal pulsa (2 pulsos), emissores acompanham
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr) ** 2
    cristal_em.default_value = 0.6 + 1.6 * pulso
    cristal_em.keyframe_insert('default_value', frame=q)
    emissor_em.default_value = 3.0 + 5.0 * pulso
    emissor_em.keyframe_insert('default_value', frame=q)
    luz_c.energy = 6 + 10 * pulso
    luz_c.keyframe_insert('energy', frame=q)
    luz_r.energy = 20 + 30 * pulso
    luz_r.keyframe_insert('energy', frame=q)
    # rocha flutua, balança
    rocha.location = CE + Vector((0, 0, Z_ROCHA + 0.04 * math.sin(2 * PI * fr)))
    rocha.rotation_euler = (0.05 * math.sin(2 * PI * fr + 1), 0.04 * math.sin(2 * PI * fr), 0.12 * math.sin(2 * PI * fr))
    rocha.keyframe_insert('location', frame=q)
    rocha.keyframe_insert('rotation_euler', frame=q)
    for k, o in enumerate(pedrinhas):
        r, dz, f0, voltas = orb[k]
        a = f0 + 2 * PI * voltas * fr
        o.location = CE + Vector((math.cos(a) * r * 1.1, math.sin(a) * r, Z_ROCHA + dz + 0.05 * math.sin(a * 2 + k)))
        o.rotation_euler = (a * 2, a, k)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)
    for o, off, f0 in caindo:
        u = (fr + f0) % 1.0
        tt = u * 0.5
        z = Z_ROCHA - 0.22 - 4.9 * tt * tt
        o.location = CE + off + Vector((0, 0, z))
        o.scale = [1.0 if z > Z_DECK + 0.95 else 0.001] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for k, o in enumerate(poeiras):
        a = k * 2 * PI / len(poeiras) + 2 * PI * fr
        o.location = CE + Vector((math.cos(a) * 0.58, math.sin(a) * 0.5, Z_ROCHA - 0.15 + 0.1 * math.sin(a * 3)))
        o.scale = [0.2 + 0.04 * math.sin(a * 2 + k)] * 3
        o.rotation_euler = (a, k, a * 0.5)
        for c in ('location', 'scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects) + [luz_c, luz_r]:
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: luz e câmera
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
so_uma = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.frame_set(int(QUADROS * 0.42) + 1)                                 # pilão no alto, lâmina erguida
    vistas = [(300, 3.0), (210, 3.2), (120, 3.4), (30, 2.8)]
    for i, (ang, alt) in enumerate(vistas):
        if so_uma is not None and so_uma != str(i):
            continue
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 7.6, math.sin(a) * 7.6, alt)), ALVO, 35)
        sc.render.filepath = os.path.join(AQUI, 'terraplenagem_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if so_uma is None or so_uma == 'perto':
        sc.frame_set(int(QUADROS * 0.02) + 1)                             # logo após o golpe: poeira no chão
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((-1.7, 3.5, 1.35), (-0.05, 1.05, 0.85), 30)                 # de perto: compactador, rocha, unidade
        sc.render.filepath = os.path.join(AQUI, 'terraplenagem_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_uma is None or so_uma == 'lamina':
        sc.frame_set(int(QUADROS * 0.42) + 1)
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((-2.6, -3.0, 1.5), (-0.4, -1.0, 0.55), 32)                 # de perto: lâmina, braços, cilindros, unidade
        sc.render.filepath = os.path.join(AQUI, 'terraplenagem_lamina.png')
        bpy.ops.render.render(write_still=True)
print('TERRAPLENAGEM ok')
