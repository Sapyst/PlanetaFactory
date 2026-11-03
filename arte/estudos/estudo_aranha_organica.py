"""Estudo isolado exploratório (alta fidelidade artística): ARANHA BIO-MECÂNICA ORGÂNICA.
Versão artística rica, detalhada e de estética biomórfica de predador alienígena:
- Quitina negra com iridescência e textura de carapaça de besouro/escorpião.
- Cefalotórax esculpido com tubérculo ocular, 8 olhos sensores compostos em carmesim vítreo.
- Quelíceras volumétricas articuladas com presas venenosas pontiagudas e pedipalpos frontais com sensores táteis.
- Abdômen (opistossoma) bulboso e segmentado com tergitos dorsais sobrepostos e fiandeiras traseiras.
- 6 Pernas biomecânicas completas com coxas arredondadas, fêmures arqueados com tendões e atuadores cromados,
  joelhos com coifas flexíveis, tíbias caneladas com espinhos ventrais e garras tarsais curvas.
- Animação em laço de 96 quadros (4 s): respiração abdominal, contração dos pedipalpos e pulso ocular.

Uso: blender -b --python estudo_aranha_organica.py -- foto
     blender -b --python estudo_aranha_organica.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(999)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

QUADRIL_Z = 0.55
FEMUR_LEN = 0.70
TIBIA_LEN = 0.90
QUADRIS = [(s * 0.42, y) for y in (0.35, 0.0, -0.35) for s in (1, -1)]

def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o

# ------------------------------------------------------------------ MATERIAIS BIOMECÂNICOS RICOS
def mat_quitina_iridescente():
    m = bpy.data.materials.new('QuitinaIridescente')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    # Cor base com brilho perolado / carapaça de besouro
    bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.065, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.82
    bsdf.inputs['Roughness'].default_value = 0.24
    
    # Iridescência / Coat perolado
    if 'Coat Weight' in bsdf.inputs:
        bsdf.inputs['Coat Weight'].default_value = 0.75
        bsdf.inputs['Coat Roughness'].default_value = 0.15
        if 'Coat Tint' in bsdf.inputs:
            bsdf.inputs['Coat Tint'].default_value = (0.45, 0.20, 0.55, 1.0)
    return m

def mat_olho_composto():
    m = bpy.data.materials.new('OlhoComposto')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (0.20, 0.01, 0.02, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.08
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.03, 0.06, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 18.0
    return m

def mat_musculo():
    m = bpy.data.materials.new('MusculoSintetico')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (0.08, 0.06, 0.07, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.3
    bsdf.inputs['Roughness'].default_value = 0.55
    return m

base3d.M.update({
    'quitina': mat_quitina_iridescente(),
    'olho': mat_olho_composto(),
    'musculo': mat_musculo(),
    'cromo': mats.material('PistaoCromo', (0.85, 0.86, 0.88), 1.0, 0.12, pintura=False),
    'presa': mats.material('PresaAcido', (0.04, 0.03, 0.03), 0.2, 0.10, pintura=False),
    'chao': mats.material('SoloAlien', (0.16, 0.15, 0.14), 0.0, 0.92, sujeira=0.6),
})

# ================================================================== 1. CEFALOTÓRAX ESCULPIDO
bm_corpo = bmesh.new()

# Cúpula principal do cefalotórax (cefalotórax abaulado com chanfros orgânicos)
# z de 0.46 a 0.72 m, y de -0.28 a 0.40 m
N_LAT = 16
for y_c, r_x, r_z in [(-0.25, 0.36, 0.18), (-0.05, 0.38, 0.21), (0.18, 0.35, 0.19), (0.36, 0.26, 0.14)]:
    cil(bm_corpo, (0.0, y_c, QUADRIL_Z + 0.03), r_x, 0.15, lados=12)

# Cristas dorsais e ranhuras respiratórias laterais (espiráculos)
for s in (-1, 1):
    for y_esp in (-0.15, 0.0, 0.15):
        p_esp = Vector((s * 0.36, y_esp, QUADRIL_Z + 0.04))
        cil(bm_corpo, p_esp, 0.025, 0.04, lados=6, eixo=(s, 0, 0))

# Tubérculo ocular proeminente (torreta frontal)
cil(bm_corpo, (0.0, 0.38, QUADRIL_Z + 0.07), 0.14, 0.08, lados=10)

# ================================================================== 2. 8 OLHOS COMPOSTOS EM CARMESIM
bm_olhos = bmesh.new()

# 2 Olhos medianos anteriores (grandes e frontais)
for s in (-1, 1):
    cil(bm_olhos, (s * 0.055, 0.45, QUADRIL_Z + 0.08), 0.038, 0.022, lados=10, eixo=(0, 1, 0))

# 2 Olhos medianos posteriores (dorsais)
for s in (-1, 1):
    cil(bm_olhos, (s * 0.075, 0.38, QUADRIL_Z + 0.12), 0.028, 0.020, lados=8, eixo=(0, 0.5, 1))

# 4 Olhos laterais (vigilância periférica)
for s in (-1, 1):
    cil(bm_olhos, (s * 0.13, 0.42, QUADRIL_Z + 0.06), 0.024, 0.018, lados=8, eixo=(s * 0.7, 0.7, 0))
    cil(bm_olhos, (s * 0.14, 0.35, QUADRIL_Z + 0.08), 0.020, 0.018, lados=8, eixo=(s, 0.2, 0))

# ================================================================== 3. QUELÍCERAS, PRESAS E PEDIPALPOS
bm_presas = bmesh.new()
bm_pedipalpos = bmesh.new()

for s in (-1, 1):
    x_q = s * 0.10
    # Bulbo muscular da quelícera
    cil(bm_corpo, (x_q, 0.46, QUADRIL_Z - 0.06), 0.075, 0.18, lados=8, eixo=(0, 0.3, -1))
    
    # Presa encurvada e afiada (garra de inoculação)
    pts_presa = [
        Vector((x_q, 0.48, QUADRIL_Z - 0.14)),
        Vector((x_q * 0.9, 0.56, QUADRIL_Z - 0.24)),
        Vector((s * 0.04, 0.60, QUADRIL_Z - 0.34))
    ]
    cano_pts = pts_presa
    for a, b in zip(cano_pts, cano_pts[1:]):
        tubo(bm_presas, a, b, 0.028, 8)
    # Ponta da presa
    bmesh.ops.create_cone(bm_presas, cap_ends=True, segments=8, radius1=0.028, radius2=0.003, depth=0.10,
                          matrix=Matrix.Translation(pts_presa[-1] + Vector((0, 0.03, -0.05))) @
                                 (pts_presa[-1] - pts_presa[-2]).to_track_quat('Z', 'Y').to_matrix().to_4x4())

    # Pedipalpos mecatrônicos frontais (antenas táteis com pinças)
    x_p = s * 0.22
    p0 = Vector((x_p, 0.40, QUADRIL_Z - 0.04))
    p1 = Vector((x_p + s * 0.08, 0.55, QUADRIL_Z + 0.06))
    p2 = Vector((s * 0.16, 0.75, QUADRIL_Z - 0.05))
    viga(bm_pedipalpos, p0, p1, 0.04)
    cil(bm_pedipalpos, p1, 0.035, 0.05, lados=8)
    viga(bm_pedipalpos, p1, p2, 0.03)
    cil(bm_olhos, p2, 0.022, 0.03, lados=6)

# ================================================================== 4. ABDÔMEN (OPISTOSSOMA) BULBOSO E SEGMENTADO
# Objeto separado para animação de respiração orgânica
bm_abdomen = bmesh.new()

# Bulbo abdominal composto por 5 elipsoides segmentados sobrepostos
secoes_abd = [
    (-0.35, 0.38, 0.26, 0.22),
    (-0.55, 0.46, 0.32, 0.26),
    (-0.75, 0.44, 0.30, 0.24),
    (-0.95, 0.34, 0.22, 0.18),
    (-1.10, 0.20, 0.14, 0.12)
]

for y_a, rx, rz, comp in secoes_abd:
    cil(bm_abdomen, (0.0, y_a, QUADRIL_Z + 0.10), rx, comp, lados=14)

# 4 Tergitos dorsais quitinosos arqueados sobre a coluna do abdômen
for t_i, (y_t, larg) in enumerate([(-0.45, 0.34), (-0.65, 0.40), (-0.85, 0.36), (-1.02, 0.24)]):
    p_t = Vector((0.0, y_t, QUADRIL_Z + 0.25))
    caixa(bm_abdomen, p_t, (larg, 0.12, 0.04))

# Fiandeiras mecânicas bio-produtoras no ápice traseiro
for s in (-1, 1):
    p_fian = Vector((s * 0.05, -1.18, QUADRIL_Z + 0.07))
    cil(bm_abdomen, p_fian, 0.028, 0.09, lados=8, eixo=(0, -1, 0))

# ================================================================== 5. ARTICULAÇÕES DOS 6 QUADRIS
bm_coxas = bmesh.new()
bm_musculos = bmesh.new()

for hx, hy in QUADRIS:
    # Cavidade esferoidal e mancal reforçado do quadril
    p_q = Vector((hx, hy, QUADRIL_Z))
    cil(bm_coxas, p_q, 0.088, 0.14, lados=10)
    # Feixes musculares sintéticos ligando o quadril à base do corpo
    viga(bm_musculos, p_q * 0.65 + Vector((0, 0, -0.05)), p_q, 0.055)

# ================================================================== 6. PERNAS BIOMECÂNICAS ORGÂNICAS EM MARCHA
bm_pernas = bmesh.new()
bm_pistoes = bmesh.new()

for leg_i, (hx, hy) in enumerate(QUADRIS):
    d = Vector((hx, hy, 0)).normalized()
    # Pé no chão em pose predatória agressiva
    if leg_i in (0, 3, 4):
        pe = Vector((hx, hy, 0.02)) + d * 1.05
    else:
        pe = Vector((hx, hy, 0.16)) + d * 1.15 + Vector((0, 0.14, 0))
    
    q = Vector((hx, hy, QUADRIL_Z))
    alvo = pe - q
    dist = alvo.length
    
    cos_a = max(-1.0, min(1.0, (FEMUR_LEN**2 + dist**2 - TIBIA_LEN**2) / (2.0 * FEMUR_LEN * dist)))
    a = math.acos(cos_a)
    base_ang = math.atan2(alvo.z, Vector((alvo.x, alvo.y)).length)
    el = base_ang + a
    
    joelho = q + d * (FEMUR_LEN * math.cos(el)) + Vector((0, 0, FEMUR_LEN * math.sin(el)))
    
    # --- Fêmur curvo com crista dorsal
    viga(bm_pernas, q, joelho, 0.082)
    # Crista quitinosa dorsal no fêmur
    u_f = (joelho - q).normalized()
    p_meio_f = q + u_f * (FEMUR_LEN * 0.5) + Vector((0, 0, 0.05))
    caixa(bm_pernas, p_meio_f, (0.065, 0.35, 0.035))
    
    # Pistão hidráulico cromado flexor do fêmur
    p_p1 = q + Vector((0, 0, 0.04)) + u_f * 0.12
    p_p2 = joelho + Vector((0, 0, 0.03)) - u_f * 0.08
    tubo(bm_pernas, p_p1, p_p1 + (p_p2 - p_p1) * 0.55, 0.024, 8)
    tubo(bm_pistoes, p_p1 + (p_p2 - p_p1) * 0.50, p_p2, 0.015, 8)
    
    # --- Joelho (Patela articulada com coifa)
    cil(bm_pernas, joelho, 0.072, 0.12, lados=10)
    
    # --- Tíbia arqueada
    viga(bm_pernas, joelho, pe, 0.068)
    # Espinhos quitinosos ventrais na tíbia
    u_t = (pe - joelho).normalized()
    for esp_k in (0.35, 0.65):
        p_esp_t = joelho + u_t * (TIBIA_LEN * esp_k)
        viga(bm_pernas, p_esp_t, p_esp_t - Vector((0, 0, 0.065)) + d * 0.03, 0.020)
        
    # --- Garra tarsal curva penetrando o solo
    bmesh.ops.create_cone(bm_pernas, cap_ends=True, segments=8, radius1=0.045, radius2=0.005, depth=0.20,
                          matrix=Matrix.Translation(pe + (joelho - pe).normalized() * 0.09) @
                                 (pe - joelho).to_track_quat('Z', 'Y').to_matrix().to_4x4())

# ================================================================== OBJETOS NA CENA
o_corpo = obj('aranha_cefalotorax', bm_corpo, 'quitina')
o_olhos = obj('aranha_olhos', bm_olhos, 'olho')
o_presas = obj('aranha_presas', bm_presas, 'presa')
o_pedipalpos = obj('aranha_pedipalpos', bm_pedipalpos, 'quitina')
o_abdomen = obj('aranha_abdomen', bm_abdomen, 'quitina')
o_coxas = obj('aranha_coxas', bm_coxas, 'quitina')
o_musculos = obj('aranha_musculos', bm_musculos, 'musculo')
o_pernas = obj('aranha_pernas', bm_pernas, 'quitina')
o_pistoes = obj('aranha_pistoes', bm_pistoes, 'cromo')

suavizar(o_corpo, tudo=True)
suavizar(o_olhos, tudo=True)
suavizar(o_presas, tudo=True)
suavizar(o_pedipalpos, tudo=True)
suavizar(o_abdomen, tudo=True)
suavizar(o_coxas, tudo=True)
suavizar(o_musculos, tudo=True)
suavizar(o_pernas, tudo=True)
suavizar(o_pistoes, tudo=True)

# ================================================================== ANIMAÇÃO EM LAÇO (96 QUADROS)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS
    
    # 1. Respiração orgânica do abdômen (expansão harmônica de escala e leve elevação)
    resp = 1.0 + 0.045 * math.sin(t * 4 * PI)
    o_abdomen.scale = Vector((resp, resp * 1.02, resp * 1.03))
    o_abdomen.location = Vector((0.0, 0.0, 0.015 * math.sin(t * 4 * PI)))
    o_abdomen.keyframe_insert('scale', frame=q)
    o_abdomen.keyframe_insert('location', frame=q)
    
    # 2. Micromovimento predatório dos pedipalpos (inquietude sensorial)
    rot_ped = math.radians(4.0) * math.sin(t * 8 * PI)
    o_pedipalpos.rotation_euler = Euler((rot_ped * 0.5, 0, rot_ped), 'XYZ')
    o_pedipalpos.keyframe_insert('rotation_euler', frame=q)

# ================================================================== CENA, ILUMINAÇÃO E CÂMERAS
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.05), (12, 12, 0.10))
# Adicionar pedras no terreno
for r_k in range(8):
    ang_r = r_k * 2 * PI / 8 + 0.4
    p_r = (math.cos(ang_r) * 1.6, math.sin(ang_r) * 1.6, 0.02)
    pedra(bm_chao, p_r, 0.12, achatar=0.5)
obj('EFEITO_chao', bm_chao, 'chao')

# Iluminação cinematográfica de alto contraste para destacar a iridescência
sol = bpy.data.lights.new('SolPrincipal', 'SUN')
sol.energy = 4.5
sol.angle = math.radians(2.0)
so = bpy.data.objects.new('SolPrincipal', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-38))

# Luz de contorno azulada/fria na traseira para delinear as patas e abdômen
sol_rim = bpy.data.lights.new('SolRim', 'SUN')
sol_rim.energy = 2.2
sol_rim.color = (0.55, 0.70, 0.90)
so_rim = bpy.data.objects.new('SolRim', sol_rim)
sc.collection.objects.link(so_rim)
so_rim.rotation_euler = (math.radians(-30), 0, math.radians(145))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.42, 0.46, 0.54, 1)
bg.inputs['Strength'].default_value = 0.60

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
sc.view_settings.exposure = -0.25

cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente

ALVO = (0.0, 0.0, 0.50)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO'))
    print(f'ARANHA_ORGANICA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1280, 1080
    
    # 4 ângulos cardeais/isométricos destacando a postura predatória
    for i, (ang, alt, f_num) in enumerate(((140, 2.5, 24), (40, 2.3, 48), (320, 2.6, 72), (220, 2.2, 96))):
        sc.frame_set(f_num)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 3.5, math.sin(a) * 3.5, alt - ALVO[2])), ALVO, 38)
        sc.render.filepath = os.path.join(AQUI, f'aranha_organica_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up dramático na cabeça, olhos carmesim, quelíceras e presas de inoculação
    sc.frame_set(36)
    mirar((0.45, 1.25, 0.72), (0.0, 0.45, 0.50), 55)
    sc.render.filepath = os.path.join(AQUI, 'aranha_organica_perto.png')
    bpy.ops.render.render(write_still=True)

print('ARANHA_ORGANICA ok')
