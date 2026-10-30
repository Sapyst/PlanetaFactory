"""Estudo isolado (fora do jogo): FORJA QUÂNTICA da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'computacao_quantica' (destrava o regulador climático na árvore de tecnologia).
Fabrica itens de alta tecnologia quântica: processador quântico, pacote quântico e mapa estelar.

Bocas no padrão do jogo:
- ITEM_ENT_S1: esteira sul de componentes base (x = 0,0, y = -1,50 m, z = 0,23 m)
- ITEM_ENT_O1: esteira oeste de cristais e dopantes (x = -1,50 m, y = 0,0, z = 0,23 m)
- ITEM_SAI_N1: esteira norte de processadores e pacotes acabados (x = 0,0, y = +1,50 m, z = 0,23 m)
- FLUIDO_ENT_L1: tubulação leste de fluido refrigerante quântico criogênico a z = 0,35 m (x = +1,50 m, y = 0,0)

Engenharia de forjamento e emaranhamento quântico da IA:
- Base de concreto armado 2,96 × 2,96 m com canaletas de resfriamento, esteiras de roletes de aço nas bocas sul, oeste e norte.
- Câmara Central de Forjamento Quântico:
  * Vaso blindado octogonal de alta pressão e vácuo criogênico em titânio e chumbo, com anel toroidal de confinamento magnético em cobre.
  * Bigorna Quântica central levitante onde bolachas de cristal são emaranhadas sob feixes laser cruzados coerentes.
  * Prensa / Martelo Quântico vertical superior acionado por atuadores telescópicos cromados pesados e bobinas de indução linear.
  * 4 Janelas circulares de quartzo polarizado revelando o clarão pulsante e faíscas azuis/violetas de dobra molecular.
- Manipulação Mecatrônica Interna:
  * Braço alimentador SCARA de alta velocidade pegando componentes das esteiras de entrada e posicionando na bigorna.
  * Braço ejetor quântico empurrando processadores finalizados para a esteira norte de roletes.
- Circuito de Fluido Leste:
  * Bocal rígido flangeado a 0,35 m de altura com medidor de vazão de rotor aletado giratório e trocador de calor criogênico.
- Torre de Telemetria e Alinhamento Holográfico:
  * Carrossel óptico quântico no topo com anel rotativo e cristal lapidado projetando coordenadas e feixes de coerência.

Peças animadas separadas:
- 'martelo_quantico': êmbolo de compressão e forjamento quântico descendo no impacto e subindo suavemente.
- 'anel_confinamento': anel magnético toroidal superior girando continuamente a 360° em Z.
- 'carrossel_optico': prisma e coroa óptica no teto girando a 360° em Z.
- 'braco_alimenta': braço mecatrônico posicionando bolachas de cristal na câmara de forjamento.
- 'braco_ejetor': braço mecatrônico conduzindo peças finalizadas para a saída norte.
- 'rotor_fluxo': rotor do fluxômetro de refrigerante criogênico leste girando a 4 voltas por ciclo.
- 'rolete_s0'..'s3', 'rolete_o0'..'o3', 'rolete_n0'..'n3': roletes de aço das esteiras girando continuamente.
- 'peca_forjada_0', 'peca_forjada_1': processadores quânticos avançando na esteira norte.
- 'luz_forja': pulso harmônico de plasma violeta-ciano na câmara de forjamento durante a prensagem.

Uso: blender -b --python estudo_forja_quantica.py -- foto
     blender -b --python estudo_forja_quantica.py -- nada
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
Z_EST = 0.23                 # esteiras sul, oeste e norte
Z_CANO = 0.35                # tubo de fluido leste
Z_CAMARA = 0.85              # centro da câmara de forjamento

# ------------------------------------------------------------------ utilidades de geometria
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

def toro(bm, centro, R, r, nR=32, nr=12, rot=Matrix.Identity(3)):
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
    m = bpy.data.materials.new('VidroQuartzo')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.8, 0.95, 1.0, 1)
    b.inputs['Transmission Weight'].default_value = 0.94
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['Alpha'].default_value = 0.35
    b.inputs['IOR'].default_value = 1.54
    return m

base3d.M.update({
    'titânio': mats.material('TitânioEscuro', (0.12, 0.13, 0.15), 0.9, 0.35, pintura=False, sujeira=0.6, escovado=True),
    'aco': mats.material('AçoEstrutural', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('CobreCriogenico', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'ouro': mats.material('OuroSupercondutor', (0.95, 0.78, 0.22), 1.0, 0.18, pintura=False, sujeira=0.2),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'vidro': vidro_mat(),
    'plasma': luz_mat('PlasmaForja', (0.45, 0.2, 1.0), 22.0),
    'cristal_res': luz_mat('CristalOptico', (0.2, 0.85, 1.0), 16.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 12.0),
    'led_alerta': luz_mat('LedAlerta', (1.0, 0.2, 0.05), 10.0),
})

# ------------------------------------------------------------------ BASE E LAJE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base metálicas, guias e sapatas de ancoragem
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
# Cantoneiras e parafusos de ancoragem nos cantos
for cx, cy in ((-1.30, -1.30), (1.30, -1.30), (-1.30, 1.30), (1.30, 1.30)):
    caixa_de(bm_aco, (cx - 0.12, cy - 0.12, Z_LAJE + 0.02), (cx + 0.12, cy + 0.12, Z_LAJE + 0.06))
    hexa(bm_aco, (cx, cy), 0.03, Z_LAJE + 0.06, Z_LAJE + 0.09)

# Listras de perigo industrial ao redor do perímetro de operação
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ BOCAS E ESTEIRAS (SUL, OESTE, NORTE)
# Bocas de esteira de itens a Z_EST = 0.23 m
# Cada esteira tem guias laterais, suportes e 4 roletes giratórios de aço
ESTEIRAS_CONFIG = [
    ('sul', Vector((0.0, -1.50, Z_EST)), Vector((0.0, 1.0, 0.0)), 0.65),
    ('oeste', Vector((-1.50, 0.0, Z_EST)), Vector((1.0, 0.0, 0.0)), 0.65),
    ('norte', Vector((0.0, 1.50, Z_EST)), Vector((0.0, -1.0, 0.0)), 0.65)
]

bm_est_guias = bmesh.new()
rolete_objs = []

for nome_e, p_boca, dir_int, comp in ESTEIRAS_CONFIG:
    u_lat = dir_int.cross(Z_VEC).normalized()
    p_fim = p_boca + dir_int * comp
    # Guias laterais da esteira
    for sgn in (-1, 1):
        p1 = p_boca + u_lat * (sgn * 0.22)
        p2 = p_fim + u_lat * (sgn * 0.22)
        viga(bm_est_guias, p1 + Vector((0, 0, -0.04)), p2 + Vector((0, 0, -0.04)), 0.04)
        viga(bm_est_guias, p1 + Vector((0, 0, 0.04)), p2 + Vector((0, 0, 0.04)), 0.025)
    # Suportes verticais ao piso
    for s in (0.15, 0.45):
        p_sup = p_boca + dir_int * s
        for sgn in (-1, 1):
            tubo(bm_est_guias, p_sup + u_lat * (sgn * 0.22) + Vector((0, 0, -0.04)),
                 Vector((p_sup[0] + u_lat[0] * sgn * 0.22, p_sup[1] + u_lat[1] * sgn * 0.22, Z_LAJE)), 0.025, 8)
    # 4 Roletes giratórios separados
    for r_i in range(4):
        s = 0.08 + r_i * 0.16
        p_rol = p_boca + dir_int * s
        bm_r = bmesh.new()
        cil(bm_r, (0, 0, 0), 0.035, 0.40, eixo=u_lat, lados=12)
        # Eixo central
        cil(bm_r, (0, 0, 0), 0.012, 0.46, eixo=u_lat, lados=8)
        r_o = obj(f'rolete_{nome_e}_{r_i}', bm_r, 'cromo')
        r_o.location = p_rol
        suavizar(r_o)
        rolete_objs.append((r_o, u_lat))

obj('esteiras_guias', bm_est_guias, 'titânio')

# ------------------------------------------------------------------ BOCA LESTE DE FLUIDO REFRIGERANTE CRIOGÊNICO
# Bocal de fluido rígido a x = +1.50 m, y = 0.0, z = 0.35 m
p_fluido = Vector((1.50, 0.0, Z_CANO))
bm_tubo_fluido = bmesh.new()
bm_flange_fluido = bmesh.new()

# Flange de engate padronizada da boca leste
tubo(bm_flange_fluido, p_fluido, p_fluido - Vector((0.08, 0, 0)), 0.085, 16)
tubo(bm_tubo_fluido, p_fluido - Vector((0.08, 0, 0)), p_fluido - Vector((0.35, 0, 0)), 0.055, 16)
# Caixa do medidor de vazão (fluxômetro criogênico)
p_medidor = p_fluido - Vector((0.48, 0, 0))
caixa_de(bm_flange_fluido, (p_medidor[0] - 0.09, -0.09, Z_CANO - 0.09), (p_medidor[0] + 0.09, 0.09, Z_CANO + 0.09))
# Tubo descendo e entrando no trocador de calor criogênico lateral
cano(bm_tubo_fluido, bm_flange_fluido, [
    (p_medidor[0] - 0.09, 0.0, Z_CANO),
    (p_medidor[0] - 0.25, 0.0, Z_CANO),
    (p_medidor[0] - 0.25, 0.35, Z_CANO),
    (0.85, 0.35, Z_LAJE + 0.22)
], 0.045, flange=True)

obj('tubo_fluido_leste', bm_tubo_fluido, 'cobre')
obj('flange_fluido_leste', bm_flange_fluido, 'titânio')

# Rotor aletado do medidor de vazão (animado separadamente)
bm_rot = bmesh.new()
cil(bm_rot, (0, 0, 0), 0.02, 0.06, eixo=Vector((1, 0, 0)), lados=10)
for a_i in range(4):
    ang = a_i * PI / 2
    bmesh.ops.create_cube(bm_rot, size=1.0, matrix=Matrix.Translation((0, 0.035 * math.cos(ang), 0.035 * math.sin(ang))) @
                          Matrix.Rotation(ang, 3, 'X').to_4x4() @ Matrix.Scale(0.05, 4, Vector((1, 0, 0))) @
                          Matrix.Scale(0.008, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.04, 4, Vector((0, 0, 1))))
rotor_fluxo = obj('rotor_fluxo', bm_rot, 'latao')
rotor_fluxo.location = p_medidor
suavizar(rotor_fluxo)

# ------------------------------------------------------------------ CÂMARA DE FORJAMENTO QUÂNTICO CENTRAL
# Estrutura cilíndrica-octogonal monumental com blindagem em titânio e chumbo
bm_camara = bmesh.new()
bm_vidro = bmesh.new()
bm_cobre = bmesh.new()
bm_ouro = bmesh.new()

# Pedestal inferior da câmara
casca(bm_camara, (0, 0, 0), 0.88, 0.72, Z_LAJE + 0.02, 0.40, n=24)
cil(bm_camara, (0, 0, 0.40), 0.76, 0.04, lados=24)

# 8 Colunas angulares de sustentação com tirantes de pré-tensão
for i in range(8):
    a = i * 2 * PI / 8
    p_col = Vector((0.82 * math.cos(a), 0.82 * math.sin(a), 0.42))
    viga(bm_camara, p_col, p_col + Vector((0, 0, 0.95)), 0.08)
    hexa(bm_aco, (p_col[0], p_col[1]), 0.022, 1.38, 1.42)

# Vaso de vácuo central octogonal com aberturas para as esteiras e janelas de quartzo
casca(bm_camara, (0, 0, 0), 0.74, 0.64, 0.42, 1.36, n=8)
# Anéis toroidais de aperto e confinamento em cobre criogênico
toro(bm_cobre, (0, 0, 0.55), 0.75, 0.035, nR=24, nr=10)
toro(bm_cobre, (0, 0, 0.95), 0.75, 0.035, nR=24, nr=10)
toro(bm_cobre, (0, 0, 1.30), 0.75, 0.035, nR=24, nr=10)

# 4 Janelas circulares de quartzo polarizado nas diagonais da câmara
for ang_diag in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
    d_jan = Vector((math.cos(ang_diag), math.sin(ang_diag), 0))
    p_jan = d_jan * 0.74 + Vector((0, 0, Z_CAMARA))
    rot_jan = d_jan.to_track_quat('Z', 'Y').to_matrix().to_3x3()
    # Aro de latão da janela
    toro(bm_ouro, p_jan, 0.16, 0.025, nR=16, nr=8, rot=rot_jan)
    # Lente de quartzo translúcida
    cil(bm_vidro, p_jan, 0.14, 0.02, eixo=d_jan, lados=16)

# Bigorna Quântica central levitante (z = 0.56 m)
caixa_de(bm_camara, (-0.30, -0.30, 0.42), (0.30, 0.30, 0.54))
# Matriz de indução em anel de ouro sobre a bigorna
toro(bm_ouro, (0, 0, 0.55), 0.22, 0.025, nR=20, nr=8)
# Emaranhador central: prisma de cristal facetado no centro da bigorna
bmesh.ops.create_cone(bm_vidro, cap_ends=True, segments=8, radius1=0.10, radius2=0.06, depth=0.08,
                      matrix=Matrix.Translation((0, 0, 0.58)))

obj('camara_corpo', bm_camara, 'titânio')
obj('camara_janelas_vidro', bm_vidro, 'vidro')
obj('camara_aneis_cobre', bm_cobre, 'cobre')
obj('camara_aros_ouro', bm_ouro, 'ouro')

# ------------------------------------------------------------------ PRENSA / MARTELO QUÂNTICO VERTICAL
# Êmbolo telescópico superior acionado hidraulicamente com bobinas de indução linear
bm_martelo = bmesh.new()
# Pistão telescópico cromado superior
cil(bm_martelo, (0, 0, 0.50), 0.10, 0.65, lados=16)
# Cabeçote prensador com ranhuras de focalização quântica
caixa_de(bm_martelo, (-0.24, -0.24, 0.0), (0.24, 0.24, 0.20))
# Matriz de estampagem inferior em latão/ouro
toro(bm_martelo, (0, 0, 0.04), 0.18, 0.022, nR=16, nr=8)
# 4 Projeções de laser de coerência molecular nos 4 cantos da prensa
for dx, dy in ((-0.20, -0.20), (0.20, -0.20), (-0.20, 0.20), (0.20, 0.20)):
    cil(bm_martelo, (dx, dy, -0.04), 0.03, 0.09, lados=8)
    bmesh.ops.create_cone(bm_martelo, cap_ends=True, segments=6, radius1=0.015, radius2=0.0, depth=0.06,
                          matrix=Matrix.Translation((dx, dy, -0.10)))

martelo_quantico = obj('martelo_quantico', bm_martelo, 'cromo')
# Posição inicial de repouso elevada
martelo_quantico.location = Vector((0, 0, 1.15))
suavizar(martelo_quantico)

# Anel magnético toroidal superior giratório de confinamento (z = 1.45 m)
bm_anel_giro = bmesh.new()
toro(bm_anel_giro, (0, 0, 0), 0.82, 0.042, nR=32, nr=12)
# 6 Bobinas supercondutoras distribuídas no anel
for k in range(6):
    a = k * 2 * PI / 6
    pos_b = Vector((0.82 * math.cos(a), 0.82 * math.sin(a), 0))
    rot_b = Matrix.Rotation(a, 3, 'Z')
    toro(bm_anel_giro, pos_b, 0.07, 0.02, nR=14, nr=6, rot=rot_b)
anel_confinamento = obj('anel_confinamento', bm_anel_giro, 'cobre')
anel_confinamento.location = Vector((0, 0, 1.45))
suavizar(anel_confinamento)

# Carrossel óptico quântico no topo (z = 1.68 m) com prisma e feixes
bm_optico = bmesh.new()
cil(bm_optico, (0, 0, 0), 0.28, 0.06, lados=20)
# Prisma central lapidado
bmesh.ops.create_cone(bm_optico, cap_ends=True, segments=6, radius1=0.14, radius2=0.0, depth=0.18,
                      matrix=Matrix.Translation((0, 0, 0.12)))
# 3 Lentes satélites orbitais em suportes articulados
for l_i in range(3):
    a_l = l_i * 2 * PI / 3
    pos_l = Vector((0.42 * math.cos(a_l), 0.42 * math.sin(a_l), 0.04))
    tubo(bm_optico, (0, 0, 0.02), pos_l, 0.015, 8)
    toro(bm_optico, pos_l, 0.06, 0.012, nR=12, nr=6)

carrossel_optico = obj('carrossel_optico', bm_optico, 'ouro')
carrossel_optico.location = Vector((0, 0, 1.68))
suavizar(carrossel_optico)

# Cristal quântico central do carrossel emitindo feixe vertical
bm_c_topo = bmesh.new()
hexa(bm_c_topo, (0, 0), 0.08, 0, 0.22, ponta=0.08)
cristal_topo = obj('cristal_topo', bm_c_topo, 'cristal_res', pai=carrossel_optico)
cristal_topo.location = Vector((0, 0, 0.06))

# Luz de plasma volumétrica na câmara central
luz_forja_data = bpy.data.lights.new('LuzForja', 'POINT')
luz_forja_data.color = (0.55, 0.25, 1.0)
luz_forja_data.energy = 80.0
luz_forja_data.shadow_soft_size = 0.2
luz_forja = bpy.data.objects.new('LuzForja', luz_forja_data)
sc.collection.objects.link(luz_forja)
luz_forja.location = Vector((0, 0, 0.65))

# ------------------------------------------------------------------ BRAÇOS ROBÓTICOS MANIPULADORES
# Braço alimentador SCARA pegando insumos da esteira sul para a bigorna
bm_braco_al = bmesh.new()
cil(bm_braco_al, (0, 0, 0), 0.06, 0.25, lados=12)
tubo(bm_braco_al, (0, 0, 0.20), (0.28, 0, 0.22), 0.035, 10)
cil(bm_braco_al, (0.28, 0, 0.22), 0.045, 0.12, lados=10)
tubo(bm_braco_al, (0.28, 0, 0.22), (0.52, 0, 0.16), 0.028, 8)
# Garra de pinça a vácuo na ponta
caixa_de(bm_braco_al, (0.48, -0.06, 0.06), (0.56, 0.06, 0.16))
braco_alimenta = obj('braco_alimenta', bm_braco_al, 'titânio')
braco_alimenta.location = Vector((-0.45, -0.55, Z_EST + 0.08))
suavizar(braco_alimenta)

# Braço ejetor quântico empurrando o produto pronto para a saída norte
bm_braco_ej = bmesh.new()
cil(bm_braco_ej, (0, 0, 0), 0.05, 0.22, lados=12)
tubo(bm_braco_ej, (0, 0, 0.18), (0.32, 0, 0.20), 0.032, 10)
cil(bm_braco_ej, (0.32, 0, 0.20), 0.04, 0.10, lados=10)
tubo(bm_braco_ej, (0.32, 0, 0.20), (0.58, 0, 0.14), 0.025, 8)
caixa_de(bm_braco_ej, (0.54, -0.05, 0.05), (0.62, 0.05, 0.14))
braco_ejetor = obj('braco_ejetor', bm_braco_ej, 'titânio')
braco_ejetor.location = Vector((0.45, 0.45, Z_EST + 0.08))
suavizar(braco_ejetor)

# ------------------------------------------------------------------ PEÇAS EM TRÂNSITO NA SAÍDA NORTE
# Processadores quânticos acabados: pastilhas com circuito de ouro e cristal central
pecas_forjadas = []
for p_idx in range(2):
    bm_p = bmesh.new()
    caixa_de(bm_p, (-0.09, -0.09, 0), (0.09, 0.09, 0.025))
    # Contatos de ouro perimetrais
    for cx in (-0.08, 0.08):
        caixa_de(bm_p, (cx - 0.015, -0.07, 0.025), (cx + 0.015, 0.07, 0.030))
    # Núcleo de cristal do chip quântico
    hexa(bm_p, (0, 0), 0.035, 0.025, 0.055)
    p_o = obj(f'peca_forjada_{p_idx}', bm_p, 'ouro')
    suavizar(p_o)
    pecas_forjadas.append(p_o)

# ------------------------------------------------------------------ RADIADORES CRIOGÊNICOS E MÓDULOS PERIFÉRICOS
# 2 Bancos de capacitores e trocadores térmicos a sudoeste e noroeste
bm_peri = bmesh.new()
for x_p, y_p in ((-0.95, -0.95), (-0.95, 0.95)):
    caixa_de(bm_peri, (x_p - 0.30, y_p - 0.30, Z_LAJE), (x_p + 0.30, y_p + 0.30, Z_LAJE + 0.65))
    # Aletas de refrigeração
    for dy in [-0.22 + k * 0.06 for k in range(8)]:
        caixa(bm_peri, (x_p - 0.32, y_p + dy, Z_LAJE + 0.35), (0.03, 0.015, 0.50))
    # Buchas de conexão e chicotes elétricos
    for db in (-0.15, 0.0, 0.15):
        cil(bm_peri, (x_p + 0.15, y_p + db, Z_LAJE + 0.68), 0.04, 0.08, lados=10)
        cano(bm_peri, bm_peri, [
            (x_p + 0.15, y_p + db, Z_LAJE + 0.72),
            (x_p + 0.35, y_p + db, Z_LAJE + 0.85),
            (-0.55, y_p * 0.6, 0.60)
        ], 0.018, flange=False)

obj('modulos_perifericos', bm_peri, 'aco')

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação contínua dos roletes das esteiras (4 voltas por ciclo)
    ang_rol = t * 8 * PI
    for r_o, u_lat in rolete_objs:
        q_rot = Quaternion(u_lat, ang_rol)
        r_o.rotation_euler = q_rot.to_euler()
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 2. Rotação do rotor do medidor de fluxo leste (4 voltas por ciclo)
    rotor_fluxo.rotation_euler = Euler((t * 8 * PI, 0, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Rotação do anel magnético de confinamento superior (1 volta = 360°)
    anel_confinamento.rotation_euler = Euler((0, 0, t * 2 * PI), 'XYZ')
    anel_confinamento.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Rotação do carrossel óptico superior (1 volta = 360°)
    carrossel_optico.rotation_euler = Euler((0, 0, -t * 2 * PI), 'XYZ')
    carrossel_optico.keyframe_insert('rotation_euler', frame=q)
    
    # 5. Ciclo do Martelo Quântico (prensa desce no quadro 24 a 48, estampa com impacto no 48, e sobe)
    # Ciclo de prensagem:
    # 0.0 a 0.20: repouso no topo (z = 1.15)
    # 0.20 a 0.45: descida acelerada até z = 0.62 (impacto)
    # 0.45 a 0.55: compressão quântica no fundo (z = 0.62)
    # 0.55 a 0.85: subida suave até z = 1.15
    # 0.85 a 1.00: repouso no topo
    if t < 0.20:
        z_mart = 1.15
    elif t < 0.45:
        s_desc = (t - 0.20) / 0.25
        z_mart = 1.15 - (1.15 - 0.62) * (s_desc ** 2)
    elif t < 0.55:
        z_mart = 0.62
    elif t < 0.85:
        s_sub = (t - 0.55) / 0.30
        z_mart = 0.62 + (1.15 - 0.62) * (math.sin(s_sub * PI / 2))
    else:
        z_mart = 1.15
        
    martelo_quantico.location = Vector((0, 0, z_mart))
    martelo_quantico.keyframe_insert('location', frame=q)
    
    # 6. Clarão pulsante de plasma na câmara central durante a prensagem
    if 0.44 <= t <= 0.56:
        s_flash = math.sin((t - 0.44) / 0.12 * PI)
        luz_forja_data.energy = 80.0 + 380.0 * s_flash
        luz_forja_data.color = (0.35 + 0.4 * s_flash, 0.45 + 0.5 * s_flash, 1.0)
    else:
        luz_forja_data.energy = 80.0 + 20.0 * math.sin(t * 4 * PI)
        luz_forja_data.color = (0.55, 0.25, 1.0)
    luz_forja_data.keyframe_insert('energy', frame=q)
    luz_forja_data.keyframe_insert('color', frame=q)
    
    # 7. Braço alimentador oscilando (pega matéria-prima sul e leva para a câmara)
    ang_al = math.radians(28.0 * math.sin(t * 2 * PI))
    braco_alimenta.rotation_euler = Euler((0, 0, ang_al), 'XYZ')
    braco_alimenta.keyframe_insert('rotation_euler', frame=q)
    
    # 8. Braço ejetor oscilando (conduz produto acabado para a saída norte)
    ang_ej = math.radians(-32.0 * math.sin(t * 2 * PI + PI / 3))
    braco_ejetor.rotation_euler = Euler((0, 0, ang_ej), 'XYZ')
    braco_ejetor.keyframe_insert('rotation_euler', frame=q)
    
    # 9. Peças em trânsito na esteira norte
    for p_i, p_o in enumerate(pecas_forjadas):
        fase_p = (t + p_i * 0.5) % 1.0
        y_peca = 0.85 + fase_p * 0.60
        p_o.location = Vector((0.0, y_peca, Z_EST + 0.025))
        p_o.keyframe_insert('location', frame=q)

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

ALVO = (0.0, 0.0, 0.90)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'FORJA_QUANTICA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((300, 4.2, 0.48), (215, 4.0, 0.48), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'forja_quantica_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na câmara de forjamento, martelo quântico, anel magnético e bigorna quântica
    sc.frame_set(int(0.48 * FPS) + 1)
    mirar((0.85, -1.15, 1.85), (0.0, -0.05, 0.80), 38)
    sc.render.filepath = os.path.join(AQUI, 'forja_quantica_perto.png')
    bpy.ops.render.render(write_still=True)

print('FORJA_QUANTICA ok')
