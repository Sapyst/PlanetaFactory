"""Estudo isolado (fora do jogo): fornalha de fundição a carvão, 2×2 tiles. Entrada pelo sul (tile da direita),
saída pelo norte (tile da esquerda), como no jogo.
Base de tijolo refratário com fuligem; casco de aço com cintas, rebites e marcas de calor; chaminé alta com fumaça.
Caçamba sobe os trilhos puxada por guincho, vira carvão e minério na boca de carga e desce. Soprador centrífugo com
rotor girando atrás da grade, duto até o anel de ar e canos até as ventaneiras. Porta de ferro fundido com frestas em
brasa. Bica de vazamento despeja metal líquido (com faíscas) em lingoteiras numa corrente; a barra esfria do laranja
ao cinza passando pelo spray d'água (vapor). Escória, pó de carvão, óleo e ferrugem.
Uso: blender -b --python estudo_fornalha.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24


def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=64, nr=16):
    """Anel tubular contínuo (sem emendas)."""
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))
QUADROS = 96                 # 4 s em laço
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def tijolo_mat():
    """Tijolo refratário: textura de tijolos, rejunte claro, fuligem que escurece para cima e manchas."""
    m = bpy.data.materials.new('Tijolo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = no(nt, 'ShaderNodeTexCoord')
    tj = no(nt, 'ShaderNodeTexBrick', **{'Scale': 4.0, 'Mortar Size': 0.008, 'Brick Width': 0.9, 'Row Height': 0.28})
    tj.inputs['Color1'].default_value = (0.36, 0.14, 0.07, 1)
    tj.inputs['Color2'].default_value = (0.26, 0.10, 0.05, 1)
    tj.inputs['Mortar'].default_value = (0.30, 0.28, 0.25, 1)
    sx = no(nt, 'ShaderNodeSeparateXYZ')                       # tijolos deitados: fiadas ao longo de z, volta pelo arco
    nt.links.new(tc.outputs['Object'], sx.inputs[0])
    arco = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(sx.outputs['X'], arco.inputs[0])
    nt.links.new(sx.outputs['Y'], arco.inputs[1])
    cx = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(arco.outputs['Value'], cx.inputs['X'])
    nt.links.new(sx.outputs['Z'], cx.inputs['Y'])
    nt.links.new(cx.outputs[0], tj.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    fu = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.15, 'From Max': 0.6, 'To Min': 0.1, 'To Max': 0.75})
    nt.links.new(sep.outputs['Z'], fu.inputs['Value'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(fu.outputs['Result'], soma.inputs[0])
    nt.links.new(ru.outputs['Fac'], soma.inputs[1])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[7].default_value = (0.02, 0.018, 0.016, 1)
    nt.links.new(soma.outputs['Value'], mix.inputs[0])
    nt.links.new(tj.outputs['Color'], mix.inputs[6])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.92
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    nt.links.new(tj.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def brasa_mat(nome, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1.0, 0.35, 0.05, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.33, 0.04, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def lingote_mat():
    """Barra que esfria conforme anda para o norte (y no mundo): brasa amarela → vermelho → aço cinza."""
    m = mats.material('Lingote', (0.30, 0.30, 0.31), 1.0, 0.45, pintura=False, sujeira=0.3, ferrugem=0.0)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    quente = no(nt, 'ShaderNodeMapRange', **{'From Min': Y_VAZA, 'From Max': 0.88, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sep.outputs['Y'], quente.inputs['Value'])
    pot = no(nt, 'ShaderNodeMath', operation='POWER')
    pot.inputs[1].default_value = 2.2
    nt.links.new(quente.outputs['Result'], pot.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.6, 0.04, 0.0, 1)
    cor.inputs[7].default_value = (1.0, 0.55, 0.12, 1)
    nt.links.new(quente.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Emission Color'])
    forca = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    forca.inputs[1].default_value = 9.0
    nt.links.new(pot.outputs['Value'], forca.inputs[0])
    nt.links.new(forca.outputs['Value'], b.inputs['Emission Strength'])
    return m


def fumaca_grad_mat(nome, dens, z0, z1):
    """Fumaça que sai preta e se dilui em cinza claro conforme sobe (z0 → z1 no mundo)."""
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


def fogo_mat():
    """Labareda em volume: núcleo amarelo, borda laranja, some nas pontas."""
    m = base3d.volume_mat('Fogo', (1.0, 0.4, 0.05), 3.0, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 70.0
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)          # absorve: não fica pálido sob o sol
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1)
    return m


Y_VAZA = 0.45                # onde a bica despeja (y da lingoteira)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'queimado': mats.material('Queimado', (0.13, 0.11, 0.12), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'carvao': mats.material('Carvão', (0.02, 0.02, 0.022), 0, 0.6, pintura=False, sujeira=0.0, desgaste=0.0),
    'minerio': mats.material('Minério', (0.30, 0.13, 0.07), 0.2, 0.7, pintura=False, sujeira=0.5, ferrugem=0.5),
    'escoria': mats.material('Escória', (0.035, 0.03, 0.028), 0.0, 0.08, pintura=False, sujeira=0.2, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'po': mats.material('Pó de carvão', (0.025, 0.024, 0.024), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'tijolo': tijolo_mat(),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'metal_liquido': brasa_mat('Metal líquido', 40.0),
    'frestas': brasa_mat('Frestas', 18.0),
    'faisca': brasa_mat('Faísca', 60.0),
    'lingote': lingote_mat(),
    'fumaca': fumaca_grad_mat('Fumaça', 12.0, 3.0, 4.8),
    'vazamento': fumaca_grad_mat('Vazamento', 5.0, 0.9, 2.0),
    'fogo': fogo_mat(),
    'vapor': base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 3.0, 0.35, 1.1),
})

S = Vector((0.15, 0.15, 0))  # eixo do forno
R_TIJ, R_CASCO = 0.56, 0.48
Z_TIJ, Z_CASCO, Z_CONE = 0.56, 1.45, 1.72
Z_CHAMINE = 3.0

# ------------------------------------------------------------------ laje e base de tijolo
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()
caixa_de(bm, (-0.985, -0.985, 0.0), (0.985, -0.97, 0.08))
caixa_de(bm, (-0.985, 0.97, 0.0), (0.985, 0.985, 0.08))
obj('laje_listras', bm, 'listras')
bm = bmesh.new()
cil(bm, S + Vector((0, 0, (0.08 + Z_TIJ) / 2)), R_TIJ, Z_TIJ - 0.08, lados=24)
obj('base_tijolo', bm, 'tijolo')
bm = bmesh.new()
for z in (0.1, Z_TIJ - 0.03):                                             # cintas de aço na base
    cil(bm, S + Vector((0, 0, z)), R_TIJ + 0.012, 0.04, lados=24)
for k in range(8):                                                        # nervuras verticais (contrafortes)
    a = k * PI / 4 + PI / 8
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, S + d * (R_TIJ + 0.015) + Vector((0, 0, 0.32)), (0.035, 0.035, 0.48), Matrix.Rotation(a, 3, 'Z'))
obj('base_cintas', bm, 'ferro')

# ------------------------------------------------------------------ casco de aço, cone e chaminé
bm = bmesh.new()
cil(bm, S + Vector((0, 0, (Z_TIJ + Z_CASCO) / 2)), R_CASCO, Z_CASCO - Z_TIJ, lados=28)
obj('casco', bm, 'casco')
bm = bmesh.new()
cil(bm, S + Vector((0, 0, (Z_CASCO + Z_CONE) / 2)), R_CASCO, Z_CONE - Z_CASCO, lados=28, r2=0.2)
cil(bm, S + Vector((0, 0, (Z_CONE + Z_CHAMINE) / 2)), 0.13, Z_CHAMINE - Z_CONE, lados=24)
suavizar(obj('cone_chamine', bm, 'queimado'))
bm, br = bmesh.new(), bmesh.new()
for z in (0.72, 0.98, 1.24, Z_CASCO - 0.02):                              # cintas do casco com rebites
    cil(bm, S + Vector((0, 0, z)), R_CASCO + 0.01, 0.035, lados=28)
    for k in range(20):
        a = k * 2 * PI / 20
        cil(br, S + Vector((math.cos(a) * (R_CASCO + 0.018), math.sin(a) * (R_CASCO + 0.018), z)), 0.007, 0.01,
            Vector((math.cos(a), math.sin(a), 0)), lados=6)
for z in (2.0, 2.4, 2.8):                                                 # cintas da chaminé
    cil(bm, S + Vector((0, 0, z)), 0.145, 0.03, lados=16)
cil(bm, S + Vector((0, 0, Z_CHAMINE + 0.03)), 0.17, 0.05, lados=16)       # boca da chaminé
for sx in (-1, 1):                                                        # estais da chaminé
    viga(bm, S + Vector((sx * 0.14, 0, 2.6)), S + Vector((sx * 0.46, 0, Z_CASCO)), 0.012)
obj('cintas', bm, 'ferro')
obj('rebites', br, 'aco')

# ------------------------------------------------------------------ anel de ar (sopro), ventaneiras e duto do soprador
Z_ANEL, R_ANEL = 0.84, 0.66
bm, bf = bmesh.new(), bmesh.new()
toro(bm, S + Vector((0, 0, Z_ANEL)), R_ANEL, 0.055)
for k in range(8):                                                        # ventaneiras: do anel para dentro do casco
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    p0 = S + d * R_ANEL + Vector((0, 0, Z_ANEL - 0.04))
    p1 = S + d * (R_ANEL - 0.02) + Vector((0, 0, Z_ANEL - 0.2))
    p2 = S + d * (R_CASCO - 0.01) + Vector((0, 0, 0.62))
    tubo(bm, p0, p1, 0.026, 14)
    tubo(bm, p1, p2, 0.026, 14)
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=0.026, matrix=Matrix.Translation(p1))   # cotovelo
    cil(bf, p1, 0.034, 0.03, lados=8)                                     # flange do cotovelo
    cil(bf, p2 + d * 0.02, 0.04, 0.03, d, lados=8)                        # bocal no casco
for k in range(6):                                                        # suportes do anel no casco
    a = k * PI / 3 + PI / 6
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(bf, S + d * R_CASCO + Vector((0, 0, Z_ANEL + 0.1)), S + d * R_ANEL + Vector((0, 0, Z_ANEL + 0.04)), 0.025)
suavizar(obj('anel_ar', bm, 'casco'))
obj('anel_flanges', bf, 'ferro')

# soprador centrífugo (caracol) a oeste-sul, com rotor visível atrás da grade
B = Vector((-0.66, -0.5, 0.36))
RB = 0.24
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=RB, radius2=RB, depth=0.18,
                      matrix=Matrix.Translation(B) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
cil(bm, B + Vector((-0.09, 0, 0)), RB, 0.008, Vector((1, 0, 0)), lados=24)           # tampa oeste
caixa_de(bm, (B.x - 0.09, B.y - 0.02, B.z), (B.x + 0.09, B.y + RB, B.z + RB + 0.12))  # bocal de saída (sobe)
caixa_de(bm, (B.x - 0.13, B.y - 0.2, 0.08), (B.x + 0.13, B.y + 0.2, 0.13))           # pé
obj('soprador', bm, 'amarelo')
bm = bmesh.new()
for k in range(-5, 6):                                                    # grade da entrada (face leste)
    caixa(bm, B + Vector((0.092, k * 0.04, 0)), (0.006, 0.008, 2 * math.sqrt(max(RB ** 2 - (k * 0.04) ** 2, 0.0004))))
cil(bm, B + Vector((0.093, 0, 0)), RB, 0.012, Vector((1, 0, 0)), lados=24)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.x) > 0.9 and abs(f.calc_center_median().x - (B.x + 0.093)) < 0.007], context='FACES_ONLY')
obj('soprador_grade', bm, 'ferro')
rotor = bpy.data.objects.new('rotor', None)
sc.collection.objects.link(rotor)
rotor.location = B
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.05, 0.12, Vector((1, 0, 0)), lados=12)
for k in range(10):                                                       # pás curvas
    a = k * 2 * PI / 10
    caixa(bm, Matrix.Rotation(a, 3, 'X') @ Vector((0.0, 0.0, 0.14)), (0.12, 0.012, 0.17),
          Matrix.Rotation(a, 3, 'X') @ Matrix.Rotation(0.4, 3, 'X'))
obj('rotor_pas', bm, 'aco', rotor)
bm = bmesh.new()                                                          # motor do soprador (oeste) com aletas
cil(bm, B + Vector((-0.22, 0, 0)), 0.1, 0.22, Vector((1, 0, 0)), lados=14)
for k in range(6):
    cil(bm, B + Vector((-0.14 - k * 0.032, 0, 0)), 0.118, 0.008, Vector((1, 0, 0)), lados=14)
caixa(bm, B + Vector((-0.22, 0, -0.13)), (0.2, 0.18, 0.06))
caixa(bm, B + Vector((-0.2, 0.1, 0.06)), (0.08, 0.06, 0.07))              # caixa de ligação
obj('soprador_motor', bm, 'grafite')
bm = bmesh.new()                                                          # duto: bocal → sobe → anel
alvo = S + (B - S).xy.to_3d().normalized() * R_ANEL
alvo.z = Z_ANEL
topo_b = Vector((B.x, B.y + RB / 2, Z_ANEL))
tubo(bm, Vector((B.x, B.y + RB / 2, B.z + RB + 0.1)), topo_b, 0.07, 20)
tubo(bm, topo_b, alvo, 0.07, 20)
bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=0.07, matrix=Matrix.Translation(topo_b))   # curva
suavizar(obj('duto', bm, 'casco'))
bm = bmesh.new()
for p in (topo_b + Vector((0, 0, -0.09)), Vector((B.x, B.y + RB / 2, B.z + RB + 0.12))):
    cil(bm, p, 0.085, 0.025, lados=20)
obj('duto_flanges', bm, 'ferro')
bm = bmesh.new()                                                          # manômetro no duto
cil(bm, topo_b + Vector((0.0, -0.09, 0.1)), 0.035, 0.015, Vector((0, -1, 0)), lados=16)
obj('manometro', bm, 'cromo')

# ------------------------------------------------------------------ porta da fornalha (leste) com frestas em brasa
PORTA = S + Vector((R_TIJ + 0.005, 0, 0.3))
bm = bmesh.new()
caixa(bm, PORTA + Vector((0.02, 0, 0)), (0.04, 0.38, 0.34))               # batente
obj('porta_batente', bm, 'ferro')
bm = bmesh.new()
for k in range(5):                                                        # chapas da porta com frestas entre elas
    caixa(bm, PORTA + Vector((0.055, 0, -0.12 + k * 0.06)), (0.03, 0.28, 0.045))
for sy in (-1, 1):
    cil(bm, PORTA + Vector((0.06, sy * 0.16, 0.08 * sy)), 0.018, 0.06, lados=8)   # dobradiças
caixa(bm, PORTA + Vector((0.08, 0.1, 0)), (0.02, 0.025, 0.12))            # trinco
obj('porta', bm, 'ferro')
bm = bmesh.new()
caixa(bm, PORTA + Vector((0.035, 0, -0.0)), (0.01, 0.27, 0.28))
obj('porta_brasa', bm, 'frestas')
luz_porta = bpy.data.lights.new('Brasa', 'POINT')
luz_porta.color = (1.0, 0.45, 0.12)
luz_porta.shadow_soft_size = 0.1
lp = bpy.data.objects.new('Brasa', luz_porta)
sc.collection.objects.link(lp)
lp.location = PORTA + Vector((0.25, 0, 0.0))

# ------------------------------------------------------------------ caçamba: trilhos, guincho e carro (entrada sul, tile da direita)
R0 = Vector((0.52, -0.88, 0.14))                                          # fundo (poço de carga)
R1 = Vector((0.52, -0.46, Z_CASCO + 0.16))                                # topo: por fora do casco e do anel
U = (R1 - R0).normalized()
LAT = Vector((1, 0, 0))
NRM = U.cross(LAT).normalized()                                           # perpendicular aos trilhos, para cima
if NRM.z < 0:
    NRM = -NRM
ROT_T = Matrix((LAT, U, NRM)).transposed()
bm = bmesh.new()
for sx in (-1, 1):
    a, b = R0 + LAT * sx * 0.13, R1 + LAT * sx * 0.13 + U * 0.08
    viga(bm, a, b, 0.035)
for t in (0.2, 0.55):                                                     # pernas até a laje
    p = R0 + (R1 - R0) * t
    for sx in (-1, 1):
        q = p + LAT * sx * 0.13
        viga(bm, q, Vector((q.x, q.y, 0.08)), 0.035)
    viga(bm, p + LAT * -0.13 - NRM * 0.02, p + LAT * 0.13 - NRM * 0.02, 0.03)
for t in (0.85, 1.0):                                                     # travessas no topo e mão-francesa no casco
    p = R0 + (R1 - R0) * t
    viga(bm, p + LAT * -0.13, p + LAT * 0.13, 0.03)
for sx in (-1, 1):                                                        # escora do topo: diagonal para o sul, fora do anel
    q0 = R1 + LAT * sx * 0.13 - U * 0.05
    viga(bm, q0, Vector((q0.x, -0.74, 0.08)), 0.035)
    caixa(bm, Vector((q0.x, -0.74, 0.09)), (0.08, 0.08, 0.02))
obj('trilhos', bm, 'amarelo')
bm = bmesh.new()                                                          # poço de carga com carvão e minério
caixa_de(bm, (0.3, -0.98, 0.08), (0.74, -0.96, 0.3))
for sx in (0.3, 0.74):
    caixa_de(bm, (sx - 0.01, -0.98, 0.08), (sx + 0.01, -0.66, 0.3))
obj('poco', bm, 'ferro')
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(55):
    c = Vector((random.uniform(0.32, 0.72), random.uniform(-0.95, -0.7), 0.1 + random.uniform(0, 0.08)))
    pedra(bm if random.random() < 0.6 else bm2, c, random.uniform(0.018, 0.035))
obj('poco_carvao', bm, 'carvao')
obj('poco_minerio', bm2, 'minerio')
bm = bmesh.new()                                                          # guincho no topo
GUI = R1 + U * 0.04 + NRM * 0.14
cil(bm, GUI, 0.06, 0.2, LAT, lados=14)
for sx in (-1, 1):
    cil(bm, GUI + LAT * sx * 0.105, 0.08, 0.012, LAT, lados=14)
    viga(bm, GUI + LAT * sx * 0.12, R1 + LAT * sx * 0.13 + U * 0.04, 0.03)
cil(bm, GUI + LAT * 0.22, 0.06, 0.13, LAT, lados=12)                      # motor do guincho
obj('guincho', bm, 'grafite')
bm = bmesh.new()                                                          # calha de carga: topo dos trilhos → boca no cone
c0 = R1 + U * 0.02 + NRM * 0.02
dirc = (S.xy - c0.xy).to_3d().normalized()
c1 = S + dirc * -0.2 + Vector((0, 0, 1.64))                               # boca no cone (raio ~0,26 nessa altura)
c1 = S + (c0 - S).xy.to_3d().normalized() * 0.22 + Vector((0, 0, 1.64))
dc = c1 - c0
fr_c = dc.normalized()
lat_c = Vector((0, 0, 1)).cross(fr_c).normalized()
rot_c = Matrix((fr_c, lat_c, fr_c.cross(lat_c) * -1 if fr_c.cross(lat_c).z < 0 else fr_c.cross(lat_c))).transposed()
rot_c = Matrix((lat_c, fr_c, lat_c.cross(fr_c))).transposed()
caixa(bm, (c0 + c1) / 2, (0.3, dc.length, 0.012), rot_c)                  # fundo
for sx in (-1, 1):
    caixa(bm, (c0 + c1) / 2 + rot_c @ Vector((sx * 0.15, 0, 0.06)), (0.012, dc.length, 0.12), rot_c)
cil(bm, c1 + Vector((0, 0, 0.0)), 0.13, 0.08, lados=16)                   # colar da boca de carga no cone
for t in (0.3, 0.75):                                                     # suportes da calha no cone
    p = c0 + dc * t
    viga(bm, p - Vector((0, 0, 0.02)), S + (p - S).xy.to_3d().normalized() * (R_CASCO - 0.01) + Vector((0, 0, Z_CASCO - 0.05)), 0.025)
obj('boca_carga', bm, 'ferro')

carro = bpy.data.objects.new('carro', None)
sc.collection.objects.link(carro)
carro.rotation_mode = 'QUATERNION'
bm = bmesh.new()
caixa(bm, (0, 0, 0.05), (0.22, 0.2, 0.012))                               # fundo
caixa(bm, (0, -0.1, 0.11), (0.22, 0.012, 0.12))                           # traseira
caixa(bm, (0, 0.1, 0.1), (0.22, 0.012, 0.1))                              # frente (bica)
for sx in (-1, 1):
    caixa(bm, (sx * 0.11, 0, 0.1), (0.012, 0.2, 0.11))
obj('carro_cacamba', bm, 'amarelo', carro)
bm = bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(bm, Vector((sx * 0.13, sy * 0.07, 0.02)), 0.028, 0.02, Vector((1, 0, 0)), lados=10)   # rodas
caixa(bm, (0, 0.11, 0.17), (0.05, 0.03, 0.03))                            # olhal do cabo
obj('carro_rodas', bm, 'ferro', carro)
carga = bpy.data.objects.new('carga', None)
sc.collection.objects.link(carga)
carga.parent = carro
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(14):
    pedra(bm if k % 2 else bm2, (random.uniform(-0.08, 0.08), random.uniform(-0.07, 0.07), 0.09 + random.uniform(0, 0.06)), 0.03)
obj('carga_carvao', bm, 'carvao', carga)
obj('carga_minerio', bm2, 'minerio', carga)
bm = bmesh.new()                                                          # cabo: unidade em z, esticado a cada quadro
cil(bm, Vector((0, 0, 0.5)), 0.006, 1.0, lados=6)
cabo = obj('cabo', bm, 'aco')
cabo.rotation_mode = 'QUATERNION'

# ------------------------------------------------------------------ bica de vazamento e lingoteiras (saída norte, tile da esquerda)
XL = -0.5
dir_b = (Vector((XL, Y_VAZA, 0)) - S).xy.to_3d().normalized()
A_B = S + dir_b * (R_TIJ - 0.02) + Vector((0, 0, 0.47))
LABIO = Vector((XL + 0.0, Y_VAZA, 0.42))
bm = bmesh.new()
d = (LABIO - A_B)
rot_b = Matrix((d.normalized(), Vector((0, 0, 1)).cross(d.normalized()).normalized(), Vector((0, 0, 1)))).transposed()
caixa(bm, (A_B + LABIO) / 2, (d.length + 0.04, 0.12, 0.02), rot_b)        # calha refratária da bica
for sy in (-1, 1):
    caixa(bm, (A_B + LABIO) / 2 + rot_b @ Vector((0, sy * 0.06, 0.035)), (d.length + 0.04, 0.015, 0.07), rot_b)
caixa(bm, A_B + Vector((0, 0, 0.02)), (0.16, 0.16, 0.12), rot_b)          # bloco do furo de corrida
obj('bica', bm, 'ferro')
bm = bmesh.new()
caixa(bm, (A_B + LABIO) / 2 + Vector((0, 0, 0.013)), (d.length + 0.02, 0.09, 0.008), rot_b)
cil(bm, LABIO + Vector((0, 0, -0.09)), 0.016, 0.16, lados=10)             # jato de metal caindo
obj('metal_jato', bm, 'metal_liquido')
luz_vaza = bpy.data.lights.new('Vazamento', 'POINT')
luz_vaza.color = (1.0, 0.5, 0.15)
luz_vaza.energy = 25
luz_vaza.shadow_soft_size = 0.05
lv = bpy.data.objects.new('Vazamento', luz_vaza)
sc.collection.objects.link(lv)
lv.location = LABIO + Vector((0.06, -0.06, -0.02))

# corrente de lingoteiras: laço com trecho de cima indo para o norte
Y0, Y1, ZL, RL = 0.28, 0.92, 0.26, 0.07
LR = Y1 - Y0
TOTAL_L = 2 * LR + 2 * PI * RL
N_L = int(round(TOTAL_L / 0.14))
PASSO_L = TOTAL_L / N_L
bm = bmesh.new()                                                          # estrutura da lingoteira
for sx in (-1, 1):
    caixa_de(bm, (XL + sx * 0.13 - 0.012, Y0 - 0.1, ZL - 2 * RL - 0.04), (XL + sx * 0.13 + 0.012, Y1 + 0.1, ZL - 0.02))
    for y in (Y0, Y1):
        caixa_de(bm, (XL + sx * 0.13 - 0.02, y - 0.02, 0.08), (XL + sx * 0.13 + 0.02, y + 0.02, ZL - 2 * RL - 0.04))
obj('lingoteira_estrutura', bm, 'grafite')
bm = bmesh.new()
for y in (Y0, Y1):
    cil(bm, Vector((XL, y, ZL - RL)), 0.012, 0.3, Vector((1, 0, 0)), lados=8)
obj('lingoteira_eixos', bm, 'cromo')
moldes, lingotes = [], []
for k in range(N_L):
    mo = bpy.data.objects.new('molde', None)
    sc.collection.objects.link(mo)
    mo.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    caixa(bm, (0, 0, -0.012), (0.2, PASSO_L - 0.012, 0.012))
    for sy in (-1, 1):
        caixa(bm, (0, sy * (PASSO_L - 0.012) / 2, 0.015), (0.2, 0.012, 0.042))
    for sx in (-1, 1):
        caixa(bm, (sx * 0.1, 0, 0.015), (0.012, PASSO_L - 0.012, 0.042))
    obj('molde_ferro', bm, 'ferro', mo)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.012), (0.17, PASSO_L - 0.04, 0.03))
    li = obj('lingote', bm, 'lingote', mo)
    moldes.append(mo)
    lingotes.append(li)


def no_laco_l(u):
    """Molde a u metros do começo do trecho de cima (indo para +y): posição e rotação em torno de x."""
    if u < LR:
        return Vector((XL, Y0 + u, ZL)), 0.0
    u -= LR
    if u < PI * RL:
        a = u / RL
        return Vector((XL, Y1 + RL * math.sin(a), ZL - RL + RL * math.cos(a))), -a
    u -= PI * RL
    if u < LR:
        return Vector((XL, Y1 - u, ZL - 2 * RL)), -PI
    u -= LR
    a = PI + u / RL
    return Vector((XL, Y0 + RL * math.sin(a), ZL - RL + RL * math.cos(a))), -a


bm = bmesh.new()                                                          # spray d'água sobre as lingoteiras
Y_AGUA = 0.68
tubo(bm, (XL - 0.16, Y_AGUA, ZL + 0.2), (XL + 0.16, Y_AGUA, ZL + 0.2), 0.016)
tubo(bm, (XL + 0.16, Y_AGUA, ZL + 0.2), (XL + 0.16, Y_AGUA, 0.08), 0.016)
for k in range(5):
    cil(bm, Vector((XL - 0.12 + k * 0.06, Y_AGUA, ZL + 0.18)), 0.01, 0.03, lados=6)
cil(bm, Vector((XL + 0.16, Y_AGUA, 0.3)), 0.03, 0.06, lados=8)            # registro
obj('spray', bm, 'cobre')
bm = bmesh.new()                                                          # saída norte: rampa com barras frias
caixa_de(bm, (XL - 0.14, Y1 + 0.08, 0.08), (XL + 0.14, 0.98, 0.12))
for k in range(3):
    caixa(bm, (XL - 0.06 + k * 0.06, 0.95, 0.14), (0.05, 0.13, 0.03), Matrix.Rotation(0.1 * k, 3, 'Z'))
obj('saida', bm, 'aco')

# ------------------------------------------------------------------ sujeira: escória, pó de carvão, óleo, respingos
bm = bmesh.new()
for k in range(9):                                                        # escória derramada perto da bica
    c = Vector((XL + random.uniform(-0.05, 0.25), Y_VAZA + random.uniform(-0.25, 0.05), 0))
    mancha(bm, c, random.uniform(0.03, 0.08), 0.083)
for k in range(12):
    pedra(bm, Vector((XL + random.uniform(-0.0, 0.3), Y_VAZA + random.uniform(-0.3, 0.0), 0.09)), random.uniform(0.01, 0.025), 0.4)
obj('escoria', bm, 'escoria')
bm = bmesh.new()
for k in range(10):                                                       # pó de carvão em volta do poço e dos trilhos
    mancha(bm, (random.uniform(0.2, 0.85), random.uniform(-0.95, -0.4)), random.uniform(0.06, 0.14), 0.0815)
for k in range(5):
    mancha(bm, (random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9)), random.uniform(0.05, 0.12), 0.081)
obj('po_carvao', bm, 'po')
bm = bmesh.new()
for c, r in (((-0.62, -0.25), 0.1), ((-0.8, -0.55), 0.07), ((0.85, 0.3), 0.08)):
    mancha(bm, c, r, 0.0825)
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for k in range(25):                                                       # pedras e carvão caídos
    c = Vector((random.uniform(0.2, 0.9), random.uniform(-0.9, -0.3), 0.09))
    pedra(bm, c, random.uniform(0.01, 0.022))
obj('caidos', bm, 'carvao')
bm = bmesh.new()                                                          # escorridos de fuligem no casco
for k in range(14):
    a = random.uniform(0, 2 * PI)
    d = Vector((math.cos(a), math.sin(a), 0))
    z1 = random.uniform(1.1, Z_CASCO)
    caixa(bm, S + d * (R_CASCO + 0.003) + Vector((0, 0, z1 - 0.12)), (0.004, random.uniform(0.02, 0.05), random.uniform(0.15, 0.4)),
          Matrix.Rotation(a, 3, 'Z'))
obj('fuligem', bm, 'escoria')

# ------------------------------------------------------------------ fumaça, vapor e faíscas
fumacas, vapores, faiscas = [], [], []
for k in range(10):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    fumacas.append(obj('fumaca', bm, 'fumaca'))
for k in range(4):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))
for k in range(10):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.006)
    faiscas.append(obj('faisca', bm, 'faisca'))
vel_f = [Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(0.6, 1.4))) for _ in faiscas]

# ------------------------------------------------------------------ pressão interna: válvulas, vazamentos, jatos de fogo
VALVULAS = []
for ang in (200, 340):                                                    # válvulas de alívio no cone
    a = math.radians(ang)
    d = Vector((math.cos(a), math.sin(a), 0))
    base_v = S + d * 0.36 + Vector((0, 0, 1.56))
    bm = bmesh.new()
    cil(bm, base_v + Vector((0, 0, 0.06)), 0.03, 0.14, lados=12)          # tubo
    cil(bm, base_v + Vector((0, 0, 0.01)), 0.05, 0.02, lados=12)          # flange no cone
    cil(bm, base_v + Vector((0, 0, 0.15)), 0.045, 0.05, lados=12)         # corpo da válvula
    for k in range(4):                                                    # mola exposta
        cil(bm, base_v + Vector((0, 0, 0.19 + k * 0.018)), 0.03, 0.006, lados=12)
    cil(bm, base_v + Vector((0, 0, 0.27)), 0.022, 0.02, lados=12)         # chapéu
    tubo(bm, base_v + Vector((0, 0, 0.15)), base_v + Vector((0, 0, 0.15)) + d * 0.1 + Vector((0, 0, 0.04)), 0.022, 12)   # bocal de escape
    o = suavizar(obj('valvula', bm, 'ferro'))
    VALVULAS.append((base_v + Vector((0, 0, 0.15)) + d * 0.11 + Vector((0, 0, 0.045)), (d + Vector((0, 0, 0.5))).normalized(), o))
pivo = bpy.data.objects.new('pressao', None)
sc.collection.objects.link(pivo)
pivo.location = S + Vector((0, 0, Z_TIJ))
bpy.context.view_layer.update()
for nome in ('casco', 'cone_chamine', 'cintas', 'rebites', 'fuligem', 'valvula', 'boca_carga'):
    for o in [o for o in sc.objects if o.name.split('.')[0] == nome]:
        o.parent = pivo
        o.matrix_parent_inverse = pivo.matrix_world.inverted()
VAZ = []                                                                  # pontos de vazamento nas emendas das cintas
for k in range(6):
    a = random.uniform(0, 2 * PI)
    z = random.choice((0.98, 1.24, Z_CASCO - 0.02))
    d = Vector((math.cos(a), math.sin(a), 0))
    VAZ.append((S + d * (R_CASCO + 0.02) + Vector((0, 0, z + 0.02)), d))
vazamentos = []
for k in range(len(VAZ) * 2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vazamentos.append(obj('vazamento', bm, 'vazamento'))
jatos = []
for k in range(3):                                                        # 2 válvulas + boca da chaminé
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co.z = (v.co.z + 1.0) / 2.0                                     # base na origem, cresce em +z
    o = obj('jato', bm, 'fogo')
    o.rotation_mode = 'QUATERNION'
    jatos.append(o)
luzes_jato = []
for k in range(3):
    lj = bpy.data.lights.new('Clarão', 'POINT')
    lj.color = (1.0, 0.5, 0.15)
    lj.shadow_soft_size = 0.2
    oj = bpy.data.objects.new('Clarão', lj)
    sc.collection.objects.link(oj)
    luzes_jato.append(lj)
    oj.location = (VALVULAS[k][0] if k < 2 else S + Vector((0, 0, Z_CHAMINE + 0.25)))


def pressao(fr):
    """Dois ciclos por laço: pressão sobe devagar (85%) e alivia de uma vez (15%) com jato de fogo."""
    c = (fr * 2) % 1.0
    ciclo = int(fr * 2) % 2
    if c < 0.85:
        return c / 0.85, 0.0, ciclo
    x = (c - 0.85) / 0.15
    return 1.0 - x, math.sin(PI * x) ** 0.6, ciclo


# ------------------------------------------------------------------ animação (laço de 4 s)
DUR = QUADROS / FPS
SAIDA_CH = S + Vector((0, 0, Z_CHAMINE + 0.06))
from mathutils import Euler


def suave(x):
    return x * x * (3 - 2 * x)


for q in range(1, QUADROS + 1):
    t = (q - 1) / FPS
    fr = (q - 1) / QUADROS
    # pressão: casco incha e treme; vaza fumaça; no alívio, jato de fogo na válvula do ciclo e na chaminé
    pr, jato, ciclo = pressao(fr)
    trem = 0.0035 * pr * pr
    pivo.scale = (1 + 0.012 * pr * pr + trem * math.sin(2 * PI * 37 * fr), 1 + 0.012 * pr * pr + trem * math.sin(2 * PI * 41 * fr + 1), 1 + 0.004 * pr)
    pivo.location = S + Vector((trem * math.sin(2 * PI * 53 * fr), trem * math.sin(2 * PI * 47 * fr + 2), Z_TIJ))
    pivo.keyframe_insert('scale', frame=q)
    pivo.keyframe_insert('location', frame=q)
    for k, o in enumerate(vazamentos):
        pt, d = VAZ[k % len(VAZ)]
        u = ((k // len(VAZ)) / 2 + fr * 4 + k * 0.13) % 1.0
        forca = 0.4 + 0.6 * pr
        o.location = pt + d * (0.12 * u) + Vector((0.05 * u, 0, 0.45 * u))
        o.scale = [max(0.001, (0.03 + 0.14 * u) * forca)] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    for k, o in enumerate(jatos):
        ativo = jato if (k == 2 or k == ciclo) else 0.0
        if k < 2:
            pos, d, _ = VALVULAS[k]
            comp, larg = 0.55 * ativo, 0.07 * ativo
        else:
            pos, d = S + Vector((0, 0, Z_CHAMINE + 0.06)), Vector((0, 0, 1))
            comp, larg = 0.8 * ativo, 0.12 * ativo
        o.location = pos
        o.rotation_quaternion = d.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), fr * 40)
        o.scale = (max(larg, 0.02), max(larg, 0.02), max(comp, 0.05))
        o.hide_render = ativo < 0.05                                      # volume não aceita escala ~0: some
        o.hide_viewport = o.hide_render
        for c in ('location', 'rotation_quaternion', 'scale', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
        luzes_jato[k].energy = 220 * ativo * (1 + 0.3 * math.sin(fr * 90))
        luzes_jato[k].keyframe_insert('energy', frame=q)
    # caçamba: sobe (0–0,42), vira (0,42–0,52), volta (0,52–0,6), desce (0,6–1)
    if fr < 0.42:
        s, tomb = suave(fr / 0.42), 0.0
    elif fr < 0.52:
        s, tomb = 1.0, suave((fr - 0.42) / 0.1)
    elif fr < 0.6:
        s, tomb = 1.0, 1.0 - suave((fr - 0.52) / 0.08)
    else:
        s, tomb = 1.0 - suave((fr - 0.6) / 0.4), 0.0
    p = R0 + (R1 - R0) * (0.05 + 0.88 * s) + NRM * 0.03
    rot = ROT_T.to_quaternion() @ Quaternion((1, 0, 0), -1.9 * tomb)
    carro.location = p
    carro.rotation_quaternion = rot
    carro.keyframe_insert('location', frame=q)
    carro.keyframe_insert('rotation_quaternion', frame=q)
    carga.scale = [1.0 if fr < 0.47 else 0.001] * 3
    carga.keyframe_insert('scale', frame=q)
    olhal = p + rot @ Vector((0, 0.11, 0.17))
    dc = GUI - olhal
    cabo.location = olhal
    cabo.rotation_quaternion = dc.normalized().to_track_quat('Z', 'Y')
    cabo.scale = (1, 1, dc.length)
    cabo.keyframe_insert('location', frame=q)
    cabo.keyframe_insert('rotation_quaternion', frame=q)
    cabo.keyframe_insert('scale', frame=q)
    # rotor do soprador: 12 voltas no laço
    rotor.rotation_euler = (2 * PI * 12 * fr, 0, 0)
    rotor.keyframe_insert('rotation_euler', frame=q)
    # brasa da porta pulsando
    pulso = 0.75 + 0.25 * math.sin(2 * PI * 3 * fr) * math.sin(2 * PI * 5 * fr + 1)
    luz_porta.energy = 40 * pulso
    luz_porta.keyframe_insert('energy', frame=q)
    no_e = base3d.M['frestas'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    no_e.default_value = 18 * pulso
    no_e.keyframe_insert('default_value', frame=q)
    # lingoteiras: 3 moldes por laço; barra aparece depois da bica e some quando o molde vira
    for k, mo in enumerate(moldes):
        u = (k * PASSO_L + 3 * PASSO_L * fr) % TOTAL_L
        pos, ang = no_laco_l(u)
        mo.location = pos
        mo.rotation_quaternion = Quaternion((1, 0, 0), ang)
        mo.keyframe_insert('location', frame=q)
        mo.keyframe_insert('rotation_quaternion', frame=q)
        cheio = u < LR and pos.y > Y_VAZA - 0.02
        lingotes[k].scale = [1.0 if cheio else 0.001] * 3
        lingotes[k].keyframe_insert('scale', frame=q)
    # fumaça da chaminé
    for k, o in enumerate(fumacas):
        u = (k / len(fumacas) + fr * 2) % 1.0
        o.location = SAIDA_CH + Vector((0.7 * u * u, 0.25 * u, 1.9 * u + 0.08))
        o.scale = [0.09 + 0.5 * u] * 3
        o.rotation_euler = (k, u * 2, k * 0.5)
        for c in ('location', 'scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
    # vapor do spray
    for k, o in enumerate(vapores):
        u = (k / len(vapores) + fr * 2) % 1.0
        o.location = Vector((XL + 0.08 * math.sin(k * 2.0), Y_AGUA + 0.04 * k - 0.06, ZL + 0.05 + 0.7 * u))
        o.scale = [0.06 + 0.2 * u] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # faíscas saltando do jato
    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + fr * 4) % 1.0) * 0.35
        v = vel_f[k]
        o.location = Vector((XL, Y_VAZA, ZL + 0.02)) + v * tt + Vector((0, 0, -4.9 * tt * tt))
        o.scale = [max(0.001, 1 - tt / 0.35)] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects) + [luz_porta] + luzes_jato:
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (12, 12, 1.0))
obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.55
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
sc.view_settings.exposure = -0.5
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
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(int(QUADROS * 0.46) + 1)                                 # no meio do jato do 1º ciclo
    for i, (ang, alt) in enumerate(((300, 2.0), (210, 2.2), (120, 2.4), (30, 1.8))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 5.4, math.sin(a) * 5.4, alt)), ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'fornalha_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
    mirar((-1.9, -0.6, 1.2), (-0.35, 0.5, 0.35), 35)                     # de perto: bica, lingoteiras, vapor
    sc.render.filepath = os.path.join(AQUI, 'fornalha_perto.png')
    bpy.ops.render.render(write_still=True)
if modo == 'video':
    sc.render.engine = 'BLENDER_EEVEE'
    for at, v in (('use_shadows', True), ('volumetric_tile_size', '4'), ('taa_render_samples', 32)):
        if hasattr(sc.eevee, at):
            setattr(sc.eevee, at, v)
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(300)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 6.0, math.sin(a) * 6.0, 2.1)), (0, 0, 1.4), 32)
    if hasattr(sc.render.image_settings, 'media_type'):
        sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(AQUI, 'fornalha_video.mp4')
    sc.frame_end = QUADROS
    bpy.ops.render.render(animation=True)
print('FORNALHA ok')
