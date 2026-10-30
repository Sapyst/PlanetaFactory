"""Estudo isolado (fora do jogo): SENSOR DE VARREDURA da IA, 2×2 tiles.
Sem bocas de itens ou fluidos (estrutura de sensoriamento, radar e cartografia).
Revela 1 chunk/min até 6 chunks no mapa e marca ninhos de aranha (com a pesquisa 'cartografia', até 16 chunks).
Estilo: máquina de alta tecnologia da IA suportada por mecânica industrial pesada, gasta e sem humanos.
- Laje de concreto 1,90 × 1,90 m com cantos chanfrados, cantoneiras de aço e chumbadores; listras de aviso nas bordas;
  manchas de óleo sob a coroa; eletrodutos pesados com flanges e caixa de terminais elétricos; haste de aterramento de cobre.
- Pedestal estacionário octogonal de chapas de aço rebitadas, aletas de resfriamento na face norte, painel frontal com barramento
  de 8 LEDs indicadores de setor de varredura, motor elétrico blindado com redutor e pinhão dentado.
- Coroa dentada usinada com anel de retenção e ranhura de esferas.
- Conjunto móvel azimutal (giro): mesa giratória circular, garfo de sustentação (yoke) de dois montantes em viga I com nervuras
  reforçadas e acabamento amarelo industrial gasto e lascado, mancais bipartidos com parafusos de flange em z = 1,45 m.
- Conjunto articulado de elevação (antena): chassi de RF aletado, grande refletor parabólico de malha grelhada (1,48 × 0,94 m)
  com anel perimetral tubular e treliça traseira espacial; alimentador frontal em tripé tubular com corneta cônica de cobre,
  núcleo de cristal lapidado pulsando energia azul-violeta no ponto focal e guia de onda retangular curvo com flanges; painel
  phased array secundário no topo com 18 domos emissores cerâmicos; contrapesos duplos de ferro fundido torneado.
- Par de pistões telescópicos de elevação (camisa ancorada no garfo, haste na armação da antena) com mangueiras de pressão.
- Animação em laço de 96 quadros (4 s a 24 qps): rotação azimutal contínua de 360° em Z, elevação oscilatória suave da antena
  (12° a 26°), pistões acompanhando o movimento com precisão geométrica, cristal focalizador emitindo 4 pulsos de radar
  por ciclo com relaxamento rápido, LEDs de diagnóstico percorrendo os setores cardeais e pinhão do motor girando sincronizado.
Uso: blender -b --python estudo_sensor_varredura.py -- foto
     blender -b --python estudo_sensor_varredura.py -- nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(63)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades de modelagem
def suavizar(o, tudo=False):
    """Sombra suave nas faces quad (tubos e curvas continuam nítidos nas tampas)."""
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
    """Anel tubular contínuo."""
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


def curva_cotovelo(bm, p, r, lados=14):
    """Esfera para concordância suave em cotovelos de canos."""
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano_rigido(bm, bf, pts, r, flange=True):
    """Cano com curvas esféricas e anéis de flange nos nós."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 14)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.12:
            for c in (a + u * 0.04, b - u * 0.04):
                tubo(bf, c - u * 0.007, c + u * 0.007, r * 1.55, 14)
    for c in pts[1:-1]:
        curva_cotovelo(bm, c, r, 14)


def prisma_octo(bm, c, ap, z0, z1):
    """Prisma octogonal alinhado aos eixos."""
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


def hexa_cristal(bm, c, r, h, ponta=0.0):
    """Prisma hexagonal com ponta lapidada piramidal."""
    c = Vector(c)
    z0, z1 = c.z - h / 2, c.z + h / 2
    vs0 = [bm.verts.new((c.x + r * math.cos(k * PI / 3), c.y + r * math.sin(k * PI / 3), z0)) for k in range(6)]
    vs1 = [bm.verts.new((c.x + r * math.cos(k * PI / 3), c.y + r * math.sin(k * PI / 3), z1)) for k in range(6)]
    bm.faces.new(list(reversed(vs0)))
    if ponta > 0:
        vp = bm.verts.new((c.x, c.y, z1 + ponta))
        for k in range(6):
            bm.faces.new((vs1[k], vs1[(k + 1) % 6], vp))
    else:
        bm.faces.new(vs1)
    for k in range(6):
        bm.faces.new((vs0[k], vs0[(k + 1) % 6], vs1[(k + 1) % 6], vs1[k]))


# ------------------------------------------------------------------ materiais
def emissivo_mat(nome, cor, forca_inicial=0.0):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1.0)
    b.inputs['Emission Color'].default_value = (*cor, 1.0)
    b.inputs['Emission Strength'].default_value = forca_inicial
    b.inputs['Roughness'].default_value = 0.2
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.75, 0.50, 0.06), 0.0, 0.40, desgaste=0.85, sujeira=0.75),
    'amarelo_chapa': mats.material('AmareloChapa', (0.72, 0.48, 0.07), 0.0, 0.45, desgaste=0.90, sujeira=0.80),
    'grafite': mats.material('Grafite', (0.08, 0.085, 0.09), 0.0, 0.48, desgaste=0.65, sujeira=0.70),
    'aco': mats.material('Aço', (0.44, 0.45, 0.46), 1.0, 0.42, pintura=False, ferrugem=0.55, sujeira=0.70, escovado=True),
    'aco_escuro': mats.material('AçoEscuro', (0.22, 0.23, 0.24), 1.0, 0.50, pintura=False, ferrugem=0.75, sujeira=0.85),
    'cromo': mats.material('Cromo', (0.86, 0.87, 0.89), 1.0, 0.12, pintura=False, sujeira=0.20),
    'cobre': mats.material('Cobre', (0.82, 0.42, 0.22), 1.0, 0.32, pintura=False, ferrugem=0.35, sujeira=0.65),
    'ferro': mats.material('FerroFundido', (0.10, 0.095, 0.09), 0.8, 0.68, pintura=False, ferrugem=0.85, sujeira=0.90),
    'concreto': mats.material('Concreto', (0.34, 0.33, 0.31), 0.0, 0.90, sujeira=0.75, desgaste=0.20),
    'oleo': mats.material('Óleo', (0.012, 0.010, 0.008), 0.0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'po': mats.material('Pó', (0.18, 0.16, 0.14), 0.0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'ceramica': mats.material('Cerâmica', (0.70, 0.72, 0.75), 0.0, 0.25, pintura=False, sujeira=0.30),
    'borracha': mats.material('Borracha', (0.04, 0.04, 0.045), 0.0, 0.85, pintura=False, sujeira=0.60),
    'listras': base3d.listras_mat(),
    'chao': mats.material('Chão', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0),
})

# Cristal da IA: violeta azulado de alta energia com pulso
mat_cristal = emissivo_mat('CristalSensor', (0.42, 0.18, 0.95), 3.0)
base3d.M['cristal'] = mat_cristal
bsdf_cristal = mat_cristal.node_tree.nodes['Principled BSDF']

# LEDs de diagnóstico de setor (8 LEDs)
mats_led = []
bsdfs_led = []
for i in range(8):
    m_led = emissivo_mat('LED_Setor_%d' % i, (0.15, 0.85, 0.35), 0.5)
    base3d.M['led_%d' % i] = m_led
    mats_led.append(m_led)
    bsdfs_led.append(m_led.node_tree.nodes['Principled BSDF'])


# ==================================================================
# 1. BASE ESTACIONÁRIA ('corpo')
# ==================================================================
bm_base = bmesh.new()
bm_aco = bmesh.new()
bm_ferro = bmesh.new()
bm_amarelo = bmesh.new()
bm_cobre = bmesh.new()

# Laje de concreto de 1,90 × 1,90 m com chanfros de 0,22 m nos 4 cantos
L, H_LAJE, CH = 0.94, 0.12, 0.24
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

# Cantoneiras de ferro de ancoragem nos cantos chanfrados com chumbadores
for ang_c in (math.radians(45), math.radians(135), math.radians(225), math.radians(315)):
    rot_c = Matrix.Rotation(ang_c, 3, 'Z')
    pos_c = rot_c @ Vector((1.12, 0, H_LAJE / 2))
    caixa(bm_ferro, pos_c, (0.06, 0.22, H_LAJE + 0.02), rot_c)
    # Porca e chumbador hexagonal
    cil(bm_aco, pos_c + Vector((0, 0, H_LAJE / 2 + 0.015)), 0.022, 0.03, lados=6)
    cil(bm_ferro, pos_c + Vector((0, 0, H_LAJE / 2 + 0.005)), 0.032, 0.01, lados=12)

# Degrau intermediário octogonal de concreto
prisma_octo(bm_base, (0, 0), 0.76, H_LAJE, H_LAJE + 0.06)

# Pedestal metálico principal octogonal (Z = 0,18 até Z = 0,78)
Z_PED_0, Z_PED_1 = H_LAJE + 0.06, 0.78
prisma_octo(bm_amarelo, (0, 0), 0.58, Z_PED_0, Z_PED_1)

# Frisos e anéis de reforço no pedestal
for z_an in (Z_PED_0 + 0.04, 0.50, Z_PED_1 - 0.04):
    toro(bm_aco, (0, 0, z_an), 0.60, 0.016, nR=20, nr=6)

# Painel frontal de diagnóstico da IA (face Sul, Y = -0.58)
caixa(bm_ferro, (0.0, -0.59, 0.48), (0.42, 0.04, 0.28))
caixa(bm_aco, (0.0, -0.615, 0.48), (0.38, 0.01, 0.24))

# Barramento de 8 LEDs de diagnóstico (arco ou linha no painel)
bm_leds = [bmesh.new() for _ in range(8)]
for i in range(8):
    x_led = -0.14 + (i / 7.0) * 0.28
    cil(bm_leds[i], (x_led, -0.622, 0.54), 0.012, 0.008, eixo=Vector((0, -1, 0)), lados=8)
    # Anel metálico ao redor do LED
    toro(bm_aco, (x_led, -0.62, 0.54), 0.016, 0.004, nR=10, nr=4, rot=Matrix.Rotation(math.radians(90), 3, 'X'))

# Mostrador matricial / fita de status abaixo dos LEDs
caixa(bm_ferro, (0.0, -0.622, 0.43), (0.30, 0.008, 0.08))

# Aletas de resfriamento traseiras (face Norte, Y = +0.58)
caixa(bm_ferro, (0.0, 0.59, 0.48), (0.48, 0.04, 0.32))
for i in range(8):
    x_aleta = -0.18 + i * 0.052
    caixa(bm_aco, (x_aleta, 0.63, 0.48), (0.008, 0.06, 0.30))

# Eletrodutos pesados entrando pela borda Sul e Leste com caixa de passagem e prensa-cabos
pts_duto_sul = [Vector((0.52, -0.96, 0.04)), Vector((0.52, -0.72, 0.04)),
                Vector((0.52, -0.52, 0.28)), Vector((0.36, -0.52, 0.35)),
                Vector((0.26, -0.52, 0.35))]
cano_rigido(bm_aco, bm_ferro, pts_duto_sul, 0.024)
# Caixa de entrada e prensa-cabo no pedestal
caixa(bm_ferro, (0.24, -0.53, 0.35), (0.06, 0.08, 0.10))
cil(bm_aco, (0.27, -0.52, 0.35), 0.034, 0.02, eixo=Vector((1, 0, 0)), lados=10)

pts_duto_leste = [Vector((0.96, 0.25, 0.04)), Vector((0.72, 0.25, 0.04)),
                 Vector((0.54, 0.25, 0.28))]
cano_rigido(bm_aco, bm_ferro, pts_duto_leste, 0.020)

# Caixa de passagem blindada na lateral Leste
caixa(bm_ferro, (0.54, 0.25, 0.32), (0.08, 0.16, 0.16))

# Barramento de aterramento com fita de cobre e haste no concreto
caixa(bm_cobre, (0.45, -0.70, 0.13), (0.018, 0.25, 0.005))
cil(bm_cobre, (0.45, -0.80, 0.08), 0.014, 0.12, lados=8)
cil(bm_ferro, (0.45, -0.80, 0.135), 0.022, 0.015, lados=6)

# Motor elétrico de giro no quadrante Sudeste do pedestal
POS_MOT = Vector((0.36, -0.36, Z_PED_1 - 0.12))
caixa(bm_ferro, POS_MOT - Vector((0, 0, 0.10)), (0.16, 0.16, 0.08))
cil(bm_amarelo, POS_MOT, 0.075, 0.22, lados=14)
# Aletas do motor
for k in range(6):
    ang_m = k * PI / 3
    rot_m = Matrix.Rotation(ang_m, 3, 'Z')
    caixa(bm_aco, POS_MOT + rot_m @ Vector((0.082, 0, 0)), (0.012, 0.005, 0.20), rot_m)
# Caixa de redução e eixo do pinhão de giro
cil(bm_ferro, POS_MOT + Vector((0, 0, 0.14)), 0.065, 0.08, lados=12)
POS_PINHAO = POS_MOT + Vector((0, 0, 0.21))

# Coroa dentada fixa no topo do pedestal (Z = 0.78 a 0.85)
cil(bm_ferro, (0, 0, 0.805), 0.56, 0.05, lados=24)
toro(bm_aco, (0, 0, 0.835), 0.54, 0.016, nR=24, nr=6)
toro(bm_aco, (0, 0, 0.775), 0.54, 0.016, nR=24, nr=6)
# Dentes da coroa
for k in range(32):
    ang_d = k * 2 * PI / 32
    rd = Matrix.Rotation(ang_d, 3, 'Z')
    caixa(bm_aco, rd @ Vector((0.555, 0, 0.805)), (0.018, 0.024, 0.045), rd)

# Manchas de óleo e graxa na laje
bm_oleo = bmesh.new()
mancha(bm_oleo, (0.35, -0.32), 0.18, H_LAJE + 0.002)
mancha(bm_oleo, (0.0, 0.0), 0.35, H_LAJE + 0.001)
mancha(bm_oleo, (-0.25, 0.30), 0.14, H_LAJE + 0.002)

# Faixas de aviso (ladrilhos com listras) nas 4 faces retas da laje de concreto
bm_listras = bmesh.new()
for ang_l in (0, PI / 2, PI, 3 * PI / 2):
    rl = Matrix.Rotation(ang_l, 3, 'Z')
    caixa(bm_listras, rl @ Vector((0, L + 0.004, H_LAJE / 2)), (1.10, 0.008, H_LAJE * 0.75), rl)

# Cria os objetos do corpo fixo
o_base = obj('corpo_base', bm_base, 'concreto')
o_aco = obj('corpo_aco', bm_aco, 'aco')
o_ferro = obj('corpo_ferro', bm_ferro, 'ferro')
o_amarelo = obj('corpo_amarelo', bm_amarelo, 'amarelo')
o_cobre = obj('corpo_cobre', bm_cobre, 'cobre')
o_oleo = obj('corpo_oleo', bm_oleo, 'oleo')
o_listras = obj('corpo_listras', bm_listras, 'listras')
suavizar(o_base)
suavizar(o_amarelo)
suavizar(o_aco)

objs_led = []
for i in range(8):
    objs_led.append(obj('corpo_led_%d' % i, bm_leds[i], 'led_%d' % i))


# ==================================================================
# 2. CONJUNTO MÓVEL AZIMUTAL ('giro')
# ==================================================================
bm_giro_amarelo = bmesh.new()
bm_giro_ferro = bmesh.new()
bm_giro_aco = bmesh.new()

# Mesa giratória (disco sobre a coroa dentada, centro em Z = 0,84)
Z_MESA = 0.85
cil(bm_giro_ferro, (0, 0, Z_MESA), 0.52, 0.04, lados=24)
toro(bm_giro_aco, (0, 0, Z_MESA + 0.02), 0.50, 0.016, nR=20, nr=5)

# Yoke / Garfo de sustentação: 2 montantes verticais em X = -0.42 e X = +0.42
X_YOKE = 0.42
Z_MANCAL = 1.45
for sx in (-1, 1):
    px = sx * X_YOKE
    # Sapata reforçada do montante
    caixa(bm_giro_ferro, (px, 0.0, Z_MESA + 0.04), (0.18, 0.36, 0.05))
    # Coluna principal em perfil I (viga reforçada)
    viga(bm_giro_amarelo, (px, 0.0, Z_MESA + 0.05), (px, 0.0, Z_MANCAL), 0.12)
    # Flanges laterais do perfil I
    caixa(bm_giro_amarelo, (px - 0.06, 0.0, (Z_MESA + Z_MANCAL) / 2), (0.018, 0.22, Z_MANCAL - Z_MESA))
    caixa(bm_giro_amarelo, (px + 0.06, 0.0, (Z_MESA + Z_MANCAL) / 2), (0.018, 0.22, Z_MANCAL - Z_MESA))
    # Nervuras diagonais de reforço na base do montante
    viga(bm_giro_ferro, (px, -0.15, Z_MESA + 0.04), (px, -0.04, Z_MESA + 0.26), 0.035)
    viga(bm_giro_ferro, (px, 0.15, Z_MESA + 0.04), (px, 0.04, Z_MESA + 0.26), 0.035)
    # Mancal bipartido no topo (apoio do eixo de elevação)
    cil(bm_giro_ferro, (px, 0.0, Z_MANCAL), 0.09, 0.14, eixo=Vector((1, 0, 0)), lados=14)
    toro(bm_giro_aco, (px + sx * 0.07, 0.0, Z_MANCAL), 0.08, 0.012, nR=12, nr=4, rot=Matrix.Rotation(math.radians(90), 3, 'Y'))
    # Parafusos do mancal
    for sy in (-0.055, 0.055):
        cil(bm_giro_aco, (px, sy, Z_MANCAL + 0.08), 0.012, 0.03, lados=6)

# Travessa de união inferior entre os montantes do garfo
caixa(bm_giro_ferro, (0.0, 0.0, Z_MESA + 0.08), (X_YOKE * 2 - 0.10, 0.20, 0.06))

# Olhetes de fixação da base dos pistões de elevação (no garfo, em Y = -0.16)
for sx in (-0.24, 0.24):
    caixa(bm_giro_ferro, (sx, -0.16, Z_MESA + 0.12), (0.05, 0.08, 0.08))
    cil(bm_giro_aco, (sx, -0.16, Z_MESA + 0.12), 0.016, 0.07, eixo=Vector((1, 0, 0)), lados=10)

# Caixa de engrenagem / redutor de giro acoplado ao pinhão (gira com a mesa)
caixa(bm_giro_ferro, (0.36, -0.36, Z_MESA), (0.12, 0.12, 0.06))

# Pinhão dentado de giro (engrenado na coroa fixa)
bm_pinhao = bmesh.new()
cil(bm_pinhao, POS_PINHAO, 0.07, 0.045, lados=20)
for k in range(12):
    ang_p = k * 2 * PI / 12
    rp = Matrix.Rotation(ang_p, 3, 'Z')
    caixa(bm_pinhao, POS_PINHAO + rp @ Vector((0.068, 0, 0)), (0.014, 0.018, 0.045), rp)
o_pinhao = obj('giro_pinhao', bm_pinhao, 'aco')

o_giro_am = obj('giro_amarelo', bm_giro_amarelo, 'amarelo')
o_giro_fe = obj('giro_ferro', bm_giro_ferro, 'ferro')
o_giro_ac = obj('giro_aco', bm_giro_aco, 'aco')
suavizar(o_giro_am)
suavizar(o_giro_fe)

# Empty pai do conjunto giratório
empty_giro = bpy.data.objects.new('giro', None)
empty_giro.empty_display_type = 'ARROWS'
empty_giro.location = Vector((0, 0, 0))
sc.collection.objects.link(empty_giro)

for o in (o_giro_am, o_giro_fe, o_giro_ac, o_pinhao):
    o.parent = empty_giro


# ==================================================================
# 3. CONJUNTO BASCULANTE DE ELEVAÇÃO ('antena')
# ==================================================================
# Modelado na posição de repouso com eixo horizontal alinhado a X em (0, 0, Z_MANCAL)
bm_ant_am = bmesh.new()
bm_ant_ac = bmesh.new()
bm_ant_fe = bmesh.new()
bm_ant_co = bmesh.new()
bm_ant_ce = bmesh.new()
bm_ant_cr = bmesh.new()

# Eixo transversal horizontal passando pelos mancais
cil(bm_ant_ac, (0, 0, 0), 0.065, X_YOKE * 2 + 0.20, eixo=Vector((1, 0, 0)), lados=20)

# Chassi central de montagem da antena (caixa fundida com aletas)
caixa(bm_ant_fe, (0, 0.04, 0.0), (0.42, 0.26, 0.26))
for i in range(8):
    y_al = -0.06 + i * 0.03
    caixa(bm_ant_ac, (0, y_al, 0.14), (0.40, 0.008, 0.035))

# Ancoragem dos pistões de elevação na armação da antena (em Y = -0.18, Z = -0.14)
for sx in (-0.24, 0.24):
    caixa(bm_ant_fe, (sx, -0.18, -0.14), (0.05, 0.08, 0.08))
    cil(bm_ant_ac, (sx, -0.18, -0.14), 0.016, 0.07, eixo=Vector((1, 0, 0)), lados=10)

# Braços de contrapeso estendidos para trás e para baixo (Y = -0.42, Z = -0.28)
for sx in (-0.22, 0.22):
    viga(bm_ant_fe, (sx, 0.0, 0.0), (sx, -0.40, -0.26), 0.06)
    # Cilindro pesado de contrapeso em ferro fundido
    cil(bm_ant_fe, (sx, -0.42, -0.28), 0.11, 0.16, eixo=Vector((1, 0, 0)), lados=18)
    toro(bm_ant_ac, (sx, -0.42, -0.28), 0.10, 0.015, nR=18, nr=6, rot=Matrix.Rotation(math.radians(90), 3, 'Y'))

# Barra estabilizadora entre os dois contrapesos
tubo(bm_ant_fe, (-0.22, -0.42, -0.28), (0.22, -0.42, -0.28), 0.04, lados=12)

# Treliça traseira espacial da antena parabólica (tubos em X e diamante)
pts_anel_trelissa = [
    Vector((-0.68, 0.12, 0.42)), Vector((0.68, 0.12, 0.42)),
    Vector((-0.68, 0.12, -0.38)), Vector((0.68, 0.12, -0.38)),
    Vector((0.0, 0.16, 0.46)), Vector((0.0, 0.16, -0.42)),
    Vector((-0.72, 0.10, 0.0)), Vector((0.72, 0.10, 0.0))
]
for pt in pts_anel_trelissa:
    tubo(bm_ant_ac, (0, 0.08, 0.0), pt, 0.018, lados=8)

for a, b in zip(pts_anel_trelissa, pts_anel_trelissa[1:] + [pts_anel_trelissa[0]]):
    tubo(bm_ant_ac, a, b, 0.016, lados=8)

# REFLETOR PARABÓLICO DE GRELHA METÁLICA
# Dimensões: Rx = 0.74 m, Rz = 0.46 m; profundidade Foco = 0.45 m; y = (x^2/(4*Fx) + z^2/(4*Fz))
Fx, Fz = 0.60, 0.45

# Anel elíptico tubular perimetral da boca da antena
pts_borda = []
N_BORDA = 24
for i in range(N_BORDA):
    ang = i * 2 * PI / N_BORDA
    bx = 0.74 * math.cos(ang)
    bz = 0.46 * math.sin(ang)
    by = 0.20 + (bx * bx / (4 * Fx) + bz * bz / (4 * Fz))
    pts_borda.append(Vector((bx, by, bz)))

for a, b in zip(pts_borda, pts_borda[1:] + [pts_borda[0]]):
    tubo(bm_ant_am, a, b, 0.022, lados=6)

# Costelas curvas parabólicas em X (longarinas horizontais em perfil de aço)
for z_cost in (-0.32, -0.16, 0.0, 0.16, 0.32):
    larg_x = 0.72 * math.sqrt(max(0.01, 1.0 - (z_cost / 0.46) ** 2))
    pts_cost = []
    for k in range(9):
        tx = -larg_x + (k / 8.0) * (2 * larg_x)
        ty = 0.20 + (tx * tx / (4 * Fx) + z_cost * z_cost / (4 * Fz))
        pts_cost.append(Vector((tx, ty, z_cost)))
    for a, b in zip(pts_cost, pts_cost[1:]):
        tubo(bm_ant_ac, a, b, 0.010, lados=4)

# Costelas curvas parabólicas em Z (nervuras verticais)
for x_cost in (-0.50, -0.25, 0.0, 0.25, 0.50):
    alt_z = 0.44 * math.sqrt(max(0.01, 1.0 - (x_cost / 0.74) ** 2))
    pts_cost_v = []
    for k in range(7):
        tz = -alt_z + (k / 6.0) * (2 * alt_z)
        ty = 0.20 + (x_cost * x_cost / (4 * Fx) + tz * tz / (4 * Fz))
        pts_cost_v.append(Vector((x_cost, ty, tz)))
    for a, b in zip(pts_cost_v, pts_cost_v[1:]):
        tubo(bm_ant_ac, a, b, 0.010, lados=4)

# ESTRUTURA DO ALIMENTADOR FRONTAL (Feedhorn Boom)
# Tripé convergindo para o ponto focal à frente da parábola
POS_FOCO = Vector((0.0, 0.74, 0.05))
tubo(bm_ant_am, (-0.68, 0.24, -0.32), POS_FOCO, 0.018, lados=6)
tubo(bm_ant_am, (0.68, 0.24, -0.32), POS_FOCO, 0.018, lados=6)
tubo(bm_ant_am, (0.0, 0.26, 0.42), POS_FOCO, 0.018, lados=6)

# Corneta alimentadora (feedhorn) cônica de cobre apontando para o refletor (-Y)
cil(bm_ant_co, POS_FOCO, 0.075, 0.12, eixo=Vector((0, -1, 0)), lados=14, r2=0.04)
# Estrias corrugadas concêntricas de choque
for dy in (0.02, 0.05, 0.08):
    toro(bm_ant_co, POS_FOCO + Vector((0, -dy, 0)), 0.068 - dy * 0.2, 0.007, nR=14, nr=5,
         rot=Matrix.Rotation(math.radians(90), 3, 'X'))

# Cristal focalizador no centro da corneta (emite os pulsos do radar)
POS_CRISTAL_REL = POS_FOCO + Vector((0, -0.06, 0))
hexa_cristal(bm_ant_cr, POS_CRISTAL_REL, 0.028, 0.08, ponta=0.035)

# Guia de onda retangular curvo em cobre descendo do feedhorn até a caixa de RF
pts_guia = [
    POS_FOCO + Vector((0, 0.04, 0)),
    Vector((0.08, 0.60, -0.10)),
    Vector((0.25, 0.40, -0.20)),
    Vector((0.15, 0.18, -0.10)),
    Vector((0.08, 0.12, 0.0))
]
for a, b in zip(pts_guia, pts_guia[1:]):
    viga(bm_ant_co, a, b, 0.028)
    # Flanges do guia de onda
    u = (b - a).normalized()
    caixa(bm_ant_fe, (a + b) / 2, (0.045, 0.045, 0.008), u.to_track_quat('Z', 'Y').to_matrix())

# PAINEL PHASED ARRAY SECUNDÁRIO (no topo da armação, inclinado)
POS_PA = Vector((0.0, 0.24, 0.58))
caixa(bm_ant_am, POS_PA, (0.46, 0.06, 0.18), Matrix.Rotation(math.radians(-15), 3, 'X'))
caixa(bm_ant_fe, POS_PA + Vector((0, 0.035, 0)), (0.42, 0.015, 0.14), Matrix.Rotation(math.radians(-15), 3, 'X'))

# 18 domos cerâmicos em grade 3×6 no painel
rot_pa = Matrix.Rotation(math.radians(-15), 3, 'X')
for ix in range(6):
    for iz in range(3):
        x_d = -0.175 + ix * 0.070
        z_d = -0.045 + iz * 0.045
        pos_domo = POS_PA + rot_pa @ Vector((x_d, 0.045, z_d))
        cil(bm_ant_ce, pos_domo, 0.018, 0.014, eixo=rot_pa @ Vector((0, 1, 0)), lados=8)

# Constrói os objetos da antena
o_ant_am = obj('antena_amarelo', bm_ant_am, 'amarelo')
o_ant_ac = obj('antena_aco', bm_ant_ac, 'aco')
o_ant_fe = obj('antena_ferro', bm_ant_fe, 'ferro')
o_ant_co = obj('antena_cobre', bm_ant_co, 'cobre')
o_ant_ce = obj('antena_ceramica', bm_ant_ce, 'ceramica')
o_ant_cr = obj('antena_cristal', bm_ant_cr, 'cristal')
suavizar(o_ant_am)
suavizar(o_ant_ac)
suavizar(o_ant_co)

# Empty pai da antena (com pivô no eixo de elevação)
empty_antena = bpy.data.objects.new('antena', None)
empty_antena.empty_display_type = 'ARROWS'
empty_antena.location = Vector((0, 0, Z_MANCAL))
sc.collection.objects.link(empty_antena)
empty_antena.parent = empty_giro

for o in (o_ant_am, o_ant_ac, o_ant_fe, o_ant_co, o_ant_ce, o_ant_cr):
    o.parent = empty_antena


# ==================================================================
# 4. PISTÕES DE ELEVAÇÃO (Atuadores telescópicos entre Yoke e Antena)
# ==================================================================
# Par de pistões telescópicos: camisa presa no Yoke (giro), haste presa na Antena
# Âncoras no Yoke (coordenadas locais de giro): (±0.24, -0.16, Z_MESA + 0.12)
# Âncoras na Antena (coordenadas locais de antena): (±0.24, -0.18, -0.14)
pistao_pares = []
for idx, sx in enumerate((-0.24, 0.24)):
    # Camisa (cilindro externo em grafite/amarelo)
    bm_camisa = bmesh.new()
    cil(bm_camisa, (0, 0, 0.15), 0.028, 0.30, lados=14)
    # Olhete de base da camisa
    cil(bm_camisa, (0, 0, 0), 0.032, 0.05, eixo=Vector((1, 0, 0)), lados=12)
    toro(bm_camisa, (0, 0, 0.30), 0.032, 0.008, nR=14, nr=6)
    o_cam = obj('pistao%d_camisa' % idx, bm_camisa, 'grafite')
    suavizar(o_cam)
    o_cam.parent = empty_giro

    # Haste (cilindro interno cromado que desliza)
    bm_haste = bmesh.new()
    cil(bm_haste, (0, 0, 0.18), 0.018, 0.36, lados=14)
    cil(bm_haste, (0, 0, 0.36), 0.026, 0.05, eixo=Vector((1, 0, 0)), lados=12)
    o_has = obj('pistao%d_haste' % idx, bm_haste, 'cromo')
    suavizar(o_has)
    o_has.parent = empty_giro

    pistao_pares.append((sx, o_cam, o_has))


# ==================================================================
# 5. EFEITOS DE CENA E ANIMAÇÃO
# ==================================================================
# Luz pontual pulsante no cristal do alimentador
luz_radar_d = bpy.data.lights.new('EFEITO_LuzRadar', 'POINT')
luz_radar_d.color = (0.45, 0.25, 1.0)
luz_radar_d.energy = 8.0
luz_radar_d.shadow_soft_size = 0.08
luz_radar = bpy.data.objects.new('EFEITO_LuzRadar', luz_radar_d)
sc.collection.objects.link(luz_radar)
luz_radar.parent = empty_antena
luz_radar.location = POS_CRISTAL_REL

# Chão e iluminação geral para o render de Cycles
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


# ------------------------------------------------------------------ ANIMAÇÃO DE 96 QUADROS (4 s)
PULSOS = [6, 30, 54, 78]  # Quadros dos picos de emissão do radar

for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS  # 0.0 a 1.0

    # 1. Giro azimutal contínuo (360° em 4 s)
    ang_z = t * 2 * PI
    empty_giro.rotation_euler = Euler((0, 0, ang_z), 'XYZ')
    empty_giro.keyframe_insert('rotation_euler', frame=q)

    # Pinhão dentado gira na proporção da coroa
    rot_pinhao = -ang_z * (0.55 / 0.07)
    o_pinhao.rotation_euler = Euler((0, 0, rot_pinhao), 'XYZ')
    o_pinhao.keyframe_insert('rotation_euler', frame=q)

    # 2. Elevação oscilatória suave da antena (12° a 26° de tilt)
    # Oscila com duas ondas para movimento natural de varredura do terreno
    ang_x = math.radians(18.0) + math.radians(7.0) * math.sin(t * 2 * PI * 2) + math.radians(2.0) * math.sin(t * 2 * PI * 4)
    empty_antena.rotation_euler = Euler((ang_x, 0, 0), 'XYZ')
    empty_antena.keyframe_insert('rotation_euler', frame=q)

    # 3. Pistões de elevação telescópicos
    # Ponto base da camisa no Yoke (no referencial de giro)
    # Ponto topo da haste na Antena: rotação de ang_x em torno de (0, 0, 0) local de antena
    for sx, o_cam, o_has in pistao_pares:
        p_base = Vector((sx, -0.16, Z_MESA + 0.12 - Z_MANCAL))  # relativo a Z_MANCAL
        p_ancora_ant = Vector((sx, -0.18, -0.14))
        p_topo = Matrix.Rotation(ang_x, 3, 'X') @ p_ancora_ant

        v_eixo = p_topo - p_base
        dist_pistao = v_eixo.length
        dir_pistao = v_eixo.normalized()
        quat_pistao = dir_pistao.to_track_quat('Z', 'Y')

        # Posiciona e orienta a camisa no Yoke
        o_cam.location = p_base + Vector((0, 0, Z_MANCAL))
        o_cam.rotation_mode = 'QUATERNION'
        o_cam.rotation_quaternion = quat_pistao
        o_cam.keyframe_insert('location', frame=q)
        o_cam.keyframe_insert('rotation_quaternion', frame=q)

        # Posiciona e orienta a haste deslizando na camisa
        o_has.location = p_topo + Vector((0, 0, Z_MANCAL)) - dir_pistao * 0.36
        o_has.rotation_mode = 'QUATERNION'
        o_has.rotation_quaternion = quat_pistao
        o_has.keyframe_insert('location', frame=q)
        o_has.keyframe_insert('rotation_quaternion', frame=q)

    # 4. Emissão do cristal do alimentador e luz do radar
    # Procura a distância do quadro atual para o pulso mais recente
    dt_min = min((q - p) % 24 for p in PULSOS)
    if dt_min < 2:
        forca_emissao = 28.0
    elif dt_min < 10:
        forca_emissao = 28.0 * math.exp(-(dt_min - 2) * 0.45)
    else:
        forca_emissao = 2.5

    bsdf_cristal.inputs['Emission Strength'].default_value = forca_emissao
    bsdf_cristal.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)

    luz_radar_d.energy = forca_emissao * 2.2
    luz_radar_d.keyframe_insert('energy', frame=q)

    # 5. LEDs do painel do pedestal: setor ativo conforme o azimute
    setor_ativo = int((t * 8) % 8)
    for i in range(8):
        f_led = 9.0 if i == setor_ativo else 0.4
        bsdfs_led[i].inputs['Emission Strength'].default_value = f_led
        bsdfs_led[i].inputs['Emission Strength'].keyframe_insert('default_value', frame=q)


# Suaviza interpolação dos keyframes para animação em laço contínuo
for o in list(sc.objects):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


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
    sc.frame_set(6)  # Momento do 1º pulso de radar ativo com cristal aceso

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 1.9), (210, 2.1), (120, 2.3), (30, 1.8))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 4.6, math.sin(a) * 4.6, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'sensor_varredura_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada dos detalhes (perto): alimentador, cristal, corneta de cobre e mancal
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(6)
        mirar(Vector((0.85, 1.65, 1.75)), Vector((0.02, 0.42, 1.40)), 36)
        sc.render.filepath = os.path.join(AQUI, 'sensor_varredura_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(6)
    mirar(ALVO + Vector((2.8, -3.2, 1.6)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'sensor_varredura_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('SENSOR_VARREDURA ok (%d tris)' % tot_tri)
