"""Estudo isolado (fora do jogo): MONTADORA QUÂNTICA da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'montadora_4'.
A máquina de montagem mais avançada de todo o jogo:
- Velocidade 2,5 (2,5× a velocidade base).
- 4 Encaixes de Módulos Quânticos.
- DUAS RECEITAS SIMULTÂNEAS AO MESMO TEMPO:
  * Linha 1 (Sul -> Norte): esteira sul de entrada (ITEM_ENT_S1 a z = 0,23 m) -> esteira norte de saída (ITEM_SAI_N1 a z = 0,23 m).
  * Linha 2 (Oeste -> Leste): esteira oeste de entrada (ITEM_ENT_O1 a z = 0,23 m) -> esteira leste de saída (ITEM_SAI_L1 a z = 0,23 m).
  * As duas esteiras cruzam o centro da câmara sob uma matriz de entrelaçamento atômico sem colisão física.

Engenharia de síntese e teletransporte molecular da IA:
- Base de titânio escuro e ouro supercondutor 2,96 × 2,96 m com trilhos ortogonais e blindagem quântica.
- Câmara Central de Dupla Manufatura Quântica:
  * Duplo anel toroidal contra-rotativo de confinamento magnético em cobre criogênico e ouro (superior +360°, inferior -360°).
  * Cristal cúbico hiper-facetado central levitante pulsando em frequência de relógio quântico.
  * 4 Emissores laser de coerência molecular nos cantos da câmara projetando feixes cruzados de reconfiguração atômica.
  * Peças da Linha 1 avançando em direção norte; peças da Linha 2 avançando em direção leste simultaneamente.
- Baia de 4 Módulos Quânticos com cartuchos criogênicos e LEDs ciano ultrabrilhantes.
- Exaustão e resfriamento criogênico em circuito fechado.

Peças animadas separadas:
- 'anel_quantico_sup': anel toroidal superior girando a +360° em Z.
- 'anel_quantico_inf': anel toroidal inferior girando a -360° em Z.
- 'cristal_central': cubo quântico hiper-facetado levitando, girando e pulsando em escala.
- 'laser_foco_0'..'3': os 4 projetores de coerência oscilando sutilmente na focalização.
- 'peca_linha1_0'..'2': peças em trânsito na linha sul-norte.
- 'peca_linha2_0'..'2': peças em trânsito na linha oeste-leste.
- 'rolete_s0'..'s2', 'rolete_n0'..'n2', 'rolete_o0'..'o2', 'rolete_l0'..'l2': roletes de aço de todas as 4 bocas girando continuamente.
- 'luz_sintese': iluminação de plasma ciano-violeta pulsando no centro da câmara.

Uso: blender -b --python estudo_montadora_quantica.py -- foto
     blender -b --python estudo_montadora_quantica.py -- nada
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
Z_EST = 0.23                 # esteiras sul, norte, oeste, leste

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

base3d.M.update({
    'titânio': mats.material('TitânioEscuro', (0.12, 0.13, 0.15), 0.9, 0.35, pintura=False, sujeira=0.6, escovado=True),
    'aco': mats.material('AçoEstrutural', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('CobreCriogenico', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'ouro': mats.material('OuroSupercondutor', (0.95, 0.78, 0.22), 1.0, 0.18, pintura=False, sujeira=0.2),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'plasma_quantico': luz_mat('PlasmaQuantico', (0.2, 0.85, 1.0), 24.0),
    'cristal_res': luz_mat('CristalRessonancia', (0.85, 0.25, 1.0), 18.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 14.0),
    'laser': luz_mat('LaserCoerencia', (0.1, 1.0, 0.8), 28.0),
})

# ------------------------------------------------------------------ LAJE E BASE OCTOGONAL (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Plinto metálico com canaletas ortogonais cruzadas
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
# Cantoneiras e sapatas nos cantos chanfrados
for cx, cy in ((-1.25, -1.25), (1.25, -1.25), (-1.25, 1.25), (1.25, 1.25)):
    caixa_de(bm_aco, (cx - 0.14, cy - 0.14, Z_LAJE + 0.02), (cx + 0.14, cy + 0.14, Z_LAJE + 0.08))
    hexa(bm_aco, (cx, cy), 0.035, Z_LAJE + 0.08, Z_LAJE + 0.12)

obj('placas_base_aco', bm_aco, 'titânio')

# Listras de perigo industrial delimitando o perímetro de isolamento
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ DUAS LINHAS DE PRODUÇÃO ORTOGONAIS (4 BOCAS)
# Linha 1: Sul (entrada) -> Norte (saída)
# Linha 2: Oeste (entrada) -> Leste (saída)
BOCAS_CONFIG = [
    ('sul', Vector((0.0, -1.50, Z_EST)), Vector((0.0, 1.0, 0.0)), 0.60),
    ('norte', Vector((0.0, 1.50, Z_EST)), Vector((0.0, -1.0, 0.0)), 0.60),
    ('oeste', Vector((-1.50, 0.0, Z_EST)), Vector((1.0, 0.0, 0.0)), 0.60),
    ('leste', Vector((1.50, 0.0, Z_EST)), Vector((-1.0, 0.0, 0.0)), 0.60),
]

bm_est_chassi = bmesh.new()
rolete_objs = []

for nome_b, p_boca, dir_int, comp in BOCAS_CONFIG:
    u_lat = dir_int.cross(Z_VEC).normalized()
    p_fim = p_boca + dir_int * comp
    for sgn in (-1, 1):
        p1 = p_boca + u_lat * (sgn * 0.22)
        p2 = p_fim + u_lat * (sgn * 0.22)
        viga(bm_est_chassi, p1 + Vector((0, 0, -0.04)), p2 + Vector((0, 0, -0.04)), 0.035)
        viga(bm_est_chassi, p1 + Vector((0, 0, 0.03)), p2 + Vector((0, 0, 0.03)), 0.02)
    # Roletes giratórios da boca
    for r_i in range(3):
        s = 0.08 + r_i * 0.16
        p_rol = p_boca + dir_int * s
        bm_r = bmesh.new()
        cil(bm_r, (0, 0, 0), 0.032, 0.38, eixo=u_lat, lados=12)
        cil(bm_r, (0, 0, 0), 0.012, 0.44, eixo=u_lat, lados=8)
        r_o = obj(f'rolete_{nome_b}_{r_i}', bm_r, 'cromo')
        r_o.location = p_rol
        suavizar(r_o)
        rolete_objs.append((r_o, u_lat))

obj('chassi_esteiras_cruzadas', bm_est_chassi, 'titânio')

# Peças em trânsito simultâneo nas duas linhas
pecas_linha1 = []
pecas_linha2 = []

for i in range(3):
    # Linha 1: processador quântico (placa retangular com anel de ouro)
    bm_p1 = bmesh.new()
    caixa_de(bm_p1, (-0.08, -0.08, 0), (0.08, 0.08, 0.025))
    toro(bm_p1, (0, 0, 0.025), 0.045, 0.008, nR=12, nr=6)
    p1_o = obj(f'peca_linha1_{i}', bm_p1, 'ouro')
    suavizar(p1_o)
    pecas_linha1.append(p1_o)
    
    # Linha 2: cubo quântico de pacote (bloco prismático com cristal ciano)
    bm_p2 = bmesh.new()
    caixa_de(bm_p2, (-0.06, -0.06, 0), (0.06, 0.06, 0.08))
    hexa(bm_p2, (0, 0), 0.03, 0.08, 0.12)
    p2_o = obj(f'peca_linha2_{i}', bm_p2, 'cromo')
    suavizar(p2_o)
    pecas_linha2.append(p2_o)

# ------------------------------------------------------------------ CÂMARA CENTRAL DE DUPLA SÍNTESE QUÂNTICA
# Pedestal central de confinamento com bigorna levitante
bm_centro = bmesh.new()
bm_ouro = bmesh.new()
casca(bm_centro, (0, 0, 0), 0.75, 0.55, Z_LAJE + 0.02, 0.35, n=24)
# Matriz de bobinas toroidais no piso do centro
toro(bm_ouro, (0, 0, 0.36), 0.48, 0.028, nR=24, nr=8)
toro(bm_ouro, (0, 0, 0.44), 0.38, 0.024, nR=24, nr=8)

# 4 Pilares do pórtico quântico nos quadrantes diagonais (±0.85, ±0.85)
for dx, dy in ((-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
    viga(bm_centro, (dx, dy, Z_LAJE), (dx * 0.8, dy * 0.8, 1.85), 0.12)
    toro(bm_ouro, (dx * 0.8, dy * 0.8, 1.85), 0.10, 0.02, nR=16, nr=6)

obj('pedestal_centro', bm_centro, 'titânio')
obj('aneis_piso_ouro', bm_ouro, 'ouro')

# ------------------------------------------------------------------ DUPLO ANEL TOROIDAL CONTRA-ROTATIVO
# Anel Superior (gira a +360° em Z a z = 1.65 m)
bm_anel_sup = bmesh.new()
toro(bm_anel_sup, (0, 0, 0), 0.65, 0.038, nR=32, nr=10)
for k in range(8):
    ang_k = k * 2 * PI / 8
    pos_k = Vector((0.65 * math.cos(ang_k), 0.65 * math.sin(ang_k), 0))
    toro(bm_anel_sup, pos_k, 0.06, 0.015, nR=14, nr=6)
anel_quantico_sup = obj('anel_quantico_sup', bm_anel_sup, 'ouro')
anel_quantico_sup.location = Vector((0, 0, 1.65))
suavizar(anel_quantico_sup)

# Anel Inferior (contra-rotação a -360° em Z a z = 1.45 m)
bm_anel_inf = bmesh.new()
toro(bm_anel_inf, (0, 0, 0), 0.52, 0.032, nR=28, nr=10)
for k in range(6):
    ang_k = k * 2 * PI / 6
    pos_k = Vector((0.52 * math.cos(ang_k), 0.52 * math.sin(ang_k), 0))
    toro(bm_anel_inf, pos_k, 0.055, 0.014, nR=12, nr=6)
anel_quantico_inf = obj('anel_quantico_inf', bm_anel_inf, 'cobre')
anel_quantico_inf.location = Vector((0, 0, 1.45))
suavizar(anel_quantico_inf)

# Cristal Hiper-facetado Central Levitante (z = 0.95 m)
bm_cristal = bmesh.new()
# Cubo chanfrado e facetado de cristal quântico
bmesh.ops.create_cube(bm_cristal, size=0.22)
for k_c in range(6):
    a = k_c * 2 * PI / 6
    pos_sub = Vector((0.14 * math.cos(a), 0.14 * math.sin(a), 0.04 * math.sin(2 * a)))
    bmesh.ops.create_cone(bm_cristal, cap_ends=True, segments=6, radius1=0.04, radius2=0.0, depth=0.08,
                          matrix=Matrix.Translation(pos_sub))

cristal_central = obj('cristal_central', bm_cristal, 'cristal_res')
cristal_central.location = Vector((0, 0, 0.95))
suavizar(cristal_central)

# Luz Pontual de Síntese Quântica no centro
luz_sint_data = bpy.data.lights.new('LuzSintese', 'POINT')
luz_sint_data.color = (0.35, 0.85, 1.0)
luz_sint_data.energy = 220.0
luz_sint_data.shadow_soft_size = 0.20
luz_sint = bpy.data.objects.new('LuzSintese', luz_sint_data)
sc.collection.objects.link(luz_sint)
luz_sint.location = Vector((0, 0, 0.95))

# ------------------------------------------------------------------ 4 PROJETORES LASER DE COERÊNCIA MOLECULAR
lasers_foco = []
bm_torres_laser = bmesh.new()

for i, (dx, dy) in enumerate(((0.60, 0.60), (-0.60, 0.60), (-0.60, -0.60), (0.60, -0.60))):
    p_b = Vector((dx, dy, 0.35))
    p_t = Vector((dx * 0.70, dy * 0.70, 0.90))
    dir_c = (Vector((0, 0, 0.95)) - p_t).normalized()
    rot_c = dir_c.to_track_quat('-Z', 'Y').to_matrix().to_3x3()
    
    # Suporte da torre laser
    tubo(bm_torres_laser, p_b, p_t, 0.035, 10)
    toro(bm_torres_laser, p_t, 0.055, 0.015, nR=12, nr=6, rot=rot_c)
    
    # Cabeçote do laser animado separadamente
    bm_las = bmesh.new()
    cil(bm_las, (0, 0, 0), 0.025, 0.08, eixo=dir_c, lados=10)
    bmesh.ops.create_cone(bm_las, cap_ends=True, segments=6, radius1=0.018, radius2=0.005, depth=0.05,
                          matrix=Matrix.Translation(dir_c * 0.06) @ rot_c.to_4x4())
    las_o = obj(f'laser_foco_{i}', bm_las, 'cromo')
    las_o.location = p_t
    suavizar(las_o)
    lasers_foco.append((las_o, p_t, dir_c))

obj('torres_suporte_laser', bm_torres_laser, 'titânio')

# ------------------------------------------------------------------ 4 ENCAIXES DE MÓDULOS QUÂNTICOS
# Baia de 4 módulos quânticos a sudeste (x = 0.95 m, y = -0.95 m)
bm_mod = bmesh.new()
bm_leds = bmesh.new()
p_baia = Vector((0.95, -0.95, Z_LAJE))
caixa_de(bm_mod, (p_baia[0] - 0.28, p_baia[1] - 0.28, Z_LAJE), (p_baia[0] + 0.28, p_baia[1] + 0.28, Z_LAJE + 0.35))

for m_i, (mx, my) in enumerate(((-0.14, -0.14), (0.14, -0.14), (-0.14, 0.14), (0.14, 0.14))):
    pos_m = p_baia + Vector((mx, my, 0.35))
    caixa_de(bm_mod, (pos_m[0] - 0.08, pos_m[1] - 0.08, pos_m[2]), (pos_m[0] + 0.08, pos_m[1] + 0.08, pos_m[2] + 0.22))
    toro(bm_mod, (pos_m[0], pos_m[1], pos_m[2] + 0.18), 0.07, 0.012, nR=12, nr=6)
    # LED ciano de atividade
    caixa(bm_leds, (pos_m[0], pos_m[1], pos_m[2] + 0.23), (0.02, 0.02, 0.02))

obj('baia_modulos_quantica', bm_mod, 'titânio')
obj('leds_modulos_quantica', bm_leds, 'led_ciano')

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação dos roletes das 4 esteiras
    ang_rol = t * 8 * PI
    for r_o, u_lat in rolete_objs:
        q_rot = Quaternion(u_lat, ang_rol)
        r_o.rotation_euler = q_rot.to_euler()
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 2. Contra-rotação dos anéis toroidais superiores
    anel_quantico_sup.rotation_euler = Euler((0, 0, t * 2 * PI), 'XYZ')
    anel_quantico_inf.rotation_euler = Euler((0, 0, -t * 2 * PI), 'XYZ')
    anel_quantico_sup.keyframe_insert('rotation_euler', frame=q)
    anel_quantico_inf.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Levitação, rotação e pulso harmônico do cristal central
    dz_cristal = 0.03 * math.sin(t * 4 * PI)
    cristal_central.location = Vector((0, 0, 0.95 + dz_cristal))
    cristal_central.rotation_euler = Euler((t * 2 * PI, t * 2 * PI, t * 4 * PI), 'XYZ')
    pulso_c = 1.0 + 0.06 * math.sin(t * 8 * PI)
    cristal_central.scale = Vector((pulso_c, pulso_c, pulso_c))
    cristal_central.keyframe_insert('location', frame=q)
    cristal_central.keyframe_insert('rotation_euler', frame=q)
    cristal_central.keyframe_insert('scale', frame=q)
    
    # 4. Trânsito simultâneo nas duas linhas de produção (velocidade 2,5)
    # Linha 1: Sul -> Norte (y avança de -1.40 a +1.40 m)
    for p_i, p_o in enumerate(pecas_linha1):
        fase_p1 = (t + p_i / 3.0) % 1.0
        y_p1 = -1.40 + fase_p1 * 2.80
        p_o.location = Vector((0.0, y_p1, Z_EST + 0.025))
        p_o.keyframe_insert('location', frame=q)
        
    # Linha 2: Oeste -> Leste (x avança de -1.40 a +1.40 m)
    for p_i, p_o in enumerate(pecas_linha2):
        fase_p2 = (t + p_i / 3.0) % 1.0
        x_p2 = -1.40 + fase_p2 * 2.80
        p_o.location = Vector((x_p2, 0.0, Z_EST + 0.025))
        p_o.keyframe_insert('location', frame=q)
        
    # 5. Oscilação dos lasers de foco
    for l_i, (las_o, p_orig, dir_orig) in enumerate(lasers_foco):
        ang_las = math.radians(6.0 * math.sin(t * 8 * PI + l_i * PI / 2))
        las_o.rotation_euler = Euler((ang_las, 0, ang_las), 'XYZ')
        las_o.keyframe_insert('rotation_euler', frame=q)
        
    # 6. Pulso de energia quântica central
    luz_sint_data.energy = 220.0 + 80.0 * math.sin(t * 8 * PI)
    luz_sint_data.keyframe_insert('energy', frame=q)

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
    print(f'MONTADORA_QUANTICA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'montadora_quantica_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up no cristal central, anéis contra-rotativos e interseção das duas receitas
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((1.15, -1.35, 1.45), (0.05, -0.05, 0.85), 36)
    sc.render.filepath = os.path.join(AQUI, 'montadora_quantica_perto.png')
    bpy.ops.render.render(write_still=True)

print('MONTADORA_QUANTICA ok')
