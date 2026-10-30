"""Estudo isolado (fora do jogo): ACUMULADOR DE CRISTAL da IA, 2×2 tiles (lote 14, energia II).
Capacidade nominal: 600 MJ, potência de pico: 4 MW. Desbloqueado por 'ciencia_tempestade' e 'acumulacao_2'.
Bocas: — (banco de armazenamento eletrostático quântico de alta densidade conectado diretamente à rede).

Engenharia de supercondutividade e confinamento piezoelétrico da IA:
- Base de concreto armado 1,92 × 1,92 m chanfrada nos 4 cantos com canaletas de contenção dielétrica e chapas de ancoragem.
- 4 câmaras prismáticas colossais de cristal piezoelétrico em titânio escuro e latão industrial com 4 colunas de tirantes
  tensores de alta resistência mecânica, anéis toroidais de confinamento de campo eletrostático e visores de quartzo blindado.
- No interior de cada câmara: um cristal lapidado monumental de tempestade (violeta elétrico luminescente) levitando em suspensão
  eletrostática entre garras de ouro e anéis de foco polarizado.
- Coluna central de monitoramento e distribuição quântica:
  - Display vertical de carga formado por 16 segmentos de barras de LED de alta intensidade (indicando 0 a 600 MJ).
  - Anel toroidal de focalização magnética no topo girando continuamente no eixo Z.
  - Cristal central estabilizador de harmônicos com pulso volumétrico de luminescência.
- Sistema de controle térmico criogênico a leste: radiador aletado de cobre com ventilador axial veloz,
  bomba magnética em bronze com visor de vazão e tubulação aletada de recirculação ligando as 4 câmaras.
- Conexões de alta tensão ao sul: barramentos maciços laminados de cobre sobre cavalete reforçado com isoladores cerâmicos.
- Efeitos eletrostáticos: micro-arcos e pulsos de luminescência sincronizados com o ciclo de carga/descarga da rede.

Peças animadas separadas:
- 'ventoinha_radiador': ventilador axial de resfriamento do módulo criogênico girando continuamente a 6 voltas por ciclo.
- 'anel_foco': anel toroidal superior de focalização magnética girando a 360° em Z.
- 'cristal_centro': cristal central ressonante no topo com pulso harmônico de escala e emissão.
- 'cristal_0'..'cristal_3': os 4 grandes cristais de tempestade pulsando em luminescência e escala.
- 'led_barra0'..'led_barra15': 16 barras de LED da coluna central acendendo progressivamente conforme o nível de carga.

Uso: blender -b --python estudo_acumulador_cristal.py -- foto
     blender -b --python estudo_acumulador_cristal.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço fechado
random.seed(523)
Z_VEC = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

# Cotas padronizadas
Z_LAJE = 0.08
Z_PED = 0.22
Z_CAMARA_BASE = 0.24
Z_CAMARA_TOPO = 1.35
R_CAMARA = 0.30              # raio da carcaça de cada câmara de cristal
DIST_CAMARA = 0.52           # distância do centro aos 4 pilares

# ------------------------------------------------------------------ utilidades geométricas
def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o

def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))

def cano(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.12:
            for c in (a + u * 0.04, b - u * 0.04):
                tubo(bf, c - u * 0.007, c + u * 0.007, r * 1.45, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)

def casca(bm, c, r_out, r_in, z0, z1, n=24):
    c_xy = Vector((c[0], c[1], 0.0))
    an = []
    for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
        an.append([bm.verts.new(c_xy + Vector((r * math.cos(2 * PI * k / n), r * math.sin(2 * PI * k / n), z)))
                   for k in range(n)])
    for i in range(4):
        A, B = an[i], an[(i + 1) % 4]
        for k in range(n):
            bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))

def hexa(bm, c, r, z0, z1, ponta=0.0):
    cil(bm, Vector((c[0], c[1], (z0 + z1) / 2)), r, z1 - z0, lados=6)
    if ponta > 0:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=0.0, depth=ponta,
                              matrix=Matrix.Translation((c[0], c[1], z1 + ponta / 2)))

def toro(bm, centro, R, r, nR=32, nr=10, rot=Matrix.Identity(3)):
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))

# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

def vidro_mat():
    m = bpy.data.materials.new('VidroDielétrico')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.85, 0.95, 1)
    b.inputs['Transmission Weight'].default_value = 0.96
    b.inputs['Roughness'].default_value = 0.03
    b.inputs['Alpha'].default_value = 0.32
    b.inputs['IOR'].default_value = 1.52
    return m

def cristal_mat(nome, cor, forca=3.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Transmission Weight'].default_value = 0.75
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['IOR'].default_value = 1.65
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

base3d.M.update({
    'titânio': mats.material('TitânioEscuro', (0.12, 0.13, 0.15), 0.9, 0.35, pintura=False, sujeira=0.6, escovado=True),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.85, ferrugem=0.35),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'bronze': mats.material('Bronze', (0.55, 0.38, 0.18), 1.0, 0.35, pintura=False, sujeira=0.7),
    'ouro': mats.material('OuroConfinamento', (0.88, 0.72, 0.16), 1.0, 0.18, pintura=False, sujeira=0.2),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'vidro': vidro_mat(),
    'cristal_tempestade': cristal_mat('CristalTempestade', (0.6, 0.15, 1.0), 4.5),
    'cristal_centro': cristal_mat('CristalCentro', (0.2, 0.85, 1.0), 6.0),
    'led_carga_on': luz_mat('LedCargaOn', (0.1, 0.95, 0.9), 12.0),
    'led_carga_off': luz_mat('LedCargaOff', (0.02, 0.08, 0.10), 0.2),
    'campo': luz_mat('CampoEletrostatico', (0.5, 0.2, 1.0), 8.0),
})

# ------------------------------------------------------------------ BASE E LAJE DE CONCRETO (2x2 tiles)
bm = bmesh.new()
# Laje 1.92 x 1.92 m com cantos chanfrados
caixa_de(bm, (-0.96, -0.96, 0), (0.96, 0.96, Z_LAJE))
# Canaletas de contenção de fluido dielétrico no perímetro
for x_d in (-0.88, 0.88):
    caixa_de(bm, (x_d - 0.03, -0.88, Z_LAJE - 0.01), (x_d + 0.03, 0.88, Z_LAJE + 0.002))
for y_d in (-0.88, 0.88):
    caixa_de(bm, (-0.88, y_d - 0.03, Z_LAJE - 0.01), (0.88, y_d + 0.03, Z_LAJE + 0.002))
# Pedestais octogonais para as 4 câmaras
for dx, dy in ((-DIST_CAMARA, -DIST_CAMARA), (DIST_CAMARA, -DIST_CAMARA),
              (-DIST_CAMARA, DIST_CAMARA), (DIST_CAMARA, DIST_CAMARA)):
    cil(bm, Vector((dx, dy, (Z_LAJE + Z_PED) / 2)), R_CAMARA + 0.04, Z_PED - Z_LAJE, lados=8)
obj('laje_concreto', bm, 'concreto')

# Demarcações de segurança zebradas e chapas de aço
bm = bmesh.new()
for dx, dy in ((-DIST_CAMARA, -DIST_CAMARA), (DIST_CAMARA, -DIST_CAMARA),
              (-DIST_CAMARA, DIST_CAMARA), (DIST_CAMARA, DIST_CAMARA)):
    caixa_de(bm, (dx - 0.32, dy - 0.32, Z_PED), (dx + 0.32, dy + 0.32, Z_CAMARA_BASE))
obj('camaras_chapa_base', bm, 'aco')

# ------------------------------------------------------------------ 4 CÂMARAS MONUMENTAIS DE CRISTAL DE TEMPESTADE
bm_est, bm_vidro, bm_ouro, bm_cobre = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

pos_camaras = [
    Vector((-DIST_CAMARA, -DIST_CAMARA, 0)),
    Vector(( DIST_CAMARA, -DIST_CAMARA, 0)),
    Vector((-DIST_CAMARA,  DIST_CAMARA, 0)),
    Vector(( DIST_CAMARA,  DIST_CAMARA, 0))
]

cristais_objs = []

for i_c, p_c in enumerate(pos_camaras):
    # Cilindro de quartzo blindado translúcido da câmara
    cil(bm_vidro, p_c + Vector((0, 0, (Z_CAMARA_BASE + Z_CAMARA_TOPO) / 2)),
        R_CAMARA - 0.03, Z_CAMARA_TOPO - Z_CAMARA_BASE, lados=18)
    
    # Base e topo maciços em titânio e latão
    cil(bm_est, p_c + Vector((0, 0, Z_CAMARA_BASE + 0.04)), R_CAMARA + 0.02, 0.08, lados=16)
    cil(bm_est, p_c + Vector((0, 0, Z_CAMARA_TOPO - 0.04)), R_CAMARA + 0.02, 0.08, lados=16)
    
    # 4 colunas de tirantes tensores de alta pressão por câmara
    for a in range(4):
        ang = a * PI / 2 + PI / 4
        d_tir = Vector((math.cos(ang), math.sin(ang), 0))
        p_tir = p_c + d_tir * (R_CAMARA + 0.015)
        tubo(bm_est, p_tir + Vector((0, 0, Z_CAMARA_BASE)), p_tir + Vector((0, 0, Z_CAMARA_TOPO)), 0.012, 10)
        # Porcas sextavadas nos topos dos tirantes
        cil(bm_est, p_tir + Vector((0, 0, Z_CAMARA_TOPO + 0.01)), 0.018, 0.02, lados=6)
        
    # Anéis de confinamento eletrostático externos (toroides de cobre aletados)
    for z_anel in (0.48, 0.78, 1.08):
        toro(bm_cobre, p_c + Vector((0, 0, z_anel)), R_CAMARA + 0.01, 0.018, nR=24, nr=8)
        
    # Garras polares internas de ouro suportando o campo de levitação
    for z_g, dir_g in ((Z_CAMARA_BASE + 0.12, 1), (Z_CAMARA_TOPO - 0.12, -1)):
        cil(bm_ouro, p_c + Vector((0, 0, z_g)), 0.08, 0.04, lados=12)
        for a in range(3):
            ang = a * 2 * PI / 3
            d_garra = Vector((math.cos(ang), math.sin(ang), 0))
            tubo(bm_ouro, p_c + Vector((0, 0, z_g)), p_c + d_garra * 0.12 + Vector((0, 0, z_g + dir_g * 0.08)), 0.012, 8)

    # Grande cristal de tempestade móvel/pulsante dentro da câmara
    c_obj = bpy.data.objects.new(f'cristal_{i_c}', None)
    sc.collection.objects.link(c_obj)
    c_obj.location = p_c + Vector((0, 0, (Z_CAMARA_BASE + Z_CAMARA_TOPO) / 2))
    
    bm_cristal = bmesh.new()
    # Prisma hexagonal lapidado com pontas duplas
    hexa(bm_cristal, Vector((0, 0, 0)), 0.12, -0.32, 0.32, ponta=0.18)
    # Ponta inferior invertida
    bmesh.ops.create_cone(bm_cristal, cap_ends=True, segments=6, radius1=0.12, radius2=0.0, depth=0.18,
                          matrix=Matrix.Translation((0, 0, -0.32 - 0.09)) @ Matrix.Rotation(PI, 3, 'X').to_4x4())
    obj(f'cristal_{i_c}_mesh', bm_cristal, 'cristal_tempestade', c_obj)
    cristais_objs.append(c_obj)

obj('camaras_estrutura', bm_est, 'titânio')
obj('camaras_vidro', bm_vidro, 'vidro')
obj('camaras_ouro_garras', bm_ouro, 'ouro')
obj('camaras_cobre_aneis', bm_cobre, 'cobre')

# ------------------------------------------------------------------ COLUNA CENTRAL E DISPLAY VERTICAL DE CARGA (16 LEDs)
bm_col, bm_leds_base = bmesh.new(), bmesh.new()
# Coluna octogonal central
cil(bm_col, Vector((0, 0, (Z_LAJE + 1.45) / 2)), 0.18, 1.45 - Z_LAJE, lados=8)
# Anéis decorativos de latão na coluna
for z_an in (0.35, 0.75, 1.15, 1.45):
    toro(bm_col, Vector((0, 0, z_an)), 0.19, 0.014, nR=24, nr=8)

# Painel frontal (sul) para as 16 barras de LEDs de carga
caixa_de(bm_col, (-0.09, -DIST_CAMARA + 0.22, 0.26), (0.09, -DIST_CAMARA + 0.25, 1.40))
obj('coluna_central_corpo', bm_col, 'titânio')

# 16 barras de LED individuais animadas
leds_objs = []
Z_LED0 = 0.30
DZ_LED = 0.065
for i_led in range(16):
    z_l = Z_LED0 + i_led * DZ_LED
    led_o = bpy.data.objects.new(f'led_barra{i_led}', None)
    sc.collection.objects.link(led_o)
    led_o.location = Vector((0, -DIST_CAMARA + 0.255, z_l))
    bm_l = bmesh.new()
    caixa(bm_l, Vector((0, 0, 0)), (0.12, 0.012, 0.035))
    obj(f'led_barra{i_led}_mesh', bm_l, 'led_carga_on', led_o)
    leds_objs.append(led_o)

# ------------------------------------------------------------------ TOPO DA COLUNA: ANEL DE LEVITAÇÃO E CRISTAL CENTRAL
bm_prato = bmesh.new()
# Prato emissor superior
cil(bm_prato, Vector((0, 0, 1.50)), 0.28, 0.06, Z_VEC, lados=16)
for a in range(4):
    ang = a * PI / 2
    d_br = Vector((math.cos(ang), math.sin(ang), 0))
    tubo(bm_prato, Vector((0, 0, 1.50)), d_br * 0.32 + Vector((0, 0, 1.58)), 0.016, 8)
obj('prato_emissor_topo', bm_prato, 'ouro')

# Anel toroidal de focalização magnética giratório
anel_foco = bpy.data.objects.new('anel_foco', None)
sc.collection.objects.link(anel_foco)
anel_foco.location = Vector((0, 0, 1.62))
bm_af = bmesh.new()
toro(bm_af, Vector((0, 0, 0)), 0.24, 0.022, nR=24, nr=8)
for a in range(4):
    ang = a * PI / 2
    d_a = Vector((math.cos(ang), math.sin(ang), 0))
    cil(bm_af, d_a * 0.24, 0.03, 0.04, Z_VEC, lados=8)
obj('anel_foco_mesh', bm_af, 'campo', anel_foco)

# Cristal central estabilizador de alta densidade
cristal_centro = bpy.data.objects.new('cristal_centro', None)
sc.collection.objects.link(cristal_centro)
cristal_centro.location = Vector((0, 0, 1.62))
bm_cc = bmesh.new()
hexa(bm_cc, Vector((0, 0, 0)), 0.075, -0.14, 0.14, ponta=0.10)
# Ponta inferior
bmesh.ops.create_cone(bm_cc, cap_ends=True, segments=6, radius1=0.075, radius2=0.0, depth=0.10,
                      matrix=Matrix.Translation((0, 0, -0.14 - 0.05)) @ Matrix.Rotation(PI, 3, 'X').to_4x4())
obj('cristal_centro_mesh', bm_cc, 'cristal_centro', cristal_centro)

# ------------------------------------------------------------------ BARRAMENTOS DE COBRE E ISOLADORES DE REDE (Sul)
bm_bar, bm_iso = bmesh.new(), bmesh.new()
# Cavalete de isoladores cerâmicos na face sul
Y_CAV = -0.85
for ix in (-0.35, 0.0, 0.35):
    for iz in range(4):
        cil(bm_iso, Vector((ix, Y_CAV, 0.12 + iz * 0.05)), 0.04 - iz * 0.005, 0.04, lados=12)
    # Terminal de cobre do polo
    cil(bm_bar, Vector((ix, Y_CAV, 0.34)), 0.02, 0.05, lados=8)
    # Barramento laminado maciço subindo para a coluna central
    tubo(bm_bar, Vector((ix, Y_CAV, 0.36)), Vector((ix * 0.4, -0.22, 0.45)), 0.016, 10)

# Barramentos radiais conectando as 4 câmaras à coluna central
for p_c in pos_camaras:
    p_polo = p_c + (Vector((0, 0, 0)) - p_c).normalized() * R_CAMARA + Vector((0, 0, 0.65))
    p_centro = Vector((0, 0, 0.65)) + (p_c - Vector((0, 0, 0))).normalized() * 0.18
    tubo(bm_bar, p_polo, p_centro, 0.018, 10)
    # Conectores com parafusos
    cil(bm_bar, p_polo, 0.03, 0.03, lados=6)

obj('barramentos_cobre', bm_bar, 'cobre')
obj('isoladores_porcelana', bm_iso, 'titânio')

# ------------------------------------------------------------------ REFRIGERAÇÃO CRIOGÊNICA (Leste)
bm_rad, bm_alet = bmesh.new(), bmesh.new()
X_RAD, Y_RAD = 0.85, 0.0
# Chassi do radiador
caixa_de(bm_rad, (X_RAD - 0.10, Y_RAD - 0.32, Z_LAJE), (X_RAD + 0.09, Y_RAD + 0.32, 0.58))
# Aletas de cobre
for iz in range(10):
    z_a = Z_LAJE + 0.05 + iz * 0.045
    caixa_de(bm_alet, (X_RAD - 0.09, Y_RAD - 0.30, z_a), (X_RAD + 0.09, Y_RAD + 0.30, z_a + 0.012))
# Carenagem para ventoinha axial
casca(bm_rad, (X_RAD, Y_RAD, 0), 0.18, 0.14, 0.22, 0.50, 20)
obj('radiador_chassi', bm_rad, 'grafite')
obj('radiador_aletas', bm_alet, 'cobre')

# Ventoinha axial de resfriamento girando no eixo X
ventoinha = bpy.data.objects.new('ventoinha_radiador', None)
sc.collection.objects.link(ventoinha)
ventoinha.location = Vector((X_RAD, Y_RAD, 0.36))
bm_v = bmesh.new()
cil(bm_v, Vector((0, 0, 0)), 0.035, 0.02, Vector((1, 0, 0)), lados=12)
for k in range(5):
    ang = k * 2 * PI / 5
    rot_pa = Matrix.Rotation(ang, 3, 'X') @ Matrix.Rotation(0.35, 3, 'Y')
    caixa(bm_v, rot_pa @ Vector((0, 0.07, 0)), (0.004, 0.075, 0.025), rot_pa)
obj('ventoinha_mesh', bm_v, 'aluminio', ventoinha)

# Tubos de fluido criogênico ligando o radiador às câmaras
bm_tubos = bmesh.new()
for p_c in pos_camaras:
    p_base_c = p_c + Vector((0, 0, Z_CAMARA_BASE + 0.06))
    tubo(bm_tubos, Vector((X_RAD - 0.10, 0, 0.20)), p_base_c, 0.014, 8)
obj('tubos_refrigeracao', bm_tubos, 'aco')

# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço fechado a 24 fps)
em_cristal_temp = base3d.M['cristal_tempestade'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_cristal_cen = base3d.M['cristal_centro'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']

# Luzes pontuais internas para iluminação das câmaras
luzes_camaras = []
for i_c, p_c in enumerate(pos_camaras):
    l_data = bpy.data.lights.new(f'LuzCamara_{i_c}', 'POINT')
    l_data.color = (0.5, 0.2, 1.0)
    l_data.energy = 35.0
    l_obj = bpy.data.objects.new(f'EFEITO_LuzCamara_{i_c}', l_data)
    sc.collection.objects.link(l_obj)
    l_obj.location = p_c + Vector((0, 0, 0.80))
    luzes_camaras.append((l_data, l_obj))

for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS                     # progresso 0..1 do ciclo
    fase = 2 * PI * t
    
    # 1. Ventoinha do radiador: 6 voltas completas por ciclo
    ventoinha.rotation_euler = Euler((fase * 6, 0, 0), 'XYZ')
    ventoinha.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Anel toroidal superior de foco: rotação contínua em Z
    anel_foco.rotation_euler = Euler((0, 0, -fase), 'XYZ')
    anel_foco.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Ciclo de Carga e Descarga (simulação de 0 a 100% e de volta a 0%)
    # Carga cresce entre t=0 e 0.50; descarga entre t=0.50 e 1.00
    if t < 0.50:
        nivel_carga = t / 0.50
    else:
        nivel_carga = (1.0 - t) / 0.50
        
    # Animação da coluna de 16 LEDs indicadores de carga
    # Cada LED acende se nivel_carga >= (i / 16)
    leds_acesos = int(nivel_carga * 16.99)
    for i_led, led_o in enumerate(leds_objs):
        if i_led <= leds_acesos:
            # LED aceso e brilhando
            led_o.scale = Vector((1.0, 1.0, 1.0))
        else:
            # LED apagado / recolhido
            led_o.scale = Vector((0.4, 0.2, 0.4))
        led_o.keyframe_insert('scale', frame=q)
        
    # 4. Pulso de luminescência e escala nos 4 grandes cristais
    pulso_c = 0.5 + 0.5 * math.sin(fase * 2)
    escala_c = 1.0 + 0.06 * nivel_carga * pulso_c
    for i_c, c_obj in enumerate(cristais_objs):
        c_obj.scale = Vector((escala_c, escala_c, 1.0 + 0.04 * pulso_c))
        c_obj.rotation_euler = Euler((0, 0, fase * 0.5 * (1 if i_c % 2 == 0 else -1)), 'XYZ')
        c_obj.keyframe_insert('scale', frame=q)
        c_obj.keyframe_insert('rotation_euler', frame=q)
        
    # Brilho dos cristais proporcional à carga armazenada
    brilho_emissao = 2.0 + 8.0 * nivel_carga * (0.8 + 0.2 * pulso_c)
    em_cristal_temp.default_value = brilho_emissao
    em_cristal_temp.keyframe_insert('default_value', frame=q)
    
    for l_data, _ in luzes_camaras:
        l_data.energy = 15.0 + 40.0 * nivel_carga * (0.8 + 0.2 * pulso_c)
        l_data.keyframe_insert('energy', frame=q)
        
    # 5. Cristal central ressonante no topo
    pulso_cen = 0.5 + 0.5 * math.sin(fase * 4)
    cristal_centro.scale = Vector((1.0 + 0.08 * pulso_cen, 1.0 + 0.08 * pulso_cen, 1.0 + 0.12 * pulso_cen))
    cristal_centro.rotation_euler = Euler((0, 0, fase), 'XYZ')
    cristal_centro.keyframe_insert('scale', frame=q)
    cristal_centro.keyframe_insert('rotation_euler', frame=q)
    em_cristal_cen.default_value = 4.0 + 6.0 * pulso_cen
    em_cristal_cen.keyframe_insert('default_value', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('EFEITO_chao', bm, 'chao')

# Luz Solar
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(45), 0, math.radians(-35))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.65

# Cycles GPU OptiX
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
sc.view_settings.exposure = -0.35

cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente

ALVO = (0.0, 0.0, 0.85)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'ACUMULADOR_CRISTAL_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((300, 3.4, 0.25), (215, 3.2, 0.50), (120, 3.6, 0.75), (35, 3.0, 0.95))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.2, math.sin(a) * 4.2, alt - ALVO[2])), ALVO, 32)
        sc.render.filepath = os.path.join(AQUI, f'acumulador_cristal_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na câmara frontal de cristal, coluna de LEDs e anel de foco
    sc.frame_set(int(0.50 * FPS) + 1)  # no pico de 100% de carga
    mirar((0.95, -1.35, 1.30), (0.0, -0.25, 0.90), 36)
    sc.render.filepath = os.path.join(AQUI, 'acumulador_cristal_perto.png')
    bpy.ops.render.render(write_still=True)

print('ACUMULADOR_CRISTAL ok')
