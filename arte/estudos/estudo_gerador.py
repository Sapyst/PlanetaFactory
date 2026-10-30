"""Estudo isolado (fora do jogo): gerador a combustão da IA, 2×2 tiles. Carvão entra pelo sul (ITEM_ENT_S1, tile da
direita), queima numa fornalha de tijolo com grelha, ferve a caldeira, o vapor gira a turbina, o volante de inércia e o
alternador de bobinas de cobre; a energia sai por isoladores e cabos grossos para a rede (postes).
- Boca de carga: funil baixo no sul, rosca transportadora (girando, corrente e motor) até a fornalha; comporta guilhotina
  na entrada movida por pistão (pistao1).
- Fornalha: tijolo refratário com tirantes; frente de ferro fundido com frestas em brasa e porta de inspeção que abre por
  pistão (pistao0) mostrando a grelha e o fogo. Cinzeiro com cinza escorrendo para fora.
- Caldeira (tambor com cintas e rebites) que incha com a pressão; domo de vapor, válvulas de alívio cuspindo vapor;
  caixa de fumaça e chaminé com fumaça preta que dilui e labareda no alívio.
- Turbina, volante, eixo, mancais, alternador aberto com bobinas de cobre e anéis coletores com escovas.
- Fenômeno da IA: anel de campo violeta levitando em volta do alternador, segurado por dois emissores sem tocar.
- Mastro de isoladores com antena da IA (antena). Bomba de alimentação devolve o condensado à caldeira.
Uso: blender -b --python estudo_gerador.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(23)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
EY = Vector((0, 1, 0))
EX = Vector((1, 0, 0))
EZ = Vector((0, 0, 1))


def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=64, nr=16, rot=Matrix.Identity(3), estica=(1, 1, 1)):
    """Anel tubular contínuo no plano xy local, esticado e girado."""
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        anel = []
        for b in (j * 2 * PI / nr for j in range(nr)):
            p = d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))
            p = Vector((p.x * estica[0], p.y * estica[1], p.z * estica[2]))
            anel.append(bm.verts.new(Vector(centro) + rot @ p))
        aneis.append(anel)
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def anel(bm, centro, r_in, r_out, larg, eixo, lados=48):
    """Coroa sólida (aro de volante, flange vazada) em volta de `eixo`."""
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    vs = []
    for i in range(lados):
        a = i * 2 * PI / lados
        c, s = math.cos(a), math.sin(a)
        vs.append([bm.verts.new(Vector(centro) + q @ Vector((c * r, s * r, z)))
                   for r, z in ((r_in, -larg / 2), (r_out, -larg / 2), (r_out, larg / 2), (r_in, larg / 2))])
    for i in range(lados):
        A, B = vs[i], vs[(i + 1) % lados]
        for j in range(4):
            bm.faces.new((A[j], B[j], B[(j + 1) % 4], A[(j + 1) % 4]))


def esfera(bm, p, r, seg=16):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, lados=18, flanges=True):
    """Cano por pontos: cotovelos redondos e flanges perto de cada emenda."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, lados)
        if flanges:
            u = (b - a).normalized()
            L = (b - a).length
            for p in ((a + u * min(0.07, L * 0.3)), (b - u * min(0.07, L * 0.3))):
                cil(bf, p, r * 1.5, 0.022, u, lados)
                for k in range(6):                                         # parafusos da flange
                    w = u.orthogonal().normalized()
                    w = Quaternion(u, k * PI / 3) @ w
                    cil(bf, p + w * r * 1.3, 0.006, 0.04, u, 6)
    for p in pts[1:-1]:
        esfera(bm, p, r, lados)


def isolador(bm, base, n, eixo=EZ, r=0.045):
    """Isolador de discos (cerâmica) empilhados ao longo de `eixo`."""
    e = Vector(eixo).normalized()
    cil(bm, Vector(base) + e * (n * 0.032 / 2), r * 0.38, n * 0.032 + 0.02, e, 12)
    for k in range(n):
        cil(bm, Vector(base) + e * (0.016 + k * 0.032), r, 0.012, e, 18)
        cil(bm, Vector(base) + e * (0.024 + k * 0.032), r * 0.7, 0.01, e, 18)


def caido(a, b, sag, n=14):
    a, b = Vector(a), Vector(b)
    return [a + (b - a) * t - Vector((0, 0, sag * 4 * t * (1 - t))) for t in (i / n for i in range(n + 1))]


def curva(pts, n=6):
    """Catmull-Rom pelos pontos (mangueiras e cabos que passam por onde devem)."""
    pts = [Vector(p) for p in pts]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for j in range(n):
            t = j / n
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ materiais
def tijolo_mat():
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
    sx = no(nt, 'ShaderNodeSeparateXYZ')
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
    fu = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.15, 'From Max': 0.6, 'To Min': 0.15, 'To Max': 0.85})
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


def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
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


def fogo_mat(nome='Fogo', forca=70.0):
    """Labareda em volume: absorve (escura) e emite forte — não fica pálida sob o sol."""
    m = base3d.volume_mat(nome, (1.0, 0.4, 0.05), 3.0, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = forca
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1)
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.85),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.75),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'queimado': mats.material('Queimado', (0.12, 0.10, 0.10), 1.0, 0.6, pintura=False, ferrugem=0.6, sujeira=1.0),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.16, pintura=False, sujeira=0.4),
    'cobre': mats.material('Cobre', (0.80, 0.40, 0.22), 1.0, 0.32, pintura=False, sujeira=0.7),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'carvao': mats.material('Carvão', (0.02, 0.02, 0.022), 0, 0.55, pintura=False, sujeira=0.0, desgaste=0.0),
    'cinza': mats.material('Cinza', (0.30, 0.29, 0.27), 0, 0.97, pintura=False, sujeira=0.25, desgaste=0.0),
    'escoria': mats.material('Fuligem', (0.022, 0.02, 0.019), 0.0, 0.85, pintura=False, sujeira=0.1, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
    'po': mats.material('Pó de carvão', (0.025, 0.024, 0.024), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'ceramica': mats.material('Cerâmica', (0.28, 0.09, 0.04), 0, 0.12, pintura=False, sujeira=0.6, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.55, pintura=False, sujeira=0.4, desgaste=0.0),
    'tijolo': tijolo_mat(),
    'listras': base3d.listras_mat(),
    'sinal': emissivo('Sinal', (1.0, 0.5, 0.05), 8.0),
    'frestas': emissivo('Frestas', (1.0, 0.33, 0.04), 18.0, (1.0, 0.35, 0.05)),
    'brasa': emissivo('Brasa', (1.0, 0.36, 0.05), 14.0, (1.0, 0.35, 0.05)),
    'porta_quente': emissivo('Porta quente', (0.9, 0.15, 0.02), 1.5, (0.1, 0.05, 0.04)),
    'campo': emissivo('Campo', (0.42, 0.1, 1.0), 4.0, (0.3, 0.08, 0.8)),
    'fumaca': fumaca_grad_mat('Fumaça', 12.0, 2.95, 4.8),
    'fogo': fogo_mat('Fogo', 14.0),
    'fogo_dentro': fogo_mat('Fogo interno', 45.0),
    'vapor': base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 4.0, 1.2, 2.6),
    'jato_vapor': base3d.volume_mat('Jato de vapor', (0.92, 0.92, 0.94), 7.0, -10.0, 10.0),
    'vazamento': base3d.volume_mat('Vazamento', (0.88, 0.88, 0.9), 2.5, 0.4, 1.8),
    'poeira_cinza': base3d.volume_mat('Poeira de cinza', (0.35, 0.34, 0.32), 3.0, 0.0, 0.6),
})

# ------------------------------------------------------------------ medidas
FX0, FX1, FY0, FY1, FZ1 = 0.06, 0.82, -0.62, 0.30, 0.64        # fornalha (caixa de tijolo)
PAREDE = 0.08
DX, DZ, DR = 0.44, 0.95, 0.30                                   # tambor da caldeira (eixo y)
DY0, DY1 = -0.48, 0.30
SX_, SY0, SY1, SR = DX, 0.30, 0.54, 0.33                        # caixa de fumaça
CHX, CHY, CHZ = DX, 0.42, 2.92                                  # chaminé
AX, AZ = -0.5, 0.60                                             # linha de eixo (turbina, volante, alternador)
TY0, TY1 = -0.94, -0.50                                         # turbina
VY = -0.31                                                      # volante
GY0, GY1 = -0.10, 0.56                                          # alternador
RING_Y, RING_R = 0.18, 0.47                                     # anel de campo

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()
caixa_de(bm, (-0.985, -0.985, 0.0), (0.985, -0.97, 0.08))
caixa_de(bm, (-0.985, 0.97, 0.0), (0.985, 0.985, 0.08))
caixa_de(bm, (-0.985, -0.97, 0.0), (-0.97, 0.97, 0.08))
obj('laje_listras', bm, 'listras')

# ------------------------------------------------------------------ fornalha: paredes de tijolo (oca por dentro)
bm = bmesh.new()
ZP = FZ1 - PAREDE                                                # topo das paredes = base do teto
caixa_de(bm, (FX0, FY0, 0.08), (FX0 + PAREDE, FY1, ZP))                       # oeste
caixa_de(bm, (FX0 + PAREDE, FY1 - PAREDE, 0.08), (FX1 - PAREDE, FY1, ZP))     # norte
IX0, IX1, IZ0, IZ1 = 0.38, 0.62, 0.12, 0.34                                   # entrada do carvão (sul)
caixa_de(bm, (FX0 + PAREDE, FY0, 0.08), (IX0, FY0 + PAREDE, ZP))
caixa_de(bm, (IX1, FY0, 0.08), (FX1 - PAREDE, FY0 + PAREDE, ZP))
caixa_de(bm, (IX0, FY0, IZ1), (IX1, FY0 + PAREDE, ZP))
caixa_de(bm, (IX0, FY0, 0.08), (IX1, FY0 + PAREDE, IZ0))
caixa_de(bm, (FX0, FY0, ZP), (FX1, FY1, FZ1))                                 # teto
obj('fornalha_tijolo', bm, 'tijolo')
# frente leste de ferro fundido: porta no meio, chapas com frestas embaixo
PY0, PY1, PZ0, PZ1 = -0.30, 0.0, 0.23, 0.47                                   # vão da porta
EX0 = FX1 - PAREDE
bm = bmesh.new()
caixa_de(bm, (EX0, FY0, PZ1), (FX1, FY1, ZP))
caixa_de(bm, (EX0, FY0, PZ0), (FX1, PY0, PZ1))
caixa_de(bm, (EX0, PY1, PZ0), (FX1, FY1, PZ1))
for z0, z1 in ((0.08, 0.105), (0.125, 0.15), (0.17, 0.195), (0.215, PZ0)):    # chapas: frestas de 1,5 cm entre elas
    caixa_de(bm, (EX0 + 0.03, FY0, z0), (FX1, FY1, z1))
caixa_de(bm, (EX0, FY0, 0.08), (EX0 + 0.012, FY1, PZ0))                      # fundo das frestas (atrás da brasa)
obj('frente_ferro', bm, 'ferro')
bm = bmesh.new()
caixa_de(bm, (EX0 + 0.012, FY0 + 0.01, 0.085), (EX0 + 0.03, FY1 - 0.01, PZ0 - 0.005))
obj('frestas_brasa', bm, 'frestas')
bm = bmesh.new()                                                              # moldura da porta e nervuras da frente
for z in (PZ0 - 0.02, PZ1 + 0.02):
    caixa_de(bm, (FX1, PY0 - 0.04, z - 0.015), (FX1 + 0.02, PY1 + 0.04, z + 0.015))
for y in (PY0 - 0.025, PY1 + 0.025):
    caixa_de(bm, (FX1, y - 0.015, PZ0 - 0.035), (FX1 + 0.02, y + 0.015, PZ1 + 0.035))
for y in (FY0 + 0.03, FY1 - 0.03):
    caixa_de(bm, (FX1, y - 0.02, 0.08), (FX1 + 0.025, y + 0.02, FZ1))
obj('frente_moldura', bm, 'ferro')
# esqueleto de aço: cantoneiras e tirantes
bm, br = bmesh.new(), bmesh.new()
for x in (FX0, FX1):
    for y in (FY0, FY1):
        caixa_de(bm, (x - 0.02, y - 0.02, 0.08), (x + 0.02, y + 0.02, FZ1 + 0.02))
for z in (0.2, 0.5):
    for x in (FX0 + 0.14, FX1 - 0.14):                                         # tirantes norte-sul
        tubo(bm, (x, FY0 - 0.035, z), (x, FY1 + 0.035, z), 0.009, 8)
        for y in (FY0 - 0.03, FY1 + 0.03):
            cil(br, Vector((x, y, z)), 0.02, 0.018, EY, 6)
    tubo(bm, (FX0 - 0.035, FY1 - 0.15, z), (FX1 + 0.06, FY1 - 0.15, z), 0.009, 8)   # tirante leste-oeste
    for x in (FX0 - 0.03, FX1 + 0.05):
        cil(br, Vector((x, FY1 - 0.15, z)), 0.02, 0.018, EX, 6)
obj('fornalha_esqueleto', bm, 'aco')
obj('fornalha_porcas', br, 'ferro')

# grelha, brasa e fogo por dentro
bm = bmesh.new()
for k in range(11):
    x = FX0 + PAREDE + 0.03 + k * 0.05
    caixa_de(bm, (x - 0.012, FY0 + PAREDE, 0.20), (x + 0.012, FY1 - PAREDE, 0.235))
for y in (FY0 + 0.12, -0.15, FY1 - 0.12):
    caixa_de(bm, (FX0 + PAREDE, y - 0.015, 0.18), (FX1 - PAREDE, y + 0.015, 0.20))
obj('grelha', bm, 'ferro')
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(140):
    c = Vector((random.uniform(FX0 + 0.11, FX1 - 0.11), random.uniform(FY0 + 0.11, FY1 - 0.11), 0.25 + random.uniform(0, 0.05)))
    pedra(bm if random.random() < 0.55 else bm2, c, random.uniform(0.02, 0.035))
obj('brasa_carvao', bm, 'brasa')
obj('carvao_queimando', bm2, 'carvao')
bm = bmesh.new()                                                               # cinza caída no fundo (sob a grelha)
for k in range(30):
    pedra(bm, (random.uniform(FX0 + 0.1, FX1 - 0.1), random.uniform(FY0 + 0.1, FY1 - 0.1), 0.09), random.uniform(0.02, 0.05), 0.4)
obj('cinza_fundo', bm, 'cinza')
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
fogo_in = obj('fogo_dentro', bm, 'fogo_dentro')
fogo_in.location = (0.47, -0.16, 0.36)
luz_f = bpy.data.lights.new('Fornalha', 'POINT')
luz_f.color = (1.0, 0.42, 0.1)
luz_f.shadow_soft_size = 0.15
lf = bpy.data.objects.new('Fornalha', luz_f)
sc.collection.objects.link(lf)
lf.location = (0.55, -0.15, 0.36)

# porta de inspeção (articulada no alto) e pistão 0
HX, HZ = FX1 + 0.038, PZ1 + 0.012
porta = bpy.data.objects.new('porta_inspecao', None)
sc.collection.objects.link(porta)
porta.location = (HX, (PY0 + PY1) / 2, HZ)
LARG_P, ALT_P = (PY1 - PY0) + 0.04, (PZ1 - PZ0) + 0.03
bm = bmesh.new()
caixa(bm, (0.0, 0, -ALT_P / 2), (0.024, LARG_P, ALT_P))
for k in range(3):                                                             # nervuras
    caixa(bm, (0.018, -LARG_P / 3 + k * LARG_P / 3, -ALT_P / 2), (0.014, 0.018, ALT_P - 0.03))
caixa(bm, (0.03, 0, -0.15), (0.03, 0.05, 0.04))                               # olhal do pistão
cil(bm, Vector((0.0, 0, 0)), 0.015, LARG_P + 0.06, EY, 12)                    # dobradiça
obj('porta', bm, 'ferro', porta)
bm = bmesh.new()
caixa(bm, (-0.0135, 0, -ALT_P / 2), (0.003, LARG_P - 0.02, ALT_P - 0.02))
obj('porta_dentro', bm, 'porta_quente', porta)
bm = bmesh.new()                                                               # suportes da dobradiça
for y in (PY0 - 0.035, PY1 + 0.035):
    caixa_de(bm, (FX1, y - 0.012, HZ - 0.03), (HX + 0.03, y + 0.012, HZ + 0.03))
obj('porta_mancais', bm, 'aco')
A0 = Vector((0.905, (PY0 + PY1) / 2, 0.92))                                    # âncora do pistão 0
bm = bmesh.new()                                                               # coluna e braço da âncora
caixa_de(bm, (FX1 - 0.04, A0.y - 0.02, FZ1), (FX1, A0.y + 0.02, A0.z + 0.04))
caixa_de(bm, (FX1 - 0.04, A0.y - 0.02, A0.z + 0.02), (A0.x + 0.03, A0.y + 0.02, A0.z + 0.06))
for sy in (-1, 1):
    caixa_de(bm, (A0.x - 0.02, A0.y + sy * 0.03 - 0.006, A0.z - 0.02), (A0.x + 0.02, A0.y + sy * 0.03 + 0.006, A0.z + 0.04))
obj('pistao0_suporte', bm, 'grafite')


def pistao(nome, comp_c, comp_h, rc, rh):
    """Camisa (origem na âncora, cresce em +z) e haste (origem no olhal, cresce em +z)."""
    bm = bmesh.new()
    cil(bm, Vector((0, 0, comp_c / 2)), rc, comp_c, EZ, 18)
    cil(bm, Vector((0, 0, 0.012)), rc * 1.18, 0.024, EZ, 18)
    cil(bm, Vector((0, 0, comp_c - 0.012)), rc * 1.18, 0.024, EZ, 18)
    cil(bm, Vector((0, 0, 0)), 0.014, 0.08, EY, 10)                            # pino da âncora
    cil(bm, Vector((rc * 0.9, 0, comp_c * 0.25)), 0.012, 0.03, EX, 8)            # porta de óleo
    cil(bm, Vector((rc * 0.9, 0, comp_c * 0.8)), 0.012, 0.03, EX, 8)
    c = suavizar(obj(nome + '_camisa', bm, 'amarelo'))
    c.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, comp_h / 2)), rh, comp_h, EZ, 14)
    cil(bm, Vector((0, 0, 0)), 0.012, 0.06, EY, 10)
    caixa(bm, (0, 0, 0.02), (0.03, 0.03, 0.04))
    h = suavizar(obj(nome + '_haste', bm, 'cromo'))
    h.rotation_mode = 'QUATERNION'
    return c, h


p0_c, p0_h = pistao('pistao0', 0.34, 0.32, 0.032, 0.014)


def lug_porta(th):
    D = Vector((math.sin(th), 0, -math.cos(th)))
    N = Vector((math.cos(th), 0, math.sin(th)))
    return Vector(porta.location) + D * 0.15 + N * 0.05


# ------------------------------------------------------------------ boca de carga sul (S1): funil, calha, rosca, corrente e motor
BX = 0.5
bm = bmesh.new()
caixa_de(bm, (BX - 0.13, -0.97, 0.08), (BX + 0.13, FY0 - 0.03, 0.11))         # fundo da calha
for sx in (-1, 1):
    caixa_de(bm, (BX + sx * 0.12 - 0.01, -0.97, 0.08), (BX + sx * 0.12 + 0.01, FY0 - 0.03, 0.31))
caixa_de(bm, (BX - 0.13, -0.975, 0.08), (BX + 0.13, -0.96, 0.17))               # tampa de fundo (mancal)
# funil: paredes inclinadas abrindo para cima; frente sul baixa (por onde o item cai)
for sx in (-1, 1):
    v = bmesh.ops.create_cube(bm, size=1.0)['verts']
    for vv in v:
        y = -0.97 if vv.co.y < 0 else -0.70
        z = 0.31 if vv.co.z < 0 else 0.52
        xin = BX + sx * 0.12
        xout = BX + sx * 0.21
        x = xin + (xout - xin) * (z - 0.31) / 0.21 + (0.012 * sx if vv.co.x * sx > 0 else 0)
        vv.co = Vector((x, y, z))
v = bmesh.ops.create_cube(bm, size=1.0)['verts']                                # parede norte do funil (inclinada)
for vv in v:
    x = BX - 0.21 if vv.co.x < 0 else BX + 0.21
    z = 0.31 if vv.co.z < 0 else 0.52
    y = -0.72 + (0.012 if vv.co.y > 0 else 0)
    vv.co = Vector((x, y, z))
obj('funil', bm, 'amarelo')
bm = bmesh.new()                                                                 # lábio da boca com listras
caixa_de(bm, (BX - 0.2, -0.985, 0.27), (BX + 0.2, -0.955, 0.31))
obj('boca_listras', bm, 'listras')
bm = bmesh.new()                                                                 # tampa sobre a calha perto da fornalha
caixa_de(bm, (BX - 0.135, -0.70, 0.31), (BX + 0.135, FY0 - 0.03, 0.325))
for sx in (-1, 1):
    for y in (-0.92, -0.8):
        caixa_de(bm, (BX + sx * 0.14 - 0.015, y - 0.015, 0.08), (BX + sx * 0.14 + 0.015, y + 0.015, 0.16))
obj('calha_tampa', bm, 'ferro')
rosca = bpy.data.objects.new('rosca', None)
sc.collection.objects.link(rosca)
rosca.location = (BX, 0, 0.205)
bm = bmesh.new()
cil(bm, Vector((0, -0.8225, 0)), 0.022, 0.325, EY, 12)
vs_in, vs_out = [], []
N_H, PASSO = 90, 0.09
for i in range(N_H + 1):
    a = i * 2 * PI * 3.3 / N_H
    y = -0.96 + i * (3.3 * PASSO) / N_H
    d = Vector((math.cos(a), 0, math.sin(a)))
    vs_in.append(bm.verts.new(Vector((0, y, 0)) + d * 0.02))
    vs_out.append(bm.verts.new(Vector((0, y, 0)) + d * 0.088))
for i in range(N_H):
    bm.faces.new((vs_in[i], vs_out[i], vs_out[i + 1], vs_in[i + 1]))
o = obj('rosca_helice', bm, 'aco', rosca)
md = o.modifiers.new('esp', 'SOLIDIFY')
md.thickness = 0.008
bm = bmesh.new()                                                                 # coroa da corrente no eixo
cil(bm, Vector((0, -0.985, 0)), 0.05, 0.01, EY, 16)
obj('rosca_coroa', bm, 'ferro', rosca)
bm = bmesh.new()                                                                 # caixa da corrente e motorredutor
caixa_de(bm, (BX - 0.07, -0.998, 0.12), (0.86, -0.99, 0.26))
caixa_de(bm, (BX - 0.07, -0.99, 0.12), (0.86, -0.975, 0.13))
caixa_de(bm, (BX - 0.07, -0.99, 0.25), (0.86, -0.975, 0.26))
obj('corrente_capa', bm, 'amarelo')
bm = bmesh.new()
MOT = Vector((0.78, -0.82, 0.205))
cil(bm, MOT, 0.07, 0.24, EY, 16)
for k in range(5):
    cil(bm, MOT + Vector((0, 0.02 + k * 0.03, 0)), 0.082, 0.008, EY, 16)
caixa(bm, MOT + Vector((0, -0.14, 0)), (0.13, 0.06, 0.13))                    # redutor
caixa(bm, MOT + Vector((0, 0.0, -0.09)), (0.16, 0.2, 0.04))                   # pé
caixa(bm, MOT + Vector((0.06, 0.05, 0.07)), (0.05, 0.06, 0.05))               # caixa de ligação
cil(bm, Vector((MOT.x, -0.985, MOT.z)), 0.035, 0.02, EY, 12)                  # pinhão
obj('rosca_motor', bm, 'grafite')
bm = bmesh.new()
caixa_de(bm, (MOT.x - 0.1, -0.9, 0.08), (MOT.x + 0.1, -0.7, MOT.z - 0.11))
obj('rosca_motor_base', bm, 'ferro')
bm, bm2 = bmesh.new(), bmesh.new()                                               # carvão no funil e na calha
for k in range(40):
    c = Vector((BX + random.uniform(-0.1, 0.1), random.uniform(-0.94, -0.7), 0.14 + random.uniform(0, 0.12)))
    pedra(bm, c, random.uniform(0.022, 0.034))
obj('funil_carvao', bm, 'carvao')

# comporta guilhotina na entrada da fornalha + pistão 1 (vertical)
GY = FY0 - 0.018
GZ0 = 0.105
bm = bmesh.new()
for sx in (-1, 1):                                                               # guias em U
    x = BX + sx * 0.155
    caixa_de(bm, (x - 0.02, GY - 0.022, 0.08), (x + 0.02, GY - 0.012, 1.02))
    caixa_de(bm, (x - 0.02, FY0 - 0.004, 0.08), (x + 0.02, FY0, 1.02))
    xo = x + sx * 0.02
    caixa_de(bm, (min(xo, xo - sx * 0.006), GY - 0.022, 0.08), (max(xo, xo - sx * 0.006), FY0, 1.02))
caixa_de(bm, (BX - 0.2, GY - 0.03, 1.0), (BX + 0.2, FY0, 1.05))                # travessa de cima
obj('comporta_guias', bm, 'grafite')
comporta = bpy.data.objects.new('comporta', None)
sc.collection.objects.link(comporta)
comporta.location = (BX, GY, GZ0)
bm = bmesh.new()
caixa(bm, (0, 0, 0.13), (0.29, 0.012, 0.26))
for z in (0.05, 0.13, 0.21):
    caixa(bm, (0, -0.01, z), (0.27, 0.01, 0.02))
caixa(bm, (0, -0.005, 0.27), (0.06, 0.03, 0.03))                               # olhal
obj('comporta_chapa', bm, 'ferro', comporta)
A1 = Vector((BX, GY - 0.005, 0.99))
p1_c, p1_h = pistao('pistao1', 0.32, 0.34, 0.03, 0.013)

# ------------------------------------------------------------------ caldeira (tambor), domo, válvulas, caixa de fumaça, chaminé
pivo = bpy.data.objects.new('pressao', None)
sc.collection.objects.link(pivo)
pivo.location = (DX, (DY0 + DY1) / 2, DZ)
bm = bmesh.new()
cil(bm, Vector((DX, (DY0 + DY1) / 2, DZ)), DR, DY1 - DY0, EY, 40)
res = bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=DR)  # tampo abaulado (sul)
for v in res['verts']:
    v.co = Vector((DX + v.co.x, DY0 - max(0.0, -v.co.y) * 0.4 + min(0.0, 0) , DZ + v.co.z)) if v.co.y <= 0 else Vector((DX + v.co.x, DY0, DZ + v.co.z))
o_tambor = suavizar(obj('caldeira', bm, 'casco'))
bm, br = bmesh.new(), bmesh.new()
for y in (DY0 + 0.04, -0.28, 0.06, DY1 - 0.03):                                 # cintas com rebites
    cil(bm, Vector((DX, y, DZ)), DR + 0.012, 0.04, EY, 40)
    for k in range(22):
        a = k * 2 * PI / 22
        d = Vector((math.cos(a), 0, math.sin(a)))
        cil(br, Vector((DX, y, DZ)) + d * (DR + 0.02), 0.007, 0.01, d, 6)
for k in range(9):                                                                # rebites da costura longitudinal
    cil(br, Vector((DX - 0.16, DY0 + 0.08 + k * 0.085, DZ + 0.255)), 0.007, 0.012, Vector((-0.53, 0, 0.85)), 6)
DOMO = Vector((DX, -0.12, DZ + DR - 0.03))
cil(bm, DOMO + Vector((0, 0, 0.09)), 0.11, 0.18, EZ, 24)
cil(bm, DOMO + Vector((0, 0, 0.185)), 0.135, 0.03, EZ, 24)
for k in range(12):
    a = k * PI / 6
    cil(br, DOMO + Vector((math.cos(a) * 0.123, math.sin(a) * 0.123, 0.205)), 0.008, 0.02, EZ, 6)
obj('caldeira_cintas', bm, 'ferro')
obj('caldeira_rebites', br, 'aco')
bm = bmesh.new()                                                                  # selas no teto da fornalha
for y in (-0.36, 0.12):
    v = bmesh.ops.create_cube(bm, size=1.0)['verts']
    for vv in v:
        x = DX + (0.24 if vv.co.x > 0 else -0.24)
        yy = y + (0.04 if vv.co.y > 0 else -0.04)
        z = FZ1 if vv.co.z < 0 else DZ - math.sqrt(max(DR ** 2 - (x - DX) ** 2, 0)) + 0.03
        vv.co = Vector((x, yy, z))
obj('caldeira_selas', bm, 'grafite')
VALV = []
for y, sx in ((-0.36, 1), (0.16, -1)):                                            # válvulas de alívio
    base_v = Vector((DX + sx * 0.08, y, DZ + DR - 0.01))
    bm = bmesh.new()
    cil(bm, base_v + Vector((0, 0, 0.06)), 0.028, 0.12, EZ, 14)
    cil(bm, base_v + Vector((0, 0, 0.005)), 0.05, 0.02, EZ, 14)
    cil(bm, base_v + Vector((0, 0, 0.14)), 0.045, 0.05, EZ, 14)
    for k in range(4):
        cil(bm, base_v + Vector((0, 0, 0.18 + k * 0.018)), 0.03, 0.006, EZ, 14)
    cil(bm, base_v + Vector((0, 0, 0.26)), 0.022, 0.02, EZ, 14)
    d = Vector((sx, 0, 0))
    tubo(bm, base_v + Vector((0, 0, 0.14)), base_v + Vector((0, 0, 0.17)) + d * 0.1, 0.02, 12)
    VALV.append((base_v + Vector((0, 0, 0.175)) + d * 0.11, (d + Vector((0, 0, 0.8))).normalized()))
    suavizar(obj('valvula', bm, 'ferro'))
bm = bmesh.new()                                                                  # manômetro
MANO = Vector((DX + 0.2, -0.05, DZ + 0.26))
tubo(bm, Vector((DX + 0.17, -0.05, DZ + 0.2)), MANO, 0.008, 8)
cil(bm, MANO + Vector((0.0, 0, 0.0)), 0.04, 0.02, Vector((0.6, 0, 0.8)), 18)
obj('manometro', bm, 'cromo')
# caixa de fumaça e chaminé
bm = bmesh.new()
cil(bm, Vector((SX_, (SY0 + SY1) / 2, DZ)), SR, SY1 - SY0, EY, 40)
cil(bm, Vector((SX_, SY1 + 0.012, DZ)), SR + 0.015, 0.025, EY, 40)
cil(bm, Vector((SX_, SY1 + 0.035, DZ)), SR - 0.06, 0.03, EY, 32)               # tampa de limpeza
cil(bm, Vector((CHX, CHY, DZ + SR - 0.02)), 0.18, 0.1, EZ, 24, r2=0.13)        # pé da chaminé
cil(bm, Vector((CHX, CHY, (DZ + SR + CHZ) / 2)), 0.12, CHZ - DZ - SR, EZ, 24)
obj('chamine', bm, 'queimado')
bm, br = bmesh.new(), bmesh.new()
for z in (1.65, 2.05, 2.45):
    cil(bm, Vector((CHX, CHY, z)), 0.135, 0.03, EZ, 24)
cil(bm, Vector((CHX, CHY, CHZ + 0.025)), 0.165, 0.05, EZ, 24)
cil(bm, Vector((SX_, SY0 + 0.015, DZ)), SR + 0.012, 0.035, EY, 40)
for k in range(16):
    a = k * 2 * PI / 16
    cil(br, Vector((SX_ + math.cos(a) * (SR - 0.035), SY1 + 0.052, DZ + math.sin(a) * (SR - 0.035))), 0.009, 0.015, EY, 6)
for sx in (-1, 1):                                                                # estais da chaminé até o teto da fornalha
    viga(bm, Vector((CHX + sx * 0.12, CHY, 2.3)), Vector((CHX + sx * 0.36, CHY - 0.35, FZ1 + 0.02)), 0.01)
    caixa(bm, Vector((CHX + sx * 0.36, CHY - 0.35, FZ1 + 0.01)), (0.05, 0.05, 0.02))
    viga(bm, Vector((SX_ + sx * 0.2, (SY0 + SY1) / 2, DZ - 0.24)), Vector((SX_ + sx * 0.24, (SY0 + SY1) / 2 + 0.04, 0.08)), 0.04)
    caixa(bm, Vector((SX_ + sx * 0.24, (SY0 + SY1) / 2 + 0.04, 0.09)), (0.08, 0.08, 0.02))
obj('chamine_cintas', bm, 'ferro')
obj('chamine_parafusos', br, 'aco')

# ------------------------------------------------------------------ linha de eixo: turbina, volante, alternador
bm, bf = bmesh.new(), bmesh.new()
for i in range(6):                                                                # carcaça da turbina em anéis crescentes
    y0 = TY0 + i * (TY1 - TY0) / 6
    r = 0.2 + i * 0.022
    cil(bm, Vector((AX, y0 + (TY1 - TY0) / 12, AZ)), r, (TY1 - TY0) / 6 + 0.002, EY, 36)
    cil(bf, Vector((AX, y0 + 0.006, AZ)), r + 0.018, 0.016, EY, 36)
caixa_de(bf, (AX - 0.36, TY0 + 0.02, AZ - 0.015), (AX + 0.36, TY1 - 0.02, AZ + 0.015))   # junta horizontal
for k in range(8):
    for sx in (-1, 1):
        cil(bf, Vector((AX + sx * 0.33, TY0 + 0.05 + k * 0.05, AZ + 0.02)), 0.009, 0.05, EZ, 6)
cil(bm, Vector((AX, (TY0 + TY1) / 2 - 0.06, AZ + 0.27)), 0.1, 0.12, EZ, 20)     # caixa de entrada de vapor
o_turb = suavizar(obj('turbina', bm, 'amarelo'))
obj('turbina_flanges', bf, 'ferro')
bm = bmesh.new()
caixa_de(bm, (AX - 0.24, TY0 + 0.02, 0.08), (AX + 0.24, TY1 - 0.02, AZ - 0.17))
caixa_de(bm, (AX - 0.3, TY0 - 0.01, 0.08), (AX + 0.3, TY1 + 0.01, 0.12))
obj('turbina_base', bm, 'grafite')
bm = bmesh.new()                                                                  # regulador e sensor na ponta sul
cil(bm, Vector((AX, TY0 - 0.03, AZ)), 0.09, 0.06, EY, 18)
caixa(bm, Vector((AX, TY0 - 0.04, AZ + 0.13)), (0.12, 0.06, 0.1))
obj('turbina_regulador', bm, 'grafite')
# mancais
bm = bmesh.new()
for y in (-0.43, -0.215, GY1 + 0.14):
    caixa_de(bm, (AX - 0.1, y - 0.035, 0.08), (AX + 0.1, y + 0.035, AZ - 0.06))
    cil(bm, Vector((AX, y, AZ)), 0.075, 0.07, EY, 20)
    caixa_de(bm, (AX - 0.14, y - 0.05, 0.08), (AX + 0.14, y + 0.05, 0.11))
    tubo(bm, (AX + 0.05, y, AZ + 0.07), (AX + 0.05, y, AZ + 0.13), 0.008, 8)     # copo de óleo
    cil(bm, Vector((AX + 0.05, y, AZ + 0.145)), 0.018, 0.03, EZ, 10)
obj('mancais', bm, 'ferro')
# conjunto girante: eixo, acoplamentos, volante, anéis coletores
giro = bpy.data.objects.new('eixo_giro', None)
sc.collection.objects.link(giro)
giro.location = (AX, 0, AZ)
bm = bmesh.new()
cil(bm, Vector((0, (TY1 + GY1 + 0.2) / 2, 0)), 0.035, GY1 + 0.2 - TY1, EY, 16)
for y in (TY1 + 0.02, -0.15):
    cil(bm, Vector((0, y, 0)), 0.075, 0.035, EY, 18)
obj('eixo', bm, 'aco', giro)
bm = bmesh.new()
for y in (TY1 + 0.02, -0.15):
    for k in range(6):
        a = k * PI / 3
        cil(bm, Vector((math.cos(a) * 0.058, y, math.sin(a) * 0.058)), 0.008, 0.05, EY, 6)
obj('acopl_parafusos', bm, 'ferro', giro)
RV = 0.45
bm = bmesh.new()
anel(bm, Vector((0, VY, 0)), RV - 0.07, RV, 0.1, EY, 56)
cil(bm, Vector((0, VY, 0)), 0.09, 0.12, EY, 20)
for k in range(6):
    a = k * PI / 3
    d = Vector((math.cos(a), 0, math.sin(a)))
    viga(bm, d * 0.08 + Vector((0, VY, 0)), d * (RV - 0.06) + Vector((0, VY, 0)), 0.04)
o = obj('volante', bm, 'grafite', giro)
bm = bmesh.new()                                                                   # faixa amarela no aro (lê o giro)
for k in range(4):
    a0 = k * PI / 2
    vs = []
    for j in range(7):
        a = a0 + j * 0.05
        d = Vector((math.cos(a), 0, math.sin(a)))
        vs.append((bm.verts.new(d * (RV + 0.002) + Vector((0, VY - 0.045, 0))), bm.verts.new(d * (RV + 0.002) + Vector((0, VY + 0.045, 0)))))
    for j in range(6):
        bm.faces.new((vs[j][0], vs[j + 1][0], vs[j + 1][1], vs[j][1]))
obj('volante_marcas', bm, 'amarelo', giro)
bm = bmesh.new()                                                                   # anéis coletores
for k in range(3):
    cil(bm, Vector((0, GY1 + 0.03 + k * 0.025, 0)), 0.06, 0.016, EY, 20)
obj('aneis_coletores', bm, 'cobre', giro)
bm = bmesh.new()                                                                   # escovas e porta-escovas (fixos)
for k in range(3):
    y = GY1 + 0.03 + k * 0.025
    caixa(bm, Vector((AX, y, AZ + 0.085)), (0.022, 0.014, 0.05))
    caixa(bm, Vector((AX, y, AZ + 0.12)), (0.03, 0.02, 0.02))
viga(bm, (AX - 0.14, GY1 + 0.055, AZ + 0.13), (AX + 0.14, GY1 + 0.055, AZ + 0.13), 0.02)
for sx in (-1, 1):
    viga(bm, (AX + sx * 0.14, GY1 + 0.055, AZ + 0.13), (AX + sx * 0.14, GY1 + 0.055, 0.08), 0.02)
obj('escovas', bm, 'grafite')
# alternador aberto: núcleo laminado, bobinas de cobre, aros e tirantes
bm = bmesh.new()
for k in range(18):                                                                # lâminas do núcleo
    y = GY0 + 0.06 + k * (GY1 - GY0 - 0.12) / 17
    cil(bm, Vector((AX, y, AZ)), 0.255, 0.024, EY, 36)
cil(bm, Vector((AX, (GY0 + GY1) / 2, AZ)), 0.245, GY1 - GY0 - 0.1, EY, 36)
obj('alternador_nucleo', bm, 'aco')
bm = bmesh.new()
N_B = 10
for k in range(N_B):
    a = k * 2 * PI / N_B
    rad = Vector((math.cos(a), 0, math.sin(a)))
    tg = Vector((-math.sin(a), 0, math.cos(a)))
    rot = Matrix((tg, EY, rad)).transposed()
    for c in range(3):                                                             # 3 voltas de fio por bobina
        toro(bm, Vector((AX, (GY0 + GY1) / 2, AZ)) + rad * (0.272 + c * 0.017), 0.075 - c * 0.012, 0.012, 28, 8, rot,
             (1.0, 3.3 - c * 0.35, 1.0))
obj('bobinas', bm, 'cobre')
bm = bmesh.new()
for y in (GY0, GY1):
    anel(bm, Vector((AX, y, AZ)), 0.07, 0.37, 0.04, EY, 48)
for k in range(8):
    a = k * PI / 4 + PI / 8
    d = Vector((math.cos(a), 0, math.sin(a)))
    viga(bm, Vector((AX, GY0, AZ)) + d * 0.355, Vector((AX, GY1, AZ)) + d * 0.355, 0.026)
for y in (GY0, GY1):                                                              # pés
    caixa_de(bm, (AX - 0.3, y - 0.03, 0.08), (AX - 0.2, y + 0.03, AZ - 0.25))
    caixa_de(bm, (AX + 0.2, y - 0.03, 0.08), (AX + 0.3, y + 0.03, AZ - 0.25))
    caixa_de(bm, (AX - 0.34, y - 0.06, 0.08), (AX + 0.34, y + 0.06, 0.11))
obj('alternador_carcaca', bm, 'grafite')
# caixa de terminais e isoladores (buchas) no alto
TB = Vector((AX, 0.47, AZ + 0.37))
bm = bmesh.new()
caixa(bm, TB, (0.36, 0.13, 0.1))
caixa_de(bm, (AX - 0.06, 0.44, AZ + 0.33), (AX + 0.06, 0.5, AZ + 0.34))
obj('caixa_terminais', bm, 'grafite')
bm = bmesh.new()
BUCHAS = []
for k in range(3):
    b0 = TB + Vector((-0.12 + k * 0.12, 0, 0.05))
    isolador(bm, b0, 6, EZ, 0.04)
    BUCHAS.append(b0 + Vector((0, 0, 0.22)))
obj('buchas', bm, 'ceramica')
# anel de campo da IA levitando em volta do alternador
campo = bpy.data.objects.new('anel_campo', None)
sc.collection.objects.link(campo)
campo.location = (AX, RING_Y, AZ)
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), RING_R, 0.022, 96, 14, Matrix.Rotation(PI / 2, 3, 'X'))
o = suavizar(obj('campo_anel', bm, 'campo', campo))
bm = bmesh.new()
for k in range(12):                                                               # contas de metal escuro no anel
    a = k * 2 * PI / 12
    d = Vector((math.cos(a), 0, math.sin(a)))
    cil(bm, d * RING_R, 0.032, 0.05, d.cross(EY), 12)
obj('campo_contas', bm, 'grafite', campo)
bm, bc = bmesh.new(), bmesh.new()                                                 # emissores (garras sem contato)
EMIS = []
for ang in (215, 325):
    a = math.radians(ang)
    d = Vector((math.cos(a), 0, math.sin(a)))
    p = Vector((AX, RING_Y, AZ)) + d * RING_R
    base_e = Vector((p.x + d.x * 0.08, RING_Y, 0.08))
    viga(bm, base_e, Vector((p.x + d.x * 0.08, RING_Y, p.z - 0.05)), 0.05)
    caixa(bm, Vector((base_e.x, RING_Y, 0.1)), (0.14, 0.14, 0.04))
    garfo = Vector((p.x + d.x * 0.08, RING_Y, p.z - 0.04))
    for sy in (-1, 1):                                                            # garfo dos dois lados do anel
        viga(bm, garfo, garfo + Vector((0, sy * 0.07, 0)), 0.03)
        q = p + Vector((0, sy * 0.07, 0))
        viga(bm, garfo + Vector((0, sy * 0.07, 0)), q - d * 0.0 + Vector((0, 0, 0.0)), 0.026)
        cil(bc, q, 0.022, 0.012, EY, 12)
    EMIS.append(p)
obj('emissores', bm, 'grafite')
obj('emissores_ponta', bc, 'campo')
luz_c = bpy.data.lights.new('Campo', 'POINT')
luz_c.color = (0.6, 0.3, 1.0)
luz_c.shadow_soft_size = 0.4
lc = bpy.data.objects.new('Campo', luz_c)
sc.collection.objects.link(lc)
lc.location = (AX, RING_Y, AZ + 0.2)

# ------------------------------------------------------------------ canos: vapor principal, escape → bomba → caldeira
bm, bf = bmesh.new(), bmesh.new()
TOPO_D = DOMO + Vector((0, 0, 0.2))
ZV = 1.58
ENTRADA_T = Vector((AX, (TY0 + TY1) / 2 - 0.06, AZ + 0.33))
cano(bm, bf, [TOPO_D, Vector((DX, -0.12, ZV)), Vector((AX, -0.12, ZV)), Vector((AX, ENTRADA_T.y, ZV)), ENTRADA_T], 0.045)
suavizar(obj('cano_vapor', bm, 'casco'))
obj('cano_vapor_flanges', bf, 'ferro')
bm = bmesh.new()                                                                   # válvula atuada no vapor principal
VP = Vector((0.2, -0.12, ZV))
cil(bm, VP, 0.075, 0.12, EX, 18)
viga(bm, VP, VP + Vector((0, 0, 0.12)), 0.035)
caixa(bm, VP + Vector((0, 0, 0.17)), (0.1, 0.09, 0.08))
cil(bm, VP + Vector((0.07, 0, 0.17)), 0.035, 0.05, EX, 12)
obj('valvula_vapor', bm, 'amarelo')
bm = bmesh.new()                                                                   # pórtico que segura o cano
for x in (-0.95, -0.06):
    viga(bm, (x, -0.12, 0.08), (x, -0.12, ZV - 0.05), 0.045)
    caixa(bm, (x, -0.12, 0.1), (0.1, 0.1, 0.04))
viga(bm, (-0.98, -0.12, ZV - 0.07), (-0.03, -0.12, ZV - 0.07), 0.045)
for x in (AX - 0.25, AX + 0.25):                                                   # abraçadeiras em U
    for sy in (-1, 1):
        viga(bm, (x, -0.12 + sy * 0.055, ZV - 0.05), (x, -0.12 + sy * 0.055, ZV + 0.04), 0.012)
    viga(bm, (x, -0.18, ZV + 0.05), (x, -0.06, ZV + 0.05), 0.014)
obj('portico', bm, 'amarelo')
# escape da turbina → bomba de alimentação → caldeira
BOMBA = Vector((0.0, -0.8, 0.2))
bm, bf = bmesh.new(), bmesh.new()
SAIDA_T = Vector((AX + 0.3, TY1 - 0.08, AZ - 0.08))
cano(bm, bf, [SAIDA_T, Vector((BOMBA.x, SAIDA_T.y, SAIDA_T.z)), Vector((BOMBA.x, SAIDA_T.y, BOMBA.z + 0.12)),
              Vector((BOMBA.x, BOMBA.y + 0.1, BOMBA.z + 0.12))], 0.03)
cano(bm, bf, [Vector((BOMBA.x, BOMBA.y - 0.08, BOMBA.z)), Vector((BOMBA.x, BOMBA.y - 0.08, DZ)), Vector((BOMBA.x, -0.4, DZ)),
              Vector((DX - DR + 0.03, -0.4, DZ))], 0.026)
suavizar(obj('cano_agua', bm, 'aco'))
obj('cano_agua_flanges', bf, 'ferro')
bm = bmesh.new()
cil(bm, BOMBA, 0.09, 0.1, EX, 18)                                                  # corpo da bomba (caracol)
cil(bm, BOMBA + Vector((-0.12, 0, 0)), 0.065, 0.16, EX, 16)                         # motor
caixa(bm, BOMBA + Vector((-0.06, 0, -0.09)), (0.26, 0.16, 0.04))
tubo(bm, BOMBA, BOMBA + Vector((0, 0.1, 0.12)), 0.03, 12)
tubo(bm, BOMBA, BOMBA + Vector((0, -0.08, 0.0)), 0.026, 12)
obj('bomba', bm, 'amarelo')
bm = bmesh.new()
viga(bm, (BOMBA.x, -0.4, 0.08), (BOMBA.x, -0.4, DZ - 0.04), 0.03)                # apoio do cano
viga(bm, (BOMBA.x, -0.4, 0.6), (FX0, -0.4, 0.6), 0.025)
obj('cano_apoio', bm, 'ferro')

# ------------------------------------------------------------------ cinzeiro (leste) com cinza escorrendo para fora
CZ_Y0, CZ_Y1 = -0.56, -0.36
bm = bmesh.new()
caixa_de(bm, (FX1, CZ_Y0, 0.08), (FX1 + 0.09, CZ_Y1, 0.2))                       # gaveta
v = bmesh.ops.create_cube(bm, size=1.0)['verts']                                    # bica inclinada
for vv in v:
    x = FX1 + 0.09 if vv.co.x < 0 else 0.99
    y = CZ_Y0 + 0.03 if vv.co.y < 0 else CZ_Y1 - 0.03
    z = (0.14 if x < 0.95 else 0.11) + (0.012 if vv.co.z > 0 else 0)
    vv.co = Vector((x, y, z))
for sy in (CZ_Y0 + 0.03, CZ_Y1 - 0.03):
    v = bmesh.ops.create_cube(bm, size=1.0)['verts']
    for vv in v:
        x = FX1 + 0.09 if vv.co.x < 0 else 0.99
        y = sy + (0.006 if vv.co.y > 0 else -0.006)
        z = (0.14 if x < 0.95 else 0.11) + (0.05 if vv.co.z > 0 else 0)
        vv.co = Vector((x, y, z))
obj('cinzeiro', bm, 'ferro')
bm = bmesh.new()
for k in range(26):                                                                  # cinza na bica e no monte fora da laje
    t = random.random()
    x = FX1 + 0.1 + t * 0.07
    pedra(bm, (x, random.uniform(CZ_Y0 + 0.05, CZ_Y1 - 0.05), 0.15 - 0.03 * t + 0.01), random.uniform(0.01, 0.02), 0.4)
for k in range(90):
    r = random.uniform(0, 0.2) ** 0.9
    a = random.uniform(-PI / 2, PI / 2)
    c = Vector((0.99 + math.cos(a) * r, (CZ_Y0 + CZ_Y1) / 2 + math.sin(a) * r * 1.3, 0))
    c.z = random.uniform(0.0, 0.07 * (1 - r / 0.25)) if c.x > 0.985 else 0.085
    pedra(bm, c, random.uniform(0.008, 0.02), 0.3)
for k in range(10):                                                                  # escorrido na borda da laje
    pedra(bm, (0.985, (CZ_Y0 + CZ_Y1) / 2 + random.uniform(-0.1, 0.1), random.uniform(0.02, 0.08)), random.uniform(0.012, 0.025), 0.6)
res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)               # monte de cinza encostado na laje
for v in res['verts']:
    c = v.co.copy()
    f = 1 + 0.12 * math.sin(c.x * 9 + c.y * 5) + 0.08 * math.sin(c.y * 13)
    v.co = Vector((0.985 + c.x * 0.12 * f, (CZ_Y0 + CZ_Y1) / 2 + c.y * 0.17 * f, max(c.z, -0.2) * 0.06))
for pg in bm.faces:
    pg.smooth = True
obj('cinza_monte', bm, 'cinza')
bm = bmesh.new()
mancha(bm, (1.03, (CZ_Y0 + CZ_Y1) / 2), 0.13, 0.002)
mancha(bm, (0.9, (CZ_Y0 + CZ_Y1) / 2), 0.1, 0.0815)
obj('cinza_mancha', bm, 'cinza')
cinzas = []
for k in range(12):
    bm = bmesh.new()
    pedra(bm, (0, 0, 0), random.uniform(0.008, 0.014))
    cinzas.append(obj('cinza_caindo', bm, 'cinza'))

# ------------------------------------------------------------------ unidade hidráulica e mangueiras dos pistões
HP = Vector((0.73, 0.78, 0.08))
bm = bmesh.new()
caixa_de(bm, (HP.x - 0.18, HP.y - 0.14, 0.08), (HP.x + 0.18, HP.y + 0.14, 0.32))      # tanque de óleo
cil(bm, HP + Vector((-0.06, 0, 0.34)), 0.06, 0.18, EX, 14)                           # motor
cil(bm, HP + Vector((0.08, 0, 0.34)), 0.045, 0.08, EX, 12)                           # bomba
caixa(bm, HP + Vector((0.1, -0.1, 0.3)), (0.1, 0.06, 0.08))                         # bloco de válvulas
obj('hidraulica', bm, 'grafite')
bm = bmesh.new()
cil(bm, HP + Vector((-0.1, 0.08, 0.27)), 0.025, 0.04, EZ, 10)                        # tampa do tanque
obj('hidraulica_tampa', bm, 'amarelo')
bm = bmesh.new()
V0 = HP + Vector((0.1, -0.13, 0.3))
mangueira(bm, curva([V0, V0 + Vector((0.06, -0.06, 0.08)), Vector((0.935, 0.45, 0.6)), Vector((0.935, 0.25, 1.08)),
                     Vector((0.935, A0.y + 0.12, 1.08)), A0 + Vector((0.0, 0.0, 0.07))]), 0.012)
mangueira(bm, curva([V0 + Vector((0.03, 0, 0)), V0 + Vector((0.09, -0.06, 0.08)), Vector((0.955, 0.45, 0.6)), Vector((0.955, 0.25, 1.12)),
                     Vector((0.955, -0.6, 1.12)), Vector((0.75, -0.66, 1.1)), A1 + Vector((0.06, 0.0, 0.06))]), 0.012)
bm2 = bmesh.new()                                                                   # poste com braçadeiras das mangueiras
for y in (0.25, -0.62):
    viga(bm2, (0.955, y, 0.08), (0.955, y, 1.16), 0.035)
    caixa(bm2, (0.955, y, 0.1), (0.08, 0.08, 0.04))
    caixa(bm2, (0.945, y, 1.11), (0.06, 0.05, 0.05))
caixa(bm2, (0.945, 0.25, 0.6), (0.06, 0.05, 0.05))
obj('mangueiras_poste', bm2, 'grafite')
obj('mangueiras', bm, 'borracha')

# ------------------------------------------------------------------ mastro de saída: isoladores, cabos grossos, antena
MX, MY = -0.9, 0.86
ZM = 1.65
bm = bmesh.new()
viga(bm, (MX, MY, 0.08), (MX, MY, ZM + 0.25), 0.07)
caixa(bm, (MX, MY, 0.1), (0.18, 0.18, 0.04))
viga(bm, (MX - 0.04, MY, ZM), (-0.1, MY, ZM), 0.05)                                   # cruzeta
viga(bm, (MX, MY, ZM - 0.35), (-0.4, MY, ZM - 0.02), 0.035)                           # mão-francesa
obj('mastro', bm, 'amarelo')
bm = bmesh.new()
TOPOS = []
for k, x in enumerate((-0.68, -0.46, -0.24)):
    isolador(bm, (x, MY, ZM + 0.025), 5, EZ, 0.045)
    TOPOS.append(Vector((x, MY, ZM + 0.025 + 5 * 0.032 + 0.02)))
obj('isoladores', bm, 'ceramica')
bm = bmesh.new()
for b, t in zip(BUCHAS, TOPOS):
    mangueira(bm, caido(b + Vector((0, 0, 0.0)), t, 0.06, 16), 0.016)
for t in TOPOS:                                                                        # saída para o poste (norte)
    mangueira(bm, bezier(t, t + Vector((0, 0.12, 0.03)), t + Vector((0, 0.3, 0.0)), t + Vector((0, 0.5, -0.08)), 10), 0.016)
obj('cabos', bm, 'borracha')
bm = bmesh.new()
for b in BUCHAS + TOPOS:
    cil(bm, b, 0.024, 0.03, EZ, 10)                                                   # terminais
obj('terminais', bm, 'cobre')
# eletrocalha com cabos de sinal: alternador → hidráulica, sensores da IA
bm = bmesh.new()
caixa_de(bm, (-0.2, 0.74, 0.08), (0.55, 0.84, 0.1))
for y in (0.74, 0.84):
    caixa_de(bm, (-0.2, y - 0.005, 0.08), (0.55, y + 0.005, 0.14))
obj('eletrocalha', bm, 'aco')
bm = bmesh.new()
for k in range(4):
    y = 0.765 + k * 0.022
    tubo(bm, (-0.22, y, 0.112), (0.56, y, 0.112), 0.01, 8)
mangueira(bm, bezier((-0.22, 0.79, 0.112), (-0.35, 0.79, 0.112), (AX + 0.18, 0.55, 0.3), (AX + 0.18, 0.47, AZ + 0.33), 12), 0.018)
mangueira(bm, bezier((0.56, 0.79, 0.112), (0.62, 0.79, 0.12), (0.6, 0.7, 0.25), (HP.x - 0.18, 0.72, 0.25), 8), 0.015)
obj('cabos_sinal', bm, 'borracha')
# antena da IA no topo do mastro
antena = bpy.data.objects.new('antena', None)
sc.collection.objects.link(antena)
antena.location = (MX, MY, ZM + 0.25)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.02)), 0.05, 0.04, EZ, 16)
cil(bm, Vector((0, 0, 0.2)), 0.01, 0.36, EZ, 8)
caixa(bm, Vector((0.05, 0, 0.12)), (0.06, 0.012, 0.09))                               # sensor que varre
obj('antena_haste', bm, 'grafite', antena)
bm = bmesh.new()
esfera(bm, Vector((0, 0, 0.39)), 0.022, 12)
obj('antena_luz', bm, 'sinal', antena)

# ------------------------------------------------------------------ sujeira: fuligem, óleo, pó
bm = bmesh.new()
for k in range(14):                                                                    # pó de carvão em volta da boca e do motor
    mancha(bm, (random.uniform(0.25, 0.9), random.uniform(-0.95, -0.66)), random.uniform(0.04, 0.1), 0.0815)
for k in range(6):
    mancha(bm, (random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9)), random.uniform(0.05, 0.12), 0.081)
obj('po_carvao', bm, 'po')
bm = bmesh.new()
for c, r in (((AX + 0.12, -0.43), 0.08), ((AX - 0.1, -0.215), 0.06), ((AX + 0.05, -0.75), 0.13), ((AX - 0.2, GY1 + 0.1), 0.07),
             ((HP.x - 0.25, HP.y - 0.1), 0.09), ((BOMBA.x, BOMBA.y), 0.08)):
    mancha(bm, c, r, 0.0825)
obj('oleo', bm, 'oleo')
bm = bmesh.new()                                                                       # óleo escorrendo na turbina e nos mancais
for k in range(10):
    a = random.uniform(-PI * 0.9, -PI * 0.1)
    y = random.uniform(TY0 + 0.05, TY1 - 0.05)
    r = 0.2 + (y - TY0) / (TY1 - TY0) * 0.13
    d = Vector((math.cos(a), 0, math.sin(a)))
    t = Vector((-math.sin(a), 0, math.cos(a)))
    caixa(bm, Vector((AX, y, AZ)) + d * (r + 0.004), (0.004, random.uniform(0.012, 0.025), random.uniform(0.05, 0.12)),
          Matrix((d, EY, t)).transposed())
for y in (-0.43, -0.215):
    caixa(bm, Vector((AX + 0.101, y, 0.4)), (0.003, 0.02, 0.2))
obj('oleo_escorrido', bm, 'oleo')
bm = bmesh.new()                                                                       # fuligem: chaminé, caixa de fumaça, frente da fornalha, tambor
for k in range(8):
    y = random.uniform(PY0 - 0.02, PY1 + 0.02)
    caixa(bm, Vector((FX1 + 0.002, y, PZ1 + 0.09)), (0.003, random.uniform(0.02, 0.05), random.uniform(0.08, 0.16)))
for k in range(5):
    x = BX + random.uniform(-0.12, 0.12)
    caixa(bm, Vector((x, FY0 - 0.002, IZ1 + 0.12)), (random.uniform(0.02, 0.05), 0.003, random.uniform(0.1, 0.2)))
obj('fuligem', bm, 'escoria')
bm = bmesh.new()
for k in range(12):                                                                    # fuligem na caixa de fumaça e no tambor
    a = random.uniform(0.2, PI - 0.2)
    y = random.uniform(SY0 + 0.02, SY1 - 0.02)
    d = Vector((math.cos(a), 0, math.sin(a)))
    t = Vector((-math.sin(a), 0, math.cos(a)))
    caixa(bm, Vector((SX_, y, DZ)) + d * (SR + 0.003), (0.004, random.uniform(0.03, 0.06), random.uniform(0.1, 0.25)),
          Matrix((d, EY, t)).transposed())
obj('fuligem_caixa', bm, 'escoria')
bm = bmesh.new()                                                                       # fuligem assentada: teto da fornalha e laje
for c in ((0.12, 0.2), (0.78, 0.2), (0.78, -0.55), (0.12, -0.5)):
    mancha(bm, c, random.uniform(0.05, 0.09), FZ1 + 0.001)
for k in range(10):
    mancha(bm, (random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9)), random.uniform(0.06, 0.15), 0.0812)
for c in ((0.86, 0.0), (0.88, -0.25), (0.3, -0.72), (0.65, -0.72)):
    mancha(bm, c, random.uniform(0.07, 0.12), 0.0818)
obj('fuligem_chao', bm, 'escoria')
bm = bmesh.new()
for k in range(25):                                                                    # carvão caído
    pedra(bm, (random.uniform(0.25, 0.95), random.uniform(-0.96, -0.62), 0.09), random.uniform(0.01, 0.022))
obj('caidos', bm, 'carvao')

# pressão no tambor: incha e treme (filhos do pivô)
bpy.context.view_layer.update()
for nome in ('caldeira', 'caldeira_cintas', 'caldeira_rebites', 'valvula', 'manometro'):
    for o in [o for o in sc.objects if o.name.split('.')[0] == nome]:
        o.parent = pivo
        o.matrix_parent_inverse = pivo.matrix_world.inverted()

# ------------------------------------------------------------------ volumes animados: fumaça, vapor, labaredas
def bolha(nome, mat, base_origem=False):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    if base_origem:
        for v in bm.verts:
            v.co.z = (v.co.z + 1.0) / 2.0
    o = obj(nome, bm, mat)
    o.rotation_mode = 'QUATERNION'
    return o


fumacas = [bolha('fumaca', 'fumaca') for _ in range(14)]
jatos_v = [bolha('jato_vapor', 'jato_vapor', True) for _ in range(2)]
jato_f = bolha('labareda', 'fogo', True)
VAZ = [(Vector((DX - 0.2, -0.12, ZV)), Vector((0, 0, 1))), (Vector((AX, ENTRADA_T.y + 0.07, ZV - 0.07)), Vector((0, -1, 0.5)).normalized()),
       (Vector((SAIDA_T.x + 0.07, SAIDA_T.y, SAIDA_T.z)), Vector((0, -0.4, 1)).normalized())]
vazamentos = [bolha('vazamento', 'vazamento') for _ in range(len(VAZ) * 2)]
luz_ch = bpy.data.lights.new('Clarão', 'POINT')
luz_ch.color = (1.0, 0.5, 0.15)
luz_ch.shadow_soft_size = 0.2
och = bpy.data.objects.new('Clarão', luz_ch)
sc.collection.objects.link(och)
och.location = (CHX, CHY, CHZ + 0.3)


def pressao(fr):
    """Dois ciclos por laço: sobe devagar (85%) e alivia de uma vez (15%)."""
    c = (fr * 2) % 1.0
    ciclo = int(fr * 2) % 2
    if c < 0.85:
        return c / 0.85, 0.0, ciclo
    x = (c - 0.85) / 0.15
    return 1.0 - x, math.sin(PI * x) ** 0.6, ciclo


def mira_pistao(c, h, A, P, q):
    d = P - A
    c.location = A
    c.rotation_quaternion = d.normalized().to_track_quat('Z', 'Y')
    h.location = P
    h.rotation_quaternion = (-d).normalized().to_track_quat('Z', 'Y')
    for o in (c, h):
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)


SAIDA_CH = Vector((CHX, CHY, CHZ + 0.06))
em_fr = base3d.M['frestas'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_br = base3d.M['brasa'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_cp = base3d.M['campo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_si = base3d.M['sinal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    pr, jato, ciclo = pressao(fr)
    # tambor incha e treme
    trem = 0.003 * pr * pr
    pivo.scale = (1 + 0.014 * pr * pr + trem * math.sin(2 * PI * 37 * fr), 1 + 0.004 * pr, 1 + 0.014 * pr * pr + trem * math.sin(2 * PI * 41 * fr + 1))
    pivo.location = Vector((DX + trem * math.sin(2 * PI * 53 * fr), (DY0 + DY1) / 2, DZ + trem * math.sin(2 * PI * 47 * fr + 2)))
    pivo.keyframe_insert('scale', frame=q)
    pivo.keyframe_insert('location', frame=q)
    # brasa pulsando com a pressão
    pulso = 0.7 + 0.2 * pr + 0.15 * math.sin(2 * PI * 3 * fr) * math.sin(2 * PI * 5 * fr + 1)
    em_fr.default_value = 35 * pulso
    em_fr.keyframe_insert('default_value', frame=q)
    em_br.default_value = 14 * pulso
    em_br.keyframe_insert('default_value', frame=q)
    luz_f.energy = 60 * pulso
    luz_f.keyframe_insert('energy', frame=q)
    fogo_in.scale = (0.2 + 0.03 * math.sin(2 * PI * 6 * fr), 0.3 + 0.03 * math.sin(2 * PI * 4 * fr + 1), 0.09 + 0.03 * pulso)
    fogo_in.rotation_euler = (0, 0, 2 * PI * fr)
    fogo_in.keyframe_insert('scale', frame=q)
    fogo_in.keyframe_insert('rotation_euler', frame=q)
    # porta de inspeção: abre (0,15–0,25), fica aberta, fecha (0,72–0,82)
    th = 0.85 * (suave((fr - 0.15) / 0.1) - suave((fr - 0.72) / 0.1))
    porta.rotation_euler = (0, -th, 0)
    porta.keyframe_insert('rotation_euler', frame=q)
    bpy.context.view_layer.update()
    mira_pistao(p0_c, p0_h, A0, lug_porta(th), q)
    # comporta: sobe e desce duas vezes no laço (a rosca empurra o carvão com ela aberta)
    g = 0.2 * suave(math.sin(2 * PI * 2 * fr) * 1.6 + 0.3)
    comporta.location = (BX, GY, GZ0 + g)
    comporta.keyframe_insert('location', frame=q)
    mira_pistao(p1_c, p1_h, A1, Vector((BX, GY - 0.005, GZ0 + g + 0.285)), q)
    # giros
    rosca.rotation_euler = (0, 2 * PI * 4 * fr, 0)
    rosca.keyframe_insert('rotation_euler', frame=q)
    giro.rotation_euler = (0, 2 * PI * 3 * fr, 0)
    giro.keyframe_insert('rotation_euler', frame=q)
    campo.rotation_euler = (0, -2 * PI * fr, 0)
    campo.scale = [1 + 0.012 * math.sin(2 * PI * 4 * fr)] * 3
    campo.keyframe_insert('rotation_euler', frame=q)
    campo.keyframe_insert('scale', frame=q)
    em_cp.default_value = 1.6 + 1.2 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr)) + 1.5 * jato
    em_cp.keyframe_insert('default_value', frame=q)
    luz_c.energy = 18 + 12 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr))
    luz_c.keyframe_insert('energy', frame=q)
    antena.rotation_euler = (0, 0, 2 * PI * fr)
    antena.keyframe_insert('rotation_euler', frame=q)
    em_si.default_value = 12.0 if (fr * 4) % 1.0 < 0.25 else 0.4
    em_si.keyframe_insert('default_value', frame=q)
    # jatos de vapor nas válvulas de alívio (uma por ciclo) e labareda na chaminé
    for k, o in enumerate(jatos_v):
        ativo = jato if k == ciclo else 0.0
        pos, d = VALV[k]
        o.location = pos
        o.rotation_quaternion = d.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), fr * 40)
        o.scale = (max(0.1 * ativo, 0.02), max(0.1 * ativo, 0.02), max(0.7 * ativo, 0.05))
        o.hide_render = ativo < 0.05
        o.hide_viewport = o.hide_render
        for c in ('location', 'rotation_quaternion', 'scale', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
    jato_f.location = SAIDA_CH
    jato_f.rotation_quaternion = Quaternion((0, 0, 1), fr * 40)
    jato_f.scale = (max(0.1 * jato, 0.02), max(0.1 * jato, 0.02), max(0.55 * jato, 0.05))
    jato_f.hide_render = jato < 0.05
    jato_f.hide_viewport = jato_f.hide_render
    for c in ('location', 'rotation_quaternion', 'scale', 'hide_render', 'hide_viewport'):
        jato_f.keyframe_insert(c, frame=q)
    luz_ch.energy = 200 * jato
    luz_ch.keyframe_insert('energy', frame=q)
    # vazamentos de vapor nas flanges
    for k, o in enumerate(vazamentos):
        pt, d = VAZ[k % len(VAZ)]
        u = ((k // len(VAZ)) / 2 + fr * 4 + k * 0.13) % 1.0
        f = 0.4 + 0.6 * pr
        o.location = pt + d * (0.1 * u) + Vector((0.03 * u, 0, 0.35 * u))
        o.scale = [max(0.001, (0.025 + 0.11 * u) * f)] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # fumaça preta da chaminé
    for k, o in enumerate(fumacas):
        u = (k / len(fumacas) + fr * 2) % 1.0
        o.location = SAIDA_CH + Vector((0.7 * u * u, 0.25 * u, 1.9 * u + 0.02))
        o.scale = [0.13 + 0.5 * u] * 3
        o.rotation_quaternion = Quaternion((0.3, 1, 0.2), k + u * 2)
        for c in ('location', 'scale', 'rotation_quaternion'):
            o.keyframe_insert(c, frame=q)
    # cinza escorrendo da bica
    for k, o in enumerate(cinzas):
        tt = ((k / len(cinzas) + fr * 3) % 1.0) * 0.22
        o.location = Vector((0.99 + 0.25 * tt, (CZ_Y0 + CZ_Y1) / 2 + 0.06 * math.sin(k * 2.3), 0.12 - 4.9 * tt * tt))
        o.scale = [1.0 if o.location.z > 0.0 else 0.001] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects) + [luz_f, luz_c, luz_ch] + [base3d.M[n] for n in ('frestas', 'brasa', 'campo', 'sinal')]:
    ad = getattr(o, 'animation_data', None) if not hasattr(o, 'node_tree') else getattr(o.node_tree, 'animation_data', None)
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
    prf = bpy.context.preferences.addons['cycles'].preferences
    prf.compute_device_type = 'OPTIX'
    prf.get_devices()
    for dv in prf.devices:
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


ALVO = (0.0, 0.0, 1.05)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_vistas = [int(a) for a in args[1:]] if len(args) > 1 else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.frame_set(int(QUADROS * 0.46) + 1)                                   # porta aberta, alívio do 1º ciclo
    vistas = [('0', (300, 2.0)), ('1', (210, 2.2)), ('2', (120, 2.4)), ('3', (30, 1.8))]
    for i, (nome, (ang, alt)) in enumerate(vistas):
        if so_vistas is not None and i not in so_vistas:
            continue
        sc.frame_set(int(QUADROS * (0.46 if i in (0, 2) else 0.38)) + 1)   # 0 e 2: alívio com labareda; 1 e 3: fumaça preta
        sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 5.4, math.sin(a) * 5.4, alt)), ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'gerador_%s.png' % nome)
        bpy.ops.render.render(write_still=True)
    sc.frame_set(int(QUADROS * 0.46) + 1)
    if so_vistas is None or 4 in so_vistas:
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((2.35, -1.75, 1.05), (0.68, -0.42, 0.42), 34)                 # de perto: porta, frestas, cinzeiro, boca
        sc.render.filepath = os.path.join(AQUI, 'gerador_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_vistas is None or 5 in so_vistas:
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((-2.2, -1.45, 1.35), (-0.45, -0.05, 0.65), 34)                # de perto: volante, alternador, anel de campo
        sc.render.filepath = os.path.join(AQUI, 'gerador_perto2.png')
        bpy.ops.render.render(write_still=True)
print('GERADOR ok')
