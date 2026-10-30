"""Estudo isolado (fora do jogo): MUROS NOVOS e MINA DE PULSO. Tudo 1×1 (1 tile = 1 m; x leste, y norte).
Os muros seguem o muro de pedra aprovado (estudo_poste_muro.py): pilar de 0,64 m no centro do tile e pano mais fino
do centro até a borda, um por vizinho (girado para os outros lados). Cada muro montado em L com 4 pilares.
- muros_reforcados (700 ♥) — MURO DE TIJOLO: tijolo refratário (três tons de queima, um ou outro trocado por tijolo
  comum vermelho) em aparelho corrido com amarração nos cantos e juntas de argamassa rebaixadas; sapata, cinta de
  concreto no meio (quina quebrada com vergalhão enferrujado à mostra), capa com espetos de vergalhão; cantoneiras
  aparafusadas nos cantos do pilar (um trecho faltando). Tijolos lascados, partidos ao meio e arrancados (buraco com
  entulho no pé), mordidas, ácido, salitre, rachaduras, musgo e lama. Emissor de campo da IA no topo.
- muro_liga (1.500 ♥, a aranha não escala) — MURO DE LIGA: chapas de liga lisa e escorregadia (brilho de película
  furta-cor, lubrificante escorrendo) rebitadas sobre quadro de aço, mata-juntas, cantoneiras de quina, topo
  inclinado para fora com lâminas serrilhadas (dentes quebrados); arranhões de garra que escorregam para baixo,
  manchas de ácido, chapa trocada em primer, remendo aparafusado, solda com mancha térmica, rodapé enlameado.
- muro_escudo (regenera 5 ♥/s com energia) — MURO DE CAMPO: pilar emissor (plinto de concreto com faixa de perigo,
  coluna com três bobinas esmaltadas em carretéis de fenolite com tirantes, saias de porcelana, coroa de cobre com
  eletrodo violeta e arcos), barras emissoras com pinos voltadas para os vizinhos, eletrocalha com cabos até os
  terminais, caixa de ligação, eletroduto, capacitor estufado. O pano é um trilho de concreto com pinos e uma parede
  de campo translúcida que ondula (ondas viajantes por chaves de forma, faixas e células que correm no material).
- mina_pulso (atordoa 3 s, rearma em 20 s) — MINA DE PULSO: carcaça verde-oliva semienterrada num monte de terra com
  mato, flange aparafusado, bobina toroidal vista entre os espaçadores, tampa blindada com nervuras, sensor de pressão
  com fole de borracha, LED piscando, antena de enlace da IA, capacitor meio enterrado ligado por cabos; torrões e
  mato por cima, capim deitado e chão queimado de disparos antigos.
  Animação (laço de 4 s, rearme comprimido): dispara no quadro 6 (tampa pula, bobina acende, arcos, faíscas, torrões
  e poeira) e solta uma onda circular que corre até ~2,8 m e some; depois o LED fica âmbar piscando cada vez mais
  rápido (carregando) e volta ao vermelho lento (armada).
Uso: blender -b --python estudo_muros_mina.py -- foto [chave]     (chaves: tijolo, liga, campo, mina, mina_disparo)
     blender -b --python estudo_muros_mina.py -- teste [chave]    (metade da resolução, 24 amostras)"""
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



# ------------------------------------------------------------------ do muro de pedra
def acido(P, c, n, r=0.04, gotas=3):
    """Mancha de ácido: borda queimada esfumada, miolo oliva molhado, escorridos finos e furinhos corroídos."""
    c, n = Vector(c), Vector(n).normalized()
    t1, t2 = base_parede(n)
    decal(P.B('chamusco'), c + n * 0.0008, n, r * 1.5, 15, 0.6)
    decal(P.B('acido_d'), c + n * 0.0016, n, r, 13, 0.6)
    for i in range(gotas):
        p = c + t1 * random.uniform(-r * 0.6, r * 0.6) - Z * r * 0.4
        escorrido(P.B('acido'), p + n * 0.0012, n, random.uniform(0.04, 0.13), random.uniform(0.004, 0.007))
    for i in range(3):
        p = c + t1 * random.uniform(-r * 0.4, r * 0.4) + t2 * random.uniform(-r * 0.4, r * 0.4)
        cil(P.B('fenda'), p + n * 0.002, random.uniform(0.0015, 0.003), 0.002, n, lados=7)


def musgo(P, c, r, k=6):
    for i in range(k):
        pedra(P.B('musgo'), Vector(c) + ruido_vec(r) * Vector((1, 1, 0.4)), random.uniform(0.01, 0.025), 0.45)


def arame_farpado(P, a, b, sag=0.008):
    """Dois fios torcidos de a a b com farpas a cada ~8 cm."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    u = (b - a).normalized()
    s = u.cross(Z).normalized()
    n = int(L / 0.004) + 2
    for fase in (0, PI):
        pts = []
        for i in range(n + 1):
            t = i / n
            ang = 2 * PI * (L * t) / 0.035 + fase
            pts.append(a.lerp(b, t) - Z * sag * 4 * t * (1 - t) + (s * math.cos(ang) + Z * math.sin(ang)) * 0.0022)
        varrer(P.B('cabo_aco', True), pts, 0.0013, 5)
    nb = max(1, int(L / 0.08))
    for i in range(nb):
        t = (i + 0.5) / nb
        p = a.lerp(b, t) - Z * sag * 4 * t * (1 - t)
        for k in range(2):
            ang = k * PI / 2 + i * 0.7
            d = (s * math.cos(ang) + Z * math.sin(ang)) * 0.012 + u * 0.004
            tubo(P.B('cabo_aco'), p - d, p + d, 0.0009, 4)
        toro(P.B('cabo_aco', True), p, 0.0035, 0.0011, 8, 4, u)



def tronco(bm, z0, z1, a0, a1):
    """Tronco de pirâmide quadrado (pingadeira entre a parte baixa e a alta)."""
    vs = [bm.verts.new((sx * a, sy * a, z)) for (z, a) in ((z0, a0), (z1, a1)) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs[3::-1])
    bm.faces.new(vs[4:])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))



# ================================================================== materiais novos
def liga_mat(nome, cor, rough, filme=360.0):
    """Liga lisa: metal pouco áspero, película fina furta-cor (lubrificante/óxido) e brilho alongado."""
    m = mats.material(nome, cor, 1.0, rough, pintura=False, ferrugem=0.1, sujeira=0.75, desgaste=0.0)
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    if filme > 0 and 'Thin Film Thickness' in b.inputs:
        b.inputs['Thin Film Thickness'].default_value = filme
        b.inputs['Thin Film IOR'].default_value = 1.42
    if 'Anisotropic' in b.inputs:
        b.inputs['Anisotropic'].default_value = 0.35
    return m


def campo_mat():
    """Parede de campo: transparente com emissão violeta (âmbar perto do trilho), células, faixas que correm,
    borda mais densa de lado (fresnel) e topo que se desfaz."""
    m = bpy.data.materials.new('Campo de energia')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no

    def op(o, a, b):
        n = no(nt, 'ShaderNodeMath', operation=o, use_clamp=False)
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    def faixa(v, a0, a1, b0, b1):
        n = no(nt, 'ShaderNodeMapRange', **{'From Min': a0, 'From Max': a1, 'To Min': b0, 'To Max': b1})
        nt.links.new(v, n.inputs['Value'])
        return n.outputs['Result']
    out = no(nt, 'ShaderNodeOutputMaterial')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    wave = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', wave_profile='SIN')
    wave.inputs['Scale'].default_value = 1.6
    wave.inputs['Distortion'].default_value = 4.0
    wave.inputs['Detail'].default_value = 3.0
    nt.links.new(geo.outputs['Position'], wave.inputs['Vector'])
    vor = no(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE')
    vor.inputs['Scale'].default_value = 13.0
    nt.links.new(geo.outputs['Position'], vor.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    lw = no(nt, 'ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.35
    linhas = faixa(vor.outputs['Distance'], 0.0, 0.045, 1.0, 0.0)
    bandas = faixa(wave.outputs['Fac'], 0.55, 1.0, 0.0, 1.0)
    falha = faixa(ru.outputs['Fac'], 0.35, 0.65, 0.25, 1.0)
    topo = faixa(sp.outputs['Z'], 1.12, 1.33, 1.0, 0.0)
    baixo = faixa(sp.outputs['Z'], 0.11, 0.32, 1.0, 0.0)
    a = op('MULTIPLY', linhas, falha)
    a = op('MULTIPLY', a, 0.42)
    a = op('ADD', a, op('MULTIPLY', bandas, 0.28))
    a = op('ADD', a, op('MULTIPLY', op('POWER', lw.outputs['Facing'], 2.0), 0.35))
    a = op('ADD', a, op('MULTIPLY', baixo, 0.3))
    a = op('ADD', a, 0.07)
    a = op('MULTIPLY', a, topo)
    alfa = no(nt, 'ShaderNodeClamp')
    nt.links.new(a, alfa.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.5, 0.13, 1.0, 1)
    cor.inputs[7].default_value = (1.0, 0.42, 0.07, 1)
    nt.links.new(op('MULTIPLY', baixo, 0.75), cor.inputs[0])
    em = no(nt, 'ShaderNodeEmission')
    nt.links.new(cor.outputs[2], em.inputs['Color'])
    nt.links.new(op('ADD', op('MULTIPLY', alfa.outputs[0], 7.0), 1.0), em.inputs['Strength'])
    gl = no(nt, 'ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.08
    gl.inputs['Color'].default_value = (0.6, 0.5, 0.9, 1)
    soma = no(nt, 'ShaderNodeAddShader')
    nt.links.new(em.outputs[0], soma.inputs[0])
    nt.links.new(gl.outputs[0], soma.inputs[1])
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(alfa.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(soma.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m, wave.inputs['Phase Offset']


def onda_mat():
    """Anel da onda de pulso: faixa translúcida com emissão que cresce para a borda externa (coordenada do objeto)."""
    m = bpy.data.materials.new('Onda de pulso (anel)')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    tc = no(nt, 'ShaderNodeTexCoord')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sp.inputs[0])
    cb = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sp.outputs['X'], cb.inputs['X'])
    nt.links.new(sp.outputs['Y'], cb.inputs['Y'])
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(cb.outputs[0], ln.inputs[0])
    rr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.72, 'From Max': 1.0, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(ln.outputs['Value'], rr.inputs['Value'])
    pw = no(nt, 'ShaderNodeMath', operation='POWER')
    pw.inputs[1].default_value = 3.0
    nt.links.new(rr.outputs['Result'], pw.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(pw.outputs[0], mr.inputs[0])
    nt.links.new(ru.outputs['Fac'], mr.inputs[1])
    a = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    a.inputs[1].default_value = 1.6
    nt.links.new(mr.outputs[0], a.inputs[0])
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.62, 0.3, 1.0, 1)
    em.inputs['Strength'].default_value = 6.0
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(a.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m, em.inputs['Strength']


M.update({
    'tij1': mats.material('Tijolo refratário', (0.56, 0.38, 0.19), 0, 0.88, pintura=False, sujeira=1.0, desgaste=0.0, ferrugem=0.2),
    'tij2': mats.material('Tijolo refratário escuro', (0.45, 0.25, 0.12), 0, 0.85, pintura=False, sujeira=1.0, desgaste=0.0, ferrugem=0.2),
    'tij3': mats.material('Tijolo refratário claro', (0.64, 0.52, 0.33), 0, 0.9, pintura=False, sujeira=1.0, desgaste=0.0, ferrugem=0.1),
    'tij4': mats.material('Tijolo comum (trocado)', (0.36, 0.1, 0.055), 0, 0.85, pintura=False, sujeira=1.0, desgaste=0.0),
    'tij_q': mats.material('Tijolo queimado', (0.13, 0.085, 0.06), 0, 0.8, pintura=False, sujeira=1.0, desgaste=0.0),
    'arg_tij': mats.material('Argamassa do tijolo', (0.3, 0.28, 0.24), 0, 0.95, pintura=False, sujeira=1.0, desgaste=0.0),
    'quebra_tij': mats.material('Tijolo recém-quebrado', (0.72, 0.5, 0.3), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'quebra_tij_d': decal_mat('Lasca de tijolo', (0.7, 0.48, 0.28), 0.95, borda=0.9),
    'salitre_d': decal_mat('Salitre', (0.52, 0.5, 0.45), 0.95, borda=0.12),
    'concreto_cinta': mats.material('Concreto da cinta', (0.4, 0.39, 0.36), 0, 0.9, sujeira=1.0, desgaste=0.0, ferrugem=0.3),
    'liga': liga_mat('Liga lisa', (0.74, 0.75, 0.77), 0.17, 0.0),
    'liga_b': liga_mat('Liga trocada', (0.58, 0.55, 0.5), 0.24, 0.0),
    'liga2': mats.material('Liga das mata-juntas', (0.32, 0.33, 0.35), 1.0, 0.32, pintura=False, ferrugem=0.35, sujeira=0.9),
    'lamina': mats.material('Lâmina', (0.55, 0.55, 0.57), 1.0, 0.25, pintura=False, ferrugem=0.55, sujeira=0.6, escovado=True),
    'risco': mats.material('Risco de garra', (0.86, 0.86, 0.88), 1.0, 0.2, pintura=False, sujeira=0.0, desgaste=0.0),
    'solda': mats.material('Cordão de solda', (0.16, 0.14, 0.12), 0.8, 0.6, pintura=False, ferrugem=0.6, sujeira=0.6),
    'termico_d': decal_mat('Mancha térmica', (0.16, 0.12, 0.3), 0.25, metal=1.0, borda=0.4),
    'oleo_d': decal_mat('Lubrificante', (0.03, 0.025, 0.015), 0.05, borda=0.5),
    'esmalte': mats.material('Fio esmaltado', (0.42, 0.13, 0.04), 0.8, 0.28, pintura=False, sujeira=0.6, desgaste=0.0),
    'oliva': mats.material('Verde-oliva', (0.12, 0.13, 0.06), 0, 0.55, desgaste=1.0, sujeira=1.0, ferrugem=0.7),
    'terra': mats.material('Terra', (0.085, 0.058, 0.034), 0, 0.97, pintura=False, sujeira=0.5, desgaste=0.0),
    'terra_d': decal_mat('Terra (mancha)', (0.075, 0.052, 0.032), 0.95, borda=0.4),
    'mato': mats.material('Mato', (0.11, 0.16, 0.035), 0, 0.7, pintura=False, sujeira=0.3, desgaste=0.0),
    'mato_seco': mats.material('Mato seco', (0.3, 0.24, 0.1), 0, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'poeira_pulso': base3d.volume_mat('Poeira do pulso', (0.3, 0.24, 0.17), 3.0, 0.0, 0.3),
})
M['campo'], CAMPO_FASE = campo_mat()
M['onda'], ONDA_FORCA = onda_mat()
M['onda_aro'] = emissivo('Onda de pulso (aro)', (0.8, 0.55, 1.0), 14.0)
ONDA_ARO = M['onda_aro'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
M['bobina_luz'] = emissivo('Bobina carregada', (0.6, 0.18, 1.0), 2.0)
BOBINA_LUZ = M['bobina_luz'].node_tree.nodes['Principled BSDF']
M['led_mina'] = emissivo('LED da mina', (1.0, 0.06, 0.03), 14.0)
LED_MINA = M['led_mina'].node_tree.nodes['Principled BSDF']
for k_, kw in (('tij1', dict(amassado=0.2)), ('tij2', dict(amassado=0.2)), ('tij3', dict(amassado=0.2)),
               ('tij4', dict(amassado=0.2)), ('tij_q', dict(amassado=0.2)), ('arg_tij', dict(amassado=0.0)),
               ('concreto_cinta', dict(amassado=0.0, fuligem=0.7)), ('liga', dict(amassado=0.18, poeira=0.45, fuligem=0.5)),
               ('liga_b', dict(amassado=0.2, poeira=0.6)), ('liga2', dict(amassado=0.0, fuligem=0.3)), ('lamina', dict(amassado=0.0, poeira=0.4)),
               ('oliva', dict(amassado=0.2, poeira=0.35)), ('esmalte', dict(amassado=0.0, poeira=0.4)), ('terra', dict(amassado=0.0, lama=0.0, poeira=0.12, fuligem=0.3))):
    rustico(M[k_], **kw)
for k_, f_, e_ in (('tij1', 0.5, 45), ('tij2', 0.5, 45), ('tij3', 0.5, 45), ('tij4', 0.5, 45), ('tij_q', 0.5, 45),
                   ('arg_tij', 0.9, 70), ('concreto_cinta', 0.45, 50), ('quebra_tij', 0.8, 50), ('terra', 1.0, 30)):
    aspero(M[k_], f_, e_)


def fim_objs(P):
    antes = set(o.name for o in sc.objects)
    P.fim()
    return [o for o in sc.objects if o.name not in antes]


# ================================================================== utilidades comuns aos muros
def mordida_m(P, c, n, h, esc=1.0, lasca='quebra_d'):
    """Mordida de aranha: lasca arrancada, dois furos de presa em V e riscos de garra."""
    c, n, h = Vector(c), Vector(n), Vector(h)
    decal(P.B(lasca), c + n * 0.001, n, 0.035 * esc, 11, 0.6, 1.3)
    for sx in (-1, 1):
        p0 = c + h * sx * 0.03 * esc + Z * 0.02 * esc
        p1 = c + h * sx * 0.008 * esc - Z * 0.015 * esc
        u = (p1 - p0).normalized()
        caixa(P.B('fenda'), (p0 + p1) / 2 + n * 0.0015, ((p1 - p0).length, 0.003, 0.006 * esc), rot_cols(u, n, u.cross(n)))
    for i in range(3):
        p0 = c + h * (0.05 + i * 0.011) * esc + Z * 0.05 * esc
        p1 = p0 + (h * 0.025 - Z * 0.08) * esc
        u = (p1 - p0).normalized()
        caixa(P.B('fenda'), (p0 + p1) / 2 + n * 0.0015, ((p1 - p0).length, 0.0014, 0.0022), rot_cols(u, n, u.cross(n)))


def marcas_garra(P, c, n, comp=0.35, k=4, larg=0.015, curva=0.03):
    """Arranhões de garra que escorrega: riscos paralelos brilhantes com sulco escuro, fundos no alto e
    afinando para baixo, levemente curvos (a pata gira enquanto desliza)."""
    c, n = Vector(c), Vector(n).normalized()
    t1, t2 = base_parede(n)
    sent = random.choice((-1, 1))
    for i in range(k):
        p0 = c + t1 * (i - (k - 1) / 2) * larg * random.uniform(0.85, 1.15) + t2 * random.uniform(-0.012, 0.012)
        L = comp * random.uniform(0.7, 1.1)
        m = 9
        pts = [p0 - t2 * L * (j / m) + t1 * sent * curva * math.sin(j / m * PI * 0.7) + n * 0.0007 for j in range(m + 1)]
        for j, (a, b) in enumerate(zip(pts, pts[1:])):
            u = (b - a).normalized()
            w = 0.0042 * (1 - 0.8 * j / m)
            R = rot_cols(u, n, u.cross(n))
            caixa(P.B('risco'), (a + b) / 2, ((b - a).length + 0.0012, 0.0012, w), R)
            caixa(P.B('fenda'), (a + b) / 2 + n * 0.0005, ((b - a).length + 0.0012, 0.0012, w * 0.35), R)


def entulho(P, c, r, k, mats_=('tij1', 'tij2', 'arg_tij')):
    for i in range(k):
        p = Vector(c) + Vector((random.uniform(-r, r), random.uniform(-r, r), 0))
        pedra(P.B(random.choice(mats_)), p, random.uniform(0.007, 0.022), 0.6)


def emissor_topo(P, nome, zt2):
    """Emissor de campo da IA (como no muro de pedra): base, bobininhas de cobre, núcleo violeta e anel que gira."""
    cil(P.B('grafite'), (0, 0, zt2 + 0.004), 0.055, 0.008, lados=24)
    for k in range(4):
        toro(P.B('cobre', True), (0, 0, zt2 + 0.012 + k * 0.007), 0.032, 0.0037, 28, 6)
    cil(P.B('violeta'), (0, 0, zt2 + 0.022), 0.024, 0.03, lados=16)
    for k in range(3):
        a = k * 2 * PI / 3
        tubo(P.B('aco'), (math.cos(a) * 0.045, math.sin(a) * 0.045, zt2 + 0.008), (math.cos(a) * 0.045, math.sin(a) * 0.045, zt2 + 0.035), 0.003, 6)
    decal(P.B('chamusco'), (0.0, 0.0, zt2 + 0.0005), Z, 0.085)
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 0.05, 0.0035, 36, 8)
    anel = suavizar(obj(nome + '_anel', bm, 'violeta'))
    p_an = P.W((0, 0, zt2 + 0.043))
    anel.location = p_an
    anel.rotation_mode = 'QUATERNION'
    lz = luz(nome + '_luz_emissor', (0.6, 0.2, 1.0), 1.5, P.W((0, 0, zt2 + 0.05)), 0.04)
    fse = random.random()

    def anima(q, fr, anel=anel, lz=lz, fse=fse, z_an=p_an.z):
        anel.rotation_quaternion = Quaternion(Z, 2 * PI * 2 * fr) @ Quaternion((1, 0, 0), 0.1 * math.sin(2 * PI * (fr + fse)))
        anel.location.z = z_an + 0.004 * math.sin(2 * PI * 2 * (fr + fse))
        lz.data.energy = 1.0 + 0.8 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr))
        chave(anel, 'rotation_quaternion', q)
        chave(anel, 'location', q)
        lz.data.keyframe_insert('energy', frame=q)
    ANIM.append(anima)


def espetos_vergalhao(P, pts, z, alt=0.05):
    for i, (x, y) in enumerate(pts):
        if random.random() < 0.08:                                       # espeto torto
            cil(P.B('aco'), (x + 0.008, y, z + 0.012), 0.008, alt * 0.7, Vector((0.7, 0.2, 1)), lados=6, r2=0.0008)
            continue
        cil(P.B('aco'), (x, y, z + alt / 2), 0.0085, alt, lados=6, r2=0.0008)
        if random.random() < 0.3:
            pedra(P.B('crosta'), (x, y, z + 0.004), 0.009, 0.5)


# ================================================================== MURO DE TIJOLO (muros_reforcados)
TJ_L, TJ_H, TJ_D, JT = 0.23, 0.065, 0.10, 0.011
TB = 0.30                          # face dos tijolos do pilar
ZT_0 = 0.06                        # topo da sapata
ZT_C0, ZT_C1 = 0.70, 0.82          # cinta de concreto
ZT_T = 1.40                        # topo dos tijolos do pilar
HZ_UP = (ZT_T - ZT_C1) / 8
ZT_P = ZT_C1 + 4 * HZ_UP           # topo dos tijolos do pano (casa com uma junta do pilar)
ZT_PC = ZT_C1 + 5 * HZ_UP          # topo da capa do pano
PXT = 0.11                         # meia espessura do pano (face dos tijolos)
TIJ_MATS = ('tij1',) * 9 + ('tij2',) * 5 + ('tij3',) * 4 + ('tij_q',) + ('tij4',)


def bloco_tijolo(bm, c, tam, rot, lasca=0.0, rr=random):
    """Tijolo: icosfera empurrada para caixa de quina viva levemente gasta; às vezes com a quina de fora lascada."""
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    sem = Vector((rr.uniform(0, 50), rr.uniform(0, 50), rr.uniform(0, 50)))
    k = Vector((rr.choice((-1, 1)), 1, rr.choice((-1, 1)))).normalized()
    corta = rr.random() < lasca
    for v in res['verts']:
        p = v.co.copy()
        q = Vector([math.copysign(abs(p[i]) ** 0.11, p[i]) for i in range(3)])
        q *= 1 - 0.035 * abs(noise.noise(p * 2.0 + sem)) - 0.02 * abs(noise.noise(p * 7 + sem))
        if corta and q.dot(k) > 1.2:
            q -= k * (q.dot(k) - 1.2) * 0.95
        v.co = Vector(c) + rot @ Vector((q.x * tam[0] / 2, q.y * tam[1] / 2, q.z * tam[2] / 2))
    return corta, k


def fiadas(P, n, h, dist, z0, z1, vaos, inicio, borda=None, dep=TJ_D, perdas=True):
    """Assenta tijolos em aparelho corrido numa face vertical de normal n. vaos(i) → lista de (a, b) ao longo de h;
    inicio(i) → onde começa um tijolo naquela fiada. Juntas: faixa de argamassa rebaixada atrás de cada fiada
    (some onde o tijolo foi arrancado: buraco de verdade até o miolo). borda: s onde a peça encontra o vizinho; o
    tijolo partido ali tem cor e forma sorteadas pela posição no mundo, para casar com a outra metade."""
    n, h = Vector(n).normalized(), Vector(h).normalized()
    rot = rot_cols(h, n, Z)
    nf = max(1, round((z1 - z0) / (TJ_H + JT)))
    hz = (z1 - z0) / nf
    passo = TJ_L + JT
    lista, buracos = [], []
    for i in range(nf):
        zb = z0 + i * hz
        zm = zb + hz / 2
        s0 = inicio(i)
        for (a, b) in vaos(i, zb):
            furos = []
            k = math.floor((a - s0) / passo)
            while True:
                ja = s0 + k * passo
                k += 1
                if ja >= b - 0.004:
                    break
                ea, eb = max(ja, a), min(ja + TJ_L, b)
                if eb - ea < 0.025:
                    continue
                na_borda = borda is not None and abs(eb - borda) < 1e-4
                rr = random
                if na_borda:
                    wp = P.W(n * dist + h * borda + Z * zm)
                    rr = random.Random(int(round(wp.x * 100)) * 7919 + int(round(wp.y * 100)) * 104729 + int(round(wp.z * 1000)))
                mat = rr.choice(TIJ_MATS)
                sai = rr.uniform(-0.004, 0.002)
                cc = n * (dist - dep / 2 + sai) + h * ((ea + eb) / 2) + Z * zm
                canto = ea <= a + 1e-4 or eb >= b - 1e-4
                face = n * dist + h * ((ea + eb) / 2) + Z * zm
                if perdas and not canto and zb > 0.14 and random.random() < 0.03:          # tijolo arrancado
                    furos.append((ea, eb))
                    buracos.append((face, n, h, eb - ea, hz))
                    for _ in range(3):
                        pedra(P.B(random.choice(('tij1', 'arg_tij', 'quebra_tij'))), n * (dist - dep + 0.02) + h * random.uniform(ea + 0.02, eb - 0.02) + Z * (zb + 0.012), 0.012, 0.6)
                    continue
                tam = (eb - ea, dep, hz - JT)
                if perdas and not na_borda and eb - ea > 0.12 and random.random() < 0.06:  # partido em dois
                    corte = ea + random.uniform(0.35, 0.65) * (eb - ea)
                    for (pa, pb, dz, gira, rec) in ((ea, corte - 0.0035, 0.0, 0.0, 0.0),
                                                    (corte + 0.0035, eb, -0.004, random.uniform(-0.07, 0.07), 0.005)):
                        r2 = rot @ Matrix.Rotation(gira, 3, 'Y')
                        bloco_tijolo(P.B(mat, True), n * (dist - dep / 2 + sai - rec) + h * ((pa + pb) / 2) + Z * (zm + dz), (pb - pa, dep, hz - JT), r2, 0.6)
                    caixa(P.B('fenda'), n * (dist - 0.0075) + h * corte + Z * zm, (0.007, 0.001, hz - JT), rot)
                    lista.append((face, n, h, eb - ea, hz))
                    continue
                corta, kk = bloco_tijolo(P.B(mat, True), cc, tam, rot, 0 if na_borda else 0.22, rr)
                lista.append((face, n, h, eb - ea, hz))
            segs = [(a, b)]
            for fa, fb in furos:
                novo = []
                for sa, sb in segs:
                    if fb <= sa or fa >= sb:
                        novo.append((sa, sb))
                        continue
                    if fa > sa:
                        novo.append((sa, fa))
                    if fb < sb:
                        novo.append((fb, sb))
                segs = novo
            for sa, sb in segs:
                if sb - sa > 0.004:
                    caixa(P.B('arg_tij'), n * (dist - 0.008 - (dep - 0.009) / 2) + h * ((sa + sb) / 2) + Z * zm, (sb - sa, dep - 0.009, hz), rot)
    return lista, buracos


def vergalhao_exposto(P, c, n, h):
    """Quina de concreto quebrada: lasca clara, dois vergalhões enferrujados à mostra e escorrido."""
    c, n, h = Vector(c), Vector(n), Vector(h)
    decal(P.B('quebra'), c + n * 0.001, n, 0.045, 12, 0.5, 1.4)
    for k in (-1, 1):
        p = c + h * k * 0.018 + Z * 0.012
        tubo(P.B('crosta'), p - h * 0.04 - n * 0.006, p + h * 0.03 + n * 0.004, 0.0048, 8)
        pedra(P.B('crosta'), p + n * 0.004, 0.006, 0.5)
    escorrido(P.B('escorre'), c - Z * 0.02 + n * 0.001, n, 0.025, 0.012)


def tijolo_centro(nome, cx, cy, lados, seed):
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    caixa_de(P.B('concreto'), (-0.325, -0.325, 0.0), (0.325, 0.325, ZT_0))
    ci = TB - TJ_D + 0.001
    caixa_de(P.B('arg_tij'), (-ci, -ci, ZT_0), (ci, ci, ZT_T))
    faces = []
    for qd in range(4):
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        n = R @ Vector((0, 1, 0))
        h = R @ Vector((-1, 0, 0))
        tem = qd in lados

        def vaos(i, zb, qd=qd, tem=tem, base=0):
            a, b = (-TB, TB) if (qd + i + base) % 2 == 0 else (-TB + TJ_D, TB - TJ_D)
            if tem and zb < ZT_PC - 0.01:
                return [(a, -PXT), (PXT, b)]
            return [(a, b)]
        l1, b1 = fiadas(P, n, h, TB, ZT_0, ZT_C0, vaos, lambda i, qd=qd: -TB if (qd + i) % 2 == 0 else -TB + TJ_D)
        l2, b2 = fiadas(P, n, h, TB, ZT_C1, ZT_T, lambda i, zb, qd=qd, tem=tem: vaos(i, zb, qd, tem, 1),
                        lambda i, qd=qd: -TB if (qd + i + 1) % 2 == 0 else -TB + TJ_D)
        faces.append((qd, n, h, tem, l1 + l2, b1 + b2))
    # cinta de concreto (quina quebrada com vergalhão) e número de série
    caixa_de(P.B('concreto_cinta'), (-0.315, -0.315, ZT_C0), (0.315, 0.315, ZT_C1))
    qv = random.randrange(4)
    for qd, n, h, tem, lst, bur in faces:
        if qd == qv:
            vergalhao_exposto(P, n * 0.315 + h * 0.26 + Z * (ZT_C0 + 0.05), n, h)
        if not tem and qd != qv:
            serie_plana(P.B('tinta'), n * 0.3155 + h * -0.12 + Z * (ZT_C0 + 0.06), n, 0.028, 5)
        rachadura_plana(P.B('fenda'), n * 0.3158 + h * random.uniform(-0.15, 0.15) + Z * ZT_C1, n, 0.1, -PI / 2, 4)
        escorrido(P.B('escorre'), n * 0.3157 + h * random.uniform(-0.25, 0.25) + Z * (ZT_C1 - 0.012), n, 0.09, 0.01)
    # cantoneiras nos quatro cantos (em dois trechos: abaixo e acima da cinta), um trecho faltando
    falta = (random.randrange(4), random.randrange(2))
    C = TB + 0.006
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        for t, (z0, z1) in enumerate(((ZT_0 + 0.005, ZT_C0 - 0.006), (ZT_C1 + 0.006, ZT_T - 0.01))):
            if (i, t) == falta:
                z1 = z0 + 0.16
                decal(P.B('quebra_tij_d'), Vector((sx * (TB + 0.002), sy * (TB - 0.03), z1 + 0.05)), Vector((sx, 0, 0)), 0.02)
            caixa_de(P.B('galv'), (min(sx * C, sx * (C - 0.006)), min(sy * C, sy * (C - 0.055)), z0),
                     (max(sx * C, sx * (C - 0.006)), max(sy * C, sy * (C - 0.055)), z1))
            caixa_de(P.B('galv'), (min(sx * C, sx * (C - 0.055)), min(sy * C, sy * (C - 0.006)), z0),
                     (max(sx * C, sx * (C - 0.055)), max(sy * C, sy * (C - 0.006)), z1))
            zz = z0 + 0.06
            while zz < z1 - 0.04:
                porca(P.B('aco'), (sx * (C + 0.0005), sy * (C - 0.03), zz), Vector((sx, 0, 0)), 0.008, 0.006)
                porca(P.B('aco'), (sx * (C - 0.03), sy * (C + 0.0005), zz + 0.04), Vector((0, sy, 0)), 0.008, 0.006)
                zz += 0.2
            ninho(P, (sx * (C + 0.003), sy * (C - 0.03), z1 - 0.012), Vector((sx, 0, 0)), 0.011, 4, min(0.16, z1 - z0 - 0.04))
    # capa com pingadeira, chapa e espetos de vergalhão
    caixa_de(P.B('concreto_cinta'), (-0.32, -0.32, ZT_T), (0.32, 0.32, ZT_T + 0.07))
    caixa_de(P.B('quebra'), (-0.3205, 0.27, ZT_T + 0.03), (-0.28, 0.3205, ZT_T + 0.0705))
    rachadura_plana(P.B('fenda'), (0.08, -0.3205, ZT_T + 0.065), (0, -1, 0), 0.06, -PI / 2, 3)
    zt = ZT_T + 0.07
    pts = [(x, y) for x in (-0.25, -0.125, 0.0, 0.125, 0.25) for y in (-0.25, 0.25)] + [(x, y) for x in (-0.25, 0.25) for y in (-0.125, 0.0, 0.125)]
    espetos_vergalhao(P, pts, zt)
    for k in range(3):
        decal(P.B('chamusco'), (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), zt + 0.0004), Z, random.uniform(0.04, 0.08))
    emissor_topo(P, nome, zt)
    # marcas das aranhas, salitre, musgo, lama, entulho dos buracos
    baixos = [(c, n, h) for f in faces for (c, n, h, w, hz) in f[4] if 0.2 < c.z < ZT_C0 and w > 0.1]
    altos = [(c, n, h) for f in faces for (c, n, h, w, hz) in f[4] if c.z > ZT_C1 and w > 0.1]
    random.shuffle(baixos)
    random.shuffle(altos)
    for (c, n, h) in baixos[:2]:
        mordida_m(P, c + n * 0.003, n, h, 0.85, 'quebra_tij_d')
    for (c, n, h) in baixos[2:4] + altos[:1]:
        acido(P, c + n * 0.003, n, 0.038, 3)
    for qd, n, h, tem, lst, bur in faces:
        for (c, n_, h_, w, hz) in bur:
            entulho(P, Vector((c.x, c.y, 0)) * 1.0 + n_ * 0.06, 0.06, 7, ('tij1', 'tij2', 'arg_tij', 'quebra_tij'))
        if not tem:
            rachadura_plana(P.B('fenda'), n * (TB + 0.002) + h * random.uniform(-0.1, 0.1) + Z * 1.3, n, 0.3, -PI / 2, 8, 0.0022)
        k_m = 3 if n.y > 0.5 else 1
        for k in range(k_m):
            sv = random.uniform(-0.22, 0.22)
            musgo(P, n * 0.31 + h * sv + Z * ZT_0, 0.06, 6)
            decal(P.B('musgo_d'), n * (TB + 0.004) + h * sv + Z * 0.11, n, 0.07, alongar=1.5)
        for k in range(3):
            decal(P.B('lama'), n * (TB + 0.0045) + h * random.uniform(-0.25, 0.25) + Z * random.uniform(0.08, 0.16), n, random.uniform(0.03, 0.05))
    P.fim()


def tijolo_lado(nome, cx, cy, quartos, seed):
    """Pano de tijolo do centro até a borda norte (local), girado por quartos (N=0, O=1, S=2, L=3)."""
    random.seed(seed)
    P = Peca(nome, cx, cy, quartos * PI / 2)
    caixa_de(P.B('concreto'), (-0.125, TB, 0.0), (0.125, 0.5, ZT_0))
    ci = PXT - TJ_D + 0.001
    caixa_de(P.B('arg_tij'), (-ci, TB - 0.08, ZT_0), (ci, 0.5, ZT_P))
    lst, bur = [], []
    h = Vector((0, 1, 0))
    for sx in (-1, 1):
        n = Vector((sx, 0, 0))
        for (z0, z1, off) in ((ZT_0, ZT_C0, 0), (ZT_C1, ZT_P, 1)):
            l, b = fiadas(P, n, h, PXT, z0, z1, lambda i, zb: [(TB, 0.5)],
                          lambda i, off=off: 0.5 + JT / 2 if (i + off) % 2 == 0 else 0.5 - TJ_L / 2, borda=0.5)
            lst += l
            bur += b
    # cinta (continua a do pilar) e capa com espetos
    caixa_de(P.B('concreto_cinta'), (-0.125, TB, ZT_C0), (0.125, 0.5, ZT_C1))
    caixa_de(P.B('concreto_cinta'), (-0.13, TB, ZT_P), (0.13, 0.5, ZT_PC))
    sx = random.choice((-1, 1))
    vergalhao_exposto(P, (sx * 0.1255, 0.43, ZT_C0 + 0.05), Vector((sx, 0, 0)), Vector((0, 1, 0)))
    rachadura_plana(P.B('fenda'), (0.0, 0.41, ZT_PC + 0.0004), Z, 0.07, PI * random.uniform(0.3, 0.7), 4)
    decal(P.B('quebra'), (-sx * 0.1305, 0.47, ZT_P + 0.04), (-sx, 0, 0), 0.025)
    espetos_vergalhao(P, [(-0.07, 0.36), (0.07, 0.36), (0.0, 0.41), (-0.07, 0.46), (0.07, 0.46)], ZT_PC, 0.045)
    for k in range(2):
        decal(P.B('chamusco'), (random.uniform(-0.08, 0.08), random.uniform(0.33, 0.48), ZT_PC + 0.0004), Z, 0.04)
    for s2 in (-1, 1):
        escorrido(P.B('escorre'), (s2 * 0.1257, random.uniform(0.33, 0.47), ZT_C1 - 0.01), Vector((s2, 0, 0)), 0.09, 0.009)
    random.shuffle(lst)
    feitas = 0
    for (c, n, h_, w, hz) in lst:
        if 0.25 < c.z < 0.65 and w > 0.12 and feitas < 1:
            mordida_m(P, c + n * 0.003, n, h_, 0.75, 'quebra_tij_d')
            feitas += 1
    for (c, n, h_, w, hz) in lst[4:6]:
        acido(P, c + n * 0.003, n, 0.03, 2)
    rachadura_plana(P.B('fenda'), (-sx * (PXT + 0.002), 0.42, 1.05), (-sx, 0, 0), 0.24, -PI / 2, 7, 0.0022)
    for (c, n, h_, w, hz) in bur:
        entulho(P, Vector((c.x, c.y, 0)) + n * 0.05, 0.05, 6, ('tij1', 'tij2', 'arg_tij', 'quebra_tij'))
    for s2 in (-1, 1):
        musgo(P, (s2 * 0.11, 0.42, ZT_0 - 0.01), 0.06, 6)
        decal(P.B('musgo_d'), (s2 * (PXT + 0.004), 0.41, 0.11), (s2, 0, 0), 0.06, alongar=1.4)
        for k in range(3):
            decal(P.B('lama'), (s2 * (PXT + 0.0045), random.uniform(0.33, 0.48), random.uniform(0.08, 0.15)), (s2, 0, 0), random.uniform(0.025, 0.045))
    P.fim()


# ================================================================== MURO DE LIGA (muro_liga)
LG = 0.29             # face das chapas do pilar (parte reta)
LG_T = 0.32           # borda do topo inclinado
ZL_B = 0.07           # topo da sapata
ZL_I, ZL_T = 1.20, 1.38   # topo inclinado do pilar
CH = 0.012            # espessura da chapa
PXL, PXL_T = 0.075, 0.115
ZLP_I, ZLP_T = 1.02, 1.18


def chapa(P, n, h, dist, s0, s1, z0, z1, mat=None, gap=0.0022, passo=0.058, ins=0.016):
    """Chapa de liga sobre o quadro: caixa fina com rebites no contorno (um ou outro faltando: só o furo)."""
    n, h = Vector(n), Vector(h)
    if mat is None:
        r = random.random()
        mat = 'liga_b' if r < 0.1 else ('oxido' if r < 0.14 else 'liga')
    rot = rot_cols(h, n, Z)
    a, b, za, zb = s0 + gap, s1 - gap, z0 + gap, z1 - gap
    caixa(P.B(mat), n * (dist - CH / 2) + h * ((a + b) / 2) + Z * ((za + zb) / 2), (b - a, CH, zb - za), rot)
    pts = []
    nh = max(1, round((b - a - 2 * ins) / passo))
    nz = max(1, round((zb - za - 2 * ins) / passo))
    for i in range(nh + 1):
        s = a + ins + (b - a - 2 * ins) * i / nh
        pts += [(s, za + ins), (s, zb - ins)]
    for j in range(1, nz):
        z = za + ins + (zb - za - 2 * ins) * j / nz
        pts += [(a + ins, z), (b - ins, z)]
    for s, z in pts:
        c = n * dist + h * s + Z * z
        if random.random() < 0.04:
            cil(P.B('fenda'), c + n * 0.0004, 0.0033, 0.001, n, lados=8)
            escorrido(P.B('escorre'), c - Z * 0.004, n, random.uniform(0.03, 0.08), 0.005)
            continue
        cil(P.B('liga2', True), c + n * 0.0012, 0.0058, 0.0024, n, lados=10, r2=0.0042)
    return (n * dist + h * ((a + b) / 2) + Z * ((za + zb) / 2), n, h, b - a, zb - za, mat)


def prisma(bm, perfil, y0, y1):
    """Perfil (x, z) fechado extrudado ao longo de y."""
    A = [bm.verts.new((x, y0, z)) for x, z in perfil]
    B = [bm.verts.new((x, y1, z)) for x, z in perfil]
    bm.faces.new(list(reversed(A)))
    bm.faces.new(B)
    m = len(perfil)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((A[i], A[j], B[j], B[i]))


def lamina(P, a, b, n_out, desce=0.5, alc=0.04, dente=0.019):
    """Lâmina serrilhada presa na borda a→b, apontando para fora e para baixo; alguns dentes quebrados."""
    a, b = Vector(a), Vector(b)
    u = (b - a).normalized()
    L = (b - a).length
    d = Vector(n_out).normalized() * math.cos(desce) - Z * math.sin(desce)
    nd = max(2, int(L / dente))
    base = [a + u * L * i / nd for i in range(nd + 1)]
    fora = []
    for i in reversed(range(nd)):
        fora.append(a + u * L * (i + 1) / nd + d * alc * 0.5)
        ponta = 1.0 if random.random() > 0.12 else random.uniform(0.55, 0.7)
        fora.append(a + u * L * (i + 0.5) / nd + d * alc * ponta)
    fora.append(a + d * alc * 0.5)
    pts = base + fora
    nrm = u.cross(d).normalized()
    bm = P.B('lamina')
    v1 = [bm.verts.new(p + nrm * 0.0009) for p in pts]
    v2 = [bm.verts.new(p - nrm * 0.0009) for p in pts]
    bm.faces.new(v1)
    bm.faces.new(list(reversed(v2)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((v1[i], v1[j], v2[j], v2[i]))
    k = max(1, int(L / 0.1))
    for i in range(k + 1):
        porca(P.B('aco'), a + u * L * (i + 0.5) / (k + 1) + d * 0.008 + nrm * 0.001, nrm, 0.0055, 0.004, False)
    if random.random() < 0.6:
        ninho(P, a + u * L * random.uniform(0.2, 0.8) + d * 0.01, d, 0.006, 3, 0)


def solda(P, a, b, n):
    """Cordão de solda (gotas) com mancha térmica em volta."""
    a, b, n = Vector(a), Vector(b), Vector(n)
    L = (b - a).length
    k = int(L / 0.006)
    for i in range(k):
        pedra(P.B('solda'), a.lerp(b, i / k) + n * 0.002, 0.0042, 0.55)
    for i in range(3):
        decal(P.B('termico_d'), a.lerp(b, (i + 0.5) / 3) + n * 0.0008, n, L / 3.2, 13, 0.5, 1.0)


def liga_centro(nome, cx, cy, lados, seed):
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    caixa_de(P.B('concreto'), (-0.325, -0.325, 0.0), (0.325, 0.325, ZL_B))
    caixa_de(P.B('grafite'), (-LG + CH, -LG + CH, ZL_B), (LG - CH, LG - CH, ZL_I))     # quadro (não aparece)
    for sx in (-1, 1):
        for sy in (-1, 1):                                                 # chumbadores da sapata
            porca(P.B('aco'), (sx * 0.305, sy * 0.25, ZL_B), Z, 0.011, 0.009)
            porca(P.B('aco'), (sx * 0.25, sy * 0.305, ZL_B), Z, 0.011, 0.009)
    faces = []
    for qd in range(4):
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        n = R @ Vector((0, 1, 0))
        h = R @ Vector((-1, 0, 0))
        lst = []
        for (z0, z1) in ((ZL_B, 0.46), (0.46, 0.84), (0.84, ZL_I)):
            for (s0, s1) in ((-LG, 0.0), (0.0, LG)):
                lst.append(chapa(P, n, h, LG, s0, s1, z0, z1))
        faces.append((qd, n, h, qd in lados, lst))
        # mata-junta na dobra do topo
        caixa(P.B('liga2'), n * (LG + 0.004) + Z * (ZL_I - 0.012), (2 * LG, 0.008, 0.03), rot_cols(h, n, Z))
        for s in (-0.22, -0.11, 0.0, 0.11, 0.22):
            cil(P.B('liga2', True), n * (LG + 0.008) + h * s + Z * (ZL_I - 0.012), 0.006, 0.0024, n, lados=10, r2=0.004)
        # rodapé (cantoneira) com rasgos de dreno
        caixa(P.B('liga2'), n * (LG + 0.004) + Z * (ZL_B + 0.02), (2 * LG - 0.02, 0.008, 0.04), rot_cols(h, n, Z))
        for s in (-0.18, 0.0, 0.18):
            caixa(P.B('fenda'), n * (LG + 0.0085) + h * s + Z * (ZL_B + 0.012), (0.04, 0.001, 0.008), rot_cols(h, n, Z))
    # cantoneiras de quina
    for sx in (-1, 1):
        for sy in (-1, 1):
            C = LG + 0.005
            caixa_de(P.B('liga2'), (min(sx * C, sx * (C - 0.006)), min(sy * C, sy * (C - 0.045)), ZL_B),
                     (max(sx * C, sx * (C - 0.006)), max(sy * C, sy * (C - 0.045)), ZL_I))
            caixa_de(P.B('liga2'), (min(sx * C, sx * (C - 0.045)), min(sy * C, sy * (C - 0.006)), ZL_B),
                     (max(sx * C, sx * (C - 0.045)), max(sy * C, sy * (C - 0.006)), ZL_I))
            for zz in (0.15, 0.4, 0.65, 0.9, 1.12):
                cil(P.B('liga2', True), (sx * (C + 0.001), sy * (C - 0.022), zz), 0.0058, 0.0024, Vector((sx, 0, 0)), lados=10, r2=0.0042)
                cil(P.B('liga2', True), (sx * (C - 0.022), sy * (C + 0.001), zz + 0.03), 0.0058, 0.0024, Vector((0, sy, 0)), lados=10, r2=0.0042)
    # topo inclinado para fora, tampa e lâminas
    tronco(P.B('liga'), ZL_I, ZL_T, LG, LG_T)
    caixa_de(P.B('liga2'), (-LG_T - 0.004, -LG_T - 0.004, ZL_T), (LG_T + 0.004, LG_T + 0.004, ZL_T + 0.016))
    incl = math.atan2(LG_T - LG, ZL_T - ZL_I)
    for qd, n, h, tem, lst in faces:
        nn = (n * math.cos(incl) - Z * math.sin(incl))            # normal da face inclinada
        for t in (0.25, 0.75):
            zc = ZL_I + (ZL_T - ZL_I) * t
            dc = LG + (LG_T - LG) * t
            for s in (-0.2, -0.1, 0.0, 0.1, 0.2):
                cil(P.B('liga2', True), n * (dc + 0.001) + h * s * (dc / LG) + Z * zc, 0.0058, 0.0024, nn, lados=10, r2=0.0042)
        for k in range(2):                                                # lubrificante escorrendo da dobra
            p = n * (LG + 0.0007) + h * random.uniform(-0.24, 0.24) + Z * (ZL_I - 0.03)
            escorrido(P.B('oleo'), p, n, random.uniform(0.08, 0.22), random.uniform(0.0035, 0.005))
        e = LG_T + 0.002
        lamina(P, n * e + h * -(LG_T - 0.025) + Z * (ZL_T + 0.004), n * e + h * (LG_T - 0.025) + Z * (ZL_T + 0.004), n)
    emissor_topo(P, nome, ZL_T + 0.016)
    for k in range(2):
        decal(P.B('chamusco'), (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), ZL_T + 0.0165), Z, 0.07)
    # sensor (olho fixo) numa face sem pano
    livres = [f for f in faces if not f[3]] or faces
    qd, n, h, tem, lst = livres[0]
    pc = n * (LG + 0.006) + Z * 1.0
    caixa(P.B('grafite'), pc + h * 0.12, (0.08, 0.012, 0.1), rot_cols(h, n, Z))
    cil(P.B('vidro_escuro'), pc + h * 0.12 + n * 0.008 + Z * 0.015, 0.016, 0.006, n, lados=20)
    cil(P.B('led_r'), pc + h * 0.12 + n * 0.0115 + Z * 0.015, 0.005, 0.002, n, lados=12)
    serie_plana(P.B('tinta'), pc + h * 0.12 + n * 0.0062 - Z * 0.03, n, 0.009, 5)
    serie_plana(P.B('tinta'), n * (LG + 0.0004) + h * -0.15 + Z * 0.62, n, 0.03, 6)
    # chapa trocada / remendo aparafusado / solda
    qd, n, h, tem, lst = faces[random.randrange(4)]
    rc = n * (LG + 0.003) + h * 0.14 + Z * 0.3
    caixa(P.B('oxido'), rc, (0.13, 0.005, 0.11), rot_cols(h, n, Z))
    for a in (-1, 1):
        for b in (-1, 0, 1):
            porca(P.B('aco'), rc + n * 0.0025 + h * a * 0.052 + Z * b * 0.04, n, 0.007, 0.005)
    escorrido(P.B('escorre'), rc + h * 0.04 - Z * 0.05 + n * 0.003, n, 0.1, 0.01)
    qd, n, h, tem, lst = faces[(qd + 1) % 4]
    solda(P, n * LG + h * -0.2 + Z * 0.5, n * LG + h * -0.05 + Z * 0.5, n)
    # arranhões de garra, ácido, lama, poeira
    for qd, n, h, tem, lst in faces:
        for k in range(2 if tem else 3):
            c, n_, h_, w, hz, m = random.choice(lst)
            p = n * (LG + 0.0002) + h * random.uniform(-0.22, 0.22) + Z * random.uniform(0.55, 1.12)
            marcas_garra(P, p, n, random.uniform(0.22, 0.42), random.choice((3, 4)), random.uniform(0.013, 0.018))
        for k in range(2):
            p = n * (LG + 0.0005) + h * random.uniform(-0.22, 0.22) + Z * random.uniform(0.15, 0.75)
            acido(P, p, n, random.uniform(0.028, 0.042), 3)
        for k in range(3):
            decal(P.B('lama'), n * (LG + 0.009) + h * random.uniform(-0.25, 0.25) + Z * random.uniform(0.09, 0.17), n, random.uniform(0.03, 0.05))
        decal(P.B('oleo_d'), n * (LG + 0.0006) + h * random.uniform(-0.15, 0.15) + Z * random.uniform(0.6, 1.0), n, 0.05, 13, 0.6, 0.6)
        musgo(P, n * 0.31 + h * random.uniform(-0.2, 0.2) + Z * ZL_B, 0.05, 4)
    P.fim()


def liga_lado(nome, cx, cy, quartos, seed):
    random.seed(seed)
    P = Peca(nome, cx, cy, quartos * PI / 2)
    y0 = LG - 0.002
    caixa_de(P.B('concreto'), (-0.11, 0.3, 0.0), (0.11, 0.5, ZL_B))
    caixa_de(P.B('grafite'), (-PXL + CH, y0, ZL_B), (PXL - CH, 0.5, ZLP_I))
    h = Vector((0, 1, 0))
    lst = []
    for sx in (-1, 1):
        n = Vector((sx, 0, 0))
        for (z0, z1) in ((ZL_B, 0.39), (0.39, 0.71), (0.71, ZLP_I)):
            lst.append(chapa(P, n, h, PXL, y0, 0.5, z0, z1))
        caixa_de(P.B('liga2'), (sx * PXL - 0.004 * (sx < 0), 0.482, ZL_B), (sx * PXL + 0.004 * (sx > 0), 0.5, ZLP_I))   # meia mata-junta
        for zz in (0.13, 0.3, 0.47, 0.64, 0.81, 0.97):
            cil(P.B('liga2', True), (sx * (PXL + 0.0042), 0.491, zz), 0.0058, 0.0024, n, lados=10, r2=0.0042)
        caixa_de(P.B('liga2'), (sx * PXL - 0.004 * (sx < 0), y0, ZL_B), (sx * PXL + 0.004 * (sx > 0), 0.5, ZL_B + 0.04))
        for yy in (0.36, 0.45):
            caixa(P.B('fenda'), (sx * (PXL + 0.0045), yy, ZL_B + 0.012), (0.001, 0.035, 0.008))
    # topo inclinado para os dois lados, tampa e lâminas
    prisma(P.B('liga'), [(-PXL, ZLP_I), (PXL, ZLP_I), (PXL_T, ZLP_T), (-PXL_T, ZLP_T)], y0, 0.5)
    caixa_de(P.B('liga2'), (-PXL_T - 0.004, y0, ZLP_T), (PXL_T + 0.004, 0.5, ZLP_T + 0.014))
    for sx in (-1, 1):
        n = Vector((sx, 0, 0))
        caixa_de(P.B('liga2'), (sx * PXL - 0.004 * (sx < 0), y0, ZLP_I - 0.03), (sx * PXL + 0.004 * (sx > 0), 0.5, ZLP_I))
        nn = Vector((sx * (ZLP_T - ZLP_I), 0, -(PXL_T - PXL))).normalized()
        for t in (0.3, 0.75):
            for yy in (0.33, 0.41, 0.48):
                cil(P.B('liga2', True), (sx * (PXL + (PXL_T - PXL) * t + 0.001), yy, ZLP_I + (ZLP_T - ZLP_I) * t), 0.0058, 0.0024, nn, lados=10, r2=0.0042)
        e = PXL_T + 0.002
        lamina(P, (sx * e, y0 + 0.004, ZLP_T + 0.004), (sx * e, 0.5, ZLP_T + 0.004), n)
        p = (sx * (PXL + 0.0007), random.uniform(0.33, 0.47), ZLP_I - 0.035)
        escorrido(P.B('oleo'), p, n, random.uniform(0.08, 0.2), 0.004)
        for k in range(random.choice((1, 2))):
            p = Vector((sx * (PXL + 0.0002), random.uniform(0.33, 0.45), random.uniform(0.5, 0.95)))
            marcas_garra(P, p, n, random.uniform(0.2, 0.36), random.choice((3, 4)), random.uniform(0.012, 0.016))
        acido(P, (sx * (PXL + 0.0005), random.uniform(0.34, 0.46), random.uniform(0.18, 0.6)), n, 0.032, 3)
        for k in range(3):
            decal(P.B('lama'), (sx * (PXL + 0.0095), random.uniform(0.32, 0.49), random.uniform(0.09, 0.16)), n, random.uniform(0.025, 0.045))
        musgo(P, (sx * 0.085, random.uniform(0.35, 0.45), ZL_B), 0.04, 4)
    for k in range(2):
        decal(P.B('chamusco'), (random.uniform(-0.06, 0.06), random.uniform(0.33, 0.47), ZLP_T + 0.0145), Z, 0.035)
    P.fim()


# ================================================================== MURO DE CAMPO (muro_escudo)
ZC_PL = 0.30          # topo do plinto
ZC_TOP = 1.42         # base da chapa de topo
BOBINAS = ((0.40, 0.66), (0.76, 1.02), (1.12, 1.36))
YC_BAR = 0.26         # eixo das barras emissoras
ZF0, ZF1 = 0.11, 1.32  # altura da parede de campo


def enrolamento(bm, c, r, z0, z1, voltas, rf=0.0042, n_por=14, fase=0.0):
    N = int(voltas * n_por)
    pts = []
    for i in range(N + 1):
        t = i / N
        a = 2 * PI * voltas * t + fase
        pts.append(Vector(c) + Vector((math.cos(a) * r, math.sin(a) * r, z0 + (z1 - z0) * t)))
    varrer(bm, pts, rf, 6)


def campo_centro(nome, cx, cy, lados, seed):
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    caixa_de(P.B('concreto'), (-0.32, -0.32, 0.0), (0.32, 0.32, 0.06))
    caixa_de(P.B('concreto'), (-0.24, -0.24, 0.06), (0.24, 0.24, 0.27))
    tronco(P.B('concreto'), 0.27, ZC_PL, 0.24, 0.215)
    caixa_de(P.B('listras'), (-0.2415, -0.2415, 0.19), (0.2415, 0.2415, 0.245))
    for k in range(4):                                                    # lascas no plinto
        R = Matrix.Rotation(k * PI / 2, 3, 'Z')
        n = R @ Vector((0, 1, 0))
        h = R @ Vector((-1, 0, 0))
        decal(P.B('quebra'), n * 0.2425 + h * random.uniform(-0.18, 0.18) + Z * random.uniform(0.1, 0.18), n, random.uniform(0.015, 0.03))
    # coluna, flange da base
    cil(P.B('grafite', True), (0, 0, (ZC_PL + ZC_TOP) / 2), 0.06, ZC_TOP - ZC_PL, lados=24)
    cil(P.B('ferro', True), (0, 0, ZC_PL + 0.01), 0.11, 0.02, lados=32)
    for k in range(6):
        a = k * PI / 3 + 0.3
        porca(P.B('aco'), (math.cos(a) * 0.09, math.sin(a) * 0.09, ZC_PL + 0.02), Z, 0.009, 0.007)
    # bobinas: carretel de fenolite, duas camadas de fio esmaltado, tirantes, terminal
    for ib, (z0, z1) in enumerate(BOBINAS):
        cil(P.B('resina', True), (0, 0, (z0 + z1) / 2), 0.075, z1 - z0, lados=28)
        for zf in (z0 + 0.007, z1 - 0.007):
            cil(P.B('resina', True), (0, 0, zf), 0.15, 0.014, lados=40)
        voltas = int((z1 - z0 - 0.032) / 0.0089)
        enrolamento(P.B('esmalte', True), (0, 0, 0), 0.083, z0 + 0.019, z1 - 0.019, voltas)
        enrolamento(P.B('esmalte', True), (0, 0, 0), 0.0915, z0 + 0.0235, z1 - 0.0235, voltas - 1, fase=0.5)
        for k in range(4):
            a = PI / 4 + k * PI / 2
            p = Vector((math.cos(a) * 0.125, math.sin(a) * 0.125, 0))
            tubo(P.B('aco'), p + Z * (z0 - 0.004), p + Z * (z1 + 0.012), 0.0048, 8)
            porca(P.B('aco'), p + Z * z1, Z, 0.009, 0.008)
            porca(P.B('aco'), p + Z * z0, -Z, 0.009, 0.008)
            ninho(P, p + Z * (z1 + 0.005), Vector((math.cos(a), math.sin(a), 0)), 0.006, 3, 0)
        if ib == 1:                                                       # remendo de fita no enrolamento
            cil(P.B('fita'), (0, 0, z0 + 0.12), 0.0975, 0.03, lados=32)
        decal(P.B('queimado'), (math.cos(ib * 2.1) * 0.12, math.sin(ib * 2.1) * 0.12, z1 + 0.0005), Z, 0.03)
        decal(P.B('chamusco'), (math.cos(ib * 2.1 + 2) * 0.12, math.sin(ib * 2.1 + 2) * 0.12, z1 + 0.0005), Z, 0.035)
    for zs in (0.693, 1.053):
        saia(P.B('porcelana', True), (0, 0, zs), 0.062, 0.1, 0.03)
    # chapa de topo, coroa: postes de porcelana, toroide de cobre, eletrodo violeta
    caixa_de(P.B('grafite'), (-0.2, -0.2, ZC_TOP), (0.2, 0.2, ZC_TOP + 0.03))
    zt = ZC_TOP + 0.03
    for sx in (-1, 1):
        for sy in (-1, 1):
            porca(P.B('aco'), (sx * 0.175, sy * 0.175, zt), Z, 0.01, 0.008)
    for k in range(3):
        a = k * 2 * PI / 3 + 0.4
        p = Vector((math.cos(a) * 0.11, math.sin(a) * 0.11, 0))
        cil(P.B('porcelana', True), p + Z * (zt + 0.03), 0.011, 0.06, lados=14)
        for j in range(2):
            cil(P.B('porcelana', True), p + Z * (zt + 0.012 + j * 0.02), 0.02, 0.005, lados=16, r2=0.012)
    toro(P.B('cobre', True), (0, 0, zt + 0.075), 0.11, 0.022, 48, 14)
    tubo(P.B('aco'), (0, 0, zt), (0, 0, zt + 0.06), 0.008, 10)
    bm = P.B('violeta')
    res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.032)
    for v in res['verts']:
        v.co += Vector((0, 0, zt + 0.09))
    for k in range(4):
        decal(P.B('chamusco'), (random.uniform(-0.17, 0.17), random.uniform(-0.17, 0.17), zt + 0.0005), Z, random.uniform(0.03, 0.06))
    # barras emissoras voltadas para cada vizinho
    for qd in lados:
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        n = R @ Vector((0, 1, 0))
        h = R @ Vector((-1, 0, 0))
        rot = rot_cols(h, n, Z)
        caixa(P.B('grafite'), n * YC_BAR + Z * 0.765, (0.05, 0.02, 1.29), rot)
        caixa(P.B('aco'), n * 0.245 + Z * 0.21, (0.07, 0.012, 0.12), rot)              # suporte de baixo no plinto
        for a in (-1, 1):
            porca(P.B('aco'), n * 0.251 + h * a * 0.026 + Z * 0.175, n, 0.007, 0.005)
        caixa(P.B('aco'), n * 0.23 + Z * (ZC_TOP + 0.015), (0.06, 0.07, 0.02), rot)      # braço de cima
        zz = 0.16
        while zz < 1.37:
            p = n * (YC_BAR + 0.01)
            cil(P.B('cobre'), p + n * 0.007 + Z * zz, 0.009, 0.014, n, lados=10, r2=0.004)
            cil(P.B('led_v'), p + n * 0.0155 + Z * zz, 0.004, 0.004, n, lados=10)
            if random.random() < 0.35:
                decal(P.B('queimado'), p + n * 0.0003 + Z * (zz + 0.018), n, 0.016)
            zz += 0.07
        for (z0, z1) in BOBINAS:                                          # isoladores de passagem bobina → barra
            zs = z1 - 0.007
            tubo(P.B('porcelana', True), n * 0.15 + Z * zs, n * 0.25 + Z * zs, 0.011, 14)
            for t in (0.18, 0.21):
                cil(P.B('porcelana', True), n * t + Z * zs, 0.02, 0.004, n, lados=16)
        serie_plana(P.B('tinta'), n * (YC_BAR + 0.0102) + Z * 1.38, n, 0.008, 4)
    # eletrocalha com cabos, caixa de ligação, eletroduto e capacitor numa face livre
    livres = [q for q in range(4) if q not in lados]
    qf = livres[0]
    R = Matrix.Rotation(qf * PI / 2, 3, 'Z')
    nf = R @ Vector((0, 1, 0))
    hf = R @ Vector((-1, 0, 0))
    rot = rot_cols(hf, nf, Z)
    caixa(P.B('grafite'), nf * 0.175 + Z * 0.345, (0.16, 0.11, 0.09), rot)
    caixa(P.B('maquina'), nf * 0.2315 + Z * 0.345, (0.13, 0.003, 0.07), rot)
    for a in (-1, 1):
        for b in (-1, 1):
            porca(P.B('aco'), nf * 0.233 + hf * a * 0.055 + Z * (0.345 + b * 0.027), nf, 0.006, 0.004)
    cil(P.B('led_a'), nf * 0.234 + hf * 0.04 + Z * 0.37, 0.004, 0.003, nf, lados=10)
    serie_plana(P.B('tinta'), nf * 0.2335 + hf * -0.015 + Z * 0.325, nf, 0.01, 5)
    zb0 = 0.39
    caixa(P.B('galv'), nf * 0.208 + Z * ((zb0 + ZC_TOP) / 2), (0.07, 0.004, ZC_TOP - zb0), rot)
    for a in (-1, 1):
        caixa(P.B('galv'), nf * 0.185 + hf * a * 0.034 + Z * ((zb0 + ZC_TOP) / 2), (0.003, 0.045, ZC_TOP - zb0), rot)
    for (z0, z1) in BOBINAS:
        caixa(P.B('aco'), nf * 0.157 + Z * (z1 - 0.007), (0.05, 0.016, 0.012), rot)
        caixa(P.B('aco'), nf * 0.157 + Z * (z0 + 0.007), (0.05, 0.016, 0.012), rot)
    cores = ('borracha', 'cabo_verm', 'borracha')
    for i, (z0, z1) in enumerate(BOBINAS):
        s = (i - 1) * 0.018
        p0 = nf * 0.185 + hf * s + Z * zb0
        t = nf * 0.153 + hf * (s * 0.6) + Z * (z1 + 0.012)
        caixa(P.B('latao'), t - Z * 0.004, (0.014, 0.02, 0.008), rot)
        pts = [p0 + Z * (k * (z1 - 0.05 - zb0) / 8) for k in range(9)]
        pts += bezier(pts[-1], pts[-1] + Z * 0.05, t + nf * 0.02 + Z * 0.02, t + Z * 0.004, 8)[1:]
        varrer(P.B(cores[i], True), pts, 0.0065, 10)
    for zc in (0.5, 0.88, 1.24):                                          # abraçadeiras dos cabos na calha
        caixa(P.B('aco'), nf * 0.172 + Z * zc, (0.07, 0.003, 0.012), rot)
    ecs = [nf * 0.23 + hf * -0.05 + Z * 0.33, nf * 0.27 + hf * -0.05 + Z * 0.33]
    ecs += bezier(ecs[-1], ecs[-1] + nf * 0.03, nf * 0.30 + hf * -0.05 + Z * 0.28, nf * 0.30 + hf * -0.05 + Z * 0.22, 8)[1:]
    ecs.append(nf * 0.30 + hf * -0.05 + Z * 0.06)
    varrer(P.B('galv', True), ecs, 0.014, 14)
    chapa_arco(P.B('aco'), nf * 0.30 + hf * -0.05 + Z * 0.15, Z, 0.0145, 0.002, 0.016, -PI / 2 - 0.3, PI / 2 + 0.3)
    ninho(P, nf * 0.315 + hf * -0.05 + Z * 0.12, nf, 0.008, 4, 0.05)
    cp = nf * 0.17 + hf * 0.16
    cil(P.B('capacitor', True), cp + Z * (ZC_PL + 0.045), 0.035, 0.09, lados=20)
    cil(P.B('aluminio', True), cp + Z * (ZC_PL + 0.092), 0.034, 0.008, lados=20, r2=0.026)
    for k in range(5):
        pedra(P.B('crosta_branca'), cp + ruido_vec(0.02) * Vector((1, 1, 0)) + Z * (ZC_PL + 0.097), 0.005, 0.5)
    escorrido(P.B('crosta_branca'), cp + nf * 0.036 + Z * (ZC_PL + 0.085), nf, 0.06, 0.008)
    pc = bezier(cp + Z * (ZC_PL + 0.096), cp + Z * (ZC_PL + 0.14), nf * 0.2 + hf * 0.09 + Z * 0.43, nf * 0.2 + hf * 0.07 + Z * 0.39, 10)
    varrer(P.B('borracha', True), pc, 0.004, 8)
    # musgo, lama, óleo no pé
    for qd in range(4):
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        n = R @ Vector((0, 1, 0))
        h = R @ Vector((-1, 0, 0))
        musgo(P, n * 0.3 + h * random.uniform(-0.2, 0.2) + Z * 0.06, 0.05, 5)
        for k in range(2):
            decal(P.B('lama'), n * 0.2408 + h * random.uniform(-0.2, 0.2) + Z * random.uniform(0.08, 0.15), n, random.uniform(0.03, 0.05))
        if qd == qf:
            decal(P.B('oleo'), n * 0.27 + h * random.uniform(-0.1, 0.1) + Z * 0.0605, Z, 0.04)
    P.fim()
    # arcos entre o eletrodo e a coroa, luz do eletrodo
    arcos = []
    for k in range(3):
        a = random.uniform(0, 2 * PI)
        arcos.append(arco_obj(nome + '_arco%d' % k, P.W((0, 0, zt + 0.09)), P.W((math.cos(a) * 0.105, math.sin(a) * 0.105, zt + 0.08)), 0.25, 0.0022, galhos=1))
    pisca(arcos, 0.55, seed)
    emissor_luz = luz(nome + '_luz_eletrodo', (0.6, 0.2, 1.0), 4.0, P.W((0, 0, zt + 0.12)), 0.04)
    fse = random.random()

    def anima(q, fr, lz=emissor_luz, fse=fse):
        lz.data.energy = 3.0 + 2.0 * (0.5 + 0.5 * math.sin(2 * PI * (5 * fr + fse)))
        lz.data.keyframe_insert('energy', frame=q)
    ANIM.append(anima)


def campo_folha(nome, P, y0, y1, z0, z1):
    """Parede de campo do pano: malha fina em coordenadas do mundo com ondas viajantes por chaves de forma
    (seno/cosseno de duas ondas; o laço fecha em 4 s). Ancorada no emissor e no trilho, solta no topo;
    a fase e a amplitude dependem só do mundo, então casa com o pano do vizinho na borda."""
    nu, nv = 16, 56
    L2 = 2 * (y1 - y0)
    along = P.D((0, 1, 0))
    eixo_u = 0 if abs(along.x) > 0.5 else 1
    nw = P.D((1, 0, 0))
    ax = Vector((abs(round(nw.x)), abs(round(nw.y)), 0))
    vs, fs, uv = [], [], []
    for j in range(nv + 1):
        z = z0 + (z1 - z0) * j / nv
        for i in range(nu + 1):
            y = y0 + (y1 - y0) * i / nu
            vs.append(P.W((0, y, z)))
            uv.append((y, z))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            fs.append((a, a + 1, a + nu + 2, a + nu + 1))
    me = bpy.data.meshes.new(nome)
    me.from_pydata([tuple(v) for v in vs], [], fs)
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    o.data.materials.append(M['campo'])
    for pg in me.polygons:
        pg.use_smooth = True
    o.visible_shadow = False
    o.shape_key_add(name='Basis')
    ondas = ((2 * PI / 0.46, 2 * PI / 0.95, 2), (2 * PI / 0.29, -2 * PI / 0.6, 3))
    keys = []
    for (ku, kz, ciclos) in ondas:
        ks = o.shape_key_add(name='s', from_mix=False)
        kc = o.shape_key_add(name='c', from_mix=False)
        for kk in (ks, kc):
            kk.slider_min, kk.slider_max = -1.0, 1.0
        for idx, v in enumerate(vs):
            y, z = uv[idx]
            env = math.sin(PI * (y - y0) / L2) * min(1.0, (z - z0) / 0.3)
            fi = ku * v[eixo_u] + kz * z
            amp = 0.016 * env
            ks.data[idx].co = v + ax * amp * math.sin(fi)
            kc.data[idx].co = v + ax * amp * math.cos(fi)
        keys.append((ks, kc, ciclos))

    def f(q, fr, keys=keys):
        for ks, kc, ciclos in keys:
            w = 2 * PI * ciclos * fr
            ks.value = math.cos(w)
            kc.value = -math.sin(w)
            ks.keyframe_insert('value', frame=q)
            kc.keyframe_insert('value', frame=q)
    ANIM.append(f)
    return o


def campo_lado(nome, cx, cy, quartos, seed):
    """Pano do muro de campo: trilho de concreto com canal de aço e pinos emissores + a parede de campo."""
    random.seed(seed)
    P = Peca(nome, cx, cy, quartos * PI / 2)
    caixa_de(P.B('concreto'), (-0.09, 0.24, 0.0), (0.09, 0.5, 0.07))
    caixa_de(P.B('grafite'), (-0.035, 0.24, 0.07), (0.035, 0.5, 0.095))
    for sx in (-1, 1):
        caixa_de(P.B('aco'), (sx * 0.035 - 0.003 * (sx < 0), 0.24, 0.07), (sx * 0.035 + 0.003 * (sx > 0), 0.5, 0.1))
        for yy in (0.3, 0.42):
            porca(P.B('aco'), (sx * 0.06, yy, 0.07), Z, 0.008, 0.006)
        for k in range(2):
            decal(P.B('lama'), (sx * 0.0905, random.uniform(0.27, 0.48), random.uniform(0.02, 0.05)), (sx, 0, 0), random.uniform(0.02, 0.035))
        decal(P.B('queimado'), (sx * 0.0905, random.uniform(0.3, 0.46), 0.06), (sx, 0, 0), 0.025)
        musgo(P, (sx * 0.095, random.uniform(0.3, 0.46), 0.0), 0.04, 4)
    yy = 0.5 - 0.0325
    while yy > 0.27:
        cil(P.B('cobre'), (0, yy, 0.101), 0.011, 0.012, lados=10, r2=0.004)
        cil(P.B('led_v'), (0, yy, 0.108), 0.0045, 0.004, lados=10)
        if random.random() < 0.4:
            decal(P.B('queimado'), (random.choice((-1, 1)) * 0.02, yy, 0.0953), Z, 0.014)
        yy -= 0.065
    for k in range(3):
        decal(P.B('chamusco'), (random.choice((-1, 1)) * random.uniform(0.12, 0.2), random.uniform(0.28, 0.48), 0.0004), Z, random.uniform(0.04, 0.07))
    rachadura_plana(P.B('fenda'), (0.0905, 0.36, 0.068), (1, 0, 0), 0.06, -PI / 2, 3)
    pedra(P.B('quebra'), (0.06, 0.47, 0.07), 0.01, 0.5)
    P.fim()
    campo_folha(nome + '_campo', P, YC_BAR + 0.012, 0.5, ZF0, ZF1)
    luz(nome + '_luz_campo', (0.6, 0.22, 1.0), 2.5, P.W((0.0, 0.40, 0.55)), 0.2)


# ================================================================== MINA DE PULSO (mina_pulso)
R_CAR = 0.205
Z_FL0, Z_FL1 = 0.034, 0.046        # flange
Z_TA0, Z_TA1 = 0.072, 0.094        # tampa (anel plano)
P_DISP = 6                         # quadro do disparo


def alt_terra(r, a):
    if r < 0.245:
        hh = 0.036 + 0.012 * (r - 0.205) / 0.04
    else:
        t = min(1.0, (r - 0.245) / 0.25)
        hh = 0.048 * (1 - t * t * (3 - 2 * t)) - 0.003 * t
    return hh + 0.006 * noise.noise(Vector((math.cos(a) * r * 9, math.sin(a) * r * 9, 3.1))) * min(1.0, max(0.0, (r - 0.2) / 0.05))


def z_tampa(r):
    """Altura da superfície de cima da tampa (anel plano + domo)."""
    return Z_TA1 + 0.018 * min(1.0, max(0.0, (0.17 - r) / 0.105))


def mato(bm, c, r, k, alt=(0.04, 0.11), inc=(0.1, 0.6), dir_fixa=None, w=(0.0025, 0.005)):
    """Tufo de capim: folhas finas afinando e curvando (inc) a partir de c."""
    for i in range(k):
        p = Vector(c) + Vector((random.uniform(-r, r), random.uniform(-r, r), 0))
        hh = random.uniform(*alt)
        a = dir_fixa + random.uniform(-0.35, 0.35) if dir_fixa is not None else random.uniform(0, 2 * PI)
        ic = random.uniform(*inc)
        ww = random.uniform(*w)
        d = Vector((math.cos(a), math.sin(a), 0))
        s = Vector((-math.sin(a), math.cos(a), 0))
        ant = None
        for j in range(5):
            t = j / 4
            q = p + Z * hh * t * (1 - 0.6 * ic * t) + d * hh * ic * t * t
            larg = ww * (1 - t) + 0.0003
            v1, v2 = bm.verts.new(q - s * larg), bm.verts.new(q + s * larg)
            if ant:
                bm.faces.new((ant[0], ant[1], v2, v1))
            ant = (v1, v2)


def projeteis(nome, mat, pool_n, eventos, vel, espalha, vida=14, raio=0.008, achatar=0.7):
    """Como faiscas(), com material e tamanho próprios (torrões de terra que pulam no disparo)."""
    pool = []
    for i in range(pool_n):
        bm = bmesh.new()
        pedra(bm, (0, 0, 0), raio * random.uniform(0.6, 1.3), achatar)
        o = obj('%s_%d' % (nome, i), bm, mat)
        o.rotation_mode = 'XYZ'
        pool.append(o)
    rr = random.Random(pool_n * 31)
    plano = {o: [] for o in pool}
    k = 0
    for q0, pt, d in eventos:
        for _ in range(pool_n // max(1, len(eventos))):
            o = pool[k % pool_n]
            k += 1
            v = Vector(d).normalized() * vel + Vector((rr.gauss(0, 1), rr.gauss(0, 1), abs(rr.gauss(0, 1)))) * espalha
            p0 = Vector(pt) + Vector((rr.uniform(-0.2, 0.2), rr.uniform(-0.2, 0.2), 0))
            plano[o].append((q0 + rr.randint(0, 2), p0, v, rr.randint(vida // 2, vida), Vector((rr.uniform(-9, 9), rr.uniform(-9, 9), rr.uniform(-9, 9)))))

    def f(q, fr, plano=plano):
        for o, lst in plano.items():
            vivo = None
            for item in lst:
                if item[0] <= q < item[0] + item[3]:
                    vivo = item
            if vivo:
                q0, pt, v, vd, giro = vivo
                t = (q - q0) / FPS
                p = pt + v * t + Z * (-4.9 * t * t)
                p.z = max(p.z, 0.004)
                o.location = p
                o.rotation_euler = tuple(giro * t)
                o.hide_render = False
            else:
                o.hide_render = True
            for c in ('location', 'rotation_euler', 'hide_render'):
                chave(o, c, q)
    ANIM.append(f)


def mina(nome):
    random.seed(77)
    P = Peca(nome, 0, 0, 0)
    # carcaça semienterrada e flange aparafusado
    cil(P.B('oliva', True), (0, 0, -0.04), R_CAR, 0.15, lados=56)
    cil(P.B('ferro', True), (0, 0, (Z_FL0 + Z_FL1) / 2), 0.232, Z_FL1 - Z_FL0, lados=56)
    for k in range(12):
        a = k * PI / 6 + 0.13
        if k == 5:
            cil(P.B('fenda'), (math.cos(a) * 0.222, math.sin(a) * 0.222, Z_FL1 + 0.0004), 0.004, 0.001, lados=8)
            continue
        porca(P.B('latao' if k == 9 else 'aco'), (math.cos(a) * 0.222, math.sin(a) * 0.222, Z_FL1), Z, 0.0075, 0.006)
    ninho(P, (0.0, -0.233, Z_FL0 + 0.006), Vector((0, -1, 0)), 0.01, 4, 0)
    # bobina toroidal entre os espaçadores (núcleo que acende, fio de cobre enrolado)
    zc = (Z_FL1 + Z_TA0) / 2
    toro(P.B('bobina_luz', True), (0, 0, zc), 0.188, 0.0102, 72, 10)
    voltas = 110
    pts = []
    N = voltas * 8
    for i in range(N + 1):
        t = i / N
        th = 2 * PI * t
        fi = 2 * PI * voltas * t
        d = Vector((math.cos(th), math.sin(th), 0))
        pts.append(d * (0.188 + 0.0118 * math.cos(fi)) + Z * (zc + 0.0118 * math.sin(fi)))
    varrer(P.B('cobre', True), pts, 0.0016, 5)
    for k in range(10):
        a = k * PI / 5 + 0.31
        cil(P.B('aco', True), (math.cos(a) * 0.212, math.sin(a) * 0.212, zc), 0.0055, Z_TA0 - Z_FL1 + 0.002, lados=10)
    # prensa-cabo e capacitor meio enterrado ligado por dois cabos
    ag = -0.62
    gl = Vector((math.cos(ag + 0.22) * 0.224, math.sin(ag + 0.22) * 0.224, Z_FL1))
    cil(P.B('latao', True), gl + Z * 0.006, 0.0085, 0.012, lados=12)
    cil(P.B('latao'), gl + Z * 0.013, 0.0095, 0.004, lados=6)
    dc = Vector((math.cos(ag), math.sin(ag), 0))
    tc = Vector((-math.sin(ag), math.cos(ag), 0))
    cc = dc * 0.33 + Z * 0.035
    cil(P.B('capacitor', True), cc, 0.045, 0.15, tc, lados=24)
    cil(P.B('aluminio', True), cc + tc * 0.078, 0.046, 0.006, tc, lados=24)
    cil(P.B('aluminio', True), cc - tc * 0.078, 0.046, 0.006, tc, lados=24)
    cil(P.B('aluminio', True), cc - tc * 0.087, 0.042, 0.014, -tc, lados=24, r2=0.022)                # fundo estufado
    for k in range(6):
        pedra(P.B('crosta_branca'), cc - tc * 0.09 + ruido_vec(0.025) * Vector((1, 1, 0.3)) + Z * 0.01, 0.005, 0.5)
    for t in (-0.04, 0.04):
        chapa_arco(P.B('aco'), cc + tc * t, tc, 0.0455, 0.002, 0.014, -0.4, PI + 0.4, 16)
        for sg in (-1, 1):
            p = cc + tc * t + dc * sg * 0.05 - Z * 0.012
            cil(P.B('aco'), p, 0.005, 0.03, lados=6)                     # estaca da cinta
    ninho(P, cc + tc * 0.04 + Z * 0.046, Z, 0.008, 4, 0)
    serie_plana(P.B('tinta'), cc + Z * 0.0458, Z, 0.01, 4, horiz=tc)
    for i, (sg, mat) in enumerate(((-1, 'borracha'), (1, 'cabo_verm'))):
        tb = cc + tc * 0.081 + dc * sg * 0.016 + Z * 0.012
        tubo(P.B('latao'), tb - tc * 0.002, tb + tc * 0.012, 0.0045, 6)
        alvo = gl + Z * 0.016 + dc * sg * 0.003
        pc = bezier(tb + tc * 0.012, tb + tc * 0.05 + Z * 0.03, alvo + Z * 0.06 + dc * 0.04, alvo, 14)
        varrer(P.B(mat, True), pc, 0.0042, 8)
    # monte de terra em volta (anel com ruído), pedrinhas, capim, chão queimado e capim deitado
    rs = [0.207 + (0.62 - 0.207) * (k / 16) ** 1.35 for k in range(17)]
    na = 72
    bm = P.B('terra', True)
    aneis = []
    for r in rs:
        anel = []
        for j in range(na):
            an_ = 2 * PI * j / na
            esc = 1.0 if r < 0.3 else 1.0 + (r - 0.3) / 0.32 * (-0.12 + 0.22 * noise.noise(Vector((math.cos(an_) * 2.2, math.sin(an_) * 2.2, 0.7))))
            anel.append(bm.verts.new((math.cos(an_) * r * esc, math.sin(an_) * r * esc, alt_terra(r, an_) - (0.006 if r > 0.6 else 0.0))))
        aneis.append(anel)
    for A, B in zip(aneis, aneis[1:]):
        for j in range(na):
            bm.faces.new((A[j], A[(j + 1) % na], B[(j + 1) % na], B[j]))
    for k in range(70):
        r = random.uniform(0.22, 0.6)
        a = random.uniform(0, 2 * PI)
        if (Vector((math.cos(a), math.sin(a), 0)) * r - cc).length < 0.1:
            continue
        pedra(P.B(random.choice(('terra', 'brita', 'brita'))), (math.cos(a) * r, math.sin(a) * r, alt_terra(r, a)), random.uniform(0.005, 0.016), 0.6)
    for k in range(46):
        r = random.uniform(0.25, 0.62)
        a = random.uniform(0, 2 * PI)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        if (p - cc).length < 0.11:
            continue
        p.z = alt_terra(r, a) - 0.003
        if random.random() < 0.55:
            mato(P.B('mato'), p, 0.02, random.randint(5, 9), (0.04, 0.12))
        else:
            mato(P.B('mato_seco'), p, 0.02, random.randint(4, 7), (0.03, 0.08), (0.5, 1.1))
    for k in range(9):                                                   # capim deitado para fora (disparos antigos)
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.3, 0.5)
        p = Vector((math.cos(a) * r, math.sin(a) * r, alt_terra(r, a) - 0.002))
        mato(P.B('mato_seco'), p, 0.015, 6, (0.05, 0.09), (1.6, 2.2), a, (0.002, 0.004))
    for k in range(7):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.62, 0.95)
        decal(P.B('chamusco'), (math.cos(a) * r, math.sin(a) * r, 0.0006), Z, random.uniform(0.07, 0.13), 15, 0.6, 1.6, a)
    P.fim()
    # tampa (objeto que pula no disparo): anel, domo, nervuras, parafusos, faixa, sensor, LED, antena, terra
    T = Peca(nome + '_tampa', 0, 0, 0)
    cil(T.B('oliva', True), (0, 0, (Z_TA0 + Z_TA1) / 2), 0.215, Z_TA1 - Z_TA0, lados=56)
    cil(T.B('oliva', True), (0, 0, Z_TA1 + 0.009), 0.17, 0.018, lados=56, r2=0.065)
    cil(T.B('listras'), (0, 0, Z_TA0 + 0.01), 0.2165, 0.012, lados=56)
    for k in range(8):
        a = k * PI / 4 + 0.2
        for (r0, r1) in ((0.068, 0.17), (0.17, 0.205)):
            p0 = Vector((math.cos(a) * r0, math.sin(a) * r0, z_tampa(r0)))
            p1 = Vector((math.cos(a) * r1, math.sin(a) * r1, z_tampa(r1)))
            u = (p1 - p0).normalized()
            t = Vector((-math.sin(a), math.cos(a), 0))
            caixa(T.B('oliva'), (p0 + p1) / 2 + u.cross(t) * 0.004, ((p1 - p0).length, 0.012, 0.012), rot_cols(u, t, u.cross(t)))
    for k in range(12):
        a = k * PI / 6 + 0.46
        porca(T.B('aco'), (math.cos(a) * 0.196, math.sin(a) * 0.196, Z_TA1), Z, 0.0072, 0.0055)
    for a in (PI / 2 + 0.2, -PI / 2 + 0.2):                              # olhais de içamento (drone)
        toro(T.B('aco', True), (math.cos(a) * 0.18, math.sin(a) * 0.18, Z_TA1 + 0.012), 0.011, 0.003, 18, 6, Vector((-math.sin(a), math.cos(a), 0)))
    serie_plana(T.B('tinta'), (0.0, -0.185, Z_TA1 + 0.0002), Z, 0.011, 5, horiz=(1, 0, 0))
    for k in range(5):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.1, 0.2)
        decal(T.B('quebra_d'), (math.cos(a) * r, math.sin(a) * r, z_tampa(r) + 0.0008), Z, random.uniform(0.008, 0.016))
    # sensor de pressão: fole de borracha + prato serrilhado + três hastes
    zs = z_tampa(0.0)
    cil(T.B('aco', True), (0, 0, zs + 0.002), 0.04, 0.004, lados=32)
    for k in range(5):
        toro(T.B('borracha', True), (0, 0, zs + 0.007 + k * 0.0055), 0.031 - k * 0.0012, 0.0036, 32, 8)
    zp = zs + 0.034
    cil(T.B('aco', True), (0, 0, zp), 0.041, 0.008, lados=40)
    for k in range(16):
        a = k * PI / 8
        caixa(T.B('fenda'), (math.cos(a) * 0.024, math.sin(a) * 0.024, zp + 0.0042), (0.03, 0.0016, 0.001), Matrix.Rotation(a, 3, 'Z'))
    for k in range(3):
        a = k * 2 * PI / 3 + 0.5
        p = Vector((math.cos(a) * 0.034, math.sin(a) * 0.034, zp + 0.004))
        tubo(T.B('aco'), p, p + Z * 0.026 + Vector((math.cos(a), math.sin(a), 0)) * 0.004, 0.0018, 6)
        bm = T.B('aco', True)
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0035)
        for v in res['verts']:
            v.co += p + Z * 0.027 + Vector((math.cos(a), math.sin(a), 0)) * 0.004
    decal(T.B('terra_d'), (0.012, -0.01, zp + 0.0045), Z, 0.025)
    # LED piscando com gaiola
    al = 0.62
    pl = Vector((math.cos(al) * 0.14, math.sin(al) * 0.14, z_tampa(0.14)))
    cil(T.B('grafite', True), pl + Z * 0.003, 0.016, 0.01, lados=20)
    cil(T.B('led_mina', True), pl + Z * 0.011, 0.0095, 0.008, lados=20, r2=0.006)
    for k in range(3):
        a = k * 2 * PI / 3
        p = pl + Vector((math.cos(a), math.sin(a), 0)) * 0.015
        tubo(T.B('aco'), p + Z * 0.006, p + Z * 0.024, 0.0014, 6)
    toro(T.B('aco', True), pl + Z * 0.024, 0.015, 0.0014, 20, 5)
    # antena de enlace da IA
    aa = 3.75
    pa = Vector((math.cos(aa) * 0.15, math.sin(aa) * 0.15, z_tampa(0.15)))
    cil(T.B('grafite', True), pa + Z * 0.006, 0.01, 0.014, lados=14)
    enrolamento(T.B('aco', True), pa, 0.0045, 0.012, 0.03, 6, 0.0012, 10)
    pw = bezier(pa + Z * 0.012, pa + Z * 0.1, pa + Z * 0.2 + Vector((0.01, 0.02, 0)), pa + Z * 0.25 + Vector((0.03, 0.03, 0)), 12)
    varrer(T.B('aco', True), pw, 0.0016, 6)
    bm = T.B('led_v', True)
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.0055)
    for v in res['verts']:
        v.co += pw[-1]
    # terra e mato por cima da tampa
    for k in range(9):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.07, 0.2)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        if (p - pl).length < 0.04 or (p - pa).length < 0.04:
            continue
        p.z = z_tampa(r) + 0.002
        pedra(T.B('terra'), p, random.uniform(0.01, 0.022), 0.5)
        if k % 3 == 0:
            mato(T.B('mato'), p + Z * 0.004, 0.006, 4, (0.025, 0.06))
        if r > 0.172:
            decal(T.B('terra_d'), (p.x, p.y, Z_TA1 + 0.0006), Z, 0.02)
    for k in range(4):
        a = random.uniform(0, 2 * PI)
        decal(T.B('terra_d'), (math.cos(a) * 0.19, math.sin(a) * 0.19, Z_TA1 + 0.0007), Z, random.uniform(0.02, 0.035), 13, 0.6, 1.8, a + PI / 2)
    for k in range(16):                                                  # terra jogada por cima de um lado da tampa
        a = random.uniform(2.0, 3.3)
        r = random.uniform(0.06, 0.21)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        if (p - pl).length < 0.04 or (p - pa).length < 0.035:
            continue
        p.z = z_tampa(min(r, 0.2)) + 0.003
        pedra(T.B('terra'), p, random.uniform(0.012, 0.03), 0.38)
        if k % 4 == 0:
            mato(T.B('mato' if k % 8 else 'mato_seco'), p + Z * 0.006, 0.008, 5, (0.03, 0.07))
    for k in range(6):                                                   # ferrugem nas bordas e nos parafusos
        a = random.uniform(0, 2 * PI)
        ninho(T, (math.cos(a) * 0.2155, math.sin(a) * 0.2155, Z_TA0 + random.uniform(0.004, 0.018)), Vector((math.cos(a), math.sin(a), 0)), 0.008, 4, 0.0)
    for k in range(5):
        a = random.uniform(0, 2 * PI)
        p = Vector((math.cos(a) * 0.2152, math.sin(a) * 0.2152, Z_TA0 + 0.014))
        decal(T.B('lama'), p, Vector((math.cos(a), math.sin(a), 0)), random.uniform(0.012, 0.02))
    for k in range(4):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.09, 0.15)
        decal(T.B('oleo_d'), (math.cos(a) * r, math.sin(a) * r, z_tampa(r) + 0.0012), Z, random.uniform(0.012, 0.022))
    objs_tampa = fim_objs(T)
    piv = bpy.data.objects.new(nome + '_tampa_piv', None)
    sc.collection.objects.link(piv)
    for o in objs_tampa:
        o.parent = piv
    # disparo: onda (aro + faixa translúcida), poeira, arcos, faíscas, torrões, luz
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 1.0, 0.016, 160, 10)
    aro = suavizar(obj(nome + '_onda_aro', bm, 'onda_aro'))
    aro.visible_shadow = False
    bm = bmesh.new()
    ri = [0.72 + 0.28 * k / 6 for k in range(7)]
    an = [[bm.verts.new((math.cos(2 * PI * j / 120) * r, math.sin(2 * PI * j / 120) * r, 0.02 * (r - 0.72) / 0.28)) for j in range(120)] for r in ri]
    for A, B in zip(an, an[1:]):
        for j in range(120):
            bm.faces.new((A[j], A[(j + 1) % 120], B[(j + 1) % 120], B[j]))
    faixa_o = obj(nome + '_onda_faixa', bm, 'onda')
    faixa_o.visible_shadow = False
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 1.0, 0.16, 64, 12)
    po = obj(nome + '_poeira', bm, 'poeira_pulso')
    arcos = []
    for k in range(4):
        a = random.uniform(0, 2 * PI)
        b_ = a + random.uniform(0.5, 1.2)
        arcos.append(arco_obj(nome + '_arco%d' % k, (math.cos(a) * 0.212, math.sin(a) * 0.212, Z_TA0 + 0.003),
                              (math.cos(b_) * 0.3, math.sin(b_) * 0.3, alt_terra(0.3, b_) + 0.004), 0.3, 0.0022, galhos=1))
    pisca(arcos, 0.0, 5, {q: q % 4 for q in range(P_DISP, P_DISP + 9)})
    ev = [(P_DISP, (math.cos(a) * 0.215, math.sin(a) * 0.215, zc), (math.cos(a), math.sin(a), 0.6)) for a in (0.3, 1.9, 3.4, 4.8)]
    faiscas(nome + '_faisca', 28, ev, 1.4, 0.5, 9, 0.0)
    ev2 = [(P_DISP, (math.cos(a) * 0.35, math.sin(a) * 0.35, 0.03), (math.cos(a) * 0.6, math.sin(a) * 0.6, 1.0)) for a in [k * PI / 4 for k in range(8)]]
    projeteis(nome + '_torrao', 'terra', 24, ev2, 1.5, 0.45, 14, 0.008)
    lp = luz(nome + '_luz_pulso', (0.6, 0.3, 1.0), 0.0, (0, 0, 0.2), 0.1)
    ll = luz(nome + '_luz_led', (1.0, 0.06, 0.03), 0.0, P.W(pl + Z * 0.02), 0.01)

    def anima(q, fr):
        d = q - P_DISP
        piv.location = (0, 0, 0.016 * max(0.0, 1 - abs(d - 1) / 2.5))
        chave(piv, 'location', q)
        ativo = 0 <= d < 26
        t = min(1.0, max(0.0, d) / 26)
        R = 0.25 + 2.6 * (1 - (1 - t) ** 2)
        for o in (aro, faixa_o):
            o.hide_render = not ativo
            o.scale = (R, R, 1.0)
            o.location = (0, 0, 0.03)
            for c in ('hide_render', 'scale', 'location'):
                chave(o, c, q)
        ONDA_ARO.default_value = 18.0 * (1 - t) ** 1.4
        ONDA_ARO.keyframe_insert('default_value', frame=q)
        ONDA_FORCA.default_value = 7.0 * (1 - t) ** 1.2
        ONDA_FORCA.keyframe_insert('default_value', frame=q)
        tp = min(1.0, max(0.0, d) / 30)
        po.hide_render = not (0 <= d < 30)
        sp = 0.3 + 0.75 * (1 - (1 - tp) ** 2)
        po.scale = (sp, sp, 0.5 + 0.9 * tp)
        po.location = (0, 0, 0.04 + 0.05 * tp)
        for c in ('hide_render', 'scale', 'location'):
            chave(po, c, q)
        lp.data.energy = 110.0 * max(0.0, 1 - d / 8) ** 2 if d >= 0 else 0.0
        lp.data.keyframe_insert('energy', frame=q)
        # bobina: descarga forte no disparo, apagada, depois recarga crescendo
        if 0 <= d < 6:
            bf, bc = 40.0 * (1 - d / 6), (0.8, 0.5, 1.0)
        elif q < P_DISP or q >= 80:
            bf, bc = 1.6 + 0.4 * math.sin(2 * PI * 2 * fr), (0.6, 0.18, 1.0)
        elif q < 30:
            bf, bc = 0.0, (0.6, 0.18, 1.0)
        else:
            bf, bc = 2.2 * (q - 30) / 50, (1.0, 0.45, 0.05)
        BOBINA_LUZ.inputs['Emission Strength'].default_value = bf
        BOBINA_LUZ.inputs['Emission Color'].default_value = (*bc, 1)
        BOBINA_LUZ.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
        BOBINA_LUZ.inputs['Emission Color'].keyframe_insert('default_value', frame=q)
        # LED: armada = vermelho lento; descarregada = apagado; recarga = âmbar cada vez mais rápido
        if q < P_DISP or q >= 80:
            on = ((q - 80) % 12 < 4) if q >= 80 else (q % 12 < 4)
            cor, f_ = (1.0, 0.06, 0.03), 16.0 if on else 0.15
        elif q < 30:
            cor, f_ = (1.0, 0.06, 0.03), 0.0
        else:
            per = max(3, int(12 - 9 * (q - 30) / 50))
            on = (q - 30) % per < max(1, per // 2)
            cor, f_ = (1.0, 0.42, 0.04), 14.0 if on else 0.2
        LED_MINA.inputs['Emission Strength'].default_value = f_
        LED_MINA.inputs['Emission Color'].default_value = (*cor, 1)
        LED_MINA.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
        LED_MINA.inputs['Emission Color'].keyframe_insert('default_value', frame=q)
        ll.data.color = cor
        ll.data.energy = 0.35 * f_ / 16.0
        ll.data.keyframe_insert('energy', frame=q)
        ll.data.keyframe_insert('color', frame=q)
    ANIM.append(anima)


# ================================================================== montagem
GRUPOS = {}


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
L_PIL = [((0, 0), (3,)), ((1, 0), (1, 3)), ((2, 0), (1, 0)), ((2, 1), (2,))]


def montar_muro(centro, lado, base_seed):
    for i, ((x, y), lados) in enumerate(L_PIL):
        centro('%s_c%d' % (centro.__name__, i), x, y, lados, base_seed + i)
        for qd in lados:
            lado('%s_l%d_%d' % (lado.__name__, i, qd), x, y, qd, base_seed + 30 + i * 4 + qd)


def anima_campo(q, fr):
    CAMPO_FASE.default_value = 2 * PI * 2 * fr
    CAMPO_FASE.keyframe_insert('default_value', frame=q)


ANIM.append(anima_campo)
grupo('tijolo', lambda: montar_muro(tijolo_centro, tijolo_lado, 300))
grupo('liga', lambda: montar_muro(liga_centro, liga_lado, 400))
grupo('campo', lambda: montar_muro(campo_centro, campo_lado, 500))
grupo('mina', lambda: mina('mina'))
POS = {k: Vector((0, 0, 0)) for k in GRUPOS}
# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for f in ANIM:
        f(q, fr)
for o in list(sc.objects) + list(bpy.data.lights):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action and hasattr(ad.action, 'fcurves'):
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR' if not fc.data_path.startswith('hide') else 'CONSTANT'
# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (40, 30, -0.5), (200, 200, 1.0))
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


def foto(arq, grp, pos, alvo, lente, rx, ry):
    for nome, col in GRUPOS.items():
        col.hide_render = nome != grp
    off = POS[grp]
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    mirar(Vector(pos) + off, Vector(alvo) + off, lente)
    sc.render.filepath = os.path.join(AQUI, arq)
    bpy.ops.render.render(write_still=True)

modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_uma = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None
FOTOS = {
    'tijolo': ('muro_tijolo.png', 'tijolo', (3.55, -2.55, 2.05), (1.1, 0.25, 0.68), 30, 1600, 1100, F_FOTO),
    'liga': ('muro_liga.png', 'liga', (3.55, -2.55, 2.05), (1.1, 0.25, 0.68), 30, 1600, 1100, F_FOTO),
    'campo': ('muro_campo.png', 'campo', (3.55, -2.55, 2.05), (1.1, 0.25, 0.7), 30, 1600, 1100, F_FOTO),
    'mina': ('mina_pulso.png', 'mina', (0.82, -0.78, 0.55), (0.0, -0.02, 0.05), 38, 1400, 1100, 93),
    'mina_disparo': ('mina_pulso_disparo.png', 'mina', (1.75, -2.05, 1.15), (0.0, -0.1, 0.05), 28, 1600, 1100, 11),
}
EXTRAS = {    # só para revisão (modo rev)
    'tijolo_perto': ('rev/tijolo_perto.png', 'tijolo', (1.7, -1.25, 1.2), (1.0, 0.1, 0.7), 32, 1200, 900, F_FOTO),
    'liga_perto': ('rev/liga_perto.png', 'liga', (1.7, -1.25, 1.2), (1.0, 0.1, 0.8), 32, 1200, 900, F_FOTO),
    'campo_perto': ('rev/campo_perto.png', 'campo', (1.7, -1.25, 1.2), (1.0, 0.1, 0.8), 32, 1200, 900, F_FOTO),
    'mina_topo': ('rev/mina_topo.png', 'mina', (0.25, -0.35, 0.75), (0.0, 0.0, 0.06), 40, 1000, 900, 93),
    'mina_carga': ('rev/mina_carga.png', 'mina', (0.82, -0.78, 0.55), (0.0, -0.02, 0.05), 38, 1000, 800, 66),
}
if modo in ('foto', 'teste', 'rev'):
    sc.cycles.samples = 128 if modo == 'foto' else (64 if modo == 'rev' else 24)
    os.makedirs(os.path.join(AQUI, 'rev'), exist_ok=True)
    lista = EXTRAS if modo == 'rev' else FOTOS
    for chave_f, (arq, grp, pos, alvo, lente, rx, ry, qf) in lista.items():
        if so_uma and chave_f != so_uma:
            continue
        if modo == 'teste':
            rx, ry = rx // 2, ry // 2
        sc.frame_set(qf)
        foto(arq, grp, pos, alvo, lente, rx, ry)
print('MUROS_MINA ok')
