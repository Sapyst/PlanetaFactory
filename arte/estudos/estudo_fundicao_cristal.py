"""Estudo isolado (fora do jogo): FUNDIÇÃO DE CRISTAL da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'fundicao_cristal'.
Velocidade 4,0, 4 encaixes de módulos. Transforma minério de ferro e cristais diretamente em lingotes de aço puro
sem necessidade de etapas intermediárias de queima.

Bocas no padrão do jogo:
- ITEM_ENT_S1: esteira sul de minério de ferro bruto (x = 0,0, y = -1,50 m, z = 0,23 m)
- ITEM_ENT_O1: esteira oeste de cristais de tempestade/fluxo (x = -1,50 m, y = 0,0, z = 0,23 m)
- ITEM_SAI_N1: esteira norte de lingotes de aço prontos (x = 0,0, y = +1,50 m, z = 0,23 m)
- FLUIDO_ENT_L1: tubulação leste de água/refrigerante para resfriamento a z = 0,35 m (x = +1,50 m, y = 0,0)

Engenharia metalúrgica e ressonância de cristal da IA:
- Base de concreto armado 2,96 × 2,96 m com bacia de contenção refratária, trilhos e chapas de aço xadrez.
- Crisol / Cadinho de Indução Central (z = 0.30 a 1.35 m):
  * Vaso refratário circular maciço com carcaça em aço corten e 4 cintas de aperto em ferro fundido.
  * Bobinas toroidais de alta indução em cobre criogênico envolvendo a carcaça.
  * Banho de metal líquido superaquecido turbilhonando sob campos eletromagnéticos.
  * 4 Garras mecatrônicas articuladas sustentando cristais de tempestade lapidados apontando para o banho.
- Bica de Vazamento e Corrente de Lingotamento Contínuo:
  * Bica basculante refratária alimentando lingoteiras móveis na direção norte.
  * Bicos aspersores de água (spray cooling) resfriando rapidamente os lingotes com vapor subindo.
  * Lingotes mudando de incandescente para aço escuro à medida que avançam para a esteira norte.
- 4 Encaixes de Módulos (slots traseiros com conectores industriais e LEDs ciano).
- Sistema de Exaustão de Gases e Ciclone:
  * Coifa cônica superior suspensa captando gases metalúrgicos.
  * Tubo pesado flangeado direcionando fumos para o ciclone traseiro com chaminé.

Peças animadas separadas:
- 'cristal_foco_0'..'3': os 4 cristais de tempestade oscilando harmonicamente e pulsando luminescência.
- 'turbilhao_metal': banho de metal líquido girando continuamente no interior do cadinho.
- 'lingote_0'..'4': lingotes incandescentes avançando continuamente na corrente norte e esfriando.
- 'rotor_fluxo': rotor do fluxômetro de refrigeração leste girando a 4 voltas por ciclo.
- 'rolete_s0'..'s3', 'rolete_o0'..'o3': roletes de aço das esteiras sul e oeste girando continuamente.
- 'EFEITO_vapor_0', '1': colunas de vapor de resfriamento subindo das lingoteiras.
- 'luz_banho': iluminação incandescente alaranjada pulsando no topo do cadinho.

Uso: blender -b --python estudo_fundicao_cristal.py -- foto
     blender -b --python estudo_fundicao_cristal.py -- nada
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
Z_CADINHO = 0.75             # centro do cadinho refratário

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

def metal_liquido_mat():
    m = bpy.data.materials.new('MetalLiquido')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1.0, 0.45, 0.08, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.40, 0.06, 1)
    b.inputs['Emission Strength'].default_value = 18.0
    b.inputs['Roughness'].default_value = 0.22
    b.inputs['Metallic'].default_value = 0.95
    return m

base3d.M.update({
    'titânio': mats.material('TitânioEscuro', (0.12, 0.13, 0.15), 0.9, 0.35, pintura=False, sujeira=0.6, escovado=True),
    'aco': mats.material('AçoEstrutural', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('CobreCriogenico', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'ouro': mats.material('OuroSupercondutor', (0.95, 0.78, 0.22), 1.0, 0.18, pintura=False, sujeira=0.2),
    'refratario': mats.material('TijoloRefratario', (0.35, 0.28, 0.22), 0.0, 0.85, sujeira=0.8, desgaste=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'metal_liquido': metal_liquido_mat(),
    'cristal_temp': luz_mat('CristalTempestade', (0.6, 0.2, 1.0), 16.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 12.0),
    'faisca': luz_mat('FaiscaIncandescente', (1.0, 0.8, 0.3), 20.0),
    'vapor': base3d.volume_mat('VaporResfriamento', (0.85, 0.90, 0.95), 0.4, 0.2, 1.4),
})

# ------------------------------------------------------------------ LAJE E BASE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base metálicas, sapatas e trilhos
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
# Bacia refratária de retenção de escória sob o cadinho
casca(bm_aco, (0, 0, 0), 0.98, 0.82, Z_LAJE + 0.02, Z_LAJE + 0.12, n=24)
obj('placas_base_aco', bm_aco, 'aco')

# Listras de perigo industrial delimitando o perímetro de calor extremo
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ BOCAS E ESTEIRAS (SUL, OESTE, NORTE)
# Boca SUL: minério de ferro bruto
# Boca OESTE: cristais de fluxo
# Boca NORTE: lingotes acabados
ESTEIRAS_CONFIG = [
    ('sul', Vector((0.0, -1.50, Z_EST)), Vector((0.0, 1.0, 0.0)), 0.65),
    ('oeste', Vector((-1.50, 0.0, Z_EST)), Vector((1.0, 0.0, 0.0)), 0.65),
    ('norte', Vector((0.0, 1.50, Z_EST)), Vector((0.0, -1.0, 0.0)), 0.70)
]

bm_est_guias = bmesh.new()
rolete_objs = []

for nome_e, p_boca, dir_int, comp in ESTEIRAS_CONFIG:
    u_lat = dir_int.cross(Z_VEC).normalized()
    p_fim = p_boca + dir_int * comp
    for sgn in (-1, 1):
        p1 = p_boca + u_lat * (sgn * 0.22)
        p2 = p_fim + u_lat * (sgn * 0.22)
        viga(bm_est_guias, p1 + Vector((0, 0, -0.04)), p2 + Vector((0, 0, -0.04)), 0.04)
        viga(bm_est_guias, p1 + Vector((0, 0, 0.04)), p2 + Vector((0, 0, 0.04)), 0.025)
    for s in (0.15, 0.45):
        p_sup = p_boca + dir_int * s
        for sgn in (-1, 1):
            tubo(bm_est_guias, p_sup + u_lat * (sgn * 0.22) + Vector((0, 0, -0.04)),
                 Vector((p_sup[0] + u_lat[0] * sgn * 0.22, p_sup[1] + u_lat[1] * sgn * 0.22, Z_LAJE)), 0.025, 8)
    for r_i in range(4):
        s = 0.08 + r_i * 0.16
        p_rol = p_boca + dir_int * s
        bm_r = bmesh.new()
        cil(bm_r, (0, 0, 0), 0.035, 0.40, eixo=u_lat, lados=12)
        cil(bm_r, (0, 0, 0), 0.012, 0.46, eixo=u_lat, lados=8)
        r_o = obj(f'rolete_{nome_e}_{r_i}', bm_r, 'cromo')
        r_o.location = p_rol
        suavizar(r_o)
        rolete_objs.append((r_o, u_lat))

obj('esteiras_guias', bm_est_guias, 'titânio')

# ------------------------------------------------------------------ BOCA LESTE DE FLUIDO REFRIGERANTE (ÁGUA)
p_fluido = Vector((1.50, 0.0, Z_CANO))
bm_tubo_fluido = bmesh.new()
bm_flange_fluido = bmesh.new()

tubo(bm_flange_fluido, p_fluido, p_fluido - Vector((0.08, 0, 0)), 0.085, 16)
tubo(bm_tubo_fluido, p_fluido - Vector((0.08, 0, 0)), p_fluido - Vector((0.35, 0, 0)), 0.055, 16)
p_medidor = p_fluido - Vector((0.48, 0, 0))
caixa_de(bm_flange_fluido, (p_medidor[0] - 0.09, -0.09, Z_CANO - 0.09), (p_medidor[0] + 0.09, 0.09, Z_CANO + 0.09))
cano(bm_tubo_fluido, bm_flange_fluido, [
    (p_medidor[0] - 0.09, 0.0, Z_CANO),
    (p_medidor[0] - 0.25, 0.0, Z_CANO),
    (p_medidor[0] - 0.25, 0.45, Z_CANO),
    (0.35, 0.45, 0.50),
    (0.35, 0.65, 0.38)
], 0.045, flange=True)

obj('tubo_fluido_leste', bm_tubo_fluido, 'cobre')
obj('flange_fluido_leste', bm_flange_fluido, 'titânio')

# Rotor do medidor de fluxo leste
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

# ------------------------------------------------------------------ CRISOL / CADINHO DE INDUÇÃO CENTRAL
bm_cadinho = bmesh.new()
bm_bobinas = bmesh.new()
bm_ref = bmesh.new()

# Carcaça circular externa do cadinho (z = 0.12 a 1.05 m)
casca(bm_cadinho, (0, 0, 0), 0.78, 0.68, Z_LAJE + 0.04, 1.05, n=24)
# Revestimento refratário interno de carbeto de silício
casca(bm_ref, (0, 0, 0), 0.68, 0.54, Z_LAJE + 0.08, 1.02, n=24)
cil(bm_ref, (0, 0, Z_LAJE + 0.08), 0.54, 0.04, lados=24)

# Cintas de aperto de ferro fundido com parafusos tensores
for z_cinta in (0.30, 0.55, 0.80, 0.98):
    toro(bm_cadinho, (0, 0, z_cinta), 0.785, 0.022, nR=24, nr=8)
    for a_p in (0, PI/2, PI, 3*PI/2):
        pos_p = Vector((0.80 * math.cos(a_p), 0.80 * math.sin(a_p), z_cinta))
        caixa(bm_cadinho, pos_p, (0.04, 0.04, 0.04))

# Bobinas toroidais de cobre de indução de alta frequência envolvendo o cadinho
for z_bob in (0.40, 0.65, 0.90):
    toro(bm_bobinas, (0, 0, z_bob), 0.84, 0.038, nR=24, nr=10)

# Bica refratária de vazamento norte inclinada para as lingoteiras
caixa_de(bm_cadinho, (-0.16, 0.65, 0.75), (0.16, 0.95, 0.90))
caixa_de(bm_ref, (-0.10, 0.68, 0.80), (0.10, 0.95, 0.88))

obj('cadinho_carcaca', bm_cadinho, 'aco')
obj('cadinho_refratario', bm_ref, 'refratario')
obj('cadinho_bobinas', bm_bobinas, 'cobre')

# Banho de Metal Líquido turbilhonando no interior do cadinho (animado separadamente)
bm_metal = bmesh.new()
# Disco circular de metal incandescente
cil(bm_metal, (0, 0, 0), 0.53, 0.02, lados=24)
# Pequenas ondas de vórtice
for r_ond in (0.18, 0.35):
    toro(bm_metal, (0, 0, 0.01), r_ond, 0.012, nR=20, nr=6)

turbilhao_metal = obj('turbilhao_metal', bm_metal, 'metal_liquido')
turbilhao_metal.location = Vector((0, 0, 0.72))
suavizar(turbilhao_metal)

# Luz Incandescente volumétrica do metal líquido
luz_banho_data = bpy.data.lights.new('LuzBanho', 'POINT')
luz_banho_data.color = (1.0, 0.45, 0.08)
luz_banho_data.energy = 160.0
luz_banho_data.shadow_soft_size = 0.25
luz_banho = bpy.data.objects.new('LuzBanho', luz_banho_data)
sc.collection.objects.link(luz_banho)
luz_banho.location = Vector((0, 0, 0.95))

# ------------------------------------------------------------------ 4 CRISTAIS DE FOCO PIEZOELÉTRICO
# Montados nos 4 quadrantes diagonais: (±0.65, ±0.65)
bm_garras = bmesh.new()
cristais_foco = []

for i, (dx, dy) in enumerate(((0.65, 0.65), (-0.65, 0.65), (-0.65, -0.65), (0.65, -0.65))):
    p_base_garra = Vector((dx, dy, Z_LAJE + 0.02))
    p_topo_garra = Vector((dx * 0.75, dy * 0.75, 1.25))
    dir_centro = (Vector((0, 0, 0.75)) - p_topo_garra).normalized()
    rot_c = dir_centro.to_track_quat('-Z', 'Y').to_matrix().to_3x3()
    
    # Coluna e haste articulada da garra
    viga(bm_garras, p_base_garra, p_topo_garra, 0.07)
    toro(bm_garras, p_topo_garra, 0.08, 0.02, nR=14, nr=6, rot=rot_c)
    # Cabos condutores de alta tensão
    tubo(bm_garras, p_topo_garra, p_topo_garra + Vector((0, 0, 0.12)), 0.02, 8)
    
    # Cristal lapidado animado separadamente
    bm_c = bmesh.new()
    hexa(bm_c, (0, 0), 0.055, -0.15, 0.10, ponta=0.08)
    c_o = obj(f'cristal_foco_{i}', bm_c, 'cristal_temp')
    c_o.location = p_topo_garra + dir_centro * 0.12
    c_o.rotation_euler = dir_centro.to_track_quat('Z', 'Y').to_euler()
    cristais_foco.append((c_o, p_topo_garra + dir_centro * 0.12))

obj('garras_cristais', bm_garras, 'titânio')

# ------------------------------------------------------------------ TREM DE LINGOTAMENTO CONTÍNUO E RESFRIAMENTO
# Corrente de lingoteiras articuladas avançando na direção norte (y = 0.95 a 1.50 m)
bm_moldeira = bmesh.new()
caixa_de(bm_moldeira, (-0.24, 0.90, Z_EST - 0.05), (0.24, 1.48, Z_EST + 0.02))
# Bicos aspersores de água (spray cooling) sobre a corrente
for y_sp in (1.05, 1.25):
    tubo(bm_moldeira, (-0.30, y_sp, 0.42), (0.30, y_sp, 0.42), 0.018, 8)
    for x_sp in (-0.12, 0.12):
        bmesh.ops.create_cone(bm_moldeira, cap_ends=True, segments=8, radius1=0.015, radius2=0.03, depth=0.04,
                              matrix=Matrix.Translation((x_sp, y_sp, 0.38)))

obj('calha_lingotamento', bm_moldeira, 'aco')

# 5 Lingotes de aço em trânsito com materiais térmicos progressivos
lingotes_objs = []
for l_idx in range(5):
    bm_ling = bmesh.new()
    # Barra chanfrada trapezoidal de lingote de aço
    caixa_de(bm_ling, (-0.08, -0.04, 0), (0.08, 0.04, 0.035))
    mat_l = 'metal_liquido' if l_idx < 2 else 'aco'
    l_o = obj(f'lingote_{l_idx}', bm_ling, mat_l)
    lingotes_objs.append(l_o)

# ------------------------------------------------------------------ 4 ENCAIXES DE MÓDULOS (TRASEIRA SUL/SUDESTE)
bm_mod = bmesh.new()
bm_leds = bmesh.new()
for m_i, x_m in enumerate((-0.75, -0.45, 0.45, 0.75)):
    p_slot = Vector((x_m, -1.25, Z_LAJE + 0.16))
    caixa_de(bm_mod, (x_m - 0.11, -1.35, Z_LAJE), (x_m + 0.11, -1.15, Z_LAJE + 0.32))
    # Dente/fresta do encaixe do módulo
    caixa_de(bm_mod, (x_m - 0.08, -1.36, Z_LAJE + 0.08), (x_m + 0.08, -1.18, Z_LAJE + 0.28))
    # LED indicador ciano de módulo conectado
    caixa(bm_leds, (x_m, -1.36, Z_LAJE + 0.30), (0.02, 0.01, 0.02))

obj('slots_modulos', bm_mod, 'titânio')
obj('leds_modulos', bm_leds, 'led_ciano')

# ------------------------------------------------------------------ COIFA DE EXAUSTÃO E CICLONE DE GASES
bm_coifa = bmesh.new()
bm_duto = bmesh.new()

# Coifa cônica superior suspensa sobre o cadinho (z = 1.30 a 1.70 m)
bmesh.ops.create_cone(bm_coifa, cap_ends=False, segments=20, radius1=0.72, radius2=0.22, depth=0.40,
                      matrix=Matrix.Translation((0, 0, 1.50)))
toro(bm_coifa, (0, 0, 1.30), 0.72, 0.025, nR=20, nr=6)

# Duto de exaustão curvo indo para o ciclone a noroeste (-0.95, 0.95)
cano(bm_duto, bm_coifa, [
    (0.0, 0.0, 1.70),
    (0.0, 0.0, 1.95),
    (-0.55, 0.55, 1.95),
    (-0.95, 0.95, 1.65)
], 0.10, flange=True)

# Filtro ciclônico cilíndrico-cônico a noroeste (-0.95, 0.95)
p_cic = Vector((-0.95, 0.95, 0))
cil(bm_coifa, p_cic + Vector((0, 0, 1.25)), 0.28, 0.65, lados=16)
bmesh.ops.create_cone(bm_coifa, cap_ends=True, segments=16, radius1=0.28, radius2=0.08, depth=0.45,
                      matrix=Matrix.Translation(p_cic + Vector((0, 0, 0.70))))
# Chaminé de exaustão vertical do ciclone
cil(bm_duto, p_cic + Vector((0, 0, 1.75)), 0.12, 0.55, lados=14)

obj('coifa_exaustao', bm_coifa, 'aco')
obj('dutos_exaustao', bm_duto, 'titânio')

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação contínua dos roletes das esteiras
    ang_rol = t * 8 * PI
    for r_o, u_lat in rolete_objs:
        q_rot = Quaternion(u_lat, ang_rol)
        r_o.rotation_euler = q_rot.to_euler()
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 2. Rotação do rotor do medidor de fluxo leste (4 voltas por ciclo)
    rotor_fluxo.rotation_euler = Euler((t * 8 * PI, 0, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Turbilhonamento do banho de metal líquido (2 voltas por ciclo)
    turbilhao_metal.rotation_euler = Euler((0, 0, t * 4 * PI), 'XYZ')
    turbilhao_metal.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Oscilação harmônica e pulso piezoelétrico dos 4 cristais de tempestade
    for i, (c_o, p_orig) in enumerate(cristais_foco):
        defasagem = i * PI / 2
        pulso_c = 1.0 + 0.08 * math.sin(t * 8 * PI + defasagem)
        c_o.scale = Vector((pulso_c, pulso_c, pulso_c))
        # Micro-vibração de ressonância
        dz = 0.010 * math.sin(t * 16 * PI + defasagem)
        c_o.location = p_orig + Vector((0, 0, dz))
        c_o.keyframe_insert('scale', frame=q)
        c_o.keyframe_insert('location', frame=q)
        
    # 5. Avanço contínuo dos lingotes de aço na esteira norte (ciclo fechado)
    for l_i, l_o in enumerate(lingotes_objs):
        fase_l = (t + l_i / 5.0) % 1.0
        y_ling = 0.92 + fase_l * 0.56
        l_o.location = Vector((0.0, y_ling, Z_EST + 0.022))
        l_o.keyframe_insert('location', frame=q)
        
    # 6. Pulso térmico da luz do cadinho
    luz_banho_data.energy = 160.0 + 40.0 * math.sin(t * 8 * PI)
    luz_banho_data.keyframe_insert('energy', frame=q)

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
    print(f'FUNDICAO_CRISTAL_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'fundicao_cristal_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up no cadinho de metal líquido incandescente, cristais de foco e bica de lingotamento
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((1.05, -1.35, 1.55), (0.05, -0.05, 0.85), 36)
    sc.render.filepath = os.path.join(AQUI, 'fundicao_cristal_perto.png')
    bpy.ops.render.render(write_still=True)

print('FUNDICAO_CRISTAL ok')
