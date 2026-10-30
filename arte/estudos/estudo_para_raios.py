"""Estudo isolado (fora do jogo): PARA-RAIOS e PARA-RAIOS DE CRISTAL da IA (lote 15, clima).
Regras: para_raios (1×1) pega raios num raio de 14 m e gera 120 MJ por raio; para_raios_2 (1×1, cristal) pega em
22 m e gera 200 MJ. Sem acumulador perto, é só proteção. 1 tile = 1 m; x leste, y norte.
- para_raios: laje de concreto 0,90 × 0,90 com poço de inspeção no canto sudeste (terra queimada, fulguritos, haste de
  terra com conector). Mastro tubular de aço afilado em três gomos com flanges aparafusados (o gomo do meio é peça
  trocada, em primer vermelho), sapata com nervuras e chumbadores; três estais com esticadores e grampos. No topo,
  captor Franklin: haste com a ponta derretida e revenida (azul-dourado), coroa de pontas (duas fundidas). Descida de
  cobre grossa e esverdeada, afastada do mastro por isoladores de carretel em braçadeiras; contador de descargas da IA;
  caixa de transferência com centelhador de chifres; cabo ao banco de capacitores (barra de LEDs de carga) e fita de
  cobre até a haste de terra. Figura de Lichtenberg queimada na laje e no chão.
- para_raios_2 (cristal): mastro mais grosso e mais alto, estais em dois níveis; bobina em carretel de fenolite no
  mastro (a descida passa por ela); no topo, copa de cobre com quatro garras segurando um cristal grande, dois anéis
  de campo em isoladores, garras com pontas fundidas; bobina de choque no chão antes de 6 capacitores.
Animação (laço de 4 s): raio nos quadros 11–17 (líder, descarga, religamento), clarão, faíscas e gotas de metal,
descida brilhando, arcos nos isoladores, Lichtenberg acendendo, chifres faiscando, cristal acendendo, LEDs de carga
subindo e descarregando devagar, chuva caindo.
Uso: blender -b --python estudo_para_raios.py -- foto [chave]   (chaves: pr, pc, raio)
     blender -b --python estudo_para_raios.py -- teste [chave]
     blender -b --python estudo_para_raios.py -- cam grp quadro x y z ax ay az lente arq [amostras]"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise

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
F_FOTO = 12


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


def varrer(bm, pts, raios, lados=12, tampas=(False, False)):
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
    u = Vector(u).normalized()
    s = u.cross(Z)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    return s, s.cross(u).normalized() if abs(u.z) > 0.9 else Z.copy()


def chapa_arco(bm, c, u, r_in, esp, larg, a0, a1, n=14):
    """Chapa curva em volta do eixo u (abraçadeira, cinta); ângulo medido de s para cima (ver base_lat)."""
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


def anel_cinta(bm, c, r_in, esp, larg, n=28):
    """Cinta fechada em volta de um eixo vertical."""
    c = Vector(c)
    lin = []
    for i in range(n):
        a = 2 * PI * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        lin.append([bm.verts.new(c + d * rr + Z * w) for rr in (r_in, r_in + esp) for w in (-larg / 2, larg / 2)])
    for i in range(n):
        A, B = lin[i], lin[(i + 1) % n]
        for (p, q) in ((0, 1), (3, 2), (2, 0), (1, 3)):
            bm.faces.new((A[p], A[q], B[q], B[p]))


def rot_cols(x, y, z):
    return Matrix((Vector(x), Vector(y), Vector(z))).transposed()


def base_parede(n):
    """Base do plano de uma parede de normal n (horizontal): t1 horizontal, t2 para cima."""
    n = Vector(n).normalized()
    t1 = Z.cross(n)
    if t1.length < 1e-4:
        t1 = Vector((1, 0, 0))
    t1.normalize()
    return t1, n.cross(t1).normalized()


def decal(bm, c, n, r, nv=13, jit=0.45, alongar=1.0, gira=0.0):
    """Mancha irregular plana sobre uma superfície de normal n."""
    c, n = Vector(c), Vector(n).normalized()
    t1, t2 = base_parede(n)
    if abs(n.z) > 0.9:
        t1, t2 = Vector((1, 0, 0)), Vector((0, 1, 0))
    t1, t2 = t1 * math.cos(gira) + t2 * math.sin(gira), t2 * math.cos(gira) - t1 * math.sin(gira)
    vs, uvs = [], []
    for i in range(nv):
        a = 2 * PI * i / nv
        f = 1 + jit * (random.random() - 0.5) + 0.25 * math.sin(3 * a + random.random())
        vs.append(bm.verts.new(c + (t1 * math.cos(a) * alongar + t2 * math.sin(a)) * r * f))
        uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    fc = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.verify()
    for lp in fc.loops:
        lp[uvl].uv = uvs[vs.index(lp.vert)]


def escorrido(bm, c, n, L, w=0.008):
    """Escorrido vertical (ferrugem, óleo, ácido) descendo de c pela superfície de normal horizontal n."""
    c, n = Vector(c), Vector(n).normalized()
    t1, _ = base_parede(n)
    rot = rot_cols(t1, n, Z)
    k = 4
    for i in range(k):                                                   # afina para baixo
        z0 = L * i / k
        caixa(bm, c - Z * (z0 + L / k / 2) + n * 0.0006, (w * (1 - 0.18 * i), 0.0012, L / k + 0.002), rot)


def rachadura_plana(bm, c, n, L, dir0=-PI / 2, n_seg=7, larg=0.0028):
    """Trinca em zigue-zague sobre o plano de normal n (dir0: ângulo no plano, -π/2 = para baixo)."""
    c, n = Vector(c), Vector(n).normalized()
    t1, t2 = base_parede(n)
    if abs(n.z) > 0.9:
        t1, t2 = Vector((1, 0, 0)), Vector((0, 1, 0))
    p = c.copy()
    for i in range(n_seg):
        a = dir0 + random.uniform(-0.7, 0.7)
        d = t1 * math.cos(a) + t2 * math.sin(a)
        q = p + d * L / n_seg
        u = (q - p).normalized()
        caixa(bm, (p + q) / 2 + n * 0.0007, ((q - p).length + larg, 0.0014, larg * (1 - 0.08 * i)), rot_cols(u, n, u.cross(n)))
        p = q


def cat_pts(a, b, sag, n=24):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Z * sag * 4 * (i / n) * (1 - i / n) for i in range(n + 1)]


def ruido_vec(esc=1.0):
    return Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * esc


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat():
    m = bpy.data.materials.new('Cristal da torre')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.2, 0.03, 0.5, 1)
    b.inputs['Roughness'].default_value = 0.14
    b.inputs['IOR'].default_value = 1.55
    b.inputs['Transmission Weight'].default_value = 0.45
    b.inputs['Emission Color'].default_value = (0.45, 0.1, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 3.0
    ru = mats.no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 6.0})
    bump = mats.no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def halo_mat():
    """Sujeira em volta das poças: escurece o chão e some em degradê radial."""
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


def tinta_mat():
    """Tinta de estêncil gasta: branca encardida, falhando em manchas."""
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


def refletiva_mat():
    """Faixa refletiva vermelha e branca, gasta: listras diagonais, encardida e falhando (alfa por ruído)."""
    m = bpy.data.materials.new('Faixa refletiva')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    tc = no(nt, 'ShaderNodeTexCoord')
    wave = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL', wave_profile='SAW')
    wave.inputs['Scale'].default_value = 9.0
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    corte = no(nt, 'ShaderNodeMath', operation='GREATER_THAN')
    corte.inputs[1].default_value = 0.5
    nt.links.new(wave.outputs['Fac'], corte.inputs[0])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.42, 0.035, 0.025, 1)
    mix.inputs[7].default_value = (0.7, 0.68, 0.6, 1)
    nt.links.new(corte.outputs['Value'], mix.inputs[0])
    suj = no(nt, 'ShaderNodeTexNoise', **{'Scale': 25.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], suj.inputs['Vector'])
    enc = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    enc.inputs[0].default_value = 0.7
    nt.links.new(mix.outputs[2], enc.inputs[6])
    nt.links.new(suj.outputs['Color'], enc.inputs[7])
    nt.links.new(enc.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Coat Weight'].default_value = 0.4
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.36, 'From Max': 0.5, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(suj.outputs['Fac'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def decal_mat(nome, cor, rough, metal=0.0, borda=0.5):
    """Decalque com borda esfumada e rasgada (alfa pela distância ao centro do UV + ruído)."""
    m = mats.material(nome, cor, metal, rough, pintura=False, sujeira=0.3, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = no(nt, 'ShaderNodeTexCoord')
    d = no(nt, 'ShaderNodeVectorMath', operation='DISTANCE')
    d.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(tc.outputs['UV'], d.inputs[0])
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.4
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(d.outputs['Value'], soma.inputs[2])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.25 + 0.2 * (1 - borda), 'From Max': 0.62, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(soma.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def brilho_mat(nome, cor, forca, alfa):
    """Halo de arco: emissão translúcida, mais densa no miolo do tubo (peso de camada)."""
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
    """Camada de uso: poeira no que olha para cima, lama embaixo (até ~0,17 m), fuligem e amassados."""
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
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.03, 'From Max': 0.19, 'To Min': 1.0, 'To Max': 0.0})
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


def aspero(m, forca=0.6, escala=40.0):
    """Relevo granulado (pedra, concreto, argamassa)."""
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 8.0, 'Roughness': 0.7})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': forca})
    bump.inputs['Distance'].default_value = 0.01
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])


M = base3d.M
M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.4),
    'trafo': mats.material('Cinza do transformador', (0.24, 0.27, 0.26), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.7),
    'capacitor': mats.material('Azul dos capacitores', (0.06, 0.1, 0.16), 0, 0.45, desgaste=0.9, sujeira=1.0, ferrugem=0.5),
    'maquina': mats.material('Casco da máquina', (0.13, 0.135, 0.13), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'oxido': mats.material('Primer vermelho', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'galv': mats.material('Galvanizado', (0.5, 0.52, 0.53), 1.0, 0.5, pintura=False, ferrugem=0.9, sujeira=0.9),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'aluminio': mats.material('Alumínio', (0.72, 0.73, 0.74), 1.0, 0.34, pintura=False, sujeira=0.7, ferrugem=0.0),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'cobre_velho': mats.material('Cobre oxidado', (0.42, 0.24, 0.13), 1.0, 0.5, pintura=False, sujeira=1.0, ferrugem=0.0),
    'zinabre': decal_mat('Zinabre', (0.2, 0.42, 0.32), 0.8, borda=0.4),
    'latao': mats.material('Latão', (0.75, 0.55, 0.2), 1.0, 0.35, pintura=False, sujeira=0.8),
    'cabo': mats.material('Condutor de alumínio', (0.36, 0.37, 0.37), 0.8, 0.5, pintura=False, sujeira=0.8),
    'cabo_aco': mats.material('Cabo de aço', (0.3, 0.3, 0.3), 1.0, 0.5, pintura=False, sujeira=0.9, ferrugem=0.6),
    'porcelana': mats.material('Porcelana', (0.38, 0.15, 0.07), 0, 0.12, pintura=False, sujeira=0.7, desgaste=0.0),
    'porcelana_crua': mats.material('Porcelana quebrada', (0.78, 0.75, 0.68), 0, 0.85, pintura=False, sujeira=0.3, desgaste=0.0),
    'polimero': mats.material('Polímero cinza', (0.28, 0.3, 0.29), 0, 0.6, pintura=False, sujeira=0.9, desgaste=0.0),
    'resina': mats.material('Fenolite envernizado', (0.22, 0.09, 0.03), 0, 0.22, pintura=False, sujeira=0.8, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
    'cabo_verm': mats.material('Cabo vermelho', (0.32, 0.025, 0.02), 0, 0.55, pintura=False, sujeira=0.8, desgaste=0.0),
    'fita': mats.material('Fita isolante preta', (0.012, 0.012, 0.014), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'fita_azul': mats.material('Fita azul', (0.02, 0.06, 0.3), 0, 0.35, pintura=False, sujeira=0.8, desgaste=0.0),
    'fita_prata': mats.material('Fita prata', (0.45, 0.46, 0.46), 0.6, 0.45, pintura=False, sujeira=1.0, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.36, 0.35, 0.33), 0, 0.92, sujeira=0.8, desgaste=0.0),
    'concreto_poste': mats.material('Concreto do poste', (0.42, 0.41, 0.39), 0, 0.88, sujeira=0.9, desgaste=0.0, ferrugem=0.25),
    'concreto_novo': decal_mat('Remendo de argamassa', (0.36, 0.35, 0.32), 0.9, borda=0.8),
    'quebra_d': decal_mat('Lasca de pedra', (0.36, 0.34, 0.3), 0.95, borda=0.9),
    'acido_d': decal_mat('Ácido (mancha)', (0.16, 0.19, 0.025), 0.25, borda=0.6),
    'musgo_d': decal_mat('Musgo (mancha)', (0.04, 0.075, 0.015), 0.95, borda=0.3),
    'brita': mats.material('Brita', (0.2, 0.19, 0.18), 0, 0.85, pintura=False, sujeira=0.6, desgaste=0.0),
    'pedra1': mats.material('Pedra cinza', (0.19, 0.185, 0.17), 0, 0.85, pintura=False, sujeira=1.0, desgaste=0.0, ferrugem=0.15),
    'pedra2': mats.material('Pedra parda', (0.2, 0.16, 0.12), 0, 0.85, pintura=False, sujeira=1.0, desgaste=0.0, ferrugem=0.25),
    'pedra3': mats.material('Pedra escura', (0.1, 0.1, 0.095), 0, 0.8, pintura=False, sujeira=1.0, desgaste=0.0),
    'argamassa': mats.material('Argamassa', (0.26, 0.24, 0.2), 0, 0.95, pintura=False, sujeira=1.0, desgaste=0.0),
    'quebra': mats.material('Pedra recém-quebrada', (0.44, 0.42, 0.38), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'musgo': mats.material('Musgo', (0.05, 0.1, 0.02), 0, 0.95, pintura=False, sujeira=0.5, desgaste=0.0),
    'lama': decal_mat('Lama', (0.07, 0.05, 0.03), 0.55, borda=0.4),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.015, 0.012, 0.009), 0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'fenda': mats.material('Fenda', (0.012, 0.01, 0.009), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'queimado': decal_mat('Queimado de arco', (0.012, 0.011, 0.012), 0.75, borda=0.6),
    'chamusco': decal_mat('Chamuscado', (0.045, 0.035, 0.025), 0.8, borda=0.3),
    'crosta': mats.material('Crosta de ferrugem', (0.26, 0.085, 0.025), 0, 0.95, pintura=False, sujeira=0.7, desgaste=0.0),
    'escorre': mats.material('Escorrido de ferrugem', (0.24, 0.09, 0.03), 0, 0.85, pintura=False, sujeira=0.3, desgaste=0.0),
    'crosta_branca': mats.material('Crosta de eletrólito', (0.7, 0.72, 0.62), 0, 0.95, pintura=False, sujeira=0.6, desgaste=0.0),
    'acido': mats.material('Ácido das aranhas', (0.14, 0.17, 0.02), 0, 0.2, pintura=False, sujeira=0.4, desgaste=0.0),
    'mostrador': mats.material('Plaqueta', (0.62, 0.62, 0.58), 0.6, 0.45, pintura=False, sujeira=1.0, desgaste=0.0),
    'vidro_escuro': mats.material('Lente', (0.01, 0.01, 0.012), 0, 0.05, pintura=False, sujeira=0.2, desgaste=0.0),
    'halo': halo_mat(),
    'tinta': tinta_mat(),
    'refletiva': refletiva_mat(),
    'listras': base3d.listras_mat(),
    'cristal': cristal_mat(),
    'violeta': emissivo('Campo violeta', (0.55, 0.12, 1.0), 9.0),
    'arco': emissivo('Arco', (0.8, 0.62, 1.0), 9.0),
    'arco_brilho': brilho_mat('Halo do arco', (0.5, 0.18, 1.0), 4.0, 0.3),
    'faisca': emissivo('Faísca', (1.0, 0.72, 0.4), 40.0),
    'led_v': emissivo('LED violeta', (0.6, 0.15, 1.0), 14.0),
    'led_a': emissivo('LED âmbar', (1.0, 0.45, 0.05), 12.0),
    'led_r': emissivo('LED vermelho', (1.0, 0.06, 0.03), 14.0),
})
for n in M['chao'].node_tree.nodes:
    if n.type == 'AMBIENT_OCCLUSION':
        n.only_local = True
for chave, kw in (('amarelo', {}), ('grafite', {}), ('trafo', dict(amassado=0.15)), ('capacitor', {}),
                  ('maquina', dict(amassado=0.15)), ('oxido', {}), ('aco', dict(amassado=0.0, fuligem=0.5)),
                  ('galv', dict(amassado=0.0)), ('ferro', dict(amassado=0.1)), ('aluminio', dict(amassado=0.1)),
                  ('concreto', dict(amassado=0.0, fuligem=0.6)), ('concreto_poste', dict(amassado=0.0, fuligem=0.7)),
                  ('concreto_novo', dict(amassado=0.0, fuligem=0.3)), ('borracha', dict(amassado=0.0, fuligem=0.0)),
                  ('pedra1', dict(amassado=0.25)), ('pedra2', dict(amassado=0.25)), ('pedra3', dict(amassado=0.25)),
                  ('argamassa', dict(amassado=0.0)), ('porcelana', dict(amassado=0.0, poeira=0.6, fuligem=0.5)),
                  ('polimero', dict(amassado=0.0)), ('cobre', dict(amassado=0.0, poeira=0.5)),
                  ('cobre_velho', dict(amassado=0.0)), ('cabo', dict(amassado=0.0, poeira=0.4))):
    rustico(M[chave], **kw)
for chave, f, e in (('pedra1', 0.7, 35), ('pedra2', 0.7, 35), ('pedra3', 0.7, 35), ('argamassa', 0.9, 60),
                    ('concreto', 0.45, 50), ('concreto_poste', 0.4, 60), 
                    ('musgo', 1.0, 90), ('crosta', 1.0, 120), ('quebra', 0.8, 50), ('brita', 0.6, 60)):
    aspero(M[chave], f, e)
CRISTAL_EMIS = next(n for n in M['cristal'].node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Emission Strength']
VIOLETA_EMIS = M['violeta'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


# ------------------------------------------------------------------ peça: geometria local → mundo
class Peca:
    def __init__(s, nome, cx, cy, ang=0.0):
        s.nome = nome
        s.M = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(ang, 4, 'Z')
        s.Rm = Matrix.Rotation(ang, 3, 'Z')
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
        s.bms = {}


ANIM = []          # funções f(q, fr) que posicionam e gravam chaves


def chave(o, prop, q):
    o.keyframe_insert(prop, frame=q)


def luz(nome, cor, energia, loc, raio=0.03):
    d = bpy.data.lights.new(nome, 'POINT')
    d.color = cor
    d.energy = energia
    d.shadow_soft_size = raio
    o = bpy.data.objects.new(nome, d)
    sc.collection.objects.link(o)
    o.location = loc
    return o


def cabo(nome, a, b, sag, r=0.0055, mat='cabo', amp=0.05, freq=1, fitas=(), pts=None, lados=10):
    """Cabo em catenária (ou pelos pontos dados) como objeto próprio com origem em a; balança girando em torno do
    eixo a→b (as pontas ficam paradas). fitas: (t0, t1, material) = remendo de fita com ponta solta."""
    a, b = Vector(a), Vector(b)
    if pts is None:
        pts = cat_pts(a, b, sag, max(12, int((b - a).length * 16)))
    rel = [Vector(p) - a for p in pts]
    bm = bmesh.new()
    varrer(bm, rel, r, lados)
    o = suavizar(obj(nome, bm, mat))
    o.location = a
    o.rotation_mode = 'QUATERNION'
    for (t0, t1, fm) in fitas:
        n = len(rel) - 1
        i0 = int(t0 * n)
        i1 = max(int(t1 * n), i0 + 1)
        seg = [rel[i0].lerp(rel[i0 + 1], 0.3)] + rel[i0 + 1:i1] + [rel[i1 - 1].lerp(rel[i1], 0.7)]
        bf = bmesh.new()
        varrer(bf, seg, r * 1.75, lados, tampas=(True, True))
        u = (seg[-1] - seg[-2]).normalized()
        s = u.cross(Z)
        if s.length < 1e-3:
            s = Vector((1, 0, 0))
        s.normalize()
        ponta = seg[-1] + Z * (-r * 1.7)                                     # ponta da fita descolada, caída
        caixa(bf, ponta + Z * -0.012 + u * 0.004, (0.013, 0.0016, 0.026), rot_cols(s, s.cross(Z).normalized(), Z))
        suavizar(obj(nome + '_fita', bf, fm, o))
    eixo = (b - a).normalized()
    fase = random.random()
    if amp > 0:
        def f(q, fr, o=o, eixo=eixo, amp=amp, fase=fase, freq=freq):
            o.rotation_quaternion = Quaternion(eixo, amp * math.sin(2 * PI * (freq * fr + fase)))
            chave(o, 'rotation_quaternion', q)
        ANIM.append(f)
    return o


def raio_pts(a, b, desvio, prof=4):
    """Raio por deslocamento do ponto médio: cada nível divide os trechos e empurra o meio para o lado."""
    a, b = Vector(a), Vector(b)
    pts = [a, b]
    d = desvio * (b - a).length
    for _ in range(prof):
        novo = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            u = (q - p).normalized()
            v = ruido_vec(1.0)
            v -= u * v.dot(u)
            novo += [(p + q) / 2 + v * d, q]
        pts = novo
        d *= 0.52
    return pts


def arco_obj(nome, a, b, desvio, r=0.0032, n=9, galhos=2, mat='arco'):
    """Raio de energia fractal de a até b, afinando, com galhos e halo violeta translúcido."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    pts = raio_pts(a, b, desvio * 1.4, 5 if L < 0.6 else 7)
    ramos = [(pts, r)]
    for g in range(galhos):
        k = random.randint(len(pts) // 5, len(pts) * 3 // 4)
        p0 = pts[k]
        d = ((b - a).normalized() + ruido_vec(0.9)).normalized() * L * random.uniform(0.15, 0.35)
        ramos.append((raio_pts(p0, p0 + d, 0.3, 3), r * 0.5))
    bm = bmesh.new()
    for lst, rr in ramos:
        n_ = len(lst) - 1
        for i, (p, q) in enumerate(zip(lst, lst[1:])):
            tubo(bm, p, q, rr * (1 - 0.5 * i / n_), 5)
    nf = len(bm.faces)
    for lst, rr in ramos[:1]:
        for i, (p, q) in enumerate(zip(lst[::2], lst[2::2])):
            tubo(bm, p, q, rr * 2.6 * (1 - 0.4 * i / len(lst) * 2), 8)
    for f in list(bm.faces)[nf:]:
        f.material_index = 1
    o = obj(nome, bm, mat)
    o.data.materials.append(M['arco_brilho'])
    o.visible_shadow = False
    return o


def pisca(objs, prob, sem, fixo=None):
    """Liga/desliga objetos (arcos) quadro a quadro, sorteio determinístico; fixo: {quadro: índice visível}."""
    def f(q, fr, objs=objs, prob=prob, sem=sem, fixo=fixo):
        rr = random.Random(q * 131 + sem)
        vis = rr.random() < prob
        k = rr.randrange(len(objs))
        if fixo and q in fixo:
            vis, k = True, fixo[q]
        for i, o in enumerate(objs):
            o.hide_render = not (vis and i == k)
            chave(o, 'hide_render', q)
    ANIM.append(f)


def faiscas(nome, pool_n, eventos, vel, espalha, vida=9, chao=0.0):
    """Faíscas: pequenas esferas brilhantes que nascem num evento (quadro, ponto, direção) e caem em arco."""
    pool = []
    for i in range(pool_n):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0035)
        o = obj('%s_%d' % (nome, i), bm, 'faisca')
        o.rotation_mode = 'QUATERNION'
        pool.append(o)
    plano = {o: [] for o in pool}
    k = 0
    rr = random.Random(pool_n * 17)
    for q0, pt, d in eventos:
        for _ in range(pool_n // max(1, len(eventos)) + 1):
            o = pool[k % pool_n]
            k += 1
            v = Vector(d).normalized() * vel + Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))) * espalha
            plano[o].append((q0 + rr.randint(0, 2), Vector(pt), v, rr.randint(vida // 2, vida)))

    def f(q, fr, plano=plano):
        for o, lst in plano.items():
            vivo = None
            for (q0, pt, v, vd) in lst:
                if q0 <= q < q0 + vd:
                    vivo = (q0, pt, v, vd)
            if vivo:
                q0, pt, v, vd = vivo
                t = (q - q0) / FPS
                p = pt + v * t + Z * (-4.9 * t * t)
                vv = v + Z * (-9.8 * t)
                if p.z < chao + 0.003:
                    p.z = chao + 0.003
                o.location = p
                s = max(0.4, 1 - (q - q0) / vd)
                o.scale = (s, s, s * (1 + min(3.0, vv.length * 0.6)))
                o.rotation_quaternion = vv.normalized().to_track_quat('Z', 'Y') if vv.length > 1e-3 else Quaternion()
                o.hide_render = False
            else:
                o.hide_render = True
            for c in ('location', 'scale', 'hide_render', 'rotation_quaternion'):
                chave(o, c, q)
    ANIM.append(f)
    return pool


SEG = dict(a=(0, 1, 1, 0), b=(1, 1, 0, 1), c=(1, 0, 0, 1), d=(0, 0, 1, 0), e=(0, 0, 0, 1), f=(0, 1, 0, 1), g=(0, 0.5, 1, 0))
DIG = ['abcdef', 'bc', 'abged', 'abgcd', 'fgbc', 'afgcd', 'afgedc', 'abc', 'abcdefg', 'abfgcd']


def serie_plana(bm, c, n, alt=0.025, nd=6, apagado=0.35, horiz=None):
    """Número de série em estêncil (7 segmentos) sobre o plano de normal n; parte apagada."""
    c, n = Vector(c), Vector(n).normalized()
    t1, t2 = base_parede(n)
    if horiz is not None:
        t1 = Vector(horiz).normalized()
        t2 = n.cross(t1).normalized()
    rot = rot_cols(t1, t2, n)
    larg = alt * 0.55
    texto = [random.choice(DIG) for _ in range(nd)]
    texto.insert(2, 'g')
    for i, dg in enumerate(texto):
        x0 = (i - len(texto) / 2) * larg * 1.5
        for sg in dg:
            if random.random() < apagado:
                continue
            hx, hy, vx, vy = SEG[sg]
            if sg in 'adg':
                p = Vector((x0 + larg / 2, alt * (hy - 0.5), 0))
                tam = (larg * 0.8, alt * 0.12, 0.0012)
            else:
                p = Vector((x0 + larg * hx, alt * (0.25 if sg in 'bf' else -0.25), 0))
                tam = (larg * 0.16, alt * 0.42, 0.0012)
            caixa(bm, c + n * 0.0008 + rot @ p, tam, rot)


def ninho(P, c, n, r=0.018, k=7, esc=0.07):
    """Ninho de ferrugem: bolhas de crosta em volta de c e escorrido para baixo."""
    c = Vector(c)
    for i in range(k):
        pedra(P.B('crosta'), c + ruido_vec(r) * Vector((1, 1, 0.6)), random.uniform(0.004, 0.009), 0.55)
    if esc > 0 and abs(Vector(n).z) < 0.5:
        escorrido(P.B('escorre'), c - Z * 0.005, n, esc, 0.012)


def porca(bm, c, eixo, r=0.011, h=0.009, arruela=True):
    eixo = Vector(eixo).normalized()
    cil(bm, Vector(c) + eixo * h / 2, r, h, eixo, lados=6)
    if arruela:
        cil(bm, Vector(c), r * 1.35, 0.002, eixo, lados=14)


def saia(bm, c, r_in, r_out, h, a0=0.0, a1=2 * PI, n=28, bm_lasca=None):
    """Saia de isolador (disco cônico). Com a0..a1 parcial: saia lascada, a quebra em porcelana crua."""
    c = Vector(c)
    perfil = [(r_in, h), (r_out, h * 0.22), (r_out * 0.985, 0.0), (r_in, 0.005)]
    cheio = abs(a1 - a0 - 2 * PI) < 1e-6
    m = n if cheio else n + 1
    aneis = []
    for i in range(m):
        a = a0 + (a1 - a0) * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(c + d * rr + Z * zz) for rr, zz in perfil])
    seq = list(zip(aneis, aneis[1:])) + ([(aneis[-1], aneis[0])] if cheio else [])
    for A, B in seq:
        for j in range(4):
            bm.faces.new((A[j], B[j], B[(j + 1) % 4], A[(j + 1) % 4]))
    if not cheio and bm_lasca is not None:
        for L, sgn in ((aneis[0], 1), (aneis[-1], -1)):
            vs = []
            for k, v in enumerate(L):
                p = v.co + Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)) * 0.0015 * (k in (1, 2))
                vs.append(bm_lasca.verts.new(p))
            bm_lasca.faces.new(vs)



# ================================================================== PARA-RAIOS: materiais extras
def revenido_mat(nome, z0, z1):
    """Aço revenido pelo calor do raio: palha → bronze → roxo → azul → cinza queimado na ponta (pela altura z)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Metallic'].default_value = 1.0
    geo = no(nt, 'ShaderNodeNewGeometry')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    zz = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    zz.inputs[1].default_value = (z1 - z0) * 0.12
    nt.links.new(ru.outputs['Fac'], zz.inputs[0])
    nt.links.new(sp.outputs['Z'], zz.inputs[2])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z1})
    nt.links.new(zz.outputs['Value'], mr.inputs['Value'])
    cr = no(nt, 'ShaderNodeValToRGB')
    el = cr.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.42, 0.42, 0.42, 1)
    el[1].position, el[1].color = 1.0, (0.05, 0.045, 0.05, 1)
    for p, c in ((0.25, (0.4, 0.34, 0.2, 1)), (0.42, (0.33, 0.2, 0.1, 1)), (0.58, (0.2, 0.09, 0.2, 1)),
                 (0.72, (0.09, 0.11, 0.24, 1)), (0.86, (0.08, 0.08, 0.09, 1))):
        e = el.new(p)
        e.color = c
    nt.links.new(mr.outputs['Result'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.3, 'To Max': 0.75})
    nt.links.new(mr.outputs['Result'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    return m


def patina(m, forca=1.0):
    """Cobre esverdeado: zinabre em manchas (mais embaixo e nas frestas), fosco e não metálico onde pega."""
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 22.0, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.6, 'To Min': 0.0, 'To Max': forca})
    nt.links.new(ru.outputs['Fac'], fr.inputs['Value'])
    vd = no(nt, 'ShaderNodeTexNoise', **{'Scale': 140.0, 'Detail': 3.0})
    nt.links.new(geo.outputs['Position'], vd.inputs['Vector'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.17, 0.36, 0.27, 1)
    cor.inputs[7].default_value = (0.32, 0.5, 0.38, 1)
    nt.links.new(vd.outputs['Fac'], cor.inputs[0])
    c = no(nt, 'ShaderNodeMix', data_type='RGBA')
    nt.links.new(fr.outputs['Result'], c.inputs[0])
    if lk:
        nt.links.new(lk.from_socket, c.inputs[6])
    nt.links.new(cor.outputs[2], c.inputs[7])
    nt.links.new(c.outputs[2], b.inputs['Base Color'])
    for nome_in, val in (('Metallic', 0.0), ('Roughness', 0.9)):
        lk2 = next((l for l in nt.links if l.to_socket == b.inputs[nome_in]), None)
        mx = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        nt.links.new(fr.outputs['Result'], mx.inputs[0])
        if lk2:
            nt.links.new(lk2.from_socket, mx.inputs[2])
        else:
            mx.inputs[2].default_value = b.inputs[nome_in].default_value
        mx.inputs[3].default_value = val
        nt.links.new(mx.outputs[0], b.inputs[nome_in])
    return m


def molhado(m, f=0.35):
    """Multiplica a rugosidade (chão molhado de chuva)."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = b.inputs['Roughness']
    mul = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    mul.inputs[1].default_value = f
    if ent.is_linked:
        nt.links.new(ent.links[0].from_socket, mul.inputs[0])
    else:
        mul.inputs[0].default_value = ent.default_value
    nt.links.new(mul.outputs[0], ent)
    return m


def chao_chuva_mat():
    """Chão de terra batida encharcado: poças lisas e espelhadas nas baixadas, lama no resto."""
    m = mats.material('Chão molhado', (0.045, 0.04, 0.035), 0, 0.75, pintura=False, sujeira=0.3, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.6, 'Detail': 8.0, 'Distortion': 0.6})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    po = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.52, 'From Max': 0.57, 'To Min': 0.62, 'To Max': 0.05})
    nt.links.new(ru.outputs['Fac'], po.inputs['Value'])
    nt.links.new(po.outputs['Result'], b.inputs['Roughness'])
    gr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], gr.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    nt.links.new(gr.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def terra_chao_mat():
    """Terra queimada pelo raio: preto-fosco no miolo, degradê com ruído até sumir."""
    m = halo_mat()
    m.name = 'Terra queimada (chão)'
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.012, 0.01, 0.009, 1)
    b.inputs['Roughness'].default_value = 0.95
    for n in m.node_tree.nodes:
        if n.type == 'MAP_RANGE':
            n.inputs['To Min'].default_value = 0.92
    return m


def chuva_mat():
    m = bpy.data.materials.new('Chuva')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.75, 0.78, 0.85, 1)
    ag.inputs['Roughness'].default_value = 0.2
    ag.inputs['Emission Color'].default_value = (0.55, 0.55, 0.75, 1)
    ag.inputs['Emission Strength'].default_value = 0.0
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.12
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(ag.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def ceu_tempestade():
    """Céu de tempestade: nuvens baixas escuras em camadas; clarão violeta-branco em volta do raio."""
    w = bpy.data.worlds.new('Tempestade')
    nt = w.node_tree
    no = mats.no
    bg = nt.nodes['Background']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.2, 'Detail': 12.0, 'Roughness': 0.62})
    ru.noise_dimensions = '3D'
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, 3.2)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    cr = no(nt, 'ShaderNodeValToRGB')
    el = cr.color_ramp.elements
    el[0].position, el[0].color = 0.35, (0.004, 0.0045, 0.007, 1)
    el[1].position, el[1].color = 0.72, (0.045, 0.05, 0.068, 1)
    nt.links.new(ru.outputs['Fac'], cr.inputs['Fac'])
    # clarão: direção do raio (ponto alto no céu) → borrão grande
    dt = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    dt.inputs[1].default_value = Vector((-0.12, 0.62, 0.78)).normalized()
    nt.links.new(tc.outputs['Generated'], dt.inputs[0])
    pw = no(nt, 'ShaderNodeMath', operation='POWER')
    pw.inputs[1].default_value = 6.0
    nt.links.new(dt.outputs['Value'], pw.inputs[0])
    cl = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    cl.name = 'clarao'
    cl.inputs[1].default_value = 0.0
    nt.links.new(pw.outputs['Value'], cl.inputs[0])
    cm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')                 # o clarão acende as nuvens claras
    nt.links.new(cl.outputs['Value'], cm.inputs[0])
    nt.links.new(ru.outputs['Fac'], cm.inputs[1])
    fl = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='ADD')
    fl.inputs[7].default_value = (0.5, 0.42, 0.75, 1)
    nt.links.new(cm.outputs['Value'], fl.inputs[0])
    nt.links.new(cr.outputs['Color'], fl.inputs[6])
    nt.links.new(fl.outputs[2], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    return w, cl.inputs[1]


M.update({
    'revenido_pr': revenido_mat('Revenido (para-raios)', 3.55, 3.88),
    'revenido_pc': revenido_mat('Revenido (garras)', 4.0, 4.16),
    'derretido': mats.material('Metal fundido', (0.07, 0.065, 0.075), 1.0, 0.45, pintura=False, sujeira=0.4, desgaste=0.0),
    'descida': patina(mats.material('Descida de cobre', (0.72, 0.38, 0.22), 1.0, 0.36, pintura=False, sujeira=0.9)),
    'fita_cobre': patina(mats.material('Fita de cobre', (0.6, 0.33, 0.2), 1.0, 0.45, pintura=False, sujeira=1.0), 1.0),
    'cobre_bob': patina(mats.material('Cobre da bobina', (0.78, 0.4, 0.22), 1.0, 0.3, pintura=False, sujeira=0.8), 0.6),
    'terra_q': decal_mat('Terra queimada', (0.018, 0.015, 0.014), 0.92, borda=0.25),
    'terra_poco': mats.material('Terra do poço', (0.045, 0.035, 0.028), 0, 0.95, pintura=False, sujeira=1.0, desgaste=0.0),
    'fulgurito': mats.material('Fulgurito', (0.05, 0.06, 0.05), 0, 0.12, pintura=False, sujeira=0.6, desgaste=0.0),
    'lich': mats.material('Lichtenberg queimado', (0.01, 0.009, 0.009), 0, 0.85, pintura=False, sujeira=0.0, desgaste=0.0),
    'raio': emissivo('Raio', (0.85, 0.8, 1.0), 120.0),
    'raio_halo': brilho_mat('Halo do raio', (0.55, 0.38, 1.0), 22.0, 0.55),
    'descarga': emissivo('Descarga na descida', (0.8, 0.7, 1.0), 0.0),
    'descarga_halo': brilho_mat('Halo da descida', (0.55, 0.3, 1.0), 0.0, 0.5),
    'carga': emissivo('Carga do capacitor', (0.55, 0.15, 1.0), 2.0),
    'plasma': emissivo('Plasma', (0.95, 0.9, 1.0), 200.0),
    'gota_metal': emissivo('Gota de metal fundido', (1.0, 0.55, 0.15), 30.0),
    'chuva': chuva_mat(),
    'terra_chao': terra_chao_mat(),
    'chao_chuva': chao_chuva_mat(),
    'cristal_pc': cristal_mat(),
})
M['cristal_pc'].name = 'Cristal do para-raios'
for chave_m, kw in (('descida', dict(amassado=0.0, poeira=0.4)), ('fita_cobre', dict(amassado=0.0)),
                    ('cobre_bob', dict(amassado=0.0, poeira=0.3)), ('terra_poco', dict(amassado=0.3, poeira=0.0, lama=0.0))):
    rustico(M[chave_m], **kw)
aspero(M['terra_poco'], 1.0, 40)
aspero(M['fulgurito'], 0.6, 30)
aspero(M['derretido'], 0.5, 80)
EM = lambda k: next(n for n in M[k].node_tree.nodes if n.type in ('BSDF_PRINCIPLED', 'EMISSION')).inputs[
    'Emission Strength' if k in ('descarga', 'carga', 'cristal_pc') else 'Strength']
DESC_EMIS = EM('descarga')
DESC_HALO = EM('descarga_halo')
CARGA_EMIS = EM('carga')
CRIS_PC = EM('cristal_pc')
GRUPOS = {}

# linha do tempo do raio (quadro → intensidade): líder, descarga de retorno, religamento, cauda
RAIO_T = {11: 0.25, 12: 1.0, 13: 1.0, 14: 0.35, 15: 0.85, 16: 0.3, 17: 0.12}
F_RAIO = 13
F_CALMO = 60


def forca(q):
    return RAIO_T.get(q, 0.0)


def carga_nivel(q):
    """LEDs acesos (0..10): sobe com o raio, escorre devagar para o acumulador."""
    if q < 12:
        return 3 + int(2 * (1 - q / 12))
    if q <= 17:
        return min(10, 3 + int((q - 11) * 1.6))
    return max(3, 10 - int((q - 17) / 79 * 8))


class Acc:
    """Malha montada por listas (rápida para milhares de peças: Lichtenberg, raio, chuva)."""
    def __init__(s):
        s.v, s.f = [], []

    def faixa(s, p, q, w, dz=0.0):
        """Faixa plana horizontal de p a q (largura w)."""
        p, q = Vector(p), Vector(q)
        u = (q - p).normalized()
        n = Z.cross(u).normalized() * w / 2
        p = p - u * w / 2
        q = q + u * w / 2
        i = len(s.v)
        s.v += [tuple(p - n), tuple(q - n), tuple(q + n), tuple(p + n)]
        s.f.append((i, i + 1, i + 2, i + 3))

    def prisma(s, a, b, r, n=5, r2=None):
        a, b = Vector(a), Vector(b)
        u = (b - a)
        if u.length < 1e-6:
            return
        u.normalize()
        e1 = u.orthogonal().normalized()
        e2 = u.cross(e1)
        r2 = r if r2 is None else r2
        i = len(s.v)
        for k in range(n):
            ang = 2 * PI * k / n
            d = e1 * math.cos(ang) + e2 * math.sin(ang)
            s.v.append(tuple(a + d * r))
            s.v.append(tuple(b + d * r2))
        for k in range(n):
            k2 = (k + 1) % n
            s.f.append((i + 2 * k, i + 2 * k2, i + 2 * k2 + 1, i + 2 * k + 1))

    def objeto(s, nome, mat, mw=None):
        me = bpy.data.meshes.new(nome)
        me.from_pydata(s.v, [], s.f)
        me.update()
        o = bpy.data.objects.new(nome, me)
        sc.collection.objects.link(o)
        o.data.materials.append(M[mat])
        if mw is not None:
            o.matrix_world = mw
        return o


def queimadura(P, c, n, r, mat='queimado'):
    """Marca de queimado irregular: cacho de manchas pequenas, puxado para cima (fuligem do arco)."""
    c, n = Vector(c), Vector(n).normalized()
    for k in range(4):
        off = Z * random.uniform(-0.3, 1.4) * r + Z.cross(n).normalized() * random.uniform(-0.5, 0.5) * r \
            if abs(n.z) < 0.9 else ruido_vec(0.6 * r) * Vector((1, 1, 0))
        decal(P.B(mat if k else 'chamusco'), c + off + n * 0.0003 * k, n, r * random.uniform(0.35, 0.7), nv=17, jit=0.9,
              alongar=random.uniform(0.35, 0.7), gira=random.uniform(-0.3, 0.3))


def vis_q(o, q, vis):
    o.hide_render = not vis
    chave(o, 'hide_render', q)


def isol_carretel(P, a, b, r=0.011, discos=2):
    """Isolador de carretel (porcelana marrom) de a até b, com saias."""
    a, b = Vector(a), Vector(b)
    u = (b - a).normalized()
    L = (b - a).length
    bp = P.B('porcelana', True)
    cil(bp, (a + b) / 2, r, L, u, lados=16)
    for k in range(discos):
        t = (k + 0.5) / discos
        cil(bp, a.lerp(b, t), r * 1.9, 0.005, u, lados=18, r2=r * 1.3)
    tubo(P.B('aco'), a - u * 0.01, a + u * 0.004, r * 0.45, 6)


def esticador(P, anc, olhal, d):
    """Estai: chapa chumbada, olhal, esticador de ferro fundido, grampos e cabo de aço até o olhal no colar."""
    s = Vector((-d.y, d.x, 0))
    caixa(P.B('aco'), anc + Z * 0.006, (0.055, 0.055, 0.012), rot_cols(d, s, Z))
    for sx in (-1, 1):
        porca(P.B('aco'), anc + s * sx * 0.018 + Z * 0.012, Z, 0.007, 0.007)
    toro(P.B('aco', True), anc + Z * 0.03, 0.012, 0.004, 16, 6, s)
    u = (olhal - (anc + Z * 0.04)).normalized()
    e0 = anc + Z * 0.042
    e1 = e0 + u * 0.03
    e2 = e1 + u * 0.1
    tubo(P.B('aco'), e0, e1, 0.0045, 6)
    cil(P.B('ferro', True), e1 + u * 0.05, 0.01, 0.085, u, lados=10)
    caixa(P.B('ferro'), e1 + u * 0.05, (0.022, 0.006, 0.055), rot_cols(s, u.cross(s), u))
    tubo(P.B('aco'), e2, e2 + u * 0.03, 0.0045, 6)
    tubo(P.B('cabo_aco'), e2 + u * 0.025, olhal, 0.003, 6)
    for w in (0.065, 0.11, 0.15):
        caixa(P.B('aco'), e2 + u * w, (0.013, 0.013, 0.011), rot_cols(s, u.cross(s), u))
    ninho(P, e1 + u * 0.012, d, 0.01, 4, 0)
    # fiapo do laço (ponta solta do cabo depois do grampo)
    tubo(P.B('cabo_aco'), e2 + u * 0.03 + s * 0.007, e2 + u * 0.17 + s * 0.007, 0.0026, 6)


def lichtenberg(P, c, dir0, L, nivel, z, bm_q, bm_b, larg=0.012):
    """Figura de Lichtenberg: árvore fractal plana queimada (bm_q) e a mesma acesa (bm_b) para o raio."""
    c = Vector(c)
    pts = [c]
    a = dir0
    n = 9
    for i in range(n):
        a += random.uniform(-0.55, 0.55)
        pts.append(pts[-1] + Vector((math.cos(a), math.sin(a), 0)) * L / n)
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        u = (q - p).normalized()
        w = larg * (1 - 0.7 * i / n)
        for ac, dz in ((bm_q, 0.0014), (bm_b, 0.0024)):
            ac.faixa(Vector((p.x, p.y, z + dz)), Vector((q.x, q.y, z + dz)), w)
        if nivel > 0 and random.random() < 0.55 and i < n - 2:
            lichtenberg(P, p, a + random.choice((-1, 1)) * random.uniform(0.5, 1.1), L * random.uniform(0.3, 0.55),
                        nivel - 1, z, bm_q, bm_b, w * 0.7)


def raio_arvore(bm_c, bm_h, a, b, r, nivel, desvio=0.11, prof=8, galhos=5):
    """Raio de verdade: canal principal fractal afinando para baixo, galhos que se ramificam e morrem no ar."""
    a, b = Vector(a), Vector(b)
    pts = raio_pts(a, b, desvio, prof)
    n_ = len(pts) - 1
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        bm_c.prisma(p, q, r * (1.0 - 0.35 * i / n_), 5)
    for i, (p, q) in enumerate(zip(pts[::3], pts[3::3])):
        bm_h.prisma(p, q, r * 3.2 * (1.0 - 0.3 * i * 3 / n_), 7)
    L = (b - a).length
    if nivel > 0:
        for g in range(galhos):
            k = random.randint(n_ // 10, n_ * 4 // 5)
            p0 = pts[k]
            dvec = ((b - a).normalized() * random.uniform(0.4, 0.9) + ruido_vec(1.0) * Vector((1, 1, 0.3))).normalized()
            Lg = L * random.uniform(0.08, 0.28) * (1 - k / n_ * 0.6)
            raio_arvore(bm_c, bm_h, p0, p0 + dvec * Lg, r * 0.42, nivel - 1, 0.16, max(4, prof - 2), max(1, galhos - 2))


def raio_obj(nome, a, b, r, nivel, galhos, desvio=0.11, prof=8):
    bc, bh = Acc(), Acc()
    raio_arvore(bc, bh, a, b, r, nivel, desvio, prof, galhos)
    oc = bc.objeto(nome, 'raio')
    oh = bh.objeto(nome + '_halo', 'raio_halo')
    for o in (oc, oh):
        o.visible_shadow = False
    return oc, oh


# ================================================================== PARA-RAIOS (os dois tipos)
ZP = 0.09            # topo da laje
POCO = (0.18, 0.38, -0.38, -0.18)     # poço de inspeção (x0, x1, y0, y1)
CXB = (-0.13, 0.12, -0.415, -0.235)   # caixa de transferência
ZCX = ZP + 0.30


def para_raios(nome, cx, cy, seed, cristal=False):
    """Monta um para-raios; devolve o ponto (mundo) onde o raio pega."""
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    ZM = 3.72 if cristal else 3.22                    # topo do mastro
    R0, R1 = (0.075, 0.048) if cristal else (0.062, 0.036)
    YD = 0.19 if cristal else 0.15                    # afastamento da descida (para o sul)

    def rm(z):
        return R0 + (R1 - R0) * (z - ZP) / (ZM - ZP)

    # --- laje com o poço de inspeção no canto sudeste
    bc = P.B('concreto')
    x0, x1, y0, y1 = POCO
    caixa_de(bc, (-0.45, -0.45, 0.0), (x0, 0.45, ZP))
    caixa_de(bc, (x1, -0.45, 0.0), (0.45, 0.45, ZP))
    caixa_de(bc, (x0, y1, 0.0), (x1, 0.45, ZP))
    caixa_de(bc, (x0, -0.45, 0.0), (x1, y0, ZP))
    for k in range(5):
        rachadura_plana(P.B('fenda'), (random.uniform(-0.35, 0.1), random.uniform(-0.1, 0.38), ZP), Z, 0.24,
                        random.uniform(0, 2 * PI), 7)
    caixa_de(P.B('quebra'), (-0.45, 0.33, ZP - 0.045), (-0.4, 0.45, ZP + 0.0005))
    caixa_de(P.B('quebra'), (0.41, 0.4, ZP - 0.03), (0.45, 0.45, ZP + 0.0005))
    rachadura_plana(P.B('fenda'), (-0.45, -0.1, ZP - 0.004), (-1, 0, 0), 0.09, -PI / 2, 5)
    rachadura_plana(P.B('fenda'), (0.2, -0.45, ZP - 0.004), (0, -1, 0), 0.09, -PI / 2, 5)
    for k in range(6):
        decal(P.B('lama'), (random.uniform(-0.4, 0.4), -0.451, random.uniform(0.02, 0.06)), (0, -1, 0), random.uniform(0.02, 0.045))
        decal(P.B('lama'), (0.451, random.uniform(-0.4, 0.4), random.uniform(0.02, 0.06)), (1, 0, 0), random.uniform(0.02, 0.045))
    # poço: aro de ferro fundido, terra queimada, fulguritos, haste de terra
    bf = P.B('ferro')
    e = 0.016
    caixa_de(bf, (x0 - e, y0 - e, ZP - 0.012), (x1 + e, y0, ZP + 0.006))
    caixa_de(bf, (x0 - e, y1, ZP - 0.012), (x1 + e, y1 + e, ZP + 0.006))
    caixa_de(bf, (x0 - e, y0, ZP - 0.012), (x0, y1, ZP + 0.006))
    caixa_de(bf, (x1, y0, ZP - 0.012), (x1 + e, y1, ZP + 0.006))
    ninho(P, (x1 + 0.008, y0 + 0.03, ZP + 0.006), (1, 0, 0), 0.012, 5, 0.04)
    caixa_de(P.B('terra_poco'), (x0, y0, -0.02), (x1, y1, 0.035))
    pc = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0.035))
    for k in range(14):
        pedra(P.B('terra_poco'), pc + Vector((random.uniform(-0.09, 0.09), random.uniform(-0.09, 0.09), 0)), random.uniform(0.008, 0.02), 0.5)
    for k in range(6):                                                     # fulguritos: areia fundida pelo raio
        a = random.uniform(0, 2 * PI)
        p = pc + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.03, 0.08)
        tubo(P.B('fulgurito'), p, p + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, random.uniform(0.008, 0.02))), random.uniform(0.004, 0.007), 5)
        pedra(P.B('fulgurito'), p, 0.008, 0.7)
    decal(P.B('terra_q'), pc + Z * 0.0012, Z, 0.085)
    haste_t = pc + Z * 0.075
    cil(P.B('cobre_velho', True), pc + Z * 0.035, 0.009, 0.09, lados=14)
    caixa(P.B('latao'), haste_t - Z * 0.01, (0.03, 0.028, 0.022))
    porca(P.B('aco'), haste_t + Vector((0.015, 0, -0.01)), Vector((1, 0, 0)), 0.006, 0.006, False)
    decal(P.B('zinabre'), haste_t + Vector((0, -0.0145, -0.01)), (0, -1, 0), 0.012)
    decal(P.B('queimado'), haste_t + Vector((0, 0, 0.0012)), Z, 0.016)
    # terra queimada em volta da laje, do lado do poço
    for k, (qx, qy, qr) in enumerate(((0.62, -0.42, 0.34), (0.5, -0.62, 0.22), (0.78, -0.2, 0.2))):
        bm = bmesh.new()
        mancha(bm, (cx + qx, cy + qy), qr, 0.001 + k * 0.0002)
        obj(nome + '_terra_q%d' % k, bm, 'terra_chao')
    # Lichtenberg: do poço pela laje e pelo chão
    bq, bb = Acc(), Acc()
    for a in (0.4, -0.25, -0.9):
        lichtenberg(P, (0.47, pc.y + random.uniform(-0.05, 0.05), 0.0009), a, 0.32, 3, 0.0, bq, bb)
    for a in (1.25, 0.75):
        lichtenberg(P, (pc.x + random.uniform(-0.04, 0.04), y1 + 0.025, 0), a, 0.26, 3, ZP, bq, bb)
    lich_b = bb
    # --- sapata do mastro: chapa, nervuras, chumbadores
    caixa(P.B('grafite'), (0, 0, ZP + 0.011), (0.28, 0.28, 0.022))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Vector((sx * 0.105, sy * 0.105, ZP + 0.022))
            tubo(P.B('aco'), p - Z * 0.01, p + Z * 0.045, 0.008, 8)
            porca(P.B('aco'), p, Z, 0.014, 0.012)
            ninho(P, p + Vector((sx * 0.02, 0, 0)), (sx, 0, 0), 0.01, 4, 0)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        rr_ = rm(ZP)
        caixa(P.B('grafite'), d * (rr_ + 0.035) + Z * (ZP + 0.022 + 0.04), (0.07, 0.008, 0.08), rot_cols(d, Vector((-d.y, d.x, 0)), Z))
        caixa(P.B('grafite'), d * (rr_ + 0.02) + Z * (ZP + 0.022 + 0.1), (0.04, 0.008, 0.04), rot_cols(d, Vector((-d.y, d.x, 0)), Z))
    decal(P.B('queimado'), (0.06, -0.12, ZP + 0.0226), Z, 0.035)
    escorrido(P.B('escorre'), Vector((0.14, -0.0, ZP + 0.02)), (1, 0, 0), 0.016, 0.02)
    # --- mastro em três gomos com flanges (o do meio é peça trocada em primer vermelho)
    fz = (0.33, 0.62) if cristal else (0.36, 0.7)
    zf = [ZP + 0.022, ZP + (ZM - ZP) * fz[0], ZP + (ZM - ZP) * fz[1], ZM]
    for i in range(3):
        mat = 'oxido' if i == 1 else 'galv'
        n = 12
        for j in range(n):
            za = zf[i] + (zf[i + 1] - zf[i]) * j / n
            zb = zf[i] + (zf[i + 1] - zf[i]) * (j + 1) / n
            cil(P.B(mat, True), (0, 0, (za + zb) / 2), rm(za), zb - za + 0.0005, lados=28, r2=rm(zb))
        cil(P.B(mat, True), (0, 0, zf[i] + 0.05), rm(zf[i]) + 0.004, 0.006, lados=28)  # cordão de solda
    for zz in zf[1:3]:
        for s in (-1, 1):
            cil(P.B('aco', True), (0, 0, zz + s * 0.009), rm(zz) + 0.035, 0.018, lados=32)
        for k in range(8):
            a = k * PI / 4 + 0.2
            p = Vector((math.cos(a), math.sin(a), 0)) * (rm(zz) + 0.022)
            tubo(P.B('aco'), p + Z * (zz - 0.03), p + Z * (zz + 0.03), 0.004, 6)
            porca(P.B('aco'), p + Z * (zz + 0.018), Z, 0.0075, 0.007)
            porca(P.B('aco'), p + Z * (zz - 0.018), -Z, 0.0075, 0.007)
        for k in range(3):
            a = random.uniform(0, 2 * PI)
            d = Vector((math.cos(a), math.sin(a), 0))
            ninho(P, d * (rm(zz) + 0.034) + Z * (zz - 0.012), d, 0.014, 5, 0.0)
            escorrido(P.B('escorre'), d * (rm(zz - 0.03) + 0.0008) + Z * (zz - 0.02), d, random.uniform(0.1, 0.3), 0.012)
    serie_plana(P.B('tinta'), Vector((rm(1.2) * 0.72, -rm(1.2) * 0.72, 1.2)), Vector((0.7, -0.7, 0)), 0.03, 6, 0.35)
    for k in range(6):                                                     # remendos de ferrugem e queimado
        z = random.uniform(0.4, ZM - 0.2)
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        queimadura(P, d * (rm(z) + 0.0015) + Z * z, d, random.uniform(0.015, 0.03), 'queimado' if k % 3 == 0 else 'chamusco')
    # queimado forte no topo do mastro (raio que escorreu pela superfície)
    for k in range(5):
        a = random.uniform(-2.0, 0.2)
        z = ZM - random.uniform(0.02, 0.35)
        d = Vector((math.cos(a), math.sin(a), 0))
        queimadura(P, d * (rm(z) + 0.0015) + Z * z, d, random.uniform(0.02, 0.035))
    # faixa refletiva gasta perto do pé
    anel_cinta(P.B('refletiva'), (0, 0, 0.62), rm(0.62) + 0.0005, 0.0012, 0.08, 32)
    # --- estais
    nivel_estai = (1.55, 2.45) if cristal else (2.42,)
    angs = (math.radians(100), math.radians(220), math.radians(340))
    for ie, ze in enumerate(nivel_estai):
        cil(P.B('aco', True), (0, 0, ze), rm(ze) + 0.012, 0.05, lados=24)
        for k in range(4):
            a = k * PI / 2 + 0.3
            porca(P.B('aco'), Vector((math.cos(a), math.sin(a), 0)) * (rm(ze) + 0.012) + Z * (ze + 0.012),
                  Vector((math.cos(a), math.sin(a), 0)), 0.006, 0.006, False)
        for k, a in enumerate(angs):
            a2 = a + ie * 0.18
            d = Vector((math.cos(a2), math.sin(a2), 0))
            caixa(P.B('aco'), d * (rm(ze) + 0.024) + Z * ze, (0.03, 0.008, 0.04), rot_cols(d, Vector((-d.y, d.x, 0)), Z))
            olhal = d * (rm(ze) + 0.036) + Z * ze
            anc = Vector((math.cos(a2) * 0.385, math.sin(a2) * 0.385, ZP))
            if ie == 1:
                anc = Vector((math.cos(a2) * 0.4, math.sin(a2) * 0.4, ZP))
            esticador(P, anc, olhal, d)
    # --- topo
    if not cristal:
        ponta = topo_franklin(P, ZM, rm)
    else:
        ponta = topo_cristal(P, ZM, rm)
    # --- descida de cobre com isoladores
    z_top = ZM - 0.06
    zb_list = []
    z = z_top - 0.12
    while z > 0.75:
        zb_list.append(z)
        z -= 0.42
    ZB0, ZB1 = 2.62, 2.98                                                  # bobina no mastro (cristal)
    ZCONT = 1.13                                                           # contador de descargas
    obst = list(zf[1:3]) + list(nivel_estai) + [ZCONT - 0.03, ZCONT + 0.03]
    novo = []
    for z in zb_list:
        while any(abs(z - o) < 0.065 for o in obst) or (cristal and ZB0 - 0.07 < z < ZB1 + 0.07):
            z -= 0.03
        novo.append(z)
    zb_list = novo
    for z in zb_list:
        chapa_arco(P.B('aco', True), (0, 0, z), Z, rm(z), 0.005, 0.03, 0, 2 * PI, 24)
        for s in (-1, 1):
            caixa(P.B('aco'), Vector((s * 0.022, -rm(z) - 0.015, z)), (0.006, 0.03, 0.03))
        tubo(P.B('aco'), (0, -rm(z) - 0.004, z), (0, -YD + 0.05, z), 0.006, 8)
        caixa(P.B('aco'), (0, -rm(z) - 0.02, z), (0.05, 0.006, 0.03))
        porca(P.B('aco'), Vector((0.024, -rm(z) - 0.02, z)), Vector((1, 0, 0)), 0.006, 0.006, False)
        isol_carretel(P, Vector((0, -YD + 0.05, z)), Vector((0, -YD + 0.014, z)), 0.01, 2)
        toro(P.B('latao', True), (0, -YD, z), 0.0125, 0.0035, 16, 6)
        caixa(P.B('latao'), (0, -YD + 0.012, z), (0.018, 0.008, 0.02))
        decal(P.B('zinabre'), Vector((0, -YD - 0.0095, z - 0.012)), (0, -1, 0), 0.01, alongar=0.6)
    # caminho da descida
    topo_d = ponta['grampo']
    pts = bezier(topo_d, topo_d + Vector((0, -0.06, -0.01)), Vector((0, -YD, z_top - 0.02)), Vector((0, -YD, z_top - 0.1)), 10)
    zcaixa = ZCX + 0.05
    g = Vector((CXB[0] + 0.05, -0.30, ZCX))
    if cristal:
        trechos = [(pts[-1].z, ZB1 + 0.03), (ZB0 - 0.03, 0.62)]
    else:
        trechos = [(pts[-1].z, 0.62)]
    caminhos = []
    for ti, (za, zb) in enumerate(trechos):
        seg = [Vector((0, -YD, za - (za - zb) * i / 16)) for i in range(17)]
        if ti == 0:
            seg = pts + seg[1:]
        if ti == len(trechos) - 1:
            seg += bezier(seg[-1], seg[-1] - Z * 0.08, g + Vector((0, 0, 0.1)), g + Z * 0.012, 10)[1:]
        caminhos.append(seg)
    for seg in caminhos:
        varrer(P.B('descida', True), seg, 0.0085, 12)
    # remendos: emenda com luva de pressão e fita
    zz = 1.55 if not cristal else 1.75
    cil(P.B('latao', True), (0, -YD, zz), 0.013, 0.06, lados=12)
    for s in (-1, 1):
        cil(P.B('latao', True), (0, -YD, zz + s * 0.022), 0.0145, 0.008, lados=12)
    varrer(P.B('fita', True), [Vector((0, -YD, 1.18)), Vector((0, -YD, 1.24))], 0.0125, 12, (True, True))
    # contador de descargas da IA (caixa na descida, visor de 7 segmentos)
    zc = ZCONT
    c = Vector((0, -YD - 0.042, zc))
    caixa(P.B('grafite'), c, (0.07, 0.05, 0.11))
    caixa(P.B('amarelo'), c + Vector((0, -0.026, 0)), (0.072, 0.004, 0.112))
    caixa(P.B('vidro_escuro'), c + Vector((0, -0.0285, 0.018)), (0.05, 0.002, 0.03))
    serie_plana(P.B('led_a'), c + Vector((0, -0.0296, 0.018)), (0, -1, 0), 0.014, 3, 0.0, horiz=Vector((1, 0, 0)))
    caixa(P.B('led_v'), c + Vector((0.026, -0.029, -0.04)), (0.006, 0.002, 0.006))
    serie_plana(P.B('tinta'), c + Vector((0, -0.0285, -0.02)), (0, -1, 0), 0.008, 5, 0.4, horiz=Vector((1, 0, 0)))
    for s in (-1, 1):
        chapa_arco(P.B('aco', True), Vector((0, -YD, zc + s * 0.035)), Z, 0.0095, 0.003, 0.012, 0, 2 * PI, 16)
        caixa(P.B('aco'), Vector((0, -YD - 0.014, zc + s * 0.035)), (0.026, 0.012, 0.012))
    decal(P.B('queimado'), c + Vector((0.02, -0.0285, 0.05)), (0, -1, 0), 0.012)
    ninho(P, c + Vector((-0.036, -0.02, -0.05)), (-1, 0, 0), 0.008, 4, 0.03)
    # --- caixa de transferência com centelhador de chifres
    cb0 = Vector((CXB[0], CXB[2], ZP))
    cb1 = Vector((CXB[1], CXB[3], ZCX))
    caixa_de(P.B('grafite'), cb0, cb1)
    caixa_de(P.B('amarelo'), Vector((CXB[0] + 0.012, CXB[2] - 0.006, ZP + 0.02)), Vector((CXB[1] - 0.012, CXB[2], ZCX - 0.02)))
    caixa(P.B('listras'), Vector(((CXB[0] + CXB[1]) / 2, CXB[2] - 0.0065, ZP + 0.06)), (0.2, 0.002, 0.04))
    serie_plana(P.B('tinta'), Vector(((CXB[0] + CXB[1]) / 2, CXB[2] - 0.0068, ZCX - 0.06)), (0, -1, 0), 0.016, 5, 0.3,
                horiz=Vector((1, 0, 0)))
    for sx in (CXB[0] + 0.03, CXB[1] - 0.03):
        for sz in (ZP + 0.04, ZCX - 0.04):
            cil(P.B('aco'), Vector((sx, CXB[2] - 0.007, sz)), 0.006, 0.004, Vector((0, -1, 0)), lados=6)
    for k in range(3):                                                     # dobradiças
        caixa(P.B('aco'), Vector((CXB[0] + 0.012, CXB[2] - 0.008, ZP + 0.07 + k * 0.08)), (0.012, 0.006, 0.03))
    caixa(P.B('led_a'), Vector((CXB[1] - 0.03, CXB[2] - 0.0075, ZCX - 0.035)), (0.008, 0.002, 0.008))
    decal(P.B('queimado'), Vector((CXB[1] - 0.04, CXB[2] - 0.0068, ZCX - 0.05)), (0, -1, 0), 0.03, alongar=0.7)
    ninho(P, Vector((CXB[0] + 0.03, CXB[2] - 0.008, ZP + 0.03)), (0, -1, 0), 0.012, 6, 0.04)
    escorrido(P.B('oleo'), Vector((CXB[1] - 0.06, CXB[2] - 0.0068, ZP + 0.15)), (0, -1, 0), 0.12, 0.008)
    cil(P.B('borracha', True), g + Z * 0.006, 0.016, 0.012, lados=14)                   # prensa-cabo
    # chifres: dois postes de porcelana sobre a tampa e as hastes em V
    hx = (0.0, 0.085)
    hy = -0.36
    chif = []
    for i, x in enumerate(hx):
        b0 = Vector((x, hy, ZCX))
        cil(P.B('porcelana', True), b0 + Z * 0.04, 0.01, 0.08, lados=14)
        for k in range(3):
            cil(P.B('porcelana', True), b0 + Z * (0.018 + k * 0.022), 0.019, 0.005, lados=16, r2=0.011)
        tp = b0 + Z * 0.085
        s = -1 if i == 0 else 1
        pts_h = bezier(tp, tp + Vector((-s * 0.012, 0, 0.03)), tp + Vector((s * 0.0, 0, 0.09)), tp + Vector((s * 0.05, 0, 0.17)), 10)
        varrer(P.B('cobre', True), pts_h, 0.0042, 8, (False, True))
        chif.append(pts_h)
        decal(P.B('queimado'), b0 + Z * 0.083 + Vector((0, -0.01, 0)), (0, -1, 0), 0.008)
    pedra(P.B('derretido'), chif[0][4] + Vector((0.0035, 0, 0)), 0.006, 0.8)
    pedra(P.B('derretido'), chif[1][5] + Vector((-0.0035, 0, 0)), 0.006, 0.8)
    # ligação: prensa-cabo → chifre esquerdo (sob a tampa: pino) e chifre direito → fita até a haste
    cil(P.B('latao', True), Vector((hx[0], hy, ZCX + 0.004)), 0.016, 0.008, lados=12)
    fpts = [Vector((hx[1] + 0.012, hy, ZCX + 0.004)), Vector((CXB[1] + 0.004, hy, ZCX + 0.004)),
            Vector((CXB[1] + 0.006, hy, ZCX - 0.01)), Vector((CXB[1] + 0.006, hy, ZP + 0.02)),
            Vector((CXB[1] + 0.02, hy, ZP + 0.003)), Vector((x0 - 0.02, hy + 0.06, ZP + 0.003)),
            Vector((x0 + 0.01, pc.y - 0.01, ZP + 0.0095)), Vector((pc.x - 0.006, pc.y - 0.01, ZP + 0.0095)),
            haste_t + Vector((-0.02, 0, 0.005))]
    for a, b in zip(fpts, fpts[1:]):
        u = (b - a).normalized()
        s = u.cross(Z)
        if s.length < 1e-3:
            s = Vector((0, 1, 0))
        s.normalize()
        caixa(P.B('fita_cobre'), (a + b) / 2, ((b - a).length + 0.006, 0.022, 0.003), rot_cols(u, s, u.cross(s).normalized()))
    for t in (0.3, 0.7):
        p = fpts[4].lerp(fpts[5], t)
        cil(P.B('aco'), p + Z * 0.004, 0.006, 0.004, lados=6)
    decal(P.B('zinabre'), fpts[5].lerp(fpts[6], 0.5) + Z * 0.0035, Z, 0.014, alongar=1.6)
    # --- banco de capacitores (oeste)
    ncap = 6 if cristal else 4
    ys = [-0.1 + i * 0.096 for i in range(ncap)] if cristal else [-0.12, 0.01, 0.14, 0.27]
    xc = -0.33
    rc = 0.042 if cristal else 0.05
    hc = 0.24 if cristal else 0.26
    caixa_de(P.B('grafite'), (xc - 0.08, ys[0] - 0.07, ZP), (xc + 0.08, ys[-1] + 0.07, ZP + 0.02))
    for yy in (ys[0] - 0.07, ys[-1] + 0.07):
        for xx in (xc - 0.08, xc + 0.08):
            caixa_de(P.B('grafite'), (xx - 0.008, yy - 0.008, ZP), (xx + 0.008, yy + 0.008, ZP + hc + 0.08))
    caixa_de(P.B('galv'), (xc + 0.072, ys[0] - 0.07, ZP + hc * 0.55), (xc + 0.078, ys[-1] + 0.07, ZP + hc * 0.55 + 0.025))
    caixa_de(P.B('galv'), (xc - 0.078, ys[0] - 0.07, ZP + hc * 0.55), (xc - 0.072, ys[-1] + 0.07, ZP + hc * 0.55 + 0.025))
    topos = []
    aneis_carga = bmesh.new()
    for i, y in enumerate(ys):
        c = Vector((xc, y, ZP + 0.02))
        estufado = (i == 1)
        mat_c = 'oxido' if (cristal and i == 4) else 'capacitor'           # um capacitor trocado de outra cor
        if estufado:
            cil(P.B(mat_c, True), c + Z * hc * 0.42, rc, hc * 0.84, lados=28)
            cil(P.B(mat_c, True), c + Z * (hc * 0.84 + 0.015), rc * 1.07, 0.03, lados=28, r2=rc * 0.86)
            topo = c + Z * (hc + 0.006)
            for k in range(7):
                pedra(P.B('crosta_branca'), topo + ruido_vec(0.02) * Vector((1, 1, 0.2)), random.uniform(0.004, 0.008), 0.6)
            escorrido(P.B('crosta_branca'), c + Vector((rc + 0.0005, 0, hc * 0.8)), (1, 0, 0), 0.14, 0.014)
        else:
            cil(P.B(mat_c, True), c + Z * hc / 2, rc, hc, lados=28)
            topo = c + Z * hc
        cil(P.B('aluminio', True), topo + Z * 0.005, rc * 0.95, 0.01, lados=28)
        toro(aneis_carga, topo + Z * 0.011, rc * 0.62, 0.0035, 28, 6)
        for sx in (-1, 1):
            tp = topo + Vector((0, sx * rc * 0.45, 0.01))
            cil(P.B('porcelana', True), tp + Z * 0.014, 0.008, 0.028, lados=12)
            cil(P.B('porcelana', True), tp + Z * 0.012, 0.013, 0.004, lados=12)
            tubo(P.B('latao'), tp + Z * 0.028, tp + Z * 0.04, 0.0032, 6)
            porca(P.B('latao'), tp + Z * 0.034, Z, 0.006, 0.005, False)
        topos.append(topo + Z * 0.036)
        serie_plana(P.B('tinta'), c + Vector((rc + 0.0005, 0, hc * 0.5)), (1, 0, 0), 0.011, 3, 0.3, horiz=Vector((0, 1, 0)))
        if i % 2 == 0:
            decal(P.B('queimado'), c + Vector((rc * 0.7, -rc * 0.7, hc * 0.85)), (0.7, -0.7, 0), 0.012, alongar=0.7)
    for i in range(len(ys) - 1):                                           # barramento
        a = topos[i] + Vector((0, rc * 0.45, 0))
        b = topos[i + 1] + Vector((0, -rc * 0.45, 0))
        caixa(P.B('cobre'), (a + b) / 2, (0.012, (b - a).length + 0.012, 0.003))
    o_car = obj(nome + '_carga', aneis_carga, 'carga')
    o_car.matrix_world = P.M
    # barra de LEDs de carga (poste da frente do rack, face leste)
    leds = []
    lx = xc + 0.088
    ly = ys[0] - 0.07
    caixa(P.B('grafite'), Vector((lx - 0.002, ly, ZP + 0.04 + hc * 0.5)), (0.006, 0.026, hc * 0.95))
    for k in range(10):
        p = Vector((lx + 0.0015, ly, ZP + 0.06 + k * hc * 0.09))
        caixa(P.B('vidro_escuro'), p, (0.003, 0.016, 0.012))
        bl = bmesh.new()
        caixa(bl, p + Vector((0.0008, 0, 0)), (0.003, 0.0165, 0.0125))
        o = obj(nome + '_led%d' % k, bl, 'led_v' if k < 8 else 'led_r')
        o.matrix_world = P.M
        leds.append(o)
    # cabo grosso: prensa-cabo da caixa → (bobina de choque) → barramento
    st = Vector((CXB[0] - 0.004, -0.3, ZP + 0.1))
    cil(P.B('borracha', True), st + Vector((0.004, 0, 0)), 0.014, 0.012, Vector((1, 0, 0)), lados=12)
    alvo = topos[0] + Vector((0, -rc * 0.45, 0.004))
    if not cristal:
        cp = bezier(st, st + Vector((-0.06, 0, -0.02)), Vector((xc + 0.12, -0.27, ZP + 0.01)), Vector((xc + 0.1, -0.22, ZP + 0.012)), 8)
        cp += bezier(cp[-1], cp[-1] + Vector((0, 0.03, 0)), alvo + Vector((0.08, -0.05, -0.05)), alvo, 10)[1:]
        varrer(P.B('borracha', True), cp, 0.008, 10)
        for t in (5, 13):
            varrer(P.B('fita_azul', True), [cp[t], cp[t + 1]], 0.0115, 10, (True, True))
    else:
        bobina_choque(P, Vector((-0.06, 0.28, ZP)), st, alvo, xc)
    # cabo de volta (terra do banco) até a fita
    a = topos[-1] + Vector((0, rc * 0.45, 0.004))
    cp = bezier(a, a + Vector((0.05, 0.06, 0)), Vector((-0.12, 0.42, ZP + 0.01)), Vector((0.0, 0.42, ZP + 0.01)), 10)
    cp += bezier(cp[-1], cp[-1] + Vector((0.2, 0, 0)), Vector((0.433, 0.3, ZP + 0.01)), Vector((0.433, -0.12, ZP + 0.01)), 12)[1:]
    cp += bezier(cp[-1], cp[-1] + Vector((0, -0.04, 0)), Vector((x1 + 0.03, y1 + 0.04, ZP + 0.01)), Vector((x1 - 0.01, y1 - 0.02, ZP + 0.012)), 6)[1:]
    varrer(P.B('cabo_verm', True), cp, 0.0055, 10)
    # --- brita e lama em volta da laje
    for k in range(70):
        a = random.uniform(0, 2 * PI)
        rr_ = random.uniform(0.48, 0.75)
        x_, y_ = math.cos(a) * rr_, math.sin(a) * rr_
        if max(abs(x_), abs(y_)) < 0.47:
            continue
        pedra(P.B('brita'), (x_, y_, 0.0), random.uniform(0.008, 0.024), 0.5)
    bm = bmesh.new()
    mancha(bm, (cx, cy), 0.7, 0.0008)
    obj(nome + '_halo', bm, 'halo')
    P.fim()
    o_lb = lich_b.objeto(nome + '_lich_brilho', 'descarga', P.M)
    bq.objeto(nome + '_lich', 'lich', P.M)
    # --- efeitos do raio
    desc_h = bmesh.new()
    for seg in caminhos:
        varrer(desc_h, seg, 0.02, 8)
    o_dh = obj(nome + '_descida_brilho', desc_h, 'descarga_halo')
    o_dh.matrix_world = P.M
    o_dh.visible_shadow = False
    arcs_iso = []
    for z in zb_list[1::2]:
        arcs_iso.append(arco_obj(nome + '_arco_iso%.2f' % z, P.W((0.012, -YD + 0.01, z + 0.004)),
                                 P.W((0.02, -rm(z) - 0.004, z + 0.03)), 0.35, 0.0022, 6, 1))
    arcs_ch = [arco_obj(nome + '_arco_chifre%d' % v, P.W(chif[0][7 - v]), P.W(chif[1][7 - v]), 0.4, 0.003, 7, 1) for v in range(2)]
    arcs_cap = [arco_obj(nome + '_arco_cap%d' % i, P.W(topos[i] + Vector((0.004, rc * 0.45, 0.006))),
                         P.W(topos[i + 1] + Vector((0.004, -rc * 0.45, 0.006))), 0.5, 0.0018, 5, 0) for i in range(len(ys) - 1)]
    tip = P.W(ponta['ponta'])
    bp = bmesh.new()
    bmesh.ops.create_icosphere(bp, subdivisions=3, radius=0.035, matrix=Matrix.Translation(tip))
    o_pl = obj(nome + '_plasma', bp, 'plasma')
    bp = bmesh.new()
    bmesh.ops.create_icosphere(bp, subdivisions=3, radius=0.14, matrix=Matrix.Translation(tip))
    o_ph = obj(nome + '_plasma_halo', bp, 'raio_halo')
    for o in (o_pl, o_ph):
        o.visible_shadow = False
    corona = []
    for v in range(7):
        d = (Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.2, 0.9)))).normalized()
        corona.append(arco_obj(nome + '_corona%d' % v, tip, tip + d * random.uniform(0.18, 0.4), 0.2, 0.003, 7, 1))
    l_tip = luz(nome + '_luz_ponta', (0.75, 0.68, 1.0), 0.0, tip + Vector((0, -0.1, -0.05)), 0.05)
    l_poco = luz(nome + '_luz_poco', (0.6, 0.45, 1.0), 0.0, P.W(pc + Vector((0, 0, 0.12))), 0.03)
    l_cap = luz(nome + '_luz_cap', (0.55, 0.2, 1.0), 0.0, P.W(Vector((xc + 0.15, 0.05, ZP + hc + 0.12))), 0.04)
    l_cris = None
    if cristal:
        l_cris = luz(nome + '_luz_cristal', (0.55, 0.2, 1.0), 6.0, P.W(Vector((0.12, -0.14, ZM + 0.42))), 0.05)

    def anima(q, fr):
        f = forca(q)
        rr = random.Random(q * 313 + seed)
        vis_q(o_pl, q, f > 0.3)
        vis_q(o_ph, q, f > 0.2)
        vis_q(o_dh, q, f > 0.2)
        vis_q(o_lb, q, f > 0.5)
        for i, o in enumerate(corona):
            vis_q(o, q, f > 0.3 and (rr.random() < 0.7 or (q == F_RAIO and i % 2 == 0)))
        for i, o in enumerate(arcs_iso):
            vis_q(o, q, f > 0.5 and (rr.random() < 0.6 or q == F_RAIO))
        for i, o in enumerate(arcs_ch):
            ch = (12 <= q <= 18 and (q + i) % 2 == 0) or (q % 23 == 0 and i == 0)
            vis_q(o, q, ch)
        for i, o in enumerate(arcs_cap):
            vis_q(o, q, 12 <= q <= 16 and (rr.random() < 0.5 or (q == F_RAIO and i % 2 == 1)))
        n_on = carga_nivel(q)
        for k, o in enumerate(leds):
            vis_q(o, q, k < n_on)
        l_tip.data.energy = 700.0 * f
        l_tip.data.keyframe_insert('energy', frame=q)
        l_poco.data.energy = 60.0 * f
        l_poco.data.keyframe_insert('energy', frame=q)
        l_cap.data.energy = 25.0 * max(f, 0.6 if 12 <= q <= 18 else 0.0)
        l_cap.data.keyframe_insert('energy', frame=q)
        if l_cris is not None:
            l_cris.data.energy = 6.0 + 2.0 * math.sin(2 * PI * 2 * fr) + 260.0 * f + (40.0 if 12 <= q <= 22 else 0)
            l_cris.data.keyframe_insert('energy', frame=q)
    ANIM.append(anima)
    # faíscas na ponta e gotas de metal fundido caindo
    ev = [(12, tip, Vector((0, 0, 1))), (15, tip, Vector((0.3, -0.3, 1)))]
    faiscas(nome + '_fsc_ponta', 28, ev, 1.6, 1.4, 10, chao=0.0)
    ev = [(q0, P.W(chif[0][8]), Vector((0, -0.4, 1))) for q0 in (12, 15, 23)]
    faiscas(nome + '_fsc_chifre', 12, ev, 0.8, 0.8, 8, chao=ZCX)
    return tip


def topo_franklin(P, ZM, rm):
    """Captor Franklin: adaptador, haste afilada com ponta derretida e revenida, coroa de 8 pontas (duas fundidas)."""
    r = rm(ZM)
    cil(P.B('aco', True), (0, 0, ZM + 0.005), r + 0.022, 0.012, lados=28)              # tampa
    for k in range(6):
        a = k * PI / 3
        porca(P.B('aco'), Vector((math.cos(a), math.sin(a), 0)) * (r + 0.012) + Z * (ZM + 0.011), Z, 0.006, 0.006, False)
    cil(P.B('aco', True), (0, 0, ZM + 0.05), 0.026, 0.08, lados=20, r2=0.022)          # adaptador roscado
    for k in range(5):
        toro(P.B('aco', True), (0, 0, ZM + 0.02 + k * 0.014), 0.025 - k * 0.0008, 0.0025, 20, 5)
    # grampo da descida no adaptador
    cil(P.B('latao', True), (0, -0.028, ZM + 0.04), 0.012, 0.04, lados=10)
    caixa(P.B('latao'), (0, -0.018, ZM + 0.04), (0.03, 0.012, 0.03))
    decal(P.B('zinabre'), Vector((0, -0.0405, ZM + 0.03)), (0, -1, 0), 0.01)
    grampo = Vector((0, -0.032, ZM + 0.025))
    # coroa: anel com 8 pontas inclinadas
    zc = ZM + 0.1
    cil(P.B('aco', True), (0, 0, zc), 0.032, 0.026, lados=20)
    toro(P.B('aco', True), (0, 0, zc), 0.06, 0.007, 36, 8)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        tubo(P.B('aco'), Vector((math.cos(a), math.sin(a), 0)) * 0.03 + Z * zc, Vector((math.cos(a), math.sin(a), 0)) * 0.056 + Z * zc, 0.004, 6)
    for k in range(8):
        a = k * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        base = d * 0.06 + Z * (zc + 0.004)
        ax = (d * 0.55 + Z).normalized()
        L = 0.15
        if k in (1, 5):                                                   # pontas fundidas, mais curtas
            L = 0.08 if k == 1 else 0.1
            cil(P.B('aco', True), base + ax * L / 2, 0.006, L, ax, lados=10, r2=0.0045)
            fim = base + ax * L
            pedra(P.B('derretido'), fim, 0.008, 0.9)
            pedra(P.B('derretido'), fim - Z * 0.012 + d * 0.003, 0.005, 1.3)
            decal(P.B('queimado'), base + ax * 0.03 + d * 0.006, d, 0.01, alongar=0.6)
        else:
            cil(P.B('aco', True), base + ax * L / 2, 0.006, L, ax, lados=10, r2=0.0012)
        cil(P.B('aco', True), base, 0.009, 0.014, ax, lados=10)
    # haste principal: base grossa, cone longo, ponta derretida (bolha de metal com escorrido)
    z0 = zc + 0.013
    cil(P.B('aco', True), (0, 0, z0 + 0.06), 0.02, 0.12, lados=20, r2=0.017)
    zt0 = z0 + 0.12
    L = 0.42
    n = 8
    for j in range(n):                                                   # cone em fatias (a de cima revenida)
        za = zt0 + L * j / n
        zb = zt0 + L * (j + 1) / n
        ra = 0.017 + (0.005 - 0.017) * j / n
        rb = 0.017 + (0.005 - 0.017) * (j + 1) / n
        cil(P.B('revenido_pr' if j >= 3 else 'aco', True), (0, 0, (za + zb) / 2), ra, zb - za + 0.0004, lados=20, r2=rb)
    zt = zt0 + L
    bmd = P.B('derretido', True)
    bmesh.ops.create_icosphere(bmd, subdivisions=2, radius=0.011,
                               matrix=Matrix.Translation((0.002, -0.001, zt + 0.004)) @ Matrix.Diagonal((1.1, 0.9, 0.75, 1)))
    for k, (dx, dz, rr) in enumerate(((0.006, -0.018, 0.006), (0.0075, -0.034, 0.0045), (0.007, -0.047, 0.0035))):
        bmesh.ops.create_icosphere(bmd, subdivisions=1, radius=rr, matrix=Matrix.Translation((dx * 0.9, -0.004, zt + dz)))
    for k in range(3):                                                   # respingos solidificados na haste
        a = random.uniform(0, 2 * PI)
        z = zt - random.uniform(0.06, 0.2)
        rr = 0.017 + (0.005 - 0.017) * (z - zt0) / L
        pedra(P.B('derretido'), Vector((math.cos(a), math.sin(a), 0)) * rr + Z * z, 0.004, 0.8)
    for k in range(4):
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        decal(P.B('queimado'), d * 0.0335 + Z * (zc + random.uniform(-0.01, 0.01)), d, 0.012, alongar=0.6)
    return {'ponta': Vector((0.002, 0, zt + 0.014)), 'grampo': grampo}


def topo_cristal(P, ZM, rm):
    """Copa de cobre com 4 garras segurando o cristal grande; dois anéis de campo em isoladores; bobina no mastro."""
    r = rm(ZM)
    # bobina no mastro (a descida passa por ela)
    ZB0, ZB1 = 2.62, 2.98
    RB = 0.13
    cil(P.B('resina', True), (0, 0, (ZB0 + ZB1) / 2), RB - 0.008, ZB1 - ZB0, lados=40)
    for zz in (ZB0, ZB1):
        cil(P.B('resina', True), (0, 0, zz), RB + 0.018, 0.012, lados=40)
        for k in range(6):
            a = k * PI / 3 + 0.25
            porca(P.B('aco'), Vector((math.cos(a), math.sin(a), 0)) * (RB + 0.008) + Z * (zz + 0.006), Z, 0.005, 0.005, False)
    voltas = 15
    pts = []
    zh0, zh1 = ZB0 + 0.025, ZB1 - 0.025
    a0 = -PI / 2
    for i in range(voltas * 24 + 1):
        t = i / (voltas * 24)
        a = a0 + 2 * PI * voltas * t
        pts.append(Vector((math.cos(a) * RB, math.sin(a) * RB, zh1 - (zh1 - zh0) * t)))
    varrer(P.B('cobre_bob', True), pts, 0.0065, 8)
    for k in range(5):
        a = random.uniform(0, 2 * PI)
        z = random.uniform(zh0, zh1)
        d = Vector((math.cos(a), math.sin(a), 0))
        decal(P.B('queimado'), d * (RB + 0.0066) + Z * z, d, random.uniform(0.012, 0.022), alongar=0.6)
    YD = 0.19
    # pontas da bobina ligadas à descida (em cima e embaixo)
    for zz, zl in ((zh1, ZB1 + 0.03), (zh0, ZB0 - 0.03)):
        p = Vector((0, -RB, zz))
        varrer(P.B('descida', True), bezier(p, p + Vector((0, -0.03, (zl - zz) * 0.3)), Vector((0, -YD + 0.01, zl)),
                                            Vector((0, -YD, zl)), 8), 0.0065, 10)
    for k in range(4):                                                   # espaçadores de fenolite
        a = k * PI / 2 + PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(P.B('resina'), d * (RB + 0.004) + Z * (ZB0 + ZB1) / 2, (0.012, 0.012, ZB1 - ZB0), rot_cols(d, Vector((-d.y, d.x, 0)), Z))
    # tampa e adaptador
    cil(P.B('aco', True), (0, 0, ZM + 0.006), r + 0.026, 0.014, lados=28)
    for k in range(8):
        a = k * PI / 4
        porca(P.B('aco'), Vector((math.cos(a), math.sin(a), 0)) * (r + 0.014) + Z * (ZM + 0.013), Z, 0.006, 0.006, False)
    cil(P.B('aco', True), (0, 0, ZM + 0.05), 0.04, 0.08, lados=24, r2=0.034)
    grampo = Vector((0, -0.045, ZM + 0.03))
    cil(P.B('latao', True), (0, -0.044, ZM + 0.04), 0.012, 0.04, lados=10)
    # copa de cobre
    zk = ZM + 0.09
    cil(P.B('cobre_velho', True), (0, 0, zk + 0.03), 0.05, 0.06, lados=32, r2=0.105)
    toro(P.B('cobre_velho', True), (0, 0, zk + 0.06), 0.105, 0.008, 40, 8)
    for k in range(6):
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        nrm = (d + Z * 0.6).normalized()
        decal(P.B('queimado' if k % 2 else 'chamusco'), d * 0.08 + Z * (zk + 0.035) + nrm * 0.012, nrm, random.uniform(0.012, 0.022))
    decal(P.B('zinabre'), Vector((0.06, -0.06, zk + 0.025)) + Vector((0.7, -0.7, 0.6)).normalized() * 0.006,
          Vector((0.7, -0.7, 0.6)), 0.02)
    # cristal
    zc0 = zk + 0.04
    HC = 0.48
    RC = 0.08
    bm = bmesh.new()
    cil(bm, (0, 0, zc0 + HC / 2), RC, HC, lados=6)
    cil(bm, (0, 0, zc0 + HC + 0.09), RC, 0.18, lados=6, r2=0.004)
    for k, (a, tl, h, rr) in enumerate(((0.6, 0.5, 0.16, 0.03), (2.5, 0.42, 0.13, 0.026), (4.3, 0.55, 0.11, 0.022), (5.5, 0.3, 0.2, 0.028))):
        d = Vector((math.cos(a), math.sin(a), 0))
        ax = (d * math.sin(tl) + Z * math.cos(tl)).normalized()
        c = d * 0.06 + ax * h / 2 + Z * (zc0 + 0.03)
        cil(bm, c, rr, h, ax, lados=6)
        cil(bm, c + ax * (h / 2 + rr * 0.8), rr, rr * 1.6, ax, lados=6, r2=0.001)
    cris = obj(P.nome + '_cristal', bm, 'cristal_pc')
    cris.matrix_world = P.M
    tip = Vector((0, 0, zc0 + HC + 0.18))
    # rachadura e queimado no cristal (faces do prisma)
    for k in range(3):
        a = PI / 6 + k * PI / 3 * 2 - PI / 3
        nrm = Vector((math.cos(a), math.sin(a), 0))
        rf = RC * math.cos(PI / 6) + 0.0012
        rachadura_plana(P.B('fenda'), nrm * rf + Z * (zc0 + HC * random.uniform(0.45, 0.8)), nrm, 0.12, -PI / 2 + 0.3, 6, 0.0022)
    nrm = Vector((math.cos(-PI / 2), math.sin(-PI / 2), 0))
    decal(P.B('queimado'), nrm * (RC * math.cos(PI / 6) + 0.0015) + Z * (zc0 + HC - 0.02), nrm, 0.028, alongar=0.6)
    # garras (4), com articulação e pontas fundidas e revenidas
    for k in range(4):
        a = k * PI / 2 + PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        s = Vector((-d.y, d.x, 0))
        p0 = d * 0.098 + Z * (zk + 0.06)
        p1 = d * 0.135 + Z * (zk + 0.15)
        p2 = d * 0.112 + Z * (zk + 0.27)
        p3 = d * 0.082 + Z * (zk + 0.33)
        pts = bezier(p0, p0 + d * 0.035 + Z * 0.03, p1 - Z * 0.03, p1, 6) + bezier(p1, p1 + Z * 0.05, p2 + d * 0.02 - Z * 0.03, p2, 6)[1:]
        varrer(P.B('cobre_velho', True), pts, 0.011, 10)
        pts2 = bezier(p2, p2 + Z * 0.03, p3 + d * 0.012, p3 - d * 0.004, 5)
        varrer(P.B('revenido_pc', True), pts2, 0.0085, 10, (False, True))
        cil(P.B('aco', True), p1, 0.016, 0.03, s, lados=14)               # articulação
        porca(P.B('aco'), p1 + s * 0.015, s, 0.008, 0.007)
        porca(P.B('aco'), p1 - s * 0.015, -s, 0.008, 0.007)
        # pistãozinho que aperta a garra (camisa na copa, haste na garra)
        c0 = d * 0.06 + Z * (zk + 0.065) + s * 0.03
        c1 = p1 - d * 0.012 + s * 0.03
        u = (c1 - c0).normalized()
        cil(P.B('grafite', True), c0 + u * 0.03, 0.009, 0.06, u, lados=12)
        tubo(P.B('aco'), c0 + u * 0.06, c1, 0.004, 8)
        caixa(P.B('aco'), c1 - s * 0.012, (0.012, 0.03, 0.012), rot_cols(d, s, Z))
        caixa(P.B('aco'), c0 - s * 0.01 + Z * -0.004, (0.014, 0.026, 0.014), rot_cols(d, s, Z))
        if k in (0, 2):
            pedra(P.B('derretido'), p3 + Z * 0.004, 0.009, 0.9)
            pedra(P.B('derretido'), p3 - Z * 0.014 + d * 0.004, 0.005, 1.4)
        decal(P.B('queimado'), p2 + d * 0.012, d, 0.012, alongar=0.6)
    # anéis de campo em isoladores
    for ia, (za, Ra, ra) in enumerate(((zk + 0.2, 0.24, 0.016), (zk + 0.42, 0.19, 0.013))):
        toro(P.B('aluminio', True), (0, 0, za), Ra, ra, 64, 14)
        toro(P.B('violeta', True), (0, 0, za), Ra - ra * 0.92, ra * 0.25, 64, 6)
        for k in range(3):
            a = k * 2 * PI / 3 + ia * PI / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            b0 = d * 0.1 + Z * (zk + 0.058)
            b1 = d * (Ra - ra) + Z * za
            u = (b1 - b0).normalized()
            L = (b1 - b0).length
            tubo(P.B('aco'), b0, b0 + u * L * 0.35, 0.0055, 8)
            isol_carretel(P, b0 + u * L * 0.35, b0 + u * L * 0.72, 0.009, 3)
            tubo(P.B('aco'), b0 + u * L * 0.72, b1 + u * 0.004, 0.0055, 8)
            caixa(P.B('aluminio'), b1, (0.024, 0.024, 0.024 if ia else 0.03))
        for k in range(5):
            a = random.uniform(0, 2 * PI)
            b = random.uniform(-0.6, 1.2)
            d = Vector((math.cos(a), math.sin(a), 0))
            nrm = d * math.cos(b) + Z * math.sin(b)
            decal(P.B('queimado' if k % 2 else 'chamusco'), Vector((0, 0, za)) + d * Ra + nrm * (ra + 0.0006), nrm, random.uniform(0.008, 0.016))
    return {'ponta': tip, 'grampo': grampo, 'cristal': cris}


def bobina_choque(P, c, st, alvo, xc):
    """Bobina de choque no ar: tubo de cobre em hélice horizontal sobre dois postes de porcelana."""
    c = Vector(c)
    caixa_de(P.B('resina'), c + Vector((-0.14, -0.05, 0)), c + Vector((0.14, 0.05, 0.02)))
    R = 0.06
    zc = c.z + 0.14
    for sx in (-1, 1):
        b0 = c + Vector((sx * 0.11, 0, 0.02))
        cil(P.B('porcelana', True), b0 + Z * 0.035, 0.012, 0.07, lados=14)
        for k in range(3):
            cil(P.B('porcelana', True), b0 + Z * (0.012 + k * 0.02), 0.02, 0.005, lados=16, r2=0.013)
        caixa(P.B('latao'), b0 + Z * 0.075, (0.03, 0.03, 0.012))
    pts = []
    voltas = 6
    for i in range(voltas * 24 + 1):
        t = i / (voltas * 24)
        a = 2 * PI * voltas * t - PI / 2
        pts.append(Vector((c.x - 0.1 + 0.2 * t, c.y + math.cos(a) * R, zc + math.sin(a) * R)))
    varrer(P.B('cobre_bob', True), pts, 0.006, 10)
    for k in range(4):
        decal(P.B('queimado'), pts[20 + k * 30] + Vector((0, 0, 0.0065)), Z, 0.008)
    tubo(P.B('resina'), Vector((c.x - 0.115, c.y, zc)), Vector((c.x + 0.115, c.y, zc)), 0.012, 12)
    for sx in (-1, 1):
        tubo(P.B('resina'), c + Vector((sx * 0.11, 0, 0.08)), Vector((c.x + sx * 0.11, c.y, zc)), 0.008, 8)
    # entrada: da caixa → ponta leste da bobina; saída: ponta oeste → barramento
    a1 = pts[-1]
    cp = bezier(st, st + Vector((-0.05, 0, -0.04)), Vector((st.x - 0.05, -0.05, c.z + 0.01)), Vector((c.x + 0.16, c.y - 0.05, c.z + 0.012)), 10)
    cp += bezier(cp[-1], cp[-1] + Vector((0.03, 0.02, 0)), a1 + Vector((0.05, 0, -0.08)), a1, 8)[1:]
    varrer(P.B('borracha', True), cp, 0.008, 10)
    a0 = pts[0]
    cp = bezier(a0, a0 + Vector((-0.05, 0, 0.02)), alvo + Vector((0.1, 0.02, 0.06)), alvo, 10)
    varrer(P.B('borracha', True), cp, 0.008, 10)
    for t in (3, 7):
        varrer(P.B('fita_azul', True), [cp[t], cp[t + 1]], 0.0115, 10, (True, True))


# ================================================================== montagem
def montar_pr():
    para_raios('pr', 0, 0, 7)


def montar_pc():
    para_raios('pc', 0, 0, 9, cristal=True)


PONTAS = {}
RAIO_OBJ = []


def montar_raio():
    PONTAS['pr'] = para_raios('rpr', 0, 0, 7)
    PONTAS['pc'] = para_raios('rpc', 2.6, 1.3, 9, cristal=True)
    random.seed(77)
    topo = Vector((-2.0, 9.0, 34.0))
    bif = Vector((0.6, 2.4, 9.0))
    a_c, a_h = raio_obj('raio_alto', topo, bif, 0.05, 3, 6, 0.1, 8)
    b_c, b_h = raio_obj('raio_pr', bif, PONTAS['pr'], 0.03, 2, 5, 0.13, 8)
    c_c, c_h = raio_obj('raio_pc', bif + Vector((0.0, 0, 0)), PONTAS['pc'], 0.022, 2, 4, 0.14, 8)
    # líder escalonado (quadro 11): só galhos finos parados no ar
    d_c, d_h = raio_obj('raio_lider', topo, topo.lerp(bif, 0.9), 0.012, 2, 5, 0.12, 7)
    RAIO_OBJ.extend([a_c, a_h, b_c, b_h, c_c, c_h])
    l_ceu = bpy.data.lights.new('Clarão', 'AREA')
    l_ceu.shape = 'DISK'
    l_ceu.size = 8.0
    l_ceu.color = (0.75, 0.7, 1.0)
    o_ceu = bpy.data.objects.new('Clarão', l_ceu)
    sc.collection.objects.link(o_ceu)
    o_ceu.location = (0.0, 4.0, 14.0)
    o_ceu.rotation_euler = (math.radians(-20), 0, 0)
    l_bif = luz('luz_bifurca', (0.75, 0.65, 1.0), 0.0, bif, 0.3)

    def anima_raio(q, fr):
        f = forca(q)
        for o in (a_c, a_h, b_c, b_h, c_c, c_h):
            vis_q(o, q, f > 0.3)
        for o in (d_c, d_h):
            vis_q(o, q, q == 11)
        l_ceu.energy = 450.0 * f
        l_ceu.keyframe_insert('energy', frame=q)
        l_bif.data.energy = 5000.0 * f
        l_bif.data.keyframe_insert('energy', frame=q)
        RAIO_EM.default_value = 120.0 * max(f, 0.3)
        RAIO_EM.keyframe_insert('default_value', frame=q)
        DESC_EMIS.default_value = 40.0 * f
        DESC_EMIS.keyframe_insert('default_value', frame=q)
        DESC_HALO.default_value = 14.0 * f
        DESC_HALO.keyframe_insert('default_value', frame=q)
        CLARAO.default_value = 2.2 * f
        CLARAO.keyframe_insert('default_value', frame=q)
    ANIM.append(anima_raio)
    # chuva: riscos num padrão que se repete a cada PER m; o objeto desce em laço
    PER = 3.0
    ac = Acc()
    rr = random.Random(5)
    for k in range(4500):
        x, y = rr.uniform(-6, 8), rr.uniform(-6, 9)
        z = rr.uniform(0, PER)
        L = rr.uniform(0.16, 0.3)
        for rep in range(4):
            c = Vector((x, y, z + rep * PER))
            ac.prisma(c, c + Vector((0.03, 0.01, L)), 0.0013, 3)
    o = ac.objeto('chuva', 'chuva')
    o.visible_shadow = False

    def anima_chuva(q, fr, o=o):
        o.location = (0, 0, -((fr * 12 * PER) % PER))
        chave(o, 'location', q)
    ANIM.append(anima_chuva)
    # respingos no chão (coroas)
    for k in range(60):
        b = bmesh.new()
        p = Vector((rr.uniform(-2, 5), rr.uniform(-3, 4), 0.0))
        if max(abs(p.x), abs(p.y)) < 0.5 or max(abs(p.x - 2.6), abs(p.y - 1.3)) < 0.5:
            continue
        toro(b, p, 0.012, 0.0025, 12, 4)
        for j in range(5):
            a = j * 2 * PI / 5
            tubo(b, p + Vector((math.cos(a), math.sin(a), 0)) * 0.012, p + Vector((math.cos(a) * 0.02, math.sin(a) * 0.02, 0.02)), 0.0018, 4)
        obj('respingo%d' % k, b, 'chuva')


# ------------------------------------------------------------------ materiais animados (globais)
RAIO_EM = M['raio'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
MUNDO_T, CLARAO = ceu_tempestade()


def grupo(nome, construir):
    antes = set(o.name for o in sc.collection.objects)
    construir()
    col = bpy.data.collections.new(nome)
    sc.collection.children.link(col)
    for o in list(sc.collection.objects):
        if o.name not in antes:
            sc.collection.objects.unlink(o)
            col.objects.link(o)
    GRUPOS[nome] = col


import time
T0 = time.time()
grupo('pr', montar_pr)
print('T pr', time.time() - T0, flush=True)
grupo('pc', montar_pc)
print('T pc', time.time() - T0, flush=True)
grupo('raio', montar_raio)
print('T raio', time.time() - T0, flush=True)


def anima_cristal(q, fr):
    f = forca(q)
    CRIS_PC.default_value = 2.0 + 1.0 * math.sin(2 * PI * 2 * fr) + 40.0 * f + (10.0 if 12 <= q <= 22 else 0.0)
    CRIS_PC.keyframe_insert('default_value', frame=q)
    CARGA_EMIS.default_value = 2.0 + 25.0 * f + (8.0 if 12 <= q <= 18 else 0.0)
    CARGA_EMIS.keyframe_insert('default_value', frame=q)


ANIM.append(anima_cristal)

# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for f in ANIM:
        f(q, fr)
for o in list(sc.objects) + list(bpy.data.lights) + [m.node_tree for m in bpy.data.materials if m.node_tree] + \
        [w.node_tree for w in bpy.data.worlds if w.node_tree]:
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action and hasattr(ad.action, 'fcurves'):
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR' if not fc.data_path.startswith('hide') else 'CONSTANT'

print('T anim', time.time() - T0, flush=True)
# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (200, 200, 1.0))
CHAO = obj('chao', bm, 'chao')
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (200, 200, 1.0))
CHAO_M = obj('chao_molhado', bm, 'chao_chuva')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
lua = bpy.data.lights.new('Penumbra', 'SUN')
lua.energy = 0.0
lua.color = (0.6, 0.65, 0.85)
lo = bpy.data.objects.new('Penumbra', lua)
sc.collection.objects.link(lo)
lo.rotation_euler = (math.radians(35), 0, math.radians(160))
MUNDO = bpy.data.worlds.new('Mundo')
bg = MUNDO.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.55
sc.world = MUNDO
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
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def brilho(ligar):
    try:
        if ligar and not bpy.data.node_groups.get('Comp'):
            ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
            ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            rl = ng.nodes.new('CompositorNodeRLayers')
            gl = ng.nodes.new('CompositorNodeGlare')
            gl.inputs['Type'].default_value = 'Bloom'
            gl.inputs['Threshold'].default_value = 1.5
            gl.inputs['Strength'].default_value = 0.7
            gl.inputs['Size'].default_value = 0.85
            out = ng.nodes.new('NodeGroupOutput')
            ng.links.new(rl.outputs['Image'], gl.inputs['Image'])
            ng.links.new(gl.outputs[0], out.inputs[0])
        sc.compositing_node_group = bpy.data.node_groups.get('Comp') if ligar else None
        sc.render.use_compositing = ligar
    except Exception as ex:
        print('BRILHO falhou', ex)


def foto(arq, grp, quadro, pos, alvo, lente, rx, ry, amostras):
    for nome, col in GRUPOS.items():
        col.hide_render = nome != grp
    tempestade = grp == 'raio'
    CHAO.hide_render = tempestade
    CHAO_M.hide_render = not tempestade
    sc.world = MUNDO_T if tempestade else MUNDO
    sol.energy = 0.0 if tempestade else 4.0
    lua.energy = 0.08 if tempestade else 0.0
    sc.view_settings.exposure = -0.6 if tempestade else -0.5
    brilho(tempestade)
    sc.cycles.samples = amostras
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.frame_set(quadro)
    mirar(Vector(pos), Vector(alvo), lente)
    sc.render.filepath = os.path.join(AQUI, arq)
    bpy.ops.render.render(write_still=True)


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
FOTOS = {
    'pr': ('para_raios_0.png', 'pr', F_CALMO, (3.1, -3.7, 2.2), (0.02, 0.0, 1.85), 38, 1100, 1400),
    'pc': ('para_raios_cristal_0.png', 'pc', F_CALMO, (3.4, -4.1, 2.4), (0.02, 0.0, 2.15), 38, 1100, 1400),
    'raio': ('para_raios_raio.png', 'raio', F_RAIO, (2.0, -3.3, 0.75), (0.75, 0.6, 2.7), 17, 1200, 1500),
}
if modo in ('foto', 'teste'):
    so_uma = args[1] if len(args) > 1 else None
    for chave_f, (arq, grp, quadro, pos, alvo, lente, rx, ry) in FOTOS.items():
        if so_uma and chave_f != so_uma:
            continue
        if modo == 'teste':
            rx, ry = rx // 2, ry // 2
            arq = 'teste_' + arq
        foto(arq, grp, quadro, pos, alvo, lente, rx, ry, 128 if modo == 'foto' else 24)
elif modo == 'cam':
    grp, quadro = args[1], int(args[2])
    x, y, z, ax, ay, az, lente = map(float, args[3:10])
    arq = args[10]
    am = int(args[11]) if len(args) > 11 else 24
    foto(arq, grp, quadro, (x, y, z), (ax, ay, az), lente, 800, 800, am)
print('PARA_RAIOS ok')
