"""Estudo isolado (fora do jogo): ARTILHARIA da IA, 3×3 tiles. Granadas entram pelo sul (ITEM_ENT_S1, tile do meio).
Dispara granadas com alcance de 120 m e mira nos ninhos das aranhas. Partes: base, giro (gira em Z), canhao (eleva no
munhão), cano (recua), cunha, bandeja, soquete, elev0, elev1.
- Laje com faixas; pedestal octogonal aparafusado; quatro patolas hidráulicas (viga telescópica, cilindro de extensão,
  macaco vertical) com sapatas cravadas no concreto (trincas, lascas, lama).
- Plataforma giratória sobre coroa dentada com dois motores de giro (redutor e pinhão); munhoneiras amarelas.
- Obus pesado: cano longo afinando, evacuador de fumaça, freio de boca de chicanas, berço com dois cilindros de recuo
  e recuperador (hastes cromadas presas à culatra), culatra de cunha vertical com cilindro de abertura.
- Elevação por dois cilindros hidráulicos telescópicos grandes (3 estágios), de 4° (quase deitado) até 60°.
- Carregador automático: bandeja que gira de lado para a linha do cano, soquete de corrente que empurra a granada e o
  estojo de carga; paiol blindado na plataforma (grade com granadas e cargas) e paiol de recebimento no chão (boca S1).
- Unidade hidráulica na plataforma e no chão, mangueiras, feixes de cabos com abraçadeiras; mastro do telêmetro
  estereoscópico da IA com olho violeta, radar que gira e antena.
- Sujeira: pintura lascada, remendos aparafusados, peça trocada de outra cor, números apagados, ferrugem, óleo, fuligem
  no freio de boca, pó, lama nas sapatas, estojos velhos pelo chão.
Animação (laço de 4 s, 1 tiro): carrega a 4° (bandeja entra, soquete empurra, cunha fecha, bandeja sai e recebe nova
granada do paiol); gira e eleva a 55°; dispara (clarão enorme, jatos laterais do freio, onda de choque de poeira no
chão, poeira subindo, pedrinhas, recuo e retorno do cano); cunha abre, o estojo sai fumegando, desce pela calha,
cai, quica e fica; abaixa e volta.
Uso: blender -b --python estudo_artilharia.py -- foto [0|perto|disparo|capsula]
     blender -b --python estudo_artilharia.py -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(311)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


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
        A, Bq = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], Bq[(j + 1) % nr], Bq[j]))


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def feixe(bc, ba, pts, lat, n=3, r=0.014, passo=4):
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.014, pts[j] + u * 0.014, r * (n + 0.7), 12)


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


def prisma_xz(bm, perfil, y0, y1):
    a = [bm.verts.new((x, y0, z)) for x, z in perfil]
    b = [bm.verts.new((x, y1, z)) for x, z in perfil]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(perfil)
    for k in range(n):
        bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))


def prisma_polar(bm, rf, z0, z1, n=192, dr=0.0, r_in=None):
    """Prisma de contorno polar r(a) (estrelado a partir da origem). Com r_in: anel entre r_in(a) e r(a)+dr."""
    angs = [k * 2 * PI / n for k in range(n)]
    if r_in is None:
        b = [bm.verts.new((math.cos(a) * (rf(a) + dr), math.sin(a) * (rf(a) + dr), z0)) for a in angs]
        t = [bm.verts.new((v.co.x, v.co.y, z1)) for v in b]
        bm.faces.new(list(reversed(b)))
        bm.faces.new(t)
        for k in range(n):
            bm.faces.new((b[k], b[(k + 1) % n], t[(k + 1) % n], t[k]))
        return
    ob = [bm.verts.new((math.cos(a) * (rf(a) + dr), math.sin(a) * (rf(a) + dr), z0)) for a in angs]
    ot = [bm.verts.new((v.co.x, v.co.y, z1)) for v in ob]
    ib = [bm.verts.new((math.cos(a) * r_in(a), math.sin(a) * r_in(a), z0)) for a in angs]
    it = [bm.verts.new((v.co.x, v.co.y, z1)) for v in ib]
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((ob[k], ob[j], ot[j], ot[k]))
        bm.faces.new((ib[j], ib[k], it[k], it[j]))
        bm.faces.new((ot[k], ot[j], it[j], it[k]))
        bm.faces.new((ob[j], ob[k], ib[k], ib[j]))


def torno(bm, perfil, n=24, fechado=False):
    """Sólido de revolução em torno do eixo x; perfil = [(x, r)]. r = 0 vira polo."""
    aneis = []
    for x, r in perfil:
        if r < 1e-6:
            aneis.append([bm.verts.new((x, 0, 0))])
        else:
            aneis.append([bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for a in (k * 2 * PI / n for k in range(n))])
    pares = list(zip(aneis, aneis[1:])) + ([(aneis[-1], aneis[0])] if fechado else [])
    for A, Bq in pares:
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


BMS = {}


def B(nome, mat, liso=False, g='base'):
    k = (nome, mat, liso, g)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def parafuso(p, n, g='base', r=0.012):
    cil(B('parafusos', 'aco', False, g), Vector(p), r, 0.013, Vector(n), lados=6)


def remendo(c, R, w, h, g='base', mat='grafite'):
    """Chapa de remendo aparafusada numa face vertical (R = rot_face: x na face, y normal)."""
    c = Vector(c)
    caixa(B('remendos_' + mat, mat, False, g), c + R @ Vector((0, 0.004, 0)), (w, 0.008, h), R)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parafuso(c + R @ Vector((sx * (w / 2 - 0.018), 0.009, 0)) + Vector((0, 0, sz * (h / 2 - 0.018))), R @ Vector((0, 1, 0)), g, 0.009)


def stencil(c, R, g='base', n=5, alt=0.045):
    """Número de série pintado e meio apagado: traços de tinta clara."""
    c = Vector(c)
    x = -(n - 1) * alt * 0.35
    for k in range(n):
        for _ in range(random.randint(2, 4)):
            if random.random() < 0.3:
                continue
            if random.random() < 0.5:
                caixa(B('stencil', 'tinta', False, g), c + R @ Vector((x + random.choice((-1, 0, 1)) * alt * 0.22, 0.0015, 0))
                      + Vector((0, 0, random.choice((-1, 1)) * alt * 0.22)), (0.007, 0.002, alt * 0.45), R)
            else:
                caixa(B('stencil', 'tinta', False, g), c + R @ Vector((x, 0.0015, 0)) + Vector((0, 0, random.choice((-1, 0, 1)) * alt * 0.45)),
                      (alt * 0.4, 0.002, 0.007), R)
        x += alt * 0.7


def escorrido(c, R, g='base', mat='ferrugem', L=None):
    L = L or random.uniform(0.06, 0.2)
    caixa(B('escorridos_' + mat, mat, False, g), Vector(c) + R @ Vector((0, 0.0015, 0)) - Vector((0, 0, L / 2)),
          (random.uniform(0.006, 0.016), 0.002, L), R)


def mtx_cil(d):
    """Rotação com Z ao longo de d (no plano xz) e X no eixo y do pino."""
    z = d.normalized()
    x = Vector((0, 1, 0))
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vol_cor_mat(nome, cor, escala, dens, em_cor=None, em=0.0, borda0=0.3, f0=0.38, f1=0.64):
    """Volume em bolha (some na borda), densidade = cor.R do objeto × dens; emissão = cor.G × em (chaves por quadro)."""
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
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 6.0, 'Roughness': 0.6})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
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


def onda_mat(nome, cor, escala, dens, r_tubo=0.25):
    """Anel de poeira (onda de choque) em volume sobre um toro de raio 1: some longe do tubo; densidade = cor.R."""
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
    sx = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sx.inputs[0])
    cxy = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sx.outputs['X'], cxy.inputs['X'])
    nt.links.new(sx.outputs['Y'], cxy.inputs['Y'])
    lxy = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(cxy.outputs[0], lxy.inputs[0])
    sub = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    sub.inputs[1].default_value = 1.0
    nt.links.new(lxy.outputs['Value'], sub.inputs[0])
    c2 = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sub.outputs['Value'], c2.inputs['X'])
    nt.links.new(sx.outputs['Z'], c2.inputs['Y'])
    l2 = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(c2.outputs[0], l2.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': r_tubo, 'From Max': r_tubo * 0.25})
    nt.links.new(l2.outputs['Value'], borda.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 6.0, 'Roughness': 0.6})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    forma = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.36, 'From Max': 0.62})
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
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.95, ferrugem=0.4),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.85, sujeira=0.9, ferrugem=0.2),
    'chapa': mats.material('Chapa do convés', (0.12, 0.12, 0.12), 0.7, 0.55, pintura=False, ferrugem=0.7, sujeira=1.0),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cano_aco': mats.material('Aço do cano', (0.2, 0.2, 0.2), 1.0, 0.45, pintura=False, ferrugem=0.55, sujeira=0.9, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'bronze': mats.material('Bronze', (0.55, 0.38, 0.17), 1.0, 0.4, pintura=False, sujeira=0.9, ferrugem=0.2),
    'latao': mats.material('Latão', (0.62, 0.45, 0.16), 1.0, 0.32, pintura=False, sujeira=0.7),
    'latao_gasto': mats.material('Latão gasto', (0.58, 0.42, 0.17), 1.0, 0.38, pintura=False, sujeira=0.9, ferrugem=0.25),
    'aco_capsula': mats.material('Aço do estojo', (0.36, 0.35, 0.34), 1.0, 0.45, pintura=False, sujeira=0.9, ferrugem=0.5),
    'espoleta': mats.material('Espoleta', (0.7, 0.4, 0.25), 1.0, 0.3, pintura=False, sujeira=0.4),
    'oliva': mats.material('Verde-oliva', (0.13, 0.14, 0.06), 0, 0.5, desgaste=0.7, sujeira=0.7),
    'primer': mats.material('Zarcão', (0.32, 0.07, 0.035), 0, 0.6, desgaste=0.9, sujeira=0.9, ferrugem=0.4),
    'tinta': mats.material('Tinta do número', (0.62, 0.6, 0.55), 0, 0.6, desgaste=1.0, sujeira=1.0),
    'queimado': mats.material('Queimado', (0.1, 0.085, 0.08), 1.0, 0.6, pintura=False, ferrugem=0.7, sujeira=1.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'isol_verm': mats.material('Vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.6, sujeira=0.8),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.22, 0.19, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.09, 0.07, 0.05), 0, 0.85, pintura=False, sujeira=0.3, desgaste=0.0),
    'fuligem_chao': mats.material('Fuligem', (0.1, 0.092, 0.085), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'po_escuro': mats.material('Pó no aço', (0.13, 0.115, 0.1), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'boca_fria': mats.material('Boca queimada', (0.03, 0.025, 0.022), 0.6, 0.7, pintura=False, sujeira=0.2, desgaste=0.0),
    'vidro': emissivo('Vidro', (0.05, 0.04, 0.06), 0.0),
    'listras': base3d.listras_mat(),
    'olho': emissivo('Olho da IA', VIOLETA, 12.0, (0.05, 0.02, 0.1)),
    'laser': emissivo('Laser', (1.0, 0.06, 0.03), 20.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'brasa_freio': emissivo('Freio quente', (1.0, 0.3, 0.04), 0.0, (0.1, 0.085, 0.08)),
    'clarao': emissivo('Clarão', (1.0, 0.78, 0.45), 40.0),
    'faisca': emissivo('Faísca', (1.0, 0.6, 0.25), 60.0),
    'fogo': vol_cor_mat('Fogo', (0.03, 0.012, 0.005), 5.5, 12.0, (1.0, 0.3, 0.04), 45.0, borda0=0.55, f0=0.46, f1=0.58),
    'fogo_nucleo': vol_cor_mat('Fogo do núcleo', (0.05, 0.03, 0.01), 3.0, 9.0, (1.0, 0.66, 0.28), 140.0, borda0=0.35, f0=0.36, f1=0.56),
    'fumaca': vol_cor_mat('Fumaça do tiro', (0.16, 0.15, 0.14), 2.2, 9.0, borda0=0.3),
    'fumaca_clara': vol_cor_mat('Fumaça da culatra', (0.3, 0.3, 0.3), 2.5, 30.0),
    'fiapo': vol_cor_mat('Fiapo', (0.06, 0.058, 0.056), 2.2, 110.0, f0=0.4, f1=0.65),
    'poeira': vol_cor_mat('Poeira', (0.44, 0.37, 0.28), 2.6, 16.0, borda0=0.25),
    'onda': onda_mat('Onda de choque', (0.5, 0.43, 0.33), 2.2, 10.0),
})

# ------------------------------------------------------------------ medidas
Z0 = 0.10                        # topo da laje
AP_SAP, AP_C, AP_FL = 0.88, 0.74, 0.775
Z_SAP, Z_C1, Z_FL = 0.18, 0.42, 0.46
Z_G0, Z_G1 = 0.50, 0.57          # coroa
Z_D = 0.64                       # topo do convés giratório
R_COROA, R_PINHAO = 0.75, 0.055
TX, TZ = 0.05, 1.55              # munhão (referencial do giro)
P_LOAD, P_FIRE = math.radians(4), math.radians(55)
Y_LOAD, Y_FIRE = math.radians(25), math.radians(70)
REC = 0.35                       # recuo do cano
YE = 0.40                        # y dos cilindros de elevação
A_EL = Vector((1.17, YE, 0.70))  # pino da camisa (giro)
B_EL = Vector((1.45, YE, -0.24)) # pino da haste (berço)
EYE = 0.06
T_FIRE = 52
CX3 = 0.1395                     # meio do estojo
R_CAP = 0.0615                   # raio do aro do estojo (deita sobre ele)


def r_deck(a):
    d = (math.cos(a), math.sin(a))
    r = 1.0
    for x0, x1, y0, y1 in ((-1.15, 0.2, -1.0, 1.0), (-0.1, 1.32, -0.56, 0.56)):
        ts = []
        ts.append(x1 / d[0] if d[0] > 1e-9 else (x0 / d[0] if d[0] < -1e-9 else 1e9))
        ts.append(y1 / d[1] if d[1] > 1e-9 else (y0 / d[1] if d[1] < -1e-9 else 1e9))
        r = max(r, min(ts))
    return r


# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-1.485, s * 1.485 - 0.014, 0.0), (1.485, s * 1.485 + 0.014, Z0 + 0.002))
    caixa_de(bm, (s * 1.485 - 0.014, -1.485, 0.0), (s * 1.485 + 0.014, 1.485, Z0 + 0.002))
for t in (-0.5, 0.5):
    caixa_de(B('juntas', 'chamusco'), (t - 0.004, -1.47, Z0), (t + 0.004, 1.47, Z0 + 0.0008))
    caixa_de(B('juntas', 'chamusco'), (-1.47, t - 0.004, Z0), (1.47, t + 0.004, Z0 + 0.0008))

# ------------------------------------------------------------------ pedestal
O = Vector((0, 0, 0))
octo(B('sapata', 'ferro'), O, AP_SAP, Z0, Z_SAP)
for k in range(16):
    a = k * 2 * PI / 16 + PI / 16
    p = Vector((math.cos(a), math.sin(a), 0)) * 0.83 + Vector((0, 0, Z_SAP + 0.007))
    cil(B('parafusos', 'aco'), p, 0.017, 0.022, lados=6)
    cil(B('arruelas', 'ferro'), p - Vector((0, 0, 0.007)), 0.028, 0.006, lados=12)
octo(B('corpo', 'amarelo'), O, AP_C, Z_SAP, Z_C1)
R8 = AP_C / math.cos(PI / 8)
for k in range(8):
    a = PI / 8 + k * PI / 4
    caixa(B('nervuras', 'ferro'), Vector((math.cos(a), math.sin(a), 0)) * (R8 + 0.002) + Vector((0, 0, (Z_SAP + Z_C1) / 2)),
          (0.03, 0.03, Z_C1 - Z_SAP), Matrix.Rotation(a, 3, 'Z'))
FACES = {}
for k in range(8):
    a = k * PI / 4
    n = Vector((math.cos(a), math.sin(a), 0))
    FACES[k] = (n, rot_face(n))
for k in (0, 2, 4, 6):                                                       # placas blindadas nas faces cardeais
    n, R = FACES[k]
    c = n * (AP_C + 0.009) + Vector((0, 0, 0.30))
    caixa(B('placas', 'grafite'), c, (0.46, 0.018, 0.2), R)
    for sx in (-1, 0, 1):
        for sz in (-1, 1):
            parafuso(c + R @ Vector((sx * 0.2, 0.01, 0)) + Vector((0, 0, sz * 0.08)), n)
    stencil(c + R @ Vector((0.05, 0.0095, 0)) + Vector((0, 0, 0.0)), R, n=6, alt=0.04)
    for j in range(3):
        escorrido(c + R @ Vector((random.uniform(-0.2, 0.2), 0.0095, 0)) + Vector((0, 0, 0.09)), R)
octo(B('flange', 'ferro'), O, AP_FL, Z_C1, Z_FL)
for k in range(32):
    a = k * 2 * PI / 32
    cil(B('parafusos', 'aco'), Vector((math.cos(a), math.sin(a), 0)) * 0.73 + Vector((0, 0, Z_FL + 0.006)), 0.012, 0.012, lados=6)
cil(B('rolamento', 'aco', True), Vector((0, 0, (Z_FL + Z_G0) / 2)), 0.70, Z_G0 - Z_FL, lados=64)
for k in range(6):
    mancha(B('oleo', 'oleo'), (math.cos(k) * 0.6, math.sin(k) * 0.6), random.uniform(0.03, 0.06), Z_FL + 0.001)

# motores de giro (leste e oeste): motor vertical, redutor e pinhão engrenado na coroa
pinhoes = []
for ang in (0.0, PI):
    d = Vector((math.cos(ang), math.sin(ang), 0))
    R = rot_face(d)
    CM = d * 0.90
    CP = d * (R_COROA + R_PINHAO + 0.005)
    cil(B('motor_giro', 'grafite', True), CM + Vector((0, 0, 0.29)), 0.065, 0.22, lados=24)
    for j in range(5):
        cil(B('motor_aletas', 'ferro', True), CM + Vector((0, 0, 0.21 + j * 0.035)), 0.076, 0.008, lados=24)
    cil(B('motor_tampa', 'ferro', True), CM + Vector((0, 0, 0.175)), 0.07, 0.015, lados=24)
    cil(B('motor_colar', 'ferro', True), CM + Vector((0, 0, 0.43)), 0.05, 0.06, lados=20)
    caixa(B('motor_giro', 'grafite'), CM + R @ Vector((0.075, 0, 0)) + Vector((0, 0, 0.33)), (0.05, 0.06, 0.07), R)
    bm = B('redutor', 'amarelo', True)
    caixa(bm, (CM + CP) / 2 + Vector((0, 0, 0.48)), (0.11, (CM - CP).length + 0.0, 0.035), R)
    for c in (CM, CP):
        cil(bm, c + Vector((0, 0, 0.48)), 0.055, 0.035, lados=24)
    cil(B('pinhao_eixo', 'aco', True), CP + Vector((0, 0, 0.535)), 0.016, 0.07, lados=12)
    for s in (-1, 1):
        caixa(B('suporte_motor', 'ferro'), d * 0.80 + R @ Vector((s * 0.06, 0, 0)) + Vector((0, 0, 0.29)), (0.016, 0.14, 0.09), R)
    pts = bezier(CM + R @ Vector((0.1, 0, 0)) + Vector((0, 0, 0.33)), CM + R @ Vector((0.18, 0.05, 0)) + Vector((0, 0, 0.3)),
                 d * 0.86 + R @ Vector((0.3, 0.05, 0)) + Vector((0, 0, Z_SAP + 0.03)), d * 0.80 + R @ Vector((0.34, 0.0, 0)) + Vector((0, 0, Z_SAP + 0.025)), 10)
    mangueira(B('cabos', 'cabo', True), pts, 0.013)
    p = bpy.data.objects.new('pinhao', None)
    sc.collection.objects.link(p)
    p.location = CP + Vector((0, 0, (Z_G0 + Z_G1) / 2))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), R_PINHAO - 0.008, Z_G1 - Z_G0, lados=20)
    for k in range(14):
        a = k * 2 * PI / 14
        caixa(bm, Vector((math.cos(a), math.sin(a), 0)) * R_PINHAO, (0.018, 0.013, Z_G1 - Z_G0), Matrix.Rotation(a, 3, 'Z'))
    obj('pinhao_dentes', bm, 'aco', p)
    pinhoes.append(p)
    mancha(B('oleo', 'oleo'), (CM.x * 1.05, CM.y + 0.05), 0.07, Z0 + 0.0015)
    for j in range(3):
        caixa(B('escorridos_oleo', 'oleo'), CP + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0.47)), (0.01, 0.01, 0.03))

# ------------------------------------------------------------------ patolas (diagonais)
PATOLAS = []
for kk, ang in enumerate((PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)):
    n = Vector((math.cos(ang), math.sin(ang), 0))
    R = rot_face(n)
    t = R @ Vector((1, 0, 0))
    P = lambda r, tt=0.0, z=0.0: n * r + t * tt + Vector((0, 0, z))
    for s in (-1, 1):                                                        # orelhas da articulação
        caixa(B('pat_orelha', 'ferro'), P(0.81, s * 0.12, 0.28), (0.02, 0.14, 0.2), R)
        parafuso(P(0.75, s * 0.12, 0.36) + n * 0.0, n)
    cil(B('pat_pino', 'aco', True), P(0.81, 0, 0.28), 0.028, 0.29, t, lados=14)
    caixa(B('pat_viga', 'amarelo'), P(1.11, 0, 0.28), (0.2, 0.62, 0.16), R)
    caixa(B('pat_viga_reforco', 'ferro'), P(1.405, 0, 0.28), (0.214, 0.03, 0.174), R)
    mat_int = 'primer' if kk == 1 else 'grafite'                              # viga interna trocada (zarcão)
    caixa(B('pat_interna_' + mat_int, mat_int), P(1.60, 0, 0.28), (0.15, 0.42, 0.12), R)
    caixa(B('pat_cabecote', 'amarelo'), P(1.81, 0, 0.32), (0.26, 0.22, 0.16), R)
    for s in (-1, 1):
        for zz in (0.27, 0.37):
            parafuso(P(1.81, s * 0.131, zz), t * s)
    # macaco vertical: camisa sobre o cabeçote, haste atravessa e desce até a sapata cravada
    C = P(1.81)
    cil(B('pat_camisa', 'amarelo' if kk != 2 else 'grafite', True), C + Vector((0, 0, 0.63)), 0.085, 0.46, lados=32)
    cil(B('pat_camisa_tampa', 'ferro', True), C + Vector((0, 0, 0.87)), 0.095, 0.03, lados=32)
    cil(B('pat_camisa_flange', 'ferro', True), C + Vector((0, 0, 0.41)), 0.11, 0.02, lados=32)
    for j in range(8):
        a = j * PI / 4
        parafuso(C + Vector((math.cos(a) * 0.098, math.sin(a) * 0.098, 0.885)), (0, 0, 1), r=0.009)
    cil(B('pat_haste', 'cromo', True), C + Vector((0, 0, 0.2)), 0.055, 0.1, lados=24)
    caixa(B('pat_haste_oleo', 'oleo'), C + n * 0.055 + Vector((0, 0, 0.2)), (0.01, 0.003, 0.07), R)
    curva(B('pat_rotula', 'ferro', True), C + Vector((0, 0, 0.16)), 0.06, 16)
    cil(B('pat_sapata', 'ferro', True), C + Vector((0, 0, 0.115)), 0.22, 0.06, lados=40)
    for j in range(8):
        a = j * PI / 4 + 0.2
        caixa(B('pat_sapata_aleta', 'ferro'), C + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, 0.16)), (0.15, 0.018, 0.04),
              Matrix.Rotation(a, 3, 'Z'))
    for j in range(10):                                                      # trincas no concreto em volta
        a = j * 2 * PI / 10 + random.uniform(-0.2, 0.2)
        L = random.uniform(0.08, 0.26)
        rr = 0.22 + L / 2
        cpt = C + Vector((math.cos(a) * rr, math.sin(a) * rr, Z0 + 0.0006))
        if abs(cpt.x) < 1.47 and abs(cpt.y) < 1.47:
            caixa(B('trincas', 'chamusco'), cpt, (L, 0.006, 0.001), Matrix.Rotation(a + random.uniform(-0.25, 0.25), 3, 'Z'))
    for j in range(7):                                                       # lascas de concreto
        a = random.uniform(0, 2 * PI)
        rr = random.uniform(0.24, 0.34)
        pedra(B('lascas', 'concreto'), C + Vector((math.cos(a) * rr, math.sin(a) * rr, Z0 + 0.006)), random.uniform(0.01, 0.025))
    for j in range(4):
        mancha(B('lama_chao', 'lama'), (C.x + random.uniform(-0.25, 0.25), C.y + random.uniform(-0.25, 0.25)), random.uniform(0.05, 0.1), Z0 + 0.0012)
    caixa(B('pat_lama', 'lama'), C + Vector((0, 0, 0.148)), (0.3, 0.3, 0.004), Matrix.Rotation(0.5, 3, 'Z'))
    # cilindro de extensão sobre a viga
    cil(B('pat_ext_camisa', 'amarelo', True), P(1.17, 0, 0.405), 0.042, 0.34, n, lados=20)
    for rr in (1.03, 1.3):
        caixa(B('pat_ext_sela', 'ferro'), P(rr, 0, 0.375), (0.1, 0.03, 0.03), R)
    cil(B('pat_ext_haste', 'cromo', True), P(1.52, 0, 0.405), 0.022, 0.38, n, lados=14)
    caixa(B('pat_ext_orelha', 'ferro'), P(1.72, 0, 0.43), (0.07, 0.04, 0.06), R)
    # bloco de válvulas na raiz e mangueiras
    caixa(B('pat_valvula', 'grafite'), P(0.91, 0, 0.395), (0.13, 0.08, 0.07), R)
    for j in range(2):
        cil(B('pat_valvula_bobina', 'isol_verm' if j else 'amarelo', True), P(0.91, (j - 0.5) * 0.06, 0.45), 0.02, 0.04, lados=12)
    pts = bezier(P(0.96, 0.02, 0.40), P(0.99, 0.05, 0.43), P(0.99, 0.04, 0.44), P(1.0, 0.0, 0.42), 6)
    mangueira(B('mangueiras', 'borracha', True), pts, 0.011)
    pts = bezier(P(0.92, 0.07, 0.38), P(1.0, 0.16, 0.36), P(1.4, 0.15, 0.36), P(1.65, 0.14, 0.4), 12) + \
          bezier(P(1.65, 0.14, 0.4), P(1.75, 0.13, 0.45), P(1.75, 0.11, 0.78), P(1.81, 0.09, 0.8), 10)[1:]
    mangueira(B('mangueiras', 'borracha', True), pts, 0.013)
    for rr in (1.2, 1.5):
        caixa(B('abracadeiras', 'aco'), P(rr, 0.13, 0.36), (0.04, 0.045, 0.03), R)
    caixa(B('pat_listras', 'listras'), P(1.81, 0, 0.402), (0.24, 0.2, 0.004), R)
    stencil(P(1.11, 0, 0.29) + n * 0.0 + t * 0.101, rot_face(t), n=4, alt=0.04)
    for j in range(3):
        escorrido(P(random.uniform(0.95, 1.35), 0.101, 0.34), rot_face(t))
    mancha(B('oleo', 'oleo'), (C.x * 0.93, C.y * 0.93), 0.06, Z0 + 0.0014)
    PATOLAS.append((n, t))
    for j in range(5):
        caixa(B('pat_lama_viga', 'lama'), P(random.uniform(1.4, 1.9), random.choice((-1, 1)) * 0.0751, 0.24), (random.uniform(0.04, 0.1), 0.15, 0.03), R)

# ------------------------------------------------------------------ unidade hidráulica fixa (norte)
YT = 1.2
cil(B('hid_tanque', 'amarelo', True), Vector((-0.05, YT, 0.29)), 0.14, 0.9, Vector((1, 0, 0)), lados=32)
for x in (-0.5, 0.4):
    cil(B('hid_tampo', 'ferro', True), Vector((x, YT, 0.29)), 0.145, 0.02, Vector((1, 0, 0)), lados=32)
for x in (-0.3, 0.2):
    caixa_de(B('hid_sela', 'ferro'), (x - 0.03, YT - 0.13, Z0), (x + 0.03, YT + 0.13, 0.2))
    caixa_de(B('hid_cinta', 'aco'), (x - 0.02, YT - 0.146, 0.15), (x + 0.02, YT + 0.146, 0.3))
cil(B('hid_bocal', 'ferro', True), Vector((-0.25, YT, 0.45)), 0.03, 0.04, lados=16)
caixa_de(B('hid_visor', 'escuro'), (-0.08, YT - 0.142, 0.24), (0.08, YT - 0.13, 0.31))
caixa_de(B('hid_visor_moldura', 'ferro'), (-0.09, YT - 0.145, 0.235), (0.09, YT - 0.14, 0.245))
caixa_de(B('hid_visor_oleo', 'oleo'), (-0.075, YT - 0.1445, 0.245), (0.075, YT - 0.1435, 0.27))
cil(B('hid_motor', 'grafite', True), Vector((0.63, YT, 0.25)), 0.09, 0.26, Vector((1, 0, 0)), lados=28)
for j in range(6):
    cil(B('hid_motor_aletas', 'ferro', True), Vector((0.54 + j * 0.035, YT, 0.25)), 0.1, 0.008, Vector((1, 0, 0)), lados=28)
cil(B('hid_bomba', 'amarelo', True), Vector((0.465, YT, 0.25)), 0.06, 0.09, Vector((1, 0, 0)), lados=20)
caixa_de(B('hid_base', 'ferro'), (0.45, YT - 0.1, Z0), (0.8, YT + 0.1, 0.15))
cil(B('hid_filtro', 'isol_verm', True), Vector((0.47, YT + 0.1, 0.33)), 0.035, 0.11, lados=16)
pts = bezier(Vector((0.465, YT - 0.05, 0.3)), Vector((0.46, YT - 0.25, 0.36)), Vector((0.12, 0.95, 0.33)), Vector((0.08, AP_C + 0.02, 0.33)), 14)
mangueira(B('hid_cano', 'aco', True), pts, 0.018)
pts = bezier(Vector((-0.4, YT - 0.12, 0.27)), Vector((-0.4, 1.0, 0.27)), Vector((-0.1, 0.9, 0.26)), Vector((-0.08, AP_C + 0.02, 0.26)), 14)
mangueira(B('hid_cano', 'aco', True), pts, 0.018)
for x in (0.08, -0.08):
    cil(B('prensa', 'ferro', True), Vector((x, AP_C + 0.03, 0.33 if x > 0 else 0.26)), 0.032, 0.03, Vector((0, 1, 0)), lados=16)
for k in range(5):
    mancha(B('oleo', 'oleo'), (random.uniform(-0.4, 0.7), YT + random.uniform(-0.2, 0.15)), random.uniform(0.03, 0.08), Z0 + 0.0014)
pts = bezier(Vector((0.79, YT, 0.25)), Vector((0.95, YT, 0.25)), Vector((1.0, 1.46, Z0 + 0.02)), Vector((1.0, 1.5, Z0 + 0.02)), 8)
mangueira(B('cabos', 'cabo', True), pts, 0.018)
stencil(Vector((-0.2, YT - 0.142, 0.36)), rot_face(Vector((0, -1, 0))), n=5, alt=0.035)

# ------------------------------------------------------------------ paiol de recebimento (chão, boca S1)
PX0, PX1, PY0, PY1, PZ1 = -0.6, 0.6, -1.47, -1.08, 0.50
for a_, b_ in (((PX0, PY1 - 0.03, Z0), (PX1, PY1, PZ1)), ((PX0, PY0, Z0), (PX0 + 0.03, PY1, PZ1)), ((PX1 - 0.03, PY0, Z0), (PX1, PY1, PZ1)),
               ((PX0, PY0, PZ1 - 0.03), (PX1, PY1, PZ1)), ((PX0, PY0, Z0), (-0.22, PY0 + 0.03, PZ1)), ((0.22, PY0, Z0), (PX1, PY0 + 0.03, PZ1)),
               ((-0.22, PY0, 0.40), (0.22, PY0 + 0.03, PZ1)), ((-0.22, PY0, Z0), (0.22, PY0 + 0.03, 0.15))):
    caixa_de(B('paiol_chao', 'grafite'), a_, b_)
caixa_de(B('paiol_chao_fundo', 'escuro'), (PX0 + 0.03, PY1 - 0.035, Z0), (PX1 - 0.03, PY1 - 0.03, PZ1 - 0.03))
for x in (-0.25, 0.25):
    caixa_de(B('paiol_chao_quadro', 'amarelo'), (x - 0.03, PY0 - 0.012, Z0), (x + 0.03, PY0 + 0.0, PZ1 + 0.01))
caixa_de(B('paiol_chao_quadro', 'amarelo'), (-0.28, PY0 - 0.012, 0.40), (0.28, PY0, 0.44))
caixa_de(B('paiol_chao_listras', 'listras'), (-0.22, PY0 - 0.004, 0.44), (0.22, PY0, 0.49))
for x in (-0.45, 0.45):
    for z in (0.18, 0.42):
        parafuso((x, PY0 - 0.001, z), (0, -1, 0))
caixa_de(B('paiol_chao_tampa', 'amarelo'), (PX0 - 0.01, PY0 - 0.01, PZ1), (PX1 + 0.01, PY1 + 0.01, PZ1 + 0.012))
for x in (-0.5, -0.1, 0.3):
    caixa_de(B('paiol_chao_tampa_nervura', 'ferro'), (x, PY0 + 0.02, PZ1 + 0.012), (x + 0.03, PY1 - 0.02, PZ1 + 0.03))
for k in range(6):
    mancha(B('po_paiol', 'po'), (random.uniform(-0.5, 0.5), random.uniform(PY0 + 0.05, PY1 - 0.05)), random.uniform(0.04, 0.09), PZ1 + 0.0125)
remendo(Vector((0.42, PY0, 0.27)), rot_face(Vector((0, -1, 0))), 0.18, 0.14, mat='primer')
stencil(Vector((-0.42, PY0 - 0.0005, 0.30)), rot_face(Vector((0, -1, 0))), n=3, alt=0.04)
cil(B('paiol_lampada_base', 'ferro', True), Vector((-0.42, PY0 - 0.015, 0.43)), 0.03, 0.03, Vector((0, 1, 0)), lados=12)
curva(B('paiol_lampada', 'led_ambar', True), Vector((-0.42, PY0 - 0.035, 0.43)), 0.022, 12)
for y in (-1.43, -1.33, -1.23, -1.13):                                       # roletes da boca
    cil(B('paiol_rolete', 'aco', True), Vector((0, y, 0.165)), 0.018, 0.38, Vector((1, 0, 0)), lados=14)
caixa_de(B('paiol_trilho', 'ferro'), (-0.2, PY0, 0.14), (-0.18, PY1, 0.19))
caixa_de(B('paiol_trilho', 'ferro'), (0.18, PY0, 0.14), (0.2, PY1, 0.19))
# duto blindado do paiol ao pedestal (alimentação central)
caixa_de(B('duto', 'amarelo'), (-0.14, PY1, 0.22), (0.14, -AP_C + 0.01, 0.38))
for y in (-1.0, -0.86):
    caixa_de(B('duto_cinta', 'ferro'), (-0.155, y - 0.012, 0.205), (0.155, y + 0.012, 0.395))
caixa(B('duto_flange', 'ferro'), Vector((0, -AP_C - 0.012, 0.30)), (0.22, 0.016, 0.2))

# ------------------------------------------------------------------ granada e estojo (modelos)
def granada(nome, pai=None, mat='oliva'):
    """Granada de 0,38 m: corpo oliva, cinta de cobre, faixa amarela, ogiva e espoleta de latão. Origem na base."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    if pai is not None:
        e.parent = pai
    bm = bmesh.new()
    torno(bm, [(0.0, 0.0), (0.0, 0.044), (0.006, 0.05), (0.03, 0.052), (0.215, 0.052), (0.27, 0.045), (0.31, 0.03),
               (0.325, 0.02), (0.325, 0.0)], 28)
    suavizar(obj(nome + '_corpo', bm, mat, e))
    bm = bmesh.new()
    torno(bm, [(0.034, 0.0525), (0.06, 0.0525), (0.06, 0.0545), (0.034, 0.0545)], 28, fechado=True)
    obj(nome + '_cinta', bm, 'cobre', e)
    bm = bmesh.new()
    torno(bm, [(0.17, 0.0521), (0.2, 0.0521), (0.2, 0.0528), (0.17, 0.0528)], 28, fechado=True)
    obj(nome + '_faixa', bm, 'amarelo', e)
    bm = bmesh.new()
    torno(bm, [(0.32, 0.0), (0.32, 0.021), (0.345, 0.02), (0.365, 0.012), (0.38, 0.004), (0.381, 0.0)], 20)
    suavizar(obj(nome + '_espoleta', bm, 'latao', e))
    return e


PERFIL_ESTOJO = [(x * 3, r * 3) for x, r in [(0.0, 0.0), (0.0, 0.0205), (0.0055, 0.0205), (0.0065, 0.0165), (0.0105, 0.0165),
                                               (0.013, 0.0192), (0.058, 0.0186), (0.068, 0.0146), (0.086, 0.0143), (0.086, 0.0124),
                                               (0.03, 0.0124), (0.03, 0.0)]]


def estojo(nome, boca_mat, disparado=True, corpo='latao_gasto', pai=None):
    """Estojo de carga (0,28 m, aro Ø 123 mm): aro e ranhura do extrator, corpo afunilando, espoleta no fundo, faixa
    de marcação e boca (queimada se disparado; com tampão de feltro se cheio). Origem no meio."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    if pai is not None:
        e.parent = pai
    bm = bmesh.new()
    torno(bm, [(x - CX3, r) for x, r in PERFIL_ESTOJO], 28)
    suavizar(obj(nome + '_corpo', bm, corpo, e))
    bm = bmesh.new()
    torno(bm, [(0.258 - CX3, 0.0429), (0.279 - CX3, 0.0423), (0.279 - CX3, 0.0372), (0.258 - CX3, 0.0372)], 28, fechado=True)
    suavizar(obj(nome + '_boca', bm, boca_mat, e))
    bm = bmesh.new()
    torno(bm, [(0.09 - CX3, 0.0556), (0.13 - CX3, 0.0556), (0.13 - CX3, 0.0574), (0.09 - CX3, 0.0574)], 28, fechado=True)
    obj(nome + '_faixa', bm, 'isol_verm' if not disparado else 'chamusco', e)
    bm = bmesh.new()
    torno(bm, [(-CX3 - 0.0015, 0.0), (-CX3 - 0.0015, 0.016), (-CX3 + 0.0005, 0.016), (-CX3 + 0.0005, 0.0)], 18)
    obj(nome + '_espoleta', bm, 'espoleta', e)
    if not disparado:
        bm = bmesh.new()
        torno(bm, [(0.262 - CX3, 0.0), (0.262 - CX3, 0.0375), (0.275 - CX3, 0.0375), (0.275 - CX3, 0.0)], 20)
        obj(nome + '_tampao', bm, 'borracha', e)
    return e


# ------------------------------------------------------------------ giro (plataforma)
giro = bpy.data.objects.new('giro', None)
sc.collection.objects.link(giro)
G = 'giro'
cil(B('coroa', 'aco', True, G), Vector((0, 0, (Z_G0 + Z_G1) / 2)), R_COROA - 0.012, Z_G1 - Z_G0, lados=96)
for k in range(110):
    a = k * 2 * PI / 110
    caixa(B('coroa_dentes', 'aco', False, G), Vector((math.cos(a), math.sin(a), 0)) * (R_COROA - 0.004) + Vector((0, 0, (Z_G0 + Z_G1) / 2)),
          (0.026, 0.016, Z_G1 - Z_G0), Matrix.Rotation(a, 3, 'Z'))
prisma_polar(B('conves', 'chapa', False, G), r_deck, Z_G1, Z_D)
prisma_polar(B('conves_borda', 'amarelo', False, G), r_deck, Z_G1 - 0.01, Z_D + 0.012, dr=0.035, r_in=lambda a: r_deck(a) + 0.001)
for k in range(64):                                                          # parafusos na borda
    a = k * 2 * PI / 64
    r = r_deck(a) - 0.035
    parafuso((math.cos(a) * r, math.sin(a) * r, Z_D + 0.006), (0, 0, 1), G, 0.01)
for k in range(10):                                                          # pó e óleo no convés
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.3, r_deck(a) - 0.1)
    mancha(B('conves_po', 'po_escuro', False, G), (math.cos(a) * r, math.sin(a) * r), random.uniform(0.04, 0.09), Z_D + 0.0012)
for k in range(5):
    mancha(B('conves_oleo', 'oleo', False, G), (random.uniform(-0.8, 1.0), random.uniform(-0.4, 0.4)), random.uniform(0.03, 0.07), Z_D + 0.0015)
# nervuras/antiderrapante (barras soldadas) no convés da frente
for k in range(9):
    x = 0.55 + k * 0.08
    for s in (-1, 1):
        caixa_de(B('conves_barras', 'ferro', False, G), (x - 0.01, s * 0.12 - 0.08, Z_D), (x + 0.01, s * 0.12 + 0.08, Z_D + 0.006))

# munhoneiras (placas amarelas) com mancais
PERFIL_M = [(-0.42, Z_D), (0.52, Z_D), (0.52, 0.86), (0.27, 1.62), (0.12, 1.75), (-0.05, 1.75), (-0.22, 1.63), (-0.42, 1.02)]
for s in (-1, 1):
    y0, y1 = (0.30, 0.38) if s > 0 else (-0.38, -0.30)
    prisma_xz(B('munhoneira', 'amarelo', False, G), PERFIL_M, y0, y1)
    yo = s * 0.382
    for x, z in ((-0.36, 0.75), (-0.36, 0.95), (0.45, 0.75), (0.45, 0.88), (0.05, 0.75), (-0.2, 1.5), (0.25, 1.5), (0.35, 1.2), (-0.3, 1.2)):
        parafuso((x, yo, z), (0, s, 0), G, 0.013)
    caixa_de(B('munhoneira_pe', 'ferro', False, G), (-0.44, y0 - 0.03, Z_D), (0.54, y1 + 0.03, Z_D + 0.04))
    for x in (-0.3, 0.1, 0.4):                                                 # mãos-francesas
        caixa_de(B('munhoneira_aba', 'ferro', False, G), (x - 0.012, 0.38 if s > 0 else -0.47, Z_D),
                 (x + 0.012, 0.5 if s > 0 else -0.38, Z_D + 0.2))
    cil(B('mancal', 'ferro', True, G), Vector((TX, s * 0.41, TZ)), 0.13, 0.06, Vector((0, 1, 0)), lados=36)
    cil(B('mancal_tampa', 'aco', True, G), Vector((TX, s * 0.447, TZ)), 0.085, 0.014, Vector((0, 1, 0)), lados=28)
    for k in range(8):
        a = k * PI / 4
        parafuso((TX + math.cos(a) * 0.108, s * 0.442, TZ + math.sin(a) * 0.108), (0, s, 0), G, 0.01)
    cil(B('graxeira', 'latao', True, G), Vector((TX, s * 0.41, TZ + 0.14)), 0.008, 0.03, lados=8)
    Rm = rot_face(Vector((0, s, 0)))
    remendo(Vector((-0.18, yo, 0.95)), Rm, 0.16, 0.2, G, 'grafite' if s > 0 else 'primer')
    stencil(Vector((0.2, yo + s * 0.0005, 1.02)), Rm, G, n=6, alt=0.05)
    for j in range(5):
        escorrido(Vector((random.uniform(-0.3, 0.4), yo + s * 0.0005, random.uniform(1.1, 1.5))), Rm, G)
    caixa_de(B('munhoneira_listras', 'listras', False, G), (-0.42, y0 - 0.001 if s < 0 else y1 - 0.004, 0.68),
             (0.52, y0 + 0.004 if s < 0 else y1 + 0.001, 0.73))
    for k in range(4):                                                        # graxa escorrendo do mancal
        caixa(B('escorridos_oleo', 'oleo', False, G), Vector((TX + random.uniform(-0.06, 0.06), s * 0.441, TZ - 0.12 - k * 0.02)), (0.008, 0.002, 0.08))

# mancais dos cilindros de elevação (garfos no nariz)
for s in (-1, 1):
    y = s * YE
    for dy in (-0.105, 0.105):
        caixa_de(B('garfo_elev', 'ferro', False, G), (A_EL.x - 0.08, y + dy - 0.012, Z_D), (A_EL.x + 0.08, y + dy + 0.012, A_EL.z + 0.07))
    cil(B('pino', 'aco', True, G), Vector((A_EL.x, y, A_EL.z)), 0.03, 0.26, Vector((0, 1, 0)), lados=14)
    for dy in (-0.13, 0.13):
        cil(B('pino_porca', 'ferro', True, G), Vector((A_EL.x, y + dy, A_EL.z)), 0.04, 0.016, Vector((0, 1, 0)), lados=6)
    caixa_de(B('garfo_base', 'ferro', False, G), (A_EL.x - 0.1, y - 0.14, Z_D), (A_EL.x + 0.1, y + 0.14, Z_D + 0.02))
    for k in range(3):
        mancha(B('oleo', 'oleo', False, G), (A_EL.x + random.uniform(-0.1, 0.1), y + random.uniform(-0.08, 0.08)), random.uniform(0.02, 0.04), Z_D + 0.0215)

# junta rotativa central (cabos e óleo atravessam o giro)
cil(B('junta', 'ferro', True, G), Vector((0.32, 0, Z_D + 0.04)), 0.11, 0.08, lados=32)
cil(B('junta_topo', 'amarelo', True, G), Vector((0.32, 0, Z_D + 0.095)), 0.08, 0.03, lados=32)
for k in range(6):
    a = k * PI / 3
    parafuso((0.32 + math.cos(a) * 0.095, math.sin(a) * 0.095, Z_D + 0.083), (0, 0, 1), G, 0.009)

# unidade hidráulica da plataforma (lado −y)
caixa_de(B('hp_base', 'ferro', False, G), (-0.13, -0.93, Z_D), (0.42, -0.48, Z_D + 0.04))
cil(B('hp_tanque', 'amarelo', True, G), Vector((0.14, -0.79, Z_D + 0.2)), 0.12, 0.5, Vector((1, 0, 0)), lados=32)
for x in (-0.11, 0.39):
    cil(B('hp_tampo', 'ferro', True, G), Vector((x, -0.79, Z_D + 0.2)), 0.125, 0.016, Vector((1, 0, 0)), lados=32)
for x in (0.0, 0.28):
    caixa_de(B('hp_cinta', 'aco', False, G), (x - 0.015, -0.915, Z_D + 0.04), (x + 0.015, -0.665, Z_D + 0.33))
cil(B('hp_motor', 'grafite', True, G), Vector((0.1, -0.57, Z_D + 0.13)), 0.075, 0.24, Vector((1, 0, 0)), lados=28)
for j in range(5):
    cil(B('hp_motor_aletas', 'ferro', True, G), Vector((0.02 + j * 0.04, -0.57, Z_D + 0.13)), 0.084, 0.008, Vector((1, 0, 0)), lados=28)
cil(B('hp_bomba', 'amarelo', True, G), Vector((0.27, -0.57, Z_D + 0.13)), 0.055, 0.1, Vector((1, 0, 0)), lados=20)
caixa_de(B('hp_valvulas', 'grafite', False, G), (0.33, -0.66, Z_D + 0.04), (0.42, -0.50, Z_D + 0.2))
for k in range(3):
    cil(B('hp_valvula_bobina', ('amarelo', 'isol_verm', 'amarelo')[k], True, G), Vector((0.375, -0.63 + k * 0.05, Z_D + 0.23)), 0.018, 0.06, lados=12)
cil(B('hp_acumulador', 'isol_verm', True, G), Vector((-0.06, -0.57, Z_D + 0.2)), 0.05, 0.28, lados=24)
curva(B('hp_acumulador', 'isol_verm', True, G), Vector((-0.06, -0.57, Z_D + 0.34)), 0.05, 16)
cil(B('hp_filtro', 'aco', True, G), Vector((0.36, -0.82, Z_D + 0.38)), 0.035, 0.1, lados=16)
caixa_de(B('hp_visor', 'escuro', False, G), (0.06, -0.912, Z_D + 0.16), (0.22, -0.905, Z_D + 0.24))
stencil(Vector((0.14, -0.912, Z_D + 0.29)), rot_face(Vector((0, -1, 0))), G, n=4, alt=0.035)
for k in range(4):
    mancha(B('oleo', 'oleo', False, G), (random.uniform(-0.1, 0.4), random.uniform(-0.9, -0.5)), random.uniform(0.02, 0.05), Z_D + 0.0405)
caixa(B('hp_oleo_escorre', 'oleo', False, G), Vector((0.42, -0.6, Z_D + 0.1)), (0.003, 0.02, 0.1))
# mangueiras da unidade aos cilindros de elevação (do lado +y passa por tubo rígido no convés)
for s in (-1, 1):
    alvo = Vector((A_EL.x - 0.09, s * YE, A_EL.z + 0.02))
    if s < 0:
        pts = bezier(Vector((0.42, -0.6, Z_D + 0.12)), Vector((0.7, -0.6, Z_D + 0.12)), Vector((0.95, -0.45, A_EL.z + 0.1)), alvo, 14)
    else:
        pts = bezier(Vector((0.42, -0.55, Z_D + 0.08)), Vector((0.75, -0.5, Z_D + 0.02)), Vector((0.85, -0.2, Z_D + 0.03)),
                     Vector((0.9, 0.0, Z_D + 0.03)), 10)
        mangueira(B('hp_tubo', 'aco', True, G), pts, 0.014)
        pts = bezier(Vector((0.9, 0.0, Z_D + 0.03)), Vector((0.95, 0.2, Z_D + 0.03)), Vector((0.95, YE - 0.05, A_EL.z)), alvo, 12)
    mangueira(B('mangueiras', 'borracha', True, G), pts, 0.016)
for y in (-0.35, -0.15, 0.1):
    caixa(B('abracadeiras', 'aco', False, G), Vector((0.88, y, Z_D + 0.015)), (0.04, 0.03, 0.03))

# calha de ejeção (lado −y, atrás da culatra)
CH_X0, CH_X1, CH_Y0, CH_Y1 = -0.53, -0.17, -1.12, 0.03


def z_calha(y):
    return 0.70 + (y - 0.0) * 0.036


bm = B('calha', 'aco', False, G)
ys = [CH_Y0 + k * (CH_Y1 - CH_Y0) / 12 for k in range(13)]
for y0, y1 in zip(ys, ys[1:]):
    zm = z_calha((y0 + y1) / 2)
    caixa_de(B('calha', 'aco', False, G), (CH_X0, y0, zm - 0.012), (CH_X1, y1, zm))
    if y1 < -0.2:
        for x in (CH_X0 - 0.012, CH_X1):
            caixa_de(B('calha_lado', 'amarelo', False, G), (x, y0, zm - 0.012), (x + 0.012, y1, zm + 0.075))
for y in (-0.9, -0.5, -0.1):
    for x in (CH_X0 + 0.02, CH_X1 - 0.02):
        caixa_de(B('calha_pe', 'ferro', False, G), (x - 0.015, y - 0.015, Z_D), (x + 0.015, y + 0.015, z_calha(y) - 0.012))
caixa_de(B('calha_defletor', 'ferro', False, G), (CH_X0 - 0.012, 0.03, 0.69), (CH_X1 + 0.012, 0.045, 0.735))
for k in range(5):
    caixa_de(B('calha_fuligem', 'chamusco', False, G), (CH_X0 + 0.03 + k * 0.06, -0.95 + k * 0.1, z_calha(-0.6) + 0.0005),
             (CH_X0 + 0.06 + k * 0.06, -0.2, z_calha(-0.2) + 0.001))
caixa_de(B('calha_listras', 'listras', False, G), (CH_X0 - 0.013, CH_Y0, z_calha(CH_Y0) + 0.06), (CH_X1 + 0.013, CH_Y0 + 0.06, z_calha(CH_Y0) + 0.075))

# paiol blindado da plataforma (traseira +y) com grade e granadas
MX0, MX1, MY0, MY1, MZ1 = -1.15, -0.42, 0.55, 1.0, 1.22
SL0, SL1 = 0.68, 0.80                                                        # fenda da bandeja no teto
for a_, b_ in (((MX0, MY0, Z_D), (MX1, MY0 + 0.03, MZ1)), ((MX0, MY0, Z_D), (MX0 + 0.03, MY1, MZ1)), ((MX1 - 0.03, MY0, Z_D), (MX1, MY1, MZ1)),
               ((MX0, MY0, MZ1 - 0.03), (MX1, SL0, MZ1)), ((MX0, SL1, MZ1 - 0.03), (MX1, MY1, MZ1)),
               ((MX0, MY1 - 0.03, Z_D), (MX1, MY1, 0.70)), ((MX0, MY1 - 0.03, 1.15), (MX1, MY1, MZ1)),
               ((MX0, MY1 - 0.03, Z_D), (-1.1, MY1, MZ1)), ((-0.47, MY1 - 0.03, Z_D), (MX1, MY1, MZ1))):
    caixa_de(B('paiol', 'grafite', False, G), a_, b_)
caixa_de(B('paiol_fundo', 'escuro', False, G), (MX0 + 0.03, MY0 + 0.03, Z_D), (MX1 - 0.03, MY0 + 0.035, MZ1 - 0.03))
for x in (MX0 - 0.01, MX1 - 0.02):
    caixa_de(B('paiol_quina', 'amarelo', False, G), (x, MY0 - 0.01, Z_D), (x + 0.03, MY1 + 0.01, MZ1 + 0.012))
caixa_de(B('paiol_teto_borda', 'amarelo', False, G), (MX0, MY1 - 0.01, MZ1), (MX1, MY1 + 0.01, MZ1 + 0.012))
for y in (SL0 - 0.015, SL1 + 0.005):
    caixa_de(B('paiol_guia', 'ferro', False, G), (MX0 + 0.03, y, MZ1), (MX1 - 0.03, y + 0.01, MZ1 + 0.02))
caixa_de(B('paiol_fenda_fundo', 'escuro', False, G), (MX0 + 0.03, SL0, 1.0), (MX1 - 0.03, SL1, 1.003))
caixa_de(B('paiol_listras', 'listras', False, G), (MX0 + 0.04, MY1 - 0.001, 1.16), (MX1 - 0.04, MY1 + 0.003, 1.2))
for k in range(9):                                                           # grade
    x = -1.08 + k * 0.073
    tubo(B('paiol_grade', 'aco', True, G), (x, MY1 - 0.012, 0.70), (x, MY1 - 0.012, 1.15), 0.007, 8)
for z in (0.8, 0.93, 1.06):
    caixa_de(B('paiol_grade', 'ferro', False, G), (-1.1, MY1 - 0.022, z - 0.006), (-0.47, MY1 - 0.002, z + 0.006))
for x in (-1.1, -0.47):
    for z in (0.67, 1.18):
        parafuso((x, MY1 + 0.001, z), (0, 1, 0), G, 0.011)
for z in (0.74, 0.87, 1.0):                                                  # prateleiras e munição guardada
    caixa_de(B('paiol_prateleira', 'ferro', False, G), (MX0 + 0.03, 0.8, z - 0.075), (MX1 - 0.03, 0.97, z - 0.062))
    gg = granada('granada_paiol', giro)
    gg.location = (-0.835, 0.885, z)
    ee = estojo('carga_paiol', 'boca_fria', False, 'latao_gasto', giro)
    ee.location = (-0.98, 0.885, z)
remendo(Vector((-0.78, MY0, 0.85)), rot_face(Vector((0, -1, 0))), 0.2, 0.16, G, 'amarelo')
stencil(Vector((-0.78, MY0 - 0.0005, 1.1)), rot_face(Vector((0, -1, 0))), G, n=5, alt=0.04)
for k in range(4):
    escorrido(Vector((random.uniform(-1.1, -0.5), MY1 + 0.0005, 0.66)), rot_face(Vector((0, 1, 0))), G)
for k, m in enumerate(('led_verde', 'led_verde', 'led_ambar')):
    cil(B('led_' + m, m, False, G), Vector((MX1 + 0.001, 0.62 + k * 0.04, 1.15)), 0.008, 0.006, Vector((1, 0, 0)), lados=10)

# mastro do telêmetro (traseira −y)
MS = Vector((-0.95, -0.62, Z_D))
cil(B('mastro_base', 'ferro', True, G), MS + Vector((0, 0, 0.02)), 0.11, 0.04, lados=24)
for k in range(6):
    a = k * PI / 3
    parafuso(MS + Vector((math.cos(a) * 0.09, math.sin(a) * 0.09, 0.045)), (0, 0, 1), G, 0.009)
tubo(B('mastro', 'amarelo', True, G), MS + Vector((0, 0, 0.04)), MS + Vector((0, 0, 1.36)), 0.045, 24)
for z in (0.5, 0.95):
    cil(B('mastro_cinta', 'ferro', True, G), MS + Vector((0, 0, z)), 0.052, 0.03, lados=24)
for a in (0.4, 2.5, 4.4):                                                    # escoras
    p0 = MS + Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, 0.0))
    if r_deck(math.atan2(p0.y, p0.x)) < p0.length:
        p0 = MS + Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, 0.0))
    tubo(B('mastro_escora', 'ferro', True, G), p0 + Vector((0, 0, 0.01)), MS + Vector((0, 0, 0.5)), 0.016, 10)
    caixa(B('mastro_escora_pe', 'ferro', False, G), p0 + Vector((0, 0, 0.008)), (0.06, 0.06, 0.016))
caixa_de(B('mastro_caixa', 'grafite', False, G), MS + Vector((0.05, -0.1, 0.08)), MS + Vector((0.25, 0.06, 0.32)))
caixa_de(B('mastro_caixa_tampa', 'amarelo', False, G), MS + Vector((0.25, -0.09, 0.09)), MS + Vector((0.256, 0.05, 0.31)))
for k, m in enumerate(('led_verde', 'led_ambar')):
    cil(B('led_' + m, m, False, G), MS + Vector((0.258, -0.06 + k * 0.05, 0.28)), 0.008, 0.005, Vector((1, 0, 0)), lados=10)
pts = [MS + Vector((0.055, 0.0, 0.2))] + [MS + Vector((0.05 - 0.002 * k, 0.0, 0.32 + k * 0.1)) for k in range(11)]
for i in range(2):
    mangueira(B('cabos', 'cabo', True, G), [p + Vector((0.0, (i - 0.5) * 0.028, 0)) for p in pts], 0.012)
for z in (0.5, 0.8, 1.1):
    cil(B('abracadeiras', 'aco', True, G), MS + Vector((0.0, 0, z)), 0.075, 0.02, lados=20)
pts = bezier(MS + Vector((0.15, -0.1, 0.12)), MS + Vector((0.15, -0.2, 0.06)), MS + Vector((0.25, -0.25, 0.06)),
             MS + Vector((0.25, -0.25, 0.02)), 10)
feixe(B('cabos', 'cabo', True, G), B('abracadeiras', 'aco', True, G), pts, Vector((1, 0, 0)), n=2, r=0.011, passo=5)
cil(B('prensa', 'ferro', True, G), MS + Vector((0.25, -0.25, 0.015)), 0.04, 0.03, lados=16)
tel = bpy.data.objects.new('telemetro', None)
sc.collection.objects.link(tel)
tel.parent = giro
tel.location = MS + Vector((0, 0, 1.42))
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.04)), 0.07, 0.05, lados=24)                         # cabeça de giro
caixa_de(bm, (-0.05, -0.08, -0.02), (0.05, 0.08, 0.09))
obj('tel_cabeca', bm, 'ferro', tel)
tilt = bpy.data.objects.new('telemetro_tilt', None)
sc.collection.objects.link(tilt)
tilt.parent = tel
tilt.location = (0, 0, 0.12)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.045, 0.82, Vector((0, 1, 0)), lados=28)
obj('tel_tubo', bm, 'amarelo', tilt)
bm = bmesh.new()
for s in (-1, 1):
    caixa_de(bm, (-0.07, s * 0.41 - 0.06, -0.06), (0.09, s * 0.41 + 0.06, 0.06))
caixa_de(bm, (-0.08, -0.09, -0.07), (0.08, 0.09, 0.08))
obj('tel_corpo', bm, 'grafite', tilt)
bm = bmesh.new()
for s in (-1, 1):
    cil(bm, Vector((0.095, s * 0.41, 0)), 0.04, 0.016, Vector((1, 0, 0)), lados=24)
cil(bm, Vector((0.085, 0.0, 0.0)), 0.05, 0.016, Vector((1, 0, 0)), lados=24)
obj('tel_aros', bm, 'ferro', tilt)
bm = bmesh.new()
for s in (-1, 1):
    cil(bm, Vector((0.104, s * 0.41, 0)), 0.03, 0.004, Vector((1, 0, 0)), lados=24)
obj('tel_lentes', bm, 'vidro', tilt)
bm = bmesh.new()
cil(bm, Vector((0.094, 0.0, 0.0)), 0.038, 0.004, Vector((1, 0, 0)), lados=24)
obj('tel_olho', bm, 'olho', tilt)
bm = bmesh.new()
cil(bm, Vector((0.083, 0.0, 0.06)), 0.007, 0.01, Vector((1, 0, 0)), lados=10)
obj('tel_laser', bm, 'laser', tilt)
bm = bmesh.new()
toro(bm, Vector((0.095, 0, 0)), 0.046, 0.005, 32, 8, Matrix.Rotation(PI / 2, 3, 'Y'))
obj('tel_aro_olho', bm, 'cromo', tilt)
bm = bmesh.new()
caixa_de(bm, (-0.081, -0.07, 0.03), (-0.0795, 0.07, 0.06))
obj('tel_listras', bm, 'listras', tilt)
bm = bmesh.new()
tubo(bm, (-0.04, 0.06, 0.08), (-0.04, 0.06, 0.62), 0.005, 8)
cil(bm, Vector((-0.04, 0.06, 0.09)), 0.016, 0.03, lados=12)
obj('tel_antena', bm, 'aco', tilt)
bm = bmesh.new()
curva(bm, Vector((-0.04, 0.06, 0.625)), 0.011, 10)
antena_led = obj('tel_antena_led', bm, 'led_ambar', tilt)
radar = bpy.data.objects.new('radar', None)
sc.collection.objects.link(radar)
radar.parent = tilt
radar.location = (0.0, -0.03, 0.08)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.02)), 0.015, 0.04, lados=12)
caixa_de(bm, (-0.03, -0.2, 0.045), (0.0, 0.2, 0.1))
obj('radar_placa', bm, 'grafite', radar)
bm = bmesh.new()
for k in range(8):
    y = -0.175 + k * 0.05
    caixa_de(bm, (0.0, y - 0.01, 0.055), (0.002, y + 0.01, 0.09))
obj('radar_fendas', bm, 'escuro', radar)
luz_o = bpy.data.lights.new('Olho', 'POINT')
luz_o.color = VIOLETA
luz_o.energy = 0.8
luz_o.shadow_soft_size = 0.02
lo = bpy.data.objects.new('Olho', luz_o)
sc.collection.objects.link(lo)
lo.parent = tilt
lo.location = (0.14, 0, 0)

# cabos da junta rotativa à unidade hidráulica e ao carregador
pts = bezier(Vector((0.32, -0.1, Z_D + 0.04)), Vector((0.3, -0.3, Z_D + 0.02)), Vector((0.1, -0.4, Z_D + 0.02)), Vector((0.1, -0.5, Z_D + 0.09)), 10)
feixe(B('cabos', 'cabo', True, G), B('abracadeiras', 'aco', True, G), pts, Vector((0, 0, 1)), n=2, r=0.012, passo=5)

# ------------------------------------------------------------------ canhão: berço (inclina) e cano (recua)
canhao = bpy.data.objects.new('canhao', None)
sc.collection.objects.link(canhao)
canhao.parent = giro
canhao.location = (TX, 0, TZ)
cano = bpy.data.objects.new('cano', None)
sc.collection.objects.link(cano)
cano.parent = canhao
K, CN = 'canhao', 'cano'
# munhão e bloco do berço
cil(B('munhao', 'aco', True, K), Vector((0, 0, 0)), 0.075, 0.82, Vector((0, 1, 0)), lados=32)
caixa_de(B('berco_bloco', 'amarelo', False, K), (-0.12, -0.26, -0.15), (0.35, 0.26, 0.15))
for s in (-1, 1):
    cil(B('berco_cubo', 'ferro', True, K), Vector((0, s * 0.275, 0)), 0.12, 0.03, Vector((0, 1, 0)), lados=32)
    for k in range(6):
        a = k * PI / 3 + 0.3
        parafuso((math.cos(a) * 0.1, s * 0.291, math.sin(a) * 0.1), (0, s, 0), K, 0.01)
    remendo(Vector((0.22, s * 0.26, 0.0)), rot_face(Vector((0, s, 0))), 0.14, 0.18, K, 'grafite')
caixa_de(B('berco', 'amarelo', False, K), (0.35, -0.15, -0.13), (1.52, 0.15, 0.13))
for x in (0.6, 0.95, 1.25, 1.49):
    caixa_de(B('berco_cinta', 'ferro', False, K), (x - 0.02, -0.158, -0.138), (x + 0.02, 0.158, 0.138))
for x in (0.45, 0.8, 1.1, 1.38):
    for s in (-1, 1):
        parafuso((x, s * 0.151, 0.08), (0, s, 0), K, 0.011)
        parafuso((x, s * 0.151, -0.08), (0, s, 0), K, 0.011)
cil(B('berco_bucha', 'bronze', True, K), Vector((1.56, 0, 0)), 0.125, 0.08, Vector((1, 0, 0)), lados=36)
toro(B('berco_retentor', 'borracha', True, K), Vector((1.605, 0, 0)), 0.093, 0.01, 36, 8, Matrix.Rotation(PI / 2, 3, 'Y'))
stencil(Vector((1.0, -0.151, 0.0)), rot_face(Vector((0, -1, 0))), K, n=6, alt=0.05)
caixa_de(B('berco_listras', 'listras', False, K), (0.38, -0.152, 0.09), (0.6, -0.149, 0.125))
for k in range(5):
    escorrido(Vector((random.uniform(0.4, 1.6), 0.1505, 0.12)), rot_face(Vector((0, 1, 0))), K, 'ferrugem', random.uniform(0.05, 0.14))
# cilindros de recuo (em cima) e recuperador (embaixo): camisas no berço
for s in (-1, 1):
    cil(B('recuo_camisa', 'grafite' if s > 0 else 'amarelo', True, K), Vector((0.62, s * 0.1, 0.21)), 0.055, 1.2, Vector((1, 0, 0)), lados=28)
    for x in (0.03, 1.21):
        cil(B('recuo_tampa', 'ferro', True, K), Vector((x, s * 0.1, 0.21)), 0.062, 0.03, Vector((1, 0, 0)), lados=28)
    for x in (0.3, 0.9):
        caixa_de(B('recuo_sela', 'ferro', False, K), (x - 0.03, s * 0.1 - 0.05, 0.13), (x + 0.03, s * 0.1 + 0.05, 0.17))
cil(B('recuperador', 'amarelo', True, K), Vector((0.7, 0, -0.215)), 0.07, 1.3, Vector((1, 0, 0)), lados=32)
for x in (0.04, 1.36):
    cil(B('recuperador_tampa', 'ferro', True, K), Vector((x, 0, -0.215)), 0.078, 0.035, Vector((1, 0, 0)), lados=32)
for x in (0.4, 1.0):
    caixa_de(B('recuperador_sela', 'ferro', False, K), (x - 0.03, -0.06, -0.15), (x + 0.03, 0.06, -0.13))
cil(B('nitrogenio', 'isol_verm', True, K), Vector((0.9, 0.12, -0.24)), 0.04, 0.42, Vector((1, 0, 0)), lados=20)
curva(B('nitrogenio', 'isol_verm', True, K), Vector((1.11, 0.12, -0.24)), 0.04, 14)
cil(B('manometro', 'aco', True, K), Vector((0.67, 0.12, -0.24)), 0.022, 0.04, Vector((1, 0, 0)), lados=16)
pts = bezier(Vector((1.21, 0.1, 0.21)), Vector((1.3, 0.16, 0.2)), Vector((1.4, 0.18, -0.05)), Vector((1.36, 0.06, -0.17)), 10)
mangueira(B('mangueiras', 'borracha', True, K), pts, 0.012)
pts = bezier(Vector((1.21, -0.1, 0.21)), Vector((1.3, -0.16, 0.2)), Vector((1.4, -0.18, -0.05)), Vector((1.36, -0.06, -0.17)), 10)
mangueira(B('mangueiras', 'borracha', True, K), pts, 0.012)
for k in range(3):
    caixa(B('escorridos_oleo', 'oleo', False, K), Vector((1.22, s * 0.1, 0.17 - k * 0.03)), (0.003, 0.012, 0.04))
# garfos dos cilindros de elevação no berço
for s in (-1, 1):
    y = s * YE
    for dy in (-0.065, 0.065):
        caixa_de(B('berco_garfo', 'ferro', False, K), (B_EL.x - 0.07, y + dy - 0.012, B_EL.z - 0.05), (B_EL.x + 0.07, y + dy + 0.012, -0.06))
    caixa_de(B('berco_braco', 'amarelo', False, K), (B_EL.x - 0.08, s * 0.15 if s > 0 else -(YE + 0.08), -0.13),
             (B_EL.x + 0.08, YE + 0.08 if s > 0 else -0.15, -0.05))
    cil(B('pino', 'aco', True, K), Vector((B_EL.x, y, B_EL.z)), 0.026, 0.17, Vector((0, 1, 0)), lados=14)
# cabo de dados do berço até o munhão
pts = bezier(Vector((1.0, -0.151, -0.1)), Vector((0.7, -0.175, -0.12)), Vector((0.3, -0.27, -0.12)), Vector((0.1, -0.30, -0.06)), 12)
feixe(B('cabos', 'cabo', True, K), B('abracadeiras', 'aco', True, K), pts, Vector((0, 0, 1)), n=2, r=0.01, passo=4)

# cano: tubo afinando, evacuador, freio de boca
bm = B('tubo', 'cano_aco', True, CN)
torno(bm, [(-0.1, 0.0), (-0.1, 0.095), (0.0, 0.095), (0.02, 0.09), (2.3, 0.079), (3.3, 0.069), (3.3, 0.0)], 40)
bm = B('evacuador', 'cano_aco', True, CN)
torno(bm, [(2.35, 0.0), (2.35, 0.08), (2.41, 0.106), (2.67, 0.104), (2.75, 0.075), (2.75, 0.0)], 40)
for x in (2.42, 2.66):
    cil(B('evacuador_anel', 'ferro', True, CN), Vector((x, 0, 0)), 0.112, 0.016, Vector((1, 0, 0)), lados=40)
for x in (1.0, 1.7):
    cil(B('cano_anel', 'ferro', True, CN), Vector((x, 0, 0)), 0.088, 0.02, Vector((1, 0, 0)), lados=40)
FREIO = ((3.35, 3.39), (3.48, 3.52), (3.61, 3.66))
bm = B('freio', 'queimado', False, CN)
cil(bm, Vector((3.32, 0, 0)), 0.092, 0.06, Vector((1, 0, 0)), lados=32)
for x0, x1 in FREIO:                                                        # chicanas
    caixa_de(bm, (x0, -0.12, -0.1), (x1, 0.12, 0.1))
for s in (-1, 1):
    caixa_de(bm, (3.35, -0.12, s * 0.1 - (0.026 if s > 0 else 0.0)), (3.66, 0.12, s * 0.1 + (0.0 if s > 0 else 0.026)))
cil(B('freio_boca', 'escuro', False, CN), Vector((3.661, 0, 0)), 0.058, 0.003, Vector((1, 0, 0)), lados=28)
for x0, x1 in FREIO[:2]:
    cil(B('freio_furo', 'escuro', False, CN), Vector((x1 + 0.0005, 0, 0)), 0.062, 0.002, Vector((1, 0, 0)), lados=24)
bm = B('freio_brasa', 'brasa_freio', False, CN)
for x0, x1 in FREIO:
    for s in (-1, 1):
        caixa_de(bm, (x0 + 0.004, s * 0.12 - 0.001, -0.07), (x1 - 0.004, s * 0.12 + 0.001, 0.07))
for k in range(10):                                                          # fuligem na ponta do cano
    a = random.uniform(0, 2 * PI)
    L = random.uniform(0.08, 0.3)
    caixa(B('fuligem_cano', 'chamusco', False, CN), Vector((3.29 - L / 2, math.cos(a) * 0.0705, math.sin(a) * 0.0705)),
          (L, 0.02, 0.003), Matrix.Rotation(a + PI / 2, 3, 'X'))
for k in range(8):
    a = random.uniform(0, 2 * PI)
    L = random.uniform(0.04, 0.12)
    caixa(B('fuligem_cano', 'chamusco', False, CN), Vector((2.75 + L / 2, math.cos(a) * 0.0775, math.sin(a) * 0.0775)),
          (L, 0.015, 0.003), Matrix.Rotation(a + PI / 2, 3, 'X'))
MUZ = Vector((3.67, 0, 0))
# culatra: bloco da frente (câmara), bochechas, ponte; cunha vertical (sobe/desce)
caixa_de(B('culatra', 'grafite', False, CN), (-0.33, -0.17, -0.17), (-0.135, 0.17, 0.17))
for s in (-1, 1):
    caixa_de(B('culatra', 'grafite', False, CN), (-0.5, s * 0.12 if s > 0 else -0.17, -0.17), (-0.33, 0.17 if s > 0 else -0.12, 0.17))
caixa_de(B('culatra', 'grafite', False, CN), (-0.5, -0.12, 0.13), (-0.33, 0.12, 0.17))
for x in (-0.49, -0.148):
    caixa_de(B('culatra_cinta', 'aco', False, CN), (x - 0.012, -0.176, -0.176), (x + 0.012, 0.176, 0.176))
cil(B('camara', 'escuro', False, CN), Vector((-0.3305, 0, 0)), 0.066, 0.001, Vector((1, 0, 0)), lados=28)
toro(B('camara_aro', 'aco', True, CN), Vector((-0.3315, 0, 0)), 0.07, 0.006, 32, 8, Matrix.Rotation(PI / 2, 3, 'Y'))
for sy in (-1, 1):
    for sz in (-1, 1):
        parafuso((-0.5, sy * 0.145, sz * 0.145), (-1, 0, 0), CN, 0.012)
stencil(Vector((-0.22, -0.1705, 0.05)), rot_face(Vector((0, -1, 0))), CN, n=4, alt=0.04)
for k in range(6):                                                           # fuligem saindo da culatra
    caixa_de(B('fuligem_culatra', 'chamusco', False, CN), (-0.5005, -0.11 + k * 0.04, -0.17), (-0.497, -0.095 + k * 0.04, -0.17 + random.uniform(0.05, 0.14)))
# garra do recuo (em cima) e do recuperador (embaixo); hastes cromadas entrando nas camisas
caixa_de(B('culatra_garra', 'ferro', False, CN), (-0.3, -0.16, 0.17), (-0.18, 0.16, 0.27))
caixa_de(B('culatra_garra', 'ferro', False, CN), (-0.3, -0.06, -0.28), (-0.18, 0.06, -0.17))
for s in (-1, 1):
    cil(B('recuo_haste', 'cromo', True, CN), Vector((0.16, s * 0.1, 0.21)), 0.026, 0.7, Vector((1, 0, 0)), lados=20)
    cil(B('recuo_porca', 'aco', True, CN), Vector((-0.17, s * 0.1, 0.21)), 0.04, 0.025, Vector((1, 0, 0)), lados=6)
cil(B('recup_haste', 'cromo', True, CN), Vector((0.2, 0, -0.215)), 0.034, 0.78, Vector((1, 0, 0)), lados=20)
caixa_de(B('recuo_oleo', 'oleo', False, CN), (-0.1, 0.074, 0.18), (0.02, 0.076, 0.24))
# cilindro de abertura da cunha (bochecha +y) com fenda
caixa_de(B('cunha_fenda', 'escuro', False, CN), (-0.44, 0.1702, -0.17), (-0.40, 0.1712, -0.06))
cil(B('cunha_cil', 'amarelo', True, CN), Vector((-0.42, 0.2, 0.1)), 0.024, 0.32, lados=18)
for z in (0.06, 0.2):
    caixa_de(B('cunha_cil_suporte', 'ferro', False, CN), (-0.44, 0.17, z - 0.012), (-0.40, 0.226, z + 0.012))
pts = bezier(Vector((-0.42, 0.224, 0.24)), Vector((-0.42, 0.26, 0.3)), Vector((-0.3, 0.2, 0.32)), Vector((-0.24, 0.12, 0.27)), 8)
mangueira(B('mangueiras', 'borracha', True, CN), pts, 0.008)

cunha = bpy.data.objects.new('cunha', None)
sc.collection.objects.link(cunha)
cunha.parent = cano
bm = bmesh.new()
caixa_de(bm, (-0.48, -0.118, -0.17), (-0.345, 0.118, 0.129))
obj('cunha_bloco', bm, 'aco', cunha)
bm = bmesh.new()
caixa_de(bm, (-0.49, -0.04, -0.06), (-0.48, 0.04, 0.04))
cil(bm, Vector((-0.493, 0, 0)), 0.018, 0.012, Vector((1, 0, 0)), lados=14)
obj('cunha_percussor', bm, 'ferro', cunha)
bm = bmesh.new()
caixa_de(bm, (-0.44, 0.118, -0.12), (-0.40, 0.2, -0.08))
obj('cunha_orelha', bm, 'ferro', cunha)
bm = bmesh.new()
cil(bm, Vector((-0.42, 0.2, 0.06)), 0.012, 0.32, lados=14)
suavizar(obj('cunha_haste', bm, 'cromo', cunha))
bm = bmesh.new()
for k in range(3):
    caixa_de(bm, (-0.4805, -0.1 + k * 0.08, -0.15), (-0.4802, -0.07 + k * 0.08, 0.1))
obj('cunha_fuligem', bm, 'chamusco', cunha)

# ------------------------------------------------------------------ cilindros de elevação (telescópicos, 3 estágios)
def B_el_giro(pitch, s):
    return Matrix.Translation((TX, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y') @ Vector((B_EL.x, s * YE, B_EL.z))


DMIN = min((B_el_giro(math.radians(p), 1) - A_EL).length for p in range(4, 61))
DMAX = max((B_el_giro(math.radians(p), 1) - A_EL).length for p in range(4, 61))
L0 = DMIN - EYE - 0.02
LS = L0 - 0.06
print('ELEVACAO dmin %.3f dmax %.3f L0 %.3f e_max %.3f LS %.3f' % (DMIN, DMAX, L0, (DMAX - L0 - EYE) / 3, LS))
RAIOS = (0.09, 0.072, 0.057, 0.042)
elevs = []
for i, s in enumerate((1, -1)):
    p = bpy.data.objects.new('elev%d' % i, None)
    sc.collection.objects.link(p)
    p.parent = giro
    p.location = Vector((A_EL.x, s * YE, A_EL.z))
    p.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.05, 0.18, Vector((1, 0, 0)), lados=20)             # olhal (pino ao longo de x local = y)
    cil(bm, Vector((0, 0, 0.06 + (L0 - 0.06) / 2)), RAIOS[0], L0 - 0.06, lados=36)
    cil(bm, Vector((0, 0, 0.19)), RAIOS[0] + 0.012, 0.03, lados=36)
    cil(bm, Vector((0, 0, L0 - 0.015)), RAIOS[0] + 0.014, 0.03, lados=36)
    suavizar(obj('elev%d_camisa' % i, bm, 'amarelo' if i == 0 else 'grafite', p))
    bm = bmesh.new()
    for z in (0.13, L0 - 0.08):
        cil(bm, Vector((0, -RAIOS[0] - 0.008, z)), 0.014, 0.024, Vector((0, 1, 0)), lados=12)
    mangueira(bm, bezier(Vector((0, -RAIOS[0] - 0.02, 0.13)), Vector((0, -0.14, 0.2)), Vector((0, -0.14, L0 - 0.15)),
                         Vector((0, -RAIOS[0] - 0.02, L0 - 0.08)), 12), 0.011)
    suavizar(obj('elev%d_mangueira' % i, bm, 'borracha', p))
    bm = bmesh.new()
    for k in range(6):
        caixa_de(bm, (-0.02 + 0.006 * k, RAIOS[0] - 0.002, 0.25 + k * 0.03), (-0.01 + 0.006 * k, RAIOS[0] + 0.001, 0.25 + k * 0.03 + 0.08))
    obj('elev%d_escorrido' % i, bm, 'oleo', p)
    bm = bmesh.new()
    caixa_de(bm, (-0.05, -RAIOS[0] - 0.003, L0 * 0.45), (0.05, -RAIOS[0] + 0.004, L0 * 0.45 + 0.04))
    obj('elev%d_listras' % i, bm, 'listras', p)
    pai = p
    estagios = []
    for k in range(1, 4):
        e = bpy.data.objects.new('elev%d_estagio%d' % (i, k), None)
        sc.collection.objects.link(e)
        e.parent = pai
        bm = bmesh.new()
        r = RAIOS[k]
        if k < 3:
            cil(bm, Vector((0, 0, LS / 2)), r, LS, lados=32)
            cil(bm, Vector((0, 0, LS - 0.01)), r + 0.009, 0.022, lados=32)
            suavizar(obj('elev%d_tubo%d' % (i, k), bm, 'cromo' if k == 2 else 'aco', e))
        else:
            cil(bm, Vector((0, 0, LS / 2)), r, LS, lados=28)
            cil(bm, Vector((0, 0, LS + EYE)), 0.045, 0.1, Vector((1, 0, 0)), lados=20)
            cil(bm, Vector((0, 0, LS + EYE / 2)), 0.03, EYE, lados=16)
            suavizar(obj('elev%d_haste' % i, bm, 'cromo', e))
        estagios.append(e)
        pai = e
    elevs.append((p, estagios, s))

# ------------------------------------------------------------------ carregador (bandeja, soquete de corrente)
carreg = bpy.data.objects.new('carregador', None)
sc.collection.objects.link(carreg)
carreg.parent = giro
carreg.location = (TX, 0, TZ)
carreg.rotation_euler = (0, -P_LOAD, 0)
M_CAR = Matrix.Translation((TX, 0, TZ)) @ Matrix.Rotation(-P_LOAD, 4, 'Y')
PIV = Vector((0, 0.42, -0.42))
R0 = Vector((0, -0.42, 0.32))
XB = (-0.62, -1.10)
# postes do eixo (no giro) e eixo de giro da bandeja (no carregador)
for x in XB + (-1.2,):
    pw = M_CAR @ Vector((x, PIV.y, PIV.z))
    caixa_de(B('car_poste', 'amarelo', False, G), (pw.x - 0.04, pw.y - 0.04, Z_D), (pw.x + 0.04, pw.y + 0.04, pw.z - 0.03))
    caixa_de(B('car_poste_pe', 'ferro', False, G), (pw.x - 0.07, pw.y - 0.07, Z_D), (pw.x + 0.07, pw.y + 0.07, Z_D + 0.02))
    for sx in (-1, 1):
        parafuso((pw.x + sx * 0.055, pw.y + 0.055, Z_D + 0.022), (0, 0, 1), G, 0.009)
    escorrido(Vector((pw.x, pw.y - 0.0405, pw.z - 0.1)), rot_face(Vector((0, -1, 0))), G)
bm = B('car_eixo', 'aco', True, 'carreg')
cil(bm, Vector((-0.86, PIV.y, PIV.z)), 0.03, 0.72, Vector((1, 0, 0)), lados=16)
for x in XB + (-1.2,):
    cil(B('car_mancal', 'ferro', True, 'carreg'), Vector((x, PIV.y, PIV.z)), 0.055, 0.06, Vector((1, 0, 0)), lados=20)
cil(B('car_atuador', 'amarelo', True, 'carreg'), Vector((-1.28, PIV.y, PIV.z)), 0.075, 0.1, Vector((1, 0, 0)), lados=28)
cil(B('car_atuador_tampa', 'ferro', True, 'carreg'), Vector((-1.335, PIV.y, PIV.z)), 0.06, 0.02, Vector((1, 0, 0)), lados=24)
pts = bezier(Vector((-1.3, PIV.y + 0.05, PIV.z - 0.06)), Vector((-1.3, PIV.y + 0.15, PIV.z - 0.2)),
             Vector((-1.2, 0.5, -0.8)), Vector((-1.1, 0.48, -0.86)), 10)
mangueira(B('mangueiras', 'borracha', True, 'carreg'), pts, 0.011)

braco = bpy.data.objects.new('braco_bandeja', None)
sc.collection.objects.link(braco)
braco.parent = carreg
braco.location = PIV
for x in XB:
    bm = bmesh.new()
    viga(bm, Vector((x, 0, 0)), Vector((x, R0.y, R0.z)), 0.05)
    cil(bm, Vector((x, 0, 0)), 0.045, 0.07, Vector((1, 0, 0)), lados=16)
    cil(bm, Vector((x, R0.y, R0.z)), 0.035, 0.07, Vector((1, 0, 0)), lados=16)
    obj('braco_bandeja', bm, 'amarelo', braco)
bandeja = bpy.data.objects.new('bandeja', None)
sc.collection.objects.link(bandeja)
bandeja.parent = carreg
bm = bmesh.new()
caixa_de(bm, (-1.2, -0.077, -0.077), (-0.53, 0.077, -0.065))
for s in (-1, 1):
    caixa_de(bm, (-1.2, s * 0.071 - 0.006, -0.077), (-0.53, s * 0.071 + 0.006, -0.02))
obj('bandeja_calha', bm, 'aco', bandeja)
bm = bmesh.new()
for x in XB:
    caixa_de(bm, (x - 0.05, -0.05, -0.105), (x + 0.05, 0.05, -0.077))
caixa_de(bm, (-1.42, -0.1, -0.12), (-1.2, 0.1, 0.07))                        # caixa da corrente
obj('bandeja_suporte', bm, 'grafite', bandeja)
bm = bmesh.new()
cil(bm, Vector((-1.31, 0.11, -0.03)), 0.075, 0.025, Vector((0, 1, 0)), lados=28)
cil(bm, Vector((-1.31, -0.13, -0.03)), 0.055, 0.07, Vector((0, 1, 0)), lados=24)
obj('soquete_motor', bm, 'amarelo', bandeja)
bm = bmesh.new()
caixa_de(bm, (-1.201, -0.035, -0.06), (-1.198, 0.035, 0.04))
obj('soquete_fenda', bm, 'escuro', bandeja)
bm = bmesh.new()
caixa_de(bm, (-1.4, 0.1, 0.0), (-1.22, 0.102, 0.05))
obj('bandeja_listras', bm, 'listras', bandeja)
bm = bmesh.new()
for k in range(4):
    caixa_de(bm, (-1.15 + k * 0.15, -0.065, -0.0651), (-1.08 + k * 0.15, 0.065, -0.0648))
obj('bandeja_gasto', bm, 'chamusco', bandeja)
for x in (-1.39, -1.23):
    for z in (-0.1, 0.05):
        cil(B('parafusos', 'aco', False, 'bandeja'), Vector((x, 0.1035, z)), 0.009, 0.01, Vector((0, 1, 0)), lados=6)
pts = bezier(Vector((-1.31, -0.165, -0.03)), Vector((-1.31, -0.25, -0.03)), Vector((-1.1, -0.2, -0.2)), Vector((-0.95, -0.06, -0.11)), 10)
mangueira(B('cabos', 'cabo', True, 'bandeja'), pts, 0.01)
soquete = bpy.data.objects.new('soquete', None)
sc.collection.objects.link(soquete)
soquete.parent = bandeja
bm = bmesh.new()
cil(bm, Vector((-0.012, 0, 0)), 0.05, 0.024, Vector((1, 0, 0)), lados=24)
caixa_de(bm, (-0.05, -0.04, -0.064), (0.0, 0.04, -0.03))
obj('soquete_cabeca', bm, 'ferro', soquete)
bm = bmesh.new()
cil(bm, Vector((0.002, 0, 0)), 0.04, 0.006, Vector((1, 0, 0)), lados=24)
obj('soquete_pad', bm, 'borracha', soquete)
elos = []
for k in range(22):
    bm = bmesh.new()
    caixa_de(bm, (-0.022, -0.028, -0.045), (0.022, 0.028, -0.015))
    cil(bm, Vector((0.022, 0, -0.03)), 0.008, 0.07, Vector((0, 1, 0)), lados=8)
    elos.append(obj('elo', bm, 'ferro' if k % 2 else 'aco', bandeja))
# munição na bandeja (granada na frente, estojo de carga atrás)
gr_band = granada('granada_bandeja', bandeja)
es_band = estojo('carga_bandeja', 'boca_fria', False, 'latao_gasto', bandeja)
X_GR, X_ES, X_SOQ = -0.884, -1.165 + CX3, -1.17
STROKE = 0.83

# ------------------------------------------------------------------ sujeira no chão: estojos velhos, queimado, pó
def livre(x, y):
    if math.hypot(x, y) < 0.95:
        return False
    if PX0 - 0.05 < x < PX1 + 0.05 and y < PY1 + 0.05:
        return False
    if -0.6 < x < 0.85 and y > 1.0:
        return False
    for n, t in PATOLAS:
        p = Vector((x, y, 0))
        if 0.7 < p.dot(n) < 2.1 and abs(p.dot(t)) < 0.32:
            return False
    return abs(x) < 1.44 and abs(y) < 1.44


n = 0
while n < 7:
    x, y = random.uniform(-1.4, 1.4), random.uniform(-1.4, 1.4)
    if not livre(x, y):
        continue
    o = estojo('estojo_chao', 'boca_fria', True, 'latao_gasto' if n % 3 else 'aco_capsula')
    o.location = (x, y, Z0 + R_CAP)
    o.rotation_euler = (random.uniform(0, 2 * PI), 0, random.uniform(0, 2 * PI))
    n += 1
for k in range(4):                                                           # alguns fora da laje
    a = random.uniform(-PI, PI)
    r = random.uniform(1.75, 2.6)
    x, y = math.cos(a) * r, math.sin(a) * r
    if abs(x) < 1.52 and abs(y) < 1.52:
        continue
    o = estojo('estojo_chao', 'boca_fria', True, 'aco_capsula')
    o.location = (x, y, R_CAP)
    o.rotation_euler = (random.uniform(0, 2 * PI), 0, random.uniform(0, 2 * PI))
for k in range(16):
    x, y = random.uniform(-1.45, 1.45), random.uniform(-1.45, 1.45)
    if livre(x, y):
        mancha(B('fuligem_chao', 'fuligem_chao'), (x, y), random.uniform(0.05, 0.12), Z0 + 0.001)
for k in range(18):
    x, y = random.uniform(-1.45, 1.45), random.uniform(-1.45, 1.45)
    if livre(x, y):
        mancha(B('po', 'po'), (x, y), random.uniform(0.08, 0.2), Z0 + 0.0008)
for k in range(0):                                                           # (manchas de fora: tiradas, pareciam recorte)
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.7, 4.0)
    mancha(B('fuligem_fora', 'fuligem_chao'), (math.cos(a) * r, math.sin(a) * r), random.uniform(0.03, 0.08), 0.0008 + k * 0.00001)

# ------------------------------------------------------------------ objetos estáticos
PAIS = {'base': None, 'giro': giro, 'canhao': canhao, 'cano': cano, 'carreg': carreg, 'bandeja': bandeja}
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(nome if g == 'base' else g + '_' + nome, bm, mat, PAIS[g])
    if liso:
        suavizar(o)


# ------------------------------------------------------------------ efeitos (objetos)
def bola(nome, mat, sub=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    return obj(nome, bm, mat)


bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
clarao = obj('clarao', bm, 'clarao')
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=1.0, radius2=0.0, depth=1.0,
                      matrix=Matrix.Translation((0.5, 0, 0)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
cone = obj('clarao_cone', bm, 'clarao')
bolas_fogo = [bola('bola_fogo', 'fogo_nucleo' if k < 2 else 'fogo', 3) for k in range(8)]
FOGO_OFF = [(0.2 + 0.24 * k, Vector((0, random.uniform(-0.35, 0.35), random.uniform(-0.25, 0.3))) * (0 if k < 2 else 1), random.uniform(0.85, 1.2))
            for k in range(8)]
jatos = []
for s in (-1, 1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    jatos.append((obj('jato_freio', bm, 'fogo_nucleo'), s))
fumacas = [bola('fumaca_tiro', 'fumaca') for _ in range(10)]
VEL_FUM = [Vector((random.uniform(0.2, 1.4), random.uniform(-0.5, 0.5), random.uniform(-0.2, 0.3))) for _ in fumacas]
fum_culatra = [bola('fumaca_culatra', 'fumaca_clara') for _ in range(4)]
ONDA = []                                                                   # anéis de poeira da onda de choque
for k in range(26):
    ONDA.append((bola('onda_poeira', 'poeira'), None, k * 2 * PI / 26 + random.uniform(-0.08, 0.08), random.uniform(0.9, 1.1),
                 random.uniform(0.8, 1.25), 0))
for k in range(16):
    ONDA.append((bola('onda_base', 'poeira'), None, k * 2 * PI / 16 + random.uniform(-0.1, 0.1), random.uniform(0.92, 1.08),
                 random.uniform(0.8, 1.2), 1))
poeiras = [bola('poeira', 'poeira') for _ in range(16)]
faiscas = [bola('faisca', 'faisca', 0) for _ in range(20)]
VEL_F = [Vector((random.uniform(4, 9), random.uniform(-2.5, 2.5), random.uniform(-1.5, 2.5))) for _ in faiscas]
pedrinhas = []
for k in range(26):
    bm = bmesh.new()
    pedra(bm, Vector((0, 0, 0)), random.uniform(0.012, 0.03))
    pedrinhas.append(obj('pedrinha', bm, 'concreto' if k % 2 else 'lama'))
for o in bolas_fogo + [j for j, _ in jatos] + [clarao, cone]:
    o.visible_shadow = False
luz_b = bpy.data.lights.new('Clarão', 'POINT')
luz_b.color = (1.0, 0.62, 0.3)
luz_b.shadow_soft_size = 0.4
lb = bpy.data.objects.new('Clarão', luz_b)
sc.collection.objects.link(lb)
# granada nova chegando no paiol do chão (vista pela boca)
gr_chao = granada('granada_entrando')
gr_chao.rotation_euler = (0, 0, 0)

# estojo ejetado (este laço) e o do laço anterior parado no chão; fiapos
mq = emissivo('Boca quente', (1.0, 0.32, 0.05), 0.0, (0.03, 0.025, 0.022))
base3d.M['quente'] = mq
quente_in = mq.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
ejetado = estojo('estojo_ejetado', 'quente', True, 'latao_gasto')
anterior = estojo('estojo_laco_anterior', 'boca_fria', True, 'latao_gasto')
N_RASTRO, N_FINAL = 9, 3
fiapos = [bola('fiapo', 'fiapo') for _ in range(N_RASTRO + N_FINAL)]


# ------------------------------------------------------------------ animação: poses
def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def pose(q):
    """(yaw, pitch): carrega a 4°; 22→46 gira e eleva a 55°; segura; 74→92 abaixa; 90→(8 do laço seguinte) volta o giro."""
    if q <= 8:
        return Y_FIRE + (Y_LOAD - Y_FIRE) * suave((q + QUADROS - 90) / 14), P_LOAD
    if q <= 22:
        return Y_LOAD, P_LOAD
    if q <= 46:
        t = suave((q - 22) / 24)
        return Y_LOAD + (Y_FIRE - Y_LOAD) * suave((q - 22) / 20), P_LOAD + (P_FIRE - P_LOAD) * t
    yaw = Y_FIRE if q <= 90 else Y_FIRE + (Y_LOAD - Y_FIRE) * suave((q - 90) / 14)
    pitch = P_FIRE if q <= 74 else P_FIRE + (P_LOAD - P_FIRE) * suave((q - 74) / 18)
    return yaw, pitch


def M_canhao(yaw, pitch, rec=0.0):
    return (Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((TX, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y')
            @ Matrix.Translation((-rec, 0, 0)))


def recuo(q):
    dt = q - T_FIRE
    if dt < 0 or dt > 14:
        return 0.0
    if dt <= 2:
        return REC * (0.45, 0.85, 1.0)[dt]
    return REC * (1 - suave((dt - 2) / 12))


def cunha_aberta(q):
    if q <= 17:
        return 1.0
    if q <= 20:
        return 1 - suave((q - 17) / 3)
    if q <= 63:
        return 0.0
    if q <= 66:
        return suave((q - 63) / 3)
    return 1.0


def bandeja_em_linha(q):
    if q <= 6:
        return suave((q - 1) / 5)
    if q <= 20:
        return 1.0
    if q <= 27:
        return 1 - suave((q - 20) / 7)
    return 0.0


def soquete_curso(q):
    if q < 6:
        return 0.0
    if q <= 14:
        return suave((q - 6) / 8)
    if q <= 15:
        return 1.0
    if q <= 21:
        return 1 - suave((q - 15) / 6)
    return 0.0


def municao(q):
    """(visível, avanço no soquete, subida do paiol)"""
    if q <= 18:
        return True, STROKE * (suave((q - 6) / 8) if q >= 6 else 0.0), 0.0
    if q < 28:
        return False, 0.0, -0.5
    return True, 0.0, -0.5 * (1 - suave((q - 28) / 14))


# ------------------------------------------------------------------ estojo ejetado: extrai, cai na calha, rola, salta
T_EXT, T_QUEDA, T_ROLA, T_LABIO = 66, 69, 72, 90
X_CH = (CH_X0 + CH_X1) / 2
V0_CH, A_CH = 1.23, 0.49


def chao_h(x, y):
    if PX0 < x < PX1 and PY0 < y < PY1:
        return PZ1 + 0.012
    if -0.55 < x < 0.8 and YT - 0.15 < y < YT + 0.15:
        return 0.43
    p = Vector((x, y, 0))
    for n, t in PATOLAS:
        r, tt = p.dot(n), abs(p.dot(t))
        if 0.8 < r < 1.42 and tt < 0.1:
            return 0.36
        if 1.42 < r < 1.7 and tt < 0.075:
            return 0.34
        if 1.7 < r < 1.94 and tt < 0.13:
            return 0.40
    if max(abs(x), abs(y)) * 1.0 < 0.9 and math.hypot(x, y) < AP_SAP:
        return Z_FL
    if abs(x) < 1.48 and abs(y) < 1.48:
        return Z0
    return 0.0


def trajetoria_estojo(semente):
    """Por quadro desde T_EXT: (posição, euler, no_ar). Fases roteirizadas no giro até o lábio da calha, depois física."""
    rnd = random.Random(semente)
    Mg = Matrix.Rotation(Y_FIRE, 4, 'Z')
    Mc = M_canhao(Y_FIRE, P_FIRE)
    quadros = []
    x0 = -0.335 + CX3
    for e in range(T_QUEDA - T_EXT + 1):                                     # extração ao longo do cano
        u = e / (T_QUEDA - T_EXT)
        quadros.append((Mc @ Vector((x0 - 0.52 * u, 0, 0)), (0.0, -P_FIRE, Y_FIRE), True))
    pA = Matrix.Translation((TX, 0, TZ)) @ Matrix.Rotation(-P_FIRE, 4, 'Y') @ Vector((x0 - 0.52, 0, 0))
    pB = Vector((X_CH, -0.04, z_calha(-0.04) + R_CAP))
    for e in range(1, T_ROLA - T_QUEDA + 1):                                 # cai na calha e deita
        u = e / (T_ROLA - T_QUEDA)
        p = pA.lerp(pB, u) + Vector((0, 0, 0.06 * math.sin(PI * u)))
        quadros.append((Mg @ p, (0.6 * u, -P_FIRE * (1 - suave(u)), Y_FIRE), True))
    phi = 0.6
    yb = -0.04
    for e in range(1, T_LABIO - T_ROLA + 1):                                 # rola calha abaixo
        t = e / FPS
        y = -0.04 - (V0_CH * t + 0.5 * A_CH * t * t)
        phi = 0.6 + (-0.04 - y) / R_CAP
        p = Vector((X_CH, y, z_calha(y) + R_CAP))
        quadros.append((Mg @ p, (phi, 0.0, Y_FIRE), False))
    tL = (T_LABIO - T_ROLA) / FPS
    vy = V0_CH + A_CH * tL
    print('ESTOJO lábio y %.3f (calha até %.2f) v %.2f' % (y, CH_Y0, vy))
    p = Mg @ Vector((X_CH, y, z_calha(y) + R_CAP))
    v = Mg.to_3x3() @ Vector((rnd.uniform(-0.1, 0.1), -vy, -0.1))
    psi, th = Y_FIRE, 0.0
    w_psi, w_th = rnd.uniform(-4, 4), rnd.uniform(5, 9)
    passo = 1 / 240
    no_chao, quiques, parou = False, 0, None
    t = 0.0
    for e in range(1, QUADROS + 1 - (T_LABIO - T_EXT)):
        while t < e / FPS - 1e-9:
            t += passo
            if not no_chao:
                v.z -= 9.81 * passo
                p += v * passo
                th += w_th * passo
                psi += w_psi * passo
                h = chao_h(p.x, p.y)
                if p.z - R_CAP <= h:
                    p.z = h + R_CAP
                    if v.z < -0.6 and quiques < 3:
                        v.z = -v.z * 0.34
                        v.x *= 0.55
                        v.y *= 0.55
                        w_th *= 0.4
                        w_psi *= 0.5
                        quiques += 1
                    else:
                        v.z = 0.0
                        no_chao = True
                if quiques:
                    alvo = round(th / PI) * PI
                    th += (alvo - th) * min(1.0, 5 * passo)
            else:
                h = chao_h(p.x, p.y)
                if p.z - R_CAP > h + 0.02:                                   # rolou para fora de um degrau
                    no_chao = False
                    continue
                p.z = h + R_CAP
                a = Vector((math.cos(psi), math.sin(psi), 0))
                vh = Vector((v.x, v.y, 0))
                ao_longo = vh.dot(a)
                vh = vh - a * ao_longo * (1 - math.exp(-10 * passo))
                s = vh.length
                if s > 0:
                    vh *= max(0.0, s - 2.2 * passo) / s
                v = Vector((vh.x, vh.y, 0))
                nrm = Vector((-a.y, a.x, 0))
                phi -= v.dot(nrm) / R_CAP * passo
                p += v * passo
                alvo = round(th / PI) * PI
                th += (alvo - th) * min(1.0, 14 * passo)
                w_psi *= math.exp(-8 * passo)
                psi += w_psi * passo
                if v.length < 0.01 and parou is None:
                    parou = e + (T_LABIO - T_EXT)
        quadros.append((p.copy(), (phi, -th, psi), not no_chao))
    return quadros, parou if parou is not None else len(quadros) - 1


TRAJ, PAROU = trajetoria_estojo(7)
print('ESTOJO parou em', T_EXT + PAROU, 'pos', tuple(round(c, 3) for c in TRAJ[PAROU][0]),
      'z', [round(TRAJ[e][0].z, 2) for e in range(0, min(len(TRAJ), 40), 2)])


def boca_mundo(pos, eul):
    return pos + Euler(eul, 'XYZ').to_matrix() @ Vector((0.279 - CX3, 0, 0))


# ------------------------------------------------------------------ animação: quadro a quadro
M_FIRE = M_canhao(Y_FIRE, P_FIRE)
P_MUZ = M_FIRE @ MUZ
D_MUZ = (M_FIRE.to_3x3() @ Vector((1, 0, 0))).normalized()
L_MUZ = (M_FIRE.to_3x3() @ Vector((0, 1, 0))).normalized()
CHAO_MUZ = Vector((P_MUZ.x + D_MUZ.x * 0.6, P_MUZ.y + D_MUZ.y * 0.6, 0.0))
print('BOCA no tiro', tuple(round(c, 2) for c in P_MUZ), 'chão da onda', tuple(round(c, 2) for c in CHAO_MUZ))
brasa_in = base3d.M['brasa_freio'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
olho_in = base3d.M['olho'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
POEIRA_ORIG = []
for k in range(16):
    if k < 10:
        a = random.uniform(-PI, PI)
        r = random.uniform(0.6, 2.4)
        POEIRA_ORIG.append((CHAO_MUZ + Vector((math.cos(a) * r, math.sin(a) * r, 0)), T_FIRE + int(r * 1.1), r))
    else:
        n_, t_ = PATOLAS[k % 4]
        c = n_ * (1.81 + 0.15) + Vector((0, 0, 0))
        POEIRA_ORIG.append((c, T_FIRE + 2 + (k % 3), 0.0))
PED = [(random.uniform(0, 2 * PI), random.uniform(2.0, 4.5), random.uniform(1.5, 3.5), random.uniform(0.3, 1.6)) for _ in pedrinhas]


def chave(o, campos, q):
    for c in campos:
        o.keyframe_insert(c, frame=q)


def mostra(o, vis, q):
    o.hide_render = o.hide_viewport = not vis
    chave(o, ('hide_render', 'hide_viewport'), q)


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    yaw, pitch = pose(q)
    rec = recuo(q)
    dt = q - T_FIRE
    giro.rotation_euler = (0, 0, yaw)
    chave(giro, ('rotation_euler',), q)
    canhao.rotation_euler = (0, -pitch, 0)
    chave(canhao, ('rotation_euler',), q)
    cano.location = (-rec, 0, 0)
    chave(cano, ('location',), q)
    for p in pinhoes:
        p.rotation_euler = (0, 0, -yaw * R_COROA / R_PINHAO)
        chave(p, ('rotation_euler',), q)
    cunha.location = (0, 0, -0.24 * cunha_aberta(q))
    chave(cunha, ('location',), q)
    # cilindros de elevação
    for p, est, s in elevs:
        d = B_el_giro(pitch, s) - Vector((A_EL.x, s * YE, A_EL.z))
        p.rotation_quaternion = mtx_cil(d).to_quaternion()
        chave(p, ('rotation_quaternion',), q)
        e = (d.length - L0 - EYE) / 3
        for k, st in enumerate(est):
            st.location = (0, 0, (L0 - LS + e) if k == 0 else e)
            chave(st, ('location',), q)
    # carregador
    S = bandeja_em_linha(q)
    alpha = -PI / 2 * (1 - S)
    braco.rotation_euler = (alpha, 0, 0)
    chave(braco, ('rotation_euler',), q)
    bandeja.location = PIV + Matrix.Rotation(alpha, 3, 'X') @ R0 + Vector((0, 0, 0.10))
    chave(bandeja, ('location',), q)
    sq = soquete_curso(q)
    xs = X_SOQ + STROKE * sq
    soquete.location = (xs, 0, 0)
    chave(soquete, ('location',), q)
    for k, el in enumerate(elos):
        xe = xs - 0.035 - k * 0.046
        el.location = (xe, 0, 0)
        chave(el, ('location',), q)
        mostra(el, xe > -1.2, q)
    vis, av, sobe = municao(q)
    gr_band.location = (X_GR + av, 0, sobe)
    es_band.location = (X_ES + av, 0, sobe)
    for o in (gr_band, es_band):
        chave(o, ('location',), q)
        for ob in [o] + list(o.children):
            mostra(ob, vis, q)
    # granada entrando no paiol do chão
    u = (fr * 2) % 1.0
    gr_chao.location = (-0.19, -1.42 + 0.27 * u, 0.165 + 0.018 + 0.052)
    chave(gr_chao, ('location',), q)
    # telêmetro, radar, olho, antena
    tel.rotation_euler = (0, 0, math.radians(6) * math.sin(2 * PI * fr * 2))
    chave(tel, ('rotation_euler',), q)
    tilt.rotation_euler = (0, -pitch * 0.25, 0)
    chave(tilt, ('rotation_euler',), q)
    radar.rotation_euler = (0, 0, 2 * PI * 3 * fr)
    chave(radar, ('rotation_euler',), q)
    olho_in.default_value = 10.0 + 4.0 * math.sin(2 * PI * fr * 4) + (12.0 if dt in (-2, -1) else 0.0)
    olho_in.keyframe_insert('default_value', frame=q)
    mostra(antena_led, (q // 6) % 2 == 0, q)
    # freio quente
    brasa_in.default_value = 0.0 if dt < 0 else 14.0 * max(0.0, 1 - dt / 36) ** 1.3
    brasa_in.keyframe_insert('default_value', frame=q)
    # clarão, cone, bola de fogo, jatos laterais, luz
    fl = {0: 1.0, 1: 0.85, 2: 0.6}.get(dt, 0.0)
    clarao.location = P_MUZ + D_MUZ * 0.15
    clarao.scale = [max(0.01, 0.2 * fl)] * 3
    mostra(clarao, fl > 0.3, q)
    cone.location = P_MUZ
    cone.rotation_mode = 'QUATERNION'
    cone.rotation_quaternion = D_MUZ.to_track_quat('X', 'Z')
    cone.scale = (max(0.01, 2.2 * fl), max(0.01, 0.5 * fl), max(0.01, 0.5 * fl))
    mostra(cone, False, q)
    chave(clarao, ('location', 'scale'), q)
    chave(cone, ('location', 'rotation_quaternion', 'scale'), q)
    bf = {0: (0.8, 1.0, 1.0), 1: (1.0, 1.0, 0.95), 2: (1.15, 0.95, 0.8), 3: (1.25, 0.8, 0.3), 4: (1.3, 0.6, 0.06)}.get(dt)
    Mq = M_FIRE.to_3x3()
    for k, o in enumerate(bolas_fogo):
        dk, lat, sk = FOGO_OFF[k]
        if bf and (k <= 3 + 2 * dt):
            o.location = P_MUZ + D_MUZ * dk * (0.7 + 0.35 * bf[0]) + Mq @ lat * bf[0] + Vector((0, 0, 0.06 * dt))
            r = (0.3 + 0.07 * k) * sk * bf[0] * (1.15 if k < 2 else 1.0)
            o.scale = (r * 1.2, r, r)
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = D_MUZ.to_track_quat('X', 'Z') @ Quaternion((1, 0, 0), k * 1.3 + dt * 0.4)
            o.color = (bf[1], bf[2] * (1.0 - 0.06 * k), 0, 1)
            vis = True
        else:
            o.location, o.scale, o.color = P_MUZ, (0.05, 0.05, 0.05), (0, 0, 0, 1)
            vis = False
        mostra(o, vis, q)
        chave(o, ('location', 'scale', 'color', 'rotation_quaternion'), q)
    for o, s in jatos:
        jf = {0: (0.8, 1.0, 1.0), 1: (1.0, 1.0, 0.75), 2: (1.15, 0.8, 0.35), 3: (1.2, 0.6, 0.08)}.get(dt)
        if jf:
            o.location = P_MUZ - D_MUZ * 0.18 + L_MUZ * s * (0.3 + 0.65 * jf[0])
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = (L_MUZ * s).to_track_quat('X', 'Z')
            o.scale = (0.8 * jf[0], 0.2 * jf[0], 0.26 * jf[0])
            o.color = (jf[1], jf[2], 0, 1)
        else:
            o.location, o.scale, o.color = P_MUZ, (0.05, 0.05, 0.05), (0, 0, 0, 1)
        mostra(o, jf is not None, q)
        chave(o, ('location', 'scale', 'color', 'rotation_quaternion'), q)
    lb.location = P_MUZ + D_MUZ * 0.3
    luz_b.energy = {0: 6000.0, 1: 4500.0, 2: 3000.0, 3: 600.0}.get(dt, 0.0)
    chave(lb, ('location',), q)
    luz_b.keyframe_insert('energy', frame=q)
    # faíscas
    for k, o in enumerate(faiscas):
        viva = 0 <= dt <= 7
        if viva:
            tt = dt / FPS + (k % 3) * 0.01
            v = M_FIRE.to_3x3() @ VEL_F[k]
            p = P_MUZ + v * tt + Vector((0, 0, -4.9 * tt * tt))
            o.location = p
            viva = p.z > 0.05
        else:
            o.location = P_MUZ
        o.scale = [0.012 * max(0.05, 1 - max(dt, 0) / 8) if viva else 0.001] * 3
        chave(o, ('location', 'scale'), q)
        mostra(o, viva, q)
    # fumaça do tiro: nuvens saem da boca, crescem, sobem e diluem
    for k, o in enumerate(fumacas):
        nasce = T_FIRE + (k % 5)
        e = q - nasce
        vida = 38
        if 0 <= e <= vida:
            u = e / vida
            frente = 0.4 + 0.25 * k + (0.6 if k >= 5 else 0.0)
            base_p = P_MUZ + D_MUZ * frente * (0.35 + 0.65 * (1 - math.exp(-4 * u))) + (L_MUZ * (k % 3 - 1) * 0.35 if k >= 5 else Vector())
            o.location = base_p + Vector((0.5 * u, 0.25 * u * ((k % 2) * 2 - 1), 0.9 * u))
            rr = 0.3 + 0.9 * (1 - math.exp(-3 * u)) + 0.3 * u
            o.scale = (rr * 1.1, rr, rr * 0.9)
            d = (0.9 if k < 5 else 0.6) * (1 - u) ** 1.4 * min(1.0, e / 2 + 0.4)
            o.color = (d, 0, 0, 1)
            o.rotation_euler = (k, u * 1.5, k * 0.7)
        else:
            o.location, o.scale, o.color = P_MUZ, (0.05, 0.05, 0.05), (0, 0, 0, 1)
        mostra(o, 0 <= e <= vida, q)
        chave(o, ('location', 'scale', 'color', 'rotation_euler'), q)
    # onda de choque: anel de poeira que corre pelo chão a partir do sopro da boca, e outro em volta da base
    for o, _, a, fr_r, fr_s, qual in ONDA:
        c0, t0, r0, r1, dur, dmax = ((CHAO_MUZ, T_FIRE, 0.6, 5.0, 16, 0.9), (Vector((0, 0, 0)), T_FIRE, 1.6, 3.6, 14, 0.75))[qual]
        e = q - t0
        if 0 <= e <= dur:
            u = e / dur
            R = (r0 + (r1 - r0) * (1 - (1 - u) ** 3)) * fr_r
            o.location = c0 + Vector((math.cos(a) * R, math.sin(a) * R, 0.06 + 0.3 * u))
            rr = (0.16 + 0.42 * u) * fr_s * (1.0 if qual == 0 else 0.8)
            o.scale = (rr * 1.5, rr * 1.5, rr * (0.7 + 0.5 * u))
            o.rotation_euler = (0, 0, a)
            o.color = (dmax * (1 - u) ** 1.1 * min(1.0, 0.6 + 0.4 * e), 0, 0, 1)
        else:
            o.location, o.scale, o.color = c0, (0.05, 0.05, 0.05), (0, 0, 0, 1)
        mostra(o, 0 <= e <= dur, q)
        chave(o, ('location', 'scale', 'color', 'rotation_euler'), q)
    # poeira subindo do chão
    for k, o in enumerate(poeiras):
        c0, nasce, r = POEIRA_ORIG[k]
        e = q - nasce
        vida = 34
        if 0 <= e <= vida:
            u = e / vida
            dirr = (c0 - CHAO_MUZ).normalized() if r > 0 else Vector((c0.x, c0.y, 0)).normalized()
            o.location = c0 + dirr * 0.5 * (1 - math.exp(-3 * u)) + Vector((0.15 * u, 0, 0.12 + 0.9 * u))
            rr = 0.18 + 0.55 * (1 - math.exp(-3 * u))
            o.scale = (rr * 1.3, rr * 1.3, rr)
            o.color = ((0.8 if r > 0 else 0.6) * math.sin(PI * min(1.0, u * 1.4 + 0.15)) * (1 - u), 0, 0, 1)
            o.rotation_euler = (k, u, k * 0.3)
        else:
            o.location, o.scale, o.color = c0, (0.05, 0.05, 0.05), (0, 0, 0, 1)
        mostra(o, 0 <= e <= vida, q)
        chave(o, ('location', 'scale', 'color', 'rotation_euler'), q)
    # pedrinhas chutadas pela onda
    for k, o in enumerate(pedrinhas):
        a, r, vz, vr = PED[k]
        nasce = T_FIRE + int(r * 1.2)
        e = q - nasce
        if 0 <= e <= 16:
            tt = e / FPS
            c0 = CHAO_MUZ + Vector((math.cos(a) * r, math.sin(a) * r, 0))
            z = 0.02 + vz * tt - 4.9 * tt * tt
            o.location = c0 + Vector((math.cos(a), math.sin(a), 0)) * vr * tt + Vector((0, 0, max(0.02, z)))
            o.rotation_euler = (e * 0.6, e * 0.4, k)
            viva = z > 0.0
        else:
            o.location = CHAO_MUZ
            viva = False
        mostra(o, viva, q)
        chave(o, ('location', 'rotation_euler'), q)
    # fumaça clara da culatra quando a cunha abre
    for k, o in enumerate(fum_culatra):
        nasce = 65 + k * 3
        e = q - nasce
        vida = 22
        if 0 <= e <= vida:
            u = e / vida
            p0 = M_canhao(*pose(nasce)) @ Vector((-0.45, 0.0, 0.0))
            o.location = p0 + Vector((-0.1 * u, 0.05 * u, 0.55 * u))
            rr = 0.05 + 0.16 * u
            o.scale = (rr, rr, rr * 1.4)
            o.color = (0.6 * (1 - u) ** 1.3, 0, 0, 1)
            o.rotation_euler = (k, u * 2, 0)
        else:
            o.location, o.scale, o.color = (0, 0, 2), (0.05, 0.05, 0.05), (0, 0, 0, 1)
        mostra(o, 0 <= e <= vida, q)
        chave(o, ('location', 'scale', 'color', 'rotation_euler'), q)
    # estojo ejetado e o do laço anterior
    e = q - T_EXT
    pos_a, eul_a, _ = TRAJ[min(e + QUADROS, PAROU)]
    anterior.location, anterior.rotation_euler = pos_a, eul_a
    chave(anterior, ('location', 'rotation_euler'), q)
    if e >= 0:
        pos, eul, _ = TRAJ[min(e, len(TRAJ) - 1)]
        ejetado.location, ejetado.rotation_euler = pos, eul
    else:
        ejetado.location, ejetado.rotation_euler = (0, 0, -1), (0, 0, 0)
    for ob in [ejetado] + list(ejetado.children):
        mostra(ob, e >= 0, q)
    chave(ejetado, ('location', 'rotation_euler'), q)
    quente_in.default_value = 0.0 if e < 0 else 10.0 * max(0.0, 1 - e / 28) ** 1.5
    quente_in.keyframe_insert('default_value', frame=q)
    for j, f in enumerate(fiapos):
        vida, nasce = (12, 2 + j * 2) if j < N_RASTRO else (26, PAROU + (j - N_RASTRO) * 6)
        u = None
        for qq in (q, q + QUADROS):
            ee = qq - T_EXT - nasce
            if 0 <= ee <= vida and nasce < len(TRAJ):
                u = ee / vida
                break
        if u is None:
            f.location, f.scale, f.color = (0, 0, -1), (0.02, 0.02, 0.02), (0, 0, 0, 1)
            mostra(f, False, q)
        else:
            pb, eb, _ = TRAJ[min(nasce, len(TRAJ) - 1)]
            p0 = boca_mundo(pb, eb)
            if j < N_RASTRO:
                f.location = p0 + Vector((0.03 * u, -0.02 * u, 0.15 * u))
                f.scale = (0.04 + 0.08 * u, 0.04 + 0.08 * u, 0.05 + 0.11 * u)
                d = 0.55 * (1 - u) ** 1.2
            else:
                f.location = p0 + Vector((0.03 * u, 0.02 * u, 0.03 + 0.35 * u))
                f.scale = (0.03 + 0.06 * u, 0.03 + 0.06 * u, 0.05 + 0.13 * u)
                d = 0.45 * math.sin(PI * min(1.0, u * 1.3 + 0.08)) * (1 - u)
            f.color = (d, d, d, 1)
            f.rotation_euler = (j, u * 2, 1)
            mostra(f, True, q)
        chave(f, ('location', 'scale', 'color', 'rotation_euler'), q)

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (30, 30, 1.0))
obj('chao', bm, 'chao')
for k in range(30):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.8, 6.0)
    pedra(B('pedras_fora', 'concreto'), Vector((math.cos(a) * r, math.sin(a) * r, 0.01)), random.uniform(0.02, 0.06))
bm = BMS.pop(('pedras_fora', 'concreto', False, 'base'))
obj('pedras_fora', bm, 'concreto')
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
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.5
cam_d = bpy.data.cameras.new('Cam')
cam_d.clip_end = 200
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def no_giro(yaw, p):
    return Matrix.Rotation(yaw, 4, 'Z') @ Vector(p)


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
AMOSTRAS = int(args[2]) if len(args) > 2 and modo == 'foto' else 128


def brilho(ligar):
    """Brilho do clarão no compositor (só na foto do disparo)."""
    try:
        if ligar and not bpy.data.node_groups.get('Comp'):
            ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
            ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            rl = ng.nodes.new('CompositorNodeRLayers')
            gl = ng.nodes.new('CompositorNodeGlare')
            gl.inputs['Type'].default_value = 'Bloom'
            gl.inputs['Threshold'].default_value = 2.0
            gl.inputs['Strength'].default_value = 0.6
            gl.inputs['Size'].default_value = 0.8
            out = ng.nodes.new('NodeGroupOutput')
            ng.links.new(rl.outputs['Image'], gl.inputs['Image'])
            ng.links.new(gl.outputs[0], out.inputs[0])
        sc.compositing_node_group = bpy.data.node_groups.get('Comp') if ligar else None
        sc.render.use_compositing = ligar
    except Exception as ex:
        print('BRILHO falhou', ex)


def foto(nome, quadro, pos, alvo, lente, rx=1200, ry=1100, amostras=None):
    brilho(nome == 'artilharia_disparo.png')
    sc.cycles.samples = amostras or AMOSTRAS
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.frame_set(quadro)
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


if modo == 'foto':
    if so_uma in (None, '0'):                                               # cano elevado (antes do tiro)
        foto('artilharia_0.png', 50, no_giro(Y_FIRE, (3.0, 7.3, 2.9)), no_giro(Y_FIRE, (0.6, 0.0, 2.05)), 30)
    if so_uma in (None, 'perto'):                                           # culatra e carregador socando
        foto('artilharia_perto.png', 8, no_giro(Y_LOAD, (-2.7, 0.55, 1.95)), no_giro(Y_LOAD, (-0.55, 0.12, 1.36)), 30, 1300, 1000)
    if so_uma in (None, 'disparo'):
        foto('artilharia_disparo.png', T_FIRE + 2, no_giro(Y_FIRE, (4.6, -8.8, 2.6)), no_giro(Y_FIRE, (1.4, 0.0, 2.4)), 26, 1300, 1100)
    if so_uma in (None, 'capsula'):
        foto('artilharia_capsula.png', 89, no_giro(Y_FIRE, (-0.9, -3.1, 1.35)), no_giro(Y_FIRE, (-0.3, -0.95, 0.72)), 32, 1300, 1000)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    foto('artilharia_teste.png', int(v[7]), v[0:3], v[3:6], v[6], 1000, 800, 32)
print('ARTILHARIA ok')
