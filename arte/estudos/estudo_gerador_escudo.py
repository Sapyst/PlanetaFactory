"""Estudo isolado (fora do jogo): GERADOR DE ESCUDO (`escudo_1`), 2×2 tiles, sem portas de item (só energia da rede).
Cria uma bolha de 8 a 12 m que absorve dano e consome energia.
Base blindada octogonal (amarelo gasto, chapas de blindagem aparafusadas, uma trocada em zarcão, grelhas de ventilação)
alimentada assim: rede (eletroduto sul) → transformador com aletas e buchas de porcelana (sudeste) → eletrocalha →
banco de capacitores (oeste, um deles ESTUFADO, queimado e soltando fumaça e faísca) → base. Refrigeração: radiador
com duas ventoinhas girando (norte) e canos até a camisa da base. Hidráulica: central com tanque, bomba e motor (leste)
→ mangueiras → distribuidor na base → quatro pistões que inclinam os quatro emissores (braços com prato e bobina).
No meio, a coluna-bobina sobe até a taça emissora; o cristal da IA flutua preso por nada dentro de três anéis de
bobina num cardã que gira em três eixos; um fio de luz sobe do cristal até o topo da bolha.
Bolha: cúpula hexagonal translúcida violeta (linhas mais fortes que a membrana), ondulando; impactos (cuspe ácido de
aranha e projétil) acendem anéis âmbar que se espalham pelos hexágonos, com respingos de ácido escorrendo e faíscas.
Blocos simples de máquina em volta, dentro da bolha.
Animação (laço de 4 s): cardã gira, cristal pulsa, pistões ajustam os emissores, ventoinhas giram, fumaça, impactos.
Uso: blender -b --python estudo_gerador_escudo.py -- foto [0|perto|bolha]
     blender -b --python estudo_gerador_escudo.py -- teste x y z ax ay az lente fr"""
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
no = mats.no


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


def feixe(bc, ba, pts, lat, n=3, r=0.014, passo=4):
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


def torno(bm, c, perfil, lados=24):
    """Sólido de revolução em z: perfil = [(z, r), ...] de baixo para cima, com tampas."""
    aneis = []
    for z, r in perfil:
        aneis.append([bm.verts.new(Vector(c) + Vector((r * math.cos(k * 2 * PI / lados), r * math.sin(k * 2 * PI / lados), z)))
                      for k in range(lados)])
    for A, B_ in zip(aneis, aneis[1:]):
        for k in range(lados):
            bm.faces.new((A[k], A[(k + 1) % lados], B_[(k + 1) % lados], B_[k]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])


def mancha_em(bm, centro, r, n, alongar=1.0):
    """Mancha irregular colada numa face de normal n (queimado, escorrido) — alongar estica na vertical."""
    n = Vector(n).normalized()
    rot = n.to_track_quat('Z', 'Y').to_matrix()
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=14, radius=r)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.35 * math.sin(a * 3 + random.random()) + 0.15 * random.random()
        loc = Vector((v.co.x * f, v.co.y * f * alongar, 0))
        v.co = Vector(centro) + rot @ loc + n * 0.0015


def parafusos_em(bm, pts, n, r=0.008):
    for p in pts:
        cil(bm, Vector(p) + Vector(n) * 0.004, r, 0.008, Vector(n), lados=6)


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


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.16, 0.03, 0.5, 1)
    b.inputs['Roughness'].default_value = 0.15
    b.inputs['Transmission Weight'].default_value = 0.45
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 2.0
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 6.0})
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.2})
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


def feixe_vol_mat(nome, cor, dens, emis):
    """Volume que brilha mais no eixo (cilindro unitário): feixe de energia."""
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
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    xy = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], xy.inputs['X'])
    nt.links.new(sep.outputs['Y'], xy.inputs['Y'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(xy.outputs[0], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.1})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
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


def fumaca_grad_mat(nome, dens, z0, z1):
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.012, 0.011, 0.011, 1)
    mix.inputs[7].default_value = (0.42, 0.42, 0.43, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


VIOLETA = (0.55, 0.22, 1.0)
AMBAR = (1.0, 0.42, 0.04)


def bolha_mat(nome, base_fac, ganho_fac, forca, ruido):
    """Membrana do escudo: transparente no centro, mais forte na borda (fresnel), brilho violeta tremulando."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*VIOLETA, 1)
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    lw = no(nt, 'ShaderNodeLayerWeight', **{'Blend': 0.35})
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(lw.outputs['Facing'], f.inputs[0])
    f.inputs[1].default_value = ganho_fac
    f.inputs[2].default_value = base_fac
    nt.links.new(f.outputs[0], mix.inputs[0])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', name='tremor', noise_dimensions='4D', **{'Scale': 0.35, 'Detail': 2.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    s = no(nt, 'ShaderNodeMapRange', **{'To Min': forca * (1 - ruido), 'To Max': forca * (1 + ruido)})
    nt.links.new(ru.outputs['Fac'], s.inputs['Value'])
    nt.links.new(s.outputs['Result'], em.inputs['Strength'])
    return m


def impacto_mat(nome, P, forca, TH=0.55):
    """Anéis de impacto: em volta do ponto P (direção), anéis âmbar que se abrem com a `fase` (0 → 1) e somem."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new

    def mt(op, a, b=None, c=None):
        n = no(nt, 'ShaderNodeMath', operation=op)
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L(x, n.inputs[i])
        return n.outputs[0]

    out = no(nt, 'ShaderNodeOutputMaterial')
    geo = no(nt, 'ShaderNodeNewGeometry')
    nrm = no(nt, 'ShaderNodeVectorMath', operation='NORMALIZE')
    L(geo.outputs['Position'], nrm.inputs[0])
    dot = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    L(nrm.outputs[0], dot.inputs[0])
    dot.inputs[1].default_value = Vector(P).normalized()
    th = mt('ARCCOSINE', dot.outputs['Value'])
    t = mt('DIVIDE', th, TH)
    fase = no(nt, 'ShaderNodeValue', name='fase')
    fase.outputs[0].default_value = -1.0
    p = fase.outputs[0]
    total = None
    for k in range(3):
        c = mt('SUBTRACT', p, 0.2 * k)
        g = mt('MAXIMUM', mt('SUBTRACT', 1.0, mt('DIVIDE', mt('ABSOLUTE', mt('SUBTRACT', t, c)), 0.05)), 0.0)
        viva = mt('MULTIPLY', mt('GREATER_THAN', c, 0.0), mt('MAXIMUM', mt('SUBTRACT', 1.0, c), 0.0))
        g = mt('MULTIPLY', g, viva)
        total = g if total is None else mt('ADD', total, g)
    flash = mt('MULTIPLY', mt('MAXIMUM', mt('SUBTRACT', 1.0, mt('DIVIDE', t, 0.16)), 0.0),
               mt('MULTIPLY', mt('MAXIMUM', mt('SUBTRACT', 1.0, mt('MULTIPLY', p, 2.5)), 0.0), mt('GREATER_THAN', p, 0.0)))
    inten = mt('ADD', total, mt('MULTIPLY', flash, 2.5))
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.5, 0.12, 1)
    L(mt('MULTIPLY', inten, forca), em.inputs['Strength'])
    mix = no(nt, 'ShaderNodeMixShader')
    L(mt('MINIMUM', mt('MULTIPLY', inten, 0.9), 1.0), mix.inputs[0])
    L(tr.outputs[0], mix.inputs[1])
    L(em.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs['Surface'])
    return m


R_BOLHA = 8.0
IMP_A = Vector((math.cos(math.radians(268)) * math.cos(math.radians(26)), math.sin(math.radians(268)) * math.cos(math.radians(26)),
                math.sin(math.radians(26))))        # cuspe ácido de aranha (sul, baixo)
IMP_B = Vector((math.cos(math.radians(318)) * math.cos(math.radians(48)), math.sin(math.radians(318)) * math.cos(math.radians(48)),
                math.sin(math.radians(48))))        # projétil (sudeste, alto)

base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.9, ferrugem=0.4),
    'zarcao': mats.material('Zarcão', (0.36, 0.08, 0.04), 0, 0.6, desgaste=0.6, sujeira=0.9, ferrugem=0.5),
    'verde_oliva': mats.material('Verde trocado', (0.16, 0.2, 0.1), 0, 0.55, desgaste=0.8, sujeira=0.9, ferrugem=0.4),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.75, sujeira=0.85),
    'capacitor': mats.material('Capacitor', (0.12, 0.15, 0.2), 0, 0.45, desgaste=0.7, sujeira=0.9, ferrugem=0.3),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'aluminio': mats.material('Alumínio', (0.6, 0.6, 0.6), 1.0, 0.35, pintura=False, sujeira=0.8),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'bobina': mats.material('Bobina', (0.78, 0.4, 0.2), 1.0, 0.25, pintura=False, sujeira=0.5),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.27, 0.25, 0.22), 0, 0.92, sujeira=0.3, desgaste=0.0),
    'porcelana': mats.material('Porcelana', (0.42, 0.19, 0.09), 0, 0.2, pintura=False, sujeira=0.7, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'mangueira': mats.material('Mangueira', (0.03, 0.03, 0.032), 0, 0.7, pintura=False, sujeira=0.8, desgaste=0.0),
    'isol_verm': mats.material('Isolador vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.5, sujeira=0.8),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.035, 0.03, 0.028), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'eletrolito': mats.material('Eletrólito', (0.06, 0.04, 0.015), 0, 0.1, pintura=False, sujeira=0.0, desgaste=0.0),
    'crosta': mats.material('Crosta', (0.6, 0.58, 0.48), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'tinta': mats.material('Estêncil', (0.55, 0.53, 0.48), 0, 0.7, desgaste=0.9, sujeira=0.9),
    'pedra': mats.material('Pedra', (0.3, 0.27, 0.23), 0, 0.9, sujeira=0.5, desgaste=0.0),
    'bloco': mats.material('Bloco', (0.5, 0.4, 0.12), 0, 0.5, desgaste=0.8, sujeira=0.9, ferrugem=0.3),
    'bloco_cinza': mats.material('Bloco cinza', (0.25, 0.26, 0.27), 0, 0.55, desgaste=0.7, sujeira=0.9, ferrugem=0.4),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'cristal': cristal_mat(),
    'oleo_visor': vidro_mat('Óleo no visor', (0.35, 0.2, 0.03), 0.3),
    'lente': emissivo('Lente do emissor', VIOLETA, 9.0, (0.1, 0.03, 0.2)),
    'taca': emissivo('Taça', VIOLETA, 12.0),
    'arco': emissivo('Arco', (0.75, 0.55, 1.0), 18.0),
    'faisca': emissivo('Faísca', (1.0, 0.65, 0.25), 60.0),
    'brasa': emissivo('Brasa', (1.0, 0.3, 0.04), 6.0, (0.05, 0.02, 0.01)),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'led_verm': emissivo('Led vermelho', (1.0, 0.05, 0.02), 12.0),
    'olho': emissivo('Olho do sensor', VIOLETA, 8.0, (0.05, 0.02, 0.1)),
    'fio_luz': emissivo('Fio de luz', (0.6, 0.3, 1.0), 6.0),
    'acido': emissivo('Ácido', (0.5, 0.9, 0.05), 1.4, (0.35, 0.6, 0.02)),
    'projetil': mats.material('Projétil', (0.5, 0.36, 0.15), 1.0, 0.3, pintura=False, sujeira=0.5),
    'feixe_luz': feixe_vol_mat('Feixe', VIOLETA, 3.0, 8.0),
    'membrana': bolha_mat('Membrana', 0.025, 0.38, 2.2, 0.6),
    'linha': bolha_mat('Linha hexagonal', 0.55, 0.4, 7.0, 0.35),
    'imp_a': impacto_mat('Impacto A', IMP_A, 9.0),
    'imp_a_linha': impacto_mat('Impacto A linha', IMP_A, 26.0),
    'imp_b': impacto_mat('Impacto B', IMP_B, 9.0),
    'imp_b_linha': impacto_mat('Impacto B linha', IMP_B, 26.0),
    'fumaca': fumaca_grad_mat('Fumaça', 16.0, 0.7, 2.2),
    'vapor_acido': base3d.volume_mat('Vapor ácido', (0.75, 0.8, 0.55), 3.0, -50, 50),
})

# ------------------------------------------------------------------ medidas
Z0 = 0.08                      # topo da laje
APO = 0.40                     # apótema da base blindada
Z_PT = 0.43                    # topo da base
CC = Vector((0, 0, 1.58))      # centro do cristal e do cardã
R_AN = (0.36, 0.30, 0.24)      # anéis do cardã (externo, meio, interno)
DIAG = [Vector((math.cos(PI / 4 + k * PI / 2), math.sin(PI / 4 + k * PI / 2), 0)) for k in range(4)]   # NE, NO, SO, SE

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-0.985, s * 0.985 - 0.012, 0.0), (0.985, s * 0.985 + 0.012, Z0 + 0.002))
    caixa_de(bm, (s * 0.985 - 0.012, -0.985, 0.0), (s * 0.985 + 0.012, 0.985, Z0 + 0.002))
for sx in (-1, 1):                                                         # chumbadores nos cantos
    for sy in (-1, 1):
        for k in range(2):
            cil(B('parafusos', 'aco'), Vector((sx * (0.93 - 0.05 * k), sy * 0.93, Z0 + 0.006)), 0.012, 0.014, lados=6)

# ------------------------------------------------------------------ base blindada
bm = B('base', 'amarelo')
octo(bm, Vector((0, 0, 0)), APO + 0.03, Z0, Z0 + 0.05)                    # sapata
octo(bm, Vector((0, 0, 0)), APO, Z0 + 0.05, Z_PT - 0.02)
bm = B('base_tampa', 'grafite')
octo(bm, Vector((0, 0, 0)), APO + 0.012, Z_PT - 0.02, Z_PT)
R8 = (APO + 0.012) / math.cos(PI / 8)
for k in range(16):                                                        # parafusos da tampa
    a = PI / 8 + k * PI / 8
    rr = R8 * 0.92 if k % 2 == 0 else (APO + 0.012) * 0.92
    cil(B('parafusos', 'aco'), Vector((math.cos(a) * rr, math.sin(a) * rr, Z_PT + 0.004)), 0.01, 0.01, lados=6)
# chapas de blindagem nas 8 faces (uma trocada em zarcão, uma em verde, uma faltando com remendo)
for k in range(8):
    a = k * PI / 4
    n = Vector((math.cos(a), math.sin(a), 0))
    R = rot_face(n)
    larg = 2 * APO * math.tan(PI / 8) - 0.05
    mat = 'casco'
    if k == 3:
        mat = 'zarcao'
    elif k == 6:
        mat = 'verde_oliva'
    c = n * (APO + 0.012) + Vector((0, 0, 0.27))
    if k == 5:                                                             # chapa faltando: remendo menor torto
        caixa(B('chapas_' + mat, mat), c + R @ Vector((0.03, 0, 0.02)), (larg * 0.55, 0.018, 0.16),
              R @ Matrix.Rotation(0.12, 3, 'Y'))
        parafusos_em(B('parafusos', 'aco'), [c + R @ Vector((sx * larg * 0.22 + 0.03, 0.01, sz * 0.06 + 0.02)) for sx in (-1, 1) for sz in (-1, 1)], n)
        for sx in (-1, 1):                                                 # furos dos parafusos que sobraram
            for sz in (-1, 1):
                cil(B('furos', 'escuro'), c + R @ Vector((sx * larg * 0.44, 0.001, sz * 0.12)), 0.007, 0.004, n, lados=6)
        continue
    caixa(B('chapas_' + mat, mat), c, (larg, 0.024, 0.26), R)
    pts = [c + R @ Vector((sx * larg * 0.44, 0.012, sz * 0.11)) for sx in (-1, 0, 1) for sz in (-1, 1)]
    parafusos_em(B('parafusos', 'aco'), pts, n)
    if k in (0, 4):                                                        # grelha de ventilação
        for j in range(6):
            caixa(B('grelha', 'escuro'), c + R @ Vector((0, 0.013, -0.06 + j * 0.025)), (larg * 0.6, 0.004, 0.01), R)
            caixa(B('grelha_aletas', 'ferro'), c + R @ Vector((0, 0.018, -0.052 + j * 0.025)), (larg * 0.62, 0.006, 0.006),
                  R @ Matrix.Rotation(0.6, 3, 'X'))
# queimado de sobrecarga na face oeste (do lado dos capacitores) subindo pela tampa
for j in range(5):
    mancha_em(B('chamusco', 'chamusco'), Vector((-APO - 0.025, random.uniform(-0.12, 0.12), 0.16 + j * 0.05)),
              random.uniform(0.03, 0.06), Vector((-1, 0, 0)), alongar=1.6)
for j in range(5):
    mancha(B('chamusco', 'chamusco'), (random.uniform(-0.38, -0.2), random.uniform(-0.18, 0.18)), random.uniform(0.03, 0.06), Z_PT + 0.0012)
for j in range(4):                                                         # fuligem e ferrugem escorrendo nas chapas
    a = random.choice((1, 2, 7)) * PI / 4
    n = Vector((math.cos(a), math.sin(a), 0))
    mancha_em(B('escorridos', 'ferrugem'), n * (APO + 0.026) + Vector((0, 0, 0.22)) + rot_face(n) @ Vector((random.uniform(-0.08, 0.08), 0, 0)),
              0.018, n, alongar=4.0)
# estêncil gasto na chapa sul
txt = bpy.data.curves.new('estencil', 'FONT')
txt.body = 'ESC-01  Nº 4471'
txt.size = 0.035
txt.align_x = 'CENTER'
to = bpy.data.objects.new('estencil', txt)
sc.collection.objects.link(to)
to.data.materials.append(base3d.M['tinta'])
to.location = (0, -APO - 0.0255, 0.3)
to.rotation_euler = (PI / 2, 0, 0)
txt2 = bpy.data.curves.new('estencil2', 'FONT')
txt2.body = '⚠ ALTA TENSÃO'
txt2.size = 0.03
txt2.align_x = 'CENTER'
to2 = bpy.data.objects.new('estencil2', txt2)
sc.collection.objects.link(to2)
to2.data.materials.append(base3d.M['tinta'])
to2.location = (0, -APO - 0.0255, 0.215)
to2.rotation_euler = (PI / 2, 0, 0)

# ------------------------------------------------------------------ coluna-bobina e taça emissora
bm = B('coluna_caixa', 'grafite', True)
cil(bm, Vector((0, 0, Z_PT + 0.1)), 0.13, 0.2, lados=32)
cil(B('coluna_flanges', 'aco', True), Vector((0, 0, Z_PT + 0.012)), 0.16, 0.024, lados=32)
cil(B('coluna_flanges', 'aco', True), Vector((0, 0, Z_PT + 0.2)), 0.145, 0.022, lados=32)
for k in range(12):
    a = k * PI / 6
    cil(B('parafusos', 'aco'), Vector((math.cos(a) * 0.148, math.sin(a) * 0.148, Z_PT + 0.026)), 0.008, 0.008, lados=6)
cil(B('coluna_nucleo', 'ferro', True), Vector((0, 0, 0.85)), 0.065, 0.48, lados=24)
z = Z_PT + 0.23
while z < 1.03:
    toro(B('bobina', 'bobina', True), Vector((0, 0, z)), 0.083, 0.0095, 40, 8)
    z += 0.019
for k in range(4):                                                         # réguas que seguram as espiras
    a = k * PI / 2
    caixa(B('reguas', 'porcelana'), Vector((math.cos(a), math.sin(a), 0)) * 0.097 + Vector((0, 0, 0.85)),
          (0.016, 0.016, 0.4), Matrix.Rotation(a, 3, 'Z'))
cil(B('coluna_flanges', 'aco', True), Vector((0, 0, 1.06)), 0.12, 0.024, lados=32)
bm = B('taca', 'ferro', True)
torno(bm, Vector((0, 0, 0)), [(1.07, 0.06), (1.12, 0.07), (1.2, 0.15), (1.215, 0.155)], 32)
toro(B('taca_aro', 'bobina', True), Vector((0, 0, 1.215)), 0.155, 0.011, 48, 10)
cil(B('taca_luz', 'taca'), Vector((0, 0, 1.2)), 0.1, 0.01, lados=32)
for k in range(6):                                                         # dedos de contato da taça
    a = k * PI / 3 + PI / 6
    d = Vector((math.cos(a), math.sin(a), 0))
    tubo(B('taca_dedos', 'cromo', True), d * 0.13 + Vector((0, 0, 1.2)), d * 0.11 + Vector((0, 0, 1.29)), 0.008, 10)
    curva(B('taca_dedos', 'cromo', True), d * 0.11 + Vector((0, 0, 1.29)), 0.012, 12)
# cabo de terra/sinal descendo pela coluna até a caixa
pts = bezier(Vector((0.1, 0.06, 1.05)), Vector((0.14, 0.09, 0.9)), Vector((0.15, 0.1, 0.75)), Vector((0.12, 0.08, Z_PT + 0.21)), 10)
mangueira(B('cabos', 'cabo', True), pts, 0.009)
for z in (0.72, 0.9):
    caixa(B('abracadeiras', 'aco'), Vector((0.13, 0.085, z)), (0.03, 0.03, 0.012))

# ------------------------------------------------------------------ garfo do cardã
bm = B('garfo', 'amarelo', True)
for s in (-1, 1):
    pts = [Vector((s * 0.12, 0, 1.0)), Vector((s * 0.47, 0, 1.06)), Vector((s * 0.47, 0, CC.z - 0.06))]
    cano(bm, B('garfo_flanges', 'ferro', True), pts, 0.026, flange=False)
    cil(B('garfo_mancal', 'ferro', True), Vector((s * 0.47, 0, CC.z)), 0.05, 0.08, Vector((1, 0, 0)), lados=20)
    cil(B('garfo_mancal', 'ferro', True), Vector((s * 0.47, 0, CC.z - 0.04)), 0.032, 0.05, lados=16)
    cil(B('garfo_tampa', 'bobina', True), Vector((s * 0.515, 0, CC.z)), 0.032, 0.012, Vector((1, 0, 0)), lados=16)
    for k in range(4):                                                     # parafusos do mancal
        a = k * PI / 2 + PI / 4
        cil(B('parafusos', 'aco'), Vector((s * 0.512, 0.04 * math.cos(a), CC.z + 0.04 * math.sin(a))), 0.006, 0.01, Vector((1, 0, 0)), lados=6)
    caixa(B('garfo_pe', 'ferro'), Vector((s * 0.12, 0, 1.0)), (0.06, 0.07, 0.05))
    # escova de contato (graxa e cabo) no mancal
    pts = bezier(Vector((s * 0.47, 0.04, CC.z - 0.03)), Vector((s * 0.47, 0.1, CC.z - 0.15)), Vector((s * 0.47, 0.06, 1.15)),
                 Vector((s * 0.44, 0.03, 1.07)), 10)
    mangueira(B('cabos', 'cabo', True), pts, 0.01)
    mancha_em(B('oleo', 'oleo'), Vector((s * 0.47, 0, CC.z - 0.07)), 0.025, Vector((0, -1, 0)), alongar=2.5)

# ------------------------------------------------------------------ banco de capacitores (oeste)
CAPS = [Vector((x, y, 0)) for x in (-0.85, -0.65) for y in (-0.48, -0.16, 0.16, 0.48)]
ESTUFADO = Vector((-0.85, 0.16, 0))
Z_C0, Z_C1 = 0.13, 0.62
bm = B('rack', 'grafite')
caixa_de(bm, (-0.96, -0.62, Z0), (-0.54, 0.62, Z_C0))
for x in (-0.95, -0.55):
    for y in (-0.61, 0.61):
        viga(B('rack_postes', 'amarelo'), Vector((x, y, Z_C0)), Vector((x, y, 0.56)), 0.03)
    for z in (0.24, 0.5):                                                  # cintas chatas de retenção
        if x > -0.7:
            caixa_de(B('rack_cintas', 'aco'), (x - 0.006, -0.62, z - 0.02), (x + 0.006, 0.62, z + 0.02))
            continue
        # lado de fora: a cinta foi empurrada pelo capacitor estufado (dobra para fora)
        ys = [(-0.62, x), (0.0, x), (0.07, x - 0.042), (0.25, x - 0.042), (0.32, x), (0.62, x)]
        for (y1, x1), (y2, x2) in zip(ys, ys[1:]):
            L = math.hypot(x2 - x1, y2 - y1)
            caixa(B('rack_cintas', 'aco'), Vector(((x1 + x2) / 2, (y1 + y2) / 2, z)), (0.012, L + 0.006, 0.04),
                  Matrix.Rotation(math.atan2(-(x2 - x1), y2 - y1), 3, 'Z'))
for y in (-0.61, 0.61):
    caixa_de(B('rack_cintas', 'aco'), (-0.95, y - 0.006, 0.48), (-0.55, y + 0.006, 0.52))
for x in (-0.95, -0.55):
    for z in (0.24, 0.5):
        parafusos_em(B('parafusos', 'aco'), [Vector((x + (0.007 if x > -0.7 else -0.007), y, z)) for y in (-0.4, 0.0, 0.4)],
                     Vector((1 if x > -0.7 else -1, 0, 0)))
for C in CAPS:
    est = (C - ESTUFADO).length < 0.01
    if est:
        # corpo estufado: incha para fora (-x, onde há folga) e quase nada para o vizinho (+x)
        def bojo(z, th):
            u = min(1.0, max(0.0, (z - Z_C0) / 0.47))
            return 0.085 + 0.04 * math.sin(PI * u) ** 0.8 * (1 - 0.75 * max(0.0, math.cos(th)))
        bmc = B('capacitores', 'capacitor', True)
        zs = [Z_C0] + [Z_C0 + 0.47 * u for u in (0.08, 0.2, 0.35, 0.5, 0.65, 0.8, 0.92)] + [Z_C1 - 0.01]
        aneis = [[bmc.verts.new(C + Vector((bojo(z, k * 2 * PI / 28) * math.cos(k * 2 * PI / 28),
                                             bojo(z, k * 2 * PI / 28) * math.sin(k * 2 * PI / 28), z))) for k in range(28)] for z in zs]
        aneis.append([bmc.verts.new(C + Vector((0.08 * math.cos(k * 2 * PI / 28), 0.08 * math.sin(k * 2 * PI / 28), Z_C1))) for k in range(28)])
        for A_, B_ in zip(aneis, aneis[1:]):
            for k in range(28):
                bmc.faces.new((A_[k], A_[(k + 1) % 28], B_[(k + 1) % 28], B_[k]))
        bmc.faces.new(list(reversed(aneis[0])))
        bmc.faces.new(aneis[-1])
        # cinta de cima arrebentada: só um pedaço pendurado
        caixa(B('cap_cintas', 'aco'), C + Vector((0.07, -0.06, Z_C1 - 0.09)), (0.04, 0.004, 0.016), Matrix.Rotation(-0.7, 3, 'Z') @ Matrix.Rotation(0.6, 3, 'Y'))
        torno(B('cap_topo_queimado', 'fuligem', True), C, [(Z_C1, 0.08), (Z_C1 + 0.02, 0.07), (Z_C1 + 0.04, 0.045), (Z_C1 + 0.045, 0.001)], 28)
        # tampa rasgada (pétalas do respiro de segurança abertas)
        for k in range(4):
            a = k * PI / 2 + 0.3
            d = Vector((math.cos(a), math.sin(a), 0))
            caixa(B('cap_petalas', 'aluminio'), C + d * 0.03 + Vector((0, 0, Z_C1 + 0.05)), (0.03, 0.003, 0.03),
                  rot_face(d) @ Matrix.Rotation(-0.7, 3, 'X'))
        curva(B('cap_crosta', 'crosta'), C + Vector((0.01, 0, Z_C1 + 0.04)), 0.028, 10)
        curva(B('cap_brasa', 'brasa'), C + Vector((0.0, 0.01, Z_C1 + 0.046)), 0.012, 10)
        for j in range(3):                                                 # eletrólito escorrendo pelo corpo
            a = PI * 0.9 + j * 0.35
            n = Vector((math.cos(a), math.sin(a), 0))
            zz = 0.5 - j * 0.07
            mancha_em(B('eletrolito', 'eletrolito'), C + n * (bojo(zz, a) + 0.001) + Vector((0, 0, zz)), 0.009, n, alongar=5.0)
        mancha(B('eletrolito', 'eletrolito'), (C.x + 0.04, C.y + 0.05), 0.07, Z_C0 + 0.001)
    else:
        torno(B('capacitores', 'capacitor', True), C, [(Z_C0, 0.085), (Z_C1 - 0.015, 0.085), (Z_C1, 0.08)], 28)
        cil(B('cap_tampa', 'aluminio', True), C + Vector((0, 0, Z_C1 + 0.006)), 0.078, 0.012, lados=28)
    for z in ((Z_C0 + 0.025,) if est else (Z_C0 + 0.04, Z_C1 - 0.05)):    # cintas
        cil(B('cap_cintas', 'aco', True), C + Vector((0, 0, z)), 0.089 if not est else bojo(z + 0.008, PI) + 0.004, 0.016, lados=28)
    for s in (-1, 1):                                                      # terminais
        p = C + Vector((0, s * 0.035, Z_C1 + 0.012))
        if est:
            p = p + Vector((0.0, s * 0.008, 0.035))
        cil(B('cap_terminais', 'porcelana', True), p + Vector((0, 0, 0.015)), 0.014, 0.03, lados=12)
        cil(B('cap_bornes', 'cobre', True), p + Vector((0, 0, 0.04)), 0.008, 0.025, lados=8)
        cil(B('cap_bornes', 'aco', True), p + Vector((0, 0, 0.045)), 0.011, 0.006, lados=6)
# barramentos de cobre ligando os terminais em cada fileira
for x in (-0.85, -0.65):
    for s in (-1, 1):
        caixa_de(B('barramentos', 'cobre'), (x - 0.012, -0.5 + s * 0.035, Z_C1 + 0.06), (x + 0.012, 0.5 + s * 0.035, Z_C1 + 0.068))
for y in (-0.48, 0.48):
    caixa_de(B('barramentos', 'cobre'), (-0.862, y - 0.05, Z_C1 + 0.07), (-0.638, y - 0.02, Z_C1 + 0.078))
for y in (-0.3, 0.0, 0.3):                                                 # separadores isolantes
    caixa(B('barras_isol', 'isol_verm'), Vector((-0.75, y, Z_C1 + 0.066)), (0.26, 0.022, 0.026))
# fuligem subindo nos vizinhos do estufado
for C in (Vector((-0.85, 0.48, 0)), Vector((-0.85, -0.16, 0)), Vector((-0.65, 0.16, 0))):
    n = (ESTUFADO - C)
    n = Vector((n.x, n.y, 0)).normalized()
    for j in range(3):
        for i in range(4):
            lat = Vector((-n.y, n.x, 0)) * random.uniform(-0.035, 0.035)
            mancha_em(B('fuligem', 'fuligem'), C + n * 0.087 + lat + Vector((0, 0, 0.4 + j * 0.06 + random.uniform(0, 0.04))),
                      random.uniform(0.006, 0.013), n, alongar=1.6)
for j in range(6):
    mancha(B('chamusco', 'chamusco'), (ESTUFADO.x + random.uniform(-0.15, 0.15), ESTUFADO.y + random.uniform(-0.15, 0.15)),
           random.uniform(0.02, 0.05), Z_C1 + 0.08)
# caixa de junção do banco (sul do rack)
bm = B('caixa_cap', 'amarelo')
caixa_de(bm, (-0.86, -0.72, Z0), (-0.62, -0.63, 0.46))
caixa_de(B('caixa_cap_tampa', 'grafite'), (-0.85, -0.727, 0.12), (-0.63, -0.72, 0.44))
parafusos_em(B('parafusos', 'aco'), [Vector((x, -0.728, z)) for x in (-0.84, -0.64) for z in (0.13, 0.43)], Vector((0, -1, 0)))
cil(B('led_led_verm', 'led_verm'), Vector((-0.8, -0.73, 0.4)), 0.008, 0.006, Vector((0, -1, 0)), lados=10)
cil(B('led_led_ambar', 'led_ambar'), Vector((-0.77, -0.73, 0.4)), 0.008, 0.006, Vector((0, -1, 0)), lados=10)
for j in range(3):                                                         # da caixa sobe até o barramento
    x = -0.8 + j * 0.06
    pts = bezier(Vector((x, -0.68, 0.46)), Vector((x, -0.68, 0.6)), Vector((x * 0.95, -0.56, Z_C1 + 0.12)),
                 Vector((-0.75 + (j - 1) * 0.07, -0.5, Z_C1 + 0.085)), 8)
    mangueira(B('cabos', 'cabo', True), pts, 0.014)
# do banco para a base: feixe grosso por cima dos capacitores até a prensa-cabo na face oeste
for j in range(3):
    y = -0.05 + j * 0.05
    pts = bezier(Vector((-0.65, y, Z_C1 + 0.085)), Vector((-0.55, y, Z_C1 + 0.2)), Vector((-0.46, y * 0.8, 0.55)),
                 Vector((-APO - 0.06, y * 0.6, 0.32)), 12)
    mangueira(B('cabos', 'cabo', True), pts, 0.02)
caixa(B('prensa_cabo', 'ferro'), Vector((-APO - 0.045, 0, 0.32)), (0.05, 0.16, 0.08))
for j in range(3):
    cil(B('prensa_cabo', 'aco', True), Vector((-APO - 0.07, -0.03 + j * 0.03, 0.32)), 0.026, 0.03, Vector((1, 0, 0)), lados=12)
for t in (0.35, 0.65):
    pts = bezier(Vector((-0.65, 0, Z_C1 + 0.085)), Vector((-0.55, 0, Z_C1 + 0.2)), Vector((-0.46, 0, 0.55)),
                 Vector((-APO - 0.06, 0, 0.32)), 20)
    i = int(t * 20)
    u = (pts[i + 1] - pts[i - 1]).normalized()
    tubo(B('abracadeiras', 'aco', True), pts[i] - u * 0.012, pts[i] + u * 0.012, 0.075, 12)

# ------------------------------------------------------------------ transformador (sudeste) e entrada da rede
TX0, TX1, TY0, TY1 = 0.5, 0.92, -0.92, -0.54
bm = B('trafo', 'amarelo')
caixa_de(bm, (TX0, TY0, 0.13), (TX1, TY1, 0.64))
caixa_de(B('trafo_tampa', 'grafite'), (TX0 - 0.01, TY0 - 0.01, 0.64), (TX1 + 0.01, TY1 + 0.01, 0.665))
for x in (TX0 + 0.06, TX1 - 0.06):                                         # trilhos de apoio
    caixa_de(B('trafo_skid', 'ferro'), (x - 0.03, TY0 - 0.02, Z0), (x + 0.03, TY1 + 0.02, 0.13))
for k in range(9):                                                         # aletas de refrigeração (leste e norte)
    y = TY0 + 0.04 + k * 0.041
    caixa_de(B('trafo_aletas', 'casco'), (TX1, y - 0.006, 0.18), (TX1 + 0.06, y + 0.006, 0.6))
    x = TX0 + 0.04 + k * 0.042
    caixa_de(B('trafo_aletas', 'casco'), (x - 0.006, TY1, 0.18), (x + 0.006, TY1 + 0.05, 0.6))
for z in (0.17, 0.61):
    caixa_de(B('trafo_aletas', 'ferro'), (TX1, TY0 + 0.02, z - 0.012), (TX1 + 0.065, TY1 - 0.02, z + 0.012))
parafusos_em(B('parafusos', 'aco'), [Vector((x, TY0 - 0.012, 0.652)) for x in (0.53, 0.62, 0.71, 0.8, 0.89)], Vector((0, 0, 1)))
# conservador de óleo
cil(B('conservador', 'amarelo', True), Vector((0.71, TY0 + 0.05, 0.78)), 0.055, 0.36, Vector((1, 0, 0)), lados=24)
for x in (0.58, 0.84):
    caixa(B('trafo_skid', 'ferro'), Vector((x, TY0 + 0.05, 0.7)), (0.03, 0.06, 0.07))
cil(B('conservador_visor', 'oleo_visor', True), Vector((0.895, TY0 + 0.05, 0.78)), 0.03, 0.012, Vector((1, 0, 0)), lados=16)
cano(B('canos', 'casco', True), B('flanges', 'ferro', True), [Vector((0.6, TY0 + 0.05, 0.73)), Vector((0.6, TY0 + 0.05, 0.665))], 0.012, flange=False)
# buchas de porcelana (secundário) no topo
TOPOS = []
for i, x in enumerate((0.6, 0.71, 0.82)):
    base = Vector((x, -0.66, 0.665))
    cil(B('porcelana', 'porcelana', True), base + Vector((0, 0, 0.11)), 0.018, 0.22, lados=14)
    for k in range(5):
        cil(B('porcelana', 'porcelana', True), base + Vector((0, 0, 0.03 + k * 0.042)), 0.036, 0.012, lados=18)
    cil(B('iso_grampo', 'cobre', True), base + Vector((0, 0, 0.245)), 0.016, 0.04, lados=12)
    cil(B('iso_grampo', 'aco', True), base + Vector((0, 0, 0.268)), 0.022, 0.01, lados=6)
    TOPOS.append(base + Vector((0, 0, 0.26)))
for j in range(4):                                                         # descarga na bucha do meio
    mancha(B('chamusco', 'chamusco'), (0.71 + random.uniform(-0.06, 0.06), -0.66 + random.uniform(-0.06, 0.06)),
           random.uniform(0.02, 0.04), 0.666)
mancha_em(B('fuligem', 'fuligem'), Vector((0.71, -0.66 + 0.037, 0.75)), 0.018, Vector((0, 1, 0)), alongar=2.0)
# vazamento de óleo do trafo
for j in range(6):                                                         # escorrido fino de óleo na junta
    mancha_em(B('oleo', 'oleo'), Vector((0.66 + 0.002 * math.sin(j * 2), TY0 - 0.001, 0.62 - j * 0.03)), 0.006 + 0.0008 * j,
              Vector((0, -1, 0)), alongar=3.0)
mancha(B('oleo', 'oleo'), (0.62, TY0 - 0.05), 0.07, Z0 + 0.001)
# placa de identificação
caixa(B('placa', 'aluminio'), Vector((0.6, TY0 - 0.003, 0.5)), (0.1, 0.004, 0.06))
for k in range(4):
    caixa(B('placa_txt', 'escuro'), Vector((0.6, TY0 - 0.006, 0.515 - k * 0.012)), (0.08 - 0.015 * (k % 2), 0.002, 0.004))
# entrada da rede: eletroduto no sul → caixa do primário (face oeste do trafo)
cil(B('eletroduto', 'ferro', True), Vector((0.32, -0.94, Z0 + 0.06)), 0.05, 0.12, lados=16)
caixa_de(B('trafo_caixa_prim', 'grafite'), (TX0 - 0.08, -0.82, 0.2), (TX0, -0.62, 0.42))
parafusos_em(B('parafusos', 'aco'), [Vector((TX0 - 0.081, y, z)) for y in (-0.81, -0.63) for z in (0.21, 0.41)], Vector((-1, 0, 0)))
for j in range(3):
    x0 = 0.3 + (j - 1) * 0.03
    pts = bezier(Vector((x0, -0.94, Z0 + 0.12)), Vector((x0, -0.94, 0.3)), Vector((TX0 - 0.15, -0.72 + (j - 1) * 0.05, 0.12)),
                 Vector((TX0 - 0.08, -0.72 + (j - 1) * 0.05, 0.24)), 10)
    mangueira(B('cabos', 'cabo', True), pts, 0.016)

# eletrocalha no chão (sul): do trafo até a caixa do banco
YE = -0.78
bm = B('eletrocalha', 'aco')
caixa_de(bm, (-0.62, YE - 0.07, Z0), (0.48, YE + 0.07, Z0 + 0.012))
for s in (-1, 1):
    caixa_de(bm, (-0.62, YE + s * 0.07 - 0.006, Z0), (0.48, YE + s * 0.07 + 0.006, Z0 + 0.075))
for x in (-0.45, -0.2, 0.05, 0.3):
    caixa_de(B('eletrocalha_pes', 'ferro'), (x - 0.02, YE - 0.09, Z0), (x + 0.02, YE + 0.09, Z0 + 0.012))
    caixa_de(B('eletrocalha_pes', 'ferro'), (x - 0.01, YE - 0.08, Z0 + 0.072), (x + 0.01, YE + 0.08, Z0 + 0.082))
for i, tp in enumerate(TOPOS):
    yy = YE + (i - 1) * 0.04
    pts = bezier(tp + Vector((-0.01, 0, 0.0)), tp + Vector((-0.12, -0.02, 0.15)), Vector((0.62, yy, 0.25)),
                 Vector((0.42, yy, Z0 + 0.04)), 12)
    pts += [Vector((0.42 - 0.12 * j, yy, Z0 + 0.04)) for j in range(1, 9)] + [Vector((-0.6, yy, Z0 + 0.04))]
    pts += bezier(Vector((-0.6, yy, Z0 + 0.04)), Vector((-0.7, yy, Z0 + 0.04)), Vector((-0.74 + (i - 1) * 0.04, -0.75, Z0 + 0.04)),
                  Vector((-0.74 + (i - 1) * 0.04, -0.72, 0.12)), 6)[1:]
    mangueira(B('cabos', 'cabo', True), pts, 0.018)
for x in (-0.4, 0.15):
    caixa(B('abracadeiras', 'aco'), Vector((x, YE, Z0 + 0.06)), (0.04, 0.15, 0.03))
for k in range(4):
    mancha(B('po', 'po'), (random.uniform(-0.5, 0.4), YE + random.uniform(-0.05, 0.05)), random.uniform(0.04, 0.07), Z0 + 0.0125)

# ------------------------------------------------------------------ radiador com ventoinhas (norte) e refrigeração
XR0, XR1, YR0, YR1 = -0.44, 0.5, 0.66, 0.78
bm = B('radiador_tanques', 'casco')
caixa_de(bm, (XR0, YR0, 0.12), (XR1, YR1, 0.2))
caixa_de(bm, (XR0, YR0, 0.78), (XR1, YR1, 0.86))
bm = B('radiador_quadro', 'amarelo')
for x in (XR0 - 0.02, XR1 + 0.02):
    caixa_de(bm, (x - 0.014, YR0 - 0.01, Z0), (x + 0.014, YR1 + 0.01, 0.87))
bm = B('radiador_aletas', 'aco')
for k in range(64):
    x = XR0 + 0.01 + k * 0.0145
    caixa_de(bm, (x - 0.002, YR0 + 0.01, 0.2), (x + 0.002, YR1 - 0.01, 0.78))
for z in (0.4, 0.6):
    caixa_de(B('radiador_quadro', 'amarelo'), (XR0, YR0 - 0.008, z - 0.01), (XR1, YR0 + 0.0, z + 0.01))
cil(B('valvula', 'ferro', True), Vector((XR1 - 0.06, 0.72, 0.89)), 0.02, 0.06, lados=12)          # respiro
cil(B('valvula', 'aco', True), Vector((XR0 + 0.05, 0.72, 0.88)), 0.035, 0.03, lados=6)            # tampa de enchimento
FANS = [Vector((x, 0.86, 0.49)) for x in (-0.2, 0.27)]
fans = []
for F in FANS:
    bm = B('fan_anel', 'grafite', True)
    bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.2, radius2=0.2, depth=0.1,
                          matrix=Matrix.Translation(F) @ Vector((0, 1, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    for s in (-1, 1):
        toro(bm, F + Vector((0, s * 0.05, 0)), 0.2, 0.008, 48, 8, Matrix.Rotation(PI / 2, 3, 'X'))
    for s in (-1, 1):
        for t in (-1, 1):
            viga(B('fan_suporte', 'ferro'), F + Vector((s * 0.14, -0.05, t * 0.14)), Vector((F.x + s * 0.16, YR1, F.z + t * 0.16)), 0.016)
    bm = B('fan_grade', 'aco')
    for r in (0.06, 0.12, 0.18):
        toro(bm, F + Vector((0, 0.065, 0)), r, 0.0035, 40, 6, Matrix.Rotation(PI / 2, 3, 'X'))
    for k in range(6):
        a = k * PI / 6
        d = Vector((math.cos(a), 0, math.sin(a)))
        tubo(bm, F + Vector((0, 0.065, 0)) - d * 0.2, F + Vector((0, 0.065, 0)) + d * 0.2, 0.003, 6)
    cil(bm, F + Vector((0, 0.065, 0)), 0.035, 0.01, Vector((0, 1, 0)), lados=16)
    caixa(B('fan_motor', 'grafite'), F + Vector((0, -0.03, 0.0)), (0.06, 0.04, 0.06))
    e = bpy.data.objects.new('ventoinha', None)
    sc.collection.objects.link(e)
    e.location = F
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.045, 0.05, Vector((0, 1, 0)), lados=16)
    for k in range(7):
        a = k * 2 * PI / 7
        R = Matrix.Rotation(a, 3, 'Y')
        caixa(bm, R @ Vector((0, 0, 0.11)), (0.085, 0.008, 0.14), R @ Matrix.Rotation(0.45, 3, 'Z'))
    obj('ventoinha_pas', bm, 'grafite', e)
    fans.append(e)
# poeira presa nas aletas e fuligem
for k in range(6):
    mancha_em(B('po', 'po'), Vector((random.uniform(XR0 + 0.05, XR1 - 0.05), YR0 - 0.001, random.uniform(0.25, 0.7))), 0.05,
              Vector((0, -1, 0)), alongar=1.3)
# canos radiador ↔ camisa da base (face norte)
for x, zr, zb in ((-0.09, 0.16, 0.2), (0.09, 0.82, 0.34)):
    pts = [Vector((x, YR0, zr)), Vector((x, 0.55, zr)), Vector((x, 0.55, zb)), Vector((x, APO + 0.03, zb))]
    cano(B('canos', 'casco', True), B('flanges', 'ferro', True), pts, 0.024)
    cil(B('flanges', 'ferro', True), Vector((x, APO + 0.035, zb)), 0.04, 0.02, Vector((0, 1, 0)), lados=16)
# bomba de refrigeração no cano de retorno
PBR = Vector((-0.09, 0.55, 0.3))
cil(B('bomba', 'amarelo', True), PBR, 0.06, 0.1, Vector((1, 0, 0)), lados=20)
cil(B('bomba_motor', 'grafite', True), PBR + Vector((-0.11, 0, 0)), 0.045, 0.12, Vector((1, 0, 0)), lados=18)
for k in range(4):
    cil(B('bomba_aletas', 'ferro', True), PBR + Vector((-0.08 - k * 0.025, 0, 0)), 0.052, 0.006, Vector((1, 0, 0)), lados=18)
caixa_de(B('bomba_pe', 'ferro'), (-0.25, 0.5, Z0), (-0.04, 0.6, 0.24))
mancha(B('oleo', 'oleo'), (-0.12, 0.56), 0.06, Z0 + 0.001)
# camisa de refrigeração da base (anel de cano em volta)
toro(B('camisa', 'casco', True), Vector((0, 0, 0.2)), APO + 0.045, 0.014, 64, 10)
toro(B('camisa', 'casco', True), Vector((0, 0, 0.34)), APO + 0.045, 0.014, 64, 10)
for k in range(8):
    a = PI / 8 + k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    R8b = (APO) / math.cos(PI / 8)
    caixa(B('camisa_suportes', 'ferro'), d * (R8b + 0.02) + Vector((0, 0, 0.27)), (0.03, 0.04, 0.17), rot_face(d))

# ------------------------------------------------------------------ central hidráulica (leste)
HX = 0.77
cil(B('hid_tanque', 'amarelo', True), Vector((HX, 0.0, 0.33)), 0.13, 0.62, Vector((0, 1, 0)), lados=28)
for y in (-0.31, 0.31):
    cil(B('hid_aros', 'ferro', True), Vector((HX, y, 0.33)), 0.135, 0.02, Vector((0, 1, 0)), lados=28)
for y in (-0.2, 0.2):
    caixa_de(B('hid_berco', 'ferro'), (HX - 0.12, y - 0.03, Z0), (HX + 0.12, y + 0.03, 0.24))
cil(B('valvula', 'aco', True), Vector((HX, 0.18, 0.47)), 0.025, 0.03, lados=6)                   # bujão
cil(B('hid_visor', 'oleo_visor', True), Vector((HX + 0.13, 0.1, 0.33)), 0.02, 0.012, Vector((1, 0, 0)), lados=14)
# bomba + motor em cima do tanque
caixa_de(B('hid_base', 'ferro'), (HX - 0.1, -0.24, 0.45), (HX + 0.1, 0.05, 0.47))
cil(B('hid_motor', 'verde_oliva', True), Vector((HX, -0.13, 0.54)), 0.065, 0.16, Vector((0, 1, 0)), lados=24)
for k in range(6):
    cil(B('hid_motor_aletas', 'ferro', True), Vector((HX, -0.19 + k * 0.024, 0.54)), 0.072, 0.006, Vector((0, 1, 0)), lados=24)
cil(B('hid_bomba', 'grafite', True), Vector((HX, -0.0, 0.54)), 0.045, 0.1, Vector((0, 1, 0)), lados=18)
caixa(B('hid_motor', 'grafite'), Vector((HX + 0.07, -0.13, 0.56)), (0.04, 0.06, 0.06))
DISTR = Vector((0.27, 0.0, Z_PT + 0.035))                                  # distribuidor na tampa da base
caixa(B('distribuidor', 'aco'), DISTR, (0.08, 0.14, 0.05))
for s in (-1, 1):
    cil(B('distribuidor_valv', 'zarcao', True), DISTR + Vector((0, s * 0.04, 0.04)), 0.014, 0.03, lados=10)
for j, s in enumerate((-1, 1)):                                            # pressão e retorno: bomba → distribuidor
    pts = bezier(Vector((HX - 0.01, 0.06, 0.54 + s * 0.02)), Vector((HX - 0.05, 0.16, 0.56 + s * 0.03)),
                 Vector((0.45, s * 0.05, 0.62)), DISTR + Vector((0.04, s * 0.03, 0.0)), 14)
    mangueira(B('mangueiras', 'mangueira', True), pts, 0.013)
mancha(B('oleo', 'oleo'), (HX - 0.05, 0.25), 0.08, Z0 + 0.001)
mancha_em(B('oleo', 'oleo'), Vector((HX - 0.13, 0.05, 0.3)), 0.025, Vector((-1, 0, 0)), alongar=3)

# ------------------------------------------------------------------ sensor da IA (nordeste)
PS = Vector((0.82, 0.8, 0))
viga(B('sensor_poste', 'ferro'), PS + Vector((0, 0, Z0)), PS + Vector((0, 0, 0.62)), 0.045)
caixa(B('iso_base', 'ferro'), PS + Vector((0, 0, Z0 + 0.01)), (0.12, 0.12, 0.02))
caixa(B('sensor', 'grafite'), PS + Vector((0, 0, 0.72)), (0.12, 0.12, 0.18), Matrix.Rotation(-PI * 0.75, 3, 'Z'))
dS = Vector((-1, -1, 0)).normalized()
cil(B('sensor_lente', 'ferro', True), PS + dS * 0.06 + Vector((0, 0, 0.74)), 0.035, 0.03, dS, lados=20)
cil(B('sensor_olho', 'olho'), PS + dS * 0.077 + Vector((0, 0, 0.74)), 0.025, 0.004, dS, lados=20)
cil(B('led_led_verde', 'led_verde'), PS + dS * 0.062 + Vector((0.03, -0.03, 0.67)), 0.007, 0.006, dS, lados=10)
cil(B('led_led_ambar', 'led_ambar'), PS + dS * 0.062 + Vector((-0.03, 0.03, 0.67)), 0.007, 0.006, dS, lados=10)
pts = bezier(PS + Vector((0, 0, 0.3)), PS + Vector((-0.1, -0.1, 0.12)), Vector((0.45, 0.45, 0.2)), Vector((0.3, 0.3, Z_PT - 0.03)), 10)
mangueira(B('cabos', 'cabo', True), pts, 0.01)

# ------------------------------------------------------------------ emissores nos braços + pistões
HINGE_Z = Z_PT + 0.045
bracos = []          # (empty, base, k)
pistoes = []         # (camisa, haste, A, base, k)
L_C, L_H = 0.2, 0.22
for k, d in enumerate(DIAG):
    t = Vector((-d.y, d.x, 0))
    base = Matrix((d, t, Vector((0, 0, 1)))).transposed()                  # colunas: x=d, y=t, z=up
    H = d * 0.35 + Vector((0, 0, HINGE_Z))
    # olhal fixo da dobradiça (dois lóbulos) e chapa na tampa
    caixa(B('dobradica', 'ferro'), d * 0.35 + Vector((0, 0, Z_PT + 0.008)), (0.1, 0.13, 0.016), rot_face(d))
    for s in (-1, 1):
        caixa(B('dobradica', 'amarelo'), H + t * s * 0.045 + Vector((0, 0, -0.015)), (0.05, 0.012, 0.05), rot_face(d))
    cil(B('dobradica_pino', 'aco', True), H, 0.012, 0.11, t, lados=12)
    # âncora do pistão
    A = d * 0.19 + Vector((0, 0, Z_PT + 0.04))
    caixa(B('dobradica', 'ferro'), d * 0.19 + Vector((0, 0, Z_PT + 0.008)), (0.07, 0.09, 0.016), rot_face(d))
    for s in (-1, 1):
        caixa(B('dobradica', 'amarelo'), A + t * s * 0.032 + Vector((0, 0, -0.01)), (0.04, 0.01, 0.045), rot_face(d))
    cil(B('dobradica_pino', 'aco', True), A, 0.009, 0.08, t, lados=10)
    # braço (gira em torno do eixo t no ponto H)
    e = bpy.data.objects.new('braco', None)
    sc.collection.objects.link(e)
    e.location = H
    e.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    for s in (-1, 1):
        caixa(bm, Vector((0, s * 0.03, 0.26)), (0.05, 0.012, 0.52))
    caixa(bm, Vector((0, 0, 0.47)), (0.06, 0.07, 0.03))
    caixa(bm, Vector((0, 0, 0.15)), (0.04, 0.06, 0.02))
    obj('braco_chapa', bm, 'amarelo', e)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.03, 0.05, Vector((0, 1, 0)), lados=16)
    for s in (-1, 1):                                                      # olhal do pistão no braço
        caixa(bm, Vector((-0.04, s * 0.022, 0.3)), (0.05, 0.01, 0.04))
    cil(bm, Vector((-0.055, 0, 0.3)), 0.009, 0.06, Vector((0, 1, 0)), lados=10)
    obj('braco_buchas', bm, 'ferro', e)
    # cabeça emissora: prato (taça) com lente, bobina no pescoço, aletas
    bm = bmesh.new()
    torno(bm, Vector((0, 0, 0)), [(0.48, 0.035), (0.52, 0.04), (0.56, 0.09), (0.6, 0.13), (0.61, 0.135)], 28)
    obj('emissor_prato', bm, 'grafite', e)
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0.61)), 0.135, 0.009, 40, 8)
    obj('emissor_aro', bm, 'bobina', e)
    bm = bmesh.new()
    for j in range(5):
        toro(bm, Vector((0, 0, 0.495 + j * 0.013)), 0.045, 0.006, 24, 6)
    obj('emissor_bobina', bm, 'bobina', e)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.6)), 0.07, 0.012, lados=24)
    obj('emissor_lente', bm, 'lente', e)
    bm = bmesh.new()
    curva(bm, Vector((0, 0, 0.63)), 0.022, 12)
    tubo(bm, Vector((0, 0, 0.58)), Vector((0, 0, 0.63)), 0.008, 10)
    obj('emissor_ponta', bm, 'cromo', e)
    bm = bmesh.new()                                                       # cabo preso ao braço
    pts = [Vector((0.03, 0.0, z)) for z in (0.05, 0.15, 0.25, 0.35, 0.45)] + [Vector((0.02, 0, 0.5))]
    mangueira(bm, pts, 0.011)
    obj('braco_cabo', bm, 'cabo', e)
    bm = bmesh.new()
    for z in (0.12, 0.38):
        caixa(bm, Vector((0.034, 0, z)), (0.03, 0.03, 0.012))
    obj('braco_abrac', bm, 'aco', e)
    bracos.append((e, base, k))
    # cabo da tampa até a raiz do braço (folga em laço)
    raiz = H + d * 0.04 + Vector((0, 0, 0.02))
    pts = bezier(d * 0.24 + t * 0.07 + Vector((0, 0, Z_PT)), d * 0.24 + t * 0.07 + Vector((0, 0, Z_PT + 0.12)),
                 raiz + d * 0.05 + Vector((0, 0, 0.12)), raiz + d * 0.03 + Vector((0, 0, 0.06)), 8)
    mangueira(B('cabos', 'cabo', True), pts, 0.011)
    # pistão: camisa (presa na âncora) + haste cromada (presa no braço)
    cam = bpy.data.objects.new('pistao_camisa', None)
    sc.collection.objects.link(cam)
    cam.location = A
    cam.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.03 + L_C / 2)), 0.026, L_C, lados=20)
    cil(bm, Vector((0, 0, 0.03 + L_C)), 0.031, 0.016, lados=20)
    cil(bm, Vector((0, 0, 0.034)), 0.031, 0.014, lados=20)
    o = suavizar(obj('pistao_corpo', bm, 'amarelo', cam))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.0)), 0.016, 0.03, Vector((0, 1, 0)), lados=12)
    cil(bm, Vector((0, 0, 0.018)), 0.012, 0.03, lados=10)
    cil(bm, Vector((0.03, 0, 0.06)), 0.009, 0.03, Vector((1, 0, 0)), lados=10)   # porta da mangueira
    cil(bm, Vector((0.03, 0, 0.03 + L_C - 0.02)), 0.009, 0.03, Vector((1, 0, 0)), lados=10)
    obj('pistao_olhal', bm, 'ferro', cam)
    hst = bpy.data.objects.new('pistao_haste', None)
    sc.collection.objects.link(hst)
    hst.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -L_H / 2 - 0.02)), 0.013, L_H, lados=16)
    suavizar(obj('haste', bm, 'cromo', hst))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.016, 0.03, Vector((0, 1, 0)), lados=12)
    cil(bm, Vector((0, 0, -0.02)), 0.012, 0.025, lados=10)
    obj('haste_olhal', bm, 'ferro', hst)
    pistoes.append((cam, hst, A, base, k))
    # mangueiras hidráulicas: distribuidor → portas do pistão (laços folgados)
    for j, zl in enumerate((0.09, 0.03 + L_C - 0.02 + 0.03)):
        porta = A + base @ Vector((0.03, 0, 0)) + Vector((0, 0, zl * 0.7))
        ini = DISTR + Vector((-0.04, (j - 0.5) * 0.05, 0.02))
        meio = (ini + porta) / 2 + Vector((0, 0, 0.12))
        if d.x < 0:                                                        # do outro lado: contorna a coluna por fora
            meio = Vector((0, 0, 0)) + Vector(((d.x * 0.0), d.y * 0.24, Z_PT + 0.09))
        pts = bezier(ini, ini + Vector((0, 0, 0.08)), meio, porta + Vector((0, 0, 0.0)), 12)
        mangueira(B('mangueiras', 'mangueira', True), pts, 0.008)
    mancha(B('oleo', 'oleo'), (A.x + 0.03, A.y + 0.02), 0.035, Z_PT + 0.0015)

# pó e sujeira na laje
for k in range(18):
    x, y = random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95)
    mancha(B('po', 'po'), (x, y), random.uniform(0.05, 0.12), Z0 + 0.0008)
for k in range(6):
    mancha(B('chamusco', 'chamusco'), (random.uniform(-0.5, -0.3), random.uniform(-0.5, 0.5)), random.uniform(0.03, 0.06), Z0 + 0.0012)

# ------------------------------------------------------------------ blocos simples de máquina em volta (dentro da bolha)
def bloco(c, tam, mat, rot=0.0, tanque=False, chamine=False):
    R = Matrix.Rotation(rot, 3, 'Z')
    caixa(B('blocos_laje', 'concreto'), Vector((c[0], c[1], 0.04)), (tam[0] + 0.1, tam[1] + 0.1, 0.08), R)
    caixa(B('blocos_' + mat, mat), Vector((c[0], c[1], 0.08 + tam[2] / 2)), tam, R)
    caixa(B('blocos_tampa', 'grafite'), Vector((c[0], c[1], 0.08 + tam[2] + 0.02)), (tam[0] + 0.02, tam[1] + 0.02, 0.04), R)
    if tanque:
        cil(B('blocos_tanque', 'casco', True), Vector((c[0], c[1], 0.08 + tam[2] + 0.4)) + R @ Vector((tam[0] * 0.2, 0, 0)),
            min(tam[0], tam[1]) * 0.3, 0.7, lados=24)
    if chamine:
        cil(B('blocos_chamine', 'ferro', True), Vector((c[0], c[1], 0.08 + tam[2] + 0.5)) + R @ Vector((-tam[0] * 0.3, tam[1] * 0.2, 0)),
            0.12, 1.0, lados=16)
    for k in range(2):
        mancha(B('chamusco', 'po'), (c[0] + random.uniform(-0.5, 0.5), c[1] + random.uniform(-0.5, 0.5)), 0.3, 0.003)


bloco((3.6, 1.6), (2.0, 1.8, 1.4), 'bloco', 0.0, tanque=True)
bloco((-3.2, 3.4), (1.8, 1.8, 1.8), 'bloco_cinza', 0.0, chamine=True)
bloco((-4.6, -1.4), (2.0, 2.0, 1.2), 'bloco', 0.0, tanque=True)
bloco((1.8, -3.8), (1.8, 1.0, 1.0), 'bloco_cinza', 0.0)
bloco((5.2, -2.6), (1.0, 1.0, 2.4), 'bloco', 0.0, chamine=True)
bloco((0.4, 4.6), (2.8, 1.0, 0.9), 'bloco_cinza', 0.0)
bloco((-2.0, -4.8), (1.0, 2.0, 1.6), 'bloco', 0.0)
for k in range(26):                                                        # pedras e pó em volta
    r = random.uniform(2.0, 16.0)
    a = random.uniform(0, 2 * PI)
    pedra(B('pedras', 'pedra'), (math.cos(a) * r, math.sin(a) * r, 0.0), random.uniform(0.08, 0.35))

# ------------------------------------------------------------------ objetos estáticos
for (nome, mat, liso), bm in BMS.items():
    o = obj(nome, bm, mat)
    if liso:
        suavizar(o)


# ------------------------------------------------------------------ cardã: três anéis de bobina girando
def anel_bobina(bm_a, bm_b, R, eixo_pinos):
    """Anel de aço no plano xy local com espiras de cobre em volta; sem espiras perto dos pinos."""
    toro(bm_a, Vector((0, 0, 0)), R, 0.015, 64, 10)
    n = int(R * 120)
    for i in range(n):
        a = i * 2 * PI / n
        ang_pino = 0.0 if eixo_pinos == 'X' else PI / 2
        if min(abs(math.sin(a - ang_pino)), 1) < 0.22 and True:
            continue
        p = Vector((math.cos(a), math.sin(a), 0)) * R
        tg = Vector((-math.sin(a), math.cos(a), 0))
        toro(bm_b, p, 0.022, 0.0055, 16, 6, tg.to_track_quat('Z', 'Y').to_matrix())


E = []
pai = None
for i, R in enumerate(R_AN):
    e = bpy.data.objects.new('carda_%d' % i, None)
    sc.collection.objects.link(e)
    if pai is None:
        e.location = CC
    else:
        e.parent = pai
    eixo = 'X' if i != 1 else 'Y'
    bma, bmb = bmesh.new(), bmesh.new()
    anel_bobina(bma, bmb, R, eixo)
    suavizar(obj('anel_aco', bma, 'aco', e))
    suavizar(obj('anel_espiras', bmb, 'bobina', e))
    bm = bmesh.new()
    R_pai = R_AN[i - 1] if i > 0 else 0.47
    u = Vector((1, 0, 0)) if eixo == 'X' else Vector((0, 1, 0))
    for s in (-1, 1):
        tubo(bm, u * s * (R - 0.01), u * s * (R_pai - 0.012), 0.011, 12)
        cil(bm, u * s * (R + 0.008), 0.024, 0.03, u, lados=14)            # cubo do pino no anel
    suavizar(obj('anel_pinos', bm, 'cromo', e))
    E.append(e)
    pai = e

# cristal da IA flutuando no meio
cristal = bpy.data.objects.new('cristal', None)
sc.collection.objects.link(cristal)
cristal.location = CC
bm = bmesh.new()
rr = [0.085 * (1 + random.uniform(-0.12, 0.12)) for _ in range(6)]
anel_b = [bm.verts.new((math.cos(k * PI / 3) * rr[k], math.sin(k * PI / 3) * rr[k], -0.05)) for k in range(6)]
anel_c = [bm.verts.new((math.cos(k * PI / 3) * rr[k] * 0.93, math.sin(k * PI / 3) * rr[k] * 0.93, 0.06)) for k in range(6)]
topo = bm.verts.new((0.01, -0.006, 0.18))
fundo = bm.verts.new((-0.006, 0.008, -0.16))
for k in range(6):
    j = (k + 1) % 6
    bm.faces.new((anel_b[k], anel_b[j], anel_c[j], anel_c[k]))
    bm.faces.new((anel_c[k], anel_c[j], topo))
    bm.faces.new((anel_b[j], anel_b[k], fundo))
obj('cristal_corpo', bm, 'cristal', cristal)
luz_c = bpy.data.lights.new('Cristal', 'POINT')
luz_c.color = VIOLETA
luz_c.shadow_soft_size = 0.05
lc = bpy.data.objects.new('Cristal', luz_c)
sc.collection.objects.link(lc)
lc.location = Vector((0, 0, 1.32))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 1.0, 1.0, lados=16)
feixe_o = obj('feixe', bm, 'feixe_luz')                                    # taça → cristal
feixe_o.location = Vector((0, 0, (1.21 + CC.z - 0.15) / 2))
feixe_o.scale = (0.05, 0.05, (CC.z - 0.15 - 1.21) / 2 + 0.02)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 1.0, 1.0, lados=12)
fio = obj('fio_luz', bm, 'fio_luz')                                        # cristal → topo da bolha
fio.location = Vector((0, 0, (CC.z + 0.2 + R_BOLHA) / 2))
fio.scale = (0.012, 0.012, (R_BOLHA - CC.z - 0.2) / 2)
fio.visible_shadow = False
# arcos: dedos da taça → cristal (três formas)
arcos = []
for v in range(4):
    a = v * PI / 2 + PI / 6
    p0 = Vector((math.cos(a), math.sin(a), 0)) * 0.11 + Vector((0, 0, 1.3))
    alvo = CC + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, -0.13))
    bm = bmesh.new()
    pts = [p0]
    for i in range(1, 7):
        tt = i / 7
        pts.append(p0.lerp(alvo, tt) + Vector([random.uniform(-1, 1) for _ in range(3)]) * 0.025 * math.sin(PI * tt))
    pts.append(alvo)
    for a_, b_ in zip(pts, pts[1:]):
        tubo(bm, a_, b_, 0.0035, 5)
    arcos.append(obj('arco', bm, 'arco'))

# ------------------------------------------------------------------ capacitor estufado: faíscas e fumaça
P_EST = ESTUFADO + Vector((0, 0, Z_C1 + 0.05))
faiscas = []
for k in range(12):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.005)
    faiscas.append(obj('faisca', bm, 'faisca'))
vel_f = [Vector((random.uniform(-0.8, 0.6), random.uniform(-0.6, 0.8), random.uniform(0.4, 1.2))) for _ in faiscas]
luz_t = bpy.data.lights.new('Faísca', 'POINT')
luz_t.color = (1.0, 0.6, 0.3)
luz_t.shadow_soft_size = 0.02
lt = bpy.data.objects.new('Faísca', luz_t)
sc.collection.objects.link(lt)
lt.location = P_EST + Vector((0, 0, 0.05))
fumacas = []
for k in range(9):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    fumacas.append(obj('fumaca', bm, 'fumaca'))


# ------------------------------------------------------------------ bolha hexagonal
def cascas_hex(R, filtro):
    """Malha dual de uma icosfera (hexágonos + 12 pentágonos) no raio R; só células cujo centro passa no filtro.
    Cada célula vira membrana (miolo) + moldura (faces do inset) com materiais 0 e 1."""
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=3, radius=1.0)
    ico.faces.ensure_lookup_table()
    centros = {f.index: f.calc_center_median().normalized() for f in ico.faces}
    bm = bmesh.new()
    novos = {}
    celulas = []
    for v in ico.verts:
        nrm = v.co.normalized()
        if not filtro(nrm):
            continue
        t1 = nrm.orthogonal().normalized()
        t2 = nrm.cross(t1)
        fs = sorted(v.link_faces, key=lambda f: math.atan2(centros[f.index].dot(t2), centros[f.index].dot(t1)))
        vs = []
        for f in fs:
            if f.index not in novos:
                novos[f.index] = bm.verts.new(centros[f.index] * R)
            vs.append(novos[f.index])
        celulas.append(bm.faces.new(vs))
    ico.free()
    res = bmesh.ops.inset_individual(bm, faces=celulas, thickness=0.1, depth=0.0, use_even_offset=True)
    for f in res['faces']:
        f.material_index = 1
    for f in celulas:
        f.material_index = 0
    return bm


def onda(o):
    mo = o.modifiers.new('onda', 'WAVE')
    mo.use_normal = True
    mo.use_normal_x = mo.use_normal_y = mo.use_normal_z = True
    mo.height = 0.12
    mo.width = 2.2
    mo.narrowness = 1.2
    mo.speed = 2.2 * 2 / QUADROS * 2                                       # 2 cristas passam no laço
    mo.time_offset = -400
    mo.use_cyclic = True
    mo.falloff_radius = 0.0
    return mo


bm = cascas_hex(R_BOLHA, lambda n: n.z > -0.07)
me = bpy.data.meshes.new('bolha')
bm.to_mesh(me)
bm.free()
bolha = bpy.data.objects.new('bolha', me)
sc.collection.objects.link(bolha)
me.materials.append(base3d.M['membrana'])
me.materials.append(base3d.M['linha'])
bolha.visible_shadow = False
onda(bolha)
capas = []
for nome, P in (('a', IMP_A), ('b', IMP_B)):
    bm = cascas_hex(R_BOLHA + 0.03, lambda n, P=P: n.dot(P) > math.cos(0.62) and n.z > -0.07)
    me = bpy.data.meshes.new('impacto_' + nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('impacto_' + nome, me)
    sc.collection.objects.link(o)
    me.materials.append(base3d.M['imp_' + nome])
    me.materials.append(base3d.M['imp_%s_linha' % nome])
    o.visible_shadow = False
    onda(o)
    capas.append(o)
luzes_imp = []
for P, cor in ((IMP_A, (0.9, 0.8, 0.2)), (IMP_B, (1.0, 0.5, 0.12))):
    ld = bpy.data.lights.new('Impacto', 'POINT')
    ld.color = cor
    ld.shadow_soft_size = 0.3
    lo = bpy.data.objects.new('Impacto', ld)
    sc.collection.objects.link(lo)
    lo.location = P * (R_BOLHA - 0.6)
    luzes_imp.append(ld)

# cuspe ácido (A): bola de ácido chegando, respingos escorrendo na bolha, vapor chiando
def bola(nome, mat, r, sub=2, esticar=1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co.z *= esticar
        v.co += Vector([random.uniform(-1, 1) for _ in range(3)]) * r * 0.12
    return obj(nome, bm, mat)


cuspe = bola('cuspe', 'acido', 0.18, 2, 1.8)
cuspe.rotation_mode = 'QUATERNION'
cauda = [bola('cuspe_gota', 'acido', 0.07 - 0.015 * k, 1) for k in range(3)]
respingos = [bola('respingo', 'acido', random.uniform(0.04, 0.09), 1, 0.6) for _ in range(9)]
resp_dir = [random.uniform(0, 2 * PI) for _ in respingos]
resp_vel = [random.uniform(0.5, 1.4) for _ in respingos]
mancha_acida = bola('mancha_acida', 'acido', 0.45, 2, 0.08)
mancha_acida.rotation_mode = 'QUATERNION'
vapores = []
for k in range(4):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor_acido', bm, 'vapor_acido'))
# projétil (B): bala chegando, achata na bolha e cai; faíscas espirrando pela superfície
projetil = bpy.data.objects.new('projetil', None)
sc.collection.objects.link(projetil)
projetil.rotation_mode = 'QUATERNION'
bm = bmesh.new()
torno(bm, Vector((0, 0, 0)), [(-0.12, 0.035), (0.0, 0.04), (0.05, 0.035), (0.1, 0.018), (0.12, 0.004)], 16)
obj('projetil_corpo', bm, 'projetil', projetil)
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.125)), 0.03, 0.01, lados=16)
obj('projetil_base', bm, 'brasa', projetil)
faiscas_b = []
for k in range(16):
    bm = bmesh.new()
    tubo(bm, Vector((0, 0, -0.06)), Vector((0, 0, 0.06)), 0.008, 5)
    o = obj('faisca_b', bm, 'faisca')
    o.rotation_mode = 'QUATERNION'
    faiscas_b.append(o)
vel_b = [(random.uniform(0, 2 * PI), random.uniform(2.0, 5.0), random.uniform(0.5, 2.5)) for _ in faiscas_b]


def base_tangente(P):
    P = P.normalized()
    t1 = Vector((0, 0, 1)).cross(P).normalized()
    t2 = P.cross(t1)
    return P, t1, t2


# ------------------------------------------------------------------ animação (laço de 4 s)
def keyall(o, *cs, q):
    for c in cs:
        o.keyframe_insert(c, frame=q)


def ocultar(o, h, q):
    o.hide_render = o.hide_viewport = h
    keyall(o, 'hide_render', 'hide_viewport', q=q)


cristal_bsdf = base3d.M['cristal'].node_tree.nodes['Principled BSDF']
feixe_forca = base3d.M['feixe_luz'].node_tree.nodes['forca'].inputs[1]
taca_bsdf = base3d.M['taca'].node_tree.nodes['Principled BSDF']
lente_bsdf = base3d.M['lente'].node_tree.nodes['Principled BSDF']
fio_bsdf = base3d.M['fio_luz'].node_tree.nodes['Principled BSDF']
tremores = [base3d.M[m].node_tree.nodes['tremor'].inputs['W'] for m in ('membrana', 'linha')]
fases = {'a': [base3d.M[m].node_tree.nodes['fase'].outputs[0] for m in ('imp_a', 'imp_a_linha')],
         'b': [base3d.M[m].node_tree.nodes['fase'].outputs[0] for m in ('imp_b', 'imp_b_linha')]}
T_A, T_B = 12, 22                                                          # quadro do impacto
DUR = 40                                                                   # quadros até a fase 1
PA, ta1, ta2 = base_tangente(IMP_A)
PB, tb1, tb2 = base_tangente(IMP_B)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 3 * fr)                          # cristal pulsa 3× no laço
    # cardã
    E[0].rotation_euler = (2 * PI * fr, 0, 0)
    E[1].rotation_euler = (0, -2 * PI * 2 * fr, 0)
    E[2].rotation_euler = (2 * PI * 3 * fr, 0, 0)
    for e in E:
        keyall(e, 'rotation_euler', q=q)
    cristal.location = CC + Vector((0, 0, 0.012 * math.sin(2 * PI * 2 * fr)))
    cristal.rotation_euler = (0.05 * math.sin(2 * PI * fr), 0.04 * math.cos(2 * PI * fr), -2 * PI * fr)
    keyall(cristal, 'location', 'rotation_euler', q=q)
    cristal_bsdf.inputs['Emission Strength'].default_value = 0.6 + 1.6 * pulso
    cristal_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    luz_c.energy = 25 + 45 * pulso
    luz_c.keyframe_insert('energy', frame=q)
    feixe_forca.default_value = 4.0 + 8.0 * pulso
    feixe_forca.keyframe_insert('default_value', frame=q)
    taca_bsdf.inputs['Emission Strength'].default_value = 6 + 10 * pulso
    taca_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    lente_bsdf.inputs['Emission Strength'].default_value = 5 + 8 * pulso
    lente_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    fio_bsdf.inputs['Emission Strength'].default_value = 3 + 6 * pulso
    fio_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    for w in tremores:
        w.default_value = 2.0 * math.sin(2 * PI * fr)
        w.keyframe_insert('default_value', frame=q)
    for v, o in enumerate(arcos):
        ocultar(o, not (((q + v * 3) % 7) < 3 and pulso > 0.35), q)
    # braços: inclinação ajustada pelos pistões
    for e, base, k in bracos:
        phi = 0.42 + 0.09 * math.sin(2 * PI * fr + k * PI / 2)
        Mrot = base @ Matrix.Rotation(phi, 3, 'Y')
        e.rotation_quaternion = Mrot.to_quaternion()
        keyall(e, 'rotation_quaternion', q=q)
        cam, hst, A, base_p, kk = pistoes[k]
        P = e.location + Mrot @ Vector((-0.055, 0, 0.3))
        qd = (P - A).to_track_quat('Z', 'Y')
        cam.rotation_quaternion = qd
        hst.location = P
        hst.rotation_quaternion = qd
        keyall(cam, 'rotation_quaternion', q=q)
        keyall(hst, 'location', 'rotation_quaternion', q=q)
    for e in fans:
        e.rotation_euler = (0, 2 * PI * 9 * fr, 0)
        keyall(e, 'rotation_euler', q=q)
    # capacitor estufado: faíscas em rajadas, fumaça subindo
    rajada = (q % 24) < 7
    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + fr * 8) % 1.0) * 0.28
        p = P_EST + vel_f[k] * tt + Vector((0, 0, -4.9 * tt * tt))
        viva = rajada and p.z > Z0 + 0.01
        o.location = p
        o.scale = [max(0.001, (1 - tt / 0.28)) if viva else 0.001] * 3
        keyall(o, 'location', 'scale', q=q)
    luz_t.energy = 5.0 if rajada and q % 2 == 0 else 0.0
    luz_t.keyframe_insert('energy', frame=q)
    for k, o in enumerate(fumacas):
        u = (k / len(fumacas) + fr * 1.5) % 1.0
        o.location = P_EST + Vector((-0.1 * u + 0.03 * math.sin(k * 2 + u * 6), 0.06 * u, 0.06 + 1.1 * u))
        o.scale = [0.06 + 0.22 * u] * 3
        o.rotation_euler = (k, u * 2, k * 0.7)
        keyall(o, 'location', 'scale', 'rotation_euler', q=q)
    # impactos na bolha
    for nome, T0, luz in (('a', T_A, luzes_imp[0]), ('b', T_B, luzes_imp[1])):
        dt = (q - T0) % QUADROS
        f = dt / DUR if dt <= DUR * 1.4 else -1.0
        for s in fases[nome]:
            s.default_value = f
            s.keyframe_insert('default_value', frame=q)
        luz.energy = 4000 * max(0.0, 1 - dt / 10.0) if dt < 10 else 0.0
        luz.keyframe_insert('energy', frame=q)
    for o, nome, T0 in ((capas[0], 'a', T_A), (capas[1], 'b', T_B)):
        dt = (q - T0) % QUADROS
        ocultar(o, dt > DUR * 1.4, q)
    # cuspe ácido
    dt = q - T_A
    if dt < 0:                                                             # chegando de fora
        dist = -dt * 1.1
        pos = PA * (R_BOLHA + 0.2 + dist) + Vector((0, 0, 0.05 * dt * dt * 0.1))
        cuspe.location = pos
        cuspe.rotation_quaternion = PA.to_track_quat('Z', 'Y')
        cuspe.scale = (1, 1, 1)
        for j, g in enumerate(cauda):
            g.location = PA * (R_BOLHA + 0.6 + dist + 0.35 * (j + 1)) + Vector((0, 0, 0.04 * (j + 1)))
            ocultar(g, False, q)
            keyall(g, 'location', q=q)
        ocultar(cuspe, False, q)
    else:
        cuspe.location = PA * (R_BOLHA + 0.15)
        cuspe.scale = (1.6, 1.6, 0.25)
        ocultar(cuspe, True, q)
        for g in cauda:
            ocultar(g, True, q)
    keyall(cuspe, 'location', 'rotation_quaternion', 'scale', q=q)
    for j, o in enumerate(respingos):                                     # respingos deslizando na superfície
        if dt < 0:
            o.location = PA * (R_BOLHA + 0.1)
            o.scale = (0.01, 0.01, 0.01)
            ocultar(o, True, q)
        else:
            tt = dt / FPS
            a = resp_dir[j]
            ang = 0.02 + resp_vel[j] * 0.06 * (1 - math.exp(-tt * 4)) + 0.025 * tt   # espalha e escorre
            d = (ta1 * math.cos(a) + ta2 * math.sin(a))
            n = (PA * math.cos(ang) + d * math.sin(ang)).normalized()
            n = (n - Vector((0, 0, 1)) * 0.03 * tt * tt).normalized()          # escorre para baixo
            o.location = n * (R_BOLHA + 0.06)
            o.rotation_euler = n.to_track_quat('Z', 'Y').to_euler()
            sc_ = max(0.02, 1 - tt / 3.5)
            o.scale = (sc_, sc_, sc_)
            ocultar(o, sc_ <= 0.02, q)
            keyall(o, 'rotation_euler', q=q)
        keyall(o, 'location', 'scale', q=q)
    mancha_acida.location = PA * (R_BOLHA + 0.05)
    mancha_acida.rotation_quaternion = PA.to_track_quat('Z', 'Y')
    sm = 0.001 if dt < 0 else min(1.0, dt / 4.0) * max(0.05, 1 - dt / 80.0)
    mancha_acida.scale = (sm, sm, sm)
    ocultar(mancha_acida, dt < 0, q)
    keyall(mancha_acida, 'location', 'rotation_quaternion', 'scale', q=q)
    for k, o in enumerate(vapores):
        u = ((k / len(vapores)) + max(0, dt) / 40.0) % 1.0
        forca = 0 if dt < 0 else max(0.0, 1 - dt / 70.0)
        o.location = PA * (R_BOLHA + 0.25 + 1.2 * u) + Vector((0.2 * math.sin(k * 3), 0.15 * math.cos(k), 0.9 * u))
        o.scale = [max(0.05, (0.2 + 0.6 * u) * forca)] * 3
        o.rotation_euler = (k, u * 3, k * 0.5)
        ocultar(o, forca < 0.08, q)
        keyall(o, 'location', 'scale', 'rotation_euler', q=q)
    # projétil
    dt = q - T_B
    if dt < 0:
        projetil.location = PB * (R_BOLHA + 0.15 - dt * 2.4)
        projetil.rotation_quaternion = (-PB).to_track_quat('Z', 'Y')
        projetil.scale = (1, 1, 1)
        ocultar(projetil, dt < -8, q)
    else:
        tt = dt / FPS
        projetil.location = PB * (R_BOLHA + 0.12) + Vector((0, 0, -4.9 * tt * tt)) + PB * 1.2 * tt
        projetil.rotation_quaternion = (-PB).to_track_quat('Z', 'Y') @ Quaternion((1, 0, 0), 6 * tt)
        projetil.scale = (1.5, 1.5, 0.35)                                  # achatado
        ocultar(projetil, dt > 30, q)
    keyall(projetil, 'location', 'rotation_quaternion', 'scale', q=q)
    for k, o in enumerate(faiscas_b):
        a, v, up = vel_b[k]
        tt = dt / FPS
        if 0 <= dt < 14:
            d = ta1 * 0 + (tb1 * math.cos(a) + tb2 * math.sin(a))
            vel = d * v + PB * up
            o.location = PB * (R_BOLHA + 0.1) + vel * tt + Vector((0, 0, -4.9 * tt * tt))
            o.rotation_quaternion = vel.to_track_quat('Z', 'Y')
            s = max(0.05, 1 - dt / 14)
            o.scale = (s, s, 1.0 + 2.0 * s)
            ocultar(o, False, q)
        else:
            o.location = PB * (R_BOLHA + 0.1)
            o.scale = (0.05, 0.05, 0.05)
            ocultar(o, True, q)
        keyall(o, 'location', 'rotation_quaternion', 'scale', q=q)

for o in list(sc.objects) + [base3d.M[m] for m in base3d.M] + [luz_c, luz_t] + luzes_imp:
    ad = getattr(o, 'animation_data', None) or getattr(getattr(o, 'node_tree', None), 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (120, 120, 1.0))
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
cam_d.clip_end = 300
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 0.85)
FR_FOTO = 20                                                               # A abrindo anéis, B chegando
FR_BOLHA = 32                                                              # A com anéis largos, B recém-batido
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    if so_uma in (None, '0'):
        sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
        sc.frame_set(FR_FOTO)
        a = math.radians(300)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, 2.2)), ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'gerador_escudo_0.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(FR_FOTO)
        mirar((-2.05, -1.0, 1.55), (-0.4, 0.05, 0.92), 30)
        sc.render.filepath = os.path.join(AQUI, 'gerador_escudo_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'bolha'):
        sc.cycles.samples = 160
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
        sc.frame_set(FR_BOLHA)
        mirar((5.5, -25.0, 7.5), (0.0, 0.0, 3.0), 34)
        sc.render.filepath = os.path.join(AQUI, 'gerador_escudo_bolha.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(v[7]) if v[7] >= 1 else int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'gerador_escudo_teste.png')
    bpy.ops.render.render(write_still=True)
print('GERADOR DE ESCUDO ok')
