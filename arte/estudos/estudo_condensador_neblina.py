"""Estudo isolado (fora do jogo): condensador de neblina da IA, 2×2 tiles (até 12 de água/s com neblina, 80 kW).
Captação: parede de duas telas de malha fina (coletores de névoa) esticadas em quadros de aço com esticadores; a água
condensa em gotas na malha, escorre até a calha inclinada embaixo e cai na caixa coletora da ponta oeste. Atrás das
telas, um plenum de chapa com a serpentina fria (cobre com gelo e sincelos), bandeja de gotejamento e dois ventiladores
grandes que puxam o ar úmido através das telas e da serpentina e sopram o ar seco para o norte.
Resfriamento: compressor hermético sobre coxins, linha de sucção isolada e congelada, linha quente até o radiador
aletado da borda leste (com ventoinha), filtro secador e válvula de expansão.
Armazenamento: tanque com visor de nível e escotilha de vidro, bomba centrífuga, válvula atuada e cano de saída com
flange na borda sul (tile oeste: FLUIDO_SAI_S0, centro em z = 0,28).
Toque da IA: um anel de campo com cristais violeta na frente das telas puxa a névoa do ar em espiral (três braços de
névoa em volume com linhas de campo) até a malha. Névoa de chão em volume em volta de tudo.
Desgaste: limo verde nas telas, na calha e nos pés; ferrugem escorrida, remendos aparafusados, chapa trocada em
primer vermelho, poças, gotejamento constante (calha furada, sincelos, bandeja, flange da bomba).
Uso: blender -b --python estudo_condensador_neblina.py -- foto [0|perto]  |  -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

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
print('INICIO', flush=True)
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


def toro(bm, centro, R, r, eixo=Z, nR=48, nr=12, a0=0.0, a1=2 * PI):
    """Anel tubular em volta do eixo (ou só um arco, de a0 a a1)."""
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


_GOTA = {}


def gota(bm, c, r, seg=8, esc=(1, 1, 1)):
    """Esfera rápida (molde pronto): milhares de gotas sem o custo de create_uvsphere num bmesh que cresce."""
    if seg not in _GOTA:
        t = bmesh.new()
        bmesh.ops.create_uvsphere(t, u_segments=seg, v_segments=max(6, seg // 2), radius=1.0)
        t.verts.index_update()
        _GOTA[seg] = ([v.co.copy() for v in t.verts], [[v.index for v in f.verts] for f in t.faces])
        t.free()
    vs, fs = _GOTA[seg]
    c = Vector(c)
    nv = [bm.verts.new(c + Vector((v.x * r * esc[0], v.y * r * esc[1], v.z * r * esc[2]))) for v in vs]
    for f in fs:
        bm.faces.new([nv[i] for i in f])


def flange(bm, bp, c, eixo, r, esp=0.022, n=8):
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


def tubo_curvo(bm, pts, raios, lados=14):
    """Tubo fechado varrido por uma curva com raio variável (névoa em espiral, linhas de campo)."""
    pts = [Vector(p) for p in pts]
    aneis = []
    ref = Z
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if abs(t.dot(ref)) > 0.95:
            ref = X
        u = t.cross(ref).normalized()
        v = t.cross(u)
        aneis.append([bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * raios[i])
                      for a in (k * 2 * PI / lados for k in range(lados))])
    fs = []
    for A, B in zip(aneis, aneis[1:]):
        for k in range(lados):
            fs.append(bm.faces.new((A[k], A[(k + 1) % lados], B[(k + 1) % lados], B[k])))
    fs.append(bm.faces.new(aneis[0][::-1]))
    fs.append(bm.faces.new(aneis[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def placa_rot(bm, a, b, larg, esp, cima=Z):
    """Chapa (caixa) de a até b, com largura no eixo 'cima' × direção e espessura na normal."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    n = d.cross(Vector(cima)).normalized()
    w = n.cross(d)
    rot = Matrix((d, n, w)).transposed()
    caixa(bm, (a + b) / 2, ((b - a).length, esp, larg), rot)


def parafusos_linha(bp, a, b, n, eixo, r=0.006, h=0.012):
    a, b = Vector(a), Vector(b)
    for k in range(n):
        cil(bp, a.lerp(b, (k + 0.5) / n), r, h, eixo, lados=6)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


VIOLETA = (0.6, 0.3, 1.0)


def malha_mat():
    """Tela de captação: malha fina de polietileno preto-esverdeado, molhada, com limo verde subindo da base.
    A trama é gerada por coordenada (fios em x e z); entre os fios é transparente."""
    m = bpy.data.materials.new('Malha')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    tremido = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 2.0})        # fio frouxo, não grade rígida
    nt.links.new(geo.outputs['Position'], tremido.inputs['Vector'])
    desl = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY_ADD')
    desl.inputs[1].default_value = (0.012, 0.012, 0.012)
    nt.links.new(tremido.outputs['Color'], desl.inputs[0])
    nt.links.new(geo.outputs['Position'], desl.inputs[2])
    nt.links.new(desl.outputs['Vector'], sep.inputs[0])
    fios = []
    for eixo, n_fio in (('X', 105.0), ('Z', 105.0)):
        mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        mul.inputs[1].default_value = n_fio
        nt.links.new(sep.outputs[eixo], mul.inputs[0])
        fr = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(mul.outputs['Value'], fr.inputs[0])
        gt = no(nt, 'ShaderNodeMath', operation='GREATER_THAN')
        gt.inputs[1].default_value = 0.8
        nt.links.new(fr.outputs['Value'], gt.inputs[0])
        fios.append(gt)
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fios[0].outputs['Value'], mx.inputs[0])
    nt.links.new(fios[1].outputs['Value'], mx.inputs[1])
    # rasgos e remendos: ruído grande abre buracos raros na trama
    rasgo_ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 3.0})
    nt.links.new(geo.outputs['Position'], rasgo_ru.inputs['Vector'])
    rasgo = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
    rasgo.inputs[1].default_value = 0.72
    nt.links.new(rasgo_ru.outputs['Fac'], rasgo.inputs[0])
    fio = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(mx.outputs['Value'], fio.inputs[0])
    nt.links.new(rasgo.outputs['Value'], fio.inputs[1])
    # limo: mais forte embaixo (z 0.9 → 1.5), manchado
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.55, 'From Max': 0.9, 'To Min': 0.15, 'To Max': 1.0})
    nt.links.new(sep.outputs['Z'], alt.inputs['Value'])
    lm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(alt.outputs['Result'], lm.inputs[0])
    nt.links.new(ru.outputs['Fac'], lm.inputs[1])
    limo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.25, 'From Max': 0.55})
    nt.links.new(lm.outputs['Value'], limo.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.03, 0.036, 0.03, 1)
    cor.inputs[7].default_value = (0.055, 0.1, 0.02, 1)
    nt.links.new(limo.outputs['Result'], cor.inputs[0])
    # escorrido de ferrugem do quadro (faixas verticais finas)
    fx = no(nt, 'ShaderNodeMapping')
    fx.inputs['Scale'].default_value = (40.0, 40.0, 2.0)
    nt.links.new(geo.outputs['Position'], fx.inputs['Vector'])
    ferr_ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 2.0})
    nt.links.new(fx.outputs['Vector'], ferr_ru.inputs['Vector'])
    ferr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.62, 'From Max': 0.72, 'To Max': 0.8})
    nt.links.new(ferr_ru.outputs['Fac'], ferr.inputs['Value'])
    cor2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor2.inputs[7].default_value = (0.2, 0.08, 0.025, 1)
    nt.links.new(ferr.outputs['Result'], cor2.inputs[0])
    nt.links.new(cor.outputs[2], cor2.inputs[6])
    nt.links.new(cor2.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.32
    b.inputs['Coat Weight'].default_value = 0.5                        # filme d'água
    b.inputs['Coat Roughness'].default_value = 0.05
    nt.links.new(fio.outputs['Value'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def agua_mat(nome='Água', cor=(0.85, 0.93, 0.95)):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.02
    b.inputs['IOR'].default_value = 1.33
    return m


def poca_mat():
    """Poça: lâmina d'água escura que espelha, com ondinhas."""
    m = bpy.data.materials.new('Poça')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.03, 0.032, 0.03, 1)
    b.inputs['Roughness'].default_value = 0.03
    b.inputs['Specular IOR Level'].default_value = 0.6
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.05})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def gelo_mat():
    """Gelo / geada da serpentina: branco-azulado, áspero, translúcido (subsuperfície), cristais em relevo."""
    m = bpy.data.materials.new('Gelo')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.82, 0.88, 0.92, 1)
    b.inputs['Roughness'].default_value = 0.45
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = (0.02, 0.03, 0.04)
    b.inputs['Coat Weight'].default_value = 0.3
    tc = no(nt, 'ShaderNodeTexCoord')
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 260.0})
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.6})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def sincelo_mat():
    m = bpy.data.materials.new('Sincelo')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.9, 0.95, 0.97, 1)
    b.inputs['Transmission Weight'].default_value = 0.85
    b.inputs['Roughness'].default_value = 0.12
    b.inputs['IOR'].default_value = 1.31
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
    b.inputs['Emission Strength'].default_value = 3.0
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 70.0})
    tc = no(nt, 'ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def nevoa_espiral_mat():
    """Névoa puxada pelo campo: volume branco-acinzentado, rasgado por ruído, que ganha um brilho violeta fraco
    perto do anel de campo (y = Y_ANEL no mundo)."""
    m = bpy.data.materials.new('Névoa espiral')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.97, 0.98, 0.99, 1)
    vol.inputs['Anisotropy'].default_value = 0.25
    vol.inputs['Emission Color'].default_value = (*VIOLETA, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    geo0 = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 4.5, 'Detail': 8.0, 'Roughness': 0.7})
    nt.links.new(geo0.outputs['Position'], ru.inputs['Vector'])
    f0 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.7})
    nt.links.new(ru.outputs['Fac'], f0.inputs['Value'])
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')            # bolha: some na borda (sem casca)
    nt.links.new(tc.outputs['Object'], ln.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.35})
    nt.links.new(ln.outputs['Value'], borda.inputs['Value'])
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(f0.outputs['Result'], f.inputs[0])
    nt.links.new(borda.outputs['Result'], f.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='dens')
    d.inputs[1].default_value = 5.0
    nt.links.new(f.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    perto = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.2, 'From Max': Y_ANEL, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(sep.outputs['Y'], perto.inputs['Value'])
    em = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='brilho')
    em.inputs[1].default_value = 0.5
    nt.links.new(perto.outputs['Result'], em.inputs[0])
    em2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(em.outputs['Value'], em2.inputs[0])
    nt.links.new(f.outputs['Value'], em2.inputs[1])
    nt.links.new(em2.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def nevoa_chao_mat():
    """Neblina de chão em volta de tudo: densa rente ao chão, rala acima de ~1,5 m, em bancos (ruído grande)."""
    m = bpy.data.materials.new('Neblina de chão')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.86, 0.88, 0.9, 1)
    vol.inputs['Anisotropy'].default_value = 0.2
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 2.4, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sep.outputs['Z'], alt.inputs['Value'])
    alt2 = no(nt, 'ShaderNodeMath', operation='POWER')
    alt2.inputs[1].default_value = 3.0
    nt.links.new(alt.outputs['Result'], alt2.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.45, 'Detail': 5.0, 'Roughness': 0.55})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    banco = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.62, 'To Min': 0.05, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], banco.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(alt2.outputs['Value'], mul.inputs[0])
    nt.links.new(banco.outputs['Result'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = 0.9
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    return m


def nevoa_fria_mat():
    """Ar gelado que escorre da bandeja: volume branco que some por baixo."""
    return base3d.volume_mat('Névoa fria', (0.92, 0.94, 0.96), 6.0, 0.95, 0.35)


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
    ru = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y')
    ru.inputs['Scale'].default_value = 3.0
    ru.inputs['Distortion'].default_value = 4.0
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.9, 'To Min': 0.0, 'To Max': 0.8})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    forca = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca')
    forca.inputs[1].default_value = 3.0
    nt.links.new(f.outputs['Result'], forca.inputs[0])
    nt.links.new(forca.outputs['Value'], em.inputs['Strength'])
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def escorrido_mat(nome, cor, alpha=0.85):
    """Escorrido (ferrugem ou limo) em faixa vertical: some para baixo e nas bordas (coordenada UV gerada)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.8
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    desce = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 1.0, 'To Min': 0.0, 'To Max': alpha})
    nt.links.new(sep.outputs['Z'], desce.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 4.0})
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (14.0, 14.0, 1.5)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    corte = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.6})
    nt.links.new(ru.outputs['Fac'], corte.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(desce.outputs['Result'], mul.inputs[0])
    nt.links.new(corte.outputs['Result'], mul.inputs[1])
    nt.links.new(mul.outputs['Value'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


Y_ANEL = -0.36               # plano do anel de campo
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.85, ferrugem=0.45),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'primer': mats.material('Primer', (0.36, 0.07, 0.04), 0, 0.7, desgaste=0.6, sujeira=0.8, ferrugem=0.3),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.9, sujeira=0.85, escovado=True),
    'galv': mats.material('Galvanizado', (0.55, 0.56, 0.56), 1.0, 0.5, pintura=False, ferrugem=0.55, sujeira=0.85),
    'cano': mats.material('Cano', (0.30, 0.31, 0.32), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=0.9),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.95, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.78, 0.4, 0.22), 1.0, 0.32, pintura=False, sujeira=0.85, ferrugem=0.25),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.38, pintura=False, sujeira=0.8),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.8, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'espuma': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.85, pintura=False, sujeira=0.6, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'ponteiro': mats.material('Ponteiro', (0.5, 0.05, 0.02), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'limo': mats.material('Limo', (0.07, 0.13, 0.025), 0, 0.35, pintura=False, sujeira=0.5, desgaste=0.0),
    'lama': mats.material('Lama', (0.12, 0.09, 0.05), 0, 0.3, pintura=False, sujeira=0.4, desgaste=0.0),
    'pedra': mats.material('Pedra', (0.15, 0.145, 0.13), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'malha': malha_mat(),
    'agua': agua_mat(),
    'agua_calha': agua_mat('Água da calha', (0.6, 0.72, 0.62)),
    'poca': poca_mat(),
    'gelo': gelo_mat(),
    'sincelo': sincelo_mat(),
    'cristal': cristal_mat(),
    'vidro': agua_mat('Vidro', (0.9, 0.93, 0.92)),
    'nevoa': nevoa_espiral_mat(),
    'nevoa_chao': nevoa_chao_mat(),
    'nevoa_fria': nevoa_fria_mat(),
    'campo': campo_linha_mat(),
    'escorre_ferr': escorrido_mat('Escorrido de ferrugem', (0.22, 0.08, 0.025)),
    'escorre_limo': escorrido_mat('Escorrido de limo', (0.06, 0.11, 0.02), 0.95),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'verde': emissivo('Luz verde', (0.15, 1.0, 0.25), 5.0, (0.05, 0.3, 0.08)),
    'emissor': emissivo('Emissor', (0.45, 0.12, 1.0), 1.5, (0.15, 0.03, 0.4)),
})
M = base3d.M
for m in M.values():
    if hasattr(m, 'blend_method'):
        try:
            m.blend_method = 'HASHED'
        except Exception:
            pass

# ------------------------------------------------------------------ medidas
Z0 = 0.08                    # topo da laje
Y_TELA = 0.12                # plano das telas
XP = (-0.94, 0.0, 0.94)      # postes do quadro
ZT0, ZT1 = 0.9, 2.0          # malha (vertical)
Y_SERP = (0.29, 0.35)        # duas fileiras da serpentina
Z_PISO = 0.86                # bandeja/piso do plenum
Y_PAR = 0.65                 # parede dos ventiladores
VENT = [Vector((-0.48, Y_PAR, 1.48)), Vector((0.48, Y_PAR, 1.48))]
R_VENT = 0.42
C_ANEL = Vector((0.0, Y_ANEL, 1.48))
R_ANEL = 0.72
TQ = Vector((-0.52, -0.4, 0.0))  # tanque
R_TQ = 0.28
Z_TQ0, Z_TQ1 = 0.14, 0.56
BOMBA = Vector((-0.5, -0.8, 0.2))
Z_SAIDA = 0.28
COMP = Vector((0.42, -0.42, 0.0))

GM, GF, GP = bmesh.new(), bmesh.new(), bmesh.new()   # manômetros


def manometro(p, cima, face):
    p, cima, face = Vector(p), Vector(cima).normalized(), Vector(face).normalized()
    tubo(GM, p, p + cima * 0.06, 0.007, 8)
    c = p + cima * 0.09
    cil(GM, c, 0.034, 0.022, face, lados=20)
    cil(GF, c + face * 0.0115, 0.029, 0.002, face, lados=20)
    u, v, _ = base_de(face)
    ang = random.uniform(0.3, 2.4)
    d = u * math.cos(ang) + v * math.sin(ang)
    viga(GP, c + face * 0.0135 - d * 0.005, c + face * 0.0135 + d * 0.024, 0.003)


# ------------------------------------------------------------------ laje, valeta, listras
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
obj('laje', bm, 'concreto')
bm = bmesh.new()
for a, b in (((-0.98, -0.98), (0.98, -0.92)), ((-0.98, 0.92), (0.98, 0.98)),
             ((-0.98, -0.92), (-0.92, 0.92)), ((0.92, -0.92), (0.98, 0.92))):
    caixa_de(bm, (a[0], a[1], Z0), (b[0], b[1], Z0 + 0.004))
obj('listras_borda', bm, 'listras')
bm, bg = bmesh.new(), bmesh.new()                                         # valeta com grade aos pés das telas
caixa_de(bm, (-0.9, -0.06, Z0 - 0.002), (0.9, 0.05, Z0 + 0.002))
obj('valeta_fundo', bm, 'oleo')
caixa_de(bg, (-0.9, -0.065, Z0), (0.9, -0.055, Z0 + 0.012))
caixa_de(bg, (-0.9, 0.045, Z0), (0.9, 0.055, Z0 + 0.012))
for k in range(36):
    x = -0.88 + k * 0.05
    caixa_de(bg, (x, -0.055, Z0 + 0.002), (x + 0.012, 0.045, Z0 + 0.01))
obj('valeta_grade', bg, 'ferro')

# ------------------------------------------------------------------ quadro das telas: postes, travessas, sapatas
bm, bp = bmesh.new(), bmesh.new()
for x in XP:
    caixa_de(bm, (x - 0.03, Y_TELA - 0.03, Z0), (x + 0.03, Y_TELA + 0.03, 2.12))
    caixa_de(bm, (x - 0.07, Y_TELA - 0.07, Z0), (x + 0.07, Y_TELA + 0.07, Z0 + 0.015))    # sapata
    for sx in (-1, 1):
        for sy in (-1, 1):
            cil(bp, Vector((x + sx * 0.05, Y_TELA + sy * 0.05, Z0 + 0.02)), 0.008, 0.02, lados=6)
    # mão-francesa para trás (até a perna do plenum)
caixa_de(bm, (-0.97, Y_TELA - 0.03, 2.07), (0.97, Y_TELA + 0.03, 2.13))                    # travessa de cima
obj('quadro', bm, 'amarelo')
obj('quadro_parafusos', bp, 'ferro')
bm = bmesh.new()                                                                            # tampões dos postes
for x in XP:
    caixa_de(bm, (x - 0.034, Y_TELA - 0.034, 2.12), (x + 0.034, Y_TELA + 0.034, 2.135))
obj('tampoes', bm, 'ferro')

# telas: quadro interno de cantoneira, malha dupla, esticadores nos postes
PAINEIS = [(-0.87, -0.07), (0.07, 0.87)]
bm, bp, bc = bmesh.new(), bmesh.new(), bmesh.new()
for x0, x1 in PAINEIS:
    for (a, b) in (((x0, ZT0 - 0.03), (x1, ZT0)), ((x0, ZT1), (x1, ZT1 + 0.03)),
                   ((x0, ZT0 - 0.03), (x0 + 0.03, ZT1 + 0.03)), ((x1 - 0.03, ZT0 - 0.03), (x1, ZT1 + 0.03))):
        caixa_de(bm, (a[0], Y_TELA - 0.018, a[1]), (b[0], Y_TELA + 0.018, b[1]))
    caixa_de(bm, ((x0 + x1) / 2 - 0.012, Y_TELA + 0.006, ZT0), ((x0 + x1) / 2 + 0.012, Y_TELA + 0.018, ZT1))  # montante
    # esticadores: olhal no quadro → tensor → olhal no poste (lados) / na travessa (cima)
    for z in (ZT0 + 0.1, (ZT0 + ZT1) / 2, ZT1 - 0.1):
        for xa, xb in ((x0, x0 - 0.04), (x1, x1 + 0.04)):
            if abs(xb) > 0.95 or abs(xb) < 0.03:
                xb = math.copysign(0.91, xb) if abs(xb) > 0.5 else math.copysign(0.03, xb)
            tubo(bc, Vector((xa, Y_TELA, z)), Vector((xb, Y_TELA, z)), 0.004, 6)
            cil(bp, Vector(((xa + xb) / 2, Y_TELA, z)), 0.008, abs(xb - xa) * 0.5, X, lados=8)
    for x in (x0 + 0.15, (x0 + x1) / 2, x1 - 0.15):
        tubo(bc, Vector((x, Y_TELA, ZT1 + 0.03)), Vector((x, Y_TELA, 2.07)), 0.004, 6)
        cil(bp, Vector((x, Y_TELA, ZT1 + 0.055)), 0.008, 0.025, Z, lados=8)
    # laçada da malha no quadro (argolas)
    for k in range(14):
        z = ZT0 + (k + 0.5) * (ZT1 - ZT0) / 14
        for x in (x0 + 0.015, x1 - 0.015):
            toro(bc, Vector((x, Y_TELA, z)), 0.012, 0.0025, Z, nR=10, nr=4)
obj('telas_quadro', bm, 'galv')
obj('telas_tensores', bp, 'aco')
obj('telas_cabos', bc, 'cromo')
bm = bmesh.new()
for x0, x1 in PAINEIS:
    for dy in (-0.004, 0.004):
        caixa_de(bm, (x0 + 0.02, Y_TELA + dy - 0.0005, ZT0 + 0.002), (x1 - 0.02, Y_TELA + dy + 0.0005, ZT1 - 0.002))
obj('telas_malha', bm, 'malha')

# gotas na malha (mais embaixo), gotas escorrendo (alongadas), fila de gotas na borda de baixo
bm = bmesh.new()
for k in range(1500):
    x0, x1 = PAINEIS[k % 2]
    x = random.uniform(x0 + 0.03, x1 - 0.03)
    z = ZT0 + 0.01 + (ZT1 - ZT0 - 0.02) * random.random() ** 1.7
    r = random.uniform(0.0025, 0.006) * (1.3 if z < 1.2 else 1.0)
    lado = random.choice((-1, 1))
    esc = (1, 0.7, random.uniform(1.0, 1.4))
    if random.random() < 0.15:
        esc = (0.8, 0.6, random.uniform(2.5, 5.0))                     # gota escorrendo, deixando rastro
    gota(bm, (x, Y_TELA + lado * 0.0055, z), r, 8, esc)
for x0, x1 in PAINEIS:
    for k in range(60):
        x = x0 + 0.04 + k * (x1 - x0 - 0.08) / 59 + random.uniform(-0.004, 0.004)
        gota(bm, (x, Y_TELA + random.uniform(-0.01, 0.01), ZT0 - 0.034), random.uniform(0.003, 0.006), 8, (1, 1, 1.4))
obj('gotas_tela', bm, 'agua')

# ------------------------------------------------------------------ calha inclinada (leste → oeste) e caixa coletora
def z_calha(x):
    return 0.8 + (x + 0.86) / 1.78 * 0.05          # topo: 0.85 a leste, 0.80 a oeste


bm, bp, ba = bmesh.new(), bmesh.new(), bmesh.new()
X_C0, X_C1 = -0.84, 0.92
a, b = Vector((X_C0, Y_TELA, z_calha(X_C0) - 0.06)), Vector((X_C1, Y_TELA, z_calha(X_C1) - 0.06))
placa_rot(bm, a, b, 0.006, 0.12, Y)              # fundo (chapa deitada: largura em y)
for s in (-1, 1):
    placa_rot(bm, a + Vector((0, s * 0.06, 0.03)), b + Vector((0, s * 0.06, 0.03)), 0.06, 0.005)
for x in (-0.5, 0.0, 0.48):                      # emendas com tira de chapa e rebites
    zc = z_calha(x)
    caixa_de(bm, (x - 0.02, Y_TELA - 0.066, zc - 0.066), (x + 0.02, Y_TELA + 0.066, zc - 0.002))
    parafusos_linha(bp, (x, Y_TELA - 0.067, zc - 0.05), (x, Y_TELA - 0.067, zc - 0.01), 2, Y, 0.004, 0.006)
caixa_de(bm, (X_C1 - 0.004, Y_TELA - 0.06, z_calha(X_C1) - 0.06), (X_C1 + 0.004, Y_TELA + 0.06, z_calha(X_C1)))  # tampa
for x0, x1 in PAINEIS:                            # alças da calha penduradas no quadro da tela
    for x in (x0 + 0.12, x1 - 0.12):
        zc = z_calha(x)
        toro(bp, Vector((x, Y_TELA, zc - 0.035)), 0.066, 0.005, X, nR=20, nr=6, a0=PI, a1=2 * PI)
        tubo(bp, Vector((x, Y_TELA - 0.066, zc - 0.035)), Vector((x, Y_TELA - 0.066, ZT0 - 0.02)), 0.005, 6)
        tubo(bp, Vector((x, Y_TELA + 0.066, zc - 0.035)), Vector((x, Y_TELA + 0.066, ZT0 - 0.02)), 0.005, 6)
obj('calha', bm, 'galv')
obj('calha_alcas', bp, 'ferro')
# água correndo no fundo da calha, limo e lodo
placa_rot(ba, a + Vector((0, 0, 0.014)), b + Vector((-0.02, 0, 0.004)), 0.006, 0.106, Y)
obj('calha_agua', ba, 'agua_calha')
bm = bmesh.new()
for k in range(10):
    x = random.uniform(X_C0 + 0.05, X_C1 - 0.05)
    zc = z_calha(x) - 0.052
    mancha(bm, (x, Y_TELA), random.uniform(0.02, 0.05), zc + 0.02)
obj('calha_limo', bm, 'limo')

# caixa coletora (funil) na ponta oeste
CX = Vector((-0.8, Y_TELA, 0.0))
bm, bp = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.9, Y_TELA - 0.085, 0.72), (-0.86, Y_TELA + 0.085, 0.84))
caixa_de(bm, (-0.74, Y_TELA - 0.085, 0.72), (-0.70, Y_TELA + 0.085, 0.79))
for s in (-1, 1):
    caixa_de(bm, (-0.9, Y_TELA + s * 0.085 - 0.004, 0.72), (-0.70, Y_TELA + s * 0.085 + 0.004, 0.84 if s else 0.8))
cil(bm, Vector((-0.8, Y_TELA, 0.715)), 0.07, 0.04, lados=20, r2=0.035)
caixa_de(bm, (-0.9, Y_TELA - 0.085, 0.735), (-0.70, Y_TELA + 0.085, 0.745))   # grelha/tela de folhas
obj('coletora', bm, 'galv')
parafusos_linha(bp, (-0.895, Y_TELA - 0.09, 0.78), (-0.705, Y_TELA - 0.09, 0.78), 5, Y, 0.005, 0.008)
obj('coletora_rebites', bp, 'ferro')

# cano da coletora até o tampo do tanque
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [(-0.8, Y_TELA, 0.69), (-0.8, Y_TELA, 0.68), (-0.8, -0.4, 0.68), (-0.6, -0.4, 0.68), (-0.6, -0.4, 0.62)],
     0.028, fl_pontas=False)
suavizar(obj('cano_entrada', bm, 'cano'))
obj('cano_entrada_fl', bf, 'ferro')
obj('cano_entrada_par', bp, 'aco')

# ------------------------------------------------------------------ plenum: piso-bandeja, laterais, teto, parede dos ventiladores
bm, bp = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.96, 0.18, Z_PISO - 0.02), (0.96, Y_PAR, Z_PISO))                 # bandeja
caixa_de(bm, (-0.96, 0.18, Z_PISO), (0.96, 0.195, Z_PISO + 0.04))                 # borda da frente
obj('bandeja', bm, 'galv')
bm, bm2 = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.965, 0.18, Z_PISO - 0.02), (-0.94, Y_PAR, 2.1))                  # lateral oeste (amarela)
caixa_de(bm2, (0.94, 0.18, Z_PISO - 0.02), (0.965, Y_PAR, 2.1))                   # lateral leste trocada (primer)
caixa_de(bm, (-0.965, 0.18, 2.08), (0.965, Y_PAR, 2.1))                           # teto
for k in range(7):                                                                # nervuras do teto
    x = -0.9 + k * 0.3
    caixa_de(bm, (x - 0.012, 0.18, 2.1), (x + 0.012, Y_PAR, 2.12))
obj('plenum', bm, 'amarelo')
obj('plenum_lateral_trocada', bm2, 'primer')
for sx, x in ((-1, -0.97), (1, 0.97)):                                              # rebites nas bordas das laterais
    for z in (Z_PISO + 0.02, 2.06):
        parafusos_linha(bp, (x, 0.2, z), (x, Y_PAR - 0.02, z), 8, X, 0.005, 0.012)
    for yy in (0.2, Y_PAR - 0.02):
        parafusos_linha(bp, (x, yy, Z_PISO + 0.05), (x, yy, 2.05), 10, X, 0.005, 0.012)
obj('plenum_rebites', bp, 'ferro')
# remendos aparafusados
bm, bp = bmesh.new(), bmesh.new()
for c, t in (((-0.975, 0.42, 1.25), (0.012, 0.2, 0.16)), ((-0.975, 0.3, 1.8), (0.012, 0.1, 0.12)),
             ((0.3, 0.17, 2.105), (0.18, 0.05, 0.012))):
    caixa(bm, c, t)
for c, t in (((-0.982, 0.42, 1.25), (0.2, 0.16)), ((-0.982, 0.3, 1.8), (0.1, 0.12))):
    for sy in (-1, 1):
        for sz in (-1, 1):
            cil(bp, Vector((c[0], c[1] + sy * (t[0] / 2 - 0.015), c[2] + sz * (t[1] / 2 - 0.015))), 0.006, 0.012, X, lados=6)
obj('remendos', bm, 'aco')
obj('remendos_paraf', bp, 'ferro')

# parede dos ventiladores com dois furos (booleano)
bm = bmesh.new()
caixa_de(bm, (-0.965, Y_PAR - 0.012, Z_PISO - 0.02), (0.965, Y_PAR + 0.012, 2.1))
parede = obj('parede_vent', bm, 'amarelo')
for k, c in enumerate(VENT):
    bm = bmesh.new()
    cil(bm, c, R_VENT + 0.02, 0.2, Y, lados=64)
    corte = obj('corte%d' % k, bm, 'aco')
    md = parede.modifiers.new('furo%d' % k, 'BOOLEAN')
    md.operation, md.object = 'DIFFERENCE', corte
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(parede.evaluated_get(dg))
parede.modifiers.clear()
parede.data = me
for k in range(2):
    bpy.data.objects.remove(bpy.data.objects['corte%d' % k])

# pernas do plenum (atrás) e mãos-francesas
bm, bp = bmesh.new(), bmesh.new()
for x in (-0.93, 0.0, 0.93):
    caixa_de(bm, (x - 0.03, Y_PAR + 0.015, Z0), (x + 0.03, Y_PAR + 0.075, Z_PISO + 0.05))
    caixa_de(bm, (x - 0.06, Y_PAR - 0.0, Z0), (x + 0.06, Y_PAR + 0.1, Z0 + 0.015))
    viga(bm, Vector((x, Y_TELA + 0.03, 0.35)), Vector((x, Y_PAR + 0.015, 0.7)), 0.03)
    for sx in (-1, 1):
        cil(bp, Vector((x + sx * 0.045, Y_PAR + 0.08, Z0 + 0.02)), 0.008, 0.02, lados=6)
obj('pernas', bm, 'grafite')
obj('pernas_paraf', bp, 'ferro')

# ------------------------------------------------------------------ serpentina fria: dupla fileira, curvas, aletas, gelo
bm, bg, bs = bmesh.new(), bmesh.new(), bmesh.new()
X_S = 0.8                                             # curvas em ±X_S
ZS = [1.95 - k * 0.1 for k in range(10)]
R_S = 0.011
for yi, ys in enumerate(Y_SERP):
    for k, z in enumerate(ZS):
        tubo(bm, Vector((-X_S, ys, z)), Vector((X_S, ys, z)), R_S, 12)
        if k < len(ZS) - 1:
            lado = -1 if k % 2 == 0 else 1             # curva em U
            toro(bm, Vector((lado * X_S, ys, z - 0.05)), 0.05, R_S, Y, nR=12, nr=10,
                 a0=(-PI / 2 if lado > 0 else PI / 2), a1=(PI / 2 if lado > 0 else 3 * PI / 2))
    # pontas: em cima e embaixo vão para os coletores a leste (x = 0.86)
    tubo(bm, Vector((X_S, ys, ZS[0])), Vector((0.86, ys, ZS[0])), R_S, 12)
    tubo(bm, Vector((X_S, ys, ZS[-1])), Vector((0.86, ys, ZS[-1])), R_S, 12)
# coletores verticais curtos (tubo grosso) que juntam as duas fileiras
for z in (ZS[0], ZS[-1]):
    tubo(bm, Vector((0.86, Y_SERP[0] - 0.03, z)), Vector((0.86, 0.47, z)), 0.02, 14)
obj('serpentina', bm, 'cobre')
# aletas de alumínio (placas finas verticais atravessadas pelos tubos)
for k in range(17):
    x = -0.76 + k * 0.095
    caixa_de(bs, (x - 0.0015, Y_SERP[0] - 0.035, ZS[-1] - 0.04), (x + 0.0015, Y_SERP[1] + 0.035, ZS[0] + 0.04))
obj('aletas_serp', bs, 'aluminio')
# geada: luvas irregulares em trechos dos tubos e nas aletas de baixo
for yi, ys in enumerate(Y_SERP):
    for k, z in enumerate(ZS):
        x = -X_S + 0.02
        while x < X_S - 0.05:
            L = random.uniform(0.06, 0.3)
            if random.random() < 0.55 + 0.04 * k:
                rr = R_S + random.uniform(0.004, 0.009) + 0.0015 * k
                vv = bmesh.ops.create_cone(bg, cap_ends=True, segments=10, radius1=rr, radius2=rr * random.uniform(0.8, 1.1),
                                           depth=min(L, X_S - x), matrix=Matrix.Translation((x + min(L, X_S - x) / 2, ys, z)) @
                                           Matrix.Rotation(PI / 2, 4, 'Y'))['verts']
                for v in vv:
                    v.co += Vector([random.uniform(-0.002, 0.002) for _ in range(3)])
            x += L
for k in range(17):                                    # geada na base das aletas
    x = -0.76 + k * 0.095
    caixa_de(bg, (x - 0.004, Y_SERP[0] - 0.036, ZS[-1] - 0.04), (x + 0.004, Y_SERP[1] + 0.036, ZS[-1] + 0.03 + random.uniform(0, 0.12)))
obj('geada', bg, 'gelo')
# sincelos: embaixo do último tubo e na borda da bandeja (apontando para a calha)
bm = bmesh.new()
SINCELOS = []
for k in range(26):
    x = random.uniform(-0.76, 0.76)
    L = random.uniform(0.03, 0.11)
    ys = random.choice(Y_SERP)
    cil(bm, Vector((x, ys, ZS[-1] - R_S - L / 2 + 0.004)), 0.007, L, Z, lados=8, r2=0.0)
for k in range(30):
    x = random.uniform(-0.9, 0.9)
    L = random.uniform(0.012, 0.045)
    p = Vector((x, 0.188, Z_PISO - 0.02 - L / 2))
    cil(bm, p, 0.006, L, -Z, lados=8, r2=0.0005)
    SINCELOS.append(p - Vector((0, 0, L / 2)))
obj('sincelos', bm, 'sincelo')
# bica da bandeja despejando na calha (x = 0.3) e degelo
bm = bmesh.new()
BICA = Vector((0.3, 0.17, Z_PISO - 0.01))
caixa_de(bm, (0.27, 0.15, Z_PISO - 0.02), (0.33, 0.195, Z_PISO + 0.005))
obj('bica', bm, 'galv')

# ------------------------------------------------------------------ ventiladores (pás animadas), anéis, grades, motores
rotores = []
for k, c in enumerate(VENT):
    bm = bmesh.new()
    tubo_oco(bm, c + Vector((0, 0.1, 0)), R_VENT + 0.035, R_VENT + 0.015, 0.2, Y, lados=64)
    toro(bm, c + Vector((0, 0.2, 0)), R_VENT + 0.04, 0.012, Y, nR=48, nr=8)       # bocal enrolado
    obj('vent%d_anel' % k, bm, 'amarelo')
    bm, bp = bmesh.new(), bmesh.new()
    for i in range(12):                                                            # flange do anel na parede
        a = i * 2 * PI / 12
        cil(bp, c + Vector((math.cos(a) * (R_VENT + 0.06), Y_PAR + 0.016, math.sin(a) * (R_VENT + 0.06))), 0.007, 0.01, Y, lados=6)
    toro(bm, c + Vector((0, Y_PAR + 0.012 - Y_PAR, 0)) + Vector((0, 0.0, 0)), R_VENT + 0.06, 0.008, Y, nR=48, nr=6)
    obj('vent%d_flange' % k, bm, 'ferro')
    obj('vent%d_paraf' % k, bp, 'aco')
    # motor atrás (norte), preso por aranha de 3 braços no anel
    YM = Y_PAR + 0.17
    bm, bp = bmesh.new(), bmesh.new()
    cil(bm, c + Vector((0, YM - Y_PAR, 0)), 0.1, 0.16, Y, lados=24)
    for i in range(10):                                                            # aletas do motor
        a = i * 2 * PI / 10
        caixa(bm, c + Vector((math.cos(a) * 0.105, YM - Y_PAR, math.sin(a) * 0.105)), (0.012, 0.14, 0.012),
              Matrix.Rotation(-a, 3, 'Y'))
    cil(bm, c + Vector((0, YM - Y_PAR + 0.09, 0)), 0.07, 0.03, Y, lados=20)
    caixa(bm, c + Vector((0, YM - Y_PAR, 0.12)), (0.06, 0.07, 0.05))              # caixa de ligação
    obj('vent%d_motor' % k, bm, 'grafite')
    for i in range(3):
        a = PI / 2 + i * 2 * PI / 3
        d = Vector((math.cos(a), 0, math.sin(a)))
        viga(bp, c + Vector((0, YM - Y_PAR + 0.04, 0)) + d * 0.09, c + Vector((0, 0.19, 0)) + d * (R_VENT + 0.02), 0.022)
    # grade de proteção (norte)
    for r in (0.12, 0.22, 0.32, R_VENT + 0.01):
        toro(bp, c + Vector((0, 0.215, 0)), r, 0.0035, Y, nR=48, nr=6)
    for i in range(16):
        a = i * 2 * PI / 16
        d = Vector((math.cos(a), 0, math.sin(a)))
        tubo(bp, c + Vector((0, 0.215, 0)) + d * 0.12, c + Vector((0, 0.215, 0)) + d * (R_VENT + 0.01), 0.003, 6)
    obj('vent%d_grade' % k, bp, 'aco')
    # rotor: cubo + 6 pás torcidas (eixo local Y)
    piv = bpy.data.objects.new('vent%d_rotor' % k, None)
    sc.collection.objects.link(piv)
    piv.location = c + Vector((0, 0.08, 0))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.085, 0.07, Y, lados=24)
    esfera(bm, Vector((0, -0.035, 0)), 0.085, 24, (1, 0.5, 1))
    obj('vent%d_cubo' % k, bm, 'grafite', piv)
    bm = bmesh.new()
    for i in range(6):
        a0 = i * 2 * PI / 6
        linhas = []
        for j in range(7):
            t = j / 6
            r = 0.08 + t * (R_VENT - 0.1)
            corda = 0.15 - 0.05 * t
            passo = math.radians(38 - 20 * t)
            a = a0 + 0.1 * t
            rad = Vector((math.cos(a), 0, math.sin(a)))
            tang = Vector((-math.sin(a), 0, math.cos(a)))
            p1 = rad * r + (tang * math.cos(passo) + Y * math.sin(passo)) * corda / 2
            p2 = rad * r - (tang * math.cos(passo) + Y * math.sin(passo)) * corda / 2
            linhas.append((bm.verts.new(p1), bm.verts.new(p2)))
        for (a1, b1), (a2, b2) in zip(linhas, linhas[1:]):
            bm.faces.new((a1, b1, b2, a2))
    pas = obj('vent%d_pas' % k, bm, 'aluminio', piv)
    sd = pas.modifiers.new('esp', 'SOLIDIFY')
    sd.thickness = 0.006
    rotores.append(piv)

# eletrocalha atrás (norte), cabos dos motores
bm, bc = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.9, 0.9, 0.25), (0.9, 0.96, 0.26))
for s in (0.9, 0.96):
    caixa_de(bm, (-0.9, s - 0.003, 0.25), (0.9, s + 0.003, 0.3))
for x in (-0.6, 0.0, 0.6):
    caixa_de(bm, (x - 0.01, 0.89, 0.29), (x + 0.01, 0.97, 0.3))
for x in (-0.9, 0.9):
    caixa_de(bm, (x - 0.015, 0.92, Z0), (x + 0.015, 0.94, 0.25))                  # mão da eletrocalha
obj('eletrocalha_norte', bm, 'aco')
for k, c in enumerate(VENT):
    cx = c + Vector((0, Y_PAR + 0.17 - Y_PAR, 0.145))
    pts = bezier(cx, cx + Vector((0, 0.1, 0.15)), Vector((c.x * 0.8, 0.95, 0.6)), Vector((c.x * 0.7, 0.93, 0.28)), 14)
    mangueira(bc, pts, 0.013)
obj('cabos_vent', bc, 'borracha')

# ------------------------------------------------------------------ anel de campo (toque da IA) com cristais
bm, bp, bcr = bmesh.new(), bmesh.new(), bmesh.new()
toro(bm, C_ANEL, R_ANEL, 0.04, Y, nR=96, nr=16)
toro(bp, C_ANEL + Vector((0, -0.05, 0)), R_ANEL, 0.012, Y, nR=96, nr=8)          # trilho de bobina
toro(bp, C_ANEL + Vector((0, 0.05, 0)), R_ANEL, 0.012, Y, nR=96, nr=8)
EMISSORES = []
for i in range(8):
    a = i * 2 * PI / 8 + PI / 8
    d = Vector((math.cos(a), 0, math.sin(a)))
    p = C_ANEL + d * R_ANEL
    caixa(bp, p - d * 0.03, (0.09, 0.11, 0.07), Matrix.Rotation(-a, 3, 'Y'))       # garra do emissor
    cil(bp, p - d * 0.075, 0.03, 0.03, -d, lados=16)
    q = p - d * 0.13                                                              # cristal apontando para dentro
    v = [q + d * 0.05, q - d * 0.07]
    for b2 in (Vector((0, 0.025, 0)), Vector((0, -0.025, 0)), d.cross(Y) * 0.025, -d.cross(Y) * 0.025):
        v.append(q + b2)
    vs = [bcr.verts.new(x) for x in v]
    eq = [vs[2], vs[4], vs[3], vs[5]]
    for j in range(4):
        bcr.faces.new((vs[0], eq[j], eq[(j + 1) % 4]))
        bcr.faces.new((vs[1], eq[(j + 1) % 4], eq[j]))
    EMISSORES.append(q)
bmesh.ops.recalc_face_normals(bcr, faces=bcr.faces[:])
suavizar(obj('anel_campo', bm, 'grafite'))
obj('anel_garras', bp, 'aco')
obj('anel_cristais', bcr, 'cristal')
# braços do anel: dos postes laterais e da travessa de cima, com listras de perigo nos braços
bm, bl = bmesh.new(), bmesh.new()
for sx in (-1, 1):
    pa = Vector((sx * 0.94, Y_TELA - 0.03, C_ANEL.z))
    pb = C_ANEL + Vector((sx * (R_ANEL + 0.035), 0, 0))
    viga(bm, pa, pb, 0.05)
    caixa(bm, pa + Vector((0, -0.005, 0)), (0.09, 0.012, 0.12))
    viga(bm, Vector((sx * 0.94, Y_TELA - 0.03, 0.55)), pb + Vector((0, 0, -0.03)), 0.035)   # escora
pa, pb = Vector((0, Y_TELA - 0.03, 2.1)), C_ANEL + Vector((0, 0, R_ANEL + 0.035))
viga(bm, pa, pb, 0.05)
obj('anel_bracos', bm, 'grafite')
for sx in (-1, 1):
    pa = Vector((sx * 0.94, Y_TELA - 0.03, C_ANEL.z))
    pb = C_ANEL + Vector((sx * (R_ANEL + 0.035), 0, 0))
    viga(bl, pa.lerp(pb, 0.25), pa.lerp(pb, 0.75), 0.053)
obj('anel_listras', bl, 'listras')
# cabo de força do anel: desce pelo braço leste e pelo poste até a caixa
bm = bmesh.new()
pa = Vector((0.94, Y_TELA - 0.03, C_ANEL.z))
pts = bezier(C_ANEL + Vector((R_ANEL + 0.02, -0.03, 0.04)), pa.lerp(C_ANEL, 0.5) + Vector((0, 0, 0.06)),
             pa + Vector((-0.04, -0.06, 0.05)), Vector((0.9, Y_TELA - 0.05, 1.3)), 14)
pts += [Vector((0.9, Y_TELA - 0.05, z)) for z in (1.0, 0.5, 0.2)]
pts += bezier(Vector((0.9, Y_TELA - 0.05, 0.2)), Vector((0.9, 0.0, Z0 + 0.03)), Vector((0.6, -0.3, Z0 + 0.02)),
              Vector((0.22, -0.78, Z0 + 0.05)), 14)[1:]
mangueira(bm, pts, 0.014)
obj('cabo_anel', bm, 'borracha')
bm = bmesh.new()
for z in (0.5, 1.0):
    caixa(bm, Vector((0.92, Y_TELA - 0.05, z)), (0.06, 0.03, 0.015))
obj('cabo_anel_presilhas', bm, 'aco')

# linhas de campo e névoa em espiral (3 braços) — giram em volta do eixo do anel
piv_esp = bpy.data.objects.new('espiral', None)
sc.collection.objects.link(piv_esp)
piv_esp.location = C_ANEL
piv_esp.rotation_mode = 'XYZ'
Y_INI, Y_FIM = -1.9, Y_TELA - 0.07


def espiral(s, fase):
    """Ponto do braço na fração s (0 longe → 1 na tela), relativo ao centro do anel."""
    y = Y_INI + (Y_FIM - Y_INI) * s
    r = 1.15 * (1 - s) ** 1.3 + 0.5 * s
    a = fase + 2 * PI * 1.35 * s
    return Vector((r * math.cos(a), y - C_ANEL.y, r * math.sin(a) * 0.85))


for k in range(3):
    fase = k * 2 * PI / 3
    n = 60
    pts = [espiral(i / n, fase) for i in range(n + 1)]
    raios = [0.03 + 0.17 * math.sin(PI * min(1, i / n * 1.1)) ** 0.7 * (1 - 0.4 * i / n) for i in range(n + 1)]
    for i in range(34):                                                   # bolhas alongadas ao longo do braço
        sv = min(max((i + random.uniform(-0.3, 0.3)) / 33, 0.0), 1.0)
        c = espiral(sv, fase + random.uniform(-0.05, 0.05))
        t = (espiral(min(1, sv + 0.01), fase) - espiral(max(0, sv - 0.01), fase)).normalized()
        rp = 0.06 + 0.15 * math.sin(PI * min(1.0, sv * 1.1)) ** 0.7 * (1 - 0.35 * sv)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        o = obj('nevoa_b%d_%d' % (k, i), bm, 'nevoa', piv_esp)
        o.location = c
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = t.to_track_quat('Z', 'Y')
        o.scale = (rp, rp * 0.8, rp * random.uniform(2.0, 2.8))
    bm = bmesh.new()
    for j in range(2):
        fj = fase + (j - 0.5) * 0.22
        pts = [espiral(0.3 + 0.7 * i / 50, fj) * (1 + 0.05 * (j - 0.5)) for i in range(51)]
        tubo_curvo(bm, pts, [0.0018] * 51, 6)
    obj('campo_linhas%d' % k, bm, 'campo', piv_esp)
# leque de névoa espalhando na frente das telas (onde os braços chegam)
for i, (lx, lz) in enumerate(((-0.42, 0.25), (0.42, 0.25), (-0.42, -0.25), (0.42, -0.25), (0.0, 0.0))):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    o = obj('nevoa_leque%d' % i, bm, 'nevoa', piv_esp)
    o.location = (lx, Y_TELA - 0.1 - C_ANEL.y, lz)
    o.scale = (0.42, 0.07, 0.36)

# ------------------------------------------------------------------ tanque com visor, escotilha, bomba e saída
bm, bp = bmesh.new(), bmesh.new()
cil(bm, Vector((TQ.x, TQ.y, (Z_TQ0 + Z_TQ1) / 2)), R_TQ, Z_TQ1 - Z_TQ0, lados=40)
esfera(bm, Vector((TQ.x, TQ.y, Z_TQ1)), R_TQ, 40, (1, 1, 0.22))
esfera(bm, Vector((TQ.x, TQ.y, Z_TQ0)), R_TQ, 40, (1, 1, 0.12))
suavizar(obj('tanque', bm, 'amarelo'))
for z in (Z_TQ0 + 0.04, (Z_TQ0 + Z_TQ1) / 2, Z_TQ1 - 0.02):                          # cintas rebitadas
    toro(bp, Vector((TQ.x, TQ.y, z)), R_TQ + 0.004, 0.008, Z, nR=48, nr=6)
obj('tanque_cintas', bp, 'ferro')
bp = bmesh.new()
for z in (Z_TQ0 + 0.04, (Z_TQ0 + Z_TQ1) / 2, Z_TQ1 - 0.02):
    for i in range(24):
        a = i * 2 * PI / 24
        gota(bp, Vector((TQ.x + math.cos(a) * (R_TQ + 0.012), TQ.y + math.sin(a) * (R_TQ + 0.012), z)), 0.006, 6)
obj('tanque_rebites', bp, 'aco')
bm = bmesh.new()                                                                  # pés
for i in range(4):
    a = i * PI / 2 + PI / 4
    p = Vector((TQ.x + math.cos(a) * (R_TQ - 0.06), TQ.y + math.sin(a) * (R_TQ - 0.06), 0))
    caixa_de(bm, (p.x - 0.03, p.y - 0.03, Z0), (p.x + 0.03, p.y + 0.03, Z_TQ0 + 0.02))
    caixa_de(bm, (p.x - 0.05, p.y - 0.05, Z0), (p.x + 0.05, p.y + 0.05, Z0 + 0.012))
obj('tanque_pes', bm, 'grafite')
# bocal de entrada no tampo
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cil(bm, Vector((-0.6, -0.4, 0.6)), 0.04, 0.04, lados=20)
flange(bf, bp, Vector((-0.6, -0.4, 0.625)), Z, 0.055, 0.014)
# respiro com chapéu
tubo(bm, Vector((-0.4, -0.35, 0.58)), Vector((-0.4, -0.35, 0.74)), 0.012, 12)
cil(bm, Vector((-0.4, -0.35, 0.76)), 0.035, 0.02, lados=16, r2=0.005)
obj('tanque_bocais', bm, 'cano')
obj('tanque_bocais_fl', bf, 'ferro')
obj('tanque_bocais_par', bp, 'aco')
# visor de nível: tubo de vidro vertical com protetor, água até a metade (lado sudeste)
A_VIS = math.radians(-35)
dv = Vector((math.cos(A_VIS), math.sin(A_VIS), 0))
pv = Vector((TQ.x, TQ.y, 0)) + dv * (R_TQ + 0.06)
bm, bv, bw = bmesh.new(), bmesh.new(), bmesh.new()
for z in (Z_TQ0 + 0.05, Z_TQ1 - 0.04):
    tubo(bm, Vector((TQ.x, TQ.y, z)) + dv * (R_TQ - 0.01), Vector((pv.x, pv.y, z)), 0.012, 10)
    cil(bm, Vector((pv.x, pv.y, z)), 0.022, 0.04, lados=12)
tubo_oco(bv, Vector((pv.x, pv.y, (Z_TQ0 + Z_TQ1) / 2)), 0.016, 0.011, Z_TQ1 - Z_TQ0 - 0.13, Z, lados=20)
Z_NIVEL = Z_TQ0 + 0.21
cil(bw, Vector((pv.x, pv.y, (Z_TQ0 + 0.07 + Z_NIVEL) / 2)), 0.0105, Z_NIVEL - Z_TQ0 - 0.07, lados=16)
for s in (-1, 1):                                                                # protetor (2 barras)
    off = dv.cross(Z) * 0.026 * s
    tubo(bm, Vector((pv.x, pv.y, Z_TQ0 + 0.06)) + off, Vector((pv.x, pv.y, Z_TQ1 - 0.05)) + off, 0.004, 6)
obj('visor_corpo', bm, 'cromo')
obj('visor_vidro', bv, 'vidro')
obj('visor_agua', bw, 'agua_calha')
# escotilha de vidro (porthole) olhando para o sul, com água atrás
A_ESC = math.radians(-100)
de = Vector((math.cos(A_ESC), math.sin(A_ESC), 0))
pe = Vector((TQ.x, TQ.y, 0.3)) + de * (R_TQ + 0.005)
bm, bp, bv = bmesh.new(), bmesh.new(), bmesh.new()
toro(bm, pe, 0.075, 0.016, de, nR=32, nr=8)
for i in range(8):
    a = i * 2 * PI / 8
    u, v, _ = base_de(de)
    cil(bp, pe + (u * math.cos(a) + v * math.sin(a)) * 0.075 + de * 0.016, 0.007, 0.012, de, lados=6)
cil(bv, pe, 0.068, 0.012, de, lados=32)
obj('escotilha', bm, 'ferro')
obj('escotilha_paraf', bp, 'aco')
obj('escotilha_vidro', bv, 'vidro')
# água vista pela escotilha: disco escuro esverdeado logo atrás do vidro
bw = bmesh.new()
cil(bw, pe - de * 0.012, 0.066, 0.004, de, lados=32)
obj('escotilha_agua', bw, 'agua_calha')
manometro(Vector((TQ.x, TQ.y, Z_TQ1 + 0.04)) + Vector((0.13, 0.05, 0)), Z, Vector((0.6, -0.8, 0)))

# bomba centrífuga: caracol (eixo x), motor a oeste, sucção pela boca leste, recalque tangente para o sul
bm, bp, bmot = bmesh.new(), bmesh.new(), bmesh.new()
cil(bm, BOMBA, 0.1, 0.08, X, lados=32)
cil(bm, BOMBA + Vector((0.055, 0, 0)), 0.04, 0.04, X, lados=20)                       # boca de sucção
caixa_de(bm, (BOMBA.x - 0.04, BOMBA.y - 0.14, BOMBA.z + 0.04), (BOMBA.x + 0.04, BOMBA.y - 0.0, BOMBA.z + 0.1))  # voluta
caixa_de(bm, (BOMBA.x - 0.38, BOMBA.y - 0.1, Z0), (BOMBA.x + 0.08, BOMBA.y + 0.1, Z0 + 0.03))    # base
caixa_de(bm, (BOMBA.x - 0.06, BOMBA.y - 0.05, Z0 + 0.03), (BOMBA.x + 0.04, BOMBA.y + 0.05, BOMBA.z - 0.08))
obj('bomba', bm, 'ferro')
for i in range(10):
    a = i * 2 * PI / 10
    cil(bp, BOMBA + Vector((0.04, math.cos(a) * 0.088, math.sin(a) * 0.088)), 0.006, 0.014, X, lados=6)
obj('bomba_paraf', bp, 'aco')
cil(bmot, BOMBA + Vector((-0.2, 0, 0)), 0.08, 0.22, X, lados=24)
for i in range(12):
    a = i * 2 * PI / 12
    caixa(bmot, BOMBA + Vector((-0.2, math.cos(a) * 0.084, math.sin(a) * 0.084)), (0.2, 0.01, 0.01),
          Matrix.Rotation(a, 3, 'X'))
cil(bmot, BOMBA + Vector((-0.32, 0, 0)), 0.06, 0.03, X, lados=20)                    # tampa do ventilador
caixa(bmot, BOMBA + Vector((-0.2, 0, 0.1)), (0.08, 0.07, 0.05))                       # caixa de ligação
caixa_de(bmot, (BOMBA.x - 0.29, BOMBA.y - 0.07, Z0 + 0.03), (BOMBA.x - 0.11, BOMBA.y + 0.07, BOMBA.z - 0.06))
suavizar(obj('bomba_motor', bmot, 'primer'))
bm = bmesh.new()
cil(bm, BOMBA + Vector((-0.07, 0, 0)), 0.018, 0.06, X, lados=12)                      # eixo exposto (gira)
obj('bomba_eixo', bm, 'cromo')
# sucção: do pé do tanque até a boca leste
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
A_SUC = math.radians(-60)
ps = Vector((TQ.x, TQ.y, BOMBA.z)) + Vector((math.cos(A_SUC), math.sin(A_SUC), 0)) * (R_TQ - 0.01)
cano(bm, bf, bp, [ps, Vector((ps.x, BOMBA.y, BOMBA.z)), BOMBA + Vector((0.075, 0, 0))], 0.03, fl_pontas=False)
# recalque: sai da voluta para o sul até a borda (flange de saída do jogo)
cano(bm, bf, bp, [Vector((BOMBA.x, BOMBA.y - 0.13, Z_SAIDA)), Vector((BOMBA.x, -0.955, Z_SAIDA))], 0.034, fl_pontas=False)
flange(bf, bp, Vector((BOMBA.x, -0.965, Z_SAIDA)), Y, 0.07, 0.022, 8)
suavizar(obj('canos_bomba', bm, 'cano'))
obj('canos_bomba_fl', bf, 'ferro')
obj('canos_bomba_par', bp, 'aco')
# válvula de retenção + válvula com atuador elétrico no recalque
bm = bmesh.new()
caixa(bm, Vector((BOMBA.x, -0.88, Z_SAIDA)), (0.09, 0.06, 0.09))
caixa(bm, Vector((BOMBA.x, -0.88, Z_SAIDA + 0.09)), (0.07, 0.07, 0.08))
cil(bm, Vector((BOMBA.x, -0.88, Z_SAIDA + 0.06)), 0.012, 0.04, lados=10)
obj('valvula_atuador', bm, 'grafite')
bl = bmesh.new()
cil(bl, Vector((BOMBA.x + 0.036, -0.88, Z_SAIDA + 0.1)), 0.008, 0.006, X, lados=10)
obj('valvula_luz', bl, 'verde')
manometro(Vector((BOMBA.x, -0.92, Z_SAIDA + 0.034)), Z, Vector((0.5, -1, 0)))
PINGO_BOMBA = BOMBA + Vector((0.08, 0, -0.04))

# ------------------------------------------------------------------ compressor, linhas frigoríficas, radiador
bm, bp = bmesh.new(), bmesh.new()
caixa_de(bm, (COMP.x - 0.24, COMP.y - 0.2, Z0), (COMP.x + 0.24, COMP.y + 0.2, Z0 + 0.03))   # base em trilhos
for sy in (-1, 1):
    caixa_de(bm, (COMP.x - 0.24, COMP.y + sy * 0.17 - 0.02, Z0 + 0.03), (COMP.x + 0.24, COMP.y + sy * 0.17 + 0.02, Z0 + 0.06))
obj('comp_base', bm, 'grafite')
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(bp, Vector((COMP.x + sx * 0.13, COMP.y + sy * 0.17, Z0 + 0.075)), 0.025, 0.03, lados=12)   # coxins
obj('comp_coxins', bp, 'borracha')
bm = bmesh.new()
cil(bm, Vector((COMP.x, COMP.y, 0.3)), 0.17, 0.36, lados=40)
esfera(bm, Vector((COMP.x, COMP.y, 0.48)), 0.17, 40, (1, 1, 0.55))
esfera(bm, Vector((COMP.x, COMP.y, 0.12)), 0.17, 40, (1, 1, 0.3))
for sx in (-1, 1):
    caixa_de(bm, (COMP.x + sx * 0.13 - 0.03, COMP.y - 0.2, Z0 + 0.09), (COMP.x + sx * 0.13 + 0.03, COMP.y + 0.2, Z0 + 0.11))
suavizar(obj('compressor', bm, 'grafite'))
bm = bmesh.new()
caixa(bm, Vector((COMP.x - 0.17, COMP.y, 0.33)), (0.06, 0.11, 0.12))                     # caixa de terminais
obj('comp_terminais', bm, 'ferro')
bm = bmesh.new()                                                                         # acumulador de sucção
cil(bm, Vector((COMP.x + 0.0, COMP.y + 0.26, 0.28)), 0.05, 0.26, lados=20)
esfera(bm, Vector((COMP.x, COMP.y + 0.26, 0.41)), 0.05, 20, (1, 1, 0.5))
esfera(bm, Vector((COMP.x, COMP.y + 0.26, 0.15)), 0.05, 20, (1, 1, 0.5))
suavizar(obj('acumulador', bm, 'amarelo'))
# linha de sucção (isolada, com geada): coletor de cima → desce pelo plenum → compressor
SUC = [Vector((0.86, 0.47, ZS[0])), Vector((0.86, 0.47, 0.5)), Vector((0.86, -0.06, 0.5)),
       Vector((COMP.x, -0.06, 0.5)), Vector((COMP.x, COMP.y + 0.26, 0.5)), Vector((COMP.x, COMP.y + 0.26, 0.45))]
bm, bg = bmesh.new(), bmesh.new()
for a, b in zip(SUC, SUC[1:]):
    tubo(bm, a, b, 0.032, 16)
for p in SUC[1:-1]:
    esfera(bm, p, 0.032, 16)
for a, b in zip(SUC[:3], SUC[1:3]):                                                       # geada no trecho mais frio
    d = (b - a)
    t = 0.0
    while t < 1.0:
        L = random.uniform(0.05, 0.14)
        if random.random() < 0.6:
            c = a + d * min(1, t + L / d.length / 2)
            cil(bg, c, 0.036 + random.uniform(0, 0.006), min(L, d.length * (1 - t)), d, lados=12)
        t += L / d.length
suavizar(obj('linha_succao', bm, 'espuma'))
obj('linha_succao_geada', bg, 'gelo')
# linha quente: topo do compressor → radiador (coletor norte)
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [Vector((COMP.x, COMP.y, 0.57)), Vector((COMP.x, COMP.y, 0.85)), Vector((COMP.x, -0.12, 0.85)),
                  Vector((0.88, -0.12, 0.85)), Vector((0.88, -0.12, 0.8))], 0.013, 12, fl=False)
# linha de líquido: radiador (coletor sul, embaixo) → filtro secador → válvula de expansão sob o plenum
cano(bm, bf, bp, [Vector((0.88, -0.9, 0.18)), Vector((0.7, -0.9, 0.18)), Vector((0.7, -0.9, 0.6)),
                  Vector((0.7, 0.32, 0.6)), Vector((0.86, 0.32, 0.6)), Vector((0.86, 0.32, 0.7))], 0.009, 10, fl=False)
tubo(bm, Vector((0.86, 0.32, 0.78)), Vector((0.86, 0.32, ZS[-1])), 0.009, 10)            # sobe até o coletor de baixo
suavizar(obj('linhas_cobre', bm, 'cobre'))
bm = bmesh.new()
cil(bm, Vector((0.7, -0.9, 0.4)), 0.03, 0.18, lados=16)                                  # filtro secador
caixa(bm, Vector((0.86, 0.32, 0.74)), (0.05, 0.05, 0.08))                                # válvula de expansão
cil(bm, Vector((0.86, 0.32, 0.8)), 0.022, 0.03, lados=14)
obj('frigo_pecas', bm, 'cobre')
bm = bmesh.new()
mangueira(bm, bezier((0.885, 0.32, 0.76), (0.92, 0.3, 0.7), (0.92, 0.0, 0.55), (0.88, -0.06, 0.53), 8), 0.004)  # capilar do bulbo
obj('capilar', bm, 'cobre')
manometro(Vector((0.86, -0.06, 0.532)), Z, Vector((-0.4, -1, 0)))
manometro(Vector((COMP.x, -0.12, 0.863)), Z, Vector((-0.4, -1, 0.0)))
# radiador da borda leste: colmeia de aletas, tubos em U nas pontas, ventoinha virada para dentro
RX0, RX1 = 0.84, 0.95
RY0, RY1 = -0.9, -0.12
RZ0, RZ1 = 0.14, 0.86
bm, bf2, bu = bmesh.new(), bmesh.new(), bmesh.new()
for (a, b) in (((RX0, RY0 - 0.03, RZ0), (RX1, RY0, RZ1)), ((RX0, RY1, RZ0), (RX1, RY1 + 0.03, RZ1)),
               ((RX0, RY0 - 0.03, RZ1), (RX1, RY1 + 0.03, RZ1 + 0.02)), ((RX0, RY0 - 0.03, RZ0 - 0.02), (RX1, RY1 + 0.03, RZ0))):
    caixa_de(bm, a, b)
for y in (RY0 + 0.03, RY1 - 0.03):
    caixa_de(bm, (RX0 + 0.02, y - 0.015, Z0), (RX1 - 0.02, y + 0.015, RZ0 - 0.02))
obj('radiador_quadro', bm, 'grafite')
for k in range(70):
    y = RY0 + 0.01 + k * (RY1 - RY0 - 0.02) / 69
    caixa_de(bf2, (RX0 + 0.005, y - 0.0007, RZ0), (RX1 - 0.005, y + 0.0007, RZ1))
obj('radiador_aletas', bf2, 'aluminio')
for k in range(8):
    z = RZ0 + 0.05 + k * 0.09
    for x in (RX0 + 0.03, RX1 - 0.03):
        tubo(bu, Vector((x, RY0 - 0.03, z)), Vector((x, RY1 + 0.03, z)), 0.008, 10)
    for y, s in ((RY0 - 0.03, -1), (RY1 + 0.03, 1)):
        toro(bu, Vector(((RX0 + RX1) / 2, y, z)), 0.025, 0.008, Z, nR=10, nr=8,
             a0=(-PI / 2 if s > 0 else PI / 2), a1=(PI / 2 if s > 0 else 3 * PI / 2))
obj('radiador_tubos', bu, 'cobre')
# ventoinha do radiador (lado de dentro)
CVR = Vector((0.77, (RY0 + RY1) / 2, 0.5))
bm, bp = bmesh.new(), bmesh.new()
tubo_oco(bm, CVR, 0.27, 0.25, 0.1, X, lados=48)
for r in (0.08, 0.16, 0.24):
    toro(bp, CVR + Vector((-0.05, 0, 0)), r, 0.003, X, nR=40, nr=5)
for i in range(12):
    a = i * 2 * PI / 12
    d = Vector((0, math.cos(a), math.sin(a)))
    tubo(bp, CVR + Vector((-0.05, 0, 0)) + d * 0.06, CVR + Vector((-0.05, 0, 0)) + d * 0.25, 0.0025, 5)
cil(bp, CVR + Vector((-0.02, 0, 0)), 0.06, 0.06, X, lados=20)
for i in range(4):                                                                       # suportes da ventoinha
    a = i * PI / 2 + PI / 4
    d = Vector((0, math.cos(a), math.sin(a)))
    viga(bp, CVR + Vector((0.05, 0, 0)) + d * 0.27, Vector((RX0, CVR.y, CVR.z)) + d * 0.3, 0.02)
obj('ventoinha_anel', bm, 'amarelo')
obj('ventoinha_grade', bp, 'aco')
piv_r = bpy.data.objects.new('ventoinha_rotor', None)
sc.collection.objects.link(piv_r)
piv_r.location = CVR + Vector((0.01, 0, 0))
bm = bmesh.new()
for i in range(5):
    a0 = i * 2 * PI / 5
    linhas = []
    for j in range(5):
        t = j / 4
        r = 0.06 + t * 0.17
        passo = math.radians(35 - 15 * t)
        a = a0 + 0.15 * t
        rad = Vector((0, math.cos(a), math.sin(a)))
        tang = Vector((0, -math.sin(a), math.cos(a)))
        corda = 0.09 - 0.02 * t
        p1 = rad * r + (tang * math.cos(passo) + X * math.sin(passo)) * corda / 2
        p2 = rad * r - (tang * math.cos(passo) + X * math.sin(passo)) * corda / 2
        linhas.append((bm.verts.new(p1), bm.verts.new(p2)))
    for (a1, b1), (a2, b2) in zip(linhas, linhas[1:]):
        bm.faces.new((a1, b1, b2, a2))
pr = obj('ventoinha_pas', bm, 'grafite', piv_r)
pr.modifiers.new('esp', 'SOLIDIFY').thickness = 0.004

# ------------------------------------------------------------------ armário elétrico (80 kW), sensores, cabos
bm, bp, bl = bmesh.new(), bmesh.new(), bmesh.new()
AR0, AR1 = Vector((-0.12, -0.95, Z0)), Vector((0.22, -0.7, 0.82))
caixa_de(bm, AR0, AR1)
for k in range(7):
    caixa_de(bm, (-0.1, -0.93 + k * 0.034, 0.82), (0.2, -0.92 + k * 0.034, 0.87))              # aletas de calor
caixa_de(bm, (-0.14, -0.97, Z0), (0.24, -0.68, Z0 + 0.05))                                     # pedestal
obj('armario', bm, 'grafite')
caixa_de(bp, (-0.08, -0.956, 0.25), (0.18, -0.95, 0.45))                                       # grelha
parafusos_linha(bp, (-0.1, -0.956, 0.78), (0.2, -0.956, 0.78), 6, Y, 0.005, 0.01)
parafusos_linha(bp, (-0.1, -0.956, 0.12), (0.2, -0.956, 0.12), 6, Y, 0.005, 0.01)
caixa_de(bp, (0.0, -0.957, 0.55), (0.1, -0.951, 0.6))                                          # plaqueta (número apagado)
obj('armario_det', bp, 'ferro')
for k in range(4):
    cil(bl, Vector((-0.06 + k * 0.06, -0.954, 0.7)), 0.013, 0.008, Y, lados=12)
obj('armario_luzes', bl, 'lampada')
bl = bmesh.new()
cil(bl, Vector((0.18, -0.954, 0.7)), 0.013, 0.008, Y, lados=12)
obj('armario_luz_ok', bl, 'verde')
# remendo de outra cor no armário + fiação exposta saindo por um rasgo
bm = bmesh.new()
caixa_de(bm, (0.222, -0.9, 0.3), (0.228, -0.76, 0.5))
obj('armario_remendo', bm, 'galv')
bc = bmesh.new()
for k, cor_dy in enumerate((0.0, 0.012, 0.024)):
    pts = bezier((0.225, -0.88 + cor_dy, 0.55), (0.29, -0.88 + cor_dy, 0.56), (0.3, -0.84, 0.42), (COMP.x - 0.2, COMP.y, 0.33), 12)
    mangueira(bc, pts, 0.006)
# cabo de alimentação blindado saindo do chão na borda sul
pts = bezier((0.12, -0.99, Z0 - 0.02), (0.12, -0.99, 0.2), (0.12, -0.96, 0.2), (0.12, -0.92, Z0 + 0.06), 10)
mangueira(bc, pts, 0.022)
# cabo para a eletrocalha norte (passa por baixo de tudo, na valeta lateral oeste do armário)
pts = bezier((-0.12, -0.8, 0.2), (-0.2, -0.8, Z0 + 0.02), (-0.2, -0.1, Z0 + 0.02), (-0.2, 0.3, Z0 + 0.02), 14)
pts += bezier(Vector((-0.2, 0.3, Z0 + 0.02)), Vector((-0.2, 0.8, Z0 + 0.02)), Vector((-0.1, 0.92, 0.1)), Vector((-0.1, 0.93, 0.27)), 10)[1:]
mangueira(bc, pts, 0.016)
# ventoinha do radiador
pts = bezier((0.22, -0.85, 0.6), (0.4, -0.85, 0.75), (0.7, -0.75, 0.8), (0.77, CVR.y, 0.5 + 0.08), 12)
mangueira(bc, pts, 0.008)
# bomba
pts = bezier((-0.12, -0.75, 0.3), (-0.3, -0.75, 0.4), (-0.6, -0.75, 0.4), (BOMBA.x - 0.2, BOMBA.y, BOMBA.z + 0.125), 12)
mangueira(bc, pts, 0.009)
obj('cabos', bc, 'borracha')
bm = bmesh.new()
for p in ((-0.2, -0.5), (-0.2, 0.0), (-0.2, 0.5)):
    caixa(bm, Vector((p[0], p[1], Z0 + 0.025)), (0.06, 0.03, 0.012))
obj('presilhas_chao', bm, 'aco')

# sensor de umidade (para a IA): mastro, abrigo de pratos empilhados, antena e luz
SX = Vector((-0.9, -0.08, 0))
bm, bp = bmesh.new(), bmesh.new()
tubo(bm, Vector((SX.x, SX.y, Z0)), Vector((SX.x, SX.y, 1.32)), 0.018, 12)
caixa_de(bm, (SX.x - 0.05, SX.y - 0.05, Z0), (SX.x + 0.05, SX.y + 0.05, Z0 + 0.012))
for k in range(7):
    cil(bp, Vector((SX.x, SX.y, 1.12 + k * 0.025)), 0.07 - k * 0.002, 0.008, lados=24, r2=0.05)
cil(bp, Vector((SX.x, SX.y, 1.3)), 0.075, 0.012, lados=24)
tubo(bm, Vector((SX.x, SX.y, 1.32)), Vector((SX.x, SX.y, 1.62)), 0.004, 6)
obj('sensor_mastro', bm, 'aco')
obj('sensor_pratos', bp, 'mostrador')
bl = bmesh.new()
esfera(bl, Vector((SX.x, SX.y, 1.625)), 0.012, 10)
obj('sensor_luz', bl, 'lampada')
bm = bmesh.new()
pts = bezier((SX.x + 0.02, SX.y, 1.0), (SX.x + 0.03, SX.y, 0.4), (SX.x + 0.03, SX.y - 0.05, Z0 + 0.02), (-0.2, -0.3, Z0 + 0.02), 12)
mangueira(bm, pts, 0.006)
obj('sensor_cabo', bm, 'borracha')

obj('manometros', GM, 'cromo')
obj('manometros_face', GF, 'mostrador')
obj('manometros_ponteiro', GP, 'ponteiro')

# ------------------------------------------------------------------ desgaste: poças, limo nos pés, escorridos
bm = bmesh.new()
for c, r in (((-0.8, 0.0), 0.16), ((-0.55, -0.0), 0.1), ((0.0, -0.12), 0.14), ((0.35, -0.08), 0.1),
             ((-0.35, -0.85), 0.11), ((PINGO_BOMBA.x, PINGO_BOMBA.y), 0.08), ((-0.75, 0.55), 0.12), ((0.5, 0.45), 0.1),
             ((0.0, 0.4), 0.13)):
    mancha(bm, c, r, Z0 + 0.0015)
obj('pocas', bm, 'poca')
bm = bmesh.new()
for x in XP:
    mancha(bm, (x, Y_TELA), 0.1, Z0 + 0.001)
for k in range(12):
    mancha(bm, (random.uniform(-0.9, 0.9), random.uniform(-0.25, 0.08)), random.uniform(0.03, 0.08), Z0 + 0.0012)
obj('limo_chao', bm, 'limo')
bm = bmesh.new()
for c, r in (((COMP.x + 0.1, COMP.y - 0.1), 0.09), ((BOMBA.x - 0.2, BOMBA.y), 0.08)):
    mancha(bm, c, r, Z0 + 0.0018)
obj('oleo_chao', bm, 'oleo')
# escorridos: placas finas encostadas (ferrugem sob rebites, limo no pé dos postes e da tela)
bm, bl = bmesh.new(), bmesh.new()
for x in XP:
    for s in (-1, 1):
        caixa_de(bl, (x - 0.025, Y_TELA + s * 0.031 - 0.0005, Z0), (x + 0.025, Y_TELA + s * 0.031 + 0.0005, Z0 + 0.35))
for x in (-0.6, -0.2, 0.2, 0.6, 0.85):                                                   # parede dos ventiladores
    caixa_de(bm, (x - 0.02, Y_PAR + 0.0125, 0.9), (x + 0.02, Y_PAR + 0.0135, 1.7 - abs(x) * 0.3))
for y in (0.3, 0.5):                                                                     # laterais
    caixa_de(bm, (-0.9665, y - 0.025, 1.0), (-0.9655, y + 0.025, 2.05))
    caixa_de(bm, (0.9655, y - 0.025, 1.1), (0.9665, y + 0.025, 2.05))
for a in (0.4, 1.9, 3.3, 4.6):                                                           # tanque
    d = Vector((math.cos(a), math.sin(a), 0))
    p = Vector((TQ.x, TQ.y, 0)) + d * (R_TQ + 0.0015)
    rot = Matrix.Rotation(a, 3, 'Z')
    caixa(bm, Vector((p.x, p.y, (Z_TQ0 + Z_TQ1) / 2 - 0.05)), (0.001, 0.05, 0.32), rot)
obj('escorrido_ferrugem', bm, 'escorre_ferr')
obj('escorrido_limo', bl, 'escorre_limo')

# ------------------------------------------------------------------ partes animadas: gotas caindo, respingos, névoa fria
FONTES = [  # (início, z do chão/alvo, período em quadros, fase)
    (Vector((0.0, Y_TELA, z_calha(0.0) - 0.07)), Z0 + 0.002, 20, 0),          # calha furada na emenda
    (Vector((-0.5, Y_TELA, z_calha(-0.5) - 0.07)), Z0 + 0.002, 32, 7),        # outra emenda
    (BICA + Vector((0, -0.01, -0.02)), z_calha(0.3) - 0.055, 12, 3),           # bica da bandeja → calha
    (PINGO_BOMBA, Z0 + 0.002, 28, 11),                                         # flange da bomba
    (Vector((-0.8, Y_TELA, 0.67)), Z0 + 0.002, 40, 19),                        # junta da coletora
]
for p in SINCELOS[:8]:
    FONTES.append((p, z_calha(p.x) - 0.055, random.choice((24, 32, 48)), random.randint(0, 40)))
gotas = []
for k, (p, zc, per, fase) in enumerate(FONTES):
    bm = bmesh.new()
    esfera(bm, (0, 0, 0), 0.006, 10, (1, 1, 1.6))
    g = obj('pingo%d' % k, bm, 'agua')
    bm = bmesh.new()
    toro(bm, (0, 0, 0), 1.0, 0.08, Z, nR=24, nr=5)
    rp = obj('respingo%d' % k, bm, 'agua')
    gotas.append((g, rp, p, zc, per, fase))
# gotas escorrendo na malha (descem devagar e somem na borda de baixo)
corredoras = []
for k in range(24):
    x0, x1 = PAINEIS[k % 2]
    bm = bmesh.new()
    esfera(bm, (0, 0, 0), random.uniform(0.004, 0.006), 10, (0.9, 0.7, 1.6))
    o = obj('escorre%d' % k, bm, 'agua')
    corredoras.append((o, random.uniform(x0 + 0.05, x1 - 0.05), random.uniform(ZT0 + 0.2, ZT1 - 0.05),
                       random.choice((-1, 1)), random.random()))
# névoa fria caindo da bandeja (bolhas de volume que descem e crescem)
frias = []
for k in range(5):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    o = obj('nevoa_fria%d' % k, bm, 'nevoa_fria')
    frias.append((o, -0.7 + k * 0.35, k / 5))
# névoa de chão: caixa grande
bm = bmesh.new()
caixa_de(bm, (-4.5, -4.5, -0.05), (4.5, 4.5, 2.5))
obj('neblina_chao', bm, 'nevoa_chao')

cristal_em = M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
campo_forca = M['campo'].node_tree.nodes['forca'].inputs[1]
luzes_em = []
for i, q in enumerate(EMISSORES[::2]):
    ld = bpy.data.lights.new('luz_cristal%d' % i, 'POINT')
    ld.color = VIOLETA
    ld.shadow_soft_size = 0.03
    lo = bpy.data.objects.new('luz_cristal%d' % i, ld)
    sc.collection.objects.link(lo)
    lo.location = q
    luzes_em.append(ld)

print('GEOMETRIA ok', flush=True)
FR_FOTO = int(QUADROS * 0.35) + 1
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for k, piv in enumerate(rotores):
        piv.rotation_euler = (0, 2 * PI * (10 + k) * fr, 0)
        piv.keyframe_insert('rotation_euler', frame=q)
    piv_r.rotation_euler = (2 * PI * 14 * fr, 0, 0)
    piv_r.keyframe_insert('rotation_euler', frame=q)
    piv_esp.rotation_euler = (0, -2 * PI / 3 * fr, 0)                     # 1/3 de volta: o laço fecha (3 braços)
    piv_esp.keyframe_insert('rotation_euler', frame=q)
    pulso = 0.8 + 0.2 * math.sin(2 * PI * 4 * fr)
    cristal_em.default_value = 3.0 * pulso
    cristal_em.keyframe_insert('default_value', frame=q)
    campo_forca.default_value = 3.0 * pulso
    campo_forca.keyframe_insert('default_value', frame=q)
    for ld in luzes_em:
        ld.energy = 1.2 * pulso
        ld.keyframe_insert('energy', frame=q)
    for g, rp, p, zc, per, fase in gotas:
        t_q = ((q - 1 + fase) % per)                                        # quadros desde que soltou
        queda = math.sqrt(2 * max(0.001, p.z - zc) / 9.8) * FPS              # quadros até bater
        if t_q < queda:
            tt = t_q / FPS
            g.location = (p.x, p.y, p.z - 4.9 * tt * tt)
            g.scale = (1, 1, 1 + min(1.5, tt * 6))
            g.hide_render = False
            rp.hide_render = True
            rp.scale = (0.001, 0.001, 0.001)
        else:
            g.location = p
            g.scale = (0.7, 0.7, 0.7)                                        # gota nova se formando na ponta
            u = (t_q - queda) / 6.0
            rp.hide_render = u > 1
            rs = 0.005 + 0.04 * min(u, 1)
            rp.scale = (rs, rs, 0.04)
            rp.location = (p.x, p.y, zc + 0.002)
        for o, cs in ((g, ('location', 'scale', 'hide_render')), (rp, ('location', 'scale', 'hide_render'))):
            for c in cs:
                o.keyframe_insert(c, frame=q)
    for o, x, z0, lado, ph in corredoras:
        u = (ph + fr) % 1.0
        o.location = (x + 0.004 * math.sin(u * 30 + ph * 9), Y_TELA + lado * 0.0065, z0 - (z0 - ZT0) * u)
        o.keyframe_insert('location', frame=q)
    for o, x, ph in frias:
        u = (ph + fr) % 1.0
        o.location = (x + 0.05 * math.sin(u * 5 + x * 7), 0.2 - 0.04 * u, Z_PISO - 0.05 - 0.45 * u)
        s = 0.06 + 0.14 * u
        o.scale = (s * 1.4, s * 0.8, s * 0.7)
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR' if fc.data_path != 'hide_render' else 'CONSTANT'

print('ANIMACAO ok', flush=True)
# ------------------------------------------------------------------ cena: luz, céu, câmera
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.0
sol.angle = math.radians(6)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-30))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bgn = mundo.node_tree.nodes['Background']
bgn.inputs['Color'].default_value = (0.6, 0.64, 0.7, 1)
bgn.inputs['Strength'].default_value = 0.7
bm = bmesh.new()                                                             # chão em volta (terra úmida)
caixa_de(bm, (-8, -8, -0.02), (8, 8, 0.0))
obj('chao', bm, 'lama')
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
sc.cycles.max_bounces = 12
sc.cycles.transmission_bounces = 12
sc.cycles.transparent_max_bounces = 32
sc.cycles.volume_bounces = 1
sc.cycles.volume_step_rate = 4.0
sc.cycles.volume_max_steps = 256
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.3
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, -0.2, 1.0)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 160
    sc.frame_set(FR_FOTO)
    if so_uma in (None, '0'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
        mirar((2.2, -4.7, 2.4), (0.0, -0.1, 0.95), 32)
        sc.render.filepath = os.path.join(AQUI, 'condensador_0.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((0.34, -0.3, 1.42), (0.08, 0.12, 0.93), 26)
        sc.render.filepath = os.path.join(AQUI, 'condensador_perto.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 900, 760
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'condensador_teste.png')
    bpy.ops.render.render(write_still=True)
print('CONDENSADOR ok', flush=True)
