"""Estudo isolado (fora do jogo): TURBINA ALTA da IA, 3×3 tiles (lote 14, energia II).
Potência: 600 kW ("conta como +2 níveis de altura no vento"). Prioridade do lote: destrava o Defletor de Vento.
Bocas: — (gerador eólico puro de alta altitude conectado diretamente à rede elétrica).

Evolução monumental da turbina eólica básica (2×2, 200 kW, 3,64 m):
- Base maciça de concreto armado 2,96 × 2,96 m com cantos chanfrados e 4 sapatas de ancoragem estaiada com blocos
  pesados de fixação, manilhas de aço forjado e esticadores tensores duplos com porcas de trava.
- Torre colossal de 3 estágios (altura até o hub: 4,80 m; altura total até o mastro: 5,45 m) em aço corten e primer óxido,
  unida por flanges circulares de 16 parafusos hexagonais maciços.
- Colar intermediário de estais a 3,15 m com 4 cabos de aço galvanizado de alta tensão ancorados na base.
- Cremalheira dentada vertical na face norte para robô de manutenção autônomo da IA (sem escadas humanas).
- Eletrocalhas duplas laterais com feixes de cabos de força blindados e abraçadeiras de latão descendo até a
  subestação transformadora e gabinete inversor na base da torre.
- Mesa de guinada no topo a 4,45 m com coroa dentada forjada e 2 servomotores com pinhões sincronizados girando a nacele.
- Nacele colossal aerodinâmica em amarelo-industrial desgastado com listras de perigo, portas de acesso mecatrônico,
  radiador de óleo com ventoinha aletada giratória, acoplamento elástico e gerador síncrono aletado visível por grelhas.
- Anel de foco harmônico de vento da IA na entrada da nacele com cristal ressonante e luminescência violeta.
- Rotor colossal com cubo aerodinâmico (hub) com sistema mecânico de passo de pá (pitch) hidráulico cromado.
- 3 pás gigantescas em compósito de fibra de carbono e titânio (raio de 1,65 m, envergadura total de 3,30 m),
  com bordas de ataque reforçadas em níquel, winglets defletores nas pontas e fitas de campo de vórtice luminescentes.
- Mastro de telemetria meteorológica no topo da nacele com anemômetro quádruplo giratório, cata-vento de rajada
  e estrobo de advertência aérea piscante a cada 24 quadros.

Peças animadas separadas:
- 'nacele': guinada suave da nacele (+/- 8°) buscando o vento ideal.
- 'helice': rotação contínua e imponente das 3 pás colossais (2 voltas completas por ciclo de 96 quadros).
- 'anemometro': anemômetro quádruplo no mastro girando a 8 voltas por ciclo.
- 'catavento': cata-vento no topo oscilando com as rajadas de alta altitude.
- 'ventoinha_oleo': ventoinha do radiador de óleo da nacele girando velozmente a 6 voltas por ciclo.
- 'pinhao_guinada0', 'pinhao_guinada1': pinhões dos motores rolando na coroa dentada da torre.
- 'cristal_ressonador': cristal de campo eólico emitindo pulso harmônico de luminescência.

Uso: blender -b --python estudo_turbina_alta.py -- foto
     blender -b --python estudo_turbina_alta.py -- nada
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

# Cotas estruturais da Turbina Alta
Z_LAJE = 0.08
Z_PED = 0.28                 # pedestal de concreto central
Z_CHAPA = 0.32               # chapa de aço base da torre
Z_FLANGE1 = 1.80             # união estágio 1 -> 2
Z_COLARES = 3.20             # colar dos estais e união estágio 2 -> 3
Z_TOPO_TORRE = 4.45          # coroa dentada de guinada
Z_HUB = 4.80                 # eixo do rotor colossal
X_HUB = 0.72                 # balanço frontal do rotor
R_PA = 1.65                  # raio das pás (envergadura de 3,30 m)

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

def feixe(bc, ba, pts, n=3, r=0.009, passo=4, lado=Vector((1, 0, 0))):
    for i in range(n):
        off = lado * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 1.2), 12)

# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

def campo_mat():
    m = bpy.data.materials.new('CampoEolico')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.45, 0.15, 1.0, 1)
    em.inputs['Strength'].default_value = 6.0
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.65
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m

base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'torre': mats.material('TorreAlta', (0.45, 0.46, 0.48), 0, 0.48, desgaste=0.9, sujeira=0.9, ferrugem=0.55),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.9, escovado=True),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.9, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'bronze': mats.material('Bronze', (0.55, 0.38, 0.18), 1.0, 0.35, pintura=False, sujeira=0.7),
    'cabo_aco': mats.material('CaboAco', (0.32, 0.31, 0.29), 1.0, 0.45, pintura=False, ferrugem=0.5, sujeira=0.7),
    'pa_carbono': mats.material('FibraCarbono', (0.15, 0.16, 0.18), 0, 0.35, desgaste=0.8, sujeira=0.7),
    'pa_borda': mats.material('NiquelAero', (0.72, 0.74, 0.75), 1.0, 0.25, pintura=False, sujeira=0.5),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Ferrugem', (0.28, 0.10, 0.03), 0, 0.85, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'campo': campo_mat(),
    'cristal': luz_mat('CristalHarmonico', (0.55, 0.2, 1.0), 5.0),
    'estrobo_aviso': luz_mat('EstroboAereo', (1.0, 0.15, 0.05), 15.0),
    'luz_farol': luz_mat('LuzFarol', (0.9, 0.95, 1.0), 12.0),
    'led_verde': luz_mat('LedRede', (0.1, 0.95, 0.2), 8.0),
})

# ------------------------------------------------------------------ LAJE E FUNDAÇÃO ESTAIADA
bm = bmesh.new()
# Laje de concreto armado 2.96 x 2.96 m
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
# Pedestal central octogonal para a torre
cil(bm, Vector((0, 0, (Z_LAJE + Z_PED) / 2)), 0.52, Z_PED - Z_LAJE, lados=8)
# 4 blocos pesados de ancoragem nos cantos para os estais tensores
for cx, cy in ((-1.22, -1.22), (1.22, -1.22), (-1.22, 1.22), (1.22, 1.22)):
    caixa_de(bm, (cx - 0.20, cy - 0.20, Z_LAJE), (cx + 0.20, cy + 0.20, 0.35))
obj('laje_concreto', bm, 'concreto')

# Sapatas de ancoragem de aço e manilhas nos 4 blocos
bm, bmest = bmesh.new(), bmesh.new()
for cx, cy in ((-1.22, -1.22), (1.22, -1.22), (-1.22, 1.22), (1.22, 1.22)):
    # Placa base de aço com parafusos
    caixa_de(bm, (cx - 0.16, cy - 0.16, 0.35), (cx + 0.16, cy + 0.16, 0.38))
    for dx in (-0.12, 0.12):
        for dy in (-0.12, 0.12):
            cil(bm, Vector((cx + dx, cy + dy, 0.39)), 0.012, 0.02, lados=6)
    # Ancoragem estaiada colinear: sapata -> manilha -> esticador -> cabo -> olhal do colar
    p_base = Vector((cx, cy, 0.38))
    dir_canto = Vector((cx, cy, 0)).normalized()
    p_colar = dir_canto * 0.28 + Vector((0, 0, Z_COLARES))
    v_cabo = p_colar - p_base
    
    # Haste da manilha inferior (s de 0.0 a 0.08)
    p_m0 = p_base
    p_m1 = p_base + v_cabo * 0.08
    tubo(bm, p_m0, p_m1, 0.022, 10)
    
    # Corpo do esticador tensor de rosca dupla (s de 0.08 a 0.20)
    p_e0 = p_base + v_cabo * 0.08
    p_e1 = p_base + v_cabo * 0.20
    tubo(bm, p_e0, p_e1, 0.038, 12)
    # Porcas de ajuste do esticador
    cil(bm, p_e0, 0.046, 0.03, v_cabo.normalized(), lados=6)
    cil(bm, p_e1, 0.046, 0.03, v_cabo.normalized(), lados=6)
    
    # Cabo de aço galvanizado de alta tensão (s de 0.20 a 1.00)
    tubo(bmest, p_e1, p_colar, 0.013, 10)
obj('ancoragem_sapatas', bm, 'aco')
obj('estais_cabos_aco', bmest, 'cabo_aco')

# Chapa base da torre com círculo de 24 porcas hexagonais pesadas
bm = bmesh.new()
cil(bm, Vector((0, 0, (Z_PED + Z_CHAPA) / 2)), 0.48, Z_CHAPA - Z_PED, lados=24)
for a in range(24):
    ang = a * 2 * PI / 24
    p_porca = Vector((0.44 * math.cos(ang), 0.44 * math.sin(ang), Z_CHAPA + 0.015))
    cil(bm, p_porca, 0.014, 0.03, lados=6)
obj('torre_chapa_base', bm, 'aco')

# ------------------------------------------------------------------ SUBESTAÇÃO E GABINETE INVERSOR AO PÉ DA TORRE
# Posicionado no quadrante sul (y ~ -0.90 m)
bm, bmcob, bmf = bmesh.new(), bmesh.new(), bmesh.new()
Y_INV = -0.90
caixa_de(bm, (-0.42, Y_INV - 0.28, Z_LAJE), (0.42, Y_INV + 0.28, 0.72))
# Portas industriais com aletas de ventilação
for x_p in (-0.20, 0.20):
    caixa_de(bm, (x_p - 0.18, Y_INV - 0.29, 0.14), (x_p + 0.18, Y_INV - 0.27, 0.68))
    for jz in range(5):
        caixa_de(bmf, (x_p - 0.14, Y_INV - 0.295, 0.22 + jz * 0.08), (x_p + 0.14, Y_INV - 0.285, 0.26 + jz * 0.08))
# Barramentos de cobre e isoladores cerâmicos conectando à torre
for dx in (-0.15, 0.0, 0.15):
    for iz in range(3):
        cil(bm, Vector((dx, Y_INV + 0.15, 0.74 + iz * 0.04)), 0.03 - iz * 0.005, 0.03, lados=12)
    tubo(bmcob, Vector((dx, Y_INV + 0.15, 0.85)), Vector((dx * 0.5, -0.42, 0.85)), 0.012, 10)
# Faixas de perigo zebradas no armário
caixa_de(bmf, (-0.43, Y_INV - 0.29, 0.08), (0.43, Y_INV - 0.28, 0.12))
obj('inversor_gabinete', bm, 'grafite')
obj('inversor_detalhes', bmf, 'listras')
obj('inversor_barramentos', bmcob, 'cobre')

# ------------------------------------------------------------------ TORRE TUBULAR COLOSSAL (3 ESTÁGIOS)
bm, bmf_torre = bmesh.new(), bmesh.new()

# Estágio 1 (z = 0.32 até 1.80 m): raio afilando de 0.36 para 0.29 m
bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.36, radius2=0.29, depth=Z_FLANGE1 - Z_CHAPA,
                      matrix=Matrix.Translation((0, 0, (Z_CHAPA + Z_FLANGE1) / 2)))
# Flange 1 a 1.80 m
cil(bmf_torre, Vector((0, 0, Z_FLANGE1)), 0.34, 0.05, lados=24)
for a in range(16):
    ang = a * 2 * PI / 16
    cil(bmf_torre, Vector((0.315 * math.cos(ang), 0.315 * math.sin(ang), Z_FLANGE1)), 0.012, 0.06, lados=6)

# Estágio 2 (z = 1.80 até 3.20 m): raio afilando de 0.29 para 0.23 m
bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.29, radius2=0.23, depth=Z_COLARES - Z_FLANGE1,
                      matrix=Matrix.Translation((0, 0, (Z_FLANGE1 + Z_COLARES) / 2)))
# Colar maciço dos estais a 3.20 m com 4 olhais salientes
cil(bmf_torre, Vector((0, 0, Z_COLARES)), 0.28, 0.08, lados=24)
for a in range(4):
    ang = a * PI / 2 + PI / 4
    d_olhal = Vector((math.cos(ang), math.sin(ang), 0))
    caixa(bmf_torre, d_olhal * 0.30 + Vector((0, 0, Z_COLARES)), (0.08, 0.04, 0.08), Matrix.Rotation(ang, 3, 'Z'))

# Estágio 3 (z = 3.20 até 4.45 m): raio afilando de 0.23 para 0.18 m
bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.23, radius2=0.18, depth=Z_TOPO_TORRE - Z_COLARES,
                      matrix=Matrix.Translation((0, 0, (Z_COLARES + Z_TOPO_TORRE) / 2)))
# Flange superior da mesa de guinada a 4.45 m
cil(bmf_torre, Vector((0, 0, Z_TOPO_TORRE)), 0.25, 0.06, lados=24)

# Cremalheira vertical mecatrônica na face norte (para robô de manutenção)
for iz in range(40):
    z_dente = 0.40 + iz * 0.10
    caixa_de(bmf_torre, (-0.03, 0.26 - (iz/40)*0.10, z_dente - 0.015),
                        (0.03, 0.30 - (iz/40)*0.10, z_dente + 0.015))
# Trilhos guia da cremalheira
tubo(bmf_torre, Vector((-0.05, 0.34, 0.35)), Vector((-0.05, 0.19, Z_TOPO_TORRE)), 0.012, 8)
tubo(bmf_torre, Vector((0.05, 0.34, 0.35)), Vector((0.05, 0.19, Z_TOPO_TORRE)), 0.012, 8)

# Eletrocalhas descendo com cabos de força na face leste
tubo(bmf_torre, Vector((0.36, 0, 0.35)), Vector((0.19, 0, Z_TOPO_TORRE)), 0.022, 10)
# Escorridos de ferrugem e graxa na torre
for k in range(4):
    ang = k * PI / 2
    d_esc = Vector((math.cos(ang), math.sin(ang), 0))
    caixa(bmf_torre, d_esc * 0.30 + Vector((0, 0, 2.2)), (0.002, 0.03, 0.6), Matrix.Rotation(ang, 3, 'Z'))

obj('torre_corpo', bm, 'torre')
obj('torre_reforcos', bmf_torre, 'aco')

# Coroa dentada fixa de guinada no topo da torre (z = 4.45 a 4.58 m)
bm = bmesh.new()
casca(bm, (0, 0, 0), 0.25, 0.17, Z_TOPO_TORRE, Z_TOPO_TORRE + 0.12, 32)
# Dentes da coroa
for a in range(32):
    ang = a * 2 * PI / 32
    d_dente = Vector((math.cos(ang), math.sin(ang), 0))
    caixa(bm, d_dente * 0.24 + Vector((0, 0, Z_TOPO_TORRE + 0.06)), (0.018, 0.014, 0.10), Matrix.Rotation(ang, 3, 'Z'))
obj('coroa_guinada_fixa', bm, 'aco')

# ------------------------------------------------------------------ NACELE COLOSSAL E MOTORES DE GUINADA
nacele = bpy.data.objects.new('nacele', None)
sc.collection.objects.link(nacele)
nacele.location = Vector((0, 0, Z_TOPO_TORRE + 0.10))

bm, bmg, bmf_nac = bmesh.new(), bmesh.new(), bmesh.new()
# Mesa giratória da nacele
cil(bm, Vector((0, 0, 0.02)), 0.26, 0.05, Z_VEC, lados=24)

# Corpo principal da nacele (comprimento X de -1.10 a +0.65 m, largura Y de -0.32 a +0.32 m)
# Formato aerodinâmico afunilado para trás
caixa_de(bm, (-0.60, -0.30, 0.05), (0.50, 0.30, 0.65))
# Seção traseira afunilada
bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.30, radius2=0.14, depth=0.55,
                      matrix=Matrix.Translation((-0.85, 0, 0.35)) @ Matrix.Rotation(PI/2, 3, 'Y').to_4x4())
# Nariz dianteiro com anel de acoplamento do rotor
cil(bmg, Vector((0.55, 0, 0.35)), 0.24, 0.15, Vector((1, 0, 0)), lados=24)

# Grelhas de ventilação do gerador e portas mecatrônicas
for y_side in (-0.31, 0.31):
    for jz in range(4):
        caixa_de(bmf_nac, (-0.35, y_side - 0.005, 0.18 + jz * 0.10), (0.25, y_side + 0.005, 0.24 + jz * 0.10))
# Faixas de perigo nas laterais
caixa_de(bmf_nac, (-0.55, -0.31, 0.08), (0.45, -0.30, 0.14))
caixa_de(bmf_nac, (-0.55, 0.30, 0.08), (0.45, 0.31, 0.14))

# Radiador de óleo no teto da nacele
X_RO, Y_RO, Z_RO = -0.25, 0.0, 0.65
caixa_de(bm, (X_RO - 0.22, Y_RO - 0.18, Z_RO), (X_RO + 0.22, Y_RO + 0.18, Z_RO + 0.10))
casca(bm, (X_RO, Y_RO, 0), 0.16, 0.13, Z_RO + 0.10, Z_RO + 0.18, 20)
# Mangueiras de óleo de alta pressão conectando à multiplicadora
mangueira(bm, [Vector((X_RO - 0.18, 0.10, Z_RO + 0.05)), Vector((X_RO - 0.30, 0.18, Z_RO)),
               Vector((0.15, 0.18, 0.35))], 0.014)

# Faróis de inspeção mecatrônica da IA apontados para a frente/baixo
bm_farol, bm_luz = bmesh.new(), bmesh.new()
dir_farol = Vector((1.0, 0.0, -0.45)).normalized()
for y_ref in (-0.22, 0.22):
    p_ref = Vector((0.44, y_ref, 0.05))
    cil(bm_farol, p_ref, 0.038, 0.05, dir_farol, lados=12)
    cil(bm_luz, p_ref + dir_farol * 0.026, 0.032, 0.008, dir_farol, lados=12)
obj('nacele_farois_carcaca', bm_farol, 'grafite', nacele)
obj('nacele_farois_luz', bm_luz, 'luz_farol', nacele)

# Dois manômetros de óleo e pressão com visores de latão na lateral esquerda
bm_man = bmesh.new()
for j_man, x_man in enumerate((-0.10, 0.10)):
    cil(bm_man, Vector((x_man, 0.315, 0.42)), 0.032, 0.02, Vector((0, 1, 0)), lados=12)
obj('nacele_manometros', bm_man, 'latao', nacele)

obj('nacele_carcaca', bm, 'amarelo', nacele)
obj('nacele_estrutura', bmg, 'grafite', nacele)
obj('nacele_detalhes', bmf_nac, 'listras', nacele)

# Ventoinha de resfriamento de óleo no teto da nacele
ventoinha_oleo = bpy.data.objects.new('ventoinha_oleo', None)
sc.collection.objects.link(ventoinha_oleo)
ventoinha_oleo.parent = nacele
ventoinha_oleo.location = Vector((X_RO, Y_RO, Z_RO + 0.14))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.03, 0.02, Z_VEC, lados=12)
for k in range(5):
    ang = k * 2 * PI / 5
    rot_p = Matrix.Rotation(ang, 3, 'Z') @ Matrix.Rotation(0.35, 3, 'X')
    caixa(bm, rot_p @ Vector((0.065, 0, 0)), (0.07, 0.025, 0.004), rot_p)
obj('ventoinha_oleo_mesh', bm, 'aluminio', ventoinha_oleo)

# Pinhões dos servomotores de guinada (engrenam na coroa fixa)
pinhao0 = bpy.data.objects.new('pinhao_guinada0', None)
sc.collection.objects.link(pinhao0)
pinhao0.parent = nacele
pinhao0.location = Vector((0.0, -0.24, -0.04))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.035, 0.08, Z_VEC, lados=12)
obj('pinhao0_mesh', bm, 'bronze', pinhao0)

pinhao1 = bpy.data.objects.new('pinhao_guinada1', None)
sc.collection.objects.link(pinhao1)
pinhao1.parent = nacele
pinhao1.location = Vector((0.0, 0.24, -0.04))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.035, 0.08, Z_VEC, lados=12)
obj('pinhao1_mesh', bm, 'bronze', pinhao1)

# ------------------------------------------------------------------ ANEL DE FOCO HARMÔNICO DA IA (Ressonância Eólica)
# Localizado no pescoço entre a nacele e o rotor
bm, bmc = bmesh.new(), bmesh.new()
# Anel toroidal de foco quântico
toro_pts = []
for a in range(24):
    ang = a * 2 * PI / 24
    d = Vector((0, math.cos(ang), math.sin(ang)))
    toro_pts.append(d * 0.35)
for p0, p1 in zip(toro_pts, toro_pts[1:] + [toro_pts[0]]):
    tubo(bm, p0 + Vector((0.52, 0, 0.35)), p1 + Vector((0.52, 0, 0.35)), 0.016, 8)
# Cristal ressonador montado no foco
hexa(bmc, Vector((0.52, 0, 0.35)), 0.04, -0.05, 0.05, ponta=0.03)
obj('anel_foco_armacao', bm, 'latao', nacele)
cristal_res = obj('cristal_ressonador', bmc, 'cristal', nacele)

# ------------------------------------------------------------------ MASTRO DE TELEMETRIA E ANEMÔMETRO (Topo da nacele)
X_MAS, Y_MAS, Z_MAS = -0.55, 0.0, 0.65
bm = bmesh.new()
# Mastro tubular estaiado
tubo(bm, Vector((X_MAS, Y_MAS, Z_MAS)), Vector((X_MAS, Y_MAS, Z_MAS + 0.45)), 0.014, 10)
# Estais do mastro
for dy in (-0.14, 0.14):
    tubo(bm, Vector((X_MAS, dy, Z_MAS)), Vector((X_MAS, Y_MAS, Z_MAS + 0.30)), 0.005, 6)
# Estrobo aéreo no topo
cil(bm, Vector((X_MAS, Y_MAS, Z_MAS + 0.46)), 0.025, 0.03, Z_VEC, lados=12)
obj('mastro_telemetria', bm, 'aco', nacele)

# Luz do estrobo aéreo
estrobo_data = bpy.data.lights.new('LuzEstrobo', 'POINT')
estrobo_data.energy = 45.0
estrobo_data.color = (1.0, 0.2, 0.05)
estrobo_obj = bpy.data.objects.new('EFEITO_LuzEstrobo', estrobo_data)
sc.collection.objects.link(estrobo_obj)
estrobo_obj.parent = nacele
estrobo_obj.location = Vector((X_MAS, Y_MAS, Z_MAS + 0.48))

# Anemômetro quádruplo de conchas
anemometro = bpy.data.objects.new('anemometro', None)
sc.collection.objects.link(anemometro)
anemometro.parent = nacele
anemometro.location = Vector((X_MAS, Y_MAS, Z_MAS + 0.36))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.012, 0.03, Z_VEC, lados=8)
for a in range(4):
    ang = a * PI / 2
    d_br = Vector((math.cos(ang), math.sin(ang), 0))
    tubo(bm, Vector((0, 0, 0)), d_br * 0.10, 0.004, 6)
    # Concha hemisférica
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.022,
                              matrix=Matrix.Translation(d_br * 0.10))
obj('anemometro_conchas', bm, 'aluminio', anemometro)

# Cata-vento de rajada
catavento = bpy.data.objects.new('catavento', None)
sc.collection.objects.link(catavento)
catavento.parent = nacele
catavento.location = Vector((X_MAS + 0.12, Y_MAS, Z_MAS + 0.32))
bm = bmesh.new()
tubo(bm, Vector((0, 0, 0)), Vector((0, 0, 0.08)), 0.005, 6)
tubo(bm, Vector((-0.08, 0, 0.08)), Vector((0.08, 0, 0.08)), 0.004, 6)
# Barbatana triangular
caixa_de(bm, (-0.08, -0.002, 0.05), (-0.04, 0.002, 0.12))
# Ponta de flecha
bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.015, radius2=0.0, depth=0.04,
                      matrix=Matrix.Translation((0.09, 0, 0.08)) @ Matrix.Rotation(PI/2, 3, 'Y').to_4x4())
obj('catavento_flecha', bm, 'latao', catavento)

# ------------------------------------------------------------------ ROTOR COLOSSAL E 3 PÁS DE ALTA ALTITUDE
# Objeto giratório do rotor (centrado no hub em x = +0.72 m em relação ao centro da torre)
rotor_obj = bpy.data.objects.new('helice', None)
sc.collection.objects.link(rotor_obj)
rotor_obj.parent = nacele
rotor_obj.location = Vector((0.68, 0, 0.35))

bm_hub, bm_pas, bm_campo, bm_mats = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

# Nariz ogival aerodinâmico (cubo / spinner) em amarelo industrial
bmesh.ops.create_cone(bm_hub, cap_ends=True, segments=24, radius1=0.22, radius2=0.02, depth=0.38,
                      matrix=Matrix.Translation((0.19, 0, 0)) @ Matrix.Rotation(PI/2, 3, 'Y').to_4x4())
# Colar do hub com mancal
cil(bm_hub, Vector((-0.02, 0, 0)), 0.23, 0.08, Vector((1, 0, 0)), lados=24)

# 3 Pás monumentais defasadas em 120°
for i_pa in range(3):
    ang_pa = i_pa * 2 * PI / 3
    rot_pa = Matrix.Rotation(ang_pa, 3, 'X')
    
    # Raiz da pá cilíndrica com atuador de passo (pitch)
    p_raiz = rot_pa @ Vector((0, 0.20, 0))
    cil(bm_hub, p_raiz, 0.065, 0.08, rot_pa @ Vector((0, 1, 0)), lados=16)
    # Pistão cromado de ajuste de passo
    tubo(bm_mats, p_raiz + Vector((0.04, 0, 0)), p_raiz + rot_pa @ Vector((0.04, 0.06, 0)), 0.014, 10)
    
    # Perfil aerodinâmico da pá ao longo do raio (y de 0.20 até 1.65 m)
    # Modelada em fatias com torção aerodinâmica e afinamento
    fatias = [
        (0.24, 0.16, 0.050, 0.22),    # r, corda, espessura, torção (rad)
        (0.60, 0.22, 0.042, 0.16),
        (1.05, 0.18, 0.032, 0.10),
        (1.45, 0.12, 0.022, 0.05),
        (1.65, 0.06, 0.012, 0.00),    # ponta com winglet
    ]
    aneis_pa = []
    for r_f, corda, esp, torc in fatias:
        rot_fat = rot_pa @ Matrix.Rotation(torc, 3, 'Y')
        # 4 vértices do perfil aerodinâmico
        v0 = rot_pa @ Vector((-corda*0.35, r_f, -esp*0.5))
        v1 = rot_pa @ Vector(( corda*0.65, r_f, -esp*0.2))  # bordo de fuga
        v2 = rot_pa @ Vector(( corda*0.65, r_f,  esp*0.2))
        v3 = rot_pa @ Vector((-corda*0.35, r_f,  esp*0.5))  # bordo de ataque arredondado
        pts_fat = [bm_pas.verts.new(p) for p in (v0, v1, v2, v3)]
        aneis_pa.append(pts_fat)
        
    # Unir as fatias formando o corpo da pá em fibra de carbono
    for A, B in zip(aneis_pa, aneis_pa[1:]):
        for j in range(4):
            bm_pas.faces.new((A[j], A[(j+1)%4], B[(j+1)%4], B[j]))
    # Fechar a ponta da pá
    bm_pas.faces.new(aneis_pa[-1])
    
    # Winglet defletor na ponta (dobrado para trás e para cima)
    p_ponta = rot_pa @ Vector((0, 1.65, 0))
    p_wing = p_ponta + rot_pa @ Vector((-0.06, 0.04, 0.12))
    tubo(bm_pas, p_ponta, p_wing, 0.018, 8)
    
    # Borda de ataque reforçada em níquel aeroespacial
    p_ataque0 = rot_pa @ Vector((-0.08, 0.25, 0))
    p_ataque1 = rot_pa @ Vector((-0.03, 1.64, 0))
    tubo(bm_mats, p_ataque0, p_ataque1, 0.012, 8)
    
    # Fita de campo harmônico violeta na borda de fuga
    p_fuga0 = rot_pa @ Vector((0.14, 0.30, 0))
    p_fuga1 = rot_pa @ Vector((0.08, 1.62, 0))
    tubo(bm_campo, p_fuga0, p_fuga1, 0.008, 6)

    # Geradores de vórtice aerodinâmicos (aletas triangulares no extradorso)
    for k_vg in range(6):
        r_vg = 0.50 + k_vg * 0.18
        p_vg = rot_pa @ Vector((-0.02, r_vg, 0.025))
        caixa(bm_pas, p_vg, (0.015, 0.003, 0.012), rot_pa)

obj('hub_spinner', bm_hub, 'amarelo', rotor_obj)
obj('rotor_pas_carbono', bm_pas, 'pa_carbono', rotor_obj)
obj('rotor_bordas_reforco', bm_mats, 'pa_borda', rotor_obj)
obj('rotor_fita_campo', bm_campo, 'campo', rotor_obj)

# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço fechado a 24 fps)
em_cristal = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']

for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS                     # progresso 0..1 do ciclo
    fase = 2 * PI * t
    
    # 1. Rotação das pás colossais: 2 voltas completas por ciclo (suave e imponente)
    ang_helice = fase * 2
    rotor_obj.rotation_euler = Euler((ang_helice, 0, 0), 'XYZ')
    rotor_obj.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Guinada suave da nacele (oscilação lenta em Z de +/- 6° acompanhando a variação do vento)
    ang_guinada = 0.10 * math.sin(fase)
    nacele.rotation_euler = Euler((0, 0, ang_guinada), 'XYZ')
    nacele.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Pinhões de guinada rolando sincronizados na coroa
    pinhao0.rotation_euler = Euler((0, 0, ang_guinada * 8), 'XYZ')
    pinhao1.rotation_euler = Euler((0, 0, ang_guinada * 8), 'XYZ')
    pinhao0.keyframe_insert('rotation_euler', frame=q)
    pinhao1.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Ventoinha do radiador de óleo: rotação ultra-rápida (6 voltas por ciclo)
    ventoinha_oleo.rotation_euler = Euler((0, 0, fase * 6), 'XYZ')
    ventoinha_oleo.keyframe_insert('rotation_euler', frame=q)
    
    # 5. Anemômetro de conchas no mastro: 8 voltas por ciclo
    anemometro.rotation_euler = Euler((0, 0, -fase * 8), 'XYZ')
    anemometro.keyframe_insert('rotation_euler', frame=q)
    
    # 6. Cata-vento oscilando na rajada
    catavento.rotation_euler = Euler((0, 0, 0.25 * math.cos(fase * 2)), 'XYZ')
    catavento.keyframe_insert('rotation_euler', frame=q)
    
    # 7. Pulso harmônico de ressonância no cristal de campo eólico
    pulso_w = 0.5 + 0.5 * math.sin(fase * 4)
    em_cristal.default_value = 3.0 + 4.0 * pulso_w
    em_cristal.keyframe_insert('default_value', frame=q)
    
    # 8. Estrobo aéreo de alta altitude piscando periodicamente a cada 24 quadros (1 s)
    fase_estrobo = (q % 24) / 24.0
    luz_on = 1.0 if fase_estrobo < 0.15 else 0.02
    estrobo_data.energy = 45.0 * luz_on
    estrobo_data.keyframe_insert('energy', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (16, 16, 1.0))
obj('EFEITO_chao', bm, 'chao')

# Luz Solar
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
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

# Para enquadrar a turbina colossal (5,45 m de altura) e a base 3x3 tiles
ALVO = (0.0, 0.0, 2.70)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'TURBINA_ALTA_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos com distância suficiente para enquadrar a torre monumental
    for i, (ang, alt, dist, tq) in enumerate(((300, 4.2, 7.8, 0.25),
                                             (215, 3.8, 7.8, 0.50),
                                             (120, 4.5, 7.8, 0.75),
                                             (35,  3.6, 7.8, 0.95))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * dist, math.sin(a) * dist, alt - ALVO[2])), ALVO, 32)
        sc.render.filepath = os.path.join(AQUI, f'turbina_alta_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na nacele colossal, hub, anel de foco harmônico e telemetria
    sc.frame_set(int(0.25 * FPS) + 1)
    mirar((2.40, -1.80, 5.25), (0.45, 0.0, 4.80), 38)
    sc.render.filepath = os.path.join(AQUI, 'turbina_alta_perto.png')
    bpy.ops.render.render(write_still=True)

print('TURBINA_ALTA ok')
