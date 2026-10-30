"""Estudo isolado (fora do jogo): BROCA DE NÚCLEO da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'broca_profunda'.
Perfuração profunda do manto planetário:
- Jazida esgotada rende 10% para sempre (mineração perpétua de minério profundo).
- Bocas no padrão do jogo:
  * ITEM_SAI_S1: esteira sul de minério britado profundo a z = 0,23 m (x = 0,0, y = -1,50 m).
  * FLUIDO_ENT_O1: tubulação oeste de fluido de perfuração/lama pesada a z = 0,35 m (x = -1,50 m, y = 0,0).

Engenharia pesada de perfuração ultra-profunda da IA:
- Base maciça de concreto armado 2,96 × 2,96 m com canaletas de lama, berços de ancoragem e sapatas pesadas.
- Torre Derrick de Perfuração em Treliça de Aço Corten (altura 2,55 m):
  * 4 Pilares estruturais inclinados convergindo para o topo com travamentos diagonais em X.
  * Moitão de polias quádruplo no topo com cabos de aço trançados para içamento de alta tonelagem.
  * Guias verticais duplas com cabeçote rotativo Top Drive motorizado deslizando no avanço de penetração.
- Coluna de Perfuração Rotativa:
  * Trado e haste de perfuração em liga pesada de tungstênio e diamante girando velozmente no poço de revestimento central.
  * Mangueiras reforçadas de injeção de fluido de perfuração sob pressão conectadas ao cabeçote giratório.
- Sistema de Peneiramento e Ejeção Sul:
  * Peneira vibratória (shaker) inclinada separando fragmentos de minério da lama de retorno.
  * Esteira sul de roletes de aço conduzindo pedras e minério britado para fora.
- Tanque de Circulação de Fluido Oeste:
  * Bocal rígido flangeado a 0,35 m com rotor fluxômetro, bomba centrífuga e tanque de decantação.

Peças animadas separadas:
- 'haste_perfuracao': haste de perfuração central girando velozmente a 8 voltas por ciclo.
- 'top_drive': cabeçote motriz superior oscilando suavemente em Z no avanço da perfuração.
- 'polia_topo_0', 'polia_topo_1': polias superiores do moitão girando sincronizadas com os cabos.
- 'peneira_vibratoria': calha de peneiramento com vibração de alta frequência separando sólidos.
- 'rolete_s0'..'s3': roletes de aço da esteira sul girando continuamente.
- 'minerio_transito_0'..'2': pedras de minério avançando na esteira sul.
- 'rotor_fluxo': rotor do fluxômetro de fluido oeste girando a 4 voltas por ciclo.

Uso: blender -b --python estudo_broca_nucleo.py -- foto
     blender -b --python estudo_broca_nucleo.py -- nada
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
    'minerio': mats.material('PedraMinerio', (0.28, 0.18, 0.12), 0.0, 0.9, sujeira=0.8, desgaste=0.8),
    'led_alerta': luz_mat('LedAlerta', (1.0, 0.2, 0.05), 12.0),
})

# ------------------------------------------------------------------ LAJE E BASE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base metálicas e berços dos 4 pilares
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
for cx, cy in ((-1.20, -1.20), (1.20, -1.20), (-1.20, 1.20), (1.20, 1.20)):
    caixa_de(bm_aco, (cx - 0.14, cy - 0.14, Z_LAJE + 0.02), (cx + 0.14, cy + 0.14, Z_LAJE + 0.08))
    hexa(bm_aco, (cx, cy), 0.035, Z_LAJE + 0.08, Z_LAJE + 0.12)

# Poço de boca de poço (wellhead) e mesa rotativa no piso
casca(bm_aco, (0, 0, 0), 0.55, 0.35, Z_LAJE + 0.02, Z_LAJE + 0.12, n=24)
toro(bm_aco, (0, 0, Z_LAJE + 0.12), 0.45, 0.025, nR=24, nr=8)
obj('placas_base_aco', bm_aco, 'aco')

# Listras de perigo industrial
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ BOCA SUL DE SAÍDA DE MINÉRIO (ITEM_SAI_S1)
p_boca_s = Vector((0.0, -1.50, Z_EST))
bm_est_s = bmesh.new()
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

# Fragmentos de minério de rocha profunda em trânsito
minerio_transito = []
for m_idx in range(3):
    bm_m = bmesh.new()
    pedra(bm_m, (0, 0, 0.03), 0.045, achatar=0.6)
    m_o = obj(f'minerio_transito_{m_idx}', bm_m, 'minerio')
    suavizar(m_o)
    minerio_transito.append(m_o)

# ------------------------------------------------------------------ BOCA OESTE DE FLUIDO DE PERFURAÇÃO (LAMA)
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
    (p_medidor[0] + 0.25, 0.45, Z_CANO),
    (-0.55, 0.45, 0.85)
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

# ------------------------------------------------------------------ TORRE DERRICK DE PERFURAÇÃO (2,55 m de altura)
bm_derrick = bmesh.new()
# 4 Pilares da torre convergindo de (±1.15, ±1.15, 0.08) até (±0.35, ±0.35, 2.45)
P_BASE_T = [Vector((-1.15, -1.15, Z_LAJE)), Vector((1.15, -1.15, Z_LAJE)),
            Vector((-1.15, 1.15, Z_LAJE)), Vector((1.15, 1.15, Z_LAJE))]
P_TOPO_T = [Vector((-0.35, -0.35, 2.45)), Vector((0.35, -0.35, 2.45)),
            Vector((-0.35, 0.35, 2.45)), Vector((0.35, 0.35, 2.45))]

for pb, pt in zip(P_BASE_T, P_TOPO_T):
    viga(bm_derrick, pb, pt, 0.12)

# Travamentos horizontais e diagonais da treliça nos 4 lados
for z_tr in (0.75, 1.35, 1.95):
    f_z = (z_tr - Z_LAJE) / (2.45 - Z_LAJE)
    pts_z = [pb + (pt - pb) * f_z for pb, pt in zip(P_BASE_T, P_TOPO_T)]
    for i in range(4):
        pA, pB = pts_z[i], pts_z[(i + 1) % 4]
        viga(bm_derrick, pA, pB, 0.07)

# Guias verticais centrais cromadas para o Top Drive
for gx in (-0.22, 0.22):
    cil(bm_derrick, (gx, 0.0, 1.35), 0.035, 2.10, lados=12)

# Coroa superior do moitão
caixa_de(bm_derrick, (-0.42, -0.42, 2.40), (0.42, 0.42, 2.55))
obj('torre_derrick', bm_derrick, 'amarelo_mineracao')

# Duas polias superiores do moitão giratórias (animadas separadas)
polias_topo = []
for p_idx, px in enumerate((-0.12, 0.12)):
    bm_pol = bmesh.new()
    cil(bm_pol, (0, 0, 0), 0.16, 0.04, eixo=Vector((0, 1, 0)), lados=16)
    toro(bm_pol, (0, 0, 0), 0.155, 0.015, nR=16, nr=6, rot=Matrix.Rotation(PI / 2, 3, 'X'))
    pol_o = obj(f'polia_topo_{p_idx}', bm_pol, 'cromo')
    pol_o.location = Vector((px, 0.0, 2.48))
    suavizar(pol_o)
    polias_topo.append(pol_o)

# ------------------------------------------------------------------ TOP DRIVE E COLUNA ROTATIVA DE PERFURAÇÃO
# Cabeçote Top Drive motorizado
bm_top = bmesh.new()
caixa_de(bm_top, (-0.28, -0.28, -0.25), (0.28, 0.28, 0.25))
# Redutor planetário e motor elétrico de acionamento
cil(bm_top, (0, 0, 0.35), 0.18, 0.30, lados=14)
# Mangueira flexível trançada de injeção de lama de alta pressão
mangueira(bm_top, [
    Vector((0.25, 0.15, 0.10)),
    Vector((0.45, 0.35, 0.40)),
    Vector((0.65, 0.45, 0.90)),
    Vector((0.55, 0.45, 1.40))
], 0.03)

top_drive = obj('top_drive', bm_top, 'titânio')
top_drive.location = Vector((0.0, 0.0, 1.45))
suavizar(top_drive)

# Haste rotativa de perfuração com trado helicoidal
bm_haste = bmesh.new()
cil(bm_haste, (0, 0, 0.60), 0.065, 1.80, lados=14)
# Lâminas helicoidais do trado de tungstênio
for h_i in range(16):
    z_h = 0.10 + h_i * 0.08
    a_h = h_i * PI / 4
    rot_h = Matrix.Rotation(a_h, 3, 'Z')
    bmesh.ops.create_cube(bm_haste, size=1.0, matrix=Matrix.Translation((0, 0, z_h)) @ rot_h.to_4x4() @
                          Matrix.Scale(0.18, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.04, 4, Vector((0, 1, 0))) @
                          Matrix.Scale(0.03, 4, Vector((0, 0, 1))))

haste_perfuracao = obj('haste_perfuracao', bm_haste, 'cromo')
haste_perfuracao.location = Vector((0.0, 0.0, 0.45))
suavizar(haste_perfuracao)

# ------------------------------------------------------------------ PENEIRA VIBRATÓRIA (SHAKER)
bm_peneira = bmesh.new()
caixa_de(bm_peneira, (-0.28, -0.65, Z_LAJE + 0.02), (0.28, 0.05, Z_EST + 0.02))
# Borda inclinada da peneira
for sgn in (-1, 1):
    viga(bm_peneira, (sgn * 0.26, -0.65, Z_EST + 0.03), (sgn * 0.26, 0.05, Z_EST + 0.08), 0.03)

peneira_vibratoria = obj('peneira_vibratoria', bm_peneira, 'aco')
suavizar(peneira_vibratoria)

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação veloz da haste de perfuração (8 voltas por ciclo)
    ang_haste = t * 16 * PI
    haste_perfuracao.rotation_euler = Euler((0, 0, ang_haste), 'XYZ')
    haste_perfuracao.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Rotação das polias do topo sincronizadas com o cabo
    ang_pol = t * 4 * PI
    for p_o in polias_topo:
        p_o.rotation_euler = Euler((0, ang_pol, 0), 'XYZ')
        p_o.keyframe_insert('rotation_euler', frame=q)
        
    # 3. Oscilação vertical suave do Top Drive (avanço de penetração no ciclo fechado)
    dz_top = 0.08 * math.sin(t * 2 * PI)
    top_drive.location = Vector((0.0, 0.0, 1.45 + dz_top))
    haste_perfuracao.location = Vector((0.0, 0.0, 0.45 + dz_top))
    top_drive.keyframe_insert('location', frame=q)
    haste_perfuracao.keyframe_insert('location', frame=q)
    
    # 4. Vibração de alta frequência da peneira de lama
    dz_pen = 0.006 * math.sin(t * 32 * PI)
    peneira_vibratoria.location = Vector((0.0, 0.0, dz_pen))
    peneira_vibratoria.keyframe_insert('location', frame=q)
    
    # 5. Rotação dos roletes da esteira sul
    ang_rol = t * 8 * PI
    for r_o in rolete_objs:
        r_o.rotation_euler = Euler((ang_rol, 0, 0), 'XYZ')
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 6. Rotação do fluxômetro de fluido oeste
    rotor_fluxo.rotation_euler = Euler((t * 8 * PI, 0, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 7. Avanço dos fragmentos de minério britado na esteira sul
    for m_i, m_o in enumerate(minerio_transito):
        fase_m = (t + m_i / 3.0) % 1.0
        y_m = -0.65 - fase_m * 0.80
        m_o.location = Vector((0.0, y_m, Z_EST + 0.025))
        m_o.keyframe_insert('location', frame=q)

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
    print(f'BROCA_NUCLEO_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'broca_nucleo_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na haste rotativa, trado helicoidal, mesa rotativa e peneira
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((1.15, -1.35, 1.35), (0.05, -0.15, 0.65), 38)
    sc.render.filepath = os.path.join(AQUI, 'broca_nucleo_perto.png')
    bpy.ops.render.render(write_still=True)

print('BROCA_NUCLEO ok')
