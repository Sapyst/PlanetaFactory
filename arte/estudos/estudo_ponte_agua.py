"""Estudo isolado (fora do jogo): PONTE SOBRE A ÁGUA (1×1 tile), até 400 tris.
Apoio logístico para esteira, cano e trilho sobre rios e lagos.
Mesma altura e linguagem visual da plataforma_agua:
- Vão estreito no sentido do fluxo (sul-norte, eixo Y de -0,50 a +0,50 m) emendando sem frestas.
- 2 pilares nas laterais (x = -0,42 e +0,42 m) descendo até o leito (z = 0 a 1,90 m).
- Estática, sem animação de máquina.
- Detalhes de textura e silhueta: sapatas submersas no leito, cracas/oxidação na zona subaquática,
  anel de telemetria de cota d'água, viga transversal de amarração, vigas longitudinais e deque reforçado.

Uso: blender -b --python estudo_ponte_agua.py -- foto
     blender -b --python estudo_ponte_agua.py -- nada
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
    'deck_gasto': mats.material('DeckPonteGasto', (0.28, 0.30, 0.32), 0.95, 0.45, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True),
    'aco_estrutural': mats.material('AcoPonte', (0.35, 0.36, 0.37), 1.0, 0.40, pintura=False, ferrugem=0.75, sujeira=0.8),
    'pilar_submerso': mats.material('PilarPonteSubmerso', (0.16, 0.18, 0.17), 0.4, 0.80, pintura=False, ferrugem=0.95, sujeira=1.0),
    'sapata_leito': mats.material('SapataPonteLeito', (0.22, 0.23, 0.22), 0.1, 0.95, pintura=False, ferrugem=0.6, sujeira=1.0),
    'anel_telemetria': luz_mat('LuzTelemetriaPonte', (0.15, 0.85, 0.95), 10.0),
    'chao': mats.material('LeitoRioPonte', (0.14, 0.15, 0.13), 0, 0.95, sujeira=0.8),
})

# ------------------------------------------------------------------ 1. PILARES LATERAIS E SAPATAS (z = 0 a 1.76 m)
bm_pilares = bmesh.new()
bm_sapatas = bmesh.new()
bm_aneis = bmesh.new()
bm_estrut = bmesh.new()

pos_pilares = [(-0.42, 0.0), (0.42, 0.0)]

for px, py in pos_pilares:
    # Sapata reforçada no leito (z = 0.0 a 0.16 m)
    cil(bm_sapatas, (px, py, 0.08), 0.11, 0.16, lados=8)
    
    # Tubo principal do pilar (z = 0.08 a 1.76 m)
    cil(bm_pilares, (px, py, 0.92), 0.072, 1.68, lados=8)
    
    # Colar de maré / cracas submersas (z = 0.30 a 0.55 m)
    cil(bm_sapatas, (px, py, 0.42), 0.086, 0.20, lados=8)
    
    # Anel luminescente de cota d'água / telemetria a z = 1.60 m
    cil(bm_aneis, (px, py, 1.60), 0.082, 0.04, lados=8)
    
    # Consolos / mísulas de topo suportando o vigamento longitudinal (z = 1.70 a 1.78 m)
    caixa(bm_estrut, (px, py, 1.74), (0.16, 0.22, 0.08))

# Travessa transversal inferior conectando os 2 pilares a z = 1.00 m
viga(bm_estrut, (-0.42, 0.0, 1.00), (0.42, 0.0, 1.00), 0.06)

# Vigas longitudinais estruturais sob as bordas do deque (ao longo de Y, de -0.48 a +0.48 m)
for px in (-0.42, 0.42):
    viga(bm_estrut, (px, -0.48, 1.80), (px, 0.48, 1.80), 0.065)

# ------------------------------------------------------------------ 2. DEQUE DA PONTE (z = 1.83 a 1.90 m)
bm_deque = bmesh.new()

# Deque ocupando y de -0.50 a +0.50 m (1,00 m exato) para emenda contínua na direção do fluxo
# Largura livre de 0,94 m (x de -0.47 a +0.47 m)
caixa_de(bm_deque, (-0.47, -0.50, 1.83), (0.47, 0.50, 1.90))

# Guias laterais / bordas reforçadas para contenção de esteira/cano
caixa_de(bm_estrut, (-0.48, -0.50, 1.83), (-0.45, 0.50, 1.93))
caixa_de(bm_estrut, (0.45, -0.50, 1.83), (0.48, 0.50, 1.93))

# Objetos da cena
o_sapatas = obj('ponte_sapatas', bm_sapatas, 'sapata_leito')
o_pilares = obj('ponte_pilares', bm_pilares, 'pilar_submerso')
o_estrut = obj('ponte_estruturas', bm_estrut, 'aco_estrutural')
o_aneis = obj('ponte_aneis', bm_aneis, 'anel_telemetria')
o_deque = obj('ponte_deque', bm_deque, 'deck_gasto')

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
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO'))
    print(f'PONTE_AGUA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    
    # 4 ângulos cardeais/isométricos mostrando os 1,9 m de altura e o canal de fluxo sul-norte
    for i, (ang, alt) in enumerate(((320, 2.5), (220, 2.3), (140, 2.6), (40, 2.2))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 3.4, math.sin(a) * 3.4, alt - ALVO[2])), ALVO, 38)
        sc.render.filepath = os.path.join(AQUI, f'ponte_agua_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up focado no pilar lateral, sapata de leito, anel de cota e cabeceira do deque
    mirar((0.95, -0.65, 0.95), (0.42, 0.0, 0.85), 46)
    sc.render.filepath = os.path.join(AQUI, 'ponte_agua_perto.png')
    bpy.ops.render.render(write_still=True)

print('PONTE_AGUA ok')
