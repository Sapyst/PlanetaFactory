"""Estudo isolado (fora do jogo): PAINEL SOLAR 2 da IA, 2×2 tiles (lote 13, energia I).
Evolução tecnológica direta do painel solar básico: maior rendimento fotovoltaico, rastreamento solar biaxial,
células solares dopadas com cristal quântico (perovskita safira/violeta), limpeza ultrassônica contínua
e anel condensador de fótons com lentes orbitais harmônicas.

Engenharia mecânica pesada e estanque da IA:
- Base de concreto armado 1.92 × 1.92 m chanfrada nos 4 cantos com eletrocalhas blindadas e chumbadores duplos.
- Pedestal central cilíndrico reforçado em aço amarelo-industrial desgastado com coroa dentada azimutal
  acionada por servomotor de passo blindado com chicote de cabos de controle.
- Cabeçote basculante com eixo de torção em aço forjado, mancais esféricos de bronze com graxeiros
  e atuador eletromecânico telescópico de fuso de esferas com coifa de borracha sanfonada e haste cromada.
- Duas grandes asas fotovoltaicas bifaciais com molduras de alumínio anodizado escuro, células dopadas
  com micro-prismas anti-reflexo em azul-safira/violeta, barramentos de prata e aletas dissipadoras traseiras.
- Barras de limpeza autônoma ultrassônica que correm em trilhos laterais com bicos de sopro ionizado
  e mangueira espiralada retrátil.
- Inversor trifásico Tier 2 no pedestal com aletas de resfriamento, barramento de LEDs indicadores de produção
  e eletroduto pesado com flange de saída para a rede elétrica ao norte.
- Fenômeno da IA: anel condensador de radiação UV com cristal ressonante e 3 lentes ópticas levitantes
  orbitando continuamente em harmonia.

Peças animadas separadas:
- 'rastreador_azimute': giro azimutal contínuo em Z acompanhando o arco solar (oscilação harmônica suave).
- 'rastreador_elevacao': inclinação em elevação da matriz fotovoltaica.
- 'haste_atuador': haste cromada do atuador linear estendendo e retraindo sincronizada com a elevação.
- 'limpador_esq' e 'limpador_dir': barras de varredura ultrassônica correndo nos trilhos das placas.
- 'lentes_orbita': carrossel de 3 lentes ópticas concentradoras orbitando a 360° ao redor do cristal.
- 'cristal_res': cristal condensador com pulso harmônico de luminescência quântica.

Uso: blender -b --python estudo_painel_solar_2.py -- foto
     blender -b --python estudo_painel_solar_2.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(619)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

M = base3d.M
M['concreto'] = mats.material('ConcretoBase', (0.32, 0.31, 0.29), 0.05, 0.90, pintura=False, ferrugem=0.08, sujeira=0.75)
M['aco_escuro'] = mats.material('AcoEscuro', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.45, sujeira=0.60)
M['aco_gasto'] = mats.material('AcoGasto', (0.35, 0.36, 0.37), 0.85, 0.38, pintura=False, ferrugem=0.30, sujeira=0.50)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['aluminio_anodizado'] = mats.material('AluminioAnodizado', (0.18, 0.19, 0.22), 0.85, 0.32, pintura=False, ferrugem=0.05, sujeira=0.25)
M['aluminio_brilhante'] = mats.material('AluminioAletas', (0.65, 0.67, 0.68), 0.92, 0.25, pintura=False, ferrugem=0.02, sujeira=0.20)
M['cobre'] = mats.material('CobreBarramentos', (0.75, 0.38, 0.20), 0.92, 0.28, pintura=False, ferrugem=0.05, sujeira=0.35)
M['cromo'] = mats.material('CromoHaste', (0.85, 0.85, 0.85), 0.96, 0.12, pintura=False, ferrugem=0.02, sujeira=0.15)
M['borracha'] = mats.material('BorrachaSanfona', (0.05, 0.05, 0.05), 0.05, 0.85, pintura=False, ferrugem=0.0, sujeira=0.70)
M['bronze'] = mats.material('BronzeMancal', (0.55, 0.38, 0.20), 0.90, 0.32, pintura=False, ferrugem=0.12, sujeira=0.30)
M['chao'] = mats.material('Chao', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0)
M['listras'] = base3d.listras_mat()

# Célula Solar Perovskita Quântica (Azul Safira / Violeta Metálico com reflexos anti-reflexo)
m_celula = bpy.data.materials.new('CelulaSolarPerovskita')
m_celula.use_nodes = True
bs_cel = m_celula.node_tree.nodes['Principled BSDF']
bs_cel.inputs['Base Color'].default_value = (0.05, 0.08, 0.28, 1.0)
bs_cel.inputs['Metallic'].default_value = 0.82
bs_cel.inputs['Roughness'].default_value = 0.18
bs_cel.inputs['IOR'].default_value = 1.65
if 'Coat Weight' in bs_cel.inputs:
    bs_cel.inputs['Coat Weight'].default_value = 0.90
    bs_cel.inputs['Coat Roughness'].default_value = 0.04
M['celula_solar'] = m_celula

# Emissões e Cristal Quântico
def mat_emissao(nome, cor, forca=5.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*cor, 1.0)
    bsdf.inputs['Emission Color'].default_value = (*cor, 1.0)
    bsdf.inputs['Emission Strength'].default_value = forca
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m

M['cristal_uv'] = mat_emissao('CristalUV', (0.40, 0.15, 0.95), 6.0)
M['lentes_feixe'] = mat_emissao('LentesFeixe', (0.95, 0.70, 0.20), 4.5)
M['led_verde'] = mat_emissao('LEDVerde', (0.10, 0.95, 0.20), 6.0)


def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


def toro(bm, centro, R, r, nR=24, nr=8, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        anel_pts = []
        for j in range(nr):
            b = j * 2 * PI / nr
            p = d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))
            anel_pts.append(bm.verts.new(Vector(centro) + rot @ p))
        aneis.append(anel_pts)
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


# ==============================================================================
# 1. BASE DE CONCRETO CHANFRADA (1.92 × 1.92 m) E PEDESTAL ESTÁTICO
# ==============================================================================
bm_con = bmesh.new()
bm_base_aco = bmesh.new()
bm_base_ped = bmesh.new()

# Laje octogonal chanfrada
R_BASE = 0.96
caixa_de(bm_con, Vector((-0.96, -0.72, -0.06)), Vector((+0.96, +0.72, +0.06)))
caixa_de(bm_con, Vector((-0.72, -0.96, -0.06)), Vector((+0.72, +0.96, +0.06)))
for sx, sy in ((-1, -1), (-1, +1), (+1, -1), (+1, +1)):
    p0 = Vector((sx * 0.72, sy * 0.72, -0.06))
    p1 = Vector((sx * 0.96, sy * 0.72, -0.06))
    p2 = Vector((sx * 0.72, sy * 0.96, -0.06))
    p0_t, p1_t, p2_t = p0 + Vector((0, 0, 0.12)), p1 + Vector((0, 0, 0.12)), p2 + Vector((0, 0, 0.12))
    v0, v1, v2 = bm_con.verts.new(p0), bm_con.verts.new(p1), bm_con.verts.new(p2)
    v0t, v1t, v2t = bm_con.verts.new(p0_t), bm_con.verts.new(p1_t), bm_con.verts.new(p2_t)
    if sx * sy > 0:
        bm_con.faces.new([v0, v2, v1])
        bm_con.faces.new([v0t, v1t, v2t])
        bm_con.faces.new([v1, v2, v2t, v1t])
    else:
        bm_con.faces.new([v0, v1, v2])
        bm_con.faces.new([v0t, v2t, v1t])
        bm_con.faces.new([v1, v1t, v2t, v2])

# Sapata octogonal de aço com chumbadores duplos
tubo(bm_base_aco, Vector((0, 0, 0.06)), Vector((0, 0, 0.11)), 0.42, 16)
for i_ch in range(8):
    ach = i_ch * (2 * PI / 8)
    cx = math.cos(ach) * 0.36
    cy = math.sin(ach) * 0.36
    tubo(bm_base_aco, Vector((cx, cy, 0.11)), Vector((cx, cy, 0.16)), 0.012, 6)
    caixa(bm_base_aco, Vector((cx, cy, 0.16)), (0.03, 0.03, 0.015))  # porca

# Coluna cilíndrica do pedestal em amarelo gasto (z = 0.11 a 0.58 m)
tubo(bm_base_ped, Vector((0, 0, 0.11)), Vector((0, 0, 0.58)), 0.22, 20)
# 4 nervuras triangulares reforçando a base do pedestal
for inerv in range(4):
    an = inerv * (PI / 2)
    nx = math.cos(an) * 0.28
    ny = math.sin(an) * 0.28
    caixa(bm_base_ped, Vector((nx, ny, 0.22)), (0.035, 0.16, 0.22), Matrix.Rotation(an, 3, 'Z'))

# Eletrocalhas blindadas no chão até a borda norte
caixa_de(bm_base_aco, Vector((-0.06, 0.30, 0.06)), Vector((+0.06, 0.96, 0.11)))
caixa(bm_base_aco, Vector((0.0, 0.95, 0.085)), (0.16, 0.04, 0.08))  # caixa de passagem

# Inversor centralizado Tier 2 na face traseira norte do pedestal (y = +0.24, z = 0.25 a 0.55)
caixa(bm_base_aco, Vector((0.0, +0.28, 0.38)), (0.34, 0.12, 0.28))
# Dissipador de calor em aletas de alumínio na traseira do inversor
for ia in range(10):
    ax = -0.14 + ia * 0.031
    caixa(bm_base_aco, Vector((ax, +0.35, 0.38)), (0.008, 0.04, 0.26))
# Barramento de 6 LEDs de produção no painel frontal do inversor
bm_leds = bmesh.new()
for il in range(6):
    lx = -0.10 + il * 0.04
    caixa(bm_leds, Vector((lx, +0.218, 0.44)), (0.015, 0.005, 0.015))


# ==============================================================================
# 2. CABEÇOTE AZIMUTAL GIRATÓRIO ('rastreador_azimute', z = 0.58 a 0.88 m)
# ==============================================================================
# O objeto 'rastreador_azimute' terá seu pivô exatamente em Vector((0, 0, 0.58)).
# Suas coordenadas locais começam a partir de z = 0.0 relativo a esse ponto!
bm_azimute = bmesh.new()
bm_azimute_aco = bmesh.new()

# Coroa dentada azimutal de giro contínuo
tubo(bm_azimute_aco, Vector((0, 0, 0.00)), Vector((0, 0, 0.06)), 0.24, 24)
# Dentes usinados na coroa
for idt in range(24):
    adt = idt * (2 * PI / 24)
    dx = math.cos(adt) * 0.245
    dy = math.sin(adt) * 0.245
    caixa(bm_azimute_aco, Vector((dx, dy, 0.03)), (0.012, 0.012, 0.05), Matrix.Rotation(adt, 3, 'Z'))

# Servomotor de passo blindado acoplado à coroa na lateral
caixa(bm_azimute_aco, Vector((-0.26, 0.05, 0.03)), (0.12, 0.10, 0.14))
tubo(bm_azimute_aco, Vector((-0.26, 0.05, -0.04)), Vector((-0.26, 0.05, 0.10)), 0.045, 12)

# Coluna superior do cabeçote em amarelo gasto (z = 0.06 a 0.26 local)
tubo(bm_azimute, Vector((0, 0, 0.06)), Vector((0, 0, 0.26)), 0.18, 16)

# Garfo em U reforçado que sustenta o eixo transversal de elevação
caixa(bm_azimute, Vector((-0.22, 0.0, 0.32)), (0.06, 0.16, 0.18))
caixa(bm_azimute, Vector((+0.22, 0.0, 0.32)), (0.06, 0.16, 0.18))
# Mancais de bronze esféricos nos dois lados do garfo (eixo em X, altura z local = 0.35 m -> z mundo = 0.93 m)
tubo(bm_azimute_aco, Vector((-0.26, 0.0, 0.35)), Vector((-0.18, 0.0, 0.35)), 0.075, 16)
tubo(bm_azimute_aco, Vector((+0.18, 0.0, 0.35)), Vector((+0.26, 0.0, 0.35)), 0.075, 16)
# Bicos graxeiros angulados
tubo(bm_azimute_aco, Vector((-0.22, 0.06, 0.40)), Vector((-0.22, 0.08, 0.43)), 0.008, 6)
tubo(bm_azimute_aco, Vector((+0.22, 0.06, 0.40)), Vector((+0.22, 0.08, 0.43)), 0.008, 6)

# Piranômetro da IA: sensor hemisférico no topo do garfo do azimute
tubo(bm_azimute_aco, Vector((+0.22, 0.0, 0.41)), Vector((+0.22, 0.0, 0.50)), 0.010, 8)
tubo(bm_azimute_aco, Vector((+0.22, 0.0, 0.50)), Vector((+0.22, 0.0, 0.52)), 0.022, 12)
toro(bm_azimute_aco, Vector((+0.22, 0.0, 0.52)), 0.018, 0.003, 12, 4)
tubo(bm_azimute_aco, Vector((+0.22, 0.0, 0.52)), Vector((+0.22, 0.0, 0.535)), 0.015, 10)  # cúpula óptica

# Olhal inferior de fixação do atuador de elevação no cabeçote azimutal (x = 0, y = +0.14, z = 0.15)
caixa(bm_azimute_aco, Vector((0.0, +0.14, 0.15)), (0.08, 0.08, 0.08))
tubo(bm_azimute_aco, Vector((-0.05, +0.14, 0.15)), Vector((+0.05, +0.14, 0.15)), 0.022, 10)  # pino mestre


# ==============================================================================
# 3. ATUADOR LINEAR TELESCÓPICO DE FUSO DE ESFERAS (Corpo e Haste)
# ==============================================================================
# O corpo do atuador é filho de 'rastreador_azimute' com rotação em torno do olhal inferior.
# A haste cromada desliza ao longo do eixo do atuador.
bm_atuador_corpo = bmesh.new()
bm_atuador_haste = bmesh.new()

# Corpo cilíndrico do atuador com coifa sanfonada (em coordenadas locais da camisa)
tubo(bm_atuador_corpo, Vector((0, 0, 0.0)), Vector((0, 0, 0.14)), 0.035, 14)
# Motorredutor do fuso no fundo da camisa
caixa(bm_atuador_corpo, Vector((0, 0.035, 0.04)), (0.07, 0.07, 0.07))
# Fole sanfonado de borracha na saída da haste
for isanf in range(4):
    zs = 0.11 + isanf * 0.012
    toro(bm_atuador_corpo, Vector((0, 0, zs)), 0.030, 0.006, 12, 6)

# Haste cromada de alta precisão (objeto 'haste_atuador')
tubo(bm_atuador_haste, Vector((0, 0, 0.0)), Vector((0, 0, 0.15)), 0.018, 12)
# Olhal superior cromado com rótula esférica
caixa(bm_atuador_haste, Vector((0, 0, 0.15)), (0.04, 0.04, 0.04))
tubo(bm_atuador_haste, Vector((-0.025, 0, 0.15)), Vector((+0.025, 0, 0.15)), 0.012, 8)


# ==============================================================================
# 4. MATRIZ FOTOVOLTAICA BIAXIAL E BRAÇOS TRELIÇADOS ('rastreador_elevacao')
# ==============================================================================
# Pivô de elevação centrado no eixo dos mancais do garfo: z local = 0.35 m (z mundo = 0.93 m).
# As placas e a treliça giram em torno do eixo X local!
bm_elevacao = bmesh.new()
bm_celulas = bmesh.new()
bm_barramentos = bmesh.new()

# Eixo transversal maciço de torção de elevação (ao longo de X, de x = -0.75 a +0.75)
tubo(bm_elevacao, Vector((-0.75, 0, 0)), Vector((+0.75, 0, 0)), 0.055, 18)

# Braços treliçados em alumínio forjado que conectam o eixo transversal às duas placas
for sx in (-0.55, +0.55):
    # Braço longitudinal superior (ao longo de Y inclinado)
    tubo(bm_elevacao, Vector((sx, -0.65, 0.04)), Vector((sx, +0.65, 0.04)), 0.038, 12)
    # Braços diagonais de reforço estrutural
    tubo(bm_elevacao, Vector((sx * 0.45, 0, 0)), Vector((sx, -0.45, 0.04)), 0.028, 8)
    tubo(bm_elevacao, Vector((sx * 0.45, 0, 0)), Vector((sx, +0.45, 0.04)), 0.028, 8)

# Olhal traseiro sob a treliça para a fixação da haste do atuador (y = +0.18, z = -0.06)
caixa(bm_elevacao, Vector((0.0, +0.18, -0.06)), (0.07, 0.06, 0.06))
tubo(bm_elevacao, Vector((-0.04, +0.18, -0.06)), Vector((+0.04, +0.18, -0.06)), 0.016, 8)

# DUAS GRANDES ASAS DE PLACAS SOLARES (Asa Esquerda x < 0, Asa Direita x > 0)
# Cada placa: largura 0.68 m, comprimento em Y de -0.68 a +0.68 m (1.36 m de vão)
for sinal_x in (-1.0, 1.0):
    cx = sinal_x * 0.50
    # Moldura externa em alumínio anodizado escuro
    caixa_de(bm_elevacao, Vector((cx - 0.34, -0.68, 0.04)), Vector((cx + 0.34, +0.68, 0.075)))
    # Travessas internas de reforço da moldura
    for y_tr in (-0.34, 0.0, +0.34):
        caixa(bm_elevacao, Vector((cx, y_tr, 0.055)), (0.66, 0.02, 0.03))

    # Painel de vidro fotovoltaico com células de perovskita (embutido na moldura)
    caixa_de(bm_celulas, Vector((cx - 0.32, -0.66, 0.060)), Vector((cx + 0.32, +0.66, 0.072)))

    # Barramentos ultrafinos em prata/ouro (busbars) dividindo as células
    for bx in (-0.18, 0.0, +0.18):
        tubo(bm_barramentos, Vector((cx + bx, -0.65, 0.073)), Vector((cx + bx, +0.65, 0.073)), 0.003, 4)
    for by in (-0.50, -0.25, 0.0, +0.25, +0.50):
        tubo(bm_barramentos, Vector((cx - 0.31, by, 0.073)), Vector((cx + 0.31, by, 0.073)), 0.002, 4)

    # Micro-aletas dissipadoras térmicas traseiras sob a placa
    for iy in range(12):
        ay = -0.60 + iy * 0.10
        caixa(bm_elevacao, Vector((cx, ay, 0.035)), (0.60, 0.008, 0.025))

    # Caixa de junção traseira sob cada asa com cabos em conduíte corrugado
    caixa(bm_base_aco, Vector((cx, +0.20, 0.015)), (0.12, 0.10, 0.04))
    mangueira(bm_base_aco, [Vector((cx, +0.20, 0.015)), Vector((cx * 0.5, +0.10, -0.05)), Vector((0.0, 0.0, -0.10))], 0.012)

    # Cantoneiras e parafusos de retenção nas bordas externas das molduras
    for my in (-0.65, -0.32, 0.0, +0.32, +0.65):
        caixa(bm_base_aco, Vector((cx - sinal_x * 0.34, my, 0.058)), (0.015, 0.04, 0.025))
        tubo(bm_base_aco, Vector((cx - sinal_x * 0.345, my, 0.058)), Vector((cx - sinal_x * 0.355, my, 0.058)), 0.005, 6)

    # Trilhos laterais guia para o robô limpador ultrassônico
    tubo(bm_elevacao, Vector((cx - 0.33, -0.68, 0.082)), Vector((cx - 0.33, +0.68, 0.082)), 0.008, 8)
    tubo(bm_elevacao, Vector((cx + 0.33, -0.68, 0.082)), Vector((cx + 0.33, +0.68, 0.082)), 0.008, 8)


# ==============================================================================
# 5. ROBÔS LIMPADORES ULTRASSÔNICOS ('limpador_esq', 'limpador_dir')
# ==============================================================================
# Cada robô é uma barra transversal que corre nos trilhos guia da placa ao longo de Y.
# Modelados centrados na origem local do objeto.
bm_limp_esq = bmesh.new()
bm_limp_dir = bmesh.new()

for bm_l in (bm_limp_esq, bm_limp_dir):
    # Barra transversal aerodinâmica
    caixa(bm_l, Vector((0, 0, 0.01)), (0.66, 0.045, 0.022))
    # Rolete de microfibra / escova cilíndrica de varredura
    tubo(bm_l, Vector((-0.31, -0.015, -0.002)), Vector((+0.31, -0.015, -0.002)), 0.012, 12)
    # Bicos de sopro de ar comprimido ionizado
    for ib in range(7):
        bx = -0.27 + ib * 0.09
        tubo(bm_l, Vector((bx, +0.018, 0.005)), Vector((bx, +0.018, -0.004)), 0.004, 6)
    # Patins laterais com rolamentos duplos nos trilhos guia
    caixa(bm_l, Vector((-0.33, 0, 0.01)), (0.035, 0.065, 0.028))
    caixa(bm_l, Vector((+0.33, 0, 0.01)), (0.035, 0.065, 0.028))
    tubo(bm_l, Vector((-0.33, -0.02, 0.01)), Vector((-0.33, +0.02, 0.01)), 0.010, 8)
    tubo(bm_l, Vector((+0.33, -0.02, 0.01)), Vector((+0.33, +0.02, 0.01)), 0.010, 8)


# ==============================================================================
# 6. FENÔMENO QUÂNTICO DA IA: NÚCLEO CONDENSADOR UV, LENTES ORBITAIS E PIRANÔMETRO
# ==============================================================================
# Montado no centro entre as duas placas solares (x = 0, y = 0, z = 0.08 relativo à matriz)
bm_condensador_base = bmesh.new()
bm_cristal = bmesh.new()
bm_lentes = bmesh.new()

# Garra e base de anéis de cobre no centro da matriz
toro(bm_condensador_base, Vector((0, 0, 0.08)), 0.08, 0.012, 20, 6)
for ig in range(4):
    ag = ig * (PI / 2) + PI / 4
    gx = math.cos(ag) * 0.075
    gy = math.sin(ag) * 0.075
    tubo(bm_condensador_base, Vector((gx, gy, 0.05)), Vector((gx, gy, 0.12)), 0.007, 6)
    tubo(bm_condensador_base, Vector((gx, gy, 0.12)), Vector((gx * 0.5, gy * 0.5, 0.14)), 0.006, 6)

# Cristal quântico multifacetado central (objeto 'cristal_res', centrado na origem local)
# Bipirâmide hexagonal alongada
crist_pts = [
    Vector((0, 0, +0.06)),
    Vector((0, 0, -0.06)),
]
for k in range(6):
    ak = k * (PI / 3)
    crist_pts.append(Vector((math.cos(ak) * 0.032, math.sin(ak) * 0.032, 0.0)))
v_cr = [bm_cristal.verts.new(p) for p in crist_pts]
for k in range(6):
    k_prox = (k + 1) % 6
    bm_cristal.faces.new([v_cr[0], v_cr[2 + k], v_cr[2 + k_prox]])
    bm_cristal.faces.new([v_cr[1], v_cr[2 + k_prox], v_cr[2 + k]])

# 3 Lentes ópticas satélites em órbita harmônica (objeto 'lentes_orbita', centrado na origem local)
# Raio de órbita 0.15 m
for il in range(3):
    al = il * (2 * PI / 3)
    lx = math.cos(al) * 0.15
    ly = math.sin(al) * 0.15
    # Aro da lente em alumínio brilhante
    toro(bm_condensador_base, Vector((lx, ly, 0.0)), 0.024, 0.003, 16, 4)
    # Lente convexa translúcida com emissão âmbar
    tubo(bm_lentes, Vector((lx, ly, -0.002)), Vector((lx, ly, +0.002)), 0.022, 12)
    # Feixe sutil de convergência em direção ao centro
    tubo(bm_lentes, Vector((lx * 0.85, ly * 0.85, 0.0)), Vector((0, 0, 0)), 0.003, 4)


# ==============================================================================
# 7. INSTANCIAÇÃO DOS OBJETOS BLENDER E HIERARQUIA
# ==============================================================================
# 1. Base Estática
o_base = obj('base_concreto', bm_con, 'concreto')
o_base_aco = obj('base_sapatas', bm_base_aco, 'aco_escuro')
o_base_aco.parent = o_base
o_base_ped = obj('pedestal_coluna', bm_base_ped, 'chassi_amarelo')
o_base_ped.parent = o_base
o_leds = obj('inversor_leds', bm_leds, 'led_verde')
o_leds.parent = o_base

# 2. Cabeçote Azimutal ('rastreador_azimute') com pivô em (0, 0, 0.58)
P_AZIM_PIVO = Vector((0.0, 0.0, 0.58))
o_azimute = obj('rastreador_azimute', bm_azimute, 'chassi_amarelo')
o_azimute.location = P_AZIM_PIVO
o_azimute.parent = o_base
o_azim_aco = obj('azimute_mecanismos', bm_azimute_aco, 'aco_gasto')
o_azim_aco.parent = o_azimute

# 3. Atuador Linear de Elevação (Corpo e Haste)
# Corpo articulado no olhal inferior do cabeçote (y = +0.14, z = 0.15 local)
P_ATU_BASE = Vector((0.0, +0.14, 0.15))
o_atu_corpo = obj('atuador_corpo', bm_atuador_corpo, 'aco_escuro')
o_atu_corpo.location = P_ATU_BASE
o_atu_corpo.parent = o_azimute

o_atu_haste = obj('haste_atuador', bm_atuador_haste, 'cromo')
o_atu_haste.parent = o_atu_corpo

# 4. Matriz Fotovoltaica de Elevação ('rastreador_elevacao') com pivô em (0, 0, 0.35 local)
P_ELEV_PIVO = Vector((0.0, 0.0, 0.35))
o_elev = obj('rastreador_elevacao', bm_elevacao, 'aluminio_anodizado')
o_elev.location = P_ELEV_PIVO
o_elev.parent = o_azimute

o_cel = obj('matriz_celulas', bm_celulas, 'celula_solar')
o_cel.parent = o_elev
o_barr = obj('matriz_barramentos', bm_barramentos, 'cobre')
o_barr.parent = o_elev

# 5. Robôs Limpadores (filhos de 'rastreador_elevacao')
P_LIMP_ESQ_BASE = Vector((-0.50, 0.0, 0.075))
P_LIMP_DIR_BASE = Vector((+0.50, 0.0, 0.075))

o_limp_esq = obj('limpador_esq', bm_limp_esq, 'aluminio_brilhante')
o_limp_esq.location = P_LIMP_ESQ_BASE
o_limp_esq.parent = o_elev

o_limp_dir = obj('limpador_dir', bm_limp_dir, 'aluminio_brilhante')
o_limp_dir.location = P_LIMP_DIR_BASE
o_limp_dir.parent = o_elev

# 6. Fenômeno Quântico: Condensador UV, Cristal e Lentes Orbitais
o_cond_base = obj('condensador_base', bm_condensador_base, 'cobre')
o_cond_base.parent = o_elev

P_CRIST_CTR = Vector((0.0, 0.0, 0.10))
o_cristal = obj('cristal_res', bm_cristal, 'cristal_uv')
o_cristal.location = P_CRIST_CTR
o_cristal.parent = o_elev

P_LENTES_CTR = Vector((0.0, 0.0, 0.10))
o_lentes = obj('lentes_orbita', bm_lentes, 'lentes_feixe')
o_lentes.location = P_LENTES_CTR
o_lentes.parent = o_elev

# Suavizações
for o in (o_base, o_base_aco, o_base_ped, o_azimute, o_azim_aco, o_atu_corpo, o_atu_haste, o_elev, o_limp_esq, o_limp_dir, o_cristal):
    suavizar(o)


# ==============================================================================
# 8. ANIMAÇÕES EM LAÇO FECHADO DE 96 QUADROS (24 FPS, 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)
    t = (f - 1) / QUADROS  # 0.0 a 95/96
    ang_ciclo = t * 2 * PI

    # 1. Rastreamento Solar Biaxial da IA:
    # Azimute oscila suavemente ±7.5° acompanhando a declinação solar
    rot_az = math.radians(7.5) * math.sin(ang_ciclo)
    o_azimute.rotation_euler = Euler((0.0, 0.0, rot_az), 'XYZ')
    o_azimute.keyframe_insert('rotation_euler', frame=f)

    # Elevação da matriz solar oscila entre 26° e 38° (ângulo nominal de pico solar)
    ang_elev = math.radians(32.0 + 6.0 * math.cos(ang_ciclo))
    o_elev.rotation_euler = Euler((ang_elev, 0.0, 0.0), 'XYZ')
    o_elev.keyframe_insert('rotation_euler', frame=f)

    # Cinemática precisa do atuador de fuso de esferas:
    # Posição do olhal na matriz em coordenadas locais do cabeçote azimutal:
    p_olhal_matriz_local = P_ELEV_PIVO + Matrix.Rotation(ang_elev, 3, 'X') @ Vector((0.0, +0.18, -0.06))
    v_atuador = p_olhal_matriz_local - P_ATU_BASE
    dist_atuador = v_atuador.length
    # Orientação angular do atuador
    rot_pitch_atuador = math.atan2(v_atuador.y, v_atuador.z)
    o_atu_corpo.rotation_euler = Euler((-rot_pitch_atuador, 0.0, 0.0), 'XYZ')
    o_atu_corpo.keyframe_insert('rotation_euler', frame=f)

    # Extensão da haste cromada
    extensao_haste = max(0.0, dist_atuador - 0.15)
    o_atu_haste.location = Vector((0.0, 0.0, extensao_haste))
    o_atu_haste.keyframe_insert('location', frame=f)

    # 2. Varredura dos Robôs Limpadores Ultrassônicos:
    # Movimento contínuo de varredura suave de ida e volta ao longo de Y na placa
    y_limp = 0.52 * math.cos(ang_ciclo)
    o_limp_esq.location = P_LIMP_ESQ_BASE + Vector((0.0, y_limp, 0.0))
    o_limp_esq.keyframe_insert('location', frame=f)

    o_limp_dir.location = P_LIMP_DIR_BASE + Vector((0.0, -y_limp, 0.0))
    o_limp_dir.keyframe_insert('location', frame=f)

    # 3. Lentes Ópticas Satélites Orbitando a 360° no plano do cristal
    o_lentes.rotation_euler = Euler((0.0, 0.0, ang_ciclo), 'XYZ')
    o_lentes.keyframe_insert('rotation_euler', frame=f)

    # 4. Pulso Harmônico do Cristal UV Central
    s_cr = 1.0 + 0.10 * math.sin(ang_ciclo * 2.0)
    o_cristal.scale = Vector((s_cr, s_cr, s_cr))
    o_cristal.keyframe_insert('scale', frame=f)


# ==============================================================================
# 9. ILUMINAÇÃO, CHÃO E CÂMERAS CYCLES
# ==============================================================================
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (14, 14, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.6
sol_d.color = (1.0, 0.98, 0.94)
sol_d.angle = math.radians(12.0)
o_sol = bpy.data.objects.new('EFEITO_Sol', sol_d)
sc.collection.objects.link(o_sol)
o_sol.rotation_euler = (math.radians(52), 0, math.radians(-38))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.58, 0.65, 0.78, 1.0)
bg.inputs['Strength'].default_value = 0.60

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

cam_d = bpy.data.cameras.new('Camera')
cam_d.lens = 38
cam_d.clip_start = 0.1
cam_d.clip_end = 100.0
cam = bpy.data.objects.new('EFEITO_Camera', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente=36):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = Vector((0.0, 0.0, 0.85))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(25)

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.2), (210, 2.4), (120, 2.3), (30, 2.1))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'painel_solar_2_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: células fotovoltaicas azuis, robô limpador, atuador linear e lentes orbitais
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(25)
        mirar(Vector((1.45, -1.55, 1.35)), Vector((0.05, -0.10, 0.85)), 35)
        sc.render.filepath = os.path.join(AQUI, 'painel_solar_2_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(25)
    mirar(ALVO + Vector((2.6, -3.0, 1.4)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'painel_solar_2_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('PAINEL_SOLAR_2 ok (%d tris)' % tot_tri)
