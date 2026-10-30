"""Estudo isolado (fora do jogo): a ferrovia da IA — trilho_reto, trilho_curva, trilho_fim e sinal_trem.
Medidas e portas como no arte/CATALOGO.md (1 tile = 1 m; x leste, y norte):
- Via: leito de brita (0,84 m de largura no pé) com pedras soltas de verdade enchendo os vãos até quase o topo dos
  dormentes; dormentes de concreto protendido (seção trapezoidal, cintura fina no meio), alguns rachados, um quebrado
  com a armadura aparecendo e um trocado por madeira gasta (fixado com tirefão); trilho de perfil real (patim, alma,
  boleto coroado) varrido ao longo do eixo; placa de apoio com palmilha de borracha, ombreiras, grampos elásticos
  (tipo "e-clip") e parafusos; emenda com talas e 4 parafusos atravessando a alma na borda de cada tile (folga de
  dilatação). Topo do boleto polido onde a roda passa, lateral enferrujada; óleo, mato, lama.
- trilho_reto 1×1 (N–S, 5 dormentes a cada 0,2 m: a borda do tile cai no meio do vão).
- trilho_curva 3×3, raio 2,5 m (centro no canto SE da área): entra pelo sul no tile da esquerda e sai a leste no tile
  de cima. 20 dormentes em leque, superelevação de 12 mm no trilho externo (rampa dentro da peça: bordas niveladas),
  contratrilho junto ao trilho interno com calços, cadeiras e pontas abertas; emenda no meio do arco.
- trilho_fim 1×1: para-choque de aço preso aos trilhos por sapatas de atrito (garras + parafusos pela alma), travessa
  com listras, dois amortecedores hidráulicos (camisa, haste cromada, placa de choque gasta — uma trocada), mangueiras
  até o acumulador sobre a travessa, escoras, luz vermelha pulsando com eletroduto.
- sinal_trem 1×1 (até 1,55 m): sapata e pedestal de concreto, chumbadores, placa com nervuras, mastro, cabeça de LEDs
  (vermelho/âmbar/verde em matriz de pontos, palas), olho sensor violeta da IA no topo, caixa de controle com aletas e
  LEDs de estado, cabo descendo o mastro, eletroduto corrugado até o pedestal, eletroduto no chão até a caixa de
  passagem e dali o contato de trilho (sensor preso no patim) e o ramal para o próximo bloco.
Conjunto: reto (0,−2) → reto (0,−1) → curva (0..3, 0..3) → reto (3,2) → fim (4,2); sinal no tile (1,−2), a leste.
Animação 4 s: sinal verde → âmbar → vermelho, contato de trilho piscando (e acendendo forte quando o bloco ocupa),
luz do para-choque pulsando, LEDs da caixa, olho da IA, mato balançando.
Uso: blender -b --python estudo_trilhos.py -- foto [nome]"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(41)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

# ------------------------------------------------------------------ medidas da via
G = 0.24            # meia bitola (eixo do trilho)
ZL = 0.046          # topo do leito de brita
ZD0 = 0.036         # fundo do dormente
ZDT = 0.080         # topo do dormente no assento
ZTB = ZDT + 0.002 + 0.005   # base do trilho (palmilha + placa)
HT = 0.056          # altura do trilho → topo em 0,143
ZR = 0.06           # eixo de giro da superelevação
UD = 0.38           # meio comprimento do dormente
UB = 0.42           # meia largura do pé do leito
PASSO = 0.2
CANT = math.asin(0.012 / (2 * G))

# perfil do trilho (w lateral, z a partir da base): patim, alma e boleto coroado
_meio = [(0.022, 0.0), (0.022, 0.0042), (0.011, 0.0072), (0.0045, 0.0098), (0.0031, 0.0125), (0.0029, 0.033),
         (0.0036, 0.0362), (0.0066, 0.038), (0.0112, 0.0392), (0.0115, 0.0495), (0.0104, 0.0538), (0.0068, 0.0555),
         (0.0, 0.056)]
PERFIL = _meio + [(-w, z) for (w, z) in reversed(_meio[:-1])]


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, Rr, r, nR=32, nr=10, eixo=Z):
    rot = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = rot @ Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + d * (Rr + r * math.cos(b)) + rot @ Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def varrer(bm, pts, raios, lados=16, tampas=(True, True)):
    """Tubo varrido ao longo de pts (transporte paralelo do quadro): cotovelos redondos de verdade."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    if not isinstance(raios, (list, tuple)):
        raios = [raios] * n
    tans = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    e1 = Z.cross(tans[0])
    if e1.length < 1e-4:
        e1 = tans[0].orthogonal()
    e1.normalize()
    aneis = []
    for i in range(n):
        t = tans[i]
        e1 = (e1 - t * e1.dot(t)).normalized()
        e2 = t.cross(e1)
        aneis.append([bm.verts.new(pts[i] + (e1 * math.cos(a) + e2 * math.sin(a)) * raios[i])
                      for a in (k * 2 * PI / lados for k in range(lados))])
    for A, B in zip(aneis, aneis[1:]):
        for j in range(lados):
            bm.faces.new((A[j], A[(j + 1) % lados], B[(j + 1) % lados], B[j]))
    if tampas[0]:
        bm.faces.new(list(reversed(aneis[0])))
    if tampas[1]:
        bm.faces.new(aneis[-1])


def catmull(pts, n=6):
    """Curva suave passando pelos pontos (Catmull-Rom)."""
    P = [Vector(p) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def corrugado(bm, pts, r, passo=0.007, lados=12):
    """Eletroduto corrugado: reamostra o caminho e alterna o raio (gomos)."""
    pts = [Vector(p) for p in pts]
    dens = []
    for a, b in zip(pts, pts[1:]):
        k = max(1, int((b - a).length / passo))
        dens += [a.lerp(b, i / k) for i in range(k)]
    dens.append(pts[-1])
    varrer(bm, dens, [r * (1.12 if i % 2 else 0.94) for i in range(len(dens))], lados)


def base_lat(u):
    u = Vector(u).normalized()
    s = u.cross(Z)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    return s, s.cross(u).normalized() if abs(u.z) > 0.9 else Z.copy()


def chapa_arco(bm, c, u, r_in, esp, larg, a0, a1, n=14):
    """Chapa curva em volta do eixo u (pala, sela, abraçadeira); ângulo medido de s para cima; larg ao longo de u
    começando em c (não centrada)."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    linhas = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        d = s * math.cos(a) + up * math.sin(a)
        linhas.append([bm.verts.new(c + d * rr + u * w) for rr in (r_in, r_in + esp) for w in (0.0, larg)])
    for A, B in zip(linhas, linhas[1:]):
        for (i, j) in ((0, 1), (3, 2), (2, 0), (1, 3)):
            bm.faces.new((A[i], A[j], B[j], B[i]))
    for L in (linhas[0], linhas[-1]):
        bm.faces.new((L[0], L[1], L[3], L[2]))


def prisma(bm, pts_base, h, eixo=Z):
    """Prisma de base poligonal (pts no plano) extrudado por h na direção eixo."""
    eixo = Vector(eixo)
    A = [bm.verts.new(Vector(p)) for p in pts_base]
    B = [bm.verts.new(Vector(p) + eixo * h) for p in pts_base]
    n = len(A)
    bm.faces.new(list(reversed(A)))
    bm.faces.new(B)
    for i in range(n):
        bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    b.inputs['Roughness'].default_value = 0.25
    return m


def principled(m):
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def trilho_mat():
    """Lateral do trilho: aço escuro com ferrugem laranja-marrom em manchas, escorrida para baixo, rugosa."""
    m = bpy.data.materials.new('Trilho enferrujado')
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, 2.2)                 # manchas um pouco alongadas (escorrido)
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    gr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 22.0, 'Detail': 10.0, 'Roughness': 0.7})
    nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    fi = no(nt, 'ShaderNodeTexNoise', **{'Scale': 260.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], fi.inputs['Vector'])
    rampa = no(nt, 'ShaderNodeValToRGB')
    el = rampa.color_ramp.elements
    el[0].position, el[0].color = 0.42, (0.055, 0.05, 0.047, 1)
    el[1].position, el[1].color = 0.66, (0.3, 0.115, 0.04, 1)
    e3 = el.new(0.54)
    e3.color = (0.13, 0.065, 0.035, 1)
    nt.links.new(gr.outputs['Fac'], rampa.inputs['Fac'])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.45
    nt.links.new(rampa.outputs['Color'], var.inputs[6])
    nt.links.new(fi.outputs['Color'], var.inputs[7])
    nt.links.new(var.outputs[2], b.inputs['Base Color'])
    met = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.6, 'To Min': 0.7, 'To Max': 0.1})
    nt.links.new(gr.outputs['Fac'], met.inputs['Value'])
    nt.links.new(met.outputs['Result'], b.inputs['Metallic'])
    b.inputs['Roughness'].default_value = 0.82
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    bump.inputs['Distance'].default_value = 0.002
    nt.links.new(fi.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def brilho_mat():
    """Topo do boleto: aço polido pela roda, com riscos ao longo e manchas de óxido fino nas beiradas."""
    m = bpy.data.materials.new('Boleto polido')
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    b.inputs['Metallic'].default_value = 1.0
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.9, 0.89, 0.87, 1)
    cor.inputs[7].default_value = (0.42, 0.36, 0.32, 1)
    fc = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.75})
    nt.links.new(ru.outputs['Fac'], fc.inputs['Value'])
    nt.links.new(fc.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    rr = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.07, 'To Max': 0.24})
    nt.links.new(ru.outputs['Fac'], rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    return m


def brita_mat(nome, cor, rough, oleo=False):
    m = mats.material(nome, cor, 0, rough, pintura=False, sujeira=0.5, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 260.0})
    nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    bump.inputs['Distance'].default_value = 0.001
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    if oleo:
        b.inputs['Coat Weight'].default_value = 0.8
        b.inputs['Coat Roughness'].default_value = 0.08
    return m


def leito_mat():
    """Leito de brita por baixo das pedras soltas: cascalho em voronoi (cor e relevo), meio sujo."""
    m = bpy.data.materials.new('Leito de brita')
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 230.0, 'Randomness': 1.0})
    nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 180.0, 'Detail': 3.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    rampa = no(nt, 'ShaderNodeValToRGB')
    el = rampa.color_ramp.elements
    el[0].position, el[0].color = 0.3, (0.04, 0.037, 0.034, 1)
    el[1].position, el[1].color = 0.7, (0.24, 0.225, 0.205, 1)
    nt.links.new(ru.outputs['Fac'], rampa.inputs['Fac'])
    sombra = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    sombra.inputs[0].default_value = 0.7
    nt.links.new(rampa.outputs['Color'], sombra.inputs[6])
    nt.links.new(vo.outputs['Distance'], sombra.inputs[7])
    nt.links.new(sombra.outputs[2], b.inputs['Base Color'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    bump.inputs['Distance'].default_value = 0.002
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.92
    return m


def madeira_mat():
    """Madeira gasta: fibra ao longo de x, acinzentada pelo sol, rachaduras escuras finas."""
    m = mats.material('Madeira gasta', (0.25, 0.21, 0.16), 0, 0.9, pintura=False, sujeira=1.0, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (3.0, 90.0, 90.0)
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 9.0, 'Roughness': 0.7})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    lk = next(l for l in nt.links if l.to_socket == b.inputs['Base Color'])
    fenda = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.24, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], fenda.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[7].default_value = (0.03, 0.025, 0.02, 1)
    nt.links.new(fenda.outputs['Result'], mix.inputs[0])
    nt.links.new(lk.from_socket, mix.inputs[6])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.8})
    bump.inputs['Distance'].default_value = 0.003
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mato_mat(nome, cor, cor2):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.07, 'From Max': 0.2})
    nt.links.new(sp.outputs['Z'], mr.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*cor, 1)
    mix.inputs[7].default_value = (*cor2, 1)
    nt.links.new(mr.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Subsurface Weight'].default_value = 0.15
    return m


def liquido_mat(nome, cor, rough=0.08, coat=1.0):
    m = bpy.data.materials.new(nome)
    b = principled(m)
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.05
    return m


def halo_mat(nome='Mancha de sujeira', cor=(0.07, 0.06, 0.045)):
    """Escurece o chão em volta de poças e some em degradê radial (sem borda dura)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.7
    tc = no(nt, 'ShaderNodeTexCoord')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sp.inputs[0])
    cb = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sp.outputs['X'], cb.inputs['X'])
    nt.links.new(sp.outputs['Y'], cb.inputs['Y'])
    d = no(nt, 'ShaderNodeVectorMath', operation='DISTANCE')
    d.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(cb.outputs[0], d.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 5.0})
    nt.links.new(tc.outputs['Generated'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.25
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(d.outputs['Value'], soma.inputs[2])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.62, 'To Min': 0.8, 'To Max': 0.0})
    nt.links.new(soma.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def tinta_mat(nome='Estêncil apagado', cor=(0.72, 0.7, 0.62)):
    """Tinta gasta: falha em manchas (alfa por ruído)."""
    m = mats.material(nome, cor, 0, 0.8, pintura=False, sujeira=0.9, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 140.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.58, 'To Min': 0.0, 'To Max': 0.9})
    nt.links.new(ru.outputs['Fac'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def rustico(m, poeira=1.0, lama=1.0, fuligem=1.0, amassado=0.12, lz=(0.03, 0.17)):
    """Camada de uso: poeira no que olha para cima, lama embaixo (lz: faixa de altura), fuligem e amassados."""
    nt = m.node_tree
    no = mats.no
    b = principled(m)
    lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    cor = lk.from_socket if lk else None
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 8.0, 'Detail': 3.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    gr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], gr.inputs['Vector'])
    cima = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.9, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(sn.outputs['Z'], cima.inputs['Value'])
    pr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.62, 'To Min': 0.2, 'To Max': 0.9 * poeira})
    nt.links.new(ru.outputs['Fac'], pr.inputs['Value'])
    fp = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(cima.outputs['Result'], fp.inputs[0])
    nt.links.new(pr.outputs['Result'], fp.inputs[1])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': lz[0], 'From Max': lz[1], 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sp.outputs['Z'], baixo.inputs['Value'])
    lr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.6, 'To Min': 0.2, 'To Max': 1.0 * lama})
    nt.links.new(ru.outputs['Fac'], lr.inputs['Value'])
    fl = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(baixo.outputs['Result'], fl.inputs[0])
    nt.links.new(lr.outputs['Result'], fl.inputs[1])
    fu = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 0.75 * fuligem})
    nt.links.new(gr.outputs['Fac'], fu.inputs['Value'])
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    c1.inputs[7].default_value = (0.08, 0.07, 0.065, 1)
    nt.links.new(fu.outputs['Result'], c1.inputs[0])
    if cor is not None:
        nt.links.new(cor, c1.inputs[6])
    else:
        c1.inputs[6].default_value = b.inputs['Base Color'].default_value
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c2.inputs[7].default_value = (0.36, 0.31, 0.24, 1)
    nt.links.new(fp.outputs['Value'], c2.inputs[0])
    nt.links.new(c1.outputs[2], c2.inputs[6])
    c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c3.inputs[7].default_value = (0.1, 0.07, 0.04, 1)
    nt.links.new(fl.outputs['Value'], c3.inputs[0])
    nt.links.new(c2.outputs[2], c3.inputs[6])
    nt.links.new(c3.outputs[2], b.inputs['Base Color'])
    rk = next((l for l in nt.links if l.to_socket == b.inputs['Roughness']), None)
    soma = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(fp.outputs['Value'], soma.inputs[0])
    nt.links.new(fl.outputs['Value'], soma.inputs[1])
    rmix = no(nt, 'ShaderNodeMix', data_type='FLOAT')
    rmix.inputs[3].default_value = 0.95
    nt.links.new(soma.outputs['Value'], rmix.inputs[0])
    if rk:
        nt.links.new(rk.from_socket, rmix.inputs[2])
    else:
        rmix.inputs[2].default_value = b.inputs['Roughness'].default_value
    nt.links.new(rmix.outputs[0], b.inputs['Roughness'])
    met = next((l for l in nt.links if l.to_socket == b.inputs['Metallic']), None)
    if met or b.inputs['Metallic'].default_value > 0:
        mm = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        nt.links.new(soma.outputs['Value'], mm.inputs[0])
        if met:
            nt.links.new(met.from_socket, mm.inputs[2])
        else:
            mm.inputs[2].default_value = b.inputs['Metallic'].default_value
        mm.inputs[3].default_value = 0.0
        nt.links.new(mm.outputs[0], b.inputs['Metallic'])
    if amassado > 0:
        vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 5.0})
        vo.feature = 'SMOOTH_F1'
        nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
        bump = no(nt, 'ShaderNodeBump', **{'Strength': amassado})
        bump.inputs['Distance'].default_value = 0.02
        nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
        nk = next((l for l in nt.links if l.to_socket == b.inputs['Normal']), None)
        if nk:
            nt.links.new(nk.from_socket, bump.inputs['Normal'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])


LUZES = {}   # materiais emissivos animados


def luz(chave, nome, cor, base):
    m = emissivo(nome, cor, 0.0, base)
    LUZES[chave] = principled(m)
    return m


base3d.M.update({
    'trilho': trilho_mat(),
    'brilho': brilho_mat(),
    'leito': leito_mat(),
    'brita_a': brita_mat('Brita clara', (0.3, 0.29, 0.275), 0.85),
    'brita_b': brita_mat('Brita escura', (0.2, 0.195, 0.19), 0.8),
    'brita_c': brita_mat('Brita manchada de ferrugem', (0.2, 0.12, 0.075), 0.85),
    'brita_d': brita_mat('Brita encardida', (0.22, 0.2, 0.165), 0.9),
    'brita_o': brita_mat('Brita com óleo', (0.03, 0.027, 0.024), 0.25, oleo=True),
    'concreto': mats.material('Concreto do dormente', (0.46, 0.45, 0.42), 0, 0.88, pintura=False, sujeira=0.9,
                              desgaste=0.0),
    'concreto2': mats.material('Concreto do pedestal', (0.36, 0.35, 0.33), 0, 0.9, pintura=False, sujeira=0.9,
                               desgaste=0.0),
    'madeira': madeira_mat(),
    'fenda': mats.material('Fenda', (0.015, 0.013, 0.012), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'armadura': mats.material('Armadura enferrujada', (0.3, 0.12, 0.05), 0.4, 0.8, pintura=False, ferrugem=1.0),
    'placa': mats.material('Placa de apoio', (0.12, 0.11, 0.1), 0.8, 0.65, pintura=False, ferrugem=0.95, sujeira=1.0),
    'grampo': mats.material('Grampo elástico', (0.2, 0.2, 0.21), 0.9, 0.38, pintura=False, ferrugem=0.7),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'galv': mats.material('Aço galvanizado', (0.5, 0.51, 0.5), 1.0, 0.5, pintura=False, ferrugem=0.55, sujeira=0.9),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.6),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.8, sujeira=0.8, ferrugem=0.35),
    'cinza': mats.material('Cinza trocado', (0.33, 0.34, 0.33), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.5),
    'oxido': mats.material('Primer vermelho', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'pvc': mats.material('Eletroduto', (0.12, 0.12, 0.13), 0, 0.6, pintura=False, sujeira=1.0, desgaste=0.0),
    'preto': mats.material('Preto fosco', (0.012, 0.012, 0.013), 0, 0.5, pintura=False, sujeira=0.3, desgaste=0.0),
    'oleo': liquido_mat('Óleo', (0.012, 0.01, 0.008), 0.15),
    'lama': liquido_mat('Lama molhada', (0.085, 0.058, 0.032), 0.3, 0.6),
    'lama_seca': mats.material('Lama seca', (0.2, 0.15, 0.1), 0, 0.95, pintura=False, sujeira=0.6, desgaste=0.0),
    'poca': liquido_mat('Poça barrenta', (0.07, 0.055, 0.035), 0.03),
    'halo': halo_mat(),
    'halo_lama': halo_mat('Mancha de lama', (0.13, 0.09, 0.05)),
    'ferrugem_m': halo_mat('Mancha de ferrugem', (0.3, 0.11, 0.035)),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'mato': mato_mat('Mato verde', (0.05, 0.09, 0.02), (0.16, 0.22, 0.05)),
    'mato_seco': mato_mat('Mato seco', (0.16, 0.12, 0.05), (0.42, 0.33, 0.14)),
    'folha': mato_mat('Folha de erva', (0.04, 0.1, 0.025), (0.09, 0.18, 0.04)),
    'tinta': tinta_mat(),
    'tinta_bloco': tinta_mat('Marca de bloco', (0.8, 0.78, 0.72)),
    'tinta_violeta': tinta_mat('Marca violeta da IA', (0.32, 0.08, 0.55)),
    'listras': base3d.listras_mat(),
    'adesivo': mats.material('Adesivo de alerta', (0.75, 0.55, 0.02), 0, 0.4, pintura=False, sujeira=0.9),
    'led_v': luz('ia', 'Olho da IA', (0.55, 0.12, 1.0), (0.05, 0.01, 0.1)),
    'led_r': luz('vermelho', 'LED vermelho', (1.0, 0.03, 0.01), (0.12, 0.01, 0.005)),
    'led_a': luz('ambar', 'LED âmbar', (1.0, 0.42, 0.02), (0.12, 0.05, 0.005)),
    'led_g': luz('verde', 'LED verde', (0.1, 1.0, 0.25), (0.01, 0.1, 0.03)),
    'led_s': luz('sensor', 'LED do sensor', (0.6, 0.15, 1.0), (0.05, 0.015, 0.1)),
    'led_c1': luz('caixa1', 'LED da caixa 1', (0.1, 1.0, 0.25), (0.01, 0.08, 0.02)),
    'led_c2': luz('caixa2', 'LED da caixa 2', (1.0, 0.42, 0.02), (0.1, 0.04, 0.005)),
    'luz_fim': luz('fim', 'Luz vermelha do para-choque', (1.0, 0.04, 0.01), (0.15, 0.01, 0.005)),
})
for n in base3d.M['chao'].node_tree.nodes:
    if n.type == 'AMBIENT_OCCLUSION':
        n.only_local = True

for chave, kw in (('concreto', dict(amassado=0.0, lz=(0.03, 0.075), lama=0.8)),
                  ('concreto2', dict(amassado=0.0, lz=(0.0, 0.12))),
                  ('madeira', dict(amassado=0.0, lz=(0.03, 0.07))),
                  ('placa', dict(amassado=0.0, lz=(0.06, 0.1), lama=0.5, poeira=0.6)),
                  ('grampo', dict(amassado=0.0, lz=(0.07, 0.1), lama=0.4, poeira=0.5)),
                  ('ferro', dict(amassado=0.08, lz=(0.08, 0.13), lama=0.5)),
                  ('aco', dict(amassado=0.0, lz=(0.06, 0.12), fuligem=0.5)),
                  ('galv', dict(amassado=0.05, lz=(0.0, 0.15))),
                  ('amarelo', dict(amassado=0.12, lz=(0.1, 0.24))),
                  ('grafite', dict(amassado=0.1, lz=(0.0, 0.12))),
                  ('cinza', dict(amassado=0.1, lz=(0.0, 0.2))),
                  ('oxido', dict(amassado=0.1)),
                  ('pvc', dict(amassado=0.0, lz=(0.0, 0.06))),
                  ('borracha', dict(amassado=0.0, fuligem=0.0, lz=(0.06, 0.09))),
                  ('cromo', dict(amassado=0.0, poeira=0.4, fuligem=0.3, lz=(0.0, 0.0001)))):
    rustico(base3d.M[chave], **kw)


# ------------------------------------------------------------------ caminhos e quadros da via
class Reta:
    def __init__(s, a, b):
        s.a, s.b = Vector(a), Vector(b)
        s.L = (s.b - s.a).length
        s.t = (s.b - s.a).normalized()

    def pc(s, x):
        return s.a + s.t * x

    def tang(s, x):
        return s.t


class Arco:
    """Arco de centro c e raio R, de th0 para th1 (sentido do ângulo dado pelo sinal)."""
    def __init__(s, c, R, th0, th1):
        s.c, s.R, s.th0 = Vector(c), R, th0
        s.sg = 1 if th1 > th0 else -1
        s.L = R * abs(th1 - th0)

    def th(s, x):
        return s.th0 + s.sg * x / s.R

    def pc(s, x):
        t = s.th(x)
        return s.c + Vector((math.cos(t), math.sin(t), 0)) * s.R

    def tang(s, x):
        t = s.th(x)
        return Vector((-math.sin(t), math.cos(t), 0)) * s.sg


class Quadro:
    """Referencial da via no ponto x: a ao longo, u à esquerda de quem anda, z para cima (com giro de superelevação)."""
    def __init__(s, cam, x, rolar=0.0):
        s.p = cam.pc(x)
        s.t = cam.tang(x)
        n = Z.cross(s.t).normalized()
        s.n = n * math.cos(rolar) + Z * math.sin(rolar)
        s.up = -n * math.sin(rolar) + Z * math.cos(rolar)

    def __call__(s, u, a, z):
        return s.p + s.t * a + s.n * u + s.up * (z - ZR) + Z * ZR


def caixa_q(bm, Q, u0, u1, a0, a1, z0, z1):
    """Caixa no referencial Q (u, a, z)."""
    c = [(u0, a0, z0), (u1, a0, z0), (u1, a1, z0), (u0, a1, z0), (u0, a0, z1), (u1, a0, z1), (u1, a1, z1), (u0, a1, z1)]
    v = [bm.verts.new(Q(*p)) for p in c]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])


class Lote:
    """Junta a geometria de uma peça por material; no fim vira um objeto por material."""
    def __init__(s, nome):
        s.nome = nome
        s.bms = {}

    def B(s, mat, liso=False):
        if (mat, liso) not in s.bms:
            s.bms[(mat, liso)] = bmesh.new()
        return s.bms[(mat, liso)]

    def fim(s):
        for (mat, liso), bm in s.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            o = obj('%s_%s' % (s.nome, mat), bm, mat)
            if liso:
                suavizar(o)


def decal(bm, pts, z_off=0.0006):
    """Polígono plano (já no mundo) levemente acima da superfície."""
    vs = [bm.verts.new(Vector(p) + Z * z_off) for p in pts]
    bm.faces.new(vs)


def halo_em(mat, c, r, z, alongar=1.0, ang=0.0):
    """Mancha com degradê radial (coordenada Generated): precisa ser um objeto só seu."""
    bm = bmesh.new()
    mancha_em(bm, c, r, z, alongar, ang)
    obj('halo', bm, mat)


def mancha_em(bm, c, r, z, alongar=1.0, ang=0.0):
    """Mancha irregular plana no ponto c (mundo), na altura z."""
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=r)
    ca, sa = math.cos(ang), math.sin(ang)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.3 * math.sin(a * 3 + random.random() * 6) + 0.15 * random.random()
        x, y = v.co.x * f * alongar, v.co.y * f
        v.co = Vector((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca, z))


# ------------------------------------------------------------------ peças da via
def varrer_perfil(bm, cam, x0, x1, perfil, u0, z0, rolar, passo=0.03, tampas=True, xs=None, esc=None):
    n = max(1, int(math.ceil((x1 - x0) / passo)))
    xs = xs or [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    aneis = []
    for x in xs:
        Q = Quadro(cam, x, rolar(x))
        e = esc(x) if esc else 1.0
        aneis.append([bm.verts.new(Q(u0 + w * (1 + 0.12 * (1 - e)), 0, z0 + max(z * e, min(z, 0.003))))
                      for (w, z) in perfil])
    k = len(perfil)
    for A, Bn in zip(aneis, aneis[1:]):
        for j in range(k):
            bm.faces.new((A[j], A[(j + 1) % k], Bn[(j + 1) % k], Bn[j]))
    if tampas:
        bm.faces.new(list(reversed(aneis[0])))
        bm.faces.new(aneis[-1])


def faixa_topo(bm, cam, x0, x1, u0, rolar, passo=0.03):
    """Faixa polida no topo do boleto (onde a roda passa), 0,4 mm acima da coroa."""
    topo = [(w, z) for (w, z) in _meio if z > 0.05]

    def zp(w):
        w = abs(w)
        for (wa, za), (wb, zb) in zip(topo, topo[1:]):
            if wb <= w <= wa:
                return za + (zb - za) * (wa - w) / (wa - wb)
        return HT
    perfil = [(w, zp(w) + 0.0003) for w in (-0.009, -0.0068, -0.004, 0.0, 0.004, 0.0068, 0.009)]
    n = max(1, int(math.ceil((x1 - x0) / passo)))
    linhas = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        Q = Quadro(cam, x, rolar(x))
        linhas.append([bm.verts.new(Q(u0 + w, 0, ZTB + z)) for (w, z) in perfil])
    for A, Bn in zip(linhas, linhas[1:]):
        for j in range(len(perfil) - 1):
            bm.faces.new((A[j], A[j + 1], Bn[j + 1], Bn[j]))


ESTACOES = [(-UD, 0.040, 0.033, 0.040), (-0.31, 0.042, 0.034, 0.044), (-0.17, 0.037, 0.029, 0.037),
            (0.17, 0.037, 0.029, 0.037), (0.31, 0.042, 0.034, 0.044), (UD, 0.040, 0.033, 0.040)]


def dormente_concreto(bm, Q, u_ini=-UD, u_fim=UD, quebra=None):
    """Dormente monobloco: seção trapezoidal, mais alto e largo nos assentos, cintura fina no meio.
    quebra: lado (+1/−1) com ponta quebrada irregular."""
    est = [e for e in ESTACOES if u_ini - 1e-6 <= e[0] <= u_fim + 1e-6]
    if quebra:
        est = [e for e in est if abs(e[0]) < 0.33]
        est.append((0.335 * quebra, 0.041, 0.033, 0.043))
        est.sort(key=lambda e: e[0])
    aneis = []
    for i, (u, hb, ht, h) in enumerate(est):
        ponta = quebra and abs(u - 0.335 * quebra) < 1e-6
        if ponta:   # face de quebra irregular
            j = [random.uniform(-0.012, 0.012) for _ in range(4)]
            aneis.append([bm.verts.new(Q(u + j[0], -hb, ZD0)), bm.verts.new(Q(u + j[1], hb, ZD0)),
                          bm.verts.new(Q(u - 0.02 * quebra + j[2], ht * 0.6, ZD0 + h * 0.75)),
                          bm.verts.new(Q(u + j[3], -ht, ZD0 + h))])
        else:
            aneis.append([bm.verts.new(Q(u, -hb, ZD0)), bm.verts.new(Q(u, hb, ZD0)),
                          bm.verts.new(Q(u, ht, ZD0 + h)), bm.verts.new(Q(u, -ht, ZD0 + h))])
    for A, Bn in zip(aneis, aneis[1:]):
        for j in range(4):
            bm.faces.new((A[j], A[(j + 1) % 4], Bn[(j + 1) % 4], Bn[j]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])
    return est


def rachadura(bm, Q, u0, ht, h, lado=1):
    """Fenda em zigue-zague atravessando o topo e descendo pela face lateral do dormente."""
    pts = []
    a = -ht
    u = u0
    while a < ht:
        pts.append((u, a))
        a += random.uniform(0.006, 0.012)
        u += random.uniform(-0.006, 0.006)
    pts.append((u, ht))
    z = ZD0 + h + 0.0006
    for (ua, aa), (ub, ab) in zip(pts, pts[1:]):
        w = random.uniform(0.0008, 0.002)
        decal(bm, [Q(ua - w, aa, z), Q(ub - w, ab, z), Q(ub + w, ab, z), Q(ua + w, aa, z)], 0)
    # descendo pela face (lado a=+)
    ub = pts[-1][0]
    zz = ZD0 + h
    while zz > ZD0 + 0.006:
        z2 = zz - random.uniform(0.006, 0.01)
        u2 = ub + random.uniform(-0.004, 0.004)
        aa = lado * (0.0295 + (0.037 - 0.0295) * (ZD0 + h - zz) / h + 0.0007)
        ab = lado * (0.0295 + (0.037 - 0.0295) * (ZD0 + h - z2) / h + 0.0007)
        decal(bm, [Q(ub - 0.0012, aa, zz), Q(u2 - 0.0012, ab, z2), Q(u2 + 0.0012, ab, z2), Q(ub + 0.0012, aa, zz)], 0)
        zz, ub = z2, u2


def grampo(bm, Q, u0, lado, a_sinal=1):
    """Grampo elástico: perna enfiada na ombreira (ao longo de a), volta por cima e a ponta apoia no patim."""
    w = lambda x: u0 + lado * x
    s = a_sinal
    pts = [(0.028, -0.017 * s, 0.006), (0.028, 0.004 * s, 0.006), (0.0285, 0.015 * s, 0.0072),
           (0.0295, 0.02 * s, 0.0105), (0.0285, 0.017 * s, 0.014), (0.025, 0.008 * s, 0.0152),
           (0.0215, -0.002 * s, 0.0135), (0.0185, -0.009 * s, 0.0102), (0.0172, -0.0135 * s, 0.0078)]
    cam = catmull([Q(w(x), a, ZTB + z) for (x, a, z) in pts], 3)
    varrer(bm, cam, 0.0026, 8)


def parafuso(bmh, Q, u, a, z, r=0.0055, eixo=None, haste=0.004):
    """Cabeça sextavada com arruela e ponta de rosca, apontando para eixo (padrão: up)."""
    e = eixo if eixo is not None else Q.up
    p = Q(u, a, z)
    cil(bmh, p + e * 0.0006, r * 1.3, 0.0012, e, lados=14)
    cil(bmh, p + e * 0.0032, r, 0.004, e, lados=6)
    if haste:
        cil(bmh, p + e * (0.0052 + haste / 2), r * 0.5, haste, e, lados=8)


def assento(P, Q, u0, madeira=False, sem_interno=False, placa_ext=0.0):
    """Placa de apoio com palmilha, ombreiras, 2 grampos e 2 parafusos (ou tirefões na madeira)."""
    ui, ue = (u0 - 0.047, u0 + 0.047)
    if placa_ext:
        if placa_ext > 0:
            ue = u0 + placa_ext
        else:
            ui = u0 + placa_ext
    caixa_q(P.B('borracha'), Q, ui - 0.002, ue + 0.002, -0.032, 0.032, ZDT, ZDT + 0.002)
    caixa_q(P.B('placa'), Q, ui, ue, -0.030, 0.030, ZDT + 0.002, ZTB)
    if madeira:
        for lado in (-1, 1):
            for a in (-0.017, 0.017):
                p = Q(u0 + lado * 0.0265, a, ZTB)
                cil(P.B('ferro'), p + Q.up * 0.0045, 0.0075, 0.009, Q.up, lados=4)   # cabeça quadrada do tirefão
                cil(P.B('ferro'), p + Q.up * 0.0095, 0.009, 0.002, Q.up, lados=16)  # aba sobre o patim
            parafuso(P.B('aco'), Q, u0 + lado * 0.039, 0.0, ZTB, 0.005)
        return
    for lado in (-1, 1):
        if sem_interno and lado == sem_interno:
            continue
        uc = u0 + lado * 0.028
        caixa_q(P.B('ferro'), Q, uc - 0.005, uc + 0.005, -0.014, 0.014, ZTB, ZTB + 0.0095)   # ombreira
        grampo(P.B('grampo', True), Q, u0, lado, 1 if lado > 0 else -1)
        parafuso(P.B('aco'), Q, u0 + lado * 0.040, 0.021 * lado, ZTB)
        parafuso(P.B('aco'), Q, u0 + lado * 0.040, -0.021 * lado, ZTB)


def talas(P, cam, x, rolar):
    """Emenda: tala dos dois lados da alma e 4 parafusos atravessando (cabeça de um lado, porca do outro)."""
    Q = Quadro(cam, x, rolar(x))
    for u0 in (-G, G):
        for lado in (-1, 1):
            w0, w1 = 0.0032, 0.0098
            u_a, u_b = sorted((u0 + lado * w0, u0 + lado * w1))
            caixa_q(P.B('ferro'), Q, u_a, u_b, -0.075, 0.075, ZTB + 0.0125, ZTB + 0.0335)
            # chanfro de cima e de baixo (encosta no boleto e no patim)
            u_c, u_d = sorted((u0 + lado * w0, u0 + lado * 0.0068))
            caixa_q(P.B('ferro'), Q, u_c, u_d, -0.075, 0.075, ZTB + 0.0335, ZTB + 0.0365)
            caixa_q(P.B('ferro'), Q, u_c, u_d, -0.075, 0.075, ZTB + 0.0098, ZTB + 0.0125)
        for a in (-0.058, -0.022, 0.022, 0.058):
            p = Q(u0, a, ZTB + 0.023)
            tubo(P.B('aco'), p - Q.n * 0.019, p + Q.n * 0.019, 0.0028, 8)
            s = 1 if a > 0 else -1          # cabeças alternadas
            cil(P.B('aco'), p + Q.n * s * 0.0135, 0.0058, 0.0045, Q.n, lados=6)
            cil(P.B('aco'), p - Q.n * s * 0.0118, 0.0072, 0.0012, Q.n, lados=14)
            cil(P.B('aco'), p - Q.n * s * 0.0145, 0.0056, 0.0045, Q.n, lados=6)
        # marca de tinta na emenda (a IA marca as emendas que inspecionou)
        q2 = Quadro(cam, x + 0.09, rolar(x + 0.09))
        caixa_q(P.B('tinta_violeta'), q2, u0 + 0.0031, u0 + 0.0034, -0.004, 0.004, ZTB + 0.014, ZTB + 0.03)


def pedras(P, cam, L, xs_dorm, rolar, dens=950, x_fim=None, oleos=(), rampa=lambda x: 1.0):
    """Brita solta: enche os vãos entre dormentes quase até o topo, cobre os ombros e a saia do leito."""
    xf = x_fim if x_fim is not None else L
    n = int(xf * dens)
    zonas = [x for x in (0.035, xf - 0.035) if rampa(x) < 1.0]
    n_extra = 260 * len(zonas)
    for i in range(n + n_extra):
        if i >= n:
            x = zonas[(i - n) % len(zonas)] + random.uniform(-0.03, 0.03)
        else:
            x = random.uniform(0.008, xf - 0.008)
        u = random.uniform(-UB + 0.01, UB - 0.01)
        if random.random() < 0.35:                 # reforço na saia do leito (o talude fica coberto)
            u = random.choice((-1, 1)) * random.uniform(0.36, UB - 0.006)
        r = random.uniform(0.008, 0.017)
        d = min(abs(x - xd) for xd in xs_dorm) if xs_dorm else 1.0
        au = abs(u)
        if au < 0.335:
            sup = ZL
        else:
            sup = ZL - (au - 0.335) / (UB - 0.335) * (ZL - 0.004)
        sob_dorm = d < 0.043 and au < UD + 0.004
        if sob_dorm:
            continue
        if au < UD + 0.02:
            topo = ZDT - 0.006 - r * 0.55          # enche o vão
            if d < 0.06:
                topo -= 0.004
        else:
            topo = sup + r * 0.4
        topo = max(topo, sup)
        z = sup + (topo - sup) * random.random() ** 0.4
        e = rampa(x)
        if e < 1.0:                                 # talude na ponta livre
            if d < 0.05 and au < UD + 0.004:
                continue
            z = max(0.002, z * e) + (r * 0.3 if e < 0.3 else 0.0)
        Q = Quadro(cam, x, rolar(x))
        c = Q(u, 0, z)
        m = 'brita_a' if random.random() < 0.5 else ('brita_b' if random.random() < 0.5 else 'brita_d')
        if min(abs(u - G), abs(u + G)) < 0.06 and random.random() < 0.45:
            m = 'brita_c'                           # ferrugem escorrida do trilho
        for (xo, uo, ro) in oleos:
            if (x - xo) ** 2 + (u - uo) ** 2 < ro * ro * random.uniform(0.5, 1.2):
                m = 'brita_o'
        pedra(P.B(m, True), c, r, random.uniform(0.5, 0.8))


def leito(P, cam, x0, x1, rolar, rampa, passo=0.05):
    """Leito de brita; nas pontas livres desce em talude (rampa(x) = 0 na ponta, 1 no corpo)."""
    perf = [(-UB, 0.0), (-0.40, 0.012), (-0.335, ZL), (0.335, ZL), (0.40, 0.012), (UB, 0.0)]
    perf = perf + [(UB - 0.002, -0.004), (-UB + 0.002, -0.004)]
    n = max(1, int(math.ceil((x1 - x0) / passo)))
    xs = sorted(set([x0 + (x1 - x0) * i / n for i in range(n + 1)] +
                    [x for x in (x0 + 0.02, x0 + 0.045, x0 + 0.07, x1 - 0.02, x1 - 0.045, x1 - 0.07)]))
    varrer_perfil(P.B('leito'), cam, x0, x1, perf, 0.0, 0.0, rolar, passo, xs=xs, esc=rampa)


TUFOS = []


def tufo(pos, alt, n, seco=False, folhas=False):
    """Touceira de capim: lâminas finas curvando para fora; objeto com origem na base (balança no vento)."""
    bm = bmesh.new()
    for _ in range(n):
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        s = d.cross(Z)
        h = alt * random.uniform(0.5, 1.0)
        incl = random.uniform(0.15, 0.6)
        larg = random.uniform(0.002, 0.0035)
        base = d * random.uniform(0, 0.012)
        k = 5
        pts = [base + d * (incl * h * (i / k) ** 1.6) + Z * (h * i / k) for i in range(k + 1)]
        vs = []
        for i, p in enumerate(pts):
            w = larg * (1 - i / k) + 0.0002
            vs.append((bm.verts.new(p - s * w), bm.verts.new(p + s * w)))
        for (a1, b1), (a2, b2) in zip(vs, vs[1:]):
            bm.faces.new((a1, b1, b2, a2))
    o = obj('tufo', bm, 'mato_seco' if seco else 'mato')
    o.location = pos
    if folhas:                                     # roseta de folhas largas (erva daninha)
        bf = bmesh.new()
        for i in range(6):
            a = i * PI / 3 + random.uniform(-0.2, 0.2)
            d = Vector((math.cos(a), math.sin(a), 0))
            s = d.cross(Z)
            L = random.uniform(0.025, 0.04)
            pts = [d * L * t + Z * (0.012 * math.sin(PI * t * 0.8)) for t in (0, 0.33, 0.66, 1.0)]
            ws = [0.002, 0.009, 0.008, 0.001]
            vv = [(bf.verts.new(p - s * w), bf.verts.new(p + s * w)) for p, w in zip(pts, ws)]
            for (a1, b1), (a2, b2) in zip(vv, vv[1:]):
                bf.faces.new((a1, b1, b2, a2))
        of = obj('erva', bf, 'folha')
        of.parent = o
    TUFOS.append((o, random.uniform(0, 2 * PI), random.uniform(0.03, 0.08)))
    return o


def mato_na_via(cam, L, xs_dorm, rolar, n, seco=0.4, x_fim=None):
    xf = x_fim if x_fim is not None else L
    for _ in range(n):
        for _t in range(20):
            x = random.uniform(0.03, xf - 0.03)
            if min(abs(x - xd) for xd in xs_dorm) > 0.06:
                break
        u = random.choice([random.uniform(-0.17, 0.17), random.uniform(0.3, 0.4) * random.choice((-1, 1))])
        Q = Quadro(cam, x, rolar(x))
        z = ZDT - 0.012 if abs(u) < UD else ZL - 0.01
        tufo(Q(u, 0, z), random.uniform(0.05, 0.13), random.randint(9, 18), random.random() < seco,
             random.random() < 0.3)


def sujeira_na_via(P, cam, xs_dorm, rolar, oleo_idx=(), ferr_idx=(), lama_n=3, L=1.0):
    """Óleo pingado no meio dos dormentes, ferrugem escorrida em volta das placas, lama nos vãos."""
    for i in oleo_idx:
        xd = xs_dorm[i]
        Q = Quadro(cam, xd, rolar(xd))
        c = Q(random.uniform(-0.1, 0.1), random.uniform(-0.01, 0.01), ZD0 + 0.037 + 0.0007)
        mancha_em(P.B('oleo'), c, random.uniform(0.018, 0.03), c.z, 1.6, math.atan2(Q.n.y, Q.n.x))
        # escorrido descendo a face do dormente
        for lado in (-1, 1):
            if random.random() < 0.6:
                ua = random.uniform(-0.08, 0.08)
                bm = P.B('oleo')
                zt = ZD0 + 0.036
                decal(bm, [Q(ua - 0.006, lado * 0.0298, zt), Q(ua + 0.006, lado * 0.0298, zt),
                           Q(ua + 0.003, lado * 0.0345, ZD0 + 0.012), Q(ua - 0.002, lado * 0.0345, ZD0 + 0.01)], 0)
    for i in ferr_idx:
        xd = xs_dorm[i]
        Q = Quadro(cam, xd, rolar(xd))
        for u0 in (-G, G):
            for lado in (-1, 1):
                c = Q(u0 + lado * 0.055, random.uniform(-0.01, 0.01), ZDT + 0.0006)
                halo_em('ferrugem_m', c, 0.018, c.z, 1.2)
    for _ in range(lama_n):
        x = random.uniform(0.05, L - 0.05)
        u = random.choice((-1, 1)) * random.uniform(0.25, 0.4)
        Q = Quadro(cam, x, rolar(x))
        c = Q(u, 0, ZDT - 0.006)
        bm = P.B('lama', True)
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        rr = random.uniform(0.03, 0.05)
        for v in res['verts']:
            j = random.uniform(0.75, 1.25)
            v.co = c + Vector((v.co.x * rr * 1.3 * j, v.co.y * rr * j, v.co.z * rr * 0.16 * random.uniform(0.6, 1.4)))


def via(nome, cam, tala_ini=True, cant=False, contra=False, junta_meio=False, especiais=None, fim=False,
        oleo_idx=(), ferr_idx=(), mato=6, seco=0.4, oleos=()):
    """Monta uma peça de via sobre o caminho cam (de x=0, borda de entrada, até L)."""
    especiais = especiais or {}
    P = Lote(nome)
    L = cam.L
    if cant:
        def rolar(x):
            r = min(1.0, x / (0.3 * L), (L - x) / (0.3 * L))
            r = max(0.0, r)
            return CANT * r * r * (3 - 2 * r)
    else:
        def rolar(x):
            return 0.0
    n_d = int(round(L / PASSO)) if not fim else 5
    esp = L / n_d if not fim else PASSO
    xs = [(k + 0.5) * esp for k in range(n_d)]
    x_leito = L if not fim else 0.98

    def rampa(x):
        e = 1.0
        if not tala_ini:
            e = min(e, x / 0.07)
        if fim:
            e = min(e, (x_leito - x) / 0.07)
        return max(0.0, min(1.0, e))
    leito(P, cam, 0.0, x_leito, rolar, rampa)
    # dormentes
    for k, xd in enumerate(xs):
        tipo = especiais.get(k, 'concreto')
        Q = Quadro(cam, xd, rolar(xd))
        if tipo == 'madeira':
            # trocado: madeira gasta, um pouco torto e afundado, pontas rachadas
            Q = Quadro(cam, xd + 0.006, rolar(xd))
            ang = math.radians(2.0)
            Q.t, Q.n = (Q.t * math.cos(ang) + Q.n * math.sin(ang)), (Q.n * math.cos(ang) - Q.t * math.sin(ang))
            caixa_q(P.B('madeira'), Q, -0.385, 0.385, -0.043, 0.043, ZD0 - 0.004, ZDT)
            for su in (-1, 1):
                for _ in range(3):
                    a0 = random.uniform(-0.03, 0.03)
                    decal(P.B('fenda'), [Q(su * 0.3851, a0 - 0.0012, ZD0), Q(su * 0.3851, a0 + 0.0012, ZD0),
                                         Q(su * 0.3851, a0 + 0.001, ZDT - 0.005), Q(su * 0.3851, a0 - 0.001,
                                                                                    ZDT - 0.005)], 0)
                    decal(P.B('fenda'), [Q(su * 0.385, a0 - 0.0012, ZDT), Q(su * 0.33, a0 - 0.0006, ZDT),
                                         Q(su * 0.33, a0 + 0.0006, ZDT), Q(su * 0.385, a0 + 0.0012, ZDT)], 0.0006)
            for u0 in (-G, G):
                assento(P, Q, u0, madeira=True)
            continue
        quebra = especiais.get(('quebra', k))
        dormente_concreto(P.B('concreto'), Q, quebra=quebra)
        if quebra:
            # pedaço solto caído no vão e armadura aparecendo
            for j in range(4):
                p = Q(0.335 * quebra + random.uniform(-0.003, 0.003) * j, random.uniform(-0.02, 0.02),
                      ZD0 + 0.012 + 0.007 * j)
                tubo(P.B('armadura'), p, p + Q.n * quebra * random.uniform(0.012, 0.03) + Q.up * random.uniform(
                    -0.006, 0.01), 0.0016, 6)
            bmc = P.B('concreto')
            c = Q(0.36 * quebra, 0.07 * (1 if k % 2 else -1), ZDT - 0.008)
            pedra(bmc, c, 0.02, 0.55)
            pedra(bmc, c + Q.t * 0.025 + Q.n * 0.02, 0.011, 0.6)
        if tipo == 'rachado':
            rachadura(P.B('fenda'), Q, random.uniform(-0.12, 0.12), 0.029, 0.037, random.choice((-1, 1)))
            rachadura(P.B('fenda'), Q, G + 0.06 * random.choice((-1, 1)), 0.034, 0.044)
            # lascas na quina
            for _ in range(2):
                pedra(P.B('concreto'), Q(random.uniform(-0.3, 0.3), 0.045, ZDT - 0.024), 0.006, 0.6)
        # número de série em tinta, meio apagado, no meio do dormente
        if k % 2 == 0:
            for j in range(4):
                if random.random() < 0.75:
                    caixa_q(P.B('tinta'), Q, -0.04 + j * 0.022, -0.04 + j * 0.022 + 0.014, -0.012, 0.012,
                            ZD0 + 0.0372, ZD0 + 0.0378)
        contra_aqui = contra and contra[0] <= xd <= contra[1]
        for u0 in (-G, G):
            if contra_aqui and u0 < 0:
                assento(P, Q, u0, sem_interno=1, placa_ext=0.078)
            else:
                assento(P, Q, u0)
    # trilhos (folga de dilatação de 3 mm nas emendas)
    x_tr1 = L - 0.0015 if not fim else 0.92
    cortes = [0.0015 if tala_ini else 0.0, x_tr1]
    if junta_meio:
        cortes = [cortes[0], L / 2 - 0.0015, L / 2 + 0.0015, x_tr1]
    for i in range(0, len(cortes), 2):
        for u0 in (-G, G):
            varrer_perfil(P.B('trilho'), cam, cortes[i], cortes[i + 1], PERFIL, u0, ZTB, rolar)
            faixa_topo(P.B('brilho', True), cam, cortes[i] + 0.002, cortes[i + 1] - 0.002, u0, rolar)
    if tala_ini:
        talas(P, cam, 0.0, rolar)
    if junta_meio:
        talas(P, cam, L / 2, rolar)
    if contra:
        contratrilho(P, cam, contra, xs, rolar)
    pedras(P, cam, L, xs, rolar, x_fim=x_leito, oleos=oleos, rampa=rampa)
    sujeira_na_via(P, cam, xs, rolar, oleo_idx, ferr_idx, 3, x_leito)
    mato_na_via(cam, L, xs, rolar, mato, seco, x_fim=x_leito)
    P.fim()
    return P, xs, rolar


def contratrilho(P, cam, faixa, xs, rolar):
    """Contratrilho junto ao trilho interno (lado direito, u<0): barra de guarda com folga de roda, pontas abertas,
    apoiada em cadeiras sobre placas compridas; calço e parafuso atravessando a alma do trilho."""
    x0, x1 = faixa
    UG = -G + 0.034                        # eixo da barra de guarda
    ABRE = 0.14

    def ug(x):
        d = min(x - x0, x1 - x)
        f = max(0.0, 1 - d / ABRE)
        return UG + 0.022 * f * f

    n = int((x1 - x0) / 0.02)
    aneis = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        Q = Quadro(cam, x, rolar(x))
        u = ug(x)
        z0, z1 = ZTB + 0.016, ZTB + HT + 0.012
        if i in (0, n):
            z1 -= 0.012
        aneis.append([bm_v for bm_v in (P.B('ferro').verts.new(Q(u - 0.005, 0, z0)),
                                        P.B('ferro').verts.new(Q(u + 0.005, 0, z0)),
                                        P.B('ferro').verts.new(Q(u + 0.005, 0, z1)),
                                        P.B('ferro').verts.new(Q(u - 0.005, 0, z1)))])
    bm = P.B('ferro')
    for A, Bn in zip(aneis, aneis[1:]):
        for j in range(4):
            bm.faces.new((A[j], A[(j + 1) % 4], Bn[(j + 1) % 4], Bn[j]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])
    faixa_g = P.B('brilho', True)        # face interna da guarda polida pelo friso da roda
    for i in range(n):
        xa, xb = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
        Qa, Qb = Quadro(cam, xa, rolar(xa)), Quadro(cam, xb, rolar(xb))
        ua, ub = ug(xa) - 0.0053, ug(xb) - 0.0053
        decal(faixa_g, [Qa(ua, 0, ZTB + 0.04), Qb(ub, 0, ZTB + 0.04), Qb(ub, 0, ZTB + HT + 0.01), Qa(ua, 0, ZTB + HT + 0.01)], 0)
    for xd in xs:
        if not (x0 + 0.05 <= xd <= x1 - 0.05):
            continue
        Q = Quadro(cam, xd, rolar(xd))
        u = ug(xd)
        caixa_q(P.B('ferro'), Q, u - 0.007, u + 0.03, -0.022, 0.022, ZTB, ZTB + 0.016)         # cadeira (base)
        caixa_q(P.B('ferro'), Q, u + 0.005, u + 0.022, -0.016, 0.016, ZTB + 0.016, ZTB + 0.046)  # encosto
        caixa_q(P.B('ferro'), Q, -G + 0.0031, u - 0.005, -0.011, 0.011, ZTB + 0.017, ZTB + 0.03)  # calço
        p = Q(-G, 0, ZTB + 0.0235)
        tubo(P.B('aco'), p - Q.n * 0.016, Q(u + 0.03, 0, ZTB + 0.0235), 0.003, 8)
        cil(P.B('aco'), p - Q.n * 0.0135, 0.0058, 0.0045, Q.n, lados=6)
        cil(P.B('aco'), Q(u + 0.0245, 0, ZTB + 0.0235), 0.0062, 0.005, Q.n, lados=6)
        parafuso(P.B('aco'), Q, u + 0.02, 0.0, ZTB, 0.005, haste=0)


# ------------------------------------------------------------------ montagem da via
reta_a = Reta((0.5, -2, 0), (0.5, -1, 0))
reta_b = Reta((0.5, -1, 0), (0.5, 0, 0))
curva = Arco((3, 0, 0), 2.5, PI, PI / 2)
reta_c = Reta((3, 2.5, 0), (4, 2.5, 0))
reta_f = Reta((4, 2.5, 0), (5, 2.5, 0))

via('reto_a', reta_a, tala_ini=False, especiais={1: 'rachado'}, oleo_idx=(3,), ferr_idx=(0, 2, 4), mato=5,
    oleos=((0.62, 0.05, 0.08),))
via('reto_b', reta_b, especiais={3: 'madeira', 0: 'rachado'}, oleo_idx=(1, 2), ferr_idx=(1, 4), mato=6,
    oleos=((0.45, -0.03, 0.1),))
via('curva', curva, cant=True, contra=(0.38, curva.L - 0.38), junta_meio=True,
    especiais={6: 'rachado', 14: 'rachado', 11: 'concreto', ('quebra', 11): 1},
    oleo_idx=(4, 9, 15), ferr_idx=(2, 3, 8, 12, 17), mato=16, oleos=((1.2, 0.02, 0.12), (2.9, -0.05, 0.1)))
via('reto_c', reta_c, especiais={2: 'rachado'}, oleo_idx=(2,), ferr_idx=(0, 3), mato=6)
_, XS_F, _ = via('fim', reta_f, fim=True, ferr_idx=(1, 2), mato=16, seco=0.6, oleos=((0.5, 0.2, 0.09),))

# marca de bloco: ponta do dormente pintada onde fica o sinal (borda do bloco)
P = Lote('marca_bloco')
Q = Quadro(reta_a, 0.5, 0)
for u0, mat in ((-UD + 0.005, 'tinta_bloco'), (-UD + 0.045, 'tinta_violeta')):
    caixa_q(P.B(mat), Q, u0, u0 + 0.035, -0.0335, 0.0335, ZD0 + 0.04, ZD0 + 0.0408)
P.fim()


# ------------------------------------------------------------------ para-choque (fim de linha)
def para_choque():
    """Para-choque de atrito: sapatas presas nos trilhos, travessa com listras, 2 amortecedores hidráulicos,
    acumulador, escoras, luz vermelha. Referencial: u à esquerda (norte do mundo), a para leste (fim da linha)."""
    P = Lote('para_choque')
    Qb = Quadro(reta_f, 0.0, 0.0)
    q = lambda u, a, z: Qb(u, a, z)
    T = ZTB + HT                                             # topo do trilho
    XH0, XH1 = 0.62, 0.68                                    # travessa
    ZH0, ZH1 = 0.215, 0.32
    for u0 in (-G, G):
        # viga de apoio sobre o boleto (sola) e garras das sapatas
        caixa_q(P.B('amarelo'), Qb, u0 - 0.02, u0 + 0.02, 0.55, 0.915, T, T + 0.02)
        caixa_q(P.B('ferro'), Qb, u0 - 0.026, u0 + 0.026, 0.55, 0.915, T + 0.02, T + 0.026)
        for a in (0.60, 0.80):
            for lado in (-1, 1):
                ua, ub = sorted((u0 + lado * 0.0128, u0 + lado * 0.025))
                caixa_q(P.B('ferro'), Qb, ua, ub, a - 0.03, a + 0.03, ZTB + 0.037, T)          # garra no boleto
                uc, ud = sorted((u0 + lado * 0.0042, u0 + lado * 0.025))
                caixa_q(P.B('ferro'), Qb, uc, ud, a - 0.03, a + 0.03, ZTB + 0.016, ZTB + 0.034)  # lábio sob o boleto
            for da in (-0.015, 0.015):
                p = Qb(u0, a + da, ZTB + 0.025)
                tubo(P.B('aco'), p - Qb.n * 0.033, p + Qb.n * 0.033, 0.0032, 8)
                for s in (-1, 1):
                    cil(P.B('aco'), p + Qb.n * s * 0.028, 0.0065, 0.006, Qb.n, lados=6)
            # marca de deslize: brilho no boleto à frente da sapata (ela já escorregou uma vez)
        caixa_q(P.B('brilho'), Qb, u0 - 0.0095, u0 + 0.0095, 0.47, 0.55, T + 0.0003, T + 0.0006)
        # pilar dianteiro e escora traseira
        caixa_q(P.B('amarelo'), Qb, u0 - 0.019, u0 + 0.019, XH0, XH0 + 0.04, T + 0.026, ZH0)
        viga(P.B('amarelo'), Qb(u0, XH1 - 0.01, ZH1 - 0.02), Qb(u0, 0.905, T + 0.03), 0.032)
        caixa_q(P.B('ferro'), Qb, u0 - 0.03, u0 + 0.03, 0.86, 0.915, T + 0.026, T + 0.036)     # pé da escora
        for a in (0.875, 0.9):
            for s in (-1, 1):
                parafuso(P.B('aco'), Qb, u0 + s * 0.022, a, T + 0.036, 0.005, haste=0.003)
    # travessa frontal (com listras na face) e reforços
    caixa_q(P.B('amarelo'), Qb, -0.37, 0.37, XH0, XH1, ZH0, ZH1)
    caixa_q(P.B('listras'), Qb, -0.36, 0.36, XH0 - 0.002, XH0, ZH0 + 0.01, ZH1 - 0.01)
    caixa_q(P.B('amarelo'), Qb, -0.372, 0.372, XH0 - 0.004, XH1 + 0.004, ZH1, ZH1 + 0.008)
    caixa_q(P.B('amarelo'), Qb, -0.372, 0.372, XH0 - 0.004, XH1 + 0.004, ZH0 - 0.008, ZH0)
    tubo(P.B('ferro'), Qb(-G, 0.885, T + 0.05), Qb(G, 0.885, T + 0.05), 0.014, 12)          # tirante traseiro
    for u0 in (-G, G):
        viga(P.B('ferro'), Qb(u0, 0.885, T + 0.05), Qb(-u0 * 0.3, XH1, ZH0 + 0.01), 0.012)  # mão-francesa em X
    # remendo de chapa aparafusado na travessa (peça trocada)
    caixa_q(P.B('cinza'), Qb, 0.24, 0.34, XH1, XH1 + 0.005, ZH0 + 0.015, ZH1 - 0.02)
    for uu in (0.25, 0.33):
        for zz in (ZH0 + 0.025, ZH1 - 0.03):
            cil(P.B('aco'), Qb(uu, XH1 + 0.007, zz), 0.0055, 0.004, Qb.t, lados=6)
    # amortecedores hidráulicos
    ZB = 0.268
    for k, u0 in enumerate((-0.2, 0.2)):
        e = -Qb.t
        cil(P.B('ferro', True), Qb(u0, XH0 - 0.006, ZB), 0.058, 0.012, e, lados=24)          # flange
        for j in range(6):
            a = j * PI / 3 + PI / 6
            p = Qb(u0 + 0.046 * math.cos(a), XH0 - 0.014, ZB + 0.046 * math.sin(a))
            cil(P.B('aco'), p, 0.0055, 0.005, e, lados=6)
        cil(P.B('grafite', True), Qb(u0, 0.555, ZB), 0.039, 0.118, e, lados=28)               # camisa
        toro(P.B('grafite', True), Qb(u0, 0.5, ZB), 0.039, 0.004, 28, 8, e)
        cil(P.B('borracha', True), Qb(u0, 0.494, ZB), 0.03, 0.008, e, lados=24)               # vedação
        cil(P.B('cromo', True), Qb(u0, 0.468, ZB), 0.022, 0.05, e, lados=24)                   # haste
        mat_pl = 'oxido' if k == 0 else 'aco'                                              # uma placa trocada
        cil(P.B(mat_pl, True), Qb(u0, 0.437, ZB), 0.065, 0.014, e, lados=32)                   # placa de choque
        cil(P.B('brilho', True), Qb(u0, 0.4298, ZB + 0.004), 0.034, 0.0006, e, lados=24)       # centro polido
        for j in range(4):                                                                 # parafusos escareados
            a = j * PI / 2 + PI / 4
            cil(P.B('aco'), Qb(u0 + 0.045 * math.cos(a), 0.4296, ZB + 0.045 * math.sin(a)), 0.006, 0.0012, e,
                lados=10)
        for j in range(5):                                                                 # riscos de pancada
            a = random.uniform(0, 2 * PI)
            rr = random.uniform(0.01, 0.05)
            p1 = Qb(u0 + rr * math.cos(a), 0.4296, ZB + rr * math.sin(a))
            p2 = p1 + Qb.n * random.uniform(-0.02, 0.02) + Z * random.uniform(-0.015, 0.015)
            tubo(P.B('brilho'), p1, p2, 0.0008, 4)
        # niple de óleo e mangueira até o acumulador
        cil(P.B('aco'), Qb(u0, 0.56, ZB + 0.042), 0.007, 0.012, Z, lados=6)
        pts = bezier(Qb(u0, 0.56, ZB + 0.047), Qb(u0, 0.56, ZB + 0.11), Qb(u0 * 0.6, 0.66, 0.36),
                     Qb(u0 * 0.55 + (0.003 if u0 > 0 else -0.003), 0.69, 0.355), 14)
        mangueira(P.B('borracha'), pts, 0.0065)
        # etiqueta de pressão e plaqueta na camisa
        caixa_q(P.B('adesivo'), Qb, u0 - 0.012, u0 + 0.012, 0.53, 0.575, ZB + 0.0392, ZB + 0.0396)
    # vazamento: óleo escorrendo da camisa esquerda até o dormente
    pe = Qb(-0.2, 0.505, ZB - 0.039)
    for j, (dz, r) in enumerate(((0.0, 0.0045), (0.01, 0.0035))):
        p = pe - Z * dz
        bm = P.B('oleo', True)
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r, matrix=Matrix.Translation(p))
    mancha_em(P.B('oleo'), Qb(-0.2, 0.5, 0), 0.035, ZDT + 0.0007, 1.5)
    # acumulador hidráulico sobre a travessa
    eu = Qb.n
    cil(P.B('grafite', True), Qb(0, 0.69, 0.355), 0.03, 0.22, eu, lados=28)
    for s in (-1, 1):
        cil(P.B('grafite', True), Qb(s * 0.112, 0.69, 0.355), 0.026, 0.006, eu, lados=24)
        cil(P.B('aco'), Qb(s * 0.12, 0.69, 0.355), 0.008, 0.01, eu, lados=6)
        chapa_arco(P.B('ferro', True), Qb(s * 0.07 - 0.009, 0.69, 0.355), eu, 0.0305, 0.003, 0.018,
                   math.radians(-20), math.radians(200), 12)
        caixa_q(P.B('ferro'), Qb, s * 0.07 - 0.012, s * 0.07 + 0.012, 0.655, 0.725, ZH1 + 0.008, ZH1 + 0.012)
    cil(P.B('cromo', True), Qb(0.0, 0.69, 0.391), 0.014, 0.005, Z, lados=20)                    # manômetro
    cil(P.B('aco'), Qb(0.0, 0.69, 0.387), 0.004, 0.006, Z, lados=8)
    cil(P.B('tinta'), Qb(0.0, 0.69, 0.3938), 0.012, 0.0006, Z, lados=20)
    # luz vermelha (pisca) com pala, suporte e eletroduto
    LU = 0.27
    caixa_q(P.B('ferro'), Qb, LU - 0.02, LU + 0.02, XH0 + 0.005, XH1 - 0.005, ZH1 + 0.008, ZH1 + 0.022)
    cil(P.B('grafite', True), Qb(LU, 0.64, 0.355), 0.027, 0.05, -Qb.t, lados=24)
    cil(P.B('luz_fim', True), Qb(LU, 0.614, 0.355), 0.021, 0.004, -Qb.t, lados=24)
    toro(P.B('grafite', True), Qb(LU, 0.615, 0.355), 0.023, 0.003, 24, 6, -Qb.t)
    chapa_arco(P.B('grafite', True), Qb(LU, 0.615, 0.355), -Qb.t, 0.028, 0.002, 0.035, math.radians(-15),
               math.radians(195), 14)
    for j in range(3):                                                                    # grade de proteção
        uu = LU - 0.012 + j * 0.012
        tubo(P.B('aco'), Qb(uu, 0.607, 0.333), Qb(uu, 0.607, 0.377), 0.0012, 4)
    pts = bezier(Qb(LU, 0.665, 0.355), Qb(LU + 0.06, 0.72, 0.36), Qb(0.33, 0.72, 0.25), Qb(0.33, 0.7, T + 0.03),
                 14)
    corrugado(P.B('pvc', True), pts + bezier(Qb(0.33, 0.7, T + 0.03), Qb(0.33, 0.7, 0.04),
                                             Qb(0.4, 0.88, 0.02), Qb(0.41, 0.95, -0.01), 10)[1:], 0.007)
    toro(P.B('aco'), Qb(0.33, 0.702, 0.2), 0.009, 0.002, 16, 6, Z)                        # abraçadeira
    # números de série apagados na travessa (tinta)
    for j in range(5):
        if random.random() < 0.8:
            caixa_q(P.B('tinta'), Qb, -0.33 + j * 0.02, -0.318 + j * 0.02, XH1, XH1 + 0.0008, ZH1 - 0.04,
                    ZH1 - 0.022)
    P.fim()


para_choque()


# ------------------------------------------------------------------ sinal de bloco
SC = Vector((1.5, -1.5, 0))


def ret_arred(bm, c, w, h, r, esp, eixo_y=-1, n=6):
    """Placa retangular de cantos redondos no plano xz, espessura esp para o lado eixo_y."""
    pts = []
    for (cx, cz, a0) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, PI / 2), (-w / 2 + r, -h / 2 + r, PI),
                         (w / 2 - r, -h / 2 + r, 1.5 * PI)):
        for k in range(n + 1):
            a = a0 + (PI / 2) * k / n
            pts.append(Vector((c.x + cx + r * math.cos(a), c.y, c.z + cz + r * math.sin(a))))
    prisma(bm, pts, esp, Vector((0, eixo_y, 0)))


def sinal():
    P = Lote('sinal')
    c = SC
    # sapata e pedestal de concreto
    bm = P.B('concreto2')
    caixa_de(bm, c + Vector((-0.15, -0.15, 0)), c + Vector((0.15, 0.15, 0.045)))
    caixa_de(bm, c + Vector((-0.14, -0.14, 0.045)), c + Vector((0.14, 0.14, 0.055)))
    caixa_de(bm, c + Vector((-0.1, -0.1, 0.055)), c + Vector((0.1, 0.1, 0.15)))
    pedra(bm, c + Vector((0.1, -0.1, 0.15)), 0.008, 0.6)                                  # lasca solta
    caixa_de(P.B('listras'), c + Vector((-0.1005, -0.1005, 0.09)), c + Vector((0.1005, 0.1005, 0.13)))
    caixa_de(P.B('fenda'), c + Vector((0.03, -0.1007, 0.055)), c + Vector((0.033, -0.1004, 0.088)))   # trinca
    # placa de base, chumbadores, nervuras
    caixa_de(P.B('galv'), c + Vector((-0.085, -0.085, 0.15)), c + Vector((0.085, 0.085, 0.162)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = c + Vector((sx * 0.065, sy * 0.065, 0.162))
            cil(P.B('aco'), p + Z * 0.012, 0.0055, 0.024, lados=8)
            cil(P.B('aco'), p + Z * 0.0007, 0.012, 0.0014, lados=16)
            cil(P.B('ferro'), p + Z * 0.0058, 0.0105, 0.009, lados=6)
    for k in range(4):
        a = k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        s = Vector((-d.y, d.x, 0))
        base = [c + d * 0.029 + s * 0.004 + Z * 0.162, c + d * 0.078 + s * 0.004 + Z * 0.162,
                c + d * 0.029 + s * 0.004 + Z * 0.27]
        prisma(P.B('galv'), base, 0.008, -s)
    # mastro
    cil(P.B('galv', True), c + Z * (0.162 + 1.36 / 2), 0.029, 1.36, lados=28)
    caixa_de(P.B('listras'), c + Vector((-0.0295, -0.0295, 0.3)), c + Vector((0.0295, 0.0295, 0.36)))
    cil(P.B('listras', True), c + Z * 0.33, 0.0296, 0.06, lados=28)
    cil(P.B('galv', True), c + Z * 1.525, 0.032, 0.006, lados=28)
    # cabeça do sinal: anteparo, braçadeiras, caixa de LEDs, palas
    Y0 = c.y - 0.029                                         # frente do mastro
    for zz in (1.12, 1.42):
        toro(P.B('aco'), c + Z * zz, 0.031, 0.004, 28, 6)
        caixa_de(P.B('aco'), Vector((c.x - 0.012, Y0 - 0.016, zz - 0.012)), Vector((c.x + 0.012, Y0 + 0.004, zz + 0.012)))
        for sx in (-1, 1):
            cil(P.B('aco'), Vector((c.x + sx * 0.018, c.y + 0.031, zz)), 0.005, 0.01, Vector((0, 1, 0)), lados=6)
    ret_arred(P.B('grafite'), Vector((c.x, Y0 - 0.016, 1.29)), 0.21, 0.46, 0.03, 0.01)       # anteparo
    ret_arred(P.B('tinta_bloco'), Vector((c.x, Y0 - 0.0262, 1.29)), 0.21, 0.46, 0.03, 0.0006)
    ret_arred(P.B('grafite'), Vector((c.x, Y0 - 0.0268, 1.29)), 0.19, 0.44, 0.02, 0.0006)
    YC = Y0 - 0.026
    ret_arred(P.B('grafite'), Vector((c.x, YC, 1.29)), 0.13, 0.41, 0.02, 0.065)              # corpo
    YF = YC - 0.065                                          # face da caixa
    for k in range(5):                                       # aletas no topo (dissipador)
        caixa_de(P.B('ferro'), Vector((c.x - 0.05 + k * 0.025 - 0.002, YF + 0.006, 1.495)),
                 Vector((c.x - 0.05 + k * 0.025 + 0.002, YC - 0.004, 1.505)))
    for zz, chave in ((1.415, 'led_r'), (1.29, 'led_a'), (1.165, 'led_g')):
        cc = Vector((c.x, YF, zz))
        toro(P.B('cromo'), cc - Vector((0, 0.002, 0)), 0.046, 0.003, 32, 6, Vector((0, 1, 0)))
        cil(P.B('preto'), cc - Vector((0, 0.001, 0)), 0.044, 0.002, Vector((0, 1, 0)), lados=32)
        bm = P.B(chave, True)
        pos = [(0, 0)] + [(0.0125 * math.cos(k * PI / 3), 0.0125 * math.sin(k * PI / 3)) for k in range(6)] + \
              [(0.025 * math.cos(k * PI / 6), 0.025 * math.sin(k * PI / 6)) for k in range(12)] + \
              [(0.036 * math.cos(k * PI / 9 + 0.17), 0.036 * math.sin(k * PI / 9 + 0.17)) for k in range(18)]
        for (dx, dz) in pos:
            m = Matrix.Translation(cc + Vector((dx, -0.002, dz))) @ Matrix.Diagonal((1, 0.55, 1, 1))
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0042, matrix=m)
        chapa_arco(P.B('grafite', True), cc, Vector((0, -1, 0)), 0.05, 0.0025, 0.075, math.radians(-12),
                   math.radians(192), 18)
    # plaqueta de identificação do bloco (estêncil apagado)
    caixa_de(P.B('aco'), Vector((c.x - 0.04, YF - 0.002, 1.088)), Vector((c.x + 0.04, YF, 1.112)))
    for j in range(4):
        if random.random() < 0.8:
            caixa_de(P.B('preto'), Vector((c.x - 0.03 + j * 0.016, YF - 0.0026, 1.093)),
                     Vector((c.x - 0.02 + j * 0.016, YF - 0.002, 1.107)))
    # olho da IA no topo (aponta para a via que chega)
    caixa_de(P.B('grafite'), Vector((c.x - 0.022, YF + 0.01, 1.5)), Vector((c.x + 0.022, YC - 0.01, 1.508)))
    cil(P.B('grafite', True), Vector((c.x, YF + 0.025, 1.528)), 0.02, 0.04, Vector((0, 1, 0)), lados=24)
    cil(P.B('preto', True), Vector((c.x, YF + 0.004, 1.528)), 0.016, 0.002, Vector((0, 1, 0)), lados=24)
    cil(P.B('led_v', True), Vector((c.x, YF + 0.0028, 1.528)), 0.008, 0.001, Vector((0, 1, 0)), lados=20)
    toro(P.B('led_v'), Vector((c.x, YF + 0.0032, 1.528)), 0.0125, 0.0012, 24, 4, Vector((0, 1, 0)))
    tubo(P.B('aco'), Vector((c.x + 0.012, YF + 0.04, 1.545)), Vector((c.x + 0.012, YF + 0.04, 1.552)), 0.002, 6)
    # cabo da cabeça descendo pelo mastro (lado leste) com abraçadeiras, até a caixa de controle
    XC = c.x + 0.036
    pts = [Vector((c.x + 0.03, YC + 0.004, 1.09)), Vector((XC, c.y - 0.01, 1.05)), Vector((XC, c.y, 0.95)),
           Vector((XC, c.y, 0.76)), Vector((c.x + 0.03, c.y + 0.06, 0.725)), Vector((c.x + 0.03, c.y + 0.08, 0.705))]
    varrer(P.B('borracha', True), catmull(pts, 5), 0.0065, 10)
    cil(P.B('aco'), Vector((c.x + 0.03, YC + 0.004, 1.083)), 0.009, 0.014, lados=6)            # prensa-cabo
    for zz in (0.8, 0.9, 1.0):
        toro(P.B('aco'), Vector((c.x + 0.004, c.y, zz)), 0.037, 0.0022, 28, 5)
    # caixa de controle (atrás do mastro, lado norte), aletas, tampa aparafusada, LEDs
    X0, X1, Yb, Yt, Zb, Zt = c.x - 0.072, c.x + 0.072, c.y + 0.042, c.y + 0.112, 0.4, 0.7
    caixa_de(P.B('cinza'), Vector((X0, Yb, Zb)), Vector((X1, Yt, Zt)))
    caixa_de(P.B('borracha'), Vector((X0 + 0.004, Yt, Zb + 0.004)), Vector((X1 - 0.004, Yt + 0.002, Zt - 0.004)))
    caixa_de(P.B('cinza'), Vector((X0 + 0.002, Yt + 0.002, Zb + 0.002)), Vector((X1 - 0.002, Yt + 0.008, Zt - 0.002)))
    caixa_de(P.B('oxido'), Vector((X0 + 0.015, Yt + 0.008, Zb + 0.03)), Vector((X0 + 0.07, Yt + 0.011, Zb + 0.1)))
    for (xx, zz) in ((X0 + 0.02, Zb + 0.035), (X0 + 0.065, Zb + 0.035), (X0 + 0.02, Zb + 0.095),
                     (X0 + 0.065, Zb + 0.095)):
        cil(P.B('aco'), Vector((xx, Yt + 0.0125, zz)), 0.003, 0.003, Vector((0, 1, 0)), lados=6)
    for xx in (X0 + 0.012, c.x, X1 - 0.012):
        for zz in (Zb + 0.012, Zt - 0.012):
            mat = 'oxido' if (xx > c.x and zz > 0.5) else 'aco'                   # um parafuso trocado
            cil(P.B(mat), Vector((xx, Yt + 0.0105, zz)), 0.0052, 0.005, Vector((0, 1, 0)), lados=6)
    for k in range(7):                                                            # aletas no lado leste
        zz = Zb + 0.04 + k * 0.035
        caixa_de(P.B('ferro'), Vector((X1, Yb + 0.008, zz - 0.003)), Vector((X1 + 0.012, Yt - 0.008, zz + 0.003)))
    caixa_de(P.B('adesivo'), Vector((X0 + 0.085, Yt + 0.0081, Zt - 0.07)), Vector((X0 + 0.125, Yt + 0.0085, Zt - 0.03)))
    caixa_de(P.B('preto'), Vector((X0 + 0.1, Yt + 0.0086, Zt - 0.062)), Vector((X0 + 0.11, Yt + 0.0089, Zt - 0.044)))
    for j, (chave, xx) in enumerate((('led_v', X1 - 0.05), ('led_c1', X1 - 0.035), ('led_c2', X1 - 0.02))):
        cil(P.B('preto'), Vector((xx, Yt + 0.009, Zt - 0.11)), 0.0055, 0.003, Vector((0, 1, 0)), lados=16)
        bmesh.ops.create_icosphere(P.B(chave, True), subdivisions=2, radius=0.0035,
                                   matrix=Matrix.Translation(Vector((xx, Yt + 0.0108, Zt - 0.11))))
    for k in range(4):                                                            # número de série
        if random.random() < 0.75:
            caixa_de(P.B('tinta'), Vector((X0 + 0.02 + k * 0.016, Yt + 0.0081, Zt - 0.035)),
                     Vector((X0 + 0.03 + k * 0.016, Yt + 0.0085, Zt - 0.018)))
    # escorrido de ferrugem saindo dos parafusos da tampa
    for xx in (X0 + 0.012, X1 - 0.012):
        decal(P.B('oxido'), [Vector((xx - 0.002, Yt + 0.0083, Zb + 0.006)), Vector((xx + 0.002, Yt + 0.0083, Zb + 0.006)),
                             Vector((xx + 0.0015, Yt + 0.0083, Zb + 0.045)), Vector((xx - 0.0015, Yt + 0.0083, Zb + 0.05))], 0)
    for zz in (Zb + 0.06, Zt - 0.06):                                             # braçadeiras ao mastro
        toro(P.B('aco'), c + Z * zz, 0.031, 0.004, 28, 6)
        caixa_de(P.B('aco'), Vector((c.x - 0.015, c.y + 0.028, zz - 0.014)), Vector((c.x + 0.015, Yb, zz + 0.014)))
    # prensa-cabos embaixo e eletroduto corrugado até o pedestal
    for xx in (c.x - 0.035, c.x + 0.035):
        cil(P.B('aco'), Vector((xx, c.y + 0.08, Zb - 0.008)), 0.011, 0.016, lados=6)
    for xx, xp in ((c.x - 0.035, c.x - 0.055), (c.x + 0.035, c.x + 0.055)):
        pts = [Vector((xx, c.y + 0.08, Zb - 0.016)), Vector((xx, c.y + 0.085, 0.3)),
               Vector((xp, c.y + 0.093, 0.2)), Vector((xp, c.y + 0.092, 0.162))]
        corrugado(P.B('pvc', True), catmull(pts, 6), 0.009)
        cil(P.B('galv'), Vector((xp, c.y + 0.092, 0.156)), 0.013, 0.014, lados=6)
    # sujeira: lama respingada no pedestal e mancha no chão
    halo_em('halo_lama', c + Vector((-0.12, 0.05, 0)), 0.18, 0.0012, 1.4)
    P.fim()
    return P


sinal()


# ------------------------------------------------------------------ eletrodutos, caixa de passagem e contato de trilho
def eletrica():
    P = Lote('eletrica')
    # caixa de passagem sobre bloquinho de concreto
    JB = Vector((1.11, -1.6, 0))
    caixa_de(P.B('concreto2'), JB + Vector((-0.07, -0.075, 0)), JB + Vector((0.07, 0.075, 0.022)))
    caixa_de(P.B('cinza'), JB + Vector((-0.045, -0.055, 0.022)), JB + Vector((0.045, 0.055, 0.095)))
    caixa_de(P.B('cinza'), JB + Vector((-0.048, -0.058, 0.095)), JB + Vector((0.048, 0.058, 0.103)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cil(P.B('aco'), JB + Vector((sx * 0.04, sy * 0.05, 0.105)), 0.004, 0.004, lados=6)
    caixa_de(P.B('adesivo'), JB + Vector((-0.02, -0.0555, 0.05)), JB + Vector((0.02, -0.0551, 0.08)))
    caixa_de(P.B('tinta_violeta'), JB + Vector((-0.03, -0.03, 0.1032)), JB + Vector((0.03, -0.015, 0.1036)))
    # eletroduto rígido do pedestal do sinal até a caixa de passagem (no chão, com selas)
    p0 = SC + Vector((-0.15, -0.06, 0.016))
    p1 = JB + Vector((0.045, -0.02, 0.016))
    tubo(P.B('pvc', True), p0 + Vector((0.006, 0, 0)), p1 - Vector((0.004, 0, 0)), 0.012, 16)
    for p in (p0, p1):
        cil(P.B('galv'), p, 0.016, 0.012, Vector((1, 0, 0)), lados=6)
    for t in (0.3, 0.7):
        q = p0.lerp(p1, t)
        chapa_arco(P.B('galv', True), q - Vector((0.008, 0, 0)), Vector((1, 0, 0)), 0.0122, 0.002, 0.016, 0, PI, 10)
        for sy in (-1, 1):
            caixa_de(P.B('galv'), Vector((q.x - 0.008, q.y + sy * 0.0122, 0.0)), Vector((q.x + 0.008, q.y + sy * 0.0142, q.z)))
            caixa_de(P.B('galv'), Vector((q.x - 0.008, q.y + sy * 0.0142, 0.0)), Vector((q.x + 0.008, q.y + sy * 0.03, 0.002)))
            cil(P.B('aco'), Vector((q.x, q.y + sy * 0.022, 0.004)), 0.0045, 0.004, lados=6)
    # ramal para o próximo bloco: corre ao lado da via e mergulha no chão com luva
    p2 = JB + Vector((-0.02, 0.055, 0.03))
    pts = [p2, p2 + Vector((0, 0.04, -0.012)), Vector((p2.x - 0.06, -1.35, 0.014)), Vector((p2.x - 0.08, -1.12, 0.014)),
           Vector((p2.x - 0.08, -1.03, 0.0)), Vector((p2.x - 0.08, -0.99, -0.03))]
    varrer(P.B('pvc', True), catmull(pts, 6), 0.011, 14)
    cil(P.B('concreto2'), Vector((p2.x - 0.08, -1.0, 0.004)), 0.03, 0.008, lados=16)
    cil(P.B('galv'), p2 + Vector((0, -0.006, 0)), 0.015, 0.012, Vector((0, 1, 0)), lados=6)
    # contato de trilho no patim do trilho leste do reto_a, entre dormentes (y = −1,6)
    Q = Quadro(reta_a, 0.4, 0.0)
    T = ZTB + HT
    caixa_q(P.B('ferro'), Q, -0.3, -0.18, -0.02, 0.02, ZTB - 0.006, ZTB)                     # placa sob o patim
    for (ua, ub) in ((-0.2225, -0.212), (-0.268, -0.2575)):                                   # garras no patim
        caixa_q(P.B('ferro'), Q, ua, ub, -0.02, 0.02, ZTB + 0.0058, ZTB + 0.0098)
    caixa_q(P.B('ferro'), Q, -0.214, -0.205, -0.02, 0.02, ZTB, ZTB + 0.0098)
    caixa_q(P.B('ferro'), Q, -0.274, -0.2625, -0.02, 0.02, ZTB, ZTB + 0.0098)
    for uu in (-0.21, -0.268):
        for a in (-0.012, 0.012):
            parafuso(P.B('aco'), Q, uu, a, ZTB + 0.0098, 0.0042, haste=0.003)
    caixa_q(P.B('ferro'), Q, -0.3, -0.292, -0.02, 0.02, ZTB - 0.006, ZTB + 0.052)            # braço vertical
    caixa_q(P.B('grafite'), Q, -0.292, -0.266, -0.03, 0.03, ZTB + 0.02, ZTB + 0.052)         # corpo do sensor
    caixa_q(P.B('preto'), Q, -0.2662, -0.2656, -0.024, 0.024, ZTB + 0.024, ZTB + 0.048)       # face magnética
    caixa_q(P.B('led_v'), Q, -0.2655, -0.2652, -0.018, 0.018, ZTB + 0.0345, ZTB + 0.0375)     # faixa violeta
    caixa_q(P.B('adesivo'), Q, -0.288, -0.27, -0.031, -0.0302, ZTB + 0.026, ZTB + 0.046)
    for a in (-0.022, 0.022):
        parafuso(P.B('aco'), Q, -0.279, a, ZTB + 0.052, 0.0035, haste=0)
    pled = Q(-0.279, 0.0, ZTB + 0.0535)
    bmesh.ops.create_icosphere(P.B('led_s', True), subdivisions=2, radius=0.0042, matrix=Matrix.Translation(pled))
    cil(P.B('preto'), Q(-0.279, 0.0, ZTB + 0.0525), 0.0062, 0.002, Q.up, lados=16)
    cil(P.B('aco'), Q(-0.279, 0.034, ZTB + 0.036), 0.0075, 0.01, Q.t, lados=6)                # prensa-cabo
    pts = [Q(-0.279, 0.039, ZTB + 0.036), Q(-0.285, 0.07, ZTB + 0.02), Q(-0.36, 0.06, ZDT + 0.01),
           Q(-0.45, 0.0, ZDT + 0.004), JB + Vector((-0.12, 0.0, 0.04)), JB + Vector((-0.06, 0.0, 0.05)),
           JB + Vector((-0.045, 0.0, 0.05))]
    corrugado(P.B('pvc', True), catmull(pts, 6), 0.0065)
    cil(P.B('galv'), JB + Vector((-0.05, 0.0, 0.05)), 0.01, 0.01, Vector((1, 0, 0)), lados=6)
    # lama e poça no chão perto da caixa
    mancha_em(P.B('poca'), Vector((1.25, -1.25, 0)), 0.09, 0.0016, 1.7, 0.4)
    halo_em('halo_lama', Vector((1.25, -1.25, 0)), 0.16, 0.0011, 1.6, 0.4)
    halo_em('halo_lama', Vector((0.98, -0.4, 0)), 0.14, 0.0011, 2.0, 1.4)
    P.fim()
    return pled


PLED = eletrica()

# mato em volta do sinal e da caixa, poças e manchas nas laterais da via
for p, h, n, s in (((1.36, -1.32, 0), 0.14, 16, False), ((1.66, -1.62, 0), 0.1, 12, True),
                   ((1.02, -1.78, 0), 0.12, 14, False), ((4.6, 3.02, 0), 0.16, 18, True),
                   ((5.04, 2.3, 0), 0.14, 16, False), ((3.3, 3.0, 0), 0.1, 12, False),
                   ((0.05, 0.6, 0), 0.12, 14, True), ((2.2, 0.35, 0), 0.13, 14, False)):
    tufo(Vector(p), h, n, s, random.random() < 0.5)
P = Lote('chao_sujo')
for c_, r_, m_, al in (((0.98, 0.9), 0.12, 'poca', 2.0), ((2.35, 0.55), 0.1, 'poca', 1.5),
                       ((4.3, 3.05), 0.09, 'poca', 2.2), ((-0.02, -0.6), 0.1, 'oleo', 1.4)):
    mancha_em(P.B(m_), c_, r_, 0.0016, al, random.uniform(0, PI))
    halo_em('halo_lama', c_, r_ * 1.9, 0.001, al, random.uniform(0, PI))
P.fim()


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


Q_VERDE, Q_AMBAR, Q_VERM = (1, 40), (41, 56), (57, 96)
FORCA = {'vermelho': 16.0, 'ambar': 12.0, 'verde': 10.0}


def nivel(q, faixa):
    a, b = faixa
    return suave((q - a + 1.5) / 2.5) * suave((b - q + 1.5) / 2.5)


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for chave, faixa in (('verde', Q_VERDE), ('ambar', Q_AMBAR), ('vermelho', Q_VERM)):
        inp = LUZES[chave].inputs['Emission Strength']
        inp.default_value = 0.04 + FORCA[chave] * nivel(q, faixa)
        inp.keyframe_insert('default_value', frame=q)
    # contato de trilho: pisca curto a cada meio segundo; acende forte quando o bloco ocupa (vermelho)
    pisca = 1.0 if (q % 12) in (8, 9, 10, 11) else 0.0
    ocup = nivel(q, (57, 66))
    inp = LUZES['sensor'].inputs['Emission Strength']
    inp.default_value = 0.05 + 9.0 * max(pisca, ocup)
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZES['fim'].inputs['Emission Strength']
    inp.default_value = 0.3 + 11.0 * (0.5 + 0.5 * math.cos(2 * PI * (q - 70) / 24)) ** 2
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZES['ia'].inputs['Emission Strength']
    inp.default_value = 4.0 + 3.0 * math.sin(2 * PI * fr * 2)
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZES['caixa1'].inputs['Emission Strength']
    inp.default_value = 5.0 if (q // 6) % 2 == 0 else 0.1
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZES['caixa2'].inputs['Emission Strength']
    inp.default_value = 5.0 * nivel(q, Q_AMBAR) + 0.1
    inp.keyframe_insert('default_value', frame=q)
    for o, f0, amp in TUFOS:
        o.rotation_euler = (amp * math.sin(2 * PI * fr * 2 + f0), amp * 0.6 * math.sin(2 * PI * fr + f0 * 1.7), 0)
        o.keyframe_insert('rotation_euler', frame=q)


def linear(ad):
    if not ad or not ad.action:
        return
    curvas = getattr(ad.action, 'fcurves', None)
    if curvas is None:
        curvas = []
        for camada in getattr(ad.action, 'layers', []):
            for faixa in camada.strips:
                for cb in faixa.channelbags:
                    curvas += list(cb.fcurves)
    for fc in curvas:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


for o in sc.objects:
    linear(o.animation_data)
for m in bpy.data.materials:
    if m.node_tree:
        linear(m.node_tree.animation_data)

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (2.5, 0.5, -0.5), (16, 16, 1.0))
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
    prf = bpy.context.preferences.addons['cycles'].preferences
    prf.compute_device_type = 'OPTIX'
    prf.get_devices()
    for dv in prf.devices:
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
cam_d.clip_start = 0.01


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def foto(nome, pos, alvo, lente, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_uma = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None
FOTOS = {
    'conjunto': ('trilhos_conjunto.png', (5.3, -2.9, 2.55), (2.3, 0.75, 0.05), 29, 1600, 1000),
    'perto': ('trilho_perto.png', (0.9, -2.24, 0.2), (0.68, -1.86, 0.095), 30, 1400, 1000),
    'curva': ('trilho_curva.png', (2.45, 0.6, 0.85), (1.3, 1.85, 0.04), 27, 1400, 1000),
    'fim': ('trilho_fim.png', (3.75, 1.65, 0.75), (4.62, 2.5, 0.2), 34, 1400, 1000),
    'sinal': ('sinal_perto.png', (2.3, -2.62, 1.05), (1.38, -1.52, 0.76), 25, 1100, 1300),
    'insp1': ('insp_perfil.png', (0.74, -2.6, 0.115), (0.74, -2.0, 0.115), 200, 1000, 800),
    'insp2': ('insp_contra.png', (1.62, 1.22, 0.5), (1.4, 1.62, 0.08), 32, 1000, 800),
    'insp3': ('insp_sensor.png', (0.98, -1.72, 0.22), (0.76, -1.6, 0.11), 40, 1000, 800),
}
if modo in ('foto', 'teste'):
    sc.cycles.samples = 128 if modo == 'foto' else 24
    sc.frame_set(70)                                   # vermelho aceso, sensor piscando, luz do fim no pico
    for chave, (nome, pos, alvo, lente, rx, ry) in FOTOS.items():
        if (so_uma and chave != so_uma) or (not so_uma and chave.startswith('insp')):
            continue
        if modo == 'teste':
            rx, ry = rx // 2, ry // 2
        foto(nome, pos, alvo, lente, rx, ry)
print('TRILHOS ok')
