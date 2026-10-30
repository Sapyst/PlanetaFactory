"""Estudo isolado (fora do jogo): fornalha elétrica, 2×2 tiles.
Forno industrial elétrico a arco e indução eletromagnética (EAF):
- Tamanho: 2×2 tiles (área 1.92 × 1.92 m, laje de 1.96 × 1.96 m).
- Entrada de minério no Sul (tile da direita: x = +0.48 m, y = -0.96 m, z = 0.23 m):
  esteira transportadora com tremonha selada e dosador vibratório.
- Saída de barras de metal no Norte (tile da esquerda: x = -0.48 m, y = +0.96 m, z = 0.23 m):
  bica de vazamento contínuo com esteira de lingotes arrefecendo.
- Boca de fluido Oeste (refrigeração líquida): x = -0.96 m, y = 0.0 m, z = 0.35 m com flange e válvula.
- 2 Slots de Módulo: baia lateral com dois cartuchos removíveis de módulo, dissipadores e barramento de LEDs.
- 3 Eletrodos verticais de grafite maciço com colunas de avanço eletromecânico e braços condutores de cobre.
- Transformador de potência traseiro com radiador aletado, ventoinha e cabos flexíveis refrigerados a água.
- Exaustão de 4º furo (Direct Evacuation System) com duto arrefecido até o ciclone de despoeiramento.
- Fenômeno da IA: agitador eletromagnético de poça de fusão (EMS) com pulso de cristal piezo-harmônico e clarões de arco elétrico.

Uso: blender -b --python estudo_fornalha_eletrica.py -- foto | video | perto | nada
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
random.seed(47)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
Z0 = 0.08                    # topo da laje
Z_P = 0.35                   # altura padrão das bocas de fluido


def suavizar(o):
    """Sombra suave nas laterais (quads) mantendo tampas planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=32, nr=10):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


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


def lingote_mat():
    m = mats.material('LingoteEletrico', (0.32, 0.32, 0.33), 1.0, 0.42, pintura=False, sujeira=0.3, ferrugem=0.1)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    quente = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.25, 'From Max': 0.90, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sep.outputs['Y'], quente.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.6, 0.05, 0.0, 1)
    cor.inputs[7].default_value = (1.0, 0.55, 0.12, 1)
    nt.links.new(quente.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Emission Color'])
    forca = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    forca.inputs[1].default_value = 10.0
    nt.links.new(quente.outputs['Result'], forca.inputs[0])
    nt.links.new(forca.outputs['Value'], b.inputs['Emission Strength'])
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
    'azul_industrial': mats.material('Azul Fornalha', (0.09, 0.22, 0.32), 0, 0.42, desgaste=1.1, sujeira=1.0, ferrugem=0.55),
    'aco_escuro': mats.material('Aço Escuro', (0.24, 0.25, 0.26), 1.0, 0.45, pintura=False, ferrugem=0.75, sujeira=0.8, escovado=True),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'grafite_eletrodo': mats.material('Grafite Eletrodo', (0.04, 0.04, 0.045), 0.2, 0.65, pintura=False, sujeira=0.4, desgaste=0.3),
    'cobre_barra': mats.material('Cobre Barramento', (0.82, 0.45, 0.22), 1.0, 0.28, pintura=False, sujeira=0.5),
    'ouro': mats.material('Ouro Conector', (0.85, 0.68, 0.18), 1.0, 0.22, pintura=False, sujeira=0.2),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'ceramica_isolador': mats.material('Cerâmica Isoladora', (0.82, 0.80, 0.75), 0, 0.15, pintura=False, sujeira=0.3),
    'lingote': lingote_mat(),
    'metal_liquido': luz_mat('Metal Líquido', (1.0, 0.45, 0.08), 15.0),
    'arco_plasma': luz_mat('Arco Elétrico Plasma', (0.2, 0.7, 1.0), 30.0),
    'cristal_ia': luz_mat('Cristal IA Térmico', (0.15, 0.85, 1.0), 10.0),
    'ciano': luz_mat('Luz ciano', (0.1, 0.9, 1.0), 8.0),
    'faisca': luz_mat('Faísca Arco', (0.4, 0.8, 1.0), 16.0),
    'listras': base3d.listras_mat(),
    'fumaca': fumaca_grad_mat('Fumaça EAF', 6.0, 2.0, 3.8),
    'vapor': base3d.volume_mat('Vapor EAF', (0.92, 0.92, 0.94), 7.0, 0.3, 1.3),
})

# ------------------------------------------------------------------ LAJE DE FUNDAÇÃO 2×2 TILES
bm_laje = bmesh.new()
caixa_de(bm_laje, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
# soleiras e berços
caixa_de(bm_laje, (-0.65, -0.65, Z0), (0.65, 0.65, Z0 + 0.04))
obj('laje', bm_laje, 'concreto')

# listras de segurança
bm_list = bmesh.new()
for s in (-1, 1):
    caixa_de(bm_list, (-0.985, s * 0.97 - 0.008, Z0 + 0.035), (0.985, s * 0.97 + 0.008, Z0 + 0.042))
    caixa_de(bm_list, (s * 0.97 - 0.008, -0.985, Z0 + 0.035), (s * 0.97 + 0.008, 0.985, Z0 + 0.042))
obj('laje_listras', bm_list, 'listras')

# ------------------------------------------------------------------ FORNO ELÉTRICO A ARCO (EAF)
# Cuba circular pesada com painéis refrigerados: centro em x = 0.02, y = 0.08
FC = Vector((0.02, 0.08, 0))
R_FORNO, Z_CUBA, Z_ABOB = 0.46, 0.85, 1.15

bm_cuba = bmesh.new()
# cadinho e corpo cilíndrico
cil(bm_cuba, FC + Vector((0, 0, (Z0 + Z_CUBA) / 2)), R_FORNO, Z_CUBA - Z0, lados=36)
# anel de flange de apoio do teto basculante
cil(bm_cuba, FC + Vector((0, 0, Z_CUBA)), R_FORNO + 0.035, 0.05, lados=36)
# painéis externos de refrigeração com aletas verticais
for i in range(12):
    a = i * 2 * PI / 12
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm_cuba, FC + d * (R_FORNO + 0.015) + Vector((0, 0, 0.50)), (0.025, 0.08, 0.45), Matrix.Rotation(a, 3, 'Z'))
# abóbada / teto refrigerado em calota esférica
bmesh.ops.create_uvsphere(bm_cuba, u_segments=36, v_segments=14, radius=1.0,
                          matrix=Matrix.Translation(FC + Vector((0, 0, Z_CUBA))) @ Matrix.Diagonal((R_FORNO, R_FORNO, 0.22, 1)))
# 3 orifícios na abóbada para passagem dos eletrodos
for i in range(3):
    a = i * 2 * PI / 3 + PI / 6
    pe = FC + Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, Z_ABOB + 0.05))
    cil(bm_cuba, pe, 0.065, 0.04, lados=16)
suavizar(obj('eaf_cuba', bm_cuba, 'aco_escuro'))

# ------------------------------------------------------------------ 3 ELETRODOS DE GRAFITE VERTICAIS E MECANISMO DE ELEVAÇÃO
# Mastros de elevação na lateral sudeste/leste: x = 0.55, y = 0.15
P_MASTROS = Vector((0.55, 0.15, 0))
bm_mast = bmesh.new()
for ie in range(3):
    ym = P_MASTROS.y - 0.20 + ie * 0.20
    # coluna de guia vertical de fuso
    viga(bm_mast, Vector((P_MASTROS.x, ym, Z0)), Vector((P_MASTROS.x, ym, 2.35)), 0.04)
    # sapata
    caixa(bm_mast, Vector((P_MASTROS.x, ym, Z0 + 0.02)), (0.10, 0.10, 0.04))
    # motor elétrico de avanço no topo
    cil(bm_mast, Vector((P_MASTROS.x, ym, 2.40)), 0.045, 0.12, lados=14)
obj('eletrodos_colunas_guia', bm_mast, 'azul_industrial')

# 3 conjuntos móveis: braço de cobre condutor + eletrodo de grafite
eletrodos_moveis = []
for ie in range(3):
    a = ie * 2 * PI / 3 + PI / 6
    pe_centro = FC + Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 0))
    ym = P_MASTROS.y - 0.20 + ie * 0.20

    o_el = bpy.data.objects.new('eletrodo_conjunto_%d' % ie, None)
    sc.collection.objects.link(o_el)
    o_el.location = Vector((0, 0, 1.45))

    # braço de cobre que sai da coluna até o centro do furo
    bm_br = bmesh.new()
    caixa_de(bm_br, (P_MASTROS.x - 0.06, ym - 0.05, -0.04), (P_MASTROS.x + 0.06, ym + 0.05, 0.04))
    tubo(bm_br, Vector((P_MASTROS.x - 0.05, ym, 0)), Vector((pe_centro.x + 0.05, pe_centro.y, 0)), 0.04, 14)
    # pinça porta-eletrodo refrigerada a água
    cil(bm_br, Vector((pe_centro.x, pe_centro.y, 0)), 0.075, 0.12, lados=18)
    obj('braco_cobre_%d' % ie, bm_br, 'cobre_barra', o_el)

    # cilindro de grafite maciço
    bm_gr = bmesh.new()
    cil(bm_gr, Vector((pe_centro.x, pe_centro.y, 0.10)), 0.052, 1.05, lados=20)
    suavizar(obj('grafite_haste_%d' % ie, bm_gr, 'grafite_eletrodo', o_el))

    eletrodos_moveis.append((o_el, ie))

# clarão do arco de plasma dentro do forno (visível pelas frestas)
luz_arco = bpy.data.lights.new('LuzArcoPlasma', 'POINT')
luz_arco.color = (0.3, 0.75, 1.0)
luz_arco.energy = 45.0
o_luz_arco = bpy.data.objects.new('EFEITO_LuzArco', luz_arco)
sc.collection.objects.link(o_luz_arco)
o_luz_arco.location = FC + Vector((0, 0, 0.90))

# ------------------------------------------------------------------ TRANSFORMADOR DE POTÊNCIA (TRASEIRA LESTE: x = 0.70, y = -0.55)
P_TRANSF = Vector((0.70, -0.55, 0))
bm_tr = bmesh.new()
# cuba do transformador
caixa_de(bm_tr, (P_TRANSF.x - 0.22, P_TRANSF.y - 0.25, Z0), (P_TRANSF.x + 0.22, P_TRANSF.y + 0.25, 0.75))
# aletas do radiador de óleo
for k in range(8):
    xa = P_TRANSF.x - 0.18 + k * 0.05
    caixa_de(bm_tr, (xa - 0.005, P_TRANSF.y - 0.29, Z0 + 0.08), (xa + 0.005, P_TRANSF.y + 0.29, 0.70))
# isoladores cerâmicos no topo (bushings)
for ib in (-0.12, 0.0, 0.12):
    pb = Vector((P_TRANSF.x + ib, P_TRANSF.y, 0.75))
    cil(bm_tr, pb + Vector((0, 0, 0.08)), 0.038, 0.16, lados=14)
    # pratos cerâmicos
    for zc in (0.80, 0.85, 0.90):
        cil(bm_tr, Vector((pb.x, pb.y, zc)), 0.055, 0.015, lados=14)
obj('transformador_corpo', bm_tr, 'azul_industrial')

# cabos refrigerados a água (tranças condutoras flexíveis do transformador aos braços)
bm_cabos = bmesh.new()
for ie in range(3):
    ym = P_MASTROS.y - 0.20 + ie * 0.20
    p_orig = Vector((P_TRANSF.x - 0.10, P_TRANSF.y + 0.15, 0.65))
    p_dest = Vector((P_MASTROS.x - 0.05, ym, 1.45))
    mangueira(bm_cabos, bezier(p_orig, p_orig + Vector((-0.15, 0.15, 0.3)), p_dest + Vector((0.15, -0.15, 0.2)), p_dest, 10), 0.022)
suavizar(obj('cabos_agua_arco', bm_cabos, 'borracha'))

# ------------------------------------------------------------------ 2 SLOTS DE MÓDULOS (LATERAL NORDESTE: x = 0.55, y = 0.65)
MOD_POS = Vector((0.55, 0.65, 0))
bm_mrack = bmesh.new()
bm_mcart = bmesh.new()
bm_mleds = bmesh.new()

caixa_de(bm_mrack, (MOD_POS.x - 0.06, MOD_POS.y - 0.24, Z0), (MOD_POS.x + 0.24, MOD_POS.y + 0.24, 0.65))
for ym in (-0.12, 0.12):
    caixa_de(bm_mrack, (MOD_POS.x - 0.07, MOD_POS.y + ym - 0.09, 0.14), (MOD_POS.x + 0.20, MOD_POS.y + ym + 0.09, 0.58))
obj('modulos_rack', bm_mrack, 'grafite')

for ym in (-0.12, 0.12):
    # cartucho
    caixa_de(bm_mcart, (MOD_POS.x - 0.09, MOD_POS.y + ym - 0.07, 0.16), (MOD_POS.x + 0.18, MOD_POS.y + ym + 0.07, 0.55))
    # puxador frontal
    tubo(bm_mcart, (MOD_POS.x - 0.09, MOD_POS.y + ym - 0.04, 0.35), (MOD_POS.x - 0.12, MOD_POS.y + ym - 0.04, 0.35), 0.007, 8)
    tubo(bm_mcart, (MOD_POS.x - 0.12, MOD_POS.y + ym - 0.04, 0.35), (MOD_POS.x - 0.12, MOD_POS.y + ym + 0.04, 0.35), 0.007, 8)
    tubo(bm_mcart, (MOD_POS.x - 0.12, MOD_POS.y + ym + 0.04, 0.35), (MOD_POS.x - 0.09, MOD_POS.y + ym + 0.04, 0.35), 0.007, 8)
    # aletas de resfriamento
    for k in range(4):
        za = 0.20 + k * 0.08
        caixa_de(bm_mcart, (MOD_POS.x - 0.08, MOD_POS.y + ym - 0.065, za), (MOD_POS.x + 0.15, MOD_POS.y + ym + 0.065, za + 0.012))
    # LEDs indicadores de barramento
    for il in range(4):
        zl = 0.22 + il * 0.07
        cil(bm_mleds, Vector((MOD_POS.x - 0.092, MOD_POS.y + ym + 0.05, zl)), 0.007, 0.006, Vector((-1, 0, 0)), lados=10)

obj('modulos_cartuchos', bm_mcart, 'azul_industrial')
obj('modulos_leds', bm_mleds, 'ciano')

# ------------------------------------------------------------------ BOCA DE FLUIDO OESTE: x = -0.96 m, y = 0.0 m, z = 0.35 m
bm_bf = bmesh.new()
boca_o = Vector((-0.96, 0.0, Z_P))
tubo(bm_bf, boca_o, Vector((-0.65, 0.0, Z_P)), 0.038, 16)
tubo(bm_bf, boca_o, boca_o + Vector((0.02, 0, 0)), 0.065, 16)               # flange externa
# válvula esfera de corte
cil(bm_bf, Vector((-0.78, 0.0, Z_P)), 0.05, 0.06, Vector((1, 0, 0)), lados=14)
caixa_de(bm_bf, (-0.80, -0.015, Z_P + 0.06), (-0.70, 0.015, Z_P + 0.08))   # alavanca vermelha
# tubulação que sobe para resfriar a abóbada e os eletrodos
cano(bm_bf, bm_bf, bm_bf, [Vector((-0.65, 0.0, Z_P)), Vector((-0.65, 0.0, 0.95)),
                           FC + Vector((-R_FORNO, 0, 0.95))], 0.032)
suavizar(obj('boca_fluido_refrigeracao', bm_bf, 'aco_escuro'))

# ------------------------------------------------------------------ ENTRADA SUL: TREMONHA E ESTEIRA (x = +0.48 m, y = -0.96 m, z = 0.23 m)
P_ENT = Vector((0.48, -0.96, 0.23))
bm_ent = bmesh.new()
caixa_de(bm_ent, (P_ENT.x - 0.14, -0.98, Z0), (P_ENT.x + 0.14, -0.65, Z_P - 0.12))
# tremonha de carga
bmesh.ops.create_cone(bm_ent, cap_ends=False, segments=20, radius1=0.10, radius2=0.16, depth=0.22,
                      matrix=Matrix.Translation(Vector((P_ENT.x, -0.55, 0.45))))
# duto de injeção direta na abóbada do forno
tubo(bm_ent, Vector((P_ENT.x, -0.55, 0.34)), FC + Vector((0.20, -0.25, Z_ABOB)), 0.045, 14)
obj('esteira_entrada_tremonha', bm_ent, 'grafite')

# ------------------------------------------------------------------ SAÍDA NORTE: BICA DE VAZAMENTO E CARROSSEL DE LINGOTEIRAS (x = -0.48 m, y = +0.96 m, z = 0.23 m)
P_SAI = Vector((-0.48, 0.96, 0.23))
bm_sai = bmesh.new()
# bica basculante do forno
caixa_de(bm_sai, (FC.x - 0.18, FC.y + 0.25, 0.35), (FC.x - 0.32, FC.y + 0.50, 0.42))
# canaleta refratária com metal líquido
caixa_de(bm_sai, (FC.x - 0.22, FC.y + 0.28, 0.38), (FC.x - 0.28, FC.y + 0.48, 0.40))
# leito da esteira de lingotamento até o limite norte
caixa_de(bm_sai, (-0.60, 0.45, Z0), (-0.36, 0.98, 0.20))
for yl in (0.50, 0.65, 0.80, 0.95):
    cil(bm_sai, Vector((-0.48, yl, 0.18)), 0.022, 0.22, Vector((1, 0, 0)), lados=14)
obj('esteira_saida_bica', bm_sai, 'aco_escuro')

# veio de metal líquido caindo na lingoteira
bm_vm = bmesh.new()
tubo(bm_vm, Vector((FC.x - 0.28, FC.y + 0.48, 0.38)), Vector((-0.48, 0.50, 0.24)), 0.016, 10)
obj('veio_metal_liquido', bm_vm, 'metal_liquido')

# lingotes individuais que avançam e esfriam
lingotes = []
for k in range(4):
    bm_lg = bmesh.new()
    caixa(bm_lg, (0, 0, 0.02), (0.16, 0.09, 0.04))
    o = obj('lingote_%d' % k, bm_lg, 'lingote')
    lingotes.append(o)

# ------------------------------------------------------------------ SISTEMA DE EXAUSTÃO DO 4º FURO (DES) E CHAMINÉ
# 4º orifício refrigerado na abóbada do forno
P_4FURO = FC + Vector((-0.22, -0.15, Z_ABOB + 0.08))
bm_des = bmesh.new()
# cotovelo refrigerado a água
curva(bm_des, P_4FURO, 0.065, 16)
# duto descendo até o ciclone traseiro no sudoeste
P_CICLONE = Vector((-0.55, -0.60, 0))
cano(bm_des, bm_des, bm_des, [P_4FURO, Vector((P_CICLONE.x, -0.15, 1.45)),
                              Vector((P_CICLONE.x, P_CICLONE.y, 1.45)),
                              Vector((P_CICLONE.x, P_CICLONE.y, 0.95))], 0.05)
# vaso cônico do ciclone de retenção de pó metálico
bmesh.ops.create_cone(bm_des, cap_ends=False, segments=24, radius1=0.06, radius2=0.18, depth=0.45,
                      matrix=Matrix.Translation(P_CICLONE + Vector((0, 0, 0.50))))
cil(bm_des, P_CICLONE + Vector((0, 0, 0.85)), 0.18, 0.25, lados=24)
# chaminé de descarga filtrada
tubo(bm_des, P_CICLONE + Vector((0, 0, 0.98)), P_CICLONE + Vector((0, 0, 2.65)), 0.06, 18)
cil(bm_des, P_CICLONE + Vector((0, 0, 2.68)), 0.09, 0.04, lados=18)        # chapéu
suavizar(obj('sistema_exaustao_des', bm_des, 'aco_escuro'))

# ------------------------------------------------------------------ FENÔMENO DA IA: AGITADOR ELETROMAGNÉTICO (EMS)
# Anel de bobinas magnéticas de ressonância na base da cuba (z = 0.35 m)
bm_ems = bmesh.new()
toro(bm_ems, FC + Vector((0, 0, 0.35)), R_FORNO + 0.04, 0.032, nR=32, nr=10)
for k in range(6):
    a = k * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    cil(bm_ems, FC + d * (R_FORNO + 0.04) + Vector((0, 0, 0.35)), 0.045, 0.07, d, lados=12)
obj('anel_ems_ia', bm_ems, 'cobre_barra')

# cristal piezo-harmônico no console de controle da IA
o_cristal = bpy.data.objects.new('cristal_ia_eaf', None)
sc.collection.objects.link(o_cristal)
o_cristal.location = FC + Vector((-R_FORNO - 0.08, -0.25, 0.70))
bm_cr = bmesh.new()
bmesh.ops.create_icosphere(bm_cr, subdivisions=1, radius=0.055)
obj('cristal_ia_malha', bm_cr, 'cristal_ia', o_cristal)

# ------------------------------------------------------------------ EFEITOS: Faíscas de Arco, Fumaça e Vapor
faiscas = []
vel_f = []
for k in range(12):
    bm_f = bmesh.new()
    bmesh.ops.create_icosphere(bm_f, subdivisions=1, radius=0.007)
    o = obj('EFEITO_faisca_%d' % k, bm_f, 'faisca')
    faiscas.append(o)
    a = random.uniform(0, 2 * PI)
    elev = random.uniform(0.3, 1.4)
    v = random.uniform(1.0, 2.4)
    vel_f.append(Vector((math.cos(a) * math.cos(elev) * v, math.sin(a) * math.cos(elev) * v, math.sin(elev) * v)))

fumacas = []
for k in range(5):
    bm_fm = bmesh.new()
    bmesh.ops.create_icosphere(bm_fm, subdivisions=1, radius=0.075)
    o = obj('EFEITO_fumaca_%d' % k, bm_fm, 'fumaca')
    fumacas.append(o)


# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço contínuo)
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    u = (q - 1) / QUADROS
    t = (q - 1) / FPS

    # 1. Três eletrodos oscilando milimetricamente no ajuste fino do arco
    for o_el, ie in eletrodos_moveis:
        dz = 0.025 * math.sin(u * 8 * PI + ie * 2 * PI / 3)
        o_el.location = Vector((0, 0, 1.45 + dz))
        o_el.keyframe_insert('location', frame=q)

    # 2. Clarões intensos do arco de plasma dentro do forno
    tremor_arco = 1.0 + 0.35 * math.sin(u * 32 * PI) + 0.25 * math.cos(u * 54 * PI)
    luz_arco.energy = 38.0 * max(0.2, tremor_arco)
    luz_arco.keyframe_insert('energy', frame=q)

    # 3. Lingotes de aço avançando continuamente
    for k, o in enumerate(lingotes):
        ul = (k / len(lingotes) + u) % 1.0
        y_ling = 0.45 + ul * 0.50
        o.location = Vector((-0.48, y_ling, 0.22))
        o.keyframe_insert('location', frame=q)

    # 4. Faíscas do metal líquido na bica
    p_bica = Vector((-0.48, 0.50, 0.24))
    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + u * 6) % 1.0) * 0.26
        o.location = p_bica + vel_f[k] * tt + Vector((0, 0, -4.9 * tt * tt))
        o.keyframe_insert('location', frame=q)

    # 5. Fumaça saindo da chaminé
    for k, o in enumerate(fumacas):
        uf = (k / len(fumacas) + u * 2) % 1.0
        o.location = P_CICLONE + Vector((0.04 * math.sin(k + uf * 3), 0.03 * math.cos(k), 2.70 + 0.8 * uf))
        s = 0.05 + 0.18 * uf
        o.scale = (s, s, s)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)

    # 6. Pulso harmônico do cristal IA
    pulso_cr = 1.0 + 0.18 * math.sin(u * 6 * PI)
    o_cristal.scale = (pulso_cr, pulso_cr, pulso_cr)
    o_cristal.keyframe_insert('scale', frame=q)


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


ALVO = (0.0, 0.0, 0.85)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo in ('foto', 'perto'):
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    if modo == 'foto':
        sc.frame_set(int(QUADROS * 0.25) + 1)
        for i, (ang, alt) in enumerate(((305, 4.4), (215, 4.2), (125, 4.6), (35, 4.0))):
            a = math.radians(ang)
            mirar(Vector(ALVO) + Vector((math.cos(a) * 4.2, math.sin(a) * 4.2, alt)), ALVO, 32)
            sc.render.filepath = os.path.join(AQUI, 'fornalha_eletrica_%d.png' % i)
            bpy.ops.render.render(write_still=True)
    sc.frame_set(int(QUADROS * 0.35))
    # close-up olhando para os eletrodos de grafite, braços de cobre, módulo e vazamento
    mirar((-1.35, 0.55, 1.45), (-0.10, 0.15, 0.75), 32)
    sc.render.filepath = os.path.join(AQUI, 'fornalha_eletrica_perto.png')
    bpy.ops.render.render(write_still=True)

elif modo == 'video':
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(305)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 5.4, math.sin(a) * 5.4, 3.0)), ALVO, 34)
    if hasattr(sc.render.image_settings, 'media_type'):
        sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(AQUI, 'fornalha_eletrica_video.mp4')
    bpy.ops.render.render(animation=True)

total_tris = sum(len(o.data.polygons) * 2 for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO') and not o.name == 'chao')
print('FORNALHA ELETRICA ok — tris aproximados: %d' % total_tris)
