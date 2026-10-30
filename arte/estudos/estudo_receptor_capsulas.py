"""Estudo isolado (fora do jogo): RECEPTOR DE CÁPSULAS da IA, 2×2 tiles (lote 17, proliferação).
Saída de itens ao norte (ITEM_SAI_N0, borda norte y = +0,95 m, altura z = 0,23 m).
Função: Estação industrial pesada de captura balística e desaceleração de cápsulas coloniais.
Equipada com funil de amortecimento magnético profundo, 4 garras pneumáticas/hidráulicas articuladas
com sapatas de retenção acionadas por pistões, unidade de potência hidráulica (HPU) com acumulador,
mastro de telemetria com antena e estrobo, e rampa de descarte norte com roletes de esteira e cortina de borracha.

Peças animadas separadas:
- 'garra0', 'garra1', 'garra2', 'garra3': braços articulados de frenagem com amortecedores.
- 'haste0', 'haste1', 'haste2', 'haste3': hastes cromadas dos pistões acompanhando as garras.
- 'empurrador': pistão ejetor na base do funil que empurra o núcleo da cápsula para a esteira norte.
- 'rolete0'..'rolete4': roletes da esteira de saída girando ao transportar o núcleo.
- 'nucleo_capsula': canister recuperado com cristal gênese deslizando na esteira.
- 'capsula_chegada': cápsula balística que desce, freia nos anéis de indução e é retida pelas garras.

Uso: blender -b --python estudo_receptor_capsulas.py -- foto
     blender -b --python estudo_receptor_capsulas.py -- nada
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
random.seed(155)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades de modelagem
def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


def curva_cotovelo(bm, p, r, lados=12):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=6, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano_rigido(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 12)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.08:
            for c in (a + u * 0.03, b - u * 0.03):
                tubo(bf, c - u * 0.005, c + u * 0.005, r * 1.5, 12)
    for c in pts[1:-1]:
        curva_cotovelo(bm, c, r, 12)


def toro(bm, centro, R, r, nR=24, nr=6, rot=Matrix.Identity(3)):
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = rot @ Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + rot @ Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def prisma_octo(bm, c, ap, z0, z1):
    rv = ap / math.cos(PI / 8)
    vs = []
    for z in (z0, z1):
        vs.append([bm.verts.new((c[0] + rv * math.cos(PI / 8 + k * PI / 4),
                                 c[1] + rv * math.sin(PI / 8 + k * PI / 4), z))
                   for k in range(8)])
    bm.faces.new(list(reversed(vs[0])))
    bm.faces.new(vs[1])
    for k in range(8):
        bm.faces.new((vs[0][k], vs[0][(k + 1) % 8], vs[1][(k + 1) % 8], vs[1][k]))


def hexa_cristal(bm, c, r, h, ponta_sup=0.0, ponta_inf=0.0):
    c = Vector(c)
    z0, z1 = c.z - h / 2, c.z + h / 2
    vs0 = [bm.verts.new((c.x + r * math.cos(k * PI / 3), c.y + r * math.sin(k * PI / 3), z0)) for k in range(6)]
    vs1 = [bm.verts.new((c.x + r * math.cos(k * PI / 3), c.y + r * math.sin(k * PI / 3), z1)) for k in range(6)]
    if ponta_inf > 0:
        vp0 = bm.verts.new((c.x, c.y, z0 - ponta_inf))
        for k in range(6):
            bm.faces.new((vs0[(k + 1) % 6], vs0[k], vp0))
    else:
        bm.faces.new(list(reversed(vs0)))
    if ponta_sup > 0:
        vp1 = bm.verts.new((c.x, c.y, z1 + ponta_sup))
        for k in range(6):
            bm.faces.new((vs1[k], vs1[(k + 1) % 6], vp1))
    else:
        bm.faces.new(vs1)
    for k in range(6):
        bm.faces.new((vs0[k], vs0[(k + 1) % 6], vs1[(k + 1) % 6], vs1[k]))


# ------------------------------------------------------------------ MATERIAIS
M = base3d.M
M['concreto'] = mats.material('Concreto', (0.34, 0.33, 0.31), 0.05, 0.90, pintura=False, ferrugem=0.08, sujeira=0.75)
M['aco_escuro'] = mats.material('AcoEscuro', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.45, sujeira=0.60)
M['aco_gasto'] = mats.material('AcoGasto', (0.35, 0.36, 0.37), 0.85, 0.38, pintura=False, ferrugem=0.30, sujeira=0.50)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['remendo_primer'] = mats.material('RemendoPrimer', (0.42, 0.16, 0.12), 0.10, 0.65, pintura=True, ferrugem=0.20, sujeira=0.40)
M['cobre'] = mats.material('CobreIndutivo', (0.75, 0.38, 0.20), 0.92, 0.30, pintura=False, ferrugem=0.05, sujeira=0.40)
M['borracha'] = mats.material('BorrachaAmortecedor', (0.05, 0.05, 0.05), 0.05, 0.85, pintura=False, ferrugem=0.0, sujeira=0.70)
M['cromo'] = mats.material('CromoPistao', (0.85, 0.85, 0.85), 0.96, 0.12, pintura=False, ferrugem=0.02, sujeira=0.15)
M['listras'] = base3d.listras_mat()
M['oleo'] = mats.material('OleoSujeira', (0.02, 0.02, 0.01), 0.20, 0.15, pintura=False, ferrugem=0.0, sujeira=0.95)
M['chao'] = mats.material('Chao', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0)

# Emissões
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

M['bobina_inducao'] = mat_emissao('BobinaInducao', (0.15, 0.65, 1.0), 3.5)
M['cristal_nucleo'] = mat_emissao('CristalNucleo', (0.1, 0.95, 0.4), 6.0)
M['estrobo'] = mat_emissao('EstroboAproximacao', (1.0, 0.9, 0.3), 8.0)

# ==============================================================================
# 1. BASE DE CONCRETO CHANFRADA, CALHAS, SAPATAS E BORDAS DE SEGURANÇA
# ==============================================================================
bm_con = bmesh.new()
bm_aco = bmesh.new()
bm_lis = bmesh.new()
bm_bor = bmesh.new()

# Laje 1.92 × 1.92 m, cantos chanfrados em 45°
R_EXT = 0.96
L_CHANFRO = 0.35
vs_laje = [
    Vector((-R_EXT + L_CHANFRO, -R_EXT, 0.0)),
    Vector((R_EXT - L_CHANFRO, -R_EXT, 0.0)),
    Vector((R_EXT, -R_EXT + L_CHANFRO, 0.0)),
    Vector((R_EXT, R_EXT - L_CHANFRO, 0.0)),
    Vector((R_EXT - L_CHANFRO, R_EXT, 0.0)),
    Vector((-R_EXT + L_CHANFRO, R_EXT, 0.0)),
    Vector((-R_EXT, R_EXT - L_CHANFRO, 0.0)),
    Vector((-R_EXT, -R_EXT + L_CHANFRO, 0.0)),
]
H_LAJE = 0.12
v_inf = [bm_con.verts.new(v) for v in vs_laje]
v_sup = [bm_con.verts.new(v + Vector((0, 0, H_LAJE))) for v in vs_laje]
bm_con.faces.new(list(reversed(v_inf)))
bm_con.faces.new(v_sup)
for k in range(8):
    bm_con.faces.new((v_inf[k], v_inf[(k + 1) % 8], v_sup[(k + 1) % 8], v_sup[k]))

# Rodapés com listras de perigo nos cantos chanfrados
for k in (0, 2, 4, 6):
    p0 = vs_laje[(k + 1) % 8]
    p1 = vs_laje[(k + 2) % 8]
    meio = (p0 + p1) * 0.5 + Vector((0, 0, H_LAJE * 0.5))
    norm = Vector((p1.y - p0.y, -(p1.x - p0.x), 0)).normalized()
    comp = (p1 - p0).length
    ang = math.atan2(p1.y - p0.y, p1.x - p0.x)
    caixa(bm_lis, meio + norm * 0.012, (comp * 0.95, 0.02, H_LAJE * 0.8), rot=Matrix.Rotation(ang, 3, 'Z'))

# 4 sapatas de aço nos cantos retos com tirantes chumbados no concreto
for cx, cy in ((-0.82, -0.82), (0.82, -0.82), (-0.82, 0.82), (0.82, 0.82)):
    caixa(bm_aco, (cx, cy, H_LAJE + 0.015), (0.16, 0.16, 0.03))
    for bx, by in ((-0.05, -0.05), (0.05, -0.05), (-0.05, 0.05), (0.05, 0.05)):
        tubo(bm_aco, (cx + bx, cy + by, H_LAJE + 0.015), (cx + bx, cy + by, H_LAJE + 0.05), 0.012, 6)

# ==============================================================================
# 2. BLINDAGEM OCTOGONAL INFERIOR COM NERVURAS, ESCOTILHA E REMENDOS
# ==============================================================================
# Corpo octogonal principal (z = 0.12 a 0.72 m)
prisma_octo(bm_con, (0, 0), 0.80, H_LAJE, 0.72)

# Chassi reforçado de aço em volta do octógono
bm_cha = bmesh.new()
prisma_octo(bm_cha, (0, 0), 0.82, H_LAJE + 0.02, 0.70)

# Nervuras verticais de reforço em cada um dos 8 vértices
R_V = 0.82 / math.cos(PI / 8)
for k in range(8):
    ang = PI / 8 + k * PI / 4
    dx, dy = math.cos(ang), math.sin(ang)
    p_inf = Vector((dx * (R_V + 0.04), dy * (R_V + 0.04), H_LAJE))
    p_sup = Vector((dx * (R_V + 0.01), dy * (R_V + 0.01), 0.72))
    viga(bm_aco, p_inf, p_sup, 0.035)

# Escotilha de inspeção frontal (Sul, y < 0) com dobradiças e trincos manuais
caixa(bm_aco, (0.0, -0.83, 0.42), (0.36, 0.03, 0.28))
tubo(bm_aco, (-0.16, -0.84, 0.54), (-0.16, -0.84, 0.30), 0.012, 8)  # dobradiça
caixa(bm_aco, (0.15, -0.85, 0.42), (0.04, 0.02, 0.08))               # trinco

# Chapa trocada em primer vermelho com 6 parafusos aparentes (sudoeste)
bm_rem = bmesh.new()
ang_rem = -3 * PI / 4
p_rem = Vector((math.cos(ang_rem) * 0.825, math.sin(ang_rem) * 0.825, 0.45))
caixa(bm_rem, p_rem, (0.28, 0.015, 0.22), rot=Matrix.Rotation(ang_rem + PI / 2, 3, 'Z'))
for dx_p in (-0.11, 0.0, 0.11):
    for dz_p in (-0.08, 0.08):
        pos_b = p_rem + Vector((math.cos(ang_rem + PI / 2) * dx_p, math.sin(ang_rem + PI / 2) * dx_p, dz_p))
        tubo(bm_aco, pos_b, pos_b + Vector((math.cos(ang_rem) * 0.02, math.sin(ang_rem) * 0.02, 0)), 0.008, 6)

# ==============================================================================
# 3. UNIDADE HIDRÁULICA (HPU) E ACUMULADOR DE PRESSÃO (OESTE)
# ==============================================================================
# Berço de vigas soldadas a oeste (x ~ -0.68, y ~ 0.0)
caixa(bm_aco, (-0.68, 0.0, H_LAJE + 0.04), (0.28, 0.52, 0.04))
# Motor elétrico trifásico aletado
tubo(bm_aco, (-0.68, -0.14, H_LAJE + 0.16), (-0.68, 0.02, H_LAJE + 0.16), 0.08, 16)
for ia in range(6):
    ang_al = ia * PI / 6
    dx_al, dz_al = math.cos(ang_al) * 0.085, math.sin(ang_al) * 0.085
    caixa(bm_aco, (-0.68 + dx_al, -0.06, H_LAJE + 0.16 + dz_al), (0.015, 0.16, 0.02))

# Acumulador hidráulico esférico (pressão de nitrogênio)
bmesh.ops.create_uvsphere(bm_cha, u_segments=16, v_segments=10, radius=0.09,
                          matrix=Matrix.Translation(Vector((-0.68, 0.16, H_LAJE + 0.17))))
tubo(bm_aco, (-0.68, 0.16, H_LAJE + 0.05), (-0.68, 0.16, H_LAJE + 0.10), 0.025, 10)

# Manômetro de glicerina com mostrador em latão
tubo(bm_aco, (-0.68, 0.16, H_LAJE + 0.28), (-0.68, 0.16, H_LAJE + 0.32), 0.035, 12)
tubo(bm_aco, (-0.68, 0.16, H_LAJE + 0.25), (-0.68, 0.16, H_LAJE + 0.28), 0.01, 8)

# Distribuidor de pressão e tubulações rígidas de alta pressão
caixa(bm_aco, (-0.56, 0.0, H_LAJE + 0.18), (0.08, 0.18, 0.08))
cano_rigido(bm_aco, bm_aco, [(-0.68, 0.08, H_LAJE + 0.16), (-0.56, 0.08, H_LAJE + 0.16)], 0.015)
cano_rigido(bm_aco, bm_aco, [(-0.56, -0.05, H_LAJE + 0.18), (-0.45, -0.05, 0.55), (-0.38, -0.15, 0.85)], 0.012)
cano_rigido(bm_aco, bm_aco, [(-0.56, 0.05, H_LAJE + 0.18), (-0.45, 0.05, 0.55), (-0.38, 0.15, 0.85)], 0.012)

# ==============================================================================
# 4. TORRE DE TELEMETRIA E FAROL ESTROBOSCÓPICO (SUDESTE)
# ==============================================================================
Z_TOPO_TORRE = 1.85
p_base_t = Vector((0.68, -0.68, H_LAJE))
for dx_t, dy_t in ((-0.06, -0.06), (0.06, -0.06), (-0.06, 0.06), (0.06, 0.06)):
    p_b = p_base_t + Vector((dx_t, dy_t, 0))
    p_t = p_base_t + Vector((dx_t * 0.4, dy_t * 0.4, Z_TOPO_TORRE - H_LAJE))
    tubo(bm_aco, p_b, p_t, 0.010, 8)

# Travessas da torre
for iz in range(5):
    zt = H_LAJE + 0.25 + iz * 0.28
    caixa(bm_aco, (0.68, -0.68, zt), (0.11 - iz * 0.012, 0.11 - iz * 0.012, 0.015))

# Antena parabólica de recepção
bm_ant = bmesh.new()
pos_ant = p_base_t + Vector((-0.02, 0.02, Z_TOPO_TORRE - H_LAJE - 0.10))
bmesh.ops.create_uvsphere(bm_ant, u_segments=16, v_segments=8, radius=0.12,
                          matrix=Matrix.Translation(pos_ant) @ Matrix.Rotation(PI / 4, 4, 'Z') @ Matrix.Rotation(-PI / 6, 4, 'Y'))
tubo(bm_aco, pos_ant, pos_ant + Vector((-0.08, 0.08, 0.05)), 0.008, 6)

# Farol estroboscópico de alinhamento balístico no topo da torre
caixa(bm_aco, (0.68, -0.68, Z_TOPO_TORRE + 0.02), (0.08, 0.08, 0.04))
tubo(bm_aco, (0.68, -0.68, Z_TOPO_TORRE + 0.04), (0.68, -0.68, Z_TOPO_TORRE + 0.12), 0.03, 12)

# ==============================================================================
# 5. FUNIL DE CAPTURA BALÍSTICA E ANÉIS DE DESACELERAÇÃO INDUTIVA
# ==============================================================================
Z_BASE_FUNIL = 0.72
Z_TOPO_FUNIL = 1.38
R_EXT_TOPO = 0.74
R_INT_TOPO = 0.64
R_EXT_BASE = 0.52
R_INT_BASE = 0.38
LADOS_F = 16

bm_fun = bmesh.new()
v_ext_b = [bm_fun.verts.new((R_EXT_BASE * math.cos(k * 2 * PI / LADOS_F), R_EXT_BASE * math.sin(k * 2 * PI / LADOS_F), Z_BASE_FUNIL)) for k in range(LADOS_F)]
v_ext_t = [bm_fun.verts.new((R_EXT_TOPO * math.cos(k * 2 * PI / LADOS_F), R_EXT_TOPO * math.sin(k * 2 * PI / LADOS_F), Z_TOPO_FUNIL)) for k in range(LADOS_F)]
v_int_t = [bm_fun.verts.new((R_INT_TOPO * math.cos(k * 2 * PI / LADOS_F), R_INT_TOPO * math.sin(k * 2 * PI / LADOS_F), Z_TOPO_FUNIL)) for k in range(LADOS_F)]
v_int_b = [bm_fun.verts.new((R_INT_BASE * math.cos(k * 2 * PI / LADOS_F), R_INT_BASE * math.sin(k * 2 * PI / LADOS_F), Z_BASE_FUNIL - 0.25)) for k in range(LADOS_F)]

for k in range(LADOS_F):
    k1 = (k + 1) % LADOS_F
    # Casca externa
    bm_fun.faces.new((v_ext_b[k], v_ext_b[k1], v_ext_t[k1], v_ext_t[k]))
    # Borda superior chanfrada de choque
    bm_fun.faces.new((v_ext_t[k], v_ext_t[k1], v_int_t[k1], v_int_t[k]))
    # Casca interna do cone receptor
    bm_fun.faces.new((v_int_t[k], v_int_t[k1], v_int_b[k1], v_int_b[k]))

# Fundo do poço
v_fundo = [bm_fun.verts.new((R_INT_BASE * 0.85 * math.cos(k * 2 * PI / LADOS_F), R_INT_BASE * 0.85 * math.sin(k * 2 * PI / LADOS_F), Z_BASE_FUNIL - 0.35)) for k in range(LADOS_F)]
for k in range(LADOS_F):
    k1 = (k + 1) % LADOS_F
    bm_fun.faces.new((v_int_b[k], v_int_b[k1], v_fundo[k1], v_fundo[k]))
bm_fun.faces.new(list(reversed(v_fundo)))

# Anel de reforço usinado no topo com olhais de içamento
bm_aneis = bmesh.new()
toro(bm_aneis, (0, 0, Z_TOPO_FUNIL), R_EXT_TOPO, 0.028, nR=24, nr=6)

# Anéis magnéticos indutivos de cobre nos níveis intermediários
bm_cobre = bmesh.new()
toro(bm_cobre, (0, 0, 1.22), 0.70, 0.032, nR=24, nr=6)
toro(bm_cobre, (0, 0, 1.05), 0.63, 0.035, nR=24, nr=6)
toro(bm_cobre, (0, 0, 0.88), 0.56, 0.038, nR=24, nr=6)

# Barras condutoras radiais e aletas térmicas ao redor dos anéis de cobre
for ia in range(12):
    ang = ia * PI / 6
    dx, dy = math.cos(ang), math.sin(ang)
    caixa(bm_cobre, (dx * 0.74, dy * 0.74, 1.05), (0.08, 0.02, 0.38), rot=Matrix.Rotation(ang, 3, 'Z'))

# Conectores dos cabos de alimentação de alta corrente
for ang_c in (-PI / 3, PI / 3, -2 * PI / 3):
    px, py = math.cos(ang_c) * 0.78, math.sin(ang_c) * 0.78
    caixa(bm_aco, (px, py, 1.05), (0.08, 0.08, 0.22))
    mangueira(bm_aco, [Vector((px, py, 0.95)), Vector((px * 1.05, py * 1.05, 0.65)), Vector((px * 0.95, py * 0.95, 0.45))], 0.016)

# ==============================================================================
# 6. ESTEIRA DE SAÍDA NORTE (ITEM_SAI_N0: y = +0,95 m, z = 0,23 m)
# ==============================================================================
# Túnel de saída na blindagem norte
caixa(bm_aco, (0.0, 0.68, 0.35), (0.44, 0.30, 0.30))
# Cortina de borracha fatiada contra poeira e detritos na boca
for ib in range(5):
    caixa(bm_bor, (0.0 - 0.16 + ib * 0.08, 0.78, 0.34), (0.075, 0.01, 0.24))

# Chassi da mesa de roletes (borda norte y = 0.95)
caixa(bm_cha, (-0.23, 0.85, 0.23), (0.04, 0.26, 0.12))
caixa(bm_cha, (0.23, 0.85, 0.23), (0.04, 0.26, 0.12))
# Listras de aviso nas bordas da guia norte
caixa(bm_lis, (-0.25, 0.85, 0.26), (0.01, 0.24, 0.06))
caixa(bm_lis, (0.25, 0.85, 0.26), (0.01, 0.24, 0.06))

# ==============================================================================
# CRIAÇÃO DOS OBJETOS ESTÁTICOS
# ==============================================================================
o_con = obj('base_concreto', bm_con, 'concreto')
suavizar(o_con)

o_aco = obj('detalhes_aco', bm_aco, 'aco_gasto')
suavizar(o_aco)

o_cha = obj('chassi_amarelo', bm_cha, 'chassi_amarelo')
suavizar(o_cha)

o_rem = obj('remendo_primer', bm_rem, 'remendo_primer')

o_lis = obj('listras_aviso', bm_lis, 'listras')

o_bor = obj('cortina_borracha', bm_bor, 'borracha')

o_fun = obj('funil_captura', bm_fun, 'aco_escuro')
suavizar(o_fun)

o_cob = obj('bobinas_cobre', bm_cobre, 'cobre')
suavizar(o_cob)

o_ane = obj('reforcos_anel', bm_aneis, 'aco_gasto')
suavizar(o_ane)

o_ant = obj('antena_telemetria', bm_ant, 'aco_gasto')
suavizar(o_ant)

# Mancha de óleo hidráulico sob o bloco de válvulas (Oeste)
bm_oleo = bmesh.new()
mancha(bm_oleo, (-0.68, 0.0), 0.22, H_LAJE + 0.001)
o_ole = obj('corpo_oleo', bm_oleo, 'oleo')

# Estrobo luminoso no topo da torre de telemetria
bm_est = bmesh.new()
tubo(bm_est, (0.68, -0.68, Z_TOPO_TORRE + 0.07), (0.68, -0.68, Z_TOPO_TORRE + 0.11), 0.024, 10)
o_est = obj('lampada_estrobo', bm_est, 'estrobo')

# Luz pontual do estrobo
luz_est = bpy.data.lights.new('LuzEstrobo', 'POINT')
luz_est.color = (1.0, 0.92, 0.4)
luz_est.energy = 0.0
o_luz_est = bpy.data.objects.new('EFEITO_LuzEstrobo', luz_est)
o_luz_est.location = Vector((0.68, -0.68, Z_TOPO_TORRE + 0.14))
sc.collection.objects.link(o_luz_est)

# Anel luminoso de desaceleração magnética (Efeito de indução no funil)
bm_ind = bmesh.new()
toro(bm_ind, (0, 0, 1.15), 0.62, 0.015, nR=24, nr=6)
o_ind = obj('EFEITO_CampoIndutivo', bm_ind, 'bobina_inducao')
suavizar(o_ind)

luz_ind = bpy.data.lights.new('LuzInducao', 'POINT')
luz_ind.color = (0.2, 0.7, 1.0)
luz_ind.energy = 0.0
o_luz_ind = bpy.data.objects.new('EFEITO_LuzInducao', luz_ind)
o_luz_ind.location = Vector((0.0, 0.0, 1.15))
sc.collection.objects.link(o_luz_ind)

# ==============================================================================
# 7. PEÇAS MÓVEIS: 4 GARRAS DE RETENÇÃO E PISTÕES HIDRÁULICOS
# ==============================================================================
garras = []
hastes = []

for ig in range(4):
    ang_g = ig * PI / 2 + PI / 4
    dx_g, dy_g = math.cos(ang_g), math.sin(ang_g)

    # ---------------- Garra / Braço articulado
    bm_br = bmesh.new()
    # Mancal com bucha
    tubo(bm_br, (0, -0.06, 0), (0, 0.06, 0), 0.035, 12)
    # Haste mestra do braço descendo para dentro do funil
    viga(bm_br, Vector((0, 0, 0)), Vector((-0.24, 0, 0.16)), 0.05)
    viga(bm_br, Vector((-0.24, 0, 0.16)), Vector((-0.42, 0, -0.05)), 0.045)
    # Sapata de retenção curva com almofada de borracha de alto atrito
    caixa(bm_br, (-0.42, 0, -0.08), (0.06, 0.18, 0.08))
    # Olhal de fixação da haste do cilindro no meio do braço
    tubo(bm_br, (-0.14, -0.03, 0.10), (-0.14, 0.03, 0.10), 0.022, 10)

    o_g = obj('garra%d' % ig, bm_br, 'chassi_amarelo')
    suavizar(o_g)
    o_g.location = Vector((dx_g * 0.74, dy_g * 0.74, 1.36))
    o_g.rotation_euler = Euler((0, 0, ang_g), 'XYZ')
    garras.append(o_g)

    # ---------------- Camisa do Cilindro (presa na blindagem inferior)
    p_base_cil = Vector((dx_g * 0.84, dy_g * 0.84, 0.65))
    bm_cam = bmesh.new()
    tubo(bm_cam, (0, -0.04, 0), (0, 0.04, 0), 0.028, 10)
    o_cam = obj('camisa_pistao%d' % ig, bm_cam, 'aco_escuro')
    o_cam.location = p_base_cil
    o_cam.rotation_euler = Euler((0, 0, ang_g), 'XYZ')

    # ---------------- Haste telescópica móvel cromada
    bm_has = bmesh.new()
    tubo(bm_has, (0, 0, 0), (0, 0, 0.45), 0.026, 12)            # camisa externa
    tubo(bm_has, (0, 0, 0.20), (0, 0, 0.62), 0.016, 12)         # haste cromada
    tubo(bm_has, (0, -0.025, 0.62), (0, 0.025, 0.62), 0.018, 10) # olhal superior
    o_h = obj('haste%d' % ig, bm_has, 'cromo')
    suavizar(o_h)
    o_h.location = p_base_cil
    hastes.append(o_h)

# ==============================================================================
# 8. PEÇAS MÓVEIS: ROLETES DE SAÍDA E MECANISMO EXPULSOR (EMPURRADOR)
# ==============================================================================
roletes = []
for ir in range(5):
    y_rol = 0.74 + ir * 0.05
    bm_rol = bmesh.new()
    tubo(bm_rol, (-0.21, 0, 0), (0.21, 0, 0), 0.018, 12)
    tubo(bm_rol, (-0.23, 0, 0), (0.23, 0, 0), 0.008, 8)
    o_r = obj('rolete%d' % ir, bm_rol, 'aco_gasto')
    suavizar(o_r)
    o_r.location = Vector((0.0, y_rol, 0.23))
    roletes.append(o_r)

# Empurrador interno
bm_emp = bmesh.new()
caixa(bm_emp, (0.0, 0.0, 0.0), (0.24, 0.08, 0.12))
tubo(bm_emp, (0.0, -0.30, 0.0), (0.0, 0.0, 0.0), 0.025, 12)
o_emp = obj('empurrador', bm_emp, 'aco_escuro')
suavizar(o_emp)
o_emp.location = Vector((0.0, 0.25, 0.23))

# ==============================================================================
# 9. CÁPSULA BALÍSTICA E NÚCLEO GÊNESE EXTRAÍDO
# ==============================================================================
bm_cap = bmesh.new()
# Escudo térmico ablativo inferior escuro
tubo(bm_cap, (0, 0, -0.22), (0, 0, -0.15), 0.32, 16)
# Corpo cônico da cápsula com aletas aerodinâmicas
v_cb = [bm_cap.verts.new((0.32 * math.cos(k * 2 * PI / 16), 0.32 * math.sin(k * 2 * PI / 16), -0.15)) for k in range(16)]
v_ct = [bm_cap.verts.new((0.20 * math.cos(k * 2 * PI / 16), 0.20 * math.sin(k * 2 * PI / 16), 0.35)) for k in range(16)]
v_np = [bm_cap.verts.new((0.08 * math.cos(k * 2 * PI / 16), 0.08 * math.sin(k * 2 * PI / 16), 0.52)) for k in range(16)]
for k in range(16):
    k1 = (k + 1) % 16
    bm_cap.faces.new((v_cb[k], v_cb[k1], v_ct[k1], v_ct[k]))
    bm_cap.faces.new((v_ct[k], v_ct[k1], v_np[k1], v_np[k]))
# Topo com nariz abobadado
bmesh.ops.create_uvsphere(bm_cap, u_segments=16, v_segments=8, radius=0.08, matrix=Matrix.Translation(Vector((0, 0, 0.52))))
# 4 aletas aerodinâmicas de reentrada
for ia in range(4):
    ang_al = ia * PI / 2
    dx_a, dy_a = math.cos(ang_al), math.sin(ang_al)
    caixa(bm_cap, (dx_a * 0.30, dy_a * 0.30, 0.05), (0.14, 0.02, 0.30), rot=Matrix.Rotation(ang_al, 3, 'Z'))

o_cap = obj('capsula_chegada', bm_cap, 'aco_escuro')
suavizar(o_cap)

# Núcleo / Canister gênese com cristal pulsante
bm_nuc = bmesh.new()
tubo(bm_nuc, (0, 0, 0.02), (0, 0, 0.16), 0.09, 12)
hexa_cristal(bm_nuc, (0, 0, 0.09), 0.05, 0.12, ponta_sup=0.03, ponta_inf=0.03)
o_nuc = obj('nucleo_capsula', bm_nuc, 'cristal_nucleo')
suavizar(o_nuc)

# ==============================================================================
# 10. ANIMAÇÃO EM LAÇO (96 QUADROS A 24 QPS - 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)

    # --- Estrobo na torre (flashes rápidos a cada 24 quadros)
    ciclo_est = (f % 24)
    pot_est = 60.0 if ciclo_est in (1, 2, 6, 7) else 0.0
    luz_est.energy = pot_est
    luz_est.keyframe_insert('energy', frame=f)

    # --- Cápsula balística descendo e pousando
    if f < 18:
        alt_cap = 4.2 - (f / 18.0) * 1.8
        o_cap.location = Vector((0.0, 0.0, alt_cap))
        o_cap.rotation_euler = Euler((math.sin(f * 0.4) * 0.04, math.cos(f * 0.3) * 0.04, f * 0.05), 'XYZ')
    elif f <= 32:
        t_fren = (f - 18) / 14.0
        s_fren = 1.0 - math.cos(t_fren * PI * 0.5)
        alt_cap = 2.4 - s_fren * (2.4 - 1.10)
        o_cap.location = Vector((0.0, 0.0, alt_cap))
        o_cap.rotation_euler = Euler((0, 0, 18 * 0.05 + t_fren * 0.4), 'XYZ')
    elif f <= 72:
        recuo = math.sin((f - 32) * PI / 10.0) * 0.03 if f <= 42 else 0.0
        o_cap.location = Vector((0.0, 0.0, 1.10 - recuo))
        o_cap.rotation_euler = Euler((0, 0, 18 * 0.05 + 0.4), 'XYZ')
    else:
        o_cap.location = Vector((0.0, 0.0, 1.10))
        o_cap.rotation_euler = Euler((0, 0, 18 * 0.05 + 0.4), 'XYZ')
    o_cap.keyframe_insert('location', frame=f)
    o_cap.keyframe_insert('rotation_euler', frame=f)

    # --- Luz de indução magnética dos anéis
    if 20 <= f <= 36:
        pot_ind = math.sin((f - 20) / 16.0 * PI) * 80.0
    else:
        pot_ind = 2.0
    luz_ind.energy = pot_ind
    luz_ind.keyframe_insert('energy', frame=f)

    # --- Garras de retenção articuladas (abrem e fecham)
    if f < 28:
        ang_abertura = math.radians(24.0)
    elif f <= 36:
        t_fc = (f - 28) / 8.0
        ang_abertura = math.radians(24.0 - t_fc * 28.0)
    elif f <= 72:
        ang_abertura = math.radians(-4.0)
    elif f <= 88:
        t_ab = (f - 72) / 16.0
        ang_abertura = math.radians(-4.0 + t_ab * 28.0)
    else:
        ang_abertura = math.radians(24.0)

    for ig, og in enumerate(garras):
        ang_g = ig * PI / 2 + PI / 4
        q_base = Quaternion(Vector((0, 0, 1)), ang_g)
        q_art = Quaternion(Vector((0, 1, 0)), ang_abertura)
        og.rotation_euler = (q_base @ q_art).to_euler()
        og.keyframe_insert('rotation_euler', frame=f)

        # Orientar a haste do pistão apontando para o olhal da garra
        p_olhal_loc = Vector((-0.14, 0.0, 0.10))
        p_olhal_mundo = og.location + (q_base @ q_art) @ p_olhal_loc
        p_base_cil = hastes[ig].location
        dir_haste = p_olhal_mundo - p_base_cil
        hastes[ig].rotation_euler = dir_haste.to_track_quat('Z', 'Y').to_euler()
        hastes[ig].keyframe_insert('rotation_euler', frame=f)

    # --- Empurrador de descarte interno
    if f < 42:
        y_emp = 0.22
    elif f <= 58:
        t_e = (f - 42) / 16.0
        y_emp = 0.22 + t_e * 0.36
    elif f <= 70:
        y_emp = 0.58
    elif f <= 84:
        t_r = (f - 70) / 14.0
        y_emp = 0.58 - t_r * 0.36
    else:
        y_emp = 0.22
    o_emp.location = Vector((0.0, y_emp, 0.23))
    o_emp.keyframe_insert('location', frame=f)

    # --- Núcleo Gênese na esteira de saída norte
    if f < 46:
        o_nuc.location = Vector((0.0, 0.26, 0.23))
        o_nuc.hide_render = True
    elif f <= 60:
        o_nuc.hide_render = False
        t_n = (f - 46) / 14.0
        y_n = 0.30 + t_n * 0.44
        o_nuc.location = Vector((0.0, y_n, 0.24))
    elif f <= 90:
        o_nuc.hide_render = False
        t_sai = (f - 60) / 30.0
        y_n = 0.74 + t_sai * 0.24
        o_nuc.location = Vector((0.0, y_n, 0.24))
    else:
        o_nuc.hide_render = True
    o_nuc.keyframe_insert('location', frame=f)
    o_nuc.keyframe_insert('hide_render', frame=f)

    # --- Rotação dos roletes da esteira ao transportar o canister
    for ir, orol in enumerate(roletes):
        if 48 <= f <= 92:
            ang_rol = -(f - 48) * 0.35
        else:
            ang_rol = 0.0
        orol.rotation_euler = Euler((ang_rol, 0, 0), 'XYZ')
        orol.keyframe_insert('rotation_euler', frame=f)

# ==============================================================================
# CÂMERAS, LUZ E RENDERIZAÇÃO
# ==============================================================================
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (14, 14, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.2
sol_d.angle = math.radians(2.2)
o_sol = bpy.data.objects.new('Sol', sol_d)
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


ALVO = Vector((0.0, 0.0, 0.95))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(52)  # Momento em que as garras travam a cápsula e o núcleo desliza na esteira

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.1), (210, 2.3), (120, 2.4), (30, 2.0))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 4.6, math.sin(a) * 4.6, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'receptor_capsulas_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: funil com garras travadas, cilindros hidráulicos, anéis de cobre e núcleo na esteira
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(52)
        mirar(Vector((1.75, 1.70, 1.75)), Vector((0.0, 0.15, 0.85)), 35)
        sc.render.filepath = os.path.join(AQUI, 'receptor_capsulas_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(52)
    mirar(ALVO + Vector((2.8, -3.2, 1.5)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'receptor_capsulas_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('RECEPTOR_CAPSULAS ok (%d tris)' % tot_tri)
