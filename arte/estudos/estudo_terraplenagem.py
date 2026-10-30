"""Estudo isolado (fora do jogo): TERRAPLENAGEM v2, 3×3 tiles, sem portas de item. Instalação fixa da IA, cravada no
chão — nada de veículo. Quatro pernas hidráulicas (cilindros grandes) cravadas como estacas nos cantos seguram um
quadro de aço rebitado que "respira". Do cubo central pende o núcleo: disco-anel que gira e pulsa, com cristal
apontado para a terra. Embaixo o terreno se reorganiza com ordem demais: terraços em degraus perfeitos, terra virando
placas, blocos que sobem da cava girando, se alinham em grade no ar e voltam a assentar, pingando lama. Em cima, a
rocha suspensa ("bloco") sendo fatiada em cubos por linhas de luz âmbar: metade pedra bruta, metade voxels que se
soltam. Pilão de compactação ("cabecote") com dois cilindros (pistao0/pistao1) socando a borda nivelada. Unidade
hidráulica no oeste com mangueiras até cada cilindro; cabos-raiz descendo pelas pernas e entrando na terra; anel de
sensores de topografia ("antena") girando num mastro do quadro.
Uso: blender -b --python estudo_terraplenagem.py -- foto [0|1|2|3|perto|rocha]"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(31)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def tubo_curvo(bm, pts, r, lados=14, tampas=True):
    """Tubo contínuo ao longo de uma polilinha, com transporte paralelo (sem torção)."""
    pts = [Vector(p) for p in pts]
    aneis, u = [], None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if u is None:
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            u = t.cross(ref).normalized()
        else:
            u = (u - t * u.dot(t)).normalized()
        v = t.cross(u).normalized()
        aneis.append([bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r)
                      for a in (k * 2 * PI / lados for k in range(lados))])
    for A, B in zip(aneis, aneis[1:]):
        for k in range(lados):
            bm.faces.new((A[k], A[(k + 1) % lados], B[(k + 1) % lados], B[k]))
    if tampas:
        bm.faces.new(list(reversed(aneis[0])))
        bm.faces.new(aneis[-1])


def polilinha(via, passo=0.05):
    pts = []
    for p, q in zip(via, via[1:]):
        p, q = Vector(p), Vector(q)
        n = max(2, int((q - p).length / passo))
        pts += [p + (q - p) * (k / n) for k in range(n)]
    pts.append(Vector(via[-1]))
    return pts


def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.25, 0.06, 0.7, 1)
    b.inputs['Roughness'].default_value = 0.15
    b.inputs['Transmission Weight'].default_value = 0.4
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.45, 0.12, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 1.5
    return m


def terra_mat(nome, c1, c2, rough, bump=0.4, escala=3.0, esticar_z=1.0):
    """Terra: dois tons por ruído, relevo granulado. esticar_z < 1 alonga o ruído em z (escorrido de lama)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, esticar_z)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 10.0, 'Roughness': 0.65})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], fino.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*c1, 1)
    mix.inputs[7].default_value = (*c2, 1)
    nt.links.new(mr.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    bp = no(nt, 'ShaderNodeBump', **{'Strength': bump, 'Distance': 0.02})
    nt.links.new(fino.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def placa_mat():
    """Terra compactada em placas: terra lisa demais, com juntas retas em grade (ordem que não é natural)."""
    m = terra_mat('Placa', (0.2, 0.15, 0.1), (0.16, 0.12, 0.085), 0.8, 0.15, 2.0)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    mix_cor = next(n for n in nt.nodes if n.type == 'MIX')
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    tj = no(nt, 'ShaderNodeTexBrick', **{'Scale': 1.0, 'Mortar Size': 0.004, 'Brick Width': 0.225, 'Row Height': 0.225,
                                         })
    tj.offset = 0.0
    tj.inputs['Color1'].default_value = (1, 1, 1, 1)
    tj.inputs['Color2'].default_value = (0.93, 0.93, 0.93, 1)
    tj.inputs['Mortar'].default_value = (0.25, 0.22, 0.2, 1)
    nt.links.new(tc.outputs['Object'], tj.inputs['Vector'])
    mul = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    mul.inputs[0].default_value = 1.0
    nt.links.new(mix_cor.outputs[2], mul.inputs[6])
    nt.links.new(tj.outputs['Color'], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs['Base Color'])
    return m


def corte_mat(nome, P, w, forca, minimo):
    """Rocha com linhas de luz âmbar na grade de corte (passo P no espaço do objeto). minimo=1: grade sobre toda a
    superfície (linhas finas); minimo=2: só as arestas dos cubos já cortados."""
    m = terra_mat(nome, (0.25, 0.21, 0.17), (0.14, 0.12, 0.1), 0.85, 0.5, 4.0)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    soma = None
    for eixo in ('X', 'Y', 'Z'):
        d = no(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = P
        nt.links.new(sep.outputs[eixo], d.inputs[0])
        fr = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs[0], fr.inputs[0])
        s5 = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
        s5.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], s5.inputs[0])
        ab = no(nt, 'ShaderNodeMath', operation='ABSOLUTE')
        nt.links.new(s5.outputs[0], ab.inputs[0])
        perto = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
        perto.inputs[1].default_value = w / P
        nt.links.new(ab.outputs[0], perto.inputs[0])
        if soma is None:
            soma = perto
        else:
            ad = no(nt, 'ShaderNodeMath', operation='ADD')
            nt.links.new(soma.outputs[0], ad.inputs[0])
            nt.links.new(perto.outputs[0], ad.inputs[1])
            soma = ad
    linha = no(nt, 'ShaderNodeMath', operation='GREATER_THAN')
    linha.inputs[1].default_value = minimo - 0.5
    nt.links.new(soma.outputs[0], linha.inputs[0])
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    f.inputs[1].default_value = forca
    nt.links.new(linha.outputs[0], f.inputs[0])
    nt.links.new(f.outputs[0], b.inputs['Emission Strength'])
    b.inputs['Emission Color'].default_value = (1.0, 0.5, 0.08, 1)
    return m


VIOLETA = (0.66, 0.42, 1.0)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.95, sujeira=0.9),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.9, sujeira=0.8, escovado=True),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=1.0),
    'ferro': mats.material('Ferro', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.75, pintura=False, sujeira=0.4, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.04, 0.04, 0.045), 0, 0.6, pintura=False, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': terra_mat('Lama', (0.075, 0.05, 0.032), (0.13, 0.09, 0.055), 0.45, 0.25, 6.0),
    'torrao': terra_mat('Torrão', (0.17, 0.12, 0.075), (0.11, 0.075, 0.05), 0.92, 0.6, 5.0),
    'chao': terra_mat('Chão', (0.25, 0.19, 0.13), (0.17, 0.125, 0.085), 0.95, 0.5, 1.2),
    'revirado': terra_mat('Revirado', (0.13, 0.09, 0.06), (0.19, 0.135, 0.09), 0.9, 0.7, 4.0),
    'bloco_terra': terra_mat('Bloco de terra', (0.2, 0.145, 0.095), (0.07, 0.05, 0.035), 0.7, 0.4, 7.0, 0.15),
    'fundo': mats.material('Fundo da cava', (0.02, 0.016, 0.012), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'placa': placa_mat(),
    'rocha': corte_mat('Rocha', 0.13, 0.0012, 0.7, 1),
    'voxel': corte_mat('Voxel', 0.13, 0.005, 5.0, 2),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'cristal': cristal_mat(),
    'emissor': emissivo('Emissor', (0.55, 0.25, 1.0), 6.0, (0.12, 0.04, 0.3)),
    'costura': emissivo('Costura de corte', (1.0, 0.5, 0.08), 25.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', (1.0, 0.5, 0.05), 10.0),
    'poeira': base3d.volume_mat('Poeira', (0.45, 0.36, 0.27), 4.0, -0.3, 1.2),
    'poeira_rocha': base3d.volume_mat('Poeira da rocha', (0.45, 0.36, 0.27), 4.0, 1.9, 3.2),
    'poeira_chao': base3d.volume_mat('Poeira do chão', (0.5, 0.4, 0.3), 9.0, 0.0, 1.0),
})


# ------------------------------------------------------------------ cilindros hidráulicos
def cilindro(nome, r_c, l_c, r_h, l_h, cor='amarelo'):
    """Camisa (origem no pino de trás, ao longo de +z) e haste (origem no olhal, ao longo de +z, entra na camisa)."""
    cam = bpy.data.objects.new(nome + '_camisa', None)
    sc.collection.objects.link(cam)
    cam.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.04 + l_c / 2)), r_c, l_c, lados=24)
    suavizar(obj(nome + '_tubo', bm, cor, cam))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.04 + l_c - 0.03)), r_c + 0.016, 0.07, lados=24)        # cabeçote (flange da gaxeta)
    cil(bm, Vector((0, 0, 0.07)), r_c + 0.014, 0.07, lados=24)                      # fundo
    cil(bm, Vector((0, 0, 0)), 0.035, r_c * 2 + 0.04, Vector((1, 0, 0)), lados=12)  # pino de trás
    caixa(bm, Vector((0, 0, 0.025)), (0.06, r_c * 1.5, 0.07))
    for z in (0.13, l_c - 0.06):                                                    # portas de óleo
        caixa(bm, Vector((0, -r_c - 0.015, z + 0.04)), (0.05, 0.04, 0.05))
    obj(nome + '_cabecotes', bm, 'ferro', cam)
    bm = bmesh.new()
    for z in (0.04 + l_c - 0.03, 0.07):                                             # parafusos dos flanges
        for k in range(10):
            a = k * 2 * PI / 10
            cil(bm, Vector((math.cos(a) * (r_c + 0.016), math.sin(a) * (r_c + 0.016), z)), 0.008, 0.08, lados=6)
    obj(nome + '_parafusos', bm, 'aco', cam)
    hst = bpy.data.objects.new(nome + '_haste', None)
    sc.collection.objects.link(hst)
    hst.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, l_h / 2)), r_h, l_h, lados=18)
    suavizar(obj(nome + '_cromo', bm, 'cromo', hst))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.035, r_h * 2 + 0.05, Vector((1, 0, 0)), lados=12)
    caixa(bm, Vector((0, 0, 0.035)), (0.06, r_h * 2 + 0.03, 0.08))
    obj(nome + '_olhal', bm, 'ferro', hst)
    return cam, hst


def pos_cilindro(cam, hst, a, b, q):
    d = b - a
    cam.location = a
    cam.rotation_quaternion = d.to_track_quat('Z', 'Y')
    hst.location = b
    hst.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    for o in (cam, hst):
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)


# ------------------------------------------------------------------ chão com a cava em terraços
CAVA = [(0.95, -0.12), (0.7, -0.24), (0.45, -0.36)]      # (meia-largura, altura do piso) de cada degrau
FUNDO = -0.6
bm = bmesh.new()                                           # chão em volta (com o furo da cava)
G = 40.0
h0 = CAVA[0][0]
for a, b in (((-G, -G), (G, -h0)), ((-G, h0), (G, G)), ((-G, -h0), (-h0, h0)), ((h0, -h0), (G, h0))):
    caixa_de(bm, (a[0], a[1], -1.0), (b[0], b[1], 0.0))
obj('chao', bm, 'chao')
bm = bmesh.new()                                           # degraus: anéis quadrados de terra compactada
for i, (w, z) in enumerate(CAVA):
    wi = CAVA[i + 1][0] if i + 1 < len(CAVA) else None
    if wi is None:
        continue
    for a, b in (((-w, -w), (w, -wi)), ((-w, wi), (w, w)), ((-w, -wi), (-wi, wi)), ((wi, -wi), (w, wi))):
        caixa_de(bm, (a[0], a[1], FUNDO), (b[0], b[1], z))
obj('terracos', bm, 'placa')
bm = bmesh.new()                                           # borda da cava: placas niveladas (moldura de ordem)
for a, b in (((-1.12, -1.12), (1.12, -0.95)), ((-1.12, 0.95), (1.12, 1.12)), ((-1.12, -0.95), (-0.95, 0.95)), ((0.95, -0.95), (1.12, 0.95))):
    caixa_de(bm, (a[0], a[1], -0.02), (b[0], b[1], 0.004))
obj('borda_placas', bm, 'placa')
bm = bmesh.new()
caixa_de(bm, (-0.45, -0.45, FUNDO - 0.02), (0.45, 0.45, -0.58))
obj('fundo_cava', bm, 'fundo')

# blocos de terra (4×4) que saem do fundo da cava
WB = CAVA[2][0]
PASSO_B = 2 * WB / 4
LADO_B = PASSO_B - 0.03
Z_REPOUSO = CAVA[2][1] - LADO_B / 2                         # topo rente ao piso do fundo
blocos = []
for i in range(4):
    for j in range(4):
        cel = Vector((-WB + PASSO_B * (i + 0.5), -WB + PASSO_B * (j + 0.5), Z_REPOUSO))
        o = bpy.data.objects.new('bloco_terra', None)
        sc.collection.objects.link(o)
        o.rotation_mode = 'QUATERNION'
        bm = bmesh.new()
        caixa(bm, (0, 0, 0), (LADO_B, LADO_B, LADO_B))
        obj('bloco_terra_cubo', bm, 'bloco_terra', o)
        bm = bmesh.new()                                    # placa lisa no topo (a face que vira piso)
        caixa(bm, (0, 0, LADO_B / 2 + 0.002), (LADO_B - 0.004, LADO_B - 0.004, 0.004))
        obj('bloco_terra_placa', bm, 'placa', o)
        bm = bmesh.new()                                    # lama escorrendo pelas faces
        for k in range(5):
            sx, sy = random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            t = random.uniform(-0.06, 0.06)
            p = Vector((sx * (LADO_B / 2 + 0.003) + (t if sx == 0 else 0), sy * (LADO_B / 2 + 0.003) + (t if sy == 0 else 0), 0))
            h = random.uniform(0.06, 0.14)
            caixa(bm, p + Vector((0, 0, -LADO_B / 2 + h / 2 - 0.01)), (0.006 if sx else 0.025, 0.006 if sy else 0.025, h))
        for k in range(3):
            pedra(bm, Vector((random.uniform(-0.07, 0.07), random.uniform(-0.07, 0.07), -LADO_B / 2 - 0.01)), 0.025, 0.5)
        obj('bloco_terra_lama', bm, 'lama', o)
        eixo = random.choice((Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))))
        blocos.append((o, cel, Vector((cel.x * 1.75, cel.y * 1.75, 0.62 + 0.2 * ((i + j) % 2))), random.uniform(0, 1),
                       eixo, random.choice((1, 2)) * random.choice((1, -1))))
gotas = []
for k in range(16):                                         # gotas de lama caindo dos blocos no ar
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.012)
    for v in bm.verts:
        v.co.z *= 1.8
    gotas.append(obj('gota', bm, 'lama'))

# ------------------------------------------------------------------ pernas hidráulicas cravadas (cantos)
PE = 1.25
Z_QUADRO = 1.95
QW = 0.8                     # meia-largura do quadro
PES = [Vector((sx * PE, sy * PE, 0.32)) for sx in (-1, 1) for sy in (-1, 1)]
SUP = [Vector((sx * (QW - 0.05), sy * (QW - 0.05), Z_QUADRO - 0.12)) for sx in (-1, 1) for sy in (-1, 1)]
for p in PES:
    c = Vector((p.x, p.y, 0))
    s = Vector((math.copysign(1, p.x), math.copysign(1, p.y), 0))
    bm = bmesh.new()                                        # estaca cravada: tubo grosso que entra na terra
    cil(bm, c + Vector((0, 0, 0.05)), 0.16, 0.3, lados=24)
    cil(bm, c + Vector((0, 0, 0.2)), 0.2, 0.04, lados=24)   # flange
    suavizar(obj('estaca', bm, 'casco'))
    bm = bmesh.new()                                        # garfo do pino da perna
    d = (Vector((0, 0, 0)) - c).normalized()
    for k in (-1, 1):
        lado = Vector((-d.y, d.x, 0)) * k * 0.1
        caixa(bm, c + lado + Vector((0, 0, 0.28)), (0.03, 0.03, 0.16), Matrix.Rotation(math.atan2(d.y, d.x), 3, 'Z'))
        caixa(bm, c + lado + Vector((0, 0, 0.28)), (0.12, 0.03, 0.16), Matrix.Rotation(math.atan2(d.y, d.x), 3, 'Z'))
    cil(bm, p, 0.03, 0.26, Vector((-d.y, d.x, 0)), lados=10)
    for k in range(4):                                      # mãos-francesas do flange
        a = k * PI / 2 + PI / 4
        r = Vector((math.cos(a), math.sin(a), 0))
        viga(bm, c + r * 0.19 + Vector((0, 0, 0.22)), c + r * 0.13 + Vector((0, 0, 0.34)), 0.025)
    obj('garfo_perna', bm, 'ferro')
    bm = bmesh.new()
    for k in range(12):
        a = k * 2 * PI / 12
        cil(bm, c + Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.225)), 0.011, 0.02, lados=6)
    obj('estaca_rebites', bm, 'aco')
    bm = bmesh.new()                                        # terra levantada e rachada em volta da estaca
    for k in range(16):
        a = k * 2 * PI / 16 + random.uniform(-0.1, 0.1)
        pedra(bm, c + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.22, 0.3), random.uniform(0.04, 0.08), 0.45)
    obj('estaca_terra', bm, 'revirado')
    bm = bmesh.new()
    for k in range(7):                                      # rachaduras radiais
        a = random.uniform(0, 2 * PI)
        r = Vector((math.cos(a), math.sin(a), 0))
        L = random.uniform(0.25, 0.5)
        caixa(bm, c + r * (0.28 + L / 2) + Vector((0, 0, 0.001)), (L, 0.012, 0.004), Matrix.Rotation(a, 3, 'Z'))
    obj('estaca_rachas', bm, 'fundo')
pernas = [cilindro('perna%d' % i, 0.11, 0.95, 0.055, 1.08) for i in range(4)]

# ------------------------------------------------------------------ quadro de aço (respira) com cubo central
quadro = bpy.data.objects.new('quadro', None)
sc.collection.objects.link(quadro)
quadro.location = (0, 0, Z_QUADRO)
bm = bmesh.new()
for a, b in (((-QW, -QW), (QW, -QW + 0.14)), ((-QW, QW - 0.14), (QW, QW)), ((-QW, -QW + 0.14), (-QW + 0.14, QW - 0.14)),
             ((QW - 0.14, -QW + 0.14), (QW, QW - 0.14))):
    caixa_de(bm, (a[0], a[1], -0.08), (b[0], b[1], 0.08))
for sx in (-1, 1):                                          # vigas em X até o cubo
    for sy in (-1, 1):
        viga(bm, Vector((sx * (QW - 0.1), sy * (QW - 0.1), 0)), Vector((sx * 0.15, sy * 0.15, 0)), 0.1)
obj('quadro_vigas', bm, 'amarelo', quadro)
bm = bmesh.new()
for sx in (-1, 1):                                          # suportes das pernas nos cantos
    for sy in (-1, 1):
        caixa(bm, Vector((sx * (QW - 0.05), sy * (QW - 0.05), -0.12)), (0.2, 0.2, 0.08))
        for k in (-1, 1):
            caixa(bm, Vector((sx * (QW - 0.05) + k * 0.075, sy * (QW - 0.05), -0.17)), (0.025, 0.12, 0.1))
obj('quadro_suportes', bm, 'ferro', quadro)
bm = bmesh.new()                                            # rebites nas vigas
for lado in range(4):
    for k in range(14):
        t = -QW + 0.1 + k * (2 * QW - 0.2) / 13
        for off in (0.035, 0.105):
            if lado == 0:
                p = Vector((t, -QW + off, 0.082))
            elif lado == 1:
                p = Vector((t, QW - off, 0.082))
            elif lado == 2:
                p = Vector((-QW + off, t, 0.082))
            else:
                p = Vector((QW - off, t, 0.082))
            cil(bm, p, 0.01, 0.01, lados=6)
obj('quadro_rebites', bm, 'aco', quadro)
bm = bmesh.new()
for k in range(26):
    lado = random.randrange(4)
    t = random.uniform(-QW + 0.15, QW - 0.15)
    h = random.uniform(0.04, 0.14)
    w = random.uniform(0.01, 0.03)
    if lado == 0:
        caixa(bm, Vector((t, -QW - 0.002, 0.08 - h / 2)), (w, 0.003, h))
    elif lado == 1:
        caixa(bm, Vector((t, QW + 0.002, 0.08 - h / 2)), (w, 0.003, h))
    elif lado == 2:
        caixa(bm, Vector((-QW - 0.002, t, 0.08 - h / 2)), (0.003, w, h))
    else:
        caixa(bm, Vector((QW + 0.002, t, 0.08 - h / 2)), (0.003, w, h))
obj('quadro_escorridos', bm, 'oleo', quadro)
bm = bmesh.new()                                            # cubo central (mancal do núcleo)
cil(bm, Vector((0, 0, 0)), 0.2, 0.2, lados=24)
cil(bm, Vector((0, 0, -0.13)), 0.13, 0.08, lados=20)
suavizar(obj('cubo', bm, 'casco', quadro))
bm = bmesh.new()
for z in (0.1, -0.1):
    cil(bm, Vector((0, 0, z)), 0.225, 0.03, lados=24)
obj('cubo_flanges', bm, 'ferro', quadro)
bm = bmesh.new()                                            # emissor do topo: segura a rocha
cil(bm, Vector((0, 0, 0.14)), 0.16, 0.04, lados=24, r2=0.1)
obj('emissor_topo', bm, 'grafite', quadro)
bm = bmesh.new()
toro(bm, Vector((0, 0, 0.17)), 0.12, 0.014, 32, 8)
obj('emissor_topo_anel', bm, 'emissor', quadro)
bm = bmesh.new()                                            # óleo escorrendo do cubo
for k in range(5):
    a = random.uniform(0, 2 * PI)
    caixa(bm, Vector((math.cos(a) * 0.202, math.sin(a) * 0.202, -0.02)), (0.004, 0.025, random.uniform(0.08, 0.16)),
          Matrix.Rotation(a, 3, 'Z'))
obj('cubo_oleo', bm, 'oleo', quadro)

# núcleo: eixo, disco-anel girando, cristal
Z_NUCLEO = -0.55             # relativo ao quadro (z ≈ 1,4)
bm = bmesh.new()
cil(bm, Vector((0, 0, (Z_NUCLEO - 0.17) / 2)), 0.05, -Z_NUCLEO - 0.17 + 0.02, lados=16)
suavizar(obj('eixo', bm, 'cromo', quadro))
nucleo = bpy.data.objects.new('nucleo', None)
sc.collection.objects.link(nucleo)
nucleo.parent = quadro
nucleo.location = (0, 0, Z_NUCLEO)
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), 0.52, 0.055, 64, 14)
suavizar(obj('nucleo_anel', bm, 'casco', nucleo))
bm = bmesh.new()
for k in range(6):                                          # raios
    a = k * PI / 3
    viga(bm, Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, 0)), Vector((math.cos(a) * 0.48, math.sin(a) * 0.48, 0)), 0.04)
cil(bm, Vector((0, 0, 0.02)), 0.14, 0.1, lados=20)
obj('nucleo_raios', bm, 'amarelo', nucleo)
bm = bmesh.new()
for k in range(8):                                          # bobinas de cobre no anel
    a = k * PI / 4 + PI / 8
    toro(bm, Vector((math.cos(a) * 0.52, math.sin(a) * 0.52, 0)), 0.07, 0.016, 20, 6,
         Vector((-math.sin(a), math.cos(a), 0)).to_track_quat('Z', 'Y').to_matrix())
obj('nucleo_bobinas', bm, 'cobre', nucleo)
bm = bmesh.new()
for k in range(8):                                          # emissores apontando para baixo
    a = k * PI / 4
    cil(bm, Vector((math.cos(a) * 0.52, math.sin(a) * 0.52, -0.07)), 0.03, 0.03, lados=12)
obj('nucleo_emissores', bm, 'emissor', nucleo)
bm = bmesh.new()                                            # cristal: prisma com pontas (para a terra e para cima)
cil(bm, Vector((0, 0, -0.08)), 0.07, 0.2, lados=6)
cil(bm, Vector((0, 0, -0.27)), 0.07, 0.18, lados=6, r2=0.0)
for v in bm.verts:
    v.co.z -= 0.0
obj('cristal', bm, 'cristal', nucleo)
luz_n = bpy.data.lights.new('Núcleo', 'POINT')
luz_n.color = VIOLETA
luz_n.shadow_soft_size = 0.2
ln = bpy.data.objects.new('Núcleo', luz_n)
sc.collection.objects.link(ln)
ln.parent = quadro
ln.location = (0, 0, Z_NUCLEO - 0.45)

# ------------------------------------------------------------------ rocha sendo fatiada em cubos (em cima do cubo)
Z_ROCHA = 0.62               # relativo ao quadro (z ≈ 2,57)
P = 0.13
X_CORTE = 0.02
rocha = bpy.data.objects.new('bloco', None)
sc.collection.objects.link(rocha)
rocha.parent = quadro
rocha.location = (0, 0, Z_ROCHA)
rocha.rotation_mode = 'XYZ'
sem = Vector((3.1, 7.7, 1.3))
PLANOS = [(Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.6, 1))).normalized(),
           random.uniform(0.28, 0.34)) for _ in range(8)]


def raio_rocha(p):
    """Superfície da rocha bruta: True se o ponto (local) está dentro."""
    n = p.normalized() if p.length > 1e-6 else Vector((0, 0, 1))
    q = Vector((p.x / 1.1, p.y, p.z / 0.85))
    r = 0.38 * (1 + (0.05 * noise.noise(n * 1.8 + sem) + 0.02 * noise.noise(n * 5 + sem)) / 0.38)
    if q.length > r:
        return False
    return all(q.dot(pn) <= dist for pn, dist in PLANOS)


bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=4, radius=0.38)
cortados = []
for v in bm.verts:
    n = v.co.normalized()
    c = v.co * (1 + (0.05 * noise.noise(n * 1.8 + sem) + 0.02 * noise.noise(n * 5 + sem) + 0.008 * noise.noise(n * 14 + sem)) / 0.38)
    for pn, dist in PLANOS:
        e = c.dot(pn) - dist
        if e > 0:
            c -= pn * e
    c = Vector((c.x * 1.1, c.y, c.z * 0.85))
    if c.x > X_CORTE:                                        # face de corte plana: o lado +x virou cubos
        c.x = X_CORTE
        cortados.append(Vector((c.y, c.z)))
    v.co = c
o_r = obj('bloco_rocha', bm, 'rocha', rocha)
for pg in o_r.data.polygons:
    pg.use_smooth = False


def casco_2d(pts):
    pts = sorted(set((round(p.x, 4), round(p.y, 4)) for p in pts))
    if len(pts) < 3:
        return pts

    def cruz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    baixo, cima = [], []
    for p in pts:
        while len(baixo) >= 2 and cruz(baixo[-2], baixo[-1], p) <= 0:
            baixo.pop()
        baixo.append(p)
    for p in reversed(pts):
        while len(cima) >= 2 and cruz(cima[-2], cima[-1], p) <= 0:
            cima.pop()
        cima.append(p)
    return baixo[:-1] + cima[:-1]


bm = bmesh.new()                                            # costura de luz na face de corte
contorno = casco_2d(cortados)
cen = Vector((sum(p[0] for p in contorno) / len(contorno), sum(p[1] for p in contorno) / len(contorno)))
vs = [bm.verts.new(Vector((X_CORTE + 0.004, cen.x + (p[0] - cen.x) * 0.97, cen.y + (p[1] - cen.y) * 0.97))) for p in contorno]
bm.faces.new(vs)
obj('costura_corte', bm, 'costura', rocha)
luz_corte = bpy.data.lights.new('Corte', 'POINT')
luz_corte.color = (1.0, 0.5, 0.1)
luz_corte.shadow_soft_size = 0.1
lco = bpy.data.objects.new('Corte', luz_corte)
sc.collection.objects.link(lco)
lco.parent = rocha
lco.location = (X_CORTE + 0.15, 0, 0)

# voxels: cubos cortados do lado +x, ainda em grade, afastando-se em camadas
camadas = {}
for i in range(0, 4):
    for j in range(-3, 4):
        for k in range(-3, 4):
            c = Vector((X_CORTE + P * (i + 0.5), P * j, P * k))
            if raio_rocha(Vector((c.x, c.y, c.z))):
                camadas.setdefault(i, []).append(c)
voxels = []
for i, cs in sorted(camadas.items()):
    pai = bpy.data.objects.new('voxels', None)
    sc.collection.objects.link(pai)
    pai.parent = rocha
    bm = bmesh.new()
    for c in cs:
        caixa(bm, c, (P - 0.014, P - 0.014, P - 0.014))
    obj('voxels_camada', bm, 'voxel', pai)
    voxels.append((pai, i))
soltos = []                                                 # cubos já soltos, flutuando em grade mais longe
for k, (y, z) in enumerate(((-1, 1), (1, 0), (0, -1), (1, 2), (-1, -1))):
    o = bpy.data.objects.new('cubo_solto', None)
    sc.collection.objects.link(o)
    o.parent = rocha
    o.rotation_mode = 'XYZ'
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (P - 0.014, P - 0.014, P - 0.014))
    obj('cubo_solto_pedra', bm, 'voxel', o)
    soltos.append((o, Vector((0, y * P * 1.25, z * P * 1.25)), k))
poeira_r = []
for k in range(5):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    poeira_r.append(obj('poeira_rocha', bm, 'poeira_rocha'))

# ------------------------------------------------------------------ pilão de compactação (leste)
XP = 1.27
bm = bmesh.new()                                            # braço em balanço do quadro até o pilão
for sy in (-1, 1):
    caixa_de(bm, (QW, sy * 0.2 - 0.05, -0.07), (XP + 0.12, sy * 0.2 + 0.05, 0.07))
    viga(bm, Vector((XP, sy * 0.2, -0.06)), Vector((QW - 0.05, sy * 0.45, -0.07)), 0.05)
caixa_de(bm, (XP - 0.12, -0.26, 0.07), (XP + 0.12, 0.26, 0.12))
obj('braco_pilao', bm, 'amarelo', quadro)
bm = bmesh.new()
for sy in (-1, 1):
    for k in range(6):
        cil(bm, Vector((QW + 0.04 + k * 0.08, sy * 0.2, 0.072)), 0.009, 0.01, lados=6)
obj('braco_rebites', bm, 'aco', quadro)
pilao = bpy.data.objects.new('cabecote', None)
sc.collection.objects.link(pilao)
pilao.location = (XP, 0, 0)
bm = bmesh.new()
caixa_de(bm, (-0.2, -0.3, 0.08), (0.2, 0.3, 0.34))                  # massa
caixa_de(bm, (-0.06, -0.06, 0.34), (0.06, 0.06, 0.4))
obj('pilao_massa', bm, 'amarelo', pilao)
bm = bmesh.new()
caixa_de(bm, (-0.205, -0.305, 0.14), (0.205, 0.305, 0.24))
obj('pilao_listras', bm, 'listras', pilao)
bm = bmesh.new()
caixa_de(bm, (-0.22, -0.32, 0.0), (0.22, 0.32, 0.08))                # sapata
for sy in (-1, 1):                                                   # orelhas das hastes
    for dx in (-0.05, 0.05):
        caixa_de(bm, (dx - 0.012, sy * 0.15 - 0.04, 0.34), (dx + 0.012, sy * 0.15 + 0.04, 0.44))
    cil(bm, Vector((0, sy * 0.15, 0.41)), 0.02, 0.13, Vector((1, 0, 0)), lados=10)
obj('pilao_sapata', bm, 'ferro', pilao)
bm = bmesh.new()
for k in range(16):
    pedra(bm, Vector((random.uniform(-0.21, 0.21), random.uniform(-0.31, 0.31), random.uniform(0.0, 0.06))), random.uniform(0.02, 0.04), 0.5)
obj('pilao_lama', bm, 'lama', pilao)
cil_pilao = [cilindro('pistao%d' % i, 0.07, 0.62, 0.035, 0.95, 'grafite') for i in range(2)]
bm = bmesh.new()                                            # piso socado embaixo do pilão: placa lisa + borda revirada
caixa_de(bm, (XP - 0.28, -0.4, -0.01), (XP + 0.2, 0.4, 0.003))
obj('piso_socado', bm, 'placa')
bm = bmesh.new()
for k in range(20):
    a = random.uniform(-PI / 2, PI / 2)
    pedra(bm, Vector((XP + 0.22 + random.uniform(0, 0.08), random.uniform(-0.45, 0.45), 0.0)), random.uniform(0.02, 0.05), 0.4)
obj('piso_socado_borda', bm, 'revirado')

# ------------------------------------------------------------------ anel de sensores de topografia (mastro no canto NO)
MA = Vector((-QW + 0.07, QW - 0.07, 0))
bm = bmesh.new()
cil(bm, MA + Vector((0, 0, 0.3)), 0.04, 0.44, lados=16)
cil(bm, MA + Vector((0, 0, 0.09)), 0.08, 0.02, lados=16)
for k in range(3):
    a = k * 2 * PI / 3
    viga(bm, MA + Vector((0, 0, 0.3)), MA + Vector((math.cos(a) * 0.06, math.sin(a) * 0.06, 0.09)), 0.015)
suavizar(obj('mastro', bm, 'grafite', quadro))
antena = bpy.data.objects.new('antena', None)
sc.collection.objects.link(antena)
antena.parent = quadro
antena.location = MA + Vector((0, 0, 0.55))
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), 0.2, 0.016, 40, 8)
for k in range(3):
    a = k * 2 * PI / 3
    viga(bm, Vector((0, 0, 0)), Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0)), 0.016)
cil(bm, Vector((0, 0, 0)), 0.05, 0.05, lados=14)
obj('antena_anel', bm, 'aco', antena)
bm = bmesh.new()
for k in range(6):
    a = k * PI / 3
    caixa(bm, Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.0)), (0.06, 0.045, 0.05), Matrix.Rotation(a, 3, 'Z'))
obj('antena_sensores', bm, 'amarelo', antena)
bm = bmesh.new()
for k in range(6):
    a = k * PI / 3
    caixa(bm, Vector((math.cos(a) * 0.231, math.sin(a) * 0.231, 0.0)), (0.004, 0.03, 0.02), Matrix.Rotation(a, 3, 'Z'))
obj('antena_lentes', bm, 'led_ambar', antena)

# ------------------------------------------------------------------ unidade hidráulica (oeste, no chão)
XH = -1.3
bm = bmesh.new()
caixa_de(bm, (XH - 0.16, -0.5, 0.0), (XH + 0.18, 0.5, 0.06))                      # skid
obj('hpu_skid', bm, 'ferro')
bm = bmesh.new()
cil(bm, Vector((XH, 0.2, 0.25)), 0.15, 0.5, Vector((0, 1, 0)), lados=24)        # tanque
suavizar(obj('hpu_tanque', bm, 'grafite'))
bm = bmesh.new()
for y in (0.02, 0.38):
    caixa_de(bm, (XH - 0.12, y - 0.03, 0.06), (XH + 0.12, y + 0.03, 0.13))
    cil(bm, Vector((XH, y, 0.25)), 0.158, 0.03, Vector((0, 1, 0)), lados=24)
cil(bm, Vector((XH, 0.3, 0.42)), 0.035, 0.04, lados=12)
obj('hpu_cintas', bm, 'ferro')
bm = bmesh.new()
cil(bm, Vector((XH, -0.2, 0.2)), 0.1, 0.24, Vector((0, 1, 0)), lados=20)         # motor
for k in range(6):
    cil(bm, Vector((XH, -0.3 + k * 0.035, 0.2)), 0.115, 0.008, Vector((0, 1, 0)), lados=20)
caixa_de(bm, (XH - 0.11, -0.33, 0.06), (XH + 0.11, -0.07, 0.1))
suavizar(obj('hpu_motor', bm, 'grafite'))
bm = bmesh.new()
cil(bm, Vector((XH, -0.37, 0.2)), 0.07, 0.1, Vector((0, 1, 0)), lados=16)       # bomba
obj('hpu_bomba', bm, 'amarelo')
MAN = Vector((XH + 0.08, -0.43, 0.2))
bm = bmesh.new()
caixa(bm, MAN, (0.16, 0.1, 0.22))
for k in range(3):
    caixa(bm, MAN + Vector((0.09, -0.05 + k * 0.05, 0.04)), (0.05, 0.04, 0.06))
obj('hpu_valvulas', bm, 'aco')
bm = bmesh.new()
for k in range(3):
    cil(bm, MAN + Vector((0.118, -0.05 + k * 0.05, 0.08)), 0.008, 0.01, Vector((1, 0, 0)), lados=8)
obj('hpu_leds', bm, 'led_verde')
bm = bmesh.new()
for y in (0.4, 0.47):
    cil(bm, Vector((XH + 0.12, y, 0.3)), 0.035, 0.46, lados=16)
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.035, matrix=Matrix.Translation((XH + 0.12, y, 0.53)))
suavizar(obj('hpu_acumuladores', bm, 'amarelo'))
bm = bmesh.new()
caixa_de(bm, (XH - 0.165, -0.5, 0.0), (XH - 0.16, 0.5, 0.06))
obj('hpu_listras', bm, 'listras')
bm = bmesh.new()
tubo_curvo(bm, bezier((XH, -0.05, 0.22), (XH, -0.0, 0.32), (XH, 0.0, 0.32), (XH, 0.05, 0.25), 6), 0.02)
suavizar(obj('hpu_tubos', bm, 'aco'))
bm = bmesh.new()
mancha(bm, (XH + 0.2, -0.35), 0.2, 0.002)
mancha(bm, (XH - 0.05, 0.6), 0.12, 0.002)
for p in PES:
    mancha(bm, (p.x * 0.93, p.y * 0.93), 0.1, 0.0025)
obj('oleo_chao', bm, 'oleo')

# mangueiras: bloco de válvulas → pé de cada perna (porta da camisa) e → coluna do pilão
MANG = []
for n, p in enumerate(PES):
    d = (Vector((0, 0, 0)) - Vector((p.x, p.y, 0))).normalized()
    porta = p + d * 0.0 + Vector((0, 0, 0.18)) + Vector((-d.y, d.x, 0)) * 0.13
    a = MAN + Vector((0.08, -0.05 + 0.05 * (n % 3), -0.08))
    meio = Vector((p.x * 1.08, p.y * 0.72 if abs(p.y) > 0 else 0, 0.03))
    via = [a, Vector((a.x + 0.05, a.y, 0.03)), Vector((XH + 0.25, p.y * 0.85, 0.03)), Vector((p.x * 0.9 - (0.0 if p.x < 0 else 0.0), p.y * 1.1, 0.03))]
    if p.x > 0:
        via = [a, Vector((a.x + 0.05, a.y, 0.03)), Vector((XH + 0.25, math.copysign(1.15, p.y), 0.03)),
               Vector((p.x - 0.3, math.copysign(1.15, p.y), 0.03))]
    MANG.append(bezier(via[-1], via[-1] + Vector((0, 0, 0.05)), porta + Vector((0, 0, -0.15)), porta, 10))
    MANG.append(polilinha(via[:-1] + [via[-1]], 0.08))
XC = 1.06                                                  # coluna rígida que leva o óleo ao pilão
for sy, n in ((-0.06, 0), (0.06, 1)):
    a = MAN + Vector((0.08, 0.05, -0.12 + 0.04 * n))
    MANG.append(polilinha([a, Vector((XH + 0.25, -1.08 - 0.05 * n, 0.03)), Vector((XC, -1.08 - 0.05 * n, 0.03)),
                           Vector((XC, -0.55 + sy, 0.03))], 0.08))
    MANG.append(bezier(Vector((XC, -0.55 + sy, 0.03)), Vector((XC, -0.55 + sy, 0.1)), Vector((XC, -0.47 + sy, 0.12)),
                       Vector((XC, -0.47 + sy, 0.2)), 8))
bm = bmesh.new()
for m in MANG:
    tubo_curvo(bm, m, 0.019, 10)
suavizar(obj('mangueiras', bm, 'borracha'))
bm = bmesh.new()                                           # coluna de tubos (aço) até o braço do pilão
for sy in (-0.06, 0.06):
    tubo_curvo(bm, [Vector((XC, -0.47 + sy, 0.2)), Vector((XC, -0.47 + sy, Z_QUADRO - 0.3))], 0.022, 14)
caixa_de(bm, (XC - 0.1, -0.62, 0.0), (XC + 0.1, -0.32, 0.03))
for z in (0.6, 1.1, 1.5):
    caixa(bm, Vector((XC, -0.47, z)), (0.06, 0.2, 0.04))
suavizar(obj('coluna_oleo', bm, 'aco'))
TOPO_COL = [Vector((XC, -0.47 + sy, Z_QUADRO - 0.3)) for sy in (-0.06, 0.06)]
bm = bmesh.new()
for t in (0.25, 0.5, 0.75):                                # abraçadeiras no chão
    caixa(bm, Vector((XH + 0.25 + (XC - XH - 0.25) * t, -1.1, 0.03)), (0.05, 0.14, 0.05))
obj('abracadeiras', bm, 'ferro')

# ------------------------------------------------------------------ cabos-raiz: do quadro, pelas pernas, entrando na terra
bm, bab = bmesh.new(), bmesh.new()
for n, (p, s_) in enumerate(zip(PES, SUP)):
    c = Vector((p.x, p.y, 0))
    d = Vector((p.x, p.y, 0)).normalized()
    eixo = (s_ - p).normalized()
    lado = eixo.cross(Vector((0, 0, 1))).normalized()
    off = lado * 0.17
    topo = s_ + off + eixo * 0.05
    base = p + off + eixo * 0.08
    via = [s_ + Vector((0, 0, 0.12)) + off * 0.6, topo] + [base + (topo - base) * t for t in (0.7, 0.4)] + [base]
    pe = c + off * 1.3 + d * 0.12 + Vector((0, 0, 0.05))
    pts = polilinha(via, 0.05)[:-1] + bezier(base, base - eixo * 0.12, pe + Vector((0, 0, 0.1)), pe, 6)
    tubo_curvo(bm, pts, 0.017, 8)
    for t in (0.1, 0.32, 0.55):                           # abraçadeiras: cabo preso na camisa
        q_ = p + (s_ - p) * t
        caixa(bab, q_ + off * 0.55, (0.13, 0.03, 0.03), Matrix.Rotation(math.atan2(lado.y, lado.x), 3, 'Z'))
    for r in range(4):                                     # raízes: abrem e entram na terra
        ang = math.atan2(d.y, d.x) + (r - 1.5) * 0.55 + random.uniform(-0.15, 0.15)
        dr = Vector((math.cos(ang), math.sin(ang), 0))
        L = random.uniform(0.25, 0.45)
        fim = pe + dr * L + Vector((0, 0, -0.2))
        tubo_curvo(bm, bezier(pe, pe + dr * 0.08 + Vector((0, 0, -0.03)), pe + dr * L * 0.7 + Vector((0, 0, -0.02)), fim, 10),
                   0.013 - 0.0015 * r, 6)
obj('cabos_abracadeiras', bab, 'ferro')
obj('cabos_raiz', bm, 'cabo')
bm = bmesh.new()
for p in PES:                                               # terra fofa onde as raízes entram
    for k in range(10):
        a = random.uniform(0, 2 * PI)
        pedra(bm, Vector((p.x, p.y, 0)) + Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.35, 0.6), random.uniform(0.02, 0.045), 0.4)
obj('raiz_terra', bm, 'torrao')

# ------------------------------------------------------------------ chão em volta: revirado, torrões, lama
bm = bmesh.new()
for k in range(110):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.2, 3.2)
    c = Vector((math.cos(a) * r, math.sin(a) * r, 0.01))
    if abs(c.x) < 1.15 and abs(c.y) < 1.15:
        continue
    pedra(bm, c, random.uniform(0.02, 0.09), 0.55)
obj('torroes', bm, 'torrao')
bm = bmesh.new()
for k in range(16):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.3, 2.8)
    mancha(bm, (math.cos(a) * r, math.sin(a) * r), random.uniform(0.15, 0.4), 0.001)
obj('chao_revirado', bm, 'revirado')
bm = bmesh.new()
for k in range(8):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(1.3, 2.2)
    mancha(bm, (math.cos(a) * r, math.sin(a) * r), random.uniform(0.1, 0.25), 0.0015)
obj('lama_chao', bm, 'lama')

impactos = []
for k in range(5):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    impactos.append(obj('poeira_impacto', bm, 'poeira_chao'))
poeira_c = []
for k in range(6):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    poeira_c.append(obj('poeira_cava', bm, 'poeira'))

# ------------------------------------------------------------------ animação (laço de 4 s)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def altura_pilao(h):
    if h < 0.08:
        return 0.0
    if h < 0.6:
        return 0.32 * suave((h - 0.08) / 0.52)
    if h < 0.86:
        return 0.32
    x = (h - 0.86) / 0.14
    return 0.32 * (1 - x * x)


cristal_em = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
emissor_em = base3d.M['emissor'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    resp = math.sin(2 * PI * fr)
    zq = Z_QUADRO + 0.04 * resp                               # o quadro respira (pernas estendem e recolhem)
    quadro.location = (0, 0, zq)
    quadro.keyframe_insert('location', frame=q)
    for (cam_p, hst_p), p, s in zip(pernas, PES, SUP):
        pos_cilindro(cam_p, hst_p, p, s + Vector((0, 0, zq - Z_QUADRO)), q)
    nucleo.rotation_euler = (0, 0, 2 * PI * fr)
    nucleo.keyframe_insert('rotation_euler', frame=q)
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr) ** 2
    cristal_em.default_value = 0.8 + 1.8 * pulso
    cristal_em.keyframe_insert('default_value', frame=q)
    emissor_em.default_value = 3.0 + 6.0 * pulso
    emissor_em.keyframe_insert('default_value', frame=q)
    luz_n.energy = 8 + 14 * pulso
    luz_n.keyframe_insert('energy', frame=q)
    luz_corte.energy = 6 + 4 * math.sin(2 * PI * 4 * fr) ** 2
    luz_corte.keyframe_insert('energy', frame=q)
    # rocha: gira devagar; camadas de voxels se afastam e voltam (respiração da grade)
    rocha.rotation_euler = (0.04 * math.sin(2 * PI * fr), 0.03 * math.cos(2 * PI * fr), 0.25 * math.sin(2 * PI * fr))
    rocha.location = (0, 0, Z_ROCHA + 0.03 * math.sin(2 * PI * fr + 1))
    rocha.keyframe_insert('rotation_euler', frame=q)
    rocha.keyframe_insert('location', frame=q)
    abre = 0.5 - 0.5 * math.cos(2 * PI * fr)
    for pai, i in voxels:
        pai.location = (0.012 + (0.015 + 0.03 * abre) * i, 0, 0)
        pai.keyframe_insert('location', frame=q)
    nx = max(camadas) if camadas else 0
    for o, off, k in soltos:
        u = (fr + k * 0.2) % 1.0
        base_x = X_CORTE + P * (nx + 1.5) + 0.045 * nx + 0.04 + 0.12 * u
        o.location = Vector((base_x, 0, 0)) + off * (1 + 0.3 * u)
        o.rotation_euler = (0, 0, 0)
        o.scale = [max(0.001, min(1.0, (1 - u) * 4, u * 8))] * 3
        for c in ('location', 'rotation_euler', 'scale'):
            o.keyframe_insert(c, frame=q)
    for k, o in enumerate(poeira_r):
        a = k * 2 * PI / len(poeira_r) + 2 * PI * fr
        o.location = (0.35 + 0.1 * math.cos(a), 0.3 * math.sin(a), Z_ROCHA + zq - 0.1 + 0.1 * math.cos(a * 2))
        o.scale = [0.12 + 0.03 * math.sin(a + k)] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # blocos de terra: sobem girando, alinham em grade, descem e assentam
    for n, (o, cel, slot, f0, eixo, voltas) in enumerate(blocos):
        u = (fr + f0) % 1.0
        acima = Vector((cel.x, cel.y, 0.14))                 # sai da cava na vertical antes de abrir e girar
        if u < 0.12:
            pos, giro = cel, 0.0
        elif u < 0.24:
            pos, giro = cel.lerp(acima, suave((u - 0.12) / 0.12)), 0.0
        elif u < 0.44:
            s = suave((u - 0.24) / 0.2)
            pos, giro = acima.lerp(slot, s), voltas * (PI / 2) * suave((s - 0.4) / 0.6)   # só gira depois de abrir
        elif u < 0.76:
            pos, giro = slot + Vector((0, 0, 0.015 * math.sin(2 * PI * (u - 0.44) / 0.32))), voltas * (PI / 2)
        elif u < 0.9:
            s = suave((u - 0.76) / 0.14)
            pos, giro = slot.lerp(acima, s), voltas * (PI / 2) * (1 + suave(s / 0.6))
        else:
            pos, giro = acima.lerp(cel, suave((u - 0.9) / 0.1)), voltas * PI
        o.location = pos
        o.rotation_quaternion = Quaternion(eixo, giro)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('rotation_quaternion', frame=q)
        g = gotas[n]
        ug = ((u - 0.45) / 0.3 * 3) % 1.0 if 0.45 < u < 0.75 else None
        if ug is not None:
            tt = ug * 0.38
            zg = slot.z - LADO_B / 2 - 0.03 - 4.9 * tt * tt
            g.location = Vector((slot.x + 0.04, slot.y - 0.03, zg))
            g.scale = [1.0 if zg > CAVA[2][1] else 0.001] * 3
        else:
            g.location = Vector((slot.x, slot.y, slot.z))
            g.scale = [0.001] * 3
        g.keyframe_insert('location', frame=q)
        g.keyframe_insert('scale', frame=q)
    for k, o in enumerate(poeira_c):
        a = k * 2 * PI / len(poeira_c) - 2 * PI * fr
        o.location = (0.5 * math.cos(a), 0.5 * math.sin(a), -0.2 + 0.15 * math.sin(a * 2 + k))
        o.scale = [0.22 + 0.05 * math.sin(a + k)] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # pilão: 2 golpes por laço; cilindros presos sob o braço do quadro
    h = (fr * 2) % 1.0
    zp = altura_pilao(h)
    pilao.location = (XP, 0, zp)
    pilao.keyframe_insert('location', frame=q)
    for i, sy in enumerate((-0.15, 0.15)):
        pos_cilindro(*cil_pilao[i], Vector((XP, sy, zq - 0.08)), Vector((XP, sy, zp + 0.41)), q)
    for k, o in enumerate(impactos):
        u = (h + k * 0.05) % 1.0
        a = k * 2 * PI / len(impactos)
        o.location = Vector((XP + math.cos(a) * (0.25 + 0.4 * u), math.sin(a) * (0.35 + 0.4 * u), 0.08 + 0.3 * u))
        o.scale = [0.14 + 0.3 * u] * 3
        o.hide_render = u > 0.45
        o.hide_viewport = o.hide_render
        for c in ('location', 'scale', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
    antena.rotation_euler = (0, 0, 2 * PI * fr)
    antena.keyframe_insert('rotation_euler', frame=q)
for o in list(sc.objects) + [luz_n, luz_corte]:
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# mangueiras do pilão: topo da coluna → portas de cima dos cilindros (posição média)
bm = bmesh.new()
for i, sy in enumerate((-0.15, 0.15)):
    port = Vector((XP, sy - 0.085, Z_QUADRO - 0.08 - 0.19))
    tubo_curvo(bm, bezier(TOPO_COL[i], TOPO_COL[i] + Vector((0, 0, 0.12)), port + Vector((-0.12, -0.15, 0.05)), port, 14), 0.017, 10)
suavizar(obj('mangueiras_pilao', bm, 'borracha'))

# ------------------------------------------------------------------ cena: luz e câmera
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


ALVO = (0.0, 0.0, 1.05)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_uma = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.frame_set(int(QUADROS * 0.3) + 1)
    for i, (ang, alt) in enumerate(((300, 3.4), (210, 3.6), (120, 3.8), (30, 3.2))):
        if so_uma is not None and so_uma != str(i):
            continue
        sc.render.resolution_x, sc.render.resolution_y = 1200, 1200
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 7.2, math.sin(a) * 7.2, alt)), ALVO, 35)
        sc.render.filepath = os.path.join(AQUI, 'terraplenagem_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if so_uma is None or so_uma == 'perto':
        sc.frame_set(int(QUADROS * 0.27) + 1)
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((1.9, -2.6, 1.25), (0.0, 0.0, 0.45), 30)          # de perto: cava, blocos em grade, pilão
        sc.render.filepath = os.path.join(AQUI, 'terraplenagem_perto.png')
        bpy.ops.render.render(write_still=True)
    if so_uma is None or so_uma == 'rocha':
        sc.frame_set(int(QUADROS * 0.5) + 1)
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((1.9, -1.6, 2.9), (0.1, 0.0, 2.3), 34)            # de perto: rocha fatiada, núcleo, quadro
        sc.render.filepath = os.path.join(AQUI, 'terraplenagem_rocha.png')
        bpy.ops.render.render(write_still=True)
print('TERRAPLENAGEM ok')
