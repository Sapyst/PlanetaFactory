"""Estudo isolado (fora do jogo): IRRADIADOR DE MÓDULOS da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'irradiador_modulos'.
O último modelo de todo o projeto PlanetaFactory!
Transmissor de campo indutivo de área:
- Divide os efeitos de 2 módulos com todas as máquinas industriais em um raio de 3 tiles.
- Sem bocas de esteira de itens (irradiação de área eletromagnética e quântica).

Engenharia de irradiação pesada da IA autônoma:
- Laje de concreto e placas de aço corten 2,96 × 2,96 m com canaletas de cabos e sapatas pesadas.
- Torre Central Transmissora de Micro-Ondas e Campo Quântico (altura 2,65 m):
  * Pedestal octogonal maciço de titânio ancorado por 4 contrafortes diagonais de aço com flanges e parafusos.
  * Coluna central cilíndrica/octogonal com barramento vertical de 8 LEDs ciano indicadores de potência.
  * Bobinas toroidais duplas de cobre criogênico e anel de platina supercondutora.
  * Baia frontal para 2 módulos de alta densidade encaixados com aletas criogênicas e travas pneumáticas.
  * Carrossel superior giratório contínuo a 360° com 4 antenas parabólicas com sondas guias de onda.
  * Cristal de tempestade lapidado no topo emitindo harmônicos e pulso de ressonância piezoelétrica.
- 4 Subestações Radiadoras Criogênicas Periféricas (nos 4 cantos diagonais):
  * Carenagens de exaustão com ventiladores axiais de 5 pás girando a 6 voltas/ciclo.
  * Tubulações completas de líquido criogênico em circuito fechado com flanges e manômetros conectadas à torre.

Peças animadas separadas:
- 'carrossel_irradiador': anel superior de 4 antenas parabólicas girando a 360° em Z.
- 'cristal_transmissor': cristal de tempestade do topo pulsando harmonia e escala.
- 'ventoinha_crio_0'..'3': 4 ventiladores dos radiadores criogênicos girando a 6 voltas por ciclo.
- 'led_barra_0'..'7': barramento vertical de LEDs ciano na coluna da torre.
- 'luz_campo': iluminação volumétrica azulada/ciano pulsando no topo da torre.

Uso: blender -b --python estudo_irradiador_modulos.py -- foto
     blender -b --python estudo_irradiador_modulos.py -- nada
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
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'campo_irradiado': luz_mat('CampoIrradiado', (0.25, 0.85, 1.0), 24.0),
    'cristal_temp': luz_mat('CristalTempestade', (0.65, 0.20, 1.0), 20.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 16.0),
})

# ------------------------------------------------------------------ LAJE E BASE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base metálicas e anéis concêntricos de aterramento
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.38, -1.38, Z_LAJE), (1.38, 1.38, Z_LAJE + 0.02))
casca(bm_aco, (0, 0, 0), 1.28, 0.82, Z_LAJE + 0.02, Z_LAJE + 0.04, n=32)

# Canaletas metálicas de fiação / cabos no chão
for ang_c in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
    d_c = Vector((math.cos(ang_c), math.sin(ang_c), 0))
    p1 = d_c * 0.70 + Vector((0, 0, Z_LAJE + 0.025))
    p2 = d_c * 1.25 + Vector((0, 0, Z_LAJE + 0.025))
    viga(bm_aco, p1, p2, 0.05)

obj('placas_base_aco', bm_aco, 'aco')

# Listras de perigo industrial
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.26, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ TORRE TRANSMISSORA CENTRAL (2,65 m)
bm_torre = bmesh.new()
bm_ouro = bmesh.new()
bm_cobre = bmesh.new()
bm_flanges = bmesh.new()

# Pedestal e coluna central octogonal
casca(bm_torre, (0, 0, 0), 0.75, 0.52, Z_LAJE + 0.02, 0.48, n=8)
casca(bm_torre, (0, 0, 0), 0.54, 0.38, 0.48, 1.68, n=8)

# 4 Contrafortes diagonais estruturais de reforço com parafusos
for i_cf in range(4):
    ang_cf = i_cf * PI / 2 + PI / 4
    d_cf = Vector((math.cos(ang_cf), math.sin(ang_cf), 0))
    p_chao = d_cf * 0.92 + Vector((0, 0, Z_LAJE + 0.02))
    p_torre = d_cf * 0.54 + Vector((0, 0, 0.78))
    viga(bm_torre, p_chao, p_torre, 0.07)
    # Sapata de fixação no piso
    caixa(bm_torre, p_chao + Vector((0, 0, 0.02)), (0.09, 0.09, 0.04))
    hexa(bm_flanges, (p_chao[0], p_chao[1]), 0.015, Z_LAJE + 0.04, Z_LAJE + 0.065)

# Bobinas toroidais de Tesla em cobre criogênico e anel superior de ouro
toro(bm_cobre, (0, 0, 0.78), 0.58, 0.042, nR=24, nr=10)
toro(bm_cobre, (0, 0, 1.20), 0.58, 0.042, nR=24, nr=10)
toro(bm_ouro, (0, 0, 1.58), 0.50, 0.035, nR=24, nr=8)

# Cabeçote superior da torre (z = 1.68 a 2.12 m)
casca(bm_torre, (0, 0, 0), 0.60, 0.40, 1.68, 2.08, n=16)
cil(bm_torre, (0, 0, 2.08), 0.48, 0.06, lados=24)

# Buchas cerâmicas isolantes na coluna
for b_z in (0.95, 1.40):
    for a_iso in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
        p_iso = Vector((0.55 * math.cos(a_iso), 0.55 * math.sin(a_iso), b_z))
        cil(bm_torre, p_iso, 0.035, 0.06, lados=8)

obj('torre_corpo', bm_torre, 'titânio')
obj('torre_cobre', bm_cobre, 'cobre')
obj('torre_ouro', bm_ouro, 'ouro')
obj('torre_flanges', bm_flanges, 'cromo')

# ------------------------------------------------------------------ 2 CARTUCHOS DE MÓDULOS DE ALTA DENSIDADE
bm_mod = bmesh.new()
bm_leds = bmesh.new()
for m_i, y_m in enumerate((-0.24, 0.24)):
    p_slot = Vector((0.56, y_m, 0.42))
    # Caixa reforçada do módulo
    caixa_de(bm_mod, (p_slot[0] - 0.13, p_slot[1] - 0.15, p_slot[2]), (p_slot[0] + 0.13, p_slot[1] + 0.15, p_slot[2] + 0.48))
    # Aletas de refrigeração no módulo
    for dz in (0.08, 0.16, 0.24, 0.32, 0.40):
        caixa(bm_mod, (p_slot[0] + 0.14, p_slot[1], p_slot[2] + dz), (0.025, 0.26, 0.018))
    # Alça industrial pesada
    tubo(bm_mod, (p_slot[0] + 0.14, p_slot[1] - 0.08, p_slot[2] + 0.24), (p_slot[0] + 0.14, p_slot[1] + 0.08, p_slot[2] + 0.24), 0.012, 8)
    # LED ciano de atividade no módulo
    caixa(bm_leds, (p_slot[0] + 0.13, p_slot[1], p_slot[2] + 0.46), (0.02, 0.05, 0.02))

# 8 Barras de LED verticais na coluna frontal indicando potência irradiada
for k in range(8):
    z_led = 0.55 + k * 0.13
    caixa(bm_leds, (0.0, -0.55, z_led), (0.08, 0.018, 0.035))

obj('slots_modulos', bm_mod, 'titânio')
obj('leds_torre', bm_leds, 'led_ciano')

# ------------------------------------------------------------------ CARROSSEL IRRADIADOR SUPERIOR COM ANTENAS
# Anel giratório superior a z = 2.18 m com 4 antenas parabólicas
bm_carrossel = bmesh.new()
toro(bm_carrossel, (0, 0, 0), 0.65, 0.038, nR=32, nr=10)
for a_i in range(4):
    ang = a_i * PI / 2
    d_ant = Vector((math.cos(ang), math.sin(ang), 0))
    p_ant = d_ant * 0.65
    rot_ant = d_ant.to_track_quat('-Z', 'Y').to_matrix().to_3x3()
    # Haste da antena
    tubo(bm_carrossel, (0, 0, 0), p_ant, 0.025, 12)
    # Parabólica de emissão
    bmesh.ops.create_cone(bm_carrossel, cap_ends=False, segments=16, radius1=0.18, radius2=0.035, depth=0.12,
                          matrix=Matrix.Translation(p_ant + d_ant * 0.09) @ rot_ant.to_4x4())
    toro(bm_carrossel, p_ant + d_ant * 0.09, 0.18, 0.014, nR=16, nr=8, rot=rot_ant)
    # Guia de onda central e sonda no foco da parabólica
    tubo(bm_carrossel, p_ant, p_ant + d_ant * 0.18, 0.012, 8)
    curva(bm_carrossel, p_ant + d_ant * 0.18, 0.022, lados=10)

carrossel_irradiador = obj('carrossel_irradiador', bm_carrossel, 'ouro')
carrossel_irradiador.location = Vector((0.0, 0.0, 2.18))
suavizar(carrossel_irradiador)

# Cristal de Tempestade Central no topo (z = 2.48 m)
bm_cristal = bmesh.new()
hexa(bm_cristal, (0, 0), 0.09, -0.16, 0.16, ponta=0.09)
cristal_transmissor = obj('cristal_transmissor', bm_cristal, 'cristal_temp', pai=carrossel_irradiador)
cristal_transmissor.location = Vector((0.0, 0.0, 0.26))

# Luz de Campo Irradiado volumétrica no topo
luz_campo_data = bpy.data.lights.new('LuzCampo', 'POINT')
luz_campo_data.color = (0.25, 0.85, 1.0)
luz_campo_data.energy = 220.0
luz_campo_data.shadow_soft_size = 0.28
luz_campo = bpy.data.objects.new('LuzCampo', luz_campo_data)
sc.collection.objects.link(luz_campo)
luz_campo.location = Vector((0.0, 0.0, 2.48))

# ------------------------------------------------------------------ 4 RADIADORES CRIOGÊNICOS PERIFÉRICOS
bm_rad = bmesh.new()
bm_tubo_crio = bmesh.new()
bm_flange_crio = bmesh.new()
ventoinhas = []

pos_radiadores = [
    (-0.95, -0.95),
    (0.95, -0.95),
    (-0.95, 0.95),
    (0.95, 0.95)
]

for i, (rx, ry) in enumerate(pos_radiadores):
    p_rad = Vector((rx, ry, Z_LAJE))
    # Caixa do radiador
    caixa_de(bm_rad, (p_rad[0] - 0.24, p_rad[1] - 0.24, Z_LAJE), (p_rad[0] + 0.24, p_rad[1] + 0.24, Z_LAJE + 0.46))
    # Coifa circular da ventoinha
    casca(bm_rad, (p_rad[0], p_rad[1], 0), 0.20, 0.18, Z_LAJE + 0.08, Z_LAJE + 0.44, n=20)
    # Grelha de proteção
    for g_i in range(3):
        tubo(bm_rad, (p_rad[0] - 0.18 + g_i * 0.18, p_rad[1] - 0.18, Z_LAJE + 0.45),
                     (p_rad[0] - 0.18 + g_i * 0.18, p_rad[1] + 0.18, Z_LAJE + 0.45), 0.008, 6)
    
    # Tubulação de líquido criogênico ligando o radiador à base da torre
    u_dir = (Vector((0, 0, Z_LAJE + 0.20)) - p_rad).normalized()
    p_cano_ini = p_rad + Vector((0, 0, 0.20)) + u_dir * 0.24
    p_cano_fim = Vector((0.55 * rx / abs(rx), 0.55 * ry / abs(ry), Z_LAJE + 0.22))
    cano(bm_tubo_crio, bm_flange_crio, [p_cano_ini, p_cano_fim], 0.024, flange=True)
    
    # Manômetro de pressão no radiador
    p_mano = p_rad + Vector((0, 0, Z_LAJE + 0.42)) - u_dir * 0.22
    cil(bm_rad, p_mano, 0.045, 0.025, lados=14)
    hexa(bm_flange_crio, (p_mano[0], p_mano[1]), 0.015, p_mano[2] + 0.015, p_mano[2] + 0.028)
    
    # Ventoinha animada separadamente
    bm_v = bmesh.new()
    cil(bm_v, (0, 0, 0), 0.045, 0.045, lados=12)
    for p in range(5):
        a_p = p * 2 * PI / 5
        rot_p = Matrix.Rotation(a_p, 3, 'Z')
        bmesh.ops.create_cube(bm_v, size=1.0, matrix=Matrix.Translation((0.09 * math.cos(a_p), 0.09 * math.sin(a_p), 0)) @
                              rot_p.to_4x4() @ Matrix.Rotation(math.radians(25), 3, 'X').to_4x4() @
                              Matrix.Scale(0.08, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.012, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.038, 4, Vector((0, 0, 1))))
    v_o = obj(f'ventoinha_crio_{i}', bm_v, 'titânio')
    v_o.location = p_rad + Vector((0.0, 0.0, Z_LAJE + 0.26))
    suavizar(v_o)
    ventoinhas.append(v_o)

obj('radiadores_chassi', bm_rad, 'aco')
obj('tubos_criogenicos', bm_tubo_crio, 'cobre')
obj('flanges_criogenicas', bm_flange_crio, 'cromo')

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação contínua do carrossel irradiador superior (1 volta = 360°)
    carrossel_irradiador.rotation_euler = Euler((0, 0, t * 2 * PI), 'XYZ')
    carrossel_irradiador.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Pulso harmônico de escala e luminescência do cristal transmissor
    pulso_c = 1.0 + 0.09 * math.sin(t * 8 * PI)
    cristal_transmissor.scale = Vector((pulso_c, pulso_c, pulso_c))
    cristal_transmissor.keyframe_insert('scale', frame=q)
    
    # 3. Rotação das ventoinhas dos radiadores (6 voltas por ciclo)
    ang_vent = t * 12 * PI
    for v_o in ventoinhas:
        v_o.rotation_euler = Euler((0, 0, ang_vent), 'XYZ')
        v_o.keyframe_insert('rotation_euler', frame=q)
        
    # 4. Pulso de energia do campo irradiado
    luz_campo_data.energy = 220.0 + 80.0 * math.sin(t * 8 * PI)
    luz_campo_data.keyframe_insert('energy', frame=q)

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

ALVO = (0.0, 0.0, 1.15)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'IRRADIADOR_MODULOS_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'irradiador_modulos_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na torre transmissora, antenas parabólicas, cristal transmissor e baia de módulos
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((1.15, -1.35, 1.65), (0.05, -0.05, 1.15), 36)
    sc.render.filepath = os.path.join(AQUI, 'irradiador_modulos_perto.png')
    bpy.ops.render.render(write_still=True)

print('IRRADIADOR_MODULOS ok')
