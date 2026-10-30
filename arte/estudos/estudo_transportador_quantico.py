"""Estudo isolado (fora do jogo): TRANSPORTADOR QUÂNTICO da IA, 3×3 tiles (lote 17, proliferação).
Entrada de itens ao sul (ITEM_ENT_S1, x = 0,0, borda sul y = -1,45 m, altura z = 0,23 m).
Saída de itens ao norte (ITEM_SAI_N1, x = 0,0, borda norte y = +1,45 m, altura z = 0,23 m).
Função: Terminal pesado de translocação e emaranhamento quântico da IA entre colônias distantes.
Transfere instantaneamente matéria e dados em nível subatômico sem necessidade de trilhos ou foguetes.

Mecânica industrial pesada:
- Laje de concreto armado 2,92 × 2,92 m com sapatas de aço, chumbadores duplos e canais de duto perimetrais.
- 4 pilones mestres em treliça estrutural nos cantos com cabeçotes projetores de campo e isoladores cerâmicos.
- Conjunto ressonador de 3 níveis: estator toroidal externo, anel superior contra-rotativo com 8 cristais de foco,
  anel inferior contra-rotativo com 6 ímãs supercondutores e cristal hiper-facetado central levitante.
- Estação criogênica de resfriamento a hélio a oeste (tanque esférico isolado, compressor e trocador aletado).
- Banco de 4 condensadores de descarga quântica a leste com barramento maciço de cobre e centelhadores.
- Esteiras ativas com roletes de aço usinado, guias com listras de perigo e motores de passo blindados.
- Animação em laço de 96 quadros (4 s a 24 qps): anéis girando em contra-rotação perfeitamente sincronizada,
  cristal central levitando e pulsando, carga colonial entrando pelo sul, pulso quântico e saída pelo norte.

Uso: blender -b --python estudo_transportador_quantico.py -- foto
     blender -b --python estudo_transportador_quantico.py -- nada
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
random.seed(314)
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
M['prata'] = mats.material('PrataSupercondutora', (0.80, 0.82, 0.85), 0.95, 0.20, pintura=False, ferrugem=0.02, sujeira=0.25)
M['cromo'] = mats.material('CromoPistao', (0.85, 0.85, 0.85), 0.96, 0.12, pintura=False, ferrugem=0.02, sujeira=0.15)
M['ceramica'] = mats.material('CeramicaIsolador', (0.68, 0.70, 0.72), 0.05, 0.25, pintura=False, ferrugem=0.0, sujeira=0.35)
M['listras'] = base3d.listras_mat()
M['oleo'] = mats.material('OleoSujeira', (0.02, 0.02, 0.01), 0.20, 0.15, pintura=False, ferrugem=0.0, sujeira=0.95)
M['chao'] = mats.material('Chao', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0)

# Emissões quânticas
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

M['cristal_quantico'] = mat_emissao('CristalQuantico', (0.35, 0.25, 0.95), 6.0)
M['arco_campo'] = mat_emissao('ArcoCampo', (0.20, 0.70, 1.0), 10.0)
M['led_azul'] = mat_emissao('LED_Azul', (0.1, 0.5, 1.0), 4.0)

# ==============================================================================
# 1. LAJE MACIÇA 3×3 (2.92 × 2.92 m) COM CANAIS E SAPATAS DE ANCORAGEM
# ==============================================================================
bm_con = bmesh.new()
bm_aco = bmesh.new()
bm_lis = bmesh.new()

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
H_LAJE = 0.14
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

# Placas de base e chumbadores duplos com porcas sextavadas nos 4 cantos retos
for cx, cy in ((-1.25, -1.25), (1.25, -1.25), (-1.25, 1.25), (1.25, 1.25)):
    caixa(bm_aco, (cx, cy, H_LAJE + 0.015), (0.24, 0.24, 0.03))
    for bx in (-0.08, 0.08):
        for by in (-0.08, 0.08):
            tubo(bm_aco, (cx + bx, cy + by, H_LAJE + 0.015), (cx + bx, cy + by, H_LAJE + 0.06), 0.016, 6)

# ==============================================================================
# 2. QUATRO PILONES MESTRES EM TRELIÇA E PROJETORES DE ONDA (QUADRANTES)
# ==============================================================================
bm_cha = bmesh.new()
bm_cer = bmesh.new()

pos_pilones = [
    Vector((-1.05, -1.05, H_LAJE)),
    Vector((1.05, -1.05, H_LAJE)),
    Vector((1.05, 1.05, H_LAJE)),
    Vector((-1.05, 1.05, H_LAJE))
]

Z_TOPO_PILONE = 2.15

for ip, pp in enumerate(pos_pilones):
    # Pedestal de chassi com reforço angular
    caixa(bm_cha, (pp.x, pp.y, H_LAJE + 0.25), (0.34, 0.34, 0.50))
    for dx_g in (-0.18, 0.18):
        caixa(bm_aco, (pp.x + dx_g, pp.y, H_LAJE + 0.15), (0.04, 0.30, 0.30))
    for dy_g in (-0.18, 0.18):
        caixa(bm_aco, (pp.x, pp.y + dy_g, H_LAJE + 0.15), (0.30, 0.04, 0.30))

    # Mastro estrutural duplo com travessas treliçadas até o topo
    p_col1 = pp + Vector((-0.07, -0.07, 0.50))
    p_col2 = pp + Vector((0.07, 0.07, 0.50))
    p_col1_t = pp + Vector((-0.04, -0.04, Z_TOPO_PILONE - H_LAJE))
    p_col2_t = pp + Vector((0.04, 0.04, Z_TOPO_PILONE - H_LAJE))
    tubo(bm_aco, p_col1, p_col1_t, 0.038, 8)
    tubo(bm_aco, p_col2, p_col2_t, 0.038, 8)

    # Travessas horizontais e diagonais
    for iz in range(5):
        zt = H_LAJE + 0.65 + iz * 0.28
        caixa(bm_aco, (pp.x, pp.y, zt), (0.18, 0.18, 0.02))

    # Cabeçote projetor de onda quântica inclinado para a câmara central
    v_inward = Vector((-pp.x, -pp.y, 0)).normalized()
    p_ponta = pp + Vector((0, 0, Z_TOPO_PILONE - H_LAJE)) + v_inward * 0.42 + Vector((0, 0, -0.12))
    viga(bm_cha, pp + Vector((0, 0, Z_TOPO_PILONE - H_LAJE)), p_ponta, 0.07)

    # Isolador cerâmico trifásico na ponta do cabeçote
    tubo(bm_cer, p_ponta, p_ponta + Vector((0, 0, -0.20)), 0.045, 12)
    # Anel toroidal emissor de campo quântico na ponta
    ang_rad = math.atan2(v_inward.y, v_inward.x)
    toro(bm_aco, p_ponta + Vector((0, 0, -0.22)), 0.065, 0.015, nR=16, nr=5, rot=Matrix.Rotation(ang_rad, 3, 'Z'))

    # Duto blindado de alta corrente descendo pela coluna até a laje
    cano_rigido(bm_aco, bm_aco, [
        p_ponta + Vector((0, 0, 0.05)),
        pp + Vector((0, 0, Z_TOPO_PILONE - H_LAJE + 0.05)),
        pp + Vector((v_inward.x * 0.12, v_inward.y * 0.12, 0.55)),
        pp + Vector((v_inward.x * 0.25, v_inward.y * 0.25, H_LAJE + 0.05))
    ], 0.016)

# Remendo de chapa soldada com primer vermelho no pilone nordeste (ip = 2)
bm_rem = bmesh.new()
p_rem = pos_pilones[2] + Vector((0.0, 0.175, 0.35))
caixa(bm_rem, p_rem, (0.24, 0.015, 0.28))
for dx_p in (-0.09, 0.0, 0.09):
    for dz_p in (-0.10, 0.10):
        tubo(bm_aco, p_rem + Vector((dx_p, 0.01, dz_p)), p_rem + Vector((dx_p, 0.025, dz_p)), 0.008, 6)

# ==============================================================================
# 3. CÂMARA CENTRAL DE TRANSLOCAÇÃO E ESTATOR TOROIDAL FIXO
# ==============================================================================
# Plataforma octogonal central de confinamento
prisma_octo(bm_con, (0, 0), 0.88, H_LAJE, 0.45)
# Piso com grelha radial usinada e canais de aterramento
for ig in range(9):
    yg = -0.40 + ig * 0.10
    caixa(bm_aco, (0.0, yg, 0.455), (0.92, 0.025, 0.01))

# Estator toroidal supercondutor externo (fixo na base a z = 0.58 m)
bm_cob = bmesh.new()
toro(bm_cob, (0, 0, 0.58), 0.84, 0.048, nR=24, nr=6)
# 8 apoios verticais aletados em torno do estator
for ia in range(8):
    ang_a = ia * PI / 4
    dx_a, dy_a = math.cos(ang_a), math.sin(ang_a)
    caixa(bm_aco, (dx_a * 0.84, dy_a * 0.84, 0.50), (0.05, 0.05, 0.16), rot=Matrix.Rotation(ang_a, 3, 'Z'))

# Condutores pesados de cobre ligando o estator aos bancos de pulso e criogenia
cano_rigido(bm_cob, bm_aco, [(0.76, 0.0, 0.58), (0.98, 0.0, 0.58), (1.12, -0.35, 0.38)], 0.022)
cano_rigido(bm_cob, bm_aco, [(-0.76, 0.0, 0.58), (-0.98, 0.0, 0.58), (-1.12, 0.35, 0.38)], 0.022)

# ==============================================================================
# 4. BANCO DE CONDENSADORES DE VÁCUO (LESTE) E HPU CRIOGÊNICA (OESTE)
# ==============================================================================
# 4 condensadores cilíndricos com aletas a Leste (x ~ +1.10 m, y ~ -0.45 a +0.45 m)
caixa(bm_aco, (1.10, 0.0, H_LAJE + 0.04), (0.34, 1.05, 0.04))
for ic in (-0.36, -0.12, 0.12, 0.36):
    # Cilindro de carcaça com aletas
    tubo(bm_aco, (1.10, ic, H_LAJE + 0.06), (1.10, ic, 0.88), 0.09, 14)
    for ial in range(4):
        ang_c = ial * PI / 4
        dx_c, dy_c = math.cos(ang_c) * 0.10, math.sin(ang_c) * 0.10
        caixa(bm_cob, (1.10 + dx_c, ic + dy_c, 0.48), (0.015, 0.015, 0.52))
    # Isolador cerâmico no topo
    tubo(bm_cer, (1.10, ic, 0.88), (1.10, ic, 1.00), 0.055, 10)
# Barramento maciço de cobre ligando os 4 condensadores
tubo(bm_cob, (1.10, -0.40, 1.00), (1.10, 0.40, 1.00), 0.020, 10)

# Unidade criogênica a Oeste (x ~ -1.10 m, y ~ -0.45 a +0.45 m)
caixa(bm_aco, (-1.10, 0.0, H_LAJE + 0.04), (0.34, 1.05, 0.04))
# Tanque de hélio líquido esférico com anéis de cinta
bmesh.ops.create_uvsphere(bm_cha, u_segments=16, v_segments=10, radius=0.19,
                          matrix=Matrix.Translation(Vector((-1.10, -0.22, 0.48))))
tubo(bm_aco, (-1.10, -0.22, H_LAJE + 0.05), (-1.10, -0.22, 0.32), 0.05, 10)
# Manômetro e visor de nível criogênico
tubo(bm_aco, (-1.10, -0.22, 0.67), (-1.10, -0.22, 0.78), 0.02, 8)
tubo(bm_aco, (-1.10, -0.22, 0.78), (-1.10, -0.22, 0.82), 0.04, 12)

# Compressor criogênico aletado duplo
tubo(bm_aco, (-1.10, 0.12, H_LAJE + 0.16), (-1.10, 0.38, H_LAJE + 0.16), 0.08, 14)
for ial in range(6):
    yl = 0.15 + ial * 0.04
    caixa(bm_aco, (-1.10, yl, H_LAJE + 0.16), (0.20, 0.01, 0.18))
cano_rigido(bm_aco, bm_aco, [(-1.10, -0.05, 0.48), (-1.10, 0.10, 0.48), (-0.88, 0.10, 0.48)], 0.015)
mangueira(bm_aco, [Vector((-1.10, -0.22, 0.67)), Vector((-0.95, -0.22, 0.88)), Vector((-0.68, -0.22, 0.68))], 0.018)

# Mancha de óleo hidráulico/óleo de vácuo sob a bomba
bm_oleo = bmesh.new()
mancha(bm_oleo, (-1.10, 0.20), 0.25, H_LAJE + 0.001)
o_ole = obj('corpo_oleo', bm_oleo, 'oleo')

# ==============================================================================
# 5. BOCAS DE ENTRADA (SUL) E SAÍDA (NORTE) DE ITENS (z = 0,23 m)
# ==============================================================================
# Sul (Entrada: ITEM_ENT_S1: x = 0.0, y = -1.45 m, z = 0.23 m)
caixa(bm_cha, (-0.23, -1.25, 0.23), (0.04, 0.38, 0.12))
caixa(bm_cha, (0.23, -1.25, 0.23), (0.04, 0.38, 0.12))
caixa(bm_lis, (-0.25, -1.25, 0.26), (0.01, 0.36, 0.06))
caixa(bm_lis, (0.25, -1.25, 0.26), (0.01, 0.36, 0.06))

# Norte (Saída: ITEM_SAI_N1: x = 0.0, y = +1.45 m, z = 0.23 m)
caixa(bm_cha, (-0.23, 1.25, 0.23), (0.04, 0.38, 0.12))
caixa(bm_cha, (0.23, 1.25, 0.23), (0.04, 0.38, 0.12))
caixa(bm_lis, (-0.25, 1.25, 0.26), (0.01, 0.36, 0.06))
caixa(bm_lis, (0.25, 1.25, 0.26), (0.01, 0.36, 0.06))

# Roletes estáticos nas esteiras sul e norte
for ir in range(6):
    ys = -1.42 + ir * 0.06
    tubo(bm_aco, (-0.21, ys, 0.23), (0.21, ys, 0.23), 0.016, 10)
    tubo(bm_aco, (-0.23, ys, 0.23), (0.23, ys, 0.23), 0.008, 6)
    yn = 1.12 + ir * 0.06
    tubo(bm_aco, (-0.21, yn, 0.23), (0.21, yn, 0.23), 0.016, 10)
    tubo(bm_aco, (-0.23, yn, 0.23), (0.23, yn, 0.23), 0.008, 6)

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

o_cer = obj('isoladores_ceramica', bm_cer, 'ceramica')
suavizar(o_cer)

o_cob = obj('bobinas_cobre', bm_cob, 'cobre')
suavizar(o_cob)

# ==============================================================================
# 6. PEÇAS MÓVEIS: ANÉIS DE FOCALIZAÇÃO QUÂNTICA CONTRA-ROTATIVOS
# ==============================================================================
# Anel Superior (z = 1.55 m, gira em +Z) com 8 cristais montados em aletas de prata
bm_asup = bmesh.new()
toro(bm_asup, (0, 0, 0), 0.74, 0.034, nR=24, nr=6)
for ic in range(8):
    ang_c = ic * PI / 4
    dx_c, dy_c = math.cos(ang_c), math.sin(ang_c)
    caixa(bm_asup, (dx_c * 0.74, dy_c * 0.74, 0), (0.07, 0.05, 0.09), rot=Matrix.Rotation(ang_c, 3, 'Z'))
    hexa_cristal(bm_asup, (dx_c * 0.63, dy_c * 0.63, 0), 0.038, 0.11, ponta_sup=0.03, ponta_inf=0.03)

o_asup = obj('anel_giro_sup', bm_asup, 'prata')
suavizar(o_asup)
o_asup.location = Vector((0.0, 0.0, 1.55))

# Anel Inferior (z = 1.15 m, gira em -Z) com 6 bobinas magnéticas de cobre
bm_ainf = bmesh.new()
toro(bm_ainf, (0, 0, 0), 0.64, 0.032, nR=24, nr=6)
for ic in range(6):
    ang_c = ic * PI / 3
    dx_c, dy_c = math.cos(ang_c), math.sin(ang_c)
    caixa(bm_ainf, (dx_c * 0.64, dy_c * 0.64, 0), (0.06, 0.06, 0.08), rot=Matrix.Rotation(ang_c, 3, 'Z'))
    hexa_cristal(bm_ainf, (dx_c * 0.53, dy_c * 0.53, 0), 0.035, 0.10, ponta_sup=0.025, ponta_inf=0.025)

o_ainf = obj('anel_giro_inf', bm_ainf, 'cobre')
suavizar(o_ainf)
o_ainf.location = Vector((0.0, 0.0, 1.15))

# Cristal de Ressonância Central Levitação (Z ~ 1.35 m)
bm_cris = bmesh.new()
hexa_cristal(bm_cris, (0, 0, 0), 0.11, 0.32, ponta_sup=0.12, ponta_inf=0.12)
# Pequenos fragmentos satélites orbitais orbitando o cristal
for isat in range(3):
    ang_s = isat * 2 * PI / 3
    hexa_cristal(bm_cris, (math.cos(ang_s) * 0.25, math.sin(ang_s) * 0.25, 0.0), 0.025, 0.06, ponta_sup=0.02, ponta_inf=0.02)

o_cris = obj('cristal_central', bm_cris, 'cristal_quantico')
suavizar(o_cris)
o_cris.location = Vector((0.0, 0.0, 1.35))

# Luz do pulso quântico do cristal central
luz_quant = bpy.data.lights.new('LuzQuantica', 'POINT')
luz_quant.color = (0.35, 0.45, 1.0)
luz_quant.energy = 25.0
o_luz_quant = bpy.data.objects.new('EFEITO_LuzQuantica', luz_quant)
o_luz_quant.location = Vector((0.0, 0.0, 1.35))
sc.collection.objects.link(o_luz_quant)

# Feixe de filamentos quânticos (gaiola translúcida/anelada sem bloquear a visão do cristal)
bm_feixe = bmesh.new()
for ifx in range(8):
    ang_fx = ifx * PI / 4
    dx_fx, dy_fx = math.cos(ang_fx) * 0.38, math.sin(ang_fx) * 0.38
    tubo(bm_feixe, (dx_fx, dy_fx, 0.45), (dx_fx, dy_fx, 2.20), 0.015, 8)
o_feixe = obj('EFEITO_FeixeSalto', bm_feixe, 'arco_campo')
suavizar(o_feixe)

# ==============================================================================
# 7. CARGAS ANIMADAS: PACOTE DE ENTRADA E PACOTE GÊNESE DE SAÍDA
# ==============================================================================
# Contêiner pesado que entra pela esteira sul para ser desmaterializado
bm_paco_ent = bmesh.new()
caixa(bm_paco_ent, (0, 0, 0.08), (0.28, 0.34, 0.16))
for be in (-0.12, 0.12):
    tubo(bm_paco_ent, (be, -0.15, 0.16), (be, 0.15, 0.16), 0.012, 6)
o_pent = obj('carga_entrada', bm_paco_ent, 'aco_escuro')
suavizar(o_pent)

# Pacote gênese colonial que se materializa e sai pela esteira norte
bm_paco_sai = bmesh.new()
caixa(bm_paco_sai, (0, 0, 0.09), (0.24, 0.28, 0.18))
hexa_cristal(bm_paco_sai, (0, 0, 0.18), 0.04, 0.08, ponta_sup=0.03)
o_psai = obj('carga_saida', bm_paco_sai, 'chassi_amarelo')
suavizar(o_psai)

# ==============================================================================
# 8. ANIMAÇÃO EM LAÇO (96 QUADROS A 24 QPS - 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)

    # --- Anel superior girando no sentido horário (+Z)
    ang_sup = (f / float(QUADROS)) * 2 * PI
    o_asup.rotation_euler = Euler((0, 0, ang_sup), 'XYZ')
    o_asup.keyframe_insert('rotation_euler', frame=f)

    # --- Anel inferior girando no sentido anti-horário (-Z)
    ang_inf = -(f / float(QUADROS)) * 2 * PI
    o_ainf.rotation_euler = Euler((0, 0, ang_inf), 'XYZ')
    o_ainf.keyframe_insert('rotation_euler', frame=f)

    # --- Cristal central levitando com pulsação harmônica
    z_cris = 1.35 + math.sin(f * 2 * PI / 48.0) * 0.04
    rot_cris = (f / float(QUADROS)) * PI
    o_cris.location = Vector((0.0, 0.0, z_cris))
    o_cris.rotation_euler = Euler((math.sin(f * 0.2) * 0.03, math.cos(f * 0.2) * 0.03, rot_cris), 'XYZ')
    o_cris.keyframe_insert('location', frame=f)
    o_cris.keyframe_insert('rotation_euler', frame=f)

    # --- Iluminação e efeito do salto quântico (quadros 36..48)
    if 36 <= f <= 48:
        t_salto = (f - 36) / 12.0
        pico_luz = math.sin(t_salto * PI) * 120.0
        o_feixe.hide_render = False
        o_feixe.scale = Vector((1.0 + math.sin(t_salto * PI) * 0.25, 1.0 + math.sin(t_salto * PI) * 0.25, 1.0))
    else:
        pico_luz = 15.0 + math.sin(f * 0.3) * 5.0
        o_feixe.hide_render = True
        o_feixe.scale = Vector((0.1, 0.1, 0.1))

    luz_quant.energy = pico_luz
    luz_quant.keyframe_insert('energy', frame=f)
    o_feixe.keyframe_insert('hide_render', frame=f)
    o_feixe.keyframe_insert('scale', frame=f)

    # --- Carga de entrada (desliza do sul até o centro, desmaterializa no quadro 42)
    if f < 35:
        o_pent.hide_render = False
        t_ent = f / 35.0
        y_ent = -1.45 + t_ent * 1.45
        o_pent.location = Vector((0.0, y_ent, 0.455))
    elif f <= 41:
        o_pent.hide_render = False
        o_pent.location = Vector((0.0, 0.0, 0.455))
    else:
        o_pent.hide_render = True
        o_pent.location = Vector((0.0, 0.0, 0.455))
    o_pent.keyframe_insert('location', frame=f)
    o_pent.keyframe_insert('hide_render', frame=f)

    # --- Carga de saída (rematerializa no quadro 49, sai pelo norte)
    if f < 49:
        o_psai.hide_render = True
        o_psai.location = Vector((0.0, 0.0, 0.455))
    elif f <= 55:
        o_psai.hide_render = False
        o_psai.location = Vector((0.0, 0.0, 0.455))
    elif f <= 86:
        o_psai.hide_render = False
        t_sai = (f - 55) / 31.0
        y_sai = 0.0 + t_sai * 1.45
        o_psai.location = Vector((0.0, y_sai, 0.455))
    else:
        o_psai.hide_render = True
        o_psai.location = Vector((0.0, 1.45, 0.455))
    o_psai.keyframe_insert('location', frame=f)
    o_psai.keyframe_insert('hide_render', frame=f)

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


ALVO = Vector((0.0, 0.0, 1.15))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(28)  # Momento com carga colonial entrando, anéis em plena contra-rotação e cristal visível

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.7), (210, 2.9), (120, 3.0), (30, 2.6))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 6.0, math.sin(a) * 6.0, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'transportador_quantico_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: anéis de contra-rotação, cristal quântico com satélites, pilones e condensadores
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(28)
        mirar(Vector((2.6, 1.15, 1.85)), Vector((0.0, 0.0, 1.25)), 34)
        sc.render.filepath = os.path.join(AQUI, 'transportador_quantico_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(28)
    mirar(ALVO + Vector((3.8, -4.2, 2.0)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'transportador_quantico_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('TRANSPORTADOR_QUANTICO ok (%d tris)' % tot_tri)
