"""Estudo isolado (fora do jogo): MONTADORA 3 da IA, 3×3 tiles (lote 11, produção II).
Tecnologia: 'montadora_3'.
Evolução industrial de Tier 3 da montadora automatizada:
- Velocidade 1,5 (50% mais rápida que a Montadora 2).
- 4 Encaixes de Módulos (em vez de 2 da Montadora 2): baia lateral ampliada a leste com 4 cartuchos
  de módulos encaixados, aletas dissipadoras e LEDs indicadores de barramento ciano.
- Bocas no padrão do jogo:
  * ITEM_ENT_S1: esteira sul de entrada a z = 0,23 m (x = 0,0, y = -1,50 m)
  * ITEM_SAI_N1: esteira norte de saída a z = 0,23 m (x = 0,0, y = +1,50 m)
  * FLUIDO_ENT_O1: tubulação oeste de fluido para solda/lubrificação a z = 0,35 m (x = -1,50 m, y = 0,0)

Engenharia mecatrônica de alta velocidade da IA:
- Base de concreto armado 2,96 × 2,96 m com canaletas de cavacos e esteira central sul-norte contínua.
- Estações internas de montagem em alta cadência:
  1. Dois braços robóticos SCARA paralelos trabalhando em sincronia na alimentação de microcomponentes.
  2. Prensa eletroidráulica dupla com guias cromadas temperadas, amortecedores hidráulicos e travas centradoras.
  3. Duplo cabeçote de solda laser/plasma cruzado com feixes de alta precisão e faíscas dinâmicas.
- Fenômeno da IA: anel focalizador quântico no teto com cristal ressonador emitindo campo de estabilização atômica.
- Sistema de exaustão com ventilador axial potente no topo da coifa e ciclone duplo de filtragem.
- Entrada de fluido oeste com fluxômetro aletado giratório e manômetro analógico.

Peças animadas separadas:
- 'martelo_prensa': prensa eletroidráulica descendo no impacto e retornando velozmente.
- 'braco_scara_1', 'braco_scara_2': dois braços manipuladores articulados operando defasados.
- 'braco_laser_1', 'braco_laser_2': cabeçotes laser oscilando na união de chapas.
- 'anel_quantico': anel focalizador superior girando a 360° em Z.
- 'ventoinha_exaustor': ventilador axial de teto girando a 6 voltas por ciclo.
- 'rotor_fluxo': rotor do fluxômetro de fluido oeste girando a 4 voltas por ciclo.
- 'rolete_s0'..'s3', 'rolete_n0'..'n3': roletes de aço das esteiras girando continuamente.
- 'talisca_0'..'5': taliscas de arraste avançando na esteira central com peças em trânsito.
- 'EFEITO_faisca_0'..'7': centelhas brilhantes de solda laser com decaimento.

Uso: blender -b --python estudo_montadora_3.py -- foto
     blender -b --python estudo_montadora_3.py -- nada
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
Z_EST = 0.23                 # esteira sul-norte
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
    'amarelo_t3': mats.material('AmareloT3', (0.82, 0.55, 0.06), 0.1, 0.40, desgaste=1.2, sujeira=0.85, ferrugem=0.35),
    'azul_petroleo': mats.material('AzulPetroleo', (0.08, 0.28, 0.35), 0.1, 0.38, desgaste=1.0, sujeira=0.75, ferrugem=0.3),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'laser': luz_mat('LaserSolda', (0.2, 0.85, 1.0), 30.0),
    'faisca': luz_mat('FaiscaSolda', (1.0, 0.9, 0.4), 25.0),
    'cristal_ia': luz_mat('CristalIA', (0.4, 0.7, 1.0), 16.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.95, 0.9), 12.0),
    'led_alerta': luz_mat('LedAlerta', (1.0, 0.2, 0.05), 10.0),
})

# ------------------------------------------------------------------ BASE E LAJE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
obj('laje_concreto', bm, 'concreto')

# Placas de base metálicas, calhas e trilhos
bm_aco = bmesh.new()
caixa_de(bm_aco, (-1.35, -1.35, Z_LAJE), (1.35, 1.35, Z_LAJE + 0.02))
# Cantoneiras e sapatas de ancoragem
for cx, cy in ((-1.30, -1.30), (1.30, -1.30), (-1.30, 1.30), (1.30, 1.30)):
    caixa_de(bm_aco, (cx - 0.12, cy - 0.12, Z_LAJE + 0.02), (cx + 0.12, cy + 0.12, Z_LAJE + 0.06))
    hexa(bm_aco, (cx, cy), 0.03, Z_LAJE + 0.06, Z_LAJE + 0.09)

obj('placas_base_aco', bm_aco, 'aco')

# Listras de perigo industrial
bm_listras = bmesh.new()
casca(bm_listras, (0, 0, 0), 1.36, 1.28, Z_LAJE + 0.021, Z_LAJE + 0.023, n=32)
obj('listras_perigo', bm_listras, 'listras')

# ------------------------------------------------------------------ ESTEIRA CENTRAL SUL-NORTE
# Esteira contínua passando pelo centro da máquina a z = 0,23 m
bm_est = bmesh.new()
caixa_de(bm_est, (-0.24, -1.50, Z_EST - 0.04), (0.24, 1.50, Z_EST))
# Guias laterais da esteira
for sgn in (-1, 1):
    viga(bm_est, Vector((sgn * 0.22, -1.50, Z_EST + 0.03)), Vector((sgn * 0.22, 1.50, Z_EST + 0.03)), 0.03)
obj('esteira_chassi', bm_est, 'titânio')

# Roletes giratórios das extremidades sul e norte
rolete_objs = []
for nome_b, y_b, dir_y in (('sul', -1.50, 1.0), ('norte', 1.50, -1.0)):
    for r_i in range(3):
        y_r = y_b + dir_y * (0.08 + r_i * 0.14)
        bm_r = bmesh.new()
        cil(bm_r, (0, 0, 0), 0.032, 0.38, eixo=Vector((1, 0, 0)), lados=12)
        cil(bm_r, (0, 0, 0), 0.012, 0.44, eixo=Vector((1, 0, 0)), lados=8)
        r_o = obj(f'rolete_{nome_b}_{r_i}', bm_r, 'cromo')
        r_o.location = Vector((0.0, y_r, Z_EST - 0.01))
        suavizar(r_o)
        rolete_objs.append(r_o)

# Taliscas de arraste com peças em trânsito
talisca_objs = []
for t_idx in range(6):
    bm_t = bmesh.new()
    caixa_de(bm_t, (-0.18, -0.015, 0), (0.18, 0.015, 0.025))
    # Peça metálica usinada sendo transportada
    caixa_de(bm_t, (-0.10, -0.08, 0.025), (0.10, 0.08, 0.065))
    cil(bm_t, (0, 0, 0.065), 0.04, 0.03, lados=12)
    t_o = obj(f'talisca_{t_idx}', bm_t, 'aluminio')
    suavizar(t_o)
    talisca_objs.append(t_o)

# ------------------------------------------------------------------ BOCA OESTE DE FLUIDO
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
    (p_medidor[0] + 0.25, -0.35, Z_CANO),
    (-0.55, -0.35, 0.50)
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

# ------------------------------------------------------------------ 4 ENCAIXES DE MÓDULOS (FLANCO LESTE)
# Baia de módulos lateral no flanco leste ampliada para 4 módulos (x = +1.15 m)
bm_mod = bmesh.new()
bm_leds = bmesh.new()

caixa_de(bm_mod, (0.95, -0.65, Z_LAJE), (1.35, 0.65, Z_LAJE + 0.45))
for m_i, y_m in enumerate((-0.45, -0.15, 0.15, 0.45)):
    # Cartucho do módulo inserido
    caixa_de(bm_mod, (1.10, y_m - 0.10, Z_LAJE + 0.08), (1.38, y_m + 0.10, Z_LAJE + 0.40))
    # Aletas de refrigeração no módulo
    for dz in (0.15, 0.22, 0.29, 0.36):
        caixa(bm_mod, (1.39, y_m, Z_LAJE + dz), (0.025, 0.18, 0.015))
    # Barra de LEDs ciano indicando atividade do módulo
    for k_led in range(3):
        caixa(bm_leds, (1.37, y_m - 0.05 + k_led * 0.05, Z_LAJE + 0.42), (0.015, 0.025, 0.015))

obj('baia_modulos', bm_mod, 'titânio')
obj('leds_modulos', bm_leds, 'led_ciano')

# ------------------------------------------------------------------ PÓRTICO E CHASSI INDUSTRIAL (AMARELO T3)
bm_portico = bmesh.new()
# 4 Pilares verticais do pórtico principal
for px, py in ((-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
    caixa_de(bm_portico, (px - 0.12, py - 0.12, Z_LAJE), (px + 0.12, py + 0.12, 1.85))
    # Reforços diagonais
    viga(bm_portico, Vector((px, py, 0.40)), Vector((px * 0.4, py, 1.80)), 0.08)

# Vigas superiores em caixão do pórtico
viga(bm_portico, (-0.85, -0.85, 1.80), (0.85, -0.85, 1.80), 0.16)
viga(bm_portico, (-0.85, 0.85, 1.80), (0.85, 0.85, 1.80), 0.16)
viga(bm_portico, (-0.85, -0.85, 1.80), (-0.85, 0.85, 1.80), 0.16)
viga(bm_portico, (0.85, -0.85, 1.80), (0.85, 0.85, 1.80), 0.16)

# Carcaças laterais protetoras da montadora em amarelo industrial T3
caixa_de(bm_portico, (-0.95, -0.85, Z_LAJE + 0.10), (-0.75, 0.85, 1.65))
obj('portico_montadora', bm_portico, 'amarelo_t3')

# ------------------------------------------------------------------ DOIS BRAÇOS SCARA PARALELOS
# Braço SCARA 1 (sul-oeste, alimenta carcaças)
bm_scara1 = bmesh.new()
cil(bm_scara1, (0, 0, 0), 0.065, 0.35, lados=12)
tubo(bm_scara1, (0, 0, 0.28), (0.35, 0, 0.30), 0.04, 10)
cil(bm_scara1, (0.35, 0, 0.30), 0.05, 0.20, lados=10)
tubo(bm_scara1, (0.35, 0, 0.30), (0.65, 0, 0.22), 0.032, 8)
caixa_de(bm_scara1, (0.62, -0.06, 0.12), (0.72, 0.06, 0.24))

braco_scara_1 = obj('braco_scara_1', bm_scara1, 'azul_petroleo')
braco_scara_1.location = Vector((-0.55, -0.55, 0.45))
suavizar(braco_scara_1)

# Braço SCARA 2 (sul-leste, insere componentes)
bm_scara2 = bmesh.new()
cil(bm_scara2, (0, 0, 0), 0.065, 0.35, lados=12)
tubo(bm_scara2, (0, 0, 0.28), (0.35, 0, 0.30), 0.04, 10)
cil(bm_scara2, (0.35, 0, 0.30), 0.05, 0.20, lados=10)
tubo(bm_scara2, (0.35, 0, 0.30), (0.65, 0, 0.22), 0.032, 8)
caixa_de(bm_scara2, (0.62, -0.06, 0.12), (0.72, 0.06, 0.24))

braco_scara_2 = obj('braco_scara_2', bm_scara2, 'azul_petroleo')
braco_scara_2.location = Vector((0.55, -0.45, 0.45))
suavizar(braco_scara_2)

# ------------------------------------------------------------------ PRENSA ELETROIDRÁULICA DUPLA
bm_prensa = bmesh.new()
# Pistões cromados duplos verticais
for px in (-0.14, 0.14):
    cil(bm_prensa, (px, 0, 0.40), 0.055, 0.60, lados=14)
# Bloco martelo da prensa com ranhuras e cunhas de estampagem
caixa_de(bm_prensa, (-0.22, -0.16, 0.0), (0.22, 0.16, 0.20))
caixa_de(bm_prensa, (-0.18, -0.12, -0.04), (0.18, 0.12, 0.0))

martelo_prensa = obj('martelo_prensa', bm_prensa, 'cromo')
martelo_prensa.location = Vector((0.0, 0.0, 0.95))
suavizar(martelo_prensa)

# ------------------------------------------------------------------ DOIS CABEÇOTES DE SOLDA LASER
# Braços laser posicionados a norte (y = 0.45 m)
bm_laser1 = bmesh.new()
tubo(bm_laser1, (0, 0, 0), (0.24, 0.15, -0.15), 0.028, 8)
cil(bm_laser1, (0.24, 0.15, -0.15), 0.04, 0.10, lados=10)
bmesh.ops.create_cone(bm_laser1, cap_ends=True, segments=8, radius1=0.03, radius2=0.008, depth=0.08,
                      matrix=Matrix.Translation((0.24, 0.15, -0.22)))

braco_laser_1 = obj('braco_laser_1', bm_laser1, 'titânio')
braco_laser_1.location = Vector((-0.35, 0.42, 0.85))
suavizar(braco_laser_1)

bm_laser2 = bmesh.new()
tubo(bm_laser2, (0, 0, 0), (-0.24, 0.15, -0.15), 0.028, 8)
cil(bm_laser2, (-0.24, 0.15, -0.15), 0.04, 0.10, lados=10)
bmesh.ops.create_cone(bm_laser2, cap_ends=True, segments=8, radius1=0.03, radius2=0.008, depth=0.08,
                      matrix=Matrix.Translation((-0.24, 0.15, -0.22)))

braco_laser_2 = obj('braco_laser_2', bm_laser2, 'titânio')
braco_laser_2.location = Vector((0.35, 0.42, 0.85))
suavizar(braco_laser_2)

# Luz do Laser de Solda
luz_laser_data = bpy.data.lights.new('LuzLaser', 'POINT')
luz_laser_data.color = (0.25, 0.85, 1.0)
luz_laser_data.energy = 120.0
luz_laser_data.shadow_soft_size = 0.12
luz_laser = bpy.data.objects.new('LuzLaser', luz_laser_data)
sc.collection.objects.link(luz_laser)
luz_laser.location = Vector((0.0, 0.52, 0.32))

# ------------------------------------------------------------------ ANEL FOCALIZADOR QUÂNTICO E EXAUSTÃO
# Anel magnético toroidal superior girando no teto do pórtico (z = 1.95 m)
bm_anel = bmesh.new()
toro(bm_anel, (0, 0, 0), 0.55, 0.035, nR=28, nr=10)
for k in range(6):
    ang_k = k * 2 * PI / 6
    pos_k = Vector((0.55 * math.cos(ang_k), 0.55 * math.sin(ang_k), 0))
    toro(bm_anel, pos_k, 0.05, 0.014, nR=12, nr=6)

anel_quantico = obj('anel_quantico', bm_anel, 'cobre')
anel_quantico.location = Vector((0.0, 0.0, 1.95))
suavizar(anel_quantico)

# Cristal focalizador central da IA
bm_c_ia = bmesh.new()
hexa(bm_c_ia, (0, 0), 0.065, -0.12, 0.12, ponta=0.06)
cristal_ia = obj('cristal_ia', bm_c_ia, 'cristal_ia', pai=anel_quantico)
cristal_ia.location = Vector((0, 0, 0))

# Coifa de exaustão superior com duto para o ciclone traseiro
bm_coifa = bmesh.new()
bmesh.ops.create_cone(bm_coifa, cap_ends=False, segments=16, radius1=0.45, radius2=0.20, depth=0.35,
                      matrix=Matrix.Translation((0.0, 0.0, 2.15)))
obj('coifa_topo', bm_coifa, 'aco')

# Ventoinha axial de teto na coifa
bm_vent = bmesh.new()
cil(bm_vent, (0, 0, 0), 0.04, 0.05, lados=12)
for p in range(5):
    ang_p = p * 2 * PI / 5
    rot_p = Matrix.Rotation(ang_p, 3, 'Z')
    bmesh.ops.create_cube(bm_vent, size=1.0, matrix=Matrix.Translation((0.09 * math.cos(ang_p), 0.09 * math.sin(ang_p), 0)) @
                          rot_p.to_4x4() @ Matrix.Rotation(math.radians(30), 3, 'X').to_4x4() @
                          Matrix.Scale(0.08, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.012, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.035, 4, Vector((0, 0, 1))))

ventoinha_exaustor = obj('ventoinha_exaustor', bm_vent, 'titânio')
ventoinha_exaustor.location = Vector((0.0, 0.0, 2.30))
suavizar(ventoinha_exaustor)

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação dos roletes das esteiras
    ang_rol = t * 8 * PI
    for r_o in rolete_objs:
        r_o.rotation_euler = Euler((ang_rol, 0, 0), 'XYZ')
        r_o.keyframe_insert('rotation_euler', frame=q)
        
    # 2. Rotação do fluxômetro de fluido oeste
    rotor_fluxo.rotation_euler = Euler((t * 8 * PI, 0, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Rotação do anel focalizador quântico (1 volta = 360°)
    anel_quantico.rotation_euler = Euler((0, 0, t * 2 * PI), 'XYZ')
    anel_quantico.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Rotação rápida do ventilador de exaustão (6 voltas por ciclo)
    ventoinha_exaustor.rotation_euler = Euler((0, 0, t * 12 * PI), 'XYZ')
    ventoinha_exaustor.keyframe_insert('rotation_euler', frame=q)
    
    # 5. Avanço das taliscas na esteira sul-norte
    for t_i, t_o in enumerate(talisca_objs):
        fase_t = (t + t_i / 6.0) % 1.0
        y_tal = -1.45 + fase_t * 2.90
        t_o.location = Vector((0.0, y_tal, Z_EST))
        t_o.keyframe_insert('location', frame=q)
        
    # 6. Ciclo da prensa eletroidráulica (dupla prensagem veloz: 2 impactos por ciclo)
    # Ciclo harmônico com 2 impactos: descida rápida no impacto e recuo amortecido
    t_prensa = (t * 2) % 1.0
    if t_prensa < 0.35:
        s_d = t_prensa / 0.35
        z_p = 0.95 - 0.45 * (s_d ** 2)
    elif t_prensa < 0.50:
        z_p = 0.50 # impacto
    else:
        s_u = (t_prensa - 0.50) / 0.50
        z_p = 0.50 + 0.45 * math.sin(s_u * PI / 2)
        
    martelo_prensa.location = Vector((0.0, 0.0, z_p))
    martelo_prensa.keyframe_insert('location', frame=q)
    
    # 7. Braços SCARA operando em alta cadência defasados
    ang_sc1 = math.radians(35.0 * math.sin(t * 4 * PI))
    ang_sc2 = math.radians(-35.0 * math.cos(t * 4 * PI))
    braco_scara_1.rotation_euler = Euler((0, 0, ang_sc1), 'XYZ')
    braco_scara_2.rotation_euler = Euler((0, 0, ang_sc2), 'XYZ')
    braco_scara_1.keyframe_insert('rotation_euler', frame=q)
    braco_scara_2.keyframe_insert('rotation_euler', frame=q)
    
    # 8. Braços de solda laser oscilando na área de solda
    ang_las1 = math.radians(12.0 * math.sin(t * 8 * PI))
    ang_las2 = math.radians(-12.0 * math.sin(t * 8 * PI + PI / 4))
    braco_laser_1.rotation_euler = Euler((ang_las1, 0, 0), 'XYZ')
    braco_laser_2.rotation_euler = Euler((ang_las2, 0, 0), 'XYZ')
    braco_laser_1.keyframe_insert('rotation_euler', frame=q)
    braco_laser_2.keyframe_insert('rotation_euler', frame=q)
    
    # 9. Luz pulsante de solda laser
    int_laser = 120.0 + 80.0 * math.sin(t * 16 * PI)
    luz_laser_data.energy = max(10.0, int_laser)
    luz_laser_data.keyframe_insert('energy', frame=q)

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
    print(f'MONTADORA_3_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'montadora_3_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na prensa, braços SCARA duplos, cabeçotes laser e esteira
    sc.frame_set(int(0.45 * FPS) + 1)
    mirar((0.35, -1.25, 0.95), (0.0, -0.10, 0.45), 38)
    sc.render.filepath = os.path.join(AQUI, 'montadora_3_perto.png')
    bpy.ops.render.render(write_still=True)

print('MONTADORA_3 ok')
