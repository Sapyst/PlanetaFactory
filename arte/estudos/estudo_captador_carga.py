"""Estudo isolado (fora do jogo): CAPTADOR DE CARGA (`captador_carga`), 2×2 tiles.
Regra: transforma cristal lapidado + água (30 por cristal) em cristal carregado a cada raio que cai perto.
Portas (proposta, o catálogo ainda não tem o modelo): ITEM_ENT_S1 (sul, tile da direita), ITEM_SAI_O0 (oeste, tile de
baixo), FLUIDO_ENT_N0 (norte, tile da esquerda).
- Captação: mastro treliçado no canto nordeste; no topo um anel de pontas de cobre segura um cristal-guia que levita no
  campo. O cabo de descida desce a perna com abraçadeiras, passa por isoladores e pelo centelhador e chega ao banco de
  capacitores.
- Câmara: tambor octogonal blindado (chapas, cintas, colunas de canto, rebites) com janelas gradeadas. Dentro, o banho
  d'água borbulhando e o carrossel de cestos com cristais meio mergulhados; o eixo é o polo terra.
- Descarga: três eletrodos de grafite descem pelo tampo puxados por pistões (pórtico em arco); a corrente chega por
  trilhos de cobre (contato deslizante) vindos do banco de capacitores por cabos grossos.
- Fluxo: esteira de taliscas sobe do sul até a boca sudeste (cortina de tiras); o cristal cai no cesto. O cesto tomba
  na boca sudoeste e o cristal carregado (violeta, soltando faíscas) desce a bica até a esteira de saída a oeste.
  Água entra pelo cano do norte (válvula motorizada, medidor).
- Desgaste: queimados de arco, cobre oxidado (azinhavre), ferrugem escorrida, crosta de calcário, óleo dos pistões,
  lama embaixo, chapa trocada em zarcão, remendo aparafusado, fiação exposta, placa de série apagada, vapor do banho.
- Cena (laço de 4 s): eletrodos descem; o raio cai no mastro (com repiques), o pulso desce o cabo, carrega o banco,
  corre aos eletrodos e o banho acende; o cristal da vez passa de opaco a carregado; eletrodos sobem. Céu de tempestade.
Uso: blender -b --python estudo_captador_carga.py -- foto [0 perto raio]"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
Z = Vector((0, 0, 1))
random.seed(23)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
M = base3d.M
no = mats.no


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = rot @ Vector((math.cos(a), math.sin(a), 0))
        up = rot @ Z
        aneis.append([bm.verts.new(Vector(centro) + d * (R + r * math.cos(b)) + up * (r * math.sin(b)))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def varrer(bm, pts, raio, lados=12, tampas=True):
    """Tubo varrido ao longo de pts (transporte paralelo): cabos e mangueiras com curva redonda de verdade."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
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
        aneis.append([bm.verts.new(pts[i] + (e1 * math.cos(a) + e2 * math.sin(a)) * raio)
                      for a in (k * 2 * PI / lados for k in range(lados))])
    for A, B in zip(aneis, aneis[1:]):
        for j in range(lados):
            bm.faces.new((A[j], A[(j + 1) % lados], B[(j + 1) % lados], B[j]))
    if tampas:
        bm.faces.new(list(reversed(aneis[0])))
        bm.faces.new(aneis[-1])


def ruido_vec(esc=1.0):
    return Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * esc


def dirz(a):
    return Vector((math.cos(a), math.sin(a), 0))


def prisma_oct(bm, centro, ap, z0, z1):
    """Prisma octogonal com faces viradas para 0°, 45°, 90°… (apótema ap)."""
    rr = ap / math.cos(PI / 8)
    vb = [bm.verts.new(Vector((centro.x, centro.y, z0)) + dirz(PI / 8 + k * PI / 4) * rr) for k in range(8)]
    vt = [bm.verts.new(Vector((centro.x, centro.y, z1)) + dirz(PI / 8 + k * PI / 4) * rr) for k in range(8)]
    for k in range(8):
        bm.faces.new((vb[k], vb[(k + 1) % 8], vt[(k + 1) % 8], vt[k]))
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)


def base_tr(fwd):
    """Matriz com y = fwd, x lateral horizontal e z para cima (calhas, bicas)."""
    fwd = Vector(fwd).normalized()
    lat = Z.cross(fwd).normalized()
    up = lat.cross(fwd).normalized()
    if up.z < 0:
        up = -up
        lat = -lat
    return Matrix((lat, fwd, up)).transposed()


def comprimento(pts):
    return sum((b - a).length for a, b in zip(pts, pts[1:]))


def ao_longo(pts, u):
    """Ponto a u metros do começo da poligonal (e a direção do trecho)."""
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length
        if u <= L:
            return a.lerp(b, max(u, 0.0) / L), (b - a).normalized()
        u -= L
    return pts[-1].copy(), (pts[-1] - pts[-2]).normalized()


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def janela(fr, a, b):
    return a <= fr <= b


def chave(o, prop, q):
    o.keyframe_insert(prop, frame=q)


ANIM = []


def luz(nome, cor, energia, loc, raio=0.05):
    d = bpy.data.lights.new(nome, 'POINT')
    d.color = cor
    d.energy = energia
    d.shadow_soft_size = raio
    o = bpy.data.objects.new(nome, d)
    sc.collection.objects.link(o)
    o.location = loc
    return d


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def halo_mat(nome, cor, forca, alfa):
    """Halo translúcido (arco, raio): emissão mais densa no miolo do tubo."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*cor, 1)
    em.inputs['Strength'].default_value = forca
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    lw = no(nt, 'ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.5
    inv = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs['Facing'], inv.inputs[1])
    pw = no(nt, 'ShaderNodeMath', operation='POWER')
    pw.inputs[1].default_value = 2.5
    nt.links.new(inv.outputs['Value'], pw.inputs[0])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    mul.inputs[1].default_value = alfa
    nt.links.new(pw.outputs['Value'], mul.inputs[0])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(mul.outputs['Value'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def rustico(m, poeira=1.0, lama=1.0, fuligem=1.0, amassado=0.12):
    """Camada de uso: poeira no que olha para cima, lama embaixo (até ~0,25 m), fuligem e amassados."""
    nt = m.node_tree
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
    pr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.62, 'To Min': 0.2, 'To Max': 0.85 * poeira})
    nt.links.new(ru.outputs['Fac'], pr.inputs['Value'])
    fp = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(cima.outputs['Result'], fp.inputs[0])
    nt.links.new(pr.outputs['Result'], fp.inputs[1])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.06, 'From Max': 0.26, 'To Min': 1.0, 'To Max': 0.0})
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
    return m


def patina(m, quanto=0.9, escala=11.0):
    """Azinhavre: verde-azulado em manchas e nas frestas do cobre."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = next(l for l in nt.links if l.to_socket == b.inputs['Base Color'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 9.0, 'Roughness': 0.65})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    fr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.47, 'From Max': 0.6, 'To Min': 0.0, 'To Max': quanto})
    nt.links.new(ru.outputs['Fac'], fr.inputs['Value'])
    ao = no(nt, 'ShaderNodeAmbientOcclusion', samples=8)
    ao.inputs['Distance'].default_value = 0.05
    fa = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.95, 'From Max': 0.5, 'To Min': 0.0, 'To Max': quanto})
    nt.links.new(ao.outputs['AO'], fa.inputs['Value'])
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fr.outputs['Result'], mx.inputs[0])
    nt.links.new(fa.outputs['Result'], mx.inputs[1])
    c = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c.inputs[7].default_value = (0.16, 0.38, 0.30, 1)
    nt.links.new(mx.outputs['Value'], c.inputs[0])
    nt.links.new(lk.from_socket, c.inputs[6])
    nt.links.new(c.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMix', data_type='FLOAT')
    rg.inputs[2].default_value = 0.32
    rg.inputs[3].default_value = 0.85
    nt.links.new(mx.outputs['Value'], rg.inputs[0])
    nt.links.new(rg.outputs[0], b.inputs['Roughness'])
    mt = no(nt, 'ShaderNodeMix', data_type='FLOAT')
    mt.inputs[2].default_value = 1.0
    mt.inputs[3].default_value = 0.0
    nt.links.new(mx.outputs['Value'], mt.inputs[0])
    nt.links.new(mt.outputs[0], b.inputs['Metallic'])
    return m


def vidro_mat(nome='Vidro'):
    """Vidro de janela blindada: fino (IOR 1), um pouco de reflexo, encardido e com respingos de calcário embaixo."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Coat Weight'].default_value = 0.35
    b.inputs['Coat Roughness'].default_value = 0.05
    b.inputs['Coat IOR'].default_value = 1.5
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 26.0, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.3, 'To Min': 0.1, 'To Max': 0.8})
    nt.links.new(sep.outputs['Z'], alt.inputs['Value'])
    enc = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(alt.outputs['Result'], enc.inputs[0])
    nt.links.new(ru.outputs['Fac'], enc.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.95, 0.97, 0.96, 1)
    cor.inputs[7].default_value = (0.45, 0.42, 0.33, 1)
    nt.links.new(enc.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.02, 'To Max': 0.45})
    nt.links.new(enc.outputs['Value'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    return m


def agua_banho_mat():
    """Banho: água turva esverdeada (volume) que acende em violeta por dentro quando a descarga passa."""
    m = bpy.data.materials.new('Banho')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.88, 0.86, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['IOR'].default_value = 1.33
    tc = no(nt, 'ShaderNodeTexCoord')
    ondas = no(nt, 'ShaderNodeTexNoise', **{'Scale': 22.0, 'Detail': 4.0})
    ondas.noise_dimensions = '4D'
    ondas.name = 'ondas'
    nt.links.new(tc.outputs['Object'], ondas.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    nt.links.new(ondas.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.name = 'vol'
    vol.inputs['Color'].default_value = (0.35, 0.5, 0.42, 1)
    vol.inputs['Density'].default_value = 0.7
    vol.inputs['Absorption Color'].default_value = (0.35, 0.5, 0.4, 1)
    vol.inputs['Emission Color'].default_value = (0.55, 0.22, 1.0, 1)
    vol.inputs['Emission Strength'].default_value = 0.0
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    return m


def bolha_mat():
    m = bpy.data.materials.new('Bolha')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.0
    b.inputs['IOR'].default_value = 0.75
    return m


def cristal_mat():
    """Um material para todos os cristais: cor do objeto R = carga (0 opaco, 1 carregado), G = clarão do banho."""
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['IOR'].default_value = 1.55
    oi = no(nt, 'ShaderNodeObjectInfo')
    sep = no(nt, 'ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sep.inputs[0])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 34.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    # opaco: leitoso cinza-lilás, fosco, com nuvens; carregado: violeta translúcido
    turvo = no(nt, 'ShaderNodeMix', data_type='RGBA')
    turvo.inputs[6].default_value = (0.36, 0.33, 0.40, 1)
    turvo.inputs[7].default_value = (0.20, 0.18, 0.24, 1)
    nt.links.new(ru.outputs['Fac'], turvo.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[7].default_value = (0.30, 0.06, 0.75, 1)
    nt.links.new(sep.outputs['Red'], cor.inputs[0])
    nt.links.new(turvo.outputs[2], cor.inputs[6])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.55, 'To Max': 0.12})
    nt.links.new(sep.outputs['Red'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    tw = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.15, 'To Max': 0.75})
    nt.links.new(sep.outputs['Red'], tw.inputs['Value'])
    nt.links.new(tw.outputs['Result'], b.inputs['Transmission Weight'])
    b.inputs['Emission Color'].default_value = (0.5, 0.16, 1.0, 1)
    er = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    er.inputs[1].default_value = 7.0
    nt.links.new(sep.outputs['Red'], er.inputs[0])
    eg = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    eg.inputs[1].default_value = 22.0
    nt.links.new(sep.outputs['Green'], eg.inputs[0])
    es = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(er.outputs['Value'], es.inputs[0])
    nt.links.new(eg.outputs['Value'], es.inputs[1])
    # veios internos brilham mais que a casca
    ve = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.7, 'To Min': 0.45, 'To Max': 1.4})
    nt.links.new(ru.outputs['Fac'], ve.inputs['Value'])
    ef = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(es.outputs['Value'], ef.inputs[0])
    nt.links.new(ve.outputs['Result'], ef.inputs[1])
    nt.links.new(ef.outputs['Value'], b.inputs['Emission Strength'])
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 60.0})
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def terra_mat():
    """Chão de terra molhada da tempestade: lama escura, pedrisco e poças rasas brilhando."""
    m = mats.material('Terra', (0.11, 0.085, 0.06), 0, 0.75, pintura=False, sujeira=0.2, desgaste=0.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.9, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    poca = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.56, 'From Max': 0.6, 'To Min': 0.75, 'To Max': 0.04})
    nt.links.new(ru.outputs['Fac'], poca.inputs['Value'])
    nt.links.new(poca.outputs['Result'], b.inputs['Roughness'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], fino.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.3})
    nt.links.new(fino.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def ceramica_mat():
    m = bpy.data.materials.new('Cerâmica')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.33, 0.12, 0.05, 1)
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Coat Weight'].default_value = 0.6
    return rustico(m, poeira=0.8, lama=0.0, fuligem=1.3, amassado=0.0)


VIOLETA = (0.55, 0.2, 1.0)
M.update({
    'amarelo': rustico(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.85)),
    'grafite': rustico(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.75, sujeira=0.8, ferrugem=0.5)),
    'zarcao': rustico(mats.material('Zarcão', (0.36, 0.08, 0.04), 0, 0.6, desgaste=0.6, sujeira=0.8, ferrugem=0.4)),
    'aco': rustico(mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True), amassado=0.05),
    'casco': rustico(mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0)),
    'queimado': mats.material('Queimado', (0.13, 0.11, 0.12), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'ferro': rustico(mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9), amassado=0.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.4),
    'cobre': patina(mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.7), 0.55),
    'cobre_ox': patina(mats.material('Cobre oxidado', (0.62, 0.32, 0.18), 1.0, 0.4, pintura=False, sujeira=0.9), 0.95, 7.0),
    'grafite_el': mats.material('Grafite do eletrodo', (0.05, 0.05, 0.055), 0.3, 0.55, pintura=False, sujeira=0.6),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.7, desgaste=0.0),
    'concreto': rustico(mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0), amassado=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.12, 0.08, 0.045), 0, 0.55, pintura=False, sujeira=0.2, desgaste=0.0),
    'ferrugem': mats.material('Ferrugem escorrida', (0.30, 0.11, 0.035), 0, 0.85, pintura=False, sujeira=0.3, desgaste=0.0),
    'calcario': mats.material('Calcário', (0.62, 0.6, 0.55), 0, 0.95, pintura=False, sujeira=0.5, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.012, 0.011, 0.011), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'fio_verm': mats.material('Fio vermelho', (0.4, 0.03, 0.02), 0, 0.5, pintura=False, sujeira=0.5),
    'fio_azul': mats.material('Fio azul', (0.03, 0.08, 0.35), 0, 0.5, pintura=False, sujeira=0.5),
    'fio_amar': mats.material('Fio amarelo', (0.55, 0.42, 0.03), 0, 0.5, pintura=False, sujeira=0.5),
    'ceramica': ceramica_mat(),
    'terra': terra_mat(),
    'vidro': vidro_mat(),
    'banho': agua_banho_mat(),
    'bolha': bolha_mat(),
    'cristal': cristal_mat(),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'led_violeta': emissivo('LED violeta', VIOLETA, 8.0),
    'led_apagado': mats.material('LED apagado', (0.05, 0.03, 0.07), 0, 0.3, pintura=False, sujeira=0.3),
    'olho': emissivo('Olho da IA', (0.6, 0.25, 1.0), 6.0),
    'arco': emissivo('Arco', (0.85, 0.72, 1.0), 30.0),
    'arco_brilho': halo_mat('Halo do arco', (0.55, 0.2, 1.0), 6.0, 0.3),
    'raio': emissivo('Raio', (0.9, 0.85, 1.0), 120.0),
    'raio_brilho': halo_mat('Halo do raio', (0.6, 0.35, 1.0), 14.0, 0.35),
    'pulso': emissivo('Pulso', (0.8, 0.55, 1.0), 60.0),
    'faisca': emissivo('Faísca', (0.85, 0.7, 1.0), 50.0),
    'faisca_q': emissivo('Faísca quente', (1.0, 0.6, 0.25), 40.0),
    'vapor': base3d.volume_mat('Vapor', (0.85, 0.86, 0.88), 2.2, 1.1, 2.6),
    'vapor_dentro': base3d.volume_mat('Vapor do banho', (0.85, 0.86, 0.88), 0.35, 0.5, 0.95),
    'vapor_vaza': base3d.volume_mat('Vapor vazando', (0.85, 0.86, 0.88), 1.6, 0.9, 1.7),
})

# ------------------------------------------------------------------ medidas
C = Vector((-0.05, 0.0, 0.0))           # eixo da câmara
R_OUT, TH = 0.5, 0.05                   # apótema externo e espessura da blindagem
R_IN = R_OUT - TH
Z_BASE, Z_TOP, Z_AGUA = 0.14, 1.0, 0.5
Z_TAMPA = Z_TOP + 0.05
RC = 0.24                               # raio do carrossel (centro dos cestos)
Z_CESTO = 0.455                         # fundo do cesto
Z_CRI = 0.505                           # centro do cristal no cesto (meio mergulhado)
ANG_EL = [math.radians(a) for a in (95, 120, 145)]
R_EL, R_TRILHO = 0.38, 0.45
Z_VIGA = 1.8
MASTRO = Vector((0.74, 0.76, 0.0))
Z_MASTRO = 3.05
CAPS_Y = (-0.16, 0.08, 0.32)
CAP_X = 0.77
TAN8 = math.tan(PI / 8)

FACE_ENT, FACE_SAI = 7, 5               # sudeste (entrada) e sudoeste (saída)
ABERT = {i: (-0.13, 0.13, 0.3, 0.78) for i in range(8)}
ABERT[FACE_ENT] = (-0.1, 0.1, 0.56, 0.8)
ABERT[FACE_SAI] = (-0.1, 0.1, 0.5, 0.76)
ABERT[2] = (-0.13, 0.13, 0.36, 0.78)


def ponto_face(i, u, z, r=R_OUT):
    a = i * PI / 4
    return C + dirz(a) * r + dirz(a + PI / 2) * u + Z * z


def rot_face(i):
    return Matrix.Rotation(i * PI / 4, 3, 'Z')


# ------------------------------------------------------------------ laje, base e chão
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()
for y in (-0.985, 0.97):
    caixa_de(bm, (-0.985, y, 0.0), (0.985, y + 0.015, 0.08))
obj('laje_listras', bm, 'listras')
bm = bmesh.new()
prisma_oct(bm, C, R_OUT + 0.05, 0.08, Z_BASE)
obj('base_camara', bm, 'ferro')
bm = bmesh.new()
for k in range(8):                                                       # chumbadores da base
    for s in (-1, 1):
        p = ponto_face(k, s * 0.14, Z_BASE + 0.008, R_OUT + 0.03)
        cil(bm, p, 0.012, 0.022, lados=6)
obj('chumbadores', bm, 'aco')

# ------------------------------------------------------------------ câmara blindada: chapas com janelas, colunas, cintas
bm_g, bm_z, bm_vid = bmesh.new(), bmesh.new(), bmesh.new()
for i in range(8):
    u0, u1, za, zb = ABERT[i]
    Rm = R_OUT - TH / 2
    W2 = Rm * TAN8 + 0.004
    rects = [(-W2, W2, Z_BASE, za), (-W2, W2, zb, Z_TOP), (-W2, u0, za, zb), (u1, W2, za, zb)]
    alvo = bm_z if i == 6 else bm_g                                        # chapa sul trocada (zarcão)
    for (a0, a1, z0, z1) in rects:
        c = ponto_face(i, (a0 + a1) / 2, (z0 + z1) / 2, Rm)
        caixa(alvo, c, (TH, a1 - a0, z1 - z0), rot_face(i))
    if i not in (FACE_ENT, FACE_SAI):
        caixa(bm_vid, ponto_face(i, (u0 + u1) / 2, (za + zb) / 2, Rm), (0.008, u1 - u0, zb - za), rot_face(i))
obj('camara_chapas', bm_g, 'grafite')
obj('camara_chapa_trocada', bm_z, 'zarcao')
obj('janelas_vidro', bm_vid, 'vidro')

bm, br, bgr = bmesh.new(), bmesh.new(), bmesh.new()
for i in range(8):
    u0, u1, za, zb = ABERT[i]
    e = 0.035
    rf = rot_face(i)
    for (cu, cz, su, sz) in (((u0 + u1) / 2, za - e / 2, u1 - u0 + 2 * e, e), ((u0 + u1) / 2, zb + e / 2, u1 - u0 + 2 * e, e),
                             (u0 - e / 2, (za + zb) / 2, e, zb - za), (u1 + e / 2, (za + zb) / 2, e, zb - za)):
        caixa(bm, ponto_face(i, cu, cz, R_OUT + 0.012), (0.024, su, sz), rf)      # moldura aparafusada
    for (cu, cz) in ((u0 - e / 2, za - e / 2), (u1 + e / 2, za - e / 2), (u0 - e / 2, zb + e / 2), (u1 + e / 2, zb + e / 2),
                     (u0 - e / 2, (za + zb) / 2), (u1 + e / 2, (za + zb) / 2)):
        cil(br, ponto_face(i, cu, cz, R_OUT + 0.026), 0.007, 0.01, dirz(i * PI / 4), lados=6)
    if i not in (FACE_ENT, FACE_SAI):                                      # grade de proteção: duas barras
        for f in (0.33, 0.67):
            uu = u0 + (u1 - u0) * f
            cil(bgr, ponto_face(i, uu, (za + zb) / 2, R_OUT + 0.03), 0.009, zb - za + 0.03, lados=8)
obj('molduras', bm, 'ferro')
obj('rebites_janela', br, 'aco')
suavizar(obj('grades', bgr, 'aco'))

bm = bmesh.new()
for k in range(8):                                                       # colunas de canto (H) nas emendas
    a = PI / 8 + k * PI / 4
    p = C + dirz(a) * (R_OUT / math.cos(PI / 8) - 0.005)
    caixa(bm, Vector((p.x, p.y, (0.1 + Z_TOP + 0.03) / 2)), (0.07, 0.05, Z_TOP + 0.03 - 0.1), Matrix.Rotation(a, 3, 'Z'))
obj('colunas', bm, 'amarelo')
bm, br = bmesh.new(), bmesh.new()
for zc in (0.2, 0.9):                                                    # cintas horizontais com rebites
    for i in range(8):
        Wc = (R_OUT + 0.01) * TAN8 * 2
        caixa(bm, ponto_face(i, 0, zc, R_OUT + 0.008), (0.016, Wc, 0.06), rot_face(i))
        for s in (-1, 1):
            for uu in (0.06, 0.12):
                cil(br, ponto_face(i, s * uu, zc, R_OUT + 0.018), 0.006, 0.008, dirz(i * PI / 4), lados=6)
obj('cintas', bm, 'ferro')
obj('rebites', br, 'aco')

bm, br = bmesh.new(), bmesh.new()                                         # remendo aparafusado na chapa sul (amassado)
p_rem = ponto_face(6, -0.06, 0.963, R_OUT + 0.004)
caixa(bm, p_rem, (0.008, 0.12, 0.055), rot_face(6) @ Matrix.Rotation(0.04, 3, 'X'))
for du in (-0.05, 0.05):
    for dz in (-0.018, 0.018):
        cil(br, p_rem + dirz(6 * PI / 4 + PI / 2) * du + Z * dz + dirz(6 * PI / 4) * 0.006, 0.006, 0.008, dirz(6 * PI / 4), lados=6)
obj('remendo', bm, 'casco')
obj('remendo_parafusos', br, 'cromo')

# ------------------------------------------------------------------ tampo: anel parafusado, buchas e sujeira
bm = bmesh.new()
prisma_oct(bm, C, R_OUT + 0.035, Z_TOP, Z_TAMPA)
obj('tampo', bm, 'casco')
bm = bmesh.new()
for k in range(32):
    a = k * 2 * PI / 32
    cil(bm, C + dirz(a) * (R_OUT + 0.0) + Z * (Z_TAMPA + 0.008), 0.009, 0.016, lados=6)
obj('tampo_parafusos', bm, 'aco')
bm = bmesh.new()
for a in ANG_EL:                                                          # buchas dos eletrodos (encaixe real no tampo)
    p = C + dirz(a) * R_EL
    cil(bm, p + Z * (Z_TAMPA + 0.03), 0.048, 0.06, lados=16)
    cil(bm, p + Z * (Z_TAMPA + 0.065), 0.036, 0.015, lados=16)
cil(bm, C + Z * (Z_TAMPA + 0.025), 0.06, 0.05, lados=16)                 # bucha do eixo
obj('buchas', bm, 'ceramica')
bm = bmesh.new()                                                          # queimados de arco em volta das buchas
for a in ANG_EL:
    p = C + dirz(a) * R_EL
    mancha(bm, (p.x, p.y), random.uniform(0.07, 0.1), Z_TAMPA + 0.0015)
obj('tampo_queimado', bm, 'fuligem')

# ------------------------------------------------------------------ banho: água, fundo, aspersores e bolhas
bm = bmesh.new()
prisma_oct(bm, C, R_IN - 0.002, Z_BASE + 0.001, Z_AGUA)
banho = obj('banho', bm, 'banho')
bm = bmesh.new()
for k in range(6):                                                        # aspersores de ar no fundo
    a = k * PI / 3 + 0.3
    tubo(bm, C + dirz(a) * 0.08 + Z * (Z_BASE + 0.02), C + dirz(a) * 0.4 + Z * (Z_BASE + 0.02), 0.012, 8)
toro(bm, C + Z * (Z_BASE + 0.02), 0.08, 0.014, 24, 8)
obj('aspersores', bm, 'cobre_ox')
bolhas = []
for k in range(46):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    o = obj('bolha', bm, 'bolha')
    a = random.uniform(0, 2 * PI)
    if k < 18:                                                            # bolhas grossas nos eletrodos
        ae = random.choice(ANG_EL)
        base = C + dirz(ae) * R_EL + dirz(random.uniform(0, 2 * PI)) * random.uniform(0.02, 0.05)
    else:
        base = C + dirz(a) * random.uniform(0.1, 0.4)
    bolhas.append((o, base, random.random(), random.uniform(0.005, 0.012), random.uniform(1.5, 3.0)))


def anim_bolhas(q, fr):
    for o, base, fase, r, vel in bolhas:
        u = (fase + fr * vel) % 1.0
        z = Z_BASE + 0.03 + (Z_AGUA - Z_BASE - 0.03) * u
        o.location = base + Z * z + Vector((0.01 * math.sin(7 * u + fase * 9), 0.01 * math.cos(5 * u), 0))
        s = r * (0.6 + 0.6 * u)
        o.scale = (s, s, s * 0.85)
        chave(o, 'location', q)
        chave(o, 'scale', q)
ANIM.append(anim_bolhas)

# ------------------------------------------------------------------ carrossel: eixo terra, raios, cestos que tombam
Z_RAIOS = 0.74
bm = bmesh.new()
cil(bm, C + Z * ((Z_BASE + Z_TAMPA + 0.18) / 2), 0.03, Z_TAMPA + 0.18 - Z_BASE, lados=16)
obj('eixo', bm, 'cromo')
bm = bmesh.new()
cil(bm, C + Z * (Z_BASE + 0.03), 0.07, 0.06, lados=16)                   # mancal de fundo (terra do banho)
obj('mancal_fundo', bm, 'cobre_ox')
rotor = bpy.data.objects.new('carrossel', None)
sc.collection.objects.link(rotor)
rotor.location = C
bm, bc = bmesh.new(), bmesh.new()
cil(bm, Z * Z_RAIOS, 0.06, 0.07, lados=16)                                # cubo
for k in range(8):
    a = -PI / 4 + k * PI / 4
    d, t = dirz(a), dirz(a + PI / 2)
    piv = d * (RC - 0.05) - t * 0.03
    viga(bm, Z * Z_RAIOS + d * 0.05, Z * Z_RAIOS + d * (RC - 0.05) - t * 0.03, 0.018)   # raio do carrossel
    viga(bm, Z * Z_RAIOS + d * (RC - 0.05) - t * 0.03, piv + Z * (Z_CESTO + 0.06), 0.012)  # haste (pendurada)
obj('carrossel_raios', bm, 'aco', rotor)
cestos = []
for k in range(8):
    a = -PI / 4 + k * PI / 4
    d, t = dirz(a), dirz(a + PI / 2)
    piv = bpy.data.objects.new('cesto_pivo', None)
    sc.collection.objects.link(piv)
    piv.parent = rotor
    piv.location = d * (RC - 0.05) + Z * (Z_CESTO + 0.06) - t * 0.03
    piv.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cc = d * 0.05 + t * 0.03 - Z * 0.06                                   # centro do fundo do cesto (local ao pivô)
    toro(bm, cc, 0.048, 0.005, 20, 6)
    viga(bm, cc - d * 0.048, cc + d * 0.048, 0.008)
    viga(bm, cc - t * 0.048, cc + t * 0.048, 0.008)
    for s in (-1, 1):                                                     # costas do cesto (lado de dentro)
        q0 = cc + (-d * math.cos(0.6) + t * s * math.sin(0.6)) * 0.048
        viga(bm, q0, q0 + Z * 0.08, 0.007)
    toro(bm, cc + Z * 0.08, 0.048, 0.004, 20, 6)
    viga(bm, Vector((0, 0, 0)), cc - d * 0.048 + Z * 0.08, 0.01)          # braço do pivô às costas
    viga(bm, Vector((0, 0, 0)), cc - d * 0.048, 0.01)
    obj('cesto', bm, 'cobre_ox', piv)
    cestos.append((piv, a, d, t))


def ang_slot(j, fr):
    return -PI / 4 + (j + fr) * PI / 4


def tombo(a):
    """Cesto tomba para fora ao passar pela boca sudoeste (225°–241°), já erguido pelo came."""
    g = ((math.degrees(a) - 225.0) % 360.0)
    if g < 16.0:
        return math.sin(PI * g / 16.0) * math.radians(38)
    return 0.0


def ergue(a):
    """Came ergue o cesto (colar desliza na haste) de 200° a 220°, segura até 240° e baixa até 260°."""
    g = math.degrees(a) % 360.0
    if 200 <= g < 220:
        return suave((g - 200) / 20)
    if 220 <= g < 240:
        return 1.0
    if 240 <= g < 260:
        return 1.0 - suave((g - 240) / 20)
    return 0.0


LIFT = 0.1


def anim_carrossel(q, fr):
    rotor.rotation_euler = (0, 0, fr * PI / 4)
    chave(rotor, 'rotation_euler', q)
    for piv, a0, d, t in cestos:
        a = a0 + fr * PI / 4
        piv.rotation_quaternion = Quaternion(Vector((-math.sin(a0), math.cos(a0), 0)), tombo(a))
        piv.location = d * (RC - 0.05) + Z * (Z_CESTO + 0.06 + LIFT * ergue(a)) - t * 0.03
        chave(piv, 'rotation_quaternion', q)
        chave(piv, 'location', q)
ANIM.append(anim_carrossel)
bm = bmesh.new()
cam_pts = []
for k in range(25):
    g = 190 + k * 75 / 24
    cam_pts.append(C + dirz(math.radians(g)) * (RC + 0.055) + Z * (Z_CESTO - 0.012 + LIFT * ergue(math.radians(g))))
varrer(bm, cam_pts, 0.008, 8)
for g in (195, 230, 262):                                                 # mãos do came presas na parede
    p = C + dirz(math.radians(g)) * (RC + 0.055) + Z * (Z_CESTO - 0.012 + LIFT * ergue(math.radians(g)))
    viga(bm, p, C + dirz(math.radians(g)) * (R_IN + 0.005) + Z * (p.z + 0.06), 0.01)
obj('came', bm, 'aco')

# ------------------------------------------------------------------ cristais: malha lapidada
def cristal_geo(bm, r=0.04, h=0.062):
    g = [bm.verts.new(dirz(k * PI / 3) * r) for k in range(6)]
    tb = [bm.verts.new(dirz(k * PI / 3 + PI / 6) * r * 0.55 + Z * h * 0.45) for k in range(6)]
    ap = bm.verts.new(-Z * h)
    for k in range(6):
        bm.faces.new((g[k], g[(k + 1) % 6], tb[k]))
        bm.faces.new((tb[k], g[(k + 1) % 6], tb[(k + 1) % 6]))
        bm.faces.new((g[(k + 1) % 6], g[k], ap))
    bm.faces.new(tb)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def mini_arco_geo(bm, a, b, r=0.0016):
    pts = raio_pts(a, b, 0.35, 3)
    for p, q_ in zip(pts, pts[1:]):
        tubo(bm, p, q_, r, 4)


def raio_pts(a, b, desvio, prof=4):
    a, b = Vector(a), Vector(b)
    pts = [a, b]
    dd = desvio * (b - a).length
    for _ in range(prof):
        novo = [pts[0]]
        for p, q_ in zip(pts, pts[1:]):
            u = (q_ - p).normalized()
            v = ruido_vec(1.0)
            v -= u * v.dot(u)
            novo += [(p + q_) / 2 + v * dd, q_]
        pts = novo
        dd *= 0.52
    return pts


def novo_cristal(nome):
    o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(o)
    o.rotation_mode = 'XYZ'
    bm = bmesh.new()
    cristal_geo(bm, random.uniform(0.036, 0.043), random.uniform(0.055, 0.068))
    corpo = obj(nome + '_corpo', bm, 'cristal', o)
    corpo.rotation_euler = (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(0, PI))
    arcos = []
    for k in range(3):                                                    # estalos de carga entre as pontas
        bm = bmesh.new()
        a = dirz(random.uniform(0, 2 * PI)) * 0.04 + Z * random.uniform(-0.02, 0.03)
        b = dirz(random.uniform(0, 2 * PI)) * 0.075 + Z * random.uniform(0.0, 0.06)
        mini_arco_geo(bm, a, b)
        ao = obj(nome + '_estalo', bm, 'arco', o)
        ao.visible_shadow = False
        arcos.append(ao)
    fa = []
    for k in range(3):                                                    # faíscas que pulam do cristal
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.004)
        fo = obj(nome + '_faisca', bm, 'faisca', o)
        fo.visible_shadow = False
        fa.append((fo, dirz(random.uniform(0, 2 * PI)) * random.uniform(0.25, 0.5) + Z * random.uniform(0.4, 0.9), random.random()))
    return o, corpo, arcos, fa


def carga_visual(o, corpo, arcos, fa, q, fr, carga, clarao, sem):
    corpo.color = (carga, clarao, 0, 1)
    chave(corpo, 'color', q)
    rr = random.Random(q * 977 + sem)
    for k, ao in enumerate(arcos):
        ao.hide_render = not (carga > 0.5 and rr.random() < 0.35 + 0.4 * clarao)
        chave(ao, 'hide_render', q)
    for fo, v, fase in fa:
        tt = ((fase + fr * 3) % 1.0) * 0.3
        fo.location = v * tt + Z * (-4.9 * tt * tt) + Z * 0.02
        fo.scale = [max(0.001, (1 - tt / 0.3)) * (1 if carga > 0.5 else 0.001)] * 3
        chave(fo, 'location', q)
        chave(fo, 'scale', q)


# cristais no carrossel: j = 0..3 começam nos cestos 0..3 (j=1 é o da vez: carrega no raio)
cri_carr = [novo_cristal('cristal_banho_%d' % j) for j in range(6)]
J_VEZ = 3

# ------------------------------------------------------------------ eletrodos, pórtico em arco, pistões, trilhos
bm = bmesh.new()
segs = 16
a0g, a1g = math.radians(78), math.radians(162)
for k in range(segs):                                                    # viga em arco
    pa = C + dirz(a0g + (a1g - a0g) * k / segs) * R_EL + Z * Z_VIGA
    pb = C + dirz(a0g + (a1g - a0g) * (k + 1) / segs) * R_EL + Z * Z_VIGA
    viga(bm, pa, pb, 0.055)
for ap in (math.radians(80), math.radians(132.5), math.radians(160)):    # colunas do pórtico
    pp = C + dirz(ap) * 0.47
    viga(bm, pp + Z * Z_TAMPA, pp + Z * (Z_VIGA + 0.03), 0.05)
    viga(bm, pp + Z * (Z_VIGA - 0.0), C + dirz(ap) * (R_EL - 0.01) + Z * Z_VIGA, 0.04)
    viga(bm, pp + Z * (Z_VIGA - 0.22), C + dirz(ap) * (R_EL + 0.0) + Z * (Z_VIGA - 0.03), 0.025)   # mão-francesa
    caixa(bm, pp + Z * (Z_TAMPA + 0.01), (0.1, 0.1, 0.02), Matrix.Rotation(ap, 3, 'Z'))
obj('portico', bm, 'amarelo')
bm = bmesh.new()
for k in range(segs + 1):
    if k % 2 == 0:
        pa = C + dirz(a0g + (a1g - a0g) * k / segs) * R_EL + Z * (Z_VIGA + 0.028)
        cil(bm, pa, 0.008, 0.008, lados=6)
obj('portico_parafusos', bm, 'aco')

EL_UP, EL_DN = 0.6, 0.38                                                  # cota da ponta: acima d'água / mergulhada
L_EL = 0.75
eletrodos, hastes = [], []
bm_cam, bm_tr, bm_iso = bmesh.new(), bmesh.new(), bmesh.new()
for i, a in enumerate(ANG_EL):
    p = C + dirz(a) * R_EL
    cil(bm_cam, p + Z * (Z_VIGA - 0.125), 0.03, 0.35, lados=16)            # camisa do pistão (atravessa a viga, flange em cima)
    cil(bm_cam, p + Z * (Z_VIGA + 0.035), 0.04, 0.014, lados=16)
    cil(bm_cam, p + Z * (Z_VIGA - 0.29), 0.036, 0.02, lados=16)
    pt = C + dirz(a) * R_TRILHO
    caixa(bm_tr, pt + Z * ((Z_TAMPA + 0.08 + Z_VIGA - 0.04) / 2), (0.016, 0.03, Z_VIGA - 0.12 - Z_TAMPA), Matrix.Rotation(a, 3, 'Z'))
    for zz in (Z_TAMPA + 0.04, Z_VIGA - 0.03):                            # isoladores do trilho
        cil(bm_iso, pt + Z * zz, 0.022, 0.05, lados=10)
    viga(bm_cam, pt + Z * (Z_VIGA - 0.03) - dirz(a) * 0.02, C + dirz(a) * (R_EL + 0.02) + Z * (Z_VIGA - 0.03), 0.02)
    # eletrodo: objeto que sobe e desce (ponta na origem)
    e = bpy.data.objects.new('eletrodo', None)
    sc.collection.objects.link(e)
    bm = bmesh.new()
    cil(bm, Z * (L_EL / 2), 0.022, L_EL, lados=14)
    cil(bm, Z * 0.01, 0.018, 0.02, lados=14, r2=0.022)
    suavizar(obj('eletrodo_grafite', bm, 'grafite_el', e))
    bm = bmesh.new()
    caixa(bm, Z * (L_EL + 0.02), (0.07, 0.06, 0.05), Matrix.Rotation(a, 3, 'Z'))       # garra do eletrodo
    viga(bm, Z * (L_EL + 0.02), dirz(a) * (R_TRILHO - R_EL - 0.01) + Z * (L_EL + 0.02), 0.025)   # braço da escova
    obj('eletrodo_garra', bm, 'cobre', e)
    bm = bmesh.new()
    caixa(bm, dirz(a) * (R_TRILHO - R_EL - 0.012) + Z * (L_EL + 0.02), (0.012, 0.04, 0.05), Matrix.Rotation(a, 3, 'Z'))
    obj('eletrodo_escova', bm, 'grafite_el', e)
    bm = bmesh.new()                                                      # haste do pistão (sobe até dentro da camisa)
    cil(bm, Z * (L_EL + 0.045 + 0.18), 0.013, 0.36, lados=12)
    suavizar(obj('eletrodo_haste', bm, 'cromo', e))
    bm = bmesh.new()                                                      # crosta queimada na ponta
    cil(bm, Z * 0.07, 0.0235, 0.1, lados=14)
    obj('eletrodo_queima', bm, 'queimado', e)
    eletrodos.append((e, p))
suavizar(obj('pistoes_camisa', bm_cam, 'amarelo'))
obj('trilhos_cobre', bm_tr, 'cobre')
obj('trilhos_isoladores', bm_iso, 'ceramica')


def descida(fr):
    if fr < 0.05:
        return 0.0
    if fr < 0.22:
        return suave((fr - 0.05) / 0.17)
    if fr < 0.6:
        return 1.0
    if fr < 0.82:
        return 1.0 - suave((fr - 0.6) / 0.22)
    return 0.0


def anim_eletrodos(q, fr):
    s = descida(fr)
    for e, p in eletrodos:
        e.location = p + Z * (EL_UP + (EL_DN - EL_UP) * s)
        chave(e, 'location', q)
ANIM.append(anim_eletrodos)

# hidráulica: central no tampo (oeste) e mangueiras até as camisas
A_HID = math.radians(20)
HID = C + dirz(A_HID) * 0.3 + Z * Z_TAMPA
bm = bmesh.new()
caixa(bm, HID + Z * 0.06, (0.18, 0.13, 0.12), Matrix.Rotation(A_HID, 3, 'Z'))
cil(bm, HID + Z * 0.15 + dirz(A_HID) * 0.03, 0.035, 0.08, lados=12)   # reservatório
obj('central_hidraulica', bm, 'amarelo')
bm = bmesh.new()
dmb = dirz(A_HID - PI / 2)
cil(bm, HID + Z * 0.06 + dmb * 0.12, 0.04, 0.1, dmb, lados=12)          # motor da bomba
for k in range(5):
    cil(bm, HID + Z * 0.06 + dmb * (0.1 + k * 0.012), 0.047, 0.004, dmb, lados=12)
obj('central_motor', bm, 'grafite')
bm = bmesh.new()
for i, a in enumerate(ANG_EL):
    p = C + dirz(a) * R_EL
    p0 = HID + Z * 0.12 + dirz(A_HID + PI / 2) * (0.03 - 0.02 * i)
    p1 = p + Z * (Z_VIGA + 0.02) + dirz(a + PI / 2) * 0.03
    varrer(bm, bezier(p0, p0 + Z * 0.45, p1 + Z * 0.25, p1, 16), 0.009, 8)
obj('mangueiras_hid', bm, 'borracha')

# ------------------------------------------------------------------ acionamento do carrossel (topo) e olho da IA
bm = bmesh.new()
cil(bm, C + Z * (Z_TAMPA + 0.07), 0.095, 0.1, lados=20)                   # caixa de engrenagem
cil(bm, C + Z * (Z_TAMPA + 0.125), 0.07, 0.02, lados=20)
obj('redutor', bm, 'grafite')
bm = bmesh.new()
dm = dirz(math.radians(275))
cil(bm, C + Z * (Z_TAMPA + 0.07) + dm * 0.17, 0.05, 0.16, dm, lados=14)   # motor
for k in range(6):
    cil(bm, C + Z * (Z_TAMPA + 0.07) + dm * (0.12 + k * 0.02), 0.058, 0.005, dm, lados=14)
obj('motor_carrossel', bm, 'zarcao')
bm = bmesh.new()                                                          # olho de vigilância do banho (sul)
A_OLHO = math.radians(200)
po = C + dirz(A_OLHO) * 0.4 + Z * Z_TAMPA
cil(bm, po + Z * 0.05, 0.035, 0.1, lados=12)
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.045, matrix=Matrix.Translation(po + Z * 0.12))
obj('olho_suporte', bm, 'grafite')
bm = bmesh.new()
cil(bm, po + Z * 0.12 + (-dirz(A_OLHO) * 0.6 - Z * 0.8).normalized() * 0.04, 0.022, 0.012, -dirz(A_OLHO) * 0.6 - Z * 0.8, lados=16)
obj('olho_lente', bm, 'olho')
bm = bmesh.new()                                                          # antena de dados
cil(bm, po + Z * 0.3 + dirz(A_OLHO + 0.5) * 0.05, 0.004, 0.36, lados=6)
obj('antena', bm, 'aco')

# chaminé de vapor (sudoeste do tampo)
CH = C + dirz(math.radians(325)) * 0.3
bm = bmesh.new()
cil(bm, CH + Z * (Z_TAMPA + 0.25), 0.055, 0.5, lados=18)
tubo(bm, CH + Z * (Z_TAMPA + 0.5), CH + Z * (Z_TAMPA + 0.58) + dirz(math.radians(325)) * 0.08, 0.055, 18)
bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=9, radius=0.055, matrix=Matrix.Translation(CH + Z * (Z_TAMPA + 0.5)))
suavizar(obj('chamine_vapor', bm, 'casco'))
bm = bmesh.new()
for zz in (0.03, 0.26, 0.48):
    cil(bm, CH + Z * (Z_TAMPA + zz), 0.068, 0.02, lados=18)
obj('chamine_flanges', bm, 'ferro')
SAIDA_V = CH + Z * (Z_TAMPA + 0.62) + dirz(math.radians(325)) * 0.13
bm = bmesh.new()
for k in range(5):                                                        # escorridos de calcário/ferrugem da chaminé
    a = math.radians(325) + random.uniform(-1.2, 1.2)
    caixa(bm, CH + dirz(a) * 0.056 + Z * (Z_TAMPA + 0.35), (0.004, 0.012, 0.25), Matrix.Rotation(a, 3, 'Z'))
obj('chamine_escorrido', bm, 'ferrugem')

# ------------------------------------------------------------------ bocas: entrada (sudeste) e saída (noroeste)
bm, bt = bmesh.new(), bmesh.new()
for i in (FACE_ENT, FACE_SAI):
    u0, u1, za, zb = ABERT[i]
    rf = rot_face(i)
    caixa(bm, ponto_face(i, 0, zb + 0.04, R_OUT + 0.06), (0.12, u1 - u0 + 0.1, 0.02), rf)      # capuz
    for s in (-1, 1):
        caixa(bm, ponto_face(i, s * (u1 - u0 + 0.08) / 2, (za + zb) / 2 + 0.02, R_OUT + 0.06), (0.12, 0.012, zb - za + 0.06), rf)
    for k in range(6):                                                    # cortina de tiras de borracha
        uu = u0 + 0.012 + k * (u1 - u0 - 0.024) / 5
        caixa(bt, ponto_face(i, uu, (za + zb) / 2 + 0.01, R_OUT + 0.1), (0.004, 0.026, zb - za - 0.02),
              rf @ Matrix.Rotation(random.uniform(-0.12, 0.12), 3, 'Y'))
obj('bocas_capuz', bm, 'amarelo')
obj('bocas_cortina', bt, 'borracha')

# caminho de entrada: esteira de taliscas do sul (x=0,5) até a boca sudeste, calha interna até o cesto 0
ENT0 = Vector((0.5, -0.99, 0.2))
LAB_E = ponto_face(FACE_ENT, 0, 0.6, R_OUT + 0.08)
IN_E = ponto_face(FACE_ENT, 0, 0.575, R_IN - 0.01)
FIM_E = C + dirz(-PI / 4) * (RC + 0.075) + Z * 0.545
CESTO0 = C + dirz(-PI / 4) * RC + Z * Z_CRI
CAM_E = [ENT0 + Z * 0.075, LAB_E + Z * 0.075, IN_E + Z * 0.066, FIM_E + Z * 0.066, CESTO0]
L_ENT = comprimento(CAM_E)
bm = bmesh.new()
u_inc = (LAB_E - ENT0)
L_inc = u_inc.length
dir_i = u_inc.normalized()
lat_i = Z.cross(dir_i).normalized()
nrm_i = dir_i.cross(lat_i).normalized()
if nrm_i.z < 0:
    nrm_i = -nrm_i
ROT_I = Matrix((lat_i, dir_i, nrm_i)).transposed()
mid = (ENT0 + LAB_E) / 2
for s in (-1, 1):                                                         # longarinas
    caixa(bm, mid + lat_i * s * 0.12 + nrm_i * 0.0, (0.02, L_inc + 0.06, 0.07), ROT_I)
for t in (0.05, 0.5):                                                     # pernas até a laje
    p = ENT0 + u_inc * t
    for s in (-1, 1):
        q0 = p + lat_i * s * 0.12 - nrm_i * 0.03
        viga(bm, q0, Vector((q0.x, q0.y, 0.08)), 0.035)
    viga(bm, p - lat_i * 0.12 - nrm_i * 0.06, p + lat_i * 0.12 - nrm_i * 0.06, 0.025)
for s in (-1, 1):                                                         # mão-francesa no capuz da boca
    viga(bm, LAB_E + lat_i * s * 0.12 - nrm_i * 0.03, ponto_face(FACE_ENT, s * 0.12, 0.45, R_OUT + 0.012), 0.03)
obj('esteira_ent_estrutura', bm, 'amarelo')
bm = bmesh.new()
caixa(bm, mid, (0.2, L_inc, 0.02), ROT_I)                                 # correia
for p in (ENT0, LAB_E):
    cil(bm, p - nrm_i * 0.02, 0.025, 0.21, lat_i, lados=12)               # tambores
obj('esteira_ent_correia', bm, 'borracha')
bm = bmesh.new()                                                          # motor da esteira no topo
cil(bm, LAB_E - nrm_i * 0.02 + lat_i * 0.17, 0.045, 0.1, lat_i, lados=12)
caixa(bm, LAB_E - nrm_i * 0.02 + lat_i * 0.17 - nrm_i * 0.055, (0.06, 0.08, 0.03), ROT_I)
obj('esteira_ent_motor', bm, 'grafite')
bm = bmesh.new()                                                          # calha interna inclinada
dc = FIM_E - IN_E
rc = base_tr(dc)
caixa(bm, (IN_E + FIM_E) / 2 - Z * 0.005, (0.12, dc.length + 0.04, 0.008), rc)
for s in (-1, 1):
    caixa(bm, (IN_E + FIM_E) / 2 + rc @ Vector((s * 0.06, 0, 0.02)), (0.008, dc.length + 0.04, 0.04), rc)
dsl = IN_E - LAB_E
caixa(bm, (LAB_E + IN_E) / 2 - Z * 0.01, (0.2, dsl.length + 0.02, 0.012), base_tr(dsl))   # soleira da boca
obj('calha_entrada', bm, 'aco')
taliscas = []
N_TAL = 4
for k in range(N_TAL):
    bm = bmesh.new()
    caixa(bm, Vector((0, 0, 0.025)), (0.19, 0.012, 0.04))
    o = obj('talisca', bm, 'borracha')
    o.rotation_mode = 'QUATERNION'
    taliscas.append(o)
SP_E = L_inc / 4.0
N_ENT = int(L_ENT / SP_E)
cri_ent = [novo_cristal('cristal_entra_%d' % k) for k in range(N_ENT)]


def anim_entrada(q, fr):
    for k, o in enumerate(taliscas):
        u = ((L_ENT - 0.06) % SP_E + k * SP_E + fr * SP_E) % L_inc
        o.location = ENT0 + dir_i * u + nrm_i * 0.01
        o.rotation_quaternion = ROT_I.to_quaternion()
        chave(o, 'location', q)
        chave(o, 'rotation_quaternion', q)
    for k, (o, corpo, arcos, fa) in enumerate(cri_ent):
        u = L_ENT - SP_E * (k + 1 - fr)
        if u < 0:
            o.location = ENT0 + Z * -1.0
        else:
            p, d = ao_longo(CAM_E, u)
            o.location = p
        o.rotation_euler = (0, 0, k * 1.3)
        chave(o, 'location', q)
        chave(o, 'rotation_euler', q)
        carga_visual(o, corpo, arcos, fa, q, fr, 0.0, 0.0, 100 + k)
ANIM.append(anim_entrada)

# caminho de saída: cesto tomba na boca noroeste, bica desce até a esteira de saída (x=-0,5) ao norte
HC = 0.066                                                                # centro do cristal acima da superfície
CESTO4 = C + dirz(5 * PI / 4) * RC + Z * (Z_CRI + LIFT)
IN_S = ponto_face(FACE_SAI, 0, 0.535, R_IN - 0.08)
LAB_S = ponto_face(FACE_SAI, 0, 0.5, R_OUT + 0.1)
ESS0 = Vector((-0.63, -0.5, 0.245))
ESS1 = Vector((-0.995, -0.5, 0.245))
CAM_S = [CESTO4, IN_S + Z * HC, LAB_S + Z * HC, ESS0 + Z * HC, ESS1 + Z * HC]
L_SAI = comprimento(CAM_S)
bm = bmesh.new()
for a_, b_ in ((IN_S - Z * 0.004, LAB_S - Z * 0.004), (LAB_S - Z * 0.004, ESS0 + Z * 0.0)):
    dc = b_ - a_
    fwd = dc.normalized()
    lat = Z.cross(fwd).normalized()
    rcm = base_tr(dc)
    caixa(bm, (a_ + b_) / 2, (0.12, dc.length + 0.03, 0.008), rcm)
    for s in (-1, 1):
        caixa(bm, (a_ + b_) / 2 + lat * s * 0.06 + Z * 0.02, (0.008, dc.length + 0.03, 0.045), rcm)
viga(bm, LAB_S - Z * 0.02, Vector((LAB_S.x, LAB_S.y, 0.08)), 0.03)         # escora da bica
obj('bica_saida', bm, 'aco')
bm = bmesh.new()                                                          # esteira de saída (curta, até a borda norte)
mid_s = (ESS0 + ESS1) / 2
for s in (-1, 1):
    caixa_de(bm, (ESS1.x, ESS0.y + s * 0.12 - 0.01, 0.08), (ESS0.x + 0.03, ESS0.y + s * 0.12 + 0.01, ESS0.z + 0.03))
caixa_de(bm, (ESS0.x + 0.01, ESS0.y - 0.12, 0.12), (ESS0.x + 0.03, ESS0.y + 0.12, ESS0.z))
obj('esteira_sai_estrutura', bm, 'amarelo')
bm = bmesh.new()
caixa_de(bm, (ESS1.x, ESS0.y - 0.1, ESS0.z - 0.02), (ESS0.x + 0.02, ESS0.y + 0.1, ESS0.z))
cil(bm, Vector((ESS0.x, ESS0.y, ESS0.z - 0.02)), 0.022, 0.21, Vector((0, 1, 0)), lados=12)
obj('esteira_sai_correia', bm, 'borracha')
SP_S = 0.2
N_SAI = int(L_SAI / SP_S) + 1
cri_sai = [novo_cristal('cristal_sai_%d' % k) for k in range(N_SAI)]


def anim_saida(q, fr):
    for k, (o, corpo, arcos, fa) in enumerate(cri_sai):
        if k == 0:
            u = SP_S * min(1.0, fr / 0.85) ** 1.5
        else:
            u = SP_S * (k + fr)
        if u > L_SAI:
            o.location = Vector((0, 0, -2))
        else:
            p, d = ao_longo(CAM_S, u)
            o.location = p
        o.rotation_euler = (0.3 * math.sin(k + fr * 6), 0, k * 0.9 + fr * 2)
        chave(o, 'location', q)
        chave(o, 'rotation_euler', q)
        carga_visual(o, corpo, arcos, fa, q, fr, 1.0, 0.0, 300 + k)
ANIM.append(anim_saida)

# ------------------------------------------------------------------ mastro captor (nordeste)
def r_perna(z):
    return 0.15 - 0.09 * z / Z_MASTRO


ANG_P = [math.radians(a) for a in (210, 330, 90)]
bm = bmesh.new()
caixa(bm, MASTRO + Z * 0.1, (0.36, 0.36, 0.04))                           # sapata
obj('mastro_sapata', bm, 'concreto')
bm = bmesh.new()
for a in ANG_P:
    viga(bm, MASTRO + dirz(a) * r_perna(0.12) + Z * 0.12, MASTRO + dirz(a) * r_perna(Z_MASTRO) + Z * Z_MASTRO, 0.03)
nz = 8
for k in range(nz):
    z0 = 0.2 + k * (Z_MASTRO - 0.25) / nz
    z1 = 0.2 + (k + 1) * (Z_MASTRO - 0.25) / nz
    for i in range(3):
        a, b = ANG_P[i], ANG_P[(i + 1) % 3]
        viga(bm, MASTRO + dirz(a) * r_perna(z0) + Z * z0, MASTRO + dirz(b) * r_perna(z0) + Z * z0, 0.016)
        viga(bm, MASTRO + dirz(a) * r_perna(z0) + Z * z0, MASTRO + dirz(b) * r_perna(z1) + Z * z1, 0.011)
obj('mastro', bm, 'amarelo')
bm = bmesh.new()
for a in ANG_P:
    caixa(bm, MASTRO + dirz(a) * r_perna(0.12) + Z * 0.13, (0.06, 0.06, 0.02))
    for s in (-1, 1):
        cil(bm, MASTRO + dirz(a) * r_perna(0.12) + dirz(a + PI / 2) * s * 0.02 + Z * 0.15, 0.007, 0.03, lados=6)
obj('mastro_chumbadores', bm, 'aco')
# coroa: anel com pontas de cobre e cristal-guia levitando no meio
ZC = Z_MASTRO + 0.22
bm = bmesh.new()
for a in ANG_P:
    viga(bm, MASTRO + dirz(a) * r_perna(Z_MASTRO) + Z * Z_MASTRO, MASTRO + dirz(a) * 0.16 + Z * ZC, 0.022)
cil(bm, MASTRO + Z * (Z_MASTRO + 0.02), 0.07, 0.04, lados=12)
obj('coroa_suporte', bm, 'ferro')
bm = bmesh.new()
toro(bm, MASTRO + Z * ZC, 0.16, 0.018, 40, 10)
toro(bm, MASTRO + Z * (Z_MASTRO + 0.05), 0.075, 0.012, 24, 8)
for k in range(8):
    a = k * PI / 4
    pb = MASTRO + dirz(a) * 0.16 + Z * ZC
    cil(bm, pb + dirz(a) * 0.03 + Z * 0.13, 0.012, 0.28, dirz(a) * 0.22 + Z, lados=8, r2=0.002)
obj('coroa_pontas', bm, 'cobre_ox')
bm = bmesh.new()
for k in range(3):                                                        # bobinas de campo no anel
    a = k * 2 * PI / 3 + 0.5
    cil(bm, MASTRO + dirz(a) * 0.16 + Z * ZC, 0.03, 0.06, dirz(a + PI / 2), lados=12)
obj('coroa_bobinas', bm, 'cobre')
TOPO_CRI = MASTRO + Z * (ZC + 0.04)
cri_guia = bpy.data.objects.new('cristal_guia', None)
sc.collection.objects.link(cri_guia)
bm = bmesh.new()
cristal_geo(bm, 0.07, 0.11)
cg = obj('cristal_guia_corpo', bm, 'cristal', cri_guia)
cg.rotation_euler = (PI, 0, 0)
PONTA_RAIO = MASTRO + Z * (ZC + 0.4)
bm = bmesh.new()                                                          # ponta captora central (acima do cristal)
cil(bm, MASTRO + Z * (ZC + 0.28), 0.01, 0.24, lados=8, r2=0.003)
toro(bm, MASTRO + Z * (ZC + 0.17), 0.04, 0.008, 20, 6)
for k in range(3):
    a = k * 2 * PI / 3
    viga(bm, MASTRO + dirz(a) * 0.04 + Z * (ZC + 0.17), MASTRO + dirz(a) * 0.15 + Z * (ZC + 0.015), 0.008)
obj('ponta_captora', bm, 'cobre')
bm = bmesh.new()
mancha(bm, (MASTRO.x, MASTRO.y), 0.3, 0.1215)
obj('mastro_queimado', bm, 'fuligem')


def anim_guia(q, fr):
    cri_guia.location = TOPO_CRI + Z * (0.015 * math.sin(2 * PI * fr * 2))
    cri_guia.rotation_euler = (0, 0, 2 * PI * fr)
    chave(cri_guia, 'location', q)
    chave(cri_guia, 'rotation_euler', q)
    clar = 1.0 if janela(fr, 0.28, 0.4) else 0.0
    cg.color = (1.0, clar, 0, 1)
    chave(cg, 'color', q)
ANIM.append(anim_guia)

# cabo de descida: anel → perna sudoeste com abraçadeiras → isoladores → centelhador → banco de capacitores
a_desc = ANG_P[0]
CAB = []
for k in range(14):
    z = ZC - 0.02 - k * (ZC - 1.15) / 13
    CAB.append(MASTRO + dirz(a_desc) * (r_perna(min(z, Z_MASTRO)) + 0.045) + Z * z)
CAB[0] = MASTRO + dirz(a_desc) * 0.16 + Z * (ZC - 0.02)
ISO = MASTRO + dirz(a_desc) * 0.3 + Z * 1.0
CENT = ISO + Vector((0.0, -0.17, -0.05))
BUS_IN = Vector((CAP_X + 0.045, 0.42, 0.735))
cab_pts = CAB + bezier(CAB[-1], CAB[-1] - Z * 0.1, ISO + Z * 0.15, ISO + Z * 0.06, 6)[1:]
bm = bmesh.new()
varrer(bm, cab_pts, 0.016, 10)
cab2 = bezier(CENT + Vector((0, -0.02, -0.03)), CENT + Vector((0, -0.1, -0.2)), BUS_IN + Vector((0, 0.15, 0.08)), BUS_IN + Z * 0.03, 12)
varrer(bm, cab2, 0.016, 10)
obj('cabo_descida', bm, 'borracha')
bm = bmesh.new()
cil(bm, BUS_IN + Z * 0.02, 0.022, 0.04, lados=10)
obj('cabo_descida_terminal', bm, 'cobre_ox')
bm = bmesh.new()
for p in CAB[2::2]:                                                       # abraçadeiras na perna
    cil(bm, p, 0.024, 0.025, lados=10)
    viga(bm, p, MASTRO + dirz(a_desc) * r_perna(p.z) + Z * p.z, 0.012)
obj('cabo_abracadeiras', bm, 'aco')
bm = bmesh.new()                                                          # isolador de discos e centelhador
viga(bm, MASTRO + dirz(a_desc) * r_perna(1.0) + Z * 1.0, ISO - dirz(a_desc) * 0.04, 0.03)
viga(bm, MASTRO + dirz(a_desc) * r_perna(0.85) + Z * 0.85, CENT + Vector((0, 0.06, -0.05)), 0.025)
obj('suporte_isolador', bm, 'amarelo')
bm = bmesh.new()
for k in range(5):
    cil(bm, ISO + Z * (-0.05 + k * 0.025), 0.035, 0.012, lados=14)
cil(bm, ISO, 0.016, 0.14, lados=10)
obj('isolador', bm, 'ceramica')
bm = bmesh.new()
for dz in (0.04, -0.04):
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=0.028, matrix=Matrix.Translation(CENT + Z * dz))
tubo(bm, ISO - Z * 0.07, CENT + Z * 0.065, 0.008, 8)
tubo(bm, CENT - Z * 0.065, CENT + Vector((0, -0.02, -0.03)) - Z * 0.03, 0.008, 8)
obj('centelhador', bm, 'cobre')
bm = bmesh.new()
caixa(bm, CENT + Vector((0.035, 0.0, 0.0)), (0.004, 0.09, 0.12))
obj('centelhador_queimado', bm, 'fuligem')
bm = bmesh.new()                                                          # aterramento: cabo até a haste no chão
varrer(bm, bezier(MASTRO + dirz(ANG_P[1]) * r_perna(0.3) + Z * 0.3, MASTRO + dirz(ANG_P[1]) * 0.2 + Z * 0.1,
                  MASTRO + Vector((0.18, -0.25, 0.15)), MASTRO + Vector((0.2, -0.3, 0.13)), 8), 0.009, 8)
cil(bm, MASTRO + Vector((0.2, -0.3, 0.12)), 0.012, 0.06, lados=8)
obj('aterramento', bm, 'cobre_ox')

# ------------------------------------------------------------------ banco de capacitores (leste)
bm = bmesh.new()
caixa_de(bm, (0.6, -0.3, 0.08), (0.94, 0.47, 0.13))                       # estrado
for y in (-0.28, 0.45):
    caixa_de(bm, (0.6, y, 0.13), (0.94, y + 0.02, 0.62))
caixa_de(bm, (0.6, -0.3, 0.6), (0.94, 0.47, 0.62))                        # quadro de cima (aberto)
obj('banco_quadro', bm, 'amarelo')
bm, bt = bmesh.new(), bmesh.new()
for y in CAPS_Y:
    cil(bm, Vector((CAP_X, y, 0.37)), 0.1, 0.46, lados=24)
    for zz in (0.18, 0.56):
        cil(bt, Vector((CAP_X, y, zz)), 0.104, 0.02, lados=24)
suavizar(obj('capacitores', bm, 'grafite'))
obj('capacitores_cintas', bt, 'aco')
bm, bc = bmesh.new(), bmesh.new()
for y in CAPS_Y:
    for dx in (-0.045, 0.045):
        for k in range(4):
            cil(bm, Vector((CAP_X + dx, y, 0.64 + k * 0.025)), 0.026, 0.012, lados=12)
        cil(bm, Vector((CAP_X + dx, y, 0.67)), 0.012, 0.1, lados=10)
for dx in (-0.045, 0.045):                                                # barramentos
    caixa_de(bc, (CAP_X + dx - 0.012, CAPS_Y[0] - 0.03, 0.72), (CAP_X + dx + 0.012, CAPS_Y[-1] + 0.12, 0.735))
obj('capacitores_isoladores', bm, 'ceramica')
obj('barramentos', bc, 'cobre_ox')
bm = bmesh.new()
for y in CAPS_Y:
    mancha(bm, (CAP_X + 0.045, y), 0.05, 0.6205)
obj('banco_queimado', bm, 'fuligem')
# indicador de carga: régua de LEDs violeta na face oeste do quadro
LEDS = []
for k in range(6):
    bm = bmesh.new()
    caixa(bm, Vector((0.66, -0.3025, 0.25 + k * 0.05)), (0.025, 0.006, 0.03))
    lo = obj('led', bm, 'led_violeta')
    bm = bmesh.new()
    caixa(bm, Vector((0.66, -0.3005, 0.25 + k * 0.05)), (0.027, 0.006, 0.032))
    obj('led_vidro', bm, 'led_apagado')
    LEDS.append(lo)
bm = bmesh.new()                                                          # placa de alta tensão (triângulo)
pt = Vector((0.82, -0.3, 0.44))
v = [bm.verts.new(pt + Vector((-0.07, 0, -0.05))), bm.verts.new(pt + Vector((0.07, 0, -0.05))), bm.verts.new(pt + Vector((0, 0, 0.07)))]
bm.faces.new(v)
f = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
for vv in [e for e in f['geom'] if isinstance(e, bmesh.types.BMVert)]:
    vv.co.y -= 0.004
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('placa_at', bm, 'amarelo')
bm = bmesh.new()
for a_, b_ in (((0.012, 0, 0.045), (-0.01, 0, 0.0)), ((-0.01, 0, 0.0), (0.012, 0, 0.0)), ((0.012, 0, 0.0), (-0.012, 0, -0.035))):
    viga(bm, pt + Vector(a_) + Vector((0, -0.006, 0)), pt + Vector(b_) + Vector((0, -0.006, 0)), 0.008)
obj('placa_at_raio', bm, 'fuligem')
bm = bmesh.new()                                                          # placa de série apagada
p_pl = Vector((0.82, -0.302, 0.26))
caixa(bm, p_pl, (0.12, 0.006, 0.05))
obj('placa_serie', bm, 'aco')
bm = bmesh.new()
for k in range(4):
    caixa(bm, p_pl + Vector((random.uniform(-0.03, 0.02), -0.004, 0.015 - k * 0.01)), (random.uniform(0.02, 0.07), 0.002, 0.004))
obj('placa_serie_letras', bm, 'ferro')

# cabos grossos: barramento → trilhos dos eletrodos (passam sobre a eletrocalha)
CABOS_EL = []
SELA = C + dirz(math.radians(45)) * 0.44
bm = bmesh.new()                                                          # poste da sela dos cabos (no tampo)
viga(bm, SELA + Z * Z_TAMPA, SELA + Z * 1.98, 0.045)
viga(bm, SELA + Z * 1.6, C + dirz(math.radians(45)) * 0.25 + Z * Z_TAMPA, 0.03)
caixa(bm, SELA + Z * 1.98, (0.07, 0.2, 0.025), Matrix.Rotation(math.radians(45), 3, 'Z'))
obj('sela_poste', bm, 'amarelo')
bm = bmesh.new()
dsl_t = dirz(math.radians(135))
for i, a in enumerate(ANG_EL):
    pt_ = C + dirz(a) * R_TRILHO + Z * (Z_VIGA - 0.02)
    p0 = Vector((CAP_X - 0.045 + 0.09 * (i % 2), CAPS_Y[0] + 0.05 + i * 0.09, 0.745))
    sl = SELA + Z * 2.015 + dsl_t * (-0.06 + 0.06 * i)
    ida = (pt_ - p0)
    ida.z = 0
    ida.normalize()
    pts = bezier(p0, p0 + Z * 0.6, sl - ida * 0.35, sl, 14) + bezier(sl, sl + ida * 0.3, pt_ + Z * 0.3, pt_, 14)[1:]
    varrer(bm, pts, 0.017, 10)
    CABOS_EL.append(pts)
obj('cabos_eletrodos', bm, 'borracha')
bm = bmesh.new()
for pts in CABOS_EL:                                                      # terminais de cobre (olhal) e mangas
    cil(bm, pts[0] + Z * 0.0, 0.024, 0.04, lados=10)
    cil(bm, pts[-1], 0.024, 0.04, pts[-1] - pts[-2], lados=10)
obj('cabos_terminais', bm, 'cobre_ox')
bm = bmesh.new()
for t in (0.35, 0.6):                                                     # amarração do feixe
    for pts in CABOS_EL:
        p = pts[int(t * (len(pts) - 1))]
        toro(bm, p, 0.021, 0.004, 12, 5, (pts[int(t * (len(pts) - 1)) + 1] - p).normalized().to_track_quat('Z', 'Y').to_matrix())
obj('cabos_amarras', bm, 'aco')

# ------------------------------------------------------------------ água: cano do oeste, válvula motorizada e medidor
XW = -0.5
ZW = 0.275
P_A = [Vector((XW, 0.995, ZW)), Vector((XW, 0.74, ZW)), Vector((-0.2, 0.74, ZW)), Vector((-0.2, R_OUT + 0.002, ZW))]
bm = bmesh.new()
for a_, b_ in zip(P_A, P_A[1:]):
    tubo(bm, a_, b_, 0.03, 16)
for p in P_A[1:-1]:
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.03, matrix=Matrix.Translation(p))
suavizar(obj('cano_agua', bm, 'aco'))
bm = bmesh.new()
for p, d in ((P_A[0] + Vector((0, -0.02, 0)), Vector((0, 1, 0))), (Vector((XW, 0.92, ZW)), Vector((0, 1, 0))),
             (Vector((XW, 0.80, ZW)), Vector((0, 1, 0))), (Vector((-0.42, 0.74, ZW)), Vector((1, 0, 0))),
             (Vector((-0.3, 0.74, ZW)), Vector((1, 0, 0))), (P_A[-1] + Vector((0, 0.012, 0)), Vector((0, 1, 0)))):
    cil(bm, p, 0.045, 0.018, d, lados=16)
caixa_de(bm, (XW - 0.04, 0.69, 0.08), (XW + 0.04, 0.79, ZW - 0.028))     # selas de apoio
caixa_de(bm, (-0.24, 0.6, 0.08), (-0.16, 0.66, ZW - 0.028))
obj('cano_flanges', bm, 'ferro')
bm = bmesh.new()                                                          # válvula motorizada
VV = Vector((XW, 0.86, ZW))
caixa(bm, VV, (0.08, 0.075, 0.075))
cil(bm, VV + Z * 0.07, 0.012, 0.06, lados=8)
caixa(bm, VV + Z * 0.12, (0.09, 0.07, 0.06))
obj('valvula', bm, 'zarcao')
bm = bmesh.new()
caixa(bm, VV + Z * 0.12 + Vector((-0.046, 0.0, 0.0)), (0.004, 0.03, 0.02))
obj('valvula_led', bm, 'led_violeta')
bm = bmesh.new()                                                          # medidor de vazão
MV = Vector((-0.36, 0.74, ZW))
cil(bm, MV, 0.05, 0.1, Vector((1, 0, 0)), lados=16)
cil(bm, MV + Z * 0.07, 0.035, 0.03, lados=16)
obj('medidor', bm, 'grafite')
bm = bmesh.new()
cil(bm, MV + Z * 0.086, 0.028, 0.004, lados=16)
obj('medidor_vidro', bm, 'vidro')
bm = bmesh.new()                                                          # crosta de calcário nas juntas do cano
for p in (Vector((XW, 0.92, ZW - 0.035)), P_A[-1] + Vector((0, 0.03, -0.03)), Vector((-0.3, 0.74, ZW - 0.035))):
    for k in range(6):
        pedra(bm, p + ruido_vec(0.025) * Vector((1, 1, 0.4)), random.uniform(0.006, 0.012), 0.5)
obj('calcario_juntas', bm, 'calcario')
bm = bmesh.new()
for k in range(5):                                                        # escorrido de calcário embaixo das janelas
    i = random.choice((2, 4, 6))
    caixa(bm, ponto_face(i, random.uniform(-0.1, 0.1), 0.22, R_OUT + 0.0015), (0.003, random.uniform(0.01, 0.02), 0.13), rot_face(i))
obj('calcario_escorrido', bm, 'calcario')

# fiação exposta: caixa de junção na chapa oeste com tampa solta e fios pendurados
JB = ponto_face(1, 0.13, 0.95, R_OUT + 0.04)
bm = bmesh.new()
caixa(bm, JB, (0.06, 0.1, 0.1), rot_face(1))
obj('caixa_juncao', bm, 'grafite')
bm = bmesh.new()
caixa(bm, JB + dirz(PI / 4) * 0.06 + Z * -0.09, (0.005, 0.1, 0.1), rot_face(1) @ Matrix.Rotation(-0.5, 3, 'Y') @ Matrix.Rotation(0.3, 3, 'X'))
obj('caixa_tampa_solta', bm, 'grafite')
for k, m_ in enumerate(('fio_verm', 'fio_azul', 'fio_amar', 'fio_verm')):
    bm = bmesh.new()
    a_ = ponto_face(1, 0.1 + k * 0.02, 0.93, R_OUT + 0.072)
    b_ = ponto_face(1, 0.15 + k * 0.012, 0.62 - 0.03 * k, R_OUT + 0.03)
    varrer(bm, bezier(a_, a_ + dirz(PI / 4) * 0.08 - Z * 0.1, b_ + dirz(PI / 4) * 0.1, b_, 10), 0.0035, 6)
    obj('fio', bm, m_)
bm = bmesh.new()                                                          # eletroduto da caixa até o tampo
varrer(bm, bezier(JB + Z * 0.05, JB + Z * 0.14, HID + Z * 0.15 + dirz(A_HID + PI / 2) * 0.1, HID + Z * 0.06 + dirz(A_HID + PI / 2) * 0.065, 10), 0.012, 8)
obj('eletroduto', bm, 'aco')

# ------------------------------------------------------------------ sujeira: óleo, lama, ferrugem, queimados, poças
bm = bmesh.new()
for i in (0, 1):                                                          # óleo da central hidráulica escorrendo
    for k in range(2):
        caixa(bm, ponto_face(i, random.choice((-1, 1)) * random.uniform(0.17, 0.185), 0.75, R_OUT + 0.0015), (0.003, 0.012, 0.45), rot_face(i))
for c_, r_ in (((0.5, 0.05), 0.06), ((0.45, 0.32), 0.05), ((0.42, -0.62), 0.05)):
    mancha(bm, c_, r_, 0.0815)
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for k in range(22):                                                       # ferrugem escorrida dos rebites e cintas
    i = random.randrange(8)
    caixa(bm, ponto_face(i, random.choice((-1, 1)) * random.uniform(0.168, 0.188), random.uniform(0.35, 0.8), R_OUT + 0.0012),
          (0.0025, random.uniform(0.006, 0.014), random.uniform(0.08, 0.22)), rot_face(i))
obj('ferrugem_escorrida', bm, 'ferrugem')
bm = bmesh.new()
for k in range(16):                                                       # respingos de lama embaixo das chapas
    i = random.randrange(8)
    caixa(bm, ponto_face(i, random.uniform(-0.17, 0.17), Z_BASE + random.uniform(0.0, 0.07), R_OUT + 0.0018),
          (0.003, random.uniform(0.03, 0.08), random.uniform(0.03, 0.09)), rot_face(i))
obj('lama_chapas', bm, 'lama')
bm = bmesh.new()
for k in range(10):
    mancha(bm, (random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95)), random.uniform(0.05, 0.13), 0.081)
for k in range(18):
    pedra(bm, Vector((random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95), 0.085)), random.uniform(0.01, 0.025), 0.4)
obj('lama_laje', bm, 'lama')
bm = bmesh.new()
for i in ANG_EL:                                                          # marcas de arco nas chapas sob o pórtico
    for k in range(2):
        a = i + random.uniform(-0.2, 0.2)
        fi = int(round(a / (PI / 4))) % 8
        caixa(bm, ponto_face(fi, random.uniform(-0.12, 0.12), random.uniform(0.84, 0.98), R_OUT + 0.0015),
              (0.003, random.uniform(0.04, 0.09), random.uniform(0.05, 0.12)), rot_face(fi))
obj('queimado_chapas', bm, 'fuligem')
bm = bmesh.new()
caixa(bm, Vector((0, 0, -0.5)), (40, 40, 1.0))
chao = obj('chao', bm, 'terra')
bm = bmesh.new()
for k in range(40):
    a = random.uniform(0, 2 * PI)
    rr = random.uniform(1.1, 4.5)
    pedra(bm, Vector((math.cos(a) * rr, math.sin(a) * rr, 0.0)), random.uniform(0.03, 0.12), 0.5)
obj('pedras', bm, 'terra')

# ------------------------------------------------------------------ vapor, arcos, raio, pulsos
vapores = []
for k in range(9):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))
vap_dentro = []
for k in range(5):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vap_dentro.append(obj('vapor_banho', bm, 'vapor_dentro'))
vap_vaza = []
VAZ_P = [ponto_face(1, 0.0, Z_TOP + 0.03, R_OUT + 0.04), ponto_face(6, -0.12, Z_TOP + 0.03, R_OUT + 0.04)]
for k in range(6):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vap_vaza.append(obj('vapor_vaza', bm, 'vapor_vaza'))


def brilho_banho(fr):
    if fr < 0.35:
        return 0.0
    if fr < 0.38:
        return suave((fr - 0.35) / 0.03)
    if fr < 0.47:
        return 1.0
    if fr < 0.9:
        return 0.08 + 0.92 * math.exp(-(fr - 0.47) * 9)
    return 0.08 * (1 - (fr - 0.9) / 0.1)


def anim_vapor(q, fr):
    forca = 0.6 + 0.6 * brilho_banho(fr)
    for k, o in enumerate(vapores):
        u = (k / len(vapores) + fr * 1.5) % 1.0
        o.location = SAIDA_V + Vector((-0.5 * u * u, -0.35 * u * u, 1.3 * u + 0.04))
        o.scale = [(0.05 + 0.35 * u) * forca] * 3
        o.rotation_euler = (k, u * 2, k * 0.5)
        for c_ in ('location', 'scale', 'rotation_euler'):
            chave(o, c_, q)
    for k, o in enumerate(vap_dentro):
        u = (k / len(vap_dentro) + fr) % 1.0
        a = k * 2.1 + fr * 1.0
        o.location = C + dirz(a) * 0.22 + Z * (Z_AGUA + 0.06 + 0.3 * u)
        o.scale = [0.1 + 0.1 * u] * 3
        for c_ in ('location', 'scale'):
            chave(o, c_, q)
    for k, o in enumerate(vap_vaza):
        p = VAZ_P[k % 2]
        d = dirz((1 if k % 2 == 0 else 6) * PI / 4)
        u = ((k // 2) / 3 + fr * 2.5) % 1.0
        o.location = p + d * (0.12 * u) + Z * (0.35 * u)
        o.scale = [max(0.002, (0.02 + 0.1 * u) * forca)] * 3
        for c_ in ('location', 'scale'):
            chave(o, c_, q)
ANIM.append(anim_vapor)


def arco_obj(nome, a, b, desvio, r=0.0035, galhos=2, mat='arco', halo='arco_brilho', fator=2.6):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    pts = raio_pts(a, b, desvio * 1.4, 5 if L < 0.8 else 8)
    ramos = [(pts, r)]
    for g in range(galhos):
        k = random.randint(len(pts) // 6, len(pts) * 3 // 4)
        p0 = pts[k]
        d = ((b - a).normalized() + ruido_vec(0.9)).normalized() * L * random.uniform(0.12, 0.3)
        ramos.append((raio_pts(p0, p0 + d, 0.3, 4), r * 0.45))
    bm = bmesh.new()
    for lst, rr in ramos:
        n_ = len(lst) - 1
        for i, (p, q_) in enumerate(zip(lst, lst[1:])):
            tubo(bm, p, q_, rr * (1 - 0.5 * i / n_), 5)
    nf = len(bm.faces)
    for lst, rr in ramos[:1]:
        for i, (p, q_) in enumerate(zip(lst[::2], lst[2::2])):
            tubo(bm, p, q_, rr * fator, 8)
    for f_ in list(bm.faces)[nf:]:
        f_.material_index = 1
    o = obj(nome, bm, mat)
    o.data.materials.append(M[halo])
    o.visible_shadow = False
    return o


# raio: três descargas (repiques) do céu até a ponta captora
CEU = PONTA_RAIO + Vector((2.2, 3.5, 15.0))
raios = [arco_obj('raio', CEU + ruido_vec(0.6), PONTA_RAIO, 0.18, r=0.02, galhos=5, mat='raio', halo='raio_brilho', fator=4.0)
         for _ in range(3)]
JANELAS_RAIO = [(0.28, 0.30), (0.33, 0.345), (0.36, 0.395)]
arco_coroa = [arco_obj('arco_coroa', TOPO_CRI + ruido_vec(0.03), MASTRO + dirz(k * 2.1) * 0.16 + Z * (ZC + 0.1), 0.3, r=0.003, galhos=1)
              for k in range(3)]
arco_cent = [arco_obj('arco_centelhador', CENT + Z * 0.015, CENT - Z * 0.015 + ruido_vec(0.005), 0.4, r=0.004, galhos=0)
             for _ in range(2)]
# arcos no banho: eletrodo ↔ água e eletrodo ↔ cristal da vez
arcos_banho = []
for i, a in enumerate(ANG_EL):
    pe = C + dirz(a) * R_EL + Z * (Z_AGUA + 0.03)
    for k in range(2):
        alvo = C + dirz(a + random.uniform(-0.5, 0.5)) * random.uniform(0.15, 0.42) + Z * (Z_AGUA + 0.003)
        arcos_banho.append(arco_obj('arco_banho', pe, alvo, 0.3, r=0.0028, galhos=2))
for i in range(3):
    a_cri = ang_slot(J_VEZ, 0.38 + i * 0.03)
    pc = C + dirz(a_cri) * RC + Z * (Z_CRI + 0.02)
    pe = C + dirz(ANG_EL[i % 2]) * R_EL + Z * (Z_AGUA + 0.06)
    arcos_banho.append(arco_obj('arco_cristal', pe, pc, 0.25, r=0.0032, galhos=1))
arcos_banho.append(arco_obj('arco_eixo', C + Z * (Z_AGUA + 0.12) + dirz(2.0) * 0.035, C + dirz(ang_slot(J_VEZ, 0.4)) * RC + Z * (Z_CRI + 0.03), 0.3, r=0.0025, galhos=1))

# pulsos de energia correndo pelos cabos
CAMINHO_DESC = cab_pts + cab2
L_DESC = comprimento(CAMINHO_DESC)
pulsos_desc, pulsos_el = [], []
for k in range(4):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    o = obj('pulso', bm, 'pulso')
    o.rotation_mode = 'QUATERNION'
    o.visible_shadow = False
    pulsos_desc.append(o)
for pts in CABOS_EL:
    lst = []
    for k in range(2):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
        o = obj('pulso', bm, 'pulso')
        o.rotation_mode = 'QUATERNION'
        o.visible_shadow = False
        lst.append(o)
    pulsos_el.append((pts, comprimento(pts), lst))

# faíscas quentes nos terminais e na ponta captora
faiscas = []
for k in range(24):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.005)
    o = obj('faisca', bm, 'faisca_q' if k % 2 else 'faisca')
    o.visible_shadow = False
    origem = [PONTA_RAIO, CENT, C + dirz(ANG_EL[k % 3]) * R_TRILHO + Z * (Z_VIGA - 0.1)][k % 3]
    faiscas.append((o, origem, Vector((random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), random.uniform(0.2, 1.3))), random.random()))

# luzes: clarão do raio, ponta captora, banho por dentro, lâmpada de serviço
luz_ceu_d = bpy.data.lights.new('Clarão', 'SUN')
luz_ceu_d.color = (0.75, 0.72, 1.0)
luz_ceu_d.angle = math.radians(12)
luz_ceu = bpy.data.objects.new('Clarão', luz_ceu_d)
sc.collection.objects.link(luz_ceu)
luz_ceu.rotation_euler = (math.radians(25), math.radians(-12), math.radians(145))
luz_ponta = luz('Ponta', (0.75, 0.6, 1.0), 0, PONTA_RAIO + Z * 0.1, 0.1)
luz_banho = luz('Banho', VIOLETA, 0, C + Z * (Z_AGUA + 0.12), 0.15)
luz_banho2 = luz('Banho fundo', VIOLETA, 0, C + Z * (Z_BASE + 0.12), 0.2)
luz_servico = luz('Serviço', (1.0, 0.62, 0.3), 3.0, C + Z * (Z_TOP - 0.08) + dirz(PI) * 0.25, 0.05)
luz_trilhos = luz('Trilhos', VIOLETA, 0, C + dirz(ANG_EL[1]) * R_TRILHO + Z * 1.45, 0.1)


def nivel_banco(fr):
    if fr < 0.28:
        return 0.05
    if fr < 0.33:
        return 0.05 + 0.95 * suave((fr - 0.28) / 0.05)
    if fr < 0.355:
        return 1.0
    if fr < 0.45:
        return 1.0 - 0.95 * suave((fr - 0.355) / 0.095)
    return 0.05


def anim_energia(q, fr):
    rr = random.Random(q * 31 + 7)
    raio_on = -1
    for k, (a, b) in enumerate(JANELAS_RAIO):
        if janela(fr, a, b):
            raio_on = k
    for k, o in enumerate(raios):
        o.hide_render = k != raio_on
        chave(o, 'hide_render', q)
    flash = 1.0 if raio_on >= 0 else 0.0
    luz_ceu_d.energy = 3.5 * flash
    chave(luz_ceu_d, 'energy', q)
    luz_ponta.energy = 900 * flash
    chave(luz_ponta, 'energy', q)
    bg_str.default_value = 1.0 + 1.6 * flash
    bg_str.keyframe_insert('default_value', frame=q)
    for k, o in enumerate(arco_coroa):
        o.hide_render = not ((flash > 0 and rr.random() < 0.8) or (rr.random() < 0.12))
        chave(o, 'hide_render', q)
    for k, o in enumerate(arco_cent):
        o.hide_render = not (janela(fr, 0.29, 0.34) and k == q % 2)
        chave(o, 'hide_render', q)
    # pulsos descendo o cabo do mastro (0,28–0,34) e indo do banco aos eletrodos (0,33–0,39)
    for k, o in enumerate(pulsos_desc):
        t = (fr - 0.28) / 0.06
        u = t * L_DESC - k * 0.18
        vis = 0 <= t <= 1.0 and 0 <= u <= L_DESC
        p, d = ao_longo(CAMINHO_DESC, max(0.0, min(u, L_DESC)))
        o.location = p
        o.rotation_quaternion = d.to_track_quat('Z', 'Y')
        o.scale = (0.02, 0.02, 0.07) if vis else (0.001, 0.001, 0.001)
        for c_ in ('location', 'rotation_quaternion', 'scale'):
            chave(o, c_, q)
    for pts, L, lst in pulsos_el:
        for k, o in enumerate(lst):
            t = (fr - 0.335) / 0.05
            u = t * L - k * 0.2
            vis = 0 <= t <= 1.15 and 0 <= u <= L
            p, d = ao_longo(pts, max(0.0, min(u, L)))
            o.location = p
            o.rotation_quaternion = d.to_track_quat('Z', 'Y')
            o.scale = (0.021, 0.021, 0.07) if vis else (0.001, 0.001, 0.001)
            for c_ in ('location', 'rotation_quaternion', 'scale'):
                chave(o, c_, q)
    # banco: régua de LEDs
    nv = nivel_banco(fr)
    for k, lo in enumerate(LEDS):
        lo.hide_render = nv < (k + 0.5) / len(LEDS)
        chave(lo, 'hide_render', q)
    # banho acende
    g = brilho_banho(fr)
    pisc = 0.8 + 0.2 * math.sin(fr * 230) * math.sin(fr * 97)
    vol_em.default_value = 0.5 * g * pisc
    vol_em.keyframe_insert('default_value', frame=q)
    luz_banho.energy = 5 * g * pisc + 0.6
    luz_banho2.energy = 8 * g * pisc
    luz_trilhos.energy = 30 * (1.0 if janela(fr, 0.34, 0.46) else 0.0) * pisc
    for l_ in (luz_banho, luz_banho2, luz_trilhos):
        chave(l_, 'energy', q)
    ondas_w.default_value = fr * 4.0 * (1 + g)
    ondas_w.keyframe_insert('default_value', frame=q)
    for k, o in enumerate(arcos_banho):
        o.hide_render = not (g > 0.6 and descida(fr) > 0.9 and rr.random() < 0.5)
        chave(o, 'hide_render', q)
    # faíscas
    for k, (o, origem, v, fase) in enumerate(faiscas):
        ativo = janela(fr, 0.28, 0.42) if k % 3 < 2 else janela(fr, 0.34, 0.5)
        tt = ((fase + fr * 6) % 1.0) * 0.3
        o.location = origem + v * tt + Z * (-4.9 * tt * tt)
        o.scale = [max(0.001, (1 - tt / 0.3)) if ativo else 0.001] * 3
        chave(o, 'location', q)
        chave(o, 'scale', q)
    # cristais no banho: o da vez (j=1) carrega quando o banho acende
    for j, (o, corpo, arcos, fa) in enumerate(cri_carr):
        a = ang_slot(j, fr)
        o.location = C + dirz(a) * RC + Z * (Z_CRI + LIFT * ergue(a) + 0.004 * math.sin(fr * 2 * PI * 3 + j) * (1 - ergue(a)))
        o.rotation_euler = (0, 0, a + j)
        chave(o, 'location', q)
        chave(o, 'rotation_euler', q)
        if j > J_VEZ:
            carga = 1.0
        elif j == J_VEZ:
            carga = suave((fr - 0.37) / 0.04)
        else:
            carga = 0.0
        carga_visual(o, corpo, arcos, fa, q, fr, carga, g * (0.6 + 0.4 * rr.random()), 200 + j)
ANIM.append(anim_energia)

# ------------------------------------------------------------------ mundo: céu de tempestade
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
nt = mundo.node_tree
bg = nt.nodes['Background']
tcw = no(nt, 'TextureNodeTexCoord' if False else 'ShaderNodeTexCoord')
nuv = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.2, 'Detail': 10.0, 'Roughness': 0.62})
mp = no(nt, 'ShaderNodeMapping')
mp.inputs['Scale'].default_value = (1.0, 1.0, 3.5)
nt.links.new(tcw.outputs['Generated'], mp.inputs['Vector'])
nt.links.new(mp.outputs['Vector'], nuv.inputs['Vector'])
rampa = no(nt, 'ShaderNodeValToRGB')
rampa.color_ramp.elements[0].position = 0.38
rampa.color_ramp.elements[0].color = (0.012, 0.013, 0.017, 1)
rampa.color_ramp.elements[1].position = 0.72
rampa.color_ramp.elements[1].color = (0.11, 0.115, 0.135, 1)
nt.links.new(nuv.outputs['Fac'], rampa.inputs['Fac'])
sepw = no(nt, 'ShaderNodeSeparateXYZ')
nt.links.new(tcw.outputs['Generated'], sepw.inputs[0])
hor = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.05, 'From Max': 0.35, 'To Min': 1.0, 'To Max': 0.0})
nt.links.new(sepw.outputs['Z'], hor.inputs['Value'])
mixh = no(nt, 'ShaderNodeMix', data_type='RGBA')
mixh.inputs[7].default_value = (0.07, 0.072, 0.085, 1)
nt.links.new(hor.outputs['Result'], mixh.inputs[0])
nt.links.new(rampa.outputs['Color'], mixh.inputs[6])
nt.links.new(mixh.outputs[2], bg.inputs['Color'])
bg_str = bg.inputs['Strength']
bg_str.default_value = 0.9
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 1.0
sol.angle = math.radians(22)
sol.color = (0.78, 0.82, 0.95)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(42), 0, math.radians(-40))

vol_em = M['banho'].node_tree.nodes['vol'].inputs['Emission Strength']
ondas_w = M['banho'].node_tree.nodes['ondas'].inputs['W']

# ------------------------------------------------------------------ portas (nós do jogo)
for nome, p in (('PORTA_ITEM_ENT_S1', Vector((0.5, -1.0, 0.2))), ('PORTA_ITEM_SAI_O0', Vector((-1.0, -0.5, 0.25))),
                ('PORTA_FLUIDO_ENT_N0', Vector((-0.5, 1.0, ZW)))):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    e.location = p

# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for f_ in ANIM:
        f_(q, fr)
for idb in list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.materials) + [mundo]:
    ad = getattr(idb, 'animation_data', None)
    if idb is not None and getattr(idb, 'node_tree', None) is not None and idb.node_tree.animation_data:
        ad2 = idb.node_tree.animation_data
    else:
        ad2 = None
    for a_ in (ad, ad2):
        if a_ and a_.action:
            try:
                for fc in a_.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'CONSTANT' if fc.data_path in ('hide_render',) else 'LINEAR'
            except AttributeError:
                for ly in a_.action.layers:
                    for st in ly.strips:
                        for cb in st.channelbags:
                            for fc in cb.fcurves:
                                for kp in fc.keyframe_points:
                                    kp.interpolation = 'CONSTANT' if fc.data_path in ('hide_render',) else 'LINEAR'

# ------------------------------------------------------------------ render e câmera
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
sc.cycles.max_bounces = 10
sc.cycles.transmission_bounces = 10
sc.cycles.volume_bounces = 1
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = 1.0
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def renderizar():
    import time
    for tentativa in range(30):
        try:
            renderizar()
            return
        except RuntimeError as erro:
            print('GPU ocupada, tentando de novo:', erro)
            time.sleep(30)


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0] if args else 'foto'
quais = args[1:] or ['0', 'perto', 'raio']
if modo == 'foto':
    sc.cycles.samples = int(os.environ.get('AMOSTRAS', '160'))
    sc.render.resolution_percentage = int(os.environ.get('ESCALA', '100'))
    if '0' in quais:
        sc.frame_set(44)                                                   # banho aceso, cristal da vez carregado
        sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
        mirar((-4.1, -3.0, 2.4), (0.1, 0.1, 1.35), 31)
        sc.render.filepath = os.path.join(AQUI, 'captador_carga_0.png')
        renderizar()
    if 'perto' in quais:
        sc.frame_set(44)
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar(C + Vector((-0.86, 0.1, 0.98)), C + Vector((0.05, 0.1, 0.48)), 24)
        sc.render.filepath = os.path.join(AQUI, 'captador_carga_perto.png')
        renderizar()
    if 'raio' in quais:
        sc.frame_set(37)                                                   # repique do raio, pulso no cabo, banho acendendo
        sc.render.resolution_x, sc.render.resolution_y = 1100, 1400
        mirar((-6.6, -4.4, 1.4), (0.4, 0.6, 3.4), 24)
        sc.render.filepath = os.path.join(AQUI, 'captador_carga_raio.png')
        renderizar()
print('CAPTADOR ok')
