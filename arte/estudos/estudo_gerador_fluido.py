"""Estudo isolado (fora do jogo): GERADOR A FLUIDO da IA, 3×3 tiles (lote 13, energia I).
Potência nominal: 2,4 MW. Queima fluido combustível de seiva refinada / óleo orgânico volátil.
Entrada de fluido: FLUIDO_ENT_S1 no sul (borda sul y = -1.44 m, centrado em x = 0.0 m, altura z = 0.35 m).

Engenharia pesada e mecânica industrial da IA:
- Base de concreto armado 2.88 × 2.88 m chanfrada nos 4 cantos em 45°, com canaletas perimetrais de drenagem,
  grelhas de aço galvanizado, manchas escuras de óleo lubrificante e sapatas antivibração vibro-stop com coxins.
- Linha de combustível sul: flange de 4 parafusos faceando y = -1.44 m (z = 0.35 m), válvula de bloqueio esfera
  com volante vermelho, fluxômetro visual com rotor giratório, conjunto de filtros duplos duplex com manômetro,
  bomba de injeção e trilho common-rail com tubos individuais para os injetores de cada cilindro.
- Bloco industrial do motor de combustão interna pesada a seiva: cárter com nervuras de reforço, bloco fundido
  com tampas ovais de inspeção, cabeçotes em liga reforçada, turbocompressor duplo (caracol quente oxidado e caracol frio
  de alumínio), tubulação de ar com abraçadeiras de manga e trocador de calor intercooler aletado.
- Sistema de exaustão vertical maciço: coletor com manta térmica cerâmica, silenciador cilíndrico de alta capacidade
  com cinta de expansão térmica e chaminé que sobe até 2,95 m com corte a 45° e fuligem preta de escape.
- Teto de resfriamento com radiador em colmeia e duas coifas de exaustão com ventiladores axiais de 4 pás em alta rotação,
  protegidos por telas de arame galvanizado.
- Alternador industrial de 2,4 MW com estator estriado, bobinas de enrolamento de cobre visíveis, volante de inércia
  com capa de segurança em listras de perigo, e caixa de saída de alta tensão com 3 isoladores cerâmicos e barramentos.
- Ressonador quântico harmônico da IA: quatro emissores de fluxo que sustentam um anel toroidal de plasma violeta
  levitante em contra-rotação sobre o alternador, absorvendo as flutuações de torque da combustão da seiva.

Peças animadas separadas:
- 'ventilador0' e 'ventilador1': ventiladores axiais superiores contra-rotativos girando em loop contínuo.
- 'volante': volante de inércia do acoplamento do alternador girando velozmente no eixo Y.
- 'rotor_fluxo': rotor do visor de fluxo de combustível girando continuamente.
- 'anel_quantico': toro de campo quântico levitante girando e oscilando harmonicamente.
- 'motor_vibracao': microrruído harmônico de alta frequência em Z simulando o ciclo de queima do motor.
- 'luz_estrobo': lâmpada de monitoramento no mastro piscando a cada 24 quadros.

Uso: blender -b --python estudo_gerador_fluido.py -- foto
     blender -b --python estudo_gerador_fluido.py -- nada
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
random.seed(841)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

M = base3d.M
M['concreto'] = mats.material('ConcretoBase', (0.32, 0.31, 0.29), 0.05, 0.90, pintura=False, ferrugem=0.08, sujeira=0.75)
M['aco_escuro'] = mats.material('AcoEscuro', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.45, sujeira=0.60)
M['aco_gasto'] = mats.material('AcoGasto', (0.35, 0.36, 0.37), 0.85, 0.38, pintura=False, ferrugem=0.30, sujeira=0.50)
M['ferrugem_pesada'] = mats.material('FerrugemEscape', (0.28, 0.14, 0.08), 0.25, 0.85, pintura=False, ferrugem=0.90, sujeira=0.75)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['motor_verde'] = mats.material('MotorVerdeIndustrial', (0.12, 0.24, 0.18), 0.20, 0.45, pintura=True, ferrugem=0.25, sujeira=0.70, desgaste=0.60)
M['aluminio'] = mats.material('AluminioAletas', (0.62, 0.64, 0.65), 0.92, 0.28, pintura=False, ferrugem=0.05, sujeira=0.30)
M['cobre'] = mats.material('CobreBobinas', (0.75, 0.38, 0.20), 0.92, 0.28, pintura=False, ferrugem=0.05, sujeira=0.35)
M['borracha'] = mats.material('BorrachaDuto', (0.05, 0.05, 0.05), 0.05, 0.85, pintura=False, ferrugem=0.0, sujeira=0.70)
M['silicone_azul'] = mats.material('SiliconeTurbo', (0.08, 0.28, 0.65), 0.10, 0.35, pintura=True, ferrugem=0.0, sujeira=0.30)
M['vermelho_valvula'] = mats.material('VermelhoValvula', (0.65, 0.12, 0.10), 0.20, 0.40, pintura=True, ferrugem=0.20, sujeira=0.40)
M['ceramica_isolador'] = mats.material('CeramicaIsolador', (0.72, 0.32, 0.15), 0.05, 0.20, pintura=False, ferrugem=0.02, sujeira=0.25)
M['oleo'] = mats.material('OleoSujeira', (0.02, 0.02, 0.01), 0.20, 0.15, pintura=False, ferrugem=0.0, sujeira=0.95)
M['manta_termica'] = mats.material('MantaTermica', (0.75, 0.72, 0.65), 0.05, 0.85, pintura=False, ferrugem=0.05, sujeira=0.55)
M['chao'] = mats.material('Chao', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0)
M['listras'] = base3d.listras_mat()

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

M['plasma_quantico'] = mat_emissao('PlasmaQuantico', (0.55, 0.15, 0.95), 6.5)
M['luz_estrobo'] = mat_emissao('LuzEstrobo', (1.0, 0.85, 0.25), 8.0)


def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


def toro(bm, centro, R, r, nR=32, nr=10, rot=Matrix.Identity(3)):
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
# 1. LAJE DE CONCRETO CHANFRADA (3×3 tiles = 2.88 × 2.88 m), CANALETAS E SAPATAS
# ==============================================================================
bm_con = bmesh.new()
bm_aco = bmesh.new()
bm_oleo = bmesh.new()

# Laje octogonal chanfrada nos cantos
R_EXT = 1.44  # raio de 2.88 m / 2
H_BASE = 0.12
# Corpo central e chanfros
caixa_de(bm_con, Vector((-1.44, -1.10, -0.06)), Vector((+1.44, +1.10, +0.06)))
caixa_de(bm_con, Vector((-1.10, -1.44, -0.06)), Vector((+1.10, +1.44, +0.06)))
for sx, sy in ((-1, -1), (-1, +1), (+1, -1), (+1, +1)):
    # Bloco triangular nos 4 cantos chanfrados
    p0 = Vector((sx * 1.10, sy * 1.10, -0.06))
    p1 = Vector((sx * 1.44, sy * 1.10, -0.06))
    p2 = Vector((sx * 1.10, sy * 1.44, -0.06))
    p0_t = p0 + Vector((0, 0, 0.12))
    p1_t = p1 + Vector((0, 0, 0.12))
    p2_t = p2 + Vector((0, 0, 0.12))
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

# Canaleta de contenção e dreno na laje
caixa_de(bm_aco, Vector((-1.32, -1.32, +0.05)), Vector((-1.24, +1.32, +0.065)))
caixa_de(bm_aco, Vector((+1.24, -1.32, +0.05)), Vector((+1.32, +1.32, +0.065)))
caixa_de(bm_aco, Vector((-1.24, -1.32, +0.05)), Vector((+1.24, -1.24, +0.065)))
caixa_de(bm_aco, Vector((-1.24, +1.24, +0.05)), Vector((+1.24, +1.32, +0.065)))

# Manchas de óleo queimado sob o motor e bomba
mancha(bm_oleo, (-0.35, 0.10), 0.45, 0.062)
mancha(bm_oleo, (-0.15, -0.65), 0.30, 0.062)
mancha(bm_oleo, (0.05, -1.15), 0.22, 0.062)

# Sapatas de montagem com amortecedores vibro-stop (molas e coxins) sob os chassis
for sx in (-0.85, -0.45, +0.05, +0.45, +0.95):
    for sy in (-0.75, +0.75):
        # Base de aço
        caixa(bm_aco, Vector((sx, sy, +0.09)), (0.16, 0.16, 0.06))
        # Coxim de borracha / mola cilíndrica
        tubo(bm_aco, Vector((sx, sy, +0.12)), Vector((sx, sy, +0.18)), 0.055, 12)
        # Chumbadores duplos
        for dx in (-0.06, +0.06):
            tubo(bm_aco, Vector((sx + dx, sy, +0.09)), Vector((sx + dx, sy, +0.13)), 0.008, 6)

# Longarinas estruturais em duplo I-beam de aço sustentando o conjunto mecânico
caixa_de(bm_aco, Vector((-0.92, -0.85, +0.18)), Vector((-0.80, +0.85, +0.26)))
caixa_de(bm_aco, Vector((+0.00, -0.85, +0.18)), Vector((+0.12, +0.85, +0.26)))
caixa_de(bm_aco, Vector((+0.92, -0.85, +0.18)), Vector((+1.04, +0.85, +0.26)))


# ==============================================================================
# 2. LINHA DE COMBUSTÍVEL SUL (BOCA FLUIDO_ENT_S1 em y = -1.44 m, x = 0, z = 0.35 m)
# ==============================================================================
bm_combustivel = bmesh.new()
bm_comb_valv = bmesh.new()
bm_rotor_flx = bmesh.new()

# Boca de conexão FLUIDO_ENT_S1 perfeitamente na borda: y = -1.44 m, z = 0.35 m
P_BOCA_S1 = Vector((0.0, -1.44, 0.35))
# Flange de 4 parafusos faceando o sul
tubo(bm_combustivel, P_BOCA_S1, P_BOCA_S1 + Vector((0, 0.04, 0)), 0.085, 16)
for ang_f in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
    fx = math.cos(ang_f) * 0.065
    fz = math.sin(ang_f) * 0.065 + 0.35
    tubo(bm_aco, Vector((fx, -1.44, fz)), Vector((fx, -1.42, fz)), 0.008, 6)

# Tubulação principal de combustível de seiva (diâmetro 0.08 m) que avança para o norte
P_VALV = Vector((0.0, -1.28, 0.35))
tubo(bm_combustivel, P_BOCA_S1 + Vector((0, 0.04, 0)), P_VALV, 0.042, 14)

# Válvula globo de bloqueio de emergência
caixa(bm_comb_valv, P_VALV, (0.13, 0.10, 0.13))
# Haste e volante manual vermelho no topo
tubo(bm_aco, P_VALV + Vector((0, 0, 0.06)), P_VALV + Vector((0, 0, 0.20)), 0.012, 8)
toro(bm_comb_valv, P_VALV + Vector((0, 0, 0.20)), 0.07, 0.010, 16, 6)
# Raios do volante
tubo(bm_comb_valv, P_VALV + Vector((-0.06, 0, 0.20)), P_VALV + Vector((+0.06, 0, 0.20)), 0.006, 6)
tubo(bm_comb_valv, P_VALV + Vector((0, -0.06, 0.20)), P_VALV + Vector((0, +0.06, 0.20)), 0.006, 6)

# Fluxômetro cilíndrico de vidro com visor de rotor (y = -1.14 m)
P_FLUX = Vector((0.0, -1.14, 0.35))
tubo(bm_combustivel, P_VALV, P_FLUX - Vector((0, 0.06, 0)), 0.042, 14)
# Caixa do fluxômetro com anéis de bronze
tubo(bm_aco, P_FLUX - Vector((0, 0.06, 0)), P_FLUX + Vector((0, 0.06, 0)), 0.065, 16)
tubo(bm_combustivel, P_FLUX - Vector((0, 0.04, 0)), P_FLUX + Vector((0, 0.04, 0)), 0.055, 16)

# Rotor giratório dentro do fluxômetro ('rotor_fluxo', modelado centrado na origem)
tubo(bm_rotor_flx, Vector((0, -0.03, 0)), Vector((0, +0.03, 0)), 0.012, 8)
for i_rf in range(4):
    ang_rf = i_rf * (PI / 2)
    rx = math.cos(ang_rf) * 0.035
    rz = math.sin(ang_rf) * 0.035
    caixa(bm_rotor_flx, Vector((rx * 0.5, 0, rz * 0.5)), (0.004, 0.045, 0.035), Matrix.Rotation(ang_rf, 3, 'Y'))

# Conjunto de filtros duplos (duplex filters) de combustível (y = -0.96 m, x = -0.15 e +0.15)
tubo(bm_combustivel, P_FLUX + Vector((0, 0.06, 0)), Vector((0, -0.96, 0.35)), 0.042, 14)
for fx in (-0.15, +0.15):
    # Tubo de ramificação
    tubo(bm_combustivel, Vector((0, -0.96, 0.35)), Vector((fx, -0.96, 0.35)), 0.030, 10)
    # Copo do filtro vertical
    tubo(bm_aco, Vector((fx, -0.96, 0.18)), Vector((fx, -0.96, 0.52)), 0.065, 14)
    # Tampa com porca central
    tubo(bm_comb_valv, Vector((fx, -0.96, 0.52)), Vector((fx, -0.96, 0.55)), 0.025, 8)
    # Dreno no fundo
    tubo(bm_aco, Vector((fx, -0.96, 0.18)), Vector((fx, -0.96, 0.14)), 0.012, 6)

# Manômetro diferencial entre os dois filtros
tubo(bm_aco, Vector((0, -0.96, 0.42)), Vector((0, -0.96, 0.56)), 0.010, 8)
tubo(bm_comb_valv, Vector((0, -0.96, 0.56)), Vector((0, -0.94, 0.56)), 0.035, 12)

# Tubulação que sobe para a bomba de alta pressão e common-rail do motor
pts_tubo_inj = [
    Vector((-0.15, -0.96, 0.35)),
    Vector((-0.35, -0.90, 0.38)),
    Vector((-0.45, -0.75, 0.55)),
    Vector((-0.45, -0.60, 0.72))
]
mangueira(bm_combustivel, pts_tubo_inj, 0.022)

# Bomba injetora volumétrica de alta pressão (x = -0.45, y = -0.55, z = 0.72)
caixa(bm_aco, Vector((-0.45, -0.55, 0.72)), (0.18, 0.22, 0.20))
# Common rail (tubo distribuidor forjado espesso de z = 0.88, ao longo de y = -0.45 a +0.45)
tubo(bm_combustivel, Vector((-0.45, -0.45, 0.88)), Vector((-0.45, +0.45, 0.88)), 0.025, 12)
# 6 tubos de injeção direta curvados ligando o rail aos 6 cilindros
for i_cil in range(6):
    y_cil = -0.40 + i_cil * 0.16
    tubo(bm_combustivel, Vector((-0.45, y_cil, 0.88)), Vector((-0.38, y_cil, 0.98)), 0.008, 6)
    tubo(bm_combustivel, Vector((-0.38, y_cil, 0.98)), Vector((-0.32, y_cil, 1.05)), 0.008, 6)
    # Bico injetor hexagonal no cabeçote
    caixa(bm_aco, Vector((-0.32, y_cil, 1.06)), (0.03, 0.03, 0.04))


# ==============================================================================
# 3. BLOCO DO MOTOR INDUSTRIAL A SEIVA (2,4 MW) - VIBRAÇÃO HARMÔNICA
# ==============================================================================
# Modelado em coordenadas locais para que possa vibrar no objeto 'motor_vibracao'
# Posição central do bloco: x = -0.40, y = 0.00, z = 0.65
bm_motor = bmesh.new()
bm_motor_cabecote = bmesh.new()
bm_turbo = bmesh.new()
bm_escape = bmesh.new()
bm_dutos = bmesh.new()

# Cárter inferior nervurado em ferro fundido (de y = -0.55 a +0.55, z = -0.38 a -0.15)
caixa_de(bm_motor, Vector((-0.36, -0.55, -0.38)), Vector((+0.36, +0.55, -0.15)))
# 8 nervuras de arrefecimento do cárter
for ny in range(8):
    y_nerv = -0.48 + ny * 0.14
    caixa(bm_motor, Vector((0.0, y_nerv, -0.39)), (0.74, 0.015, 0.03))
# Bujão de dreno e visor de nível de óleo
tubo(bm_aco, Vector((-0.37, -0.40, -0.32)), Vector((-0.39, -0.40, -0.32)), 0.025, 8)
tubo(bm_aco, Vector((-0.37, +0.20, -0.22)), Vector((-0.37, +0.20, -0.12)), 0.012, 6)  # vareta/tubo

# Bloco de cilindros maciço (z = -0.15 a +0.25, y = -0.55 a +0.55)
caixa_de(bm_motor, Vector((-0.34, -0.55, -0.15)), Vector((+0.34, +0.55, +0.25)))
# 6 janelas ovais de inspeção do bloco com parafusos perimetrais na lateral oeste
for i_jan in range(6):
    yj = -0.40 + i_jan * 0.16
    caixa(bm_motor_cabecote, Vector((-0.345, yj, 0.05)), (0.012, 0.11, 0.18))
    # Parafusos na tampa
    for dy in (-0.04, +0.04):
        for dz in (-0.06, +0.06):
            tubo(bm_aco, Vector((-0.355, yj + dy, 0.05 + dz)), Vector((-0.345, yj + dy, 0.05 + dz)), 0.006, 6)

# Cabeçote reforçado com tampa de válvulas (z = +0.25 a +0.48)
caixa_de(bm_motor_cabecote, Vector((-0.32, -0.56, +0.25)), Vector((+0.32, +0.56, +0.42)))
# Tampas individuais de tuchos de válvulas no topo
for i_valv in range(6):
    yv = -0.40 + i_valv * 0.16
    caixa(bm_motor_cabecote, Vector((0.0, yv, +0.44)), (0.42, 0.13, 0.05))
    # Parafuso central do cabeçote
    tubo(bm_aco, Vector((0.0, yv, +0.465)), Vector((0.0, yv, +0.48)), 0.012, 6)

# Turbocompressor Industrial (x = -0.42, y = +0.35, z = +0.32)
# Caracol da turbina quente (escape)
toro(bm_turbo, Vector((-0.42, +0.35, +0.32)), 0.11, 0.045, 18, 8, Matrix.Rotation(PI/2, 3, 'Y'))
# Caracol do compressor frio (ar de admissão)
toro(bm_dutos, Vector((-0.42, +0.48, +0.32)), 0.10, 0.040, 18, 8, Matrix.Rotation(PI/2, 3, 'Y'))
# Eixo central com mancais de óleo
tubo(bm_aco, Vector((-0.42, +0.32, +0.32)), Vector((-0.42, +0.51, +0.32)), 0.035, 12)

# Mangueiras de silicone azul do intercooler
pts_intercooler = [
    Vector((-0.42, +0.52, +0.32)),
    Vector((-0.48, +0.58, +0.22)),
    Vector((-0.48, +0.58, -0.05)),
    Vector((-0.42, +0.50, -0.15))
]
mangueira(bm_dutos, pts_intercooler, 0.032)
# Radiador Intercooler aletado na lateral oeste (x = -0.48, y = +0.10 a +0.50)
caixa(bm_dutos, Vector((-0.48, +0.30, -0.05)), (0.08, 0.38, 0.28))
for ic_a in range(12):
    ay = +0.12 + ic_a * 0.03
    caixa(bm_aco, Vector((-0.525, ay, -0.05)), (0.015, 0.008, 0.26))

# Coletor de escape isolado com manta térmica cerâmica (x = -0.18, z = +0.32)
tubo(bm_escape, Vector((-0.20, -0.42, +0.32)), Vector((-0.20, +0.32, +0.32)), 0.065, 14)
# Conexão do escape com a turbina
tubo(bm_escape, Vector((-0.20, +0.32, +0.32)), Vector((-0.42, +0.32, +0.32)), 0.065, 14)
# Cintas de fixação da manta térmica
for cy in (-0.35, -0.15, +0.05, +0.25):
    tubo(bm_aco, Vector((-0.20, cy - 0.01, +0.32)), Vector((-0.20, cy + 0.01, +0.32)), 0.072, 14)

# Duto vertical de saída dos gases quentes em direção ao silenciador (sobe em x = -0.20, y = +0.40)
tubo(bm_turbo, Vector((-0.20, +0.40, +0.35)), Vector((-0.20, +0.40, +0.75)), 0.075, 14)


# ==============================================================================
# 4. SILENCIADOR INDUSTRIAL E CHAMINÉ VERTICAL DE ALTA CAPACIDADE (x = -0.20, y = +0.40)
# ==============================================================================
# Silenciador de grande diâmetro com anéis térmicos e chaminé alta
bm_silenciador = bmesh.new()
bm_fuligem = bmesh.new()

Z_SIL_BASE = 1.40
Z_SIL_TOPO = 2.45
R_SIL = 0.18

# Corpo cilíndrico do silenciador industrial (z = 1.40 a 2.45 m)
tubo(bm_silenciador, Vector((-0.60, +0.40, Z_SIL_BASE)), Vector((-0.60, +0.40, Z_SIL_TOPO)), R_SIL, 18)
# Cintas de reforço térmico e flanges
for z_cinta in (Z_SIL_BASE + 0.15, Z_SIL_BASE + 0.50, Z_SIL_BASE + 0.85):
    tubo(bm_aco, Vector((-0.60, +0.40, z_cinta - 0.015)), Vector((-0.60, +0.40, z_cinta + 0.015)), R_SIL + 0.015, 18)
    for ang_sc in range(8):
        asc = ang_sc * (2 * PI / 8)
        scx = math.cos(asc) * (R_SIL + 0.012) - 0.60
        scy = math.sin(asc) * (R_SIL + 0.012) + 0.40
        tubo(bm_aco, Vector((scx, scy, z_cinta - 0.02)), Vector((scx, scy, z_cinta + 0.02)), 0.006, 6)

# Chaminé superior que sobe até z = 2.95 m
tubo(bm_silenciador, Vector((-0.60, +0.40, Z_SIL_TOPO)), Vector((-0.60, +0.40, 2.92)), 0.095, 16)
# Boca chanfrada com fuligem preta de quebra de fluxo
tubo(bm_fuligem, Vector((-0.60, +0.40, 2.90)), Vector((-0.60, +0.40, 2.96)), 0.102, 16)
# Estais de aço segurando a chaminé alta contra o vento
for ea in (0, 2*PI/3, 4*PI/3):
    ex = math.cos(ea) * 0.45 - 0.60
    ey = math.sin(ea) * 0.45 + 0.40
    tubo(bm_aco, Vector((-0.60, +0.40, 2.80)), Vector((ex, ey, 1.45)), 0.005, 6)


# ==============================================================================
# 5. BANCO DE RESFRIAMENTO DE TETO COM 2 VENTILADORES AXIAIS ('ventilador0', '1')
# ==============================================================================
bm_radiador = bmesh.new()
bm_vent0 = bmesh.new()
bm_vent1 = bmesh.new()

# Plataforma de sustentação do radiador sobre o bloco do motor (z = 1.30 a 1.55 m)
caixa_de(bm_radiador, Vector((-0.88, -0.65, 1.28)), Vector((+0.05, +0.25, 1.38)))
# 4 colunas de suporte estrutural
for rx, ry in ((-0.85, -0.60), (-0.85, +0.20), (+0.00, -0.60), (+0.00, +0.20)):
    tubo(bm_aco, Vector((rx, ry, 0.20)), Vector((rx, ry, 1.28)), 0.035, 10)

# Colmeia do trocador de calor de resfriamento líquido da camisa do motor
caixa_de(bm_aco, Vector((-0.84, -0.60, 1.35)), Vector((+0.00, +0.20, 1.42)))

# Coifas cônicas dos dois grandes ventiladores axiais
# Ventilador 0: centrado em x = -0.42, y = -0.35, z = 1.48
# Ventilador 1: centrado em x = -0.42, y = -0.05, z = 1.48
P_VENT0 = Vector((-0.42, -0.38, 1.46))
P_VENT1 = Vector((-0.42, -0.02, 1.46))
R_VENT = 0.22

for p_vent in (P_VENT0, P_VENT1):
    # Coifa cilíndrica aerodinâmica
    tubo(bm_radiador, p_vent - Vector((0, 0, 0.02)), p_vent + Vector((0, 0, 0.08)), R_VENT + 0.02, 20)
    # Grade protetora de arame superior
    toro(bm_aco, p_vent + Vector((0, 0, 0.08)), R_VENT, 0.006, 20, 4)
    toro(bm_aco, p_vent + Vector((0, 0, 0.08)), R_VENT * 0.55, 0.005, 16, 4)
    for ga in range(6):
        ang_g = ga * (PI / 3)
        gx = math.cos(ang_g) * R_VENT
        gy = math.sin(ang_g) * R_VENT
        tubo(bm_aco, p_vent + Vector((0, 0, 0.08)), p_vent + Vector((gx, gy, 0.08)), 0.004, 4)

# Modelagem das 4 pás de cada ventilador (centradas na origem local)
for bm_v in (bm_vent0, bm_vent1):
    # Cubo central com ogiva
    tubo(bm_v, Vector((0, 0, -0.02)), Vector((0, 0, +0.04)), 0.045, 12)
    tubo(bm_v, Vector((0, 0, +0.04)), Vector((0, 0, +0.07)), 0.025, 8)
    # 4 pás aerodinâmicas inclinadas a 32°
    for ip in range(4):
        ang_p = ip * (PI / 2)
        rot_p = Matrix.Rotation(ang_p, 3, 'Z')
        # Pá como lâmina perfilada
        px = math.cos(ang_p) * (R_VENT * 0.55)
        py = math.sin(ang_p) * (R_VENT * 0.55)
        caixa(bm_v, Vector((px, py, 0.015)), (R_VENT * 0.85, 0.075, 0.008), rot_p @ Matrix.Rotation(math.radians(32), 3, 'X'))


# ==============================================================================
# 6. VOLANTE DE INÉRCIA E ACOPLAMENTO ('volante', centrado em x = 0.08, z = 0.65)
# ==============================================================================
bm_volante = bmesh.new()
bm_vol_perigo = bmesh.new()

# Capa de proteção estática em listras de perigo sobre o acoplamento elástico
caixa(bm_vol_perigo, Vector((+0.08, 0.0, 0.65)), (0.16, 0.52, 0.65))

# Volante de inércia maciço e disco de freio (centrado na origem local do objeto 'volante')
# Diâmetro 0.48 m
tubo(bm_volante, Vector((0, -0.08, 0)), Vector((0, +0.08, 0)), 0.24, 24)
# Anel externo reforçado com dentes de cremalheira para partida
tubo(bm_volante, Vector((0, -0.04, 0)), Vector((0, +0.04, 0)), 0.26, 24)
# Furos de balanceamento dinâmico no disco
for i_fur in range(6):
    af = i_fur * (PI / 3)
    fx = math.cos(af) * 0.16
    fz = math.sin(af) * 0.16
    caixa(bm_aco, Vector((fx, 0, fz)), (0.04, 0.09, 0.04))


# ==============================================================================
# 7. ALTERNADOR INDUSTRIAL DE 2,4 MW (x = +0.20 a +1.05, y = -0.50 a +0.50, z = 0.65)
# ==============================================================================
bm_alternador = bmesh.new()
bm_alt_cobre = bmesh.new()
bm_alt_alta_tensao = bmesh.new()

X_ALT_CTR = 0.62
Z_ALT_CTR = 0.65
R_ALT = 0.32

# Carcaça cilíndrica horizontal do alternador (eixo em Y, de y = -0.45 a +0.45)
tubo(bm_alternador, Vector((X_ALT_CTR, -0.45, Z_ALT_CTR)), Vector((X_ALT_CTR, +0.45, Z_ALT_CTR)), R_ALT, 24)
# Tampas frontais e traseiras circulares com flanges de parafusos
tubo(bm_alternador, Vector((X_ALT_CTR, -0.47, Z_ALT_CTR)), Vector((X_ALT_CTR, -0.45, Z_ALT_CTR)), R_ALT + 0.025, 24)
tubo(bm_alternador, Vector((X_ALT_CTR, +0.45, Z_ALT_CTR)), Vector((X_ALT_CTR, +0.47, Z_ALT_CTR)), R_ALT + 0.025, 24)
for ang_af in range(12):
    aaf = ang_af * (2 * PI / 12)
    afx = math.cos(aaf) * (R_ALT + 0.012) + X_ALT_CTR
    afz = math.sin(aaf) * (R_ALT + 0.012) + Z_ALT_CTR
    tubo(bm_aco, Vector((afx, -0.475, afz)), Vector((afx, -0.465, afz)), 0.007, 6)
    tubo(bm_aco, Vector((afx, +0.465, afz)), Vector((afx, +0.475, afz)), 0.007, 6)

# 8 aberturas de ventilação mostrando as bobinas de enrolamento de cobre maciço
for i_ab in range(8):
    aab = i_ab * (2 * PI / 8)
    ax = math.cos(aab) * (R_ALT + 0.01) + X_ALT_CTR
    az = math.sin(aab) * (R_ALT + 0.01) + Z_ALT_CTR
    caixa(bm_alternador, Vector((ax, 0.0, az)), (0.05, 0.65, 0.08), Matrix.Rotation(aab, 3, 'Y'))
    # Bobina de cobre interna
    tubo(bm_alt_cobre, Vector((ax * 0.95, -0.35, az * 0.95)), Vector((ax * 0.95, +0.35, az * 0.95)), 0.035, 10)

# Sapatas de fixação do alternador nas longarinas
for sy in (-0.35, +0.35):
    for sx in (X_ALT_CTR - 0.25, X_ALT_CTR + 0.25):
        caixa(bm_alternador, Vector((sx, sy, 0.30)), (0.08, 0.12, 0.22))
        tubo(bm_aco, Vector((sx, sy, 0.40)), Vector((sx, sy, 0.43)), 0.014, 6)

# Caixa de saída de alta tensão (terminal box) no topo do alternador
caixa(bm_alternador, Vector((X_ALT_CTR, 0.0, Z_ALT_CTR + R_ALT + 0.12)), (0.35, 0.50, 0.20))
caixa(bm_aco, Vector((X_ALT_CTR, 0.0, Z_ALT_CTR + R_ALT + 0.225)), (0.37, 0.52, 0.02))

# 3 Buchas isoladoras cerâmicas de alta tensão com anéis corona e barramentos
for idx_b, by in enumerate((-0.16, 0.0, +0.16)):
    pb = Vector((X_ALT_CTR, by, Z_ALT_CTR + R_ALT + 0.23))
    # Discos isoladores cerâmicos cônicos (4 discos por bucha)
    for idisc in range(4):
        zd = pb.z + idisc * 0.05
        tubo(bm_alt_alta_tensao, Vector((pb.x, pb.y, zd)), Vector((pb.x, pb.y, zd + 0.04)), 0.055 - idisc * 0.005, 12)
    # Anel corona de topo em alumínio
    toro(bm_aco, pb + Vector((0, 0, 0.21)), 0.065, 0.008, 16, 6)
    # Terminal de cobre maciço
    tubo(bm_alt_cobre, pb + Vector((0, 0, 0.20)), pb + Vector((0, 0, 0.28)), 0.015, 8)
    # Cabo condutor grosso descendo pela lateral
    mangueira(bm_aco, [pb + Vector((0, 0, 0.28)), pb + Vector((0.25, 0, 0.18)), pb + Vector((0.45, 0, -0.20))], 0.016)


# ==============================================================================
# 8. CONVERSOR HARMÔNICO RESSONANTE DA IA ('anel_quantico' e mastro)
# ==============================================================================
bm_quantico_base = bmesh.new()
bm_plasma = bmesh.new()
bm_luz = bmesh.new()

P_QUANT_CTR = Vector((X_ALT_CTR, 0.0, Z_ALT_CTR + R_ALT + 0.52))

# 4 emissores eletromagnéticos em cruz apontados para o centro do anel
for ie in range(4):
    ae = ie * (PI / 2) + PI / 4
    ex = math.cos(ae) * 0.28 + X_ALT_CTR
    ey = math.sin(ae) * 0.28
    # Suporte tubular angulado
    tubo(bm_quantico_base, Vector((ex, ey, Z_ALT_CTR + R_ALT + 0.23)), Vector((ex, ey, P_QUANT_CTR.z)), 0.015, 8)
    # Emissor focalizador com ponta de cristal
    p_orig = Vector((ex, ey, P_QUANT_CTR.z))
    p_foco = P_QUANT_CTR + Vector((math.cos(ae) * 0.16, math.sin(ae) * 0.16, 0))
    tubo(bm_quantico_base, p_orig, p_foco, 0.018, 8)
    tubo(bm_quantico_base, p_foco, p_foco + (P_QUANT_CTR - p_foco).normalized() * 0.03, 0.010, 6)

# Toro de plasma quântico levitante (modelado centrado na origem local de 'anel_quantico')
# Diâmetro externo 0.26 m, tubo 0.024 m
toro(bm_plasma, Vector((0, 0, 0)), 0.13, 0.024, 28, 10)
# Núcleo de cristal ressonante central flutuante
for i_nc in range(6):
    anc = i_nc * (PI / 3)
    nx = math.cos(anc) * 0.04
    ny = math.sin(anc) * 0.04
    tubo(bm_plasma, Vector((0, 0, -0.03)), Vector((nx, ny, 0.0)), 0.006, 6)
    tubo(bm_plasma, Vector((nx, ny, 0.0)), Vector((0, 0, +0.03)), 0.006, 6)

# Mastro de telemetria da rede da IA no canto posterior nordeste (sem obstruir as câmeras)
P_MASTRO = Vector((+1.18, +0.95, 0.12))
tubo(bm_aco, P_MASTRO, P_MASTRO + Vector((0, 0, 1.85)), 0.028, 10)
# Antenas chicote inclinadas
tubo(bm_aco, P_MASTRO + Vector((0, 0, 1.85)), P_MASTRO + Vector((-0.15, 0.15, 2.25)), 0.006, 6)
tubo(bm_aco, P_MASTRO + Vector((0, 0, 1.85)), P_MASTRO + Vector((+0.15, -0.15, 2.25)), 0.006, 6)
# Estrobo de topo (centrado na origem local de 'luz_estrobo')
tubo(bm_luz, Vector((0, 0, -0.03)), Vector((0, 0, +0.03)), 0.035, 12)
P_LUZ_CTR = P_MASTRO + Vector((0, 0, 1.88))


# ==============================================================================
# 9. INSTANCIAÇÃO DOS OBJETOS BLENDER E HIERARQUIA
# ==============================================================================
# Conjunto Base Estática
o_base = obj('base_concreto', bm_con, 'concreto')
o_aco = obj('base_estruturas', bm_aco, 'aco_gasto')
o_aco.parent = o_base
o_oleo = obj('base_manchas_oleo', bm_oleo, 'oleo')
o_oleo.parent = o_base

# Linha de Combustível
o_comb = obj('linha_combustivel', bm_combustivel, 'aco_escuro')
o_comb.parent = o_base
o_valv = obj('valvulas_combustivel', bm_comb_valv, 'vermelho_valvula')
o_valv.parent = o_base

# Rotor do Fluxômetro
o_rotor_flx = obj('rotor_fluxo', bm_rotor_flx, 'cobre')
o_rotor_flx.location = P_FLUX
o_rotor_flx.parent = o_base

# Bloco do Motor com Microrruído de Vibração ('motor_vibracao')
P_MOTOR_CTR = Vector((-0.40, 0.00, 0.65))
o_motor = obj('motor_vibracao', bm_motor, 'motor_verde')
o_motor.location = P_MOTOR_CTR
o_motor.parent = o_base

o_cabecote = obj('motor_cabecote', bm_motor_cabecote, 'aco_escuro')
o_cabecote.parent = o_motor
o_turbo = obj('motor_turbo', bm_turbo, 'ferrugem_pesada')
o_turbo.parent = o_motor
o_escape = obj('motor_escape_manta', bm_escape, 'manta_termica')
o_escape.parent = o_motor
o_dutos = obj('motor_dutos', bm_dutos, 'silicone_azul')
o_dutos.parent = o_motor

# Silenciador e Chaminé
o_sil = obj('silenciador_corpo', bm_silenciador, 'aco_escuro')
o_sil.parent = o_base
o_ful = obj('silenciador_fuligem', bm_fuligem, 'oleo')
o_ful.parent = o_base

# Radiador de Teto
o_rad = obj('radiador_teto', bm_radiador, 'aluminio')
o_rad.parent = o_base

# Ventiladores Axiais
o_vent0 = obj('ventilador0', bm_vent0, 'aluminio')
o_vent0.location = P_VENT0
o_vent0.parent = o_base

o_vent1 = obj('ventilador1', bm_vent1, 'aluminio')
o_vent1.location = P_VENT1
o_vent1.parent = o_base

# Volante de Inércia
P_VOL_CTR = Vector((+0.08, 0.0, 0.65))
o_volante = obj('volante', bm_volante, 'aco_gasto')
o_volante.location = P_VOL_CTR
o_volante.parent = o_base
o_vol_perigo = obj('volante_protecao', bm_vol_perigo, 'listras')
o_vol_perigo.parent = o_base

# Alternador de 2,4 MW
o_alt = obj('alternador_corpo', bm_alternador, 'motor_verde')
o_alt.parent = o_base
o_alt_cob = obj('alternador_bobinas', bm_alt_cobre, 'cobre')
o_alt_cob.parent = o_base
o_alt_at = obj('alternador_isoladores', bm_alt_alta_tensao, 'ceramica_isolador')
o_alt_at.parent = o_base

# Ressonador Quântico
o_quant_base = obj('quantico_suportes', bm_quantico_base, 'aco_escuro')
o_quant_base.parent = o_base

o_quant_plasma = obj('anel_quantico', bm_plasma, 'plasma_quantico')
o_quant_plasma.location = P_QUANT_CTR
o_quant_plasma.parent = o_base

o_luz = obj('luz_estrobo', bm_luz, 'luz_estrobo')
o_luz.location = P_LUZ_CTR
o_luz.parent = o_base

# Suavização de polígonos
for o in (o_base, o_motor, o_cabecote, o_turbo, o_sil, o_rad, o_vent0, o_vent1, o_volante, o_alt, o_quant_plasma, o_luz):
    suavizar(o)


# ==============================================================================
# 10. ANIMAÇÕES EM LAÇO FECHADO DE 96 QUADROS (24 FPS, 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)
    t = (f - 1) / QUADROS  # 0.0 a 95/96
    ang_ciclo = t * 2 * PI

    # 1. Ventiladores Axiais contra-rotativos (4 voltas em 96 quadros)
    o_vent0.rotation_euler = Euler((0.0, 0.0, ang_ciclo * 4.0), 'XYZ')
    o_vent0.keyframe_insert('rotation_euler', frame=f)

    o_vent1.rotation_euler = Euler((0.0, 0.0, -ang_ciclo * 4.0), 'XYZ')
    o_vent1.keyframe_insert('rotation_euler', frame=f)

    # 2. Volante de Inércia do Acoplamento do Alternador (8 voltas em 96 quadros no eixo Y)
    o_volante.rotation_euler = Euler((0.0, ang_ciclo * 8.0, 0.0), 'XYZ')
    o_volante.keyframe_insert('rotation_euler', frame=f)

    # 3. Rotor do Fluxômetro de Combustível (4 voltas em 96 quadros no eixo Y)
    o_rotor_flx.rotation_euler = Euler((0.0, ang_ciclo * 4.0, 0.0), 'XYZ')
    o_rotor_flx.keyframe_insert('rotation_euler', frame=f)

    # 4. Anel Quântico Levitante (Rotação no eixo Z e oscilação harmônica em Z)
    z_quant = P_QUANT_CTR.z + 0.018 * math.sin(ang_ciclo * 2.0)
    o_quant_plasma.location = Vector((P_QUANT_CTR.x, P_QUANT_CTR.y, z_quant))
    o_quant_plasma.rotation_euler = Euler((0.0, 0.0, -ang_ciclo * 2.0), 'XYZ')
    o_quant_plasma.keyframe_insert('location', frame=f)
    o_quant_plasma.keyframe_insert('rotation_euler', frame=f)

    # 5. Microrruído de Vibração de Alta Frequência no Bloco do Motor (simulação dos 6 cilindros a 24 Hz)
    vibr_z = 0.0025 * math.sin(ang_ciclo * 12.0)
    vibr_x = 0.0012 * math.cos(ang_ciclo * 12.0)
    o_motor.location = P_MOTOR_CTR + Vector((vibr_x, 0.0, vibr_z))
    o_motor.keyframe_insert('location', frame=f)

    # 6. Estrobo de Monitoramento da Rede (Pisca a cada 24 quadros: f=1..2, 25..26, 49..50, 73..74)
    f_rel = (f - 1) % 24
    sz_luz = 1.35 if f_rel < 2 else 1.0
    o_luz.scale = Vector((sz_luz, sz_luz, sz_luz))
    o_luz.keyframe_insert('scale', frame=f)


# ==============================================================================
# 11. ILUMINAÇÃO, CHÃO E CÂMERAS CYCLES
# ==============================================================================
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (16, 16, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.5
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


ALVO = Vector((0.0, 0.0, 0.90))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(25)

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.5), (210, 2.7), (120, 2.6), (30, 2.4))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 5.4, math.sin(a) * 5.4, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'gerador_fluido_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: bloco do motor, turbo, common rail, acoplamento e anel quântico
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(25)
        mirar(Vector((1.85, -2.15, 1.60)), Vector((-0.10, -0.20, 0.65)), 35)
        sc.render.filepath = os.path.join(AQUI, 'gerador_fluido_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(25)
    mirar(ALVO + Vector((3.4, -3.8, 1.8)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'gerador_fluido_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('GERADOR_FLUIDO ok (%d tris)' % tot_tri)
