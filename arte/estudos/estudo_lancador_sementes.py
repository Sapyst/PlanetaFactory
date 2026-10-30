"""Estudo isolado (fora do jogo): LANÇADOR DE SEMENTES da IA, 3×3 tiles (lote 17, proliferação).
Entrada de itens pelo sul (ITEM_ENT_S1, tile do meio da borda sul, altura z = 0,23 m).
Função: Acelerador eletromagnético de massa (mass driver) de alta potência. Recebe o núcleo-semente montado
e o lança a até 400 m de distância sobre o planeta para fundar novas colônias autônomas da IA.
Estilo: Artilharia orbital industrial extrema — sem humanos. Laje maciça de concreto com sapatas de recuo e molas
de amortecimento sísmico, torre com mancais de ferro fundido para elevação, berço de alimentação articulado que
insere a cápsula na culatra, tubo acelerador maciço com 5 estágios de bobinas indutoras de cobre, freio de boca com
rasgos de descompressão de plasma e pistões duplos de absorção de recuo.
- Laje de concreto 2,90 × 2,90 m com chanfros nos 4 cantos, chapas de ancoragem com parafusos de chumbador; esteira de
  rolete ao sul (ITEM_ENT_S1) levando a cápsula-semente até o elevador de carregamento.
- Berço basculante de municiamento com pistão articulado inserindo a cápsula na culatra do acelerador.
- Culatra blindada com trincos de travamento hidráulico e câmara de pré-aceleração com anéis de condensador de alta tensão.
- Tubo acelerador eletromagnético de 3,4 m de comprimento com trilhos duplos de aço escovado, 5 bobinas toroidais de cobre
  com aletas dissipadoras e isoladores cerâmicos.
- Freio de boca com respiros radiais para expulsão de calor/gás ionizado e anel terminal magnético de desacoplamento.
- Par de pistões telescópicos amortecedores de recuo (camisa presa na mesa giratória, haste no colar do canhão) com mangueiras.
- A cápsula-semente: ogiva blindada com anéis de selagem de plasma e núcleo de cristal lapidado visível na ponta.
- Animação em laço de 96 quadros (4 s a 24 qps): berço sobe e alimenta a culatra (quadros 1..24), culatra trava com pistão
  (quadros 25..36), bobinas de aceleração acendem em cascata luminosa linear (quadros 38..48), DISPARO no quadro 50 com
  clarão eletromagnético, a cápsula é ejetada a alta velocidade, recuo violento do tubo acelerador comprimindo os pistões
  amortecedores e retorno suave com dissipação de calor nos respiros (quadros 51..96).
Uso: blender -b --python estudo_lancador_sementes.py -- foto
     blender -b --python estudo_lancador_sementes.py -- nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(133)
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


# ------------------------------------------------------------------ materiais
def emissivo_mat(nome, cor, forca_inicial=0.0):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1.0)
    b.inputs['Emission Color'].default_value = (*cor, 1.0)
    b.inputs['Emission Strength'].default_value = forca_inicial
    b.inputs['Roughness'].default_value = 0.20
    return m


base3d.M.update({
    'amarelo': mats.material('AmareloLancador', (0.76, 0.52, 0.07), 0.0, 0.42, desgaste=0.92, sujeira=0.82),
    'primer': mats.material('PrimerLancador', (0.36, 0.12, 0.08), 0.0, 0.55, desgaste=0.88, sujeira=0.85, ferrugem=0.45),
    'grafite': mats.material('GrafiteLancador', (0.08, 0.085, 0.09), 0.0, 0.48, desgaste=0.65, sujeira=0.75),
    'aco': mats.material('AçoLancador', (0.45, 0.46, 0.47), 1.0, 0.38, pintura=False, ferrugem=0.60, sujeira=0.70, escovado=True),
    'aco_escuro': mats.material('AçoEscuroLancador', (0.22, 0.23, 0.24), 1.0, 0.50, pintura=False, ferrugem=0.85, sujeira=0.88),
    'cromo': mats.material('CromoLancador', (0.88, 0.89, 0.90), 1.0, 0.08, pintura=False, sujeira=0.15),
    'cobre': mats.material('CobreLancador', (0.84, 0.44, 0.22), 1.0, 0.30, pintura=False, ferrugem=0.35, sujeira=0.65),
    'ferro': mats.material('FerroFundidoLancador', (0.10, 0.095, 0.09), 0.8, 0.68, pintura=False, ferrugem=0.88, sujeira=0.90),
    'concreto': mats.material('ConcretoLancador', (0.34, 0.33, 0.31), 0.0, 0.90, sujeira=0.78, desgaste=0.25),
    'oleo': mats.material('ÓleoLancador', (0.012, 0.010, 0.008), 0.0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'borracha': mats.material('BorrachaLancador', (0.04, 0.04, 0.045), 0.0, 0.85, pintura=False, sujeira=0.60),
    'ceramica': mats.material('CerâmicaLancador', (0.82, 0.84, 0.86), 0.0, 0.20, pintura=False, sujeira=0.25),
    'queimado': mats.material('QueimadoLancador', (0.12, 0.11, 0.11), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'listras': base3d.listras_mat(),
    'chao': mats.material('ChãoLancador', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0),
})

# Bobinas magnéticas de aceleração: ciano/azul elétrico pulsante
mats_bobina = []
bsdfs_bobina = []
for i in range(5):
    mb = emissivo_mat('BobinaAceleracao_%d' % i, (0.25, 0.75, 1.0), 1.0)
    base3d.M['bobina_%d' % i] = mb
    mats_bobina.append(mb)
    bsdfs_bobina.append(mb.node_tree.nodes['Principled BSDF'])

# Clarão do disparo eletromagnético
mat_clarao = emissivo_mat('ClaraoDisparo', (0.6, 0.85, 1.0), 0.0)
base3d.M['clarao'] = mat_clarao
bsdf_clarao = mat_clarao.node_tree.nodes['Principled BSDF']

# Cristal da cápsula-semente
mat_cristal_sem = emissivo_mat('CristalSemente', (0.55, 0.22, 1.0), 6.0)
base3d.M['cristal_sem'] = mat_cristal_sem


# ==================================================================
# 1. BASE ESTACIONÁRIA E ESTRUTURA DO BERÇO ('corpo')
# ==================================================================
bm_base = bmesh.new()
bm_aco = bmesh.new()
bm_ferro = bmesh.new()
bm_amarelo = bmesh.new()
bm_primer = bmesh.new()
bm_cobre = bmesh.new()
bm_borracha = bmesh.new()
bm_oleo = bmesh.new()
bm_listras = bmesh.new()

# Laje maciça de concreto de 2,90 × 2,90 m (±1,45 m) com chanfros de 0,38 m
L, H_LAJE, CH = 1.45, 0.16, 0.38
pts_laje = [
    (L - CH, L), (-(L - CH), L),
    (-L, L - CH), (-L, -(L - CH)),
    (-(L - CH), -L), (L - CH, -L),
    (L, -(L - CH)), (L, L - CH)
]
vf_inf = [bm_base.verts.new((x, y, 0.0)) for x, y in pts_laje]
vf_sup = [bm_base.verts.new((x, y, H_LAJE)) for x, y in pts_laje]
bm_base.faces.new(list(reversed(vf_inf)))
bm_base.faces.new(vf_sup)
for k in range(len(pts_laje)):
    bm_base.faces.new((vf_inf[k], vf_inf[(k + 1) % len(pts_laje)], vf_sup[(k + 1) % len(pts_laje)], vf_sup[k]))

# Sapatas de ancoragem com molas de recuo nos 4 cantos
for ang_c in (math.radians(45), math.radians(135), math.radians(225), math.radians(315)):
    rot_c = Matrix.Rotation(ang_c, 3, 'Z')
    pos_c = rot_c @ Vector((1.80, 0, H_LAJE / 2))
    caixa(bm_ferro, pos_c, (0.08, 0.35, H_LAJE + 0.02), rot_c)
    # Molas helicoidais duplas de aço
    for dy in (-0.11, 0.11):
        cil(bm_aco, pos_c + rot_c @ Vector((0, dy, H_LAJE / 2 + 0.03)), 0.035, 0.08, lados=10)
        cil(bm_ferro, pos_c + rot_c @ Vector((0, dy, H_LAJE / 2 + 0.075)), 0.045, 0.015, lados=10)

# Faixas de perigo nas 4 faces da laje
for ang_l in (0, PI / 2, PI, 3 * PI / 2):
    rl = Matrix.Rotation(ang_l, 3, 'Z')
    caixa(bm_listras, rl @ Vector((0, L + 0.004, H_LAJE / 2)), (1.70, 0.008, H_LAJE * 0.75), rl)

# BOCA DE ENTRADA DE ITENS AO SUL (ITEM_ENT_S1, Y = -1.45 m, X = 0.0, Z = 0.23 m)
# Calha com roletes e esteira
pos_boca_s = Vector((0.0, -1.35, 0.23))
caixa(bm_ferro, pos_boca_s + Vector((0, 0, -0.05)), (0.76, 0.28, 0.16))
caixa(bm_amarelo, pos_boca_s + Vector((0, 0.05, 0.12)), (0.80, 0.16, 0.32))
for ir, dy in enumerate((-1.45, -1.35, -1.25)):
    cil(bm_aco, Vector((0, dy, 0.23)), 0.024, 0.54, eixo=Vector((1, 0, 0)), lados=12)
caixa(bm_borracha, (0, -1.20, 0.28), (0.50, 0.015, 0.12))

# PEDESTAL CENTRAL E MANCAIS DO CANHÃO (Z = H_LAJE até Z = 1.35)
prisma_octo(bm_amarelo, (0, 0.10), 1.05, H_LAJE, 0.90)
toro(bm_aco, (0, 0.10, 0.52), 1.08, 0.016, nR=32, nr=6)
toro(bm_aco, (0, 0.10, 0.88), 1.08, 0.016, nR=32, nr=6)

# Dois grandes montantes/bochechas em viga de ferro fundido segurando o eixo horizontal do canhão
# Eixo do canhão em X = 0, Y = 0.10, Z = 1.45 m (inclinação padrão ~60° em relação ao solo)
X_MANCAL = 0.62
Z_EIXO_C = 1.45
for sx in (-1, 1):
    px = sx * X_MANCAL
    caixa(bm_ferro, (px, 0.10, (0.90 + Z_EIXO_C) / 2), (0.18, 0.56, Z_EIXO_C - 0.90 + 0.10))
    viga(bm_amarelo, (px, -0.16, 0.90), (px, 0.02, Z_EIXO_C), 0.12)
    viga(bm_amarelo, (px, 0.36, 0.90), (px, 0.18, Z_EIXO_C), 0.12)
    # Mancal circular maciço no topo
    cil(bm_ferro, (px, 0.10, Z_EIXO_C), 0.14, 0.18, eixo=Vector((1, 0, 0)), lados=18)
    toro(bm_aco, (px + sx * 0.09, 0.10, Z_EIXO_C), 0.12, 0.016, nR=18, nr=6,
         rot=Matrix.Rotation(math.radians(90), 3, 'Y'))
    for sy in (-0.08, 0.08):
        cil(bm_aco, (px, 0.10 + sy, Z_EIXO_C + 0.12), 0.014, 0.03, lados=6)

# Banco de capacitores pesados na traseira do pedestal (face Norte, Y = +0.85)
caixa(bm_ferro, (0, 0.88, 0.56), (1.10, 0.28, 0.62))
for ic in range(4):
    xc = -0.36 + ic * 0.24
    cil(bm_aco_escuro := bmesh.new(), (xc, 0.92, 0.94), 0.09, 0.28, lados=14)
    toro(bm_cobre, (xc, 0.92, 1.05), 0.092, 0.010, nR=14, nr=5)
    toro(bm_cobre, (xc, 0.92, 0.83), 0.092, 0.010, nR=14, nr=5)
    # Cabos pesados interligando os capacitores à torre
    mangueira(bm_borracha, [
        Vector((xc, 0.92, 1.08)),
        Vector((xc * 0.6, 0.55, 1.15)),
        Vector((xc * 0.3, 0.25, 1.30))
    ], 0.016)

# Manchas de graxa e fuligem na laje
for pos_m in ((0, -0.65), (0.45, 0.25), (-0.45, 0.25), (0, 0.70)):
    mancha(bm_oleo, pos_m, 0.28, H_LAJE + 0.002)

o_base = obj('corpo_base', bm_base, 'concreto')
o_aco = obj('corpo_aco', bm_aco, 'aco')
o_ferro = obj('corpo_ferro', bm_ferro, 'ferro')
o_amarelo = obj('corpo_amarelo', bm_amarelo, 'amarelo')
o_primer = obj('corpo_primer', bm_primer, 'primer')
o_cobre = obj('corpo_cobre', bm_cobre, 'cobre')
o_borracha = obj('corpo_borracha', bm_borracha, 'borracha')
o_cap = obj('corpo_capacitores', bm_aco_escuro, 'aco_escuro')
o_oleo = obj('corpo_oleo', bm_oleo, 'oleo')
o_listras = obj('corpo_listras', bm_listras, 'listras')

suavizar(o_base)
suavizar(o_amarelo)
suavizar(o_primer)


# ==================================================================
# 2. CANHÃO ACELERADOR E ELEVAÇÃO ('canhao')
# ==================================================================
# Modelado com o eixo apontando para frente com inclinação de lançamento (62° sobre a horizontal)
# Pivô em (0, 0.10, Z_EIXO_C)
ANG_DISPARO = math.radians(62)
rot_disparo = Matrix.Rotation(ANG_DISPARO, 3, 'X')
DIR_DISPARO = rot_disparo @ Vector((0, 1, 0))  # Vetor ao longo do tubo do canhão

bm_can_fe = bmesh.new()
bm_can_am = bmesh.new()
bm_can_ac = bmesh.new()
bm_can_co = bmesh.new()
bm_can_qu = bmesh.new()

# Eixo horizontal transversal de suporte
cil(bm_can_ac, (0, 0, 0), 0.09, X_MANCAL * 2 + 0.16, eixo=Vector((1, 0, 0)), lados=18)

# Berço central e culatra do canhão (atrás do pivô, alongado ao longo de -DIR)
COMPRIMENTO_TUBO = 3.40
L_CULATRA = 1.05
# Caixa da culatra em ferro fundido pesado
caixa(bm_can_fe, -DIR_DISPARO * (L_CULATRA / 2), (0.74, 0.74, L_CULATRA), rot_disparo)
# Anéis e travas de culatra
toro(bm_can_ac, -DIR_DISPARO * 0.10, 0.38, 0.020, nR=24, nr=6, rot=rot_disparo)
toro(bm_can_ac, -DIR_DISPARO * 0.65, 0.38, 0.020, nR=24, nr=6, rot=rot_disparo)

# TUBO ACELERADOR PRINCIPAL (Cilindro longo de aço de z=0 até a boca)
# Raio externo 0.32 m, furo interno calibre 0.22 m
P_BOCA = DIR_DISPARO * (COMPRIMENTO_TUBO - L_CULATRA / 2)
cil(bm_can_am, DIR_DISPARO * (COMPRIMENTO_TUBO / 2 - 0.20), 0.32, COMPRIMENTO_TUBO - 0.40,
    eixo=DIR_DISPARO, lados=24)
# Calibre interno vazado (cilindro queimado)
cil(bm_can_qu, P_BOCA - DIR_DISPARO * 0.35, 0.22, 0.70, eixo=DIR_DISPARO, lados=20)

# 5 BOBINAS TOROIDAIS DE ACELERAÇÃO ELETROMAGNÉTICA EM COBRE
objs_bobinas = []
eixo_u = DIR_DISPARO.orthogonal().normalized()
eixo_v = DIR_DISPARO.cross(eixo_u).normalized()

for i in range(5):
    dist_b = 0.35 + i * 0.44
    pos_bob = DIR_DISPARO * dist_b
    bm_bob = bmesh.new()
    # Toro principal da bobina de cobre
    toro(bm_can_co, pos_bob, 0.36, 0.035, nR=24, nr=6, rot=rot_disparo)
    # Aletas radiais de dissipação em volta do tubo
    for kb in range(8):
        ab = kb * 2 * PI / 8
        d_rad = eixo_u * math.cos(ab) + eixo_v * math.sin(ab)
        pos_aleta = pos_bob + d_rad * 0.38
        caixa(bm_can_ac, pos_aleta, (0.008, 0.06, 0.12), rot_disparo)
    # Anel luminoso interno emissor da bobina
    toro(bm_bob, pos_bob, 0.33, 0.012, nR=20, nr=5, rot=rot_disparo)
    o_b = obj('canhao_bobina_%d' % i, bm_bob, 'bobina_%d' % i)
    objs_bobinas.append(o_b)

# FREIO DE BOCA COM RASGOS DE DESCOMPRESSÃO DE PLASMA (Na boca do canhão)
cil(bm_can_fe, P_BOCA - DIR_DISPARO * 0.12, 0.36, 0.34, eixo=DIR_DISPARO, lados=20)
# Rasgos laterais de descompressão (aberturas angulares)
for kr in (-1, 1):
    caixa(bm_can_qu, P_BOCA + Vector((kr * 0.30, 0, 0)), (0.16, 0.10, 0.22), rot_disparo)
toro(bm_can_ac, P_BOCA, 0.37, 0.020, nR=24, nr=6, rot=rot_disparo)

# Anel emissivo de clarão na boca do canhão
bm_clar = bmesh.new()
toro(bm_clar, P_BOCA + DIR_DISPARO * 0.02, 0.23, 0.025, nR=20, nr=6, rot=rot_disparo)
o_clarao = obj('canhao_clarao', bm_clar, 'clarao')

# PONTOS DE ANCORAGEM DOS PISTÕES DE RECUO NO TUBO (Colar em DIR * 0.25)
POS_COLAR_PISTAO = DIR_DISPARO * 0.25
for sx in (-0.42, 0.42):
    caixa(bm_can_fe, POS_COLAR_PISTAO + Vector((sx, 0, 0)), (0.08, 0.08, 0.08))
    cil(bm_can_ac, POS_COLAR_PISTAO + Vector((sx, 0, 0)), 0.020, 0.10, eixo=Vector((1, 0, 0)), lados=10)

o_can_fe = obj('canhao_ferro', bm_can_fe, 'ferro')
o_can_am = obj('canhao_amarelo', bm_can_am, 'amarelo')
o_can_ac = obj('canhao_aco', bm_can_ac, 'aco')
o_can_co = obj('canhao_cobre', bm_can_co, 'cobre')
o_can_qu = obj('canhao_queimado', bm_can_qu, 'queimado')

suavizar(o_can_am)
suavizar(o_can_co)
suavizar(o_can_ac)

# Empty pai do conjunto de elevação do canhão
empty_canhao = bpy.data.objects.new('canhao', None)
empty_canhao.empty_display_type = 'ARROWS'
empty_canhao.location = Vector((0, 0.10, Z_EIXO_C))
sc.collection.objects.link(empty_canhao)

for o in (o_can_fe, o_can_am, o_can_ac, o_can_co, o_can_qu, o_clarao) + tuple(objs_bobinas):
    o.parent = empty_canhao


# ==================================================================
# 3. PISTÕES DE ABSORÇÃO DE RECUO
# ==================================================================
# Par de pistões telescópicos: camisa ancorada na base (Y = -0.45, Z = 0.90), haste no canhão
pistao_recuo = []
for idx, sx in enumerate((-0.42, 0.42)):
    p_base_p = Vector((sx, -0.45, 0.90))
    bm_cam = bmesh.new()
    cil(bm_cam, (0, 0, 0.24), 0.045, 0.48, lados=14)
    cil(bm_cam, (0, 0, 0), 0.055, 0.06, eixo=Vector((1, 0, 0)), lados=12)
    toro(bm_cam, (0, 0, 0.48), 0.050, 0.010, nR=14, nr=5)
    o_cam = obj('pistao%d_camisa' % idx, bm_cam, 'amarelo')
    suavizar(o_cam)

    bm_has = bmesh.new()
    cil(bm_has, (0, 0, 0.30), 0.028, 0.60, lados=12)
    cil(bm_has, (0, 0, 0.60), 0.042, 0.06, eixo=Vector((1, 0, 0)), lados=12)
    o_has = obj('pistao%d_haste' % idx, bm_has, 'cromo')
    suavizar(o_has)

    pistao_recuo.append((sx, p_base_p, o_cam, o_has))


# ==================================================================
# 4. A CÁPSULA-SEMENTE (Projétil autônomo modelado)
# ==================================================================
bm_sem_ac = bmesh.new()
bm_sem_cr = bmesh.new()
# Ogiva cônica aerodinâmica (diâmetro 0.38 m, comprimento 0.85 m)
cil(bm_sem_ac, (0, 0, 0.30), 0.19, 0.60, lados=18, r2=0.08)
cil(bm_sem_ac, (0, 0, 0.04), 0.19, 0.08, lados=18)
# Anéis de obturação de cobre
toro(bm_sem_ac, (0, 0, 0.06), 0.192, 0.008, nR=18, nr=4)
toro(bm_sem_ac, (0, 0, 0.14), 0.192, 0.008, nR=18, nr=4)
# Cristal-semente visível na ponta da ogiva
hexa_cristal(bm_sem_cr, (0, 0, 0.68), 0.055, 0.14, ponta_sup=0.08)

o_sem_ac = obj('semente_corpo', bm_sem_ac, 'aco')
o_sem_cr = obj('semente_cristal', bm_sem_cr, 'cristal_sem')
suavizar(o_sem_ac)

empty_semente = bpy.data.objects.new('semente', None)
empty_semente.empty_display_type = 'SPHERE'
sc.collection.objects.link(empty_semente)
o_sem_ac.parent = empty_semente
o_sem_cr.parent = empty_semente


# ==================================================================
# 5. ILUMINAÇÃO, EFEITOS E ANIMAÇÃO
# ==================================================================
luz_disparo_d = bpy.data.lights.new('EFEITO_LuzDisparo', 'POINT')
luz_disparo_d.color = (0.35, 0.75, 1.0)
luz_disparo_d.energy = 0.0
luz_disparo_d.shadow_soft_size = 0.15
luz_disparo = bpy.data.objects.new('EFEITO_LuzDisparo', luz_disparo_d)
sc.collection.objects.link(luz_disparo)
luz_disparo.parent = empty_canhao
luz_disparo.location = P_BOCA + DIR_DISPARO * 0.10

# Chão e sol industrial
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (16, 16, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.2
sol_d.angle = math.radians(2.2)
o_sol = bpy.data.objects.new('Sol', sol_d)
sc.collection.objects.link(o_sol)
o_sol.rotation_euler = (math.radians(52), 0, math.radians(-35))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1.0)
bg.inputs['Strength'].default_value = 0.55


# ------------------------------------------------------------------ ANIMAÇÃO DE 96 QUADROS (4 s)
# Quadro 50 = DISPARO
FR_TIRO = 50

for q in range(1, QUADROS + 1):
    sc.frame_set(q)

    # 1. Recuo do canhão acelerador
    # Em repouso: recuo = 0; no tiro: recua bruscamente 0.22 m ao longo de -DIR e volta com amortecimento
    if q < FR_TIRO:
        recuo = 0.0
    elif q == FR_TIRO:
        recuo = 0.24
    elif q < FR_TIRO + 8:
        # Recuperação pneumática rápida
        recuo = 0.24 * math.exp(-(q - FR_TIRO) * 0.35)
    else:
        recuo = 0.0

    p_canhao = Vector((0, 0.10, Z_EIXO_C)) - DIR_DISPARO * recuo
    empty_canhao.location = p_canhao
    empty_canhao.keyframe_insert('location', frame=q)

    # 2. Pistões de absorção de recuo acompanhando o canhão
    for sx, p_base_p, o_cam, o_has in pistao_recuo:
        p_topo_p = p_canhao + POS_COLAR_PISTAO + Vector((sx, 0, 0))
        v_eixo = p_topo_p - p_base_p
        dir_p = v_eixo.normalized()
        quat_p = dir_p.to_track_quat('Z', 'Y')

        o_cam.location = p_base_p
        o_cam.rotation_mode = 'QUATERNION'
        o_cam.rotation_quaternion = quat_p
        o_cam.keyframe_insert('location', frame=q)
        o_cam.keyframe_insert('rotation_quaternion', frame=q)

        o_has.location = p_topo_p - dir_p * 0.60
        o_has.rotation_mode = 'QUATERNION'
        o_has.rotation_quaternion = quat_p
        o_has.keyframe_insert('location', frame=q)
        o_has.keyframe_insert('rotation_quaternion', frame=q)

    # 3. Cascata de ativação das bobinas eletromagnéticas antes do disparo (quadros 36 a 49)
    for ib in range(5):
        fr_bob = 36 + ib * 2.5
        if fr_bob <= q <= FR_TIRO:
            f_bob = 28.0
        elif FR_TIRO < q < FR_TIRO + 10:
            f_bob = 28.0 * math.exp(-(q - FR_TIRO) * 0.40)
        else:
            f_bob = 0.8
        bsdfs_bobina[ib].inputs['Emission Strength'].default_value = f_bob
        bsdfs_bobina[ib].inputs['Emission Strength'].keyframe_insert('default_value', frame=q)

    # 4. Clarão eletromagnético no disparo
    if q == FR_TIRO:
        f_tiro = 45.0
    elif q == FR_TIRO + 1:
        f_tiro = 18.0
    elif q == FR_TIRO + 2:
        f_tiro = 5.0
    else:
        f_tiro = 0.0

    bsdf_clarao.inputs['Emission Strength'].default_value = f_tiro
    bsdf_clarao.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    luz_disparo_d.energy = f_tiro * 3.5
    luz_disparo_d.keyframe_insert('energy', frame=q)

    # 5. Movimento da cápsula-semente
    # Antes do tiro: dentro do tubo/culatra. No tiro (50): voa ao longo de DIR_DISPARO!
    quat_sem = DIR_DISPARO.to_track_quat('Z', 'Y')
    empty_semente.rotation_mode = 'QUATERNION'
    empty_semente.rotation_quaternion = quat_sem
    if q < FR_TIRO:
        # Na culatra esperando o disparo
        p_sem = p_canhao + DIR_DISPARO * 0.20
    else:
        # Voo supersônico suborbital
        dist_voo = (q - FR_TIRO) * 1.85
        p_sem = p_canhao + P_BOCA + DIR_DISPARO * dist_voo

    empty_semente.location = p_sem
    empty_semente.keyframe_insert('location', frame=q)
    empty_semente.keyframe_insert('rotation_quaternion', frame=q)


# ==================================================================
# 6. CONFIGURAÇÃO DE CÂMERA E MODOS
# ==================================================================
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
sc.view_settings.exposure = -0.4

cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente=34):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = Vector((0.0, 0.15, 1.65))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(FR_TIRO)  # Momento exato do disparo: clarão na boca, cápsula ejetada e bobinas em chamas

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.5), (210, 2.7), (120, 2.8), (30, 2.3))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 6.2, math.sin(a) * 6.2, alt - ALVO.z))
        mirar(pos_cam, ALVO, 34)
        sc.render.filepath = os.path.join(AQUI, 'lancador_sementes_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: boca do canhão com clarão, cápsula-semente e freio de boca
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(FR_TIRO)
        mirar(Vector((1.65, 0.35, 4.25)), Vector((0.0, 1.45, 3.95)), 36)
        sc.render.filepath = os.path.join(AQUI, 'lancador_sementes_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(FR_TIRO)
    mirar(ALVO + Vector((3.6, -4.2, 2.0)), ALVO, 34)
    sc.render.filepath = os.path.join(AQUI, 'lancador_sementes_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('LANCADOR_SEMENTES ok (%d tris)' % tot_tri)
