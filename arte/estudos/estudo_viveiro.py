"""Estudo isolado (fora do jogo): VIVEIRO, o reflorestamento da IA, 2×2 tiles. Seiva entra por cano no tile oeste da
borda oeste (O0). Partes: antena, pistao0, pistao1.
A IA polui; o viveiro compensa: transforma seiva em mudas dentro de cápsulas-dardo e as crava no chão em volta.
- Estufa de aço gasto (pilares, tesouras, terças, mãos-francesas rebitadas, beiral amarelo lascado) com painéis de vidro
  sujos e embaçados por condensação; alguns trincados com só um caco no caixilho, um faltando; cacos no chão.
- Tanque de seiva (sudoeste) com visor âmbar borbulhando; o cano vem da boca O0, atravessa a chapa de rodapé por um
  colar e entra no tanque. Vazamento de seiva na flange.
- Estação de dosagem (oeste): armário com duas dosadoras de êmbolo; cada uma é empurrada por um pistão (pistao0, pistao1:
  camisa presa no suporte do armário, haste na cruzeta que empurra o êmbolo). Mangueiras sobem até a lança, que tem o
  magazine de cápsulas vazias (tubo de vidro) e dois bicos: seiva (âmbar) e gel de semente (verde).
- Carrossel de bandejas (6, girando no sentido horário sobre trilho circular com roletes, coroa dentada e motor): a
  bandeja recebe a cápsula sob o magazine, é dosada, passa pelo CAMPO DE CRESCIMENTO (arco de emissores violeta sobre
  dois pilones: névoa luminosa, sementes flutuando) onde a muda cresce rápido demais, e chega ao leste.
- Braço plantador elétrico (leste, fora do vidro): pega a cápsula com a muda, gira, arma e lança; a cápsula voa ponta à
  frente e se crava no chão lá fora (torrões espirram). Mudas e árvores jovens já plantadas em volta, cada uma com a
  cápsula gasta no pé.
- Aspersores girando sob a cumeeira (alimentados do tanque) com névoa e gotas; barras de luz de crescimento magenta
  (uma pisca, defeito); antena de sensores girando no topo.
- Raízes saindo por rachaduras da laje e escorrendo pela borda, musgo, terra derramada, poça.
Animação (laço de 4 s): carrossel avança uma estação (0–1,2 s); cápsula cai do magazine; dosadoras bombeiam; mudas
crescem conforme a idade; braço pega (≈1,7 s), arma e lança (≈3 s); cápsula voa e se crava (≈3,5 s).
Uso: blender -b --python estudo_viveiro.py -- foto [0|1|2|3|perto]
     blender -b --python estudo_viveiro.py -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(47)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3), a0=0.0, a1=2 * PI):
    """Anel tubular (ou arco de a0 a a1) no plano xy local girado por `rot`."""
    fechado = abs(a1 - a0 - 2 * PI) < 1e-6
    n = nR if fechado else nR + 1
    aneis = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B_ = aneis[i], aneis[(i + 1) % n]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B_[(j + 1) % nr], B_[j]))


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.16:
            for c in (a + u * 0.05, b - u * 0.05):
                tubo(bf, c - u * 0.008, c + u * 0.008, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def feixe(bc, ba, pts, lat, n=3, r=0.008, passo=4):
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.008, pts[j] + u * 0.008, r * (n + 0.8), 10)


def raiz(bm, pts, r0, r1):
    """Raiz afinando de r0 a r1, com nós arredondados."""
    pts = [Vector(p) for p in pts]
    n = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        r = r0 + (r1 - r0) * i / n
        u = (b - a).normalized()
        tubo(bm, a - u * r * 0.4, b + u * r * 0.4, r, 7)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r * 1.05, matrix=Matrix.Translation(b))


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def rebites(bm, a, b, n, off=Vector((0, 0, 0)), r=0.0055):
    a, b = Vector(a), Vector(b)
    for i in range(n):
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r,
                                   matrix=Matrix.Translation(a.lerp(b, (i + 0.5) / n) + off))


BMS = {}


def B(nome, mat, liso=False):
    k = (nome, mat, liso)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def liquido_mat(nome, cor, forca=0.0, transm=0.7):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.4
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_sujo_mat(nome, sujo=1.0):
    """Vidro velho de estufa: transparente (sombra correta), embaçado pela condensação em manchas, gotas (voronoi),
    sujeira e escorridos verticais mais fortes embaixo; reflexo especular nas bordas (fresnel)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    geo = no(nt, 'ShaderNodeNewGeometry')
    nevoa = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.5, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], nevoa.inputs['Vector'])
    esc = no(nt, 'ShaderNodeMapping')                                  # escorridos: ruído esticado na vertical
    esc.inputs['Scale'].default_value = (28.0, 28.0, 2.0)
    nt.links.new(geo.outputs['Position'], esc.inputs['Vector'])
    escn = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 3.0})
    nt.links.new(esc.outputs['Vector'], escn.inputs['Vector'])
    gotas = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 140.0})
    nt.links.new(geo.outputs['Position'], gotas.inputs['Vector'])
    gm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.18, 'From Max': 0.32, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(gotas.outputs['Distance'], gm.inputs['Value'])
    fog = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.7, 'To Min': 0.12, 'To Max': 0.5 * sujo})
    nt.links.new(nevoa.outputs['Fac'], fog.inputs['Value'])
    sj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 0.35 * sujo})
    nt.links.new(escn.outputs['Fac'], sj.inputs['Value'])
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.2, 'From Max': 1.1, 'To Min': 0.3 * sujo, 'To Max': 0.0})
    nt.links.new(sep.outputs['Z'], baixo.inputs['Value'])
    s1 = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(fog.outputs['Result'], s1.inputs[0])
    nt.links.new(sj.outputs['Result'], s1.inputs[1])
    s2 = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(s1.outputs['Value'], s2.inputs[0])
    nt.links.new(baixo.outputs['Result'], s2.inputs[1])
    gq = no(nt, 'ShaderNodeMath', operation='MULTIPLY')                # gotas: mais transparentes que a névoa
    gq.inputs[1].default_value = 0.18
    nt.links.new(gm.outputs['Result'], gq.inputs[0])
    opaco = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(s2.outputs['Value'], opaco.inputs[0])
    nt.links.new(gq.outputs['Value'], opaco.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.62, 0.68, 0.64, 1)                 # embaçado
    cor.inputs[7].default_value = (0.16, 0.13, 0.08, 1)                 # sujeira
    nt.links.new(sj.outputs['Result'], cor.inputs[0])
    trans = no(nt, 'ShaderNodeBsdfTransparent')
    trans.inputs['Color'].default_value = (0.86, 0.92, 0.88, 1)
    fosco = no(nt, 'ShaderNodeBsdfPrincipled')
    fosco.inputs['Roughness'].default_value = 0.55
    nt.links.new(cor.outputs[2], fosco.inputs['Base Color'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.12})
    nt.links.new(gm.outputs['Result'], bump.inputs['Height'])
    mix1 = no(nt, 'ShaderNodeMixShader')
    nt.links.new(opaco.outputs['Value'], mix1.inputs[0])
    nt.links.new(trans.outputs[0], mix1.inputs[1])
    nt.links.new(fosco.outputs[0], mix1.inputs[2])
    brilho = no(nt, 'ShaderNodeBsdfGlossy')
    brilho.inputs['Roughness'].default_value = 0.06
    lw = no(nt, 'ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.25
    fr = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    fr.inputs[1].default_value = 0.8
    nt.links.new(lw.outputs['Fresnel'], fr.inputs[0])
    mix2 = no(nt, 'ShaderNodeMixShader')
    nt.links.new(fr.outputs['Value'], mix2.inputs[0])
    nt.links.new(mix1.outputs[0], mix2.inputs[1])
    nt.links.new(brilho.outputs[0], mix2.inputs[2])
    nt.links.new(mix2.outputs[0], out.inputs['Surface'])
    return m


def folha_mat(nome, c1, c2, emis=0.0, bump=0.0):
    """Folha viva: verde saturado variando entre jovem e madura, translúcida contra a luz."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 18.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (*c1, 1)
    cor.inputs[7].default_value = (*c2, 1)
    nt.links.new(mr.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.42
    b.inputs['Emission Color'].default_value = (*c1, 1)
    b.inputs['Emission Strength'].default_value = emis
    if bump:
        bu = no(nt, 'ShaderNodeBump', **{'Strength': bump})
        vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 60.0})
        nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
        nt.links.new(vo.outputs['Distance'], bu.inputs['Height'])
        nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
    tr = no(nt, 'ShaderNodeBsdfTranslucent')
    nt.links.new(cor.outputs[2], tr.inputs['Color'])
    mx = no(nt, 'ShaderNodeMixShader')
    mx.inputs[0].default_value = 0.3
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


C = Vector((0.0, 0.0, 0.0))                                             # centro do carrossel


def campo_cresc_mat():
    """Campo de crescimento: névoa luminosa no setor norte do carrossel, violeta com veios verde-lima; some nas bordas
    do setor (raio, ângulo e altura) para não mostrar a malha."""
    m = bpy.data.materials.new('Campo de crescimento')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.08, 0.04, 0.12, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    sub = no(nt, 'ShaderNodeVectorMath', operation='SUBTRACT')
    sub.inputs[1].default_value = (C.x, C.y, 0.0)
    nt.links.new(geo.outputs['Position'], sub.inputs[0])
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(sub.outputs[0], sep.inputs[0])
    # raio no plano
    x2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(sep.outputs['X'], x2.inputs[0]); nt.links.new(sep.outputs['X'], x2.inputs[1])
    y2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(sep.outputs['Y'], y2.inputs[0]); nt.links.new(sep.outputs['Y'], y2.inputs[1])
    s = no(nt, 'ShaderNodeMath', operation='ADD'); nt.links.new(x2.outputs[0], s.inputs[0]); nt.links.new(y2.outputs[0], s.inputs[1])
    rho = no(nt, 'ShaderNodeMath', operation='SQRT'); nt.links.new(s.outputs[0], rho.inputs[0])
    dr = no(nt, 'ShaderNodeMath', operation='SUBTRACT'); dr.inputs[1].default_value = 0.43
    nt.links.new(rho.outputs[0], dr.inputs[0])
    adr = no(nt, 'ShaderNodeMath', operation='ABSOLUTE'); nt.links.new(dr.outputs[0], adr.inputs[0])
    fr_ = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.2, 'From Max': 0.06}); nt.links.new(adr.outputs[0], fr_.inputs['Value'])
    # ângulo
    at = no(nt, 'ShaderNodeMath', operation='ARCTAN2'); nt.links.new(sep.outputs['Y'], at.inputs[0]); nt.links.new(sep.outputs['X'], at.inputs[1])
    dth = no(nt, 'ShaderNodeMath', operation='SUBTRACT'); dth.inputs[1].default_value = PI / 2
    nt.links.new(at.outputs[0], dth.inputs[0])
    adth = no(nt, 'ShaderNodeMath', operation='ABSOLUTE'); nt.links.new(dth.outputs[0], adth.inputs[0])
    fa = no(nt, 'ShaderNodeMapRange', **{'From Min': math.radians(66), 'From Max': math.radians(40)}); nt.links.new(adth.outputs[0], fa.inputs['Value'])
    # altura
    fz = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 1.0, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sep.outputs['Z'], fz.inputs['Value'])
    fz2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.46, 'From Max': 0.56}); nt.links.new(sep.outputs['Z'], fz2.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    rm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.7, 'To Min': 0.15, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], rm.inputs['Value'])
    mul = rm.outputs['Result']
    for f in (fr_, fa, fz, fz2):
        mm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(mul, mm.inputs[0]); nt.links.new(f.outputs['Result'], mm.inputs[1])
        mul = mm.outputs[0]
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY'); d.inputs[1].default_value = 3.0
    nt.links.new(mul, d.inputs[0]); nt.links.new(d.outputs[0], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca'); e.inputs[1].default_value = 8.0
    nt.links.new(mul, e.inputs[0]); nt.links.new(e.outputs[0], vol.inputs['Emission Strength'])
    veio = no(nt, 'ShaderNodeTexNoise', **{'Scale': 14.0, 'Detail': 2.0})
    nt.links.new(geo.outputs['Position'], veio.inputs['Vector'])
    vm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.62})
    nt.links.new(veio.outputs['Fac'], vm.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.55, 0.2, 1.0, 1)
    cor.inputs[7].default_value = (0.45, 1.0, 0.15, 1)
    nt.links.new(vm.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], vol.inputs['Emission Color'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
SEIVA = (1.0, 0.55, 0.06)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.9, ferrugem=0.4),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.45, pintura=False, ferrugem=0.85, sujeira=0.85, escovado=True),
    'estrutura': mats.material('Aço estrutural', (0.2, 0.2, 0.2), 0.9, 0.6, pintura=False, ferrugem=0.95, sujeira=0.95),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'mang_ambar': mats.material('Mangueira âmbar', (0.5, 0.22, 0.03), 0, 0.5, pintura=False, sujeira=0.7, desgaste=0.0),
    'mang_verde': mats.material('Mangueira verde', (0.08, 0.28, 0.06), 0, 0.5, pintura=False, sujeira=0.7, desgaste=0.0),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'terra': mats.material('Terra', (0.085, 0.055, 0.03), 0, 0.95, pintura=False, sujeira=0.5, desgaste=0.0),
    'terra_seca': mats.material('Terra seca', (0.2, 0.14, 0.09), 0, 0.95, pintura=False, sujeira=0.4, desgaste=0.0),
    'musgo': folha_mat('Musgo', (0.16, 0.42, 0.03), (0.06, 0.2, 0.02), bump=0.6),
    'raiz': mats.material('Raiz', (0.27, 0.17, 0.09), 0, 0.8, pintura=False, sujeira=0.7, desgaste=0.0),
    'caule': mats.material('Caule', (0.16, 0.38, 0.05), 0, 0.5, pintura=False, sujeira=0.2, desgaste=0.0),
    'tronco': mats.material('Tronco', (0.17, 0.11, 0.07), 0, 0.85, pintura=False, sujeira=0.6, desgaste=0.0),
    'folha': folha_mat('Folha', (0.38, 0.85, 0.06), (0.06, 0.48, 0.05), emis=0.06),
    'folha_campo': folha_mat('Folha do campo', (0.55, 1.0, 0.12), (0.12, 0.7, 0.1), emis=0.25),
    'copa': folha_mat('Copa', (0.3, 0.72, 0.05), (0.05, 0.36, 0.04)),
    'vidro': vidro_sujo_mat('Vidro sujo'),
    'caco': vidro_sujo_mat('Caco', 0.5),
    'tubo_vidro': liquido_mat('Tubo de vidro', (0.85, 0.9, 0.88), 0.0, 0.85),
    'seiva': liquido_mat('Seiva', SEIVA, 1.4, 0.5),
    'seiva_poca': liquido_mat('Seiva derramada', (0.55, 0.22, 0.02), 0.15, 0.2),
    'agua': liquido_mat('Água', (0.8, 0.88, 0.92), 0.0, 0.9),
    'poca': liquido_mat('Poça', (0.04, 0.045, 0.04), 0.0, 0.0),
    'gota_seiva': emissivo('Gota de seiva', SEIVA, 6.0),
    'gel': emissivo('Gel de semente', (0.35, 1.0, 0.12), 4.0),
    'bolha': emissivo('Bolha de seiva', (1.0, 0.8, 0.35), 4.0),
    'listras': base3d.listras_mat(),
    'cresce': emissivo('Luz de crescimento', (1.0, 0.22, 0.7), 9.0),
    'cresce_falha': emissivo('Luz de crescimento falhando', (1.0, 0.22, 0.7), 9.0),
    'lente': emissivo('Lente do emissor', VIOLETA, 10.0, (0.1, 0.04, 0.2)),
    'anel_capsula': emissivo('Anel da cápsula', VIOLETA, 4.0),
    'semente': emissivo('Semente', (0.75, 1.0, 0.2), 12.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'olho': emissivo('Olho do sensor', VIOLETA, 8.0, (0.05, 0.02, 0.1)),
    'nevoa': base3d.volume_mat('Névoa', (0.88, 0.92, 0.92), 6.0, 1.15, 0.5),
    'campo': campo_cresc_mat(),
})

# ------------------------------------------------------------------ medidas
Z0 = 0.08                       # topo da laje
AP = 0.82                       # apótema do pavilhão octogonal (centrado no carrossel)
R8 = AP / math.cos(PI / 8)
W8 = 2 * AP * math.tan(PI / 8)  # largura de cada face
ZE = 1.10                       # beiral
Z_TEL0, Z_TEL1 = 1.18, 1.50     # telhado: no beiral e no lanternim
AL = 0.30                       # apótema do lanternim
RL = AL / math.cos(PI / 8)
R_T = 0.42                      # raio das bandejas
Z_BAND = 0.44
Z_TERRA = 0.50
Z_CAP = 0.555
TANQUE = Vector((-0.72, -0.72, 0))
R_TQ = 0.16
PORTA = Vector((-1.0, -0.5, 0.35))     # FLUIDO_ENT_O0
PB = Vector((0.70, -0.70, 0))          # pedestal do braço (canto sudeste, fora do vidro)
ZS = 0.56
L1, L2, LG = 0.46, 0.44, 0.13
ST0 = Vector((C.x - R_T, C.y, 0))      # estação de dosagem (θ = 180°)
FACE_ABERTA = 7                        # face sudeste (315°): sem vidro, o braço entra por ela


def viga_i(bm, a, b, h, w, up, t=0.007):
    """Perfil I de a até b: alma no plano de (b−a, up), mesas perpendiculares a `up`."""
    a, b = Vector(a), Vector(b)
    z = (b - a).normalized()
    y = (Vector(up) - z * Vector(up).dot(z)).normalized()
    x = y.cross(z)
    R = Matrix((x, y, z)).transposed()
    L = (b - a).length
    m = (a + b) / 2
    caixa(bm, m, (t, h, L), R)
    for s in (-1, 1):
        caixa(bm, m + y * s * (h / 2 - t / 2), (w, t, L), R)


def V(a_deg, r=R8, z=0.0):
    a = math.radians(a_deg)
    return Vector((C.x + r * math.cos(a), C.y + r * math.sin(a), z))


def face(k):
    """Face k do octógono (centrada em 45k graus): cantos A, B, normal n, tangente t, centro."""
    phi = math.radians(45 * k)
    n = Vector((math.cos(phi), math.sin(phi), 0))
    t = Vector((-n.y, n.x, 0))
    return V(45 * k - 22.5), V(45 * k + 22.5), n, t, C + n * AP


def z_tel(rho):
    """Altura da linha das tesouras no apótema rho."""
    return Z_TEL0 + (AP - rho) / (AP - AL) * (Z_TEL1 - Z_TEL0)


def pos_estacao(th):
    a = math.radians(th)
    return Vector((C.x + R_T * math.cos(a), C.y + R_T * math.sin(a), 0))


def chapa(bm, k, u0, u1, z0, z1, esp=0.016):
    A, Bv, n, t, Fc = face(k)
    caixa(bm, Fc + t * (u0 + u1) / 2 + Vector((0, 0, (z0 + z1) / 2)), (esp, u1 - u0, z1 - z0),
          Matrix.Rotation(math.radians(45 * k), 3, 'Z'))


def quad(bm, a0, a1, b0, b1, ins=0.026, jag=None):
    """Painel de vidro num quadrilátero (a0→a1 embaixo, b0→b1 em cima), recuado `ins` dos perfis.
    jag: alturas (fração) do caco que sobrou no caixilho."""
    a0, a1, b0, b1 = map(Vector, (a0, a1, b0, b1))
    lu = ((a1 - a0).length + (b1 - b0).length) / 2
    lv = ((b0 - a0).length + (b1 - a1).length) / 2
    u0, v0 = ins / lu, ins / lv
    n = 7 if jag else 1

    def P(u, v):
        return (a0.lerp(a1, u)).lerp(b0.lerp(b1, u), v)
    us = [u0 + (1 - 2 * u0) * i / n for i in range(n + 1)]
    vb = [bm.verts.new(P(u, v0)) for u in us]
    vt = [bm.verts.new(P(u, v0 + (1 - 2 * v0) * (jag[i] if jag else 1))) for i, u in enumerate(us)]
    for i in range(n):
        bm.faces.new((vb[i], vb[i + 1], vt[i + 1], vt[i]))


# ------------------------------------------------------------------ laje, rachaduras, listras
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-0.985, s * 0.985 - 0.012, 0.0), (0.985, s * 0.985 + 0.012, Z0 + 0.002))
    caixa_de(bm, (s * 0.985 - 0.012, -0.985, 0.0), (s * 0.985 + 0.012, 0.985, Z0 + 0.002))
A7, B7, n7, t7, F7 = face(FACE_ABERTA)                                    # soleira listrada da face aberta
caixa(bm, F7 + Vector((0, 0, Z0 + 0.001)), (0.05, W8, 0.002), Matrix.Rotation(math.radians(315), 3, 'Z'))
RACHAS = [((-0.62, 0.62), (-0.78, 0.8), (-0.985, 0.9)), ((-0.6, 0.66), (-0.45, 0.85), (-0.4, 0.985)),
          ((-0.55, 0.55), (-0.35, 0.42)), ((0.1, -0.6), (0.2, -0.8), (0.18, -0.985)), ((0.62, 0.3), (0.85, 0.12), (0.985, 0.15))]
bm = B('rachas', 'escuro')
for pts in RACHAS:
    pts = [Vector((p[0], p[1], Z0 + 0.0006)) for p in pts]
    for a, b in zip(pts, pts[1:]):
        for k in range(4):
            p0, p1 = a.lerp(b, k / 4), a.lerp(b, (k + 1) / 4)
            j = Vector((random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), 0))
            u = (p1 - p0)
            w = Vector((-u.y, u.x, 0)).normalized() * random.uniform(0.006, 0.014)
            v0, v1 = bm.verts.new(p0 - w), bm.verts.new(p0 + w)
            v2, v3 = bm.verts.new(p1 + j + w * 0.7), bm.verts.new(p1 + j - w * 0.7)
            bm.faces.new((v0, v3, v2, v1))
# canto noroeste: placa da laje erguida pelas raízes
bm = B('laje_quebrada', 'concreto')
caixa(bm, (-0.78, 0.78, Z0 + 0.03), (0.26, 0.2, 0.06), Matrix.Rotation(0.22, 3, 'X') @ Matrix.Rotation(0.6, 3, 'Z'))

# ------------------------------------------------------------------ pavilhão octogonal de aço
bm_e = B('estrutura', 'estrutura')
bm_am = B('beiral', 'amarelo')
bm_r = B('rebites', 'ferro')
for k in range(8):                                                         # pilares nos vértices
    p = V(45 * k + 22.5)
    rad = (p - C); rad.z = 0; rad.normalize()
    viga_i(bm_e, p + Vector((0, 0, Z0)), p + Vector((0, 0, ZE + 0.07)), 0.065, 0.055, rad)
    caixa(bm_e, p + Vector((0, 0, Z0 + 0.006)), (0.13, 0.13, 0.012), Matrix.Rotation(math.radians(45 * k + 22.5), 3, 'Z'))
    for dx in (-0.045, 0.045):
        for dy in (-0.045, 0.045):
            cil(bm_r, p + Matrix.Rotation(math.radians(45 * k + 22.5), 3, 'Z') @ Vector((dx, dy, Z0 + 0.016)), 0.008, 0.012, lados=6)
for k in range(8):
    A, Bv, n, t, Fc = face(k)
    viga_i(bm_am, A + Vector((0, 0, ZE + 0.035)), Bv + Vector((0, 0, ZE + 0.035)), 0.07, 0.055, (0, 0, 1))  # beiral
    rebites(bm_r, A + n * 0.031 + Vector((0, 0, ZE + 0.035)), Bv + n * 0.031 + Vector((0, 0, ZE + 0.035)), 8)
    if k != FACE_ABERTA:
        viga(bm_e, A + Vector((0, 0, 0.62)), Bv + Vector((0, 0, 0.62)), 0.035)                        # travessa
    for s in (-1, 1):                                                       # mãos-francesas
        p = A if s < 0 else Bv
        for e in (-0.004, 0.004):
            a_ = bm_e.verts.new(p + n * e + Vector((0, 0, ZE - 0.12)))
            b_ = bm_e.verts.new(p + n * e + Vector((0, 0, ZE)))
            c_ = bm_e.verts.new(p + n * e + Vector((0, 0, ZE)) - s * t * 0.11)
            bm_e.faces.new((a_, b_, c_) if e > 0 else (c_, b_, a_))
# espigões do telhado, terça no meio, anel do lanternim
for k in range(8):
    a = 45 * k + 22.5
    p0, p1 = V(a, R8, Z_TEL0), V(a, RL, Z_TEL1)
    tv = Vector((-math.sin(math.radians(a)), math.cos(math.radians(a)), 0))
    up = (p1 - p0).normalized().cross(tv)
    viga_i(bm_e, p0, p1, 0.05, 0.04, up)
    rebites(bm_r, p0 + up * 0.026 + tv * 0.012, p1 + up * 0.026 + tv * 0.012, 7, r=0.004)
    viga(bm_e, V(a, R8, ZE + 0.07), p0, 0.035)                                                      # montante beiral→espigão
for k in range(8):
    a0, a1 = 45 * k - 22.5, 45 * k + 22.5
    rm = (R8 + RL) / 2
    viga(bm_e, V(a0, rm, (Z_TEL0 + Z_TEL1) / 2), V(a1, rm, (Z_TEL0 + Z_TEL1) / 2), 0.03)
    viga(bm_e, V(a0, RL, Z_TEL1), V(a1, RL, Z_TEL1), 0.04)
# lanternim: venezianas de aço entre o telhado e a tampa, tampa grafite
ZL0, ZL1 = Z_TEL1 + 0.02, Z_TEL1 + 0.13
bm_lv = B('veneziana', 'casco')
for k in range(8):
    A, Bv = V(45 * k - 22.5, RL), V(45 * k + 22.5, RL)
    viga(bm_e, A + Vector((0, 0, ZL0 - 0.02)), A + Vector((0, 0, ZL1)), 0.03)
    n = Vector((math.cos(math.radians(45 * k)), math.sin(math.radians(45 * k)), 0))
    for j in range(4):
        z = ZL0 + 0.015 + j * 0.027
        caixa(bm_lv, (A + Bv) / 2 + n * 0.005 + Vector((0, 0, z)), (0.004, (Bv - A).length - 0.03, 0.03),
              Matrix.Rotation(math.radians(45 * k), 3, 'Z') @ Matrix.Rotation(-0.6, 3, 'Y'))
bm = B('tampa', 'grafite')
cil(bm, C + Vector((0, 0, ZL1 + 0.012)), RL + 0.04, 0.024, lados=8)
cil(bm, C + Vector((0, 0, ZL1 + 0.034)), RL - 0.05, 0.02, lados=8)
# chapas de rodapé (enferrujadas); a sudoeste é alta e tem o colar da alimentação das dosadoras
bm_k = B('rodape', 'casco')
P_ALIM = Vector((-0.665, -0.495, 0.5))                                    # onde o cano tanque→armário cruza a face SO
A5, B5, n5, t5, F5 = face(5)
u_al = t5.dot(P_ALIM - F5)
for k, zt in ((0, 0.3), (1, 0.3), (2, 0.3), (4, 0.3), (6, 0.22)):
    chapa(bm_k, k, -W8 / 2 + 0.03, W8 / 2 - 0.03, Z0, zt)
rc = 0.035
chapa(bm_k, 5, -W8 / 2 + 0.03, u_al - rc, Z0, 0.58)
chapa(bm_k, 5, u_al + rc, W8 / 2 - 0.03, Z0, 0.58)
chapa(bm_k, 5, u_al - rc, u_al + rc, Z0, P_ALIM.z - rc)
chapa(bm_k, 5, u_al - rc, u_al + rc, P_ALIM.z + rc, 0.58)
tubo(B('colar', 'ferro', True), P_ALIM - n5 * 0.025, P_ALIM + n5 * 0.025, rc, 20)
viga(bm_e, A5 + Vector((0, 0, 0.58)), B5 + Vector((0, 0, 0.58)), 0.035)
# olhos-sensores da IA nos pilares, mirando o carrossel
for a in (67.5, 157.5, 292.5):
    p = V(a, R8 - 0.06, 0.98)
    u = (C + Vector((0, 0, 0.55)) - p).normalized()
    caixa(B('grafite', 'grafite'), p + (V(a, R8) - p) * 0.4, (0.03, 0.03, 0.05), Matrix.Rotation(math.radians(a), 3, 'Z'))
    cil(B('grafite', 'grafite'), p, 0.022, 0.05, u, 16)
    cil(B('olho', 'olho'), p + u * 0.026, 0.013, 0.004, u, 12)

# ------------------------------------------------------------------ vidros
bm_v = B('vidro', 'vidro')
# paredes: rodapé → travessa (0,62) → beiral; a face aberta não tem vidro; S e NO perderam a fiada de baixo
JAG = {(2, 1): [0.7, 0.85, 0.5, 0.9, 0.62, 0.8, 0.95, 0.75], (0, 0): [0.35, 0.6, 0.25, 0.55, 0.18, 0.4, 0.66, 0.3]}
for k in range(8):
    if k == FACE_ABERTA:
        continue
    A, Bv, n, t, Fc = face(k)
    if k == 5:
        fileiras = [(1, 0.58, ZE)]
    elif k in (3, 6):
        fileiras = [(1, 0.62, ZE)]
    else:
        fileiras = [(0, 0.3, 0.62), (1, 0.62, ZE)]
    for fi, z0, z1 in fileiras:
        quad(bm_v, A + Vector((0, 0, z0)), Bv + Vector((0, 0, z0)), A + Vector((0, 0, z1)), Bv + Vector((0, 0, z1)),
             jag=JAG.get((k, fi)))
# telhado: duas fiadas por face; falta uma (norte, de cima) e uma está quebrada (sul, de baixo)
for k in range(8):
    a0, a1 = 45 * k - 22.5, 45 * k + 22.5
    rm = (R8 + RL) / 2
    zm = (Z_TEL0 + Z_TEL1) / 2
    for fi, (ra, za, rb, zb) in enumerate(((R8, Z_TEL0, rm, zm), (rm, zm, RL, Z_TEL1))):
        if (k, fi) == (2, 1):
            continue
        jag = [0.55, 0.3, 0.62, 0.2, 0.45, 0.12, 0.38, 0.5] if (k, fi) == (6, 0) else None
        o = Vector((0, 0, 0.03))
        quad(bm_v, V(a0, ra, za) + o, V(a1, ra, za) + o, V(a0, rb, zb) + o, V(a1, rb, zb) + o, jag=jag)
bm_c = B('cacos', 'caco')
for cx, cy, n_ in ((0.0, -0.55, 6), (0.5, 0.05, 4), (-0.5, 0.42, 3)):
    for k in range(n_):
        p = Vector((cx + random.uniform(-0.12, 0.12), cy + random.uniform(-0.1, 0.1), Z0 + 0.003))
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.02, 0.05)
        vs = [bm_c.verts.new(p + Vector((r * math.cos(a + tt), r * math.sin(a + tt) * 0.6, 0.002 * j)))
              for j, tt in enumerate((0, 2.1, 4.0))]
        bm_c.faces.new(vs)

# ------------------------------------------------------------------ tanque de seiva (canto sudoeste, fora do vidro) e entrada O0
bm_t = B('tanque', 'casco', True)
bm_ta = B('tanque_amarelo', 'amarelo', True)
bm_f = B('flanges', 'ferro', True)
bm_aco = B('aco', 'aco', True)
T = TANQUE
cil(bm_t, T + Vector((0, 0, 0.51)), R_TQ, 0.7, lados=32)
res = bmesh.ops.create_uvsphere(bm_t, u_segments=32, v_segments=10, radius=R_TQ,
                                matrix=Matrix.Translation(T + Vector((0, 0, 0.86))) @ Matrix.Diagonal((1, 1, 0.45, 1)))
bmesh.ops.delete(bm_t, geom=[v for v in res['verts'] if v.co.z < 0.86 - 1e-4], context='VERTS')
for z in (0.2, 0.5, 0.82):
    toro(bm_ta, T + Vector((0, 0, z)), R_TQ + 0.004, 0.012, 48, 8)
for k in range(4):
    a = PI / 4 + k * PI / 2
    p = T + Vector((math.cos(a) * 0.115, math.sin(a) * 0.115, 0))
    viga(bm_aco, p + Vector((0, 0, Z0)), p + Vector((0, 0, 0.19)), 0.032)
    caixa(bm_aco, p + Vector((0, 0, Z0 + 0.005)), (0.065, 0.065, 0.01))
# visor de nível (voltado para sudoeste, para fora)
dv = Vector((-0.707, -0.707, 0))
VIS = T + dv * (R_TQ + 0.035)
for z in (0.24, 0.78):
    tubo(bm_f, T + dv * (R_TQ - 0.01) + Vector((0, 0, z)), VIS + dv * 0.012 + Vector((0, 0, z)), 0.014, 12)
tubo(B('visor_vidro', 'tubo_vidro', True), VIS + Vector((0, 0, 0.24)), VIS + Vector((0, 0, 0.78)), 0.016, 16)
NIVEL = 0.62
tubo(B('visor_seiva', 'seiva', True), VIS + Vector((0, 0, 0.245)), VIS + Vector((0, 0, NIVEL)), 0.012, 12)
VISOR_BOLHAS = (VIS + Vector((0, 0, 0.26)), VIS + Vector((0, 0, NIVEL - 0.01)))
# entrada: flange na boca O0 → cotovelo → bocal norte do tanque
XE = -0.76
yt = T.y + math.sqrt(R_TQ ** 2 - (XE - T.x) ** 2)
cano(bm_aco, bm_f, [PORTA, Vector((XE, PORTA.y, PORTA.z)), Vector((XE, yt - 0.01, PORTA.z))], 0.045, flange=False)
for p, u in ((PORTA + Vector((0.012, 0, 0)), Vector((1, 0, 0))), (Vector((XE, yt + 0.025, PORTA.z)), Vector((0, 1, 0)))):
    tubo(bm_f, p - u * 0.01, p + u * 0.01, 0.07, 20)
    w = u.cross(Vector((0, 0, 1)))
    for k in range(8):
        a = k * PI / 4
        cil(bm_r, p + u * 0.012 + w * 0.058 * math.cos(a) + Vector((0, 0, 0.058 * math.sin(a))), 0.007, 0.01, u, 6)
caixa(bm_f, (-0.9, PORTA.y, (Z0 + PORTA.z - 0.045) / 2), (0.04, 0.05, PORTA.z - 0.045 - Z0))      # sela
# vazamento de seiva na flange da boca
bm = B('seiva_poca', 'seiva_poca')
mancha(bm, (-0.93, PORTA.y - 0.03, 0), 0.07, Z0 + 0.0015)
caixa(bm, PORTA + Vector((0.012, -0.072, -(PORTA.z - Z0) / 2 + 0.02)), (0.012, 0.004, PORTA.z - Z0 - 0.06))
# válvula atuada no topo (motor, sem volante)
cil(bm_aco, T + Vector((0, 0, 0.95)), 0.03, 0.04, lados=16)
caixa(B('grafite', 'grafite'), T + Vector((0, 0, 1.0)), (0.07, 0.05, 0.06))
cil(B('led_verde', 'led_verde'), T + Vector((-0.036, 0, 1.01)), 0.007, 0.004, Vector((-1, 0, 0)), 8)
bm = B('escorrido', 'ferrugem')
for a in (0.3, 1.9, 2.6, 4.2):
    p = T + Vector((math.cos(a) * (R_TQ + 0.001), math.sin(a) * (R_TQ + 0.001), 0))
    caixa(bm, p + Vector((0, 0, 0.55)), (0.006 + 0.004 * abs(math.sin(a)), 0.006 + 0.004 * abs(math.cos(a)), 0.4))
for k in range(14):
    a = random.uniform(0, 2 * PI)
    pedra(B('musgo', 'musgo'), T + Vector((math.cos(a) * 0.14, math.sin(a) * 0.14, Z0 + 0.006)), random.uniform(0.01, 0.022), 0.5)

# ------------------------------------------------------------------ estação de dosagem (dentro, oeste): armário, dosadoras
DX0, DX1, DY0, DY1, DZ = -0.80, -0.60, -0.32, -0.04, 0.6
caixa_de(B('armario', 'amarelo'), (DX0, DY0, Z0), (DX1, DY1, DZ))
caixa_de(B('grafite', 'grafite'), (DX1 - 0.002, DY0 + 0.04, 0.2), (DX1 + 0.006, DY1 - 0.04, 0.5))
for z in (0.22, 0.48):
    rebites(bm_r, (DX1 + 0.006, DY0 + 0.05, z), (DX1 + 0.006, DY1 - 0.05, z), 6)
cil(B('led_ambar', 'led_ambar'), Vector((DX1 + 0.008, DY1 - 0.06, 0.55)), 0.008, 0.006, Vector((1, 0, 0)), 8)
cil(B('led_verde', 'led_verde'), Vector((DX1 + 0.008, DY1 - 0.09, 0.55)), 0.008, 0.006, Vector((1, 0, 0)), 8)
# alimentação: tanque → (colar na face SO) → armário
d = Vector((0.342, 0.94, 0))
cano(bm_aco, bm_f, [T + d * (R_TQ - 0.01) + Vector((0, 0, P_ALIM.z)), Vector((P_ALIM.x, T.y + 0.94 * R_TQ + 0.02, P_ALIM.z)),
                    Vector((P_ALIM.x, DY0 + 0.01, P_ALIM.z))], 0.016, flange=False)
DOS_X = [-0.72, -0.64]
Z_DOS = DZ + 0.05
DYO = DY0 + 0.34                                                           # deslocamento das peças em y
PIST_Y0, PIST_LC = DY0 + 0.02, 0.09
CRUZ_Y = (-0.215 + DYO, -0.185 + DYO)
for i, x in enumerate(DOS_X):
    caixa_de(bm_aco, (x - 0.03, PIST_Y0 - 0.012, DZ), (x + 0.03, PIST_Y0 + 0.004, Z_DOS + 0.03))
    caixa_de(bm_aco, (x - 0.03, -0.155 + DYO, DZ), (x + 0.03, -0.14 + DYO, Z_DOS + 0.03))
    cil(B('dosadora', 'grafite', True), Vector((x, -0.09 + DYO, Z_DOS)), 0.026, 0.11, Vector((0, 1, 0)), 20)
    tubo(bm_f, (x, -0.15 + DYO, Z_DOS), (x, -0.136 + DYO, Z_DOS), 0.032, 20)
    tubo(bm_f, (x, -0.044 + DYO, Z_DOS), (x, -0.03 + DYO, Z_DOS), 0.032, 20)
    caixa_de(bm_aco, (x - 0.026, -0.23 + DYO, DZ), (x + 0.026, -0.16 + DYO, DZ + 0.012))
    mangueira(B('mang_sup', 'borracha', True), bezier((x, -0.2 + DYO, DZ - 0.002), (x, -0.25 + DYO, DZ - 0.02),
                                                      (x + 0.02, -0.28 + DYO, DZ + 0.01), (x, PIST_Y0 + 0.03, Z_DOS - 0.018), 6), 0.006)
# lança: coluna, braço até a estação 180°, cabeça com magazine e dois bicos
LZ = 0.80
cano(bm_aco, bm_f, [Vector((-0.70, DY1 + 0.0, DZ)), Vector((-0.70, DY1 + 0.0, LZ)), Vector((ST0.x - 0.03, ST0.y - 0.03, LZ))], 0.018, flange=False)
CAB = Vector((ST0.x, ST0.y, LZ))
caixa(B('cabeca', 'amarelo'), CAB + Vector((0, -0.03, 0)), (0.11, 0.1, 0.06))
BICOS = [CAB + Vector((-0.02, -0.028, -0.03)), CAB + Vector((0.02, -0.028, -0.03))]
for i, bp in enumerate(BICOS):
    cil(bm_f, bp + Vector((0, 0, -0.035)), 0.008, 0.05, lados=10, r2=0.004)
    cil(bm_aco, bp + Vector((0, 0, 0.005)), 0.012, 0.02, lados=12)
    mat = ('mang_ambar', 'mang_verde')[i]
    x = DOS_X[i]
    mangueira(B('mang' + mat, mat, True), bezier((x, -0.03 + DYO, Z_DOS), (x, 0.02 + DYO, Z_DOS + 0.04),
                                                 (bp.x - 0.1, bp.y - 0.08, LZ + 0.14), bp + Vector((0, 0, 0.04)), 10), 0.008)
MAG_Z0, MAG_Z1 = LZ + 0.03, 1.18
tubo(B('magazine', 'tubo_vidro', True), (CAB.x, CAB.y, MAG_Z0), (CAB.x, CAB.y, MAG_Z1), 0.042, 20)
for z in (MAG_Z0 + 0.01, (MAG_Z0 + MAG_Z1) / 2, MAG_Z1 - 0.01):
    toro(B('mag_aneis', 'amarelo', True), Vector((CAB.x, CAB.y, z)), 0.045, 0.006, 24, 6)
for k in range(3):
    a = k * 2 * PI / 3
    viga(bm_aco, (CAB.x + 0.05 * math.cos(a), CAB.y + 0.05 * math.sin(a), LZ), (CAB.x + 0.05 * math.cos(a), CAB.y + 0.05 * math.sin(a), MAG_Z1), 0.008)
cil(B('grafite', 'grafite'), Vector((CAB.x, CAB.y, MAG_Z1 + 0.02)), 0.055, 0.04, lados=20)
tubo(bm_aco, (CAB.x, CAB.y, MAG_Z1 + 0.04), (CAB.x, CAB.y, z_tel(abs(CAB.x - C.x)) - 0.025), 0.01, 8)
feixe(B('cabos', 'cabo', True), B('abracadeiras', 'aco'),
      bezier((-0.78, -0.1, DZ), (-0.8, -0.05, 0.9), (-0.75, 0.0, 1.15), Vector((CAB.x, CAB.y, MAG_Z1 + 0.035)), 12),
      Vector((0, 1, 0)), n=2, r=0.006)
# alimentação dos aspersores: sobe do armário e corre sob o espigão até o anel no lanternim
Z_ANEL, R_ANEL = 1.42, 0.26
ASP = [V(a, R_ANEL, 1.2) for a in (90, 210, 330)]
p_fim = V(200, R_ANEL, Z_ANEL)
cano(bm_aco, bm_f, [Vector((-0.775, -0.29, DZ)), Vector((-0.775, -0.29, 1.08)), p_fim], 0.016, flange=False)
toro(bm_aco, C + Vector((0, 0, Z_ANEL)), R_ANEL, 0.016, 48, 12)
for a in ASP:
    tubo(bm_aco, Vector((a.x, a.y, Z_ANEL)), a + Vector((0, 0, 0.04)), 0.012, 12)
    curva(bm_aco, Vector((a.x, a.y, Z_ANEL)), 0.017)
    cil(B('grafite', 'grafite'), a + Vector((0, 0, 0.03)), 0.022, 0.03, lados=16)
for a in (0, 120, 240):
    p = V(a + 30, R_ANEL, Z_ANEL)
    tubo(bm_f, p + Vector((0, 0, 0.016)), Vector((p.x, p.y, Z_TEL1 + 0.13)), 0.004, 6)

# ------------------------------------------------------------------ carrossel: parte fixa
bm_cf = B('carrossel_fixo', 'grafite')
cil(bm_cf, C + Vector((0, 0, Z0 + 0.02)), 0.16, 0.04, lados=8)
cil(bm_aco, C + Vector((0, 0, (Z0 + 0.33) / 2)), 0.07, 0.33 - Z0, lados=20)
caixa(B('motor', 'amarelo'), C + Vector((0, -0.24, 0.19)), (0.12, 0.1, 0.2))
cil(bm_aco, C + Vector((0, -0.15, 0.3)), 0.012, 0.1, lados=10)
cil(B('pinhao', 'ferro', True), C + Vector((0, -0.15, 0.345)), 0.03, 0.03, lados=12)
for k in range(6):
    a = math.radians(30 + 60 * k)
    p = C + Vector((R_T * math.cos(a), R_T * math.sin(a), 0))
    viga(bm_aco, p + Vector((0, 0, Z0)), p + Vector((0, 0, 0.392)), 0.025)
    caixa(bm_aco, p + Vector((0, 0, Z0 + 0.005)), (0.06, 0.06, 0.01))
toro(B('trilho', 'cromo', True), C + Vector((0, 0, 0.398)), R_T, 0.01, 96, 8)
feixe(B('cabos', 'cabo', True), B('abracadeiras', 'aco'),
      bezier(C + Vector((-0.06, -0.24, 0.12)), C + Vector((-0.1, -0.4, Z0 + 0.01)), Vector((-0.5, -0.3, Z0 + 0.01)),
             Vector((DX1 + 0.005, -0.25, 0.12)), 10), Vector((0, 0, 1)), n=2, r=0.008)

# ------------------------------------------------------------------ campo de crescimento: pilones, arco, emissores
bm_em = B('emissores', 'estrutura')
bm_l = B('lentes', 'lente')
R_P = 0.65
for th in (162, 18):
    p = V(th, R_P)
    viga_i(bm_em, p + Vector((0, 0, Z0)), p + Vector((0, 0, 1.02)), 0.055, 0.05, (C - p).normalized())
    caixa(bm_aco, p + Vector((0, 0, Z0 + 0.008)), (0.11, 0.11, 0.016))
    u = (C - p); u.z = 0; u.normalize()
    for z in (0.62, 0.84):
        cil(B('grafite', 'grafite'), p + u * 0.045 + Vector((0, 0, z)), 0.04, 0.05, u, 16)
        cil(bm_l, p + u * 0.073 + Vector((0, 0, z)), 0.03, 0.006, u, 16)
        toro(B('bobina', 'cobre', True), p + u * 0.045 + Vector((0, 0, z)), 0.044, 0.006, 24, 6,
             u.to_track_quat('Z', 'Y').to_matrix())
toro(bm_em, C + Vector((0, 0, 1.02)), R_P, 0.018, 64, 10, a0=math.radians(18), a1=math.radians(162))
for th in (50, 90, 130):
    a = math.radians(th)
    p = C + Vector((R_P * math.cos(a), R_P * math.sin(a), 1.0))
    u = Vector((-math.cos(a), -math.sin(a), -0.9)).normalized()
    cil(B('grafite', 'grafite'), p + u * 0.03, 0.035, 0.06, u, 16)
    cil(bm_l, p + u * 0.062, 0.026, 0.006, u, 16)
bm = bmesh.new()
n = 24
an = [math.radians(22 + (158 - 22) * i / n) for i in range(n + 1)]
vs = []
for a in an:
    vs.append([bm.verts.new(C + Vector((r * math.cos(a), r * math.sin(a), z))) for r, z in ((0.2, 0.46), (0.66, 0.46), (0.66, 1.0), (0.2, 1.0))])
for i in range(n):
    for j in range(4):
        bm.faces.new((vs[i][j], vs[i][(j + 1) % 4], vs[i + 1][(j + 1) % 4], vs[i + 1][j]))
bm.faces.new(list(reversed(vs[0])))
bm.faces.new(vs[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj('campo', bm, 'campo')

# ------------------------------------------------------------------ anel de luz de crescimento (falta o segmento oeste, onde fica o magazine)
R_LUZ, Z_LUZ = 0.45, 1.2
SEG_LUZ = [k for k in range(8) if k != 4]
for k in SEG_LUZ:
    a0, a1 = 45 * k - 22.5, 45 * k + 22.5
    p0, p1 = V(a0, R_LUZ, Z_LUZ), V(a1, R_LUZ, Z_LUZ)
    m = (p0 + p1) / 2
    L = (p1 - p0).length - 0.02
    R_ = Matrix.Rotation(math.radians(45 * k), 3, 'Z')
    bm = B('barra_luz', 'grafite')
    caixa(bm, m + Vector((0, 0, 0.02)), (0.09, L, 0.04), R_)
    for j in range(7):
        caixa(bm, m + R_ @ Vector((0, -L / 2 + 0.02 + j * (L - 0.04) / 6, 0.052)), (0.08, 0.006, 0.025), R_)
    caixa(B('led_luz%d' % (k == 2), 'cresce_falha' if k == 2 else 'cresce'), m + Vector((0, 0, -0.0025)), (0.06, L - 0.02, 0.004), R_)
    for s in (-1, 1):
        ph = m + R_ @ Vector((0, s * L * 0.3, 0.065))
        tubo(bm_f, ph, Vector((ph.x, ph.y, z_tel((ph - C).dot(R_ @ Vector((1, 0, 0)))) - 0.02)), 0.004, 6)
# nó da IA (canto nordeste, fora do vidro): armário elétrico com olho violeta; cabos para o campo, a luz e o braço
NO_ = Vector((0.83, 0.83, 0))
caixa_de(B('no_ia', 'grafite'), (0.7, 0.7, Z0), (0.96, 0.96, 0.52))
caixa_de(B('no_ia_am', 'amarelo'), (0.69, 0.69, Z0), (0.97, 0.97, 0.13))
for k in range(5):
    caixa_de(B('aletas_no', 'aco'), (0.72 + k * 0.05, 0.695, 0.2), (0.74 + k * 0.05, 0.7, 0.45))
for k in range(4):                                                         # coluna de leds de carga
    cil(B('led_verde' if k else 'led_ambar', 'led_verde' if k else 'led_ambar'), Vector((0.696, 0.74, 0.26 + 0.05 * k)),
        0.007, 0.006, Vector((-1, 0, 0)), 8)
caixa_de(B('grafite', 'grafite'), (0.694, 0.79, 0.2), (0.7, 0.93, 0.48))   # tampa aparafusada
rebites(bm_r, (0.693, 0.8, 0.47), (0.693, 0.92, 0.47), 4)
rebites(bm_r, (0.693, 0.8, 0.21), (0.693, 0.92, 0.21), 4)
for k in range(3):                                                         # bornes de cobre no topo, cabos saindo
    p = Vector((0.76 + 0.07 * k, 0.9, 0.52))
    cil(B('bornes', 'cobre', True), p + Vector((0, 0, 0.03)), 0.014, 0.06, lados=12)
    for j in range(3):
        toro(B('bornes_isol', 'grafite', True), p + Vector((0, 0, 0.012 + 0.016 * j)), 0.02, 0.005, 16, 6)
cil(B('olho', 'olho'), Vector((0.83, 0.83, 0.525)), 0.02, 0.006, lados=16)    # sensor no tampo
bm_cab = B('cabos', 'cabo', True)
bm_ab = B('abracadeiras', 'aco')
pE = V(18, R_P)
A1, B1, n1, t1, F1 = face(1)
feixe(bm_cab, bm_ab, bezier((0.72, 0.72, 0.12), (0.62, 0.62, Z0 + 0.01), F1 + Vector((0, 0, Z0 + 0.012)),
                            pE + Vector((0.03, 0.03, Z0 + 0.02)), 10), Vector((0, 0, 1)), n=2, r=0.008)
feixe(bm_cab, bm_ab, [Vector((0.9, 0.7, 0.12)), Vector((0.93, 0.6, Z0 + 0.012)), Vector((0.93, 0.0, Z0 + 0.012)),
                      Vector((0.93, -0.36, Z0 + 0.012)), Vector((0.92, -0.42, 0.1))], Vector((0, 0, 1)), n=3, r=0.008, passo=1)
pv = V(67.5, R8 - 0.04)
feixe(bm_cab, bm_ab, [Vector((0.75, 0.96, 0.4)), Vector((pv.x + 0.02, pv.y + 0.05, 0.5)), pv + Vector((0, 0, 0.7)),
                      pv + Vector((0, 0, ZE - 0.02)), V(67.5, R_LUZ + 0.06, Z_LUZ + 0.05)], Vector((0, 0, 1)), n=2, r=0.006, passo=1)

# ------------------------------------------------------------------ braço plantador: pedestal fixo e armário (canto sudeste)
bm_pd = B('pedestal', 'amarelo', True)
cil(bm_pd, PB + Vector((0, 0, (Z0 + 0.40) / 2)), 0.11, 0.40 - Z0, lados=24)
cil(bm_f, PB + Vector((0, 0, Z0 + 0.012)), 0.155, 0.024, lados=24)
for k in range(8):
    a = k * PI / 4 + PI / 8
    cil(bm_r, PB + Vector((0.13 * math.cos(a), 0.13 * math.sin(a), Z0 + 0.03)), 0.01, 0.014, lados=6)
toro(B('listra_ped', 'listras', True), PB + Vector((0, 0, 0.34)), 0.112, 0.012, 32, 6)
caixa_de(B('armario_braco', 'grafite'), (0.84, -0.62, Z0), (0.97, -0.4, 0.36))
caixa_de(B('aletas_braco', 'aco'), (0.835, -0.6, 0.12), (0.84, -0.42, 0.32))
cil(B('led_verde', 'led_verde'), Vector((0.833, -0.45, 0.33)), 0.007, 0.006, Vector((-1, 0, 0)), 8)
feixe(bm_cab, bm_ab, bezier((0.86, -0.6, 0.1), (0.84, -0.7, Z0 + 0.01), (0.8, -0.74, Z0 + 0.01), PB + Vector((0.08, -0.08, 0.16)), 8),
      Vector((0, 0, 1)), n=3, r=0.008)

# ------------------------------------------------------------------ raízes (erupção no noroeste), musgo, terra, poça
bm_rz = B('raizes', 'raiz', True)


def z_sup(x, y):
    """Superfície: topo da laje dentro, chão fora (com a quina arredondada)."""
    m = max(abs(x), abs(y))
    return Z0 if m < 0.975 else max(0.0, Z0 - (m - 0.975) * 3.0)


def raiz_org(bm, p, d, comp, r0, sem, galhos=True, sobe=0.0):
    """Raiz que serpenteia rente à superfície (meio enterrada), afina e solta radicelas; desce pela borda da laje."""
    rr = random.Random(sem)
    p = Vector((p[0], p[1], 0))
    d = Vector((d[0], d[1], 0)).normalized()
    n = 16
    passo = comp / n
    pts = []
    for i in range(n + 1):
        t = i / n
        r = r0 * (1 - 0.8 * t)
        arco = sobe * math.sin(PI * min(1.0, t * 3)) if t < 0.34 else 0.0       # trecho que estufa a laje
        pts.append(Vector((p.x, p.y, z_sup(p.x, p.y) + r * 0.45 + arco)))
        d = Matrix.Rotation(rr.uniform(-0.38, 0.38), 3, 'Z') @ d
        p = p + d * passo
    raiz(bm, pts, r0, r0 * 0.2)
    if galhos:
        for j in range(3, n - 2, 4):
            lado = Matrix.Rotation(rr.choice((-1, 1)) * rr.uniform(0.6, 1.1), 3, 'Z') @ d
            raiz_org(bm, pts[j], (pts[j + 1] - pts[j - 1]).normalized().lerp(lado, 0.7), comp * 0.3, r0 * 0.45, sem * 7 + j, False)


k_ = 0
for pts in RACHAS:
    a = Vector((pts[0][0], pts[0][1], 0))
    b_ = Vector((pts[-1][0], pts[-1][1], 0))
    raiz_org(bm_rz, a, b_ - a, (b_ - a).length + 0.25, 0.016, 11 + k_)
    k_ += 1
# erupção no noroeste: raízes grossas que estufam e racham a laje, uma entra pela face NO sem vidro
O_NO = Vector((-0.7, 0.7, 0))
for k in range(6):
    a = math.radians(95 + k * 30)
    raiz_org(bm_rz, O_NO, (math.cos(a), math.sin(a)), 0.55 + 0.1 * (k % 2), 0.03 - 0.002 * k, 50 + k, sobe=0.05 + 0.015 * (k % 3))
raiz_org(bm_rz, O_NO, (1, -1), 0.75, 0.024, 70, sobe=0.04)
raiz(bm_rz, [V(112.5, R8, Z0 + 0.01), V(112.5, R8, 0.25) + Vector((0.02, 0.02, 0)), V(112.5, R8, 0.45) + Vector((-0.02, 0.03, 0)),
             V(112.5, R8, 0.6) + Vector((0.03, 0.03, 0))], 0.012, 0.004)
bm_m = B('musgo', 'musgo')
for cx, cy, r in ((-0.72, 0.72, 0.16), (-0.5, 0.85, 0.09), (0.15, -0.75, 0.1), (-0.3, -0.6, 0.06), (0.88, 0.3, 0.07),
                  (-0.88, 0.4, 0.06), (0.3, 0.55, 0.05)):
    mancha(bm_m, (cx, cy, 0), r, Z0 + 0.0012)
    for k in range(int(10 + 60 * r)):
        pedra(bm_m, (cx + random.uniform(-r, r), cy + random.uniform(-r, r) * 0.7, Z0 + 0.003), random.uniform(0.008, 0.02), 0.45)
for k in range(8):
    p = V(45 * k + 22.5)
    for j in range(5):
        pedra(bm_m, (p.x + random.uniform(-0.07, 0.07), p.y + random.uniform(-0.07, 0.07), Z0 + 0.015), random.uniform(0.008, 0.016), 0.5)
bm_te = B('terra', 'terra')
for k in range(40):
    a = random.uniform(0, 2 * PI)
    r = R_T + random.uniform(-0.12, 0.14)
    pedra(bm_te, C + Vector((r * math.cos(a), r * math.sin(a), Z0 + 0.004)), random.uniform(0.008, 0.02), 0.35)
for k in range(5):
    a = random.uniform(0, 2 * PI)
    mancha(bm_te, (C.x + 0.4 * math.cos(a), C.y + 0.4 * math.sin(a), 0), 0.08, Z0 + 0.0008 + 0.0002 * k)
mancha(B('poca', 'poca'), (-0.2, 0.1, 0), 0.16, Z0 + 0.001)
mancha(B('poca', 'poca'), (0.15, -0.2, 0), 0.1, Z0 + 0.0011)

# ------------------------------------------------------------------ mudas e árvores já plantadas lá fora
def folha(bm, base, d, comp, larg, cai=0.25):
    d = Vector(d).normalized()
    up = Vector((0, 0, 1))
    side = d.cross(up)
    side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
    rows = []
    n = 6
    for i in range(n + 1):
        t = i / n
        c = base + d * comp * t + up * (-cai * comp * t * t)
        w = larg * (math.sin(PI * t) ** 0.7 if 0 < t < 1 else 0.0)
        lift = up * 0.3 * w
        rows.append((bm.verts.new(c + side * w + lift), bm.verts.new(c), bm.verts.new(c - side * w + lift)))
    for i in range(n):
        bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
        bm.faces.new((rows[i][1], rows[i][2], rows[i + 1][2], rows[i + 1][1]))


def muda(bmc, bmf, base, h, nf, sem):
    """Muda: caule curvo e folhas em espiral (as de baixo maiores e mais abertas). Origem na base do caule."""
    rr = random.Random(sem)
    base = Vector(base)
    sx, sy = rr.uniform(-0.15, 0.15) * h, rr.uniform(-0.15, 0.15) * h
    pts = [base + Vector((sx * t * t, sy * t * t, h * t)) for t in (i / 6 for i in range(7))]
    mangueira(bmc, pts, 0.003 + 0.012 * h)
    a0 = rr.uniform(0, 2 * PI)
    for j in range(nf):
        t = 0.28 + 0.72 * j / nf
        p = base + Vector((sx * t * t, sy * t * t, h * t))
        a = a0 + j * 2.4
        comp = h * (0.62 - 0.3 * t) * rr.uniform(0.85, 1.15)
        d = Vector((math.cos(a), math.sin(a), 0.35 + 0.9 * t))
        folha(bmf, p, d, comp, comp * 0.36, cai=0.35 - 0.25 * t)
    topo = pts[-1]
    for a in (a0, a0 + PI):                                                 # broto no topo
        folha(bmf, topo, (math.cos(a) * 0.3, math.sin(a) * 0.3, 1), h * 0.16, h * 0.05, 0.0)


def capsula(partes, origem=Vector((0, 0, 0)), rot=Matrix.Identity(3), gasta=False):
    """Cápsula-dardo: ponta cônica (−z), corpo, aletas, anel luminoso e colar; boca aberta com terra (+z)."""
    o = Vector(origem)
    bc = partes.setdefault('casco' if gasta else 'aco', bmesh.new())
    ba = partes.setdefault('ferro' if gasta else 'anel_capsula', bmesh.new())
    bt = partes.setdefault('terra', bmesh.new())
    M_ = Matrix.Translation(o) @ rot.to_4x4()
    res = bmesh.ops.create_cone(bc, cap_ends=True, segments=16, radius1=0.028, radius2=0.028, depth=0.09,
                                matrix=M_ @ Matrix.Translation((0, 0, 0.005)))
    bmesh.ops.create_cone(bc, cap_ends=True, segments=16, radius1=0.003, radius2=0.028, depth=0.06,
                          matrix=M_ @ Matrix.Translation((0, 0, -0.07)))
    for k in range(3):
        a = k * 2 * PI / 3
        caixa(bc, o + rot @ Vector((0.038 * math.cos(a), 0.038 * math.sin(a), -0.005)), (0.02, 0.003, 0.05),
              rot @ Matrix.Rotation(a, 3, 'Z'))
    bmesh.ops.create_cone(ba, cap_ends=True, segments=16, radius1=0.0292, radius2=0.0292, depth=0.012,
                          matrix=M_ @ Matrix.Translation((0, 0, 0.018)))
    toro(bc, o + rot @ Vector((0, 0, 0.05)), 0.028, 0.005, 20, 6, rot)
    bmesh.ops.create_cone(bt, cap_ends=True, segments=12, radius1=0.024, radius2=0.024, depth=0.006,
                          matrix=M_ @ Matrix.Translation((0, 0, 0.046)))
    return partes


ARVORES = [(1.5, 0.6, 0.55), (1.8, -0.2, 0.3), (1.25, 1.5, 0.85), (-0.35, 1.6, 0.6), (0.35, -1.65, 0.4),
           (2.25, 0.95, 0.22), (-1.6, 0.95, 0.45), (-1.45, -1.35, 0.5), (0.9, 2.05, 0.3), (2.45, -0.6, 0.2)]
fora = {}
for i, (x, y, h) in enumerate(ARVORES):
    p = Vector((x, y, 0))
    pedra(B('terra_fora', 'terra_seca'), p + Vector((0, 0, 0.0)), 0.09 + 0.05 * h, 0.35)
    inc = Matrix.Rotation(random.uniform(0.25, 0.5), 3, 'X') @ Matrix.Rotation(random.uniform(0, 2 * PI), 3, 'Z')
    capsula(fora, p + inc @ Vector((0, 0, 0.0)) + Vector((0.07, 0.04, 0.025)), Matrix.Rotation(random.uniform(0, 2 * PI), 3, 'Z') @ inc, gasta=True)
    if h < 0.35:
        muda(B('caule_fora', 'caule', True), B('folha_fora', 'folha'), p + Vector((0, 0, 0.03)), h, 9, 100 + i)
    else:                                                                  # árvore jovem: tronco, galhos e copa
        bt = B('troncos', 'tronco', True)
        topo = p + Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), h))
        raiz(bt, [p + Vector((0, 0, 0)), p.lerp(topo, 0.5) + Vector((0.02, 0, 0)), topo], 0.012 + 0.03 * h, 0.008)
        bmc = B('copa', 'copa')
        for k in range(6):
            a = k * 2 * PI / 6 + random.uniform(0, 0.5)
            c = topo + Vector((math.cos(a) * 0.12 * h, math.sin(a) * 0.12 * h, random.uniform(-0.08, 0.12) * h))
            raiz(bt, [p.lerp(topo, 0.75), c], 0.008, 0.004)
            rc = 0.15 * h + 0.03
            for j in range(34):
                d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.4, 1))).normalized()
                cf = 0.05 + 0.06 * h
                folha(bmc, c + d * rc * random.uniform(0.3, 0.8), d + Vector((0, 0, 0.3)), cf, cf * 0.42, 0.3)
        for k in range(4):                                                 # raízes à mostra
            a = random.uniform(0, 2 * PI)
            raiz(bt, [p + Vector((0, 0, 0.02)), p + Vector((math.cos(a) * 0.07, math.sin(a) * 0.07, 0.0)),
                      p + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, -0.02))], 0.009, 0.003)
for mat, bm in fora.items():
    obj('capsulas_gastas_' + mat, bm, mat)

# ------------------------------------------------------------------ objetos estáticos
for (nome, mat, liso), bm in BMS.items():
    o = obj(nome, bm, mat)
    if liso:
        suavizar(o)


# ------------------------------------------------------------------ objetos animados
def peca(nome, partes, liso=()):
    objs = []
    for mat, bm in partes.items():
        o = obj(nome + '_' + mat, bm, mat)
        if mat in liso or True:
            suavizar(o)
        o.rotation_mode = 'QUATERNION'
        objs.append(o)
    return objs


def pose(objs, Mw, q, prev={}):
    loc, rot, _ = Mw.decompose()
    for o in objs:
        k = o.name
        if k in prev:
            rot.make_compatible(prev[k])
        prev[k] = rot.copy()
        o.location = loc
        o.rotation_quaternion = rot
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)


def escala(objs, s, q):
    for o in objs:
        o.scale = (s, s, s)
        o.keyframe_insert('scale', frame=q)


def vis(objs, v, q):
    for o in objs:
        o.hide_render = o.hide_viewport = not v
        o.keyframe_insert('hide_render', frame=q)
        o.keyframe_insert('hide_viewport', frame=q)


# carrossel (gira em volta de C): cubo, coroa dentada, raios, bandejas, roletes, terra
car = {}
bcar = car.setdefault('aco', bmesh.new())
bam = car.setdefault('amarelo', bmesh.new())
bfe = car.setdefault('ferro', bmesh.new())
bte = car.setdefault('terra', bmesh.new())
bmu = car.setdefault('musgo', bmesh.new())
cil(bfe, Vector((0, 0, 0.345)), 0.12, 0.03, lados=40)
for k in range(32):
    a = k * 2 * PI / 32
    caixa(bfe, (0.123 * math.cos(a), 0.123 * math.sin(a), 0.345), (0.012, 0.008, 0.028), Matrix.Rotation(a, 3, 'Z'))
cil(bam, Vector((0, 0, 0.41)), 0.09, 0.1, lados=24)
cil(bcar, Vector((0, 0, 0.465)), 0.06, 0.01, lados=24)
car.setdefault('lente', bmesh.new())
cil(car['lente'], Vector((0, 0, 0.472)), 0.03, 0.006, lados=16)
for k in range(6):
    a = math.radians(180 - 60 * k)
    R_ = Matrix.Rotation(a, 3, 'Z')
    viga(bcar, R_ @ Vector((0.08, 0, 0.426)), R_ @ Vector((R_T - 0.08, 0, 0.426)), 0.03)
    # bandeja: fundo, paredes, terra e rebites
    c = R_ @ Vector((R_T, 0, 0))
    caixa(bam, c + Vector((0, 0, 0.446)), (0.2, 0.17, 0.012), R_)
    for (dx, dy, sx, sy) in ((0.096, 0, 0.008, 0.17), (-0.096, 0, 0.008, 0.17), (0, 0.081, 0.2, 0.008), (0, -0.081, 0.2, 0.008)):
        caixa(bam, c + R_ @ Vector((dx, dy, 0.483)), (sx, sy, 0.064), R_)
    caixa(bte, c + Vector((0, 0, 0.475)), (0.184, 0.154, 0.05), R_)
    for j in range(6):
        pedra(bte, c + R_ @ Vector((random.uniform(-0.07, 0.07), random.uniform(-0.06, 0.06), Z_TERRA)), random.uniform(0.01, 0.018), 0.4)
    for j in range(3):
        pedra(bmu, c + R_ @ Vector((random.uniform(-0.08, 0.08), random.uniform(-0.065, 0.065), Z_TERRA + 0.002)), random.uniform(0.007, 0.013), 0.4)
    for sy in (-1, 1):
        rebites(bfe, c + R_ @ Vector((-0.09, sy * 0.086, 0.5)), c + R_ @ Vector((0.09, sy * 0.086, 0.5)), 5, r=0.004)
    for j in range(5):                                                      # forração de brotos na terra
        pb = c + R_ @ Vector((random.uniform(-0.075, 0.075), random.uniform(-0.06, 0.06), Z_TERRA - 0.002))
        if (pb - c).length < 0.04:
            continue
        muda(car.setdefault('caule', bmesh.new()), car.setdefault('folha', bmesh.new()), pb, random.uniform(0.025, 0.045), 4, 300 + k * 10 + j)
    # garfo e rolete sobre o trilho
    caixa(bcar, c + Vector((0, 0, 0.432)), (0.03, 0.04, 0.016), R_)
    cil(bfe, c + Vector((0, 0, 0.42)), 0.012, 0.03, R_ @ Vector((1, 0, 0)), 12)
carrossel = peca('carrossel', car)


def ang_carrossel(fr):
    return -60.0 * smooth(fr / 0.3)                                         # graus, sentido horário


# cápsulas e mudas das bandejas (uma por bandeja), cápsula em trânsito no braço e no voo
MUDA_H, MUDA_NF = 0.32, 12
cap_band, mud_band = [], []
for k in range(6):
    cap_band.append(peca('capsula%d' % k, capsula({})))
    mp = {'caule': bmesh.new(), 'folha_campo': bmesh.new()}
    muda(mp['caule'], mp['folha_campo'], Vector((0, 0, 0)), MUDA_H, MUDA_NF, k)
    mud_band.append(peca('muda%d' % k, mp))
cap_voo = peca('capsula_voo', capsula({}))
mp = {'caule': bmesh.new(), 'folha_campo': bmesh.new()}
muda(mp['caule'], mp['folha_campo'], Vector((0, 0, 0)), MUDA_H, MUDA_NF, 2)  # a bandeja 2 é a colhida no laço
mud_voo = peca('muda_voo', mp)
mag_baixo = peca('capsula_magazine', capsula({}))                          # a de baixo da pilha do magazine
mag_pilha = capsula({}, Vector((CAB.x, CAB.y, MAG_Z0 + 0.27)))
for mat, bm in mag_pilha.items():
    obj('magazine_pilha_' + mat, bm, mat)
CAP_MAG = Vector((CAB.x, CAB.y, MAG_Z0 + 0.11))

# braço: torre (ψ), braço (α), antebraço (β), punho+garra (γ), dedos
torre = {'amarelo': bmesh.new(), 'grafite': bmesh.new(), 'aco': bmesh.new(), 'ferro': bmesh.new(), 'olho': bmesh.new()}
cil(torre['grafite'], Vector((0, 0, 0.40 + 0.03 - ZS)), 0.125, 0.06, lados=28)
for s in (-1, 1):
    caixa_de(torre['amarelo'], (-0.08, s * 0.065 - 0.012, 0.46 - ZS), (0.08, s * 0.065 + 0.012, 0.05))
cil(torre['grafite'], Vector((0, 0.1, 0)), 0.06, 0.05, Vector((0, 1, 0)), 24)          # motor do ombro
cil(torre['aco'], Vector((0, 0.13, 0)), 0.045, 0.012, Vector((0, 1, 0)), 24)
caixa_de(torre['grafite'], (-0.17, -0.06, 0.46 - ZS), (-0.09, 0.06, 0.56 - ZS))          # contrapeso/eletrônica
cil(torre['olho'], Vector((-0.171, 0, 0.53 - ZS)), 0.012, 0.004, Vector((1, 0, 0)), 12)
rebites(torre['ferro'], (-0.07, -0.078, 0.47 - ZS), (0.07, -0.078, 0.47 - ZS), 5, r=0.005)
mangueira(torre['grafite'], bezier((-0.13, 0.06, 0.53 - ZS), (-0.1, 0.12, 0.6 - ZS), (-0.03, 0.14, 0.04), (0, 0.13, 0.04), 6), 0.008)
pc_torre = peca('braco_torre', torre)

sup = {'amarelo': bmesh.new(), 'grafite': bmesh.new(), 'aco': bmesh.new(), 'cabo': bmesh.new(), 'listras': bmesh.new()}
caixa_de(sup['amarelo'], (0.0, -0.045, -0.035), (L1 - 0.05, 0.045, 0.035))
cil(sup['aco'], Vector((0, 0, 0)), 0.042, 0.106, Vector((0, 1, 0)), 24)
for s in (-1, 1):
    caixa_de(sup['amarelo'], (L1 - 0.07, s * 0.04 - 0.006, -0.03), (L1 + 0.04, s * 0.04 + 0.006, 0.03))
cil(sup['grafite'], Vector((L1, 0.07, 0)), 0.045, 0.05, Vector((0, 1, 0)), 24)           # motor do cotovelo
cil(sup['aco'], Vector((L1, 0, 0)), 0.02, 0.1, Vector((0, 1, 0)), 16)
caixa_de(sup['listras'], (0.12, -0.046, -0.036), (0.2, 0.046, 0.036))
mangueira(sup['cabo'], [Vector((0.03 + i * (L1 - 0.06) / 6, 0.03, 0.04 + 0.008 * math.sin(i))) for i in range(7)], 0.009)
pc_sup = peca('braco_sup', sup)

ant = {'aco': bmesh.new(), 'grafite': bmesh.new(), 'cabo': bmesh.new()}
caixa_de(ant['aco'], (0.03, -0.028, -0.026), (L2 - 0.04, 0.028, 0.026))
cil(ant['aco'], Vector((0, 0, 0)), 0.032, 0.068, Vector((0, 1, 0)), 20)
for s in (-1, 1):
    caixa_de(ant['aco'], (L2 - 0.06, s * 0.03 - 0.005, -0.024), (L2 + 0.03, s * 0.03 + 0.005, 0.024))
cil(ant['grafite'], Vector((L2, -0.05, 0)), 0.032, 0.035, Vector((0, 1, 0)), 20)          # motor do punho
mangueira(ant['cabo'], [Vector((0.04 + i * (L2 - 0.08) / 5, -0.03, 0.03)) for i in range(6)], 0.007)
pc_ant = peca('braco_ant', ant)

pun = {'grafite': bmesh.new(), 'amarelo': bmesh.new(), 'olho': bmesh.new()}
cil(pun['grafite'], Vector((0, 0, 0)), 0.024, 0.05, Vector((0, 1, 0)), 20)
caixa_de(pun['amarelo'], (0.015, -0.022, -0.03), (0.075, 0.022, 0.03))
caixa_de(pun['grafite'], (0.07, -0.07, -0.022), (0.085, 0.07, 0.022))                      # trilho dos dedos
cil(pun['olho'], Vector((0.086, 0, 0.026)), 0.008, 0.004, Vector((1, 0, 0)), 10)
pc_pun = peca('braco_punho', pun)
dedos = []
for s in (-1, 1):
    dd = {'aco': bmesh.new(), 'borracha': bmesh.new()}
    caixa_de(dd['aco'], (0.078, -0.007, -0.02), (0.165, 0.007, 0.02))
    caixa_de(dd['borracha'], (0.1, -s * 0.009, -0.016), (0.16, -s * 0.006, 0.016))
    dedos.append((s, peca('dedo%d' % (s > 0), dd)))

# dosadoras: pistao0 e pistao1 (camisa fixa no suporte do armário, haste presa na cruzeta) + êmbolo
pistoes = []
for i, x in enumerate(DOS_X):
    cam = {'amarelo': bmesh.new(), 'ferro': bmesh.new()}
    cil(cam['amarelo'], Vector((x, PIST_Y0 + PIST_LC / 2, Z_DOS)), 0.018, PIST_LC, Vector((0, 1, 0)), 20)
    for y in (PIST_Y0 + 0.004, PIST_Y0 + PIST_LC - 0.004):
        cil(cam['ferro'], Vector((x, y, Z_DOS)), 0.022, 0.008, Vector((0, 1, 0)), 20)
    o = obj('pistao%d' % i, cam['amarelo'], 'amarelo')
    suavizar(o)
    o2 = obj('pistao%d_tampas' % i, cam['ferro'], 'ferro')
    suavizar(o2)
    has = {'cromo': bmesh.new(), 'aco': bmesh.new()}
    L_H = 0.1
    cil(has['cromo'], Vector((0, -L_H / 2, 0)), 0.007, L_H, Vector((0, 1, 0)), 12)        # haste: termina na origem (cruzeta)
    caixa(has['aco'], (0, 0.004, 0), (0.05, 0.012, 0.036))                                 # cruzeta
    cil(has['cromo'], Vector((0, 0.04, 0)), 0.009, 0.07, Vector((0, 1, 0)), 12)          # êmbolo para dentro da bomba
    pistoes.append((x, peca('pistao%d_haste' % i, has)))

# antena (cumeeira, oeste): mastro fixo e cabeça de sensores que gira
ANT = C + Vector((0, 0, ZL1 + 0.044))
bm = B('mastro', 'aco')
cil(bm, ANT + Vector((0, 0, 0.12)), 0.014, 0.24, lados=12)
caixa(bm, ANT + Vector((0, 0, 0.005)), (0.08, 0.08, 0.012))
an_ = {'grafite': bmesh.new(), 'olho': bmesh.new(), 'aco': bmesh.new()}
toro(an_['aco'], Vector((0, 0, 0)), 0.07, 0.007, 32, 8)
for k in range(3):
    a = k * 2 * PI / 3
    viga(an_['aco'], (0, 0, 0), (0.07 * math.cos(a), 0.07 * math.sin(a), 0), 0.008)
cil(an_['grafite'], Vector((0, 0, 0.02)), 0.025, 0.05, lados=16)
for s in (-1, 1):
    cil(an_['grafite'], Vector((s * 0.07, 0, 0.0)), 0.018, 0.04, Vector((s, 0, 0)), 16)
    cil(an_['olho'], Vector((s * 0.091, 0, 0.0)), 0.012, 0.004, Vector((s, 0, 0)), 12)
cil(an_['aco'], Vector((0, 0, 0.09)), 0.003, 0.12, lados=6)
antena = peca('antena', an_)
B_ = BMS.get(('mastro', 'aco', False))
if B_ is not None:
    obj('mastro', B_, 'aco')

# aspersores (cabeça girando) com névoa e gotas
cab_asp = []
for i, a in enumerate(ASP):
    h = {'aco': bmesh.new(), 'cobre': bmesh.new()}
    cil(h['aco'], Vector((0, 0, 0)), 0.018, 0.03, lados=16)
    for k in range(3):
        aa = k * 2 * PI / 3
        d = Vector((math.cos(aa), math.sin(aa), -0.25))
        tubo(h['aco'], Vector((0, 0, -0.005)), d * 0.08, 0.005, 8)
        cil(h['cobre'], d * 0.08 + Vector((-math.sin(aa), math.cos(aa), 0)) * 0.006, 0.006, 0.014,
            Vector((-math.sin(aa), math.cos(aa), -0.3)), 8)
    cab_asp.append(peca('aspersor%d' % i, h))
nevoas = []
for i, a in enumerate(ASP):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.3, radius2=0.05, depth=0.5,
                          matrix=Matrix.Translation((0, 0, -0.27)))
    o = obj('nevoa%d' % i, bm, 'nevoa')
    o.location = a
    nevoas.append(o)


def bolinha(nome, mat, r, sub=1, esticar=1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co.z *= esticar
    return obj(nome, bm, mat)


gotas = [(bolinha('gota', 'agua', 0.0045, 1, 1.6), i, k) for i in range(len(ASP)) for k in range(14)]
pingos = [(bolinha('pingo', ('gota_seiva', 'gel')[i], 0.005, 1, 1.5), i, k) for i in range(2) for k in range(2)]
bolhas = [bolinha('bolha', 'bolha', 0.004, 0) for k in range(4)]
sementes = []
for k in range(26):
    bm = bmesh.new()
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.009)
    for v in res['verts']:
        v.co.z *= 1.7
    asa = [bm.verts.new(p) for p in ((0, 0, 0.008), (0.03, 0.004, 0.02), (0.034, -0.004, 0.012))]
    bm.faces.new(asa)
    o = obj('semente', bm, 'semente')
    o.rotation_mode = 'XYZ'
    sementes.append(o)
torroes = [bolinha('torrao', 'terra_seca', random.uniform(0.008, 0.015), 1) for k in range(10)]
vel_t = [Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(0.8, 1.6))) for k in range(10)]

# ------------------------------------------------------------------ cinemática do braço
def ik(r, z):
    d = max(1e-4, math.hypot(r, z))
    ca = max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
    al = math.atan2(z, r) + math.acos(ca)
    er, ez = L1 * math.cos(al), L1 * math.sin(al)
    be = math.atan2(z - ez, r - er)
    return al, be


def alvo_pega():
    p = pos_estacao(0)
    v = p - PB
    return math.degrees(math.atan2(v.y, v.x)), v.length


PSI_P, R_G = alvo_pega()
#        nome        ψ        r_punho      z_punho  γ    garra
POSES = {'pronto': (PSI_P, 0.40, 0.32, 35, 0), 'aprox': (PSI_P, R_G - LG - 0.14, 0.0, 0, 0),
         'pega': (PSI_P, R_G - LG, Z_CAP + 0.005 - ZS, 0, 0), 'fecha': (PSI_P, R_G - LG, Z_CAP + 0.005 - ZS, 0, 1),
         'ergue': (PSI_P, R_G - LG - 0.04, 0.24, 10, 1), 'arma': (-25, 0.2, 0.5, 140, 1),
         'lanca': (-25, 0.16, 0.5, 15, 1), 'solta': (-25, 0.2, 0.46, -5, 0),
         'alto1': (100, -0.06, 0.85, 90, 1), 'alto2': (30, -0.06, 0.85, 90, 1),
         'alto3': (30, -0.06, 0.85, 90, 0), 'alto4': (100, -0.06, 0.85, 90, 0),
         'desce': (PSI_P, R_G - LG - 0.04, 0.24, 10, 0),
         'retrai': (PSI_P, 0.08, 0.3, 90, 1), 'retrai2': (PSI_P, 0.08, 0.3, 90, 0)}
ROTEIRO = [(0.0, 'pronto'), (0.31, 'pronto'), (0.35, 'aprox'), (0.39, 'pega'), (0.42, 'fecha'), (0.46, 'ergue'),
           (0.51, 'retrai'), (0.56, 'alto1'), (0.63, 'alto2'), (0.69, 'arma'), (0.745, 'lanca'), (0.79, 'solta'),
           (0.83, 'alto3'), (0.89, 'alto4'), (0.93, 'retrai2'), (0.97, 'desce'), (1.0, 'pronto')]
FR_SOLTA = 0.745
FR_PEGA = 0.42


def juntas(fr):
    for (f0, a), (f1, b) in zip(ROTEIRO, ROTEIRO[1:]):
        if f0 <= fr <= f1:
            t = (fr - f0) / (f1 - f0) if f1 > f0 else 0
            t = t if b == 'lanca' else smooth(t)                            # o lançamento é seco, sem amaciar
            pa, pb = POSES[a], POSES[b]
            ja, jb = ik(pa[1], pa[2]), ik(pb[1], pb[2])
            psi = pa[0] + (pb[0] - pa[0]) * t
            al = ja[0] + (jb[0] - ja[0]) * t
            be = ja[1] + (jb[1] - ja[1]) * t
            ga = math.radians(pa[3] + (pb[3] - pa[3]) * t)
            gr = pa[4] + (pb[4] - pa[4]) * t
            return math.radians(psi), al, be, ga, gr
    return juntas(0.0)


def matrizes(fr):
    psi, al, be, ga, gr = juntas(fr)
    Rz = Matrix.Rotation(psi, 4, 'Z')
    Mt = Matrix.Translation(PB + Vector((0, 0, ZS))) @ Rz
    Ms = Mt @ Matrix.Rotation(-al, 4, 'Y')
    E = Ms @ Vector((L1, 0, 0))
    Ma = Matrix.Translation(E) @ Rz @ Matrix.Rotation(-be, 4, 'Y')
    W = Ma @ Vector((L2, 0, 0))
    Mp = Matrix.Translation(W) @ Rz @ Matrix.Rotation(-ga, 4, 'Y')
    return Mt, Ms, Ma, Mp, gr


def pega(fr):
    return matrizes(fr)[3] @ Matrix.Translation((LG, 0, 0))


M_CAP_PEGA = Matrix.Translation(pos_estacao(0) + Vector((0, 0, Z_CAP)))
M_REL = pega(FR_PEGA).inverted() @ M_CAP_PEGA
G = Vector((0, 0, -9.81))
P_SOLTA = (pega(FR_SOLTA) @ M_REL).to_translation()
POUSO = Vector((1.9, -1.15, 0.035))
T_VOO = 0.5
V0 = (POUSO - P_SOLTA) / T_VOO - 0.5 * G * T_VOO
FR_POUSO = FR_SOLTA + T_VOO / 4.0


def idade(k, fr):
    return (k + fr + 0.7) % 6.0


def cresc(a):
    return 0.1 + 0.9 * smooth((a - 0.25) / 2.6) ** 0.8


# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    rot = ang_carrossel(fr)
    pose(carrossel, Matrix.Translation(C) @ Matrix.Rotation(math.radians(rot), 4, 'Z'), q)
    # bandejas: cápsula cai do magazine ao chegar na estação 180°, muda cresce com a idade, braço colhe a 0°
    for k in range(6):
        th = 180 - 60 * k + rot
        a = idade(k, fr)
        p = pos_estacao(th)
        Rk = Matrix.Rotation(math.radians(th), 4, 'Z')
        z = Z_CAP
        if a < 0.06:                                                        # caindo do magazine
            z = CAP_MAG.z + (Z_CAP - CAP_MAG.z) * (a / 0.06) ** 2
        cap_vis = a < 3.0 + (FR_PEGA - 0.3) - 0.001
        Mc = Matrix.Translation(p + Vector((0, 0, z))) @ Rk
        pose(cap_band[k], Mc, q)
        vis(cap_band[k], cap_vis, q)
        s = cresc(a)
        bal = 0.06 * math.sin(2 * PI * (2 * fr + k * 0.3)) if 1.0 < a < 2.9 else 0.0   # balança no campo
        pose(mud_band[k], Mc @ Matrix.Translation((0, 0, 0.05)) @ Matrix.Rotation(bal, 4, 'X'), q)
        escala(mud_band[k], s, q)
        vis(mud_band[k], cap_vis and a > 0.25, q)
    vis(mag_baixo, not (0.3 <= fr < 0.42), q)
    pose(mag_baixo, Matrix.Translation(CAP_MAG), q)
    # braço
    Mt, Ms, Ma, Mp, gr = matrizes(fr)
    pose(pc_torre, Mt, q)
    pose(pc_sup, Ms, q)
    pose(pc_ant, Ma, q)
    pose(pc_pun, Mp, q)
    for s, dd in dedos:
        w = 0.062 - (0.062 - 0.036) * gr
        pose(dd, Mp @ Matrix.Translation((0, s * w, 0)), q)
    # cápsula em trânsito: na garra → voo balístico ponta à frente → cravada
    if FR_PEGA <= fr < FR_SOLTA:
        Mv = pega(fr) @ M_REL
        vis(cap_voo + mud_voo, True, q)
    elif FR_SOLTA <= fr:
        t = min((fr - FR_SOLTA) * 4.0, T_VOO)
        p = P_SOLTA + V0 * t + 0.5 * G * t * t
        v = V0 + G * t
        q_vel = (-v).to_track_quat('Z', 'Y')
        q_ini = (pega(FR_SOLTA) @ M_REL).to_quaternion()
        qq = q_ini.slerp(q_vel, min(1.0, t / 0.12))
        if t >= T_VOO:
            p = p + v.normalized() * 0.05                                   # crava a ponta no chão
        Mv = Matrix.Translation(p) @ qq.to_matrix().to_4x4()
        vis(cap_voo + mud_voo, True, q)
    else:
        Mv = Matrix.Translation(POUSO)
        vis(cap_voo + mud_voo, False, q)
    pose(cap_voo, Mv, q)
    pose(mud_voo, Mv @ Matrix.Translation((0, 0, 0.05)), q)
    # torrões espirrando no pouso
    for k, o in enumerate(torroes):
        t = (fr - FR_POUSO) * 4.0
        viva = 0 <= t < 0.35
        tt = max(0.0, t)
        p = POUSO + Vector((0, 0, 0.0)) + vel_t[k] * tt + 0.5 * G * tt * tt
        p.z = max(p.z, 0.01)
        o.location = p
        o.keyframe_insert('location', frame=q)
        o.hide_render = o.hide_viewport = not viva
        o.keyframe_insert('hide_render', frame=q)
    # dosadoras: bombeiam enquanto a bandeja está parada na estação 180°
    for i, (x, has) in enumerate(pistoes):
        ativa = 0.36 <= fr <= 0.92
        c = 0.5 - 0.5 * math.cos(2 * PI * 4 * (fr - 0.36) + i * PI) if ativa else 0.0
        y = CRUZ_Y[0] + (CRUZ_Y[1] - CRUZ_Y[0]) * c
        pose(has, Matrix.Translation((x, y, Z_DOS)), q)
    for o, i, k in pingos:
        u = (k / 2 + fr * 6 + i * 0.25) % 1.0
        ativa = 0.38 <= fr <= 0.92
        o.location = BICOS[i] + Vector((0, 0, -0.065 - 0.06 * u * u))
        o.keyframe_insert('location', frame=q)
        o.hide_render = o.hide_viewport = not ativa
        o.keyframe_insert('hide_render', frame=q)
    # aspersores: 2 voltas no laço; gotas saem dos bicos em cone
    for i, h in enumerate(cab_asp):
        ang = 2 * PI * 2 * fr * (1 if i == 0 else -1)
        pose(h, Matrix.Translation(ASP[i]) @ Matrix.Rotation(ang, 4, 'Z'), q)
        nevoas[i].rotation_euler = (0, 0, ang * 0.5)
        nevoas[i].keyframe_insert('rotation_euler', frame=q)
    for o, i, k in gotas:
        u = (k / 14 + fr * 3) % 1.0
        aa = k * 2 * PI / 14 * 3 + 2 * PI * 2 * fr * (1 if i == 0 else -1)
        r = 0.08 + 0.2 * u
        o.location = ASP[i] + Vector((r * math.cos(aa), r * math.sin(aa), -0.03 - 0.55 * u * u))
        o.keyframe_insert('location', frame=q)
    # bolhas no visor do tanque
    for k, o in enumerate(bolhas):
        u = (k / 4 + fr * 2) % 1.0
        o.location = VISOR_BOLHAS[0].lerp(VISOR_BOLHAS[1], u) + Vector((0, 0.004 * math.sin(k * 3 + u * 9), 0))
        o.keyframe_insert('location', frame=q)
    # sementes flutuando no campo: espiral subindo
    for k, o in enumerate(sementes):
        u = (k / len(sementes) + fr) % 1.0
        th = math.radians(35 + 110 * ((k * 0.618) % 1.0)) + 0.6 * u
        r = 0.3 + 0.25 * ((k * 0.37) % 1.0) + 0.04 * math.sin(2 * PI * u * 2 + k)
        o.location = C + Vector((r * math.cos(th), r * math.sin(th), 0.56 + 0.42 * u))
        o.rotation_euler = (0.4 * math.sin(2 * PI * u + k), 0.3, 2 * PI * u * 2 + k)
        o.scale = [max(0.05, math.sin(PI * u))] * 3
        for c in ('location', 'rotation_euler', 'scale'):
            o.keyframe_insert(c, frame=q)
    # antena gira 1 volta
    pose(antena, Matrix.Translation(ANT + Vector((0, 0, 0.27))) @ Matrix.Rotation(2 * PI * fr, 4, 'Z'), q)

# luzes animadas: campo pulsa, barra norte falha
campo_forca = base3d.M['campo'].node_tree.nodes['forca'].inputs[1]
falha = base3d.M['cresce_falha'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    campo_forca.default_value = 8.0 + 3.0 * math.sin(2 * PI * 2 * fr)
    campo_forca.keyframe_insert('default_value', frame=q)
    falha.default_value = 0.6 if q in (12, 13, 40, 71, 72, 73) else 9.0
    falha.keyframe_insert('default_value', frame=q)

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
for i, k in enumerate((0, 2, 6)):                                        # luz do anel de crescimento
    ld = bpy.data.lights.new('Cresce%d' % i, 'AREA')
    ld.shape, ld.size, ld.size_y = 'RECTANGLE', 0.06, 0.32
    ld.color = (1.0, 0.5, 0.85)
    ld.energy = 7.0
    lo = bpy.data.objects.new('Cresce%d' % i, ld)
    sc.collection.objects.link(lo)
    lo.location = V(45 * k, R_LUZ * math.cos(PI / 8), Z_LUZ - 0.01)
    lo.rotation_euler = (0, 0, math.radians(45 * k))
lc = bpy.data.lights.new('Campo', 'POINT')
lc.color = (0.6, 0.35, 1.0)
lc.energy = 14.0
lc.shadow_soft_size = 0.3
lco = bpy.data.objects.new('Campo', lc)
sc.collection.objects.link(lco)
lco.location = C + Vector((0, 0.42, 0.85))
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
sc.cycles.transparent_max_bounces = 24
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


ALVO = (0.2, -0.1, 0.75)
FR_FOTO = int(QUADROS * 0.845) + 1                                         # cápsula no ar, dosadoras bombeando
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
if modo == 'checar':
    def dseg(p, a, b):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        return (a + ab * t - p).length
    obst = {'pilone_L': [V(18, R_P, z / 20) for z in range(2, 21)],
            'pilar_L': [V(-22.5, R8, z / 20) for z in range(2, 23)],
            'pilar_S': [V(-67.5, R8, z / 20) for z in range(2, 23)],
            'beiral_SE': [V(-22.5, R8, ZE + 0.035).lerp(V(-67.5, R8, ZE + 0.035), u / 20) for u in range(21)],
            'beiral_L': [V(-22.5, R8, ZE + 0.035).lerp(V(22.5, R8, ZE + 0.035), u / 20) for u in range(21)],
            'beiral_S': [V(-67.5, R8, ZE + 0.035).lerp(V(-112.5, R8, ZE + 0.035), u / 20) for u in range(21)],
            'tanque_topo': [Vector((0.0, 0.0, 0.0))],
            'armario': [Vector((0.84, -0.4 - 0.22 * u / 10, 0.36)) for u in range(11)],
            'anel_luz': [V(a, R_LUZ, Z_LUZ) for a in range(-90, 90, 5)]}
    for nome, pts in obst.items():
        mn = (9, 0)
        for q in range(1, QUADROS + 1):
            fr = (q - 1) / QUADROS
            Mt, Ms, Ma, Mp, gr = matrizes(fr)
            S, E, W = Mt.to_translation(), Ma.to_translation(), Mp.to_translation()
            Gp = (Mp @ Matrix.Translation((LG + 0.03, 0, 0))).to_translation()
            for p in pts:
                d = min(dseg(p, S, E), dseg(p, E, W), dseg(p, W, Gp))
                if d < mn[0]:
                    mn = (d, fr)
        print('CHECAR %s: menor distância %.3f m em fr %.2f' % (nome, mn[0], mn[1]))
    print('P_SOLTA', P_SOLTA, 'V0', V0)
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
    sc.frame_set(FR_FOTO)
    for i, (ang, alt) in enumerate(((300, 2.0), (210, 2.2), (120, 2.4), (30, 1.8))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.6, math.sin(a) * 4.6, alt)), ALVO, 34)
        sc.render.filepath = os.path.join(AQUI, 'viveiro_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        sc.frame_set(int(QUADROS * 0.42) + 1)                               # garra fechando na cápsula; dosadoras bombeando
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((0.8, -1.2, 1.15), (0.1, 0.1, 0.6), 25)
        sc.render.filepath = os.path.join(AQUI, 'viveiro_perto.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'viveiro_teste.png')
    bpy.ops.render.render(write_still=True)
print('VIVEIRO ok')
