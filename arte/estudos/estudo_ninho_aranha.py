"""Estudo isolado (fora do jogo): NINHO DE ARANHA, 3×3 tiles (até 5.000 tris).
Construído pelas aranhas com sucata de fábrica e minério fundidos.
Gera novas aranhas mecânicas e é o alvo prioritário dos ataques defensivos:
- Ocupa a área de 3×3 tiles (diâmetro ~2,80 m, limites em [-1.44, 1.44] m) e altura de 2,65 m.
- Câmara central de incubação com abertura de eclosão (mandíbulas frontais) por onde a aranha sai.
- Mesma paleta da aranha: blindagem preta/grafite carbonizado, escória e minério fundidos,
  sensores e bioplasma em carmesim vivo (sem o amarelo industrial da fábrica).
- Animação em laço de 96 quadros (4 s a 24 fps):
  * 'mandibula_portal_esq' e 'mandibula_portal_dir': mandíbulas da abertura abrindo e fechando.
  * 'nucleo_bioplasma': núcleo de incubação central com pulso de escala e respiração biológica.
  * 'coroa_superior': garras dorsais com leve oscilação de confinamento.
  * 'luz_ninho': pulso volumétrico carmesim iluminando o interior e a boca da caverna.
  * 'EFEITO_fumaca_0'..'7': baforadas de vapor quente subindo da câmara.

Uso: blender -b --python estudo_ninho_aranha.py -- foto
     blender -b --python estudo_ninho_aranha.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(666)

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
    'blindagem_hostil': mats.material('BlindagemNinho', (0.10, 0.10, 0.12), 0.85, 0.35, pintura=False, sujeira=0.85, ferrugem=0.35, escovado=True),
    'sucata_fundida': mats.material('SucataFundida', (0.15, 0.14, 0.14), 0.7, 0.70, pintura=False, sujeira=0.95, ferrugem=0.6),
    'chassi_escuro': mats.material('MinérioEscuro', (0.07, 0.07, 0.08), 0.3, 0.85, pintura=False, sujeira=0.9),
    'bioplasma_carmesim': luz_mat('BioplasmaIncubacao', (1.0, 0.02, 0.04), 28.0),
    'fumaca_hostil': mats.material('FumacaVapor', (0.20, 0.18, 0.19), 0.0, 0.95, sujeira=0.0),
    'chao': mats.material('ChaoNinho', (0.20, 0.19, 0.18), 0.0, 0.92, sujeira=0.6),
})

# ================================================================== 1. MONTE BASAL DE SUCATA E MINÉRIO FUNDIDO
bm_base = bmesh.new()
bm_sucata = bmesh.new()

# Plataforma de terra negra calcinada e escória de fusão
cil(bm_base, (0.0, 0.0, 0.10), 1.40, 0.20, lados=16)

# Anel de rochas e blocos de minério fundidos
for i in range(10):
    ang = 2 * PI * i / 10 + 0.15
    r_bloco = random.uniform(1.15, 1.35)
    p_b = (math.cos(ang) * r_bloco, math.sin(ang) * r_bloco, 0.18)
    pedra(bm_base, p_b, random.uniform(0.18, 0.28), achatar=0.7)

# Cúpula externa do ninho com cavidade interna (oco para a câmara de incubação)
# Raio externo diminuindo de 1.25 m na base para 0.50 m no topo a z = 2.10 m
N_ANEIS = 5
z_alturas = [0.20, 0.70, 1.25, 1.75, 2.15]
raios_ext = [1.25, 1.05, 0.85, 0.65, 0.45]
raios_int = [0.95, 0.78, 0.58, 0.40, 0.25]
SEG = 14

aneis_ext = []
aneis_int = []

for r_out, r_in, z_p in zip(raios_ext, raios_int, z_alturas):
    pts_ext = []
    pts_int = []
    for s_i in range(SEG):
        ang = 2 * PI * s_i / SEG
        dx, dy = math.cos(ang), math.sin(ang)
        # Borda frontal ao sul (ang entre -135° e -45°, índices 9, 10, 11) tem abertura de eclosão
        pts_ext.append(bm_base.verts.new(Vector((dx * r_out, dy * r_out, z_p))))
        pts_int.append(bm_base.verts.new(Vector((dx * r_in, dy * r_in, z_p))))
    aneis_ext.append(pts_ext)
    aneis_int.append(pts_int)

# Criar faces da parede do ninho, deixando a abertura frontal aberta nos primeiros 3 anéis
for a_idx in range(N_ANEIS - 1):
    A_ext, B_ext = aneis_ext[a_idx], aneis_ext[a_idx + 1]
    A_int, B_int = aneis_int[a_idx], aneis_int[a_idx + 1]
    for s_i in range(SEG):
        s_nxt = (s_i + 1) % SEG
        # Abertura de eclosão ao sul (s_i em 10 ou 11) nas alturas inferiores (a_idx < 2)
        abertura_sul = (a_idx < 2) and (s_i in (10, 11))
        if not abertura_sul:
            bm_base.faces.new((A_ext[s_i], A_ext[s_nxt], B_ext[s_nxt], B_ext[s_i]))
            bm_base.faces.new((B_int[s_i], B_int[s_nxt], A_int[s_nxt], A_int[s_i]))

# Pilares e vigas de sucata torcida inclinadas convergindo para o topo (formando a coroa)
for p_i in range(8):
    ang_p = 2 * PI * p_i / 8
    # Deixar o portal sul livre (p_i == 6 é 270° / -Y)
    if p_i == 6:
        continue
    p_chao = Vector((math.cos(ang_p) * 1.32, math.sin(ang_p) * 1.32, 0.15))
    p_topo = Vector((math.cos(ang_p) * 0.40, math.sin(ang_p) * 0.40, 2.35))
    viga(bm_sucata, p_chao, p_topo, 0.11)
    # Espigão afiado se projetando além do topo
    p_ponta = p_topo + Vector((math.cos(ang_p) * 0.14, math.sin(ang_p) * 0.14, 0.32))
    viga(bm_sucata, p_topo, p_ponta, 0.08)

# Dois pilares laterais reforçados emoldurando o portal de eclosão ao sul
for s_p in (-0.52, 0.52):
    p_chao_g = Vector((s_p, -1.22, 0.15))
    p_topo_g = Vector((s_p * 0.65, -0.72, 1.45))
    viga(bm_sucata, p_chao_g, p_topo_g, 0.10)

# Placas de blindagem rebitadas/soldadas sobre a parede externa
for pl_i in range(6):
    ang_pl = 2 * PI * pl_i / 6 + 0.35
    p_pl = Vector((math.cos(ang_pl) * 0.98, math.sin(ang_pl) * 0.98, 1.10))
    caixa(bm_sucata, p_pl, (0.28, 0.28, 0.04))

# Dentes pontiagudos ao redor do arco da abertura de eclosão ao sul
for d_i, dx_d in enumerate((-0.42, -0.21, 0.0, 0.21, 0.42)):
    p_dente_base = Vector((dx_d, -0.92, 1.15))
    p_dente_ponta = Vector((dx_d * 0.85, -0.86, 0.85))
    viga(bm_sucata, p_dente_base, p_dente_ponta, 0.048)

o_base = obj('ninho_base', bm_base, 'chassi_escuro')
o_sucata = obj('ninho_estruturas', bm_sucata, 'blindagem_hostil')
suavizar(o_base)
suavizar(o_sucata)

# ================================================================== 2. MANDÍBULAS ARTICULADAS DA ABERTURA FRONTAL
# Duas quelíceras mecânicas na boca do ninho que abrem e fecham
bm_mand_esq = bmesh.new()
bm_mand_dir = bmesh.new()

# Garra esquerda
viga(bm_mand_esq, (0.0, 0.0, 0.0), (-0.18, 0.25, -0.15), 0.065)
bmesh.ops.create_cone(bm_mand_esq, cap_ends=True, segments=6, radius1=0.045, radius2=0.005, depth=0.25,
                      matrix=Matrix.Translation((-0.18, 0.35, -0.25)) @ Matrix.Rotation(math.radians(-45), 4, 'X'))
o_mand_esq = obj('mandibula_portal_esq', bm_mand_esq, 'blindagem_hostil')
o_mand_esq.location = Vector((-0.38, -0.85, 0.45))
suavizar(o_mand_esq)

# Garra direita (espelhada)
viga(bm_mand_dir, (0.0, 0.0, 0.0), (0.18, 0.25, -0.15), 0.065)
bmesh.ops.create_cone(bm_mand_dir, cap_ends=True, segments=6, radius1=0.045, radius2=0.005, depth=0.25,
                      matrix=Matrix.Translation((0.18, 0.35, -0.25)) @ Matrix.Rotation(math.radians(-45), 4, 'X'))
o_mand_dir = obj('mandibula_portal_dir', bm_mand_dir, 'blindagem_hostil')
o_mand_dir.location = Vector((0.38, -0.85, 0.45))
suavizar(o_mand_dir)

# ================================================================== 3. NÚCLEO DE BIOPLASMA / INCUBAÇÃO CENTRAL
bm_nucleo = bmesh.new()
# Casulo / ovoide cristalino bio-mecânico central
bmesh.ops.create_uvsphere(bm_nucleo, u_segments=12, v_segments=8, radius=0.38,
                          matrix=Matrix.Scale(1.35, 4, Vector((0, 0, 1))))
o_nucleo = obj('nucleo_bioplasma', bm_nucleo, 'bioplasma_carmesim')
o_nucleo.location = Vector((0.0, 0.0, 0.95))
suavizar(o_nucleo, tudo=True)

# Luz carmesim de incubação volumétrica
luz_ninho_data = bpy.data.lights.new('LuzNinho', 'POINT')
luz_ninho_data.color = (1.0, 0.02, 0.05)
luz_ninho_data.energy = 320.0
luz_ninho_data.shadow_soft_size = 0.35
luz_ninho = bpy.data.objects.new('LuzNinho', luz_ninho_data)
sc.collection.objects.link(luz_ninho)
luz_ninho.location = Vector((0.0, -0.15, 1.05))

# ================================================================== 4. COROA SUPERIOR OSCILANTE
bm_coroa = bmesh.new()
# Anel de garras superiores
for g_i in range(6):
    ang_g = 2 * PI * g_i / 6
    p_g0 = Vector((math.cos(ang_g) * 0.32, math.sin(ang_g) * 0.32, 0.0))
    p_g1 = Vector((math.cos(ang_g) * 0.20, math.sin(ang_g) * 0.20, 0.35))
    viga(bm_coroa, p_g0, p_g1, 0.05)
o_coroa = obj('coroa_superior', bm_coroa, 'blindagem_hostil')
o_coroa.location = Vector((0.0, 0.0, 2.25))
suavizar(o_coroa)

# ================================================================== 5. VAPOR E FUMAÇA HOSTIL (EFEITO)
fumacas = []
for f_i in range(5):
    bm_f = bmesh.new()
    bmesh.ops.create_uvsphere(bm_f, u_segments=8, v_segments=6, radius=0.14 + 0.03 * f_i)
    o_f = obj(f'EFEITO_fumaca_{f_i}', bm_f, 'fumaca_hostil')
    suavizar(o_f, tudo=True)
    fumacas.append(o_f)

# ================================================================== ANIMAÇÃO EM LAÇO (96 QUADROS, 4 s)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Movimento de mastigação/abertura das mandíbulas mecânicas frontais
    # 2 ciclos de abertura/fechamento por laço de 4 s
    ang_mand = math.radians(16.0) * math.sin(t * 4 * PI)
    o_mand_esq.rotation_euler = Euler((0, 0, -ang_mand), 'XYZ')
    o_mand_dir.rotation_euler = Euler((0, 0, ang_mand), 'XYZ')
    o_mand_esq.keyframe_insert('rotation_euler', frame=q)
    o_mand_dir.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Respiração pulsante de escala do núcleo de bioplasma (batimento cardíaco vivo)
    # Pulso rítmico assimétrico
    pulso_bio = 1.0 + 0.08 * math.sin(t * 8 * PI) + 0.04 * math.sin(t * 16 * PI)
    o_nucleo.scale = Vector((pulso_bio, pulso_bio, pulso_bio * 1.05))
    o_nucleo.keyframe_insert('scale', frame=q)
    
    # 3. Pulso de luminosidade da câmara de incubação
    luz_ninho_data.energy = 300.0 + 140.0 * math.sin(t * 8 * PI)
    luz_ninho_data.keyframe_insert('energy', frame=q)
    
    # 4. Oscilação lenta da coroa superior de confinamento
    o_coroa.rotation_euler = Euler((0, 0, math.radians(6.0) * math.sin(t * 2 * PI)), 'XYZ')
    o_coroa.keyframe_insert('rotation_euler', frame=q)
    
    # 5. Fumaça/vapor tóxico subindo da chaminé e se dissipando
    for f_idx, o_f in enumerate(fumacas):
        f_t = (t + f_idx / 5.0) % 1.0
        z_fum = 2.20 + f_t * 1.10
        r_fum = 0.15 + f_t * 0.25
        ang_fum = f_idx * 1.25 + f_t * 2.0
        o_f.location = Vector((math.cos(ang_fum) * r_fum, math.sin(ang_fum) * r_fum, z_fum))
        s_fum = 0.5 + f_t * 1.2
        o_f.scale = Vector((s_fum, s_fum, s_fum))
        o_f.keyframe_insert('location', frame=q)
        o_f.keyframe_insert('scale', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.05), (14, 14, 0.10))
obj('EFEITO_chao', bm_chao, 'chao')

# Sol principal
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-38))

# Luz de contra-luz suave
sol2 = bpy.data.lights.new('Sol2', 'SUN')
sol2.energy = 1.6
so2 = bpy.data.objects.new('Sol2', sol2)
sc.collection.objects.link(so2)
so2.rotation_euler = (math.radians(-32), 0, math.radians(140))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.45, 0.48, 0.58, 1)
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

ALVO = (0.0, -0.15, 1.25)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO'))
    print(f'NINHO_ARANHA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    
    # 4 ângulos cardeais/isométricos capturando o monte hostil, a abertura de eclosão e o topo
    # Ângulo frontal 0 voltado diretamente para a boca sul (270°)
    for i, (ang, alt, f_num) in enumerate(((270, 3.4, 24), (200, 3.8, 15), (25, 4.2, 60), (115, 3.5, 84))):
        sc.frame_set(f_num)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, alt - ALVO[2])), ALVO, 35)
        sc.render.filepath = os.path.join(AQUI, f'ninho_aranha_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up focado na abertura de eclosão, mandíbulas ativas e núcleo carmesim brilhante
    sc.frame_set(24)
    mirar((0.0, -2.10, 0.95), (0.0, -0.65, 0.85), 45)
    sc.render.filepath = os.path.join(AQUI, 'ninho_aranha_perto.png')
    bpy.ops.render.render(write_still=True)

print('NINHO_ARANHA ok')
