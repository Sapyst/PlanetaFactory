"""Estudo isolado (fora do jogo): fornalha de aço, 2×2 tiles.
Evolução industrial pesada da fornalha de fundição:
- Tamanho: 2×2 tiles (área 1.92 × 1.92 m, laje de 1.96 × 1.96 m).
- Entrada de minério/combustível no Sul (tile da direita: x = +0.48 m, y = -0.96 m, z = 0.23 m):
  elevador skip inclinado com trilhos em perfil I, guincho a tambor e caçamba basculante sobre topo de sino duplo.
- Saída de barras de aço no Norte (tile da esquerda: x = -0.48 m, y = +0.96 m, z = 0.23 m):
  bica de vazamento contínuo de aço líquido com separador de escória, corrente de lingoteiras e spray de resfriamento.
- Casco cilíndrico de aço estrutural rebitado com cintas de reforço e tirantes tensores roscados.
- Anel de ar de sopro quente (bustle pipe) com 6 ventaneiras com visores de mira em latão e mangueiras de refrigeração.
- Recuperador térmico com duto descendente (downcomer) e chaminé metálica alta com anéis de rigidez.
- Fenômeno da IA: anel de contenção magnética de plasma na garganta de fusão com cristal piezo-térmico.

Uso: blender -b --python estudo_fornalha_aco.py -- foto | video | perto | nada
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
random.seed(33)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
Z0 = 0.08                    # topo da laje


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


def tijolo_refratario_mat():
    m = bpy.data.materials.new('TijoloRefratario')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = no(nt, 'ShaderNodeTexCoord')
    tj = no(nt, 'ShaderNodeTexBrick', **{'Scale': 5.0, 'Mortar Size': 0.008, 'Brick Width': 0.8, 'Row Height': 0.28})
    tj.inputs['Color1'].default_value = (0.34, 0.12, 0.06, 1)
    tj.inputs['Color2'].default_value = (0.24, 0.08, 0.04, 1)
    tj.inputs['Mortar'].default_value = (0.28, 0.26, 0.22, 1)
    nt.links.new(tc.outputs['Object'], tj.inputs['Vector'])
    nt.links.new(tj.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.92
    return m


def brasa_mat(nome, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1.0, 0.35, 0.05, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.33, 0.04, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def lingote_mat():
    """Barra que esfria conforme avança para o norte: brasa alaranjada → aço escuro."""
    m = mats.material('LingoteAco', (0.32, 0.32, 0.33), 1.0, 0.42, pintura=False, sujeira=0.3, ferrugem=0.1)
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


def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


base3d.M.update({
    'aco_estrutural': mats.material('Aço Estrutural', (0.28, 0.30, 0.32), 1.0, 0.45, pintura=False, ferrugem=0.75, sujeira=0.8, escovado=True),
    'casco_forno': mats.material('Casco Forno', (0.18, 0.17, 0.16), 1.0, 0.55, pintura=False, ferrugem=0.85, sujeira=1.0),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'primer_oxido': mats.material('Primer Óxido', (0.36, 0.10, 0.06), 0, 0.65, desgaste=0.8, sujeira=0.9, ferrugem=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'ferro_fundido': mats.material('Ferro Fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'bronze_mira': mats.material('Bronze Mira', (0.70, 0.48, 0.18), 1.0, 0.32, pintura=False, sujeira=0.5),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'carvao': mats.material('Coque Siderúrgico', (0.02, 0.02, 0.022), 0, 0.6, pintura=False, sujeira=0.0, desgaste=0.0),
    'minerio': mats.material('Sinter Minério', (0.32, 0.12, 0.06), 0.2, 0.7, pintura=False, sujeira=0.5, ferrugem=0.5),
    'escoria': mats.material('Escória Vítrea', (0.035, 0.03, 0.028), 0.0, 0.08, pintura=False, sujeira=0.2, desgaste=0.0),
    'tijolo': tijolo_refratario_mat(),
    'lingote': lingote_mat(),
    'metal_liquido': brasa_mat('Metal Líquido', 14.0),
    'faisca': luz_mat('Faísca Fundição', (1.0, 0.65, 0.2), 16.0),
    'cristal_ia': luz_mat('Cristal Térmico IA', (0.2, 0.75, 1.0), 10.0),
    'listras': base3d.listras_mat(),
    'fumaca': fumaca_grad_mat('Fumaça Forno', 7.0, 2.5, 4.2),
    'vapor': base3d.volume_mat('Vapor Resfriamento', (0.92, 0.92, 0.94), 8.0, 0.3, 1.4),
})

# ------------------------------------------------------------------ LAJE DE FUNDAÇÃO 2×2 TILES
bm_laje = bmesh.new()
caixa_de(bm_laje, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
# bacia de contenção refratária sob o cadinho
caixa_de(bm_laje, (-0.65, -0.65, Z0), (0.65, 0.65, Z0 + 0.04))
obj('laje', bm_laje, 'concreto')

# listras zebradas nas bordas da laje
bm_list = bmesh.new()
for s in (-1, 1):
    caixa_de(bm_list, (-0.985, s * 0.97 - 0.008, Z0 + 0.035), (0.985, s * 0.97 + 0.008, Z0 + 0.042))
    caixa_de(bm_list, (s * 0.97 - 0.008, -0.985, Z0 + 0.035), (s * 0.97 + 0.008, 0.985, Z0 + 0.042))
obj('laje_listras', bm_list, 'listras')

# ------------------------------------------------------------------ CORPO PRINCIPAL DO FORNO (ALTO-FORNO COMPACTO)
# Centro em x = 0.05, y = 0.05. Altura do cadinho até o topo da cúpula: z = 0.12 até 2.45 m
FC = Vector((0.05, 0.05, 0))
R_CADINHO, R_VENTRE, R_TOPO = 0.38, 0.46, 0.32
Z_CAD, Z_VENT, Z_CUP = 0.75, 1.45, 2.35

bm_casco = bmesh.new()
# cadinho inferior (cilíndrico com tijolos refratários aparentes na base)
cil(bm_casco, FC + Vector((0, 0, (Z0 + Z_CAD) / 2)), R_CADINHO, Z_CAD - Z0, lados=36)
# rampa de alargamento até o ventre (bosh)
bmesh.ops.create_cone(bm_casco, cap_ends=False, segments=36, radius1=R_CADINHO, radius2=R_VENTRE, depth=Z_VENT - Z_CAD,
                      matrix=Matrix.Translation(FC + Vector((0, 0, (Z_CAD + Z_VENT) / 2))))
# cuba superior estreitando até o topo
bmesh.ops.create_cone(bm_casco, cap_ends=False, segments=36, radius1=R_VENTRE, radius2=R_TOPO, depth=Z_CUP - Z_VENT,
                      matrix=Matrix.Translation(FC + Vector((0, 0, (Z_VENT + Z_CUP) / 2))))
# cúpula hemisférica do topo
bmesh.ops.create_uvsphere(bm_casco, u_segments=36, v_segments=14, radius=1.0,
                          matrix=Matrix.Translation(FC + Vector((0, 0, Z_CUP))) @ Matrix.Diagonal((R_TOPO, R_TOPO, 0.15, 1)))
suavizar(obj('forno_casco', bm_casco, 'casco_forno'))

# cintas estruturais de aço forjado com tirantes e parafusos tensores
bm_cintas = bmesh.new()
for zc in (0.35, 0.65, 0.95, 1.30, 1.70, 2.10):
    # raio correspondente da seção
    rz = R_CADINHO if zc <= Z_CAD else (R_CADINHO + (R_VENTRE - R_CADINHO) * (zc - Z_CAD) / (Z_VENT - Z_CAD) if zc <= Z_VENT else R_VENTRE - (R_VENTRE - R_TOPO) * (zc - Z_VENT) / (Z_CUP - Z_VENT))
    cil(bm_cintas, FC + Vector((0, 0, zc)), rz + 0.015, 0.035, lados=36)
    # tirantes/presilhas verticais
    for i in range(8):
        a = i * PI / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(bm_cintas, FC + d * (rz + 0.02) + Vector((0, 0, zc)), (0.02, 0.04, 0.05), Matrix.Rotation(a, 3, 'Z'))
obj('forno_cintas', bm_cintas, 'aco_estrutural')

# ------------------------------------------------------------------ ANEL DE AR DE SOPRO QUENTE (BUSTLE PIPE) E VENTANEIRAS
# Anel toroidal em torno do ventre do forno a z = 1.05 m
R_BUSTLE = 0.58
bm_bustle = bmesh.new()
toro(bm_bustle, FC + Vector((0, 0, 1.05)), R_BUSTLE, 0.045, nR=32, nr=10)
# 6 ventaneiras de injeção descendo em ângulo para o cadinho
bm_vent = bmesh.new()
for i in range(6):
    a = i * PI / 3 + 0.2
    d = Vector((math.cos(a), math.sin(a), 0))
    p_anel = FC + d * R_BUSTLE + Vector((0, 0, 1.05))
    p_boca = FC + d * (R_CADINHO - 0.02) + Vector((0, 0, 0.72))
    tubo(bm_vent, p_anel, p_boca, 0.022, 12)
    # flange e visor de mira em latão
    cil(bm_vent, p_anel + d * 0.02, 0.035, 0.02, d, lados=12)
    cil(bm_vent, p_boca - d * 0.03, 0.032, 0.02, d, lados=12)
    # mirilho na ponta traseira
    cil(bm_vent, p_anel + d * 0.04, 0.016, 0.02, d, lados=10)
suavizar(obj('anel_bustle', bm_bustle, 'primer_oxido'))
suavizar(obj('ventaneiras', bm_vent, 'bronze_mira'))

# duto de ar quente conectando o soprador ao bustle pipe
bm_sopro = bmesh.new()
P_SOPRO = Vector((0.72, -0.45, 0.40))
# caracol do soprador de alta pressão
cil(bm_sopro, P_SOPRO, 0.16, 0.14, Vector((0, 1, 0)), lados=24)
cil(bm_sopro, P_SOPRO + Vector((0, -0.12, 0)), 0.10, 0.18, Vector((0, 1, 0)), lados=20)   # motor elétrico com aletas
for k in range(6):
    cil(bm_sopro, P_SOPRO + Vector((0, -0.18 + k * 0.025, 0)), 0.115, 0.006, Vector((0, 1, 0)), lados=20)
# duto subindo até o anel
cano(bm_sopro, bm_sopro, bm_sopro, [P_SOPRO + Vector((0, 0.08, 0.12)), Vector((0.72, -0.20, 1.05)),
                                    FC + Vector((R_BUSTLE, 0, 1.05))], 0.04, folga=0.06)
suavizar(obj('soprador_forçado', bm_sopro, 'amarelo'))

# rotor do soprador giratório animado
o_rotor_sopro = bpy.data.objects.new('rotor_soprador', None)
sc.collection.objects.link(o_rotor_sopro)
o_rotor_sopro.location = P_SOPRO
bm_rs = bmesh.new()
for k in range(8):
    a = k * PI / 4
    caixa(bm_rs, Vector((math.cos(a) * 0.07, 0, math.sin(a) * 0.07)), (0.012, 0.08, 0.05), Matrix.Rotation(a, 3, 'Y'))
cil(bm_rs, Vector((0, 0, 0)), 0.025, 0.10, Vector((0, 1, 0)), lados=12)
obj('rotor_palhetas', bm_rs, 'aco_estrutural', o_rotor_sopro)

# ------------------------------------------------------------------ ENTRADA SUL: SKIP CAR INCLINADO (MINÉRIO/COQUE): x = +0.48 m, y = -0.96 m, z = 0.23 m
P_ENT_SUL = Vector((0.48, -0.96, 0.23))
P_TOPO_SKIP = FC + Vector((0.15, -0.30, 2.45))

# trilhos inclinados duplos em perfil I
bm_trilhos = bmesh.new()
for dx in (-0.11, 0.11):
    viga(bm_trilhos, P_ENT_SUL + Vector((dx, 0.0, -0.05)), P_TOPO_SKIP + Vector((dx, 0.0, 0.0)), 0.035)
    # sapatas de apoio
    caixa(bm_trilhos, P_ENT_SUL + Vector((dx, 0.0, -0.08)), (0.08, 0.08, 0.04))
# travessas e estais dos trilhos
for u_t in (0.25, 0.50, 0.75):
    pt = P_ENT_SUL.lerp(P_TOPO_SKIP, u_t)
    caixa(bm_trilhos, pt, (0.26, 0.03, 0.02))
    # pilar de sustentação até o chão
    viga(bm_trilhos, pt, Vector((pt.x, pt.y, Z0)), 0.03)
obj('trilhos_skip', bm_trilhos, 'aco_estrutural')

# guincho com tambor de cabo e roldana superior
bm_guincho = bmesh.new()
P_GUINCHO = P_ENT_SUL + Vector((0, 0.20, 0.12))
cil(bm_guincho, P_GUINCHO, 0.08, 0.20, Vector((1, 0, 0)), lados=20)
cil(bm_guincho, P_GUINCHO + Vector((0.14, 0, 0)), 0.06, 0.10, Vector((1, 0, 0)), lados=16)   # redutor
caixa_de(bm_guincho, (P_GUINCHO.x - 0.12, P_GUINCHO.y - 0.10, Z0), (P_GUINCHO.x + 0.20, P_GUINCHO.y + 0.10, P_GUINCHO.z - 0.06))
# roldana no topo dos trilhos
cil(bm_guincho, P_TOPO_SKIP + Vector((0, -0.05, 0.12)), 0.065, 0.04, Vector((1, 0, 0)), lados=18)
obj('guincho_tambor', bm_guincho, 'grafite')

# caçamba (skip car) animada que sobe e bascula
o_skip = bpy.data.objects.new('skip_car', None)
sc.collection.objects.link(o_skip)
o_skip.location = P_ENT_SUL + Vector((0, 0.05, 0.08))

bm_sc = bmesh.new()
# caçamba em cunha
caixa_de(bm_sc, (-0.09, -0.12, 0.0), (0.09, 0.12, 0.16))
# rodas abraçando os trilhos
for dx in (-0.11, 0.11):
    for dy in (-0.08, 0.08):
        cil(bm_sc, Vector((dx, dy, 0.02)), 0.022, 0.02, Vector((1, 0, 0)), lados=12)
# carga de sinter e coque dentro da caçamba
caixa_de(bm_sc, (-0.08, -0.10, 0.08), (0.08, 0.10, 0.15))
obj('skip_car_chassi', bm_sc, 'amarelo', o_skip)

# cúpula de sino duplo de alimentação no topo do forno
bm_sino = bmesh.new()
cil(bm_sino, P_TOPO_SKIP + Vector((0, 0.10, 0.12)), 0.14, 0.26, lados=24)
bmesh.ops.create_cone(bm_sino, cap_ends=False, segments=24, radius1=0.14, radius2=0.08, depth=0.12,
                      matrix=Matrix.Translation(P_TOPO_SKIP + Vector((0, 0.10, 0.31))))
cil(bm_sino, P_TOPO_SKIP + Vector((0, 0.10, 0.40)), 0.035, 0.15, lados=14)   # atuador de sino
obj('topo_sino_duplo', bm_sino, 'ferro_fundido')

# ------------------------------------------------------------------ SAÍDA NORTE: BICA DE VAZAMENTO E CARROSSEL DE LINGOTEIRAS (x = -0.48 m, y = +0.96 m, z = 0.23 m)
P_SAI_NORTE = Vector((-0.48, 0.96, 0.23))
P_FURO_CORRIDA = FC + Vector((-0.24, 0.12, 0.40))

# bica refratária inclinada saindo do furo de corrida
bm_bica = bmesh.new()
caixa_de(bm_bica, (P_FURO_CORRIDA.x - 0.05, P_FURO_CORRIDA.y, P_FURO_CORRIDA.z - 0.04),
                  (P_FURO_CORRIDA.x + 0.05, P_FURO_CORRIDA.y + 0.30, P_FURO_CORRIDA.z))
# canaleta com metal líquido incandescente
caixa_de(bm_bica, (P_FURO_CORRIDA.x - 0.03, P_FURO_CORRIDA.y + 0.02, P_FURO_CORRIDA.z - 0.01),
                  (P_FURO_CORRIDA.x + 0.03, P_FURO_CORRIDA.y + 0.28, P_FURO_CORRIDA.z + 0.01))
# canal de escória (slag runner) desviando lateralmente
caixa_de(bm_bica, (P_FURO_CORRIDA.x - 0.18, P_FURO_CORRIDA.y + 0.15, 0.25),
                  (P_FURO_CORRIDA.x - 0.04, P_FURO_CORRIDA.y + 0.22, 0.32))
obj('bica_refrataria', bm_bica, 'tijolo')

# veio de metal líquido caindo na lingoteira
bm_metal = bmesh.new()
tubo(bm_metal, P_FURO_CORRIDA + Vector((0, 0.28, 0.0)), Vector((-0.48, 0.42, 0.24)), 0.016, 10)
obj('veio_metal_liquido', bm_metal, 'metal_liquido')

# esteira/corrente de lingoteiras (de y = 0.35 até y = 0.96 m em x = -0.48 m)
bm_ling_est = bmesh.new()
caixa_de(bm_ling_est, (-0.60, 0.30, Z0), (-0.36, 0.96, 0.20))
# roletes e corrente
for yl in (0.35, 0.50, 0.65, 0.80, 0.95):
    cil(bm_ling_est, Vector((-0.48, yl, 0.18)), 0.024, 0.22, Vector((1, 0, 0)), lados=14)
obj('esteira_lingoteira_base', bm_ling_est, 'grafite')

# lingotes individuais animados que esfriam e avançam
lingotes = []
for k in range(5):
    bm_ling = bmesh.new()
    caixa(bm_ling, (0, 0, 0.02), (0.16, 0.09, 0.04))
    o = obj('lingote_%d' % k, bm_ling, 'lingote')
    lingotes.append(o)

# bico de spray de resfriamento com vapor
bm_spray = bmesh.new()
P_SPRAY = Vector((-0.48, 0.65, 0.36))
tubo(bm_spray, P_SPRAY + Vector((-0.10, 0, 0)), P_SPRAY + Vector((0.10, 0, 0)), 0.012, 10)
for dx in (-0.05, 0.05):
    cil(bm_spray, P_SPRAY + Vector((dx, 0, -0.02)), 0.014, 0.02, lados=8)
obj('spray_resfriamento', bm_spray, 'aco_estrutural')

# ------------------------------------------------------------------ RECUPERADOR TÉRMICO E CHAMINÉ COM DOWNCOMER
# Downcomer (tubo de gás de topo) saindo do sino e descendo até o recuperador
P_RECUP = Vector((-0.55, -0.50, 0))
bm_down = bmesh.new()
cano(bm_down, bm_down, bm_down, [P_TOPO_SKIP + Vector((-0.10, 0.05, 0.30)), Vector((P_RECUP.x, -0.30, 2.55)),
                                 Vector((P_RECUP.x, P_RECUP.y, 1.85)), Vector((P_RECUP.x, P_RECUP.y, 1.30))], 0.045)
suavizar(obj('duto_downcomer', bm_down, 'primer_oxido'))

# vaso cilíndrico do recuperador térmico
bm_rec = bmesh.new()
cil(bm_rec, P_RECUP + Vector((0, 0, 0.70)), 0.18, 1.20, lados=28)
bmesh.ops.create_uvsphere(bm_rec, u_segments=28, v_segments=12, radius=1.0,
                          matrix=Matrix.Translation(P_RECUP + Vector((0, 0, 1.30))) @ Matrix.Diagonal((0.18, 0.18, 0.08, 1)))
suavizar(obj('recuperador_corpo', bm_rec, 'casco_forno'))

# chaminé alta de exaustão com anéis de reforço e chapéu
bm_cham = bmesh.new()
Z_CHAM = 3.45
tubo(bm_cham, P_RECUP + Vector((0, 0, 1.35)), P_RECUP + Vector((0, 0, Z_CHAM)), 0.065, 20)
for zc in (1.8, 2.3, 2.8, 3.2):
    cil(bm_cham, P_RECUP + Vector((0, 0, zc)), 0.08, 0.02, lados=20)
# chapéu cônico no topo
bmesh.ops.create_cone(bm_cham, cap_ends=False, segments=20, radius1=0.11, radius2=0.07, depth=0.08,
                      matrix=Matrix.Translation(P_RECUP + Vector((0, 0, Z_CHAM + 0.04))))
suavizar(obj('chamine_alta', bm_cham, 'casco_forno'))

# ------------------------------------------------------------------ FENÔMENO DA IA: ANEL DE CONTENÇÃO MAGNÉTICA DE FUSÃO
# Anel circular em latão escovado com bobinas quânticas em torno do pescoço de fusão (z = 1.65 m)
bm_mag = bmesh.new()
toro(bm_mag, FC + Vector((0, 0, 1.65)), 0.52, 0.028, nR=32, nr=10)
for k in range(6):
    a = k * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    cil(bm_mag, FC + d * 0.52 + Vector((0, 0, 1.65)), 0.042, 0.06, Vector((math.sin(a), -math.cos(a), 0)), lados=12)
obj('anel_mag_ia', bm_mag, 'cobre')

# cristal térmico pulsante da IA no console frontal
o_cristal = bpy.data.objects.new('cristal_termico', None)
sc.collection.objects.link(o_cristal)
o_cristal.location = FC + Vector((0, -R_VENTRE - 0.06, 1.35))
bm_cr = bmesh.new()
bmesh.ops.create_icosphere(bm_cr, subdivisions=1, radius=0.055)
obj('cristal_termico_malha', bm_cr, 'cristal_ia', o_cristal)

# ------------------------------------------------------------------ EFEITOS: Faíscas, Fumaça e Vapor
faiscas = []
vel_f = []
for k in range(12):
    bm_f = bmesh.new()
    bmesh.ops.create_icosphere(bm_f, subdivisions=1, radius=0.006)
    o = obj('EFEITO_faisca_%d' % k, bm_f, 'faisca')
    faiscas.append(o)
    a = random.uniform(0, 2 * PI)
    elev = random.uniform(0.4, 1.3)
    v = random.uniform(0.8, 2.0)
    vel_f.append(Vector((math.cos(a) * math.cos(elev) * v, math.sin(a) * math.cos(elev) * v, math.sin(elev) * v)))

fumacas = []
for k in range(5):
    bm_fm = bmesh.new()
    bmesh.ops.create_icosphere(bm_fm, subdivisions=1, radius=0.08)
    o = obj('EFEITO_fumaca_%d' % k, bm_fm, 'fumaca')
    fumacas.append(o)

vapores = []
for k in range(4):
    bm_vp = bmesh.new()
    bmesh.ops.create_icosphere(bm_vp, subdivisions=1, radius=0.06)
    o = obj('EFEITO_vapor_%d' % k, bm_vp, 'vapor')
    vapores.append(o)

# iluminação pontual da brasa de vazamento
luz_brasa = bpy.data.lights.new('LuzBrasa', 'POINT')
luz_brasa.color = (1.0, 0.45, 0.1)
luz_brasa.energy = 30.0
o_luz_brasa = bpy.data.objects.new('EFEITO_LuzBrasa', luz_brasa)
sc.collection.objects.link(o_luz_brasa)
o_luz_brasa.location = Vector((-0.48, 0.45, 0.32))


# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço contínuo)
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    u = (q - 1) / QUADROS
    t = (q - 1) / FPS

    # 1. Skip car subindo nos trilhos, basculando e descendo (ciclo de 4 s)
    if u < 0.45:
        # subindo
        w = u / 0.45
        pos_skip = P_ENT_SUL.lerp(P_TOPO_SKIP, w) + Vector((0, 0.05, 0.08))
        rot_skip = (0, 0, 0)
    elif u < 0.60:
        # basculando minério no topo
        w_b = (u - 0.45) / 0.15
        pos_skip = P_TOPO_SKIP + Vector((0, 0.05, 0.08))
        rot_skip = (math.radians(-35 * math.sin(w_b * PI)), 0, 0)
    else:
        # descendo de volta
        w_d = (u - 0.60) / 0.40
        pos_skip = P_TOPO_SKIP.lerp(P_ENT_SUL, w_d) + Vector((0, 0.05, 0.08))
        rot_skip = (0, 0, 0)

    o_skip.location = pos_skip
    o_skip.rotation_euler = rot_skip
    o_skip.keyframe_insert('location', frame=q)
    o_skip.keyframe_insert('rotation_euler', frame=q)

    # 2. Rotação contínua do soprador de ar forçado (4 voltas por ciclo)
    o_rotor_sopro.rotation_euler = (0, u * 8 * PI, 0)
    o_rotor_sopro.keyframe_insert('rotation_euler', frame=q)

    # 3. Lingotes de aço avançando continuamente na esteira norte
    for k, o in enumerate(lingotes):
        ul = (k / len(lingotes) + u) % 1.0
        y_ling = 0.35 + ul * 0.61
        o.location = Vector((-0.48, y_ling, 0.22))
        o.keyframe_insert('location', frame=q)

    # 4. Faíscas de aço fundido pulando na bica
    p_vaza = Vector((-0.48, 0.42, 0.24))
    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + u * 5) % 1.0) * 0.28
        o.location = p_vaza + vel_f[k] * tt + Vector((0, 0, -4.9 * tt * tt))
        o.keyframe_insert('location', frame=q)

    # 5. Fumaça saindo da chaminé alta
    for k, o in enumerate(fumacas):
        uf = (k / len(fumacas) + u * 2) % 1.0
        o.location = P_RECUP + Vector((0.05 * math.sin(k + uf * 3), 0.04 * math.cos(k), Z_CHAM + 0.10 + 0.9 * uf))
        s = 0.05 + 0.20 * uf
        o.scale = (s, s, s)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)

    # 6. Vapor de resfriamento subindo do spray
    for k, o in enumerate(vapores):
        uv = (k / len(vapores) + u * 3) % 1.0
        o.location = Vector((-0.48 + 0.04 * math.sin(k + uv * 4), 0.65 + 0.03 * math.cos(k), 0.25 + 0.5 * uv))
        sv = 0.04 + 0.14 * uv
        o.scale = (sv, sv, sv)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)

    # 7. Pulso do cristal térmico da IA
    pulso_cr = 1.0 + 0.15 * math.sin(u * 6 * PI)
    o_cristal.scale = (pulso_cr, pulso_cr, pulso_cr)
    o_cristal.keyframe_insert('scale', frame=q)

    # 8. Tremor na intensidade da luz da brasa
    luz_brasa.energy = 28.0 + 6.0 * math.sin(u * 18 * PI)
    luz_brasa.keyframe_insert('energy', frame=q)


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


ALVO = (0.0, 0.0, 0.95)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo in ('foto', 'perto'):
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    if modo == 'foto':
        sc.frame_set(int(QUADROS * 0.25) + 1)
        for i, (ang, alt) in enumerate(((305, 4.4), (215, 4.2), (125, 4.6), (35, 4.0))):
            a = math.radians(ang)
            mirar(Vector(ALVO) + Vector((math.cos(a) * 4.2, math.sin(a) * 4.2, alt)), ALVO, 32)
            sc.render.filepath = os.path.join(AQUI, 'fornalha_aco_%d.png' % i)
            bpy.ops.render.render(write_still=True)
    sc.frame_set(int(QUADROS * 0.35))
    # close-up olhando para o vazamento de metal líquido, lingoteiras, bica e ventaneiras
    mirar((-1.35, 0.65, 1.25), (-0.40, 0.35, 0.35), 34)
    sc.render.filepath = os.path.join(AQUI, 'fornalha_aco_perto.png')
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
    sc.render.filepath = os.path.join(AQUI, 'fornalha_aco_video.mp4')
    bpy.ops.render.render(animation=True)

total_tris = sum(len(o.data.polygons) * 2 for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO') and not o.name == 'chao')
print('FORNALHA DE ACO ok — tris aproximados: %d' % total_tris)
