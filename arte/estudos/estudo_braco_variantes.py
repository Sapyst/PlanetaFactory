"""Estudo isolado (fora do jogo): variantes do braço mecânico aprovado (estudo_braco.py), 1×1 tile, mesmas partes
(base, giro, braco1, braco2, garra) e mesmas portas (ITEM_ENT_S, ITEM_SAI_N).

BRAÇO RÁPIDO — alcance 1 tile, 2× mais rápido, gasta mais energia. Mais leve e nervoso: braço 1 em esqueleto de
alumínio vazado (treliça de chapa), braço 2 em tubo de fibra de carbono; servomotores elétricos grandes em cada eixo
(giro, ombro, cotovelo, punho) com aletas, ventoinha girando e brilho fraco de calor entre as aletas; armário de
inversores no chão com dissipador; cabos de força laranja grossos com presilhas; garra de eletroímã (bobina que acende
quando segura). Faixa laranja-avermelhada gasta para distinguir do normal.

BRAÇO LONGO — alcance 2 tiles (pula um tile); recolhido cabe no tile. Base reforçada (chapa grossa com chumbadores,
pedestal com mãos-francesas, coroa dentada + pinhão do motor de giro), contrapeso de placas na traseira do giro, lança
com joelho erguida por dois pistões longos, cotovelo com atuador rotativo hidráulico, braço 2 telescópico de três
estágios com cilindro de extensão e cabo espiralado que estica, mangueiras com muitas abraçadeiras, central
hidráulica (tanque, bomba, visor de óleo) no chão, garra de dois dedos.

Cada braço pega um item no tile ao sul e solta no tile ao norte (o longo, 2 tiles adiante); o rápido faz dois ciclos
no laço de 4 s. O braço normal aprovado entra na foto de comparação importado do glb do estudo.
Uso: blender -b --python estudo_braco_variantes.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


# ------------------------------------------------------------------ materiais
def emissor(nome, cor, forca, base=(0.05, 0.03, 0.02)):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def fibra_mat():
    """Fibra de carbono: trama em xadrez fino, verniz brilhante por cima, sujeira de leve."""
    m = bpy.data.materials.new('Fibra de carbono')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = no(nt, 'ShaderNodeTexCoord')
    xd = no(nt, 'ShaderNodeTexChecker', **{'Scale': 140.0})
    xd.inputs['Color1'].default_value = (0.018, 0.018, 0.02, 1)
    xd.inputs['Color2'].default_value = (0.05, 0.05, 0.055, 1)
    nt.links.new(tc.outputs['Object'], xd.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 12.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mx = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mx.inputs[7].default_value = (0.09, 0.075, 0.06, 1)          # poeira
    fr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.75, 'To Min': 0.0, 'To Max': 0.6})
    nt.links.new(ru.outputs['Fac'], fr.inputs['Value'])
    nt.links.new(fr.outputs['Result'], mx.inputs[0])
    nt.links.new(xd.outputs['Color'], mx.inputs[6])
    nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.35
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = 0.6
        b.inputs['Coat Roughness'].default_value = 0.12
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.15})
    nt.links.new(xd.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def oleo_escorrido_mat():
    m = mats.material('Óleo', (0.02, 0.016, 0.011), 0, 0.22, pintura=False, sujeira=0.0, desgaste=0.0)
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, ferrugem=0.5, desgaste=0.95, sujeira=0.9),
    'laranja': mats.material('Laranja gasto', (0.58, 0.13, 0.03), 0, 0.5, ferrugem=0.5, desgaste=1.0, sujeira=0.9),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, ferrugem=0.4, desgaste=0.75, sujeira=0.8),
    'primer': mats.material('Primer trocado', (0.20, 0.26, 0.30), 0, 0.6, ferrugem=0.3, desgaste=0.8, sujeira=0.9),
    'zarcao': mats.material('Zarcão trocado', (0.33, 0.07, 0.035), 0, 0.65, ferrugem=0.6, desgaste=0.8, sujeira=0.9),
    'remendo': mats.material('Chapa de remendo', (0.26, 0.2, 0.16), 1.0, 0.6, pintura=False, ferrugem=1.0, sujeira=1.0),
    'fio_vermelho': mats.material('Fio vermelho', (0.5, 0.03, 0.02), 0, 0.5, pintura=False, sujeira=0.5, desgaste=0.0),
    'fio_azul': mats.material('Fio azul', (0.03, 0.08, 0.4), 0, 0.5, pintura=False, sujeira=0.5, desgaste=0.0),
    'fio_amarelo': mats.material('Fio amarelo', (0.55, 0.45, 0.03), 0, 0.5, pintura=False, sujeira=0.5, desgaste=0.0),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'aluminio': mats.material('Alumínio', (0.66, 0.67, 0.68), 1.0, 0.32, pintura=False, sujeira=0.7, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'ferro': mats.material('Ferro fundido', (0.11, 0.10, 0.095), 0.8, 0.6, pintura=False, ferrugem=0.95, sujeira=0.9),
    'placa': mats.material('Placa de ferro', (0.30, 0.29, 0.28), 1.0, 0.45, pintura=False, ferrugem=0.9, sujeira=0.6),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
    'cabo_laranja': mats.material('Cabo de força', (0.62, 0.17, 0.02), 0, 0.55, pintura=False, sujeira=0.9, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': oleo_escorrido_mat(),
    'fibra': fibra_mat(),
    'calor': emissor('Calor', (1.0, 0.2, 0.03), 0.5, base=(0.03, 0.02, 0.018)),
    'led': emissor('LED âmbar', (1.0, 0.5, 0.06), 9.0, base=(1.0, 0.5, 0.1)),
    'led_violeta': emissor('LED violeta', (0.55, 0.15, 1.0), 9.0, base=(0.5, 0.2, 0.9)),
    'bobina': emissor('Bobina', (1.0, 0.45, 0.08), 0.0, base=(0.80, 0.42, 0.24)),
    'visor': emissor('Visor de óleo', (0.6, 0.3, 0.02), 0.4, base=(0.25, 0.12, 0.01)),
    'listras': base3d.listras_mat(),
})
base3d.M['bobina'].node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 1.0
M = base3d.M


def envelhecer(m, poeira=0.8, lama=0.8, escorrido=0.7, fuligem=0.5):
    """Camada de uso por cima do material: poeira nas faces de cima, lama perto do chão, escorridos verticais de
    ferrugem/óleo e manchas de fuligem."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    no = mats.no
    entra_cor = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
    entra_r = b.inputs['Roughness'].links[0].from_socket if b.inputs['Roughness'].is_linked else None
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    def ruido(escala, vet=None, det=6.0):
        r = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': det})
        nt.links.new(vet if vet is not None else geo.outputs['Position'], r.inputs['Vector'])
        return r.outputs['Fac']
    def faixa(sock, a, b_, ate=1.0):
        mr = no(nt, 'ShaderNodeMapRange', **{'From Min': a, 'From Max': b_, 'To Min': 0.0, 'To Max': ate})
        nt.links.new(sock, mr.inputs['Value'])
        return mr.outputs['Result']
    def mult(x, y):
        mm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(x, mm.inputs[0])
        if isinstance(y, float):
            mm.inputs[1].default_value = y
        else:
            nt.links.new(y, mm.inputs[1])
        return mm.outputs['Value']
    def mistura(cor_base, fac, cor):
        mx = no(nt, 'ShaderNodeMix', data_type='RGBA')
        nt.links.new(fac, mx.inputs[0])
        if cor_base is None:
            mx.inputs[6].default_value = b.inputs['Base Color'].default_value
        else:
            nt.links.new(cor_base, mx.inputs[6])
        mx.inputs[7].default_value = (*cor, 1)
        return mx.outputs[2]
    # escorridos: ruído esticado na vertical
    esc = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY')
    esc.inputs[1].default_value = (38.0, 38.0, 2.5)
    nt.links.new(geo.outputs['Position'], esc.inputs[0])
    f_esc = mult(faixa(ruido(1.0, esc.outputs[0], 3.0), 0.58, 0.72, escorrido), faixa(sn.outputs['Z'], 0.6, 0.2))
    cor = mistura(entra_cor, f_esc, (0.10, 0.045, 0.02))
    f_ful = faixa(ruido(5.0), 0.6, 0.75, fuligem)
    cor = mistura(cor, f_ful, (0.015, 0.014, 0.013))
    f_poe = mult(faixa(sn.outputs['Z'], 0.55, 0.95, poeira), faixa(ruido(9.0), 0.4, 0.66))
    cor = mistura(cor, f_poe, (0.30, 0.27, 0.23))
    f_lama = mult(faixa(sp.outputs['Z'], 0.16, 0.02, lama), faixa(ruido(9.0), 0.3, 0.6))
    cor = mistura(cor, f_lama, (0.13, 0.09, 0.055))
    nt.links.new(cor, b.inputs['Base Color'])
    rmax = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    if entra_r is not None:
        nt.links.new(entra_r, rmax.inputs[0])
    else:
        rmax.inputs[0].default_value = b.inputs['Roughness'].default_value
    soma = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(f_poe, soma.inputs[0])
    nt.links.new(f_lama, soma.inputs[1])
    nt.links.new(mult(soma.outputs['Value'], 0.95), rmax.inputs[1])
    nt.links.new(rmax.outputs['Value'], b.inputs['Roughness'])
    if b.inputs['Metallic'].is_linked:                         # poeira e lama tiram o brilho de metal da lasca
        ml = b.inputs['Metallic'].links[0].from_socket
        inv = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
        inv.inputs[0].default_value = 1.0
        nt.links.new(soma.outputs['Value'], inv.inputs[1])
        nt.links.new(mult(ml, inv.outputs['Value']), b.inputs['Metallic'])


for nome, kw in (('amarelo', {}), ('laranja', {}), ('grafite', {}), ('primer', {}), ('zarcao', {}), ('remendo', {}),
                 ('aco', {}), ('aluminio', dict(escorrido=0.5)), ('cromo', dict(poeira=0.5, escorrido=0.3, fuligem=0.2)),
                 ('cobre', {}), ('ferro', {}), ('concreto', dict(escorrido=0.3, poeira=0.6)), ('borracha', dict(escorrido=0.2, poeira=0.35)),
                 ('cabo_laranja', dict(escorrido=0.3)), ('fibra', dict(escorrido=0.3, fuligem=0.3)), ('placa', dict(lama=0.3)),
                 ('listras', dict(escorrido=0.5))):
    envelhecer(M[nome], **{**dict(poeira=0.8, lama=0.8, escorrido=0.7, fuligem=0.5), **kw})


def estencil_mat():
    m = bpy.data.materials.new('Estêncil apagado')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.62, 0.6, 0.52, 1)
    b.inputs['Roughness'].default_value = 0.8
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mx = no(nt, 'ShaderNodeMixShader')
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 55.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    corte = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.56})
    nt.links.new(ru.outputs['Fac'], corte.inputs['Value'])
    nt.links.new(corte.outputs['Result'], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


M['estencil'] = estencil_mat()


# ------------------------------------------------------------------ geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


COL = sc.collection


def novo_obj(nome, bm, mat, pai=None, suave=False, chanfro=True):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    COL.objects.link(o)
    o.data.materials.append(M[mat])
    if pai is not None:
        o.parent = pai
    if suave:
        suavizar(o)
    if chanfro:
        bv = o.modifiers.new('chanfro', 'BEVEL')
        bv.width = 0.0025
        bv.segments = 2
        bv.limit_method = 'ANGLE'
        bv.angle_limit = math.radians(40)
    return o


class Parte:
    """Peça articulada: um Empty no pivô; a geometria é escrita em coordenadas do braço em repouso e deslocada."""
    def __init__(s, nome, pai, pivo):
        s.nome = nome
        s.e = bpy.data.objects.new(nome, None)
        COL.objects.link(s.e)
        s.pivo = Vector(pivo)
        s.pai = pai
        if pai is not None:
            s.e.parent = pai.e
            s.e.location = s.pivo - pai.pivo
        s.bms = {}
        s.objs = []

    def b(s, mat, suave=False):
        k = (mat, suave)
        if k not in s.bms:
            s.bms[k] = bmesh.new()
        return s.bms[k]

    def fechar(s):
        for (mat, suave), bm in s.bms.items():
            bmesh.ops.translate(bm, vec=-s.pivo, verts=bm.verts[:])
            s.objs.append(novo_obj('%s_%s' % (s.nome, mat), bm, mat, s.e, suave))
        s.bms = {}


def cilx(bm, c, r, h, lados=16):
    cil(bm, Vector(c), r, h, X, lados)


def cily(bm, c, r, h, lados=16):
    cil(bm, Vector(c), r, h, Y, lados)


def cilz(bm, c, r, h, lados=16):
    cil(bm, Vector(c), r, h, Z, lados)


def anel(bm, centro, R, r, eixo=Z, nR=32, nr=8):
    """Anel tubular (toro) em volta do eixo dado."""
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + q @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def cunha(bm, p0, p1, p2, esp, normal):
    """Chapa triangular (mão-francesa) de espessura esp."""
    n = Vector(normal).normalized() * esp / 2
    vs = [bm.verts.new(Vector(p) + s * n) for s in (-1, 1) for p in (p0, p1, p2)]
    bm.faces.new((vs[0], vs[1], vs[2]))
    bm.faces.new((vs[5], vs[4], vs[3]))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((vs[i], vs[i + 3], vs[j + 3], vs[j]))


def mangueira(bm, pts, r, lados=10):
    for a, b in zip(pts, pts[1:]):
        u = (b - a).normalized()
        cil(bm, (a + b) / 2, r, (b - a).length + r * 1.2, u, lados)
    for p in pts[1:-1]:                                         # cotovelo redondo (esfera) em cada emenda
        bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=6, radius=r * 0.995,
                                  matrix=Matrix.Translation(p))


def abracadeiras(bm, pts, r, passo=2, larg=0.012):
    for i in range(passo, len(pts) - 1, passo):
        u = (pts[i + 1] - pts[i - 1]).normalized()
        cil(bm, pts[i], r * 1.35, larg, u, 12)


def parafusos(bm, centro, R, n, r=0.012, h=0.012, z0=0.0, a0=0.0):
    for k in range(n):
        a = a0 + k * 2 * PI / n
        cil(bm, Vector(centro) + Vector((math.cos(a) * R, math.sin(a) * R, z0 + h / 2)), r, h, Z, 6)


def aletas(bm, c, eixo, r, n, passo, esp=0.007):
    """Aletas de dissipação: discos finos ao longo do eixo a partir de c."""
    for k in range(n):
        cil(bm, Vector(c) + Vector(eixo) * passo * k, r, esp, eixo, 20)


def dentes(bm, centro, R, n, alt, larg, h, z):
    for k in range(n):
        a = k * 2 * PI / n
        caixa(bm, Vector(centro) + Vector((math.cos(a) * R, math.sin(a) * R, z)), (alt, larg, h), Matrix.Rotation(a, 3, 'Z'))


def laje(raiz, oleo_pts=()):
    """Laje de concreto do tile, listras de perigo nas bordas e manchas de óleo."""
    bm = raiz.b('concreto')
    caixa_de(bm, (-0.49, -0.49, 0), (0.49, 0.49, 0.05))
    bm = raiz.b('listras')
    for s in (-1, 1):
        caixa_de(bm, (-0.49, s * 0.49 - 0.03, 0.05), (0.49, s * 0.49 + 0.03, 0.0515))
        caixa_de(bm, (s * 0.49 - 0.03, -0.46, 0.05), (s * 0.49 + 0.03, 0.46, 0.0515))
    bm = raiz.b('oleo')
    for (x, y, r) in oleo_pts:
        mancha(bm, (x, y), r, 0.0522)


def esteira(raiz, cy, nome_sensor=True):
    """Trecho curto de esteira N-S (só contexto): longarinas, rolos, lona, pés e motor; topo da lona em z = 0.22."""
    bm = raiz.b('grafite')
    for s in (-1, 1):
        caixa_de(bm, (s * 0.2 - 0.015, cy - 0.46, 0.135), (s * 0.2 + 0.015, cy + 0.46, 0.235))
    bm = raiz.b('aco')
    for s in (-1, 1):
        for t in (-0.36, 0.36):
            caixa_de(bm, (s * 0.2 - 0.015, cy + t - 0.015, 0.0), (s * 0.2 + 0.015, cy + t + 0.015, 0.135))
        viga(bm, Vector((s * 0.2, cy - 0.36, 0.02)), Vector((s * 0.2, cy + 0.36, 0.12)), 0.012)
    for t in (-0.36, 0.36):
        caixa_de(bm, (-0.19, cy + t - 0.01, 0.05), (0.19, cy + t + 0.01, 0.07))
    bm = raiz.b('cromo', True)
    for t in (-0.43, -0.2, 0.0, 0.2, 0.43):
        cilx(bm, (0, cy + t, 0.19), 0.025, 0.37)
    bm = raiz.b('borracha')
    caixa_de(bm, (-0.175, cy - 0.44, 0.208), (0.175, cy + 0.44, 0.22))
    caixa_de(bm, (-0.175, cy - 0.44, 0.158), (0.175, cy + 0.44, 0.166))
    bm = raiz.b('grafite', True)
    cilx(bm, (0.26, cy - 0.43, 0.19), 0.045, 0.09, 20)               # motor da esteira
    bm = raiz.b('amarelo', True)
    cilx(bm, (0.315, cy - 0.43, 0.19), 0.03, 0.02, 16)


def item_obj(nome, raiz):
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (0.10, 0.10, 0.05))
    o = novo_obj(nome, bm, 'placa', raiz.e)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.0258), (0.07, 0.07, 0.002))
    novo_obj(nome + '_marca', bm, 'ferro', o, chanfro=False)
    return o


def amassado(bm, c, u, v, w, h, prof, covas, n=14):
    """Chapa fina rente à face (normal = u×v), com amassados (covas: [(su, sv, raio)] em fração de w/h)."""
    c, u, v = Vector(c), Vector(u).normalized(), Vector(v).normalized()
    nn = u.cross(v)
    grade = []
    for i in range(n + 1):
        lin = []
        for j in range(n + 1):
            a, bb = i / n - 0.5, j / n - 0.5
            d = 0.0
            for (su, sv, rr) in covas:
                d += prof * math.exp(-((a - su) ** 2 + (bb - sv) ** 2) / (rr * rr))
            lin.append(bm.verts.new(c + u * a * w + v * bb * h - nn * d))
        grade.append(lin)
    for i in range(n):
        for j in range(n):
            bm.faces.new((grade[i][j], grade[i + 1][j], grade[i + 1][j + 1], grade[i][j + 1]))
    for i in range(n):                                         # borda dobrada (espessura)
        for (p0, p1) in ((grade[i][0], grade[i + 1][0]), (grade[n][i], grade[n][i + 1]),
                         (grade[i + 1][n], grade[i][n]), (grade[0][i + 1], grade[0][i])):
            q0 = bm.verts.new(p0.co - nn * 0.003)
            q1 = bm.verts.new(p1.co - nn * 0.003)
            bm.faces.new((p1, p0, q0, q1))


def remendo(parte, c, u, v, w, h, eixo_n, mat='remendo'):
    """Chapa de remendo aparafusada (4–6 parafusos) com cordão de solda velho numa borda."""
    c, u, v = Vector(c), Vector(u).normalized(), Vector(v).normalized()
    nn = u.cross(v)
    bm = parte.b(mat)
    rot = Matrix((u, v, nn)).transposed()
    caixa(bm, c + nn * 0.002, (w, h, 0.004), rot)
    for (a, b_) in ((-0.4, -0.38), (0.4, -0.38), (-0.4, 0.38), (0.4, 0.38), (0.0, -0.38), (0.0, 0.38)):
        cil(parte.b('aco'), c + u * a * w + v * b_ * h + nn * 0.005, 0.0055, 0.004, nn, 6)
    for k in range(7):                                         # solda: contas ao longo da borda de baixo
        bmesh.ops.create_uvsphere(parte.b('ferro'), u_segments=6, v_segments=4, radius=0.0035,
                                  matrix=Matrix.Translation(c + u * (k / 6 - 0.5) * w * 0.9 - v * h * 0.5 + nn * 0.001))


def fiacao(parte, p0, saida, p1, cores=('fio_vermelho', 'fio_azul', 'fio_amarelo')):
    """Fios expostos saindo de um prensa-cabo quebrado: soltos em laço, um com o cobre aparecendo."""
    p0, saida, p1 = Vector(p0), Vector(saida), Vector(p1)
    for k, mat in enumerate(cores):
        off = Vector(((k - 1) * 0.006, (k - 1) * 0.004, (k - 1) * 0.005))
        pts = bezier(p0 + off * 0.5, p0 + saida + off * 2, p1 + saida * 0.5 + off * 3, p1 + off, 10)
        mangueira(parte.b(mat, True), pts if k != 1 else pts[:7], 0.003, 6)
        if k == 1:
            mangueira(parte.b('cobre', True), [pts[6], pts[6] + (pts[7] - pts[6]) * 0.8], 0.0018, 6)
    cil(parte.b('borracha', True), p0, 0.012, 0.016, saida.normalized(), 10)          # fita isolante remendando


def estencil(texto, parte, pos, normal, up, tam):
    cu = bpy.data.curves.new('serie', 'FONT')
    cu.body = texto
    cu.size = tam
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    o = bpy.data.objects.new('serie_' + texto[:6], cu)
    COL.objects.link(o)
    o.data.materials.append(M['estencil'])
    n, up = Vector(normal).normalized(), Vector(up).normalized()
    right = up.cross(n)
    o.parent = parte.e
    o.matrix_basis = Matrix.Translation(Vector(pos) + n * 0.0008 - parte.pivo) @ Matrix((right, up, n)).transposed().to_4x4()
    return o


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def trajetoria(u, tabela):
    """tabela: [(u, r, z, yaw)]; interpolação suave entre pontos."""
    for (u0, *a), (u1, *b) in zip(tabela, tabela[1:]):
        if u0 <= u <= u1:
            t = suave((u - u0) / (u1 - u0))
            return [x + (y - x) * t for x, y in zip(a, b)]
    return tabela[-1][1:]


def chave(o, prop, q):
    o.keyframe_insert(prop, frame=q)


Z0 = 0.05            # topo da laje
TOPO_ESTEIRA = 0.22
H_ITEM = 0.05


# =================================================================== BRAÇO RÁPIDO
def braco_rapido(O):
    global COL
    COL = bpy.data.collections.new('rapido')
    sc.collection.children.link(COL)
    raiz = Parte('rapido_raiz', None, (0, 0, 0))
    raiz.e.location = O
    laje(raiz, ((0.32, -0.12, 0.05), (-0.25, 0.3, 0.04)))
    est = Parte('rapido_esteiras', raiz, (0, 0, 0))
    esteira(est, -1.0)
    esteira(est, 1.0)
    est.fechar()
    Zg = Z0 + 0.225
    S = Vector((0, 0, Z0 + 0.40))
    L1, L2 = 0.55, 0.62
    E = S + Vector((0, 0, L1))
    W = E + Vector((0, L2, 0))
    # ---------------------------------------------------------- base: plinto, coluna com faixa, coroa dentada
    base = Parte('rapido_base', raiz, (0, 0, 0))
    bm = base.b('grafite')
    cil(bm, (0, 0, Z0 + 0.03), 0.31, 0.06, Z, 8)
    bm = base.b('aco')
    cil(bm, (0, 0, Z0 + 0.075), 0.26, 0.03, Z, 8)
    parafusos(base.b('cromo'), (0, 0, 0), 0.225, 8, 0.016, 0.014, Z0 + 0.09, PI / 8)
    cilz(base.b('aco', True), (0, 0, Z0 + 0.155), 0.13, 0.13, 32)
    cilz(base.b('laranja', True), (0, 0, Z0 + 0.135), 0.1335, 0.035, 32)
    cilz(base.b('grafite', True), (0, 0, Zg - 0.01), 0.145, 0.02, 32)
    dentes(base.b('aco'), (0, 0, 0), 0.148, 40, 0.012, 0.008, 0.018, Zg - 0.01)
    # armário de inversores no chão, com dissipador, faixa e LED; cabo grosso até a coluna; eletroduto até a borda
    bm = base.b('grafite')
    caixa_de(bm, (0.30, -0.44, Z0), (0.45, -0.25, Z0 + 0.22))
    bm = base.b('laranja')
    caixa_de(bm, (0.298, -0.442, Z0 + 0.17), (0.452, -0.248, Z0 + 0.195))
    bm = base.b('aluminio')
    for k in range(7):
        y = -0.425 + k * 0.026
        caixa_de(bm, (0.45, y - 0.004, Z0 + 0.03), (0.49, y + 0.004, Z0 + 0.16))   # aletas do dissipador
    caixa_de(base.b('calor'), (0.45, -0.43, Z0 + 0.04), (0.462, -0.268, Z0 + 0.15))
    cil(base.b('led'), Vector((0.298, -0.40, Z0 + 0.13)), 0.007, 0.006, X, 10)
    cil(base.b('led_violeta'), Vector((0.298, -0.37, Z0 + 0.13)), 0.007, 0.006, X, 10)
    bm = base.b('aco')
    caixa_de(bm, (0.298, -0.43, Z0 + 0.04), (0.302, -0.27, Z0 + 0.11))           # tampa de inspeção
    pts = bezier((0.30, -0.33, Z0 + 0.10), (0.20, -0.30, Z0 + 0.12), (0.12, -0.17, Z0 + 0.15), (0.095, -0.095, Z0 + 0.16), 10)
    pts2 = bezier((0.30, -0.36, Z0 + 0.07), (0.18, -0.36, Z0 + 0.12), (0.06, -0.20, Z0 + 0.16), (0.04, -0.125, Z0 + 0.15), 10)
    mangueira(base.b('cabo_laranja', True), pts, 0.016)
    mangueira(base.b('cabo_laranja', True), pts2, 0.016)
    abracadeiras(base.b('aco', True), pts, 0.016, 3)
    abracadeiras(base.b('aco', True), pts2, 0.016, 3)
    for p, u in ((pts[0], X), (pts[-1], (pts[-1] - pts[-2]).normalized()), (pts2[0], X), (pts2[-1], (pts2[-1] - pts2[-2]).normalized())):
        cil(base.b('grafite', True), p, 0.024, 0.03, u, 12)                        # prensa-cabos
    pe = bezier((0.40, -0.44, Z0 + 0.01), (0.40, -0.47, Z0 + 0.01), (0.40, -0.49, Z0 - 0.0), (0.40, -0.52, -0.02), 4)
    mangueira(base.b('grafite', True), pe, 0.02)                                  # eletroduto para o chão
    # ---------------------------------------------------------- giro: corpo, faixa, servo do giro, servo do ombro
    giro = Parte('rapido_giro', base, (0, 0, Zg))
    bm = giro.b('amarelo')
    caixa_de(bm, (-0.11, -0.13, Zg), (0.11, 0.13, Zg + 0.11))
    caixa_de(giro.b('laranja'), (-0.1115, -0.1315, Zg + 0.02), (0.1115, 0.1315, Zg + 0.045))
    bm = giro.b('grafite')
    caixa_de(bm, (-0.08, -0.12, Zg + 0.11), (0.08, 0.04, Zg + 0.135))              # tampa
    for x in (-0.085, 0.085):                                                    # mancais do ombro
        caixa_de(giro.b('aco'), (x - 0.0175, -0.055, Zg + 0.11), (x + 0.0175, 0.055, Zg + 0.21))
        caixa_de(giro.b('grafite'), (x - 0.02, -0.06, Zg + 0.105), (x + 0.02, 0.06, Zg + 0.12))
    # servo do ombro (+X): redutor, carcaça, aletas, calor entre aletas, ventoinha
    cilx(giro.b('aco', True), (0.106, 0, S.z), 0.05, 0.008, 24)                     # redutor (encosta no mancal)
    cilx(giro.b('grafite', True), (0.11 + 0.06, 0, S.z), 0.072, 0.12, 32)
    cilx(giro.b('calor', True), (0.17, 0, S.z), 0.0735, 0.09, 32)
    aletas(giro.b('grafite', True), (0.128, 0, S.z), X, 0.09, 8, 0.012)
    cilx(giro.b('laranja', True), (0.222, 0, S.z), 0.075, 0.016, 32)
    caixa_de(giro.b('aco'), (0.11, -0.045, Zg + 0.02), (0.21, 0.045, Zg + 0.075))   # mão do servo no corpo
    anel(giro.b('grafite', True), (0.25, 0, S.z), 0.064, 0.007, X, 40, 8)            # bocal da ventoinha
    cilx(giro.b('grafite', True), (0.24, 0, S.z), 0.071, 0.016, 32)
    bm = giro.b('aco')
    for k in range(4):
        caixa(bm, (0.256, 0, S.z), (0.004, 0.13, 0.004), Matrix.Rotation(k * PI / 4, 3, 'X'))  # grade
    # servo do giro (lado -X): carcaça vertical com aletas e ventoinha em cima; pinhão embaixo na coroa
    cx = Vector((-0.18, 0.0, 0))
    caixa_de(giro.b('aco'), (-0.18, -0.04, Zg + 0.0), (-0.11, 0.04, Zg + 0.03))       # suporte
    cilz(giro.b('grafite', True), cx + Vector((0, 0, Zg + 0.09)), 0.055, 0.14, 32)
    cilz(giro.b('calor', True), cx + Vector((0, 0, Zg + 0.09)), 0.0565, 0.11, 32)
    aletas(giro.b('grafite', True), cx + Vector((0, 0, Zg + 0.04)), Z, 0.07, 8, 0.0135)
    cilz(giro.b('laranja', True), cx + Vector((0, 0, Zg + 0.155)), 0.058, 0.014, 32)
    anel(giro.b('grafite', True), cx + Vector((0, 0, Zg + 0.18)), 0.048, 0.006, Z, 40, 8)
    bm = giro.b('aco')
    for k in range(4):
        caixa(bm, cx + Vector((0, 0, Zg + 0.186)), (0.1, 0.004, 0.004), Matrix.Rotation(k * PI / 4, 3, 'Z'))
    cilz(giro.b('aco', True), cx + Vector((0, 0, Zg + 0.004)), 0.016, 0.03, 16)     # eixo do pinhão
    pinhao = Parte('rapido_pinhao', giro, cx + Vector((0, 0, Zg - 0.01)))
    cilz(pinhao.b('aco', True), pinhao.pivo, 0.022, 0.018, 16)
    dentes(pinhao.b('aco'), pinhao.pivo, 0.025, 10, 0.012, 0.008, 0.018, 0)
    # caixa de drivers na traseira do giro, com aletas e LED; cabos grossos para os servos
    caixa_de(giro.b('grafite'), (-0.09, -0.20, Zg + 0.0), (0.09, -0.13, Zg + 0.10))
    bm = giro.b('aluminio')
    for k in range(9):
        x = -0.08 + k * 0.02
        caixa_de(bm, (x - 0.003, -0.235, Zg + 0.01), (x + 0.003, -0.20, Zg + 0.09))
    caixa_de(giro.b('calor'), (-0.085, -0.212, Zg + 0.015), (0.085, -0.2, Zg + 0.085))
    cil(giro.b('led'), Vector((0.06, -0.14, Zg + 0.103)), 0.007, 0.006, Z, 10)
    pts = bezier((0.07, -0.16, Zg + 0.10), (0.12, -0.17, Zg + 0.16), (0.222, -0.13, Zg + 0.10), (0.222, -0.045, S.z - 0.06), 8)
    mangueira(giro.b('cabo_laranja', True), pts, 0.013)
    abracadeiras(giro.b('aco', True), pts, 0.013, 3)
    pts = bezier((-0.07, -0.16, Zg + 0.08), (-0.12, -0.16, Zg + 0.06), (-0.16, -0.10, Zg + 0.035), (-0.16, -0.05, Zg + 0.03), 6)
    mangueira(giro.b('cabo_laranja', True), pts, 0.012)
    # ---------------------------------------------------------- braço 1: esqueleto de alumínio vazado
    b1 = Parte('rapido_braco1', giro, S)
    cilx(b1.b('grafite', True), S, 0.05, 0.134, 24)
    bm = b1.b('aluminio')
    for x in (-0.045, 0.045):
        for y in (-0.03, 0.03):
            caixa_de(bm, (x - 0.006, y - 0.008, S.z), (x + 0.006, y + 0.008, E.z))     # longarinas
        n = 5
        for k in range(n):                                                     # diagonais (vazado em zigue-zague)
            z0 = S.z + 0.05 + k * (L1 - 0.1) / n
            z1 = z0 + (L1 - 0.1) / n
            ya, yb = (-0.025, 0.025) if k % 2 == 0 else (0.025, -0.025)
            viga(bm, Vector((x, ya, z0)), Vector((x, yb, z1)), 0.011)
        caixa_de(b1.b('laranja'), (x - 0.007, -0.04, S.z - 0.04), (x + 0.007, 0.04, S.z + 0.06))     # chapas das pontas
        caixa_de(b1.b('laranja'), (x - 0.007, -0.04, E.z - 0.06), (x + 0.007, 0.04, E.z + 0.04))
    bm = b1.b('aco', True)
    for f in (0.36, 0.64):
        cilx(bm, (0, 0, S.z + L1 * f), 0.01, 0.1, 12)                              # espaçadores
    cilx(b1.b('cromo', True), E, 0.016, 0.125, 12)                                 # eixo do cotovelo
    for s in (-1, 1):
        cilx(b1.b('aco', True), (s * 0.058, 0, E.z), 0.02, 0.012, 6)
    # servo do cotovelo (+X)
    cilx(b1.b('grafite', True), (0.115, 0, E.z), 0.06, 0.10, 32)
    cilx(b1.b('calor', True), (0.115, 0, E.z), 0.0612, 0.075, 32)
    aletas(b1.b('grafite', True), (0.08, 0, E.z), X, 0.075, 7, 0.011)
    cilx(b1.b('laranja', True), (0.157, 0, E.z), 0.062, 0.014, 32)
    anel(b1.b('grafite', True), (0.178, 0, E.z), 0.052, 0.006, X, 40, 8)
    bm = b1.b('aco')
    for k in range(4):
        caixa(bm, (0.184, 0, E.z), (0.004, 0.105, 0.004), Matrix.Rotation(k * PI / 4, 3, 'X'))
    # caixa de passagem no ombro e cabo grosso até o servo do cotovelo, com presilhas
    caixa_de(b1.b('grafite'), (0.051, -0.055, S.z + 0.06), (0.075, -0.015, S.z + 0.12))
    pts = bezier((0.064, -0.035, S.z + 0.12), (0.066, -0.045, S.z + 0.30), (0.12, -0.05, E.z - 0.16), (0.16, -0.03, E.z - 0.056), 12)
    mangueira(b1.b('cabo_laranja', True), pts, 0.011)
    pts2 = [p + Vector((-0.0, 0.022, 0.0)) for p in pts]
    mangueira(b1.b('borracha', True), pts2[:-4], 0.006)
    for k in range(1, 4):
        z = S.z + 0.12 + k * 0.1
        caixa_de(b1.b('aco'), (0.051, -0.05, z - 0.008), (0.08, 0.0, z + 0.008))       # presilhas
    # ---------------------------------------------------------- braço 2: tubo de fibra de carbono
    b2 = Parte('rapido_braco2', b1, E)
    cilx(b2.b('aluminio', True), E, 0.056, 0.066, 32)                               # luva do cotovelo
    caixa_de(b2.b('aluminio'), (-0.03, E.y + 0.03, E.z - 0.035), (0.03, E.y + 0.08, E.z + 0.035))
    cily(b2.b('fibra', True), E + Vector((0, 0.08 + (L2 - 0.13) / 2, 0)), 0.032, L2 - 0.13, 32)
    for f in (0.075, L2 - 0.075):
        cily(b2.b('aluminio', True), E + Vector((0, f, 0)), 0.037, 0.04, 32)
    for f in (0.24, 0.40):
        cily(b2.b('laranja', True), E + Vector((0, f, 0)), 0.0335, 0.03, 32)
    bm = b2.b('aluminio')
    for s in (-1, 1):                                                          # garfo do punho
        caixa_de(bm, (s * 0.044 - 0.006, W.y - 0.06, W.z - 0.03), (s * 0.044 + 0.006, W.y + 0.02, W.z + 0.03))
    pts = [E + Vector((0.0, f, 0.052)) for f in (0.07, 0.15, 0.25, 0.35, 0.45, 0.53)]
    pts[0] = E + Vector((0.0, 0.07, 0.04))
    pts.append(W + Vector((0.035, -0.055, 0.03)))
    mangueira(b2.b('cabo_laranja', True), pts, 0.01)
    bm = b2.b('aco', True)
    for f in (0.15, 0.35):
        anel(bm, E + Vector((0, f, 0)), 0.0345, 0.0025, Y, 32, 6)
        cily(bm, E + Vector((0, f, 0.046)), 0.012, 0.014, 10)
    # ---------------------------------------------------------- garra: servo do punho + eletroímã
    g = Parte('rapido_garra', b2, W)
    cilx(g.b('grafite', True), W, 0.036, 0.075, 24)
    aletas(g.b('grafite', True), W + Vector((-0.03, 0, 0)), X, 0.042, 5, 0.015, 0.005)
    cilx(g.b('calor', True), W, 0.037, 0.05, 24)
    cilz(g.b('cromo', True), W + Vector((0, 0, -0.045)), 0.02, 0.03, 16)
    cilz(g.b('grafite', True), W + Vector((0, 0, -0.0825)), 0.07, 0.045, 32)
    bm = g.b('aluminio')
    for k in range(10):                                                        # aletas radiais em cima do ímã
        a = k * PI / 5
        caixa(bm, W + Vector((math.cos(a) * 0.045, math.sin(a) * 0.045, -0.054)), (0.04, 0.004, 0.018), Matrix.Rotation(a, 3, 'Z'))
    cilz(g.b('bobina', True), W + Vector((0, 0, -0.11)), 0.066, 0.01, 32)
    for k in range(3):
        anel(g.b('cobre', True), W + Vector((0, 0, -0.106 - k * 0.004)), 0.0675, 0.0022, Z, 48, 6)
    cilz(g.b('aco', True), W + Vector((0, 0, -0.12)), 0.072, 0.01, 32)
    cilz(g.b('cromo', True), W + Vector((0, 0, -0.1255)), 0.03, 0.002, 24)          # polo central
    cil(g.b('led'), W + Vector((0, -0.068, -0.075)), 0.006, 0.006, Y, 10)
    pts = bezier(W + Vector((0.035, -0.04, 0.025)), W + Vector((0.07, -0.02, 0.0)), W + Vector((0.06, -0.03, -0.04)), W + Vector((0.035, -0.045, -0.065)), 6)
    mangueira(g.b('cabo_laranja', True), pts, 0.008)
    # ---------------------------------------------------------- hélices das ventoinhas (giram)
    helices = []
    for (pai, c, eixo, R) in ((giro, Vector((0.243, 0, S.z)), 'X', 0.055), (giro, cx + Vector((0, 0, Zg + 0.172)), 'Z', 0.042),
                              (b1, Vector((0.172, 0, E.z)), 'X', 0.045)):
        h = Parte('rapido_helice_%d' % len(helices), pai, c)
        bm = h.b('grafite')
        e = Vector((1, 0, 0)) if eixo == 'X' else Vector((0, 0, 1))
        for k in range(7):
            a = k * 2 * PI / 7
            rot = Matrix.Rotation(a, 3, eixo) @ (Matrix.Rotation(0.5, 3, 'X' if eixo == 'Z' else 'Y'))
            off = Matrix.Rotation(a, 3, eixo) @ (Vector((0, R * 0.55, 0)) if eixo == 'X' else Vector((R * 0.55, 0, 0)))
            tam = (0.003, R * 0.9, 0.022) if eixo == 'X' else (R * 0.9, 0.022, 0.003)
            caixa(bm, c + off, tam, rot)
        cil(h.b('laranja', True), c, R * 0.3, 0.012, e, 16)
        helices.append((h, 0 if eixo == 'X' else 2))
    # ---------------------------------------------------------- uso pesado: remendos, amassados, peças trocadas, fios
    remendo(giro, (-0.055, 0.13, Zg + 0.078), -X, Z, 0.07, 0.045, Y)
    remendo(base, (0.375, -0.4402, Z0 + 0.065), X, Z, 0.09, 0.04, -Y)
    amassado(base.b('grafite', True), (0.375, -0.345, Z0 + 0.2215), X, Y, 0.14, 0.18, 0.006, ((0.18, -0.1, 0.16), (-0.25, 0.2, 0.1)))
    amassado(giro.b('amarelo', True), (-0.1115, 0.07, Zg + 0.075), -Y, Z, 0.10, 0.05, 0.004, ((0.1, 0.1, 0.2),))
    cilx(giro.b('primer', True), (0.222, 0, S.z), 0.0755, 0.017, 32)                # tampa trocada (outra cor)
    caixa_de(base.b('primer'), (0.2965, -0.43, Z0 + 0.04), (0.2985, -0.27, Z0 + 0.11))   # tampa de inspeção trocada
    fiacao(base, (0.299, -0.295, Z0 + 0.125), Vector((-0.04, 0.0, 0.02)), (0.30, -0.315, Z0 + 0.09))
    fiacao(giro, (-0.06, -0.165, Zg + 0.1005), Vector((0.0, 0.0, 0.03)), (-0.02, -0.15, Zg + 0.1005))
    caixa_de(giro.b('oleo'), (0.10, -0.012, S.z - 0.075), (0.106, 0.012, S.z - 0.02))   # graxa escorrendo do redutor
    estencil('RX-07  4471-B', base, (0.375, -0.4405, Z0 + 0.155), -Y, Z, 0.02)
    estencil('RX-07', giro, (0.04, 0.1316, Zg + 0.075), Y, Z, 0.022)
    estencil('0418-77', b1, (-0.0525, 0.0, E.z - 0.04), -X, Z, 0.011)
    for p in (raiz, base, giro, pinhao, b1, b2, g) + tuple(h for h, _ in helices):
        p.fechar()
    itens = (item_obj('rapido_item', raiz), item_obj('rapido_item_chegando', raiz))
    return dict(nome='rapido', raiz=raiz, giro=giro, b1=b1, b2=b2, g=g, pinhao=pinhao, helices=helices, itens=itens,
                S=S, L1=L1, L2=L2, delta=PI / 2, col=COL, O=Vector(O))


def ik_rapido(A, r, z):
    L1, L2 = A['L1'], A['L2']
    zr = z - A['S'].z
    d = min(math.hypot(r, zr), L1 + L2 - 1e-4)
    c2 = (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q = math.acos(max(-1, min(1, c2)))
    f1 = math.atan2(zr, r) + math.atan2(L2 * math.sin(q), L1 + L2 * math.cos(q))
    return f1, f1 - q, L2


# =================================================================== BRAÇO LONGO
L2MIN, L2MAX = 0.64, 1.44
P0_REL = Vector((0, -0.10, 0.48))       # olhal da haste na lança (lança em repouso, vertical)
A_REL = Vector((0, 0.16, -0.12))        # olhal da camisa no giro, relativo ao ombro
X_PIST = 0.20


def braco_longo(O):
    global COL
    COL = bpy.data.collections.new('longo')
    sc.collection.children.link(COL)
    raiz = Parte('longo_raiz', None, (0, 0, 0))
    raiz.e.location = O
    laje(raiz, ((0.30, -0.30, 0.09), (0.18, -0.36, 0.05), (-0.2, 0.25, 0.04)))
    est = Parte('longo_esteiras', raiz, (0, 0, 0))
    esteira(est, -2.0)
    esteira(est, 2.0)
    est.fechar()
    Zg = Z0 + 0.36
    S = Vector((0, 0, Zg + 0.21))
    E = S + Vector((0, 0.20, 0.76))
    L1 = (E - S).length
    W = E + Vector((0, L2MIN, 0))
    # ---------------------------------------------------------- base reforçada: chapa, chumbadores, pedestal, mãos-francesas
    base = Parte('longo_base', raiz, (0, 0, 0))
    caixa_de(base.b('aco'), (-0.44, -0.44, Z0), (0.44, 0.44, Z0 + 0.035))
    bm = base.b('aco', True)
    bmn = base.b('aco')
    for k in range(16):
        t = k / 16 * 4
        lado, f = int(t), t - int(t)
        s = -0.40 + 0.8 * f
        p = [(s, -0.40), (0.40, s), (-s, 0.40), (-0.40, -s)][lado]
        cilz(bm, (p[0], p[1], Z0 + 0.055), 0.011, 0.06, 10)                          # chumbador (barra roscada)
        cilz(bmn, (p[0], p[1], Z0 + 0.038), 0.024, 0.006, 16)                        # arruela
        cil(bmn, Vector((p[0], p[1], Z0 + 0.05)), 0.02, 0.018, Z, 6)                # porca
    cilz(base.b('amarelo'), (0, 0, Z0 + 0.035 + 0.13), 0.22, 0.26, 8)
    caixa_de(base.b('listras'), (-0.09, -0.207, Z0 + 0.06), (0.09, -0.2, Z0 + 0.12))
    bm = base.b('amarelo')
    for k in range(8):
        a = k * PI / 4 + PI / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        r0 = 0.20
        cunha(bm, d * r0 + Vector((0, 0, Z0 + 0.035)), d * 0.41 + Vector((0, 0, Z0 + 0.035)), d * r0 + Vector((0, 0, Z0 + 0.24)), 0.018, Vector((-d.y, d.x, 0)))
    cilz(base.b('grafite', True), (0, 0, Z0 + 0.31), 0.25, 0.03, 48)                # flange de topo
    parafusos(base.b('aco'), (0, 0, 0), 0.232, 16, 0.011, 0.012, Z0 + 0.325)
    cilz(base.b('grafite', True), (0, 0, Zg - 0.015), 0.232, 0.03, 48)               # coroa
    dentes(base.b('aco'), (0, 0, 0), 0.24, 64, 0.018, 0.011, 0.028, Zg - 0.015)
    # central hidráulica no chão: tanque com visor, motor-bomba com aletas, mangueiras até o pedestal
    tq = Vector((0.27, -0.30, Z0 + 0.10))
    cily(base.b('amarelo', True), tq, 0.065, 0.20, 32)
    for s in (-1, 1):
        cily(base.b('grafite', True), tq + Vector((0, s * 0.1, 0)), 0.068, 0.012, 32)
        caixa_de(base.b('grafite'), (tq.x - 0.05, tq.y + s * 0.07 - 0.012, Z0 + 0.035), (tq.x + 0.05, tq.y + s * 0.07 + 0.012, tq.z - 0.03))
    caixa_de(base.b('visor'), (tq.x + 0.06, tq.y - 0.05, tq.z - 0.025), (tq.x + 0.068, tq.y + 0.03, tq.z + 0.025))
    cilz(base.b('grafite', True), tq + Vector((0, -0.04, 0.07)), 0.018, 0.02, 12)    # tampa de abastecimento
    bp = Vector((0.31, -0.04, Z0 + 0.09))
    cilx(base.b('grafite', True), bp, 0.042, 0.10, 24)                               # motor da bomba
    aletas(base.b('grafite', True), bp + Vector((-0.04, 0, 0)), X, 0.05, 7, 0.013)
    cilx(base.b('aco', True), bp + Vector((-0.07, 0, 0)), 0.03, 0.04, 16)            # bomba
    caixa_de(base.b('aco'), (0.25, -0.08, Z0 + 0.035), (0.37, 0.0, Z0 + 0.045))
    for xx in (0.28, 0.34):
        caixa_de(base.b('grafite'), (xx - 0.01, -0.07, Z0 + 0.045), (xx + 0.01, -0.01, Z0 + 0.06))
    h1 = bezier(tq + Vector((-0.04, 0.05, 0.05)), tq + Vector((-0.05, 0.10, 0.12)), bp + Vector((-0.08, -0.02, 0.07)), bp + Vector((-0.09, 0.0, 0.0)), 10)
    h2 = bezier(bp + Vector((-0.09, 0.0, 0.0)) + Vector((0, 0.03, 0)), Vector((0.20, 0.0, Z0 + 0.10)), Vector((0.17, 0.0, Z0 + 0.15)), Vector((0.19, 0.08, Z0 + 0.17)), 10)
    h3 = bezier(tq + Vector((-0.06, 0.0, 0.03)), Vector((0.16, -0.25, Z0 + 0.10)), Vector((0.17, -0.17, Z0 + 0.16)), Vector((0.145, -0.145, Z0 + 0.19)), 10)
    for h in (h1, h2, h3):
        mangueira(base.b('borracha', True), h, 0.012)
        abracadeiras(base.b('aco', True), h, 0.012, 2)
        cil(base.b('cobre', True), h[-1], 0.017, 0.025, (h[-1] - h[-2]).normalized(), 6)
    # ---------------------------------------------------------- giro: plataforma, contrapeso, mancais, olhais dos pistões
    giro = Parte('longo_giro', base, (0, 0, Zg))
    cilz(giro.b('grafite', True), (0, 0, Zg + 0.02), 0.26, 0.04, 48)
    caixa_de(giro.b('amarelo'), (-0.15, -0.20, Zg + 0.04), (0.15, 0.10, Zg + 0.16))
    caixa_de(giro.b('grafite'), (-0.25, 0.10, Zg + 0.04), (0.25, 0.21, Zg + 0.08))       # travessa dianteira
    caixa_de(giro.b('listras'), (-0.25, 0.21, Zg + 0.045), (0.25, 0.214, Zg + 0.075))
    bm = giro.b('ferro')
    for k in range(4):                                                         # contrapeso em placas
        y0 = -0.20 - k * 0.052
        caixa_de(bm, (-0.17 + 0.006 * k, y0 - 0.05, Zg + 0.04), (0.17 - 0.006 * k, y0, Zg + 0.25 - 0.008 * k))
    caixa_de(giro.b('listras'), (-0.14, -0.4125, Zg + 0.06), (0.14, -0.408, Zg + 0.2))
    for x in (-0.12, 0.12):
        for z in (Zg + 0.08, Zg + 0.20):
            cily(giro.b('cromo', True), (x, -0.30, z), 0.009, 0.235, 10)               # tirantes
            cil(giro.b('aco'), Vector((x, -0.4165, z)), 0.017, 0.012, Y, 6)
    anel(giro.b('aco', True), (0, -0.30, Zg + 0.265), 0.03, 0.008, X, 24, 8)          # olhal de içamento
    for x in (-0.09, 0.09):                                                    # mancais do ombro (chapas)
        bm = giro.b('amarelo')
        caixa_de(bm, (x - 0.015, -0.12, Zg + 0.16), (x + 0.015, 0.12, Zg + 0.26))
        cunha(bm, (x, -0.12, Zg + 0.26), (x, 0.0, S.z + 0.075), (x, 0.12, Zg + 0.26), 0.03, X)
        cilx(giro.b('grafite', True), (x / abs(x) * 0.115, 0, S.z), 0.05, 0.02, 32)
    cilx(giro.b('cromo', True), S, 0.03, 0.27, 16)                                  # pino do ombro
    for s in (-1, 1):
        cil(giro.b('aco'), S + Vector((s * 0.137, 0, 0)), 0.04, 0.016, X, 6)
    A = S + A_REL
    for s in (-1, 1):                                                          # olhais da camisa na travessa
        for dx in (-0.045, 0.045):
            caixa_de(giro.b('amarelo'), (s * X_PIST + dx - 0.008, A.y - 0.045, Zg + 0.08), (s * X_PIST + dx + 0.008, A.y + 0.045, A.z + 0.03))
        cilx(giro.b('cromo', True), (s * X_PIST, A.y, A.z), 0.016, 0.115, 12)
    # bloco de válvulas na traseira com solenoides e LEDs; mangueiras até os olhais
    caixa_de(giro.b('grafite'), (-0.07, -0.195, Zg + 0.16), (0.07, -0.13, Zg + 0.235))
    for k in range(3):
        cilz(giro.b('cobre', True), (-0.04 + k * 0.04, -0.162, Zg + 0.26), 0.014, 0.05, 12)
        cil(giro.b('led'), Vector((-0.04 + k * 0.04, -0.196, Zg + 0.22)), 0.005, 0.005, Y, 8)
    for s in (-1, 1):
        h = bezier(Vector((s * 0.07, -0.15, Zg + 0.20)), Vector((s * 0.27, -0.15, Zg + 0.22)), Vector((s * 0.27, A.y - 0.10, A.z + 0.03)), Vector((s * 0.27, A.y, A.z)), 12)
        mangueira(giro.b('borracha', True), h, 0.011)
        abracadeiras(giro.b('aco', True), h, 0.011, 2)
        cil(giro.b('cobre', True), h[-1], 0.017, 0.025, X, 6)
    # motor hidráulico do giro (lado -X) com pinhão na coroa
    mg = Vector((-0.28, -0.06, 0))
    caixa_de(giro.b('amarelo'), (-0.30, -0.10, Zg + 0.04), (-0.15, -0.02, Zg + 0.065))
    cilz(giro.b('grafite', True), mg + Vector((0, 0, Zg + 0.12)), 0.042, 0.11, 24)
    cilz(giro.b('aco', True), mg + Vector((0, 0, Zg + 0.02)), 0.018, 0.05, 16)
    cil(giro.b('cobre', True), mg + Vector((0, 0.04, Zg + 0.14)), 0.012, 0.03, Y, 6)
    h = bezier(mg + Vector((0, 0.045, Zg + 0.14)), mg + Vector((0, 0.0, Zg + 0.24)), Vector((-0.14, -0.16, Zg + 0.27)), Vector((-0.07, -0.17, Zg + 0.21)), 8)
    mangueira(giro.b('borracha', True), h, 0.009)
    abracadeiras(giro.b('aco', True), h, 0.009, 2)
    pinhao = Parte('longo_pinhao', giro, mg + Vector((0, 0, Zg - 0.015)))
    cilz(pinhao.b('aco', True), pinhao.pivo, 0.028, 0.026, 16)
    dentes(pinhao.b('aco'), pinhao.pivo, 0.033, 10, 0.012, 0.01, 0.026, 0)
    # ---------------------------------------------------------- pistões de elevação (camisa no giro, haste na lança)
    pist = []
    for s in (-1, 1):
        cam = Parte('longo_camisa_%d' % s, giro, (s * X_PIST, A.y, A.z))
        c0 = cam.pivo
        cilx(cam.b('aco', True), c0, 0.03, 0.07, 16)                                 # olhal
        cily(cam.b('amarelo', True), c0 + Vector((0, 0.24, 0)), 0.036, 0.40, 32)
        cily(cam.b('grafite', True), c0 + Vector((0, 0.43, 0)), 0.041, 0.03, 32)     # cabeçote
        cily(cam.b('grafite', True), c0 + Vector((0, 0.06, 0)), 0.041, 0.03, 32)
        tubo(cam.b('cromo', True), c0 + Vector((s * 0.045, 0.07, 0.0)), c0 + Vector((s * 0.045, 0.40, 0.0)), 0.007, 10)   # linha de óleo
        for yy in (0.07, 0.40):
            caixa_de(cam.b('aco'), (c0.x + s * 0.03 - 0.008, c0.y + yy - 0.01, c0.z - 0.008), (c0.x + s * 0.052, c0.y + yy + 0.01, c0.z + 0.008))
        caixa_de(cam.b('oleo'), (c0.x - 0.015, c0.y + 0.415, c0.z - 0.0375), (c0.x + 0.015, c0.y + 0.30, c0.z - 0.033))   # óleo escorrendo
        P = S + P0_REL + Vector((s * X_PIST, 0, 0))
        has = Parte('longo_haste_%d' % s, None, P)
        pist.append((cam, has, s))
    # ---------------------------------------------------------- lança (braço 1) com joelho
    b1 = Parte('longo_braco1', giro, S)
    K = S + Vector((0, 0, 0.50))
    cilx(b1.b('grafite', True), S, 0.072, 0.15, 32)
    bm = b1.b('amarelo')
    caixa_de(bm, (-0.06, -0.06, S.z), (0.06, 0.06, K.z + 0.04))
    rotk = Matrix.Rotation(-math.atan2(E.y - K.y, E.z - K.z), 3, 'X')
    dk = (E - K).normalized()
    caixa(bm, (K + E - dk * 0.09) / 2, (0.12, 0.12, (E - K).length - 0.09), rotk)
    bm = b1.b('grafite')
    caixa_de(bm, (-0.064, -0.064, S.z + 0.10), (0.064, 0.064, S.z + 0.14))            # cintas de reforço
    caixa_de(bm, (-0.064, -0.064, S.z + 0.34), (0.064, 0.064, S.z + 0.38))
    for s in (-1, 1):                                                          # bochechas do cotovelo
        cunha(b1.b('amarelo'), E + Vector((s * 0.0, 0, 0)) + Vector((s * 0.07, -0.14, -0.2)), E + Vector((s * 0.07, 0.07, -0.05)), E + Vector((s * 0.07, -0.02, 0.09)), 0.02, X)
    cilx(b1.b('cromo', True), E, 0.028, 0.19, 16)                                  # pino do cotovelo
    cil(b1.b('aco'), E + Vector((-0.09, 0, 0)), 0.04, 0.016, X, 6)
    for s in (-1, 1):                                                          # chapas de reforço nas laterais
        caixa_de(b1.b('grafite'), (s * 0.063 - 0.003, -0.035, S.z + 0.06), (s * 0.063 + 0.003, 0.035, K.z - 0.02))
    caixa_de(b1.b('grafite'), (0.06, -0.035, S.z + 0.16), (0.10, 0.035, S.z + 0.24))         # bloco de distribuição (óleo vem pelo pino oco)
    P0 = S + P0_REL
    caixa_de(b1.b('amarelo'), (-0.06, P0.y - 0.04, P0.z - 0.05), (0.06, -0.06, P0.z + 0.05))    # olhal traseiro da haste
    cilx(b1.b('cromo', True), P0, 0.018, 2 * X_PIST + 0.12, 12)                         # pino passante
    for s in (-1, 1):
        cilx(b1.b('grafite', True), P0 + Vector((s * 0.10, 0, 0)), 0.03, 0.08, 16)     # buchas
    # atuador rotativo hidráulico no cotovelo (+X), com portas e mangueiras pela lança
    cilx(b1.b('amarelo', True), E + Vector((0.13, 0, 0)), 0.085, 0.09, 32)
    cilx(b1.b('grafite', True), E + Vector((0.178, 0, 0)), 0.07, 0.012, 32)
    parafusos_x = b1.b('aco')
    for k in range(10):
        a = k * PI / 5
        cil(parafusos_x, E + Vector((0.18, math.cos(a) * 0.075, math.sin(a) * 0.075)), 0.008, 0.012, X, 6)
    for dz, dy in ((0.05, -0.06), (-0.05, -0.06)):
        cil(b1.b('cobre', True), E + Vector((0.13, dy - 0.03, dz)), 0.012, 0.03, Y, 6)
    for k, dy in enumerate((-0.02, 0.02)):
        h = [S + Vector((0.083, dy, 0.24))]
        for f in (0.30, 0.38, 0.46):
            h.append(S + Vector((0.083, dy, f)))
        h += bezier(K + Vector((0.083, dy, 0.0)), K + Vector((0.11, dy - 0.05, 0.06)), E + Vector((0.13, -0.16, (0.05 if k else -0.05))),
                    E + Vector((0.13, -0.105, 0.05 if k else -0.05)), 8)
        mangueira(b1.b('borracha', True), h, 0.011)
        abracadeiras(b1.b('aco', True), h[:-3], 0.011, 1)
    # ---------------------------------------------------------- braço 2: telescópico em três estágios
    b2 = Parte('longo_braco2', b1, E)
    cilx(b2.b('amarelo', True), E, 0.075, 0.12, 32)
    caixa_de(b2.b('amarelo'), (-0.055, E.y + 0.03, E.z - 0.05), (0.055, E.y + 0.55, E.z + 0.05))
    bm = b2.b('grafite')
    caixa_de(bm, (-0.059, E.y + 0.52, E.z - 0.054), (0.059, E.y + 0.55, E.z + 0.054))       # boca do estágio
    caixa_de(b2.b('borracha'), (-0.046, E.y + 0.549, E.z - 0.042), (0.046, E.y + 0.553, E.z + 0.042))
    caixa_de(b2.b('listras'), (-0.0555, E.y + 0.30, E.z - 0.03), (0.0555, E.y + 0.40, E.z + 0.03))
    # cilindro de extensão sobre o estágio externo
    cily(b2.b('grafite', True), E + Vector((0, 0.27, 0.10)), 0.024, 0.50, 24)
    for yy in (0.06, 0.48):
        caixa_de(b2.b('amarelo'), (-0.012, E.y + yy - 0.015, E.z + 0.05), (0.012, E.y + yy + 0.015, E.z + 0.09))
    h = bezier(E + Vector((0.06, 0.05, 0.06)), E + Vector((0.08, 0.15, 0.09)), E + Vector((0.03, 0.40, 0.12)), E + Vector((0.0, 0.48, 0.125)), 10)
    mangueira(b2.b('borracha', True), h, 0.008)
    abracadeiras(b2.b('aco', True), h, 0.008, 2)
    caixa_de(b2.b('aco'), (0.055, E.y + 0.39, E.z - 0.012), (0.098, E.y + 0.41, E.z + 0.012))   # suporte do cabo espiral
    meio = Parte('longo_estagio2', b2, E)
    caixa_de(meio.b('grafite'), (-0.042, E.y + 0.08, E.z - 0.038), (0.042, E.y + 0.58, E.z + 0.038))
    caixa_de(meio.b('aco'), (-0.045, E.y + 0.56, E.z - 0.041), (0.045, E.y + 0.58, E.z + 0.041))
    caixa_de(meio.b('amarelo'), (-0.014, E.y + 0.56, E.z + 0.038), (0.014, E.y + 0.58, E.z + 0.12))     # olhal da haste
    cily(meio.b('cromo', True), E + Vector((0, 0.31, 0.10)), 0.012, 0.50, 16)                        # haste de extensão
    inner = Parte('longo_estagio3', meio, E)
    caixa_de(inner.b('aco'), (-0.03, E.y + 0.12, E.z - 0.027), (0.03, E.y + 0.60, E.z + 0.027))
    for s in (-1, 1):                                                          # garfo do punho
        caixa_de(inner.b('grafite'), (s * 0.05 - 0.008, W.y - 0.055, W.z - 0.035), (s * 0.05 + 0.008, W.y + 0.03, W.z + 0.035))
    caixa_de(inner.b('grafite'), (-0.058, W.y - 0.055, W.z - 0.02), (0.058, W.y - 0.045, W.z + 0.02))
    caixa_de(inner.b('aco'), (0.03, W.y - 0.045, W.z - 0.012), (0.098, W.y - 0.035, W.z + 0.012))  # suporte do cabo espiral
    # ---------------------------------------------------------- garra de dois dedos
    g = Parte('longo_garra', inner, W)
    cilx(g.b('aco', True), W, 0.04, 0.084, 24)
    cilz(g.b('cromo', True), W + Vector((0, 0, -0.05)), 0.025, 0.04, 16)
    caixa_de(g.b('grafite'), (-0.10, -0.045 + W.y, W.z - 0.105), (0.10, 0.045 + W.y, W.z - 0.065))
    caixa_de(g.b('amarelo'), (-0.06, -0.04 + W.y, W.z - 0.07), (0.06, 0.04 + W.y, W.z - 0.06))
    cilx(g.b('aco', True), W + Vector((0, 0.055, -0.08)), 0.017, 0.16, 16)              # cilindro pneumático
    cil(g.b('cobre', True), W + Vector((0.05, 0.072, -0.08)), 0.008, 0.02, Y, 6)
    caixa_de(g.b('cromo'), (-0.095, W.y - 0.02, W.z - 0.115), (0.095, W.y + 0.02, W.z - 0.105))      # guia
    cil(g.b('led'), W + Vector((0.0, -0.046, -0.085)), 0.006, 0.005, Y, 10)
    dedos = []
    for s in (-1, 1):
        d = Parte('longo_dedo_%d' % s, g, W + Vector((s * 0.075, 0, -0.11)))
        c = d.pivo
        caixa_de(d.b('aco'), (c.x - 0.013, c.y - 0.03, c.z - 0.07), (c.x + 0.013, c.y + 0.03, c.z + 0.0))
        caixa_de(d.b('grafite'), (c.x - 0.011 - s * 0.010, c.y - 0.028, c.z - 0.095), (c.x + 0.011 - s * 0.010, c.y + 0.028, c.z - 0.06))
        caixa_de(d.b('borracha'), (c.x - s * 0.0225 - 0.002, c.y - 0.024, c.z - 0.092), (c.x - s * 0.0225 + 0.002, c.y + 0.024, c.z - 0.064))
        dedos.append((d, s))
    # ---------------------------------------------------------- cabo espiralado (do estágio externo até o punho)
    Y0, Y1 = 0.40, 0.60                                         # do suporte no externo até o suporte do punho (repouso)
    espiral = Parte('longo_espiral', b2, E)
    voltas, rr, rw = 11, 0.02, 0.0045
    def helice(L):
        pts = []
        n = voltas * 18
        for i in range(n + 1):
            t = i / n
            a = t * voltas * 2 * PI
            pts.append(E + Vector((0.09 + rr * math.cos(a), Y0 + L * t, rr * math.sin(a))))
        return pts
    c_pts, e_pts = helice(Y1 - Y0), helice(Y1 - Y0 + (L2MAX - L2MIN))
    bm = espiral.b('borracha', True)
    def tubo_pts(bm, pts):
        aneis = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            q = t.to_track_quat('Z', 'Y').to_matrix()
            aneis.append([bm.verts.new(p + q @ Vector((math.cos(k * PI / 3) * rw, math.sin(k * PI / 3) * rw, 0))) for k in range(6)])
        for A_, B_ in zip(aneis, aneis[1:]):
            for k in range(6):
                bm.faces.new((A_[k], A_[(k + 1) % 6], B_[(k + 1) % 6], B_[k]))
        return aneis
    tubo_pts(bm, c_pts)
    tmp = bmesh.new()
    tubo_pts(tmp, e_pts)
    esticado = [v.co.copy() - espiral.pivo for v in tmp.verts]
    tmp.free()
    # ---------------------------------------------------------- uso pesado: remendos, amassados, peças trocadas, fios, óleo
    remendo(b1, (-0.0665, 0.0, S.z + 0.29), -Y, Z, 0.08, 0.08, -X)
    remendo(giro, (0.151, -0.08, Zg + 0.10), Y, Z, 0.08, 0.06, X)
    amassado(giro.b('ferro', True), (0.1705, -0.226, Zg + 0.13), Y, Z, 0.045, 0.16, 0.007, ((0.1, 0.15, 0.25), (-0.2, -0.25, 0.15)))
    amassado(giro.b('amarelo', True), (-0.04, 0.1005, Zg + 0.12), -X, Z, 0.17, 0.07, 0.006, ((-0.2, 0.1, 0.18), (0.25, -0.15, 0.12)))
    amassado(base.b('aco', True), (-0.22, -0.30, Z0 + 0.0355), X, Y, 0.12, 0.08, 0.005, ((0.1, 0.0, 0.22), (-0.3, 0.2, 0.15)))
    caixa_de(giro.b('zarcao'), (-0.1645, -0.304, Zg + 0.04), (0.1645, -0.251, Zg + 0.2435))   # placa trocada (zarcão)
    cily(b2.b('primer', True), E + Vector((0, 0.27, 0.10)), 0.0245, 0.22, 24)                      # camisa trocada pela metade
    fiacao(giro, (0.07, -0.185, Zg + 0.225), Vector((0.03, -0.01, 0.02)), (0.07, -0.185, Zg + 0.17))
    bm = base.b('oleo')
    for (x, y, r) in ((0.27, -0.12, 0.06), (0.24, -0.32, 0.07), (-0.2, 0.2, 0.05), (0.05, -0.30, 0.04)):
        mancha(bm, (x, y), r, Z0 + 0.0362)
    caixa_de(base.b('oleo'), (bp.x - 0.075, bp.y - 0.003, Z0 + 0.045), (bp.x - 0.07, bp.y + 0.003, bp.z - 0.02))
    estencil('LG-12  0093-K', b1, (-0.066, 0.0, S.z + 0.42), -X, Y, 0.016)
    estencil('LG-12', giro, (0.0, -0.408, Zg + 0.212), -Y, Z, 0.02)
    estencil('OLEO HID 46', base, tq + Vector((0.0, 0.0, 0.0656)), Z, -X, 0.018)
    for p in (raiz, base, giro, pinhao, b1, b2, meio, inner, g, espiral) + tuple(d for d, _ in dedos) + tuple(c for c, _, _ in pist):
        p.fechar()
    eo = espiral.objs[0]
    eo.shape_key_add(name='Base')
    k2 = eo.shape_key_add(name='Esticado')
    for i, co in enumerate(esticado):
        k2.data[i].co = co
    # hastes: filhas da lança; olhal no pino e haste apontando para a camisa (repouso: ao longo de -Y)
    for cam, has, s in pist:
        has.pai = b1
        has.e.parent = b1.e
        has.e.location = has.pivo - b1.pivo
        c0 = has.pivo
        cily(has.b('cromo', True), c0 + Vector((0, -0.15, 0)), 0.018, 0.30, 24)
        cilx(has.b('aco', True), c0, 0.028, 0.06, 16)
        has.fechar()
    itens = (item_obj('longo_item', raiz), item_obj('longo_item_chegando', raiz))
    return dict(nome='longo', raiz=raiz, giro=giro, b1=b1, b2=b2, g=g, pinhao=pinhao, meio=meio, inner=inner, dedos=dedos,
                pist=pist, espiral=eo, itens=itens, S=S, L1=L1, delta=math.atan2(E.z - S.z, E.y - S.y), col=COL, O=Vector(O))


def ik_longo(A, r, z):
    zr = z - A['S'].z
    f1 = math.radians(85 - 70 * (r - 0.36) / (2.0 - 0.36))
    Ex, Ez = A['L1'] * math.cos(f1), A['L1'] * math.sin(f1)
    vx, vz = r - Ex, zr - Ez
    l2 = math.hypot(vx, vz)
    if not (L2MIN - 1e-3 <= l2 <= L2MAX + 1e-3):
        print('AVISO l2 fora: %.3f (r=%.2f z=%.2f)' % (l2, r, z))
    return f1, math.atan2(vz, vx), max(L2MIN, min(L2MAX, l2))


# =================================================================== pose e animação
def posar(A, yaw, f1, f2, l2, aberto=1.0, q=None):
    a1 = f1 - A['delta']
    A['giro'].e.rotation_euler = (0, 0, yaw)
    A['b1'].e.rotation_euler = (a1, 0, 0)
    A['b2'].e.rotation_euler = (f2 - a1, 0, 0)
    A['g'].e.rotation_euler = (-f2, 0, 0)
    A['pinhao'].e.rotation_euler = (0, 0, -yaw * (0.24 / 0.033 if A['nome'] == 'longo' else 0.148 / 0.022))
    objs = [A['giro'].e, A['b1'].e, A['b2'].e, A['g'].e, A['pinhao'].e]
    if A['nome'] == 'longo':
        ext = (l2 - L2MIN) / 2
        A['meio'].e.location = (0, ext, 0)
        A['inner'].e.location = (0, ext, 0)
        objs += [A['meio'].e, A['inner'].e]
        for d, s in A['dedos']:
            d.e.location = d.pivo - A['g'].pivo + Vector((s * 0.028 * aberto, 0, 0))
            objs.append(d.e)
        A['espiral'].data.shape_keys.key_blocks['Esticado'].value = (l2 - L2MIN) / (L2MAX - L2MIN)
        if q is not None:
            A['espiral'].data.shape_keys.key_blocks['Esticado'].keyframe_insert('value', frame=q)
        S = A['S']
        Ap = S + A_REL
        P0 = S + P0_REL
        rel = P0 - S
        py = rel.y * math.cos(a1) - rel.z * math.sin(a1)
        pz = rel.y * math.sin(a1) + rel.z * math.cos(a1)
        th = math.atan2(S.z + pz - Ap.z, S.y + py - Ap.y)
        for cam, has, s in A['pist']:
            cam.e.rotation_euler = (th, 0, 0)
            has.e.rotation_euler = (th - a1, 0, 0)
            objs += [cam.e, has.e]
    if q is not None:
        for o in objs:
            chave(o, 'rotation_euler', q)
            chave(o, 'location', q)


def tabela(r_ext, r_ret, z_pega, z_ret):
    h = 0.14
    return [(0.00, r_ext, z_pega + h, PI), (0.07, r_ext, z_pega, PI), (0.13, r_ext, z_pega, PI), (0.19, r_ext, z_pega + h, PI),
            (0.30, r_ret, z_ret, PI * 0.85), (0.42, r_ret, z_ret, PI * 0.15), (0.53, r_ext, z_pega + h, 0.0),
            (0.60, r_ext, z_pega, 0.0), (0.66, r_ext, z_pega, 0.0), (0.72, r_ext, z_pega + h, 0.0),
            (0.82, r_ret, z_ret, PI * 0.15), (0.91, r_ret, z_ret, PI * 0.85), (1.00, r_ext, z_pega + h, PI)]


def animar(A, ciclos, r_ext, r_ret, z_ret, desce):
    z_pega = TOPO_ESTEIRA + H_ITEM + desce
    tab = tabela(r_ext, r_ret, z_pega, z_ret)
    ik = ik_rapido if A['nome'] == 'rapido' else ik_longo
    it, chega = A['itens']
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        u = (fr * ciclos) % 1.0
        r, z, yaw = trajetoria(u, tab)
        f1, f2, l2 = ik(A, r, z)
        preso = 0.10 <= u < 0.63
        aberto = 1.0 - suave((u - 0.08) / 0.03) + suave((u - 0.62) / 0.03)
        aberto = max(0.0, min(1.0, aberto))
        posar(A, yaw, f1, f2, l2, aberto, q)
        # item: na esteira sul → na garra → na esteira norte, sai andando; outro chega pelo sul
        zc = TOPO_ESTEIRA + H_ITEM / 2
        if preso:
            p = Vector((-r * math.sin(yaw), r * math.cos(yaw), z - desce - H_ITEM / 2))
            it.location, it.rotation_euler = p, (0, 0, yaw)
            vis = True
        elif u < 0.10:
            it.location, it.rotation_euler = (0, -r_ext, zc), (0, 0, PI)
            vis = True
        else:
            t = suave((u - 0.70) / 0.26)
            it.location, it.rotation_euler = (0, r_ext + 0.48 * t, zc), (0, 0, 0)
            vis = u < 0.96
        it.hide_render = it.hide_viewport = not vis
        for c in ('location', 'rotation_euler', 'hide_render', 'hide_viewport'):
            chave(it, c, q)
        t = (u - 0.72) / 0.28
        chega.location = (0, -r_ext - 0.48 * (1 - suave(t)), zc)
        chega.rotation_euler = (0, 0, PI)
        chega.hide_render = chega.hide_viewport = not (u >= 0.72)
        for c in ('location', 'rotation_euler', 'hide_render', 'hide_viewport'):
            chave(chega, c, q)
        if A['nome'] == 'rapido':
            bob = M['bobina'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
            bob.default_value = 3.0 if preso else 0.0
            bob.keyframe_insert('default_value', frame=q)
            for h, eixo in A['helices']:
                rot = [0, 0, 0]
                rot[eixo] = fr * 2 * PI * 16
                h.e.rotation_euler = rot
                chave(h.e, 'rotation_euler', q)


rap = braco_rapido((0.0, 0.0, 0.0))
lon = braco_longo((1.8, 0.0, 0.0))
animar(rap, 2, 1.0, 0.55, Z0 + 0.65, 0.1265)
animar(lon, 1, 2.0, 0.60, 0.85, 0.17)

# ------------------------------------------------------------------ braço normal aprovado (glb do estudo)
COL = bpy.data.collections.new('normal')
sc.collection.children.link(COL)
GLB = os.path.join(AQUI, 'modelos', 'estudos', 'braco_detalhado', 'braco_detalhado_sem_textura.glb')
antes = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
novos = [o for o in bpy.data.objects if o not in antes]
TROCA = {'P_Faixa': 'amarelo', 'P_Escuro': 'grafite', 'P_Aco': 'aco', 'P_Metal': 'cromo', 'P_Cobre': 'cobre'}
normal_raiz = bpy.data.objects.new('normal_raiz', None)
COL.objects.link(normal_raiz)
normal_raiz.location = (-1.6, 0.0, Z0)
for o in novos:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    COL.objects.link(o)
    if o.parent is None:
        o.parent = normal_raiz
    if o.type == 'MESH':
        for s_ in o.material_slots:
            nome = s_.material.name.split('.')[0] if s_.material else ''
            if nome in TROCA:
                s_.material = M[TROCA[nome]]
            else:
                print('material do glb sem troca:', nome)
        for pg in o.data.polygons:
            pg.use_smooth = False
NR = Parte('normal_laje', None, (0, 0, 0))
NR.e.location = (-1.6, 0, 0)
laje(NR, ((0.2, 0.25, 0.05),))
NR.fechar()
NE = Parte('normal_esteiras', None, (0, 0, 0))
NE.e.location = (-1.6, 0, 0)
esteira(NE, -1.0)
esteira(NE, 1.0)
NE.fechar()
normal_raiz.location = (-1.6, 0.0, Z0)

# ------------------------------------------------------------------ cena: chão, luz, câmera
COL = sc.collection
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
novo_obj('chao', bm, 'chao', chanfro=False)
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
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def mostrar(*nomes):
    for c in bpy.data.collections:
        c.hide_render = c.name not in nomes


def foto(nome, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.filepath = os.path.join(AQUI, nome + '.png')
    bpy.ops.render.render(write_still=True)


modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_fotos = sys.argv[sys.argv.index('--') + 2:] if '--' in sys.argv else []
quer = lambda n: not so_fotos or n in so_fotos
if modo in ('foto', 'teste'):
    sc.cycles.samples = 128 if modo == 'foto' else 24
    R = rap['O']
    Lo = lon['O']
    if quer('braco_rapido_0'):
        mostrar('rapido')
        sc.frame_set(1 + int(0.24 * 48))                                        # subindo com a placa presa
        mirar(R + Vector((2.5, -1.2, 1.45)), R + Vector((0, -0.25, 0.42)), 44)
        foto('braco_rapido_0', 1200, 1100)
    if quer('braco_rapido_perto'):
        mostrar('rapido')
        sc.frame_set(1 + int(0.33 * 48))                                        # recolhido no giro, eletroímã aceso
        mirar(R + Vector((1.05, -0.95, 0.95)), R + Vector((0.02, -0.12, 0.52)), 36)
        foto('braco_rapido_perto', 1300, 1000)
    if quer('braco_longo_0'):
        mostrar('longo')
        sc.frame_set(1 + int(0.10 * 96))                                        # esticado, pegando 2 tiles ao sul
        mirar(Lo + Vector((3.4, -0.2, 1.9)), Lo + Vector((0, -0.85, 0.5)), 30)
        foto('braco_longo_0', 1300, 1000)
    if quer('braco_longo_perto'):
        mostrar('longo')
        sc.frame_set(1 + int(0.36 * 96))
        mirar(Lo + Vector((1.25, -1.0, 1.25)), Lo + Vector((0.0, 0.0, 0.75)), 30)
        foto('braco_longo_perto', 1300, 1000)
    if quer('braco_longo_recolhido'):
        mostrar('longo')
        sc.frame_set(1 + int(0.10 * 96))
        for o in lon['col'].all_objects:
            if o.animation_data:
                o.animation_data_clear()
        if lon['espiral'].data.shape_keys.animation_data:
            lon['espiral'].data.shape_keys.animation_data_clear()
        f1 = math.radians(85)
        posar(lon, PI * 0.0, f1, math.radians(-62), L2MIN, 1.0)
        for it in lon['itens']:
            it.hide_render = True
        mirar(Lo + Vector((1.9, -1.7, 1.35)), Lo + Vector((0, 0, 0.62)), 36)
        foto('braco_longo_recolhido', 1100, 1200)
    if quer('bracos_juntos'):
        # volta a animação do longo se foi apagada: refaz
        if not lon['b1'].e.animation_data:
            animar(lon, 1, 2.0, 0.60, 0.85, 0.17)
        mostrar('rapido', 'longo', 'normal')
        sc.frame_set(1 + int(0.40 * 96))
        for o in bpy.data.objects:
            if 'esteiras' in o.name or '_item' in o.name:
                o.hide_render = True
                if o.animation_data:
                    o.animation_data_clear()
                o.hide_render = True
        mirar(Vector((0.15, -3.9, 1.75)), Vector((0.1, 0.1, 0.55)), 30)
        foto('bracos_juntos', 1700, 950)
print('BRACOS ok')
