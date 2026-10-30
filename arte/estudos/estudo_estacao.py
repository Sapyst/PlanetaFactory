"""Estudo isolado (fora do jogo): ESTAÇÃO DE TREM (terminal de carga autônomo), 2×3 tiles (1,92 × 2,90 × 2,15 m).
x leste, y norte; a área vai de x -0,96..0,96 e y -1,45..1,45. A linha passa encostada a OESTE, por fora da área
(eixo em x = -1,5). Esteiras a LESTE: entrada no tile L2 (sul, y = -1) e saída no tile L0 (norte, y = +1).

Sem humanos: nada de plataforma de passageiros, banco, bilheteria, guarda-corpo ou escada. É um terminal que a IA
construiu para si: pórtico de aço em balanço sobre a linha, cobertura de chapa corrugada furada e enferrujada,
dois braços hidráulicos (no estilo do braço aprovado) sobre pedestais, funil sobre balança com quatro células de
carga, calha vibratória de descarga, campo violeta que segura o minério no ar e o pousa no vagão, scanner que varre a
carga com um leque de luz, sensores laser de chegada do trem, sinais, armário da IA com antena e farol, ar
comprimido com flanges, cabos em eletrocalha. Um trecho de linha (lastro, dormentes, trilhos) e um vagão de carga
parado dão onde o braço trabalhar.

Laço de 4 s: braço SUL tira minério da esteira de entrada e joga no funil; a calha despeja pedras no campo, que as
segura girando e pousa no monte do vagão; braço NORTE tira pilhas de chapa do vagão e põe na esteira de saída.
Uso: blender -b --python estudo_estacao.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mancha, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


# ------------------------------------------------------------------ (copiado de estudo_braco_variantes.py)
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



# ------------------------------------------------------------------ materiais próprios da estação
M.update({
    'vagao': mats.material('Vagão óxido', (0.30, 0.085, 0.045), 0, 0.6, ferrugem=0.9, desgaste=1.0, sujeira=1.0),
    'chapa': mats.material('Chapa corrugada', (0.40, 0.40, 0.38), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=1.0),
    'chapa_primer': mats.material('Chapa trocada', (0.22, 0.30, 0.33), 0, 0.6, ferrugem=0.7, desgaste=0.9, sujeira=1.0),
    'minerio': mats.material('Minério de ferro', (0.17, 0.085, 0.055), 0.3, 0.8, pintura=False, ferrugem=0.6, sujeira=0.4, desgaste=0.0),
    'po': mats.material('Pó de minério', (0.27, 0.12, 0.065), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'madeira': mats.material('Dormente', (0.075, 0.058, 0.042), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'lastro': mats.material('Lastro', (0.24, 0.235, 0.225), 0, 0.95, pintura=False, sujeira=0.8, desgaste=0.0),
    'lastro2': mats.material('Lastro escuro', (0.17, 0.16, 0.15), 0, 0.95, pintura=False, sujeira=0.8, desgaste=0.0),
    'trilho': mats.material('Trilho', (0.36, 0.33, 0.30), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=0.9),
    'boleto': mats.material('Boleto polido', (0.70, 0.70, 0.70), 1.0, 0.22, pintura=False, sujeira=0.2),
    'laser': emissor('Laser vermelho', (1.0, 0.04, 0.02), 30.0, base=(1.0, 0.1, 0.05)),
    'scan': emissor('Leque de leitura', (0.55, 0.12, 1.0), 25.0, base=(0.5, 0.2, 0.9)),
    'nucleo': emissor('Núcleo da IA', (0.5, 0.12, 1.0), 6.0, base=(0.3, 0.1, 0.5)),
    'bobina_campo': emissor('Bobina do campo', (0.55, 0.15, 1.0), 4.0, base=(0.80, 0.42, 0.24)),
    'sinal_vermelho': emissor('Sinal vermelho', (1.0, 0.03, 0.02), 14.0, base=(0.6, 0.05, 0.03)),
    'sinal_ambar': emissor('Sinal âmbar', (1.0, 0.45, 0.03), 0.0, base=(0.5, 0.25, 0.02)),
    'sinal_verde': emissor('Sinal verde', (0.1, 1.0, 0.15), 0.0, base=(0.05, 0.25, 0.06)),
    'farol': emissor('Farol âmbar', (1.0, 0.42, 0.03), 3.0, base=(0.7, 0.32, 0.04)),
    'farol_luz': emissor('Refletor do farol', (1.0, 0.5, 0.06), 40.0, base=(1.0, 0.6, 0.2)),
})
for k in range(6):
    M['seg%d' % k] = emissor('Barra de peso %d' % k, (1.0, 0.45, 0.04) if k < 4 else (1.0, 0.08, 0.03), 0.0, base=(0.06, 0.04, 0.03))
M['ferrugem_chao'] = mats.material('Ferrugem no chão', (0.22, 0.08, 0.03), 0, 0.9, pintura=False, sujeira=0.3, desgaste=0.0)
M['bobina_campo'].node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 1.0
for nome, kw in (('vagao', dict(escorrido=1.0, poeira=1.0, lama=1.0)), ('chapa', dict(escorrido=1.0, fuligem=0.6)),
                 ('chapa_primer', dict(escorrido=0.9)), ('trilho', dict(poeira=0.6)), ('madeira', dict(escorrido=0.3)),
                 ('lastro', dict(escorrido=0.0, fuligem=0.3)), ('lastro2', dict(escorrido=0.0))):
    envelhecer(M[nome], **{**dict(poeira=0.8, lama=0.8, escorrido=0.7, fuligem=0.5), **kw})


def campo_mat():
    """Campo da IA: brilho violeta transparente, mais forte na borda (silhueta) e em faixas que descem."""
    m = bpy.data.materials.new('Campo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.5, 0.14, 1.0, 1)
    em.inputs['Strength'].default_value = 2.5
    mx = no(nt, 'ShaderNodeMixShader')
    lw = no(nt, 'ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.35
    tc = no(nt, 'ShaderNodeTexCoord')
    wv = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z')
    wv.inputs['Scale'].default_value = 4.5
    wv.inputs['Distortion'].default_value = 2.0
    wv.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    fx = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.6, 'From Max': 1.0, 'To Min': 0.0, 'To Max': 0.22})
    nt.links.new(wv.outputs['Fac'], fx.inputs['Value'])
    bd = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.2, 'From Max': 1.0, 'To Min': 0.04, 'To Max': 0.55})
    nt.links.new(lw.outputs['Facing'], bd.inputs['Value'])
    so = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(fx.outputs['Result'], so.inputs[0])
    nt.links.new(bd.outputs['Result'], so.inputs[1])
    nt.links.new(so.outputs['Value'], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    m['onda'] = wv.name
    return m


M['campo'] = campo_mat()


# ------------------------------------------------------------------ geometria extra
def perfil_I(bm, a, b, h, w, v, tf=0.012, tw=0.008):
    """Perfil I de a até b; v = direção da altura (as mesas ficam separadas ao longo de v)."""
    a, b = Vector(a), Vector(b)
    u = (b - a).normalized()
    v = Vector(v).normalized()
    s = v.cross(u)
    rot = Matrix((s, v, u)).transposed()
    L = (b - a).length
    c = (a + b) / 2
    caixa(bm, c + v * (h / 2 - tf / 2), (w, tf, L), rot)
    caixa(bm, c - v * (h / 2 - tf / 2), (w, tf, L), rot)
    caixa(bm, c, (tw, h - 2 * tf, L), rot)


def chapa_corrugada(bm, x0, x1, y0, y1, z, furos=(), passo=0.076, amp=0.009, dx=0.04, ondula_y=True):
    """Telha de aço ondulada (ondas ao longo de y, o caimento em x), com furos de ferrugem de borda irregular."""
    nx = max(2, int(round((x1 - x0) / dx)))
    ny = max(2, int(round((y1 - y0) / (passo / 8))))
    vs = [[None] * (ny + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        for j in range(ny + 1):
            y = y0 + (y1 - y0) * j / ny
            zz = z + amp * math.sin(2 * PI * (y - y0) / passo) - 0.006 * math.sin(PI * (x - x0) / (x1 - x0)) * 0.5
            vs[i][j] = bm.verts.new((x, y, zz))
    for i in range(nx):
        for j in range(ny):
            cx = x0 + (x1 - x0) * (i + 0.5) / nx
            cy = y0 + (y1 - y0) * (j + 0.5) / ny
            fura = False
            for (hx, hy, hr, sd) in furos:
                d = math.hypot(cx - hx, cy - hy)
                a = math.atan2(cy - hy, cx - hx)
                if d < hr * (1 + 0.32 * math.sin(3 * a + sd) + 0.18 * math.sin(7 * a + 2 * sd) + 0.1 * math.sin(13 * a + sd)):
                    fura = True
                    break
            if not fura:
                bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)


def prisma_y(bm, perfil, y0, y1):
    """Prisma ao longo de y com seção (x, z) dada (lista convexa, anti-horária vista de +y)."""
    a = [bm.verts.new((x, y0, z)) for x, z in perfil]
    b = [bm.verts.new((x, y1, z)) for x, z in perfil]
    n = len(perfil)
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))


def mola(bm, base, h, R, r, voltas=5, lados=8):
    """Mola helicoidal vertical (tubo em hélice)."""
    pts = [Vector(base) + Vector((R * math.cos(t), R * math.sin(t), h * t / (2 * PI * voltas)))
           for t in (i * 2 * PI * voltas / (voltas * 12) for i in range(voltas * 12 + 1))]
    for a, b in zip(pts, pts[1:]):
        cil(bm, (a + b) / 2, r, (b - a).length + r * 0.8, b - a, lados)


def flange_tubo(bm, a, b, r):
    """Flange (dois discos com parafusos) no meio de a→b."""
    a, b = Vector(a), Vector(b)
    u = (b - a).normalized()
    c = (a + b) / 2
    cil(bm, c, r * 1.9, 0.014, u, 16)
    w = u.orthogonal().normalized()
    w2 = u.cross(w)
    for k in range(6):
        ang = k * PI / 3
        cil(bm, c + (w * math.cos(ang) + w2 * math.sin(ang)) * r * 1.55, r * 0.22, 0.03, u, 6)


def cano(parte, pts, r, mat='aco', flanges=(), lados=16):
    """Cano rígido por pontos: trechos retos, cotovelo redondo (esfera) e flanges nos trechos pedidos."""
    pts = [Vector(p) for p in pts]
    bm = parte.b(mat, True)
    for a, b in zip(pts, pts[1:]):
        cil(bm, (a + b) / 2, r, (b - a).length, b - a, lados)
    for p in pts[1:-1]:
        bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r * 1.0, matrix=Matrix.Translation(p))
    for i in flanges:
        flange_tubo(parte.b('ferro', True), pts[i], pts[i + 1], r)


def feixe(parte, pts, r=0.006, cores=('borracha', 'cabo_laranja', 'borracha', 'fio_azul'), passo=3):
    """Feixe de cabos paralelos (desvio lateral pequeno) com abraçadeiras."""
    pts = [Vector(p) for p in pts]
    n = len(cores)
    for k, mat in enumerate(cores):
        off = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            w = t.cross(Z if abs(t.z) < 0.9 else X).normalized()
            w2 = t.cross(w)
            ang = 2 * PI * k / n
            off.append(p + (w * math.cos(ang) + w2 * math.sin(ang)) * r * 1.6)
        mangueira(parte.b(mat, True), off, r, 8)
    abracadeiras(parte.b('aco', True), pts, r * 2.2, passo, 0.01)


Z0 = 0.05                 # topo da laje
TOPO = 0.22               # topo da lona das esteiras
XT = -1.5                 # eixo da linha
TOPO_TRILHO = 0.178
DECK = 0.34               # piso do vagão
PAREDE = 0.80             # borda das paredes do vagão
GRIP = 0.15               # do punho ao centro do item preso

# ------------------------------------------------------------------ carga do vagão (função de altura usada no scanner)
MONTE_C = Vector((XT, -0.42))


def monte(x, y):
    dx = (x - MONTE_C.x) / 0.40
    dy = (y - MONTE_C.y) / 0.88
    return DECK + 0.25 * max(0.0, 1 - dx * dx * 0.55 - dy * dy)


PILHAS = [(-1.38, 0.80, 3), (-1.62, 0.80, 2), (-1.38, 1.13, 2), (-1.62, 1.13, 3), (-1.50, 0.48, 1)]
H_CHAPA = 0.08


def topo_carga(x, y):
    z = max(DECK, monte(x, y))
    for (px, py, n) in PILHAS:
        if abs(x - px) < 0.05 and abs(y - py) < 0.09:
            z = max(z, DECK + n * H_CHAPA)
    return z


raiz = Parte('estacao', None, (0, 0, 0))


# =================================================================== laje
def laje_estacao(p):
    bm = p.b('concreto')
    v = caixa(bm, (0, 0, Z0 / 2), (1.92, 2.90, Z0))
    bm = p.b('listras')
    caixa_de(bm, (-0.96, -1.45, Z0), (-0.88, 1.45, Z0 + 0.0015))           # borda do lado da linha
    for s in (-1, 1):
        caixa_de(bm, (-0.96, s * 1.45 - (0.04 if s > 0 else -0.04), Z0), (0.96, s * 1.45, Z0 + 0.0015))
    bm = p.b('ferro')
    for y in (-0.5, 0.5):                                                  # juntas de dilatação
        caixa_de(bm, (-0.88, y - 0.004, Z0 - 0.003), (0.96, y + 0.004, Z0 + 0.0008))
    caixa_de(bm, (0.2, -1.41, Z0 - 0.003), (0.208, 1.41, Z0 + 0.0008))
    # manchas: óleo sob os braços e esteiras, pó de minério sob a calha e na borda
    bm = p.b('oleo')
    for (x, y, r) in ((-0.45, -0.55, 0.09), (-0.75, 0.55, 0.07), (0.4, -0.95, 0.06), (0.55, 0.62, 0.08), (-0.2, 0.15, 0.05)):
        mancha(bm, (x, y), r, Z0 + 0.0012)
    bm = p.b('po')
    for (x, y, r) in ((-0.8, 0.0, 0.22), (-0.92, -0.35, 0.16), (-0.9, 0.4, 0.12), (-0.4, 0.0, 0.18), (0.1, -1.0, 0.14),
                      (-0.6, -0.3, 0.1), (-0.93, 1.1, 0.1), (-0.93, -1.0, 0.13)):
        mancha(bm, (x, y), r, Z0 + 0.0008 + random.random() * 0.0003)
    bm = p.b('minerio')
    for _ in range(26):                                                    # pedrinhas caídas
        x, y = random.uniform(-0.95, -0.2), random.gauss(0, 0.35)
        pedra(bm, (x, y, Z0 + 0.008), random.uniform(0.008, 0.02), 0.6)


# =================================================================== linha: lastro, dormentes, trilhos
def linha(p):
    y0, y1 = -2.7, 2.7
    prisma_y(p.b('lastro'), [(-2.10, 0.0), (-0.97, 0.0), (-1.07, 0.075), (-1.98, 0.075)][::-1], y0, y1)
    for k in range(4200):                                                  # brita
        x = random.uniform(-2.08, -0.98)
        y = random.uniform(y0 + 0.02, y1 - 0.02)
        if x < -1.98:
            z = 0.075 * (x + 2.10) / 0.12
        elif x > -1.07:
            z = 0.075 * (-0.97 - x) / 0.10
        else:
            z = 0.075
        pedra(p.b('lastro' if random.random() < 0.6 else 'lastro2'), (x, y, z - 0.004), random.uniform(0.014, 0.026), 0.75)
    n = int((y1 - y0) / 0.22)
    for k in range(n):
        y = y0 + 0.11 + k * 0.22
        mat = 'concreto' if k in (5, 17) else 'madeira'                    # dormentes trocados por concreto
        tor = Matrix.Rotation(random.uniform(-0.03, 0.03), 3, 'Z')
        caixa(p.b(mat), (XT + random.uniform(-0.01, 0.01), y, 0.093), (0.86, 0.085, 0.04), tor)
        for s in (-1, 1):
            caixa(p.b('ferro'), (XT + s * 0.25, y, 0.1155), (0.11, 0.075, 0.006))     # placa de apoio
            for d in (-0.042, 0.042):
                cil(p.b('ferrugem' if 'ferrugem' in M else 'ferro'), Vector((XT + s * 0.25 + d, y + 0.025 * s, 0.121)), 0.006, 0.01, Z, 6)
    for s in (-1, 1):                                                      # trilhos: patim, alma, boleto
        x = XT + s * 0.25
        caixa_de(p.b('trilho'), (x - 0.03, y0, 0.1185), (x + 0.03, y1, 0.128))
        caixa_de(p.b('trilho'), (x - 0.007, y0, 0.128), (x + 0.007, y1, 0.158))
        caixa_de(p.b('trilho'), (x - 0.018, y0, 0.158), (x + 0.018, y1, 0.172))
        caixa_de(p.b('boleto'), (x - 0.016, y0, 0.172), (x + 0.016, y1, TOPO_TRILHO))
        for yj in (-1.9, 1.3):                                             # tala de junção com parafusos
            for t in (-1, 1):
                caixa_de(p.b('ferro'), (x + t * 0.007, yj - 0.12, 0.13), (x + t * 0.016, yj + 0.12, 0.156))
                for d in (-0.08, -0.03, 0.03, 0.08):
                    cil(p.b('aco'), Vector((x + t * 0.02, yj + d, 0.143)), 0.007, 0.008, X, 6)
    bm = p.b('po')
    for (x, y, r) in ((-1.15, 0.0, 0.2), (-1.3, -0.4, 0.16), (-1.2, 0.5, 0.12)):
        mancha(bm, (x, y), r, 0.077)
    bm = p.b('oleo')
    for (y, r) in ((-1.2, 0.08), (0.6, 0.1), (1.9, 0.07)):
        mancha(bm, (XT + random.uniform(-0.1, 0.1), y), r, 0.1145)


# =================================================================== vagão de carga (parado)
def vagao(p):
    xw = 0.37
    ey = 1.45
    for yb in (-0.95, 0.95):                                               # truques
        for s in (-1, 1):
            caixa_de(p.b('grafite'), (XT + s * 0.31 - 0.02, yb - 0.30, 0.20), (XT + s * 0.31 + 0.02, yb + 0.30, 0.27))   # laterais
            for dy in (-0.17, 0.17):
                cilx(p.b('ferro', True), (XT + s * 0.25, yb + dy, 0.253), 0.075, 0.03, 20)                         # roda
                cilx(p.b('aco', True), (XT + s * 0.25 - s * 0.018, yb + dy, 0.253), 0.08, 0.008, 20)               # friso
                cilx(p.b('aco', True), (XT + s * 0.31, yb + dy, 0.253), 0.032, 0.05, 12)                           # mancal
            mola(p.b('aco', True), (XT + s * 0.31, yb, 0.27), 0.05, 0.025, 0.006, 4)
        for dy in (-0.17, 0.17):
            cilx(p.b('aco', True), (XT, yb + dy, 0.253), 0.022, 0.62, 12)                                          # eixo
        caixa_de(p.b('grafite'), (XT - 0.33, yb - 0.06, 0.27), (XT + 0.33, yb + 0.06, 0.31))                        # travessa
        cil(p.b('aco', True), Vector((XT, yb, 0.315)), 0.06, 0.02, Z, 16)                                          # prato do pião
    # chassi, piso, paredes com montantes
    caixa_de(p.b('grafite'), (XT - xw, -ey, 0.31), (XT + xw, ey, 0.33))
    caixa_de(p.b('grafite'), (XT - 0.06, -ey - 0.02, 0.27), (XT + 0.06, ey + 0.02, 0.31))
    caixa_de(p.b('vagao'), (XT - xw + 0.01, -ey + 0.07, 0.33), (XT + xw - 0.01, ey - 0.07, DECK))
    for s in (-1, 1):
        caixa_de(p.b('vagao'), (XT + s * xw - 0.012, -1.38, DECK - 0.01), (XT + s * xw + 0.003 * s, 1.38, PAREDE))
        caixa_de(p.b('aco'), (XT + s * (xw + 0.004) - 0.012, -1.40, PAREDE - 0.025), (XT + s * (xw + 0.004) + 0.012, 1.40, PAREDE + 0.01))
        for k in range(10):
            y = -1.30 + k * 0.289
            caixa_de(p.b('vagao'), (XT + s * (xw + 0.012) - 0.012, y - 0.015, 0.31), (XT + s * (xw + 0.012) + 0.012, y + 0.015, PAREDE - 0.025))
            for zz in (0.36, 0.55, 0.74):
                cil(p.b('ferro'), Vector((XT + s * (xw + 0.026), y, zz)), 0.006, 0.006, X, 6)                     # rebites
    for t in (-1, 1):
        caixa_de(p.b('vagao'), (XT - xw, t * 1.38 - 0.012, DECK - 0.01), (XT + xw, t * 1.38 + 0.012, PAREDE))
        caixa_de(p.b('aco'), (XT - xw - 0.01, t * 1.38 - 0.015, PAREDE - 0.02), (XT + xw + 0.01, t * 1.38 + 0.015, PAREDE + 0.01))
        caixa_de(p.b('grafite'), (XT - 0.05, t * ey, 0.26), (XT + 0.05, t * (ey + 0.1), 0.32))                      # engate
        cil(p.b('aco', True), Vector((XT, t * (ey + 0.12), 0.29)), 0.045, 0.05, Y, 12)
        for s in (-1, 1):
            cil(p.b('aco', True), Vector((XT + s * 0.27, t * (ey + 0.04), 0.30)), 0.03, 0.08, Y, 12)              # para-choques
            cil(p.b('ferro', True), Vector((XT + s * 0.27, t * (ey + 0.085), 0.30)), 0.05, 0.014, Y, 16)
    # remendos, amassados, painel trocado, número de série, pó escorrendo
    remendo(p, (XT + xw + 0.006, -0.58, 0.62), Y, Z, 0.20, 0.14, X)
    remendo(p, (XT - xw - 0.006, 0.29, 0.5), -Y, Z, 0.20, 0.12, -X)
    caixa_de(p.b('primer'), (XT + xw + 0.003, 0.15, DECK + 0.02), (XT + xw + 0.008, 0.42, PAREDE - 0.04))
    amassado(p.b('vagao', True), (XT + xw + 0.0035, 1.0, 0.56), Y, Z, 0.26, 0.3, 0.012, ((0.1, -0.1, 0.18), (-0.25, 0.2, 0.12)))
    estencil('KX-114  CARGA 32t', p, (XT + xw + 0.004, -1.0, 0.70), X, Z, 0.035)
    estencil('0 7 7 3', p, (XT - xw - 0.012, -0.9, 0.70), -X, Z, 0.04)
    bm = p.b('po')
    for (y, r) in ((-0.3, 0.15), (0.1, 0.12), (-0.9, 0.1)):
        amassado(bm, (XT + xw + 0.0052, y, PAREDE - 0.12), Y, Z, r, 0.2, 0.0, ())
    # carga: monte de minério na metade sul, pilhas de chapa na norte
    bm = bmesh.new()
    n = 22
    vs = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x = XT - 0.35 + 0.70 * i / n
            y = -1.36 + 1.70 * j / n
            vs[i, j] = bm.verts.new((x, y, monte(x, y) - 0.02))
    for i in range(n):
        for j in range(n):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    for v in bm.verts:
        v.co.z += random.uniform(-0.01, 0.01) if v.co.z > DECK else 0
    o = novo_obj('monte', bm, 'po', raiz.e, chanfro=False)
    bm = p.b('minerio')
    for _ in range(380):
        x = random.uniform(XT - 0.34, XT + 0.34)
        y = random.uniform(-1.34, 0.30)
        z = monte(x, y)
        if z > DECK + 0.01:
            pedra(bm, (x, y, z - 0.005), random.uniform(0.02, 0.045), 0.7)
    for (px, py, nn) in PILHAS:
        for k in range(nn if (px, py) != (-1.38, 0.80) else nn - 1):
            item_chapas(p, Vector((px, py, DECK + H_CHAPA * (k + 0.5))), PI / 2 + random.uniform(-0.05, 0.05))


def item_chapas(p, c, yaw):
    """Pilha de chapas de ferro amarrada com duas cintas (item 0,10 × 0,18 × 0,08)."""
    rot = Matrix.Rotation(yaw, 3, 'Z')
    for k in range(4):
        caixa(p.b('placa'), c + Vector((0, 0, -0.03 + k * 0.02)), (0.10 - 0.004 * (k % 2), 0.18 - 0.003 * k, 0.017), rot)
    for t in (-0.05, 0.05):
        caixa(p.b('aco'), c + rot @ Vector((0, t, 0)), (0.104, 0.012, 0.084), rot)


# =================================================================== pórtico em balanço e cobertura
YP = (-1.30, 1.30)
XC_O, XC_L = -0.86, 0.84          # colunas oeste e leste
Z_VIGA = 1.92                     # centro das vigas (altura 0,12)
X_PONTA = -1.97


def portico(p):
    for y in YP:
        for x in (XC_O, XC_L):
            perfil_I(p.b('amarelo'), (x, y, Z0), (x, y, Z_VIGA - 0.06), 0.12, 0.10, Y)
            caixa_de(p.b('aco'), (x - 0.11, y - 0.11, Z0), (x + 0.11, y + 0.11, Z0 + 0.016))      # placa de base
            for dx in (-0.08, 0.08):
                for dy in (-0.08, 0.08):
                    cil(p.b('ferro'), Vector((x + dx, y + dy, Z0 + 0.024)), 0.012, 0.016, Z, 6)
                    cil(p.b('aco'), Vector((x + dx, y + dy, Z0 + 0.04)), 0.006, 0.02, Z, 6)
            caixa_de(p.b('listras'), (x - 0.052, y - 0.062, Z0 + 0.016), (x + 0.052, y + 0.062, Z0 + 0.30))
        perfil_I(p.b('amarelo'), (0.93, y, Z_VIGA), (X_PONTA, y, Z_VIGA), 0.12, 0.09, Z)          # viga em balanço
        for x in (XC_O, XC_L):                                                                  # chapa de ligação
            caixa_de(p.b('aco'), (x - 0.09, y - 0.072, Z_VIGA - 0.2), (x + 0.09, y - 0.062, Z_VIGA + 0.04))
            for dz in (-0.17, -0.11, -0.05):
                for dx in (-0.06, 0.06):
                    cil(p.b('ferro'), Vector((x + dx, y - 0.076, Z_VIGA + dz)), 0.008, 0.01, Y, 6)
        a, b = Vector((XC_O, y, 1.40)), Vector((-1.50, y, Z_VIGA - 0.06))                    # mão-francesa do balanço
        perfil_I(p.b('aco'), a, b, 0.07, 0.06, (b - a).cross(Y), 0.01, 0.007)
        a, b = Vector((XC_L, y, 1.55)), Vector((0.50, y, Z_VIGA - 0.06))
        perfil_I(p.b('aco'), a, b, 0.06, 0.05, (b - a).cross(Y), 0.01, 0.007)
        caixa_de(p.b('aco'), (X_PONTA - 0.004, y - 0.05, Z_VIGA - 0.06), (X_PONTA + 0.006, y + 0.05, Z_VIGA + 0.06))   # tampa
    # vigas longitudinais sobre as colunas e viga do meio (y = 0) em balanço apoiada nelas
    for x in (XC_O, XC_L):
        perfil_I(p.b('amarelo'), (x, -1.30, 1.82), (x, 1.30, 1.82), 0.08, 0.07, Z, 0.01, 0.007)
    perfil_I(p.b('amarelo'), (0.93, 0, Z_VIGA), (X_PONTA, 0, Z_VIGA), 0.12, 0.09, Z)
    perfil_I(p.b('aco'), (X_PONTA + 0.04, -1.30, 1.82), (X_PONTA + 0.04, 1.30, 1.82), 0.08, 0.07, Z, 0.01, 0.007)   # trilho do scanner
    for s in (-1, 1):                                                                          # contraventamento em X no balanço
        viga(p.b('aco'), Vector((-0.95, s * 0.045, 1.95)), Vector((-1.90, s * 1.255, 1.95)), 0.016)
        viga(p.b('aco'), Vector((-0.95, s * 1.255, 1.95)), Vector((-1.90, s * 0.045, 1.95)), 0.016)
    # terças e telhas
    for x in (0.86, 0.43, 0.0, -0.43, -0.86, -1.30, -1.66, -1.96):
        caixa_de(p.b('aco'), (x - 0.025, -1.47, Z_VIGA + 0.06), (x + 0.025, 1.47, Z_VIGA + 0.11))
    telhas = [(-1.50, -0.70, 'chapa', [(-1.86, -1.36, 0.10, 1.0), (0.25, -1.05, 0.07, 2.0)]),
              (-0.76, 0.04, 'chapa', [(-0.45, -0.32, 0.15, 3.0), (-1.2, -0.5, 0.05, 1.5), (0.55, -0.1, 0.06, 4.0)]),
              (-0.02, 0.76, 'chapa_primer', [(-1.6, 0.4, 0.06, 2.2)]),
              (0.72, 1.50, 'chapa', [(-0.9, 1.05, 0.12, 5.0), (-1.92, 0.95, 0.09, 0.2)])]
    for k, (y0, y1, mat, furos) in enumerate(telhas):
        bm = bmesh.new()
        chapa_corrugada(bm, X_PONTA - 0.04, 0.96, y0, y1, Z_VIGA + 0.122 + 0.006 * (k % 2), furos)
        o = novo_obj('telha_%d' % k, bm, mat, raiz.e, suave=True, chanfro=False)
        sd = o.modifiers.new('espessura', 'SOLIDIFY')
        sd.thickness = 0.002
    remendo(p, (0.3, 1.25, Z_VIGA + 0.145), X, Y, 0.22, 0.20, Z)            # remendo sobre um furo antigo
    # cabos e eletrocalha: armário → coluna da viga do meio → balanço
    eletrocalha(p, [(0.62, 0.0, 1.27), (0.62, 0.0, 1.78), (-1.40, 0.0, 1.78)])
    # pó e ferrugem escorrida em pingos sob os furos (manchas no chão)
    bm = p.b('ferrugem_chao')
    for (x, y, r) in ((-0.45, -0.32, 0.12), (0.55, -0.1, 0.05), (-0.9, 1.05, 0.08)):
        if -0.96 < x < 0.96:
            mancha(bm, (x, y), r, Z0 + 0.0016)


def eletrocalha(p, pts):
    """Calha perfurada de cabos (fundo + abas) com feixe dentro e suportes pendurados."""
    pts = [Vector(q) for q in pts]
    for a, b in zip(pts, pts[1:]):
        u = (b - a).normalized()
        w = u.cross(Z if abs(u.z) < 0.9 else X).normalized()
        n = u.cross(w)
        rot = Matrix((w, n, u)).transposed()
        L = (b - a).length
        c = (a + b) / 2
        caixa(p.b('aco'), c - n * 0.025, (0.09, 0.004, L), rot)
        for s in (-1, 1):
            caixa(p.b('aco'), c + w * s * 0.045, (0.004, 0.05, L), rot)
        for k in range(int(L / 0.3)):
            q = a + u * (0.15 + k * 0.3)
            if abs(u.z) < 0.9:
                caixa_de(p.b('ferro'), (q.x - 0.006 + 0 * w.x, q.y - 0.006, q.z - 0.03), (q.x + 0.006, q.y + 0.006, 1.86))
    feixe(p, [pts[0] + Vector((0, 0, -0.03))] + [q + Vector((0, 0, -0.012)) for q in pts[1:]], 0.008,
          ('borracha', 'cabo_laranja', 'borracha', 'fio_azul', 'borracha'), 4)


# =================================================================== funil, balança, calha vibratória
HC = Vector((-0.38, 0.0))
Z_BOCA = 1.0
Z_FUNIL = 1.21
Z_BORDA = 1.45
Z_CHUTE0, Z_CHUTE1 = 0.92, 0.855
X_CHUTE0, X_CHUTE1 = -0.38, -1.33


def z_calha(x):
    return Z_CHUTE0 + (Z_CHUTE1 - Z_CHUTE0) * (x - X_CHUTE0) / (X_CHUTE1 - X_CHUTE0)


def funil(p):
    hx, hy = HC
    h = 0.28
    # caixa reta (paredes de chapa) e tremonha (tronco de pirâmide)
    for s in (-1, 1):
        caixa_de(p.b('amarelo'), (hx - h, hy + s * h - 0.006, Z_FUNIL), (hx + h, hy + s * h + 0.006, Z_BORDA))
        caixa_de(p.b('amarelo'), (hx + s * h - 0.006, hy - h, Z_FUNIL), (hx + s * h + 0.006, hy + h, Z_BORDA))
        caixa_de(p.b('aco'), (hx - h - 0.02, hy + s * (h + 0.012) - 0.012, Z_BORDA - 0.02), (hx + h + 0.02, hy + s * (h + 0.012) + 0.012, Z_BORDA + 0.006))
        caixa_de(p.b('aco'), (hx + s * (h + 0.012) - 0.012, hy - h - 0.02, Z_BORDA - 0.02), (hx + s * (h + 0.012) + 0.012, hy + h + 0.02, Z_BORDA + 0.006))
        caixa_de(p.b('aco'), (hx - h - 0.01, hy + s * (h + 0.01) - 0.01, 1.32), (hx + h + 0.01, hy + s * (h + 0.01) + 0.01, 1.345))
        caixa_de(p.b('aco'), (hx + s * (h + 0.01) - 0.01, hy - h - 0.01, 1.32), (hx + s * (h + 0.01) + 0.01, hy + h + 0.01, 1.345))
    bm = p.b('amarelo')
    r0, r1 = h + 0.006, 0.07
    vs = [bm.verts.new((hx + sx * r, hy + sy * r, z)) for (r, z) in ((r1, Z_BOCA), (r0, Z_FUNIL))
          for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs[3::-1])
    bm.faces.new(vs[4:])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[j + 4], vs[i + 4]))
    for s in (-1, 1):                                                       # costelas na tremonha
        a = Vector((hx + s * 0.18, hy - h - 0.004, Z_FUNIL))
        b = Vector((hx + s * 0.05, hy - 0.075, Z_BOCA + 0.02))
        viga(p.b('aco'), a, b, 0.016)
    # minério dentro (superfície + pedras)
    caixa_de(p.b('po'), (hx - h + 0.007, hy - h + 0.007, Z_FUNIL), (hx + h - 0.007, hy + h - 0.007, 1.33))
    for _ in range(45):
        pedra(p.b('minerio'), (hx + random.uniform(-0.25, 0.25), hy + random.uniform(-0.25, 0.25), 1.335), random.uniform(0.02, 0.04), 0.7)
    # pernas, células de carga, orelhas
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = hx + sx * 0.33, hy + sy * 0.33
            perfil_I(p.b('grafite'), (lx, ly, Z0), (lx, ly, 1.12), 0.09, 0.08, X, 0.01, 0.007)
            caixa_de(p.b('aco'), (lx - 0.07, ly - 0.07, Z0), (lx + 0.07, ly + 0.07, Z0 + 0.012))
            caixa_de(p.b('aco'), (lx - 0.055, ly - 0.055, 1.12), (lx + 0.055, ly + 0.055, 1.132))
            cilz(p.b('cromo', True), (lx, ly, 1.16), 0.034, 0.056, 20)       # célula de carga (tipo coluna)
            cilz(p.b('fio_azul', True), (lx, ly, 1.16), 0.0345, 0.012, 20)
            cil(p.b('borracha', True), Vector((lx + sx * 0.037, ly, 1.16)), 0.007, 0.02, X, 8)    # prensa-cabo
            caixa_de(p.b('aco'), (lx - 0.05, ly - 0.05, 1.188), (lx + 0.05, ly + 0.05, 1.205))     # orelha
            a = Vector((hx + sx * h, hy + sy * h, 1.20))
            viga(p.b('amarelo'), a, Vector((lx, ly, 1.20)), 0.04)
            cunha(p.b('aco'), Vector((hx + sx * h, hy + sy * h, 1.205)), Vector((lx - sx * 0.02, ly - sy * 0.02, 1.205)),
                  Vector((hx + sx * h, hy + sy * h, 1.30)), 0.012, Vector((-sy, sx, 0)))
            caixa_de(p.b('listras'), (lx - 0.048, ly - 0.048, Z0 + 0.012), (lx + 0.048, ly + 0.048, Z0 + 0.22))
            # cabo da célula até a caixa de soma
            pts = bezier((lx + sx * 0.05, ly, 1.16), (lx + sx * 0.09, ly, 1.10), (lx + sx * 0.02, ly - sy * 0.05, 1.0), (lx, ly - sy * 0.055, 0.92), 6)
            mangueira(p.b('borracha', True), pts, 0.005, 8)
    # contraventamento das pernas (sul, norte e leste; oeste fica livre para a calha)
    for (a, b) in (((hx - 0.33, -0.33, 0.2), (hx + 0.33, -0.33, 0.95)), ((hx + 0.33, -0.33, 0.2), (hx - 0.33, -0.33, 0.95)),
                   ((hx - 0.33, 0.33, 0.2), (hx + 0.33, 0.33, 0.95)), ((hx + 0.33, 0.33, 0.2), (hx - 0.33, 0.33, 0.95)),
                   ((hx + 0.33, -0.33, 0.2), (hx + 0.33, 0.33, 0.95)), ((hx + 0.33, 0.33, 0.2), (hx + 0.33, -0.33, 0.95))):
        viga(p.b('aco'), Vector(a), Vector(b), 0.014)
    # caixa de soma com barra de peso (LEDs) na perna sudeste
    cx, cy = hx + 0.33, -0.33 - 0.07
    caixa_de(p.b('grafite'), (cx - 0.06, cy - 0.03, 0.80), (cx + 0.06, cy + 0.02, 0.95))
    for k in range(6):
        caixa_de(p.b('seg%d' % k), (cx - 0.04, cy - 0.032, 0.82 + k * 0.02), (cx + 0.04, cy - 0.029, 0.835 + k * 0.02))
    estencil('W-4 CELULAS', p, (cx, cy - 0.0305, 0.94), -Y, Z, 0.012)
    pts = bezier((cx, cy, 0.80), (cx, cy - 0.02, 0.5), (cx + 0.1, cy - 0.04, Z0 + 0.03), (0.30, -0.25, Z0 + 0.02), 10)
    feixe(p, pts, 0.006, ('borracha', 'fio_azul', 'borracha'), 3)
    # comporta da boca com cilindro pneumático
    caixa_de(p.b('grafite'), (hx - 0.10, hy - 0.10, Z_CHUTE0 + 0.01), (hx + 0.10, hy + 0.10, Z_BOCA))
    caixa_de(p.b('aco'), (hx + 0.10, hy - 0.07, 0.94), (hx + 0.16, hy + 0.07, 0.98))
    cilx(p.b('aco', True), (hx + 0.27, hy, 0.96), 0.03, 0.20, 20)
    cilx(p.b('cromo', True), (hx + 0.135, hy, 0.96), 0.011, 0.07, 12)
    for xx in (hx + 0.175, hx + 0.365):
        cilx(p.b('grafite', True), (xx, hy, 0.96), 0.036, 0.016, 20)
    # calha vibratória: fundo inclinado, abas, saia de borracha, molas, motor vibrador
    a = Vector((X_CHUTE0 - 0.05, 0, Z_CHUTE0))
    b = Vector((X_CHUTE1, 0, Z_CHUTE1))
    u = (b - a).normalized()
    L = (b - a).length
    nrm = Y.cross(u).normalized() * -1
    if nrm.z < 0:
        nrm = -nrm
    rot = Matrix((u, Y, nrm)).transposed()
    c = (a + b) / 2
    caixa(p.b('aco'), c, (L, 0.18, 0.008), rot)
    for s in (-1, 1):
        caixa(p.b('amarelo'), c + Y * s * 0.094 + nrm * 0.035, (L, 0.008, 0.075), rot)
        caixa(p.b('aco'), c + Y * s * 0.094 + nrm * 0.074, (L, 0.03, 0.006), rot)
    caixa(p.b('po'), c + nrm * 0.006 + u * 0.05, (L - 0.12, 0.17, 0.004), rot)
    for k in range(5):
        x = random.uniform(X_CHUTE0 - 0.3, X_CHUTE1 + 0.1)
        pedra(p.b('minerio'), (x, random.uniform(-0.06, 0.06), z_calha(x) + 0.02), random.uniform(0.015, 0.025), 0.7)
    caixa_de(p.b('borracha'), (X_CHUTE1 - 0.006, -0.085, Z_CHUTE1 - 0.06), (X_CHUTE1, 0.085, Z_CHUTE1 + 0.004))   # saia
    xs = -0.80
    zc = z_calha(xs)
    for s in (-1, 1):
        caixa_de(p.b('grafite'), (xs - 0.11, s * 0.13 - 0.02, Z0), (xs + 0.11, s * 0.13 + 0.02, 0.72))
        caixa_de(p.b('aco'), (xs - 0.13, s * 0.13 - 0.04, 0.72), (xs + 0.13, s * 0.13 + 0.04, 0.735))
        caixa_de(p.b('aco'), (xs - 0.12, s * 0.13 - 0.04, Z0), (xs + 0.12, s * 0.13 + 0.04, Z0 + 0.012))
        for dx in (-0.08, 0.08):
            mola(p.b('cromo', True), (xs + dx, s * 0.13, 0.735), zc - 0.004 - 0.735, 0.025, 0.005, 4)
            caixa_de(p.b('aco'), (xs + dx - 0.03, s * 0.088, zc - 0.012), (xs + dx + 0.03, s * 0.16, zc - 0.003))
        caixa_de(p.b('listras'), (xs - 0.112, s * 0.13 - 0.022, Z0 + 0.012), (xs + 0.112, s * 0.13 + 0.022, Z0 + 0.2))
    caixa_de(p.b('aco'), (xs - 0.03, -0.09, zc - 0.07), (xs + 0.03, 0.09, zc - 0.004))
    cily(p.b('grafite', True), (xs, 0, zc - 0.095), 0.045, 0.16, 20)
    aletas(p.b('grafite', True), (xs, -0.06, zc - 0.095), Y, 0.052, 6, 0.024, 0.005)
    cily(p.b('primer', True), (xs, 0.088, zc - 0.095), 0.048, 0.02, 20)    # tampa trocada
    pts = bezier((xs, -0.09, zc - 0.095), (xs, -0.16, zc - 0.12), (xs + 0.05, -0.2, Z0 + 0.05), (xs + 0.25, -0.2, Z0 + 0.012), 8)
    mangueira(p.b('cabo_laranja', True), pts, 0.009)
    # pó escorrendo na calha e borda
    remendo(p, (hx, hy - h - 0.012, 1.26), X, Z, 0.16, 0.08, -Y)
    estencil('TREMONHA 2  - 4 t', p, (hx + 0.06, hy - h - 0.0065, 1.40), -Y, Z, 0.022)
    amassado(p.b('amarelo', True), (hx + h + 0.0065, hy + 0.1, 1.38), Y, Z, 0.16, 0.1, 0.006, ((0.1, 0.0, 0.25),))
    fiacao(p, (hx + 0.33 + 0.05, -0.33, 0.70), Vector((0.04, 0.0, -0.02)), (hx + 0.33 + 0.05, -0.31, 0.64))


# =================================================================== campo, scanner, sensores, sinais
CAMPO_C = Vector((XT, 0.0, 1.45))


def campo(p):
    c = CAMPO_C
    anel(p.b('aco', True), c, 0.22, 0.026, Z, 48, 10)
    anel(p.b('bobina_campo', True), c + Vector((0, 0, -0.03)), 0.205, 0.012, Z, 48, 8)
    for k in range(12):                                                     # bobinas enroladas no anel
        a = k * 2 * PI / 12
        d = Vector((math.cos(a), math.sin(a), 0))
        for j in range(3):
            anel(p.b('cobre', True), c + d * 0.22 + d.cross(Z) * (j - 1) * 0.012, 0.031, 0.004, d.cross(Z), 16, 6)
    for s in (-1, 1):                                                       # tirantes até a viga do meio
        a = c + Vector((s * 0.22, 0, 0.02))
        tubo(p.b('aco'), a, Vector((a.x, 0, Z_VIGA - 0.06)), 0.009, 8)
        caixa_de(p.b('aco'), (a.x - 0.03, -0.03, a.z - 0.01), (a.x + 0.03, 0.03, a.z + 0.03))
        caixa_de(p.b('aco'), (a.x - 0.05, -0.05, Z_VIGA - 0.075), (a.x + 0.05, 0.05, Z_VIGA - 0.06))
    caixa_de(p.b('grafite'), (c.x - 0.08, -0.06, 1.66), (c.x + 0.08, 0.06, Z_VIGA - 0.06))   # caixa de potência
    cil(p.b('nucleo'), Vector((c.x, -0.061, 1.76)), 0.018, 0.004, Y, 16)
    pts = bezier((c.x + 0.05, 0.0, 1.66), (c.x + 0.12, 0.02, 1.58), (c.x + 0.22, 0.02, 1.52), (c.x + 0.22, 0.0, 1.475), 6)
    mangueira(p.b('cabo_laranja', True), pts, 0.009)
    # cone do campo (transparente)
    bm = bmesh.new()
    n, m = 48, 10
    aneis_ = []
    for j in range(m + 1):
        t = j / m
        z = c.z - 0.03 - t * (c.z - 0.03 - 0.62)
        R = 0.20 + 0.10 * t
        aneis_.append([bm.verts.new((c.x + R * math.cos(2 * PI * i / n), c.y + R * math.sin(2 * PI * i / n), z)) for i in range(n)])
    for j in range(m):
        for i in range(n):
            k = (i + 1) % n
            bm.faces.new((aneis_[j][i], aneis_[j][k], aneis_[j + 1][k], aneis_[j + 1][i]))
    o = novo_obj('campo', bm, 'campo', raiz.e, suave=False, chanfro=False)
    for pg in o.data.polygons:
        pg.use_smooth = True
    o.visible_shadow = False
    luz = bpy.data.lights.new('luz_campo', 'POINT')
    luz.color = (0.55, 0.2, 1.0)
    luz.energy = 25
    luz.shadow_soft_size = 0.2
    lo = bpy.data.objects.new('luz_campo', luz)
    COL.objects.link(lo)
    lo.location = (c.x, 0, 1.1)
    return luz


def sensores(p):
    """Sensores laser de chegada do trem (sob as vigas em balanço) e sinais de linha nas pontas."""
    lasers = []
    for y in YP:
        x = -1.62
        caixa_de(p.b('grafite'), (x - 0.04, y - 0.035, Z_VIGA - 0.16), (x + 0.04, y + 0.035, Z_VIGA - 0.06))
        caixa_de(p.b('amarelo'), (x - 0.042, y - 0.037, Z_VIGA - 0.11), (x + 0.042, y + 0.037, Z_VIGA - 0.095))
        cilz(p.b('ferro', True), (x, y, Z_VIGA - 0.17), 0.02, 0.02, 16)
        cilz(p.b('laser', True), (x, y, Z_VIGA - 0.181), 0.012, 0.002, 16)
        zf = topo_carga(x, y)
        tubo(p.b('laser'), (x, y, zf), (x, y, Z_VIGA - 0.18), 0.0025, 8)
        cil(p.b('laser'), Vector((x, y, zf + 0.001)), 0.012, 0.002, Z, 12)
        pts = bezier((x + 0.04, y, Z_VIGA - 0.1), (x + 0.12, y, Z_VIGA - 0.1), (x + 0.2, y, Z_VIGA - 0.08), (x + 0.3, y, Z_VIGA - 0.065), 5)
        mangueira(p.b('borracha', True), pts, 0.006, 8)
        # sinal de linha pendurado na ponta, virado para quem chega
        s = 1 if y > 0 else -1
        yy = y + s * 0.12
        xs_ = X_PONTA + 0.04
        tubo(p.b('aco'), (xs_, y + s * 0.02, Z_VIGA - 0.06), (xs_, yy, Z_VIGA - 0.06), 0.012, 8)
        tubo(p.b('aco'), (xs_, yy, Z_VIGA - 0.06), (xs_, yy, 1.62), 0.012, 8)
        caixa_de(p.b('grafite'), (xs_ - 0.05, yy - 0.04, 1.28), (xs_ + 0.05, yy + 0.04, 1.62))
        for k, mat in enumerate(('sinal_vermelho', 'sinal_ambar', 'sinal_verde')):
            zl = 1.56 - k * 0.11
            cil(p.b(mat), Vector((xs_, yy + s * 0.041, zl)), 0.03, 0.006, Y, 20)
            caixa_de(p.b('grafite'), (xs_ - 0.04, yy + s * 0.04 if s > 0 else yy - 0.1, zl + 0.03),
                     (xs_ + 0.04, yy + 0.1 if s > 0 else yy - 0.04, zl + 0.036))                    # pala
        lasers.append((x, y))
    return lasers


def scanner():
    """Carro do scanner que corre no trilho da ponta do balanço; leque de luz violeta sobre a carga."""
    sc_ = Parte('scanner', raiz, (X_PONTA + 0.04, 0, 1.73))
    c = sc_.pivo
    caixa_de(sc_.b('grafite'), (c.x - 0.05, -0.07, 1.69), (c.x + 0.07, 0.07, 1.775))
    for t in (-1, 1):                                                              # trole: chapas e rodinhas na mesa inferior
        caixa_de(sc_.b('aco'), (c.x + t * 0.042 - 0.004, -0.07, 1.775), (c.x + t * 0.042 + 0.004, 0.07, 1.815))
        for s in (-1, 1):
            cilx(sc_.b('aco', True), (c.x + t * 0.025, s * 0.05, 1.802), 0.012, 0.012, 12)
            cilx(sc_.b('cromo', True), (c.x + t * 0.034, s * 0.05, 1.802), 0.004, 0.018, 8)
    cil(sc_.b('ferro', True), Vector((c.x + 0.07, 0, 1.70)), 0.03, 0.05, Vector((1, 0, -0.8)), 20)
    cil(sc_.b('scan', True), Vector((c.x + 0.09, 0, 1.684)), 0.022, 0.006, Vector((1, 0, -0.8)), 20)
    caixa_de(sc_.b('primer'), (c.x - 0.051, -0.06, 1.70), (c.x - 0.049, 0.06, 1.76))
    pts = bezier((c.x - 0.05, 0.06, 1.75), (c.x - 0.1, 0.1, 1.7), (c.x - 0.06, 0.3, 1.66), (c.x - 0.02, 0.5, 1.76), 8)
    mangueira(sc_.b('cabo_laranja', True), pts, 0.007)                             # cabo arrastado (loop solto)
    sc_.fechar()
    raios = []
    for k in range(7):
        bm = bmesh.new()
        cil(bm, Vector((0, 0, -0.5)), 0.0022, 1.0, Z, 6)
        o = novo_obj('raio_%d' % k, bm, 'scan', raiz.e, chanfro=False)
        o.visible_shadow = False
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0)), 0.011, 0.002, Z, 10)
        ponto = novo_obj('ponto_%d' % k, bm, 'scan', raiz.e, chanfro=False)
        raios.append((o, ponto, -1.80 + 0.6 * k / 6))
    return sc_, raios


# =================================================================== armário da IA, antena, farol, sinaleiro
def armario(p):
    x0, x1, y0, y1 = 0.30, 0.78, -0.32, 0.32
    caixa_de(p.b('grafite'), (x0 - 0.01, y0 - 0.01, Z0), (x1 + 0.01, y1 + 0.01, Z0 + 0.06))
    v = caixa_de(p.b('grafite'), (x0, y0, Z0 + 0.06), (x1, y1, 1.25))
    caixa_de(p.b('amarelo'), (x0 - 0.002, y0 - 0.002, 1.12), (x1 + 0.002, y1 + 0.002, 1.15))
    # painéis aparafusados no leste (um trocado, outra cor) e venezianas
    for k, (ya, yb, mat) in enumerate(((-0.30, -0.01, 'grafite'), (0.01, 0.30, 'primer'))):
        caixa_de(p.b(mat), (x1, ya, 0.15), (x1 + 0.008, yb, 1.08))
        for (yy, zz) in ((ya + 0.02, 0.17), (yb - 0.02, 0.17), (ya + 0.02, 1.06), (yb - 0.02, 1.06), (ya + 0.02, 0.6), (yb - 0.02, 0.6)):
            cil(p.b('aco'), Vector((x1 + 0.011, yy, zz)), 0.007, 0.006, X, 6)
    for k in range(9):
        caixa(p.b('aco'), (x1 + 0.014, -0.155, 0.30 + k * 0.035), (0.012, 0.22, 0.004), Matrix.Rotation(-0.6, 3, 'Y'))
    # janela do núcleo (violeta) atrás de grade, LEDs
    cil(p.b('ferro', True), Vector((x1 + 0.012, 0.155, 0.82)), 0.095, 0.012, X, 32)
    cil(p.b('nucleo', True), Vector((x1 + 0.016, 0.155, 0.82)), 0.08, 0.006, X, 32)
    for k in range(5):
        caixa(p.b('aco'), (x1 + 0.022, 0.155, 0.82 + (k - 2) * 0.03), (0.004, 0.17, 0.006))
    for k in range(6):
        cil(p.b('led' if k % 2 == 0 else 'led_violeta'), Vector((x1 + 0.009, 0.06 + k * 0.035, 0.55)), 0.007, 0.006, X, 10)
    # dissipador no norte, prensa-cabos em cima, feixes saindo para os braços pela base
    for k in range(10):
        caixa_de(p.b('aluminio'), (x0 + 0.04 + k * 0.04, y1, 0.3), (x0 + 0.046 + k * 0.04, y1 + 0.05, 0.95))
    caixa_de(p.b('ferro'), (x0 + 0.04, y1, 0.32), (x1 - 0.04, y1 + 0.008, 0.93))
    for k in range(4):
        cilz(p.b('borracha', True), (0.56 + (k % 2) * 0.06, -0.03 + (k // 2) * 0.06, 1.265), 0.016, 0.03, 12)
    for s in (-1, 1):
        pts = bezier((x0, s * 0.20, Z0 + 0.12), (0.1, s * 0.45, Z0 + 0.012), (-0.2, s * 0.5, Z0 + 0.012), (-0.415, s * 0.80, Z0 + 0.15), 14)
        feixe(p, pts, 0.008, ('borracha', 'cabo_laranja', 'borracha', 'fio_vermelho'), 3)
    # antena (mastro, yagi, prato) e farol âmbar giratório
    ax, ay = 0.70, 0.22
    cilz(p.b('aco', True), (ax, ay, 1.52), 0.012, 0.54, 12)
    cilz(p.b('grafite', True), (ax, ay, 1.27), 0.03, 0.04, 16)
    for k in range(5):
        cilx(p.b('aluminio', True), (ax, ay, 1.55 + k * 0.045), 0.003, 0.16 - k * 0.02, 8)
    cil(p.b('aluminio', True), Vector((ax - 0.045, ay, 1.36)), 0.07, 0.01, Vector((-1, 0, 0.5)), 24, )
    cil(p.b('grafite', True), Vector((ax - 0.022, ay, 1.37)), 0.012, 0.04, Vector((-1, 0, 0.5)), 10)
    cilz(p.b('led', True), (ax, ay, 1.80), 0.008, 0.012, 10)
    fiacao(p, (x1, -0.31, 1.10), Vector((0.05, -0.02, 0.0)), (x1 - 0.06, -0.32, 0.98))
    remendo(p, (x0 + 0.12, y0 - 0.002, 0.85), X, Z, 0.14, 0.12, -Y)
    estencil('IA-NUCLEO  ESTACAO 07', p, (x1 + 0.0085, -0.155, 0.95), X, Z, 0.022)
    estencil('3 3 0 1 - B', p, (0.55, y0 - 0.002, 0.30), -Y, Z, 0.03)
    # farol
    fx, fy = 0.40, -0.20
    cilz(p.b('grafite', True), (fx, fy, 1.265), 0.05, 0.03, 20)
    farol = Parte('farol', raiz, (fx, fy, 1.30))
    cilz(farol.b('farol_luz', True), (fx, fy, 1.30), 0.012, 0.05, 10)
    caixa_de(farol.b('aco'), (fx - 0.004, fy - 0.03, 1.285), (fx + 0.004, fy + 0.03, 1.33))
    caixa_de(farol.b('farol_luz'), (fx + 0.004, fy - 0.025, 1.29), (fx + 0.006, fy + 0.025, 1.325))
    farol.fechar()
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=0.045, matrix=Matrix.Translation((fx, fy, 1.30)))
    for v in bm.verts:
        if v.co.z < 1.28:
            v.co.z = 1.28
    o = novo_obj('cupula', bm, 'farol', raiz.e, chanfro=False)
    suavizar(o)
    sl = bpy.data.lights.new('luz_farol', 'SPOT')
    sl.color = (1.0, 0.5, 0.08)
    sl.energy = 30
    sl.spot_size = math.radians(40)
    slo = bpy.data.objects.new('luz_farol', sl)
    COL.objects.link(slo)
    slo.parent = farol.e
    slo.location = (0, 0, 0)
    slo.rotation_euler = (0, math.radians(100), 0)
    return farol


def sinaleiro(p):
    """Torre de luz na coluna leste do quadro sul (verde, âmbar, vermelho)."""
    x, y = XC_L + 0.06, -1.30
    caixa_de(p.b('aco'), (x, y - 0.03, 1.20), (x + 0.06, y + 0.03, 1.22))
    for k, mat in enumerate(('sinal_verde', 'sinal_ambar', 'sinal_vermelho')):
        cilz(p.b(mat, True), (x + 0.04, y, 1.25 + k * 0.055), 0.028, 0.05, 20)
        cilz(p.b('grafite', True), (x + 0.04, y, 1.2775 + k * 0.055), 0.03, 0.005, 20)
    cilz(p.b('grafite', True), (x + 0.04, y, 1.42), 0.03, 0.025, 20)


# =================================================================== ar comprimido
def ar_comprimido(p):
    tx, ty = 0.62, 0.60
    cilz(p.b('primer', True), (tx, ty, 0.45), 0.10, 0.56, 32)
    for zz in (0.17, 0.73):
        bmesh.ops.create_uvsphere(p.b('primer', True), u_segments=32, v_segments=12, radius=0.1,
                                  matrix=Matrix.Translation((tx, ty, zz)) @ Matrix.Diagonal((1, 1, 0.45, 1)))
    for k in range(3):                                                      # pés
        a = k * 2 * PI / 3 + 0.4
        viga(p.b('grafite'), Vector((tx + math.cos(a) * 0.07, ty + math.sin(a) * 0.07, 0.17)),
             Vector((tx + math.cos(a) * 0.11, ty + math.sin(a) * 0.11, Z0)), 0.02)
    cilz(p.b('cromo', True), (tx, ty, 0.80), 0.014, 0.05, 12)               # válvula de segurança
    cil(p.b('grafite', True), Vector((tx + 0.1, ty, 0.6)), 0.016, 0.04, X, 12)   # transdutor de pressão
    pts = bezier((tx + 0.12, ty, 0.6), (tx + 0.18, ty, 0.6), (0.68, 0.36, 0.9), (0.68, 0.32, 0.95), 8)
    mangueira(p.b('borracha', True), pts, 0.006, 8)
    caixa_de(p.b('oleo'), (tx - 0.01, ty - 0.101, 0.2), (tx + 0.015, ty - 0.099, 0.42))   # óleo escorrendo
    # compressor (motor aletado + cabeçote) no skid ao lado
    caixa_de(p.b('grafite'), (0.74, 0.46, Z0), (0.94, 0.74, Z0 + 0.04))
    cilx(p.b('grafite', True), (0.84, 0.66, 0.16), 0.06, 0.16, 24)
    aletas(p.b('grafite', True), (0.77, 0.66, 0.16), X, 0.07, 7, 0.022, 0.005)
    caixa_de(p.b('aco'), (0.78, 0.48, 0.09), (0.90, 0.56, 0.25))
    for k in range(4):
        caixa_de(p.b('aluminio'), (0.78, 0.48 + k * 0.02, 0.25), (0.90, 0.488 + k * 0.02, 0.29))
    cano(p, [(0.84, 0.52, 0.29), (0.84, 0.52, 0.34), (0.72, 0.60, 0.34)], 0.012, 'cobre')
    # linha principal até o funil (flanges nos trechos)
    linha = [(0.52, ty, 0.30), (0.46, ty, 0.30), (0.46, ty, 0.12), (0.06, ty, 0.12), (0.06, 0.40, 0.12), (0.06, 0.40, 1.38),
             (-0.50, 0.40, 1.38), (-0.50, 0.33, 1.38)]
    cano(p, linha, 0.02, 'aco', flanges=(3, 5, 6))
    for x in (0.36, 0.2):                                                   # selas de apoio no chão
        caixa_de(p.b('ferro'), (x - 0.02, ty - 0.03, Z0), (x + 0.02, ty + 0.03, 0.10))
    for zz in (0.5, 0.9):                                                   # braçadeiras na perna do funil
        caixa_de(p.b('aco'), (-0.05, 0.37, zz - 0.01), (0.07, 0.43, zz + 0.01))
    # canhões de ar na parede norte do funil
    for x in (-0.25, -0.50):
        cil(p.b('grafite', True), Vector((x, 0.36, 1.30)), 0.05, 0.10, Y, 20)
        cil(p.b('aco', True), Vector((x, 0.30, 1.30)), 0.015, 0.03, Y, 12)
        cil(p.b('aco', True), Vector((x, 0.36, 1.355)), 0.012, 0.03, Z, 12)
    cano(p, [(-0.25, 0.40, 1.38), (-0.25, 0.36, 1.38), (-0.25, 0.36, 1.355)], 0.012, 'aco')
    # derivação até a comporta
    cano(p, [(0.06, 0.40, 0.96), (0.06, 0.12, 0.96), (0.06, 0.0, 0.96), (HC.x + 0.38, 0.0, 0.96)], 0.012, 'aco', flanges=(1,))


# =================================================================== esteiras (leste)
def esteira_ew(p, y, x0, x1, motor_x, nome):
    """Esteira leste–oeste de x0 a x1 (topo da lona = TOPO). Rolos giram (partes)."""
    for s in (-1, 1):
        caixa_de(p.b('grafite'), (x0, y + s * 0.2 - 0.015, 0.135), (x1, y + s * 0.2 + 0.015, 0.235))
    n = max(2, int((x1 - x0) / 0.4))
    for k in range(n + 1):
        x = x0 + 0.06 + (x1 - x0 - 0.12) * k / n
        for s in (-1, 1):
            caixa_de(p.b('aco'), (x - 0.015, y + s * 0.2 - 0.015, Z0 if x < 0.96 else 0.0), (x + 0.015, y + s * 0.2 + 0.015, 0.135))
        caixa_de(p.b('aco'), (x - 0.01, y - 0.19, 0.05 + Z0), (x + 0.01, y + 0.19, 0.07 + Z0))
    caixa_de(p.b('borracha'), (x0 + 0.02, y - 0.175, 0.208), (x1 - 0.02, y + 0.175, TOPO))
    caixa_de(p.b('borracha'), (x0 + 0.02, y - 0.175, 0.158), (x1 - 0.02, y + 0.175, 0.166))
    for xx in (x0 + 0.02, x1 - 0.02):
        cily(p.b('borracha', True), (xx, y, 0.19), 0.03, 0.35, 20)
    cily(p.b('grafite', True), (motor_x, y - 0.27, 0.19), 0.045, 0.09, 20)
    cily(p.b('amarelo', True), (motor_x, y - 0.32, 0.19), 0.03, 0.02, 16)
    rolos = []
    nr = int((x1 - x0) / 0.15)
    for k in range(1, nr):
        x = x0 + (x1 - x0) * k / nr
        r = Parte('%s_rolo_%d' % (nome, k), raiz, (x, y, 0.19))
        cily(r.b('cromo', True), (x, y, 0.19), 0.017, 0.37, 16)
        caixa_de(r.b('aco'), (x - 0.017, y - 0.15, 0.188), (x + 0.017, y - 0.13, 0.192))     # marca para ver girar
        r.fechar()
        rolos.append(r)
    return rolos


# =================================================================== braço (estilo do aprovado, sobre pedestal)
L1, L2 = 0.55, 0.62
ZP = Z0 + 0.38                        # topo do pedestal
ZG = ZP + 0.225
SZ = ZG + 0.145
A_REL = Vector((0, -0.155, -0.06))    # olhal da camisa no giro, relativo ao ombro
P0_REL = Vector((0, -0.045, 0.264))   # olhal da haste no braço 1 (em repouso, vertical)


def ik(r, z):
    zr = z - SZ
    d = min(math.hypot(r, zr), L1 + L2 - 1e-4)
    c2 = (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q = math.acos(max(-1, min(1, c2)))
    f1 = math.atan2(zr, r) + math.atan2(L2 * math.sin(q), L1 + L2 * math.cos(q))
    return f1, f1 - q


def ponto_piston(a1):
    y = P0_REL.y * math.cos(a1) - P0_REL.z * math.sin(a1)
    z = P0_REL.y * math.sin(a1) + P0_REL.z * math.cos(a1)
    return Vector((0, y, z))


def braco(nome, O, dmin, dmax):
    O = Vector(O)
    S = Vector((O.x, O.y, SZ))
    E = S + Vector((0, 0, L1))
    W = E + Vector((0, L2, 0))
    base = Parte(nome + '_base', raiz, (O.x, O.y, ZP))
    # pedestal com mãos-francesas, faixa de perigo, chumbadores
    caixa_de(base.b('amarelo'), (O.x - 0.18, O.y - 0.18, Z0), (O.x + 0.18, O.y + 0.18, ZP - 0.02))
    caixa_de(base.b('aco'), (O.x - 0.22, O.y - 0.22, Z0), (O.x + 0.22, O.y + 0.22, Z0 + 0.02))
    caixa_de(base.b('aco'), (O.x - 0.2, O.y - 0.2, ZP - 0.02), (O.x + 0.2, O.y + 0.2, ZP))
    caixa_de(base.b('listras'), (O.x - 0.1815, O.y - 0.1815, Z0 + 0.02), (O.x + 0.1815, O.y + 0.1815, Z0 + 0.12))
    for k in range(4):
        d = Vector((math.cos(k * PI / 2), math.sin(k * PI / 2), 0))
        t = d.cross(Z)
        cunha(base.b('aco'), O.to_3d() * 0 + Vector((O.x, O.y, Z0 + 0.02)) + d * 0.18, Vector((O.x, O.y, Z0 + 0.02)) + d * 0.22,
              Vector((O.x, O.y, Z0 + 0.25)) + d * 0.18, 0.012, t)
        for s in (-1, 1):
            cil(base.b('ferro'), Vector((O.x, O.y, Z0 + 0.03)) + d * 0.2 + t * s * 0.15, 0.012, 0.02, Z, 6)
    remendo(base, (O.x + 0.0, O.y - 0.182, 0.30), X, Z, 0.16, 0.10, -Y)
    estencil('BR-%s 2207' % nome.upper()[:1], base, (O.x + 0.1815, O.y, 0.30), X, Z, 0.022)
    # base do braço (aprovado): plinto octogonal, anel, parafusos, coluna, anel coletor, caixa de ligação
    cil(base.b('grafite'), Vector((O.x, O.y, ZP + 0.03)), 0.26, 0.06, Z, 8)
    cil(base.b('aco'), Vector((O.x, O.y, ZP + 0.075)), 0.22, 0.03, Z, 8)
    parafusos(base.b('cromo'), (O.x, O.y, 0), 0.19, 8, 0.014, 0.012, ZP + 0.09, PI / 8)
    cilz(base.b('aco', True), (O.x, O.y, ZP + 0.155), 0.13, 0.13, 32)
    cilz(base.b('grafite', True), (O.x, O.y, ZG - 0.01), 0.145, 0.02, 32)
    caixa_de(base.b('grafite'), (O.x + 0.14, O.y - 0.16, ZP + 0.09), (O.x + 0.22, O.y - 0.08, ZP + 0.16))
    caixa_de(base.b('amarelo'), (O.x + 0.15, O.y - 0.15, ZP + 0.16), (O.x + 0.21, O.y - 0.09, ZP + 0.172))
    pts = bezier((O.x + 0.15, O.y - 0.12, ZP + 0.13), (O.x + 0.13, O.y - 0.07, ZP + 0.15), (O.x + 0.12, O.y - 0.03, ZP + 0.19), (O.x + 0.13, O.y, ZP + 0.205), 6)
    mangueira(base.b('borracha', True), pts, 0.011)
    # mangueiras hidráulicas do pedestal ao giro (lado leste)
    pts = bezier((O.x + 0.18, O.y + 0.05, Z0 + 0.2), (O.x + 0.24, O.y + 0.05, ZP - 0.05), (O.x + 0.2, O.y + 0.06, ZP + 0.12), (O.x + 0.135, O.y + 0.05, ZP + 0.18), 8)
    mangueira(base.b('borracha', True), pts, 0.012)
    abracadeiras(base.b('aco', True), pts, 0.012, 2)
    # ---------------------------------------------------------- giro
    giro = Parte(nome + '_giro', base, (O.x, O.y, ZG))
    caixa_de(giro.b('amarelo'), (O.x - 0.13, O.y - 0.13, ZG), (O.x + 0.13, O.y + 0.13, ZG + 0.11))
    caixa_de(giro.b('grafite'), (O.x - 0.10, O.y - 0.10, ZG + 0.11), (O.x + 0.10, O.y + 0.06, ZG + 0.14))
    cilx(giro.b('aco', True), (O.x - 0.17, O.y, ZG + 0.055), 0.055, 0.10, 24)
    aletas(giro.b('grafite', True), (O.x - 0.205, O.y, ZG + 0.055), X, 0.066, 4, 0.024, 0.008)
    cilx(giro.b('cobre', True), (O.x - 0.23, O.y, ZG + 0.055), 0.03, 0.02, 16)
    for x in (-0.085, 0.085):
        caixa_de(giro.b('aco'), (O.x + x - 0.0175, O.y - 0.055, ZG + 0.11), (O.x + x + 0.0175, O.y + 0.055, SZ + 0.05))
        cilx(giro.b('cromo', True), (O.x + x * 1.25, O.y, SZ), 0.022, 0.012, 6)
    caixa_de(giro.b('grafite'), (O.x + 0.065, O.y - 0.135, ZG + 0.08), (O.x + 0.135, O.y - 0.085, ZG + 0.13))   # bloco de válvulas
    for k in range(2):
        cilz(giro.b('cobre', True), (O.x + 0.085 + 0.03 * k, O.y - 0.11, ZG + 0.14), 0.012, 0.02, 8)
    A = S + A_REL
    for s in (-1, 1):
        caixa_de(giro.b('aco'), (A.x + s * 0.035 - 0.008, A.y - 0.03, ZG + 0.03), (A.x + s * 0.035 + 0.008, O.y - 0.13, A.z + 0.03))
    cilx(giro.b('cromo', True), A, 0.012, 0.09, 10)
    remendo(giro, (O.x - 0.05, O.y + 0.1315, ZG + 0.06), -X, Z, 0.08, 0.05, Y)
    amassado(giro.b('amarelo', True), (O.x + 0.1315, O.y + 0.03, ZG + 0.06), -Y, Z, 0.1, 0.06, 0.005, ((0.1, 0.1, 0.2),))
    caixa_de(giro.b('oleo'), (O.x + 0.1316, O.y - 0.02, ZG + 0.01), (O.x + 0.1325, O.y + 0.005, ZG + 0.09))
    # ---------------------------------------------------------- braço 1: treliça
    b1 = Parte(nome + '_braco1', giro, S)
    cilx(b1.b('grafite', True), S, 0.045, 0.15, 20)
    for x in (-0.045, 0.045):
        caixa_de(b1.b('cromo' if False else 'aco'), (S.x + x - 0.011, S.y - 0.025, S.z), (S.x + x + 0.011, S.y + 0.025, E.z))
    for k in range(1, 5):
        z = S.z + L1 * k / 5
        caixa_de(b1.b('amarelo'), (S.x - 0.04, S.y - 0.009, z - 0.009), (S.x + 0.04, S.y + 0.009, z + 0.009))
    for k in range(4):
        z0 = S.z + L1 * k / 5 + 0.01
        viga(b1.b('aco'), Vector((S.x - 0.045, S.y + 0.026, z0)), Vector((S.x + 0.045, S.y + 0.026, z0 + L1 / 5 - 0.02)), 0.008)
    P0 = S + P0_REL
    cilx(b1.b('cromo', True), P0, 0.01, 0.112, 10)                           # pino do olhal
    cilx(b1.b('grafite', True), E, 0.058, 0.14, 24)
    for x in (-0.075, 0.075):
        cilx(b1.b('aco', True), (E.x + x, E.y, E.z), 0.04, 0.012, 16)
        cilx(b1.b('cromo', True), (E.x + x * 1.12, E.y, E.z), 0.014, 0.012, 6)
    hose = bezier((S.x + 0.12, S.y - 0.02, S.z + 0.0), (S.x + 0.12, S.y - 0.03, S.z + 0.2), (S.x + 0.08, S.y - 0.02, E.z - 0.25), (S.x + 0.07, E.y - 0.03, E.z - 0.05), 12)
    mangueira(b1.b('borracha', True), hose, 0.014)
    abracadeiras(b1.b('aco', True), hose, 0.014, 3)
    for dx, mat in ((-0.075, 'cobre'), (-0.062, 'borracha')):
        cabo = bezier((S.x + dx, S.y - 0.02, S.z + 0.07), (S.x + dx - 0.01, S.y - 0.02, S.z + 0.2), (S.x + dx, S.y + 0.0, E.z - 0.2), (S.x + dx, E.y - 0.02, E.z - 0.06), 10)
        mangueira(b1.b(mat, True), cabo, 0.006, 8)
    for k in range(1, 4):
        z = S.z + L1 * k / 4
        caixa_de(b1.b('aco'), (S.x - 0.085, S.y - 0.03, z - 0.01), (S.x - 0.056, S.y, z + 0.01))
    estencil('0418-77', b1, (S.x + 0.0565, S.y, E.z - 0.12), X, Z, 0.011)
    # ---------------------------------------------------------- braço 2: viga afilada
    b2 = Parte(nome + '_braco2', b1, E)
    cil(b2.b('amarelo', True), E + Vector((0, L2 / 2, 0)), 0.04, L2, Y, 20, 0.03)
    for k in (0.3, 0.55):
        cilx(b2.b('grafite', True), E + Vector((0, L2 * k, 0)), 0.022, 0.09, 12)
    cily(b2.b('grafite', True), E + Vector((0, 0.08, 0)), 0.045, 0.03, 20)
    caixa_de(b2.b('aco'), (W.x - 0.035, W.y - 0.06, W.z - 0.03), (W.x - 0.025, W.y + 0.02, W.z + 0.03))
    caixa_de(b2.b('aco'), (W.x + 0.025, W.y - 0.06, W.z - 0.03), (W.x + 0.035, W.y + 0.02, W.z + 0.03))
    cabo2 = bezier((E.x + 0.06, E.y + 0.0, E.z - 0.04), (E.x + 0.08, E.y + 0.15, E.z + 0.05), (W.x + 0.07, W.y - 0.25, W.z + 0.06), (W.x + 0.045, W.y - 0.04, W.z + 0.02), 10)
    mangueira(b2.b('borracha', True), cabo2, 0.011)
    abracadeiras(b2.b('aco', True), cabo2, 0.011, 3)
    caixa_de(b2.b('oleo'), (W.x - 0.01, W.y - 0.2, W.z - 0.031), (W.x + 0.01, W.y - 0.05, W.z - 0.0295))
    # ---------------------------------------------------------- garra pneumática
    g = Parte(nome + '_garra', b2, W)
    cilz(g.b('aco', True), (W.x, W.y, W.z - 0.01), 0.045, 0.04, 20)
    cilz(g.b('grafite', True), (W.x, W.y, W.z - 0.035), 0.05, 0.012, 20)
    caixa_de(g.b('grafite'), (W.x - 0.075, W.y - 0.04, W.z - 0.105), (W.x + 0.075, W.y + 0.04, W.z - 0.06))
    caixa_de(g.b('amarelo'), (W.x - 0.076, W.y - 0.041, W.z - 0.075), (W.x + 0.076, W.y + 0.041, W.z - 0.067))
    cilx(g.b('cromo', True), (W.x, W.y + 0.05, W.z - 0.08), 0.016, 0.12, 12)
    cil(g.b('led'), Vector((W.x, W.y - 0.041, W.z - 0.09)), 0.006, 0.004, Y, 10)
    dedos = []
    for s in (-1, 1):
        d = Parte('%s_dedo_%d' % (nome, (s + 1) // 2), g, (W.x + s * 0.06, W.y, W.z - 0.1))
        caixa_de(d.b('aco'), (W.x + s * 0.06 - 0.009, W.y - 0.025, W.z - 0.205), (W.x + s * 0.06 + 0.009, W.y + 0.025, W.z - 0.1))
        caixa_de(d.b('borracha'), (W.x + s * 0.048, W.y - 0.022, W.z - 0.2), (W.x + s * 0.051, W.y + 0.022, W.z - 0.13))
        dedos.append((d, s))
    # ---------------------------------------------------------- pistão: camisa no giro, haste no braço 1
    Ap = A
    d0 = (P0 - Ap)
    th0 = math.atan2(d0.z, d0.y)
    u0 = d0.normalized()
    Lc = dmin - 0.035
    Lh = dmax - Lc + 0.035
    cam = Parte(nome + '_camisa', giro, Ap)
    cil(cam.b('amarelo', True), Ap + u0 * (Lc / 2 + 0.02), 0.028, Lc - 0.04, u0, 20)
    cil(cam.b('grafite', True), Ap + u0 * (Lc - 0.015), 0.034, 0.03, u0, 20)
    cil(cam.b('grafite', True), Ap + u0 * 0.03, 0.032, 0.03, u0, 20)
    cilx(cam.b('grafite', True), Ap, 0.022, 0.06, 16)
    caixa(cam.b('grafite'), Ap + u0 * 0.012, (0.05, 0.03, 0.03))
    pts = bezier(Ap + u0 * 0.035 + Vector((0.03, 0, 0)), Ap + u0 * 0.03 + Vector((0.08, -0.02, 0)), Vector((O.x + 0.1, O.y - 0.1, ZG + 0.17)), Vector((O.x + 0.1, O.y - 0.11, ZG + 0.15)), 6)
    mangueira(cam.b('borracha', True), pts, 0.008, 8)
    has = Parte(nome + '_haste', b1, P0)
    cil(has.b('cromo', True), P0 - u0 * (Lh / 2), 0.013, Lh, u0, 16)
    cilx(has.b('grafite', True), P0, 0.02, 0.07, 16)
    for pt in (base, giro, b1, b2, g, cam, has) + tuple(d for d, _ in dedos):
        pt.fechar()
    return dict(nome=nome, O=O, S=S, base=base, giro=giro, b1=b1, b2=b2, g=g, cam=cam, has=has, dedos=dedos,
                A=Ap, P0=P0, th0=th0)


def posar(B, yaw, f1, f2, aberto, q):
    a1 = f1 - PI / 2
    B['giro'].e.rotation_euler = (0, 0, yaw)
    B['b1'].e.rotation_euler = (a1, 0, 0)
    B['b2'].e.rotation_euler = (f2 - a1, 0, 0)
    B['g'].e.rotation_euler = (-f2, 0, 0)
    P = B['S'] + ponto_piston(a1)
    d = P - B['A']
    th = math.atan2(d.z, d.y)
    B['cam'].e.rotation_euler = (th - B['th0'], 0, 0)
    B['has'].e.rotation_euler = (th - B['th0'] - a1, 0, 0)
    objs = [B['giro'].e, B['b1'].e, B['b2'].e, B['g'].e, B['cam'].e, B['has'].e]
    for dd, s in B['dedos']:
        dd.e.location = dd.pivo - B['g'].pivo + Vector((s * 0.028 * aberto, 0, 0))
        objs.append(dd.e)
    for o in objs:
        chave(o, 'rotation_euler', q)
        chave(o, 'location', q)


# =================================================================== trajetórias
O_SUL = Vector((-0.60, -0.80, 0))
O_NORTE = Vector((-0.60, 0.80, 0))
PEGA_SUL = Vector((0.10, -1.0))                  # ponta da esteira de entrada
SOLTA_SUL = Vector((-0.42, -0.14))               # boca do funil
PEGA_NORTE = Vector((-1.38, 0.80))               # pilha de chapas no vagão
SOLTA_NORTE = Vector((0.12, 1.0))                # ponta da esteira de saída


def polar(O, p):
    d = p - O.to_2d()
    return d.length, math.atan2(-d.x, d.y)


rC, yC = polar(O_SUL, PEGA_SUL)
rH, yH = polar(O_SUL, SOLTA_SUL)
zC = TOPO + 0.05 + GRIP
zH = 1.72
TAB_SUL = [(0.00, rC, zC + 0.12, yC), (0.06, rC, zC, yC), (0.12, rC, zC, yC), (0.19, rC, zC + 0.2, yC),
           (0.31, 0.50, 1.38, (yC + yH) / 2), (0.40, rH, zH, yH), (0.50, rH, zH, yH), (0.60, 0.50, 1.38, (yC + yH) / 2),
           (0.80, rC, zC + 0.2, yC), (1.00, rC, zC + 0.12, yC)]
SEGURA_SUL = (0.09, 0.47)
rW, yW = polar(O_NORTE, PEGA_NORTE)
rP, yP = polar(O_NORTE, SOLTA_NORTE)
zW = DECK + 3 * H_CHAPA - H_CHAPA / 2 + GRIP
zP = TOPO + H_CHAPA / 2 + GRIP
TAB_NORTE = [(0.00, rW, zW + 0.15, yW), (0.06, rW, zW, yW), (0.12, rW, zW, yW), (0.22, 0.70, 1.12, yW),
             (0.33, 0.40, 1.20, 0.6), (0.42, 0.45, 1.0, -0.6), (0.48, rP, zP + 0.12, yP), (0.53, rP, zP, yP),
             (0.58, rP, zP, yP), (0.64, rP, zP + 0.15, yP), (0.74, 0.40, 1.15, -0.6), (0.84, 0.42, 1.2, 0.6),
             (0.93, 0.70, 1.12, yW), (1.00, rW, zW + 0.15, yW)]
SEGURA_NORTE = (0.09, 0.56)
FASE_NORTE = 0.35

# faixa de curso do pistão (para dimensionar camisa e haste)
ds = []
for tab in (TAB_SUL, TAB_NORTE):
    for i in range(200):
        r, z, _ = trajetoria(i / 200, tab)
        f1, f2 = ik(r, z)
        ds.append((ponto_piston(f1 - PI / 2) - A_REL).length)
DMIN, DMAX = min(ds), max(ds)
print('pistão: d %.3f .. %.3f' % (DMIN, DMAX))

# =================================================================== montar a cena
laje_estacao(raiz)
linha(raiz)
vagao(raiz)
portico(raiz)
funil(raiz)
luz_campo = campo(raiz)
LASERS = sensores(raiz)
SCN, RAIOS = scanner()
FAROL = armario(raiz)
sinaleiro(raiz)
ar_comprimido(raiz)
ROLOS_E = esteira_ew(raiz, -1.0, 0.0, 1.55, 1.45, 'ent')
ROLOS_S = esteira_ew(raiz, 1.0, 0.0, 1.55, 1.45, 'sai')
for y in (-1.0, 1.0):                                         # batente na ponta (sensor de presença) e capota no fim
    caixa_de(raiz.b('grafite'), (-0.02, y - 0.2, 0.17), (0.0, y + 0.2, 0.30))
    caixa_de(raiz.b('amarelo'), (-0.021, y - 0.2, 0.26), (0.001, y + 0.2, 0.285))
    cil(raiz.b('led'), Vector((0.002, y + 0.19, 0.25)), 0.006, 0.004, X, 10)
    caixa_de(raiz.b('grafite'), (1.42, y - 0.22, 0.23), (1.58, y + 0.22, 0.42))
    for k in range(7):
        caixa_de(raiz.b('borracha'), (1.415, y - 0.19 + k * 0.055, 0.235), (1.42, y - 0.15 + k * 0.055, 0.40))   # cortina
for zz in (0.0,):
    pass
SUL = braco('sul', O_SUL, DMIN, DMAX)
NORTE = braco('norte', O_NORTE, DMIN, DMAX)
raiz.fechar()


def item_minerio(nome):
    bm = bmesh.new()
    random.seed(42)
    pedra(bm, (0, 0, 0), 0.044, 0.85)
    o = novo_obj(nome, bm, 'minerio', raiz.e)
    return o


def item_placa(nome):
    pp = Parte(nome, raiz, (0, 0, 0))
    item_chapas(pp, Vector((0, 0, 0)), 0.0)
    pp.fechar()
    return pp.e


ENT = [item_minerio('minerio_%d' % k) for k in range(6)]            # R0 (preso) + fila R1..R5
for o in ENT[1:]:
    o.data = ENT[0].data
CAMPO_ITENS = [item_minerio('flutua_%d' % k) for k in range(3)]
for o in CAMPO_ITENS:
    o.data = ENT[0].data
SAI = [item_placa('chapas_%d' % k) for k in range(5)]                # P (preso) + Q1..Q4


# =================================================================== animação
def vis(o, v, q):
    for oo in [o] + list(o.children):
        oo.hide_render = oo.hide_viewport = not v
        chave(oo, 'hide_render', q)
        chave(oo, 'hide_viewport', q)


def pos(o, p, rot, q):
    o.location = p
    o.rotation_euler = rot
    chave(o, 'location', q)
    chave(o, 'rotation_euler', q)


def aberto_de(u, seg):
    a = 1.0 - suave((u - (seg[0] - 0.03)) / 0.03) + suave((u - seg[1]) / 0.03)
    return max(0.0, min(1.0, a))


def ponta(O, r, z, yaw):
    return Vector((O.x - r * math.sin(yaw), O.y + r * math.cos(yaw), z))


def emis(mat, v, q):
    s = M[mat].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    s.default_value = v
    s.keyframe_insert('default_value', frame=q)


onda = M['campo'].node_tree.nodes[M['campo']['onda']]
emc = next(n for n in M['campo'].node_tree.nodes if n.type == 'EMISSION')
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # ---------------- braço sul: esteira → funil
    u = fr
    r, z, yaw = trajetoria(u, TAB_SUL)
    f1, f2 = ik(r, z)
    posar(SUL, yaw, f1, f2, aberto_de(u, SEGURA_SUL), q)
    s_in = suave((u - 0.22) / 0.36)
    ry = Vector((0, 0, 0))
    R0 = ENT[0]
    if u < SEGURA_SUL[0]:
        pos(R0, (PEGA_SUL.x, PEGA_SUL.y, TOPO + 0.045), (0, 0, 0.3), q)
        vis(R0, True, q)
    elif u < SEGURA_SUL[1]:
        pos(R0, ponta(O_SUL, r, z - GRIP, yaw), (0, 0, yaw + 0.3), q)
        vis(R0, True, q)
    else:
        t = suave((u - SEGURA_SUL[1]) / 0.06)
        p0 = ponta(O_SUL, rH, zH - GRIP, yH)
        pos(R0, (p0.x, p0.y, p0.z + (1.36 - p0.z) * t * t), (t * 1.5, 0, yH + 0.3), q)
        vis(R0, u < SEGURA_SUL[1] + 0.07, q)
    for k in range(1, 6):
        x = PEGA_SUL.x + 0.3 * k - 0.3 * s_in
        pos(ENT[k], (x, -1.0, TOPO + 0.045), (0, 0, 0.3 + k * 0.0), q)
        vis(ENT[k], x < 1.40, q)
    for rr in ROLOS_E:
        rr.e.rotation_euler = (0, 0.3 * s_in / 0.017, 0)
        chave(rr.e, 'rotation_euler', q)
    # ---------------- braço norte: vagão → esteira de saída
    un = (fr + FASE_NORTE) % 1.0
    r, z, yaw = trajetoria(un, TAB_NORTE)
    f1, f2 = ik(r, z)
    posar(NORTE, yaw, f1, f2, aberto_de(un, SEGURA_NORTE), q)
    s_out = suave((un - 0.62) / 0.33)
    P = SAI[0]
    if un < SEGURA_NORTE[0]:
        pos(P, (PEGA_NORTE.x, PEGA_NORTE.y, zW - GRIP), (0, 0, yW), q)
    elif un < SEGURA_NORTE[1]:
        pos(P, ponta(O_NORTE, r, z - GRIP, yaw), (0, 0, yaw), q)
    else:
        pos(P, (SOLTA_NORTE.x + 0.3 * s_out, SOLTA_NORTE.y, zP - GRIP), (0, 0, yP), q)
    for k in range(1, 5):
        x = SOLTA_NORTE.x + 0.3 * k + 0.3 * s_out
        pos(SAI[k], (x, 1.0, zP - GRIP), (0, 0, yP), q)
        vis(SAI[k], x < 1.40, q)
    for rr in ROLOS_S:
        rr.e.rotation_euler = (0, -0.3 * s_out / 0.017, 0)
        chave(rr.e, 'rotation_euler', q)
    # ---------------- campo: pedras saem da calha, sobem, giram no ar e pousam no monte
    for k, o in enumerate(CAMPO_ITENS):
        uf = (fr + k / 3) % 1.0
        ang = 2 * PI * k / 3
        hov = Vector((XT + 0.07 * math.cos(ang + fr * 2 * PI), 0.07 * math.sin(ang + fr * 2 * PI), 1.14 + 0.05 * k))
        x0 = -0.40
        if uf < 0.14:
            t = uf / 0.14
            x = x0 + (X_CHUTE1 - x0) * t
            p = Vector((x, 0.0, z_calha(x) + 0.04))
            rot = (0, t * 4, 0)
        elif uf < 0.30:
            t = suave((uf - 0.14) / 0.16)
            a = Vector((X_CHUTE1 - 0.02, 0, Z_CHUTE1 + 0.04))
            p = a + (hov - a) * t + Vector((0, 0, 0.08 * math.sin(PI * t)))
            rot = (0.5 + t, t * 2, t)
        elif uf < 0.72:
            t = (uf - 0.30) / 0.42
            p = hov + Vector((0, 0, 0.025 * math.sin(2 * PI * t * 2)))
            rot = (1.5 + t * 2, 2 + t * 3, 1 + t * 4)
        else:
            t = suave((uf - 0.72) / 0.22)
            alvo = Vector((XT + 0.12 * math.cos(ang * 2), -0.12 + 0.1 * math.sin(ang), 0))
            alvo.z = monte(alvo.x, alvo.y) + 0.02 - 0.05 * max(0, (uf - 0.94) / 0.06)
            p = hov + (alvo - hov) * t
            rot = (3.5 + t, 5 + t, 5 + t * 0.5)
        pos(o, p, rot, q)
        vis(o, uf < 0.995, q)
    # ---------------- scanner: vai e volta ao longo do vagão
    ys = -1.15 * math.cos(2 * PI * fr)
    SCN.e.location = SCN.pivo + Vector((0, ys, 0))
    chave(SCN.e, 'location', q)
    cab = Vector((X_PONTA + 0.04 + 0.09, ys, 1.684))
    for (o, ponto_, xk) in RAIOS:
        alvo = Vector((xk, ys, topo_carga(xk, ys) + 0.002))
        d = alvo - cab
        o.location = cab
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        o.scale = (1, 1, d.length)
        ponto_.location = alvo
        for c in ('location', 'rotation_euler', 'scale'):
            chave(o, c, q)
        chave(ponto_, 'location', q)
    # ---------------- luzes
    emis('sinal_ambar', 14.0 if (q // 6) % 2 == 0 else 0.0, q)
    emis('led', 9.0 if (q // 4) % 3 != 0 else 1.0, q)
    emis('led_violeta', 9.0 if (q // 9) % 2 == 0 else 2.0, q)
    emis('nucleo', 5.0 + 2.5 * math.sin(2 * PI * fr * 2), q)
    emis('bobina_campo', 3.5 + 1.5 * math.sin(2 * PI * fr * 4), q)
    nivel = 3.2 + 1.5 * math.sin(2 * PI * (fr - 0.1))
    for k in range(6):
        emis('seg%d' % k, 7.0 if k < nivel else 0.0, q)
    luz_campo.energy = 20 + 8 * math.sin(2 * PI * fr * 4)
    luz_campo.keyframe_insert('energy', frame=q)
    onda.inputs['Phase Offset'].default_value = -2 * PI * fr * 2
    onda.inputs['Phase Offset'].keyframe_insert('default_value', frame=q)
    emc.inputs['Strength'].default_value = 2.5 + 0.8 * math.sin(2 * PI * fr * 4)
    emc.inputs['Strength'].keyframe_insert('default_value', frame=q)
    FAROL.e.rotation_euler = (0, 0, 2 * PI * fr * 3)
    chave(FAROL.e, 'rotation_euler', q)

# ------------------------------------------------------------------ cena: chão, luz, câmera
COL = sc.collection
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (16, 16, 1.0))
novo_obj('chao', bm, 'chao', chanfro=False)
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(56), 0, math.radians(42))
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
sc.cycles.transparent_max_bounces = 16
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.4
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos_, alvo, lente):
    cam.location = Vector(pos_)
    cam.rotation_euler = (Vector(alvo) - Vector(pos_)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def foto(nome, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.filepath = os.path.join(AQUI, nome + '.png')
    bpy.ops.render.render(write_still=True)


modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_fotos = sys.argv[sys.argv.index('--') + 2:] if '--' in sys.argv else []
quer = lambda n: not so_fotos or n in so_fotos
if modo in ('foto', 'teste'):
    sc.cycles.samples = 160 if modo == 'foto' else 24
    suf = '' if modo == 'foto' else '_teste'
    if quer('estacao_trem_0'):
        sc.frame_set(1 + int(0.40 * QUADROS))
        mirar((-4.1, -3.7, 2.05), (-0.6, -0.05, 0.85), 28)
        foto('estacao_trem_0' + suf, 1400, 1050)
    if quer('estacao_trem_1'):
        sc.frame_set(1 + int(0.15 * QUADROS))
        mirar((3.7, 3.6, 1.75), (-0.3, -0.05, 0.85), 28)
        foto('estacao_trem_1' + suf, 1400, 1050)
    if quer('estacao_trem_perto'):
        sc.frame_set(1 + int(0.45 * QUADROS))
        mirar((-2.85, 0.95, 1.6), (-0.95, -0.15, 1.0), 30)
        foto('estacao_trem_perto' + suf, 1400, 1050)
    if 'braco_teste' in so_fotos:
        sc.frame_set(1 + int(0.15 * QUADROS))
        mirar((0.9, 2.6, 1.5), (-0.6, 0.75, 0.95), 30)
        foto('estacao_braco_teste', 1200, 900)
