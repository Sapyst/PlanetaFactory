"""Estudo isolado (fora do jogo): FAROL DE CRISTAL da IA, 1×1 tile (lote 17, proliferação).
Sem bocas de itens ou fluidos (estrutura de iluminação de alta potência e visibilidade noturna da fábrica).
Projeta luz de 10 m à noite, revelando instalações, esteiras e alertando a aproximação de enxames de aranhas mecânicas.
Estilo: IA autônoma em mundo hostil — torre pesada de aço treliçado e desgastado suportando um conjunto óptico
de ressonância com grande cristal lapidado suspenso, carrossel de lentes condensadoras e espelhos parabólicos em giro contínuo.
- Laje de concreto 0,86 × 0,86 m com chanfros nos 4 cantos, cantoneiras de aço com parafusos de chumbador.
- Eletroduto pesado de alta tensão com flanges e cotovelo arredondado; caixa blindada de disjuntores e transformador com
  alavanca manual industrial, barramento com isoladores cerâmicos em carretel e luzes de carga; haste de aterramento de cobre.
- Torre treliçada piramidal de 4 montantes em viga angular com cruzetas de contraventamento em 3 níveis; um gomo reparado com
  chapa de aço soldada e parafusada de outra cor com rebites aparentes.
- Eletrocalha vertical perfurada com feixes de cabos coaxiais de alta tensão presos por abraçadeiras metálicas a cada 0,25 m.
- 4 estais de cabo de aço com esticadores de rosca galvanizados (turnbuckles) estaiando a torre da laje até a plataforma alta.
- Plataforma superior em z = 2,05 m com piso de grelha metálica e coroa dentada com motor de giro blindado.
- Gaiola de garras em aço forjado e cobre segurando o cristal lapidado hexagonal de ressonância no foco central, envolvido
  por anéis toroidais de indução magnética em cobre torneado.
- Carrossel óptico giratório ('giro'): dois suportes arqueados com espelho refletor parabólico traseiro e lente condensadora
  dianteira com anéis de foco girando continuamente em 360°, varrendo o horizonte.
- Anel toroidal anti-estático de proteção contra corona no topo com haste central afilada.
- Animação em laço de 96 quadros (4 s a 24 qps): rotação azimutal contínua de 360° do carrossel óptico, pulso harmônico de
  ressonância do cristal emissor, iluminação direcional focada varrendo o terreno e LEDs de diagnóstico piscando.
Uso: blender -b --python estudo_farol_cristal.py -- foto
     blender -b --python estudo_farol_cristal.py -- nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(89)
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
    b.inputs['Roughness'].default_value = 0.15
    return m


base3d.M.update({
    'amarelo': mats.material('AmareloFarol', (0.76, 0.52, 0.08), 0.0, 0.42, desgaste=0.90, sujeira=0.80),
    'primer': mats.material('PrimerVermelho', (0.38, 0.12, 0.08), 0.0, 0.55, desgaste=0.85, sujeira=0.85, ferrugem=0.4),
    'grafite': mats.material('GrafiteFarol', (0.08, 0.085, 0.09), 0.0, 0.48, desgaste=0.65, sujeira=0.75),
    'aco': mats.material('AçoFarol', (0.45, 0.46, 0.47), 1.0, 0.40, pintura=False, ferrugem=0.65, sujeira=0.70, escovado=True),
    'aco_escuro': mats.material('AçoEscuroFarol', (0.22, 0.23, 0.24), 1.0, 0.50, pintura=False, ferrugem=0.80, sujeira=0.85),
    'cromo': mats.material('CromoFarol', (0.88, 0.89, 0.90), 1.0, 0.08, pintura=False, sujeira=0.15),
    'cobre': mats.material('CobreFarol', (0.84, 0.44, 0.22), 1.0, 0.30, pintura=False, ferrugem=0.35, sujeira=0.65),
    'ferro': mats.material('FerroFundidoFarol', (0.10, 0.095, 0.09), 0.8, 0.68, pintura=False, ferrugem=0.85, sujeira=0.90),
    'concreto': mats.material('ConcretoFarol', (0.33, 0.32, 0.30), 0.0, 0.90, sujeira=0.75, desgaste=0.25),
    'oleo': mats.material('ÓleoFarol', (0.012, 0.010, 0.008), 0.0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'po': mats.material('PóFarol', (0.18, 0.16, 0.14), 0.0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'ceramica': mats.material('CerâmicaFarol', (0.80, 0.82, 0.85), 0.0, 0.20, pintura=False, sujeira=0.25),
    'vidro_lente': mats.material('VidroLente', (0.75, 0.85, 0.95), 0.0, 0.05, pintura=False, sujeira=0.10),
    'chao': mats.material('ChãoFarol', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0),
})

# Cristal de emissão potente: âmbar dourado de farol (1.0, 0.65, 0.15)
mat_cristal = emissivo_mat('CristalFarol', (1.0, 0.68, 0.18), 12.0)
base3d.M['cristal'] = mat_cristal
bsdf_cristal = mat_cristal.node_tree.nodes['Principled BSDF']

# LEDs de diagnóstico na caixa de força
mat_led_carga = emissivo_mat('LEDCarga', (0.2, 0.9, 0.3), 4.0)
base3d.M['led_carga'] = mat_led_carga
mat_led_alta_tensao = emissivo_mat('LEDAltaTensao', (1.0, 0.15, 0.05), 6.0)
base3d.M['led_alta_tensao'] = mat_led_alta_tensao


# ==================================================================
# 1. BASE ESTACIONÁRIA E TORRE TRELIÇADA ('corpo')
# ==================================================================
bm_base = bmesh.new()
bm_aco = bmesh.new()
bm_ferro = bmesh.new()
bm_amarelo = bmesh.new()
bm_primer = bmesh.new()
bm_cobre = bmesh.new()
bm_ceramica = bmesh.new()

# Laje de concreto de 0,86 × 0,86 m com chanfros nos 4 cantos
L, H_LAJE, CH = 0.43, 0.10, 0.10
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
    pos_c = rot_c @ Vector((0.52, 0, H_LAJE / 2))
    caixa(bm_ferro, pos_c, (0.05, 0.12, H_LAJE + 0.02), rot_c)
    cil(bm_aco, pos_c + Vector((0, 0, H_LAJE / 2 + 0.012)), 0.016, 0.025, lados=6)
    cil(bm_ferro, pos_c + Vector((0, 0, H_LAJE / 2 + 0.005)), 0.026, 0.008, lados=10)

# Caixa de força e transformador de alta tensão (face Sul, Y = -0.32)
caixa(bm_ferro, (0.0, -0.31, H_LAJE + 0.22), (0.28, 0.14, 0.32))
caixa(bm_amarelo, (0.0, -0.39, H_LAJE + 0.22), (0.24, 0.02, 0.28))
# Dobradiças e fecho industrial da caixa
caixa(bm_aco, (-0.11, -0.405, H_LAJE + 0.32), (0.02, 0.015, 0.04))
caixa(bm_aco, (-0.11, -0.405, H_LAJE + 0.12), (0.02, 0.015, 0.04))
caixa(bm_ferro, (0.11, -0.405, H_LAJE + 0.22), (0.025, 0.02, 0.06))
# Alavanca seletora blindada
viga(bm_aco, (0.11, -0.415, H_LAJE + 0.22), (0.11, -0.45, H_LAJE + 0.26), 0.012)
cil(bm_amarelo, (0.11, -0.45, H_LAJE + 0.26), 0.016, 0.025, lados=8)

# Barramento com 3 isoladores cerâmicos em carretel no topo da caixa de força
for k, ix in enumerate((-0.07, 0.0, 0.07)):
    pos_iso = Vector((ix, -0.31, H_LAJE + 0.38))
    cil(bm_ceramica, pos_iso + Vector((0, 0, 0.03)), 0.022, 0.06, lados=10)
    toro(bm_ceramica, pos_iso + Vector((0, 0, 0.045)), 0.025, 0.007, nR=12, nr=4)
    toro(bm_ceramica, pos_iso + Vector((0, 0, 0.02)), 0.025, 0.007, nR=12, nr=4)
    cil(bm_cobre, pos_iso + Vector((0, 0, 0.07)), 0.008, 0.03, lados=6)
    # Fio de cobre ligando ao mastro
    tubo(bm_cobre, pos_iso + Vector((0, 0, 0.08)), Vector((ix * 1.5, -0.18, H_LAJE + 0.52)), 0.005, lados=6)

# Conduíte de alta tensão vindo da borda Sul
pts_duto = [Vector((0.28, -0.46, 0.03)), Vector((0.28, -0.38, 0.03)),
            Vector((0.20, -0.31, H_LAJE + 0.08))]
cano_rigido(bm_aco, bm_ferro, pts_duto, 0.018)

# Fita e haste de aterramento de cobre no canto sudoeste da laje
caixa(bm_cobre, (-0.32, -0.32, H_LAJE + 0.01), (0.015, 0.12, 0.004))
cil(bm_cobre, (-0.32, -0.36, H_LAJE - 0.04), 0.012, 0.12, lados=8)
cil(bm_ferro, (-0.32, -0.36, H_LAJE + 0.015), 0.020, 0.012, lados=6)

# TORRE TRELIÇADA DE AÇO
# 4 montantes piramidais subindo de Z = H_LAJE até Z = 2.05 m
# Base: largura 0.42 m (±0.21 m); Topo: largura 0.22 m (±0.11 m)
Z_TOPO_TORRE = 2.05
R_BASE_TORRE = 0.22
R_TOPO_TORRE = 0.11
NIVEIS_Z = [H_LAJE, 0.55, 1.05, 1.55, Z_TOPO_TORRE]

montantes_pts = []
for sx in (-1, 1):
    for sy in (-1, 1):
        p_base_m = Vector((sx * R_BASE_TORRE, sy * R_BASE_TORRE, H_LAJE))
        p_topo_m = Vector((sx * R_TOPO_TORRE, sy * R_TOPO_TORRE, Z_TOPO_TORRE))
        viga(bm_amarelo, p_base_m, p_topo_m, 0.032)
        # Sapatas de ancoragem na laje
        caixa(bm_ferro, p_base_m + Vector((0, 0, 0.02)), (0.07, 0.07, 0.04))
        cil(bm_aco, p_base_m + Vector((0, 0, 0.045)), 0.012, 0.02, lados=6)

# Travessas horizontais e cruzetas de contraventamento em X em cada nível
for i in range(len(NIVEIS_Z) - 1):
    z_a, z_b = NIVEIS_Z[i], NIVEIS_Z[i + 1]
    t_a = (z_a - H_LAJE) / (Z_TOPO_TORRE - H_LAJE)
    t_b = (z_b - H_LAJE) / (Z_TOPO_TORRE - H_LAJE)
    ra = R_BASE_TORRE * (1 - t_a) + R_TOPO_TORRE * t_a
    rb = R_BASE_TORRE * (1 - t_b) + R_TOPO_TORRE * t_b

    # Cantos nos dois níveis
    c_a = [Vector((ra, ra, z_a)), Vector((-ra, ra, z_a)), Vector((-ra, -ra, z_a)), Vector((ra, -ra, z_a))]
    c_b = [Vector((rb, rb, z_b)), Vector((-rb, rb, z_b)), Vector((-rb, -rb, z_b)), Vector((rb, -rb, z_b))]

    for f in range(4):
        # Travessa horizontal no topo do nível
        viga(bm_aco, c_b[f], c_b[(f + 1) % 4], 0.022)

        # Gomo reparado: no nível 2 da face Leste (f=0), chapa de primer soldada com rebites!
        if i == 2 and f == 0:
            p_centro_chapa = (c_a[f] + c_a[(f + 1) % 4] + c_b[f] + c_b[(f + 1) % 4]) / 4
            caixa(bm_primer, p_centro_chapa, (0.012, (ra + rb) * 0.9, (z_b - z_a) * 0.92))
            # Rebites na chapa trocada
            for dy in (-0.08, 0.0, 0.08):
                for dz in (-0.18, 0.0, 0.18):
                    cil(bm_aco, p_centro_chapa + Vector((0.008, dy, dz)), 0.007, 0.012, eixo=Vector((1, 0, 0)), lados=6)
        else:
            # Cruzetas em X de contraventamento
            tubo(bm_aco, c_a[f], c_b[(f + 1) % 4], 0.012, lados=6)
            tubo(bm_aco, c_a[(f + 1) % 4], c_b[f], 0.012, lados=6)

# Eletrocalha vertical para cabos de força (face Oeste da torre)
pts_calha_inf = Vector((-R_BASE_TORRE - 0.025, 0.0, H_LAJE + 0.15))
pts_calha_sup = Vector((-R_TOPO_TORRE - 0.025, 0.0, Z_TOPO_TORRE))
viga(bm_ferro, pts_calha_inf, pts_calha_sup, 0.035)

# Feixe de cabos de força passando pela eletrocalha com abraçadeiras
mangueira(bm_grafite := bmesh.new(), [
    Vector((-0.18, -0.28, H_LAJE + 0.35)),
    Vector((-R_BASE_TORRE - 0.015, -0.01, H_LAJE + 0.20)),
    Vector((-R_TOPO_TORRE - 0.015, -0.01, Z_TOPO_TORRE - 0.10)),
    Vector((-0.12, 0.0, Z_TOPO_TORRE + 0.06))
], 0.012)
for tz in (0.60, 1.10, 1.60):
    t_val = (tz - H_LAJE) / (Z_TOPO_TORRE - H_LAJE)
    rx_c = R_BASE_TORRE * (1 - t_val) + R_TOPO_TORRE * t_val
    caixa(bm_ferro, (-rx_c - 0.025, 0.0, tz), (0.045, 0.04, 0.015))

# 4 estais de cabo de aço trançado com esticadores de rosca (turnbuckles)
for ang_est in (math.radians(45), math.radians(135), math.radians(225), math.radians(315)):
    rot_est = Matrix.Rotation(ang_est, 3, 'Z')
    p_chao = rot_est @ Vector((0.36, 0.36, H_LAJE + 0.02))
    p_alto = rot_est @ Vector((R_TOPO_TORRE + 0.02, R_TOPO_TORRE + 0.02, Z_TOPO_TORRE - 0.10))

    # Sapata com olhal no chão
    caixa(bm_ferro, p_chao, (0.04, 0.04, 0.03))
    toro(bm_aco, p_chao + Vector((0, 0, 0.025)), 0.016, 0.005, nR=10, nr=4)

    # Esticador de rosca (turnbuckle) a 1/3 do cabo
    p_meio = p_chao * 0.65 + p_alto * 0.35
    u_cabo = (p_alto - p_chao).normalized()
    tubo(bm_aco, p_chao, p_meio - u_cabo * 0.04, 0.004, lados=4)
    # Corpo vazado do esticador
    cil(bm_ferro, p_meio, 0.014, 0.08, eixo=u_cabo, lados=8)
    tubo(bm_aco, p_meio + u_cabo * 0.04, p_alto, 0.004, lados=4)

# PLATAFORMA SUPERIOR (Z = Z_TOPO_TORRE)
caixa(bm_ferro, (0, 0, Z_TOPO_TORRE + 0.02), (0.36, 0.36, 0.04))
# Grelha de piso vazada e anel protetor
toro(bm_aco, (0, 0, Z_TOPO_TORRE + 0.04), 0.22, 0.012, nR=24, nr=5)
# Coroa dentada fixa no topo da plataforma
cil(bm_ferro, (0, 0, Z_TOPO_TORRE + 0.055), 0.18, 0.025, lados=24)
for k in range(24):
    ang_d = k * 2 * PI / 24
    rd = Matrix.Rotation(ang_d, 3, 'Z')
    caixa(bm_aco, rd @ Vector((0.18, 0, Z_TOPO_TORRE + 0.055)), (0.010, 0.012, 0.025), rd)

# Motor de giro da lanterna no canto da plataforma
POS_MOT_F = Vector((0.14, -0.14, Z_TOPO_TORRE + 0.07))
cil(bm_amarelo, POS_MOT_F, 0.032, 0.08, lados=10)
cil(bm_ferro, POS_MOT_F + Vector((0, 0, 0.05)), 0.022, 0.03, lados=8)

# GAIOLA DE CONTENÇÃO DO CRISTAL (Peça fixa central)
# 4 garras forjadas segurando o cristal no foco
Z_CRISTAL = Z_TOPO_TORRE + 0.30
for ang_g in (0, PI / 2, PI, 3 * PI / 2):
    rg = Matrix.Rotation(ang_g, 3, 'Z')
    # Haste da garra
    viga(bm_ferro, (0, 0, Z_TOPO_TORRE + 0.04), rg @ Vector((0.10, 0, Z_CRISTAL - 0.12)), 0.018)
    viga(bm_ferro, rg @ Vector((0.10, 0, Z_CRISTAL - 0.12)), rg @ Vector((0.08, 0, Z_CRISTAL)), 0.018)
    viga(bm_ferro, rg @ Vector((0.08, 0, Z_CRISTAL)), rg @ Vector((0.055, 0, Z_CRISTAL + 0.12)), 0.018)
    # Eletrodo de cobre na ponta da garra
    cil(bm_cobre, rg @ Vector((0.052, 0, Z_CRISTAL)), 0.012, 0.03, eixo=rg @ Vector((-1, 0, 0)), lados=6)

# Anéis toroidais de indução magnética em cobre envolvendo a cintura do cristal
toro(bm_cobre, (0, 0, Z_CRISTAL - 0.08), 0.075, 0.009, nR=18, nr=5)
toro(bm_cobre, (0, 0, Z_CRISTAL + 0.08), 0.075, 0.009, nR=18, nr=5)

# O CRISTAL DE RESSONÂNCIA (Prisma hexagonal imponente lapidado com pontas piramidais)
bm_cristal = bmesh.new()
hexa_cristal(bm_cristal, (0, 0, Z_CRISTAL), 0.048, 0.24, ponta_sup=0.08, ponta_inf=0.08)

# LEDs na caixa de força
bm_leds_box = bmesh.new()
cil(bm_leds_box, (-0.05, -0.405, H_LAJE + 0.28), 0.010, 0.006, eixo=Vector((0, -1, 0)), lados=8)
o_led_carga = obj('corpo_led_carga', bm_leds_box, 'led_carga')

bm_led_aviso = bmesh.new()
cil(bm_led_aviso, (0.05, -0.405, H_LAJE + 0.28), 0.012, 0.008, eixo=Vector((0, -1, 0)), lados=8)
o_led_aviso = obj('corpo_led_aviso', bm_led_aviso, 'led_alta_tensao')

# Manchas de óleo na laje
bm_oleo = bmesh.new()
mancha(bm_oleo, (0.08, -0.06), 0.16, H_LAJE + 0.002)
mancha(bm_oleo, (-0.12, 0.14), 0.11, H_LAJE + 0.002)

# Instancia os objetos do corpo fixo
o_base = obj('corpo_base', bm_base, 'concreto')
o_aco = obj('corpo_aco', bm_aco, 'aco')
o_ferro = obj('corpo_ferro', bm_ferro, 'ferro')
o_amarelo = obj('corpo_amarelo', bm_amarelo, 'amarelo')
o_primer = obj('corpo_primer', bm_primer, 'primer')
o_cobre = obj('corpo_cobre', bm_cobre, 'cobre')
o_ceramica = obj('corpo_ceramica', bm_ceramica, 'ceramica')
o_grafite = obj('corpo_grafite', bm_grafite, 'grafite')
o_oleo = obj('corpo_oleo', bm_oleo, 'oleo')
o_cristal = obj('corpo_cristal', bm_cristal, 'cristal')
suavizar(o_base)
suavizar(o_amarelo)
suavizar(o_primer)
suavizar(o_cristal)


# ==================================================================
# 2. CARROSSEL ÓPTICO GIRATÓRIO ('giro')
# ==================================================================
# Gira continuamente em 360° ao redor do cristal central (eixo Z em X=0, Y=0)
bm_giro_fe = bmesh.new()
bm_giro_ac = bmesh.new()
bm_giro_cr = bmesh.new()
bm_giro_vd = bmesh.new()

# Anel giratório de base sobre a coroa dentada
cil(bm_giro_fe, (0, 0, Z_TOPO_TORRE + 0.075), 0.16, 0.025, lados=24)
toro(bm_giro_ac, (0, 0, Z_TOPO_TORRE + 0.088), 0.15, 0.010, nR=24, nr=5)

# Dois arcos verticais de sustentação do sistema óptico (em X = -0.16 e X = +0.16)
for sx in (-0.15, 0.15):
    # Braço arqueado em ferradura suportando a óptica
    viga(bm_giro_fe, (sx, -0.06, Z_TOPO_TORRE + 0.08), (sx, -0.18, Z_CRISTAL), 0.022)
    viga(bm_giro_fe, (sx, -0.18, Z_CRISTAL), (sx, 0.0, Z_CRISTAL + 0.28), 0.022)
    viga(bm_giro_fe, (sx, 0.0, Z_CRISTAL + 0.28), (sx, 0.16, Z_CRISTAL), 0.022)
    viga(bm_giro_fe, (sx, 0.16, Z_CRISTAL), (sx, 0.06, Z_TOPO_TORRE + 0.08), 0.022)

# LADO FOCAL FRONTAL (+Y): Grande lente condensadora cilíndrica com moldura
caixa(bm_giro_ac, (0.0, 0.17, Z_CRISTAL), (0.24, 0.025, 0.32))
# Vidro da lente (disco abaulado com estrias tipo Fresnel)
cil(bm_giro_vd, (0.0, 0.175, Z_CRISTAL), 0.12, 0.018, eixo=Vector((0, 1, 0)), lados=18)
toro(bm_giro_ac, (0.0, 0.185, Z_CRISTAL), 0.12, 0.010, nR=18, nr=4, rot=Matrix.Rotation(math.radians(90), 3, 'X'))
toro(bm_giro_ac, (0.0, 0.185, Z_CRISTAL), 0.07, 0.007, nR=14, nr=4, rot=Matrix.Rotation(math.radians(90), 3, 'X'))

# LADO REFLETOR TRASEIRO (-Y): Espelho parabólico cromado de alta refletividade
# Perfil côncavo virado para o cristal (+Y)
pts_espelho = []
for ang_e in (k * 2 * PI / 16 for k in range(16)):
    ex = 0.13 * math.cos(ang_e)
    ez = Z_CRISTAL + 0.14 * math.sin(ang_e)
    ey = -0.17 + (ex * ex + (ez - Z_CRISTAL) ** 2) * 1.8
    pts_espelho.append(Vector((ex, ey, ez)))
for a, b in zip(pts_espelho, pts_espelho[1:] + [pts_espelho[0]]):
    tubo(bm_giro_cr, a, b, 0.010, lados=6)
# Chapa de fundo do espelho parabólico
caixa(bm_giro_cr, (0.0, -0.165, Z_CRISTAL), (0.22, 0.018, 0.26))

# COROA TOPO: Anel toroidal anti-estático (amortecedor de corona) no topo da lanterna
Z_CORONA = Z_CRISTAL + 0.32
toro(bm_giro_cr, (0, 0, Z_CORONA), 0.14, 0.014, nR=20, nr=6)
# Haste central captora afilada
cil(bm_giro_ac, (0, 0, Z_CORONA + 0.08), 0.012, 0.16, lados=8, r2=0.002)

# Cria os objetos móveis do carrossel
o_giro_fe = obj('giro_ferro', bm_giro_fe, 'ferro')
o_giro_ac = obj('giro_aco', bm_giro_ac, 'aco')
o_giro_cr = obj('giro_cromo', bm_giro_cr, 'cromo')
o_giro_vd = obj('giro_lente', bm_giro_vd, 'vidro_lente')
suavizar(o_giro_ac)
suavizar(o_giro_cr)

# Empty pai do carrossel giratório
empty_giro = bpy.data.objects.new('giro', None)
empty_giro.empty_display_type = 'ARROWS'
empty_giro.location = Vector((0, 0, 0))
sc.collection.objects.link(empty_giro)

for o in (o_giro_fe, o_giro_ac, o_giro_cr, o_giro_vd):
    o.parent = empty_giro


# ==================================================================
# 3. ILUMINAÇÃO DIRECIONAL E EFEITOS DE CENA
# ==================================================================
# Luz pontual volumétrica de alta intensidade no cristal
luz_cristal_d = bpy.data.lights.new('EFEITO_LuzCristal', 'POINT')
luz_cristal_d.color = (1.0, 0.70, 0.22)
luz_cristal_d.energy = 45.0
luz_cristal_d.shadow_soft_size = 0.06
luz_cristal = bpy.data.objects.new('EFEITO_LuzCristal', luz_cristal_d)
sc.collection.objects.link(luz_cristal)
luz_cristal.location = Vector((0, 0, Z_CRISTAL))

# Feixe concentrado direcionado (Spot) acoplado ao carrossel giratório
spot_farol_d = bpy.data.lights.new('EFEITO_SpotFarol', 'SPOT')
spot_farol_d.color = (1.0, 0.75, 0.25)
spot_farol_d.energy = 120.0
spot_farol_d.spot_size = math.radians(48)
spot_farol_d.spot_blend = 0.25
spot_farol_d.shadow_soft_size = 0.05
spot_farol = bpy.data.objects.new('EFEITO_SpotFarol', spot_farol_d)
sc.collection.objects.link(spot_farol)
spot_farol.parent = empty_giro
spot_farol.location = Vector((0, 0.20, Z_CRISTAL))
spot_farol.rotation_euler = (math.radians(-90), 0, 0)  # Aponta para +Y (frente da lente)

# Chão e sol de ambiente industrial
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (10, 10, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 2.8  # Luz ambiente mais suave para evidenciar o poder luminoso do farol
sol_d.angle = math.radians(2.0)
o_sol = bpy.data.objects.new('Sol', sol_d)
sc.collection.objects.link(o_sol)
o_sol.rotation_euler = (math.radians(50), 0, math.radians(-40))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.45, 0.52, 0.65, 1.0)
bg.inputs['Strength'].default_value = 0.40


# ------------------------------------------------------------------ ANIMAÇÃO DE 96 QUADROS (4 s)
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS  # 0.0 a 1.0

    # 1. Rotação azimutal contínua do carrossel óptico (360° em 4 s)
    ang_z = t * 2 * PI
    empty_giro.rotation_euler = Euler((0, 0, ang_z), 'XYZ')
    empty_giro.keyframe_insert('rotation_euler', frame=q)

    # 2. Pulso de ressonância do cristal (onda de choque luminosa contínua)
    pulso = 12.0 + 5.0 * math.sin(t * 2 * PI * 3) + 2.0 * math.sin(t * 2 * PI * 6)
    bsdf_cristal.inputs['Emission Strength'].default_value = pulso
    bsdf_cristal.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)

    luz_cristal_d.energy = pulso * 3.5
    luz_cristal_d.keyframe_insert('energy', frame=q)

    spot_farol_d.energy = 100.0 + pulso * 3.0
    spot_farol_d.keyframe_insert('energy', frame=q)

    # 3. Lâmpada de alta tensão pulsando
    f_aviso = 8.0 if (q % 12) < 4 else 1.5
    mat_led_alta_tensao.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = f_aviso
    mat_led_alta_tensao.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value', frame=q)


# Suaviza curvas de interpolação
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


def mirar(pos, alvo, lente=38):
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
    sc.frame_set(16)  # Posição angular elegante do carrossel óptico

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.0), (210, 2.2), (120, 2.4), (30, 1.9))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 3.6, math.sin(a) * 3.6, alt - ALVO.z))
        mirar(pos_cam, ALVO, 38)
        sc.render.filepath = os.path.join(AQUI, 'farol_cristal_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada da cabeça de cristal, lentes e mecânica de rotação
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(16)
        mirar(Vector((0.68, 0.72, Z_CRISTAL + 0.22)), Vector((0.0, 0.05, Z_CRISTAL)), 42)
        sc.render.filepath = os.path.join(AQUI, 'farol_cristal_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(16)
    mirar(ALVO + Vector((2.2, -2.4, 1.2)), ALVO, 38)
    sc.render.filepath = os.path.join(AQUI, 'farol_cristal_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('FAROL_CRISTAL ok (%d tris)' % tot_tri)
