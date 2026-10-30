"""Estudo isolado (fora do jogo): POSTO AVANÇADO da IA, 3×3 tiles (lote 17, proliferação).
Entrada de itens pelas 4 bocas cardeais (ITEM_ENT_S1, ITEM_ENT_N1, ITEM_ENT_L1, ITEM_ENT_O1, meio de cada borda).
Função: Núcleo-filho fabricado pela própria fábrica autônoma para expansão territorial; possui estoque interno
massivo para abastecer a logística regional e transmissor integrado de energia sem fio de 150 kW.
Estilo: Fortaleza industrial pesada da IA — bunker blindado octogonal com 4 bocas de esteira com roletes,
4 câmaras de estocagem cilíndricas nos cantos com visores de nível e pistões de compactação, cúpula de processamento
central e torre de transmissão sem fio com cristal ressonador suspenso e anel irradiador de 3 hastes no topo.
- Laje de concreto 2,90 × 2,90 m com chanfros nos 4 cantos, calhas de esteira com cantoneiras de aço e chumbadores;
  faixas de perigo nas bordas e poças de óleo/lubrificante perto das bocas e mancais.
- 4 bocas de esteira nas bordas cardeais (x=0 ou y=0, z=0,23 m) com roletes cilíndricos, cortinas de lamelas de borracha
  e sensores de passagem de itens.
- 4 silos de estocagem nos quadrantes diagonais com carcaças em amarelo gasto e remendos de chapa de aço, aletas de resfriamento,
  tubulações de alívio de pressão e barramentos verticais de LEDs indicadores de capacidade de carga.
- 4 pistões hidráulicos verticais de pressurização/compactação de carga sobre os silos (camisa no flange superior, haste móvel).
- Torre transmissora sem fio central: base com transformador aletado e bobina de indução toroidal de cobre; 4 pilones
  em arco com garras segurando o cristal-núcleo secundário em ressonância (pulso violeta de energia da IA).
- Antena transmissora superior ('antena'): anel de irradiação com 3 hastes simétricas terminadas em esferas capacitivas e
  anel de corona anti-estático girando continuamente no topo da torre (z = 2,55 m).
- Animação em laço de 96 quadros (4 s a 24 qps): rotação contínua da antena de transmissão de 150 kW, oscilação de
  pressurização dos 4 pistões de estoque (ciclos defasados), rotação dos roletes das 4 esteiras de entrada, pulsação
  do cristal de ressonância e LEDs de estoque correndo nos visores verticais.
Uso: blender -b --python estudo_posto_avancado.py -- foto
     blender -b --python estudo_posto_avancado.py -- nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(117)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades de forma
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


# ------------------------------------------------------------------ materiais
def emissivo_mat(nome, cor, forca_inicial=0.0):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1.0)
    b.inputs['Emission Color'].default_value = (*cor, 1.0)
    b.inputs['Emission Strength'].default_value = forca_inicial
    b.inputs['Roughness'].default_value = 0.18
    return m


base3d.M.update({
    'amarelo': mats.material('AmareloPosto', (0.75, 0.50, 0.06), 0.0, 0.42, desgaste=0.90, sujeira=0.80),
    'primer': mats.material('PrimerPosto', (0.36, 0.12, 0.08), 0.0, 0.55, desgaste=0.85, sujeira=0.85, ferrugem=0.45),
    'grafite': mats.material('GrafitePosto', (0.08, 0.085, 0.09), 0.0, 0.48, desgaste=0.65, sujeira=0.75),
    'aco': mats.material('AçoPosto', (0.44, 0.45, 0.46), 1.0, 0.40, pintura=False, ferrugem=0.65, sujeira=0.70, escovado=True),
    'aco_escuro': mats.material('AçoEscuroPosto', (0.22, 0.23, 0.24), 1.0, 0.50, pintura=False, ferrugem=0.80, sujeira=0.85),
    'cromo': mats.material('CromoPosto', (0.86, 0.87, 0.89), 1.0, 0.10, pintura=False, sujeira=0.15),
    'cobre': mats.material('CobrePosto', (0.84, 0.44, 0.22), 1.0, 0.30, pintura=False, ferrugem=0.35, sujeira=0.65),
    'ferro': mats.material('FerroFundidoPosto', (0.10, 0.095, 0.09), 0.8, 0.68, pintura=False, ferrugem=0.85, sujeira=0.90),
    'concreto': mats.material('ConcretoPosto', (0.34, 0.33, 0.31), 0.0, 0.90, sujeira=0.75, desgaste=0.25),
    'oleo': mats.material('ÓleoPosto', (0.012, 0.010, 0.008), 0.0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'borracha': mats.material('BorrachaPosto', (0.04, 0.04, 0.045), 0.0, 0.85, pintura=False, sujeira=0.60),
    'listras': base3d.listras_mat(),
    'chao': mats.material('ChãoPosto', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0),
})

# Cristal de emissão violeta-celeste (núcleo-filho da IA)
mat_cristal = emissivo_mat('CristalNucleoFilho', (0.55, 0.22, 1.0), 8.0)
base3d.M['cristal'] = mat_cristal
bsdf_cristal = mat_cristal.node_tree.nodes['Principled BSDF']

# LEDs dos visores de nível dos 4 silos de estoque
mat_led_silo = emissivo_mat('LEDSiloEstoque', (0.25, 0.85, 0.95), 3.0)
base3d.M['led_silo'] = mat_led_silo
mat_led_status = emissivo_mat('LEDStatusPosto', (1.0, 0.45, 0.05), 4.0)
base3d.M['led_status'] = mat_led_status


# ==================================================================
# 1. BASE ESTACIONÁRIA E CORPO DO BUNKER ('corpo')
# ==================================================================
bm_base = bmesh.new()
bm_aco = bmesh.new()
bm_ferro = bmesh.new()
bm_amarelo = bmesh.new()
bm_primer = bmesh.new()
bm_cobre = bmesh.new()
bm_borracha = bmesh.new()
bm_leds = bmesh.new()

# Laje maciça de concreto de 2,90 × 2,90 m (±1,45 m) com chanfros de 0,35 m nos cantos
L, H_LAJE, CH = 1.45, 0.14, 0.35
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

# Cantoneiras de ferro de ancoragem nos cantos chanfrados com chumbadores pesados
for ang_c in (math.radians(45), math.radians(135), math.radians(225), math.radians(315)):
    rot_c = Matrix.Rotation(ang_c, 3, 'Z')
    pos_c = rot_c @ Vector((1.85, 0, H_LAJE / 2))
    caixa(bm_ferro, pos_c, (0.06, 0.32, H_LAJE + 0.02), rot_c)
    for dy in (-0.10, 0.10):
        cil(bm_aco, pos_c + rot_c @ Vector((0, dy, H_LAJE / 2 + 0.015)), 0.020, 0.03, lados=6)
        cil(bm_ferro, pos_c + rot_c @ Vector((0, dy, H_LAJE / 2 + 0.005)), 0.030, 0.01, lados=10)

# Faixas de aviso nas laterais do concreto
bm_listras = bmesh.new()
for ang_l in (0, PI / 2, PI, 3 * PI / 2):
    rl = Matrix.Rotation(ang_l, 3, 'Z')
    caixa(bm_listras, rl @ Vector((0, L + 0.004, H_LAJE / 2)), (1.80, 0.008, H_LAJE * 0.75), rl)

# BUNKER CENTRAL OCTOGONAL (Z = H_LAJE até Z = 0,95)
prisma_octo(bm_amarelo, (0, 0), 1.12, H_LAJE, 0.95)
# Frisos de aço e anéis de reforço no bunker
for z_an in (H_LAJE + 0.04, 0.52, 0.92):
    toro(bm_aco, (0, 0, z_an), 1.15, 0.016, nR=32, nr=6)

# 4 BOCAS CARDIAIS DE ENTRADA DE ITENS (Meio de cada borda: X=0 ou Y=0 na borda ±1,45 m)
# Altura de esteira do jogo: topo em z = 0,23 m
bm_roletes = bmesh.new()
for ang_boca in (0, PI / 2, PI, 3 * PI / 2):
    rb = Matrix.Rotation(ang_boca, 3, 'Z')
    # Garganta de entrada com pórtico de aço rebitado
    pos_boca = rb @ Vector((0, 1.35, 0.28))
    caixa(bm_ferro, pos_boca, (0.72, 0.24, 0.28), rb)
    caixa(bm_amarelo, pos_boca + rb @ Vector((0, -0.06, 0.08)), (0.76, 0.14, 0.36), rb)

    # Canal da esteira com roletes de aço (z = 0.20 a 0.24)
    caixa(bm_aco, rb @ Vector((0, 1.38, 0.18)), (0.58, 0.26, 0.06), rb)
    # Cortina de borracha anti-poeira
    caixa(bm_borracha, rb @ Vector((0, 1.25, 0.32)), (0.50, 0.015, 0.14), rb)

    # 3 Roletes cilíndricos na boca de entrada
    for ir, dy in enumerate((1.28, 1.38, 1.48)):
        cil(bm_roletes, rb @ Vector((0, dy, 0.23)), 0.024, 0.52, eixo=rb @ Vector((1, 0, 0)), lados=12)

    # Sensores ópticos nas laterais da boca
    cil(bm_ferro, rb @ Vector((-0.30, 1.35, 0.32)), 0.020, 0.06, eixo=rb @ Vector((0, 1, 0)), lados=8)
    cil(bm_cobre, rb @ Vector((0.30, 1.35, 0.32)), 0.020, 0.06, eixo=rb @ Vector((0, 1, 0)), lados=8)

# 4 CÂMARAS/SILOS DE ESTOCAGEM VERTICAIS (Quadrantes SO, SE, NE, NO: r = 0,85 m, diâmetro 0,55 m)
# Uma delas leva chapa trocada de primer vermelho!
POS_SILOS = [
    Vector((0.72, 0.72, 0.95)),
    Vector((-0.72, 0.72, 0.95)),
    Vector((-0.72, -0.72, 0.95)),
    Vector((0.72, -0.72, 0.95))
]
H_SILO = 0.65
for idx, ps in enumerate(POS_SILOS):
    # Cilindro do silo
    mat_silo = bm_primer if idx == 1 else bm_amarelo
    cil(mat_silo, ps + Vector((0, 0, H_SILO / 2)), 0.28, H_SILO, lados=20)
    # Cintas e flanges de reforço
    toro(bm_aco, ps + Vector((0, 0, 0.08)), 0.29, 0.014, nR=20, nr=5)
    toro(bm_aco, ps + Vector((0, 0, H_SILO - 0.08)), 0.29, 0.014, nR=20, nr=5)
    # Tampa do silo com parafusos
    cil(bm_ferro, ps + Vector((0, 0, H_SILO + 0.02)), 0.30, 0.04, lados=20)
    for kp in range(8):
        ap = kp * 2 * PI / 8
        cil(bm_aco, ps + Vector((0.26 * math.cos(ap), 0.26 * math.sin(ap), H_SILO + 0.045)), 0.010, 0.015, lados=6)

    # Visor vertical de nível em acrílico com LEDs azuis
    dir_out = Vector((ps.x, ps.y, 0)).normalized()
    rot_silo = dir_out.to_track_quat('Y', 'Z').to_matrix()
    p_visor = ps + dir_out * 0.285 + Vector((0, 0, H_SILO / 2))
    caixa(bm_ferro, p_visor, (0.08, 0.02, 0.44), rot_silo)
    # Fita de 6 LEDs de ocupação
    for ile in range(6):
        z_le = p_visor.z - 0.18 + ile * 0.072
        cil(bm_leds, Vector((p_visor.x, p_visor.y, z_le)) + dir_out * 0.012, 0.010, 0.008, eixo=dir_out, lados=8)

    # Tubulações de equalização de pressão conectando os silos à cúpula central
    cano_pts = [ps + Vector((0, 0, H_SILO - 0.12)),
                ps * 0.5 + Vector((0, 0, H_SILO + 0.10)),
                Vector((0, 0, 1.25))]
    cano_rigido(bm_cobre, bm_ferro, cano_pts, 0.016)

# 4 PISTÕES VERTICAIS DE COMPACTAÇÃO DE CARGA (Sobre as tampas dos 4 silos)
# Camisas fixas no topo dos silos, hastes animadas descendo/subindo
pistao_hastes = []
for idx, ps in enumerate(POS_SILOS):
    p_pist = ps + Vector((0, 0, H_SILO + 0.04))
    # Base da camisa
    cil(bm_ferro, p_pist + Vector((0, 0, 0.03)), 0.065, 0.04, lados=14)
    # Camisa do pistão
    cil(bm_amarelo, p_pist + Vector((0, 0, 0.20)), 0.042, 0.30, lados=14)
    toro(bm_aco, p_pist + Vector((0, 0, 0.35)), 0.045, 0.009, nR=14, nr=5)
    # Mangueira hidráulica de alta pressão chegando no topo da camisa
    mangueira(bm_borracha, [
        p_pist + Vector((0.04, 0.02, 0.32)),
        p_pist + Vector((0.10, 0.06, 0.36)),
        ps * 0.6 + Vector((0, 0, 1.30))
    ], 0.008)

    # Haste telescópica móvel (objeto separado)
    bm_h = bmesh.new()
    cil(bm_h, (0, 0, 0.16), 0.024, 0.34, lados=12)
    cil(bm_h, (0, 0, 0.33), 0.036, 0.02, lados=12)
    o_h = obj('posto_pistao%d_haste' % idx, bm_h, 'cromo')
    suavizar(o_h)
    o_h.location = p_pist
    pistao_hastes.append((idx, o_h, p_pist))

# CÚPULA CENTRAL E GERADOR SEM FIO (Z = 0.95 até Z = 1.45)
prisma_octo(bm_ferro, (0, 0), 0.78, 0.95, 1.30)
# Aletas de refrigeração da subestação de 150 kW nas 4 diagonais
for ad in (math.radians(45), math.radians(135), math.radians(225), math.radians(315)):
    rd = Matrix.Rotation(ad, 3, 'Z')
    for ia in range(5):
        caixa(bm_aco, rd @ Vector((0.82, -0.08 + ia * 0.04, 1.12)), (0.05, 0.008, 0.28), rd)

# Bobina de indução toroidal em cobre com condutores pesados
toro(bm_cobre, (0, 0, 1.36), 0.54, 0.035, nR=28, nr=8)
toro(bm_cobre, (0, 0, 1.44), 0.50, 0.030, nR=28, nr=8)

# 4 PILONES EM ARCO SEGURANDO O CRISTAL-NÚCLEO SECUNDÁRIO (Z = 1.45 até Z = 2.05)
Z_CRISTAL_P = 1.76
for ang_p in (0, PI / 2, PI, 3 * PI / 2):
    rp = Matrix.Rotation(ang_p, 3, 'Z')
    # Pilar em arco
    viga(bm_amarelo, rp @ Vector((0.48, 0, 1.45)), rp @ Vector((0.28, 0, Z_CRISTAL_P)), 0.045)
    viga(bm_amarelo, rp @ Vector((0.28, 0, Z_CRISTAL_P)), rp @ Vector((0.18, 0, 2.08)), 0.045)
    # Garras com eletrodos de cobre segurando o cristal
    caixa(bm_ferro, rp @ Vector((0.18, 0, Z_CRISTAL_P)), (0.08, 0.05, 0.08), rp)
    cil(bm_cobre, rp @ Vector((0.12, 0, Z_CRISTAL_P)), 0.016, 0.06, eixo=rp @ Vector((-1, 0, 0)), lados=8)

# Anéis de confinamento de campo magnético ao redor do cristal
toro(bm_aco, (0, 0, Z_CRISTAL_P - 0.12), 0.15, 0.010, nR=20, nr=5)
toro(bm_aco, (0, 0, Z_CRISTAL_P + 0.12), 0.15, 0.010, nR=20, nr=5)

# O CRISTAL-NÚCLEO SECUNDÁRIO (Monólito lapidado hexagonal imponente)
bm_cristal = bmesh.new()
hexa_cristal(bm_cristal, (0, 0, Z_CRISTAL_P), 0.09, 0.36, ponta_sup=0.12, ponta_inf=0.12)

# Manchas de óleo e sujeira na base
bm_oleo = bmesh.new()
for ang_m in (0.4, 1.9, 3.6, 5.2):
    mancha(bm_oleo, (math.cos(ang_m) * 0.85, math.sin(ang_m) * 0.85), 0.22, H_LAJE + 0.002)

# Instancia objetos do corpo fixo
o_base = obj('corpo_base', bm_base, 'concreto')
o_aco = obj('corpo_aco', bm_aco, 'aco')
o_ferro = obj('corpo_ferro', bm_ferro, 'ferro')
o_amarelo = obj('corpo_amarelo', bm_amarelo, 'amarelo')
o_primer = obj('corpo_primer', bm_primer, 'primer')
o_cobre = obj('corpo_cobre', bm_cobre, 'cobre')
o_borracha = obj('corpo_borracha', bm_borracha, 'borracha')
o_roletes = obj('corpo_roletes', bm_roletes, 'aco')
o_oleo = obj('corpo_oleo', bm_oleo, 'oleo')
o_listras = obj('corpo_listras', bm_listras, 'listras')
o_leds = obj('corpo_leds', bm_leds, 'led_silo')
o_cristal = obj('corpo_cristal', bm_cristal, 'cristal')

suavizar(o_base)
suavizar(o_amarelo)
suavizar(o_primer)
suavizar(o_cristal)


# ==================================================================
# 2. ANTENA TRANSMISSORA SEM FIO SUPERIOR ('antena')
# ==================================================================
# No topo da torre (Z = 2,10 até Z = 2,65 m), gira continuamente em 360° emitindo 150 kW
bm_ant_fe = bmesh.new()
bm_ant_ac = bmesh.new()
bm_ant_co = bmesh.new()
bm_ant_cr = bmesh.new()

Z_TOPO_ANT = 2.12
# Anel de acoplamento e mancal superior
cil(bm_ant_fe, (0, 0, Z_TOPO_ANT), 0.16, 0.04, lados=20)
toro(bm_ant_ac, (0, 0, Z_TOPO_ANT + 0.02), 0.15, 0.012, nR=20, nr=5)

# Mastro central afilado
cil(bm_ant_ac, (0, 0, Z_TOPO_ANT + 0.22), 0.045, 0.40, lados=12, r2=0.025)

# 3 HASTES IRRADIADORAS SIMÉTRICAS A 120°
Z_IRRAD = Z_TOPO_ANT + 0.28
for k in range(3):
    ang_h = k * 2 * PI / 3
    rh = Matrix.Rotation(ang_h, 3, 'Z')
    # Haste tubular inclinada
    tubo(bm_ant_co, (0, 0, Z_IRRAD - 0.06), rh @ Vector((0.42, 0, Z_IRRAD + 0.12)), 0.016, lados=8)
    # Tirante de reforço
    tubo(bm_ant_ac, (0, 0, Z_IRRAD + 0.14), rh @ Vector((0.36, 0, Z_IRRAD + 0.10)), 0.009, lados=6)
    # Esfera capacitiva transmissora na ponta
    bmesh.ops.create_uvsphere(bm_ant_co, u_segments=14, v_segments=8, radius=0.045,
                             matrix=Matrix.Translation(rh @ Vector((0.42, 0, Z_IRRAD + 0.12))))

# Anel de corona anti-estático interligando as pontas das 3 hastes
toro(bm_ant_ac, (0, 0, Z_IRRAD + 0.12), 0.42, 0.010, nR=24, nr=5)

# Ponta captora de descarga superior
cil(bm_ant_cr, (0, 0, Z_TOPO_ANT + 0.48), 0.018, 0.12, lados=8, r2=0.002)

o_ant_fe = obj('antena_ferro', bm_ant_fe, 'ferro')
o_ant_ac = obj('antena_aco', bm_ant_ac, 'aco')
o_ant_co = obj('antena_cobre', bm_ant_co, 'cobre')
o_ant_cr = obj('antena_cromo', bm_ant_cr, 'cromo')
suavizar(o_ant_ac)
suavizar(o_ant_co)

# Empty pai da antena transmissora
empty_antena = bpy.data.objects.new('antena', None)
empty_antena.empty_display_type = 'ARROWS'
empty_antena.location = Vector((0, 0, 0))
sc.collection.objects.link(empty_antena)

for o in (o_ant_fe, o_ant_ac, o_ant_co, o_ant_cr):
    o.parent = empty_antena


# ==================================================================
# 3. ILUMINAÇÃO, EFEITOS E ANIMAÇÃO
# ==================================================================
# Luz volumétrica pulsante no cristal do posto
luz_nucleo_d = bpy.data.lights.new('EFEITO_LuzNucleoPosto', 'POINT')
luz_nucleo_d.color = (0.60, 0.25, 1.0)
luz_nucleo_d.energy = 25.0
luz_nucleo_d.shadow_soft_size = 0.10
luz_nucleo = bpy.data.objects.new('EFEITO_LuzNucleoPosto', luz_nucleo_d)
sc.collection.objects.link(luz_nucleo)
luz_nucleo.location = Vector((0, 0, Z_CRISTAL_P))

# Luz do campo de irradiação sem fio no topo
luz_sem_fio_d = bpy.data.lights.new('EFEITO_LuzSemFio', 'POINT')
luz_sem_fio_d.color = (0.45, 0.70, 1.0)
luz_sem_fio_d.energy = 15.0
luz_sem_fio = bpy.data.objects.new('EFEITO_LuzSemFio', luz_sem_fio_d)
sc.collection.objects.link(luz_sem_fio)
luz_sem_fio.parent = empty_antena
luz_sem_fio.location = Vector((0, 0, Z_IRRAD + 0.12))

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
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS  # 0.0 a 1.0

    # 1. Rotação contínua da antena de transmissão sem fio (360° em 4 s)
    ang_z = t * 2 * PI
    empty_antena.rotation_euler = Euler((0, 0, ang_z), 'XYZ')
    empty_antena.keyframe_insert('rotation_euler', frame=q)

    # 2. Pulso de ressonância do cristal-núcleo secundário
    pulso_c = 8.0 + 4.5 * math.sin(t * 2 * PI * 2) + 2.0 * math.sin(t * 2 * PI * 4)
    bsdf_cristal.inputs['Emission Strength'].default_value = pulso_c
    bsdf_cristal.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    luz_nucleo_d.energy = pulso_c * 3.2
    luz_nucleo_d.keyframe_insert('energy', frame=q)

    # 3. Pulso do campo sem fio superior
    luz_sem_fio_d.energy = 12.0 + 6.0 * math.sin(t * 2 * PI * 3)
    luz_sem_fio_d.keyframe_insert('energy', frame=q)

    # 4. Oscilação harmônica defasada dos 4 pistões de compactação dos silos
    for idx, o_h, p_orig in pistao_hastes:
        fase = idx * (PI / 2)
        dz_pistao = 0.04 * math.sin(t * 2 * PI * 2 + fase)
        o_h.location = p_orig + Vector((0, 0, dz_pistao))
        o_h.keyframe_insert('location', frame=q)


# Suaviza curvas de animação
for o in list(sc.objects):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


# ==================================================================
# 4. CONFIGURAÇÃO DE CÂMERA E MODOS
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


ALVO = Vector((0.0, 0.0, 1.25))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(12)  # Posição com transmissão ativa e pistões em movimento

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.3), (210, 2.5), (120, 2.6), (30, 2.2))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 5.6, math.sin(a) * 5.6, alt - ALVO.z))
        mirar(pos_cam, ALVO, 34)
        sc.render.filepath = os.path.join(AQUI, 'posto_avancado_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: boca de esteira, silos, cristal e torre sem fio
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(12)
        mirar(Vector((1.45, -1.55, 1.85)), Vector((0.10, -0.15, 1.35)), 35)
        sc.render.filepath = os.path.join(AQUI, 'posto_avancado_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(12)
    mirar(ALVO + Vector((3.4, -3.8, 1.8)), ALVO, 34)
    sc.render.filepath = os.path.join(AQUI, 'posto_avancado_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('POSTO_AVANCADO ok (%d tris)' % tot_tri)
