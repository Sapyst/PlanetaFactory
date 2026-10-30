"""Estudo isolado (fora do jogo): as duas máquinas de clima 3×3 do lote 15, sem portas de item (só energia da rede).

CÚPULA CONTRA RAIOS (`cupula_tempestade`): nenhum raio cai num raio de 30 m.
Torre de treliça amarela sobre quatro pilhas de isoladores de porcelana (a torre é isolada do chão: a descarga não vai
direto para a terra, vai para o banco). No topo, três anéis captores enormes (corona) eriçados de pontas, e no alto o
cristal da IA preso por três garras: é ele que projeta a cúpula. Guarda-chuva: oito varetas abertas do colar do topo,
cada uma com escora (como a de um guarda-chuva) e ponta captora; rede de cabos em três anéis entre as varetas. Quatro
estais com isolador-ovo e esticador até as âncoras dos cantos. Cordoalha de cobre desce pela perna noroeste até a caixa
de descida → barramento → banco de capacitores (oeste, 8 latas, uma trocada, uma rompida e queimada) → centelhador de
esferas (nordeste) → anel de aterramento em volta da laje → seis hastes de terra (quatro na borda, duas no solo) com
caixa de inspeção; marcas de Lichtenberg queimadas no chão. Retificador com aletas (leste) manda a energia para a rede
pelo eletroduto sul. Contador de descargas, sensor da IA, sinalizadores âmbar.
Cúpula de campo de 30 m quase invisível (meridianos que convergem no zênite): o raio bate, a cúpula acende em volta,
a descarga escorre pelo meridiano até o zênite e cai reta no cristal; o centelhador estoura e as hastes faíscam.

REGULADOR CLIMÁTICO (`controle_clima`): escolhe o clima num raio de 80 m.
Pedestal blindado com quatro braços-garra que sustentam o anel estator (bobinado) a 3 m; dentro, o núcleo de cristal
grande flutua entre dois anéis levitando inclinados que giram. Os braços se fecham num cubo no alto com o feixe de
cornetas de micro-ondas e a agulha final; coluna de luz subindo até o buraco. Duas antenas parabólicas (norte) apontadas
para o céu em forquilha motorizada, cornetas no foco e frentes de onda subindo. Dois canhões de calor (leste e oeste)
com aletas, boca em brasa, fuligem e ar quente tremendo. Duas torres de vapor (sul) alimentadas por cano com flange da
caldeira (sul), com válvulas atuadas, manômetros, bomba e entrada de água pela borda sul. Armário de comando (norte) e
feixes de cabo em eletrocalhas para tudo. Céu: tempestade fechada com um buraco perfeito de 80 m sobre a máquina, sol
entrando pelo furo, cortina de chuva em volta e raios caindo do lado de fora; chão seco dentro, molhado fora.

Animação (laço de 4 s, 96 quadros): cúpula — sinalizadores piscam, cristal pulsa, raio no quadro 40 (bate, escorre, cai
na torre, centelhador estoura), cúpula acende e apaga; regulador — anéis giram, cristal pulsa, frentes de onda sobem,
vapor sobe, antenas corrigem a mira, raios do lado de fora.
Uso: blender -b --python estudo_clima_3x3.py -- foto cupula [0|desvio]
     blender -b --python estudo_clima_3x3.py -- foto regulador [0|ceu]
     blender -b --python estudo_clima_3x3.py -- teste <cupula|regulador> x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(15)

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto', 'cupula']
MODO = ARGS[0]
QUAL = ARGS[1] if len(ARGS) > 1 else 'cupula'

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no
Z = Vector((0, 0, 1))


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B_ = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B_[(j + 1) % nr], B_[j]))


def rot_de(eixo):
    return Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, flange=True, lados=16):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.2:
            for c in (a + u * 0.06, b - u * 0.06):
                tubo(bf, c - u * 0.01, c + u * 0.01, r * 1.55, lados)
                for k in range(6):                                       # parafusos da flange
                    t1 = u.orthogonal().normalized()
                    t2 = u.cross(t1)
                    ang = k * PI / 3
                    pp = c + (t1 * math.cos(ang) + t2 * math.sin(ang)) * r * 1.3
                    tubo(bf, pp - u * 0.016, pp + u * 0.016, r * 0.12, 6)
    for c in pts[1:-1]:
        curva(bm, c, r, lados)


def feixe(bc, ba, pts, lat, n=3, r=0.014, passo=4):
    """Feixe de n cabos lado a lado com abraçadeiras a cada `passo` pontos."""
    pts = [Vector(p) for p in pts]
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 0.6), 12)


def octo(bm, c, apo, z0, z1):
    R = apo / math.cos(PI / 8)
    vs0 = [bm.verts.new((c.x + R * math.cos(PI / 8 + k * PI / 4), c.y + R * math.sin(PI / 8 + k * PI / 4), z0)) for k in range(8)]
    vs1 = [bm.verts.new((v.co.x, v.co.y, z1)) for v in vs0]
    bm.faces.new(list(reversed(vs0)))
    bm.faces.new(vs1)
    for k in range(8):
        bm.faces.new((vs0[k], vs0[(k + 1) % 8], vs1[(k + 1) % 8], vs1[k]))


def rot_face(n):
    n = Vector((n.x, n.y, 0)).normalized()
    return Matrix((Vector((n.y, -n.x, 0)), n, Vector((0, 0, 1)))).transposed()


def torno(bm, c, perfil, lados=24, M3=Matrix.Identity(3), tampas=True):
    """Sólido de revolução no eixo z local (girado por M3): perfil = [(z, r), ...]."""
    aneis = []
    for z, r in perfil:
        aneis.append([bm.verts.new(Vector(c) + M3 @ Vector((r * math.cos(k * 2 * PI / lados), r * math.sin(k * 2 * PI / lados), z)))
                      for k in range(lados)])
    for A, B_ in zip(aneis, aneis[1:]):
        for k in range(lados):
            bm.faces.new((A[k], A[(k + 1) % lados], B_[(k + 1) % lados], B_[k]))
    if tampas:
        bm.faces.new(list(reversed(aneis[0])))
        bm.faces.new(aneis[-1])


def mancha_em(bm, centro, r, n, alongar=1.0):
    n = Vector(n).normalized()
    rot = n.to_track_quat('Z', 'Y').to_matrix()
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=14, radius=r)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.35 * math.sin(a * 3 + random.random()) + 0.15 * random.random()
        loc = Vector((v.co.x * f, v.co.y * f * alongar, 0))
        v.co = Vector(centro) + rot @ loc + n * 0.0015


def escorrido(bm, topo, n, comp, larg=0.012):
    """Escorrido vertical (ferrugem/óleo/fuligem) colado numa face de normal n, afinando para baixo."""
    n = Vector(n).normalized()
    t = Z.cross(n).normalized()
    p = Vector(topo) + n * 0.0015
    passos = 6
    for i in range(passos):
        z0, z1 = comp * i / passos, comp * (i + 1) / passos
        w0, w1 = larg * (1 - 0.7 * i / passos), larg * (1 - 0.7 * (i + 1) / passos)
        dx = random.uniform(-0.004, 0.004)
        vs = [bm.verts.new(p + t * (-w0) - Z * z0), bm.verts.new(p + t * w0 - Z * z0),
              bm.verts.new(p + t * (w1 + dx) - Z * z1), bm.verts.new(p + t * (-w1 + dx) - Z * z1)]
        bm.faces.new(vs)


def parafusos_em(bm, pts, n, r=0.008):
    for p in pts:
        cil(bm, Vector(p) + Vector(n) * 0.004, r, 0.008, Vector(n), lados=6)


def chapa(bmc, bmp, c, larg, alt, n, esp=0.012, giro=0.0):
    """Remendo aparafusado numa face de normal horizontal n."""
    R = rot_face(Vector(n)) @ Matrix.Rotation(giro, 3, 'Y')
    c = Vector(c)
    caixa(bmc, c + Vector(n) * esp / 2, (larg, esp, alt), R)
    pts = [c + Vector(n) * esp + R @ Vector((sx * larg * 0.4, 0, sz * alt * 0.38)) for sx in (-1, 1) for sz in (-1, 1)]
    parafusos_em(bmp, pts, n)


def isolador(bm, a, b, r, saias=5):
    """Pilha de isolador de porcelana de a até b: núcleo + saias."""
    a, b = Vector(a), Vector(b)
    u = (b - a).normalized()
    L = (b - a).length
    tubo(bm, a, b, r * 0.55, 16)
    for i in range(saias):
        c = a + u * (L * (i + 0.6) / (saias + 0.2))
        cil(bm, c, r, L / saias * 0.28, u, lados=20, r2=r * 0.7)


def catenaria(a, b, flecha, n=12):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Z * flecha * 4 * (i / n) * (1 - i / n) for i in range(n + 1)]


def linha(bm, pts, r, lados=6):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        u = (b - a).normalized()
        tubo(bm, a - u * r * 0.5, b + u * r * 0.5, r, lados)


def fixar_poligonos(bm):
    """Recalcula as normais (a malha juntou peças de origens diferentes)."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


BMS = {}


def B(nome, mat, liso=False):
    k = (nome, mat, liso)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def descarregar():
    for (nome, mat, liso), bm in BMS.items():
        o = obj(nome, bm, mat)
        if liso:
            suavizar(o)
    BMS.clear()


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def brilho_mat(nome, cor, forca, alfa):
    """Emissão meio transparente (halo de descarga, frente de onda)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission', name='em')
    em.inputs['Color'].default_value = (*cor, 1)
    em.inputs['Strength'].default_value = forca
    lw = no(nt, 'ShaderNodeLayerWeight', **{'Blend': 0.5})
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(lw.outputs['Facing'], f.inputs[0])
    f.inputs[1].default_value = alfa
    inv = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    inv.inputs[0].default_value = alfa
    nt.links.new(f.outputs[0], inv.inputs[1])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(inv.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def cristal_mat(nome, cor_base, cor_em, forca):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor_base, 1)
    b.inputs['Roughness'].default_value = 0.15
    b.inputs['Transmission Weight'].default_value = 0.45
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (*cor_em, 1)
    b.inputs['Emission Strength'].default_value = forca
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 18.0, 'Detail': 6.0})
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def vidro_mat(nome, cor, forca=0.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = 0.7
    b.inputs['IOR'].default_value = 1.45
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def agua_mat():
    m = bpy.data.materials.new('Poça')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.03, 0.032, 0.03, 1)
    b.inputs['Roughness'].default_value = 0.03
    b.inputs['Specular IOR Level'].default_value = 0.6
    return m


def feixe_vol_mat(nome, cor, dens, emis, escuro=(0.05, 0.02, 0.1)):
    """Volume que brilha mais no eixo do cilindro unitário (coluna de energia, ar quente)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (*escuro, 1)
    vol.inputs['Emission Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    xy = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], xy.inputs['X'])
    nt.links.new(sep.outputs['Y'], xy.inputs['Y'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(xy.outputs[0], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.1})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    ponta = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.25})    # some no fim do cilindro (z 0 → 1)
    nt.links.new(sep.outputs['Z'], ponta.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', name='ru', noise_dimensions='4D', **{'Scale': 4.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    mul2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    nt.links.new(ponta.outputs['Result'], mul2.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = dens
    nt.links.new(mul2.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca')
    e.inputs[1].default_value = emis
    nt.links.new(mul2.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def fumaca_grad_mat(nome, dens, z0, z1, escura=(0.012, 0.011, 0.011), clara=(0.42, 0.42, 0.43)):
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*escura, 1)
    mix.inputs[7].default_value = (*clara, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


def nuvem_mat(nome, dens, z0, z1, furo=0.0, escala=0.011, base_cor=(0.05, 0.052, 0.06), topo_cor=(0.5, 0.52, 0.56)):
    """Camada de nuvem de tempestade em coordenadas do mundo (objeto na origem, escala 1): base escura e encaroçada,
    topo mais claro; com `furo` > 0 abre um buraco perfeito de raio `furo` no eixo z com uma parede adensada."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Anisotropy'].default_value = 0.25
    L(vol.outputs[0], out.inputs['Volume'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    L(geo.outputs['Position'], sep.inputs[0])
    esc = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY')
    esc.inputs[1].default_value = (escala, escala, escala * 2.2)
    L(geo.outputs['Position'], esc.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', name='ru', noise_dimensions='4D', **{'Scale': 1.0, 'Detail': 9.0, 'Roughness': 0.62})
    L(esc.outputs[0], ru.inputs['Vector'])
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z1})
    L(sep.outputs['Z'], t.inputs['Value'])
    # limiar sobe perto da base (base encaroçada) e do topo
    lim = no(nt, 'ShaderNodeFloatCurve')
    cv = lim.mapping.curves[0]
    cv.points[0].location = (0.0, 0.66)
    cv.points[1].location = (1.0, 0.7)
    cv.points.new(0.12, 0.47)
    cv.points.new(0.75, 0.45)
    lim.mapping.update()
    L(t.outputs['Result'], lim.inputs['Value'])
    sub = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    L(ru.outputs['Fac'], sub.inputs[0])
    L(lim.outputs[0], sub.inputs[1])
    dd = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    L(sub.outputs[0], dd.inputs[0])
    dd.inputs[1].default_value = 12.0
    dens_n = dd.outputs[0]
    if furo > 0:
        cxy = no(nt, 'ShaderNodeCombineXYZ')
        L(sep.outputs['X'], cxy.inputs['X'])
        L(sep.outputs['Y'], cxy.inputs['Y'])
        rr = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
        L(cxy.outputs[0], rr.inputs[0])
        borda = no(nt, 'ShaderNodeMapRange', **{'From Min': furo, 'From Max': furo + 1.5})      # corte perfeito
        L(rr.outputs['Value'], borda.inputs['Value'])
        parede = no(nt, 'ShaderNodeMapRange', **{'From Min': furo, 'From Max': furo + 30, 'To Min': 2.6, 'To Max': 1.0})
        L(rr.outputs['Value'], parede.inputs['Value'])
        m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        L(dens_n, m1.inputs[0])
        L(borda.outputs['Result'], m1.inputs[1])
        m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
        L(m1.outputs[0], m2.inputs[0])
        L(parede.outputs['Result'], m2.inputs[1])
        dens_n = m2.outputs[0]
    fd = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    L(dens_n, fd.inputs[0])
    fd.inputs[1].default_value = dens
    L(fd.outputs[0], vol.inputs['Density'])
    # cor: base escura → topo claro, com manchas
    tc2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 1.0})
    L(t.outputs['Result'], tc2.inputs['Value'])
    ss = no(nt, 'ShaderNodeMath', operation='POWER')
    L(tc2.outputs['Result'], ss.inputs[0])
    ss.inputs[1].default_value = 1.6
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*base_cor, 1)
    mix.inputs[7].default_value = (*topo_cor, 1)
    L(ss.outputs[0], mix.inputs[0])
    L(mix.outputs[2], vol.inputs['Color'])
    return m


def cortina_mat(nome, dens):
    """Cortina de chuva: volume cinza fino em riscos verticais, mais denso embaixo da nuvem."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.2, 0.21, 0.23, 1)
    L(vol.outputs[0], out.inputs['Volume'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    esc = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY')
    esc.inputs[1].default_value = (0.06, 0.06, 0.004)
    L(geo.outputs['Position'], esc.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 4.0})
    L(esc.outputs[0], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.7, 'To Min': 0.15, 'To Max': 1.0})
    L(ru.outputs['Fac'], mr.inputs['Value'])
    fd = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    L(mr.outputs['Result'], fd.inputs[0])
    fd.inputs[1].default_value = dens
    L(fd.outputs[0], vol.inputs['Density'])
    return m


def chuva_mat():
    m = bpy.data.materials.new('Chuva')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.75, 0.78, 0.82, 1)
    ag.inputs['Roughness'].default_value = 0.15
    ag.inputs['Transmission Weight'].default_value = 0.5
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.8
    nt.links.new(ag.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def terra_mat(nome, seco_r=0.0):
    """Chão de terra: molhado e escuro (lâmina d'água nas baixadas); com seco_r > 0, seco e claro dentro do raio."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    L(b.outputs[0], out.inputs['Surface'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.35, 'Detail': 8.0, 'Roughness': 0.6})
    L(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 6.0})
    L(geo.outputs['Position'], fino.inputs['Vector'])
    poca = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.6, 'From Max': 0.66})
    L(ru.outputs['Fac'], poca.inputs['Value'])
    cor_m = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor_m.inputs[6].default_value = (0.05, 0.045, 0.04, 1)
    cor_m.inputs[7].default_value = (0.1, 0.088, 0.075, 1)
    L(fino.outputs['Fac'], cor_m.inputs[0])
    rough_m = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.6, 'To Max': 0.04})
    L(poca.outputs['Result'], rough_m.inputs['Value'])
    cor_s = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor_s.inputs[6].default_value = (0.13, 0.11, 0.09, 1)
    cor_s.inputs[7].default_value = (0.2, 0.17, 0.135, 1)
    L(fino.outputs['Fac'], cor_s.inputs[0])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    L(fino.outputs['Fac'], bump.inputs['Height'])
    L(bump.outputs['Normal'], b.inputs['Normal'])
    if seco_r > 0:
        sep = no(nt, 'ShaderNodeSeparateXYZ')
        L(geo.outputs['Position'], sep.inputs[0])
        cxy = no(nt, 'ShaderNodeCombineXYZ')
        L(sep.outputs['X'], cxy.inputs['X'])
        L(sep.outputs['Y'], cxy.inputs['Y'])
        rr = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
        L(cxy.outputs[0], rr.inputs[0])
        k = no(nt, 'ShaderNodeMapRange', **{'From Min': seco_r - 6, 'From Max': seco_r + 4})
        L(rr.outputs['Value'], k.inputs['Value'])
        cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
        L(k.outputs['Result'], cor.inputs[0])
        L(cor_s.outputs[2], cor.inputs[6])
        L(cor_m.outputs[2], cor.inputs[7])
        L(cor.outputs[2], b.inputs['Base Color'])
        rgh = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        L(k.outputs['Result'], rgh.inputs[0])
        rgh.inputs[2].default_value = 0.92
        L(rough_m.outputs['Result'], rgh.inputs[3])
        L(rgh.outputs[0], b.inputs['Roughness'])
    else:
        L(cor_m.outputs[2], b.inputs['Base Color'])
        L(rough_m.outputs['Result'], b.inputs['Roughness'])
    return m


VIOLETA = (0.55, 0.22, 1.0)
AMBAR = (1.0, 0.42, 0.04)
RAIO_COR = (0.82, 0.78, 1.0)
R_CUP = 30.0                                        # raio da cúpula contra raios
R_FURO = 80.0                                       # raio do céu limpo do regulador
# ponto onde o raio bate na cúpula (azimute 215°, elevação 42°)
AZ_P, EL_P = math.radians(208), math.radians(40)
P_DIR = Vector((math.cos(EL_P) * math.cos(AZ_P), math.cos(EL_P) * math.sin(AZ_P), math.sin(EL_P)))


def cupula_mat():
    """Campo quase invisível: membrana com fresnel mínimo, meridianos que convergem no zênite e paralelos fracos.
    `fase` (0 → 1) acende em volta de P_DIR e uma onda clara corre pelos meridianos; `flash` acende tudo um pouco."""
    m = bpy.data.materials.new('Cúpula de campo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new

    def mt(op, a, b=None, c=None, clamp=False):
        n = no(nt, 'ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L(x, n.inputs[i])
        return n.outputs[0]

    out = no(nt, 'ShaderNodeOutputMaterial')
    tc = no(nt, 'ShaderNodeTexCoord')
    nrm = no(nt, 'ShaderNodeVectorMath', operation='NORMALIZE')
    L(tc.outputs['Object'], nrm.inputs[0])
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    L(nrm.outputs[0], sep.inputs[0])
    az = mt('ARCTAN2', sep.outputs['Y'], sep.outputs['X'])
    el = mt('ARCSINE', sep.outputs['Z'])
    # meridianos (48) e paralelos (a cada 7,5°)
    mer = mt('SUBTRACT', 1.0, mt('DIVIDE', mt('ABSOLUTE', mt('SINE', mt('MULTIPLY', az, 24.0))),
                                  mt('MAXIMUM', mt('MULTIPLY', mt('COSINE', el), 0.05), 0.004)), clamp=True)
    par = mt('SUBTRACT', 1.0, mt('DIVIDE', mt('ABSOLUTE', mt('SINE', mt('MULTIPLY', el, 24.0))), 0.04), clamp=True)
    linhas = mt('MAXIMUM', mer, mt('MULTIPLY', par, 0.6))
    # distância angular até o ponto do raio
    dot = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    L(nrm.outputs[0], dot.inputs[0])
    dot.inputs[1].default_value = P_DIR
    th = mt('ARCCOSINE', dot.outputs['Value'])
    fase_n = no(nt, 'ShaderNodeValue', name='fase')
    fase_n.outputs[0].default_value = -1.0
    flash_n = no(nt, 'ShaderNodeValue', name='flash')
    flash_n.outputs[0].default_value = 0.0
    fase, flash = fase_n.outputs[0], flash_n.outputs[0]
    viva = mt('MULTIPLY', mt('GREATER_THAN', fase, 0.0), mt('MAXIMUM', mt('SUBTRACT', 1.0, fase), 0.0))
    nucleo = mt('POWER', mt('MAXIMUM', mt('SUBTRACT', 1.0, mt('DIVIDE', th, 0.42)), 0.0), 2.0)
    frente = mt('MAXIMUM', mt('SUBTRACT', 1.0, mt('DIVIDE', mt('ABSOLUTE', mt('SUBTRACT', th, mt('MULTIPLY', fase, 1.6))), 0.09)), 0.0)
    acesa = mt('MULTIPLY', mt('ADD', mt('MULTIPLY', nucleo, 3.0), frente), viva)
    # membrana: fresnel mínimo; linhas: um pouco mais; acesa: forte nas linhas, média na membrana
    lw = no(nt, 'ShaderNodeLayerWeight', **{'Blend': 0.2})
    base = mt('MULTIPLY', lw.outputs['Facing'], 0.05)
    intens = mt('ADD', mt('ADD', base, mt('MULTIPLY', linhas, mt('ADD', 0.025, mt('ADD', mt('MULTIPLY', acesa, 5.0), mt('MULTIPLY', flash, 0.6))))),
                mt('ADD', mt('MULTIPLY', acesa, 0.9), mt('MULTIPLY', flash, 0.12)))
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')                       # violeta, âmbar perto do impacto
    cor.inputs[6].default_value = (*VIOLETA, 1)
    cor.inputs[7].default_value = (0.95, 0.75, 1.0, 1)
    L(mt('MINIMUM', mt('MULTIPLY', nucleo, viva), 1.0), cor.inputs[0])
    L(cor.outputs[2], em.inputs['Color'])
    L(mt('MULTIPLY', intens, 6.0), em.inputs['Strength'])
    mix = no(nt, 'ShaderNodeMixShader')
    L(mt('MINIMUM', mt('MULTIPLY', intens, 0.7), 0.95), mix.inputs[0])
    L(tr.outputs[0], mix.inputs[1])
    L(em.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs['Surface'])
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.95, sujeira=0.95, ferrugem=0.5),
    'zarcao': mats.material('Zarcão', (0.36, 0.08, 0.04), 0, 0.6, desgaste=0.6, sujeira=0.9, ferrugem=0.5),
    'verde_oliva': mats.material('Verde trocado', (0.16, 0.2, 0.1), 0, 0.55, desgaste=0.8, sujeira=0.9, ferrugem=0.4),
    'azul_trocado': mats.material('Azul trocado', (0.07, 0.14, 0.26), 0, 0.5, desgaste=0.85, sujeira=0.9, ferrugem=0.4),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.75, sujeira=0.85),
    'capacitor': mats.material('Capacitor', (0.12, 0.15, 0.2), 0, 0.45, desgaste=0.7, sujeira=0.9, ferrugem=0.3),
    'prato': mats.material('Prato', (0.5, 0.5, 0.47), 0, 0.5, desgaste=0.8, sujeira=1.0, ferrugem=0.6),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'galvanizado': mats.material('Galvanizado', (0.5, 0.51, 0.5), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=0.9),
    'aluminio': mats.material('Alumínio', (0.6, 0.6, 0.6), 1.0, 0.35, pintura=False, sujeira=0.8),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'cobre_velho': mats.material('Cobre oxidado', (0.3, 0.42, 0.33), 0.5, 0.6, pintura=False, sujeira=0.9, ferrugem=0.3),
    'bobina': mats.material('Bobina', (0.78, 0.4, 0.2), 1.0, 0.25, pintura=False, sujeira=0.5),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'porcelana': mats.material('Porcelana', (0.42, 0.19, 0.09), 0, 0.2, pintura=False, sujeira=0.7, desgaste=0.0),
    'porcelana_cinza': mats.material('Porcelana cinza', (0.5, 0.5, 0.48), 0, 0.2, pintura=False, sujeira=0.8, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'mangueira': mats.material('Mangueira', (0.03, 0.03, 0.032), 0, 0.7, pintura=False, sujeira=0.8, desgaste=0.0),
    'isol_verm': mats.material('Isolador vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.5, sujeira=0.8),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'queimado': mats.material('Queimado', (0.04, 0.034, 0.03), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.025, 0.022, 0.02), 0, 0.92, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'crosta': mats.material('Crosta', (0.6, 0.58, 0.48), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'tinta': mats.material('Estêncil', (0.55, 0.53, 0.48), 0, 0.7, desgaste=0.9, sujeira=0.9),
    'pedra': mats.material('Pedra', (0.3, 0.27, 0.23), 0, 0.9, sujeira=0.5, desgaste=0.0),
    'bloco': mats.material('Bloco', (0.5, 0.4, 0.12), 0, 0.5, desgaste=0.8, sujeira=0.9, ferrugem=0.3),
    'bloco_cinza': mats.material('Bloco cinza', (0.25, 0.26, 0.27), 0, 0.55, desgaste=0.7, sujeira=0.9, ferrugem=0.4),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'poca': agua_mat(),
    'visor': vidro_mat('Visor', (0.35, 0.35, 0.3), 0.0),
    'face_mostrador': mats.material('Mostrador', (0.62, 0.6, 0.52), 0, 0.4, pintura=False, sujeira=0.7, desgaste=0.0),
    'brasa': emissivo('Brasa', (1.0, 0.3, 0.04), 9.0, (0.05, 0.02, 0.01)),
    'brasa_forte': emissivo('Brasa forte', (1.0, 0.5, 0.12), 26.0, (0.1, 0.04, 0.01)),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'led_verm': emissivo('Led vermelho', (1.0, 0.05, 0.02), 12.0),
    'sinal': emissivo('Sinalizador', AMBAR, 25.0, (0.4, 0.15, 0.02)),
    'olho': emissivo('Olho do sensor', VIOLETA, 8.0, (0.05, 0.02, 0.1)),
    'faisca': emissivo('Faísca', (1.0, 0.75, 0.4), 60.0),
    'raio': emissivo('Raio', RAIO_COR, 90.0),
    'raio_halo': brilho_mat('Halo do raio', (0.6, 0.45, 1.0), 6.0, 0.35),
    'arco': emissivo('Arco', (0.8, 0.65, 1.0), 40.0),
    'cristal': cristal_mat('Cristal', (0.16, 0.03, 0.5), (0.5, 0.18, 1.0), 3.0),
    'onda': brilho_mat('Frente de onda', VIOLETA, 3.0, 0.4),
    'chuva': chuva_mat(),
    'fumaca': fumaca_grad_mat('Fumaça', 12.0, 0.8, 2.6),
})


# ------------------------------------------------------------------ peças comuns
Z0 = 0.10                                           # topo da laje 3×3


def laje():
    bm = bmesh.new()
    caixa_de(bm, (-1.49, -1.49, 0), (1.49, 1.49, Z0))
    obj('laje', bm, 'concreto')
    bl = B('laje_listras', 'listras')
    for s in (-1, 1):
        caixa_de(bl, (-1.495, s * 1.495 - 0.014, 0.0), (1.495, s * 1.495 + 0.014, Z0 + 0.002))
        caixa_de(bl, (s * 1.495 - 0.014, -1.495, 0.0), (s * 1.495 + 0.014, 1.495, Z0 + 0.002))
    for k in range(10):                                                    # rachaduras e manchas na laje
        p = Vector((random.uniform(-1.3, 1.3), random.uniform(-1.3, 1.3), Z0 + 0.0012))
        a = random.uniform(0, PI)
        pts = [p]
        for i in range(5):
            a += random.uniform(-0.6, 0.6)
            pts.append(pts[-1] + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.05, 0.11))
        for a_, b_ in zip(pts, pts[1:]):
            viga(B('rachaduras', 'escuro'), a_, b_, 0.004)
    for k in range(8):
        mancha(B('laje_po', 'po'), (random.uniform(-1.3, 1.3), random.uniform(-1.3, 1.3)), random.uniform(0.08, 0.2), Z0 + 0.0008)


def poca(c, r):
    mancha(B('pocas', 'poca'), c, r, Z0 + 0.0016)


def lichtenberg(bm, p, ang, comp, larg, prof, z):
    """Figura de Lichtenberg queimada: ramo que se divide e afina."""
    n = max(2, int(comp / 0.07))
    pts = [Vector(p)]
    for i in range(n):
        ang += random.uniform(-0.55, 0.55)
        pts.append(pts[-1] + Vector((math.cos(ang), math.sin(ang), 0)) * 0.07)
        if prof > 0 and random.random() < 0.22:
            lichtenberg(bm, pts[-1], ang + random.choice((-1, 1)) * random.uniform(0.35, 0.9), comp * random.uniform(0.35, 0.6),
                        larg * 0.62, prof - 1, z)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        w = larg * (1 - 0.75 * i / n)
        d = (b - a)
        lat = Vector((-d.y, d.x, 0)).normalized() * w
        vs = [bm.verts.new(Vector((q.x, q.y, z))) for q in (a - lat, a + lat, b + lat * 0.8, b - lat * 0.8)]
        bm.faces.new(vs)


def caminho_raio(a, b, desvio, n, semente=None):
    """Pontos de uma descarga quebrada de a até b."""
    if semente is not None:
        random.seed(semente)
    a, b = Vector(a), Vector(b)
    pts = [a, b]
    d = desvio
    while len(pts) - 1 < n:                                                # deslocamento do ponto médio (fractal)
        novos = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            u = (q - p).normalized()
            t1 = u.orthogonal().normalized()
            t2 = u.cross(t1)
            m = (p + q) / 2 + (t1 * random.uniform(-1, 1) + t2 * random.uniform(-1, 1)) * d
            novos += [m, q]
        pts = novos
        d *= 0.52
    return pts


def descarga(nome, pts, r, ramos=0, compr=0.25, desvio_r=0.3, halo=True):
    """Canal do raio (núcleo branco + halo) com ramificações que afinam; devolve a lista de objetos."""
    bn, bh = bmesh.new(), bmesh.new()

    def poe(pp, rr):
        linha(bn, pp, rr, 6)
        if halo:
            linha(bh, pp, rr * 5, 8)

    poe(pts, r)
    L = sum((b - a).length for a, b in zip(pts, pts[1:]))
    for k in range(ramos):
        i = random.randint(1, len(pts) - 3)
        a = pts[i]
        d = (pts[i + 1] - pts[i - 1]).normalized()
        lado = d.orthogonal().normalized()
        lado.rotate(Matrix.Rotation(random.uniform(0, 2 * PI), 3, d))
        dirr = (d * random.uniform(0.8, 1.2) + lado * random.uniform(0.4, 0.8)).normalized()
        comp = L * compr * random.uniform(0.4, 1.0)
        rp = caminho_raio(a, a + dirr * comp, comp * desvio_r * 0.5, 16)
        poe(rp, r * 0.45)
        if random.random() < 0.5:                                          # sub-ramo
            j = random.randint(1, len(rp) - 2)
            d2 = (dirr + lado * random.uniform(-0.8, 0.8)).normalized()
            rp2 = caminho_raio(rp[j], rp[j] + d2 * comp * 0.45, comp * 0.08, 8)
            poe(rp2, r * 0.25)
    obs = [obj(nome, bn, 'raio')]
    obs[0].visible_shadow = False
    obs[0].visible_diffuse = False                                         # a luz da descarga vem das lâmpadas pontuais
    if halo:
        h = obj(nome + '_halo', bh, 'raio_halo')
        h.visible_shadow = False
        h.visible_diffuse = False
        obs.append(h)
    return obs


def chuva(centro, tam, n, comp=0.45):
    """Riscos de chuva numa caixa (centro, tam); devolve o objeto (cai no laço)."""
    bm = bmesh.new()
    cx, cy, cz = centro
    for k in range(n):
        p = Vector((cx + random.uniform(-tam[0], tam[0]) / 2, cy + random.uniform(-tam[1], tam[1]) / 2,
                    cz + random.uniform(-tam[2], tam[2]) / 2))
        d = Vector((0.08, 0.03, -1)).normalized() * comp * random.uniform(0.7, 1.3)
        tubo(bm, p, p + d, 0.0035, 3)
    o = obj('chuva', bm, 'chuva')
    o.visible_shadow = False
    return o


def keyall(o, *cs, q):
    for c in cs:
        o.keyframe_insert(c, frame=q)


def ocultar(o, h, q):
    o.hide_render = o.hide_viewport = h
    keyall(o, 'hide_render', 'hide_viewport', q=q)


def chave_valor(sock, v, q):
    sock.default_value = v
    sock.keyframe_insert('default_value', frame=q)


def luz_ponto(nome, cor, raio=0.05):
    d = bpy.data.lights.new(nome, 'POINT')
    d.color = cor
    d.shadow_soft_size = raio
    o = bpy.data.objects.new(nome, d)
    sc.collection.objects.link(o)
    return o, d


def chave_luz(d, e, q):
    d.energy = e
    d.keyframe_insert('energy', frame=q)


def bloco(c, tam, mat, chamine=False, tanque=False):
    """Blocos simples de máquina em volta (só para escala)."""
    caixa(B('blocos_laje', 'concreto'), Vector((c[0], c[1], 0.05)), (tam[0] + 0.2, tam[1] + 0.2, 0.1))
    caixa(B('blocos_' + mat, mat), Vector((c[0], c[1], 0.1 + tam[2] / 2)), tam)
    caixa(B('blocos_tampa', 'grafite'), Vector((c[0], c[1], 0.1 + tam[2] + 0.03)), (tam[0] + 0.04, tam[1] + 0.04, 0.06))
    if chamine:
        cil(B('blocos_chamine', 'ferro', True), Vector((c[0] - tam[0] * 0.25, c[1], 0.1 + tam[2] + 0.9)), 0.2, 1.8, lados=16)
    if tanque:
        cil(B('blocos_tanque', 'casco', True), Vector((c[0] + tam[0] * 0.2, c[1], 0.1 + tam[2] + 0.5)), min(tam[:2]) * 0.3, 0.9, lados=24)


# =================================================================== CÚPULA CONTRA RAIOS
def construir_cupula():
    laje()
    ZP = 0.46                                        # topo do pedestal
    ZI = 0.86                                        # topo dos isoladores (pé da torre)
    ZT = 6.2                                         # colar do topo
    W0, W1 = 0.36, 0.14                              # meia-largura da torre embaixo e em cima

    def w(z):
        return W0 + (W1 - W0) * (z - ZI) / (ZT - ZI)

    DIAG = [Vector((math.cos(PI / 4 + k * PI / 2), math.sin(PI / 4 + k * PI / 2), 0)) for k in range(4)]   # NE NO SO SE
    # ---------------- pedestal octogonal blindado
    bm = B('pedestal', 'amarelo')
    octo(bm, Vector((0, 0, 0)), 0.66, Z0, Z0 + 0.05)
    octo(bm, Vector((0, 0, 0)), 0.62, Z0 + 0.05, ZP - 0.03)
    octo(B('pedestal_tampa', 'grafite'), Vector((0, 0, 0)), 0.635, ZP - 0.03, ZP)
    APO = 0.62
    for k in range(8):
        a = k * PI / 4
        n = Vector((math.cos(a), math.sin(a), 0))
        R = rot_face(n)
        larg = 2 * APO * math.tan(PI / 8) - 0.05
        c = n * (APO + 0.012) + Vector((0, 0, (Z0 + ZP) / 2 + 0.01))
        mat = {2: 'zarcao', 5: 'verde_oliva'}.get(k, 'casco')
        if k == 6:                                                         # chapa arrancada: furos e remendo torto
            chapa(B('remendos', 'azul_trocado'), B('parafusos', 'aco'), c + R @ Vector((0.04, 0, 0)), larg * 0.5, 0.18, n, giro=0.15)
            for sx in (-1, 1):
                for sz in (-1, 1):
                    cil(B('furos', 'escuro'), c + R @ Vector((sx * larg * 0.44, 0.001, sz * 0.12)), 0.008, 0.004, n, lados=6)
            continue
        caixa(B('chapas_' + mat, mat), c, (larg, 0.024, 0.27), R)
        parafusos_em(B('parafusos', 'aco'), [c + R @ Vector((sx * larg * 0.44, 0.012, sz * 0.115)) for sx in (-1, 0, 1) for sz in (-1, 1)], n)
        if k in (0, 4):
            for j in range(5):
                caixa(B('grelha', 'escuro'), c + R @ Vector((0, 0.013, -0.06 + j * 0.03)), (larg * 0.6, 0.004, 0.012), R)
                caixa(B('grelha_aletas', 'ferro'), c + R @ Vector((0, 0.019, -0.052 + j * 0.03)), (larg * 0.62, 0.006, 0.007),
                      R @ Matrix.Rotation(0.6, 3, 'X'))
        for j in range(2):                                                 # escorridos de ferrugem dos parafusos
            escorrido(B('escorridos', 'ferrugem'), c + R @ Vector((random.uniform(-0.15, 0.15), 0.013, 0.1)), n, random.uniform(0.08, 0.16))
    stencil = B('estencil', 'tinta')                                       # número de série meio apagado
    for i in range(5):
        if i != 2:
            caixa(stencil, Vector((0.645, -0.07 + i * 0.035, 0.24)), (0.003, 0.022, 0.05))
    # ---------------- isoladores de porcelana nos pés da torre + sapatas
    for d in DIAG:
        p = d * W0 * math.sqrt(2)
        cil(B('sapatas', 'ferro', True), Vector((p.x, p.y, ZP + 0.015)), 0.13, 0.03, lados=20)
        parafusos_em(B('parafusos', 'aco'), [Vector((p.x, p.y, ZP + 0.03)) + Vector((math.cos(a), math.sin(a), 0)) * 0.105
                                             for a in (k * PI / 3 for k in range(6))], Z)
        isolador(B('isoladores', 'porcelana', True), Vector((p.x, p.y, ZP + 0.03)), Vector((p.x, p.y, ZI - 0.04)), 0.1, 5)
        cil(B('pes_torre', 'aco', True), Vector((p.x, p.y, ZI - 0.02)), 0.085, 0.04, lados=20)
    # ---------------- torre de treliça
    NIV = [ZI + (ZT - ZI) * i / 9 for i in range(10)]
    pernas = []
    for d in DIAG:
        a = d * W0 * math.sqrt(2) + Vector((0, 0, ZI))
        b = d * W1 * math.sqrt(2) + Vector((0, 0, ZT))
        pernas.append((a, b))
        tubo(B('pernas', 'amarelo', True), a, b, 0.04, 14)
    def canto(k, z):
        return DIAG[k] * w(z) * math.sqrt(2) + Vector((0, 0, z))
    for i, z in enumerate(NIV):
        for k in range(4):
            j = (k + 1) % 4
            mat = 'zarcao' if (i in (3, 4) and k == 1) else 'galvanizado'
            tubo(B('travessas_' + mat, mat, True), canto(k, z), canto(j, z), 0.018, 8)
            if i < len(NIV) - 1:                                           # X nas faces
                z2 = NIV[i + 1]
                if not (i == 6 and k == 2):                                # uma diagonal faltando (arrancada)
                    tubo(B('diagonais_' + mat, mat, True), canto(k, z), canto(j, z2), 0.013, 8)
                tubo(B('diagonais_' + mat, mat, True), canto(j, z), canto(k, z2), 0.013, 8)
            # chapas de nó (gusset) em cada encontro
            caixa(B('nos', 'aco'), canto(k, z) - DIAG[k] * 0.02, (0.06, 0.06, 0.06))
    # restos da diagonal arrancada: toco torto
    a = canto(2, NIV[6])
    tubo(B('diagonais_galvanizado', 'galvanizado', True), a, a + (canto(3, NIV[7]) - a).normalized() * 0.18 + Vector((0.03, 0, -0.04)), 0.013, 8)
    # placas de numeração e escada? NÃO (não há humanos) — sensores da IA presos na torre
    for z, k in ((2.4, 0), (4.1, 2)):
        p = canto(k, z) + DIAG[k] * 0.06
        caixa(B('sensores', 'grafite'), p, (0.08, 0.08, 0.12))
        cil(B('sensores_olho', 'olho'), p + DIAG[k] * 0.045, 0.02, 0.01, DIAG[k], lados=12)
    # ---------------- colar do topo, mastro, anéis captores
    cil(B('colar', 'grafite', True), Vector((0, 0, ZT + 0.04)), 0.3, 0.12, lados=24)
    cil(B('colar', 'grafite', True), Vector((0, 0, ZT - 0.05)), 0.24, 0.08, lados=24)
    parafusos_em(B('parafusos', 'aco'), [Vector((math.cos(a) * 0.26, math.sin(a) * 0.26, ZT + 0.1)) for a in (k * PI / 6 for k in range(12))], Z)
    ZM = 7.72
    tubo(B('mastro', 'aco', True), Vector((0, 0, ZT)), Vector((0, 0, ZM)), 0.075, 20)
    for z in (6.62, 7.12, 7.5):
        cil(B('mastro_luvas', 'ferro', True), Vector((0, 0, z)), 0.1, 0.07, lados=20)
    ANEIS = [(6.48, 1.12, 0.06, 18), (6.95, 0.82, 0.052, 14), (7.36, 0.52, 0.045, 10)]
    for i, (z, R, r, npt) in enumerate(ANEIS):
        mat = 'aluminio' if i != 1 else 'cobre'
        toro(B('aneis_' + mat, mat, True), Vector((0, 0, z)), R, r, 72, 14)
        for k in range(6):                                                 # raios do anel
            a = k * PI / 3 + i * 0.3
            d = Vector((math.cos(a), math.sin(a), 0))
            tubo(B('aneis_raios', 'aco', True), Vector((0, 0, z)) + d * 0.08, Vector((0, 0, z)) + d * (R - r * 0.6), 0.016, 10)
            caixa(B('aneis_garras', 'ferro'), Vector((0, 0, z)) + d * (R - r * 0.9), (0.05, 0.05, r * 2.6), Matrix.Rotation(a, 3, 'Z'))
        for k in range(npt):                                               # pontas captoras eriçadas
            a = (k + 0.5) * 2 * PI / npt + i * 0.2
            d = Vector((math.cos(a), math.sin(a), 0))
            base_p = Vector((0, 0, z)) + d * (R + r * 0.6)
            ponta = base_p + (d * 0.55 + Z * 0.85).normalized() * (0.32 - 0.05 * i)
            tubo(B('pontas', 'cromo', True), base_p, ponta, 0.011, 8)
            cil(B('pontas_cone', 'cromo'), ponta + (ponta - base_p).normalized() * 0.03, 0.011, 0.06, ponta - base_p, lados=8, r2=0.001)
            if (k + i) % 5 == 0:                                           # pontas queimadas/derretidas
                curva(B('pontas_queimadas', 'chamusco'), ponta, 0.02, 8)
        # derretimento e escorrido de óxido nos anéis
        for k in range(4):
            a = random.uniform(0, 2 * PI)
            p = Vector((math.cos(a) * R, math.sin(a) * R, z - r * 0.9))
            for j in range(3):
                tubo(B('pingos_oxido', 'cobre_velho'), p + Vector((0, 0, -0.012 * j)), p + Vector((0, 0, -0.012 * j - 0.03)), 0.009 - 0.002 * j, 6)
    # garras que seguram o cristal no topo
    ZC = ZM + 0.36
    for k in range(3):
        a = k * 2 * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = bezier(Vector((0, 0, ZM - 0.04)) + d * 0.06, Vector((0, 0, ZM + 0.05)) + d * 0.2, Vector((0, 0, ZC - 0.15)) + d * 0.2,
                     Vector((0, 0, ZC + 0.05)) + d * 0.08, 8)
        mangueira(B('garras', 'grafite'), pts, 0.022)
        curva(B('garras_juntas', 'aco'), pts[4], 0.03, 10)
        cil(B('garras_pontas', 'cromo'), pts[-1] + Vector((0, 0, 0.02)) - d * 0.012, 0.016, 0.05, Z - d * 0.5, lados=8, r2=0.004)
    cil(B('colar_cristal', 'bobina', True), Vector((0, 0, ZM + 0.02)), 0.11, 0.06, lados=20)
    for k in range(5):
        toro(B('colar_espiras', 'bobina', True), Vector((0, 0, ZM - 0.12 - k * 0.028)), 0.088, 0.011, 24, 6)
    # ---------------- guarda-chuva: 8 varetas, escoras, pontas e rede
    RT, ZTIP = 2.1, 5.25
    pontas_v = []
    for k in range(8):
        a = k * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * 0.3 + Vector((0, 0, ZT + 0.02))
        p1 = d * RT + Vector((0, 0, ZTIP))
        tubo(B('varetas', 'amarelo', True), p0, p1, 0.026, 12)
        caixa(B('varetas_orelhas', 'ferro'), p0 + d * 0.03, (0.07, 0.07, 0.09), Matrix.Rotation(a, 3, 'Z'))
        pontas_v.append(p1)
        # ponta captora na ponta da vareta
        tubo(B('pontas', 'cromo', True), p1, p1 + (d * 0.3 + Z).normalized() * 0.42, 0.012, 8)
        curva(B('pontas_bola', 'cromo'), p1 + (d * 0.3 + Z).normalized() * 0.44, 0.03, 10)
        cil(B('varetas_tampas', 'ferro', True), p1 + d * 0.02, 0.034, 0.06, d, lados=12)
        # escora (como a do guarda-chuva) do meio da torre ao meio da vareta
        zs = 4.55
        diag = k % 2 == 1
        ps = d * (w(zs) * (math.sqrt(2) if diag else 1.0) + 0.02) + Vector((0, 0, zs))
        pm = p0.lerp(p1, 0.5)
        tubo(B('escoras', 'galvanizado', True), ps, pm - Z * 0.03, 0.018, 10)
        caixa(B('escoras_presilha', 'ferro'), pm - Z * 0.02, (0.06, 0.06, 0.05), Matrix.Rotation(a, 3, 'Z'))
        caixa(B('escoras_presilha', 'ferro'), ps, (0.05, 0.05, 0.07), Matrix.Rotation(a, 3, 'Z'))
        if k == 5:                                                          # vareta remendada com luva aparafusada
            pr = p0.lerp(p1, 0.78)
            tubo(B('remendo_luva', 'zarcao', True), pr - (p1 - p0).normalized() * 0.1, pr + (p1 - p0).normalized() * 0.1, 0.036, 12)
    # rede: três anéis de cabo entre as varetas (com flecha)
    for f in (0.42, 0.7, 1.0):
        for k in range(8):
            a, b = k * PI / 4, (k + 1) * PI / 4
            pa = Vector((math.cos(a), math.sin(a), 0)) * 0.3 + Vector((0, 0, ZT + 0.02))
            pb = Vector((math.cos(b), math.sin(b), 0)) * 0.3 + Vector((0, 0, ZT + 0.02))
            A = pa.lerp(pontas_v[k], f)
            Bp = pb.lerp(pontas_v[(k + 1) % 8], f)
            linha(B('rede', 'cobre', True), catenaria(A, Bp, 0.05 + 0.08 * f, 10), 0.008, 6)
            curva(B('rede_presilhas', 'ferro'), A, 0.017, 8)
    # ---------------- estais com isolador-ovo, esticador e âncora
    for k, d in enumerate(DIAG):
        top = canto(k, 4.0) + d * 0.03
        anc = d * 1.39 * math.sqrt(2) + Vector((0, 0, Z0 + 0.09))
        anc = Vector((math.copysign(1.36, d.x), math.copysign(1.36, d.y), Z0 + 0.09))
        u = (anc - top).normalized()
        i1 = top + u * 0.45
        i2 = i1 + u * 0.16
        e1 = anc - u * 0.55
        e2 = anc - u * 0.3
        linha(B('estais', 'galvanizado', True), [top, i1], 0.007)
        linha(B('estais', 'galvanizado', True), catenaria(i2, e1, 0.04, 14), 0.007)
        linha(B('estais', 'galvanizado', True), [e2, anc], 0.007)
        bmesh.ops.create_uvsphere(B('isol_ovo', 'porcelana_cinza', True), u_segments=14, v_segments=10, radius=1.0,
                                  matrix=Matrix.Translation((i1 + i2) / 2) @ rot_de(u).to_4x4() @ Matrix.Diagonal((0.045, 0.045, 0.085, 1)))
        tubo(B('esticador', 'ferro', True), e1, e2, 0.016, 8)                # esticador (corpo)
        for s in (e1, e2):
            cil(B('esticador_porcas', 'aco'), s, 0.022, 0.03, u, lados=6)
        caixa(B('ancoras', 'ferro'), Vector((anc.x, anc.y, Z0 + 0.015)), (0.2, 0.2, 0.03))
        caixa(B('ancoras_orelha', 'ferro'), Vector((anc.x, anc.y, Z0 + 0.06)), (0.03, 0.08, 0.08), Matrix.Rotation(math.atan2(d.y, d.x) + PI / 2, 3, 'Z'))
        parafusos_em(B('parafusos', 'aco'), [Vector((anc.x + sx * 0.075, anc.y + sy * 0.075, Z0 + 0.03)) for sx in (-1, 1) for sy in (-1, 1)], Z, 0.012)
        escorrido(B('escorridos', 'ferrugem'), Vector((anc.x, anc.y - 0.1, Z0 + 0.03)), Vector((0, -1, 0)), 0.02)
    # ---------------- cordoalha de descida (perna noroeste) → caixa de descida
    k = 1
    dn = DIAG[k]
    pts = []
    for i in range(14):
        z = ZT - 0.1 - (ZT - 0.1 - ZI - 0.15) * i / 13
        pts.append(canto(k, z) + dn * 0.07 + Vector((-dn.y, dn.x, 0)) * 0.05)
    lat = Vector((dn.y, -dn.x, 0))
    # do anel grande até o colar
    topo_c = [Vector((math.cos(PI * 0.75), math.sin(PI * 0.75), 0)) * 1.08 + Vector((0, 0, ANEIS[0][0] - 0.05)),
              Vector((math.cos(PI * 0.75), math.sin(PI * 0.75), 0)) * 0.5 + Vector((0, 0, ZT + 0.2)), pts[0] + Z * 0.05]
    feixe(B('cordoalha', 'cobre'), B('cordoalha_abracadeiras', 'aco'), bezier(topo_c[0], topo_c[0] - Z * 0.3, topo_c[1], topo_c[2], 8) + pts[1:], lat, 3, 0.016, 2)
    CX = Vector((-0.86, 0.86, 0))                                          # caixa de descida
    caixa_de(B('caixa_descida', 'amarelo'), (CX.x - 0.2, CX.y - 0.18, Z0), (CX.x + 0.2, CX.y + 0.18, Z0 + 0.55))
    caixa_de(B('caixa_descida_tampa', 'grafite'), (CX.x - 0.215, CX.y - 0.195, Z0 + 0.55), (CX.x + 0.215, CX.y + 0.195, Z0 + 0.59))
    chapa(B('remendos', 'zarcao'), B('parafusos', 'aco'), Vector((CX.x + 0.2, CX.y, Z0 + 0.3)), 0.2, 0.22, Vector((1, 0, 0)))
    for j in range(3):
        mancha_em(B('chamusco', 'chamusco'), Vector((CX.x + 0.07 * j - 0.07, CX.y - 0.181, Z0 + 0.48)), 0.035, Vector((0, -1, 0)), 1.8)
    isolador(B('isoladores', 'porcelana', True), Vector((CX.x, CX.y, Z0 + 0.59)), Vector((CX.x, CX.y, Z0 + 0.82)), 0.06, 4)
    fim = pts[-1]
    feixe(B('cordoalha', 'cobre'), B('cordoalha_abracadeiras', 'aco'),
          bezier(fim, fim + Vector((-0.1, 0.1, -0.1)), Vector((CX.x, CX.y, Z0 + 1.0)), Vector((CX.x, CX.y, Z0 + 0.84)), 8), lat, 3, 0.016, 3)
    # ---------------- banco de capacitores (oeste)
    caixa_de(B('skid', 'ferro'), (-1.44, -1.18, Z0), (-0.84, 0.55, Z0 + 0.07))
    for x in (-1.44, -0.84):
        for y in (-1.18, 0.55):
            viga(B('rack', 'amarelo'), Vector((x, y, Z0 + 0.07)), Vector((x, y, Z0 + 1.05)), 0.05)
    for y in (-1.18, 0.55):
        viga(B('rack', 'amarelo'), Vector((-1.44, y, Z0 + 1.05)), Vector((-0.84, y, Z0 + 1.05)), 0.05)
    for x in (-1.44, -0.84):
        viga(B('rack', 'amarelo'), Vector((x, -1.18, Z0 + 1.05)), Vector((x, 0.55, Z0 + 1.05)), 0.05)
        viga(B('rack_trava', 'galvanizado'), Vector((x, -1.18, Z0 + 0.12)), Vector((x, 0.55, Z0 + 0.95)), 0.025)
    CAPS = [(x, y) for x in (-1.29, -0.99) for y in (-1.0, -0.6, -0.2, 0.2)] + [(-1.14, 0.42)]
    for i, (x, y) in enumerate(CAPS[:8]):
        rompido = i == 5
        trocado = i == 2
        mat = 'zarcao' if trocado else 'capacitor'
        h = 0.72 if not trocado else 0.66
        cil(B('caps_' + mat, mat, True), Vector((x, y, Z0 + 0.07 + h / 2)), 0.125, h, lados=28)
        for zz in (0.18, h - 0.12):                                        # cintas
            toro(B('caps_cintas', 'aco', True), Vector((x, y, Z0 + 0.07 + zz)), 0.128, 0.008, 28, 6)
        topo = Z0 + 0.07 + h
        if rompido:                                                        # tampa estourada, eletrólito, fuligem
            cil(B('caps_rompido_tampa', 'casco'), Vector((x + 0.05, y - 0.02, topo + 0.05)), 0.11, 0.015,
                Vector((0.4, -0.2, 1)), lados=24)
            cil(B('caps_rompido_miolo', 'escuro'), Vector((x, y, topo + 0.002)), 0.1, 0.004, lados=24)
            for j in range(6):
                mancha_em(B('fuligem', 'fuligem'), Vector((x + 0.126 * math.cos(j), y + 0.126 * math.sin(j), topo - 0.08)), 0.045,
                          Vector((math.cos(j), math.sin(j), 0)), 2.0)
            for j in range(3):
                escorrido(B('eletrolito', 'oleo'), Vector((x - 0.126, y + 0.03 * j, topo - 0.02)), Vector((-1, 0, 0)), 0.3 + 0.1 * j)
            poca((x - 0.2, y), 0.09)
        else:
            cil(B('caps_tampas', 'grafite', True), Vector((x, y, topo + 0.01)), 0.13, 0.02, lados=28)
            isolador(B('buchas', 'porcelana', True), Vector((x, y, topo + 0.02)), Vector((x, y, topo + 0.17)), 0.04, 3)
            cil(B('buchas_terminal', 'cobre', True), Vector((x, y, topo + 0.19)), 0.018, 0.04, lados=10)
        stencil_y = y
        caixa(B('estencil', 'tinta'), Vector((x + 0.126, stencil_y, Z0 + 0.45)), (0.004, 0.05, 0.03))
    # barramento de cobre por cima (x2 linhas), um trecho remendado com cabo
    for x in (-1.29, -0.99):
        zb = Z0 + 0.07 + 0.72 + 0.21
        viga(B('barramento', 'cobre'), Vector((x, -1.08, zb)), Vector((x, 0.38, zb)), 0.035)
        for y in (-1.0, -0.6, -0.2, 0.2):
            tubo(B('barramento_lig', 'cobre', True), Vector((x, y, zb - 0.04)), Vector((x, y, zb)), 0.012, 8)
    viga(B('barramento', 'cobre'), Vector((-1.29, 0.38, Z0 + 1.0)), Vector((-0.99, 0.38, Z0 + 1.0)), 0.035)
    mangueira(B('cabos', 'cabo'), bezier(Vector((-0.99, -0.6, Z0 + 0.82)), Vector((-0.95, -0.6, Z0 + 0.95)),
                                          Vector((-0.99, -0.62, Z0 + 1.05)), Vector((-0.99, -0.62, Z0 + 1.0)), 6), 0.012)
    # barramento → caixa de descida
    feixe(B('cordoalha', 'cobre'), B('cordoalha_abracadeiras', 'aco'),
          bezier(Vector((-1.14, 0.38, Z0 + 1.0)), Vector((-1.14, 0.7, Z0 + 1.0)), Vector((CX.x - 0.1, CX.y, Z0 + 0.9)),
                 Vector((CX.x - 0.03, CX.y, Z0 + 0.62)), 8), Vector((1, 0, 0)), 2, 0.016, 4)
    # ---------------- centelhador de esferas (nordeste)
    SG = Vector((0.6, 1.08, 0))
    caixa_de(B('centelhador_base', 'grafite'), (SG.x - 0.42, SG.y - 0.2, Z0), (SG.x + 0.42, SG.y + 0.2, Z0 + 0.18))
    chapa(B('remendos', 'verde_oliva'), B('parafusos', 'aco'), Vector((SG.x + 0.1, SG.y - 0.2, Z0 + 0.1)), 0.3, 0.12, Vector((0, -1, 0)))
    ESF = []
    for s in (-1, 1):
        p = SG + Vector((s * 0.28, 0, 0))
        isolador(B('isoladores', 'porcelana', True), Vector((p.x, p.y, Z0 + 0.18)), Vector((p.x, p.y, Z0 + 0.8)), 0.075, 6)
        cil(B('centelhador_suporte', 'cobre', True), Vector((p.x, p.y, Z0 + 0.84)), 0.04, 0.08, lados=14)
        tubo(B('centelhador_hastes', 'cobre', True), Vector((p.x, p.y, Z0 + 0.88)), Vector((p.x - s * 0.08, p.y, Z0 + 0.98)), 0.025, 12)
        c = Vector((p.x - s * 0.17, p.y, Z0 + 1.0))
        bmesh.ops.create_uvsphere(B('esferas', 'cobre', True), u_segments=28, v_segments=16, radius=0.1, matrix=Matrix.Translation(c))
        mancha_em(B('esferas_queimadas', 'chamusco'), c + Vector((-s * 0.1, 0, 0)), 0.04, Vector((-s, 0, 0)))
        ESF.append(c + Vector((-s * 0.1, 0, 0)))
    # cabos: caixa de descida → esfera oeste, esfera leste → anel de terra
    mangueira(B('cabos', 'cabo'), bezier(Vector((CX.x + 0.2, CX.y + 0.05, Z0 + 0.4)), Vector((CX.x + 0.6, CX.y + 0.1, Z0 + 0.4)),
                                          Vector((SG.x - 0.36, SG.y, Z0 + 0.45)), Vector((SG.x - 0.28, SG.y, Z0 + 0.82)), 10), 0.022)
    mangueira(B('cordoalha', 'cobre'), bezier(Vector((SG.x + 0.28, SG.y + 0.04, Z0 + 0.82)), Vector((SG.x + 0.5, SG.y + 0.1, Z0 + 0.6)),
                                               Vector((1.4, 1.38, Z0 + 0.15)), Vector((1.38, 1.4, Z0 + 0.03)), 10), 0.015)
    # ---------------- anel de aterramento em volta da laje + hastes
    RA = 1.42
    for a, b in (((-RA, -RA), (RA, -RA)), ((RA, -RA), (RA, RA)), ((RA, RA), (-RA, RA)), ((-RA, RA), (-RA, -RA))):
        viga(B('anel_terra', 'cobre_velho'), Vector((a[0], a[1], Z0 + 0.012)), Vector((b[0], b[1], Z0 + 0.012)), 0.025)
    for t in range(20):                                                    # grampos do anel
        s = t / 5
        lado = int(s)
        f = s - lado
        p = [Vector((-RA + 2 * RA * f, -RA, 0)), Vector((RA, -RA + 2 * RA * f, 0)), Vector((RA - 2 * RA * f, RA, 0)), Vector((-RA, RA - 2 * RA * f, 0))][lado]
        caixa(B('anel_grampos', 'aco'), Vector((p.x, p.y, Z0 + 0.03)), (0.05, 0.05, 0.02))
    HASTES = [Vector((0, -1.75, 0)), Vector((1.75, 0.05, 0)), Vector((-0.05, 1.75, 0)), Vector((-1.75, -0.05, 0)),
              Vector((3.2, -2.4, 0)), Vector((-2.8, 2.9, 0))]
    for i, h in enumerate(HASTES):
        cil(B('caixas_inspecao', 'concreto', True), Vector((h.x, h.y, 0.04)), 0.17, 0.12, lados=20)
        cil(B('caixas_inspecao_furo', 'escuro', True), Vector((h.x, h.y, 0.1)), 0.13, 0.005, lados=20)
        for j in range(5):
            caixa(B('grelhas_inspecao', 'ferro'), Vector((h.x - 0.1 + j * 0.05, h.y, 0.105)), (0.012, 0.24, 0.012))
        tubo(B('hastes', 'cobre', True), Vector((h.x + 0.05, h.y + 0.05, 0.0)), Vector((h.x + 0.05, h.y + 0.05, 0.42)), 0.018, 12)
        cil(B('hastes_grampo', 'aco', True), Vector((h.x + 0.05, h.y + 0.05, 0.3)), 0.032, 0.05, lados=8)
        curva(B('hastes_topo', 'cobre_velho'), Vector((h.x + 0.05, h.y + 0.05, 0.43)), 0.024, 10)
        alvo = Vector((max(-RA, min(RA, h.x)), max(-RA, min(RA, h.y)), Z0 + 0.02))
        if i < 4:
            mangueira(B('cordoalha', 'cobre'), bezier(Vector((h.x + 0.05, h.y + 0.05, 0.3)), Vector((h.x * 0.95, h.y * 0.95, 0.3)),
                                                       alvo + Z * 0.08, alvo, 6), 0.012)
        else:                                                              # hastes no solo, cabo enterrado aparecendo
            d = (alvo - Vector((h.x, h.y, 0))).normalized()
            mangueira(B('cordoalha', 'cobre'), bezier(Vector((h.x + 0.05, h.y + 0.05, 0.3)), Vector((h.x, h.y, 0.1)) + d * 0.3,
                                                       Vector((h.x, h.y, -0.02)) + d * 0.6, Vector((h.x, h.y, -0.05)) + d * 0.9, 6), 0.012)
        # Lichtenberg queimado no chão em volta das hastes
        for r_ in range(5 if i >= 4 else 3):
            ang = random.uniform(0, 2 * PI)
            if i < 4:
                ang = math.atan2(h.y, h.x) + random.uniform(-1.2, 1.2)
            lichtenberg(B('lichtenberg', 'queimado'), Vector((h.x, h.y, 0)) + Vector((math.cos(ang), math.sin(ang), 0)) * 0.18, ang,
                        random.uniform(0.6, 1.4), 0.009, 4, 0.004 + 0.0004 * r_)
        mancha(B('queimado_base', 'queimado'), (h.x, h.y), 0.3, 0.0035)
    # e na laje, saindo do pedestal (descarga antiga que escapou)
    for ang in (3.6, 4.2):
        lichtenberg(B('lichtenberg_laje', 'queimado'), Vector((math.cos(ang), math.sin(ang), 0)) * 0.68, ang, 0.7, 0.008, 4, Z0 + 0.0014)
    # ---------------- retificador com aletas (leste) → eletroduto da rede (sul)
    RX = Vector((1.13, -0.3, 0))
    caixa_de(B('retificador', 'amarelo'), (RX.x - 0.26, RX.y - 0.55, Z0), (RX.x + 0.26, RX.y + 0.55, Z0 + 0.95))
    caixa_de(B('retificador_tampa', 'grafite'), (RX.x - 0.28, RX.y - 0.57, Z0 + 0.95), (RX.x + 0.28, RX.y + 0.57, Z0 + 1.0))
    for j in range(9):                                                     # aletas de radiador na face leste
        y = RX.y - 0.44 + j * 0.11
        caixa(B('retificador_aletas', 'ferro'), Vector((RX.x + 0.3, y, Z0 + 0.5)), (0.08, 0.012, 0.75))
    for j in range(3):
        isolador(B('isoladores', 'porcelana', True), Vector((RX.x - 0.1 + j * 0.0, RX.y - 0.35 + j * 0.35, Z0 + 1.0)),
                 Vector((RX.x - 0.1, RX.y - 0.35 + j * 0.35, Z0 + 1.28)), 0.05, 4)
    feixe(B('cabos', 'cabo'), B('abracadeiras', 'aco'),
          bezier(Vector((RX.x - 0.1, RX.y + 0.35, Z0 + 1.3)), Vector((RX.x - 0.1, RX.y + 0.6, Z0 + 1.6)),
                 Vector((0.3, 0.95, Z0 + 1.2)), Vector((SG.x - 0.28, SG.y - 0.05, Z0 + 0.6)), 14), Vector((1, 0, 0)), 3, 0.013, 4)
    for j in range(2):
        mancha_em(B('fuligem', 'fuligem'), Vector((RX.x - 0.261, RX.y + 0.2 - 0.3 * j, Z0 + 0.8)), 0.06, Vector((-1, 0, 0)), 1.6)
        escorrido(B('escorridos', 'oleo'), Vector((RX.x + 0.261, RX.y - 0.48 + 0.2 * j, Z0 + 0.3)), Vector((1, 0, 0)), 0.2)
    poca((RX.x + 0.4, RX.y - 0.3), 0.12)
    mancha(B('oleo_chao', 'oleo'), (RX.x + 0.36, RX.y - 0.4), 0.1, Z0 + 0.002)
    # leds de estado no retificador
    for j, m in enumerate(('led_verde', 'led_ambar', 'led_verm')):
        cil(B(m, m), Vector((RX.x - 0.262, RX.y - 0.4 + j * 0.05, Z0 + 0.8)), 0.01, 0.006, Vector((-1, 0, 0)), lados=10)
    # eletroduto até a borda sul (porta de energia)
    cano(B('eletroduto', 'galvanizado', True), B('eletroduto_flanges', 'ferro'),
         [Vector((RX.x - 0.05, RX.y - 0.55, Z0 + 0.2)), Vector((RX.x - 0.05, -1.25, Z0 + 0.2)), Vector((RX.x - 0.05, -1.25, Z0 - 0.0)),
          Vector((RX.x - 0.05, -1.52, Z0 - 0.0))], 0.045)
    caixa_de(B('caixa_rede', 'grafite'), (RX.x - 0.2, -1.49, 0.0), (RX.x + 0.1, -1.35, Z0 + 0.38))
    # contador de descargas (mostrador) e sinalizadores na caixa da rede
    cil(B('contador', 'ferro', True), Vector((RX.x - 0.05, -1.48, Z0 + 0.26)), 0.06, 0.03, Vector((0, -1, 0)), lados=20)
    cil(B('contador_face', 'face_mostrador'), Vector((RX.x - 0.05, -1.497, Z0 + 0.26)), 0.05, 0.004, Vector((0, -1, 0)), lados=20)
    tubo(B('contador_ponteiro', 'led_verm'), Vector((RX.x - 0.05, -1.5, Z0 + 0.26)), Vector((RX.x - 0.02, -1.5, Z0 + 0.3)), 0.003, 4)
    # ---------------- sensor da IA (sul), poste com sinalizadores
    SP = Vector((-0.45, -1.25, 0))
    caixa(B('poste_base', 'ferro'), Vector((SP.x, SP.y, Z0 + 0.02)), (0.16, 0.16, 0.04))
    tubo(B('poste', 'amarelo', True), Vector((SP.x, SP.y, Z0)), Vector((SP.x, SP.y, Z0 + 1.35)), 0.03, 12)
    caixa(B('poste_cabeca', 'grafite'), Vector((SP.x, SP.y, Z0 + 1.42)), (0.14, 0.12, 0.14))
    cil(B('olho', 'olho'), Vector((SP.x, SP.y - 0.065, Z0 + 1.44)), 0.03, 0.012, Vector((0, -1, 0)), lados=16)
    mangueira(B('cabos', 'cabo'), bezier(Vector((SP.x, SP.y, Z0 + 0.2)), Vector((SP.x + 0.2, SP.y + 0.1, Z0 + 0.05)),
                                          Vector((-0.6, -0.8, Z0 + 0.02)), Vector((-0.55, -0.62, Z0 + 0.2)), 8), 0.012)
    SINAIS = [Vector((SP.x, SP.y, Z0 + 1.56)), Vector((0, 0, 4.55)) + DIAG[0] * w(4.55) * math.sqrt(2) + DIAG[0] * 0.06,
              Vector((0, 0, 4.55)) + DIAG[2] * w(4.55) * math.sqrt(2) + DIAG[2] * 0.06]
    for p in SINAIS:
        cil(B('sinal_base', 'grafite', True), p - Z * 0.04, 0.045, 0.04, lados=14)
        cil(B('sinais', 'sinal', True), p + Z * 0.02, 0.035, 0.08, lados=14)
        for k in range(4):
            a = k * PI / 2
            tubo(B('sinal_grade', 'ferro'), p - Z * 0.02 + Vector((math.cos(a), math.sin(a), 0)) * 0.04,
                 p + Z * 0.07 + Vector((math.cos(a), math.sin(a), 0)) * 0.04, 0.004, 4)
    # ---------------- eletrocalha com cabos no chão (oeste → leste pelo sul do pedestal)
    pts = [Vector((-0.84, -0.9, Z0 + 0.06)), Vector((-0.2, -0.9, Z0 + 0.06)), Vector((0.5, -0.9, Z0 + 0.06)), Vector((RX.x - 0.26, -0.9, Z0 + 0.06))]
    for a, b in zip(pts, pts[1:]):
        caixa_de(B('eletrocalha', 'galvanizado'), (a.x, a.y - 0.07, Z0), (b.x, b.y + 0.07, Z0 + 0.012))
        for s in (-1, 1):
            caixa_de(B('eletrocalha', 'galvanizado'), (a.x, a.y + s * 0.07 - 0.006, Z0), (b.x, b.y + s * 0.07 + 0.006, Z0 + 0.07))
    for k in range(4):
        mangueira(B('cabos', 'cabo'), [Vector((-0.84, -0.94 + 0.026 * k, Z0 + 0.03)), Vector((RX.x - 0.26, -0.94 + 0.026 * k, Z0 + 0.03))], 0.013)
    # ---------------- poças, folhas de chuva, pedras
    for c, r in (((0.3, -0.5), 0.2), ((-0.5, 0.2), 0.12), ((0.9, 0.7), 0.15), ((-0.2, 1.25), 0.1)):
        poca(c, r)
    for k in range(40):
        r = random.uniform(2.0, 25.0)
        a = random.uniform(0, 2 * PI)
        pedra(B('pedras', 'pedra'), (math.cos(a) * r, math.sin(a) * r, 0.0), random.uniform(0.06, 0.3))
    # máquinas protegidas dentro da cúpula (só escala)
    bloco((9.0, 4.0), (3.0, 2.4, 2.2), 'bloco', chamine=True)
    bloco((-8.0, 7.0), (2.6, 2.6, 3.0), 'bloco_cinza', tanque=True)
    bloco((-12.0, -6.0), (3.5, 2.0, 1.8), 'bloco')
    bloco((5.0, -11.0), (2.2, 4.0, 2.6), 'bloco_cinza', chamine=True)
    bloco((15.0, -4.0), (2.0, 2.0, 1.6), 'bloco', tanque=True)
    bloco((-3.0, -16.0), (4.0, 2.2, 2.0), 'bloco')
    bloco((-17.0, 3.0), (2.4, 3.0, 2.4), 'bloco_cinza', chamine=True)
    bloco((2.0, 18.0), (3.0, 2.0, 2.0), 'bloco')
    descarregar()
    return dict(ZC=ZC, ZM=ZM, ANEIS=ANEIS, ESF=ESF, HASTES=HASTES, SINAIS=SINAIS, CAPS=CAPS, pontas_v=pontas_v)


def animar_cupula(info):
    ZC = info['ZC']
    # cristal no topo (pulsa e gira devagar)
    cr = bpy.data.objects.new('cristal', None)
    sc.collection.objects.link(cr)
    cr.location = Vector((0, 0, ZC))
    bm = bmesh.new()
    rr = [0.11 * (1 + random.uniform(-0.12, 0.12)) for _ in range(6)]
    anel_b = [bm.verts.new((math.cos(k * PI / 3) * rr[k], math.sin(k * PI / 3) * rr[k], -0.08)) for k in range(6)]
    anel_c = [bm.verts.new((math.cos(k * PI / 3) * rr[k] * 0.92, math.sin(k * PI / 3) * rr[k] * 0.92, 0.1)) for k in range(6)]
    topo = bm.verts.new((0.012, -0.008, 0.36))
    fundo = bm.verts.new((-0.006, 0.008, -0.2))
    for k in range(6):
        j = (k + 1) % 6
        bm.faces.new((anel_b[k], anel_b[j], anel_c[j], anel_c[k]))
        bm.faces.new((anel_c[k], anel_c[j], topo))
        bm.faces.new((anel_b[j], anel_b[k], fundo))
    obj('cristal_corpo', bm, 'cristal', cr)
    lc, lcd = luz_ponto('Luz do cristal', VIOLETA, 0.08)
    lc.location = Vector((0, 0, ZC))
    # cúpula de campo (hemisfério de 30 m)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=144, v_segments=72, radius=R_CUP)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')
    cup = obj('cupula', bm, 'cupula')
    suavizar(cup)
    for f in cup.data.polygons:
        f.use_smooth = True
    cup.visible_shadow = False
    base3d.M['cupula'] = cup.data.materials[0]
    # raio: nuvem → P (bate na cúpula)
    P = P_DIR * R_CUP
    topo_r = P + Vector((-9.0, -4.0, 34.0))
    raio1 = descarga('raio_cai', caminho_raio(topo_r, P + P_DIR * 0.1, 5.0, 64, semente=7), 0.09, ramos=9, compr=0.28)
    # descarga escorrendo pelo meridiano de P até o zênite (colada na superfície)
    random.seed(8)
    pts = []
    n = 30
    for i in range(n + 1):
        t = i / n
        el = EL_P + (PI / 2 - EL_P) * t
        az = AZ_P + random.uniform(-0.035, 0.035) * math.sin(PI * t) / max(math.cos(el), 0.15)
        rr_ = R_CUP + 0.12 + random.uniform(-0.05, 0.12)
        pts.append(Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))) * rr_)
    pts[-1] = Vector((0, 0, R_CUP + 0.1))
    escorre = descarga('raio_escorre', pts, 0.07, ramos=0)
    # tentáculos rastejando pela superfície em volta do ponto de impacto
    random.seed(9)
    bt = []
    for k in range(9):
        ang = k * 2 * PI / 9 + random.uniform(-0.2, 0.2)
        t1 = Z.cross(P_DIR).normalized()
        t2 = P_DIR.cross(t1)
        q = []
        dire = (t1 * math.cos(ang) + t2 * math.sin(ang))
        th = 0.0
        for i in range(10):
            th += 0.012 + random.uniform(0, 0.012)
            d = (P_DIR * math.cos(th) + dire * math.sin(th)).normalized()
            dire = (dire + (t1 * random.uniform(-0.3, 0.3) + t2 * random.uniform(-0.3, 0.3))).normalized()
            q.append(d * (R_CUP + 0.1))
        bt.append(q)
    rasteja = []
    for q in bt:
        rasteja += descarga('raio_rasteja', q, 0.035, ramos=0)
    # queda do zênite até o cristal
    queda = descarga('raio_queda', caminho_raio(Vector((0, 0, R_CUP)), Vector((0, 0, ZC + 0.36)), 1.6, 64, semente=10), 0.08, ramos=4, compr=0.15)
    # arcos curtos do cristal até os anéis captores e centelhador
    arcos = []
    random.seed(11)
    for i, (z, R, r, npt) in enumerate(info['ANEIS']):
        for k in range(3):
            a = random.uniform(0, 2 * PI)
            alvo = Vector((math.cos(a) * R, math.sin(a) * R, z + r))
            arcos += descarga('arco_anel', caminho_raio(Vector((0, 0, ZC - 0.1)), alvo, 0.12, 9), 0.012, halo=True)
    a, b = info['ESF']
    arcos += descarga('arco_centelhador', caminho_raio(a, b, 0.04, 8), 0.02, ramos=2, compr=0.4, desvio_r=0.5)
    # faíscas nas hastes de terra
    for h in info['HASTES']:
        p = Vector((h.x + 0.05, h.y + 0.05, 0.43))
        for k in range(2):
            ang = random.uniform(0, 2 * PI)
            arcos += descarga('arco_haste', caminho_raio(p, p + Vector((math.cos(ang) * 0.4, math.sin(ang) * 0.4, -0.38)), 0.08, 7), 0.008, halo=True)
    # luzes do raio
    luzes = []
    for nome, pos, cor, e in (('Raio P', P + P_DIR * 0.5, RAIO_COR, 7.0e3), ('Raio nuvem', topo_r + Vector((0, 0, -2)), RAIO_COR, 1.2e4),
                              ('Raio zênite', Vector((0, 0, R_CUP + 1)), RAIO_COR, 4.0e3), ('Raio torre', Vector((0, 0, 9.5)), RAIO_COR, 1.0e3),
                              ('Centelhador', (a + b) / 2, (0.85, 0.7, 1.0), 150.0)):
        lo, ld = luz_ponto(nome, cor, 0.3)
        lo.location = pos
        luzes.append((ld, e))
    sinais = []
    for p in info['SINAIS']:
        lo, ld = luz_ponto('Sinalizador', AMBAR, 0.03)
        lo.location = p + Z * 0.03
        sinais.append(ld)
    # fumaça saindo do capacitor rompido
    x, y = info['CAPS'][5]
    fumacas = []
    for k in range(6):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        fumacas.append(obj('fumaca', bm, 'fumaca'))
    p_fum = Vector((x, y, Z0 + 0.85))
    # chuva perto da câmera de perto
    chuva_o = chuva((3.0, -5.0, 4.0), (9.0, 7.0, 9.0), 1500, 0.4)
    sinal_bsdf = base3d.M['sinal'].node_tree.nodes['Principled BSDF']
    cristal_bsdf = base3d.M['cristal'].node_tree.nodes['Principled BSDF']
    fase = base3d.M['cupula'].node_tree.nodes['fase'].outputs[0]
    flash = base3d.M['cupula'].node_tree.nodes['flash'].outputs[0]
    T = 40                                                                 # quadro do impacto
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        dt = q - T
        cr.rotation_euler = (0, 0, 2 * PI * fr)
        keyall(cr, 'rotation_euler', q=q)
        pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr)
        carga = 1.0 if 0 <= dt <= 10 else 0.0
        cristal_bsdf.inputs['Emission Strength'].default_value = 0.8 + 1.2 * pulso + 25 * carga * max(0, 1 - dt / 10)
        cristal_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
        chave_luz(lcd, 15 + 25 * pulso + 2000 * carga * max(0, 1 - dt / 10), q)
        piscar = 1.0 if (q // 12) % 2 == 0 else 0.08                        # sinalizadores piscam
        sinal_bsdf.inputs['Emission Strength'].default_value = 25 * piscar
        sinal_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
        for ld in sinais:
            chave_luz(ld, 6 * piscar, q)
        # raio: cai (40-41, pisca de novo 43-44), escorre (41-45), queda (42-46), arcos (42-47)
        vis_cai = dt in (0, 1, 3, 4)
        vis_esc = 1 <= dt <= 5 and dt != 2
        vis_queda = 2 <= dt <= 6
        vis_arco = 2 <= dt <= 7 and dt != 5
        for o in raio1:
            ocultar(o, not vis_cai, q)
        for o in escorre + rasteja:
            ocultar(o, not vis_esc, q)
        for o in queda:
            ocultar(o, not vis_queda, q)
        for o in arcos:
            ocultar(o, not vis_arco, q)
        chave_valor(fase, (dt / 30.0) if dt >= 0 else -1.0, q)
        chave_valor(flash, max(0.0, 1 - dt / 4) if dt >= 0 else 0.0, q)
        for (ld, e), vis in zip(luzes, (vis_cai, vis_cai, vis_queda, vis_queda, vis_arco)):
            chave_luz(ld, e if vis else 0.0, q)
        chuva_o.location = Vector((0.0, 0.0, -(fr * 8 % 1.0) * 3.0))
        keyall(chuva_o, 'location', q=q)
        for k, o in enumerate(fumacas):
            u = ((fr + k / len(fumacas)) % 1.0)
            o.location = p_fum + Vector((0.25 * u + 0.05 * math.sin(k), 0.1 * u, 1.6 * u))
            s = 0.06 + 0.28 * u
            o.scale = (s, s, s * 1.2)
            keyall(o, 'location', 'scale', q=q)
    return T


# =================================================================== REGULADOR CLIMÁTICO
def construir_regulador():
    laje()
    ZP = 0.72                                         # topo do pedestal
    ZE = 3.05                                         # centro do estator / núcleo
    RE = 0.95                                         # raio do estator
    # ---------------- pedestal blindado octogonal em dois andares
    APO = 0.68
    bm = B('pedestal', 'amarelo')
    octo(bm, Vector((0, 0, 0)), APO + 0.04, Z0, Z0 + 0.06)
    octo(bm, Vector((0, 0, 0)), APO, Z0 + 0.06, 0.48)
    octo(B('pedestal_tampa', 'grafite'), Vector((0, 0, 0)), APO + 0.015, 0.48, 0.52)
    octo(B('pedestal', 'amarelo'), Vector((0, 0, 0)), 0.5, 0.52, ZP - 0.02)
    octo(B('pedestal_tampa', 'grafite'), Vector((0, 0, 0)), 0.515, ZP - 0.02, ZP)
    for k in range(8):
        a = k * PI / 4
        n = Vector((math.cos(a), math.sin(a), 0))
        R = rot_face(n)
        larg = 2 * APO * math.tan(PI / 8) - 0.05
        c = n * (APO + 0.012) + Vector((0, 0, 0.29))
        mat = {1: 'zarcao', 4: 'azul_trocado'}.get(k, 'casco')
        caixa(B('chapas_' + mat, mat), c, (larg, 0.024, 0.3), R)
        parafusos_em(B('parafusos', 'aco'), [c + R @ Vector((sx * larg * 0.44, 0.012, sz * 0.13)) for sx in (-1, 0, 1) for sz in (-1, 1)], n)
        if k == 6:
            chapa(B('remendos', 'verde_oliva'), B('parafusos', 'aco'), c + R @ Vector((-0.05, 0.012, 0.03)), 0.16, 0.12, n, giro=-0.1)
        for j in range(2):
            escorrido(B('escorridos', 'ferrugem'), c + R @ Vector((random.uniform(-0.18, 0.18), 0.013, 0.12)), n, random.uniform(0.1, 0.2))
        mancha_em(B('fuligem', 'fuligem'), n * (APO + 0.026) + Vector((0, 0, 0.42)) + R @ Vector((random.uniform(-0.1, 0.1), 0, 0)),
                  0.06, n, 1.5)
    # coroa dentada girando (engrenagem do pedestal) — visível entre os andares
    for k in range(40):
        a = k * 2 * PI / 40
        caixa(B('coroa', 'ferro'), Vector((math.cos(a) * 0.54, math.sin(a) * 0.54, 0.6)), (0.04, 0.035, 0.08), Matrix.Rotation(a, 3, 'Z'))
    # ---------------- quatro braços-garra até o estator e o cubo do topo
    ZH = 4.45                                         # cubo das cornetas
    BR = []
    for k in range(4):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * 0.42 + Vector((0, 0, ZP))
        p1 = d * 0.8 + Vector((0, 0, 1.4))
        p2 = d * (RE + 0.22) + Vector((0, 0, 2.4))
        p3 = d * (RE + 0.12) + Vector((0, 0, ZE))
        p4 = d * (RE * 0.7) + Vector((0, 0, 3.75))
        p5 = d * 0.24 + Vector((0, 0, ZH - 0.1))
        caminho = bezier(p0, p1, p2, p3, 10) + bezier(p3, p3 + Z * 0.4, p4 + d * 0.15, p5, 8)[1:]
        for a_, b_ in zip(caminho, caminho[1:]):
            viga(B('bracos', 'amarelo'), a_, b_, 0.11)
        for c in caminho[1:-1]:
            curva(B('bracos_juntas', 'amarelo'), c, 0.072, 12)
        # costelas (nervuras) e rebites ao longo dos braços
        for j in range(2, len(caminho) - 2, 2):
            u = (caminho[j + 1] - caminho[j - 1]).normalized()
            viga(B('bracos_nervuras', 'grafite'), caminho[j] - u * 0.015, caminho[j] + u * 0.015, 0.14)
        caixa(B('bracos_pe', 'ferro'), p0 + Z * 0.04, (0.22, 0.22, 0.08), Matrix.Rotation(a, 3, 'Z'))
        parafusos_em(B('parafusos', 'aco'), [p0 + Z * 0.08 + Matrix.Rotation(a, 3, 'Z') @ Vector((sx * 0.08, sy * 0.08, 0)) for sx in (-1, 1) for sy in (-1, 1)], Z, 0.012)
        BR.append(caminho)
        # pistão hidráulico de cada braço (camisa no pedestal, haste no braço)
        pc = d * 0.62 + Vector((0, 0, 0.5)) + Vector((-d.y, d.x, 0)) * 0.0
        ph = caminho[5] - d * 0.02
        u = (ph - pc).normalized()
        Lp = (ph - pc).length
        tubo(B('pistoes_camisa', 'amarelo', True), pc, pc + u * Lp * 0.55, 0.045, 16)
        tubo(B('pistoes_haste', 'cromo', True), pc + u * Lp * 0.5, ph, 0.022, 12)
        caixa(B('pistoes_orelha', 'ferro'), pc, (0.1, 0.1, 0.1), Matrix.Rotation(a, 3, 'Z'))
        caixa(B('pistoes_orelha', 'ferro'), ph, (0.08, 0.08, 0.08), Matrix.Rotation(a, 3, 'Z'))
        mangueira(B('mangueiras', 'mangueira'), bezier(pc + u * 0.12 + Vector((-d.y, d.x, 0)) * 0.05, pc + Vector((-d.y, d.x, 0)) * 0.2,
                                                       Vector((0, 0, 0.55)) + d * 0.66 + Vector((-d.y, d.x, 0)) * 0.25,
                                                       Vector((0, 0, 0.42)) + d * 0.69 + Vector((-d.y, d.x, 0)) * 0.22, 8), 0.016)
        escorrido(B('escorridos', 'oleo'), pc + u * Lp * 0.55 - Z * 0.04, d, 0.12)
    # ---------------- estator (anel bobinado) a meia altura, preso nos braços
    toro(B('estator', 'casco', True), Vector((0, 0, ZE)), RE, 0.07, 96, 14)
    for k in range(72):                                                    # espiras de cobre
        a = k * 2 * PI / 72
        if min(abs(((a - PI / 4) % (PI / 2)) - PI / 4 + PI / 4), abs(((a - PI / 4) % (PI / 2)) - PI / 2)) < 0.12:
            continue
        p = Vector((math.cos(a), math.sin(a), 0)) * RE + Vector((0, 0, ZE))
        tg = Vector((-math.sin(a), math.cos(a), 0))
        toro(B('estator_espiras', 'bobina', True), p, 0.09, 0.013, 16, 6, rot_de(tg))
    for k in range(4):                                                     # abraçadeiras estator ↔ braço
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('estator_garras', 'ferro'), d * (RE + 0.07) + Vector((0, 0, ZE)), (0.16, 0.22, 0.22), Matrix.Rotation(a, 3, 'Z'))
        parafusos_em(B('parafusos', 'aco'), [d * (RE + 0.152) + Vector((0, 0, ZE)) + Vector((-d.y, d.x, 0)) * s * 0.07 + Z * t * 0.07
                                             for s in (-1, 1) for t in (-1, 1)], d, 0.012)
    # ---------------- cubo do topo + cornetas de micro-ondas + agulha
    cil(B('cubo', 'grafite', True), Vector((0, 0, ZH)), 0.36, 0.24, lados=24)
    cil(B('cubo', 'grafite', True), Vector((0, 0, ZH + 0.15)), 0.3, 0.06, lados=24)
    toro(B('cubo_aro', 'aco', True), Vector((0, 0, ZH - 0.12)), 0.36, 0.02, 48, 8)
    CORN = []
    for k in range(7):
        if k == 0:
            base_c, eixo = Vector((0, 0, ZH + 0.18)), Z
        else:
            a = (k - 1) * PI / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            base_c, eixo = d * 0.2 + Vector((0, 0, ZH + 0.17)), (d * 0.35 + Z).normalized()
        L = 0.42 if k else 0.5
        Rm = rot_de(eixo) @ Matrix.Rotation(PI / 4, 3, 'Z')
        bmesh.ops.create_cone(B('cornetas', 'aluminio'), cap_ends=True, segments=4, radius1=0.035, radius2=0.12 if k else 0.15, depth=L,
                              matrix=Matrix.Translation(base_c + eixo * L / 2) @ Rm.to_4x4())
        bmesh.ops.create_cone(B('cornetas_boca', 'escuro'), cap_ends=True, segments=4, radius1=0.1 if k else 0.13, radius2=0.1 if k else 0.13,
                              depth=0.004, matrix=Matrix.Translation(base_c + eixo * (L + 0.001)) @ Rm.to_4x4())
        cil(B('cornetas_guia', 'cobre', True), base_c, 0.04, 0.12, eixo, lados=12)
        CORN.append((base_c + eixo * L, eixo))
    # fuligem/queimado nas bocas das cornetas
    for (p, e) in CORN[1:4]:
        mancha_em(B('fuligem', 'fuligem'), p - e * 0.06 + Vector((e.x, e.y, 0)).normalized() * 0.075, 0.04, Vector((e.x, e.y, 0)), 1.4)
    tubo(B('agulha', 'aco', True), Vector((0, 0, ZH + 0.5)), Vector((0, 0, 5.55)), 0.03, 12)
    cil(B('agulha_ponta', 'cromo'), Vector((0, 0, 5.6)), 0.03, 0.12, lados=12, r2=0.002)
    for z in (4.95, 5.25):
        toro(B('agulha_aneis', 'cobre', True), Vector((0, 0, z)), 0.12, 0.012, 32, 6)
        for k in range(3):
            a = k * 2 * PI / 3
            tubo(B('agulha_aneis', 'cobre', True), Vector((0, 0, z)), Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, z)), 0.006, 6)
    # ---------------- antenas parabólicas (norte): forquilha motorizada + prato + corneta no foco
    PRATOS = []
    for s in (-1, 1):
        A = Vector((s * 0.98, 0.98, 0))
        caixa(B('antena_base', 'concreto'), Vector((A.x, A.y, Z0 + 0.06)), (0.5, 0.5, 0.12))
        cil(B('antena_pedestal', 'amarelo', True), Vector((A.x, A.y, Z0 + 0.12 + 0.45)), 0.13, 0.9, lados=20)
        cil(B('antena_flange', 'ferro', True), Vector((A.x, A.y, Z0 + 0.14)), 0.2, 0.04, lados=20)
        parafusos_em(B('parafusos', 'aco'), [Vector((A.x + math.cos(a) * 0.17, A.y + math.sin(a) * 0.17, Z0 + 0.16)) for a in (k * PI / 4 for k in range(8))], Z)
        cil(B('antena_giro', 'ferro', True), Vector((A.x, A.y, Z0 + 1.06)), 0.18, 0.08, lados=24)
        for k in range(32):                                                # coroa de azimute
            a = k * 2 * PI / 32
            caixa(B('antena_dentes', 'aco'), Vector((A.x + math.cos(a) * 0.185, A.y + math.sin(a) * 0.185, Z0 + 1.06)), (0.025, 0.02, 0.06),
                  Matrix.Rotation(a, 3, 'Z'))
        caixa(B('antena_motor', 'grafite'), Vector((A.x - s * 0.2, A.y - 0.08, Z0 + 0.95)), (0.14, 0.16, 0.18))
        cil(B('antena_motor_aletas', 'ferro', True), Vector((A.x - s * 0.2, A.y - 0.08, Z0 + 0.86)), 0.06, 0.06, lados=12)
        PRATOS.append(A)
    # ---------------- torres de vapor (sul), caldeira e canos
    TV = [Vector((-1.0, -1.0, 0)), Vector((1.0, -1.0, 0))]
    HTV = 2.75
    for t in TV:
        perfil = [(Z0, 0.4), (Z0 + 0.08, 0.4), (Z0 + 0.1, 0.36), (Z0 + 0.8, 0.31), (Z0 + 1.6, 0.27), (Z0 + 2.2, 0.27), (Z0 + HTV - 0.15, 0.3), (Z0 + HTV, 0.31)]
        torno(B('torres_vapor', 'casco' if t.x < 0 else 'galvanizado', True), (t.x, t.y, 0), perfil, 32)
        torno(B('torres_boca', 'escuro', True), (t.x, t.y, 0), [(Z0 + HTV - 0.3, 0.27), (Z0 + HTV + 0.003, 0.27)], 32)
        for zz in (0.35, 0.95, 1.55, 2.15, HTV - 0.1):                     # cintas rebitadas
            r = [r_ for z_, r_ in perfil if z_ <= Z0 + zz][-1]
            # raio aproximado da cinta pela interpolação do perfil
            zs = [p[0] for p in perfil]
            for i in range(len(perfil) - 1):
                if perfil[i][0] <= Z0 + zz <= perfil[i + 1][0]:
                    f = (Z0 + zz - perfil[i][0]) / (perfil[i + 1][0] - perfil[i][0])
                    r = perfil[i][1] + (perfil[i + 1][1] - perfil[i][1]) * f
            toro(B('torres_cintas', 'ferro', True), Vector((t.x, t.y, Z0 + zz)), r + 0.006, 0.014, 48, 6)
            for k in range(12):
                a = k * PI / 6
                curva(B('rebites', 'aco'), Vector((t.x + math.cos(a) * (r + 0.02), t.y + math.sin(a) * (r + 0.02), Z0 + zz)), 0.008, 6)
        # fuligem e crosta de mineral na boca, escorridos
        for k in range(10):
            a = k * 2 * PI / 10 + random.uniform(-0.2, 0.2)
            n = Vector((math.cos(a), math.sin(a), 0))
            escorrido(B('crosta_escorrida', 'crosta'), Vector((t.x, t.y, 0)) + n * 0.313 + Z * (Z0 + HTV - 0.02), n, random.uniform(0.15, 0.5), 0.02)
            if k % 3 == 0:
                escorrido(B('escorridos', 'ferrugem'), Vector((t.x, t.y, 0)) + n * 0.276 + Z * (Z0 + 2.1), n, random.uniform(0.3, 0.7), 0.018)
        for k in range(6):
            a = random.uniform(0, 2 * PI)
            n = Vector((math.cos(a), math.sin(a), 0))
            mancha_em(B('fuligem', 'fuligem'), Vector((t.x, t.y, 0)) + n * 0.31 + Z * (Z0 + HTV - 0.12), 0.07, n, 1.2)
        # porta de inspeção aparafusada (redonda, sem maçaneta)
        n = Vector((-t.x, 0, 0)).normalized() if t.x else Vector((0, -1, 0))
        n = Vector((0, -1, 0))
        cil(B('torres_inspecao', 'zarcao' if t.x < 0 else 'azul_trocado', True), Vector((t.x, t.y, 0)) + n * 0.33 + Z * (Z0 + 0.6), 0.13, 0.03, n, lados=20)
        parafusos_em(B('parafusos', 'aco'), [Vector((t.x, t.y, 0)) + n * 0.345 + Z * (Z0 + 0.6) + Vector((math.cos(a) * 0.105, 0, math.sin(a) * 0.105))
                                             for a in (k * PI / 4 for k in range(8))], n)
    # caldeira horizontal (sul, entre as torres)
    CB = Vector((0, -1.12, Z0 + 0.42))
    tubo(B('caldeira', 'zarcao', True), CB + Vector((-0.42, 0, 0)), CB + Vector((0.42, 0, 0)), 0.27, 32)
    for s in (-1, 1):
        bmesh.ops.create_uvsphere(B('caldeira_tampos', 'zarcao', True), u_segments=32, v_segments=12, radius=1.0,
                                  matrix=Matrix.Translation(CB + Vector((s * 0.42, 0, 0))) @ Matrix.Diagonal((0.1, 0.27, 0.27, 1)))
        toro(B('caldeira_cintas', 'ferro', True), CB + Vector((s * 0.3, 0, 0)), 0.275, 0.014, 48, 6, rot_de(Vector((1, 0, 0))))
        caixa(B('caldeira_berco', 'ferro'), Vector((CB.x + s * 0.25, CB.y, Z0 + 0.08)), (0.08, 0.42, 0.16))
    chapa(B('remendos', 'casco'), B('parafusos', 'aco'), CB + Vector((0.1, -0.27, 0.05)), 0.2, 0.14, Vector((0, -1, 0)), giro=0.08)
    for k in range(4):
        escorrido(B('escorridos', 'ferrugem'), CB + Vector((-0.3 + 0.2 * k, -0.27, 0.05)), Vector((0, -1, 0)), random.uniform(0.1, 0.22))
    # manômetro e válvula de alívio no alto da caldeira
    cil(B('manometro', 'ferro', True), CB + Vector((-0.15, -0.05, 0.36)), 0.055, 0.03, Vector((0, -1, 0.4)), lados=20)
    cil(B('manometro_face', 'face_mostrador'), CB + Vector((-0.15, -0.065, 0.366)), 0.046, 0.004, Vector((0, -1, 0.4)), lados=20)
    tubo(B('manometro_tubo', 'cobre', True), CB + Vector((-0.15, 0.0, 0.26)), CB + Vector((-0.15, -0.04, 0.34)), 0.01, 8)
    cil(B('valvula_alivio', 'cromo', True), CB + Vector((0.2, 0, 0.32)), 0.04, 0.12, lados=12)
    cil(B('valvula_alivio', 'cromo', True), CB + Vector((0.2, 0, 0.4)), 0.025, 0.06, lados=12)
    # canos de vapor: caldeira → base de cada torre (com flanges e válvula atuada)
    for s in (-1, 1):
        t = TV[0 if s < 0 else 1]
        p0 = CB + Vector((s * 0.28, 0.0, 0.25))
        pts = [p0, p0 + Vector((0, 0, 0.18)), Vector((t.x - s * 0.02, CB.y, p0.z + 0.18)), Vector((t.x - s * 0.02, t.y + 0.0, p0.z + 0.18))]
        pts = [p0, p0 + Vector((0, 0, 0.2)), Vector((t.x - s * 0.34, CB.y, p0.z + 0.2)), Vector((t.x - s * 0.34, t.y + 0.05, Z0 + 0.6))]
        pts = [p0, p0 + Vector((0, 0, 0.16)), Vector((t.x - s * 0.36, p0.y, p0.z + 0.16)), Vector((t.x - s * 0.3, p0.y, p0.z + 0.16))]
        cano(B('canos_vapor', 'aco', True), B('flanges', 'ferro', True), pts, 0.045)
        va = Vector((s * 0.48, p0.y, p0.z + 0.16))
        caixa(B('valvulas_corpo', 'ferro'), va, (0.12, 0.12, 0.12))
        caixa(B('valvulas_atuador', 'amarelo'), va + Vector((0, 0, 0.16)), (0.14, 0.12, 0.14))
        mangueira(B('cabos', 'cabo'), bezier(va + Vector((0, 0.06, 0.2)), va + Vector((0, 0.2, 0.3)), Vector((s * 0.4, -0.6, Z0 + 0.2)),
                                              Vector((s * 0.35, -0.6, Z0 + 0.02)), 8), 0.01)
        mancha(B('oleo_chao', 'oleo'), (t.x - s * 0.1, t.y + 0.35), 0.1, Z0 + 0.002)
    # entrada de água pela borda sul (porta de fluido) → bomba → caldeira
    cano(B('canos_agua', 'galvanizado', True), B('flanges', 'ferro', True),
         [Vector((-0.45, -1.52, Z0 + 0.12)), Vector((-0.45, -1.42, Z0 + 0.12)), Vector((-0.45, -1.42, Z0 + 0.12))], 0.04)
    BP = Vector((-0.52, -1.39, Z0 + 0.0))
    cano(B('canos_agua', 'galvanizado', True), B('flanges', 'ferro', True),
         [Vector((0.45, -1.55, Z0 + 0.12)), Vector((0.45, -1.43, Z0 + 0.12)), Vector((0.32, -1.43, Z0 + 0.12)), Vector((0.32, -1.3, Z0 + 0.3))], 0.04)
    caixa(B('bomba', 'azul_trocado'), Vector((0.62, -1.3, Z0 + 0.13)), (0.2, 0.18, 0.22))
    cil(B('bomba_motor', 'grafite', True), Vector((0.62, -1.3, Z0 + 0.3)), 0.07, 0.14, lados=16)
    for k in range(8):
        a = k * PI / 4
        tubo(B('bomba_aletas', 'ferro'), Vector((0.62 + math.cos(a) * 0.075, -1.3 + math.sin(a) * 0.075, Z0 + 0.24)),
             Vector((0.62 + math.cos(a) * 0.075, -1.3 + math.sin(a) * 0.075, Z0 + 0.36)), 0.008, 4)
    poca((0.2, -1.33), 0.1)
    # ---------------- canhões de calor (leste e oeste)
    CAN = []
    for s in (-1, 1):
        C0 = Vector((s * 1.12, 0.05, Z0))
        caixa(B('canhao_base', 'grafite'), C0 + Vector((0, 0, 0.12)), (0.5, 0.62, 0.24))
        for sy in (-1, 1):                                                 # munhões
            caixa(B('canhao_munhao', 'amarelo'), C0 + Vector((0, sy * 0.25, 0.42)), (0.12, 0.06, 0.4))
            cil(B('canhao_eixo', 'aco', True), C0 + Vector((0, sy * 0.25, 0.58)), 0.06, 0.1, Vector((0, 1, 0)), lados=16)
        eixo = Vector((s * math.cos(math.radians(55)), 0, math.sin(math.radians(55))))
        piv = C0 + Vector((0, 0, 0.58))
        a0 = piv - eixo * 0.45
        a1 = piv + eixo * 0.75
        tubo(B('canhao_corpo', 'casco', True), a0, piv + eixo * 0.2, 0.2, 28)
        tubo(B('canhao_cano', 'ferro', True), piv + eixo * 0.2, a1, 0.15, 28)
        cil(B('canhao_boca', 'ferro', True), a1, 0.19, 0.09, eixo, lados=28, r2=0.21)
        cil(B('canhao_interior', 'escuro', True), a1 + eixo * 0.046, 0.18, 0.004, eixo, lados=28)
        for j in range(4):                                                 # resistências em brasa dentro da boca
            toro(B('canhao_brasa', 'brasa_forte' if j < 2 else 'brasa', True), a1 - eixo * (0.02 + j * 0.06), 0.13 - 0.02 * j, 0.012, 32, 6, rot_de(eixo))
        for j in range(10):                                                # aletas de dissipação
            toro(B('canhao_aletas', 'aco', True), piv + eixo * (0.25 + j * 0.045), 0.185, 0.012, 32, 6, rot_de(eixo))
        tubo(B('canhao_traseira', 'grafite', True), a0 - eixo * 0.08, a0, 0.16, 24)
        for k in range(6):                                                 # grelha de admissão atrás
            a = k * PI / 3
            t1 = eixo.orthogonal().normalized()
            t2 = eixo.cross(t1)
            tubo(B('canhao_grade', 'ferro'), a0 - eixo * 0.085, a0 - eixo * 0.085 + (t1 * math.cos(a) + t2 * math.sin(a)) * 0.15, 0.008, 4)
        # fuligem em volta da boca e escorrendo pelo cano
        for k in range(8):
            a = k * PI / 4
            t1 = Vector((0, 1, 0))
            t2 = eixo.cross(t1)
            n = (t1 * math.cos(a) + t2 * math.sin(a))
            mancha_em(B('fuligem', 'fuligem'), a1 - eixo * random.uniform(0.0, 0.25) + n * 0.152, 0.05, n, 1.5)
        # cabos de força e mangueira de combustível
        feixe(B('cabos', 'cabo'), B('abracadeiras', 'aco'),
              bezier(a0 + Vector((0, 0.1, -0.1)), a0 + Vector((-s * 0.1, 0.25, -0.35)), C0 + Vector((-s * 0.35, 0.42, 0.15)),
                     C0 + Vector((-s * 0.55, 0.42, 0.06)), 10), Vector((0, 0, 1)), 3, 0.014, 4)
        CAN.append((a1, eixo))
    # ---------------- armário de comando (norte, entre as antenas)
    caixa_de(B('armario', 'amarelo'), (-0.42, 1.18, Z0), (0.42, 1.46, Z0 + 1.1))
    caixa_de(B('armario_tampa', 'grafite'), (-0.44, 1.16, Z0 + 1.1), (0.44, 1.48, Z0 + 1.15))
    for j in range(5):
        caixa(B('grelha', 'escuro'), Vector((-0.2 + j * 0.1, 1.175, Z0 + 0.85)), (0.06, 0.004, 0.15))
    chapa(B('remendos', 'zarcao'), B('parafusos', 'aco'), Vector((0.2, 1.18, Z0 + 0.45)), 0.2, 0.25, Vector((0, -1, 0)), giro=0.06)
    for j, m in enumerate(('led_verde', 'led_verde', 'led_ambar', 'led_verm')):
        cil(B(m, m), Vector((-0.3 + j * 0.05, 1.175, Z0 + 1.0)), 0.011, 0.006, Vector((0, -1, 0)), lados=10)
    caixa(B('estencil', 'tinta'), Vector((-0.15, 1.176, Z0 + 0.62)), (0.22, 0.003, 0.05))
    cil(B('olho', 'olho'), Vector((0.3, 1.175, Z0 + 0.98)), 0.025, 0.01, Vector((0, -1, 0)), lados=14)
    # feixes de cabo: armário → antenas, cubo, canhões (por eletrocalha no chão)
    for s in (-1, 1):
        feixe(B('cabos', 'cabo'), B('abracadeiras', 'aco'),
              bezier(Vector((s * 0.42, 1.3, Z0 + 0.6)), Vector((s * 0.6, 1.3, Z0 + 0.6)), Vector((s * 0.85, 1.05, Z0 + 0.4)),
                     Vector((s * 0.88, 0.98, Z0 + 0.4)), 8), Vector((0, 0, 1)), 3, 0.014, 3)
    for a, b in ((Vector((-0.38, 1.18, Z0)), Vector((-0.38, 0.55, Z0))), (Vector((0.38, 1.18, Z0)), Vector((0.38, 0.55, Z0)))):
        caixa_de(B('eletrocalha', 'galvanizado'), (a.x - 0.07, b.y, Z0), (a.x + 0.07, a.y, Z0 + 0.012))
        for s in (-1, 1):
            caixa_de(B('eletrocalha', 'galvanizado'), (a.x + s * 0.07 - 0.006, b.y, Z0), (a.x + s * 0.07 + 0.006, a.y, Z0 + 0.07))
        for k in range(3):
            mangueira(B('cabos', 'cabo'), [Vector((a.x - 0.03 + 0.03 * k, a.y, Z0 + 0.03)), Vector((a.x - 0.03 + 0.03 * k, b.y, Z0 + 0.03)),
                                           Vector((a.x * 0.8 - 0.03 + 0.03 * k, 0.48, Z0 + 0.3))], 0.013)
    # feixe que sobe pelo braço nordeste até o cubo e o estator
    caminho = BR[0]
    off = Vector((0, 0, 0.075))
    lat = Vector((-math.sin(PI / 4), math.cos(PI / 4), 0))
    feixe(B('cabos', 'cabo'), B('abracadeiras', 'aco'), [p + off for p in caminho[1:-1]], lat, 3, 0.013, 3)
    # ---------------- pó e poças (dentro do círculo seco — pouca água), pedras
    for c, r in (((0.5, 0.6), 0.1), ((-0.8, 0.3), 0.08)):
        poca(c, r)
    for k in range(50):
        r = random.uniform(2.2, 60.0)
        a = random.uniform(0, 2 * PI)
        pedra(B('pedras', 'pedra'), (math.cos(a) * r, math.sin(a) * r, 0.0), random.uniform(0.06, 0.4))
    bloco((8.0, 6.0), (3.0, 2.4, 2.2), 'bloco', chamine=True)
    bloco((-9.0, 5.0), (2.6, 2.6, 3.0), 'bloco_cinza', tanque=True)
    bloco((-7.0, -8.0), (3.5, 2.0, 1.8), 'bloco')
    bloco((11.0, -5.0), (2.2, 4.0, 2.6), 'bloco_cinza', chamine=True)
    bloco((2.0, 14.0), (3.0, 2.0, 2.0), 'bloco', tanque=True)
    bloco((-16.0, -2.0), (2.4, 3.0, 2.4), 'bloco_cinza')
    descarregar()
    return dict(ZE=ZE, RE=RE, ZH=ZH, PRATOS=PRATOS, TV=TV, HTV=HTV, CAN=CAN, CORN=CORN)


def parabolica(nome, A, az, el):
    """Antena na forquilha: devolve o vazio que mira (az, el); prato f=0,36 m, Ø 1,3 m, corneta no foco em quatro pernas."""
    piv = bpy.data.objects.new(nome + '_azimute', None)
    sc.collection.objects.link(piv)
    piv.location = Vector((A.x, A.y, Z0 + 1.1))
    piv.rotation_euler = (0, 0, az)
    garfo = bmesh.new()
    caixa(garfo, Vector((0, 0, 0.04)), (0.34, 0.28, 0.06))
    for s in (-1, 1):
        caixa(garfo, Vector((0, s * 0.2, 0.28)), (0.12, 0.05, 0.5))
    obj(nome + '_garfo', garfo, 'amarelo', piv)
    elv = bpy.data.objects.new(nome + '_elevacao', None)
    sc.collection.objects.link(elv)
    elv.parent = piv
    elv.location = Vector((0, 0, 0.48))
    elv.rotation_euler = (0, PI / 2 - el, 0)                               # z local aponta para o céu inclinado
    f = 0.36
    R = 0.65
    perfil = [((r * r) / (4 * f), r) for r in [0.06 + (R - 0.06) * i / 14 for i in range(15)]]
    bm = bmesh.new()
    torno(bm, (0, 0, 0.0), [(z + 0.08, r) for z, r in perfil], 40, tampas=False)
    torno(bm, (0, 0, 0.0), [(z + 0.055, r) for z, r in perfil], 40, tampas=False)
    o = obj(nome + '_prato', bm, 'prato', elv)
    suavizar(o)
    for f_ in o.data.polygons:
        f_.use_smooth = True
    bm = bmesh.new()
    zr = (R * R) / (4 * f)
    toro(bm, Vector((0, 0, zr + 0.068)), R, 0.018, 64, 8)
    for k in range(12):                                                    # costelas atrás do prato
        a = k * PI / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [d * r + Vector((0, 0, (r * r) / (4 * f) + 0.03)) for r in (0.1, 0.3, 0.5, R)]
        for a_, b_ in zip(pts, pts[1:]):
            viga(bm, a_, b_, 0.025)
    cil(bm, Vector((0, 0, 0.0)), 0.1, 0.16, lados=20)                       # cubo do prato
    for s in (-1, 1):
        cil(bm, Vector((0, s * 0.17, 0.0)), 0.05, 0.1, Vector((0, 1, 0)), lados=14)
    o = obj(nome + '_costelas', bm, 'aco', elv)
    suavizar(o)
    bm = bmesh.new()
    foco = Vector((0, 0, f + 0.08))
    for k in range(4):                                                     # quatro pernas até a corneta
        a = k * PI / 2 + PI / 4
        p = Vector((math.cos(a) * R * 0.92, math.sin(a) * R * 0.92, (R * 0.92) ** 2 / (4 * f) + 0.08))
        tubo(bm, p, foco + Vector((math.cos(a), math.sin(a), 0)) * 0.05, 0.012, 8)
    o = obj(nome + '_pernas', bm, 'galvanizado', elv)
    suavizar(o)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.09, radius2=0.03, depth=0.16,
                          matrix=Matrix.Translation(foco + Vector((0, 0, -0.04))) @ Matrix.Rotation(PI / 4, 4, 'Z'))
    cil(bm, foco + Vector((0, 0, 0.07)), 0.05, 0.1, lados=16)
    obj(nome + '_corneta', bm, 'aluminio', elv)
    bm = bmesh.new()
    cil(bm, foco + Vector((0, 0, -0.121)), 0.06, 0.003, lados=4)
    obj(nome + '_corneta_boca', bm, 'olho', elv)
    bm = bmesh.new()                                                       # sujeira: manchas de ferrugem e fuligem no prato
    for k in range(9):
        r = random.uniform(0.15, 0.6)
        a = random.uniform(0, 2 * PI)
        p = Vector((math.cos(a) * r, math.sin(a) * r, (r * r) / (4 * f) + 0.0825))
        n = Vector((-p.x / (2 * f), -p.y / (2 * f), 1)).normalized()
        mancha_em(bm, p, random.uniform(0.04, 0.09), n, 1.3)
    obj(nome + '_manchas', bm, 'ferrugem', elv)
    # cabo da corneta descendo por uma perna até o cubo
    bm = bmesh.new()
    a = PI / 4
    p = Vector((math.cos(a) * R * 0.92, math.sin(a) * R * 0.92, (R * 0.92) ** 2 / (4 * f) + 0.1))
    mangueira(bm, bezier(foco + Vector((0.04, 0.04, 0.05)), foco.lerp(p, 0.5) + Vector((0, 0, 0.02)), p, Vector((0.12, 0.12, 0.02)), 10), 0.01)
    obj(nome + '_cabo', bm, 'cabo', elv)
    return piv, elv, foco


def animar_regulador(info):
    ZE, RE, ZH = info['ZE'], info['RE'], info['ZH']
    # núcleo de cristal grande flutuando
    cr = bpy.data.objects.new('nucleo', None)
    sc.collection.objects.link(cr)
    cr.location = Vector((0, 0, ZE))
    bm = bmesh.new()
    rr = [0.2 * (1 + random.uniform(-0.1, 0.1)) for _ in range(8)]
    an1 = [bm.verts.new((math.cos(k * PI / 4) * rr[k], math.sin(k * PI / 4) * rr[k], -0.16)) for k in range(8)]
    an2 = [bm.verts.new((math.cos(k * PI / 4 + 0.1) * rr[k] * 0.95, math.sin(k * PI / 4 + 0.1) * rr[k] * 0.95, 0.18)) for k in range(8)]
    topo = bm.verts.new((0.02, -0.01, 0.62))
    fundo = bm.verts.new((-0.01, 0.015, -0.5))
    for k in range(8):
        j = (k + 1) % 8
        bm.faces.new((an1[k], an1[j], an2[j], an2[k]))
        bm.faces.new((an2[k], an2[j], topo))
        bm.faces.new((an1[j], an1[k], fundo))
    obj('nucleo_corpo', bm, 'cristal', cr)
    lasc = bmesh.new()                                                     # lascas menores orbitando presas ao núcleo
    for k in range(5):
        a = k * 2 * PI / 5
        c = Vector((math.cos(a) * 0.34, math.sin(a) * 0.34, random.uniform(-0.2, 0.2)))
        res = bmesh.ops.create_icosphere(lasc, subdivisions=0, radius=0.05)
        for v in res['verts']:
            v.co = c + Vector((v.co.x, v.co.y, v.co.z * 2.2))
    obj('lascas', lasc, 'cristal', cr)
    lc, lcd = luz_ponto('Luz do núcleo', VIOLETA, 0.2)
    lc.location = Vector((0, 0, ZE))
    # dois anéis levitando inclinados (sem contato) girando em eixos diferentes
    aneis = []
    for i, (R, incl) in enumerate(((0.74, 0.5), (0.6, -0.75))):
        e = bpy.data.objects.new('anel_lev_%d' % i, None)
        sc.collection.objects.link(e)
        e.location = Vector((0, 0, ZE))
        e2 = bpy.data.objects.new('anel_lev_incl_%d' % i, None)
        sc.collection.objects.link(e2)
        e2.parent = e
        e2.rotation_euler = (incl, 0, 0)
        bm = bmesh.new()
        toro(bm, Vector((0, 0, 0)), R, 0.035, 96, 12)
        suavizar(obj('anel_lev', bm, 'cromo' if i == 0 else 'aluminio', e2))
        bm = bmesh.new()
        for k in range(16):                                                # bobinas e blocos de ímã no anel
            a = k * 2 * PI / 16
            p = Vector((math.cos(a), math.sin(a), 0)) * R
            if k % 2:
                caixa(bm, p, (0.07, 0.07, 0.1), Matrix.Rotation(a, 3, 'Z'))
            else:
                tg = Vector((-math.sin(a), math.cos(a), 0))
                toro(bm, p, 0.05, 0.012, 16, 6, rot_de(tg))
        obj('anel_lev_bobinas', bm, 'bobina' if i == 0 else 'grafite', e2)
        aneis.append(e)
    # arcos curtos do estator para os anéis (sustentação elétrica)
    arcos = []
    random.seed(21)
    for k in range(6):
        a = random.uniform(0, 2 * PI)
        p0 = Vector((math.cos(a), math.sin(a), 0)) * (RE - 0.07) + Vector((0, 0, ZE))
        p1 = Vector((math.cos(a + 0.3), math.sin(a + 0.3), 0)) * 0.76 + Vector((0, 0, ZE + random.uniform(-0.3, 0.3)))
        arcos += descarga('arco_estator', caminho_raio(p0, p1, 0.05, 7), 0.006, halo=True)
    # coluna de luz subindo do cubo para o buraco
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.5)), 1.0, 1.0, lados=20)
    col = obj('coluna', bm, 'coluna')
    col.location = Vector((0, 0, ZH + 0.6))
    col.scale = (0.45, 0.45, 60)
    col.visible_shadow = False
    # antenas parabólicas
    pratos = []
    for i, A in enumerate(info['PRATOS']):
        az = math.atan2(A.y, A.x)
        pratos.append((parabolica('antena_%d' % i, A, az, math.radians(62)), az))
    # frentes de onda subindo de cada prato (anéis)
    ondas = []
    for (piv, elv, foco), az in pratos:
        for k in range(4):
            bm = bmesh.new()
            toro(bm, Vector((0, 0, 0)), 1.0, 0.014, 64, 6)
            o = obj('onda', bm, 'onda')
            o.parent = elv
            o.visible_shadow = False
            ondas.append((o, foco, k))
    # vapor saindo das torres
    vapores = []
    for t in info['TV']:
        for k in range(6):
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
            o = obj('vapor', bm, 'vapor')
            vapores.append((o, t, k))
    # ar quente dos canhões (volume âmbar fraco num cone)
    for a1, eixo in info['CAN']:
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.5)), 1.0, 1.0, lados=20, r2=1.5)
        o = obj('ar_quente', bm, 'ar_quente')
        o.location = a1 + eixo * 0.05
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = eixo.to_track_quat('Z', 'Y')
        o.scale = (0.18, 0.18, 2.6)
        o.visible_shadow = False
        lo, ld = luz_ponto('Boca do canhão', (1.0, 0.45, 0.12), 0.1)
        lo.location = a1 + eixo * 0.1
        ld.energy = 60
    # raios caindo do lado de fora (na tempestade)
    fora = []
    for k, (az, r) in enumerate(((2.05, 98.0), (4.4, 110.0), (1.2, 104.0), (5.6, 100.0))):
        p = Vector((math.cos(az) * r, math.sin(az) * r, 0))
        fora.append(descarga('raio_fora', caminho_raio(p + Vector((random.uniform(-8, 8), random.uniform(-8, 8), 62)), p, 6.0, 30, semente=30 + k),
                             0.25, ramos=6, compr=0.3) + [None])
        lo, ld = luz_ponto('Raio fora', RAIO_COR, 1.0)
        lo.location = p + Vector((0, 0, 30))
        fora[-1][-1] = ld
    nucleo_bsdf = base3d.M['cristal'].node_tree.nodes['Principled BSDF']
    onda_em = base3d.M['onda'].node_tree.nodes['em'].inputs['Strength']
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr)
        cr.rotation_euler = (0, 0, -2 * PI * fr)
        cr.location = Vector((0, 0, ZE + 0.03 * math.sin(2 * PI * fr)))
        keyall(cr, 'rotation_euler', 'location', q=q)
        nucleo_bsdf.inputs['Emission Strength'].default_value = 0.9 + 1.4 * pulso
        nucleo_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
        chave_luz(lcd, 60 + 80 * pulso, q)
        aneis[0].rotation_euler = (0, 0, 2 * PI * fr)
        aneis[1].rotation_euler = (0, 0, -4 * PI * fr)
        keyall(aneis[0], 'rotation_euler', q=q)
        keyall(aneis[1], 'rotation_euler', q=q)
        for j, o in enumerate(arcos):
            ocultar(o, ((q + j * 3) // 4) % 3 == 0, q)
        for i, ((piv, elv, foco), az) in enumerate(pratos):                # antenas corrigem a mira devagar
            piv.rotation_euler = (0, 0, az + 0.06 * math.sin(2 * PI * fr + i))
            elv.rotation_euler = (0, PI / 2 - math.radians(62) + 0.03 * math.sin(2 * PI * 2 * fr + i), 0)
            keyall(piv, 'rotation_euler', q=q)
            keyall(elv, 'rotation_euler', q=q)
        for o, foco, k in ondas:
            u = (fr * 2 + k / 4) % 1.0
            o.location = foco + Vector((0, 0, 0.2 + u * 2.8))
            s = 0.22 + u * 0.75
            o.scale = (s, s, s)
            keyall(o, 'location', 'scale', q=q)
        for o, t, k in vapores:
            u = (fr + k / 6) % 1.0
            o.location = Vector((t.x + 0.35 * u * u * (1 if t.x > 0 else -1), t.y - 0.2 * u, Z0 + info['HTV'] + 0.12 + 2.2 * u))
            s = 0.16 + 0.5 * u
            o.scale = (s, s, s * 0.9)
            keyall(o, 'location', 'scale', q=q)
        for k, obs in enumerate(fora):
            ld = obs[-1]
            vis = ((q - 20 - (0, 1, 40, 70)[k]) % 96) in (0, 1, 3, 4, 5)
            for o in obs[:-1]:
                ocultar(o, not vis, q)
            chave_luz(ld, 2.0e5 if vis else 0.0, q)


# =================================================================== cena
if QUAL == 'cupula':
    base3d.M['cupula'] = cupula_mat()
    base3d.M['nuvem'] = nuvem_mat('Nuvem de tempestade', 0.09, 46.0, 86.0, escala=0.012)
else:
    base3d.M['nuvem'] = nuvem_mat('Nuvem de tempestade', 0.11, 58.0, 98.0, furo=R_FURO, escala=0.01)
    base3d.M['vapor'] = base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 7.0, 2.9, 5.6)
    base3d.M['ar_quente'] = feixe_vol_mat('Ar quente', (1.0, 0.35, 0.06), 0.25, 0.9, (0.5, 0.3, 0.2))
    base3d.M['coluna'] = feixe_vol_mat('Coluna', VIOLETA, 0.06, 1.4)
base3d.M['cortina'] = cortina_mat('Cortina de chuva', 0.016 if QUAL != 'cupula' else 0.007)
base3d.M['terra'] = terra_mat('Terra', 0.0 if QUAL == 'cupula' else R_FURO)

if QUAL == 'cupula':
    INFO = construir_cupula()
    T_RAIO = animar_cupula(INFO)
else:
    INFO = construir_regulador()
    animar_regulador(INFO)

# chão
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (1400, 1400, 1.0))
chao = obj('chao', bm, 'terra')
# nuvem (camada de volume; só a câmera e o espalhamento a veem — não faz sombra)
bm = bmesh.new()
if QUAL == 'cupula':
    caixa(bm, (0, 0, 66.0), (1300, 1300, 40.0))
else:
    caixa(bm, (0, 0, 78.0), (1300, 1300, 40.0))
nuvem = obj('nuvem', bm, 'nuvem')
nuvem.visible_shadow = False
nuvem.visible_diffuse = False
nuvem.visible_glossy = False

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
wn = mundo.node_tree
bg = wn.nodes['Background']
geo_w = no(wn, 'ShaderNodeTexCoord')
sep_w = no(wn, 'ShaderNodeSeparateXYZ')
wn.links.new(geo_w.outputs['Generated'], sep_w.inputs[0])
grad = no(wn, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.6})
wn.links.new(sep_w.outputs['Z'], grad.inputs['Value'])
cor_w = no(wn, 'ShaderNodeMix', data_type='RGBA')
wn.links.new(grad.outputs['Result'], cor_w.inputs[0])
wn.links.new(cor_w.outputs[2], bg.inputs['Color'])

if QUAL == 'cupula':
    cor_w.inputs[6].default_value = (0.05, 0.055, 0.065, 1)
    cor_w.inputs[7].default_value = (0.09, 0.1, 0.12, 1)
    bg.inputs['Strength'].default_value = 1.0
    luz_d = bpy.data.lights.new('Céu encoberto', 'SUN')                    # luz difusa da tempestade
    luz_d.energy = 0.5
    luz_d.angle = math.radians(40)
    luz_d.color = (0.7, 0.75, 0.9)
    lo = bpy.data.objects.new('Céu encoberto', luz_d)
    sc.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(25), 0, math.radians(-50))
else:
    cor_w.inputs[6].default_value = (0.2, 0.22, 0.25, 1)
    cor_w.inputs[7].default_value = (0.2, 0.38, 0.85, 1)
    bg.inputs['Strength'].default_value = 1.0
    # tampa invisível com o furo: só bloqueia luz (sol e céu) fora do círculo
    bm = bmesh.new()
    res = bmesh.ops.create_circle(bm, cap_ends=False, segments=96, radius=R_FURO)
    ext = bmesh.ops.create_circle(bm, cap_ends=False, segments=96, radius=700)
    vi, ve = res['verts'], ext['verts']
    for k in range(96):
        j = (k + 1) % 96
        bm.faces.new((vi[k], vi[j], ve[j], ve[k]))
    for v in bm.verts:
        v.co.z = 57.0
    tampa = obj('tampa_sombra', bm, 'escuro')
    tampa.visible_camera = False
    tampa.visible_diffuse = False
    tampa.visible_glossy = False
    tampa.visible_transmission = False
    tampa.visible_volume_scatter = False
    sol = bpy.data.lights.new('Sol', 'SUN')
    sol.energy = 3.0
    sol.angle = math.radians(1.5)
    sol.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new('Sol', sol)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(16), 0, math.radians(-30))

# cortina de chuva: anel de volume em volta (do círculo limpo, no regulador; da cúpula, na tempestade)
if True:
    bm = bmesh.new()
    vi = []
    R_IN, Z_TOP = (R_FURO + 8, 70.0) if QUAL != 'cupula' else (110.0, 58.0)
    for z in (0.0, Z_TOP):
        for rr_ in (R_IN, 420.0):
            vi.append([bm.verts.new((math.cos(k * 2 * PI / 96) * rr_, math.sin(k * 2 * PI / 96) * rr_, z)) for k in range(96)])
    (bi, be, ti, te) = vi
    for k in range(96):
        j = (k + 1) % 96
        bm.faces.new((bi[j], bi[k], be[k], be[j]))
        bm.faces.new((ti[k], ti[j], te[j], te[k]))
        bm.faces.new((bi[k], bi[j], ti[j], ti[k]))
        bm.faces.new((be[j], be[k], te[k], te[j]))
    cortina = obj('cortina_chuva', bm, 'cortina')
    cortina.visible_shadow = False

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
sc.cycles.transparent_max_bounces = 32
sc.cycles.volume_bounces = 0
sc.cycles.volume_step_rate = 1.5
sc.cycles.volume_max_steps = 256
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = 0.0
cam_d = bpy.data.cameras.new('Cam')
cam_d.clip_end = 2000
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def foto(nome, fr, pos, alvo, lente, res, amostras=128, expo=0.0):
    sc.cycles.samples = amostras
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.exposure = expo
    sc.frame_set(fr)
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError:                                                   # GPU cheia (outros estudos): vai na CPU
        sc.cycles.device = 'CPU'
        bpy.ops.render.render(write_still=True)


if MODO == 'foto':
    quais = ARGS[2:] or (['0', 'desvio'] if QUAL == 'cupula' else ['0', 'ceu'])
    if QUAL == 'cupula':
        if '0' in quais:
            foto('cupula_raios_0.png', 12, (6.0, -7.4, 2.9), (0.0, 0.0, 3.7), 28, (1100, 1300), 128, 0.7)
        if 'desvio' in quais:
            a = math.radians(248)
            foto('cupula_raios_desvio.png', T_RAIO + 3, (math.cos(a) * 64, math.sin(a) * 64, 3.5), (0.0, 0.0, 19.0), 22, (1600, 1000), 128, -0.3)
    else:
        if '0' in quais:
            foto('regulador_clima_0.png', 20, (2.4, -8.6, 2.5), (0.0, 0.0, 2.6), 27, (1100, 1300), 128, -0.5)
        if 'ceu' in quais:
            foto('regulador_clima_ceu.png', 20, (4.6, -6.6, 0.9), (-0.8, 1.2, 9.0), 14, (1100, 1400), 128, -0.5)
if MODO == 'teste':
    v = [float(x) for x in ARGS[2:]]
    foto('clima3x3_teste.png', int(v[7]), v[0:3], v[3:6], v[6], (900, 900), 48, v[8] if len(v) > 8 else 0.0)
print('CLIMA 3x3 ok')
