"""Estudo isolado (fora do jogo): broca de minério como sonda de perfuração de verdade, 2×2 tiles.
Chassi sobre sapatas estabilizadoras, torre treliçada, cabeça motriz que desce pelos trilhos girando uma rosca
helicoidal (trado) que entra no chão, dois pistões de avanço, corrente porta-cabos levando as mangueiras, unidade de
força com radiador e escapamento, detrito em volta do furo, rosca transportadora até o funil e calha de saída (sul,
tile da esquerda). Materiais físicos (mats.py).
Uso: blender -b --python estudo_broca.py -- foto | video"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s: a cabeça desce e volta uma vez; o trado dá 8 voltas (laço perfeito)
VOLTAS = 8
DECK = 0.29                  # topo do piso do chassi
FURO = Vector((0.0, -0.2, 0))
Z_ALTO, Z_BAIXO = 2.2, 1.2   # curso da cabeça motriz
random.seed(4)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def listras_mat():
    m = bpy.data.materials.new('Listras')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type, wave.bands_direction, wave.wave_profile = 'BANDS', 'DIAGONAL', 'SAW'
    wave.inputs['Scale'].default_value = 7.0
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    corte = nt.nodes.new('ShaderNodeMath')
    corte.operation = 'GREATER_THAN'
    corte.inputs[1].default_value = 0.5
    nt.links.new(wave.outputs['Fac'], corte.inputs[0])
    sujo = nt.nodes.new('ShaderNodeTexNoise')
    sujo.inputs['Scale'].default_value = 14.0
    nt.links.new(tc.outputs['Object'], sujo.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (0.03, 0.03, 0.03, 1)
    mix.inputs[7].default_value = (0.62, 0.42, 0.04, 1)
    nt.links.new(corte.outputs['Value'], mix.inputs[0])
    gasto = nt.nodes.new('ShaderNodeMix')
    gasto.data_type, gasto.blend_type = 'RGBA', 'MULTIPLY'
    gasto.inputs[0].default_value = 0.5
    nt.links.new(mix.outputs[2], gasto.inputs[6])
    nt.links.new(sujo.outputs['Color'], gasto.inputs[7])
    nt.links.new(gasto.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    return m


def lampada_mat():
    m = bpy.data.materials.new('Lâmpada')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1.0, 0.45, 0.05, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.42, 0.04, 1)
    b.inputs['Emission Strength'].default_value = 6.0
    return m


def volume_mat(nome, cor, dens, z0, z1):
    """Volume com ruído; a densidade some conforme sobe (z0 → z1 no mundo): fumaça e poeira que se desfazem."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ru = nt.nodes.new('ShaderNodeTexNoise')
    ru.inputs['Scale'].default_value = 3.0
    ru.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    forma = nt.nodes.new('ShaderNodeMapRange')                 # bolha: some na borda da esfera
    forma.inputs['From Min'].default_value = 0.42
    forma.inputs['From Max'].default_value = 0.68
    nt.links.new(ru.outputs['Fac'], forma.inputs['Value'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    sobe = nt.nodes.new('ShaderNodeMapRange')
    sobe.inputs['From Min'].default_value = z0
    sobe.inputs['From Max'].default_value = z1
    sobe.inputs['To Min'].default_value = dens
    sobe.inputs['To Max'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], sobe.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(forma.outputs['Result'], mul.inputs[0])
    nt.links.new(sobe.outputs['Result'], mul.inputs[1])
    nt.links.new(mul.outputs['Value'], vol.inputs['Density'])
    return m


M = {
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.6),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'trado': mats.material('Trado', (0.36, 0.36, 0.36), 1.0, 0.35, pintura=False, ferrugem=0.6, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'rocha': mats.material('Rocha', (0.17, 0.14, 0.11), 0, 0.9, sujeira=0.4, desgaste=0.0),
    'minerio': mats.material('Minério', (0.30, 0.13, 0.07), 0.2, 0.7, pintura=False, sujeira=0.5, ferrugem=0.5),
    'terra': mats.material('Terra', (0.11, 0.085, 0.065), 0, 0.95, sujeira=0.3, desgaste=0.0),
    'escuro': mats.material('Furo', (0.01, 0.008, 0.006), 0, 1.0, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': listras_mat(),
    'lampada': lampada_mat(),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.16, 0.11, 0.07), 0, 0.35, pintura=False, sujeira=0.3, desgaste=0.0),
    'fumaca': volume_mat('Fumaça', (0.16, 0.16, 0.17), 9.0, 1.45, 2.9),
    'poeira': volume_mat('Poeira', (0.42, 0.33, 0.24), 4.0, 0.0, 0.9),
}


# ------------------------------------------------------------------ geometria
def obj(nome, bm, mat, pai=None):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    o.data.materials.append(M[mat])
    if pai is not None:
        o.parent = pai
    return o


def caixa(bm, centro, tam, rot=Matrix.Identity(3)):
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res['verts']:
        v.co = Vector(centro) + rot @ Vector((v.co.x * tam[0], v.co.y * tam[1], v.co.z * tam[2]))
    return res['verts']


def caixa_de(bm, a, b):
    """Caixa alinhada aos eixos entre os cantos a e b."""
    a, b = Vector(a), Vector(b)
    caixa(bm, (a + b) / 2, tuple(abs(b[i] - a[i]) for i in range(3)))


def cil(bm, centro, r, h, eixo=Vector((0, 0, 1)), lados=12, r2=None):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=r, radius2=r if r2 is None else r2, depth=h,
                          matrix=Matrix.Translation(centro) @ q)


def tubo(bm, a, b, r, lados=8):
    a, b = Vector(a), Vector(b)
    cil(bm, (a + b) / 2, r, (b - a).length, b - a, lados)


def viga(bm, a, b, w):
    """Barra quadrada de a até b."""
    a, b = Vector(a), Vector(b)
    q = (b - a).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((a + b) / 2) @ q @ Matrix.Diagonal((w, w, (b - a).length, 1)))


def bezier(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    return [p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3
            for t in (i / n for i in range(n + 1))]


def mangueira(bm, pts, r):
    for a, b in zip(pts, pts[1:]):
        u = (b - a).normalized()
        tubo(bm, a - u * r * 0.6, b + u * r * 0.6, r, 6)


def pedra(bm, centro, r, achatar=0.6):
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    rot = Matrix.Rotation(random.uniform(0, 2 * PI), 3, 'Z') @ Matrix.Rotation(random.uniform(-0.5, 0.5), 3, 'X')
    for v in res['verts']:
        c = v.co * random.uniform(0.75, 1.2)
        c.z *= achatar
        v.co = Vector(centro) + rot @ c


# ------------------------------------------------------------------ chassi, sapatas, piso com abertura
bm = bmesh.new()
for x in (-0.72, 0.72):                                                   # longarinas em I
    caixa_de(bm, (x - 0.05, -0.92, 0.10), (x + 0.05, 0.92, 0.12))
    caixa_de(bm, (x - 0.012, -0.92, 0.12), (x + 0.012, 0.92, 0.245))
    caixa_de(bm, (x - 0.05, -0.92, 0.245), (x + 0.05, 0.92, 0.26))
for y in (-0.85, -0.2, 0.42, 0.85):                                       # travessas
    caixa_de(bm, (-0.72, y - 0.03, 0.14), (0.72, y + 0.03, 0.26))
obj('chassi', bm, 'grafite')
bm = bmesh.new()                                                          # piso com abertura em volta do furo
ax0, ax1, ay0, ay1 = FURO.x - 0.25, FURO.x + 0.25, FURO.y - 0.25, FURO.y + 0.24
caixa_de(bm, (-0.92, -0.92, 0.26), (ax0, 0.92, DECK))
caixa_de(bm, (ax1, -0.92, 0.26), (0.92, 0.92, DECK))
caixa_de(bm, (ax0, -0.92, 0.26), (ax1, ay0, DECK))
caixa_de(bm, (ax0, ay1, 0.26), (ax1, 0.92, DECK))
for i in range(14):                                                       # chapa xadrez: gomos em relevo
    for j in range(14):
        x, y = -0.86 + i * 0.132, -0.86 + j * 0.132
        if ax0 - 0.03 < x < ax1 + 0.03 and ay0 - 0.03 < y < ay1 + 0.03:
            continue
        caixa(bm, (x, y, DECK + 0.002), (0.05, 0.012, 0.004), Matrix.Rotation(PI / 4 * (1 if (i + j) % 2 else -1), 3, 'Z'))
obj('piso', bm, 'aco')
bm = bmesh.new()                                                          # listras na borda do piso e da abertura
for a, b in (((-0.92, -0.925, 0.262), (0.92, -0.92, DECK)), ((-0.92, 0.92, 0.262), (0.92, 0.925, DECK)),
             ((-0.925, -0.92, 0.262), (-0.92, 0.92, DECK)), ((0.92, -0.92, 0.262), (0.925, 0.92, DECK)),
             ((ax0 - 0.05, ay0 - 0.05, DECK), (ax1 + 0.05, ay0, DECK + 0.002)),
             ((ax0 - 0.05, ay1, DECK), (ax1 + 0.05, ay1 + 0.05, DECK + 0.002)),
             ((ax0 - 0.05, ay0, DECK), (ax0, ay1, DECK + 0.002)), ((ax1, ay0, DECK), (ax1 + 0.05, ay1, DECK + 0.002))):
    caixa_de(bm, a, b)
obj('listras_piso', bm, 'listras')
bm, bc = bmesh.new(), bmesh.new()                                         # sapatas estabilizadoras nos cantos
for sx in (-1, 1):
    for sy in (-1, 1):
        p = Vector((sx * 0.86, sy * 0.86, 0))
        caixa_de(bm, (sx * 0.72, p.y - 0.04, 0.16), (p.x + sx * 0.05, p.y + 0.04, 0.24))            # braço
        cil(bm, Vector((p.x, p.y, 0.30)), 0.045, 0.16, lados=10)                                  # cilindro do macaco
        cil(bc, Vector((p.x, p.y, 0.12)), 0.026, 0.20, lados=8)                                   # haste
        caixa(bm, (p.x, p.y, 0.012), (0.16, 0.16, 0.024))                                         # sapata
        cil(bm, Vector((p.x, p.y, 0.03)), 0.04, 0.02, lados=8)
obj('sapatas', bm, 'amarelo')
obj('hastes_sapatas', bc, 'cromo')
bm = bmesh.new()                                                          # guarda-corpo leste e oeste
for x in (-0.89, 0.89):
    for y in (-0.6, 0.0, 0.6):
        tubo(bm, (x, y, DECK), (x, y, DECK + 0.55), 0.016)
    for z in (0.3, 0.55):
        tubo(bm, (x, -0.62, DECK + z), (x, 0.62, DECK + z), 0.016)
obj('guarda_corpo', bm, 'amarelo')

# ------------------------------------------------------------------ furo no chão: colar, boca escura e detrito
bm = bmesh.new()
cil(bm, FURO + Vector((0, 0, 0.035)), 0.22, 0.07, lados=20)
obj('colar', bm, 'aco')
bm = bmesh.new()
cil(bm, FURO + Vector((0, 0, 0.0715)), 0.175, 0.002, lados=20)
obj('boca', bm, 'escuro')
bm, bmn = bmesh.new(), bmesh.new()
for k in range(90):                                                       # detrito em volta do colar
    a = random.uniform(0, 2 * PI)
    r = 0.22 + abs(random.gauss(0, 0.12))
    c = FURO + Vector((math.cos(a) * r, math.sin(a) * r, 0.01))
    pedra(bmn if random.random() < 0.3 else bm, c, random.uniform(0.012, 0.035))
for k in range(40):                                                       # e grãos sobre o colar
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.18, 0.22)
    pedra(bm, FURO + Vector((math.cos(a) * r, math.sin(a) * r, 0.075)), random.uniform(0.008, 0.016))
obj('detrito', bm, 'rocha')
obj('detrito_minerio', bmn, 'minerio')
bm = bmesh.new()                                                          # mancha de terra revirada
cil(bm, FURO + Vector((0, 0, 0.002)), 0.62, 0.004, lados=24)
obj('terra', bm, 'terra')

# ------------------------------------------------------------------ torre treliçada
YF, YT = 0.12, 0.42                                                       # montantes da frente e de trás
TOPO = 2.78
bm = bmesh.new()
for x in (-0.2, 0.2):
    for y in (YF, YT):
        caixa_de(bm, (x - 0.03, y - 0.03, DECK), (x + 0.03, y + 0.03, TOPO))
niveis = [DECK + 0.05 + i * 0.35 for i in range(8)]
for i, z in enumerate(niveis):
    for x in (-0.2, 0.2):                                                 # laterais: travessa + diagonal
        viga(bm, (x, YF, z), (x, YT, z), 0.025)
        if i + 1 < len(niveis):
            a, b = ((x, YF, z), (x, YT, niveis[i + 1])) if i % 2 else ((x, YT, z), (x, YF, niveis[i + 1]))
            viga(bm, a, b, 0.02)
    viga(bm, (-0.2, YT, z), (0.2, YT, z), 0.025)                          # fundo
    if i + 1 < len(niveis):
        viga(bm, (-0.2, YT, z), (0.2, YT, niveis[i + 1]), 0.02)
for sx in (-1, 1):                                                        # escoras até o chassi
    viga(bm, (sx * 0.2, YT, 1.45), (sx * 0.5, 0.86, DECK + 0.02), 0.04)
    caixa(bm, (sx * 0.5, 0.86, DECK + 0.015), (0.1, 0.1, 0.03))
for x in (-0.2, 0.2):                                                     # sapatas dos montantes
    for y in (YF, YT):
        caixa(bm, (x, y, DECK + 0.015), (0.11, 0.11, 0.03))
caixa_de(bm, (-0.26, YF - 0.06, TOPO), (0.26, YT + 0.06, TOPO + 0.06))    # coroa
obj('torre', bm, 'amarelo')
bm = bmesh.new()                                                          # polia da coroa e farol
cil(bm, Vector((0, (YF + YT) / 2, TOPO + 0.16)), 0.1, 0.04, Vector((1, 0, 0)), lados=16)
for x in (-0.04, 0.04):
    caixa(bm, (x, (YF + YT) / 2, TOPO + 0.12), (0.015, 0.06, 0.16))
cil(bm, Vector((0.18, YT, TOPO + 0.1)), 0.03, 0.08, lados=8)
obj('polia', bm, 'aco')
bm = bmesh.new()
cil(bm, Vector((0.18, YT, TOPO + 0.17)), 0.035, 0.07, lados=10)
obj('farol', bm, 'lampada')
bm = bmesh.new()                                                          # trilhos cromados na frente dos montantes
for x in (-0.2, 0.2):
    caixa_de(bm, (x - 0.012, YF - 0.036, DECK + 0.2), (x + 0.012, YF - 0.03, TOPO - 0.1))
obj('trilhos', bm, 'cromo')
bm = bmesh.new()                                                          # bucha guia do trado no piso
cil(bm, FURO + Vector((0, 0, DECK + 0.04)), 0.21, 0.08, lados=16)
cil(bm, FURO + Vector((0, 0, DECK + 0.09)), 0.24, 0.02, lados=16)
obj('bucha', bm, 'grafite')
for i in range(8):                                                        # parafusos da bucha
    a = i * PI / 4
    bm = bmesh.new()
    cil(bm, FURO + Vector((math.cos(a) * 0.225, math.sin(a) * 0.225, DECK + 0.105)), 0.009, 0.014, lados=6)
    obj('parafuso', bm, 'cromo')

# ------------------------------------------------------------------ cabeça motriz (anda na torre)
cabeca = bpy.data.objects.new('cabeca', None)
sc.collection.objects.link(cabeca)
C = Vector((FURO.x, FURO.y, 0))                                           # origem da cabeça: eixo do furo, z = zc
bm = bmesh.new()
caixa(bm, (0, 0, 0), (0.36, 0.36, 0.26))                                  # caixa de engrenagens
caixa_de(bm, (-0.14, 0.15, -0.1), (0.14, YF - FURO.y - 0.045, 0.1))       # braço até o carro
caixa_de(bm, (-0.3, YF - FURO.y - 0.065, -0.2), (0.3, YF - FURO.y - 0.042, 0.2))   # carro
for x in (-0.2, 0.2):                                                     # patins nos trilhos
    for z in (-0.16, 0.16):
        caixa(bm, (x, YF - FURO.y - 0.02, z), (0.1, 0.05, 0.07))
for sx in (-1, 1):                                                        # orelhas dos pistões
    caixa_de(bm, (sx * 0.22, YF - FURO.y - 0.06, -0.13), (sx * 0.36, 0.28 - FURO.y + 0.05, -0.09))
obj('cabeca_corpo', bm, 'amarelo', cabeca)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.16)), 0.16, 0.06, lados=16)                       # redutor
cil(bm, Vector((0, 0, 0.3)), 0.11, 0.22, lados=16)                        # motor
for k in range(6):
    cil(bm, Vector((0, 0, 0.21 + k * 0.035)), 0.13, 0.008, lados=16)      # aletas
cil(bm, Vector((0, 0, 0.42)), 0.09, 0.03, lados=16)
caixa(bm, (0.13, -0.06, 0.3), (0.08, 0.1, 0.12))                          # caixa de ligação
for x in (-0.09, 0.09):                                                   # parafusos de fixação
    for y in (-0.15, 0.15):
        cil(bm, Vector((x * 1.6, y, 0.135)), 0.012, 0.012, lados=6)
obj('cabeca_motor', bm, 'grafite', cabeca)
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.17)), 0.06, 0.08, lados=12)                      # árvore de saída
caixa(bm, (0.17, 0.0, 0.0), (0.012, 0.2, 0.12))                          # placa de identificação
obj('cabeca_aco', bm, 'aco', cabeca)
bm = bmesh.new()
for x in (0.1, 0.16):                                                     # conexões hidráulicas
    cil(bm, Vector((x - 0.27, 0.12, 0.18)), 0.014, 0.05, lados=6)
obj('cabeca_cobre', bm, 'cromo', cabeca)

# trado: tubo, hélice e ponta com pastilhas; origem no topo, gira em z
trado = bpy.data.objects.new('trado', None)
sc.collection.objects.link(trado)
COMP = 3.4
bm = bmesh.new()
cil(bm, Vector((0, 0, -COMP / 2)), 0.04, COMP, lados=12)
cil(bm, Vector((0, 0, -0.05)), 0.055, 0.1, lados=6)                       # luva sextavada
cil(bm, Vector((0, 0, -COMP - 0.06)), 0.14, 0.12, lados=12, r2=0.02)      # ponta
obj('trado_tubo', bm, 'trado', trado)
bm = bmesh.new()
PASSO_H, R0, R1, ESP = 0.17, 0.038, 0.15, 0.012
n = int((COMP - 0.16) / PASSO_H * 28)
ant = None
for i in range(n + 1):
    a = i * 2 * PI / 28
    z = -0.14 - i * PASSO_H / 28
    c, s = math.cos(a), math.sin(a)
    r1 = R1 * (1 - 0.04 * random.random())                                # borda gasta, irregular
    vs = [bm.verts.new((R0 * c, R0 * s, z)), bm.verts.new((r1 * c, r1 * s, z)),
          bm.verts.new((r1 * c, r1 * s, z - ESP)), bm.verts.new((R0 * c, R0 * s, z - ESP))]
    if ant:
        for j in range(3):
            bm.faces.new((ant[j], ant[j + 1], vs[j + 1], vs[j]))
    else:
        bm.faces.new(vs)
    ant = vs
bm.faces.new(list(reversed(ant)))
obj('trado_helice', bm, 'trado', trado)
bm = bmesh.new()
for k in range(4):                                                        # pastilhas de corte
    a = k * PI / 2
    caixa(bm, (math.cos(a) * 0.08, math.sin(a) * 0.08, -COMP - 0.1), (0.05, 0.02, 0.03), Matrix.Rotation(a, 3, 'Z'))
obj('trado_pastilhas', bm, 'cromo', trado)
# grãos presos na hélice (sobem girando com o trado)
bm = bmesh.new()
for k in range(70):
    zz = random.uniform(-COMP, -0.3)
    i = (-zz - 0.14) * 28 / PASSO_H
    a = i * 2 * PI / 28
    r = random.uniform(0.06, 0.13)
    pedra(bm, (math.cos(a) * r, math.sin(a) * r, zz + 0.012), random.uniform(0.01, 0.022))
obj('trado_terra', bm, 'rocha', trado)

# ------------------------------------------------------------------ pistões de avanço (camisa fixa, haste na cabeça)
YP = 0.28
CAMISA = (DECK + 0.03, 1.36)
bm, bh = bmesh.new(), bmesh.new()
for sx in (-1, 1):
    cil(bm, Vector((sx * 0.3, YP, (CAMISA[0] + CAMISA[1]) / 2)), 0.042, CAMISA[1] - CAMISA[0], lados=12)
    cil(bm, Vector((sx * 0.3, YP, CAMISA[1] - 0.03)), 0.05, 0.05, lados=12)          # cabeçote
    caixa(bm, (sx * 0.3, YP, DECK + 0.03), (0.1, 0.1, 0.06))                         # olhal na base
    cil(bm, Vector((sx * 0.3, YP, CAMISA[0] + 0.25)), 0.05, 0.03, lados=12)          # abraçadeira
obj('pistoes_camisa', bm, 'grafite')
HASTE = 0.9
hastes = []
for sx in (-1, 1):
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -HASTE / 2)), 0.024, HASTE, lados=10)
    hastes.append(obj('pistao_haste', bm, 'cromo'))
    hastes[-1].location = (sx * 0.3, YP, Z_ALTO - 0.11)

# ------------------------------------------------------------------ corrente porta-cabos (U que acompanha a cabeça)
XC, YA, RB = -0.44, 0.31, 0.065                    # pista fixa em y = YA, pista da cabeça em y = YA − 2·RB
Z_FIXO = 1.7
COMP_CORR = 2.0 + PI * RB
bm = bmesh.new()
caixa_de(bm, (XC - 0.04, YA - 0.02, Z_FIXO - 0.05), (-0.2, YA + 0.02, Z_FIXO + 0.02))   # suporte fixo na torre
caixa_de(bm, (XC - 0.04, YA - 0.06, Z_FIXO - 0.02), (XC + 0.04, YA + 0.03, Z_FIXO + 0.02))
obj('corrente_suporte', bm, 'grafite')
bm = bmesh.new()                                                         # suporte da corrente na cabeça
caixa_de(bm, (XC - 0.04, YA - 2 * RB - 0.03, -0.04), (-0.18, YA - 2 * RB + 0.03, 0.0))
obj('cabeca_suporte_corrente', bm, 'grafite', cabeca)
N_ELOS = int(COMP_CORR / 0.045)
elos = []
for k in range(N_ELOS):
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (0.07, 0.045, 0.04))
    for sx in (-1, 1):
        caixa(bm, (sx * 0.036, 0, 0), (0.006, 0.05, 0.044))
    o = obj('elo', bm, 'grafite')
    o.rotation_mode = 'QUATERNION'
    elos.append(o)
bm = bmesh.new()                                                         # mangueiras saindo da corrente para o motor
mangueira(bm, bezier((XC, YA - 2 * RB, 0.02), (XC, YA - 2 * RB, 0.12), (-0.3, 0.05, 0.2), (-0.15, 0.12, 0.18), 8), 0.014)
mangueira(bm, bezier((XC + 0.02, YA - 2 * RB, 0.02), (XC + 0.02, YA - 2 * RB, 0.16), (-0.12, -0.05, 0.38), (0.0, -0.06, 0.38), 8), 0.012)
obj('cabeca_mangueiras', bm, 'borracha', cabeca)


def ponto_corrente(sig, zc):
    """Ponto da corrente a sig metros da ponta fixa; o fundo do U fica a meio caminho (comprimento constante)."""
    zb = (Z_FIXO + zc + PI * RB - COMP_CORR) / 2
    perna1 = Z_FIXO - zb
    if sig < perna1:
        return Vector((XC, YA, Z_FIXO - sig)), Vector((0, 0, -1))
    sig -= perna1
    if sig < PI * RB:
        a = sig / RB
        cy = YA - RB
        return Vector((XC, cy + RB * math.cos(a), zb - RB * math.sin(a))), Vector((0, -math.sin(a), -math.cos(a)))
    sig -= PI * RB
    return Vector((XC, YA - 2 * RB, zb + sig)), Vector((0, 0, 1))


# ------------------------------------------------------------------ unidade de força: motor diesel, radiador, escape
bm = bmesh.new()
caixa_de(bm, (0.48, 0.40, DECK), (0.92, 0.92, DECK + 0.5))
caixa_de(bm, (0.46, 0.38, DECK + 0.5), (0.94, 0.94, DECK + 0.53))        # tampa
obj('forca', bm, 'amarelo')
bm = bmesh.new()
for k in range(11):                                                      # grade do radiador (face oeste)
    caixa_de(bm, (0.465, 0.46 + k * 0.04, DECK + 0.08), (0.48, 0.475 + k * 0.04, DECK + 0.44))
caixa_de(bm, (0.47, 0.44, DECK + 0.06), (0.48, 0.90, DECK + 0.08))
caixa_de(bm, (0.47, 0.44, DECK + 0.44), (0.48, 0.90, DECK + 0.46))
for k in range(5):                                                       # venezianas (face sul)
    caixa(bm, (0.7, 0.395, DECK + 0.12 + k * 0.06), (0.32, 0.012, 0.02), Matrix.Rotation(0.5, 3, 'X'))
obj('forca_grade', bm, 'grafite')
bm = bmesh.new()
tubo(bm, (0.82, 0.82, DECK + 0.5), (0.82, 0.82, DECK + 1.15), 0.035)    # escapamento
cil(bm, Vector((0.82, 0.82, DECK + 0.8)), 0.05, 0.25, lados=10)          # silencioso
caixa(bm, (0.82, 0.86, DECK + 1.17), (0.09, 0.06, 0.01), Matrix.Rotation(0.4, 3, 'X'))   # tampa de chuva
obj('escape', bm, 'aco')
bm = bmesh.new()                                                         # tanque hidráulico
caixa_de(bm, (0.48, -0.12, DECK), (0.88, 0.32, DECK + 0.32))
cil(bm, Vector((0.68, 0.1, DECK + 0.35)), 0.04, 0.05, lados=10)
obj('tanque', bm, 'grafite')
bm = bmesh.new()                                                         # mangueiras: força → pistões e corrente
mangueira(bm, bezier((0.5, 0.5, DECK + 0.35), (0.35, 0.5, DECK + 0.3), (0.35, YP + 0.05, DECK + 0.1), (0.3, YP, DECK + 0.06), 8), 0.013)
mangueira(bm, bezier((0.5, 0.6, DECK + 0.4), (0.0, 0.62, DECK + 0.3), (-0.3, 0.6, DECK + 0.1), (-0.3, YP, DECK + 0.06), 10), 0.013)
mangueira(bm, bezier((0.5, 0.7, DECK + 0.45), (0.0, 0.62, 1.0), (-0.3, 0.55, 1.5), (XC, YA + 0.02, Z_FIXO + 0.02), 12), 0.016)
mangueira(bm, bezier((0.5, 0.75, DECK + 0.42), (0.05, 0.66, 1.0), (-0.32, 0.58, 1.5), (XC + 0.025, YA + 0.02, Z_FIXO + 0.02), 12), 0.012)
obj('mangueiras', bm, 'borracha')

# ------------------------------------------------------------------ saída: rosca transportadora → funil → calha (sul)
F = Vector((-0.5, -0.62, 0))
bm = bmesh.new()
a, b = FURO + Vector((0.0, -0.18, 0.06)), F + Vector((0.0, 0.0, 0.95))
tubo(bm, a, b, 0.07, 12)                                                 # tubo da rosca
for t in (0.25, 0.5, 0.75):
    c = a + (b - a) * t
    tubo(bm, c - (b - a).normalized() * 0.012, c + (b - a).normalized() * 0.012, 0.085, 12)   # flanges
cil(bm, b + Vector((0, 0, 0.06)), 0.08, 0.1, lados=12)                   # motor da rosca
obj('rosca', bm, 'grafite')
bm = bmesh.new()
cil(bm, F + Vector((0, 0, 0.72)), 0.2, 0.3, lados=4, r2=0.27)            # funil (quadrado, gira 45°)
bmesh.ops.rotate(bm, verts=bm.verts, cent=F, matrix=Matrix.Rotation(PI / 4, 3, 'Z'))
for sx in (-1, 1):
    for sy in (-1, 1):
        tubo(bm, F + Vector((sx * 0.14, sy * 0.14, DECK)), F + Vector((sx * 0.14, sy * 0.14, 0.62)), 0.018)
obj('funil', bm, 'amarelo')
CALHA0, CALHA1 = F + Vector((0, -0.05, 0.56)), Vector((F.x, -1.0, 0.36))
bm = bmesh.new()
cil(bm, F + Vector((0, 0, 0.53)), 0.08, 0.1, lados=4, r2=0.13)           # bocal
mc = (CALHA1 - CALHA0).normalized()
rotc = Matrix((Vector((1, 0, 0)), mc, Vector((1, 0, 0)).cross(mc))).transposed()
meio, comp = (CALHA0 + CALHA1) / 2, (CALHA1 - CALHA0).length
caixa(bm, meio, (0.2, comp, 0.012), rotc)                                # fundo da calha
for sx in (-1, 1):
    caixa(bm, meio + rotc @ Vector((sx * 0.1, 0, 0.04)), (0.012, comp, 0.08), rotc)
obj('calha', bm, 'aco')
bm = bmesh.new()
for k in range(25):                                                      # minério no funil
    pedra(bm, F + Vector((random.uniform(-0.16, 0.16), random.uniform(-0.16, 0.16), 0.84 + random.uniform(0, 0.03))), random.uniform(0.02, 0.04))
obj('funil_minerio', bm, 'minerio')
pedras_calha = []
for k in range(6):
    bm = bmesh.new()
    pedra(bm, (0, 0, 0), random.uniform(0.025, 0.04), 0.8)
    pedras_calha.append(obj('pedra_calha', bm, 'minerio'))
bm = bmesh.new()                                                         # placa de saída (seta pintada)
caixa(bm, (F.x, -0.95, DECK + 0.002), (0.24, 0.06, 0.003))
obj('marca_saida', bm, 'listras')



# ------------------------------------------------------------------ sujeira: vazamentos de óleo, lama, escorridos
def mancha(bm, centro, r, z):
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=14, radius=r)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.35 * math.sin(a * 3 + random.random()) + 0.15 * random.random()
        v.co = Vector((centro[0] + v.co.x * f, centro[1] + v.co.y * f * random.uniform(0.6, 1.0), z))


bm = bmesh.new()
for c, r in (((0.55, 0.3), 0.12), ((0.62, 0.08), 0.08), ((-0.3, 0.27), 0.07), ((0.32, 0.25), 0.06), ((0.3, -0.5), 0.1)):
    mancha(bm, c, r, DECK + 0.0045)                                      # óleo no piso
for c, r in (((0.95, 0.5), 0.18), ((-0.95, -0.7), 0.1), ((0.88, -0.88), 0.09)):
    mancha(bm, c, r, 0.006)                                              # óleo pingado no chão
for k in range(8):                                                       # escorridos na lateral da unidade de força
    x = random.uniform(0.52, 0.9)
    caixa_de(bm, (x, 0.392, DECK + 0.02), (x + 0.008, 0.396, DECK + random.uniform(0.12, 0.3)))
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for k in range(14):                                                      # lama respingada em volta do furo e na bucha
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.25, 0.55)
    mancha(bm, (FURO.x + math.cos(a) * r, FURO.y + math.sin(a) * r), random.uniform(0.03, 0.08), 0.008)
for k in range(10):
    a = random.uniform(0, 2 * PI)
    caixa(bm, FURO + Vector((math.cos(a) * 0.212, math.sin(a) * 0.212, DECK + 0.05 - random.uniform(0, 0.03))),
          (0.025, 0.01, random.uniform(0.04, 0.08)), Matrix.Rotation(a + PI / 2, 3, 'Z'))
for k in range(6):                                                       # escorrido de lama na calha
    u = random.uniform(0.1, 0.9)
    mancha(bm, (CALHA0 + (CALHA1 - CALHA0) * u).xy + Vector((random.uniform(-0.06, 0.06), 0)), 0.03, 0)
obj('lama', bm, 'lama')
lama = sc.objects['lama']
for v in lama.data.vertices:                                             # a lama da calha acompanha a inclinação
    if v.co.z == 0:
        u = (v.co.y - CALHA0.y) / (CALHA1.y - CALHA0.y)
        v.co.z = CALHA0.z + (CALHA1.z - CALHA0.z) * u + 0.008

# ------------------------------------------------------------------ canos rígidos com flanges (força → tanque → torre)
bm, bf = bmesh.new(), bmesh.new()
rota = [Vector(p) for p in ((0.48, 0.2, DECK + 0.12), (0.3, 0.2, DECK + 0.12), (0.3, 0.2, DECK + 0.05),
                            (0.3, 0.6, DECK + 0.05), (0.26, 0.6, DECK + 0.05))]
rota2 = [Vector(p) for p in ((0.48, 0.0, DECK + 0.2), (0.4, 0.0, DECK + 0.2), (0.4, 0.0, 0.9), (0.24, 0.0, 0.9),
                             (0.24, YF, 0.9))]
for r in (rota, rota2):
    for a, b in zip(r, r[1:]):
        tubo(bm, a, b, 0.018, 10)
        u = (b - a).normalized()
        for c in (a + u * 0.03, b - u * 0.03):
            tubo(bf, c - u * 0.008, c + u * 0.008, 0.028, 10)            # flanges
    for c in r[1:-1]:
        cil(bf, c, 0.024, 0.04, lados=10)                                # cotovelos
for z in (0.55, 0.75):                                                   # abraçadeiras na torre
    caixa(bf, (0.22, 0.0, z + 0.15), (0.05, 0.04, 0.03))
cil(bf, Vector((0.4, 0.0, 0.6)), 0.04, 0.09, lados=10)                   # válvula
tubo(bf, (0.4, 0.0, 0.6), (0.4, -0.08, 0.6), 0.01, 6)
cil(bf, Vector((0.4, -0.085, 0.6)), 0.035, 0.01, Vector((0, 1, 0)), lados=10)   # volante da válvula
obj('canos', bm, 'aco')
obj('canos_flanges', bf, 'grafite')

# ------------------------------------------------------------------ fumaça do escape e poeira do furo
SAIDA = Vector((0.82, 0.82, DECK + 1.17))
fumacas = []
for k in range(6):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    fumacas.append(obj('fumaca', bm, 'fumaca'))
poeiras = []
for k in range(5):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    poeiras.append(obj('poeira', bm, 'poeira'))

# ------------------------------------------------------------------ animação
def zc_de(t):
    return (Z_ALTO + Z_BAIXO) / 2 + (Z_ALTO - Z_BAIXO) / 2 * math.cos(2 * PI * t / (QUADROS / FPS))


for q in range(1, QUADROS + 1):
    t = (q - 1) / FPS
    fr = (q - 1) / QUADROS
    zc = zc_de(t)
    cabeca.location = (C.x, C.y, zc)
    cabeca.keyframe_insert('location', frame=q)
    trado.location = (C.x, C.y, zc - 0.21)
    trado.rotation_euler = (0, 0, -2 * PI * VOLTAS * fr)
    trado.keyframe_insert('location', frame=q)
    trado.keyframe_insert('rotation_euler', frame=q)
    for h in hastes:
        h.location.z = zc - 0.11
        h.keyframe_insert('location', frame=q)
    for k, o in enumerate(elos):
        p, d = ponto_corrente((k + 0.5) * COMP_CORR / N_ELOS, zc - 0.02)
        o.location = p
        o.rotation_quaternion = d.to_track_quat('Y', 'X')
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)
    for k, o in enumerate(pedras_calha):                                  # minério escorrega pela calha
        u = (k / len(pedras_calha) + fr * 4) % 1.0
        o.location = CALHA0 + (CALHA1 - CALHA0) * u + Vector((0.05 * math.sin(k * 2.1), 0, 0.03))
        o.rotation_euler = (u * 6, u * 3, k)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)
    for k, o in enumerate(fumacas):                                       # baforadas sobem, crescem e derivam com o vento
        u = (k / len(fumacas) + fr * 2) % 1.0
        o.location = SAIDA + Vector((0.35 * u * u, 0.15 * u, 1.3 * u + 0.05))
        o.scale = [0.05 + 0.32 * u] * 3
        o.rotation_euler = (k, u * 2, k * 0.5)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
        o.keyframe_insert('rotation_euler', frame=q)
    for k, o in enumerate(poeiras):                                       # poeira girando em volta do trado
        u = (k / len(poeiras) + fr * 2) % 1.0
        a = 2 * PI * (k / len(poeiras) + fr * 2)
        o.location = FURO + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.06 + 0.5 * u))
        o.scale = [0.12 + 0.2 * u] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
for o in sc.objects:
    if o.animation_data and o.animation_data.action:
        for fc in getattr(o.animation_data.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (12, 12, 1.0))
obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), 0, math.radians(-35))
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
    for d in pr.devices:
        d.use = True
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
    sc.frame_set(30)
    for i, (ang, alt, lente) in enumerate(((235, 2.2, 38), (320, 1.6, 38), (60, 2.6, 38), (160, 2.0, 38))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 5.2, math.sin(a) * 5.2, alt)), ALVO, lente)
        sc.render.filepath = os.path.join(AQUI, 'broca_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
    mirar((1.1, -1.9, 1.3), (0.0, -0.2, 0.55), 35)                       # de perto: furo, trado, calha
    sc.render.filepath = os.path.join(AQUI, 'broca_perto.png')
    bpy.ops.render.render(write_still=True)
if modo == 'video':
    sc.cycles.samples = 80
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.35
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(240)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 5.4, math.sin(a) * 5.4, 1.6)), (0, 0, 1.05), 36)
    os.makedirs(os.path.join(AQUI, 'quadros_broca'), exist_ok=True)
    sc.render.filepath = os.path.join(AQUI, 'quadros_broca', 'q')
    bpy.ops.render.render(animation=True)
print('BROCA ok')
