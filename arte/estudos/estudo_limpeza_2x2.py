"""Estudos isolados (fora do jogo), lote 12 (limpeza), 2×2 tiles, sem portas:

COLETOR DE LIXO 2 (`coletor_lixo_2`): evolução do coletor aprovado (estudo_coletor_lixo.py) — raio 10, recolhe lama
E cinza e devolve resíduo compactado. Pintura laranja queimada do nível 2 (com peças trocadas ainda no amarelo do
nível 1). Silo octogonal dividido em duas câmaras com visores (lodo a sudoeste, cinza a sudeste). Separador DUPLO em
série no teto: ciclone de lama (pesado, úmido) → ciclone de cinza (fino, seco) → filtro → turbina de exaustão.
Dois braços de sucção de 3 segmentos (três pistões cada) em torres giratórias, mangueira corrugada pelas juntas;
drone-varredor preso por cabo-mangueira que desce de um carretel no silo por uma lança com polia. Prensa enfardadeira
(sudoeste) solta fardos cintados numa esteira que os expele pela boca de cortinas a leste, caindo num monte fora da
laje. Fios de lama e de cinza flutuam até os bocais puxados pelo campo violeta da IA.

PURIFICADOR DE AR (`purificador_ar`): absorve a poluição do chunk. Plenum com dois ventiladores grandes ao sul
puxando fumaça escura; torre de filtragem com gavetas de filtros plissados enegrecidos de fuligem (uma puxada para
troca) e pilha de filtros saturados num palete ao lado, mais um novo esperando; lavador (coluna de borrifo com visor
mostrando o chuveiro de gotas e a água preta no fundo), tanque e bomba de água, bandeja de decantação da borra; ar
limpo saindo por cima com leve brilho. Toque da IA: cristal violeta num berço de garras à frente dos ventiladores,
que atrai a fuligem do ar em fios.

Uso: blender -b --python estudo_limpeza_2x2.py -- foto [coletor|purificador|ambos]   (ou -- teste ...)"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
EX, EY, EZ = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
sc = None


def nova_cena(seed):
    global sc
    random.seed(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = base3d.iniciar()
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, QUADROS
    base3d.M.clear()


def vazio(nome, pai=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    if pai is not None:
        e.parent = pai
    e.location = loc
    return e


# ================================================================== geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def suave_tudo(o):
    for pg in o.data.polygons:
        pg.use_smooth = True
    return o


def toro(bm, centro, R, r, nR=64, nr=16, eixo=EZ):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + q @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def octo(bm, c, r, z0, z1, r2=None):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0,
                          matrix=Matrix.Translation(Vector(c) + Vector((0, 0, (z0 + z1) / 2))) @ Matrix.Rotation(PI / 8, 4, 'Z'))


def tubo_curvo(bm, pts, raio, lados=16, corrug=0.0, passo=0.02):
    pts = [Vector(p) for p in pts]
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    tot = L[-1]
    n = max(2, int(tot / passo))

    def ponto(s):
        for i in range(len(L) - 1):
            if L[i + 1] >= s:
                f = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
                return pts[i].lerp(pts[i + 1], f)
        return pts[-1]
    P = [ponto(tot * i / n) for i in range(n + 1)]
    aneis, nrm = [], None
    for i, p in enumerate(P):
        t = (P[min(i + 1, n)] - P[max(i - 1, 0)]).normalized()
        if nrm is None:
            nrm = t.orthogonal().normalized()
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        u = i / n
        r = raio(u) if callable(raio) else raio
        if corrug and 0 < i < n:
            r *= (1.0 - corrug * (i % 2))
        aneis.append([bm.verts.new(p + (nrm * math.cos(a) + bi * math.sin(a)) * r)
                      for a in (j * 2 * PI / lados for j in range(lados))])
    for A, B in zip(aneis, aneis[1:]):
        for j in range(lados):
            bm.faces.new((A[j], A[(j + 1) % lados], B[(j + 1) % lados], B[j]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])
    return P


def esfera(bm, c, r, seg=12):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def gota(bm, c, r, achatar=0.45):
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in res['verts']:
        v.co = Vector(c) + Vector((v.co.x * random.uniform(0.8, 1.3), v.co.y * random.uniform(0.8, 1.3), v.co.z * achatar))


def base_ortho(n, up=EZ):
    """Base (t, u, n) para algo colado numa face de normal n; t × u = n."""
    n = Vector(n).normalized()
    u = Vector(up) - n * Vector(up).dot(n)
    if u.length < 1e-4:
        u = EY - n * EY.dot(n)
    u.normalize()
    return u.cross(n), u, n


def rot_de(n, up=EZ):
    t, u, n = base_ortho(n, up)
    return Matrix((t, u, n)).transposed()


def cano(bm, pts, r, lados=18):
    """Cano rígido por pontos, com cotovelo redondo (esfera) em cada canto."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)


def flange(bm, p, eixo, r, esp=0.02, lados=18):
    cil(bm, Vector(p), r, esp, eixo, lados=lados)


def mancha_lisa(bm, c, r, z, seg=40):
    fs = [random.uniform(0, 6) for _ in range(4)]
    vs = []
    for k in range(seg):
        a = k * 2 * PI / seg
        f = 1 + 0.22 * math.sin(2 * a + fs[0]) + 0.14 * math.sin(3 * a + fs[1]) + 0.08 * math.sin(5 * a + fs[2]) + 0.04 * math.sin(9 * a + fs[3])
        vs.append(bm.verts.new((c[0] + math.cos(a) * r * f, c[1] + math.sin(a) * r * f * 0.8, z)))
    bm.faces.new(vs)


# ------------------------------------------------------------------ detalhe rústico (nunca enxuto)
class Decal:
    """Decalques com alfa por ruído (fuligem, ferrugem escorrida, óleo): quads com UV para a borda sumir."""
    def __init__(s, mat):
        s.bm = bmesh.new()
        s.uv = s.bm.loops.layers.uv.new('UVMap')
        s.mat = mat

    def quad(s, p, n, w, h, up=EZ, off=0.0018):
        t, u, n = base_ortho(n, up)
        c = Vector(p) + n * off
        vs = [s.bm.verts.new(c + t * sx * w / 2 + u * sy * h / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = s.bm.faces.new(vs)
        for l, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            l[s.uv].uv = uv

    def cilindro(s, c, r, ang, z0, z1, larg, eixo_z=True, off=0.0025, cols=6):
        """Decalque curvo numa parede cilíndrica vertical (centro c, raio r), centrado no ângulo ang."""
        vs = []
        c = Vector((c[0], c[1], 0))
        for i in range(cols + 1):
            a = ang + (i / cols - 0.5) * larg / r
            d = Vector((math.cos(a), math.sin(a), 0))
            vs.append((s.bm.verts.new(Vector(c) + d * (r + off) + Vector((0, 0, z0))),
                       s.bm.verts.new(Vector(c) + d * (r + off) + Vector((0, 0, z1)))))
        for i in range(cols):
            f = s.bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
            for l, uv in zip(f.loops, ((i / cols, 0), ((i + 1) / cols, 0), ((i + 1) / cols, 1), (i / cols, 1))):
                l[s.uv].uv = uv

    def fim(s, nome):
        return obj(nome, s.bm, s.mat)


SEG7 = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc',
        '8': 'abcdefg', '9': 'abcdfg', '-': 'g', 'I': 'bc', 'L': 'fed', 'P': 'abfge', 'A': 'abcefg', 'C': 'afed',
        'F': 'afeg', 'S': 'afgcd', 'V': 'bcdef', 'E': 'afged', 'D': 'bcdeg', 'T': 'fged'}
SEGP = {'a': (0.5, 1.0, 1), 'd': (0.5, 0.0, 1), 'g': (0.5, 0.5, 1), 'b': (1.0, 0.75, 0), 'c': (1.0, 0.25, 0),
        'e': (0.0, 0.25, 0), 'f': (0.0, 0.75, 0)}


def numero(bm, p, n, texto, alt=0.045, apagar=0.25, up=EZ):
    """Número de série em estêncil, gasto (segmentos faltando)."""
    t, u, n = base_ortho(n, up)
    R = Matrix((t, u, n)).transposed()
    w = alt * 0.5
    x0 = -(len(texto) * w * 1.5) / 2
    for i, ch in enumerate(texto):
        for sg in SEG7.get(ch, ''):
            if random.random() < apagar:
                continue
            cx, cy, horiz = SEGP[sg]
            c = Vector(p) + n * 0.002 + t * (x0 + i * w * 1.5 + cx * w) + u * (cy * alt - alt / 2)
            tam = (w * 0.9, alt * 0.09, 0.002) if horiz else (alt * 0.09, alt * 0.45, 0.002)
            caixa(bm, c, tam, R)


def remendo(bp, bb, p, n, w, h, up=EZ, esp=0.006):
    """Chapa de remendo aparafusada sobre a face (normal n)."""
    t, u, n = base_ortho(n, up)
    R = Matrix((t, u, n)).transposed()
    c = Vector(p) + n * esp / 2
    caixa(bp, c, (w, h, esp), R)
    nx, ny = max(2, int(w / 0.05)), max(2, int(h / 0.05))
    for i in range(nx):
        for j in range(ny):
            if 0 < i < nx - 1 and 0 < j < ny - 1:
                continue
            q = c + t * (-w / 2 + 0.012 + (w - 0.024) * i / (nx - 1)) + u * (-h / 2 + 0.012 + (h - 0.024) * j / (ny - 1))
            cil(bb, q + n * esp / 2, 0.0055, 0.006, n, lados=6)


def chapa_amassada(bm, p, n, w, h, up=EZ, dentes=2, prof=0.012, res=16, off=0.004):
    """Painel com amassados (afunda em direção à parede)."""
    t, u, n = base_ortho(n, up)
    cs = [(random.uniform(-0.3, 0.3) * w, random.uniform(-0.3, 0.3) * h, random.uniform(0.05, 0.12) * max(w, h)) for _ in range(dentes)]
    V = []
    for j in range(res + 1):
        for i in range(res + 1):
            x, y = (i / res - 0.5) * w, (j / res - 0.5) * h
            d = sum(prof * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (s * s)) for cx, cy, s in cs)
            V.append(bm.verts.new(Vector(p) + t * x + u * y + n * (off - min(d, off * 0.9))))
    for j in range(res):
        for i in range(res):
            a = j * (res + 1) + i
            bm.faces.new((V[a], V[a + 1], V[a + res + 2], V[a + res + 1]))


def poeira(bm, x0, x1, y0, y1, z, n, rmin=0.004, rmax=0.012):
    for k in range(n):
        gota(bm, (random.uniform(x0, x1), random.uniform(y0, y1), z), random.uniform(rmin, rmax), 0.22)


def fiacao(bms, p0, p1, cai=0.08, n=5, r=0.0045):
    """Feixe de fios soltos (cores) pendurados entre p0 e p1."""
    p0, p1 = Vector(p0), Vector(p1)
    for k in range(n):
        o = Vector((random.uniform(-0.012, 0.012), random.uniform(-0.012, 0.012), random.uniform(-0.01, 0.01)))
        c = cai * random.uniform(0.7, 1.3)
        mangueira(bms[k % len(bms)], bezier(p0 + o, p0.lerp(p1, 0.3) + o - Vector((0, 0, c)), p0.lerp(p1, 0.7) + o - Vector((0, 0, c)), p1 + o, 10), r)


def escorrido(bm, base, d, z_top, comp, larg):
    n = 6
    for k in range(n):
        f = k / n
        w = larg * (1 - 0.6 * f)
        caixa(bm, base + d * 0.003 + Vector((0, 0, z_top - comp * (f + 0.5 / n))), (0.004, w, comp / n + 0.002), Matrix.Rotation(math.atan2(d.y, d.x), 3, 'Z'))
    gota(bm, base + d * 0.006 + Vector((0, 0, z_top - comp)), larg * 0.7, 1.2)


def tambor(bc, ba, c, r, h, eixo=EZ, faixa=None):
    c = Vector(c)
    e = Vector(eixo).normalized()
    cil(bc, c, r, h, e, lados=28)
    for f in (-0.5, -0.17, 0.17, 0.5):
        cil(ba, c + e * h * f * (0.98 if abs(f) == 0.5 else 1), r + 0.006, 0.014, e, lados=28)
    cil(ba, c + e * (h / 2 + 0.004), r * 0.93, 0.01, e, lados=28)
    cil(ba, c + e * (h / 2 + 0.01) + (e.orthogonal().normalized() * r * 0.55), 0.022, 0.012, e, lados=10)
    if faixa is not None:
        cil(faixa, c, r + 0.003, 0.08, e, lados=28)


def pistao(nome, pai, Lc, Lh, rc=0.03, mat_c='laranja'):
    """Pistão: camisa (origem no olhal, eixo +Z) e haste (origem no olhal da ponta, eixo +Z de volta)."""
    bm = bmesh.new()
    cil(bm, Vector((0, 0, Lc / 2)), rc, Lc, EZ, 18)
    cil(bm, Vector((0, 0, 0.012)), rc + 0.006, 0.024, EZ, 18)
    cil(bm, Vector((0, 0, Lc - 0.012)), rc + 0.006, 0.024, EZ, 18)
    cil(bm, Vector((0, 0, 0)), rc * 0.38, rc * 1.6, EY, 10)
    cil(bm, Vector((rc, 0, Lc * 0.2)), 0.009, 0.022, EX, 8)
    cil(bm, Vector((rc, 0, Lc * 0.85)), 0.009, 0.022, EX, 8)
    camisa = suavizar(obj(nome + '_camisa', bm, mat_c, pai))
    camisa.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, Lh / 2)), rc * 0.48, Lh, EZ, 14)
    cil(bm, Vector((0, 0, 0)), rc * 0.36, rc * 1.6, EY, 10)
    caixa(bm, (0, 0, 0.014), (rc * 0.9, rc * 0.85, 0.028))
    haste = suavizar(obj(nome + '_haste', bm, 'cromo', pai))
    haste.rotation_mode = 'QUATERNION'
    bm = bmesh.new()                                                              # mangueiras hidráulicas nas portas
    for zz in (Lc * 0.2, Lc * 0.85):
        mangueira(bm, bezier((rc + 0.01, 0, zz), (rc + 0.04, 0, zz), (rc + 0.04, 0.03, zz - 0.06), (rc + 0.02, 0.05, zz - 0.12), 8), 0.006)
    obj(nome + '_mang', bm, 'borracha', camisa)
    return camisa, haste


def pistao_por(camisa, haste, A, B, q):
    d = (B - A).normalized()
    camisa.location = A
    camisa.rotation_quaternion = d.to_track_quat('Z', 'Y')
    haste.location = B
    haste.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    for o in (camisa, haste):
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)


# ================================================================== materiais
def emis_mat(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat(nome, cor, transm, rough=0.05):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = 0.25
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.33
    return m


def lama_mat(nome, cor, rough, bump=0.4, escala=18.0, cor2=None):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    cor_m = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor_m.inputs[6].default_value = (*cor, 1)
    c2 = cor2 or (cor[0] * 0.45, cor[1] * 0.45, cor[2] * 0.45)
    cor_m.inputs[7].default_value = (*c2, 1)
    nt.links.new(ru.outputs['Fac'], cor_m.inputs[0])
    nt.links.new(cor_m.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': rough * 0.4, 'To Max': min(1.0, rough * 1.6)})
    nt.links.new(ru.outputs['Fac'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    bp = no(nt, 'ShaderNodeBump', **{'Strength': bump})
    nt.links.new(ru.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def fio_mat(nome, cor, veio=3.0):
    """Fio de sujeira levitando: material da sujeira com veios violeta do campo correndo por dentro."""
    m = lama_mat(nome, cor, 0.3, 0.2)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    v = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.6, 'From Max': 0.72, 'To Min': 0.0, 'To Max': veio})
    nt.links.new(ru.outputs['Fac'], v.inputs['Value'])
    nt.links.new(v.outputs['Result'], b.inputs['Emission Strength'])
    b.inputs['Emission Color'].default_value = (0.55, 0.18, 1.0, 1)
    return m


def campo_mat():
    m = bpy.data.materials.new('Campo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.05, 0.02, 0.1, 1)
    vol.inputs['Emission Color'].default_value = (0.5, 0.16, 1.0, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.2})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = 3.0
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    e.inputs[1].default_value = 6.0
    nt.links.new(mul.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def nuvem_mat(nome, cor, dens, emis=None, forca=0.0, lim=(0.35, 0.7)):
    """Volume em bolha: ruído × queda radial (coordenadas do objeto), sem borda dura. Fumaça, névoa, ar limpo."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.5, 'Detail': 6.0, 'Roughness': 0.6})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    fr = no(nt, 'ShaderNodeMapRange', **{'From Min': lim[0], 'From Max': lim[1]})
    nt.links.new(ru.outputs['Fac'], fr.inputs['Value'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.35})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(fr.outputs['Result'], mul.inputs[0])
    nt.links.new(borda.outputs['Result'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = dens
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    if emis:
        vol.inputs['Emission Color'].default_value = (*emis, 1)
        e = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        e.inputs[1].default_value = forca
        nt.links.new(mul.outputs['Value'], e.inputs[0])
        nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def decal_mat(nome, cor, alfa, escala=7.0, estica=0.25, lim=(0.42, 0.62), rough=0.85, metal=0.0, escorre=True):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    tc = no(nt, 'ShaderNodeTexCoord')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, estica)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': lim[0], 'From Max': lim[1], 'To Min': 0.0, 'To Max': alfa})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    uv = no(nt, 'ShaderNodeUVMap')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs['UV'], sep.inputs[0])

    def mult(a, b_, clamp=False, k=None):
        n = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        n.use_clamp = clamp
        nt.links.new(a, n.inputs[0])
        if k is None:
            nt.links.new(b_, n.inputs[1])
        else:
            n.inputs[1].default_value = k
        return n.outputs[0]

    def sino(s):
        um = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
        um.inputs[0].default_value = 1.0
        nt.links.new(s, um.inputs[1])
        return mult(mult(s, um.outputs[0]), None, True, 9.0)
    e = mult(sino(sep.outputs['X']), sino(sep.outputs['Y']))
    if escorre:
        pw = no(nt, 'ShaderNodeMath', operation='POWER')
        nt.links.new(sep.outputs['Y'], pw.inputs[0])
        pw.inputs[1].default_value = 0.6
        e = mult(e, pw.outputs[0])
    nt.links.new(mult(mr.outputs['Result'], e), b.inputs['Alpha'])
    return m


def chao_mat(cor_suj, cor_suj2, cor_cin, rough_suj=0.18, umido=True):
    """Chão de terra batida: 'sujo' mistura lama/fuligem (com brilho molhado opcional), 'cinza' mistura pó de cinza."""
    m = bpy.data.materials.new('Chão sujo')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    at = no(nt, 'ShaderNodeAttribute', attribute_name='sujo')
    ac = no(nt, 'ShaderNodeAttribute', attribute_name='cinza')
    av = no(nt, 'ShaderNodeAttribute', attribute_name='varrido')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 8.0, 'Roughness': 0.6})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])

    def mascara(attr, a, b_):
        s = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
        nt.links.new(ru.outputs['Fac'], s.inputs[0])
        s.inputs[1].default_value = 0.35
        nt.links.new(attr.outputs['Fac'], s.inputs[2])
        mk = no(nt, 'ShaderNodeMapRange', **{'From Min': a, 'From Max': b_})
        nt.links.new(s.outputs['Value'], mk.inputs['Value'])
        return mk
    mk = mascara(at, 0.62, 0.7)
    mc = mascara(ac, 0.6, 0.74)
    terra = no(nt, 'ShaderNodeMix', data_type='RGBA')
    terra.inputs[6].default_value = (0.33, 0.30, 0.26, 1)
    terra.inputs[7].default_value = (0.24, 0.22, 0.19, 1)
    nt.links.new(ru.outputs['Fac'], terra.inputs[0])
    um = no(nt, 'ShaderNodeMix', data_type='RGBA')
    um.inputs[7].default_value = (0.24, 0.23, 0.215, 1)
    nt.links.new(av.outputs['Fac'], um.inputs[0])
    nt.links.new(terra.outputs[2], um.inputs[6])
    cin = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cin.inputs[7].default_value = (*cor_cin, 1)
    nt.links.new(mc.outputs['Result'], cin.inputs[0])
    nt.links.new(um.outputs[2], cin.inputs[6])
    lama = no(nt, 'ShaderNodeMix', data_type='RGBA')
    lama.inputs[6].default_value = (*cor_suj, 1)
    lama.inputs[7].default_value = (*cor_suj2, 1)
    nt.links.new(fino.outputs['Fac'], lama.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    nt.links.new(mk.outputs['Result'], cor.inputs[0])
    nt.links.new(cin.outputs[2], cor.inputs[6])
    nt.links.new(lama.outputs[2], cor.inputs[7])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.88, 'To Max': rough_suj})
    nt.links.new(mk.outputs['Result'], rg.inputs['Value'])
    rr = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(fino.outputs['Fac'], rr.inputs[0])
    rr.inputs[1].default_value = 0.25
    rv = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(av.outputs['Fac'], rv.inputs[0])
    rv.inputs[1].default_value = -0.3 if umido else 0.0
    nt.links.new(rg.outputs['Result'], rv.inputs[2])
    nt.links.new(rv.outputs['Value'], rr.inputs[2])
    nt.links.new(rr.outputs['Value'], b.inputs['Roughness'])
    h = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(mk.outputs['Result'], h.inputs[0])
    nt.links.new(fino.outputs['Fac'], h.inputs[1])
    h2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(mc.outputs['Result'], h2.inputs[0])
    h2.inputs[1].default_value = 0.6
    nt.links.new(h.outputs['Value'], h2.inputs[2])
    bp = no(nt, 'ShaderNodeBump', **{'Strength': 0.35, 'Distance': 0.01})
    nt.links.new(h2.outputs['Value'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def materiais_comuns():
    base3d.M.update({
        'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=1.0),
        'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.75, sujeira=1.0),
        'silo': mats.material('Silo', (0.16, 0.17, 0.15), 0, 0.55, desgaste=0.8, sujeira=1.0, ferrugem=0.55),
        'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True),
        'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=1.0),
        'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.95, sujeira=0.9),
        'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
        'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.6, pintura=False, sujeira=0.9, desgaste=0.0),
        'tambor': mats.material('Tambor', (0.16, 0.2, 0.13), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
        'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.8, desgaste=0.0),
        'primer': mats.material('Zarcão', (0.32, 0.075, 0.035), 0, 0.6, desgaste=0.7, sujeira=0.9, ferrugem=0.3),
        'galvan': mats.material('Galvanizado', (0.5, 0.51, 0.5), 0.9, 0.55, pintura=False, ferrugem=0.5, sujeira=0.9),
        'stencil': mats.material('Estêncil', (0.62, 0.6, 0.55), 0, 0.6, desgaste=1.0, sujeira=0.7),
        'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
        'vazio': mats.material('Vazio', (0.01, 0.01, 0.012), 0, 0.8, pintura=False, sujeira=0.0, desgaste=0.0),
        'fio_verm': mats.material('Fio vermelho', (0.35, 0.03, 0.02), 0, 0.5, pintura=False, sujeira=0.6, desgaste=0.0),
        'fio_azul': mats.material('Fio azul', (0.03, 0.06, 0.25), 0, 0.5, pintura=False, sujeira=0.6, desgaste=0.0),
        'cobre': mats.material('Cobre', (0.75, 0.38, 0.2), 1.0, 0.35, pintura=False, ferrugem=0.2, sujeira=0.6),
        'vidro': vidro_mat('Vidro', (0.8, 0.82, 0.8), 0.9, 0.04),
        'lama': lama_mat('Lama', (0.12, 0.08, 0.045), 0.25),
        'lama_seca': lama_mat('Lama seca', (0.22, 0.17, 0.11), 0.85, 0.6),
        'campo': campo_mat(),
        'anel_campo': emis_mat('Anel de campo', (0.55, 0.18, 1.0), 10.0, (0.1, 0.04, 0.2)),
        'led': emis_mat('LED', (0.6, 0.2, 1.0), 6.0),
        'led_ambar': emis_mat('LED âmbar', (1.0, 0.45, 0.05), 6.0),
        'led_verm': emis_mat('LED vermelho', (1.0, 0.06, 0.02), 5.0),
        'listras': base3d.listras_mat(),
        'd_fuligem': decal_mat('Fuligem', (0.012, 0.011, 0.01), 0.95, 6.0, 0.35, (0.38, 0.6), 0.9),
        'd_ferrugem': decal_mat('Ferrugem escorrida', (0.28, 0.1, 0.035), 0.9, 9.0, 0.12, (0.45, 0.62), 0.8),
        'd_oleo': decal_mat('Óleo escorrido', (0.01, 0.008, 0.006), 0.95, 8.0, 0.1, (0.48, 0.6), 0.12),
        'd_lama': decal_mat('Lama escorrida', (0.1, 0.07, 0.04), 0.95, 8.0, 0.18, (0.44, 0.6), 0.35),
        'd_poeira': decal_mat('Poeira', (0.36, 0.33, 0.28), 0.8, 10.0, 1.0, (0.4, 0.65), 0.95, escorre=False),
    })


def cena_final(alvo, vistas, nome, perto, extra_perto=None):
    bm = bmesh.new()
    caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
    obj('chao', bm, 'chao_sujo')
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
        pr = bpy.context.preferences.addons['cycles'].preferences
        pr.compute_device_type = 'OPTIX'
        pr.get_devices()
        for dv in pr.devices:
            dv.use = True
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.cycles.volume_bounces = 1
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -0.5
    cam_d = bpy.data.cameras.new('Cam')
    cam = bpy.data.objects.new('Cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam

    def mirar(pos, alv, lente):
        cam.location = pos
        cam.rotation_euler = (Vector(alv) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        cam_d.lens = lente
    modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
    sc.frame_set(int(QUADROS * 0.12) + 1)
    teste = modo == 'teste'
    sc.cycles.samples = 24 if teste else 160
    esc = 0.5 if teste else 1.0
    suf = '_teste' if teste else ''
    sc.render.resolution_x, sc.render.resolution_y = int(1100 * esc), int(1300 * esc)
    for i, (ang, dist, alt, lente) in enumerate(vistas):
        a = math.radians(ang)
        mirar(Vector(alvo) + Vector((math.cos(a) * dist, math.sin(a) * dist, alt)), alvo, lente)
        sc.render.filepath = os.path.join(AQUI, '%s%s_%d.png' % (nome, suf, i))
        bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = int(1300 * esc), int(1000 * esc)
    for sfx, (pos, alv, lente) in (('perto', perto),) + ((('perto2', extra_perto),) if extra_perto else ()):
        mirar(pos, alv, lente)
        sc.render.filepath = os.path.join(AQUI, '%s%s_%s.png' % (nome, suf, sfx))
        bpy.ops.render.render(write_still=True)


def linear_keys():
    for o in list(sc.objects) + list(bpy.data.materials):
        ad = getattr(o, 'animation_data', None)
        if isinstance(o, bpy.types.Material) and o.node_tree:
            ad = o.node_tree.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, 'fcurves', []):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'


def sst(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def chao_grade(func, ext=3.4, passo=0.03):
    bm = bmesh.new()
    N = int(2 * ext / passo)
    V, SUJ, CIN, VAR = [], [], [], []
    for j in range(N + 1):
        for i in range(N + 1):
            x, y = -ext + i * passo, -ext + j * passo
            s, c, v = func(x, y) if max(abs(x), abs(y)) > 0.98 else (0.0, 0.0, 0.0)
            SUJ.append(s)
            CIN.append(c)
            VAR.append(v)
            V.append(bm.verts.new((x, y, 0.001 + 0.007 * max(s, c * 0.6))))
    for j in range(N):
        for i in range(N):
            a = j * (N + 1) + i
            bm.faces.new((V[a], V[a + 1], V[a + N + 2], V[a + N + 1]))
    o = obj('chao_sujeira', bm, 'chao_sujo')
    for nome, vals in (('sujo', SUJ), ('cinza', CIN), ('varrido', VAR)):
        at = o.data.attributes.new(nome, 'FLOAT', 'POINT')
        at.data.foreach_set('value', vals)
    for pg in o.data.polygons:
        pg.use_smooth = True
    return o


def laje(bp=None):
    bm = bmesh.new()
    caixa_de(bm, (-1.0, -1.0, 0), (1.0, 1.0, 0.08))
    obj('laje', bm, 'concreto')
    bm = bmesh.new()
    caixa_de(bm, (-1.005, -1.005, 0.0), (1.005, -0.985, 0.08))
    caixa_de(bm, (-1.005, 0.985, 0.0), (1.005, 1.005, 0.08))
    obj('laje_listras', bm, 'listras')
    bm = bmesh.new()                                                              # trincas e lascas na borda da laje
    for k in range(10):
        x = random.uniform(-0.95, 0.95)
        s = random.choice((-1, 1))
        caixa(bm, (x, s * 1.0, 0.07), (random.uniform(0.03, 0.08), 0.03, 0.025), Matrix.Rotation(random.uniform(-0.3, 0.3), 3, 'Z'))
    obj('laje_lascas', bm, 'vazio')


# ================================================================== COLETOR DE LIXO 2
def coletor_lixo_2():
    nova_cena(31)
    materiais_comuns()
    base3d.M.update({
        'laranja': mats.material('Laranja nível 2', (0.55, 0.15, 0.025), 0, 0.45, desgaste=0.95, sujeira=1.0, ferrugem=0.2),
        'sedimento': lama_mat('Sedimento', (0.08, 0.075, 0.07), 0.7),
        'lodo': lama_mat('Lodo', (0.17, 0.10, 0.04), 0.35),
        'cinza': lama_mat('Cinza', (0.36, 0.35, 0.34), 0.95, 0.5, 30.0, (0.16, 0.155, 0.15)),
        'fardo': lama_mat('Fardo', (0.045, 0.035, 0.025), 0.7, 1.6, 45.0, (0.13, 0.12, 0.11)),
        'fio_lama': fio_mat('Fio de lama', (0.10, 0.065, 0.035)),
        'fio_cinza': fio_mat('Fio de cinza', (0.3, 0.29, 0.28), 2.0),
        'v_lodo': emis_mat('Visor lodo', (0.3, 0.16, 0.05), 0.8, (0.2, 0.11, 0.04)),
        'v_agua': emis_mat('Visor água', (0.2, 0.25, 0.08), 1.0, (0.12, 0.15, 0.05)),
        'v_espuma': emis_mat('Visor espuma', (0.4, 0.34, 0.22), 0.6, (0.35, 0.3, 0.2)),
        'v_sedimento': emis_mat('Visor sedimento', (0.1, 0.09, 0.08), 0.5, (0.09, 0.085, 0.08)),
        'v_cinza': emis_mat('Visor cinza', (0.42, 0.42, 0.42), 0.7, (0.4, 0.4, 0.4)),
        'v_cinza_esc': emis_mat('Visor cinza escura', (0.18, 0.18, 0.18), 0.6, (0.16, 0.16, 0.16)),
        'v_carvao': emis_mat('Visor carvão', (0.05, 0.05, 0.05), 0.4, (0.04, 0.04, 0.04)),
        'v_po': emis_mat('Visor pó', (0.55, 0.55, 0.56), 0.9, (0.5, 0.5, 0.5)),
        'vapor': base3d.volume_mat('Vapor', (0.92, 0.92, 0.94), 5.0, 2.25, 3.1),
        'poeira_cinza': nuvem_mat('Poeira de cinza', (0.5, 0.5, 0.5), 2.0),
        'chao_sujo': chao_mat((0.11, 0.075, 0.04), (0.05, 0.035, 0.02), (0.38, 0.37, 0.36)),
    })
    dfu, dfe, dol, dla, dpo = (Decal(m) for m in ('d_fuligem', 'd_ferrugem', 'd_oleo', 'd_lama', 'd_poeira'))
    B_REM, B_REMP, B_TROCA, B_PAR, B_NUM, B_AMAS = (bmesh.new() for _ in range(6))
    laje()

    C = Vector((0.0, 0.15, 0.0))           # centro do silo
    R_SILO = 0.44
    AP = R_SILO * math.cos(PI / 8)
    Z_SILO, Z_TETO = 1.05, 1.15
    P = 1.1
    TORRES = ((1, Vector((0.72, 0.45, 0))), (-1, Vector((-0.72, 0.45, 0))))

    # ------------------------------------------------------------------ silo de duas câmaras
    bm = bmesh.new()
    octo(bm, C, R_SILO, 0.08, Z_SILO)
    obj('silo', bm, 'silo')
    bm = bmesh.new()
    octo(bm, C, R_SILO + 0.02, 0.08, 0.16)
    octo(bm, C, R_SILO + 0.012, 0.18, 0.22)
    octo(bm, C, R_SILO + 0.012, 0.96, 1.0)
    octo(bm, C, R_SILO + 0.015, Z_SILO - 0.01, Z_SILO + 0.02)
    obj('silo_cintas', bm, 'laranja')
    bm = bmesh.new()
    octo(bm, C, R_SILO, Z_SILO, Z_TETO, r2=0.32)
    octo(bm, C, 0.33, Z_TETO, Z_TETO + 0.02)
    obj('silo_teto', bm, 'silo')
    bm, br = bmesh.new(), bmesh.new()
    for k in range(8):
        a = PI / 8 + k * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(bm, C + d * (R_SILO + 0.008) + Vector((0, 0, 0.58)), (0.03, 0.03, 0.92), Matrix.Rotation(a, 3, 'Z'))
    for k in range(8):
        a = k * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        for z in (0.2, 0.98):
            for j in (-2, -1, 1, 2):
                cil(br, C + d * (AP + 0.022) + t * j * 0.07 + Vector((0, 0, z)), 0.007, 0.01, d, lados=6)
    obj('silo_nervuras', bm, 'grafite')
    obj('silo_rebites', br, 'aco')

    # visores nas faces diagonais SO (lodo) e SE (cinza): construídos no quadro da face (normal −Y) e girados
    def visor(nome, ang, camadas, mats_v, bolhas):
        pai = vazio('visor_' + nome, None, C)
        pai.rotation_euler = (0, 0, ang + PI / 2)
        YV = -AP
        bm = bmesh.new()
        for sx in (-1, 1):
            caixa_de(bm, (sx * 0.1, YV - 0.045, 0.28), (sx * 0.128, YV + 0.002, 0.92))
        for z in (0.28, 0.9):
            caixa_de(bm, (-0.128, YV - 0.045, z), (0.128, YV + 0.002, z + 0.022))
        obj('visor_moldura', bm, 'ferro', pai)
        bm = bmesh.new()
        for z in (0.29, 0.45, 0.6, 0.75, 0.91):
            for sx in (-1, 1):
                cil(bm, Vector((sx * 0.114, YV - 0.047, z)), 0.008, 0.008, -EY, lados=6)
        obj('visor_parafusos', bm, 'aco', pai)
        z_baixo = lambda x: 0.30
        for mat, zt in camadas:
            bm = bmesh.new()
            fase = random.uniform(0, 6)
            amp = 0.0 if mat == 'vazio' else 0.008
            z_cima = (lambda zt, fase, amp: (lambda x: zt + amp * math.sin(x * 38 + fase) + amp * 0.5 * math.sin(x * 91 + fase * 2)))(zt, fase, amp)
            xs = [-0.1 + 0.2 * i / 24 for i in range(25)]
            baixo = [bm.verts.new((x, YV - 0.012, z_baixo(x))) for x in xs]
            cima = [bm.verts.new((x, YV - 0.012, z_cima(x))) for x in xs]
            for i in range(24):
                bm.faces.new((baixo[i], baixo[i + 1], cima[i + 1], cima[i]))
            obj('visor_camada', bm, mats_v.get(mat, mat), pai)
            z_baixo = z_cima
        bm = bmesh.new()
        for zr, mt in bolhas:
            for k in range(12):
                gota(bm, (random.uniform(-0.09, 0.09), YV - 0.02, random.uniform(*zr)), random.uniform(0.004, 0.009), 0.8)
        obj('visor_grumos', bm, mt, pai)
        bm = bmesh.new()
        caixa_de(bm, (-0.1, YV - 0.034, 0.3), (0.1, YV - 0.03, 0.9))
        obj('visor_vidro', bm, 'vidro', pai)
        bm, bl, ba = bmesh.new(), bmesh.new(), bmesh.new()
        caixa_de(bm, (0.14, YV - 0.012, 0.3), (0.162, YV + 0.002, 0.9))
        for k in range(12):
            z = 0.32 + k * 0.05
            caixa_de(bl if z < camadas[-2][1] else ba, (0.145, YV - 0.015, z), (0.157, YV - 0.011, z + 0.022))
        obj('regua', bm, 'grafite', pai)
        obj('regua_leds', bl, 'led', pai)
        obj('regua_apagada', ba, 'vazio', pai)
        bm = bmesh.new()                                                          # vidro sujo: escorridos de dentro
        for k in range(5):
            escorrido(bm, Vector((random.uniform(-0.08, 0.08), YV - 0.045, 0)), -EY, 0.28, random.uniform(0.05, 0.14), random.uniform(0.01, 0.02))
        obj('visor_escorridos', bm, 'lama' if nome == 'lodo' else 'cinza', pai)
        return pai
    visor('lodo', -3 * PI / 4, (('sedimento', 0.43), ('lodo', 0.6), ('oleo', 0.64), ('agua_lodo', 0.76), ('espuma', 0.8), ('vazio', 0.902)),
          {'lodo': 'v_lodo', 'agua_lodo': 'v_agua', 'espuma': 'v_espuma', 'sedimento': 'v_sedimento'}, [((0.44, 0.58), 'lodo')])
    visor('cinza', -PI / 4, (('v_carvao', 0.38), ('v_cinza_esc', 0.5), ('v_cinza', 0.62), ('v_carvao', 0.65), ('v_cinza', 0.74), ('v_po', 0.79), ('vazio', 0.902)),
          {}, [((0.4, 0.7), 'sedimento')])

    # marca do nível 2 (duas faixas e "II") nas faces leste e oeste, número de série gasto
    for lado in (1, -1):
        d = Vector((lado, 0, 0))
        p = C + d * (AP + 0.001)
        for j, z in enumerate((0.78, 0.84)):
            caixa(B_NUM, p + Vector((0, -0.1 * lado, z)), (0.004, 0.12, 0.03))
        numero(B_NUM, p + Vector((0, 0.06 * lado, 0.81)), d, 'II', 0.09, 0.0)
        numero(B_NUM, p + Vector((0, 0.0, 0.38)), d, '2-7140' if lado > 0 else '2-0913', 0.04, 0.3)
    remendo(B_REM, B_PAR, C + Vector((0, AP, 0.55)), EY, 0.18, 0.24)                    # remendo na face norte
    remendo(B_REMP, B_PAR, C + Vector((-AP * 0.707, AP * 0.707, 0.62)), Vector((-1, 1, 0)), 0.14, 0.16)
    chapa_amassada(B_AMAS, C + Vector((AP * 0.707, AP * 0.707, 0.5)), Vector((1, 1, 0)), 0.26, 0.5, dentes=3, prof=0.02)
    for k in range(8):                                                          # ferrugem e lama escorrendo pelas faces
        a = k * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        if k in (5, 7):
            dla.quad(C + d * AP + t * 0.13 * random.choice((-1, 1)) + Vector((0, 0, 0.6)), d, 0.06, 0.6)
            continue
        dfe.quad(C + d * AP + t * random.uniform(-0.1, 0.1) + Vector((0, 0, 0.62)), d, 0.1, random.uniform(0.3, 0.6))
        dla.quad(C + d * AP + t * random.uniform(-0.1, 0.1) + Vector((0, 0, 0.25)), d, 0.2, 0.22, up=-EZ)
    bm = bmesh.new()
    for k in range(18):
        f = random.choice((0, 1, 2, 3, 4, 6))
        a = f * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        escorrido(bm, C + d * AP + t * random.uniform(-0.14, 0.14), d, Z_SILO - 0.01, random.uniform(0.12, 0.45), random.uniform(0.012, 0.028))
    obj('silo_escorridos', bm, 'lama')

    # ------------------------------------------------------------------ separador DUPLO em série no teto
    def ciclone(c, r, zc0, zb0, zb1, nome, carga):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.05, radius2=r, depth=zb0 - zc0,
                              matrix=Matrix.Translation(Vector(c) + Vector((0, 0, (zc0 + zb0) / 2))))
        cil(bm, Vector(c) + Vector((0, 0, (zb0 + zb1) / 2)), r, zb1 - zb0, lados=32)
        suavizar(obj('ciclone_' + nome, bm, 'aco'))
        bm = bmesh.new()
        for z in (zb0, zb1 - 0.005):
            cil(bm, Vector(c) + Vector((0, 0, z)), r + 0.014, 0.022, lados=32)
        cil(bm, Vector(c) + Vector((0, 0, zc0 + 0.005)), 0.065, 0.02, lados=20)
        obj('ciclone_flanges_' + nome, bm, 'ferro')
        bm = bmesh.new()                                                          # eclusa rotativa + motor
        caixa_de(bm, Vector(c) + Vector((-0.06, -0.06, Z_TETO + 0.02)), Vector(c) + Vector((0.06, 0.06, zc0 - 0.005)))
        cil(bm, Vector(c) + Vector((0, -0.085, (Z_TETO + zc0) / 2 + 0.01)), 0.035, 0.05, EY, lados=14)
        for j in range(4):
            cil(bm, Vector(c) + Vector((0, -0.065 - j * 0.01, (Z_TETO + zc0) / 2 + 0.01)), 0.042, 0.004, EY, lados=14)
        obj('eclusa_' + nome, bm, 'grafite')
        bm = bmesh.new()
        for k in range(3):                                                        # pernas no teto
            a = PI / 2 + k * 2 * PI / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            pe = Vector(c) + d * (r + 0.05)
            pe = Vector((pe.x, pe.y, Z_TETO - 0.02 + 0.0))
            if (pe.xy - C.xy).length > 0.3:
                pe.z = Z_TETO - (Z_TETO - Z_SILO) * ((pe.xy - C.xy).length - 0.3) / (R_SILO - 0.3) + 0.0
            viga(bm, pe, Vector(c) + d * (r + 0.005) + Vector((0, 0, zb0 + 0.02)), 0.022)
            caixa(bm, pe + Vector((0, 0, 0.006)), (0.05, 0.05, 0.012))
        obj('ciclone_pernas_' + nome, bm, 'laranja')
        dfe.cilindro(c, r, -PI / 2 + random.uniform(-0.4, 0.4), zb0 + 0.02, zb1 - 0.02, 0.1)
        dfe.cilindro(c, r, PI / 4, zb0 + 0.05, zb1 - 0.05, 0.08)
        bm = bmesh.new()                                                          # transbordo em volta da eclusa
        gota(bm, Vector(c) + Vector((0, 0, Z_TETO + 0.02)), 0.09, 0.22)
        for k in range(5):
            a = random.uniform(0, 2 * PI)
            gota(bm, Vector(c) + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, Z_TETO + 0.012)), random.uniform(0.015, 0.035), 0.3)
        obj('transbordo_' + nome, bm, carga)
    LC, RL = Vector((-0.17, 0.15, 0)), 0.14
    CC, RC = Vector((0.2, 0.15, 0)), 0.12
    ciclone(LC, RL, 1.22, 1.36, 1.66, 'lama', 'lama')
    ciclone(CC, RC, 1.22, 1.34, 1.72, 'cinza', 'cinza')
    numero(B_NUM, LC + Vector((0, -RL - 0.001, 1.52)), -EY, '1', 0.07, 0.0)
    numero(B_NUM, CC + Vector((0, -RC - 0.001, 1.55)), -EY, '2', 0.07, 0.0)
    bm = bmesh.new()
    cil(bm, LC + Vector((0, 0, 1.74)), 0.05, 0.16, lados=20)                     # saída de vórtice da lama
    suavizar(obj('vortice_lama', bm, 'aco'))
    bm = bmesh.new()                                                              # cruzamento lama → cinza (pescoço de ganso)
    X1 = Vector((-0.01, 0.07, 0))
    cano(bm, [LC + Vector((0, 0, 1.8)), LC + Vector((0, 0, 1.92)), X1 + Vector((0, 0, 1.92)), X1 + Vector((0, 0, 1.6)), Vector((0.1, 0.07, 1.6))], 0.04)
    suavizar(obj('cano_cruzamento', bm, 'casco'))
    bm = bmesh.new()
    caixa_de(bm, (0.06, 0.03, 1.55), (0.14, 0.11, 1.65))                          # entrada tangencial do ciclone de cinza
    caixa_de(bm, (-0.115, 0.27, 1.5), (-0.025, 0.39, 1.62))                      # entrada tangencial do ciclone de lama
    caixa_de(bm, (-0.27, 0.38, 1.49), (0.06, 0.52, 1.63))                        # coletor de entrada (os dois braços)
    obj('entradas', bm, 'aco')
    bm = bmesh.new()
    flange(bm, LC + Vector((0, 0, 1.8)), EZ, 0.058)
    flange(bm, X1 + Vector((0, 0, 1.75)), EZ, 0.055)
    flange(bm, Vector((0.055, 0.07, 1.6)), EX, 0.055)
    for x in (-0.27, 0.06):
        caixa_de(bm, (x - 0.008, 0.37, 1.48), (x + 0.008, 0.53, 1.64))
    obj('cruzamento_flanges', bm, 'ferro')
    bm = bmesh.new()                                                              # filtro de cartuchos sobre o ciclone de cinza
    caixa_de(bm, (0.07, 0.02, 1.78), (0.33, 0.28, 1.95))
    obj('filtro', bm, 'grafite')
    bm = bmesh.new()
    for s in (-1, 1):
        x = 0.2 + s * 0.13
        for k in range(11):
            y = 0.04 + k * 0.021
            caixa_de(bm, (min(x, x + s * 0.012), y - 0.004, 1.8), (max(x, x + s * 0.012), y + 0.004, 1.93))
    obj('filtro_pregas', bm, 'cinza')
    bm = bmesh.new()
    cil(bm, CC + Vector((0, 0, 1.75)), 0.05, 0.07, lados=20)
    obj('vortice_cinza', bm, 'aco')
    bm = bmesh.new()                                                              # turbina de exaustão
    T0 = CC + Vector((0, 0, 2.03))
    bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.13, radius2=0.13, depth=0.15, matrix=Matrix.Translation(T0))
    bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.118, radius2=0.118, depth=0.15, matrix=Matrix.Translation(T0))
    suavizar(obj('turbina_casco', bm, 'casco'))
    bm = bmesh.new()
    toro(bm, T0 + Vector((0, 0, 0.075)), 0.124, 0.01, 48, 10)
    toro(bm, T0 - Vector((0, 0, 0.07)), 0.128, 0.01, 48, 10)
    for k in range(3):
        a = k * 2 * PI / 3
        viga(bm, T0 - Vector((0, 0, 0.06)), T0 + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, -0.06)), 0.012)
    for k in range(5):
        a = k * PI / 5
        viga(bm, T0 + Vector((-math.cos(a) * 0.122, -math.sin(a) * 0.122, 0.08)), T0 + Vector((math.cos(a) * 0.122, math.sin(a) * 0.122, 0.08)), 0.007)
    caixa_de(bm, (0.06, 0.0, 1.95), (0.34, 0.3, 1.965))
    obj('turbina_aros', bm, 'ferro')
    rotor = vazio('rotor', None, T0 + Vector((0, 0, 0.01)))
    bm = bmesh.new()
    esfera(bm, (0, 0, 0), 0.03, 14)
    for k in range(7):
        a = k * 2 * PI / 7
        caixa(bm, Matrix.Rotation(a, 3, 'Z') @ Vector((0.07, 0, 0)), (0.085, 0.035, 0.005), Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(0.5, 3, 'X'))
    obj('rotor_pas', bm, 'aco', rotor)
    dfu.quad(T0 + Vector((0, -0.131, 0.0)), -EY, 0.12, 0.14, off=0.002)
    dfu.quad(T0 + Vector((0.131, 0, 0.0)), EX, 0.12, 0.14, off=0.002)
    remendo(B_TROCA, B_PAR, Vector((0.2, 0.019, 1.865)), -EY, 0.16, 0.1)         # tampa do filtro trocada (amarela, nível 1)
    numero(B_NUM, Vector((0.2, 0.012, 1.87)), -EY, '07', 0.04, 0.3)
    dpo.quad(Vector((0.2, 0.15, 1.951)), EZ, 0.26, 0.26, up=EY)

    # ------------------------------------------------------------------ torres e braços de 3 segmentos
    BRACOS = []
    S1 = Vector((0.38, 0, 0.22))         # junta 2 (no quadro do seg. 1)
    S2 = Vector((0.5, 0, -0.12))         # junta 3 (no quadro do seg. 2)
    S3 = Vector((0.2, 0, -0.82))         # ponta do seg. 3
    BOCA = S3 + Vector((0.12, 0, -0.18))
    for lado, T in TORRES:
        bm = bmesh.new()
        cil(bm, T + Vector((0, 0, 0.115)), 0.16, 0.07, lados=28)
        caixa(bm, T + Vector((-lado * 0.12, -0.14, 0.13)), (0.08, 0.06, 0.1))
        obj('torre_base', bm, 'grafite')
        bm = bmesh.new()
        for k in range(16):
            a = k * 2 * PI / 16
            if k % 5 == 3:
                continue                                                         # parafuso faltando
            cil(bm, T + Vector((math.cos(a) * 0.145, math.sin(a) * 0.145, 0.155)), 0.008, 0.012, lados=6)
        obj('torre_parafusos', bm, 'aco')
        dol.quad(T + Vector((-lado * 0.16, -0.14, 0.16)), Vector((-lado, 0, 0)), 0.07, 0.12)
        giro = vazio('giro', None, T)
        giro.rotation_euler = (0, 0, 0 if lado > 0 else PI)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.185)), 0.135, 0.05, lados=28)
        obj('torre_colar', bm, 'laranja', giro)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, (0.21 + P - 0.1) / 2)), 0.07, P - 0.1 - 0.21, lados=20)
        suavizar(obj('torre_coluna', bm, 'laranja', giro))
        bm = bmesh.new()
        for sy in (-1, 1):
            caixa_de(bm, (-0.06, sy * 0.05, P - 0.11), (0.06, sy * 0.07, P + 0.07))
        caixa_de(bm, (-0.06, -0.07, P + 0.07), (0.06, 0.07, P + 0.09))
        caixa_de(bm, (0.065, -0.03, 0.56), (0.12, 0.03, 0.64))
        for sy in (-1, 1):
            caixa_de(bm, (0.09, sy * 0.022 - 0.006, 0.6), (0.13, sy * 0.022 + 0.006, 0.66))
        caixa_de(bm, (-0.115, -0.05, 0.42), (-0.07, 0.05, 0.56))
        obj('torre_garfo', bm, 'grafite', giro)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, P)), 0.022, 0.17, EY, lados=12)
        cil(bm, Vector((0, 0, P + 0.165)), 0.07, 0.15, lados=20)
        cil(bm, Vector((0.075, 0, P + 0.16)), 0.05, 0.05, EX, lados=16)
        obj('junta_rotativa', bm, 'aco', giro)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, P + 0.1)), 0.082, 0.02, lados=20)
        cil(bm, Vector((0, 0, P + 0.235)), 0.082, 0.02, lados=20)
        cil(bm, Vector((0.1, 0, P + 0.16)), 0.068, 0.018, EX, lados=16)
        obj('junta_flanges', bm, 'ferro', giro)
        bm = bmesh.new()
        mangueira(bm, bezier((-0.07, 0.03, 0.5), (0.0, 0.09, 0.52), (0.07, 0.07, 0.6), (0.1, 0.035, 0.63), 10), 0.009)
        mangueira(bm, bezier((-0.07, -0.03, 0.47), (0.02, -0.12, 0.45), (0.1, -0.12, 0.75), (0.13, -0.045, 0.9), 12), 0.009)
        obj('torre_hidraulica', bm, 'borracha', giro)
        bt = bmesh.new()                                                         # remendo trocado na coluna (amarelo do nível 1)
        caixa(bt, Vector((-0.072, 0, 0.75)), (0.012, 0.09, 0.16))
        obj('torre_remendo', bt, 'amarelo', giro)
        bm = bmesh.new()
        for z in (0.69, 0.81):
            for y in (-0.035, 0.035):
                cil(bm, Vector((-0.08, y, z)), 0.006, 0.008, -EX, lados=6)
        obj('torre_remendo_paraf', bm, 'aco', giro)
        bm = bmesh.new()
        numero(bm, Vector((0, -0.071, 0.35)), -EY, '2-%d' % random.randint(100, 999), 0.035, 0.3)
        obj('torre_num', bm, 'stencil', giro)

        # ---- segmento 1 (lança)
        def lug(bm, a, b, pino, w):
            """Orelha soldada: do ponto da viga a→b mais próximo do pino até o pino."""
            ab = b - a
            t = max(0.0, min(1.0, (pino - a).dot(ab) / ab.length_squared))
            viga(bm, a + ab * t, pino, w)
        OY = EY * 0.1                                                             # canos correm ao lado da viga
        seg1 = vazio('seg1', giro, (0, 0, P))
        bm = bmesh.new()
        viga(bm, Vector((-0.03, 0, -0.006)), S1, 0.07)
        cil(bm, Vector((0, 0, 0)), 0.045, 0.095, EY, lados=16)
        lug(bm, Vector((0, 0, 0)), S1, Vector((0.2, 0, -0.045)), 0.045)            # olhal do pistão A (sob a lança)
        lug(bm, Vector((0, 0, 0)), S1, Vector((0.08, 0, 0.16)), 0.045)             # olhal do pistão B (sobre a lança)
        obj('seg1', bm, 'laranja', seg1)
        bm = bmesh.new()
        for sy in (-1, 1):
            caixa(bm, S1 + Vector((0, sy * 0.04, 0)), (0.13, 0.012, 0.12), Matrix.Rotation(-0.3, 3, 'Y'))
        cil(bm, S1, 0.02, 0.105, EY, lados=12)
        cil(bm, Vector((0.2, 0, -0.045)), 0.012, 0.075, EY, lados=10)
        cil(bm, Vector((0.08, 0, 0.16)), 0.012, 0.075, EY, lados=10)
        obj('seg1_juntas', bm, 'grafite', seg1)
        # ---- segmento 2
        seg2 = vazio('seg2', seg1, S1)
        bm = bmesh.new()
        viga(bm, Vector((-0.02, 0, 0.005)), S2, 0.06)
        cil(bm, Vector((0, 0, 0)), 0.04, 0.07, EY, lados=16)
        lug(bm, Vector((0, 0, 0)), S2, Vector((0.15, 0, 0.14)), 0.04)              # olhal da haste B
        lug(bm, Vector((0, 0, 0)), S2, Vector((0.14, 0, -0.075)), 0.04)            # olhal da camisa C (embaixo)
        obj('seg2', bm, 'laranja', seg2)
        bm = bmesh.new()
        for sy in (-1, 1):
            caixa(bm, S2 + Vector((0, sy * 0.036, 0)), (0.11, 0.012, 0.11))
        cil(bm, S2, 0.018, 0.095, EY, lados=12)
        cil(bm, Vector((0.15, 0, 0.14)), 0.011, 0.06, EY, lados=10)
        cil(bm, Vector((0.14, 0, -0.075)), 0.011, 0.06, EY, lados=10)
        obj('seg2_juntas', bm, 'grafite', seg2)
        # ---- segmento 3 (desce até o bocal)
        seg3 = vazio('seg3', seg2, S2)
        bm = bmesh.new()
        viga(bm, Vector((0, 0, 0.02)), S3, 0.055)
        cil(bm, Vector((0, 0, 0)), 0.036, 0.06, EY, lados=16)
        viga(bm, Vector((0, 0, -0.03)), Vector((-0.07, 0, -0.07)), 0.03)           # chifre do pistão C
        caixa_de(bm, S3 + Vector((-0.03, -0.035, -0.06)), S3 + Vector((0.07, 0.035, 0.02)))
        obj('seg3', bm, 'laranja', seg3)
        bm = bmesh.new()
        cil(bm, Vector((-0.07, 0, -0.07)), 0.011, 0.055, EY, lados=10)
        for sy in (-1, 1):
            caixa(bm, Vector((-0.07, sy * 0.022, -0.07)), (0.04, 0.008, 0.04))
        obj('seg3_juntas', bm, 'grafite', seg3)
        bm, ba = bmesh.new(), bmesh.new()                                         # canos rígidos ao lado dos seg. 1 e 2
        d1 = S1.normalized()
        P1a, P1b = d1 * 0.3 + OY, S1 - d1 * 0.06 + OY
        tubo(bm, P1a, P1b, 0.045, 18)
        for t in (0.45, 0.85):
            p = d1 * (S1.length * t)
            viga(ba, p + EY * 0.03, p + EY * 0.06, 0.02)
            cil(ba, p + OY, 0.052, 0.018, d1, lados=18)
        cil(ba, P1a + d1 * 0.01, 0.055, 0.02, d1, lados=18)
        suavizar(obj('cano_seg1', bm, 'casco', seg1))
        obj('cano_seg1_abr', ba, 'ferro', seg1)
        bm, ba = bmesh.new(), bmesh.new()
        d2 = S2.normalized()
        P2a, P2b = d2 * 0.08 + OY, S2 - d2 * 0.07 + OY
        tubo(bm, P2a, P2b, 0.042, 18)
        for t in (0.3, 0.75):
            p = d2 * (S2.length * t)
            viga(ba, p + EY * 0.028, p + EY * 0.06, 0.018)
            cil(ba, p + OY, 0.05, 0.018, d2, lados=18)
        suavizar(obj('cano_seg2', bm, 'casco', seg2))
        obj('cano_seg2_abr', ba, 'ferro', seg2)
        bm = bmesh.new()                                                          # mangueiras corrugadas nas juntas
        J0 = Vector((0.125, 0, 0.16))
        tubo_curvo(bm, bezier(J0, J0 + Vector((0.09, 0, 0.0)), P1a - d1 * 0.1, P1a, 20), 0.05, 16, corrug=0.13, passo=0.014)
        suavizar(obj('mang_j1', bm, 'borracha', seg1))
        bm = bmesh.new()
        A2s = P1b - S1                                                             # no quadro do seg. 2
        tubo_curvo(bm, bezier(A2s, A2s + d1 * 0.1 + EY * 0.04, P2a - d2 * 0.1 + EY * 0.04, P2a, 20), 0.046, 16, corrug=0.13, passo=0.014)
        suavizar(obj('mang_j2', bm, 'borracha', seg2))
        bm = bmesh.new()
        A3s = P2b - S2                                                             # no quadro do seg. 3
        TOPO = BOCA + Vector((0, 0, 0.16))
        pts = bezier(A3s, A3s + d2 * 0.16, Vector((0.2, 0.08, -0.08)), Vector((0.17, 0.03, -0.32)), 24)
        pts += bezier(Vector((0.17, 0.03, -0.32)), Vector((0.14, 0.0, -0.55)), TOPO + Vector((-0.01, 0, 0.3)), TOPO, 26)[1:]
        tubo_curvo(bm, pts, 0.05, 16, corrug=0.13, passo=0.014)
        suavizar(obj('mang_j3', bm, 'borracha', seg3))
        bm, ba = bmesh.new(), bmesh.new()
        for zt in (-0.3, -0.58):                                                  # abraçadeiras: viga → anel na mangueira
            i = min(range(len(pts)), key=lambda j: abs(pts[j].z - zt))
            al = pts[i]
            tg = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
            toro(ba, al, 0.054, 0.008, 24, 6, eixo=tg)
            t = (al.z - 0.02) / (S3.z - 0.02)
            pb = Vector((0, 0, 0.02)).lerp(S3, t)
            viga(bm, pb, al + (pb - al).normalized() * 0.055, 0.02)
        obj('seg3_abr', bm, 'grafite', seg3)
        obj('mang_abr', ba, 'aco', seg3)
        bm = bmesh.new()                                                          # bocal de sucção
        bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.18, radius2=0.075, depth=0.13,
                              matrix=Matrix.Translation(BOCA + Vector((0, 0, 0.065))))
        cil(bm, BOCA + Vector((0, 0, 0.145)), 0.075, 0.035, lados=20)
        suavizar(obj('bocal', bm, 'casco', seg3))
        bm = bmesh.new()
        cil(bm, BOCA + Vector((0, 0, 0.165)), 0.085, 0.016, lados=20)
        for k in range(6):
            a = k * PI / 3
            d = Vector((math.cos(a), math.sin(a), 0))
            viga(bm, BOCA + d * 0.175 + Vector((0, 0, 0.005)), BOCA + d * 0.08 + Vector((0, 0, 0.125)), 0.014)
        toro(bm, BOCA + Vector((0, 0, 0.01)), 0.186, 0.009, 48, 8)               # saia de borracha gasta
        obj('bocal_nervuras', bm, 'ferro', seg3)
        bm = bmesh.new()
        toro(bm, BOCA + Vector((0, 0, -0.004)), 0.176, 0.013, 48, 10)
        obj('bocal_anel', bm, 'anel_campo', seg3)
        bm = bmesh.new()
        for k in range(18):
            a = random.uniform(0, 2 * PI)
            h = random.uniform(0.0, 0.1)
            rr = 0.18 - (0.18 - 0.075) * h / 0.13 + 0.004
            gota(bm, BOCA + Vector((math.cos(a) * rr, math.sin(a) * rr, h + 0.005)), random.uniform(0.008, 0.02), 0.5)
        obj('bocal_lama', bm, 'lama', seg3)
        bm = bmesh.new()
        for k in range(10):
            a = random.uniform(0, 2 * PI)
            h = random.uniform(0.02, 0.11)
            rr = 0.18 - (0.18 - 0.075) * h / 0.13 + 0.004
            gota(bm, BOCA + Vector((math.cos(a) * rr, math.sin(a) * rr, h + 0.005)), random.uniform(0.006, 0.014), 0.4)
        obj('bocal_cinza', bm, 'cinza', seg3)
        luz = bpy.data.lights.new('Campo', 'POINT')
        luz.color = (0.6, 0.25, 1.0)
        luz.energy = 7
        luz.shadow_soft_size = 0.15
        lo = bpy.data.objects.new('Campo', luz)
        sc.collection.objects.link(lo)
        lo.parent = seg3
        lo.location = BOCA + Vector((0, 0, -0.06))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        campo = obj('campo', bm, 'campo', seg3)
        campo.location = BOCA + Vector((0, 0, -0.05))
        campo.scale = (0.21, 0.21, 0.11)
        # detalhe rústico nos segmentos: número, remendo, fiação do sensor
        bm = bmesh.new()
        n1 = Vector((-d1.z, 0, d1.x))
        n2 = Vector((-d2.z, 0, d2.x))
        numero(bm, S1 * 0.55 + Vector((0, -0.036, 0)), -EY, '%02d' % random.randint(10, 99), 0.04, 0.25, up=n1)
        numero(bm, S1 + S2 * 0.5 + Vector((0, -0.031, 0)), -EY, '2', 0.035, 0.0, up=n2)
        obj('seg_num', bm, 'stencil', seg1)
        bm = bmesh.new()
        caixa(bm, S1 * 0.3 + Vector((0, 0.037, 0)), (0.12, 0.006, 0.06), Matrix.Rotation(-math.atan2(S1.z, S1.x), 3, 'Y'))
        obj('seg_remendo', bm, 'primer', seg1)
        bm = bmesh.new()
        caixa(bm, S3 * 0.5 + Vector((0, -0.03, 0)), (0.04, 0.02, 0.05))           # caixa do sensor de chão
        obj('sensor', bm, 'grafite', seg3)
        bm = bmesh.new()
        caixa(bm, S3 * 0.5 + Vector((-0.012, -0.041, 0.01)), (0.008, 0.002, 0.008))
        obj('sensor_led', bm, 'led_ambar', seg3)
        bf = [bmesh.new(), bmesh.new(), bmesh.new()]
        fiacao(bf, S3 * 0.5 + Vector((0, -0.04, 0.03)), S3 * 0.2 + Vector((0.0, -0.035, 0.0)), 0.04, 4, 0.004)
        obj('sensor_fios_a', bf[0], 'fio_verm', seg3)
        obj('sensor_fios_b', bf[1], 'fio_azul', seg3)
        obj('sensor_fios_c', bf[2], 'borracha', seg3)

        cA, hA = pistao('pA', giro, 0.32, 0.3, 0.032)
        cB, hB = pistao('pB', seg1, 0.26, 0.24, 0.026)
        cC, hC = pistao('pC', seg2, 0.2, 0.2, 0.022)

        # fios de sujeira (lama e cinza) no quadro da torre; nascem além da faixa limpa
        fios = []
        alcance = S1.x + S2.x + BOCA.x
        zb = P + S1.z + S2.z + BOCA.z
        for k in range(16):
            cinza = k % 3 == 0
            r = random.uniform(alcance + 0.22, alcance + 0.62)
            a = random.uniform(-0.4, 0.4)
            G = Vector((r * math.cos(a), r * math.sin(a), 0.012))
            M = Vector((alcance, 0, zb)) + Vector((random.uniform(-0.06, 0.06), random.uniform(-0.06, 0.06), 0))
            dirg = (G - M).xy.to_3d().normalized()
            cam = bezier(G, G + Vector((0, 0, random.uniform(0.15, 0.32))) - dirg * 0.05,
                         M + dirg * random.uniform(0.05, 0.12) + Vector((0, 0, -0.12)), M + Vector((0, 0, 0.03)), 40)
            ond = random.uniform(0, 6)
            cam = [p + (EZ.cross(dirg)) * 0.008 * math.sin(i * 0.3 + ond) for i, p in enumerate(cam)]
            fios.append(cam)
            bm = bmesh.new()
            tubo_curvo(bm, cam, lambda u: 0.008 * (1 - u) ** 1.5 + 0.002, 8, passo=0.012)
            suavizar(obj('fio_sujeira', bm, 'fio_cinza' if cinza else 'fio_lama', giro))
            bm = bmesh.new()
            gota(bm, G, random.uniform(0.02, 0.035), 0.45)
            obj('fio_grumo', bm, 'cinza' if cinza else 'lama', giro)
        contas = []
        for k in range(len(fios) * 4):
            bm = bmesh.new()
            gota(bm, (0, 0, 0), random.uniform(0.006, 0.013), 0.8)
            contas.append((obj('conta', bm, 'cinza' if (k % len(fios)) % 3 == 0 else 'lama', giro), fios[k % len(fios)], (k // len(fios)) / 4 + random.uniform(0, 0.1)))
        BRACOS.append(dict(lado=lado, giro=giro, seg1=seg1, seg2=seg2, seg3=seg3, contas=contas,
                           pA=(cA, hA), pB=(cB, hB), pC=(cC, hC)))

        # cano fixo: junta rotativa → coletor de entrada do ciclone de lama
        bm = bmesh.new()
        topo = T + Vector((0, 0, P + 0.245))
        cot = Vector((T.x, T.y, 1.56))
        fim = Vector((0.06 if lado > 0 else -0.27, 0.45, 1.56))
        cano(bm, [topo, cot, fim], 0.05, 20)
        suavizar(obj('cano_fixo', bm, 'casco'))
        bm = bmesh.new()
        flange(bm, topo + Vector((0, 0, 0.01)), EZ, 0.068)
        flange(bm, fim + Vector((lado * 0.01, 0, 0)), EX, 0.068)
        flange(bm, cot.lerp(fim, 0.45), EX, 0.062, 0.025)
        obj('cano_flanges', bm, 'ferro')
        bm = bmesh.new()
        m = cot.lerp(fim, 0.3)
        pe = Vector((m.x * 0.5, 0.4, 0))
        rr = (pe.xy - C.xy).length
        pe.z = Z_TETO - (Z_TETO - Z_SILO) * max(0.0, rr - 0.3) / (R_SILO - 0.3)
        viga(bm, m - Vector((0, 0, 0.05)), pe, 0.025)
        obj('cano_escora', bm, 'laranja')
        dfe.quad(cot.lerp(fim, 0.7) + Vector((0, -0.05, 0)), -EY, 0.12, 0.06, off=0.003)

    # ------------------------------------------------------------------ cabos de força silo → torres
    bm, bc = bmesh.new(), bmesh.new()
    for lado in (1, -1):
        caixa_de(bm, (lado * AP, 0.2, 0.6), (lado * (AP + 0.05), 0.31, 0.74))
        for j in range(3):
            y = 0.225 + j * 0.03
            mangueira(bc, bezier((lado * (AP + 0.05), y, 0.62), (lado * (AP + 0.12), y, 0.55),
                                 (lado * 0.6, y + 0.05, 0.4), (lado * 0.6, y + 0.06, 0.2), 12), 0.011)
        caixa_de(bm, (lado * 0.6 - 0.03, 0.2, 0.25), (lado * 0.6 + 0.03, 0.34, 0.27))
    obj('caixa_juncao', bm, 'grafite')
    obj('cabos', bc, 'borracha')
    bm = bmesh.new()
    for lado in (1, -1):
        for j in range(3):
            caixa_de(bm, (min(lado * (AP + 0.05), lado * (AP + 0.052)), 0.22 + j * 0.03, 0.7),
                     (max(lado * (AP + 0.05), lado * (AP + 0.052)), 0.235 + j * 0.03, 0.715))
    obj('caixa_leds', bm, 'led')

    # ------------------------------------------------------------------ carretel e lança do drone (face sul do silo)
    YS = C.y - AP
    RC0 = Vector((0, YS - 0.15, 0.74))
    bm = bmesh.new()
    for sx in (-1, 1):
        caixa_de(bm, (sx * 0.15 - 0.012, YS - 0.22, 0.62), (sx * 0.15 + 0.012, YS, 0.86))
        caixa_de(bm, (sx * 0.15 - 0.02, YS - 0.03, 0.6), (sx * 0.15 + 0.02, YS, 0.88))
    obj('carretel_suporte', bm, 'laranja')
    bm = bmesh.new()
    cil(bm, RC0, 0.06, 0.26, EX, lados=24)
    for sx in (-1, 1):
        cil(bm, RC0 + Vector((sx * 0.12, 0, 0)), 0.11, 0.012, EX, lados=28)
    cil(bm, RC0 + Vector((0.2, 0, 0)), 0.045, 0.1, EX, lados=16)                 # motor do carretel
    cil(bm, RC0 + Vector((0.165, 0, 0)), 0.03, 0.04, EX, lados=12)
    obj('carretel', bm, 'grafite')
    bm = bmesh.new()
    for k in range(6):                                                           # cabo enrolado
        x = -0.1 + k * 0.04
        toro(bm, RC0 + Vector((x, 0, 0)), 0.078, 0.019, 32, 8, eixo=EX)
    suave_tudo(obj('carretel_cabo', bm, 'borracha'))
    bm = bmesh.new()                                                             # lança com polia
    PB0 = Vector((0, YS, 1.0))
    PT = Vector((0, YS - 0.55, 1.33))
    for sx in (-1, 1):
        viga(bm, PB0 + Vector((sx * 0.05, 0, 0)), PT + Vector((sx * 0.035, 0.0, 0)), 0.03)
    viga(bm, Vector((0, YS + 0.05, Z_TETO - 0.02)), PB0.lerp(PT, 0.55) + Vector((0, 0, 0.0)), 0.025)
    caixa_de(bm, (-0.08, YS - 0.03, 0.95), (0.08, YS, 1.05))
    for t in (0.33, 0.66):
        p = PB0.lerp(PT, t)
        viga(bm, p + Vector((-0.05, 0, 0)), p + Vector((0.05, 0, 0)), 0.015)
    obj('lanca_drone', bm, 'laranja')
    bm = bmesh.new()
    cil(bm, PT, 0.06, 0.03, EX, lados=24)
    cil(bm, PT, 0.012, 0.1, EX, lados=10)
    obj('polia', bm, 'ferro')
    numero(B_NUM, PB0.lerp(PT, 0.5) + Vector((0.051, 0, 0)), EX, '2', 0.03, 0.0)
    D = Vector((0.2, -1.85, 0.4))                    # drone (posição na foto)
    drone = vazio('drone', None, D)
    bm = bmesh.new()                                                             # cabo-mangueira: carretel → polia → drone
    cabo = [RC0 + Vector((0, 0, 0.1))] + bezier(RC0 + Vector((0, 0, 0.1)), RC0 + Vector((0, 0, 0.35)), PT + Vector((0, 0.1, 0.06)), PT + Vector((0, 0, 0.065)), 10)[1:]
    cabo2 = bezier(PT + Vector((0, -0.06, 0.0)), PT + Vector((0, -0.3, -0.2)), D + Vector((-0.05, 0.45, 0.35)), D + Vector((0, 0, 0.1)), 40)
    tubo_curvo(bm, cabo, 0.017, 10, corrug=0.1, passo=0.012)
    tubo_curvo(bm, [PT + Vector((0, 0, 0.065))] + [PT + Vector((0, -math.sin(a) * 0.065, math.cos(a) * 0.065)) for a in (0.6, 1.2, 1.57)], 0.017, 10)
    tubo_curvo(bm, cabo2, 0.02, 12, corrug=0.12, passo=0.012)
    suavizar(obj('cabo_drone', bm, 'borracha'))
    bm = bmesh.new()                                                             # cabo de força espiralado no cabo
    hel = []
    for i, p in enumerate(cabo2[2:-2]):
        q = cabo2[i + 3] - cabo2[i + 1]
        t, u, n = base_ortho(q, EX)
        a = i * 0.9
        hel.append(p + (t * math.cos(a) + u * math.sin(a)) * 0.024)
    tubo_curvo(bm, hel, 0.005, 6, passo=0.01)
    obj('cabo_forca', bm, 'fio_verm')
    bm = bmesh.new()
    for u in (0.25, 0.5, 0.75):
        i = int(u * (len(cabo2) - 1))
        toro(bm, cabo2[i], 0.026, 0.006, 16, 6, eixo=cabo2[i + 1] - cabo2[i])
    obj('cabo_abracadeiras', bm, 'aco')

    # drone-varredor (no quadro do drone)
    bm = bmesh.new()
    octo(bm, (0, 0, 0), 0.14, -0.03, 0.05)
    octo(bm, (0, 0, 0), 0.1, 0.05, 0.09, r2=0.07)
    obj('drone_casco', bm, 'laranja', drone)
    bm = bmesh.new()
    octo(bm, (0, 0, 0), 0.148, -0.01, 0.01)
    cil(bm, Vector((0, 0, 0.1)), 0.035, 0.03, lados=16)                          # engate do cabo
    obj('drone_cinta', bm, 'grafite', drone)
    rotores = []
    bm, bd = bmesh.new(), bmesh.new()
    for k in range(4):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        viga(bm, d * 0.1, d * 0.2, 0.03)
        toro(bd, d * 0.255, 0.085, 0.014, 32, 8)
        bmesh.ops.create_cone(bd, cap_ends=False, segments=32, radius1=0.085, radius2=0.085, depth=0.05, matrix=Matrix.Translation(d * 0.255 + Vector((0, 0, -0.02))))
        cil(bm, d * 0.255 + Vector((0, 0, -0.01)), 0.022, 0.05, lados=12)
        for j in range(3):
            b_ = j * 2 * PI / 3 + a
            viga(bm, d * 0.255 + Vector((0, 0, -0.03)), d * 0.255 + Vector((math.cos(b_) * 0.08, math.sin(b_) * 0.08, -0.03)), 0.008)
        ro = vazio('rotor_drone', drone, d * 0.255 + Vector((0, 0, 0.02)))
        br_ = bmesh.new()
        for j in range(3):
            b_ = j * 2 * PI / 3
            caixa(br_, Matrix.Rotation(b_, 3, 'Z') @ Vector((0.038, 0, 0)), (0.07, 0.016, 0.003), Matrix.Rotation(b_, 3, 'Z') @ Matrix.Rotation(0.4, 3, 'X'))
        cil(br_, Vector((0, 0, 0)), 0.012, 0.012, lados=10)
        obj('rotor_drone_pas', br_, 'aco', ro)
        rotores.append(ro)
    obj('drone_bracos', bm, 'grafite', drone)
    suavizar(obj('drone_dutos', bd, 'casco', drone))
    bm = bmesh.new()                                                             # sino de sucção sob o drone
    bmesh.ops.create_cone(bm, cap_ends=False, segments=28, radius1=0.12, radius2=0.06, depth=0.08, matrix=Matrix.Translation((0, 0, -0.07)))
    suavizar(obj('drone_sino', bm, 'casco', drone))
    bm = bmesh.new()
    toro(bm, (0, 0, -0.112), 0.12, 0.01, 40, 8)
    obj('drone_anel', bm, 'anel_campo', drone)
    bm = bmesh.new()
    for k in range(14):
        a = random.uniform(0, 2 * PI)
        h = random.uniform(0, 0.06)
        rr = 0.12 - 0.06 * h / 0.08 + 0.004
        gota(bm, Vector((math.cos(a) * rr, math.sin(a) * rr, -0.11 + h)), random.uniform(0.006, 0.014), 0.5)
    for k in range(10):
        a = random.uniform(0, 2 * PI)
        gota(bm, Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, -0.025)), random.uniform(0.005, 0.012), 0.5)
    obj('drone_lama', bm, 'lama', drone)
    bm = bmesh.new()                                                             # sensores, remendo, fiação exposta
    caixa(bm, Vector((0, -0.135, 0.01)), (0.06, 0.02, 0.03))
    obj('drone_sensor', bm, 'grafite', drone)
    bm = bmesh.new()
    cil(bm, Vector((-0.015, -0.146, 0.012)), 0.007, 0.004, -EY, lados=10)
    cil(bm, Vector((0.015, -0.146, 0.012)), 0.007, 0.004, -EY, lados=10)
    obj('drone_olhos', bm, 'led_ambar', drone)
    bm, bb = bmesh.new(), bmesh.new()
    remendo(bm, bb, Vector((0.1 * 0.924, 0.1 * 0.383, 0.03)), Vector((0.924, 0.383, 0)), 0.06, 0.04)
    obj('drone_remendo', bm, 'amarelo', drone)
    obj('drone_remendo_paraf', bb, 'aco', drone)
    bm = bmesh.new()
    numero(bm, Vector((-0.13 * 0.924, -0.13 * 0.383, 0.012)), Vector((-0.924, -0.383, 0)), 'D2', 0.03, 0.2)
    obj('drone_num', bm, 'stencil', drone)
    bf = [bmesh.new(), bmesh.new(), bmesh.new()]
    fiacao(bf, Vector((0.12, -0.04, 0.03)), Vector((0.16, 0.06, 0.0)), 0.025, 4, 0.0035)
    for b_, m_ in zip(bf, ('fio_verm', 'fio_azul', 'cobre')):
        obj('drone_fios', b_, m_, drone)
    luz = bpy.data.lights.new('Campo drone', 'POINT')
    luz.color = (0.6, 0.25, 1.0)
    luz.energy = 4
    luz.shadow_soft_size = 0.1
    lo = bpy.data.objects.new('Campo drone', luz)
    sc.collection.objects.link(lo)
    lo.parent = drone
    lo.location = (0, 0, -0.16)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    cd = obj('campo_drone', bm, 'campo', drone)
    cd.location = (0, 0, -0.16)
    cd.scale = (0.15, 0.15, 0.1)
    # fios sob o drone (no mundo; drone paira e oscila pouco)
    fios_d = []
    for k in range(14):
        cinza = k % 2 == 0
        r = random.uniform(0.12, 0.36)
        a = random.uniform(0, 2 * PI)
        G = Vector((D.x + r * math.cos(a), D.y + r * math.sin(a), 0.012))
        M = D + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), -0.12))
        dirg = (G - M).xy.to_3d().normalized()
        lat = EZ.cross(dirg)
        cam = bezier(G, G + Vector((0, 0, random.uniform(0.04, 0.1))) + dirg * 0.05 + lat * random.uniform(-0.1, 0.1), M + dirg * 0.12 + lat * random.uniform(-0.08, 0.08) + Vector((0, 0, -0.04)), M, 36)
        ond = random.uniform(0, 6)
        cam = [p + lat * 0.01 * math.sin(i * 0.35 + ond) * (1 - i / 36) for i, p in enumerate(cam)]
        fios_d.append(cam)
        bm = bmesh.new()
        tubo_curvo(bm, cam, lambda u: 0.005 * (1 - u) ** 1.5 + 0.0015, 8, passo=0.012)
        suavizar(obj('fio_drone', bm, 'fio_cinza' if cinza else 'fio_lama'))
        bm = bmesh.new()
        gota(bm, G, random.uniform(0.018, 0.03), 0.45)
        obj('fio_grumo', bm, 'cinza' if cinza else 'lama')
    contas_d = []
    for k in range(len(fios_d) * 3):
        bm = bmesh.new()
        gota(bm, (0, 0, 0), random.uniform(0.005, 0.011), 0.8)
        contas_d.append((obj('conta', bm, 'cinza' if (k % len(fios_d)) % 2 == 0 else 'lama'), fios_d[k % len(fios_d)], (k // len(fios_d)) / 3))
    bm = bmesh.new()                                                             # nuvem de cinza levantada sob o drone
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    po = obj('poeira_drone', bm, 'poeira_cinza')
    po.location = (D.x, D.y, 0.12)
    po.scale = (0.45, 0.45, 0.14)

    # ------------------------------------------------------------------ prensa enfardadeira (sudoeste)
    PC = Vector((-0.6, -0.62, 0))
    bm = bmesh.new()
    caixa_de(bm, (PC.x - 0.28, PC.y - 0.27, 0.08), (PC.x + 0.28, PC.y + 0.27, 0.11))
    for sx in (-1, 1):
        for sy in (-1, 1):
            caixa_de(bm, (PC.x + sx * 0.22 - 0.03, PC.y + sy * 0.21 - 0.03, 0.11), (PC.x + sx * 0.22 + 0.03, PC.y + sy * 0.21 + 0.03, 1.03))
    for sy in (-1, 1):
        caixa_de(bm, (PC.x - 0.26, PC.y + sy * 0.21 - 0.04, 0.95), (PC.x + 0.26, PC.y + sy * 0.21 + 0.04, 1.05))
    caixa_de(bm, (PC.x - 0.12, PC.y - 0.25, 0.95), (PC.x + 0.12, PC.y + 0.25, 1.05))
    obj('prensa', bm, 'laranja')
    bm = bmesh.new()                                                             # câmara de fardo (aberta a leste)
    caixa_de(bm, (PC.x - 0.15, PC.y - 0.15, 0.11), (PC.x + 0.15, PC.y - 0.13, 0.5))
    caixa_de(bm, (PC.x - 0.15, PC.y + 0.13, 0.11), (PC.x + 0.15, PC.y + 0.15, 0.5))
    caixa_de(bm, (PC.x - 0.15, PC.y - 0.15, 0.11), (PC.x - 0.13, PC.y + 0.15, 0.5))
    caixa_de(bm, (PC.x - 0.15, PC.y - 0.15, 0.11), (PC.x + 0.15, PC.y + 0.15, 0.13))
    obj('camara', bm, 'ferro')
    bm = bmesh.new()                                                             # comporta leste erguida
    caixa_de(bm, (PC.x + 0.15, PC.y - 0.15, 0.42), (PC.x + 0.17, PC.y + 0.15, 0.78))
    for sy in (-1, 1):
        caixa_de(bm, (PC.x + 0.15, PC.y + sy * 0.165 - 0.01, 0.11), (PC.x + 0.19, PC.y + sy * 0.165 + 0.01, 0.85))
    obj('comporta', bm, 'grafite')
    bm = bmesh.new()
    caixa_de(bm, (PC.x - 0.13, PC.y - 0.13, 0.13), (PC.x + 0.15, PC.y + 0.13, 0.33))
    obj('fardo_formando', bm, 'fardo')
    bm = bmesh.new()
    for sx in (-1, 1):
        cil(bm, Vector((PC.x + sx * 0.16, PC.y, 0.55)), 0.013, 0.8, lados=10)
    obj('prensa_guias', bm, 'cromo')
    bm = bmesh.new()
    cil(bm, PC + Vector((0, 0, 1.3)), 0.065, 0.5, lados=24)
    cil(bm, PC + Vector((0, 0, 1.06)), 0.085, 0.03, lados=24)
    cil(bm, PC + Vector((0, 0, 1.55)), 0.08, 0.03, lados=24)
    suavizar(obj('prensa_cilindro', bm, 'grafite'))
    dfe.cilindro(PC, 0.066, -PI / 2, 1.1, 1.5, 0.06)
    placa = vazio('prensa_placa')
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (0.25, 0.24, 0.035))
    caixa(bm, (0, 0, 0.03), (0.36, 0.06, 0.03))
    for sx in (-1, 1):
        cil(bm, Vector((sx * 0.16, 0, 0.03)), 0.024, 0.05, lados=12)
    obj('prensa_placa', bm, 'ferro', placa)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.36)), 0.03, 0.66, lados=16)
    suavizar(obj('prensa_haste', bm, 'cromo', placa))
    bm = bmesh.new()                                                             # empurrador (oeste) que tira o fardo
    cil(bm, Vector((PC.x - 0.29, PC.y, 0.24)), 0.04, 0.2, EX, lados=18)
    cil(bm, Vector((PC.x - 0.19, PC.y, 0.24)), 0.048, 0.02, EX, lados=18)
    caixa_de(bm, (PC.x - 0.4, PC.y - 0.06, 0.11), (PC.x - 0.36, PC.y + 0.06, 0.3))
    suavizar(obj('empurrador', bm, 'laranja'))
    bm = bmesh.new()
    cil(bm, Vector((PC.x - 0.16, PC.y, 0.24)), 0.016, 0.05, EX, lados=12)
    obj('empurrador_haste', bm, 'cromo')
    bm = bmesh.new()                                                             # rosca de lodo+cinza: silo (face oeste) → câmara
    SA = Vector((-AP - 0.0, 0.05, 0.28))
    SB = Vector((-0.6, -0.4, 0.7))
    tubo(bm, SA, SB, 0.045, 20)
    cil(bm, SA + (SB - SA).normalized() * 0.02, 0.06, 0.03, SB - SA, lados=20)
    cil(bm, SA.lerp(SB, 0.4), 0.075, 0.12, SB - SA, lados=20)
    suavizar(obj('rosca', bm, 'casco'))
    bm = bmesh.new()
    SBb = SB + (SB - SA).normalized() * 0.02
    cil(bm, SBb + Vector((0, 0, -0.06)), 0.04, 0.12, lados=14)
    obj('rosca_bica', bm, 'ferro')
    bm = bmesh.new()
    caixa_de(bm, (-0.98, -0.3, 0.08), (-0.8, -0.12, 0.3))
    cil(bm, Vector((-0.89, -0.21, 0.34)), 0.05, 0.08, lados=14)
    obj('hidraulica', bm, 'grafite')
    bm = bmesh.new()
    mangueira(bm, bezier((-0.89, -0.19, 0.38), (-0.89, -0.2, 0.9), (-0.75, -0.6, 1.2), PC + Vector((-0.06, 0.03, 1.12)), 14), 0.011)
    mangueira(bm, bezier((-0.86, -0.25, 0.38), (-0.8, -0.3, 1.0), (-0.72, -0.6, 1.6), PC + Vector((-0.06, -0.03, 1.48)), 16), 0.011)
    mangueira(bm, bezier((-0.92, -0.28, 0.2), (-0.95, -0.4, 0.2), (PC.x - 0.32, PC.y + 0.1, 0.3), (PC.x - 0.3, PC.y + 0.04, 0.27), 12), 0.009)
    obj('hidraulica_mangueiras', bm, 'borracha')
    numero(B_NUM, Vector((-0.89, -0.30 - 0.001, 0.2)), -EY, '2-44', 0.03, 0.3)
    dol.quad(Vector((-0.89, -0.3, 0.17)), -EY, 0.12, 0.16)
    remendo(B_TROCA, B_PAR, PC + Vector((-0.22, -0.241, 0.6)), -EY, 0.05, 0.22)   # montante trocado (amarelo)
    dla.quad(PC + Vector((0.05, -0.151, 0.3)), -EY, 0.26, 0.2, up=-EZ)

    # ------------------------------------------------------------------ esteira de fardos → boca de cortinas (leste)
    YE, ZE = PC.y, 0.3
    XE0, XE1 = PC.x + 0.19, 0.98
    bm = bmesh.new()
    for sy in (-1, 1):
        caixa_de(bm, (XE0, YE + sy * 0.13 - 0.012, ZE - 0.07), (XE1, YE + sy * 0.13 + 0.012, ZE + 0.02))
    for x in (XE0 + 0.08, -0.05, 0.35, 0.72):
        for sy in (-1, 1):
            caixa_de(bm, (x - 0.018, YE + sy * 0.13 - 0.018, 0.08), (x + 0.018, YE + sy * 0.13 + 0.018, ZE - 0.07))
        caixa_de(bm, (x - 0.012, YE - 0.13, 0.14), (x + 0.012, YE + 0.13, 0.16))
    obj('esteira_quadro', bm, 'laranja')
    bm = bmesh.new()
    caixa_de(bm, (XE0, YE - 0.115, ZE - 0.035), (XE1, YE + 0.115, ZE))
    obj('esteira_correia', bm, 'borracha')
    bm = bmesh.new()
    x = XE0 + 0.03
    while x < XE1 - 0.02:
        caixa_de(bm, (x, YE - 0.11, ZE), (x + 0.012, YE + 0.11, ZE + 0.008))
        x += 0.09
    for x in (XE0, XE1):
        cil(bm, Vector((x, YE, ZE - 0.018)), 0.022, 0.24, EY, lados=16)
    obj('esteira_taliscas', bm, 'ferro')
    bm = bmesh.new()                                                             # motor de tração com corrente
    caixa_de(bm, (XE1 - 0.2, YE + 0.142, 0.12), (XE1 - 0.05, YE + 0.24, 0.26))
    cil(bm, Vector((XE1 - 0.12, YE + 0.2, 0.3)), 0.04, 0.1, EY, lados=14)
    obj('esteira_motor', bm, 'grafite')
    bm = bmesh.new()
    caixa_de(bm, (XE1 - 0.14, YE + 0.142, ZE - 0.05), (XE1 + 0.0, YE + 0.16, ZE + 0.0))
    obj('esteira_guarda', bm, 'amarelo')
    # boca de cortinas
    BX0, BX1 = 0.74, 1.0
    bm = bmesh.new()
    for sy in (-1, 1):
        caixa_de(bm, (BX0, YE + sy * 0.17 - 0.015, 0.08), (BX1, YE + sy * 0.17 + 0.015, 0.62))
    caixa_de(bm, (BX0, YE - 0.185, 0.6), (BX1, YE + 0.185, 0.64))
    obj('boca', bm, 'grafite')
    bm = bmesh.new()
    for x in (BX0 - 0.01, BX1 - 0.015):
        for sy in (-1, 1):
            caixa_de(bm, (x, YE + sy * 0.17 - 0.03, 0.08), (x + 0.025, YE + sy * 0.17 + 0.03, 0.66))
        caixa_de(bm, (x, YE - 0.2, 0.6), (x + 0.025, YE + 0.2, 0.66))
    obj('boca_moldura', bm, 'listras')
    bm = bmesh.new()
    for x in (BX0 + 0.005, BX1 - 0.03):
        for j in range(7):
            y = YE - 0.135 + j * 0.045
            caixa_de(bm, (x, y - 0.019, ZE + 0.17), (x + 0.008, y + 0.019, 0.6))
    obj('boca_cortinas', bm, 'borracha')
    bm = bmesh.new()
    cil(bm, Vector((0.87, YE, 0.69)), 0.035, 0.06, lados=14)
    obj('giroflex', bm, 'led_ambar')
    bm = bmesh.new()
    cil(bm, Vector((0.87, YE, 0.66)), 0.045, 0.02, lados=14)
    obj('giroflex_base', bm, 'ferro')
    numero(B_NUM, Vector((0.87, YE - 0.186, 0.45)), -EY, 'II', 0.08, 0.0)
    dfu.quad(Vector((BX1 + 0.001, YE, 0.45)), EX, 0.34, 0.28, off=0.017)
    dla.quad(Vector((0.87, YE - 0.186, 0.25)), -EY, 0.24, 0.2, up=-EZ)

    def fardo(bm, bc, c, rot, s=1.0):
        R = Matrix.Rotation(rot[2], 3, 'Z') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[0], 3, 'X')
        caixa(bm, c, (0.2 * s, 0.17 * s, 0.15 * s), R)
        for f in (-0.28, 0.28):                                                  # cintas de aço
            caixa(bc, Vector(c) + R @ Vector((f * 0.2 * s, 0, 0)), (0.012, 0.174 * s, 0.154 * s), R)
        caixa(bc, Vector(c) + R @ Vector((0, -0.086 * s, 0.03)), (0.04, 0.004, 0.025), R)   # etiqueta/lacre
    FARDOS = []
    for k in range(3):
        b1, b2 = bmesh.new(), bmesh.new()
        fardo(b1, b2, (0, 0, 0), (0, 0, 0))
        e = vazio('fardo_esteira')
        obj('fardo', b1, 'fardo', e)
        obj('fardo_cintas', b2, 'galvan', e)
        FARDOS.append(e)
    b1, b2 = bmesh.new(), bmesh.new()
    fardo(b1, b2, (1.1, YE + 0.01, 0.2), (0.1, 0.55, 0.12))                       # caindo pela boca
    fardo(b1, b2, (1.3, -0.47, 0.075), (0, 0, 0.3))
    fardo(b1, b2, (1.42, -0.72, 0.075), (0, 0, -0.2))
    fardo(b1, b2, (1.58, -0.5, 0.075), (0, 0, 0.9))
    fardo(b1, b2, (1.38, -0.6, 0.225), (0.05, 0.0, 0.1))
    fardo(b1, b2, (1.6, -0.86, 0.06), (0.5, 0.2, 1.4))
    obj('fardos_monte', b1, 'fardo')
    obj('fardos_monte_cintas', b2, 'galvan')
    bm = bmesh.new()
    for k in range(30):
        gota(bm, (random.uniform(1.0, 1.75), random.uniform(-1.0, -0.3), 0.01), random.uniform(0.008, 0.025), 0.4)
    obj('fardos_farelo', bm, 'cinza')

    # ------------------------------------------------------------------ norte: armário elétrico aberto, tambor de óleo, sucata
    bm = bmesh.new()
    caixa_de(bm, (-0.4, 0.7, 0.08), (-0.05, 0.92, 0.62))
    obj('armario', bm, 'grafite')
    bm = bmesh.new()
    caixa(bm, Vector((-0.43, 0.6, 0.35)), (0.012, 0.22, 0.5), Matrix.Rotation(-1.1, 3, 'Z'))   # porta aberta pendurada
    obj('armario_porta', bm, 'primer')
    bm = bmesh.new()
    caixa_de(bm, (-0.38, 0.695, 0.12), (-0.07, 0.7, 0.58))
    obj('armario_fundo', bm, 'vazio')
    bf = [bmesh.new(), bmesh.new(), bmesh.new()]
    for k in range(3):
        fiacao(bf, Vector((-0.35 + k * 0.1, 0.71, 0.55)), Vector((-0.32 + k * 0.1, 0.7, 0.15)), 0.0, 3, 0.005)
    fiacao(bf, Vector((-0.1, 0.7, 0.3)), Vector((0.1, 0.45, 0.12)), 0.12, 5, 0.006)
    for b_, m_ in zip(bf, ('fio_verm', 'fio_azul', 'borracha')):
        obj('armario_fios', b_, m_)
    bm = bmesh.new()
    for j in range(4):
        caixa_de(bm, (-0.36 + j * 0.07, 0.705, 0.42), (-0.31 + j * 0.07, 0.72, 0.5))
    obj('armario_disjuntores', bm, 'ferro')
    bm = bmesh.new()
    caixa_de(bm, (-0.34, 0.721, 0.47), (-0.33, 0.723, 0.48))
    caixa_de(bm, (-0.2, 0.721, 0.47), (-0.19, 0.723, 0.48))
    obj('armario_led', bm, 'led_verm')
    bm, ba = bmesh.new(), bmesh.new()
    tambor(bm, ba, (0.5, 0.8, 0.29), 0.12, 0.42)
    obj('tambor_oleo', bm, 'tambor')
    obj('tambor_oleo_aros', ba, 'grafite')
    dol.cilindro((0.5, 0.8), 0.12, -PI / 2, 0.1, 0.48, 0.08)
    bm = bmesh.new()                                                             # bocal velho de reposição (sucata)
    bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.13, radius2=0.06, depth=0.1,
                          matrix=Matrix.Translation((0.18, 0.84, 0.15)) @ Matrix.Rotation(1.9, 4, 'X'))
    suavizar(obj('bocal_velho', bm, 'casco'))

    # ------------------------------------------------------------------ laje e chão: lama, cinza, óleo, poeira
    def sujeira(x, y):
        d = math.hypot(x, y)
        dens = noise.noise(Vector((x * 1.4, y * 1.4, 2.0))) * 0.5 + noise.noise(Vector((x * 5, y * 5, 4.0))) * 0.25
        s = sst(-0.06, 0.06, dens - (-0.25 + (d - 1.3) * 0.3))
        dc = noise.noise(Vector((x * 1.1 + 7, y * 1.1, 3.0))) * 0.5 + noise.noise(Vector((x * 4, y * 4, 9.0))) * 0.25
        c = sst(-0.06, 0.06, dc - (-0.15 + (d - 1.3) * 0.25)) * (1 - s)
        var = 0.0
        alc = S1.x + S2.x + BOCA.x
        for lado, T in TORRES:
            rx, ry = lado * (x - T.x), y - T.y
            r = math.hypot(rx, ry)
            a = abs(math.atan2(ry, rx))
            borda = 0.02 * noise.noise(Vector((x * 14, y * 14, 1)))
            k = sst(0.3, 0.38, r) * (1 - sst(alc + 0.12, alc + 0.18, r + borda)) * (1 - sst(0.74, 0.86, a + borda * 2))
            s *= 1 - k
            c *= 1 - k
            var = max(var, k)
        rd = math.hypot(x - D.x, y - D.y)                                         # disco varrido pelo drone
        k = 1 - sst(0.2, 0.3, rd + 0.03 * noise.noise(Vector((x * 12, y * 12, 5))))
        s *= 1 - k
        c *= 1 - k
        var = max(var, k)
        if 0.95 < x < 1.8 and -1.0 < y < -0.25:                                  # farelo do monte de fardos
            c = max(c, 0.6 * (1 - sst(0.2, 0.4, abs(y + 0.62))))
        return s, c, var
    chao_grade(sujeira)
    bm = bmesh.new()
    for c, r, z in (((-1.6, 0.9), 0.16, 0.0095), ((1.5, 1.4), 0.12, 0.0095), ((-1.3, -1.5), 0.18, 0.0095), ((2.0, -0.2), 0.1, 0.0095),
                    ((0.25, -0.3), 0.06, 0.0822), ((-0.35, -0.95), 0.07, 0.0822), ((0.45, 0.6), 0.05, 0.0822), ((-0.85, -0.1), 0.06, 0.0822)):
        mancha_lisa(bm, c, r, z)
    obj('oleo_pocas', bm, 'oleo')
    bm, bc2 = bmesh.new(), bmesh.new()
    for k in range(16):
        c = (random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95))
        if math.hypot(c[0] - C.x, c[1] - C.y) < R_SILO + 0.05:
            continue
        mancha(bm if k % 2 else bc2, c, random.uniform(0.04, 0.1), 0.0815)
    obj('laje_lama', bm, 'lama_seca')
    obj('laje_cinza', bc2, 'cinza')
    bm = bmesh.new()
    for k in range(80):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(R_SILO + 0.03, 0.8)
        gota(bm, (C.x + math.cos(a) * r, C.y + math.sin(a) * r, 0.083), random.uniform(0.006, 0.018), 0.3)
    for k in range(40):
        f = random.randrange(8)
        a = f * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-d.y, d.x, 0))
        z = 0.09 + random.expovariate(9.0)
        if z > 0.6 or (f in (5, 7) and z > 0.27):
            continue
        gota(bm, C + d * (AP + 0.002) + t * random.uniform(-0.16, 0.16) + Vector((0, 0, z)), random.uniform(0.005, 0.012), 0.6)
    obj('respingos', bm, 'lama')
    bm = bmesh.new()                                                              # poeira de cinza assentada no que é horizontal
    poeira(bm, -0.25, 0.25, C.y - 0.25, C.y + 0.25, Z_TETO + 0.02, 40)
    poeira(bm, PC.x - 0.26, PC.x + 0.26, PC.y - 0.25, PC.y + 0.25, 1.052, 40)
    poeira(bm, 0.75, 0.99, YE - 0.18, YE + 0.18, 0.642, 25)
    poeira(bm, -0.39, -0.06, 0.71, 0.91, 0.622, 20)
    for lado, T in TORRES:
        poeira(bm, T.x - 0.12, T.x + 0.12, T.y - 0.12, T.y + 0.12, 0.152, 20)
    obj('poeira', bm, 'cinza')

    # objetos de detalhe acumulados
    obj('remendos', B_REM, 'galvan')
    obj('remendos_primer', B_REMP, 'primer')
    obj('pecas_trocadas', B_TROCA, 'amarelo')
    obj('parafusos_remendo', B_PAR, 'aco')
    obj('numeros', B_NUM, 'stencil')
    suave_tudo(obj('chapa_amassada', B_AMAS, 'silo'))
    for dc, nome in ((dfu, 'd_fuligem'), (dfe, 'd_ferrugem'), (dol, 'd_oleo'), (dla, 'd_lama'), (dpo, 'd_poeira')):
        dc.fim(nome)

    vapores = []
    for k in range(7):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        vapores.append(obj('vapor', bm, 'vapor'))

    # ------------------------------------------------------------------ animação
    def suave(x):
        return x * x * (3 - 2 * x)
    J1 = Vector((0, 0, 0))
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        for i, b in enumerate(BRACOS):
            fase = 0.0 if i == 0 else 0.5
            yaw = 0.5 * math.sin(2 * PI * (fr + fase))
            p1 = 0.03 * math.sin(4 * PI * (fr + fase)) + 0.01
            p2 = -0.04 * math.sin(4 * PI * (fr + fase) + 0.6)
            p3 = -(p1 + p2)
            b['giro'].rotation_euler = (0, 0, yaw + (0 if b['lado'] > 0 else PI))
            b['giro'].keyframe_insert('rotation_euler', frame=q)
            for s, p in ((b['seg1'], p1), (b['seg2'], p2), (b['seg3'], p3)):
                s.rotation_euler = (0, -p, 0)
                s.keyframe_insert('rotation_euler', frame=q)
            R1, R2, R3 = Matrix.Rotation(-p1, 3, 'Y'), Matrix.Rotation(-p2, 3, 'Y'), Matrix.Rotation(-p3, 3, 'Y')
            # A: coluna (giro) → seg1; B: seg1 → seg2; C: seg2 → seg3
            pistao_por(*b['pA'], Vector((0.11, 0, 0.63)), Vector((0, 0, P)) + R1 @ Vector((0.2, 0, -0.045)), q)
            pistao_por(*b['pB'], Vector((0.08, 0, 0.16)), S1 + R2 @ Vector((0.15, 0, 0.14)), q)
            pistao_por(*b['pC'], Vector((0.14, 0, -0.075)), S2 + R3 @ Vector((-0.07, 0, -0.07)), q)
            for o, cam, u0 in b['contas']:
                u = (u0 + fr * 2) % 1.0
                idx = u * (len(cam) - 1)
                k0 = int(idx)
                o.location = cam[k0].lerp(cam[min(k0 + 1, len(cam) - 1)], idx - k0)
                o.scale = [max(0.05, 1.0 - 0.7 * u)] * 3
                o.keyframe_insert('location', frame=q)
                o.keyframe_insert('scale', frame=q)
        for o, cam, u0 in contas_d:
            u = (u0 + fr * 2) % 1.0
            idx = u * (len(cam) - 1)
            k0 = int(idx)
            o.location = cam[k0].lerp(cam[min(k0 + 1, len(cam) - 1)], idx - k0)
            o.scale = [max(0.05, 1.0 - 0.7 * u)] * 3
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('scale', frame=q)
        drone.location = D + Vector((0.015 * math.sin(2 * PI * fr), 0.01 * math.sin(4 * PI * fr), 0.012 * math.sin(2 * PI * 2 * fr)))
        drone.rotation_euler = (0.03 * math.sin(2 * PI * fr), 0.03 * math.cos(2 * PI * fr), 0.05 * math.sin(2 * PI * fr))
        drone.keyframe_insert('location', frame=q)
        drone.keyframe_insert('rotation_euler', frame=q)
        for k, ro in enumerate(rotores):
            ro.rotation_euler = (0, 0, (1 if k % 2 else -1) * 2 * PI * 16 * fr + k)
            ro.keyframe_insert('rotation_euler', frame=q)
        rotor.rotation_euler = (0, 0, -2 * PI * 9 * fr)
        rotor.keyframe_insert('rotation_euler', frame=q)
        if fr < 0.55:
            s = suave(fr / 0.55)
        elif fr < 0.7:
            s = 1.0
        else:
            s = 1.0 - suave((fr - 0.7) / 0.3)
        placa.location = PC + Vector((0, 0, 0.88 - 0.5 * s))
        placa.keyframe_insert('location', frame=q)
        for k, e in enumerate(FARDOS):
            x = XE0 + 0.17 + ((k * 0.4 + fr * 0.4) % 1.2)
            e.location = (x, YE, ZE + 0.08)
            e.scale = [1.0 if x < BX0 + 0.06 else 0.01] * 3
            e.keyframe_insert('location', frame=q)
            e.keyframe_insert('scale', frame=q)
        em = base3d.M['anel_campo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        em.default_value = 8 + 4 * math.sin(2 * PI * 6 * fr) ** 2
        em.keyframe_insert('default_value', frame=q)
        for k, o in enumerate(vapores):
            u = (k / len(vapores) + fr) % 1.0
            o.location = T0 + Vector((0.22 * u * u + 0.03 * math.sin(k * 2.0), 0.1 * u, 0.12 + 0.75 * u))
            o.scale = [0.09 + 0.26 * u] * 3
            o.rotation_euler = (k, u * 2, k * 0.5)
            for c in ('location', 'scale', 'rotation_euler'):
                o.keyframe_insert(c, frame=q)
    linear_keys()
    cena_final((0.15, -0.2, 0.75), ((300, 5.6, 2.3, 32),), 'coletor_lixo_2',
               ((1.55, -3.35, 1.1), (0.35, -1.2, 0.5), 30),
               ((1.25, -1.45, 2.55), (0.0, 0.2, 1.55), 30))


# ================================================================== PURIFICADOR DE AR
def purificador_ar():
    nova_cena(47)
    materiais_comuns()
    base3d.M.update({
        'plis_sujo': lama_mat('Plissado sujo', (0.32, 0.29, 0.23), 0.9, 0.6, 26.0, (0.035, 0.032, 0.03)),
        'plis_saturado': lama_mat('Plissado saturado', (0.11, 0.1, 0.085), 0.95, 1.0, 34.0, (0.012, 0.012, 0.011)),
        'plis_limpo': lama_mat('Plissado novo', (0.72, 0.68, 0.58), 0.9, 0.2, 20.0, (0.6, 0.56, 0.47)),
        'fuligem': lama_mat('Fuligem', (0.035, 0.033, 0.032), 0.95, 0.7, 34.0, (0.012, 0.012, 0.012)),
        'agua_preta': vidro_mat('Água preta', (0.04, 0.04, 0.035), 0.2, 0.05),
        'gotas': vidro_mat('Gotas', (0.8, 0.83, 0.85), 0.35, 0.15),
        'borra': lama_mat('Borra', (0.04, 0.038, 0.035), 0.12, 0.3),
        'fio_fuligem': fio_mat('Fio de fuligem', (0.02, 0.02, 0.02), 4.0),
        'cristal': emis_mat('Cristal', (0.5, 0.12, 1.0), 4.0, (0.22, 0.05, 0.42)),
        'fumaca': nuvem_mat('Fumaça suja', (0.03, 0.029, 0.028), 12.0),
        'neblina': nuvem_mat('Neblina suja', (0.06, 0.058, 0.055), 0.9, lim=(0.3, 0.75)),
        'nevoa': nuvem_mat('Névoa do borrifo', (0.6, 0.62, 0.64), 1.2),
        'ar_limpo': nuvem_mat('Ar limpo', (0.95, 0.93, 0.98), 0.35, (1.0, 0.92, 0.95), 0.7, (0.3, 0.75)),
        'chao_sujo': chao_mat((0.075, 0.07, 0.066), (0.03, 0.029, 0.028), (0.2, 0.195, 0.19), 0.85, umido=False),
    })
    dfu, dfe, dol, dpo = (Decal(m) for m in ('d_fuligem', 'd_ferrugem', 'd_oleo', 'd_poeira'))
    B_REM, B_REMP, B_TROCA, B_PAR, B_NUM, B_AMAS, B_FUL = (bmesh.new() for _ in range(7))
    laje()

    # ------------------------------------------------------------------ plenum de entrada com dois ventiladores ao sul
    PX0, PX1, PY0, PY1, PZ = -0.85, 0.45, -0.38, 0.5, 0.8
    bm = bmesh.new()
    caixa_de(bm, (PX0, PY0, 0.08), (PX1, PY1, PZ))
    obj('plenum', bm, 'grafite')
    bm = bmesh.new()
    for x in (PX0, PX1):
        for y in (PY0, PY1):
            caixa_de(bm, (x - 0.025, y - 0.025, 0.08), (x + 0.025, y + 0.025, PZ + 0.02))
    for z in (0.1, PZ - 0.01):
        caixa_de(bm, (PX0 - 0.02, PY0 - 0.02, z - 0.02), (PX1 + 0.02, PY0 + 0.0, z + 0.02))
        caixa_de(bm, (PX0 - 0.02, PY0, z - 0.02), (PX0 + 0.0, PY1, z + 0.02))
        caixa_de(bm, (PX1, PY0, z - 0.02), (PX1 + 0.02, PY1, z + 0.02))
    obj('plenum_quadro', bm, 'amarelo')
    FANS = (-0.5, 0.1)
    FZ, FR = 0.44, 0.27
    YF = PY0 - 0.12
    rot_fans = []
    for i, fx in enumerate(FANS):
        c = Vector((fx, PY0, FZ))
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=FR + 0.02, radius2=FR + 0.02, depth=0.12,
                              matrix=Matrix.Translation(c + Vector((0, -0.06, 0))) @ Matrix.Rotation(PI / 2, 4, 'X'))
        bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=FR, radius2=FR, depth=0.12,
                              matrix=Matrix.Translation(c + Vector((0, -0.06, 0))) @ Matrix.Rotation(PI / 2, 4, 'X'))
        suavizar(obj('fan_carenagem', bm, 'casco'))
        bm = bmesh.new()
        toro(bm, c + Vector((0, -0.12, 0)), FR + 0.012, 0.016, 64, 10, eixo=EY)       # lábio de entrada
        toro(bm, c + Vector((0, -0.005, 0)), FR + 0.03, 0.012, 64, 8, eixo=EY)
        for k in range(12):                                                    # parafusos do anel
            a = k * PI / 6
            cil(bm, c + Vector((math.cos(a) * (FR + 0.045), -0.01, math.sin(a) * (FR + 0.045))), 0.008, 0.012, EY, lados=6)
        obj('fan_aros', bm, 'ferro')
        bm = bmesh.new()
        cil(bm, c + Vector((0, 0.003, 0)), FR, 0.004, EY, lados=48)
        obj('fan_fundo', bm, 'vazio')
        bm = bmesh.new()                                                       # grade de proteção
        for rr in (0.08, 0.15, 0.22):
            toro(bm, c + Vector((0, -0.125, 0)), rr, 0.005, 48, 6, eixo=EY)
        for k in range(8):
            a = k * PI / 4
            d = Vector((math.cos(a), 0, math.sin(a)))
            viga(bm, c + Vector((0, -0.125, 0)) + d * 0.05, c + Vector((0, -0.125, 0)) + d * (FR + 0.01), 0.008)
        obj('fan_grade', bm, 'ferro')
        bm = bmesh.new()                                                       # motor no cubo, suportado por 3 braços
        cil(bm, c + Vector((0, -0.04, 0)), 0.07, 0.1, EY, lados=20)
        for k in range(3):
            a = PI / 2 + k * 2 * PI / 3
            d = Vector((math.cos(a), 0, math.sin(a)))
            viga(bm, c + Vector((0, -0.02, 0)) + d * 0.06, c + Vector((0, -0.02, 0)) + d * FR, 0.02)
        obj('fan_motor', bm, 'grafite')
        ro = vazio('fan_rotor', None, c + Vector((0, -0.095, 0)))
        bm = bmesh.new()
        esfera(bm, (0, 0, 0), 0.055, 16)
        for k in range(7):
            a = k * 2 * PI / 7
            R = Matrix.Rotation(a, 3, 'Y') @ Matrix.Rotation(0.5, 3, 'X')
            caixa(bm, Matrix.Rotation(a, 3, 'Y') @ Vector((0.15, 0, 0)), (0.19, 0.008, 0.085), R)
        obj('fan_pas', bm, 'aco', ro)
        bm = bmesh.new()
        for k in range(7):
            a = k * 2 * PI / 7
            gota(bm, Matrix.Rotation(a, 3, 'Y') @ Vector((0.2, -0.01, 0.0)), 0.02, 0.4)
        obj('fan_pas_fuligem', bm, 'fuligem', ro)
        rot_fans.append(ro)
        dfu.quad(c + Vector((0, -0.001, FR + 0.08)), -EY, 0.62, 0.16, up=-EZ, off=0.0)
        dfu.quad(c + Vector((0, -0.001, -FR - 0.07)), -EY, 0.6, 0.12, off=0.0)
        numero(B_NUM, c + Vector((FR - 0.02, -0.001, FR + 0.04)), -EY, 'V%d' % (i + 1), 0.04, 0.2)
    bm = bmesh.new()                                                           # fuligem grudada no lábio e na grade
    for fx in FANS:
        for k in range(40):
            a = random.uniform(0, 2 * PI)
            r_ = random.choice((FR + 0.012, 0.15, 0.22))
            gota(bm, Vector((fx + math.cos(a) * r_, YF - 0.005, FZ + math.sin(a) * r_)), random.uniform(0.006, 0.014), 0.7)
    obj('fan_crosta', bm, 'fuligem')
    # chapas laterais do plenum: amassadas, remendo, ferrugem, número
    chapa_amassada(B_AMAS, Vector((PX0, 0.06, 0.45)), -EX, 0.7, 0.55, dentes=3, prof=0.02)
    chapa_amassada(B_AMAS, Vector((PX1, 0.06, 0.45)), EX, 0.7, 0.55, dentes=2, prof=0.018)
    remendo(B_REMP, B_PAR, Vector((PX1 + 0.006, 0.3, 0.3)), EX, 0.18, 0.2)
    remendo(B_REM, B_PAR, Vector((-0.2, PY0, 0.73)), -EY, 0.2, 0.08)
    numero(B_NUM, Vector((PX1 + 0.012, -0.2, 0.62)), EX, 'PA-0617', 0.045, 0.3)
    dfe.quad(Vector((PX1, -0.15, 0.5)), EX, 0.12, 0.55)
    dfe.quad(Vector((PX0, 0.35, 0.5)), -EX, 0.1, 0.5)
    dol.quad(Vector((PX1, 0.4, 0.2)), EX, 0.1, 0.2)
    bm = bmesh.new()                                                           # porta de inspeção entreaberta (oeste)
    caixa(bm, Vector((PX0 - 0.06, -0.2, 0.42)), (0.012, 0.2, 0.36), Matrix.Rotation(0.5, 3, 'Z'))
    obj('porta_inspecao', bm, 'grafite')
    bm = bmesh.new()
    caixa_de(bm, (PX0 - 0.003, -0.26, 0.26), (PX0, -0.06, 0.6))
    obj('porta_vao', bm, 'vazio')

    # ------------------------------------------------------------------ torre de filtragem: gavetas de filtros plissados
    TX0, TX1, TY0, TY1 = -0.7, 0.3, -0.25, 0.42
    NIV = (0.84, 1.06, 1.28, 1.5)
    HG = 0.2
    bm = bmesh.new()
    caixa_de(bm, (TX0 - 0.02, TY0 - 0.02, PZ), (TX1 + 0.02, TY1 + 0.02, PZ + 0.03))
    caixa_de(bm, (TX0 - 0.03, TY0 - 0.03, 1.72), (TX1 + 0.03, TY1 + 0.03, 1.77))
    caixa_de(bm, (TX0, TY0 + 0.04, PZ), (TX1, TY1, 1.72))                        # corpo (trás das gavetas)
    obj('torre_corpo', bm, 'grafite')
    bm = bmesh.new()
    for x in (TX0 - 0.03, (TX0 + TX1) / 2 - 0.015, TX1):
        for y in (TY0 - 0.03, TY1):
            caixa_de(bm, (x, y, PZ), (x + 0.03, y + 0.03, 1.77))
    for z in NIV:
        caixa_de(bm, (TX0 - 0.03, TY0 - 0.035, z - 0.025), (TX1 + 0.03, TY0 - 0.005, z - 0.01))
    obj('torre_colunas', bm, 'amarelo')

    def gaveta(x0, x1, y0, z0, mat, saida=0.0, nome='gaveta'):
        """Gaveta de filtro: moldura de ferro, pacote plissado em zigue-zague na frente, alça."""
        y0 = y0 - saida
        bm = bmesh.new()
        caixa_de(bm, (x0, y0, z0), (x1, y0 + 0.02, z0 + 0.015))
        caixa_de(bm, (x0, y0, z0 + HG - 0.015), (x1, y0 + 0.02, z0 + HG))
        caixa_de(bm, (x0, y0, z0), (x0 + 0.015, y0 + 0.02, z0 + HG))
        caixa_de(bm, (x1 - 0.015, y0, z0), (x1, y0 + 0.02, z0 + HG))
        if saida > 0:                                                        # laterais à mostra da gaveta puxada
            for x in (x0, x1 - 0.012):
                caixa_de(bm, (x, y0, z0), (x + 0.012, y0 + saida + 0.03, z0 + HG))
        obj(nome + '_moldura', bm, 'ferro')
        bm = bmesh.new()
        n = int((x1 - x0 - 0.03) / 0.016)
        cols = []
        for i in range(n + 1):
            x = x0 + 0.015 + (x1 - x0 - 0.03) * i / n
            y = y0 + 0.006 + (0.045 if i % 2 else 0.0)
            cols.append((bm.verts.new((x, y, z0 + 0.015)), bm.verts.new((x, y, z0 + HG - 0.015))))
        for i in range(n):
            bm.faces.new((cols[i][0], cols[i + 1][0], cols[i + 1][1], cols[i][1]))
        for pg in bm.faces:
            pg.smooth = False
        obj(nome + '_plissado', bm, mat)
        bm = bmesh.new()
        xm = (x0 + x1) / 2
        for sx in (-1, 1):
            viga(bm, Vector((xm + sx * 0.06, y0, z0 + HG / 2)), Vector((xm + sx * 0.06, y0 - 0.035, z0 + HG / 2)), 0.012)
        viga(bm, Vector((xm - 0.066, y0 - 0.035, z0 + HG / 2)), Vector((xm + 0.066, y0 - 0.035, z0 + HG / 2)), 0.012)
        obj(nome + '_alca', bm, 'ferro')
    xm = (TX0 + TX1) / 2
    SUJ = {(0, 0): 'plis_saturado', (0, 1): 'plis_saturado', (1, 0): 'plis_sujo', (1, 1): 'plis_saturado',
           (2, 0): 'plis_sujo', (2, 1): 'plis_sujo', (3, 0): 'plis_sujo', (3, 1): 'plis_saturado'}
    for j, z in enumerate(NIV):
        for i, (x0, x1) in enumerate(((TX0, xm - 0.01), (xm + 0.01, TX1))):
            gaveta(x0, x1, TY0, z, SUJ[(j, i)], 0.2 if (j, i) == (3, 1) else 0.0)
            numero(B_NUM, Vector((x0 + 0.06, TY0 - (0.2 if (j, i) == (3, 1) else 0) - 0.001, z + HG - 0.03)), -EY, 'F%d%d' % (j + 1, i + 1), 0.025, 0.2)
    bm = bmesh.new()                                                           # trilhos e pistões que puxam a gaveta para troca
    G3 = (xm + 0.01, TX1, NIV[3])
    for x in (G3[0] + 0.005, G3[1] - 0.005):
        caixa_de(bm, (x - 0.006, TY0 - 0.26, G3[2] - 0.012), (x + 0.006, TY0, G3[2]))
    obj('trilhos', bm, 'aco')
    bm = bmesh.new()
    for sx in (-1, 1):
        caixa_de(bm, (xm + 0.25 + sx * 0.23 - 0.015, TY0 - 0.27, G3[2] - 0.06), (xm + 0.25 + sx * 0.23 + 0.015, TY0 - 0.24, G3[2] - 0.01))
    obj('trilhos_ponta', bm, 'amarelo')
    bm = bmesh.new()                                                           # crosta de fuligem nas frentes e no chão do nível
    for j, z in enumerate(NIV):
        for k in range(22):
            x = random.uniform(TX0 + 0.02, TX1 - 0.02)
            gota(bm, (x, TY0 - 0.012 - (0.2 if (j == 3 and x > xm) else 0), z + random.uniform(0.0, 0.03)), random.uniform(0.005, 0.014), 0.6)
    poeira(bm, TX0, TX1, TY0 - 0.03, TY1, 1.775, 70, 0.006, 0.016)
    poeira(bm, PX0, PX1, PY0, PY1, PZ + 0.03, 60, 0.006, 0.016)
    obj('fuligem_torre', bm, 'fuligem')
    for z in NIV:
        dfu.quad(Vector((xm, TY0 - 0.036, z - 0.018)), -EY, 1.0, 0.07, up=-EZ, off=0.0)
    for x in (TX0 - 0.03, TX1 + 0.03):
        dfu.quad(Vector((x, (TY0 + TY1) / 2, 1.3)), EX if x > 0 else -EX, 0.5, 0.8, off=0.0015)
    dfe.quad(Vector((TX1 + 0.03, 0.0, 1.2)), EX, 0.08, 0.6)
    remendo(B_TROCA, B_PAR, Vector((TX0 - 0.031, 0.1, 1.15)), -EX, 0.25, 0.3)        # chapa lateral trocada (primer)
    numero(B_NUM, Vector((TX1 + 0.031, 0.28, 1.6)), EX, '0283-4', 0.04, 0.35)
    # caixas de sensor de pressão diferencial com mangueirinhas, uma por nível
    bm, bl, bmg = bmesh.new(), bmesh.new(), bmesh.new()
    for j, z in enumerate(NIV):
        p = Vector((TX1 + 0.03, TY1 - 0.06, z + 0.1))
        caixa(bm, p + Vector((0.025, 0, 0)), (0.05, 0.06, 0.07))
        caixa(bl, p + Vector((0.051, 0.0, 0.02)), (0.002, 0.012, 0.008))
        mangueira(bmg, bezier(p + Vector((0.03, -0.03, -0.03)), p + Vector((0.06, -0.08, -0.06)), p + Vector((0.02, -0.15, -0.05)), Vector((TX1 + 0.03, TY1 - 0.24, z + 0.06)), 8), 0.004)
    obj('sensores_dp', bm, 'grafite')
    obj('sensores_led', bl, 'led_verm')
    obj('sensores_mang', bmg, 'borracha')

    # ------------------------------------------------------------------ lavador (coluna de borrifo com visor)
    LV = Vector((0.7, 0.2, 0))
    RL = 0.22
    ZJ0, ZJ1 = 0.42, 1.18                    # janela
    AJ0, AJ1 = -PI / 2 - 0.75, -PI / 2 + 0.75

    def casca(bm, c, r, z0, z1, a0, a1, nseg=40):
        vs = []
        for i in range(nseg + 1):
            a = a0 + (a1 - a0) * i / nseg
            d = Vector((math.cos(a), math.sin(a), 0))
            vs.append((bm.verts.new(c + d * r + Vector((0, 0, z0))), bm.verts.new(c + d * r + Vector((0, 0, z1)))))
        for i in range(nseg):
            bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
    bm = bmesh.new()
    cil(bm, LV + Vector((0, 0, 0.195)), RL + 0.03, 0.23, lados=40)              # tanque de base (sump)
    cil(bm, LV + Vector((0, 0, (0.31 + ZJ0) / 2)), RL, ZJ0 - 0.31, lados=40)
    casca(bm, LV, RL, ZJ0, ZJ1, AJ1, AJ0 + 2 * PI)
    cil(bm, LV + Vector((0, 0, (ZJ1 + 1.55) / 2)), RL, 1.55 - ZJ1, lados=40)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=RL, radius2=0.1, depth=0.15, matrix=Matrix.Translation(LV + Vector((0, 0, 1.625))))
    suavizar(obj('lavador', bm, 'casco'))
    bm = bmesh.new()
    casca(bm, LV, RL - 0.006, ZJ0, ZJ1, AJ1, AJ0 + 2 * PI)
    for pg in bm.faces:
        pg.normal_flip()
    obj('lavador_dentro', bm, 'ferro')
    bm = bmesh.new()
    casca(bm, LV, RL + 0.002, ZJ0 + 0.01, ZJ1 - 0.01, AJ0, AJ1)
    obj('lavador_vidro', bm, 'vidro')
    bm = bmesh.new()
    for z in (0.31, ZJ0, ZJ1, 1.55):
        cil(bm, LV + Vector((0, 0, z)), RL + 0.016, 0.025, lados=40)
    for a in (AJ0, AJ1):
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(bm, LV + d * (RL + 0.008) + Vector((0, 0, (ZJ0 + ZJ1) / 2)), (0.025, 0.025, ZJ1 - ZJ0), Matrix.Rotation(a, 3, 'Z'))
    obj('lavador_aros', bm, 'amarelo')
    bm = bmesh.new()                                                            # água preta no fundo, com espuma suja
    cil(bm, LV + Vector((0, 0, 0.47)), RL - 0.008, 0.01, lados=40)
    obj('lavador_agua', bm, 'borra')
    bm = bmesh.new()
    for k in range(40):
        a = random.uniform(0, 2 * PI)
        r_ = math.sqrt(random.random()) * (RL - 0.02)
        gota(bm, LV + Vector((math.cos(a) * r_, math.sin(a) * r_, 0.476)), random.uniform(0.006, 0.016), 0.5)
    obj('lavador_espuma', bm, 'plis_sujo')
    bm = bmesh.new()                                                            # anel de bicos de borrifo
    toro(bm, LV + Vector((0, 0, 1.12)), 0.13, 0.014, 40, 8)
    for k in range(8):
        a = k * PI / 4
        cil(bm, LV + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, 1.095)), 0.012, 0.03, lados=8)
    viga(bm, LV + Vector((0, 0.13, 1.12)), LV + Vector((0, RL, 1.12)), 0.025)
    obj('bicos', bm, 'aco')
    gotas = []
    for k in range(8):                                                           # chuveiro de gotas (cones)
        a = k * PI / 4
        bico = LV + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, 1.075))
        for j in range(26):
            u = random.random()
            dirx = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0))
            bm = bmesh.new()
            esfera(bm, (0, 0, 0), random.uniform(0.004, 0.008), 6)
            o = obj('gota', bm, 'gotas')
            gotas.append((o, bico, dirx, random.random()))
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    nv = obj('nevoa_lavador', bm, 'nevoa')
    nv.location = LV + Vector((0, 0, 0.78))
    nv.scale = (RL - 0.03, RL - 0.03, 0.34)
    luz = bpy.data.lights.new('Luz lavador', 'POINT')                         # luz de inspeção dentro da coluna
    luz.color = (1.0, 0.85, 0.65)
    luz.energy = 0.0
    luz.shadow_soft_size = 0.12
    lo = bpy.data.objects.new('Luz lavador', luz)
    sc.collection.objects.link(lo)
    lo.location = LV + Vector((0, 0.08, 0.95))
    # chaminé de ar limpo com difusor e leve brilho
    bm = bmesh.new()
    cil(bm, LV + Vector((0, 0, 1.97)), 0.1, 0.6, lados=28)
    suavizar(obj('chamine', bm, 'casco'))
    bm = bmesh.new()
    for z in (1.72, 2.0, 2.26):
        cil(bm, LV + Vector((0, 0, z)), 0.115, 0.02, lados=28)
    toro(bm, LV + Vector((0, 0, 2.27)), 0.1, 0.012, 32, 8)
    for k in range(3):                                                         # estais
        a = PI / 6 + k * 2 * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        viga(bm, LV + d * 0.11 + Vector((0, 0, 2.1)), LV + d * (RL + 0.01) + Vector((0, 0, 1.56)), 0.012)
    obj('chamine_aros', bm, 'ferro')
    bm = bmesh.new()
    toro(bm, LV + Vector((0, 0, 2.285)), 0.1, 0.006, 32, 6)
    obj('chamine_led', bm, 'led')
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    ar = obj('ar_limpo', bm, 'ar_limpo')
    ar.location = LV + Vector((0.03, 0.0, 2.6))
    ar.scale = (0.2, 0.2, 0.38)
    luz = bpy.data.lights.new('Brilho ar', 'POINT')
    luz.color = (1.0, 0.92, 0.96)
    luz.energy = 3
    luz.shadow_soft_size = 0.2
    lo = bpy.data.objects.new('Brilho ar', luz)
    sc.collection.objects.link(lo)
    lo.location = LV + Vector((0, 0, 2.45))
    for a in (-PI / 2 + 1.0, 0.3, 1.6):
        dfe.cilindro(LV, RL, a, 0.6 if a > 0 else 1.2, 1.5, 0.07, off=0.003)
    dfe.cilindro(LV, RL + 0.03, -PI / 2 - 0.9, 0.09, 0.3, 0.1, off=0.003)
    dfu.cilindro(LV, 0.1, -PI / 2, 2.0, 2.26, 0.12, off=0.003)
    numero(B_NUM, LV + Vector((0.0, -RL - 0.017, 1.4)), -EY, 'L-2', 0.06, 0.15)
    bm = bmesh.new()                                                           # vazamento: gotejando da junta do sump
    for k in range(6):
        a = -PI / 2 + random.uniform(-1.2, 0.4)
        d = Vector((math.cos(a), math.sin(a), 0))
        escorrido(bm, LV + d * (RL + 0.03), d, 0.3, random.uniform(0.08, 0.2), random.uniform(0.01, 0.018))
    obj('lavador_vaza', bm, 'borra')
    # duto: topo da torre de filtros → desce ao norte → entra baixo no lavador
    E1 = Vector((0.1, 0.3, 1.77))
    DD = [E1, Vector((0.1, 0.3, 1.9)), Vector((0.1, 0.62, 1.9)), Vector((0.55, 0.62, 1.9)), Vector((0.55, 0.62, 0.6))]
    fimd = LV + (Vector((0.55, 0.62, 0)) - LV).normalized() * (RL - 0.01) + Vector((0, 0, 0.6))
    DD.append(fimd)
    bm = bmesh.new()
    cano(bm, DD, 0.075, 24)
    suavizar(obj('duto', bm, 'casco'))
    bm = bmesh.new()
    for a, b_ in zip(DD, DD[1:]):
        dd = (b_ - a)
        flange(bm, a + dd.normalized() * 0.02, dd, 0.092, 0.025, 24)
        flange(bm, a.lerp(b_, 0.5), dd, 0.088, 0.03, 24) if dd.length > 0.4 else None
    viga(bm, Vector((0.55, 0.62, 1.3)), Vector((0.45, 0.5, 1.3)), 0.025)            # escora no plenum/torre
    viga(bm, Vector((0.55, 0.62, 0.82)), Vector((0.55, 0.62, 0.08)), 0.04)
    caixa_de(bm, (0.5, 0.57, 0.08), (0.6, 0.67, 0.1))
    obj('duto_flanges', bm, 'ferro')
    dfe.quad(Vector((0.55, 0.62 - 0.076, 1.2)), -EY, 0.08, 0.5, off=0.002)
    dfu.quad(Vector((0.1, 0.62 - 0.076, 1.9)), -EY, 0.12, 0.1, off=0.002)

    # água: tanque, bomba e recalque até o anel de bicos; dreno até a bandeja de borra
    TQ = Vector((0.82, 0.8, 0))
    bm, ba = bmesh.new(), bmesh.new()
    tambor(bm, ba, TQ + Vector((0, 0, 0.36)), 0.14, 0.56)
    obj('tanque_agua', bm, 'tambor')
    obj('tanque_aros', ba, 'grafite')
    bm = bmesh.new()
    caixa_de(bm, (0.26, 0.74, 0.08), (0.46, 0.95, 0.22))
    cil(bm, Vector((0.36, 0.84, 0.29)), 0.06, 0.12, EX, lados=18)
    cil(bm, Vector((0.24, 0.84, 0.29)), 0.05, 0.12, EX, lados=18)
    obj('bomba', bm, 'grafite')
    bm = bmesh.new()
    cano(bm, [TQ + Vector((-0.14, 0.04, 0.2)), Vector((0.5, 0.84, 0.2)), Vector((0.5, 0.84, 0.29)), Vector((0.42, 0.84, 0.29))], 0.025, 14)
    cano(bm, [Vector((0.36, 0.84, 0.35)), Vector((0.36, 0.84, 1.12)), Vector((0.7, 0.84, 1.12)), Vector((0.7, LV.y + RL, 1.12))], 0.025, 14)
    suavizar(obj('canos_agua', bm, 'galvan'))
    bm = bmesh.new()
    cano(bm, [LV + Vector((0, RL + 0.03, 0.18)), Vector((0.7, 0.66, 0.18)), Vector((-0.25, 0.66, 0.18))], 0.03, 16)
    suavizar(obj('dreno', bm, 'casco'))
    bm = bmesh.new()
    for p, e in ((Vector((0.36, 0.84, 0.7)), EZ), (Vector((0.6, 0.84, 1.12)), EX), (Vector((0.2, 0.66, 0.18)), EX)):
        flange(bm, p, e, 0.04, 0.02, 14)
    caixa_de(bm, (0.33, 0.8, 0.86), (0.39, 0.88, 0.94))                          # válvula
    obj('canos_flanges', bm, 'ferro')
    bm = bmesh.new()                                                           # bandeja de decantação da borra (noroeste)
    BX0, BX1, BY0, BY1 = -0.85, -0.25, 0.6, 0.95
    caixa_de(bm, (BX0, BY0, 0.08), (BX1, BY0 + 0.02, 0.3))
    caixa_de(bm, (BX0, BY1 - 0.02, 0.08), (BX1, BY1, 0.3))
    caixa_de(bm, (BX0, BY0, 0.08), (BX0 + 0.02, BY1, 0.3))
    caixa_de(bm, (BX1 - 0.02, BY0, 0.08), (BX1, BY1, 0.3))
    obj('bandeja', bm, 'silo' if 'silo' in base3d.M else 'grafite')
    bm = bmesh.new()
    caixa_de(bm, (BX0 + 0.02, BY0 + 0.02, 0.09), (BX1 - 0.02, BY1 - 0.02, 0.26))
    obj('bandeja_agua', bm, 'agua_preta')
    bm = bmesh.new()
    mancha(bm, (-0.5, 0.78), 0.14, 0.262)
    mancha(bm, (-0.7, 0.7), 0.07, 0.262)
    obj('bandeja_borra', bm, 'borra')
    bm = bmesh.new()
    for x in (BX0, BX1):
        for y in (BY0, BY1):
            caixa_de(bm, (x - 0.015, y - 0.015, 0.08), (x + 0.015, y + 0.015, 0.32))
    obj('bandeja_cantos', bm, 'amarelo')
    # cabos: armário (oeste do plenum) → motores dos ventiladores e berço do cristal, em eletrocalha no chão
    bm = bmesh.new()
    caixa_de(bm, (-0.98, 0.0, 0.08), (-0.88, 0.45, 0.7))
    obj('armario', bm, 'grafite')
    bm = bmesh.new()
    caixa_de(bm, (-0.981, 0.03, 0.4), (-0.979, 0.42, 0.66))
    obj('armario_tampa_aberta', bm, 'vazio')
    bf = [bmesh.new(), bmesh.new(), bmesh.new()]
    fiacao(bf, Vector((-0.985, 0.1, 0.6)), Vector((-0.985, 0.35, 0.45)), 0.1, 6, 0.005)
    for b_, m_ in zip(bf, ('fio_verm', 'fio_azul', 'cobre')):
        obj('armario_fios', b_, m_)
    bm = bmesh.new()
    caixa_de(bm, (-0.97, -0.62, 0.08), (-0.91, 0.0, 0.11))                       # eletrocalha
    caixa_de(bm, (-0.97, -0.68, 0.08), (-0.2, -0.62, 0.11))
    obj('eletrocalha', bm, 'galvan')
    bm = bmesh.new()
    for k in range(3):
        mangueira(bm, [Vector((-0.94 + k * 0.012, y, 0.115)) for y in (0.0, -0.3, -0.64)] + [Vector((-0.6, -0.65 + k * 0.012, 0.115)), Vector((-0.24, -0.65 + k * 0.012, 0.115))], 0.008)
    for fx in FANS:                                                              # cabo sobe pela parede até o motor
        mangueira(bm, bezier(Vector((fx, PY0 - 0.01, 0.12)), Vector((fx, PY0 - 0.04, 0.15)), Vector((fx, PY0 - 0.03, FZ - FR - 0.05)), Vector((fx, PY0 - 0.025, FZ - FR + 0.01)), 10), 0.008)
    obj('cabos', bm, 'borracha')

    # ------------------------------------------------------------------ cristal da IA que atrai a fuligem em fios
    CR = Vector((-0.2, -0.78, 0.66))
    bm = bmesh.new()
    caixa_de(bm, (CR.x - 0.08, CR.y - 0.08, 0.08), (CR.x + 0.08, CR.y + 0.08, 0.16))
    caixa_de(bm, (CR.x - 0.03, CR.y - 0.03, 0.16), (CR.x + 0.03, CR.y + 0.03, 0.44))
    obj('mastro', bm, 'grafite')
    bm = bmesh.new()
    cil(bm, Vector((CR.x, CR.y, 0.455)), 0.075, 0.03, lados=24)
    toro(bm, Vector((CR.x, CR.y, 0.47)), 0.08, 0.01, 32, 8)
    obj('berco', bm, 'amarelo')
    garras = []
    for k in range(3):
        a = PI / 2 + k * 2 * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        g = vazio('garra', None, Vector((CR.x, CR.y, 0.47)) + d * 0.07)
        g.rotation_euler = (0, 0, a)
        bm = bmesh.new()                                                       # dedo em L: sobe e se curva até o cristal
        viga(bm, Vector((0, 0, 0)), Vector((0.035, 0, 0.1)), 0.022)
        viga(bm, Vector((0.035, 0, 0.1)), Vector((-0.008, 0, 0.16)), 0.018)
        caixa(bm, Vector((-0.012, 0, 0.16)), (0.012, 0.03, 0.045))
        cil(bm, Vector((0, 0, 0)), 0.014, 0.04, EY, lados=10)
        caixa(bm, Vector((0.068, 0, -0.004)), (0.03, 0.02, 0.02))
        obj('garra', bm, 'amarelo', g)
        bm = bmesh.new()
        cil(bm, Vector((0.035, 0, 0.1)), 0.012, 0.035, EY, lados=10)
        caixa(bm, Vector((-0.02, 0, 0.16)), (0.004, 0.024, 0.036))
        obj('garra_junta', bm, 'aco', g)
        cp, hp = pistao('pg%d' % k, g, 0.06, 0.06, 0.011, 'grafite')
        garras.append((g, cp, hp))
    bm = bmesh.new()                                                           # cristal hexagonal com pontas
    bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.045, radius2=0.045, depth=0.2, matrix=Matrix.Translation(CR))
    bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.045, radius2=0.0, depth=0.07, matrix=Matrix.Translation(CR + Vector((0, 0, 0.135))))
    bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=0.0, radius2=0.045, depth=0.06, matrix=Matrix.Translation(CR + Vector((0, 0, -0.13))))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    obj('cristal', bm, 'cristal')
    bm = bmesh.new()
    for k in range(5):                                                           # cristais menores brotando
        a = random.uniform(0, 2 * PI)
        d = Vector((math.cos(a), math.sin(a), 0.6)).normalized()
        q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.012, radius2=0.0, depth=0.05,
                              matrix=Matrix.Translation(Vector((CR.x, CR.y, 0.475)) + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.0)) + d * 0.02) @ q)
    obj('cristais_menores', bm, 'cristal')
    luz = bpy.data.lights.new('Cristal', 'POINT')
    luz.color = (0.6, 0.25, 1.0)
    luz.energy = 10
    luz.shadow_soft_size = 0.05
    lo = bpy.data.objects.new('Cristal', luz)
    sc.collection.objects.link(lo)
    lo.location = CR + Vector((0, -0.08, 0))
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    cc = obj('campo_cristal', bm, 'campo')
    cc.location = CR
    cc.scale = (0.16, 0.16, 0.2)
    bm = bmesh.new()                                                           # fuligem já presa em volta do cristal e no berço
    for k in range(26):
        a = random.uniform(0, 2 * PI)
        gota(bm, Vector((CR.x + math.cos(a) * 0.075, CR.y + math.sin(a) * 0.075, 0.475)), random.uniform(0.006, 0.014), 0.6)
    for k in range(12):
        a = random.uniform(0, 2 * PI)
        z = random.uniform(-0.08, 0.1)
        gota(bm, CR + Vector((math.cos(a) * 0.047, math.sin(a) * 0.047, z)), random.uniform(0.004, 0.009), 0.8)
    poeira(bm, CR.x - 0.08, CR.x + 0.08, CR.y - 0.08, CR.y + 0.08, 0.162, 15)
    obj('cristal_fuligem', bm, 'fuligem')
    numero(B_NUM, Vector((CR.x, CR.y - 0.081, 0.12)), -EY, 'C-1', 0.03, 0.2)

    # fumaça escura entrando: correntes de bolhas puxadas pelos ventiladores
    fumacas = []
    CAMS = []
    for i, fx in enumerate(FANS):
        for f in range(2):
            if i == 0:
                S = Vector((fx - 0.9 - 0.7 * f, -2.2 - 0.3 * f, 0.6 + 0.35 * f))
            else:
                S = Vector((1.5 + 0.5 * f, -1.7 - 0.5 * f, 0.7 + 0.3 * f))
            cam = bezier(S, S + (Vector((fx, YF - 0.7, FZ)) - S) * 0.45 + Vector((0, 0, 0.12)), Vector((fx, YF - 0.6, FZ + 0.04)), Vector((fx, YF - 0.05, FZ)), 40)
            CAMS.append(cam)
            for k in range(11):
                bm = bmesh.new()
                bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
                o = obj('fumaca', bm, 'fumaca')
                fumacas.append((o, cam, k / 11 + random.uniform(0, 0.03), random.uniform(0.85, 1.15)))
    for k in range(5):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        o = obj('neblina', bm, 'neblina')
        o.location = (random.uniform(-2.2, 1.2), random.uniform(-3.2, -2.2), random.uniform(0.4, 0.9))
        o.scale = (random.uniform(0.6, 0.9), random.uniform(0.5, 0.7), random.uniform(0.35, 0.5))
    # fios de fuligem: saem da fumaça e convergem no cristal
    fios = []
    for k in range(16):
        cs = CAMS[k % len(CAMS)]
        G = cs[random.randint(8, 26)] + Vector((random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08)))
        M = CR + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), random.uniform(-0.08, 0.08)))
        dirg = (G - M).normalized()
        lat = dirg.cross(EZ).normalized()
        up = lat.cross(dirg)
        cam = bezier(G, G - dirg * 0.2 + lat * random.uniform(-0.25, 0.25) + up * random.uniform(-0.15, 0.15),
                     M + dirg * 0.2 + lat * random.uniform(-0.12, 0.12), M + dirg * 0.05, 48)
        ond, amp = random.uniform(0, 6), random.uniform(0.01, 0.025)
        cam = [p + (lat * math.sin(i * 0.4 + ond) + up * math.cos(i * 0.31 + ond)) * amp * math.sin(PI * i / 48) for i, p in enumerate(cam)]
        fios.append(cam)
        bm = bmesh.new()
        tubo_curvo(bm, cam, lambda u: 0.0012 + 0.0035 * math.sin(PI * min(1.0, u * 1.15)) ** 0.6, 8, passo=0.01)
        suavizar(obj('fio_fuligem', bm, 'fio_fuligem'))
    contas = []
    for k in range(len(fios) * 4):
        bm = bmesh.new()
        gota(bm, (0, 0, 0), random.uniform(0.005, 0.012), 0.8)
        contas.append((obj('conta', bm, 'fuligem'), fios[k % len(fios)], (k // len(fios)) / 4 + random.uniform(0, 0.08)))

    # ------------------------------------------------------------------ filtros saturados no palete (troca) e um novo
    PL = Vector((0.74, -0.68, 0))
    bm = bmesh.new()
    caixa_de(bm, (PL.x - 0.25, PL.y - 0.3, 0.08), (PL.x + 0.25, PL.y + 0.3, 0.1))
    for y in (-0.27, 0.0, 0.27):
        caixa_de(bm, (PL.x - 0.25, PL.y + y - 0.03, 0.1), (PL.x + 0.25, PL.y + y + 0.03, 0.14))
    caixa_de(bm, (PL.x - 0.25, PL.y - 0.3, 0.14), (PL.x + 0.25, PL.y + 0.3, 0.16))
    obj('palete', bm, 'primer')

    def pacote(nome, c, rotz, mat, incl=0.0, ry=0.0):
        """Pacote de filtro solto (moldura + plissado nas duas faces largas)."""
        R = Matrix.Rotation(rotz, 3, 'Z') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(incl, 3, 'X')
        w, dd, h = 0.46, 0.5, 0.19
        bm = bmesh.new()
        for sx in (-1, 1):
            caixa(bm, Vector(c) + R @ Vector((sx * (w / 2 - 0.008), 0, 0)), (0.016, dd, h), R)
        for sy in (-1, 1):
            caixa(bm, Vector(c) + R @ Vector((0, sy * (dd / 2 - 0.008), 0)), (w, 0.016, h), R)
        obj(nome + '_moldura', bm, 'ferro')
        bm = bmesh.new()
        n = 22
        for i in range(n):
            x = -w / 2 + 0.016 + (w - 0.032) * (i + 0.5) / n
            caixa(bm, Vector(c) + R @ Vector((x, 0, 0)), (0.008, dd - 0.03, h - 0.03), R @ Matrix.Rotation(0.0, 3, 'Z'))
        caixa(bm, Vector(c), (w - 0.03, dd - 0.03, h - 0.06), R)
        obj(nome + '_pacote', bm, mat)
    pacote('sat1', PL + Vector((0.0, 0.0, 0.255)), 0.04, 'plis_saturado')
    pacote('sat2', PL + Vector((0.02, -0.02, 0.445)), -0.1, 'plis_saturado')
    pacote('novo', PL + Vector((-0.02, 0.03, 0.635)), 0.12, 'plis_limpo')
    pacote('sat3', Vector((0.72, -0.2, 0.35)), 0.0, 'plis_saturado', incl=PI / 2 - 0.35)   # encostado no lavador
    bm = bmesh.new()                                                           # monte de fuligem caída dos filtros
    for k in range(70):
        a = random.uniform(0, 2 * PI)
        r_ = random.expovariate(6.0)
        gota(bm, (PL.x + math.cos(a) * (0.27 + r_ * 0.5), PL.y + math.sin(a) * (0.32 + r_ * 0.3), 0.082), random.uniform(0.012, 0.035), 0.35)
    for k in range(40):
        gota(bm, (PL.x + random.uniform(-0.23, 0.23), PL.y + random.uniform(-0.25, 0.25), 0.735), random.uniform(0.006, 0.016), 0.35)
    for k in range(50):
        gota(bm, (random.uniform(PX0, PX1), random.uniform(-0.62, -0.42), 0.082), random.uniform(0.008, 0.025), 0.3)
    obj('fuligem_chao', bm, 'fuligem')
    bm = bmesh.new()
    numero(bm, Vector((PL.x, PL.y - 0.301, 0.12)), -EY, 'SAT-3', 0.035, 0.2)
    obj('palete_num', bm, 'stencil')
    bm = bmesh.new()                                                           # etiqueta âmbar de troca nos saturados
    caixa(bm, PL + Vector((0.1, -0.256, 0.26)), (0.05, 0.004, 0.03))
    caixa(bm, PL + Vector((-0.05, -0.27, 0.45)), (0.05, 0.004, 0.03), Matrix.Rotation(-0.1, 3, 'Z'))
    obj('etiquetas', bm, 'led_ambar')

    # laje e chão: fuligem assentada em leque diante dos ventiladores; cinza fina em volta
    def sujeira(x, y):
        d = math.hypot(x, y)
        s = 0.0
        if y < -0.9:
            for fx in FANS:
                lx = abs(x - fx)
                w = 0.35 + (-0.9 - y) * 0.35
                s = max(s, (1 - sst(w * 0.6, w, lx + 0.06 * noise.noise(Vector((x * 6, y * 6, 1.0))))) * (1 - sst(1.5, 2.6, -y)))
        dens = noise.noise(Vector((x * 1.6, y * 1.6, 5.0))) * 0.5 + noise.noise(Vector((x * 6, y * 6, 2.0))) * 0.25
        s = max(s * sst(-0.25, 0.1, dens + 0.15), 0.0)
        c = sst(-0.06, 0.06, dens - (-0.15 + (d - 1.3) * 0.3)) * (1 - s)
        return s, c, 0.0
    chao_grade(sujeira)
    bm = bmesh.new()
    for c, r in (((-1.5, 0.9), 0.14), ((1.6, 1.2), 0.1), ((0.2, 0.75), 0.06), ((-0.6, -0.5), 0.07)):
        mancha_lisa(bm, c, r, 0.0095 if max(abs(c[0]), abs(c[1])) > 1 else 0.0822)
    obj('oleo_pocas', bm, 'oleo')

    obj('remendos', B_REM, 'galvan')
    obj('remendos_primer', B_REMP, 'primer')
    obj('pecas_trocadas', B_TROCA, 'primer')
    obj('parafusos_remendo', B_PAR, 'aco')
    obj('numeros', B_NUM, 'stencil')
    suave_tudo(obj('chapa_amassada', B_AMAS, 'grafite'))
    for dc, nome in ((dfu, 'd_fuligem'), (dfe, 'd_ferrugem'), (dol, 'd_oleo'), (dpo, 'd_poeira')):
        dc.fim(nome)

    # ------------------------------------------------------------------ animação
    for q in range(1, QUADROS + 1):
        fr = (q - 1) / QUADROS
        for k, ro in enumerate(rot_fans):
            ro.rotation_euler = (0, 2 * PI * 6 * fr * (1 if k else -1), 0)
            ro.keyframe_insert('rotation_euler', frame=q)
        for o, cam, u0, s in fumacas:
            u = (u0 + fr) % 1.0
            idx = u * (len(cam) - 1)
            k0 = int(idx)
            p = cam[k0].lerp(cam[min(k0 + 1, len(cam) - 1)], idx - k0)
            t = (cam[min(k0 + 1, len(cam) - 1)] - cam[max(k0 - 1, 0)]).normalized()
            o.location = p
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = t.to_track_quat('Z', 'Y')
            r = s * (0.3 - 0.18 * u)
            o.scale = (r, r, r * (1.4 + 0.8 * u))
            for c in ('location', 'rotation_quaternion', 'scale'):
                o.keyframe_insert(c, frame=q)
        for o, cam, u0 in contas:
            u = (u0 + fr * 2) % 1.0
            idx = u * (len(cam) - 1)
            k0 = int(idx)
            o.location = cam[k0].lerp(cam[min(k0 + 1, len(cam) - 1)], idx - k0)
            o.scale = [max(0.05, 1.0 - 0.6 * u)] * 3
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('scale', frame=q)
        for o, bico, dirx, u0 in gotas:
            u = (u0 + fr * 3) % 1.0
            o.location = bico + dirx * 0.1 * u + Vector((0, 0, -0.6 * u * (0.6 + 0.4 * u)))
            o.scale = (1, 1, 1.8)
            o.keyframe_insert('location', frame=q)
        em = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        em.default_value = 3.5 + 3 * math.sin(2 * PI * 2 * fr) ** 2
        em.keyframe_insert('default_value', frame=q)
        for k, (g, cp, hp) in enumerate(garras):
            g.rotation_euler = (0, 0.04 * math.sin(2 * PI * fr + k), g.rotation_euler[2])
            g.keyframe_insert('rotation_euler', frame=q)
            # pistão da garra: base no berço (fora), ponta no meio do dedo — no quadro da garra
            pistao_por(cp, hp, Vector((0.075, 0, 0.0)), Vector((0.03, 0, 0.088)), q)
    linear_keys()
    cena_final((0.0, -0.15, 0.85), ((300, 5.6, 2.3, 32),), 'purificador_ar',
               ((0.75, -2.4, 1.25), (-0.1, -0.5, 0.65), 30),
               ((2.7, 0.9, 1.6), (0.5, 0.2, 1.0), 30))


qual = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else 'ambos'
if qual in ('coletor', 'ambos'):
    coletor_lixo_2()
if qual in ('purificador', 'ambos'):
    purificador_ar()
print('LIMPEZA ok')
