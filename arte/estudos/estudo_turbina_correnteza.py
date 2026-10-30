"""Estudo isolado (fora do jogo): TURBINA DE CORRENTEZA da IA, 2×2 tiles (lote 13, energia I).
Sem bocas de itens ou fluidos. Gera 150 kW contínuos aproveitando a vazão hidrológica do rio.
Localizada diretamente na lâmina d'água corrente entre leito e superfície.

Engenharia mecânica pesada e estanque da IA:
- Chassi flutuante catamarã duplo com dois pontões de quilha hidrodinâmica em aço soldado amarelo-industrial desgastado,
  com reforços rebitados, ânodos galvânicos de sacrifício, batentes de borracha vulcanizada (fenders) e linha de lodo/oxidação.
- Superestrutura de vigas transversais I-beam e treliças tubulares em aço galvanizado oxidado, com olhais de içamento
  e 4 guinchos autônomos com cabos de ancoragem tensionados em direção ao fundo rochoso do rio.
- Grade defletora frontal em cunha (trash rack) com 7 lâminas verticais aerodinâmicas inclinadas a 45° com faixas de perigo,
  evitando o aprisionamento de troncos e detritos fluviais.
- Rotor hidráulico hidrocinético submerso central com cubo ogival em bronze e 4 pás helicoidais torcidas de alta eficiência,
  girando suavemente em loop contínuo de 96 quadros.
- Trem de transmissão com redutor planetário estanque submerso, eixo de subida blindado e gerador elétrico superior de 150 kW
  com 16 aletas de resfriamento, caixa de terminais IP68 com manômetro e grossos cabos blindados submarinos de saída.
- Conversor harmônico piezoelétrico no topo do gerador com cristal ressonador em cúpula de quartzo e estrobo fluvial pulsante.

Peças animadas separadas:
- 'catamara': conjunto flutuante com oscilação hidrodinâmica sutil (arfagem, rolamento e flutuação em Z).
- 'rotor': rotor hidrocinético de 4 pás girando continuamente a 360° em torno do eixo Y.
- 'boia_sensor': boia cilíndrica de telemetria de nível e vazão oscilando em sua guia graduada vertical.
- 'luz_topo': estrobo de navegação fluvial emitindo flashes periódicos a cada 24 quadros.
- 'cristal_piezo': cristal ressonador com pulso harmônico de luminescência quântica.

Uso: blender -b --python estudo_turbina_correnteza.py -- foto
     blender -b --python estudo_turbina_correnteza.py -- nada
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
random.seed(337)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

M = base3d.M
M['concreto'] = mats.material('ConcretoLeito', (0.30, 0.30, 0.28), 0.05, 0.92, pintura=False, ferrugem=0.05, sujeira=0.80)
M['aco_escuro'] = mats.material('AcoEscuro', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.45, sujeira=0.60)
M['aco_gasto'] = mats.material('AcoGasto', (0.35, 0.36, 0.37), 0.85, 0.38, pintura=False, ferrugem=0.30, sujeira=0.50)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['aluminio'] = mats.material('AluminioAletas', (0.60, 0.62, 0.63), 0.92, 0.28, pintura=False, ferrugem=0.05, sujeira=0.30)
M['cobre'] = mats.material('CobreTerminais', (0.75, 0.38, 0.20), 0.92, 0.30, pintura=False, ferrugem=0.05, sujeira=0.40)
M['borracha'] = mats.material('BorrachaFender', (0.05, 0.05, 0.05), 0.05, 0.85, pintura=False, ferrugem=0.0, sujeira=0.70)
M['verde_lodo'] = mats.material('VerdeLodo', (0.07, 0.14, 0.08), 0.02, 0.88, pintura=False, ferrugem=0.05, sujeira=0.90)
M['bronze_naval'] = mats.material('BronzeNaval', (0.55, 0.38, 0.20), 0.90, 0.32, pintura=False, ferrugem=0.15, sujeira=0.35)
M['laranja_boia'] = mats.material('LaranjaBoia', (0.85, 0.25, 0.04), 0.10, 0.42, pintura=True, ferrugem=0.0, sujeira=0.50, desgaste=0.30)
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

M['cristal'] = mat_emissao('CristalPiezo', (0.2, 0.85, 1.0), 5.0)
M['luz_branca'] = mat_emissao('EstroboTopo', (1.0, 0.92, 0.4), 8.0)

# Água translúcida de rio cristalino
m_ag = bpy.data.materials.new('AguaRio')
m_ag.use_nodes = True
bs_ag = m_ag.node_tree.nodes['Principled BSDF']
bs_ag.inputs['Base Color'].default_value = (0.15, 0.45, 0.50, 1.0)
bs_ag.inputs['Roughness'].default_value = 0.02
bs_ag.inputs['Metallic'].default_value = 0.0
bs_ag.inputs['IOR'].default_value = 1.333
if 'Transmission Weight' in bs_ag.inputs:
    bs_ag.inputs['Transmission Weight'].default_value = 0.95
elif 'Transmission' in bs_ag.inputs:
    bs_ag.inputs['Transmission'].default_value = 0.95
M['agua_rio'] = m_ag


def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


# -----------------------------------------------------------------------------
# Chassi Flutuante (Catamarã): 2 Pontões de Quilha + Vigas Transversais + Batentes
# -----------------------------------------------------------------------------
bm_chassi = bmesh.new()
bm_chassi_escuro = bmesh.new()
bm_chassi_borracha = bmesh.new()
bm_chassi_metal = bmesh.new()
bm_chassi_lodo = bmesh.new()
bm_perigo = bmesh.new()

# Modelagem dos dois pontões (x = -0.68 m e x = +0.68 m)
for sinal in (-1.0, 1.0):
    px = sinal * 0.68
    # Casco principal: comprimento de y = -0.88 a y = +0.88 m, largura 0.34 m, altura de z = -0.22 a +0.16 m
    # Nariz a montante (Sul: y = -0.88 m a -0.60 m) chanfrado em proa de quebra-onda
    # Corpo central (y = -0.60 a +0.60 m)
    # Popa a jusante (y = +0.60 a +0.88 m) afilada
    
    # Corpo central
    caixa_de(bm_chassi, Vector((px - 0.17, -0.60, -0.16)), Vector((px + 0.17, +0.60, +0.16)))
    # Quilha inferior chanfrada (fundo em V para estabilidade hidrodinâmica)
    caixa_de(bm_chassi_escuro, Vector((px - 0.14, -0.60, -0.25)), Vector((px + 0.14, +0.60, -0.16)))
    caixa_de(bm_chassi_escuro, Vector((px - 0.08, -0.58, -0.28)), Vector((px + 0.08, +0.58, -0.25)))

    # Proa a montante (Sul: y de -0.88 a -0.60)
    caixa_de(bm_chassi, Vector((px - 0.15, -0.75, -0.14)), Vector((px + 0.15, -0.60, +0.16)))
    caixa_de(bm_chassi, Vector((px - 0.11, -0.88, -0.10)), Vector((px + 0.11, -0.75, +0.16)))
    # Quebra-onda pontudo
    tubo(bm_chassi_escuro, Vector((px, -0.88, -0.20)), Vector((px, -0.88, +0.18)), 0.025, 8)
    viga(bm_chassi_escuro, Vector((px, -0.88, +0.18)), Vector((px, -0.60, +0.16)), 0.035)

    # Popa a jusante (Norte: y de +0.60 a +0.88)
    caixa_de(bm_chassi, Vector((px - 0.15, +0.60, -0.14)), Vector((px + 0.15, +0.75, +0.16)))
    caixa_de(bm_chassi, Vector((px - 0.11, +0.75, -0.10)), Vector((px + 0.11, +0.88, +0.16)))

    # Chapas de desgaste e reforço na linha d'água (faixa de z = -0.06 a +0.04)
    lado_ext = px + sinal * 0.175
    caixa_de(bm_chassi_metal, Vector((lado_ext - 0.01, -0.70, -0.05)), Vector((lado_ext + 0.01, +0.70, +0.05)))
    
    # Faixa de lodo / algas marinhas na linha d'água (z = -0.08 a +0.02)
    caixa_de(bm_chassi_lodo, Vector((lado_ext - 0.012, -0.65, -0.07)), Vector((lado_ext + 0.012, +0.65, -0.01)))

    # 4 Batentes cilíndricos de borracha (fenders) pendurados na borda externa
    for y_bat in (-0.45, -0.15, +0.15, +0.45):
        bx = px + sinal * 0.205
        # Cilindro de borracha com estrias
        tubo(bm_chassi_borracha, Vector((bx, y_bat, -0.08)), Vector((bx, y_bat, +0.08)), 0.035, 10)
        # Correntes de fixação
        tubo(bm_chassi_metal, Vector((bx, y_bat, +0.08)), Vector((px + sinal * 0.17, y_bat, +0.14)), 0.008, 6)
        tubo(bm_chassi_metal, Vector((bx, y_bat, -0.08)), Vector((px + sinal * 0.17, y_bat, -0.04)), 0.008, 6)

    # Ânodos de sacrifício galvânicos de zinco (blocos retangulares na quilha submersa)
    for y_anodo in (-0.35, +0.35):
        caixa(bm_chassi_metal, Vector((px + sinal * 0.155, y_anodo, -0.18)), (0.025, 0.08, 0.035))

    # Olhais de içamento para drones guindaste no convés dos pontões
    for y_olhai in (-0.55, +0.55):
        tubo(bm_chassi_metal, Vector((px, y_olhai, +0.16)), Vector((px, y_olhai, +0.22)), 0.02, 8)
        caixa(bm_chassi_escuro, Vector((px, y_olhai, +0.165)), (0.08, 0.08, 0.015))

    # Guinchos de amarração de ancoragem nas extremidades (y = -0.70 e y = +0.70)
    for y_guincho, dir_y in ((-0.70, -1.0), (+0.70, 1.0)):
        gx = px
        # Base e carretel do guincho
        caixa(bm_chassi_escuro, Vector((gx, y_guincho, +0.185)), (0.12, 0.10, 0.05))
        tubo(bm_chassi_metal, Vector((gx - 0.04, y_guincho, +0.22)), Vector((gx + 0.04, y_guincho, +0.22)), 0.03, 10)
        # Cabo de aço descendo em diagonal para o leito do rio
        tubo(bm_chassi_escuro, Vector((gx, y_guincho + dir_y * 0.05, +0.22)), Vector((gx + sinal * 0.20, y_guincho + dir_y * 0.30, -0.55)), 0.010, 8)

# Vigas transversais de aço galvanizado que unem os dois pontões
for y_viga in (-0.55, -0.20, +0.20, +0.55):
    # Viga I principal
    p_esq = Vector((-0.68, y_viga, +0.18))
    p_dir = Vector((+0.68, y_viga, +0.18))
    viga(bm_chassi_metal, p_esq, p_dir, 0.065)
    # Flanges de fixação nos pontões com parafusos de retenção
    for fx in (-0.55, +0.55):
        caixa(bm_chassi_escuro, Vector((fx, y_viga, +0.18)), (0.07, 0.10, 0.08))
        # Parafusos hexagonais de alta resistência
        for dx, dy in ((-0.025, -0.035), (-0.025, +0.035), (+0.025, -0.035), (+0.025, +0.035)):
            tubo(bm_chassi_metal, Vector((fx + dx, y_viga + dy, +0.22)), Vector((fx + dx, y_viga + dy, +0.235)), 0.007, 6)

# Tensores mecânicos rosqueados (turnbuckles) nos 4 cabos de ancoragem
for sinal in (-1.0, 1.0):
    for y_guincho, dir_y in ((-0.70, -1.0), (+0.70, 1.0)):
        gx = sinal * 0.68
        p_cabo_orig = Vector((gx, y_guincho + dir_y * 0.05, +0.22))
        p_cabo_dest = Vector((gx + sinal * 0.20, y_guincho + dir_y * 0.30, -0.55))
        p_mid = (p_cabo_orig + p_cabo_dest) * 0.5
        # Corpo tubular do tensor com fuso rosqueado
        tubo(bm_chassi_metal, p_mid - Vector((0, 0, 0.05)), p_mid + Vector((0, 0, 0.05)), 0.018, 8)
        caixa(bm_chassi_escuro, p_mid, (0.04, 0.04, 0.03))

# Defletores hidrodinâmicos internos direcionando o fluxo do rio para o rotor
for sinal in (-1.0, 1.0):
    px = sinal * 0.50
    p_d0 = Vector((px, -0.65, -0.15))
    p_d1 = Vector((sinal * 0.42, -0.40, -0.15))
    viga(bm_chassi_escuro, p_d0, p_d1, 0.025)
    caixa_de(bm_chassi, Vector((min(px, sinal * 0.42) - 0.01, -0.65, -0.20)), Vector((max(px, sinal * 0.42) + 0.01, -0.40, 0.05)))

# Berço central longitudinal que sustenta os mancais do rotor e o gerador superior
caixa_de(bm_chassi_metal, Vector((-0.24, -0.58, +0.17)), Vector((-0.16, +0.58, +0.22)))
caixa_de(bm_chassi_metal, Vector((+0.16, -0.58, +0.17)), Vector((+0.24, +0.58, +0.22)))
# Travessas diagonais do berço
tubo(bm_chassi_metal, Vector((-0.20, -0.30, +0.19)), Vector((+0.20, +0.30, +0.19)), 0.018, 8)
tubo(bm_chassi_metal, Vector((-0.20, +0.30, +0.19)), Vector((+0.20, -0.30, +0.19)), 0.018, 8)

# Grade defletora frontal de detritos (Trash Rack) a montante (Sul: y de -0.65 a -0.92 m)
# Formato em cunha angulada a 45°
p_topo_rack = Vector((0.0, -0.62, +0.28))
# Travessa superior e inferior
tubo(bm_chassi_escuro, Vector((-0.52, -0.62, +0.28)), Vector((+0.52, -0.62, +0.28)), 0.025, 10)
tubo(bm_chassi_escuro, Vector((-0.52, -0.88, -0.28)), Vector((+0.52, -0.88, -0.28)), 0.025, 10)
tubo(bm_chassi_escuro, Vector((-0.52, -0.75, 0.00)), Vector((+0.52, -0.75, 0.00)), 0.022, 10)

# Faixas de perigo na travessa superior
caixa(bm_perigo, Vector((0.0, -0.62, +0.29)), (0.90, 0.04, 0.04))

# 7 lâminas verticais afiadas em cunha
for i in range(7):
    rx = -0.42 + i * 0.14
    p_sup = Vector((rx, -0.62, +0.28))
    p_inf = Vector((rx, -0.88, -0.28))
    # Lâmina perfilada
    viga(bm_chassi_escuro, p_inf, p_sup, 0.018)
    # Reforço em cunha frontal
    viga(bm_chassi_metal, p_inf + Vector((0, -0.03, 0)), (p_sup + p_inf) * 0.5 + Vector((0, -0.04, 0)), 0.012)
    # Ponta da lâmina chanfrada
    tubo(bm_chassi_metal, p_inf, p_inf + Vector((0, -0.04, 0.02)), 0.010, 6)

# Mancais estanques submersos para o rotor:
# Mancal dianteiro (y = -0.48 m):
caixa(bm_chassi_escuro, Vector((0.0, -0.48, -0.08)), (0.24, 0.10, 0.16))
tubo(bm_chassi_metal, Vector((0.0, -0.53, -0.08)), Vector((0.0, -0.43, -0.08)), 0.085, 14)
# Parafusos do mancal dianteiro
for p_my in (-0.51, -0.45):
    for p_mx in (-0.09, +0.09):
        tubo(bm_chassi_metal, Vector((p_mx, p_my, 0.00)), Vector((p_mx, p_my, 0.02)), 0.007, 6)
# Suportes estruturais em V descendo das vigas para o mancal dianteiro
tubo(bm_chassi_escuro, Vector((-0.20, -0.48, +0.18)), Vector((-0.08, -0.48, -0.05)), 0.025, 8)
tubo(bm_chassi_escuro, Vector((+0.20, -0.48, +0.18)), Vector((+0.08, -0.48, -0.05)), 0.025, 8)

# Mancal traseiro com caixa multiplicadora planetária submersa (y = +0.40 m):
caixa(bm_chassi_escuro, Vector((0.0, +0.38, -0.06)), (0.30, 0.16, 0.22))
tubo(bm_chassi_metal, Vector((0.0, +0.30, -0.06)), Vector((0.0, +0.46, -0.06)), 0.105, 16)
# Anel de parafusos perimetrais no flange da caixa multiplicadora
for ang_p in range(12):
    ap = ang_p * (2 * PI / 12)
    px = math.cos(ap) * 0.125
    pz = math.sin(ap) * 0.125 - 0.06
    tubo(bm_chassi_metal, Vector((px, +0.31, pz)), Vector((px, +0.325, pz)), 0.006, 6)

# Nervuras radiais na caixa multiplicadora
for ang_n in (0, PI/4, PI/2, 3*PI/4, PI, 5*PI/4, 3*PI/2, 7*PI/4):
    nx = math.cos(ang_n) * 0.115
    nz = math.sin(ang_n) * 0.115 - 0.06
    caixa(bm_chassi_metal, Vector((nx, +0.38, nz)), (0.015, 0.12, 0.015))

# Eixo de transmissão vertical blindado que sobe da caixa submersa para a superestrutura (x = 0, y = +0.38)
tubo(bm_chassi_metal, Vector((0.0, +0.38, 0.05)), Vector((0.0, +0.38, +0.32)), 0.045, 14)
# Tubos de lubrificação de óleo e visor de nível com manômetro
mangueira(bm_chassi_metal, [Vector((-0.07, +0.35, -0.05)), Vector((-0.10, +0.35, +0.15)), Vector((-0.10, +0.35, +0.35))], 0.010)
caixa(bm_chassi_escuro, Vector((-0.10, +0.35, +0.25)), (0.04, 0.03, 0.06))  # visor

# Suportes para o mancal traseiro
tubo(bm_chassi_escuro, Vector((-0.20, +0.38, +0.18)), Vector((-0.12, +0.38, 0.02)), 0.028, 8)
tubo(bm_chassi_escuro, Vector((+0.20, +0.38, +0.18)), Vector((+0.12, +0.38, 0.02)), 0.028, 8)


# -----------------------------------------------------------------------------
# Gerador Elétrico Superior de 150 kW (x = 0.0, y = +0.05 a +0.45, z = +0.38 a +0.72)
# -----------------------------------------------------------------------------
bm_gerador = bmesh.new()
bm_gerador_aletas = bmesh.new()
bm_gerador_cobre = bmesh.new()
bm_gerador_cabos = bmesh.new()

# Carcaça cilíndrica horizontal do gerador elétrico (eixo em Y, de y = -0.15 a +0.35, z = +0.44)
Z_GEN = 0.45
R_GEN = 0.16
tubo(bm_gerador, Vector((0.0, -0.12, Z_GEN)), Vector((0.0, +0.32, Z_GEN)), R_GEN, 18)
# Tampas frontal e traseira chanfradas com anéis de flange e parafusos
caixa(bm_gerador, Vector((0.0, -0.13, Z_GEN)), (0.34, 0.02, 0.34))
caixa(bm_gerador, Vector((0.0, +0.33, Z_GEN)), (0.34, 0.02, 0.34))
tubo(bm_gerador_aletas, Vector((0.0, -0.135, Z_GEN)), Vector((0.0, -0.125, Z_GEN)), R_GEN + 0.015, 18)
tubo(bm_gerador_aletas, Vector((0.0, +0.325, Z_GEN)), Vector((0.0, +0.335, Z_GEN)), R_GEN + 0.015, 18)
for ang_gf in range(8):
    agf = ang_gf * (2 * PI / 8)
    gx = math.cos(agf) * (R_GEN + 0.010)
    gz = math.sin(agf) * (R_GEN + 0.010) + Z_GEN
    tubo(bm_gerador_aletas, Vector((gx, -0.14, gz)), Vector((gx, -0.13, gz)), 0.006, 6)
    tubo(bm_gerador_aletas, Vector((gx, +0.33, gz)), Vector((gx, +0.34, gz)), 0.006, 6)

# 16 aletas longitudinais de resfriamento em alumínio ao redor da carcaça do gerador
for i in range(16):
    ang = i * (2 * PI / 16)
    ax = math.cos(ang) * (R_GEN + 0.02)
    az = math.sin(ang) * (R_GEN + 0.02) + Z_GEN
    # Aleta como lâmina fina
    rot_aleta = Matrix.Rotation(ang, 3, 'Y')
    caixa(bm_gerador_aletas, Vector((ax, +0.10, az)), (0.008, 0.38, 0.04), rot_aleta)

# Pés de montagem do gerador no berço de vigas
for gy in (-0.05, +0.25):
    for gx in (-0.16, +0.16):
        caixa(bm_gerador, Vector((gx, gy, 0.28)), (0.05, 0.06, 0.16))
        # Parafusos na sapata
        tubo(bm_gerador_aletas, Vector((gx, gy, 0.36)), Vector((gx, gy, 0.38)), 0.012, 6)

# Caixa de junção elétrica estanque blindada (NEMA 4X / IP68) no topo do gerador
caixa(bm_gerador, Vector((0.0, +0.08, Z_GEN + R_GEN + 0.06)), (0.18, 0.22, 0.10))
# Tampa da caixa com parafusos perimetrais
caixa(bm_gerador_aletas, Vector((0.0, +0.08, Z_GEN + R_GEN + 0.115)), (0.19, 0.23, 0.015))
for cx, cy in ((-0.08, -0.01), (-0.08, +0.17), (+0.08, -0.01), (+0.08, +0.17), (0.0, -0.01), (0.0, +0.17)):
    tubo(bm_gerador_aletas, Vector((cx, cy, Z_GEN + R_GEN + 0.12)), Vector((cx, cy, Z_GEN + R_GEN + 0.13)), 0.006, 6)

# Manômetro analógico de pressão de vedação interna com mostrador circular e aro de cobre
p_manom = Vector((+0.095, +0.08, Z_GEN + R_GEN + 0.06))
tubo(bm_gerador_aletas, p_manom, p_manom + Vector((0.02, 0, 0)), 0.025, 14)
tubo(bm_gerador_cobre, p_manom + Vector((0.018, 0, 0)), p_manom + Vector((0.024, 0, 0)), 0.027, 14)  # aro
caixa(bm_gerador_cobre, p_manom + Vector((0.023, 0, 0)), (0.002, 0.004, 0.020))  # agulha indicadora

# Prensa-cabos industriais de latão/cobre e 2 cabos de alta potência blindados saindo para a lateral
p_cabo1 = Vector((-0.095, +0.04, Z_GEN + R_GEN + 0.05))
p_cabo2 = Vector((-0.095, +0.12, Z_GEN + R_GEN + 0.05))
tubo(bm_gerador_cobre, p_cabo1, p_cabo1 + Vector((-0.03, 0, 0)), 0.018, 12)
tubo(bm_gerador_cobre, p_cabo2, p_cabo2 + Vector((-0.03, 0, 0)), 0.018, 12)
# Porcas sextavadas nos prensa-cabos
tubo(bm_gerador_aletas, p_cabo1 + Vector((-0.015, 0, 0)), p_cabo1 + Vector((-0.010, 0, 0)), 0.024, 6)
tubo(bm_gerador_aletas, p_cabo2 + Vector((-0.015, 0, 0)), p_cabo2 + Vector((-0.010, 0, 0)), 0.024, 6)

# Cabos descendo em curva Bézier suave protegidos por conduíte flexível até o pontão oeste
pts_cabo1 = [
    Vector((-0.12, +0.04, Z_GEN + R_GEN + 0.05)),
    Vector((-0.28, +0.04, Z_GEN + 0.10)),
    Vector((-0.45, +0.02, 0.24)),
    Vector((-0.68, +0.00, 0.19)),
    Vector((-0.80, -0.05, 0.12))
]
pts_cabo2 = [
    Vector((-0.12, +0.12, Z_GEN + R_GEN + 0.05)),
    Vector((-0.28, +0.12, Z_GEN + 0.08)),
    Vector((-0.45, +0.10, 0.22)),
    Vector((-0.68, +0.08, 0.18)),
    Vector((-0.80, +0.05, 0.12))
]
mangueira(bm_gerador_cabos, pts_cabo1, 0.014)
mangueira(bm_gerador_cabos, pts_cabo2, 0.014)
# Abraçadeiras fixando os cabos na travessa estrutural
caixa(bm_gerador_aletas, Vector((-0.45, +0.06, 0.22)), (0.04, 0.12, 0.02))
caixa(bm_gerador_aletas, Vector((-0.68, +0.04, 0.18)), (0.04, 0.12, 0.02))

# Acoplamento elástico e carcaça do ventilador traseiro
tubo(bm_gerador, Vector((0.0, -0.15, Z_GEN)), Vector((0.0, -0.12, Z_GEN)), 0.15, 16)
tubo(bm_gerador_aletas, Vector((0.0, -0.16, Z_GEN)), Vector((0.0, -0.15, Z_GEN)), 0.14, 16)


# -----------------------------------------------------------------------------
# Ressonador Quântico Piezoelétrico da IA e Estrobo Fluvial
# -----------------------------------------------------------------------------
bm_piezo_base = bmesh.new()
bm_cristal = bmesh.new()
bm_luz = bmesh.new()

# Base em anel de cobre e 4 colunas sobre o topo da caixa de junção
Z_DOMO = Z_GEN + R_GEN + 0.13
tubo(bm_piezo_base, Vector((0.0, +0.08, Z_DOMO)), Vector((0.0, +0.08, Z_DOMO + 0.02)), 0.07, 14)
for i in range(4):
    ang_c = i * (PI / 2) + PI / 4
    cx = math.cos(ang_c) * 0.055
    cy = math.sin(ang_c) * 0.055 + 0.08
    tubo(bm_piezo_base, Vector((cx, cy, Z_DOMO + 0.02)), Vector((cx, cy, Z_DOMO + 0.12)), 0.007, 8)
tubo(bm_piezo_base, Vector((0.0, +0.08, Z_DOMO + 0.12)), Vector((0.0, +0.08, Z_DOMO + 0.135)), 0.065, 14)

# Cristal piezoelétrico multifacetado que ressoa com a geração hidrelétrica
# Modelado centrado na origem local (0, 0, 0)
P_CRISTAL_CTR = Vector((0.0, +0.08, Z_DOMO + 0.07))
cristal_pts = [
    Vector((0, 0, +0.04)),   # topo
    Vector((0, 0, -0.04)),   # base
    Vector((+0.028, 0, 0)),
    Vector((-0.028, 0, 0)),
    Vector((0, +0.028, 0)),
    Vector((0, -0.028, 0))
]
v_c = [bm_cristal.verts.new(p) for p in cristal_pts]
# Faces superiores
bm_cristal.faces.new([v_c[0], v_c[2], v_c[4]])
bm_cristal.faces.new([v_c[0], v_c[4], v_c[3]])
bm_cristal.faces.new([v_c[0], v_c[3], v_c[5]])
bm_cristal.faces.new([v_c[0], v_c[5], v_c[2]])
# Faces inferiores
bm_cristal.faces.new([v_c[1], v_c[4], v_c[2]])
bm_cristal.faces.new([v_c[1], v_c[3], v_c[4]])
bm_cristal.faces.new([v_c[1], v_c[5], v_c[3]])
bm_cristal.faces.new([v_c[1], v_c[2], v_c[5]])

# Mastro central superior com estrobo fluvial âmbar/vermelho
Z_ESTROBO = Z_DOMO + 0.135
P_LUZ_CTR = Vector((0.0, +0.08, Z_ESTROBO + 0.08))
tubo(bm_piezo_base, Vector((0.0, +0.08, Z_ESTROBO)), Vector((0.0, +0.08, Z_ESTROBO + 0.05)), 0.015, 8)
# Lanterna de Fresnel do estrobo centrada na origem local
tubo(bm_luz, Vector((0, 0, -0.025)), Vector((0, 0, +0.025)), 0.028, 12)
# Gaiola de proteção do estrobo
for i in range(4):
    ang_g = i * (PI / 2)
    gx = math.cos(ang_g) * 0.035
    gy = math.sin(ang_g) * 0.035 + 0.08
    tubo(bm_piezo_base, Vector((gx, gy, Z_ESTROBO + 0.05)), Vector((gx, gy, Z_ESTROBO + 0.11)), 0.004, 6)
caixa(bm_piezo_base, Vector((0.0, +0.08, Z_ESTROBO + 0.115)), (0.07, 0.07, 0.01))


# -----------------------------------------------------------------------------
# Sensor de Telemetria de Vazão e Nível com Boia Móvel ('boia_sensor')
# -----------------------------------------------------------------------------
# Coluna guia na borda interna do pontão leste (x = +0.48, y = -0.15)
bm_sensor_guia = bmesh.new()
bm_boia = bmesh.new()

tubo(bm_sensor_guia, Vector((+0.48, -0.15, -0.25)), Vector((+0.48, -0.15, +0.32)), 0.012, 8)
# Braçadeiras na viga
caixa(bm_sensor_guia, Vector((+0.52, -0.15, +0.18)), (0.08, 0.04, 0.03))
caixa(bm_sensor_guia, Vector((+0.52, -0.15, -0.10)), (0.08, 0.04, 0.03))
# Transdutor de medição no topo com display digital da IA
caixa(bm_sensor_guia, Vector((+0.48, -0.15, +0.35)), (0.06, 0.08, 0.06))

# Boia anular em plástico laranja de alta visibilidade
tubo(bm_boia, Vector((+0.48, -0.15, -0.06)), Vector((+0.48, -0.15, +0.04)), 0.055, 12)
# Haste indicadora graduada
tubo(bm_sensor_guia, Vector((+0.48, -0.15, +0.04)), Vector((+0.48, -0.15, +0.22)), 0.005, 6)


# -----------------------------------------------------------------------------
# Rotor Hidrocinético de 4 Pás Torcidas ('rotor')
# -----------------------------------------------------------------------------
# Centrado na origem de rotação do rotor: montado entre y = -0.45 e +0.35, z = -0.08 m.
# O objeto 'rotor' terá seu pivô exatamente no eixo central: Vector((0.0, 0.0, -0.08)).
# Suas coordenadas locais terão o eixo longitudinal ao longo de Y!
bm_rotor_hub = bmesh.new()
bm_rotor_pas = bmesh.new()

# Eixo central e cubo ogival (em coordenadas relativas ao centro do rotor)
# Extensão em Y de -0.42 a +0.34 m
tubo(bm_rotor_hub, Vector((0.0, -0.38, 0.0)), Vector((0.0, +0.32, 0.0)), 0.055, 14)
# Nariz ogival a montante (reduz arrasto de entrada d'água)
tubo(bm_rotor_hub, Vector((0.0, -0.44, 0.0)), Vector((0.0, -0.38, 0.0)), 0.035, 10)
tubo(bm_rotor_hub, Vector((0.0, -0.47, 0.0)), Vector((0.0, -0.44, 0.0)), 0.015, 8)

# Cubo central reforçado onde as pás se conectam (y de -0.15 a +0.15 m)
tubo(bm_rotor_hub, Vector((0.0, -0.15, 0.0)), Vector((0.0, +0.15, 0.0)), 0.085, 16)
# Anéis de travamento e parafusos de flange
for y_fl in (-0.14, +0.14):
    tubo(bm_rotor_hub, Vector((0.0, y_fl - 0.01, 0.0)), Vector((0.0, y_fl + 0.01, 0.0)), 0.098, 16)
    for k in range(8):
        ang_f = k * (2 * PI / 8)
        fx = math.cos(ang_f) * 0.090
        fz = math.sin(ang_f) * 0.090
        tubo(bm_rotor_pas, Vector((fx, y_fl, fz)), Vector((fx, y_fl + 0.015, fz)), 0.006, 6)

# 4 Pás Helicoidais Hidrocinéticas Torcidas de Alta Eficiência
# Raio máximo das pás: 0.38 m (vão livre entre os pontões é 0.98 m, raio cabe perfeitamente com folga segura)
# Cada pá é modelada com 5 seções transversais torcidas ao longo do raio para simular perfil NACA/Gorlov real
NUM_PAS = 4
RAIO_PA = 0.37
COMPRIMENTO_PA = 0.32  # extensão em Y da pá

for p_idx in range(NUM_PAS):
    ang_base = p_idx * (2 * PI / NUM_PAS)
    
    # Construção de cada seção da pá (da raiz r = 0.08 até a ponta r = RAIO_PA)
    # Com torção aerodinâmica suave: ângulo de ataque varia da raiz para a ponta
    secoes = []
    num_estagios = 5
    for est in range(num_estagios):
        frac = est / (num_estagios - 1)
        r_atual = 0.085 + frac * (RAIO_PA - 0.085)
        # Torção helicoidal (pitch angle diminui em direção à ponta)
        pitch = math.radians(48.0 - frac * 26.0)
        # Largura da corda da pá (afinamento na ponta)
        corda = 0.18 * (1.0 - frac * 0.35)
        espessura = 0.030 * (1.0 - frac * 0.55)
        
        # Posição angular em torno do eixo Y
        ang_s = ang_base + math.radians(frac * 18.0)  # leve arqueamento helicoidal (sweep)
        
        # Centro da seção no plano r-Y
        y_sec = -0.12 + frac * 0.24
        
        # Matriz de orientação local da seção
        # Eixo radial r aponta na direção de ang_s
        rad_dir = Vector((math.cos(ang_s), 0.0, math.sin(ang_s)))
        y_dir = Vector((0.0, 1.0, 0.0))
        tang_dir = rad_dir.cross(y_dir).normalized()
        
        c_pt = rad_dir * r_atual + Vector((0, y_sec, 0))
        
        # 4 vértices do perfil aerodinâmico da seção
        # Inclinado pelo ângulo pitch em torno do vetor radial
        u_corda = (y_dir * math.cos(pitch) + tang_dir * math.sin(pitch)).normalized()
        u_esp = u_corda.cross(rad_dir).normalized()
        
        v0 = c_pt - u_corda * (corda * 0.45) - u_esp * (espessura * 0.5)  # bordo de fuga
        v1 = c_pt + u_corda * (corda * 0.55) - u_esp * (espessura * 0.2)  # bordo de ataque inferior
        v2 = c_pt + u_corda * (corda * 0.55) + u_esp * (espessura * 0.2)  # bordo de ataque superior
        v3 = c_pt - u_corda * (corda * 0.45) + u_esp * (espessura * 0.5)  # bordo de fuga superior
        
        # Vértices no bmesh
        bm_verts = [bm_rotor_pas.verts.new(pt) for pt in (v0, v1, v2, v3)]
        secoes.append(bm_verts)

    # Conectar seções adjacentes com faces
    for s0, s1 in zip(secoes, secoes[1:]):
        # Face inferior
        bm_rotor_pas.faces.new([s0[0], s1[0], s1[1], s0[1]])
        # Bordo de ataque
        bm_rotor_pas.faces.new([s0[1], s1[1], s1[2], s0[2]])
        # Face superior
        bm_rotor_pas.faces.new([s0[2], s1[2], s1[3], s0[3]])
        # Bordo de fuga
        bm_rotor_pas.faces.new([s0[3], s1[3], s1[0], s0[0]])
    
    # Fechamento na ponta da pá (capa hidrodinâmica)
    s_top = secoes[-1]
    bm_rotor_pas.faces.new([s_top[0], s_top[1], s_top[2], s_top[3]])


# -----------------------------------------------------------------------------
# Criação dos Objetos Blender e Materiais
# -----------------------------------------------------------------------------
# 1. Objeto Chassi Flutuante (pai do conjunto estrutural)
o_chassi = obj('catamara', bm_chassi, 'chassi_amarelo')
o_chassi_esc = obj('catamara_escuro', bm_chassi_escuro, 'aco_escuro')
o_chassi_esc.parent = o_chassi
o_chassi_borr = obj('catamara_borracha', bm_chassi_borracha, 'borracha')
o_chassi_borr.parent = o_chassi
o_chassi_met = obj('catamara_metal', bm_chassi_metal, 'aco_gasto')
o_chassi_met.parent = o_chassi
o_chassi_lodo = obj('catamara_lodo', bm_chassi_lodo, 'verde_lodo')
o_chassi_lodo.parent = o_chassi
o_perigo = obj('catamara_perigo', bm_perigo, 'listras')
o_perigo.parent = o_chassi

# 2. Objeto Gerador Elétrico e Superestrutura
o_gen = obj('gerador_corpo', bm_gerador, 'aco_escuro')
o_gen.parent = o_chassi
o_gen_aletas = obj('gerador_aletas', bm_gerador_aletas, 'aluminio')
o_gen_aletas.parent = o_chassi
o_gen_cobre = obj('gerador_cobre', bm_gerador_cobre, 'cobre')
o_gen_cobre.parent = o_chassi
o_gen_cabos = obj('gerador_cabos', bm_gerador_cabos, 'borracha')
o_gen_cabos.parent = o_chassi

# 3. Ressonador Piezoelétrico e Luz
o_piezo_b = obj('piezo_base', bm_piezo_base, 'bronze_naval')
o_piezo_b.parent = o_chassi
o_cristal = obj('cristal_piezo', bm_cristal, 'cristal')
o_cristal.location = P_CRISTAL_CTR
o_cristal.parent = o_chassi
o_luz = obj('luz_topo', bm_luz, 'luz_branca')
o_luz.location = P_LUZ_CTR
o_luz.parent = o_chassi

# 4. Sensor de Telemetria e Boia
o_sensor = obj('sensor_coluna', bm_sensor_guia, 'aco_gasto')
o_sensor.parent = o_chassi
o_boia = obj('boia_sensor', bm_boia, 'laranja_boia')
o_boia.parent = o_chassi

# 5. Rotor Hidrocinético (com pivô em Vector((0, 0, -0.08)))
o_rotor = obj('rotor', bm_rotor_hub, 'aco_escuro')
o_rotor.location = Vector((0.0, 0.0, -0.08))
o_rotor.parent = o_chassi
o_pas = obj('rotor_pas', bm_rotor_pas, 'bronze_naval')
o_pas.parent = o_rotor

# Suavizações
for o in (o_chassi, o_chassi_esc, o_chassi_borr, o_chassi_met, o_gen, o_gen_aletas, o_rotor, o_pas, o_boia, o_luz):
    suavizar(o)


# -----------------------------------------------------------------------------
# Animações em Laço Fechado de 96 Quadros (24 FPS, 4 segundos)
# -----------------------------------------------------------------------------
for f in range(1, QUADROS + 1):
    sc.frame_set(f)
    t = (f - 1) / QUADROS  # 0.0 a 95/96
    ang_ciclo = t * 2 * PI

    # 1. Rotação Contínua do Rotor Hidráulico: 2 voltas completas (720°) em 96 quadros
    o_rotor.rotation_euler = Euler((0.0, ang_ciclo * 2.0, 0.0), 'XYZ')
    o_rotor.keyframe_insert('rotation_euler', frame=f)

    # 2. Oscilação Hidrodinâmica Suave do Chassi Flutuante ('catamara')
    z_chassi = 0.014 * math.sin(ang_ciclo)
    rx_chassi = math.radians(0.75) * math.cos(ang_ciclo)
    ry_chassi = math.radians(0.45) * math.sin(ang_ciclo * 2.0)
    o_chassi.location = Vector((0.0, 0.0, z_chassi))
    o_chassi.rotation_euler = Euler((rx_chassi, ry_chassi, 0.0), 'XYZ')
    o_chassi.keyframe_insert('location', frame=f)
    o_chassi.keyframe_insert('rotation_euler', frame=f)

    # 3. Boia de Medição de Vazão com defasagem de onda
    z_boia = 0.018 * math.sin(ang_ciclo + PI / 3)
    o_boia.location = Vector((0.0, 0.0, z_boia))
    o_boia.keyframe_insert('location', frame=f)

    # 4. Estrobo de Sinalização Fluvial (Piscadas a cada 24 quadros: f=1..3, 25..27, 49..51, 73..75)
    f_rel = (f - 1) % 24
    sz_luz = 1.4 if f_rel < 3 else 1.0
    o_luz.scale = Vector((sz_luz, sz_luz, sz_luz))
    o_luz.keyframe_insert('scale', frame=f)

    # 5. Pulso Harmônico do Cristal Piezoelétrico
    s_cr = 1.0 + 0.08 * math.sin(ang_ciclo * 2.0)
    o_cristal.scale = Vector((s_cr, s_cr, s_cr))
    o_cristal.keyframe_insert('scale', frame=f)


# -----------------------------------------------------------------------------
# Cenário de Contexto Fluvial (Água e Leito para o Render de Foto)
# -----------------------------------------------------------------------------
# Plano de água translúcida estilizada em z = -0.04 m (área 2.6 × 2.6 m)
bm_agua = bmesh.new()
caixa_de(bm_agua, Vector((-1.30, -1.30, -0.05)), Vector((+1.30, +1.30, -0.03)))
o_agua = obj('chao_agua', bm_agua, 'agua_rio')

# Leito de pedras e cascalho subaquático em z = -0.58 m
bm_leito = bmesh.new()
caixa_de(bm_leito, Vector((-1.35, -1.35, -0.65)), Vector((+1.35, +1.35, -0.55)))
for _ in range(14):
    rx = random.uniform(-1.0, 1.0)
    ry = random.uniform(-1.0, 1.0)
    rr = random.uniform(0.04, 0.09)
    pedra(bm_leito, Vector((rx, ry, -0.55)), rr, 6)
o_leito = obj('chao_leito', bm_leito, 'concreto')


# -----------------------------------------------------------------------------
# Iluminação e Câmera Cycles
# -----------------------------------------------------------------------------
sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.4
sol_d.color = (1.0, 0.98, 0.94)
sol_d.angle = math.radians(12.0)
o_sol = bpy.data.objects.new('EFEITO_Sol', sol_d)
sc.collection.objects.link(o_sol)
o_sol.rotation_euler = (math.radians(52), 0, math.radians(-38))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.65, 0.78, 1.0)
bg.inputs['Strength'].default_value = 0.65

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


ALVO = Vector((0.0, 0.0, 0.15))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(25)  # Quadro com boa iluminação e posição das pás

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 2.2), (210, 2.4), (120, 2.3), (30, 2.1))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 4.4, math.sin(a) * 4.4, alt - ALVO.z))
        mirar(pos_cam, ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'turbina_correnteza_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: rotor com pás helicoidais, redutor estanque, gerador superior com aletas e cabos
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(25)
        mirar(Vector((1.65, -1.55, 1.15)), Vector((0.0, -0.10, 0.15)), 35)
        sc.render.filepath = os.path.join(AQUI, 'turbina_correnteza_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(25)
    mirar(ALVO + Vector((2.6, -3.0, 1.4)), ALVO, 36)
    sc.render.filepath = os.path.join(AQUI, 'turbina_correnteza_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('TURBINA_CORRENTEZA ok (%d tris)' % tot_tri)
