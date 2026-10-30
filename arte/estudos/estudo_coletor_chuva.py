"""Estudo isolado (fora do jogo): coletor de chuva da IA, 2×2 tiles. Funciona em qualquer lugar: rende até 25 de
água/s com chuva forte e 0 no seco; tanque próprio de 2.000; solta a água pelo cano de saída (FLUIDO_SAI_S1).

Flor de chapa: dez pétalas-calha de aço em duas camadas (5 internas, 5 externas defasadas 36°), presas por dobradiça
num colar-funil sobre o tanque; cada pétala tem seu pistão hidráulico (camisa no braço soldado ao tanque, haste na
orelha da pétala), mangueira do anel distribuidor, que vem da unidade hidráulica. Com chuva as pétalas abrem num
cálice e escorrem a água para a garganta; no seco fecham num botão (proteção contra pó e sol).
Garganta: domo de grade com folhas e lodo presos; abaixo, cesto-filtro de folhas com calha de descarte até a caçamba.
Tanque cilíndrico com cintas, visor de nível de vidro com boia, bocal sul com válvula atuada, bomba centrífuga com
motor aletado e cano de saída com flange na borda sul. Ladrão (transbordo) a oeste jorra numa canaleta.
Toque da IA: mastro com sensor de nuvem (domo com núcleo violeta), antena, anemômetro e lança com anel emissor; seis
fios de campo descem do anel até o domo de grade e as gotas descem guiadas pelos fios, presas por anéis de campo.
Sujeira: ferrugem, limo, lodo, folhas, óleo, chapa trocada de outra cor, remendos aparafusados, fiação exposta.

Uso: blender -b --python estudo_coletor_chuva.py -- foto [chuva|seco|perto]
     blender -b --python estudo_coletor_chuva.py -- teste <chuva|seco> x y z ax ay az lente fr
     blender -b --python estudo_coletor_chuva.py -- checar        (interpenetração das pétalas/pistões)"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(31)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

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
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def tubo_oco(bm, centro, ro, ri, h, eixo=Z, lados=40):
    u, v, w = base_de(eixo)
    centro = Vector(centro)
    an = {}
    for k, (r, z) in enumerate(((ro, -h / 2), (ro, h / 2), (ri, -h / 2), (ri, h / 2))):
        an[k] = [bm.verts.new(centro + (u * math.cos(a) + v * math.sin(a)) * r + w * z)
                 for a in (i * 2 * PI / lados for i in range(lados))]
    fs = []
    for i in range(lados):
        j = (i + 1) % lados
        fs.append(bm.faces.new((an[0][i], an[0][j], an[1][j], an[1][i])))
        fs.append(bm.faces.new((an[2][i], an[3][i], an[3][j], an[2][j])))
        fs.append(bm.faces.new((an[1][i], an[1][j], an[3][j], an[3][i])))
        fs.append(bm.faces.new((an[0][i], an[2][i], an[2][j], an[0][j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def esfera(bm, c, r, seg=20):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def flange(bm, bp, c, eixo, r, esp=0.022, n=8):
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(bm, c, r, esp, eixo, lados=24)
    u, v, _ = base_de(eixo)
    for k in range(n):
        a = k * 2 * PI / n + 0.3
        cil(bp, c + (u * math.cos(a) + v * math.sin(a)) * (r - 0.011), 0.0055, esp + 0.014, eixo, lados=6)


def cano(bm, bf, bp, pts, r, lados=24, fl=True, fl_pontas=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)
    if fl:
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            d, L = (b - a).normalized(), (b - a).length
            if L < r * 4.5:
                continue
            if i > 0 or fl_pontas:
                flange(bf, bp, a + d * r * 1.9, d, r * 1.5, r * 0.42)
            if i < len(pts) - 2 or fl_pontas:
                flange(bf, bp, b - d * r * 1.9, d, r * 1.5, r * 0.42)


def trilha(bm, pts, r, lados=8):
    """Tubo fino contínuo por pontos (borda enrolada, fio, cabo): esfera em cada junta."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)


def bez(p0, p1, p2, p3, t):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    return p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3


def manometro(bm_ac, bm_face, bm_pont, p, cima, face):
    p, cima, face = Vector(p), Vector(cima).normalized(), Vector(face).normalized()
    tubo(bm_ac, p, p + cima * 0.07, 0.008, 8)
    c = p + cima * 0.1
    cil(bm_ac, c, 0.038, 0.024, face, lados=20)
    cil(bm_face, c + face * 0.0125, 0.032, 0.002, face, lados=20)
    u, v, _ = base_de(face)
    ang = random.uniform(0.3, 2.4)
    d = u * math.cos(ang) + v * math.sin(ang)
    viga(bm_pont, c + face * 0.0145 - d * 0.005, c + face * 0.0145 + d * 0.026, 0.003)


def folha(bm, c, tam, giro, normal=Z, dobra=0.25):
    """Folha caída: lâmina pontuda com nervura central dobrada (leque de triângulos)."""
    c, normal = Vector(c), Vector(normal).normalized()
    u, v, w = base_de(normal)
    a = giro
    du, dv = u * math.cos(a) + v * math.sin(a), -u * math.sin(a) + v * math.cos(a)
    n = 7
    cen = [c + du * (tam * (i / n - 0.5)) + w * (0.002) for i in range(n + 1)]
    vc = [bm.verts.new(p) for p in cen]
    lados = []
    for s in (-1, 1):
        ls = []
        for i in range(n + 1):
            t = i / n
            lw = tam * 0.28 * math.sin(PI * t) ** 0.9
            ls.append(bm.verts.new(cen[i] + dv * (s * lw) + w * (lw * dobra + random.uniform(-0.002, 0.004))))
        lados.append(ls)
    for i in range(n):
        bm.faces.new((vc[i], vc[i + 1], lados[1][i + 1], lados[1][i]))
        bm.faces.new((vc[i], lados[0][i], lados[0][i + 1], vc[i + 1]))
    tubo(bm, cen[0] - du * tam * 0.12, cen[0] + du * 0.003, 0.0015, 4)   # cabinho


def borrao(bm, c, r, normal, alt=0.3):
    """Placa irregular abaulada encostada numa superfície (lodo, limo grosso)."""
    c, normal = Vector(c), Vector(normal).normalized()
    u, v, w = base_de(normal)
    n = 12
    cen = bm.verts.new(c + w * r * alt)
    fase = random.uniform(0, 6)
    borda = []
    for i in range(n):
        a = i * 2 * PI / n
        f = r * (1 + 0.3 * math.sin(a * 3 + fase) + 0.15 * random.random())
        borda.append(bm.verts.new(c + (u * math.cos(a) + v * math.sin(a)) * f - w * 0.002))
    for i in range(n):
        bm.faces.new((cen, borda[i], borda[(i + 1) % n]))


def quat_zx(zd, xd):
    """Rotação cujo z local aponta para zd e x local fica o mais perto possível de xd."""
    zd = Vector(zd).normalized()
    xd = (Vector(xd) - zd * Vector(xd).dot(zd)).normalized()
    yd = zd.cross(xd)
    return Matrix((xd, yd, zd)).transposed().to_quaternion()


def molhavel(m):
    """Insere um multiplicador de rugosidade (nó 'molhado') para a cena de chuva deixar tudo brilhante e úmido."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = b.inputs['Roughness']
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.name = 'molhado'
    mul.inputs[1].default_value = 1.0
    if ent.is_linked:
        lk = ent.links[0]
        nt.links.new(lk.from_socket, mul.inputs[0])
    else:
        mul.inputs[0].default_value = ent.default_value
    nt.links.new(mul.outputs[0], ent)
    return m


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat(nome='Vidro', sujo=1.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Coat Weight'].default_value = 0.8
    b.inputs['Coat Roughness'].default_value = 0.03
    b.inputs['Coat IOR'].default_value = 1.5
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 18.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.6, 'From Max': 0.15, 'To Min': 0.0, 'To Max': sujo})
    nt.links.new(sep.outputs['Z'], alt.inputs['Value'])
    enc = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(alt.outputs['Result'], enc.inputs[0])
    nt.links.new(ru.outputs['Fac'], enc.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.97, 0.98, 0.98, 1)
    cor.inputs[7].default_value = (0.25, 0.3, 0.12, 1)
    nt.links.new(enc.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.03, 'To Max': 0.5})
    nt.links.new(enc.outputs['Value'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    return m


def agua_mat(nome, cor, tr, rough=0.03, ior=1.33):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Transmission Weight'].default_value = tr
    b.inputs['Roughness'].default_value = rough
    b.inputs['IOR'].default_value = ior
    return m


def filme_mat(fino=True):
    """Película d'água escorrendo: transparente com estrias claras ao longo do escoamento (eixo z do objeto)."""
    m = bpy.data.materials.new('Filme d\'água')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.9, 0.94, 0.96, 1)
    ag.inputs['Transmission Weight'].default_value = 0.0 if fino else 1.0   # película: sem transmissão (não faz sombra)
    ag.inputs['Roughness'].default_value = 0.02
    ag.inputs['IOR'].default_value = 1.33
    ag.inputs['Coat Weight'].default_value = 1.0 if fino else 0.0
    ag.inputs['Coat IOR'].default_value = 1.33
    br = no(nt, 'ShaderNodeBsdfPrincipled')
    br.inputs['Base Color'].default_value = (0.7, 0.74, 0.76, 1)
    br.inputs['Roughness'].default_value = 0.35
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    tc = no(nt, 'ShaderNodeTexCoord')
    esc = no(nt, 'ShaderNodeMapping')
    esc.inputs['Scale'].default_value = (30.0, 30.0, 4.0)
    nt.links.new(tc.outputs['Object'], esc.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.0, 'Detail': 5.0})
    nt.links.new(esc.outputs['Vector'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 0.6})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f.outputs['Result'], m1.inputs[0])
    nt.links.new(ag.outputs[0], m1.inputs[1])
    nt.links.new(br.outputs[0], m1.inputs[2])
    m2 = no(nt, 'ShaderNodeMixShader')                                 # meio transparente: a chapa aparece por baixo
    m2.inputs[0].default_value = 0.2 if fino else 0.75                 # fração de água (o resto é transparente)
    nt.links.new(tr.outputs[0], m2.inputs[1])
    nt.links.new(m1.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs['Surface'])
    return m


def chuva_mat():
    """Riscos de chuva: cinza-claro translúcido; somem dentro do cálice (para não atravessar as pétalas)."""
    m = bpy.data.materials.new('Chuva')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.8, 0.84, 0.88, 1)
    ag.inputs['Roughness'].default_value = 0.15
    ag.inputs['Transmission Weight'].default_value = 0.6
    ag.inputs['IOR'].default_value = 1.33
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    cxy = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], cxy.inputs['X'])
    nt.links.new(sep.outputs['Y'], cxy.inputs['Y'])
    rr = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(cxy.outputs[0], rr.inputs[0])
    dentro = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
    dentro.inputs[1].default_value = 1.08
    nt.links.new(rr.outputs['Value'], dentro.inputs[0])
    zc = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    zc.inputs[1].default_value = 0.55
    zc.inputs[2].default_value = 1.24
    nt.links.new(rr.outputs['Value'], zc.inputs[0])
    abaixo = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
    nt.links.new(sep.outputs['Z'], abaixo.inputs[0])
    nt.links.new(zc.outputs['Value'], abaixo.inputs[1])
    corta = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(dentro.outputs['Value'], corta.inputs[0])
    nt.links.new(abaixo.outputs['Value'], corta.inputs[1])
    fade = no(nt, 'ShaderNodeMath', operation='MAXIMUM')               # e um pouco transparentes sempre
    fade.inputs[1].default_value = 0.5
    nt.links.new(corta.outputs['Value'], fade.inputs[0])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(fade.outputs['Value'], mix.inputs[0])
    nt.links.new(ag.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.2
    b.inputs['Transmission Weight'].default_value = 0.4
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 2.0
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 70.0})
    tc = no(nt, 'ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def terra_mat(nome, molhada):
    """Chão: terra com tufos de capim seco; molhada fica escura e com brilho."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.5, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])
    seca = no(nt, 'ShaderNodeMix', data_type='RGBA')
    if molhada:
        seca.inputs[6].default_value = (0.075, 0.058, 0.04, 1)
        seca.inputs[7].default_value = (0.045, 0.055, 0.025, 1)
    else:
        seca.inputs[6].default_value = (0.24, 0.19, 0.13, 1)
        seca.inputs[7].default_value = (0.14, 0.14, 0.07, 1)
    capim = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], capim.inputs['Value'])
    nt.links.new(capim.outputs['Result'], seca.inputs[0])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.35
    nt.links.new(seca.outputs[2], var.inputs[6])
    nt.links.new(fino.outputs['Color'], var.inputs[7])
    nt.links.new(var.outputs[2], b.inputs['Base Color'])
    if molhada:
        ro = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.6, 'To Min': 0.12, 'To Max': 0.55})
        nt.links.new(ru.outputs['Fac'], ro.inputs['Value'])
        nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    else:
        b.inputs['Roughness'].default_value = 0.95
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.4 if not molhada else 0.25})
    nt.links.new(fino.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def limo_mat():
    """Limo verde escorrido: manchas irregulares, mais denso embaixo (coordenada z do objeto)."""
    m = mats.material('Limo', (0.05, 0.085, 0.025), 0, 0.5, pintura=False, sujeira=0.5, desgaste=0.0)
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.45, 0.05)

base3d.M.update({
    'amarelo': molhavel(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.85, ferrugem=0.45)),
    'zarcao': molhavel(mats.material('Zarcão', (0.32, 0.07, 0.035), 0, 0.6, desgaste=0.7, sujeira=0.8, ferrugem=0.4)),
    'grafite': molhavel(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.75, ferrugem=0.3)),
    'chapa': molhavel(mats.material('Chapa', (0.36, 0.37, 0.37), 1.0, 0.45, pintura=False, ferrugem=1.0, sujeira=0.9, escovado=True)),
    'aco': molhavel(mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True)),
    'cano': molhavel(mats.material('Cano', (0.30, 0.31, 0.32), 1.0, 0.5, pintura=False, ferrugem=0.9, sujeira=0.9)),
    'ferro': molhavel(mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9)),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'bronze': mats.material('Bronze', (0.62, 0.40, 0.18), 1.0, 0.3, pintura=False, sujeira=0.5, ferrugem=0.2),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'concreto': molhavel(mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0)),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'ponteiro': mats.material('Ponteiro', (0.5, 0.05, 0.02), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'boia': mats.material('Boia', (0.6, 0.08, 0.02), 0, 0.4, pintura=False, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lodo': mats.material('Lodo', (0.06, 0.045, 0.022), 0, 0.15, pintura=False, sujeira=0.3, desgaste=0.0),
    'lodo_seco': mats.material('Lodo seco', (0.15, 0.115, 0.075), 0, 0.9, pintura=False, sujeira=0.3, desgaste=0.0),
    'limo': limo_mat(),
    'ferrugem': mats.material('Ferrugem escorrida', (0.26, 0.09, 0.03), 0, 0.8, pintura=False, sujeira=0.4, desgaste=0.0),
    'folha_seca': mats.material('Folha seca', (0.25, 0.14, 0.05), 0, 0.7, pintura=False, sujeira=0.3, desgaste=0.0),
    'folha_verde': mats.material('Folha', (0.1, 0.12, 0.03), 0, 0.55, pintura=False, sujeira=0.3, desgaste=0.0),
    'folha_podre': mats.material('Folha podre', (0.06, 0.04, 0.02), 0, 0.4, pintura=False, sujeira=0.3, desgaste=0.0),
    'galho': mats.material('Galho', (0.11, 0.08, 0.05), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'pedra': mats.material('Pedra', (0.15, 0.145, 0.13), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'palha': mats.material('Palha', (0.28, 0.22, 0.11), 0, 0.8, pintura=False, sujeira=0.5, desgaste=0.0),
    'cristal': cristal_mat(),
    'visor': vidro_mat('Visor', 0.6),
    'domo': vidro_mat('Domo do sensor', 0.3),
    'agua_visor': agua_mat('Água do visor', (0.42, 0.5, 0.4), 0.75, ior=1.05),
    'gota': agua_mat('Gota', (0.85, 0.9, 0.95), 1.0),
    'poca': agua_mat('Poça', (0.06, 0.06, 0.055), 0.0, 0.03),
    'jato': filme_mat(False),
    'filme': filme_mat(),
    'chuva': chuva_mat(),
    'terra_seca': terra_mat('Terra seca', False),
    'terra_molhada': terra_mat('Terra molhada', True),
    'emissor': emissivo('Emissor', VIOLETA, 3.0, (0.15, 0.03, 0.4)),
    'campo_anel': emissivo('Anel de campo', VIOLETA, 6.0, (0.3, 0.1, 0.6)),
    'fio': emissivo('Fio de campo', VIOLETA, 1.0, (0.5, 0.48, 0.5)),
    'led_verde': emissivo('LED verde', (0.2, 1.0, 0.25), 5.0),
    'led_ambar': emissivo('LED âmbar', AMBAR, 6.0),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
})
M = base3d.M
_pb = M['poca'].node_tree.nodes['Principled BSDF']                      # poça: espelho escuro com verniz
_pb.inputs['Coat Weight'].default_value = 1.0
_pb.inputs['Coat IOR'].default_value = 1.5
_pb.inputs['Coat Roughness'].default_value = 0.02
CHUVA, SECO = [], []          # objetos que só aparecem num estado


def so_chuva(o):
    CHUVA.append(o)
    return o


def so_seco(o):
    SECO.append(o)
    return o


# ------------------------------------------------------------------ medidas
R_T = 0.44                    # tanque
Z_T0, Z_T1, H_DOMO = 0.14, 0.98, 0.08
R_ESF = (R_T ** 2 + H_DOMO ** 2) / (2 * H_DOMO)


def z_domo(r):
    return Z_T1 + math.sqrt(max(0.0, R_ESF ** 2 - r * r)) - (R_ESF - H_DOMO)


R_GAR = 0.29                  # garganta / cesto
Z_CESTO0, Z_CESTO1 = 1.075, 1.185
Z_COLAR0, Z_COLAR1 = 1.185, 1.225
R_COLAR = 0.49


def z_colar(r):
    return Z_COLAR0 + (Z_COLAR1 - Z_COLAR0) * (r - R_GAR) / (R_COLAR - R_GAR)

CAMADAS = {                   # pétalas: raio/altura da dobradiça, ângulo aberto/fechado, âncora do pistão (r, z)
    'A': dict(rh=0.36, zh=1.26, aberto=math.radians(62), fechado=math.radians(1), anc=(0.56, 0.96), fase=0.0),
    'B': dict(rh=0.445, zh=1.345, aberto=math.radians(56), fechado=math.radians(2), anc=(0.64, 1.0), fase=PI / 5),
}
L_P, SAG, CURL, ESP = 0.72, 0.028, 0.25, 0.008
T_ORELHA = 0.2 / L_P
APEX = Vector((0, 0, 1.40))   # topo do domo de grade (onde os fios de campo chegam)
R_ANEL_C, Z_ANEL_C = 0.11, 2.58
MASTRO = Vector((0.82, 0.82, 0.0))
Z_MANI, R_MANI = 0.86, 0.5    # anel distribuidor hidráulico
PHI_VISOR = math.radians(200)
PHI_CALHA = math.radians(234)
P_BOMBA = Vector((0.32, -0.62, 0.27))
Z_SAIDA = 0.56
X_SAIDA = 0.5


def hw(t):
    """Meia-largura da pétala (folha pontuda)."""
    a = min(max((t - 0.07) / 0.12, 0.0), 1.0)
    return 0.085 * (1 - t) + 0.14 * max(0.0, math.sin(PI * t)) ** 0.8 * a * a * (3 - 2 * a)


HMAX = max(hw(i / 100) for i in range(101))


def S0(t, s):
    u = t * L_P
    h = hw(t)
    return Vector((s * h, -(SAG * s * s * h / HMAX) - CURL * u * u, u))


def nP(t, s):
    """Normal do lado de dentro/de cima da pétala (−y local)."""
    e = 1e-3
    a = S0(min(1, t + e), s) - S0(max(0, t - e), s)
    b = S0(t, min(1, s + e)) - S0(t, max(-1, s - e))
    n = b.cross(a)
    if n.length < 1e-9:
        return Vector((0, -1, 0))
    n.normalize()
    return n if n.y < 0 else -n


def S(t, s, off=0.0):
    return S0(t, s) + nP(t, s) * off


def mat_base(cam, phi):
    return Matrix.Translation((cam['rh'] * math.cos(phi), cam['rh'] * math.sin(phi), cam['zh'])) @ \
        Matrix.Rotation(phi - PI / 2, 4, 'Z')


def mat_petala(cam, phi, th):
    return mat_base(cam, phi) @ Matrix.Rotation(-th, 4, 'X')


# ------------------------------------------------------------------ chão e laje
def altura(x, y):
    if abs(x) < 1.02 and abs(y) < 1.02:
        return 0.0
    return 0.03 * math.sin(x * 1.7) * math.cos(y * 2.1) + 0.02 * math.sin(x * 4.3 + y * 3.1) - 0.01


bm = bmesh.new()
xs = [-80, -50, -30, -20, -14, -10, -8, -6, -5] + [i * 0.2 - 4.4 for i in range(45)] + [5, 6, 8, 10, 14, 20, 30, 50, 80]
vs = [[bm.verts.new((x, y, altura(x, y))) for x in xs] for y in xs]
for j in range(len(xs) - 1):
    for i in range(len(xs) - 1):
        bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
chao = suavizar(obj('chao', bm, 'terra_seca'))
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, -0.05), (0.98, 0.98, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()
caixa_de(bm, (-0.985, -0.985, 0.0), (0.985, -0.95, 0.083))
caixa_de(bm, (-0.985, 0.95, 0.0), (0.985, 0.985, 0.083))
obj('laje_listras', bm, 'listras')
bm, bm2 = bmesh.new(), bmesh.new()                                        # pedras soltas e capim seco em volta
for k in range(45):
    x, y = random.uniform(-3.5, 3.5), random.uniform(-3.5, 3.5)
    if abs(x) < 1.1 and abs(y) < 1.1:
        continue
    pedra(bm, (x, y, altura(x, y)), random.uniform(0.02, 0.07), 0.5)
for k in range(30):
    x0, y0 = random.uniform(-3, 3), random.uniform(-3, 3)
    if abs(x0) < 1.15 and abs(y0) < 1.15:
        continue
    base = Vector((x0, y0, altura(x0, y0) - 0.01))
    for j in range(6):
        top = base + Vector((random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(0.12, 0.35)))
        cil(bm2, (base + top) / 2, 0.003, (top - base).length, top - base, lados=4, r2=0.001)
o = obj('pedras', bm, 'pedra')
o.modifiers.new('sub', 'SUBSURF').levels = 1
liso(o)
obj('capim', bm2, 'palha')

# ------------------------------------------------------------------ tanque: casco, cintas, domo, rebites, saia
bm = bmesh.new()
cil(bm, Vector((0, 0, (Z_T0 + Z_T1) / 2)), R_T, Z_T1 - Z_T0, lados=64)
suavizar(obj('tanque', bm, 'amarelo'))
bm = bmesh.new()                                                           # domo (calota)
res = bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=40, radius=R_ESF)
for v in list(bm.verts):
    if v.co.z < R_ESF - H_DOMO - 0.002:
        pass
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < R_ESF - H_DOMO - 0.03], context='VERTS')
for v in bm.verts:
    v.co.z = max(v.co.z, R_ESF - H_DOMO)
    v.co.z += Z_T1 - (R_ESF - H_DOMO)
liso(obj('domo_tanque', bm, 'amarelo'))
bm, bp = bmesh.new(), bmesh.new()
for z in (Z_T0 + 0.04, 0.42, 0.7, Z_T1 - 0.01):                            # cintas e anel de rebites
    toro(bm, Vector((0, 0, z)), R_T + 0.004, 0.012, nR=64, nr=8)
    for k in range(36):
        a = k * 2 * PI / 36
        esfera(bp, Vector((math.cos(a) * (R_T + 0.014), math.sin(a) * (R_T + 0.014), z + 0.022)), 0.006, 6)
for k in range(4):                                                         # costuras verticais soldadas
    a = k * PI / 2 + 0.4
    viga(bm, Vector((math.cos(a) * (R_T + 0.002), math.sin(a) * (R_T + 0.002), Z_T0 + 0.05)),
         Vector((math.cos(a) * (R_T + 0.002), math.sin(a) * (R_T + 0.002), Z_T1 - 0.02)), 0.012)
cil(bm, Vector((0, 0, 0.11)), R_T + 0.03, 0.06, lados=64)                  # saia/sapata
for k in range(12):                                                        # chumbadores da saia
    a = k * 2 * PI / 12
    cil(bp, Vector((math.cos(a) * (R_T + 0.05), math.sin(a) * (R_T + 0.05), 0.1)), 0.012, 0.05, lados=6)
    caixa(bm, Vector((math.cos(a) * (R_T + 0.045), math.sin(a) * (R_T + 0.045), 0.1)), (0.04, 0.04, 0.04),
          Matrix.Rotation(a, 3, 'Z'))
suavizar(obj('tanque_cintas', bm, 'grafite'))
obj('tanque_rebites', bp, 'ferro')
bm = bmesh.new()                                                           # remendos aparafusados no casco
bp = bmesh.new()
for a, z, w, h in ((math.radians(250), 0.55, 0.16, 0.12), (math.radians(160), 0.28, 0.12, 0.09), (math.radians(300), 0.85, 0.1, 0.08)):
    rot = Matrix.Rotation(a, 3, 'Z')
    c = Vector((math.cos(a) * (R_T + 0.006), math.sin(a) * (R_T + 0.006), z))
    caixa(bm, c, (0.008, w, h), rot)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cil(bp, c + rot @ Vector((0.006, sx * (w / 2 - 0.015), sz * (h / 2 - 0.015))), 0.006, 0.008, rot @ X, lados=6)
obj('remendos', bm, 'zarcao')
obj('remendos_parafusos', bp, 'ferro')
bm = bmesh.new()                                                           # ferrugem escorrida das cintas e rebites
for k in range(26):
    a = random.uniform(0, 2 * PI)
    z0 = random.choice((0.42, 0.7, Z_T1 - 0.01)) - 0.015
    L = random.uniform(0.05, 0.22)
    rot = Matrix.Rotation(a, 3, 'Z')
    w = random.uniform(0.006, 0.018)
    caixa(bm, Vector((math.cos(a) * (R_T + 0.0015), math.sin(a) * (R_T + 0.0015), z0 - L / 2)), (0.002, w, L), rot)
obj('ferrugem_tanque', bm, 'ferrugem')
bm = bmesh.new()                                                           # limo na base do tanque (faixa irregular)
for k in range(150):                                                       # fiapos verticais de alturas variadas
    a = random.uniform(0, 2 * PI)
    h = random.uniform(0.02, 0.1) * (2.2 if math.cos(a - PI) > 0.4 else 1.0) * random.choice((0.5, 1, 1, 1.6))
    w = random.uniform(0.006, 0.02)
    rot = Matrix.Rotation(a, 3, 'Z')
    z0 = Z_T0 + 0.07
    c = Vector((math.cos(a) * (R_T + 0.0018), math.sin(a) * (R_T + 0.0018), 0))
    t = rot @ Y
    vv = [bm.verts.new(p) for p in (c - t * w / 2 + Z * z0, c + t * w / 2 + Z * z0, c + t * w * 0.15 + Z * (z0 + h), c - t * w * 0.15 + Z * (z0 + h))]
    bm.faces.new(vv)
obj('limo_tanque', bm, 'limo')

# ------------------------------------------------------------------ pescoço, cesto-filtro de folhas, colar-funil
bm = bmesh.new()
cil(bm, Vector((0, 0, (z_domo(R_GAR) - 0.02 + Z_CESTO0) / 2)), R_GAR + 0.01, Z_CESTO0 - z_domo(R_GAR) + 0.02, lados=48)
cil(bm, Vector((0, 0, Z_CESTO0)), R_GAR + 0.03, 0.018, lados=48)           # flange do pescoço
suavizar(obj('pescoco', bm, 'grafite'))
bm, bm2 = bmesh.new(), bmesh.new()
n = 40
for k in range(n):                                                         # barras do cesto
    a = k * 2 * PI / n
    if abs(((a - PHI_CALHA + PI) % (2 * PI)) - PI) < 0.27:
        continue                                                           # boca da calha de descarte
    p = Vector((math.cos(a) * R_GAR, math.sin(a) * R_GAR, 0))
    tubo(bm, p + Vector((0, 0, Z_CESTO0)), p + Vector((0, 0, Z_CESTO1)), 0.006, 6)
toro(bm2, Vector((0, 0, (Z_CESTO0 + Z_CESTO1) / 2)), R_GAR, 0.007, nR=48, nr=6)
cil(bm2, Vector((0, 0, Z_CESTO1 - 0.006)), R_GAR + 0.02, 0.014, lados=48)
for k in range(6):                                                         # montantes do cesto
    a = k * PI / 3 + 0.25
    caixa(bm2, Vector((math.cos(a) * (R_GAR + 0.012), math.sin(a) * (R_GAR + 0.012), (Z_CESTO0 + Z_CESTO1) / 2)),
          (0.02, 0.02, Z_CESTO1 - Z_CESTO0), Matrix.Rotation(a, 3, 'Z'))
obj('cesto_grade', bm, 'aco')
obj('cesto_aro', bm2, 'grafite')
bm = bmesh.new()                                                           # tela fina do cesto (por dentro)
tubo_oco(bm, Vector((0, 0, (Z_CESTO0 + Z_CESTO1) / 2)), R_GAR - 0.008, R_GAR - 0.012, Z_CESTO1 - Z_CESTO0 - 0.01, lados=48)
tela = obj('cesto_tela', bm, 'ferro')
bm = bmesh.new()                                                           # colar-funil: chapa anular inclinada
nA = 72
an_in = [bm.verts.new((math.cos(a) * (R_GAR - 0.01), math.sin(a) * (R_GAR - 0.01), Z_COLAR0)) for a in (i * 2 * PI / nA for i in range(nA))]
an_out = [bm.verts.new((math.cos(a) * R_COLAR, math.sin(a) * R_COLAR, Z_COLAR1)) for a in (i * 2 * PI / nA for i in range(nA))]
an_outb = [bm.verts.new((math.cos(a) * R_COLAR, math.sin(a) * R_COLAR, Z_COLAR1 - 0.03)) for a in (i * 2 * PI / nA for i in range(nA))]
an_inb = [bm.verts.new((math.cos(a) * (R_GAR - 0.01), math.sin(a) * (R_GAR - 0.01), Z_COLAR0 - 0.03)) for a in (i * 2 * PI / nA for i in range(nA))]
for i in range(nA):
    j = (i + 1) % nA
    bm.faces.new((an_in[i], an_in[j], an_out[j], an_out[i]))
    bm.faces.new((an_out[i], an_out[j], an_outb[j], an_outb[i]))
    bm.faces.new((an_outb[i], an_outb[j], an_inb[j], an_inb[i]))
    bm.faces.new((an_inb[i], an_inb[j], an_in[j], an_in[i]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
toro(bm, Vector((0, 0, Z_COLAR1 + 0.004)), R_COLAR, 0.012, nR=72, nr=8)   # borda enrolada
suavizar(obj('colar', bm, 'amarelo'))
bm = bmesh.new()                                                           # 6 escoras do colar até o domo
for a in (math.radians(g) for g in (18, 90, 162, 198, 306)):
    pt = Vector((math.cos(a) * (R_COLAR - 0.04), math.sin(a) * (R_COLAR - 0.04), Z_COLAR1 - 0.03))
    pb = Vector((math.cos(a) * (R_T - 0.06), math.sin(a) * (R_T - 0.06), z_domo(R_T - 0.06)))
    viga(bm, pb, pt, 0.022)
    caixa(bm, pb + Vector((0, 0, 0.005)), (0.05, 0.05, 0.012), Matrix.Rotation(a, 3, 'Z'))
obj('colar_escoras', bm, 'grafite')
bm = bmesh.new()                                                           # domo de grade sobre a garganta
NG = 16
for k in range(NG):
    a = k * 2 * PI / NG
    pts = [Vector((math.cos(a) * R_GAR * (1 - f) * 0.97, math.sin(a) * R_GAR * (1 - f) * 0.97,
                   Z_COLAR0 + 0.01 + (APEX.z - Z_COLAR0 - 0.03) * math.sin(f * PI / 2))) for f in (i / 8 for i in range(9))]
    trilha(bm, pts, 0.0065, 6)
for f in (0.3, 0.6):
    rr = R_GAR * (1 - f) * 0.97
    toro(bm, Vector((0, 0, Z_COLAR0 + 0.01 + (APEX.z - Z_COLAR0 - 0.03) * math.sin(f * PI / 2))), rr, 0.006, nR=40, nr=6)
toro(bm, Vector((0, 0, Z_COLAR0 + 0.012)), R_GAR * 0.97, 0.009, nR=48, nr=6)
cil(bm, APEX - Vector((0, 0, 0.02)), 0.035, 0.035, lados=16)              # cubo do ápice (pega os fios)
obj('domo_grade', bm, 'aco')
bm, bm2, bm3, bm4 = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()      # folhas, galhos e lodo presos no domo
for k in range(26):
    f = random.uniform(0.05, 0.85)
    a = random.uniform(0, 2 * PI)
    rr = R_GAR * (1 - f) * 0.97
    z = Z_COLAR0 + 0.01 + (APEX.z - Z_COLAR0 - 0.03) * math.sin(f * PI / 2)
    nrm = Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, 1.0))
    folha([bm, bm2, bm3][k % 3], Vector((math.cos(a) * rr, math.sin(a) * rr, z)) + nrm.normalized() * 0.01,
          random.uniform(0.05, 0.09), random.uniform(0, PI), nrm)
for k in range(4):
    a = random.uniform(0, 2 * PI)
    c = Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, 1.31))
    d = Vector((math.cos(a + 1.4), math.sin(a + 1.4), 0.2)) * random.uniform(0.08, 0.14)
    tubo(bm4, c - d, c + d, 0.006, 5)
obj('folhas_domo_s', bm, 'folha_seca')
obj('folhas_domo_v', bm2, 'folha_verde')
obj('folhas_domo_p', bm3, 'folha_podre')
obj('galhos_domo', bm4, 'galho')
bm = bmesh.new()
for k in range(22):                                                        # lodo no pé do domo (borda da garganta)
    a = random.uniform(0, 2 * PI)
    pedra(bm, (math.cos(a) * R_GAR * 0.93, math.sin(a) * R_GAR * 0.93, Z_COLAR0 + 0.015), random.uniform(0.018, 0.035), 0.35)
liso(obj('lodo_garganta', bm, 'lodo'))
bm = bmesh.new()                                                           # lodo e limo escorrendo no colar
for k in range(24):
    a = random.uniform(0, 2 * PI)
    rr = random.uniform(R_GAR + 0.02, R_COLAR - 0.04)
    z = Z_COLAR0 + (Z_COLAR1 - Z_COLAR0) * (rr - R_GAR) / (R_COLAR - R_GAR) + 0.003
    rot = Matrix.Rotation(a, 3, 'Z')
    caixa(bm, Vector((math.cos(a) * rr, math.sin(a) * rr, z)), (random.uniform(0.04, 0.1), random.uniform(0.015, 0.04), 0.003), rot)
obj('limo_colar', bm, 'limo')

# ------------------------------------------------------------------ calha de descarte de folhas e caçamba
CB = Vector((math.cos(PHI_CALHA) * 0.84, math.sin(PHI_CALHA) * 0.84, 0))
dC = Vector((math.cos(PHI_CALHA), math.sin(PHI_CALHA), 0))
tC = Vector((-dC.y, dC.x, 0))
calha_pts = [dC * 0.25 + Z * 1.092, dC * 0.52 + Z * 1.05, dC * 0.84 + Z * 0.58]
bm = bmesh.new()
for a, b in zip(calha_pts, calha_pts[1:]):                                  # perfil em U: fundo + abas
    d = (b - a)
    nrm = d.cross(tC).normalized()
    if nrm.z < 0:
        nrm = -nrm
    for sx in (-1, 1):
        q0, q1 = a + tC * sx * 0.065, b + tC * sx * 0.065
        f = [bm.verts.new(p) for p in (q0, q1, q1 + nrm * 0.05, q0 + nrm * 0.05)]
        bm.faces.new(f)
    f = [bm.verts.new(p) for p in (a - tC * 0.065, b - tC * 0.065, b + tC * 0.065, a + tC * 0.065)]
    bm.faces.new(f)
calha = obj('calha_folhas', bm, 'cano')
calha.modifiers.new('esp', 'SOLIDIFY').thickness = 0.006
bm = bmesh.new()
for a, b in zip(calha_pts, calha_pts[1:]):
    for sx in (-1, 1):
        d = (b - a)
        nrm = d.cross(tC).normalized()
        if nrm.z < 0:
            nrm = -nrm
        trilha(bm, [a + tC * sx * 0.068 + nrm * 0.05, b + tC * sx * 0.068 + nrm * 0.05], 0.006, 6)
pm = calha_pts[1]                                                          # suporte da dobra até o braço no tanque
pt = Vector((dC.x * R_T, dC.y * R_T, 0.9))
viga(bm, pm - Z * 0.01, Vector((pm.x, pm.y, 0.9)), 0.02)
viga(bm, Vector((pm.x, pm.y, 0.9)), pt, 0.02)
viga(bm, calha_pts[2] - Z * 0.01, Vector((calha_pts[2].x, calha_pts[2].y, 0.43)), 0.02)
obj('calha_suportes', bm, 'grafite')
bm, bm2 = bmesh.new(), bmesh.new()                                         # folhas descendo pela calha
for k in range(10):
    f = random.uniform(0.05, 0.95)
    a, b = (calha_pts[0], calha_pts[1]) if f < 0.4 else (calha_pts[1], calha_pts[2])
    ff = f / 0.4 if f < 0.4 else (f - 0.4) / 0.6
    p = a.lerp(b, ff) + tC * random.uniform(-0.035, 0.035) + Z * 0.006
    folha(bm if k % 2 else bm2, p, random.uniform(0.05, 0.08), random.uniform(0, PI), (b - a).cross(tC).normalized() * (1 if (b - a).cross(tC).z > 0 else -1))
obj('folhas_calha', bm, 'folha_seca')
obj('folhas_calha2', bm2, 'folha_podre')
# caçamba (sem porta: drones esvaziam pelo topo)
CX0, CX1, CY0, CY1, CZ1 = CB.x - 0.24, CB.x + 0.2, CB.y - 0.2, CB.y + 0.22, 0.44
CX0, CY0 = max(CX0, -0.92), max(CY0, -0.92)
bm = bmesh.new()
caixa_de(bm, (CX0, CY0, 0.08), (CX1, CY0 + 0.012, CZ1))
caixa_de(bm, (CX0, CY1 - 0.012, 0.08), (CX1, CY1, CZ1))
caixa_de(bm, (CX0, CY0, 0.08), (CX0 + 0.012, CY1, CZ1))
caixa_de(bm, (CX1 - 0.012, CY0, 0.08), (CX1, CY1, CZ1))
caixa_de(bm, (CX0, CY0, 0.08), (CX1, CY1, 0.1))
obj('cacamba', bm, 'amarelo')
bm = bmesh.new()
for x in (CX0 + 0.1, CX1 - 0.1):                                           # nervuras
    caixa_de(bm, (x - 0.012, CY0 - 0.012, 0.1), (x + 0.012, CY0, CZ1))
    caixa_de(bm, (x - 0.012, CY1, 0.1), (x + 0.012, CY1 + 0.012, CZ1))
caixa_de(bm, (CX0 - 0.01, CY0 - 0.01, CZ1 - 0.02), (CX1 + 0.01, CY0 + 0.015, CZ1 + 0.005))    # aro (quatro barras)
caixa_de(bm, (CX0 - 0.01, CY1 - 0.015, CZ1 - 0.02), (CX1 + 0.01, CY1 + 0.01, CZ1 + 0.005))
caixa_de(bm, (CX0 - 0.01, CY0 - 0.01, CZ1 - 0.02), (CX0 + 0.015, CY1 + 0.01, CZ1 + 0.005))
caixa_de(bm, (CX1 - 0.015, CY0 - 0.01, CZ1 - 0.02), (CX1 + 0.01, CY1 + 0.01, CZ1 + 0.005))
for x in (CX0 + 0.03, CX1 - 0.03):                                         # olhais de içamento (drone)
    toro(bm, Vector((x, (CY0 + CY1) / 2, CZ1 + 0.03)), 0.025, 0.006, X, nR=16, nr=6)
obj('cacamba_aro', bm, 'grafite')
bm, bm2, bm3 = bmesh.new(), bmesh.new(), bmesh.new()                        # monte de folhas e lodo dentro
for k in range(40):
    p = Vector((random.uniform(CX0 + 0.04, CX1 - 0.04), random.uniform(CY0 + 0.04, CY1 - 0.04), 0))
    p.z = CZ1 - 0.07 + 0.05 * math.exp(-((p.x - CB.x) ** 2 + (p.y - CB.y) ** 2) * 30) + random.uniform(-0.01, 0.01)
    folha([bm, bm2, bm3][k % 3], p, random.uniform(0.05, 0.09), random.uniform(0, PI),
          Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), 1)))
caixa_de(bm3, (CX0 + 0.013, CY0 + 0.013, 0.1), (CX1 - 0.013, CY1 - 0.013, CZ1 - 0.08))
obj('cacamba_folhas', bm, 'folha_seca')
obj('cacamba_folhas2', bm2, 'folha_verde')
obj('cacamba_lodo', bm3, 'folha_podre')
bm = bmesh.new()                                                           # chorume escorrendo pelos furos de dreno
for k in range(5):
    x = CX0 + 0.06 + k * (CX1 - CX0 - 0.12) / 4
    caixa_de(bm, (x - 0.01, CY0 - 0.0135, 0.1), (x + 0.01, CY0 - 0.0125, 0.1 + random.uniform(0.04, 0.12)))
    mancha(bm, (x, CY0 - 0.05), random.uniform(0.03, 0.05), 0.0815)
obj('chorume', bm, 'lodo')

# ------------------------------------------------------------------ pétalas (duas camadas, cada uma com pivô)
PETALAS = []                  # (pivo, camada, phi, nome)
fios_tip = []
NT_, NS_ = 30, 14


def malha_petala(bm):
    vv = [[bm.verts.new(S0(i / NT_, -1 + 2 * j / NS_)) for j in range(NS_ + 1)] for i in range(NT_ + 1)]
    for i in range(NT_):
        for j in range(NS_):
            bm.faces.new((vv[i][j], vv[i][j + 1], vv[i + 1][j + 1], vv[i + 1][j]))


def criar_petala(cam_nome, k):
    cam = CAMADAS[cam_nome]
    phi = cam['fase'] + k * 2 * PI / 5
    nome = 'petala%s%d' % (cam_nome, k)
    pv = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(pv)
    trocada = (cam_nome == 'B' and k == 3)
    bm = bmesh.new()
    malha_petala(bm)
    o = obj(nome + '_chapa', bm, 'zarcao' if trocada else 'chapa', pv)
    sm = o.modifiers.new('esp', 'SOLIDIFY')
    sm.thickness, sm.offset = ESP, -1
    liso(o)
    bm = bmesh.new()                                                       # borda enrolada (calha) e nervura de baixo
    borda = [S(i / NT_, -1, -0.002) for i in range(NT_ + 1)][::-1] + [S(i / NT_, 1, -0.002) for i in range(1, NT_ + 1)]
    trilha(bm, borda, 0.0075, 8)
    trilha(bm, [S(0, -1, 0) + Vector((0, 0, 0.004)), S(0, 1, 0) + Vector((0, 0, 0.004))], 0.008)
    for s in (-0.55, 0.0, 0.55):                                           # nervuras por baixo (veias da folha)
        pts = [S(t, s * (1 - t), -ESP - (0.006 if s == 0 else 0.004)) for t in (i / 10 * 0.85 for i in range(11))]
        trilha(bm, pts, 0.009 if s == 0 else 0.006, 6)
    for t0 in (0.2, 0.45, 0.68):
        trilha(bm, [S(t0, 0, -ESP - 0.004), S(t0 + 0.12, -0.8, -ESP - 0.003)], 0.005, 6)
        trilha(bm, [S(t0, 0, -ESP - 0.004), S(t0 + 0.12, 0.8, -ESP - 0.003)], 0.005, 6)
    cil(bm, Vector((0, 0, 0)), 0.021, 0.17, X, lados=16)                   # nó da dobradiça
    suavizar(obj(nome + '_aro', bm, 'amarelo' if not trocada else 'grafite', pv))
    bm = bmesh.new()                                                       # orelha do pistão (por baixo)
    po = S(T_ORELHA, 0, -0.05)
    for sx in (-1, 1):
        a = S(T_ORELHA - 0.03, 0, -ESP) + Vector((sx * 0.022, 0, 0))
        b = S(T_ORELHA + 0.03, 0, -ESP) + Vector((sx * 0.022, 0, 0))
        f = [bm.verts.new(p) for p in (a, b, po + Vector((sx * 0.022, 0, 0)) + (b - a) * 0.3,
                                          po + Vector((sx * 0.022, 0, 0)) - (b - a) * 0.3)]
        bm.faces.new(f)
    o2 = obj(nome + '_orelha', bm, 'amarelo' if not trocada else 'grafite', pv)
    o2.modifiers.new('esp', 'SOLIDIFY').thickness = 0.008
    bm = bmesh.new()                                                       # pino da orelha e rebites da borda
    cil(bm, po, 0.009, 0.07, X, lados=10)
    for i in range(2, NT_ - 2, 3):
        for s in (-0.86, 0.86):
            esfera(bm, S(i / NT_, s, 0.002), 0.0045, 6)
    for i in range(2, NT_ - 4, 4):
        esfera(bm, S(i / NT_, 0, 0.002), 0.004, 6)
    obj(nome + '_rebites', bm, 'ferro', pv)
    bm = bmesh.new()                                                       # remendo aparafusado (algumas)
    if k in (1, 4) or (cam_nome == 'A' and k == 2):
        t0, s0 = random.uniform(0.3, 0.6), random.uniform(-0.4, 0.4)
        c, nrm = S(t0, s0, 0.004), nP(t0, s0)
        du = (S(t0 + 0.02, s0) - S(t0, s0)).normalized()
        dv = nrm.cross(du)
        w, h = 0.08, 0.1
        vv = [bm.verts.new(c + du * a * h / 2 + dv * b * w / 2) for a, b in ((-1, -1), (-1, 1), (1, 1), (1, -1))]
        bm.faces.new(vv)
        rem = obj(nome + '_remendo', bm, 'cano', pv)
        rem.modifiers.new('esp', 'SOLIDIFY').thickness = 0.004
        bm = bmesh.new()
        for a, b in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            esfera(bm, c + nrm * 0.004 + du * a * (h / 2 - 0.012) + dv * b * (w / 2 - 0.012), 0.005, 6)
        obj(nome + '_remendo_paraf', bm, 'ferro', pv)
    bm, bm2 = bmesh.new(), bmesh.new()                                     # lodo no pé da pétala e folhas presas
    for j in range(7):
        t = random.uniform(0.02, 0.16)
        s = random.uniform(-0.7, 0.7)
        borrao(bm, S(t, s, 0.0), random.uniform(0.02, 0.045), nP(t, s), 0.25)
    for j in range(3):
        t = random.uniform(0.08, 0.55)
        s = random.uniform(-0.6, 0.6)
        folha(bm2, S(t, s, 0.006), random.uniform(0.05, 0.08), random.uniform(0, PI), nP(t, s))
    liso(obj(nome + '_lodo', bm, 'lodo', pv))
    obj(nome + '_folhas', bm2, random.choice(('folha_seca', 'folha_podre', 'folha_verde')), pv)
    bm = bmesh.new()                                                       # escorrido de ferrugem/limo por baixo
    for j in range(5):
        s = random.uniform(-0.8, 0.8)
        t0 = random.uniform(0.15, 0.7)
        pts = [S(t0 - d, s, -ESP - 0.0015) for d in (0, 0.04, 0.08, 0.12)]
        for a, b in zip(pts, pts[1:]):
            dd = (b - a)
            nrm = nP(t0, s)
            side = dd.cross(nrm).normalized() * 0.008
            vv = [bm.verts.new(p) for p in (a - side, a + side, b + side * 0.6, b - side * 0.6)]
            bm.faces.new(vv)
    obj(nome + '_ferrugem', bm, 'ferrugem' if k % 2 else 'limo', pv)
    bm = bmesh.new()                                                       # filme d'água escorrendo (só chuva)
    nt2, ns2 = 22, 6
    vv = [[bm.verts.new(S(i / nt2 * 0.85, -0.4 + 0.8 * j / ns2, 0.0035)) for j in range(ns2 + 1)] for i in range(nt2 + 1)]
    for i in range(nt2):
        for j in range(ns2):
            bm.faces.new((vv[i][j], vv[i][j + 1], vv[i + 1][j + 1], vv[i + 1][j]))
    so_chuva(liso(obj(nome + '_filme', bm, 'filme', pv)))
    PETALAS.append((pv, cam_nome, phi, nome))
    return pv


for k in range(5):
    criar_petala('A', k)
    criar_petala('B', k)

# dobradiças fixas no colar (garfo + pino)
bm, bp = bmesh.new(), bmesh.new()
for pv, cn, phi, nome in PETALAS:
    cam = CAMADAS[cn]
    Mb = mat_base(cam, phi)
    zc = z_colar(cam['rh']) - 0.004
    for sx in (-1, 1):
        h = cam['zh'] - zc + 0.018
        c = Mb @ Vector((sx * 0.103, 0, -h / 2 + 0.018))
        caixa(bm, c, (0.014, 0.06, h), Mb.to_3x3())
    caixa(bm, Mb @ Vector((0, 0, -(cam["zh"] - zc) + 0.006)), (0.23, 0.07, 0.012), Mb.to_3x3())
    tubo(bp, Mb @ Vector((-0.122, 0, 0)), Mb @ Vector((0.122, 0, 0)), 0.009, 10)
obj('dobradicas', bm, 'grafite')
obj('dobradicas_pinos', bp, 'cromo')

# ------------------------------------------------------------------ pistões das pétalas: braços no tanque e anel hidráulico
def pistao(nome):
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    camisa = bpy.data.objects.new(nome + '_camisa', None)
    haste = bpy.data.objects.new(nome + '_haste', None)
    for o in (camisa, haste):
        sc.collection.objects.link(o)
        o.parent = raiz
        o.rotation_mode = 'QUATERNION'
    bm, bm2 = bmesh.new(), bmesh.new()
    cil(bm, Vector((0, 0, 0.17)), 0.032, 0.26, lados=20)
    for z in (0.045, 0.3):
        cil(bm2, Vector((0, 0, z)), 0.037, 0.02, lados=20)
    cil(bm2, Vector((0, 0, 0.0)), 0.015, 0.05, X, lados=10)                # olhal (pino em x local)
    caixa(bm2, Vector((0, 0, 0.016)), (0.032, 0.04, 0.032))
    caixa(bm2, Vector((0, 0.036, 0.075)), (0.022, 0.02, 0.022))            # porta da mangueira
    suavizar(obj(nome + '_corpo', bm, 'amarelo', camisa))
    obj(nome + '_tampas', bm2, 'ferro', camisa)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.16)), 0.013, 0.3, lados=14)
    cil(bm, Vector((0, 0, 0.0)), 0.015, 0.035, X, lados=10)
    caixa(bm, Vector((0, 0, 0.014)), (0.03, 0.026, 0.028))
    suavizar(obj(nome + '_cromo', bm, 'cromo', haste))
    bm = bmesh.new()                                                       # sanfona/raspador e óleo na haste
    cil(bm, Vector((0, 0, 0.3)), 0.02, 0.012, lados=14)
    obj(nome + '_raspador', bm, 'borracha', camisa)
    return camisa, haste


def ancora(cn, phi):
    r, z = CAMADAS[cn]['anc']
    return Vector((math.cos(phi) * r, math.sin(phi) * r, z))


PISTOES = {}
bm, bp = bmesh.new(), bmesh.new()
for pv, cn, phi, nome in PETALAS:
    PISTOES[nome] = pistao('pistao_' + nome)
    a = ancora(cn, phi)
    d = Vector((math.cos(phi), math.sin(phi), 0))
    t = Vector((-d.y, d.x, 0))
    pw = Vector((d.x * (R_T - 0.005), d.y * (R_T - 0.005), a.z - 0.06))
    for sx in (-1, 1):                                                     # braço em garfo soldado no casco
        f = [bm.verts.new(p) for p in (pw + t * sx * 0.03 - Z * 0.05, pw + t * sx * 0.03 + Z * 0.04,
                                         a + t * sx * 0.03 + Z * 0.03, a + t * sx * 0.03 - Z * 0.03)]
        bm.faces.new(f)
    caixa(bp, pw + d * 0.003, (0.01, 0.1, 0.13), Matrix.Rotation(phi, 3, 'Z'))   # chapa de reforço
    tubo(bp, a - t * 0.05, a + t * 0.05, 0.008, 8)
bracos = obj('bracos_pistao', bm, 'grafite')
bracos.modifiers.new('esp', 'SOLIDIFY').thickness = 0.01
obj('bracos_pinos', bp, 'ferro')
bm, bp = bmesh.new(), bmesh.new()                                          # anel distribuidor hidráulico
toro(bm, Vector((0, 0, Z_MANI)), R_MANI, 0.017, nR=72, nr=10)
for k in range(8):
    a = k * PI / 4 + 0.2
    if abs(((a - PHI_VISOR + PI) % (2 * PI)) - PI) < 0.15:
        continue
    p = Vector((math.cos(a) * R_MANI, math.sin(a) * R_MANI, Z_MANI))
    w = Vector((math.cos(a) * R_T, math.sin(a) * R_T, Z_MANI))
    viga(bm, w, p, 0.016)
    toro(bm, p, 0.02, 0.005, Vector((-math.sin(a), math.cos(a), 0)), nR=16, nr=6)
for pv, cn, phi, nome in PETALAS:                                          # tês com válvula para cada pistão
    p = Vector((math.cos(phi) * R_MANI, math.sin(phi) * R_MANI, Z_MANI))
    cil(bp, p + Z * 0.025, 0.012, 0.04, lados=10)
    caixa(bp, p + Z * 0.05, (0.024, 0.024, 0.02))
suavizar(obj('anel_hidraulico', bm, 'cano'))
obj('anel_tes', bp, 'bronze')

# ------------------------------------------------------------------ visor de nível
dV = Vector((math.cos(PHI_VISOR), math.sin(PHI_VISOR), 0))
tV = Vector((-dV.y, dV.x, 0))
R_VIS = R_T + 0.08
V0z, V1z = 0.2, 0.78
pV = dV * R_VIS
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
for z in (V0z, V1z):                                                       # niples com válvula até o tanque
    cano(bm, bf, bp, [dV * (R_T - 0.01) + Z * z, dV * (R_VIS - 0.025) + Z * z], 0.014, 12, fl=False)
    cil(bm, dV * (R_T + 0.04) + Z * z, 0.022, 0.035, dV, lados=8)
    caixa(bm, dV * (R_T + 0.04) + Z * (z + 0.035), (0.02, 0.02, 0.03))
for z in (V0z - 0.02, V1z + 0.02):                                         # cabeçotes do visor
    cil(bm, pV + Z * z, 0.03, 0.06, lados=16)
cil(bm, pV + Z * (V0z - 0.08), 0.012, 0.05, lados=8)                       # dreno do visor
for z in (0.35, 0.5, 0.65):                                                # abraçadeiras
    toro(bm, pV + Z * z, 0.024, 0.005, nR=20, nr=6)
    viga(bm, pV + Z * z - dV * 0.024, dV * (R_T + 0.005) + Z * z, 0.012)
suavizar(obj('visor_metal', bm, 'aco'))
obj('visor_flanges', bf, 'grafite')
obj('visor_paraf', bp, 'ferro')
bm = bmesh.new()
tubo_oco(bm, pV + Z * ((V0z + V1z) / 2), 0.02, 0.016, V1z - V0z - 0.02, lados=24)
obj('visor_vidro', bm, 'visor')
bm, bm2 = bmesh.new(), bmesh.new()                                         # régua graduada
caixa(bm, pV + tV * 0.05 + Z * ((V0z + V1z) / 2), (0.006, 0.035, V1z - V0z), Matrix.Rotation(PHI_VISOR, 3, 'Z'))
for i in range(11):
    z = V0z + 0.01 + (V1z - V0z - 0.02) * i / 10
    caixa(bm2, pV + tV * (0.045 if i % 5 else 0.04) + dV * 0.004 + Z * z, (0.002, 0.02 if i % 5 else 0.03, 0.004),
          Matrix.Rotation(PHI_VISOR, 3, 'Z'))
obj('visor_regua', bm, 'mostrador')
obj('visor_marcas', bm2, 'grafite')
viga(bm := bmesh.new(), pV + tV * 0.05, dV * (R_T + 0.005) + tV * 0.05, 0.01)
obj('visor_regua_sup', bm, 'grafite')
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.5)), 0.0155, 1.0, lados=20)
agua_visor = obj('visor_agua', bm, 'agua_visor')
agua_visor.location = pV + Z * (V0z - 0.008)
bm = bmesh.new()
esfera(bm, Vector((0, 0, 0)), 0.0145, 14)
boia = obj('visor_boia', bm, 'boia')

# ------------------------------------------------------------------ saída: bocal sul, válvula, bomba, motor, cano com flange
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
Z_B = P_BOMBA.z
suc = [Vector((0, -R_T + 0.02, Z_B)), Vector((0, P_BOMBA.y, Z_B)), Vector((P_BOMBA.x - 0.075, P_BOMBA.y, Z_B))]
cano(bm, bf, bp, suc, 0.042)
cil(bm, Vector((0, -R_T - 0.01, Z_B)), 0.075, 0.03, Y, lados=24)           # bocal reforçado no casco
cano(bm, bf, bp, [Vector((P_BOMBA.x, P_BOMBA.y - 0.1, P_BOMBA.z + 0.1)), Vector((P_BOMBA.x, P_BOMBA.y - 0.1, Z_SAIDA)),
                  Vector((X_SAIDA, P_BOMBA.y - 0.1, Z_SAIDA)), Vector((X_SAIDA, -0.985, Z_SAIDA))], 0.045)
flange(bf, bp, Vector((X_SAIDA, -0.975, Z_SAIDA)), Y, 0.085, 0.024, 10)    # flange da porta de saída
suavizar(obj('canos', bm, 'cano'))
obj('canos_flanges', bf, 'grafite')
obj('canos_paraf', bp, 'ferro')
bm = bmesh.new()                                                           # válvula gaveta com atuador elétrico
VG = Vector((0, -0.53, Z_B))
cil(bm, VG, 0.065, 0.09, Y, lados=20)
caixa(bm, VG + Z * 0.09, (0.06, 0.06, 0.1))
caixa(bm, VG + Z * 0.17, (0.11, 0.09, 0.08))
cil(bm, VG + Z * 0.17 + X * 0.07, 0.035, 0.05, X, lados=16)
suavizar(obj('valvula', bm, 'amarelo'))
bm = bmesh.new()                                                           # retenção no recalque
cil(bm, Vector((P_BOMBA.x, P_BOMBA.y - 0.1, 0.47)), 0.06, 0.07, lados=20)
caixa(bm, Vector((P_BOMBA.x + 0.05, P_BOMBA.y - 0.1, 0.47)), (0.03, 0.05, 0.05))
suavizar(obj('retencao', bm, 'ferro'))
bm = bmesh.new()                                                           # caracol da bomba
cil(bm, P_BOMBA, 0.14, 0.11, X, lados=40)
cil(bm, P_BOMBA + Vector((0, -0.04, 0.02)), 0.13, 0.115, X, lados=40)
cil(bm, Vector((P_BOMBA.x, P_BOMBA.y - 0.1, P_BOMBA.z + 0.06)), 0.05, 0.12, lados=20)
cil(bm, P_BOMBA - X * 0.07, 0.05, 0.04, X, lados=20)
for k in range(10):
    a = k * 2 * PI / 10
    cil(bm, P_BOMBA + X * 0.058 + Vector((0, math.cos(a), math.sin(a))) * 0.125, 0.007, 0.012, X, lados=6)
suavizar(obj('bomba_caracol', bm, 'ferro'))
bm = bmesh.new()                                                           # motor aletado
MX0, MX1 = P_BOMBA.x + 0.1, P_BOMBA.x + 0.4
cil(bm, Vector(((MX0 + MX1) / 2, P_BOMBA.y, Z_B)), 0.1, MX1 - MX0, X, lados=32)
for k in range(18):
    a = k * 2 * PI / 18
    if 1.2 < (a % (2 * PI)) < 1.95:
        continue
    rot = Matrix.Rotation(a, 3, 'X')
    caixa(bm, Vector(((MX0 + MX1) / 2, P_BOMBA.y, Z_B)) + rot @ Vector((0, 0.108, 0)), (MX1 - MX0 - 0.03, 0.022, 0.004), rot)
caixa(bm, Vector(((MX0 + MX1) / 2, P_BOMBA.y, Z_B + 0.12)), (0.09, 0.08, 0.05))    # caixa de ligação
suavizar(obj('motor', bm, 'grafite'))
bm = bmesh.new()
cil(bm, Vector((MX1 + 0.025, P_BOMBA.y, Z_B)), 0.105, 0.05, X, lados=32)     # tampa do ventilador
for k in range(8):
    caixa(bm, Vector((MX1 + 0.051, P_BOMBA.y, Z_B - 0.07 + k * 0.02)), (0.004, 0.18 - abs(k - 3.5) * 0.02, 0.006))
cil(bm, Vector((P_BOMBA.x + 0.078, P_BOMBA.y, Z_B)), 0.06, 0.045, X, lados=20)   # luva do acoplamento
suavizar(obj('motor_tampa', bm, 'amarelo'))
bm = bmesh.new()                                                           # base (skid) da bomba
caixa_de(bm, (P_BOMBA.x - 0.1, P_BOMBA.y - 0.13, 0.08), (MX1 + 0.06, P_BOMBA.y + 0.13, 0.12))
for x in (P_BOMBA.x, MX0 + 0.05, MX1 - 0.05):
    caixa_de(bm, (x - 0.025, P_BOMBA.y - 0.09, 0.12), (x + 0.025, P_BOMBA.y + 0.09, Z_B - 0.08))
caixa_de(bm, (X_SAIDA - 0.03, -0.9, 0.08), (X_SAIDA + 0.03, -0.86, Z_SAIDA - 0.045))   # pé do cano de saída
obj('skid', bm, 'grafite')
bm, bf, bpn = bmesh.new(), bmesh.new(), bmesh.new()
manometro(bm, bf, bpn, Vector((P_BOMBA.x, P_BOMBA.y - 0.1, Z_SAIDA + 0.045)), Z, Vector((-0.6, -1, 0)))
manometro(bm, bf, bpn, Vector((0.06, -0.62, Z_B + 0.04)), Z, Vector((-1, -0.6, 0)))
obj('manometros', bm, 'aco')
obj('manometros_face', bf, 'mostrador')
obj('manometros_pont', bpn, 'ponteiro')

# ------------------------------------------------------------------ ladrão (transbordo) a oeste e canaleta
PHI_L = PI
dL = Vector((-1, 0, 0))
Z_L = 0.74
SAI_L = Vector((-0.8, 0, 0.33))
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [dL * (R_T - 0.01) + Z * Z_L, dL * 0.64 + Z * Z_L, dL * 0.64 + Z * 0.33, SAI_L], 0.04)
cil(bm, SAI_L + dL * 0.01, 0.052, 0.04, X, lados=24, r2=None)               # boca
suavizar(obj('ladrao', bm, 'cano'))
obj('ladrao_flanges', bf, 'grafite')
obj('ladrao_paraf', bp, 'ferro')
bm = bmesh.new()
viga(bm, dL * 0.64 + Z * 0.5, dL * R_T + Z * 0.5, 0.02)
caixa_de(bm, (-0.67, -0.03, 0.08), (-0.61, 0.03, 0.29))
obj('ladrao_suporte', bm, 'grafite')
bm = bmesh.new()                                                           # canaleta com grade na borda oeste
caixa_de(bm, (-0.98, -0.3, 0.06), (-0.86, 0.3, 0.085))
obj('canaleta', bm, 'ferro')
bm = bmesh.new()
for k in range(14):
    y = -0.28 + k * 0.56 / 13
    caixa_de(bm, (-0.975, y - 0.005, 0.083), (-0.865, y + 0.005, 0.09))
obj('canaleta_grade', bm, 'aco')
bm = bmesh.new()                                                           # limo e lodo escorrendo do ladrão
for k in range(10):
    mancha(bm, (random.uniform(-0.86, -0.72), random.uniform(-0.12, 0.12)), random.uniform(0.015, 0.04), 0.0815)
for k in range(5):
    z0 = 0.33 - 0.02
    caixa_de(bm, (-0.83, -0.01 + k * 0.005 - 0.01, z0 - 0.06 - k * 0.01), (-0.828, 0.01 + k * 0.005, z0))
obj('limo_ladrao', bm, 'limo')

# ------------------------------------------------------------------ unidade hidráulica (NO) e mangueiras
HU0, HU1 = Vector((-0.9, 0.5, 0.08)), Vector((-0.56, 0.86, 0.38))
bm = bmesh.new()
caixa_de(bm, HU0, HU1)
cil(bm, Vector((-0.73, 0.68, 0.45)), 0.065, 0.14, Y, lados=20)             # motor da bomba hidráulica
for k in range(5):
    cil(bm, Vector((-0.73, 0.62 + k * 0.03, 0.45)), 0.074, 0.006, Y, lados=20)
caixa_de(bm, (-0.66, 0.52, 0.38), (-0.57, 0.62, 0.44))                     # bloco de válvulas
suavizar(obj('hidraulica', bm, 'grafite'))
bm = bmesh.new()
cil(bm, Vector((-0.86, 0.82, 0.62)), 0.04, 0.48, lados=20)                 # acumulador
esfera(bm, Vector((-0.86, 0.82, 0.86)), 0.04, 20)
esfera(bm, Vector((-0.86, 0.82, 0.38)), 0.04, 20)
viga(bm, Vector((-0.86, 0.86, 0.6)), Vector((-0.86, 0.9, 0.6)), 0.012)
suavizar(obj('acumulador', bm, 'zarcao'))
bm = bmesh.new()
cil(bm, Vector((-0.84, 0.55, 0.42)), 0.022, 0.03, lados=10)                # bocal de enchimento
caixa_de(bm, (-0.905, 0.6, 0.15), (-0.9, 0.7, 0.33))                       # visor de óleo
obj('hidraulica_det', bm, 'cromo')
bm = bmesh.new()
phiH = math.radians(135)
pM = Vector((math.cos(phiH) * R_MANI, math.sin(phiH) * R_MANI, Z_MANI))
mangueira(bm, bezier((-0.62, 0.57, 0.44), (-0.62, 0.57, 0.75), pM + Vector((-0.12, 0.12, -0.1)), pM - Z * 0.015, 16), 0.013)
mangueira(bm, bezier((-0.6, 0.6, 0.44), (-0.55, 0.62, 0.8), pM + Vector((-0.06, 0.16, -0.05)), pM + Vector((0.04, 0.03, -0.012)), 16), 0.01)
mangueira(bm, bezier((-0.86, 0.82, 0.9), (-0.86, 0.82, 1.0), (-0.75, 0.75, 0.95), (-0.66, 0.62, 0.44), 14), 0.009)
obj('mangueiras_hu', bm, 'borracha')

# ------------------------------------------------------------------ mastro: sensor de nuvem, antena, anemômetro, lança com anel
Z_TOPO = 2.78
bm = bmesh.new()
cil(bm, MASTRO + Z * 0.1, 0.11, 0.03, lados=24)
cil(bm, MASTRO + Z * (Z_TOPO / 2), 0.042, Z_TOPO, lados=20)
for k in range(4):                                                         # mãos-francesas da base
    a = k * PI / 2 + PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    f = [bm.verts.new(p) for p in (MASTRO + d * 0.04 + Z * 0.11, MASTRO + d * 0.105 + Z * 0.11, MASTRO + d * 0.04 + Z * 0.32)]
    bm.faces.new(f)
for z in (0.9, 1.7, 2.4):                                                  # anéis de emenda
    cil(bm, MASTRO + Z * z, 0.052, 0.03, lados=20)
LANCA_A = MASTRO + Z * Z_ANEL_C + Z * 0.14
LANCA_B = Vector((0, 0, Z_ANEL_C + 0.14))
tubo(bm, LANCA_A, LANCA_B, 0.028, 16)
tubo(bm, MASTRO + Z * 2.05, LANCA_A.lerp(LANCA_B, 0.45), 0.018, 12)        # escora diagonal
cil(bm, LANCA_B, 0.045, 0.06, lados=16)
tubo(bm, LANCA_B, LANCA_B - Z * 0.1, 0.02, 12)
cil(bm, MASTRO + Z * Z_TOPO, 0.06, 0.04, lados=20)
suavizar(obj('mastro', bm, 'amarelo'))
bm = bmesh.new()                                                           # anel emissor: toro + cristais
toro(bm, Vector((0, 0, Z_ANEL_C)), R_ANEL_C, 0.013, nR=48, nr=10)
for k in range(3):
    a = k * 2 * PI / 3 + 0.3
    viga(bm, LANCA_B - Z * 0.1, Vector((math.cos(a) * R_ANEL_C, math.sin(a) * R_ANEL_C, Z_ANEL_C + 0.01)), 0.012)
suavizar(obj('anel_emissor', bm, 'grafite'))
bm = bmesh.new()
FIOS_TOPO = []
for k in range(6):
    a = k * PI / 3
    p = Vector((math.cos(a) * R_ANEL_C, math.sin(a) * R_ANEL_C, Z_ANEL_C - 0.02))
    FIOS_TOPO.append(p)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.016, radius2=0.0, depth=0.05,
                          matrix=Matrix.Translation(p - Z * 0.01) @ Matrix.Rotation(PI, 4, 'X'))
bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.02, radius2=0.0, depth=0.08,
                      matrix=Matrix.Translation(LANCA_B - Z * 0.14) @ Matrix.Rotation(PI, 4, 'X'))
emissores = obj('emissores', bm, 'cristal')
bm = bmesh.new()                                                           # fios de campo: anel → ápice do domo
FIOS = []
for p in FIOS_TOPO:
    q = APEX + (p - APEX).normalized() * 0.02 + Z * 0.0
    q = Vector((p.x * 0.18, p.y * 0.18, APEX.z + 0.005))
    tubo(bm, p - Z * 0.03, q, 0.0028, 6)
    FIOS.append((p - Z * 0.035, q))
fios = obj('fios_campo', bm, 'fio')
bm = bmesh.new()                                                           # sensor de nuvem no topo
cil(bm, MASTRO + Z * (Z_TOPO + 0.05), 0.075, 0.06, lados=24)
cil(bm, MASTRO + Z * (Z_TOPO + 0.085), 0.09, 0.012, lados=24)
caixa(bm, MASTRO + Z * (Z_TOPO - 0.12) + Vector((-0.06, -0.06, 0)), (0.07, 0.07, 0.1))   # caixa do sensor
tubo(bm, MASTRO + Z * (Z_TOPO + 0.06) + Vector((0.07, -0.02, 0)), MASTRO + Z * (Z_TOPO + 0.75) + Vector((0.07, -0.02, 0)), 0.005, 6)  # antena
cil(bm, MASTRO + Z * (Z_TOPO + 0.08) + Vector((0.07, -0.02, 0)), 0.014, 0.05, lados=10)
tubo(bm, MASTRO + Z * (Z_TOPO - 0.05), MASTRO + Z * (Z_TOPO - 0.05) + Vector((-0.12, 0.12, 0.1)), 0.008, 6)
suavizar(obj('sensor_corpo', bm, 'grafite'))
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.07)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.001], context='VERTS')
for v in bm.verts:
    v.co += MASTRO + Z * (Z_TOPO + 0.09)
liso(obj('sensor_domo', bm, 'domo'))
bm = bmesh.new()
esfera(bm, MASTRO + Z * (Z_TOPO + 0.12), 0.03, 16)
nucleo_sensor = obj('sensor_nucleo', bm, 'cristal')
bm = bmesh.new()
esfera(bm, MASTRO + Z * (Z_TOPO + 0.76) + Vector((0.07, -0.02, 0)), 0.012, 10)
luz_antena = obj('antena_luz', bm, 'led_ambar')
anemo = bpy.data.objects.new('anemometro', None)                           # anemômetro
sc.collection.objects.link(anemo)
anemo.location = MASTRO + Z * (Z_TOPO - 0.05) + Vector((-0.12, 0.12, 0.1))
bm = bmesh.new()
for k in range(3):
    a = k * 2 * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    tubo(bm, Vector((0, 0, 0.0)), d * 0.08, 0.003, 6)
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.018,
                              matrix=Matrix.Translation(d * 0.09) @ Matrix.Diagonal((1, 1, 0.8, 1)))
cil(bm, Vector((0, 0, 0)), 0.01, 0.03, lados=8)
obj('anemometro_copos', bm, 'aco', anemo)
bm = bmesh.new()                                                           # conduíte e cabos descendo o mastro
for z in (0.4, 0.95, 1.5, 2.1):
    toro(bm, MASTRO + Z * z, 0.047, 0.005, nR=20, nr=5)
obj('abracadeiras_mastro', bm, 'ferro')
bm = bmesh.new()
tubo(bm, MASTRO + Vector((0.05, -0.02, 0.15)), MASTRO + Vector((0.05, -0.02, Z_TOPO - 0.15)), 0.011, 8)
tubo(bm, MASTRO + Vector((0.035, 0.04, 0.15)), MASTRO + Vector((0.035, 0.04, Z_ANEL_C + 0.1)), 0.008, 8)
mangueira(bm, bezier(MASTRO + Vector((0.035, 0.04, Z_ANEL_C + 0.1)), MASTRO + Vector((0.0, 0.04, Z_ANEL_C + 0.2)),
                     MASTRO + Vector((-0.1, -0.05, Z_ANEL_C + 0.2)), LANCA_A.lerp(LANCA_B, 0.12) + Vector((0, 0, 0.03)), 10), 0.008)
mangueira(bm, bezier(MASTRO + Vector((0.05, -0.02, 0.15)), MASTRO + Vector((0.05, -0.1, 0.1)),
                     Vector((0.75, 0.66, 0.66)), Vector((0.72, 0.62, 0.62)), 10), 0.011)
for k in range(2):                                                         # cabo preso por fitas ao longo da lança
    a = LANCA_A.lerp(LANCA_B, 0.12) + Vector((0, 0, 0.03))
    b = LANCA_B + Vector((0, 0, 0.03))
    tubo(bm, a + Vector((0.0, 0.0, 0.005 * k)), b + Vector((0.0, 0.0, 0.005 * k)), 0.006, 6)
obj('cabos_mastro', bm, 'borracha')

# ------------------------------------------------------------------ armário de controle (NE), eletrocalha, cabos
AR0, AR1 = Vector((0.4, 0.5, 0.08)), Vector((0.74, 0.7, 0.62))
bm = bmesh.new()
caixa_de(bm, AR0, AR1)
caixa_de(bm, AR0 - Vector((0.015, 0.015, 0)), AR1 + Vector((0.015, 0.015, 0)) - Vector((0, 0, AR1.z - 0.14)))
caixa_de(bm, (AR0.x - 0.02, AR0.y - 0.02, AR1.z), (AR1.x + 0.02, AR1.y + 0.02, AR1.z + 0.025))
suavizar(obj('armario', bm, 'grafite'))
bm = bmesh.new()
for k in range(6):                                                         # venezianas na face sul
    caixa(bm, Vector(((AR0.x + AR1.x) / 2, AR0.y - 0.004, 0.25 + k * 0.035)), (0.22, 0.01, 0.012),
          Matrix.Rotation(0.5, 3, 'X'))
caixa(bm, Vector((AR0.x + 0.06, AR0.y - 0.006, 0.52)), (0.07, 0.008, 0.05))  # placa de série apagada
obj('armario_det', bm, 'aco')
bm = bmesh.new()
for k in range(3):
    esfera(bm, Vector((AR1.x - 0.04 - k * 0.035, AR0.y - 0.005, 0.56)), 0.009, 10)
leds = obj('armario_leds', bm, 'led_verde')
bm = bmesh.new()
esfera(bm, Vector((AR0.x + 0.05, AR0.y - 0.005, 0.56)), 0.011, 10)
led_alerta = obj('armario_led_ambar', bm, 'led_ambar')
bm = bmesh.new()                                                           # eletrocalha: armário → motor (borda leste)
caixa_de(bm, (0.86, -0.62, 0.1), (0.94, 0.62, 0.13))
caixa_de(bm, (0.86, -0.62, 0.13), (0.865, 0.62, 0.16))
caixa_de(bm, (0.935, -0.62, 0.13), (0.94, 0.62, 0.16))
caixa_de(bm, (0.42, 0.86, 0.1), (0.94, 0.94, 0.13))                        # → unidade hidráulica (borda norte)
caixa_de(bm, (-0.56, 0.86, 0.1), (0.42, 0.94, 0.13))
for y in (-0.5, -0.1, 0.3):
    caixa_de(bm, (0.88, y - 0.01, 0.08), (0.92, y + 0.01, 0.1))
for x in (-0.3, 0.1):
    caixa_de(bm, (x - 0.01, 0.88, 0.08), (x + 0.01, 0.92, 0.1))
obj('eletrocalha', bm, 'aco')
bm = bmesh.new()                                                           # cabos dentro da calha (expostos)
for k in range(3):
    o_ = k * 0.016 - 0.016
    trilha(bm, [Vector((0.9 + o_, 0.62, 0.14)), Vector((0.9 + o_, -0.6, 0.14))], 0.008, 6)
    trilha(bm, [Vector((0.42, 0.9 + o_, 0.14)), Vector((-0.55, 0.9 + o_, 0.14))], 0.007, 6)
mangueira(bm, bezier((0.74, 0.6, 0.3), (0.85, 0.6, 0.3), (0.9, 0.62, 0.2), (0.9, 0.6, 0.145), 8), 0.012)
mangueira(bm, bezier((0.9, -0.6, 0.145), (0.9, -0.66, 0.3), (0.7, -0.62, 0.5), (P_BOMBA.x + 0.25, P_BOMBA.y, Z_B + 0.145), 12), 0.012)
mangueira(bm, bezier((0.5, 0.7, 0.3), (0.45, 0.85, 0.2), (0.42, 0.9, 0.18), (0.42, 0.9, 0.145), 6), 0.011)
mangueira(bm, bezier((-0.55, 0.9, 0.145), (-0.6, 0.9, 0.2), (-0.62, 0.8, 0.3), (-0.73, 0.75, 0.45), 8), 0.011)
mangueira(bm, bezier(VG + Z * 0.21, VG + Z * 0.35 + X * 0.05, Vector((0.2, -0.45, 0.6)), Vector((0.45, -0.45, 0.6)), 10), 0.007)
mangueira(bm, bezier(Vector((0.45, -0.45, 0.6)), Vector((0.75, -0.45, 0.6)), Vector((0.9, -0.3, 0.3)), Vector((0.9, -0.3, 0.145)), 10), 0.007)
obj('cabos', bm, 'borracha')
bm = bmesh.new()                                                           # fiação exposta: fios coloridos soltos do armário
for k, cor in enumerate(('cobre', 'cobre')):
    pts = bezier((AR1.x, 0.66, 0.5), (AR1.x + 0.08, 0.66 - k * 0.02, 0.45), (AR1.x + 0.06, 0.62, 0.3), (AR1.x + 0.0, 0.6, 0.32), 8)
    trilha(bm, pts, 0.003, 5)
obj('fios_expostos', bm, 'cobre')

# ------------------------------------------------------------------ sujeira geral no chão da laje
bm = bmesh.new()
for c, r in (((P_BOMBA.x + 0.1, P_BOMBA.y + 0.12), 0.09), ((MX1, P_BOMBA.y - 0.15), 0.07), ((-0.6, 0.45), 0.1), ((-0.75, 0.48), 0.05)):
    mancha(bm, c, r, 0.0825)
obj('oleo_chao', bm, 'oleo')
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(16):                                                        # lodo seco e folhas espalhadas
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.5, 0.9)
    mancha(bm, (math.cos(a) * r, math.sin(a) * r), random.uniform(0.02, 0.05), 0.0815)
for k in range(26):
    p = Vector((random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95), 0.083))
    if p.length < 0.5:
        continue
    folha(bm2, p, random.uniform(0.04, 0.08), random.uniform(0, PI), Vector((random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 1)))
obj('lodo_chao', bm, 'lodo_seco')
obj('folhas_chao', bm2, 'folha_seca')
bm = bmesh.new()                                                           # anel de limo em volta do pé do tanque
for k in range(30):
    a = k * 2 * PI / 30
    mancha(bm, (math.cos(a) * (R_T + 0.055), math.sin(a) * (R_T + 0.055)), random.uniform(0.015, 0.035), 0.082)
obj('limo_chao', bm, 'limo')
bm = bmesh.new()                                                           # escorrido de água pelo casco (só chuva)
for k in range(9):
    a = random.uniform(0, 2 * PI)
    rot = Matrix.Rotation(a, 3, 'Z')
    h = random.uniform(0.3, 0.75)
    caixa(bm, Vector((math.cos(a) * (R_T + 0.0025), math.sin(a) * (R_T + 0.0025), Z_T1 - h / 2)), (0.002, random.uniform(0.02, 0.05), h), rot)
so_chuva(obj('escorrido_tanque', bm, 'filme'))

# ------------------------------------------------------------------ poças (chuva) e lodo rachado (seco)
def poca(bm, centro, r, z):
    n = 40
    f0, f1 = random.uniform(0, 6), random.uniform(0, 6)
    vv = []
    for i in range(n):
        a = i * 2 * PI / n
        f = 1 + 0.22 * math.sin(a * 2 + f0) + 0.12 * math.sin(a * 5 + f1)
        vv.append(bm.verts.new((centro[0] + math.cos(a) * r * f, centro[1] + math.sin(a) * r * f * 0.75, z)))
    bm.faces.new(vv)


POCAS = []
bm = bmesh.new()
for k in range(10):
    while True:
        x, y = random.uniform(-3.2, 3.2), random.uniform(-3.2, 3.2)
        if not (abs(x) < 1.1 and abs(y) < 1.1):
            break
    r = random.uniform(0.1, 0.28)
    POCAS.append((Vector((x, y, altura(x, y) + 0.012)), r))
    poca(bm, (x, y), r, altura(x, y) + 0.012)
for c, r in (((0.1, -0.85), 0.07), ((-0.2, 0.75), 0.08), ((0.75, 0.2), 0.06)):
    poca(bm, c, r, 0.083)
    POCAS.append((Vector((c[0], c[1], 0.083)), r))
so_chuva(obj('pocas', bm, 'poca'))
bm = bmesh.new()
for k in range(7):
    x, y = random.uniform(-3, 3), random.uniform(-3, 3)
    if abs(x) < 1.1 and abs(y) < 1.1:
        continue
    poca(bm, (x, y), random.uniform(0.1, 0.25), altura(x, y) + 0.004)
so_seco(obj('barro_rachado', bm, 'lodo_seco'))

# ------------------------------------------------------------------ efeitos de chuva
# riscos de chuva: padrão que se repete a cada 3 m em z; o objeto desce em laço
PER = 3.0
bm = bmesh.new()
for k in range(2600):
    x, y = random.uniform(-4.5, 4.5), random.uniform(-4.5, 4.5)
    z = random.uniform(0, PER)
    L = random.uniform(0.12, 0.22)
    for rep in (0, 1):
        c = Vector((x, y, z + rep * PER))
        tubo(bm, c, c + Vector((0.012, 0.006, L)), 0.0015, 4)
chuva = so_chuva(obj('chuva', bm, 'chuva'))
# respingos no chão e nas pétalas (coroas que abrem e somem)
RESPINGOS = []
for k in range(45):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 1.0, 0.25, Z, nR=12, nr=5)
    for j in range(6):
        a = j * PI / 3
        tubo(bm, Vector((math.cos(a), math.sin(a), 0)), Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, 1.8)), 0.2, 4)
    o = so_chuva(obj('respingo', bm, 'gota'))
    RESPINGOS.append(o)
ONDAS = []
for k in range(14):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 1.0, 0.006, Z, nR=40, nr=5)
    ONDAS.append(so_chuva(obj('onda', bm, 'gota')))
# gotas guiadas pelos fios de campo (cada uma com um anel violeta)
GOTAS_FIO = []
for i, (a, b) in enumerate(FIOS):
    for j in range(4):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0, matrix=Matrix.Diagonal((0.011, 0.011, 0.017, 1)))
        g = so_chuva(liso(obj('gota_fio', bm, 'gota')))
        g.rotation_mode = 'QUATERNION'
        g.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
        bm = bmesh.new()
        toro(bm, Vector((0, 0, 0)), 0.016, 0.0025, Z, nR=20, nr=5)
        an = so_chuva(obj('anel_campo', bm, 'campo_anel'))
        an.rotation_mode = 'QUATERNION'
        an.rotation_quaternion = (b - a).to_track_quat('Z', 'Y')
        GOTAS_FIO.append((g, an, a, b, (j + random.random() * 0.4) / 4))
# pingos das pétalas (calhas pingando) e do colar
PINGOS = []
for k in range(16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0, matrix=Matrix.Diagonal((0.008, 0.008, 0.014, 1)))
    PINGOS.append(so_chuva(liso(obj('pingo', bm, 'gota'))))
# jato do ladrão: água saindo em arco até a canaleta
V_L = Vector((-0.55, 0, 0.0))


def no_ladrao(t):
    return SAI_L + dL * 0.03 + V_L * t + Vector((0, 0, -4.9 * t * t))


T_L = (math.sqrt(4 * 4.9 * (SAI_L.z - 0.09))) / (2 * 4.9)
bm = bmesh.new()
NJ, LJ = 24, 14
aneis = []
for i in range(NJ + 1):
    t = T_L * i / NJ
    c = no_ladrao(t)
    tg = (no_ladrao(t + 0.001) - c).normalized()
    v = tg.cross(Y).normalized()
    r = 0.026 + 0.012 * (i / NJ)
    aneis.append([bm.verts.new(c + (Y * math.cos(a) * 1.15 + v * math.sin(a) * 0.8) * r) for a in (j * 2 * PI / LJ for j in range(LJ))])
for i in range(NJ):
    for j in range(LJ):
        bm.faces.new((aneis[i][j], aneis[i][(j + 1) % LJ], aneis[i + 1][(j + 1) % LJ], aneis[i + 1][j]))
bm.faces.new(aneis[0][::-1])
jato_l = so_chuva(liso(obj('jato_ladrao', bm, 'jato')))
IMP_L = no_ladrao(T_L)
bm = bmesh.new()
for k in range(8):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.01, 0.07)
    mancha(bm, (IMP_L.x + math.cos(a) * r, IMP_L.y + math.sin(a) * r), random.uniform(0.02, 0.04), 0.092)
so_chuva(obj('espuma_ladrao', bm, 'filme'))
# água dentro da garganta (sob o domo, só chuva)
bm = bmesh.new()
cil(bm, Vector((0, 0, Z_COLAR0 - 0.005)), R_GAR - 0.015, 0.01, lados=40)
so_chuva(obj('agua_garganta', bm, 'poca'))

# ------------------------------------------------------------------ luzes pontuais
luz_anel_d = bpy.data.lights.new('Luz anel', 'POINT')
luz_anel_d.color = VIOLETA
luz_anel_d.shadow_soft_size = 0.05
luz_anel = bpy.data.objects.new('Luz anel', luz_anel_d)
sc.collection.objects.link(luz_anel)
luz_anel.location = Vector((0, 0, Z_ANEL_C - 0.1))
luz_sensor_d = bpy.data.lights.new('Luz sensor', 'POINT')
luz_sensor_d.color = VIOLETA
luz_sensor_d.shadow_soft_size = 0.03
luz_sensor = bpy.data.objects.new('Luz sensor', luz_sensor_d)
sc.collection.objects.link(luz_sensor)
luz_sensor.location = MASTRO + Z * (Z_TOPO + 0.2)

# ------------------------------------------------------------------ cena: luz, céu, câmera
sol_d = bpy.data.lights.new('Sol', 'SUN')
so = bpy.data.objects.new('Sol', sol_d)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
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
sc.cycles.max_bounces = 12
sc.cycles.transmission_bounces = 12
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


# ------------------------------------------------------------------ estados: chuva (aberto) e seco (fechado)
MANG_P = []                   # mangueiras dos pistões (refeitas por estado)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def pose_petalas(est, fr=0.0):
    """Ângulo de cada pétala, pistões apontados e mangueiras do anel até a porta de cada camisa."""
    for o in MANG_P:
        bpy.data.objects.remove(o, do_unlink=True)
    MANG_P.clear()
    bm = bmesh.new()
    for pv, cn, phi, nome in PETALAS:
        c = CAMADAS[cn]
        th = c['aberto'] if est == 'chuva' else c['fechado']
        if est == 'chuva':                                                 # leve ajuste ao vento
            th += math.radians(1.2) * math.sin(2 * PI * fr + phi)
        Mp = mat_petala(c, phi, th)
        pv.matrix_world = Mp
        camisa, haste = PISTOES[nome]
        a = ancora(cn, phi)
        ponta = Mp @ S(T_ORELHA, 0, -0.05)
        d = ponta - a
        tg = Vector((-math.sin(phi), math.cos(phi), 0))
        camisa.location = a
        camisa.rotation_quaternion = quat_zx(d, tg)
        haste.location = ponta
        haste.rotation_quaternion = quat_zx(-d, tg)
        # mangueira: tê do anel → porta da camisa
        porta = a + camisa.rotation_quaternion.to_matrix() @ Vector((0, 0.047, 0.075))
        t0 = Vector((math.cos(phi) * R_MANI, math.sin(phi) * R_MANI, Z_MANI + 0.06))
        saida = camisa.rotation_quaternion.to_matrix() @ Y
        mangueira(bm, bezier(t0, t0 + Z * 0.08, porta + saida * 0.08, porta, 10), 0.008)
    MANG_P.append(obj('mangueiras_pistoes', bm, 'borracha'))


def estado(est):
    chuva_on = est == 'chuva'
    for o in CHUVA:
        o.hide_render = not chuva_on
    for o in SECO:
        o.hide_render = chuva_on
    pose_petalas(est)
    chao.data.materials[0] = M['terra_molhada' if chuva_on else 'terra_seca']
    for m in bpy.data.materials:
        if m.node_tree and 'molhado' in m.node_tree.nodes:
            m.node_tree.nodes['molhado'].inputs[1].default_value = 0.45 if chuva_on else 1.0
    # nível do tanque no visor
    nivel = 0.86 if chuva_on else 0.14
    hz = (V1z - V0z) * nivel
    agua_visor.scale = (1, 1, hz)
    boia.location = pV + Z * (V0z - 0.008 + hz)
    # céu e sol
    if chuva_on:
        sol_d.energy = 1.1
        sol_d.angle = math.radians(25)
        bg.inputs['Color'].default_value = (0.36, 0.39, 0.43, 1)
        bg.inputs['Strength'].default_value = 0.75
        sc.view_settings.exposure = 0.1
    else:
        sol_d.energy = 4.0
        sol_d.angle = math.radians(2.5)
        bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
        bg.inputs['Strength'].default_value = 0.55
        sc.view_settings.exposure = -0.5
    M['fio'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.5 if chuva_on else 0.0
    M['emissor'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0 if chuva_on else 0.3
    luz_anel_d.energy = 6 if chuva_on else 0
    luz_sensor_d.energy = 3 if chuva_on else 0.5
    luz_sensor_d.color = VIOLETA if chuva_on else AMBAR
    cr = M['cristal'].node_tree.nodes['Principled BSDF']
    cr.inputs['Emission Color'].default_value = (*(VIOLETA if chuva_on else AMBAR), 1)
    bpy.context.view_layer.update()


def raio_baixo(p):
    """Onde um pingo que cai de p bate (ignorando os efeitos)."""
    efeitos = CHUVA
    for o in efeitos:
        o.hide_viewport = True
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, idx, ob, mt = sc.ray_cast(dg, p - Z * 0.02, Vector((0, 0, -1)))
    for o in efeitos:
        o.hide_viewport = False
    return loc if ok else Vector((p.x, p.y, 0.0))


def animar(est):
    """Laço de 4 s do estado: chuva descendo, respingos, gotas nos fios, pingos, luzes, anemômetro."""
    for o in list(sc.objects):
        o.animation_data_clear()
    for m in (M['cristal'], M['campo_anel'], M['led_ambar']):
        m.node_tree.animation_data_clear()
    luz_anel_d.animation_data_clear()
    chuva_on = est == 'chuva'
    # pontos de pingo: borda de baixo das pétalas abertas e borda do colar
    origens = []
    if chuva_on:
        for pv, cn, phi, nome in PETALAS[:8]:
            s = random.choice((-0.75, 0.75))
            origens.append(pv.matrix_world @ S(random.uniform(0.3, 0.55), s, -ESP - 0.01))
        for k in range(8):
            a = k * 2 * PI / 8 + 0.2
            origens.append(Vector((math.cos(a) * (R_COLAR + 0.012), math.sin(a) * (R_COLAR + 0.012), Z_COLAR1 - 0.035)))
        destinos = [raio_baixo(p) for p in origens]
        # respingos: chão, laje e pétalas
        pos_resp = []
        for k in range(len(RESPINGOS)):
            if k < 14:
                pv = PETALAS[k % 10][0]
                t, s = random.uniform(0.3, 0.9), random.uniform(-0.6, 0.6)
                p = pv.matrix_world @ S(t, s, 0.004)
                n_ = (pv.matrix_world.to_3x3() @ nP(t, s)).normalized()
            else:
                while True:
                    x, y = random.uniform(-2.8, 2.8), random.uniform(-2.8, 2.8)
                    if math.hypot(x, y) > 1.15:
                        break
                p = raio_baixo(Vector((x, y, 3.0)))
                n_ = Z
            pos_resp.append((p, n_, random.random(), random.uniform(0.008, 0.016)))
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        anemo.rotation_euler = (0, 0, 2 * PI * (6 if chuva_on else 2) * fr)
        anemo.keyframe_insert('rotation_euler', frame=q)
        pisca = 1.0 if (q // 6) % 4 == 0 else 0.0
        el = M['led_ambar'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        el.default_value = 8.0 * pisca + 0.3
        el.keyframe_insert('default_value', frame=q)
        cr = M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        cr.default_value = (2.2 + 0.8 * math.sin(2 * PI * 4 * fr)) if chuva_on else (0.4 + 0.2 * math.sin(2 * PI * fr))
        cr.keyframe_insert('default_value', frame=q)
        if not chuva_on:
            continue
        chuva.location = (0, 0, -((fr * 8 * PER) % PER))
        chuva.keyframe_insert('location', frame=q)
        ca = M['campo_anel'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        ca.default_value = 6.0 * (0.8 + 0.2 * math.sin(2 * PI * 8 * fr))
        ca.keyframe_insert('default_value', frame=q)
        luz_anel_d.energy = 6 * (0.85 + 0.15 * math.sin(2 * PI * 4 * fr))
        luz_anel_d.keyframe_insert('energy', frame=q)
        for g, an, a, b, ph in GOTAS_FIO:                                  # desce acelerando pelo fio
            u = (ph + fr) % 1.0
            p = a.lerp(b, u * u * 0.4 + u * 0.6)
            sz = suave(u / 0.1) * (1 - suave((u - 0.93) / 0.07)) + 0.001
            g.location = p
            g.scale = (sz, sz, sz)
            an.location = p
            an.scale = (sz, sz, sz)
            for o in (g, an):
                o.keyframe_insert('location', frame=q)
                o.keyframe_insert('scale', frame=q)
        for k, o in enumerate(PINGOS):                                     # pingos: crescem, soltam e caem
            a, b = origens[k], destinos[k]
            ph = (k * 0.37) % 1.0
            u = (ph + fr * 2) % 1.0
            T = math.sqrt(2 * max(0.05, a.z - b.z) / 9.8)
            if u < 0.35:
                p, sz = a, 0.4 + 0.6 * u / 0.35
            else:
                tt = (u - 0.35) / 0.65 * T * 1.15
                p = a - Z * min(a.z - b.z, 4.9 * tt * tt)
                sz = 1.0 if tt < T else 0.001
            o.location = p
            o.scale = (sz, sz, sz)
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('scale', frame=q)
        for k, o in enumerate(RESPINGOS):
            p, n_, ph, tam = pos_resp[k]
            u = (ph + fr * 3) % 1.0
            s = tam * (0.3 + u * 1.2)
            o.location = p
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = n_.to_track_quat('Z', 'Y')
            o.scale = (s, s, max(0.0005, s * (1 - u) * 1.2))
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
            o.keyframe_insert('scale', frame=q)
        for k, o in enumerate(ONDAS):
            c, r = POCAS[k % len(POCAS)]
            u = (k * 0.29 + fr * 2) % 1.0
            off = Vector((math.sin(k * 3.1) * r * 0.4, math.cos(k * 2.3) * r * 0.4, 0.002))
            o.location = c + off
            s = 0.02 + 0.16 * u
            o.scale = (s, s, max(0.05, 1 - u))
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('scale', frame=q)
    for o in list(sc.objects):
        ad = getattr(o, 'animation_data', None)
        if ad and ad.action:
            for fc in getattr(ad.action, 'fcurves', []):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'


def checar():
    """Interpenetração: pétalas entre si e com pistões/braços/dobradiças, nos dois estados."""
    def bvh(o):
        dg = bpy.context.evaluated_depsgraph_get()
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        mw = o.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        ps = [tuple(p.vertices) for p in me.polygons]
        t = BVHTree.FromPolygons(vs, ps)
        oe.to_mesh_clear()
        return t
    for est in ('chuva', 'seco'):
        estado(est)
        bpy.context.view_layer.update()
        chapas = [c for pv, *_ in PETALAS for c in pv.children if c.name.endswith(('_chapa', '_aro'))]
        outros = [o for o in sc.objects if o.type == 'MESH' and (o.name.startswith('pistao_') or o.name in (
            'bracos_pistao', 'dobradicas', 'colar', 'domo_grade', 'mangueiras_pistoes', 'fios_campo', 'mastro',
            'calha_folhas', 'anel_hidraulico', 'cesto_aro', 'colar_escoras'))]
        tr = {o.name: bvh(o) for o in chapas + outros}
        ruins = []
        for i, a in enumerate(chapas):
            pa = a.parent
            for b in chapas[i + 1:] + outros:
                if b.parent == pa:
                    continue
                if tr[a.name].overlap(tr[b.name]):
                    ruins.append((a.name, b.name))
        print('CHECAR', est, len(ruins), ruins[:40])


FR_FOTO = int(QUADROS * 0.5) + 1
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
ALVO = Vector((0.0, 0.0, 1.0))
if modo == 'checar':
    checar()
if modo == 'foto':
    quais = args[1:] or ['chuva', 'seco', 'perto']
    sc.cycles.samples = 160
    for q in quais:
        est = 'seco' if q == 'seco' else 'chuva'
        estado(est)
        animar(est)
        sc.frame_set(FR_FOTO)
        if q == 'perto':
            sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
            mirar((-1.25, -1.55, 2.45), (0.02, -0.05, 1.3), 30)
        else:
            sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
            a = math.radians(238)
            mirar(ALVO + Vector((math.cos(a) * 5.0, math.sin(a) * 5.0, 1.9)), ALVO + Vector((0, 0, 0.1)), 34)
        sc.render.filepath = os.path.join(AQUI, 'coletor_chuva_%s.png' % q)
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    est = args[1]
    v = [float(x) for x in args[2:]]
    sc.cycles.samples = 40
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    estado(est)
    animar(est)
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'coletor_chuva_teste.png')
    bpy.ops.render.render(write_still=True)
print('COLETOR_CHUVA ok')
