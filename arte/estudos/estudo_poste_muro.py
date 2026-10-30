"""Estudo isolado (fora do jogo): rede de energia da IA e muro de defesa — POSTE DE ENERGIA, TORRE SEM FIO e MURO.
Áreas e alturas como no arte/CATALOGO.md (1 tile = 1 m; x leste, y norte):
- poste_energia (1×1, só o centro do tile, 0,70 × 0,40 × 2,30): poste de concreto afilado e rachado (lasca com
  vergalhão enferrujado à mostra) encaixado numa luva de aço com nervuras sobre chapa chumbada num bloco de concreto
  (4 chumbadores com porca e arruela). Cruzeta em cantoneira presa por parafuso U e mãos-francesas; três isoladores
  de porcelana (um com a saia lascada, que solta faíscas) e um para-raios polimérico; condutores chegando e saindo em
  catenária; transformador pequeno com aletas, tampa aparafusada, buchas de AT e BT, placa, óleo vazando; cabos de
  BT com laço de gotejamento entrando num eletroduto com pescoço de ganso que desce e some no chão; captor no topo
  com o anel de campo violeta da IA; cabo de descida de cobre até a haste de terra; faixa refletiva gasta, número
  de série em estêncil, fios remendados com fita, ninhos de ferrugem, nó da IA com LED.
- torre_sem_fio (1×1, 0,80 × 0,80 × 2,90, parte `cristal`): mastro treliçado triangular galvanizado e enferrujado,
  três estais com esticadores ancorados na laje; plataforma com bobina de Tesla (primário em espiral de tubo de
  cobre sobre barras de fenolite, secundário com enrolamento helicoidal, toroide de alumínio queimado) e o cristal no
  topo preso por garras, pulsando; arcos de energia saindo do toroide e do cristal para o ar. Na base: banco de
  capacitores (um estufado e vazando), centelhador com arco, caixa de entrada com eletroduto, cabos subindo pela
  perna, fita de aterramento até a haste. Marcas de queimado de arco, ferrugem.
- muro_centro (pilar 0,64 × 0,64 × 1,50, com recuo: base larga até 0,72 m, pingadeira inclinada, parte alta de
  0,50) e muro_lado (pano 0,20 × 1,26 do centro à borda norte; girado para os outros lados): pedra rachão
  assentada em argamassa, cantoneiras na base, cinta aparafusada no alto, capa com espetos,
  arame farpado no pano, chapa de reforço; mordidas e ácido das aranhas, musgo e lama embaixo, rachaduras e remendos.
  Toque da IA: sensor (olho que varre) e emissor de campo no topo do pilar. Montado em L com 4 pilares.
- rede: dois postes e uma torre ligando máquinas genéricas (blocos) com cabos e arcos.
Animação (laço de 4 s): arcos piscando, faíscas no isolador lascado, cristal pulsando, anel girando, cabos balançando.
Uso: blender -b --python estudo_poste_muro.py -- foto [chave]   (chaves: poste, poste_perto, torre, torre_perto,
     muro, muro_perto, rede)        blender -b --python estudo_poste_muro.py -- teste [chave]"""
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


# ================================================================== POSTE DE ENERGIA
ZB = 0.09           # topo do bloco de concreto
ZTP = 2.16          # topo do concreto do poste
ZC = 1.98           # cruzeta (topo da aba horizontal)


def rp(z):
    return 0.078 + (0.055 - 0.078) * (z - ZB) / (ZTP - ZB)


ISO_X = (-0.29, -0.13, 0.29)
Y_ARM = -0.095
XT = 0.22           # eixo do transformador
ZT0, ZT1 = 1.25, 1.55
RT = 0.085


def isolador(P, x, y, z, lascado=False):
    """Isolador de pino de porcelana; devolve o ponto (local) onde o condutor apoia no topo."""
    tubo(P.B('aco'), (x, y, z - 0.03), (x, y, z + 0.03), 0.008, 10)
    porca(P.B('aco'), (x, y, z - 0.006), -Z, 0.013, 0.01)
    cil(P.B('aco'), (x, y, z + 0.004), 0.016, 0.008, lados=6)
    bp = P.B('porcelana', True)
    cil(bp, (x, y, z + 0.055), 0.017, 0.09, lados=20)
    for k, (dz, rr) in enumerate(((0.026, 0.034), (0.05, 0.04), (0.074, 0.047))):
        if lascado and k == 1:
            a0 = random.uniform(0, 2 * PI)
            saia(bp, (x, y, z + dz), 0.016, rr, 0.013, a0, a0 + 2 * PI - 1.1, 26, P.B('porcelana_crua'))
            cil(P.B('porcelana_crua'), Vector((x, y, z + dz + 0.004)) + Vector((math.cos(a0 - 0.55), math.sin(a0 - 0.55), 0)) * 0.0185,
                0.004, 0.009, lados=6)
        else:
            saia(bp, (x, y, z + dz), 0.016, rr, 0.013, n=28)
    cil(bp, (x, y, z + 0.104), 0.021, 0.022, lados=24)                   # cabeça
    toro(P.B('aluminio', True), (x, y, z + 0.1), 0.0215, 0.0028, 24, 6)  # amarração no pescoço
    cil(bp, (x, y, z + 0.117), 0.021, 0.004, lados=24, r2=0.016)
    topo = Vector((x, y, z + 0.119 + 0.0055))
    for s in (-1, 1):                                                    # fio de amarração em volta do condutor
        toro(P.B('aluminio', True), topo + Vector((0, s * 0.026, 0)), 0.0075, 0.0018, 14, 5, Vector((0, 1, 0)))
        tubo(P.B('aluminio'), topo + Vector((0.006, s * 0.026, -0.006)), (x + 0.018, y + s * 0.006, z + 0.1), 0.0017, 5)
    return topo


def poste(nome, cx, cy, ang, destinos, seed, faiscas_on=True, terra_dir=None):
    """destinos: lista (índice do isolador, ponto mundo) → condutores em catenária saindo de cada isolador."""
    random.seed(seed)
    P = Peca(nome, cx, cy, ang)
    # --- bloco de concreto, chapa, chumbadores, luva com nervuras
    bc = P.B('concreto')
    caixa_de(bc, (-0.2, -0.2, 0.0), (0.2, 0.2, ZB))
    caixa_de(bc, (-0.215, -0.215, -0.02), (0.215, 0.215, 0.012))          # rebarba da forma
    for k in range(3):
        rachadura_plana(P.B('fenda'), (random.uniform(-0.15, 0.15), -0.2, ZB - 0.005), (0, -1, 0), 0.08, -PI / 2 + random.uniform(-0.4, 0.4), 4)
    rachadura_plana(P.B('fenda'), (0.2, 0.05, ZB - 0.003), (1, 0, 0), 0.09, -PI / 2, 5)
    caixa_de(P.B('quebra'), (0.168, 0.168, ZB - 0.035), (0.201, 0.201, ZB + 0.0005))   # quina quebrada
    caixa_de(P.B('aco'), (-0.15, -0.15, ZB), (0.15, 0.15, ZB + 0.018))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Vector((sx * 0.115, sy * 0.115, ZB + 0.018))
            tubo(P.B('aco'), p - Z * 0.02, p + Z * 0.05, 0.009, 10)
            porca(P.B('aco'), p, Z, 0.016, 0.014)
            ninho(P, p + Vector((sx * 0.02, sy * 0.012, 0.005)), Vector((sx, 0, 0)), 0.012, 4, 0)
            escorrido(P.B('escorre'), Vector((sx * 0.2, sy * 0.1, ZB)), Vector((sx, 0, 0)), 0.07, 0.016)
    bl = P.B('aco', True)
    cil(bl, (0, 0, ZB + 0.018 + 0.1), 0.095, 0.2, lados=32)
    toro(bl, (0, 0, ZB + 0.218), 0.095, 0.006, 32, 6)
    for k in range(4):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        for i in range(4):
            z0 = ZB + 0.018 + i * 0.03
            ext = 0.06 * (1 - i / 4)
            caixa(P.B('aco'), d * (0.095 + ext / 2) + Z * (z0 + 0.015), (ext, 0.008, 0.03), rot_cols(d, t, Z))
    for k in range(3):                                                    # parafusos da luva
        a = k * 2 * PI / 3 + 0.4
        d = Vector((math.cos(a), math.sin(a), 0))
        cil(P.B('aco'), d * 0.098 + Z * (ZB + 0.17), 0.009, 0.012, d, lados=6)
    # --- poste de concreto afilado
    bmesh.ops.create_cone(P.B('concreto_poste', True), cap_ends=True, segments=28, radius1=rp(ZB + 0.12),
                          radius2=rp(ZTP), depth=ZTP - ZB - 0.12, matrix=Matrix.Translation((0, 0, (ZB + 0.12 + ZTP) / 2)))
    cil(P.B('concreto_poste', True), (0, 0, ZTP + 0.008), rp(ZTP) * 0.95, 0.016, lados=28, r2=rp(ZTP) * 0.7)

    def sup(a, z, extra=0.0):
        return Vector((math.cos(a), math.sin(a), 0)) * (rp(z) + extra) + Z * z

    # trincas verticais e a lasca com vergalhão
    for (a0, z0, L) in ((0.9, 0.85, 0.55), (2.6, 1.55, 0.4), (-1.0, 0.5, 0.35), (-2.3, 1.9, 0.3)):
        a, z = a0, z0
        for i in range(9):
            a2, z2 = a + random.uniform(-0.12, 0.12), z - L / 9
            p, q = sup(a, z, 0.0006), sup(a2, z2, 0.0006)
            u = (q - p).normalized()
            nrm = Vector((math.cos(a), math.sin(a), 0))
            caixa(P.B('fenda'), (p + q) / 2, ((q - p).length + 0.003, 0.0016, 0.0028 * (1 - i / 12)), rot_cols(u, nrm, u.cross(nrm)))
            a, z = a2, z2
    a_l, z_l = 2.2, 0.62                                                  # lasca: concreto arrancado
    for i in range(5):
        zz = z_l - 0.06 + i * 0.03
        caixa(P.B('quebra'), sup(a_l, zz, -0.004), (0.012, 0.055 - abs(i - 2) * 0.012, 0.032),
              rot_cols(Vector((math.cos(a_l), math.sin(a_l), 0)), Vector((-math.sin(a_l), math.cos(a_l), 0)), Z))
    for s in (-0.012, 0.012):
        tubo(P.B('escorre'), sup(a_l + s * 6, z_l - 0.07, -0.003), sup(a_l + s * 6, z_l + 0.07, -0.003), 0.0045, 8)
    escorrido(P.B('escorre'), sup(a_l, z_l - 0.075, 0.0), Vector((math.cos(a_l), math.sin(a_l), 0)), 0.22, 0.02)
    # faixa refletiva gasta
    bmesh.ops.create_cone(P.B('refletiva', True), cap_ends=False, segments=32, radius1=rp(0.95) + 0.0025,
                          radius2=rp(1.07) + 0.0025, depth=0.12, matrix=Matrix.Translation((0, 0, 1.01)))
    # número de série em estêncil (vertical)
    a_s = 1.1
    n_s = Vector((math.cos(a_s), math.sin(a_s), 0))
    serie_plana(P.B('tinta'), sup(a_s, 0.62, 0.0008), n_s, 0.03, 5, horiz=Z)
    # --- cruzeta (cantoneira), parafuso U, mãos-francesas, cinta
    bg = P.B('galv')
    caixa_de(bg, (-0.35, Y_ARM - 0.03, ZC - 0.006), (0.35, Y_ARM + 0.03, ZC))
    caixa_de(bg, (-0.35, Y_ARM + 0.024, ZC - 0.06), (0.35, Y_ARM + 0.03, ZC))
    for sx in (-1, 1):                                                   # ponteiras cortadas tortas e ferrugem
        ninho(P, (sx * 0.33, Y_ARM + 0.022, ZC - 0.03), Vector((0, -1, 0)), 0.01, 3, 0.02)
    ru = rp(ZC - 0.03) + 0.007
    pts = []
    for i in range(17):
        a = PI * i / 16
        pts.append(Vector((math.cos(a) * ru, math.sin(a) * ru, ZC - 0.03)))
    pts = [Vector((ru, Y_ARM + 0.045, ZC - 0.03))] + pts[0:] + [Vector((-ru, Y_ARM + 0.045, ZC - 0.03))]
    pts = [Vector((ru, Y_ARM - 0.0, ZC - 0.03))] + pts + [Vector((-ru, Y_ARM - 0.0, ZC - 0.03))]
    varrer(P.B('aco', True), pts, 0.006, 8)
    for sx in (-1, 1):
        porca(P.B('aco'), (sx * ru, Y_ARM + 0.024, ZC - 0.03), -Vector((0, 1, 0)), 0.011, 0.009)
        tubo(P.B('aco'), (sx * ru, Y_ARM + 0.012, ZC - 0.03), (sx * ru, Y_ARM + 0.026, ZC - 0.03), 0.006, 8)
    ninho(P, (ru, Y_ARM + 0.022, ZC - 0.036), Vector((0, -1, 0)), 0.014, 6, 0.022)
    zf = ZC - 0.32
    anel_cinta(P.B('galv'), (0, 0, zf), rp(zf) + 0.001, 0.007, 0.04)
    caixa(P.B('galv'), (0, -rp(zf) - 0.016, zf), (0.05, 0.018, 0.04))
    for sx in (-1, 1):
        a = Vector((sx * 0.25, Y_ARM + 0.0, ZC - 0.008))
        b = Vector((sx * 0.022, -rp(zf) - 0.022, zf))
        viga(P.B('galv'), a, b, 0.012)
        porca(P.B('aco'), b + Vector((sx * 0.006, -0.008, 0)), Vector((sx, 0, 0)), 0.008, 0.006)
        cil(P.B('aco'), Vector((sx * 0.25, Y_ARM, ZC - 0.012)), 0.008, 0.008, lados=6)
    ninho(P, (-0.022, -rp(zf) - 0.024, zf - 0.006), Vector((0, -1, 0)), 0.012, 5, 0)
    escorrido(P.B('escorre'), Vector((0, -rp(zf - 0.02) - 0.0005, zf - 0.02)), (0, -1, 0), 0.25, 0.014)
    # --- isoladores e para-raios
    topos = []
    for i, x in enumerate(ISO_X):
        topos.append(P.W(isolador(P, x, Y_ARM, ZC, lascado=(i == 1))))
    xa = 0.13                                                           # para-raios
    tubo(P.B('aco'), (xa, Y_ARM, ZC - 0.045), (xa, Y_ARM, ZC + 0.02), 0.007, 8)
    porca(P.B('aco'), (xa, Y_ARM, ZC - 0.008), -Z, 0.012, 0.009)
    bpol = P.B('polimero', True)
    cil(bpol, (xa, Y_ARM, ZC + 0.075), 0.017, 0.11, lados=20)
    for k in range(5):
        cil(bpol, (xa, Y_ARM, ZC + 0.03 + k * 0.022), 0.03 - 0.002 * (k % 2), 0.006, lados=24, r2=0.019)
    cil(P.B('aluminio', True), (xa, Y_ARM, ZC + 0.137), 0.014, 0.014, lados=16)
    tubo(P.B('aluminio'), (xa, Y_ARM, ZC + 0.144), (xa, Y_ARM, ZC + 0.16), 0.004, 8)
    cil(P.B('borracha'), (xa, Y_ARM, ZC - 0.055), 0.012, 0.022, lados=12)     # desligador
    chamusco_pt = Vector((xa, Y_ARM - 0.017, ZC + 0.05))
    decal(P.B('queimado'), chamusco_pt, (0, -1, 0), 0.008, alongar=0.7)
    # --- captor e anel de campo (toque da IA)
    tubo(P.B('aco'), (0, 0, ZTP + 0.01), (0, 0, 2.27), 0.009, 12)
    for k in range(3):
        a = k * 2 * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        tubo(P.B('aco'), Vector((0, 0, 2.265)), Vector((0, 0, 2.285)) + d * 0.018, 0.003, 6)
    cil(P.B('aco'), (0, 0, 2.28), 0.0045, 0.04, lados=8, r2=0.0005)
    cil(P.B('aco'), (0, 0, ZTP + 0.02), 0.022, 0.012, lados=6)
    bc2 = P.B('cobre', True)
    for k in range(5):
        toro(bc2, (0, 0, 2.185 + k * 0.0065), 0.016, 0.0034, 24, 6)
    cil(P.B('grafite'), (0, 0, 2.18), 0.026, 0.006, lados=20)
    cil(P.B('grafite'), (0, 0, 2.22), 0.026, 0.004, lados=20)
    # --- nó da IA (caixa com LED) no lado norte
    zn = 1.74
    nn = Vector((0, 1, 0))
    yb = rp(zn) + 0.006
    anel_cinta(P.B('galv'), (0, 0, zn - 0.03), rp(zn - 0.03) + 0.001, 0.006, 0.025)
    anel_cinta(P.B('galv'), (0, 0, zn + 0.03), rp(zn + 0.03) + 0.001, 0.006, 0.025)
    caixa_de(P.B('grafite'), (-0.035, yb, zn - 0.05), (0.035, yb + 0.045, zn + 0.05))
    caixa_de(P.B('oxido'), (-0.037, yb + 0.045, zn - 0.052), (0.037, yb + 0.05, zn + 0.052))   # tampa trocada
    for sx in (-1, 1):
        for sz in (-1, 1):
            cil(P.B('aco'), (sx * 0.03, yb + 0.051, zn + sz * 0.045), 0.004, 0.004, nn, lados=6)
    cil(P.B('led_v'), (0.015, yb + 0.052, zn + 0.025), 0.005, 0.004, nn, lados=10)
    cil(P.B('borracha'), (-0.012, yb + 0.052, zn + 0.025), 0.0055, 0.004, nn, lados=10)
    serie_plana(P.B('tinta'), (0, yb + 0.0505, zn - 0.012), nn, 0.012, 4)
    tubo(P.B('borracha'), (0.02, yb + 0.02, zn + 0.05), (0.02, yb + 0.02, zn + 0.06), 0.004, 8)
    pts = [Vector((0.02, yb + 0.02, zn + 0.06)), Vector((0.02, rp(zn + 0.15) + 0.022, zn + 0.15)),
           Vector((0.02, rp(2.0) + 0.022, 2.0)), Vector((0.02, rp(2.14) + 0.022, 2.14)), Vector((0.012, 0.03, 2.19))]
    pts = bezier(pts[0], pts[1], pts[2], pts[2], 8) + bezier(pts[2], pts[3], pts[3], pts[4], 6)[1:]
    varrer(P.B('borracha', True), pts, 0.0032, 8)
    # --- transformador
    bt = P.B('trafo', True)
    cil(bt, (XT, 0, (ZT0 + ZT1) / 2), RT, ZT1 - ZT0, lados=40)
    cil(bt, (XT, 0, ZT0 - 0.008), RT * 0.93, 0.016, lados=40)
    cil(P.B('trafo', True), (XT, 0, ZT1 + 0.007), RT + 0.009, 0.014, lados=40)
    cil(P.B('trafo', True), (XT, 0, ZT1 + 0.018), RT * 0.95, 0.009, lados=40, r2=RT * 0.75)
    for k in range(14):                                                  # parafusos da tampa
        a = 2 * PI * k / 14 + 0.1
        if k == 5:
            continue                                                     # um parafuso faltando
        cil(P.B('aco'), Vector((XT + math.cos(a) * (RT + 0.004), math.sin(a) * (RT + 0.004), ZT1 + 0.017)), 0.005, 0.006, lados=6)
    for ad in (30, 45, 60, 110, 125, 140, -30, -45, -60, -110, -125, -140):           # aletas (falta a frente das buchas de BT)
        a = math.radians(ad)
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        caixa(P.B('trafo'), Vector((XT, 0, (ZT0 + ZT1) / 2 - 0.005)) + d * (RT + 0.014), (0.03, 0.004, ZT1 - ZT0 - 0.07), rot_cols(d, t, Z))
    for ad in (60,):                                                      # uma aleta amassada e enferrujada
        d = Vector((math.cos(math.radians(ad)), math.sin(math.radians(ad)), 0))
        ninho(P, Vector((XT, 0, ZT0 + 0.06)) + d * (RT + 0.03), d, 0.012, 5, 0)
    for sy in (-1, 1):                                                   # olhais de içamento
        caixa(P.B('trafo'), (XT, sy * (RT + 0.004), ZT1 + 0.006), (0.025, 0.012, 0.03))
        tubo(P.B('aco'), (XT - 0.008, sy * (RT + 0.006), ZT1 + 0.02), (XT + 0.008, sy * (RT + 0.006), ZT1 + 0.02), 0.004, 6)
    buchas_at = []
    for sx in (-1, 1):                                                   # buchas de AT na tampa
        c = Vector((XT + sx * 0.036, 0.012 * sx, ZT1 + 0.02))
        cil(P.B('porcelana', True), c + Z * 0.025, 0.011, 0.05, lados=16)
        for k in range(3):
            cil(P.B('porcelana', True), c + Z * (0.012 + k * 0.016), 0.019, 0.005, lados=18, r2=0.012)
        tubo(P.B('latao'), c + Z * 0.05, c + Z * 0.068, 0.0045, 8)
        cil(P.B('latao'), c + Z * 0.062, 0.008, 0.006, lados=6)
        buchas_at.append(P.W(c + Z * 0.068))
    buchas_bt = []
    for k, yy in enumerate((-0.035, 0.0, 0.035)):                        # buchas de BT no lado leste
        c = Vector((XT + RT, yy, ZT0 + 0.2))
        cil(P.B('borracha', True), c + Vector((0.016, 0, 0)), 0.01, 0.032, Vector((1, 0, 0)), lados=14)
        cil(P.B('borracha', True), c + Vector((0.01, 0, 0)), 0.015, 0.006, Vector((1, 0, 0)), lados=16)
        tubo(P.B('latao'), c + Vector((0.03, 0, 0)), c + Vector((0.045, 0, 0)), 0.004, 8)
        buchas_bt.append(P.W(c + Vector((0.045, 0, 0))))
    pl = Vector((XT, -RT - 0.0015, ZT0 + 0.15))                          # placa de identificação
    caixa(P.B('mostrador'), pl, (0.045, 0.002, 0.045))
    serie_plana(P.B('tinta'), pl + Vector((0, -0.0012, 0.008)), (0, -1, 0), 0.008, 6, 0.2)
    for k in range(3):
        caixa(P.B('fenda'), pl + Vector((0, -0.0014, -0.006 - k * 0.005)), (0.034 - k * 0.008, 0.0008, 0.0015))
    serie_plana(P.B('tinta'), Vector((XT, RT + 0.0005, ZT0 + 0.12)), (0, 1, 0), 0.022, 4, 0.45)
    for k in range(6):                                                   # cintas de fixação no poste
        pass
    for zz in (ZT0 + 0.07, ZT1 - 0.07):
        anel_cinta(P.B('galv'), (0, 0, zz), rp(zz) + 0.001, 0.007, 0.035)
        caixa_de(P.B('galv'), (rp(zz) + 0.006, -0.03, zz - 0.016), (XT - RT + 0.004, 0.03, zz + 0.016))
        caixa_de(P.B('galv'), (XT - RT - 0.004, -0.045, zz - 0.022), (XT - RT + 0.002, 0.045, zz + 0.022))
        for sy in (-1, 1):
            cil(P.B('aco'), (XT - RT - 0.006, sy * 0.035, zz), 0.006, 0.006, Vector((1, 0, 0)), lados=6)
        ninho(P, (rp(zz) + 0.02, -0.031, zz - 0.012), Vector((0, -1, 0)), 0.012, 5, 0.012)
    # registro de dreno vazando óleo
    dv = Vector((XT, -RT, ZT0 + 0.025))
    tubo(P.B('latao'), dv, dv + Vector((0, -0.025, 0)), 0.006, 10)
    cil(P.B('latao'), dv + Vector((0, -0.025, 0)), 0.009, 0.01, Vector((0, 1, 0)), lados=6)
    tubo(P.B('latao'), dv + Vector((0, -0.018, 0)), dv + Vector((0, -0.018, 0.018)), 0.003, 6)
    escorrido(P.B('oleo'), dv + Vector((0.012, 0.0, -0.004)), (0, -1, 0), 0.03, 0.02)
    escorrido(P.B('oleo'), Vector((XT + 0.012, -RT - 0.0003, ZT0 + 0.11)), (0, -1, 0), 0.075, 0.012)
    gota_p = P.W(dv + Vector((0, -0.034, -0.008)))
    bm = bmesh.new()
    mancha(bm, (gota_p.x, gota_p.y), 0.06, 0.003)
    obj(nome + '_poca_oleo', bm, 'oleo')
    bm = bmesh.new()
    mancha(bm, (gota_p.x, gota_p.y), 0.14, 0.0015)
    obj(nome + '_halo', bm, 'halo')
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.005)
    gota = obj(nome + '_gota', bm, 'oleo')

    def anima_gota(q, fr, gota=gota, p=gota_p):
        u = (fr * 2) % 1.0
        if u < 0.75:
            s = 0.3 + 0.7 * u / 0.75
            gota.location = p - Z * 0.004 * s
            gota.scale = (s, s, s * 1.2)
        else:
            t = (u - 0.75) * 2.0
            gota.location = p - Z * (0.006 + 4.9 * t * t)
            gota.scale = (0.8, 0.8, 1.4) if gota.location.z > 0.01 else (0.01, 0.01, 0.01)
        chave(gota, 'location', q)
        chave(gota, 'scale', q)
    ANIM.append(anima_gota)
    # --- eletroduto de BT com pescoço de ganso, descendo e sumindo no chão
    xe = 0.112
    re = 0.016
    pts = [Vector((0.25, 0, -0.05)), Vector((0.25, 0, 0.12))]
    pts += [Vector((0.25 - (0.25 - xe) * (1 - math.cos(a)), 0, 0.12 + 0.138 * math.sin(a)))
            for a in (PI / 2 * i / 8 for i in range(1, 9))]
    pts += [Vector((xe, 0, 0.3)), Vector((xe, 0, 1.12))]
    rg = 0.04
    pts += [Vector((xe + rg - rg * math.cos(a), 0, 1.12 + rg * math.sin(a))) for a in (PI * i / 10 for i in range(1, 11))]
    pts += [Vector((xe + 2 * rg, 0, 1.11))]
    varrer(P.B('galv', True), pts, re, 16, tampas=(False, False))
    boca = Vector((xe + 2 * rg, 0, 1.105))
    toro(P.B('borracha', True), boca, re - 0.003, 0.003, 18, 6)
    for zz in (0.42, 0.78, 1.02):
        chapa_arco(P.B('galv', True), (xe, 0, zz), Z, re + 0.001, 0.004, 0.03, -PI / 2, PI / 2 + 0.01, 12)
        caixa_de(P.B('galv'), (rp(zz), -0.012, zz - 0.015), (xe - re + 0.002, 0.012, zz + 0.015))
        anel_cinta(P.B('galv'), (0, 0, zz), rp(zz) + 0.001, 0.005, 0.03)
    ninho(P, (xe + 0.01, -0.012, 0.42), Vector((0, -1, 0)), 0.012, 4, 0)
    decal(P.B('lama'), (0.25, -0.012, 0.06), (0, -1, 0), 0.025, alongar=0.8)
    # cabos de BT: das buchas, laço de gotejamento, para dentro do pescoço de ganso
    for k, bb in enumerate(buchas_bt):
        loc = s_inv = None
        bl_ = P.M.inverted() @ bb
        yy = bl_.y
        b0 = bl_
        p1 = Vector((0.4, yy * 1.2, b0.z - 0.02))
        p2 = Vector((0.39, yy * 0.9, 1.0 - 0.01 * k))
        p3 = Vector((0.27, yy * 0.6, 1.02 - 0.01 * k))
        pA = bezier(b0, b0 + Vector((0.06, 0, 0)), p1, p2, 10)
        pB = bezier(p2, p2 + (p2 - p1).normalized() * 0.0 + Vector((-0.04, 0, -0.04)), Vector((boca.x + 0.02, yy * 0.4, 1.0)),
                    Vector((boca.x, yy * 0.35, boca.z - 0.004)), 10)[1:]
        pts_w = [P.W(p) for p in pA + pB]
        fit = ((0.35, 0.45, 'fita'),) if k == 1 else (((0.55, 0.62, 'fita_azul'),) if k == 2 else ())
        cabo(nome + '_bt%d' % k, pts_w[0], pts_w[-1], 0, 0.0055, 'borracha', amp=0.02, freq=1, fitas=fit, pts=pts_w)
    # --- aterramento: descida de cobre do captor até a haste
    xg = -1
    sd = 0.02
    zs = [ZTP + 0.012] + [ZTP - 0.06 - i * 0.3 for i in range(7)] + [ZB + 0.27]
    pts = [Vector((-0.012, 0, ZTP + 0.016))]
    pts += [Vector((-(rp(z) + sd), 0, z)) for z in zs[1:]]
    pts += bezier(pts[-1], pts[-1] - Z * 0.06, Vector((-0.15, 0, ZB + 0.1)), Vector((-0.17, 0.0, ZB + 0.025)), 8)[1:]
    pts_s = [pts[0]] + bezier(pts[0], pts[0] + Vector((-0.04, 0, 0)), pts[1] + Vector((0, 0, 0.05)), pts[1], 6)[1:] + pts[2:]
    varrer(P.B('cobre_velho', True), pts_s, 0.0032, 8)
    for z in zs[1:]:
        caixa_de(P.B('galv'), (-(rp(z) + sd + 0.004), -0.005, z - 0.008), (-rp(z) + 0.002, 0.005, z + 0.008))
        if random.random() < 0.4:
            decal(P.B('zinabre'), Vector((-(rp(z) + sd + 0.0033), 0, z - 0.03)), (-1, 0, 0), 0.006, alongar=0.6)
    gp = Vector((-0.17, 0, ZB + 0.012))
    caixa(P.B('latao'), gp + Z * 0.005, (0.03, 0.02, 0.012))               # terminal na chapa? (fica no bloco)
    pts = bezier(Vector((-0.17, 0, ZB + 0.02)), Vector((-0.215, 0, ZB + 0.03)), Vector((-0.24, 0.02, 0.02)), Vector((-0.27, 0.05, 0.05)), 8)
    varrer(P.B('cobre_velho', True), pts, 0.0032, 8)
    cil(P.B('cobre_velho', True), (-0.27, 0.05, 0.02), 0.009, 0.08, lados=12)  # haste de terra
    caixa(P.B('latao'), (-0.27, 0.05, 0.05), (0.03, 0.024, 0.018))
    cil(P.B('aco'), (-0.27, 0.064, 0.05), 0.006, 0.008, Vector((0, 1, 0)), lados=6)
    # para-raios → olhal da tampa do transformador (terra comum)
    pts = bezier(Vector((xa, Y_ARM, ZC - 0.066)), Vector((xa + 0.01, Y_ARM - 0.02, ZC - 0.2)),
                 Vector((XT - 0.05, -0.1, ZT1 + 0.15)), Vector((XT - 0.04, -0.07, ZT1 + 0.016)), 14)
    varrer(P.B('cobre_velho', True), pts, 0.0028, 8)
    caixa(P.B('latao'), (XT - 0.04, -0.07, ZT1 + 0.016), (0.014, 0.014, 0.01))
    # --- jumpers: linha → buchas de AT; para-raios → linha (com conector)
    t_b = P.M.inverted() @ topos[1]
    t_c = P.M.inverted() @ topos[2]
    ba0 = P.M.inverted() @ buchas_at[0]
    ba1 = P.M.inverted() @ buchas_at[1]
    j1 = bezier(t_b + Vector((0.0, -0.03, 0)), t_b + Vector((0.0, -0.17, -0.12)), Vector((0.12, -0.2, 1.75)), ba0, 18)
    j2 = bezier(t_c + Vector((0.0, -0.03, 0)), t_c + Vector((0.04, -0.18, -0.15)), Vector((0.3, -0.12, 1.72)), ba1, 16)
    j3 = bezier(Vector((xa, Y_ARM, ZC + 0.16)), Vector((xa + 0.02, Y_ARM, ZC + 0.21)), t_c + Vector((-0.06, -0.02, 0.06)),
                t_c + Vector((-0.0, -0.015, 0.0)), 10)
    for nome_j, pj, fit in (('j1', j1, ((0.45, 0.55, 'fita'),)), ('j2', j2, ((0.3, 0.37, 'fita_prata'), (0.62, 0.7, 'fita'))),
                            ('j3', j3, ())):
        pw = [P.W(p) for p in pj]
        cabo(nome + '_' + nome_j, pw[0], pw[-1], 0, 0.0045, 'borracha' if nome_j != 'j3' else 'cabo', amp=0.03, freq=1,
             fitas=fit, pts=pw)
    for t in (t_b, t_c):                                                 # conectores de derivação
        caixa(P.B('aluminio'), t + Vector((0, -0.03, 0.004)), (0.02, 0.022, 0.02))
        cil(P.B('aco'), t + Vector((0, -0.03, 0.017)), 0.004, 0.006, lados=6)
    caixa(P.B('aluminio'), t_c + Vector((0, -0.015, 0.004)), (0.018, 0.012, 0.016))
    # --- condutores (catenária) saindo de cada isolador
    for i, dst in destinos:
        a = topos[i]
        L = (Vector(dst) - a).length
        cabo(nome + '_cond%d_%d' % (i, random.randint(0, 999)), a, dst, 0.035 * L + 0.04, 0.0055, 'cabo',
             amp=0.03 + 0.01 * L, freq=1)
    # --- chão: brita, lama, musgo no bloco
    for k in range(40):
        a = random.uniform(0, 2 * PI)
        rr = random.uniform(0.23, 0.45)
        x_, y_ = math.cos(a) * rr, math.sin(a) * rr
        if max(abs(x_), abs(y_)) < 0.225 or (abs(x_ - 0.25) < 0.04 and abs(y_) < 0.04) or (abs(x_ + 0.27) < 0.03 and abs(y_ - 0.05) < 0.03):
            continue
        pedra(P.B('brita'), (x_, y_, 0.0), random.uniform(0.008, 0.022), 0.5)
    for k in range(10):
        a = random.uniform(PI * 0.3, PI * 0.8)
        pedra(P.B('musgo'), (math.cos(a) * 0.2, math.sin(a) * 0.2, random.uniform(0.0, 0.05)), random.uniform(0.012, 0.025), 0.5)
    bm = bmesh.new()
    mancha(bm, (0, 0), 0.34, 0.0012)
    bm.transform(P.M)
    obj(nome + '_halo_base', bm, 'halo')
    P.fim()
    # --- animados: anel de campo, luz, faíscas no isolador lascado
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 0.055, 0.0045, 40, 8)
    anel = suavizar(obj(nome + '_anel_campo', bm, 'violeta'))
    anel.location = P.W((0, 0, 2.238))
    anel.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 0.036, 0.0022, 32, 6)
    anel2 = suavizar(obj(nome + '_anel_campo2', bm, 'violeta'))
    anel2.location = P.W((0, 0, 2.205))
    anel2.rotation_mode = 'QUATERNION'
    lz = luz(nome + '_luz_anel', (0.6, 0.2, 1.0), 2.0, P.W((0, 0, 2.24)), 0.05)
    fse = random.random()

    def anima_anel(q, fr, anel=anel, anel2=anel2, lz=lz, fse=fse):
        anel.rotation_quaternion = Quaternion(Z, 2 * PI * 2 * fr) @ Quaternion((1, 0, 0), 0.12 * math.sin(2 * PI * (fr + fse)))
        s = 1 + 0.06 * math.sin(2 * PI * 4 * fr)
        anel.scale = (s, s, s)
        anel.location.z = (P.W((0, 0, 2.238))).z + 0.005 * math.sin(2 * PI * 2 * fr)
        anel2.rotation_quaternion = Quaternion(Z, -2 * PI * 3 * fr)
        lz.data.energy = 1.5 + 1.0 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr))
        for o, c in ((anel, 'rotation_quaternion'), (anel, 'scale'), (anel, 'location'), (anel2, 'rotation_quaternion')):
            chave(o, c, q)
        lz.data.keyframe_insert('energy', frame=q)
    ANIM.append(anima_anel)
    if faiscas_on:
        tl = P.M.inverted() @ topos[1]
        base_f = Vector((ISO_X[1], Y_ARM, ZC + 0.05))
        arcs = []
        for v in range(3):
            a0 = tl + Vector((0.0, 0.0, -0.01))
            b0 = Vector((ISO_X[1] + random.uniform(-0.02, 0.02), Y_ARM - 0.01, ZC + 0.006))
            arcs.append(arco_obj(nome + '_arco_iso%d' % v, P.W(a0), P.W(b0), 0.25, 0.0018, 8, 1))
        eventos = []
        for q0 in (10, 42, 74):
            eventos.append((q0, P.W(base_f + Vector((0.02, -0.03, 0))), P.D((0.3, -1, 0.4))))
        faiscas(nome + '_fsc', 18, eventos, 0.9, 0.6, 10)
        fixo = {}
        for q0 in (10, 42, 74):
            for d in range(4):
                fixo[q0 + d] = d % 3

        def anima_iso(q, fr, arcs=arcs, fixo=fixo):
            for i, o in enumerate(arcs):
                o.hide_render = not (q in fixo and fixo[q] == i)
                chave(o, 'hide_render', q)
        ANIM.append(anima_iso)
        li = luz(nome + '_luz_iso', (1.0, 0.65, 0.45), 0.0, P.W(base_f + Vector((0, -0.03, 0.02))), 0.01)

        def anima_luz(q, fr, li=li, fixo=fixo):
            li.data.energy = 6.0 if q in fixo else 0.0
            li.data.keyframe_insert('energy', frame=q)
        ANIM.append(anima_luz)
    return topos, P.W((0, 0, 2.238))


# ================================================================== TORRE SEM FIO
ZP = 0.10           # topo da laje
ZTT = 2.18          # topo da treliça / plataforma
LEG_A = [PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3]


def rl(z):
    return 0.22 + (0.10 - 0.22) * (z - ZP) / (ZTT - ZP)


def perna(k, z):
    a = LEG_A[k % 3]
    return Vector((math.cos(a) * rl(z), math.sin(a) * rl(z), z))


def torre(nome, cx, cy, seed, alvos=()):
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    # --- laje
    bc = P.B('concreto')
    caixa_de(bc, (-0.4, -0.4, 0.0), (0.4, 0.4, ZP))
    for k in range(4):
        rachadura_plana(P.B('fenda'), (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), ZP), Z, 0.22, random.uniform(0, 2 * PI), 7)
    caixa_de(P.B('quebra'), (-0.4, 0.31, ZP - 0.04), (-0.355, 0.4, ZP + 0.0005))
    rachadura_plana(P.B('fenda'), (-0.4, -0.1, ZP - 0.004), (-1, 0, 0), 0.09, -PI / 2, 5)
    rachadura_plana(P.B('fenda'), (0.15, -0.4, ZP - 0.004), (0, -1, 0), 0.09, -PI / 2, 5)
    # --- pernas, sapatas, treliça
    bgl = P.B('galv', True)
    for k in range(3):
        a = LEG_A[k]
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        b0 = perna(k, ZP)
        caixa(P.B('galv'), b0 + Z * 0.007, (0.1, 0.1, 0.014), rot_cols(d, t, Z))
        for sx in (-1, 1):
            for sy in (-1, 1):
                p = b0 + d * sx * 0.035 + t * sy * 0.035 + Z * 0.014
                tubo(P.B('aco'), p - Z * 0.01, p + Z * 0.03, 0.006, 8)
                porca(P.B('aco'), p, Z, 0.011, 0.01)
        for s in (-1, 1):
            caixa(P.B('galv'), b0 + t * s * 0.016 + Z * 0.05, (0.06, 0.006, 0.07), rot_cols(d, t, Z))
        ninho(P, b0 + d * 0.04 + Z * 0.016, d, 0.016, 6, 0)
        tubo(bgl, perna(k, ZP + 0.014), perna(k, ZTT), 0.015, 14)
    niveis = [ZP + 0.14 + i * (ZTT - 0.06 - ZP - 0.14) / 8 for i in range(9)]
    for i, z in enumerate(niveis):
        for k in range(3):
            tubo(P.B('galv'), perna(k, z), perna(k + 1, z), 0.0065, 8)
            cil(P.B('galv'), perna(k, z), 0.019, 0.025, lados=12)          # nó soldado/abraçado
            if i < len(niveis) - 1:
                z2 = niveis[i + 1]
                if i % 2 == 0:
                    tubo(P.B('galv'), perna(k, z), perna(k + 1, z2), 0.0055, 8)
                else:
                    tubo(P.B('galv'), perna(k + 1, z), perna(k, z2), 0.0055, 8)
    for k in range(3):                                                   # ferrugem nos nós baixos
        for i in (0, 1, 3):
            p = perna(k, niveis[i])
            d = Vector((p.x, p.y, 0)).normalized()
            ninho(P, p + d * 0.019, d, 0.012, 4, 0.03)
    # --- colar dos estais e estais com esticadores
    ZE = 1.55
    for k in range(3):
        a = LEG_A[k]
        d = Vector((math.cos(a), math.sin(a), 0))
        pk = perna(k, ZE)
        cil(P.B('aco'), pk, 0.021, 0.04, lados=12)
        olhal = pk + d * 0.03
        caixa(P.B('aco'), pk + d * 0.018, (0.03, 0.008, 0.035), rot_cols(d, Vector((-d.y, d.x, 0)), Z))
        anc = Vector((math.cos(a) * 0.355, math.sin(a) * 0.355, ZP))
        caixa(P.B('aco'), anc + Z * 0.006, (0.05, 0.05, 0.012))
        for sx in (-1, 1):
            porca(P.B('aco'), anc + Vector((-d.y, d.x, 0)) * sx * 0.017 + Z * 0.012, Z, 0.007, 0.007)
        toro(P.B('aco', True), anc + Z * 0.03, 0.012, 0.004, 16, 6, Vector((-d.y, d.x, 0)))
        u = (olhal - (anc + Z * 0.04)).normalized()
        e0 = anc + Z * 0.042
        e1 = e0 + u * 0.03
        e2 = e1 + u * 0.09
        tubo(P.B('aco'), e0, e1, 0.004, 6)
        cil(P.B('ferro', True), e1 + u * 0.045, 0.009, 0.075, u, lados=10)
        caixa(P.B('ferro'), e1 + u * 0.045, (0.02, 0.006, 0.05), rot_cols(Vector((-d.y, d.x, 0)), u.cross(Vector((-d.y, d.x, 0))), u))
        tubo(P.B('aco'), e2, e2 + u * 0.03, 0.004, 6)
        tubo(P.B('cabo_aco'), e2 + u * 0.025, olhal, 0.0028, 6)
        for w in (0.06, 0.1):                                            # grampos do laço do cabo
            caixa(P.B('aco'), e2 + u * w, (0.012, 0.012, 0.01), rot_cols(Vector((-d.y, d.x, 0)), u.cross(Vector((-d.y, d.x, 0))), u))
        ninho(P, e1 + u * 0.01, d, 0.01, 4, 0)
    # --- plataforma
    cil(P.B('grafite'), (0, 0, ZTT + 0.012), 0.165, 0.024, lados=6)
    for k in range(6):
        a = k * PI / 3 + PI / 6
        cil(P.B('aco'), (math.cos(a) * 0.14, math.sin(a) * 0.14, ZTT + 0.026), 0.007, 0.006, lados=6)
    decal(P.B('queimado'), (0.12, -0.04, ZTT + 0.0245), Z, 0.03)
    for k in range(3):                                                   # escorridos de ferrugem na borda
        a = k * 2 * PI / 3 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        escorrido(P.B('escorre'), d * 0.1435 + Z * (ZTT + 0.022), d, 0.02, 0.01)
    # barras de fenolite e primário em espiral
    for k in range(3):
        a = k * 2 * PI / 3 + PI / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(P.B('resina'), d * 0.115 + Z * (ZTT + 0.034), (0.09, 0.016, 0.02), rot_cols(d, Vector((-d.y, d.x, 0)), Z))
    zsp = ZTT + 0.044 + 0.0045
    voltas = 4 + 300 / 360
    pts = []
    n = 160
    for i in range(n + 1):
        t = i / n
        a = 2 * PI * voltas * t + PI / 6
        r = 0.068 + (0.142 - 0.068) * t
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, zsp)))
    varrer(P.B('cobre', True), pts, 0.0045, 10)
    pe_ext = pts[-1]
    pe_int = pts[0]
    for k in range(3):                                                   # chamuscado nas voltas
        decal(P.B('queimado'), pts[40 + k * 37] + Z * 0.0046, Z, 0.006)
    # secundário
    ZS0, ZS1 = ZTT + 0.024, ZTT + 0.38
    cil(P.B('resina', True), (0, 0, (ZS0 + ZS1) / 2), 0.04, ZS1 - ZS0, lados=32)
    cil(P.B('resina', True), (0, 0, ZS0 + 0.006), 0.056, 0.012, lados=32)
    for k in range(3):
        a = k * 2 * PI / 3
        cil(P.B('aco'), (math.cos(a) * 0.05, math.sin(a) * 0.05, ZS0 + 0.014), 0.0045, 0.005, lados=6)
    voltas = 42
    pts = []
    zh0, zh1 = ZS0 + 0.03, ZS1 - 0.025
    for i in range(voltas * 20 + 1):
        t = i / (voltas * 20)
        a = 2 * PI * voltas * t
        pts.append(Vector((math.cos(a) * 0.0423, math.sin(a) * 0.0423, zh0 + (zh1 - zh0) * t)))
    varrer(P.B('cobre', True), pts, 0.0021, 6)
    tubo(P.B('cobre'), pts[0], Vector((0.0423, 0, zh0 - 0.012)) + Vector((0.02, 0, 0)), 0.0021, 6)
    for k in range(4):                                                   # marcas de arco no verniz
        decal(P.B('queimado'), Vector((math.cos(1.0 + k * 1.7) * 0.0447, math.sin(1.0 + k * 1.7) * 0.0447, zh0 + 0.07 * k + 0.05)),
              Vector((math.cos(1.0 + k * 1.7), math.sin(1.0 + k * 1.7), 0)), 0.007, alongar=0.6)
    # toroide
    ZTo = ZS1 + 0.03
    cil(P.B('aluminio', True), (0, 0, ZS1 + 0.012), 0.03, 0.026, lados=24)
    toro(P.B('aluminio', True), (0, 0, ZTo), 0.085, 0.032, 56, 18)
    cil(P.B('aluminio', True), (0, 0, ZTo), 0.07, 0.012, lados=40)
    for k in range(7):                                                   # queimados de arco no toroide
        a = random.uniform(0, 2 * PI)
        b = random.uniform(-0.6, 1.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        nrm = d * math.cos(b) + Z * math.sin(b)
        decal(P.B('queimado' if k % 2 else 'chamusco'), Vector((0, 0, ZTo)) + d * 0.085 + nrm * 0.0325,
              nrm, random.uniform(0.008, 0.018))
    # suporte do cristal (garras de cobre)
    ZK = ZTo + 0.006
    cil(P.B('cobre', True), (0, 0, ZK + 0.012), 0.024, 0.024, lados=20, r2=0.03)
    cil(P.B('cobre', True), (0, 0, ZK + 0.028), 0.031, 0.008, lados=20)
    for k in range(3):
        a = k * 2 * PI / 3 + 0.5
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = bezier(d * 0.028 + Z * (ZK + 0.03), d * 0.05 + Z * (ZK + 0.05), d * 0.042 + Z * (ZK + 0.09), d * 0.032 + Z * (ZK + 0.11), 8)
        varrer(P.B('cobre_velho', True), pts, 0.0045, 8, tampas=(False, True))
        cil(P.B('aco'), d * 0.047 + Z * (ZK + 0.06), 0.004, 0.006, d, lados=6)
    # --- cabos do primário descendo pela perna 2 (330°)
    k2 = 2
    a2 = LEG_A[k2]
    d2 = Vector((math.cos(a2), math.sin(a2), 0))
    t2 = Vector((-d2.y, d2.x, 0))
    ZBAIXO = ZP + 0.24

    def lado_perna(z, off, s):
        return perna(k2, z) + d2 * 0.032 + t2 * s * off

    for s, mat, ponta in ((-1, 'borracha', pe_ext), (1, 'cabo_verm', pe_int)):
        if s == 1:                                                       # tomada da volta interna passa por cima
            ini = [ponta, ponta + Z * 0.04, Vector((ponta.x, ponta.y, zsp + 0.05)).lerp(d2 * 0.17 + Z * (zsp + 0.05), 0.6),
                   d2 * 0.17 + t2 * 0.012 + Z * (zsp + 0.04)]
            ini = bezier(ini[0], ini[1], ini[2], ini[3], 10)
        else:
            ini = bezier(ponta, ponta + (d2 * 0.04), d2 * 0.17 - t2 * 0.012 + Z * (zsp + 0.01), d2 * 0.18 - t2 * 0.012 + Z * (ZTT - 0.02), 8)
        meio = bezier(ini[-1], ini[-1] - Z * 0.06, lado_perna(ZTT - 0.25, 0.012, s) + Z * 0.08, lado_perna(ZTT - 0.25, 0.012, s), 8)[1:]
        desce = [lado_perna(z, 0.012, s) for z in (ZTT - 0.25 - i * 0.2 for i in range(1, 9)) if z > ZBAIXO]
        desce.append(lado_perna(ZBAIXO, 0.012, s))
        varrer(P.B(mat, True), ini + meio + desce, 0.0055, 10)
        if s == -1:
            for (t0, t1) in ((14, 16),):
                pass
    for z in (1.95, 1.72, 1.27, 1.05, 0.8, 0.55):                         # abraçadeiras dos cabos na perna
        c = perna(k2, z)
        chapa_arco(P.B('aco', True), c, Z, 0.016, 0.003, 0.016, 0, 2 * PI, 18)
        caixa(P.B('grafite'), c + d2 * 0.03, (0.012, 0.045, 0.018), rot_cols(d2, t2, Z))
    for z in (1.3, 0.85):                                                # remendo de fita no cabo preto
        varrer(P.B('fita', True), [lado_perna(z - 0.025, 0.012, -1), lado_perna(z + 0.025, 0.012, -1)], 0.0095, 10, (True, True))
    varrer(P.B('fita_prata', True), [lado_perna(0.62, 0.012, 1), lado_perna(0.68, 0.012, 1)], 0.0095, 10, (True, True))
    # --- banco de capacitores (sul)
    caixa_de(P.B('grafite'), (-0.18, -0.36, ZP), (0.18, -0.22, ZP + 0.016))
    for sx in (-1, 1):
        caixa_de(P.B('grafite'), (sx * 0.178 - 0.008, -0.36, ZP), (sx * 0.178 + 0.008, -0.22, ZP + 0.2))
    caixa_de(P.B('galv'), (-0.186, -0.331, ZP + 0.1), (0.186, -0.325, ZP + 0.125))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cil(P.B('aco'), (sx * 0.15, -0.29 + sy * 0.055, ZP + 0.018), 0.008, 0.006, lados=6)
    topos_cap = []
    for i, x in enumerate((-0.12, -0.04, 0.04, 0.12)):
        c = Vector((x, -0.29, ZP + 0.016))
        h = 0.16
        if i == 2:                                                       # estufado, rachado e vazando
            cil(P.B('capacitor', True), c + Z * 0.06, 0.035, 0.12, lados=28)
            cil(P.B('capacitor', True), c + Z * 0.138, 0.0375, 0.036, lados=28, r2=0.03)
            cil(P.B('aluminio', True), c + Z * 0.162, 0.03, 0.016, lados=28, r2=0.018)
            for k in range(8):
                pedra(P.B('crosta_branca'), c + Z * 0.165 + ruido_vec(0.018) * Vector((1, 1, 0.2)), random.uniform(0.004, 0.008), 0.6)
            escorrido(P.B('crosta_branca'), c + Vector((0, -0.036, 0.14)), (0, -1, 0), 0.12, 0.014)
            decal(P.B('queimado'), c + Vector((0.0, -0.0353, 0.1)), (0, -1, 0), 0.016, alongar=0.7)
            decal(P.B('crosta_branca'), c + Vector((0, -0.05, -0.0155 + ZP * 0)) + Z * 0.0, Z, 0.03)
            topo = c + Z * 0.172
        else:
            cil(P.B('capacitor', True), c + Z * h / 2, 0.035, h, lados=28)
            cil(P.B('aluminio', True), c + Z * (h + 0.004), 0.033, 0.008, lados=28)
            topo = c + Z * (h + 0.008)
        for sx in (-1, 1):                                               # terminais
            tp = topo + Vector((sx * 0.014, 0, 0))
            cil(P.B('porcelana', True), tp + Z * 0.012, 0.007, 0.024, lados=12)
            cil(P.B('porcelana', True), tp + Z * 0.01, 0.011, 0.004, lados=12)
            tubo(P.B('latao'), tp + Z * 0.024, tp + Z * 0.036, 0.003, 6)
            porca(P.B('latao'), tp + Z * 0.03, Z, 0.006, 0.005, False)
        topos_cap.append(topo + Z * 0.032)
        serie_plana(P.B('tinta'), c + Vector((0, -0.0355, 0.06)), (0, -1, 0), 0.01, 3, 0.3)
    for i in range(3):                                                   # barramento de cobre entre capacitores
        a = topos_cap[i] + Vector((0.014, 0, 0))
        b = topos_cap[i + 1] + Vector((-0.014, 0, 0))
        caixa(P.B('cobre'), (a + b) / 2, ((b - a).length + 0.012, 0.012, 0.003))
    caixa(P.B('led_v'), Vector((0.17, -0.2195, ZP + 0.17)), (0.006, 0.002, 0.006))
    decal(P.B('queimado'), (0.06, -0.25, ZP + 0.0006), Z, 0.04, alongar=1.4)
    # cabos: capacitores → pé da perna 2 → sobem
    for s, mat in ((-1, 'borracha'), (1, 'cabo_verm')):
        st = topos_cap[3] + Vector((0.014, 0, 0.006)) if s == 1 else topos_cap[0] + Vector((-0.014, 0, 0.006))
        alvo = lado_perna(ZBAIXO, 0.012, s)
        if s == 1:
            pts = bezier(st, st + Z * 0.06, alvo - Z * 0.08 + d2 * 0.04, alvo, 12)
        else:
            via = Vector((-0.02, -0.19, ZP + 0.012))
            pts = bezier(st, st + Z * 0.05, Vector((-0.12, -0.2, ZP + 0.012)), via, 8) + \
                  bezier(via, via + Vector((0.1, 0.0, 0)), alvo + Vector((-0.06, -0.06, -0.12)), alvo, 10)[1:]
        varrer(P.B(mat, True), pts, 0.0055, 10)
    # --- centelhador (nordeste) com arco
    gc = Vector((0.24, 0.2, ZP))
    caixa_de(P.B('resina'), gc + Vector((-0.07, -0.025, 0)), gc + Vector((0.07, 0.025, 0.02)))
    bolas = []
    for sx in (-1, 1):
        pp = gc + Vector((sx * 0.045, 0, 0.02))
        cil(P.B('porcelana', True), pp + Z * 0.04, 0.009, 0.08, lados=14)
        for k in range(3):
            cil(P.B('porcelana', True), pp + Z * (0.02 + k * 0.022), 0.016, 0.004, lados=14, r2=0.01)
        tubo(P.B('latao'), pp + Z * 0.08, pp + Z * 0.092, 0.004, 8)
        b = pp + Z * 0.092 + Vector((-sx * 0.03, 0, 0))
        tubo(P.B('latao'), pp + Z * 0.092, b, 0.004, 8)
        bm_b = P.B('latao', True)
        bmesh.ops.create_uvsphere(bm_b, u_segments=16, v_segments=10, radius=0.012, matrix=Matrix.Translation(b))
        bolas.append(b)
        for k in range(2):
            cil(P.B('aco'), gc + Vector((sx * 0.06, (k - 0.5) * 0.03, 0.022)), 0.005, 0.004, lados=6)
    decal(P.B('queimado'), gc + Vector((0, 0, 0.0206)), Z, 0.022)
    decal(P.B('queimado'), gc + Vector((0, 0.04, -ZP + ZP + 0.0006)), Z, 0.035)
    pts = bezier(gc + Vector((-0.045, 0.0, 0.025)), gc + Vector((-0.1, -0.05, 0.012)), Vector((0.03, 0.0, ZP + 0.01)),
                 Vector((0.0, -0.19, ZP + 0.01)), 12)
    pts += bezier(pts[-1], pts[-1] + Vector((0, -0.03, 0)), topos_cap[1] + Vector((0.014, 0.06, -0.02)), topos_cap[1] + Vector((0.014, 0, 0.006)), 8)[1:]
    varrer(P.B('borracha', True), pts, 0.0045, 8)
    pts = bezier(gc + Vector((0.045, 0.0, 0.025)), gc + Vector((0.09, -0.04, 0.012)), Vector((0.2, 0.08, ZP + 0.008)),
                 Vector((0.08, -0.05, ZP + 0.008)), 10)
    pts += bezier(pts[-1], pts[-1] + Vector((-0.03, -0.05, 0)), topos_cap[3] + Vector((-0.014, 0.07, -0.03)),
                  topos_cap[3] + Vector((-0.014, 0, 0.006)), 10)[1:]
    varrer(P.B('cabo_verm', True), pts, 0.0045, 8)
    # --- caixa de entrada (oeste) com eletroduto vindo do chão
    cx0 = Vector((-0.33, 0.05, ZP))
    caixa_de(P.B('grafite'), cx0 + Vector((-0.04, -0.07, 0)), cx0 + Vector((0.04, 0.07, 0.17)))
    caixa_de(P.B('amarelo'), cx0 + Vector((0.04, -0.072, -0.002)), cx0 + Vector((0.046, 0.072, 0.172)))
    for sy in (-1, 1):
        for sz in (0.012, 0.158):
            cil(P.B('aco'), cx0 + Vector((0.047, sy * 0.062, sz)), 0.005, 0.004, Vector((1, 0, 0)), lados=6)
    serie_plana(P.B('tinta'), cx0 + Vector((0.0467, 0, 0.12)), (1, 0, 0), 0.012, 5)
    caixa(P.B('listras'), cx0 + Vector((0.0465, 0, 0.04)), (0.002, 0.12, 0.03))
    caixa(P.B('led_a'), cx0 + Vector((0.047, 0.045, 0.145)), (0.002, 0.006, 0.006))
    ninho(P, cx0 + Vector((0.046, -0.06, 0.03)), Vector((1, 0, 0)), 0.012, 5, 0.03)
    pts = [Vector((-0.47, 0.05, -0.05)), Vector((-0.47, 0.05, 0.07))]
    pts += [Vector((-0.47 + 0.05 * (1 - math.cos(a)), 0.05, 0.07 + 0.05 * math.sin(a))) for a in (PI / 2 * i / 8 for i in range(1, 9))]
    pts += [Vector((-0.37, 0.05, 0.12))]
    varrer(P.B('galv', True), pts, 0.016, 14)
    porca(P.B('aco'), Vector((-0.37, 0.05, 0.12)), Vector((-1, 0, 0)), 0.022, 0.012, False)
    pts = bezier(cx0 + Vector((0.04, -0.04, 0.04)), cx0 + Vector((0.12, -0.04, 0.0)), Vector((-0.12, -0.02, ZP + 0.012)),
                 Vector((-0.1, -0.06, ZP + 0.012)), 10)
    pts += bezier(pts[-1], pts[-1] + Vector((0.0, -0.06, 0)), Vector((-0.13, -0.17, ZP + 0.012)), Vector((-0.17, -0.2, ZP + 0.012)), 8)[1:]
    pts += bezier(pts[-1], pts[-1] + Vector((0.01, -0.03, 0)), topos_cap[0] + Vector((-0.06, 0, -0.05)), topos_cap[0] + Vector((-0.014, 0, 0.004)), 8)[1:]
    varrer(P.B('borracha', True), pts, 0.006, 10)
    # --- aterramento: fita trançada da sapata da perna 0 até a haste
    b0 = perna(0, ZP)
    pts = [b0 + Vector((0.05, 0.0, 0.016)), Vector((0.1, 0.32, ZP + 0.004)), Vector((0.38, 0.34, ZP + 0.004)),
           Vector((0.402, 0.34, ZP - 0.01)), Vector((0.41, 0.34, 0.03)), Vector((0.45, 0.34, 0.035))]
    for a, b in zip(pts, pts[1:]):
        u = (b - a).normalized()
        s = u.cross(Z)
        if s.length < 1e-3:
            s = Vector((0, 1, 0))
        s.normalize()
        caixa(P.B('cobre_velho'), (a + b) / 2, ((b - a).length + 0.005, 0.018, 0.003), rot_cols(u, s, u.cross(s).normalized()))
    cil(P.B('cobre_velho', True), (0.45, 0.34, 0.02), 0.009, 0.07, lados=12)
    caixa(P.B('latao'), (0.45, 0.34, 0.045), (0.028, 0.026, 0.02))
    decal(P.B('zinabre'), Vector((0.24, 0.335, ZP + 0.0058)), Z, 0.012, alongar=1.5)
    # brita e lama em volta da laje
    for k in range(55):
        a = random.uniform(0, 2 * PI)
        rr = random.uniform(0.43, 0.66)
        x_, y_ = math.cos(a) * rr, math.sin(a) * rr
        if max(abs(x_), abs(y_)) < 0.425 or (abs(x_ + 0.47) < 0.04 and abs(y_ - 0.05) < 0.04) or (abs(x_ - 0.45) < 0.03 and abs(y_ - 0.34) < 0.03):
            continue
        pedra(P.B('brita'), (x_, y_, 0.0), random.uniform(0.008, 0.022), 0.5)
    for k in range(8):
        decal(P.B('lama'), (random.uniform(-0.38, 0.38), -0.401, random.uniform(0.02, 0.06)), (0, -1, 0), random.uniform(0.02, 0.04))
    bm = bmesh.new()
    mancha(bm, (cx, cy), 0.62, 0.0012)
    obj(nome + '_halo', bm, 'halo')
    P.fim()
    # --- cristal (parte `cristal`)
    zc0 = ZK + 0.034
    bm = bmesh.new()
    cil(bm, (0, 0, 0.095), 0.034, 0.19, lados=6)
    cil(bm, (0, 0, 0.19 + 0.035), 0.034, 0.07, lados=6, r2=0.002)
    for k, (a, tl, h, r) in enumerate(((1.55, 0.45, 0.09, 0.014), (3.64, 0.55, 0.07, 0.011), (5.74, 0.35, 0.06, 0.01))):
        d = Vector((math.cos(a), math.sin(a), 0))
        ax = (d * math.sin(tl) + Z * math.cos(tl)).normalized()
        c = d * 0.03 + ax * h / 2 + Z * 0.0
        cil(bm, c, r, h, ax, lados=6)
        cil(bm, c + ax * (h / 2 + 0.012), r, 0.024, ax, lados=6, r2=0.001)
    cris = obj(nome + '_cristal', bm, 'cristal')
    cris.location = P.W((0, 0, zc0))
    lc = luz(nome + '_luz_cristal', (0.55, 0.2, 1.0), 10.0, P.W((0.07, -0.07, zc0 + 0.3)), 0.04)
    lt = luz(nome + '_luz_arcos', (0.7, 0.55, 1.0), 0.0, P.W((0, 0, ZTo + 0.06)), 0.05)
    # --- arcos do toroide e do cristal para o ar
    arcs = []
    for v in range(10):
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        ini = Vector((0, 0, ZTo)) + d * 0.117 + Z * random.uniform(-0.01, 0.02)
        fim_ = ini + (d * random.uniform(0.6, 1.0) + Z * random.uniform(-0.25, 0.7)).normalized() * random.uniform(0.22, 0.42)
        arcs.append(arco_obj(nome + '_arco%d' % v, P.W(ini), P.W(fim_), 0.13, 0.0034, 10, 3))
    arcs_c = []
    topo_c = Vector((0, 0, zc0 + 0.26))
    for v in range(4):
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        fim_ = topo_c + (d * random.uniform(0.3, 0.8) + Z).normalized() * random.uniform(0.14, 0.26)
        arcs_c.append(arco_obj(nome + '_arco_cr%d' % v, P.W(topo_c), P.W(fim_), 0.15, 0.0026, 8, 2))
    arcs_alvo = []
    for i, alvo in enumerate(alvos):
        grupo = []
        for v in range(3):
            grupo.append(arco_obj(nome + '_arco_alvo%d_%d' % (i, v), P.W(topo_c - Z * 0.03), Vector(alvo), 0.05, 0.005, 26, 4))
        arcs_alvo.append(grupo)
    # centelhador: arco entre as bolas
    arcs_g = [arco_obj(nome + '_arco_gap%d' % v, P.W(bolas[0] + Vector((0.012, 0, 0))), P.W(bolas[1] - Vector((0.012, 0, 0))), 0.5, 0.0025, 5, 0)
              for v in range(2)]
    fase_c = random.random()

    def pulso(fr):
        return 0.5 + 0.5 * math.cos(2 * PI * 2 * (fr - (F_FOTO - 1) / QUADROS))

    def anima_torre(q, fr, arcs=arcs, arcs_c=arcs_c, arcs_alvo=arcs_alvo, arcs_g=arcs_g, cris=cris, lc=lc, lt=lt):
        p = pulso(fr)
        rr = random.Random(q * 977 + seed)
        n_on = 0
        for i, o in enumerate(arcs):
            vis = rr.random() < 0.18 + 0.25 * p
            if q == F_FOTO:
                vis = i in (0, 3, 6, 8)
            o.hide_render = not vis
            n_on += vis
            chave(o, 'hide_render', q)
        for i, o in enumerate(arcs_c):
            vis = rr.random() < 0.25 * p
            if q == F_FOTO:
                vis = i in (1,)
            o.hide_render = not vis
            n_on += vis
            chave(o, 'hide_render', q)
        for grupo in arcs_alvo:
            k = rr.randrange(3)
            vis = rr.random() < 0.35 + 0.5 * p
            if q == F_FOTO:
                vis, k = True, 0
            for i, o in enumerate(grupo):
                o.hide_render = not (vis and i == k)
                chave(o, 'hide_render', q)
        for i, o in enumerate(arcs_g):
            o.hide_render = not ((q % 5) in (0, 1, 3) and (q // 2) % 2 == i)
            if q == F_FOTO:
                o.hide_render = i != 0
            chave(o, 'hide_render', q)
        CRISTAL_EMIS.default_value = 1.2 + 3.8 * p
        CRISTAL_EMIS.keyframe_insert('default_value', frame=q)
        lc.data.energy = 2.0 + 6.0 * p
        lc.data.keyframe_insert('energy', frame=q)
        lt.data.energy = 3.0 * n_on
        lt.data.keyframe_insert('energy', frame=q)
        cris.rotation_euler = (0, 0, 0.02 * math.sin(2 * PI * fr))
        chave(cris, 'rotation_euler', q)
    ANIM.append(anima_torre)
    ev = [(q0, P.W(gc + Vector((0, 0, 0.115))), Vector((0, 0, 1))) for q0 in (4, 30, 55, 80)]
    faiscas(nome + '_fsc_gap', 14, ev, 0.6, 0.7, 8, chao=ZP + 0.02)
    return P.W(topo_c)


# ================================================================== MURO
LO = 0.305          # face externa das pedras na parte baixa do pilar
UP = 0.25           # face externa das pedras na parte alta (recuo)
Z_REC = 0.72        # topo da parte baixa
Z_UP = 0.80         # começo da parte alta (entre os dois: pingadeira inclinada)
Z_PIL = 1.38        # topo das pedras do pilar
CANT = 0.32         # face externa das cantoneiras (parte baixa)
PANO_X = 0.085
PANO_EXT = 0.10
Z_PANO = 1.10


def bloco_pedra(bm, c, tam, rot, rug=0.3, lasca=0.45):
    """Pedra rachão: icosfera empurrada para caixa (superelipse), ruído forte, quina arrancada e giro leve."""
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    sem = Vector((random.uniform(0, 50), random.uniform(0, 50), random.uniform(0, 50)))
    k = Vector((random.choice((-1, 1)), random.choice((-1, 1)), random.choice((-1, 1)))).normalized()
    corta = random.random() < lasca
    rot = rot @ Matrix.Rotation(random.uniform(-0.13, 0.13), 3, 'Y')
    for v in res['verts']:
        p = v.co.copy()
        q = Vector([math.copysign(abs(p[i]) ** 0.45, p[i]) for i in range(3)])
        f = 1 - rug * abs(noise.noise(p * 1.4 + sem)) - 0.08 * abs(noise.noise(p * 5 + sem))
        q *= f
        if corta and q.dot(k) > 0.75:
            q -= k * (q.dot(k) - 0.75) * 0.9
        q.y = min(q.y, 0.95) if q.y > 0 else q.y                        # face de fora mais chapada
        v.co = Vector(c) + rot @ Vector((q.x * tam[0] / 2, q.y * tam[1] / 2, q.z * tam[2] / 2))


def pedras_face(P, base_n, h, n, s0, s1, z0, z1, pular=None, dep=0.08, mats_p=('pedra1', 'pedra2', 'pedra3', 'pedra1')):
    """Assenta pedras numa face vertical. base_n(z): distância da face externa; s0/s1 podem ser funções de z."""
    h, n = Vector(h).normalized(), Vector(n).normalized()
    rot = rot_cols(h, n, Z)
    z = z0
    lista = []
    while z < z1 - 0.03:
        hz = min(random.uniform(0.08, 0.16), z1 - z)
        if z1 - (z + hz) < 0.05:
            hz = z1 - z
        zm = z + hz / 2
        a0 = s0(zm) if callable(s0) else s0
        a1 = s1(zm) if callable(s1) else s1
        dist = base_n(zm) if callable(base_n) else base_n
        s = a0 + random.uniform(-0.05, 0.0)
        while s < a1 - 0.03:
            w = random.uniform(0.09, 0.24)
            if a1 - (s + w) < 0.06:
                w = a1 - s
            a, b = max(s, a0), min(s + w, a1)
            if b - a > 0.03 and not (pular and pular(a, b, z, z + hz)):
                gap = 0.013
                sai = random.uniform(-0.006, 0.004)
                c = n * (dist - dep / 2 + sai) + h * ((a + b) / 2) + Z * zm
                bloco_pedra(P.B(random.choice(mats_p), True), c, (b - a - gap, dep, hz - gap), rot)
                lista.append((n * dist + h * ((a + b) / 2) + Z * zm, n, h, b - a, hz))
            s += w
        z += hz
    return lista


def mordida(P, c, n, h, esc=1.0):
    """Mordida de aranha: lasca arrancada (pedra clara), dois furos de presa em V e riscos de garra."""
    c, n, h = Vector(c), Vector(n), Vector(h)
    decal(P.B('quebra_d'), c + n * 0.001, n, 0.035 * esc, 11, 0.6, 1.3)
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


def ext_pilar(z):
    return LO if z < Z_REC + 0.02 else UP


def muro_lado(nome, cx, cy, quartos, seed):
    """Pano do centro até a borda norte (local), girado por quartos (N=0, O=1, S=2, L=3)."""
    random.seed(seed)
    P = Peca(nome, cx, cy, quartos * PI / 2)
    caixa_de(P.B('concreto'), (-0.11, 0.32, 0.0), (0.11, 0.5, 0.05))
    caixa_de(P.B('argamassa'), (-PANO_X, 0.23, 0.05), (PANO_X, 0.5, Z_PANO))
    lst = []
    for sx in (-1, 1):
        lst += pedras_face(P, PANO_EXT, (0, 1, 0), (sx, 0, 0), lambda z: ext_pilar(z) + 0.004, 0.495, 0.05, Z_PANO, dep=0.07)
    caixa_de(P.B('concreto'), (-0.105, UP - 0.01, Z_PANO), (0.105, 0.5, Z_PANO + 0.055))
    rachadura_plana(P.B('fenda'), (0.0, 0.42, Z_PANO + 0.055), Z, 0.08, PI * random.uniform(0.3, 0.7), 4)
    decal(P.B('quebra_d'), (0.105, 0.47, Z_PANO + 0.03), (1, 0, 0), 0.02)
    zc = Z_PANO + 0.055
    for yy in (0.31, 0.46):
        for sx in (-1, 1):
            cil(P.B('aco'), (sx * 0.06, yy, zc + 0.022), 0.008, 0.044, lados=6, r2=0.0008)
    yp = 0.40
    caixa_de(P.B('galv'), (-0.012, yp - 0.012, zc - 0.03), (0.012, yp - 0.009, 1.262))
    caixa_de(P.B('galv'), (-0.012, yp - 0.012, zc - 0.03), (-0.009, yp + 0.012, 1.262))
    ninho(P, (0.0, yp - 0.013, zc + 0.02), Vector((0, -1, 0)), 0.008, 3, 0)
    for zz in (1.2, 1.242):
        arame_farpado(P, (0.0, UP + 0.004, zz), (0.0, 0.5, zz), 0.004)
        cil(P.B('aco'), (0.0, UP + 0.004, zz), 0.006, 0.012, Vector((0, 1, 0)), lados=8)
    sx = random.choice((-1, 1))
    zr = random.uniform(0.3, 0.55)
    caixa_de(P.B('oxido' if seed % 2 else 'galv'), (sx * 0.112 - 0.003, 0.34, zr), (sx * 0.112 + 0.003, 0.49, zr + 0.22))
    for yy in (0.355, 0.475):
        for zz in (zr + 0.018, zr + 0.202):
            cil(P.B('aco'), (sx * 0.118, yy, zz), 0.008, 0.006, Vector((sx, 0, 0)), lados=6)
    ninho(P, (sx * 0.1155, 0.475, zr + 0.19), Vector((sx, 0, 0)), 0.012, 5, 0.1)
    acido(P, (sx * 0.1152, 0.41, zr + 0.13), Vector((sx, 0, 0)), 0.03, 2)
    random.shuffle(lst)
    feitas = 0
    for (c, n, h, w, hz) in lst:
        if 0.25 < c.z < 0.95 and n.x * sx < 0 and feitas < 1:
            mordida(P, c + n * 0.004, n, h, 0.8)
            feitas += 1
    for (c, n, h, w, hz) in lst[3:5]:
        acido(P, c + Z * 0.02 + n * 0.004, n, 0.028, 2)
    rachadura_plana(P.B('fenda'), (-sx * 0.107, 0.44, 0.95), (-sx, 0, 0), 0.35, -PI / 2, 9, 0.0035)
    for sx2 in (-1, 1):
        musgo(P, (sx2 * 0.1, 0.42, 0.04), 0.07, 7)
        decal(P.B('musgo_d'), (sx2 * 0.108, 0.41, 0.09), (sx2, 0, 0), 0.07, alongar=1.4)
        for k in range(3):
            decal(P.B('lama'), (sx2 * 0.109, random.uniform(0.33, 0.48), random.uniform(0.05, 0.13)), (sx2, 0, 0), random.uniform(0.025, 0.045))
    P.fim()


def tronco(bm, z0, z1, a0, a1):
    """Tronco de pirâmide quadrado (pingadeira entre a parte baixa e a alta)."""
    vs = [bm.verts.new((sx * a, sy * a, z)) for (z, a) in ((z0, a0), (z1, a1)) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs[3::-1])
    bm.faces.new(vs[4:])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))


def muro_centro(nome, cx, cy, lados, seed, sensor_q=2):
    """Pilar 0,64 × 0,64 × 1,50 com recuo: base larga, pingadeira inclinada, parte alta mais estreita.
    lados: quartos onde há pano (N=0, O=1, S=2, L=3)."""
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    caixa_de(P.B('concreto'), (-0.32, -0.32, 0.0), (0.32, 0.32, 0.05))
    caixa_de(P.B('argamassa'), (-LO + 0.015, -LO + 0.015, 0.05), (LO - 0.015, LO - 0.015, Z_REC))
    tronco(P.B('concreto'), Z_REC, Z_UP, 0.318, UP - 0.005)
    caixa_de(P.B('argamassa'), (-UP + 0.015, -UP + 0.015, Z_UP), (UP - 0.015, UP - 0.015, Z_PIL))
    faces = []
    for qd in range(4):
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        n = R @ Vector((0, 1, 0))
        h = R @ Vector((-1, 0, 0))
        tem = qd in lados

        def pular(a, b, z0, z1, tem=tem):
            return tem and a < 0.12 and b > -0.12 and z0 < Z_PANO + 0.06
        lst = pedras_face(P, LO, h, n, -0.27, 0.27, 0.05, Z_REC, pular, dep=0.08)
        lst += pedras_face(P, UP, h, n, -UP + 0.005, UP - 0.005, Z_UP, Z_PIL, pular, dep=0.07)
        faces.append((qd, n, h, tem, lst))
        for k in range(3):                                               # pingadeira gasta: lascas e escorrido
            decal(P.B('quebra_d'), n * ((0.318 + UP) / 2 + 0.003) + h * random.uniform(-0.2, 0.2) + Z * ((Z_REC + Z_UP) / 2 + 0.002),
                  (n * 0.75 + Z * 0.66).normalized(), random.uniform(0.012, 0.025))
    # cantoneiras só na parte baixa, uma delas faltando um pedaço
    falta = random.randrange(4)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        ztop = Z_REC - 0.01 if i != falta else 0.42
        caixa_de(P.B('galv'), (min(sx * CANT, sx * (CANT - 0.006)), min(sy * CANT, sy * (CANT - 0.055)), 0.05),
                 (max(sx * CANT, sx * (CANT - 0.006)), max(sy * CANT, sy * (CANT - 0.055)), ztop))
        caixa_de(P.B('galv'), (min(sx * CANT, sx * (CANT - 0.055)), min(sy * CANT, sy * (CANT - 0.006)), 0.05),
                 (max(sx * CANT, sx * (CANT - 0.055)), max(sy * CANT, sy * (CANT - 0.006)), ztop))
        for zz in (0.17, 0.5):
            if zz < ztop:
                cil(P.B('aco'), (sx * (CANT + 0.003), sy * (CANT - 0.03), zz), 0.008, 0.006, Vector((sx, 0, 0)), lados=6)
                cil(P.B('aco'), (sx * (CANT - 0.03), sy * (CANT + 0.003), zz + 0.05), 0.008, 0.006, Vector((0, sy, 0)), lados=6)
        ninho(P, (sx * (CANT + 0.004), sy * (CANT - 0.03), ztop - 0.01), Vector((sx, 0, 0)), 0.012, 5, min(0.2, ztop - 0.07))
    # uma cinta na parte alta (interrompida onde entra o pano), um trecho trocado
    zc_ = random.uniform(0.98, 1.05)
    eu = UP + 0.007
    for qd, n, h, tem, lst in faces:
        trechos = [(-eu, -0.13), (0.13, eu)] if tem else [(-eu, eu)]
        for a, b in trechos:
            mat = 'oxido' if (qd + seed) % 4 == 0 else 'galv'
            caixa(P.B(mat), n * (eu + 0.003) + h * ((a + b) / 2) + Z * zc_, (b - a, 0.006, 0.045), rot_cols(h, n, Z))
            for sv in (a + 0.035, b - 0.035):
                cil(P.B('aco'), n * (eu + 0.007) + h * sv + Z * zc_, 0.008, 0.005, n, lados=6)
    # capa, chapa de topo, espetos
    caixa_de(P.B('concreto'), (-0.272, -0.272, Z_PIL), (0.272, 0.272, Z_PIL + 0.06))
    caixa_de(P.B('quebra'), (0.23, -0.2725, Z_PIL + 0.02), (0.2725, -0.23, Z_PIL + 0.0605))
    rachadura_plana(P.B('fenda'), (-0.1, -0.272, Z_PIL + 0.055), (0, -1, 0), 0.05, -PI / 2, 3)
    zt = Z_PIL + 0.06
    caixa_de(P.B('aco'), (-0.255, -0.255, zt), (0.255, 0.255, zt + 0.012))
    for sx in (-1, 1):
        for sy in (-1, 1):
            porca(P.B('aco'), (sx * 0.225, sy * 0.225, zt + 0.012), Z, 0.011, 0.008)
    for qd in range(4):
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        for i in range(5):
            p = R @ Vector((-0.17 + i * 0.085, 0.235, zt + 0.012))
            if qd == 1 and i == 1:
                cil(P.B('aco'), p + Vector((0.006, 0, 0.008)), 0.009, 0.016, Vector((0.6, 0, 1)), lados=6)
                continue
            cil(P.B('aco'), p + Z * 0.022, 0.009, 0.044, lados=6, r2=0.0007)
    ninho(P, (0.15, -0.273, zt - 0.006), Vector((0, -1, 0)), 0.015, 5, 0.05)
    # emissor de campo (topo)
    zt2 = zt + 0.012
    cil(P.B('grafite'), (0, 0, zt2 + 0.004), 0.055, 0.008, lados=24)
    for k in range(4):
        toro(P.B('cobre', True), (0, 0, zt2 + 0.012 + k * 0.007), 0.032, 0.0037, 28, 6)
    cil(P.B('violeta'), (0, 0, zt2 + 0.022), 0.024, 0.03, lados=16)
    for k in range(3):
        a = k * 2 * PI / 3
        tubo(P.B('aco'), (math.cos(a) * 0.045, math.sin(a) * 0.045, zt2 + 0.008), (math.cos(a) * 0.045, math.sin(a) * 0.045, zt2 + 0.035), 0.003, 6)
    # sensor (face sem pano, parte alta)
    R = Matrix.Rotation(sensor_q * PI / 2, 3, 'Z')
    ns = R @ Vector((0, 1, 0))
    hs = R @ Vector((-1, 0, 0))
    zs = 1.22
    pc = ns * (UP + 0.008)
    caixa(P.B('grafite'), pc + Z * zs, (0.1, 0.008, 0.12), rot_cols(hs, ns, Z))
    for a in (-1, 1):
        for b in (-1, 1):
            cil(P.B('aco'), pc + ns * 0.005 + hs * a * 0.04 + Z * (zs + b * 0.05), 0.006, 0.005, ns, lados=6)
    caixa(P.B('grafite'), pc + ns * 0.02 + Z * (zs + 0.035), (0.03, 0.035, 0.012), rot_cols(hs, ns, Z))
    serie_plana(P.B('tinta'), pc + ns * 0.0042 + Z * (zs - 0.045), ns, 0.01, 5)
    p0 = pc + ns * 0.006 + hs * 0.04 + Z * (zs + 0.06)
    A = ns * 0.29 + hs * 0.02 + Z * (zt + 0.02)
    pts = bezier(p0, p0 + Z * 0.05, A - Z * 0.07, A, 10)
    pts += bezier(A, A + Z * 0.025 - ns * 0.02, ns * 0.1 + Z * (zt2 + 0.016), ns * 0.056 + Z * (zt2 + 0.006), 10)[1:]
    varrer(P.B('borracha', True), pts, 0.004, 8)
    for zz in (zs + 0.11,):
        caixa(P.B('aco'), ns * (UP + 0.011) + hs * 0.035 + Z * zz, (0.012, 0.006, 0.01), rot_cols(hs, ns, Z))
    # marcas das aranhas (mais embaixo: alcance delas), rachaduras e remendos
    baixas = [(c, n, h) for qd, n_, h_, tem, lst in faces for (c, n, h, w, hz) in lst if c.z < Z_REC]
    altas = [(c, n, h) for qd, n_, h_, tem, lst in faces for (c, n, h, w, hz) in lst if c.z > Z_UP]
    random.shuffle(baixas)
    random.shuffle(altas)
    for (c, n, h) in baixas[:2]:
        if c.z > 0.2:
            mordida(P, c + n * 0.004, n, h)
    for (c, n, h) in baixas[2:4] + altas[:1]:
        acido(P, c + n * 0.004, n, 0.04, 3)
    livre = [f for f in faces if not f[3] and f[0] != sensor_q] or [faces[sensor_q]]
    qd, n, h, tem, lst = livre[0]
    rachadura_plana(P.B('fenda'), n * (UP + 0.007) + h * 0.12 + Z * 1.32, n, 0.45, -PI / 2, 10, 0.004)
    rp_c = n * (LO + 0.0075) + h * -0.12 + Z * 0.42                     # remendo de argamassa com chapa
    decal(P.B('concreto_novo'), rp_c, n, 0.08, 12, 0.3, 1.2)
    caixa(P.B('oxido'), rp_c + n * 0.003 + h * 0.01, (0.1, 0.005, 0.07), rot_cols(h, n, Z))
    for a in (-1, 1):
        cil(P.B('aco'), rp_c + n * 0.007 + h * (0.01 + a * 0.038), 0.007, 0.006, n, lados=6)
    escorrido(P.B('escorre'), rp_c + n * 0.006 + h * 0.03 - Z * 0.035, n, 0.12, 0.012)
    # musgo e lama embaixo (mais no lado norte, sombra)
    for qd, n, h, tem, lst in faces:
        k_m = 3 if n.y > 0.5 else 1
        for k in range(k_m):
            sv = random.uniform(-0.22, 0.22)
            musgo(P, n * 0.315 + h * sv + Z * 0.04, 0.06, 7)
            decal(P.B('musgo_d'), n * (LO + 0.006) + h * sv + Z * 0.1, n, 0.07, alongar=1.5)
        for k in range(3):
            decal(P.B('lama'), n * (LO + 0.006) + h * random.uniform(-0.25, 0.25) + Z * random.uniform(0.07, 0.15), n, random.uniform(0.03, 0.05))
    P.fim()
    # animados: anel do emissor e cabeça do sensor
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 0.05, 0.0035, 36, 8)
    anel = suavizar(obj(nome + '_anel', bm, 'violeta'))
    z_an = P.W((0, 0, zt2 + 0.043)).z
    anel.location = P.W((0, 0, zt2 + 0.043))
    anel.rotation_mode = 'QUATERNION'
    piv = bpy.data.objects.new(nome + '_sensor_piv', None)
    sc.collection.objects.link(piv)
    piv.location = P.W(pc + ns * 0.02 + Z * (zs + 0.035 - 0.006))
    bm = bmesh.new()
    cil(bm, (0, 0, -0.022), 0.022, 0.044, lados=20)
    cil(bm, (0, 0.024, -0.024), 0.014, 0.012, Vector((0, 1, 0)), lados=20)
    suavizar(obj(nome + '_sensor', bm, 'grafite', piv))
    bm = bmesh.new()
    cil(bm, (0, 0.031, -0.024), 0.011, 0.003, Vector((0, 1, 0)), lados=20)
    obj(nome + '_lente', bm, 'vidro_escuro', piv)
    bm = bmesh.new()
    cil(bm, (0, 0.0335, -0.024), 0.004, 0.002, Vector((0, 1, 0)), lados=12)
    obj(nome + '_olho', bm, 'led_r', piv)
    piv.rotation_mode = 'XYZ'
    yaw0 = math.atan2(ns.y, ns.x) - PI / 2
    lz = luz(nome + '_luz_emissor', (0.6, 0.2, 1.0), 1.5, P.W((0, 0, zt2 + 0.05)), 0.04)
    fse = random.random()

    def anima(q, fr, anel=anel, piv=piv, yaw0=yaw0, lz=lz, fse=fse, z_an=z_an):
        anel.rotation_quaternion = Quaternion(Z, 2 * PI * 2 * fr) @ Quaternion((1, 0, 0), 0.1 * math.sin(2 * PI * (fr + fse)))
        anel.location.z = z_an + 0.004 * math.sin(2 * PI * 2 * (fr + fse))
        piv.rotation_euler = (0, 0, yaw0 + 0.7 * math.sin(2 * PI * (fr + fse)))
        lz.data.energy = 1.0 + 0.8 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr))
        chave(anel, 'rotation_quaternion', q)
        chave(anel, 'location', q)
        chave(piv, 'rotation_euler', q)
        lz.data.keyframe_insert('energy', frame=q)
    ANIM.append(anima)


# ================================================================== máquinas genéricas (rede)
def maquina(nome, cx, cy, lx, ly, h, lado_term, seed, receptor=False):
    """Bloco simples: casco, faixa de perigo, caixa de ligação com 3 buchas no lado indicado (vetor)."""
    random.seed(seed)
    P = Peca(nome, cx, cy, 0)
    caixa_de(P.B('concreto'), (-lx / 2, -ly / 2, 0), (lx / 2, ly / 2, 0.08))
    caixa_de(P.B('maquina'), (-lx / 2 + 0.06, -ly / 2 + 0.06, 0.08), (lx / 2 - 0.06, ly / 2 - 0.06, h))
    caixa_de(P.B('listras'), (-lx / 2 + 0.058, -ly / 2 + 0.058, 0.08), (lx / 2 - 0.058, ly / 2 - 0.058, 0.18))
    caixa_de(P.B('grafite'), (-lx / 2 + 0.04, -ly / 2 + 0.04, h), (lx / 2 - 0.04, ly / 2 - 0.04, h + 0.05))
    for k in range(3):
        caixa_de(P.B('grafite'), (-0.3 + k * 0.22, -0.2, h + 0.05), (-0.16 + k * 0.22, 0.2, h + 0.12))
    for k in range(4):
        sx, sy = random.choice((-1, 1)), random.choice((-1, 1))
        ninho(P, (sx * (lx / 2 - 0.058), sy * random.uniform(0.1, ly / 2 - 0.2), random.uniform(0.3, h - 0.1)), Vector((sx, 0, 0)), 0.02, 6, 0.15)
    d = Vector(lado_term).normalized()
    t = Vector((-d.y, d.x, 0))
    face = d * (lx / 2 - 0.06 if abs(d.x) > 0.5 else ly / 2 - 0.06)
    zt = h - 0.25
    caixa(P.B('grafite'), face + d * 0.05 + Z * zt, (0.1, 0.3, 0.2), rot_cols(d, t, Z))
    serie_plana(P.B('tinta'), face + d * 0.1 + Z * (zt - 0.06), d, 0.02, 5)
    terms = []
    for k in (-1, 0, 1):
        c = face + d * 0.1 + t * k * 0.09 + Z * (zt + 0.1)
        cil(P.B('porcelana', True), c + Z * 0.03, 0.012, 0.06, lados=14)
        for j in range(2):
            cil(P.B('porcelana', True), c + Z * (0.015 + j * 0.022), 0.022, 0.005, lados=16, r2=0.013)
        tubo(P.B('latao'), c + Z * 0.06, c + Z * 0.075, 0.004, 8)
        terms.append(P.W(c + Z * 0.075))
    if receptor:
        cil(P.B('cobre', True), (0.3, 0.3, h + 0.12), 0.012, 0.24, lados=12)
        for k in range(3):
            toro(P.B('cobre', True), (0.3, 0.3, h + 0.08 + k * 0.03), 0.03, 0.005, 20, 6)
        bm = bmesh.new()
        cil(bm, (0.3, 0.3, h + 0.27), 0.022, 0.07, lados=6)
        cil(bm, (0.3, 0.3, h + 0.32), 0.022, 0.03, lados=6, r2=0.001)
        bm.transform(P.M)
        obj(nome + '_cristal_rec', bm, 'cristal')
        decal(P.B('queimado'), (0.3, 0.3, h + 0.0505), Z, 0.08)
    for k in range(30):
        a = random.uniform(0, 2 * PI)
        pedra(P.B('brita'), (math.cos(a) * (lx / 2 + random.uniform(0.02, 0.2)), math.sin(a) * (ly / 2 + random.uniform(0.02, 0.2)), 0), random.uniform(0.01, 0.025), 0.5)
    P.fim()
    return terms, P.W((0.3, 0.3, h + 0.3))


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


def montar_poste():
    dst = []
    for i, x in enumerate(ISO_X):
        dst.append((i, Vector((x * 1.4, 7.5, 1.95))))
        dst.append((i, Vector((x * 1.2 + 0.4, -7.5, 1.9))))
    poste('poste', 0, 0, 0, dst, 7)


def montar_torre():
    torre('torre', 0, 0, 11)


MURO_O = Vector((0, 0, 0))


def montar_muro():
    pil = [((0, 0), (3,), 2), ((1, 0), (1, 3), 2), ((2, 0), (1, 0), 2), ((2, 1), (2,), 3)]
    for i, ((x, y), lados, sq) in enumerate(pil):
        muro_centro('muro_c%d' % i, x, y, lados, 30 + i, sq)
        for qd in lados:
            muro_lado('muro_l%d_%d' % (i, qd), x, y, qd, 60 + i * 4 + qd)


R0 = Vector((0, 0, 0))


def montar_rede():
    t1, _ = maquina('maq_a', -2.4, 0.5, 2.0, 2.0, 1.15, (1, 0, 0), 101)
    t2, _ = maquina('maq_b', 5.6, 0.6, 2.0, 2.0, 1.35, (-1, 0, 0), 102)
    t3, rec = maquina('maq_c', -1.9, -3.2, 2.0, 2.0, 1.2, (0, 1, 0), 103, receptor=True)
    A = Vector((0.0, 0.5))
    B = Vector((3.0, 0.6))
    ang = PI / 2

    def ins_w(c, i):
        return Matrix.Translation((c.x, c.y, 0)) @ Matrix.Rotation(ang, 4, 'Z') @ isolador_pt(i)
    dA = [(i, t1[i]) for i in range(3)] + [(i, ins_w(B, i)) for i in range(3)]
    dB = [(i, t2[2 - i]) for i in range(3)]
    _, anelB = poste('posteA', A.x, A.y, ang, dA, 201, faiscas_on=False)
    _, anelB = poste('posteB', B.x, B.y, ang, dB, 202, faiscas_on=True)
    torre('torreR', 1.4, -2.6, 203, alvos=(anelB + Vector((0, 0, 0.0)), rec))


def isolador_pt(i):
    return Vector((ISO_X[i], Y_ARM, ZC + 0.119 + 0.0055))


grupo('poste', montar_poste)
grupo('torre', montar_torre)
grupo('muro', montar_muro)
grupo('rede', montar_rede)
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
    'poste': ('poste_0.png', 'poste', (2.7, -3.1, 1.75), (0.03, 0.0, 1.13), 42, 1100, 1400),
    'poste_perto': ('poste_perto.png', 'poste', (1.45, -0.8, 2.3), (0.06, -0.04, 1.8), 30, 1200, 1300),
    'torre': ('torre_sem_fio_0.png', 'torre', (3.0, -3.5, 2.0), (0.0, 0.0, 1.42), 40, 1100, 1400),
    'torre_perto': ('torre_sem_fio_perto.png', 'torre', (0.9, -1.15, 2.85), (0.0, 0.0, 2.52), 30, 1200, 1300),
    'muro': ('muro_0.png', 'muro', (4.4, -3.6, 2.9), (1.15, 0.35, 0.55), 30, 1600, 1000),
    'muro_perto': ('muro_perto.png', 'muro', (1.85, -1.45, 1.35), (1.05, 0.0, 0.85), 32, 1400, 1100),
    'rede': ('rede_energia.png', 'rede', (8.6, -8.6, 5.4), (1.4, -0.7, 0.8), 28, 1600, 1000),
}
if modo in ('foto', 'teste'):
    sc.cycles.samples = 128 if modo == 'foto' else 24
    sc.frame_set(F_FOTO)
    for chave_f, (arq, grp, pos, alvo, lente, rx, ry) in FOTOS.items():
        if so_uma and chave_f != so_uma:
            continue
        if modo == 'teste':
            rx, ry = rx // 2, ry // 2
        foto(arq, grp, pos, alvo, lente, rx, ry)
print('POSTE_MURO ok')
