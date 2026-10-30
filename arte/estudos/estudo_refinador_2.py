"""Estudo isolado (fora do jogo): refinador 2, 3×3 tiles.
Evolução industrial de Tier 2 do refinador químico:
- Bocas de fluido:
  - Entrada Oeste O1: x = -1.44 m, y = 0.0 m, z = 0.35 m (bomba centrífuga de alta pressão).
  - Saída Leste L1: x = +1.44 m, y = 0.0 m, z = 0.35 m (fluido refinado com trocador duplo).
  - Saída Norte N0 (item sólido): x = -1.0 m, y = +1.44 m, z = 0.23 m (esteira/bica de células).
  - Boca Sul S1 (retorno de tratamento/água limpa): x = 0.0 m, y = -1.44 m, z = 0.35 m com flange e válvula.
- 3 Slots de Módulo (encaixes de melhoria): baia lateral sul com 3 cartuchos removíveis, dissipadores e barramento LED.
- Duas colunas de fracionamento interligadas (torre primária de pratos + coluna secundária de despoluição/stripping).
- Dois reatores de alta pressão com camisas espirais, agitadores elétricos potentes e válvulas de alívio PSV.
- Trocador de calor casco-e-tubo duplo de alta eficiência térmica.
- Flare de queima limpa com quebra-vento, estais de sustentação e chama piloto tremeluzente.
- Fenômeno da IA: anel de indução molecular quântico giratório no topo da torre primária com ressonância atômica.
- Robô de manutenção na cremalheira vertical da torre.

Uso: blender -b --python estudo_refinador_2.py -- foto | video | perto | nada
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
random.seed(57)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
Z0 = 0.08                    # topo da laje de concreto
Z_P = 0.35                   # altura padrão de bocas de cano no jogo


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


def base_perp(u):
    u = Vector(u).normalized()
    e1 = u.orthogonal().normalized()
    return e1, u.cross(e1).normalized()


def flange(bf, bp, c, u, r, parafusos=True):
    c, u = Vector(c), Vector(u).normalized()
    for s in (-1, 1):
        tubo(bf, c + u * s * 0.003, c + u * s * 0.016, r * 1.6 + 0.005, 14)
    if not parafusos:
        return
    e1, e2 = base_perp(u)
    n = 4 if r < 0.035 else (6 if r < 0.05 else 8)
    for k in range(n):
        a = k * 2 * PI / n + 0.2
        p = c + (e1 * math.cos(a) + e2 * math.sin(a)) * (r * 1.35 + 0.004)
        tubo(bp, p - u * 0.02, p + u * 0.02, 0.0045, 6)


def cano(bm, bf, bp, pts, r, folga=0.08, flanges=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 14)
        u = (b - a).normalized()
        if flanges and (b - a).length > 2.5 * folga:
            flange(bf, bp, a + u * folga, u, r)
            flange(bf, bp, b - u * folga, u, r)
    for c in pts[1:-1]:
        curva(bm, c, r, 14)


def bocal(bm, bf, bp, c, u, r, comp):
    c, u = Vector(c), Vector(u).normalized()
    tubo(bm, c - u * 0.02, c + u * comp, r, 14)
    flange(bf, bp, c + u * (comp - 0.01), u, r)
    return c + u * comp


GAUGES = []


def manometro(bc, bm_face, pos, normal, r=0.034, haste=None):
    pos, n = Vector(pos), Vector(normal).normalized()
    if haste is not None:
        tubo(bc, Vector(haste), pos - n * 0.0, 0.007, 8)
    tubo(bc, pos - n * 0.012, pos + n * 0.012, r, 20)
    tubo(bc, pos + n * 0.012, pos + n * 0.016, r * 1.06, 20)
    tubo(bm_face, pos + n * 0.011, pos + n * 0.0135, r * 0.9, 20)
    e = bpy.data.objects.new('ponteiro_piv', None)
    sc.collection.objects.link(e)
    e.location = pos + n * 0.0145
    e.rotation_mode = 'QUATERNION'
    e.rotation_quaternion = n.to_track_quat('Z', 'Y')
    bm = bmesh.new()
    caixa(bm, (0, r * 0.35, 0), (0.004, r * 0.75, 0.002))
    obj('ponteiro', bm, 'preto', e)
    GAUGES.append((e, n, random.uniform(0, 2 * PI), random.uniform(0.25, 0.7)))


def valvula(bc, ba, bf, bp, c, u, r, cima=Vector((0, 0, 1))):
    c, u, cima = Vector(c), Vector(u).normalized(), Vector(cima).normalized()
    curva(bc, c, r * 1.7, 18)
    flange(bf, bp, c - u * r * 2.2, u, r)
    flange(bf, bp, c + u * r * 2.2, u, r)
    tubo(bc, c, c + cima * (r * 1.7 + 0.08), r * 0.7, 12)
    tubo(bc, c + cima * (r * 1.7 + 0.03), c + cima * (r * 1.7 + 0.045), r * 1.2, 12)
    p = c + cima * (r * 1.7 + 0.1)
    tubo(ba, p - cima * 0.02, p + cima * 0.02, 0.07, 20)
    cil(ba, p + cima * 0.035, 0.07, 0.03, cima, lados=20, r2=0.035)
    e1, _ = base_perp(cima)
    caixa(bc, p - cima * 0.06 + e1 * 0.05, (0.04, 0.03, 0.05))


# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat():
    m = bpy.data.materials.new('Vidro')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.78, 0.84, 0.80, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Alpha'].default_value = 0.4
    return m


def malha_mat():
    m = bpy.data.materials.new('Tela')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.55, 0.36, 0.04, 1)
    b.inputs['Roughness'].default_value = 0.5
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hz = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(sep.outputs['X'], hz.inputs[0])
    nt.links.new(sep.outputs['Y'], hz.inputs[1])
    fios = []
    for entrada in (hz.outputs['Value'], sep.outputs['Z']):
        d = no(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = 0.02
        nt.links.new(entrada, d.inputs[0])
        fr = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs['Value'], fr.inputs[0])
        lt = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
        lt.inputs[1].default_value = 0.18
        nt.links.new(fr.outputs['Value'], lt.inputs[0])
        fios.append(lt)
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fios[0].outputs['Value'], mx.inputs[0])
    nt.links.new(fios[1].outputs['Value'], mx.inputs[1])
    nt.links.new(mx.outputs['Value'], b.inputs['Alpha'])
    return m


def fogo_mat():
    m = base3d.volume_mat('Fogo', (1.0, 0.4, 0.05), 4.0, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 42.0
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)
    vol.inputs['Emission Color'].default_value = (1.0, 0.35, 0.04, 1)
    vol.inputs['Density'].default_value = 6.0
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


def seiva_mat():
    m = mats.material('Seiva', (0.16, 0.15, 0.015), 0, 0.06, pintura=False, sujeira=0.15, desgaste=0.0)
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Emission Color'].default_value = (0.6, 0.6, 0.05, 1)
    b.inputs['Emission Strength'].default_value = 0.06
    b.inputs['Coat Weight'].default_value = 1.0
    return m


base3d.M.update({
    'azul_petroleo': mats.material('Azul Industrial', (0.08, 0.22, 0.32), 0, 0.42, desgaste=1.1, sujeira=1.0, ferrugem=0.55),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'laranja': mats.material('Laranja', (0.62, 0.22, 0.04), 0, 0.45, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'primer_oxido': mats.material('Primer Óxido', (0.36, 0.10, 0.06), 0, 0.65, desgaste=0.8, sujeira=0.9, ferrugem=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'cinza': mats.material('Cinza', (0.28, 0.29, 0.30), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'verde_tubo': mats.material('Cano água limpa', (0.06, 0.26, 0.14), 0, 0.45, desgaste=0.9, sujeira=0.8, ferrugem=0.4),
    'oxido': mats.material('Cano de respiro', (0.38, 0.10, 0.06), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.7),
    'processo': mats.material('Cano de processo', (0.18, 0.17, 0.16), 0.6, 0.5, pintura=False, ferrugem=0.8, sujeira=1.0),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.8, sujeira=0.8, escovado=True),
    'inox': mats.material('Inox', (0.64, 0.65, 0.65), 1.0, 0.26, pintura=False, ferrugem=0.2, sujeira=0.7, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'ouro': mats.material('Ouro Conector', (0.85, 0.68, 0.18), 1.0, 0.22, pintura=False, sujeira=0.2),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.015, 0.014, 0.013), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.78, 0.72), 0, 0.3, pintura=False, sujeira=0.5, desgaste=0.0),
    'preto': mats.material('Preto', (0.01, 0.01, 0.01), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'bateria': mats.material('Casca da célula', (0.05, 0.05, 0.06), 0.6, 0.3, pintura=False, sujeira=0.2, desgaste=0.0),
    'seiva': seiva_mat(),
    'vidro': vidro_mat(),
    'malha': malha_mat(),
    'listras': base3d.listras_mat(),
    'liquido': luz_mat('Líquido no visor', (1.0, 0.55, 0.08), 3.0),
    'violeta': luz_mat('Campo violeta', (0.6, 0.15, 1.0), 10.0),
    'ciano': luz_mat('Luz ciano', (0.1, 0.9, 1.0), 8.0),
    'ambar': luz_mat('Luz âmbar', (1.0, 0.5, 0.05), 8.0),
    'verde_luz': luz_mat('Luz verde', (0.15, 1.0, 0.25), 6.0),
    'vermelho_luz': luz_mat('Luz vermelha', (1.0, 0.06, 0.04), 8.0),
    'fogo': fogo_mat(),
    'fumaca': fumaca_grad_mat('Fumaça do flare', 8.0, 3.6, 5.0),
    'vapor_alto': base3d.volume_mat('Vapor alto', (0.92, 0.92, 0.94), 9.0, 2.5, 3.6),
    'vapor_troc': base3d.volume_mat('Vapor trocador', (0.92, 0.92, 0.94), 9.0, 1.0, 2.0),
})

# ------------------------------------------------------------------ LAJE E FUNDAÇÃO COM CONTENÇÃO
bm_laje = bmesh.new()
caixa_de(bm_laje, (-1.48, -1.48, 0), (1.48, 1.48, Z0))
# bacia de contenção perimetral (mureta de 0.05 m em volta de todo o piso)
for x in (-1.48, 1.46):
    caixa_de(bm_laje, (x, -1.48, Z0), (x + 0.02, 1.48, Z0 + 0.05))
for y in (-1.48, 1.46):
    caixa_de(bm_laje, (-1.48, y, Z0), (1.48, y + 0.02, Z0 + 0.05))
obj('laje', bm_laje, 'concreto')

# listras de segurança na mureta de contenção
bm_list = bmesh.new()
for s in (-1, 1):
    caixa_de(bm_list, (-1.485, s * 1.47 - 0.008, Z0 + 0.045), (1.485, s * 1.47 + 0.008, Z0 + 0.052))
    caixa_de(bm_list, (s * 1.47 - 0.008, -1.485, Z0 + 0.045), (s * 1.47 + 0.008, 1.485, Z0 + 0.052))
obj('laje_listras', bm_list, 'listras')

# ------------------------------------------------------------------ BOCA OESTE O1 (ENTRADA DE CARGA / SEIVA): x = -1.44 m, z = 0.35 m
PB = Vector((-1.05, 0.0, Z_P))
bm_bb = bmesh.new()
caixa_de(bm_bb, (-1.18, -0.18, Z0), (-0.48, 0.18, Z0 + 0.06))
for x in (-1.12, -0.58):
    for s in (-1, 1):
        cil(bm_bb, Vector((x, s * 0.15, Z0 + 0.065)), 0.012, 0.014, lados=6)
obj('bomba_base', bm_bb, 'grafite')

bm_bv = bmesh.new()
cil(bm_bv, PB, 0.14, 0.12, Vector((1, 0, 0)), lados=28)
cil(bm_bv, PB + Vector((0, 0.04, 0.10)), 0.08, 0.12, Vector((1, 0, 0)), lados=20)
caixa_de(bm_bv, (-1.12, -0.09, Z0 + 0.06), (-0.98, 0.09, PB.z - 0.11))
tubo(bm_bv, PB + Vector((0.06, 0, 0)), PB + Vector((0.16, 0, 0)), 0.065, 16)
suavizar(obj('bomba_voluta', bm_bv, 'azul_petroleo'))

bm_can_c, bf_c, bp_c = bmesh.new(), bmesh.new(), bmesh.new()
boca_o = Vector((-1.44, 0, Z_P))
cano(bm_can_c, bf_c, bp_c, [boca_o, PB + Vector((-0.06, 0, 0))], 0.05, folga=0.05)
flange(bf_c, bp_c, boca_o + Vector((0.025, 0, 0)), (1, 0, 0), 0.05)
rec0 = PB + Vector((0, 0.0, 0.14))
Z_CARGA = 2.05
cano(bm_can_c, bf_c, bp_c, [rec0, Vector((PB.x, 0, Z_CARGA))], 0.042)
cano(bm_can_c, bf_c, bp_c, [Vector((PB.x, -0.72, Z_CARGA)), Vector((PB.x, 0.72, Z_CARGA))], 0.042, flanges=False)
curva(bm_can_c, Vector((PB.x, 0, Z_CARGA)), 0.05)
suavizar(obj('canos_carga', bm_can_c, 'processo'))
obj('canos_carga_flanges', bf_c, 'ferro')
obj('canos_carga_parafusos', bp_c, 'aco')

# motor elétrico da bomba de carga com aletas
bm_bm = bmesh.new()
cil(bm_bm, Vector((-0.68, 0, PB.z)), 0.115, 0.26, Vector((1, 0, 0)), lados=24)
for k in range(10):
    cil(bm_bm, Vector((-0.79 + k * 0.026, 0, PB.z)), 0.128, 0.007, Vector((1, 0, 0)), lados=24)
cil(bm_bm, Vector((-0.53, 0, PB.z)), 0.105, 0.04, Vector((1, 0, 0)), lados=24, r2=0.08)
caixa_de(bm_bm, (-0.80, -0.11, Z0 + 0.06), (-0.56, 0.11, PB.z - 0.09))
caixa_de(bm_bm, (-0.74, -0.05, PB.z + 0.11), (-0.62, 0.05, PB.z + 0.17))
suavizar(obj('bomba_motor', bm_bm, 'grafite'))

# ------------------------------------------------------------------ DOIS REATORES QUÍMICOS DE ALTA PRESSÃO (OESTE: y = -0.72 e +0.72)
RX = -0.48
REATORES = (-0.72, 0.72)
R_R, Z_FUNDO, Z_TOPO = 0.31, 0.62, 1.72
Z_C0, Z_C1, R_C = 0.76, 1.54, 0.345

agitadores = []
bm_rcas, bm_rcam, bm_rfer, bm_rac = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
bm_rbf, bm_rbp, bm_rproc, bm_rvap, bm_rresp = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()


def zh(off):
    return Z_TOPO + 0.12 * math.sqrt(max(0.0, 1 - (off / R_R) ** 2))


for RY in REATORES:
    s = 1 if RY > 0 else -1
    C = Vector((RX, RY, 0))
    # casco inox
    cil(bm_rcas, C + Vector((0, 0, (Z_FUNDO + Z_TOPO) / 2)), R_R, Z_TOPO - Z_FUNDO, lados=40)
    for zc in (Z_FUNDO, Z_TOPO):
        bmesh.ops.create_uvsphere(bm_rcas, u_segments=40, v_segments=16, radius=1.0,
                                  matrix=Matrix.Translation(C + Vector((0, 0, zc))) @ Matrix.Diagonal((R_R, R_R, 0.12, 1)))
    # camisa com nervuras espirais de resfriamento
    cil(bm_rcam, C + Vector((0, 0, (Z_C0 + Z_C1) / 2)), R_C, Z_C1 - Z_C0, lados=40)
    cil(bm_rcam, C + Vector((0, 0, Z_C0 - 0.03)), R_R + 0.005, 0.06, lados=40, r2=R_C)
    cil(bm_rcam, C + Vector((0, 0, Z_C1 + 0.03)), R_C, 0.06, lados=40, r2=R_R + 0.005)
    for z in (0.95, 1.15, 1.35):
        cil(bm_rfer, C + Vector((0, 0, z)), R_C + 0.010, 0.032, lados=40)
    # flanges do tampo
    cil(bm_rfer, C + Vector((0, 0, Z_TOPO - 0.03)), R_R + 0.038, 0.05, lados=40)
    for k in range(24):
        a = k * 2 * PI / 24
        p = C + Vector((math.cos(a) * (R_R + 0.024), math.sin(a) * (R_R + 0.024), Z_TOPO - 0.03))
        cil(bm_rac, p, 0.006, 0.09, lados=6)
    # pernas pesadas
    for k in range(4):
        a = k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa_de(bm_rfer, C + d * 0.34 + Vector((-0.03, -0.03, Z0)), C + d * 0.34 + Vector((0.03, 0.03, 0.72)))
        caixa(bm_rfer, C + d * 0.34 + Vector((0, 0, Z0 + 0.008)), (0.10, 0.10, 0.016))
    # agitador superior com ventoinha aletada animada
    caixa(bm_rfer, C + Vector((0, 0, 1.92)), (0.18, 0.18, 0.14))
    tubo(bm_rfer, C + Vector((0, 0, Z_TOPO + 0.1)), C + Vector((0, 0, 1.85)), 0.055, 16)
    ag = bpy.data.objects.new('agitador_%d' % (1 if s > 0 else 2), None)
    sc.collection.objects.link(ag)
    ag.location = C + Vector((0, 0, 2.25))
    agitadores.append(ag)
    bm_ag = bmesh.new()
    cil(bm_ag, C + Vector((0, 0, 2.10)), 0.08, 0.24, lados=24)
    for k in range(8):
        cil(bm_ag, C + Vector((0, 0, 2.01 + k * 0.025)), 0.092, 0.006, lados=24)
    suavizar(obj('agitador_motor_%d' % (1 if s > 0 else 2), bm_ag, 'grafite'))
    # ventoinha no topo do agitador
    bm_av = bmesh.new()
    for k in range(6):
        a = k * PI / 3
        caixa(bm_av, Vector((math.cos(a) * 0.036, math.sin(a) * 0.036, 0)), (0.065, 0.012, 0.01), Matrix.Rotation(a, 3, 'Z'))
    cil(bm_av, Vector((0, 0, 0)), 0.02, 0.022, lados=12)
    obj('agitador_ventoinha_%d' % (1 if s > 0 else 2), bm_av, 'aco', ag)
    # alimentação pelo coletor
    pf = C + Vector((-0.18, 0, 0))
    bocal(bm_rproc, bm_rbf, bm_rbp, Vector((pf.x, RY, zh(0.18) - 0.01)), (0, 0, 1), 0.036, 0.09)
    cano(bm_rproc, bm_rbf, bm_rbp, [Vector((PB.x, RY, Z_CARGA)), Vector((pf.x, RY, Z_CARGA)),
                                   Vector((pf.x, RY, zh(0.18) + 0.08))], 0.036, flanges=False)
    valvula(bm_rfer, bm_rfer, bm_rbf, bm_rbp, Vector((-0.84, RY, Z_CARGA)), (1, 0, 0), 0.036)
    # saída de vapores de topo em direção às torres
    pv = Vector((RX + 0.16, RY, zh(0.16) - 0.01))
    bocal(bm_rproc, bm_rbf, bm_rbp, pv, (0, 0, 1), 0.046, 0.07)
    # válvula PSV de segurança
    pp = Vector((RX, RY - s * 0.18, zh(0.18) - 0.01))
    topo_psv = bocal(bm_rfer, bm_rbf, bm_rbp, pp, (0, 0, 1), 0.032, 0.12)
    cil(bm_rfer, topo_psv + Vector((0, 0, 0.04)), 0.048, 0.07, lados=16)
    cano(bm_rresp, bm_rbf, bm_rbp, [topo_psv + Vector((0, -s * 0.06, 0.04)),
                                    Vector((RX, RY - s * 0.30, topo_psv.z + 0.04)),
                                    Vector((RX, 0, 2.38))], 0.032, flanges=False)

suavizar(obj('reatores_casco', bm_rcas, 'inox'))
suavizar(obj('reatores_camisa', bm_rcam, 'azul_petroleo'))
obj('reatores_ferro', bm_rfer, 'ferro')
obj('reatores_parafusos', bm_rac, 'aco')
obj('reatores_processo', bm_rproc, 'processo')
obj('reatores_respiro', bm_rresp, 'oxido')

# ------------------------------------------------------------------ TORRE DE FRACIONAMENTO DUPLA (CENTRO-LESTE)
# Torre Primária (T1): x = 0.52, y = 0.42, altura z = 3.25 m com pratos e visores
# Coluna Secundária de Despoluição (T2): x = 0.52, y = -0.32, altura z = 2.45 m
T1 = Vector((0.52, 0.42, 0))
T2 = Vector((0.52, -0.32, 0))
R_T1, R_T2 = 0.28, 0.22
Z_TT1, Z_TT2 = 3.25, 2.45

bm_t1 = bmesh.new()
cil(bm_t1, T1 + Vector((0, 0, (0.45 + Z_TT1) / 2)), R_T1, Z_TT1 - 0.45, lados=40)
bmesh.ops.create_uvsphere(bm_t1, u_segments=40, v_segments=16, radius=1.0,
                          matrix=Matrix.Translation(T1 + Vector((0, 0, Z_TT1))) @ Matrix.Diagonal((R_T1, R_T1, 0.12, 1)))
suavizar(obj('torre_primaria', bm_t1, 'cinza'))

bm_t2 = bmesh.new()
cil(bm_t2, T2 + Vector((0, 0, (0.45 + Z_TT2) / 2)), R_T2, Z_TT2 - 0.45, lados=36)
bmesh.ops.create_uvsphere(bm_t2, u_segments=36, v_segments=16, radius=1.0,
                          matrix=Matrix.Translation(T2 + Vector((0, 0, Z_TT2))) @ Matrix.Diagonal((R_T2, R_T2, 0.10, 1)))
suavizar(obj('torre_secundaria', bm_t2, 'inox'))

# saias e anéis de base das duas torres
bm_tsaias = bmesh.new()
for T, R_T in ((T1, R_T1), (T2, R_T2)):
    bmesh.ops.create_cone(bm_tsaias, cap_ends=False, segments=36, radius1=R_T + 0.02, radius2=R_T, depth=0.45 - Z0,
                          matrix=Matrix.Translation(T + Vector((0, 0, (0.45 + Z0) / 2))))
    cil(bm_tsaias, T + Vector((0, 0, Z0 + 0.015)), R_T + 0.06, 0.03, lados=36)
obj('torres_saias', bm_tsaias, 'listras')

# juntas flangeadas nas seções
bm_tj = bmesh.new()
for z in (1.0, 1.6, 2.2, 2.8):
    for dz in (-0.014, 0.014):
        cil(bm_tj, T1 + Vector((0, 0, z + dz)), R_T1 + 0.035, 0.024, lados=40)
for z in (1.1, 1.8):
    for dz in (-0.014, 0.014):
        cil(bm_tj, T2 + Vector((0, 0, z + dz)), R_T2 + 0.032, 0.024, lados=36)
obj('torres_juntas', bm_tj, 'ferro')

# visores de prato na torre primária (face oeste-sudoeste com líquido iluminado)
A_VIS = math.radians(205)
dV = Vector((math.cos(A_VIS), math.sin(A_VIS), 0))
bm_vp, bm_vvidro, bm_vliq = bmesh.new(), bmesh.new(), bmesh.new()
PRATOS = (0.75, 1.20, 1.40, 1.85, 2.05, 2.45, 2.65, 3.00)
for z in PRATOS:
    c = T1 + dV * R_T1 + Vector((0, 0, z))
    tubo(bm_vp, c - dV * 0.02, c + dV * 0.035, 0.05, 20)
    tubo(bm_vvidro, c + dV * 0.035, c + dV * 0.04, 0.036, 20)
    tubo(bm_vliq, c + dV * 0.02, c + dV * 0.03, 0.037, 20)
suavizar(obj('visores_corpo', bm_vp, 'ferro'))
obj('visores_vidro', bm_vvidro, 'vidro')
obj('visores_liquido', bm_vliq, 'liquido')

# visor tubular de nível externo (face leste)
dN = Vector((1, 0, 0))
bm_nv, bm_nvidro = bmesh.new(), bmesh.new()
for z in (0.65, 1.35):
    bocal(bm_nv, bm_nv, bm_nv, T1 + dN * (R_T1 - 0.01) + Vector((0, 0, z)), dN, 0.02, 0.1)
tubo(bm_nv, T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 0.65)), T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 0.69)), 0.03, 16)
tubo(bm_nv, T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 1.31)), T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 1.35)), 0.03, 16)
tubo(bm_nvidro, T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 0.69)), T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 1.31)), 0.022, 16)
obj('visor_nivel_corpo', bm_nv, 'ferro')
obj('visor_nivel_vidro', bm_nvidro, 'vidro')

# bóia/coluna de líquido móvel animada no visor
o_nivel = bpy.data.objects.new('nivel_fluido', None)
sc.collection.objects.link(o_nivel)
o_nivel.location = T1 + dN * (R_T1 + 0.11) + Vector((0, 0, 0.69))
bm_nl = bmesh.new()
cil(bm_nl, Vector((0, 0, 0.25)), 0.016, 0.5, lados=14)
obj('nivel_fluido_coluna', bm_nl, 'liquido', o_nivel)

# dutos de interligação aérea entre a torre primária e secundária
bm_inter = bmesh.new()
cano(bm_inter, bm_inter, bm_inter, [T1 + Vector((0, -R_T1, 2.50)), Vector((T1.x, 0.05, 2.50)),
                                    Vector((T2.x, 0.05, 2.10)), T2 + Vector((0, R_T2, 2.10))], 0.04)
cano(bm_inter, bm_inter, bm_inter, [T2 + Vector((0, R_T2, 0.85)), Vector((T2.x, 0.05, 0.85)),
                                    Vector((T1.x, 0.05, 0.85)), T1 + Vector((0, -R_T1, 0.85))], 0.035)
suavizar(obj('torres_interligacao', bm_inter, 'processo'))

# trilho de manutenção com robô de inspeção
Y_TR = T1.y + R_T1 + 0.075
bm_trilho = bmesh.new()
for dx in (-0.06, 0.06):
    caixa_de(bm_trilho, (T1.x + dx - 0.012, Y_TR - 0.012, 0.5), (T1.x + dx + 0.012, Y_TR + 0.012, 2.85))
caixa_de(bm_trilho, (T1.x - 0.012, Y_TR - 0.008, 0.5), (T1.x + 0.012, Y_TR + 0.004, 2.85))
obj('torre_trilho', bm_trilho, 'amarelo')

# robô que sobe e desce na torre
o_robo = bpy.data.objects.new('robo_inspecao', None)
sc.collection.objects.link(o_robo)
o_robo.location = Vector((T1.x, Y_TR, 1.2))
bm_rb = bmesh.new()
caixa(bm_rb, (0, 0.06, 0), (0.18, 0.07, 0.16))
caixa(bm_rb, (0, 0.11, 0.03), (0.09, 0.04, 0.07))
obj('robo_chassi', bm_rb, 'azul_petroleo', o_robo)
bm_ro = bmesh.new()
cil(bm_ro, Vector((0.0, 0.132, 0.04)), 0.014, 0.008, Vector((0, 1, 0)), lados=12)
obj('robo_sensor', bm_ro, 'ciano', o_robo)

# ------------------------------------------------------------------ FENÔMENO DA IA: ANEL DE INDUÇÃO MOLECULAR QUÂNTICO (T1)
Z_AN, R_AN = 3.05, 0.52
bm_colar = bmesh.new()
cil(bm_colar, T1 + Vector((0, 0, Z_AN)), R_T1 + 0.03, 0.18, lados=40)
for dz in (-0.10, 0.10):
    cil(bm_colar, T1 + Vector((0, 0, Z_AN + dz)), R_T1 + 0.05, 0.02, lados=40)
obj('anel_colar_base', bm_colar, 'grafite')

# anel giratório levitante de campo quântico
o_anel = bpy.data.objects.new('anel_quantico', None)
sc.collection.objects.link(o_anel)
o_anel.location = T1 + Vector((0, 0, Z_AN))

bm_anel = bmesh.new()
toro(bm_anel, Vector((0, 0, 0)), R_AN, 0.032, 64, 14)
suavizar(obj('anel_aro', bm_anel, 'azul_petroleo', o_anel))

bm_acampo = bmesh.new()
toro(bm_acampo, Vector((0, 0, 0)), R_AN - 0.026, 0.010, 64, 8)
obj('anel_luz_campo', bm_acampo, 'violeta', o_anel)

# emissores radiais de indução no anel
bm_aem = bmesh.new()
for k in range(8):
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm_aem, d * R_AN, (0.05, 0.05, 0.08), Matrix.Rotation(a, 3, 'Z'))
    cil(bm_aem, d * (R_AN + 0.03), 0.015, 0.03, d, lados=10)
obj('anel_emissores', bm_aem, 'cromo', o_anel)

# ------------------------------------------------------------------ TROCADOR DE CALOR CASCO-E-TUBO DUPLO (LESTE / SUDESTE)
# Dois trocadores montados em bateria horizontal na cota Z = 0.45 e Z = 0.85
X_TC0, X_TC1, Y_TC = 0.15, 1.05, -0.95
bm_tc = bmesh.new()
for ztc in (0.42, 0.82):
    # casco
    cil(bm_tc, Vector(((X_TC0 + X_TC1) / 2, Y_TC, ztc)), 0.15, (X_TC1 - X_TC0) - 0.22, Vector((1, 0, 0)), lados=32)
    # cabeçotes
    for x0, x1 in ((X_TC0, X_TC0 + 0.11), (X_TC1 - 0.11, X_TC1)):
        cil(bm_tc, Vector(((x0 + x1) / 2, Y_TC, ztc)), 0.16, x1 - x0, Vector((1, 0, 0)), lados=32)
    # flanges de espelho
    for x in (X_TC0 + 0.11, X_TC1 - 0.11):
        cil(bm_tc, Vector((x, Y_TC, ztc)), 0.18, 0.024, Vector((1, 0, 0)), lados=32)
# berços e pés de apoio
for x in (0.35, 0.85):
    caixa_de(bm_tc, (x - 0.04, Y_TC - 0.16, Z0), (x + 0.04, Y_TC + 0.16, 0.95))
suavizar(obj('trocador_duplo', bm_tc, 'cinza'))

# tubulação de saída para a boca leste L1: x = +1.44 m, y = 0.0 m, z = 0.35 m
bm_tcl, bf_tcl, bp_tcl = bmesh.new(), bmesh.new(), bmesh.new()
boca_l = Vector((1.44, 0, Z_P))
cano(bm_tcl, bf_tcl, bp_tcl, [Vector((X_TC1 + 0.05, Y_TC, 0.42)), Vector((1.25, Y_TC, 0.42)),
                              Vector((1.25, 0, 0.42)), Vector((1.25, 0, Z_P)), boca_l], 0.042, folga=0.06)
flange(bf_tcl, bp_tcl, boca_l - Vector((0.025, 0, 0)), (1, 0, 0), 0.042)
valvula(bm_tcl, bm_tcl, bf_tcl, bp_tcl, Vector((1.25, -0.45, 0.42)), (0, 1, 0), 0.042)
suavizar(obj('canos_saida_leste', bm_tcl, 'processo'))
obj('canos_saida_flanges', bf_tcl, 'ferro')
obj('canos_saida_parafusos', bp_tcl, 'aco')

# ------------------------------------------------------------------ BOCA SUL S1 (RETORNO DE TRATAMENTO / ÁGUA LIMPA): y = -1.44 m, z = 0.35 m
bm_bs, bf_bs, bp_bs = bmesh.new(), bmesh.new(), bmesh.new()
boca_s = Vector((0.0, -1.44, Z_P))
tubo(bm_bs, boca_s, Vector((0.0, -1.15, Z_P)), 0.04, 18)
flange(bf_bs, bp_bs, boca_s + Vector((0, 0.025, 0)), (0, 1, 0), 0.04)
valvula(bm_bs, bm_bs, bf_bs, bp_bs, Vector((0.0, -1.25, Z_P)), (0, 1, 0), 0.04)
# tubo sobe e ramifica para os cascos dos trocadores e camisas
cano(bm_bs, bf_bs, bp_bs, [Vector((0.0, -1.15, Z_P)), Vector((0.0, Y_TC, Z_P)), Vector((0.15, Y_TC, Z_P))], 0.035)
suavizar(obj('boca_sul_tubos', bm_bs, 'verde_tubo'))
obj('boca_sul_flanges', bf_bs, 'ferro')

# ------------------------------------------------------------------ 3 SLOTS DE MÓDULOS (Lateral Sul-Sudoeste: y = -1.44 m, x entre -0.9 e -0.3)
MOD_Y = -1.44
bm_mrack = bmesh.new()
bm_mcart = bmesh.new()
bm_mleds = bmesh.new()

# rack metálico reforçado fixado no piso
caixa_de(bm_mrack, (-0.95, MOD_Y - 0.04, Z0), (-0.25, MOD_Y + 0.08, 0.65))
for xm in (-0.80, -0.60, -0.40):
    caixa_de(bm_mrack, (xm - 0.07, MOD_Y - 0.05, 0.15), (xm + 0.07, MOD_Y - 0.02, 0.58))
obj('modulos_rack', bm_mrack, 'grafite')

for idx, xm in enumerate((-0.80, -0.60, -0.40)):
    # cartucho de módulo
    caixa_de(bm_mcart, (xm - 0.06, MOD_Y - 0.08, 0.18), (xm + 0.06, MOD_Y + 0.02, 0.55))
    # puxador frontal
    tubo(bm_mcart, (xm - 0.04, MOD_Y - 0.09, 0.36), (xm - 0.04, MOD_Y - 0.11, 0.36), 0.007, 8)
    tubo(bm_mcart, (xm - 0.04, MOD_Y - 0.11, 0.36), (xm + 0.04, MOD_Y - 0.11, 0.36), 0.007, 8)
    tubo(bm_mcart, (xm + 0.04, MOD_Y - 0.11, 0.36), (xm + 0.04, MOD_Y - 0.09, 0.36), 0.007, 8)
    # aletas dissipadoras
    for k in range(4):
        za = 0.22 + k * 0.08
        caixa_de(bm_mcart, (xm - 0.055, MOD_Y - 0.075, za), (xm + 0.055, MOD_Y - 0.02, za + 0.012))
    # 4 LEDs por módulo
    for il in range(4):
        zl = 0.24 + il * 0.07
        cil(bm_mleds, Vector((xm + 0.045, MOD_Y - 0.082, zl)), 0.007, 0.006, Vector((0, -1, 0)), lados=10)

obj('modulos_cartuchos', bm_mcart, 'azul_petroleo')
obj('modulos_leds', bm_mleds, 'ciano')

# ------------------------------------------------------------------ FLARE DE QUEIMA LIMPA (Nordeste: x = 1.22, y = 1.22)
FL = Vector((1.22, 1.22, 0))
Z_FL = 3.65
bm_fl = bmesh.new()
# vaso separador de condensado na base
cil(bm_fl, FL + Vector((0, 0, (Z0 + 0.65) / 2)), 0.18, 0.65 - Z0, lados=32)
bmesh.ops.create_uvsphere(bm_fl, u_segments=32, v_segments=12, radius=1.0,
                          matrix=Matrix.Translation(FL + Vector((0, 0, 0.65))) @ Matrix.Diagonal((0.18, 0.18, 0.08, 1)))
# fuste do mastro subindo contínuo até o bico queimador
cil(bm_fl, FL + Vector((0, 0, (0.65 + Z_FL - 0.08) / 2)), 0.06, (Z_FL - 0.08) - 0.65, lados=24)
for z in (1.2, 1.8, 2.4, 3.0):
    cil(bm_fl, FL + Vector((0, 0, z)), 0.075, 0.024, lados=24)
# bico de queima e quebra-vento no topo
cil(bm_fl, FL + Vector((0, 0, Z_FL - 0.04)), 0.08, 0.08, lados=24)
bmesh.ops.create_cone(bm_fl, cap_ends=False, segments=24, radius1=0.08, radius2=0.12, depth=0.12,
                      matrix=Matrix.Translation(FL + Vector((0, 0, Z_FL - 0.02))))
# linhas verticais de gás piloto e acendimento ao longo do mastro
for a_deg in (45, 165, 285):
    rad = math.radians(a_deg)
    d = Vector((math.cos(rad), math.sin(rad), 0))
    tubo(bm_fl, FL + d * 0.085 + Vector((0, 0, 0.70)), FL + d * 0.085 + Vector((0, 0, Z_FL)), 0.008, 8)
suavizar(obj('flare_estrutura', bm_fl, 'oxido'))

# estais tensores
bm_est = bmesh.new()
for alvo in (Vector((1.45, 0.45, Z0)), Vector((0.45, 1.45, Z0)), Vector((1.45, 1.45, Z0))):
    topo = FL + Vector((0, 0, 2.8)) + (alvo - FL).xy.to_3d().normalized() * 0.07
    tubo(bm_est, topo, alvo + Vector((0, 0, 0.03)), 0.005, 6)
obj('flare_estais', bm_est, 'aco')

# chamas do flare
chamas = []
for k, (esc, alt) in enumerate(((0.09, 0.55), (0.04, 0.16))):
    bm_ch = bmesh.new()
    bmesh.ops.create_icosphere(bm_ch, subdivisions=2, radius=1.0)
    for v in bm_ch.verts:
        v.co.z = (v.co.z + 1.0) / 2.0
    o = obj('EFEITO_chama_%d' % k, bm_ch, 'fogo')
    o.location = FL + Vector((0, 0, Z_FL))
    chamas.append((o, esc, alt))

luz_flare = bpy.data.lights.new('LuzFlare', 'POINT')
luz_flare.color = (1.0, 0.45, 0.12)
luz_flare.energy = 25.0
o_luz_flare = bpy.data.objects.new('EFEITO_LuzFlare', luz_flare)
sc.collection.objects.link(o_luz_flare)
o_luz_flare.location = FL + Vector((0, 0, Z_FL + 0.15))

# fumaça subindo do flare
fumacas_flare = []
for k in range(5):
    bm_ff = bmesh.new()
    bmesh.ops.create_icosphere(bm_ff, subdivisions=1, radius=0.08)
    o = obj('EFEITO_fumaca_%d' % k, bm_ff, 'fumaca')
    fumacas_flare.append(o)

# ------------------------------------------------------------------ PRODUTO SÓLIDO / BICA NORTE N0 (x = -1.0 m, y = +1.44 m, z = 0.23 m)
# Encapsulador que compacta resíduos em células/baterias sólidas e esteira de roletes ejetando no norte
CX, CY = -1.0, 1.05
bm_enc = bmesh.new()
caixa_de(bm_enc, (CX - 0.22, CY - 0.22, Z0), (CX + 0.22, CY + 0.22, 0.65))
# pistão vertical de compactação
cil(bm_enc, Vector((CX, CY, 0.85)), 0.06, 0.35, lados=16)
cil(bm_enc, Vector((CX, CY, 0.68)), 0.08, 0.04, lados=16)
obj('encapsulador_corpo', bm_enc, 'azul_petroleo')

# bica/calha de roletes saindo ao norte
bm_bica = bmesh.new()
caixa_de(bm_bica, (CX - 0.15, CY + 0.18, Z_P - 0.16), (CX + 0.15, 1.48, Z_P - 0.12))
for y in (1.18, 1.30, 1.42):
    cil(bm_bica, Vector((CX, y, Z_P - 0.11)), 0.016, 0.28, Vector((1, 0, 0)), lados=12)
obj('bica_estrutura', bm_bica, 'grafite')

# células sólidas saindo na bica
celulas = []
for k in range(3):
    bm_cel = bmesh.new()
    caixa(bm_cel, (0, 0, 0.03), (0.12, 0.08, 0.06))
    cil(bm_cel, Vector((0, 0, 0.062)), 0.02, 0.01, lados=10)
    o = obj('celula_%d' % k, bm_cel, 'bateria')
    celulas.append(o)

# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço contínuo)
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    u = (q - 1) / QUADROS
    t = (q - 1) / FPS

    # 1. Agitadores girando velozmente
    for idx, ag in enumerate(agitadores):
        ag.rotation_euler = (0, 0, (u * 12 * PI + idx * PI / 2))
        ag.keyframe_insert('rotation_euler', frame=q)

    # 2. Anel quântico girando continuamente a 360° no topo da torre
    o_anel.rotation_euler = (0, 0, u * 2 * PI)
    o_anel.keyframe_insert('rotation_euler', frame=q)

    # 3. Flutuação suave da coluna de nível do líquido
    nivel_z = 0.69 + 0.06 * math.sin(u * 4 * PI)
    o_nivel.location = T1 + dN * (R_T1 + 0.11) + Vector((0, 0, nivel_z))
    o_nivel.keyframe_insert('location', frame=q)

    # 4. Robô de inspeção subindo e descendo na cremalheira da torre
    robo_z = 0.85 + 1.40 * (0.5 - 0.5 * math.cos(u * 2 * PI))
    o_robo.location = Vector((T1.x, Y_TR, robo_z))
    o_robo.keyframe_insert('location', frame=q)

    # 5. Chama do flare tremeluzente e iluminação pontual
    tremor = 1.0 + 0.18 * math.sin(u * 16 * PI) + 0.12 * math.cos(u * 28 * PI)
    for o, esc, alt in chamas:
        o.scale = (esc * tremor, esc * tremor, alt * (0.9 + 0.25 * tremor))
        o.keyframe_insert('scale', frame=q)

    luz_flare.energy = 22.0 * tremor
    luz_flare.keyframe_insert('energy', frame=q)

    # fumaça subindo do flare
    for k, o in enumerate(fumacas_flare):
        uf = (k / len(fumacas_flare) + u * 2) % 1.0
        o.location = FL + Vector((0.06 * math.sin(k + uf * 3), 0.04 * math.cos(k), Z_FL + 0.15 + 1.2 * uf))
        s = 0.05 + 0.22 * uf
        o.scale = (s, s, s)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)

    # 6. Células sólidas deslizando pela bica norte
    for k, o in enumerate(celulas):
        uc = (k / len(celulas) + u) % 1.0
        y_cel = 1.15 + uc * 0.32
        o.location = Vector((CX, y_cel, Z_P - 0.08))
        o.keyframe_insert('location', frame=q)

    # 7. Vibração dos manômetros
    for piv, norm, fase, amp in GAUGES:
        trem_g = amp * 0.15 * math.sin(u * 32 * PI + fase)
        piv.rotation_quaternion = (norm.to_track_quat('Z', 'Y').to_matrix() @ Matrix.Rotation(trem_g, 3, 'Z')).to_quaternion()
        piv.keyframe_insert('rotation_quaternion', frame=q)


# ------------------------------------------------------------------ CÂMERAS E MODOS DE RENDER
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
        sc.frame_set(int(QUADROS * 0.20) + 1)
        for i, (ang, alt) in enumerate(((305, 5.0), (215, 4.8), (125, 5.2), (35, 4.6))):
            a = math.radians(ang)
            mirar(Vector(ALVO) + Vector((math.cos(a) * 4.8, math.sin(a) * 4.8, alt)), ALVO, 30)
            sc.render.filepath = os.path.join(AQUI, 'refinador_2_%d.png' % i)
            bpy.ops.render.render(write_still=True)
    sc.frame_set(int(QUADROS * 0.35))
    # close-up olhando para os reatores, visor de nível, anel quântico e bomba
    mirar((-1.85, -1.25, 2.30), (0.10, -0.10, 1.20), 28)
    sc.render.filepath = os.path.join(AQUI, 'refinador_2_perto.png')
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
    sc.render.filepath = os.path.join(AQUI, 'refinador_2_video.mp4')
    bpy.ops.render.render(animation=True)

total_tris = sum(len(o.data.polygons) * 2 for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO') and not o.name == 'chao')
print('REFINADOR 2 ok — tris aproximados: %d' % total_tris)
