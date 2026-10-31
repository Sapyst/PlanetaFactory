"""Estudo isolado (fora do jogo): PLATAFORMA SOBRE A ÁGUA (1×1 tile), até 600 tris.
Apoio logístico sobre rios, lagos e depressões aquáticas.
O jogo coloca uma sob CADA tile construído sobre a água:
- Ocupa 1,00×1,00 m exatos no topo e emenda sem frestas com as vizinhas em qualquer direção.
- Altura total de 1,9 m: origem nos pés no leito (z = 0) e topo do deque em z = 1,90 m.
- Estática, sem animação de máquina.
- Detalhes de textura e silhueta: marcas d'água, cracas/oxidação pesada na parte submersa dos pilares,
  sapatas de ancoragem no leito, contraventamento estrutural, anéis de telemetria e chapa de piso gasta.

Uso: blender -b --python estudo_plataforma_agua.py -- foto
     blender -b --python estudo_plataforma_agua.py -- nada
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga

PI = math.pi
FPS = 24
QUADROS = 96

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o

def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

base3d.M.update({
    'deck_gasto': mats.material('DeckAcoGasto', (0.28, 0.30, 0.32), 0.95, 0.45, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True),
    'aco_estrutural': mats.material('AcoEstrutural', (0.35, 0.36, 0.37), 1.0, 0.40, pintura=False, ferrugem=0.75, sujeira=0.8),
    'pilar_submerso': mats.material('PilarSubmerso', (0.16, 0.18, 0.17), 0.4, 0.80, pintura=False, ferrugem=0.95, sujeira=1.0),
    'sapata_leito': mats.material('SapataLeito', (0.22, 0.23, 0.22), 0.1, 0.95, pintura=False, ferrugem=0.6, sujeira=1.0),
    'anel_telemetria': luz_mat('LuzTelemetriaAgua', (0.15, 0.85, 0.95), 10.0),
    'chao': mats.material('LeitoRio', (0.14, 0.15, 0.13), 0, 0.95, sujeira=0.8),
    'agua': mats.material('AguaSuperficie', (0.05, 0.15, 0.18), 0.1, 0.1, pintura=False),
})

# ------------------------------------------------------------------ 1. PILARES E SAPATAS (z = 0 a 1.76 m)
bm_pilares = bmesh.new()
bm_sapatas = bmesh.new()
bm_aneis = bmesh.new()
bm_estrut = bmesh.new()

pos_pilares = [(-0.38, -0.38), (0.38, -0.38), (-0.38, 0.38), (0.38, 0.38)]

for px, py in pos_pilares:
    # Sapata reforçada de assentamento no leito
    cil(bm_sapatas, (px, py, 0.08), 0.11, 0.16, lados=8)
    
    # Tubo maciço do pilar (z = 0.08 a 1.76 m)
    cil(bm_pilares, (px, py, 0.92), 0.075, 1.68, lados=8)
    
    # Colar de maré / incrustação subaquática (z = 0.30 a 0.55 m)
    cil(bm_sapatas, (px, py, 0.42), 0.088, 0.20, lados=8)
    
    # Anel luminescente de cota d'água / telemetria a z = 1.60 m
    cil(bm_aneis, (px, py, 1.60), 0.085, 0.04, lados=8)

# Vigas de travamento horizontal (contraventamento)
# Eixo X em z = 1.15 m
viga(bm_estrut, (-0.38, -0.38, 1.15), (0.38, -0.38, 1.15), 0.06)
viga(bm_estrut, (-0.38, 0.38, 1.15), (0.38, 0.38, 1.15), 0.06)

# Eixo Y em z = 0.95 m
viga(bm_estrut, (-0.38, -0.38, 0.95), (-0.38, 0.38, 0.95), 0.06)
viga(bm_estrut, (0.38, -0.38, 0.95), (0.38, 0.38, 0.95), 0.06)

# Mísulas/consolos estruturais sob o deque (z = 1.65 a 1.76 m)
for px, py in pos_pilares:
    caixa(bm_estrut, (px, py, 1.71), (0.17, 0.17, 0.09))

# ------------------------------------------------------------------ 2. DEQUE BLINDADO (1.00 × 1.00 m exatos, z = 1.76 a 1.90 m)
bm_deque = bmesh.new()

# Chapa do deque ocupando exatamente [-0.50, 0.50] em X e Y para emenda perfeita sem frestas
caixa_de(bm_deque, (-0.50, -0.50, 1.76), (0.50, 0.50, 1.90))

# Vigas perimetrais inferiores de reforço de borda
caixa_de(bm_estrut, (-0.46, -0.46, 1.72), (0.46, 0.46, 1.76))

# Objetos da cena
o_sapatas = obj('plataforma_sapatas', bm_sapatas, 'sapata_leito')
o_pilares = obj('plataforma_pilares', bm_pilares, 'pilar_submerso')
o_estrut = obj('plataforma_estruturas', bm_estrut, 'aco_estrutural')
o_aneis = obj('plataforma_aneis', bm_aneis, 'anel_telemetria')
o_deque = obj('plataforma_deque', bm_deque, 'deck_gasto')

suavizar(o_pilares)
suavizar(o_sapatas)
suavizar(o_aneis)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.05), (10, 10, 0.10))
obj('EFEITO_chao', bm, 'chao')

# Sol
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.0)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), 0, math.radians(-38))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.50, 0.58, 0.70, 1)
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
    # O conversor lê os objetos reais da plataforma (ignora EFEITO_*)
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO'))
    print(f'PLATAFORMA_AGUA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    
    # 4 ângulos cardeais/isométricos mostrando a altura inteira de 1,9 m
    for i, (ang, alt) in enumerate(((315, 2.5), (225, 2.3), (135, 2.6), (45, 2.2))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 3.4, math.sin(a) * 3.4, alt - ALVO[2])), ALVO, 38)
        sc.render.filepath = os.path.join(AQUI, f'plataforma_agua_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up focado no pilar frontal, sapatas, cracas subaquáticas e contraventamento
    mirar((0.95, -0.95, 0.85), (0.38, -0.38, 0.70), 48)
    sc.render.filepath = os.path.join(AQUI, 'plataforma_agua_perto.png')
    bpy.ops.render.render(write_still=True)

print('PLATAFORMA_AGUA ok')

