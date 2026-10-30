"""Estudo isolado (fora do jogo): três braços novos, 1×1 tile, partes giro, braco1, braco2, garra; pegam no sul e
soltam no norte (ITEM_ENT_S, ITEM_SAI_N). Base: braços aprovados (estudo_braco.py e estudo_braco_variantes.py).

BRAÇO COM FILTRO (braco_filtro) — o normal com scanner: câmera presa na garra com feixe de leitura âmbar que varre
o item antes de pegar; painel de seleção no chão com 5 luzes da IA (2 filtros escolhidos acesos, com ícone gravado);
garra de dois dedos com olho-sensor violeta; giroflex vermelho engaiolado que acende quando o item é rejeitado. No
ciclo uma placa de cobre (errada) passa pela esteira leste-oeste, é lida, luz vermelha, segue; a placa de ferro
(certa) é lida, a luz do filtro pisca, o braço pega e solta no norte.

BRAÇO EMPILHADOR (braco_empilhador) — braço reforçado (vigas-caixão, pistão de elevação na frente, atuador no
cotovelo) com contrapeso de placas na traseira do giro; garra-gaiola com garfos de pinça embaixo e pistões
compactadores que descem uma prensa sobre a pilha. Mergulha 4 vezes na fila, empilha 4 placas por baixo, leva a
pilha e solta no norte; contador de 4 LEDs na garra.

BRAÇO QUÂNTICO (braco_quantico) — estrutura pesada (chapa com chumbadores, pedestal com mãos-francesas, coroa e
pinhão, servos grandes com aletas e ventoinha, banco de capacitores, dois pistões de elevação, lança telescópica de
cinco seções com cilindro telescópico embaixo e carretel de cabo); a transferência é um campo violeta: as placas
sobem da esteira sul por um emissor de anéis na ponta da lança, voam por cima da lança dentro do campo e descem na
esteira norte. A lança estica de 1 a 3 tiles e deixa um rastro de anéis flutuando. Ciclo 0,2 s × 8 itens.
Uso: blender -b --python estudo_bracos_novos.py -- foto [nomes...]"""
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



# ------------------------------------------------------------------ materiais novos (campo, laser, luzes da IA)
def campo_mat(nome, cor, forca, base=0.2, borda=0.8, ruido=True):
    """Campo de energia: emissão com borda mais forte (casca), miolo transparente e estrias de ruído."""
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
    mx = no(nt, 'ShaderNodeMixShader')
    lw = no(nt, 'ShaderNodeLayerWeight', **{'Blend': 0.35})
    mr = no(nt, 'ShaderNodeMapRange', **{'To Min': base, 'To Max': base + borda})
    nt.links.new(lw.outputs['Facing'], mr.inputs['Value'])
    fac = mr.outputs['Result']
    if ruido:
        tc = no(nt, 'ShaderNodeTexCoord')
        ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 6.0, 'Distortion': 1.5})
        nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
        rr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.72, 'To Min': 0.1, 'To Max': 1.0})
        nt.links.new(ru.outputs['Fac'], rr.inputs['Value'])
        mm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(fac, mm.inputs[0])
        nt.links.new(rr.outputs['Result'], mm.inputs[1])
        fac = mm.outputs['Value']
    nt.links.new(fac, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


M.update({
    'campo': campo_mat('Campo violeta', (0.55, 0.16, 1.0), 6.0, base=0.0, borda=0.55),
    'halo': campo_mat('Halo violeta', (0.62, 0.25, 1.0), 4.0, base=0.0, borda=0.45, ruido=False),
    'laser': campo_mat('Laser âmbar', (1.0, 0.36, 0.03), 9.0, base=0.05, borda=0.12, ruido=False),
    'laser_linha': emissor('Linha do laser', (1.0, 0.4, 0.04), 35.0, base=(1.0, 0.5, 0.1)),
    'labio': emissor('Lábio violeta', (0.55, 0.15, 1.0), 14.0, base=(0.5, 0.2, 0.9)),
    'sensor': emissor('Sensor violeta', (0.55, 0.15, 1.0), 7.0, base=(0.3, 0.1, 0.6)),
    'cap_v': emissor('Visor do capacitor', (0.55, 0.15, 1.0), 3.0, base=(0.2, 0.06, 0.35)),
    'vidro': mats.material('Vidro escuro', (0.01, 0.012, 0.015), 0, 0.05, pintura=False, sujeira=0.4, desgaste=0.0),
    'giroflex': emissor('Giroflex vermelho', (1.0, 0.03, 0.015), 0.0, base=(0.35, 0.02, 0.01)),
    'slot_on': emissor('Filtro aceso', (0.55, 0.15, 1.0), 8.0, base=(0.5, 0.2, 0.9)),
    'slot_flash': emissor('Filtro que pisca', (0.55, 0.15, 1.0), 8.0, base=(0.5, 0.2, 0.9)),
    'slot_off': emissor('Filtro apagado', (0.3, 0.1, 0.6), 0.12, base=(0.035, 0.03, 0.05)),
})
for _k in range(4):
    M['cont%d' % _k] = emissor('Contador %d' % _k, (1.0, 0.5, 0.06), 0.0, base=(0.25, 0.12, 0.02))
M['cobre_item'] = mats.material('Placa de cobre', (0.72, 0.36, 0.2), 1.0, 0.4, pintura=False, ferrugem=0.3, sujeira=0.6)


def item_novo(nome, pai_e, mat='placa', marca='ferro'):
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (0.10, 0.10, 0.05))
    o = novo_obj(nome, bm, mat, pai_e)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.0258), (0.07, 0.07, 0.002))
    novo_obj(nome + '_marca', bm, marca, o, chanfro=False)
    return o


def varredura(bm, pts, r, lados=16, tampa=False):
    """Tubo contínuo por pontos (sem esferas nas emendas): bom para campo transparente."""
    aneis = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        q = t.to_track_quat('Z', 'Y').to_matrix()
        aneis.append([bm.verts.new(p + q @ Vector((math.cos(k * 2 * PI / lados) * r, math.sin(k * 2 * PI / lados) * r, 0)))
                      for k in range(lados)])
    for A_, B_ in zip(aneis, aneis[1:]):
        for k in range(lados):
            bm.faces.new((A_[k], A_[(k + 1) % lados], B_[(k + 1) % lados], B_[k]))
    if tampa:
        bm.faces.new(aneis[0][::-1])
        bm.faces.new(aneis[-1])


def chave_vis(o, vis, q):
    for x in [o] + [c for c in o.children if c.name.endswith('_marca')]:      # a plaquinha some junto com o item
        x.hide_render = x.hide_viewport = not vis
        x.keyframe_insert('hide_render', frame=q)
        x.keyframe_insert('hide_viewport', frame=q)


def chave_emis(mat, forca, q):
    inp = mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    inp.default_value = forca
    inp.keyframe_insert('default_value', frame=q)


def plinto(base, Zg, faixa):
    """Base do braço 1×1 (como o normal): plinto oitavado, anel de parafusos, coluna com faixa, coroa dentada."""
    cil(base.b('grafite'), (0, 0, Z0 + 0.03), 0.31, 0.06, Z, 8)
    cil(base.b('aco'), (0, 0, Z0 + 0.075), 0.26, 0.03, Z, 8)
    parafusos(base.b('cromo'), (0, 0, 0), 0.225, 8, 0.016, 0.014, Z0 + 0.09, PI / 8)
    h = Zg - 0.02 - (Z0 + 0.09)
    cilz(base.b('aco', True), (0, 0, Z0 + 0.09 + h / 2), 0.13, h, 32)
    cilz(base.b(faixa, True), (0, 0, Z0 + 0.135), 0.1335, 0.035, 32)
    cilz(base.b('grafite', True), (0, 0, Zg - 0.01), 0.148, 0.02, 32)
    dentes(base.b('aco'), (0, 0, 0), 0.151, 40, 0.012, 0.008, 0.018, Zg - 0.01)


def pistao(nome, giro, b1, A, P0, rc, Lc, rh, Lh, cor='amarelo'):
    """Pistão hidráulico: camisa articulada no giro (olhal em A), haste articulada no braço 1 (olhal em P0).
    Repouso: camisa ao longo de +Y a partir de A; haste ao longo de -Y a partir de P0."""
    A, P0 = Vector(A), Vector(P0)
    cam = Parte(nome + '_camisa', giro, A)
    cilx(cam.b('aco', True), A, rc * 0.8, 0.054, 16)
    cily(cam.b(cor, True), A + Vector((0, 0.03 + Lc / 2, 0)), rc, Lc, 32)
    cily(cam.b('grafite', True), A + Vector((0, 0.03 + Lc - 0.012, 0)), rc + 0.005, 0.024, 32)
    cily(cam.b('grafite', True), A + Vector((0, 0.045, 0)), rc + 0.005, 0.024, 32)
    tubo(cam.b('cromo', True), A + Vector((rc + 0.007, 0.06, 0)), A + Vector((rc + 0.007, 0.03 + Lc - 0.02, 0)), 0.005, 10)
    for yy in (0.06, 0.03 + Lc - 0.02):
        caixa_de(cam.b('aco'), (A.x + rc - 0.004, A.y + yy - 0.008, A.z - 0.006), (A.x + rc + 0.013, A.y + yy + 0.008, A.z + 0.006))
    caixa_de(cam.b('oleo'), (A.x - 0.01, A.y + 0.03 + Lc - 0.03, A.z - rc - 0.004), (A.x + 0.01, A.y + 0.03 + Lc - 0.14, A.z - rc + 0.001))
    has = Parte(nome + '_haste', b1, P0)
    cily(has.b('cromo', True), P0 + Vector((0, -Lh / 2, 0)), rh, Lh, 24)
    cilx(has.b('aco', True), P0, rh * 1.6, 0.05, 16)
    return dict(cam=cam, has=has, A=A, P0=P0, Lc=Lc, Lh=Lh, curso=[])


def posar_pistao(p, S, a1):
    rel = p['P0'] - S
    py = rel.y * math.cos(a1) - rel.z * math.sin(a1)
    pz = rel.y * math.sin(a1) + rel.z * math.cos(a1)
    d = S + Vector((0, py, pz)) - p['A']
    th = math.atan2(d.z, d.y)
    p['cam'].e.rotation_euler = (th, 0, 0)
    p['has'].e.rotation_euler = (th - a1, 0, 0)
    p['curso'].append(d.length)
    return [p['cam'].e, p['has'].e]


def ik2(A, r, z):
    L1, L2 = A['L1'], A['L2']
    zr = z - A['S'].z
    d = min(math.hypot(r, zr), L1 + L2 - 1e-4)
    c2 = (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    q = math.acos(max(-1, min(1, c2)))
    f1 = math.atan2(zr, r) + math.atan2(L2 * math.sin(q), L1 + L2 * math.cos(q))
    return f1, f1 - q


def posar2(A, yaw, f1, f2, q):
    a1 = f1 - PI / 2
    A['giro'].e.rotation_euler = (0, 0, yaw)
    A['b1'].e.rotation_euler = (a1, 0, 0)
    A['b2'].e.rotation_euler = (f2 - a1, 0, 0)
    A['g'].e.rotation_euler = (-f2, 0, 0)
    A['pinhao'].e.rotation_euler = (0, 0, -yaw * A['relacao'])
    objs = [A['giro'].e, A['b1'].e, A['b2'].e, A['g'].e, A['pinhao'].e]
    for p in A['pists']:
        objs += posar_pistao(p, A['S'], a1)
    for o in objs:
        chave(o, 'rotation_euler', q)


def helice(nome, pai, c, eixo, R):
    h = Parte(nome, pai, c)
    bm = h.b('grafite')
    e = Vector((1, 0, 0)) if eixo == 'X' else Vector((0, 0, 1))
    for k in range(7):
        a = k * 2 * PI / 7
        rot = Matrix.Rotation(a, 3, eixo) @ (Matrix.Rotation(0.5, 3, 'X' if eixo == 'Z' else 'Y'))
        off = Matrix.Rotation(a, 3, eixo) @ (Vector((0, R * 0.55, 0)) if eixo == 'X' else Vector((R * 0.55, 0, 0)))
        tam = (0.003, R * 0.9, 0.022) if eixo == 'X' else (R * 0.9, 0.022, 0.003)
        caixa(bm, c + off, tam, rot)
    cil(h.b('zarcao', True), c, R * 0.3, 0.012, e, 16)
    return h


def servo_x(parte, c, s, r=0.072, L=0.12, tampa='zarcao'):
    """Servomotor deitado no eixo X (lado s): redutor, carcaça, calor entre aletas, tampa, bocal e grade da ventoinha.
    c = centro do redutor (face encostada). Devolve o centro da ventoinha."""
    c = Vector(c)
    ex = Vector((s, 0, 0))
    cilx(parte.b('aco', True), c + ex * 0.004, r * 0.7, 0.008, 24)
    cilx(parte.b('grafite', True), c + ex * (0.008 + L / 2), r, L, 32)
    cilx(parte.b('calor', True), c + ex * (0.008 + L / 2), r + 0.0015, L * 0.75, 32)
    aletas(parte.b('grafite', True), c + ex * 0.025, ex, r * 1.25, 8, L * 0.1)
    cilx(parte.b(tampa, True), c + ex * (0.008 + L + 0.008), r * 1.04, 0.016, 32)
    anel(parte.b('grafite', True), c + ex * (0.008 + L + 0.034), r * 0.88, 0.007, X, 40, 8)
    cilx(parte.b('grafite', True), c + ex * (0.008 + L + 0.024), r * 0.98, 0.016, 32)
    bm = parte.b('aco')
    for k in range(4):
        caixa(bm, c + ex * (0.008 + L + 0.04), (0.004, r * 1.8, 0.004), Matrix.Rotation(k * PI / 4, 3, 'X'))
    return c + ex * (0.008 + L + 0.028)


# =================================================================== BRAÇO COM FILTRO
F_DESCE = 0.13          # punho → topo do item preso
F_H = 0.14              # altura extra da leitura (pairando)


def braco_filtro(O):
    global COL
    COL = bpy.data.collections.new('filtro')
    sc.collection.children.link(COL)
    raiz = Parte('filtro_raiz', None, (0, 0, 0))
    raiz.e.location = O
    laje(raiz, ((-0.30, 0.22, 0.05), (0.15, -0.36, 0.04)))
    es = Parte('filtro_esteira_s', raiz, (0, -1.0, 0))
    esteira(es, -1.0)
    es.fechar()
    es.e.rotation_euler = (0, 0, PI / 2)                      # esteira leste-oeste: o que não serve segue adiante
    en = Parte('filtro_esteira_n', raiz, (0, 0, 0))
    esteira(en, 1.0)
    en.fechar()
    Zg = Z0 + 0.225
    S = Vector((0, 0, Z0 + 0.40))
    L1, L2 = 0.55, 0.62
    E = S + Vector((0, 0, L1))
    W = E + Vector((0, L2, 0))
    # ---------------------------------------------------------- base (plinto do normal com faixa azul-primer)
    base = Parte('filtro_base', raiz, (0, 0, 0))
    plinto(base, Zg, 'primer')
    # painel de seleção: armário com tampo inclinado, 5 luzes da IA com ícone gravado de cada filtro
    caixa_de(base.b('grafite'), (0.28, -0.17, Z0), (0.46, 0.13, Z0 + 0.15))
    caixa_de(base.b('primer'), (0.278, -0.172, Z0 + 0.11), (0.462, 0.132, Z0 + 0.13))
    caixa_de(base.b('grafite'), (0.28, -0.17, Z0 + 0.15), (0.295, 0.13, Z0 + 0.285))
    for yy in (-0.17, 0.13):
        cunha(base.b('grafite'), (0.28, yy, Z0 + 0.15), (0.46, yy, Z0 + 0.15), (0.28, yy, Z0 + 0.285), 0.012, Y)
    th = math.atan2(0.135, 0.18)
    R = Matrix.Rotation(th, 3, 'Y')
    n = R @ Z
    C = Vector((0.37, -0.02, Z0 + 0.15 + 0.0675)) + n * 0.012
    caixa(base.b('primer'), C, (0.235, 0.31, 0.022), R)
    caixa(base.b('aco'), C + R @ Vector((0.112, 0, 0.004)), (0.012, 0.31, 0.03), R)          # friso de baixo
    slots = ('slot_flash', 'slot_on', 'slot_off', 'slot_off', 'slot_off')
    for k in range(5):
        yo = (k - 2) * 0.058
        P = C + R @ Vector((-0.035, yo, 0.011))
        cil(base.b('aco', True), P + n * 0.005, 0.021, 0.01, n, 20)                          # aro
        cil(base.b(slots[k], True), P + n * 0.012, 0.015, 0.012, n, 20)                      # lente
        bm = base.b('aco')
        for a in (PI / 4, -PI / 4):
            caixa(bm, P + n * 0.021, (0.036, 0.003, 0.003), R @ Matrix.Rotation(a, 3, 'Z'))  # grade da lente
        Q = C + R @ Vector((0.05, yo, 0.011))
        caixa(base.b('aco'), Q + n * 0.002, (0.036, 0.036, 0.004), R)                         # plaquinha do ícone
        if k == 0:
            caixa(base.b('placa'), Q + n * 0.006, (0.018, 0.018, 0.006), R)                  # ícone: placa de ferro
        elif k == 1:
            cil(base.b('aco', True), Q + n * 0.006, 0.008, 0.006, n, 12)                     # ícone: engrenagem
            for j in range(6):
                caixa(base.b('aco'), Q + n * 0.006 + R @ Vector((math.cos(j * PI / 3) * 0.01, math.sin(j * PI / 3) * 0.01, 0)),
                      (0.004, 0.004, 0.006), R @ Matrix.Rotation(j * PI / 3, 3, 'Z'))
        else:
            caixa(base.b('ferro'), Q + n * 0.005, (0.02, 0.003, 0.003), R)                    # vazio: traço
    estencil('FILTRO  5 VIAS', base, C + R @ Vector((-0.095, 0.0, 0.0115)), n, R @ Y, 0.014)
    # giroflex vermelho engaiolado num poste preso ao armário
    pz0 = Z0 + 0.29
    caixa_de(base.b('grafite'), (0.40, 0.13, Z0 + 0.09), (0.44, 0.21, Z0 + 0.11))
    cilz(base.b('aco', True), (0.42, 0.205, Z0 + 0.145), 0.012, 0.29, 12)
    cilz(base.b('grafite', True), (0.42, 0.205, pz0 + 0.01), 0.03, 0.02, 24)
    cilz(base.b('giroflex', True), (0.42, 0.205, pz0 + 0.045), 0.024, 0.05, 24)
    cilz(base.b('grafite', True), (0.42, 0.205, pz0 + 0.076), 0.032, 0.012, 24)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        cilz(base.b('aco', True), (0.42 + math.cos(a) * 0.03, 0.205 + math.sin(a) * 0.03, pz0 + 0.045), 0.003, 0.06, 6)
    luz = bpy.data.lights.new('filtro_giroflex_luz', 'POINT')
    luz.color = (1.0, 0.05, 0.02)
    luz.energy = 0.0
    luz.shadow_soft_size = 0.02
    lo = bpy.data.objects.new('filtro_giroflex_luz', luz)
    COL.objects.link(lo)
    lo.parent = raiz.e
    lo.location = (0.42, 0.205, pz0 + 0.045)
    # cabos do painel até a coluna e eletroduto para o chão
    for dy, mat in ((-0.06, 'borracha'), (-0.02, 'cabo_laranja')):
        pts = bezier((0.28, dy, Z0 + 0.08), (0.22, dy, Z0 + 0.08), (0.17, dy * 0.5, Z0 + 0.13), (0.128, dy * 0.4, Z0 + 0.15), 8)
        mangueira(base.b(mat, True), pts, 0.011)
        abracadeiras(base.b('aco', True), pts, 0.011, 3)
        cil(base.b('grafite', True), pts[0], 0.017, 0.022, X, 10)
        cil(base.b('grafite', True), pts[-1], 0.017, 0.022, (pts[-1] - pts[-2]).normalized(), 10)
    pe = bezier((0.40, -0.17, Z0 + 0.04), (0.40, -0.25, Z0 + 0.03), (0.40, -0.40, Z0 + 0.01), (0.40, -0.52, -0.02), 6)
    mangueira(base.b('grafite', True), pe, 0.017)
    # ---------------------------------------------------------- giro (como o normal): corpo, motor com aletas, válvulas
    giro = Parte('filtro_giro', base, (0, 0, Zg))
    caixa_de(giro.b('amarelo'), (-0.11, -0.13, Zg), (0.11, 0.13, Zg + 0.11))
    caixa_de(giro.b('primer'), (-0.1115, -0.1315, Zg + 0.02), (0.1115, 0.1315, Zg + 0.045))
    caixa_de(giro.b('grafite'), (-0.08, -0.12, Zg + 0.11), (0.08, 0.04, Zg + 0.135))
    for x in (-0.085, 0.085):
        caixa_de(giro.b('aco'), (x - 0.0175, -0.055, Zg + 0.11), (x + 0.0175, 0.055, S.z + 0.04))
        caixa_de(giro.b('grafite'), (x - 0.02, -0.06, Zg + 0.105), (x + 0.02, 0.06, Zg + 0.12))
        cil(giro.b('aco'), Vector((x * 1.24, 0, S.z)), 0.022, 0.012, X, 6)
    cilx(giro.b('cromo', True), S, 0.016, 0.21, 12)
    cilx(giro.b('aco', True), (-0.165, 0, Zg + 0.055), 0.055, 0.10, 24)                      # motor do giro, deitado
    aletas(giro.b('grafite', True), (-0.13, 0, Zg + 0.055), -X, 0.066, 4, 0.024, 0.008)
    cilx(giro.b('cobre', True), (-0.225, 0, Zg + 0.055), 0.03, 0.02, 12)
    cx = Vector((-0.18, 0.0, 0))
    cilz(giro.b('aco', True), cx + Vector((0, 0, Zg + 0.002)), 0.016, 0.02, 16)
    pinhao = Parte('filtro_pinhao', giro, cx + Vector((0, 0, Zg - 0.01)))
    cilz(pinhao.b('aco', True), pinhao.pivo, 0.022, 0.018, 16)
    dentes(pinhao.b('aco'), pinhao.pivo, 0.025, 10, 0.012, 0.008, 0.018, 0)
    caixa_de(giro.b('grafite'), (0.065, -0.135, Zg + 0.11), (0.135, -0.085, Zg + 0.16))       # bloco de válvulas
    for k in range(2):
        cilz(giro.b('cobre', True), (0.085 + 0.03 * k, -0.11, Zg + 0.175), 0.012, 0.03, 10)
    cil(giro.b('led'), Vector((0.136, -0.10, Zg + 0.14)), 0.006, 0.005, X, 8)
    # suporte traseiro do pistão
    A = Vector((0, -0.20, Zg + 0.15))
    caixa_de(giro.b('amarelo'), (-0.05, -0.235, Zg), (0.05, -0.13, Zg + 0.07))
    for s in (-1, 1):
        caixa_de(giro.b('amarelo'), (s * 0.030, -0.235, Zg + 0.05), (s * 0.044, -0.165, A.z + 0.03))
    cilx(giro.b('cromo', True), A, 0.011, 0.105, 12)
    h = bezier(Vector((0.10, -0.135, Zg + 0.13)), Vector((0.10, -0.20, Zg + 0.12)), Vector((0.06, -0.22, Zg + 0.09)), Vector((0.044, -0.215, Zg + 0.09)), 8)
    mangueira(giro.b('borracha', True), h, 0.008)
    # ---------------------------------------------------------- braço 1: chapas amarelas com travessas (o normal)
    b1 = Parte('filtro_braco1', giro, S)
    cilx(b1.b('grafite', True), S, 0.045, 0.13, 24)
    for s in (-1, 1):
        caixa_de(b1.b('amarelo'), (s * 0.038, -0.025, S.z), (s * 0.058, 0.025, E.z))
        caixa_de(b1.b('amarelo'), (s * 0.038, -0.07, S.z + 0.22), (s * 0.058, -0.025, S.z + 0.28))   # olhal da haste
    P0 = S + Vector((0, -0.05, 0.25))
    cilx(b1.b('cromo', True), P0, 0.011, 0.13, 12)
    for k in range(1, 5):
        cilx(b1.b('aco', True), (0, 0.012, S.z + L1 * k / 5 + 0.02), 0.011, 0.076, 10)
    cilx(b1.b('grafite', True), E, 0.055, 0.13, 24)
    for s in (-1, 1):
        cilx(b1.b('aco', True), (s * 0.07, 0, E.z), 0.038, 0.012, 20)
        cil(b1.b('aco'), Vector((s * 0.08, 0, E.z)), 0.014, 0.01, X, 6)
    # mangueira pneumática (+X) e cabo de dados do scanner (-X), com bocais e presilhas
    caixa_de(b1.b('grafite'), (0.058, -0.02, S.z + 0.06), (0.076, 0.02, S.z + 0.10))
    caixa_de(b1.b('grafite'), (-0.076, -0.02, S.z + 0.06), (-0.058, 0.02, S.z + 0.10))
    hp = [Vector((0.07, 0.0, S.z + 0.10))] + [Vector((0.07, 0.0, S.z + f)) for f in (0.2, 0.3, 0.4)] + \
         bezier(Vector((0.07, 0.0, E.z - 0.11)), Vector((0.075, 0.0, E.z - 0.07)), Vector((0.08, 0.02, E.z - 0.065)), Vector((0.08, 0.05, E.z - 0.055)), 5)
    mangueira(b1.b('borracha', True), hp, 0.01)
    hd = [Vector((-0.07, 0.0, S.z + 0.10))] + [Vector((-0.07, 0.0, S.z + f)) for f in (0.2, 0.3, 0.4)] + \
         bezier(Vector((-0.07, 0.0, E.z - 0.11)), Vector((-0.075, 0.0, E.z - 0.07)), Vector((-0.08, 0.02, E.z - 0.065)), Vector((-0.08, 0.05, E.z - 0.055)), 5)
    mangueira(b1.b('cabo_laranja', True), hd, 0.008)
    for f in (0.17, 0.33):
        for s in (-1, 1):
            caixa_de(b1.b('aco'), (s * 0.058, -0.016, S.z + f), (s * 0.082, 0.016, S.z + f + 0.014))
    # ---------------------------------------------------------- braço 2: tubo afilado amarelo, garfo do punho
    b2 = Parte('filtro_braco2', b1, E)
    cilx(b2.b('amarelo', True), E, 0.05, 0.07, 24)
    cil(b2.b('amarelo', True), E + Vector((0, 0.04 + (L2 - 0.11) / 2, 0)), 0.038, L2 - 0.11, Y, 24, r2=0.03)
    cily(b2.b('grafite', True), E + Vector((0, 0.06, 0)), 0.042, 0.02, 24)
    for f in (0.25, 0.42):
        cily(b2.b('primer', True), E + Vector((0, f, 0)), 0.0365 - f * 0.012, 0.025, 24)
    for s in (-1, 1):
        caixa_de(b2.b('grafite'), (s * 0.044 - 0.006, W.y - 0.07, W.z - 0.03), (s * 0.044 + 0.006, W.y + 0.02, W.z + 0.03))
    caixa_de(b2.b('grafite'), (-0.05, W.y - 0.075, W.z - 0.02), (0.05, W.y - 0.065, W.z + 0.02))
    for s, mat, r in ((1, 'borracha', 0.009), (-1, 'cabo_laranja', 0.007)):
        pts = [E + Vector((s * 0.08, 0.05, -0.055)), E + Vector((s * 0.06, 0.12, 0.045))] + \
              [E + Vector((s * 0.03, f, 0.045 - f * 0.012)) for f in (0.2, 0.3, 0.4, 0.5)] + [W + Vector((s * 0.03, -0.05, 0.03))]
        mangueira(b2.b(mat, True), pts, r)
    for f in (0.2, 0.4):
        cily(b2.b('aco', True), E + Vector((0, f, 0)), 0.04 - f * 0.012, 0.012, 24)
    # ---------------------------------------------------------- garra: dedos, olho-sensor e câmera do scanner
    g = Parte('filtro_garra', b2, W)
    cilx(g.b('aco', True), W, 0.04, 0.084, 24)
    cilz(g.b('cromo', True), W + Vector((0, 0, -0.045)), 0.022, 0.035, 16)
    caixa_de(g.b('grafite'), (W.x - 0.075, W.y - 0.045, W.z - 0.105), (W.x + 0.075, W.y + 0.045, W.z - 0.065))
    caixa_de(g.b('amarelo'), (W.x - 0.06, W.y - 0.04, W.z - 0.07), (W.x + 0.06, W.y + 0.04, W.z - 0.06))
    caixa_de(g.b('cromo'), (W.x - 0.095, W.y - 0.02, W.z - 0.115), (W.x + 0.095, W.y + 0.02, W.z - 0.105))
    cilx(g.b('aco', True), W + Vector((0, 0.055, -0.08)), 0.016, 0.16, 16)
    cil(g.b('cobre', True), W + Vector((0.05, 0.072, -0.08)), 0.007, 0.02, Y, 6)
    cilz(g.b('grafite', True), W + Vector((0, 0, -0.118)), 0.016, 0.008, 20)                 # olho-sensor
    cilz(g.b('sensor', True), W + Vector((0, 0, -0.1235)), 0.011, 0.004, 20)
    # câmera do scanner (lado -X da garra), cano da lente apontado para o item
    caixa_de(g.b('aco'), (W.x - 0.088, W.y - 0.012, W.z - 0.085), (W.x - 0.075, W.y + 0.012, W.z - 0.07))
    caixa_de(g.b('grafite'), (W.x - 0.13, W.y - 0.03, W.z - 0.09), (W.x - 0.088, W.y + 0.03, W.z - 0.045))
    caixa_de(g.b('primer'), (W.x - 0.132, W.y - 0.032, W.z - 0.06), (W.x - 0.086, W.y + 0.032, W.z - 0.05))
    caixa_de(g.b('grafite'), (W.x - 0.135, W.y - 0.034, W.z - 0.047), (W.x - 0.083, W.y + 0.034, W.z - 0.042))   # pala
    alvo = W + Vector((0, 0, -(F_DESCE + F_H)))
    L0 = W + Vector((-0.11, 0, -0.095))
    dl = (alvo - L0).normalized()
    cil(g.b('grafite', True), L0, 0.014, 0.03, dl, 20)
    cil(g.b('aco', True), L0 + dl * 0.016, 0.016, 0.006, dl, 20)
    cil(g.b('vidro', True), L0 + dl * 0.0185, 0.011, 0.002, dl, 20)
    cil(g.b('led', True), L0 + Vector((0.0, 0.022, 0.0)), 0.004, 0.004, -X, 8)
    fiacao(g, W + Vector((-0.11, 0.03, -0.06)), Vector((0.0, 0.015, 0.02)), W + Vector((-0.075, 0.04, -0.07)))
    dedos = []
    for s in (-1, 1):
        d = Parte('filtro_dedo_%d' % s, g, W + Vector((s * 0.067, 0, -0.11)))
        c = d.pivo
        caixa_de(d.b('aco'), (c.x - 0.013, c.y - 0.03, c.z - 0.035), (c.x + 0.013, c.y + 0.03, c.z + 0.0))
        caixa_de(d.b('grafite'), (c.x - 0.013, c.y - 0.028, c.z - 0.065), (c.x + 0.013, c.y + 0.028, c.z - 0.035))
        caixa_de(d.b('borracha'), (c.x - s * 0.013 - s * 0.004, c.y - 0.024, c.z - 0.063), (c.x - s * 0.013, c.y + 0.024, c.z - 0.04))
        cil(d.b('sensor'), c + Vector((-s * 0.0132, 0, -0.03)), 0.003, 0.002, X, 8)            # sensor de toque
        dedos.append((d, s))
    # feixe de leitura: leque âmbar do cano da lente até o topo do item, com a linha no item
    Pa = L0 + dl * 0.02
    fx = Parte('filtro_feixe', g, Pa)
    bm = fx.b('laser')
    zt = alvo.z + 0.002
    vs = [bm.verts.new(v) for v in (Pa + Vector((0, -0.0008, 0)), Vector((-0.07, W.y - 0.0008, zt)), Vector((0.07, W.y - 0.0008, zt)),
                                     Pa + Vector((0, 0.0008, 0)), Vector((-0.07, W.y + 0.0008, zt)), Vector((0.07, W.y + 0.0008, zt)))]
    bm.faces.new((vs[0], vs[1], vs[2]))
    bm.faces.new((vs[5], vs[4], vs[3]))
    bm.faces.new((vs[1], vs[4], vs[5], vs[2]))
    caixa(fx.b('laser_linha'), Vector((0, W.y, zt)), (0.142, 0.003, 0.002))
    cil(fx.b('laser_linha', True), Pa, 0.004, 0.006, dl, 10)
    # ---------------------------------------------------------- pistão de elevação (camisa no giro, haste no braço 1)
    pst = pistao('filtro_pistao', giro, b1, A, P0, 0.03, 0.26, 0.014, 0.27)
    # ---------------------------------------------------------- uso pesado
    remendo(giro, (-0.06, 0.1315, Zg + 0.075), -X, Z, 0.07, 0.04, Y)
    remendo(base, (0.37, -0.172, Z0 + 0.06), X, Z, 0.08, 0.05, -Y)
    amassado(giro.b('amarelo', True), (0.1115, 0.05, Zg + 0.08), Y, Z, 0.10, 0.05, 0.004, ((0.1, 0.1, 0.2),))
    amassado(base.b('grafite', True), (0.462, -0.05, Z0 + 0.07), Y, Z, 0.16, 0.08, 0.005, ((0.2, -0.1, 0.2), (-0.25, 0.2, 0.12)))
    caixa_de(b1.b('zarcao'), (0.0585, -0.025, S.z + 0.36), (0.06, 0.025, S.z + 0.46))           # chapa trocada
    fiacao(base, (0.29, 0.10, Z0 + 0.14), Vector((-0.03, 0.0, 0.02)), (0.29, 0.06, Z0 + 0.10))
    fiacao(giro, (-0.04, -0.12, Zg + 0.1355), Vector((0.0, 0.0, 0.03)), (-0.0, -0.10, Zg + 0.1355))
    caixa_de(giro.b('oleo'), (-0.215, -0.01, Zg - 0.0), (-0.21, 0.01, Zg + 0.03))
    estencil('FX-03  2210-S', giro, (0.04, 0.1316, Zg + 0.075), Y, Z, 0.016)
    estencil('0731', b1, (-0.0585, 0.0, S.z + 0.40), -X, Y, 0.012)
    partes = [raiz, base, giro, pinhao, b1, b2, g, fx, pst['cam'], pst['has']] + [d for d, _ in dedos]
    for p in partes:
        p.fechar()
    itens = (item_novo('filtro_item_certo', raiz.e, 'placa', 'ferro'), item_novo('filtro_item_errado', raiz.e, 'cobre_item', 'grafite'))
    return dict(nome='filtro', raiz=raiz, giro=giro, b1=b1, b2=b2, g=g, pinhao=pinhao, dedos=dedos, feixe=fx, luz=lo,
                pists=[pst], itens=itens, S=S, L1=L1, L2=L2, relacao=0.148 / 0.022, col=COL, O=Vector(O))


def animar_filtro(A):
    zp = TOPO_ESTEIRA + H_ITEM + F_DESCE
    zh = zp + F_H
    rr, zr = 0.55, 0.75
    tab = [(0.00, 1.0, zh, PI), (0.53, 1.0, zh, PI), (0.565, 1.0, zp, PI), (0.60, 1.0, zp, PI), (0.635, 1.0, zh, PI),
           (0.69, rr, zr, 0.8 * PI), (0.75, rr, zr, 0.2 * PI), (0.80, 1.0, zh, 0.0), (0.835, 1.0, zp, 0.0),
           (0.87, 1.0, zp, 0.0), (0.90, 1.0, zh, 0.0), (0.945, rr, zr, 0.5 * PI), (0.99, 1.0, zh, PI), (1.0, 1.0, zh, PI)]
    certo, errado = A['itens']
    zc = TOPO_ESTEIRA + H_ITEM / 2
    for q in range(1, QUADROS + 1):
        u = (q - 1) / QUADROS
        r, z, yaw = trajetoria(u, tab)
        f1, f2 = ik2(A, r, z)
        posar2(A, yaw, f1, f2, q)
        aberto = 1.0 - suave((u - 0.57) / 0.015) + suave((u - 0.855) / 0.015)
        aberto = max(0.0, min(1.0, aberto))
        for d, s in A['dedos']:
            d.e.location = d.pivo - A['g'].pivo + Vector((s * 0.026 * aberto, 0, 0))
            chave(d.e, 'location', q)
        # item errado (cobre): chega do oeste, é lido, luz vermelha, segue para o leste
        if u < 0.12:
            x = -0.55 * (1 - suave(u / 0.12))
        elif u < 0.30:
            x = 0.0
        else:
            x = 0.55 * suave((u - 0.30) / 0.12)
        errado.location = (x, -1.0, zc)
        chave(errado, 'location', q)
        chave_vis(errado, abs(x) < 0.47, q)
        # item certo (ferro): chega, é lido, a luz do filtro pisca, é pego e solto no norte
        preso = 0.585 <= u < 0.86
        if u < 0.30:
            p, vis = Vector((-0.55, -1.0, zc)), False
        elif u < 0.42:
            p, vis = Vector((-0.55 * (1 - suave((u - 0.30) / 0.12)), -1.0, zc)), True
            vis = p.x > -0.47
        elif u < 0.585:
            p, vis = Vector((0, -1.0, zc)), True
        elif preso:
            p, vis = Vector((-r * math.sin(yaw), r * math.cos(yaw), z - F_DESCE - H_ITEM / 2)), True
        else:
            t = suave((u - 0.88) / 0.11)
            p, vis = Vector((0, 1.0 + 0.48 * t, zc)), u < 0.985
        certo.location, certo.rotation_euler = p, (0, 0, yaw if preso else 0.0)
        chave(certo, 'location', q)
        chave(certo, 'rotation_euler', q)
        chave_vis(certo, vis, q)
        # feixe de leitura varrendo (só durante as leituras)
        lendo = 0.13 <= u < 0.27 or 0.43 <= u < 0.52
        A['feixe'].e.rotation_euler = (0.24 * math.sin(u * 2 * PI * 9), 0, 0)
        chave(A['feixe'].e, 'rotation_euler', q)
        for o in A['feixe'].objs:
            chave_vis(o, lendo, q)
        # luzes: giroflex vermelho na rejeição; a luz do filtro escolhido pisca no aceite
        rej = 0.22 <= u < 0.37
        pisca = (q // 2) % 2 == 0
        chave_emis(M['giroflex'], (40.0 if pisca else 12.0) if rej else 0.0, q)
        A['luz'].data.energy = (3.0 if pisca else 1.2) if rej else 0.0
        A['luz'].data.keyframe_insert('energy', frame=q)
        ace = 0.47 <= u < 0.56
        chave_emis(M['slot_flash'], (40.0 if pisca else 8.0) if ace else 8.0, q)


# =================================================================== BRAÇO EMPILHADOR
E_FUNDO = 0.34          # punho → fundo da gaiola
E_PRENSA0 = -0.285      # fundo da prensa (repouso, mais baixa) em relação ao punho
E_R = 0.75              # alcance: pega na esteira sul e solta na norte a 0,75 m


def braco_empilhador(O):
    global COL
    COL = bpy.data.collections.new('empilhador')
    sc.collection.children.link(COL)
    raiz = Parte('empilhador_raiz', None, (0, 0, 0))
    raiz.e.location = O
    laje(raiz, ((0.28, 0.30, 0.06), (-0.3, -0.25, 0.05), (0.25, -0.33, 0.035)))
    est = Parte('empilhador_esteiras', raiz, (0, 0, 0))
    esteira(est, -1.0)
    esteira(est, 1.0)
    est.fechar()
    Zg = Z0 + 0.25
    S = Vector((0, 0, Zg + 0.20))
    L1, L2 = 0.55, 0.62
    E = S + Vector((0, 0, L1))
    W = E + Vector((0, L2, 0))
    # ---------------------------------------------------------- base reforçada: chapa, chumbadores, pedestal, mãos-francesas
    base = Parte('empilhador_base', raiz, (0, 0, 0))
    caixa_de(base.b('aco'), (-0.40, -0.40, Z0), (0.40, 0.40, Z0 + 0.03))
    bm, bmn = base.b('aco', True), base.b('aco')
    for k in range(12):
        t = k / 12 * 4
        lado, f = int(t), t - int(t)
        s_ = -0.36 + 0.72 * f
        p = [(s_, -0.36), (0.36, s_), (-s_, 0.36), (-0.36, -s_)][lado]
        cilz(bm, (p[0], p[1], Z0 + 0.05), 0.01, 0.05, 10)
        cilz(bmn, (p[0], p[1], Z0 + 0.033), 0.021, 0.006, 16)
        cil(bmn, Vector((p[0], p[1], Z0 + 0.044)), 0.017, 0.016, Z, 6)
    cilz(base.b('amarelo'), (0, 0, Z0 + 0.03 + 0.09), 0.17, 0.18, 8)
    bm = base.b('amarelo')
    for k in range(6):
        a = k * PI / 3 + PI / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        cunha(bm, d * 0.155 + Vector((0, 0, Z0 + 0.03)), d * 0.33 + Vector((0, 0, Z0 + 0.03)), d * 0.155 + Vector((0, 0, Z0 + 0.19)), 0.016, Vector((-d.y, d.x, 0)))
    caixa_de(base.b('listras'), (-0.07, -0.158, Z0 + 0.05), (0.07, -0.152, Z0 + 0.10))
    cilz(base.b('grafite', True), (0, 0, Z0 + 0.225), 0.16, 0.03, 40)
    parafusos(base.b('aco'), (0, 0, 0), 0.145, 12, 0.009, 0.01, Z0 + 0.24)
    cilz(base.b('grafite', True), (0, 0, Zg - 0.01), 0.185, 0.02, 48)
    dentes(base.b('aco'), (0, 0, 0), 0.19, 56, 0.013, 0.009, 0.02, Zg - 0.01)
    # unidade hidráulica no chão (tanque + motor-bomba) e mangueiras até o pedestal
    tq = Vector((-0.28, 0.26, Z0 + 0.09))
    cilx(base.b('amarelo', True), tq, 0.055, 0.17, 32)
    for s in (-1, 1):
        cilx(base.b('grafite', True), tq + Vector((s * 0.085, 0, 0)), 0.058, 0.012, 32)
        caixa_de(base.b('grafite'), (tq.x + s * 0.06 - 0.01, tq.y - 0.04, Z0 + 0.03), (tq.x + s * 0.06 + 0.01, tq.y + 0.04, tq.z - 0.03))
    caixa_de(base.b('visor'), (tq.x - 0.04, tq.y - 0.058, tq.z - 0.02), (tq.x + 0.03, tq.y - 0.052, tq.z + 0.02))
    cilz(base.b('grafite', True), tq + Vector((0.05, 0, 0.06)), 0.015, 0.02, 12)
    bp = Vector((-0.28, 0.07, Z0 + 0.075))
    cilx(base.b('grafite', True), bp, 0.04, 0.09, 24)
    aletas(base.b('grafite', True), bp + Vector((-0.035, 0, 0)), X, 0.048, 6, 0.013)
    cilx(base.b('aco', True), bp + Vector((0.065, 0, 0)), 0.028, 0.04, 16)
    for hh in (bezier(tq + Vector((0.04, -0.05, 0.03)), tq + Vector((0.06, -0.10, 0.08)), bp + Vector((0.07, 0.04, 0.05)), bp + Vector((0.075, 0.0, 0.028)), 8),
               bezier(bp + Vector((0.085, 0.0, 0.0)), Vector((-0.13, 0.05, Z0 + 0.08)), Vector((-0.12, 0.05, Z0 + 0.15)), Vector((-0.155, 0.07, Z0 + 0.17)), 8)):
        mangueira(base.b('borracha', True), hh, 0.011)
        abracadeiras(base.b('aco', True), hh, 0.011, 2)
        cil(base.b('cobre', True), hh[-1], 0.016, 0.022, (hh[-1] - hh[-2]).normalized(), 6)
    # ---------------------------------------------------------- giro: corpo, contrapeso em placas, mancais, olhal do pistão
    giro = Parte('empilhador_giro', base, (0, 0, Zg))
    cilz(giro.b('grafite', True), (0, 0, Zg + 0.015), 0.21, 0.03, 48)
    caixa_de(giro.b('amarelo'), (-0.13, -0.14, Zg + 0.03), (0.13, 0.14, Zg + 0.14))
    caixa_de(giro.b('zarcao'), (-0.1315, -0.1415, Zg + 0.05), (0.1315, 0.1415, Zg + 0.075))
    bm = giro.b('ferro')
    for k in range(4):
        y0 = -0.14 - k * 0.05
        caixa_de(bm, (-0.16 + 0.007 * k, y0 - 0.048, Zg + 0.03), (0.16 - 0.007 * k, y0, Zg + 0.23 - 0.01 * k))
    caixa_de(giro.b('listras'), (-0.12, -0.3425, Zg + 0.05), (0.12, -0.338, Zg + 0.17))
    for x in (-0.11, 0.11):
        for z in (Zg + 0.07, Zg + 0.17):
            cily(giro.b('cromo', True), (x, -0.24, z), 0.008, 0.215, 10)
            cil(giro.b('aco'), Vector((x, -0.346, z)), 0.015, 0.01, Y, 6)
    anel(giro.b('aco', True), (0, -0.24, Zg + 0.235), 0.026, 0.007, X, 24, 8)
    for x in (-0.09, 0.09):
        caixa_de(giro.b('amarelo'), (x - 0.015, -0.08, Zg + 0.14), (x + 0.015, 0.08, S.z + 0.06))
        cunha(giro.b('amarelo'), (x, -0.08, Zg + 0.14), (x, -0.16, Zg + 0.14), (x, -0.08, S.z), 0.02, X)
        cil(giro.b('aco'), Vector((x * 1.28, 0, S.z)), 0.03, 0.014, X, 6)
    cilx(giro.b('cromo', True), S, 0.022, 0.24, 12)
    # motor do giro (servo deitado na lateral -X, pinhão na coroa)
    cx = Vector((-0.225, 0.06, 0))
    caixa_de(giro.b('amarelo'), (-0.26, 0.02, Zg + 0.03), (-0.13, 0.10, Zg + 0.05))
    cilz(giro.b('grafite', True), cx + Vector((0, 0, Zg + 0.11)), 0.045, 0.12, 24)
    aletas(giro.b('grafite', True), cx + Vector((0, 0, Zg + 0.065)), Z, 0.056, 7, 0.014)
    cilz(giro.b('zarcao', True), cx + Vector((0, 0, Zg + 0.178)), 0.047, 0.016, 24)
    cilz(giro.b('aco', True), cx + Vector((0, 0, Zg + 0.012)), 0.016, 0.03, 16)
    pinhao = Parte('empilhador_pinhao', giro, cx + Vector((0, 0, Zg - 0.01)))
    cilz(pinhao.b('aco', True), pinhao.pivo, 0.026, 0.02, 16)
    dentes(pinhao.b('aco'), pinhao.pivo, 0.03, 10, 0.013, 0.009, 0.02, 0)
    # olhal dianteiro do pistão
    A = Vector((0, 0.20, Zg + 0.08))
    caixa_de(giro.b('amarelo'), (-0.055, 0.14, Zg + 0.03), (0.055, 0.24, Zg + 0.07))
    for s in (-1, 1):
        caixa_de(giro.b('amarelo'), (s * 0.032, 0.16, Zg + 0.05), (s * 0.046, 0.24, A.z + 0.035))
    cilx(giro.b('cromo', True), A, 0.012, 0.11, 12)
    # bloco de válvulas com solenoides; mangueiras até o pistão
    caixa_de(giro.b('grafite'), (0.05, 0.02, Zg + 0.14), (0.075, 0.12, Zg + 0.19))
    for k in range(3):
        cilx(giro.b('cobre', True), (0.083, 0.035 + k * 0.035, Zg + 0.17), 0.011, 0.02, 10)
        cil(giro.b('led'), Vector((0.0755, 0.035 + k * 0.035, Zg + 0.15)), 0.005, 0.004, X, 8)
    h = bezier(Vector((0.06, 0.12, Zg + 0.16)), Vector((0.06, 0.17, Zg + 0.15)), Vector((0.06, 0.22, Zg + 0.12)), Vector((0.047, 0.22, Zg + 0.10)), 8)
    mangueira(giro.b('borracha', True), h, 0.009)
    # ---------------------------------------------------------- braço 1: viga-caixão reforçada
    b1 = Parte('empilhador_braco1', giro, S)
    cilx(b1.b('grafite', True), S, 0.055, 0.15, 24)
    for s in (-1, 1):
        caixa_de(b1.b('amarelo'), (s * 0.042, -0.05, S.z), (s * 0.058, 0.05, E.z))
        caixa_de(b1.b('grafite'), (s * 0.058, -0.035, S.z + 0.10), (s * 0.064, 0.035, E.z - 0.10))      # chapa dobrada
    for yy in (-0.05, 0.04):
        caixa_de(b1.b('grafite'), (-0.042, yy, S.z + 0.06), (0.042, yy + 0.01, E.z - 0.06))
    for z in (S.z + 0.16, S.z + 0.38):
        caixa_de(b1.b('aco'), (-0.066, -0.054, z), (0.066, 0.054, z + 0.025))                          # cintas
    P0 = S + Vector((0, 0.085, 0.25))
    for s in (-1, 1):
        caixa_de(b1.b('amarelo'), (s * 0.028, 0.05, P0.z - 0.04), (s * 0.042, 0.11, P0.z + 0.04))
    cilx(b1.b('cromo', True), P0, 0.012, 0.1, 12)
    cilx(b1.b('grafite', True), E, 0.06, 0.15, 24)
    # atuador rotativo hidráulico do cotovelo (+X)
    cilx(b1.b('amarelo', True), E + Vector((0.11, 0, 0)), 0.068, 0.07, 32)
    cilx(b1.b('grafite', True), E + Vector((0.149, 0, 0)), 0.056, 0.01, 32)
    for k in range(8):
        a = k * PI / 4
        cil(b1.b('aco'), E + Vector((0.152, math.cos(a) * 0.06, math.sin(a) * 0.06)), 0.007, 0.01, X, 6)
    for dz in (0.035, -0.035):
        cil(b1.b('cobre', True), E + Vector((0.11, -0.072, dz)), 0.01, 0.02, Y, 6)
        hh = [Vector((0.075, -0.035, S.z + 0.20))] + [Vector((0.075, -0.035 + dz * 0.3, S.z + f)) for f in (0.28, 0.36)] + \
             bezier(Vector((0.075, -0.035 + dz * 0.3, E.z - 0.12)), Vector((0.09, -0.06, E.z - 0.08)), Vector((0.11, -0.10, E.z + dz)), Vector((0.11, -0.082, E.z + dz)), 6)
        mangueira(b1.b('borracha', True), hh, 0.009)
    caixa_de(b1.b('grafite'), (0.064, -0.05, S.z + 0.12), (0.09, -0.02, S.z + 0.20))
    # ---------------------------------------------------------- braço 2: viga-caixão com treliça de tirantes por cima
    b2 = Parte('empilhador_braco2', b1, E)
    cilx(b2.b('amarelo', True), E, 0.058, 0.07, 24)
    caixa_de(b2.b('amarelo'), (-0.035, E.y + 0.04, E.z - 0.04), (0.035, W.y - 0.07, E.z + 0.035))
    caixa_de(b2.b('grafite'), (-0.038, E.y + 0.04, E.z - 0.043), (0.038, W.y - 0.07, E.z - 0.035))
    caixa_de(b2.b('listras'), (-0.0355, E.y + 0.25, E.z - 0.03), (-0.035, E.y + 0.36, E.z + 0.025))
    caixa_de(b2.b('listras'), (0.035, E.y + 0.25, E.z - 0.03), (0.0355, E.y + 0.36, E.z + 0.025))
    km = E + Vector((0, 0.30, 0.13))
    caixa_de(b2.b('grafite'), (-0.012, km.y - 0.012, E.z + 0.035), (0.012, km.y + 0.012, km.z))            # montante
    for p_ in (E + Vector((0, 0.07, 0.035)), W + Vector((0, -0.09, 0.035))):
        tubo(b2.b('cromo', True), p_, km, 0.007, 10)
        caixa_de(b2.b('aco'), (p_.x - 0.012, p_.y - 0.012, p_.z), (p_.x + 0.012, p_.y + 0.012, p_.z + 0.012))
    cilx(b2.b('aco', True), km, 0.014, 0.04, 12)
    for s in (-1, 1):
        caixa_de(b2.b('grafite'), (s * 0.044 - 0.006, W.y - 0.075, W.z - 0.03), (s * 0.044 + 0.006, W.y + 0.02, W.z + 0.03))
    caixa_de(b2.b('grafite'), (-0.05, W.y - 0.08, W.z - 0.03), (0.05, W.y - 0.07, W.z + 0.03))
    hh = [E + Vector((0.05, 0.06, 0.03)), E + Vector((0.045, 0.12, 0.05))] + [E + Vector((0.045, f, 0.05)) for f in (0.2, 0.3, 0.4, 0.48)] + [W + Vector((0.035, -0.06, 0.035))]
    mangueira(b2.b('borracha', True), hh, 0.009)
    abracadeiras(b2.b('aco', True), hh, 0.009, 2)
    # ---------------------------------------------------------- garra-gaiola: prensa compactadora + garfos de pinça
    g = Parte('empilhador_garra', b2, W)
    zb = W.z - E_FUNDO
    cilx(g.b('aco', True), W, 0.04, 0.084, 24)
    cilz(g.b('cromo', True), W + Vector((0, 0, -0.05)), 0.022, 0.05, 16)
    cilz(g.b('grafite', True), W + Vector((0, 0, -0.0825)), 0.055, 0.015, 32)
    caixa_de(g.b('grafite'), (W.x - 0.11, W.y - 0.08, W.z - 0.11), (W.x + 0.11, W.y + 0.08, W.z - 0.09))
    caixa_de(g.b('amarelo'), (W.x - 0.112, W.y - 0.082, W.z - 0.106), (W.x + 0.112, W.y + 0.082, W.z - 0.096))
    for sx in (-1, 1):
        for sy in (-1, 1):
            caixa_de(g.b('aco'), (sx * 0.064 - 0.007, W.y + sy * 0.064 - 0.007, zb), (sx * 0.064 + 0.007, W.y + sy * 0.064 + 0.007, W.z - 0.11))
            caixa_de(g.b('grafite'), (sx * 0.064 - 0.009, W.y + sy * 0.064 - 0.009, zb), (sx * 0.064 + 0.009, W.y + sy * 0.064 + 0.009, zb + 0.012))
        caixa_de(g.b('aco'), (-0.071, W.y + sx * 0.064 - 0.005, W.z - 0.205), (0.071, W.y + sx * 0.074, W.z - 0.193))   # cintas ±Y
        caixa_de(g.b('aco'), (-0.071, W.y + sx * 0.064 - 0.005, zb + 0.06), (0.071, W.y + sx * 0.074, zb + 0.072))
    caixa_de(g.b('listras'), (-0.05, W.y + 0.0745, W.z - 0.25), (0.05, W.y + 0.0755, W.z - 0.21))
    for s in (-1, 1):                                                          # camisas dos compactadores
        cilz(g.b('amarelo', True), W + Vector((s * 0.087, 0, -0.005)), 0.018, 0.17, 24)
        cilz(g.b('grafite', True), W + Vector((s * 0.087, 0, 0.078)), 0.021, 0.012, 24)
        cilz(g.b('grafite', True), W + Vector((s * 0.087, 0, -0.084)), 0.024, 0.012, 24)
        cil(g.b('cobre', True), W + Vector((s * 0.087, 0.022, 0.06)), 0.006, 0.014, Y, 6)
    caixa_de(g.b('grafite'), (W.x - 0.04, W.y - 0.08, W.z - 0.09), (W.x + 0.04, W.y - 0.06, W.z - 0.06))      # válvulas
    for s in (-1, 1):
        hh = bezier(W + Vector((s * 0.04, -0.07, -0.07)), W + Vector((s * 0.06, -0.07, -0.05)), W + Vector((s * 0.087, -0.03, 0.08)), W + Vector((s * 0.087, 0.022, 0.06)), 8)
        mangueira(g.b('borracha', True), hh[:-1], 0.005)
    for k in range(4):                                                         # contador de itens
        cil(g.b('grafite', True), W + Vector((-0.045 + k * 0.03, 0.083, -0.10)), 0.009, 0.004, Y, 12)
        cil(g.b('cont%d' % k, True), W + Vector((-0.045 + k * 0.03, 0.0855, -0.10)), 0.006, 0.003, Y, 12)
    # cilindros das pinças (fixos na gaiola, lados ±X)
    for s in (-1, 1):
        cilx(g.b('aco', True), Vector((s * 0.12, W.y, zb + 0.025)), 0.014, 0.04, 16)
        cilx(g.b('grafite', True), Vector((s * 0.142, W.y, zb + 0.025)), 0.016, 0.008, 16)
        caixa_de(g.b('aco'), (s * 0.071 if s > 0 else -0.10, W.y + 0.022, zb + 0.008), (0.10 if s > 0 else -0.071, W.y + 0.036, zb + 0.04))
        caixa_de(g.b('aco'), (s * 0.071 if s > 0 else -0.10, W.y - 0.036, zb + 0.008), (0.10 if s > 0 else -0.071, W.y - 0.022, zb + 0.04))
    pincas = []
    for s in (-1, 1):
        pc = Parte('empilhador_pinca_%d' % s, g, Vector((s * 0.055, W.y, zb)))
        for yy in (-0.028, 0.028):
            caixa_de(pc.b('aco'), (s * 0.051 if s > 0 else -0.059, W.y + yy - 0.01, zb + 0.004), (0.059 if s > 0 else -0.051, W.y + yy + 0.01, zb + 0.045))
            caixa_de(pc.b('borracha'), (s * 0.0505 if s > 0 else -0.0515, W.y + yy - 0.009, zb + 0.006), (0.0515 if s > 0 else -0.0505, W.y + yy + 0.009, zb + 0.04))
        caixa_de(pc.b('grafite'), (s * 0.059 if s > 0 else -0.067, W.y - 0.04, zb + 0.004), (0.067 if s > 0 else -0.059, W.y + 0.04, zb + 0.045))
        cilx(pc.b('cromo', True), Vector((s * 0.085, W.y, zb + 0.025)), 0.006, 0.04, 10)
        pincas.append((pc, s))
    # prensa: chapa dentro da gaiola, abas por fora entre as cantoneiras, hastes subindo até as camisas
    pr = Parte('empilhador_prensa', g, W + Vector((0, 0, E_PRENSA0)))
    zp0 = W.z + E_PRENSA0
    caixa_de(pr.b('grafite'), (-0.056, W.y - 0.056, zp0), (0.056, W.y + 0.056, zp0 + 0.012))
    caixa_de(pr.b('borracha'), (-0.05, W.y - 0.05, zp0 - 0.003), (0.05, W.y + 0.05, zp0))
    for s in (-1, 1):
        caixa_de(pr.b('amarelo'), (s * 0.056 if s > 0 else -0.097, W.y - 0.012, zp0), (0.097 if s > 0 else -0.056, W.y + 0.012, zp0 + 0.012))
        cilz(pr.b('cromo', True), Vector((s * 0.087, W.y, zp0 + 0.012 + 0.095)), 0.008, 0.19, 12)
    # ---------------------------------------------------------- pistão de elevação na frente do braço 1
    pst = pistao('empilhador_pistao', giro, b1, A, P0, 0.034, 0.26, 0.016, 0.25)
    # ---------------------------------------------------------- uso pesado
    remendo(giro, (0.1315, 0.06, Zg + 0.105), Y, Z, 0.08, 0.05, X)
    remendo(b1, (-0.064, 0.0, S.z + 0.30), -Y, Z, 0.06, 0.09, -X)
    amassado(giro.b('ferro', True), (0.1595, -0.26, Zg + 0.12), Y, Z, 0.04, 0.14, 0.006, ((0.1, 0.2, 0.25),))
    amassado(giro.b('amarelo', True), (-0.04, 0.1405, Zg + 0.11), -X, Z, 0.12, 0.04, 0.004, ((-0.2, 0.1, 0.2),))
    amassado(base.b('aco', True), (0.25, 0.20, Z0 + 0.0305), X, Y, 0.12, 0.10, 0.004, ((0.1, 0.0, 0.22),))
    caixa_de(giro.b('primer'), (-0.1395, -0.24, Zg + 0.03), (-0.13, -0.19, Zg + 0.21))          # placa trocada
    cilx(b1.b('primer', True), E + Vector((0.11, 0, 0)), 0.0685, 0.025, 32)
    fiacao(giro, (0.05, 0.12, Zg + 0.17), Vector((-0.02, 0.02, 0.02)), (0.03, 0.13, Zg + 0.14))
    fiacao(g, W + Vector((0.04, -0.08, -0.08)), Vector((0.0, -0.02, 0.0)), W + Vector((0.07, -0.08, -0.1)))
    for (x, y, r) in ((0.10, -0.25, 0.05), (-0.25, 0.10, 0.06)):
        mancha(base.b('oleo'), (x, y), r, Z0 + 0.0312)
    estencil('ST-04  5582-E', giro, (0.0, -0.3435, Zg + 0.20), -Y, Z, 0.016)
    estencil('4 x', b2, (0.0355, E.y + 0.16, E.z), X, Y, 0.02)
    estencil('0907', b1, (0.0645, 0.0, S.z + 0.28), X, Z, 0.012)
    partes = [raiz, base, giro, pinhao, b1, b2, g, pr, pst['cam'], pst['has']] + [p for p, _ in pincas]
    for p in partes:
        p.fechar()
    itens = [item_novo('empilhador_item_%d' % k, raiz.e) for k in range(4)]
    return dict(nome='empilhador', raiz=raiz, giro=giro, b1=b1, b2=b2, g=g, pinhao=pinhao, pincas=pincas, prensa=pr,
                pists=[pst], itens=itens, S=S, L1=L1, L2=L2, relacao=0.19 / 0.03, col=COL, O=Vector(O))


def animar_empilhador(A):
    zp = TOPO_ESTEIRA + 0.001 + E_FUNDO                        # fundo da gaiola rente à lona
    zh = zp + 0.10
    rr, zr = 0.50, 0.95
    TD = [0.02 + 0.105 * k for k in range(4)]                  # início de cada mergulho
    TC = [t + 0.04 for t in TD]                                # pinça fecha (item entra por baixo)
    tab = [(0.0, E_R, zh, PI)]
    for t in TD:
        tab += [(t, E_R, zh, PI), (t + 0.035, E_R, zp, PI), (t + 0.045, E_R, zp, PI), (t + 0.08, E_R, zh, PI)]
    tab += [(0.50, rr, zr, 0.85 * PI), (0.60, rr, zr, 0.15 * PI), (0.67, E_R, zh, 0.0), (0.705, E_R, zp, 0.0),
            (0.735, E_R, zp, 0.0), (0.775, E_R, zh, 0.0), (0.86, rr, zr, 0.5 * PI), (0.95, E_R, zh, PI), (1.0, E_R, zh, PI)]
    SOLTA = 0.72
    zc = TOPO_ESTEIRA + H_ITEM / 2
    for q in range(1, QUADROS + 1):
        u = (q - 1) / QUADROS
        r, z, yaw = trajetoria(u, tab)
        f1, f2 = ik2(A, r, z)
        posar2(A, yaw, f1, f2, q)
        Wp = Vector((-r * math.sin(yaw), r * math.cos(yaw), z))
        fundo = z - E_FUNDO
        dentro = [k for k in range(4) if TC[k] <= u < SOLTA]   # já na gaiola (o último pego fica embaixo)
        n = len(dentro)
        # pinças: abrem quando o item novo empurra a pilha para cima, e na entrega
        aberto = 0.0
        for k in range(4):
            if TD[k] + 0.025 <= u < TC[k]:
                aberto = 1.0
        if u >= SOLTA or u < TC[0]:
            aberto = 1.0
        for pc, s in A['pincas']:
            pc.e.location = pc.pivo - A['g'].pivo + Vector((s * 0.012 * aberto, 0, 0))
            chave(pc.e, 'location', q)
        # pilha na gaiola: se um item novo está entrando por baixo, a pilha sobe junto
        base_pilha = fundo
        for k in range(4):
            if TD[k] <= u < TC[k] and n > 0:
                base_pilha = max(fundo, TOPO_ESTEIRA + H_ITEM)
        topo = base_pilha + 0.05 * n if n else fundo
        # prensa compactadora: encosta no topo e dá um golpe logo depois de cada item entrar
        golpe = 0.0
        for t in TC:
            x = (u - t - 0.005) / 0.045
            if 0 <= x <= 1:
                golpe = max(golpe, math.sin(x * PI))
        folga = 0.022 * (1 - golpe) + 0.002
        if u >= SOLTA or n == 0:
            folga = 0.03
        pz = min(max(topo - z, E_PRENSA0) + folga, -0.125)
        A['prensa'].e.location = A['prensa'].pivo - A['g'].pivo + Vector((0, 0, pz - E_PRENSA0))
        chave(A['prensa'].e, 'location', q)
        # contador de LEDs
        for k in range(4):
            chave_emis(M['cont%d' % k], 9.0 if k < n else 0.0, q)
        # itens
        for k, it in enumerate(A['itens']):
            vis = True
            rot = PI
            if k in dentro:
                nivel = sum(1 for j in dentro if j > k)
                p = Vector((Wp.x, Wp.y, base_pilha + 0.025 + 0.05 * nivel))
                rot = yaw
            elif u >= SOLTA:                                      # pilha entregue na esteira norte, sai andando
                nivel = 3 - k
                t = suave((u - 0.78) / 0.14)
                p = Vector((0, E_R + 0.70 * t, zc + 0.05 * nivel))
                vis = p.y < 1.44
                rot = 0.0
                if u >= 0.92:                                    # nova fila chegando pelo sul
                    t2 = suave((u - 0.92) / 0.08)
                    p = Vector((0, -E_R - 0.15 * k - 0.6 * (1 - t2), zc))
                    vis = p.y > -1.44
                    rot = PI
            else:                                                  # na fila da esteira sul
                feitos = sum(suave((u - TD[j] - 0.06) / 0.04) for j in range(4) if j < k)
                p = Vector((0, -E_R - 0.15 * (k - feitos), zc))
            it.location, it.rotation_euler = p, (0, 0, rot)
            chave(it, 'location', q)
            chave(it, 'rotation_euler', q)
            chave_vis(it, vis, q)


# =================================================================== BRAÇO QUÂNTICO
# Montado no referencial do braço (+Y = para onde a lança aponta) e girado 180°: a lança aponta para o sul.
Q_LARG = (0.15, 0.125, 0.10, 0.08, 0.06)
Q_EMAX = 0.5                                                   # extensão por estágio (4 estágios: +2 m)
Q_NI = 40                                                      # itens no fluxo
Q_ZC = TOPO_ESTEIRA + H_ITEM / 2


def q_ini(k):
    return 0.085 if k == 0 else 0.09 + 0.01 * k


def q_fim(k):
    return 0.76 + 0.025 * k


def braco_quantico(O):
    global COL
    COL = bpy.data.collections.new('quantico')
    sc.collection.children.link(COL)
    raiz = Parte('quantico_raiz', None, (0, 0, 0))
    raiz.e.location = O
    laje(raiz, ((0.3, 0.3, 0.06),))
    est = Parte('quantico_esteiras', raiz, (0, 0, 0))
    for cy in (-1.0, -2.0, -3.0, 1.0):
        esteira(est, cy)
    est.fechar()
    rot = Parte('quantico_rot', raiz, (0, 0, 0))
    rot.e.rotation_euler = (0, 0, PI)
    Zg = Z0 + 0.30
    S = Vector((0, 0, Zg + 0.24))
    E = S + Vector((0, 0, 0.62))
    Ez = E.z
    ZC = Ez + 0.22                                             # altura do fluxo por cima da lança
    # ---------------------------------------------------------- base pesada
    base = Parte('quantico_base', rot, (0, 0, 0))
    caixa_de(base.b('aco'), (-0.44, -0.44, Z0), (0.44, 0.44, Z0 + 0.035))
    bm, bmn = base.b('aco', True), base.b('aco')
    for k in range(16):
        t = k / 16 * 4
        lado, f = int(t), t - int(t)
        s_ = -0.40 + 0.8 * f
        p = [(s_, -0.40), (0.40, s_), (-s_, 0.40), (-0.40, -s_)][lado]
        cilz(bm, (p[0], p[1], Z0 + 0.055), 0.011, 0.06, 10)
        cilz(bmn, (p[0], p[1], Z0 + 0.038), 0.024, 0.006, 16)
        cil(bmn, Vector((p[0], p[1], Z0 + 0.05)), 0.02, 0.018, Z, 6)
    cilz(base.b('ferro'), (0, 0, Z0 + 0.035 + 0.11), 0.22, 0.22, 8)
    caixa_de(base.b('listras'), (-0.09, 0.2, Z0 + 0.06), (0.09, 0.207, Z0 + 0.12))
    bm = base.b('grafite')
    for k in range(8):
        a = k * PI / 4 + PI / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        cunha(bm, d * 0.20 + Vector((0, 0, Z0 + 0.035)), d * 0.41 + Vector((0, 0, Z0 + 0.035)), d * 0.20 + Vector((0, 0, Z0 + 0.22)), 0.018, Vector((-d.y, d.x, 0)))
    cilz(base.b('grafite', True), (0, 0, Z0 + 0.265), 0.245, 0.03, 48)
    parafusos(base.b('aco'), (0, 0, 0), 0.228, 16, 0.011, 0.012, Z0 + 0.28)
    cilz(base.b('grafite', True), (0, 0, Zg - 0.015), 0.232, 0.03, 48)
    dentes(base.b('aco'), (0, 0, 0), 0.24, 64, 0.018, 0.011, 0.028, Zg - 0.015)
    # caixa de força no chão com eletrocalha até o pedestal
    caixa_de(base.b('grafite'), (0.25, 0.22, Z0 + 0.035), (0.42, 0.42, Z0 + 0.20))
    caixa_de(base.b('zarcao'), (0.248, 0.218, Z0 + 0.16), (0.422, 0.422, Z0 + 0.175))
    bm = base.b('aluminio')
    for k in range(6):
        y = 0.24 + k * 0.03
        caixa_de(bm, (0.42, y - 0.004, Z0 + 0.06), (0.45, y + 0.004, Z0 + 0.17))
    cil(base.b('led_violeta'), Vector((0.248, 0.38, Z0 + 0.13)), 0.007, 0.006, X, 10)
    caixa_de(base.b('aco'), (0.17, 0.27, Z0 + 0.035), (0.25, 0.33, Z0 + 0.06))                       # eletrocalha
    for k in range(3):
        pts = bezier(Vector((0.25, 0.28 + k * 0.02, Z0 + 0.10)), Vector((0.20, 0.28 + k * 0.02, Z0 + 0.07)),
                     Vector((0.17, 0.20 + k * 0.01, Z0 + 0.10)), Vector((0.14, 0.15 + k * 0.012, Z0 + 0.14)), 8)
        mangueira(base.b('cabo_laranja' if k != 1 else 'borracha', True), pts, 0.012)
    # ---------------------------------------------------------- giro: plataforma, corpo, servos, capacitores, travessa
    giro = Parte('quantico_giro', base, (0, 0, Zg))
    cilz(giro.b('grafite', True), (0, 0, Zg + 0.02), 0.26, 0.04, 48)
    caixa_de(giro.b('ferro'), (-0.23, -0.16, Zg + 0.04), (0.23, 0.14, Zg + 0.17))
    caixa_de(giro.b('zarcao'), (-0.2315, -0.1615, Zg + 0.12), (0.2315, 0.1415, Zg + 0.14))
    caixa_de(giro.b('grafite'), (-0.34, 0.14, Zg + 0.04), (0.34, 0.24, Zg + 0.08))                  # travessa
    caixa_de(giro.b('listras'), (-0.34, 0.24, Zg + 0.045), (0.34, 0.244, Zg + 0.075))
    caixa_de(giro.b('grafite'), (-0.22, -0.31, Zg + 0.04), (0.22, -0.16, Zg + 0.07))                 # convés traseiro
    for k in range(4):                                                         # banco de capacitores
        c = Vector((-0.15 + k * 0.1, -0.24, Zg + 0.07))
        cilz(giro.b('aco', True), c + Vector((0, 0, 0.11)), 0.045, 0.22, 32)
        cilz(giro.b('cap_v', True), c + Vector((0, 0, 0.13)), 0.0455, 0.05, 32)
        cilz(giro.b('grafite', True), c + Vector((0, 0, 0.225)), 0.047, 0.012, 32)
        for dx in (-0.018, 0.018):
            cilz(giro.b('cobre', True), c + Vector((dx, 0, 0.24)), 0.008, 0.02, 8)
        anel(giro.b('grafite', True), c + Vector((0, 0, 0.03)), 0.046, 0.004, Z, 32, 6)
    caixa_de(giro.b('cobre'), (-0.18, -0.248, Zg + 0.305), (0.18, -0.232, Zg + 0.312))               # barramento
    caixa_de(giro.b('cobre'), (-0.18, -0.248, Zg + 0.290), (-0.165, -0.232, Zg + 0.312))
    for x in (-0.09, 0.09):                                                    # mancais do ombro
        caixa_de(giro.b('ferro'), (x - 0.013 + (0.003 if x > 0 else -0.003), -0.09, Zg + 0.17), (x + 0.013 + (0.003 if x > 0 else -0.003), 0.09, S.z + 0.07))
        cunha(giro.b('ferro'), (x, -0.09, Zg + 0.17), (x, -0.16, Zg + 0.17), (x, -0.09, S.z), 0.026, X)
    cilx(giro.b('cromo', True), S, 0.03, 0.22, 16)
    helices = []
    for s in (-1, 1):                                                          # servos do ombro, sobre pedestais
        caixa_de(giro.b('grafite'), (min(s * 0.12, s * 0.22), -0.05, Zg + 0.17), (max(s * 0.12, s * 0.22), 0.05, S.z - 0.072))
        cv = servo_x(giro, (s * 0.105, 0, S.z), s, 0.072, 0.11)
        helices.append((helice('quantico_helice_%d' % s, giro, cv, 'X', 0.055), 0))
        pts = bezier(Vector((s * 0.15, -0.248, Zg + 0.30)), Vector((s * 0.2, -0.20, Zg + 0.36)), Vector((s * 0.2, -0.10, S.z + 0.10)), Vector((s * 0.17, -0.03, S.z + 0.06)), 10)
        mangueira(giro.b('cabo_laranja', True), pts, 0.012)
        abracadeiras(giro.b('aco', True), pts, 0.012, 3)
    # motor de giro (pinhão na coroa) no lado +X, à frente
    mg = Vector((0.28, -0.05, 0))
    caixa_de(giro.b('ferro'), (0.23, -0.09, Zg + 0.04), (0.33, -0.01, Zg + 0.065))
    cilz(giro.b('grafite', True), mg + Vector((0, 0, Zg + 0.13)), 0.042, 0.12, 24)
    aletas(giro.b('grafite', True), mg + Vector((0, 0, Zg + 0.085)), Z, 0.052, 6, 0.016)
    cilz(giro.b('zarcao', True), mg + Vector((0, 0, Zg + 0.198)), 0.044, 0.014, 24)
    cilz(giro.b('aco', True), mg + Vector((0, 0, Zg + 0.02)), 0.018, 0.05, 16)
    pinhao = Parte('quantico_pinhao', giro, mg + Vector((0, 0, Zg - 0.015)))
    cilz(pinhao.b('aco', True), pinhao.pivo, 0.028, 0.026, 16)
    dentes(pinhao.b('aco'), pinhao.pivo, 0.033, 10, 0.012, 0.01, 0.026, 0)
    # olhais das camisas na travessa
    A_ = S + Vector((0, 0.17, -0.13))
    XP = 0.30
    for s in (-1, 1):
        for dx in (-0.045, 0.045):
            caixa_de(giro.b('ferro'), (s * XP + dx - 0.008, A_.y - 0.045, Zg + 0.08), (s * XP + dx + 0.008, A_.y + 0.045, A_.z + 0.03))
        cilx(giro.b('cromo', True), (s * XP, A_.y, A_.z), 0.016, 0.115, 12)
    # ---------------------------------------------------------- braço 1: coluna-caixão pesada
    b1 = Parte('quantico_braco1', giro, S)
    cilx(b1.b('grafite', True), S, 0.075, 0.15, 32)
    caixa_de(b1.b('ferro'), (-0.07, -0.07, S.z + 0.04), (0.07, 0.07, Ez - 0.06))
    for z in (S.z + 0.12, S.z + 0.30, S.z + 0.50):
        caixa_de(b1.b('grafite'), (-0.074, -0.074, z), (0.074, 0.074, z + 0.035))
    for s in (-1, 1):
        caixa_de(b1.b('zarcao'), (s * 0.07 - 0.003, -0.04, S.z + 0.16), (s * 0.07 + 0.003, 0.04, S.z + 0.29))
        cunha(b1.b('ferro'), (s * 0.06, 0.07, Ez - 0.20), (s * 0.06, 0.07, Ez - 0.06), (s * 0.06, 0.12, Ez - 0.06), 0.016, X)
    P0 = S + Vector((0, -0.11, 0.44))
    caixa_de(b1.b('ferro'), (-0.06, -0.14, P0.z - 0.05), (0.06, -0.07, P0.z + 0.05))
    cilx(b1.b('cromo', True), P0, 0.02, 2 * XP + 0.12, 12)
    for s in (-1, 1):
        cilx(b1.b('grafite', True), P0 + Vector((s * 0.10, 0, 0)), 0.03, 0.06, 16)
    cilx(b1.b('grafite', True), E, 0.085, 0.15, 32)
    for s in (-1, 1):
        cil(b1.b('aco'), E + Vector((s * 0.08, 0, 0)), 0.035, 0.012, X, 6)
    # eletrocalha com cabos subindo pelo braço 1 (lado -X)
    caixa_de(b1.b('aco'), (-0.10, -0.03, S.z + 0.10), (-0.075, 0.03, Ez - 0.10))
    for k, mat in enumerate(('cabo_laranja', 'borracha', 'cabo_laranja')):
        x = -0.088
        pts = [Vector((x, -0.018 + k * 0.018, S.z + 0.12 + j * 0.1)) for j in range(5)]
        mangueira(b1.b(mat, True), pts, 0.006)
    for z in (S.z + 0.2, S.z + 0.4):
        caixa_de(b1.b('grafite'), (-0.104, -0.034, z), (-0.073, 0.034, z + 0.012))
    # ---------------------------------------------------------- braço 2: lança telescópica de cinco seções
    b2 = Parte('quantico_braco2', b1, E)
    for s in (-1, 1):                                                          # bochechas na articulação
        caixa_de(b2.b('ferro'), (s * 0.077 if s > 0 else -0.097, -0.07, Ez - 0.07), (0.097 if s > 0 else -0.077, 0.14, Ez + 0.07))
        cilx(b2.b('aco', True), E + Vector((s * 0.1, 0, 0)), 0.05, 0.01, 24)
    cores = ('grafite', 'amarelo', 'ferro', 'amarelo', 'aco')
    estagios = [b2]
    for k in range(1, 5):
        estagios.append(Parte('quantico_estagio%d' % k, b2, E))
    for k in range(5):
        w = Q_LARG[k] / 2
        st = estagios[k]
        caixa_de(st.b(cores[k]), (-w, q_ini(k), Ez - w), (w, q_fim(k), Ez + w))
        if k < 4:
            caixa_de(st.b('grafite'), (-w - 0.006, q_fim(k) - 0.025, Ez - w - 0.006), (w + 0.006, q_fim(k), Ez + w + 0.006))   # boca
            caixa_de(st.b('borracha'), (-w + 0.003, q_fim(k), Ez - w + 0.003), (w - 0.003, q_fim(k) + 0.003, Ez - w + 0.012))
        if k in (1, 3):
            caixa_de(st.b('listras'), (w, q_fim(k) - 0.20, Ez - w * 0.6), (w + 0.002, q_fim(k) - 0.10, Ez + w * 0.6))
    # cilindro telescópico embaixo da lança (camisa amarela + 4 hastes cromadas)
    zt = Ez - 0.12
    caixa_de(b2.b('ferro'), (-0.02, 0.10, zt), (0.02, 0.14, Ez - 0.075))
    tubos = [b2] + [Parte('quantico_tubo%d' % k, b2, E) for k in range(1, 5)]
    for k in range(5):
        r = 0.032 - 0.005 * k
        cily(tubos[k].b('amarelo' if k == 0 else 'cromo', True), Vector((0, (0.10 + 0.03 * k + 0.76 + 0.02 * k) / 2, zt)), r, 0.76 + 0.02 * k - 0.10 - 0.03 * k, 32)
        if k < 4:
            cily(tubos[k].b('grafite', True), Vector((0, 0.76 + 0.02 * k - 0.008, zt)), r + 0.004, 0.016, 32)
    caixa_de(estagios[4].b('ferro'), (-0.02, q_fim(4) - 0.02, zt - 0.01), (0.02, q_fim(4), Ez - 0.025))
    # carretel de cabo no lado -X da lança: gira conforme a lança estica
    dr = Vector((-0.125, 0.42, Ez))
    caixa_de(b2.b('ferro'), (-0.098, 0.38, Ez - 0.02), (-0.075, 0.46, Ez + 0.02))
    car = Parte('quantico_carretel', b2, dr)
    cilx(car.b('grafite', True), dr, 0.05, 0.05, 32)
    for s in (-1, 1):
        cilx(car.b('zarcao', True), dr + Vector((s * 0.028, 0, 0)), 0.07, 0.006, 32)
    for k in range(5):
        anel(car.b('borracha', True), dr + Vector((-0.02 + k * 0.01, 0, 0)), 0.056, 0.0055, X, 32, 6)
    caixa(car.b('aco'), dr + Vector((-0.032, 0, 0.0)), (0.004, 0.11, 0.012))                         # trava (mostra o giro)
    cb = Parte('quantico_cabo', b2, dr + Vector((0, 0.0, -0.062)))
    cily(cb.b('borracha', True), cb.pivo + Vector((0, (q_fim(4) - 0.01 - dr.y) / 2, 0)), 0.006, q_fim(4) - 0.01 - dr.y, 10)
    caixa_de(estagios[4].b('ferro'), (-0.13, q_fim(4) - 0.03, Ez - 0.07), (-0.03, q_fim(4) - 0.01, Ez - 0.05))   # garra do cabo
    # servo do cotovelo (-X) e mangueira até a ponta
    servo_x(b1, (-0.10, 0, Ez), -1, 0.06, 0.08)
    helices.append((helice('quantico_helice_cot', b1, E + Vector((-0.10 - 0.008 - 0.08 - 0.028, 0, 0)), 'X', 0.045), 0))
    # ---------------------------------------------------------- garra: emissor de anéis na ponta (campo de levitação)
    ye = 1.0
    g = Parte('quantico_garra', b2, Vector((0, ye, Ez)))
    caixa_de(g.b('ferro'), (-0.03, q_fim(4), Ez - 0.03), (0.03, ye - 0.11 + 0.012, Ez + 0.03))
    for zr_ in (Ez - 0.14, Ez + 0.10):
        anel(g.b('ferro', True), Vector((0, ye, zr_)), 0.10, 0.016, Z, 48, 10)
        anel(g.b('labio', True), Vector((0, ye, zr_)), 0.083, 0.005, Z, 48, 8)
        for k in range(8):
            a = k * PI / 4 + PI / 8
            caixa(g.b('aco'), Vector((math.cos(a) * 0.10, ye + math.sin(a) * 0.10, zr_)), (0.016, 0.012, 0.038), Matrix.Rotation(a, 3, 'Z'))
    for a in (-PI / 2, PI / 6, 5 * PI / 6):
        pc = Vector((math.cos(a) * 0.115, ye + math.sin(a) * 0.115, 0))
        cilz(g.b('aco', True), pc + Vector((0, 0, Ez - 0.02)), 0.012, 0.30, 12)
        for j in range(5):
            anel(g.b('cobre', True), pc + Vector((0, 0, Ez - 0.08 + j * 0.026)), 0.016, 0.004, Z, 16, 6)
    tubo(g.b('aco', True), Vector((0, ye - 0.115, Ez + 0.03)), Vector((0, ye - 0.115, Ez + 0.10)), 0.01, 10)
    cil(g.b('led_violeta'), Vector((0.0, ye - 0.128, Ez - 0.06)), 0.006, 0.005, -Y, 10)
    luz = bpy.data.lights.new('quantico_luz_ponta', 'POINT')
    luz.color = (0.6, 0.25, 1.0)
    luz.energy = 25.0
    luz.shadow_soft_size = 0.1
    lo = bpy.data.objects.new('quantico_luz_ponta', luz)
    COL.objects.link(lo)
    lo.parent = g.e
    lo.location = (0, 0, -0.30)
    # campo: coluna na ponta (desce até a esteira), curva de saída, trecho sobre a lança (estica), descida ao norte
    cz0 = Q_ZC - 0.01
    varredura(g.b('campo'), [Vector((0, ye, cz0 + (Ez + 0.12 - cz0) * t / 12)) for t in range(13)], 0.05, 20, True)
    arco = [Vector((0, ye - 0.10 + 0.10 * math.cos(a), Ez + 0.12 + 0.10 * math.sin(a))) for a in (j * PI / 2 / 8 for j in range(9))]
    varredura(g.b('campo'), arco + [arco[-1] + Vector((0, -0.03, 0))], 0.05, 20)
    cl = Parte('quantico_campo_lanca', b2, Vector((0, -0.20, ZC)))
    varredura(cl.b('campo'), [Vector((0, -0.20 + 1.10 * t / 10, ZC)) for t in range(11)], 0.05, 20)
    DES = bezier(Vector((0, -0.20, ZC)), Vector((0, -0.60, ZC)), Vector((0, -1.0, ZC - 0.40)), Vector((0, -1.0, 0.36)), 24)
    varredura(giro.b('campo'), DES, 0.05, 20)
    # anéis fixos da descida e anel de pouso sobre a esteira norte
    def anel_campo(parte, c, eixo, R=0.095):
        anel(parte.b('ferro', True), c, R, 0.013, eixo, 48, 10)
        anel(parte.b('labio', True), c, R - 0.014, 0.0045, eixo, 48, 8)
        q_ = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
        for k in range(3):
            a = k * 2 * PI / 3 + PI / 2
            d = q_ @ Vector((math.cos(a), math.sin(a), 0))
            caixa(parte.b('aco'), c + d * (R + 0.012), (0.022, 0.022, 0.022), q_ @ Matrix.Rotation(a, 3, 'Z'))
            anel(parte.b('cobre', True), c + d * (R + 0.012) + Vector(eixo).normalized() * 0.0, 0.016, 0.0035, Vector(eixo), 16, 6)
    for t in (0.25, 0.55, 0.85):
        i = int(t * 24)
        anel_campo(giro, DES[i], (DES[i + 1] - DES[i - 1]).normalized())
    anel_campo(giro, Vector((0, -1.0, 0.42)), Z, 0.10)
    # rastro de anéis: um anel a cada 0,25 m sobre a lança; os de fora do estágio fixo aparecem quando a lança passa
    rastro = []
    y = 0.30
    while y <= 0.86 + 4 * Q_EMAX:
        an = Parte('quantico_anel_%d' % len(rastro), b2, Vector((0, y, ZC)))
        anel_campo(an, an.pivo, Y)
        rastro.append((an, y))
        y += 0.25
    # ---------------------------------------------------------- pistões de elevação (camisa na travessa, haste no braço 1)
    pists = [pistao('quantico_pistao_%d' % s, giro, b1, A_ + Vector((s * XP, 0, 0)), P0 + Vector((s * XP, 0, 0)), 0.04, 0.38, 0.02, 0.36, 'ferro')
             for s in (-1, 1)]
    # ---------------------------------------------------------- uso pesado
    remendo(giro, (0.2315, 0.02, Zg + 0.08), Y, Z, 0.08, 0.05, X)
    remendo(b1, (0.0, 0.07, S.z + 0.40), X, Z, 0.08, 0.07, Y)
    amassado(giro.b('ferro', True), (-0.10, 0.1405, Zg + 0.10), -X, Z, 0.16, 0.06, 0.005, ((-0.2, 0.1, 0.2), (0.25, -0.2, 0.12)))
    amassado(estagios[0].b('grafite', True), (0.0755, 0.40, Ez), Y, Z, 0.25, 0.1, 0.005, ((0.2, 0.1, 0.15), (-0.25, -0.1, 0.12)))
    amassado(base.b('aco', True), (-0.25, -0.28, Z0 + 0.0355), X, Y, 0.12, 0.08, 0.004, ((0.1, 0.0, 0.22),))
    caixa_de(estagios[2].b('primer'), (-0.0505, 0.40, Ez - 0.05), (0.0505, 0.55, Ez + 0.05))           # seção trocada
    caixa_de(giro.b('primer'), (-0.05, -0.31, Zg + 0.07), (0.05, -0.30, Zg + 0.10))
    fiacao(giro, (0.17, -0.16, Zg + 0.15), Vector((0.0, -0.03, 0.02)), (0.12, -0.165, Zg + 0.13))
    fiacao(base, (0.25, 0.30, Z0 + 0.18), Vector((-0.03, 0.0, 0.02)), (0.25, 0.26, Z0 + 0.15))
    for (x, y_, r) in ((0.15, -0.30, 0.06), (-0.30, 0.15, 0.05), (0.32, 0.0, 0.04)):
        mancha(base.b('oleo'), (x, y_), r, Z0 + 0.0362)
    estencil('QX-09  0001-V', giro, (0.0, 0.2445, Zg + 0.06), Y, Z, 0.014)
    estencil('CAMPO', estagios[0], (0.0755, 0.62, Ez), X, Y, 0.03)
    estencil('5508', b1, (-0.0705, 0.0, S.z + 0.08), -X, Z, 0.014)
    partes = [raiz, rot, base, giro, pinhao, b1, b2, g, cl, car, cb] + estagios[1:] + tubos[1:] + [h for h, _ in helices] + \
             [a for a, _ in rastro] + [p['cam'] for p in pists] + [p['has'] for p in pists]
    for p in partes:
        p.fechar()
    # itens: uma malha só, várias cópias; cada um com halo violeta para quando está no campo
    proto = item_novo('quantico_item_0', raiz.e)
    bmh = bmesh.new()
    bmesh.ops.create_uvsphere(bmh, u_segments=16, v_segments=8, radius=0.085)
    for v in bmh.verts:
        v.co.z *= 0.6
    hal = novo_obj('quantico_item_0_halo', bmh, 'halo', proto, chanfro=False)
    itens = [(proto, hal)]
    marca = [c for c in proto.children if c.name.endswith('_marca')][0]
    for i in range(1, Q_NI):
        o = bpy.data.objects.new('quantico_item_%d' % i, proto.data)
        COL.objects.link(o)
        o.parent = raiz.e
        o.modifiers.new('chanfro', 'BEVEL').width = 0.0025
        mk = bpy.data.objects.new('quantico_item_%d_marca' % i, marca.data)
        COL.objects.link(mk)
        mk.parent = o
        h = bpy.data.objects.new('quantico_item_%d_halo' % i, hal.data)
        COL.objects.link(h)
        h.parent = o
        itens.append((o, h))
    return dict(nome='quantico', raiz=raiz, giro=giro, b1=b1, b2=b2, g=g, estagios=estagios, tubos=tubos, car=car, cb=cb,
                cl=cl, rastro=rastro, helices=helices, pists=pists, itens=itens, S=S, E=E, ZC=ZC, DES=DES, ye=ye,
                col=COL, O=Vector(O))


def q_ext(fr):
    if fr < 0.18:
        return 0.0
    if fr < 0.42:
        return Q_EMAX * suave((fr - 0.18) / 0.24)
    if fr < 0.72:
        return Q_EMAX
    if fr < 0.94:
        return Q_EMAX * (1 - suave((fr - 0.72) / 0.22))
    return 0.0


def q_caminho(A, e):
    """Caminho do fluxo no referencial do braço (y, z): esteira sul → coluna → curva → sobre a lança → descida → norte."""
    ye = A['ye'] + 4 * e
    Ez, ZC = A['E'].z, A['ZC']
    seg = [(0, [Vector((0, 3.55, Q_ZC)), Vector((0, ye, Q_ZC))])]
    seg.append((1, [Vector((0, ye, Q_ZC)), Vector((0, ye, Ez + 0.12))]))
    seg.append((1, [Vector((0, ye - 0.10 + 0.10 * math.cos(a), Ez + 0.12 + 0.10 * math.sin(a))) for a in (j * PI / 2 / 8 for j in range(9))]))
    seg.append((1, [Vector((0, ye - 0.10, ZC)), Vector((0, -0.20, ZC))]))
    seg.append((1, A['DES'] + [Vector((0, -1.0, Q_ZC))]))
    seg.append((0, [Vector((0, -1.0, Q_ZC)), Vector((0, -1.48, Q_ZC))]))
    pts, tipo = [], []
    for t, ps in seg:
        for p in ps:
            if pts and (p - pts[-1]).length < 1e-6:
                continue
            pts.append(p)
            tipo.append(t)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + (b - a).length)
    return pts, tipo, cum


def q_ponto(pts, tipo, cum, s):
    for i in range(len(pts) - 1):
        if cum[i] <= s <= cum[i + 1]:
            f = (s - cum[i]) / max(1e-9, cum[i + 1] - cum[i])
            return pts[i] + (pts[i + 1] - pts[i]) * f, tipo[i + 1] if tipo[i] != tipo[i + 1] else tipo[i]
    return pts[-1], tipo[-1]


def animar_quantico(A):
    random.seed(11)
    eixos = [Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized() for _ in range(Q_NI)]
    fases = [random.uniform(0, 2 * PI) for _ in range(Q_NI)]
    campo_em = M['campo'].node_tree.nodes['Emission'].inputs['Strength']
    for p in A['pists']:                                       # braço 1 parado: pistões fixos
        posar_pistao(p, A['S'], 0.0)
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        e = q_ext(fr)
        for k in range(1, 5):
            A['estagios'][k].e.location = (0, k * e, 0)
            A['tubos'][k].e.location = (0, k * e, 0)
            chave(A['estagios'][k].e, 'location', q)
            chave(A['tubos'][k].e, 'location', q)
        A['g'].e.location = A['g'].pivo - A['b2'].pivo + Vector((0, 4 * e, 0))
        chave(A['g'].e, 'location', q)
        A['cl'].e.scale = (1, (1.10 + 4 * e) / 1.10, 1)
        chave(A['cl'].e, 'scale', q)
        L0 = q_fim(4) - 0.01 - A['car'].pivo.y
        A['cb'].e.scale = (1, (L0 + 4 * e) / L0, 1)
        chave(A['cb'].e, 'scale', q)
        A['car'].e.rotation_euler = (-4 * e / 0.056, 0, 0)
        chave(A['car'].e, 'rotation_euler', q)
        ponta = A['ye'] + 4 * e - 0.12
        for an, y in A['rastro']:
            s = 1.0 if y <= 0.86 else max(0.0, min(1.0, (ponta - y) / 0.12))
            boia = 0.006 * math.sin(fr * 2 * PI * 2 + y * 5)
            an.e.scale = (max(s, 0.02),) * 3
            an.e.location = an.pivo - A['b2'].pivo + Vector((0, 0, boia))
            chave(an.e, 'scale', q)
            chave(an.e, 'location', q)
            for o in an.objs:
                chave_vis(o, s > 0.03, q)
        for h, eixo in A['helices']:
            rot = [0, 0, 0]
            rot[eixo] = fr * 2 * PI * 16
            h.e.rotation_euler = rot
            chave(h.e, 'rotation_euler', q)
        # pulso do campo a cada 0,2 s (5 Hz)
        campo_em.default_value = 7.0 + 3.0 * math.sin(fr * 2 * PI * 20)
        campo_em.keyframe_insert('default_value', frame=q)
        chave_emis(M['labio'], 14.0 + 8.0 * math.sin(fr * 2 * PI * 20), q)
        # itens: 40 no caminho, 4 voltas por laço = 40 itens/s = 8 itens a cada 0,2 s
        pts, tipo, cum = q_caminho(A, e)
        Lt = cum[-1]
        for i, (o, h) in enumerate(A['itens']):
            ui = (i / Q_NI + 4 * fr) % 1.0
            p, t = q_ponto(pts, tipo, cum, ui * Lt)
            o.location = (-p.x, -p.y, p.z)
            if t == 1:
                ang = fases[i] + ui * 2 * PI * 2.5
                o.rotation_euler = Matrix.Rotation(ang, 3, eixos[i]).to_euler()
            else:
                o.rotation_euler = (0, 0, fases[i] * 0.05)
            vis = True if t == 1 else (p.y < 3.46 if p.y > 0 else p.y > -1.45)
            chave(o, 'location', q)
            chave(o, 'rotation_euler', q)
            chave_vis(o, vis, q)
            for c in o.children:
                if c.name.endswith('_marca'):
                    chave_vis(c, vis, q)
            chave_vis(h, vis and t == 1, q)


# =================================================================== montagem, cena e fotos
POS = {'filtro': (0.0, 0.0, 0.0), 'empilhador': (1.8, 0.0, 0.0), 'quantico': (3.7, 0.0, 0.0)}
fil = braco_filtro(POS['filtro'])
emp = braco_empilhador(POS['empilhador'])
qua = braco_quantico(POS['quantico'])
animar_filtro(fil)
animar_empilhador(emp)
animar_quantico(qua)
for A in (fil, emp):
    for p in A['pists']:
        print('CURSO %s: %.3f .. %.3f (camisa %.2f, haste %.2f)' % (p['cam'].nome, min(p['curso']), max(p['curso']), p['Lc'], p['Lh']))

COL = sc.collection
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (16, 16, 1.0))
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
    pr_ = bpy.context.preferences.addons['cycles'].preferences
    pr_.compute_device_type = 'OPTIX'
    pr_.get_devices()
    for dv in pr_.devices:
        dv.use = True
except Exception:
    sc.cycles.device = 'CPU'
sc.cycles.use_denoising = True
sc.cycles.transparent_max_bounces = 32
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
    sc.cycles.samples = 128 if modo == 'foto' else 20
    esc = 1.0 if modo == 'foto' else 0.5
    Fo, Eo, Qo = (Vector(POS[k]) for k in ('filtro', 'empilhador', 'quantico'))
    if quer('braco_filtro'):
        mostrar('filtro')
        sc.frame_set(1 + int(0.25 * QUADROS))                  # lendo a placa de cobre: feixe + giroflex
        mirar(Fo + Vector((1.75, -1.85, 1.25)), Fo + Vector((0.12, -0.45, 0.42)), 34)
        foto('braco_filtro', int(1300 * esc), int(1050 * esc))
    if quer('braco_empilhador'):
        mostrar('empilhador')
        sc.frame_set(1 + int(0.385 * QUADROS))                 # quarto mergulho: pilha de 3 + o quarto entrando
        mirar(Eo + Vector((1.7, -1.75, 1.2)), Eo + Vector((0.0, -0.4, 0.48)), 34)
        foto('braco_empilhador', int(1300 * esc), int(1050 * esc))
    if quer('braco_quantico'):
        mostrar('quantico')
        sc.frame_set(1 + int(0.56 * QUADROS))                  # lança esticada a 3 tiles, fluxo correndo
        mirar(Qo + Vector((3.0, -3.4, 2.2)), Qo + Vector((0.0, -1.35, 0.85)), 30)
        foto('braco_quantico', int(1400 * esc), int(1000 * esc))
    if quer('bracos_novos_juntos'):
        mostrar('filtro', 'empilhador', 'quantico')
        sc.frame_set(1 + int(0.56 * QUADROS))
        mirar(Vector((-1.5, -4.3, 2.3)), Vector((1.95, -1.0, 0.68)), 23)
        foto('bracos_novos_juntos', int(1700 * esc), int(950 * esc))
    REV = os.path.join(AQUI, 'rev')
    os.makedirs(REV, exist_ok=True)
    def rev(nome, col, quadro, pos, alvo, lente, rx=900, ry=700):
        if not quer(nome):
            return
        mostrar(col)
        sc.frame_set(1 + int(quadro * QUADROS))
        mirar(pos, alvo, lente)
        foto(os.path.join('rev', nome), int(rx * esc), int(ry * esc))
    if modo == 'teste':
        rev('bn_filtro_garra', 'filtro', 0.25, Fo + Vector((0.55, -1.55, 0.75)), Fo + Vector((0.0, -1.0, 0.42)), 45)
        rev('bn_filtro_painel', 'filtro', 0.50, Fo + Vector((1.0, -0.35, 0.75)), Fo + Vector((0.37, -0.02, 0.25)), 40)
        rev('bn_filtro_pega', 'filtro', 0.59, Fo + Vector((-0.9, -1.6, 0.7)), Fo + Vector((0.0, -0.8, 0.35)), 40)
        rev('bn_filtro_traseira', 'filtro', 0.78, Fo + Vector((-1.2, -1.0, 1.0)), Fo + Vector((0.0, 0.1, 0.5)), 35)
        rev('bn_emp_garra', 'empilhador', 0.36, Eo + Vector((0.6, -1.5, 0.65)), Eo + Vector((0.0, -0.75, 0.40)), 45)
        rev('bn_emp_entrega', 'empilhador', 0.72, Eo + Vector((0.7, 1.6, 0.8)), Eo + Vector((0.0, 0.7, 0.40)), 40)
        rev('bn_emp_traseira', 'empilhador', 0.55, Eo + Vector((-1.0, -1.4, 1.0)), Eo + Vector((0.0, 0.0, 0.5)), 35)
        rev('bn_q_ponta', 'quantico', 0.56, Qo + Vector((0.8, -2.2, 1.6)), Qo + Vector((0.0, -3.0, 1.0)), 40)
        rev('bn_q_base', 'quantico', 0.56, Qo + Vector((1.4, -1.2, 1.2)), Qo + Vector((0.0, 0.0, 0.75)), 35)
        rev('bn_q_recolhido', 'quantico', 0.05, Qo + Vector((2.2, -2.0, 1.6)), Qo + Vector((0.0, -0.4, 0.8)), 32)
        rev('bn_q_norte', 'quantico', 0.56, Qo + Vector((-1.3, 1.9, 1.3)), Qo + Vector((0.0, 0.6, 0.8)), 35)
print('BRACOS NOVOS ok')
