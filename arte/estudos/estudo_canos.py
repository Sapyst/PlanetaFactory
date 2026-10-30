"""Estudo isolado (fora do jogo): tubulação industrial da IA — canos (reto, curva, T, cruz), bomba e tanque.
Portas e áreas como no arte/CATALOGO.md (1 tile = 1 m; x leste, y norte; eixo do cano a 0,34 m):
- cano_reto N–S, cano_curva S–L (cotovelo de raio longo, R = 0,5 m = 5 diâmetros), cano_t S/N/L, cano_cruz 4 lados.
  Flanges aparafusadas cuja face fica exatamente na borda do tile: duas peças vizinhas fecham um par de flanges e os
  parafusos (furação simétrica) atravessam os dois. Suportes de perfil H com sela e abraçadeira sobre bloco de concreto.
  Variantes do reto: visor de vidro (seiva âmbar correndo, anéis de campo violeta da IA), junta de dilatação (fole com
  tirantes), isolamento térmico descascado (lata rasgada, lã exposta), tampão cego com respiro e manômetro.
  T e cruz são conexões forjadas (corpo esférico, ressaltos e gargalos cônicos); dreno atuado sob o T, pé fundido na cruz.
- bomba 1×1 sobre a poça de seiva, saída norte: bomba de êmbolo — câmara de sucção mergulhada (crivo, espuma,
  respingos), cilindro com gaxeta, cruzeta (cabecote, com faixa de luz) correndo em duas guias, biela e virabrequim
  com volante, coroa e pinhão, motor com aletas; válvula de retenção e câmara de ar na descarga, manômetro.
- tanque 2×2 (até 1,7 m): cilindro com cintas e rebites, costuras verticais, saia ancorada, visor de nível com a seiva
  subindo e descendo, válvula de alívio que solta vapor, tampa de inspeção para drone (olhal de garra e balizas).
  Canos nos 4 lados no tile da esquerda de quem olha de fora: S0 (−0,5; −1), N0 (+0,5; +1), L0 (+1; +0,5), O0 (−1; −0,5).
Conjunto: bomba (0,0) → reto c/ visor (0,1) → T (0,2) → [curva (0,3) → reto isolado (1,3)] e [reto c/ fole (1,2) →
curva (2,2)] → cruz (2,3) → reto c/ visor (3,3) → tanque (4,5; 3,5) pela boca O0; ramal norte da cruz em tampão (2,4).
Uso: blender -b --python estudo_canos.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(23)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

CZ = 0.34          # eixo do cano
R = 0.10           # raio do cano
RF = 0.158         # raio da flange
EF = 0.035         # espessura da flange
RB = 0.133         # raio da furação


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, Rr, r, nR=48, nr=12, eixo=Z):
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


def varrer(bm, pts, raios, lados=28, tampas=(False, False)):
    """Tubo varrido ao longo de pts (quadros de transporte paralelo): curvas redondas de verdade."""
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


def base_lat(u):
    """Base do plano da flange: s horizontal, cima."""
    u = Vector(u).normalized()
    s = u.cross(Z)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    return s, s.cross(u).normalized() if abs(u.z) > 0.9 else Z.copy()


def chapa_arco(bm, c, u, r_in, esp, larg, a0, a1, n=14):
    """Chapa curva em volta do eixo u (sela, abraçadeira, lata rasgada); ângulo medido de s para cima."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    linhas = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        d = s * math.cos(a) + up * math.sin(a)
        linhas.append([bm.verts.new(c + d * rr + u * w) for rr in (r_in, r_in + esp) for w in (-larg / 2, larg / 2)])
    for A, B in zip(linhas, linhas[1:]):
        for (i, j) in ((0, 1), (3, 2), (2, 0), (1, 3)):
            bm.faces.new((A[i], A[j], B[j], B[i]))
    for L in (linhas[0], linhas[-1]):
        bm.faces.new((L[0], L[1], L[3], L[2]))


def rot_de(u):
    """Matriz que leva x→s, y→u, z→cima (caixas alinhadas ao cano)."""
    u = Vector(u).normalized()
    s, up = base_lat(u)
    return Matrix((s, u, up)).transposed()


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat():
    """Vidro grosso sem refração (não vira lente), verniz que reflete o céu, encardido nas pontas."""
    m = bpy.data.materials.new('Vidro')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.92, 0.9, 0.82, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['Coat Weight'].default_value = 0.8
    b.inputs['Coat Roughness'].default_value = 0.03
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 22.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.75, 'To Min': 0.02, 'To Max': 0.35})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m


FLUXO_F = 7.0      # faixas por metro
FLUXO_K = 14       # faixas que passam por laço (2 m em 4 s)
FASES = []


def fluxo_mat(nome, forca, mundo_z=False):
    """Seiva correndo: faixas âmbar claras/escuras e bolhas que andam ao longo de z do objeto (sentido do fluxo).
    A fase é um nó Valor com quadro-chave: fase(t) cresce FLUXO_K por laço e pulsa a cada golpe da bomba."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.08
    if mundo_z:
        geo = no(nt, 'ShaderNodeNewGeometry')
        vet = geo.outputs['Position']
    else:
        tc = no(nt, 'ShaderNodeTexCoord')
        vet = tc.outputs['Object']
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(vet, sep.inputs[0])
    val = no(nt, 'ShaderNodeValue')
    val.name = 'fase'
    FASES.append(val)
    mz = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    mz.inputs[1].default_value = FLUXO_F
    nt.links.new(sep.outputs['Z'], mz.inputs[0])
    sub = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(mz.outputs['Value'], sub.inputs[0])
    nt.links.new(val.outputs[0], sub.inputs[1])
    pi2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    pi2.inputs[1].default_value = 2 * PI
    nt.links.new(sub.outputs['Value'], pi2.inputs[0])
    sen = no(nt, 'ShaderNodeMath', operation='SINE')
    nt.links.new(pi2.outputs['Value'], sen.inputs[0])
    faixa = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0})
    nt.links.new(sen.outputs['Value'], faixa.inputs['Value'])
    # bolhas: ruído arrastado junto com a fase
    off = no(nt, 'ShaderNodeMath', operation='DIVIDE')
    off.inputs[1].default_value = FLUXO_F
    nt.links.new(val.outputs[0], off.inputs[0])
    comb = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(off.outputs['Value'], comb.inputs['Z'])
    vsub = no(nt, 'ShaderNodeVectorMath', operation='SUBTRACT')
    nt.links.new(vet, vsub.inputs[0])
    nt.links.new(comb.outputs[0], vsub.inputs[1])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 34.0, 'Detail': 2.0})
    nt.links.new(vsub.outputs['Vector'], ru.inputs['Vector'])
    bol = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.64, 'From Max': 0.72})
    nt.links.new(ru.outputs['Fac'], bol.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.45, 0.13, 0.005, 1)
    cor.inputs[7].default_value = (1.0, 0.56, 0.08, 1)
    nt.links.new(faixa.outputs['Result'], cor.inputs[0])
    cor2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor2.inputs[7].default_value = (1.0, 0.68, 0.22, 1)
    nt.links.new(bol.outputs['Result'], cor2.inputs[0])
    nt.links.new(cor.outputs[2], cor2.inputs[6])
    nt.links.new(cor2.outputs[2], b.inputs['Base Color'])
    nt.links.new(cor2.outputs[2], b.inputs['Emission Color'])
    e1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    e1.inputs[1].default_value = 0.7
    e1.inputs[2].default_value = 0.3
    nt.links.new(faixa.outputs['Result'], e1.inputs[0])
    e2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    e2.inputs[1].default_value = 0.6
    nt.links.new(bol.outputs['Result'], e2.inputs[0])
    nt.links.new(e1.outputs['Value'], e2.inputs[2])
    e3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    e3.inputs[1].default_value = forca
    nt.links.new(e2.outputs['Value'], e3.inputs[0])
    nt.links.new(e3.outputs['Value'], b.inputs['Emission Strength'])
    return m


def liquido_mat(nome, cor, forca=0.0, transm=0.4, rough=0.05):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.4
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    b.inputs['Coat Weight'].default_value = 1.0
    return m


def la_mat():
    """Lã mineral do isolamento: fibrosa, amarelada, encardida."""
    m = mats.material('Lã de rocha', (0.62, 0.5, 0.26), 0, 0.98, pintura=False, sujeira=0.9, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = no(nt, 'ShaderNodeTexCoord')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60.0, 60.0, 8.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 10.0})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.6})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def halo_mat():
    """Sujeira em volta das poças: escurece o chão e some em degradê radial (sem borda dura)."""
    m = bpy.data.materials.new('Mancha de sujeira')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.07, 0.06, 0.045, 1)
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
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.62, 'To Min': 0.75, 'To Max': 0.0})
    nt.links.new(soma.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


SEIVA = (1.0, 0.55, 0.06)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'cano': mats.material('Cano de seiva', (0.10, 0.12, 0.10), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.75),
    'tanque': mats.material('Casco do tanque', (0.15, 0.165, 0.14), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.7),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'inox': mats.material('Inox', (0.62, 0.62, 0.62), 1.0, 0.3, pintura=False, ferrugem=0.25, sujeira=0.8, escovado=True),
    'lata': mats.material('Lata do isolamento', (0.55, 0.56, 0.56), 1.0, 0.45, pintura=False, ferrugem=0.3, sujeira=1.0),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'forjado': mats.material('Aço forjado', (0.16, 0.15, 0.14), 0.9, 0.55, pintura=False, ferrugem=0.85, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'halo': halo_mat(),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.02, 0.016, 0.012), 0, 0.32, pintura=False, sujeira=0.0, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.78, 0.72), 0, 0.3, pintura=False, sujeira=0.5, desgaste=0.0),
    'preto': mats.material('Preto', (0.01, 0.01, 0.01), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'crosta': mats.material('Crosta de seiva', (0.30, 0.13, 0.02), 0, 0.5, pintura=False, sujeira=0.6, desgaste=0.0),
    'la': la_mat(),
    'listras': base3d.listras_mat(),
    'vidro': vidro_mat(),
    'fluxo': fluxo_mat('Seiva correndo', 2.6),
    'nivel': fluxo_mat('Seiva no visor de nível', 2.2, mundo_z=True),
    'poca': liquido_mat('Poça de seiva', (0.75, 0.32, 0.02), 0.35, 0.3),
    'derramada': liquido_mat('Seiva derramada', (0.5, 0.2, 0.015), 0.12, 0.2),
    'gota': emissivo('Gota de seiva', SEIVA, 4.0),
    'gota_oleo': mats.material('Gota de óleo', (0.01, 0.009, 0.007), 0, 0.04, pintura=False, sujeira=0.0, desgaste=0.0),
    'espuma': mats.material('Espuma de seiva', (0.95, 0.78, 0.45), 0, 0.6, pintura=False, sujeira=0.0, desgaste=0.0),
    'violeta': emissivo('Campo violeta', (0.55, 0.12, 1.0), 9.0),
    'ambar': emissivo('Luz âmbar', (1.0, 0.5, 0.05), 8.0),
    'verde_luz': emissivo('Luz verde', (0.15, 1.0, 0.25), 6.0),
    'vapor': base3d.volume_mat('Vapor', (0.92, 0.92, 0.94), 6.0, 1.6, 2.6),
})


for n in base3d.M['chao'].node_tree.nodes:                                   # manchas por cima não sujam o chão (AO)
    if n.type == 'AMBIENT_OCCLUSION':
        n.only_local = True


def tinta_mat():
    """Tinta de estêncil gasta (números de série): branca encardida, falhando em manchas (alfa por ruído)."""
    m = mats.material('Estêncil apagado', (0.72, 0.7, 0.62), 0, 0.8, pintura=False, sujeira=0.9, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 140.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.6, 'To Min': 0.0, 'To Max': 0.8})
    nt.links.new(ru.outputs['Fac'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def rustico(m, poeira=1.0, lama=1.0, fuligem=1.0, amassado=0.12):
    """Camada de uso por cima de qualquer material: poeira assentada no que olha para cima, lama respingada
    embaixo (até ~0,16 m), manchas de fuligem e amassados (bump de voronoi). Tudo em coordenada de mundo."""
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
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
    pr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.62, 'To Min': 0.25, 'To Max': 0.95 * poeira})
    nt.links.new(ru.outputs['Fac'], pr.inputs['Value'])
    fp = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(cima.outputs['Result'], fp.inputs[0])
    nt.links.new(pr.outputs['Result'], fp.inputs[1])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.03, 'From Max': 0.17, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sp.outputs['Z'], baixo.inputs['Value'])
    lr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.6, 'To Min': 0.3, 'To Max': 1.0 * lama})
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
    c2.inputs[7].default_value = (0.36, 0.31, 0.24, 1)               # poeira
    nt.links.new(fp.outputs['Value'], c2.inputs[0])
    nt.links.new(c1.outputs[2], c2.inputs[6])
    c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c3.inputs[7].default_value = (0.1, 0.07, 0.04, 1)                # lama
    nt.links.new(fl.outputs['Value'], c3.inputs[0])
    nt.links.new(c2.outputs[2], c3.inputs[6])
    nt.links.new(c3.outputs[2], b.inputs['Base Color'])
    # poeira e lama deixam fosco
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
    if met or b.inputs['Metallic'].default_value > 0:               # poeira/lama não são metal
        mm = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        nt.links.new(soma.outputs['Value'], mm.inputs[0])
        if met:
            nt.links.new(met.from_socket, mm.inputs[2])
        else:
            mm.inputs[2].default_value = b.inputs['Metallic'].default_value
        mm.inputs[3].default_value = 0.0
        nt.links.new(mm.outputs[0], b.inputs['Metallic'])
    # amassados e mossas
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


base3d.M.update({
    'tinta': tinta_mat(),
    'oxido': mats.material('Primer vermelho', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'cinza': mats.material('Peça trocada cinza', (0.33, 0.34, 0.33), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.5),
    'fio_v': mats.material('Fio vermelho', (0.5, 0.03, 0.02), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'fio_a': mats.material('Fio azul', (0.03, 0.08, 0.4), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'fio_m': mats.material('Fio amarelo', (0.55, 0.42, 0.03), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
})
for chave, kw in (('amarelo', {}), ('grafite', {}), ('cano', {}), ('tanque', dict(amassado=0.12)),
                  ('ferro', dict(amassado=0.1)), ('forjado', dict(amassado=0.1)), ('lata', dict(amassado=0.4)),
                  ('aco', dict(amassado=0.0, fuligem=0.5)), ('oxido', {}), ('cinza', {}), ('inox', dict(amassado=0.0)),
                  ('concreto', dict(amassado=0.0, fuligem=0.6)), ('borracha', dict(amassado=0.0, fuligem=0.0)),
                  ('cromo', dict(amassado=0.0, poeira=0.4, fuligem=0.3))):
    rustico(base3d.M[chave], **kw)


# ------------------------------------------------------------------ peça: geometria local (tile) → mundo
class Peca:
    def __init__(s, nome, cx, cy, quartos=0):
        s.nome = nome
        s.M = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(quartos * PI / 2, 4, 'Z')
        s.Rm = Matrix.Rotation(quartos * PI / 2, 3, 'Z')
        s.bms = {}

    def B(s, mat, liso=False):
        if (mat, liso) not in s.bms:
            s.bms[(mat, liso)] = bmesh.new()
        return s.bms[(mat, liso)]

    def W(s, p):
        return s.M @ Vector(p)

    def D(s, d):
        return s.Rm @ Vector(d)

    def fim(s):
        for (mat, liso), bm in s.bms.items():
            bm.transform(s.M)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            o = obj('%s_%s' % (s.nome, mat), bm, mat)
            if liso:
                suavizar(o)


GOTAS = []        # (ponto onde a gota se forma, mundo; material; vezes por laço; fase)
GAUGES = []


def halo(c, r, z):
    bm = bmesh.new()
    mancha(bm, c, r * 2.0, z - 0.0008)
    obj('halo', bm, 'halo')


def pingo(P, p_local, mat='gota', vezes=1, poca='derramada', r_poca=0.07):
    p = P.W(p_local)
    GOTAS.append((p, mat, vezes, random.random()))
    bm = bmesh.new()
    mancha(bm, (p.x, p.y), r_poca, 0.0025 + random.random() * 0.001)
    obj('poca_pingo', bm, poca)


def flange(P, c, u, pescoco=True, cano='cano', mat='ferro'):
    """Flange com a face em c (normal u, para fora). Furação em π/8 + kπ/4: simétrica, casa com a do vizinho."""
    c, u = Vector(c), Vector(u).normalized()
    if pescoco:
        cil(P.B(cano, True), c - u * 0.0575, R, 0.045, u, lados=32, r2=0.112)
    cil(P.B(mat, True), c - u * EF / 2, RF, EF, u, lados=40)
    s, up = base_lat(u)
    bp = P.B('aco')
    for k in range(8):
        a = PI / 8 + k * PI / 4
        p = c + (s * math.cos(a) + up * math.sin(a)) * RB
        tubo(bp, p - u * 0.058, p, 0.0105, 8)
        cil(bp, p - u * (EF + 0.008), 0.019, 0.016, u, lados=6)


def manometro(P, pos, normal, haste, r=0.036):
    """Manômetro pequeno: haste, caixa cromada, mostrador e ponteiro (treme com os golpes da bomba)."""
    pos, n = P.W(pos), P.D(normal).normalized()
    bm, bf = bmesh.new(), bmesh.new()
    tubo(bm, P.W(haste), pos, 0.007, 8)
    tubo(bm, pos - n * 0.012, pos + n * 0.012, r, 24)
    tubo(bm, pos + n * 0.012, pos + n * 0.016, r * 1.06, 24)
    tubo(bf, pos + n * 0.011, pos + n * 0.0135, r * 0.9, 24)
    suavizar(obj('manometro', bm, 'cromo'))
    obj('mostrador', bf, 'mostrador')
    e = bpy.data.objects.new('ponteiro_piv', None)
    sc.collection.objects.link(e)
    e.location = pos + n * 0.0145
    e.rotation_mode = 'QUATERNION'
    e.rotation_quaternion = n.to_track_quat('Z', 'Y')
    bm = bmesh.new()
    caixa(bm, (0, r * 0.35, 0), (0.004, r * 0.75, 0.002))
    caixa(bm, (r * 0.0, 0, -0.0005), (0.008, 0.008, 0.002))
    obj('ponteiro', bm, 'preto', e)
    GAUGES.append((e, n, random.uniform(-0.6, 0.6)))


def suporte(P, c, u, r=R, cor='amarelo'):
    """Suporte de chão: bloco de concreto, chapa chumbada, perfil H, sela por baixo e abraçadeira por cima."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    rot = rot_de(u)
    chapa_arco(P.B('ferro', True), c, u, r + 0.001, 0.016, 0.1, math.radians(193), math.radians(347), 16)
    chapa_arco(P.B('aco', True), c, u, r + 0.001, 0.005, 0.04, math.radians(-10), math.radians(190), 20)
    zb = c.z - r - 0.014
    for sx in (-1, 1):                                                      # orelhas da sela e parafusos da abraçadeira
        q = c + s * sx * (r + 0.03) + Z * (-0.03)
        caixa(P.B('ferro'), q, (0.05, 0.1, 0.012), rot)
        tubo(P.B('aco'), q - Z * 0.02, q + Z * 0.035, 0.006, 6)
        cil(P.B('aco'), q + Z * 0.012, 0.011, 0.01, lados=6)
    pe = Vector((c.x, c.y, 0))
    caixa_de(P.B('concreto'), pe + Vector((-0.13, -0.13, 0)), pe + Vector((0.13, 0.13, 0.05)))
    caixa(P.B('ferro'), pe + Z * 0.0575, (0.2, 0.2, 0.015), rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = pe + rot @ Vector((sx * 0.075, sy * 0.075, 0.07))
            tubo(P.B('aco'), q - Z * 0.008, q + Z * 0.022, 0.006, 6)
            cil(P.B('aco'), q, 0.012, 0.01, lados=6)
    h = zb - 0.065
    m = pe + Z * (0.065 + h / 2)
    caixa(P.B(cor), m, (0.012, 0.075, h), rot)                              # alma
    for sy in (-1, 1):
        caixa(P.B(cor), m + u * sy * 0.035, (0.075, 0.01, h), rot)          # mesas
    caixa(P.B(cor), pe + Z * (zb - 0.006), (0.11, 0.1, 0.012), rot)         # chapa de topo


def remendo(P, c, u, r, a0, a1, larg, mat='oxido'):
    """Remendo de chapa aparafusado sobre o cano/casco (eixo u, raio r): chapa curva e parafusos nos cantos."""
    c, u = Vector(c), Vector(u).normalized()
    chapa_arco(P.B(mat, True), c, u, r + 0.001, 0.006, larg, a0, a1, 10)
    s, up = base_lat(u)
    for a in (a0 + 0.08 * (a1 - a0), a1 - 0.08 * (a1 - a0)):
        d = s * math.cos(a) + up * math.sin(a)
        for w in (-larg / 2 + 0.014, larg / 2 - 0.014):
            cil(P.B('aco'), c + d * (r + 0.009) + u * w, 0.008, 0.008, d, lados=6)
    for k in range(3):                                                  # solda escorrida na borda do remendo
        a = a0 + (a1 - a0) * random.random()
        d = s * math.cos(a) + up * math.sin(a)
        caixa(P.B('ferro'), c + d * (r + 0.004) + u * (larg / 2 + 0.003), (0.006, 0.006, 0.006))


SEG = dict(a=(0, 1, 1, 0), b=(1, 1, 0, 1), c=(1, 0, 0, 1), d=(0, 0, 1, 0), e=(0, 0, 0, 1), f=(0, 1, 0, 1), g=(0, 0.5, 1, 0))
DIG = ['abcdef', 'bc', 'abged', 'abgcd', 'fgbc', 'afgcd', 'afgedc', 'abc', 'abcdefg', 'abfgcd']


def serie(P, c, u, r, ang, n=6, alt=0.03, apagado=0.35):
    """Número de série em estêncil (7 segmentos) sobre o cilindro de eixo u e raio r, no ângulo ang; parte apagada."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    d = s * math.cos(ang) + up * math.sin(ang)
    t = d.cross(u).normalized()
    larg = alt * 0.55
    rot = Matrix((u, t, d)).transposed()
    bm = P.B('tinta')
    texto = [random.choice(DIG) for _ in range(n)]
    texto.insert(2, 'g')                                                # traço
    for i, dg in enumerate(texto):
        x0 = (i - len(texto) / 2) * larg * 1.5
        for sg in dg:
            if random.random() < apagado:
                continue
            hx, hy, vx, vy = SEG[sg]
            if sg in 'adg':
                p = Vector((x0 + larg / 2, alt * (hy - 0.5), 0))
                tam = (larg * 0.8, alt * 0.12, 0.0015)
            else:
                p = Vector((x0 + larg * hx, alt * (0.25 if sg in 'bf' else -0.25), 0))
                tam = (larg * 0.16, alt * 0.42, 0.0015)
            caixa(bm, c + d * (r + 0.0012) + rot @ p, tam, rot)


def fios(P, a, b, n=3, solto=0.06):
    """Fiação exposta: feixe de fios coloridos de a até b, com a ponta desencapada caindo."""
    a, b = Vector(a), Vector(b)
    for k, m in enumerate(('fio_v', 'fio_a', 'fio_m')[:n]):
        off = Vector(((k - 1) * 0.008, (k - 1) * 0.006, 0))
        meio = (a + b) / 2 + Vector((0, 0, -solto)) + off * 2
        pts = bezier(a + off, a + off + Vector((0, 0, -solto * 0.6)), meio, b + off, 10)
        mangueira(P.B(m), pts, 0.0045)
        tubo(P.B('cobre'), b + off, b + off + (b - meio).normalized() * 0.015, 0.002, 6)


def amassar(bm, n0, centro, raio, prof, eixo_c):
    """Amassado de verdade: empurra os vértices novos (n0 em diante) perto de centro em direção ao eixo."""
    centro = Vector(centro)
    for v in list(bm.verts)[n0:]:
        dd = (v.co - centro).length
        if dd < raio:
            ax = eixo_c(v.co)
            dirv = (v.co - ax)
            if dirv.length > 1e-6:
                v.co -= dirv.normalized() * prof * (0.5 + 0.5 * math.cos(PI * dd / raio))


# ------------------------------------------------------------------ canos
def cano_reto(nome, cx, cy, quartos=0, var='simples', sentido=1):
    P = Peca(nome, cx, cy, quartos)
    C = lambda y: Vector((0, y, CZ))
    yN, yS = 0.5, -0.5
    flange(P, C(yS), (0, -1, 0))
    if var == 'tampao':
        flange(P, C(0.44), (0, 1, 0))
        cil(P.B('ferro', True), C(0.4575), RF, 0.035, (0, 1, 0), lados=40)   # flange cega
        bp = P.B('aco')
        for k in range(8):
            a = PI / 8 + k * PI / 4
            p = C(0.44) + Vector((math.cos(a), 0, math.sin(a))) * RB
            cil(bp, p + Vector((0, 0.043, 0)), 0.019, 0.016, (0, 1, 0), lados=6)
            tubo(bp, p, p + Vector((0, 0.057, 0)), 0.0105, 8)
        tubo(P.B('cano', True), C(-0.47), C(0.41), R, 32)
        tubo(P.B('cano', True), C(0.1) + Z * 0.08, C(0.1) + Z * 0.125, 0.022, 16)        # respiro no topo
        cil(P.B('ferro', True), C(0.1) + Z * 0.135, 0.032, 0.02, lados=16)
        cil(P.B('grafite', True), C(0.1) + Z * 0.15, 0.022, 0.012, lados=16)
        caixa(P.B('grafite'), C(0.1) + Vector((0.035, 0, 0.142)), (0.03, 0.04, 0.03))    # solenoide
        caixa(P.B('verde_luz'), C(0.1) + Vector((0.051, 0, 0.148)), (0.003, 0.012, 0.006))
        manometro(P, C(-0.15) + Vector((-0.17, 0, 0.03)), (-1, 0, 0), C(-0.15) + Vector((-0.09, 0, 0.02)))
        suporte(P, C(-0.15), (0, 1, 0))
        serie(P, C(-0.32), (0, 1, 0), R, math.radians(30), 5)
        remendo(P, C(0.22), (0, 1, 0), R, math.radians(100), math.radians(170), 0.08)
        pingo(P, C(0.44) + Vector((0, 0.0, -RF)), 'gota', 1)
        P.fim()
        return P
    flange(P, C(yN), (0, 1, 0))
    if var == 'simples':
        tubo(P.B('cano', True), C(-0.47), C(0.47), R, 32)
        suporte(P, C(0), (0, 1, 0))
    elif var == 'visor':
        tubo(P.B('cano', True), C(-0.47), C(-0.23), R, 32)
        tubo(P.B('cano', True), C(0.23), C(0.47), R, 32)
        for yy, sg in ((-0.2, 1), (0.2, -1)):
            flange(P, C(yy), (0, sg, 0))                                    # flange do cano
            flange(P, C(yy), (0, -sg, 0), pescoco=False)                    # porta-vidro
            cil(P.B('borracha', True), C(yy - sg * (EF + 0.004)), 0.1, 0.008, (0, 1, 0), lados=32)
        tubo(P.B('vidro', True), C(-0.165), C(0.165), 0.093, 40)
        for k in range(4):                                                  # tirantes do visor
            a = k * PI / 2
            p = Vector((math.cos(a), 0, math.sin(a))) * RB
            tubo(P.B('aco', True), C(-0.25) + p, C(0.25) + p, 0.0075, 10)
            for yy in (-0.243, 0.243, -0.157, 0.157):
                cil(P.B('aco'), C(yy) + p, 0.015, 0.012, (0, 1, 0), lados=6)
        for yy in (-0.07, 0.07):                                            # anéis de campo da IA (soltos no ar)
            toro(P.B('violeta', True), C(yy), 0.112, 0.004, 48, 8, eixo=(0, 1, 0))
        # fluido: objeto próprio com z no sentido do fluxo
        a, b = P.W(C(-0.162 * sentido)), P.W(C(0.162 * sentido))
        bm = bmesh.new()
        cil(bm, Vector((0, 0, (b - a).length / 2)), 0.084, (b - a).length, lados=40)
        o = suavizar(obj('%s_seiva' % nome, bm, 'fluxo'))
        o.location = a
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
        suporte(P, C(-0.35), (0, 1, 0))
        suporte(P, C(0.35), (0, 1, 0))
        manometro(P, C(0.32) + Vector((0.16, 0, 0.04)), (1, 0, 0), C(0.32) + Vector((0.08, 0, 0.03)))
        serie(P, C(0.35), (0, 1, 0), R, math.radians(150), 5)
        remendo(P, C(-0.36), (0, 1, 0), R, math.radians(25), math.radians(95), 0.07)
    elif var == 'dilatacao':
        tubo(P.B('cano', True), C(-0.47), C(-0.12), R, 32)
        tubo(P.B('cano', True), C(0.12), C(0.47), R, 32)
        n = 7 * 8
        pts = [C(-0.1 + 0.2 * i / n) for i in range(n + 1)]
        raios = [0.112 + 0.017 * (0.5 - 0.5 * math.cos(2 * PI * 7 * i / n)) for i in range(n + 1)]
        varrer(P.B('inox', True), pts, raios, 40)
        for yy in (-0.11, 0.11):
            cil(P.B('ferro', True), C(yy), 0.128, 0.022, (0, 1, 0), lados=40)
        for k in range(3):                                                  # tirantes com orelhas e porcas
            a = PI / 2 + k * 2 * PI / 3
            d = Vector((math.cos(a), 0, math.sin(a)))
            for yy in (-0.11, 0.11):
                caixa(P.B('ferro'), C(yy) + d * 0.152, (0.035, 0.022, 0.05), Matrix.Rotation(-a + PI / 2, 3, 'Y'))
            p = C(0) + d * 0.162
            tubo(P.B('aco', True), p - Vector((0, 0.16, 0)), p + Vector((0, 0.16, 0)), 0.008, 10)
            for yy in (-0.131, 0.131, -0.089, 0.089):
                cil(P.B('aco'), p + Vector((0, yy - 0.0, 0)), 0.015, 0.012, (0, 1, 0), lados=6)
        suporte(P, C(-0.32), (0, 1, 0))
        suporte(P, C(0.32), (0, 1, 0), cor='cinza')                         # suporte trocado, de outra cor
        remendo(P, C(-0.2), (0, 1, 0), R, math.radians(40), math.radians(140), 0.075)
        serie(P, C(0.3), (0, 1, 0), R, math.radians(35), 4)
        pingo(P, C(0.03) + Vector((0, 0, -0.128)), 'gota', 2, r_poca=0.09)
    elif var == 'isolado':
        tubo(P.B('cano', True), C(-0.47), C(0.47), R, 32)
        tubo(P.B('lata', True), C(-0.42), C(-0.06), 0.14, 40)
        tubo(P.B('lata', True), C(0.1), C(0.42), 0.14, 40)
        bm = P.B('la', True)
        n0 = len(bm.verts)
        pts = [C(-0.075 + 0.19 * i / 12) for i in range(13)]
        varrer(bm, pts, [0.125 + random.uniform(-0.004, 0.006) for _ in pts], 28, (True, True))
        for v in list(bm.verts)[n0:]:                                       # fibra desfiada
            d = (v.co - Vector((0, v.co.y, CZ)))
            if d.length > 0.05:
                v.co += d.normalized() * random.uniform(-0.004, 0.008)
        for yy in (-0.36, -0.14, 0.2, 0.36):                                # cintas da lata
            cil(P.B('aco', True), C(yy), 0.1435, 0.014, (0, 1, 0), lados=40)
        chapa_arco(P.B('lata', True), C(0.13) + Vector((0.02, 0, -0.012)), (0, 1, 0), 0.142, 0.002, 0.07,
                   math.radians(-55), math.radians(15), 12)                 # aba de lata solta, descascando
        chapa_arco(P.B('lata', True), C(-0.075) + Vector((-0.03, 0, 0.02)), (0, 1, 0), 0.142, 0.002, 0.04,
                   math.radians(110), math.radians(175), 10)
        suporte(P, C(0.27), (0, 1, 0), r=0.14)
        serie(P, C(-0.25), (0, 1, 0), 0.14, math.radians(100), 5, 0.035)
        serie(P, C(0.28), (0, 1, 0), 0.14, math.radians(75), 4, 0.03, 0.55)
        suporte(P, C(-0.27), (0, 1, 0), r=0.14)
    P.fim()
    return P


def cano_curva(nome, cx, cy, quartos=0):
    """Cotovelo de raio longo (centro no canto sudeste, R = 0,5 m), soldado às flanges; cordões de solda."""
    P = Peca(nome, cx, cy, quartos)
    cen = Vector((0.5, -0.5, CZ))
    n = 40
    pts = [cen + Vector((math.cos(a), math.sin(a), 0)) * 0.5 for a in (PI - (PI / 2) * i / n for i in range(n + 1))]
    bmc = P.B('cano', True)
    n0 = len(bmc.verts)
    varrer(bmc, pts, R, 32)
    ad = 3 * PI / 4 - 0.3                                                   # amassado no lado de fora, em cima
    pd = cen + Vector((math.cos(ad), math.sin(ad), 0)) * (0.5 + R * 0.6) + Z * R * 0.8
    amassar(bmc, n0, pd, 0.075, 0.022, lambda v: cen + (v - cen).xy.to_3d().normalized() * 0.5 if (v - cen).xy.length > 1e-6 else cen)
    ar = 3 * PI / 4 + 0.35
    remendo(P, cen + Vector((math.cos(ar), math.sin(ar), 0)) * 0.5, Vector((math.sin(ar), -math.cos(ar), 0)), R,
            math.radians(60), math.radians(150), 0.08)
    ap = PI - 0.42
    serie(P, cen + Vector((math.cos(ap), math.sin(ap), 0)) * 0.5, Vector((math.sin(ap), -math.cos(ap), 0)), R,
          math.radians(30), 3, 0.025)
    flange(P, Vector((0, -0.5, CZ)), (0, -1, 0))
    flange(P, Vector((0.5, 0, CZ)), (1, 0, 0))
    for a in (PI - 0.2, PI / 2 + 0.2, 3 * PI / 4):                          # cordões de solda
        p = cen + Vector((math.cos(a), math.sin(a), 0)) * 0.5
        toro(P.B('ferro', True), p, R + 0.002, 0.005, 40, 6, eixo=Vector((-math.sin(a), math.cos(a), 0)))
    a = 3 * PI / 4 + 0.22
    p = cen + Vector((math.cos(a), math.sin(a), 0)) * 0.5
    suporte(P, p, Vector((math.sin(a), -math.cos(a), 0)))
    P.fim()
    return P


def forjado_hub(P, lados, pe=True, trocada=''):
    """Corpo forjado: esfera, ressaltos e gargalos cônicos até o cano; flange na borda de cada lado."""
    c = Vector((0, 0, CZ))
    bmesh.ops.create_uvsphere(P.B('forjado', True), u_segments=40, v_segments=20, radius=0.158,
                              matrix=Matrix.Translation(c))
    dirs = dict(N=Vector((0, 1, 0)), S=Vector((0, -1, 0)), L=Vector((1, 0, 0)), O=Vector((-1, 0, 0)))
    for l in lados:
        d = dirs[l]
        tubo(P.B('forjado', True), c, c + d * 0.13, 0.142, 40)
        cil(P.B('forjado', True), c + d * 0.17, 0.142, 0.08, d, lados=40, r2=R)  # gargalo
        toro(P.B('forjado', True), c + d * 0.13, 0.142, 0.006, 40, 8, eixo=d)    # rebarba da matriz
        tubo(P.B('cano', True), c + d * 0.2, c + d * 0.47, R, 32)
        toro(P.B('ferro', True), c + d * 0.21, R + 0.002, 0.005, 40, 6, eixo=d)  # solda
        flange(P, c + d * 0.5, d, mat='oxido' if l == trocada else 'ferro')
    for k in range(2):                                                      # plaqueta de identificação da IA
        caixa(P.B('ambar'), c + Vector((-0.112, -0.098, 0.04 + k * 0.012)), (0.03, 0.002, 0.004),
              Matrix.Rotation(-PI / 4, 3, 'Z'))
    return c


def cano_t(nome, cx, cy, quartos=0):
    P = Peca(nome, cx, cy, quartos)
    c = forjado_hub(P, 'SNL', trocada='L')
    fios(P, c + Vector((0.07, -0.02, -0.23)), c + Vector((0.11, -0.09, -0.3)))
    serie(P, Vector((0, -0.3, CZ)), (0, 1, 0), R, math.radians(160), 4, 0.025)
    # dreno atuado sob o corpo
    tubo(P.B('cano', True), c - Z * 0.14, c - Z * 0.225, 0.022, 16)
    bmesh.ops.create_uvsphere(P.B('ferro', True), u_segments=20, v_segments=10, radius=0.036,
                              matrix=Matrix.Translation(c - Z * 0.25))
    cil(P.B('ferro', True), c - Z * 0.225, 0.03, 0.012, lados=16)
    tubo(P.B('cano', True), c - Z * 0.25, c + Vector((-0.07, 0, -0.25)), 0.016, 14)   # saída do dreno
    bmesh.ops.create_uvsphere(P.B('cano', True), u_segments=14, v_segments=8, radius=0.016,
                              matrix=Matrix.Translation(c + Vector((-0.07, 0, -0.25))))
    tubo(P.B('cano', True), c + Vector((-0.07, 0, -0.25)), c + Vector((-0.07, 0, -0.29)), 0.016, 14)
    caixa(P.B('grafite'), c + Vector((0.055, 0, -0.25)), (0.04, 0.045, 0.05))           # atuador do dreno
    caixa(P.B('ambar'), c + Vector((0.076, 0, -0.24)), (0.002, 0.016, 0.006))
    mangueira(P.B('borracha'), bezier(c + Vector((0.07, 0.02, -0.27)), c + Vector((0.12, 0.05, -0.32)),
                                      c + Vector((0.16, 0.1, -0.33)), Vector((0.2, 0.16, 0.012)), 8), 0.008)
    pingo(P, c + Vector((-0.07, 0, -0.295)), 'gota', 2, r_poca=0.1)
    suporte(P, Vector((0, -0.34, CZ)), (0, 1, 0))
    suporte(P, Vector((0.34, 0, CZ)), (1, 0, 0))
    P.fim()
    return P


def cano_cruz(nome, cx, cy, quartos=0):
    P = Peca(nome, cx, cy, quartos)
    c = forjado_hub(P, 'SNLO')
    serie(P, Vector((-0.33, 0, CZ)), (1, 0, 0), R, math.radians(70), 4, 0.025)
    remendo(P, Vector((0.32, 0, CZ)), (1, 0, 0), R, math.radians(200), math.radians(260), 0.07, 'cinza')
    # pé fundido sob o corpo
    caixa_de(P.B('concreto'), (-0.14, -0.14, 0), (0.14, 0.14, 0.05))
    cil(P.B('ferro', True), Vector((0, 0, 0.06)), 0.11, 0.02, lados=24)
    cil(P.B('forjado', True), Vector((0, 0, 0.13)), 0.06, 0.12, lados=24, r2=0.045)
    for k in range(4):
        a = PI / 4 + k * PI / 2
        cil(P.B('aco'), Vector((math.cos(a) * 0.085, math.sin(a) * 0.085, 0.075)), 0.012, 0.012, lados=6)
    # manômetro na diagonal (entre os ramais)
    d = Vector((-1, -1, 0)).normalized()
    manometro(P, c + d * 0.27 + Z * 0.02, d, c + d * 0.15)
    P.fim()
    return P


# ------------------------------------------------------------------ bomba de êmbolo (1×1, saída norte)
PC = Vector((0, -0.06, 0))         # eixo da coluna da bomba
ZK = 0.92                          # virabrequim
RC, LB = 0.06, 0.22                # raio da manivela, biela
NGOLPES = 6                        # golpes por laço


def dentes(bm, c, eixo, r, n, alt, larg, esp, fase=0.0):
    e = Vector(eixo).normalized()
    s, up = Vector((0, 1, 0)), Vector((0, 0, 1))
    for k in range(n):
        a = fase + k * 2 * PI / n
        d = s * math.cos(a) + up * math.sin(a)
        rot = Matrix((e, d, e.cross(d))).transposed()
        caixa(bm, c + d * (r + alt / 2), (esp, alt, larg), rot)


def bomba(cx, cy):
    P = Peca('bomba', cx, cy, 0)
    # poça de seiva e crosta
    bm = bmesh.new()
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=0.36)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.12 * math.sin(a * 3 + 0.7) + 0.06 * math.sin(a * 5 + 2.0)
        v.co = Vector((PC.x + v.co.x * f, PC.y + v.co.y * f * 0.98, 0.006))
    obj('poca_seiva', bm, 'poca')
    bm = bmesh.new()
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=0.41)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.1 * math.sin(a * 3 + 0.7) + 0.05 * math.sin(a * 7 + 1.0)
        v.co = Vector((PC.x + v.co.x * f, PC.y + v.co.y * f * 0.98, 0.003))
    obj('poca_crosta', bm, 'crosta')
    # estrado: 4 pernas, travessas na borda e duas longarinas que seguram a flange da coluna
    am = P.B('amarelo')
    for sx in (-1, 1):
        for sy in (-1, 1):
            caixa_de(P.B('cinza') if sx > 0 and sy > 0 else am, (sx * 0.42 - 0.03, sy * 0.42 - 0.03, 0.012), (sx * 0.42 + 0.03, sy * 0.42 + 0.03, 0.2))
            caixa_de(P.B('ferro'), (sx * 0.42 - 0.05, sy * 0.42 - 0.05, 0), (sx * 0.42 + 0.05, sy * 0.42 + 0.05, 0.012))
            for k in range(2):
                q = Vector((sx * 0.42 + (k - 0.5) * 0.07 * sx, sy * 0.42 - 0.04 * sy, 0.018))
                cil(P.B('aco'), q, 0.008, 0.012, lados=6)
    for sy in (-1, 1):
        caixa_de(am, (-0.39, sy * 0.42 - 0.025, 0.15), (0.39, sy * 0.42 + 0.025, 0.2))
    for sx in (-1, 1):
        caixa_de(am, (sx * 0.42 - 0.025, -0.39, 0.15), (sx * 0.42 + 0.025, 0.39, 0.2))
    for yb in (-0.24, 0.12):
        caixa_de(am, (-0.395, yb - 0.03, 0.16), (0.395, yb + 0.03, 0.2))
    caixa_de(P.B('listras'), (-0.39, -0.4475, 0.15), (0.39, -0.445, 0.2))
    # câmara de sucção mergulhada: crivo e flange
    bc = P.B('ferro', True)
    tubo(bc, PC + Z * 0.0, PC + Z * 0.19, 0.15, 40)
    toro(bc, PC + Z * 0.012, 0.15, 0.012, 40, 8)
    for k in range(18):                                                     # rasgos do crivo (escuros)
        a = k * 2 * PI / 18
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(P.B('preto'), PC + d * 0.149 + Z * 0.06, (0.004, 0.018, 0.07), Matrix.Rotation(a, 3, 'Z'))
    cil(P.B('ferro', True), PC + Z * 0.21, 0.2, 0.02, lados=40)
    for k in range(10):
        a = k * 2 * PI / 10 + 0.3
        q = PC + Vector((math.cos(a), math.sin(a), 0)) * 0.18
        tubo(P.B('aco'), q + Z * 0.19, q + Z * 0.24, 0.008, 6)
        cil(P.B('aco'), q + Z * 0.228, 0.014, 0.012, lados=6)
    # cilindro (lado do fluido), cintas, flange de topo e gaxeta
    tubo(P.B('amarelo', True), PC + Z * 0.22, PC + Z * 0.48, 0.13, 40)
    for zz in (0.27, 0.43):
        cil(P.B('ferro', True), PC + Z * zz, 0.137, 0.022, lados=40)
    cil(P.B('ferro', True), PC + Z * 0.49, 0.17, 0.02, lados=40)
    for k in range(8):
        a = k * 2 * PI / 8 + 0.2
        q = PC + Vector((math.cos(a), math.sin(a), 0)) * 0.152
        tubo(P.B('aco'), q + Z * 0.47, q + Z * 0.52, 0.007, 6)
        cil(P.B('aco'), q + Z * 0.507, 0.012, 0.01, lados=6)
    tubo(P.B('ferro', True), PC + Z * 0.5, PC + Z * 0.555, 0.065, 32)      # caixa de gaxeta
    cil(P.B('aco', True), PC + Z * 0.56, 0.075, 0.012, lados=32)
    for k in range(2):
        a = k * PI
        q = PC + Vector((math.cos(a), math.sin(a), 0)) * 0.062 + Vector((0.0, 0, 0))
        tubo(P.B('aco'), q + Z * 0.52, q + Z * 0.58, 0.006, 6)
    remendo(P, PC + Z * 0.35, Z, 0.13, 0.25, 1.0, 0.07, 'cinza')
    serie(P, PC + Z * 0.35, Z, 0.13, 1.75, 3, 0.022)
    # descarga norte: bocal, válvula de retenção, câmara de ar (amortece os golpes), cano até a borda
    tubo(P.B('amarelo', True), PC + Vector((0, 0.1, CZ)), PC + Vector((0, 0.17, CZ)), 0.085, 32)
    flange_l = lambda y, u: flange(P, Vector((0, y, CZ)), (0, u, 0))
    tubo(P.B('ferro', True), Vector((0, 0.13, CZ)), Vector((0, 0.27, CZ)), 0.112, 36)   # corpo da retenção
    cil(P.B('ferro', True), Vector((0, 0.2, CZ)), 0.14, 0.06, (0, 1, 0), lados=36)
    tubo(P.B('ferro', True), Vector((0, 0.2, CZ)), Vector((0, 0.2, 0.47)), 0.06, 24)
    tubo(P.B('amarelo', True), Vector((0, 0.2, 0.47)), Vector((0, 0.2, 0.62)), 0.075, 32)
    bmesh.ops.create_uvsphere(P.B('amarelo', True), u_segments=32, v_segments=16, radius=0.075,
                              matrix=Matrix.Translation(Vector((0, 0.2, 0.62))))
    cil(P.B('ferro', True), Vector((0, 0.2, 0.475)), 0.09, 0.02, lados=32)
    toro(P.B('ferro', True), Vector((0, 0.2, 0.56)), 0.075, 0.008, 40, 8)
    tubo(P.B('cano', True), Vector((0, 0.26, CZ)), Vector((0, 0.47, CZ)), R, 32)
    flange_l(0.5, 1)
    manometro(P, Vector((-0.12, 0.2, 0.58)), (-1, 0, 0), Vector((-0.07, 0.2, 0.56)))
    # colunas laterais, travessas, mancais e guias da cruzeta
    gr = P.B('grafite')
    for sx in (-1, 1):
        for yb in (-0.24, 0.12):
            caixa_de(gr, (sx * 0.18 - 0.02, yb - 0.02, 0.2), (sx * 0.18 + 0.02, yb + 0.02, 0.99))
        caixa_de(gr, (sx * 0.18 - 0.02, -0.26, 0.85), (sx * 0.18 + 0.02, 0.14, 0.89))
        caixa_de(gr, (sx * 0.18 - 0.02, -0.26, 0.99), (sx * 0.18 + 0.02, 0.14, 1.02))
        caixa_de(gr, (sx * 0.1 if sx > 0 else -0.16, -0.075, 0.852), (sx * 0.16 if sx > 0 else -0.1, -0.045, 0.875))
        caixa_de(P.B('ferro'), (sx * 0.18 - 0.03, PC.y - 0.06, 0.89), (sx * 0.18 + 0.03, PC.y + 0.06, 0.95))   # mancal
        cil(P.B('ferro', True), Vector((sx * 0.18, PC.y, ZK)), 0.05, 0.06, (1, 0, 0), lados=24)
        tubo(P.B('cromo', True), Vector((sx * 0.12, PC.y, 0.5)), Vector((sx * 0.12, PC.y, 0.865)), 0.02, 20)
        for zz in (0.51, 0.855):
            cil(P.B('ferro', True), Vector((sx * 0.12, PC.y, zz)), 0.032, 0.02, lados=20)
        viga(gr, Vector((sx * 0.18, -0.24, 0.3)), Vector((sx * 0.18, 0.12, 0.7)), 0.025)
    # motor com aletas, pinhão e cabo
    MZ = ZK - 0.225
    MX0, MX1 = 0.28, 0.46
    mot = Vector(((MX0 + MX1) / 2, PC.y, MZ))
    tubo(P.B('grafite', True), Vector((MX0, PC.y, MZ)), Vector((MX1, PC.y, MZ)), 0.092, 32)
    for k in range(9):
        cil(P.B('grafite', True), Vector((0.315 + k * 0.014, PC.y, MZ)), 0.11, 0.005, (1, 0, 0), lados=32)
    cil(P.B('ferro', True), Vector((MX1 + 0.012, PC.y, MZ)), 0.088, 0.024, (1, 0, 0), lados=32)      # tampa do ventilador
    for k in range(6):
        caixa(P.B('preto'), Vector((MX1 + 0.025, PC.y, MZ - 0.05 + k * 0.02)), (0.002, 0.11, 0.006))
    caixa(P.B('grafite'), Vector((0.37, PC.y + 0.0, MZ + 0.135)), (0.08, 0.07, 0.05))             # caixa de ligação
    caixa(P.B('ambar'), Vector((0.37, PC.y - 0.036, MZ + 0.135)), (0.04, 0.002, 0.008))
    for xx in (MX0 + 0.012, MX1 - 0.012):
        caixa_de(P.B('grafite'), (xx - 0.015, PC.y - 0.08, MZ - 0.12), (xx + 0.015, PC.y + 0.08, MZ - 0.075))
    caixa_de(am, (0.27, -0.27, MZ - 0.135), (0.47, 0.15, MZ - 0.12))
    for yb in (-0.24, 0.12):
        caixa_de(am, (0.3, yb - 0.025, 0.2), (0.44, yb + 0.025, MZ - 0.135))
    tubo(P.B('aco', True), Vector((0.22, PC.y, MZ)), Vector((MX0, PC.y, MZ)), 0.02, 16)              # eixo do motor
    mangueira(P.B('borracha'), bezier(Vector((0.39, PC.y + 0.0, MZ + 0.15)), Vector((0.45, 0.05, MZ + 0.2)),
                                      Vector((0.47, 0.2, 0.4)), Vector((0.45, 0.3, 0.2)), 10), 0.011)
    caixa(P.B('grafite'), Vector((0.42, 0.3, 0.175)), (0.07, 0.09, 0.05))                          # caixa de junção
    mangueira(P.B('borracha'), bezier(Vector((0.42, 0.34, 0.16)), Vector((0.42, 0.42, 0.12)),
                                      Vector((0.44, 0.46, 0.03)), Vector((0.47, 0.5, 0.012)), 8), 0.011)
    for t in (0.35, 0.7):                                                   # abraçadeiras do cabo
        p = bezier(Vector((0.39, PC.y + 0.0, MZ + 0.15)), Vector((0.45, 0.05, MZ + 0.2)),
                   Vector((0.47, 0.2, 0.4)), Vector((0.45, 0.3, 0.2)), 10)[int(t * 10)]
        toro(P.B('aco', True), p, 0.014, 0.003, 16, 6, eixo=Vector((0, 1, -0.5)))
    fios(P, Vector((0.36, PC.y - 0.04, MZ + 0.12)), Vector((0.33, PC.y - 0.135, MZ + 0.06)))
    caixa(P.B('grafite'), Vector((0.37, PC.y - 0.075, MZ + 0.09)), (0.07, 0.004, 0.045),
          Matrix.Rotation(0.9, 3, 'X'))                                     # tampa da caixa de ligação, solta
    serie(P, Vector((0.37, PC.y, MZ)), (1, 0, 0), 0.092, math.radians(250), 3, 0.02, 0.5)
    # sujeira: óleo sob o motor e escorrido de seiva na gaxeta
    for c_, r_ in (((0.37, -0.18), 0.09), ((0.36, 0.25), 0.06), ((-0.3, 0.3), 0.07)):
        bm = bmesh.new()
        mancha(bm, c_, r_, 0.0035)
        obj('oleo', bm, 'oleo')
        halo(c_, r_, 0.0035)
    for k in range(5):
        a = random.uniform(-PI, 0)
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(P.B('crosta'), PC + d * 0.1315 + Z * random.uniform(0.3, 0.42), (0.003, 0.012, random.uniform(0.06, 0.14)),
              Matrix.Rotation(a, 3, 'Z'))
    pingo(P, Vector((0, 0.5 - EF - 0.0, CZ - RF)), 'gota', 1)
    P.fim()

    # ---- partes móveis: virabrequim (volante, coroa, manivela), pinhão, biela e cabecote (cruzeta + haste)
    vira = bpy.data.objects.new('virabrequim', None)
    sc.collection.objects.link(vira)
    vira.location = Vector((0, PC.y, ZK))
    bm = bmesh.new()
    tubo(bm, Vector((-0.28, 0, 0)), Vector((0.27, 0, 0)), 0.026, 20)
    for sx in (-1, 1):                                                      # braços da manivela com contrapeso
        cil(bm, Vector((sx * 0.045, 0, 0)), 0.055, 0.02, (1, 0, 0), lados=24)
        caixa(bm, Vector((sx * 0.045, 0, -0.03)), (0.02, 0.07, 0.07))
        chapa_arco(bm, Vector((sx * 0.045, 0, 0)), Vector((1, 0, 0)), 0.03, 0.06, 0.02, math.radians(40), math.radians(140), 10)
    tubo(bm, Vector((-0.055, 0, -RC)), Vector((0.055, 0, -RC)), 0.022, 16)  # moente
    o = suavizar(obj('manivela', bm, 'aco', vira))
    bm = bmesh.new()                                                        # volante de inércia maciço (oeste)
    tubo(bm, Vector((-0.27, 0, 0)), Vector((-0.23, 0, 0)), 0.165, 48)       # aro
    cil(bm, Vector((-0.25, 0, 0)), 0.05, 0.06, (1, 0, 0), lados=24)         # cubo
    chapa_arco(bm, Vector((-0.28, 0, 0)), Vector((1, 0, 0)), 0.06, 0.09, 0.02, math.radians(50), math.radians(130), 12)
    suavizar(obj('volante', bm, 'ferro', vira))
    bm = bmesh.new()
    caixa(bm, Vector((-0.2715, 0, -0.1)), (0.004, 0.025, 0.12))             # marca de ponto (mostra o giro)
    obj('volante_marca', bm, 'ambar', vira)
    bm = bmesh.new()                                                        # coroa (leste)
    cil(bm, Vector((0.25, 0, 0)), 0.158, 0.03, (1, 0, 0), lados=48)
    dentes(bm, Vector((0.25, 0, 0)), (1, 0, 0), 0.155, 36, 0.026, 0.014, 0.03, fase=-PI / 2 + PI / 36)
    cil(bm, Vector((0.25, 0, 0)), 0.05, 0.06, (1, 0, 0), lados=24)
    obj('coroa', bm, 'ferro', vira)
    pin = bpy.data.objects.new('pinhao', None)
    sc.collection.objects.link(pin)
    pin.location = Vector((0.25, PC.y, MZ))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.044, 0.03, (1, 0, 0), lados=24)
    dentes(bm, Vector((0, 0, 0)), (1, 0, 0), 0.042, 12, 0.026, 0.014, 0.03, fase=PI / 2)
    obj('pinhao_dentes', bm, 'aco', pin)
    biela = bpy.data.objects.new('biela', None)
    sc.collection.objects.link(biela)
    biela.rotation_mode = 'XYZ'
    bm = bmesh.new()
    for zz, rr in ((0, 0.03), (LB, 0.036)):
        cil(bm, Vector((0, 0, zz)), rr, 0.045, (1, 0, 0), lados=24)
    caixa(bm, Vector((0, 0, LB / 2)), (0.03, 0.035, LB - 0.05))
    obj('biela_corpo', bm, 'amarelo', biela)
    cab = bpy.data.objects.new('cabecote', None)                            # parte do catálogo: sobe e desce
    sc.collection.objects.link(cab)
    bm = bmesh.new()
    for sx in (-1, 1):
        caixa_de(bm, (sx * 0.03 if sx > 0 else -0.15, -0.045, -0.035), (sx * 0.15 if sx > 0 else -0.03, 0.045, 0.035))
        cil(bm, Vector((sx * 0.12, 0, 0)), 0.036, 0.09, lados=24)           # buchas nas guias
    caixa_de(bm, (-0.15, -0.045, -0.045), (0.15, 0.045, -0.035))
    tubo(bm, Vector((-0.04, 0, 0)), Vector((0.04, 0, 0)), 0.014, 12)        # pino da cruzeta
    obj('cruzeta', bm, 'ferro', cab)
    bm = bmesh.new()
    tubo(bm, Vector((0, 0, -0.045)), Vector((0, 0, -0.33)), 0.032, 24)      # haste do êmbolo
    suavizar(obj('haste', bm, 'cromo', cab))
    bm = bmesh.new()
    caixa_de(bm, (-0.11, -0.0465, -0.012), (0.11, -0.044, 0.012))           # faixa de luz da cruzeta
    obj('cabecote_luz', bm, 'ambar', cab)
    return P, vira, pin, biela, cab


# ------------------------------------------------------------------ tanque 2×2
RT = 0.74


def tanque(cx, cy, ligadas=()):
    P = Peca('tanque', cx, cy, 0)
    caixa_de(P.B('concreto'), (-0.98, -0.98, 0), (0.98, 0.98, 0.08))
    for a, b in (((-0.985, -0.985), (0.985, -0.965)), ((-0.985, 0.965), (0.985, 0.985)),
                 ((-0.985, -0.965), (-0.965, 0.965)), ((0.965, -0.965), (0.985, 0.965))):
        caixa_de(P.B('listras'), (a[0], a[1], 0.0), (b[0], b[1], 0.082))
    # saia ancorada
    tubo(P.B('ferro', True), Vector((0, 0, 0.08)), Vector((0, 0, 0.16)), RT + 0.02, 64)
    for k in range(8):
        a = k * PI / 4 + PI / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        rot = Matrix.Rotation(a, 3, 'Z')
        caixa(P.B('ferro'), d * (RT + 0.06) + Z * 0.088, (0.1, 0.12, 0.016), rot)
        for sy in (-1, 1):
            caixa(P.B('ferro'), d * (RT + 0.05) + rot @ Vector((0, sy * 0.045, 0.14)), (0.08, 0.012, 0.11), rot)
        tubo(P.B('aco'), d * (RT + 0.075) + Z * 0.08, d * (RT + 0.075) + Z * 0.13, 0.009, 6)
        cil(P.B('aco'), d * (RT + 0.075) + Z * 0.104, 0.017, 0.014, lados=6)
    # casco, cintas com rebites, costuras verticais
    bmt = P.B('tanque', True)
    n0 = len(bmt.verts)
    varrer(bmt, [Vector((0, 0, 0.14 + 1.22 * i / 30)) for i in range(31)], RT, 96)
    for ang_d, zd, rd, pf in ((-40, 1.12, 0.11, 0.022), (75, 0.45, 0.09, 0.018), (160, 0.8, 0.12, 0.02)):
        a = math.radians(ang_d)
        amassar(bmt, n0, Vector((math.cos(a) * RT, math.sin(a) * RT, zd)), rd, pf, lambda v: Vector((0, 0, v.z)))
    remendo(P, Vector((0, 0, 0.4)), Z, RT, 0.55, 0.8, 0.2)
    serie(P, Vector((0, 0, 0.79)), Z, RT, 0.95, 4, 0.05)
    serie(P, Vector((0, 0, 1.12)), Z, RT, 2.6, 5, 0.04, 0.5)
    aJ = math.radians(-20)
    dJ = Vector((math.cos(aJ), math.sin(aJ), 0))
    rJ = Matrix.Rotation(aJ, 3, 'Z')
    caixa(P.B('grafite'), dJ * (RT + 0.045) + Z * 0.4, (0.08, 0.1, 0.13), rJ)     # caixa de junção, tampa aberta
    caixa(P.B('grafite'), dJ * (RT + 0.105) + rJ @ Vector((0, -0.06, 0.4)), (0.004, 0.1, 0.13),
          rJ @ Matrix.Rotation(-1.1, 3, 'Z'))
    caixa(P.B('preto'), dJ * (RT + 0.0855) + Z * 0.4, (0.002, 0.08, 0.11), rJ)
    fios(P, dJ * (RT + 0.09) + Z * 0.37, dJ * (RT + 0.16) + Z * 0.22, 3, 0.05)
    mangueira(P.B('borracha'), bezier(dJ * (RT + 0.045) + Z * 0.335, dJ * (RT + 0.06) + Z * 0.25,
                                      dJ * (RT + 0.1) + Z * 0.12, dJ * (RT + 0.17) + Z * 0.088, 8), 0.012)
    br = P.B('aco')
    for zz in (0.62, 0.96, 1.28):
        cil(P.B('ferro', True), Vector((0, 0, zz)), RT + 0.012, 0.045, lados=72)
        for k in range(48):
            a = k * 2 * PI / 48
            d = Vector((math.cos(a), math.sin(a), 0))
            for dz in (-0.013, 0.013):
                cil(br, d * (RT + 0.012) + Z * (zz + dz), 0.0055, 0.008, d, lados=6)
    for a0 in (20, 110, 200):
        a = math.radians(a0)
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(P.B('tanque'), d * (RT + 0.003) + Z * 0.75, (0.008, 0.05, 1.2), Matrix.Rotation(a, 3, 'Z'))
        t = Vector((-math.sin(a), math.cos(a), 0))
        for k in range(26):
            zz = 0.2 + k * 0.045
            if any(abs(zz - c) < 0.04 for c in (0.62, 0.96, 1.28)):
                continue
            for sl in (-0.015, 0.015):
                cil(br, d * (RT + 0.007) + t * sl + Z * zz, 0.0055, 0.008, d, lados=6)
    # faixa de perigo em volta, embaixo
    tubo(P.B('listras', True), Vector((0, 0, 0.17)), Vector((0, 0, 0.24)), RT + 0.004, 72)
    # teto cônico, borda, plataforma e tampa de inspeção para drone
    cil(P.B('tanque', True), Vector((0, 0, 1.47)), RT, 0.22, lados=72, r2=0.3)
    toro(P.B('ferro', True), Vector((0, 0, 1.36)), RT + 0.004, 0.014, 72, 8)
    cil(P.B('ferro', True), Vector((0, 0, 1.59)), 0.3, 0.02, lados=48)
    tubo(P.B('ferro', True), Vector((0, 0, 1.6)), Vector((0, 0, 1.64)), 0.19, 40)
    cil(P.B('amarelo', True), Vector((0, 0, 1.655)), 0.225, 0.03, lados=48)
    for k in range(12):
        a = k * 2 * PI / 12
        q = Vector((math.cos(a), math.sin(a), 0)) * 0.205
        tubo(P.B('aco'), q + Z * 1.62, q + Z * 1.682, 0.0075, 6)
        cil(P.B('aco'), q + Z * 1.675, 0.014, 0.012, lados=6)
    caixa(P.B('ferro'), Vector((0.0, 0.0, 1.677)), (0.06, 0.016, 0.016))     # olhal de garra do drone
    cil(P.B('ferro', True), Vector((0, 0, 1.684)), 0.012, 0.03, (1, 0, 0), lados=12)
    caixa(P.B('ferro'), Vector((-0.235, 0, 1.655)), (0.04, 0.09, 0.03))       # dobradiça
    cil(P.B('aco', True), Vector((-0.245, 0, 1.655)), 0.012, 0.11, (0, 1, 0), lados=12)
    for k in range(3):                                                      # balizas de pouso
        a = PI / 2 + k * 2 * PI / 3
        q = Vector((math.cos(a), math.sin(a), 0)) * 0.27
        cil(P.B('ferro', True), q + Z * 1.605, 0.018, 0.012, lados=12)
        bmesh.ops.create_uvsphere(P.B('ambar', True), u_segments=12, v_segments=6, radius=0.012,
                                  matrix=Matrix.Translation(q + Z * 1.615))
    toro(P.B('listras', True), Vector((0, 0, 1.6)), 0.255, 0.004, 48, 6)
    # válvula de alívio no teto (corpo fixo; o chapéu sobe no alívio)
    aR = math.radians(240)
    dR = Vector((math.cos(aR), math.sin(aR), 0))
    VR = dR * 0.5 + Z * 1.48
    tubo(P.B('ferro', True), VR - Z * 0.03, VR + Z * 0.05, 0.03, 20)
    cil(P.B('ferro', True), VR + Z * 0.005, 0.05, 0.016, lados=20)
    cil(P.B('amarelo', True), VR + Z * 0.075, 0.045, 0.05, lados=20)
    tubo(P.B('ferro', True), VR + Z * 0.07, VR + Z * 0.07 + dR * 0.1, 0.022, 16)
    bmesh.ops.create_uvsphere(P.B('ferro', True), u_segments=16, v_segments=8, radius=0.022,
                              matrix=Matrix.Translation(VR + Z * 0.07 + dR * 0.1))
    tubo(P.B('ferro', True), VR + Z * 0.07 + dR * 0.1, VR + Z * 0.13 + dR * 0.1, 0.022, 16)
    for k in range(4):
        toro(P.B('aco', True), VR + Z * (0.108 + k * 0.014), 0.026, 0.004, 20, 6)
    # visor de nível (sudeste): tomadas, tubo de vidro, régua e guarda
    aG = math.radians(300)
    dG = Vector((math.cos(aG), math.sin(aG), 0))
    tG = Vector((-math.sin(aG), math.cos(aG), 0))
    G0, G1 = 0.3, 1.18
    RG = RT + 0.11
    for zz in (G0 - 0.04, G1 + 0.04):
        tubo(P.B('cano', True), dG * (RT - 0.01) + Z * zz, dG * RG + Z * zz, 0.018, 14)
        cil(P.B('ferro', True), dG * (RT + 0.005) + Z * zz, 0.035, 0.012, dG, lados=16)
        bmesh.ops.create_uvsphere(P.B('ferro', True), u_segments=16, v_segments=8, radius=0.032,
                                  matrix=Matrix.Translation(dG * RG + Z * zz))
        cil(P.B('grafite'), dG * (RT + 0.06) + Z * zz + tG * 0.03, 0.02, 0.03, tG, lados=12)
    tubo(P.B('vidro', True), dG * RG + Z * (G0 - 0.012), dG * RG + Z * (G1 + 0.012), 0.036, 24)
    for sl in (-1, 1):
        tubo(P.B('aco', True), dG * RG + tG * sl * 0.052 + Z * (G0 - 0.03), dG * RG + tG * sl * 0.052 + Z * (G1 + 0.03), 0.006, 8)
    caixa(P.B('grafite'), dG * (RT + 0.045) + Z * ((G0 + G1) / 2), (0.006, 0.07, G1 - G0), Matrix.Rotation(aG, 3, 'Z'))
    for k in range(11):
        larg = 0.045 if k % 5 == 0 else 0.025
        caixa(P.B('mostrador'), dG * (RT + 0.049) + tG * 0.0 + Z * (G0 + (G1 - G0) * k / 10),
              (0.002, larg, 0.006), Matrix.Rotation(aG, 3, 'Z'))
    # bocais nos 4 lados (tile da esquerda): reforço no casco, cano, válvula atuada e flange na borda
    portas = dict(S=(Vector((-0.5, -1, 0)), Vector((0, -1, 0))), N=(Vector((0.5, 1, 0)), Vector((0, 1, 0))),
                  L=(Vector((1, 0.5, 0)), Vector((1, 0, 0))), O=(Vector((-1, -0.5, 0)), Vector((-1, 0, 0))))
    for l, (pb, u) in portas.items():
        borda = pb + Z * CZ
        lat = Vector((u.y, -u.x, 0))
        off = lat.dot(pb)
        dentro = lat * off + u * (math.sqrt(RT ** 2 - off ** 2) - 0.05) + Z * CZ
        tubo(P.B('cano', True), dentro, borda - u * 0.03, R, 32)
        nas = lat * off + u * math.sqrt(RT ** 2 - off ** 2) + Z * CZ
        cil(P.B('tanque', True), nas + u * 0.004, 0.15, 0.014, u, lados=36)  # chapa de reforço
        flange(P, borda, u)
        meio = (nas + borda) / 2
        if l in 'SO':                                                       # válvula de bloqueio atuada (sem volante)
            bmesh.ops.create_uvsphere(P.B('oxido' if l == 'S' else 'ferro', True), u_segments=28, v_segments=14,
                                      radius=0.13, matrix=Matrix.Translation(meio))
            tubo(P.B('ferro', True), meio, meio + Z * 0.19, 0.03, 16)
            caixa(P.B('grafite'), meio + Z * 0.24, (0.12, 0.12, 0.08), rot_de(u))
            caixa(P.B('ambar'), meio + Z * 0.24 - lat * 0.061, (0.002, 0.05, 0.012), rot_de(u))
            pingo(P, meio - Z * 0.13 + u * 0.03, 'gota', 1)
    # sujeira: escorridos de seiva no casco (alívio, visor) e poças
    for k in range(7):
        a = aR + random.uniform(-0.25, 0.25)
        d = Vector((math.cos(a), math.sin(a), 0))
        h = random.uniform(0.25, 0.7)
        caixa(P.B('crosta'), d * (RT + 0.002) + Z * (1.36 - h / 2), (0.003, random.uniform(0.012, 0.03), h),
              Matrix.Rotation(a, 3, 'Z'))
    for k in range(5):
        a = aG + random.uniform(-0.12, 0.12)
        d = Vector((math.cos(a), math.sin(a), 0))
        h = random.uniform(0.15, 0.4)
        caixa(P.B('oleo'), d * (RT + 0.002) + Z * (0.62 - h / 2), (0.003, random.uniform(0.01, 0.025), h),
              Matrix.Rotation(a, 3, 'Z'))
    for c_, r_, m_ in (((-0.8, 0.6), 0.1, 'oleo'), ((0.75, -0.75), 0.08, 'derramada'), ((0.55, -0.6), 0.07, 'oleo')):
        bm = bmesh.new()
        mancha(bm, P.W(Vector((c_[0], c_[1], 0))).to_tuple()[:2], r_, 0.083)
        obj('poca_tanque', bm, m_)
        halo(P.W(Vector((c_[0], c_[1], 0))).to_tuple()[:2], r_, 0.083)
    P.fim()
    # nível: seiva no visor (sobe e desce), chapéu da válvula de alívio
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.5)), 0.028, 1.0, lados=20)
    niv = suavizar(obj('nivel_seiva', bm, 'nivel'))
    niv.location = P.W(dG * RG + Z * G0)
    cap = bpy.data.objects.new('alivio_chapeu', None)
    sc.collection.objects.link(cap)
    cap.location = P.W(VR + Z * 0.165)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.03, 0.02, lados=20)
    cil(bm, Vector((0, 0, 0.015)), 0.012, 0.02, lados=12)
    obj('alivio_tampa', bm, 'amarelo', cap)
    saida_vapor = P.W(VR + Z * 0.135 + dR * 0.1)
    return P, niv, (G1 - G0), cap, saida_vapor


# ------------------------------------------------------------------ montagem do conjunto
PB, vira, pinhao, biela, cabecote = bomba(0, 0)
cano_reto('reto_visor', 0, 1, 0, 'visor', sentido=1)
cano_t('t', 0, 2, 0)
cano_curva('curva_a', 0, 3, 0)
cano_reto('reto_isolado', 1, 3, 1, 'isolado')
cano_reto('reto_fole', 1, 2, 1, 'dilatacao')
cano_curva('curva_b', 2, 2, 2)
cano_cruz('cruz', 2, 3, 0)
cano_reto('reto_visor2', 3, 3, 1, 'visor', sentido=-1)
cano_reto('tampao', 2, 4, 0, 'tampao')
TC = Vector((4.5, 3.5, 0))
PT, nivel, ALT_NIVEL, chapeu, SAIDA_VAPOR = tanque(TC.x, TC.y, ligadas=('O',))

# sujeira solta no chão: óleo e seiva entre as peças
for c_, r_, m_ in (((0.6, 1.3), 0.12, 'oleo'), ((1.4, 2.6), 0.09, 'derramada'), ((2.6, 2.4), 0.1, 'oleo'),
                   ((0.55, 3.55), 0.08, 'oleo'), ((3.0, 2.6), 0.07, 'derramada'), ((-0.5, 2.4), 0.1, 'oleo')):
    bm = bmesh.new()
    mancha(bm, c_, r_, 0.0028)
    obj('mancha', bm, m_)
    halo(c_, r_, 0.0028)

# gotas: objetos (esfera esticada) e respingos da sucção
gotas = []
for p, mat, vezes, fase in GOTAS:
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.011)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.z *= 1.7
    o = suavizar(obj('gota', bm, mat))
    gotas.append((o, p, vezes, fase))
respingos = []
for k in range(14):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.006, 0.011))
    o = suavizar(obj('respingo', bm, 'gota'))
    a = random.uniform(0, 2 * PI)
    respingos.append((o, a, random.uniform(0.25, 0.6), random.uniform(0.5, 0.9), k % NGOLPES))
espumas = []
for k in range(70):
    a = random.uniform(0, 2 * PI)
    rr = random.uniform(0.152, 0.25)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=random.uniform(0.008, 0.02))
    o = suavizar(obj('espuma', bm, 'espuma'))
    o.location = PC + Vector((math.cos(a) * rr, math.sin(a) * rr, 0.004))
    o.scale = (1, 1, 0.55)
    espumas.append((o, random.random()))
vapores = []
for k in range(7):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    return x * x * (3 - 2 * x)


def manivela(fr):
    th = 2 * PI * NGOLPES * fr
    pino = Vector((0, PC.y + RC * math.sin(th), ZK - RC * math.cos(th)))
    zx = pino.z - math.sqrt(LB ** 2 - (pino.y - PC.y) ** 2)
    return th, pino, zx


DUR = QUADROS / FPS
chapeu_base = chapeu.location.copy()
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    th, pino, zx = manivela(fr)
    vira.rotation_euler = (th, 0, 0)
    pinhao.rotation_euler = (-th * 3, 0, 0)
    xh = Vector((0, PC.y, zx))
    d = pino - xh
    biela.location = xh
    biela.rotation_euler = (math.atan2(-d.y, d.z), 0, 0)
    cabecote.location = xh
    for o, c in ((vira, 'rotation_euler'), (pinhao, 'rotation_euler'), (biela, 'location'), (biela, 'rotation_euler'),
                 (cabecote, 'location')):
        o.keyframe_insert(c, frame=q)
    # sucção: êmbolo subindo (cos(th) > 0 → manivela descendo... usa a velocidade da cruzeta)
    golpe = (NGOLPES * fr) % 1.0
    sucao = math.sin(PI * golpe) ** 2
    # fluxo nos visores: avança FLUXO_K faixas por laço e pulsa a cada golpe
    fase = FLUXO_K * fr - 0.35 * math.sin(2 * PI * NGOLPES * fr) / (2 * PI) * 2
    for val in FASES:
        val.outputs[0].default_value = fase
        val.outputs[0].keyframe_insert('default_value', frame=q)
    # ponteiros dos manômetros batendo com os golpes
    for e, n, f0 in GAUGES:
        e.rotation_quaternion = n.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), f0 - 0.35 * math.sin(2 * PI * NGOLPES * fr))
        e.keyframe_insert('rotation_quaternion', frame=q)
    # espuma pulsando
    for o, f0 in espumas:
        s = 0.75 + 0.35 * math.sin(2 * PI * (NGOLPES * fr + f0)) ** 2
        o.scale = (s, s, 0.55 * s)
        o.keyframe_insert('scale', frame=q)
    # respingos: saltam da borda da câmara no começo de cada golpe
    for o, a, v, alt, k in respingos:
        u = (NGOLPES * fr - k * 0.13) % 1.0
        tt = u * 0.5
        voo = tt < 0.32
        p0 = PC + Vector((math.cos(a), math.sin(a), 0)) * 0.16 + Z * 0.01
        pos = p0 + Vector((math.cos(a), math.sin(a), 0)) * v * tt * 0.5 + Z * (alt * 1.6 * tt - 4.9 * tt * tt)
        o.location = pos if voo and pos.z > 0.004 else p0 - Z * 0.05
        o.keyframe_insert('location', frame=q)
    # gotas: incha pendurada, cai e some
    for o, p, vezes, f0 in gotas:
        u = (vezes * fr + f0) % 1.0
        h = p.z - 0.004
        tq = math.sqrt(2 * h / 9.8) / (DUR / vezes)
        if u < 0.7:
            s = 0.25 + 0.75 * suave(u / 0.7)
            o.location = p - Z * 0.011 * s
            o.scale = (s, s, s)
        elif u < 0.7 + tq:
            t = (u - 0.7) * DUR / vezes
            o.location = p - Z * (0.011 + 4.9 * t * t)
            o.scale = (0.85, 0.85, 1.25)
        else:
            o.location = p - Z * 0.011
            o.scale = (0.05, 0.05, 0.05)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    # nível do tanque: sobe e desce uma vez por laço
    nv = 0.55 + 0.3 * math.sin(2 * PI * (fr - 0.41))
    nivel.scale = (1, 1, ALT_NIVEL * nv)
    nivel.keyframe_insert('scale', frame=q)
    # válvula de alívio: estoura entre 55% e 85% do laço
    ab = 0.0
    if 0.55 <= fr < 0.85:
        x = (fr - 0.55) / 0.3
        ab = min(1.0, x / 0.1) * min(1.0, (1 - x) / 0.25)
    chapeu.location = chapeu_base + Z * 0.025 * ab
    chapeu.keyframe_insert('location', frame=q)
    for k, o in enumerate(vapores):
        u = (k / len(vapores) + fr * 3) % 1.0
        ativo = ab > 0.05 and u < 0.9
        o.location = SAIDA_VAPOR + Vector((0.12 * u, 0.06 * u, 0.9 * u + 0.03))
        o.scale = [max(0.03, (0.04 + 0.22 * u) * (0.4 + 0.6 * ab))] * 3
        o.rotation_euler = (k, u * 2, k * 0.5)
        o.hide_render = not ativo
        o.hide_viewport = o.hide_render
        for c in ('location', 'scale', 'rotation_euler', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)

for o in list(sc.objects) + list(bpy.data.materials):
    ad = getattr(o, 'animation_data', None)
    if o in list(bpy.data.materials):
        ad = o.node_tree.animation_data if o.node_tree else None
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (2.5, 2.0, -0.5), (16, 16, 1.0))
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
    'conjunto': ('canos_conjunto.png', (6.0, -2.6, 3.4), (2.2, 1.9, 0.35), 33, 1600, 1000),
    'canos': ('canos_perto.png', (-1.25, 4.7, 1.45), (1.15, 2.35, 0.2), 30, 1400, 1000),
    'bomba': ('bomba_perto.png', (1.45, -1.5, 1.0), (0.0, -0.04, 0.45), 32, 1200, 1300),
    'tanque': ('tanque_0.png', (TC.x + 1.5, TC.y - 3.1, 2.0), (TC.x, TC.y, 0.8), 34, 1200, 1300),
}
if modo in ('foto', 'teste'):
    sc.cycles.samples = 128 if modo == 'foto' else 24
    sc.frame_set(int(QUADROS * 0.66) + 1)                                   # alívio aberto, gotas caindo
    for chave, (nome, pos, alvo, lente, rx, ry) in FOTOS.items():
        if so_uma and chave != so_uma:
            continue
        if modo == 'teste':
            rx, ry = rx // 2, ry // 2
        foto(nome, pos, alvo, lente, rx, ry)
print('CANOS ok')
