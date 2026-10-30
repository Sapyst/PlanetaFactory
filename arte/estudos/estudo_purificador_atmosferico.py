"""Estudo isolado (fora do jogo): PURIFICADOR ATMOSFÉRICO da IA (purificador_ar_2), 3×3 tiles, absorve 40 de
poluição/min. Versão grande e avançada do purificador de ar.
Estrutura: torre de tiragem alta em hiperboloide (resfriamento invertido: puxa o ar sujo por baixo e solta o limpo
por cima). Treliça de cantoneiras de aço em duas famílias retas cruzadas (tipo Shukhov), anéis de aperto por fora,
painéis de chapa por dentro (alguns faltando, alguns trocados em primer, remendos aparafusados). Assenta em 8 pares
de pernas em V sobre sapatas; entre as pernas fica a boca de entrada. No topo, deque de grade com três ventiladores
grandes em virolas com motor na ponte e grade de proteção, girando.
Funil de fumaça: a fumaça escura do ambiente é puxada de longe em espiral logarítmica (volume procedural em
coordenadas polares) que desce e afunila até a boca entre as pernas; por dentro, três braços menores enrolam até o
cristal.
Base: dois armários de filtros de carvão ativado em módulos (cassetes empilhados, face em colmeia preta) nas quinas
sul; lavador de gás (coluna com câmara de vidro, chuveiros em anel e névoa) na quina NE com bomba de recirculação;
tanque de lama negra aberto na quina NO alimentado pela bomba de lama. Um coletor em arco em volta do núcleo
alimenta os filtros e o lavador; os três devolvem o gás para dentro da torre por dutos com moldura reforçada.
Toque da IA: núcleo de cristal violeta levitando entre quatro braços com cilindros hidráulicos e cabeças de bobina;
a poluição condensa em gotas negras que caem no funil da prensa e saem como blocos negros compactos (resíduo) por
uma comporta de guilhotina para a esteira que leva à borda sul (tile do meio).
Saída: ar limpo saindo por cima dos ventiladores com tremor de calor (refração) e cintilação (centelhas subindo).
Desgaste: fuligem pesada na metade de baixo da torre e na base, escorridos negros, ferrugem, remendos, peças trocadas.
Uso: blender -b --python estudo_purificador_atmosferico.py -- foto [0|perto|vortice]
     |  -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(47)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
print('INICIO', flush=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def base_de(eixo):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    return q @ X, q @ Y, q @ Z


def toro(bm, centro, R, r, eixo=Z, nR=48, nr=12, a0=0.0, a1=2 * PI):
    u, v, w = base_de(eixo)
    centro = Vector(centro)
    fechado = abs(a1 - a0 - 2 * PI) < 1e-6
    n = nR if fechado else nR + 1
    aneis = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / nR
        d = u * math.cos(a) + v * math.sin(a)
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + w * (r * math.sin(b)))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % n]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))
    if not fechado:
        bm.faces.new(aneis[0][::-1])
        bm.faces.new(aneis[-1])


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


def esfera(bm, c, r, seg=20, esc=(1, 1, 1)):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r,
                              matrix=Matrix.Translation(Vector(c)) @ Matrix.Diagonal((*esc, 1)))


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


def placa_rot(bm, a, b, larg, esp, cima=Z):
    """Chapa de a até b: 'esp' no eixo (dir × cima), 'larg' no eixo 'cima' corrigido."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    n = d.cross(Vector(cima)).normalized()
    w = n.cross(d)
    rot = Matrix((d, n, w)).transposed()
    caixa(bm, (a + b) / 2, ((b - a).length, esp, larg), rot)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def faixa(bm, uv, pts, normais, larg):
    """Fita (escorrido) por uma lista de pontos de cima para baixo, com UV v=1 em cima, v=0 embaixo."""
    vs = []
    for p, n in zip(pts, normais):
        t = n.cross(Z).normalized() if abs(n.dot(Z)) < 0.95 else X
        vs.append((bm.verts.new(p - t * larg / 2), bm.verts.new(p + t * larg / 2)))
    m = len(vs)
    for i in range(m - 1):
        f = bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
        for lo, (uu, vv) in zip(f.loops, ((0, 1 - i / (m - 1)), (0, 1 - (i + 1) / (m - 1)),
                                         (1, 1 - (i + 1) / (m - 1)), (1, 1 - i / (m - 1)))):
            lo[uv].uv = (uu, vv)


def escorrido_reto(bm, uv, topo, normal, larg, alt, n=4):
    topo, normal = Vector(topo), Vector(normal).normalized()
    faixa(bm, uv, [topo - Z * alt * k / n for k in range(n + 1)], [normal] * (n + 1), larg)


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


VIOLETA = (0.6, 0.3, 1.0)
FULIGEM = (0.012, 0.011, 0.01)


def fuliginar(m, faixas, forca=0.95, escala=3.0):
    """Fuligem pesada em manchas: mistura preto na cor base. faixas = [(z cheio, z limpo), ...] no mundo."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = b.inputs['Base Color']
    src = ent.links[0].from_socket if ent.links else None
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    tot = None
    for za, zb in faixas:
        mr = no(nt, 'ShaderNodeMapRange', **{'From Min': za, 'From Max': zb, 'To Min': 1.0, 'To Max': 0.0})
        nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
        if tot is None:
            tot = mr.outputs['Result']
        else:
            mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
            nt.links.new(tot, mx.inputs[0])
            nt.links.new(mr.outputs['Result'], mx.inputs[1])
            tot = mx.outputs['Value']
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 9.0, 'Roughness': 0.65})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    mr2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.32, 'From Max': 0.6, 'To Min': 0.45, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], mr2.inputs['Value'])
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(tot, f.inputs[0])
    nt.links.new(mr2.outputs['Result'], f.inputs[1])
    f2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    f2.inputs[1].default_value = forca
    nt.links.new(f.outputs['Value'], f2.inputs[0])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    if src is not None:
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = ent.default_value
    mix.inputs[7].default_value = (*FULIGEM, 1)
    nt.links.new(f2.outputs['Value'], mix.inputs[0])
    nt.links.new(mix.outputs[2], ent)
    return m


def escorrido_mat(nome, cor, alpha=0.9, brilho=0.8):
    """Escorrido em fita com UV: mais forte em cima (v=1), some embaixo e nas bordas, rasgado por ruído."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = brilho
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['UV'], sep.inputs[0])
    desce = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 1.0, 'To Min': 0.0, 'To Max': alpha})
    nt.links.new(sep.outputs['Y'], desce.inputs['Value'])
    borda = no(nt, 'ShaderNodeMath', operation='PINGPONG')       # 0 nas bordas, 0,5 no meio
    borda.inputs[1].default_value = 0.5
    nt.links.new(sep.outputs['X'], borda.inputs[0])
    bmr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.3})
    nt.links.new(borda.outputs['Value'], bmr.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 5.0})
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (6.0, 1.2, 1.0)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    corte = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.58})
    nt.links.new(ru.outputs['Fac'], corte.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(desce.outputs['Result'], m1.inputs[0])
    nt.links.new(corte.outputs['Result'], m1.inputs[1])
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(bmr.outputs['Result'], m2.inputs[1])
    nt.links.new(m2.outputs['Value'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def colmeia_mat():
    """Face do cassete de carvão ativado: colmeia de células pretas com grânulos, poeira cinza nas paredes."""
    m = bpy.data.materials.new('Colmeia de carvão')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    vo = no(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', **{'Scale': 140.0})
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    parede = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.03, 'From Max': 0.06})
    nt.links.new(vo.outputs['Distance'], parede.inputs['Value'])
    gr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 400.0, 'Detail': 2.0})
    nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
    cel = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cel.inputs[6].default_value = (0.025, 0.024, 0.024, 1)
    cel.inputs[7].default_value = (0.006, 0.006, 0.006, 1)
    nt.links.new(gr.outputs['Fac'], cel.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.09, 0.085, 0.08, 1)
    nt.links.new(parede.outputs['Result'], cor.inputs[0])
    nt.links.new(cel.outputs[2], cor.inputs[7])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.8})
    nt.links.new(parede.outputs['Result'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def bloco_mat():
    """Bloco de poluição compactada: preto fosco com veios violeta fracos (resto de campo) nas rachaduras."""
    m = bpy.data.materials.new('Bloco negro')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.012, 0.011, 0.012, 1)
    b.inputs['Roughness'].default_value = 0.42
    b.inputs['Emission Color'].default_value = (*VIOLETA, 1)
    tc = no(nt, 'ShaderNodeTexCoord')
    vo = no(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', **{'Scale': 22.0, 'Randomness': 1.0})
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    vr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 14.0, 'Detail': 3.0})       # só alguns veios acesos
    nt.links.new(tc.outputs['Object'], vr.inputs['Vector'])
    veio0 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.012, 'From Max': 0.0, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(vo.outputs['Distance'], veio0.inputs['Value'])
    msk = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.62, 'To Min': 0.0, 'To Max': 0.9})
    nt.links.new(vr.outputs['Fac'], msk.inputs['Value'])
    veio = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(veio0.outputs['Result'], veio.inputs[0])
    nt.links.new(msk.outputs['Result'], veio.inputs[1])
    nt.links.new(vo.outputs['Distance'], veio.inputs['Value'])
    nt.links.new(veio.outputs['Value'], b.inputs['Emission Strength'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def lodo_mat():
    m = bpy.data.materials.new('Lama negra')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.008, 0.008, 0.007, 1)
    b.inputs['Roughness'].default_value = 0.1
    b.inputs['Specular IOR Level'].default_value = 0.7
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Transmission Weight'].default_value = 0.45
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 3.0
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 60.0})
    tc = no(nt, 'ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def agua_mat(nome='Água', cor=(0.85, 0.93, 0.95), rough=0.02):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough
    b.inputs['IOR'].default_value = 1.33
    return m


def vidro_sujo_mat():
    """Vidro grosso da câmara do lavador: transparente com película de fuligem e gotas embaçadas."""
    m = bpy.data.materials.new('Vidro sujo')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.5
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    suj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.7, 'To Min': 0.12, 'To Max': 0.65})
    nt.links.new(ru.outputs['Fac'], suj.inputs['Value'])
    nt.links.new(suj.outputs['Result'], b.inputs['Roughness'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.85, 0.88, 0.86, 1)
    cor.inputs[7].default_value = (0.25, 0.23, 0.2, 1)
    nt.links.new(suj.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 140.0})
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.15})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def tremor_mat():
    """Tremor do ar limpo saindo: refração quase nula com ondulação forte (distorce o que está atrás)."""
    m = bpy.data.materials.new('Tremor do ar')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    g = no(nt, 'ShaderNodeBsdfRefraction')
    g.inputs['IOR'].default_value = 1.03
    g.inputs['Roughness'].default_value = 0.0
    g.inputs['Color'].default_value = (1, 1, 1, 1)
    tc = no(nt, 'ShaderNodeTexCoord')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (5.0, 5.0, 1.6)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 4.0})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 1.0, 'Distance': 0.3})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], g.inputs['Normal'])
    # bordas e pontas somem (transparente): não aparece como tubo de vidro
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    lw = no(nt, 'ShaderNodeLayerWeight', **{'Blend': 0.35})
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    pb = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.25, 'To Min': 1.0, 'To Max': 0.0})
    pt = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 1.0, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(sep.outputs['Z'], pb.inputs['Value'])
    nt.links.new(sep.outputs['Z'], pt.inputs['Value'])
    f1 = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(pb.outputs['Result'], f1.inputs[0])
    nt.links.new(pt.outputs['Result'], f1.inputs[1])
    f2 = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(f1.outputs['Value'], f2.inputs[0])
    nt.links.new(lw.outputs['Facing'], f2.inputs[1])
    f3 = no(nt, 'ShaderNodeMath', operation='POWER')
    f3.inputs[1].default_value = 0.6
    nt.links.new(f2.outputs['Value'], f3.inputs[0])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f3.outputs['Value'], mix.inputs[0])
    nt.links.new(g.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def ar_limpo_mat():
    """Coluna de ar limpo: volume quase transparente, branco-azulado, com brilho fraco; some ao subir."""
    m = base3d.volume_mat('Ar limpo', (0.82, 0.9, 1.0), 0.07, 5.5, 7.9)
    vol = next(n for n in m.node_tree.nodes if n.type == 'PRINCIPLED_VOLUME')
    vol.inputs['Emission Color'].default_value = (0.75, 0.88, 1.0, 1)
    vol.inputs['Emission Strength'].default_value = 0.08
    return m


def vortice_mat(nome, cor, dens, bracos, K, zc0, zc_incl, r_ref, w0, w_incl, r_in0, r_in1, r_out0, r_out1,
                em_r0=None, em_r1=None, em_forca=0.0, n_esc=1.2, zc_pot=1.0):
    """Fumaça em espiral logarítmica (coordenadas polares do objeto): braços = sin(bracos·θ + K·ln ρ), banda na
    altura zc(ρ) = zc0 + zc_incl·(ρ - r_ref)^pot com largura w0 + w_incl·ρ; some dentro de r_in e fora de r_out."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (*cor, 1)
    vol.inputs['Anisotropy'].default_value = 0.3
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])

    def op(o, a, b=None, nome_=None):
        n = no(nt, 'ShaderNodeMath', operation=o)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs['Value']

    def mr(v, a, b, c=0.0, d=1.0):
        n = no(nt, 'ShaderNodeMapRange', **{'From Min': a, 'From Max': b, 'To Min': c, 'To Max': d})
        nt.links.new(v, n.inputs['Value'])
        return n.outputs['Result']

    x, y, z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
    rho = op('SQRT', op('ADD', op('MULTIPLY', x, x), op('MULTIPLY', y, y)))
    rho_s = op('MAXIMUM', rho, 0.02)
    th = op('ARCTAN2', y, x)
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': n_esc, 'Detail': 5.0, 'Roughness': 0.6})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    fase = op('ADD', op('MULTIPLY', th, float(bracos)), op('MULTIPLY', op('LOGARITHM', rho_s, math.e), K))
    fase = op('ADD', fase, op('MULTIPLY', ru.outputs['Fac'], 2.2))
    banda = op('POWER', op('ADD', op('MULTIPLY', op('SINE', fase), 0.5), 0.5), 3.5)
    dr = op('MAXIMUM', op('SUBTRACT', rho, r_ref), 0.0)
    zc = op('ADD', op('MULTIPLY', op('POWER', dr, zc_pot), zc_incl), zc0)
    w = op('ADD', op('MULTIPLY', rho, w_incl), w0)
    dz = op('ABSOLUTE', op('SUBTRACT', z, zc))
    vert = op('SUBTRACT', 1.0, op('MINIMUM', op('DIVIDE', dz, w), 1.0))
    vert = op('POWER', vert, 1.6)
    rin = mr(rho, r_in0, r_in1)
    rout = mr(rho, r_out0, r_out1, 1.0, 0.0)
    ru2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': n_esc * 2.6, 'Detail': 7.0, 'Roughness': 0.62})
    nt.links.new(tc.outputs['Object'], ru2.inputs['Vector'])
    fiapo = mr(ru2.outputs['Fac'], 0.36, 0.66)
    forma = op('MULTIPLY', op('MULTIPLY', banda, vert), op('MULTIPLY', rin, rout))
    forma = op('MULTIPLY', forma, fiapo)
    forma = op('MULTIPLY', forma, mr(rho, r_out0, r_in1, 0.55, 1.6))            # mais densa perto da boca
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='dens')
    d.inputs[1].default_value = dens
    nt.links.new(forma, d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    if em_forca > 0:
        vol.inputs['Emission Color'].default_value = (*VIOLETA, 1)
        perto = mr(rho, em_r0, em_r1)
        e = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='brilho')
        e.inputs[1].default_value = em_forca
        nt.links.new(op('MULTIPLY', perto, forma), e.inputs[0])
        nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def chao_mat():
    """Terra seca com fuligem que o funil arrasta: manchas escuras em espiral perto da torre."""
    m = mats.material('Chão', (0.2, 0.16, 0.11), 0, 0.9, pintura=False, sujeira=0.3, desgaste=0.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = b.inputs['Base Color'].links[0].from_socket
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    x, y = sep.outputs['X'], sep.outputs['Y']

    def op(o, a, bb=None):
        n = no(nt, 'ShaderNodeMath', operation=o)
        for i, v in enumerate((a, bb)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs['Value']
    rho = op('MAXIMUM', op('POWER', op('ADD', op('MULTIPLY', x, x), op('MULTIPLY', y, y)), 0.5), 0.05)
    th = op('ARCTAN2', y, x)
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.5, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    fase = op('ADD', op('ADD', op('MULTIPLY', th, 3.0), op('MULTIPLY', op('LOGARITHM', rho, math.e), -5.5)),
              op('MULTIPLY', ru.outputs['Fac'], 4.0))
    banda = op('POWER', op('ADD', op('MULTIPLY', op('SINE', fase), 0.5), 0.5), 1.5)
    perto = no(nt, 'ShaderNodeMapRange', **{'From Min': 7.0, 'From Max': 1.5, 'To Min': 0.0, 'To Max': 0.9})
    nt.links.new(rho, perto.inputs['Value'])
    f = op('MULTIPLY', banda, perto.outputs['Result'])
    f = op('MINIMUM', op('ADD', f, op('MULTIPLY', perto.outputs['Result'], 0.35)), 0.95)
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    nt.links.new(src, mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.018, 0.016, 1)
    nt.links.new(f, mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    return m


def campo_linha_mat():
    m = bpy.data.materials.new('Linha de campo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*VIOLETA, 1)
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexWave', wave_type='RINGS')
    ru.inputs['Scale'].default_value = 2.0
    ru.inputs['Distortion'].default_value = 5.0
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.85, 'To Min': 0.0, 'To Max': 0.9})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    forca = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca')
    forca.inputs[1].default_value = 7.0
    nt.links.new(f.outputs['Result'], forca.inputs[0])
    nt.links.new(forca.outputs['Value'], em.inputs['Strength'])
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def stencil_mat():
    """Letreiro pintado à máscara, apagado: tinta preta que falha em manchas (mostra o fundo)."""
    m = bpy.data.materials.new('Estêncil')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    b.inputs['Roughness'].default_value = 0.7
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.55, 'To Min': 0.0, 'To Max': 0.85})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


ZB, ZT = 1.9, 4.9            # pé e topo da casca da torre
K_VORT = -11.0               # aperto da espiral do funil
base3d.M.update({
    'amarelo': fuliginar(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.9, ferrugem=0.5),
                         [(0.3, 2.6), (ZT + 0.6, ZT - 0.5)], 0.9),
    'grafite': fuliginar(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.35),
                         [(0.3, 2.0)], 0.6),
    'primer': fuliginar(mats.material('Primer', (0.36, 0.07, 0.04), 0, 0.7, desgaste=0.6, sujeira=0.8, ferrugem=0.3),
                        [(1.4, 3.2)], 0.8),
    'aco': fuliginar(mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.9, sujeira=0.85, escovado=True),
                     [(0.3, 2.4)], 0.85),
    'galv': fuliginar(mats.material('Galvanizado', (0.55, 0.56, 0.56), 1.0, 0.5, pintura=False, ferrugem=0.6, sujeira=0.85),
                      [(0.3, 2.4)], 0.85),
    'chapa': fuliginar(mats.material('Chapa da torre', (0.5, 0.5, 0.48), 1.0, 0.55, pintura=False, ferrugem=0.75, sujeira=0.9),
                       [(ZB, 3.5), (ZT + 0.2, ZT - 0.7)], 1.0, 2.2),
    'chapa_ferr': fuliginar(mats.material('Chapa enferrujada', (0.28, 0.13, 0.06), 0.6, 0.75, pintura=False, ferrugem=1.0, sujeira=0.9),
                            [(ZB, 3.2)], 0.8),
    'cano': fuliginar(mats.material('Cano', (0.30, 0.31, 0.32), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=0.9),
                      [(0.3, 2.2)], 0.7),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.95, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.45),
    'cobre': mats.material('Cobre', (0.78, 0.4, 0.22), 1.0, 0.32, pintura=False, sujeira=0.85, ferrugem=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.38, pintura=False, sujeira=0.8),
    'concreto': fuliginar(mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.8, desgaste=0.0),
                          [(0.0, 0.5)], 0.55, 1.4),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.018, 0.017, 0.016), 0, 0.95, pintura=False, sujeira=0.2, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'ponteiro': mats.material('Ponteiro', (0.5, 0.05, 0.02), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'verde_vel': mats.material('Verde velho', (0.12, 0.2, 0.12), 0, 0.55, desgaste=0.8, sujeira=0.85, ferrugem=0.4),
    'colmeia': colmeia_mat(),
    'bloco': bloco_mat(),
    'lodo': lodo_mat(),
    'cristal': cristal_mat(),
    'agua': agua_mat(),
    'agua_suja': agua_mat('Água suja', (0.4, 0.4, 0.38), 0.1),
    'vidro': vidro_sujo_mat(),
    'tremor': tremor_mat(),
    'ar_limpo': ar_limpo_mat(),
    'vortice': vortice_mat('Funil de fumaça', (0.035, 0.032, 0.03), 5.0, 3, K_VORT, 0.75, 0.42, 1.0, 0.2, 0.1,
                           1.1, 1.5, 6.5, 8.0, 2.6, 1.0, 1.2, 0.9, 1.12),
    'vortice_in': vortice_mat('Fumaça interna', (0.03, 0.028, 0.027), 14.0, 3, -2.2, 1.32, -0.42, 0.0, 0.07, 0.17,
                              0.12, 0.3, 1.0, 1.2, 0.8, 0.15, 2.5, 2.8),
    'nevoa_lav': base3d.volume_mat('Névoa do lavador', (0.7, 0.72, 0.72), 9.0, 1.2, 2.4),
    'fumaca_porta': base3d.volume_mat('Fumaça da comporta', (0.03, 0.03, 0.03), 14.0, 0.3, 1.3),
    'campo': campo_linha_mat(),
    'escorre_negro': escorrido_mat('Escorrido negro', (0.01, 0.009, 0.008), 0.95, 0.35),
    'escorre_ferr': escorrido_mat('Escorrido de ferrugem', (0.22, 0.08, 0.025), 0.85, 0.8),
    'estencil': stencil_mat(),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'verde': emissivo('Luz verde', (0.15, 1.0, 0.25), 5.0, (0.05, 0.3, 0.08)),
    'vermelha': emissivo('Luz vermelha', (1.0, 0.08, 0.03), 5.0, (0.3, 0.02, 0.01)),
    'emissor': emissivo('Emissor', (0.45, 0.12, 1.0), 2.0, (0.15, 0.03, 0.4)),
    'centelha': emissivo('Centelha', (1.0, 0.95, 0.8), 30.0, (1.0, 1.0, 1.0)),
    'chao': chao_mat(),
})
M = base3d.M
for m in M.values():
    if hasattr(m, 'blend_method'):
        try:
            m.blend_method = 'HASHED'
        except Exception:
            pass

# ------------------------------------------------------------------ medidas
Z0 = 0.1                     # topo da laje
H = 1.5                      # meia largura (3×3)
RB, RT = 1.0, 0.84           # raio da casca embaixo e em cima
PHI = math.radians(78)       # torção das retas da treliça (cintura ~0,68 m)
NL = 24                      # retas por família
NS = 18                      # segmentos por reta
DB = 0.045                   # recuo radial da família B (por cima da A)


def pA(th, t):
    p1 = Vector((RB * math.cos(th), RB * math.sin(th), ZB))
    p2 = Vector((RT * math.cos(th + PHI), RT * math.sin(th + PHI), ZT))
    return p1.lerp(p2, t)


def raio_t(t):
    return pA(0.0, t).to_2d().length


def t_de_z(z):
    return (z - ZB) / (ZT - ZB)


def raio_z(z):
    return raio_t(min(max(t_de_z(z), 0.0), 1.0))


def sup(a, z, dr=0.0):
    r = raio_z(z) + dr
    return Vector((r * math.cos(a), r * math.sin(a), z))


def normal_sup(a, z):
    d = (raio_z(z + 0.01) - raio_z(z - 0.01)) / 0.02
    return Vector((math.cos(a), math.sin(a), -d)).normalized()


def radial(v, dr):
    """Empurra o ponto dr para fora no raio (mantém z)."""
    r = v.to_2d().length
    return Vector((v.x * (r + dr) / r, v.y * (r + dr) / r, v.z))


# penetrações de duto na casca: (ângulo, z) — moldura reforçada em volta, sem treliça nem painel por dentro
PEN = [(math.radians(225), 2.8), (math.radians(315), 2.8), (math.radians(45), 3.4)]
HQ = 0.25                    # meia largura da moldura


def local_pen(p, k):
    a, z = PEN[k]
    c = sup(a, z)
    T = Vector((-math.sin(a), math.cos(a), 0))
    return (p - c).dot(T), p.z - z


def dentro_pen(p, folga=0.0):
    for k in range(len(PEN)):
        u, v = local_pen(p, k)
        if abs(u) < HQ + folga and abs(v) < HQ + folga:
            return True
    return False


# ------------------------------------------------------------------ laje, listras, sapatas
bm = bmesh.new()
caixa_de(bm, (-H, -H, 0), (H, H, Z0))
obj('laje', bm, 'concreto')
bm = bmesh.new()
for a, b in (((-H, -H), (H, -H + 0.07)), ((-H, H - 0.07), (H, H)),
             ((-H, -H + 0.07), (-H + 0.07, H - 0.07)), ((H - 0.07, -H + 0.07), (H, H - 0.07))):
    caixa_de(bm, (a[0], a[1], Z0), (b[0], b[1], Z0 + 0.004))
obj('listras_borda', bm, 'listras')
# rachaduras/juntas da laje (sulcos escuros)
bm = bmesh.new()
for x in (-0.5, 0.5):
    caixa_de(bm, (x - 0.006, -H + 0.07, Z0 - 0.003), (x + 0.006, H - 0.07, Z0 + 0.001))
    caixa_de(bm, (-H + 0.07, x - 0.006, Z0 - 0.003), (H - 0.07, x + 0.006, Z0 + 0.001))
obj('juntas', bm, 'oleo')

# ------------------------------------------------------------------ pernas em V e anel de pé da casca
COLS = [math.radians(22.5 + 45 * k) for k in range(8)]
ABRE = math.radians(7)
RPE = 1.07
bm, bs, bp = bmesh.new(), bmesh.new(), bmesh.new()
PES = []
for th in COLS:
    topo = Vector((RB * math.cos(th), RB * math.sin(th), ZB - 0.1))
    for s in (-1, 1):
        a = th + s * ABRE
        pe = Vector((RPE * math.cos(a), RPE * math.sin(a), Z0 + 0.2))
        PES.append(pe)
        placa_rot(bm, pe, topo, 0.075, 0.075, Vector((math.cos(a), math.sin(a), 0)))
        # pedestal de concreto e sapata com chumbadores
        caixa(bs, (pe.x, pe.y, Z0 + 0.06), (0.2, 0.2, 0.12), Matrix.Rotation(a, 3, 'Z'))
        caixa(bp, (pe.x, pe.y, Z0 + 0.13), (0.15, 0.15, 0.02), Matrix.Rotation(a, 3, 'Z'))
        for sx in (-1, 1):
            for sy in (-1, 1):
                q = Matrix.Rotation(a, 3, 'Z') @ Vector((sx * 0.055, sy * 0.055, 0))
                cil(bp, (pe.x + q.x, pe.y + q.y, Z0 + 0.15), 0.01, 0.035, lados=6)
        # nervura entre perna e sapata
        tubo(bp, pe + Vector((0, 0, -0.06)), pe + (topo - pe).normalized() * 0.12, 0.03, 6)
    # gusset no topo do V
    caixa(bm, topo + Vector((0, 0, 0.02)), (0.12, 0.16, 0.1), Matrix.Rotation(th, 3, 'Z'))
obj('pernas', bm, 'amarelo')
obj('pedestais', bs, 'concreto')
obj('sapatas', bp, 'ferro')
# anel de pé (caixão) e anel de topo
bm = bmesh.new()
tubo_oco(bm, (0, 0, ZB - 0.04), RB + 0.11, RB - 0.07, 0.14, lados=72)
tubo_oco(bm, (0, 0, ZT + 0.04), RT + 0.12, RT - 0.05, 0.12, lados=72)
obj('aneis_casca', bm, 'amarelo')
bp = bmesh.new()
for k in range(48):                                                    # rebites dos anéis
    a = k * 2 * PI / 48
    for z, r in ((ZB + 0.035, RB + 0.11), (ZB - 0.11, RB + 0.11), (ZT + 0.1, RT + 0.12)):
        cil(bp, (r * math.cos(a), r * math.sin(a), z), 0.009, 0.012, Vector((math.cos(a), math.sin(a), 0)), lados=6)
obj('aneis_rebites', bp, 'ferro')

# ------------------------------------------------------------------ treliça hiperboloide (duas famílias de cantoneiras)
bA, bB = bmesh.new(), bmesh.new()
n_cort = 0


def cantoneira(bm, a, b, rad_dr):
    """Cantoneira L: aba deitada na superfície e aba em pé para fora."""
    m = (a + b) / 2
    nrm = Vector((m.x, m.y, 0)).normalized()
    placa_rot(bm, a, b, 0.008, 0.045, nrm)                             # aba deitada (fina na normal)
    placa_rot(bm, a + nrm * 0.02, b + nrm * 0.02, 0.034, 0.008, nrm)   # aba em pé


for fam, bmx, sinal, dr in (('A', bA, 1, 0.0), ('B', bB, -1, DB)):
    for i in range(NL):
        th = i * 2 * PI / NL + (PI / NL if fam == 'B' else 0)
        p1 = Vector((RB * math.cos(th), RB * math.sin(th), ZB))
        p2 = Vector((RT * math.cos(th + sinal * PHI), RT * math.sin(th + sinal * PHI), ZT))
        pts = [radial(p1.lerp(p2, k / (NS * 4)), dr) for k in range(NS * 4 + 1)]
        # corta onde há moldura de duto (amostrado fino; as pontas morrem dentro da moldura)
        fora = [not dentro_pen(p) for p in pts]
        corrida = []
        for p, f in zip(pts, fora):
            if f:
                corrida.append(p)
            else:
                if len(corrida) > 1:
                    for k in range(0, len(corrida) - 1, 4):
                        cantoneira(bmx, corrida[k], corrida[min(k + 4, len(corrida) - 1)], dr)
                corrida = []
                n_cort += 1
        if len(corrida) > 1:
            for k in range(0, len(corrida) - 1, 4):
                cantoneira(bmx, corrida[k], corrida[min(k + 4, len(corrida) - 1)], dr)
obj('trelica_A', bA, 'amarelo')
obj('trelica_B', bB, 'amarelo')

# anéis de aperto por fora (em cima da família B)
bm, bp = bmesh.new(), bmesh.new()
Z_ANEIS = [ZB + (ZT - ZB) * t for t in (0.2, 0.4, 0.6, 0.8)]
for z in Z_ANEIS:
    r = raio_z(z) + DB + 0.051
    toro(bm, (0, 0, z), r, 0.012, Z, nR=96, nr=8)
    for k in range(NL):                                                 # grampos nos cruzamentos
        a = k * 2 * PI / NL + 0.07
        caixa(bp, (r * math.cos(a), r * math.sin(a), z), (0.03, 0.05, 0.035), Matrix.Rotation(a, 3, 'Z'))
obj('aneis_aperto', bm, 'aco')
obj('aneis_grampos', bp, 'ferro')

# ------------------------------------------------------------------ painéis de chapa por dentro da treliça
NP, NTP = 36, 13
gp = {k: bmesh.new() for k in ('chapa', 'chapa_ferr', 'primer', 'galv')}
buracos = []
for j in range(NTP):
    z0 = ZB + 0.04 + (ZT - ZB - 0.08) * j / NTP
    z1 = ZB + 0.04 + (ZT - ZB - 0.08) * (j + 1) / NTP
    for i in range(NP):
        a0, a1 = i * 2 * PI / NP, (i + 1) * 2 * PI / NP
        cen = sup((a0 + a1) / 2, (z0 + z1) / 2, -0.012)
        if dentro_pen(cen, 0.02):
            continue
        r_ = random.random()
        if r_ < 0.045 and 1 < j < NTP - 1:
            buracos.append(((a0 + a1) / 2, (z0 + z1) / 2))
            continue
        k = 'chapa_ferr' if r_ < 0.11 else 'primer' if r_ < 0.16 else 'galv' if r_ < 0.24 else 'chapa'
        bmx = gp[k]
        ma, mz = (a1 - a0) * 0.012, (z1 - z0) * 0.02
        vs = [bmx.verts.new(sup(a, z, -0.012)) for a, z in ((a0 + ma, z0 + mz), (a1 - ma, z0 + mz),
                                                           (a1 - ma, z1 - mz), (a0 + ma, z1 - mz))]
        bmx.faces.new(vs)
for k, bmx in gp.items():
    o = obj('paineis_' + k, bmx, k)
    sd = o.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = 0.006
    sd.offset = 0.0
# interior escuro (fuligem grossa por dentro): casca contínua bem recuada
bm = bmesh.new()
an = []
for j in range(25):
    z = ZB + (ZT - ZB) * j / 24
    an.append([bm.verts.new(sup(i * 2 * PI / 48, z, -0.06)) for i in range(48)])
for A, B in zip(an, an[1:]):
    for i in range(48):
        bm.faces.new((A[i], A[(i + 1) % 48], B[(i + 1) % 48], B[i]))
suavizar(obj('casca_interna', bm, 'fuligem'))

# remendos aparafusados por cima de painéis (chapa trocada) e rebites
bm, bp = bmesh.new(), bmesh.new()
REMENDOS = [(math.radians(a), z + 0.35, w, h) for a, z, w, h in
            ((200, 2.0, 0.22, 0.18), (250, 2.6, 0.18, 0.26), (290, 1.8, 0.3, 0.2), (330, 3.1, 0.2, 0.16),
             (20, 2.3, 0.26, 0.2), (95, 2.9, 0.2, 0.22), (160, 3.6, 0.18, 0.14), (275, 3.9, 0.2, 0.16),
             (240, 1.75, 0.16, 0.14), (300, 2.55, 0.16, 0.2))]
for a, z, w, h in REMENDOS:
    n = normal_sup(a, z)
    T = Vector((-math.sin(a), math.cos(a), 0))
    U = n.cross(T)
    c = sup(a, z, -0.0075)
    rot = Matrix((T, U, n)).transposed()
    caixa(bm, c, (w, h, 0.004), rot)
    for su in (-1, 1):
        for k in range(4):
            q = c + T * (-w / 2 + 0.02 + k * (w - 0.04) / 3) + U * su * (h / 2 - 0.018) + n * 0.003
            cil(bp, q, 0.0055, 0.006, n, lados=6)
obj('remendos', bm, 'galv')
obj('remendos_rebites', bp, 'ferro')

# molduras reforçadas das penetrações de duto + chapa de colar
bm, bc, bp = bmesh.new(), bmesh.new(), bmesh.new()
for a, z in PEN:
    n = normal_sup(a, z)
    T = Vector((-math.sin(a), math.cos(a), 0))
    U = n.cross(T)
    c = sup(a, z, 0.035)
    rot = Matrix((T, U, n)).transposed()
    for su in (-1, 1):
        caixa(bm, c + U * su * HQ, (2 * HQ + 0.06, 0.06, 0.11), rot)
        caixa(bm, c + T * su * HQ, (0.06, 2 * HQ - 0.06, 0.11), rot)
    cc = sup(a, z, -0.012)
    caixa(bc, cc, (2 * HQ, 2 * HQ, 0.008), rot)
    for k in range(12):
        ang = k * 2 * PI / 12
        cil(bp, cc + (T * math.cos(ang) + U * math.sin(ang)) * 0.15 + n * 0.006, 0.007, 0.01, n, lados=6)
obj('molduras_duto', bm, 'amarelo')
obj('colares_duto', bc, 'primer')
obj('colares_paraf', bp, 'ferro')

# escorridos negros descendo da casca (das juntas, dos anéis, dos buracos)
bm = bmesh.new()
uv = bm.loops.layers.uv.new()
for k in range(60):
    a = random.uniform(0, 2 * PI)
    zt = random.choice(Z_ANEIS + [ZT - 0.05, ZT - 0.05])
    zt -= random.uniform(0.0, 0.1)
    alt = random.uniform(0.35, 1.2)
    nzs = 8
    pts, nrs = [], []
    for s in range(nzs + 1):
        z = zt - alt * s / nzs
        if z < ZB + 0.05:
            break
        pts.append(sup(a, z, -0.0072))
        nrs.append(normal_sup(a, z))
    if len(pts) > 2 and not any(dentro_pen(p, 0.05) for p in pts):
        faixa(bm, uv, pts, nrs, random.uniform(0.03, 0.09))
for a, z in buracos:                                               # buraco: borda carcomida escorrendo
    pts = [sup(a, z - 0.08 - 0.08 * s, -0.0072) for s in range(6)]
    faixa(bm, uv, pts, [normal_sup(a, p.z) for p in pts], 0.12)
obj('escorridos_casca', bm, 'escorre_negro')
bm = bmesh.new()
uv = bm.loops.layers.uv.new()
for k in range(26):
    a = random.uniform(0, 2 * PI)
    zt = random.uniform(ZB + 0.6, ZT - 0.6)
    pts = [sup(a, zt - 0.08 * s, -0.0071) for s in range(7)]
    faixa(bm, uv, pts, [normal_sup(a, p.z) for p in pts], random.uniform(0.02, 0.05))
obj('escorridos_ferr_casca', bm, 'escorre_ferr')

# letreiro apagado na casca (estêncil de série, plano tangente)
txt = bpy.data.curves.new('serie', 'FONT')
txt.body = 'PA-02  #7741'
txt.size = 0.13
txt.align_x = 'CENTER'
to = bpy.data.objects.new('serie', txt)
sc.collection.objects.link(to)
to.data.materials.append(M['estencil'])
a_s = math.radians(300)
p_s = sup(a_s, 3.3, -0.0068)
to.location = p_s
to.rotation_euler = (PI / 2, 0, a_s + PI / 2)

# ------------------------------------------------------------------ topo: deque de grade, 3 ventiladores, pontes, motores
ZD = ZT + 0.11               # deque
FANS = [Vector((0.44 * math.cos(math.radians(a)), 0.44 * math.sin(math.radians(a)), 0)) for a in (90, 210, 330)]
RF = 0.32
bm, bg = bmesh.new(), bmesh.new()
for a in (30, 150, 270):                                             # vigas radiais entre as virolas
    d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
    placa_rot(bm, Vector((0, 0, ZD - 0.04)), d * (RT + 0.08) + Vector((0, 0, ZD - 0.04)), 0.08, 0.05)
cil(bm, (0, 0, ZD - 0.04), 0.1, 0.08, lados=16)
for k in range(37):                                                  # grade: barras chatas
    y = -0.9 + k * 0.05
    w = math.sqrt(max(0.0, (RT + 0.08) ** 2 - y * y))
    if w > 0.02:
        caixa_de(bg, (-w, y - 0.002, ZD - 0.015), (w, y + 0.002, ZD + 0.012))
for k in range(8):
    x = -0.84 + k * 0.24
    w = math.sqrt(max(0.0, (RT + 0.08) ** 2 - x * x))
    caixa_de(bg, (x - 0.003, -w, ZD - 0.015), (x + 0.003, w, ZD + 0.012))
obj('deque_vigas', bm, 'amarelo')
obj('deque_grade', bg, 'ferro')
rotores = []
for k, c0 in enumerate(FANS):
    c = c0 + Vector((0, 0, 0))
    bm, bp, bf = bmesh.new(), bmesh.new(), bmesh.new()
    tubo_oco(bm, c + Vector((0, 0, ZD + 0.24)), RF + 0.02, RF, 0.46, lados=64)          # virola
    toro(bm, c + Vector((0, 0, ZD + 0.47)), RF + 0.035, 0.022, Z, nR=64, nr=10)          # boca enrolada
    tubo_oco(bf, c + Vector((0, 0, ZD + 0.03)), RF + 0.07, RF, 0.025, lados=64)          # flange no deque
    for i in range(16):
        a = i * 2 * PI / 16
        cil(bp, c + Vector((math.cos(a) * (RF + 0.05), math.sin(a) * (RF + 0.05), ZD + 0.05)), 0.007, 0.02, lados=6)
    for i in range(4):                                                                    # nervuras verticais
        a = i * PI / 2 + PI / 4
        caixa(bm, c + Vector((math.cos(a) * (RF + 0.03), math.sin(a) * (RF + 0.03), ZD + 0.24)), (0.02, 0.03, 0.42),
              Matrix.Rotation(a, 3, 'Z'))
    obj('virola%d' % k, bm, 'amarelo' if k != 1 else 'verde_vel')                         # uma trocada (outra cor)
    obj('virola%d_flange' % k, bf, 'ferro')
    obj('virola%d_paraf' % k, bp, 'aco')
    # ponte com motor (eixo para baixo), grade de proteção
    bm, bp = bmesh.new(), bmesh.new()
    d = (c0.normalized() if c0.length > 0 else X)
    t = Vector((-d.y, d.x, 0))
    placa_rot(bm, c - t * (RF + 0.04) + Vector((0, 0, ZD + 0.5)), c + t * (RF + 0.04) + Vector((0, 0, ZD + 0.5)), 0.06, 0.06)
    for s in (-1, 1):
        caixa(bm, c + t * s * (RF + 0.04) + Vector((0, 0, ZD + 0.44)), (0.07, 0.07, 0.1), Matrix.Rotation(math.atan2(t.y, t.x), 3, 'Z'))
    cil(bm, c + Vector((0, 0, ZD + 0.62)), 0.1, 0.2, lados=24)                             # motor
    for i in range(12):                                                                   # aletas
        a = i * 2 * PI / 12
        caixa(bm, c + Vector((math.cos(a) * 0.105, math.sin(a) * 0.105, ZD + 0.62)), (0.014, 0.014, 0.17),
              Matrix.Rotation(a, 3, 'Z'))
    cil(bm, c + Vector((0, 0, ZD + 0.74)), 0.075, 0.04, lados=20)                         # tampa da ventoinha
    caixa(bm, c + t * 0.12 + Vector((0, 0, ZD + 0.66)), (0.07, 0.06, 0.06), Matrix.Rotation(math.atan2(t.y, t.x), 3, 'Z'))
    obj('motor%d' % k, bm, 'grafite')
    cil(bp, c + Vector((0, 0, ZD + 0.42)), 0.025, 0.18, lados=12)                        # eixo
    for r in (0.1, 0.18, 0.26, RF + 0.01):
        toro(bp, c + Vector((0, 0, ZD + 0.455)), r, 0.004, Z, nR=48, nr=6)
    for i in range(16):
        a = i * 2 * PI / 16
        dd = Vector((math.cos(a), math.sin(a), 0))
        tubo(bp, c + dd * 0.1 + Vector((0, 0, ZD + 0.455)), c + dd * (RF + 0.01) + Vector((0, 0, ZD + 0.455)), 0.0035, 6)
    obj('grade_vent%d' % k, bp, 'aco')
    # rotor: cubo + 6 pás torcidas (eixo Z)
    piv = bpy.data.objects.new('rotor%d' % k, None)
    sc.collection.objects.link(piv)
    piv.location = c + Vector((0, 0, ZD + 0.3))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.075, 0.08, lados=24)
    esfera(bm, Vector((0, 0, -0.04)), 0.075, 24, (1, 1, 0.6))
    obj('cubo%d' % k, bm, 'grafite', piv)
    bm = bmesh.new()
    for i in range(6):
        a0 = i * 2 * PI / 6
        linhas = []
        for j in range(7):
            tt = j / 6
            r = 0.07 + tt * (RF - 0.085)
            corda = 0.13 - 0.04 * tt
            passo = math.radians(36 - 18 * tt)
            a = a0 + 0.12 * tt
            rad = Vector((math.cos(a), math.sin(a), 0))
            tang = Vector((-math.sin(a), math.cos(a), 0))
            p1 = rad * r + (tang * math.cos(passo) + Z * math.sin(passo)) * corda / 2
            p2 = rad * r - (tang * math.cos(passo) + Z * math.sin(passo)) * corda / 2
            linhas.append((bm.verts.new(p1), bm.verts.new(p2)))
        for (a1, b1), (a2, b2) in zip(linhas, linhas[1:]):
            bm.faces.new((a1, b1, b2, a2))
    pas = obj('pas%d' % k, bm, 'aluminio', piv)
    sd = pas.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = 0.006
    rotores.append(piv)
# fuligem/poeira no deque e sinaleiro âmbar
bm = bmesh.new()
for k in range(14):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.2, 0.8)
    if any((Vector((r * math.cos(a), r * math.sin(a), 0)) - f).length < RF + 0.08 for f in FANS):
        continue
    mancha(bm, (r * math.cos(a), r * math.sin(a)), random.uniform(0.04, 0.1), ZD + 0.0125)
obj('deque_fuligem', bm, 'fuligem')
bm, bl = bmesh.new(), bmesh.new()
cil(bm, (0, 0, ZD + 0.06), 0.035, 0.1, lados=12)
cil(bl, (0, 0, ZD + 0.14), 0.03, 0.06, lados=16)
esfera(bl, (0, 0, ZD + 0.17), 0.03, 16)
obj('sinaleiro_base', bm, 'grafite')
farol = obj('sinaleiro', bl, 'lampada')

# ------------------------------------------------------------------ escada de cabos subindo a casca (oeste) com feixe
A_ESC = PI
bm, bc, bp = bmesh.new(), bmesh.new(), bmesh.new()
zs = [ZB + 0.08 + (ZT - ZB - 0.1) * k / 14 for k in range(15)]
for s in (-1, 1):
    pts = [sup(A_ESC, z, DB + 0.15) + Vector((0, s * 0.09, 0)) for z in zs]
    for a, b in zip(pts, pts[1:]):
        placa_rot(bm, a, b, 0.04, 0.008, X)
for z in zs[:-1]:
    for dz in (0.0, 0.11):
        p = sup(A_ESC, z + dz, DB + 0.15)
        tubo(bm, p - Y * 0.09, p + Y * 0.09, 0.006, 6)
for z in Z_ANEIS:                                                          # mãos-francesas até o anel
    for s in (-1, 1):
        a = sup(A_ESC, z, DB + 0.15) + Vector((0, s * 0.09, 0))
        b = sup(A_ESC, z, DB + 0.06) + Vector((0, s * 0.09, 0))
        tubo(bp, a, b, 0.01, 6)
for i, (cor_off, r) in enumerate(((-0.05, 0.014), (0.0, 0.017), (0.05, 0.012), (0.025, 0.01))):
    pts = [sup(A_ESC, z, DB + 0.18) + Vector((0, cor_off, 0)) for z in zs]
    mangueira(bc, pts, r)
for z in zs[::2]:
    toro(bp, sup(A_ESC, z, DB + 0.18), 0.075, 0.004, X, nR=16, nr=4)
obj('escada_cabos', bm, 'galv')
obj('escada_suportes', bp, 'aco')
obj('feixe_cabos', bc, 'borracha')
# cabos do topo da escada até cada motor
bc = bmesh.new()
topo_esc = sup(A_ESC, zs[-1], DB + 0.18)
for k, c in enumerate(FANS):
    alvo = c + Vector((0, 0, ZD + 0.66)) + (Vector((-c.y, c.x, 0)).normalized() * 0.12 if c.length else X)
    pts = bezier(topo_esc + Vector((0, (k - 1) * 0.04, 0)), topo_esc + Vector((0.1, (k - 1) * 0.04, 0.35)),
                 alvo + Vector((0, 0, 0.3)), alvo, 14)
    mangueira(bc, pts, 0.011)
obj('cabos_motores', bc, 'borracha')

# ------------------------------------------------------------------ núcleo: prensa, funil, cristal levitando, braços
NUC = Vector((0, 0, 0))
ZP0, ZP1 = Z0, 0.62          # caixa da prensa
bm, bp, bl = bmesh.new(), bmesh.new(), bmesh.new()
caixa_de(bm, (-0.26, -0.26, ZP0), (0.26, 0.26, ZP1))
caixa_de(bm, (-0.3, -0.3, ZP0), (0.3, 0.3, ZP0 + 0.05))                    # rodapé
for s in (-1, 1):                                                           # reforços laterais
    caixa_de(bm, (s * 0.26 - 0.015, -0.2, ZP0 + 0.05), (s * 0.26 + 0.015, 0.2, ZP1 - 0.04))
    caixa_de(bm, (-0.2, s * 0.26 - 0.015, ZP0 + 0.1), (0.2, s * 0.26 + 0.015, ZP0 + 0.14))
obj('prensa', bm, 'grafite')
for x in (-0.24, 0.24):
    for y in (-0.24, 0.24):
        cil(bp, (x, y, ZP1 + 0.005), 0.012, 0.016, lados=6)
for k in range(10):
    cil(bp, (-0.278, -0.2 + k * 0.045, ZP0 + 0.4), 0.007, 0.012, X, lados=6)
    cil(bp, (0.278, -0.2 + k * 0.045, ZP0 + 0.4), 0.007, 0.012, X, lados=6)
obj('prensa_paraf', bp, 'ferro')
# boca da comporta (sul) na altura da esteira, guilhotina animada com dois cilindros
ZE = 0.3                     # topo da lona da esteira
bm = bmesh.new()
caixa_de(bm, (-0.12, -0.275, ZE - 0.02), (-0.09, -0.255, ZE + 0.2))
caixa_de(bm, (0.09, -0.275, ZE - 0.02), (0.12, -0.255, ZE + 0.2))
caixa_de(bm, (-0.12, -0.275, ZE + 0.17), (0.12, -0.255, ZE + 0.2))
caixa_de(bm, (-0.12, -0.275, ZE - 0.035), (0.12, -0.255, ZE - 0.01))
obj('comporta_moldura', bm, 'aco')
bm = bmesh.new()
caixa_de(bm, (-0.09, -0.271, ZE - 0.01), (0.09, -0.262, ZE + 0.17))
obj('boca_escura', bm, 'oleo')
piv_gate = bpy.data.objects.new('guilhotina', None)
sc.collection.objects.link(piv_gate)
bm, bp = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.1, -0.29, ZE - 0.015), (0.1, -0.278, ZE + 0.155))
for x in (-0.06, 0.06):
    cil(bp, (x, -0.293, ZE + 0.14), 0.008, 0.01, Y, lados=6)
obj('guilhotina_chapa', bm, 'aco', piv_gate)
obj('guilhotina_olhais', bp, 'ferro', piv_gate)
# dois cilindros da guilhotina: camisa presa na orelha da prensa, haste presa na chapa
bm, bh = bmesh.new(), bmesh.new()
for x in (-0.06, 0.06):
    caixa_de(bm, (x - 0.03, -0.33, ZP1 - 0.03), (x + 0.03, -0.26, ZP1))             # orelha na prensa
    cil(bm, (x, -0.31, ZE + 0.27), 0.022, 0.16, lados=16)                           # camisa
    cil(bm, (x, -0.31, ZE + 0.355), 0.026, 0.02, lados=16)
obj('guilhotina_cil', bm, 'amarelo')
for x in (-0.06, 0.06):
    cil(bh, (x, -0.31, ZE + 0.19), 0.009, 0.07, lados=12)
    caixa_de(bh, (x - 0.015, -0.315, ZE + 0.14), (x + 0.015, -0.284, ZE + 0.158))
obj('guilhotina_haste', bh, 'cromo', piv_gate)
bc = bmesh.new()
for x in (-0.06, 0.06):                                                     # mangueiras hidráulicas
    sx = 1 if x > 0 else -1
    mangueira(bc, bezier((x, -0.31, ZE + 0.365), (x + 0.02 * sx, -0.33, ZE + 0.45), (0.2 * sx, -0.3, ZP1 + 0.08),
                         (0.18 * sx, -0.18, ZP1 + 0.004), 10), 0.007)
obj('guilhotina_mang', bc, 'borracha')

# funil sobre a prensa (cone), com anel de rebites e gotas negras pingando do cristal
ZC = 1.32                    # centro do cristal
bm, bp = bmesh.new(), bmesh.new()
cil(bm, (0, 0, ZP1 + 0.14), 0.1, 0.28, lados=32, r2=0.25)
toro(bm, (0, 0, ZP1 + 0.28), 0.25, 0.012, Z, nR=48, nr=8)
for k in range(16):
    a = k * 2 * PI / 16
    cil(bp, (0.24 * math.cos(a), 0.24 * math.sin(a), ZP1 + 0.27), 0.006, 0.012, lados=6)
obj('funil', bm, 'aco')
obj('funil_rebites', bp, 'ferro')
bm = bmesh.new()
cil(bm, (0, 0, ZP1 + 0.282), 0.235, 0.004, lados=32)
obj('funil_lama', bm, 'lodo')                                          # condensado negro acumulado no funil

# cristal: aglomerado (bipirâmide grande + menores) em pivô que gira
piv_cr = bpy.data.objects.new('cristal_piv', None)
sc.collection.objects.link(piv_cr)
piv_cr.location = (0, 0, ZC)
bm = bmesh.new()


def bipiramide(bm, c, r, h_cima, h_baixo, lados, rot):
    c = Vector(c)
    topo = bm.verts.new(c + rot @ Vector((0, 0, h_cima)))
    fundo = bm.verts.new(c + rot @ Vector((0, 0, -h_baixo)))
    an = [bm.verts.new(c + rot @ Vector((r * math.cos(a) * random.uniform(0.85, 1.1), r * math.sin(a) * random.uniform(0.85, 1.1),
                                       random.uniform(-0.02, 0.02))))
          for a in (i * 2 * PI / lados for i in range(lados))]
    for i in range(lados):
        bm.faces.new((an[i], an[(i + 1) % lados], topo))
        bm.faces.new((an[(i + 1) % lados], an[i], fundo))


bipiramide(bm, (0, 0, 0), 0.12, 0.3, 0.22, 6, Matrix.Identity(3))
for k in range(6):
    a = k * 2 * PI / 6 + 0.3
    rot = Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(random.uniform(0.5, 0.9), 3, 'Y')
    bipiramide(bm, (0.05 * math.cos(a), 0.05 * math.sin(a), random.uniform(-0.08, 0.05)), random.uniform(0.035, 0.055),
               random.uniform(0.12, 0.2), 0.05, 5, rot)
obj('cristal', bm, 'cristal', piv_cr)
# anel de campo em volta do cristal e bobina de cobre por cima
bm = bmesh.new()
toro(bm, (0, 0, ZC), 0.56, 0.01, Z, nR=96, nr=8)
toro(bm, (0, 0, ZC - 0.22), 0.34, 0.006, Z, nR=64, nr=6)
anel_campo = obj('anel_campo', bm, 'campo')
# quatro braços com cilindro hidráulico e cabeça de bobina apontada para o cristal
bm, bh, bco, bp, bc = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
CABECAS = []
for k in range(4):
    a = PI / 4 + k * PI / 2
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    raiz = d * 0.45 + Vector((0, 0, ZP1 - 0.08))
    cab = d * 0.47 + Vector((0, 0, ZC))
    CABECAS.append(cab)
    # pedestal-orelha na quina da prensa
    caixa(bm, d * 0.42 + Vector((0, 0, ZP1 - 0.1)), (0.1, 0.08, 0.12), Matrix.Rotation(a, 3, 'Z'))
    for s in (-1, 1):
        caixa(bm, raiz + t * s * 0.045, (0.05, 0.015, 0.09), Matrix.Rotation(a, 3, 'Z'))
    cil(bp, raiz, 0.016, 0.11, t, lados=12)                                # pino
    # braço (viga em caixão) da raiz até a cabeça
    placa_rot(bm, raiz, cab - d * 0.06, 0.07, 0.05, d)
    # cilindro hidráulico paralelo: camisa presa ao pedestal da prensa, haste na metade do braço
    cb = d * 0.2 + Vector((0, 0, ZP1 + 0.02))
    cm = raiz.lerp(cab, 0.62) - (cab - raiz).normalized().cross(t).normalized() * 0.0
    meio = cb.lerp(cm, 0.55)
    tubo(bh, cb, meio, 0.026, 16)
    tubo(bh, meio - (cm - cb).normalized() * 0.02, meio + (cm - cb).normalized() * 0.01, 0.03, 16)
    tubo(bp, meio, cm, 0.011, 12)
    esfera(bp, cm, 0.02, 10)
    caixa(bm, cb + Vector((0, 0, -0.02)), (0.06, 0.06, 0.05), Matrix.Rotation(a, 3, 'Z'))
    # cabeça: bobina de cobre com anéis, ponteira de ferro
    cil(bm, cab, 0.065, 0.12, d, lados=20)
    for j in range(5):
        cil(bco, cab - d * (0.04 - j * 0.02), 0.072, 0.012, d, lados=20)
    cil(bp, cab - d * 0.09, 0.03, 0.06, d, lados=16, r2=0.015)
    # mangueira até a camisa e cabo até a bobina
    mangueira(bc, bezier(cb + Vector((0, 0, -0.02)) + t * 0.03, cb + t * 0.1 + Vector((0, 0, -0.1)),
                         d * 0.16 + t * 0.06 + Vector((0, 0, ZP1 + 0.06)), d * 0.12 + Vector((0, 0, ZP1 + 0.005)), 10), 0.008)
    mangueira(bc, bezier(cab + d * 0.06, cab + d * 0.15 + Vector((0, 0, -0.05)), raiz + d * 0.1 + Vector((0, 0, 0.2)),
                         raiz + d * 0.05 + Vector((0, 0, 0.05)), 12), 0.009)
obj('bracos', bm, 'amarelo')
obj('bracos_cil', bh, 'grafite')
obj('bobinas', bco, 'cobre')
obj('bracos_aco', bp, 'cromo')
obj('bracos_mang', bc, 'borracha')
# emissores violeta nas pontas das bobinas
bm = bmesh.new()
for c in CABECAS:
    d = Vector((c.x, c.y, 0)).normalized()
    esfera(bm, c - d * 0.125, 0.012, 10)
obj('emissores', bm, 'emissor')

# ------------------------------------------------------------------ coletor em arco em volta do núcleo
R_COL, Z_COL, r_col = 0.72, 0.5, 0.07
A0_COL, A1_COL = math.radians(-58), math.radians(238)
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
toro(bm, (0, 0, Z_COL), R_COL, r_col, Z, nR=72, nr=16, a0=A0_COL, a1=A1_COL)
for a in (A0_COL, A1_COL):                                                 # flanges cegos nas pontas
    p = Vector((R_COL * math.cos(a), R_COL * math.sin(a), Z_COL))
    tg = Vector((-math.sin(a), math.cos(a), 0)) * (1 if a == A1_COL else -1)
    flange(bf, bp, p + tg * 0.012, tg, r_col * 1.45, 0.025)
for k in range(9):                                                         # bocas de aspiração (grelhas para dentro)
    a = A0_COL + (A1_COL - A0_COL) * (k + 0.5) / 9
    p = Vector(((R_COL - r_col) * math.cos(a), (R_COL - r_col) * math.sin(a), Z_COL + 0.02))
    caixa(bf, p, (0.03, 0.12, 0.08), Matrix.Rotation(a, 3, 'Z'))
for a in (math.radians(g) for g in (-25, 15, 75, 120, 160, 200)):          # suportes (selas)
    p = Vector((R_COL * math.cos(a), R_COL * math.sin(a), 0))
    caixa(bf, p + Vector((0, 0, (Z0 + Z_COL - r_col) / 2)), (0.05, 0.12, Z_COL - r_col - Z0), Matrix.Rotation(a, 3, 'Z'))
    caixa(bf, p + Vector((0, 0, Z0 + 0.008)), (0.12, 0.16, 0.016), Matrix.Rotation(a, 3, 'Z'))
obj('coletor', bm, 'cano')
obj('coletor_pecas', bf, 'ferro')
obj('coletor_paraf', bp, 'aco')
bm = bmesh.new()
for k in range(9):
    a = A0_COL + (A1_COL - A0_COL) * (k + 0.5) / 9
    p = Vector(((R_COL - r_col - 0.016) * math.cos(a), (R_COL - r_col - 0.016) * math.sin(a), Z_COL + 0.02))
    for j in range(4):
        caixa(bm, p + Vector((0, 0, -0.03 + j * 0.02)), (0.004, 0.11, 0.006), Matrix.Rotation(a, 3, 'Z'))
obj('coletor_grelhas', bm, 'aco')


# ------------------------------------------------------------------ armários de filtro de carvão (quinas sul)
def armario_filtro(nome, cx, cy, tag):
    """Armário girado com a face de dentro para a torre: base-plenum com entrada, 3 cassetes, coifa e saída."""
    rz = math.atan2(-cy, -cx) - PI / 2
    piv = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(piv)
    piv.location = (cx, cy, 0)
    piv.rotation_euler = (0, 0, rz)
    L = 0.27                                                              # meia largura
    bm, bq, bp, bco, bf = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    caixa_de(bm, (-L, -L, Z0), (L, L, 0.42))                              # plenum de base
    for sx in (-1, 1):                                                    # montantes
        for sy in (-1, 1):
            caixa_de(bm, (sx * L - 0.025, sy * L - 0.025, 0.42), (sx * L + 0.025, sy * L + 0.025, 1.52))
    caixa_de(bm, (-L - 0.02, -L - 0.02, 1.5), (L + 0.02, L + 0.02, 1.56))
    obj(nome + '_quadro', bm, 'amarelo', piv)
    zc = [0.43, 0.79, 1.15]
    trocado = random.randrange(3)
    for i, z in enumerate(zc):
        mat = 'verde_vel' if i == trocado else 'grafite'
        b1 = bmesh.new()
        caixa_de(b1, (-L + 0.03, -L + 0.03, z + 0.01), (L - 0.03, L - 0.03, z + 0.34))
        obj(nome + '_cassete%d' % i, b1, mat, piv)
        # face de colmeia para fora (−Y local) e para os lados, molduras, travas de garra
        caixa_de(bco, (-L + 0.06, -L + 0.026, z + 0.04), (L - 0.06, -L + 0.03, z + 0.31))
        for sx in (-1, 1):
            caixa_de(bco, (sx * (L - 0.026) - 0.002, -L + 0.06, z + 0.04), (sx * (L - 0.026) + 0.002, L - 0.06, z + 0.31))
        for zz in (z + 0.035, z + 0.315):
            caixa_de(bq, (-L + 0.04, -L + 0.018, zz - 0.008), (L - 0.04, -L + 0.03, zz + 0.008))
        for x in (-L + 0.045, L - 0.045):
            caixa_de(bq, (x - 0.008, -L + 0.018, z + 0.03), (x + 0.008, -L + 0.03, z + 0.32))
        for x in (-0.12, 0.12):                                           # travas (olhais para a garra do drone)
            caixa_de(bp, (x - 0.02, -L + 0.008, z + 0.16), (x + 0.02, -L + 0.022, z + 0.2))
            toro(bp, Vector((x, -L + 0.0, z + 0.18)), 0.016, 0.004, Y, nR=12, nr=5)
        caixa_de(bf, (0.07, -L + 0.012, z + 0.255), (0.17, -L + 0.018, z + 0.29))     # plaqueta de série
    obj(nome + '_colmeia', bco, 'colmeia', piv)
    obj(nome + '_molduras', bq, 'aco', piv)
    obj(nome + '_travas', bp, 'ferro', piv)
    obj(nome + '_plaquetas', bf, 'mostrador', piv)
    # coifa (tronco de pirâmide) e bocal de saída em cima
    bm = bmesh.new()
    cil(bm, (0, 0, 1.66), 0.38, 0.2, lados=4, r2=0.15)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(PI / 4, 3, 'Z'))
    obj(nome + '_coifa', bm, 'galv', piv)
    # entrada no plenum (face +Y local, para a torre)
    bm, bp = bmesh.new(), bmesh.new()
    flange(bm, bp, (0, L + 0.012, 0.5 - 0.0), Y, 0.14, 0.024)
    obj(nome + '_flange_ent', bm, 'ferro', piv)
    obj(nome + '_paraf_ent', bp, 'aco', piv)
    # manômetro diferencial no montante
    bm, bf2, bpt = bmesh.new(), bmesh.new(), bmesh.new()
    c = Vector((L + 0.03, -L - 0.02, 1.0))
    cil(bm, c, 0.04, 0.025, Vector((0.5, -1, 0)), lados=20)
    cil(bf2, c + Vector((0.5, -1, 0)).normalized() * 0.0125, 0.034, 0.002, Vector((0.5, -1, 0)), lados=20)
    obj(nome + '_manometro', bm, 'aco', piv)
    obj(nome + '_mostrador', bf2, 'mostrador', piv)
    # letreiro apagado
    t = bpy.data.curves.new(nome + '_txt', 'FONT')
    t.body = 'C-ATV ' + tag
    t.size = 0.055
    t.align_x = 'CENTER'
    to = bpy.data.objects.new(nome + '_txt', t)
    sc.collection.objects.link(to)
    to.data.materials.append(M['estencil'])
    to.parent = piv
    to.location = (0, -L - 0.0015, 0.3)
    to.rotation_euler = (PI / 2, 0, 0)
    # fuligem no topo, escorrido negro descendo da coifa
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    for x in (-L, L):
        escorrido_reto(bm, uv, (x, -L - 0.0265, 1.49), (0, -1, 0), random.uniform(0.025, 0.04), random.uniform(0.3, 0.7))
    escorrido_reto(bm, uv, (0.0, -L - 0.0215, 1.5), (0, -1, 0), 0.3, 0.03)
    for x in (-0.1, 0.12):
        escorrido_reto(bm, uv, (x, -L - 0.001, 0.41), (0, -1, 0), 0.05, 0.25)
    obj(nome + '_escorridos', bm, 'escorre_negro', piv)
    return piv, rz


FILTROS = [(-1.08, -1.08, 'SO'), (1.08, -1.08, 'SE')]
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
for cx, cy, tag in FILTROS:
    armario_filtro('filtro_' + tag, cx, cy, tag)
    a = math.atan2(cy, cx)
    d = Vector((math.cos(a), math.sin(a), 0))
    # entrada: do coletor (arco) até a face de dentro do armário, na altura do coletor
    p_col = d * (R_COL + r_col * 0.6) + Vector((0, 0, Z_COL))
    p_arm = Vector((cx, cy, 0.5)) - d * (0.27 + 0.024)
    cano(bm, bf, bp, [p_col, p_arm], 0.085, fl_pontas=True)
    # saída: bocal da coifa → sobe → entra na casca pela moldura
    a_pen, z_pen = PEN[0] if cy < 0 and cx < 0 else PEN[1]
    pc = sup(a_pen, z_pen, 0.0)
    topo = Vector((cx, cy, 1.76))
    alto = Vector((cx, cy, z_pen))
    cano(bm, bf, bp, [topo, alto, pc + d * 0.0], 0.09, fl_pontas=False)
    flange(bf, bp, sup(a_pen, z_pen, 0.105), normal_sup(a_pen, z_pen), 0.15, 0.03, 10)
    flange(bf, bp, topo + Z * 0.012, Z, 0.13, 0.024)
obj('dutos_filtro', bm, 'galv')
obj('dutos_filtro_fl', bf, 'ferro')
obj('dutos_filtro_paraf', bp, 'aco')

# ------------------------------------------------------------------ lavador de gás (quina NE)
LV = Vector((1.08, 1.08, 0))
R_LV = 0.3
Z_LV0, Z_LV1, Z_LV2 = 0.5, 1.25, 2.3      # vaso de baixo, câmara de vidro, tampo
bm, bp, bf = bmesh.new(), bmesh.new(), bmesh.new()
cil(bm, LV + Vector((0, 0, (Z_LV0 + Z_LV1) / 2)), R_LV, Z_LV1 - Z_LV0, lados=40)
cil(bm, LV + Vector((0, 0, Z_LV0 - 0.12)), 0.05, 0.24, lados=24, r2=R_LV)          # fundo cônico
for z in (Z_LV0 + 0.04, (Z_LV0 + Z_LV1) / 2, Z_LV1 - 0.03):                         # cintas
    toro(bf, LV + Vector((0, 0, z)), R_LV + 0.006, 0.01, Z, nR=48, nr=6)
for k in range(4):                                                                   # pernas
    a = math.radians(15) + k * PI / 2
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa_de(bf, LV + d * 0.315 - Vector((0.025, 0.025, 0)) + Vector((0, 0, Z0)), LV + d * 0.315 + Vector((0.025, 0.025, Z_LV0 + 0.25)))
    caixa(bf, LV + d * 0.315 + Vector((0, 0, Z0 + 0.01)), (0.1, 0.1, 0.02))
obj('lavador_vaso', bm, 'amarelo')
obj('lavador_cintas', bf, 'ferro')
# câmara de vidro: 8 montantes, anéis, 8 vidros
bm, bv = bmesh.new(), bmesh.new()
for k in range(8):
    a = k * 2 * PI / 8
    caixa(bm, LV + Vector((R_LV * math.cos(a), R_LV * math.sin(a), (Z_LV1 + Z_LV2) / 2)), (0.04, 0.04, Z_LV2 - Z_LV1),
          Matrix.Rotation(a, 3, 'Z'))
    a2 = a + PI / 8
    rr = R_LV * math.cos(PI / 8)
    caixa(bv, LV + Vector((rr * math.cos(a2), rr * math.sin(a2), (Z_LV1 + Z_LV2) / 2)),
          (0.012, 2 * R_LV * math.sin(PI / 8) - 0.03, Z_LV2 - Z_LV1 - 0.06), Matrix.Rotation(a2, 3, 'Z'))
for z in (Z_LV1 + 0.02, (Z_LV1 + Z_LV2) / 2, Z_LV2 - 0.02):
    tubo_oco(bm, LV + Vector((0, 0, z)), R_LV + 0.03, R_LV - 0.02, 0.04, lados=8)
cil(bm, LV + Vector((0, 0, Z_LV2 + 0.08)), R_LV + 0.02, 0.16, lados=40, r2=0.12)     # tampo cônico
obj('lavador_quadro', bm, 'amarelo')
for o in (obj('lavador_vidros', bv, 'vidro'),):
    pass
# chuveiros: anel de distribuição com 8 bicos virados para baixo e para dentro
bm, bb = bmesh.new(), bmesh.new()
Z_CH = Z_LV2 - 0.12
toro(bm, LV + Vector((0, 0, Z_CH)), 0.17, 0.018, Z, nR=40, nr=10)
esfera(bm, LV + Vector((0, 0, Z_CH)), 0.03, 12)
for k in range(4):
    a = k * PI / 2
    tubo(bm, LV + Vector((0, 0, Z_CH)), LV + Vector((0.17 * math.cos(a), 0.17 * math.sin(a), Z_CH)), 0.012, 8)
BICOS = []
for k in range(8):
    a = k * 2 * PI / 8 + PI / 8
    p = LV + Vector((0.17 * math.cos(a), 0.17 * math.sin(a), Z_CH - 0.03))
    cil(bb, p, 0.012, 0.035, lados=10, r2=0.02)
    BICOS.append(p - Vector((0, 0, 0.02)))
cil(bb, LV + Vector((0, 0, Z_CH - 0.03)), 0.012, 0.035, lados=10, r2=0.02)
BICOS.append(LV + Vector((0, 0, Z_CH - 0.05)))
obj('chuveiro_anel', bm, 'cobre')
obj('chuveiro_bicos', bb, 'cromo')
# chuva dos chuveiros: estrias finas em cones (o objeto desce em laço)
bm = bmesh.new()
P_CHUVA = 0.12
for p in BICOS:
    for j in range(16):
        ang = random.uniform(0, 2 * PI)
        ab = random.uniform(0.05, 0.3)
        d = Vector((math.cos(ang) * math.sin(ab), math.sin(ang) * math.sin(ab), -math.cos(ab)))
        for s in range(int((Z_CH - Z_LV1 + 0.1) / P_CHUVA) + 2):
            q0 = p + d * (s * P_CHUVA / max(0.2, math.cos(ab)) + random.uniform(0, 0.05))
            q1 = q0 + d * 0.035
            rr = (Vector((q1.x, q1.y, 0)) - Vector((LV.x, LV.y, 0))).length
            if q1.z < Z_LV1 - 0.15 or rr > R_LV - 0.04:
                continue
            tubo(bm, q0, q1, 0.0018, 4)
chuva = obj('chuva_lavador', bm, 'agua')
# névoa dentro da câmara
bm = bmesh.new()
cil(bm, LV + Vector((0, 0, (Z_LV1 + Z_CH) / 2)), R_LV - 0.04, Z_CH - Z_LV1 - 0.02, lados=24)
obj('nevoa_lavador', bm, 'nevoa_lav')
# poça de água suja na base da câmara (topo do vaso visto através do vidro)
bm = bmesh.new()
cil(bm, LV + Vector((0, 0, Z_LV1 + 0.01)), R_LV - 0.02, 0.01, lados=32)
obj('lavador_poca', bm, 'agua_suja')
# entrada do coletor (lado de baixo) e saída do topo para a casca
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
d_lv = Vector((1, 1, 0)).normalized()
p_col = d_lv * (R_COL + r_col * 0.6) + Vector((0, 0, Z_COL))
q_lv = LV - d_lv * (R_LV + 0.2)
cano(bm, bf, bp, [p_col, q_lv + Vector((0, 0, Z_COL)), q_lv + Vector((0, 0, 0.78)), LV - d_lv * R_LV + Vector((0, 0, 0.78))], 0.085)
a_pen, z_pen = PEN[2]
saida = LV + Vector((0.0, 0.0, Z_LV2 + 0.16))
cano(bm, bf, bp, [saida, Vector((LV.x, LV.y, z_pen)), sup(a_pen, z_pen, 0.0)], 0.085, fl_pontas=False)
flange(bf, bp, sup(a_pen, z_pen, 0.105), normal_sup(a_pen, z_pen), 0.14, 0.03, 10)
obj('lavador_dutos', bm, 'galv')
obj('lavador_dutos_fl', bf, 'ferro')
obj('lavador_dutos_paraf', bp, 'aco')
# bomba de recirculação (leste) : sucção do vaso → bomba → recalque subindo até o anel dos chuveiros
BR = Vector((1.32, 0.52, 0))
bm, bf, bp, bmot = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
caixa_de(bf, (BR.x - 0.14, BR.y - 0.17, Z0), (BR.x + 0.14, BR.y + 0.17, Z0 + 0.05))
cil(bm, BR + Vector((0, 0.05, 0.22)), 0.1, 0.09, X, lados=24)                          # voluta
cil(bmot, BR + Vector((0, -0.08, 0.22)), 0.075, 0.18, Y, lados=20)                     # motor
for i in range(10):
    a = i * 2 * PI / 10
    caixa(bmot, BR + Vector((0.08 * math.cos(a), -0.08, 0.22 + 0.08 * math.sin(a))), (0.012, 0.16, 0.012),
          Matrix.Rotation(-a, 3, 'Y'))
caixa_de(bf, (BR.x - 0.08, BR.y - 0.17, Z0 + 0.05), (BR.x + 0.08, BR.y + 0.1, Z0 + 0.14))
obj('bomba_rec', bm, 'primer')
obj('bomba_rec_motor', bmot, 'grafite')
obj('bomba_rec_base', bf, 'ferro')
bm, bf = bmesh.new(), bmesh.new()
suc = [Vector((LV.x, LV.y - R_LV, Z_LV0 + 0.1)), Vector((LV.x, 0.7, Z_LV0 + 0.1)), Vector((LV.x, 0.7, 0.22)),
       Vector((BR.x, 0.7, 0.22)), BR + Vector((0, 0.1, 0.22))]
cano(bm, bf, bp, suc, 0.035)
rec = [BR + Vector((0, 0.05, 0.32)), BR + Vector((0, 0.05, 2.28)), Vector((1.25, BR.y + 0.05, 2.28)),
       Vector((1.25, LV.y, 2.28)), Vector((1.25, LV.y, Z_CH + 0.015))]
cano(bm, bf, bp, rec, 0.03)
viga(bf, Vector((BR.x + 0.07, BR.y + 0.05, Z0 + 0.05)), Vector((BR.x + 0.07, BR.y + 0.05, 2.3)), 0.05)
for z in (0.9, 1.6):                                                                    # abraçadeiras no poste
    caixa_de(bf, (BR.x + 0.025, BR.y + 0.03, z), (BR.x + 0.05, BR.y + 0.07, z + 0.04))
obj('lavador_canos', bm, 'cano')
obj('lavador_canos_fl', bf, 'ferro')
obj('lavador_canos_paraf', bp, 'aco')

# ------------------------------------------------------------------ lama negra: dreno do lavador → bomba → tanque (NO)
TQ = Vector((-1.08, 1.08, 0))
R_TQ, Z_TQ1 = 0.38, 0.72
Z_LAMA = 0.64
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
tubo_oco(bm, TQ + Vector((0, 0, (Z0 + Z_TQ1) / 2)), R_TQ, R_TQ - 0.02, Z_TQ1 - Z0, lados=48)
cil(bm, TQ + Vector((0, 0, Z0 + 0.02)), R_TQ, 0.04, lados=48)
toro(bm, TQ + Vector((0, 0, Z_TQ1)), R_TQ - 0.01, 0.018, Z, nR=48, nr=8)                # borda enrolada
for z in (Z0 + 0.12, 0.42):
    toro(bf, TQ + Vector((0, 0, z)), R_TQ + 0.006, 0.012, Z, nR=48, nr=6)
for k in range(12):                                                                     # nervuras verticais
    a = k * 2 * PI / 12
    caixa(bf, TQ + Vector(((R_TQ + 0.01) * math.cos(a), (R_TQ + 0.01) * math.sin(a), (Z0 + Z_TQ1) / 2)),
          (0.02, 0.025, Z_TQ1 - Z0 - 0.06), Matrix.Rotation(a, 3, 'Z'))
obj('tanque_lama', bm, 'grafite')
obj('tanque_cintas', bf, 'ferro')
bm = bmesh.new()
cil(bm, TQ + Vector((0, 0, Z_LAMA)), R_TQ - 0.021, 0.01, lados=48)
obj('lama_superficie', bm, 'lodo')
# crosta seca na borda (anel de fuligem) e transbordo escorrendo pelo lado
bm = bmesh.new()
toro(bm, TQ + Vector((0, 0, Z_LAMA + 0.004)), R_TQ - 0.04, 0.02, Z, nR=48, nr=6)
obj('lama_crosta', bm, 'fuligem')
bm = bmesh.new()
uv = bm.loops.layers.uv.new()
for a in (math.radians(a) for a in (-20, 5, 40, 250, 280, 300)):
    n = Vector((math.cos(a), math.sin(a), 0))
    escorrido_reto(bm, uv, TQ + n * (R_TQ + 0.022) + Vector((0, 0, Z_TQ1 - 0.01)), n,
                   random.uniform(0.05, 0.12), random.uniform(0.3, 0.6))
obj('tanque_escorridos', bm, 'escorre_negro')
bm = bmesh.new()
mancha(bm, (TQ.x + 0.32, TQ.y - 0.3), 0.18, Z0 + 0.002)
mancha(bm, (TQ.x - 0.05, TQ.y - 0.4), 0.12, Z0 + 0.002)
obj('poca_lama', bm, 'lodo')
# medidor de nível: boia em guia e régua
bm, bp = bmesh.new(), bmesh.new()
tubo(bm, TQ + Vector((0.2, 0.2, Z_TQ1 + 0.25)), TQ + Vector((0.2, 0.2, Z_LAMA - 0.1)), 0.008, 8)
viga(bm, TQ + Vector((0.2, 0.2, Z_TQ1 + 0.25)), TQ + Vector((0.27, 0.27, Z_TQ1 + 0.25)), 0.02)
viga(bm, TQ + Vector((0.27, 0.27, Z_TQ1 + 0.25)), TQ + Vector((0.27, 0.27, Z_TQ1 + 0.01)), 0.02)
cil(bp, TQ + Vector((0.2, 0.2, Z_LAMA + 0.02)), 0.04, 0.05, lados=16)
obj('nivel_guia', bm, 'aco')
obj('nivel_boia', bp, 'primer')
# dreno do lavador (ponta do cone) → bomba de lama (norte) → tanque
BL = Vector((0.0, 1.25, 0))
bm, bf, bp, bmot = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
caixa_de(bf, (BL.x - 0.17, BL.y - 0.12, Z0), (BL.x + 0.17, BL.y + 0.12, Z0 + 0.05))
cil(bm, BL + Vector((0.08, 0, 0.2)), 0.09, 0.08, X, lados=24)
cil(bmot, BL + Vector((-0.04, 0, 0.2)), 0.07, 0.16, X, lados=20)
caixa_de(bf, (BL.x - 0.08, BL.y - 0.07, Z0 + 0.05), (BL.x + 0.08, BL.y + 0.07, Z0 + 0.13))
obj('bomba_lama', bm, 'amarelo')
obj('bomba_lama_motor', bmot, 'grafite')
obj('bomba_lama_base', bf, 'ferro')
bm, bf = bmesh.new(), bmesh.new()
dreno = [LV + Vector((0, 0, Z_LV0 - 0.24)), LV + Vector((0, 0, 0.18)), Vector((LV.x, BL.y, 0.18)),
         Vector((BL.x + 0.12, BL.y, 0.18))]
cano(bm, bf, bp, dreno, 0.035)
lama_cano = [BL + Vector((0.08, 0, 0.29)), BL + Vector((0.08, 0, 0.42)), Vector((-0.6, BL.y, 0.42)),
             Vector((-0.6, BL.y, 0.92)), Vector((TQ.x + 0.2, TQ.y + 0.12, 0.92)), Vector((TQ.x + 0.2, TQ.y + 0.12, 0.8))]
cano(bm, bf, bp, lama_cano, 0.035)
viga(bf, Vector((-0.6, BL.y + 0.045, Z0)), Vector((-0.6, BL.y + 0.045, 0.95)), 0.04)
obj('lama_canos', bm, 'cano')
obj('lama_canos_fl', bf, 'ferro')
# jorro de lama caindo do bocal na superfície + anéis de onda
bm = bmesh.new()
BOCA_LAMA = Vector((TQ.x + 0.2, TQ.y + 0.12, 0.78))
pts = [BOCA_LAMA - Z * (BOCA_LAMA.z - Z_LAMA) * k / 8 + Vector((0.003 * math.sin(k), 0, 0)) for k in range(9)]
mangueira(bm, pts, 0.016)
obj('jorro_lama', bm, 'lodo')
ondas = []
for k in range(3):
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 1.0, 0.12, Z, nR=32, nr=5)
    o = obj('onda_lama%d' % k, bm, 'lodo')
    ondas.append(o)
bolhas = []
for k in range(5):
    bm = bmesh.new()
    esfera(bm, (0, 0, 0), 1.0, 14, (1, 1, 0.6))
    o = obj('bolha%d' % k, bm, 'lodo')
    ang, rr = random.uniform(0, 2 * PI), random.uniform(0.05, 0.28)
    bolhas.append((o, TQ + Vector((rr * math.cos(ang), rr * math.sin(ang), Z_LAMA + 0.005)), random.random(),
                   random.uniform(0.025, 0.045)))

# ------------------------------------------------------------------ esteira de resíduo (sul) e blocos negros
YE0, YE1 = -0.3, -1.5
ZE = 0.3                     # topo da lona
LE = 0.15                    # meia largura
bm, bp, bl = bmesh.new(), bmesh.new(), bmesh.new()
for s in (-1, 1):
    caixa_de(bm, (s * (LE + 0.02) - 0.012, YE1, ZE - 0.1), (s * (LE + 0.02) + 0.012, YE0, ZE + 0.04))   # longarinas
    caixa_de(bm, (s * (LE + 0.02) - 0.03, YE1, ZE + 0.03), (s * (LE + 0.02) + 0.012 * s, YE0, ZE + 0.04))
for y in (-0.55, -0.8, -1.4):
    for s in (-1, 1):
        caixa_de(bm, (s * (LE + 0.02) - 0.02, y - 0.02, Z0), (s * (LE + 0.02) + 0.02, y + 0.02, ZE - 0.1))
        caixa_de(bp, (s * (LE + 0.02) - 0.05, y - 0.05, Z0), (s * (LE + 0.02) + 0.05, y + 0.05, Z0 + 0.012))
    caixa_de(bm, (-LE - 0.02, y - 0.015, Z0 + 0.08), (LE + 0.02, y + 0.015, Z0 + 0.1))
obj('esteira_quadro', bm, 'amarelo')
obj('esteira_sapatas', bp, 'ferro')
bm = bmesh.new()
caixa_de(bm, (-LE, YE1, ZE - 0.012), (LE, YE0, ZE))
caixa_de(bm, (-LE, YE1, ZE - 0.075), (LE, YE0, ZE - 0.063))
obj('esteira_lona', bm, 'borracha')
roletes = []
for k in range(9):
    y = YE0 - 0.06 - k * (YE0 - YE1 - 0.12) / 8
    piv = bpy.data.objects.new('rolete%d' % k, None)
    sc.collection.objects.link(piv)
    piv.location = (0, y, ZE - 0.04)
    b1 = bmesh.new()
    cil(b1, (0, 0, 0), 0.026, 2 * LE + 0.02, X, lados=16)
    for x in (-LE + 0.03, 0, LE - 0.03):
        caixa(b1, (x, 0, 0.0), (0.012, 0.054, 0.006))
    obj('rolete%d_m' % k, b1, 'aco', piv)
    roletes.append(piv)
# motor de acionamento com redutor e protetor da corrente (lado leste, ponta sul)
bm, bmot, bp = bmesh.new(), bmesh.new(), bmesh.new()
caixa_de(bm, (LE + 0.035, -1.44, ZE - 0.11), (LE + 0.1, -1.3, ZE + 0.02))          # redutor
cil(bmot, (LE + 0.17, -1.37, ZE - 0.12), 0.06, 0.16, Y, lados=20)
caixa_de(bp, (LE + 0.09, -1.45, Z0), (LE + 0.25, -1.29, ZE - 0.18))
obj('esteira_redutor', bm, 'primer')
obj('esteira_motor', bmot, 'grafite')
obj('esteira_base_motor', bp, 'ferro')
# calha de saída na borda (porta de item, tile do meio sul) e listra
bm = bmesh.new()
caixa_de(bm, (-LE - 0.03, -1.5, ZE - 0.02), (LE + 0.03, -1.47, ZE + 0.09))
obj('esteira_boca', bm, 'aco')
# blocos negros compactos
BLOCO = 0.12
blocos = []
for k in range(5):
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (BLOCO, BLOCO * random.uniform(0.95, 1.05), BLOCO * 0.92))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.008, segments=2, affect='EDGES')
    for v in bm.verts:
        v.co += Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * 0.003
    o = obj('bloco%d' % k, bm, 'bloco')
    blocos.append((o, k, random.uniform(-0.15, 0.15)))
# migalhas e pó preto caídos ao longo da esteira e embaixo
bm = bmesh.new()
for k in range(70):
    y = random.uniform(YE1 + 0.02, YE0 - 0.02)
    x = random.uniform(-0.3, 0.3) if random.random() < 0.6 else random.uniform(-LE + 0.01, LE - 0.01)
    z = Z0 if abs(x) > LE + 0.04 else Z0
    pedra(bm, (x, y, z + 0.004), random.uniform(0.006, 0.016), 0.6)
obj('migalhas', bm, 'bloco')
bm = bmesh.new()
mancha(bm, (0, -0.95), 0.28, Z0 + 0.001)
mancha(bm, (0.05, -0.35), 0.2, Z0 + 0.001)
obj('po_preto', bm, 'fuligem')

# ------------------------------------------------------------------ armário elétrico (oeste) e calha de cabos no chão
bm, bp, bl, bv = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
AX = -1.36
caixa_de(bm, (AX - 0.1, -0.32, Z0), (AX + 0.11, 0.32, 1.05))
caixa_de(bm, (AX - 0.12, -0.34, 1.05), (AX + 0.13, 0.34, 1.09))                      # chapéu
obj('armario', bm, 'grafite')
for y0, y1 in ((-0.3, -0.01), (0.01, 0.3)):                                           # portas de acesso (aparafusadas)
    caixa_de(bv, (AX + 0.11, y0, Z0 + 0.06), (AX + 0.118, y1, 1.02))
    for z in (Z0 + 0.1, 0.55, 0.98):
        for y in (y0 + 0.02, y1 - 0.02):
            cil(bp, (AX + 0.121, y, z), 0.007, 0.008, X, lados=6)
for k in range(6):                                                                    # venezianas
    caixa_de(bp, (AX + 0.116, -0.25, 0.25 + k * 0.035), (AX + 0.13, -0.06, 0.265 + k * 0.035))
for k, mat in enumerate(('verde', 'verde', 'vermelha', 'lampada')):
    cil(bl, (AX + 0.12, 0.08 + k * 0.045, 0.9), 0.011, 0.012, X, lados=12)
obj('armario_portas', bv, 'verde_vel')
obj('armario_pecas', bp, 'ferro')
leds = obj('armario_leds', bl, 'verde')
# feixe de cabos: armário → escada de cabos (sobe para a torre) e calha no chão → prensa e esteira
bc, bt = bmesh.new(), bmesh.new()
for k in range(3):
    mangueira(bc, bezier(Vector((AX + 0.04 + k * 0.02, 0.0, 1.09)), Vector((AX + 0.04, 0.0, 1.35)),
                         sup(A_ESC, ZB + 0.08, DB + 0.18) + Vector((0, 0, -0.3)),
                         sup(A_ESC, ZB + 0.08, DB + 0.18) + Vector((0, (k - 1) * 0.04, 0)), 14), 0.013)
caixa_de(bt, (AX + 0.11, -0.06, Z0), (-0.27, 0.06, Z0 + 0.05))                        # calha no chão
for k in range(12):
    x = AX + 0.15 + k * 0.08
    caixa_de(bt, (x, -0.065, Z0 + 0.048), (x + 0.012, 0.065, Z0 + 0.056))
obj('cabos_armario', bc, 'borracha')
obj('calha_chao', bt, 'galv')
t = bpy.data.curves.new('arm_txt', 'FONT')
t.body = '480V  PA2'
t.size = 0.05
to = bpy.data.objects.new('arm_txt', t)
sc.collection.objects.link(to)
to.data.materials.append(M['estencil'])
to.location = (AX + 0.1185, 0.03, 0.62)
to.rotation_euler = (PI / 2, 0, PI / 2)

# ------------------------------------------------------------------ desgaste na base: fuligem, óleo, escorridos nas pernas
bm = bmesh.new()
for k in range(26):
    ang = random.uniform(0, 2 * PI)
    rr = random.uniform(0.35, 1.25)
    p = (rr * math.cos(ang), rr * math.sin(ang))
    if abs(p[0]) < LE + 0.08 and p[1] < -0.25:
        continue
    mancha(bm, p, random.uniform(0.08, 0.22), Z0 + 0.0012)
obj('base_fuligem', bm, 'fuligem')
bm = bmesh.new()
for p, r in (((0.0, 0.0), 0.0),):
    pass
for p, r in (((BR.x - 0.05, BR.y - 0.1), 0.09), ((BL.x - 0.15, BL.y - 0.1), 0.08), ((0.3, -0.15), 0.07)):
    mancha(bm, p, r, Z0 + 0.0015)
obj('oleo_chao', bm, 'oleo')
bm = bmesh.new()
uv = bm.loops.layers.uv.new()
for th in COLS:                                                          # escorridos negros pelas pernas
    for s in (-1, 1):
        a = th + s * ABRE
        pe = Vector((RPE * math.cos(a), RPE * math.sin(a), Z0 + 0.2))
        topo = Vector((RB * math.cos(th), RB * math.sin(th), ZB - 0.1))
        d = (topo - pe).normalized()
        nrm = Vector((math.cos(a), math.sin(a), 0))
        if random.random() < 0.7:
            L_ = random.uniform(0.4, 0.9)
            pts = [topo.lerp(pe, 0.05 + L_ * k / 6) + nrm * 0.039 for k in range(7)]
            faixa(bm, uv, pts, [nrm] * 7, 0.05)
obj('pernas_escorridos', bm, 'escorre_negro')

# ------------------------------------------------------------------ volumes: funil de fumaça, braços internos, ar limpo
bm = bmesh.new()
cil(bm, (0, 0, 2.95), 8.2, 5.6, lados=64)
vort = obj('funil_fumaca', bm, 'vortice')
bm = bmesh.new()
cil(bm, (0, 0, 1.15), 1.22, 1.3, lados=48)
vort_in = obj('fumaca_interna', bm, 'vortice_in')
# linhas de campo violeta acompanhando a espiral perto da boca (tubos finos)
bm = bmesh.new()
for k in range(3):
    pts = []
    for s in range(60):
        u = s / 59
        rho = 1.7 + 3.0 * (1 - u) ** 1.2
        th = k * 2 * PI / 3 - math.log(rho) * K_VORT / 3 + 0.9
        z = 0.75 + 0.42 * max(rho - 1.0, 0) ** 1.12 + 0.08 * math.sin(u * 9)
        pts.append(Vector((rho * math.cos(th), rho * math.sin(th), z)))
    mangueira(bm, pts, 0.003)
campo_esp = obj('campo_espiral', bm, 'campo')
# ar limpo: coluna fraca + tremor refrativo por ventilador, centelhas subindo
tremores = []
for k, c in enumerate(FANS):
    bm = bmesh.new()
    cil(bm, c + Vector((0, 0, ZD + 1.6)), RF - 0.02, 2.0, lados=32, r2=RF + 0.18)
    obj('ar_limpo%d' % k, bm, 'ar_limpo')
    bm = bmesh.new()
    cil(bm, (0, 0, 0), RF - 0.03, 1.4, lados=32, r2=RF + 0.1)
    o = obj('tremor%d' % k, bm, 'tremor')
    suavizar(o)
    o.location = c + Vector((0, 0, ZD + 1.35))
    o.visible_shadow = False
    tremores.append(o)
centelhas = []
for k in range(66):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    o = obj('centelha%d' % k, bm, 'centelha')
    o.visible_shadow = False
    c = FANS[k % 3]
    ang, rr = random.uniform(0, 2 * PI), random.uniform(0.0, RF - 0.04)
    centelhas.append((o, c + Vector((rr * math.cos(ang), rr * math.sin(ang), ZD + 0.55)), random.random(),
                      random.uniform(0.8, 1.4), random.uniform(0.004, 0.008), random.uniform(0, 2 * PI)))
# gotas negras pingando do cristal no funil
gotas = []
for k in range(3):
    bm = bmesh.new()
    esfera(bm, (0, 0, 0), 0.012, 10, (1, 1, 1.5))
    gotas.append((obj('gota_negra%d' % k, bm, 'lodo'), k * 32 + random.randint(0, 6),
                  Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0))))
# fumacinha escapando da comporta quando abre
fum_porta = []
for k in range(2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    fum_porta.append((obj('fumaca_porta%d' % k, bm, 'fumaca_porta'), k * 0.5))

cristal_em = M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
campo_forca = M['campo'].node_tree.nodes['forca'].inputs[1]
luz_cr_d = bpy.data.lights.new('luz_cristal', 'POINT')
luz_cr_d.color = VIOLETA
luz_cr_d.shadow_soft_size = 0.08
luz_cr = bpy.data.objects.new('luz_cristal', luz_cr_d)
sc.collection.objects.link(luz_cr)
luz_cr.location = (0, 0, ZC)
luz_farol_d = bpy.data.lights.new('luz_farol', 'POINT')
luz_farol_d.color = (1.0, 0.5, 0.1)
luz_farol_d.shadow_soft_size = 0.03
luz_farol = bpy.data.objects.new('luz_farol', luz_farol_d)
sc.collection.objects.link(luz_farol)
luz_farol.location = (0, 0, ZD + 0.24)
farol_em = M['lampada'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']

# volumes não entram na oclusão (sujeira por AO) das peças nem do chão
for o in sc.objects:
    if o.type == 'MESH' and o.data.materials and o.data.materials[0].name in (
            'Funil de fumaça', 'Fumaça interna', 'Névoa do lavador', 'Fumaça da comporta'):
        o.visible_diffuse = False
        o.visible_glossy = False
        o.visible_transmission = False
print('GEOMETRIA ok', flush=True)

# ------------------------------------------------------------------ animação (laço de 4 s)
FR_FOTO = int(QUADROS * 0.3) + 1
PASSO = 0.3                  # espaço entre blocos; 2 blocos por laço
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for k, piv in enumerate(rotores):
        piv.rotation_euler = (0, 0, -2 * PI * (11 + k) * fr)
        piv.keyframe_insert('rotation_euler', frame=q)
    vort.rotation_euler = (0, 0, 2 * PI * fr)
    vort.keyframe_insert('rotation_euler', frame=q)
    vort_in.rotation_euler = (0, 0, 2 * PI * 2 * fr)
    vort_in.keyframe_insert('rotation_euler', frame=q)
    campo_esp.rotation_euler = (0, 0, 2 * PI * fr)
    campo_esp.keyframe_insert('rotation_euler', frame=q)
    piv_cr.rotation_euler = (0, 0, 2 * PI * fr)
    piv_cr.location = (0, 0, ZC + 0.02 * math.sin(2 * PI * 2 * fr))
    piv_cr.keyframe_insert('rotation_euler', frame=q)
    piv_cr.keyframe_insert('location', frame=q)
    pulso = 0.75 + 0.25 * math.sin(2 * PI * 4 * fr)
    cristal_em.default_value = 1.6 * pulso
    cristal_em.keyframe_insert('default_value', frame=q)
    campo_forca.default_value = 7.0 * pulso
    campo_forca.keyframe_insert('default_value', frame=q)
    luz_cr_d.energy = 90 * pulso
    luz_cr_d.keyframe_insert('energy', frame=q)
    pisca = 1.0 if (q // 12) % 2 == 0 else 0.1
    farol_em.default_value = 8.0 * pisca
    farol_em.keyframe_insert('default_value', frame=q)
    luz_farol_d.energy = 6 * pisca
    luz_farol_d.keyframe_insert('energy', frame=q)
    for t_ in tremores:
        t_.rotation_euler = (0, 0, 2 * PI * fr)
        t_.keyframe_insert('rotation_euler', frame=q)
    # esteira: blocos andam 0,6 m por laço; a guilhotina abre quando um bloco passa na boca
    abre = 0.0
    for o, k, dx in blocos:
        u = (k * PASSO + fr * 2 * PASSO) % (5 * PASSO)
        y = -0.12 - u
        o.location = (dx * 0.2, y, ZE + BLOCO * 0.46)
        o.rotation_euler = (0, 0, dx * 0.3)
        o.hide_render = y < YE1 + 0.02
        abre = max(abre, 1.0 - min(abs(y + 0.27) / 0.12, 1.0))
        for c in ('location', 'rotation_euler', 'hide_render'):
            o.keyframe_insert(c, frame=q)
    piv_gate.location = (0, 0, 0.14 * suave(abre * 1.6))
    piv_gate.keyframe_insert('location', frame=q)
    for k, piv in enumerate(roletes):
        piv.rotation_euler = (-2 * PI * fr * 2 * PASSO / (2 * PI * 0.026), 0, 0)
        piv.keyframe_insert('rotation_euler', frame=q)
    for o, ph in fum_porta:
        u = (fr * 2 + ph) % 1.0
        o.location = (0.02 * math.sin(u * 6), -0.33 - 0.1 * u, ZP0 + 0.12 + 0.55 * u)
        s = 0.05 + 0.13 * u
        o.scale = (s, s, s * 1.2)
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # gotas negras do cristal ao funil
    for o, fase, dx in gotas:
        t_q = (q - 1 + fase) % 32
        z0, z1 = ZC - 0.23, ZP1 + 0.27
        queda = math.sqrt(2 * (z0 - z1) / 9.8) * FPS
        if t_q < queda:
            tt = t_q / FPS
            o.location = Vector((0, 0, z0 - 4.9 * tt * tt)) + dx
            o.hide_render = False
        else:
            o.location = Vector((0, 0, z0)) + dx
            o.hide_render = t_q < queda + 6
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('hide_render', frame=q)
    # chuva do lavador desce em laço
    chuva.location = (0, 0, -P_CHUVA * ((fr * 8) % 1.0))
    chuva.keyframe_insert('location', frame=q)
    # lama: ondas do jorro e bolhas que estouram
    for k, o in enumerate(ondas):
        u = (fr * 3 + k / 3) % 1.0
        s = 0.02 + 0.12 * u
        o.location = (BOCA_LAMA.x, BOCA_LAMA.y, Z_LAMA + 0.006)
        o.scale = (s, s, 0.05)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for o, p, ph, r in bolhas:
        u = (fr * 2 + ph) % 1.0
        s = r * suave(u / 0.85) if u < 0.85 else 0.002
        o.location = p
        o.scale = (s, s, s)
        o.hide_render = u >= 0.85
        for c in ('location', 'scale', 'hide_render'):
            o.keyframe_insert(c, frame=q)
    # centelhas: sobem, giram em hélice, piscam
    for o, p, ph, vel, r, a0 in centelhas:
        u = (ph + fr * vel) % 1.0
        z = p.z + 2.6 * u
        ang = a0 + u * 3
        o.location = (p.x + 0.05 * math.cos(ang) * (1 + u * 2), p.y + 0.05 * math.sin(ang) * (1 + u * 2), z)
        tw = 0.5 + 0.5 * math.sin(2 * PI * (fr * 6 + ph * 7))
        s = r * (0.3 + tw) * (1 - u) ** 0.5
        o.scale = (max(s, 0.0005),) * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)

print('ANIMACAO ok', flush=True)
# ------------------------------------------------------------------ cena: luz, céu enfumaçado, chão, câmera
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.2
sol.angle = math.radians(6)
sol.color = (1.0, 0.93, 0.82)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bgn = mundo.node_tree.nodes['Background']
bgn.inputs['Color'].default_value = (0.5, 0.47, 0.42, 1)
bgn.inputs['Strength'].default_value = 0.75
bm = bmesh.new()
caixa_de(bm, (-300, -300, -0.02), (300, 300, 0.0))
obj('chao', bm, 'chao')
# pedras e entulho em volta
bm = bmesh.new()
for k in range(90):
    ang, rr = random.uniform(0, 2 * PI), random.uniform(2.2, 9.0)
    pedra(bm, (rr * math.cos(ang), rr * math.sin(ang), 0.0), random.uniform(0.03, 0.18), 0.5)
obj('pedras', bm, 'concreto')
sc.render.engine = 'CYCLES'
sc.cycles.device = 'GPU'
try:
    prf = bpy.context.preferences.addons['cycles'].preferences
    prf.compute_device_type = 'OPTIX'
    prf.get_devices()
    for dv_ in prf.devices:
        dv_.use = True
except Exception:
    sc.cycles.device = 'CPU'
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 10
sc.cycles.transmission_bounces = 10
sc.cycles.transparent_max_bounces = 32
sc.cycles.volume_bounces = 1
sc.cycles.volume_step_rate = 3.0
sc.cycles.volume_max_steps = 256
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.2
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.clip_end = 200


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 100
    sc.frame_set(FR_FOTO)
    if so_uma in (None, '0'):
        sc.render.resolution_x, sc.render.resolution_y = 1200, 1400
        mirar((7.4, -8.9, 4.0), (0.0, 0.0, 2.45), 30)
        sc.render.filepath = os.path.join(AQUI, 'purificador_atm_0.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        campo_esp.hide_render = True                                     # linha de campo passaria na lente
        sc.render.resolution_x, sc.render.resolution_y = 1400, 1050
        sc.view_settings.exposure = 0.35
        mirar((0.3, -2.25, 1.3), (0.0, -0.15, 0.85), 26)
        sc.render.filepath = os.path.join(AQUI, 'purificador_atm_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'vortice'):
        campo_esp.hide_render = False
        sc.view_settings.exposure = -0.2
        sc.render.resolution_x, sc.render.resolution_y = 1500, 1100
        mirar((7.5, -9.5, 10.5), (0.0, 0.0, 1.0), 24)
        sc.render.filepath = os.path.join(AQUI, 'purificador_atm_vortice.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 24
    sc.render.resolution_x, sc.render.resolution_y = 800, 700
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    campo_esp.hide_render = (Vector(v[0:3]).length < 4)
    sc.render.filepath = os.path.join(AQUI, 'purificador_atm_teste.png')
    bpy.ops.render.render(write_still=True)
print('PURIFICADOR ok', flush=True)
