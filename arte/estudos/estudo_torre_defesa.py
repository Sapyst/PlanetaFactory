"""Estudo isolado (fora do jogo): TORRE DE DEFESA de energia da IA, 2×2 tiles. Munição de reserva entra pelo sul
(ITEM_ENT_S1, tile da direita). Partes como no jogo: base, giro (gira em Z), canhao (inclina), pistao0, pistao1.
Defende a fábrica das aranhas (o sistema imunológico do planeta) e dos ninhos: puxa 120 kW da rede, guarda 6 MJ e
atira com essa carga (0,05 MJ por tiro, 3 tiros/s, alcance 18 m, dano 8). A munição física é só a reserva.
- Pedestal octogonal blindado e aparafusado (placas grafite com parafusos), sapata com chumbadores, faixas de carga.
- Banco de capacitores (norte) com visores de carga, barramento de cobre, caixa de entrada com isoladores; cabos
  grossos da rede chegando por eletroduto na borda leste; cabos da caixa até o pedestal.
- Coroa dentada no giro e motor de giro com redutor e pinhão (gira de verdade conforme a cabeça vira).
- Cabeça: bochechas blindadas amarelas, caixa traseira com aletas, mancais dos munhões com cabos de força passando
  pela junta rotativa; casulo sensor com olho e varredor laser que varre o chão procurando aranhas.
- Canhão de trilho duplo (railgun): culatra com respiros, porta de ejeção e células; trilhos de aço com face de
  cobre, bobinas de aceleração com anéis de carga, gaiola de tirantes, aletas de dissipação, boca com eletrodos
  enegrecidos. Recua a cada tiro dentro do berço (colar dos pistões).
- Pistões de elevação (camisa presa na base da cabeça, haste no colar do berço) com mangueiras.
- Carregador de reserva: esteira curta da boca sul até o elevador com visor (cápsulas subindo) e duto até o pedestal.
- Sujeira: queimado de disparo, fuligem na boca, cápsulas de armadura no chão, óleo, pó, pintura lascada.
- Efeitos: arco/plasma na boca, clarão, rastro do projétil, faíscas, fumaça que dilui, vapor dos respiros.
Animação (laço de 4 s): a cabeça vira e o canhão eleva; rajada de 4 tiros a 3 tiros/s (clarão, recuo, cápsula
ejetada, carga caindo no banco); depois abaixa e volta varrendo.
Uso: blender -b --python estudo_torre_defesa.py -- foto [0|1|2|3|perto]
     blender -b --python estudo_torre_defesa.py -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(57)

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


def prisma_xz(bm, perfil, y0, y1):
    """Chapa com perfil (x, z) extrudada em y — bochechas blindadas."""
    a = [bm.verts.new((x, y0, z)) for x, z in perfil]
    b = [bm.verts.new((x, y1, z)) for x, z in perfil]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(perfil)
    for k in range(n):
        bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))


BMS = {}


def B(nome, mat, liso=False, g='base'):
    k = (nome, mat, liso, g)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def parafuso(p, n, g='base', r=0.011):
    cil(B('parafusos', 'aco', False, g), Vector(p), r, 0.012, Vector(n), lados=6)


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def plasma_mat():
    """Bola de plasma em volume: absorve pouco, emite forte violeta-branco, some na borda."""
    m = bpy.data.materials.new('Plasma')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.05, 0.02, 0.08, 1)
    vol.inputs['Emission Color'].default_value = (0.75, 0.5, 1.0, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.2})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = 6.0
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    e.inputs[1].default_value = 40.0
    nt.links.new(mul.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def fumaca_grad_mat(nome, dens, z0, z1):
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    no = mats.no
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    next(n for n in nt.nodes if n.type == 'TEX_NOISE').inputs['Scale'].default_value = 5.5
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.015, 0.014, 0.014, 1)
    mix.inputs[7].default_value = (0.42, 0.42, 0.43, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.95, sujeira=0.9, ferrugem=0.35),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.8, sujeira=0.85),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'bobina': mats.material('Bobina', (0.78, 0.4, 0.2), 1.0, 0.25, pintura=False, sujeira=0.6),
    'latao': mats.material('Latão', (0.62, 0.45, 0.16), 1.0, 0.32, pintura=False, sujeira=0.7),
    'queimado': mats.material('Queimado', (0.13, 0.11, 0.12), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'porcelana': mats.material('Porcelana', (0.42, 0.19, 0.09), 0, 0.2, pintura=False, sujeira=0.7, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'isol_verm': mats.material('Isolador vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.5, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'vidro': emissivo('Vidro do visor', (0.05, 0.04, 0.06), 0.0),
    'listras': base3d.listras_mat(),
    'carga': emissivo('Faixa de carga', (0.5, 0.2, 1.0), 2.5),
    'fuligem_chao': mats.material('Fuligem', (0.045, 0.04, 0.036), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'brilho': emissivo('Brilho das bobinas', (0.55, 0.25, 1.0), 2.0),
    'brasa': emissivo('Trilho quente', (1.0, 0.3, 0.04), 0.5, (0.2, 0.08, 0.03)),
    'olho': emissivo('Olho do sensor', VIOLETA, 12.0, (0.05, 0.02, 0.1)),
    'laser': emissivo('Laser', (1.0, 0.06, 0.03), 30.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'arco': emissivo('Arco', (0.75, 0.55, 1.0), 25.0),
    'clarao': emissivo('Clarão', (0.8, 0.6, 1.0), 22.0),
    'rastro': emissivo('Rastro', (0.65, 0.4, 1.0), 25.0),
    'faisca': emissivo('Faísca', (1.0, 0.6, 0.25), 60.0),
    'plasma': plasma_mat(),
    'fumaca': fumaca_grad_mat('Fumaça', 5.0, 1.15, 2.9),
    'vapor': base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 3.0, 1.2, 2.0),
})

def fiapo_mat():
    """Fiapo de fumaça cinza-escuro em volume; a densidade vem da cor do objeto (chave por quadro) para sumir aos poucos."""
    m = bpy.data.materials.new('Fiapo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.06, 0.058, 0.056, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.2, 'Detail': 5.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.3})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    forma = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.65})
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
    m3.inputs[1].default_value = 110.0
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    nt.links.new(m3.outputs['Value'], vol.inputs['Density'])
    return m


base3d.M.update({
    'latao_gasto': mats.material('Latão gasto', (0.58, 0.42, 0.17), 1.0, 0.38, pintura=False, sujeira=0.9, ferrugem=0.25),
    'aco_capsula': mats.material('Aço da cápsula', (0.36, 0.35, 0.34), 1.0, 0.45, pintura=False, sujeira=0.9, ferrugem=0.5),
    'espoleta': mats.material('Espoleta', (0.7, 0.4, 0.25), 1.0, 0.3, pintura=False, sujeira=0.4),
    'celula_apagada': emissivo('Célula de carga gasta', (0.35, 0.12, 0.7), 0.25, (0.12, 0.05, 0.22)),
    'celula_cheia': emissivo('Célula de carga cheia', (0.55, 0.25, 1.0), 2.5, (0.2, 0.08, 0.35)),
    'boca_fria': mats.material('Boca queimada', (0.03, 0.025, 0.022), 0.6, 0.7, pintura=False, sujeira=0.2, desgaste=0.0),
    'fiapo': fiapo_mat(),
})


# ------------------------------------------------------------------ modelo da cápsula (calibre do trilho: Ø 41 mm, 92 mm)
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


CX = 0.046                    # meio da cápsula (origem do objeto)
R_CAP = 0.0205                # raio do aro (fica deitada sobre ele)
PERFIL_CAPSULA = [(0.0, 0.0), (0.0, 0.0205), (0.0055, 0.0205), (0.0065, 0.0165), (0.0105, 0.0165), (0.013, 0.0192),
                  (0.058, 0.0186), (0.068, 0.0146), (0.086, 0.0143), (0.086, 0.0124), (0.03, 0.0124), (0.03, 0.0)]


def capsula(nome, boca_mat, disparada=True, corpo='latao_gasto', celula='celula_apagada'):
    """Cápsula de armadura do trilho: aro e ranhura do extrator, corpo afunilando no gargalo, espoleta no centro do
    fundo, faixa de célula de carga e boca (enegrecida se disparada; com o projétil se cheia)."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    bm = bmesh.new()
    torno(bm, [(x - CX, r) for x, r in PERFIL_CAPSULA])
    suavizar(obj(nome + '_corpo', bm, corpo, e))
    bm = bmesh.new()
    torno(bm, [(0.086 - CX, 0.0143), (0.093 - CX, 0.0141), (0.093 - CX, 0.0124), (0.086 - CX, 0.0124)], fechado=True)
    suavizar(obj(nome + '_boca', bm, boca_mat, e))
    bm = bmesh.new()
    torno(bm, [(0.03 - CX, 0.0185), (0.043 - CX, 0.0185), (0.043 - CX, 0.0191), (0.03 - CX, 0.0191)], 20, fechado=True)
    obj(nome + '_celula', bm, celula, e)
    bm = bmesh.new()
    torno(bm, [(-CX - 0.0006, 0.0), (-CX - 0.0006, 0.0055), (-CX + 0.0002, 0.0055), (-CX + 0.0002, 0.0)], 16)
    obj(nome + '_espoleta', bm, 'espoleta', e)
    if not disparada:
        bm = bmesh.new()
        torno(bm, [(0.06 - CX, 0.0), (0.06 - CX, 0.0122), (0.1 - CX, 0.0122), (0.112 - CX, 0.008), (0.118 - CX, 0.0)], 16)
        suavizar(obj(nome + '_projetil', bm, 'aco', e))
    return e


# ------------------------------------------------------------------ medidas
Z0 = 0.08                 # topo da laje
AP_P, AP_C = 0.62, 0.42   # apótema da sapata e do corpo do pedestal
Z_C1 = 0.58               # topo do corpo
Z_FL = 0.62               # topo do flange
Z_G0, Z_G1 = 0.64, 0.70   # coroa dentada (giro)
Z_MESA = 0.78             # topo da mesa giratória
Z_PL = 0.84               # topo da placa da cabeça
TX, TZ = 0.05, 1.10       # munhão (no referencial do giro)
R_COROA, R_PINHAO = 0.435, 0.05
D_PINHAO = R_COROA + R_PINHAO
DIR_MOTOR = Vector((-1, -1, 0)).normalized()   # motor de giro no sudoeste
YP = 0.19                 # y dos pistões (±)
A_PIS = Vector((0.24, YP, 0.90))               # pino da camisa (giro)
B_PIS = Vector((0.43, YP, -0.10))              # pino da haste (canhão)
L_CAM, L_HAS = 0.22, 0.22
REC = 0.045               # recuo máximo do cano
BX = 0.5                  # boca sul (S1)

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-0.985, s * 0.985 - 0.012, 0.0), (0.985, s * 0.985 + 0.012, Z0 + 0.002))
    caixa_de(bm, (s * 0.985 - 0.012, -0.985, 0.0), (s * 0.985 + 0.012, 0.985, Z0 + 0.002))

# ------------------------------------------------------------------ pedestal
O = Vector((0, 0, 0))
octo(B('sapata', 'ferro'), O, AP_P, Z0, 0.15)
for k in range(16):                                                        # chumbadores
    a = k * 2 * PI / 16 + PI / 16
    p = Vector((math.cos(a), math.sin(a), 0)) * 0.56 + Vector((0, 0, 0.156))
    cil(B('parafusos', 'aco'), p, 0.016, 0.02, lados=6)
    cil(B('arruelas', 'ferro'), p - Vector((0, 0, 0.006)), 0.026, 0.006, lados=12)
octo(B('corpo', 'amarelo'), O, AP_C, 0.15, Z_C1)
for k in range(8):                                                         # nervuras nos vértices
    a = PI / 8 + k * PI / 4
    R8 = AP_C / math.cos(PI / 8)
    caixa(B('nervuras', 'ferro'), Vector((math.cos(a), math.sin(a), 0)) * (R8 + 0.002) + Vector((0, 0, (0.15 + Z_C1) / 2)),
          (0.03, 0.03, Z_C1 - 0.15), Matrix.Rotation(a, 3, 'Z'))
PLACAS = {}
for k in range(8):                                                         # placas blindadas aparafusadas
    a = k * PI / 4
    n = Vector((math.cos(a), math.sin(a), 0))
    R = rot_face(n)
    c = n * (AP_C + 0.009) + Vector((0, 0, 0.37))
    caixa(B('placas', 'grafite'), c, (0.27, 0.018, 0.34), R)
    PLACAS[k] = (n, R)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parafuso(c + R @ Vector((sx * 0.115, 0.01, 0)) + Vector((0, 0, sz * 0.145)), n)
        parafuso(c + R @ Vector((sx * 0.115, 0.01, 0)), n)
octo(B('flange', 'ferro'), O, AP_C + 0.025, Z_C1, Z_FL)
for k in range(24):
    a = k * 2 * PI / 24
    cil(B('parafusos', 'aco'), Vector((math.cos(a), math.sin(a), 0)) * 0.41 + Vector((0, 0, Z_FL + 0.006)), 0.011, 0.012, lados=6)
cil(B('rolamento', 'aco', True), Vector((0, 0, (Z_FL + Z_G0) / 2)), 0.36, Z_G0 - Z_FL, lados=48)

# faixas de carga nas placas leste e oeste (visor vertical)
faixas = []
for k in (0, 4):
    n, R = PLACAS[k]
    f = n * (AP_C + 0.018)
    z0, h = 0.25, 0.24
    zc = z0 + h / 2
    for s in (-1, 1):
        caixa(B('visor_moldura', 'ferro'), f + R @ Vector((s * 0.035, 0.01, 0)) + Vector((0, 0, zc)), (0.014, 0.02, h + 0.04), R)
        caixa(B('visor_moldura', 'ferro'), f + R @ Vector((0, 0.01, 0)) + Vector((0, 0, zc + s * (h / 2 + 0.014))), (0.084, 0.02, 0.014), R)
    caixa(B('visor_fundo', 'escuro'), f + R @ Vector((0, 0.002, 0)) + Vector((0, 0, zc)), (0.056, 0.006, h), R)
    for j in range(1, 6):
        caixa(B('visor_marcas', 'grafite'), f + R @ Vector((0, 0.012, 0)) + Vector((0, 0, z0 + j * h / 6)), (0.056, 0.004, 0.005), R)
    bm = bmesh.new()
    caixa_de(bm, (-0.024, -0.002, 0.0), (0.024, 0.002, h))
    fx = obj('faixa_carga', bm, 'carga')
    fx.location = f + R @ Vector((0, 0.008, 0)) + Vector((0, 0, z0))
    fx.rotation_euler = R.to_euler()
    faixas.append(fx)

# motor de giro (sudoeste): motor vertical, redutor e pinhão engrenado na coroa
CM = DIR_MOTOR * 0.60
CP = DIR_MOTOR * D_PINHAO
RM = rot_face(DIR_MOTOR)
cil(B('motor', 'grafite', True), CM + Vector((0, 0, 0.40)), 0.07, 0.24, lados=24)
for j in range(6):
    cil(B('motor_aletas', 'ferro', True), CM + Vector((0, 0, 0.31 + j * 0.035)), 0.082, 0.008, lados=24)
cil(B('motor_tampa', 'ferro', True), CM + Vector((0, 0, 0.275)), 0.075, 0.016, lados=24)
caixa(B('motor', 'grafite'), CM + RM @ Vector((0.07, 0.02, 0)) + Vector((0, 0, 0.44)), (0.05, 0.06, 0.07), RM)   # caixa de ligação
bm = B('redutor', 'amarelo', True)
caixa(bm, (CM + CP) / 2 + Vector((0, 0, 0.547)), (0.12, (CM - CP).length + 0.12, 0.055), RM)
for c in (CM, CP):
    cil(bm, c + Vector((0, 0, 0.547)), 0.06, 0.055, lados=24)
cil(B('pinhao_eixo', 'aco', True), CP + Vector((0, 0, 0.61)), 0.016, 0.07, lados=12)
for s in (-1, 1):                                                          # mão francesa do motor no corpo
    p0 = DIR_MOTOR * (AP_C + 0.02) + RM @ Vector((s * 0.08, 0, 0))
    caixa(B('suporte_motor', 'ferro'), (p0 + CM + RM @ Vector((s * 0.05, 0, 0))) / 2 + Vector((0, 0, 0.36)),
          (0.02, (CM - p0).length + 0.02, 0.1), RM)
    viga(B('suporte_motor', 'ferro'), p0 + Vector((0, 0, 0.18)), CM + RM @ Vector((s * 0.05, 0, 0)) - DIR_MOTOR * 0.06 + Vector((0, 0, 0.31)), 0.02)
for s in (-1, 1):
    parafuso(DIR_MOTOR * (AP_C + 0.03) + RM @ Vector((s * 0.08, 0.0, 0)) + Vector((0, 0, 0.39)), DIR_MOTOR)
pts = bezier(CM + RM @ Vector((0.1, 0.02, 0)) + Vector((0, 0, 0.44)), CM + RM @ Vector((0.18, 0.02, 0)) + Vector((0, 0, 0.42)),
             CM + RM @ Vector((0.25, -0.08, 0)) + Vector((0, 0, 0.2)), DIR_MOTOR.copy() * 0.0 + PLACAS[6][0] * (AP_C + 0.03) + Vector((-0.05, 0, 0.2)), 10)
mangueira(B('cabos', 'cabo', True), pts, 0.013)
pinhao = bpy.data.objects.new('pinhao', None)
sc.collection.objects.link(pinhao)
pinhao.location = CP + Vector((0, 0, (Z_G0 + Z_G1) / 2))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), R_PINHAO - 0.008, Z_G1 - Z_G0, lados=20)
for k in range(13):
    a = k * 2 * PI / 13
    caixa(bm, Vector((math.cos(a), math.sin(a), 0)) * R_PINHAO, (0.018, 0.014, Z_G1 - Z_G0), Matrix.Rotation(a, 3, 'Z'))
cil(bm, Vector((0, 0, 0.035)), 0.02, 0.012, lados=6)
obj('pinhao_dentes', bm, 'aco', pinhao)
# graxa no pinhão e no rolamento
for k in range(5):
    mancha(B('oleo', 'oleo'), (CP.x + random.uniform(-0.05, 0.05), CP.y + random.uniform(-0.05, 0.05)), random.uniform(0.02, 0.04), Z_FL + 0.0015)
mancha(B('oleo', 'oleo'), (CM.x - 0.05, CM.y - 0.02), 0.08, Z0 + 0.0015)
for k in range(3):
    caixa(B('escorridos', 'oleo'), DIR_MOTOR * (AP_C + 0.0005 + 0.019) + RM @ Vector((random.uniform(-0.1, 0.1), 0, 0)) + Vector((0, 0, 0.45)),
          (random.uniform(0.008, 0.016), 0.002, random.uniform(0.1, 0.2)), RM)

# ------------------------------------------------------------------ banco de capacitores (norte) e entrada da rede
YC = 0.79
CAPS = [Vector((x, YC, 0)) for x in (-0.72, -0.48, -0.24)]
caixa_de(B('rack', 'ferro'), (-0.84, 0.68, Z0), (-0.12, 0.90, 0.11))
for x in (-0.82, -0.6, -0.36, -0.14):
    caixa_de(B('rack', 'ferro'), (x - 0.012, 0.68, 0.11), (x + 0.012, 0.70, 0.3))
    caixa_de(B('rack', 'ferro'), (x - 0.012, 0.88, 0.11), (x + 0.012, 0.90, 0.3))
for y in (0.69, 0.89):
    caixa_de(B('rack_cinta', 'amarelo'), (-0.84, y - 0.012, 0.28), (-0.12, y + 0.012, 0.32))
for x in (-0.82, -0.14):
    for y in (0.7, 0.88):
        parafuso((x, y, 0.116), (0, 0, 1))
for i, C in enumerate(CAPS):
    cil(B('capacitor', 'amarelo', True), C + Vector((0, 0, 0.355)), 0.095, 0.49, lados=32)
    for z in (0.16, 0.42):
        cil(B('capacitor_cinta', 'grafite', True), C + Vector((0, 0, z)), 0.099, 0.03, lados=32)
    cil(B('capacitor_tampa', 'grafite', True), C + Vector((0, 0, 0.62)), 0.1, 0.04, lados=32)
    for s in (-1, 1):                                                      # terminais
        p = C + Vector((s * 0.045, 0, 0))
        cil(B('terminal_colar', 'isol_verm' if s < 0 else 'borracha', True), p + Vector((0, 0, 0.65)), 0.026, 0.02, lados=16)
        cil(B('terminal', 'cobre', True), p + Vector((0, 0, 0.69)), 0.014, 0.07, lados=12)
        cil(B('terminal_porca', 'aco'), p + Vector((0, 0, 0.752)), 0.022, 0.012, lados=6)
    # visor de carga virado para o norte (lado de fora)
    n = Vector((0, 1, 0))
    R = rot_face(n)
    f = C + n * 0.096
    z0, h = 0.19, 0.2
    caixa(B('visor_moldura', 'ferro'), f + Vector((0, 0.006, z0 + h / 2)), (0.06, 0.012, h + 0.03), R)
    caixa(B('visor_fundo', 'escuro'), f + Vector((0, 0.013, z0 + h / 2)), (0.036, 0.004, h), R)
    bm = bmesh.new()
    caixa_de(bm, (-0.013, -0.002, 0.0), (0.013, 0.002, h))
    fx = obj('faixa_carga', bm, 'carga')
    fx.location = f + Vector((0, 0.016, z0))
    faixas.append(fx)
    for k in range(5):                                                     # escorrido do eletrólito/ferrugem
        a = random.uniform(-PI * 0.9, -PI * 0.1)
        nn = Vector((math.cos(a), math.sin(a), 0))
        L = random.uniform(0.08, 0.25)
        caixa(B('escorridos', 'ferrugem' if k % 2 else 'chamusco'), C + nn * 0.0955 + Vector((0, 0, 0.58 - L / 2)),
              (0.012, 0.002, L), rot_face(nn))
# barramento de cobre sobre os terminais + (oeste→leste) e − (outro barramento)
for s, z in ((-1, 0.765), (1, 0.79)):
    xs = [C.x + s * 0.045 for C in CAPS]
    caixa_de(B('barramento', 'cobre'), (xs[0] - 0.02, YC - 0.018, z - 0.006), (xs[-1] + 0.02, YC + 0.018, z + 0.006))
    for x in xs:
        tubo(B('barramento', 'cobre', True), (x, YC, 0.72), (x, YC, z), 0.008, 10)
# caixa de entrada da rede
JB0, JB1 = Vector((0.14, 0.66, Z0)), Vector((0.44, 0.92, 0.62))
caixa_de(B('caixa_entrada', 'grafite'), JB0, JB1)
caixa_de(B('caixa_porta', 'amarelo'), (0.17, 0.92, 0.12), (0.41, 0.935, 0.58))
for x in (0.19, 0.39):
    for z in (0.15, 0.55):
        parafuso((x, 0.94, z), (0, 1, 0))
caixa_de(B('caixa_listras', 'listras'), (0.17, 0.936, 0.46), (0.41, 0.94, 0.52))
for k, m in enumerate(('led_verde', 'led_verde', 'led_ambar')):
    cil(B('led_' + m, m), Vector((0.23 + k * 0.05, 0.937, 0.4)), 0.009, 0.006, Vector((0, 1, 0)), lados=10)
JB_ISO = []
for i, x in enumerate((0.21, 0.29, 0.37)):                                 # isoladores no topo
    base = Vector((x, 0.79, 0.62))
    cil(B('porcelana', 'porcelana', True), base + Vector((0, 0, 0.06)), 0.016, 0.12, lados=14)
    for j in range(4):
        cil(B('porcelana', 'porcelana', True), base + Vector((0, 0, 0.02 + j * 0.028)), 0.036, 0.01, lados=18)
    cil(B('iso_grampo', 'cobre', True), base + Vector((0, 0, 0.135)), 0.016, 0.03, lados=12)
    JB_ISO.append(base + Vector((0, 0, 0.14)))
# barramento → isolador da caixa (cabo flexível)
pts = bezier(Vector((CAPS[-1].x + 0.045 + 0.015, YC, 0.79)), Vector((CAPS[-1].x + 0.2, YC, 0.79)),
             JB_ISO[0] + Vector((-0.1, 0, 0.05)), JB_ISO[0] + Vector((-0.015, 0, 0)), 10)
mangueira(B('cabos', 'cabo', True), pts, 0.02)
pts = bezier(Vector((CAPS[-1].x - 0.045 + 0.015, YC - 0.03, 0.765)), Vector((CAPS[-1].x + 0.1, YC - 0.1, 0.72)),
             JB_ISO[1] + Vector((-0.06, -0.08, 0.04)), JB_ISO[1] + Vector((0, -0.016, 0)), 10)
mangueira(B('cabos', 'cabo', True), pts, 0.02)
# rede: eletroduto na borda leste, três cabos grossos sobem e entram na face leste da caixa
EL = Vector((0.9, 0.78, 0))
cil(B('eletroduto', 'ferro', True), EL + Vector((0, 0, Z0 + 0.05)), 0.07, 0.1, lados=20)
cil(B('eletroduto', 'ferro', True), EL + Vector((0, 0, Z0 + 0.1)), 0.08, 0.012, lados=20)
for k in range(4):
    a = k * PI / 2 + PI / 4
    parafuso(EL + Vector((math.cos(a) * 0.065, math.sin(a) * 0.065, Z0 + 0.11)), (0, 0, 1), r=0.008)
cil(B('prensa_cabo', 'ferro', True), Vector((0.455, 0.79, 0.34)), 0.06, 0.03, Vector((1, 0, 0)), lados=20)
for i in range(3):
    dy = (i - 1) * 0.04
    pts = bezier(EL + Vector((-0.02, dy, Z0 + 0.1)), EL + Vector((-0.02, dy, 0.5)), Vector((0.62, 0.79 + dy, 0.34)),
                 Vector((0.46, 0.79 + dy * 0.6, 0.34)), 14)
    mangueira(B('cabos', 'cabo', True), pts, 0.019)
for t in (0.4, 0.75):                                                      # abraçadeiras do feixe
    p = bezier(EL + Vector((-0.02, 0, Z0 + 0.1)), EL + Vector((-0.02, 0, 0.5)), Vector((0.62, 0.79, 0.34)), Vector((0.46, 0.79, 0.34)), 20)[int(t * 20)]
    q = bezier(EL + Vector((-0.02, 0, Z0 + 0.1)), EL + Vector((-0.02, 0, 0.5)), Vector((0.62, 0.79, 0.34)), Vector((0.46, 0.79, 0.34)), 20)[int(t * 20) + 1]
    u = (q - p).normalized()
    caixa(B('abracadeiras', 'aco'), p, (0.03, 0.15, 0.05), Matrix.Rotation(math.atan2(u.y, u.x), 3, 'Z') @ Matrix.Rotation(-math.asin(max(-1, min(1, u.z))), 3, 'Y'))
# caixa → pedestal (face norte), dois cabos grossos e prensa-cabo
PN = PLACAS[2][0] * (AP_C + 0.018)
for i, dx in enumerate((-0.05, 0.05)):
    cil(B('prensa_cabo', 'ferro', True), PN + Vector((dx, 0.012, 0.27)), 0.03, 0.03, Vector((0, 1, 0)), lados=16)
    pts = bezier(Vector((0.22 + i * 0.1, 0.65, 0.22)), Vector((0.22 + i * 0.1, 0.55, 0.22)), PN + Vector((dx, 0.12, 0.27)),
                 PN + Vector((dx, 0.025, 0.27)), 10)
    mangueira(B('cabos', 'cabo', True), pts, 0.02)
for i in range(2):
    cil(B('prensa_cabo', 'ferro', True), Vector((0.22 + i * 0.1, 0.655, 0.22)), 0.03, 0.03, Vector((0, 1, 0)), lados=16)

# ------------------------------------------------------------------ carregador de reserva (boca sul S1)
Y_EL0, Y_EL1 = -0.78, -0.56
bm = B('esteira_lado', 'amarelo')
for sx in (-1, 1):
    caixa_de(bm, (BX + sx * 0.115 - 0.01, -0.975, 0.12), (BX + sx * 0.115 + 0.01, Y_EL0, 0.25))
caixa_de(B('esteira_lona', 'borracha'), (BX - 0.1, -0.97, 0.175), (BX + 0.1, Y_EL0, 0.2))
for y in (-0.95, -0.81):
    cil(B('esteira_rolo', 'aco', True), Vector((BX, y, 0.187)), 0.02, 0.21, Vector((1, 0, 0)), lados=16)
    for sx in (-1, 1):
        caixa_de(B('esteira_pe', 'ferro'), (BX + sx * 0.115 - 0.015, y - 0.02, Z0), (BX + sx * 0.115 + 0.015, y + 0.02, 0.12))
caixa_de(B('boca_listras', 'listras'), (BX - 0.15, -0.985, 0.25), (BX + 0.15, -0.955, 0.28))
for sx in (-1, 1):
    caixa_de(B('esteira_lado', 'amarelo'), (BX + sx * 0.15 - 0.015, -0.985, 0.12), (BX + sx * 0.15 + 0.015, -0.955, 0.28))
cil(B('esteira_motor', 'grafite', True), Vector((BX + 0.17, -0.95, 0.187)), 0.04, 0.09, Vector((1, 0, 0)), lados=16)
# elevador com visor
XV = BX + 0.12
caixa_de(B('elevador', 'amarelo'), (BX - 0.12, Y_EL0, Z0), (XV - 0.05, Y_EL1, 0.56))     # corpo + nicho do visor a leste
for a_, b_ in (((XV - 0.05, Y_EL0, Z0), (XV, -0.74, 0.56)), ((XV - 0.05, -0.6, Z0), (XV, Y_EL1, 0.56)),
               ((XV - 0.05, -0.74, Z0), (XV, -0.6, 0.18)), ((XV - 0.05, -0.74, 0.52), (XV, -0.6, 0.56))):
    caixa_de(B('elevador', 'amarelo'), a_, b_)
caixa_de(B('elevador_tampa', 'ferro'), (BX - 0.13, Y_EL0 - 0.01, 0.56), (BX + 0.13, Y_EL1 + 0.01, 0.58))
caixa_de(B('elevador_boca', 'escuro'), (BX - 0.085, Y_EL0 - 0.003, 0.2), (BX + 0.085, Y_EL0 + 0.02, 0.32))
for sx in (-1, 1):
    caixa_de(B('elevador_quadro', 'ferro'), (BX + sx * 0.1 - 0.015, Y_EL0 - 0.012, 0.19), (BX + sx * 0.1 + 0.015, Y_EL0, 0.34))
caixa_de(B('elevador_quadro', 'ferro'), (BX - 0.115, Y_EL0 - 0.012, 0.32), (BX + 0.115, Y_EL0, 0.345))
caixa_de(B('elevador_listras', 'listras'), (BX - 0.115, Y_EL0 - 0.004, 0.36), (BX + 0.115, Y_EL0, 0.4))
caixa_de(B('elevador_visor', 'escuro'), (XV - 0.0505, -0.74, 0.18), (XV - 0.049, -0.6, 0.52))
for z in (0.17, 0.53):
    caixa_de(B('elevador_quadro', 'ferro'), (XV, -0.755, z - 0.012), (XV + 0.016, -0.585, z + 0.012))
for y in (-0.745, -0.595):
    caixa_de(B('elevador_quadro', 'ferro'), (XV, y - 0.01, 0.16), (XV + 0.016, y + 0.01, 0.54))
for y in (-0.7, -0.67, -0.64):
    tubo(B('elevador_grade', 'aco'), (XV - 0.004, y, 0.18), (XV - 0.004, y, 0.52), 0.003, 6)
cil(B('elevador_motor', 'grafite', True), Vector((BX, -0.70, 0.64)), 0.05, 0.12, lados=20)
cil(B('elevador_motor', 'ferro', True), Vector((BX, -0.70, 0.585)), 0.06, 0.012, lados=20)
# duto do elevador até a face sudeste do pedestal
NSE = Vector((1, -1, 0)).normalized()
E_D = Vector((BX - 0.02, Y_EL1 - 0.03, 0.46))
F_D = NSE * (AP_C - 0.02) + Vector((0, 0, 0.46))
u = (F_D - E_D)
caixa(B('duto', 'amarelo'), (E_D + F_D) / 2, (0.12, u.length, 0.12), Matrix.Rotation(math.atan2(u.y, u.x) - PI / 2, 3, 'Z'))
for t in (0.25, 0.75):
    caixa(B('duto_cinta', 'ferro'), E_D.lerp(F_D, t), (0.14, 0.02, 0.14), Matrix.Rotation(math.atan2(u.y, u.x) - PI / 2, 3, 'Z'))
caixa(B('duto_flange', 'ferro'), NSE * (AP_C + 0.012) + Vector((0, 0, 0.46)), (0.2, 0.012, 0.18), rot_face(NSE))
# cápsulas (munição de reserva) dentro do visor, subindo
capsulas_el = [capsula('capsula_elevador', 'latao_gasto', False, celula='celula_cheia') for k in range(6)]
capsulas_est = [capsula('capsula_esteira', 'latao_gasto', False, celula='celula_cheia') for k in range(3)]

# ------------------------------------------------------------------ giro (cabeça)
giro = bpy.data.objects.new('giro', None)
sc.collection.objects.link(giro)
G = 'giro'
bm = B('coroa', 'aco', True, G)
cil(bm, Vector((0, 0, (Z_G0 + Z_G1) / 2)), R_COROA - 0.012, Z_G1 - Z_G0, lados=72)
for k in range(80):
    a = k * 2 * PI / 80
    caixa(B('coroa_dentes', 'aco', False, G), Vector((math.cos(a), math.sin(a), 0)) * (R_COROA - 0.004) + Vector((0, 0, (Z_G0 + Z_G1) / 2)),
          (0.026, 0.016, Z_G1 - Z_G0), Matrix.Rotation(a, 3, 'Z'))
cil(B('mesa', 'ferro', True, G), Vector((0, 0, (Z_G1 + Z_MESA) / 2)), 0.43, Z_MESA - Z_G1, lados=64)
for k in range(24):
    a = k * 2 * PI / 24
    cil(B('parafusos', 'aco', False, G), Vector((math.cos(a), math.sin(a), 0)) * 0.4 + Vector((0, 0, Z_MESA + 0.006)), 0.01, 0.012, lados=6)
caixa_de(B('placa_cabeca', 'grafite', False, G), (-0.64, -0.34, Z_MESA), (0.34, 0.34, Z_PL))
for x in (-0.6, -0.2, 0.3):
    for s in (-1, 1):
        parafuso((x, s * 0.3, Z_PL + 0.006), (0, 0, 1), G)
# bochechas blindadas
PERFIL = [(-0.42, Z_PL), (0.24, Z_PL), (0.24, 1.04), (0.1, 1.32), (-0.26, 1.32), (-0.42, 1.18)]
for s in (-1, 1):
    y0, y1 = (0.25, 0.32) if s > 0 else (-0.32, -0.25)
    prisma_xz(B('bochechas', 'amarelo', False, G), PERFIL, y0, y1)
    yo = s * 0.322
    for x, z in ((-0.36, 0.9), (-0.36, 1.13), (-0.2, 1.27), (0.0, 1.27), (0.18, 0.9), (0.18, 1.04), (-0.12, 0.9), (0.07, 1.23)):
        parafuso((x, yo, z), (0, s, 0), G, 0.012)
    # mancal do munhão (lado de fora) e tampa aparafusada
    cil(B('mancal', 'ferro', True, G), Vector((TX, s * 0.345, TZ)), 0.1, 0.05, Vector((0, 1, 0)), lados=32)
    cil(B('mancal_tampa', 'aco', True, G), Vector((TX, s * 0.375, TZ)), 0.065, 0.012, Vector((0, 1, 0)), lados=24)
    for k in range(6):
        a = k * PI / 3
        parafuso((TX + math.cos(a) * 0.082, s * 0.372, TZ + math.sin(a) * 0.082), (0, s, 0), G, 0.009)
    # junta rotativa: feixe de cabos da caixa traseira ao mancal, por fora da bochecha
    pts = bezier(Vector((-0.55, s * 0.305, 1.02)), Vector((-0.55, s * 0.36, 1.02)), Vector((-0.2, s * 0.355, 1.16)),
                 Vector((TX - 0.085, s * 0.355, TZ + 0.01)), 16)
    feixe(B('cabos', 'cabo', True, G), B('abracadeiras', 'aco', True, G), pts, Vector((0, 0, 1)), n=3, r=0.012, passo=5)
    for x in (-0.33, -0.12):
        caixa(B('suporte_cabo', 'ferro', False, G), Vector((x, s * 0.33, 1.08 + (x + 0.33) * 0.3)), (0.025, 0.02, 0.07))
    # fuligem na frente da bochecha (sopro da boca)
    for k in range(6):
        z = random.uniform(1.0, 1.25)
        caixa(B('fuligem', 'chamusco', False, G), Vector((0.24 - (z - 1.04) * 0.5 + 0.002, s * random.uniform(0.255, 0.315), z)),
              (0.004, random.uniform(0.01, 0.03), random.uniform(0.04, 0.12)), Matrix.Rotation(0.47, 3, 'Y'))
# caixa traseira (eletrônica e carga) com aletas
caixa_de(B('traseira', 'grafite', False, G), (-0.64, -0.3, Z_PL), (-0.42, 0.3, 1.16))
caixa_de(B('traseira_tampa', 'ferro', False, G), (-0.65, -0.31, 1.16), (-0.41, 0.31, 1.18))
for k in range(11):
    y = -0.25 + k * 0.05
    caixa_de(B('aletas_traseira', 'aco', False, G), (-0.71, y - 0.004, 0.88), (-0.64, y + 0.004, 1.13))
for z in (0.9, 1.11):
    caixa_de(B('aletas_traseira', 'ferro', False, G), (-0.715, -0.27, z - 0.008), (-0.64, 0.27, z + 0.008))
for k, m in enumerate(('led_verde', 'led_ambar', 'led_verde')):
    cil(B('led_' + m, m, False, G), Vector((-0.52 + k * 0.04, 0.302, 1.12)), 0.008, 0.006, Vector((0, 1, 0)), lados=10)
caixa_de(B('traseira_listras', 'listras', False, G), (-0.64, -0.302, 0.86), (-0.42, -0.3, 0.9))
# garfos dos pistões (camisa) na placa e válvula com mangueiras
for s in (-1, 1):
    y = s * YP
    for dy in (-0.042, 0.042):
        caixa_de(B('garfo', 'ferro', False, G), (A_PIS.x - 0.05, y + dy - 0.008, Z_PL), (A_PIS.x + 0.05, y + dy + 0.008, A_PIS.z + 0.04))
    cil(B('pino', 'aco', True, G), Vector((A_PIS.x, y, A_PIS.z)), 0.014, 0.11, Vector((0, 1, 0)), lados=12)
    cil(B('pino_rotula', 'ferro', True, G), Vector((A_PIS.x, y - s * 0.07, A_PIS.z)), 0.02, 0.03, Vector((0, 1, 0)), lados=12)
    caixa_de(B('valvula', 'amarelo', False, G), (0.02, y - s * 0.07 - 0.04, Z_PL), (0.12, y - s * 0.07 + 0.04, Z_PL + 0.07))
    pts = bezier(Vector((0.12, y - s * 0.07, Z_PL + 0.04)), Vector((0.17, y - s * 0.07, Z_PL + 0.04)),
                 Vector((A_PIS.x - 0.04, y - s * 0.085, A_PIS.z - 0.02)), Vector((A_PIS.x, y - s * 0.085, A_PIS.z)), 8)
    mangueira(B('mangueiras', 'borracha', True, G), pts, 0.009)
    for k in range(3):
        mancha(B('oleo', 'oleo', False, G), (A_PIS.x + random.uniform(-0.06, 0.04), y + random.uniform(-0.05, 0.05)), random.uniform(0.02, 0.04), Z_PL + 0.0012)
# casulo sensor (sobre a bochecha direita) com olho e varredor laser
SY = -0.285
caixa_de(B('sensor', 'grafite', False, G), (-0.2, SY - 0.085, 1.32), (0.06, SY + 0.085, 1.43))
caixa_de(B('sensor_viseira', 'ferro', False, G), (0.0, SY - 0.09, 1.43), (0.09, SY + 0.09, 1.445))
cil(B('sensor_lente', 'ferro', True, G), Vector((0.08, SY, 1.375)), 0.05, 0.04, Vector((1, 0, 0)), lados=28)
toro(B('sensor_aro', 'cromo', True, G), Vector((0.1, SY, 1.375)), 0.042, 0.006, 32, 8, Matrix.Rotation(PI / 2, 3, 'Y'))
cil(B('sensor_olho', 'olho', False, G), Vector((0.101, SY, 1.375)), 0.034, 0.004, Vector((1, 0, 0)), lados=28)
for k, m in enumerate(('led_verde', 'led_ambar')):
    cil(B('led_' + m, m, False, G), Vector((0.061, SY + 0.06 - k * 0.12, 1.41)), 0.007, 0.005, Vector((1, 0, 0)), lados=10)
cil(B('varredor_base', 'ferro', True, G), Vector((-0.08, SY, 1.44)), 0.04, 0.02, lados=20)
pts = bezier(Vector((-0.2, SY, 1.38)), Vector((-0.28, SY, 1.38)), Vector((-0.3, SY + 0.02, 1.3)), Vector((-0.3, SY + 0.02, 1.29)), 6)
mangueira(B('cabos', 'cabo', True, G), pts, 0.01)
S_VARR = Vector((-0.08, SY, 1.47))
varredor = bpy.data.objects.new('varredor', None)
sc.collection.objects.link(varredor)
varredor.parent = giro
varredor.location = S_VARR
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.032, 0.04, lados=20)
cil(bm, Vector((0, 0, 0.026)), 0.026, 0.012, lados=20)
obj('varredor_cabeca', bm, 'grafite', varredor)
bm = bmesh.new()
cil(bm, Vector((0.033, 0, 0)), 0.012, 0.006, Vector((1, 0, 0)), lados=12)
obj('varredor_lente', bm, 'laser', varredor)
# antena na bochecha esquerda
tubo(B('antena', 'aco', True, G), (-0.3, 0.29, 1.29), (-0.3, 0.29, 1.62), 0.006, 8)
cil(B('antena_base', 'ferro', True, G), Vector((-0.3, 0.29, 1.27)), 0.022, 0.04, lados=12)
curva(B('antena_led', 'led_ambar', True, G), Vector((-0.3, 0.29, 1.625)), 0.011, 10)

# ------------------------------------------------------------------ canhão (inclina no munhão) e cano (recua)
canhao = bpy.data.objects.new('canhao', None)
sc.collection.objects.link(canhao)
canhao.parent = giro
canhao.location = (TX, 0, TZ)
cano = bpy.data.objects.new('cano', None)
sc.collection.objects.link(cano)
cano.parent = canhao
K, CN = 'canhao', 'cano'
cil(B('munhao', 'aco', True, K), Vector((0, 0, 0)), 0.065, 0.5, Vector((0, 1, 0)), lados=28)
for s in (-1, 1):
    cil(B('munhao_colar', 'ferro', True, K), Vector((0, s * 0.135, 0)), 0.09, 0.02, Vector((0, 1, 0)), lados=28)
caixa_de(B('culatra', 'grafite', False, K), (-0.33, -0.12, -0.12), (0.12, 0.12, 0.12))
for x in (-0.29, 0.08):
    caixa_de(B('culatra_cinta', 'aco', False, K), (x - 0.015, -0.126, -0.126), (x + 0.015, 0.126, 0.126))
VENTS = []
for x in (-0.24, -0.15, -0.06):                                            # respiros no topo
    caixa_de(B('respiro', 'ferro', False, K), (x - 0.035, -0.09, 0.12), (x + 0.035, 0.09, 0.14))
    for j in range(5):
        caixa_de(B('respiro_fenda', 'escuro', False, K), (x - 0.025, -0.07 + j * 0.035 - 0.006, 0.14), (x + 0.025, -0.07 + j * 0.035 + 0.006, 0.141))
    VENTS.append(Vector((x, 0, 0.15)))
caixa_de(B('ejecao', 'escuro', False, K), (-0.015, 0.0, 0.118), (0.06, 0.11, 0.1205))     # porta de ejeção (topo, lado +y)
for y in (-0.008, 0.118):
    caixa_de(B('ejecao_quadro', 'ferro', False, K), (-0.025, y - 0.008, 0.12), (0.07, y + 0.008, 0.135))
for x in (-0.02, 0.065):
    caixa_de(B('ejecao_quadro', 'ferro', False, K), (x - 0.006, -0.008, 0.12), (x + 0.006, 0.118, 0.135))
caixa_de(B('ejecao_defletor', 'ferro', False, K), (-0.025, -0.02, 0.12), (0.07, -0.008, 0.19))      # defletor joga para +y
for k in range(4):
    caixa_de(B('fuligem_ejecao', 'chamusco', False, K), (-0.02 + k * 0.022, 0.0, 0.1206), (-0.01 + k * 0.022, 0.12, 0.1208))
PORTA = Vector((0.025, 0.055, 0.145))
for x in (-0.33 + 0.004, 0.12 - 0.004):
    for sy in (-1, 1):
        for sz in (-1, 1):
            parafuso((x, sy * 0.1, sz * 0.1), (1 if x > 0 else -1, 0, 0), K, 0.01)
for j in range(3):                                                          # células de carga no lado +y
    z = -0.07 + j * 0.065
    cil(B('celulas', 'amarelo', True, K), Vector((-0.2, 0.155, z)), 0.03, 0.22, Vector((1, 0, 0)), lados=20)
    cil(B('celulas_tampa', 'cobre', True, K), Vector((-0.085, 0.155, z)), 0.018, 0.012, Vector((1, 0, 0)), lados=12)
    cil(B('celulas_tampa', 'cobre', True, K), Vector((-0.315, 0.155, z)), 0.018, 0.012, Vector((1, 0, 0)), lados=12)
    tubo(B('cabos', 'cabo', True, K), (-0.079, 0.155, z), (-0.05, 0.155, z), 0.01, 8)
caixa_de(B('celulas_cinta', 'ferro', False, K), (-0.3, 0.12, -0.11), (-0.28, 0.19, 0.11))
caixa_de(B('celulas_cinta', 'ferro', False, K), (-0.12, 0.12, -0.11), (-0.1, 0.19, 0.11))
# colar do berço (pistões) com orelhas
CX0, CX1 = 0.40, 0.46
bm = B('colar', 'ferro', False, K)
caixa_de(bm, (CX0, -0.15, 0.076), (CX1, 0.15, 0.12))
caixa_de(bm, (CX0, -0.15, -0.12), (CX1, 0.15, -0.076))
for s in (-1, 1):
    caixa_de(bm, (CX0, s * 0.056, -0.076), (CX1, s * 0.15, 0.076))
for s in (-1, 1):
    y = s * YP
    for dy in (-0.035, 0.035):
        caixa_de(B('colar_orelha', 'ferro', False, K), (B_PIS.x - 0.03, y + dy - 0.007, B_PIS.z - 0.03), (B_PIS.x + 0.03, y + dy + 0.007, -0.076))
    cil(B('pino', 'aco', True, K), Vector((B_PIS.x, y, B_PIS.z)), 0.012, 0.09, Vector((0, 1, 0)), lados=12)
caixa_de(B('colar_listras', 'listras', False, K), (CX0 + 0.005, -0.14, 0.12), (CX1 - 0.005, 0.14, 0.123))
# trilhos (cano): aço com face de cobre, separados pelo vão (o "trilho duplo")
for s in (-1, 1):
    zr = (0.03, 0.075) if s > 0 else (-0.075, -0.03)
    caixa_de(B('trilho', 'aco', False, CN), (0.14, -0.04, zr[0]), (0.92, 0.04, zr[1]))
    zc = (0.026, 0.031) if s > 0 else (-0.031, -0.026)
    caixa_de(B('trilho_face', 'cobre', False, CN), (0.14, -0.032, zc[0]), (0.92, 0.032, zc[1]))
    caixa_de(B('trilho_quente', 'brasa', False, CN), (0.74, -0.03, zc[0] - s * 0.0005), (0.92, 0.03, zc[1] - s * 0.0005))
for x in (0.15, 0.48, 0.78):                                               # espaçadores isolantes
    for s in (-1, 1):
        caixa_de(B('espacador', 'isol_verm', False, CN), (x - 0.02, s * 0.04, -0.075), (x + 0.02, s * 0.056, 0.075))
# bobinas de aceleração e anéis de carga
for j, x in enumerate((0.2, 0.255, 0.31, 0.365)):
    toro(B('bobinas', 'bobina', True, CN), Vector((x, 0, 0)), 0.11, 0.021, 48, 12, Matrix.Rotation(PI / 2, 3, 'Y'))
    if j < 3:
        toro(B('anel_carga', 'brilho', True, CN), Vector((x + 0.0275, 0, 0)), 0.104, 0.006, 40, 6, Matrix.Rotation(PI / 2, 3, 'Y'))
for k in range(4):                                                         # gaiola de tirantes
    a = PI / 4 + k * PI / 2
    p = Vector((0, math.cos(a) * 0.14, math.sin(a) * 0.14))
    tubo(B('tirantes', 'aco', True, CN), p + Vector((0.17, 0, 0)), p + Vector((0.395, 0, 0)), 0.007, 8)
    for x in (0.17, 0.39):
        caixa(B('tirante_bloco', 'ferro', False, CN), p * 0.82 + Vector((x, 0, 0)), (0.016, 0.03, 0.06), Matrix.Rotation(a - PI / 2, 3, 'X'))
for x in (0.17, 0.39):
    caixa_de(B('bobina_quadro', 'ferro', False, CN), (x - 0.008, -0.04, 0.075), (x + 0.008, 0.04, 0.11))
    caixa_de(B('bobina_quadro', 'ferro', False, CN), (x - 0.008, -0.04, -0.11), (x + 0.008, 0.04, -0.075))
# aletas de dissipação
for k in range(12):
    x = 0.52 + k * 0.02
    caixa_de(B('aletas', 'aco', False, CN), (x - 0.002, -0.12, -0.12), (x + 0.002, 0.12, 0.12))
for s in (-1, 1):
    for t in (-1, 1):
        tubo(B('aletas_tirante', 'ferro', True, CN), (0.51, s * 0.1, t * 0.1), (0.75, s * 0.1, t * 0.1), 0.006, 8)
# boca: bloco com eletrodos, enegrecido
caixa_de(B('boca', 'queimado', False, CN), (0.8, -0.09, 0.075), (0.88, 0.09, 0.11))
caixa_de(B('boca', 'queimado', False, CN), (0.8, -0.09, -0.11), (0.88, 0.09, -0.075))
for s in (-1, 1):
    caixa_de(B('boca', 'queimado', False, CN), (0.8, s * 0.04, -0.075), (0.88, s * 0.09, 0.075))
    caixa_de(B('eletrodo', 'cobre', False, CN), (0.92, -0.03, s * 0.03), (0.95, 0.03, s * 0.07))
    caixa_de(B('fuligem_boca', 'chamusco', False, CN), (0.88, -0.041, s * 0.0755), (0.93, 0.041, s * 0.0905))
    caixa_de(B('fuligem_boca', 'chamusco', False, CN), (0.79, s * 0.0905, -0.1), (0.885, s * 0.0915, 0.1))
MUZ = Vector((0.96, 0, 0))                                                 # ponto da boca (cano)
# arcos entre os eletrodos
arcos = []
for v in range(4):
    bm = bmesh.new()
    p0 = Vector((0.935 + random.uniform(-0.01, 0.01), random.uniform(-0.02, 0.02), 0.032))
    p1 = Vector((0.935 + random.uniform(-0.01, 0.01), random.uniform(-0.02, 0.02), -0.032))
    pts = [p0] + [p0.lerp(p1, t) + Vector((random.uniform(0, 0.03), random.uniform(-0.02, 0.02), 0)) for t in (0.2, 0.4, 0.6, 0.8)] + [p1]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, 0.003, 5)
    if v % 2:
        m = pts[2]
        tubo(bm, m, m + Vector((0.05, random.uniform(-0.03, 0.03), random.uniform(-0.02, 0.02))), 0.002, 5)
    arcos.append(obj('arco', bm, 'arco', cano))
# clarão: núcleo, cone e plasma (filhos do cano)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
clarao = obj('clarao', bm, 'clarao', cano)
clarao.location = MUZ + Vector((0.02, 0, 0))
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=1.0, radius2=0.0, depth=1.0,
                      matrix=Matrix.Translation((0.5, 0, 0)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
cone = obj('clarao_cone', bm, 'clarao', cano)
cone.location = MUZ
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
plasma = obj('plasma', bm, 'plasma', cano)
plasma.location = MUZ + Vector((0.06, 0, 0))
bm = bmesh.new()                                                           # projétil em voo com cauda afinando até a boca
bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0, radius2=0.012, depth=1.5,
                      matrix=Matrix.Translation((0.85, 0, 0)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.02, matrix=Matrix.Translation((1.6, 0, 0)))
rastro = obj('rastro', bm, 'rastro', cano)
rastro.location = MUZ
luz_b = bpy.data.lights.new('Clarão', 'POINT')
luz_b.color = (0.75, 0.55, 1.0)
luz_b.shadow_soft_size = 0.05
lb = bpy.data.objects.new('Clarão', luz_b)
sc.collection.objects.link(lb)
lb.parent = cano
lb.location = MUZ + Vector((0.12, 0, 0.05))

# ------------------------------------------------------------------ pistões (camisa no giro, haste no colar do berço)
pistoes = []
for i, s in enumerate((1, -1)):
    p = bpy.data.objects.new('pistao%d' % i, None)
    sc.collection.objects.link(p)
    p.parent = giro
    p.location = Vector((A_PIS.x, s * YP, A_PIS.z))
    p.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.026, 0.05, Vector((0, 1, 0)), lados=16)            # olhal
    cil(bm, Vector((0, 0, 0.03 + L_CAM / 2)), 0.034, L_CAM, lados=24)
    cil(bm, Vector((0, 0, 0.03 + L_CAM)), 0.04, 0.02, lados=24)                        # cabeçote
    cil(bm, Vector((0, 0, 0.045)), 0.04, 0.02, lados=24)
    o = obj('pistao%d_camisa' % i, bm, 'amarelo', p)
    suavizar(o)
    bm = bmesh.new()
    for z in (0.045, 0.03 + L_CAM):                                                   # tomadas e mangueira entre elas
        cil(bm, Vector((-0.04, 0, z)), 0.009, 0.02, Vector((1, 0, 0)), lados=10)
    mangueira(bm, bezier(Vector((-0.05, 0, 0.045)), Vector((-0.08, 0, 0.08)), Vector((-0.08, 0, 0.2)), Vector((-0.05, 0, 0.03 + L_CAM)), 10), 0.007)
    suavizar(obj('pistao%d_mangueira' % i, bm, 'borracha', p))
    h = bpy.data.objects.new('pistao%d_haste_eixo' % i, None)
    sc.collection.objects.link(h)
    h.parent = p
    bm = bmesh.new()
    cil(bm, Vector((0, 0, L_HAS / 2)), 0.016, L_HAS, lados=20)
    cil(bm, Vector((0, 0, L_HAS)), 0.022, 0.05, Vector((0, 1, 0)), lados=16)           # olhal da haste
    suavizar(obj('pistao%d_haste' % i, bm, 'cromo', h))
    bm = bmesh.new()                                                                   # óleo na haste
    caixa_de(bm, (0.0155, -0.004, 0.02), (0.0165, 0.004, 0.09))
    obj('pistao%d_oleo' % i, bm, 'oleo', h)
    pistoes.append((p, h, s))

# ------------------------------------------------------------------ sujeira no chão: cápsulas, queimado, pó
def livre(x, y):
    if math.hypot(x, y) < 0.66:
        return False
    if -0.86 < x < -0.1 and 0.66 < y < 0.92:
        return False
    if 0.12 < x < 0.47 and 0.64 < y < 0.95:
        return False
    if BX - 0.17 < x < BX + 0.17 and y < -0.53:
        return False
    if math.hypot(x + 0.78, y - 0.47) < 0.16:                    # onde caem as cápsulas da rajada animada
        return False
    if (Vector((x, y, 0)) - CM).length < 0.12 or (Vector((x, y, 0)) - EL).length < 0.12:
        return False
    return abs(x) < 0.94 and abs(y) < 0.94


n = 0
while n < 26:
    a = random.uniform(-PI * 0.95, PI * 0.6)
    r = random.uniform(0.66, 0.93)
    x, y = math.cos(a) * r, math.sin(a) * r
    if not livre(x, y):
        continue
    o = capsula('capsula_chao', 'boca_fria', True, 'latao_gasto' if n % 5 else 'aco_capsula')
    o.location = (x, y, Z0 + R_CAP)
    o.rotation_euler = (random.uniform(0, 2 * PI), 0, random.uniform(0, 2 * PI))
    n += 1
for k in range(16):                                                        # queimado de disparo e de arco
    a = random.uniform(-PI, PI)
    r = random.uniform(0.62, 0.92)
    x, y = math.cos(a) * r, math.sin(a) * r
    if livre(x, y):
        mancha(B('fuligem_chao', 'fuligem_chao'), (x, y), random.uniform(0.04, 0.09), Z0 + 0.001)
for k in range(10):
    a = random.uniform(0, 2 * PI)
    mancha(B('chamusco', 'chamusco'), (math.cos(a) * 0.5, math.sin(a) * 0.5), random.uniform(0.03, 0.06), 0.1505)
for k in range(12):
    x, y = random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95)
    if livre(x, y):
        mancha(B('po', 'po'), (x, y), random.uniform(0.05, 0.12), Z0 + 0.0008)
for k in range(8):                                                         # escorridos de ferrugem nas placas
    kk = random.randrange(8)
    n_, R = PLACAS[kk]
    L = random.uniform(0.08, 0.24)
    caixa(B('escorridos', 'ferrugem'), n_ * (AP_C + 0.0185) + R @ Vector((random.uniform(-0.1, 0.1), 0, 0)) + Vector((0, 0, 0.53 - L / 2)),
          (random.uniform(0.006, 0.015), 0.002, L), R)

# ------------------------------------------------------------------ objetos estáticos
PAIS = {'base': None, 'giro': giro, 'canhao': canhao, 'cano': cano}
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(nome if g == 'base' else g + '_' + nome, bm, mat, PAIS[g])
    if liso:
        suavizar(o)


# ------------------------------------------------------------------ partículas animadas
def bolinha(nome, mat, r, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    return obj(nome, bm, mat)


def volume(nome, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    return obj(nome, bm, mat)


TIROS = [40, 48, 56, 64]                       # 3 tiros/s (8 quadros)
faiscas = [bolinha('faisca', 'faisca', 0.006, 0) for _ in range(18)]
vel_f = [Vector((random.uniform(1.5, 3.5), random.uniform(-1.2, 1.2), random.uniform(-0.6, 1.4))) for _ in faiscas]
fumacas = [(volume('fumaca', 'fumaca'), it, j) for it in range(len(TIROS)) for j in range(2)]
vapores = [(volume('vapor', 'vapor'), iv, j) for iv in range(3) for j in range(2)]
# cápsula ejetada a cada tiro: boca quente própria (esfria em ~1 s), fiapo de fumaça no voo, fumacinha final no chão
ejetadas, anteriores, quentes = [], [], []
for it in range(len(TIROS)):
    mq = emissivo('Boca quente %d' % it, (1.0, 0.32, 0.05), 0.0, (0.03, 0.025, 0.022))
    base3d.M['quente%d' % it] = mq
    quentes.append(mq.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'])
    ejetadas.append(capsula('capsula_ejetada%d' % it, 'quente%d' % it, True, 'latao_gasto' if it % 3 else 'aco_capsula'))
    anteriores.append(capsula('capsula_laco_anterior%d' % it, 'boca_fria', True, 'latao_gasto' if it % 3 else 'aco_capsula'))
N_RASTRO, N_FINAL = 7, 3
fiapos = [[volume('fiapo', 'fiapo') for _ in range(N_RASTRO + N_FINAL)] for it in range(len(TIROS))]


def chao_h(x, y):
    if math.hypot(x, y) * math.cos(PI / 8) < AP_P - 0.01:      # sapata do pedestal (aprox.)
        return 0.15
    if abs(x) < 0.98 and abs(y) < 0.98:
        return Z0
    return 0.0


def simula_capsula(it, semente):
    """Física simples: gravidade, giro no ar, quique com perda, atrito, rola perpendicular ao eixo e para.
    Devolve, por quadro desde o tiro, (posição, euler, no_ar) e o quadro em que parou."""
    rnd = random.Random(semente)
    yaw0, pitch0 = pose(TIROS[it])
    Mc = M_canhao(yaw0, pitch0)
    p = Mc @ PORTA
    v = Matrix.Rotation(yaw0, 3, 'Z') @ Vector((-0.55 + rnd.uniform(-0.1, 0.1), 0.72 + rnd.uniform(-0.04, 0.04), 2.2 + rnd.uniform(-0.08, 0.08)))
    ax = Mc.to_3x3() @ Vector((0, 1, 0))
    psi, th, phi = math.atan2(ax.y, ax.x), 0.0, 0.0
    w_psi, w_th = rnd.uniform(-9, 9), rnd.choice((-1, 1)) * rnd.uniform(16, 24)
    passo = 1 / 240
    no_chao, quiques, parou = False, 0, None
    quadros = []
    t = 0.0
    for e in range(QUADROS + 1):
        while t < e / FPS - 1e-9:
            t += passo
            h = chao_h(p.x, p.y)
            if not no_chao:
                v.z -= 9.81 * passo
                p += v * passo
                th += w_th * passo
                psi += w_psi * passo
                h = chao_h(p.x, p.y)
                if p.z - R_CAP <= h:
                    p.z = h + R_CAP
                    if v.z < -0.55 and quiques < 2:
                        v.z = -v.z * 0.36
                        v.x *= 0.5
                        v.y *= 0.5
                        w_th *= 0.45
                        w_psi *= 0.5
                        quiques += 1
                    else:
                        v.z = 0.0
                        no_chao = True
                if quiques:                                            # depois do 1º quique tende a deitar
                    alvo = round(th / PI) * PI
                    th += (alvo - th) * min(1.0, 5 * passo)
            else:
                p.z = h + R_CAP
                a = Vector((math.cos(psi), math.sin(psi), 0))
                vh = Vector((v.x, v.y, 0))
                ao_longo = vh.dot(a)
                vh = vh - a * ao_longo * (1 - math.exp(-10 * passo))      # desliza pouco ao longo do eixo
                s = vh.length
                if s > 0:
                    vh *= max(0.0, s - 1.6 * passo) / s                  # atrito de rolamento
                v = Vector((vh.x, vh.y, 0))
                nrm = Vector((-a.y, a.x, 0))
                phi += v.dot(nrm) / R_CAP * passo
                p += v * passo
                alvo = round(th / PI) * PI
                th += (alvo - th) * min(1.0, 14 * passo)
                w_psi *= math.exp(-8 * passo)
                psi += w_psi * passo
                if v.length < 0.01 and parou is None:
                    parou = e
        quadros.append((p.copy(), (phi, -th, psi), not no_chao))
    return quadros, parou if parou is not None else QUADROS


def boca_mundo(pos, eul):
    return pos + Euler(eul, 'XYZ').to_matrix() @ Vector((0.093 - CX, 0, 0))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.5)), 1.0, 1.0, lados=8)
laser = obj('laser_feixe', bm, 'laser')
laser.rotation_mode = 'QUATERNION'
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=1.0)
ponto = obj('laser_ponto', bm, 'laser')
luz_l = bpy.data.lights.new('Ponto laser', 'POINT')
luz_l.color = (1.0, 0.1, 0.05)
luz_l.energy = 1.5
luz_l.shadow_soft_size = 0.01
ll = bpy.data.objects.new('Ponto laser', luz_l)
sc.collection.objects.link(ll)
luz_o = bpy.data.lights.new('Olho', 'POINT')                 # brilho do olho na viseira
luz_o.color = VIOLETA
luz_o.energy = 0.6
luz_o.shadow_soft_size = 0.02
lo = bpy.data.objects.new('Olho', luz_o)
sc.collection.objects.link(lo)
lo.parent = giro
lo.location = (0.14, SY, 1.375)


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def pose(q):
    """(yaw, pitch) no quadro q: vira e eleva até 30, segura na rajada, volta de 74 a 96."""
    Y0, Y1, P0, P1 = math.radians(-55), math.radians(25), math.radians(2), math.radians(14)
    if q <= 30:
        t = suave((q - 1) / 29)
        return Y0 + (Y1 - Y0) * t, P0 + (P1 - P0) * t
    if q <= 72:
        tr = 0.0
        return Y1 + math.radians(1.2) * math.sin(q * 0.7) * (1 if q < 38 else 0.2), P1
    t = suave((q - 72) / 25)
    return Y1 + (Y0 - Y1) * t, P1 + (P0 - P1) * t


def M_canhao(yaw, pitch, rec=0.0):
    return (Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((TX, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y')
            @ Matrix.Translation((-rec, 0, 0)))


def tiro_info(q):
    """(índice do último tiro, quadros desde ele) ou (None, None)."""
    ult = None
    for i, s in enumerate(TIROS):
        if q >= s:
            ult = i
    return (ult, q - TIROS[ult]) if ult is not None else (None, None)


def recuo(q):
    i, dt = tiro_info(q)
    if i is None or dt > 5:
        return 0.0
    return REC * (1 - dt / 5) ** 1.5


def carga_bobinas(q):
    """0 → 1 enquanto carrega para o próximo tiro; cai a zero no disparo."""
    if q < 30 or q > 74:
        return 0.0
    i, dt = tiro_info(q)
    if i is None:
        return suave((q - 30) / 10)
    if i == len(TIROS) - 1:
        return max(0.0, 1 - dt / 6) * 0.3 if dt > 0 else 1.0
    return 1.0 if dt == 0 else suave(dt / 7)


def nivel_banco(q):
    i, dt = tiro_info(q)
    tiros = 0 if i is None else i + 1
    if q <= 72:
        return 0.86 - 0.05 * tiros
    return 0.86 - 0.05 * len(TIROS) * (1 - suave((q - 72) / 24))


TRAJ = []
for it in range(len(TIROS)):
    tr, parou = simula_capsula(it, 100 + it)
    TRAJ.append((tr, parou))
    print('CAPSULA', it, 'tiro', TIROS[it], 'parou em', TIROS[it] + parou, 'pos', tuple(round(c, 3) for c in tr[parou][0]),
          'voo', [round(tr[e][0].z, 2) for e in range(14, 34)])


brilho = base3d.M['brilho'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
brasa = base3d.M['brasa'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
carga_e = base3d.M['carga'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
EIXO_Z = Vector((0, 0, 1))
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    yaw, pitch = pose(q)
    rec = recuo(q)
    g = carga_bobinas(q)
    it, dt = tiro_info(q)
    giro.rotation_euler = (0, 0, yaw)
    giro.keyframe_insert('rotation_euler', frame=q)
    canhao.rotation_euler = (0, -pitch, 0)
    canhao.keyframe_insert('rotation_euler', frame=q)
    cano.location = (-rec, 0, 0)
    cano.keyframe_insert('location', frame=q)
    pinhao.rotation_euler = (0, 0, -yaw * R_COROA / R_PINHAO)
    pinhao.keyframe_insert('rotation_euler', frame=q)
    # pistões: camisa aponta para o pino do colar; a haste desliza
    Mp = Matrix.Translation((TX, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y')
    for p, h, s in pistoes:
        A = Vector((A_PIS.x, s * YP, A_PIS.z))
        Bp = Mp @ Vector((B_PIS.x, s * YP, B_PIS.z))
        d = Bp - A
        p.rotation_quaternion = d.to_track_quat('Z', 'Y')
        p.keyframe_insert('rotation_quaternion', frame=q)
        h.location = (0, 0, d.length - L_HAS)
        h.keyframe_insert('location', frame=q)
    # carga: bobinas, banco, trilho quente
    brilho.default_value = 0.3 + 5.0 * g + (6.0 if dt == 0 else 0.0)
    brilho.keyframe_insert('default_value', frame=q)
    quente = 0.0 if it is None else max(0.0, 1 - (q - TIROS[it]) / 30) * (0.6 + 0.4 * (it + 1) / len(TIROS))
    if q > 72:
        quente = max(0.0, 1 - (q - TIROS[-1]) / 30)
    brasa.default_value = 0.3 + 9.0 * quente
    brasa.keyframe_insert('default_value', frame=q)
    nv = nivel_banco(q)
    for fx in faixas:
        fx.scale = (1, 1, max(0.03, nv))
        fx.keyframe_insert('scale', frame=q)
    carga_e.default_value = 2.0 + (1.5 if dt in (0, 1) else 0.0)
    carga_e.keyframe_insert('default_value', frame=q)
    # arcos na boca: carregado tremula; no disparo, todos
    for v, o in enumerate(arcos):
        vis = (dt == 0) or (g > 0.55 and ((q * 3 + v * 5) % 7) < 2)
        o.hide_render = o.hide_viewport = not vis
        o.keyframe_insert('hide_render', frame=q)
        o.keyframe_insert('hide_viewport', frame=q)
    # clarão, cone, plasma, rastro e luz
    fl = 1.0 if dt == 0 else (0.45 if dt == 1 else 0.0)
    for o, esc in ((clarao, (0.07, 0.07, 0.07)), (cone, (0.32, 0.1, 0.1)), (plasma, (0.16, 0.13, 0.13))):
        o.scale = [max(0.01, e * (fl if o is not plasma else (1.0 if dt == 0 else (0.8 if dt == 1 else 0.5 if dt == 2 else 0)))) for e in esc]
        vis = fl > 0 if o is not plasma else (dt is not None and dt <= 2 and q <= 72)
        o.hide_render = o.hide_viewport = not vis
        for c in ('scale', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
    rastro.hide_render = rastro.hide_viewport = dt != 0
    for c in ('hide_render', 'hide_viewport'):
        rastro.keyframe_insert(c, frame=q)
    luz_b.energy = 220.0 * fl + 4.0 * g
    luz_b.keyframe_insert('energy', frame=q)
    # faíscas saindo da boca
    for k, o in enumerate(faiscas):
        viva = False
        if it is not None and dt <= 6 and q <= 72:
            tt = dt / FPS + (k % 3) * 0.008
            Mc = M_canhao(*pose(TIROS[it]))
            p0 = Mc @ MUZ
            v = Mc.to_3x3() @ vel_f[k]
            p = p0 + v * tt + Vector((0, 0, -4.9 * tt * tt))
            viva = p.z > 0.02
            o.location = p
        else:
            o.location = (0, 0, 1.0)
        o.scale = [max(0.001, 1 - dt / 7) if viva else 0.001] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    # cápsula ejetada a cada tiro: sai da porta no recuo girando, quica, rola, para e fica
    for i2, o in enumerate(ejetadas):
        tr, parou = TRAJ[i2]
        e = q - TIROS[i2]
        ant = anteriores[i2]                                   # a do laço anterior, já parada no mesmo lugar
        pos_fim, eul_fim, _ = tr[parou]
        ant.location, ant.rotation_euler = pos_fim, eul_fim
        vis_ant = e < parou
        for ob in [ant] + list(ant.children):
            ob.hide_render = ob.hide_viewport = not vis_ant
            ob.keyframe_insert('hide_render', frame=q)
            ob.keyframe_insert('hide_viewport', frame=q)
        if e >= 0:
            pos, eul, _ = tr[min(e, len(tr) - 1)]
            o.location, o.rotation_euler = pos, eul
        else:
            o.location, o.rotation_euler = (0, 0, -1), (0, 0, 0)
        for ob in [o] + list(o.children):
            ob.hide_render = ob.hide_viewport = e < 0
            ob.keyframe_insert('hide_render', frame=q)
            ob.keyframe_insert('hide_viewport', frame=q)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)
        quentes[i2].default_value = 0.0 if e < 0 else 9.0 * max(0.0, 1 - e / 26) ** 1.6
        quentes[i2].keyframe_insert('default_value', frame=q)
        # fumaça: fiapo atrás da cápsula no voo e fumacinha final saindo da boca parada (com volta do laço)
        for j, f in enumerate(fiapos[i2]):
            vida, nasce = (12, j * 2) if j < N_RASTRO else (24, parou + (j - N_RASTRO) * 5)
            u = None
            for qq in (q, q + QUADROS):
                ee = qq - TIROS[i2] - nasce
                if 0 <= ee <= vida and TIROS[i2] + nasce <= QUADROS + 40:
                    u = ee / vida
                    break
            if u is None:
                f.location, f.scale, f.color = (0, 0, -1), (0.02, 0.02, 0.02), (0, 0, 0, 1)
                f.hide_render = f.hide_viewport = True
            else:
                pb, eb, _ = tr[min(nasce, len(tr) - 1)]
                p0 = boca_mundo(pb, eb)
                if j < N_RASTRO:
                    f.location = p0 + Vector((0.02 * u, -0.01 * u, 0.07 * u))
                    f.scale = (0.02 + 0.04 * u, 0.02 + 0.04 * u, 0.026 + 0.05 * u)
                    d = 1.0 * (1 - u) ** 1.2
                else:
                    f.location = p0 + Vector((0.015 * u, 0.01 * u, 0.012 + 0.2 * u))
                    f.scale = (0.014 + 0.035 * u, 0.014 + 0.035 * u, 0.024 + 0.07 * u)
                    d = 0.7 * math.sin(PI * min(1.0, u * 1.3 + 0.08)) * (1 - u)
                f.color = (d, d, d, 1)
                f.rotation_euler = (j, u * 2, i2)
                f.hide_render = f.hide_viewport = False
            for c in ('location', 'scale', 'color', 'rotation_euler', 'hide_render', 'hide_viewport'):
                f.keyframe_insert(c, frame=q)
    # fumaça de cada tiro: sai da boca, sobe e dilui
    for o, i2, j in fumacas:
        e = q - TIROS[i2] - j * 2
        if 0 <= e <= 26:
            u = e / 26
            Mc = M_canhao(*pose(TIROS[i2]))
            p0 = Mc @ (MUZ + Vector((0.05 + 0.1 * j, 0, 0)))
            dfrente = Mc.to_3x3() @ Vector((1, 0, 0))
            o.location = p0 + dfrente * (0.25 * u + 0.06) + Vector((0.05 * u, 0.04 * u * (1 - 2 * j), 0.6 * u))
            o.scale = (0.05 + 0.16 * u, 0.04 + 0.12 * u, 0.06 + 0.24 * u)
            o.rotation_euler = (i2 + u, j * 2 + u, u * 2)
            o.hide_render = o.hide_viewport = False
        else:
            o.location = (0, 0, 1.6)
            o.scale = (0.05, 0.05, 0.05)
            o.hide_render = o.hide_viewport = True
        for c in ('location', 'scale', 'rotation_euler', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
    # vapor dos respiros da culatra (mais forte depois de atirar)
    Mc = M_canhao(yaw, pitch, 0.0)
    for o, iv, j in vapores:
        u = (j / 2 + fr * 3 + iv * 0.31) % 1.0
        forca = 0.35 + 0.65 * max(quente, g * 0.4)
        o.location = Mc @ VENTS[iv] + Vector((-0.04 * u, 0.02 * u, 0.4 * u))
        o.scale = [max(0.02, (0.03 + 0.1 * u) * forca)] * 3
        o.rotation_euler = (iv, u * 2, j)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)
    # varredor laser: varre o chão; trava no alvo durante a rajada
    trava = suave((q - 30) / 6) * (1 - suave((q - 72) / 6))
    off = (math.radians(-20) + math.radians(26) * math.sin(2 * PI * 3 * fr)) * (1 - trava)
    varredor.rotation_euler = (0, 0, off)
    varredor.keyframe_insert('rotation_euler', frame=q)
    S = Matrix.Rotation(yaw, 4, 'Z') @ (S_VARR + Vector((0.035, 0, 0)))
    ang = yaw + off
    D = 2.1 + 0.25 * math.sin(2 * PI * 5 * fr) * (1 - trava)
    T = Matrix.Rotation(ang, 3, 'Z') @ Vector((D, SY - 0.08, 0.002))
    dv = T - S
    laser.location = S
    laser.rotation_quaternion = dv.to_track_quat('Z', 'Y')
    laser.scale = (0.0035, 0.0035, dv.length)
    ponto.location = T
    ponto.scale = (0.025, 0.025, 1)
    ll.location = T + Vector((0, 0, 0.04))
    for o2, cs in ((laser, ('location', 'rotation_quaternion', 'scale')), (ponto, ('location', 'scale')), (ll, ('location',))):
        for c in cs:
            o2.keyframe_insert(c, frame=q)
    # cápsulas de reserva: esteira → elevador (sobem no visor)
    for k, o in enumerate(capsulas_est):
        u = (k / 3 + fr * 2) % 1.0
        o.location = (BX, -0.95 + 0.17 * u, 0.2 + R_CAP)
        o.rotation_euler = (0, 0, 0)
        o.scale = [1.0 if u < 0.97 else 0.001] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for k, o in enumerate(capsulas_el):
        u = (k / 6 + fr) % 1.0
        o.location = (XV - 0.027, -0.67 + 0.021 * ((k % 2) * 2 - 1), 0.2 + 0.3 * u)
        o.rotation_euler = (0, 0, PI / 2)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)

for o in list(sc.objects) + [luz_b] + [base3d.M[m] for m in ('brilho', 'brasa', 'carga', 'quente0', 'quente1', 'quente2', 'quente3')]:
    ad = getattr(o, 'animation_data', None) or getattr(getattr(o, 'node_tree', None), 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

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
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.05, 0.0, 0.75)
FR_FOTO = TIROS[1]                                                         # segundo tiro: clarão, recuo, fumaça do 1º
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
    sc.frame_set(FR_FOTO)
    for i, (ang, alt) in enumerate(((300, 2.0), (210, 2.2), (120, 2.4), (30, 1.8))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, alt)), ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'torre_defesa_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(TIROS[1] + 6)                                         # recarregando: arco na boca, bobinas acesas
        mirar((1.75, -1.55, 1.75), (0.35, 0.05, 1.12), 34)                 # cabeça, canhão, boca, pistões
        sc.render.filepath = os.path.join(AQUI, 'torre_defesa_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'capsula'):                                       # cápsulas: duas em voo com fiapo, uma quicando
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(62)
        mirar((-2.05, 1.3, 1.45), (-0.5, 0.3, 0.78), 28)
        sc.render.filepath = os.path.join(AQUI, 'torre_defesa_capsula.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(v[7]))
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'torre_defesa_teste.png')
    bpy.ops.render.render(write_still=True)
print('TORRE_DEFESA ok')
