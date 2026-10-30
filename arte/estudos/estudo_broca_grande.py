"""Estudo isolado (fora do jogo): broca grande, 3×3 tiles.
Plataforma pesada de perfuração contínua e mineração de alto rendimento:
- Tamanho: 3×3 tiles (área 2.88 × 2.88 m, deck de 2.96 × 2.96 m).
- Saída de minério no Sul: x = 0.0 m, y = -1.44 m, z = 0.23 m (esteira industrial de roletes).
- Entrada de fluido Oeste (supressão de poeira / névoa hídrica): x = -1.44 m, y = 0.0 m, z = 0.35 m com flange padrão.
- Grande cabeça de corte rotativa multifacetada com dentes de carboneto de tungstênio, descendo e girando no solo.
- Quatro pistões hidráulicos maciços de avanço vertical com hastes cromadas e mangueiras trançadas.
- Peneira vibratória e britador cônico primário integrados no fluxo de minério.
- Unidade de força com radiador duplo, ventiladores axiais e chaminé alta com silenciador.
- Fenômeno da IA: emissor de ressonância acústico-piezoelétrica na cabeça motriz que micro-fratura a rocha.

Uso: blender -b --python estudo_broca_grande.py -- foto | video | perto | nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço fechado
VOLTAS = 8                   # voltas da cabeça de corte por ciclo
DECK = 0.28                  # cota do piso do chassi
FURO = Vector((0.0, 0.15, 0)) # centro da perfuração
Z_ALTO, Z_BAIXO = 2.45, 1.45  # curso vertical da cabeça
random.seed(64)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
Z0 = 0.08
Z_P = 0.35                   # altura padrão das bocas de fluido (e esteiras a z = 0.23 m)


def suavizar(o):
    """Sombra suave nas laterais (quads) mantendo tampas planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def curva(bm, p, r, lados=12):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=6, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, bp, pts, r, folga=0.08):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 14)
    for c in pts[1:-1]:
        curva(bm, c, r, 14)


def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def fumaca_grad_mat(nome, dens, z0, z1):
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    no = mats.no
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.012, 0.011, 0.011, 1)
    mix.inputs[7].default_value = (0.42, 0.42, 0.43, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


base3d.M.update({
    'amarelo_broca': mats.material('Amarelo Mineração', (0.74, 0.46, 0.04), 0, 0.42, desgaste=1.2, sujeira=1.0, ferrugem=0.6),
    'primer_oxido': mats.material('Primer Óxido', (0.36, 0.10, 0.06), 0, 0.65, desgaste=0.8, sujeira=0.9, ferrugem=0.8),
    'aco_pesado': mats.material('Aço Pesado', (0.35, 0.36, 0.38), 1.0, 0.42, pintura=False, ferrugem=0.8, sujeira=0.9, escovado=True),
    'trado_aco': mats.material('Aço Carboneto Trado', (0.28, 0.28, 0.30), 1.0, 0.35, pintura=False, ferrugem=0.6, sujeira=0.9),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'rocha': mats.material('Rocha Fragmentada', (0.17, 0.14, 0.11), 0, 0.9, sujeira=0.5, desgaste=0.0),
    'minerio': mats.material('Minério Puro', (0.32, 0.12, 0.06), 0.2, 0.7, pintura=False, sujeira=0.5, ferrugem=0.5),
    'terra': mats.material('Terra Revolvida', (0.11, 0.085, 0.065), 0, 0.95, sujeira=0.4, desgaste=0.0),
    'escuro': mats.material('Furo Poço', (0.01, 0.008, 0.006), 0, 1.0, sujeira=0.0, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.16, 0.11, 0.07), 0, 0.35, pintura=False, sujeira=0.3, desgaste=0.0),
    'cristal_ia': luz_mat('Cristal Piezo IA', (0.15, 0.85, 1.0), 9.0),
    'listras': base3d.listras_mat(),
    'fumaca': fumaca_grad_mat('Fumaça Diesel', 8.0, 1.8, 3.8),
    'poeira': base3d.volume_mat('Névoa Supressão', (0.50, 0.45, 0.38), 3.5, 0.2, 1.4),
})

# ------------------------------------------------------------------ CHASSI 3×3, SAPATAS ESTABILIZADORAS E PISO DECK
bm_chassi = bmesh.new()
# longarinas e travessas pesadas em perfil I estrutural
for x in (-1.35, -0.45, 0.45, 1.35):
    caixa_de(bm_chassi, (x - 0.06, -1.44, 0.10), (x + 0.06, 1.44, 0.13))
    caixa_de(bm_chassi, (x - 0.016, -1.44, 0.13), (x + 0.016, 1.44, DECK - 0.02))
    caixa_de(bm_chassi, (x - 0.06, -1.44, DECK - 0.02), (x + 0.06, 1.44, DECK))
for y in (-1.35, -0.65, 0.15, 0.85, 1.35):
    caixa_de(bm_chassi, (-1.35, y - 0.04, 0.12), (1.35, y + 0.04, DECK))
obj('chassi_vigas', bm_chassi, 'grafite')

# piso de chapa xadrez com recorte central do poço de perfuração
bm_piso = bmesh.new()
A_FURO_R = 0.55
caixa_de(bm_piso, (-1.44, -1.44, DECK), (1.44, 1.44, DECK + 0.02))
obj('piso_deck', bm_piso, 'aco_pesado')

# listras zebradas nas bordas do chassi
bm_list = bmesh.new()
for s in (-1, 1):
    caixa_de(bm_list, (-1.45, s * 1.43 - 0.01, DECK + 0.021), (1.45, s * 1.43 + 0.01, DECK + 0.023))
    caixa_de(bm_list, (s * 1.43 - 0.01, -1.45, DECK + 0.021), (s * 1.43 + 0.01, 1.45, DECK + 0.023))
obj('piso_listras', bm_list, 'listras')

# 4 sapatas estabilizadoras hidráulicas articuladas nos 4 cantos
bm_sap, bm_has_sap = bmesh.new(), bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1):
        p_sap = Vector((sx * 1.35, sy * 1.35, 0))
        # braço estrutural
        viga(bm_sap, Vector((sx * 1.15, sy * 1.15, DECK)), p_sap + Vector((0, 0, 0.35)), 0.08)
        # cilindro hidráulico
        cil(bm_sap, p_sap + Vector((0, 0, 0.32)), 0.065, 0.28, lados=14)
        # haste cromada
        cil(bm_has_sap, p_sap + Vector((0, 0, 0.12)), 0.038, 0.26, lados=12)
        # prato da sapata no chão
        caixa(bm_sap, p_sap + Vector((0, 0, 0.02)), (0.24, 0.24, 0.04))
obj('sapatas_estabilizadoras', bm_sap, 'amarelo_broca')
obj('sapatas_hastes', bm_has_sap, 'cromo')

# ------------------------------------------------------------------ POÇO DE PERFURAÇÃO, COLAR E MANCHAS DE DETRITOS
bm_colar = bmesh.new()
cil(bm_colar, FURO + Vector((0, 0, DECK + 0.04)), 0.45, 0.10, lados=28)
cil(bm_colar, FURO + Vector((0, 0, DECK + 0.09)), 0.49, 0.03, lados=28)
# bicos de aspersão de névoa d'água no colar
for k in range(8):
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    cil(bm_colar, FURO + d * 0.46 + Vector((0, 0, DECK + 0.10)), 0.015, 0.03, d, lados=8)
obj('colar_poco', bm_colar, 'aco_pesado')

bm_esc = bmesh.new()
cil(bm_esc, FURO + Vector((0, 0, DECK + 0.091)), 0.40, 0.002, lados=28)
obj('boca_escura', bm_esc, 'escuro')

# detritos de rocha e minério ao redor do colar
bm_det, bm_det_min = bmesh.new(), bmesh.new()
for k in range(60):
    a = random.uniform(0, 2 * PI)
    r = 0.48 + abs(random.gauss(0, 0.15))
    c = FURO + Vector((math.cos(a) * r, math.sin(a) * r, DECK + 0.02))
    pedra(bm_det_min if random.random() < 0.35 else bm_det, c, random.uniform(0.015, 0.045))
obj('detritos_rocha', bm_det, 'rocha')
obj('detritos_minerio', bm_det_min, 'minerio')

# ------------------------------------------------------------------ TORRE DUPLA DE IÇAMENTO TRELIÇADA (ALTURA Z = 3.65 m)
# Dois grandes pórticos verticais treliçados: um a leste (x = 0.65) e um a oeste (x = -0.65)
Z_TOPO_TORRE = 3.65
bm_torre = bmesh.new()
for sx in (-0.65, 0.65):
    for dy in (-0.35, 0.35):
        # montantes tubulares de canto
        viga(bm_torre, Vector((sx - 0.04, FURO.y + dy, DECK)), Vector((sx - 0.04, FURO.y + dy, Z_TOPO_TORRE)), 0.05)
        viga(bm_torre, Vector((sx + 0.04, FURO.y + dy, DECK)), Vector((sx + 0.04, FURO.y + dy, Z_TOPO_TORRE)), 0.05)
    # treliças diagonais e horizontais
    for zt in (0.8, 1.4, 2.0, 2.6, 3.2):
        caixa(bm_torre, Vector((sx, FURO.y, zt)), (0.12, 0.72, 0.035))
        viga(bm_torre, Vector((sx, FURO.y - 0.35, zt)), Vector((sx, FURO.y + 0.35, zt + 0.6)), 0.025)
# viga-ponte transversal superior unindo as duas torres no topo
caixa_de(bm_torre, (-0.75, FURO.y - 0.40, Z_TOPO_TORRE), (0.75, FURO.y + 0.40, Z_TOPO_TORRE + 0.14))
# polias de içamento no topo
for sx in (-0.30, 0.30):
    cil(bm_torre, Vector((sx, FURO.y, Z_TOPO_TORRE + 0.22)), 0.14, 0.05, Vector((1, 0, 0)), lados=18)
obj('torre_trelicada', bm_torre, 'amarelo_broca')

# ------------------------------------------------------------------ CABEÇA MOTRIZ E TRADO TRIPLO DE PERFURAÇÃO (MÓVEL)
# Objeto animado verticalmente que desce de Z_ALTO (2.45) a Z_BAIXO (1.45)
o_cabeca = bpy.data.objects.new('cabeca_motriz', None)
sc.collection.objects.link(o_cabeca)
o_cabeca.location = Vector((FURO.x, FURO.y, Z_ALTO))

bm_cm = bmesh.new()
# caixa de transmissão e redutores planetários
caixa_de(bm_cm, (-0.52, -0.42, -0.22), (0.52, 0.42, 0.18))
# 2 motores elétricos/hidráulicos aletados no topo da cabeça
for sx in (-0.28, 0.28):
    cil(bm_cm, Vector((sx, 0.0, 0.35)), 0.16, 0.36, lados=20)
    for k in range(6):
        cil(bm_cm, Vector((sx, 0.0, 0.24 + k * 0.04)), 0.18, 0.010, lados=20)
# mancais e patins que deslizam nos trilhos das torres
for sx in (-0.60, 0.60):
    caixa(bm_cm, (sx, 0.0, 0.0), (0.12, 0.65, 0.35))
obj('cabeca_corpo', bm_cm, 'amarelo_broca', o_cabeca)

# cristal piezo-harmônico da IA acoplado no centro da cabeça motriz
bm_cr = bmesh.new()
bmesh.ops.create_icosphere(bm_cr, subdivisions=1, radius=0.075)
obj('cristal_piezo_ia', bm_cr, 'cristal_ia', o_cabeca)

# Eixo rotativo do trado (gira 8 voltas por ciclo sob a cabeça motriz)
o_trado = bpy.data.objects.new('trado_rotativo', None)
sc.collection.objects.link(o_trado)
o_trado.parent = o_cabeca
o_trado.location = Vector((0, 0, -0.22))

bm_trado = bmesh.new()
COMP_TRADO = 3.2
# tubo central maciço
cil(bm_trado, Vector((0, 0, -COMP_TRADO / 2)), 0.09, COMP_TRADO, lados=16)
# grande hélice de corte espiral dupla
PASSO_H, R0_H, R1_H = 0.24, 0.088, 0.36
n_seg = int(COMP_TRADO / PASSO_H * 24)
ant1, ant2 = None, None
for i in range(n_seg + 1):
    a = i * 2 * PI / 24
    z = -0.15 - i * PASSO_H / 24
    c, s = math.cos(a), math.sin(a)
    # pá 1
    v1 = [bm_trado.verts.new((R0_H * c, R0_H * s, z)), bm_trado.verts.new((R1_H * c, R1_H * s, z)),
          bm_trado.verts.new((R1_H * c, R1_H * s, z - 0.02)), bm_trado.verts.new((R0_H * c, R0_H * s, z - 0.02))]
    if ant1:
        for j in range(3):
            bm_trado.faces.new((ant1[j], ant1[j + 1], v1[j + 1], v1[j]))
    ant1 = v1
# cabeça de corte cônica na ponta inferior com pastilhas de tungstênio
cil(bm_trado, Vector((0, 0, -COMP_TRADO - 0.12)), 0.38, 0.24, lados=16, r2=0.08)
for k in range(8):
    a = k * PI / 4
    caixa(bm_trado, Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, -COMP_TRADO - 0.16)), (0.06, 0.04, 0.05), Matrix.Rotation(a, 3, 'Z'))
suavizar(obj('trado_geometria', bm_trado, 'trado_aco', o_trado))

# ------------------------------------------------------------------ 4 PISTÕES TELESCÓPICOS DE AVANÇO VERTICAL
# 4 cilindros nos 4 cantos da cabeça de corte (2 a leste, 2 a oeste)
bm_camisas = bmesh.new()
hastes = []
for sx in (-0.42, 0.42):
    for dy in (-0.28, 0.28):
        pos_p = Vector((FURO.x + sx, FURO.y + dy, 0))
        # camisa fixa no chassi
        cil(bm_camisas, pos_p + Vector((0, 0, 0.85)), 0.055, 1.10, lados=14)
        cil(bm_camisas, pos_p + Vector((0, 0, 1.38)), 0.07, 0.06, lados=14)   # cabeçote
        caixa(bm_camisas, pos_p + Vector((0, 0, DECK + 0.04)), (0.12, 0.12, 0.08))
        # haste móvel
        o_has = bpy.data.objects.new('haste_pistao_%d_%d' % (1 if sx > 0 else 2, 1 if dy > 0 else 2), None)
        sc.collection.objects.link(o_has)
        o_has.location = pos_p + Vector((0, 0, Z_ALTO - 0.20))
        bm_h = bmesh.new()
        cil(bm_h, Vector((0, 0, -0.65)), 0.032, 1.30, lados=12)
        suavizar(obj('haste_malha_%d_%d' % (1 if sx > 0 else 2, 1 if dy > 0 else 2), bm_h, 'cromo', o_has))
        hastes.append((o_has, pos_p))

suavizar(obj('pistoes_camisas', bm_camisas, 'grafite'))

# ------------------------------------------------------------------ BRITADOR CÔNICO E PENEIRA VIBRATÓRIA (SUL-SUDESTE)
P_BRIT = Vector((0.45, -0.55, 0))
bm_brit = bmesh.new()
# carcaça cônica do britador
bmesh.ops.create_cone(bm_brit, cap_ends=False, segments=24, radius1=0.22, radius2=0.34, depth=0.45,
                      matrix=Matrix.Translation(P_BRIT + Vector((0, 0, 0.55))))
cil(bm_brit, P_BRIT + Vector((0, 0, 0.80)), 0.35, 0.12, lados=24)
# calha coletora do furo até o britador
cano(bm_brit, bm_brit, bm_brit, [FURO + Vector((0.25, -0.20, DECK + 0.05)),
                                 P_BRIT + Vector((0, 0, 0.85))], 0.08)
obj('britador_conico', bm_brit, 'aco_pesado')

# peneira vibratória inclinada (animada em alta frequência)
o_peneira = bpy.data.objects.new('peneira_vibratoria', None)
sc.collection.objects.link(o_peneira)
o_peneira.location = Vector((0.15, -0.85, 0.40))
bm_pen = bmesh.new()
caixa(bm_pen, (0, 0, 0), (0.35, 0.45, 0.08), Matrix.Rotation(math.radians(18), 3, 'X'))
obj('peneira_caixa', bm_pen, 'amarelo_broca', o_peneira)

# ------------------------------------------------------------------ BOCA DE SAÍDA SUL: ESTEIRA DE MINÉRIO (x = 0.0 m, y = -1.44 m, z = 0.23 m)
bm_est_sai = bmesh.new()
# leito da esteira de y = -0.75 até y = -1.48 m
caixa_de(bm_est_sai, (-0.24, -1.48, Z_P - 0.16), (0.24, -0.75, Z_P - 0.12))
for ye in (-0.85, -1.05, -1.25, -1.45):
    cil(bm_est_sai, Vector((0.0, ye, Z_P - 0.11)), 0.022, 0.44, Vector((1, 0, 0)), lados=14)
# saias laterais em chapa
for sx in (-0.22, 0.22):
    caixa_de(bm_est_sai, (sx - 0.012, -1.48, Z_P - 0.12), (sx + 0.012, -0.75, Z_P + 0.02))
obj('esteira_saida_estrutura', bm_est_sai, 'aco_pesado')

# pedras de minério avançando continuamente na esteira sul
pedras_saida = []
for k in range(5):
    bm_pdr = bmesh.new()
    pedra(bm_pdr, (0, 0, 0), random.uniform(0.035, 0.06), achatar=0.75)
    o = obj('pedra_minerio_%d' % k, bm_pdr, 'minerio')
    pedras_saida.append(o)

# ------------------------------------------------------------------ BOCA DE FLUIDO OESTE: x = -1.44 m, y = 0.0 m, z = 0.35 m
bm_bf = bmesh.new()
boca_o = Vector((-1.44, 0.0, Z_P))
tubo(bm_bf, boca_o, Vector((-1.05, 0.0, Z_P)), 0.042, 16)
tubo(bm_bf, boca_o, boca_o + Vector((0.025, 0, 0)), 0.075, 16)              # flange padrão
# válvula esfera
cil(bm_bf, Vector((-1.22, 0.0, Z_P)), 0.055, 0.08, Vector((1, 0, 0)), lados=14)
caixa_de(bm_bf, (-1.24, -0.015, Z_P + 0.06), (-1.10, 0.015, Z_P + 0.08))  # alavanca vermelha
# cano até o anel de aspersão do poço
cano(bm_bf, bm_bf, bm_bf, [Vector((-1.05, 0.0, Z_P)), Vector((-0.65, 0.0, Z_P)),
                           Vector((-0.65, FURO.y, Z_P)), FURO + Vector((-0.46, 0, Z_P))], 0.035)
suavizar(obj('boca_fluido_aspersao', bm_bf, 'aco_pesado'))

# ------------------------------------------------------------------ UNIDADE DE FORÇA INDUSTRIAL (NORDESTE: x = 0.85, y = 0.85)
P_FORCA = Vector((0.85, 0.85, 0))
bm_forca = bmesh.new()
# cofre do motor
caixa_de(bm_forca, (P_FORCA.x - 0.45, P_FORCA.y - 0.40, DECK), (P_FORCA.x + 0.45, P_FORCA.y + 0.40, DECK + 0.75))
# radiadores axiais
for yr in (P_FORCA.y - 0.20, P_FORCA.y + 0.20):
    cil(bm_forca, Vector((P_FORCA.x - 0.46, yr, DECK + 0.45)), 0.16, 0.03, Vector((1, 0, 0)), lados=20)
# chaminé de escape alta com silenciador
tubo(bm_forca, P_FORCA + Vector((0.25, 0.20, DECK + 0.75)), P_FORCA + Vector((0.25, 0.20, 2.75)), 0.05, 16)
cil(bm_forca, P_FORCA + Vector((0.25, 0.20, 1.85)), 0.09, 0.35, lados=16)   # silenciador
obj('unidade_forca_corpo', bm_forca, 'amarelo_broca')

# dois ventiladores axiais giratórios no radiador
ventoinhas_radiador = []
for iv, yr in enumerate((P_FORCA.y - 0.20, P_FORCA.y + 0.20)):
    o_v = bpy.data.objects.new('ventoinha_radiador_%d' % iv, None)
    sc.collection.objects.link(o_v)
    o_v.location = Vector((P_FORCA.x - 0.46, yr, DECK + 0.45))
    bm_v = bmesh.new()
    for k in range(6):
        a = k * PI / 3
        caixa(bm_v, Vector((0, math.cos(a) * 0.08, math.sin(a) * 0.08)), (0.015, 0.07, 0.03), Matrix.Rotation(a, 3, 'X'))
    cil(bm_v, Vector((0, 0, 0)), 0.035, 0.04, Vector((1, 0, 0)), lados=12)
    obj('ventoinha_palhetas_%d' % iv, bm_v, 'grafite', o_v)
    ventoinhas_radiador.append(o_v)

# ------------------------------------------------------------------ EFEITOS: Névoa de Supressão e Fumaça
fumacas = []
for k in range(5):
    bm_fm = bmesh.new()
    bmesh.ops.create_icosphere(bm_fm, subdivisions=1, radius=0.08)
    o = obj('EFEITO_fumaca_%d' % k, bm_fm, 'fumaca')
    fumacas.append(o)

nevoas = []
for k in range(4):
    bm_nv = bmesh.new()
    bmesh.ops.create_icosphere(bm_nv, subdivisions=1, radius=0.10)
    o = obj('EFEITO_nevoa_%d' % k, bm_nv, 'poeira')
    nevoas.append(o)


# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço contínuo)
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    u = (q - 1) / QUADROS
    t = (q - 1) / FPS

    # 1. Curso vertical da cabeça motriz (desce e sobe com avanço hidráulico)
    w_curso = 0.5 - 0.5 * math.cos(u * 2 * PI)
    z_cab = Z_ALTO - (Z_ALTO - Z_BAIXO) * w_curso
    o_cabeca.location = Vector((FURO.x, FURO.y, z_cab))
    o_cabeca.keyframe_insert('location', frame=q)

    # 2. Rotação veloz do trado helicoidal (8 voltas completas por ciclo)
    o_trado.rotation_euler = (0, 0, u * VOLTAS * 2 * PI)
    o_trado.keyframe_insert('rotation_euler', frame=q)

    # 3. Quatro hastes telescópicas acompanhando a cabeça
    for o_has, pos_p in hastes:
        o_has.location = pos_p + Vector((0, 0, z_cab - 0.20))
        o_has.keyframe_insert('location', frame=q)

    # 4. Ventiladores axiais do radiador girando velozmente
    for iv, o_v in enumerate(ventoinhas_radiador):
        o_v.rotation_euler = (u * 12 * PI * (1 if iv == 0 else -1), 0, 0)
        o_v.keyframe_insert('rotation_euler', frame=q)

    # 5. Vibração de alta frequência na peneira
    vib = 0.008 * math.sin(u * 48 * PI)
    o_peneira.location = Vector((0.15, -0.85, 0.40 + vib))
    o_peneira.keyframe_insert('location', frame=q)

    # 6. Pedras de minério avançando continuamente na esteira sul
    for k, o in enumerate(pedras_saida):
        up = (k / len(pedras_saida) + u) % 1.0
        y_pdr = -0.80 - up * 0.65
        o.location = Vector((0.0 + 0.04 * math.sin(k * 2), y_pdr, Z_P - 0.07))
        o.keyframe_insert('location', frame=q)

    # 7. Fumaça saindo do escape da unidade de força
    for k, o in enumerate(fumacas):
        uf = (k / len(fumacas) + u * 2) % 1.0
        o.location = P_FORCA + Vector((0.25 + 0.05 * math.sin(k + uf * 3), 0.20 + 0.04 * math.cos(k), 2.80 + 0.9 * uf))
        s = 0.05 + 0.20 * uf
        o.scale = (s, s, s)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)

    # 8. Névoa de supressão ao redor do colar de perfuração
    for k, o in enumerate(nevoas):
        un = (k / len(nevoas) + u * 3) % 1.0
        a = k * PI / 2 + un * 2
        o.location = FURO + Vector((0.40 * math.cos(a), 0.40 * math.sin(a), DECK + 0.12 + 0.25 * un))
        sn = 0.08 + 0.18 * un
        o.scale = (sn, sn, sn)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)


# ------------------------------------------------------------------ CÂMERAS E ILUMINAÇÃO
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (14, 14, 1.0))
obj('chao', bm_chao, 'chao')

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
bg.inputs['Strength'].default_value = 0.6

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


ALVO = (0.0, 0.0, 1.1)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo in ('foto', 'perto'):
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    if modo == 'foto':
        sc.frame_set(int(QUADROS * 0.25) + 1)
        for i, (ang, alt) in enumerate(((305, 5.0), (215, 4.8), (125, 5.2), (35, 4.6))):
            a = math.radians(ang)
            mirar(Vector(ALVO) + Vector((math.cos(a) * 4.8, math.sin(a) * 4.8, alt)), ALVO, 30)
            sc.render.filepath = os.path.join(AQUI, 'broca_grande_%d.png' % i)
            bpy.ops.render.render(write_still=True)
    sc.frame_set(int(QUADROS * 0.45))
    # close-up olhando para o colar de perfuração, trado em rotação, pistões e esteira sul
    mirar((-1.45, -1.25, 1.75), (0.05, -0.20, 0.65), 30)
    sc.render.filepath = os.path.join(AQUI, 'broca_grande_perto.png')
    bpy.ops.render.render(write_still=True)

elif modo == 'video':
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(305)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 6.2, math.sin(a) * 6.2, 3.6)), ALVO, 34)
    if hasattr(sc.render.image_settings, 'media_type'):
        sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(AQUI, 'broca_grande_video.mp4')
    bpy.ops.render.render(animation=True)

total_tris = sum(len(o.data.polygons) * 2 for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO') and not o.name == 'chao')
print('BROCA GRANDE ok — tris aproximados: %d' % total_tris)
