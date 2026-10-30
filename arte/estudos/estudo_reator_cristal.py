"""Estudo isolado (fora do jogo): REATOR DE CRISTAL da IA, 3×3 tiles (lote 14, energia II).
Potência nominal: 8 MW. Consome células de energia ou cristais carregados via esteira com refrigeração líquida.
Bocas no padrão do jogo:
- ITEM_ENT_S1: esteira sul de células de energia / cristais carregados (x = 0,0, y = -1,50 m, z = 0,23 m)
- ITEM_SAI_N1: esteira norte de ejeção de matrizes descarregadas (x = 0,0, y = +1,50 m, z = 0,23 m)
- FLUIDO_ENT_O1: tubulação oeste de fluido refrigerante a z = 0,35 m (x = -1,50 m, y = 0,0)

Engenharia nuclear-ressonante da IA:
- Base maciça de concreto armado 2,96 × 2,96 m com drenos de emergência, canaletas e piso com demarcação zebrada.
- Vaso de reação central octogonal blindado em chumbo e aço escovado, com 6 cintas de aperto com parafusos tensores,
  visores de quartzo com câmara incandescente e anéis de contenção magnética toroidal supercondutores em cobre.
- Núcleo de ressonância no interior: cristal de tempestade colossal lapidado suspenso em campo magnético emitindo
  plasma violeta brilhante com iluminação volumétrica pulsante.
- Mecanismo de barras de controle superiores: 4 colunas verticais com atuadores hidráulicos cromados regulando
  o fluxo de nêutrons/fótons no núcleo de reação.
- Câmara de alimentação sul: eclusa de inserção pneumática blindada com braço robótico injetor e esteira de roletes.
- Ejeção norte: bica inclinada com comportas térmicas descarregando cartuchos gastos na esteira de roletes norte.
- Circuito de refrigeração oeste: bocal flangeado rígido a 0,35 m com medidor de vazão de rotor giratório,
  bomba centrífuga de alta pressão e tubos com aletas térmicas envolvendo a carcaça do reator.
- Cúpula de teto: anel toroidal de polarização de campo giratório contínuo a 360° em Z e chaminé com anéis dissipadores.

Peças animadas separadas:
- 'anel_polarizacao': anel toroidal superior girando continuamente a 360° em Z.
- 'barras_controle': atuadores e barras verticais de controle oscilando suavemente em Z.
- 'injetor_combustivel': êmbolo do injetor inserindo cápsula na câmara de fusão do cristal.
- 'rotor_fluxo': rotor do medidor de fluxo de refrigerante oeste girando a 4 voltas por ciclo.
- 'cristal_nucleo': núcleo de cristal central girando e emitindo pulso de plasma violento.
- 'rolete_s0'..'s3', 'rolete_n0'..'n3': roletes das esteiras sul e norte girando sincronizados.

Uso: blender -b --python estudo_reator_cristal.py -- foto
     blender -b --python estudo_reator_cristal.py -- nada
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
C = Vector((0.0, 0.0, 0.0))           # centro do vaso de reação
AP = 0.68                             # apótema do reator octogonal
RV = AP / math.cos(PI / 8)             # raio dos vértices
Z_LAJE = 0.08
Z_PED = 0.20
Z_VASO_BASE = 0.22
Z_VASO_TOPO = 1.45
Z_CUPULA = 1.62
Z_EST = 0.23                          # altura da esteira de itens (bocas sul e norte)
Z_CANO = 0.35                         # altura do tubo de fluido (boca oeste)

# ------------------------------------------------------------------ utilidades de forma
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

def toro(bm, centro, R, r, nR=32, nr=10, rot=Matrix.Identity(3)):
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

def vidro_mat():
    m = bpy.data.materials.new('VidroReator')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.70, 0.82, 0.95, 1)
    b.inputs['Transmission Weight'].default_value = 0.95
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['Alpha'].default_value = 0.35
    b.inputs['IOR'].default_value = 1.54
    return m

def cristal_mat(nome, cor, forca=8.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Transmission Weight'].default_value = 0.7
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['IOR'].default_value = 1.68
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

base3d.M.update({
    'chumbo': mats.material('ChumboBlindado', (0.18, 0.19, 0.20), 0.3, 0.6, pintura=False, sujeira=0.8),
    'aco': mats.material('AçoEstrutural', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('CromoHaste', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('CobreBobinas', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'bronze': mats.material('BronzeBomba', (0.55, 0.38, 0.18), 1.0, 0.35, pintura=False, sujeira=0.7),
    'ouro': mats.material('OuroConector', (0.88, 0.72, 0.16), 1.0, 0.18, pintura=False, sujeira=0.2),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'vidro': vidro_mat(),
    'cristal_nucleo': cristal_mat('CristalNucleo', (0.55, 0.15, 1.0), 10.0),
    'plasma_reacao': luz_mat('PlasmaReacao', (0.4, 0.8, 1.0), 30.0),
    'campo': luz_mat('CampoPolarizacao', (0.6, 0.2, 1.0), 8.0),
    'led_verde': luz_mat('LedStatus', (0.1, 0.95, 0.2), 10.0),
})

# ------------------------------------------------------------------ LAJE E BASE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
# Drenos de recirculação e bacias de contenção
caixa_de(bm, (-1.35, -1.35, 0.07), (1.35, -1.30, 0.081))
caixa_de(bm, (-1.35, 1.30, 0.07), (1.35, 1.35, 0.081))
# Pedestal central octogonal
cil(bm, Vector((0, 0, (Z_LAJE + Z_PED) / 2)), 0.82, Z_PED - Z_LAJE, lados=8)
obj('laje_concreto', bm, 'concreto')

# Demarcações de segurança listradas
bm = bmesh.new()
for x in (-0.26, 0.26):
    caixa_de(bm, (x - 0.025, -1.48, 0.08), (x + 0.025, -0.75, 0.082))
    caixa_de(bm, (x - 0.025, 0.75, 0.08), (x + 0.025, 1.48, 0.082))
for y in (-0.26, 0.26):
    caixa_de(bm, (-1.48, y - 0.025, 0.08), (-0.75, y + 0.025, 0.082))
obj('faixas_seguranca', bm, 'listras')

# ------------------------------------------------------------------ VASO DE REAÇÃO OCTOGONAL BLINDADO
bm, bmg, bmv = bmesh.new(), bmesh.new(), bmesh.new()

# Paredes do vaso de pressão em chumbo blindado
cil(bm, Vector((0, 0, (Z_VASO_BASE + Z_VASO_TOPO) / 2)), AP, Z_VASO_TOPO - Z_VASO_BASE, lados=8)
# Beiral inferior e superior reforçados
cil(bmg, Vector((0, 0, Z_VASO_BASE + 0.04)), RV + 0.02, 0.08, lados=8)
cil(bmg, Vector((0, 0, Z_VASO_TOPO - 0.04)), RV + 0.02, 0.08, lados=8)

# 6 cintas maciças de aperto com parafusos tensores em aço
for iz in range(6):
    z_cinta = Z_VASO_BASE + 0.16 + iz * 0.18
    casca(bmg, (0, 0, 0), RV + 0.015, AP + 0.005, z_cinta - 0.02, z_cinta + 0.02, 16)
    # Parafusos nas cintas
    for a in range(8):
        ang = a * PI / 4
        d_p = Vector((math.cos(ang), math.sin(ang), 0))
        cil(bmg, d_p * (RV + 0.025) + Vector((0, 0, z_cinta)), 0.014, 0.03, d_p, lados=6)

# Janelas de quartzo espesso com molduras parafusadas nas faces diagonais
for ang in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
    rot_j = Matrix.Rotation(ang, 3, 'Z')
    d_j = Vector((math.cos(ang), math.sin(ang), 0))
    p_j = d_j * AP + Vector((0, 0, 0.85))
    # Vidro de quartzo translúcido
    caixa(bmv, p_j, (0.02, 0.28, 0.45), rot_j)
    # Moldura de aço com grade
    caixa(bmg, p_j + d_j * 0.015, (0.035, 0.32, 0.49), rot_j)
    for jz in range(3):
        z_gr = 0.70 + jz * 0.15
        tubo(bmg, p_j + rot_j @ Vector((0, -0.14, z_gr - 0.85)),
                  p_j + rot_j @ Vector((0,  0.14, z_gr - 0.85)), 0.005, 6)

# Bobinas eletromagnéticas supercondutoras toroidais em cobre envolvendo o vaso
for z_bob in (0.45, 0.85, 1.25):
    toro(bmg, Vector((0, 0, z_bob)), RV + 0.04, 0.025, nR=32, nr=10)

obj('vaso_chumbo', bm, 'chumbo')
obj('vaso_reforcos_aco', bmg, 'aco')
obj('vaso_janelas_quartzo', bmv, 'vidro')

# ------------------------------------------------------------------ INTERIOR DO REATOR: NÚCLEO E PLASMA
bm_cristal = bmesh.new()
# Cristal de tempestade central monumental lapidado
cristal_nuc = bpy.data.objects.new('cristal_nucleo', None)
sc.collection.objects.link(cristal_nuc)
cristal_nuc.location = Vector((0, 0, 0.85))
# Hexágono de cristal facetado com pontas piramidais duplas
hexa(bm_cristal, Vector((0, 0, 0)), 0.16, -0.30, 0.30, ponta=0.20)
bmesh.ops.create_cone(bm_cristal, cap_ends=True, segments=6, radius1=0.16, radius2=0.0, depth=0.20,
                      matrix=Matrix.Translation((0, 0, -0.30 - 0.10)) @ Matrix.Rotation(PI, 3, 'X').to_4x4())
obj('cristal_nucleo_mesh', bm_cristal, 'cristal_nucleo', cristal_nuc)

# Anel de indução de ouro segurando o cristal no vácuo
bm_anel_ind = bmesh.new()
toro(bm_anel_ind, Vector((0, 0, 0.85)), 0.24, 0.02, nR=24, nr=8)
for a in range(4):
    ang = a * PI / 2
    d_g = Vector((math.cos(ang), math.sin(ang), 0))
    tubo(bm_anel_ind, Vector((0, 0, 0.85)) + d_g * 0.24, Vector((0, 0, 0.85)) + d_g * 0.16, 0.015, 8)
obj('anel_inducao_ouro', bm_anel_ind, 'ouro')

# Luz pontual de plasma da reação violenta
luz_plasma_data = bpy.data.lights.new('LuzPlasmaReator', 'POINT')
luz_plasma_data.energy = 120.0
luz_plasma_data.color = (0.4, 0.7, 1.0)
luz_plasma_data.shadow_soft_size = 0.10
luz_plasma_obj = bpy.data.objects.new('EFEITO_LuzPlasma', luz_plasma_data)
sc.collection.objects.link(luz_plasma_obj)
luz_plasma_obj.location = Vector((0, 0, 0.85))

# ------------------------------------------------------------------ BARRAS DE CONTROLE SUPERIORES
barras_ctrl = bpy.data.objects.new('barras_controle', None)
sc.collection.objects.link(barras_ctrl)
barras_ctrl.location = Vector((0, 0, Z_VASO_TOPO))

bm_barras, bm_hastes = bmesh.new(), bmesh.new()
# Prato superior de acoplamento
cil(bm_barras, Vector((0, 0, 0.04)), 0.42, 0.06, Z_VEC, lados=16)
# 4 atuadores verticais telescópicos cromados
for a in range(4):
    ang = a * PI / 2 + PI / 4
    d_b = Vector((math.cos(ang), math.sin(ang), 0))
    p_b = d_b * 0.25
    # Camisa do atuador
    tubo(bm_barras, p_b + Vector((0, 0, 0.06)), p_b + Vector((0, 0, 0.42)), 0.028, 12)
    # Haste cromada penetrando no vaso
    tubo(bm_hastes, p_b + Vector((0, 0, -0.65)), p_b + Vector((0, 0, 0.10)), 0.016, 12)
    # Mangueira hidráulica de controle
    mangueira(bm_barras, [p_b + Vector((0, 0, 0.40)), p_b + d_b * 0.08 + Vector((0, 0, 0.45)),
                          Vector((0, 0, 0.48))], 0.006)

obj('barras_controle_mecanismo', bm_barras, 'grafite', barras_ctrl)
obj('barras_controle_hastes', bm_hastes, 'cromo', barras_ctrl)

# ------------------------------------------------------------------ TETO: CÚPULA DE POLARIZAÇÃO E ANEL TOROIDAL
bm_cup = bmesh.new()
# Cúpula de confinamento de plasma
bmesh.ops.create_cone(bm_cup, cap_ends=True, segments=18, radius1=0.48, radius2=0.22, depth=0.25,
                      matrix=Matrix.Translation((0, 0, Z_VASO_TOPO + 0.14)))
# Chaminé central de alívio térmico com anéis dissipadores
tubo(bm_cup, Vector((0, 0, Z_VASO_TOPO + 0.26)), Vector((0, 0, Z_VASO_TOPO + 0.75)), 0.09, 16)
for iz in range(4):
    tubo(bm_cup, Vector((0, 0, Z_VASO_TOPO + 0.38 + iz * 0.09)),
                 Vector((0, 0, Z_VASO_TOPO + 0.42 + iz * 0.09)), 0.12, 16)
obj('cupula_teto', bm_cup, 'chumbo')

# Anel toroidal de polarização de campo giratório contínuo a 360°
anel_pol = bpy.data.objects.new('anel_polarizacao', None)
sc.collection.objects.link(anel_pol)
anel_pol.location = Vector((0, 0, Z_VASO_TOPO + 0.35))
bm_ap = bmesh.new()
toro(bm_ap, Vector((0, 0, 0)), 0.38, 0.028, nR=28, nr=8)
for a in range(6):
    ang = a * 2 * PI / 6
    d_a = Vector((math.cos(ang), math.sin(ang), 0))
    cil(bm_ap, d_a * 0.38, 0.035, 0.05, Z_VEC, lados=8)
obj('anel_polarizacao_mesh', bm_ap, 'campo', anel_pol)

# ------------------------------------------------------------------ BOCA SUL (ITEM_ENT_S1): Esteira e injetor
# Boca a x = 0.0, y = -1.50 m, z = 0.23 m
bm_es, bm_calhas = bmesh.new(), bmesh.new()
caixa_de(bm_calhas, (-0.24, -1.50, 0.08), (-0.20, -0.65, Z_EST + 0.04))
caixa_de(bm_calhas, (0.20, -1.50, 0.08), (0.24, -0.65, Z_EST + 0.04))
# Eclusa hermética de injeção na face sul
caixa_de(bm_calhas, (-0.28, -0.75, Z_EST - 0.05), (0.28, -0.45, 0.65))

# Roletes da esteira sul
roletes_s = []
for i in range(4):
    y_r = -1.40 + i * 0.22
    r_obj = bpy.data.objects.new(f'rolete_s{i}', None)
    sc.collection.objects.link(r_obj)
    r_obj.location = Vector((0, y_r, Z_EST))
    bm_r = bmesh.new()
    cil(bm_r, Vector((0, 0, 0)), 0.022, 0.38, Vector((1, 0, 0)), lados=14)
    obj(f'rolete_s{i}_mesh', bm_r, 'aco', r_obj)
    roletes_s.append(r_obj)
obj('esteira_sul_calhas', bm_calhas, 'grafite')

# Célula de combustível em trânsito pela esteira sul
celula_combustivel = bpy.data.objects.new('celula_combustivel', None)
sc.collection.objects.link(celula_combustivel)
bm_cel = bmesh.new()
cil(bm_cel, Vector((0, 0, 0.035)), 0.045, 0.07, Vector((0, 1, 0)), lados=14)
hexa(bm_cel, Vector((0, 0, 0.035)), 0.035, -0.05, 0.05)
obj('celula_combustivel_mesh', bm_cel, 'cristal_nucleo', celula_combustivel)

# Êmbolo injetor de combustível pneumático
injetor = bpy.data.objects.new('injetor_combustivel', None)
sc.collection.objects.link(injetor)
injetor.location = Vector((0, -0.70, Z_EST + 0.05))
bm_inj = bmesh.new()
tubo(bm_inj, Vector((0, -0.15, 0)), Vector((0, 0.15, 0)), 0.035, 12)
cil(bm_inj, Vector((0, 0.15, 0)), 0.05, 0.02, Vector((0, 1, 0)), lados=12)
obj('injetor_embolo', bm_inj, 'cromo', injetor)

# ------------------------------------------------------------------ BOCA NORTE (ITEM_SAI_N1): Esteira de descarte
# Boca a x = 0.0, y = +1.50 m, z = 0.23 m
bm_calhas_n = bmesh.new()
caixa_de(bm_calhas_n, (-0.24, 0.65, 0.08), (-0.20, 1.50, Z_EST + 0.04))
caixa_de(bm_calhas_n, (0.20, 0.65, 0.08), (0.24, 1.50, Z_EST + 0.04))
# Bica inclinada saindo da face norte
caixa_de(bm_calhas_n, (-0.26, 0.45, Z_EST - 0.02), (0.26, 0.72, 0.55))

# Roletes da esteira norte
roletes_n = []
for i in range(4):
    y_rn = 0.75 + i * 0.22
    r_obj = bpy.data.objects.new(f'rolete_n{i}', None)
    sc.collection.objects.link(r_obj)
    r_obj.location = Vector((0, y_rn, Z_EST))
    bm_rn = bmesh.new()
    cil(bm_rn, Vector((0, 0, 0)), 0.022, 0.38, Vector((1, 0, 0)), lados=14)
    obj(f'rolete_n{i}_mesh', bm_rn, 'aco', r_obj)
    roletes_n.append(r_obj)
obj('esteira_norte_calhas', bm_calhas_n, 'grafite')

# Cartucho descarregado saindo pela esteira norte
cartucho_gasto = bpy.data.objects.new('cartucho_gasto', None)
sc.collection.objects.link(cartucho_gasto)
bm_cg = bmesh.new()
cil(bm_cg, Vector((0, 0, 0.03)), 0.045, 0.06, Vector((0, 1, 0)), lados=12)
obj('cartucho_gasto_mesh', bm_cg, 'chumbo', cartucho_gasto)

# ------------------------------------------------------------------ BOCA OESTE (FLUIDO_ENT_O1): Refrigeração líquida
# Boca a x = -1.50 m, y = 0.0 m, z = 0.35 m
bm_tubo_o, bf_o = bmesh.new(), bmesh.new()
# Flange rígido de encaixe faceando -1.50 m
tubo(bf_o, Vector((-1.50, 0, Z_CANO)), Vector((-1.44, 0, Z_CANO)), 0.075, 16)
tubo(bm_tubo_o, Vector((-1.44, 0, Z_CANO)), Vector((-1.05, 0, Z_CANO)), 0.045, 16)

# Medidor de vazão com visor circular de vidro
cil(bm_tubo_o, Vector((-1.25, 0, Z_CANO)), 0.07, 0.06, Vector((0, 1, 0)), lados=16)
cil(bf_o, Vector((-1.25, 0.032, Z_CANO)), 0.055, 0.008, Vector((0, 1, 0)), lados=16) # aro latão

# Rotor giratório do fluxômetro
rotor_fluxo = bpy.data.objects.new('rotor_fluxo', None)
sc.collection.objects.link(rotor_fluxo)
rotor_fluxo.location = Vector((-1.25, 0.025, Z_CANO))
bm_rf = bmesh.new()
cil(bm_rf, Vector((0, 0, 0)), 0.015, 0.012, Vector((0, 1, 0)), lados=8)
for ang in (0, PI/2, PI, 3*PI/2):
    rot_p = Matrix.Rotation(ang, 3, 'Y')
    caixa(bm_rf, rot_p @ Vector((0.028, 0, 0)), (0.026, 0.006, 0.004), rot_p)
obj('rotor_fluxo_pas', bm_rf, 'bronze', rotor_fluxo)

# Bomba centrífuga de circulação forçada e tubos contornando o reator
cil(bm_tubo_o, Vector((-0.85, 0.35, 0.30)), 0.12, 0.16, Vector((0, 0, 1)), lados=16)
cano(bm_tubo_o, bf_o, [Vector((-1.05, 0, Z_CANO)), Vector((-0.85, 0, Z_CANO)),
                       Vector((-0.85, 0.35, Z_CANO)), Vector((-0.60, 0.35, 0.65))], 0.038)
obj('tubulacao_refrig_corpo', bm_tubo_o, 'aco')
obj('tubulacao_refrig_flanges', bf_o, 'latao')

# ------------------------------------------------------------------ BANCO DE CAPACITORES E SUBESTAÇÃO (Sudeste)
X_SUB, Y_SUB = 0.85, -0.85
bm_sub, bm_cob = bmesh.new(), bmesh.new()
caixa_de(bm_sub, (X_SUB - 0.35, Y_SUB - 0.35, Z_LAJE), (X_SUB + 0.35, Y_SUB + 0.35, 0.60))
# Isoladores cerâmicos e barramentos maciços para a rede
for dx in (-0.15, 0.0, 0.15):
    for iz in range(3):
        cil(bm_sub, Vector((X_SUB + dx, Y_SUB, 0.63 + iz * 0.04)), 0.035 - iz * 0.005, 0.03, lados=12)
    tubo(bm_cob, Vector((X_SUB + dx, Y_SUB, 0.75)), Vector((X_SUB + dx * 0.4, Y_SUB + 0.30, 0.75)), 0.014, 10)
# Faixas zebradas no painel
caixa_de(bm_sub, (X_SUB - 0.36, Y_SUB - 0.36, 0.08), (X_SUB + 0.36, Y_SUB - 0.34, 0.12))
obj('subestacao_gabinete', bm_sub, 'grafite')
obj('subestacao_cobre', bm_cob, 'cobre')

# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço fechado a 24 fps)
em_cristal = base3d.M['cristal_nucleo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_plasma = base3d.M['plasma_reacao'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']

for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS                     # progresso 0..1 do ciclo
    fase = 2 * PI * t
    
    # 1. Anel toroidal superior de polarização: rotação contínua e suave de 360° em Z
    anel_pol.rotation_euler = Euler((0, 0, -fase), 'XYZ')
    anel_pol.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Barras de controle: oscilação harmônica milimétrica regulando a reação
    z_barras = 0.06 * math.sin(fase * 2)
    barras_ctrl.location = Vector((0, 0, Z_VASO_TOPO + z_barras))
    barras_ctrl.keyframe_insert('location', frame=q)
    
    # 3. Cristal central do núcleo: rotação lenta e pulso harmônico de plasma
    cristal_nuc.rotation_euler = Euler((0.05 * math.sin(fase), 0.05 * math.cos(fase), fase * 0.5), 'XYZ')
    pulso_cr = 0.5 + 0.5 * math.sin(fase * 4)
    cristal_nuc.scale = Vector((1.0 + 0.06 * pulso_cr, 1.0 + 0.06 * pulso_cr, 1.0 + 0.08 * pulso_cr))
    cristal_nuc.keyframe_insert('rotation_euler', frame=q)
    cristal_nuc.keyframe_insert('scale', frame=q)
    
    # Brilho do cristal e do plasma interno
    em_cristal.default_value = 8.0 + 12.0 * pulso_cr
    em_plasma.default_value = 25.0 + 20.0 * pulso_cr
    em_cristal.keyframe_insert('default_value', frame=q)
    em_plasma.keyframe_insert('default_value', frame=q)
    luz_plasma_data.energy = 90.0 + 60.0 * pulso_cr
    luz_plasma_data.keyframe_insert('energy', frame=q)
    
    # 4. Rotor do fluxômetro de fluido oeste: 4 voltas por ciclo
    rotor_fluxo.rotation_euler = Euler((0, fase * 4, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 5. Roletes das esteiras sul e norte girando continuamente
    for r_obj in roletes_s:
        r_obj.rotation_euler = Euler((fase * 3, 0, 0), 'XYZ')
        r_obj.keyframe_insert('rotation_euler', frame=q)
    for r_obj in roletes_n:
        r_obj.rotation_euler = Euler((fase * 3, 0, 0), 'XYZ')
        r_obj.keyframe_insert('rotation_euler', frame=q)
        
    # 6. Injeção de célula de combustível pela esteira sul
    # Avança pela esteira de y=-1.45 até -0.75 (t=0..0.50), depois entra no vaso (t=0.50..0.75)
    if t < 0.50:
        s_c = t / 0.50
        y_cel = -1.45 + s_c * 0.70
        celula_combustivel.location = Vector((0.0, y_cel, Z_EST + 0.025))
        celula_combustivel.scale = Vector((1.0, 1.0, 1.0))
    elif t < 0.75:
        s_c = (t - 0.50) / 0.25
        y_cel = -0.75 + s_c * 0.45
        celula_combustivel.location = Vector((0.0, y_cel, Z_EST + 0.025))
        celula_combustivel.scale = Vector((1.0, 1.0, 1.0))
    else:
        # Fundindo no núcleo
        s_c = (t - 0.75) / 0.25
        esc_c = max(0.001, 1.0 - s_c * 0.98)
        celula_combustivel.location = Vector((0.0, -0.30, Z_EST + 0.025))
        celula_combustivel.scale = Vector((esc_c, esc_c, esc_c))
    celula_combustivel.keyframe_insert('location', frame=q)
    celula_combustivel.keyframe_insert('scale', frame=q)
    
    # Êmbolo injetor acompanhando a inserção
    if 0.50 <= t <= 0.75:
        s_inj = math.sin(PI * (t - 0.50) / 0.25)
        injetor.location = Vector((0, -0.70 + s_inj * 0.25, Z_EST + 0.05))
    else:
        injetor.location = Vector((0, -0.70, Z_EST + 0.05))
    injetor.keyframe_insert('location', frame=q)
    
    # 7. Cartucho gasto ejetado pela esteira norte (t=0.50..1.00)
    s_g = (t * 2) % 1.0
    y_g = 0.70 + s_g * 0.75
    cartucho_gasto.location = Vector((0.0, y_g, Z_EST + 0.025))
    cartucho_gasto.keyframe_insert('location', frame=q)

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
    print(f'REATOR_CRISTAL_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((300, 4.4, 0.35), (215, 4.2, 0.60), (120, 4.6, 0.85), (35, 4.0, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'reator_cristal_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na janela de quartzo, núcleo de cristal e anel de indução
    sc.frame_set(int(0.60 * FPS) + 1)  # com a célula sendo injetada e o plasma ativo
    mirar((1.25, -1.85, 1.45), (0.10, -0.40, 0.85), 34)
    sc.render.filepath = os.path.join(AQUI, 'reator_cristal_perto.png')
    bpy.ops.render.render(write_still=True)

print('REATOR_CRISTAL ok')
