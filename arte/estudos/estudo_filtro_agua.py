"""Estudo isolado (fora do jogo): filtro de água da IA, 2×2 tiles, encostado num rio de água turva ao sul.
Tomada d'água pelo ralo da borda sul: câmara de grade (com galhos e borra presos) no cais de concreto, cano de sucção
até a bomba centrífuga (impulsor de bronze girando atrás do visor de vidro, motor com aletas). A bomba recalca para o
separador de campo: a água atravessa o ar entre duas bocas, passa por uma membrana violeta presa num anel com
emissores de cristal e sai limpa; a lama solta flutua para fora, guiada por anéis de campo até a caçamba de lodo.
Depois, três colunas de vidro e aço com camadas (cascalho, areia, carvão ativado, cristal) e a água clareando de baixo
para cima; coletor no topo com válvula atuada por pistão (pistao0) leva a água limpa por um cano de saída que jorra
de volta no rio, abrindo uma mancha clara na água turva. Lavagem reversa: dreno do topo das colunas com válvula
atuada por pistão (pistao1) despeja borra marrom na caçamba de lodo. Manômetros, flanges, mangueiras hidráulicas,
eletrocalha, armário de controle selado (sem porta: não há humanos).
Uso: blender -b --python estudo_filtro_agua.py -- foto  |  -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(23)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def base_de(eixo):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    return q @ X, q @ Y, q @ Z


def toro(bm, centro, R, r, eixo=Z, nR=48, nr=12):
    """Anel tubular contínuo em volta do eixo."""
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
    """Tubo de parede grossa fechado (vidro com espessura real: refrata certo)."""
    u, v, w = base_de(eixo)
    centro = Vector(centro)
    an = {}
    for k, (r, z) in enumerate(((ro, -h / 2), (ro, h / 2), (ri, -h / 2), (ri, h / 2))):
        an[k] = [bm.verts.new(centro + (u * math.cos(a) + v * math.sin(a)) * r + w * z)
                 for a in (i * 2 * PI / lados for i in range(lados))]
    fs = []
    for i in range(lados):
        j = (i + 1) % lados
        fs.append(bm.faces.new((an[0][i], an[0][j], an[1][j], an[1][i])))     # fora
        fs.append(bm.faces.new((an[2][i], an[3][i], an[3][j], an[2][j])))     # dentro
        fs.append(bm.faces.new((an[1][i], an[1][j], an[3][j], an[3][i])))     # topo
        fs.append(bm.faces.new((an[0][i], an[2][i], an[2][j], an[0][j])))     # fundo
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def esfera(bm, c, r, seg=20):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def flange(bm, bp, c, eixo, r, esp=0.022, n=8):
    """Flange com parafusos (bp recebe os parafusos)."""
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(bm, c, r, esp, eixo, lados=24)
    u, v, _ = base_de(eixo)
    for k in range(n):
        a = k * 2 * PI / n + 0.3
        cil(bp, c + (u * math.cos(a) + v * math.sin(a)) * (r - 0.011), 0.0055, esp + 0.014, eixo, lados=6)


def cano(bm, bf, bp, pts, r, lados=24, fl=True, fl_pontas=True):
    """Cano por pontos: trechos retos, cotovelo redondo (esfera) nos cantos e flanges perto das emendas."""
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


def bez(p0, p1, p2, p3, t):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    return p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3


def manometro(bm_ac, bm_face, bm_pont, p, cima, face):
    """Manômetro: niple saindo de p na direção 'cima', mostrador virado para 'face'."""
    p, cima, face = Vector(p), Vector(cima).normalized(), Vector(face).normalized()
    tubo(bm_ac, p, p + cima * 0.07, 0.008, 8)
    c = p + cima * 0.1
    cil(bm_ac, c, 0.038, 0.024, face, lados=20)
    cil(bm_face, c + face * 0.0125, 0.032, 0.002, face, lados=20)
    u, v, _ = base_de(face)
    ang = random.uniform(0.3, 2.4)
    d = u * math.cos(ang) + v * math.sin(ang)
    viga(bm_pont, c + face * 0.0145 - d * 0.005, c + face * 0.0145 + d * 0.026, 0.003)


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat(nome='Vidro', sujo=1.0):
    """Vidro das colunas (sem refração, verniz que reflete: não faz lente), encardido de barro embaixo."""
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
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.75, 'From Max': 0.35, 'To Min': 0.0, 'To Max': sujo})
    nt.links.new(sep.outputs['Z'], alt.inputs['Value'])
    enc = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(alt.outputs['Result'], enc.inputs[0])
    nt.links.new(ru.outputs['Fac'], enc.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.97, 0.98, 0.98, 1)
    cor.inputs[7].default_value = (0.35, 0.25, 0.12, 1)
    nt.links.new(enc.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.03, 'To Max': 0.5})
    nt.links.new(enc.outputs['Value'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    return m


def agua_grad_mat(nome, eixo, v0, v1, cor0, cor1, tr0, tr1, ior=1.33):
    """Água que muda de barrenta para limpa ao longo de um eixo do mundo (v0 → v1)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['IOR'].default_value = ior
    b.inputs['Roughness'].default_value = 0.04
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': v0, 'From Max': v1})
    nt.links.new(sep.outputs[eixo], t.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 14.0, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    tt = no(nt, 'ShaderNodeMath', operation='ADD')                       # fronteira turva irregular
    nt.links.new(t.outputs['Result'], tt.inputs[0])
    sub = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    sub.inputs[1].default_value = 0.35
    sub.inputs[2].default_value = -0.175
    nt.links.new(ru.outputs['Fac'], sub.inputs[0])
    nt.links.new(sub.outputs['Value'], tt.inputs[1])
    tt.use_clamp = True
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (*cor0, 1)
    cor.inputs[7].default_value = (*cor1, 1)
    nt.links.new(tt.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    tr = no(nt, 'ShaderNodeMapRange', **{'To Min': tr0, 'To Max': tr1})
    nt.links.new(tt.outputs['Value'], tr.inputs['Value'])
    nt.links.new(tr.outputs['Result'], b.inputs['Transmission Weight'])
    return m


def rio_mat():
    """Rio de água turva: marrom-esverdeado opaco com redemoinhos de silte e ondulação."""
    m = bpy.data.materials.new('Rio')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['IOR'].default_value = 1.33
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.9, 'Detail': 6.0, 'Distortion': 1.5})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.075, 0.055, 0.025, 1)
    cor.inputs[7].default_value = (0.17, 0.12, 0.055, 1)
    nt.links.new(ru.outputs['Fac'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    onda = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], onda.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.12})
    nt.links.new(onda.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mancha_limpa_mat():
    """Pluma de água limpa que se abre no rio onde o jato cai: some na borda (coordenada do objeto, raio 1)."""
    m = bpy.data.materials.new('Pluma limpa')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.045, 0.075, 0.06, 1)
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['IOR'].default_value = 1.33
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    tc = no(nt, 'ShaderNodeTexCoord')
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], ln.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.45
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(ln.outputs['Value'], soma.inputs[2])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.1, 'From Max': 0.5, 'To Min': 0.0, 'To Max': 0.85})
    nt.links.new(soma.outputs['Value'], f.inputs['Value'])
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def cristal_mat():
    """Cristal da IA: vidro violeta translúcido com brilho interno (força animada)."""
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.2
    b.inputs['Transmission Weight'].default_value = 0.4
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 2.0
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 70.0})                # grãos
    tc = no(nt, 'ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def granulado_mat(nome, cor, escala, rough=0.9):
    """Leito filtrante: grãos (voronoi) com variação de cor e relevo."""
    m = mats.material(nome, cor, 0, rough, pintura=False, sujeira=0.2, desgaste=0.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = no(nt, 'ShaderNodeTexCoord')
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': escala})
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.8})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def campo_mat(nome, cor, dens, emis):
    """Membrana de campo em volume: névoa violeta que brilha, mais densa no meio (ruído)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.05, 0.02, 0.1, 1)
    vol.inputs['Emission Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.6})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = dens
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca')
    e.inputs[1].default_value = emis
    nt.links.new(mul.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def terra_mat():
    """Margem: terra seca com tufos esverdeados em cima, lama escura e molhada perto da água (por altura)."""
    m = bpy.data.materials.new('Terra')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.5, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])
    seca = no(nt, 'ShaderNodeMix', data_type='RGBA')
    seca.inputs[6].default_value = (0.19, 0.15, 0.10, 1)
    seca.inputs[7].default_value = (0.11, 0.13, 0.05, 1)
    capim = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], capim.inputs['Value'])
    nt.links.new(capim.outputs['Result'], seca.inputs[0])
    molh = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.05, 'From Max': -0.3})
    nt.links.new(sep.outputs['Z'], molh.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[7].default_value = (0.055, 0.04, 0.025, 1)
    nt.links.new(molh.outputs['Result'], cor.inputs[0])
    nt.links.new(seca.outputs[2], cor.inputs[6])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.35
    nt.links.new(cor.outputs[2], var.inputs[6])
    nt.links.new(fino.outputs['Color'], var.inputs[7])
    nt.links.new(var.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.95, 'To Max': 0.3})
    nt.links.new(molh.outputs['Result'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.4})
    nt.links.new(fino.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
Z_LIMPA_M = 0.84


def jato_mat():
    """Jato de água limpa: transparente com estrias brancas de ar (ruído esticado ao longo da queda)."""
    m = bpy.data.materials.new('Jato')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.9, 0.96, 0.97, 1)
    ag.inputs['Transmission Weight'].default_value = 1.0
    ag.inputs['Roughness'].default_value = 0.05
    ag.inputs['IOR'].default_value = 1.33
    br = no(nt, 'ShaderNodeBsdfPrincipled')
    br.inputs['Base Color'].default_value = (0.78, 0.8, 0.8, 1)
    br.inputs['Roughness'].default_value = 0.5
    br.inputs['Transmission Weight'].default_value = 0.3
    tc = no(nt, 'ShaderNodeTexCoord')
    esc = no(nt, 'ShaderNodeMapping')
    esc.inputs['Scale'].default_value = (14.0, 14.0, 2.5)
    nt.links.new(tc.outputs['Object'], esc.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 6.0})
    nt.links.new(esc.outputs['Vector'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.65})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(ag.outputs[0], mix.inputs[1])
    nt.links.new(br.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def pelicula_mat():
    """Película da membrana de campo: violeta translúcida com anéis de interferência que brilham."""
    m = bpy.data.materials.new('Película')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*VIOLETA, 1)
    tc = no(nt, 'ShaderNodeTexCoord')
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], ln.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 4.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.25
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(ln.outputs['Value'], soma.inputs[2])
    onda = no(nt, 'ShaderNodeMath', operation='SINE')
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='fase')
    mul.inputs[1].default_value = 38.0
    nt.links.new(soma.outputs['Value'], mul.inputs[0])
    nt.links.new(mul.outputs['Value'], onda.inputs[0])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0, 'To Min': 0.12, 'To Max': 0.5})
    nt.links.new(onda.outputs['Value'], f.inputs['Value'])
    forca = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0, 'To Min': 0.6, 'To Max': 4.0})
    nt.links.new(onda.outputs['Value'], forca.inputs['Value'])
    nt.links.new(forca.outputs['Result'], em.inputs['Strength'])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.85, ferrugem=0.35),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.75),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cano': mats.material('Cano', (0.30, 0.31, 0.32), 1.0, 0.5, pintura=False, ferrugem=0.9, sujeira=0.9),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'bronze': mats.material('Bronze', (0.62, 0.40, 0.18), 1.0, 0.3, pintura=False, sujeira=0.5, ferrugem=0.2),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'ponteiro': mats.material('Ponteiro', (0.5, 0.05, 0.02), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.13, 0.085, 0.04), 0, 0.22, pintura=False, sujeira=0.4, desgaste=0.0),
    'lodo': mats.material('Lodo', (0.075, 0.05, 0.025), 0, 0.15, pintura=False, sujeira=0.3, desgaste=0.0),
    'lama_seca': mats.material('Lama seca', (0.2, 0.15, 0.09), 0, 0.9, pintura=False, sujeira=0.3, desgaste=0.0),
    'alga': mats.material('Alga', (0.05, 0.075, 0.025), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'galho': mats.material('Galho', (0.11, 0.08, 0.05), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'espuma': mats.material('Espuma', (0.62, 0.6, 0.55), 0, 0.85, pintura=False, sujeira=0.1, desgaste=0.0),
    'escuma': mats.material('Escuma', (0.17, 0.13, 0.07), 0, 0.5, pintura=False, sujeira=0.2, desgaste=0.0),
    'pedra': mats.material('Pedra', (0.15, 0.145, 0.13), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'cascalho': granulado_mat('Cascalho', (0.30, 0.29, 0.27), 45.0),
    'areia': granulado_mat('Areia', (0.55, 0.44, 0.28), 160.0),
    'carvao': granulado_mat('Carvão ativado', (0.022, 0.022, 0.024), 90.0, 0.6),
    'cristal': cristal_mat(),
    'vidro': vidro_mat(sujo=0.45),
    'visor': vidro_mat('Visor', 0.25),
    'agua_coluna': agua_grad_mat('Água da coluna', 'Z', Z_LIMPA_M, 1.08, (0.62, 0.55, 0.5), (0.78, 0.92, 0.94), 0.55, 0.93, 1.05),
    'agua_turva': agua_grad_mat('Água turva', 'Z', 0.32, 0.46, (0.16, 0.1, 0.04), (0.3, 0.2, 0.09), 0.0, 0.15, 1.05),
    'agua_ponte': agua_grad_mat('Água do separador', 'X', -0.17, -0.25, (0.2, 0.12, 0.05), (0.86, 0.95, 0.96), 0.0, 1.0),
    'agua_suja': agua_grad_mat('Água suja', 'Z', 0, 1, (0.17, 0.11, 0.05), (0.17, 0.11, 0.05), 0.05, 0.05),
    'jato': jato_mat(),
    'rio': rio_mat(),
    'pluma': mancha_limpa_mat(),
    'terra': terra_mat(),
    'campo': campo_mat('Membrana', VIOLETA, 14.0, 9.0),
    'emissor': emissivo('Emissor', (0.45, 0.12, 1.0), 1.2, (0.15, 0.03, 0.4)),
    'pelicula': pelicula_mat(),
    'palha': mats.material('Palha', (0.28, 0.22, 0.11), 0, 0.8, pintura=False, sujeira=0.5, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'nevoa': base3d.volume_mat('Névoa', (0.85, 0.88, 0.9), 2.5, -0.4, 0.4),
})

# ------------------------------------------------------------------ medidas
P = Vector((0.2, -0.51, 0.38))           # eixo da bomba (eixo x)
RB = 0.2                                 # raio do caracol
SEP = Vector((-0.2, -0.41, 0.82))        # centro do anel do separador (água corre em -x)
R_SEP = 0.22
COLX = (-0.2, 0.2, 0.6)                  # colunas em y = Y_COL
Y_COL, R_COL = 0.52, 0.17
Z_VID0, Z_VID1 = 0.32, 1.12              # vidro
Z_COL = 1.30                             # topo da tampa
Z_COLET = 1.40                           # coletor de água limpa
Z_DRENO, Y_DRENO = 1.18, 0.84            # dreno da lavagem reversa
X_SAIDA = 0.86                           # cano de saída (vai para o sul)
Y_MANI, Z_MANI = 0.05, 0.2               # distribuidor de entrada embaixo
Z_RIO = -0.35                            # nível da água
CACAMBA = Vector((-0.7, 0.55, 0.0))

# ------------------------------------------------------------------ laje, cais e margem
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()
caixa_de(bm, (-0.985, -0.985, 0.0), (0.985, -0.95, 0.083))               # listras no cais
obj('laje_listras', bm, 'listras')
bm = bmesh.new()
caixa_de(bm, (-1.0, -1.06, -0.9), (1.0, -0.98, 0.08))                      # muro do cais
for sx in (-1, 1):                                                         # alas de contenção
    caixa_de(bm, (sx * 1.0, -1.42, -0.9), (sx * 1.09, -0.98, 0.06))
for k in range(4):                                                         # contrafortes do muro
    x = -0.75 + k * 0.5
    if abs(x + 0.05) < 0.3:
        continue
    caixa_de(bm, (x - 0.05, -1.11, -0.9), (x + 0.05, -1.06, 0.0))
obj('cais', bm, 'concreto')
bm = bmesh.new()                                                           # faixa de alga e limo na linha d'água
caixa_de(bm, (-1.0, -1.063, Z_RIO - 0.12), (1.0, -1.061, Z_RIO + 0.09))
for sx in (-1, 1):
    caixa_de(bm, (sx * 1.0 if sx > 0 else -1.092, -1.42, Z_RIO - 0.12), (1.092 if sx > 0 else -1.0, -1.06, Z_RIO + 0.07))
for k in range(16):                                                        # escorridos de limo acima da faixa
    x = random.uniform(-0.95, 0.95)
    if -0.33 < x < 0.23:
        continue
    caixa_de(bm, (x - 0.01, -1.0625, Z_RIO + 0.05), (x + 0.01, -1.0612, Z_RIO + random.uniform(0.12, 0.3)))
obj('limo', bm, 'alga')


def altura(x, y):
    ax = abs(x)
    if y > -0.98:
        h = 0.0
        if ax > 1.15 or y > 1.15:
            h += 0.03 * math.sin(x * 1.7) * math.cos(y * 2.1) + 0.02 * math.sin(x * 4.3 + y * 3.1)
        return h
    if ax < 1.04:
        return -0.9
    t = min(1.0, (-0.98 - y) / 1.1)
    h = -0.9 * t * t * (3 - 2 * t)
    return h + 0.03 * math.sin(x * 3.1) * (1 - t)


bm = bmesh.new()
xs = [-80, -50, -30, -20, -14, -10, -8, -6, -5] + [i * 0.2 - 4.4 for i in range(45)] + [5, 6, 8, 10, 14, 20, 30, 50, 80]
vs = [[bm.verts.new((x, y, altura(x, y))) for x in xs] for y in xs]
for j in range(len(xs) - 1):
    for i in range(len(xs) - 1):
        bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
suavizar(obj('margem', bm, 'terra'))
bm = bmesh.new()                                                           # rio
caixa_de(bm, (-80, -80, Z_RIO - 0.02), (80, -1.0, Z_RIO))
obj('rio', bm, 'rio')
bm, bm2 = bmesh.new(), bmesh.new()                                         # enrocamento na margem e pedras soltas
for k in range(70):
    sx = random.choice((-1, 1))
    x = sx * random.uniform(1.12, 2.8)
    y = random.uniform(-1.85, -1.05)
    pedra(bm, (x, y, altura(x, y) + 0.03), random.uniform(0.05, 0.13), 0.55)
for k in range(30):
    x, y = random.uniform(-3, 3), random.uniform(1.2, 3.5)
    if abs(x) < 1.1 and y < 1.1:
        continue
    pedra(bm2, (x, y, altura(x, y)), random.uniform(0.02, 0.06), 0.5)
for o in (obj('enrocamento', bm, 'pedra'), obj('pedras', bm2, 'pedra')):
    o.modifiers.new('sub', 'SUBSURF').levels = 1
    for pg in o.data.polygons:
        pg.use_smooth = True
bm = bmesh.new()                                                           # juncos secos na margem
for k in range(40):
    sx = random.choice((-1, 1))
    x0 = sx * random.uniform(1.15, 2.6)
    y0 = random.uniform(-1.55, -1.15)
    base = Vector((x0, y0, max(altura(x0, y0), Z_RIO) - 0.02))
    for j in range(5):
        top = base + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), random.uniform(0.25, 0.55)))
        cil(bm, (base + top) / 2, 0.004, (top - base).length, top - base, lados=4, r2=0.001)
obj('juncos', bm, 'palha')
bm, bm2 = bmesh.new(), bmesh.new()                                         # escuma e espuma suja boiando
for k in range(26):
    c = (random.uniform(-3.5, 3.5), random.uniform(-4.5, -1.2))
    if math.hypot(c[0] - X_SAIDA, c[1] + 1.95) < 0.9:
        continue
    mancha(bm if k % 3 else bm2, c, random.uniform(0.05, 0.22), Z_RIO + 0.002)
obj('escuma', bm, 'escuma')
obj('espuma_suja', bm2, 'lama')
bm = bmesh.new()                                                           # galhos boiando
for k in range(7):
    c = Vector((random.uniform(-3, 3), random.uniform(-3.5, -1.3), Z_RIO + 0.005))
    a = random.uniform(0, PI)
    d = Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.15, 0.4)
    tubo(bm, c - d, c + d, 0.012, 6)
obj('galhos_rio', bm, 'galho')

# ------------------------------------------------------------------ tomada d'água: câmara de grade no cais (ralo sul)
TX0, TX1, TY0, TY1 = -0.3, 0.2, -1.32, -1.06
X_SUC = -0.05
bm = bmesh.new()
for x, y in ((TX0, TY0), (TX1, TY0)):                                      # pilares de canto
    caixa_de(bm, (x - 0.025, y - 0.025, -0.9), (x + 0.025, y + 0.025, 0.1))
for z in (0.06, -0.12, -0.55):                                             # cintas horizontais
    caixa_de(bm, (TX0 - 0.02, TY0 - 0.02, z - 0.015), (TX1 + 0.02, TY0 + 0.0, z + 0.015))
    for x in (TX0, TX1):
        caixa_de(bm, (x - 0.02, TY0, z - 0.015), (x + 0.02, TY1, z + 0.015))
obj('tomada_quadro', bm, 'amarelo')
bm = bmesh.new()
n = 13
for k in range(n + 1):                                                     # barras da grade (3 lados)
    x = TX0 + (TX1 - TX0) * k / n
    caixa_de(bm, (x - 0.006, TY0 - 0.006, -0.88), (x + 0.006, TY0 + 0.006, 0.07))
for k in range(1, 7):
    y = TY0 + (TY1 - TY0) * k / 7
    for x in (TX0, TX1):
        caixa_de(bm, (x - 0.006, y - 0.006, -0.88), (x + 0.006, y + 0.006, 0.07))
for k in range(12):                                                        # grade de cima, com passagem para o cano
    x = TX0 + 0.02 + (TX1 - TX0 - 0.04) * k / 11
    if abs(x - X_SUC) < 0.085:
        yc = (TY0 + TY1) / 2
        caixa_de(bm, (x - 0.005, TY0, 0.08), (x + 0.005, yc - 0.085, 0.1))
        caixa_de(bm, (x - 0.005, yc + 0.085, 0.08), (x + 0.005, TY1, 0.1))
    else:
        caixa_de(bm, (x - 0.005, TY0, 0.08), (x + 0.005, TY1, 0.1))
obj('tomada_grade', bm, 'ferro')
bm = bmesh.new()                                                           # água dentro da câmara (mais agitada)
caixa_de(bm, (TX0, TY0, Z_RIO - 0.3), (TX1, TY1, Z_RIO + 0.004))
obj('tomada_agua', bm, 'agua_suja')
bm, bm2, bm3 = bmesh.new(), bmesh.new(), bmesh.new()                       # lixo preso na grade: galhos, borra, folhas
for k in range(9):
    x = random.uniform(TX0 - 0.02, TX1 + 0.02)
    c = Vector((x, TY0 - 0.02, Z_RIO + 0.01))
    a = random.uniform(-0.4, 0.4)
    d = Vector((math.cos(a), 0, math.sin(a) * 0.4)) * random.uniform(0.08, 0.2)
    tubo(bm, c - d, c + d, random.uniform(0.006, 0.012), 6)
for k in range(14):
    x = random.uniform(TX0, TX1)
    pedra(bm2, (x, TY0 - 0.025, Z_RIO + random.uniform(-0.01, 0.04)), random.uniform(0.02, 0.045), 0.5)
for k in range(10):
    pedra(bm3, (random.uniform(TX0, TX1), TY0 - 0.02, Z_RIO + random.uniform(0.0, 0.05)), random.uniform(0.015, 0.03), 0.3)
for x in (TX0 - 0.015, TX1 + 0.015):
    for k in range(4):
        pedra(bm2, (x, random.uniform(TY0, TY1), Z_RIO + 0.02), random.uniform(0.02, 0.035), 0.5)
obj('lixo_galhos', bm, 'galho')
obj('lixo_borra', bm2, 'lama')
obj('lixo_folhas', bm3, 'alga')
bm = bmesh.new()                                                           # redemoinho da sucção
toro(bm, Vector((X_SUC, (TY0 + TY1) / 2, Z_RIO + 0.003)), 0.085, 0.006, nR=32, nr=6)
toro(bm, Vector((X_SUC, (TY0 + TY1) / 2, Z_RIO + 0.003)), 0.045, 0.005, nR=24, nr=6)
obj('redemoinho', bm, 'escuma')

# ------------------------------------------------------------------ bomba centrífuga: caracol, visor, impulsor, motor
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=36, radius1=RB, radius2=RB, depth=0.16,
                      matrix=Matrix.Translation(P) @ X.to_track_quat('Z', 'Y').to_matrix().to_4x4())
JAN = math.radians(42)                                                     # janela sul do caracol (vê o impulsor)
bmesh.ops.delete(bm, geom=[f_ for f_ in bm.faces if (f_.calc_center_median() - P).normalized().dot(-Y) > math.cos(JAN)],
                 context='FACES')
cil(bm, P + Vector((0.08, 0, 0)), RB, 0.01, X, lados=36)                   # tampa traseira
caixa_de(bm, (P.x - 0.07, P.y + 0.02, P.z), (P.x + 0.07, P.y + RB + 0.005, P.z + RB + 0.06))   # bocal de recalque
cil(bm, P + Vector((0.12, 0, 0)), 0.06, 0.08, X, lados=16)                 # mancal
caixa_de(bm, (P.x - 0.1, P.y - 0.14, 0.08), (P.x + 0.1, P.y + 0.14, P.z - RB + 0.02))   # pedestal
suavizar(obj('bomba_caracol', bm, 'amarelo'))
flange(bf, bp, P + Vector((-0.085, 0, 0)), X, RB + 0.012, 0.02, 14)        # anel do visor
cil(bf, P + Vector((0.13, 0, 0)), 0.07, 0.02, X, lados=16)
obj('bomba_anel', bf, 'ferro')
obj('bomba_parafusos', bp, 'aco')
bm = bmesh.new()
tubo_oco(bm, P + Vector((-0.08, 0, 0)), RB - 0.008, 0.066, 0.012, X, 40)    # visor de vidro em volta do olho
YJ, ZJ = P.y - RB - 0.006, RB * math.sin(JAN) + 0.012
caixa_de(bm, (P.x - 0.075, YJ - 0.004, P.z - ZJ), (P.x + 0.075, YJ + 0.004, P.z + ZJ))   # visor plano ao sul
obj('bomba_visor', bm, 'visor')
bm, bp = bmesh.new(), bmesh.new()                                          # moldura do visor sul com parafusos
for sz in (-1, 1):
    caixa_de(bm, (P.x - 0.085, YJ - 0.012, P.z + sz * ZJ - 0.018), (P.x + 0.085, P.y - RB * math.cos(JAN) + 0.02, P.z + sz * ZJ + 0.018))
for sx in (-1, 1):
    caixa_de(bm, (P.x + sx * 0.08 - 0.012, YJ - 0.012, P.z - ZJ), (P.x + sx * 0.08 + 0.012, YJ + 0.004, P.z + ZJ))
for k in range(5):
    for sz in (-1, 1):
        cil(bp, Vector((P.x - 0.06 + k * 0.03, YJ - 0.014, P.z + sz * ZJ)), 0.006, 0.008, Y, lados=6)
obj('bomba_moldura', bm, 'ferro')
obj('bomba_moldura_parafusos', bp, 'aco')
bm = bmesh.new()                                                           # fundo escuro da carcaça (atrás do impulsor)
cil(bm, P + Vector((0.07, 0, 0)), RB - 0.004, 0.006, X, lados=36)
obj('bomba_fundo', bm, 'ferro')
rotor = bpy.data.objects.new('rotor', None)
sc.collection.objects.link(rotor)
rotor.location = P
bm = bmesh.new()
cil(bm, Vector((0.0, 0, 0)), 0.045, 0.12, X, lados=16)                     # cubo
cil(bm, Vector((0.05, 0, 0)), RB - 0.025, 0.012, X, lados=36)             # disco traseiro
cil(bm, Vector((-0.07, 0, 0)), 0.025, 0.02, X, lados=8, r2=0.012)         # porca do cubo
for k in range(7):                                                         # pás curvas (dois trechos)
    a = k * 2 * PI / 7
    for r0, r1, ofs in ((0.045, 0.11, 0.0), (0.105, 0.17, 0.38)):
        p0 = Matrix.Rotation(a, 3, 'X') @ Vector((0, 0, r0))
        p1 = Matrix.Rotation(a + ofs + 0.32, 3, 'X') @ Vector((0, 0, r1))
        d = p1 - p0
        rot = Matrix((X, X.cross(d.normalized()), d.normalized())).transposed()
        caixa(bm, Vector((0.0, 0, 0)) + (p0 + p1) / 2, (0.085, 0.009, d.length + 0.006), rot)
obj('impulsor', bm, 'bronze', rotor)
luz_b = bpy.data.lights.new('Inspeção', 'POINT')                           # luz de inspeção da IA dentro do caracol
luz_b.color = (1.0, 0.6, 0.25)
luz_b.energy = 12.0
luz_b.shadow_soft_size = 0.02
lb = bpy.data.objects.new('Inspeção', luz_b)
sc.collection.objects.link(lb)
lb.location = P + Vector((-0.05, -0.1, RB - 0.06))
# motor
M0, M1 = P.x + 0.17, P.x + 0.46
bm = bmesh.new()
cil(bm, Vector(((M0 + M1) / 2, P.y, P.z)), 0.12, M1 - M0, X, lados=28)
for k in range(9):                                                         # aletas
    cil(bm, Vector((M0 + 0.025 + k * 0.03, P.y, P.z)), 0.138, 0.007, X, lados=28)
cil(bm, Vector((M1 + 0.04, P.y, P.z)), 0.125, 0.08, X, lados=28, r2=0.11)  # capa do ventilador
caixa_de(bm, (M0 + 0.02, P.y - 0.13, 0.13), (M1 - 0.02, P.y + 0.13, 0.17))  # pés
for sy in (-1, 1):
    caixa_de(bm, (M0 + 0.04, P.y + sy * 0.1 - 0.02, 0.17), (M1 - 0.04, P.y + sy * 0.1 + 0.02, P.z - 0.06))
caixa_de(bm, (M0 + 0.08, P.y - 0.07, P.z + 0.125), (M0 + 0.2, P.y + 0.07, P.z + 0.2))   # caixa de ligação
suavizar(obj('motor', bm, 'grafite'))
bm = bmesh.new()                                                           # grade do ventilador
for k in range(-5, 6):
    caixa(bm, Vector((M1 + 0.082, P.y + k * 0.018, P.z)), (0.004, 0.005, 2 * math.sqrt(max(0.105 ** 2 - (k * 0.018) ** 2, 0.0004))))
obj('motor_grade', bm, 'ferro')
bm = bmesh.new()                                                           # eixo e acoplamento com proteção de barras
cil(bm, Vector((P.x + 0.165, P.y, P.z)), 0.022, 0.07, X, lados=12)
cil(bm, Vector((P.x + 0.165, P.y, P.z)), 0.045, 0.03, X, lados=14)
obj('acoplamento', bm, 'aco')
bm = bmesh.new()
for k in range(8):
    a = k * PI / 4
    o = Vector((0, math.cos(a), math.sin(a))) * 0.07
    viga(bm, Vector((P.x + 0.135, P.y, P.z)) + o, Vector((M0 + 0.005, P.y, P.z)) + o, 0.008)
obj('acoplamento_guarda', bm, 'amarelo')
bm = bmesh.new()                                                           # base metálica (skid)
caixa_de(bm, (P.x - 0.14, P.y - 0.18, 0.08), (M1 + 0.1, P.y + 0.18, 0.13))
for x in (P.x - 0.12, M1 + 0.08):
    for sy in (-1, 1):
        cil(bm, Vector((x, P.y + sy * 0.16, 0.135)), 0.012, 0.012, lados=6)
obj('bomba_base', bm, 'ferro')

# ------------------------------------------------------------------ cano de sucção: olho da bomba → grade da tomada
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
R_SUC = 0.06
cano(bm, bf, bp, [(P.x - 0.07, P.y, P.z), (X_SUC, P.y, P.z), (X_SUC, (TY0 + TY1) / 2, P.z),
                  (X_SUC, (TY0 + TY1) / 2, Z_RIO - 0.35)], R_SUC, fl_pontas=False)
cil(bm, Vector((X_SUC, (TY0 + TY1) / 2, Z_RIO - 0.38)), 0.1, 0.08, Z, lados=24, r2=R_SUC)   # boca de sino
flange(bf, bp, Vector((X_SUC, (TY0 + TY1) / 2, 0.11)), Z, 0.095, 0.025, 10)   # colar na grade de cima
suavizar(obj('succao', bm, 'cano'))
obj('succao_flanges', bf, 'ferro')
obj('succao_parafusos', bp, 'aco')
bm = bmesh.new()                                                           # cavalete do cano de sucção
for y in (-0.8,):
    caixa_de(bm, (X_SUC - 0.07, y - 0.03, 0.08), (X_SUC + 0.07, y + 0.03, 0.1))
    for sx in (-1, 1):
        viga(bm, Vector((X_SUC + sx * 0.05, y, 0.09)), Vector((X_SUC + sx * 0.05, y, P.z - R_SUC)), 0.025)
    caixa_de(bm, (X_SUC - 0.075, y - 0.025, P.z - R_SUC - 0.025), (X_SUC + 0.075, y + 0.025, P.z - R_SUC))
obj('succao_cavalete', bm, 'amarelo')

# ------------------------------------------------------------------ recalque e separador de campo (membrana)
R_REC = 0.055
A_X, B_X = SEP.x + 0.2, SEP.x - 0.2                                        # bocas: entra suja em A, sai limpa em B
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [(P.x, SEP.y, P.z + RB + 0.06), (P.x, SEP.y, SEP.z), (A_X + 0.07, SEP.y, SEP.z)], R_REC)
cil(bm, Vector((A_X + 0.035, SEP.y, SEP.z)), 0.085, 0.07, -X, lados=24, r2=R_REC)     # boca A (sino)
cil(bm, Vector((B_X - 0.035, SEP.y, SEP.z)), 0.085, 0.07, X, lados=24, r2=R_REC)      # boca B
X_DESCE = -0.62
cano(bm, bf, bp, [(B_X - 0.07, SEP.y, SEP.z), (X_DESCE, SEP.y, SEP.z), (X_DESCE, SEP.y, Z_MANI),
                  (X_DESCE, Y_MANI, Z_MANI), (COLX[-1], Y_MANI, Z_MANI)], R_REC)
for cx in COLX:                                                            # ramais até a base de cada coluna
    cano(bm, bf, bp, [(cx, Y_MANI, Z_MANI), (cx, Y_COL - R_COL - 0.01, Z_MANI)], 0.045, fl_pontas=False)
    esfera(bm, Vector((cx, Y_MANI, Z_MANI)), R_REC + 0.004)
suavizar(obj('recalque', bm, 'cano'))
obj('recalque_flanges', bf, 'ferro')
obj('recalque_parafusos', bp, 'aco')
bm = bmesh.new()                                                           # selas do distribuidor
for x in (-0.42, 0.0, 0.4):
    caixa_de(bm, (x - 0.04, Y_MANI - 0.05, 0.08), (x + 0.04, Y_MANI + 0.05, Z_MANI - R_REC))
for y in (-0.2,):
    caixa_de(bm, (X_DESCE - 0.04, y - 0.04, 0.08), (X_DESCE + 0.04, y + 0.04, 0.1))
obj('selas', bm, 'amarelo')
bm = bmesh.new()                                                           # água suspensa entre as bocas
cil(bm, SEP, 0.05, A_X - B_X, X, lados=32)
suavizar(obj('agua_ponte', bm, 'agua_ponte'))
bm, bp = bmesh.new(), bmesh.new()                                          # anel do campo, pernas e emissores
toro(bp, SEP, R_SEP, 0.03, X, nR=56, nr=14)
bcob = bmesh.new()
for dx in (-0.045, -0.03, 0.03, 0.045):                                    # bobinas de cobre dos dois lados
    toro(bcob, SEP + Vector((dx, 0, 0)), R_SEP + 0.004, 0.009, X, nR=56, nr=8)
obj('separador_bobinas', bcob, 'cobre')
for k in range(12):                                                        # travessas entre os três anéis
    a = k * 2 * PI / 12
    d = Vector((0, math.cos(a), math.sin(a)))
    viga(bp, SEP + d * R_SEP + Vector((-0.045, 0, 0)), SEP + d * R_SEP + Vector((0.045, 0, 0)), 0.012)
PERNAS = []
for sy in (-1, 1):
    a = PI / 2 + sy * 3 * PI / 4                                           # ±135° a partir do topo
    topo = SEP + Vector((0, math.cos(a), math.sin(a))) * (R_SEP + 0.01)
    pe = Vector((SEP.x, SEP.y + (0.3 if math.cos(a) > 0 else -0.3), 0.08))
    viga(bm, topo, pe + Vector((0, 0, 0.02)), 0.045)
    caixa_de(bp, (pe.x - 0.07, pe.y - 0.07, 0.08), (pe.x + 0.07, pe.y + 0.07, 0.1))
    PERNAS.append((pe, topo))
suavizar(obj('separador_anel', bm, 'amarelo'))
obj('separador_estrutura', bp, 'ferro')
bm, be, bc = bmesh.new(), bmesh.new(), bmesh.new()
EMISSORES = []
for k in range(3):
    a = PI / 2 + k * 2 * PI / 3
    d = Vector((0, math.cos(a), math.sin(a)))
    c = SEP + d * (R_SEP - 0.035)
    rot = Matrix((X, X.cross(d), d)).transposed()
    caixa(bm, c, (0.07, 0.07, 0.06), rot)                                  # caixa do emissor
    cil(be, c - d * 0.06, 0.016, 0.06, -d, lados=6, r2=0.004)               # prisma de cristal apontando para dentro
    toro(bc, c - d * 0.035, 0.024, 0.005, d, nR=16, nr=6)
    toro(bc, c - d * 0.022, 0.026, 0.005, d, nR=16, nr=6)
    EMISSORES.append((c, d))
obj('emissores', bm, 'grafite')
obj('emissores_cristal', be, 'emissor')
obj('emissores_bobina', bc, 'cobre')
bm = bmesh.new()                                                           # membrana de campo (volume)
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
membrana = obj('membrana', bm, 'campo')
membrana.location = SEP
membrana.scale = (0.05, R_SEP - 0.03, R_SEP - 0.03)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 1.0, 0.004, X, lados=56)
pel = obj('membrana_pelicula', bm, 'pelicula')
pel.location = SEP
pel.scale = (1, R_SEP - 0.022, R_SEP - 0.022)
bm = bmesh.new()                                                           # borra grudada no lado sujo da membrana
for k in range(10):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.05, 0.13)
    pedra(bm, SEP + Vector((0.02, math.cos(a) * r, math.sin(a) * r)), random.uniform(0.008, 0.016), 0.6)
obj('borra_membrana', bm, 'lama')
luz_m = bpy.data.lights.new('Membrana', 'POINT')
luz_m.color = VIOLETA
luz_m.shadow_soft_size = 0.15
lm = bpy.data.objects.new('Membrana', luz_m)
sc.collection.objects.link(lm)
lm.location = SEP + Vector((-0.05, -0.12, R_SEP + 0.12))
GM, GF, GP = bmesh.new(), bmesh.new(), bmesh.new()                       # todos os manômetros
manometro(GM, GF, GP, Vector((P.x, SEP.y - R_REC, 0.74)), -Y, -Y)        # manômetro do recalque
manometro(GM, GF, GP, Vector((X_SUC, -0.8, P.z + R_SUC)), Z, -X)         # vacuômetro da sucção
manometro(GM, GF, GP, Vector((B_X - 0.14, SEP.y, SEP.z + R_REC)), Z, -Y)  # depois do separador

# ------------------------------------------------------------------ caminho da lama (levitação até a caçamba)
LP = [SEP + Vector((0, 0, R_SEP - 0.04)), Vector((-0.24, -0.33, 1.42)), Vector((-0.72, 0.12, 1.42)),
      Vector((CACAMBA.x, CACAMBA.y - 0.05, 0.48))]
bm2, bm3 = bmesh.new(), bmesh.new()
ANEIS_GUIA = []
for t in (0.42,):
    c = bez(*LP, t)
    d = (bez(*LP, t + 0.01) - bez(*LP, t - 0.01)).normalized()
    toro(bm2, c, 0.12, 0.016, d, nR=40, nr=10)
    for k in range(3):                                                     # nós emissores no anel guia
        u, v, _ = base_de(d)
        a = k * 2 * PI / 3 + 0.5
        cil(bm3, c + (u * math.cos(a) + v * math.sin(a)) * 0.12, 0.02, 0.04, d, lados=6)
    pe = Vector((c.x, c.y, 0.08))
    viga(bm2, pe, c - Vector((0, 0, 0.12)), 0.035)
    caixa_de(bm2, (pe.x - 0.06, pe.y - 0.06, 0.08), (pe.x + 0.06, pe.y + 0.06, 0.1))
    ANEIS_GUIA.append(c)
obj('anel_guia', bm2, 'amarelo')
obj('anel_guia_nos', bm3, 'emissor')

# ------------------------------------------------------------------ colunas de filtragem
bm_aco, bm_am, bm_vid, bm_ag = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
bm_cas, bm_are, bm_car, bm_cri, bm_par, bm_lamp, bm_tirante = (bmesh.new() for _ in range(7))
CAMADAS = ((0.46, 0.52, bm_cas), (0.52, 0.64, bm_are), (0.64, 0.76, bm_car), (0.76, 0.84, bm_cri))
Z_LIMPA = 0.84
bm_turva = bmesh.new()
for cx in COLX:
    C = Vector((cx, Y_COL, 0))
    cil(bm_am, C + Vector((0, 0, (0.08 + Z_VID0) / 2)), R_COL + 0.02, Z_VID0 - 0.08, lados=40)        # copo da base
    cil(bm_am, C + Vector((0, 0, (Z_VID1 + 1.24) / 2)), R_COL + 0.02, 1.24 - Z_VID1, lados=40)        # cinta do topo
    cil(bm_am, C + Vector((0, 0, (1.24 + Z_COL) / 2)), R_COL + 0.02, Z_COL - 1.24, lados=40, r2=0.07)  # tampa cônica
    for z in (Z_VID0 + 0.012, Z_VID1 - 0.012):                              # flanges do vidro com parafusos
        flange(bm_aco, bm_par, C + Vector((0, 0, z)), Z, R_COL + 0.035, 0.024, 16)
    for k in range(4):                                                     # tirantes com porcas
        a = k * PI / 2 + PI / 4
        q = C + Vector((math.cos(a), math.sin(a), 0)) * (R_COL + 0.022)
        cil(bm_tirante, q + Vector((0, 0, (Z_VID0 + Z_VID1) / 2)), 0.008, Z_VID1 - Z_VID0 + 0.06, lados=8)
        for z in (Z_VID0 + 0.032, Z_VID1 - 0.032):
            cil(bm_par, q + Vector((0, 0, z)), 0.014, 0.016, lados=6)
    for z in (0.12, Z_VID0 - 0.03):                                        # anéis de reforço do copo
        cil(bm_aco, C + Vector((0, 0, z)), R_COL + 0.028, 0.02, lados=40)
    tubo_oco(bm_vid, C + Vector((0, 0, (Z_VID0 + Z_VID1) / 2)), R_COL, R_COL - 0.008, Z_VID1 - Z_VID0 - 0.002, Z, 48)
    cil(bm_turva, C + Vector((0, 0, (Z_VID0 + 0.452) / 2)), R_COL - 0.009, 0.452 - Z_VID0 - 0.004, lados=48)   # entra turva
    cil(bm_ag, C + Vector((0, 0, (Z_LIMPA + Z_VID1) / 2)), R_COL - 0.009, Z_VID1 - Z_LIMPA - 0.004, lados=48)  # sai limpa
    cil(bm_aco, C + Vector((0, 0, 0.455)), R_COL - 0.007, 0.012, lados=48)  # placa de crepinas (suporte do leito)
    for z0, z1, b in CAMADAS:
        cil(b, C + Vector((0, 0, (z0 + z1) / 2)), R_COL - 0.0085, z1 - z0, lados=48)
    for k in range(9):                                                     # pontas de cristal saindo do leito
        a, r = random.uniform(0, 2 * PI), random.uniform(0.02, R_COL - 0.035)
        p0 = C + Vector((math.cos(a) * r, math.sin(a) * r, Z_LIMPA - 0.01))
        cil(bm_cri, p0 + Vector((0, 0, 0.02)), 0.012, random.uniform(0.04, 0.07),
            Vector((random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 1)), lados=6, r2=0.002)
    caixa(bm_aco, C + Vector((0, -R_COL - 0.035, 1.18)), (0.07, 0.03, 0.06))  # sensor de turbidez (olho da IA)
    cil(bm_lamp, C + Vector((0, -R_COL - 0.052, 1.18)), 0.014, 0.008, -Y, lados=12)
    cil(bm_am, C + Vector((0, 0, Z_COL + 0.01)), 0.07, 0.03, lados=20)     # pescoço até o coletor
suavizar(obj('colunas_casco', bm_am, 'amarelo'))
suavizar(obj('colunas_aneis', bm_aco, 'ferro'))
obj('colunas_parafusos', bm_par, 'aco')
suavizar(obj('colunas_tirantes', bm_tirante, 'cromo'))
suavizar(obj('colunas_vidro', bm_vid, 'vidro'))
suavizar(obj('colunas_agua', bm_ag, 'agua_coluna'))
suavizar(obj('colunas_turva', bm_turva, 'agua_turva'))
suavizar(obj('leito_cascalho', bm_cas, 'cascalho'))
suavizar(obj('leito_areia', bm_are, 'areia'))
suavizar(obj('leito_carvao', bm_car, 'carvao'))
obj('leito_cristal', bm_cri, 'cristal')
obj('sensores_luz', bm_lamp, 'lampada')
luzes_col = []

# ------------------------------------------------------------------ coletor de água limpa, válvula (pistao0) e saída
R_COL_C = 0.055
Y_V0 = 0.0                                                                 # válvula no trecho que vai para o sul
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [(COLX[0] - 0.08, Y_COL, Z_COLET), (X_SAIDA, Y_COL, Z_COLET), (X_SAIDA, -1.08, Z_COLET),
                  (X_SAIDA, -1.2, Z_COLET - 0.08)], R_COL_C, fl_pontas=False)
cil(bm, Vector((COLX[0] - 0.085, Y_COL, Z_COLET)), R_COL_C + 0.012, 0.025, X, lados=24)   # tampa cega
cil(bm, Vector((X_SAIDA, -1.235, Z_COLET - 0.105)), 0.075, 0.07,
    Vector((0, -1.2, -0.08)) - Vector((0, -1.08, 0)), lados=24, r2=R_COL_C)                # bocal de saída
for cx in COLX:
    tubo(bm, Vector((cx, Y_COL, Z_COL)), Vector((cx, Y_COL, Z_COLET)), 0.04, 20)
    esfera(bm, Vector((cx, Y_COL, Z_COLET)), R_COL_C + 0.004)
    flange(bf, bp, Vector((cx, Y_COL, Z_COL + 0.035)), Z, 0.065, 0.02, 8)
suavizar(obj('coletor', bm, 'cano'))
obj('coletor_flanges', bf, 'ferro')
obj('coletor_parafusos', bp, 'aco')
bm = bmesh.new()                                                           # postes do cano de saída
for y in (0.35, -0.45, -0.92):
    pe = Vector((X_SAIDA, y, 0.08))
    viga(bm, pe, Vector((X_SAIDA, y, Z_COLET - R_COL_C - 0.02)), 0.05)
    caixa_de(bm, (X_SAIDA - 0.08, y - 0.03, Z_COLET - R_COL_C - 0.03), (X_SAIDA + 0.08, y + 0.03, Z_COLET - R_COL_C - 0.008))
    caixa_de(bm, (X_SAIDA - 0.07, y - 0.07, 0.08), (X_SAIDA + 0.07, y + 0.07, 0.1))
    toro(bm, Vector((X_SAIDA, y, Z_COLET)), R_COL_C + 0.006, 0.006, Y, nR=24, nr=6)        # abraçadeira
obj('postes_saida', bm, 'amarelo')
manometro(GM, GF, GP, Vector((0.4, Y_COL, Z_COLET + R_COL_C)), Z, -Y)


def valvula(bm, bf, bp, c, eixo, r):
    """Válvula borboleta: corpo entre dois flanges e haste vertical com mancal; devolve o topo da haste."""
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(bm, c, r + 0.03, 0.06, eixo, lados=24)
    flange(bf, bp, c + eixo * 0.04, eixo, r + 0.035, 0.02, 8)
    flange(bf, bp, c - eixo * 0.04, eixo, r + 0.035, 0.02, 8)
    cil(bm, c + Vector((0, 0, r + 0.05)), 0.022, 0.06, lados=12)
    cil(bm, c + Vector((0, 0, r + 0.085)), 0.04, 0.012, lados=12)
    return c + Vector((0, 0, r + 0.11))


bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
HASTE0 = valvula(bm, bf, bp, (X_SAIDA, Y_V0, Z_COLET), Y, R_COL_C)
obj('valvula0', bm, 'grafite')
obj('valvula0_flanges', bf, 'ferro')
obj('valvula0_parafusos', bp, 'aco')

# ------------------------------------------------------------------ dreno da lavagem reversa, válvula (pistao1), caçamba
R_DR = 0.045
X_V1 = -0.42
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [(COLX[-1] + 0.07, Y_DRENO, Z_DRENO), (CACAMBA.x, Y_DRENO, Z_DRENO), (CACAMBA.x, Y_DRENO, 0.84)],
     R_DR, fl_pontas=False)
cil(bm, Vector((COLX[-1] + 0.075, Y_DRENO, Z_DRENO)), R_DR + 0.012, 0.02, X, lados=24)
cil(bm, Vector((CACAMBA.x, Y_DRENO, 0.81)), 0.065, 0.06, Z, lados=24, r2=R_DR)              # bocal de descarga
for cx in COLX:
    cano(bm, bf, bp, [(cx, Y_COL + R_COL + 0.015, Z_DRENO), (cx, Y_DRENO, Z_DRENO)], 0.035, fl=False)
    esfera(bm, Vector((cx, Y_DRENO, Z_DRENO)), R_DR + 0.004)
    flange(bf, bp, Vector((cx, Y_COL + R_COL + 0.03, Z_DRENO)), Y, 0.055, 0.018, 6)
suavizar(obj('dreno', bm, 'cano'))
obj('dreno_flanges', bf, 'ferro')
obj('dreno_parafusos', bp, 'aco')
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
HASTE1 = valvula(bm, bf, bp, (X_V1, Y_DRENO, Z_DRENO), X, R_DR)
obj('valvula1', bm, 'grafite')
obj('valvula1_flanges', bf, 'ferro')
obj('valvula1_parafusos', bp, 'aco')
manometro(GM, GF, GP, Vector((0.0, Y_DRENO, Z_DRENO + R_DR)), Z, -Y)
manometro(GM, GF, GP, Vector((0.4, Y_MANI - R_REC, Z_MANI)), -Y, -Y)
bm = bmesh.new()
# caçamba de lodo: tronco de pirâmide aberto, com espessura (solidificar)
b0 = [(-0.9, 0.2), (-0.5, 0.2), (-0.5, 0.9), (-0.9, 0.9)]
t0 = [(-0.95, 0.15), (-0.45, 0.15), (-0.45, 0.95), (-0.95, 0.95)]
Z_CB0, Z_CB1 = 0.12, 0.52
vb = [bm.verts.new((x, y, Z_CB0)) for x, y in b0]
vt = [bm.verts.new((x, y, Z_CB1)) for x, y in t0]
bm.faces.new(vb[::-1])
for i in range(4):
    j = (i + 1) % 4
    bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
cb = obj('cacamba', bm, 'amarelo')
sol_m = cb.modifiers.new('esp', 'SOLIDIFY')
sol_m.thickness = 0.02
sol_m.offset = 1
bm = bmesh.new()
for i in range(4):                                                         # aro de cima
    j = (i + 1) % 4
    a = Vector((*t0[i], Z_CB1))
    b = Vector((*t0[j], Z_CB1))
    viga(bm, a, b, 0.03)
for x in (-0.82, -0.7, -0.58):                                             # nervuras nas paredes leste/oeste e norte/sul
    for (yb, yt) in ((0.2, 0.15), (0.9, 0.95)):
        viga(bm, Vector((x, yb - (0.012 if yb < 0.5 else -0.012), Z_CB0 + 0.02)), Vector((x - (x + 0.7) * 0.12, yt - (0.012 if yt < 0.5 else -0.012), Z_CB1 - 0.02)), 0.022)
for sy in (0.3, 0.8):
    for xb, xt in ((-0.9, -0.95), (-0.5, -0.45)):
        viga(bm, Vector((xb + (-0.012 if xb < -0.7 else 0.012), sy, Z_CB0 + 0.02)), Vector((xt + (-0.012 if xt < -0.7 else 0.012), sy, Z_CB1 - 0.02)), 0.022)
for x in (-0.86, -0.54):                                                   # sapatas
    caixa_de(bm, (x - 0.03, 0.22, 0.08), (x + 0.03, 0.88, Z_CB0))
for xs_, ys_ in ((-0.95, 0.35), (-0.95, 0.75), (-0.45, 0.35), (-0.45, 0.75)):   # olhais de içamento
    toro(bm, Vector((xs_ + (-0.03 if xs_ < -0.7 else 0.03), ys_, Z_CB1 - 0.04)), 0.03, 0.008, Y, nR=16, nr=6)
obj('cacamba_reforcos', bm, 'ferro')
bm, bm2 = bmesh.new(), bmesh.new()                                         # lodo dentro, com caroços, e escorridos por fora
caixa_de(bm, (-0.925, 0.175, Z_CB1 - 0.08), (-0.475, 0.925, Z_CB1 - 0.06))
for k in range(30):
    pedra(bm, (random.uniform(-0.9, -0.5), random.uniform(0.2, 0.9), Z_CB1 - 0.06), random.uniform(0.015, 0.04), 0.45)
for k in range(9):
    x = random.uniform(-0.92, -0.48)
    L = random.uniform(0.08, 0.3)
    caixa_de(bm2, (x - 0.008, 0.143 + 0.05 * (L / 0.42), Z_CB1 - L), (x + 0.008, 0.149, Z_CB1 + 0.005))
for k in range(5):
    y = random.uniform(0.2, 0.9)
    L = random.uniform(0.08, 0.25)
    caixa_de(bm2, (-0.457, y - 0.008, Z_CB1 - L), (-0.451 + 0.05 * (L / 0.42) * 0, y + 0.008, Z_CB1 + 0.005))
for k in range(12):                                                        # respingos e poças de lama em volta
    mancha(bm2, (random.uniform(-0.97, -0.35), random.uniform(0.0, 0.97)), random.uniform(0.03, 0.09), 0.0815)
obj('lodo', bm, 'lodo')
obj('lodo_escorrido', bm2, 'lama')
bm, bm3 = bmesh.new(), bmesh.new()                                         # anel coletor de campo sobre a caçamba
C_ANEL = Vector((LP[3].x, LP[3].y, 0.66))
toro(bm, C_ANEL, 0.15, 0.014, Z, nR=40, nr=8)
for k in range(3):
    a = k * 2 * PI / 3 + 0.4
    q = C_ANEL + Vector((math.cos(a), math.sin(a), 0)) * 0.15
    cil(bm3, q, 0.018, 0.035, lados=6)
    alvo = Vector((-0.7 + math.cos(a) * 0.24, 0.55 + math.sin(a) * 0.38, Z_CB1))
    alvo.x = min(max(alvo.x, -0.95), -0.45)
    alvo.y = min(max(alvo.y, 0.15), 0.95)
    viga(bm, q - Vector((0, 0, 0.015)), alvo, 0.014)
obj('anel_cacamba', bm, 'ferro')
obj('anel_cacamba_nos', bm3, 'emissor')

# ------------------------------------------------------------------ atuadores: alavancas e pistões
def alavanca(nome, haste, vbase):
    """Alavanca da válvula: gira em z na ponta da haste; vbase é o braço (posição fechada)."""
    pv = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(pv)
    pv.location = haste
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.028, 0.03, lados=12)
    viga(bm, Vector((0, 0, 0)), vbase, 0.022)
    for s in (-1, 1):                                                      # garfo na ponta
        caixa(bm, vbase + Vector((0, 0, s * 0.016)), (0.04, 0.04, 0.006))
    cil(bm, vbase, 0.006, 0.05, lados=8)
    obj(nome + '_braco', bm, 'amarelo', pv)
    return pv


def pistao(nome, ancora):
    """Pistão hidráulico: camisa presa na âncora (olhal), haste presa na alavanca; os dois miram um no outro."""
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    camisa = bpy.data.objects.new(nome + '_camisa', None)
    haste = bpy.data.objects.new(nome + '_haste', None)
    for o in (camisa, haste):
        sc.collection.objects.link(o)
        o.parent = raiz
        o.rotation_mode = 'QUATERNION'
    bm, bm2 = bmesh.new(), bmesh.new()
    cil(bm, Vector((0, 0, 0.1)), 0.026, 0.15, lados=20)
    for z in (0.03, 0.172):
        cil(bm2, Vector((0, 0, z)), 0.031, 0.016, lados=20)
    cil(bm2, Vector((0, 0, 0.0)), 0.014, 0.05, Y, lados=10)                # olhal (pino em y local ≈ vertical)
    caixa(bm2, Vector((0, 0, 0.012)), (0.03, 0.04, 0.024))
    caixa(bm2, Vector((0.03, 0, 0.05)), (0.02, 0.02, 0.02))                # porta da mangueira
    suavizar(obj(nome + '_corpo', bm, 'amarelo', camisa))
    obj(nome + '_tampas', bm2, 'ferro', camisa)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.11)), 0.011, 0.2, lados=14)
    cil(bm, Vector((0, 0, 0.0)), 0.014, 0.03, Y, lados=10)
    caixa(bm, Vector((0, 0, 0.012)), (0.026, 0.024, 0.024))
    suavizar(obj(nome + '_cromo', bm, 'cromo', haste))
    return camisa, haste


# pistao0: alavanca da válvula do cano de saída; braço fechado aponta para -x, gira para +y
BR0 = Vector((-0.12, 0, 0))
ANC0 = Vector((X_SAIDA - 0.12, Y_V0 + 0.3, HASTE0.z))
alav0 = alavanca('alavanca0', HASTE0, BR0)
cam0, has0 = pistao('pistao0', ANC0)
# pistao1: alavanca da válvula do dreno; braço fechado aponta para +y, gira para +x
BR1 = Vector((0, 0.12, 0))
ANC1 = Vector((X_V1 + 0.3, Y_DRENO + 0.12, HASTE1.z))
alav1 = alavanca('alavanca1', HASTE1, BR1)
cam1, has1 = pistao('pistao1', ANC1)
bm, bp = bmesh.new(), bmesh.new()                                          # suportes das âncoras (abraçadeira no cano + braço)
for anc, cpos, eixo in ((ANC0, Vector((X_SAIDA, ANC0.y, Z_COLET)), Y), (ANC1, Vector((ANC1.x, Y_DRENO, Z_DRENO)), X)):
    toro(bm, cpos, (R_COL_C if eixo == Y else R_DR) + 0.008, 0.008, eixo, nR=24, nr=6)
    topo = cpos + Vector((0, 0, (R_COL_C if eixo == Y else R_DR) + 0.01))
    viga(bm, topo, anc - Vector((0, 0, 0.03)), 0.024)
    caixa(bm, anc - Vector((0, 0, 0.03)), (0.05, 0.05, 0.012))
    cil(bp, anc, 0.007, 0.07, lados=8)                                     # pino
    caixa(bm, anc + Vector((0, 0, 0.03)), (0.05, 0.05, 0.012))
obj('ancoras', bm, 'ferro')
obj('pinos', bp, 'cromo')

# unidade hidráulica (tanque + bomba) e mangueiras até os pistões
HU0, HU1 = Vector((0.81, 0.48, 0.08)), Vector((0.96, 0.92, 0.36))
bm = bmesh.new()
caixa_de(bm, HU0, HU1)
cil(bm, Vector((0.885, 0.62, 0.43)), 0.055, 0.12, Y, lados=16)           # motor da bomba hidráulica
for k in range(4):
    cil(bm, Vector((0.885, 0.57 + k * 0.03, 0.43)), 0.064, 0.006, Y, lados=16)
caixa_de(bm, (0.84, 0.8, 0.36), (0.93, 0.88, 0.42))                        # bloco de válvulas
obj('hidraulica', bm, 'grafite')
bm = bmesh.new()
cil(bm, Vector((0.885, 0.52, 0.375)), 0.02, 0.03, lados=10)              # bocal de enchimento
caixa_de(bm, (0.958, 0.55, 0.15), (0.966, 0.6, 0.32))                      # visor de nível
obj('hidraulica_det', bm, 'cromo')
bm = bmesh.new()
pts = bezier((0.9, 0.86, 0.42), (0.95, 0.86, 1.0), (0.95, 0.3, 1.75), ANC0 + Vector((0.03, 0.0, 0.05)), 18)
mangueira(bm, pts, 0.011)
pts = bezier((0.87, 0.84, 0.42), (0.9, 0.95, 0.9), (0.9, 0.95, 1.3), (0.6, 0.95, 1.31), 12)
pts += bezier((0.6, 0.95, 1.31), (0.3, 0.95, 1.32), (0.0, 0.95, 1.32), ANC1 + Vector((0.03, 0.0, 0.05)), 12)[1:]
mangueira(bm, pts, 0.011)
pts = bezier((0.86, 0.84, 0.42), (0.86, 0.95, 0.85), (0.89, 0.95, 1.25), (0.62, 0.955, 1.29), 10)
pts += bezier((0.62, 0.955, 1.29), (0.3, 0.958, 1.3), (0.0, 0.958, 1.3), ANC1 + Vector((0.04, 0.02, 0.03)), 10)[1:]
mangueira(bm, pts, 0.009)
obj('mangueiras', bm, 'borracha')
bm = bmesh.new()                                                           # presilhas da mangueira no dreno
for x in (0.35, 0.05):
    viga(bm, Vector((x, Y_DRENO, Z_DRENO + R_DR)), Vector((x, 0.955, 1.3)), 0.014)
obj('presilhas', bm, 'ferro')

# ------------------------------------------------------------------ armário de controle, eletrocalha e cabos
bm = bmesh.new()
caixa_de(bm, (0.72, -0.25, 0.08), (0.96, 0.2, 0.74))
for k in range(8):                                                         # aletas de calor no topo
    caixa_de(bm, (0.74, -0.22 + k * 0.055, 0.74), (0.94, -0.21 + k * 0.055, 0.8))
obj('armario', bm, 'grafite')
bm, bl = bmesh.new(), bmesh.new()
for k in range(3):                                                         # luzes de estado (para a IA ver de longe)
    cil(bl, Vector((0.7175, -0.15 + k * 0.08, 0.64)), 0.014, 0.008, X, lados=12)
caixa_de(bm, (0.713, -0.2, 0.3), (0.72, 0.15, 0.5))                       # grelha de ventilação
obj('armario_grelha', bm, 'ferro')
obj('armario_luzes', bl, 'lampada')
bm, bc = bmesh.new(), bmesh.new()                                          # eletrocalha (U) ao longo de y = -0.24
Y_EC = -0.24
X_EC0, X_EC1 = ANEIS_GUIA[0].x - 0.05, 0.72
caixa_de(bm, (X_EC0, Y_EC - 0.04, 0.08), (X_EC1, Y_EC + 0.04, 0.09))
for s in (-1, 1):
    caixa_de(bm, (X_EC0, Y_EC + s * 0.04 - 0.003, 0.08), (X_EC1, Y_EC + s * 0.04 + 0.003, 0.13))
for x in (X_EC0 + 0.1, -0.1, 0.25, 0.55):
    caixa_de(bm, (x - 0.01, Y_EC - 0.045, 0.125), (x + 0.01, Y_EC + 0.045, 0.135))   # abraçadeiras da calha
obj('eletrocalha', bm, 'aco')
for k in range(3):
    dy = (k - 1) * 0.018
    tubo(bc, Vector((X_EC0 + 0.02, Y_EC + dy, 0.105)), Vector((X_EC1, Y_EC + dy, 0.105)), 0.009, 8)
pe_sep = PERNAS[1][0] if PERNAS[1][0].y > PERNAS[0][0].y else PERNAS[0][0]
topo_sep = PERNAS[1][1] if PERNAS[1][0].y > PERNAS[0][0].y else PERNAS[0][1]
for k in range(2):                                                         # cabos: calha → perna do separador → emissor
    dx = 0.035 + k * 0.016
    pts = bezier((pe_sep.x + dx, Y_EC + 0.02, 0.105), (pe_sep.x + dx, pe_sep.y, 0.1),
                 (pe_sep.x + dx, pe_sep.y, 0.3), (topo_sep.x + dx, topo_sep.y, topo_sep.z - 0.05), 10)
    mangueira(bc, pts, 0.008)
for k in range(2):                                                         # cabos: calha → poste do anel guia
    c = ANEIS_GUIA[0]
    pts = bezier((X_EC0 + 0.03, Y_EC + (k - 0.5) * 0.02, 0.105), (c.x + 0.03, Y_EC, 0.12), (c.x + 0.03, c.y, 0.3),
                 (c.x + 0.03, c.y + (k - 0.5) * 0.02, c.z - 0.2), 10)
    mangueira(bc, pts, 0.008)
pts = bezier((0.72, -0.1, 0.3), (0.6, -0.1, 0.35), (M0 + 0.14, P.y + 0.2, P.z + 0.28), (M0 + 0.14, P.y + 0.07, P.z + 0.17), 12)
mangueira(bc, pts, 0.016)                                                  # conduíte do motor
pts = bezier((0.84, 0.2, 0.3), (0.85, 0.35, 0.3), (0.86, 0.45, 0.3), (0.86, 0.48, 0.25), 6)
mangueira(bc, pts, 0.01)                                                   # cabo da unidade hidráulica
obj('cabos', bc, 'borracha')
bm = bmesh.new()                                                           # abraçadeiras dos cabos na perna e no poste
for t in (0.3, 0.6):
    q = pe_sep.lerp(topo_sep, t)
    caixa(bm, q + Vector((0.045, 0, 0)), (0.03, 0.06, 0.012))
obj('abracadeiras', bm, 'aco')
manometro(GM, GF, GP, Vector((X_SAIDA, -0.6, Z_COLET + R_COL_C)), Z, X)
obj('manometros', GM, 'cromo')
obj('manometros_face', GF, 'mostrador')
obj('manometros_ponteiro', GP, 'ponteiro')

# ------------------------------------------------------------------ sujeira: óleo, lama, poças, ferrugem escorrida
bm = bmesh.new()
for c, r in (((M0 + 0.1, P.y - 0.05), 0.12), ((M0 + 0.3, P.y + 0.1), 0.07), ((0.88, 0.6), 0.09), ((0.7, 0.3), 0.05)):
    mancha(bm, c, r, 0.0825)
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for k in range(14):                                                        # lama arrastada da tomada e respingos
    mancha(bm, (random.uniform(-0.35, 0.3), random.uniform(-0.97, -0.7)), random.uniform(0.03, 0.08), 0.0815)
for k in range(6):
    mancha(bm, (random.uniform(-0.45, 0.0), random.uniform(-0.75, 0.2)), random.uniform(0.02, 0.05), 0.0815)
obj('lama_chao', bm, 'lama_seca')
bm = bmesh.new()
for k in range(5):                                                         # poças d'água limpa sob o coletor
    mancha(bm, (random.uniform(0.75, 0.95), random.uniform(-0.95, 0.4)), random.uniform(0.04, 0.09), 0.082)
obj('pocas', bm, 'oleo')

# ------------------------------------------------------------------ partes animadas: lama flutuando, bolhas, jato, borra
blobs = []
for k in range(8):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        v.co *= 1 + 0.16 * math.sin(v.co.x * 3 + k) * math.cos(v.co.y * 2.5 - k) + 0.08 * math.sin(v.co.z * 5 + k * 2)
    o = obj('lama_flutuando', bm, 'lama')
    suavizar(o)
    for pg in o.data.polygons:
        pg.use_smooth = True
    blobs.append(o)
bolhas = []
for cx in COLX:
    for k in range(6):
        bmb = bmesh.new()
        bmesh.ops.create_icosphere(bmb, subdivisions=1, radius=random.uniform(0.005, 0.009))
        o = obj('bolha', bmb, 'vidro')
        bolhas.append((o, Vector((cx + random.uniform(-0.1, 0.1), Y_COL + random.uniform(-0.1, 0.1), 0)), random.random()))
# jato de água limpa saindo do bocal e caindo no rio
N_BOC = Vector((X_SAIDA, -1.27, Z_COLET - 0.13))
V0 = Vector((0, -1.15, -0.75))


def no_jato(t):
    return N_BOC + V0 * t + Vector((0, 0, -4.9 * t * t))


T_CAI = (V0.z + math.sqrt(V0.z ** 2 + 19.6 * (N_BOC.z - Z_RIO))) / 9.8   # z(t) = nível do rio
IMPACTO = no_jato(T_CAI)
bm = bmesh.new()
NJ, LJ = 40, 20
aneis_j = []
for i in range(NJ + 1):                                                    # tubo varrido ao longo da parábola
    t = T_CAI * i / NJ
    c = no_jato(t)
    tg = (no_jato(t + 0.001) - c).normalized()
    v = tg.cross(X).normalized()
    r = 0.034 + 0.03 * (i / NJ) ** 1.5
    aneis_j.append([bm.verts.new(c + (X * math.cos(a) + v * math.sin(a)) * r * (1 + 0.08 * math.sin(a * 3 + i)))
                    for a in (j * 2 * PI / LJ for j in range(LJ))])
for i in range(NJ):
    A, B = aneis_j[i], aneis_j[i + 1]
    for j in range(LJ):
        bm.faces.new((A[j], A[(j + 1) % LJ], B[(j + 1) % LJ], B[j]))
bm.faces.new(aneis_j[0][::-1])
o = obj('jato', bm, 'jato')
for pg in o.data.polygons:
    pg.use_smooth = True
bm = bmesh.new()                                                           # pluma de água limpa no rio
bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.0)
pluma = obj('pluma', bm, 'pluma')
pluma.location = (IMPACTO.x - 0.1, IMPACTO.y - 0.35, Z_RIO + 0.003)
pluma.scale = (0.85, 1.1, 1)
bm = bmesh.new()                                                           # espuma branca no impacto
for k in range(14):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.02, 0.16)
    mancha(bm, (IMPACTO.x + math.cos(a) * r, IMPACTO.y + math.sin(a) * r), random.uniform(0.03, 0.08), Z_RIO + 0.006)
obj('espuma', bm, 'espuma')
aneis_onda = []
for k in range(3):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 1.0, 0.007, Z, nR=48, nr=6)
    o = obj('onda', bm, 'escuma')
    aneis_onda.append(o)
nevoas = []
for k in range(3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    nevoas.append(obj('nevoa', bm, 'nevoa'))
gotas = []
for k in range(12):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.012)
    gotas.append(obj('gota', bm, 'jato'))
vel_g = [Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(0.8, 1.6))) for _ in gotas]
# borra marrom saindo do dreno na caçamba (lavagem reversa)
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.5)), 0.03, 1.0, lados=14, r2=0.04)
borra = obj('borra_jato', bm, 'lama')
borra.location = (CACAMBA.x, Y_DRENO, 0.78)
Z_LODO = Z_CB1 - 0.06
bm = bmesh.new()
for k in range(8):
    a = k * 2 * PI / 8
    pedra(bm, (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.0), 0.025, 0.4)
respingo = obj('respingo_lodo', bm, 'lama')
respingo.location = (CACAMBA.x, Y_DRENO, Z_LODO + 0.01)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lavagem(fr):
    """Abertura do dreno: fecha (0–0,2), abre (0,2–0,3), aberto (0,3–0,7), fecha (0,7–0,8)."""
    if fr < 0.2:
        return 0.0
    if fr < 0.3:
        return suave((fr - 0.2) / 0.1)
    if fr < 0.7:
        return 1.0
    if fr < 0.8:
        return 1.0 - suave((fr - 0.7) / 0.1)
    return 0.0


cristal_em = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
campo_no = base3d.M['campo'].node_tree.nodes['forca'].inputs[1]
FR_FOTO = int(QUADROS * 0.5) + 1
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    lv = lavagem(fr)
    # impulsor: 16 voltas no laço
    rotor.rotation_euler = (-2 * PI * 16 * fr, 0, 0)
    rotor.keyframe_insert('rotation_euler', frame=q)
    # válvulas: na lavagem o dreno abre (pistao1) e a saída estrangula (pistao0)
    for alav, br, anc, cam, has, ang in ((alav0, BR0, ANC0, cam0, has0, PI / 2 * (1 - 0.6 * lv)),
                                         (alav1, BR1, ANC1, cam1, has1, PI / 2 * lv)):
        alav.rotation_euler = (0, 0, -ang if br.y > 0 else -ang)
        alav.keyframe_insert('rotation_euler', frame=q)
        ponta = alav.location + Matrix.Rotation(-ang, 3, 'Z') @ br
        d = ponta - anc
        cam.location = anc
        cam.rotation_quaternion = d.to_track_quat('Z', 'Y')
        has.location = ponta
        has.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
        for o in (cam, has):
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
    # borra no dreno
    borra.scale = (1, 1, max(0.001, (0.78 - Z_LODO) * lv))
    borra.location = (CACAMBA.x, Y_DRENO, 0.78 - 0.0)
    borra.hide_render = lv < 0.05
    respingo.scale = [max(0.001, lv * (0.8 + 0.3 * math.sin(fr * 60)))] * 3
    for o, cs in ((borra, ('scale', 'location', 'hide_render')), (respingo, ('scale',))):
        for c in cs:
            o.keyframe_insert(c, frame=q)
    # lama flutuando do separador até a caçamba
    for k, o in enumerate(blobs):
        u = (k / len(blobs) + fr) % 1.0
        pos = bez(*LP, u)
        tam = 0.032 * suave(u / 0.12) * (1 - suave((u - 0.9) / 0.1)) + 0.0005
        o.location = pos
        o.rotation_euler = (u * 7 + k, u * 5, k)
        o.scale = (tam * (1 + 0.15 * math.sin(fr * 40 + k)), tam * (1 + 0.15 * math.cos(fr * 34 + k)), tam)
        for c in ('location', 'rotation_euler', 'scale'):
            o.keyframe_insert(c, frame=q)
    # bolhas subindo na água limpa
    for o, base, ph in bolhas:
        u = (ph + fr * 2) % 1.0
        o.location = base + Vector((0.01 * math.sin(u * 20 + ph * 9), 0, 0.87 + 0.22 * u))
        o.keyframe_insert('location', frame=q)
    # brilho: cristal do leito e membrana pulsam (mais forte na lavagem do leito)
    pulso = 0.8 + 0.2 * math.sin(2 * PI * 4 * fr)
    cristal_em.default_value = 0.7 * pulso + 0.6 * lv
    cristal_em.keyframe_insert('default_value', frame=q)
    campo_no.default_value = 9.0 * (0.85 + 0.15 * math.sin(2 * PI * 6 * fr))
    campo_no.keyframe_insert('default_value', frame=q)
    luz_m.energy = 5 * (0.85 + 0.15 * math.sin(2 * PI * 6 * fr))
    luz_m.keyframe_insert('energy', frame=q)
    fase = base3d.M['pelicula'].node_tree.nodes['fase'].inputs[1]
    fase.default_value = 38.0 + 6.0 * fr
    fase.keyframe_insert('default_value', frame=q)
    for lc in luzes_col:
        lc.energy = 3.0 * pulso + 3 * lv
        lc.keyframe_insert('energy', frame=q)
    # ondas no impacto do jato
    for k, o in enumerate(aneis_onda):
        u = (k / len(aneis_onda) + fr * 2) % 1.0
        o.location = (IMPACTO.x, IMPACTO.y, Z_RIO + 0.004)
        o.scale = (0.08 + 0.45 * u, 0.08 + 0.45 * u, 0.25 * (1 - u) + 0.02)
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    for k, o in enumerate(nevoas):
        u = (k / len(nevoas) + fr * 2) % 1.0
        o.location = IMPACTO + Vector((0.05 * math.sin(k * 2.0), 0.05 * k - 0.05, 0.03 + 0.3 * u))
        o.scale = [0.06 + 0.16 * u] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    for k, o in enumerate(gotas):
        tt = ((k / len(gotas) + fr * 3) % 1.0) * 0.4
        o.location = IMPACTO + vel_g[k] * tt + Vector((0, 0, -4.9 * tt * tt + 0.01))
        o.scale = [max(0.001, 1 - tt / 0.4)] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: luz, céu, câmera
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
sc.cycles.max_bounces = 16
sc.cycles.transmission_bounces = 16
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


ALVO = (0.0, -0.3, 0.6)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
    sc.frame_set(FR_FOTO)
    for i, (ang, alt) in enumerate(((245, 2.1), (320, 2.3), (45, 2.6), (140, 2.4))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 5.0, math.sin(a) * 5.0, alt)), ALVO, 34)
        sc.render.filepath = os.path.join(AQUI, 'filtro_agua_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((-1.45, -1.75, 1.35), (-0.02, -0.45, 0.62), 33)               # tomada, bomba, separador de campo
        sc.render.filepath = os.path.join(AQUI, 'filtro_agua_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto2'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((0.55, -1.15, 1.25), (-0.05, 0.5, 0.82), 30)                  # colunas, camadas, caçamba
        sc.render.filepath = os.path.join(AQUI, 'filtro_agua_perto2.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'filtro_agua_teste.png')
    bpy.ops.render.render(write_still=True)
print('FILTRO_AGUA ok')
