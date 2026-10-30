"""Estudo isolado (fora do jogo): duas máquinas de clima 2×2 da IA, sem portas de item/fluido.

SEMEADOR DE NUVENS (`semeadura_nuvens`): chama chuva num raio de 40 m.
  Canhão vertical de semeadura: pedestal, culatra que recua sobre dois pistões, cano com jaqueta e freio de boca,
  três bobinas violeta de aceleração (toque da IA) e torre de quatro pernas com colar-bucha. Carrossel de 10
  cartuchos de iodeto ao lado, calha de alimentação com soquete. Cada disparo ejeta UM estojo vazio modelado
  (aro, ranhura, espoleta, boca queimada), quente, girando, com fiapo de fumaça, quicando e parando no chão com uma
  última fumacinha. Rastros dos cartuchos sobem até a nuvem que escurece; estouros violeta na base da nuvem; chuva
  só dentro do círculo (chão molhado só ali). Dois queimadores de solo (chama + pluma de partículas) alimentados pelo
  tanque de reagente (bomba, válvulas, canos com flanges) e garrafas de pressão.
  Sujeira: fuligem, estojos vazios no chão, ferrugem, óleo, remendos, chapa trocada, números apagados.

DEFLETOR DE VENTO (`controle_vento`): fixa a direção do vento num raio de 40 m.
  Coluna octogonal giratória sobre coroa dentada (dois motorredutores fixos), dois ventiladores dutados com
  grade e motor, cascata de cinco palhetas enormes orientáveis, cada uma com seu pistão (camisa no quadro, haste no
  chifre da palheta, mangueira do distribuidor). No topo: biruta, anemômetro e domo-sensor violeta da IA.
  Sujeira: poeira, folhas e grama voando todas na mesma direção forçada; capim deitado; linhas de fluxo
  translúcidas saindo do defletor em leque (toque da IA).

Uso: blender -b --python estudo_clima_2x2.py -- foto <semeador|defletor> [nome_da_foto ...]
     blender -b --python estudo_clima_2x2.py -- teste <semeador|defletor> <formando|chuva|-> x y z ax ay az lente quadro"""
import bpy, bmesh, math, os, sys, random, time
T0 = time.time()


def marca(t):
    print('MARCA %-24s %.1fs' % (t, time.time() - T0), flush=True)
from mathutils import Vector, Matrix, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
ZL = 0.12                     # topo da laje

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto', 'semeador']
MODO = args[0]
MAQ = args[1] if len(args) > 1 else 'semeador'
random.seed(53 if MAQ == 'semeador' else 71)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def liso(o):
    for pg in o.data.polygons:
        pg.use_smooth = True
    return o


def base_de(eixo):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    return q @ X, q @ Y, q @ Z


def toro(bm, centro, R, r, eixo=Z, nR=48, nr=12):
    u, v, w = base_de(eixo)
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = u * math.cos(a) + v * math.sin(a)
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + w * (r * math.sin(b)))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, Bq = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], Bq[(j + 1) % nr], Bq[j]))


def torno(bm, perfil, c=(0, 0, 0), eixo=Z, n=24):
    """Sólido de revolução: perfil = [(z ao longo do eixo, r)]; r = 0 vira polo."""
    u, v, w = base_de(eixo)
    c = Vector(c)
    aneis = []
    for z, r in perfil:
        if r < 1e-6:
            aneis.append([bm.verts.new(c + w * z)])
        else:
            aneis.append([bm.verts.new(c + w * z + (u * math.cos(a) + v * math.sin(a)) * r) for a in (k * 2 * PI / n for k in range(n))])
    for A, Bq in zip(aneis, aneis[1:]):
        if len(A) == 1 and len(Bq) == 1:
            continue
        if len(A) == 1:
            for k in range(n):
                bm.faces.new((A[0], Bq[k], Bq[(k + 1) % n]))
        elif len(Bq) == 1:
            for k in range(n):
                bm.faces.new((A[(k + 1) % n], A[k], Bq[0]))
        else:
            for k in range(n):
                bm.faces.new((A[k], A[(k + 1) % n], Bq[(k + 1) % n], Bq[k]))


def esfera(bm, c, r, seg=16):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def octo(bm, c, apo, z0, z1, n=8):
    R = apo / math.cos(PI / n)
    vs0 = [bm.verts.new((c[0] + R * math.cos(PI / n + k * 2 * PI / n), c[1] + R * math.sin(PI / n + k * 2 * PI / n), z0)) for k in range(n)]
    vs1 = [bm.verts.new((v.co.x, v.co.y, z1)) for v in vs0]
    bm.faces.new(list(reversed(vs0)))
    bm.faces.new(vs1)
    for k in range(n):
        bm.faces.new((vs0[k], vs0[(k + 1) % n], vs1[(k + 1) % n], vs1[k]))


def quat_zx(zd, xd):
    zd = Vector(zd).normalized()
    xd = (Vector(xd) - zd * Vector(xd).dot(zd)).normalized()
    yd = zd.cross(xd)
    return Matrix((xd, yd, zd)).transposed().to_quaternion()


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ baldes de malha por (nome, material, grupo)
GR = {}
BMS = {}


def grupo(nome, loc=(0, 0, 0), pai=None, rz=0.0):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = (0, 0, rz)
    if pai:
        e.parent = GR[pai]
    GR[nome] = e
    return e


def B(nome, mat, g='base', lis=False):
    k = (nome, mat, g, lis)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def fechar():
    feitos = []
    for (nome, mat, g, lis), bm in list(BMS.items()):
        if len(bm.verts) == 0:
            bm.free()
            continue
        o = obj(nome, bm, mat, GR.get(g))
        (liso if lis else suavizar)(o)
        feitos.append(o)
    BMS.clear()
    return feitos


def flange(c, eixo, r, g='base', esp=0.02, n=8, mat='aco'):
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(B('flanges', mat, g), c, r, esp, eixo, lados=24)
    u, v, _ = base_de(eixo)
    for k in range(n):
        a = k * 2 * PI / n + 0.3
        cil(B('parafusos', 'aco', g), c + (u * math.cos(a) + v * math.sin(a)) * (r - 0.012), 0.006, esp + 0.014, eixo, lados=6)


def cano(pts, r, g='base', mat='cano', fl=True, lados=20):
    pts = [Vector(p) for p in pts]
    bm = B('canos_' + mat, mat, g)
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)
    if fl:
        for a, b in zip(pts, pts[1:]):
            d, L = (b - a).normalized(), (b - a).length
            if L > r * 8:
                flange(a + d * r * 2.2, d, r * 1.55, g, r * 0.45)
                flange(b - d * r * 2.2, d, r * 1.55, g, r * 0.45)


def trilha(bm, pts, r, lados=8):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)


def feixe(pts, lat, g='base', n=3, r=0.008, passo=4, cores=('borracha', 'cabo_verm', 'borracha')):
    pts = [Vector(p) for p in pts]
    for i in range(n):
        off = Vector(lat) * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(B('cabos_' + cores[i % len(cores)], cores[i % len(cores)], g), [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(B('abracadeiras', 'aco', g), pts[j] - u * 0.008, pts[j] + u * 0.008, r * (n + 0.8), 10)


def parafuso(p, n, g='base', r=0.01):
    cil(B('parafusos', 'aco', g), Vector(p), r, 0.012, Vector(n), lados=6)


def rot_face(n):
    n = Vector((n[0], n[1], 0)).normalized()
    return Matrix((Vector((n.y, -n.x, 0)), n, Vector((0, 0, 1)))).transposed()


def remendo(c, n, w, h, g='base', mat='grafite'):
    """Chapa de remendo aparafusada numa face vertical de normal n."""
    R = rot_face(n)
    c = Vector(c)
    caixa(B('remendos_' + mat, mat, g), c + R @ Vector((0, 0.004, 0)), (w, 0.008, h), R)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parafuso(c + R @ Vector((sx * (w / 2 - 0.015), 0.009, 0)) + Vector((0, 0, sz * (h / 2 - 0.015))), R @ Y, g, 0.007)


def stencil(c, n, g='base', k=5, alt=0.04):
    """Número de série pintado e meio apagado."""
    R = rot_face(n)
    c = Vector(c)
    x = -(k - 1) * alt * 0.35
    for _ in range(k):
        for _ in range(random.randint(2, 4)):
            if random.random() < 0.3:
                continue
            if random.random() < 0.5:
                caixa(B('stencil', 'tinta', g), c + R @ Vector((x + random.choice((-1, 0, 1)) * alt * 0.22, 0.0015, 0))
                      + Vector((0, 0, random.choice((-1, 1)) * alt * 0.22)), (0.006, 0.002, alt * 0.45), R)
            else:
                caixa(B('stencil', 'tinta', g), c + R @ Vector((x, 0.0015, 0)) + Vector((0, 0, random.choice((-1, 0, 1)) * alt * 0.45)),
                      (alt * 0.4, 0.002, 0.006), R)
        x += alt * 0.7


def escorrido(c, n, g='base', mat='ferrugem', L=None):
    R = rot_face(n)
    L = L or random.uniform(0.05, 0.18)
    caixa(B('escorridos_' + mat, mat, g), Vector(c) + R @ Vector((0, 0.0015, 0)) - Vector((0, 0, L / 2)),
          (random.uniform(0.005, 0.014), 0.002, L), R)


def listras_borda(a, b, n, h, g='base'):
    """Faixa de perigo numa face vertical, de a até b (no chão da face), altura h."""
    a, b = Vector(a), Vector(b)
    R = rot_face(n)
    c = (a + b) / 2 + Vector((0, 0, h / 2))
    caixa(B('listras', 'listras', g), c + R @ Vector((0, 0.003, 0)), ((b - a).length, 0.006, h), R)


def folha(bm, c, tam, giro, normal=Z, dobra=0.25):
    c, normal = Vector(c), Vector(normal).normalized()
    u, v, w = base_de(normal)
    du, dv = u * math.cos(giro) + v * math.sin(giro), -u * math.sin(giro) + v * math.cos(giro)
    n = 6
    cen = [c + du * (tam * (i / n - 0.5)) for i in range(n + 1)]
    vc = [bm.verts.new(p) for p in cen]
    lados = []
    for s in (-1, 1):
        ls = []
        for i in range(n + 1):
            t = i / n
            lw = tam * 0.28 * math.sin(PI * t) ** 0.9
            ls.append(bm.verts.new(cen[i] + dv * (s * lw) + w * (lw * dobra)))
        lados.append(ls)
    for i in range(n):
        bm.faces.new((vc[i], vc[i + 1], lados[1][i + 1], lados[1][i]))
        bm.faces.new((vc[i], lados[0][i], lados[0][i + 1], vc[i + 1]))


def tufo(bm, c, n, alt, vento=None, forca=0.0):
    """Tufo de capim: lâminas afinando; com vento, todas deitam para o mesmo lado."""
    c = Vector(c)
    for _ in range(n):
        a = random.uniform(0, 2 * PI)
        base = c + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0, 0.03)
        h = alt * random.uniform(0.6, 1.2)
        if vento is not None:
            d = (Vector(vento) * forca * random.uniform(0.8, 1.15) + Vector((math.cos(a), math.sin(a), 0)) * 0.12)
        else:
            d = Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.1, 0.45)
        lado = Vector((-d.y, d.x, 0)).normalized() if d.length > 1e-4 else X
        pts = []
        for i in range(5):
            t = i / 4
            pts.append(base + Vector((0, 0, h * t * (1 - 0.45 * t * forca))) + d * h * t * t)
        vs = []
        for i, p in enumerate(pts):
            w = 0.006 * (1 - i / 4) + 0.0004
            vs.append((bm.verts.new(p - lado * w), bm.verts.new(p + lado * w)))
        for i in range(4):
            bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def molhavel(m):
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = b.inputs['Roughness']
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.name = 'molhado'
    mul.inputs[1].default_value = 1.0
    if ent.is_linked:
        nt.links.new(ent.links[0].from_socket, mul.inputs[0])
    else:
        mul.inputs[0].default_value = ent.default_value
    nt.links.new(mul.outputs[0], ent)
    return m


def vol_cor_mat(nome, cor, escala, dens, em_cor=None, em=0.0, borda0=0.3, f0=0.38, f1=0.64, radial=False):
    """Volume em bolha (some na borda), densidade = cor.R do objeto × dens; emissão = cor.G × em."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 7.0, 'Roughness': 0.62})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    if radial:                                                            # tubo: só a distância ao eixo z
        sx_ = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sx_.inputs[0])
        cx_ = no(nt, 'ShaderNodeCombineXYZ')
        nt.links.new(sx_.outputs['X'], cx_.inputs['X'])
        nt.links.new(sx_.outputs['Y'], cx_.inputs['Y'])
        nt.links.new(cx_.outputs[0], comp.inputs[0])
    else:
        nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': borda0})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    forma = no(nt, 'ShaderNodeMapRange', **{'From Min': f0, 'From Max': f1})
    nt.links.new(ru.outputs['Fac'], forma.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], m1.inputs[0])
    nt.links.new(forma.outputs['Result'], m1.inputs[1])
    oi = no(nt, 'ShaderNodeObjectInfo')
    sep = no(nt, 'ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sep.inputs[0])
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(sep.outputs[0], m2.inputs[1])
    m3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    m3.inputs[1].default_value = dens
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    nt.links.new(m3.outputs['Value'], vol.inputs['Density'])
    if em > 0:
        vol.inputs['Emission Color'].default_value = (*em_cor, 1)
        e1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(m1.outputs['Value'], e1.inputs[0])
        nt.links.new(sep.outputs[1], e1.inputs[1])
        e2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        e2.inputs[1].default_value = em
        nt.links.new(e1.outputs['Value'], e2.inputs[0])
        nt.links.new(e2.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def fumaca_grad_mat(nome, dens, z0, z1, escuro=(0.012, 0.011, 0.011), claro=(0.42, 0.42, 0.43)):
    """Fumaça que sai escura e se dilui em cinza claro conforme sobe."""
    m = base3d.volume_mat(nome, escuro, dens, z0, z1)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.6})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*escuro, 1)
    mix.inputs[7].default_value = (*claro, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


def fogo_mat():
    m = base3d.volume_mat('Fogo', (1.0, 0.4, 0.05), 3.0, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 70.0
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1)
    for n in nt.nodes:
        if n.type == 'TEX_NOISE':
            n.inputs['Scale'].default_value = 6.5
        if n.type == 'MAP_RANGE' and abs(n.inputs['From Min'].default_value - 0.42) < 1e-3:
            n.inputs['From Min'].default_value = 0.5
            n.inputs['From Max'].default_value = 0.72
    return m


def nuvem_mat():
    """Nuvem: bolha achatada com couve-flor por cima e base mais densa e reta; cor (escurece) e densidade por cor do
    objeto (R = densidade, B = claridade)."""
    m = bpy.data.materials.new('Nuvem')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Anisotropy'].default_value = 0.3
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    sx = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sx.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.2, 'Detail': 9.0, 'Roughness': 0.6})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    # distância deformada pelo ruído (bordas couve-flor)
    desv = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    desv.inputs[1].default_value = 0.7
    desv.inputs[2].default_value = -0.35
    nt.links.new(ru.outputs['Fac'], desv.inputs[0])
    dd = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(comp.outputs['Value'], dd.inputs[0])
    nt.links.new(desv.outputs['Value'], dd.inputs[1])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.82, 'From Max': 0.62})
    nt.links.new(dd.outputs['Value'], borda.inputs['Value'])
    base = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.62, 'From Max': -0.5})     # base reta
    nt.links.new(sx.outputs['Z'], base.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], m1.inputs[0])
    nt.links.new(base.outputs['Result'], m1.inputs[1])
    oi = no(nt, 'ShaderNodeObjectInfo')
    sep = no(nt, 'ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sep.inputs[0])
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(sep.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs['Value'], vol.inputs['Density'])
    # cor: base escura, topo claro; claridade geral pelo canal B
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.6, 'From Max': 0.5})
    nt.links.new(sx.outputs['Z'], alt.inputs['Value'])
    cm = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cm.inputs[6].default_value = (0.12, 0.125, 0.14, 1)
    cm.inputs[7].default_value = (0.75, 0.77, 0.8, 1)
    nt.links.new(alt.outputs['Result'], cm.inputs[0])
    cl = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    nt.links.new(sep.outputs[2], cl.inputs[0])
    nt.links.new(cm.outputs[2], cl.inputs[6])
    cl.inputs[7].default_value = (0.35, 0.36, 0.4, 1)
    nt.links.new(cl.outputs[2], vol.inputs['Color'])
    return m


def chuva_mat():
    m = bpy.data.materials.new('Chuva')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.8, 0.84, 0.88, 1)
    ag.inputs['Roughness'].default_value = 0.2
    ag.inputs['Transmission Weight'].default_value = 0.5
    ag.inputs['IOR'].default_value = 1.33
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    alto = no(nt, 'ShaderNodeMapRange', **{'From Min': 12.4, 'From Max': 12.9, 'To Min': 0.45, 'To Max': 1.0})   # some dentro da nuvem
    nt.links.new(sep.outputs['Z'], alto.inputs['Value'])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(alto.outputs['Result'], mix.inputs[0])
    nt.links.new(ag.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def terra_mat(nome, r_molhado=None, cor_seca=(0.24, 0.19, 0.13)):
    """Chão: terra com manchas de capim; com r_molhado, só o círculo debaixo da nuvem fica escuro e brilhante."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.9, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])
    capim = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], capim.inputs['Value'])
    seca = no(nt, 'ShaderNodeMix', data_type='RGBA')
    seca.inputs[6].default_value = (*cor_seca, 1)
    seca.inputs[7].default_value = (0.15, 0.15, 0.07, 1)
    nt.links.new(capim.outputs['Result'], seca.inputs[0])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.35
    nt.links.new(seca.outputs[2], var.inputs[6])
    nt.links.new(fino.outputs['Color'], var.inputs[7])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    nt.links.new(fino.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    if r_molhado is None:
        nt.links.new(var.outputs[2], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.95
        return m
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    cxy = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], cxy.inputs['X'])
    nt.links.new(sep.outputs['Y'], cxy.inputs['Y'])
    rr = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(cxy.outputs[0], rr.inputs[0])
    rn = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')                  # borda irregular
    rn.inputs[1].default_value = 2.4
    nt.links.new(ru.outputs['Fac'], rn.inputs[0])
    nt.links.new(rr.outputs['Value'], rn.inputs[2])
    molh = no(nt, 'ShaderNodeMapRange', **{'From Min': r_molhado + 1.6, 'From Max': r_molhado + 0.6})
    molh.name = 'molha'
    nt.links.new(rn.outputs['Value'], molh.inputs['Value'])
    fator = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    fator.name = 'chuva_on'
    fator.inputs[1].default_value = 1.0
    nt.links.new(molh.outputs['Result'], fator.inputs[0])
    esc = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    esc.inputs[7].default_value = (0.22, 0.2, 0.18, 1)
    nt.links.new(fator.outputs[0], esc.inputs[0])
    nt.links.new(var.outputs[2], esc.inputs[6])
    nt.links.new(esc.outputs[2], b.inputs['Base Color'])
    poca = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.55, 'To Min': 0.55, 'To Max': 0.2})
    nt.links.new(ru.outputs['Fac'], poca.inputs['Value'])
    ro = no(nt, 'ShaderNodeMix', data_type='FLOAT')
    ro.inputs[2].default_value = 0.95
    nt.links.new(fator.outputs[0], ro.inputs[0])
    nt.links.new(poca.outputs['Result'], ro.inputs[3])
    nt.links.new(ro.outputs[0], b.inputs['Roughness'])
    return m


def fluxo_mat():
    """Linha de fluxo da IA: faixa translúcida (UV: u ao longo, v através) com pulsos andando; some nas bordas e no fim."""
    m = bpy.data.materials.new('Fluxo de vento')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.66, 0.5, 1.0, 1)
    em.inputs['Strength'].default_value = 3.2
    df = no(nt, 'ShaderNodeBsdfDiffuse')
    df.inputs['Color'].default_value = (0.3, 0.28, 0.36, 1)
    soma = no(nt, 'ShaderNodeAddShader')
    nt.links.new(em.outputs[0], soma.inputs[0])
    nt.links.new(df.outputs[0], soma.inputs[1])
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['UV'], sep.inputs[0])
    fim = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.35})
    nt.links.new(sep.outputs['X'], fim.inputs['Value'])
    ini = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.06})
    nt.links.new(sep.outputs['X'], ini.inputs['Value'])
    vv = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    vv.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs['Y'], vv.inputs[1])
    vb = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(sep.outputs['Y'], vb.inputs[0])
    nt.links.new(vv.outputs[0], vb.inputs[1])
    vb4 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    vb4.inputs[1].default_value = 4.0
    nt.links.new(vb.outputs[0], vb4.inputs[0])
    vbp = no(nt, 'ShaderNodeMath', operation='POWER')
    vbp.inputs[1].default_value = 1.6
    nt.links.new(vb4.outputs[0], vbp.inputs[0])
    fase = no(nt, 'ShaderNodeValue')
    fase.name = 'fase'
    fase.outputs[0].default_value = 0.0
    uu = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    uu.inputs[1].default_value = 7.0
    nt.links.new(sep.outputs['X'], uu.inputs[0])
    nt.links.new(fase.outputs[0], uu.inputs[2])
    # estrias finas ao longo (ruído esticado) para parecer ar, não fita lisa
    est_v = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(uu.outputs[0], est_v.inputs['X'])
    sy = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    sy.inputs[1].default_value = 9.0
    nt.links.new(sep.outputs['Y'], sy.inputs[0])
    nt.links.new(sy.outputs[0], est_v.inputs['Y'])
    est = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.3, 'Detail': 3.0})
    nt.links.new(est_v.outputs[0], est.inputs['Vector'])
    estr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.7, 'To Min': 0.4, 'To Max': 1.0})
    nt.links.new(est.outputs['Fac'], estr.inputs['Value'])
    sn = no(nt, 'ShaderNodeMath', operation='SINE')
    k2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    k2.inputs[1].default_value = 2 * PI
    nt.links.new(uu.outputs[0], k2.inputs[0])
    nt.links.new(k2.outputs[0], sn.inputs[0])
    pul = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0, 'To Min': 0.45, 'To Max': 1.0})
    nt.links.new(sn.outputs[0], pul.inputs['Value'])
    a = fim.outputs['Result']
    for s in (ini.outputs['Result'], vbp.outputs[0], estr.outputs['Result'], pul.outputs['Result']):
        mm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(a, mm.inputs[0])
        nt.links.new(s, mm.inputs[1])
        a = mm.outputs[0]
    ga = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    ga.name = 'ganho'
    ga.inputs[1].default_value = 0.42
    nt.links.new(a, ga.inputs[0])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(ga.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(soma.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def biruta_mat():
    """Biruta: faixas laranja e branco sujo ao longo do eixo x do objeto."""
    m = bpy.data.materials.new('Biruta')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    k = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    k.inputs[1].default_value = 1 / 0.16
    nt.links.new(sep.outputs['X'], k.inputs[0])
    fl = no(nt, 'ShaderNodeMath', operation='FLOOR')
    nt.links.new(k.outputs[0], fl.inputs[0])
    md = no(nt, 'ShaderNodeMath', operation='MODULO')
    md.inputs[1].default_value = 2.0
    nt.links.new(fl.outputs[0], md.inputs[0])
    ab = no(nt, 'ShaderNodeMath', operation='ABSOLUTE')
    nt.links.new(md.outputs[0], ab.inputs[0])
    mx = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mx.inputs[6].default_value = (0.7, 0.12, 0.02, 1)
    mx.inputs[7].default_value = (0.55, 0.52, 0.46, 1)
    nt.links.new(ab.outputs[0], mx.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 12.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    suj = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    suj.inputs[0].default_value = 0.55
    nt.links.new(mx.outputs[2], suj.inputs[6])
    nt.links.new(ru.outputs['Color'], suj.inputs[7])
    nt.links.new(suj.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    b.inputs['Sheen Weight'].default_value = 0.4
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.45, 0.05)
R_CHUVA = 8.5                 # raio da chuva na foto (no jogo: 40 m)

base3d.M.update({
    'amarelo': molhavel(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.95, ferrugem=0.5)),
    'amarelo2': molhavel(mats.material('Amarelo desbotado', (0.62, 0.47, 0.16), 0, 0.55, desgaste=1.0, sujeira=1.0, ferrugem=0.55)),
    'zarcao': molhavel(mats.material('Zarcão', (0.32, 0.07, 0.035), 0, 0.6, desgaste=0.8, sujeira=0.9, ferrugem=0.45)),
    'grafite': molhavel(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.85, sujeira=0.9, ferrugem=0.3)),
    'verde': molhavel(mats.material('Verde-oliva', (0.12, 0.14, 0.06), 0, 0.55, desgaste=0.8, sujeira=0.9, ferrugem=0.4)),
    'azul': molhavel(mats.material('Azul gasto', (0.06, 0.13, 0.22), 0, 0.5, desgaste=0.9, sujeira=0.9, ferrugem=0.4)),
    'chapa': molhavel(mats.material('Chapa', (0.3, 0.3, 0.3), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=1.0, escovado=True)),
    'aco': molhavel(mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True)),
    'cano': molhavel(mats.material('Cano', (0.28, 0.29, 0.3), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=0.95)),
    'cano_arma': molhavel(mats.material('Aço do cano', (0.16, 0.16, 0.16), 1.0, 0.45, pintura=False, ferrugem=0.6, sujeira=0.95, escovado=True)),
    'ferro': molhavel(mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.95, sujeira=0.95)),
    'queimado': molhavel(mats.material('Queimado', (0.08, 0.065, 0.06), 1.0, 0.6, pintura=False, ferrugem=0.7, sujeira=1.0)),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'bronze': mats.material('Bronze', (0.55, 0.38, 0.17), 1.0, 0.4, pintura=False, sujeira=0.9, ferrugem=0.2),
    'latao': mats.material('Latão gasto', (0.58, 0.42, 0.17), 1.0, 0.36, pintura=False, sujeira=0.9, ferrugem=0.25),
    'aco_estojo': mats.material('Aço do estojo', (0.36, 0.35, 0.34), 1.0, 0.45, pintura=False, sujeira=0.9, ferrugem=0.5),
    'aluminio': mats.material('Alumínio', (0.6, 0.6, 0.62), 1.0, 0.35, pintura=False, sujeira=0.8, ferrugem=0.0),
    'espoleta': mats.material('Espoleta', (0.7, 0.4, 0.25), 1.0, 0.3, pintura=False, sujeira=0.4),
    'concreto': molhavel(mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.75, desgaste=0.0)),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.6, pintura=False, sujeira=0.5, desgaste=0.0),
    'cabo_verm': mats.material('Cabo vermelho', (0.28, 0.03, 0.02), 0, 0.5, pintura=False, sujeira=0.6, desgaste=0.0),
    'cabo_azul': mats.material('Cabo azul', (0.02, 0.06, 0.2), 0, 0.5, pintura=False, sujeira=0.6, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'tinta': mats.material('Tinta do número', (0.7, 0.68, 0.6), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.015, 0.014, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'po': mats.material('Poeira', (0.32, 0.26, 0.18), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'lama': mats.material('Lama', (0.08, 0.06, 0.035), 0, 0.5, pintura=False, sujeira=0.3, desgaste=0.0),
    'ferrugem': mats.material('Ferrugem escorrida', (0.26, 0.09, 0.03), 0, 0.8, pintura=False, sujeira=0.4, desgaste=0.0),
    'pedra': mats.material('Pedra', (0.15, 0.145, 0.13), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'folha_seca': mats.material('Folha seca', (0.3, 0.16, 0.05), 0, 0.7, pintura=False, sujeira=0.3, desgaste=0.0),
    'folha_verde': mats.material('Folha', (0.11, 0.14, 0.035), 0, 0.55, pintura=False, sujeira=0.3, desgaste=0.0),
    'capim': mats.material('Capim', (0.2, 0.17, 0.07), 0, 0.7, pintura=False, sujeira=0.4, desgaste=0.0),
    'capim_verde': mats.material('Capim verde', (0.09, 0.12, 0.035), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'vidro': mats.material('Vidro sujo', (0.3, 0.32, 0.3), 0, 0.15, pintura=False, sujeira=0.6, desgaste=0.0),
    'domo': emissivo('Domo do sensor', VIOLETA, 2.0, (0.12, 0.04, 0.3)),
    'bobina': emissivo('Bobina', VIOLETA, 5.0, (0.3, 0.12, 0.6)),
    'led_ambar': emissivo('LED âmbar', AMBAR, 6.0),
    'led_verde': emissivo('LED verde', (0.2, 1.0, 0.25), 5.0),
    'brasa': emissivo('Boca quente', (1.0, 0.3, 0.04), 0.0, (0.06, 0.04, 0.03)),
    'faisca': emissivo('Faísca', (1.0, 0.75, 0.4), 30.0),
    'particula': emissivo('Partícula de iodeto', (0.9, 0.9, 1.0), 4.0, (0.8, 0.8, 0.85)),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'fogo': fogo_mat(),
    'fumaca_boca': vol_cor_mat('Fumaça da boca', (0.35, 0.35, 0.36), 2.5, 9.0),
    'fiapo': vol_cor_mat('Fiapo de fumaça', (0.45, 0.45, 0.47), 4.0, 14.0),
    'rastro': vol_cor_mat('Rastro', (0.78, 0.78, 0.82), 1.6, 9.0, borda0=0.2, f0=0.3, f1=0.6, radial=True),
    'estouro': vol_cor_mat('Estouro', (0.5, 0.45, 0.6), 2.0, 3.0, VIOLETA, 25.0, f0=0.3, f1=0.6),
    'pluma': vol_cor_mat('Pluma do queimador', (0.5, 0.5, 0.53), 2.6, 16.0, borda0=0.15, f0=0.36, f1=0.66),
    'pluma_escura': vol_cor_mat('Pluma escura', (0.06, 0.06, 0.06), 3.0, 9.0, borda0=0.2, f0=0.36, f1=0.66),
    'cortina': vol_cor_mat('Cortina de chuva', (0.5, 0.53, 0.58), 1.2, 0.14, borda0=0.85, f0=0.2, f1=0.7),
    'poeira_vento': vol_cor_mat('Poeira no vento', (0.42, 0.34, 0.24), 2.2, 4.5, borda0=0.25, f0=0.32, f1=0.62),
    'nuvem': nuvem_mat(),
    'chuva': chuva_mat(),
    'fluxo': fluxo_mat(),
    'biruta': biruta_mat(),
    'terra': terra_mat('Terra', R_CHUVA) if MAQ == 'semeador' else terra_mat('Terra', None, (0.11, 0.085, 0.06)),
    'gota': mats.material('Gota', (0.8, 0.85, 0.9), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
})
M = base3d.M


# ------------------------------------------------------------------ cena comum: chão, pedras, sol, céu, câmera
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=400.0)
chao = obj('chao', bm, 'terra')


def pedrinhas(n, r0, r1, rmin=1.15):
    bm = bmesh.new()
    for _ in range(n):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(rmin, r1)
        pedra(bm, (math.cos(a) * r, math.sin(a) * r, 0.0), random.uniform(r0, r0 * 3.5), 0.5)
    obj('pedras', bm, 'pedra')


def laje(g='base'):
    """Laje 2×2 de concreto com cantoneira, faixa de perigo, chumbadores, lama no pé e poeira."""
    caixa_de(B('laje', 'concreto', g), (-1, -1, 0), (1, 1, ZL))
    for s in (-1, 1):
        caixa_de(B('cantoneira', 'aco', g), (-1.005, s * 1.0 - 0.025, ZL - 0.012), (1.005, s * 1.0 + 0.025, ZL + 0.004))
        caixa_de(B('cantoneira', 'aco', g), (s * 1.0 - 0.025, -1.005, ZL - 0.012), (s * 1.0 + 0.025, 1.005, ZL + 0.004))
    for n_, a, b in ((Vector((0, -1, 0)), (-0.98, -1.006, 0.02), (0.98, -1.006, 0.02)),
                     (Vector((0, 1, 0)), (0.98, 1.006, 0.02), (-0.98, 1.006, 0.02)),
                     (Vector((1, 0, 0)), (1.006, -0.98, 0.02), (1.006, 0.98, 0.02)),
                     (Vector((-1, 0, 0)), (-1.006, 0.98, 0.02), (-1.006, -0.98, 0.02))):
        listras_borda(a, b, n_, 0.07, g)
    for k in range(4):
        for s in (-0.6, 0.0, 0.6):
            for sx, sy in ((s, -0.96), (s, 0.96), (-0.96, s), (0.96, s)):
                cil(B('chumbadores', 'ferro', g), Vector((sx, sy, ZL + 0.01)), 0.012, 0.022, lados=6)
        break
    for _ in range(26):                                                      # lama respingada no pé da laje
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0))
        if abs(d.x) > abs(d.y):
            p = Vector((math.copysign(1.0, d.x) + math.copysign(0.004, d.x), random.uniform(-0.95, 0.95), 0))
            nn = Vector((math.copysign(1, d.x), 0, 0))
        else:
            p = Vector((random.uniform(-0.95, 0.95), math.copysign(1.0, d.y) + math.copysign(0.004, d.y), 0))
            nn = Vector((0, math.copysign(1, d.y), 0))
        R = rot_face(nn)
        caixa(B('lama_pe', 'lama', g), p + Vector((0, 0, random.uniform(0.01, 0.04))), (random.uniform(0.05, 0.16), 0.004, random.uniform(0.02, 0.07)), R)
    for _ in range(14):
        mancha(B('laje_po', 'po', g), (random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95)), random.uniform(0.04, 0.12), ZL + 0.001)


sol_d = bpy.data.lights.new('Sol', 'SUN')
sol = bpy.data.objects.new('Sol', sol_d)
sc.collection.objects.link(sol)
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
nt_w = mundo.node_tree
bg = nt_w.nodes['Background']
ceu = nt_w.nodes.new('ShaderNodeTexSky')
try:
    ceu.sky_type = 'NISHITA'
except Exception:
    pass
try:
    ceu.sun_disc = False
except Exception:
    pass
nt_w.links.new(ceu.outputs[0], bg.inputs['Color'])
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
sc.cycles.volume_bounces = 2
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.clip_end = 400


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def ceu_sol(elev, azim):
    """Sol e céu físico (Nishita) coerentes; azim em graus a partir do leste, anti-horário."""
    sol.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim + 90))
    try:
        ceu.sun_elevation = math.radians(elev)
        ceu.sun_rotation = math.radians(azim + 90)
    except Exception:
        pass


def chave(o, campos, q):
    for c in campos:
        o.keyframe_insert(c, frame=q)


def mostra(o, vis, q):
    o.hide_render = not vis
    o.keyframe_insert('hide_render', frame=q)


def cor_vol(o, d, e=0.0, b=1.0):
    o.color = (max(0.0, d), max(0.0, e), b, 1)


def bolha(nome, mat, r=1.0, sub=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    o = obj(nome, bm, mat)
    return o


def interp_linear():
    for o in list(sc.objects) + list(bpy.data.materials) + list(bpy.data.lights):
        ad = getattr(o, 'animation_data', None)
        if o.__class__.__name__ == 'Material' and o.node_tree is not None:
            ad = o.node_tree.animation_data
        if ad and ad.action:
            fcs = getattr(ad.action, 'fcurves', None)
            if fcs is None:
                fcs = []
                try:
                    for ly in ad.action.layers:
                        for st in ly.strips:
                            for cb in st.channelbags:
                                fcs.extend(cb.fcurves)
                except Exception:
                    pass
            for fc in fcs:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT' if fc.data_path == 'hide_render' else 'LINEAR'


# ====================================================================================================================
#                                          SEMEADOR DE NUVENS
# ====================================================================================================================
def semeador():
    global CENA
    G = Vector((0.25, 0.0, 0.0))            # eixo do canhão
    CAR = Vector((-0.46, 0.13, 0.0))        # carrossel
    TQ = Vector((-0.17, 0.69, 0.39))        # tanque (eixo x)
    QS = [Vector((-0.66, -0.64, 0)), Vector((0.66, -0.64, 0))]   # queimadores
    laje()
    pedrinhas(160, 0.02, 9.0)
    for _ in range(500):
        a = random.uniform(0, 2 * PI)
        r = 1.15 + random.expovariate(1 / 3.5)
        if r < 14:
            tufo(B('capim', 'capim' if random.random() < 0.6 else 'capim_verde'), (math.cos(a) * r, math.sin(a) * r, 0), random.randint(5, 9), random.uniform(0.1, 0.26))

    # ---------------- pedestal fixo
    caixa_de(B('pedestal_base', 'ferro'), G + Vector((-0.31, -0.31, ZL)), G + Vector((0.31, 0.31, ZL + 0.03)))
    caixa_de(B('pedestal', 'amarelo'), G + Vector((-0.24, -0.24, ZL + 0.03)), G + Vector((0.24, 0.24, 0.44)))
    torno(B('pedestal_furo', 'fuligem'), [(0.44, 0), (0.44, 0.068), (0.4405, 0.068), (0.4405, 0)], G, n=24)
    toro(B('pedestal_furo_aro', 'aco'), G + Vector((0, 0, 0.442)), 0.075, 0.008, nR=28, nr=6)
    for s in (-1, 1):                                                      # nervuras (mãos-francesas)
        for t in (-0.12, 0.12):
            v = [B('nervuras', 'amarelo').verts.new(p) for p in (
                G + Vector((t, s * 0.24, ZL + 0.03)), G + Vector((t, s * 0.31, ZL + 0.03)), G + Vector((t, s * 0.24, 0.34)))]
            bmv = B('nervuras', 'amarelo')
            f = bmv.faces.new(v)
            ex = bmesh.ops.extrude_face_region(bmv, geom=[f])
            for e in ex['geom']:
                if isinstance(e, bmesh.types.BMVert):
                    e.co.x += 0.016
    for x in (-0.27, -0.09, 0.09, 0.27):
        for y in (-0.28, 0.28):
            if abs(x) > 0.2 or True:
                parafuso(G + Vector((x, y, ZL + 0.036)), Z, r=0.012)
                parafuso(G + Vector((y, x, ZL + 0.036)), Z, r=0.012)
    remendo(G + Vector((0.0, -0.24, 0.3)), -Y, 0.16, 0.12, mat='zarcao')
    stencil(G + Vector((0.12, -0.245, 0.38)), -Y, k=4, alt=0.035)
    for x in (-0.18, -0.05, 0.15):
        escorrido(G + Vector((x, -0.241, 0.43)), -Y)
    escorrido(G + Vector((0.241, 0.1, 0.43)), X, mat='oleo', L=0.2)
    mancha(B('oleo_chao', 'oleo'), (G.x + 0.12, G.y - 0.36), 0.09, ZL + 0.0015)

    # ---------------- culatra (recua junto com o cano): grupo com origem no eixo, z = 0
    grupo('culatra', (G.x, G.y, 0))
    g = 'culatra'
    caixa_de(B('culatra_flange', 'aco', g), (-0.23, -0.23, 0.52), (0.23, 0.23, 0.56))
    torno(B('culatra_luva', 'cromo', g), [(0.40, 0), (0.40, 0.06), (0.52, 0.06), (0.52, 0)], n=24)   # luva-guia (entra no furo do pedestal)
    caixa_de(B('culatra', 'grafite', g), (-0.18, -0.18, 0.56), (0.18, 0.18, 0.98))
    caixa_de(B('culatra_tampa', 'amarelo2', g), (-0.19, -0.19, 0.93), (0.19, 0.19, 0.99))
    for x in (-0.15, -0.05, 0.05, 0.15):
        for y in (-0.15, 0.15):
            parafuso((x, y, 0.995), Z, g, 0.009)
            parafuso((y, x, 0.995), Z, g, 0.009)
    # janela de ejeção (face -y) com moldura e interior escuro
    caixa_de(B('janela_interior', 'fuligem', g), (-0.07, -0.183, 0.70), (0.07, -0.17, 0.86))
    for a, b in (((-0.09, -0.195, 0.68), (0.09, -0.18, 0.70)), ((-0.09, -0.195, 0.86), (0.09, -0.18, 0.88)),
                 ((-0.09, -0.195, 0.70), (-0.07, -0.18, 0.86)), ((0.07, -0.195, 0.70), (0.09, -0.18, 0.86))):
        caixa_de(B('janela_moldura', 'aco', g), a, b)
    for _ in range(8):                                                     # fuligem saindo da janela
        caixa(B('fuligem_janela', 'fuligem', g), Vector((random.uniform(-0.08, 0.08), -0.1815, random.uniform(0.86, 0.97))),
              (random.uniform(0.01, 0.03), 0.002, random.uniform(0.03, 0.09)))
    # cano: jaqueta, cano, freio de boca
    torno(B('cano_jaqueta', 'grafite', g), [(0.98, 0), (0.98, 0.11), (1.05, 0.11), (1.08, 0.095), (1.62, 0.09), (1.66, 0.075), (1.66, 0)], n=32)
    torno(B('cano', 'cano_arma', g), [(1.6, 0), (1.6, 0.066), (3.2, 0.062), (3.2, 0)], n=32)
    torno(B('freio_boca', 'queimado', g), [(3.18, 0), (3.18, 0.085), (3.42, 0.085), (3.42, 0.05), (3.4, 0.05), (3.4, 0)], n=32)
    for z in (3.24, 3.31):                                                 # janelas do freio (vazios pintados)
        for s in (-1, 1):
            caixa_de(B('freio_janelas', 'fuligem', g), (s * 0.086 - 0.002, -0.035, z), (s * 0.086 + 0.002, 0.035, z + 0.05))
            caixa_de(B('freio_janelas', 'fuligem', g), (-0.035, s * 0.086 - 0.002, z), (0.035, s * 0.086 + 0.002, z + 0.05))
    for z in (1.2, 1.4):
        toro(B('cano_cintas', 'aco', g), (0, 0, z), 0.092, 0.008, nR=32, nr=6)
    # bobinas violeta de aceleração (toque da IA), presas por braçadeiras e quatro suportes
    for z in (2.5, 2.75, 3.0):
        toro(B('bobinas_cobre', 'cobre', g), (0, 0, z), 0.16, 0.034, nR=40, nr=10)
        toro(B('bobinas_brilho', 'bobina', g), (0, 0, z), 0.16, 0.012, nR=40, nr=8)
        for k in range(18):                                                # espiras
            a = k * 2 * PI / 18
            toro(B('bobinas_espiras', 'cobre', g), (math.cos(a) * 0.16, math.sin(a) * 0.16, z), 0.036, 0.005,
                 Vector((-math.sin(a), math.cos(a), 0)), nR=12, nr=4)
        torno(B('bobinas_bracadeira', 'aco', g), [(z - 0.03, 0), (z - 0.03, 0.078), (z + 0.03, 0.078), (z + 0.03, 0)], n=24)
        for k in range(4):
            a = k * PI / 2 + PI / 4
            d = Vector((math.cos(a), math.sin(a), 0))
            viga(B('bobinas_suportes', 'aco', g), Vector((0, 0, z)) + d * 0.075, Vector((0, 0, z)) + d * 0.13, 0.02)
    # caixa de força das bobinas (presa no cano) e cabo
    caixa_de(B('caixa_bobinas', 'grafite', g), (0.065, -0.06, 2.12), (0.17, 0.06, 2.36))
    caixa_de(B('caixa_bobinas_led', 'led_ambar', g), (0.171, -0.03, 2.3), (0.175, -0.01, 2.32))
    for z in (2.15, 2.33):
        torno(B('cano_cintas', 'aco', g), [(z, 0), (z, 0.07), (z + 0.02, 0.07), (z + 0.02, 0)], n=24)
    for k, z in enumerate((2.5, 2.75, 3.0)):
        feixe(bezier((0.15, 0.03 - k * 0.02, 2.36), (0.2, 0.0, 2.42 + k * 0.1), (0.2, -0.02, z - 0.1), (0.13, -0.02 * k, z - 0.035), 8),
              Vector((0, 1, 0)), g, n=2, r=0.006, passo=99)
    # orelhas da flange para as hastes dos pistões de recuo
    for s in (-1, 1):
        caixa_de(B('orelhas', 'aco', g), (min(s * 0.2, s * 0.33), -0.05, 0.495), (max(s * 0.2, s * 0.33), 0.05, 0.52))
        cil(B('hastes_recuo', 'cromo', g), Vector((s * 0.29, 0, 0.44)), 0.016, 0.12, lados=16)
    culatra = GR['culatra']

    # ---------------- pistões de recuo (camisa fixa)
    for s in (-1, 1):
        p = G + Vector((s * 0.29, 0, 0))
        torno(B('camisas_recuo', 'amarelo2'), [(0.17, 0), (0.17, 0.036), (0.41, 0.036), (0.41, 0.022), (0.43, 0.022), (0.43, 0)], p, n=20)
        caixa_de(B('camisas_suporte', 'aco'), p + Vector((-0.04 if s > 0 else 0.0, -0.04, ZL + 0.03)),
                 p + Vector((0.0 if s > 0 else 0.04, 0.04, 0.2)))
        for z in (0.22, 0.36):
            toro(B('camisas_cintas', 'aco'), p + Vector((0, 0, z)), 0.037, 0.006, nR=24, nr=6)
        porta = p + Vector((0, -0.036, 0.22))
        cil(B('portas', 'aco'), porta + Vector((0, -0.01, 0)), 0.012, 0.022, -Y, lados=10)
    # ---------------- torre-berço: quatro pernas, colar-bucha e travamentos
    CB = 2.1
    pernas = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = G + Vector((sx * 0.36, sy * 0.36, ZL + 0.02))
            b = G + Vector((sx * 0.13, sy * 0.13, CB - 0.03))
            viga(B('torre_pernas', 'amarelo'), a, b, 0.046)
            caixa_de(B('torre_sapatas', 'ferro'), a + Vector((-0.06, -0.06, -0.02)), a + Vector((0.06, 0.06, 0.0)))
            for dx, dy in ((-0.04, -0.04), (0.04, 0.04), (-0.04, 0.04), (0.04, -0.04)):
                parafuso(a + Vector((dx, dy, 0.004)), Z, r=0.009)
            pernas.append((a, b))
    for i in range(4):                                                     # travessas em X entre pernas vizinhas
        a0, b0 = pernas[i]
        a1, b1 = pernas[(i + 1) % 4] if i < 3 else pernas[0]
    ordem = [0, 1, 3, 2]
    for i in range(4):
        pa, pb = pernas[ordem[i]], pernas[ordem[(i + 1) % 4]]
        for t0, t1 in ((0.52, 0.86), (0.86, 0.52)):
            viga(B('torre_travessas', 'aco'), pa[0].lerp(pa[1], t0), pb[0].lerp(pb[1], t1), 0.02)
        viga(B('torre_travessas', 'aco'), pa[0].lerp(pa[1], 0.86), pb[0].lerp(pb[1], 0.86), 0.026)
    torno(B('colar_bucha', 'amarelo2'), [(CB - 0.06, 0.07), (CB - 0.06, 0.16), (CB + 0.06, 0.16), (CB + 0.06, 0.07)], G, n=32)
    for k in range(8):
        a = k * PI / 4
        parafuso(G + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, CB + 0.065)), Z, r=0.009)
    toro(B('colar_graxa', 'oleo'), G + Vector((0, 0, CB + 0.062)), 0.071, 0.006, nR=32, nr=6)
    escorrido(G + Vector((0.0, -0.161, CB - 0.03)), -Y, mat='oleo', L=0.12)
    # ---------------- carrossel de cartuchos (10) e calha de alimentação
    torno(B('carrossel_base', 'ferro'), [(ZL, 0), (ZL, 0.22), (0.3, 0.22), (0.3, 0)], CAR, n=40)
    toro(B('carrossel_coroa', 'aco'), CAR + Vector((0, 0, 0.29)), 0.225, 0.012, nR=48, nr=6)
    grupo('carrossel', (CAR.x, CAR.y, 0))
    gc = 'carrossel'
    torno(B('carrossel_prato', 'aco', gc), [(0.3, 0), (0.3, 0.27), (0.335, 0.27), (0.335, 0)], n=48)
    torno(B('carrossel_eixo', 'cromo', gc), [(0.335, 0), (0.335, 0.035), (0.72, 0.035), (0.72, 0)], n=16)
    torno(B('carrossel_anel', 'amarelo', gc), [(0.6, 0.2), (0.6, 0.275), (0.625, 0.275), (0.625, 0.2)], n=48)
    for k in range(3):
        a = k * 2 * PI / 3 + 0.3
        viga(B('carrossel_postes', 'aco', gc), Vector((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.335)), Vector((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.6)), 0.02)
        viga(B('carrossel_raios', 'aco', gc), Vector((0, 0, 0.71)), Vector((math.cos(a) * 0.23, math.sin(a) * 0.23, 0.625)), 0.016)
    for k in range(10):
        a = k * 2 * PI / 10
        c = Vector((math.cos(a) * 0.19, math.sin(a) * 0.19, 0.335))
        torno(B('carrossel_soquetes', 'ferro', gc), [(0, 0.04), (0, 0.048), (0.05, 0.048), (0.05, 0.04)], c, n=20)
        if k in (0, 1):
            continue                                                       # dois vazios (já disparados)
        cartucho_cheio(c, gc, k)
    for _ in range(4):
        mancha(B('carrossel_po', 'po', gc), (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15)), 0.03, 0.336)
    # motor de indexação do carrossel
    pm = CAR + Vector((-0.1, -0.33, 0))
    caixa_de(B('motor_carrossel_base', 'ferro'), pm + Vector((-0.07, -0.07, ZL)), pm + Vector((0.07, 0.07, ZL + 0.03)))
    torno(B('motor_carrossel', 'azul'), [(ZL + 0.03, 0), (ZL + 0.03, 0.055), (0.24, 0.055), (0.24, 0.02), (0.25, 0.02), (0.25, 0)], pm, n=24)
    cil(B('motor_carrossel_pinhao', 'aco'), pm + Vector((0, 0, 0.27)), 0.1, 0.04, lados=28)
    for k in range(22):
        a = k * 2 * PI / 22
        caixa(B('motor_carrossel_pinhao', 'aco'), pm + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.27)), (0.016, 0.012, 0.04), Matrix.Rotation(a, 3, 'Z'))
    for k in range(10):
        a = k * 2 * PI / 10
        caixa(B('motor_carrossel_aletas', 'azul'), pm + Vector((math.cos(a) * 0.058, math.sin(a) * 0.058, 0.16)), (0.012, 0.006, 0.1),
              Matrix.Rotation(a, 3, 'Z'))
    # calha/bandeja de alimentação inclinada do carrossel à culatra, com soquete pneumático
    c0 = CAR + Vector((0.2, -0.02, 0.66))
    c1 = G + Vector((-0.19, 0.0, 0.8))
    d = (c1 - c0)
    Rr = Matrix.Rotation(math.atan2(d.y, d.x), 3, 'Z')
    L = d.length
    mid = (c0 + c1) / 2
    inc = math.atan2(d.z, Vector((d.x, d.y, 0)).length)
    Rt = Rr @ Matrix.Rotation(-inc, 3, 'Y')
    caixa(B('calha', 'chapa'), mid, (L, 0.1, 0.008), Rt)
    for s in (-1, 1):
        caixa(B('calha', 'chapa'), mid + Rt @ Vector((0, s * 0.05, 0.03)), (L, 0.008, 0.06), Rt)
    viga(B('calha_pe', 'aco'), mid + Vector((0, 0, -0.01)), Vector((mid.x, mid.y, ZL)), 0.03)
    caixa_de(B('calha_pe', 'ferro'), Vector((mid.x - 0.05, mid.y - 0.05, ZL)), Vector((mid.x + 0.05, mid.y + 0.05, ZL + 0.015)))
    sq = mid + Rt @ Vector((0, 0, 0.09))
    cil(B('soquete_camisa', 'verde'), sq, 0.032, L * 0.6, Rt @ X, lados=18)
    cil(B('soquete_haste', 'cromo'), sq + Rt @ Vector((L * 0.36, 0, 0)), 0.012, L * 0.25, Rt @ X, lados=12)
    for s in (-0.25, 0.25):
        viga(B('soquete_suporte', 'aco'), sq + Rt @ Vector((s * L, 0, -0.03)), mid + Rt @ Vector((s * L, 0.05, 0.06)), 0.014)

    # ---------------- tanque de reagente (iodeto) deitado, selas, cintas, visor, bocal
    torno(B('tanque', 'verde'), [(-0.6, 0), (-0.6, 0.12), (-0.585, 0.17), (-0.56, 0.2), (0.48, 0.2), (0.505, 0.17), (0.52, 0.12), (0.52, 0)],
          TQ, X, n=40)
    for x in (-0.4, 0.3):
        caixa_de(B('selas', 'ferro'), Vector((TQ.x + x - 0.05, TQ.y - 0.17, ZL)), Vector((TQ.x + x + 0.05, TQ.y + 0.17, TQ.z - 0.12)))
        toro(B('tanque_cintas', 'aco'), TQ + Vector((x, 0, 0)), 0.203, 0.008, X, nR=40, nr=6)
    for x in (-0.15, 0.05):
        toro(B('tanque_cintas', 'aco'), TQ + Vector((x, 0, 0)), 0.202, 0.005, X, nR=40, nr=6)
    remendo(TQ + Vector((-0.05, -0.196, 0.0)), -Y, 0.14, 0.1, mat='amarelo2')
    stencil(TQ + Vector((0.18, -0.2, 0.05)), -Y, k=3, alt=0.05)          # "AgI" apagado
    for x in (-0.5, -0.3, 0.1, 0.4):
        escorrido(TQ + Vector((x, -0.2, -0.05)), -Y)
    # visor de nível
    for z in (-0.12, 0.12):
        tubo(B('visor_tubos', 'aco'), TQ + Vector((0.42, -0.2, z)), TQ + Vector((0.42, -0.25, z)), 0.01, 8)
    cil(B('visor_vidro', 'vidro'), TQ + Vector((0.42, -0.255, 0)), 0.014, 0.26, lados=12)
    cil(B('visor_liquido', 'azul'), TQ + Vector((0.42, -0.255, -0.06)), 0.01, 0.13, lados=12)
    # boca de visita no topo e respiro com válvula
    torno(B('tanque_boca', 'aco'), [(0.16, 0), (0.16, 0.08), (0.22, 0.08), (0.22, 0.1), (0.24, 0.1), (0.24, 0)], TQ + Vector((-0.3, 0, 0)), n=24)
    for k in range(8):
        a = k * PI / 4
        parafuso(TQ + Vector((-0.3 + math.cos(a) * 0.088, math.sin(a) * 0.088, 0.242)), Z, r=0.007)
    cano([TQ + Vector((0.1, 0, 0.19)), TQ + Vector((0.1, 0, 0.36)), TQ + Vector((0.18, 0, 0.36))], 0.015, fl=False)
    cil(B('respiro_chapeu', 'ferro'), TQ + Vector((0.2, 0, 0.36)), 0.03, 0.04, X, lados=14)
    # ---------------- mastro do sensor de nuvem (toque da IA) sobre o tanque
    MS = TQ + Vector((-0.5, 0.0, 0.2))
    tubo(B('mastro', 'aco'), MS, MS + Vector((0, 0, 1.05)), 0.022, 16)
    caixa_de(B('mastro_base', 'ferro'), MS + Vector((-0.05, -0.05, -0.01)), MS + Vector((0.05, 0.05, 0.02)))
    torno(B('sensor_caixa', 'grafite'), [(1.0, 0), (1.0, 0.07), (1.12, 0.07), (1.12, 0)], MS, n=24)
    esfera(B('sensor_domo', 'domo', lis=True), MS + Vector((0, 0, 1.12)), 0.06, 20)
    torno(B('sensor_aro', 'aco'), [(1.11, 0.058), (1.11, 0.075), (1.13, 0.075), (1.13, 0.058)], MS, n=24)
    tubo(B('antena', 'aco'), MS + Vector((0.06, 0, 1.05)), MS + Vector((0.06, 0, 1.5)), 0.004, 6)
    esfera(B('antena_led', 'led_ambar'), MS + Vector((0.06, 0, 1.5)), 0.009, 8)
    feixe(bezier(MS + Vector((0.025, 0, 1.0)), MS + Vector((0.03, 0, 0.6)), MS + Vector((0.03, 0, 0.3)), MS + Vector((0.03, -0.02, 0.02)), 10),
          Vector((0, 1, 0)), n=2, r=0.006, passo=3)

    # ---------------- bomba, motor e canos até os queimadores; garrafas de pressão
    PB = Vector((0.72, 0.66, 0.0))
    caixa_de(B('bomba_base', 'ferro'), PB + Vector((-0.14, -0.13, ZL)), PB + Vector((0.2, 0.13, ZL + 0.04)))
    torno(B('bomba_voluta', 'ferro'), [(-0.06, 0), (-0.06, 0.1), (0.06, 0.1), (0.06, 0)], PB + Vector((-0.04, 0, 0.32)), X, n=28)
    torno(B('bomba_motor', 'azul'), [(0.02, 0), (0.02, 0.085), (0.26, 0.085), (0.26, 0.06), (0.28, 0.06), (0.28, 0)], PB + Vector((-0.04, 0, 0.32)), X, n=24)
    for k in range(12):
        a = k * 2 * PI / 12
        caixa(B('bomba_aletas', 'azul'), PB + Vector((0.11, math.cos(a) * 0.088, 0.32 + math.sin(a) * 0.088)), (0.2, 0.012, 0.006),
              Matrix.Rotation(a, 3, 'X'))
    caixa_de(B('bomba_pe', 'ferro'), PB + Vector((-0.08, -0.06, ZL + 0.04)), PB + Vector((0.18, 0.06, 0.24)))
    cano([TQ + Vector((0.5, -0.03, -0.07)), PB + Vector((-0.1, 0, 0.32))], 0.022)
    cano([PB + Vector((-0.04, -0.1, 0.32)), PB + Vector((-0.04, -0.2, 0.32)), Vector((0.9, PB.y - 0.2, 0.32)),
          Vector((0.9, QS[1].y, 0.32)), Vector((0.9, QS[1].y, 0.24)), QS[1] + Vector((0.14, 0, 0.24))], 0.02)
    flange(QS[1] + Vector((0.145, 0, 0.24)), X, 0.034)
    for y in (0.3, -0.1, -0.45):                                           # suportes do cano leste
        viga(B('cano_suportes', 'aco'), Vector((0.9, y, ZL)), Vector((0.9, y, 0.3)), 0.025)
        toro(B('cano_abracadeiras', 'aco'), Vector((0.9, y, 0.32)), 0.024, 0.005, Y, nR=20, nr=5)
    # válvula atuada no cano leste
    VV = Vector((0.9, 0.05, 0.32))
    cil(B('valvula', 'zarcao'), VV, 0.042, 0.1, Y, lados=20)
    tubo(B('valvula_haste', 'aco'), VV + Vector((0, 0, 0.04)), VV + Vector((0, 0, 0.12)), 0.01, 8)
    caixa_de(B('valvula_atuador', 'amarelo'), VV + Vector((-0.04, -0.05, 0.12)), VV + Vector((0.04, 0.05, 0.2)))
    # oeste: saída do fundo do tanque com válvula manual... de roda? não: válvula atuada e cano até o queimador oeste
    cano([TQ + Vector((-0.51, 0, -0.19)), Vector((TQ.x - 0.51, TQ.y, 0.17)), Vector((-0.92, TQ.y, 0.17)),
          Vector((-0.92, QS[0].y, 0.17)), QS[0] + Vector((-0.14, 0, 0.17))], 0.018)
    VO = Vector((-0.92, 0.3, 0.17))
    cil(B('valvula', 'zarcao'), VO, 0.036, 0.09, Y, lados=20)
    caixa_de(B('valvula_atuador', 'amarelo'), VO + Vector((-0.035, -0.04, 0.05)), VO + Vector((0.035, 0.04, 0.12)))
    tubo(B('valvula_haste', 'aco'), VO + Vector((0, 0, 0.03)), VO + Vector((0, 0, 0.05)), 0.008, 8)
    for y in (0.45, -0.2):
        caixa_de(B('cano_suportes', 'aco'), Vector((-0.935, y - 0.015, ZL)), Vector((-0.905, y + 0.015, 0.15)))
    # garrafas de pressão (nitrogênio) que empurram o reagente
    for k, y in enumerate((-0.12, 0.02)):
        pg = Vector((-0.8, y, 0))
        torno(B('garrafas', 'cinza' if False else 'azul' if k else 'zarcao'), [(ZL, 0), (ZL, 0.06), (0.62, 0.06), (0.67, 0.035), (0.69, 0.02), (0.69, 0)], pg, n=24)
        torno(B('garrafas_valvula', 'latao'), [(0.69, 0), (0.69, 0.015), (0.74, 0.015), (0.74, 0)], pg, n=12)
        toro(B('garrafas_cinta', 'aco'), pg + Vector((0, 0, 0.45)), 0.063, 0.007, nR=24, nr=5)
        mangueira(B('mangueiras', 'borracha'), bezier(pg + Vector((0, 0, 0.73)), pg + Vector((-0.05, 0, 0.85)), Vector((-0.92, 0.2, 0.4)),
                                                         Vector((-0.92, 0.22, 0.19)), 10), 0.008)
    caixa_de(B('garrafas_suporte', 'ferro'), Vector((-0.88, -0.2, ZL)), Vector((-0.86, 0.1, 0.5)))
    viga(B('garrafas_suporte', 'aco'), Vector((-0.87, -0.19, 0.45)), Vector((-0.87, 0.09, 0.45)), 0.02)

    # ---------------- queimadores de solo (dois): pote, chaminé, cabeça, ignitor
    for i, q in enumerate(QS):
        torno(B('queimador_pote', 'ferro'), [(ZL, 0), (ZL, 0.15), (0.3, 0.15), (0.33, 0.12), (0.34, 0.12), (0.34, 0)], q, n=32)
        for k in range(8):
            a = k * PI / 4 + 0.2
            parafuso(q + Vector((math.cos(a) * 0.135, math.sin(a) * 0.135, 0.342)), Z, r=0.008)
        torno(B('queimador_chamine', 'chapa'), [(0.34, 0), (0.34, 0.07), (0.95, 0.06), (0.95, 0)], q, n=28)
        torno(B('queimador_cabeca', 'queimado'), [(0.95, 0), (0.95, 0.09), (1.0, 0.11), (1.1, 0.11), (1.1, 0.075), (1.06, 0.075), (1.06, 0)], q, n=28)
        for k in range(12):                                                # fendas da cabeça
            a = k * 2 * PI / 12
            caixa(B('queimador_fendas', 'fuligem'), q + Vector((math.cos(a) * 0.111, math.sin(a) * 0.111, 1.05)), (0.004, 0.018, 0.06),
                  Matrix.Rotation(a, 3, 'Z'))
        for z in (0.5, 0.75):
            toro(B('queimador_cintas', 'aco'), q + Vector((0, 0, z)), 0.067, 0.007, nR=28, nr=6)
        # fuligem escorrendo na chaminé e mancha no chão
        for k in range(10):
            a = random.uniform(0, 2 * PI)
            n_ = Vector((math.cos(a), math.sin(a), 0))
            caixa(B('fuligem_chamine', 'fuligem'), q + n_ * 0.068 + Vector((0, 0, random.uniform(0.75, 0.93))),
                  (random.uniform(0.01, 0.03), 0.003, random.uniform(0.05, 0.25)), rot_face(n_))
        mancha(B('fuligem_chao', 'fuligem'), (q.x, q.y), 0.22, ZL + 0.0012)
        # ignitor: braço com eletrodo sobre a boca e cabo
        s = 1 if i else -1
        ig = q + Vector((s * -0.16, 0.0, 1.0))
        viga(B('ignitor', 'aco'), q + Vector((s * -0.06, 0, 0.9)), ig, 0.016)
        tubo(B('ignitor_eletrodo', 'cobre'), ig, q + Vector((s * -0.05, 0, 1.14)), 0.004, 6)
        caixa_de(B('ignitor_bobina', 'grafite'), q + Vector((-0.04, 0.07, 0.6)), q + Vector((0.04, 0.12, 0.72)))
        fim = Vector((-0.04, -0.85, 0.45)) if i else Vector((-0.36, -0.85, 0.45))
        feixe(bezier(q + Vector((0, 0.12, 0.66)), q + Vector((0, 0.22, 0.6)), fim + Vector((s * 0.25, 0.1, -0.05)), fim, 10),
              Vector((0, 0, 1)), n=2, r=0.006, passo=4)
        # manômetro no pote
        mp = q + Vector((0, -0.15, 0.24))
        tubo(B('manometro_tubo', 'aco'), mp, mp + Vector((0, -0.05, 0.04)), 0.006, 6)
        cil(B('manometro', 'aco'), mp + Vector((0, -0.06, 0.08)), 0.03, 0.02, -Y, lados=18)
        cil(B('manometro_face', 'mostrador'), mp + Vector((0, -0.071, 0.08)), 0.026, 0.002, -Y, lados=18)
    # armário de controle entre os queimadores (alimenta ignitores e bobinas)
    caixa_de(B('armario', 'grafite'), (-0.36, -0.95, ZL), (-0.04, -0.74, 0.62))
    caixa_de(B('armario_porta', 'amarelo2'), (-0.34, -0.955, 0.16), (-0.06, -0.95, 0.58))
    caixa_de(B('armario_teto', 'chapa'), (-0.38, -0.97, 0.62), (-0.02, -0.72, 0.64))
    for z, cor in ((0.52, 'led_verde'), (0.48, 'led_ambar')):
        caixa_de(B('armario_led_' + cor, cor), (-0.12, -0.958, z), (-0.09, -0.955, z + 0.02))
    for k in range(5):
        caixa_de(B('armario_grelha', 'fuligem'), (-0.3, -0.958, 0.22 + k * 0.025), (-0.18, -0.955, 0.232 + k * 0.025))
    stencil(Vector((-0.2, -0.96, 0.4)), -Y, k=4, alt=0.035)
    escorrido(Vector((-0.3, -0.958, 0.6)), -Y)
    escorrido(Vector((-0.08, -0.958, 0.15)), -Y, mat='lama', L=0.05)
    # eletrocalha do armário até a torre (cabos das bobinas sobem por uma perna)
    perna = pernas[0]
    caixa_de(B('eletrocalha', 'aco'), (-0.14, -0.74, ZL), (-0.06, -0.47, ZL + 0.05))
    p0 = perna[0].lerp(perna[1], 0.03)
    pts = [Vector((-0.1, -0.6, ZL + 0.05)), Vector((-0.1, -0.47, ZL + 0.06)), Vector((-0.06, -0.38, ZL + 0.1))] + [perna[0].lerp(perna[1], t) + Vector((0.03, 0.03, 0)) for t in (0.1, 0.3, 0.5, 0.7, 0.9)]
    feixe(pts, Vector((1, -1, 0)).normalized(), n=3, r=0.008, passo=1)
    # cabo em laço folgado do colar até a caixa das bobinas (o cano recua)
    pc = perna[1] + Vector((0.03, 0.03, 0.02))
    feixe(bezier(pc, pc + Vector((0.05, -0.1, 0.25)), G + Vector((0.2, -0.15, 2.3)), G + Vector((0.17, -0.02, 2.2)), 10),
          Vector((0, 0, 1)), n=2, r=0.007, passo=99)
    # mangueiras hidráulicas: unidade (leste) → portas dos pistões
    UH = Vector((0.7, 0.1, 0))
    caixa_de(B('unidade_hidraulica', 'amarelo'), UH + Vector((-0.08, -0.1, ZL)), UH + Vector((0.12, 0.17, 0.42)))
    caixa_de(B('unidade_tampa', 'grafite'), UH + Vector((-0.09, -0.11, 0.42)), UH + Vector((0.13, 0.18, 0.44)))
    torno(B('unidade_motor', 'azul'), [(0.44, 0), (0.44, 0.05), (0.62, 0.05), (0.62, 0)], UH + Vector((0.02, 0.03, 0)), n=20)
    remendo(UH + Vector((0.12, 0.03, 0.25)), X, 0.12, 0.12, mat='chapa')
    for s in (-1, 1):
        porta = G + Vector((s * 0.29, -0.058, 0.22))
        mangueira(B('mangueiras', 'borracha'), bezier(UH + Vector((-0.08, -0.06 + 0.05 * s, 0.3)), UH + Vector((-0.25, -0.1, 0.35)),
                                                         porta + Vector((0, -0.14, 0.05)), porta, 12), 0.009)
    escorrido(UH + Vector((-0.081, 0.0, 0.3)), -X, mat='oleo', L=0.2)
    mancha(B('oleo_chao', 'oleo'), (UH.x - 0.12, UH.y), 0.07, ZL + 0.0015)
    # estojos vazios espalhados: no chão da frente e na laje (vários disparos antigos)
    for k in range(22):
        if k < 9:
            p = Vector((random.uniform(-0.05, 0.6), random.uniform(-0.98, -0.5), ZL))
            if (-0.4 < p.x < 0.0 and p.y < -0.72) or (p - QS[1]).length < 0.24 or (p.x < -0.02 and p.y > -0.75):
                continue
        else:
            a = random.uniform(-PI * 0.85, -PI * 0.2)
            r = random.uniform(1.15, 2.0)
            p = Vector((G.x + math.cos(a) * r, math.sin(a) * r, 0.0))
            p.z = chao_h(p.x, p.y)
            if abs(p.x) < 1.1 and abs(p.y) < 1.1 and p.z == 0.0:
                continue
        e = estojo('estojo_velho', random.random() < 0.6, velho=True)
        e.location = p + Vector((0, 0, 0.037))
        e.rotation_euler = (PI / 2, 0, random.uniform(0, 2 * PI))
    # ---------------- objetos animados
    CENA = {'G': G, 'CAR': CAR, 'QS': QS, 'culatra': culatra, 'carrossel': GR['carrossel']}


PERFIL_ESTOJO = [(0.0, 0.0), (0.0, 0.039), (0.012, 0.039), (0.012, 0.032), (0.02, 0.032), (0.026, 0.036), (0.19, 0.036),
                 (0.2, 0.034), (0.2, 0.031), (0.175, 0.031), (0.175, 0.0)]


def estojo(nome, aco=False, velho=False):
    """Estojo vazio (0,2 m, Ø 72 mm): aro e ranhura do extrator, corpo, espoleta e boca queimada. Origem no meio
    do comprimento, eixo z local."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    bm = bmesh.new()
    torno(bm, [(z - 0.1, r) for z, r in PERFIL_ESTOJO], n=24)
    suavizar(obj(nome + '_corpo', bm, 'aco_estojo' if aco else 'latao', e))
    bm = bmesh.new()
    torno(bm, [(0.188 - 0.1, 0.0), (0.188 - 0.1, 0.0362), (0.2 - 0.1, 0.0345), (0.2 - 0.1, 0.0)], n=24)
    torno(bm, [(0.17 - 0.1, 0.0), (0.17 - 0.1, 0.0312), (0.176 - 0.1, 0.0312), (0.176 - 0.1, 0.0)], n=24)
    b = obj(nome + '_boca', bm, 'fuligem' if velho else 'brasa', e)
    bm = bmesh.new()
    torno(bm, [(0.06 - 0.1, 0.0), (0.06 - 0.1, 0.0365), (0.085 - 0.1, 0.0365), (0.085 - 0.1, 0.0)], n=24)
    obj(nome + '_faixa', bm, 'fuligem' if velho else 'zarcao', e)
    bm = bmesh.new()
    torno(bm, [(-0.1012, 0.0), (-0.1012, 0.012), (-0.099, 0.012), (-0.099, 0.0)], n=14)
    obj(nome + '_espoleta', bm, 'espoleta', e)
    return e


def cartucho_cheio(c, g, k):
    """Cartucho de semeadura em pé no carrossel: estojo + projétil de iodeto com cinta de cobre e ponta âmbar."""
    c = Vector(c)
    torno(B('cartuchos_estojo', 'latao' if k % 3 else 'aco_estojo', g), [(z, r) for z, r in PERFIL_ESTOJO[:7]] + [(0.2, 0.034), (0.2, 0)], c, n=20)
    torno(B('cartuchos_projetil', 'aluminio', g), [(0.2, 0), (0.2, 0.033), (0.29, 0.033), (0.32, 0.029), (0.345, 0.018), (0.355, 0.006), (0.356, 0)], c, n=20)
    torno(B('cartuchos_cinta', 'cobre', g), [(0.212, 0), (0.212, 0.0345), (0.226, 0.0345), (0.226, 0)], c, n=20)
    torno(B('cartuchos_ponta', 'led_ambar' if k % 4 == 2 else 'zarcao', g), [(0.343, 0), (0.343, 0.019), (0.356, 0.005), (0.357, 0)], c, n=16)
    torno(B('cartuchos_faixa', 'azul', g), [(0.25, 0), (0.25, 0.0335), (0.265, 0.0335), (0.265, 0)], c, n=20)


# ------------------------------------------------------------------ semeador: efeitos e animação
TIROS = [10, 42, 74]
Z_BOCA = 3.42
Z_NUVEM = 13.0


def chao_h(x, y):
    return ZL if (abs(x) < 1.0 and abs(y) < 1.0) else 0.0


def traj_estojo(semente, p0, v0):
    """Física simples: voo girando, quiques com perda, rola até parar deitado. (pos, euler, no_ar) por quadro."""
    rnd = random.Random(semente)
    p, v = Vector(p0), Vector(v0)
    th, w_th = 0.0, rnd.uniform(14, 20)
    psi, w_psi = rnd.uniform(0, 2 * PI), rnd.uniform(-5, 5)
    R = 0.037
    passo = 1 / 240
    t = 0.0
    quiques = 0
    no_chao = False
    out = []
    for e in range(1, QUADROS + 1):
        while t < e / FPS - 1e-9:
            t += passo
            if not no_chao:
                v.z -= 9.81 * passo
                p += v * passo
                th += w_th * passo
                psi += w_psi * passo
                h = chao_h(p.x, p.y)
                if p.z - R <= h:
                    p.z = h + R
                    if v.z < -0.5 and quiques < 3:
                        v.z = -v.z * 0.32
                        v.x *= 0.5
                        v.y *= 0.5
                        w_th *= 0.45
                        quiques += 1
                    else:
                        v.z = 0.0
                        no_chao = True
            else:
                h = chao_h(p.x, p.y)
                if p.z - R > h + 0.02:
                    no_chao = False
                    continue
                p.z = h + R
                vh = Vector((v.x, v.y, 0))
                s = vh.length
                if s > 0:
                    vh *= max(0.0, s - 2.0 * passo) / s
                v = vh
                p += v * passo
                th += (round((th - PI / 2) / PI) * PI + PI / 2 - th) * min(1.0, 12 * passo)
                w_psi *= math.exp(-6 * passo)
                psi += w_psi * passo
        out.append((p.copy(), (th, 0.0, psi), not no_chao, v.length))
    return out


def efeitos_semeador():
    """Cria os objetos animados (estojos, rastros, clarões, fumaças, chamas, partículas, nuvem, chuva)."""
    G, QS = CENA['G'], CENA['QS']
    ef = {}
    # estojos ejetados (um por tiro) com fiapo de fumaça e última fumacinha
    ef['estojos'] = []
    for k, t0 in enumerate(TIROS):
        e = estojo('estojo_tiro%d' % k, aco=(k == 1))
        e.rotation_mode = 'XYZ'
        fi = bolha('fiapo%d' % k, 'fiapo', 1.0, 2)
        ul = bolha('ultima%d' % k, 'fiapo', 1.0, 2)
        porta = G + Vector((0.0, -0.2, 0.78))
        v0 = Vector((random.uniform(0.15, 0.4), -2.1 - 0.25 * k, 1.6))
        tr = traj_estojo(11 + k, porta, v0)
        ef['estojos'].append((e, fi, ul, t0, tr))
    marca('estojos')
    # rastros (um por tiro), projétil e clarão de boca
    ef['rastros'] = []
    for k in range(3):
        bm = bmesh.new()
        L = Z_NUVEM - Z_BOCA + 0.5
        torno(bm, [(-0.05, 0.0), (0.0, 0.08), (0.9, 0.62), (L, 1.0), (L, 0.0)], n=16)
        r = obj('rastro%d' % k, bm, 'rastro')
        pj = bpy.data.objects.new('projetil%d' % k, None)
        sc.collection.objects.link(pj)
        bm = bmesh.new()
        torno(bm, [(0, 0), (0, 0.033), (0.09, 0.033), (0.12, 0.029), (0.145, 0.018), (0.156, 0)], n=16)
        obj('projetil%d_corpo' % k, bm, 'aluminio', pj)
        bm = bmesh.new()
        esfera(bm, (0, 0, -0.05), 0.06, 12)
        obj('projetil%d_brasa' % k, bm, 'faisca', pj)
        es = bolha('estouro%d' % k, 'estouro', 1.0, 3)
        ef['rastros'].append((r, pj, es))
    marca('rastros')
    ef['clarao'] = bolha('clarao', 'fogo', 1.0, 3)
    ef['fumaca_boca'] = [bolha('fumaca_boca%d' % k, 'fumaca_boca', 1.0, 3) for k in range(3)]
    luz = bpy.data.lights.new('Luz boca', 'POINT')
    luz.color = (1.0, 0.55, 0.2)
    luz.shadow_soft_size = 0.1
    lo = bpy.data.objects.new('Luz boca', luz)
    sc.collection.objects.link(lo)
    ef['luz_boca'] = (lo, luz)
    # chamas e plumas dos queimadores, partículas cintilantes
    ef['chamas'] = []
    for i, q in enumerate(QS):
        ch = bolha('chama%d' % i, 'fogo', 1.0, 3)
        pl = [bolha('pluma%d' % i, 'pluma_escura' if j == 0 else 'pluma', 1.0, 3) for j in range(5)]
        lz = bpy.data.lights.new('Luz chama%d' % i, 'POINT')
        lz.color = (1.0, 0.5, 0.15)
        lz.shadow_soft_size = 0.08
        lzo = bpy.data.objects.new('Luz chama%d' % i, lz)
        sc.collection.objects.link(lzo)
        lzo.location = q + Vector((0, 0, 1.25))
        parts = []
        for j in range(26):
            bm = bmesh.new()
            esfera(bm, (0, 0, 0), random.uniform(0.004, 0.009), 6)
            parts.append((obj('particula', bm, 'particula'), random.random(), random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25)))
        ef['chamas'].append((q, ch, lz, parts, pl))
    # faísca no ignitor
    # nuvem, estouros, luz violeta, cortina e riscos de chuva
    nv = bolha('nuvem', 'nuvem', 1.0, 4)
    nv.location = (0.4, 0.6, Z_NUVEM + 2.6)
    nv.scale = (R_CHUVA * 1.35, R_CHUVA * 1.25, 4.4)
    ef['nuvem'] = nv
    lv = bpy.data.lights.new('Luz nuvem', 'POINT')
    lv.color = VIOLETA
    lv.shadow_soft_size = 2.0
    lvo = bpy.data.objects.new('Luz nuvem', lv)
    sc.collection.objects.link(lvo)
    lvo.location = (1.5, -1.0, Z_NUVEM + 0.8)
    ef['luz_nuvem'] = lv
    co = bolha('cortina', 'cortina', 1.0, 3)
    co.location = (0.2, 0.3, Z_NUVEM * 0.5)
    co.scale = (R_CHUVA, R_CHUVA, Z_NUVEM * 0.62)
    cor_vol(co, 1.0)
    ef['cortina'] = co
    PER = 4.0
    bm = bmesh.new()
    for k in range(16000):
        a = random.uniform(0, 2 * PI)
        r = R_CHUVA * math.sqrt(random.random()) * 0.96
        x, y = math.cos(a) * r + 0.2, math.sin(a) * r + 0.3
        z = random.uniform(0, Z_NUVEM + PER)
        Lr = random.uniform(0.35, 0.6)
        for dx, dy in ((0.0045, 0.0), (0.0, 0.0045)):                     # risco em cruz: dois planos finos
            v1 = bm.verts.new((x - dx, y - dy, z))
            v2 = bm.verts.new((x + dx, y + dy, z))
            v3 = bm.verts.new((x + dx + 0.03, y + dy + 0.015, z + Lr))
            v4 = bm.verts.new((x - dx + 0.03, y - dy + 0.015, z + Lr))
            bm.faces.new((v1, v2, v3, v4))
    marca('riscos')
    ch = obj('chuva', bm, 'chuva')
    ef['chuva'] = (ch, PER)
    # respingos no chão e na laje
    resp = []
    for k in range(60):
        bm = bmesh.new()
        toro(bm, (0, 0, 0), 1.0, 0.25, Z, nR=12, nr=5)
        for j in range(6):
            a = j * PI / 3
            tubo(bm, Vector((math.cos(a), math.sin(a), 0)), Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, 1.8)), 0.2, 4)
        o = obj('respingo', bm, 'gota')
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.0, 4.5)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        p.z = chao_h(p.x, p.y) + 0.002
        resp.append((o, p, random.random(), random.uniform(0.012, 0.022)))
    ef['respingos'] = resp
    return ef


def estado_semeador(est, ef):
    chuva_on = est == 'chuva'
    for o in (ef['chuva'][0], ef['cortina']) + tuple(r[0] for r in ef['respingos']):
        o.hide_render = not chuva_on
    nv = ef['nuvem']
    cor_vol(nv, 2.2 if chuva_on else 0.9, 0, 0.85 if chuva_on else 0.0)
    M['terra'].node_tree.nodes['chuva_on'].inputs[1].default_value = 1.0 if chuva_on else 0.0
    for m in bpy.data.materials:
        if m.node_tree and 'molhado' in m.node_tree.nodes:
            m.node_tree.nodes['molhado'].inputs[1].default_value = 0.4 if chuva_on else 1.0
    if chuva_on:
        ceu_sol(76, -120)
        sol_d.energy = 3.2
        sol_d.angle = math.radians(3)
        bg.inputs['Strength'].default_value = 0.2
        sc.view_settings.exposure = -0.35
    else:
        ceu_sol(62, -125)
        sol_d.energy = 3.5
        sol_d.angle = math.radians(2)
        bg.inputs['Strength'].default_value = 0.25
        sc.view_settings.exposure = -0.2


def animar_semeador(est, ef):
    G = CENA['G']
    culatra, carrossel = CENA['culatra'], CENA['carrossel']
    chuva_on = est == 'chuva'
    bobina = M['bobina'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    brasa = M['brasa'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    domo = M['domo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    lb_o, lb = ef['luz_boca']
    ch_obj, PER = ef['chuva']
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        idade = [(q - t) % QUADROS for t in TIROS]
        dt = min(idade)
        # recuo da culatra e cano
        rec = 0.0
        if dt < 2:
            rec = 0.055
        elif dt < 12:
            rec = 0.055 * (1 - suave((dt - 2) / 10))
        culatra.location = (G.x, G.y, -rec)
        chave(culatra, ('location',), q)
        # carrossel indexa 36° depois de cada tiro
        n_tiros = sum(1 for t in TIROS if q >= t + 14) + sum(suave((q - t - 6) / 8) for t in TIROS if t + 6 <= q < t + 14)
        carrossel.rotation_euler = (0, 0, -2 * PI / 10 * n_tiros)
        chave(carrossel, ('rotation_euler',), q)
        # bobinas: pulso forte no tiro
        bobina.default_value = 4.0 + 2.0 * math.sin(2 * PI * fr * 6) + (30.0 if dt < 2 else 0.0)
        bobina.keyframe_insert('default_value', frame=q)
        domo.default_value = 2.0 + 1.0 * math.sin(2 * PI * fr * 2)
        domo.keyframe_insert('default_value', frame=q)
        # clarão de boca e luz
        boca = G + Vector((0, 0, Z_BOCA - rec))
        fl = {0: 1.0, 1: 0.7, 2: 0.35}.get(dt, 0.0)
        cl = ef['clarao']
        cl.location = boca + Vector((0, 0, 0.25))
        cl.scale = (max(0.05, 0.22 * fl), max(0.05, 0.22 * fl), max(0.05, 0.45 * fl))
        mostra(cl, fl > 0.2, q)
        chave(cl, ('location', 'scale'), q)
        lb_o.location = boca + Vector((0, 0, 0.3))
        lb.energy = 900 * fl
        chave(lb_o, ('location',), q)
        lb.keyframe_insert('energy', frame=q)
        # fumaça da boca (uma por tiro): sobe, abre e dilui
        for k, fb in enumerate(ef['fumaca_boca']):
            a = idade[k]
            u = a / QUADROS
            fb.location = G + Vector((0.4 * u, 0.25 * u, Z_BOCA + 0.15 + 1.6 * u ** 0.6))
            s = 0.12 + 0.75 * u ** 0.5
            fb.scale = (s, s, s * 0.8)
            cor_vol(fb, (1 - u) ** 1.5 * (0.0 if a == 0 else 1.0))
            chave(fb, ('location', 'scale', 'color'), q)
        # rastros, projéteis e estouros na base da nuvem
        for k, (r, pj, es) in enumerate(ef['rastros']):
            a = idade[k]
            L = Z_NUVEM - Z_BOCA + 0.5
            sub = min(1.0, (a + 0.5) * 2.4 / L)
            u = a / QUADROS
            deriva = Vector((0.9 * u, 0.6 * u, 0))
            r.location = G + Vector((0, 0, Z_BOCA)) + deriva * 0.3
            r.scale = (0.11 + 0.9 * u, 0.11 + 0.9 * u, max(0.02, sub))
            r.rotation_euler = (math.radians(-2.5) * u * 0, math.radians(4) * u, 0)
            cor_vol(r, (1 - u) ** 1.2 * 1.0)
            mostra(r, a > 0 or True, q)
            chave(r, ('location', 'scale', 'rotation_euler', 'color'), q)
            zp = Z_BOCA + 0.1 + a * 2.4
            pj.location = G + Vector((0, 0, zp))
            chave(pj, ('location',), q)
            for c_ in pj.children:
                mostra(c_, zp < Z_NUVEM, q)
            ea = a - int((Z_NUVEM - Z_BOCA) / 2.4)
            es.location = G + Vector((0.2, 0.1, Z_NUVEM + 0.2))
            s = 0.4 + 2.2 * max(0, ea) / 14
            es.scale = (s, s, s * 0.6)
            cor_vol(es, max(0.0, 1 - ea / 14) if ea >= 0 else 0.0, max(0.0, 1 - ea / 6) if ea >= 0 else 0.0)
            mostra(es, 0 <= ea < 14, q)
            chave(es, ('location', 'scale', 'color'), q)
        # estojos ejetados: dentro da culatra até a ejeção, depois a trajetória
        for k, (e, fi, ul, t0, tr) in enumerate(ef['estojos']):
            a = q - t0 - 3
            if a < 0:
                mostra_tudo(e, False, q)
                mostra(fi, False, q)
                mostra(ul, False, q)
                continue
            p, eu, no_ar, vel = tr[min(a, len(tr) - 1)]
            e.location = p
            e.rotation_euler = (eu[0] + PI / 2 * 0, eu[1], eu[2])
            chave(e, ('location', 'rotation_euler'), q)
            mostra_tudo(e, True, q)
            # boca quente esfriando
            # fiapo de fumaça seguindo o estojo
            fi.location = p + Vector((0, 0, 0.06 + min(0.15, a * 0.01)))
            s = 0.035 + a * 0.004
            fi.scale = (s, s, s * 1.8)
            cor_vol(fi, max(0.0, 1 - a / 30))
            mostra(fi, a < 30, q)
            chave(fi, ('location', 'scale', 'color'), q)
            # última fumacinha quando para
            parou = next((i for i, x in enumerate(tr) if not x[2] and x[3] < 0.02), len(tr) - 1)
            b = a - parou
            ul.location = tr[parou][0] + Vector((0, 0, 0.05 + 0.012 * max(0, b)))
            s = 0.03 + 0.005 * max(0, b)
            ul.scale = (s, s, s * 1.6)
            cor_vol(ul, max(0.0, 1 - b / 20) if b >= 0 else 0.0)
            mostra(ul, 0 <= b < 20, q)
            chave(ul, ('location', 'scale', 'color'), q)
        brasa.default_value = 9.0 * max(0.0, 1 - min(idade) / 40)
        brasa.keyframe_insert('default_value', frame=q)
        # chamas dos queimadores tremendo, partículas subindo em espiral
        for i, (qq, ch, lz, parts, pl) in enumerate(ef['chamas']):
            f = 1 + 0.18 * math.sin(2 * PI * fr * 9 + i * 1.7) + 0.1 * math.sin(2 * PI * fr * 23 + i)
            ch.location = qq + Vector((0, 0, 1.18))
            ch.scale = (0.07 * f, 0.07 * f, 0.19 * f)
            chave(ch, ('location', 'scale'), q)
            sd = 1 if i else -1
            for j, o in enumerate(pl):                                     # baforadas subindo e abrindo
                if j == 0:
                    o.location = qq + Vector((0, 0, 1.42))
                    o.scale = (0.07, 0.07, 0.14)
                    cor_vol(o, 0.8)
                else:
                    u = ((j - 1) / 4 + fr) % 1.0
                    o.location = qq + Vector((sd * 0.25 * u + 0.05 * math.sin(j * 2), 0.15 * u, 1.5 + 3.2 * u))
                    sz = 0.1 + 0.55 * u
                    o.scale = (sz, sz, sz * 1.3)
                    cor_vol(o, math.sin(PI * min(1.0, u * 1.15)) ** 0.7 * (1 - u) ** 0.5)
                chave(o, ('location', 'scale', 'color'), q)
            lz.energy = 25 * f
            lz.keyframe_insert('energy', frame=q)
            for j, (o, ph, dx, dy) in enumerate(parts):
                u = (ph + fr * 2) % 1.0
                ang = 2 * PI * (u * 1.5 + ph)
                o.location = qq + Vector((math.cos(ang) * (0.06 + 0.5 * u) + dx * u * 1.5 + 0.15 * u * (1 if i else -1),
                                          math.sin(ang) * (0.06 + 0.5 * u) + dy * u * 1.5 + 0.1 * u, 1.2 + u * 3.0))
                chave(o, ('location',), q)
        # luz violeta piscando dentro da nuvem (estouros de semeadura)
        flash = max([max(0.0, 1 - ((q - t - 5) % QUADROS) / 8) if ((q - t - 5) % QUADROS) < 8 else 0.0 for t in TIROS])
        ef['luz_nuvem'].energy = (8000 if chuva_on else 3000) * flash + (600 if chuva_on else 0)
        ef['luz_nuvem'].keyframe_insert('energy', frame=q)
        if chuva_on:
            ch_obj.location = (0, 0, -((fr * 10 * PER) % PER))
            chave(ch_obj, ('location',), q)
            for o, p, ph, tam in ef['respingos']:
                u = (ph + fr * 3) % 1.0
                s = tam * (0.3 + u * 1.2)
                o.location = p
                o.scale = (s, s, max(0.0005, s * (1 - u) * 1.2))
                chave(o, ('location', 'scale'), q)
    interp_linear()


def mostra_tudo(e, vis, q):
    for c in e.children:
        mostra(c, vis, q)


# ====================================================================================================================
#                                          DEFLETOR DE VENTO
# ====================================================================================================================
AW = math.radians(25)                     # direção forçada do vento (para onde sopra), a partir do leste
W = Vector((math.cos(AW), math.sin(AW), 0))
Z_GIRO = 0.36
Z_TOPO = 3.3
X_PAL = 0.45                              # eixo de pivô das palhetas (x local)
Y_PAL = [-0.48, -0.24, 0.0, 0.24, 0.48]
Z_PAL0, Z_PAL1 = 0.7, 2.66
ANG_PAL = [math.radians(a) for a in (-17, -8, 0, 8, 17)]       # leque
Z_FANS = [1.04, 2.16]
X_FAN = -0.45
R_DUTO = 0.48


def defletor():
    global CENA
    laje()
    pedrinhas(140, 0.02, 9.0)
    # ---------------- base fixa: pedestal, rolamento, motorredutores, armário, eletrocalha
    torno(B('pedestal', 'ferro'), [(ZL, 0), (ZL, 0.56), (0.17, 0.56), (0.19, 0.5), (0.2, 0.5), (0.2, 0)], n=48)
    for k in range(16):
        a = k * 2 * PI / 16
        parafuso((math.cos(a) * 0.53, math.sin(a) * 0.53, 0.172), Z, r=0.011)
        v = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('pedestal_nervuras', 'ferro'), v * 0.585 + Vector((0, 0, ZL + 0.025)), (0.05, 0.014, 0.05), Matrix.Rotation(a, 3, 'Z'))
    torno(B('rolamento', 'aco'), [(0.2, 0.0), (0.2, 0.52), (0.26, 0.52), (0.26, 0.0)], n=64)
    toro(B('rolamento_graxa', 'oleo'), (0, 0, 0.2), 0.52, 0.008, nR=64, nr=6)
    MOT = []
    for s in (-1, 1):
        a = PI / 2 + s * PI / 2 - PI / 2 * 0.6
        a = math.radians(-30) if s > 0 else math.radians(150)
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        pc = d * 0.71
        cil(B('pinhoes', 'aco'), pc + Vector((0, 0, 0.3)), 0.06, 0.08, lados=20)
        for k in range(14):
            aa = k * 2 * PI / 14
            caixa(B('pinhoes', 'aco'), pc + Vector((math.cos(aa) * 0.064, math.sin(aa) * 0.064, 0.3)), (0.016, 0.012, 0.08), Matrix.Rotation(aa, 3, 'Z'))
        caixa(B('redutor', 'amarelo'), pc + Vector((0, 0, 0.18)), (0.2, 0.2, 0.12), Matrix.Rotation(a, 3, 'Z'))
        cil(B('redutor_eixo', 'aco'), pc + Vector((0, 0, 0.25)), 0.03, 0.03, lados=14)
        cil(B('motor_giro', 'azul'), pc + t * 0.2 + Vector((0, 0, 0.19)), 0.07, 0.24, t, lados=22)
        for k in range(10):
            aa = k * 2 * PI / 10
            u, v, w = base_de(t)
            caixa(B('motor_giro_aletas', 'azul'), pc + t * 0.2 + Vector((0, 0, 0.19)) + (u * math.cos(aa) + v * math.sin(aa)) * 0.073,
                  (0.012, 0.012, 0.2), Matrix((u, v, w)).transposed() @ Matrix.Rotation(aa, 3, 'Z'))
        cil(B('motor_giro_tampa', 'grafite'), pc + t * 0.33 + Vector((0, 0, 0.19)), 0.06, 0.03, t, lados=16)
        caixa_de(B('redutor_base', 'ferro'), pc + Vector((-0.14, -0.14, ZL)), pc + Vector((0.14, 0.14, ZL + 0.03)))
        MOT.append(pc)
        escorrido(pc + d * 0.1 + Vector((0, 0, 0.27)), d, mat='oleo', L=0.1)
    # armário de controle no canto SO (fora do giro) e eletrocalha até o anel coletor
    caixa_de(B('armario', 'grafite'), (-0.97, -0.97, ZL), (-0.7, -0.74, 0.74))
    caixa_de(B('armario_porta', 'amarelo2'), (-0.95, -0.975, 0.18), (-0.72, -0.97, 0.7))
    caixa_de(B('armario_teto', 'chapa'), (-0.99, -0.99, 0.74), (-0.68, -0.72, 0.76))
    for z, cor in ((0.62, 'led_verde'), (0.58, 'led_ambar')):
        caixa_de(B('armario_led_' + cor, cor), (-0.78, -0.978, z), (-0.75, -0.975, z + 0.02))
    stencil(Vector((-0.86, -0.98, 0.46)), -Y, k=4, alt=0.035)
    remendo(Vector((-0.97 - 0.0, -0.86, 0.4)), -X, 0.12, 0.16, mat='zarcao')
    caixa_de(B('eletrocalha', 'aco'), (-0.75, -0.72, ZL), (-0.4, -0.64, ZL + 0.05))
    feixe([Vector((-0.73, -0.68, ZL + 0.05)), Vector((-0.6, -0.68, ZL + 0.07)), Vector((-0.45, -0.6, ZL + 0.07)), Vector((-0.38, -0.5, 0.17))],
          Vector((0, 1, 0)), n=3, r=0.008, passo=1)
    for pc in MOT:
        feixe(bezier(Vector((-0.73, -0.7, ZL + 0.06)), Vector((-0.5, -0.9, 0.2)), pc + Vector((0, -0.25, 0.3)), pc + Vector((0, -0.12, 0.25)), 12),
              Vector((0, 0, 1)), n=2, r=0.007, passo=4)
    # ---------------- cabeça giratória (giro)
    grupo('giro', (0, 0, 0), rz=AW)
    g = 'giro'
    torno(B('plataforma', 'chapa', g), [(0.26, 0), (0.26, 0.6), (Z_GIRO, 0.6), (Z_GIRO, 0)], n=64)
    torno(B('plataforma_borda', 'amarelo', g), [(0.255, 0.585), (0.255, 0.61), (Z_GIRO + 0.005, 0.61), (Z_GIRO + 0.005, 0.585)], n=64)
    for k in range(120):                                                  # coroa dentada (gira contra os pinhões)
        a = k * 2 * PI / 120
        caixa(B('coroa_dentes', 'aco', g), Vector((math.cos(a) * 0.612, math.sin(a) * 0.612, 0.3)), (0.026, 0.014, 0.08), Matrix.Rotation(a, 3, 'Z'))
    for k in range(24):
        a = k * 2 * PI / 24
        parafuso((math.cos(a) * 0.56, math.sin(a) * 0.56, Z_GIRO + 0.004), Z, g, 0.009)
    for k in range(8):
        mancha(B('plataforma_po', 'po', g), (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)), random.uniform(0.04, 0.09), Z_GIRO + 0.001)
    # coluna octogonal
    octo(B('coluna', 'amarelo', g), (0, 0), 0.18, Z_GIRO, Z_TOPO)
    for z in (Z_GIRO + 0.05, 1.6, Z_TOPO - 0.06):
        octo(B('coluna_flanges', 'aco', g), (0, 0), 0.2, z - 0.02, z + 0.02)
    for z in (0.9, 1.6, 2.4):
        for k in range(8):
            a = PI / 8 + k * PI / 4
            parafuso((math.cos(a) * 0.205, math.sin(a) * 0.205, z + 0.025 * (1 if z != 1.6 else 0)), (math.cos(a), math.sin(a), 0), g, 0.008)
    remendo(Vector((0.0, -0.18, 1.3)), -Y, 0.12, 0.2, g, 'zarcao')
    remendo(Vector((0.0, 0.18, 2.6)), Y, 0.1, 0.14, g, 'chapa')
    stencil(Vector((0.0, -0.181, 1.85)), -Y, g, k=4, alt=0.04)
    for z in (1.0, 2.0, 3.1):
        for a in (0.4, 2.0, 4.1):
            n_ = Vector((math.cos(a), math.sin(a), 0))
            escorrido(n_ * 0.172 + Vector((0, 0, z)), n_, g)
    for k in range(14):                                                    # poeira presa no lado de barlavento
        z = random.uniform(0.5, 3.1)
        a = random.uniform(PI * 0.75, PI * 1.25)
        n_ = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('coluna_po', 'po', g), n_ * 0.168 + Vector((0, 0, z)), (random.uniform(0.04, 0.1), 0.004, random.uniform(0.02, 0.06)), rot_face(n_))
    # ---------------- ventiladores dutados (dois)
    FANS = []
    for i, zf in enumerate(Z_FANS):
        c = Vector((X_FAN, 0, zf))
        torno(B('dutos', 'amarelo2' if i else 'amarelo', g), [(-0.19, R_DUTO + 0.05), (-0.17, R_DUTO), (0.17, R_DUTO), (0.19, R_DUTO + 0.03),
                                                              (0.19, R_DUTO + 0.05), (0.13, R_DUTO + 0.06), (-0.13, R_DUTO + 0.06), (-0.19, R_DUTO + 0.05)],
              c, X, n=64)
        for xx in (-0.12, 0.12):
            toro(B('dutos_aros', 'aco', g), c + Vector((xx, 0, 0)), R_DUTO + 0.062, 0.01, X, nR=64, nr=6)
        for k in range(20):
            a = k * 2 * PI / 20
            parafuso(c + Vector((0.12, math.cos(a) * (R_DUTO + 0.072), math.sin(a) * (R_DUTO + 0.072))), (0, math.cos(a), math.sin(a)), g, 0.008)
        # grade de entrada (barlavento): anéis e raios
        for rr in (0.16, 0.28, 0.4):
            toro(B('grade', 'aco', g), c + Vector((-0.2, 0, 0)), rr, 0.006, X, nR=48, nr=5)
        for k in range(12):
            a = k * 2 * PI / 12
            tubo(B('grade', 'aco', g), c + Vector((-0.2, math.cos(a) * 0.14, math.sin(a) * 0.14)),
                 c + Vector((-0.2, math.cos(a) * (R_DUTO + 0.02), math.sin(a) * (R_DUTO + 0.02))), 0.006, 6)
        # motor (atrás do cubo, barlavento) preso por 4 raios estatores
        torno(B('fan_motor', 'grafite', g), [(-0.47, 0), (-0.47, 0.09), (-0.44, 0.13), (-0.12, 0.13), (-0.08, 0.1), (-0.06, 0)], c, X, n=28)
        for k in range(16):
            a = k * 2 * PI / 16
            caixa(B('fan_motor_aletas', 'grafite', g), c + Vector((-0.28, math.cos(a) * 0.135, math.sin(a) * 0.135)), (0.26, 0.012, 0.012),
                  Matrix.Rotation(a, 3, 'X'))
        for k in range(4):
            a = k * PI / 2 + PI / 4
            d = Vector((0, math.cos(a), math.sin(a)))
            viga(B('fan_estatores', 'aco', g), c + Vector((-0.15, 0, 0)) + d * 0.12, c + Vector((-0.15, 0, 0)) + d * (R_DUTO + 0.005), 0.026)
        feixe(bezier(c + Vector((-0.4, 0, 0.13)), c + Vector((-0.4, 0, 0.3)), c + Vector((-0.2, 0, R_DUTO + 0.1)), Vector((-0.17, 0, zf + 0.2)), 10),
              Vector((0, 1, 0)), g, n=2, r=0.008, passo=99)
        # braços do duto até a coluna (dois por lado)
        for s in (-1, 1):
            for dz in (-0.3, 0.3):
                pa = c + Vector((0.1, s * (R_DUTO + 0.05) * 0.85, dz))
                viga(B('dutos_bracos', 'amarelo', g), pa, Vector((-0.15, s * 0.08, zf + dz * 0.7)), 0.04)
        # rotor (gira em x): cubo e 7 pás torcidas
        rot = grupo('rotor%d' % i, tuple(c), g)
        gr = 'rotor%d' % i
        torno(B('rotor_cubo', 'aco', gr), [(-0.07, 0), (-0.07, 0.11), (0.06, 0.11), (0.11, 0.06), (0.13, 0)], (0, 0, 0), X, n=24)
        for k in range(7):
            a0 = k * 2 * PI / 7
            bm = B('rotor_pas', 'grafite', gr)
            secs = []
            for j in range(6):
                r = 0.1 + (R_DUTO - 0.115) * j / 5
                tw = math.radians(50 - 30 * j / 5)
                corda = 0.13 - 0.03 * j / 5
                a = a0
                rad = Vector((0, math.cos(a), math.sin(a)))
                tg = Vector((0, -math.sin(a), math.cos(a)))
                dx = X * math.sin(tw) + tg * math.cos(tw)
                nn = (X * math.cos(tw) - tg * math.sin(tw))
                p = rad * r
                sec = [p - dx * corda * 0.5 - nn * 0.006, p + dx * corda * 0.5 - nn * 0.002, p + dx * corda * 0.5 + nn * 0.002, p - dx * corda * 0.5 + nn * 0.01]
                secs.append([bm.verts.new(v) for v in sec])
            for j in range(5):
                A, Bq = secs[j], secs[j + 1]
                for m in range(4):
                    bm.faces.new((A[m], A[(m + 1) % 4], Bq[(m + 1) % 4], Bq[m]))
            bm.faces.new(secs[-1])
            bm.faces.new(list(reversed(secs[0])))
        FANS.append(rot)
    # ---------------- cascata de palhetas: quadro, palhetas, pistões
    caixa_de(B('quadro_deck', 'chapa', g), (0.28, -0.66, 0.47), (0.53, 0.66, 0.52))
    caixa_de(B('quadro_deck_borda', 'amarelo', g), (0.28, -0.67, 0.44), (0.54, 0.67, 0.47))
    caixa_de(B('quadro_topo', 'amarelo', g), (0.39, -0.67, 2.74), (0.51, 0.67, 2.82))
    for s in (-1, 1):
        caixa_de(B('quadro_postes', 'amarelo', g), (0.4, s * 0.66 - 0.03, 0.47), (0.5, s * 0.66 + 0.03, 2.82))
        for z in (0.48, 2.78):
            viga(B('quadro_bracos', 'aco', g), Vector((0.17, s * 0.12, z)), Vector((0.41, s * 0.12, z)), 0.05)
        viga(B('quadro_diagonais', 'aco', g), Vector((0.17, s * 0.15, 0.95)), Vector((0.3, s * 0.64, 0.53)), 0.03)
        viga(B('quadro_diagonais', 'aco', g), Vector((0.17, s * 0.15, 2.4)), Vector((0.41, s * 0.62, 2.76)), 0.03)
        listras_borda((0.28, s * 0.672, 0.44), (0.54, s * 0.672, 0.44), Vector((0, s, 0)), 0.03, g)
    listras_borda((0.541, -0.65, 0.44), (0.541, 0.65, 0.44), X, 0.03, g)
    for y in (-0.6, -0.36, -0.12, 0.12, 0.36, 0.6):
        parafuso((0.3, y, 0.522), Z, g, 0.009)
        parafuso((0.51, y, 0.522), Z, g, 0.009)
    for _ in range(10):
        mancha(B('deck_po', 'po', g), (random.uniform(0.3, 0.52), random.uniform(-0.6, 0.6)), random.uniform(0.02, 0.05), 0.5215)
    # distribuidor hidráulico no deck e mangueira até a unidade na plataforma
    caixa_de(B('distribuidor', 'zarcao', g), (0.285, -0.6, 0.52), (0.325, 0.6, 0.56))
    UH = Vector((-0.12, -0.42, Z_GIRO))
    caixa_de(B('unidade_hidraulica', 'amarelo', g), UH + Vector((-0.1, -0.08, 0)), UH + Vector((0.14, 0.1, 0.15)))
    caixa_de(B('unidade_tampa', 'grafite', g), UH + Vector((-0.11, -0.09, 0.15)), UH + Vector((0.15, 0.11, 0.165)))
    remendo(UH + Vector((0.02, -0.08, 0.08)), -Y, 0.1, 0.08, g, 'chapa')
    for s in (-1, 1):
        mangueira(B('mangueiras', 'borracha', g), bezier(UH + Vector((0.14, 0.02 * s, 0.1)), UH + Vector((0.35, 0.05 * s, 0.1)),
                                                            Vector((0.31, -0.3 + 0.03 * s, 0.4)), Vector((0.31, -0.3 + 0.03 * s, 0.52)), 12), 0.01)
    mancha(B('oleo_plat', 'oleo', g), (UH.x + 0.2, UH.y + 0.05), 0.06, Z_GIRO + 0.0015)
    # palhetas (perfil de asa grossa), cada uma num grupo com pivô vertical
    PAL = []
    for k, y in enumerate(Y_PAL):
        gp = grupo('palheta%d' % k, (X_PAL, y, 0), g, ANG_PAL[k])
        n = 'palheta%d' % k
        perfil = []
        for j in range(13):
            t = j / 12
            xx = -0.065 + 0.26 * t
            th = 0.022 * (1 - t) ** 0.8 * math.sqrt(max(0.0, t * 4)) if t < 0.25 else 0.022 * (1 - (t - 0.25) / 0.75 * 0.85)
            th = 0.024 * math.sin(PI * min(1.0, t * 0.5 + 0.25) ** 1.0) * (1 - 0.8 * t) + 0.003
            perfil.append((xx, th))
        bm = B('palhetas', 'amarelo' if k != 3 else 'verde', n)
        top = [bm.verts.new((x_, y_, z_)) for z_ in (Z_PAL0, Z_PAL1) for (x_, y_) in [(p[0], p[1]) for p in perfil] + [(p[0], -p[1]) for p in reversed(perfil)]]
        nn = len(perfil) * 2
        A, Bq = top[:nn], top[nn:]
        for m in range(nn):
            bm.faces.new((A[m], A[(m + 1) % nn], Bq[(m + 1) % nn], Bq[m]))
        bm.faces.new(list(reversed(A)))
        bm.faces.new(Bq)
        # nervuras, rebites, bordo de ataque gasto, tampa de fim
        for z in (Z_PAL0 + 0.25, 1.2, 1.7, 2.2, Z_PAL1 - 0.25):
            for sgn in (-1, 1):
                caixa(B('palhetas_nervuras', 'aco', n), Vector((0.05, sgn * 0.022, z)), (0.2, 0.004, 0.018))
                for xx in (-0.03, 0.03, 0.09, 0.14):
                    cil(B('parafusos', 'aco', n), Vector((xx, sgn * 0.024, z)), 0.005, 0.006, Vector((0, sgn, 0)), lados=6)
        tubo(B('palhetas_bordo', 'aco', n), Vector((-0.062, 0, Z_PAL0)), Vector((-0.062, 0, Z_PAL1)), 0.012, 10)
        for z in (Z_PAL0, Z_PAL1):
            caixa_de(B('palhetas_tampas', 'aco', n), (-0.07, -0.026, z - 0.012), (0.2, 0.026, z + 0.0 if z == Z_PAL0 else z + 0.012))
        cil(B('palhetas_eixo', 'cromo', n), Vector((0, 0, (0.52 + 2.74) / 2)), 0.016, 2.74 - 0.52 + 0.04, lados=12)
        for z in (0.56, 2.7):                                                  # mancais
            cil(B('palhetas_mancal', 'ferro', g), Vector((X_PAL, y, z)), 0.034, 0.05, lados=16)
        # chifre do pistão no eixo (z 0.6) apontando para barlavento
        caixa(B('palhetas_chifre', 'ferro', n), Vector((-0.045, 0, 0.62)), (0.1, 0.03, 0.028))
        cil(B('palhetas_chifre_pino', 'aco', n), Vector((-0.09, 0, 0.62)), 0.01, 0.05, lados=10)
        for _ in range(6):                                                     # poeira e riscos na face
            sgn = random.choice((-1, 1))
            caixa(B('palhetas_po', 'po', n), Vector((random.uniform(-0.04, 0.17), sgn * 0.0245, random.uniform(Z_PAL0 + 0.1, Z_PAL1 - 0.1))),
                  (random.uniform(0.03, 0.08), 0.002, random.uniform(0.01, 0.03)))
        escorrido(Vector((0.1, -0.025, Z_PAL1 - 0.05)), -Y, n, L=0.25)
        PAL.append(gp)
    # pistões das palhetas (camisa no poste do deck, haste no chifre): objetos próprios, apontados por quadro
    PIS = []
    for k, y in enumerate(Y_PAL):
        A_ = Vector((0.355, y - 0.19, 0.62))
        caixa_de(B('pistoes_postes', 'aco', g), (A_.x - 0.018, A_.y - 0.018, 0.52), (A_.x + 0.018, A_.y + 0.018, 0.6))
        mangueira(B('mangueiras', 'borracha', g), bezier(Vector((0.305, A_.y - 0.035, 0.56)), Vector((0.305, A_.y - 0.035, 0.66)),
                                                            A_ + Vector((-0.03, 0.03, 0.07)), A_ + Vector((0.0, 0.03, 0.03)), 8), 0.006)
        cil(B('pistoes_postes', 'aco', g), A_, 0.012, 0.05, Vector((0, 0, 1)), lados=10)
        bm = bmesh.new()
        torno(bm, [(-0.02, 0), (-0.02, 0.022), (0.11, 0.022), (0.11, 0.012), (0.12, 0.012), (0.12, 0)], n=16)
        cil(bm, Vector((0.02, 0.025, 0.0)), 0.007, 0.02, Y, lados=8)
        cam_ = suavizar(obj('pistao%d_camisa' % k, bm, 'amarelo2' if k % 2 else 'zarcao', GR['giro']))
        cam_.rotation_mode = 'QUATERNION'
        bm = bmesh.new()
        torno(bm, [(0.0, 0), (0.0, 0.009), (0.12, 0.009), (0.12, 0)], n=12)
        cil(bm, Vector((0, 0, 0.0)), 0.014, 0.03, Y, lados=10)
        has = suavizar(obj('pistao%d_haste' % k, bm, 'cromo', GR['giro']))
        has.rotation_mode = 'QUATERNION'
        PIS.append((cam_, has, A_))
    # ---------------- topo: biruta, anemômetro, domo-sensor da IA, antena
    octo(B('topo_tampa', 'chapa', g), (0, 0), 0.21, Z_TOPO, Z_TOPO + 0.03)
    torno(B('sensor_caixa', 'grafite', g), [(Z_TOPO + 0.03, 0), (Z_TOPO + 0.03, 0.09), (Z_TOPO + 0.14, 0.09), (Z_TOPO + 0.14, 0)], n=24)
    esfera(B('sensor_domo', 'domo', g, True), Vector((0, 0, Z_TOPO + 0.14)), 0.075, 20)
    torno(B('sensor_aro', 'aco', g), [(Z_TOPO + 0.13, 0.072), (Z_TOPO + 0.13, 0.095), (Z_TOPO + 0.15, 0.095), (Z_TOPO + 0.15, 0.072)], n=24)
    tubo(B('antena', 'aco', g), Vector((0.12, -0.1, Z_TOPO + 0.03)), Vector((0.12, -0.1, Z_TOPO + 0.6)), 0.005, 6)
    esfera(B('antena_led', 'led_ambar', g), Vector((0.12, -0.1, Z_TOPO + 0.6)), 0.01, 8)
    # anemômetro (fixo no mundo? não: gira com o vento; fica num mastro no lado)
    AM = Vector((-0.12, 0.12, Z_TOPO + 0.03))
    tubo(B('anemo_mastro', 'aco', g), AM, AM + Vector((0, 0, 0.42)), 0.012, 10)
    anemo = grupo('anemometro', tuple(AM + Vector((0, 0, 0.42))), g)
    for k in range(3):
        a = k * 2 * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        tubo(B('anemo_bracos', 'aco', 'anemometro'), Vector((0, 0, 0)), d * 0.14, 0.005, 6)
        cc = d * 0.14
        t_ = Vector((-d.y, d.x, 0))
        torno(B('anemo_conchas', 'aluminio', 'anemometro'), [(0.0, 0.0), (0.0, 0.035), (0.035, 0.03), (0.04, 0.0)], cc, t_, n=16)
    cil(B('anemo_cubo', 'aco', 'anemometro'), Vector((0, 0, 0)), 0.022, 0.03, lados=12)
    # biruta num braço lateral, com anel giratório e saco listrado apontando a favor do vento
    BR = Vector((-0.05, -0.2, Z_TOPO + 0.03))
    tubo(B('biruta_mastro', 'aco', g), BR, BR + Vector((0, -0.1, 0.55)), 0.014, 10)
    PB_ = BR + Vector((0, -0.1, 0.55))
    biruta = grupo('biruta', tuple(PB_), g)
    gb = 'biruta'
    toro(B('biruta_aro', 'aco', gb), Vector((0.06, 0, 0)), 0.09, 0.008, X, nR=28, nr=6)
    tubo(B('biruta_haste', 'aco', gb), Vector((-0.03, 0, 0)), Vector((0.06, 0, 0)), 0.008, 8)
    cil(B('biruta_anel', 'ferro', gb), Vector((0, 0, 0)), 0.022, 0.05, lados=12)
    # saco: tronco de cone com ondulações (objeto próprio para tremular)
    bm = bmesh.new()
    NS, NA = 14, 20
    aneis = []
    for i in range(NS + 1):
        t = i / NS
        r = 0.088 * (1 - 0.55 * t)
        aneis.append([bm.verts.new((0.06 + 0.8 * t, r * math.cos(a), r * math.sin(a))) for a in (j * 2 * PI / NA for j in range(NA))])
    for i in range(NS):
        for j in range(NA):
            bm.faces.new((aneis[i][j], aneis[i][(j + 1) % NA], aneis[i + 1][(j + 1) % NA], aneis[i + 1][j]))
    saco = liso(obj('biruta_saco', bm, 'biruta', GR['biruta']))
    sk = saco.shape_key_add(name='base')
    # cabos do topo descendo pela coluna até a plataforma (feixe preso)
    pts = [Vector((0.185, 0.07, Z_TOPO - 0.05))] + [Vector((0.19, 0.07, z)) for z in (2.8, 2.2, 1.6, 1.0, 0.6)] + [Vector((0.25, 0.1, Z_GIRO + 0.02))]
    feixe(pts, Vector((0, 1, 0)), g, n=3, r=0.008, passo=1)
    caixa_de(B('juncao', 'grafite', g), (0.2, -0.05, 0.75), (0.28, 0.15, 0.95))
    # ---------------- grama, tufos deitados, folhas no chão
    bm = B('capim', 'capim')
    bm2 = B('capim_verde', 'capim_verde')
    for _ in range(900):
        a = random.uniform(0, 2 * PI)
        r = 1.15 + random.expovariate(1 / 3.0)
        if r > 14:
            continue
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        tufo(bm if random.random() < 0.6 else bm2, p, random.randint(5, 9), random.uniform(0.12, 0.3), W, 0.85)
    for _ in range(40):                                                    # folhas presas no lado de sotavento das pedras/laje
        a = random.uniform(-0.6, 0.6) + AW
        p = Vector((math.cos(a), math.sin(a), 0)) * random.uniform(1.05, 1.4)
        folha(B('folhas_chao', random.choice(('folha_seca', 'folha_verde'))), p + Vector((0, 0, 0.004)), random.uniform(0.04, 0.07), AW + random.uniform(-0.5, 0.5))
    for _ in range(14):
        p = Vector((random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9), ZL + 0.004))
        folha(B('folhas_laje', 'folha_seca'), p, random.uniform(0.04, 0.06), AW + random.uniform(-0.4, 0.4))
    CENA = {'FANS': FANS, 'PAL': PAL, 'PIS': PIS, 'anemo': anemo, 'saco': saco, 'biruta': biruta}


def mundo_giro(p):
    return Matrix.Rotation(AW, 4, 'Z') @ Vector(p)


def faixa_fluxo(nome, pts, w0, w1, lado):
    """Fita translúcida ao longo de pts (largura cresce de w0 a w1), com UV: u ao longo, v através."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    n = len(pts)
    vs = []
    for i, p in enumerate(pts):
        t = i / (n - 1)
        w = w0 + (w1 - w0) * t ** 0.8
        d = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        ld = (Vector(lado) - d * Vector(lado).dot(d)).normalized()
        vs.append((bm.verts.new(p - ld * w / 2), bm.verts.new(p + ld * w / 2)))
    for i in range(n - 1):
        f = bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
        for lp, (u, v) in zip(f.loops, ((i / (n - 1), 0), ((i + 1) / (n - 1), 0), ((i + 1) / (n - 1), 1), (i / (n - 1), 1))):
            lp[uv].uv = (u, v)
    return liso(obj(nome, bm, 'fluxo'))


def efeitos_defletor():
    ef = {}
    # linhas de fluxo: saem da borda de fuga das palhetas e abrem em leque (no plano e um pouco em altura)
    ef['fitas'] = []
    for k in range(11):
        ang = math.radians(-26 + 52 * k / 10) + random.uniform(-0.03, 0.03)
        z0 = random.uniform(0.85, 2.5)
        y0 = -0.5 + k / 10
        p0 = mundo_giro((X_PAL + 0.25, y0, z0))
        d = Vector((math.cos(AW + ang), math.sin(AW + ang), 0))
        Lf = random.uniform(7.0, 11.0)
        pts = []
        for i in range(40):
            t = i / 39
            p = p0 + d * (Lf * t) + Vector((0, 0, 0.5 * t + 0.3 * math.sin(t * PI * 1.5 + k) * t))
            lat = Vector((-d.y, d.x, 0))
            p += lat * 0.18 * math.sin(t * 2 * PI * 1.2 + k * 0.7) * t
            pts.append(p)
        ver = random.random() < 0.75
        f = faixa_fluxo('fluxo%d' % k, pts, 0.12, random.uniform(0.6, 1.2), Z if ver else Vector((-d.y, d.x, 0)))
        ef['fitas'].append(f)
    # entrada: algumas linhas finas convergindo para os dutos (barlavento)
    for i, zf in enumerate([]):                                       # (linhas de entrada removidas: pareciam tracejado solto)
        for k in range(3):
            a = math.radians(-35 + 35 * k)
            c = mundo_giro((X_FAN - 0.3, 0, zf))
            d = Vector((math.cos(AW + PI + a), math.sin(AW + PI + a), 0))
            pts = [c + d * (4.0 * (1 - i_ / 24)) + Vector((0, 0, 0.6 * (1 - i_ / 24) * (k - 1))) for i_ in range(25)]
            f = faixa_fluxo('fluxo_entrada', pts, 0.6, 0.12, Z)
            ef['fitas'].append(f)
    # folhas e capim voando ao longo do fluxo
    ef['folhas'] = []
    for k in range(70):
        bm = bmesh.new()
        if k % 4 == 3:
            tufo(bm, (0, 0, 0), 1, 0.1)                                     # pedaço de capim
            mat = 'capim'
        else:
            folha(bm, (0, 0, 0), random.uniform(0.07, 0.12), 0.0, Z, 0.35)
            mat = random.choice(('folha_seca', 'folha_seca', 'folha_verde'))
        o = obj('folha_voando', bm, mat)
        o.rotation_mode = 'XYZ'
        ang = random.uniform(-0.45, 0.45)
        ini = mundo_giro((random.uniform(0.6, 1.2), random.uniform(-0.6, 0.6), random.uniform(0.15, 2.6)))
        if k % 3 == 0:                                                      # algumas vêm do chão (barlavento) e entram no fluxo
            ini = Vector((random.uniform(-4, -1.5), random.uniform(-3, 3), 0.05)) * 1.0
            ini = Matrix.Rotation(AW, 3, 'Z') @ ini
        ef['folhas'].append((o, ini, ang, random.random(), random.uniform(2.5, 4.5), random.uniform(5, 14)))
    # poeira rasteira em faixas alongadas na direção do vento
    ef['poeira'] = []
    for k in range(9):
        o = bolha('poeira%d' % k, 'poeira_vento', 1.0, 3)
        ang = random.uniform(-0.3, 0.3)
        base = Vector((random.uniform(-3.5, 1.5), random.uniform(-3.5, 3.5), 0.0))
        base = Matrix.Rotation(AW, 3, 'Z') @ base
        o.rotation_euler = (0, 0, AW + ang * 0.5)
        ef['poeira'].append((o, base, random.random(), random.uniform(1.5, 3.0)))
    return ef


def animar_defletor(ef):
    FANS, PAL, PIS = CENA['FANS'], CENA['PAL'], CENA['PIS']
    domo = M['domo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    fases = [f.data.materials[0].node_tree.nodes['fase'].outputs[0] for f in ef['fitas'][:1]]
    saco = CENA['saco']
    base_co = [v.co.copy() for v in saco.data.vertices]
    sk_b = saco.data.shape_keys.key_blocks['base'] if saco.data.shape_keys else None
    chaves_saco = []
    for i in range(4):                                                     # quatro formas de tremular, em laço
        kb = saco.shape_key_add(name='tremor%d' % i, from_mix=False)
        for v, c0 in zip(kb.data, base_co):
            t = max(0.0, (c0.x - 0.06) / 0.8)
            ond = math.sin(t * 9 + i * PI / 2) * 0.03 * t
            v.co = c0 + Vector((0, ond, ond * 0.6 - 0.04 * t * t))
        chaves_saco.append(kb)
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        for i, f in enumerate(FANS):
            f.rotation_euler = (2 * PI * (24 + 3 * i) * fr / 7 * 7 / 7 * 1.0 * (1 if i else -1), 0, 0)
            chave(f, ('rotation_euler',), q)
        for k, (gp, (cam_, has, A_)) in enumerate(zip(PAL, PIS)):
            th = ANG_PAL[k] + math.radians(2.0) * math.sin(2 * PI * fr * 2 + k * 0.9)
            gp.rotation_euler = (0, 0, th)
            chave(gp, ('rotation_euler',), q)
            pino = Vector((X_PAL, Y_PAL[k], 0.62)) + Matrix.Rotation(th, 3, 'Z') @ Vector((-0.09, 0, 0))
            d = pino - A_
            cam_.location = A_
            cam_.rotation_quaternion = d.to_track_quat('Z', 'Y')
            has.location = pino
            has.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
            chave(cam_, ('location', 'rotation_quaternion'), q)
            chave(has, ('location', 'rotation_quaternion'), q)
        CENA['anemo'].rotation_euler = (0, 0, 2 * PI * 7 * fr)
        chave(CENA['anemo'], ('rotation_euler',), q)
        CENA['biruta'].rotation_euler = (0, math.radians(3) * math.sin(2 * PI * fr * 4), math.radians(2.5) * math.sin(2 * PI * fr * 3))
        chave(CENA['biruta'], ('rotation_euler',), q)
        for i, kb in enumerate(chaves_saco):
            ph = (fr * 8) % 4
            kb.value = max(0.0, 1 - min(abs(ph - i), 4 - abs(ph - i)))
            kb.keyframe_insert('value', frame=q)
        domo.default_value = 2.5 + 1.2 * math.sin(2 * PI * fr * 3)
        domo.keyframe_insert('default_value', frame=q)
        for fs in fases:
            fs.default_value = -fr * 7.0 * 3
            fs.keyframe_insert('default_value', frame=q)
        for o, ini, ang, ph, vel, giro in ef['folhas']:
            u = (ph + fr) % 1.0
            d = Vector((math.cos(AW + ang), math.sin(AW + ang), 0))
            dist = u * vel * 2.6
            p = ini + d * dist + Vector((0, 0, 0.25 * math.sin(u * 2 * PI * 2 + ph * 6) + (0.6 * u if ini.z < 0.1 else -0.2 * u)))
            p.z = max(0.03, p.z)
            o.location = p
            o.rotation_euler = (giro * u * 2 + ph * 6, giro * 0.6 * u + ph * 3, AW + ang + 0.5 * math.sin(u * 9))
            chave(o, ('location', 'rotation_euler'), q)
            mostra(o, 0.02 < u < 0.98, q)
        for o, base, ph, comp in ef['poeira']:
            u = (ph + fr) % 1.0
            o.location = base + W * (u * 3.0) + Vector((0, 0, 0.15 + 0.1 * u))
            o.scale = (comp * (0.7 + 0.6 * u), 0.35 + 0.3 * u, 0.18 + 0.12 * u)
            cor_vol(o, math.sin(PI * u) * 1.0)
            chave(o, ('location', 'scale', 'color'), q)
    interp_linear()


def estado_defletor():
    ceu_sol(48, -150)
    sol_d.energy = 4.2
    sol_d.angle = math.radians(2)
    bg.inputs['Strength'].default_value = 0.3
    sc.view_settings.exposure = -0.55
    # a fase das fitas fica num só material: todas compartilham
    return


# ====================================================================================================================
#                                          execução
# ====================================================================================================================
CENA = {}
if MAQ == 'semeador':
    semeador()
    marca('modelo')
    fechar()
    marca('fechar')
    EF = efeitos_semeador()
    marca('efeitos')
else:
    defletor()
    fechar()
    EF = efeitos_defletor()


def render(nome, quadro, pos, alvo, lente, rx=1200, ry=1100, amostras=128):
    sc.cycles.samples = amostras
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.frame_set(quadro)
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


if MODO == 'foto':
    quais = args[2:]
    if MAQ == 'semeador':
        if not quais or 'semeador_nuvens_0' in quais:
            estado_semeador('formando', EF)
            animar_semeador('formando', EF)
            t = TIROS[1]
            render('semeador_nuvens_0.png', t + 9, (-2.5, -4.4, 1.9), (0.15, -0.1, 1.65), 27)
        if not quais or 'semeador_nuvens_chuva' in quais:
            estado_semeador('chuva', EF)
            animar_semeador('chuva', EF)
            t = TIROS[1]
            render('semeador_nuvens_chuva.png', t + 5, (-5.6, -10.2, 1.3), (0.0, 0.0, 6.0), 16, 1200, 1100, 160)
    else:
        estado_defletor()
        animar_defletor(EF)
        if not quais or 'defletor_vento_0' in quais:
            pos = mundo_giro((3.5, -3.7, 2.6))
            render('defletor_vento_0.png', 30, tuple(pos), tuple(mundo_giro((0.1, 0.0, 1.95))), 26)
        if not quais or 'defletor_vento_fluxo' in quais:
            pos = mundo_giro((1.0, -7.2, 3.4))
            render('defletor_vento_fluxo.png', 30, tuple(pos), tuple(mundo_giro((3.4, 0.2, 1.1))), 19, 1300, 1000, 140)
if MODO == 'teste':
    est = args[2]
    v = [float(x) for x in args[3:]]
    if MAQ == 'semeador':
        estado_semeador(est, EF)
        animar_semeador(est, EF)
        marca('animar')
    else:
        estado_defletor()
        animar_defletor(EF)
    render('clima2x2_teste.png', int(v[7]), v[0:3], v[3:6], v[6], 1000, 800, 32)
print('CLIMA_2x2 ok', MAQ)
