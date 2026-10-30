"""Estudo isolado (fora do jogo): METRALHADORA (torre_metralhadora), 2×2 tiles. Munição comum (caixa de munição)
entra pelo sul (ITEM_ENT_S1, tile da direita) por esteira ou braço. 10 tiros/s, alcance 18 m.
Inspiração pedida: torre com TAMBOR QUE GIRA (gatling) que se IMPLANTA (desdobra) ao ser construída.
- Casco blindado chanfrado sobre sapata aparafusada na laje (chumbadores), placas grafite, remendo de outra cor,
  grade de respiro, caixa de junção com cabos expostos, plaqueta de série apagada, óleo, ferrugem, lama e pó.
- Quatro estabilizadores (diagonais): dobradiça com coroa e motor-redutor; pé com sapata e estaca hidráulica que
  se crava na laje (lascas de concreto em volta).
- Mastro elevador (sobe a cabeça na implantação) com hastes hidráulicas, ferrolhos que travam e cabo espiral.
- Trava de transporte: poste telescópico com mandíbulas que seguram o feixe de canos até a implantação.
- Coroa fixa no cabeçote; o motor de giro anda com a cabeça e o pinhão rola na coroa.
- Cabeça: garfo com munhões, motor e engrenagem de elevação, caixa de munição com boca de roletes, cinta de
  munição elo a elo subindo até a bandeja; casulo sensor da IA (olho violeta) com radar que gira.
- Arma: culatra, motor do tambor com pinhão e coroa, feixe de 6 canos rotativo com braçadeiras e quebra-chamas,
  calha de cápsulas e calha de elos; escudo blindado amassado com marcas de impacto e remendo aparafusado.
- Carregador: esteira curta da boca sul, empurrador hidráulico, elevador de caixas e duto até o casco.
Animação: 1–96 (laço de 4 s): varredura, aquisição, aceleração do tambor, rajada de 16 tiros a 10 tiros/s (clarão,
traçante a cada 4, cápsula e elo ejetados a cada tiro, com física), desaceleração, canos em brasa e fumaça.
101–196: implantação (pernas descem e cravam, mandíbulas abrem, poste recolhe, cabeça sobe, ferrolhos travam,
a arma destrava e testa o giro do tambor).
Uso: blender -b --python estudo_metralhadora.py -- foto [0|perto|implantacao|rajada]
     blender -b --python estudo_metralhadora.py -- teste x y z ax ay az lente quadro"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
I0, I1 = 101, 196                 # implantação
random.seed(73)

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
        A, Bq = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], Bq[(j + 1) % nr], Bq[j]))


ROT_X = Matrix.Rotation(PI / 2, 3, 'Y')          # anel do toro em volta do eixo x
ROT_Y = Matrix.Rotation(PI / 2, 3, 'X')          # anel em volta do eixo y


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def feixe(bc, ba, pts, lat, n=3, r=0.012, passo=4):
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.01, pts[j] + u * 0.01, r * (n + 0.6), 12)


def chanfro(bm, h, c, z0, z1, cx=0.0, cy=0.0):
    """Prisma de quadrado com cantos chanfrados (meia largura h, chanfro c)."""
    pts = [(h, -h + c), (h, h - c), (h - c, h), (-h + c, h), (-h, h - c), (-h, -h + c), (-h + c, -h), (h - c, -h)]
    v0 = [bm.verts.new((cx + x, cy + y, z0)) for x, y in pts]
    v1 = [bm.verts.new((cx + x, cy + y, z1)) for x, y in pts]
    bm.faces.new(list(reversed(v0)))
    bm.faces.new(v1)
    for k in range(8):
        bm.faces.new((v0[k], v0[(k + 1) % 8], v1[(k + 1) % 8], v1[k]))


def dentro_chanfro(x, y, h, c):
    return abs(x) <= h and abs(y) <= h and abs(x) + abs(y) <= 2 * h - c


def rot_face(n):
    n = Vector((n.x, n.y, 0)).normalized()
    return Matrix((Vector((n.y, -n.x, 0)), n, Vector((0, 0, 1)))).transposed()


def prisma_xz(bm, perfil, y0, y1):
    a = [bm.verts.new((x, y0, z)) for x, z in perfil]
    b = [bm.verts.new((x, y1, z)) for x, z in perfil]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(perfil)
    for k in range(n):
        bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))


def engrenagem(bm, c, R, h, dentes, eixo, furo=None):
    """Engrenagem de dentes retos em volta de 'eixo' (Vector unitário)."""
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    cil(bm, Vector(c), R - 0.006, h, eixo, lados=max(16, dentes * 2))
    for k in range(dentes):
        a = k * 2 * PI / dentes
        caixa(bm, Vector(c) + q @ Vector((math.cos(a) * (R - 0.002), math.sin(a) * (R - 0.002), 0)),
              (0.009 + R * 0.02, max(0.006, R * 2 * PI / dentes * 0.45), h), q @ Matrix.Rotation(a, 3, 'Z'))
    cil(bm, Vector(c), R * 0.35, h * 1.3, eixo, lados=16)


BMS = {}


def B(nome, mat, liso=False, g='base'):
    k = (nome, mat, liso, g)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def parafuso(p, n, g='base', r=0.011):
    cil(B('parafusos', 'aco', False, g), Vector(p), r, 0.012, Vector(n), lados=6)


def novo_vazio(nome, pai=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    e.parent = pai
    e.location = loc
    return e


def obj_m(nome, bm, lista, pai=None):
    """Objeto de malha com vários materiais (índice por face)."""
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    for m in lista:
        me.materials.append(base3d.M[m])
    o.parent = pai
    return o


def com_mx(bm, Mx, mi, fn):
    """Executa fn(bm), leva a geometria nova pela matriz Mx e marca o material mi."""
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    nv, nf = len(bm.verts), len(bm.faces)
    fn(bm)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    for v in bm.verts[nv:]:
        v.co = Mx @ v.co
    for f in bm.faces[nf:]:
        f.material_index = mi


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def fumaca_grad_mat(nome, dens, z0, z1, escura=(0.015, 0.014, 0.014), clara=(0.42, 0.42, 0.43)):
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    no = mats.no
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    next(n for n in nt.nodes if n.type == 'TEX_NOISE').inputs['Scale'].default_value = 5.5
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*escura, 1)
    mix.inputs[7].default_value = (*clara, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


def fiapo_mat():
    """Fiapo de fumaça em volume; a densidade vem da cor do objeto (chave por quadro) para sumir aos poucos."""
    m = bpy.data.materials.new('Fiapo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.07, 0.068, 0.066, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.2, 'Detail': 5.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.3})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    forma = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.65})
    nt.links.new(ru.outputs['Fac'], forma.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], m1.inputs[0])
    nt.links.new(forma.outputs['Result'], m1.inputs[1])
    oi = no(nt, 'ShaderNodeObjectInfo')
    sep = no(nt, 'ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sep.inputs[0])
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(sep.outputs[0], m2.inputs[1])
    m3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    m3.inputs[1].default_value = 140.0
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    nt.links.new(m3.outputs['Value'], vol.inputs['Density'])
    return m


def cano_quente_mat():
    """Aço dos canos: escurece e azula perto da boca; brasa (chave por quadro) cresce em gradiente até a boca."""
    m = bpy.data.materials.new('Canos')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    b.inputs['Metallic'].default_value = 1.0
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    g = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.93})
    nt.links.new(sep.outputs['X'], g.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c1.inputs[6].default_value = (0.3, 0.3, 0.31, 1)
    c1.inputs[7].default_value = (0.06, 0.05, 0.06, 1)
    nt.links.new(g.outputs['Result'], c1.inputs[0])
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    c2.inputs[0].default_value = 0.5
    nt.links.new(c1.outputs[2], c2.inputs[6])
    nt.links.new(ru.outputs['Color'], c2.inputs[7])
    nt.links.new(c2.outputs[2], b.inputs['Base Color'])
    rr = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.3, 'To Max': 0.7})
    nt.links.new(ru.outputs['Fac'], rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    b.inputs['Emission Color'].default_value = (1.0, 0.1, 0.015, 1)
    pot = no(nt, 'ShaderNodeMath', operation='POWER')
    pot.inputs[1].default_value = 2.6
    nt.links.new(g.outputs['Result'], pot.inputs[0])
    val = no(nt, 'ShaderNodeValue')
    val.name = 'calor'
    val.outputs[0].default_value = 0.0
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(pot.outputs['Value'], mul.inputs[0])
    nt.links.new(val.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs['Value'], b.inputs['Emission Strength'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.95, sujeira=0.9, ferrugem=0.4),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.85, sujeira=0.9, ferrugem=0.2),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'queimado': mats.material('Queimado', (0.13, 0.11, 0.12), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'isol_verm': mats.material('Isolador vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.5, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.085, 0.06, 0.035), 0, 0.85, pintura=False, sujeira=0.2, desgaste=0.0),
    'amarelo_escudo': mats.material('Amarelo do escudo', (0.7, 0.47, 0.05), 0, 0.45, desgaste=0.45, sujeira=0.95, ferrugem=0.5),
    'oliva': mats.material('Oliva', (0.15, 0.16, 0.06), 0, 0.55, desgaste=0.95, sujeira=0.9, ferrugem=0.55),
    'remendo': mats.material('Remendo', (0.2, 0.25, 0.23), 0, 0.5, desgaste=0.9, sujeira=0.85, ferrugem=0.6),
    'listras': base3d.listras_mat(),
    'fuligem_chao': mats.material('Fuligem', (0.045, 0.04, 0.036), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'olho': emissivo('Olho do sensor', VIOLETA, 12.0, (0.05, 0.02, 0.1)),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'led_verm': emissivo('Led vermelho', (1.0, 0.05, 0.03), 10.0),
    'latao_gasto': mats.material('Latão gasto', (0.58, 0.42, 0.17), 1.0, 0.38, pintura=False, sujeira=0.9, ferrugem=0.25),
    'latao_novo': mats.material('Latão', (0.66, 0.48, 0.2), 1.0, 0.3, pintura=False, sujeira=0.5, ferrugem=0.05),
    'aco_capsula': mats.material('Aço da cápsula', (0.36, 0.35, 0.34), 1.0, 0.45, pintura=False, sujeira=0.9, ferrugem=0.5),
    'espoleta': mats.material('Espoleta', (0.7, 0.4, 0.25), 1.0, 0.3, pintura=False, sujeira=0.4),
    'boca_fria': mats.material('Boca queimada', (0.03, 0.025, 0.022), 0.6, 0.7, pintura=False, sujeira=0.2, desgaste=0.0),
    'ponta_tracante': mats.material('Ponta traçante', (0.5, 0.05, 0.03), 0, 0.45, desgaste=0.4, sujeira=0.5),
    'elo': mats.material('Elo', (0.17, 0.17, 0.18), 1.0, 0.45, pintura=False, ferrugem=0.5, sujeira=0.7),
    'canos': cano_quente_mat(),
    'clarao': emissivo('Clarão', (1.0, 0.4, 0.06), 6.0),
    'clarao_nucleo': emissivo('Clarão núcleo', (1.0, 0.7, 0.3), 14.0),
    'tracante': emissivo('Traçante', (1.0, 0.3, 0.06), 70.0),
    'faisca': emissivo('Faísca', (1.0, 0.6, 0.25), 60.0),
    'fiapo': fiapo_mat(),
    'fumaca': fumaca_grad_mat('Fumaça de tiro', 2.0, 1.15, 2.4, (0.12, 0.115, 0.11), (0.36, 0.36, 0.37)),
    'fumaca_canos': fumaca_grad_mat('Fumaça dos canos', 2.2, 1.2, 2.6, (0.16, 0.155, 0.15), (0.58, 0.58, 0.59)),
    'poeira': base3d.volume_mat('Poeira', (0.42, 0.36, 0.27), 3.5, 0.08, 0.6),
})


# ------------------------------------------------------------------ munição (calibre da metralhadora: Ø 21 mm)
def torno(bm, perfil, n=16, fechado=False):
    aneis = []
    for x, r in perfil:
        if r < 1e-6:
            aneis.append([bm.verts.new((x, 0, 0))])
        else:
            aneis.append([bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for a in (k * 2 * PI / n for k in range(n))])
    pares = list(zip(aneis, aneis[1:])) + ([(aneis[-1], aneis[0])] if fechado else [])
    for A, Bq in pares:
        if len(A) == 1 and len(Bq) == 1:
            continue
        if len(A) == 1:
            for k in range(n):
                bm.faces.new((A[0], Bq[k], Bq[(k + 1) % n]))
        elif len(Bq) == 1:
            for k in range(n):
                bm.faces.new((A[(k + 1) % n], A[k], Bq[0]))
        else:
            for k in range(n):
                bm.faces.new((A[k], A[(k + 1) % n], Bq[(k + 1) % n], Bq[k]))


CX = 0.036                    # meio do estojo (origem)
R_CAP = 0.0105                # raio do aro
PITCH = 0.026                 # passo da cinta
PERFIL_CAP = [(0.0, 0.0), (0.0, 0.0105), (0.003, 0.0105), (0.0036, 0.0086), (0.0058, 0.0086), (0.0072, 0.0101),
              (0.050, 0.0098), (0.056, 0.0070), (0.071, 0.0068), (0.071, 0.0058), (0.02, 0.0058), (0.02, 0.0)]


def cartucho(bm, Mx, vivo=False, tracante=False, elo=False):
    """Índices: 0 estojo, 1 boca, 2 espoleta, 3 projétil, 4 ponta, 5 elo."""
    com_mx(bm, Mx, 0, lambda b: torno(b, [(x - CX, r) for x, r in PERFIL_CAP]))
    com_mx(bm, Mx, 1, lambda b: torno(b, [(0.071 - CX, 0.0068), (0.0745 - CX, 0.0067), (0.0745 - CX, 0.0058),
                                          (0.071 - CX, 0.0058)], fechado=True))
    com_mx(bm, Mx, 2, lambda b: torno(b, [(-CX - 0.0004, 0.0), (-CX - 0.0004, 0.0032), (-CX + 0.0002, 0.0032),
                                          (-CX + 0.0002, 0.0)], 10))
    if vivo:
        com_mx(bm, Mx, 3, lambda b: torno(b, [(0.06 - CX, 0.0), (0.06 - CX, 0.0062), (0.08 - CX, 0.0062),
                                              (0.088 - CX, 0.0049)]))
        com_mx(bm, Mx, 4 if tracante else 3, lambda b: torno(b, [(0.088 - CX, 0.0049), (0.093 - CX, 0.0034),
                                                                 (0.0985 - CX, 0.0)]))
    if elo:
        com_mx(bm, Mx, 5, elo_geo)


def elo_geo(bm):
    """Elo de cinta: alça em volta do próprio cartucho e duas alças no vizinho (+y), unidas por pontes."""
    toro(bm, (0.004, 0, 0), 0.0114, 0.0013, 18, 5, ROT_X)
    for x in (-0.02, 0.026):
        toro(bm, (x, PITCH, 0), 0.0114, 0.0013, 18, 5, ROT_X)
    for x in (-0.009, 0.015):
        caixa(bm, (x, PITCH * 0.5, 0.0104), (0.008, PITCH * 0.75, 0.0016))
    caixa(bm, (0.003, PITCH * 0.82, 0.0112), (0.052, 0.005, 0.0014))


def elo_solto(bm, Mx):
    com_mx(bm, Mx, 0, elo_geo)


# ------------------------------------------------------------------ medidas
Z0 = 0.08                 # topo da laje
Z_TOP = 0.56              # topo do casco
Z_COV = 0.58              # topo da tampa
GAP, PLATE_T = 0.08, 0.05
LIFT = 0.26               # curso do mastro


def Z_PT(lift):           # topo do cabeçote (origem do elevador)
    return Z_COV + GAP + PLATE_T + lift


TZ = 0.32                 # munhão acima do cabeçote
R_COROA, R_PIN = 0.28, 0.04
RB = 0.048                # raio do círculo dos canos
MUZ_X = 0.93              # boca dos canos
R_GT, R_PT = 0.10, 0.045  # coroa do tambor e pinhão do motor
R_GE, R_PE = 0.07, 0.025  # engrenagem e pinhão de elevação
R_GL, R_PL = 0.07, 0.025  # engrenagem e pinhão das pernas
H_R, H_Z = 0.56, 0.50     # dobradiça das pernas (raio na diagonal, altura)
PE_R, PE_Z = 0.93, Z0 + 0.10
L_PERNA = math.hypot(PE_R - H_R, H_Z - PE_Z)
A_DEP = math.atan2(H_Z - PE_Z, PE_R - H_R)           # ângulo da perna implantada (para baixo)
A_DOB = math.radians(-95)                             # dobrada para cima
CRAVA = 0.10              # quanto a estaca desce
BX = 0.5                  # boca sul (S1)
FEED = Vector((-0.12, 0.10, 0.125))                   # boca da bandeja (canhão)
BOX_MOUTH = Vector((-0.12, 0.30, 0.345))              # boca da caixa de munição (giro)
PORTA_C = Vector((-0.21, -0.16, -0.15))               # saída da calha de cápsulas (canhão)
PORTA_E = Vector((-0.275, -0.13, -0.16))              # saída da calha de elos (canhão)
POST_X = 0.475            # trava de transporte
print('PERNA L=%.3f ang=%.1f' % (L_PERNA, math.degrees(A_DEP)))

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-0.985, s * 0.985 - 0.012, 0.0), (0.985, s * 0.985 + 0.012, Z0 + 0.002))
    caixa_de(bm, (s * 0.985 - 0.012, -0.985, 0.0), (s * 0.985 + 0.012, 0.985, Z0 + 0.002))
for k in range(9):                                                     # rachaduras finas
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.6, 0.9)
    p = Vector((math.cos(a) * r, math.sin(a) * r, Z0 + 0.0008))
    for j in range(3):
        d = Vector((math.cos(a + random.uniform(-0.8, 0.8)), math.sin(a + random.uniform(-0.8, 0.8)), 0))
        q = p + d * random.uniform(0.04, 0.09)
        viga(B('rachaduras', 'escuro'), p, q, 0.0025)
        p = q

# ------------------------------------------------------------------ sapata e casco
chanfro(B('sapata', 'ferro'), 0.50, 0.17, Z0, 0.15)
for k in range(20):                                                    # chumbadores em volta do casco
    t = k / 20
    a = t * 2 * PI
    d = Vector((math.cos(a), math.sin(a), 0))
    s = 0.465 / max(abs(d.x), abs(d.y), (abs(d.x) + abs(d.y)) * 0.465 / (2 * 0.465 - 0.15))
    p = d * s + Vector((0, 0, 0.156))
    cil(B('parafusos', 'aco'), p, 0.015, 0.022, lados=6)
    cil(B('arruelas', 'ferro'), p - Vector((0, 0, 0.006)), 0.025, 0.006, lados=12)
chanfro(B('casco', 'amarelo'), 0.42, 0.14, 0.15, Z_TOP)
chanfro(B('tampa', 'grafite'), 0.425, 0.143, Z_TOP, Z_COV)
caixa_de(B('poco', 'escuro'), (-0.15, -0.15, Z_COV - 0.004), (0.15, 0.15, Z_COV + 0.0015))      # poço do mastro
for s in (-1, 1):
    caixa_de(B('poco_quadro', 'ferro'), (-0.17, s * 0.16 - 0.01, Z_COV), (0.17, s * 0.16 + 0.01, Z_COV + 0.012))
    caixa_de(B('poco_quadro', 'ferro'), (s * 0.16 - 0.01, -0.15, Z_COV), (s * 0.16 + 0.01, 0.15, Z_COV + 0.012))
for k in range(28):                                                    # parafusos da tampa
    a = k * 2 * PI / 28
    d = Vector((math.cos(a), math.sin(a), 0))
    s = 0.39 / max(abs(d.x), abs(d.y), (abs(d.x) + abs(d.y)) * 0.39 / (2 * 0.39 - 0.12))
    parafuso(d * s + Vector((0, 0, Z_COV + 0.005)), (0, 0, 1), r=0.009)
# faixa de perigo na borda alta das quatro faces retas
FACES = {}
for k, ang in enumerate((0, 90, 180, 270)):
    a = math.radians(ang)
    n = Vector((math.cos(a), math.sin(a), 0))
    FACES[ang] = (n, rot_face(n))
    caixa(B('faixa_casco', 'listras'), n * 0.421 + Vector((0, 0, 0.535)), (0.54, 0.004, 0.03), rot_face(n))
# placas blindadas aparafusadas
PLACAS = [(0, -0.155, 0.21), (0, 0.155, 0.21), (90, 0.0, 0.46), (180, 0.0, 0.46), (270, -0.08, 0.32)]
for ang, off, larg in PLACAS:
    n, R = FACES[ang]
    c = n * 0.429 + R @ Vector((off, 0, 0)) + Vector((0, 0, 0.345))
    caixa(B('placas', 'grafite'), c, (larg, 0.018, 0.3), R)
    for sx in (-1, 1):
        for sz in (-1, 0, 1):
            parafuso(c + R @ Vector((sx * (larg / 2 - 0.025), 0.01, 0)) + Vector((0, 0, sz * 0.12)), n)
# remendo de outra cor na face norte, solda em volta
n, R = FACES[90]
c = n * 0.4395 + R @ Vector((0.1, 0, 0)) + Vector((0, 0, 0.3))
caixa(B('remendo', 'remendo'), c, (0.16, 0.006, 0.12), Matrix.Rotation(0.06, 3, 'Y') @ R if False else R)
for sx in (-1, 1):
    for sz in (-1, 1):
        parafuso(c + R @ Vector((sx * 0.065, 0.004, 0)) + Vector((0, 0, sz * 0.045)), n, r=0.008)
for j in range(14):
    t = j / 13
    caixa(B('solda', 'queimado'), c + R @ Vector((-0.085 + 0.17 * t, 0.002, 0)) + Vector((0, 0, -0.064)), (0.012, 0.008, 0.008), R)
# grade de respiro na face oeste
n, R = FACES[180]
c = n * 0.439 + Vector((0, 0, 0.33))
caixa(B('respiro_fundo', 'escuro'), c, (0.24, 0.004, 0.14), R)
for j in range(7):
    caixa(B('respiro_aletas', 'aco'), c + R @ Vector((0, 0.008, 0)) + Vector((0, 0, -0.06 + j * 0.02)), (0.25, 0.014, 0.006),
          R @ Matrix.Rotation(-0.5, 3, 'X'))
for sx in (-1, 1):
    caixa(B('respiro_quadro', 'ferro'), c + R @ Vector((sx * 0.13, 0.006, 0)), (0.016, 0.016, 0.16), R)
# plaqueta de série apagada (face sul)
n, R = FACES[270]
c = n * 0.4395 + R @ Vector((-0.1, 0, 0)) + Vector((0, 0, 0.255))
caixa(B('plaqueta', 'aco'), c, (0.12, 0.004, 0.05), R)
for j in range(9):
    if random.random() < 0.6:
        caixa(B('plaqueta_num', 'escuro'), c + R @ Vector((-0.045 + j * 0.011, 0.0025, 0)), (0.006, 0.001, 0.016), R)
# caixa de junção na face oeste com cabos expostos
JB = Vector((-0.45, -0.24, 0.22))
caixa_de(B('juncao', 'grafite'), (-0.47, -0.32, 0.16), (-0.43, -0.17, 0.30))
caixa_de(B('juncao_tampa', 'amarelo'), (-0.476, -0.31, 0.17), (-0.47, -0.18, 0.29))
for y in (-0.3, -0.19):
    for z in (0.18, 0.28):
        parafuso((-0.478, y, z), (-1, 0, 0), r=0.007)
cil(B('led_led_ambar', 'led_ambar'), Vector((-0.478, -0.245, 0.27)), 0.006, 0.004, Vector((1, 0, 0)), lados=10)
for i in range(3):                                                     # cabos soltos saindo da junção para a sapata
    pts = bezier(Vector((-0.455, -0.30 + i * 0.03, 0.16)), Vector((-0.47, -0.30 + i * 0.03, 0.1)),
                 Vector((-0.52, -0.33 + i * 0.05, 0.17)), Vector((-0.56, -0.36 + i * 0.05, 0.155)), 8)
    mangueira(B('cabos', 'cabo', True), pts, 0.008)
for i in range(2):
    pts = bezier(Vector((-0.45, -0.2 + i * 0.03, 0.30)), Vector((-0.45, -0.2 + i * 0.03, 0.42)),
                 Vector((-0.44, -0.1 + i * 0.03, 0.5)), Vector((-0.44, -0.05 + i * 0.03, 0.555)), 8)
    mangueira(B('cabos', 'cabo', True), pts, 0.009)
caixa_de(B('eletrocalha', 'ferro'), (-0.448, -0.11, 0.34), (-0.43, -0.0, 0.36))
# óleo, ferrugem, lama, pó
for k in range(14):
    ang = random.choice((0, 90, 180, 270))
    n, R = FACES[ang]
    L = random.uniform(0.06, 0.2)
    caixa(B('escorridos', random.choice(('ferrugem', 'oleo', 'ferrugem'))),
          n * 0.4395 + R @ Vector((random.uniform(-0.2, 0.2), 0.001, 0)) + Vector((0, 0, 0.5 - L / 2)),
          (random.uniform(0.006, 0.014), 0.002, L), R)
for k in range(22):                                                    # lama respingada na base do casco
    ang = random.choice((0, 90, 180, 270))
    n, R = FACES[ang]
    caixa(B('lama', 'lama'), n * 0.4385 + R @ Vector((random.uniform(-0.26, 0.26), 0.0, 0)) + Vector((0, 0, random.uniform(0.17, 0.24))),
          (random.uniform(0.02, 0.07), 0.003, random.uniform(0.015, 0.05)), R @ Matrix.Rotation(random.uniform(-0.6, 0.6), 3, 'Y'))
for k in range(10):
    a = random.uniform(0, 2 * PI)
    mancha(B('po', 'po'), (math.cos(a) * 0.38, math.sin(a) * 0.38), random.uniform(0.03, 0.06), Z_COV + 0.0012)
for k in range(8):
    a = random.uniform(0, 2 * PI)
    mancha(B('lama_chao', 'lama'), (math.cos(a) * 0.5, math.sin(a) * 0.5), random.uniform(0.04, 0.08), 0.1508)

# ------------------------------------------------------------------ pernas (estabilizadores)
PHI = [math.radians(45 + 90 * k) for k in range(4)]


def HF(k):
    d = Vector((math.cos(PHI[k]), math.sin(PHI[k]), 0))
    return Matrix.Translation(d * H_R + Vector((0, 0, H_Z))) @ Matrix.Rotation(PHI[k], 4, 'Z')


R_FACE_DIAG = (2 * 0.42 - 0.14) / math.sqrt(2)
pernas, pinhoes_perna, estacas = [], [], []
for k in range(4):
    Hm = HF(k)
    H3 = Hm.to_3x3()
    W = lambda v: Hm @ Vector(v)
    # placa de apoio no chanfro, garfo da dobradiça, eixo e porcas
    caixa(B('perna_apoio', 'ferro'), W((R_FACE_DIAG - H_R + 0.008, 0, -0.05)), (0.016, 0.26, 0.2), H3)
    for s in (-1, 1):
        caixa(B('garfo', 'amarelo'), W((-0.008, s * 0.075, -0.005)), (0.115, 0.02, 0.125), H3)
        parafuso(W((R_FACE_DIAG - H_R + 0.018, s * 0.105, -0.12)), H3 @ Vector((1, 0, 0)))
        parafuso(W((R_FACE_DIAG - H_R + 0.018, s * 0.105, 0.03)), H3 @ Vector((1, 0, 0)))
    cil(B('garfo_eixo', 'aco', True), W((0, 0, 0)), 0.02, 0.2, H3 @ Vector((0, 1, 0)), lados=14)
    for s in (-1, 1):
        cil(B('parafusos', 'aco'), W((0, s * 0.1, 0)), 0.026, 0.012, H3 @ Vector((0, 1, 0)), lados=6)
    # motor-redutor com pinhão engrenado na coroa da perna
    cil(B('perna_motor', 'grafite', True), W((0, 0.165, -0.095)), 0.032, 0.11, H3 @ Vector((0, 1, 0)), lados=20)
    for j in range(4):
        cil(B('perna_motor_aletas', 'ferro', True), W((0, 0.135 + j * 0.022, -0.095)), 0.037, 0.006, H3 @ Vector((0, 1, 0)), lados=20)
    cil(B('perna_motor_tampa', 'ferro', True), W((0, 0.222, -0.095)), 0.034, 0.012, H3 @ Vector((0, 1, 0)), lados=20)
    caixa(B('perna_motor_sela', 'ferro'), W(((R_FACE_DIAG - H_R) / 2 - 0.01, 0.165, -0.095)), (abs(R_FACE_DIAG - H_R) + 0.04, 0.06, 0.03), H3)
    pts = [W((0, 0.23, -0.095)), W((0, 0.25, -0.12)), W((-0.03, 0.24, -0.2)), W((R_FACE_DIAG - H_R + 0.01, 0.2, -0.24))]
    mangueira(B('cabos', 'cabo', True), bezier(*pts, 8), 0.008)
    p = novo_vazio('perna%d_pinhao' % k, None, W((0, 0.10, -0.095)))
    p.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    engrenagem(bm, (0, 0, 0), R_PL, 0.018, 10, Vector((0, 1, 0)))
    obj('perna%d_pinhao_dentes' % k, bm, 'aco', p)
    pinhoes_perna.append(p)
    # perna (gira na dobradiça)
    pe = novo_vazio('perna%d' % k)
    pe.location = Hm.translation
    pe.rotation_mode = 'QUATERNION'
    pernas.append(pe)
    g = 'perna%d' % k
    cil(B('junta', 'ferro', True, g), Vector((0, 0, 0)), 0.045, 0.13, Vector((0, 1, 0)), lados=24)
    engrenagem(B('coroa_perna', 'aco', True, g), (0, 0.095, 0), R_GL, 0.018, 26, Vector((0, 1, 0)))
    # viga caixão afunilada
    L = L_PERNA
    bmv = B('viga', 'amarelo', False, g)
    vs = []
    for x, w, h in ((0.03, 0.045, 0.05), (L - 0.03, 0.036, 0.038)):
        vs.append([bmv.verts.new((x, sy * w, sz * h)) for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bmv.faces.new(list(reversed(vs[0])))
    bmv.faces.new(vs[1])
    for i in range(4):
        bmv.faces.new((vs[0][i], vs[1][i], vs[1][(i + 1) % 4], vs[0][(i + 1) % 4]))
    for sy in (-1, 1):                                               # chapas laterais com furos de alívio
        for t, rr in ((0.32, 0.018), (0.55, 0.015)):
            x = L * t
            w = 0.045 + (0.036 - 0.045) * (x - 0.03) / (L - 0.06)
            cil(B('furos', 'escuro', True, g), Vector((x, sy * (w + 0.001), 0)), rr, 0.004, Vector((0, 1, 0)), lados=16)
            toro(B('furos_aro', 'ferro', True, g), Vector((x, sy * (w + 0.002), 0)), rr + 0.003, 0.0025, 20, 5, ROT_Y)
    caixa(B('listras_perna', 'listras', False, g), Vector((L - 0.1, 0, 0.040)), (0.1, 0.075, 0.004))
    for x in (0.1, 0.25):
        for sy in (-1, 1):
            parafuso((x, sy * 0.046, 0.025), (0, sy, 0), g, 0.007)
    for j in range(5):                                               # ferrugem e lama na viga
        caixa(B('lama_perna', 'lama', False, g), Vector((random.uniform(0.25, L - 0.05), random.choice((-1, 1)) * 0.043, random.uniform(-0.03, 0.0))),
              (random.uniform(0.02, 0.06), 0.003, random.uniform(0.01, 0.025)))
    caixa(B('escorrido_perna', 'ferrugem', False, g), Vector((0.2, 0.0, -0.046)), (0.06, 0.012, 0.003))
    # pé (fixo na perna, nivelado quando implantada)
    F = Matrix.Translation((L, 0, 0)) @ Matrix.Rotation(-A_DEP, 4, 'Y')
    F3 = F.to_3x3()
    FW = lambda v: F @ Vector(v)
    caixa(B('tornozelo', 'ferro', False, g), FW((0, 0, -0.02)), (0.1, 0.09, 0.1), F3)
    cil(B('sapata_pe', 'ferro', True, g), FW((0, 0, -0.085)), 0.11, 0.03, F3 @ Vector((0, 0, 1)), lados=32)
    for j in range(6):
        a = j * PI / 3 + PI / 6
        caixa(B('nervuras_pe', 'amarelo', False, g), FW((math.cos(a) * 0.07, math.sin(a) * 0.07, -0.055)), (0.045, 0.012, 0.035),
              F3 @ Matrix.Rotation(a, 3, 'Z'))
        parafuso(FW((math.cos(a + 0.5) * 0.093, math.sin(a + 0.5) * 0.093, -0.069)), F3 @ Vector((0, 0, 1)), g, 0.007)
    for j in range(8):
        a = random.uniform(0, 2 * PI)
        caixa(B('lama_pe', 'lama', False, g), FW((math.cos(a) * 0.111, math.sin(a) * 0.111, -0.085)), (0.03, 0.004, 0.026),
              F3 @ Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(PI / 2, 3, 'Z'))
    cil(B('estaca_camisa', 'amarelo', True, g), FW((0.075, 0, -0.01)), 0.026, 0.12, F3 @ Vector((0, 0, 1)), lados=20)
    cil(B('estaca_tampa', 'ferro', True, g), FW((0.075, 0, 0.055)), 0.03, 0.014, F3 @ Vector((0, 0, 1)), lados=20)
    cil(B('estaca_bucha', 'ferro', True, g), FW((0.075, 0, -0.072)), 0.03, 0.012, F3 @ Vector((0, 0, 1)), lados=20)
    pts = [Vector((0.06, 0, 0.045)), Vector((0.2, 0, 0.07)), Vector((L - 0.05, 0, 0.07)), FW((0.075, 0.02, 0.04))]
    mangueira(B('mangueira_perna', 'borracha', True, g), bezier(*pts, 12), 0.008)
    for x in (0.18, 0.33):
        caixa(B('abracadeira_perna', 'aco', False, g), Vector((x, 0, 0.05)), (0.012, 0.03, 0.03))
    # estaca (desce e crava)
    e = novo_vazio('estaca%d' % k, pe)
    e.rotation_mode = 'QUATERNION'
    e.rotation_quaternion = F3.to_quaternion()
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.0)), 0.012, 0.2, lados=14)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.0, radius2=0.012, depth=0.04,
                          matrix=Matrix.Translation((0, 0, -0.12)))
    suavizar(obj('estaca%d_haste' % k, bm, 'cromo', e))
    estacas.append((e, FW((0.075, 0, 0.02))))

# ------------------------------------------------------------------ trava de transporte (leste)
caixa_de(B('trava_luva', 'amarelo'), (POST_X - 0.035, -0.035, 0.15), (POST_X + 0.035, 0.035, 0.62))
caixa_de(B('trava_luva_boca', 'ferro'), (POST_X - 0.042, -0.042, 0.6), (POST_X + 0.042, 0.042, 0.625))
for z in (0.25, 0.45):
    caixa_de(B('trava_suporte', 'ferro'), (0.43, -0.05, z - 0.02), (POST_X - 0.035, 0.05, z + 0.02))
    for s in (-1, 1):
        parafuso((0.441, s * 0.04, z), (1, 0, 0), r=0.008)
caixa_de(B('trava_listras', 'listras'), (POST_X + 0.0355, -0.03, 0.5), (POST_X + 0.037, 0.03, 0.58))
pts = bezier(Vector((POST_X, -0.036, 0.2)), Vector((POST_X, -0.07, 0.2)), Vector((0.46, -0.12, 0.3)), Vector((0.44, -0.12, 0.33)), 8)
mangueira(B('mangueira_trava', 'borracha', True), pts, 0.008)
post = novo_vazio('trava_poste')
Z_POST0 = Z_PT(0) + TZ - 0.085           # pino das mandíbulas (canos na posição de transporte)
bm = bmesh.new()
caixa_de(bm, (-0.026, -0.026, -0.44), (0.026, 0.026, -0.01))
caixa_de(bm, (-0.03, -0.03, -0.03), (0.03, 0.03, 0.0))
obj('trava_poste_haste', bm, 'cromo', post)
bm = bmesh.new()
for s in (-1, 1):
    caixa_de(bm, (-0.03, s * 0.012 - 0.006, -0.01), (0.03, s * 0.012 + 0.006, 0.02))
cil(bm, Vector((0, 0, 0.0)), 0.008, 0.07, Vector((1, 0, 0)), lados=10)
obj('trava_poste_pino', bm, 'aco', post)
mandibulas = []
for s in (1, -1):
    j = novo_vazio('mandibula', post)
    bm = bmesh.new()
    a0, a1 = (-PI / 2, PI / 2) if s > 0 else (PI / 2, 3 * PI / 2)
    n = 14
    Ri, Re = 0.068, 0.085
    ring = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        ring.append([bm.verts.new((x, R * math.cos(a), 0.085 + R * math.sin(a))) for x, R in ((-0.018, Ri), (-0.018, Re), (0.018, Re), (0.018, Ri))])
    for i in range(n):
        A, Bq = ring[i], ring[i + 1]
        for m in range(4):
            bm.faces.new((A[m], A[(m + 1) % 4], Bq[(m + 1) % 4], Bq[m]))
    bm.faces.new(ring[0])
    bm.faces.new(list(reversed(ring[-1])))
    obj('mandibula_aco', bm, 'amarelo', j)
    bm = bmesh.new()
    for i in range(4):
        a = a0 + (a1 - a0) * (i + 0.5) / 4
        caixa(bm, Vector((0, (Ri - 0.002) * math.cos(a), 0.085 + (Ri - 0.002) * math.sin(a))), (0.034, 0.012, 0.006), Matrix.Rotation(a + PI / 2, 3, 'X'))
    obj('mandibula_borracha', bm, 'borracha', j)
    j.rotation_mode = 'XYZ'
    mandibulas.append((j, s))

# ------------------------------------------------------------------ carregador (boca sul S1)
bm = B('esteira_lado', 'amarelo')
for sx in (-1, 1):
    caixa_de(bm, (BX + sx * 0.13 - 0.01, -0.975, 0.12), (BX + sx * 0.13 + 0.01, -0.80, 0.25))
caixa_de(B('esteira_lona', 'borracha'), (BX - 0.12, -0.97, 0.175), (BX + 0.12, -0.80, 0.2))
for y in (-0.95, -0.82):
    cil(B('esteira_rolo', 'aco', True), Vector((BX, y, 0.187)), 0.02, 0.25, Vector((1, 0, 0)), lados=16)
    for sx in (-1, 1):
        caixa_de(B('esteira_pe', 'ferro'), (BX + sx * 0.13 - 0.015, y - 0.02, Z0), (BX + sx * 0.13 + 0.015, y + 0.02, 0.12))
caixa_de(B('boca_listras', 'listras'), (BX - 0.16, -0.985, 0.25), (BX + 0.16, -0.955, 0.28))
for sx in (-1, 1):
    caixa_de(B('esteira_lado', 'amarelo'), (BX + sx * 0.16 - 0.015, -0.985, 0.12), (BX + sx * 0.16 + 0.015, -0.955, 0.28))
cil(B('esteira_motor', 'grafite', True), Vector((BX - 0.19, -0.95, 0.187)), 0.04, 0.09, Vector((1, 0, 0)), lados=16)
# empurrador hidráulico (leste da esteira) que joga a caixa para o elevador
cil(B('empurrador_camisa', 'amarelo', True), Vector((0.75, -0.86, 0.27)), 0.032, 0.2, Vector((1, 0, 0)), lados=20)
cil(B('empurrador_tampa', 'ferro', True), Vector((0.855, -0.86, 0.27)), 0.037, 0.016, Vector((1, 0, 0)), lados=20)
for x in (0.68, 0.82):
    caixa_de(B('empurrador_pe', 'ferro'), (x - 0.015, -0.88, Z0), (x + 0.015, -0.84, 0.245))
pts = bezier(Vector((0.84, -0.83, 0.29)), Vector((0.84, -0.78, 0.36)), Vector((0.66, -0.76, 0.36)), Vector((0.66, -0.828, 0.29)), 8)
mangueira(B('mangueira_emp', 'borracha', True), pts, 0.007)
empurrador = novo_vazio('empurrador')
bm = bmesh.new()
cil(bm, Vector((0.09, 0, 0)), 0.014, 0.3, Vector((1, 0, 0)), lados=14)
obj('empurrador_haste', bm, 'cromo', empurrador)
bm = bmesh.new()
caixa_de(bm, (-0.07, -0.06, -0.06), (-0.055, 0.06, 0.06))
obj('empurrador_placa', bm, 'ferro', empurrador)
# elevador de caixas
EX0, EX1, EY0, EY1 = 0.10, 0.36, -0.95, -0.68
caixa_de(B('elevador', 'amarelo'), (EX0, EY0, Z0), (EX1 - 0.02, EY1, 0.62))
for a_, b_ in (((EX1 - 0.02, EY0, Z0), (EX1, -0.93, 0.62)), ((EX1 - 0.02, -0.79, Z0), (EX1, EY1, 0.62)),
               ((EX1 - 0.02, -0.93, Z0), (EX1, -0.79, 0.19)), ((EX1 - 0.02, -0.93, 0.38), (EX1, -0.79, 0.62))):
    caixa_de(B('elevador', 'amarelo'), a_, b_)
caixa_de(B('elevador_boca', 'escuro'), (EX1 - 0.05, -0.93, 0.19), (EX1 - 0.019, -0.79, 0.38))
for y in (-0.935, -0.785):
    caixa_de(B('elevador_quadro', 'ferro'), (EX1, y - 0.01, 0.18), (EX1 + 0.014, y + 0.01, 0.39))
caixa_de(B('elevador_quadro', 'ferro'), (EX1, -0.945, 0.38), (EX1 + 0.014, -0.775, 0.4))
caixa_de(B('elevador_listras', 'listras'), (EX1, -0.93, 0.41), (EX1 + 0.004, -0.79, 0.45))
caixa_de(B('elevador_tampa', 'ferro'), (EX0 - 0.01, EY0 - 0.01, 0.62), (EX1 + 0.01, EY1 + 0.01, 0.64))
cil(B('elevador_motor', 'grafite', True), Vector((0.23, -0.86, 0.7)), 0.05, 0.12, lados=20)
for j in range(4):
    cil(B('elevador_motor_aletas', 'ferro', True), Vector((0.23, -0.86, 0.66 + j * 0.025)), 0.056, 0.006, lados=20)
caixa_de(B('elevador_redutor', 'amarelo'), (0.16, -0.9, 0.64), (0.3, -0.76, 0.68))
for x in (EX0 + 0.02, EX1 - 0.04):
    for y in (EY0 + 0.02, EY1 - 0.02):
        parafuso((x, y, 0.645), (0, 0, 1), r=0.008)
for k in range(4):
    caixa_de(B('elevador_lama', 'lama'), (EX0 + 0.05 * k, EY0 - 0.003, Z0), (EX0 + 0.05 * k + 0.035, EY0, Z0 + random.uniform(0.04, 0.1)))
caixa_de(B('elevador_janela', 'escuro'), (EX0 - 0.003, -0.9, 0.24), (EX0, -0.73, 0.5))
for z in (0.235, 0.505):
    caixa_de(B('elevador_quadro', 'ferro'), (EX0 - 0.014, -0.905, z - 0.01), (EX0, -0.725, z + 0.01))
for y in (-0.86, -0.82, -0.78):
    tubo(B('elevador_grade', 'aco'), (EX0 - 0.006, y, 0.24), (EX0 - 0.006, y, 0.5), 0.003, 6)
# duto do elevador até o casco (face sul)
caixa_de(B('duto', 'amarelo'), (0.17, EY1, 0.42), (0.29, -0.435, 0.54))
for y in (-0.62, -0.5):
    caixa_de(B('duto_cinta', 'ferro'), (0.16, y - 0.01, 0.41), (0.30, y + 0.01, 0.55))
caixa_de(B('duto_flange', 'ferro'), (0.15, -0.45, 0.4), (0.31, -0.435, 0.56))
for x in (0.16, 0.3):
    for z in (0.41, 0.55):
        parafuso((x, -0.452, z), (0, -1, 0), r=0.007)
# caixas de munição comum chegando pela esteira
def caixa_municao(nome):
    e = novo_vazio(nome)
    bm = bmesh.new()
    caixa_de(bm, (-0.11, -0.07, 0.0), (0.11, 0.07, 0.15))
    obj(nome + '_corpo', bm, 'oliva', e)
    bm = bmesh.new()
    caixa_de(bm, (-0.115, -0.075, 0.15), (0.115, 0.075, 0.175))
    obj(nome + '_tampa', bm, 'grafite', e)
    bm = bmesh.new()
    for s in (-1, 1):
        caixa_de(bm, (s * 0.111 - 0.002, -0.03, 0.12), (s * 0.111 + 0.002 * s + 0.002, 0.03, 0.17))
    caixa_de(bm, (-0.112, -0.071, 0.06), (0.112, 0.071, 0.08))
    obj(nome + '_fechos', bm, 'aco', e)
    bm = bmesh.new()
    caixa_de(bm, (-0.06, -0.0712, 0.09), (0.06, -0.07, 0.11))
    obj(nome + '_faixa', bm, 'listras', e)
    return e


caixas_mun = [caixa_municao('caixa_municao%d' % k) for k in range(2)]

# ------------------------------------------------------------------ elevador da cabeça (mastro, cabeçote, coroa fixa)
elev = novo_vazio('elevador_cabeca')
EV = 'elev'
chanfro(B('cabecote', 'grafite', False, EV), 0.35, 0.10, -PLATE_T, 0.0)
caixa_de(B('mastro', 'aco', False, EV), (-0.13, -0.13, -PLATE_T - 0.48), (0.13, 0.13, -PLATE_T))
for s in (-1, 1):                                                      # trilhos-guia do mastro
    caixa_de(B('mastro_guia', 'ferro', False, EV), (-0.03, s * 0.13 - 0.008, -PLATE_T - 0.48), (0.03, s * 0.13 + 0.008, -PLATE_T))
    caixa_de(B('mastro_guia', 'ferro', False, EV), (s * 0.13 - 0.008, -0.03, -PLATE_T - 0.48), (s * 0.13 + 0.008, 0.03, -PLATE_T))
z_furo = Z_COV + 0.025 - Z_PT(LIFT)
for s in (-1, 1):
    caixa_de(B('mastro_furo', 'escuro', False, EV), (s * 0.1305 - 0.001, -0.016, z_furo - 0.016), (s * 0.1305 + 0.001, 0.016, z_furo + 0.016))
for j in range(5):
    caixa_de(B('mastro_oleo', 'oleo', False, EV), (0.1305, -0.11 + j * 0.04, -PLATE_T - random.uniform(0.15, 0.3)), (0.1312, -0.105 + j * 0.04, -PLATE_T - 0.01))
for s in (-1, 1):                                                      # hastes de elevação
    cil(B('hastes', 'cromo', True, EV), Vector((0, s * 0.22, -PLATE_T - 0.2)), 0.022, 0.4, lados=18)
    cil(B('hastes_olhal', 'ferro', True, EV), Vector((0, s * 0.22, -PLATE_T - 0.015)), 0.034, 0.03, lados=18)
    cil(B('gaxeta', 'ferro', True), Vector((0, s * 0.22, Z_COV + 0.01)), 0.036, 0.02, lados=18)
    cil(B('gaxeta', 'borracha', True), Vector((0, s * 0.22, Z_COV + 0.022)), 0.028, 0.006, lados=18)
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(B('batentes', 'borracha', True), Vector((sx * 0.27, sy * 0.24, Z_COV + GAP / 2)), 0.03, GAP, lados=16)
        cil(B('batentes_base', 'ferro', True), Vector((sx * 0.27, sy * 0.24, Z_COV + 0.006)), 0.04, 0.012, lados=16)
engrenagem(B('coroa', 'aco', True, EV), (0, 0, 0.025), R_COROA, 0.05, 84, Vector((0, 0, 1)))
for k in range(28):
    a = k * 2 * PI / 28
    d = Vector((math.cos(a), math.sin(a), 0))
    s = 0.32 / max(abs(d.x), abs(d.y), (abs(d.x) + abs(d.y)) * 0.32 / (2 * 0.32 - 0.1))
    parafuso(d * s + Vector((0, 0, 0.005)), (0, 0, 1), EV, 0.009)
for s in (-1, 1):
    caixa_de(B('cabecote_listras', 'listras', False, EV), (-0.25, s * 0.3505 - 0.002, -PLATE_T + 0.008), (0.25, s * 0.3505 + 0.002, -0.008))
for k in range(6):
    mancha(B('graxa', 'oleo', False, EV), (random.uniform(-0.3, 0.3), random.choice((-1, 1)) * random.uniform(0.29, 0.32)), random.uniform(0.015, 0.03), 0.0012)
# ferrolhos (travam o mastro em cima)
ferrolhos = []
for s in (-1, 1):
    caixa_de(B('ferrolho_bloco', 'amarelo'), (s * 0.19 - 0.03, -0.035, Z_COV), (s * 0.19 + 0.03 + 0.015 * s, 0.035, Z_COV + 0.05))
    cil(B('ferrolho_cil', 'ferro', True), Vector((s * 0.255, 0, Z_COV + 0.025)), 0.018, 0.06, Vector((1, 0, 0)), lados=14)
    f = novo_vazio('ferrolho', None)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.012, 0.09, Vector((1, 0, 0)), lados=12)
    obj('ferrolho_pino', bm, 'cromo', f)
    ferrolhos.append((f, s))
# cabo espiral de força (cobertura → cabeçote) com chave de forma
def espiral(comp, raio=0.025, voltas=9, r=0.0055, n=10):
    pts = []
    N = voltas * 16
    for i in range(N + 1):
        a = i * 2 * PI / 16
        pts.append(Vector((raio * math.cos(a), raio * math.sin(a), 0.012 + (comp - 0.024) * i / N)))
    co = []
    for i, p in enumerate(pts):
        u = (pts[min(i + 1, N)] - pts[max(i - 1, 0)]).normalized()
        a = u.cross(Vector((0, 0, 1))).normalized()
        b = u.cross(a)
        co.extend([p + (a * math.cos(t) + b * math.sin(t)) * r for t in (j * 2 * PI / n for j in range(n))])
    return co, N + 1, n


co0, NR, NN = espiral(GAP)
co1, _, _ = espiral(GAP + LIFT)
me = bpy.data.meshes.new('cabo_espiral')
faces = [(i * NN + j, i * NN + (j + 1) % NN, (i + 1) * NN + (j + 1) % NN, (i + 1) * NN + j) for i in range(NR - 1) for j in range(NN)]
me.from_pydata([tuple(c) for c in co0], [], faces)
cabo_esp = bpy.data.objects.new('cabo_espiral', me)
sc.collection.objects.link(cabo_esp)
me.materials.append(base3d.M['cabo'])
for pg in me.polygons:
    pg.use_smooth = True
cabo_esp.location = (-0.3, 0.06, Z_COV)
cabo_esp.shape_key_add(name='Base')
sk = cabo_esp.shape_key_add(name='Esticado')
for i, c in enumerate(co1):
    sk.data[i].co = c
for z in (Z_COV, Z_COV + 0.003):
    cil(B('cabo_prensa', 'ferro', True), Vector((-0.3, 0.06, z + 0.006)), 0.035, 0.012, lados=16)

# ------------------------------------------------------------------ giro (cabeça)
giro = novo_vazio('giro', elev)
G = 'giro'
cil(B('mesa', 'ferro', True, G), Vector((0, 0, 0.07)), 0.26, 0.04, lados=64)
for k in range(20):
    a = k * 2 * PI / 20
    parafuso((math.cos(a) * 0.235, math.sin(a) * 0.235, 0.092), (0, 0, 1), G, 0.009)
PERFIL_GARFO = [(-0.14, 0.09), (0.14, 0.09), (0.14, 0.30), (0.08, 0.42), (-0.08, 0.42), (-0.14, 0.34)]
for s in (-1, 1):
    y0, y1 = (0.13, 0.17) if s > 0 else (-0.17, -0.13)
    prisma_xz(B('garfo', 'amarelo', False, G), PERFIL_GARFO, y0, y1)
    yo = s * 0.172
    for x, z in ((-0.11, 0.13), (0.11, 0.13), (-0.11, 0.3), (0.11, 0.26), (0.0, 0.4), (-0.06, 0.4), (0.06, 0.4)):
        parafuso((x, yo, z), (0, s, 0), G, 0.009)
    cil(B('mancal', 'ferro', True, G), Vector((0, s * 0.175, TZ)), 0.055, 0.02, Vector((0, 1, 0)), lados=28)
    caixa_de(B('garfo_pe', 'ferro', False, G), (-0.16, y0 - 0.02, 0.09), (0.16, y1 + 0.02, 0.11))
    for k in range(4):                                                 # fuligem e lascas no garfo
        caixa(B('fuligem_garfo', 'chamusco', False, G), Vector((random.uniform(0.0, 0.13), s * 0.1715, random.uniform(0.2, 0.38))),
              (random.uniform(0.02, 0.05), 0.002, random.uniform(0.02, 0.06)))
caixa_de(B('garfo_listras', 'listras', False, G), (-0.14, -0.172, 0.12), (-0.04, -0.17, 0.15))
# motor de giro (anda com a cabeça) e pinhão rolando na coroa fixa
caixa_de(B('braco_motor', 'ferro', False, G), (-0.05, -0.37, 0.05), (0.05, -0.22, 0.075))
cil(B('motor_giro', 'grafite', True, G), Vector((0, -0.32, 0.135)), 0.045, 0.12, lados=24)
for j in range(4):
    cil(B('motor_giro_aletas', 'ferro', True, G), Vector((0, -0.32, 0.1 + j * 0.025)), 0.051, 0.006, lados=24)
cil(B('motor_giro_tampa', 'ferro', True, G), Vector((0, -0.32, 0.2)), 0.047, 0.012, lados=24)
caixa_de(B('motor_giro_caixa', 'grafite', False, G), (0.04, -0.35, 0.11), (0.08, -0.29, 0.17))
pts = bezier(Vector((0.06, -0.29, 0.17)), Vector((0.06, -0.24, 0.2)), Vector((0.05, -0.2, 0.1)), Vector((0.05, -0.18, 0.095)), 8)
mangueira(B('cabos', 'cabo', True, G), pts, 0.008)
pin_giro = novo_vazio('pinhao_giro', giro, (0, -0.32, 0.025))
bm = bmesh.new()
engrenagem(bm, (0, 0, 0), R_PIN, 0.05, 12, Vector((0, 0, 1)))
obj('pinhao_giro_dentes', bm, 'aco', pin_giro)
# motor e engrenagem de elevação (lado −y, por fora do garfo)
EP = Vector((-0.067, -0.19, TZ - 0.067))
cil(B('motor_elev', 'grafite', True, G), Vector((EP.x, -0.245, EP.z)), 0.03, 0.09, Vector((0, 1, 0)), lados=20)
cil(B('motor_elev_tampa', 'ferro', True, G), Vector((EP.x, -0.293, EP.z)), 0.032, 0.012, Vector((0, 1, 0)), lados=20)
caixa_de(B('motor_elev_sela', 'ferro', False, G), (EP.x - 0.035, -0.29, EP.z - 0.05), (EP.x + 0.035, -0.17, EP.z - 0.03))
pin_elev = novo_vazio('pinhao_elevacao', giro, EP)
bm = bmesh.new()
engrenagem(bm, (0, 0, 0), R_PE, 0.016, 10, Vector((0, 1, 0)))
obj('pinhao_elev_dentes', bm, 'aco', pin_elev)
# caixa de munição (+y) com boca de roletes
caixa_de(B('cx_mun', 'oliva', False, G), (-0.25, 0.19, 0.10), (0.05, 0.40, 0.33))
caixa_de(B('cx_mun_tampa', 'grafite', False, G), (-0.255, 0.185, 0.33), (0.055, 0.405, 0.345))
for x in (-0.22, 0.02):
    caixa_de(B('cx_mun_cinta', 'ferro', False, G), (x - 0.012, 0.186, 0.098), (x + 0.012, 0.404, 0.335))
for x in (-0.18, -0.02):
    cil(B('cx_mun_dobradica', 'aco', True, G), Vector((x, 0.405, 0.335)), 0.008, 0.05, Vector((1, 0, 0)), lados=10)
for x in (-0.256, 0.05):
    for z in (0.14, 0.29):
        caixa_de(B('cx_mun_fecho', 'aco', False, G), (x, 0.28, z - 0.015), (x + 0.006, 0.31, z + 0.015))
caixa_de(B('cx_mun_faixa', 'listras', False, G), (-0.2, 0.4005, 0.2), (-0.04, 0.403, 0.24))
caixa_de(B('cx_mun_remendo', 'remendo', False, G), (-0.17, 0.403, 0.12), (-0.07, 0.407, 0.18))
for x in (-0.16, -0.08):
    for z in (0.13, 0.17):
        parafuso((x, 0.41, z), (0, 1, 0), G, 0.006)
for j in range(6):
    caixa_de(B('cx_mun_marca', 'escuro', False, G), (-0.2 + j * 0.022, 0.401, 0.27), (-0.188 + j * 0.022, 0.4025, 0.29))
caixa_de(B('cx_mun_boca', 'ferro', False, G), (-0.18, 0.26, 0.345), (-0.06, 0.34, 0.37))
caixa_de(B('cx_mun_boca_fundo', 'escuro', False, G), (-0.17, 0.285, 0.369), (-0.07, 0.315, 0.371))
for y in (0.278, 0.322):
    cil(B('cx_mun_roletes', 'aco', True, G), Vector((-0.12, y, 0.38)), 0.009, 0.12, Vector((1, 0, 0)), lados=12)
    for s in (-1, 1):
        caixa_de(B('cx_mun_mao', 'ferro', False, G), (-0.12 + s * 0.062 - 0.004, y - 0.01, 0.37), (-0.12 + s * 0.062 + 0.004, y + 0.01, 0.39))
caixa_de(B('cx_mun_suporte', 'ferro', False, G), (-0.2, 0.17, 0.2), (-0.15, 0.19, 0.26))
caixa_de(B('cx_mun_suporte', 'ferro', False, G), (-0.05, 0.17, 0.2), (0.0, 0.19, 0.26))
viga(B('cx_mun_suporte', 'ferro', False, G), Vector((-0.1, 0.2, 0.09)), Vector((-0.1, 0.3, 0.1)), 0.02)
caixa_de(B('cx_mun_berco', 'ferro', False, G), (-0.24, 0.2, 0.09), (0.04, 0.39, 0.1))
# casulo sensor da IA (em cima do garfo −y) com olho e radar
SP0, SP1 = Vector((-0.11, -0.23, 0.425)), Vector((0.05, -0.125, 0.52))
caixa_de(B('sensor', 'grafite', False, G), SP0, SP1)
caixa_de(B('sensor_viseira', 'ferro', False, G), (0.0, -0.235, 0.52), (0.07, -0.12, 0.532))
caixa_de(B('sensor_pe', 'ferro', False, G), (-0.09, -0.2, 0.42), (0.03, -0.14, 0.426))
cil(B('sensor_lente', 'ferro', True, G), Vector((0.06, -0.178, 0.47)), 0.036, 0.03, Vector((1, 0, 0)), lados=28)
toro(B('sensor_aro', 'cromo', True, G), Vector((0.075, -0.178, 0.47)), 0.031, 0.005, 32, 8, ROT_X)
olho_o = None
cil(B('sensor_olho', 'olho', False, G), Vector((0.0755, -0.178, 0.47)), 0.025, 0.003, Vector((1, 0, 0)), lados=28)
for k, m in enumerate(('led_verde', 'led_ambar', 'led_verm')):
    cil(B('led_' + m, m, False, G), Vector((0.051, -0.215 + k * 0.012, 0.44)), 0.004, 0.004, Vector((1, 0, 0)), lados=10)
cil(B('radar_base', 'ferro', True, G), Vector((-0.07, -0.178, 0.535)), 0.022, 0.03, lados=16)
pts = bezier(Vector((-0.11, -0.2, 0.46)), Vector((-0.15, -0.2, 0.46)), Vector((-0.17, -0.18, 0.2)), Vector((-0.17, -0.16, 0.11)), 10)
feixe(B('cabos', 'cabo', True, G), B('abracadeiras', 'aco', True, G), pts, Vector((1, 0, 0)), n=2, r=0.007, passo=4)
radar = novo_vazio('radar', giro, (-0.07, -0.178, 0.55))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.02)), 0.006, 0.04, lados=10)
caixa(bm, Vector((0, 0, 0.045)), (0.012, 0.12, 0.03))
for s in (-1, 1):
    caixa(bm, Vector((0.008, s * 0.05, 0.045)), (0.006, 0.02, 0.035))
obj('radar_pa', bm, 'grafite', radar)
bm = bmesh.new()
caixa(bm, Vector((0.007, 0, 0.045)), (0.002, 0.1, 0.02))
obj('radar_face', bm, 'aco', radar)
antena_led = None
tubo(B('antena', 'aco', True, G), (-0.12, 0.15, 0.42), (-0.12, 0.15, 0.62), 0.004, 8)
curva(B('antena_led', 'led_ambar', True, G), Vector((-0.12, 0.15, 0.625)), 0.008, 10)
cil(B('antena_base', 'ferro', True, G), Vector((-0.12, 0.15, 0.415)), 0.016, 0.025, lados=12)
# cabos do giro: mesa → motor de elevação e munhão
pts = bezier(Vector((0.05, -0.2, 0.095)), Vector((0.06, -0.26, 0.15)), Vector((EP.x + 0.02, -0.3, EP.z - 0.08)), Vector((EP.x, -0.3, EP.z - 0.02)), 8)
mangueira(B('cabos', 'cabo', True, G), pts, 0.007)

# ------------------------------------------------------------------ canhão (inclina) e tambor (gira)
canhao = novo_vazio('canhao', giro, (0, 0, TZ))
K = 'canhao'
caixa_de(B('culatra', 'grafite', False, K), (-0.30, -0.11, -0.10), (0.10, 0.11, 0.10))
for x in (-0.27, 0.07):
    caixa_de(B('culatra_cinta', 'aco', False, K), (x - 0.012, -0.114, -0.104), (x + 0.012, 0.114, 0.104))
cil(B('munhao', 'aco', True, K), Vector((0, 0, 0)), 0.04, 0.4, Vector((0, 1, 0)), lados=24)
caixa_de(B('culatra_tampa', 'amarelo', False, K), (-0.24, -0.1145, -0.07), (-0.04, -0.111, 0.06))
for x in (-0.23, -0.05):
    for z in (-0.06, 0.05):
        parafuso((x, -0.116, z), (0, -1, 0), K, 0.007)
caixa_de(B('culatra_listras', 'listras', False, K), (-0.3, 0.1105, -0.09), (-0.2, 0.114, -0.06))
for j in range(8):                                                     # respiros
    caixa_de(B('culatra_fenda', 'escuro', False, K), (-0.28 + j * 0.022, -0.06, 0.1), (-0.27 + j * 0.022, 0.03, 0.1015))
caixa_de(B('culatra_traseira', 'ferro', False, K), (-0.315, -0.09, -0.08), (-0.3, 0.09, 0.08))
for sy in (-1, 1):
    for sz in (-1, 1):
        parafuso((-0.318, sy * 0.07, sz * 0.06), (-1, 0, 0), K, 0.008)
cil(B('led_led_verde', 'led_verde', False, K), Vector((-0.317, 0.0, 0.05)), 0.006, 0.004, Vector((1, 0, 0)), lados=10)
cil(B('led_led_ambar', 'led_ambar', False, K), Vector((-0.317, 0.02, 0.05)), 0.006, 0.004, Vector((1, 0, 0)), lados=10)
# engrenagem de elevação no munhão (−y)
engrenagem(B('engr_elev', 'aco', True, K), (0, -0.19, 0), R_GE, 0.016, 26, Vector((0, 1, 0)))
# motor do tambor em cima da culatra, pinhão engrenado na coroa do tambor
cil(B('motor_tambor', 'grafite', True, K), Vector((-0.07, 0, 0.145)), 0.042, 0.26, Vector((1, 0, 0)), lados=24)
for j in range(6):
    cil(B('motor_tambor_aletas', 'ferro', True, K), Vector((-0.17 + j * 0.03, 0, 0.145)), 0.048, 0.006, Vector((1, 0, 0)), lados=24)
cil(B('motor_tambor_tampa', 'ferro', True, K), Vector((-0.205, 0, 0.145)), 0.044, 0.014, Vector((1, 0, 0)), lados=24)
cil(B('motor_tambor_eixo', 'aco', True, K), Vector((0.1, 0, 0.145)), 0.012, 0.08, Vector((1, 0, 0)), lados=12)
for x in (-0.15, 0.0):
    caixa_de(B('motor_tambor_sela', 'ferro', False, K), (x - 0.015, -0.035, 0.1), (x + 0.015, 0.035, 0.12))
caixa_de(B('motor_tambor_caixa', 'grafite', False, K), (-0.12, -0.075, 0.12), (-0.06, -0.04, 0.17))
pts = bezier(Vector((-0.09, -0.075, 0.13)), Vector((-0.09, -0.12, 0.13)), Vector((-0.02, -0.125, 0.02)), Vector((0.0, -0.115, 0.0)), 8)
mangueira(B('cabos', 'cabo', True, K), pts, 0.007)
for k in range(4):
    caixa(B('oleo_motor', 'oleo', False, K), Vector((random.uniform(-0.15, 0.0), -0.111, random.uniform(-0.02, 0.06))), (0.006, 0.002, random.uniform(0.04, 0.09)))
pin_tambor = novo_vazio('pinhao_tambor', canhao, (0.135, 0, 0.145))
pin_tambor.rotation_mode = 'XYZ'
bm = bmesh.new()
engrenagem(bm, (0, 0, 0), R_PT, 0.03, 12, Vector((1, 0, 0)))
obj('pinhao_tambor_dentes', bm, 'aco', pin_tambor)
# bandeja de alimentação (+y em cima da culatra)
caixa_de(B('bandeja', 'ferro', False, K), (-0.175, 0.05, 0.1), (-0.065, 0.125, 0.112))
caixa_de(B('bandeja_capuz', 'amarelo', False, K), (-0.18, 0.045, 0.145), (-0.06, 0.105, 0.155))
for x in (-0.18, -0.07):
    caixa_de(B('bandeja_capuz', 'amarelo', False, K), (x, 0.045, 0.1), (x + 0.01, 0.105, 0.155))
caixa_de(B('bandeja_listras', 'listras', False, K), (-0.18, 0.06, 0.155), (-0.06, 0.1, 0.157))
# calha de cápsulas e calha de elos (saem por baixo, para −y, atrás do garfo)
bm = B('calhas', 'ferro', False, K)
for x0, x1, P in ((-0.235, -0.185, PORTA_C), (-0.295, -0.255, PORTA_E)):
    pts = [Vector(((x0 + x1) / 2, -0.04, -0.1)), Vector(((x0 + x1) / 2, P.y + 0.03, P.z + 0.02))]
    u = (pts[1] - pts[0])
    for s in (-1, 1):
        a = pts[0] + Vector((s * (x1 - x0) / 2, 0, 0))
        b = pts[1] + Vector((s * (x1 - x0) / 2, 0, 0))
        viga(bm, a, b, 0.006)
    caixa(bm, (pts[0] + pts[1]) / 2 + Vector((0, 0.008, -0.015)), (x1 - x0, 0.004, u.length),
          Matrix.Rotation(math.atan2(u.y, -u.z) if False else -math.atan2(-u.y, -u.z), 3, 'X'))
caixa_de(B('calha_fuligem', 'chamusco', False, K), (-0.24, -0.08, -0.101), (-0.18, -0.02, -0.1))
# escudo blindado amassado
CEL = 0.015
NY, NZ = 36, 32
Y_ESC, Z_ESC = -0.27, -0.18
AMASSADOS = [(-0.17, 0.2, 0.025, 0.012), (0.12, -0.12, 0.02, 0.01), (0.2, 0.12, 0.03, 0.013), (-0.05, 0.22, 0.018, 0.008),
             (-0.2, -0.08, 0.022, 0.01), (0.04, -0.15, 0.015, 0.008), (0.15, 0.24, 0.02, 0.009), (-0.11, -0.15, 0.03, 0.006)]


def X_esc(y, z):
    x = 0.205
    if abs(y) > 0.19:
        x -= (abs(y) - 0.19) * 0.75
    if z > 0.22:
        x -= (z - 0.22) * 0.7
    for yc, zc, R, d in AMASSADOS:
        x -= d * math.exp(-((y - yc) ** 2 + (z - zc) ** 2) / (R * R))
    x += 0.001 * math.sin(y * 37 + z * 11) * math.sin(z * 23)
    return x


def mantem(i, j):
    yc, zc = Y_ESC + (i + 0.5) * CEL, Z_ESC + (j + 0.5) * CEL
    return not (abs(yc) < 0.09 and abs(zc) < 0.09)


bm = B('escudo', 'amarelo_escudo', False, K)
F_, Bk = {}, {}
for i in range(NY + 1):
    for j in range(NZ + 1):
        y, z = Y_ESC + i * CEL, Z_ESC + j * CEL
        x = X_esc(y, z)
        F_[i, j] = bm.verts.new((x, y, z))
        Bk[i, j] = bm.verts.new((x - 0.014, y, z))
for i in range(NY):
    for j in range(NZ):
        if not mantem(i, j):
            continue
        bm.faces.new((F_[i, j], F_[i + 1, j], F_[i + 1, j + 1], F_[i, j + 1]))
        bm.faces.new((Bk[i, j + 1], Bk[i + 1, j + 1], Bk[i + 1, j], Bk[i, j]))
        for (di, dj), (a, b) in (((-1, 0), ((i, j + 1), (i, j))), ((1, 0), ((i + 1, j), (i + 1, j + 1))),
                                 ((0, -1), ((i, j), (i + 1, j))), ((0, 1), ((i + 1, j + 1), (i, j + 1)))):
            ii, jj = i + di, j + dj
            if not (0 <= ii < NY and 0 <= jj < NZ and mantem(ii, jj)):
                bm.faces.new((F_[a], Bk[a], Bk[b], F_[b]))
for yc, zc, R, d in AMASSADOS:                                         # marcas de impacto (metal nu e queimado)
    x = X_esc(yc, zc) + 0.0008
    cil(B('impacto', 'aco', False, K), Vector((x, yc, zc)), R * 0.32, 0.002, Vector((1, 0, 0)), lados=12)
    toro(B('impacto_queimado', 'chamusco', False, K), Vector((x - 0.0005, yc, zc)), R * 0.55, R * 0.12, 16, 5, ROT_X)
    for m in range(3):
        a = random.uniform(0, 2 * PI)
        caixa(B('impacto_risco', 'aco', False, K), Vector((x - 0.0003, yc + math.cos(a) * R * 0.8, zc + math.sin(a) * R * 0.8)),
              (0.002, R * 0.6, 0.002), Matrix.Rotation(a + PI / 2, 3, 'X'))
yc, zc = -0.04, -0.14                                                   # remendo aparafusado no escudo
xr = X_esc(yc, zc) + 0.004
caixa(B('escudo_remendo', 'remendo', False, K), Vector((xr, yc, zc)), (0.008, 0.12, 0.06))
for sy in (-1, 1):
    for sz in (-1, 1):
        parafuso((xr + 0.004, yc + sy * 0.05, zc + sz * 0.022), (1, 0, 0), K, 0.007)
for sy in (-1, 1):                                                      # parafusos da borda e da janela
    for z in (-0.15, 0.0, 0.15):
        parafuso((X_esc(sy * 0.17, z) + 0.004, sy * 0.17, z), (1, 0, 0), K, 0.008)
    for z in (-0.105, 0.105):
        parafuso((X_esc(sy * 0.105, z) + 0.004, sy * 0.105, z), (1, 0, 0), K, 0.007)
for j in range(10):                                                     # escorridos de ferrugem no escudo
    y = random.uniform(-0.18, 0.18)
    z = random.uniform(-0.05, 0.2)
    if abs(y) < 0.1 and abs(z) < 0.1:
        continue
    L = random.uniform(0.04, 0.1)
    caixa(B('escudo_ferrugem', 'ferrugem', False, K), Vector((X_esc(y, z - L / 2) + 0.0008, y, z - L / 2)), (0.002, random.uniform(0.004, 0.01), L))
for j in range(12):                                                     # fuligem em volta da janela
    a = random.uniform(0, 2 * PI)
    y, z = math.cos(a) * 0.105, math.sin(a) * 0.105
    caixa(B('escudo_fuligem', 'chamusco', False, K), Vector((X_esc(y, z) + 0.0007, y, z)), (0.002, 0.03, 0.03), Matrix.Rotation(a, 3, 'X'))
for sy in (-1, 1):                                                      # braços do escudo
    for sz in (-1, 1):
        a = Vector((0.095, sy * 0.09, sz * 0.08))
        b = Vector((X_esc(sy * 0.14, sz * 0.14) - 0.014, sy * 0.14, sz * 0.14))
        viga(B('escudo_bracos', 'ferro', False, K), a, b, 0.022)
        cil(B('escudo_bracos', 'ferro', True, K), b, 0.02, 0.008, Vector((1, 0, 0)), lados=12)
# tambor (feixe de canos rotativo)
tambor = novo_vazio('tambor', canhao)
tambor.rotation_mode = 'XYZ'
T = 'tambor'
cil(B('rotor', 'ferro', True, T), Vector((0.14, 0, 0)), 0.075, 0.08, Vector((1, 0, 0)), lados=36)
engrenagem(B('coroa_tambor', 'aco', True, T), (0.135, 0, 0), R_GT, 0.03, 36, Vector((1, 0, 0)))
cil(B('eixo_tambor', 'aco', True, T), Vector((0.5, 0, 0)), 0.018, 0.8, Vector((1, 0, 0)), lados=16)
for x, h in ((0.36, 0.03), (0.68, 0.03)):
    cil(B('bracadeiras', 'ferro', True, T), Vector((x, 0, 0)), 0.076, h, Vector((1, 0, 0)), lados=36)
    for k in range(6):
        a = k * PI / 3 + PI / 6
        parafuso((x + h / 2 + 0.004, math.cos(a) * 0.06, math.sin(a) * 0.06), (1, 0, 0), T, 0.006)
caixa(B('bracadeira_listra', 'listras', False, T), Vector((0.68, 0, 0.077)), (0.03, 0.03, 0.002))
for k in range(6):
    a = k * PI / 3
    c = Vector((0, math.cos(a) * RB, math.sin(a) * RB))
    cil(B('canos', 'canos', True, T), c + Vector((0.52, 0, 0)), 0.016, 0.76, Vector((1, 0, 0)), lados=20)
    cil(B('quebra_chamas', 'queimado', True, T), c + Vector((0.89, 0, 0)), 0.02, 0.06, Vector((1, 0, 0)), lados=20)
    for j in range(4):
        b = a + j * PI / 2 + PI / 4
        caixa(B('quebra_fendas', 'escuro', False, T), c + Vector((0.893, math.cos(b) * 0.0195, math.sin(b) * 0.0195)), (0.035, 0.004, 0.004),
              Matrix.Rotation(b, 3, 'X'))
    cil(B('alma', 'escuro', False, T), c + Vector((0.9205, 0, 0)), 0.009, 0.002, Vector((1, 0, 0)), lados=14)
    toro(B('boca_fuligem', 'chamusco', True, T), c + Vector((0.92, 0, 0)), 0.014, 0.004, 20, 6, ROT_X)

# clarão (filho do canhão, na boca do cano de cima)
MUZ = Vector((MUZ_X, 0, RB))
flash = novo_vazio('clarao', canhao, MUZ)
flash.rotation_mode = 'XYZ'
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
nucleo = obj('clarao_nucleo', bm, 'clarao_nucleo', flash)
nucleo.scale = (0.05, 0.035, 0.035)
bm = bmesh.new()
for j in range(4):                                                      # pétalas saindo das fendas do quebra-chamas
    a = j * PI / 2 + PI / 4
    d = Vector((0.25, math.cos(a), math.sin(a))).normalized()
    q = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.022, radius2=0.0, depth=0.16,
                          matrix=Matrix.Translation(d * 0.08) @ q @ Matrix.Diagonal((1.0, 0.45, 1.0, 1.0)))
bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.04, radius2=0.0, depth=0.3,
                      matrix=Matrix.Translation((0.15, 0, 0)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
petalas = obj('clarao_petalas', bm, 'clarao', flash)
luz_b = bpy.data.lights.new('Clarão', 'POINT')
luz_b.color = (1.0, 0.6, 0.25)
luz_b.shadow_soft_size = 0.05
lb = bpy.data.objects.new('Clarão', luz_b)
sc.collection.objects.link(lb)
lb.parent = canhao
lb.location = MUZ + Vector((0.35, 0, 0.05))
luz_c = bpy.data.lights.new('Brasa dos canos', 'POINT')
luz_c.color = (1.0, 0.3, 0.06)
luz_c.shadow_soft_size = 0.2
lc = bpy.data.objects.new('Brasa dos canos', luz_c)
sc.collection.objects.link(lc)
lc.parent = canhao
lc.location = (0.8, 0, -0.1)
luz_o = bpy.data.lights.new('Olho', 'POINT')
luz_o.color = VIOLETA
luz_o.energy = 0.4
luz_o.shadow_soft_size = 0.02
lo = bpy.data.objects.new('Olho', luz_o)
sc.collection.objects.link(lo)
lo.parent = giro
lo.location = (0.11, -0.178, 0.47)

# ------------------------------------------------------------------ cinta de munição (filha do giro)
N_CINTA = 20
cinta = []
for i in range(N_CINTA):
    bm = bmesh.new()
    cartucho(bm, Matrix.Identity(4), vivo=True, tracante=(i % 4 == 0), elo=True)
    o = obj_m('cinta%d' % i, bm, ['latao_novo', 'latao_novo', 'espoleta', 'cobre', 'ponta_tracante', 'elo'], giro)
    suavizar(o)
    o.rotation_mode = 'QUATERNION'
    cinta.append(o)

# ------------------------------------------------------------------ objetos estáticos
PAIS = {'base': None, EV: elev, G: giro, K: canhao, T: tambor, 'acumulo': None, 'lascas': None}
for k in range(4):
    PAIS['perna%d' % k] = pernas[k]
grupos = {}
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(nome if g == 'base' else g + '_' + nome, bm, mat, PAIS[g])
    if liso:
        suavizar(o)
    grupos.setdefault(g, []).append(o)
BMS.clear()


# ------------------------------------------------------------------ animação: funções de estado
def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def seg(u, a, b):
    return suave((u - a) / (b - a))


TIROS = [40 + 2.4 * k for k in range(16)]          # 10 tiros/s
Y_INI, Y_FOGO = math.radians(40), math.radians(-72)
P_INI, P_FOGO = math.radians(4), math.radians(9)


def pose(q):
    """(yaw, pitch) no laço."""
    if q <= 26:
        t = suave((q - 1) / 25)
        return Y_INI + math.radians(-50) * t + math.radians(4) * math.sin(q * 0.5), P_INI + math.radians(2) * math.sin(q * 0.3)
    if q <= 38:
        t = suave((q - 26) / 12)
        y26 = Y_INI + math.radians(-50)
        return y26 + (Y_FOGO - y26) * t, P_INI + (P_FOGO - P_INI) * t
    if q <= 78:
        trem = math.radians(0.35) if 40 <= q <= 77 else 0.0
        return Y_FOGO + trem * math.sin(q * 2.9), P_FOGO + trem * math.sin(q * 3.7 + 1)
    t = suave((q - 78) / 19)
    return Y_FOGO + (Y_INI - Y_FOGO) * t, P_FOGO + (P_INI - P_FOGO) * t


def omega(q):
    """Velocidade do tambor (rad/quadro): 10 tiros/s e 6 canos."""
    w = 10 * (2 * PI / 6) / FPS
    if q < 24:
        return 0.0
    if q < 40:
        return w * suave((q - 24) / 16)
    if q < 77:
        return w
    if q < 92:
        return w * (1 - suave((q - 77) / 15))
    return 0.0


ANG = [0.0]
for q in range(2, QUADROS + 2):
    ANG.append(ANG[-1] + (omega(q - 1) + omega(q)) / 2)
corr = math.ceil(ANG[-1] / (PI / 3)) * (PI / 3) - ANG[-1]


def ang_tambor(q):
    return ANG[q - 1] + corr * suave((q - 77) / 15)


def disparos(q):
    """Tiros com instante em (q-1, q]."""
    return [k for k, f in enumerate(TIROS) if q - 1 < f <= q]


def avanco(q):
    return max(0.0, min(16.0, (q - TIROS[0]) / 2.4 + (1 if q >= TIROS[0] else 0)))


def calor(q):
    def h(x):
        if x < 40:
            return 0.0
        if x <= 77:
            return (x - 40) / 37
        return math.exp(-(x - 77) / 16)
    return max(h(q), h(q + QUADROS))


def implanta(q):
    """Estado da implantação: u ∈ [0, 1] nos quadros 101..196; no laço tudo implantado."""
    u = 1.0 if q <= QUADROS else (q - I0) / (I1 - I0)
    return {
        'u': u,
        'perna': A_DOB + (A_DEP - A_DOB) * seg(u, 0.06, 0.34),
        'crava': seg(u, 0.36, 0.46),
        'mand': seg(u, 0.44, 0.52),
        'poste': seg(u, 0.52, 0.72),
        'lift': LIFT * seg(u, 0.5, 0.8),
        'ferrolho': seg(u, 0.8, 0.86),
        'olho': seg(u, 0.82, 0.9),
    }


def Mcan(yaw, pitch, lift=LIFT):
    return (Matrix.Translation((0, 0, Z_PT(lift))) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((0, 0, TZ))
            @ Matrix.Rotation(-pitch, 4, 'Y'))


# ------------------------------------------------------------------ física de cápsulas e elos
def chao_h(x, y):
    zp = Z_PT(LIFT)
    if dentro_chanfro(x, y, 0.35, 0.10):
        return zp + 0.05 if math.hypot(x, y) < R_COROA + 0.01 else zp
    if dentro_chanfro(x, y, 0.425, 0.143):
        return Z_COV
    if dentro_chanfro(x, y, 0.50, 0.17):
        return 0.15
    if EX0 - 0.01 < x < EX1 + 0.01 and EY0 - 0.01 < y < EY1 + 0.01:
        return 0.64
    if abs(x) < 0.98 and abs(y) < 0.98:
        return Z0
    return 0.0


def simula(f0, porta, vel, R, rolar, semente, w_lim=(16, 24)):
    """Gravidade, giro no ar, quique com perda, atrito; rola perpendicular ao eixo (cápsula) e para.
    Amostra nos quadros inteiros q0 = ceil(f0) ... ; devolve (q0, [(pos, euler)], índice em que parou)."""
    rnd = random.Random(semente)
    yaw0, pitch0 = pose(f0)
    Mc = Mcan(yaw0, pitch0)
    p = Mc @ porta
    v = Matrix.Rotation(yaw0, 3, 'Z') @ Vector((vel[0] + rnd.uniform(-0.1, 0.1), vel[1] + rnd.uniform(-0.12, 0.12),
                                                vel[2] + rnd.uniform(-0.08, 0.08)))
    psi, th, phi = yaw0 + rnd.uniform(-0.3, 0.3), 0.0, rnd.uniform(0, 2 * PI)
    w_psi, w_th = rnd.uniform(-9, 9), rnd.choice((-1, 1)) * rnd.uniform(*w_lim)
    w_phi = rnd.uniform(-20, 20)
    passo = 1 / 480
    no_chao, quiques, parou = False, 0, None
    q0 = math.ceil(f0 - 1e-9)
    amostras = []
    t = 0.0
    for e in range(QUADROS + 1):
        alvo_t = (q0 + e - f0) / FPS
        while t < alvo_t - 1e-9:
            t += passo
            if not no_chao:
                v.z -= 9.81 * passo
                p += v * passo
                th += w_th * passo
                psi += w_psi * passo
                phi += w_phi * passo
                h = chao_h(p.x, p.y)
                if p.z - R <= h:
                    p.z = h + R
                    if v.z < -0.5 and quiques < 2:
                        v.z = -v.z * (0.36 if rolar else 0.25)
                        v.x *= 0.5
                        v.y *= 0.5
                        w_th *= 0.45
                        w_psi *= 0.5
                        quiques += 1
                    else:
                        v.z = 0.0
                        no_chao = True
                if quiques:
                    alvo = round(th / PI) * PI
                    th += (alvo - th) * min(1.0, 5 * passo)
            else:
                h = chao_h(p.x, p.y)
                if p.z - R > h + 0.002:                     # saiu da borda: volta a cair
                    no_chao = False
                    quiques = 2
                    continue
                p.z = h + R
                a = Vector((math.cos(psi), math.sin(psi), 0))
                vh = Vector((v.x, v.y, 0))
                if rolar:
                    vh = vh - a * vh.dot(a) * (1 - math.exp(-10 * passo))
                    s = vh.length
                    if s > 0:
                        vh *= max(0.0, s - 1.6 * passo) / s
                else:
                    s = vh.length
                    if s > 0:
                        vh *= max(0.0, s - 6.0 * passo) / s
                v = Vector((vh.x, vh.y, 0))
                if rolar:
                    nrm = Vector((-a.y, a.x, 0))
                    phi += v.dot(nrm) / R * passo
                else:
                    w_phi *= math.exp(-30 * passo)
                    phi += w_phi * passo
                    alvo_phi = round(phi / PI) * PI
                    phi += (alvo_phi - phi) * min(1.0, 10 * passo)
                p += v * passo
                alvo = round(th / PI) * PI
                th += (alvo - th) * min(1.0, 14 * passo)
                w_psi *= math.exp(-8 * passo)
                psi += w_psi * passo
                if v.length < 0.01 and parou is None:
                    parou = e
        amostras.append((p.copy(), (phi, -th, psi)))
    return q0, amostras, parou if parou is not None else QUADROS


TRAJ_C, TRAJ_E = [], []
for k, f in enumerate(TIROS):
    TRAJ_C.append(simula(f, PORTA_C, (-0.3, -0.78, -0.1), R_CAP, True, 300 + k))
    TRAJ_E.append(simula(f, PORTA_E, (-0.2, -0.75, -0.25), 0.0125, False, 500 + k, (8, 14)))
for nome, TR in (('CAPSULA', TRAJ_C), ('ELO', TRAJ_E)):
    for k, (q0, am, par) in enumerate(TR):
        if k % 3 == 0:
            print(nome, k, 'q0', q0, 'parou', q0 + par, 'pos', tuple(round(c, 3) for c in am[par][0]),
                  'z', [round(am[e][0].z, 2) for e in range(0, 16, 2)])

# ------------------------------------------------------------------ acúmulo no chão (some na implantação)
OCUP = []


def livre(x, y, folga=0.035):
    if abs(x) > 0.95 or abs(y) > 0.95:
        return False
    if dentro_chanfro(x, y, 0.53, 0.17):
        return False
    for k in range(4):
        al = x * math.cos(PHI[k]) + y * math.sin(PHI[k])
        pp = abs(-x * math.sin(PHI[k]) + y * math.cos(PHI[k]))
        if 0.45 < al < 1.07 and pp < 0.14:
            return False
    if 0.06 < x < 0.9 and y < -0.62:
        return False
    if 0.4 < x < 0.56 and abs(y) < 0.09:
        return False
    for p in OCUP:
        if (p - Vector((x, y))).length < folga:
            return False
    return True


for TR in (TRAJ_C, TRAJ_E):                                            # pontos de pouso da rajada animada
    for q0, am, par in TR:
        OCUP.append(am[par][0].xy.copy())
bm_cap = bmesh.new()
bm_elo = bmesh.new()
centro_c = sum((am[par][0].xy for q0, am, par in TRAJ_C), Vector((0, 0))) / len(TRAJ_C)
centro_e = sum((am[par][0].xy for q0, am, par in TRAJ_E), Vector((0, 0))) / len(TRAJ_E)
print('POUSO cápsulas', tuple(round(c, 2) for c in centro_c), 'elos', tuple(round(c, 2) for c in centro_e))


def poe(bmx, centro, esp, n, R, eh_cap, z=None):
    feitos, tent = 0, 0
    while feitos < n and tent < 4000:
        tent += 1
        x = centro.x + random.gauss(0, esp)
        y = centro.y + random.gauss(0, esp)
        zz = z if z is not None else Z0
        if z is None and not livre(x, y):
            continue
        if z is not None:
            if any((p - Vector((x, y))).length < 0.04 for p in OCUP):
                continue
        OCUP.append(Vector((x, y)))
        Mx = Matrix.Translation((x, y, zz + R)) @ Matrix.Rotation(random.uniform(0, 2 * PI), 4, 'Z') @ \
            Matrix.Rotation(random.uniform(0, 2 * PI) if eh_cap else random.choice((0, PI)), 4, 'X')
        if eh_cap:
            cartucho(bmx, Mx)
        else:
            elo_solto(bmx, Mx)
        feitos += 1


poe(bm_cap, centro_c, 0.12, 34, R_CAP, True)
poe(bm_elo, centro_e, 0.12, 24, 0.0125, False)
for k in range(30):                                                     # restos de outras rajadas, em volta
    a = random.uniform(0, 2 * PI)
    poe(bm_cap if k % 3 else bm_elo, Vector((math.cos(a), math.sin(a))) * random.uniform(0.62, 0.88), 0.02, 1,
        R_CAP if k % 3 else 0.0125, bool(k % 3))
for k in range(9):                                                      # na tampa do casco (anel em volta do cabeçote)
    a = random.uniform(0, 2 * PI)
    d = Vector((math.cos(a), math.sin(a)))
    for tent in range(40):
        r = random.uniform(0.3, 0.45)
        p = d * r
        if dentro_chanfro(p.x, p.y, 0.405, 0.14) and not dentro_chanfro(p.x, p.y, 0.365, 0.11):
            poe(bm_cap if k % 2 else bm_elo, p, 0.0, 1, R_CAP if k % 2 else 0.0125, bool(k % 2), Z_COV)
            break
for k in range(14):                                                     # elos caídos no cabeçote (fora do giro do pinhão)
    for tent in range(60):
        a = math.radians(random.uniform(118, 168))
        r = random.uniform(0.31, 0.43)
        p = Vector((math.cos(a), math.sin(a))) * r
        if dentro_chanfro(p.x, p.y, 0.34, 0.10) and all((p - o_).length > 0.03 for o_ in OCUP):
            OCUP.append(p)
            Mx = Matrix.Translation((p.x, p.y, Z_PT(LIFT) + 0.0125)) @ Matrix.Rotation(random.uniform(0, 2 * PI), 4, 'Z') @ \
                Matrix.Rotation(random.choice((0, PI)), 4, 'X')
            elo_solto(bm_elo, Mx)
            break
o = obj_m('acumulo_capsulas', bm_cap, ['latao_gasto', 'boca_fria', 'espoleta'])
suavizar(o)
acumulo = [o, obj_m('acumulo_elos', bm_elo, ['elo'])]
for k in range(18):                                                     # fuligem e óleo onde caem as cápsulas
    p = centro_c + Vector((random.gauss(0, 0.15), random.gauss(0, 0.15)))
    if livre(p.x, p.y, 0.0) or True:
        if abs(p.x) < 0.95 and abs(p.y) < 0.95 and not dentro_chanfro(p.x, p.y, 0.5, 0.17):
            mancha(B('fuligem_chao', 'fuligem_chao', False, 'acumulo'), (p.x, p.y), random.uniform(0.03, 0.08), Z0 + 0.0009)
for k in range(10):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.6, 0.9)
    x, y = math.cos(a) * r, math.sin(a) * r
    if not dentro_chanfro(x, y, 0.5, 0.17):
        mancha(B('oleo_chao', 'oleo', False, 'acumulo'), (x, y), random.uniform(0.03, 0.07), Z0 + 0.001)
for k in range(14):
    x, y = random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95)
    if not dentro_chanfro(x, y, 0.5, 0.17):
        mancha(B('po', 'po', False, 'acumulo'), (x, y), random.uniform(0.05, 0.12), Z0 + 0.0007)
# lascas de concreto e rachaduras em volta das estacas (aparecem quando cravam)
for k in range(4):
    d = Vector((math.cos(PHI[k]), math.sin(PHI[k]), 0))
    t = Vector((-d.y, d.x, 0))
    c = d * (PE_R + 0.075)
    for j in range(7):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.12, 0.2)
        pp = c + Vector((math.cos(a), math.sin(a), 0)) * r
        if abs(pp.x) < 0.96 and abs(pp.y) < 0.96:
            pedra(B('lascas', 'concreto', False, 'lascas'), Vector((pp.x, pp.y, Z0 + 0.006)), random.uniform(0.008, 0.016), 0.5)
    for j in range(4):
        a = random.uniform(0, 2 * PI)
        p0 = c + Vector((math.cos(a), math.sin(a), 0)) * 0.115
        p1 = p0 + Vector((math.cos(a + random.uniform(-0.4, 0.4)), math.sin(a + random.uniform(-0.4, 0.4)), 0)) * random.uniform(0.05, 0.1)
        if abs(p1.x) < 0.97 and abs(p1.y) < 0.97:
            viga(B('lascas_rachas', 'escuro', False, 'lascas'), p0 + Vector((0, 0, Z0 + 0.0008)), p1 + Vector((0, 0, Z0 + 0.0008)), 0.003)
    mancha(B('lascas_po', 'po', False, 'lascas'), (c.x, c.y), 0.15, Z0 + 0.0011)
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(g + '_' + nome, bm, mat, None)
    grupos.setdefault(g, []).append(o)
BMS.clear()
acumulo += grupos.get('acumulo', [])
lascas = grupos.get('lascas', [])


# ------------------------------------------------------------------ partículas animadas
def volume(nome, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    return obj(nome, bm, mat)


ejetadas, anteriores, quentes = [], [], []
elos_ej, elos_ant = [], []
for k in range(len(TIROS)):
    mq = emissivo('Boca quente %d' % k, (1.0, 0.32, 0.05), 0.0, (0.03, 0.025, 0.022))
    base3d.M['quente%d' % k] = mq
    quentes.append(mq.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'])
    corpo = 'latao_gasto' if k % 5 else 'aco_capsula'
    for lista, boca, nome in ((ejetadas, 'quente%d' % k, 'capsula_ejetada%d'), (anteriores, 'boca_fria', 'capsula_anterior%d')):
        bm = bmesh.new()
        cartucho(bm, Matrix.Identity(4))
        o = obj_m(nome % k, bm, [corpo, boca, 'espoleta'])
        suavizar(o)
        lista.append(o)
    for lista, nome in ((elos_ej, 'elo_ejetado%d'), (elos_ant, 'elo_anterior%d')):
        bm = bmesh.new()
        elo_solto(bm, Matrix.Identity(4))
        lista.append(obj_m(nome % k, bm, ['elo']))
N_RASTRO, N_FINAL = 5, 2
fiapos = [[volume('fiapo', 'fiapo') for _ in range(N_RASTRO + N_FINAL)] for _ in TIROS]
fumacas = [volume('fumaca_tiro', 'fumaca') for _ in TIROS]
fumacas_canos = [volume('fumaca_canos', 'fumaca_canos') for _ in range(10)]
poeiras = [(volume('poeira', 'poeira'), k, j) for k in range(4) for j in range(2)]
tracantes = []
for k in range(0, len(TIROS), 4):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0, radius2=0.007, depth=1.6,
                          matrix=Matrix.Translation((-0.8, 0, 0)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.011)
    o = obj('tracante%d' % k, bm, 'tracante')
    o.rotation_mode = 'QUATERNION'
    tracantes.append((o, k))
faiscas = [obj('faisca', (lambda b: (bmesh.ops.create_icosphere(b, subdivisions=0, radius=0.005), b)[1])(bmesh.new()), 'faisca') for _ in range(10)]
vel_f = [Vector((random.uniform(1.5, 3.5), random.uniform(-1.4, 1.4), random.uniform(-0.6, 1.6))) for _ in faiscas]


def boca_mundo(pos, eul):
    return pos + Euler(eul, 'XYZ').to_matrix() @ Vector((0.0745 - CX, 0, 0))


def cinta_pose(pitch):
    """Curva da cinta (no giro): da boca da caixa, sobe e entra na bandeja."""
    Mcl = Matrix.Translation((0, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y')
    P3 = Mcl @ FEED
    P2 = P3 + Mcl.to_3x3() @ Vector((0, 0.12, 0.055))
    P1 = BOX_MOUTH + Vector((0, 0, 0.17))
    pts = bezier(BOX_MOUTH, P1, P2, P3, 80)
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + (b - a).length)
    return pts, acc, Mcl.to_3x3() @ Vector((1, 0, 0))


def ponto_cinta(pts, acc, s):
    L = acc[-1]
    s = max(0.0, min(L, s))
    for j in range(len(acc) - 1):
        if acc[j + 1] >= s:
            t = (s - acc[j]) / max(1e-9, acc[j + 1] - acc[j])
            return pts[j].lerp(pts[j + 1], t), (pts[j + 1] - pts[j]).normalized()
    return pts[-1], (pts[-1] - pts[-2]).normalized()


folga_min = [9.0]


def chave(o, *cs, q):
    for c in cs:
        o.keyframe_insert(c, frame=q)


def mostra(o, vis, q):
    o.hide_render = o.hide_viewport = not vis
    o.keyframe_insert('hide_render', frame=q)
    o.keyframe_insert('hide_viewport', frame=q)


calor_v = next(n for n in base3d.M['canos'].node_tree.nodes if n.name == 'calor').outputs[0]
olho_e = base3d.M['olho'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
QS = list(range(1, QUADROS + 1)) + list(range(I0, I1 + 1))
for q in QS:
    laco = q <= QUADROS
    st = implanta(q)
    u = st['u']
    if laco:
        yaw, pitch = pose(q)
        ang = ang_tambor(q)
        av = avanco(q)
        hq = calor(q)
        tiros_q = disparos(q)
    else:
        yaw = Y_INI * seg(u, 0.86, 1.0)
        pitch = P_INI * seg(u, 0.84, 0.94)
        ang = (2 * PI / 3) * seg(u, 0.88, 1.0)
        av, hq, tiros_q = 0.0, 0.0, []
    # pernas, pinhões, estacas
    for k in range(4):
        rq = (Matrix.Rotation(PHI[k], 3, 'Z') @ Matrix.Rotation(st['perna'], 3, 'Y')).to_quaternion()
        pernas[k].rotation_quaternion = rq
        chave(pernas[k], 'rotation_quaternion', q=q)
        pinhoes_perna[k].rotation_quaternion = (Matrix.Rotation(PHI[k], 3, 'Z') @ Matrix.Rotation(-st['perna'] * R_GL / R_PL, 3, 'Y')).to_quaternion()
        chave(pinhoes_perna[k], 'rotation_quaternion', q=q)
        e, base_e = estacas[k]
        F3 = Matrix.Rotation(-A_DEP, 3, 'Y')
        e.location = base_e + F3 @ Vector((0, 0, -CRAVA * st['crava']))
        chave(e, 'location', q=q)
    # trava de transporte
    post.location = (POST_X, 0, Z_POST0 - 0.32 * st['poste'])
    chave(post, 'location', q=q)
    for j, s in mandibulas:
        j.rotation_euler = (-s * math.radians(110) * st['mand'], 0, 0)
        chave(j, 'rotation_euler', q=q)
    # elevador, ferrolhos, cabo espiral
    elev.location = (0, 0, Z_PT(st['lift']))
    chave(elev, 'location', q=q)
    for f, s in ferrolhos:
        f.location = (s * (0.205 - 0.055 * st['ferrolho']), 0, Z_COV + 0.025)
        chave(f, 'location', q=q)
    kb = cabo_esp.data.shape_keys.key_blocks['Esticado']
    kb.value = st['lift'] / LIFT
    kb.keyframe_insert('value', frame=q)
    # cabeça
    giro.rotation_euler = (0, 0, yaw)
    chave(giro, 'rotation_euler', q=q)
    pin_giro.rotation_euler = (0, 0, yaw * R_COROA / R_PIN)
    chave(pin_giro, 'rotation_euler', q=q)
    canhao.rotation_euler = (0, -pitch, 0)
    chave(canhao, 'rotation_euler', q=q)
    pin_elev.rotation_euler = (0, pitch * R_GE / R_PE, 0)
    chave(pin_elev, 'rotation_euler', q=q)
    tambor.rotation_euler = (ang, 0, 0)
    chave(tambor, 'rotation_euler', q=q)
    pin_tambor.rotation_euler = (-ang * R_GT / R_PT, 0, 0)
    chave(pin_tambor, 'rotation_euler', q=q)
    radar.rotation_euler = (0, 0, (2 * PI * 2 * (q - 1) / QUADROS) if laco else 2 * PI * 1.5 * st['olho'])
    chave(radar, 'rotation_euler', q=q)
    olho_e.default_value = (0.3 + 11.7 * st['olho']) * (1.4 if laco and 30 <= q <= 80 else 1.0)
    olho_e.keyframe_insert('default_value', frame=q)
    luz_o.energy = 0.05 + 0.5 * st['olho']
    luz_o.keyframe_insert('energy', frame=q)
    # cinta: avança com os tiros
    pts, acc, ax_c = cinta_pose(pitch)
    Lc = acc[-1]
    for i, o in enumerate(cinta):
        s = ((i + av) % N_CINTA) * PITCH
        vis = 0.0 <= s <= Lc - 0.004
        p, tg = ponto_cinta(pts, acc, s)
        a = Vector((1, 0, 0)).lerp(ax_c, s / Lc).normalized()
        yl = (tg - a * tg.dot(a)).normalized()
        zl = a.cross(yl)
        o.location = p
        o.rotation_quaternion = Matrix((a, yl, zl)).transposed().to_quaternion()
        chave(o, 'location', 'rotation_quaternion', q=q)
        mostra(o, vis, q)
        if vis and laco and abs(p.y) < 0.2 and abs(p.y) > 0.12:
            folga_min[0] = min(folga_min[0], p.z - 0.42 - 0.011)
    # calor dos canos
    calor_v.default_value = 1.3 * hq ** 1.5
    calor_v.keyframe_insert('default_value', frame=q)
    luz_c.energy = 6.0 * hq
    luz_c.keyframe_insert('energy', frame=q)
    # clarão
    fl = 1.0 if tiros_q else 0.0
    flash.rotation_euler = (random.uniform(0, PI / 2) if fl else 0.0, 0, 0)
    flash.scale = [max(0.01, fl * random.uniform(1.2, 1.7))] * 3
    chave(flash, 'rotation_euler', 'scale', q=q)
    for o in (nucleo, petalas):
        mostra(o, fl > 0, q)
    luz_b.energy = 35.0 * fl
    luz_b.keyframe_insert('energy', frame=q)
    # traçantes (um a cada quatro tiros)
    for o, k in tracantes:
        e = q - TIROS[k]
        vis = laco and 0 <= e < 1.6
        if vis:
            Mc = Mcan(*pose(TIROS[k]))
            p0 = Mc @ Vector((MUZ_X, 0, RB))
            d = Mc.to_3x3() @ Vector((1, 0, 0))
            o.location = p0 + d * (0.55 + 2.4 * e)
            o.rotation_quaternion = d.to_track_quat('X', 'Z')
        else:
            o.location = (0, 0, -1)
        chave(o, 'location', 'rotation_quaternion', q=q)
        mostra(o, vis, q)
    # faíscas na boca
    ult = max((k for k, f in enumerate(TIROS) if f <= q), default=None) if laco else None
    for j, o in enumerate(faiscas):
        viva = False
        if ult is not None and q - TIROS[ult] < 3 and q <= 78:
            tt = (q - TIROS[ult]) / FPS + (j % 3) * 0.01
            Mc = Mcan(*pose(TIROS[ult]))
            p = Mc @ Vector((MUZ_X, 0, RB)) + (Mc.to_3x3() @ vel_f[j]) * tt + Vector((0, 0, -4.9 * tt * tt))
            viva = True
            o.location = p
        else:
            o.location = (0, 0, -1)
        chave(o, 'location', q=q)
        mostra(o, viva, q)
    # cápsulas e elos: cada tiro ejeta os seus
    for k in range(len(TIROS)):
        for (TR, atual, ant) in ((TRAJ_C, ejetadas[k], anteriores[k]), (TRAJ_E, elos_ej[k], elos_ant[k])):
            q0, am, par = TR[k]
            e = q - q0
            pf, ef = am[par]
            ant.location, ant.rotation_euler = pf, ef
            chave(ant, 'location', 'rotation_euler', q=q)
            mostra(ant, laco and e < par, q)
            if laco and e >= 0:
                pos, eul = am[min(e, len(am) - 1)]
                atual.location, atual.rotation_euler = pos, eul
            else:
                atual.location, atual.rotation_euler = (0, 0, -1), (0, 0, 0)
            chave(atual, 'location', 'rotation_euler', q=q)
            mostra(atual, laco and e >= 0, q)
        q0, am, par = TRAJ_C[k]
        e = q - q0
        quentes[k].default_value = 0.0 if (not laco or e < 0) else 9.0 * max(0.0, 1 - e / 26) ** 1.6
        quentes[k].keyframe_insert('default_value', frame=q)
        for j, f in enumerate(fiapos[k]):
            vida, nasce = (10, j * 2) if j < N_RASTRO else (22, par + (j - N_RASTRO) * 6)
            uu = None
            if laco:
                for qq in (q, q + QUADROS):
                    ee = qq - q0 - nasce
                    if 0 <= ee <= vida:
                        uu = ee / vida
                        break
            if uu is None:
                f.location, f.scale, f.color = (0, 0, -1), (0.02, 0.02, 0.02), (0, 0, 0, 1)
                vis = False
            else:
                pb, eb = am[min(nasce, len(am) - 1)]
                p0 = boca_mundo(pb, eb)
                if j < N_RASTRO:
                    f.location = p0 + Vector((0.01 * uu, -0.01 * uu, 0.05 * uu))
                    f.scale = (0.012 + 0.03 * uu, 0.012 + 0.03 * uu, 0.016 + 0.035 * uu)
                    d = 1.0 * (1 - uu) ** 1.2
                else:
                    f.location = p0 + Vector((0.01 * uu, 0.008 * uu, 0.01 + 0.15 * uu))
                    f.scale = (0.01 + 0.025 * uu, 0.01 + 0.025 * uu, 0.016 + 0.05 * uu)
                    d = 0.75 * math.sin(PI * min(1.0, uu * 1.3 + 0.08)) * (1 - uu)
                f.color = (d, d, d, 1)
                f.rotation_euler = (j, uu * 2, k)
                vis = True
            chave(f, 'location', 'scale', 'color', 'rotation_euler', q=q)
            mostra(f, vis, q)
        # fumaça de cada tiro
        o = fumacas[k]
        e = q - TIROS[k]
        if laco and 0 <= e <= 18:
            uu = e / 18
            Mc = Mcan(*pose(TIROS[k]))
            d = Mc.to_3x3() @ Vector((1, 0, 0))
            o.location = Mc @ Vector((MUZ_X + 0.05, 0, RB)) + d * (0.1 + 0.3 * uu) + Vector((0, 0, 0.12 * uu))
            o.scale = (0.035 + 0.09 * uu, 0.03 + 0.07 * uu, 0.03 + 0.09 * uu)
            o.rotation_euler = (k + uu, k * 0.7, uu * 2)
            vis = True
        else:
            o.location, o.scale = (0, 0, 1.5), (0.05, 0.05, 0.05)
            vis = False
        chave(o, 'location', 'scale', 'rotation_euler', q=q)
        mostra(o, vis, q)
    # fumaça subindo dos canos quentes
    Mc = Mcan(yaw, pitch, st['lift'])
    for j, o in enumerate(fumacas_canos):
        uu = ((q - 1) / 30 + j / 10) % 1.0
        forca = min(1.0, 1.4 * hq) if laco else 0.0
        a = j * 2.4
        o.location = Mc @ Vector((0.45 + 0.045 * (j % 8), math.cos(a) * 0.03, 0.04)) + Vector((-0.06 * uu, 0.04 * uu * math.sin(j), 0.55 * uu))
        o.scale = [max(0.02, (0.035 + 0.08 * uu) * forca), max(0.02, (0.035 + 0.08 * uu) * forca), max(0.02, (0.05 + 0.11 * uu) * forca)]
        o.rotation_euler = (j, uu * 2, j * 0.5)
        chave(o, 'location', 'scale', 'rotation_euler', q=q)
        mostra(o, forca > 0.1, q)
    # poeira dos pés (implantação: pouso e cravada)
    for o, k, j in poeiras:
        d = Vector((math.cos(PHI[k]), math.sin(PHI[k]), 0))
        t0 = 0.33 if j == 0 else 0.4
        uu = (u - t0) / 0.14
        vis = (not laco) and 0 <= uu <= 1
        if vis:
            o.location = d * (PE_R + 0.03 + 0.08 * uu) + Vector((0, 0, Z0 + 0.03 + 0.12 * uu))
            o.scale = (0.06 + 0.12 * uu, 0.06 + 0.12 * uu, 0.03 + 0.07 * uu)
            o.rotation_euler = (k, j, uu * 3)
        else:
            o.location, o.scale = (0, 0, -1), (0.05, 0.05, 0.05)
        chave(o, 'location', 'scale', 'rotation_euler', q=q)
        mostra(o, vis, q)
    # acúmulo e lascas
    for o in acumulo:
        mostra(o, laco, q)
    for o in lascas:
        mostra(o, laco or st['crava'] > 0.3, q)
    # empurrador e caixas de munição chegando
    ce = (q - 1) / QUADROS if laco else 0.0
    emp = suave((ce - 0.42) / 0.16) * (1 - suave((ce - 0.62) / 0.14))
    empurrador.location = (0.62 - 0.27 * emp + 0.07, -0.86, 0.27)
    chave(empurrador, 'location', q=q)
    for i, cxm in enumerate(caixas_mun):
        fase = (ce + i * 0.5) % 1.0
        if fase < 0.4:
            y = -1.0 + 0.14 * suave(fase / 0.4)
            x = BX
        else:
            y = -0.86
            x = BX - 0.27 * suave((fase - 0.42) / 0.16)
        cxm.location = (x, y, 0.2)
        chave(cxm, 'location', q=q)
        vis = (y > -0.95 or fase > 0.05) and x > 0.26
        for ob in [cxm] + list(cxm.children):
            mostra(ob, vis, q)
print('FOLGA cinta sobre o garfo: %.3f' % folga_min[0])

for o in list(sc.objects):
    ad = o.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
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


def foto(nome, q, pos, alvo, lente, res=(1300, 1000)):
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.frame_set(q)
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    if so_uma in (None, '0'):
        foto('metralhadora_0.png', 20, (-1.0, -3.7, 2.1), (0.08, 0.0, 0.82), 38, (1200, 1100))
    if so_uma in (None, 'perto'):
        foto('metralhadora_perto.png', 84, (1.4, 1.25, 1.9), (-0.02, 0.0, 1.25), 34)
    if so_uma in (None, 'implantacao'):
        foto('metralhadora_implantacao.png', 124, (2.6, -2.4, 1.85), (0.1, 0.0, 0.62), 40, (1200, 1100))
    if so_uma in (None, 'rajada'):
        foto('metralhadora_rajada.png', 60, (-2.25, -2.05, 1.6), (-0.1, -0.35, 1.0), 30)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    foto('metralhadora_teste.png', int(v[7]), v[0:3], v[3:6], v[6], (1000, 800))
print('METRALHADORA ok')
