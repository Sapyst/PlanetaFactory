"""Estudo isolado (fora do jogo): ACUMULADOR 2 da IA, 2×2 tiles (lote 13, energia I).
Capacidade nominal: 200 MJ, potência: 1,5 MW.
Evolução tecnológica direta do acumulador básico (80 MJ, 500 kW): banco de fluxo redox de eletrólito líquido
de alta densidade, 4 pilhas bipolares prismáticas reforçadas com tirantes de pressão, circulação forçada
por bomba magnética dupla com radiador aletado, barramentos maciços de cobre, coluna de carga por 12 segmentos de LEDs
e anel toroidal de foco quântico com cristal estabilizador.

Engenharia mecânica e eletroquímica pesada da IA:
- Base de concreto armado 1.92 × 1.92 m chanfrada nos 4 cantos com bacia de contenção de eletrólito e drenos.
- 4 pilhas eletroquímicas (stacks) octogonais em amarelo-industrial desgastado com tirantes tensores em aço inox,
  tampas de grafite com parafusos hexagonais, visores tubulares de recirculação e válvulas de alívio de gás.
- Tanques horizontais cilíndricos na base de anólito e católito em aço escuro com visores graduados de vidro e manômetros.
- Módulo de bombeamento e resfriamento a leste com bomba magnética em bronze e ventilador axial aletado giratório.
- Barramentos laminados de cobre de alta amperagem conectando as 4 pilhas à coluna central.
- Coluna central com núcleo ressonador toroidal e indicador vertical de carga da IA formado por 12 barras de LEDs luminosas
  que acendem progressivamente conforme a energia é acumulada.
- Cristal estabilizador de alta densidade no topo com anel magnético contra-rotativo de focalização harmônica.

Peças animadas separadas:
- 'ventoinha_radiador': ventilador axial de resfriamento do módulo de bombeamento girando continuamente no eixo X.
- 'anel_foco': anel de focalização magnética no cristal superior girando continuamente no eixo Z.
- 'cristal_nucleo': cristal central com pulso harmônico de luminescência e escala sincronizados com o ciclo de carga.
- 'led_barra0'..'led_barra11': 12 segmentos da coluna de medição de carga acendendo progressivamente (carga e descarga).

Uso: blender -b --python estudo_acumulador_2.py -- foto
     blender -b --python estudo_acumulador_2.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(523)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

M = base3d.M
M['concreto'] = mats.material('ConcretoBase', (0.32, 0.31, 0.29), 0.05, 0.90, pintura=False, ferrugem=0.08, sujeira=0.75)
M['aco_escuro'] = mats.material('AcoEscuro', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.45, sujeira=0.60)
M['aco_gasto'] = mats.material('AcoGasto', (0.35, 0.36, 0.37), 0.85, 0.38, pintura=False, ferrugem=0.30, sujeira=0.50)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['aluminio'] = mats.material('AluminioAletas', (0.62, 0.64, 0.65), 0.92, 0.28, pintura=False, ferrugem=0.05, sujeira=0.30)
M['cobre'] = mats.material('CobreBarramentos', (0.75, 0.38, 0.20), 0.92, 0.28, pintura=False, ferrugem=0.05, sujeira=0.35)
M['bronze'] = mats.material('BronzeBomba', (0.55, 0.38, 0.20), 0.90, 0.32, pintura=False, ferrugem=0.12, sujeira=0.30)
M['borracha'] = mats.material('BorrachaDutos', (0.05, 0.05, 0.05), 0.05, 0.85, pintura=False, ferrugem=0.0, sujeira=0.70)
M['ceramica_isolador'] = mats.material('CeramicaIsolador', (0.72, 0.32, 0.15), 0.05, 0.20, pintura=False, ferrugem=0.02, sujeira=0.25)
M['crosta_quimica'] = mats.material('CrostaEletrolito', (0.78, 0.85, 0.72), 0.02, 0.92, pintura=False, ferrugem=0.0, sujeira=0.85)
M['chao'] = mats.material('Chao', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0)
M['listras'] = base3d.listras_mat()

def mat_emissao(nome, cor, forca=5.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*cor, 1.0)
    bsdf.inputs['Emission Color'].default_value = (*cor, 1.0)
    bsdf.inputs['Emission Strength'].default_value = forca
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m

M['cristal_alta_dens'] = mat_emissao('CristalAltaDens', (0.35, 0.10, 0.90), 6.5)
M['led_ativo'] = mat_emissao('LEDAtivo', (0.10, 0.95, 0.45), 7.0)
M['led_apagado'] = mats.material('LEDApagado', (0.08, 0.14, 0.10), 0.10, 0.80, pintura=False)
M['eletrolito_vis'] = mat_emissao('EletrolitoFluido', (0.15, 0.85, 0.65), 3.0)


def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


def toro(bm, centro, R, r, nR=24, nr=8, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        anel_pts = []
        for j in range(nr):
            b = j * 2 * PI / nr
            p = d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))
            anel_pts.append(bm.verts.new(Vector(centro) + rot @ p))
        aneis.append(anel_pts)
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


# ==============================================================================
# 1. BASE DE CONCRETO (1.92 × 1.92 m) COM BACIA DE CONTENÇÃO E DRENOS
# ==============================================================================
bm_con = bmesh.new()
bm_aco = bmesh.new()
bm_crosta = bmesh.new()

# Laje octogonal chanfrada
R_BASE = 0.96
caixa_de(bm_con, Vector((-0.96, -0.72, -0.06)), Vector((+0.96, +0.72, +0.06)))
caixa_de(bm_con, Vector((-0.72, -0.96, -0.06)), Vector((+0.72, +0.96, +0.06)))
for sx, sy in ((-1, -1), (-1, +1), (+1, -1), (+1, +1)):
    p0 = Vector((sx * 0.72, sy * 0.72, -0.06))
    p1 = Vector((sx * 0.96, sy * 0.72, -0.06))
    p2 = Vector((sx * 0.72, sy * 0.96, -0.06))
    p0_t, p1_t, p2_t = p0 + Vector((0, 0, 0.12)), p1 + Vector((0, 0, 0.12)), p2 + Vector((0, 0, 0.12))
    v0, v1, v2 = bm_con.verts.new(p0), bm_con.verts.new(p1), bm_con.verts.new(p2)
    v0t, v1t, v2t = bm_con.verts.new(p0_t), bm_con.verts.new(p1_t), bm_con.verts.new(p2_t)
    if sx * sy > 0:
        bm_con.faces.new([v0, v2, v1])
        bm_con.faces.new([v0t, v1t, v2t])
        bm_con.faces.new([v1, v2, v2t, v1t])
    else:
        bm_con.faces.new([v0, v1, v2])
        bm_con.faces.new([v0t, v2t, v1t])
        bm_con.faces.new([v1, v1t, v2t, v2])

# Borda de contenção de respingos em aço ao redor da laje
caixa_de(bm_aco, Vector((-0.90, -0.90, 0.05)), Vector((-0.84, +0.90, 0.10)))
caixa_de(bm_aco, Vector((+0.84, -0.90, 0.05)), Vector((+0.90, +0.90, 0.10)))
caixa_de(bm_aco, Vector((-0.84, -0.90, 0.05)), Vector((+0.84, -0.84, 0.10)))
caixa_de(bm_aco, Vector((-0.84, +0.84, 0.05)), Vector((+0.84, +0.90, 0.10)))

# Crosta química esbranquiçada / esverdeada de sais de eletrólito próximo aos drenos
mancha(bm_crosta, (-0.45, -0.45), 0.28, 0.062)
mancha(bm_crosta, (+0.40, +0.35), 0.24, 0.062)

# Longarinas em duplo perfil de aço sustentando as 4 pilhas
for sy in (-0.46, +0.46):
    caixa_de(bm_aco, Vector((-0.82, sy - 0.08, 0.06)), Vector((+0.82, sy + 0.08, 0.14)))
    for sx in (-0.75, -0.15, +0.15, +0.75):
        tubo(bm_aco, Vector((sx, sy, 0.06)), Vector((sx, sy, 0.15)), 0.012, 6)  # chumbadores


# ==============================================================================
# 2. QUATRO PILHAS ELETROQUÍMICAS (STACKS) BIPOLARES REFORÇADAS
# ==============================================================================
bm_stacks = bmesh.new()
bm_stacks_aco = bmesh.new()
bm_stacks_cobre = bmesh.new()
bm_stacks_vis = bmesh.new()

# Coordenadas centrais das 4 pilhas nos 4 quadrantes
POS_STACKS = [
    Vector((-0.46, -0.46, 0.14)),  # Sudoeste
    Vector((+0.46, -0.46, 0.14)),  # Sudeste
    Vector((-0.46, +0.46, 0.14)),  # Noroeste
    Vector((+0.46, +0.46, 0.14)),  # Nordeste
]

for idx_stk, pstk in enumerate(POS_STACKS):
    # Corpo prismático octogonal da pilha (altura de z = 0.14 a 0.78 m, apótema 0.26 m)
    Z0, Z1 = pstk.z, pstk.z + 0.64
    AP = 0.26
    # Bloco octogonal em amarelo gasto
    caixa_de(bm_stacks, Vector((pstk.x - AP, pstk.y - AP + 0.06, Z0)), Vector((pstk.x + AP, pstk.y + AP - 0.06, Z1)))
    caixa_de(bm_stacks, Vector((pstk.x - AP + 0.06, pstk.y - AP, Z0)), Vector((pstk.x + AP - 0.06, pstk.y + AP, Z1)))

    # Tampa superior e inferior em grafite usinado escuro
    caixa(bm_stacks_aco, Vector((pstk.x, pstk.y, Z0 + 0.02)), (AP * 2.05, AP * 2.05, 0.04))
    caixa(bm_stacks_aco, Vector((pstk.x, pstk.y, Z1 - 0.02)), (AP * 2.05, AP * 2.05, 0.04))

    # 8 tirantes tensores verticais externos com porcas de alta pressão em aço inox
    for it in range(8):
        at = it * (2 * PI / 8)
        tx = pstk.x + math.cos(at) * (AP + 0.02)
        ty = pstk.y + math.sin(at) * (AP + 0.02)
        tubo(bm_stacks_aco, Vector((tx, ty, Z0)), Vector((tx, ty, Z1)), 0.008, 6)
        # Porcas hexagonais superior e inferior
        tubo(bm_stacks_aco, Vector((tx, ty, Z0 - 0.01)), Vector((tx, ty, Z0 + 0.03)), 0.014, 6)
        tubo(bm_stacks_aco, Vector((tx, ty, Z1 - 0.03)), Vector((tx, ty, Z1 + 0.01)), 0.014, 6)

    # Terminais de polo elétrico em cobre maciço no topo (+ e -)
    p_polo_pos = pstk + Vector((-0.10, -0.10, 0.65))
    p_polo_neg = pstk + Vector((+0.10, +0.10, 0.65))
    tubo(bm_stacks_cobre, p_polo_pos, p_polo_pos + Vector((0, 0, 0.07)), 0.022, 10)
    tubo(bm_stacks_aco, p_polo_neg, p_polo_neg + Vector((0, 0, 0.07)), 0.022, 10)
    # Porcas de aperto do terminal
    caixa(bm_stacks_cobre, p_polo_pos + Vector((0, 0, 0.05)), (0.055, 0.055, 0.025))
    caixa(bm_stacks_aco, p_polo_neg + Vector((0, 0, 0.05)), (0.055, 0.055, 0.025))

    # Válvula de escape e alívio de sobrepressão de gás
    p_valv = pstk + Vector((0.0, 0.0, 0.65))
    tubo(bm_stacks_aco, p_valv, p_valv + Vector((0, 0, 0.09)), 0.016, 8)
    toro(bm_stacks_aco, p_valv + Vector((0, 0, 0.09)), 0.025, 0.006, 12, 4)

    # Visor tubular lateral transparente com eletrólito luminescente verde/ciano
    p_vis0 = pstk + Vector((math.cos(at) * (AP + 0.01), math.sin(at) * (AP + 0.01), 0.22))
    p_vis1 = pstk + Vector((math.cos(at) * (AP + 0.01), math.sin(at) * (AP + 0.01), 0.54))
    tubo(bm_stacks_aco, p_vis0 - Vector((0, 0, 0.02)), p_vis1 + Vector((0, 0, 0.02)), 0.016, 8)
    tubo(bm_stacks_vis, p_vis0, p_vis1, 0.011, 8)


# ==============================================================================
# 3. DOIS TANQUES HORIZONTAIS DE ELETRÓLITO E TUBULAÇÕES DE RECIRCULAÇÃO
# ==============================================================================
bm_tanques = bmesh.new()

# Tanque Sul (Anólito) e Tanque Norte (Católito) sob o vão central das pilhas
for ty in (-0.08, +0.08):
    # Cilindro horizontal ao longo de X (de x = -0.70 a +0.70 m, z = 0.20 m, raio 0.085 m)
    tubo(bm_tanques, Vector((-0.70, ty, 0.20)), Vector((+0.70, ty, 0.20)), 0.085, 16)
    # Tampas convexas nas extremidades
    curva(bm_tanques, Vector((-0.70, ty, 0.20)), 0.085, 12)
    curva(bm_tanques, Vector((+0.70, ty, 0.20)), 0.085, 12)
    # Cintas de reforço do tanque
    for cx in (-0.45, -0.15, +0.15, +0.45):
        tubo(bm_aco, Vector((cx - 0.01, ty, 0.20)), Vector((cx + 0.01, ty, 0.20)), 0.092, 16)
    # Manômetro analógico com visor
    tubo(bm_aco, Vector((-0.68, ty, 0.28)), Vector((-0.68, ty, 0.35)), 0.010, 8)
    tubo(bm_aco, Vector((-0.68, ty, 0.35)), Vector((-0.66, ty, 0.35)), 0.025, 12)

# Tubulações de recirculação conectando os tanques às 4 pilhas
for pstk in POS_STACKS:
    pts_tubo = [
        Vector((pstk.x, 0.0, 0.20)),
        Vector((pstk.x, pstk.y * 0.5, 0.20)),
        Vector((pstk.x, pstk.y * 0.75, 0.25))
    ]
    mangueira(bm_stacks_aco, pts_tubo, 0.018)


# ==============================================================================
# 4. MÓDULO DE BOMBEAMENTO DUPLO E RADIADOR ALETADO (Leste: x = +0.75 a +0.92)
# ==============================================================================
bm_bomba = bmesh.new()
bm_radiador = bmesh.new()
bm_ventoinha = bmesh.new()

X_BOMBA = 0.80
# Carcaça da bomba magnética hermética dupla em bronze naval
caixa(bm_bomba, Vector((X_BOMBA, 0.0, 0.22)), (0.16, 0.32, 0.18))
tubo(bm_bomba, Vector((X_BOMBA - 0.08, -0.08, 0.22)), Vector((X_BOMBA + 0.08, -0.08, 0.22)), 0.055, 12)
tubo(bm_bomba, Vector((X_BOMBA - 0.08, +0.08, 0.22)), Vector((X_BOMBA + 0.08, +0.08, 0.22)), 0.055, 12)

# Radiador de arrefecimento líquido em alumínio aletado
caixa(bm_radiador, Vector((X_BOMBA + 0.05, 0.0, 0.44)), (0.08, 0.34, 0.24))
for irad in range(10):
    ry = -0.14 + irad * 0.031
    caixa(bm_radiador, Vector((X_BOMBA + 0.095, ry, 0.44)), (0.015, 0.008, 0.22))

# Coifa cilíndrica da ventoinha de resfriamento (eixo em X)
tubo(bm_radiador, Vector((X_BOMBA + 0.09, 0.0, 0.44)), Vector((X_BOMBA + 0.13, 0.0, 0.44)), 0.125, 18)
# Grade de proteção circular em arame
toro(bm_aco, Vector((X_BOMBA + 0.13, 0.0, 0.44)), 0.12, 0.005, 18, 4, Matrix.Rotation(PI/2, 3, 'Y'))

# Ventoinha axial de 4 pás (objeto 'ventoinha_radiador', centrada na origem local)
tubo(bm_ventoinha, Vector((-0.02, 0, 0)), Vector((+0.02, 0, 0)), 0.032, 10)
for ipa in range(4):
    apa = ipa * (PI / 2)
    rot_pa = Matrix.Rotation(apa, 3, 'X')
    py = math.cos(apa) * 0.065
    pz = math.sin(apa) * 0.065
    caixa(bm_ventoinha, Vector((0.0, py, pz)), (0.006, 0.055, 0.028), rot_pa @ Matrix.Rotation(math.radians(35), 3, 'Y'))


# ==============================================================================
# 5. BARRAMENTOS MACIÇOS DE COBRE E COLUNA CENTRAL DE CARGA
# ==============================================================================
bm_coluna = bmesh.new()
bm_coluna_cobre = bmesh.new()

# Coluna central cilíndrica (x = 0, y = 0, z = 0.10 a 0.95 m)
tubo(bm_coluna, Vector((0, 0, 0.10)), Vector((0, 0, 0.92)), 0.16, 20)
# Anéis toroidais concêntricos de indução eletrostática
for z_ind in (0.35, 0.55, 0.75):
    toro(bm_coluna_cobre, Vector((0, 0, z_ind)), 0.175, 0.015, 20, 6)

# 4 barramentos laminados de cobre espesso conectando os polos + das pilhas à coluna
for pstk in POS_STACKS:
    p_orig = pstk + Vector((-0.10 if pstk.x < 0 else +0.10, -0.10 if pstk.y < 0 else +0.10, 0.72))
    p_inter = Vector((pstk.x * 0.45, pstk.y * 0.45, 0.78))
    p_dest = Vector((math.copysign(0.16, pstk.x), math.copysign(0.16, pstk.y), 0.85))
    pts_barr = [p_orig, p_inter, p_dest]
    mangueira(bm_coluna_cobre, pts_barr, 0.018)

# Prato emissor superior com 4 garras de suporte em bronze (z = 0.92 a 1.05 m)
caixa(bm_coluna, Vector((0, 0, 0.93)), (0.34, 0.34, 0.03))
tubo(bm_coluna_cobre, Vector((0, 0, 0.94)), Vector((0, 0, 0.97)), 0.12, 16)
for ig in range(4):
    ag = ig * (PI / 2) + PI / 4
    gx = math.cos(ag) * 0.14
    gy = math.sin(ag) * 0.14
    tubo(bm_coluna, Vector((gx, gy, 0.94)), Vector((gx, gy, 1.04)), 0.012, 8)
    tubo(bm_coluna, Vector((gx, gy, 1.04)), Vector((gx * 0.45, gy * 0.45, 1.08)), 0.010, 8)


# ==============================================================================
# 6. FENÔMENO QUÂNTICO: CRISTAL ESTABILIZADOR E ANEL DE FOCO MAGNÉTICO
# ==============================================================================
bm_cristal = bmesh.new()
bm_anel_foco = bmesh.new()

P_CRIST_CTR = Vector((0.0, 0.0, 1.10))

# Cristal estabilizador de alta densidade (objeto 'cristal_nucleo', centrado na origem)
# Bipirâmide octogonal facetada
cr_pts = [
    Vector((0, 0, +0.11)),
    Vector((0, 0, -0.11)),
]
for ko in range(8):
    ako = ko * (2 * PI / 8)
    cr_pts.append(Vector((math.cos(ako) * 0.055, math.sin(ako) * 0.055, 0.0)))
v_cro = [bm_cristal.verts.new(p) for p in cr_pts]
for ko in range(8):
    ko_prox = (ko + 1) % 8
    bm_cristal.faces.new([v_cro[0], v_cro[2 + ko], v_cro[2 + ko_prox]])
    bm_cristal.faces.new([v_cro[1], v_cro[2 + ko_prox], v_cro[2 + ko]])

# Anel magnético contra-rotativo de foco quântico (objeto 'anel_foco', centrado na origem)
toro(bm_anel_foco, Vector((0, 0, 0)), 0.14, 0.012, 24, 8)
# 4 bobinas concentradoras no anel
for ic in range(4):
    aic = ic * (PI / 2)
    cx = math.cos(aic) * 0.14
    cy = math.sin(aic) * 0.14
    tubo(bm_coluna_cobre, Vector((cx, cy, -0.015)), Vector((cx, cy, +0.015)), 0.022, 10)


# ==============================================================================
# 7. COLUNA DE MEDIÇÃO DE CARGA: 12 BARRAS DE LEDS LUMINOSOS
# ==============================================================================
# Localizada na face sul da coluna central (y = -0.165, de z = 0.28 a 0.83 m)
# Cada LED é um objeto separado 'led_barra0'..'led_barra11' para animação precisa
bm_moldura_led = bmesh.new()
caixa(bm_moldura_led, Vector((0.0, -0.170, 0.55)), (0.09, 0.02, 0.60))

bms_leds = []
POS_LEDS = []
for i_led in range(12):
    bm_l = bmesh.new()
    z_led = 0.28 + i_led * 0.046
    caixa(bm_l, Vector((0.0, 0.0, 0.0)), (0.065, 0.010, 0.028))
    bms_leds.append(bm_l)
    POS_LEDS.append(Vector((0.0, -0.178, z_led)))


# ==============================================================================
# 8. INSTANCIAÇÃO DOS OBJETOS BLENDER E HIERARQUIA
# ==============================================================================
# Base e Estruturas
o_base = obj('base_concreto', bm_con, 'concreto')
o_base_aco = obj('base_longarinas', bm_aco, 'aco_escuro')
o_base_aco.parent = o_base
o_crosta = obj('base_crosta', bm_crosta, 'crosta_quimica')
o_crosta.parent = o_base

# Pilhas Eletroquímicas
o_stacks = obj('stacks_corpo', bm_stacks, 'chassi_amarelo')
o_stacks.parent = o_base
o_stacks_aco = obj('stacks_tirantes', bm_stacks_aco, 'aco_gasto')
o_stacks_aco.parent = o_base
o_stacks_cob = obj('stacks_terminais', bm_stacks_cobre, 'cobre')
o_stacks_cob.parent = o_base
o_stacks_vis = obj('stacks_visores', bm_stacks_vis, 'eletrolito_vis')
o_stacks_vis.parent = o_base

# Tanques e Bomba
o_tanques = obj('tanques_eletrolito', bm_tanques, 'aco_escuro')
o_tanques.parent = o_base
o_bomba = obj('bomba_recirculacao', bm_bomba, 'bronze')
o_bomba.parent = o_base
o_radiador = obj('radiador_bomba', bm_radiador, 'aluminio')
o_radiador.parent = o_base

# Ventoinha da Bomba ('ventoinha_radiador')
P_VENT_CTR = Vector((X_BOMBA + 0.11, 0.0, 0.44))
o_vent = obj('ventoinha_radiador', bm_ventoinha, 'aluminio')
o_vent.location = P_VENT_CTR
o_vent.parent = o_base

# Coluna Central e Barramentos
o_coluna = obj('coluna_central', bm_coluna, 'chassi_amarelo')
o_coluna.parent = o_base
o_col_cob = obj('coluna_barramentos', bm_coluna_cobre, 'cobre')
o_col_cob.parent = o_base
o_mold_led = obj('moldura_leds', bm_moldura_led, 'aco_escuro')
o_mold_led.parent = o_base

# Cristal Estabilizador e Anel de Foco
o_cristal = obj('cristal_nucleo', bm_cristal, 'cristal_alta_dens')
o_cristal.location = P_CRIST_CTR
o_cristal.parent = o_base

o_anel_foco = obj('anel_foco', bm_anel_foco, 'aco_gasto')
o_anel_foco.location = P_CRIST_CTR
o_anel_foco.parent = o_base

# 12 Barras de LED da Coluna de Carga
objs_leds = []
for i_led in range(12):
    o_ld = obj('led_barra%d' % i_led, bms_leds[i_led], 'led_ativo')
    o_ld.location = POS_LEDS[i_led]
    o_ld.parent = o_base
    objs_leds.append(o_ld)

# Suavizações
for o in (o_base, o_stacks, o_tanques, o_bomba, o_radiador, o_vent, o_coluna, o_cristal, o_anel_foco):
    suavizar(o)


# ==============================================================================
# 9. ANIMAÇÕES EM LAÇO FECHADO DE 96 QUADROS (24 FPS, 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)
    t = (f - 1) / QUADROS  # 0.0 a 95/96
    ang_ciclo = t * 2 * PI

    # 1. Rotação Contínua da Ventoinha de Resfriamento da Bomba (6 voltas em 96 quadros no eixo X)
    o_vent.rotation_euler = Euler((ang_ciclo * 6.0, 0.0, 0.0), 'XYZ')
    o_vent.keyframe_insert('rotation_euler', frame=f)

    # 2. Rotação Contínua do Anel de Foco Magnético (2 voltas em 96 quadros no eixo Z)
    o_anel_foco.rotation_euler = Euler((0.0, 0.0, -ang_ciclo * 2.0), 'XYZ')
    o_anel_foco.keyframe_insert('rotation_euler', frame=f)

    # 3. Pulso e Respiração de Carga do Cristal Estabilizador
    # Durante a carga (frames 1 a 48), energia sobe; durante a descarga (frames 49 a 96), energia desce
    curva_carga = 0.5 - 0.5 * math.cos(ang_ciclo)  # 0.0 no frame 1, 1.0 no frame 49, 0.0 no frame 97
    s_cristal = 1.0 + 0.15 * curva_carga + 0.04 * math.sin(ang_ciclo * 4.0)
    o_cristal.scale = Vector((s_cristal, s_cristal, s_cristal))
    o_cristal.keyframe_insert('scale', frame=f)

    # 4. Coluna de 12 LEDs de Carga (Escala Progressiva que acende conforme curva_carga)
    # Nível de carga de 2 a 12 barras acesas
    barras_ativas = 2.0 + curva_carga * 10.0
    for i_led in range(12):
        o_ld = objs_leds[i_led]
        if i_led < barras_ativas:
            # Segmento aceso
            o_ld.scale = Vector((1.0, 1.0, 1.0))
        else:
            # Segmento apagado / recolhido
            o_ld.scale = Vector((0.05, 0.05, 0.05))
        o_ld.keyframe_insert('scale', frame=f)


# ==============================================================================
# 10. ILUMINAÇÃO, CHÃO E CÂMERAS CYCLES
# ==============================================================================
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (14, 14, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.5
sol_d.color = (1.0, 0.98, 0.94)
sol_d.angle = math.radians(12.0)
o_sol = bpy.data.objects.new('EFEITO_Sol', sol_d)
sc.collection.objects.link(o_sol)
o_sol.rotation_euler = (math.radians(52), 0, math.radians(-38))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.58, 0.65, 0.78, 1.0)
bg.inputs['Strength'].default_value = 0.60

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

cam_d = bpy.data.cameras.new('Camera')
cam_d.lens = 38
cam_d.clip_start = 0.1
cam_d.clip_end = 100.0
cam = bpy.data.objects.new('EFEITO_Camera', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente=36):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = Vector((0.0, 0.0, 0.62))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(45)  # Quadro próximo do pico de carga (11 barras acesas e cristal brilhante)

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.2), (210, 2.4), (120, 2.3), (30, 2.1))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'acumulador_2_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: coluna de LEDs acesa, barramentos de cobre, cristal estabilizador e pilhas
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(45)
        mirar(Vector((0.0, -1.85, 1.15)), Vector((0.0, -0.10, 0.65)), 35)
        sc.render.filepath = os.path.join(AQUI, 'acumulador_2_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(45)
    mirar(ALVO + Vector((2.6, -3.0, 1.4)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'acumulador_2_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('ACUMULADOR_2 ok (%d tris)' % tot_tri)
