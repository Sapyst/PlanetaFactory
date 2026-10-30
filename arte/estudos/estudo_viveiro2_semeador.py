"""Estudos isolados (fora do jogo) da linha de proliferação verde, evolução do viveiro aprovado (estudo_viveiro.py).

VIVEIRO 2 (`viveiro_2`, 2×2): raio 12, planta a espécie do bioma e é 2× mais rápido. Seiva entra pelo cano na boca O0
(como o viveiro 1). Partes: antena, pistao0, pistao1, canhao.
- Pavilhão octogonal mais alto (mesma família do aprovado), agora com DOIS NÍVEIS de bandejas no carrossel: embaixo os
  canteiros-matriz da espécie do bioma (forração, mudinhas e espigas de semente que brilham); em cima as cápsulas de
  longo alcance (dardo de aço com ogiva de vidro e a muda dentro). As sementes sobem da matriz pelo campo violeta.
- Ponte rolante (trilho em perfil I, carro, pistão vertical e garra de 3 dedos) leva a cápsula pronta da estação leste
  do nível de cima, sai pela face sudeste aberta e a solta na boca de carga do canhão.
- CANHÃO PNEUMÁTICO DE SEMENTES (canto sudeste): pedestal, coroa de giro dentada, torre, munhões, cano longo com cintas
  e freio de boca ventilado, câmara de ar, culatra com pistão, pistão de elevação, dois cilindros de ar comprimido na
  torre, compressor no leste com mangueiras pela junta rotativa. A cápsula sai em voo (rastro de vapor, sopro na boca).
- Leitor de bioma da IA (faixa sul): pórtico com pistão que crava a sonda na terra por um colar da laje, cabeça com olho
  violeta, tubo com o testemunho de solo em camadas, pulso de leitura no chão.
- Tanque de seiva (SO, boca O0) e tanque de nutriente (NO, visor verde), canos para o armário de dosagem.
- Raízes subindo pelos pilares em espiral, raízes aéreas pendendo do beiral, raízes rachando a laje, musgo nas mesas.

SEMEADOR DE BIOMA (`restauracao_bioma`, 3×3): devolve cinzal e terra queimada ao bioma original. Água/seiva entra pela
boca O1. Partes: injetor0..3, espalhador0, espalhador1, agitador.
- Chassi pesado sobre quatro sapatas, em cima de cinza e terra queimada; reator de solo vivo (vidro com lodo e micélio
  verde que brilha, agitador), dois tanques de solo vivo, silo de esporos com dosador.
- Quatro injetores: pórtico, pistão (camisa na travessa, haste no carro) que crava a lança no solo; mangueira de lodo.
- Dois espalhadores de disco giratório nas pontas de lanças: sementes e nuvem de esporos.
- Anel de aspersores. Toque da IA: emissor violeta embaixo do chassi e a ONDA VERDE de restauração que corre no chão.
- Em volta, metade queimada (cinza, carvão, tocos, brasas, fumacinha) e metade com grama e brotos voltando.
Animação em laço de 4 s (96 quadros a 24 qps) nos dois.
Uso: blender -b --python estudo_viveiro2_semeador.py -- viveiro2|semeador foto [0|perto]
     blender -b --python estudo_viveiro2_semeador.py -- viveiro2|semeador teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['viveiro2', 'foto']
OBRA = ARGS[0]
random.seed(47 if OBRA == 'viveiro2' else 83)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3), a0=0.0, a1=2 * PI):
    fechado = abs(a1 - a0 - 2 * PI) < 1e-6
    n = nR if fechado else nR + 1
    aneis = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B_ = aneis[i], aneis[(i + 1) % n]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B_[(j + 1) % nr], B_[j]))


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.16:
            for c in (a + u * 0.05, b - u * 0.05):
                tubo(bf, c - u * 0.008, c + u * 0.008, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def feixe(bc, ba, pts, lat, n=3, r=0.008, passo=4):
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.008, pts[j] + u * 0.008, r * (n + 0.8), 10)


def raiz(bm, pts, r0, r1, lados=7):
    pts = [Vector(p) for p in pts]
    n = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        r = r0 + (r1 - r0) * i / n
        u = (b - a).normalized()
        tubo(bm, a - u * r * 0.4, b + u * r * 0.4, r, lados)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r * 1.05, matrix=Matrix.Translation(b))


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def rebites(bm, a, b, n, off=Vector((0, 0, 0)), r=0.0055):
    a, b = Vector(a), Vector(b)
    for i in range(n):
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r,
                                   matrix=Matrix.Translation(a.lerp(b, (i + 0.5) / n) + off))


def viga_i(bm, a, b, h, w, up, t=0.007):
    a, b = Vector(a), Vector(b)
    z = (b - a).normalized()
    y = (Vector(up) - z * Vector(up).dot(z)).normalized()
    x = y.cross(z)
    R = Matrix((x, y, z)).transposed()
    L = (b - a).length
    m = (a + b) / 2
    caixa(bm, m, (t, h, L), R)
    for s in (-1, 1):
        caixa(bm, m + y * s * (h / 2 - t / 2), (w, t, L), R)


BMS = {}


def B(nome, mat, liso=False):
    k = (nome, mat, liso)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def base_de(n):
    """Base ortonormal (x, y, n) para um plano de normal n."""
    n = Vector(n).normalized()
    a = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    x = a.cross(n).normalized()
    return x, n.cross(x), n


def remendo(bm, br, centro, normal, w, h, giro=0.0, esp=0.006):
    """Remendo de chapa aparafusado (chapa + parafusos nos cantos e no meio das bordas)."""
    x, y, n = base_de(normal)
    R = Matrix.Rotation(giro, 3, n)
    x, y = R @ x, R @ y
    Mr = Matrix((x, y, n)).transposed()
    c = Vector(centro) + n * esp / 2
    caixa(bm, c, (w, h, esp), Mr)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)):
        p = c + x * sx * (w / 2 - 0.012) + y * sy * (h / 2 - 0.012) + n * esp / 2
        cil(br, p, 0.0055, 0.006, n, 6)


def plaqueta(bm_p, bm_t, centro, normal, w=0.06, h=0.03):
    """Plaqueta de série meio apagada: chapinha escura com tarjas claras raspadas."""
    x, y, n = base_de(normal)
    Mr = Matrix((x, y, n)).transposed()
    c = Vector(centro)
    caixa(bm_p, c + n * 0.0015, (w, h, 0.003), Mr)
    for j, f in enumerate((0.8, 0.55, 0.35)):
        caixa(bm_t, c + n * 0.0032 + y * (h * 0.25 - j * h * 0.25) - x * w * (1 - f) * 0.4, (w * f * 0.8, h * 0.12, 0.0008), Mr)


def escorrido(bm, p, normal, comp, larg=0.008):
    """Escorrido vertical (óleo, ferrugem, fuligem) colado na superfície."""
    x, y, n = base_de(normal)
    for k in range(3):
        caixa(bm, Vector(p) + n * 0.0012 - Vector((0, 0, comp * (0.25 + 0.25 * k))) + x * random.uniform(-0.3, 0.3) * larg,
              (larg * (1 - 0.25 * k), 0.0015, comp * (0.5 - 0.1 * k)), Matrix((x, n, Vector((0, 0, 1)))).transposed())


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def liquido_mat(nome, cor, forca=0.0, transm=0.7):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.4
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def encardir(m, lama=0.0, lama_z=0.15, poeira=0.0, fuligem=0.0, fz=(0.0, 1.0), oleo=0.0):
    """Sujeira de uso médio por cima do material: lama respingada embaixo (mundo z < lama_z), poeira nas faces de
    cima, fuligem que escurece de fz[0] para fz[1] (mais forte embaixo), manchas de óleo escuras e brilhantes."""
    nt = m.node_tree
    no = mats.no
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = next((l for l in nt.links if l.to_socket == bsdf.inputs['Base Color']), None)
    src = lk.from_socket if lk else None
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 11.0, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    cur = src

    def mistura(fator, cor):
        nonlocal cur
        mx = no(nt, 'ShaderNodeMix', data_type='RGBA')
        mx.inputs[7].default_value = (*cor, 1)
        nt.links.new(fator, mx.inputs[0])
        if cur is not None:
            nt.links.new(cur, mx.inputs[6])
        else:
            mx.inputs[6].default_value = bsdf.inputs['Base Color'].default_value
        cur = mx.outputs[2]

    if lama > 0:
        zz = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
        nt.links.new(ru.outputs['Fac'], zz.inputs[0])
        zz.inputs[1].default_value = -lama_z * 0.9
        nt.links.new(sep.outputs['Z'], zz.inputs[2])
        lm = no(nt, 'ShaderNodeMapRange', **{'From Min': lama_z * 0.25, 'From Max': -lama_z * 0.2, 'To Min': 0.0, 'To Max': lama})
        nt.links.new(zz.outputs[0], lm.inputs['Value'])
        mistura(lm.outputs['Result'], (0.075, 0.05, 0.03))
    if fuligem > 0:
        fzm = no(nt, 'ShaderNodeMapRange', **{'From Min': fz[1], 'From Max': fz[0], 'To Min': 0.0, 'To Max': 1.0})
        nt.links.new(sep.outputs['Z'], fzm.inputs['Value'])
        fr2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.35, 'To Max': 1.0})
        nt.links.new(ru.outputs['Fac'], fr2.inputs['Value'])
        mu = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(fzm.outputs['Result'], mu.inputs[0])
        nt.links.new(fr2.outputs['Result'], mu.inputs[1])
        mu2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
        mu2.inputs[1].default_value = fuligem
        nt.links.new(mu.outputs[0], mu2.inputs[0])
        mistura(mu2.outputs[0], (0.014, 0.013, 0.012))
    if poeira > 0:
        pm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.95, 'To Min': 0.0, 'To Max': poeira})
        nt.links.new(sn.outputs['Z'], pm.inputs['Value'])
        pr2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.6})
        nt.links.new(ru.outputs['Fac'], pr2.inputs['Value'])
        mu = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(pm.outputs['Result'], mu.inputs[0])
        nt.links.new(pr2.outputs['Result'], mu.inputs[1])
        mistura(mu.outputs[0], (0.36, 0.32, 0.27))
    if oleo > 0:
        ol = no(nt, 'ShaderNodeTexNoise', **{'Scale': 4.0, 'Detail': 3.0})
        nt.links.new(geo.outputs['Position'], ol.inputs['Vector'])
        om = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.6, 'From Max': 0.66, 'To Min': 0.0, 'To Max': oleo})
        nt.links.new(ol.outputs['Fac'], om.inputs['Value'])
        mistura(om.outputs['Result'], (0.01, 0.008, 0.006))
    if cur is not None:
        nt.links.new(cur, bsdf.inputs['Base Color'])
    return m


def vidro_sujo_mat(nome, sujo=1.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    geo = no(nt, 'ShaderNodeNewGeometry')
    nevoa = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.5, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], nevoa.inputs['Vector'])
    esc = no(nt, 'ShaderNodeMapping')
    esc.inputs['Scale'].default_value = (28.0, 28.0, 2.0)
    nt.links.new(geo.outputs['Position'], esc.inputs['Vector'])
    escn = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 3.0})
    nt.links.new(esc.outputs['Vector'], escn.inputs['Vector'])
    gotas = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 140.0})
    nt.links.new(geo.outputs['Position'], gotas.inputs['Vector'])
    gm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.18, 'From Max': 0.32, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(gotas.outputs['Distance'], gm.inputs['Value'])
    fog = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.7, 'To Min': 0.12, 'To Max': 0.5 * sujo})
    nt.links.new(nevoa.outputs['Fac'], fog.inputs['Value'])
    sj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 0.35 * sujo})
    nt.links.new(escn.outputs['Fac'], sj.inputs['Value'])
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.2, 'From Max': 1.1, 'To Min': 0.3 * sujo, 'To Max': 0.0})
    nt.links.new(sep.outputs['Z'], baixo.inputs['Value'])
    s1 = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(fog.outputs['Result'], s1.inputs[0])
    nt.links.new(sj.outputs['Result'], s1.inputs[1])
    s2 = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(s1.outputs['Value'], s2.inputs[0])
    nt.links.new(baixo.outputs['Result'], s2.inputs[1])
    gq = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    gq.inputs[1].default_value = 0.18
    nt.links.new(gm.outputs['Result'], gq.inputs[0])
    opaco = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(s2.outputs['Value'], opaco.inputs[0])
    nt.links.new(gq.outputs['Value'], opaco.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.62, 0.68, 0.64, 1)
    cor.inputs[7].default_value = (0.16, 0.13, 0.08, 1)
    nt.links.new(sj.outputs['Result'], cor.inputs[0])
    trans = no(nt, 'ShaderNodeBsdfTransparent')
    trans.inputs['Color'].default_value = (0.86, 0.92, 0.88, 1)
    fosco = no(nt, 'ShaderNodeBsdfPrincipled')
    fosco.inputs['Roughness'].default_value = 0.55
    nt.links.new(cor.outputs[2], fosco.inputs['Base Color'])
    mix1 = no(nt, 'ShaderNodeMixShader')
    nt.links.new(opaco.outputs['Value'], mix1.inputs[0])
    nt.links.new(trans.outputs[0], mix1.inputs[1])
    nt.links.new(fosco.outputs[0], mix1.inputs[2])
    brilho = no(nt, 'ShaderNodeBsdfGlossy')
    brilho.inputs['Roughness'].default_value = 0.06
    lw = no(nt, 'ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.25
    fr = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    fr.inputs[1].default_value = 0.8
    nt.links.new(lw.outputs['Fresnel'], fr.inputs[0])
    mix2 = no(nt, 'ShaderNodeMixShader')
    nt.links.new(fr.outputs['Value'], mix2.inputs[0])
    nt.links.new(mix1.outputs[0], mix2.inputs[1])
    nt.links.new(brilho.outputs[0], mix2.inputs[2])
    nt.links.new(mix2.outputs[0], out.inputs['Surface'])
    return m


def folha_mat(nome, c1, c2, emis=0.0, bump=0.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 18.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (*c1, 1)
    cor.inputs[7].default_value = (*c2, 1)
    nt.links.new(mr.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.42
    b.inputs['Emission Color'].default_value = (*c1, 1)
    b.inputs['Emission Strength'].default_value = emis
    if bump:
        bu = no(nt, 'ShaderNodeBump', **{'Strength': bump})
        vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 60.0})
        nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
        nt.links.new(vo.outputs['Distance'], bu.inputs['Height'])
        nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
    tr = no(nt, 'ShaderNodeBsdfTranslucent')
    nt.links.new(cor.outputs[2], tr.inputs['Color'])
    mx = no(nt, 'ShaderNodeMixShader')
    mx.inputs[0].default_value = 0.3
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
SEIVA = (1.0, 0.55, 0.06)
VERDE_IA = (0.35, 1.0, 0.12)
M = base3d.M
M.update({
    'amarelo': encardir(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.95, sujeira=0.95, ferrugem=0.5),
                        lama=0.8, lama_z=0.22, poeira=0.5, fuligem=0.35, fz=(0.1, 0.9), oleo=0.5),
    'amarelo2': encardir(mats.material('Amarelo trocado', (0.55, 0.42, 0.12), 0, 0.5, desgaste=0.8, sujeira=0.9, ferrugem=0.6),
                         lama=0.7, poeira=0.5, fuligem=0.3),
    'primer': encardir(mats.material('Primer vermelho', (0.32, 0.07, 0.04), 0, 0.6, desgaste=0.7, sujeira=0.9, ferrugem=0.5),
                       lama=0.6, poeira=0.4),
    'grafite': encardir(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.8, sujeira=0.9, ferrugem=0.3),
                        lama=0.6, poeira=0.6, fuligem=0.2, oleo=0.4),
    'aco': encardir(mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.45, pintura=False, ferrugem=0.85, sujeira=0.85, escovado=True),
                    lama=0.6, poeira=0.4, oleo=0.5),
    'estrutura': encardir(mats.material('Aço estrutural', (0.2, 0.2, 0.2), 0.9, 0.6, pintura=False, ferrugem=0.95, sujeira=0.95),
                          lama=0.7, poeira=0.5),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': encardir(mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
                      lama=0.7, poeira=0.4, oleo=0.4),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.45),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'concreto': encardir(mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.8, desgaste=0.0),
                         lama=0.6, lama_z=0.1, oleo=0.6),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'borracha': encardir(mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0), poeira=0.5),
    'mang_ambar': mats.material('Mangueira âmbar', (0.5, 0.22, 0.03), 0, 0.5, pintura=False, sujeira=0.8, desgaste=0.0),
    'mang_verde': mats.material('Mangueira verde', (0.08, 0.28, 0.06), 0, 0.5, pintura=False, sujeira=0.8, desgaste=0.0),
    'mang_ar': mats.material('Mangueira de ar', (0.12, 0.16, 0.3), 0, 0.5, pintura=False, sujeira=0.8, desgaste=0.0),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.012, 0.011, 0.011), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'tarja': mats.material('Tarja raspada', (0.5, 0.48, 0.44), 0.6, 0.5, pintura=False, sujeira=0.6, desgaste=0.0),
    'terra': mats.material('Terra', (0.085, 0.055, 0.03), 0, 0.95, pintura=False, sujeira=0.5, desgaste=0.0),
    'terra_seca': mats.material('Terra seca', (0.2, 0.14, 0.09), 0, 0.95, pintura=False, sujeira=0.4, desgaste=0.0),
    'lama': mats.material('Lama', (0.06, 0.04, 0.025), 0, 0.35, pintura=False, sujeira=0.3, desgaste=0.0),
    'musgo': folha_mat('Musgo', (0.16, 0.42, 0.03), (0.06, 0.2, 0.02), bump=0.6),
    'raiz': mats.material('Raiz', (0.27, 0.17, 0.09), 0, 0.8, pintura=False, sujeira=0.7, desgaste=0.0),
    'caule': mats.material('Caule', (0.16, 0.38, 0.05), 0, 0.5, pintura=False, sujeira=0.2, desgaste=0.0),
    'tronco': mats.material('Tronco', (0.17, 0.11, 0.07), 0, 0.85, pintura=False, sujeira=0.6, desgaste=0.0),
    'folha': folha_mat('Folha', (0.38, 0.85, 0.06), (0.06, 0.48, 0.05), emis=0.06),
    'folha_campo': folha_mat('Folha do campo', (0.55, 1.0, 0.12), (0.12, 0.7, 0.1), emis=0.25),
    'copa': folha_mat('Copa', (0.3, 0.72, 0.05), (0.05, 0.36, 0.04)),
    'vidro': vidro_sujo_mat('Vidro sujo'),
    'caco': vidro_sujo_mat('Caco', 0.5),
    'tubo_vidro': liquido_mat('Tubo de vidro', (0.85, 0.9, 0.88), 0.0, 0.85),
    'seiva': liquido_mat('Seiva', SEIVA, 1.4, 0.5),
    'nutriente': liquido_mat('Nutriente', (0.35, 0.85, 0.12), 1.2, 0.5),
    'seiva_poca': liquido_mat('Seiva derramada', (0.55, 0.22, 0.02), 0.15, 0.2),
    'agua': liquido_mat('Água', (0.8, 0.88, 0.92), 0.0, 0.9),
    'poca': liquido_mat('Poça', (0.04, 0.045, 0.04), 0.0, 0.0),
    'gota_seiva': emissivo('Gota de seiva', SEIVA, 6.0),
    'gel': emissivo('Gel de semente', (0.35, 1.0, 0.12), 4.0),
    'bolha': emissivo('Bolha de seiva', (1.0, 0.8, 0.35), 4.0),
    'bolha_n': emissivo('Bolha de nutriente', (0.6, 1.0, 0.4), 4.0),
    'listras': base3d.listras_mat(),
    'cresce': emissivo('Luz de crescimento', (1.0, 0.22, 0.7), 9.0),
    'cresce_falha': emissivo('Luz de crescimento falhando', (1.0, 0.22, 0.7), 9.0),
    'lente': emissivo('Lente do emissor', VIOLETA, 10.0, (0.1, 0.04, 0.2)),
    'anel_capsula': emissivo('Anel da cápsula', VIOLETA, 4.0),
    'semente': emissivo('Semente', (0.75, 1.0, 0.2), 12.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'led_vermelho': emissivo('Led vermelho', (1.0, 0.08, 0.03), 10.0),
    'olho': emissivo('Olho do sensor', VIOLETA, 8.0, (0.05, 0.02, 0.1)),
    'nevoa': base3d.volume_mat('Névoa', (0.88, 0.92, 0.92), 6.0, 1.15, 0.5),
})

# ==================================================================================================================
#                                                     VIVEIRO 2
# ==================================================================================================================
if OBRA == 'viveiro2':
    C = Vector((0.0, 0.0, 0.0))

    def campo_cresc_mat(z0, z1):
        m = bpy.data.materials.new('Campo de crescimento')
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        no = mats.no
        out = no(nt, 'ShaderNodeOutputMaterial')
        vol = no(nt, 'ShaderNodeVolumePrincipled')
        vol.inputs['Color'].default_value = (0.08, 0.04, 0.12, 1)
        nt.links.new(vol.outputs[0], out.inputs['Volume'])
        geo = no(nt, 'ShaderNodeNewGeometry')
        sep = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Position'], sep.inputs[0])
        x2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(sep.outputs['X'], x2.inputs[0]); nt.links.new(sep.outputs['X'], x2.inputs[1])
        y2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(sep.outputs['Y'], y2.inputs[0]); nt.links.new(sep.outputs['Y'], y2.inputs[1])
        s = no(nt, 'ShaderNodeMath', operation='ADD'); nt.links.new(x2.outputs[0], s.inputs[0]); nt.links.new(y2.outputs[0], s.inputs[1])
        rho = no(nt, 'ShaderNodeMath', operation='SQRT'); nt.links.new(s.outputs[0], rho.inputs[0])
        dr = no(nt, 'ShaderNodeMath', operation='SUBTRACT'); dr.inputs[1].default_value = 0.43
        nt.links.new(rho.outputs[0], dr.inputs[0])
        adr = no(nt, 'ShaderNodeMath', operation='ABSOLUTE'); nt.links.new(dr.outputs[0], adr.inputs[0])
        fr_ = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.2, 'From Max': 0.06}); nt.links.new(adr.outputs[0], fr_.inputs['Value'])
        at = no(nt, 'ShaderNodeMath', operation='ARCTAN2'); nt.links.new(sep.outputs['Y'], at.inputs[0]); nt.links.new(sep.outputs['X'], at.inputs[1])
        dth = no(nt, 'ShaderNodeMath', operation='SUBTRACT'); dth.inputs[1].default_value = PI / 2
        nt.links.new(at.outputs[0], dth.inputs[0])
        adth = no(nt, 'ShaderNodeMath', operation='ABSOLUTE'); nt.links.new(dth.outputs[0], adth.inputs[0])
        fa = no(nt, 'ShaderNodeMapRange', **{'From Min': math.radians(66), 'From Max': math.radians(40)}); nt.links.new(adth.outputs[0], fa.inputs['Value'])
        fz = no(nt, 'ShaderNodeMapRange', **{'From Min': z1 - 0.35, 'From Max': z1, 'To Min': 1.0, 'To Max': 0.0})
        nt.links.new(sep.outputs['Z'], fz.inputs['Value'])
        fz2 = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + 0.1}); nt.links.new(sep.outputs['Z'], fz2.inputs['Value'])
        ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 5.0})
        nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
        rm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.7, 'To Min': 0.15, 'To Max': 1.0})
        nt.links.new(ru.outputs['Fac'], rm.inputs['Value'])
        mul = rm.outputs['Result']
        for f in (fr_, fa, fz, fz2):
            mm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
            nt.links.new(mul, mm.inputs[0]); nt.links.new(f.outputs['Result'], mm.inputs[1])
            mul = mm.outputs[0]
        d = no(nt, 'ShaderNodeMath', operation='MULTIPLY'); d.inputs[1].default_value = 3.0
        nt.links.new(mul, d.inputs[0]); nt.links.new(d.outputs[0], vol.inputs['Density'])
        e = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca'); e.inputs[1].default_value = 8.0
        nt.links.new(mul, e.inputs[0]); nt.links.new(e.outputs[0], vol.inputs['Emission Strength'])
        veio = no(nt, 'ShaderNodeTexNoise', **{'Scale': 14.0, 'Detail': 2.0})
        nt.links.new(geo.outputs['Position'], veio.inputs['Vector'])
        vm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.62})
        nt.links.new(veio.outputs['Fac'], vm.inputs['Value'])
        cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
        cor.inputs[6].default_value = (0.55, 0.2, 1.0, 1)
        cor.inputs[7].default_value = (0.45, 1.0, 0.15, 1)
        nt.links.new(vm.outputs['Result'], cor.inputs[0])
        nt.links.new(cor.outputs[2], vol.inputs['Emission Color'])
        return m

    # ------------------------------------------------------------------ medidas
    Z0 = 0.08
    AP = 0.82
    R8 = AP / math.cos(PI / 8)
    W8 = 2 * AP * math.tan(PI / 8)
    ZE = 1.52                       # beiral (mais alto que o v1: dois níveis e a ponte rolante)
    Z_TEL0, Z_TEL1 = 1.60, 1.90
    AL = 0.30
    RL = AL / math.cos(PI / 8)
    R_T = 0.42
    Z_BAND = 0.44                   # nível de baixo (canteiros-matriz)
    Z_TERRA = 0.50
    Z_UP = 0.80                     # nível de cima (cápsulas)
    Z_CAP2 = Z_UP + 0.14            # origem da cápsula de longo alcance no nível de cima
    TANQUE = Vector((-0.72, -0.72, 0))
    TANQUE_N = Vector((-0.72, 0.72, 0))
    R_TQ = 0.16
    PORTA = Vector((-1.0, -0.5, 0.35))     # FLUIDO_ENT_O0
    PB = Vector((0.70, -0.70, 0))          # torre do canhão (canto sudeste)
    FACE_ABERTA = 7
    ST0 = Vector((C.x - R_T, C.y, 0))
    M.update({'campo': campo_cresc_mat(0.46, 1.25)})

    def V(a_deg, r=R8, z=0.0):
        a = math.radians(a_deg)
        return Vector((C.x + r * math.cos(a), C.y + r * math.sin(a), z))

    def face(k):
        phi = math.radians(45 * k)
        n = Vector((math.cos(phi), math.sin(phi), 0))
        t = Vector((-n.y, n.x, 0))
        return V(45 * k - 22.5), V(45 * k + 22.5), n, t, C + n * AP

    def z_tel(rho):
        return Z_TEL0 + (AP - rho) / (AP - AL) * (Z_TEL1 - Z_TEL0)

    def pos_estacao(th, r=R_T):
        a = math.radians(th)
        return Vector((C.x + r * math.cos(a), C.y + r * math.sin(a), 0))

    def chapa(bm, k, u0, u1, z0, z1, esp=0.016):
        A, Bv, n, t, Fc = face(k)
        caixa(bm, Fc + t * (u0 + u1) / 2 + Vector((0, 0, (z0 + z1) / 2)), (esp, u1 - u0, z1 - z0),
              Matrix.Rotation(math.radians(45 * k), 3, 'Z'))

    def quad(bm, a0, a1, b0, b1, ins=0.026, jag=None):
        a0, a1, b0, b1 = map(Vector, (a0, a1, b0, b1))
        lu = ((a1 - a0).length + (b1 - b0).length) / 2
        lv = ((b0 - a0).length + (b1 - a1).length) / 2
        u0, v0 = ins / lu, ins / lv
        n = 7 if jag else 1

        def P(u, v):
            return (a0.lerp(a1, u)).lerp(b0.lerp(b1, u), v)
        us = [u0 + (1 - 2 * u0) * i / n for i in range(n + 1)]
        vb = [bm.verts.new(P(u, v0)) for u in us]
        vt = [bm.verts.new(P(u, v0 + (1 - 2 * v0) * (jag[i] if jag else 1))) for i, u in enumerate(us)]
        for i in range(n):
            bm.faces.new((vb[i], vb[i + 1], vt[i + 1], vt[i]))

    bm_r = B('rebites', 'ferro')
    bm_pl, bm_tj = B('plaquetas', 'escuro'), B('tarjas', 'tarja')
    # ------------------------------------------------------------------ laje
    bm = bmesh.new()
    caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
    obj('laje', bm, 'concreto')
    bm = B('laje_listras', 'listras')
    for s in (-1, 1):
        caixa_de(bm, (-0.985, s * 0.985 - 0.012, 0.0), (0.985, s * 0.985 + 0.012, Z0 + 0.002))
        caixa_de(bm, (s * 0.985 - 0.012, -0.985, 0.0), (s * 0.985 + 0.012, 0.985, Z0 + 0.002))
    A7, B7, n7, t7, F7 = face(FACE_ABERTA)
    caixa(bm, F7 + Vector((0, 0, Z0 + 0.001)), (0.05, W8, 0.002), Matrix.Rotation(math.radians(315), 3, 'Z'))
    RACHAS = [((-0.1, 0.62), (-0.2, 0.8), (-0.12, 0.985)), ((0.3, 0.6), (0.45, 0.85), (0.4, 0.985)),
              ((-0.55, 0.3), (-0.75, 0.25), (-0.985, 0.32)), ((0.1, -0.6), (0.2, -0.8), (0.18, -0.985)),
              ((0.62, 0.3), (0.85, 0.12), (0.985, 0.15)), ((-0.4, -0.5), (-0.55, -0.42), (-0.6, -0.3))]
    bm = B('rachas', 'escuro')
    for pts in RACHAS:
        pts = [Vector((p[0], p[1], Z0 + 0.0006)) for p in pts]
        for a, b in zip(pts, pts[1:]):
            for k in range(4):
                p0, p1 = a.lerp(b, k / 4), a.lerp(b, (k + 1) / 4)
                j = Vector((random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), 0))
                u = (p1 - p0)
                w = Vector((-u.y, u.x, 0)).normalized() * random.uniform(0.006, 0.014)
                v0, v1 = bm.verts.new(p0 - w), bm.verts.new(p0 + w)
                v2, v3 = bm.verts.new(p1 + j + w * 0.7), bm.verts.new(p1 + j - w * 0.7)
                bm.faces.new((v0, v3, v2, v1))
    bm = B('laje_quebrada', 'concreto')
    caixa(bm, (-0.15, 0.86, Z0 + 0.03), (0.24, 0.16, 0.06), Matrix.Rotation(-0.2, 3, 'X') @ Matrix.Rotation(0.3, 3, 'Z'))
    caixa(bm, (0.42, 0.88, Z0 + 0.02), (0.14, 0.12, 0.05), Matrix.Rotation(0.18, 3, 'Y') @ Matrix.Rotation(-0.4, 3, 'Z'))
    for k in range(12):                                                    # óleo pingado em volta do canhão e do compressor
        mancha(B('oleo_chao', 'oleo'), (random.uniform(0.45, 0.95), random.uniform(-0.95, -0.2), 0), random.uniform(0.02, 0.07), Z0 + 0.0009 + 0.00005 * k)

    # ------------------------------------------------------------------ pavilhão octogonal de aço
    bm_e = B('estrutura', 'estrutura')
    bm_am = B('beiral', 'amarelo')
    for k in range(8):
        p = V(45 * k + 22.5)
        rad = (p - C); rad.z = 0; rad.normalize()
        viga_i(bm_e, p + Vector((0, 0, Z0)), p + Vector((0, 0, ZE + 0.07)), 0.065, 0.055, rad)
        caixa(bm_e, p + Vector((0, 0, Z0 + 0.006)), (0.13, 0.13, 0.012), Matrix.Rotation(math.radians(45 * k + 22.5), 3, 'Z'))
        for dx in (-0.045, 0.045):
            for dy in (-0.045, 0.045):
                cil(bm_r, p + Matrix.Rotation(math.radians(45 * k + 22.5), 3, 'Z') @ Vector((dx, dy, Z0 + 0.016)), 0.008, 0.012, lados=6)
    for k in range(8):
        A, Bv, n, t, Fc = face(k)
        mat_b = 'amarelo2' if k == 3 else 'amarelo'                             # beiral trocado (outra tinta)
        viga_i(B('beiral_' + mat_b, mat_b), A + Vector((0, 0, ZE + 0.035)), Bv + Vector((0, 0, ZE + 0.035)), 0.07, 0.055, (0, 0, 1))
        rebites(bm_r, A + n * 0.031 + Vector((0, 0, ZE + 0.035)), Bv + n * 0.031 + Vector((0, 0, ZE + 0.035)), 8)
        if k != FACE_ABERTA:
            viga(bm_e, A + Vector((0, 0, 0.62)), Bv + Vector((0, 0, 0.62)), 0.035)
            viga(bm_e, A + Vector((0, 0, 1.08)), Bv + Vector((0, 0, 1.08)), 0.03)
        for s in (-1, 1):
            p = A if s < 0 else Bv
            for e in (-0.004, 0.004):
                a_ = bm_e.verts.new(p + n * e + Vector((0, 0, ZE - 0.12)))
                b_ = bm_e.verts.new(p + n * e + Vector((0, 0, ZE)))
                c_ = bm_e.verts.new(p + n * e + Vector((0, 0, ZE)) - s * t * 0.11)
                bm_e.faces.new((a_, b_, c_) if e > 0 else (c_, b_, a_))
        plaqueta(bm_pl, bm_tj, Fc + n * 0.032 + t * 0.12 + Vector((0, 0, ZE + 0.035)), n, 0.05, 0.03)
    for k in range(8):
        a = 45 * k + 22.5
        p0, p1 = V(a, R8, Z_TEL0), V(a, RL, Z_TEL1)
        tv = Vector((-math.sin(math.radians(a)), math.cos(math.radians(a)), 0))
        up = (p1 - p0).normalized().cross(tv)
        viga_i(bm_e, p0, p1, 0.05, 0.04, up)
        rebites(bm_r, p0 + up * 0.026 + tv * 0.012, p1 + up * 0.026 + tv * 0.012, 7, r=0.004)
        viga(bm_e, V(a, R8, ZE + 0.07), p0, 0.035)
    for k in range(8):
        a0, a1 = 45 * k - 22.5, 45 * k + 22.5
        rm = (R8 + RL) / 2
        viga(bm_e, V(a0, rm, (Z_TEL0 + Z_TEL1) / 2), V(a1, rm, (Z_TEL0 + Z_TEL1) / 2), 0.03)
        viga(bm_e, V(a0, RL, Z_TEL1), V(a1, RL, Z_TEL1), 0.04)
    ZL0, ZL1 = Z_TEL1 + 0.02, Z_TEL1 + 0.13
    bm_lv = B('veneziana', 'casco')
    for k in range(8):
        A, Bv = V(45 * k - 22.5, RL), V(45 * k + 22.5, RL)
        viga(bm_e, A + Vector((0, 0, ZL0 - 0.02)), A + Vector((0, 0, ZL1)), 0.03)
        n = Vector((math.cos(math.radians(45 * k)), math.sin(math.radians(45 * k)), 0))
        for j in range(4):
            if k == 2 and j == 1:
                continue                                                    # uma lâmina caiu
            z = ZL0 + 0.015 + j * 0.027
            caixa(bm_lv, (A + Bv) / 2 + n * 0.005 + Vector((0, 0, z)), (0.004, (Bv - A).length - 0.03, 0.03),
                  Matrix.Rotation(math.radians(45 * k), 3, 'Z') @ Matrix.Rotation(-0.6, 3, 'Y'))
    bm = B('tampa', 'grafite')
    cil(bm, C + Vector((0, 0, ZL1 + 0.012)), RL + 0.04, 0.024, lados=8)
    cil(bm, C + Vector((0, 0, ZL1 + 0.034)), RL - 0.05, 0.02, lados=8)
    remendo(B('remendos', 'casco'), bm_r, C + Vector((0.12, -0.1, ZL1 + 0.044)), (0, 0, 1), 0.12, 0.09, 0.4)
    # chapas de rodapé; SO alta com colar (alimentação seiva); O com colar (alimentação nutriente)
    bm_k = B('rodape', 'casco')
    P_ALIM = Vector((-0.665, -0.495, 0.5))
    A5, B5, n5, t5, F5 = face(5)
    u_al = t5.dot(P_ALIM - F5)
    P_NUT = Vector((-AP, -0.1, 0.42))
    A4, B4, n4, t4, F4 = face(4)
    u_n = t4.dot(P_NUT - F4)
    for k, zt in ((0, 0.3), (1, 0.3), (2, 0.3), (6, 0.22)):
        chapa(bm_k, k, -W8 / 2 + 0.03, W8 / 2 - 0.03, Z0, zt)
    chapa(B('rodape_primer', 'primer'), 3, -W8 / 2 + 0.03, W8 / 2 - 0.03, Z0, 0.3)    # chapa trocada, só no primer
    rc = 0.035
    for k, u_, P_, zt in ((5, u_al, P_ALIM, 0.58), (4, u_n, P_NUT, 0.5)):
        chapa(bm_k, k, -W8 / 2 + 0.03, u_ - rc, Z0, zt)
        chapa(bm_k, k, u_ + rc, W8 / 2 - 0.03, Z0, zt)
        chapa(bm_k, k, u_ - rc, u_ + rc, Z0, P_.z - rc)
        chapa(bm_k, k, u_ - rc, u_ + rc, P_.z + rc, zt)
        nk = face(k)[2]
        tubo(B('colar', 'ferro', True), P_ - nk * 0.025, P_ + nk * 0.025, rc, 20)
        viga(bm_e, face(k)[0] + Vector((0, 0, zt)), face(k)[1] + Vector((0, 0, zt)), 0.035)
    remendo(B('remendos', 'casco'), bm_r, face(0)[4] + face(0)[2] * 0.009 + face(0)[3] * 0.1 + Vector((0, 0, 0.18)), face(0)[2], 0.14, 0.1, 0.15)
    remendo(B('remendos', 'casco'), bm_r, face(6)[4] + face(6)[2] * 0.009 + face(6)[3] * -0.12 + Vector((0, 0, 0.15)), face(6)[2], 0.12, 0.08, -0.1)
    for k in (0, 1, 2, 6):
        A, Bv, n, t, Fc = face(k)
        for j in range(3):
            escorrido(B('escorrido', 'ferrugem'), Fc + n * 0.009 + t * random.uniform(-0.2, 0.2) + Vector((0, 0, 0.27)), n, 0.12)
    for a in (67.5, 157.5, 292.5):
        p = V(a, R8 - 0.06, 1.3)
        u = (C + Vector((0, 0, 0.8)) - p).normalized()
        caixa(B('grafite', 'grafite'), p + (V(a, R8) - p) * 0.4, (0.03, 0.03, 0.05), Matrix.Rotation(math.radians(a), 3, 'Z'))
        cil(B('grafite', 'grafite'), p, 0.022, 0.05, u, 16)
        cil(B('olho', 'olho'), p + u * 0.026, 0.013, 0.004, u, 12)

    # ------------------------------------------------------------------ vidros (três fiadas nas paredes)
    bm_v = B('vidro', 'vidro')
    JAG = {(2, 2): [0.7, 0.85, 0.5, 0.9, 0.62, 0.8, 0.95, 0.75], (1, 1): [0.35, 0.6, 0.25, 0.55, 0.18, 0.4, 0.66, 0.3]}
    for k in range(8):
        if k == FACE_ABERTA:
            continue
        A, Bv, n, t, Fc = face(k)
        if k == 5:
            fileiras = [(1, 0.58, 1.08), (2, 1.08, ZE)]
        elif k == 4:
            fileiras = [(1, 0.5, 1.08), (2, 1.08, ZE)]
        elif k == 6:
            fileiras = [(1, 0.62, 1.08)]                                    # fiada de cima caiu: só o caixilho
        else:
            fileiras = [(0, 0.3, 0.62), (1, 0.62, 1.08), (2, 1.08, ZE)]
        for fi, z0, z1 in fileiras:
            quad(bm_v, A + Vector((0, 0, z0)), Bv + Vector((0, 0, z0)), A + Vector((0, 0, z1)), Bv + Vector((0, 0, z1)),
                 jag=JAG.get((k, fi)))
    for k in range(8):
        a0, a1 = 45 * k - 22.5, 45 * k + 22.5
        rm = (R8 + RL) / 2
        zm = (Z_TEL0 + Z_TEL1) / 2
        for fi, (ra, za, rb, zb) in enumerate(((R8, Z_TEL0, rm, zm), (rm, zm, RL, Z_TEL1))):
            o = Vector((0, 0, 0.03))
            if (k, fi) == (2, 1):
                continue
            if (k, fi) == (5, 0):                                           # vidro trocado por chapa enferrujada
                bm_ch = B('chapa_telhado', 'casco')
                pa, pb, pc = V(a0, ra, za) + o, V(a1, ra, za) + o, V(a0, rb, zb) + o
                pd = V(a1, rb, zb) + o
                vs = [bm_ch.verts.new(p) for p in (pa, pb, pd, pc)]
                bm_ch.faces.new(vs)
                rebites(bm_r, pa.lerp(pc, 0.1) + Vector((0, 0, 0.006)), pb.lerp(pd, 0.1) + Vector((0, 0, 0.006)), 6)
                continue
            jag = [0.55, 0.3, 0.62, 0.2, 0.45, 0.12, 0.38, 0.5] if (k, fi) == (6, 0) else None
            quad(bm_v, V(a0, ra, za) + o, V(a1, ra, za) + o, V(a0, rb, zb) + o, V(a1, rb, zb) + o, jag=jag)
    bm_c = B('cacos', 'caco')
    for cx, cy, n_ in ((0.0, -0.55, 6), (0.5, 0.05, 4), (-0.5, 0.42, 3)):
        for k in range(n_):
            p = Vector((cx + random.uniform(-0.12, 0.12), cy + random.uniform(-0.1, 0.1), Z0 + 0.003))
            a = random.uniform(0, 2 * PI)
            r = random.uniform(0.02, 0.05)
            vs = [bm_c.verts.new(p + Vector((r * math.cos(a + tt), r * math.sin(a + tt) * 0.6, 0.002 * j)))
                  for j, tt in enumerate((0, 2.1, 4.0))]
            bm_c.faces.new(vs)

    # ------------------------------------------------------------------ tanques: seiva (SO, boca O0) e nutriente (NO)
    bm_t = B('tanque', 'casco', True)
    bm_ta = B('tanque_amarelo', 'amarelo', True)
    bm_f = B('flanges', 'ferro', True)
    bm_aco = B('aco', 'aco', True)
    VISORES = {}
    for T, liq, dv in ((TANQUE, 'seiva', Vector((-0.707, -0.707, 0))), (TANQUE_N, 'nutriente', Vector((-0.707, 0.707, 0)))):
        cil(bm_t, T + Vector((0, 0, 0.51)), R_TQ, 0.7, lados=32)
        res = bmesh.ops.create_uvsphere(bm_t, u_segments=32, v_segments=10, radius=R_TQ,
                                        matrix=Matrix.Translation(T + Vector((0, 0, 0.86))) @ Matrix.Diagonal((1, 1, 0.45, 1)))
        bmesh.ops.delete(bm_t, geom=[v for v in res['verts'] if v.co.z < 0.86 - 1e-4], context='VERTS')
        for z in (0.2, 0.5, 0.82):
            toro(bm_ta if liq == 'seiva' else B('tanque_verde', 'mang_verde', True), T + Vector((0, 0, z)), R_TQ + 0.004, 0.012, 48, 8)
        for k in range(4):
            a = PI / 4 + k * PI / 2
            p = T + Vector((math.cos(a) * 0.115, math.sin(a) * 0.115, 0))
            viga(bm_aco, p + Vector((0, 0, Z0)), p + Vector((0, 0, 0.19)), 0.032)
            caixa(bm_aco, p + Vector((0, 0, Z0 + 0.005)), (0.065, 0.065, 0.01))
        VIS = T + dv * (R_TQ + 0.035)
        for z in (0.24, 0.78):
            tubo(bm_f, T + dv * (R_TQ - 0.01) + Vector((0, 0, z)), VIS + dv * 0.012 + Vector((0, 0, z)), 0.014, 12)
        tubo(B('visor_vidro', 'tubo_vidro', True), VIS + Vector((0, 0, 0.24)), VIS + Vector((0, 0, 0.78)), 0.016, 16)
        NIVEL = 0.62 if liq == 'seiva' else 0.45
        tubo(B('visor_' + liq, liq, True), VIS + Vector((0, 0, 0.245)), VIS + Vector((0, 0, NIVEL)), 0.012, 12)
        VISORES[liq] = (VIS + Vector((0, 0, 0.26)), VIS + Vector((0, 0, NIVEL - 0.01)))
        cil(bm_aco, T + Vector((0, 0, 0.95)), 0.03, 0.04, lados=16)
        caixa(B('grafite', 'grafite'), T + Vector((0, 0, 1.0)), (0.07, 0.05, 0.06))
        cil(B('led_verde', 'led_verde'), T + Vector((-0.036, 0, 1.01)), 0.007, 0.004, Vector((-1, 0, 0)), 8)
        for a in (0.3, 1.9, 2.6, 4.2):
            p = T + Vector((math.cos(a) * (R_TQ + 0.001), math.sin(a) * (R_TQ + 0.001), 0))
            caixa(B('escorrido', 'ferrugem'), p + Vector((0, 0, 0.55)), (0.006 + 0.004 * abs(math.sin(a)), 0.006 + 0.004 * abs(math.cos(a)), 0.4))
        for k in range(14):
            a = random.uniform(0, 2 * PI)
            pedra(B('musgo', 'musgo'), T + Vector((math.cos(a) * 0.14, math.sin(a) * 0.14, Z0 + 0.006)), random.uniform(0.01, 0.022), 0.5)
        for k in range(12):                                                 # musgo no domo do tanque
            a = random.uniform(0, 2 * PI)
            rr = random.uniform(0.03, 0.12)
            pedra(B('musgo', 'musgo'), T + Vector((math.cos(a) * rr, math.sin(a) * rr, 0.86 + 0.45 * math.sqrt(max(0, R_TQ ** 2 - rr ** 2)) - 0.004)),
                  random.uniform(0.012, 0.024), 0.45)
        plaqueta(bm_pl, bm_tj, T + dv.cross(Vector((0, 0, 1))) * (R_TQ + 0.002) + Vector((0, 0, 0.36)), dv.cross(Vector((0, 0, 1))), 0.06, 0.035)
    remendo(B('remendos', 'casco'), bm_r, TANQUE + Vector((0.0, -R_TQ - 0.001, 0.4)), (0, -1, 0), 0.08, 0.1, 0.0, 0.005)
    remendo(B('remendos_primer', 'primer'), bm_r, TANQUE_N + Vector((R_TQ * 0.7, R_TQ * 0.7, 0.3)), (0.707, 0.707, 0), 0.07, 0.09, 0.2, 0.005)
    T = TANQUE
    XE = -0.76
    yt = T.y + math.sqrt(R_TQ ** 2 - (XE - T.x) ** 2)
    cano(bm_aco, bm_f, [PORTA, Vector((XE, PORTA.y, PORTA.z)), Vector((XE, yt - 0.01, PORTA.z))], 0.045, flange=False)
    for p, u in ((PORTA + Vector((0.012, 0, 0)), Vector((1, 0, 0))), (Vector((XE, yt + 0.025, PORTA.z)), Vector((0, 1, 0)))):
        tubo(bm_f, p - u * 0.01, p + u * 0.01, 0.07, 20)
        w = u.cross(Vector((0, 0, 1)))
        for k in range(8):
            a = k * PI / 4
            cil(bm_r, p + u * 0.012 + w * 0.058 * math.cos(a) + Vector((0, 0, 0.058 * math.sin(a))), 0.007, 0.01, u, 6)
    caixa(bm_f, (-0.9, PORTA.y, (Z0 + PORTA.z - 0.045) / 2), (0.04, 0.05, PORTA.z - 0.045 - Z0))
    bm = B('seiva_poca', 'seiva_poca')
    mancha(bm, (-0.93, PORTA.y - 0.03, 0), 0.07, Z0 + 0.0015)
    caixa(bm, PORTA + Vector((0.012, -0.072, -(PORTA.z - Z0) / 2 + 0.02)), (0.012, 0.004, PORTA.z - Z0 - 0.06))
    # nutriente: tanque NO → desce pelo lado de fora da face O → colar → armário
    TN = TANQUE_N
    p_s = TN + Vector((-0.08, -R_TQ * 0.98 + 0.02, 0.3))
    cano(bm_aco, bm_f, [p_s + Vector((0, 0.02, 0)), Vector((p_s.x, p_s.y - 0.1, 0.3)), Vector((-0.9, p_s.y - 0.1, 0.3)),
                        Vector((-0.9, P_NUT.y, 0.3)), Vector((-0.9, P_NUT.y, P_NUT.z)), Vector((-0.80, P_NUT.y, P_NUT.z))], 0.016, flange=False)
    for p_ in (Vector((-0.9, 0.3, 0.3)),):
        tubo(bm_f, p_ - Vector((0, 0.01, 0)), p_ + Vector((0, 0.01, 0)), 0.026, 16)
    caixa(bm_f, (-0.9, 0.3, (Z0 + 0.28) / 2), (0.03, 0.03, 0.28 - Z0))

    # ------------------------------------------------------------------ estação de dosagem (oeste)
    DX0, DX1, DY0, DY1, DZ = -0.80, -0.60, -0.32, -0.04, 0.6
    caixa_de(B('armario', 'amarelo'), (DX0, DY0, Z0), (DX1, DY1, DZ))
    caixa_de(B('grafite', 'grafite'), (DX1 - 0.002, DY0 + 0.04, 0.2), (DX1 + 0.006, DY1 - 0.04, 0.5))
    for z in (0.22, 0.48):
        rebites(bm_r, (DX1 + 0.006, DY0 + 0.05, z), (DX1 + 0.006, DY1 - 0.05, z), 6)
    cil(B('led_ambar', 'led_ambar'), Vector((DX1 + 0.008, DY1 - 0.06, 0.55)), 0.008, 0.006, Vector((1, 0, 0)), 8)
    cil(B('led_verde', 'led_verde'), Vector((DX1 + 0.008, DY1 - 0.09, 0.55)), 0.008, 0.006, Vector((1, 0, 0)), 8)
    plaqueta(bm_pl, bm_tj, Vector((DX1 + 0.007, DY0 + 0.1, 0.13)), (1, 0, 0))
    escorrido(B('oleo_esc', 'oleo'), Vector((DX1 + 0.006, DY1 - 0.08, 0.2)), (1, 0, 0), 0.1, 0.01)
    d = Vector((0.342, 0.94, 0))
    cano(bm_aco, bm_f, [T + d * (R_TQ - 0.01) + Vector((0, 0, P_ALIM.z)), Vector((P_ALIM.x, T.y + 0.94 * R_TQ + 0.02, P_ALIM.z)),
                        Vector((P_ALIM.x, DY0 + 0.01, P_ALIM.z))], 0.016, flange=False)
    DOS_X = [-0.72, -0.64]
    Z_DOS = DZ + 0.05
    DYO = DY0 + 0.34
    PIST_Y0, PIST_LC = DY0 + 0.02, 0.09
    CRUZ_Y = (-0.215 + DYO, -0.185 + DYO)
    for i, x in enumerate(DOS_X):
        caixa_de(bm_aco, (x - 0.03, PIST_Y0 - 0.012, DZ), (x + 0.03, PIST_Y0 + 0.004, Z_DOS + 0.03))
        caixa_de(bm_aco, (x - 0.03, -0.155 + DYO, DZ), (x + 0.03, -0.14 + DYO, Z_DOS + 0.03))
        cil(B('dosadora', 'grafite', True), Vector((x, -0.09 + DYO, Z_DOS)), 0.026, 0.11, Vector((0, 1, 0)), 20)
        tubo(bm_f, (x, -0.15 + DYO, Z_DOS), (x, -0.136 + DYO, Z_DOS), 0.032, 20)
        tubo(bm_f, (x, -0.044 + DYO, Z_DOS), (x, -0.03 + DYO, Z_DOS), 0.032, 20)
        caixa_de(bm_aco, (x - 0.026, -0.23 + DYO, DZ), (x + 0.026, -0.16 + DYO, DZ + 0.012))
        mangueira(B('mang_sup', 'borracha', True), bezier((x, -0.2 + DYO, DZ - 0.002), (x, -0.25 + DYO, DZ - 0.02),
                                                          (x + 0.02, -0.28 + DYO, DZ + 0.01), (x, PIST_Y0 + 0.03, Z_DOS - 0.018), 6), 0.006)
    # lança: coluna, braço até a estação 180° do nível de cima, cabeça com magazine e dois bicos
    LZ = Z_CAP2 + 0.2
    cano(bm_aco, bm_f, [Vector((-0.70, DY1, DZ)), Vector((-0.70, DY1, LZ)), Vector((ST0.x - 0.03, ST0.y - 0.03, LZ))], 0.018, flange=False)
    CAB = Vector((ST0.x, ST0.y, LZ))
    caixa(B('cabeca', 'amarelo'), CAB + Vector((0, -0.04, 0)), (0.12, 0.1, 0.06))
    BICOS = [CAB + Vector((-0.02, -0.052, -0.03)), CAB + Vector((0.02, -0.052, -0.03))]
    for i, bp in enumerate(BICOS):
        cil(bm_f, bp + Vector((0, 0, -0.035)), 0.008, 0.05, lados=10, r2=0.004)
        cil(bm_aco, bp + Vector((0, 0, 0.005)), 0.012, 0.02, lados=12)
        mat = ('mang_ambar', 'mang_verde')[i]
        x = DOS_X[i]
        mangueira(B('mang' + mat, mat, True), bezier((x, -0.03 + DYO, Z_DOS), (x, 0.02 + DYO, Z_DOS + 0.08),
                                                     (bp.x - 0.1, bp.y - 0.08, LZ + 0.14), bp + Vector((0, 0, 0.04)), 12), 0.008)
    MAG_Z0, MAG_Z1 = LZ + 0.03, z_tel(R_T) - 0.09
    tubo(B('magazine', 'tubo_vidro', True), (CAB.x, CAB.y, MAG_Z0), (CAB.x, CAB.y, MAG_Z1), 0.05, 20)
    for z in (MAG_Z0 + 0.01, (MAG_Z0 + MAG_Z1) / 2, MAG_Z1 - 0.01):
        toro(B('mag_aneis', 'amarelo', True), Vector((CAB.x, CAB.y, z)), 0.053, 0.006, 24, 6)
    for k in range(3):
        a = k * 2 * PI / 3
        viga(bm_aco, (CAB.x + 0.058 * math.cos(a), CAB.y + 0.058 * math.sin(a), LZ), (CAB.x + 0.058 * math.cos(a), CAB.y + 0.058 * math.sin(a), MAG_Z1), 0.008)
    cil(B('grafite', 'grafite'), Vector((CAB.x, CAB.y, MAG_Z1 + 0.02)), 0.062, 0.04, lados=20)
    tubo(bm_aco, (CAB.x, CAB.y, MAG_Z1 + 0.04), (CAB.x, CAB.y, z_tel(abs(CAB.x - C.x)) - 0.025), 0.01, 8)
    feixe(B('cabos', 'cabo', True), B('abracadeiras', 'aco'),
          bezier((-0.78, -0.1, DZ), (-0.8, -0.05, 1.2), (-0.75, 0.0, MAG_Z1), Vector((CAB.x, CAB.y + 0.02, MAG_Z1 + 0.035)), 12),
          Vector((0, 1, 0)), n=2, r=0.006)
    # aspersores
    Z_LUZ = ZE + 0.1
    Z_ANEL, R_ANEL = Z_LUZ + 0.2, 0.26
    ASP = [V(a, R_ANEL, Z_LUZ - 0.02) for a in (90, 210, 330)]
    p_fim = V(200, R_ANEL, Z_ANEL)
    cano(bm_aco, bm_f, [Vector((-0.775, -0.29, DZ)), Vector((-0.775, -0.29, ZE - 0.05)), p_fim], 0.016, flange=False)
    toro(bm_aco, C + Vector((0, 0, Z_ANEL)), R_ANEL, 0.016, 48, 12)
    for a in ASP:
        tubo(bm_aco, Vector((a.x, a.y, Z_ANEL)), a + Vector((0, 0, 0.04)), 0.012, 12)
        curva(bm_aco, Vector((a.x, a.y, Z_ANEL)), 0.017)
        cil(B('grafite', 'grafite'), a + Vector((0, 0, 0.03)), 0.022, 0.03, lados=16)
    for a in (0, 120, 240):
        p = V(a + 30, R_ANEL, Z_ANEL)
        tubo(bm_f, p + Vector((0, 0, 0.016)), Vector((p.x, p.y, Z_TEL1 + 0.13)), 0.004, 6)

    # ------------------------------------------------------------------ carrossel: parte fixa
    bm_cf = B('carrossel_fixo', 'grafite')
    cil(bm_cf, C + Vector((0, 0, Z0 + 0.02)), 0.16, 0.04, lados=8)
    cil(bm_aco, C + Vector((0, 0, (Z0 + 0.33) / 2)), 0.07, 0.33 - Z0, lados=20)
    caixa(B('motor', 'amarelo'), C + Vector((0, -0.24, 0.19)), (0.12, 0.1, 0.2))
    plaqueta(bm_pl, bm_tj, C + Vector((0, -0.291, 0.22)), (0, -1, 0), 0.06, 0.04)
    cil(bm_aco, C + Vector((0, -0.15, 0.3)), 0.012, 0.1, lados=10)
    cil(B('pinhao', 'ferro', True), C + Vector((0, -0.15, 0.345)), 0.03, 0.03, lados=12)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        p = C + Vector((R_T * math.cos(a), R_T * math.sin(a), 0))
        viga(bm_aco, p + Vector((0, 0, Z0)), p + Vector((0, 0, 0.392)), 0.025)
        caixa(bm_aco, p + Vector((0, 0, Z0 + 0.005)), (0.06, 0.06, 0.01))
    toro(B('trilho', 'cromo', True), C + Vector((0, 0, 0.398)), R_T, 0.01, 96, 8)
    feixe(B('cabos', 'cabo', True), B('abracadeiras', 'aco'),
          bezier(C + Vector((-0.06, -0.24, 0.12)), C + Vector((-0.1, -0.4, Z0 + 0.01)), Vector((-0.5, -0.3, Z0 + 0.01)),
                 Vector((DX1 + 0.005, -0.25, 0.12)), 10), Vector((0, 0, 1)), n=2, r=0.008)

    # ------------------------------------------------------------------ campo de crescimento (cobre os dois níveis)
    bm_em = B('emissores', 'estrutura')
    bm_l = B('lentes', 'lente')
    R_P = 0.65
    Z_ARCO = 1.32
    for th in (162, 18):
        p = V(th, R_P)
        viga_i(bm_em, p + Vector((0, 0, Z0)), p + Vector((0, 0, Z_ARCO)), 0.055, 0.05, (C - p).normalized())
        caixa(bm_aco, p + Vector((0, 0, Z0 + 0.008)), (0.11, 0.11, 0.016))
        u = (C - p); u.z = 0; u.normalize()
        for z in (0.6, 0.92, 1.18):
            cil(B('grafite', 'grafite'), p + u * 0.045 + Vector((0, 0, z)), 0.04, 0.05, u, 16)
            cil(bm_l, p + u * 0.073 + Vector((0, 0, z)), 0.03, 0.006, u, 16)
            toro(B('bobina', 'cobre', True), p + u * 0.045 + Vector((0, 0, z)), 0.044, 0.006, 24, 6,
                 u.to_track_quat('Z', 'Y').to_matrix())
    toro(bm_em, C + Vector((0, 0, Z_ARCO)), R_P, 0.018, 64, 10, a0=math.radians(18), a1=math.radians(162))
    for th in (50, 90, 130):
        a = math.radians(th)
        p = C + Vector((R_P * math.cos(a), R_P * math.sin(a), Z_ARCO - 0.02))
        u = Vector((-math.cos(a), -math.sin(a), -0.9)).normalized()
        cil(B('grafite', 'grafite'), p + u * 0.03, 0.035, 0.06, u, 16)
        cil(bm_l, p + u * 0.062, 0.026, 0.006, u, 16)
    bm = bmesh.new()
    n = 24
    an = [math.radians(22 + (158 - 22) * i / n) for i in range(n + 1)]
    vs = []
    for a in an:
        vs.append([bm.verts.new(C + Vector((r * math.cos(a), r * math.sin(a), z))) for r, z in ((0.2, 0.46), (0.66, 0.46), (0.66, 1.3), (0.2, 1.3))])
    for i in range(n):
        for j in range(4):
            bm.faces.new((vs[i][j], vs[i][(j + 1) % 4], vs[i + 1][(j + 1) % 4], vs[i + 1][j]))
    bm.faces.new(list(reversed(vs[0])))
    bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj('campo', bm, 'campo')

    # ------------------------------------------------------------------ anel de luz de crescimento
    R_LUZ = 0.45
    for k in range(8):
        if k == 4:
            continue
        a0, a1 = 45 * k - 22.5, 45 * k + 22.5
        p0, p1 = V(a0, R_LUZ, Z_LUZ), V(a1, R_LUZ, Z_LUZ)
        m = (p0 + p1) / 2
        L = (p1 - p0).length - 0.02
        R_ = Matrix.Rotation(math.radians(45 * k), 3, 'Z')
        bm = B('barra_luz', 'grafite')
        caixa(bm, m + Vector((0, 0, 0.02)), (0.09, L, 0.04), R_)
        for j in range(7):
            caixa(bm, m + R_ @ Vector((0, -L / 2 + 0.02 + j * (L - 0.04) / 6, 0.052)), (0.08, 0.006, 0.025), R_)
        caixa(B('led_luz%d' % (k == 2), 'cresce_falha' if k == 2 else 'cresce'), m + Vector((0, 0, -0.0025)), (0.06, L - 0.02, 0.004), R_)
        for s in (-1, 1):
            ph = m + R_ @ Vector((0, s * L * 0.3, 0.065))
            tubo(bm_f, ph, Vector((ph.x, ph.y, z_tel((ph - C).dot(R_ @ Vector((1, 0, 0)))) - 0.02)), 0.004, 6)

    # ------------------------------------------------------------------ nó da IA (canto nordeste)
    caixa_de(B('no_ia', 'grafite'), (0.7, 0.7, Z0), (0.96, 0.96, 0.52))
    caixa_de(B('no_ia_am', 'amarelo'), (0.69, 0.69, Z0), (0.97, 0.97, 0.13))
    for k in range(5):
        caixa_de(B('aletas_no', 'aco'), (0.72 + k * 0.05, 0.695, 0.2), (0.74 + k * 0.05, 0.7, 0.45))
    for k in range(4):
        cil(B('led_verde' if k else 'led_ambar', 'led_verde' if k else 'led_ambar'), Vector((0.696, 0.74, 0.26 + 0.05 * k)),
            0.007, 0.006, Vector((-1, 0, 0)), 8)
    caixa_de(B('grafite', 'grafite'), (0.694, 0.79, 0.2), (0.7, 0.93, 0.48))
    rebites(bm_r, (0.693, 0.8, 0.47), (0.693, 0.92, 0.47), 4)
    rebites(bm_r, (0.693, 0.8, 0.21), (0.693, 0.92, 0.21), 4)
    for k in range(3):
        p = Vector((0.76 + 0.07 * k, 0.9, 0.52))
        cil(B('bornes', 'cobre', True), p + Vector((0, 0, 0.03)), 0.014, 0.06, lados=12)
        for j in range(3):
            toro(B('bornes_isol', 'grafite', True), p + Vector((0, 0, 0.012 + 0.016 * j)), 0.02, 0.005, 16, 6)
    cil(B('olho', 'olho'), Vector((0.83, 0.83, 0.525)), 0.02, 0.006, lados=16)
    bm_cab = B('cabos', 'cabo', True)
    bm_ab = B('abracadeiras', 'aco')
    pE = V(18, R_P)
    A1, B1, n1, t1, F1 = face(1)
    feixe(bm_cab, bm_ab, bezier((0.72, 0.72, 0.12), (0.62, 0.62, Z0 + 0.01), F1 + Vector((0, 0, Z0 + 0.012)),
                                pE + Vector((0.03, 0.03, Z0 + 0.02)), 10), Vector((0, 0, 1)), n=2, r=0.008)
    pv = V(67.5, R8 - 0.04)
    feixe(bm_cab, bm_ab, [Vector((0.75, 0.96, 0.4)), Vector((pv.x + 0.02, pv.y + 0.05, 0.5)), pv + Vector((0, 0, 0.7)),
                          pv + Vector((0, 0, ZE - 0.02)), V(67.5, R_LUZ + 0.06, Z_LUZ + 0.05)], Vector((0, 0, 1)), n=2, r=0.006, passo=1)

    # ------------------------------------------------------------------ leitor de bioma (faixa sul): pórtico, pistão, sonda
    LB = Vector((-0.08, -0.905, 0))
    Z_LB = 1.0                                                              # travessa do pórtico
    for s in (-1, 1):
        p = LB + Vector((s * 0.11, 0, 0))
        viga_i(B('leitor_est', 'estrutura'), p + Vector((0, 0, Z0)), p + Vector((0, 0, Z_LB + 0.03)), 0.05, 0.045, (1, 0, 0))
        caixa(B('leitor_am', 'amarelo'), p + Vector((0, 0, Z0 + 0.008)), (0.08, 0.08, 0.016))
        cil(bm_r, p + Vector((0.025, 0.025, Z0 + 0.02)), 0.006, 0.01, lados=6)
        cil(bm_r, p + Vector((-0.025, -0.025, Z0 + 0.02)), 0.006, 0.01, lados=6)
    caixa(B('leitor_am', 'amarelo'), LB + Vector((0, 0, Z_LB + 0.05)), (0.3, 0.07, 0.05))
    caixa(B('leitor_am', 'amarelo'), LB + Vector((0, 0, 0.15)), (0.24, 0.05, 0.03))    # guia da sonda (bucha no meio)
    cil(bm_f, LB + Vector((0, 0, 0.15)), 0.024, 0.036, lados=16)
    cil(B('colar_sonda', 'ferro', True), LB + Vector((0, 0, Z0 + 0.012)), 0.035, 0.024, lados=20)
    bm = B('rachas', 'escuro')
    for k in range(5):
        a = k * 2 * PI / 5 + 0.3
        p0 = LB + Vector((0.035 * math.cos(a), 0.035 * math.sin(a), Z0 + 0.0006))
        p1 = LB + Vector((0.09 * math.cos(a + 0.2), 0.09 * math.sin(a + 0.2), Z0 + 0.0006))
        w = Vector((-math.sin(a), math.cos(a), 0)) * 0.004
        vs = [bm.verts.new(p) for p in (p0 - w, p1, p0 + w)]
        bm.faces.new(vs)
    # tubo de testemunho (camadas de solo lidas) ao lado, e caixa da IA com olho
    TB = LB + Vector((0.2, 0.0, 0))
    caixa_de(B('leitor_caixa', 'grafite'), (TB.x - 0.04, TB.y - 0.04, Z0), (TB.x + 0.07, TB.y + 0.045, 0.34))
    plaqueta(bm_pl, bm_tj, Vector((TB.x + 0.015, TB.y - 0.041, 0.2)), (0, -1, 0), 0.05, 0.03)
    cil(B('olho', 'olho'), Vector((TB.x + 0.015, TB.y - 0.041, 0.29)), 0.012, 0.004, Vector((0, -1, 0)), 12)
    tubo(B('tubo_core', 'tubo_vidro', True), Vector((TB.x - 0.065, TB.y, 0.12)), Vector((TB.x - 0.065, TB.y, 0.62)), 0.022, 16)
    for z0_, z1_, mt in ((0.125, 0.25, 'terra'), (0.25, 0.33, 'terra_seca'), (0.33, 0.42, 'terra'), (0.42, 0.48, 'raiz'),
                         (0.48, 0.54, 'terra_seca'), (0.54, 0.6, 'musgo')):
        tubo(B('core_' + mt, mt, True), Vector((TB.x - 0.065, TB.y, z0_)), Vector((TB.x - 0.065, TB.y, z1_)), 0.018, 12)
    for z in (0.12, 0.62):
        toro(B('core_aneis', 'aco', True), Vector((TB.x - 0.065, TB.y, z)), 0.024, 0.005, 20, 6)
    feixe(bm_cab, bm_ab, [Vector((TB.x + 0.071, TB.y, 0.26)), Vector((TB.x + 0.1, TB.y - 0.02, Z0 + 0.03)),
                          Vector((TB.x + 0.16, -0.958, Z0 + 0.008)), Vector((0.958, -0.958, Z0 + 0.008)),
                          Vector((0.962, 0.4, Z0 + 0.008)), Vector((0.9, 0.68, 0.15))], Vector((0, 0, 1)), n=2, r=0.006, passo=1)
    mangueira(B('mang_sonda', 'borracha', True), bezier(LB + Vector((0.11, 0.0, Z_LB)), LB + Vector((0.2, -0.03, Z_LB + 0.1)),
                                                        TB + Vector((0.0, -0.03, 0.5)), TB + Vector((0.0, 0.0, 0.34)), 10), 0.006)

    # ------------------------------------------------------------------ compressor do canhão (faixa leste)
    CX0, CX1, CY0, CY1 = 0.84, 0.945, -0.34, 0.16
    caixa_de(B('compressor', 'amarelo2'), (CX0, CY0, Z0), (CX1, CY1, 0.3))
    for k in range(9):
        caixa_de(B('aletas_comp', 'aco'), (CX0 - 0.006, CY0 + 0.04 + k * 0.045, 0.1), (CX0, CY0 + 0.06 + k * 0.045, 0.27))
    for k in range(2):                                                     # dois cabeçotes de cilindro aletados no topo
        p = Vector(((CX0 + CX1) / 2, CY0 + 0.12 + 0.2 * k, 0.3))
        cil(B('cabecote', 'ferro', True), p + Vector((0, 0, 0.06)), 0.045, 0.12, lados=20)
        for j in range(5):
            cil(B('cabecote', 'ferro', True), p + Vector((0, 0, 0.02 + 0.022 * j)), 0.058, 0.006, lados=20)
        cil(bm_aco, p + Vector((0, 0, 0.13)), 0.03, 0.02, lados=16)
    cil(B('grafite', 'grafite'), Vector(((CX0 + CX1) / 2, CY1 - 0.05, 0.36)), 0.05, 0.12, Vector((0, 1, 0)), 24)   # motor
    plaqueta(bm_pl, bm_tj, Vector((CX0 - 0.007, CY0 + 0.06, 0.06)), (-1, 0, 0), 0.05, 0.03)
    escorrido(B('oleo_esc', 'oleo'), Vector((CX0 - 0.007, CY0 + 0.3, 0.1)), (-1, 0, 0), 0.08, 0.012)
    mancha(B('oleo_chao', 'oleo'), (CX0 - 0.06, CY0 + 0.3, 0), 0.06, Z0 + 0.0021)
    cil(B('led_vermelho', 'led_vermelho'), Vector((CX0 - 0.002, CY1 - 0.04, 0.27)), 0.007, 0.006, Vector((-1, 0, 0)), 8)

    # ------------------------------------------------------------------ canhão: pedestal fixo
    Z_GIRO = 0.44
    bm_pd = B('pedestal', 'amarelo', True)
    cil(bm_pd, PB + Vector((0, 0, (Z0 + Z_GIRO - 0.02) / 2)), 0.13, Z_GIRO - 0.02 - Z0, lados=28)
    cil(bm_f, PB + Vector((0, 0, Z0 + 0.012)), 0.18, 0.024, lados=28)
    for k in range(10):
        a = k * 2 * PI / 10
        cil(bm_r, PB + Vector((0.158 * math.cos(a), 0.158 * math.sin(a), Z0 + 0.03)), 0.011, 0.016, lados=6)
    for k in range(6):                                                      # nervuras
        a = k * PI / 3 + PI / 6
        d_ = Vector((math.cos(a), math.sin(a), 0))
        bmn = B('nervuras', 'amarelo')
        vs = [bmn.verts.new(PB + d_ * r_ + Vector((0, 0, z_)) + Vector((-d_.y, d_.x, 0)) * e)
              for e in (-0.006, 0.006) for r_, z_ in ((0.128, Z0 + 0.024), (0.175, Z0 + 0.024), (0.128, 0.25))]
        bmn.faces.new(vs[0:3]); bmn.faces.new(vs[3:6][::-1])
        for i_ in range(3):
            j_ = (i_ + 1) % 3
            bmn.faces.new((vs[i_], vs[j_], vs[3 + j_], vs[3 + i_])[::-1])
    toro(B('listra_ped', 'listras', True), PB + Vector((0, 0, 0.36)), 0.132, 0.012, 32, 6)
    cil(B('coroa', 'ferro', True), PB + Vector((0, 0, Z_GIRO - 0.01)), 0.17, 0.03, lados=48)
    for k in range(48):
        a = k * 2 * PI / 48
        caixa(B('coroa', 'ferro', True), PB + Vector((0.173 * math.cos(a), 0.173 * math.sin(a), Z_GIRO - 0.01)), (0.012, 0.008, 0.026),
              Matrix.Rotation(a, 3, 'Z'))
    caixa(B('motor_giro', 'grafite'), PB + Vector((-0.2, 0.05, Z_GIRO - 0.07)), (0.07, 0.07, 0.1), Matrix.Rotation(PI / 4, 3, 'Z'))
    cil(B('pinhao', 'ferro', True), PB + Vector((-0.19, 0.04, Z_GIRO - 0.01)), 0.026, 0.028, lados=12)
    caixa(B('motor_giro', 'grafite'), PB + Vector((-0.15, 0.035, Z_GIRO - 0.09)), (0.06, 0.05, 0.04), Matrix.Rotation(0.2, 3, 'Z'))
    escorrido(B('oleo_esc', 'oleo'), PB + Vector((0.0, -0.131, 0.38)), (0, -1, 0), 0.18, 0.014)
    escorrido(B('oleo_esc', 'oleo'), PB + Vector((0.093, 0.093, 0.4)), (0.707, 0.707, 0), 0.2, 0.012)
    plaqueta(bm_pl, bm_tj, PB + Vector((-0.093, -0.093, 0.22)), (-0.707, -0.707, 0), 0.06, 0.04)
    remendo(B('remendos', 'casco'), bm_r, PB + Vector((0.12, -0.05, 0.16)), (0.92, -0.38, 0), 0.07, 0.08, 0.1, 0.004)
    # mangueiras de ar: compressor → junta rotativa (embaixo da torre)
    for k, yy in enumerate((CY0 + 0.12, CY0 + 0.32)):
        mangueira(B('mang_ar', 'mang_ar', True), bezier(((CX0 + CX1) / 2, yy, 0.43), ((CX0 + CX1) / 2 - 0.05, yy - 0.05, 0.55),
                                                        PB + Vector((0.25, 0.15 - 0.04 * k, 0.32)), PB + Vector((0.135, 0.02 * k, 0.3)), 12), 0.011)

    # ------------------------------------------------------------------ marcações do canhão
    YAW0 = -38.0                                                            # azimute de tiro (graus)
    ELEV = 47.0
    Z_MUN = 0.80                                                            # altura dos munhões
    L_CANO, L_CULATRA = 1.0, 0.27
    V_BOCA = 10.9                                                          # m/s: ~12 m de alcance a 47°

    # ------------------------------------------------------------------ raízes, musgo, terra, poça
    bm_rz = B('raizes', 'raiz', True)

    def z_sup(x, y):
        m = max(abs(x), abs(y))
        return Z0 if m < 0.975 else max(0.0, Z0 - (m - 0.975) * 3.0)

    def raiz_org(bm, p, d, comp, r0, sem, galhos=True, sobe=0.0):
        rr = random.Random(sem)
        p = Vector((p[0], p[1], 0))
        d = Vector((d[0], d[1], 0)).normalized()
        n = 16
        passo = comp / n
        pts = []
        for i in range(n + 1):
            t = i / n
            r = r0 * (1 - 0.8 * t)
            arco = sobe * math.sin(PI * min(1.0, t * 3)) if t < 0.34 else 0.0
            pts.append(Vector((p.x, p.y, z_sup(p.x, p.y) + r * 0.45 + arco)))
            d = Matrix.Rotation(rr.uniform(-0.38, 0.38), 3, 'Z') @ d
            p = p + d * passo
        raiz(bm, pts, r0, r0 * 0.2)
        if galhos:
            for j in range(3, n - 2, 4):
                lado = Matrix.Rotation(rr.choice((-1, 1)) * rr.uniform(0.6, 1.1), 3, 'Z') @ d
                raiz_org(bm, pts[j], (pts[j + 1] - pts[j - 1]).normalized().lerp(lado, 0.7), comp * 0.3, r0 * 0.45, sem * 7 + j, False)

    k_ = 0
    for pts in RACHAS:
        a = Vector((pts[0][0], pts[0][1], 0))
        b_ = Vector((pts[-1][0], pts[-1][1], 0))
        raiz_org(bm_rz, a, b_ - a, (b_ - a).length + 0.25, 0.016, 11 + k_)
        k_ += 1
    O_N = Vector((-0.15, 0.86, 0))
    for k in range(5):
        a = math.radians(160 + k * 40)
        raiz_org(bm_rz, O_N, (math.cos(a), math.sin(a)), 0.5 + 0.1 * (k % 2), 0.03 - 0.002 * k, 50 + k, sobe=0.05 + 0.015 * (k % 3))

    def raiz_sobe(bm, p, R, z0, z1, voltas, r0, sem, fase=0.0):
        """Raiz que sobe em espiral abraçando um pilar, solta radicelas que se agarram."""
        rr = random.Random(sem)
        n = int(30 * voltas)
        pts = []
        for i in range(n + 1):
            t = i / n
            a = fase + 2 * PI * voltas * t
            rad = R * (1 + 0.15 * math.sin(7 * t + sem))
            pts.append(Vector((p.x + rad * math.cos(a), p.y + rad * math.sin(a), z0 + (z1 - z0) * t)))
        raiz(bm, pts, r0, r0 * 0.25)
        for j in range(4, n - 2, 6):
            d = (pts[j] - Vector((p.x, p.y, pts[j].z))).normalized()
            raiz(bm, [pts[j], pts[j] + d * 0.03 + Vector((0, 0, -0.03)), pts[j] + d * 0.035 + Vector((0, 0, -0.07 - rr.uniform(0, 0.05)))],
                 r0 * 0.35, r0 * 0.12, 5)

    for a_, z1_, vt, sem in ((202.5, 1.35, 3.0, 3), (247.5, 0.95, 2.0, 5), (112.5, 1.5, 3.4, 7), (157.5, 0.7, 1.4, 9)):
        p = V(a_)
        raiz_sobe(bm_rz, p, 0.05, Z0, z1_, vt, 0.016, sem, fase=sem)
        raiz_org(bm_rz, p, (p - C), 0.5, 0.02, 90 + sem)
    for a_, s_ in ((200, 0), (235, 1), (120, 2), (100, 3), (175, 4), (260, 5)):    # raízes aéreas pendendo do beiral
        p = V(a_, AP / math.cos(math.radians((a_ % 45) - 22.5)) + 0.04, ZE + 0.07)
        L_ = 0.35 + 0.12 * (s_ % 3)
        raiz(bm_rz, [p, p + Vector((0.02, 0.01, -L_ * 0.3)), p + Vector((-0.01, 0.02, -L_ * 0.65)), p + Vector((0.01, -0.01, -L_))],
             0.008, 0.002, 5)
    bm_m = B('musgo', 'musgo')
    for cx, cy, r in ((-0.15, 0.82, 0.16), (-0.5, 0.75, 0.09), (0.15, -0.75, 0.1), (-0.3, -0.6, 0.06), (0.88, 0.3, 0.07),
                      (-0.88, 0.4, 0.06), (0.3, 0.55, 0.05), (-0.88, -0.05, 0.07)):
        mancha(bm_m, (cx, cy, 0), r, Z0 + 0.0012)
        for k in range(int(10 + 60 * r)):
            pedra(bm_m, (cx + random.uniform(-r, r), cy + random.uniform(-r, r) * 0.7, Z0 + 0.003), random.uniform(0.008, 0.02), 0.45)
    for k in range(8):
        p = V(45 * k + 22.5)
        for j in range(5):
            pedra(bm_m, (p.x + random.uniform(-0.07, 0.07), p.y + random.uniform(-0.07, 0.07), Z0 + 0.015), random.uniform(0.008, 0.016), 0.5)
    for k in range(8):                                                      # musgo em almofadas em cima do beiral
        A, Bv, n, t, Fc = face(k)
        for j in range(random.randint(2, 5)):
            u_ = random.uniform(-0.15, 0.15)
            pedra(bm_m, Fc + t * u_ + Vector((0, 0, ZE + 0.072)), random.uniform(0.012, 0.022), 0.4)
    bm_te = B('terra', 'terra')
    for k in range(40):
        a = random.uniform(0, 2 * PI)
        r = R_T + random.uniform(-0.12, 0.14)
        pedra(bm_te, C + Vector((r * math.cos(a), r * math.sin(a), Z0 + 0.004)), random.uniform(0.008, 0.02), 0.35)
    for k in range(5):
        a = random.uniform(0, 2 * PI)
        mancha(bm_te, (C.x + 0.4 * math.cos(a), C.y + 0.4 * math.sin(a), 0), 0.08, Z0 + 0.0008 + 0.0002 * k)
    mancha(B('poca', 'poca'), (-0.2, 0.1, 0), 0.16, Z0 + 0.001)
    mancha(B('poca', 'poca'), (0.15, -0.2, 0), 0.1, Z0 + 0.0011)

    # ------------------------------------------------------------------ plantas
    def folha(bm, base, d, comp, larg, cai=0.25):
        d = Vector(d).normalized()
        up = Vector((0, 0, 1))
        side = d.cross(up)
        side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
        rows = []
        n = 6
        for i in range(n + 1):
            t = i / n
            c = base + d * comp * t + up * (-cai * comp * t * t)
            w = larg * (math.sin(PI * t) ** 0.7 if 0 < t < 1 else 0.0)
            lift = up * 0.3 * w
            rows.append((bm.verts.new(c + side * w + lift), bm.verts.new(c), bm.verts.new(c - side * w + lift)))
        for i in range(n):
            bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
            bm.faces.new((rows[i][1], rows[i][2], rows[i + 1][2], rows[i + 1][1]))

    def muda(bmc, bmf, base, h, nf, sem, larg_max=9.0):
        rr = random.Random(sem)
        base = Vector(base)
        sx, sy = rr.uniform(-0.15, 0.15) * h, rr.uniform(-0.15, 0.15) * h
        pts = [base + Vector((sx * t * t, sy * t * t, h * t)) for t in (i / 6 for i in range(7))]
        mangueira(bmc, pts, 0.003 + 0.012 * h)
        a0 = rr.uniform(0, 2 * PI)
        for j in range(nf):
            t = 0.28 + 0.72 * j / nf
            p = base + Vector((sx * t * t, sy * t * t, h * t))
            a = a0 + j * 2.4
            comp = min(larg_max, h * (0.62 - 0.3 * t) * rr.uniform(0.85, 1.15))
            d = Vector((math.cos(a), math.sin(a), 0.35 + 0.9 * t))
            folha(bmf, p, d, comp, comp * 0.36, cai=0.35 - 0.25 * t)
        topo = pts[-1]
        for a in (a0, a0 + PI):
            folha(bmf, topo, (math.cos(a) * 0.3, math.sin(a) * 0.3, 1), h * 0.16, h * 0.05, 0.0)

    def capsula2(partes, origem=Vector((0, 0, 0)), rot=Matrix.Identity(3), gasta=False, cupula=True):
        """Cápsula de longo alcance: ponta (−z), corpo de aço, 3 aletas, anel violeta, colar; cúpula de vidro (+z) com a
        muda dentro (cravada: cúpula estilhaçada/aberta, só o aro)."""
        o = Vector(origem)
        bc = partes.setdefault('casco' if gasta else 'aco', bmesh.new())
        ba = partes.setdefault('ferro' if gasta else 'anel_capsula', bmesh.new())
        bt = partes.setdefault('terra', bmesh.new())
        bf = partes.setdefault('ferro', bmesh.new())
        M_ = Matrix.Translation(o) @ rot.to_4x4()
        bmesh.ops.create_cone(bc, cap_ends=True, segments=16, radius1=0.032, radius2=0.032, depth=0.1,
                              matrix=M_ @ Matrix.Translation((0, 0, -0.02)))
        bmesh.ops.create_cone(bc, cap_ends=True, segments=16, radius1=0.004, radius2=0.032, depth=0.06,
                              matrix=M_ @ Matrix.Translation((0, 0, -0.1)))
        for k in range(3):
            a = k * 2 * PI / 3
            caixa(bc, o + rot @ Vector((0.044 * math.cos(a), 0.044 * math.sin(a), -0.04)), (0.026, 0.003, 0.06),
                  rot @ Matrix.Rotation(a, 3, 'Z'))
        bmesh.ops.create_cone(ba, cap_ends=True, segments=16, radius1=0.0332, radius2=0.0332, depth=0.012,
                              matrix=M_ @ Matrix.Translation((0, 0, -0.005)))
        toro(bf, o + rot @ Vector((0, 0, 0.03)), 0.033, 0.005, 20, 6, rot)
        bmesh.ops.create_cone(bt, cap_ends=True, segments=12, radius1=0.029, radius2=0.029, depth=0.006,
                              matrix=M_ @ Matrix.Translation((0, 0, 0.03)))
        if cupula:
            bv = partes.setdefault('tubo_vidro', bmesh.new())
            bmesh.ops.create_cone(bv, cap_ends=False, segments=20, radius1=0.031, radius2=0.031, depth=0.08,
                                  matrix=M_ @ Matrix.Translation((0, 0, 0.073)))
            res = bmesh.ops.create_uvsphere(bv, u_segments=20, v_segments=10, radius=0.031, matrix=M_ @ Matrix.Translation((0, 0, 0.113)))
            bmesh.ops.delete(bv, geom=[v for v in res['verts'] if (M_.inverted() @ v.co).z < 0.113 - 1e-4], context='VERTS')
            cil(bf, o + rot @ Vector((0, 0, 0.146)), 0.008, 0.008, rot @ Vector((0, 0, 1)), 10)   # válvula de dosagem
        return partes

    # mudas da espécie do bioma plantadas em volta (cápsula gasta no pé) — umas de folha larga, outras pinheirinhos
    def pinheiro(bt, bc, p, h, sem):
        rr = random.Random(sem)
        raiz(bt, [p, p + Vector((0, 0, h * 0.5)), p + Vector((0.01, 0, h))], 0.006 + 0.025 * h, 0.004)
        nt_ = 8
        for j in range(nt_):                                                # andares de ramos caídos (abeto jovem)
            t = j / (nt_ - 1)
            z = h * (0.18 + 0.78 * t)
            rad = (0.36 - 0.3 * t) * h + 0.02
            nr_ = 11 - j
            for i in range(nr_):
                a = 2 * PI * i / nr_ + rr.uniform(-0.2, 0.2) + j * 0.7
                d = Vector((math.cos(a), math.sin(a), rr.uniform(-0.35, -0.1)))
                c0 = p + Vector((0.01 * t, 0, z))
                folha(bc, c0, d, rad * rr.uniform(0.8, 1.1), rad * 0.28, 0.35)
                folha(bc, c0 + Vector((0, 0, 0.012)), Matrix.Rotation(0.3, 3, 'Z') @ d, rad * 0.7, rad * 0.22, 0.25)
        folha(bc, p + Vector((0.01, 0, h * 0.92)), (0.05, 0, 1), h * 0.12, h * 0.03, 0.0)

    M.update({'agulha': folha_mat('Agulhas', (0.12, 0.36, 0.08), (0.04, 0.2, 0.05), bump=0.4)})
    ARVORES = [(1.5, 0.6, 0.55), (1.8, -0.2, 0.3), (1.25, 1.5, 0.85), (-0.35, 1.6, 0.6), (-0.6, -1.95, 0.4),
               (2.25, 0.95, 0.22), (-1.6, 0.95, 0.45), (-1.45, -1.35, 0.5), (0.9, 2.05, 0.3), (2.45, -0.6, 0.2),
               (-2.2, -0.2, 0.7), (-0.9, -2.2, 0.35), (2.9, -2.4, 0.25), (3.4, -1.3, 0.32), (-2.6, 1.9, 0.5)]
    fora = {}
    for i, (x, y, h) in enumerate(ARVORES):
        p = Vector((x, y, 0))
        pedra(B('terra_fora', 'terra_seca'), p, 0.09 + 0.05 * h, 0.35)
        inc = Matrix.Rotation(random.uniform(0.25, 0.5), 3, 'X') @ Matrix.Rotation(random.uniform(0, 2 * PI), 3, 'Z')
        capsula2(fora, p + Vector((0.08, 0.05, 0.045)), Matrix.Rotation(random.uniform(0, 2 * PI), 3, 'Z') @ inc, gasta=True, cupula=False)
        if i % 3 == 1:
            pinheiro(B('troncos', 'tronco', True), B('agulhas', 'agulha'), p, h + 0.2, 200 + i)
        elif h < 0.35:
            muda(B('caule_fora', 'caule', True), B('folha_fora', 'folha'), p + Vector((0, 0, 0.03)), h, 9, 100 + i)
        else:
            bt = B('troncos', 'tronco', True)
            topo = p + Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), h))
            raiz(bt, [p, p.lerp(topo, 0.5) + Vector((0.02, 0, 0)), topo], 0.012 + 0.03 * h, 0.008)
            bmc = B('copa', 'copa')
            for k in range(6):
                a = k * 2 * PI / 6 + random.uniform(0, 0.5)
                c = topo + Vector((math.cos(a) * 0.12 * h, math.sin(a) * 0.12 * h, random.uniform(-0.08, 0.12) * h))
                raiz(bt, [p.lerp(topo, 0.75), c], 0.008, 0.004)
                rc = 0.15 * h + 0.03
                for j in range(34):
                    d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.4, 1))).normalized()
                    cf = 0.05 + 0.06 * h
                    folha(bmc, c + d * rc * random.uniform(0.3, 0.8), d + Vector((0, 0, 0.3)), cf, cf * 0.42, 0.3)
            for k in range(4):
                a = random.uniform(0, 2 * PI)
                raiz(bt, [p + Vector((0, 0, 0.02)), p + Vector((math.cos(a) * 0.07, math.sin(a) * 0.07, 0.0)),
                          p + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, -0.02))], 0.009, 0.003)
    for mat, bm in fora.items():
        obj('capsulas_gastas_' + mat, bm, mat)

    # ------------------------------------------------------------------ ponte rolante (fixa): trilho em perfil I
    H_PT = pos_estacao(0)                                                  # casa: em cima da estação 0° do nível de cima
    E_PT = PB.copy()                                                       # fim: eixo da torre do canhão
    U_PT = (E_PT - H_PT).normalized()
    Z_TRB = 1.42                                                           # base do trilho
    ROT_PT0 = Matrix.Rotation(math.atan2(U_PT.y, U_PT.x), 3, 'Z')
    trA, trB = H_PT - U_PT * 0.1, E_PT + U_PT * 0.08
    viga_i(B('trilho_pt', 'amarelo'), trA + Vector((0, 0, Z_TRB + 0.03)), trB + Vector((0, 0, Z_TRB + 0.03)), 0.06, 0.05, (0, 0, 1))
    rebites(bm_r, trA + Vector((0, 0, Z_TRB + 0.061)), trB + Vector((0, 0, Z_TRB + 0.061)), 14, r=0.004)
    for p in (trA, trB):                                                   # batentes
        caixa(B('batente', 'listras'), p + Vector((0, 0, Z_TRB + 0.03)), (0.05, 0.05, 0.07), Matrix.Rotation(math.atan2(U_PT.y, U_PT.x), 3, 'Z'))
    # pendurais: dois tirantes até o espigão; mão-francesa até o pilar −22,5° e travessa entre os pilares da face aberta
    for f_ in (0.25, 0.5):
        p = H_PT.lerp(E_PT, f_)
        rho = (p - C).length
        tubo(bm_aco, p + Vector((0, 0, Z_TRB + 0.06)), p + Vector((0, 0, z_tel(rho) + 0.02)), 0.008, 8)
        cil(bm_f, p + Vector((0, 0, Z_TRB + 0.068)), 0.016, 0.014, lados=8)
    pX = H_PT + U_PT * U_PT.dot(face(7)[4] - H_PT)                          # onde o trilho cruza a face aberta (sob o beiral)
    caixa(bm_f, pX + Vector((0, 0, (Z_TRB + 0.06 + ZE) / 2)), (0.05, 0.05, ZE - Z_TRB - 0.06 + 0.004), ROT_PT0)
    rebites(bm_r, pX + Vector((-0.02, -0.026, Z_TRB + 0.07)), pX + Vector((0.02, -0.026, Z_TRB + 0.07)), 2, r=0.005)
    # mastro de estai em cima do beiral: tirantes seguram a ponta em balanço e ancoram no espigão
    Z_MST = ZE + 0.07 + 0.24
    viga(bm_e, pX + Vector((0, 0, ZE + 0.07)), pX + Vector((0, 0, Z_MST)), 0.035)
    caixa(bm_f, pX + Vector((0, 0, ZE + 0.075)), (0.08, 0.08, 0.01))
    tubo(bm_aco, pX + Vector((0, 0, Z_MST - 0.01)), trB + Vector((0, 0, Z_TRB + 0.06)), 0.006, 8)
    pAnc = V(-22.5, R8 - 0.12, z_tel(AP - 0.12) + 0.03)
    tubo(bm_aco, pX + Vector((0, 0, Z_MST - 0.01)), pAnc, 0.006, 8)
    pAnc2 = V(-67.5, R8 - 0.12, z_tel(AP - 0.12) + 0.03)
    tubo(bm_aco, pX + Vector((0, 0, Z_MST - 0.01)), pAnc2, 0.006, 8)
    for p_ in (trB + Vector((0, 0, Z_TRB + 0.065)), pAnc, pAnc2):
        cil(bm_f, p_, 0.014, 0.012, lados=8)
    cil(B('led_vermelho', 'led_vermelho'), pX + Vector((0, 0, Z_MST + 0.01)), 0.012, 0.02, lados=10)   # luz de topo
    feixe(bm_cab, bm_ab, [H_PT + Vector((0, 0.0, Z_TRB + 0.068)) + U_PT.cross(Vector((0, 0, 1))) * 0.015,
                          E_PT + Vector((0, 0.0, Z_TRB + 0.068)) - U_PT * 0.06 + U_PT.cross(Vector((0, 0, 1))) * 0.015],
          U_PT.cross(Vector((0, 0, 1))), n=2, r=0.005, passo=1)

    # ------------------------------------------------------------------ objetos estáticos
    for (nome, mat, liso), bm in BMS.items():
        o = obj(nome, bm, mat)
        if liso:
            suavizar(o)

    def peca(nome, partes):
        objs = []
        for mat, bm in partes.items():
            o = obj(nome + '_' + mat, bm, mat)
            suavizar(o)
            o.rotation_mode = 'QUATERNION'
            objs.append(o)
        return objs

    def pose(objs, Mw, q, prev={}):
        loc, rot, _ = Mw.decompose()
        for o in objs:
            k = o.name
            if k in prev:
                rot.make_compatible(prev[k])
            prev[k] = rot.copy()
            o.location = loc
            o.rotation_quaternion = rot
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)

    def escala(objs, s, q):
        for o in objs:
            o.scale = (s, s, s)
            o.keyframe_insert('scale', frame=q)

    def vis(objs, v, q):
        for o in objs:
            o.hide_render = o.hide_viewport = not v
            o.keyframe_insert('hide_render', frame=q)
            o.keyframe_insert('hide_viewport', frame=q)

    # carrossel de dois níveis
    car = {}
    bcar = car.setdefault('aco', bmesh.new())
    bam = car.setdefault('amarelo', bmesh.new())
    bfe = car.setdefault('ferro', bmesh.new())
    bte = car.setdefault('terra', bmesh.new())
    bmu = car.setdefault('musgo', bmesh.new())
    bse = car.setdefault('semente', bmesh.new())
    cil(bfe, Vector((0, 0, 0.345)), 0.12, 0.03, lados=40)
    for k in range(32):
        a = k * 2 * PI / 32
        caixa(bfe, (0.123 * math.cos(a), 0.123 * math.sin(a), 0.345), (0.012, 0.008, 0.028), Matrix.Rotation(a, 3, 'Z'))
    cil(bam, Vector((0, 0, 0.41)), 0.09, 0.1, lados=24)
    cil(bcar, Vector((0, 0, (0.46 + Z_UP - 0.02) / 2)), 0.045, Z_UP - 0.02 - 0.46, lados=20)       # mastro do nível de cima
    cil(bam, Vector((0, 0, Z_UP - 0.03)), 0.08, 0.05, lados=24)
    cil(bcar, Vector((0, 0, Z_UP + 0.0)), 0.06, 0.01, lados=24)
    car.setdefault('lente', bmesh.new())
    cil(car['lente'], Vector((0, 0, Z_UP + 0.007)), 0.03, 0.006, lados=16)
    for z in (0.5, 0.62):
        toro(bfe, Vector((0, 0, z)), 0.047, 0.006, 20, 6)
    MAT_SEM = []
    for k in range(6):
        a = math.radians(180 - 60 * k)
        R_ = Matrix.Rotation(a, 3, 'Z')
        for zb, nivel in ((0.426, 0), (Z_UP - 0.014, 1)):
            viga(bcar, R_ @ Vector((0.08 if nivel == 0 else 0.05, 0, zb)), R_ @ Vector((R_T - 0.08, 0, zb)), 0.03)
            c = R_ @ Vector((R_T, 0, 0))
            zt = 0.446 if nivel == 0 else Z_UP + 0.006
            caixa(bam, c + Vector((0, 0, zt)), (0.2, 0.17, 0.012), R_)
            for (dx, dy, sx, sy) in ((0.096, 0, 0.008, 0.17), (-0.096, 0, 0.008, 0.17), (0, 0.081, 0.2, 0.008), (0, -0.081, 0.2, 0.008)):
                caixa(bam, c + R_ @ Vector((dx, dy, zt + 0.037)), (sx, sy, 0.064), R_)
            caixa(bte, c + Vector((0, 0, zt + 0.029)), (0.184, 0.154, 0.05), R_)
            for j in range(6):
                pedra(bte, c + R_ @ Vector((random.uniform(-0.07, 0.07), random.uniform(-0.06, 0.06), zt + 0.054)), random.uniform(0.01, 0.018), 0.4)
            for j in range(3):
                pedra(bmu, c + R_ @ Vector((random.uniform(-0.08, 0.08), random.uniform(-0.065, 0.065), zt + 0.056)), random.uniform(0.007, 0.013), 0.4)
            for sy in (-1, 1):
                rebites(bfe, c + R_ @ Vector((-0.09, sy * 0.086, zt + 0.054)), c + R_ @ Vector((0.09, sy * 0.086, zt + 0.054)), 5, r=0.004)
            if nivel == 0:
                # canteiro-matriz: forração densa, mudinhas e espigas de semente que brilham
                for j in range(14):
                    pb = c + R_ @ Vector((random.uniform(-0.08, 0.08), random.uniform(-0.065, 0.065), Z_TERRA - 0.002))
                    hh = random.uniform(0.03, 0.11)
                    muda(car.setdefault('caule', bmesh.new()), car.setdefault('folha', bmesh.new()), pb, hh, 5, 300 + k * 30 + j)
                    if j % 4 == 0:
                        for e in range(5):
                            bmesh.ops.create_icosphere(bse, subdivisions=1, radius=0.005,
                                                       matrix=Matrix.Translation(pb + Vector((random.uniform(-0.008, 0.008), random.uniform(-0.008, 0.008), hh + 0.01 + 0.008 * e))))
                caixa(bcar, c + Vector((0, 0, 0.432)), (0.03, 0.04, 0.016), R_)
                cil(bfe, c + Vector((0, 0, 0.42)), 0.012, 0.03, R_ @ Vector((1, 0, 0)), 12)
            else:
                for j in range(4):
                    pb = c + R_ @ Vector((random.choice((-0.065, 0.065)), random.uniform(-0.055, 0.055), zt + 0.052))
                    muda(car.setdefault('caule', bmesh.new()), car.setdefault('folha', bmesh.new()), pb, random.uniform(0.02, 0.035), 4, 600 + k * 10 + j)
                cil(bfe, c + Vector((0, 0, zt + 0.05)), 0.04, 0.012, lados=16)                # anel-berço da cápsula
                # mão-francesa do mastro ao braço do nível de cima
                viga(bcar, R_ @ Vector((0.04, 0, Z_UP - 0.2)), R_ @ Vector((R_T - 0.12, 0, Z_UP - 0.03)), 0.016)
    carrossel = peca('carrossel', car)

    def ang_carrossel(fr):
        return -60.0 * smooth(fr / 0.3)

    # cápsulas do nível de cima, mudas dentro, cápsula em trânsito
    MUDA_H, MUDA_NF = 0.095, 9
    cap_band, mud_band = [], []
    for k in range(6):
        cap_band.append(peca('capsula%d' % k, capsula2({})))
        mp = {'caule': bmesh.new(), 'folha_campo': bmesh.new()}
        muda(mp['caule'], mp['folha_campo'], Vector((0, 0, 0)), MUDA_H, MUDA_NF, k, larg_max=0.026)
        mud_band.append(peca('muda%d' % k, mp))
    cap_voo = peca('capsula_voo', capsula2({}))
    mp = {'caule': bmesh.new(), 'folha_campo': bmesh.new()}
    muda(mp['caule'], mp['folha_campo'], Vector((0, 0, 0)), MUDA_H, MUDA_NF, 3, larg_max=0.026)
    mud_voo = peca('muda_voo', mp)
    CAP_MAG = Vector((CAB.x, CAB.y, MAG_Z0 + 0.13))
    mag_baixo = peca('capsula_magazine', capsula2({}))
    mag_pilha = capsula2({}, CAP_MAG + Vector((0, 0, 0.27)))
    for mat, bm in mag_pilha.items():
        obj('magazine_pilha_' + mat, bm, mat)

    # ponte rolante: carro (anda no trilho), pistão vertical (camisa no carro) e garra (haste + colar + 3 dedos)
    ROT_PT = Matrix.Rotation(math.atan2(U_PT.y, U_PT.x), 3, 'Z')
    carro = {'grafite': bmesh.new(), 'amarelo': bmesh.new(), 'ferro': bmesh.new(), 'olho': bmesh.new(), 'cabo': bmesh.new()}
    caixa_de(carro['grafite'], (-0.07, -0.045, -0.055), (0.07, 0.045, -0.005))
    for sx in (-0.05, 0.05):
        for sy in (-1, 1):
            cil(carro['ferro'], Vector((sx, sy * 0.032, 0.01)), 0.016, 0.012, Vector((0, 1, 0)), 12)   # roletes na mesa de baixo
            caixa_de(carro['grafite'], (sx - 0.012, sy * 0.04 - 0.004, -0.01), (sx + 0.012, sy * 0.04 + 0.004, 0.03))
    cil(carro['amarelo'], Vector((0, 0, -0.105)), 0.022, 0.1, lados=20)                 # camisa
    cil(carro['ferro'], Vector((0, 0, -0.157)), 0.026, 0.008, lados=20)
    cil(carro['olho'], Vector((0.071, 0, -0.03)), 0.009, 0.004, Vector((1, 0, 0)), 10)
    caixa_de(carro['grafite'], (-0.075, 0.045, -0.05), (-0.03, 0.06, -0.01))
    mangueira(carro['cabo'], bezier((-0.05, 0.055, -0.02), (-0.09, 0.07, 0.0), (-0.12, 0.06, 0.05), (-0.13, 0.03, 0.065), 6), 0.006)
    pc_carro = peca('ponte_carro', carro)
    garra = {'cromo': bmesh.new(), 'amarelo': bmesh.new(), 'grafite': bmesh.new()}
    L_HG = 0.18
    cil(garra['cromo'], Vector((0, 0, L_HG / 2 + 0.012)), 0.009, L_HG, lados=12)       # haste
    cil(garra['amarelo'], Vector((0, 0, 0.006)), 0.045, 0.012, lados=24)              # colar
    pc_garra = peca('ponte_garra', garra)
    dedos_pt = []
    for k in range(3):
        a = PI / 3 + k * 2 * PI / 3
        dd = {'aco': bmesh.new(), 'borracha': bmesh.new()}
        caixa(dd['aco'], Vector((0, 0, -0.065)), (0.006, 0.016, 0.14))
        caixa(dd['borracha'], Vector((-0.004, 0, -0.13)), (0.004, 0.014, 0.02))
        dedos_pt.append((a, peca('dedo_pt%d' % k, dd)))

    # canhão: torre (gira), berço+cano (eleva/recua), culatra (pistão)
    torre = {'grafite': bmesh.new(), 'amarelo': bmesh.new(), 'aco': bmesh.new(), 'ferro': bmesh.new(), 'casco': bmesh.new(),
             'mang_ar': bmesh.new(), 'olho': bmesh.new(), 'listras': bmesh.new(), 'led_verde': bmesh.new()}
    tz = Z_GIRO
    cil(torre['grafite'], Vector((0, 0, tz + 0.02)), 0.22, 0.035, lados=40)
    for s in (-1, 1):                                                       # munhoneiras
        bmz = torre['amarelo']
        vs = [bmz.verts.new(Vector((x_, s * 0.105 + e, z_))) for e in (-0.014, 0.014)
              for x_, z_ in ((-0.16, tz + 0.035), (0.16, tz + 0.035), (0.07, Z_MUN + 0.06), (-0.06, Z_MUN + 0.06))]
        bmz.faces.new(vs[0:4]); bmz.faces.new(vs[4:8][::-1])
        for i_ in range(4):
            j_ = (i_ + 1) % 4
            bmz.faces.new((vs[i_], vs[j_], vs[4 + j_], vs[4 + i_])[::-1])
        cil(torre['ferro'], Vector((0, s * 0.128, Z_MUN)), 0.042, 0.02, Vector((0, 1, 0)), 24)
        rebites(torre['ferro'], (-0.14, s * 0.12, tz + 0.06), (0.14, s * 0.12, tz + 0.06), 7, r=0.005)
        for k in range(6):
            a = k * PI / 3
            cil(torre['ferro'], Vector((0.03 * math.cos(a), s * 0.139, Z_MUN + 0.03 * math.sin(a))), 0.006, 0.008, Vector((0, 1, 0)), 6)
    # cilindros de ar comprimido (dois, atrás, deitados para não cruzar o cano) presos por cintas
    for s in (-1, 1):
        c_ = Vector((-0.04, s * 0.19, tz + 0.115))
        cil(torre['casco'], c_, 0.05, 0.2, Vector((1, 0, 0)), 24)
        for e in (-1, 1):
            curva(torre['casco'], c_ + Vector((e * 0.1, 0, 0)), 0.05, 20)
            toro(torre['ferro'], c_ + Vector((e * 0.055, 0, 0)), 0.052, 0.006, 24, 6, Matrix.Rotation(PI / 2, 3, 'Y'))
            caixa(torre['ferro'], c_ + Vector((e * 0.055, 0, -0.06)), (0.016, 0.05, 0.05))
        caixa(torre['listras'], c_ + Vector((0.0, 0, 0.051)), (0.07, 0.03, 0.002))
        cil(torre['aco'], c_ + Vector((-0.165, 0, 0)), 0.014, 0.04, Vector((1, 0, 0)), 12)
        mangueira(torre['mang_ar'], bezier(c_ + Vector((-0.185, 0, 0)), c_ + Vector((-0.27, -s * 0.02, 0.06)),
                                           Vector((-0.12, s * 0.1, 0.68)), Vector((-0.045, s * 0.045, 0.6)), 12), 0.012)
    caixa(torre['grafite'], Vector((0.14, 0.0, tz + 0.08)), (0.08, 0.1, 0.08))           # mancal do pistão de elevação
    cil(torre['olho'], Vector((0.181, 0.0, tz + 0.1)), 0.012, 0.004, Vector((1, 0, 0)), 12)
    cil(torre['led_verde'], Vector((0.181, 0.03, tz + 0.07)), 0.006, 0.004, Vector((1, 0, 0)), 8)
    pc_torre = peca('canhao_torre', torre)

    cano_ = {'aco': bmesh.new(), 'ferro': bmesh.new(), 'amarelo': bmesh.new(), 'grafite': bmesh.new(), 'escuro': bmesh.new(),
             'fuligem': bmesh.new(), 'mang_ar': bmesh.new(), 'cromo': bmesh.new()}
    # eixo local x = ao longo do cano (origem nos munhões)
    cil(cano_['aco'], Vector((L_CANO / 2 - 0.05, 0, 0)), 0.05, L_CANO + 0.1, Vector((1, 0, 0)), 28)
    cil(cano_['escuro'], Vector((L_CANO + 0.001, 0, 0)), 0.038, 0.002, Vector((1, 0, 0)), 24)
    for k in range(6):
        x_ = 0.1 + k * 0.15
        cil(cano_['ferro'], Vector((x_, 0, 0)), 0.058, 0.025, Vector((1, 0, 0)), 28)
        for j in range(8):
            a = j * PI / 4
            cil(cano_['ferro'], Vector((x_, 0.06 * math.cos(a), 0.06 * math.sin(a))), 0.005, 0.016, Vector((1, 0, 0)), 6)
    cil(cano_['grafite'], Vector((L_CANO - 0.07, 0, 0)), 0.068, 0.14, Vector((1, 0, 0)), 28)   # freio de boca
    for k in range(4):
        for s in (-1, 1):
            caixa(cano_['escuro'], Vector((L_CANO - 0.12 + k * 0.03, s * 0.066, 0)), (0.012, 0.006, 0.07))
    cil(cano_['fuligem'], Vector((L_CANO + 0.0025, 0, 0)), 0.067, 0.003, Vector((1, 0, 0)), 28)
    for k in range(10):                                                     # fuligem na boca
        a = random.uniform(0, 2 * PI)
        caixa(cano_['fuligem'], Vector((L_CANO - 0.03 - random.uniform(0, 0.08), 0.069 * math.cos(a), 0.069 * math.sin(a))),
              (random.uniform(0.03, 0.08), 0.01, 0.002), Matrix.Rotation(a + PI / 2, 3, 'X'))
    cil(cano_['amarelo'], Vector((-0.02, 0, 0)), 0.075, 0.14, Vector((1, 0, 0)), 28)      # berço nos munhões
    cil(cano_['ferro'], Vector((0, 0, 0)), 0.028, 0.27, Vector((0, 1, 0)), 20)          # eixo dos munhões
    cil(cano_['casco'] if 'casco' in cano_ else cano_.setdefault('casco', bmesh.new()), Vector((-0.17, 0, 0)), 0.08, 0.2, Vector((1, 0, 0)), 28)  # câmara de ar
    for x_ in (-0.255, -0.085):
        cil(cano_['ferro'], Vector((x_, 0, 0)), 0.088, 0.02, Vector((1, 0, 0)), 28)
        for j in range(10):
            a = j * 2 * PI / 10
            cil(cano_['ferro'], Vector((x_, 0.08 * math.cos(a), 0.08 * math.sin(a))), 0.006, 0.026, Vector((1, 0, 0)), 6)
    # válvula de disparo (bloco + solenoide) e mangueiras dos cilindros
    caixa(cano_['grafite'], Vector((-0.17, 0, -0.1)), (0.1, 0.07, 0.05))
    cil(cano_['amarelo'], Vector((-0.17, 0, -0.14)), 0.025, 0.04, Vector((0, 0, 1)), 16)
    # boca de carga: funil em cima da câmara, no eixo da torre
    BC_LOCAL = Matrix.Rotation(math.radians(ELEV), 3, 'Y') @ Vector((0, 0, 0.12))       # direção "para cima" do mundo no local
    fun_eixo = Matrix.Rotation(math.radians(ELEV), 3, 'Y') @ Vector((0, 0, 1))
    pf = Vector((0, 0, 0.09))
    pf = Matrix.Rotation(math.radians(ELEV), 3, 'Y') @ Vector((0, 0, 0.09))
    cil(cano_['amarelo'], pf, 0.034, 0.07, fun_eixo, 20)
    cil(cano_['ferro'], pf + fun_eixo * 0.05, 0.034, 0.03, fun_eixo, 20, r2=0.06)
    toro(cano_['ferro'], pf + fun_eixo * 0.066, 0.06, 0.005, 24, 6, fun_eixo.to_track_quat('Z', 'Y').to_matrix())
    cil(cano_['escuro'], pf + fun_eixo * 0.066, 0.05, 0.004, fun_eixo, 20)
    pc_cano = peca('canhao', cano_)

    cul = {'aco': bmesh.new(), 'cromo': bmesh.new(), 'amarelo': bmesh.new()}
    cil(cul['aco'], Vector((-0.01, 0, 0)), 0.07, 0.02, Vector((1, 0, 0)), 28)          # tampa da culatra
    cil(cul['cromo'], Vector((-0.06, 0, 0)), 0.012, 0.1, Vector((1, 0, 0)), 12)        # haste
    cil(cul['amarelo'], Vector((-0.15, 0, 0)), 0.026, 0.1, Vector((1, 0, 0)), 20)      # camisa (presa no suporte da câmara)
    pc_cul = peca('canhao_culatra', cul)
    # pistão de elevação: camisa articulada no mancal da torre, haste na orelha sob o cano
    pe = {'amarelo': bmesh.new(), 'ferro': bmesh.new()}
    cil(pe['amarelo'], Vector((0, 0, 0.13)), 0.026, 0.26, lados=20)
    cil(pe['ferro'], Vector((0, 0, 0.262)), 0.03, 0.01, lados=20)
    cil(pe['ferro'], Vector((0, 0, 0.0)), 0.016, 0.06, Vector((0, 1, 0)), 12)
    pel_cam = peca('pistao_elev_camisa', pe)
    ph = {'cromo': bmesh.new(), 'ferro': bmesh.new()}
    cil(ph['cromo'], Vector((0, 0, -0.13)), 0.012, 0.26, lados=12)
    cil(ph['ferro'], Vector((0, 0, 0.0)), 0.016, 0.05, Vector((0, 1, 0)), 12)
    pel_has = peca('pistao_elev_haste', ph)

    # antena
    ANT = C + Vector((0, 0, ZL1 + 0.044))
    bm = bmesh.new()
    cil(bm, ANT + Vector((0, 0, 0.12)), 0.014, 0.24, lados=12)
    caixa(bm, ANT + Vector((0, 0, 0.005)), (0.08, 0.08, 0.012))
    obj('mastro', bm, 'aco')
    an_ = {'grafite': bmesh.new(), 'olho': bmesh.new(), 'aco': bmesh.new()}
    toro(an_['aco'], Vector((0, 0, 0)), 0.07, 0.007, 32, 8)
    for k in range(3):
        a = k * 2 * PI / 3
        viga(an_['aco'], (0, 0, 0), (0.07 * math.cos(a), 0.07 * math.sin(a), 0), 0.008)
    cil(an_['grafite'], Vector((0, 0, 0.02)), 0.025, 0.05, lados=16)
    for s in (-1, 1):
        cil(an_['grafite'], Vector((s * 0.07, 0, 0.0)), 0.018, 0.04, Vector((s, 0, 0)), 16)
        cil(an_['olho'], Vector((s * 0.091, 0, 0.0)), 0.012, 0.004, Vector((s, 0, 0)), 12)
    cil(an_['aco'], Vector((0, 0, 0.09)), 0.003, 0.12, lados=6)
    antena = peca('antena', an_)

    # sonda do leitor de bioma: pistão (camisa na travessa, haste no carro) e a sonda presa no carro
    sc_cam = {'amarelo': bmesh.new(), 'ferro': bmesh.new()}
    cil(sc_cam['amarelo'], LB + Vector((0, 0, Z_LB - 0.225)), 0.022, 0.45, lados=20)
    for z_ in (Z_LB - 0.004, Z_LB - 0.446):
        cil(sc_cam['ferro'], LB + Vector((0, 0, z_)), 0.026, 0.008, lados=20)
    for mt, bm in sc_cam.items():
        suavizar(obj('pistao_sonda_' + mt, bm, mt))
    sonda = {'cromo': bmesh.new(), 'grafite': bmesh.new(), 'aco': bmesh.new(), 'olho': bmesh.new(), 'lama': bmesh.new()}
    cil(sonda['cromo'], Vector((0, 0, 0.2)), 0.009, 0.4, lados=12)                     # haste (sobe para a camisa)
    caixa(sonda['grafite'], Vector((0, 0, 0.0)), (0.2, 0.05, 0.04))                     # carro entre os montantes
    for s in (-1, 1):
        caixa(sonda['aco'], Vector((s * 0.09, 0.0, 0.0)), (0.02, 0.06, 0.05))
    toro(sonda['olho'], Vector((0, 0, -0.03)), 0.022, 0.004, 20, 6)
    cil(sonda['aco'], Vector((0, 0, -0.3)), 0.014, 0.54, lados=14)                      # sonda
    cil(sonda['aco'], Vector((0, 0, -0.6)), 0.014, 0.06, lados=14, r2=0.002)
    for z in (-0.12, -0.26, -0.4):
        toro(sonda['olho'], Vector((0, 0, z)), 0.0145, 0.002, 16, 4)
    cil(sonda['lama'], Vector((0, 0, -0.5)), 0.0155, 0.16, lados=14)                    # barro na ponta
    pc_sonda = peca('sonda', sonda)

    # aspersores, névoas, gotas, partículas
    cab_asp = []
    for i, a in enumerate(ASP):
        h = {'aco': bmesh.new(), 'cobre': bmesh.new()}
        cil(h['aco'], Vector((0, 0, 0)), 0.018, 0.03, lados=16)
        for k in range(3):
            aa = k * 2 * PI / 3
            d = Vector((math.cos(aa), math.sin(aa), -0.25))
            tubo(h['aco'], Vector((0, 0, -0.005)), d * 0.08, 0.005, 8)
            cil(h['cobre'], d * 0.08 + Vector((-math.sin(aa), math.cos(aa), 0)) * 0.006, 0.006, 0.014,
                Vector((-math.sin(aa), math.cos(aa), -0.3)), 8)
        cab_asp.append(peca('aspersor%d' % i, h))
    M['nevoa2'] = base3d.volume_mat('Névoa alta', (0.88, 0.92, 0.92), 5.0, Z_LUZ - 0.1, Z_UP + 0.25)
    nevoas = []
    for i, a in enumerate(ASP):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.3, radius2=0.05, depth=0.5,
                              matrix=Matrix.Translation((0, 0, -0.27)))
        o = obj('nevoa%d' % i, bm, 'nevoa2')
        o.location = a
        nevoas.append(o)

    def bolinha(nome, mat, r, sub=1, esticar=1.0):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        for v in bm.verts:
            v.co.z *= esticar
        return obj(nome, bm, mat)

    gotas = [(bolinha('gota', 'agua', 0.0045, 1, 1.6), i, k) for i in range(len(ASP)) for k in range(14)]
    pingos = [(bolinha('pingo', ('gota_seiva', 'gel')[i], 0.005, 1, 1.5), i, k) for i in range(2) for k in range(2)]
    bolhas = [(bolinha('bolha', 'bolha' if liq == 'seiva' else 'bolha_n', 0.004, 0), liq, k) for liq in ('seiva', 'nutriente') for k in range(4)]
    sementes = []
    for k in range(34):
        bm = bmesh.new()
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.009)
        for v in res['verts']:
            v.co.z *= 1.7
        asa = [bm.verts.new(p) for p in ((0, 0, 0.008), (0.03, 0.004, 0.02), (0.034, -0.004, 0.012))]
        bm.faces.new(asa)
        o = obj('semente', bm, 'semente')
        o.rotation_mode = 'XYZ'
        sementes.append(o)
    # sopro na boca do canhão e rastro de vapor da cápsula
    M['sopro'] = base3d.volume_mat('Sopro', (0.9, 0.92, 0.93), 7.0, -5.0, 5.0)
    sopro = []
    for k in range(3):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        o = obj('sopro%d' % k, bm, 'sopro')
        sopro.append(o)
    rastro = []
    for k in range(7):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        rastro.append(obj('rastro%d' % k, bm, 'sopro'))
    folhas_soltas = [obj('folha_solta%d' % k, (lambda b: (folha(b, Vector((0, 0, 0)), (1, 0, 0.2), 0.03, 0.012, 0.1), b)[1])(bmesh.new()), 'folha')
                     for k in range(5)]
    for o in folhas_soltas:
        o.rotation_mode = 'XYZ'
    pulsos = []
    for k in range(2):                                                      # pulso de leitura da sonda no chão
        bm = bmesh.new()
        toro(bm, Vector((0, 0, 0)), 1.0, 0.012, 64, 4, Matrix.Diagonal((1, 1, 0.15)))
        o = obj('pulso%d' % k, bm, 'olho')
        pulsos.append(o)

    # ------------------------------------------------------------------ cinemática e roteiro
    def m_torre(fr):
        return Matrix.Translation(PB) @ Matrix.Rotation(math.radians(yaw(fr)), 4, 'Z')

    def yaw(fr):
        return YAW0 + 6.0 * math.sin(2 * PI * fr)                           # mira varrendo um pouco a cada tiro

    def recuo(fr):
        if 0.78 <= fr:
            t = (fr - 0.78) / 0.15
            return -0.05 * (1 - smooth(t)) if t < 1 else 0.0
        return 0.0

    def m_cano(fr):
        return (m_torre(fr) @ Matrix.Translation((0, 0, Z_MUN)) @ Matrix.Rotation(-math.radians(ELEV), 4, 'Y')
                @ Matrix.Translation((recuo(fr), 0, 0)))

    BOCA_L = Vector((L_CANO + 0.02, 0, 0))

    def boca(fr):
        return m_cano(fr) @ BOCA_L

    def dir_cano(fr):
        return (m_cano(fr).to_3x3() @ Vector((1, 0, 0))).normalized()

    FR_TIRO = 0.78
    G = Vector((0, 0, -9.81))
    # ponte: casa (sobre a estação 0°) → desce → pega → sobe → anda → solta → volta
    Z_COL_PEGA = Z_CAP2 + 0.165
    LEV = 0.10
    PT = [(0.0, 0.0, LEV, 0), (0.31, 0.0, LEV, 0), (0.36, 0.0, 0.0, 0), (0.39, 0.0, 0.0, 1), (0.44, 0.0, LEV, 1),
          (0.58, 1.0, LEV, 1), (0.60, 1.0, LEV, 0), (0.62, 1.0, LEV, 0), (0.76, 0.0, LEV, 0), (1.0, 0.0, LEV, 0)]
    FR_PEGA, FR_SOLTA = 0.39, 0.60

    def ponte(fr):
        for (f0, s0, z0, g0), (f1, s1, z1, g1) in zip(PT, PT[1:]):
            if f0 <= fr <= f1:
                t = smooth((fr - f0) / (f1 - f0))
                return s0 + (s1 - s0) * t, z0 + (z1 - z0) * t, g0 + (g1 - g0) * t
        return PT[0][1:]

    def m_carro(fr):
        s, z, g = ponte(fr)
        p = H_PT.lerp(E_PT, s)
        return Matrix.Translation(Vector((p.x, p.y, Z_TRB))) @ ROT_PT.to_4x4()

    def m_garra(fr):
        s, z, g = ponte(fr)
        p = H_PT.lerp(E_PT, s)
        return Matrix.Translation(Vector((p.x, p.y, Z_COL_PEGA + z))) @ ROT_PT.to_4x4()

    def idade(k, fr):
        return (k + fr + 0.7) % 6.0

    def cresc(a):
        return 0.15 + 0.85 * smooth((a - 0.25) / 2.6) ** 0.8

    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        rot = ang_carrossel(fr)
        pose(carrossel, Matrix.Translation(C) @ Matrix.Rotation(math.radians(rot), 4, 'Z'), q)
        for k in range(6):
            th = 180 - 60 * k + rot
            a = idade(k, fr)
            p = pos_estacao(th)
            Rk = Matrix.Rotation(math.radians(th), 4, 'Z')
            z = Z_CAP2
            if a < 0.06:
                z = CAP_MAG.z + (Z_CAP2 - CAP_MAG.z) * (a / 0.06) ** 2
            cap_vis = a < 3.0 + (FR_PEGA - 0.3) - 0.001
            Mc = Matrix.Translation(p + Vector((0, 0, z))) @ Rk
            pose(cap_band[k], Mc, q)
            vis(cap_band[k], cap_vis, q)
            s = cresc(a)
            pose(mud_band[k], Mc @ Matrix.Translation((0, 0, 0.033)), q)
            escala(mud_band[k], s, q)
            vis(mud_band[k], cap_vis and a > 0.25, q)
        vis(mag_baixo, not (0.3 <= fr < 0.42), q)
        pose(mag_baixo, Matrix.Translation(CAP_MAG), q)
        # ponte rolante
        Mcar = m_carro(fr)
        pose(pc_carro, Mcar, q)
        Mg = m_garra(fr)
        pose(pc_garra, Mg, q)
        g = ponte(fr)[2]
        for a, dd in dedos_pt:
            rr_ = 0.046 - (0.046 - 0.039) * g
            pose(dd, Mg @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((rr_, 0, 0)), q)
        # cápsula em trânsito: na garra → cai no funil → (dentro do canhão) → voo
        Mcap_g = Mg @ Matrix.Translation((0, 0, -0.165))
        if FR_PEGA <= fr < FR_SOLTA:
            Mv = Mcap_g
            vcap = True
        elif FR_SOLTA <= fr < FR_SOLTA + 0.025:
            t = (fr - FR_SOLTA) * 4.0
            Mv = Matrix.Translation((0, 0, -0.5 * 9.81 * t * t)) @ (m_garra(FR_SOLTA) @ Matrix.Translation((0, 0, -0.165)))
            vcap = True
        elif fr >= FR_TIRO:
            t = (fr - FR_TIRO) * 4.0
            u = dir_cano(FR_TIRO)
            p0 = boca(FR_TIRO)
            v = u * V_BOCA + G * t
            p = p0 + u * V_BOCA * t + 0.5 * G * t * t
            qq = (-v).to_track_quat('Z', 'Y')
            spin = Quaternion(v.normalized(), 2 * PI * 6 * t)
            Mv = Matrix.Translation(p) @ (spin @ qq).to_matrix().to_4x4()
            vcap = True
        else:
            Mv = Matrix.Translation(PB + Vector((0, 0, Z_MUN)))
            vcap = False
        pose(cap_voo, Mv, q)
        pose(mud_voo, Mv @ Matrix.Translation((0, 0, 0.033)), q)
        vis(cap_voo + mud_voo, vcap, q)
        # canhão
        Mt = m_torre(fr)
        pose(pc_torre, Mt, q)
        Mc_ = m_cano(fr)
        pose(pc_cano, Mc_, q)
        aberta = 0.55 <= fr < 0.66
        ab = 0.0
        if 0.55 <= fr < 0.58:
            ab = smooth((fr - 0.55) / 0.03)
        elif 0.58 <= fr < 0.64:
            ab = 1.0
        elif 0.64 <= fr < 0.67:
            ab = 1 - smooth((fr - 0.64) / 0.03)
        pose(pc_cul, Mc_ @ Matrix.Translation((-0.27 - 0.06 * ab, 0, 0)), q)
        P_ARTIC = Mt @ Vector((0.14, 0.0, Z_GIRO + 0.1))
        P_ORELHA = Mc_ @ Vector((0.3, 0, -0.06))
        d_ = (P_ORELHA - P_ARTIC)
        qd = d_.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
        pose(pel_cam, Matrix.Translation(P_ARTIC) @ qd, q)
        pose(pel_has, Matrix.Translation(P_ORELHA) @ qd, q)
        # sopro na boca e rastro
        t = (fr - FR_TIRO) * 4.0
        for k, o in enumerate(sopro):
            viva = 0.0 <= t < 0.45
            tt = max(0.0, t)
            o.location = boca(FR_TIRO) + dir_cano(FR_TIRO) * (0.06 + 0.25 * tt * (1 + k * 0.6)) + Vector((0, 0, 0.12 * tt * k))
            s_ = max(0.03, (0.09 + 0.3 * min(1.0, tt * 3)) * (1 - 0.25 * k))
            o.scale = (s_, s_, s_ * 0.9)
            o.hide_render = o.hide_viewport = not viva
            for c_ in ('location', 'scale', 'hide_render', 'hide_viewport'):
                o.keyframe_insert(c_, frame=q)
        for k, o in enumerate(rastro):
            tk = t * (k + 0.5) / len(rastro)
            viva = 0.02 < t < 0.6
            u = dir_cano(FR_TIRO)
            o.location = boca(FR_TIRO) + u * V_BOCA * tk + 0.5 * G * tk * tk
            s_ = 0.035 + 0.12 * (t - tk)
            o.scale = (s_, s_, s_)
            o.hide_render = o.hide_viewport = not viva
            for c_ in ('location', 'scale', 'hide_render', 'hide_viewport'):
                o.keyframe_insert(c_, frame=q)
        for k, o in enumerate(folhas_soltas):                                # folhinhas arrancadas pelo sopro
            tt = max(0.0, t)
            viva = 0.0 < t < 0.5
            u = dir_cano(FR_TIRO)
            lat = Vector((-u.y, u.x, 0)).normalized()
            o.location = boca(FR_TIRO) + u * (0.2 + 1.5 * tt) + lat * (k - 2) * 0.12 * (0.3 + tt * 3) + Vector((0, 0, 0.05 * k - 1.5 * tt * tt))
            o.rotation_euler = (tt * 9 + k, tt * 7, k)
            o.hide_render = o.hide_viewport = not viva
            for c_ in ('location', 'rotation_euler', 'hide_render', 'hide_viewport'):
                o.keyframe_insert(c_, frame=q)
        # dosadoras
        for o, i, k in pingos:
            u = (k / 2 + fr * 6 + i * 0.25) % 1.0
            ativa = 0.38 <= fr <= 0.92
            o.location = BICOS[i] + Vector((0, 0, -0.065 - 0.04 * u * u))
            o.keyframe_insert('location', frame=q)
            o.hide_render = o.hide_viewport = not ativa
            o.keyframe_insert('hide_render', frame=q)
        for i, h in enumerate(cab_asp):
            ang = 2 * PI * 2 * fr * (1 if i == 0 else -1)
            pose(h, Matrix.Translation(ASP[i]) @ Matrix.Rotation(ang, 4, 'Z'), q)
            nevoas[i].rotation_euler = (0, 0, ang * 0.5)
            nevoas[i].keyframe_insert('rotation_euler', frame=q)
        for o, i, k in gotas:
            u = (k / 14 + fr * 3) % 1.0
            aa = k * 2 * PI / 14 * 3 + 2 * PI * 2 * fr * (1 if i == 0 else -1)
            r = 0.08 + 0.2 * u
            o.location = ASP[i] + Vector((r * math.cos(aa), r * math.sin(aa), -0.03 - 0.55 * u * u))
            o.keyframe_insert('location', frame=q)
        for o, liq, k in bolhas:
            u = (k / 4 + fr * 2) % 1.0
            v0, v1 = VISORES[liq]
            o.location = v0.lerp(v1, u) + Vector((0, 0.004 * math.sin(k * 3 + u * 9), 0))
            o.keyframe_insert('location', frame=q)
        for k, o in enumerate(sementes):                                   # sobem da matriz (embaixo) para as cápsulas
            u = (k / len(sementes) + fr) % 1.0
            th = math.radians(35 + 110 * ((k * 0.618) % 1.0)) + 0.8 * u
            r = R_T + 0.12 * (((k * 0.37) % 1.0) - 0.5) + 0.03 * math.sin(2 * PI * u * 2 + k)
            o.location = C + Vector((r * math.cos(th), r * math.sin(th), 0.6 + 0.62 * u))
            o.rotation_euler = (0.4 * math.sin(2 * PI * u + k), 0.3, 2 * PI * u * 2 + k)
            o.scale = [max(0.05, math.sin(PI * u))] * 3
            for c in ('location', 'rotation_euler', 'scale'):
                o.keyframe_insert(c, frame=q)
        pose(antena, Matrix.Translation(ANT + Vector((0, 0, 0.27))) @ Matrix.Rotation(2 * PI * fr, 4, 'Z'), q)
        # sonda: desce, lê (pulsa), sobe
        prof = smooth(fr / 0.2) * (1 - smooth((fr - 0.7) / 0.2))
        Z_SONDA = 0.5 - 0.3 * prof
        pose(pc_sonda, Matrix.Translation(LB + Vector((0, 0, Z_SONDA))), q)
        for k, o in enumerate(pulsos):
            u = (fr * 2 + k * 0.5) % 1.0
            s_ = 0.12 + 1.1 * u
            o.location = LB + Vector((0, 0, 0.004))
            o.scale = (s_, s_, 1)
            o.hide_render = o.hide_viewport = prof < 0.9
            for c in ('location', 'scale', 'hide_render', 'hide_viewport'):
                o.keyframe_insert(c, frame=q)

    # dosadoras (pistão0, pistão1)
    for i, x in enumerate(DOS_X):
        cam = {'amarelo': bmesh.new(), 'ferro': bmesh.new()}
        cil(cam['amarelo'], Vector((x, PIST_Y0 + PIST_LC / 2, Z_DOS)), 0.018, PIST_LC, Vector((0, 1, 0)), 20)
        for y in (PIST_Y0 + 0.004, PIST_Y0 + PIST_LC - 0.004):
            cil(cam['ferro'], Vector((x, y, Z_DOS)), 0.022, 0.008, Vector((0, 1, 0)), 20)
        suavizar(obj('pistao%d' % i, cam['amarelo'], 'amarelo'))
        suavizar(obj('pistao%d_tampas' % i, cam['ferro'], 'ferro'))
        has = {'cromo': bmesh.new(), 'aco': bmesh.new()}
        cil(has['cromo'], Vector((0, -0.05, 0)), 0.007, 0.1, Vector((0, 1, 0)), 12)
        caixa(has['aco'], (0, 0.004, 0), (0.05, 0.012, 0.036))
        cil(has['cromo'], Vector((0, 0.04, 0)), 0.009, 0.07, Vector((0, 1, 0)), 12)
        hp = peca('pistao%d_haste' % i, has)
        for q in range(1, QUADROS + 1):
            fr = (q - 1) / QUADROS
            ativa = 0.36 <= fr <= 0.92
            c = 0.5 - 0.5 * math.cos(2 * PI * 4 * (fr - 0.36) + i * PI) if ativa else 0.0
            pose(hp, Matrix.Translation((x, CRUZ_Y[0] + (CRUZ_Y[1] - CRUZ_Y[0]) * c, Z_DOS)), q)

    campo_forca = M['campo'].node_tree.nodes['forca'].inputs[1]
    falha = M['cresce_falha'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        campo_forca.default_value = 8.0 + 3.0 * math.sin(2 * PI * 2 * fr)
        campo_forca.keyframe_insert('default_value', frame=q)
        falha.default_value = 0.6 if q in (12, 13, 40, 71, 72, 73) else 9.0
        falha.keyframe_insert('default_value', frame=q)

    # ------------------------------------------------------------------ cena
    bm = bmesh.new()
    caixa(bm, (0, 0, -0.5), (16, 16, 1.0))
    obj('chao', bm, 'chao')
    LUZES_CRESCE = [(V(45 * k, R_LUZ * math.cos(PI / 8), Z_LUZ - 0.01), math.radians(45 * k)) for k in (0, 2, 6)]
    LUZ_CAMPO = C + Vector((0, 0.42, 0.95))
    NOME = 'viveiro_2'
    ALVO = Vector((0.6, -0.5, 1.0))
    FR_FOTO = 78                                                           # cápsula recém-saída da boca, ponte voltando
    FOTO_PERTO = (57, Vector((0.05, -2.3, 1.55)), Vector((0.55, -0.5, 1.0)), 30)
    VISTAS = [(238, 2.3, 4.9, 39)]
    print('BOCA', boca(FR_TIRO), 'DIR', dir_cano(FR_TIRO))

# ==================================================================================================================
#                                                 SEMEADOR DE BIOMA
# ==================================================================================================================
if OBRA == 'semeador':
    no = mats.no

    def peca(nome, partes):
        objs = []
        for mat, bm in partes.items():
            o = obj(nome + '_' + mat, bm, mat)
            suavizar(o)
            o.rotation_mode = 'QUATERNION'
            objs.append(o)
        return objs

    def pose(objs, Mw, q, prev={}):
        loc, rot, _ = Mw.decompose()
        for o in objs:
            k = o.name
            if k in prev:
                rot.make_compatible(prev[k])
            prev[k] = rot.copy()
            o.location = loc
            o.rotation_quaternion = rot
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)

    def vis(objs, v, q):
        for o in objs:
            o.hide_render = o.hide_viewport = not v
            o.keyframe_insert('hide_render', frame=q)
            o.keyframe_insert('hide_viewport', frame=q)

    def bolinha(nome, mat, r, sub=1, esticar=1.0):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        for v in bm.verts:
            v.co.z *= esticar
        return obj(nome, bm, mat)

    def folha(bm, base, d, comp, larg, cai=0.25):
        d = Vector(d).normalized()
        up = Vector((0, 0, 1))
        side = d.cross(up)
        side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
        rows = []
        n = 5
        for i in range(n + 1):
            t = i / n
            c = base + d * comp * t + up * (-cai * comp * t * t)
            w = larg * (math.sin(PI * t) ** 0.7 if 0 < t < 1 else 0.0)
            lift = up * 0.3 * w
            rows.append((bm.verts.new(c + side * w + lift), bm.verts.new(c), bm.verts.new(c - side * w + lift)))
        for i in range(n):
            bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
            bm.faces.new((rows[i][1], rows[i][2], rows[i + 1][2], rows[i + 1][1]))

    def muda(bmc, bmf, base, h, nf, sem):
        rr = random.Random(sem)
        base = Vector(base)
        sx, sy = rr.uniform(-0.15, 0.15) * h, rr.uniform(-0.15, 0.15) * h
        pts = [base + Vector((sx * t * t, sy * t * t, h * t)) for t in (i / 5 for i in range(6))]
        mangueira(bmc, pts, 0.002 + 0.012 * h)
        a0 = rr.uniform(0, 2 * PI)
        for j in range(nf):
            t = 0.3 + 0.7 * j / nf
            p = base + Vector((sx * t * t, sy * t * t, h * t))
            a = a0 + j * 2.4
            comp = h * (0.62 - 0.3 * t) * rr.uniform(0.85, 1.15)
            folha(bmf, p, Vector((math.cos(a), math.sin(a), 0.35 + 0.9 * t)), comp, comp * 0.36, cai=0.35 - 0.25 * t)

    # ---------------------------------------------------------------- fronteira queimado | restaurado (a mesma no shader)
    def xb(y):
        return 0.75 + 0.35 * math.sin(0.8 * y + 0.4) + 0.12 * math.sin(2.7 * y + 1.3) + 0.06 * math.sin(6.1 * y)

    INJ = [Vector((0.0, -1.27, 0)), Vector((1.27, 0.0, 0)), Vector((0.0, 1.27, 0)), Vector((-1.27, -0.12, 0))]   # S, L, N, O

    def chao_bioma_mat():
        """Chão: cinza e carvão rachados com brasas (oeste) | terra escura e verde (leste), fronteira bem marcada; lama
        pisada embaixo da máquina; a ONDA VERDE brilha na fronteira e anda em ondinhas para o lado queimado; anéis verdes
        em volta das lanças cravadas e do emissor central."""
        m = bpy.data.materials.new('Chão do bioma')
        nt = m.node_tree
        b = nt.nodes['Principled BSDF']
        geo = no(nt, 'ShaderNodeNewGeometry')
        sep = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Position'], sep.inputs[0])
        X, Y = sep.outputs['X'], sep.outputs['Y']

        def op(o, a, b_=None, c_=None):
            n = no(nt, 'ShaderNodeMath', operation=o)
            for i, v in enumerate((a, b_, c_)):
                if v is None:
                    continue
                if isinstance(v, (int, float)):
                    n.inputs[i].default_value = v
                else:
                    nt.links.new(v, n.inputs[i])
            return n.outputs[0]

        def mr(v, a, b_, c=0.0, d=1.0):
            n = no(nt, 'ShaderNodeMapRange', **{'From Min': a, 'From Max': b_, 'To Min': c, 'To Max': d})
            nt.links.new(v, n.inputs['Value'])
            return n.outputs['Result']

        def mix(f, c1, c2):
            n = no(nt, 'ShaderNodeMix', data_type='RGBA')
            nt.links.new(f, n.inputs[0])
            for i, c in ((6, c1), (7, c2)):
                if isinstance(c, tuple):
                    n.inputs[i].default_value = (*c, 1)
                else:
                    nt.links.new(c, n.inputs[i])
            return n.outputs[2]

        s1 = op('SINE', op('ADD', op('MULTIPLY', Y, 0.8), 0.4))
        s2 = op('SINE', op('ADD', op('MULTIPLY', Y, 2.7), 1.3))
        s3 = op('SINE', op('MULTIPLY', Y, 6.1))
        xb_ = op('ADD', op('ADD', op('MULTIPLY', s1, 0.35), op('MULTIPLY', s2, 0.12)), op('ADD', op('MULTIPLY', s3, 0.06), 0.75))
        d = op('SUBTRACT', X, xb_)
        n1 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.3, 'Detail': 6.0, 'Roughness': 0.6})
        nt.links.new(geo.outputs['Position'], n1.inputs['Vector'])
        n2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 8.0})
        nt.links.new(geo.outputs['Position'], n2.inputs['Vector'])
        n3 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 26.0, 'Detail': 2.0})
        nt.links.new(geo.outputs['Position'], n3.inputs['Vector'])
        vo = no(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', **{'Scale': 2.6, 'Randomness': 1.0})
        nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
        racha = op('MULTIPLY', mr(vo.outputs['Distance'], 0.0, 0.012, 1.0, 0.0), mr(n2.outputs['Fac'], 0.4, 0.55))
        # queimado
        cinza = mix(mr(n1.outputs['Fac'], 0.4, 0.58), (0.15, 0.145, 0.14), (0.02, 0.019, 0.018))
        cinza = mix(mr(n2.outputs['Fac'], 0.45, 0.7, 0.0, 0.6), cinza, (0.3, 0.29, 0.28))
        cinza = mix(mr(n3.outputs['Fac'], 0.3, 0.45, 0.4, 0.0), cinza, (0.05, 0.035, 0.022))
        cinza = mix(op('MULTIPLY', racha, 0.85), cinza, (0.008, 0.007, 0.007))
        # restaurado
        verde = mix(op('MULTIPLY', mr(n2.outputs['Fac'], 0.35, 0.65), mr(d, 0.0, 1.2, 0.25, 1.0)), (0.04, 0.027, 0.016), (0.045, 0.1, 0.018))
        verde = mix(op('MULTIPLY', mr(d, 0.3, 1.5), mr(n1.outputs['Fac'], 0.4, 0.62, 0.0, 0.7)), verde, (0.07, 0.14, 0.025))
        f_rest = mr(op('ADD', d, op('MULTIPLY', op('SUBTRACT', n3.outputs['Fac'], 0.5), 0.05)), -0.02, 0.04)
        cor = mix(f_rest, cinza, verde)
        umido = op('MULTIPLY', mr(d, -0.08, 0.0), mr(d, 0.3, 0.05))                 # faixa recém-virada: escura e úmida
        cor = mix(op('MULTIPLY', umido, 0.8), cor, (0.035, 0.024, 0.015))
        # lama embaixo da máquina
        ax = op('ABSOLUTE', X)
        ay = op('ABSOLUTE', Y)
        mq = op('MULTIPLY', mr(op('MAXIMUM', ax, ay), 1.75, 1.35), mr(n1.outputs['Fac'], 0.3, 0.55, 0.3, 0.9))
        cor = mix(mq, cor, (0.05, 0.036, 0.024))
        nt.links.new(cor, b.inputs['Base Color'])
        rgh = op('MULTIPLY_ADD', op('MAXIMUM', mq, op('MULTIPLY', umido, 0.6)), -0.6, 0.95)
        nt.links.new(rgh, b.inputs['Roughness'])
        bu = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
        nt.links.new(op('ADD', n2.outputs['Fac'], op('MULTIPLY', racha, -0.6)), bu.inputs['Height'])
        nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
        # emissão: onda verde, ondinhas, anéis das lanças e do emissor, brasas
        fase = no(nt, 'ShaderNodeValue', name='fase')
        banda = op('POWER', mr(op('ABSOLUTE', op('ADD', d, 0.03)), 0.0, 0.07, 1.0, 0.0), 2.0)
        ond = op('FRACT', op('ADD', op('MULTIPLY', d, 4.0), fase.outputs[0]))
        ond = op('MULTIPLY', op('MULTIPLY', mr(ond, 0.9, 0.98), mr(d, -1.3, -0.08)), mr(d, 0.0, -0.08))
        ond = op('MULTIPLY', ond, op('MULTIPLY', mr(n1.outputs['Fac'], 0.35, 0.6, 0.3, 1.0), 1.0))
        aneis = None
        for p in INJ + [Vector((0, 0, 0))]:
            dx = op('SUBTRACT', X, p.x)
            dy = op('SUBTRACT', Y, p.y)
            dist = op('SQRT', op('ADD', op('MULTIPLY', dx, dx), op('MULTIPLY', dy, dy)))
            raio = 1.3 if p.length < 0.1 else 0.42
            r_ = op('FRACT', op('SUBTRACT', op('MULTIPLY', dist, 1.6 / raio * 2), op('MULTIPLY', fase.outputs[0], 2.0)))
            a_ = op('MULTIPLY', mr(r_, 0.8, 0.97), mr(dist, raio, raio * 0.25))
            a_ = op('ADD', a_, op('MULTIPLY', mr(dist, raio * 0.35, 0.03), 0.8))
            aneis = a_ if aneis is None else op('MAXIMUM', aneis, a_)
        verde_e = op('ADD', op('ADD', op('MULTIPLY', banda, 7.0), op('MULTIPLY', ond, 1.4)), op('MULTIPLY', aneis, 2.2))
        brasa = op('MULTIPLY', mr(n3.outputs['Fac'], 0.7, 0.74), mr(d, -0.9, -1.4))
        brasa = op('MULTIPLY', brasa, mr(n1.outputs['Fac'], 0.55, 0.65))
        ecor = mix(mr(brasa, 0.0, 0.2), VERDE_IA, (1.0, 0.3, 0.04))
        nt.links.new(ecor, b.inputs['Emission Color'])
        nt.links.new(op('ADD', verde_e, op('MULTIPLY', brasa, 9.0)), b.inputs['Emission Strength'])
        return m, fase.outputs[0]

    chao_mat, FASE = chao_bioma_mat()

    def fumaca_grad_mat(nome, dens, z0, z1, c0=(0.012, 0.011, 0.011), c1=(0.42, 0.42, 0.43)):
        m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
        nt = m.node_tree
        vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
        sp = next(n for n in nt.nodes if n.type == 'SEPXYZ')
        t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
        nt.links.new(sp.outputs['Z'], t.inputs['Value'])
        mx = no(nt, 'ShaderNodeMix', data_type='RGBA')
        mx.inputs[6].default_value = (*c0, 1)
        mx.inputs[7].default_value = (*c1, 1)
        nt.links.new(t.outputs['Result'], mx.inputs[0])
        nt.links.new(mx.outputs[2], vol.inputs['Color'])
        return m

    def esporo_mat():
        m = base3d.volume_mat('Esporos', (0.8, 0.82, 0.45), 1.6, -5, 5)
        vol = next(n for n in m.node_tree.nodes if n.type == 'PRINCIPLED_VOLUME')
        vol.inputs['Emission Color'].default_value = (0.6, 1.0, 0.2, 1)
        vol.inputs['Emission Strength'].default_value = 0.12
        ru = next(n for n in m.node_tree.nodes if n.type == 'TEX_NOISE')
        ru.inputs['Scale'].default_value = 4.5
        return m

    M.update({
        'chao_bioma': chao_mat,
        'amarelo': encardir(mats.material('Amarelo S', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=1.0, ferrugem=0.6),
                            lama=1.0, lama_z=0.45, poeira=0.45, fuligem=0.85, fz=(0.2, 1.4), oleo=0.5),
        'amarelo2': encardir(mats.material('Amarelo trocado S', (0.55, 0.42, 0.12), 0, 0.5, desgaste=0.9, sujeira=0.95, ferrugem=0.6),
                             lama=0.9, lama_z=0.45, poeira=0.4, fuligem=0.8, fz=(0.2, 1.4)),
        'grafite': encardir(mats.material('Grafite S', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.85, sujeira=0.95, ferrugem=0.4),
                            lama=0.9, lama_z=0.45, poeira=0.55, fuligem=0.5, fz=(0.2, 1.2), oleo=0.4),
        'aco': encardir(mats.material('Aço S', (0.42, 0.43, 0.44), 1.0, 0.45, pintura=False, ferrugem=0.95, sujeira=0.9, escovado=True),
                        lama=0.9, lama_z=0.45, poeira=0.4, fuligem=0.6, fz=(0.2, 1.3), oleo=0.5),
        'estrutura': encardir(mats.material('Aço estrutural S', (0.2, 0.2, 0.2), 0.9, 0.6, pintura=False, ferrugem=1.0, sujeira=1.0),
                              lama=1.0, lama_z=0.5, poeira=0.5, fuligem=0.7, fz=(0.2, 1.3)),
        'casco': encardir(mats.material('Casco S', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=1.0),
                          lama=0.9, lama_z=0.5, poeira=0.4, fuligem=0.7, fz=(0.2, 1.4), oleo=0.4),
        'lanca': encardir(mats.material('Lança', (0.4, 0.4, 0.41), 1.0, 0.35, pintura=False, ferrugem=0.7, sujeira=0.8, escovado=True),
                          lama=1.0, lama_z=0.5),
        'lodo': liquido_mat('Lodo vivo', (0.05, 0.032, 0.018), 0.0, 0.0),
        'micelio': emissivo('Micélio', (0.45, 1.0, 0.18), 7.0, (0.6, 0.9, 0.5)),
        'cristal': emissivo('Cristal da IA', VIOLETA, 14.0, (0.3, 0.1, 0.5)),
        'po_esporo': folha_mat('Pó de esporo', (0.75, 0.7, 0.25), (0.5, 0.48, 0.12), emis=0.3),
        'carvao': encardir(mats.material('Carvão', (0.02, 0.019, 0.018), 0, 0.75, pintura=False, sujeira=0.0, desgaste=0.0), poeira=0.6),
        'brasa': emissivo('Brasa', (1.0, 0.3, 0.04), 18.0, (1.0, 0.35, 0.05)),
        'cinza_monte': mats.material('Monte de cinza', (0.36, 0.35, 0.34), 0, 0.95, pintura=False, sujeira=0.3, desgaste=0.0),
        'grama': folha_mat('Grama', (0.22, 0.55, 0.05), (0.06, 0.3, 0.03)),
        'broto': folha_mat('Broto', (0.5, 1.0, 0.15), (0.2, 0.7, 0.1), emis=0.35),
        'flor': emissivo('Flor', (1.0, 0.85, 0.3), 0.6, (1.0, 0.85, 0.35)),
        'flor_b': emissivo('Flor branca', (0.95, 0.95, 1.0), 0.4, (0.9, 0.9, 0.95)),
        'toco_queimado': encardir(mats.material('Toco queimado', (0.025, 0.02, 0.018), 0, 0.85, pintura=False, sujeira=0.4, desgaste=0.0), poeira=0.7),
        'fumaca': fumaca_grad_mat('Fumacinha', 4.0, 0.1, 1.6, (0.04, 0.04, 0.04), (0.5, 0.5, 0.5)),
        'vapor': base3d.volume_mat('Vapor', (0.9, 0.92, 0.93), 4.0, 2.0, 3.0),
        'esporos': esporo_mat(),
    })

    # ---------------------------------------------------------------- medidas
    H = 1.05                     # meia-largura do anel do chassi (linha de centro)
    ZC0, ZC1 = 0.56, 0.76        # vigas do chassi
    ZD = ZC1 + 0.012             # piso
    PE = [Vector((sx * 1.25, sy * 1.25, 0)) for sx in (-1, 1) for sy in (-1, 1)]
    R_RE = 0.42                  # reator central
    ZR0, ZR1 = ZD, 1.86
    TQ = [Vector((-0.72, -0.72, 0)), Vector((0.72, 0.72, 0))]
    SILO = Vector((-0.72, 0.72, 0))
    BOMBA = Vector((0.72, -0.72, 0))
    PORTA = Vector((-1.5, 0.38, 0.32))   # FLUIDO_ENT_O1
    ESP = [Vector((1.36, -0.78, 0)), Vector((-0.78, 1.36, 0))]
    bm_r = B('rebites', 'ferro')
    bm_pl, bm_tj = B('plaquetas', 'escuro'), B('tarjas', 'tarja')
    bm_f = B('flanges', 'ferro', True)
    bm_aco = B('aco', 'aco', True)
    bm_e = B('estrutura', 'estrutura')

    def viga_caixao(bm, a, b, w, h, mat_r=True):
        """Viga-caixão retangular (largura w, altura h) com rebites em cima."""
        a, b = Vector(a), Vector(b)
        u = (b - a).normalized()
        R = Matrix((u, Vector((0, 0, 1)).cross(u).normalized(), Vector((0, 0, 1)))).transposed()
        caixa(bm, (a + b) / 2, ((b - a).length, w, h), R)
        if mat_r:
            for s in (-1, 1):
                rebites(bm_r, a + R @ Vector((0, s * (w / 2 - 0.02), h / 2)), b + R @ Vector((0, s * (w / 2 - 0.02), h / 2)),
                        int((b - a).length / 0.09), r=0.006)

    # ---------------------------------------------------------------- chassi, piso, sapatas
    bm_am = B('chassi', 'amarelo')
    zc = (ZC0 + ZC1) / 2
    for s in (-1, 1):
        viga_caixao(bm_am, (-H - 0.08, s * H, zc), (H + 0.08, s * H, zc), 0.16, ZC1 - ZC0)
        viga_caixao(bm_am, (s * H, -H + 0.08, zc), (s * H, H - 0.08, zc), 0.16, ZC1 - ZC0)
    viga_caixao(B('chassi_cruz', 'grafite'), (-H + 0.08, 0, zc - 0.02), (H - 0.08, 0, zc - 0.02), 0.14, 0.16)
    viga_caixao(B('chassi_cruz', 'grafite'), (0, -H + 0.08, zc - 0.02), (0, -0.09, zc - 0.02), 0.14, 0.16)
    viga_caixao(B('chassi_cruz', 'grafite'), (0, 0.09, zc - 0.02), (0, H - 0.08, zc - 0.02), 0.14, 0.16)
    # piso de chapa xadrez em placas (uma faltando, uma trocada)
    for i in range(4):
        for j in range(4):
            x0, y0 = -H + i * (2 * H / 4), -H + j * (2 * H / 4)
            if (i, j) == (3, 1):
                continue                                                   # placa faltando: vê-se a viga
            mt = 'primer' if (i, j) == (0, 2) else 'casco'
            caixa_de(B('piso_' + mt, mt), (x0 + 0.006, y0 + 0.006, ZC1), (x0 + 2 * H / 4 - 0.006, y0 + 2 * H / 4 - 0.006, ZD))
            for c in ((x0 + 0.03, y0 + 0.03), (x0 + 2 * H / 4 - 0.03, y0 + 0.03), (x0 + 0.03, y0 + 2 * H / 4 - 0.03), (x0 + 2 * H / 4 - 0.03, y0 + 2 * H / 4 - 0.03)):
                cil(bm_r, Vector((c[0], c[1], ZD + 0.002)), 0.008, 0.006, lados=6)
    # listras de perigo na borda do chassi
    for s in (-1, 1):
        caixa(B('listras', 'listras'), (0, s * (H + 0.081), zc), (2 * H, 0.002, 0.06))
        caixa(B('listras', 'listras'), (s * (H + 0.081), 0, zc), (0.002, 2 * H, 0.06))
    for k, p in enumerate(PE):
        sx, sy = math.copysign(1, p.x), math.copysign(1, p.y)
        c = Vector((sx * H, sy * H, 0))
        # cotovelo do chassi até o macaco
        bm = B('sapata_braco', 'amarelo')
        caixa(bm, (c + p) / 2 + Vector((0, 0, zc)), (0.36, 0.2, ZC1 - ZC0), Matrix.Rotation(math.atan2(sy, sx), 3, 'Z'))
        cil(B('macaco', 'amarelo', True), p + Vector((0, 0, 0.62)), 0.075, 0.4, lados=24)      # camisa do macaco
        cil(bm_f, p + Vector((0, 0, 0.84)), 0.088, 0.03, lados=24)
        cil(bm_f, p + Vector((0, 0, 0.42)), 0.085, 0.02, lados=24)
        cil(B('macaco_haste', 'cromo', True), p + Vector((0, 0, 0.26)), 0.045, 0.32, lados=20)
        cil(B('sapata', 'casco', True), p + Vector((0, 0, 0.025)), 0.23, 0.07, lados=32, r2=0.17)        # meio afundada
        cil(B('sapata', 'casco', True), p + Vector((0, 0, 0.09)), 0.08, 0.06, lados=20)
        toro(B('sapata_rotula', 'ferro', True), p + Vector((0, 0, 0.12)), 0.055, 0.02, 24, 8)
        for j in range(4):
            a = j * PI / 2 + PI / 4
            caixa(B('sapata_nerv', 'casco'), p + Vector((0.11 * math.cos(a), 0.11 * math.sin(a), 0.07)), (0.07, 0.014, 0.05), Matrix.Rotation(a, 3, 'Z'))
        mancha(B('lama_furo', 'lama'), (p.x, p.y, 0), 0.32, 0.003)
        for j in range(9):                                                 # lama empurrada em volta da sapata
            a = random.uniform(0, 2 * PI)
            rr_ = random.uniform(0.24, 0.42)
            pedra(B('lama_pe', 'lama'), p + Vector((rr_ * math.cos(a), rr_ * math.sin(a), 0.0)), random.uniform(0.03, 0.07), 0.25)
        mangueira(B('mang_macaco', 'borracha', True), bezier(p + Vector((-sx * 0.07, 0, 0.76)), p + Vector((-sx * 0.2, 0, 0.85)),
                                                             c + Vector((sx * 0.05, -sy * 0.1, ZC1 + 0.05)), c + Vector((-sx * 0.1, -sy * 0.15, ZD + 0.02)), 10), 0.012)
        escorrido(B('oleo_esc', 'oleo'), p + Vector((0.0, -sy * 0.0, 0.0)) + Vector((-sx * 0.076, 0, 0.55)), (-sx, 0, 0), 0.12, 0.012)
        plaqueta(bm_pl, bm_tj, p + Vector((0, 0, 0.62)) + Vector((-sx, -sy, 0)).normalized() * 0.077, Vector((-sx, -sy, 0)), 0.05, 0.03)

    # ---------------------------------------------------------------- reator de solo vivo (centro)
    bm_rc = B('reator', 'casco', True)
    NJ = 12
    Z_JA0, Z_JA1 = 1.02, 1.62
    cil(bm_rc, Vector((0, 0, (ZR0 + Z_JA0) / 2)), R_RE, Z_JA0 - ZR0, lados=48)
    cil(bm_rc, Vector((0, 0, (Z_JA1 + ZR1) / 2)), R_RE, ZR1 - Z_JA1, lados=48)
    for k in range(NJ):                                                    # montantes entre as janelas
        a = k * 2 * PI / NJ
        caixa(B('reator_mont', 'amarelo'), Vector((R_RE * math.cos(a), R_RE * math.sin(a), (Z_JA0 + Z_JA1) / 2)), (0.05, 0.06, Z_JA1 - Z_JA0 + 0.02),
              Matrix.Rotation(a, 3, 'Z'))
        rebites(bm_r, Vector(((R_RE + 0.026) * math.cos(a), (R_RE + 0.026) * math.sin(a), Z_JA0 + 0.02)),
                Vector(((R_RE + 0.026) * math.cos(a), (R_RE + 0.026) * math.sin(a), Z_JA1 - 0.02)), 6, r=0.005)
    bm_v = B('reator_vidro', 'vidro')
    for k in range(NJ):
        a0, a1 = k * 2 * PI / NJ + 0.06, (k + 1) * 2 * PI / NJ - 0.06
        if k == 4:
            continue                                                       # janela tapada com chapa
        for z0_, z1_ in ((Z_JA0, Z_JA1),):
            n_ = 4
            vs0 = [bm_v.verts.new(Vector(((R_RE - 0.005) * math.cos(a0 + (a1 - a0) * i / n_), (R_RE - 0.005) * math.sin(a0 + (a1 - a0) * i / n_), z0_))) for i in range(n_ + 1)]
            vs1 = [bm_v.verts.new(Vector(((R_RE - 0.005) * math.cos(a0 + (a1 - a0) * i / n_), (R_RE - 0.005) * math.sin(a0 + (a1 - a0) * i / n_), z1_))) for i in range(n_ + 1)]
            for i in range(n_):
                bm_v.faces.new((vs0[i], vs0[i + 1], vs1[i + 1], vs1[i]))
    a4 = 4.5 * 2 * PI / NJ
    remendo(B('remendo_reator', 'primer'), bm_r, Vector((R_RE * math.cos(a4), R_RE * math.sin(a4), (Z_JA0 + Z_JA1) / 2)),
            (math.cos(a4), math.sin(a4), 0), 0.2, Z_JA1 - Z_JA0 + 0.04, 0.0, 0.008)
    for z in (ZR0 + 0.04, Z_JA0, Z_JA1, ZR1 - 0.03):
        toro(B('reator_cintas', 'ferro', True), Vector((0, 0, z)), R_RE + 0.008, 0.014, 64, 8)
    res = bmesh.ops.create_uvsphere(bm_rc, u_segments=48, v_segments=14, radius=R_RE,
                                    matrix=Matrix.Translation((0, 0, ZR1)) @ Matrix.Diagonal((1, 1, 0.38, 1)))
    bmesh.ops.delete(bm_rc, geom=[v for v in res['verts'] if v.co.z < ZR1 - 1e-4], context='VERTS')
    # interior: lodo escuro, micélio que brilha agarrado no vidro por dentro, bolhas
    cil(B('lodo', 'lodo', True), Vector((0, 0, (Z_JA0 + Z_JA1 - 0.06) / 2)), R_RE - 0.03, Z_JA1 - Z_JA0 - 0.06, lados=48)
    bm_mc = B('micelio', 'micelio')
    for k in range(70):
        a = random.uniform(0, 2 * PI)
        z = random.uniform(Z_JA0 + 0.02, Z_JA1 - 0.1)
        pts = []
        for j in range(7):
            a += random.uniform(-0.12, 0.12)
            z += random.uniform(-0.01, 0.05)
            pts.append(Vector(((R_RE - 0.024) * math.cos(a), (R_RE - 0.024) * math.sin(a), min(z, Z_JA1 - 0.05))))
        mangueira(bm_mc, pts, random.uniform(0.0015, 0.004))
    # tampo: agitador (fixo: motor e redutor; a parte que gira vai à parte)
    cil(B('grafite', 'grafite'), Vector((0, 0, ZR1 + 0.19)), 0.13, 0.12, lados=32)
    cil(B('motor_ag', 'amarelo2', True), Vector((0, 0, ZR1 + 0.36)), 0.1, 0.22, lados=28)
    for j in range(10):
        cil(B('aletas_motor', 'ferro', True), Vector((0, 0, ZR1 + 0.28 + 0.016 * j)), 0.112, 0.006, lados=28)
    plaqueta(bm_pl, bm_tj, Vector((0.1, 0, ZR1 + 0.4)), (1, 0, 0), 0.05, 0.035)
    # respiro com vapor
    VAP = Vector((-0.2, 0.22, ZR1 + 0.06))
    cano(bm_aco, bm_f, [Vector((-0.2, 0.22, ZR1 + 0.03)), Vector((-0.2, 0.22, ZR1 + 0.32)), Vector((-0.12, 0.22, ZR1 + 0.4))], 0.025, flange=False)
    cil(bm_f, Vector((-0.08, 0.22, ZR1 + 0.4)), 0.035, 0.03, Vector((1, 0, 0)), 16)
    plaqueta(bm_pl, bm_tj, Vector((R_RE * 0.707 + 0.003, -R_RE * 0.707 - 0.003, Z_JA0 - 0.12)), (0.707, -0.707, 0), 0.08, 0.04)
    for a in (0.5, 1.4, 3.0, 4.4, 5.6):
        escorrido(B('escorrido', 'ferrugem'), Vector(((R_RE + 0.002) * math.cos(a), (R_RE + 0.002) * math.sin(a), Z_JA0 - 0.02)),
                  (math.cos(a), math.sin(a), 0), 0.2, 0.012)
        escorrido(B('fuligem_esc', 'fuligem'), Vector(((R_RE + 0.002) * math.cos(a + 0.3), (R_RE + 0.002) * math.sin(a + 0.3), ZR1 - 0.05)),
                  (math.cos(a + 0.3), math.sin(a + 0.3), 0), 0.15, 0.02)

    # ---------------------------------------------------------------- emissor da IA embaixo (cristal que levita entre bobinas)
    for z in (ZC0 - 0.02,):
        cil(B('emissor_suporte', 'grafite'), Vector((0, 0, z - 0.02)), 0.12, 0.05, lados=24)
    for k in range(3):
        a = k * 2 * PI / 3
        viga(bm_aco, Vector((0.1 * math.cos(a), 0.1 * math.sin(a), ZC0 - 0.04)), Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.36)), 0.02)
    toro(B('bobina', 'cobre', True), Vector((0, 0, 0.36)), 0.2, 0.022, 48, 10)
    toro(B('bobina', 'cobre', True), Vector((0, 0, 0.405)), 0.17, 0.016, 48, 10)
    for k in range(3):
        a = k * 2 * PI / 3 + PI / 3
        cil(B('grafite', 'grafite'), Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.36)), 0.03, 0.06, lados=12)
        cil(B('lentes', 'cristal'), Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.329)), 0.018, 0.004, lados=12)

    # ---------------------------------------------------------------- tanques de solo vivo (SO e NE) e silo de esporos (NO)
    R_TQ = 0.27
    for i, T in enumerate(TQ):
        bm_t = B('tanque', 'casco', True)
        cil(bm_t, T + Vector((0, 0, ZD + 0.08 + 0.36)), R_TQ, 0.72, lados=36)
        res = bmesh.ops.create_uvsphere(bm_t, u_segments=36, v_segments=10, radius=R_TQ,
                                        matrix=Matrix.Translation(T + Vector((0, 0, ZD + 0.8))) @ Matrix.Diagonal((1, 1, 0.4, 1)))
        bmesh.ops.delete(bm_t, geom=[v for v in res['verts'] if v.co.z < ZD + 0.8 - 1e-4], context='VERTS')
        cil(B('tanque_base', 'amarelo'), T + Vector((0, 0, ZD + 0.04)), R_TQ + 0.02, 0.08, lados=36)
        for z in (ZD + 0.2, ZD + 0.5, ZD + 0.76):
            toro(B('tanque_cinta', 'amarelo', True), T + Vector((0, 0, z)), R_TQ + 0.005, 0.013, 48, 8)
        dv = (Vector((0, 0, 0)) - T).normalized() * -1                     # visor virado para fora
        dv = Matrix.Rotation(0.6 if i == 0 else -0.6, 3, 'Z') @ dv
        vis_ = T + dv * (R_TQ - 0.006)
        w = dv.cross(Vector((0, 0, 1)))
        caixa(B('visor_moldura', 'ferro'), vis_ + Vector((0, 0, ZD + 0.45)), (0.012, 0.11, 0.5), Matrix((dv, w, Vector((0, 0, 1)))).transposed())
        caixa(B('visor_lodo', 'lodo'), vis_ + dv * 0.008 + Vector((0, 0, ZD + 0.4)), (0.006, 0.07, 0.36), Matrix((dv, w, Vector((0, 0, 1)))).transposed())
        for k in range(6):
            zz = ZD + 0.25 + random.uniform(0, 0.3)
            p0 = vis_ + dv * 0.012 + w * random.uniform(-0.03, 0.03) + Vector((0, 0, zz))
            mangueira(B('micelio', 'micelio'), [p0, p0 + w * random.uniform(-0.02, 0.02) + Vector((0, 0, 0.04)), p0 + w * random.uniform(-0.03, 0.03) + Vector((0, 0, 0.08))], 0.002)
        caixa(B('visor_vidro', 'tubo_vidro'), vis_ + dv * 0.012 + Vector((0, 0, ZD + 0.45)), (0.003, 0.08, 0.46), Matrix((dv, w, Vector((0, 0, 1)))).transposed())
        plaqueta(bm_pl, bm_tj, T + w * R_TQ * 0.99 + Vector((0, 0, ZD + 0.62)), w, 0.07, 0.035)
        cil(bm_aco, T + Vector((0, 0, ZD + 0.94)), 0.04, 0.06, lados=16)
        caixa(B('grafite', 'grafite'), T + Vector((0, 0, ZD + 1.0)), (0.08, 0.06, 0.06))
        cil(B('led_verde', 'led_verde'), T + Vector((0.041, 0, ZD + 1.0)), 0.007, 0.004, Vector((1, 0, 0)), 8)
        for a in (0.4, 1.7, 2.9, 4.1, 5.3):
            escorrido(B('fuligem_esc', 'fuligem'), T + Vector((math.cos(a) * (R_TQ + 0.002), math.sin(a) * (R_TQ + 0.002), ZD + 0.75)), (math.cos(a), math.sin(a), 0), 0.25, 0.03)
            escorrido(B('lama_esc', 'lama'), T + Vector((math.cos(a + 0.5) * (R_TQ + 0.003), math.sin(a + 0.5) * (R_TQ + 0.003), ZD + 0.2)), (math.cos(a + 0.5), math.sin(a + 0.5), 0), 0.08, 0.04)
    remendo(B('remendo_reator', 'primer'), bm_r, TQ[0] + Vector((0.0, -R_TQ - 0.002, ZD + 0.55)), (0, -1, 0), 0.1, 0.12, 0.15, 0.005)
    # silo de esporos: pernas, funil, corpo com janela de pó, telhado, válvula rotativa embaixo
    S = SILO
    Z_S0, Z_S1 = ZD + 0.35, ZD + 0.95
    for k in range(4):
        a = PI / 4 + k * PI / 2
        viga_i(bm_e, S + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), ZD)), S + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), Z_S0 + 0.1)), 0.04, 0.035, (math.cos(a), math.sin(a), 0))
    bm_s = B('silo', 'amarelo2', True)
    cil(bm_s, S + Vector((0, 0, (Z_S0 + Z_S1) / 2)), 0.25, Z_S1 - Z_S0, lados=36)
    cil(bm_s, S + Vector((0, 0, Z_S0 - 0.1)), 0.25, 0.2, lados=36, r2=0.06)
    cil(bm_s, S + Vector((0, 0, Z_S1 + 0.07)), 0.26, 0.14, lados=36, r2=0.06)
    cil(B('grafite', 'grafite'), S + Vector((0, 0, Z_S0 - 0.24)), 0.06, 0.08, lados=20)
    cil(B('valvula_rot', 'amarelo', True), S + Vector((0, 0, Z_S0 - 0.24)), 0.035, 0.18, Vector((1, 0, 0)), 16)
    dvs = Vector((-0.6, 0.8, 0)).normalized()
    ws = dvs.cross(Vector((0, 0, 1)))
    Rs = Matrix((dvs, ws, Vector((0, 0, 1)))).transposed()
    caixa(B('visor_moldura', 'ferro'), S + dvs * 0.248 + Vector((0, 0, (Z_S0 + Z_S1) / 2)), (0.012, 0.12, 0.42), Rs)
    caixa(B('po_esporo', 'po_esporo'), S + dvs * 0.252 + Vector((0, 0, (Z_S0 + Z_S1) / 2 - 0.08)), (0.006, 0.08, 0.24), Rs)
    caixa(B('visor_vidro', 'tubo_vidro'), S + dvs * 0.258 + Vector((0, 0, (Z_S0 + Z_S1) / 2)), (0.003, 0.09, 0.38), Rs)
    for z in (Z_S0 + 0.02, Z_S1 - 0.02):
        toro(B('tanque_cinta', 'amarelo', True), S + Vector((0, 0, z)), 0.255, 0.012, 48, 8)
    caixa(B('listras', 'listras'), S + ws * 0.252 + Vector((0, 0, Z_S1 - 0.1)), (0.01, 0.16, 0.06), Rs)
    for k in range(10):                                                    # pó de esporo derramado no piso
        pedra(B('po_chao', 'po_esporo'), S + Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), ZD + 0.004)), random.uniform(0.015, 0.03), 0.25)
    # bomba e manifold (SE): recebe a água da boca O1 por baixo do piso
    caixa_de(B('bomba', 'grafite'), (BOMBA.x - 0.2, BOMBA.y - 0.15, ZD), (BOMBA.x + 0.12, BOMBA.y + 0.15, ZD + 0.28))
    cil(B('motor_bomba', 'amarelo', True), BOMBA + Vector((0.0, 0.0, ZD + 0.42)), 0.09, 0.28, Vector((1, 0, 0)), 24)
    for j in range(8):
        cil(B('aletas_motor', 'ferro', True), BOMBA + Vector((-0.1 + 0.025 * j, 0, ZD + 0.42)), 0.1, 0.006, Vector((1, 0, 0)), 24)
    cil(B('led_ambar', 'led_ambar'), BOMBA + Vector((0.121, 0.08, ZD + 0.22)), 0.008, 0.005, Vector((1, 0, 0)), 8)
    cil(B('led_verde', 'led_verde'), BOMBA + Vector((0.121, 0.05, ZD + 0.22)), 0.008, 0.005, Vector((1, 0, 0)), 8)
    plaqueta(bm_pl, bm_tj, BOMBA + Vector((0.122, -0.06, ZD + 0.12)), (1, 0, 0), 0.06, 0.04)
    escorrido(B('oleo_esc', 'oleo'), BOMBA + Vector((0.121, -0.1, ZD + 0.24)), (1, 0, 0), 0.1, 0.014)
    mancha(B('oleo_chao', 'oleo'), (BOMBA.x + 0.2, BOMBA.y - 0.05, 0), 0.1, ZD + 0.0015)
    # entrada O1: flange → por baixo do piso → sobe na bomba
    cano(bm_aco, bm_f, [PORTA, Vector((-1.25, PORTA.y, PORTA.z)), Vector((-1.25, -0.42, PORTA.z)), Vector((BOMBA.x - 0.05, -0.42, PORTA.z)),
                        Vector((BOMBA.x - 0.05, BOMBA.y + 0.15, PORTA.z)), Vector((BOMBA.x - 0.05, BOMBA.y + 0.15, ZD + 0.1))], 0.04, flange=False)
    p, u = PORTA + Vector((0.012, 0, 0)), Vector((1, 0, 0))
    tubo(bm_f, p - u * 0.01, p + u * 0.01, 0.07, 20)
    for k in range(8):
        a = k * PI / 4
        cil(bm_r, p + u * 0.012 + Vector((0, 0.058 * math.cos(a), 0.058 * math.sin(a))), 0.007, 0.01, u, 6)
    for p_ in (Vector((-1.38, PORTA.y, 0)), Vector((-0.4, -0.42, 0)), Vector((0.4, -0.42, 0))):
        caixa(bm_f, (p_.x, p_.y, (PORTA.z - 0.04) / 2), (0.05, 0.05, PORTA.z - 0.04))
        cil(B('lama_pe', 'lama'), Vector((p_.x, p_.y, 0.015)), 0.06, 0.03, lados=12)
    # bomba → reator; bomba → tanques (alimentação de água)
    cano(bm_aco, bm_f, [BOMBA + Vector((-0.2, 0.05, ZD + 0.18)), Vector((0.32, -0.32, ZD + 0.18)), Vector((0.28, -0.28, ZD + 0.18))], 0.025, flange=False)
    # cabos da IA
    bm_cab, bm_ab = B('cabos', 'cabo', True), B('abracadeiras', 'aco')

    # ---------------------------------------------------------------- injetores (pórtico fixo + pistão + carro com lança)
    Z_TOP = 1.42
    Z_CAM0 = 0.97
    INJ_DADOS = []
    for i, P in enumerate(INJ):
        n = Vector((P.x, P.y, 0)).normalized()
        if abs(P.x) > abs(P.y):
            n = Vector((math.copysign(1, P.x), 0, 0))
        else:
            n = Vector((0, math.copysign(1, P.y), 0))
        t = Vector((-n.y, n.x, 0))
        R = Matrix((n, t, Vector((0, 0, 1)))).transposed()
        INJ_DADOS.append((P, n, t, R))
        bmi = B('inj_portico', 'amarelo')
        for s in (-1, 1):
            q0 = P + t * s * 0.12
            viga_i(bm_e, q0 + Vector((0, 0, 0.25)), q0 + Vector((0, 0, Z_TOP + 0.04)), 0.06, 0.05, t)
            # mãos-francesas até a viga do chassi
            viga(bm_e, q0 + Vector((0, 0, 0.3)), q0 - n * (abs(n.dot(P)) - H - 0.08 + 0.0) + Vector((0, 0, ZC0 + 0.02)), 0.03)
            caixa(bmi, q0 - n * 0.09 + Vector((0, 0, zc)), (0.12, 0.08, ZC1 - ZC0 - 0.02), R)
        caixa(bmi, P + Vector((0, 0, Z_TOP + 0.07)), (0.12, 0.34, 0.06), R)     # travessa de cima
        caixa(bmi, P + Vector((0, 0, 0.3)), (0.1, 0.3, 0.05), R)                # travessa-guia de baixo (bucha)
        cil(bm_f, P + Vector((0, 0, 0.3)), 0.042, 0.06, lados=20)
        caixa(B('listras', 'listras'), P + n * 0.051 + Vector((0, 0, 0.3)), (0.002, 0.26, 0.04), R)
        rebites(bm_r, P + n * 0.061 + t * -0.15 + Vector((0, 0, Z_TOP + 0.07)), P + n * 0.061 + t * 0.15 + Vector((0, 0, Z_TOP + 0.07)), 6)
        # camisa do pistão presa na travessa de cima
        cil(B('inj_camisa', 'amarelo', True), P + Vector((0, 0, (Z_CAM0 + Z_TOP + 0.04) / 2)), 0.045, Z_TOP + 0.04 - Z_CAM0, lados=24)
        for z in (Z_CAM0 + 0.006, Z_TOP + 0.03):
            cil(bm_f, P + Vector((0, 0, z)), 0.052, 0.014, lados=24)
        cil(bm_aco, P + Vector((0, 0, Z_TOP + 0.13)), 0.03, 0.06, lados=16)    # tomada do lodo (haste oca)
        plaqueta(bm_pl, bm_tj, P + n * 0.046 + Vector((0, 0, Z_CAM0 + 0.3)), n, 0.04, 0.03)
        escorrido(B('oleo_esc', 'oleo'), P + n * 0.046 + Vector((0, 0, Z_CAM0 + 0.05)), n, 0.06, 0.01)
        # mangueira de lodo do tanque mais perto até a tomada
        T = TQ[0] if i in (0, 3) else TQ[1]
        pT = T + (P - T).normalized() * R_TQ * 0.98 + Vector((0, 0, ZD + 0.12))
        pT.z = ZD + 0.12
        mangueira(B('mang_lodo', 'borracha', True), bezier(pT, pT + (P - T).normalized() * 0.2 + Vector((0, 0, 0.2)),
                                                           P - n * 0.35 + Vector((0, 0, Z_TOP + 0.45)), P + Vector((0, 0, Z_TOP + 0.16)), 16), 0.022)
        cil(bm_f, pT, 0.032, 0.04, (P - T).normalized(), 16)
        # furo e lama no chão onde a lança entra
        mancha(B('lama_furo', 'lama'), (P.x, P.y, 0), 0.14, 0.004)
        for j in range(12):
            a = random.uniform(0, 2 * PI)
            rr_ = random.uniform(0.06, 0.2)
            pedra(B('lama_pe', 'lama'), P + Vector((rr_ * math.cos(a), rr_ * math.sin(a), 0.01)), random.uniform(0.012, 0.03), 0.4)
        cil(B('escuro', 'escuro'), P + Vector((0, 0, 0.006)), 0.032, 0.004, lados=16)

    # ---------------------------------------------------------------- espalhadores (lança, motor, disco)
    for i, E in enumerate(ESP):
        n = Vector((E.x, E.y, 0))
        n = Vector((math.copysign(1, n.x), 0, 0)) if abs(n.x) > abs(n.y) else Vector((0, math.copysign(1, n.y), 0))
        base_ = E - n * (abs(n.dot(E)) - H)
        viga_caixao(B('esp_braco', 'amarelo'), base_ + Vector((0, 0, ZC1 - 0.06)), E + Vector((0, 0, ZC1 - 0.06)) + n * 0.06, 0.1, 0.1)
        viga(bm_e, base_ + Vector((0, 0, ZC0 - 0.01)) - n * 0.02, E + Vector((0, 0, ZC1 - 0.11)) - n * 0.03, 0.03)
        cil(B('grafite', 'grafite'), E + Vector((0, 0, ZC1 + 0.07)), 0.065, 0.16, lados=24)          # motor em cima
        cil(B('esp_funil', 'amarelo2', True), E + Vector((0, 0, ZC1 + 0.27)), 0.12, 0.2, lados=24, r2=0.05)
        cil(B('esp_funil', 'amarelo2', True), E + Vector((0, 0, ZC1 + 0.4)), 0.12, 0.06, lados=24)
        cil(bm_aco, E + Vector((0, 0, ZC1 - 0.16)), 0.016, 0.12, lados=12)                           # eixo para o disco
        mangueira(B('mang_esporo', 'mang_verde', True), bezier(SILO + Vector((0, 0, ZD + 0.11)), SILO + Vector((0, 0, ZD + 0.02)) + (E - SILO) * 0.3,
                                                              E + Vector((0, 0, ZC1 + 0.75)) - (E - SILO).normalized() * 0.4, E + Vector((0, 0, ZC1 + 0.43)), 22), 0.02)
        plaqueta(bm_pl, bm_tj, E + n * 0.066 + Vector((0, 0, ZC1 + 0.07)), n, 0.04, 0.03)
    # ---------------------------------------------------------------- coroa de aspersores (no alto, em volta do tampo do reator)
    Z_CO = ZR1 + 0.12
    R_CO = 0.58
    toro(bm_aco, Vector((0, 0, Z_CO)), R_CO, 0.024, 64, 12)
    ASP = []
    for k in range(8):
        a = k * PI / 4 + PI / 8
        d_ = Vector((math.cos(a), math.sin(a), 0))
        p0 = d_ * R_CO + Vector((0, 0, Z_CO))
        p1 = d_ * 1.05 + Vector((0, 0, Z_CO - 0.06))
        tubo(bm_aco, p0, p1, 0.016, 12)
        curva(bm_aco, p1, 0.018)
        cil(B('grafite', 'grafite'), p1 + Vector((0, 0, -0.03)), 0.026, 0.05, lados=16)
        ASP.append((p1 + Vector((0, 0, -0.06)), d_))
        if k % 2 == 0:                                                     # escoras até o reator
            viga(bm_e, d_ * (R_RE + 0.01) + Vector((0, 0, ZR1 - 0.15)), d_ * (R_CO - 0.02) + Vector((0, 0, Z_CO - 0.02)), 0.02)
        for e_ in (-1, 1):
            pass
    cano(bm_aco, bm_f, [BOMBA + Vector((-0.08, -0.13, ZD + 0.28)), BOMBA + Vector((-0.08, -0.13, ZD + 0.75)),
                        Vector((0.42, -0.42, Z_CO)) - Vector((0.42, -0.42, 0)).normalized() * 0.0], 0.022, flange=False)
    # feixes de cabos: do nó da IA (no reator) às bobinas, ao motor e aos injetores
    caixa_de(B('no_ia', 'grafite'), (-0.2, -0.62, ZD), (0.2, -0.47, ZD + 0.36))
    for k in range(4):
        cil(B('led_verde' if k else 'led_ambar', 'led_verde' if k else 'led_ambar'), Vector((-0.12 + 0.05 * k, -0.621, ZD + 0.3)), 0.007, 0.004, Vector((0, -1, 0)), 8)
    cil(B('olho', 'olho'), Vector((0.12, -0.622, ZD + 0.29)), 0.016, 0.004, Vector((0, -1, 0)), 14)
    for k in range(5):
        caixa_de(B('aletas_no', 'aco'), (-0.17 + 0.07 * k, -0.625, ZD + 0.06), (-0.15 + 0.07 * k, -0.62, ZD + 0.22))
    plaqueta(bm_pl, bm_tj, Vector((-0.05, -0.622, ZD + 0.2)), (0, -1, 0), 0.06, 0.035)
    feixe(bm_cab, bm_ab, [Vector((0.0, -0.47, ZD + 0.2)), Vector((0.0, -0.44, ZD + 0.012)), Vector((0.0, -0.1, ZD + 0.012))],
          Vector((0, 0, 1)), n=3, r=0.008, passo=1)
    for P, n, t, R in INJ_DADOS:
        q = P - n * 0.25 + t * 0.2
        feixe(bm_cab, bm_ab, [Vector((0.15 * math.copysign(1, q.x) if abs(q.x) > 0.1 else 0.18, -0.47, ZD + 0.1)),
                              Vector((q.x * 0.5, q.y * 0.5 - 0.1, ZD + 0.012)), Vector((q.x, q.y, ZD + 0.012)), P + t * 0.12 - n * 0.03 + Vector((0, 0, ZD + 0.25))],
              Vector((0, 0, 1)), n=2, r=0.006, passo=1)

    # ---------------------------------------------------------------- chão: queimado | restaurado
    bm = bmesh.new()
    caixa(bm, (0, 0, -0.5), (30, 30, 1.0))
    obj('chao', bm, 'chao_bioma')
    RX, RY = (-4.5, 6.5), (-5.5, 6.5)
    # grama, brotos e flores do lado restaurado
    bm_g = B('grama', 'grama')
    bm_b, bm_bc = B('brotos', 'broto'), B('brotos_caule', 'caule', True)
    bm_fl, bm_fb = B('flores', 'flor'), B('flores_b', 'flor_b')
    for k in range(9000):
        x, y = random.uniform(*RX), random.uniform(*RY)
        d = x - xb(y)
        if d < 0.02 or (abs(x) < 1.58 and abs(y) < 1.58):
            continue
        dens = min(1.0, d / 0.9)
        if random.random() > 0.25 + 0.75 * dens:
            continue
        hmax = 0.03 + 0.11 * dens
        nb = random.randint(4, 8)
        for j in range(nb):
            a = random.uniform(0, 2 * PI)
            h = random.uniform(0.4, 1.0) * hmax
            p0 = Vector((x + random.uniform(-0.02, 0.02), y + random.uniform(-0.02, 0.02), 0.0))
            lean = Vector((math.cos(a), math.sin(a), 0)) * h * random.uniform(0.15, 0.45)
            w = Vector((-math.sin(a), math.cos(a), 0)) * 0.006
            vs = [bm_g.verts.new(p) for p in (p0 - w, p0 + w, p0 + lean + Vector((0, 0, h)))]
            bm_g.faces.new(vs)
        if d > 0.5 and random.random() < 0.06:
            fm = bm_fl if random.random() < 0.6 else bm_fb
            hf = random.uniform(0.06, 0.13)
            mangueira(bm_bc, [Vector((x, y, 0)), Vector((x + 0.005, y, hf))], 0.002)
            for e in range(5):
                a = e * 2 * PI / 5
                bmesh.ops.create_icosphere(fm, subdivisions=1, radius=0.009,
                                           matrix=Matrix.Translation((x + 0.005 + 0.011 * math.cos(a), y + 0.011 * math.sin(a), hf)) @ Matrix.Diagonal((1, 1, 0.35, 1)))
    for k in range(260):                                                   # brotos logo atrás da onda (e alguns já maiores)
        y = random.uniform(*RY)
        d = random.uniform(0.03, 0.45) if k < 200 else random.uniform(0.5, 3.0)
        x = xb(y) + d
        if (abs(x) < 1.6 and abs(y) < 1.6) or not (RX[0] < x < RX[1]):
            continue
        h = 0.03 + 0.05 * min(1, d / 0.45) + (random.uniform(0.05, 0.18) if k >= 200 else 0.0)
        muda(bm_bc, bm_b, Vector((x, y, 0.0)), h, 4 + int(4 * min(1, d)), 900 + k)
    # brotos-piloto em volta das lanças cravadas (do lado queimado: a restauração começa ali)
    for P in INJ:
        for k in range(10):
            a = random.uniform(0, 2 * PI)
            rr_ = random.uniform(0.2, 0.42)
            p = P + Vector((rr_ * math.cos(a), rr_ * math.sin(a), 0))
            if abs(p.x) < 1.52 and abs(p.y) < 1.52:
                continue
            muda(bm_bc, bm_b, p, random.uniform(0.02, 0.05), 4, 1300 + k + int(P.x * 10) + int(P.y * 100))
    # lado queimado: tocos, troncos caídos, restolho preto, montes de cinza, brasas, fumacinha
    bm_tc = B('tocos', 'toco_queimado', True)
    bm_br = B('brasas', 'brasa')
    TOCOS = [(-2.6, -1.2, 0.13, 0.55), (-3.4, 1.4, 0.1, 0.35), (-1.9, 2.6, 0.16, 0.7), (-2.2, -3.2, 0.09, 0.3), (-0.6, -3.4, 0.12, 0.45),
             (-3.8, -0.2, 0.08, 0.25), (-1.0, 3.6, 0.1, 0.4), (0.2, -2.6, 0.07, 0.22)]
    FUMOS = []
    for i, (x, y, r, h) in enumerate(TOCOS):
        if x - xb(y) > -0.1:
            continue
        p = Vector((x, y, 0))
        n_ = 12
        rr = random.Random(500 + i)
        aneis_ = []
        for j in range(5):
            z = h * j / 4
            ring = []
            for e in range(n_):
                a = e * 2 * PI / n_
                rad = r * (1.0 - 0.25 * j / 4) * rr.uniform(0.85, 1.1)
                zz = z if j < 4 else z - rr.uniform(0, h * 0.45)
                ring.append(bm_tc.verts.new(p + Vector((rad * math.cos(a), rad * math.sin(a), zz))))
            aneis_.append(ring)
        for j in range(4):
            for e in range(n_):
                bm_tc.faces.new((aneis_[j][e], aneis_[j][(e + 1) % n_], aneis_[j + 1][(e + 1) % n_], aneis_[j + 1][e]))
        bm_tc.faces.new(aneis_[-1])
        for j in range(4):                                                 # raízes queimadas
            a = rr.uniform(0, 2 * PI)
            raiz(bm_tc, [p + Vector((0, 0, 0.04)), p + Vector((math.cos(a) * r * 1.3, math.sin(a) * r * 1.3, 0.01)),
                         p + Vector((math.cos(a) * r * 2.4, math.sin(a) * r * 2.4, -0.02))], r * 0.35, r * 0.1, 6)
        if i in (0, 2, 4):
            for j in range(8):
                a = rr.uniform(0, 2 * PI)
                bmesh.ops.create_icosphere(bm_br, subdivisions=1, radius=rr.uniform(0.006, 0.014),
                                           matrix=Matrix.Translation(p + Vector((r * 0.75 * math.cos(a), r * 0.75 * math.sin(a), h - rr.uniform(0.0, h * 0.4)))))
            FUMOS.append(p + Vector((0, 0, h * 0.8)))
    for i, (x, y, L, a) in enumerate(((-2.9, 0.2, 1.1, 0.3), (-1.8, -2.2, 0.8, 1.9), (-3.0, 3.0, 0.9, -0.6))):
        p = Vector((x, y, 0.0))
        u = Vector((math.cos(a), math.sin(a), 0))
        raiz(bm_tc, [p, p + u * L * 0.5 + Vector((0, 0, 0.02)), p + u * L], 0.07, 0.045, 10)
        for j in range(3):
            bmesh.ops.create_icosphere(bm_br, subdivisions=1, radius=0.01, matrix=Matrix.Translation(p + u * L * random.uniform(0.2, 0.8) + Vector((0, 0, 0.06))))
    bm_rs = B('restolho', 'carvao')
    for k in range(2600):
        x, y = random.uniform(*RX), random.uniform(*RY)
        d = x - xb(y)
        if d > -0.04 or (abs(x) < 1.55 and abs(y) < 1.55):
            continue
        h = random.uniform(0.02, 0.09)
        a = random.uniform(0, 2 * PI)
        lean = Vector((math.cos(a), math.sin(a), 0)) * h * random.uniform(0.0, 0.5)
        w = Vector((-math.sin(a), math.cos(a), 0)) * 0.004
        p0 = Vector((x, y, 0.0))
        vs = [bm_rs.verts.new(p) for p in (p0 - w, p0 + w, p0 + lean + Vector((0, 0, h)))]
        bm_rs.faces.new(vs)
    bm_cz = B('cinza', 'cinza_monte')
    for k in range(120):
        x, y = random.uniform(*RX), random.uniform(*RY)
        if x - xb(y) > -0.1 or (abs(x) < 1.45 and abs(y) < 1.45):
            continue
        pedra(bm_cz, (x, y, 0.0), random.uniform(0.04, 0.16), 0.18)
    for k in range(70):
        x, y = random.uniform(*RX), random.uniform(*RY)
        if x - xb(y) > -0.5:
            continue
        bmesh.ops.create_icosphere(bm_br, subdivisions=1, radius=random.uniform(0.005, 0.012), matrix=Matrix.Translation((x, y, 0.004)))
    # cinza e lama acumulada na sapata e nos pés do pórtico (máquina trabalhando no queimado)
    for k in range(60):
        a = random.uniform(0, 2 * PI)
        rr_ = random.uniform(0.0, 1.5)
        p = Vector((rr_ * math.cos(a), rr_ * math.sin(a), 0.0))
        pedra(B('lama_pe', 'lama'), p, random.uniform(0.04, 0.12), 0.15)

    # ---------------------------------------------------------------- objetos estáticos
    for (nome, mat, liso), bm in BMS.items():
        o = obj(nome, bm, mat)
        if liso:
            suavizar(o)

    # ---------------------------------------------------------------- peças animadas
    # injetores: carro + haste + lança (a lança desce e crava; lama no pé dela)
    injetores = []
    Z_CARRO_ALTO, Z_CARRO_BAIXO = 0.92, 0.56
    L_LANCA = 0.72
    for i, (P, n, t, R) in enumerate(INJ_DADOS):
        pc = {'grafite': bmesh.new(), 'cromo': bmesh.new(), 'lanca': bmesh.new(), 'lama': bmesh.new(), 'ferro': bmesh.new(),
              'aco': bmesh.new(), 'olho': bmesh.new()}
        caixa(pc['grafite'], Vector((0, 0, 0)), (0.09, 0.2, 0.08), R)
        for s in (-1, 1):
            caixa(pc['aco'], t * s * 0.1, (0.07, 0.03, 0.1), R)               # patins nos montantes
        cil(pc['cromo'], Vector((0, 0, 0.26)), 0.02, 0.5, lados=16)             # haste (oca: lodo desce por ela)
        cil(pc['ferro'], Vector((0, 0, 0.045)), 0.04, 0.02, lados=20)
        cil(pc['lanca'], Vector((0, 0, -L_LANCA / 2 - 0.04)), 0.03, L_LANCA, lados=20)
        cil(pc['lanca'], Vector((0, 0, -L_LANCA - 0.04 - 0.06)), 0.03, 0.12, lados=20, r2=0.003)
        for j in range(4):
            zz = -L_LANCA + 0.05 + j * 0.06
            for e in range(6):
                a = e * PI / 3 + j * 0.5
                cil(pc['ferro'], Vector((0.031 * math.cos(a), 0.031 * math.sin(a), zz)), 0.006, 0.004, Vector((math.cos(a), math.sin(a), 0)), 8)
        cil(pc['lama'], Vector((0, 0, -L_LANCA + 0.08)), 0.032, 0.32, lados=20)       # barro grudado na ponta
        for z in (-0.12, -0.3):
            toro(pc['olho'], Vector((0, 0, z)), 0.031, 0.003, 20, 4)
        injetores.append((P, peca('injetor%d' % i, pc)))
    # espalhadores: disco com aletas que gira
    espalhadores = []
    for i, E in enumerate(ESP):
        dc = {'aco': bmesh.new(), 'amarelo': bmesh.new(), 'ferro': bmesh.new()}
        cil(dc['aco'], Vector((0, 0, 0)), 0.2, 0.012, lados=40)
        cil(dc['amarelo'], Vector((0, 0, 0.012)), 0.05, 0.02, lados=20)
        for k in range(6):
            a = k * PI / 3
            caixa(dc['ferro'], Vector((0.11 * math.cos(a), 0.11 * math.sin(a), 0.025)), (0.17, 0.008, 0.035), Matrix.Rotation(a + 0.4, 3, 'Z'))
        espalhadores.append((E, peca('espalhador%d' % i, dc)))
    # agitador: acoplamento com 4 braços que gira no tampo
    ag = {'aco': bmesh.new(), 'listras': bmesh.new(), 'ferro': bmesh.new()}
    cil(ag['aco'], Vector((0, 0, 0)), 0.05, 0.06, lados=24)
    for k in range(4):
        a = k * PI / 2
        caixa(ag['listras'], Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0)), (0.12, 0.03, 0.03), Matrix.Rotation(a, 3, 'Z'))
        cil(ag['ferro'], Vector((0.16 * math.cos(a), 0.16 * math.sin(a), 0)), 0.02, 0.04, lados=12)
    agitador = peca('agitador', ag)
    cristal = {'cristal': bmesh.new()}
    bmesh.ops.create_cone(cristal['cristal'], cap_ends=True, segments=4, radius1=0.07, radius2=0.0, depth=0.1, matrix=Matrix.Translation((0, 0, 0.05)))
    bmesh.ops.create_cone(cristal['cristal'], cap_ends=True, segments=4, radius1=0.07, radius2=0.0, depth=0.1,
                          matrix=Matrix.Translation((0, 0, -0.05)) @ Matrix.Rotation(PI, 4, 'X'))
    pc_cristal = peca('cristal', cristal)
    for o in pc_cristal:
        for pg in o.data.polygons:
            pg.use_smooth = False

    # partículas: sementes e nuvem de esporos dos discos, gotas dos aspersores, bolhas, fumaça, vapor
    sementes = []
    for i in range(len(ESP)):
        for k in range(36):
            bm = bmesh.new()
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.008)
            for v in res['verts']:
                v.co.z *= 1.5
            o = obj('semente', bm, 'flor' if k % 3 else 'broto')
            o.rotation_mode = 'XYZ'
            sementes.append((o, i, k, random.uniform(0, 2 * PI), random.uniform(2.2, 3.4), random.uniform(0.6, 1.6)))
    nuvens = []
    for i, E in enumerate(ESP):
        for k in range(3):
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
            nuvens.append((obj('esporos%d_%d' % (i, k), bm, 'esporos'), i, k))
    gotas = []
    for j, (p, d_) in enumerate(ASP):
        for k in range(9):
            gotas.append((bolinha('gota', 'agua', 0.006, 1, 1.4), j, k))
    nevoas = []
    for j, (p, d_) in enumerate(ASP):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.05, radius2=0.35, depth=1.2, matrix=Matrix.Translation((0, 0, -0.6)))
        o = obj('nevoa_asp%d' % j, bm, 'nevoa')
        o.location = p
        o.rotation_euler = (d_.to_track_quat('-Z', 'Y').to_euler()) if False else (0, 0, 0)
        q_ = (Vector((d_.x, d_.y, -0.9)).normalized()).to_track_quat('-Z', 'Y')
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = q_
        nevoas.append(o)
    M['nevoa'] = base3d.volume_mat('Névoa', (0.88, 0.92, 0.92), 1.6, 2.0, 0.2)
    for o in nevoas:
        o.data.materials[0] = M['nevoa']
    fumos = []
    for k, p in enumerate(FUMOS):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.06, radius2=0.25, depth=1.4, matrix=Matrix.Translation((0, 0, 0.7)))
        o = obj('fumo%d' % k, bm, 'fumaca')
        o.location = p
        fumos.append(o)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.04, radius2=0.25, depth=0.9, matrix=Matrix.Translation((0, 0, 0.45)))
    vapor = obj('vapor', bm, 'vapor')
    vapor.location = Vector((-0.05, 0.22, ZR1 + 0.42))
    vapor.rotation_euler = (0, math.radians(35), 0)
    M['vapor'] = base3d.volume_mat('Vapor', (0.9, 0.92, 0.93), 3.0, ZR1 + 0.4, ZR1 + 1.2)
    vapor.data.materials[0] = M['vapor']
    respingos = [bolinha('respingo', 'lama', random.uniform(0.008, 0.016), 1) for k in range(16)]
    vel_r = [Vector((random.uniform(-0.7, 0.7), random.uniform(-0.7, 0.7), random.uniform(0.6, 1.4))) for k in range(16)]

    # ---------------------------------------------------------------- roteiro (laço de 4 s)
    G = Vector((0, 0, -9.81))

    def descida(i, fr):
        """0 = carro em cima, 1 = lança cravada. Cada injetor crava em sequência (S, L, N, O)."""
        u = (fr - i * 0.25) % 1.0
        if u < 0.12:
            return smooth(u / 0.12) ** 1.5
        if u < 0.45:
            return 1.0
        if u < 0.62:
            return 1 - smooth((u - 0.45) / 0.17)
        return 0.0

    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        for i, (P, objs) in enumerate(injetores):
            z = Z_CARRO_ALTO + (Z_CARRO_BAIXO - Z_CARRO_ALTO) * descida(i, fr)
            pose(objs, Matrix.Translation(P + Vector((0, 0, z))), q)
        for i, (E, objs) in enumerate(espalhadores):
            pose(objs, Matrix.Translation(E + Vector((0, 0, ZC1 - 0.24))) @ Matrix.Rotation(2 * PI * 6 * fr * (1 if i else -1), 4, 'Z'), q)
        pose(agitador, Matrix.Translation((0, 0, ZR1 + 0.1)) @ Matrix.Rotation(2 * PI * fr, 4, 'Z'), q)
        pose(pc_cristal, Matrix.Translation((0, 0, 0.23 + 0.02 * math.sin(2 * PI * 2 * fr))) @ Matrix.Rotation(2 * PI * fr, 4, 'Z'), q)
        for o, i, k, a0, vel, vz in sementes:
            E = ESP[i]
            u = (k / 36 + fr * 1.5) % 1.0
            a = a0 + 2 * PI * 6 * fr * (1 if i else -1) * 0.0
            t = u * 0.55
            dirv = Vector((math.cos(a0), math.sin(a0), 0))
            p = E + Vector((0, 0, ZC1 - 0.22)) + dirv * (0.2 + vel * t) + Vector((0, 0, vz * t)) + 0.5 * G * t * t
            p.z = max(p.z, 0.008)
            o.location = p
            o.rotation_euler = (u * 20 + k, u * 13, k)
            for c in ('location', 'rotation_euler'):
                o.keyframe_insert(c, frame=q)
        for o, i, k in nuvens:
            E = ESP[i]
            u = (fr + k / 3) % 1.0
            nn = Vector((E.x, E.y, 0)).normalized()
            o.location = E + Vector((0, 0, ZC1 - 0.2 + 0.3 * u)) + nn * (0.25 + 0.6 * u) + Vector((-nn.y, nn.x, 0)) * (k - 1) * 0.25
            s_ = 0.08 + 0.22 * u
            o.scale = (s_, s_, s_ * 0.6)
            for c in ('location', 'scale'):
                o.keyframe_insert(c, frame=q)
        for o, j, k in gotas:
            p, d_ = ASP[j]
            u = (k / 9 + fr * 2) % 1.0
            t = u * 0.6
            a = math.atan2(d_.y, d_.x) + 0.25 * math.sin(k * 2.3)
            dd = Vector((math.cos(a), math.sin(a), 0))
            pp = p + dd * 2.4 * t + Vector((0, 0, 0.6 * t)) + 0.5 * G * t * t
            pp.z = max(pp.z, 0.01)
            o.location = pp
            o.keyframe_insert('location', frame=q)
        for o in fumos:
            o.rotation_euler = (0.1 * math.sin(2 * PI * fr), 0.1 * math.cos(2 * PI * fr), 2 * PI * fr)
            o.keyframe_insert('rotation_euler', frame=q)
        # respingos de lama quando a lança S crava
        u = fr % 1.0
        for k, o in enumerate(respingos):
            t = (u - 0.08) * 4.0
            viva = 0 <= t < 0.4
            tt = max(0.0, t)
            p = INJ[0] + vel_r[k] * tt + 0.5 * G * tt * tt
            p.z = max(p.z, 0.01)
            o.location = p
            o.hide_render = o.hide_viewport = not viva
            for c in ('location', 'hide_render', 'hide_viewport'):
                o.keyframe_insert(c, frame=q)
        FASE.default_value = fr
        FASE.keyframe_insert('default_value', frame=q)

    # ---------------------------------------------------------------- luzes de cena desta obra
    LUZES_CRESCE = []
    LUZ_CAMPO = None
    for p, cor, e in ((Vector((0, 0, 0.22)), (0.6, 0.35, 1.0), 25.0), (Vector((0, 0, (Z_JA0 + Z_JA1) / 2)), (0.45, 1.0, 0.2), 6.0)):
        l_ = bpy.data.lights.new('IA', 'POINT')
        l_.color = cor
        l_.energy = e
        l_.shadow_soft_size = 0.1
        lo = bpy.data.objects.new('IA', l_)
        sc.collection.objects.link(lo)
        lo.location = p
    NOME = 'semeador_bioma'
    ALVO = Vector((0.3, 0.0, 0.85))
    FR_FOTO = 9                                                            # lança S cravando, lama espirrando
    FOTO_PERTO = (13, Vector((1.25, -3.2, 1.05)), Vector((0.05, -1.05, 0.55)), 30)
    VISTAS = [(252, 3.4, 7.2, 34)]

# ------------------------------------------------------------------ luz, mundo, câmera, render
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
for i, (p, a) in enumerate(LUZES_CRESCE):
    ld = bpy.data.lights.new('Cresce%d' % i, 'AREA')
    ld.shape, ld.size, ld.size_y = 'RECTANGLE', 0.06, 0.32
    ld.color = (1.0, 0.5, 0.85)
    ld.energy = 7.0
    lo = bpy.data.objects.new('Cresce%d' % i, ld)
    sc.collection.objects.link(lo)
    lo.location = p
    lo.rotation_euler = (0, 0, a)
if LUZ_CAMPO is not None:
    lc = bpy.data.lights.new('Campo', 'POINT')
    lc.color = (0.6, 0.35, 1.0)
    lc.energy = 14.0
    lc.shadow_soft_size = 0.3
    lco = bpy.data.objects.new('Campo', lc)
    sc.collection.objects.link(lco)
    lco.location = LUZ_CAMPO
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
sc.cycles.transparent_max_bounces = 24
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


modo = ARGS[1] if len(ARGS) > 1 else 'foto'
so_uma = ARGS[2] if len(ARGS) > 2 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
    sc.frame_set(FR_FOTO)
    for i, (ang, alt, dist, lente) in enumerate(VISTAS):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        mirar(ALVO + Vector((math.cos(a) * dist, math.sin(a) * dist, alt)), ALVO, lente)
        sc.render.filepath = os.path.join(AQUI, '%s_%d.png' % (NOME, i))
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        fq, pos, alvo, lente = FOTO_PERTO
        sc.frame_set(fq)
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, '%s_perto.png' % NOME)
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in ARGS[2:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, '%s_teste.png' % NOME)
    bpy.ops.render.render(write_still=True)
print('ESTUDO ok', OBRA)
