"""Estudo isolado (fora do jogo): LABORATÓRIO QUÂNTICO da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'laboratorio_3'.
O ápice da computação científica e análise espectral quântica:
- Velocidade 4,0 (4× a velocidade do laboratório básico).
- 4 Encaixes de Módulos Quânticos (em vez de 2 do Laboratório 2).
- Bocas no padrão do jogo:
  * ITEM_ENT_S1: esteira sul de pacotes de ciência primários a z = 0,23 m (x = 0,0, y = -1,50 m).
  * ITEM_ENT_O1: esteira oeste de pacotes de ciência secundários a z = 0,23 m (x = -1,50 m, y = 0,0).
  * FLUIDO_ENT_L1: tubulação leste de fluido quântico/supercondutor criogênico a z = 0,35 m (x = +1,50 m, y = 0,0).

Engenharia de espectrometria e dobra quântica da IA:
- Base de concreto armado e titânio 2,96 × 2,96 m com canaletas de cabeamento óptico e esteiras sul e oeste com roletes de aço.
- Tambor Central de Espectrometria Quântica:
  * Vaso blindado esferoidal de vácuo extremo em ouro e titânio com janelas de quartzo polarizado.
  * Carrossel óptico quântico de difração superior com anéis prismáticos girando continuamente.
  * Câmara de desintegração espectral com 4 feixes laser cruzados violeta, ciano e esmeralda.
  * Braço mecatrônico duplo alimentando pacotes de ciência na gaveta hermética.
- Baia de 4 Módulos Quânticos:
  * 4 Cartuchos de módulos quânticos em pedestal rebaixado a sudeste com barras de dissipação criogênica e LEDs ciano.
- Radiador Criogênico Duplo em V a Noroeste:
  * Dois radiadores aletados com ventiladores axiais de alto fluxo girando velozmente.
- Boca Leste de Fluido:
  * Bocal rígido flangeado a 0,35 m com medidor de vazão rotativo.

Peças animadas separadas:
- 'carrossel_optico': anéis prismáticos do teto girando a 360° em Z.
- 'braco_analise': braço mecatrônico pegando pacotes de ciência e inserindo no tambor.
- 'ventoinha_rad0', 'ventoinha_rad1': ventoinhas do radiador em V girando a 6 voltas por ciclo.
- 'rotor_fluxo': rotor do fluxômetro de fluido leste girando a 4 voltas por ciclo.
- 'rolete_s0'..'s3', 'rolete_o0'..'o3': roletes de aço das esteiras sul e oeste girando continuamente.
- 'pacote_transito_s', 'pacote_transito_o': pacotes de ciência avançando nas esteiras.
- 'luz_espectro': clarão harmônico multiespectral no interior do tambor de análise.

Uso: blender -b --python estudo_laboratorio_quantico.py -- foto
     blender -b --python estudo_laboratorio_quantico.py -- nada
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
Z_EST = 0.23                 # esteiras sul e oeste
Z_CANO = 0.35                # tubo de fluido leste

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
    'espectro': luz_mat('EspectroQuântico', (0.45, 0.25, 1.0), 22.0),
    'cristal_res': luz_mat('CristalOptico', (0.1, 0.9, 0.95), 18.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 12.0),
    'pacote_ciencia': luz_mat('PacoteCiencia', (0.85, 0.15, 0.95), 14.0),
})

# ------------------------------------------------------------------ LAJE E BASE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base metálicas
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
obj('placas_base_aco', bm_aco, 'aco')

# Listras de perigo industrial
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ BOCAS E ESTEIRAS (SUL E OESTE)
ESTEIRAS_CONFIG = [
    ('sul', Vector((0.0, -1.50, Z_EST)), Vector((0.0, 1.0, 0.0)), 0.65),
    ('oeste', Vector((-1.50, 0.0, Z_EST)), Vector((1.0, 0.0, 0.0)), 0.65)
]

bm_est_guias = bmesh.new()
rolete_objs = []

for nome_e, p_boca, dir_int, comp in ESTEIRAS_CONFIG:
    u_lat = dir_int.cross(Z_VEC).normalized()
    p_fim = p_boca + dir_int * comp
    for sgn in (-1, 1):
        p1 = p_boca + u_lat * (sgn * 0.22)
        p2 = p_fim + u_lat * (sgn * 0.22)
        viga(bm_est_guias, p1 + Vector((0, 0, -0.04)), p2 + Vector((0, 0, -0.04)), 0.035)
        viga(bm_est_guias, p1 + Vector((0, 0, 0.03)), p2 + Vector((0, 0, 0.03)), 0.02)
    for r_i in range(4):
        s = 0.08 + r_i * 0.16
        p_rol = p_boca + dir_int * s
        bm_r = bmesh.new()
        cil(bm_r, (0, 0, 0), 0.032, 0.38, eixo=u_lat, lados=12)
        cil(bm_r, (0, 0, 0), 0.012, 0.44, eixo=u_lat, lados=8)
        r_o = obj(f'rolete_{nome_e}_{r_i}', bm_r, 'cromo')
        r_o.location = p_rol
        suavizar(r_o)
        rolete_objs.append((r_o, u_lat))

obj('esteiras_guias', bm_est_guias, 'titânio')

# Pacotes de ciência em trânsito nas esteiras sul e oeste
bm_pac_s = bmesh.new()
bmesh.ops.create_cube(bm_pac_s, size=0.10)
pacote_transito_s = obj('pacote_transito_s', bm_pac_s, 'pacote_ciencia')

bm_pac_o = bmesh.new()
bmesh.ops.create_cube(bm_pac_o, size=0.10)
pacote_transito_o = obj('pacote_transito_o', bm_pac_o, 'pacote_ciencia')

# ------------------------------------------------------------------ BOCA LESTE DE FLUIDO
p_fluido = Vector((1.50, 0.0, Z_CANO))
bm_tubo_fluido = bmesh.new()
bm_flange_fluido = bmesh.new()

tubo(bm_flange_fluido, p_fluido, p_fluido - Vector((0.08, 0, 0)), 0.085, 16)
tubo(bm_tubo_fluido, p_fluido - Vector((0.08, 0, 0)), p_fluido - Vector((0.35, 0, 0)), 0.055, 16)
p_medidor = p_fluido - Vector((0.48, 0, 0))
caixa_de(bm_flange_fluido, (p_medidor[0] - 0.09, -0.09, Z_CANO - 0.09), (p_medidor[0] + 0.09, 0.09, Z_CANO + 0.09))
cano(bm_tubo_fluido, bm_flange_fluido, [
    (p_medidor[0] - 0.09, 0.0, Z_CANO),
    (p_medidor[0] - 0.25, 0.0, Z_CANO),
    (p_medidor[0] - 0.25, 0.45, Z_CANO),
    (0.45, 0.45, 0.70)
], 0.045, flange=True)

obj('tubo_fluido_leste', bm_tubo_fluido, 'cobre')
obj('flange_fluido_leste', bm_flange_fluido, 'titânio')

# Rotor do medidor de fluxo leste
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

# ------------------------------------------------------------------ TAMBOR CENTRAL DE ESPECTROMETRIA QUÂNTICA
bm_tambor = bmesh.new()
bm_ouro = bmesh.new()
# Vaso esferoidal central
bmesh.ops.create_uvsphere(bm_tambor, u_segments=24, v_segments=16, radius=0.65,
                          matrix=Matrix.Translation((0.0, 0.0, 0.85)))
# Anéis equatoriais e toroidais de supercondução
toro(bm_ouro, (0.0, 0.0, 0.85), 0.68, 0.035, nR=24, nr=8)
toro(bm_ouro, (0.0, 0.0, 1.15), 0.58, 0.028, nR=24, nr=8)

# Colunas de sustentação
for ang_c in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
    p_col = Vector((0.75 * math.cos(ang_c), 0.75 * math.sin(ang_c), Z_LAJE))
    viga(bm_tambor, p_col, p_col + Vector((0, 0, 1.25)), 0.09)

obj('tambor_espectro', bm_tambor, 'titânio')
obj('aneis_tambor_ouro', bm_ouro, 'ouro')

# Carrossel óptico superior girando a 360° em Z
bm_optico = bmesh.new()
toro(bm_optico, (0, 0, 0), 0.42, 0.03, nR=24, nr=8)
# 4 Lentes/prismas lapidados
for k_l in range(4):
    a_l = k_l * PI / 2
    pos_l = Vector((0.42 * math.cos(a_l), 0.42 * math.sin(a_l), 0))
    hexa(bm_optico, (pos_l[0], pos_l[1]), 0.045, -0.06, 0.06, ponta=0.04)

carrossel_optico = obj('carrossel_optico', bm_optico, 'cristal_res')
carrossel_optico.location = Vector((0.0, 0.0, 1.55))
suavizar(carrossel_optico)

# Braço mecatrônico manipulador de pacotes de ciência
bm_braco = bmesh.new()
cil(bm_braco, (0, 0, 0), 0.05, 0.28, lados=12)
tubo(bm_braco, (0, 0, 0.22), (0.28, 0, 0.24), 0.032, 10)
cil(bm_braco, (0.28, 0, 0.24), 0.04, 0.12, lados=10)
tubo(bm_braco, (0.28, 0, 0.24), (0.55, 0, 0.18), 0.025, 8)
caixa_de(bm_braco, (0.50, -0.06, 0.08), (0.60, 0.06, 0.20))

braco_analise = obj('braco_analise', bm_braco, 'titânio')
braco_analise.location = Vector((-0.45, -0.45, Z_EST + 0.06))
suavizar(braco_analise)

# Luz Multiespectral no interior do tambor
luz_esp_data = bpy.data.lights.new('LuzEspectro', 'POINT')
luz_esp_data.color = (0.55, 0.25, 1.0)
luz_esp_data.energy = 160.0
luz_esp_data.shadow_soft_size = 0.20
luz_espectro = bpy.data.objects.new('LuzEspectro', luz_esp_data)
sc.collection.objects.link(luz_espectro)
luz_espectro.location = Vector((0.0, 0.0, 0.85))

# ------------------------------------------------------------------ 4 ENCAIXES DE MÓDULOS QUÂNTICOS (SUDESTE)
bm_mod = bmesh.new()
bm_leds = bmesh.new()
p_baia = Vector((0.95, -0.95, Z_LAJE))
caixa_de(bm_mod, (p_baia[0] - 0.26, p_baia[1] - 0.26, Z_LAJE), (p_baia[0] + 0.26, p_baia[1] + 0.26, Z_LAJE + 0.35))

for m_i, (mx, my) in enumerate(((-0.13, -0.13), (0.13, -0.13), (-0.13, 0.13), (0.13, 0.13))):
    pos_m = p_baia + Vector((mx, my, 0.35))
    caixa_de(bm_mod, (pos_m[0] - 0.075, pos_m[1] - 0.075, pos_m[2]), (pos_m[0] + 0.075, pos_m[1] + 0.075, pos_m[2] + 0.22))
    toro(bm_mod, (pos_m[0], pos_m[1], pos_m[2] + 0.18), 0.065, 0.012, nR=12, nr=6)
    caixa(bm_leds, (pos_m[0], pos_m[1], pos_m[2] + 0.23), (0.02, 0.02, 0.02))

obj('baia_modulos', bm_mod, 'titânio')
obj('leds_modulos', bm_leds, 'led_ciano')

# ------------------------------------------------------------------ RADIADOR CRIOGÊNICO EM V (NOROESTE)
bm_rad = bmesh.new()
p_rad = Vector((-0.95, 0.95, Z_LAJE))
# Suporte do radiador em V
caixa_de(bm_rad, (p_rad[0] - 0.25, p_rad[1] - 0.25, Z_LAJE), (p_rad[0] + 0.25, p_rad[1] + 0.25, Z_LAJE + 0.20))
# Dutos circulares para os ventiladores
casca(bm_rad, (p_rad[0] - 0.14, p_rad[1], 0), 0.15, 0.13, Z_LAJE + 0.20, Z_LAJE + 0.55, n=16)
casca(bm_rad, (p_rad[0] + 0.14, p_rad[1], 0), 0.15, 0.13, Z_LAJE + 0.20, Z_LAJE + 0.55, n=16)
obj('radiador_chassi', bm_rad, 'aco')

# Ventoinhas do radiador em V
ventoinhas_rad = []
for v_i, vx in enumerate((-0.14, 0.14)):
    bm_v = bmesh.new()
    cil(bm_v, (0, 0, 0), 0.035, 0.04, lados=12)
    for p in range(5):
        a_p = p * 2 * PI / 5
        rot_p = Matrix.Rotation(a_p, 3, 'Z')
        bmesh.ops.create_cube(bm_v, size=1.0, matrix=Matrix.Translation((0.07 * math.cos(a_p), 0.07 * math.sin(a_p), 0)) @
                              rot_p.to_4x4() @ Matrix.Rotation(math.radians(25), 3, 'X').to_4x4() @
                              Matrix.Scale(0.06, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.010, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.03, 4, Vector((0, 0, 1))))
    v_o = obj(f'ventoinha_rad{v_i}', bm_v, 'titânio')
    v_o.location = p_rad + Vector((vx, 0.0, Z_LAJE + 0.45))
    suavizar(v_o)
    ventoinhas_rad.append(v_o)

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação dos roletes das esteiras
    ang_rol = t * 8 * PI
    for r_o, u_lat in rolete_objs:
        q_rot = Quaternion(u_lat, ang_rol)
        r_o.rotation_euler = q_rot.to_euler()
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 2. Rotação do fluxômetro de fluido leste
    rotor_fluxo.rotation_euler = Euler((t * 8 * PI, 0, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Rotação do carrossel óptico superior (1 volta = 360°)
    carrossel_optico.rotation_euler = Euler((0, 0, t * 2 * PI), 'XYZ')
    carrossel_optico.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Rotação das ventoinhas do radiador em V
    for v_o in ventoinhas_rad:
        v_o.rotation_euler = Euler((0, 0, t * 12 * PI), 'XYZ')
        v_o.keyframe_insert('rotation_euler', frame=q)
        
    # 5. Oscilação do braço de análise
    ang_braco = math.radians(28.0 * math.sin(t * 2 * PI))
    braco_analise.rotation_euler = Euler((0, 0, ang_braco), 'XYZ')
    braco_analise.keyframe_insert('rotation_euler', frame=q)
    
    # 6. Avanço dos pacotes de ciência nas esteiras
    fase_s = t % 1.0
    y_pac_s = -1.45 + fase_s * 0.75
    pacote_transito_s.location = Vector((0.0, y_pac_s, Z_EST + 0.025))
    pacote_transito_s.keyframe_insert('location', frame=q)
    
    fase_o = (t + 0.5) % 1.0
    x_pac_o = -1.45 + fase_o * 0.75
    pacote_transito_o.location = Vector((x_pac_o, 0.0, Z_EST + 0.025))
    pacote_transito_o.keyframe_insert('location', frame=q)
    
    # 7. Variação multiespectral da luz do tambor
    luz_esp_data.energy = 160.0 + 60.0 * math.sin(t * 8 * PI)
    cor_r = 0.45 + 0.35 * math.sin(t * 2 * PI)
    cor_g = 0.25 + 0.45 * math.cos(t * 2 * PI)
    cor_b = 0.85 + 0.15 * math.sin(t * 4 * PI)
    luz_esp_data.color = (cor_r, cor_g, cor_b)
    luz_esp_data.keyframe_insert('energy', frame=q)
    luz_esp_data.keyframe_insert('color', frame=q)

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
    print(f'LABORATORIO_QUANTICO_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'laboratorio_quantico_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up no tambor espectrométrico, carrossel óptico, braço de análise e baia de 4 módulos
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((1.15, -1.35, 1.35), (0.05, -0.05, 0.85), 36)
    sc.render.filepath = os.path.join(AQUI, 'laboratorio_quantico_perto.png')
    bpy.ops.render.render(write_still=True)

print('LABORATORIO_QUANTICO ok')
