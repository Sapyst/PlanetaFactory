"""Estudo isolado (fora do jogo): EXTRATOR RESSONANTE da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'extrator_2'.
Mineração piezoelétrica e acústica de alta frequência para jazidas de cristais:
- 2× mais rápido na extração de cristais de tempestade que as brocas convencionais.
- Boca no padrão do jogo:
  * ITEM_SAI_S1: esteira sul de saída de cristais fraturados a z = 0,23 m (x = 0,0, y = -1,50 m).
  * FLUIDO_ENT_O1: tubulação oeste de fluido de refrigeração/acoplamento acústico a z = 0,35 m (x = -1,50 m, y = 0,0).

Engenharia de ressonância harmônica da IA:
- Base de concreto armado e placas de aço corten 2,96 × 2,96 m com canaletas e sapatas de ancoragem antivibratórias.
- Torre de Fraturação Acústica e Sonotrodo Central:
  * Pórtico pesado em treliça de aço com 4 amortecedores hidráulicos espessos absorvendo as ondas de choque.
  * Sonotrodo vertical maciço em titânio e latão com anéis de indução piezoelétrica pulsando em alta frequência.
  * Cristal ressonador de tempestade gigante lapidado no centro emitindo ondas de coerência sísmica para o subsolo.
  * Anel superior de sintonia harmônica girando continuamente a 360° em Z.
- Sistema de Recepção e Classificação de Fragmentos:
  * Calha vibratória rebaixada coletando lascas de cristal fraturadas por ressonância.
  * Esteira sul com roletes giratórios conduzindo fragmentos de cristal lapidados para fora da máquina.
- Unidade de Refrigeração e Acoplamento Oeste:
  * Bocal flangeado a 0,35 m de altura com medidor de vazão rotativo e mangueiras trançadas alimentando os transdutores.

Peças animadas separadas:
- 'sonotrodo_central': cabeçote ressonador de titânio oscilando verticalmente em alta frequência com pulso acústico.
- 'anel_sintonia': anel superior de sintonia harmônica girando continuamente a 360° em Z.
- 'cristal_ressonador': cristal central pulsando escala e luminescência harmônica.
- 'calha_vibratoria': calha inferior com micro-vibração de transporte de sólidos.
- 'rolete_s0'..'s3': roletes de aço da esteira sul girando continuamente.
- 'cristal_transito_0'..'2': fragmentos de cristal avançando na esteira sul.
- 'rotor_fluxo': rotor do medidor de vazão oeste girando a 4 voltas por ciclo.
- 'luz_choque': clarão estroboscópico de onda de choque piezoelétrica na base da fraturação.

Uso: blender -b --python estudo_extrator_ressonante.py -- foto
     blender -b --python estudo_extrator_ressonante.py -- nada
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
Z_EST = 0.23                 # esteira sul de saída
Z_CANO = 0.35                # tubo de fluido oeste

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
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'ouro': mats.material('OuroSupercondutor', (0.95, 0.78, 0.22), 1.0, 0.18, pintura=False, sujeira=0.2),
    'amarelo_mineracao': mats.material('AmareloMineracao', (0.78, 0.52, 0.08), 0.1, 0.45, desgaste=1.3, sujeira=0.9, ferrugem=0.45),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'cristal_temp': luz_mat('CristalTempestade', (0.6, 0.2, 1.0), 20.0),
    'onda_choque': luz_mat('OndaChoque', (0.3, 0.85, 1.0), 25.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 12.0),
})

# ------------------------------------------------------------------ LAJE E BASE ANTIVIBRATÓRIA (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base em aço corten com sapatas de amortecimento hidráulico nos 4 cantos
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
for cx, cy in ((-1.25, -1.25), (1.25, -1.25), (-1.25, 1.25), (1.25, 1.25)):
    caixa_de(bm_aco, (cx - 0.14, cy - 0.14, Z_LAJE + 0.02), (cx + 0.14, cy + 0.14, Z_LAJE + 0.08))
    # Parafusos tensores e pistões de nivelamento
    cil(bm_aco, (cx, cy, Z_LAJE + 0.08), 0.045, 0.08, lados=12)
    hexa(bm_aco, (cx, cy), 0.03, Z_LAJE + 0.16, Z_LAJE + 0.20)

# Poço central de fraturação sísmica (abertura circular no solo)
casca(bm_aco, (0, 0, 0), 0.72, 0.52, Z_LAJE + 0.02, Z_LAJE + 0.10, n=24)
obj('base_aco_amortecida', bm_aco, 'aco')

# Listras de perigo industrial delimitando o perímetro de choque mecânico
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ BOCA SUL DE SAÍDA DE CRISTAIS (ITEM_SAI_S1)
p_boca_s = Vector((0.0, -1.50, Z_EST))
bm_est_s = bmesh.new()
# Guias laterais da esteira sul
for sgn in (-1, 1):
    p1 = p_boca_s + Vector((sgn * 0.22, 0, 0))
    p2 = p_boca_s + Vector((sgn * 0.22, 0.85, 0))
    viga(bm_est_s, p1 + Vector((0, 0, -0.04)), p2 + Vector((0, 0, -0.04)), 0.035)
    viga(bm_est_s, p1 + Vector((0, 0, 0.03)), p2 + Vector((0, 0, 0.03)), 0.02)

obj('esteira_sul_guias', bm_est_s, 'titânio')

# 4 Roletes giratórios da esteira sul
rolete_objs = []
for r_i in range(4):
    y_r = -1.50 + 0.08 + r_i * 0.16
    bm_r = bmesh.new()
    cil(bm_r, (0, 0, 0), 0.032, 0.38, eixo=Vector((1, 0, 0)), lados=12)
    cil(bm_r, (0, 0, 0), 0.012, 0.44, eixo=Vector((1, 0, 0)), lados=8)
    r_o = obj(f'rolete_s_{r_i}', bm_r, 'cromo')
    r_o.location = Vector((0.0, y_r, Z_EST - 0.01))
    suavizar(r_o)
    rolete_objs.append(r_o)

# Fragmentos de cristal em trânsito na esteira sul
cristais_transito = []
for c_idx in range(3):
    bm_c = bmesh.new()
    hexa(bm_c, (0, 0), 0.045, 0, 0.07, ponta=0.04)
    c_o = obj(f'cristal_transito_{c_idx}', bm_c, 'cristal_temp')
    suavizar(c_o)
    cristais_transito.append(c_o)

# ------------------------------------------------------------------ BOCA OESTE DE FLUIDO (FLUIDO_ENT_O1)
p_fluido = Vector((-1.50, 0.0, Z_CANO))
bm_tubo_fluido = bmesh.new()
bm_flange_fluido = bmesh.new()

tubo(bm_flange_fluido, p_fluido, p_fluido + Vector((0.08, 0, 0)), 0.085, 16)
tubo(bm_tubo_fluido, p_fluido + Vector((0.08, 0, 0)), p_fluido + Vector((0.35, 0, 0)), 0.055, 16)
p_medidor = p_fluido + Vector((0.48, 0, 0))
caixa_de(bm_flange_fluido, (p_medidor[0] - 0.09, -0.09, Z_CANO - 0.09), (p_medidor[0] + 0.09, 0.09, Z_CANO + 0.09))
cano(bm_tubo_fluido, bm_flange_fluido, [
    (p_medidor[0] + 0.09, 0.0, Z_CANO),
    (p_medidor[0] + 0.25, 0.0, Z_CANO),
    (p_medidor[0] + 0.25, 0.35, Z_CANO),
    (-0.45, 0.35, 0.70)
], 0.045, flange=True)

obj('tubo_fluido_oeste', bm_tubo_fluido, 'cobre')
obj('flange_fluido_oeste', bm_flange_fluido, 'titânio')

# Rotor do medidor de fluxo oeste
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

# ------------------------------------------------------------------ PÓRTICO PESADO DE MINERAÇÃO (AMARELO)
bm_portico = bmesh.new()
# 4 Pilares inclinados piramidais de suporte ao sonotrodo
for px, py in ((-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
    viga(bm_portico, (px, py, Z_LAJE + 0.06), (px * 0.55, py * 0.55, 1.95), 0.14)
    # Cilindros hidráulicos telescópicos de absorção de choque
    tubo(bm_portico, (px, py, 0.35), (px * 0.65, py * 0.65, 1.45), 0.06, 12)

# Viga anelar superior do pórtico (teto)
casca(bm_portico, (0, 0, 0), 0.65, 0.45, 1.90, 2.05, n=24)
obj('portico_extrator', bm_portico, 'amarelo_mineracao')

# ------------------------------------------------------------------ SONOTRODO VERTICAL E RESSONADOR DE CRISTAL
# Cabeçote do sonotrodo animado verticalmente
bm_sono = bmesh.new()
# Eixo central telescópico cromado
cil(bm_sono, (0, 0, 0.45), 0.12, 0.85, lados=16)
# Massa de impacto / anel de indução acústica em latão
toro(bm_sono, (0, 0, 0.25), 0.26, 0.05, nR=24, nr=10)
toro(bm_sono, (0, 0, 0.45), 0.22, 0.04, nR=24, nr=8)
# Ponta cônica de fraturação ultrassônica apontando para o poço
bmesh.ops.create_cone(bm_sono, cap_ends=True, segments=12, radius1=0.18, radius2=0.03, depth=0.35,
                      matrix=Matrix.Translation((0, 0, -0.15)) @ Matrix.Rotation(PI, 3, 'X').to_4x4())

sonotrodo_central = obj('sonotrodo_central', bm_sono, 'titânio')
sonotrodo_central.location = Vector((0.0, 0.0, 0.85))
suavizar(sonotrodo_central)

# Cristal de Ressonância Central Lapidado de Tempestade
bm_c_res = bmesh.new()
hexa(bm_c_res, (0, 0), 0.09, -0.22, 0.15, ponta=0.10)
cristal_ressonador = obj('cristal_ressonador', bm_c_res, 'cristal_temp', pai=sonotrodo_central)
cristal_ressonador.location = Vector((0.0, 0.0, 0.05))

# Anel Superior de Sintonia Harmônica no topo do pórtico (z = 2.15 m)
bm_anel = bmesh.new()
toro(bm_anel, (0, 0, 0), 0.52, 0.035, nR=28, nr=10)
for k in range(8):
    ang_k = k * 2 * PI / 8
    pos_k = Vector((0.52 * math.cos(ang_k), 0.52 * math.sin(ang_k), 0))
    toro(bm_anel, pos_k, 0.055, 0.012, nR=12, nr=6)

anel_sintonia = obj('anel_sintonia', bm_anel, 'ouro')
anel_sintonia.location = Vector((0.0, 0.0, 2.15))
suavizar(anel_sintonia)

# Calha vibratória inferior rebaixada sob o sonotrodo conduzindo para a esteira sul
bm_calha = bmesh.new()
caixa_de(bm_calha, (-0.28, -0.65, Z_LAJE + 0.02), (0.28, 0.15, Z_EST + 0.02))
calha_vibratoria = obj('calha_vibratoria', bm_calha, 'aco')
suavizar(calha_vibratoria)

# Luz Estroboscópica de Onda de Choque Piezoelétrica
luz_choque_data = bpy.data.lights.new('LuzChoque', 'POINT')
luz_choque_data.color = (0.35, 0.85, 1.0)
luz_choque_data.energy = 180.0
luz_choque_data.shadow_soft_size = 0.20
luz_choque = bpy.data.objects.new('LuzChoque', luz_choque_data)
sc.collection.objects.link(luz_choque)
luz_choque.location = Vector((0.0, 0.0, 0.25))

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação dos roletes da esteira sul
    ang_rol = t * 8 * PI
    for r_o in rolete_objs:
        r_o.rotation_euler = Euler((ang_rol, 0, 0), 'XYZ')
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 2. Rotação do fluxômetro de fluido oeste
    rotor_fluxo.rotation_euler = Euler((t * 8 * PI, 0, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Rotação do anel de sintonia harmônica superior (1 volta = 360°)
    anel_sintonia.rotation_euler = Euler((0, 0, t * 2 * PI), 'XYZ')
    anel_sintonia.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Vibração vertical de alta frequência do sonotrodo de titânio (8 pulsos sísmicos por ciclo)
    dz_sono = 0.045 * math.sin(t * 16 * PI)
    sonotrodo_central.location = Vector((0.0, 0.0, 0.85 + dz_sono))
    sonotrodo_central.keyframe_insert('location', frame=q)
    
    # 5. Pulso harmônico de luminescência e escala do cristal ressonador
    pulso_c = 1.0 + 0.08 * math.cos(t * 16 * PI)
    cristal_ressonador.scale = Vector((pulso_c, pulso_c, pulso_c))
    cristal_ressonador.keyframe_insert('scale', frame=q)
    
    # 6. Micro-vibração da calha vibratória
    dz_calha = 0.005 * math.sin(t * 32 * PI)
    calha_vibratoria.location = Vector((0.0, 0.0, dz_calha))
    calha_vibratoria.keyframe_insert('location', frame=q)
    
    # 7. Avanço contínuo dos cristais na esteira sul
    for c_i, c_o in enumerate(cristais_transito):
        fase_c = (t + c_i / 3.0) % 1.0
        y_c = -0.65 - fase_c * 0.80
        c_o.location = Vector((0.0, y_c, Z_EST + 0.025))
        c_o.keyframe_insert('location', frame=q)
        
    # 8. Clarão estroboscópico de onda de choque piezoelétrica
    int_choque = 180.0 + 120.0 * math.sin(t * 16 * PI)
    luz_choque_data.energy = max(20.0, int_choque)
    luz_choque_data.keyframe_insert('energy', frame=q)

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

ALVO = (0.0, 0.0, 0.95)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'EXTRATOR_RESSONANTE_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'extrator_ressonante_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up no sonotrodo, cristal ressonador, poço sísmico e calha vibratória
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((1.15, -1.35, 1.35), (0.05, -0.10, 0.70), 38)
    sc.render.filepath = os.path.join(AQUI, 'extrator_ressonante_perto.png')
    bpy.ops.render.render(write_still=True)

print('EXTRATOR_RESSONANTE ok')
