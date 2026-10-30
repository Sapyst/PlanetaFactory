"""Estudo isolado (fora do jogo): SILO DE LANÇAMENTO da IA, 3×3 tiles (lote 17, proliferação).
Entrada de itens ao sul (ITEM_ENT_S1, x = 0,0, borda sul y = -1,45 m, altura z = 0,23 m).
Entrada de itens a oeste (ITEM_ENT_O1, borda oeste x = -1,45 m, y = 0,0, altura z = 0,23 m).
Entrada de fluido a leste (FLUIDO_ENT_L1, borda leste x = +1,45 m, y = 0,0, altura z = 0,35 m).
Função: Complexo monumental de montagem e lançamento orbital do foguete de proliferação da IA.
Recebe 100 partes industriais (casco blindado, computação quântica e motores de cristal) e propelente criogênico,
realizando a montagem automatizada por braços robóticos industriais e a ignição orbital vertical.

Mecânica industrial pesada:
- Laje de concreto refratário 2,92 × 2,92 m com grelhas de alívio térmico para exaustão de chamas.
- Poço central de 1,75 m com 4 garras hidráulicas de retenção/travamento na base do foguete.
- Torre de lançamento mestre a nordeste (Z = 3,35 m) com estrutura treliçada dupla, guindaste de topo e braços umbilicais.
- Braço umbilical superior criogênico ('braco_umb_sup') e braço estabilizador inferior ('braco_umb_inf') basculantes com pistões.
- Dois robôs articulados de solda e montagem ('robo_montagem0' e 'robo_montagem1') com tochas de plasma e feixes de cabos.
- Usina de propelente criogênico a leste com bomba de vácuo, manifold de válvulas, vaso horizontal e chaminé de alívio.
- Bocas de esteira com capotas de aço, roletes industriais e motores blindados nas bordas sul e oeste (z = 0,23 m).
- Foguete de proliferação ('foguete') com 4 tubeiras com anéis de reforço, duto de cabos na fuselagem,
  anel de interestágio treliçado, aletas em delta e ogiva com cristal de navegação em berço usinado.
- Animação em laço de 96 quadros (4 s a 24 qps): robôs soldando a fuselagem com faíscas de plasma (quadros 1..34),
  retração rápida e simultânea dos braços umbilicais (quadros 35..48), pré-ignição e clarão nos defletores (quadros 49..51),
  lançamento vertical veloz subindo aos céus com pluma de exaustão (quadros 52..74), e rearme do berço para o ciclo seguinte (quadros 75..96).

Uso: blender -b --python estudo_silo_lancamento.py -- foto
     blender -b --python estudo_silo_lancamento.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, cil, tubo, viga, bezier, mangueira, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(777)
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
M['concreto'] = mats.material('ConcretoRefratario', (0.32, 0.31, 0.30), 0.05, 0.92, pintura=False, ferrugem=0.10, sujeira=0.85)
M['aco_escuro'] = mats.material('AcoEscuro', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.45, sujeira=0.60)
M['aco_gasto'] = mats.material('AcoGasto', (0.35, 0.36, 0.37), 0.85, 0.38, pintura=False, ferrugem=0.30, sujeira=0.50)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['remendo_primer'] = mats.material('RemendoPrimer', (0.42, 0.16, 0.12), 0.10, 0.65, pintura=True, ferrugem=0.20, sujeira=0.40)
M['cobre'] = mats.material('CobreIndutivo', (0.75, 0.38, 0.20), 0.92, 0.30, pintura=False, ferrugem=0.05, sujeira=0.40)
M['cromo'] = mats.material('CromoPistao', (0.85, 0.85, 0.85), 0.96, 0.12, pintura=False, ferrugem=0.02, sujeira=0.15)
M['casco_foguete'] = mats.material('CascoFoguete', (0.78, 0.80, 0.82), 0.20, 0.35, pintura=True, ferrugem=0.18, sujeira=0.50, desgaste=0.60)
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

M['plasma_exaustao'] = mat_emissao('PlasmaExaustao', (1.0, 0.55, 0.15), 18.0)
M['cristal_navegacao'] = mat_emissao('CristalNavegacao', (0.15, 0.85, 0.95), 6.0)
M['arco_solda'] = mat_emissao('ArcoSolda', (0.5, 0.8, 1.0), 12.0)

# ==============================================================================
# 1. LAJE MACIÇA 3×3 COM POÇO, TRINCHEIRAS DE FOGO E GRELHAS DE EXAUSTÃO
# ==============================================================================
bm_con = bmesh.new()
bm_aco = bmesh.new()
bm_lis = bmesh.new()
bm_cob = bmesh.new()

R_EXT = 1.46
L_CH = 0.50
vs_laje = [
    Vector((-R_EXT + L_CH, -R_EXT, 0.0)),
    Vector((R_EXT - L_CH, -R_EXT, 0.0)),
    Vector((R_EXT, -R_EXT + L_CH, 0.0)),
    Vector((R_EXT, R_EXT - L_CH, 0.0)),
    Vector((R_EXT - L_CH, R_EXT, 0.0)),
    Vector((-R_EXT + L_CH, R_EXT, 0.0)),
    Vector((-R_EXT, R_EXT - L_CH, 0.0)),
    Vector((-R_EXT, -R_EXT + L_CH, 0.0)),
]
H_LAJE = 0.28
v_inf = [bm_con.verts.new(v) for v in vs_laje]
v_sup = [bm_con.verts.new(v + Vector((0, 0, H_LAJE))) for v in vs_laje]
bm_con.faces.new(list(reversed(v_inf)))
bm_con.faces.new(v_sup)
for k in range(8):
    bm_con.faces.new((v_inf[k], v_inf[(k + 1) % 8], v_sup[(k + 1) % 8], v_sup[k]))

# Rodapés com listras de perigo nos 4 cantos chanfrados da laje
for k in (0, 2, 4, 6):
    p0 = vs_laje[(k + 1) % 8]
    p1 = vs_laje[(k + 2) % 8]
    meio = (p0 + p1) * 0.5 + Vector((0, 0, H_LAJE * 0.5))
    norm = Vector((p1.y - p0.y, -(p1.x - p0.x), 0)).normalized()
    comp = (p1 - p0).length
    ang = math.atan2(p1.y - p0.y, p1.x - p0.x)
    caixa(bm_lis, meio + norm * 0.012, (comp * 0.96, 0.02, H_LAJE * 0.8), rot=Matrix.Rotation(ang, 3, 'Z'))

# Colar cilíndrico do poço de lançamento central (diâmetro 1,75 m)
R_POCO = 0.88
LADOS_P = 24
bm_poco = bmesh.new()
# Anel de flange maciço rebitado ao redor do poço
toro(bm_poco, (0, 0, H_LAJE + 0.04), R_POCO + 0.04, 0.04, nR=24, nr=6)
# Paredes internas do poço
v_p_topo = [bm_poco.verts.new((R_POCO * math.cos(k * 2 * PI / LADOS_P), R_POCO * math.sin(k * 2 * PI / LADOS_P), H_LAJE + 0.04)) for k in range(LADOS_P)]
v_p_fundo = [bm_poco.verts.new((R_POCO * 0.82 * math.cos(k * 2 * PI / LADOS_P), R_POCO * 0.82 * math.sin(k * 2 * PI / LADOS_P), 0.02)) for k in range(LADOS_P)]
for k in range(LADOS_P):
    k1 = (k + 1) % LADOS_P
    bm_poco.faces.new((v_p_topo[k], v_p_topo[k1], v_p_fundo[k1], v_p_fundo[k]))

# Cone defletor de chamas invertido no centro do fundo do poço
v_def_ponta = bm_poco.verts.new((0.0, 0.0, 0.24))
for k in range(LADOS_P):
    k1 = (k + 1) % LADOS_P
    bm_poco.faces.new((v_p_fundo[k1], v_p_fundo[k], v_def_ponta))

# Grelhas de ventilação / trincheiras de alívio de chamas nas laterais
for dx_g in (-0.95, 0.95):
    for ig in range(5):
        yg = -0.30 + ig * 0.15
        caixa(bm_aco, (dx_g, yg, H_LAJE + 0.01), (0.22, 0.04, 0.02))

# 4 garras de travamento mecânico (hold-down clamps) radiais ao redor do poço
for ia in range(4):
    ang_a = ia * PI / 2 + PI / 4
    dx_a, dy_a = math.cos(ang_a), math.sin(ang_a)
    p_garra = Vector((dx_a * (R_POCO + 0.10), dy_a * (R_POCO + 0.10), H_LAJE + 0.08))
    # Pedestal de ancoragem
    caixa(bm_aco, p_garra, (0.16, 0.16, 0.18))
    # Garra articulada de fixação
    tubo(bm_aco, p_garra, Vector((dx_a * (R_POCO - 0.06), dy_a * (R_POCO - 0.06), H_LAJE + 0.12)), 0.035, 8)
    # Haste do cilindro de liberação rápida
    tubo(bm_aco, p_garra + Vector((0, 0, 0.08)), p_garra + Vector((dx_a * -0.10, dy_a * -0.10, 0.18)), 0.02, 6)

# ==============================================================================
# 2. TORRE UMBILICAL DUPLA COM GUINDASTE E PLATAFORMAS (NORDESTE)
# ==============================================================================
p_torre = Vector((0.98, 0.98, H_LAJE))
Z_TOPO_TORRE = 3.35

bm_cha = bmesh.new()
# Base de chassi reforçada com vigas de aço
caixa(bm_cha, (p_torre.x, p_torre.y, H_LAJE + 0.20), (0.50, 0.50, 0.40))

# 4 colunas principais da torre treliçada
for dx_t, dy_t in ((-0.16, -0.16), (0.16, -0.16), (-0.16, 0.16), (0.16, 0.16)):
    tubo(bm_aco, p_torre + Vector((dx_t, dy_t, 0.40)), p_torre + Vector((dx_t * 0.75, dy_t * 0.75, Z_TOPO_TORRE - H_LAJE)), 0.032, 8)

# Travessas horizontais e cruzetas
for iz in range(8):
    zt = H_LAJE + 0.65 + iz * 0.34
    caixa(bm_aco, (p_torre.x, p_torre.y, zt), (0.28 - iz * 0.015, 0.28 - iz * 0.015, 0.025))

# Plataforma de comando e guindaste de montagem no topo da torre
caixa(bm_cha, (p_torre.x, p_torre.y, Z_TOPO_TORRE), (0.42, 0.42, 0.05))
# Braço de guindaste estendido sobre o poço
viga(bm_aco, p_torre + Vector((0, 0, Z_TOPO_TORRE - H_LAJE + 0.05)), p_torre + Vector((-0.70, -0.70, Z_TOPO_TORRE - H_LAJE + 0.05)), 0.06)
# Tambor de cabo e roldana
tubo(bm_aco, p_torre + Vector((-0.65, -0.65, Z_TOPO_TORRE - H_LAJE + 0.02)), p_torre + Vector((-0.65, -0.65, Z_TOPO_TORRE - H_LAJE - 0.20)), 0.012, 6)

# Farol estroboscópico de alerta no mastro da torre
tubo(bm_aco, (p_torre.x, p_torre.y, Z_TOPO_TORRE + 0.05), (p_torre.x, p_torre.y, Z_TOPO_TORRE + 0.20), 0.025, 10)

# Chapa trocada em primer vermelho no pedestal da torre
bm_rem = bmesh.new()
caixa(bm_rem, (p_torre.x + 0.255, p_torre.y, H_LAJE + 0.22), (0.015, 0.26, 0.24))
for dy_r in (-0.10, 0.0, 0.10):
    for dz_r in (-0.08, 0.08):
        tubo(bm_aco, (p_torre.x + 0.26, p_torre.y + dy_r, H_LAJE + 0.22 + dz_r), (p_torre.x + 0.28, p_torre.y + dy_r, H_LAJE + 0.22 + dz_r), 0.008, 6)

# ==============================================================================
# 3. USINA DE PROPELENTE CRIOGÊNICO E BOCA DE FLUIDO (FLUIDO_ENT_L1: x = +1,45, y = 0,0, z = 0,35 m)
# ==============================================================================
# Boca de fluido leste padronizada a z = 0,35 m
cano_rigido(bm_aco, bm_aco, [(1.45, 0.0, 0.35), (1.28, 0.0, 0.35), (1.12, -0.25, 0.35), (1.12, -0.45, 0.42)], 0.03)

# Vaso de pressão criogênico horizontal com tampos esféricos
tubo(bm_cha, (1.12, -0.70, 0.62), (1.12, 0.20, 0.62), 0.24, 16)
bmesh.ops.create_uvsphere(bm_cha, u_segments=16, v_segments=8, radius=0.24, matrix=Matrix.Translation(Vector((1.12, -0.70, 0.62))))
bmesh.ops.create_uvsphere(bm_cha, u_segments=16, v_segments=8, radius=0.24, matrix=Matrix.Translation(Vector((1.12, 0.20, 0.62))))

# Berços de apoio de aço soldado sob o tanque
caixa(bm_aco, (1.12, -0.55, H_LAJE + 0.10), (0.38, 0.12, 0.20))
caixa(bm_aco, (1.12, 0.05, H_LAJE + 0.10), (0.38, 0.12, 0.20))

# Válvula reguladora com volante e manômetro
tubo(bm_aco, (1.12, -0.25, 0.86), (1.12, -0.25, 1.02), 0.025, 8)
tubo(bm_aco, (1.12, -0.25, 1.02), (1.12, -0.25, 1.08), 0.05, 12)
toro(bm_aco, (1.12, -0.25, 1.10), 0.06, 0.012, nR=16, nr=5)  # volante

# Chaminé vertical de respiro de vapor criogênico
tubo(bm_aco, (1.12, -0.65, 0.86), (1.12, -0.65, 1.65), 0.035, 10)
# Curva na ponta da chaminé
tubo(bm_aco, (1.12, -0.65, 1.65), (1.05, -0.65, 1.72), 0.035, 10)

# Tubulação isolada de cobre subindo até a torre umbilical
cano_rigido(bm_cob, bm_aco, [
    (1.12, 0.20, 0.62),
    (1.08, 0.72, 0.62),
    (1.08, 0.72, 1.80),
    (0.88, 0.88, 2.25)
], 0.024)

# ==============================================================================
# 4. BOCAS DE ENTRADA DE ITENS: SUL (ITEM_ENT_S1) E OESTE (ITEM_ENT_O1) A z = 0,23 m
# ==============================================================================
# Capota e guias sul (x = 0.0, y = -1.45 m, z = 0.23 m)
caixa(bm_cha, (-0.24, -1.25, 0.23), (0.04, 0.38, 0.12))
caixa(bm_cha, (0.24, -1.25, 0.23), (0.04, 0.38, 0.12))
caixa(bm_lis, (-0.26, -1.25, 0.26), (0.01, 0.36, 0.06))
caixa(bm_lis, (0.26, -1.25, 0.26), (0.01, 0.36, 0.06))
# Motor de acionamento lateral
tubo(bm_aco, (0.28, -1.30, 0.23), (0.42, -1.30, 0.23), 0.06, 12)

# Capota e guias oeste (x = -1.45 m, y = 0.0, z = 0.23 m)
caixa(bm_cha, (-1.25, -0.24, 0.23), (0.38, 0.04, 0.12))
caixa(bm_cha, (-1.25, 0.24, 0.23), (0.38, 0.04, 0.12))
caixa(bm_lis, (-1.25, -0.26, 0.26), (0.36, 0.01, 0.06))
caixa(bm_lis, (-1.25, 0.26, 0.26), (0.36, 0.01, 0.06))
tubo(bm_aco, (-1.30, 0.28, 0.23), (-1.30, 0.42, 0.23), 0.06, 12)

# Roletes ativos nas esteiras
roletes = []
for ir in range(4):
    ys = -1.40 + ir * 0.08
    bm_rol_s = bmesh.new()
    tubo(bm_rol_s, (-0.22, 0, 0), (0.22, 0, 0), 0.018, 10)
    o_rs = obj('rolete_sul%d' % ir, bm_rol_s, 'aco_gasto')
    suavizar(o_rs)
    o_rs.location = Vector((0.0, ys, 0.23))
    roletes.append(o_rs)

    xo = -1.40 + ir * 0.08
    bm_rol_o = bmesh.new()
    tubo(bm_rol_o, (0, -0.22, 0), (0, 0.22, 0), 0.018, 10)
    o_ro = obj('rolete_oeste%d' % ir, bm_rol_o, 'aco_gasto')
    suavizar(o_ro)
    o_ro.location = Vector((xo, 0.0, 0.23))
    roletes.append(o_ro)

# Mancha de óleo hidráulico sob o redutor oeste
bm_oleo = bmesh.new()
mancha(bm_oleo, (-1.15, 0.0), 0.25, H_LAJE + 0.001)
o_ole = obj('corpo_oleo', bm_oleo, 'oleo')

# ==============================================================================
# CRIAÇÃO DOS OBJETOS ESTÁTICOS
# ==============================================================================
o_con = obj('base_concreto', bm_con, 'concreto')
suavizar(o_con)

o_poc = obj('poco_refratario', bm_poco, 'aco_escuro')
suavizar(o_poc)

o_aco = obj('detalhes_aco', bm_aco, 'aco_gasto')
suavizar(o_aco)

o_cha = obj('chassi_amarelo', bm_cha, 'chassi_amarelo')
suavizar(o_cha)

o_rem = obj('remendo_primer', bm_rem, 'remendo_primer')

o_lis = obj('listras_aviso', bm_lis, 'listras')

o_cob = obj('tubos_cobre', bm_cob, 'cobre')
suavizar(o_cob)

# ==============================================================================
# 5. PEÇAS MÓVEIS: BRAÇOS UMBILICAIS DUPLOS DA TORRE
# ==============================================================================
# Braço Umbilical Superior (Criogênico) a z = 2.25 m
p_pivo_umb_sup = Vector((0.88, 0.88, 2.25))
ang_torre_z = -3 * PI / 4

bm_usup = bmesh.new()
tubo(bm_usup, (0, -0.06, 0), (0, 0.06, 0), 0.035, 12)
viga(bm_usup, Vector((0, 0, 0)), Vector((-0.84, 0, 0.06)), 0.065)
caixa(bm_usup, (-0.84, 0, 0.06), (0.12, 0.18, 0.14))
# Bicos criogênicos de engate rápido
for ic in (-0.05, 0.05):
    tubo(bm_usup, (-0.84, ic, 0.06), (-0.94, ic, 0.06), 0.024, 10)
# Mangueira criogênica curvada
mangueira(bm_usup, [Vector((0, 0.08, 0)), Vector((-0.42, 0.15, -0.08)), Vector((-0.84, 0.06, 0.04))], 0.022)

o_usup = obj('braco_umb_sup', bm_usup, 'chassi_amarelo')
suavizar(o_usup)
o_usup.location = p_pivo_umb_sup
o_usup.rotation_euler = Euler((0, 0, ang_torre_z), 'XYZ')

# Braço Umbilical Inferior (Estabilizador mecânico) a z = 1.45 m
p_pivo_umb_inf = Vector((0.88, 0.88, 1.45))
bm_uinf = bmesh.new()
tubo(bm_uinf, (0, -0.05, 0), (0, 0.05, 0), 0.032, 10)
viga(bm_uinf, Vector((0, 0, 0)), Vector((-0.82, 0, 0.0)), 0.055)
# Sapatas de apoio estofadas
caixa(bm_uinf, (-0.82, 0, 0.0), (0.08, 0.24, 0.10))

o_uinf = obj('braco_umb_inf', bm_uinf, 'chassi_amarelo')
suavizar(o_uinf)
o_uinf.location = p_pivo_umb_inf
o_uinf.rotation_euler = Euler((0, 0, ang_torre_z), 'XYZ')

# Cilindro hidráulico de acionamento umbilical
p_base_has = p_torre + Vector((0, 0, 1.70))
bm_has_u = bmesh.new()
tubo(bm_has_u, (0, 0, 0), (0, 0, 0.45), 0.028, 10)
tubo(bm_has_u, (0, 0, 0.25), (0, 0, 0.70), 0.018, 10)
o_has_u = obj('haste_umbilical', bm_has_u, 'cromo')
suavizar(o_has_u)
o_has_u.location = p_base_has

# ==============================================================================
# 6. PEÇAS MÓVEIS: DOIS ROBÔS ARTICULADOS DE MONTAGEM E SOLDA
# ==============================================================================
robos_montagem = []
for ib, ang_b in enumerate((-PI / 4, 3 * PI / 4)):
    dx_b, dy_b = math.cos(ang_b) * (R_POCO + 0.18), math.sin(ang_b) * (R_POCO + 0.18)
    p_base_b = Vector((dx_b, dy_b, H_LAJE + 0.06))

    bm_rb = bmesh.new()
    # Base circular do robô
    tubo(bm_rb, (0, 0, 0), (0, 0, 0.12), 0.07, 14)
    # Braço proximal
    viga(bm_rb, Vector((0, 0, 0.12)), Vector((-0.34, 0, 0.42)), 0.05)
    # Braço distal
    viga(bm_rb, Vector((-0.34, 0, 0.42)), Vector((-0.62, 0, 0.25)), 0.04)
    # Cabeçote com tocha de solda plasma e câmera óptica
    tubo(bm_rb, (-0.62, 0, 0.25), (-0.74, 0, 0.20), 0.020, 10)
    caixa(bm_rb, (-0.62, 0.04, 0.28), (0.04, 0.04, 0.06))

    o_rb = obj('robo_montagem%d' % ib, bm_rb, 'chassi_amarelo')
    suavizar(o_rb)
    o_rb.location = p_base_b
    o_rb.rotation_euler = Euler((0, 0, ang_b), 'XYZ')
    robos_montagem.append(o_rb)

# Luz do arco de solda plasma
luz_solda = bpy.data.lights.new('LuzSolda', 'POINT')
luz_solda.color = (0.5, 0.8, 1.0)
luz_solda.energy = 0.0
o_luz_solda = bpy.data.objects.new('EFEITO_LuzSolda', luz_solda)
o_luz_solda.location = Vector((-0.40, 0.40, 0.85))
sc.collection.objects.link(o_luz_solda)

# ==============================================================================
# 7. PEÇA PRINCIPAL: FOGUETE DE PROLIFERAÇÃO COM DETALHES AVANÇADOS
# ==============================================================================
bm_fog = bmesh.new()
R_FOG = 0.40

# 4 Tubeiras com anéis externos de reforço usinado
for it in range(4):
    ang_t = it * PI / 2
    dx_t, dy_t = math.cos(ang_t) * 0.19, math.sin(ang_t) * 0.19
    tubo(bm_fog, (dx_t, dy_t, -0.22), (dx_t, dy_t, 0.10), 0.09, 16)
    toro(bm_fog, (dx_t, dy_t, -0.20), 0.095, 0.015, nR=16, nr=5)

# 4 Aletas em delta compostas com chanfro aerodinâmico
for ia in range(4):
    ang_al = ia * PI / 2 + PI / 4
    dx_a, dy_a = math.cos(ang_al), math.sin(ang_al)
    v_a0 = bm_fog.verts.new((dx_a * R_FOG, dy_a * R_FOG, -0.05))
    v_a1 = bm_fog.verts.new((dx_a * (R_FOG + 0.38), dy_a * (R_FOG + 0.38), -0.05))
    v_a2 = bm_fog.verts.new((dx_a * R_FOG, dy_a * R_FOG, 0.85))
    bm_fog.faces.new((v_a0, v_a1, v_a2))

# Estágio inferior (Z = 0.10 a 1.25 m)
tubo(bm_fog, (0, 0, 0.10), (0, 0, 1.25), R_FOG, 24)

# Anel de interestágio treliçado em aço escuro (Z = 1.25 a 1.45 m)
toro(bm_fog, (0, 0, 1.25), R_FOG, 0.02, nR=24, nr=5)
toro(bm_fog, (0, 0, 1.45), R_FOG, 0.02, nR=24, nr=5)
for ii in range(12):
    ang_i = ii * PI / 6
    dxi, dyi = math.cos(ang_i) * (R_FOG - 0.01), math.sin(ang_i) * (R_FOG - 0.01)
    tubo(bm_fog, (dxi, dyi, 1.25), (dxi, dyi, 1.45), 0.012, 6)

# Estágio superior (Z = 1.45 a 2.25 m)
tubo(bm_fog, (0, 0, 1.45), (0, 0, 2.25), R_FOG, 24)

# Duto longitudinal de cabos de telemetria correndo pela fuselagem
caixa(bm_fog, (R_FOG * 0.98, 0.0, 1.15), (0.02, 0.06, 1.85))

# Coifa / Nariz aerodinâmico (Z = 2.25 a 3.05 m)
v_nariz_base = [bm_fog.verts.new((R_FOG * math.cos(k * 2 * PI / 24), R_FOG * math.sin(k * 2 * PI / 24), 2.25)) for k in range(24)]
v_nariz_ponta = bm_fog.verts.new((0.0, 0.0, 3.05))
for k in range(24):
    k1 = (k + 1) % 24
    bm_fog.faces.new((v_nariz_base[k], v_nariz_base[k1], v_nariz_ponta))

# Berço e Cristal de Navegação Quântica no ápice da ogiva
toro(bm_fog, (0, 0, 3.05), 0.06, 0.015, nR=16, nr=5)
hexa_cristal(bm_fog, (0, 0, 3.12), 0.065, 0.18, ponta_sup=0.08)

# Chapa trocada em primer avermelhado na fuselagem do foguete
caixa(bm_fog, (-R_FOG * 0.98, 0.0, 0.85), (0.015, 0.24, 0.30))

o_fog = obj('foguete', bm_fog, 'casco_foguete')
suavizar(o_fog)
o_fog.location = Vector((0.0, 0.0, 0.30))

# Pluma de exaustão e iluminação de queima
luz_chama = bpy.data.lights.new('LuzExaustao', 'POINT')
luz_chama.color = (1.0, 0.6, 0.2)
luz_chama.energy = 0.0
o_luz_chama = bpy.data.objects.new('EFEITO_LuzExaustao', luz_chama)
o_luz_chama.location = Vector((0.0, 0.0, 0.15))
sc.collection.objects.link(o_luz_chama)

bm_pluma = bmesh.new()
tubo(bm_pluma, (0, 0, -0.22), (0, 0, -1.30), 0.40, 16)
o_pluma = obj('EFEITO_Chama', bm_pluma, 'plasma_exaustao')
suavizar(o_pluma)
o_pluma.parent = o_fog
o_pluma.hide_render = True

# ==============================================================================
# 8. ANIMAÇÃO EM LAÇO (96 QUADROS A 24 QPS - 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)

    # --- Robôs de solda e montagem (quadros 1..34)
    if f <= 34:
        ang_solda = math.sin(f * 0.45) * 0.15
        robos_montagem[0].rotation_euler = Euler((0, 0, -PI / 4 + ang_solda), 'XYZ')
        robos_montagem[1].rotation_euler = Euler((0, 0, 3 * PI / 4 - ang_solda), 'XYZ')
        pot_solda = 45.0 if (f % 5) in (1, 2, 3) else 0.0
    else:
        robos_montagem[0].rotation_euler = Euler((0, 0, -PI / 4 - 0.30), 'XYZ')
        robos_montagem[1].rotation_euler = Euler((0, 0, 3 * PI / 4 + 0.30), 'XYZ')
        pot_solda = 0.0
    robos_montagem[0].keyframe_insert('rotation_euler', frame=f)
    robos_montagem[1].keyframe_insert('rotation_euler', frame=f)
    luz_solda.energy = pot_solda
    luz_solda.keyframe_insert('energy', frame=f)

    # --- Braços umbilicais da torre (recuo de 34°)
    if f < 35:
        ang_umb_ret = 0.0
    elif f <= 48:
        t_u = (f - 35) / 13.0
        ang_umb_ret = math.radians(t_u * 34.0)
    elif f <= 78:
        ang_umb_ret = math.radians(34.0)
    else:
        t_ret = (f - 78) / 18.0
        ang_umb_ret = math.radians(34.0 * (1.0 - t_ret))

    q_u_base = Quaternion(Vector((0, 0, 1)), ang_torre_z)
    q_u_rot = Quaternion(Vector((0, 1, 0)), -ang_umb_ret)
    rot_umb_final = (q_u_base @ q_u_rot).to_euler()

    o_usup.rotation_euler = rot_umb_final
    o_uinf.rotation_euler = rot_umb_final
    o_usup.keyframe_insert('rotation_euler', frame=f)
    o_uinf.keyframe_insert('rotation_euler', frame=f)

    # Haste hidráulica da torre
    p_olhal_umb = o_usup.location + (q_u_base @ q_u_rot) @ Vector((-0.35, 0, -0.06))
    dir_has = p_olhal_umb - o_has_u.location
    o_has_u.rotation_euler = dir_has.to_track_quat('Z', 'Y').to_euler()
    o_has_u.keyframe_insert('rotation_euler', frame=f)

    # --- Foguete de proliferação (montagem no poço e lançamento vertical)
    if f < 51:
        vibra = math.sin(f * 2.5) * 0.008 if 45 <= f <= 50 else 0.0
        o_fog.location = Vector((0.0, 0.0, 0.30 + vibra))
        o_fog.hide_render = False
        o_pluma.hide_render = True
        luz_chama.energy = 0.0
    elif f <= 72:
        t_sub = (f - 51) / 21.0
        z_sub = 0.30 + (t_sub ** 1.8) * 4.60
        o_fog.location = Vector((0.0, 0.0, z_sub))
        o_fog.hide_render = False
        o_pluma.hide_render = False
        luz_chama.energy = 180.0
        o_luz_chama.location = Vector((0.0, 0.0, z_sub - 0.20))
    elif f <= 82:
        o_fog.hide_render = True
        o_pluma.hide_render = True
        luz_chama.energy = 0.0
    else:
        o_fog.hide_render = False
        o_fog.location = Vector((0.0, 0.0, 0.30))
        o_pluma.hide_render = True
        luz_chama.energy = 0.0

    o_fog.keyframe_insert('location', frame=f)
    o_fog.keyframe_insert('hide_render', frame=f)
    o_pluma.keyframe_insert('hide_render', frame=f)
    luz_chama.keyframe_insert('energy', frame=f)

    # --- Roletes das esteiras girando durante a entrega das 100 partes
    for orol in roletes:
        if f <= 40:
            ang_r = (f / 40.0) * 8 * PI
        else:
            ang_r = 0.0
        orol.rotation_euler = Euler((ang_r, 0, 0), 'XYZ')
        orol.keyframe_insert('rotation_euler', frame=f)

# ==============================================================================
# CÂMERAS, LUZ E RENDERIZAÇÃO
# ==============================================================================
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (18, 18, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.4
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


ALVO = Vector((0.0, 0.0, 1.45))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(46)  # Momento com braços umbilicais retraídos, foguete completo pronto no poço

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.9), (210, 3.1), (120, 3.2), (30, 2.8))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 6.4, math.sin(a) * 6.4, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'silo_lancamento_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: torre umbilical dupla, usina criogênica, tubeiras e foguete
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(46)
        mirar(Vector((2.4, 1.4, 2.1)), Vector((0.0, 0.1, 1.35)), 35)
        sc.render.filepath = os.path.join(AQUI, 'silo_lancamento_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(46)
    mirar(ALVO + Vector((3.8, -4.2, 2.0)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'silo_lancamento_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('SILO_LANCAMENTO ok (%d tris)' % tot_tri)
