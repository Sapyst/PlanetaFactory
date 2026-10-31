"""Estudo isolado (fora do jogo): POÇA DE SEIVA (1×1 tile), até 300 tris.
Fluido viscoso do planeta onde a bomba é instalada por cima:
- Tamanho cerca de 0,82×0,83 m e no máximo 0,085 m de altura (a bomba senta nela).
- Seiva escura e viscosa com brilho molhado intenso (sem transparência, material com roughness muito baixo).
- Borda de crosta mineral seca e terra manchada com pedregulhos incrustados.
- 2 bolhas de seiva animadas que inflam e estouram em laço fechado de 96 quadros (4 s).

Uso: blender -b --python estudo_poca_seiva.py -- foto
     blender -b --python estudo_poca_seiva.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, cil, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(42)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o

base3d.M.update({
    'seiva_viscosa': mats.material('SeivaViscosa', (0.10, 0.065, 0.015), 0.05, 0.05, pintura=False, sujeira=0.1),
    'crosta_seca': mats.material('CrostaSeca', (0.18, 0.15, 0.12), 0.0, 0.85, pintura=False, sujeira=0.9, ferrugem=0.4),
    'pedra_seiva': mats.material('PedraManchada', (0.22, 0.20, 0.18), 0.05, 0.70, pintura=False, sujeira=0.95),
    'chao': mats.material('ChaoPlaneta', (0.25, 0.24, 0.21), 0.0, 0.90, sujeira=0.4),
})

# ------------------------------------------------------------------ 1. CROSTA MINERAL E BORDA DE TERRA
bm_crosta = bmesh.new()
bm_seiva = bmesh.new()
bm_pedras = bmesh.new()

N_LADOS = 12
raios_crosta = [0.41 + 0.02 * math.sin(i * 2.3) for i in range(N_LADOS)]
raios_seiva = [r * 0.76 for r in raios_crosta]

# Anel de crosta externa (z = 0 a 0.035 m)
v_chao_ext = []
v_topo_ext = []
v_topo_int = []
v_fundo_int = []

for i in range(N_LADOS):
    ang = 2 * PI * i / N_LADOS
    dx, dy = math.cos(ang), math.sin(ang)
    r_ext = raios_crosta[i]
    r_int = raios_seiva[i]
    
    v_chao_ext.append(bm_crosta.verts.new(Vector((dx * r_ext, dy * r_ext, -0.004))))
    v_topo_ext.append(bm_crosta.verts.new(Vector((dx * (r_ext - 0.04), dy * (r_ext - 0.04), 0.028))))
    v_topo_int.append(bm_crosta.verts.new(Vector((dx * r_int, dy * r_int, 0.025))))
    v_fundo_int.append(bm_crosta.verts.new(Vector((dx * r_int, dy * r_int, 0.005))))

for i in range(N_LADOS):
    nxt = (i + 1) % N_LADOS
    # Borda em rampa externa
    bm_crosta.faces.new((v_chao_ext[i], v_chao_ext[nxt], v_topo_ext[nxt], v_topo_ext[i]))
    # Topo da crosta
    bm_crosta.faces.new((v_topo_ext[i], v_topo_ext[nxt], v_topo_int[nxt], v_topo_int[i]))
    # Borda interna descendo para a seiva
    bm_crosta.faces.new((v_topo_int[i], v_topo_int[nxt], v_fundo_int[nxt], v_fundo_int[i]))

# Fundo inferior da crosta
bm_crosta.faces.new(list(reversed(v_chao_ext)))

# ------------------------------------------------------------------ 2. ESPELHO DA SEIVA VISCOSA
# Superfície da seiva (z = 0.022 m)
v_seiva = []
v_centro = bm_seiva.verts.new(Vector((0.0, 0.0, 0.024)))
for i in range(N_LADOS):
    ang = 2 * PI * i / N_LADOS
    dx, dy = math.cos(ang), math.sin(ang)
    r_s = raios_seiva[i] + 0.008
    v_seiva.append(bm_seiva.verts.new(Vector((dx * r_s, dy * r_s, 0.022))))

for i in range(N_LADOS):
    nxt = (i + 1) % N_LADOS
    bm_seiva.faces.new((v_centro, v_seiva[i], v_seiva[nxt]))

# ------------------------------------------------------------------ 3. PEDRAS INCRUSTADAS NA BORDA
pos_pedras = [
    (0.38, 0.08, 0.04, 0.045),
    (-0.25, 0.32, 0.04, 0.05),
    (-0.35, -0.15, 0.035, 0.04),
    (0.15, -0.36, 0.035, 0.045)
]

for px, py, pz, pr in pos_pedras:
    pedra(bm_pedras, (px, py, pz), pr, achatar=0.6)

o_crosta = obj('poca_crosta', bm_crosta, 'crosta_seca')
o_seiva = obj('poca_superficie', bm_seiva, 'seiva_viscosa')
o_pedras = obj('poca_pedras', bm_pedras, 'pedra_seiva')

suavizar(o_crosta)
suavizar(o_seiva, tudo=True)
suavizar(o_pedras)

# ------------------------------------------------------------------ 4. BOLHAS DE SEIVA ANIMADAS (OBJETOS SEPARADOS)
bolhas = []
pos_bolhas = [
    (0.14, 0.09, 0.022, 0.045),
    (-0.12, -0.10, 0.022, 0.038)
]

for b_idx, (bx, by, bz, br) in enumerate(pos_bolhas):
    bm_b = bmesh.new()
    bmesh.ops.create_uvsphere(bm_b, u_segments=10, v_segments=6, radius=br)
    # Deixar apenas a meia-esfera superior
    for v in list(bm_b.verts):
        if v.co.z < 0:
            v.co.z = 0
    o_b = obj(f'bolha_seiva_{b_idx}', bm_b, 'seiva_viscosa')
    o_b.location = Vector((bx, by, bz))
    suavizar(o_b, tudo=True)
    bolhas.append((o_b, br))

# ------------------------------------------------------------------ ANIMAÇÃO DAS BOLHAS (96 QUADROS)
# Bolha 0: incha entre quadros 1 e 42, estoura no quadro 45, reaparece no 55
o_b0, r0 = bolhas[0]
for q in range(1, QUADROS + 1):
    if q < 44:
        # Inflamento não-linear
        t = q / 43.0
        s_xy = 0.25 + 0.95 * (t ** 1.8)
        s_z = 0.20 + 1.15 * (t ** 2.2)
        o_b0.scale = Vector((s_xy, s_xy, s_z))
        o_b0.hide_render = False
        o_b0.hide_viewport = False
    elif q < 52:
        # Estouro (colapso da bolha)
        o_b0.scale = Vector((0.08, 0.08, 0.05))
        o_b0.hide_render = True
        o_b0.hide_viewport = True
    else:
        # Renascimento e crescimento lento
        t = (q - 52) / (QUADROS - 52 + 1.0)
        s_xy = 0.08 + 0.35 * t
        s_z = 0.05 + 0.30 * t
        o_b0.scale = Vector((s_xy, s_xy, s_z))
        o_b0.hide_render = False
        o_b0.hide_viewport = False
    o_b0.keyframe_insert('scale', frame=q)
    o_b0.keyframe_insert('hide_render', frame=q)
    o_b0.keyframe_insert('hide_viewport', frame=q)

# Bolha 1: defasada, incha até o quadro 84 e estoura
o_b1, r1 = bolhas[1]
for q in range(1, QUADROS + 1):
    if q < 38:
        # Fase inicial de repouso / crescimento micro
        t = q / 38.0
        s_xy = 0.15 + 0.35 * t
        s_z = 0.12 + 0.30 * t
        o_b1.scale = Vector((s_xy, s_xy, s_z))
        o_b1.hide_render = False
        o_b1.hide_viewport = False
    elif q < 82:
        # Inchaço vigoroso
        t = (q - 38) / (82.0 - 38.0)
        s_xy = 0.50 + 0.85 * (t ** 1.6)
        s_z = 0.42 + 1.05 * (t ** 2.0)
        o_b1.scale = Vector((s_xy, s_xy, s_z))
        o_b1.hide_render = False
        o_b1.hide_viewport = False
    elif q < 90:
        # Estouro
        o_b1.scale = Vector((0.08, 0.08, 0.05))
        o_b1.hide_render = True
        o_b1.hide_viewport = True
    else:
        # Preparação do próximo ciclo
        t = (q - 90) / 7.0
        s_xy = 0.08 + 0.07 * t
        s_z = 0.05 + 0.07 * t
        o_b1.scale = Vector((s_xy, s_xy, s_z))
        o_b1.hide_render = False
        o_b1.hide_viewport = False
    o_b1.keyframe_insert('scale', frame=q)
    o_b1.keyframe_insert('hide_render', frame=q)
    o_b1.keyframe_insert('hide_viewport', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.05), (10, 10, 0.10))
obj('EFEITO_chao', bm, 'chao')

# Sol
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
sol.angle = math.radians(2.0)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-32))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.52, 0.58, 0.68, 1)
bg.inputs['Strength'].default_value = 0.70

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

ALVO = (0.0, 0.0, 0.03)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO'))
    print(f'POCA_SEIVA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    
    # 4 ângulos cardeais/isométricos capturando a poça e o relevo da crosta
    for i, (ang, alt, f_num) in enumerate(((315, 1.4, 35), (225, 1.3, 75), (135, 1.5, 20), (45, 1.2, 50))):
        sc.frame_set(f_num)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 1.8, math.sin(a) * 1.8, alt - ALVO[2])), ALVO, 42)
        sc.render.filepath = os.path.join(AQUI, f'poca_seiva_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up focado na superfície viscosa, menisco e bolha de seiva
    sc.frame_set(38)
    mirar((0.45, -0.35, 0.32), (0.12, 0.06, 0.03), 55)
    sc.render.filepath = os.path.join(AQUI, 'poca_seiva_perto.png')
    bpy.ops.render.render(write_still=True)

print('POCA_SEIVA ok')
