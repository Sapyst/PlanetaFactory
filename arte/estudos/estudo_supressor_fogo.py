"""Estudo isolado (fora do jogo): SUPRESSOR DE INCÊNDIO (supressor_fogo), 1×1 tile. Borrifa água num raio de 8 m
e apaga fogo (máquinas quentes acendem a vegetação seca e há raios). Recebe água por cano na borda oeste.
- Laje com ladrilho de listras; cano de entrada vindo de fora (selas no chão) com par de flanges na borda oeste.
- Válvula de dilúvio (corpo globular flangeado, castelo aparafusado) com cavalete e pistão hidráulico em cima: a haste
  levanta o acoplamento da haste da válvula; bloco de solenoide alimentado por tubinho de cobre tirado do T de entrada
  e mangueiras até as portas do pistão. Manômetros no trim, dreno pingando com crosta de cal.
- Reservatório pressurizado (tampos abaulados, pés, visor de nível, válvula de alívio, manômetro, remendo
  aparafusado, placa com número de série apagado) ligado ao T por mangote flexível trançado com flanges.
- Pedestal com nervuras e chumbadores, coroa dentada fixa; torre giratória (bloco fundido) com motor de giro e pinhão;
  bochechas com mancais; junta rotativa (swivel) no munhão: a água sobe pelo riser e entra pelo munhão no canhão.
  Motor de elevação com redutor e pinhão num setor dentado preso ao berço do canhão. Canhão monitor com bocal de
  latão (anel de jato/neblina serrilhado), mira da IA em cima. Caixa de eletrônica com fiação.
- Mastro de sensores da IA: olho infravermelho girando, câmara de fumaça com venezianas, sensor de calor aletado,
  para-raios com cabo de descida. Armário selado (sem porta), eletrocalhas e cabos.
- Tinta vermelha gasta: lascas, fuligem de incêndios passados (mais no lado do fogo), bolhas de calor, ferrugem,
  poeira em cima, lama embaixo, peças trocadas de outra cor (motor amarelo, motor grafite, tampo repintado).
Cena: vegetação seca queimando (fogo em volume que absorve e emite forte), fumaça preta que dilui em cinza; jato em
arco com núcleo, pedaços, gotas e névoa caindo no fogo, vapor branco subindo onde a água encontra as chamas.
Uso: blender -b --python estudo_supressor_fogo.py -- foto [0|jato]
     blender -b --python estudo_supressor_fogo.py -- teste x y z ax ay az lente quadro"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(97)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def base_de(eixo):
    w = Vector(eixo).normalized()
    ref = Z if abs(w.z) < 0.9 else X
    u = ref.cross(w).normalized()
    return u, w.cross(u), w


def toro(bm, c, R, r, eixo=Z, nR=40, nr=10):
    u, v, w = base_de(eixo)
    c = Vector(c)
    an = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = u * math.cos(a) + v * math.sin(a)
        an.append([bm.verts.new(c + d * (R + r * math.cos(b)) + w * (r * math.sin(b))) for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, Bq = an[i], an[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], Bq[(j + 1) % nr], Bq[j]))


def esfera(bm, c, r, seg=16):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def catmull(pts, n=6):
    pts = [Vector(p) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def varrer(bm, pts, r, lados=12):
    """Tubo contínuo varrido por um caminho (mangueiras e cabos sem emendas)."""
    pts = [Vector(p) for p in pts]
    an = []
    n_prev = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if n_prev is None:
            n_prev = base_de(t)[0]
        n = (n_prev - t * n_prev.dot(t)).normalized()
        n_prev = n
        b = t.cross(n)
        rr = r(i / (len(pts) - 1)) if callable(r) else r
        an.append([bm.verts.new(p + (n * math.cos(a) + b * math.sin(a)) * rr) for a in (k * 2 * PI / lados for k in range(lados))])
    for A, Bq in zip(an, an[1:]):
        for k in range(lados):
            bm.faces.new((A[k], A[(k + 1) % lados], Bq[(k + 1) % lados], Bq[k]))
    bm.faces.new(an[0][::-1])
    bm.faces.new(an[-1])
    return an


def prisma(bm, perfil, eixo_u, eixo_v, eixo_w, o, w0, w1):
    """Prisma de perfil 2D (u, v) extrudado ao longo de w (w0 → w1)."""
    o = Vector(o)
    a = [bm.verts.new(o + eixo_u * x + eixo_v * y + eixo_w * w0) for x, y in perfil]
    b = [bm.verts.new(o + eixo_u * x + eixo_v * y + eixo_w * w1) for x, y in perfil]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(perfil)
    for k in range(n):
        bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))


def rot_face(n):
    n = Vector(n).normalized()
    u, v, _ = base_de(n)
    if abs(n.z) < 0.9:
        v = Z - n * n.z
        v.normalize()
        u = v.cross(n)
    return Matrix((u, n, v)).transposed()          # caixa: x = largura, y = espessura (normal), z = altura


def engrenagem(bm, c, eixo, R, n, alt, esp, a0=0.0, a1=2 * PI, uv=None):
    u, v, w = base_de(eixo)
    if uv:
        u, v = uv
    c = Vector(c)
    larg = (a1 - a0) * R / n * 0.5
    for k in range(n):
        a = a0 + (a1 - a0) * (k + 0.5) / n
        rad = u * math.cos(a) + v * math.sin(a)
        tg = w.cross(rad)
        caixa(bm, c + rad * (R + alt / 2), (alt, larg, esp), Matrix((rad, tg, w)).transposed())


BMS = {}


def B(nome, mat, liso=False, g='base'):
    k = (nome, mat, liso, g)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def parafuso(p, n, g='base', r=0.007, mat='aco'):
    cil(B('parafusos_' + mat, mat, False, g), Vector(p), r, 0.01, Vector(n), lados=6)


def flange(c, eixo, r, esp, n, g='base', mat='ferro'):
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(B('flanges_' + mat, mat, True, g), c, r, esp, eixo, lados=28)
    u, v, _ = base_de(eixo)
    for k in range(n):
        a = k * 2 * PI / n + 0.2
        cil(B('parafusos', 'aco', False, g), c + (u * math.cos(a) + v * math.sin(a)) * (r - 0.012), 0.0055, esp + 0.016, eixo, lados=6)


def cano(pts, r, mat, g='base', lados=24, fl_meio=True, fl_pontas=True):
    pts = [Vector(p) for p in pts]
    bm = B('cano_' + mat, mat, True, g)
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d, L = (b - a).normalized(), (b - a).length
        if L < r * 5:
            continue
        if (i > 0 and fl_meio) or (i == 0 and fl_pontas):
            flange(a + d * r * 2.0, d, r * 1.55, r * 0.4, 6, g)
        if (i < len(pts) - 2 and fl_meio) or (i == len(pts) - 2 and fl_pontas):
            flange(b - d * r * 2.0, d, r * 1.55, r * 0.4, 6, g)


def escorrido(p, n, L, mat='ferrugem', w=0.01, g='base'):
    caixa(B('escorridos_' + mat, mat, False, g), Vector(p) + Vector(n) * 0.0012 + Vector((0, 0, -L / 2)), (w, 0.0015, L), rot_face(Vector(n)))


def manometro(p, cima, face, g='base', r=0.03):
    p, cima, face = Vector(p), Vector(cima).normalized(), Vector(face).normalized()
    tubo(B('niples', 'latao', True, g), p, p + cima * 0.05, 0.006, 8)
    cil(B('niples', 'latao', True, g), p + cima * 0.035, 0.01, 0.012, cima, lados=6)
    c = p + cima * (0.05 + r)
    cil(B('manometros', 'ferro', True, g), c, r, 0.022, face, lados=24)
    toro(B('manometros', 'ferro', True, g), c + face * 0.011, r - 0.002, 0.003, face, 24, 6)
    cil(B('mostrador', 'mostrador', False, g), c + face * 0.0115, r - 0.004, 0.002, face, lados=24)
    cil(B('vidro_man', 'vidro_man', False, g), c + face * 0.0135, r - 0.004, 0.001, face, lados=24)
    u, v, _ = base_de(face)
    ang = random.uniform(0.2, 2.2)
    d = u * math.cos(ang) + v * math.sin(ang)
    viga(B('ponteiro', 'ponteiro', False, g), c + face * 0.0128 - d * 0.004, c + face * 0.0128 + d * (r * 0.75), 0.0022)
    for k in range(9):                                                     # marcas da escala
        a = -0.6 + k * (PI + 1.2) / 8
        dd = u * math.cos(a) + v * math.sin(a)
        viga(B('ponteiro', 'grafite', False, g), c + face * 0.0127 + dd * (r * 0.72), c + face * 0.0127 + dd * (r * 0.86), 0.0015)


SEG = {'0': 'abcdef', '1': 'bc', '2': 'abdeg', '3': 'abcdg', '4': 'bcfg', '5': 'acdfg', '6': 'acdefg', '7': 'abc',
       '8': 'abcdefg', '9': 'abcdfg', 'S': 'acdfg', 'F': 'aefg', '-': 'g', 'P': 'abefg', 'A': 'abcefg', 'E': 'adefg'}


def estencil(p0, u, v, n, txt, h=0.03, g='base', apagado=0.35):
    """Número pintado com estêncil, gasto: segmentos e pedaços faltando."""
    p0, u, v, n = Vector(p0), Vector(u).normalized(), Vector(v).normalized(), Vector(n).normalized()
    w = h * 0.55
    e = h * 0.13
    rot = Matrix((u, n, v)).transposed()
    pos = {'a': (0.5, 1.0, 1), 'b': (1.0, 0.75, 0), 'c': (1.0, 0.25, 0), 'd': (0.5, 0.0, 1), 'e': (0.0, 0.25, 0),
           'f': (0.0, 0.75, 0), 'g': (0.5, 0.5, 1)}
    for i, ch in enumerate(txt):
        base = p0 + u * (i * w * 1.6)
        for s in SEG.get(ch, ''):
            if random.random() < apagado:
                continue
            fx, fy, horiz = pos[s]
            c = base + u * (fx * w) + v * (fy * h) + n * 0.0008
            tam = (w * random.uniform(0.6, 1.0), 0.0012, e) if horiz else (e, 0.0012, h * 0.5 * random.uniform(0.6, 1.0))
            caixa(B('estencil', 'estencil', False, g), c, tam, rot)


def estencil_cil(c, R, a_ini, z, txt, h=0.03, g='base', apagado=0.35):
    """Estêncil numa superfície cilíndrica (eixo z em c): cada caractere assentado no seu ângulo."""
    c = Vector((c[0], c[1], 0))
    w = h * 0.55
    for i, ch in enumerate(txt):
        a = a_ini + (i * w * 1.6 + w / 2) / R
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        estencil(c + d * R + t * (-w / 2) + Vector((0, 0, z)), t, Z, d, ch, h, g, apagado)


def chapa_curva(bm, c, R, a0, a1, z0, z1, esp=0.006, na=12):
    """Chapa curva com espessura assentada num cilindro (tampa, remendo, placa)."""
    vs = []
    for rr in (R, R + esp):
        vs.append([[bm.verts.new((c[0] + rr * math.cos(a0 + (a1 - a0) * i / na), c[1] + rr * math.sin(a0 + (a1 - a0) * i / na), z))
                    for z in (z0, z1)] for i in range(na + 1)])
    di, fo = vs
    for i in range(na):
        bm.faces.new((fo[i][0], fo[i + 1][0], fo[i + 1][1], fo[i][1]))
        bm.faces.new((di[i][1], di[i + 1][1], di[i + 1][0], di[i][0]))
        bm.faces.new((di[i][0], di[i + 1][0], fo[i + 1][0], fo[i][0]))
        bm.faces.new((fo[i][1], fo[i + 1][1], di[i + 1][1], di[i][1]))
    for i in (0, na):
        bm.faces.new((di[i][0], fo[i][0], fo[i][1], di[i][1]))


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


DIR_FOGO = Vector((0.92, 0.39, 0.0))


def camada(m, cor, escala, lim, forca, rough=None, alongar=1.0, lado=None, coord='Object'):
    """Camada extra de sujeira por cima do material (fuligem, bolhas de calor, poeira): ruído com corte, opcionalmente
    mais forte nas faces viradas para 'lado' e esticada em z (escorrido)."""
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
    tc = no(nt, 'ShaderNodeTexCoord')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, 1.0 / alongar)
    nt.links.new(tc.outputs[coord], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 9.0, 'Roughness': 0.65})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    mk = no(nt, 'ShaderNodeMapRange', **{'From Min': lim, 'From Max': lim + 0.12, 'To Min': 0.0, 'To Max': forca})
    nt.links.new(ru.outputs['Fac'], mk.inputs['Value'])
    fator = mk.outputs['Result']
    if lado is not None:
        geo = no(nt, 'ShaderNodeNewGeometry')
        dt = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
        dt.inputs[1].default_value = tuple(lado)
        nt.links.new(geo.outputs['Normal'], dt.inputs[0])
        ld = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.3, 'From Max': 0.9, 'To Min': 0.12, 'To Max': 1.0})
        nt.links.new(dt.outputs['Value'], ld.inputs['Value'])
        mm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(fator, mm.inputs[0])
        nt.links.new(ld.outputs['Result'], mm.inputs[1])
        fator = mm.outputs['Value']
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    nt.links.new(fator, mix.inputs[0])
    if src is not None:
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = bsdf.inputs['Base Color'].default_value
    mix.inputs[7].default_value = (*cor, 1)
    nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    if rough is not None:
        rsrc = bsdf.inputs['Roughness'].links[0].from_socket if bsdf.inputs['Roughness'].links else None
        rm = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        nt.links.new(fator, rm.inputs[0])
        if rsrc is not None:
            nt.links.new(rsrc, rm.inputs[2])
        else:
            rm.inputs[2].default_value = bsdf.inputs['Roughness'].default_value
        rm.inputs[3].default_value = rough
        nt.links.new(rm.outputs[0], bsdf.inputs['Roughness'])
    return m


def sujo(m, fuligem=0.8, poeira=0.6, calor=0.0):
    camada(m, (0.012, 0.011, 0.010), 2.6, 0.44, fuligem, 0.95, 3.0, DIR_FOGO)          # fuligem de incêndios
    if calor > 0:
        camada(m, (0.09, 0.035, 0.02), 9.0, 0.6, calor, 0.85)                          # tinta empolada de calor
    camada(m, (0.30, 0.26, 0.20), 22.0, 0.5, poeira, 0.97, 1.0, Z)                     # poeira assentada em cima
    camada(m, (0.10, 0.075, 0.05), 5.0, 0.45, poeira * 0.8, 0.9, 1.0, -Z)              # lama embaixo
    return m


def nuvem_mat(nome, escura, clara, dens, ruido=2.4, emis_cor=None, emis=0.0, corte=(0.36, 0.62), chama=False):
    """Volume com ruído que some na borda da esfera. Cor do objeto: R = densidade, G = mistura escura → clara."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    oi = no(nt, 'ShaderNodeObjectInfo')
    som = no(nt, 'ShaderNodeVectorMath', operation='ADD')
    if chama:                                                              # línguas de fogo: ruído esticado para cima
        estica = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY')
        estica.inputs[1].default_value = (1.0, 1.0, 0.4)
        nt.links.new(tc.outputs['Object'], estica.inputs[0])
        nt.links.new(estica.outputs['Vector'], som.inputs[0])
    else:
        nt.links.new(tc.outputs['Object'], som.inputs[0])
    esc = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    esc.inputs[1].default_value = 37.0
    nt.links.new(oi.outputs['Random'], esc.inputs[0])
    nt.links.new(esc.outputs['Value'], som.inputs[1])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': ruido, 'Detail': 6.0})
    nt.links.new(som.outputs['Vector'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    if chama:                                                              # labareda: afina para cima (forma no shader)
        sx = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sx.inputs[0])
        fz = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.2, 'From Max': 1.0, 'To Min': 1.0, 'To Max': 0.12})
        nt.links.new(sx.outputs['Z'], fz.inputs['Value'])
        cx = no(nt, 'ShaderNodeCombineXYZ')
        for eixo in ('X', 'Y'):
            dv = no(nt, 'ShaderNodeMath', operation='DIVIDE')
            nt.links.new(sx.outputs[eixo], dv.inputs[0])
            nt.links.new(fz.outputs['Result'], dv.inputs[1])
            nt.links.new(dv.outputs['Value'], cx.inputs[eixo])
        nt.links.new(sx.outputs['Z'], cx.inputs['Z'])
        nt.links.new(cx.outputs[0], comp.inputs[0])
    else:
        nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.15 if chama else 0.3})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    forma = no(nt, 'ShaderNodeMapRange', **{'From Min': corte[0], 'From Max': corte[1]})
    nt.links.new(ru.outputs['Fac'], forma.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], m1.inputs[0])
    nt.links.new(forma.outputs['Result'], m1.inputs[1])
    sep = no(nt, 'ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sep.inputs[0])
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(sep.outputs[0], m2.inputs[1])
    m3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    m3.inputs[1].default_value = dens
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    nt.links.new(m3.outputs['Value'], vol.inputs['Density'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*escura, 1)
    mix.inputs[7].default_value = (*clara, 1)
    nt.links.new(sep.outputs[1], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    if emis_cor and chama:                                                 # miolo amarelo, borda vermelha
        cor_e = no(nt, 'ShaderNodeMix', data_type='RGBA')
        cor_e.inputs[6].default_value = (1.0, 0.13, 0.015, 1)
        cor_e.inputs[7].default_value = (1.0, 0.62, 0.16, 1)
        k = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.25, 'From Max': 0.9})
        nt.links.new(m1.outputs['Value'], k.inputs['Value'])
        nt.links.new(k.outputs['Result'], cor_e.inputs[0])
        nt.links.new(cor_e.outputs[2], vol.inputs['Emission Color'])
    elif emis_cor:
        vol.inputs['Emission Color'].default_value = (*emis_cor, 1)
    if emis_cor:
        m4 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        m4.inputs[1].default_value = emis
        nt.links.new(m2.outputs['Value'], m4.inputs[0])
        nt.links.new(m4.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def jato_mat():
    """Jato de água aerada: transparente com estrias brancas de ar ao longo do comprimento (UV)."""
    m = bpy.data.materials.new('Jato')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.92, 0.96, 0.98, 1)
    ag.inputs['Transmission Weight'].default_value = 1.0
    ag.inputs['Roughness'].default_value = 0.04
    ag.inputs['IOR'].default_value = 1.33
    br = no(nt, 'ShaderNodeBsdfPrincipled')
    br.inputs['Base Color'].default_value = (0.82, 0.85, 0.87, 1)
    br.inputs['Roughness'].default_value = 0.45
    br.inputs['Transmission Weight'].default_value = 0.35
    uv = no(nt, 'ShaderNodeUVMap')
    esc = no(nt, 'ShaderNodeMapping')
    esc.inputs['Scale'].default_value = (9.0, 1.0, 1.0)
    nt.links.new(uv.outputs['UV'], esc.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.5, 'Detail': 6.0})
    nt.links.new(esc.outputs['Vector'], ru.inputs['Vector'])
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs['UV'], sep.inputs[0])
    aer = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 1.0, 'To Min': 0.6, 'To Max': 0.4})
    nt.links.new(sep.outputs['Y'], aer.inputs['Value'])                  # mais branco (aerado) conforme avança
    f = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(ru.outputs['Fac'], f.inputs[0])
    nt.links.new(aer.outputs['Result'], f.inputs[1])
    f2 = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.05, 'From Max': 0.1})
    nt.links.new(f.outputs['Value'], f2.inputs['Value'])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f2.outputs['Result'], mix.inputs[0])
    nt.links.new(ag.outputs[0], mix.inputs[1])
    nt.links.new(br.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def agua_mat(nome='Gota'):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.9, 0.94, 0.96, 1)
    b.inputs['Transmission Weight'].default_value = 0.85
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['IOR'].default_value = 1.33
    return m


def vidro_mat(nome):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.85, 0.82, 0.75, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.25
    b.inputs['Coat Weight'].default_value = 0.6
    return m


def terra_mat():
    """Terra seca: manchas grandes de dois tons, pedrisco fino e rachaduras de barro seco (voronoi)."""
    m = bpy.data.materials.new('Terra seca')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    n1 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.35, 'Detail': 6.0})
    n2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 10.0, 'Roughness': 0.7})
    vo = no(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE')
    vo.inputs['Scale'].default_value = 1.6
    for n in (n1, n2):
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    dist = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY_ADD')       # rachaduras tortas
    dist.inputs[1].default_value = (0.35, 0.35, 0.35)
    nt.links.new(n2.outputs['Color'], dist.inputs[0])
    nt.links.new(tc.outputs['Object'], dist.inputs[2])
    nt.links.new(dist.outputs['Vector'], vo.inputs['Vector'])
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c1.inputs[6].default_value = (0.20, 0.145, 0.09, 1)
    c1.inputs[7].default_value = (0.33, 0.26, 0.17, 1)
    k1 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.65})
    nt.links.new(n1.outputs['Fac'], k1.inputs['Value'])
    nt.links.new(k1.outputs['Result'], c1.inputs[0])
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    c2.inputs[0].default_value = 0.55
    nt.links.new(c1.outputs[2], c2.inputs[6])
    nt.links.new(n2.outputs['Color'], c2.inputs[7])
    rach0 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.012, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(vo.outputs['Distance'], rach0.inputs['Value'])
    zona = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.6})          # só em manchas
    nt.links.new(n1.outputs['Fac'], zona.inputs['Value'])
    rach = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(rach0.outputs['Result'], rach.inputs[0])
    nt.links.new(zona.outputs['Result'], rach.inputs[1])
    c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c3.inputs[7].default_value = (0.07, 0.05, 0.03, 1)
    nt.links.new(rach.outputs['Value'], c3.inputs[0])
    nt.links.new(c2.outputs[2], c3.inputs[6])
    nt.links.new(c3.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    alt = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(n2.outputs['Fac'], alt.inputs[0])
    nt.links.new(rach.outputs['Value'], alt.inputs[1])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.45})
    nt.links.new(alt.outputs['Value'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
VERM = (0.40, 0.032, 0.022)
base3d.M.update({
    'vermelho': sujo(mats.material('Vermelho gasto', VERM, 0, 0.5, desgaste=1.0, sujeira=0.95, ferrugem=0.6), 0.85, 0.6, 0.55),
    'vermelho2': sujo(mats.material('Vermelho repintado', (0.55, 0.05, 0.03), 0, 0.42, desgaste=0.6, sujeira=0.7, ferrugem=0.3), 0.5, 0.5),
    'zarcao': sujo(mats.material('Zarcão', (0.42, 0.12, 0.04), 0, 0.7, desgaste=0.8, sujeira=0.8, ferrugem=0.5), 0.6, 0.5),
    'amarelo': sujo(mats.material('Amarelo trocado', (0.62, 0.40, 0.04), 0, 0.5, desgaste=1.0, sujeira=1.0, ferrugem=0.5), 0.8, 0.6, 0.3),
    'grafite': sujo(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.8, sujeira=0.85), 0.6, 0.6),
    'aco': sujo(mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True), 0.6, 0.4),
    'ferro': sujo(mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.95, sujeira=0.9), 0.5, 0.5),
    'cano': sujo(mats.material('Cano', (0.30, 0.31, 0.32), 1.0, 0.5, pintura=False, ferrugem=0.9, sujeira=0.9), 0.5, 0.5),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'latao': sujo(mats.material('Latão', (0.62, 0.45, 0.16), 1.0, 0.32, pintura=False, sujeira=0.8), 0.9, 0.2, 0.0),
    'bronze': mats.material('Bronze', (0.55, 0.36, 0.17), 1.0, 0.35, pintura=False, sujeira=0.8, ferrugem=0.25),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'concreto': sujo(mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0), 0.7, 0.6),
    'terra': terra_mat(),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'trancado': sujo(mats.material('Trançado', (0.38, 0.38, 0.37), 1.0, 0.5, pintura=False, sujeira=0.9, ferrugem=0.5, escovado=True), 0.7, 0.5),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'fio_verm': mats.material('Fio vermelho', (0.5, 0.03, 0.02), 0, 0.4, pintura=False, sujeira=0.3, desgaste=0.0),
    'fio_amar': mats.material('Fio amarelo', (0.7, 0.5, 0.03), 0, 0.4, pintura=False, sujeira=0.3, desgaste=0.0),
    'fio_azul': mats.material('Fio azul', (0.03, 0.1, 0.45), 0, 0.4, pintura=False, sujeira=0.3, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.8, desgaste=0.0),
    'ponteiro': mats.material('Ponteiro', (0.5, 0.05, 0.02), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'vidro_man': emissivo('Vidro do manômetro', (0.05, 0.04, 0.06), 0.0, (0.6, 0.6, 0.55)),
    'estencil': mats.material('Estêncil', (0.62, 0.6, 0.55), 0, 0.6, desgaste=1.0, sujeira=1.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'cal': mats.material('Cal', (0.70, 0.68, 0.60), 0, 0.95, pintura=False, sujeira=0.5, desgaste=0.0),
    'lama': mats.material('Lama', (0.11, 0.08, 0.05), 0, 0.75, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.02, 0.018, 0.017), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'cinza': mats.material('Cinza', (0.08, 0.078, 0.075), 0, 0.98, pintura=False, sujeira=0.3, desgaste=0.0),
    'molhado': mats.material('Chão molhado', (0.035, 0.028, 0.02), 0, 0.07, pintura=False, sujeira=0.2, desgaste=0.0),
    'capim': mats.material('Capim seco', (0.42, 0.33, 0.16), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
    'capim2': mats.material('Capim seco claro', (0.55, 0.46, 0.27), 0, 0.75, pintura=False, sujeira=0.4, desgaste=0.0),
    'galho': mats.material('Galho seco', (0.16, 0.12, 0.08), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'folha': mats.material('Folha seca', (0.32, 0.18, 0.07), 0, 0.8, pintura=False, sujeira=0.4, desgaste=0.0),
    'carvao': mats.material('Galho queimado', (0.015, 0.014, 0.013), 0, 0.7, pintura=False, sujeira=0.0, desgaste=0.0),
    'pedra': mats.material('Pedra', (0.2, 0.19, 0.17), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'brasa': emissivo('Brasa', (1.0, 0.3, 0.04), 14.0, (0.1, 0.03, 0.01)),
    'brasa_fraca': emissivo('Brasa apagando', (1.0, 0.22, 0.03), 3.0, (0.05, 0.02, 0.01)),
    'ia': emissivo('Faixa da IA', VIOLETA, 6.0, (0.05, 0.02, 0.1)),
    'olho_ir': emissivo('Olho infravermelho', (1.0, 0.08, 0.04), 9.0, (0.1, 0.0, 0.0)),
    'lente': emissivo('Lente', (0.02, 0.0, 0.03), 0.0, (0.02, 0.015, 0.03)),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'visor': vidro_mat('Visor de nível'),
    'agua_visor': emissivo('Água do visor', (0.0, 0.0, 0.0), 0.0, (0.25, 0.35, 0.38)),
    'jato': jato_mat(),
    'gota': agua_mat(),
    'fogo': nuvem_mat('Fogo', (0.04, 0.015, 0.005), (0.04, 0.015, 0.005), 12.0, 3.6, (1.0, 0.3, 0.03), 22.0, (0.38, 0.6), True),
    'fumaca': nuvem_mat('Fumaça', (0.012, 0.011, 0.01), (0.3, 0.3, 0.3), 9.0, 2.2),
    'vapor': nuvem_mat('Vapor', (0.86, 0.87, 0.89), (0.95, 0.95, 0.96), 7.0, 2.3, corte=(0.3, 0.6)),
    'nevoa': nuvem_mat('Névoa', (0.9, 0.92, 0.95), (0.9, 0.92, 0.95), 2.2, 3.0, corte=(0.3, 0.65)),
})

# ------------------------------------------------------------------ medidas
Z_LAJE = 0.08
Z_GIRO = 0.77                 # topo da coroa: pivô da torre
Z_MUN = 0.27                  # munhão acima do pivô
Y_LINHA, Z_LINHA, R_LINHA = -0.30, 0.24, 0.05
X_VAL = -0.25                 # válvula de dilúvio
RES = Vector((-0.28, 0.28))   # reservatório
R_RES, Z_RES0, Z_RES1 = 0.15, 0.17, 0.64
MASTRO = Vector((0.40, -0.40))
Z_MASTRO = 1.08
ARM = Vector((0.31, 0.30))

# ------------------------------------------------------------------ laje, listras, chumbadores
caixa_de(B('laje', 'concreto'), (-0.49, -0.49, 0), (0.49, 0.49, Z_LAJE))
for (a, b) in (((-0.49, -0.49), (0.49, -0.44)), ((-0.49, 0.44), (0.49, 0.49)), ((-0.49, -0.44), (-0.44, 0.44)), ((0.44, -0.44), (0.49, 0.44))):
    caixa_de(B('listras_laje', 'listras'), (a[0], a[1], Z_LAJE), (b[0], b[1], Z_LAJE + 0.003))
for k in range(30):                                                        # lascas no concreto da borda
    s = random.choice((-1, 1))
    if random.random() < 0.5:
        p = Vector((random.uniform(-0.48, 0.48), s * 0.49, random.uniform(0.02, 0.07)))
    else:
        p = Vector((s * 0.49, random.uniform(-0.48, 0.48), random.uniform(0.02, 0.07)))
    pedra(B('lascas', 'concreto'), p, random.uniform(0.008, 0.02), 0.6)
for k in range(10):                                                        # lama respingada na laje
    mancha(B('lama_laje', 'lama'), (random.uniform(-0.46, 0.46), random.choice((-0.46, 0.46)) * random.uniform(0.8, 1.0)),
           random.uniform(0.02, 0.06), Z_LAJE + 0.0035)

# ------------------------------------------------------------------ pedestal fixo
P = 'pedestal'
cil(B(P, 'vermelho', True), Vector((0, 0, Z_LAJE + 0.015)), 0.22, 0.03, lados=40)
cil(B(P, 'vermelho', True), Vector((0, 0, 0.405)), 0.125, 0.59, lados=40)
cil(B(P, 'vermelho', True), Vector((0, 0, 0.7125)), 0.18, 0.025, lados=40)
toro(B(P, 'vermelho', True), Vector((0, 0, 0.11)), 0.125, 0.012, Z, 40, 8)                    # cordão de solda
for k in range(8):                                                         # chumbadores com porca
    a = k * PI / 4 + PI / 8
    p = Vector((math.cos(a) * 0.19, math.sin(a) * 0.19, Z_LAJE + 0.03))
    cil(B('chumbadores', 'aco'), p + Vector((0, 0, 0.012)), 0.011, 0.024, lados=6)
    cil(B('chumbadores', 'aco'), p + Vector((0, 0, 0.03)), 0.006, 0.03, lados=8)
    escorrido(Vector((math.cos(a) * 0.205, math.sin(a) * 0.205, Z_LAJE + 0.03)), Vector((math.cos(a), math.sin(a), 0)), 0.02, w=0.008)
for k in range(6):                                                         # nervuras (fora do sul: entrada d'água)
    a = math.radians(-60 + k * 60 + 30)
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    perfil = [(0.12, 0.0), (0.21, 0.0), (0.12, 0.2)]
    prisma(B(P, 'vermelho'), perfil, d, Z, t, Vector((0, 0, Z_LAJE + 0.03)), -0.006, 0.006)
for k in range(12):                                                        # parafusos do flange de cima
    a = k * PI / 6
    parafuso(Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 0.725)), Z)
# coroa dentada fixa (o pinhão do motor de giro anda nela)
cil(B('coroa', 'ferro', True), Vector((0, 0, 0.745)), 0.165, 0.04, lados=48)
engrenagem(B('coroa_dentes', 'aco'), Vector((0, 0, 0.745)), Z, 0.165, 64, 0.018, 0.036)
# tampa de inspeção aparafusada (para robôs de reparo) com remendo e estêncil
AH = math.radians(232)
chapa_curva(B('tampa_insp', 'vermelho2', True), (0, 0), 0.125, AH - 0.5, AH + 0.5, 0.27, 0.5, 0.008)
for dz in (0.285, 0.485):
    for da in (-0.42, 0.0, 0.42):
        d = Vector((math.cos(AH + da), math.sin(AH + da), 0))
        parafuso(Vector((0, 0, dz)) + d * 0.134, d, r=0.006)
        escorrido(Vector((0, 0, dz - 0.008)) + d * 0.1335, d, random.uniform(0.02, 0.06), w=0.005)
estencil_cil((0, 0), 0.1335, AH - 0.4, 0.43, 'SF', 0.03)
estencil_cil((0, 0), 0.1335, AH - 0.4, 0.33, '0417', 0.03)
for k in range(5):                                                         # ferrugem escorrendo do flange de cima
    a = random.uniform(0, 2 * PI)
    escorrido(Vector((math.cos(a) * 0.126, math.sin(a) * 0.126, 0.7)), Vector((math.cos(a), math.sin(a), 0)), random.uniform(0.08, 0.25), w=0.007)
# caixa de junção dos cabos no pedestal (nordeste) e anel coletor
d45 = Vector((math.cos(PI / 4), math.sin(PI / 4), 0))
caixa(B('caixa_juncao', 'grafite'), d45 * 0.16 + Vector((0, 0, 0.55)), (0.1, 0.07, 0.14), Matrix.Rotation(PI / 4 - PI / 2, 3, 'Z'))
for dz in (-0.05, 0.05):
    for dt in (-0.035, 0.035):
        parafuso(d45 * 0.196 + Vector((-d45.y, d45.x, 0)) * dt + Vector((0, 0, 0.55 + dz)), d45, r=0.005)
cil(B('led', 'led_verde'), d45 * 0.196 + Vector((0, 0, 0.6)), 0.006, 0.006, d45, lados=8)
cil(B('led', 'led_ambar'), d45 * 0.196 + Vector((-d45.y, d45.x, 0)) * 0.02 + Vector((0, 0, 0.6)), 0.006, 0.006, d45, lados=8)

# ------------------------------------------------------------------ cano de entrada (oeste), válvula de dilúvio, T
cano([(-1.9, Y_LINHA, Z_LINHA), (-0.52, Y_LINHA, Z_LINHA)], R_LINHA, 'cano', fl_pontas=False)
flange(Vector((-0.515, Y_LINHA, Z_LINHA)), X, 0.085, 0.022, 8)            # par de flanges na borda: porta de entrada
flange(Vector((-0.49, Y_LINHA, Z_LINHA)), X, 0.085, 0.022, 8, mat='vermelho')
for x in (-0.95, -1.5):                                                    # selas no chão segurando o cano de fora
    caixa_de(B('selas', 'ferro'), (x - 0.04, Y_LINHA - 0.07, 0.0), (x + 0.04, Y_LINHA + 0.07, 0.17))
    toro(B('selas', 'ferro'), Vector((x, Y_LINHA, Z_LINHA)), R_LINHA + 0.006, 0.006, X, 24, 6)
    pedra(B('pedras', 'pedra'), Vector((x + 0.08, Y_LINHA + 0.1, 0.0)), 0.04)
cano([(-0.49, Y_LINHA, Z_LINHA), (X_VAL - 0.11, Y_LINHA, Z_LINHA)], R_LINHA, 'vermelho', fl_pontas=False)
esfera(B('te', 'vermelho', True), Vector((-0.4, Y_LINHA, Z_LINHA)), R_LINHA + 0.008)          # T para o reservatório
cano([(-0.4, Y_LINHA, Z_LINHA), (-0.4, -0.2, Z_LINHA)], 0.032, 'vermelho', fl_pontas=False)
flange(Vector((-0.4, -0.205, Z_LINHA)), Y, 0.055, 0.016, 6)
cano([(X_VAL + 0.11, Y_LINHA, Z_LINHA), (0.0, Y_LINHA, Z_LINHA), (0.0, -0.125, Z_LINHA)], R_LINHA, 'vermelho', fl_pontas=False)
flange(Vector((0.0, -0.135, Z_LINHA)), Y, 0.08, 0.02, 8)                  # boca do pedestal
flange(Vector((X_VAL - 0.105, Y_LINHA, Z_LINHA)), X, 0.088, 0.022, 8)
flange(Vector((X_VAL + 0.105, Y_LINHA, Z_LINHA)), X, 0.088, 0.022, 8)
# corpo globular da válvula, castelo e cavalete
VC = Vector((X_VAL, Y_LINHA, Z_LINHA))
bmv = B('valvula', 'vermelho', True)
bmesh.ops.create_uvsphere(bmv, u_segments=32, v_segments=16, radius=1.0,
                          matrix=Matrix.Translation(VC) @ Matrix.Diagonal((0.1, 0.085, 0.085, 1)))
tubo(bmv, VC - X * 0.1, VC + X * 0.1, 0.062, 28)
cil(bmv, VC + Vector((0, 0, 0.09)), 0.062, 0.05, lados=28)
flange(VC + Vector((0, 0, 0.12)), Z, 0.075, 0.018, 8)
cil(bmv, VC + Vector((0, 0, 0.14)), 0.05, 0.03, lados=28)                  # castelo
cil(B('gaxeta', 'latao', True), VC + Vector((0, 0, 0.165)), 0.02, 0.025, lados=12)
Z_CAV0, Z_CAV1 = Z_LINHA + 0.155, Z_LINHA + 0.36
for s in (-1, 1):                                                          # colunas do cavalete
    tubo(B('cavalete', 'aco', True), VC + Vector((s * 0.045, 0, 0.15)), VC + Vector((s * 0.045, 0, 0.35)), 0.011, 12)
caixa(B('cavalete_placa', 'ferro'), VC + Vector((0, 0, 0.355)), (0.13, 0.08, 0.016))
for s in (-1, 1):
    for t in (-1, 1):
        parafuso(VC + Vector((s * 0.05, t * 0.028, 0.365)), Z, r=0.006)
# escala de abertura (régua) presa numa coluna
caixa(B('regua', 'latao'), VC + Vector((0.058, -0.012, 0.24)), (0.004, 0.012, 0.12))
for k in range(7):
    caixa(B('regua_marcas', 'grafite'), VC + Vector((0.0605, -0.012, 0.19 + k * 0.016)), (0.0015, 0.008, 0.002))
# drenagem da válvula pingando: tubinho para baixo, poça com cal
tubo(B('dreno', 'latao', True), VC + Vector((0.02, -0.06, -0.05)), VC + Vector((0.02, -0.11, -0.05)), 0.008, 10)
tubo(B('dreno', 'latao', True), VC + Vector((0.02, -0.11, -0.05)), VC + Vector((0.02, -0.11, -0.13)), 0.008, 10)
esfera(B('dreno', 'latao', True), VC + Vector((0.02, -0.11, -0.05)), 0.008, 10)
for k in range(5):
    mancha(B('cal_chao', 'cal'), (X_VAL + 0.02 + random.uniform(-0.04, 0.04), Y_LINHA - 0.11 + random.uniform(-0.03, 0.03)),
           random.uniform(0.015, 0.04), Z_LAJE + 0.004 + k * 0.0003)
mancha(B('poca', 'molhado'), (X_VAL + 0.02, Y_LINHA - 0.11), 0.05, Z_LAJE + 0.0055)
for x in (-0.012, 0.01):                                                   # crosta de cal no flange de saída
    escorrido(Vector((X_VAL + 0.105 + x, Y_LINHA - 0.087, Z_LINHA - 0.005)), Vector((0, -1, 0)), 0.05, 'cal', 0.007)
# manômetros do trim (antes e depois)
manometro(Vector((X_VAL - 0.15, Y_LINHA, Z_LINHA + R_LINHA)), Z, Vector((-0.3, -1, 0)))
manometro(Vector((X_VAL + 0.16, Y_LINHA, Z_LINHA + R_LINHA)), Z, Vector((0.2, -1, 0)))

# pistão hidráulico no cavalete: camisa fixa apontando para baixo, haste levanta o acoplamento
CAM0 = Z_CAV1 + 0.012
cil(B('pistao_camisa', 'amarelo', True), VC + Vector((0, 0, CAM0 + 0.1)), 0.034, 0.2, lados=24)
for dz in (0.008, 0.192):
    cil(B('pistao_tampas', 'ferro', True), VC + Vector((0, 0, CAM0 + dz)), 0.04, 0.018, lados=24)
for k in range(4):                                                         # tirantes
    a = k * PI / 2 + PI / 4
    tubo(B('pistao_tirantes', 'aco'), VC + Vector((math.cos(a) * 0.034, math.sin(a) * 0.034, CAM0)),
         VC + Vector((math.cos(a) * 0.034, math.sin(a) * 0.034, CAM0 + 0.205)), 0.0035, 6)
PORTA_A = VC + Vector((0, -0.04, CAM0 + 0.03))
PORTA_B = VC + Vector((0, -0.04, CAM0 + 0.17))
for pp in (PORTA_A, PORTA_B):
    caixa(B('pistao_portas', 'ferro'), pp + Vector((0, 0.008, 0)), (0.022, 0.016, 0.022))
escorrido(VC + Vector((0.02, -0.035, CAM0 + 0.02)), Vector((0, -1, 0)), 0.1, 'oleo', 0.006)
# bloco de solenoide (alimentado pela água do T) e mangueiras até as portas
SOL = VC + Vector((0.0, -0.13, CAM0 + 0.07))
caixa(B('solenoide', 'grafite'), SOL, (0.07, 0.05, 0.06))
cil(B('solenoide_bob', 'amarelo', True), SOL + Vector((0, 0, 0.05)), 0.018, 0.04, lados=16)
cil(B('solenoide_bob', 'ferro', True), SOL + Vector((0, 0, 0.075)), 0.01, 0.01, lados=8)
caixa_de(B('solenoide_sup', 'ferro'), VC + Vector((-0.012, -0.11, CAM0 - 0.01)), VC + Vector((0.012, -0.03, CAM0 - 0.003)))
caixa_de(B('solenoide_sup', 'ferro'), VC + Vector((-0.012, -0.112, CAM0 - 0.01)), VC + Vector((0.012, -0.105, CAM0 + 0.04)))
cil(B('led', 'led_verde'), SOL + Vector((0.0, -0.026, 0.015)), 0.005, 0.004, Y, lados=8)
for k, pp in enumerate((PORTA_A, PORTA_B)):
    s0 = SOL + Vector((0.035, 0.0, -0.015 + 0.03 * k))
    pts = catmull([s0, s0 + Vector((0.04, 0.02, 0.0)), pp + Vector((0.03, -0.03, 0)), pp + Vector((0, -0.008, 0))], 6)
    varrer(B('mangueiras_hid', 'borracha', True), pts, 0.0065, 10)
    cil(B('terminais', 'latao', True), pp + Vector((0, -0.012, 0)), 0.009, 0.012, Y, lados=6)
# tubinho de cobre: tomada no T → solenoide
tp = Vector((-0.4, Y_LINHA, Z_LINHA + R_LINHA + 0.008))
cob = [tp, tp + Vector((0, 0, 0.1)), Vector((-0.4, SOL.y, Z_LINHA + 0.16)), Vector((-0.4, SOL.y, SOL.z - 0.015)), SOL + Vector((-0.035, 0, -0.015))]
cob = catmull(cob, 5)
varrer(B('cobre', 'cobre', True), cob, 0.005, 10)
for j in range(4, len(cob) - 1, 6):
    tubo(B('abracadeiras', 'aco'), cob[j] - (cob[j + 1] - cob[j]).normalized() * 0.006, cob[j] + (cob[j + 1] - cob[j]).normalized() * 0.006, 0.008, 8)
# escape do solenoide pingando na laje
ex = SOL + Vector((0.0, -0.025, -0.03))
varrer(B('cobre', 'cobre', True), [ex, ex + Vector((0, -0.02, -0.03)), Vector((ex.x, ex.y - 0.03, Z_LAJE + 0.06))], 0.004, 8)
mancha(B('cal_chao', 'cal'), (ex.x, ex.y - 0.03), 0.03, Z_LAJE + 0.004)

# ------------------------------------------------------------------ reservatório pressurizado + mangote trançado
R = 'reservatorio'
cil(B(R, 'vermelho', True), Vector((RES.x, RES.y, (Z_RES0 + Z_RES1) / 2)), R_RES, Z_RES1 - Z_RES0, lados=48)
for z0, s, mat in ((Z_RES0, -1, 'vermelho'), (Z_RES1, 1, 'vermelho2')):    # tampos abaulados (o de cima repintado)
    bmt = B('tampo_' + mat, mat, True)
    res = bmesh.ops.create_uvsphere(bmt, u_segments=48, v_segments=16, radius=1.0)
    for v in res['verts']:
        if v.co.z * s < 0:
            v.co.z = 0
        v.co = Vector((RES.x + v.co.x * R_RES, RES.y + v.co.y * R_RES, z0 + v.co.z * 0.075))
for z in (Z_RES0 + 0.01, Z_RES1 - 0.01, (Z_RES0 + Z_RES1) / 2):           # cordões de solda
    toro(B('solda', 'vermelho', True), Vector((RES.x, RES.y, z)), R_RES, 0.006, Z, 48, 6)
for k in range(3):                                                         # pés soldados
    a = k * 2 * PI / 3 + 0.5
    d = Vector((math.cos(a), math.sin(a), 0))
    p = Vector((RES.x, RES.y, 0)) + d * (R_RES - 0.02)
    viga(B('pes', 'ferro'), p + Vector((0, 0, Z_LAJE + 0.01)), p + Vector((0, 0, Z_RES0 + 0.03)), 0.03)
    caixa(B('pes', 'ferro'), p + Vector((0, 0, Z_LAJE + 0.005)), (0.06, 0.06, 0.01))
    parafuso(p + d * 0.02 + Vector((0, 0, Z_LAJE + 0.012)), Z)
# bocal de saída (sul) e mangote flexível trançado até o T
NB = Vector((-0.4, RES.y - math.sqrt(R_RES ** 2 - (RES.x + 0.4) ** 2) + 0.01, Z_LINHA))
cano([NB, Vector((-0.4, 0.135, Z_LINHA))], 0.032, 'vermelho', fl_pontas=False)
flange(Vector((-0.4, 0.13, Z_LINHA)), Y, 0.055, 0.016, 6)
H0, H1 = Vector((-0.4, 0.118, Z_LINHA)), Vector((-0.4, -0.193, Z_LINHA))
hose = [H0 + (H1 - H0) * (i / 30) + Vector((0.012 * math.sin(i / 30 * PI), 0, -0.035 * math.sin(i / 30 * PI))) for i in range(31)]
varrer(B('mangote', 'trancado', True), hose, 0.03, 16)
for j in range(2, 29, 2):
    u = (hose[j + 1] - hose[j - 1]).normalized()
    toro(B('mangote_ondas', 'trancado', True), hose[j], 0.03, 0.004, u, 20, 6)
for pp, u in ((H0, -Y), (H1, Y)):
    cil(B('mangote_ponteiras', 'aco', True), pp + u * 0.008, 0.036, 0.03, Y, lados=6)
# visor de nível (oeste), manômetro e válvula de alívio (topo, lado de fora), remendo, placa
XV = RES.x - R_RES - 0.03
for z in (Z_RES0 + 0.05, Z_RES1 - 0.05):
    tubo(B('visor_canos', 'latao', True), Vector((RES.x - R_RES + 0.005, RES.y, z)), Vector((XV, RES.y, z)), 0.008, 10)
    cil(B('visor_canos', 'latao', True), Vector((XV, RES.y, z)), 0.014, 0.03, lados=8)
tubo(B('visor_vidro', 'visor', True), Vector((XV, RES.y, Z_RES0 + 0.065)), Vector((XV, RES.y, Z_RES1 - 0.065)), 0.009, 16)
tubo(B('visor_agua', 'agua_visor', True), Vector((XV, RES.y, Z_RES0 + 0.065)), Vector((XV, RES.y, 0.48)), 0.0065, 12)
for z in (0.3, 0.45):
    viga(B('visor_guarda', 'aco'), Vector((XV - 0.012, RES.y - 0.012, Z_RES0 + 0.06)), Vector((XV - 0.012, RES.y - 0.012, Z_RES1 - 0.06)), 0.004)
    viga(B('visor_guarda', 'aco'), Vector((XV - 0.012, RES.y + 0.012, Z_RES0 + 0.06)), Vector((XV - 0.012, RES.y + 0.012, Z_RES1 - 0.06)), 0.004)
dno = Vector((-1, 1, 0)).normalized()
TOPO = Vector((RES.x, RES.y, Z_RES1 + 0.06)) + dno * 0.07
manometro(TOPO + Vector((0, 0, -0.012)), Z, dno, r=0.034)
VAL = Vector((RES.x, RES.y, Z_RES1 + 0.07)) + Vector((1, 1, 0)).normalized() * 0.04 + dno * 0.03
cil(B('alivio', 'latao', True), VAL + Vector((0, 0, 0.005)), 0.018, 0.04, lados=12)
for k in range(4):
    cil(B('alivio_mola', 'aco', True), VAL + Vector((0, 0, 0.032 + k * 0.012)), 0.014, 0.004, lados=12)
cil(B('alivio', 'latao', True), VAL + Vector((0, 0, 0.08)), 0.01, 0.014, lados=8)
tubo(B('alivio', 'latao', True), VAL + Vector((0, 0, 0.012)), VAL + Vector((0, 0, 0.012)) + dno * 0.05, 0.008, 10)
# remendo curvo aparafusado (nordeste)
a0, a1, z0, z1, na = math.radians(20), math.radians(75), 0.33, 0.5, 10
chapa_curva(B('remendo', 'zarcao', True), RES, R_RES, a0, a1, z0, z1, 0.005, na)
for i in range(0, na + 1, 2):
    for z in (z0 + 0.012, z1 - 0.012):
        a = a0 + (a1 - a0) * i / na
        d = Vector((math.cos(a), math.sin(a), 0))
        parafuso(Vector((RES.x, RES.y, z)) + d * (R_RES + 0.006), d, r=0.005)
    a = a0 + (a1 - a0) * i / na
    d = Vector((math.cos(a), math.sin(a), 0))
    escorrido(Vector((RES.x, RES.y, z0)) + d * (R_RES + 0.002), d, random.uniform(0.04, 0.12), w=0.006)
# placa com número de série apagado (sul-sudoeste, virada para a câmera)
ap = math.radians(245)
dp = Vector((math.cos(ap), math.sin(ap), 0))
tp_ = Vector((-dp.y, dp.x, 0))
PC = Vector((RES.x, RES.y, 0.42)) + dp * (R_RES + 0.004)
chapa_curva(B('placa', 'vermelho2', True), RES, R_RES, ap - 0.42, ap + 0.42, 0.37, 0.47, 0.004)
for da in (-0.37, 0.37):
    for z in (0.38, 0.46):
        d = Vector((math.cos(ap + da), math.sin(ap + da), 0))
        parafuso(Vector((RES.x, RES.y, z)) + d * (R_RES + 0.005), d, r=0.004)
estencil_cil(RES, R_RES + 0.004, ap - 0.3, 0.425, 'PA-27', 0.026)
estencil_cil(RES, R_RES + 0.004, ap - 0.3, 0.385, '0948', 0.02, apagado=0.55)
for k in range(8):                                                         # ferrugem escorrendo pelo casco
    a = random.uniform(0, 2 * PI)
    d = Vector((math.cos(a), math.sin(a), 0))
    escorrido(Vector((RES.x, RES.y, random.uniform(0.35, Z_RES1))) + d * R_RES, d, random.uniform(0.06, 0.2), w=0.007)

# ------------------------------------------------------------------ armário de controle selado (nordeste)
A0 = Vector((ARM.x - 0.13, ARM.y - 0.11, Z_LAJE))
A1 = Vector((ARM.x + 0.13, ARM.y + 0.11, 0.52))
caixa_de(B('armario', 'vermelho'), A0 + Vector((0.01, 0.01, 0.0)), A1 - Vector((0.01, 0.01, 0.0)))
caixa_de(B('armario_tampa', 'grafite'), (A0.x - 0.005, A0.y - 0.005, A1.z), (A1.x + 0.005, A1.y + 0.005, A1.z + 0.02))
caixa_de(B('armario_base', 'ferro'), (A0.x - 0.01, A0.y - 0.01, Z_LAJE), (A1.x + 0.01, A1.y + 0.01, Z_LAJE + 0.03))
for k in range(9):                                                         # aletas de dissipação (leste)
    y = A0.y + 0.03 + k * 0.02
    caixa_de(B('armario_aletas', 'aco'), (A1.x - 0.01, y - 0.003, 0.16), (A1.x + 0.035, y + 0.003, 0.46))
for k in range(5):                                                         # venezianas (sul)
    caixa(B('armario_veneziana', 'grafite'), Vector((ARM.x, A0.y + 0.006, 0.18 + k * 0.025)), (0.16, 0.012, 0.006),
          Matrix.Rotation(-0.6, 3, 'X'))
caixa_de(B('faixa_ia', 'ia'), (ARM.x - 0.1, A0.y + 0.007, 0.43), (ARM.x + 0.1, A0.y + 0.0085, 0.44))
for k, m in enumerate(('led_verde', 'led_ambar', 'led_verde', 'olho_ir')):
    cil(B('led_' + m, m), Vector((ARM.x - 0.06 + k * 0.03, A0.y + 0.006, 0.47)), 0.006, 0.006, Y, lados=8)
for x in (A0.x + 0.02, A1.x - 0.02):                                       # painéis aparafusados (sem porta)
    for z in (0.12, 0.3, 0.48):
        parafuso(Vector((x, A0.y + 0.008, z)), -Y, r=0.005)
estencil(Vector((ARM.x - 0.1, A0.y + 0.008, 0.36)), X, Z, -Y, 'SF-17', 0.028)
for k in range(5):
    x = random.uniform(A0.x + 0.03, A1.x - 0.03)
    escorrido(Vector((x, A0.y + 0.01, A1.z - 0.01)), -Y, random.uniform(0.05, 0.2), w=0.007)
# prensa-cabos (oeste) e fiação exposta saindo de um conduíte quebrado
GL = Vector((A0.x + 0.01, ARM.y, 0.16))
for dy in (-0.06, 0.0, 0.06):
    cil(B('prensa_cabos', 'latao', True), GL + Vector((-0.012, dy, 0)), 0.014, 0.024, X, lados=6)
pts = catmull([GL + Vector((-0.024, 0.06, 0)), GL + Vector((-0.06, 0.06, -0.03)), Vector((GL.x - 0.08, ARM.y + 0.06, Z_LAJE + 0.03))], 5)
varrer(B('conduite', 'cabo', True), pts, 0.011, 12)
for k, m in enumerate(('fio_verm', 'fio_amar', 'fio_azul')):               # conduíte rachado: fios aparecem
    c0 = pts[3]
    pf = [c0 + Vector((0.0, 0.008 * (k - 1), 0.004)), c0 + Vector((-0.018, 0.012 * (k - 1), 0.03 + 0.006 * k)),
          c0 + Vector((-0.004, 0.006 * (k - 1), 0.045)), pts[1] + Vector((0, 0.004 * (k - 1), 0.0))]
    varrer(B('fios', m, True), catmull(pf, 5), 0.0028, 6)

# ------------------------------------------------------------------ eletrocalhas e cabos
def calha(a, b, w=0.06, h=0.03):
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    t = Vector((-d.y, d.x, 0))
    L = (b - a).length
    rot = Matrix((d, t, Z)).transposed()
    c = (a + b) / 2
    caixa(B('calha', 'aco'), c + Vector((0, 0, 0.002)), (L, w, 0.004), rot)
    for s in (-1, 1):
        caixa(B('calha', 'aco'), c + t * (s * w / 2) + Vector((0, 0, h / 2)), (L, 0.003, h), rot)
    for k in range(3):
        o = t * ((k - 1) * 0.016)
        tubo(B('calha_cabos', 'cabo', True), a + o + Vector((0, 0, 0.012)), b + o + Vector((0, 0, 0.012)), 0.0075, 8)
    n = int(L / 0.14)
    for k in range(1, n + 1):                                              # suportes chumbados
        p = a + d * (k * L / (n + 1))
        caixa(B('calha_sup', 'ferro'), p + Vector((0, 0, -0.003)), (0.02, w + 0.02, 0.006), rot)


ZC = Z_LAJE + 0.006
calha((A0.x - 0.01, ARM.y - 0.03, ZC), (0.17, 0.17, ZC))
calha((ARM.x + 0.05, A0.y - 0.01, ZC), (ARM.x + 0.05, MASTRO.y + 0.07, ZC))
calha((MASTRO.x - 0.07, MASTRO.y - 0.0, ZC), (-0.14, MASTRO.y - 0.0, ZC))
# cabo subindo da calha até a caixa de junção do pedestal
pj = d45 * 0.16 + Vector((0, 0, 0.48))
pts = catmull([Vector((0.17, 0.17, ZC + 0.012)), Vector((0.155, 0.155, 0.2)), pj + Vector((0, 0, -0.08)), pj], 5)
varrer(B('cabos', 'cabo', True), pts, 0.011, 10)
# cabo da calha sul subindo pelo suporte do solenoide
pts = catmull([Vector((-0.14, MASTRO.y, ZC + 0.012)), Vector((-0.2, MASTRO.y + 0.01, 0.12)), Vector((X_VAL, SOL.y - 0.005, CAM0 - 0.02)),
               SOL + Vector((0, -0.01, -0.03))], 5)
varrer(B('cabos', 'cabo', True), pts, 0.007, 10)

# ------------------------------------------------------------------ mastro de sensores (sudeste)
cil(B('mastro', 'vermelho', True), Vector((MASTRO.x, MASTRO.y, Z_LAJE + 0.01)), 0.07, 0.02, lados=6)
cil(B('mastro', 'vermelho', True), Vector((MASTRO.x, MASTRO.y, (Z_LAJE + Z_MASTRO) / 2)), 0.028, Z_MASTRO - Z_LAJE, lados=24)
for k in range(4):
    a = k * PI / 2 + PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    prisma(B('mastro', 'vermelho'), [(0.028, 0), (0.065, 0), (0.028, 0.1)], d, Z, Vector((-d.y, d.x, 0)),
           Vector((MASTRO.x, MASTRO.y, Z_LAJE + 0.02)), -0.004, 0.004)
    parafuso(Vector((MASTRO.x, MASTRO.y, Z_LAJE + 0.022)) + Vector((math.cos(a + PI / 4), math.sin(a + PI / 4), 0)) * 0.055, Z, r=0.006)
cil(B('mastro_topo', 'ferro', True), Vector((MASTRO.x, MASTRO.y, Z_MASTRO + 0.008)), 0.07, 0.016, lados=24)
# braço da câmara de fumaça (oeste) e do sensor de calor (norte)
ZB = Z_MASTRO - 0.12
viga(B('bracos', 'ferro'), Vector((MASTRO.x, MASTRO.y, ZB)), Vector((MASTRO.x - 0.16, MASTRO.y, ZB)), 0.02)
viga(B('bracos', 'ferro'), Vector((MASTRO.x, MASTRO.y, ZB - 0.08)), Vector((MASTRO.x - 0.1, MASTRO.y, ZB)), 0.012)
FUM = Vector((MASTRO.x - 0.16, MASTRO.y, ZB - 0.02))
cil(B('fumaca_cam', 'grafite', True), FUM + Vector((0, 0, 0.0)), 0.04, 0.012, lados=24)
for k in range(6):                                                         # venezianas da câmara de fumaça
    cil(B('fumaca_cam', 'grafite', True), FUM + Vector((0, 0, -0.012 - k * 0.012)), 0.042 - k * 0.002, 0.005, lados=24, r2=0.036 - k * 0.002)
cil(B('fumaca_nucleo', 'ferro', True), FUM + Vector((0, 0, -0.04)), 0.028, 0.07, lados=16)
cil(B('led_ia', 'ia'), FUM + Vector((0, 0, -0.09)), 0.008, 0.01, lados=12)
viga(B('bracos', 'ferro'), Vector((MASTRO.x, MASTRO.y, ZB + 0.04)), Vector((MASTRO.x, MASTRO.y + 0.15, ZB + 0.04)), 0.018)
CAL = Vector((MASTRO.x, MASTRO.y + 0.15, ZB + 0.03))
cil(B('calor_sens', 'aco', True), CAL + Vector((0, 0, -0.04)), 0.012, 0.08, lados=12)
for k in range(8):                                                         # aletas do sensor de calor
    cil(B('calor_aletas', 'cobre', True), CAL + Vector((0, 0, -0.012 - k * 0.009)), 0.024, 0.003, lados=20)
esfera(B('calor_bulbo', 'grafite', True), CAL + Vector((0, 0, -0.088)), 0.013, 12)
# para-raios (há raios no jogo): haste numa mão-francesa, cabo de descida pelo mastro até a laje
PR = Vector((MASTRO.x + 0.09, MASTRO.y - 0.09, Z_MASTRO - 0.05))
viga(B('bracos', 'ferro'), Vector((MASTRO.x, MASTRO.y, Z_MASTRO - 0.05)), PR, 0.016)
tubo(B('para_raios', 'cobre', True), PR, PR + Vector((0, 0, 0.42)), 0.006, 10)
cil(B('para_raios', 'cobre', True), PR + Vector((0, 0, 0.44)), 0.008, 0.04, lados=10, r2=0.0)
cil(B('isolador', 'grafite', True), PR + Vector((0, 0, 0.02)), 0.015, 0.03, lados=12)
desce = [PR + Vector((0.0, 0.0, 0.0)), PR + Vector((-0.04, 0.03, -0.06)), Vector((MASTRO.x + 0.035, MASTRO.y - 0.0, Z_MASTRO - 0.2)),
         Vector((MASTRO.x + 0.035, MASTRO.y, 0.3)), Vector((MASTRO.x + 0.045, MASTRO.y - 0.03, Z_LAJE + 0.01))]
desce = catmull(desce, 6)
varrer(B('cabo_raio', 'cobre', True), desce, 0.004, 8)
for j in range(6, len(desce) - 2, 5):
    tubo(B('abracadeiras', 'aco'), desce[j] - Z * 0.006, desce[j] + Z * 0.006, 0.007, 8)
# cabo de sinal subindo o mastro
sinal = catmull([Vector((MASTRO.x - 0.0, MASTRO.y + 0.07, ZC + 0.012)), Vector((MASTRO.x - 0.03, MASTRO.y + 0.03, 0.2)),
                 Vector((MASTRO.x - 0.032, MASTRO.y, 0.4)), Vector((MASTRO.x - 0.032, MASTRO.y, ZB - 0.1)),
                 Vector((MASTRO.x - 0.06, MASTRO.y, ZB - 0.03))], 6)
varrer(B('cabos', 'cabo', True), sinal, 0.006, 8)
for j in range(5, len(sinal) - 3, 4):
    tubo(B('abracadeiras', 'aco'), sinal[j] - Z * 0.006, sinal[j] + Z * 0.006, 0.0085, 8)
for k in range(4):
    escorrido(Vector((MASTRO.x, MASTRO.y - 0.028, random.uniform(0.4, 1.2))), -Y, random.uniform(0.06, 0.2), w=0.006)

# olho infravermelho girando (grupo 'olho', pivô no topo do mastro)
olho = bpy.data.objects.new('olho', None)
sc.collection.objects.link(olho)
olho.location = (MASTRO.x, MASTRO.y, Z_MASTRO + 0.016)
cil(B('olho_base', 'ferro', True, 'olho'), Vector((0, 0, 0.015)), 0.05, 0.03, lados=24)
bmo = B('olho_casco', 'vermelho', True, 'olho')
bmesh.ops.create_uvsphere(bmo, u_segments=24, v_segments=12, radius=1.0,
                          matrix=Matrix.Translation(Vector((0, 0, 0.085))) @ Matrix.Diagonal((0.07, 0.055, 0.055, 1)))
cil(B('olho_casco', 'vermelho', True, 'olho'), Vector((0.065, 0, 0.085)), 0.04, 0.03, X, lados=24)
toro(B('olho_aro', 'ferro', True, 'olho'), Vector((0.08, 0, 0.085)), 0.036, 0.006, X, 24, 8)
cil(B('olho_lente', 'lente', True, 'olho'), Vector((0.081, 0, 0.085)), 0.032, 0.004, X, lados=24)
cil(B('olho_iris', 'olho_ir', True, 'olho'), Vector((0.084, 0, 0.085)), 0.013, 0.003, X, lados=20)
toro(B('olho_anel', 'ia', True, 'olho'), Vector((0.083, 0, 0.085)), 0.022, 0.002, X, 24, 6)
caixa(B('olho_pala', 'grafite', False, 'olho'), Vector((0.07, 0, 0.128)), (0.06, 0.07, 0.006))
cil(B('olho_antena', 'aco', True, 'olho'), Vector((-0.04, 0.02, 0.17)), 0.003, 0.08, lados=6)
esfera(B('olho_antena', 'olho_ir', True, 'olho'), Vector((-0.04, 0.02, 0.21)), 0.006, 8)
for k in range(5):
    a = random.uniform(0, 2 * PI)
    parafuso(Vector((math.cos(a) * 0.045, math.sin(a) * 0.045, 0.06)), Vector((math.cos(a), math.sin(a), 0.3)), 'olho', r=0.004)

# ------------------------------------------------------------------ torre giratória
giro = bpy.data.objects.new('giro', None)
sc.collection.objects.link(giro)
giro.location = (0, 0, Z_GIRO)
G = 'giro'
cil(B('mesa', 'vermelho', True, G), Vector((0, 0, 0.045)), 0.24, 0.09, lados=48)
toro(B('mesa', 'vermelho', True, G), Vector((0, 0, 0.09)), 0.232, 0.008, Z, 48, 8)
cil(B('rolamento', 'ferro', True, G), Vector((0, 0, -0.0025)), 0.2, 0.005, lados=48)
for k in range(16):
    a = k * PI / 8 + 0.1
    parafuso(Vector((math.cos(a) * 0.218, math.sin(a) * 0.218, 0.09)), Z, G, 0.007)
for k in range(6):                                                         # escorridos de ferrugem na saia da mesa
    a = random.uniform(0, 2 * PI)
    escorrido(Vector((math.cos(a) * 0.24, math.sin(a) * 0.24, 0.08)), Vector((math.cos(a), math.sin(a), 0)), random.uniform(0.03, 0.07), g=G, w=0.007)
estencil_cil((0, 0), 0.24, math.radians(-75), 0.03, '0417', 0.032, G)
# bochechas com topo redondo e mancais
perfil = [(-0.1, 0.09), (0.1, 0.09)] + [(0.1 * math.cos(a), Z_MUN + 0.1 * math.sin(a)) for a in (i * PI / 12 for i in range(13))]
for s in (-1, 1):
    prisma(B('bochechas', 'vermelho', False, G), perfil, X, Z, Y, Vector((0, 0, 0)), s * 0.1, s * 0.125)
    cil(B('mancais', 'ferro', True, G), Vector((0, s * 0.135, Z_MUN)), 0.05, 0.02, Y, lados=28)
    for k in range(6):
        a = k * PI / 3
        parafuso(Vector((0.04 * math.cos(a), s * 0.146, Z_MUN + 0.04 * math.sin(a))), Vector((0, s, 0)), G, 0.005)
    caixa(B('bochechas_nervura', 'vermelho', False, G), Vector((-0.085, s * 0.1125, 0.15)), (0.02, 0.025, 0.12))
    caixa(B('bochechas_nervura', 'vermelho', False, G), Vector((0.085, s * 0.1125, 0.15)), (0.02, 0.025, 0.12))
# riser: da mesa até a junta rotativa no munhão (lado -y)
YJ = -0.165
cil(B('riser', 'vermelho', True, G), Vector((0, YJ, 0.11)), 0.038, 0.016, lados=24)
for k in range(6):
    a = k * PI / 3 + 0.3
    parafuso(Vector((0.03 * math.cos(a), YJ + 0.03 * math.sin(a), 0.12)), Z, G, 0.0045)
tubo(B('riser', 'vermelho', True, G), Vector((0, YJ, 0.1)), Vector((0, YJ, Z_MUN - 0.03)), 0.031, 24)
cil(B('junta', 'bronze', True, G), Vector((0, YJ, Z_MUN)), 0.052, 0.07, Y, lados=32)
cil(B('junta', 'bronze', True, G), Vector((0, YJ, Z_MUN - 0.045)), 0.036, 0.03, lados=24)
cil(B('junta_tampa', 'ferro', True, G), Vector((0, YJ - 0.04, Z_MUN)), 0.044, 0.012, Y, lados=24)
for k in range(6):
    a = k * PI / 3
    parafuso(Vector((0.033 * math.cos(a), YJ - 0.047, Z_MUN + 0.033 * math.sin(a))), -Y, G, 0.004)
cil(B('graxeira', 'latao', True, G), Vector((0, YJ, Z_MUN + 0.058)), 0.006, 0.014, lados=6)
escorrido(Vector((0.0, YJ - 0.03, Z_MUN - 0.04)), Vector((0, -1, 0)), 0.1, 'cal', 0.008, G)
escorrido(Vector((0.02, YJ - 0.031, Z_MUN - 0.045)), Vector((0, -1, 0)), 0.06, 'oleo', 0.005, G)
# motor de giro (amarelo: peça trocada de outra máquina) com redutor e pinhão sob a mesa
MG = Vector((-0.16, -0.15))
caixa(B('redutor_giro', 'ferro', False, G), Vector((MG.x, MG.y, 0.115)), (0.1, 0.1, 0.05))
cil(B('motor_giro', 'amarelo', True, G), Vector((MG.x, MG.y, 0.22)), 0.042, 0.16, lados=28)
for k in range(10):                                                        # aletas do motor
    cil(B('motor_giro_aletas', 'amarelo', True, G), Vector((MG.x, MG.y, 0.16 + k * 0.012)), 0.048, 0.004, lados=28)
cil(B('motor_giro_tampa', 'ferro', True, G), Vector((MG.x, MG.y, 0.305)), 0.036, 0.012, lados=24)
caixa(B('motor_giro_caixa', 'grafite', False, G), Vector((MG.x + 0.03, MG.y + 0.03, 0.25)), (0.04, 0.04, 0.04),
      Matrix.Rotation(PI / 4, 3, 'Z'))
cil(B('mesa_furo', 'ferro', True, G), Vector((MG.x, MG.y, -0.006)), 0.02, 0.012, lados=12)
escorrido(Vector((MG.x - 0.05, MG.y, 0.1)), Vector((-1, 0, 0)), 0.04, 'oleo', 0.008, G)
mancha(B('oleo_mesa', 'oleo', False, G), (MG.x + 0.02, MG.y + 0.07), 0.025, 0.0905)
pin_g = bpy.data.objects.new('pinhao_giro', None)
sc.collection.objects.link(pin_g)
pin_g.parent = giro
R_PG = math.hypot(MG.x, MG.y) - 0.185 - 0.004
pin_g.location = (MG.x, MG.y, -0.025)
cil(B('pinhao', 'aco', True, 'pin_g'), Vector((0, 0, 0)), R_PG - 0.008, 0.034, lados=20)
engrenagem(B('pinhao_dentes', 'aco', False, 'pin_g'), Vector((0, 0, 0)), Z, R_PG - 0.008, 12, 0.012, 0.032)
cil(B('pinhao', 'aco', True, 'pin_g'), Vector((0, 0, 0.017)), 0.01, 0.01, lados=10)
# caixa de eletrônica da torre (+y, atrás) com tampa faltando e fios à mostra
EB0, EB1 = Vector((-0.235, 0.035, 0.09)), Vector((-0.125, 0.19, 0.2))
caixa_de(B('eletronica', 'vermelho', False, G), EB0, EB1)
caixa_de(B('eletronica_tampa', 'grafite', False, G), (EB0.x - 0.004, EB0.y, EB1.z), (EB1.x + 0.004, EB1.y, EB1.z + 0.012))
caixa_de(B('eletronica_buraco', 'grafite', False, G), (EB0.x - 0.002, 0.07, 0.11), (EB0.x + 0.004, 0.16, 0.18))
for k, m in enumerate(('fio_verm', 'fio_amar', 'fio_azul', 'cabo')):
    pf = [Vector((EB0.x - 0.003, 0.085 + k * 0.02, 0.17)), Vector((EB0.x - 0.02, 0.09 + k * 0.022, 0.15 - k * 0.006)),
          Vector((EB0.x - 0.01, 0.1 + k * 0.016, 0.12)), Vector((EB0.x - 0.002, 0.11 + k * 0.012, 0.115))]
    varrer(B('fios_torre', m, True, G), catmull(pf, 5), 0.003, 6)
for x in (EB0.x + 0.02, EB1.x - 0.02):
    for y in (EB0.y + 0.02, EB1.y - 0.02):
        parafuso(Vector((x, y, EB1.z + 0.012)), Z, G, 0.005)
caixa_de(B('faixa_ia_torre', 'ia', False, G), (EB0.x + 0.015, EB1.y + 0.0005, 0.17), (EB1.x - 0.015, EB1.y + 0.002, 0.178))
cil(B('led_torre', 'led_ambar', False, G), Vector((EB1.x - 0.02, EB1.y + 0.001, 0.12)), 0.006, 0.005, Y, lados=8)
estencil(Vector((EB0.x + 0.012, EB1.y + 0.001, 0.115)), X, Z, Y, '17', 0.03, G)
# cabos: eletrônica → motor de giro e → motor de elevação
cg = catmull([Vector((EB0.x + 0.02, EB0.y, 0.13)), Vector((-0.2, -0.02, 0.12)), Vector((MG.x - 0.01, MG.y + 0.06, 0.15)),
              Vector((MG.x + 0.03, MG.y + 0.05, 0.25))], 6)
varrer(B('cabos_torre', 'cabo', True, G), cg, 0.007, 8)
# motor de elevação (+y): redutor colado na bochecha, pinhão no setor, motor grafite (trocado)
ANG_P = math.radians(-115)
RS = 0.1
DP = RS + 0.03
PE = Vector((DP * math.cos(ANG_P), 0.0, Z_MUN + DP * math.sin(ANG_P)))
caixa(B('redutor_elev', 'ferro', False, G), Vector((PE.x, 0.1375, PE.z)), (0.07, 0.025, 0.07))
for s in (-1, 1):
    for t in (-1, 1):
        parafuso(Vector((PE.x + s * 0.026, 0.15, PE.z + t * 0.026)), Y, G, 0.0045)
cil(B('motor_elev', 'grafite', True, G), Vector((PE.x, 0.245, PE.z)), 0.038, 0.13, Y, lados=28)
for k in range(8):
    cil(B('motor_elev_aletas', 'grafite', True, G), Vector((PE.x, 0.2 + k * 0.012, PE.z)), 0.044, 0.004, Y, lados=28)
cil(B('motor_elev_tampa', 'ferro', True, G), Vector((PE.x, 0.315, PE.z)), 0.032, 0.012, Y, lados=24)
cil(B('motor_elev_eixo', 'aco', True, G), Vector((PE.x, 0.165, PE.z)), 0.008, 0.035, Y, lados=10)
caixa(B('motor_elev_caixa', 'grafite', False, G), Vector((PE.x, 0.27, PE.z + 0.045)), (0.035, 0.04, 0.025))
ce = catmull([Vector((EB1.x, 0.17, 0.15)), Vector((-0.09, 0.22, 0.12)), Vector((PE.x, 0.27, PE.z + 0.06))], 6)
varrer(B('cabos_torre', 'cabo', True, G), ce, 0.006, 8)
pin_e = bpy.data.objects.new('pinhao_elev', None)
sc.collection.objects.link(pin_e)
pin_e.parent = giro
pin_e.location = (PE.x, 0.1625, PE.z)
R_PE = DP - RS - 0.004
cil(B('pinhao_e', 'aco', True, 'pin_e'), Vector((0, 0, 0)), R_PE - 0.007, 0.014, Y, lados=16)
engrenagem(B('pinhao_e_dentes', 'aco', False, 'pin_e'), Vector((0, 0, 0)), Y, R_PE - 0.007, 10, 0.012, 0.013)

# ------------------------------------------------------------------ canhão monitor (grupo 'eleva', pivô no munhão)
eleva = bpy.data.objects.new('eleva', None)
sc.collection.objects.link(eleva)
eleva.parent = giro
eleva.location = (0, 0, Z_MUN)
E = 'eleva'
PITCH0 = math.radians(32)
tubo(B('munhao', 'aco', True, E), Vector((0, -0.165, 0)), Vector((0, 0.17, 0)), 0.028, 20)
cil(B('berco', 'vermelho', True, E), Vector((0, 0, 0)), 0.062, 0.19, Y, lados=32)
for s in (-1, 1):
    toro(B('berco', 'vermelho', True, E), Vector((0, s * 0.095, 0)), 0.056, 0.006, Y, 32, 6)
cil(B('berco', 'vermelho', True, E), Vector((0.05, 0, 0)), 0.052, 0.06, X, lados=32)
cil(B('berco_traseira', 'ferro', True, E), Vector((-0.07, 0, 0)), 0.04, 0.02, X, lados=24)
for k in range(6):
    a = k * PI / 3
    parafuso(Vector((-0.08, 0.03 * math.cos(a), 0.03 * math.sin(a))), -X, E, 0.004)
X_B0, X_B1, X_N1 = 0.08, 0.36, 0.53
tubo(B('cano_canhao', 'vermelho', True, E), Vector((X_B0, 0, 0)), Vector((X_B1, 0, 0)), 0.04, 28)
flange(Vector((0.085, 0, 0)), X, 0.06, 0.016, 8, E)
flange(Vector((0.21, 0, 0)), X, 0.058, 0.016, 8, E)
flange(Vector((X_B1 - 0.004, 0, 0)), X, 0.056, 0.016, 8, E, 'aco')
# bocal: aletas estabilizadoras internas, cone de latão, anel jato/neblina serrilhado
BN = B('bocal', 'latao', True, E)
cil(BN, Vector(((X_B1 + X_N1) / 2, 0, 0)), 0.042, X_N1 - X_B1, X, lados=32, r2=0.022)
cil(B('anel', 'borracha', True, E), Vector((X_N1 - 0.06, 0, 0)), 0.04, 0.05, X, lados=32, r2=0.034)
for k in range(24):                                                        # serrilhado do anel
    a = k * 2 * PI / 24
    viga(B('anel_dentes', 'borracha', False, E), Vector((X_N1 - 0.084, 0.04 * math.cos(a), 0.04 * math.sin(a))),
         Vector((X_N1 - 0.036, 0.034 * math.cos(a), 0.034 * math.sin(a))), 0.007)
toro(B('bocal_ponta', 'latao', True, E), Vector((X_N1, 0, 0)), 0.021, 0.004, X, 24, 6)
cil(B('bocal_boca', 'fuligem', True, E), Vector((X_N1 + 0.0005, 0, 0)), 0.018, 0.002, X, lados=20)
# mira da IA em cima do canhão
caixa(B('mira', 'grafite', False, E), Vector((0.24, 0, 0.062)), (0.09, 0.04, 0.035))
caixa(B('mira_sup', 'ferro', False, E), Vector((0.24, 0, 0.042)), (0.04, 0.02, 0.012))
cil(B('mira_lente', 'lente', True, E), Vector((0.286, 0, 0.062)), 0.012, 0.004, X, lados=16)
toro(B('mira_anel', 'ia', True, E), Vector((0.288, 0, 0.062)), 0.012, 0.0018, X, 16, 6)
cil(B('mira_led', 'olho_ir', True, E), Vector((0.287, 0.0, 0.074)), 0.003, 0.003, X, lados=8)
mira_c = catmull([Vector((0.2, 0.0, 0.07)), Vector((0.13, 0.025, 0.06)), Vector((0.03, 0.06, 0.03)), Vector((0.0, 0.098, 0.0))], 6)
varrer(B('mira_cabo', 'cabo', True, E), mira_c, 0.004, 8)
# setor dentado da elevação (+y, fora da bochecha)
A_S = ANG_P - PITCH0
setor = [(0.0, 0.0)] + [(RS * math.cos(A_S + d), RS * math.sin(A_S + d)) for d in (math.radians(-35 + 70 * i / 12) for i in range(13))]
prisma(B('setor', 'ferro', False, E), setor, X, Z, Y, Vector((0, 0, 0)), 0.155, 0.17)
engrenagem(B('setor_dentes', 'aco', False, E), Vector((0, 0.1625, 0)), Y, RS, 20, 0.012, 0.014, A_S - math.radians(35), A_S + math.radians(35), (X, Z))
cil(B('setor', 'ferro', True, E), Vector((0, 0.1625, 0)), 0.035, 0.016, Y, lados=24)
# marcas de calor e fuligem no bocal: bolhas escuras (camada no material) + escorridos
for k in range(5):
    a = random.uniform(0, 2 * PI)
    caixa(B('fuligem_bocal', 'fuligem', False, E), Vector((random.uniform(0.25, 0.34), 0.0405 * math.cos(a), 0.0405 * math.sin(a))),
          (random.uniform(0.02, 0.05), 0.012, 0.002), Matrix.Rotation(a, 3, 'X'))

# ------------------------------------------------------------------ objetos estáticos
PAIS = {'base': None, 'giro': giro, 'eleva': eleva, 'pin_g': pin_g, 'pin_e': pin_e, 'olho': olho}
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(nome if g == 'base' else g + '_' + nome, bm, mat, PAIS[g])
    if liso:
        suavizar(o)
BMS.clear()

# acoplamento da válvula (sobe com a haste do pistão)
acopl = bpy.data.objects.new('acoplamento', None)
sc.collection.objects.link(acopl)
acopl.location = VC + Vector((0, 0, 0.21))
bm = bmesh.new()
caixa(bm, Vector((0, 0, 0)), (0.05, 0.03, 0.03))
obj('acopl_bloco', bm, 'ferro', acopl)
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.04)), 0.01, 0.07, lados=12)                       # haste da válvula
cil(bm, Vector((0, 0, 0.09)), 0.011, 0.17, lados=12)                       # haste do pistão (entra na camisa)
suavizar(obj('acopl_hastes', bm, 'cromo', acopl))
bm = bmesh.new()
caixa(bm, Vector((0.045, -0.012, 0)), (0.03, 0.004, 0.004))
obj('acopl_ponteiro', bm, 'ponteiro', acopl)

# ------------------------------------------------------------------ chão, capim seco, arbustos, fogo
bm = bmesh.new()
caixa(bm, (2, 1, -0.5), (60, 60, 1.0))
obj('chao', bm, 'terra')
FC = Vector((3.85, 1.65))       # centro do fogo
R_QUEIMA = 1.25
L_IMP = Vector((3.05, 1.28, 0.2))   # onde o jato cai (borda do fogo, do lado da máquina)


def dist_fogo(x, y):
    return math.hypot(x - FC.x, y - FC.y)


def touceira(bm, p, alt, n, lean=0.35, w=0.006):
    for k in range(n):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.0, 0.05)
        b = Vector((p.x + math.cos(a) * r, p.y + math.sin(a) * r, p.z))
        L = alt * random.uniform(0.6, 1.1)
        incl = random.uniform(0.1, lean)
        d = Vector((math.cos(a) * incl, math.sin(a) * incl, 1.0)).normalized()
        dd = d + Vector((math.cos(a), math.sin(a), -0.3)) * random.uniform(0.1, 0.5)
        lat = Vector((-math.sin(a + 0.4), math.cos(a + 0.4), 0)) * w
        m1 = b + d * L * 0.5
        tip = m1 + dd.normalized() * L * 0.5
        v = [bm.verts.new(b - lat), bm.verts.new(b + lat), bm.verts.new(m1 + lat * 0.6), bm.verts.new(m1 - lat * 0.6), bm.verts.new(tip)]
        bm.faces.new((v[0], v[1], v[2], v[3]))
        bm.faces.new((v[3], v[2], v[4]))


bmc, bmc2, bmq, bmz, bmb = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for k in range(1500):
    x, y = random.uniform(-4.5, 7.5), random.uniform(-4.0, 6.0)
    if abs(x) < 0.62 and abs(y) < 0.62:
        continue
    if abs(y - Y_LINHA) < 0.12 and x < -0.5:
        continue
    df = dist_fogo(x, y)
    if df < R_QUEIMA - 0.05:                                               # já queimado: toco preto e cinza
        touceira(bmq, Vector((x, y, 0)), 0.05, 5, 0.6, 0.004)
        if random.random() < 0.15:
            touceira(bmb, Vector((x, y, 0)), 0.02, 2, 0.6, 0.003)
        continue
    if df < R_QUEIMA + 0.25:                                               # frente do fogo: capim pegando
        touceira(bmz, Vector((x, y, 0)), 0.12, 10)
        continue
    touceira(bmc if random.random() < 0.6 else bmc2, Vector((x, y, 0)), random.uniform(0.18, 0.4), random.randint(10, 18))
for k in range(250):                                                       # capim extra denso perto (foto 0)
    x, y = random.uniform(-2.8, 2.2), random.uniform(-3.4, 1.5)
    if abs(x) < 0.62 and abs(y) < 0.62 or (abs(y - Y_LINHA) < 0.12 and x < -0.5):
        continue
    touceira(bmc if random.random() < 0.5 else bmc2, Vector((x, y, 0)), random.uniform(0.15, 0.32), random.randint(8, 14))
obj('capim', bmc, 'capim')
obj('capim_claro', bmc2, 'capim2')
obj('capim_queimado', bmq, 'carvao')
obj('capim_brasas', bmb, 'brasa')
obj('capim_frente', bmz, 'carvao')
# chão queimado, cinza, chão molhado onde o jato cai
bm = bmesh.new()
for k in range(40):
    a, r = random.uniform(0, 2 * PI), random.uniform(0, R_QUEIMA * 0.95)
    mancha(bm, (FC.x + math.cos(a) * r, FC.y + math.sin(a) * r), random.uniform(0.3, 0.6), 0.002 + k * 0.00005)
obj('chao_queimado', bm, 'fuligem')
bm = bmesh.new()
for k in range(25):
    a, r = random.uniform(0, 2 * PI), random.uniform(0, R_QUEIMA * 0.8)
    mancha(bm, (FC.x + math.cos(a) * r, FC.y + math.sin(a) * r), random.uniform(0.08, 0.25), 0.0045)
obj('cinza', bm, 'cinza')
bm = bmesh.new()
for k in range(14):
    a, r = random.uniform(0, 2 * PI), random.uniform(0, 0.35)
    mancha(bm, (L_IMP.x + math.cos(a) * r * 1.3, L_IMP.y + math.sin(a) * r), random.uniform(0.12, 0.3), 0.006)
obj('chao_molhado', bm, 'molhado')
bm = bmesh.new()
for k in range(160):                                                       # gravetos e folhas secas no chão
    x, y = random.uniform(-3.5, 6.5), random.uniform(-3.5, 5.0)
    if abs(x) < 0.6 and abs(y) < 0.6:
        continue
    a = random.uniform(0, PI)
    L = random.uniform(0.05, 0.22)
    d = Vector((math.cos(a), math.sin(a), 0))
    tubo(bm, Vector((x, y, 0.006)) - d * L / 2, Vector((x, y, 0.006)) + d * L / 2, random.uniform(0.003, 0.007), 5)
obj('gravetos', bm, 'galho')
bm = bmesh.new()
for k in range(260):
    x, y = random.uniform(-3.5, 6.5), random.uniform(-3.5, 5.0)
    if abs(x) < 0.6 and abs(y) < 0.6 or dist_fogo(x, y) < R_QUEIMA:
        continue
    mancha(bm, (x, y), random.uniform(0.008, 0.02), 0.003)
obj('folhas_chao', bm, 'folha')
for k in range(60):                                                        # pedras soltas
    x, y = random.uniform(-3, 6), random.uniform(-3, 5)
    if abs(x) < 0.7 and abs(y) < 0.7:
        continue
    pedra(B('pedras', 'pedra'), Vector((x, y, 0.0)), random.uniform(0.02, 0.07))


def arbusto(bg, bf, c, h, folhas=True):
    """Arbusto seco: galhos que se abrem em leque com ramos menores."""
    for k in range(random.randint(6, 9)):
        a = random.uniform(0, 2 * PI)
        incl = random.uniform(0.2, 0.75)
        d = Vector((math.cos(a) * incl, math.sin(a) * incl, 1.0)).normalized()
        L = h * random.uniform(0.7, 1.1)
        p0 = Vector((c.x, c.y, 0)) + Vector((math.cos(a), math.sin(a), 0)) * 0.03
        pts = [p0 + d * L * t + Vector((0, 0, -0.1 * L * t * t)) for t in (0, 0.35, 0.7, 1.0)]
        varrer(bg, catmull(pts, 3), lambda t: 0.012 * (1 - t) + 0.003, 6)
        for j in range(3):
            q = pts[1 + j % 3]
            a2 = a + random.uniform(-1.2, 1.2)
            d2 = Vector((math.cos(a2) * 0.8, math.sin(a2) * 0.8, 0.7)).normalized()
            L2 = L * random.uniform(0.2, 0.4)
            varrer(bg, [q, q + d2 * L2 * 0.5, q + d2 * L2], lambda t: 0.005 * (1 - t) + 0.0015, 5)
            if folhas and bf is not None:
                for i in range(4):
                    fp = q + d2 * L2 * random.uniform(0.3, 1.0)
                    nrm = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
                    u, v, _ = base_de(nrm)
                    s = random.uniform(0.012, 0.022)
                    vv = [bf.verts.new(fp + u * s), bf.verts.new(fp + v * s * 0.5), bf.verts.new(fp - u * s), bf.verts.new(fp - v * s * 0.5)]
                    bf.faces.new(vv)


ARB = [  # (x, y, altura, estado): 0 seco intacto, 1 queimando, 2 apagado pelo jato, 3 pegando
    (3.05, 1.28, 0.55, 2), (3.55, 1.95, 0.7, 1), (3.95, 0.95, 0.6, 1), (3.45, 2.55, 0.55, 1), (4.45, 1.75, 0.85, 1),
    (2.8, 1.95, 0.45, 3), (4.2, 2.6, 0.6, 1), (2.75, 0.75, 0.5, 2), (1.8, 2.7, 0.6, 0), (-1.6, 1.9, 0.6, 0), (-2.2, -1.6, 0.5, 0),
    (5.3, 0.6, 0.7, 0), (1.6, -1.9, 0.45, 0), (5.0, 3.0, 0.6, 1)]
bg_seco, bf_seco, bg_carv, bb = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for (x, y, h, e) in ARB:
    if e == 0:
        arbusto(bg_seco, bf_seco, Vector((x, y)), h)
    elif e == 3:
        arbusto(bg_seco, bf_seco, Vector((x, y)), h)
    else:
        arbusto(bg_carv, None, Vector((x, y)), h * 0.85, False)
        for k in range(12 if e == 1 else 6):                                # brasas nos galhos e no pé
            a, r = random.uniform(0, 2 * PI), random.uniform(0, 0.15)
            pedra(bb, Vector((x + math.cos(a) * r, y + math.sin(a) * r, random.uniform(0.0, h * 0.4))), random.uniform(0.008, 0.02))
obj('arbustos', bg_seco, 'galho')
obj('folhas', bf_seco, 'folha')
obj('arbustos_queimados', bg_carv, 'carvao')
obj('brasas', bb, 'brasa')


def esfera_unit(nome, mat, gota=False, sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    if gota:                                                               # labareda: estreita para cima
        for v in bm.verts:
            if v.co.z > 0:
                f = 1 - 0.75 * v.co.z
                v.co.x *= f
                v.co.y *= f
    return obj(nome, bm, mat)


# chamas: (posição, raio, altura) — nos arbustos queimando, na frente de capim e restos fracos onde o jato cai
CHAMAS = []
for (x, y, h, e) in ARB:
    if e == 1:
        for k in range(5):
            a, r = random.uniform(0, 2 * PI), random.uniform(0, 0.14)
            CHAMAS.append((Vector((x + math.cos(a) * r, y + math.sin(a) * r, h * random.uniform(0.15, 0.45))),
                           random.uniform(0.18, 0.3), h * random.uniform(1.1, 1.8)))
    if e == 3:
        for k in range(2):
            CHAMAS.append((Vector((x + random.uniform(-0.1, 0.1), y + random.uniform(-0.1, 0.1), 0.08)), 0.14, 0.5))
for k in range(26):                                                        # frente de capim pegando fogo
    a = math.radians(95 + k * 270 / 26)
    p = Vector((FC.x + math.cos(a) * R_QUEIMA, FC.y + math.sin(a) * R_QUEIMA, 0.04))
    if (p.xy - L_IMP.xy).length < 0.55:
        continue
    CHAMAS.append((p, random.uniform(0.1, 0.16), random.uniform(0.3, 0.6)))
chamas = []
for k, (p, r, h) in enumerate(CHAMAS):
    o = esfera_unit('chama', 'fogo')
    o.location = p
    o.scale = (r, r, h)
    o.color = (1, 0, 0, 1)
    chamas.append((o, p, r, h, random.uniform(0, 2 * PI)))
# restos de fogo que o jato está apagando (fracos, já com vapor)
for k in range(3):
    p = L_IMP + Vector((random.uniform(-0.15, 0.25), random.uniform(-0.2, 0.2), -0.15))
    o = esfera_unit('chama_morrendo', 'fogo')
    o.location = p
    o.scale = (0.06, 0.06, 0.13)
    o.color = (0.45, 0, 0, 1)
    chamas.append((o, p, 0.06, 0.13, random.uniform(0, 2 * PI)))
luzes_fogo = []
for p in (Vector((3.55, 1.95, 0.6)), Vector((4.0, 0.95, 0.5)), Vector((4.4, 1.8, 0.7)), Vector((3.45, 2.5, 0.5)), Vector((2.85, 2.0, 0.3))):
    ld = bpy.data.lights.new('Fogo', 'POINT')
    ld.color = (1.0, 0.45, 0.12)
    ld.shadow_soft_size = 0.3
    ol = bpy.data.objects.new('Luz fogo', ld)
    sc.collection.objects.link(ol)
    ol.location = p
    luzes_fogo.append(ld)
# fumaça dos arbustos queimando: sai preta e dilui em cinza, levada para leste
FONTES = [Vector((x, y, h * 0.9)) for (x, y, h, e) in ARB if e == 1]
fumacas = []
for k in range(22):
    o = esfera_unit('fumaca', 'fumaca')
    fumacas.append((o, FONTES[k % len(FONTES)], k / 22))
# vapor branco onde a água encontra o fogo
vapores = []
for k in range(14):
    o = esfera_unit('vapor', 'vapor')
    base_v = L_IMP + Vector((random.uniform(-0.3, 0.45), random.uniform(-0.35, 0.4), -0.15))
    vapores.append((o, base_v, k / 14))

# ------------------------------------------------------------------ jato em arco (na pose nominal, preso no canhão)
YAW0 = math.atan2(L_IMP.y, L_IMP.x)
giro.rotation_euler = (0, 0, YAW0)
eleva.rotation_euler = (0, -PITCH0, 0)
bpy.context.view_layer.update()
MW = eleva.matrix_world.copy()
BOCA = MW @ Vector((X_N1 + 0.004, 0, 0))
DIRJ = (MW.to_3x3() @ X).normalized()
dh = (L_IMP.xy - BOCA.xy).length
dz = BOCA.z - L_IMP.z
th = PITCH0
V0 = math.sqrt(4.9 * dh * dh / (math.cos(th) ** 2 * (dz + dh * math.tan(th))))
T_CAI = dh / (V0 * math.cos(th))


def no_jato(t):
    return BOCA + DIRJ * (V0 * t) + Vector((0, 0, -4.9 * t * t))


jato_objs = []
bm = bmesh.new()
uvl = bm.loops.layers.uv.new()
NJ, LJ = 60, 18
T_NUC = 0.62 * T_CAI
an = []
for i in range(NJ + 1):
    t = T_NUC * i / NJ
    c = no_jato(t)
    tg = (no_jato(t + 0.001) - c).normalized()
    u = tg.cross(Z).normalized()
    v = u.cross(tg)
    f = i / NJ
    r = 0.024 + 0.026 * f + (0.014 * (f - 0.8) / 0.2 if f > 0.8 else 0.0) * (-1)
    r = max(r, 0.012)
    an.append([bm.verts.new(c + (u * math.cos(a) + v * math.sin(a)) * r * (1 + 0.14 * f * math.sin(a * 3 + i * 0.9)))
               for a in (j * 2 * PI / LJ for j in range(LJ))])
for i in range(NJ):
    for j in range(LJ):
        fc = bm.faces.new((an[i][j], an[i][(j + 1) % LJ], an[i + 1][(j + 1) % LJ], an[i + 1][j]))
        for lp, (uu, vv) in zip(fc.loops, ((j / LJ, i / NJ), ((j + 1) / LJ, i / NJ), ((j + 1) / LJ, (i + 1) / NJ), (j / LJ, (i + 1) / NJ))):
            lp[uvl].uv = (uu, vv)
bm.faces.new(an[0][::-1])
fim = bm.verts.new(no_jato(T_NUC * 1.03))
for j in range(LJ):
    bm.faces.new((an[-1][j], an[-1][(j + 1) % LJ], fim))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
o = obj('jato_nucleo', bm, 'jato')
for pg in o.data.polygons:
    pg.use_smooth = True
jato_objs.append(o)
# pedaços do jato rompendo (bolhas esticadas), nuvem de gotas e névoa
bm = bmesh.new()
for k in range(70):
    t = T_CAI * random.uniform(0.5, 1.0)
    f = (t / T_CAI - 0.5) / 0.5
    c = no_jato(t)
    tg = (no_jato(t + 0.001) - c).normalized()
    u = tg.cross(Z).normalized()
    v = u.cross(tg)
    esp = 0.03 + 0.18 * f
    c = c + u * random.gauss(0, esp * 0.5) + v * random.gauss(0, esp * 0.4)
    r = random.uniform(0.008, 0.02) * (1.2 - 0.5 * f)
    q = tg.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=Matrix.Translation(c) @ q @ Matrix.Diagonal((r, r, r * random.uniform(2.5, 5), 1)))
o = obj('jato_pedacos', bm, 'jato')
for pg in o.data.polygons:
    pg.use_smooth = True
jato_objs.append(o)
bm = bmesh.new()
for k in range(700):
    t = T_CAI * (0.35 + 0.67 * random.random() ** 0.7)
    f = max(0.0, (t / T_CAI - 0.35) / 0.65)
    c = no_jato(t)
    tg = (no_jato(t + 0.001) - c).normalized()
    u = tg.cross(Z).normalized()
    v = u.cross(tg)
    esp = 0.02 + 0.32 * f * f
    c = c + u * random.gauss(0, esp * 0.6) + v * random.gauss(0, esp * 0.45)
    r = random.uniform(0.0025, 0.007)
    q = tg.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=Matrix.Translation(c) @ q @ Matrix.Diagonal((r, r, r * 2.2, 1)))
o = obj('jato_gotas', bm, 'gota')
for pg in o.data.polygons:
    pg.use_smooth = True
jato_objs.append(o)
nevoas = []
for k in range(9):
    t = T_CAI * (0.45 + 0.6 * k / 8)
    o = esfera_unit('nevoa', 'nevoa')
    c = no_jato(min(t, T_CAI * 0.98))
    o.location = c
    s = 0.08 + 0.3 * (k / 8) ** 1.3
    o.scale = (s * 1.4, s, s)
    o.rotation_euler = (0, 0, YAW0)
    o.color = (0.5 + 0.5 * k / 8, 1, 0, 1)
    nevoas.append((o, c, s))
    jato_objs.append(o)
# gotas que correm ao longo do arco (animadas)
gotas_v = []
for k in range(36):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    o = obj('gota_voando', bm, 'gota')
    gotas_v.append((o, random.random(), Vector((random.gauss(0, 1), random.gauss(0, 1), 0)), random.uniform(0.004, 0.009)))
    jato_objs.append(o)
for o in jato_objs:
    o.parent = eleva
    o.matrix_parent_inverse = MW.inverted()
# respingos no impacto (fixos no chão, animados)
respingos = []
for k in range(24):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    o = obj('respingo', bm, 'gota')
    vel = Vector((random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9), random.uniform(1.0, 2.2)))
    respingos.append((o, vel, random.random(), L_IMP + Vector((random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), -0.1))))
bm = bmesh.new()
for k in range(5):                                                         # poças no chão molhado
    mancha(bm, (L_IMP.x + random.uniform(-0.3, 0.3), L_IMP.y + random.uniform(-0.25, 0.25)), random.uniform(0.04, 0.1), 0.0075)
obj('pocas', bm, 'molhado')

# ------------------------------------------------------------------ animação (laço de 4 s)
def chave(o, q, *canais):
    for c in canais:
        o.keyframe_insert(c, frame=q)


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    yaw = YAW0 + math.radians(4.0) * math.sin(2 * PI * fr)
    pitch = PITCH0 + math.radians(0.8) * math.sin(4 * PI * fr)
    giro.rotation_euler = (0, 0, yaw)
    eleva.rotation_euler = (0, -pitch, 0)
    chave(giro, q, 'rotation_euler')
    chave(eleva, q, 'rotation_euler')
    pin_g.rotation_euler = (0, 0, -(yaw - YAW0) * 0.185 / R_PG)
    pin_e.rotation_euler = (0, (pitch - PITCH0) * RS / R_PE, 0)
    chave(pin_g, q, 'rotation_euler')
    chave(pin_e, q, 'rotation_euler')
    olho.rotation_euler = (0, 0, 2 * PI * 2 * fr + 0.6)
    chave(olho, q, 'rotation_euler')
    acopl.location = VC + Vector((0, 0, 0.21 + 0.004 * math.sin(2 * PI * 3 * fr)))     # IA modulando a pressão
    chave(acopl, q, 'location')
    for o, p, r, h, fase in chamas:
        tre = 1 + 0.22 * math.sin(2 * PI * 7 * fr + fase) * math.sin(2 * PI * 3 * fr + fase * 1.7)
        o.scale = (r * (1 + 0.1 * math.sin(2 * PI * 5 * fr + fase)), r, max(0.08, h * tre))
        o.location = p + Vector((0.02 * math.sin(2 * PI * 4 * fr + fase), 0.015 * math.cos(2 * PI * 3 * fr + fase), 0))
        chave(o, q, 'scale', 'location')
    for k, ld in enumerate(luzes_fogo):
        ld.energy = 140 * (1 + 0.25 * math.sin(2 * PI * 6 * fr + k) * math.sin(2 * PI * 11 * fr + 2 * k))
        ld.keyframe_insert('energy', frame=q)
    for k, (o, src, fase) in enumerate(fumacas):
        u = (fase + fr) % 1.0
        o.location = src + Vector((0.9 * u * u + 0.1 * math.sin(k), 0.25 * u, 2.6 * u + 0.2))
        s = 0.18 + 0.75 * u
        o.scale = (s, s, s * 0.9)
        o.rotation_euler = (k, u * 2, k * 0.5)
        dens = min(1.0, u / 0.08) * (1 - u) ** 0.8
        o.color = (max(0.02, dens), min(1.0, u * 1.5), 0, 1)
        chave(o, q, 'location', 'scale', 'rotation_euler', 'color')
    for k, (o, b0, fase) in enumerate(vapores):
        u = (fase + fr) % 1.0
        o.location = b0 + Vector((0.5 * u * u, 0.12 * u, 1.6 * u + 0.15))
        s = 0.14 + 0.5 * u
        o.scale = (s, s, s * 1.15)
        o.rotation_euler = (k * 0.7, u * 1.5, k)
        o.color = (max(0.02, min(1.0, u / 0.1) * (1 - u) ** 1.2), 1, 0, 1)
        chave(o, q, 'location', 'scale', 'rotation_euler', 'color')
    for o, c, s in nevoas:
        p = 1 + 0.08 * math.sin(2 * PI * 2 * fr + c.x * 3)
        o.scale = (s * 1.4 * p, s * p, s * p)
        chave(o, q, 'scale')
    for o, fase, lat, r in gotas_v:
        u = (fase + fr * 3) % 1.0
        t = T_CAI * (0.45 + 0.55 * u)
        c = no_jato(t)
        tg = (no_jato(t + 0.001) - c).normalized()
        uu = tg.cross(Z).normalized()
        vv = uu.cross(tg)
        esp = 0.03 + 0.25 * u * u
        o.location = c + uu * (lat.x * esp * 0.6) + vv * (lat.y * esp * 0.4)
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = tg.to_track_quat('Z', 'Y')
        o.scale = (r, r, r * 2.5)
        chave(o, q, 'location', 'rotation_quaternion', 'scale')
    for o, vel, fase, p0 in respingos:
        tt = ((fase + fr * 4) % 1.0) * 0.45
        o.location = p0 + vel * tt + Vector((0, 0, -4.9 * tt * tt))
        s = 0.007 * max(0.05, 1 - tt / 0.45)
        o.scale = (s, s, s * 1.6)
        chave(o, q, 'location', 'scale')
for o in list(sc.objects) + list(bpy.data.lights):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: luz, céu, câmera
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.6
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.6, 0.7, 1)
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
sc.cycles.max_bounces = 12
sc.cycles.transmission_bounces = 12
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.5
cam_d = bpy.data.cameras.new('Cam')
cam_d.clip_end = 200
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def foto(nome, quadro, pos, alvo, lente, amostras=128, res=(1300, 1000)):
    sc.cycles.samples = amostras
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.frame_set(quadro)
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


QF = QUADROS // 2 + 1          # fr = 0,5: canhão na pose nominal
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    if so_uma in (None, '0'):
        foto('supressor_0.png', QF, (-2.5, -2.0, 1.6), (0.15, 0.08, 0.72), 33, 128, (1200, 1100))
    if so_uma in (None, 'jato'):
        foto('supressor_jato.png', QF, (1.95, -3.7, 1.45), (1.85, 0.95, 0.72), 24, 128, (1500, 950))
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    foto('supressor_teste.png', int(v[7]), v[0:3], v[3:6], v[6], 32, (1000, 800))
print('SUPRESSOR ok')
