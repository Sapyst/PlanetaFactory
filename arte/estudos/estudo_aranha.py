"""Estudo isolado (fora do jogo): ARANHA MECÂNICA (Inimigo Principal).
O jogo monta a aranha por código com 6 pernas e IK procedural:
O estudo gera exatamente 3 objetos separados com nomes e origens estritas:
1. 'aranha_corpo': até 1.500 tris. Cerca de 1,0 × 1,96 × 0,6 m. Origem no chão sob o centro (z = 0).
   - Quadris nos 6 pontos exatos: (s*0.42, y, 0.55) para s em (-1, 1) e y em (0.35, 0.0, -0.35).
   - Cefalotórax e carapaça de blindagem angular, abdômen traseiro com dissipadores,
     cabeça com mandíbulas mecatrônicas afiadas e múltiplos sensores ópticos carmesim.
2. 'aranha_femur': até 200 tris. 0,70 m ao longo de +X, origem no quadril (0, 0, 0).
   - Articulação cilíndrica de quadril, viga estrutural blindada com atuador hidráulico e garfo de joelho em x = 0,70 m.
3. 'aranha_tibia': até 150 tris. 0,90 m ao longo de +X, origem no joelho (0, 0, 0), ponta em x = 0,90 m (garra/pé perfurante).
   - Articulação de joelho, haste afilada reforçada e agulha de tungstênio.

Paleta hostil predatória:
- Blindagem preta/grafite escuro com reflexo de titânio carbonizado (sem o amarelo industrial da fábrica).
- Sensores e óticas ópticas carmesim vivo.
- Metal maquinado escuro e pistões hidráulicos gastos.

Modos:
- '-- foto': monta prévia visual com as 6 pernas articuladas em pose de marcha para validação estética.
- '-- nada': mantém estritamente as 3 peças isoladas na origem para o conversor.

Uso: blender -b --python estudo_aranha.py -- foto
     blender -b --python estudo_aranha.py -- nada
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga

PI = math.pi
FPS = 24
QUADROS = 96

QUADRIL_Z = 0.55
FEMUR = 0.70
TIBIA = 0.90
QUADRIS = [(s * 0.42, y) for y in (0.35, 0.0, -0.35) for s in (1, -1)]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o

def luz_mat(nome, cor, forca=10.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

base3d.M.update({
    'blindagem_hostil': mats.material('BlindagemAranha', (0.10, 0.10, 0.12), 0.85, 0.35, pintura=False, sujeira=0.8, ferrugem=0.3, escovado=True),
    'chassi_escuro': mats.material('ChassiAranha', (0.06, 0.06, 0.07), 0.9, 0.45, pintura=False, sujeira=0.9),
    'metal_juntas': mats.material('MetalJuntasAranha', (0.35, 0.36, 0.38), 1.0, 0.30, pintura=False, ferrugem=0.5),
    'hidraulica_haste': mats.material('HasteHidraulica', (0.80, 0.82, 0.85), 1.0, 0.15, pintura=False),
    'olho_hostil': luz_mat('OlhosAranha', (1.0, 0.02, 0.05), 24.0),
    'chao': mats.material('ChaoHostil', (0.22, 0.21, 0.19), 0.0, 0.90, sujeira=0.5),
})

def aplicar_mat(bm, slot_idx, func, *args, **kwargs):
    f_ini = len(bm.faces)
    func(bm, *args, **kwargs)
    bm.faces.ensure_lookup_table()
    for i in range(f_ini, len(bm.faces)):
        bm.faces[i].material_index = slot_idx

# ================================================================== 1. ARANHA CORPO (origem em 0,0,0)
# Slots de materiais no corpo:
# 0: blindagem_hostil
# 1: chassi_escuro
# 2: metal_juntas
# 3: olho_hostil
bm_corpo = bmesh.new()

# Cefalotórax central
aplicar_mat(bm_corpo, 0, caixa_de, (-0.34, -0.28, 0.48), (0.34, 0.36, 0.68))
aplicar_mat(bm_corpo, 0, caixa_de, (-0.26, -0.25, 0.68), (0.26, 0.30, 0.73))
aplicar_mat(bm_corpo, 1, caixa_de, (-0.37, -0.26, 0.50), (0.37, 0.33, 0.63))

# Abdômen traseiro (opistossoma): bulbo blindado facetado alongado para trás (y de -0.28 a -0.96 m)
# Seção anterior do abdômen
aplicar_mat(bm_corpo, 0, cil, (0.0, -0.52, QUADRIL_Z + 0.06), 0.36, 0.40, lados=8, eixo=(0, 1, 0))
# Cúpula posterior afilada do abdômen
aplicar_mat(bm_corpo, 0, cil, (0.0, -0.78, QUADRIL_Z + 0.05), 0.28, 0.26, lados=8, eixo=(0, 1, 0))
aplicar_mat(bm_corpo, 1, cil, (0.0, -0.92, QUADRIL_Z + 0.04), 0.16, 0.10, lados=6, eixo=(0, 1, 0))

# Aletas de refrigeração dorsal no abdômen
for y_g in (-0.46, -0.60, -0.74):
    aplicar_mat(bm_corpo, 1, caixa, (0.0, y_g, QUADRIL_Z + 0.19), (0.24, 0.035, 0.025))

# Óticas / sensores secundários no abdômen (3 estrobos de alerta traseiros)
for k in range(3):
    aplicar_mat(bm_corpo, 3, cil, (0.0, -0.42 - 0.16 * k, QUADRIL_Z + 0.20), 0.032, 0.03, lados=6)

# Cabeça frontal (y de 0.36 a 0.86 m)
aplicar_mat(bm_corpo, 1, caixa_de, (-0.24, 0.36, 0.45), (0.24, 0.68, 0.63))
aplicar_mat(bm_corpo, 0, caixa_de, (-0.18, 0.68, 0.44), (0.18, 0.85, 0.59))

# Cluster de múltiplos olhos sensores frontais (carmesim vivo)
aplicar_mat(bm_corpo, 3, cil, (-0.08, 0.86, 0.53), 0.040, 0.025, lados=8, eixo=(0, 1, 0))
aplicar_mat(bm_corpo, 3, cil, (0.08, 0.86, 0.53), 0.040, 0.025, lados=8, eixo=(0, 1, 0))
aplicar_mat(bm_corpo, 3, cil, (-0.15, 0.80, 0.56), 0.028, 0.025, lados=6, eixo=(0, 1, 0))
aplicar_mat(bm_corpo, 3, cil, (0.15, 0.80, 0.56), 0.028, 0.025, lados=6, eixo=(0, 1, 0))
aplicar_mat(bm_corpo, 3, cil, (-0.15, 0.80, 0.48), 0.024, 0.025, lados=6, eixo=(0, 1, 0))
aplicar_mat(bm_corpo, 3, cil, (0.15, 0.80, 0.48), 0.024, 0.025, lados=6, eixo=(0, 1, 0))

# Quelíceras / mandíbulas mecatrônicas perfurantes frontais
for s in (-1, 1):
    x_m = s * 0.11
    aplicar_mat(bm_corpo, 1, caixa, (x_m, 0.74, 0.39), (0.06, 0.08, 0.08))
    aplicar_mat(bm_corpo, 2, viga, (x_m, 0.76, 0.39), (s * 0.08, 0.95, 0.24), 0.038)

# Mancais reforçados de quadril nas 6 posições exatas
for hx, hy in QUADRIS:
    aplicar_mat(bm_corpo, 2, cil, (hx, hy, QUADRIL_Z), 0.085, 0.14, lados=8)
    aplicar_mat(bm_corpo, 0, viga, (hx * 0.65, hy, QUADRIL_Z), (hx, hy, QUADRIL_Z), 0.06)

me_corpo = bpy.data.meshes.new('aranha_corpo_me')
bm_corpo.to_mesh(me_corpo)
o_corpo = bpy.data.objects.new('aranha_corpo', me_corpo)
sc.collection.objects.link(o_corpo)
o_corpo.data.materials.append(base3d.M['blindagem_hostil'])
o_corpo.data.materials.append(base3d.M['chassi_escuro'])
o_corpo.data.materials.append(base3d.M['metal_juntas'])
o_corpo.data.materials.append(base3d.M['olho_hostil'])
suavizar(o_corpo)

# ================================================================== 2. ARANHA FÊMUR (0.70 m ao longo de +X, origem 0,0,0)
# Slots no fêmur:
# 0: blindagem_hostil
# 1: hidraulica_haste
bm_femur = bmesh.new()

# Articulação de quadril no início (x = 0): mancal cilíndrico no eixo Y
aplicar_mat(bm_femur, 0, cil, (0.0, 0.0, 0.0), 0.075, 0.12, lados=8, eixo=(0, 1, 0))

# Braço blindado principal estendendo de x = 0.04 a x = 0.66 m
aplicar_mat(bm_femur, 0, viga, (0.04, 0.0, 0.0), (FEMUR - 0.05, 0.0, 0.0), 0.075)

# Placa de blindagem angular dorsal do fêmur
aplicar_mat(bm_femur, 0, caixa_de, (0.08, -0.045, 0.035), (FEMUR - 0.10, 0.045, 0.07))

# Cilindro hidráulico superior de acionamento do joelho
aplicar_mat(bm_femur, 0, tubo, (0.12, 0.0, 0.055), (0.42, 0.0, 0.055), 0.022, 8)
aplicar_mat(bm_femur, 1, tubo, (0.42, 0.0, 0.055), (FEMUR - 0.08, 0.0, 0.055), 0.014, 8)

# Articulação de joelho no final (x = 0.70 m)
aplicar_mat(bm_femur, 0, cil, (FEMUR, 0.0, 0.0), 0.065, 0.11, lados=8, eixo=(0, 1, 0))

me_femur = bpy.data.meshes.new('aranha_femur_me')
bm_femur.to_mesh(me_femur)
o_femur = bpy.data.objects.new('aranha_femur', me_femur)
sc.collection.objects.link(o_femur)
o_femur.data.materials.append(base3d.M['blindagem_hostil'])
o_femur.data.materials.append(base3d.M['hidraulica_haste'])
suavizar(o_femur)

# ================================================================== 3. ARANHA TÍBIA (0.90 m ao longo de +X, ponta = pé)
# Slots na tíbia:
# 0: blindagem_hostil
# 1: metal_juntas
# 2: olho_hostil
bm_tibia = bmesh.new()

# Articulação de joelho na origem (x = 0)
aplicar_mat(bm_tibia, 0, cil, (0.0, 0.0, 0.0), 0.062, 0.10, lados=8, eixo=(0, 1, 0))

# Haste afilada da tíbia (x = 0.03 a 0.68 m)
aplicar_mat(bm_tibia, 0, viga, (0.03, 0.0, 0.0), (TIBIA * 0.72, 0.0, 0.0), 0.068)

# Tendão/reforço hidráulico lateral
aplicar_mat(bm_tibia, 1, viga, (0.10, 0.0, 0.04), (0.58, 0.0, 0.03), 0.025)

# Sensor ótico lateral da perna
aplicar_mat(bm_tibia, 2, caixa, (0.35, 0.0, 0.045), (0.14, 0.04, 0.02))

# Garra/pé perfurante afilado em tungstênio (x = 0.68 a 0.90 m)
f_ini = len(bm_tibia.faces)
bmesh.ops.create_cone(bm_tibia, cap_ends=True, segments=6, radius1=0.045, radius2=0.005, depth=0.22,
                      matrix=Matrix.Translation((TIBIA - 0.11, 0.0, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, 'Y'))
bm_tibia.faces.ensure_lookup_table()
for i in range(f_ini, len(bm_tibia.faces)):
    bm_tibia.faces[i].material_index = 1

me_tibia = bpy.data.meshes.new('aranha_tibia_me')
bm_tibia.to_mesh(me_tibia)
o_tibia = bpy.data.objects.new('aranha_tibia', me_tibia)
sc.collection.objects.link(o_tibia)
o_tibia.data.materials.append(base3d.M['blindagem_hostil'])
o_tibia.data.materials.append(base3d.M['metal_juntas'])
o_tibia.data.materials.append(base3d.M['olho_hostil'])
suavizar(o_tibia)

# ------------------------------------------------------------------ TRATAMENTO DE MODOS
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris_c = len(o_corpo.data.polygons)
    tris_f = len(o_femur.data.polygons)
    tris_t = len(o_tibia.data.polygons)
    print(f'ARANHA_NADA_OK tris_corpo={tris_c} tris_femur={tris_f} tris_tibia={tris_t} total={tris_c + tris_f + tris_t}')
    sys.exit(0)

# ================================================================== MODO FOTO: MONTAGEM DA PRÉVIA COM IK ANALÍTICA
bm_preview = bmesh.new()

for leg_i, (hx, hy) in enumerate(QUADRIS):
    d = Vector((hx, hy, 0)).normalized()
    if leg_i in (0, 3, 4):
        pe = Vector((hx, hy, 0.02)) + d * 0.95
    else:
        pe = Vector((hx, hy, 0.15)) + d * 1.05 + Vector((0, 0.12, 0))
    
    q = Vector((hx, hy, QUADRIL_Z))
    alvo = pe - q
    dist = alvo.length
    
    cos_a = max(-1.0, min(1.0, (FEMUR**2 + dist**2 - TIBIA**2) / (2.0 * FEMUR * dist)))
    a = math.acos(cos_a)
    base_ang = math.atan2(alvo.z, Vector((alvo.x, alvo.y)).length)
    el = base_ang + a
    
    joelho = q + d * (FEMUR * math.cos(el)) + Vector((0, 0, FEMUR * math.sin(el)))
    
    viga(bm_preview, q, joelho, 0.075)
    cil(bm_preview, joelho, 0.065, 0.11, lados=8)
    viga(bm_preview, joelho, pe, 0.065)
    bmesh.ops.create_cone(bm_preview, cap_ends=True, segments=6, radius1=0.045, radius2=0.005, depth=0.18,
                          matrix=Matrix.Translation(pe + (joelho - pe).normalized() * 0.09) @
                                 (pe - joelho).to_track_quat('Z', 'Y').to_matrix().to_4x4())

o_pernas_preview = obj('EFEITO_pernas_preview', bm_preview, 'blindagem_hostil')
suavizar(o_pernas_preview)

# Esconder fêmur e tíbia soltos na origem durante o render da aranha montada
o_femur.hide_render = True
o_tibia.hide_render = True

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.05), (12, 12, 0.10))
obj('EFEITO_chao', bm_chao, 'chao')

# Sol principal
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-35))

# Sol de contra-luz para destacar silhueta das pernas
sol2 = bpy.data.lights.new('Sol2', 'SUN')
sol2.energy = 1.8
so2 = bpy.data.objects.new('Sol2', sol2)
sc.collection.objects.link(so2)
so2.rotation_euler = (math.radians(-38), 0, math.radians(145))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.45, 0.50, 0.60, 1)
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
sc.view_settings.exposure = -0.30

cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente

ALVO = (0.0, 0.0, 0.50)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    
    # 4 ângulos cardeais/isométricos mostrando a aranha predadora montada
    for i, (ang, alt) in enumerate(((315, 2.4), (225, 2.2), (135, 2.6), (45, 2.0))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 3.6, math.sin(a) * 3.6, alt - ALVO[2])), ALVO, 38)
        sc.render.filepath = os.path.join(AQUI, f'aranha_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up focado na cabeça ameaçadora, olhos carmesim e mandíbulas mecatrônicas
    mirar((0.70, 1.45, 0.85), (0.0, 0.70, 0.52), 48)
    sc.render.filepath = os.path.join(AQUI, 'aranha_perto.png')
    bpy.ops.render.render(write_still=True)

print('ARANHA ok')
