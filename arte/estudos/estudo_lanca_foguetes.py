"""Estudo isolado (fora do jogo): LANÇA-FOGUETES (torre_foguetes), 3×3 tiles. Dispara foguetes com dano em área,
alcance 30 m. Os foguetes chegam por esteira ou braço na boca sul (ITEM_ENT_S1, tile do meio) e caem no paiol.
Partes como no jogo: base, giro (gira em Z), casulo (inclina), pistao0, pistao1, radar, braco.
- Plataforma octogonal pesada e aparafusada com quatro estabilizadores hidráulicos nas diagonais: luva amarela,
  viga telescópica, cilindro de extensão, macaco vertical (camisa presa no cabeçote da viga, haste na sapata com
  rótula e chumbadores), mangueiras da caixa de junção até cada porta do macaco.
- Unidade hidráulica (leste): tanque, motor-bomba, bloco de válvulas com manômetros, acumulador; feixe de
  mangueiras entrando na plataforma. Armário de força (norte) com isoladores e cabos da rede.
- Giro: coroa dentada + motor com pinhão; mesa, bochechas blindadas, mancais dos munhões, caixas de eletrônica.
- Casulo de 9 tubos (3×3): cada tubo com tampa frontal articulada que abre e selo traseiro que estoura no disparo.
  Pistões de elevação (camisa no giro, haste na orelha do casulo).
- Paiol (sul) com boca de entrada, cortina de borracha, visor com o estoque, elevador que apresenta o foguete por
  uma escotilha de duas abas. Braço carregador: carro em trilho, coluna, lança telescópica com cilindro, pulso
  nivelado, garra de duas mandíbulas e soquete telescópico que empurra o foguete no tubo.
- Foguete: bocal, aletas dobráveis (abrem em voo), corpo oliva com faixa amarela e anel vermelho, ogiva com espoleta.
- Disparo: fogo e fumaça densa pela traseira contra o defletor refratário no chão (oeste), queimado; foguete com
  chama e rastro de fumaça em curva; explosão em área no alvo (clarão, bola de fogo, onda, anel de poeira,
  fumaça, estilhaços, cratera). Sobras: selo traseiro e duas meias-cascas (invólucro guia) ejetados por tiro,
  com física simples; fumaça residual saindo dos tubos disparados.
- Sensor da IA: radar girando no mastro.
Animação (laço de 4 s): vira e eleva, abre as tampas, salva de 4 foguetes (6 por segundo), volta à posição de
carga, fecha as tampas e o braço recarrega os 4 tubos, um a um.
Uso: blender -b --python estudo_lanca_foguetes.py -- foto [0|perto|salva|impacto]
     blender -b --python estudo_lanca_foguetes.py -- teste x y z ax ay az lente quadro"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(81)

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


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def catmull(pts, n=6):
    """Caminho suave passando pelos pontos (mangueiras e cabos com várias curvas)."""
    pts = [Vector(p) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def abracar(bm, pts, r, passo=5):
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(bm, pts[j] - u * 0.01, pts[j] + u * 0.01, r * 1.5, 12)


def feixe(bc, ba, pts, lat, n=3, r=0.014, passo=4):
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 0.6), 12)


def octo(bm, c, apo, z0, z1):
    R = apo / math.cos(PI / 8)
    vs0 = [bm.verts.new((c.x + R * math.cos(PI / 8 + k * PI / 4), c.y + R * math.sin(PI / 8 + k * PI / 4), z0)) for k in range(8)]
    vs1 = [bm.verts.new((v.co.x, v.co.y, z1)) for v in vs0]
    bm.faces.new(list(reversed(vs0)))
    bm.faces.new(vs1)
    for k in range(8):
        bm.faces.new((vs0[k], vs0[(k + 1) % 8], vs1[(k + 1) % 8], vs1[k]))


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


def torno(bm, perfil, n=24, fechado=False, c=(0.0, 0.0)):
    """Sólido de revolução em torno do eixo x (deslocado para y, z = c); perfil = [(x, r)]. r = 0 vira polo."""
    aneis = []
    for x, r in perfil:
        if r < 1e-6:
            aneis.append([bm.verts.new((x, c[0], c[1]))])
        else:
            aneis.append([bm.verts.new((x, c[0] + r * math.cos(a), c[1] + r * math.sin(a))) for a in (k * 2 * PI / n for k in range(n))])
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


def placa_furos(bm, x0, x1, centros, meio, r, n=24):
    """Chapa (normal em x) feita de células quadradas com furo redondo: frente e trás do casulo."""
    for (yc, zc) in centros:
        for xf, sentido in ((x0, -1), (x1, 1)):
            ext, inn = [], []
            for k in range(n):
                a = k * 2 * PI / n
                c, s = math.cos(a), math.sin(a)
                f = meio / max(abs(c), abs(s))
                ext.append(bm.verts.new((xf, yc + c * f, zc + s * f)))
                inn.append(bm.verts.new((xf, yc + c * r, zc + s * r)))
            for k in range(n):
                q = (ext[k], ext[(k + 1) % n], inn[(k + 1) % n], inn[k])
                bm.faces.new(q if sentido > 0 else tuple(reversed(q)))


BMS = {}


def B(nome, mat, liso=False, g='base'):
    k = (nome, mat, liso, g)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def parafuso(p, n, g='base', r=0.011):
    cil(B('parafusos', 'aco', False, g), Vector(p), r, 0.012, Vector(n), lados=6)


def escorrido(g, p, n, L, mat='ferrugem', w=0.012):
    """Escorrido vertical numa face de normal n (ferrugem, óleo, fuligem)."""
    caixa(B('escorridos_' + mat, mat, False, g), Vector(p) + Vector(n) * 0.001 + Vector((0, 0, -L / 2)), (w, 0.002, L), rot_face(Vector(n)))


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def nuvem_mat(nome, escura, clara, dens, ruido=2.4, emis_cor=None, emis=0.0, corte=(0.36, 0.62)):
    """Volume com ruído que some na borda da esfera. A cor do objeto controla: R = densidade (some aos poucos),
    G = mistura escura → clara (fumaça preta que dilui em cinza). Emissão opcional (fogo)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    oi = no(nt, 'ShaderNodeObjectInfo')
    som = no(nt, 'ShaderNodeVectorMath', operation='ADD')
    nt.links.new(tc.outputs['Object'], som.inputs[0])
    esc = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    esc.inputs[1].default_value = 37.0
    nt.links.new(oi.outputs['Random'], esc.inputs[0])
    nt.links.new(esc.outputs['Value'], som.inputs[1])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': ruido, 'Detail': 6.0})
    nt.links.new(som.outputs['Vector'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.3})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    forma = no(nt, 'ShaderNodeMapRange', **{'From Min': corte[0], 'From Max': corte[1]})
    nt.links.new(ru.outputs['Fac'], forma.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], m1.inputs[0])
    nt.links.new(forma.outputs['Result'], m1.inputs[1])
    sep = no(nt, 'ShaderNodeSeparateColor')
    nt.links.new(oi.outputs['Color'], sep.inputs[0])
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(sep.outputs[0], m2.inputs[1])
    m3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    m3.inputs[1].default_value = dens
    nt.links.new(m2.outputs['Value'], m3.inputs[0])
    nt.links.new(m3.outputs['Value'], vol.inputs['Density'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (*escura, 1)
    mix.inputs[7].default_value = (*clara, 1)
    nt.links.new(sep.outputs[1], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    if emis_cor:
        vol.inputs['Emission Color'].default_value = (*emis_cor, 1)
        m4 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        m4.inputs[1].default_value = emis
        nt.links.new(m2.outputs['Value'], m4.inputs[0])
        nt.links.new(m4.outputs['Value'], vol.inputs['Emission Strength'])
    return m


def onda_mat():
    """Anel da onda de choque: poeira clara translúcida que brilha um pouco com o clarão."""
    m = bpy.data.materials.new('Onda')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.68, 0.58, 1)
    b.inputs['Alpha'].default_value = 0.13
    b.inputs['Roughness'].default_value = 0.9
    b.inputs['Emission Color'].default_value = (1.0, 0.7, 0.4, 1)
    b.inputs['Emission Strength'].default_value = 0.25
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.95, sujeira=0.9, ferrugem=0.35),
    'amarelo2': mats.material('Amarelo trocado', (0.62, 0.36, 0.04), 0, 0.5, desgaste=1.0, sujeira=1.0, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.8, sujeira=0.85),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'latao': mats.material('Latão', (0.62, 0.45, 0.16), 1.0, 0.32, pintura=False, sujeira=0.7),
    'queimado': mats.material('Queimado', (0.13, 0.11, 0.12), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'porcelana': mats.material('Porcelana', (0.42, 0.19, 0.09), 0, 0.2, pintura=False, sujeira=0.7, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'isol_verm': mats.material('Isolador vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.5, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'escuro': mats.material('Fundo', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'tubo_int': mats.material('Interior do tubo', (0.035, 0.032, 0.03), 0.6, 0.55, pintura=False, sujeira=0.9, ferrugem=0.4),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.09, 0.065, 0.045), 0, 0.7, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem_chao': mats.material('Fuligem', (0.045, 0.04, 0.036), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'terra_queimada': mats.material('Terra revirada', (0.11, 0.085, 0.065), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'refratario': mats.material('Refratário', (0.38, 0.35, 0.32), 0, 0.85, pintura=False, sujeira=1.0, desgaste=0.0),
    'oliva': mats.material('Oliva do foguete', (0.15, 0.16, 0.10), 0, 0.55, desgaste=0.75, sujeira=0.8),
    'ogiva': mats.material('Ogiva', (0.19, 0.19, 0.18), 0.6, 0.45, desgaste=0.6, sujeira=0.7),
    'faixa_amarela': mats.material('Faixa amarela', (0.78, 0.52, 0.04), 0, 0.45, desgaste=0.5, sujeira=0.6),
    'vermelho': mats.material('Vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'composito': mats.material('Compósito', (0.05, 0.05, 0.048), 0, 0.6, desgaste=0.3, sujeira=0.7),
    'listras': base3d.listras_mat(),
    'vidro': emissivo('Vidro do manômetro', (0.05, 0.04, 0.06), 0.0, (0.6, 0.6, 0.55)),
    'luz_paiol': emissivo('Luz do paiol', AMBAR, 6.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'led_verm': emissivo('Led vermelho', (1.0, 0.05, 0.03), 10.0),
    'ia': emissivo('Faixa da IA', VIOLETA, 6.0, (0.05, 0.02, 0.1)),
    'olho': emissivo('Olho do sensor', VIOLETA, 5.0, (0.05, 0.02, 0.1)),
    'nucleo_chama': emissivo('Núcleo da chama', (1.0, 0.75, 0.4), 60.0),
    'clarao': emissivo('Clarão', (1.0, 0.7, 0.35), 45.0),
    'brasa': emissivo('Bocal quente', (1.0, 0.3, 0.04), 0.0, (0.1, 0.05, 0.03)),
    'onda': onda_mat(),
    'fogo': nuvem_mat('Fogo', (0.04, 0.015, 0.005), (0.04, 0.015, 0.005), 40.0, 2.8, (1.0, 0.38, 0.05), 110.0, (0.3, 0.6)),
    'fumaca': nuvem_mat('Fumaça densa', (0.03, 0.028, 0.027), (0.78, 0.77, 0.76), 7.0, 2.2),
    'rastro': nuvem_mat('Rastro', (0.25, 0.25, 0.25), (0.62, 0.62, 0.63), 9.0, 2.0, corte=(0.3, 0.62)),
    'poeira': nuvem_mat('Poeira', (0.2, 0.16, 0.12), (0.42, 0.36, 0.28), 5.0, 2.6),
    'fogo_exp': nuvem_mat('Fogo da explosão', (0.03, 0.012, 0.004), (0.03, 0.012, 0.004), 3.5, 3.6, (1.0, 0.4, 0.07), 22.0, (0.45, 0.75)),
    'clarao_v': nuvem_mat('Clarão', (0.2, 0.18, 0.15), (0.2, 0.18, 0.15), 1.0, 2.0, (1.0, 0.75, 0.45), 45.0, (0.25, 0.6)),
    'faisca': emissivo('Faísca', (1.0, 0.55, 0.15), 50.0),
    'fiapo': nuvem_mat('Fiapo', (0.1, 0.098, 0.096), (0.4, 0.4, 0.4), 16.0, 2.2),
})


# ------------------------------------------------------------------ medidas
Z0 = 0.08                 # topo da laje
ZD = 0.40                 # convés da plataforma
AP = 0.70                 # apótema da plataforma
R_COROA, R_PINHAO = 0.44, 0.05
ZG0, ZG1 = 0.43, 0.49     # coroa
ZM = 0.56                 # topo da mesa giratória
ZP = 0.62                 # topo da placa do giro
TZ = 1.08                 # munhão do casulo (eixo de elevação)
PX0, PX1, PH = -0.40, 0.42, 0.20        # casulo: traseira, frente, meia largura interna
SP, RI, RO = 0.12, 0.042, 0.048         # passo e raios dos tubos
LR, RR = 0.55, 0.032                    # foguete
X_TRAS_F = -0.375                        # traseira do foguete no tubo (referencial do casulo)
YB0, YB1 = 0.235, 0.285                 # bochechas (|y|)
YAW_F, PITCH_F = math.radians(20), math.radians(30)
YAW_C = math.radians(90)                # posição de carga: frente para o norte, traseira para o paiol
DIR_MOTOR = Vector((1, -1, 0)).normalized()
# paiol e braço
PY0, PY1, PZ1 = -1.38, -0.80, 0.82      # paiol (y) e topo
PICK = Vector((0.0, -1.09, 0.90))       # centro do foguete apresentado
GY_C = -0.74                             # y do centro do foguete na garra, alinhado ao tubo
AY, SZ = -0.62, 0.80                     # ombro do braço (y, z)
L_EXT, L_INT = 0.32, 0.27                # lança: luva externa e haste interna
WZ = 0.10                                # pulso acima do centro do foguete


def tubo_yz(r, c):
    return (c - 1) * SP, (1 - r) * SP


CENTROS = [tubo_yz(r, c) for r in range(3) for c in range(3)]
DISPARO = [(0, 0), (2, 2), (0, 2), (2, 0)]          # tubos da salva (e da recarga, na mesma ordem)
TF = [22, 26, 30, 34]                                # quadros dos disparos
FL = 18                                              # quadros de voo
TI = [t + FL for t in TF]                            # impactos
RC = [48 + 12 * k for k in range(4)]                 # início de cada recarga
ALVO = Vector((26 * math.cos(YAW_F), 26 * math.sin(YAW_F), 0.0))
ESPALHA = [Vector((0, 0, 0)), Vector((1.7, -1.3, 0)), Vector((-1.5, 1.2, 0)), Vector((0.8, 1.9, 0))]
ALVOS = [ALVO + Matrix.Rotation(YAW_F, 3, 'Z') @ e for e in ESPALHA]

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-1.485, s * 1.485 - 0.014, 0.0), (1.485, s * 1.485 + 0.014, Z0 + 0.002))
    caixa_de(bm, (s * 1.485 - 0.014, -1.485, 0.0), (s * 1.485 + 0.014, 1.485, Z0 + 0.002))
for k in range(14):                                                       # emendas e trincas da laje
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.8, 1.4)
    c = Vector((math.cos(a) * r, math.sin(a) * r, Z0 + 0.0006))
    caixa(B('trincas', 'chamusco'), c, (random.uniform(0.08, 0.25), 0.004, 0.001), Matrix.Rotation(random.uniform(0, PI), 3, 'Z'))

# ------------------------------------------------------------------ plataforma
O = Vector((0, 0, 0))
octo(B('saia', 'ferro'), O, AP + 0.05, Z0, 0.14)
octo(B('plataforma', 'grafite'), O, AP, 0.14, 0.36)
octo(B('conves', 'ferro'), O, AP + 0.02, 0.36, ZD)
for k in range(32):                                                       # chumbadores na saia
    a = k * 2 * PI / 32 + PI / 32
    p = Vector((math.cos(a), math.sin(a), 0)) * (AP + 0.02) + Vector((0, 0, 0.146))
    cil(B('parafusos', 'aco'), p, 0.014, 0.018, lados=6)
    cil(B('arruelas', 'ferro'), p - Vector((0, 0, 0.006)), 0.022, 0.006, lados=12)
R8 = AP / math.cos(PI / 8)
for k in range(8):                                                        # nervuras nos vértices
    a = PI / 8 + k * PI / 4
    caixa(B('nervuras', 'ferro'), Vector((math.cos(a), math.sin(a), 0)) * (R8 + 0.002) + Vector((0, 0, 0.25)),
          (0.035, 0.035, 0.22), Matrix.Rotation(a, 3, 'Z'))
FACES = {}
for k in range(8):
    a = k * PI / 4
    n = Vector((math.cos(a), math.sin(a), 0))
    FACES[k] = (n, rot_face(n))
for k in (0, 2, 4, 6):                                                    # placas blindadas amarelas nas faces retas
    n, R = FACES[k]
    c = n * (AP + 0.011) + Vector((0, 0, 0.25))
    mat = 'amarelo2' if k == 6 else 'amarelo'
    caixa(B('placas_' + mat, mat), c, (0.46, 0.022, 0.18), R)
    caixa(B('placas_listras', 'listras'), n * (AP + 0.0225) + Vector((0, 0, 0.325)), (0.46, 0.002, 0.03), R)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parafuso(c + R @ Vector((sx * 0.205, 0.012, 0)) + Vector((0, 0, sz * 0.07)), n)
        parafuso(c + R @ Vector((sx * 0.07, 0.012, 0)) + Vector((0, 0, -0.07)), n)
    for j in range(3):                                                    # escorridos de ferrugem pelas placas
        escorrido('base', c + R @ Vector((random.uniform(-0.18, 0.18), 0.012, 0)) + Vector((0, 0, 0.06)), n,
                  random.uniform(0.05, 0.14), 'ferrugem', random.uniform(0.006, 0.014))
# remendo aparafusado na face oeste (chapa trocada) e amassados
n, R = FACES[4]
caixa(B('remendo', 'casco'), n * (AP + 0.024) + R @ Vector((0.1, 0, 0)) + Vector((0, 0, 0.22)), (0.15, 0.006, 0.09), R)
for sx in (-1, 1):
    for sz in (-1, 1):
        parafuso(n * (AP + 0.027) + R @ Vector((0.1 + sx * 0.062, 0, 0)) + Vector((0, 0, 0.22 + sz * 0.034)), n, r=0.008)
# convés: costuras de chapa, parafusos, óleo
for k in range(32):
    a = k * 2 * PI / 32
    cil(B('parafusos', 'aco'), Vector((math.cos(a), math.sin(a), 0)) * 0.64 + Vector((0, 0, ZD + 0.006)), 0.01, 0.012, lados=6)
for x in (-0.3, 0.3):
    caixa_de(B('costuras', 'chamusco'), (x - 0.002, -0.62, ZD), (x + 0.002, 0.62, ZD + 0.0008))
for k in range(9):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.5, 0.66)
    mancha(B('oleo', 'oleo'), (math.cos(a) * r, math.sin(a) * r), random.uniform(0.02, 0.05), ZD + 0.0012)
cil(B('rolamento', 'aco', True), Vector((0, 0, (ZD + ZG0) / 2)), 0.40, ZG0 - ZD, lados=48)

# ------------------------------------------------------------------ estabilizadores hidráulicos (diagonais)
R_MAC = 1.50                       # raio do macaco
JACKS = []
for k in (1, 3, 5, 7):
    d, R = FACES[k]
    t = R @ Vector((1, 0, 0))
    # moldura na face, luva amarela (fixa) e viga interna (telescópica, estendida)
    caixa(B('estab_moldura', 'ferro'), d * (AP + 0.016) + Vector((0, 0, 0.27)), (0.25, 0.03, 0.2), R)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parafuso(d * (AP + 0.032) + t * sx * 0.105 + Vector((0, 0, 0.27 + sz * 0.08)), d)
    caixa(B('estab_luva', 'amarelo'), d * 0.93 + Vector((0, 0, 0.27)), (0.17, 0.56, 0.14), R)
    caixa(B('estab_luva_boca', 'ferro'), d * 1.20 + Vector((0, 0, 0.27)), (0.19, 0.03, 0.16), R)
    caixa(B('estab_listras', 'listras'), d * 1.165 + Vector((0, 0, 0.341)), (0.17, 0.05, 0.003), R)
    caixa(B('estab_viga', 'casco'), d * 1.27 + Vector((0, 0, 0.28)), (0.13, 0.30, 0.09), R)
    for j in range(3):
        caixa(B('estab_risco', 'aco'), d * (1.24 + j * 0.05) + t * random.uniform(-0.04, 0.04) + Vector((0, 0, 0.3255)),
              (0.002, random.uniform(0.02, 0.05), 0.001), R)
    for x in (0.78, 0.95, 1.1):
        for sx in (-1, 1):
            parafuso(d * x + t * sx * 0.086 + Vector((0, 0, 0.30)), t * sx)
    # cabeçote do macaco
    P = d * R_MAC
    caixa(B('estab_cabecote', 'amarelo'), P + Vector((0, 0, 0.29)), (0.18, 0.18, 0.15), R)
    caixa(B('estab_cabecote_listras', 'listras'), P + d * 0.0905 + Vector((0, 0, 0.29)), (0.17, 0.002, 0.05), R)
    for sx in (-1, 1):
        for sz in (-1, 1):
            parafuso(P + d * 0.091 + t * sx * 0.07 + Vector((0, 0, 0.29 + sz * 0.055)), d)
    # macaco: camisa sobre o cabeçote, haste até a sapata
    cil(B('macaco_flange', 'ferro', True), P + Vector((0, 0, 0.372)), 0.078, 0.016, lados=28)
    cil(B('macaco_camisa', 'amarelo', True), P + Vector((0, 0, 0.52)), 0.058, 0.28, lados=28)
    cil(B('macaco_cabeca', 'ferro', True), P + Vector((0, 0, 0.67)), 0.066, 0.03, lados=28)
    cil(B('macaco_tampa', 'aco', True), P + Vector((0, 0, 0.69)), 0.04, 0.012, lados=20)
    for j in range(6):
        a = j * PI / 3
        parafuso(P + Vector((math.cos(a) * 0.066, math.sin(a) * 0.066, 0.383)), (0, 0, 1), r=0.008)
    cil(B('macaco_haste', 'cromo', True), P + Vector((0, 0, 0.18)), 0.034, 0.10, lados=24)
    caixa(B('macaco_oleo', 'oleo'), P + d * 0.0335 + Vector((0, 0, 0.18)), (0.006, 0.002, 0.07), R)
    cil(B('macaco_raspador', 'borracha', True), P + Vector((0, 0, 0.216)), 0.042, 0.012, lados=24)
    curva(B('macaco_rotula', 'aco', True), P + Vector((0, 0, 0.13)), 0.042, 16)
    cil(B('sapata', 'ferro', True), P + Vector((0, 0, 0.097)), 0.14, 0.034, lados=32)
    cil(B('sapata_colar', 'ferro', True), P + Vector((0, 0, 0.12)), 0.06, 0.02, lados=20)
    for j in range(6):
        a = j * PI / 3 + PI / 6
        q = P + Vector((math.cos(a) * 0.11, math.sin(a) * 0.11, 0.116))
        cil(B('parafusos', 'aco'), q, 0.012, 0.016, lados=6)
        caixa(B('sapata_nervura', 'ferro'), P + Vector((math.cos(a - PI / 6) * 0.09, math.sin(a - PI / 6) * 0.09, 0.124)),
              (0.06, 0.012, 0.024), Matrix.Rotation(a - PI / 6, 3, 'Z'))
    for j in range(4):                                                    # lama na sapata
        a = random.uniform(0, 2 * PI)
        mancha(B('lama', 'lama'), (P.x + math.cos(a) * 0.15, P.y + math.sin(a) * 0.15), random.uniform(0.03, 0.06), Z0 + 0.0012)
    mancha(B('oleo', 'oleo'), (P.x - d.x * 0.17, P.y - d.y * 0.17), 0.05, Z0 + 0.0014)
    # cilindro de extensão sobre a luva (camisa na luva, haste no cabeçote da viga)
    for x in (0.75, 1.38):
        caixa(B('estab_orelha', 'ferro'), d * x + Vector((0, 0, 0.37 if x < 1 else 0.37)), (0.07, 0.04, 0.07 if x < 1 else 0.09), R)
    tubo(B('ext_camisa', 'amarelo', True), d * 0.77 + Vector((0, 0, 0.385)), d * 1.09 + Vector((0, 0, 0.385)), 0.03, 20)
    tubo(B('ext_cabeca', 'ferro', True), d * 1.08 + Vector((0, 0, 0.385)), d * 1.10 + Vector((0, 0, 0.385)), 0.034, 20)
    tubo(B('ext_haste', 'cromo', True), d * 1.10 + Vector((0, 0, 0.385)), d * 1.37 + Vector((0, 0, 0.385)), 0.016, 16)
    for x in (0.75, 1.38):
        tubo(B('pino', 'aco', True), d * x + t * -0.045 + Vector((0, 0, 0.385)), d * x + t * 0.045 + Vector((0, 0, 0.385)), 0.01, 10)
    # caixa de junção na face e mangueiras até as portas do macaco
    J = d * (AP + 0.04) + t * 0.2 + Vector((0, 0, 0.25))
    caixa(B('juncao', 'amarelo2'), J, (0.1, 0.06, 0.12), R)
    for z in (0.21, 0.29):
        cil(B('conexoes', 'latao', True), J + d * 0.035 + Vector((0, 0, z - 0.25)), 0.012, 0.02, d, lados=12)
    for i, zp in enumerate((0.43, 0.62)):
        porta = P - d * 0.058 + t * 0.03 * (1 if i else -1) + Vector((0, 0, zp))
        cil(B('conexoes', 'latao', True), porta - d * 0.008, 0.012, 0.02, d, lados=12)
        pts = catmull([J + d * 0.05 + Vector((0, 0, -0.04 + 0.08 * i)), J + d * 0.12 + Vector((0, 0, 0.06 + 0.02 * i)),
                       d * 0.95 + t * (0.065 + 0.024 * i) + Vector((0, 0, 0.356)),
                       d * 1.3 + t * (0.065 + 0.024 * i) + Vector((0, 0, 0.356 + 0.01 * i)),
                       porta - d * 0.08 + Vector((0, 0, 0.0)), porta - d * 0.02], 6)
        mangueira(B('mangueiras', 'borracha', True), pts, 0.011)
        if i == 0:
            abracar(B('abracadeiras', 'aco', True), pts, 0.018, 7)
    for j in range(2):
        escorrido('base', d * (AP + 0.032) + t * (0.2 + random.uniform(-0.03, 0.03)) + Vector((0, 0, 0.19)), d, 0.08, 'oleo', 0.008)
    JACKS.append((d, R, t, P))

# ------------------------------------------------------------------ motor de giro (sudeste): fica abaixo da placa do giro
CM = DIR_MOTOR * 0.585
CP = DIR_MOTOR * (R_COROA + R_PINHAO)
RM = rot_face(DIR_MOTOR)
cil(B('motor', 'grafite', True), CM + Vector((0, 0, 0.47)), 0.058, 0.13, lados=24)
for j in range(4):
    cil(B('motor_aletas', 'ferro', True), CM + Vector((0, 0, 0.425 + j * 0.03)), 0.068, 0.007, lados=24)
cil(B('motor_tampa', 'ferro', True), CM + Vector((0, 0, 0.537)), 0.05, 0.012, lados=24)
caixa(B('motor', 'grafite'), CM + RM @ Vector((0.065, 0.0, 0)) + Vector((0, 0, 0.46)), (0.04, 0.05, 0.06), RM)
bm = B('redutor', 'amarelo', True)
caixa(bm, (CM + CP) / 2 + Vector((0, 0, 0.415)), (0.1, (CM - CP).length, 0.03), RM)
cil(bm, CP + Vector((0, 0, 0.415)), 0.045, 0.03, lados=20)
cil(B('pinhao_eixo', 'aco', True), CP + Vector((0, 0, 0.45)), 0.014, 0.08, lados=12)
pts = catmull([CM + RM @ Vector((0.085, 0, 0)) + Vector((0, 0, 0.46)), CM + RM @ Vector((0.12, 0.02, 0)) + Vector((0, 0, 0.43)),
               FACES[7][0] * (AP + 0.08) + FACES[7][1] @ Vector((-0.2, 0, 0)) + Vector((0, 0, 0.405)),
               FACES[7][0] * (AP + 0.035) + FACES[7][1] @ Vector((-0.2, 0, 0)) + Vector((0, 0, 0.3))], 6)
mangueira(B('cabos', 'cabo', True), pts, 0.012)
pinhao = bpy.data.objects.new('pinhao', None)
sc.collection.objects.link(pinhao)
pinhao.location = CP + Vector((0, 0, (ZG0 + ZG1) / 2))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), R_PINHAO - 0.008, ZG1 - ZG0, lados=20)
for k in range(13):
    a = k * 2 * PI / 13
    caixa(bm, Vector((math.cos(a), math.sin(a), 0)) * R_PINHAO, (0.018, 0.014, ZG1 - ZG0), Matrix.Rotation(a, 3, 'Z'))
obj('pinhao_dentes', bm, 'aco', pinhao)
for k in range(5):
    mancha(B('oleo', 'oleo'), (CP.x + random.uniform(-0.05, 0.05), CP.y + random.uniform(-0.05, 0.05)), random.uniform(0.015, 0.03), ZD + 0.0016)

# ------------------------------------------------------------------ unidade hidráulica (leste)
caixa_de(B('hpu_skid', 'ferro'), (0.82, -0.44, Z0), (1.42, 0.44, 0.13))
for y in (-0.42, 0.42):
    caixa_de(B('hpu_skid', 'ferro'), (0.82, y - 0.02, 0.13), (1.42, y + 0.02, 0.16))
for x in (0.85, 1.39):
    for y in (-0.41, 0.41):
        parafuso((x, y, 0.136), (0, 0, 1))
TQ = Vector((1.24, 0.06, 0.34))
cil(B('hpu_tanque', 'amarelo', True), TQ, 0.15, 0.58, Vector((0, 1, 0)), lados=36)
for s in (-1, 1):
    cil(B('hpu_tanque_tampa', 'ferro', True), TQ + Vector((0, s * 0.295, 0)), 0.155, 0.014, Vector((0, 1, 0)), lados=36)
    caixa_de(B('hpu_berco', 'ferro'), (1.1, TQ.y + s * 0.18 - 0.02, 0.13), (1.38, TQ.y + s * 0.18 + 0.02, 0.24))
    toro(B('hpu_cinta', 'aco', True), TQ + Vector((0, s * 0.18, 0)), 0.152, 0.006, 40, 6, Matrix.Rotation(PI / 2, 3, 'X'))
for j in range(12):
    a = j * PI / 6
    parafuso(TQ + Vector((math.cos(a) * 0.13, 0.304, math.sin(a) * 0.13)), (0, 1, 0), r=0.007)
cil(B('hpu_bocal', 'ferro', True), TQ + Vector((0.05, -0.12, 0.155)), 0.03, 0.04, lados=16)
cil(B('hpu_respiro', 'aco', True), TQ + Vector((-0.04, 0.15, 0.16)), 0.012, 0.06, lados=10)
caixa_de(B('hpu_nivel', 'ferro'), (1.083, -0.07, 0.27), (1.093, 0.13, 0.42))
caixa_de(B('hpu_nivel_vidro', 'vidro'), (1.08, -0.05, 0.29), (1.085, 0.11, 0.40))
caixa_de(B('hpu_nivel_oleo', 'oleo'), (1.079, -0.05, 0.29), (1.0805, 0.11, 0.35))
caixa_de(B('hpu_listras', 'listras'), (1.39, -0.23, 0.26), (1.392, 0.35, 0.3))
for j in range(5):
    escorrido('base', TQ + Vector((-0.12 + j * 0.06, -0.296, random.uniform(-0.05, 0.08))), Vector((0, -1, 0)), random.uniform(0.05, 0.12), 'oleo', 0.007)
MP = Vector((0.98, -0.27, 0.25))                                          # motor-bomba ao longo de y
cil(B('hpu_motor', 'grafite', True), MP, 0.085, 0.24, Vector((0, 1, 0)), lados=28)
for j in range(7):
    cil(B('hpu_motor_aletas', 'ferro', True), MP + Vector((0, -0.1 + j * 0.033, 0)), 0.095, 0.008, Vector((0, 1, 0)), lados=28)
cil(B('hpu_motor_tampa', 'ferro', True), MP + Vector((0, -0.13, 0)), 0.07, 0.02, Vector((0, 1, 0)), lados=24)
cil(B('hpu_acopl', 'aco', True), MP + Vector((0, 0.14, 0)), 0.04, 0.05, Vector((0, 1, 0)), lados=16)
cil(B('hpu_bomba', 'amarelo2', True), MP + Vector((0, 0.21, 0)), 0.06, 0.09, Vector((0, 1, 0)), lados=20)
caixa_de(B('hpu_motor_pe', 'ferro'), (0.9, -0.36, 0.13), (1.06, -0.18, 0.18))
caixa_de(B('hpu_caixa_lig', 'grafite'), (0.94, -0.33, 0.33), (1.02, -0.24, 0.37))
VB = Vector((0.96, 0.2, 0.22))                                            # bloco de válvulas
caixa(B('hpu_valvulas', 'ferro'), VB, (0.14, 0.2, 0.12))
for j in range(4):
    cil(B('hpu_solenoide', 'amarelo', True), VB + Vector((0.0, -0.075 + j * 0.05, 0.1)), 0.018, 0.08, lados=14)
    cil(B('led_ambar' if j == 2 else 'led_verde', 'led_ambar' if j == 2 else 'led_verde'), VB + Vector((0.0, -0.075 + j * 0.05, 0.142)), 0.008, 0.004, lados=10)
SAIDAS = []
for j in range(4):
    p = VB + Vector((-0.07, -0.075 + j * 0.05, -0.02))
    cil(B('conexoes', 'latao', True), p - Vector((0.01, 0, 0)), 0.012, 0.02, Vector((1, 0, 0)), lados=12)
    SAIDAS.append(p - Vector((0.02, 0, 0)))
for j, y in enumerate((0.13, 0.27)):                                     # manômetros
    g = VB + Vector((0.0, y - 0.2, 0.0)) + Vector((0, 0, 0.0))
    g = Vector((1.03, y, 0.3))
    tubo(B('hpu_mano_haste', 'latao', True), (1.0, y, 0.28), g, 0.006, 8)
    cil(B('hpu_mano', 'aco', True), g, 0.035, 0.02, Vector((1, 0, 0)), lados=24)
    cil(B('hpu_mano_vidro', 'vidro', True), g + Vector((0.011, 0, 0)), 0.029, 0.002, Vector((1, 0, 0)), lados=24)
    caixa(B('hpu_mano_ponteiro', 'vermelho'), g + Vector((0.013, 0, 0.008)), (0.001, 0.003, 0.022), Matrix.Rotation(0.6 - j, 3, 'X'))
cil(B('hpu_acumulador', 'vermelho', True), Vector((1.0, 0.38, 0.32)), 0.045, 0.32, lados=24)
curva(B('hpu_acumulador', 'vermelho', True), Vector((1.0, 0.38, 0.48)), 0.045, 20)
cil(B('hpu_acumulador_valv', 'latao', True), Vector((1.0, 0.38, 0.53)), 0.012, 0.03, lados=10)
for pts, r in ((catmull([TQ + Vector((-0.12, -0.2, -0.08)), Vector((1.08, -0.05, 0.16)), MP + Vector((0, 0.25, -0.05))], 6), 0.02),
               (catmull([MP + Vector((0, 0.25, 0.06)), Vector((1.02, 0.08, 0.36)), VB + Vector((0.03, -0.1, 0.06))], 6), 0.014),
               (catmull([VB + Vector((0.03, 0.1, 0.0)), Vector((1.0, 0.32, 0.18)), Vector((1.0, 0.38, 0.16))], 5), 0.012)):
    mangueira(B('mangueiras', 'borracha', True), pts, r)
ENTR = []
for j in range(4):                                                        # válvulas → face leste da plataforma
    alvo = Vector((AP + 0.024, -0.12 + j * 0.08, 0.2 + 0.012 * (j % 2)))
    cil(B('conexoes', 'latao', True), alvo + Vector((0.008, 0, 0)), 0.013, 0.02, Vector((1, 0, 0)), lados=12)
    pts = catmull([SAIDAS[j], SAIDAS[j] + Vector((-0.06, 0, -0.03)), Vector((0.8, -0.1 + j * 0.07, 0.15)), alvo + Vector((0.05, 0, 0)), alvo + Vector((0.016, 0, 0))], 6)
    mangueira(B('mangueiras', 'borracha', True), pts, 0.011)
    ENTR.append(pts)
abracar(B('abracadeiras', 'aco', True), ENTR[1], 0.04, 8)
for k in range(5):
    mancha(B('oleo', 'oleo'), (random.uniform(0.85, 1.38), random.uniform(-0.4, 0.4)), random.uniform(0.03, 0.07), 0.1306)

# ------------------------------------------------------------------ armário de força (norte) e rede
caixa_de(B('armario', 'grafite'), (-0.3, 0.86, Z0), (0.3, 1.2, 0.66))
caixa_de(B('armario_porta', 'amarelo'), (-0.27, 1.2, 0.12), (0.27, 1.215, 0.62))
caixa_de(B('armario_tampa', 'ferro'), (-0.31, 0.85, 0.66), (0.31, 1.21, 0.68))
caixa_de(B('armario_listras', 'listras'), (-0.27, 1.216, 0.5), (0.27, 1.22, 0.56))
for x in (-0.24, 0.24):
    for z in (0.16, 0.58):
        parafuso((x, 1.222, z), (0, 1, 0))
for x in (-0.12, 0.12):
    caixa_de(B('armario_dobradica', 'aco'), (x - 0.02, 1.215, 0.6), (x + 0.02, 1.225, 0.615))
for k, m in enumerate(('led_verde', 'led_verde', 'led_ambar', 'led_verm')):
    cil(B('led_' + m, m), Vector((-0.12 + k * 0.06, 1.218, 0.44)), 0.009, 0.006, Vector((0, 1, 0)), lados=10)
for j in range(5):
    caixa_de(B('armario_venezianas', 'ferro'), (-0.29, 0.86 - 0.004, 0.3 + j * 0.05), (0.29, 0.862, 0.32 + j * 0.05))
ISO = []
for i, x in enumerate((-0.16, 0.0, 0.16)):
    base = Vector((x, 1.03, 0.68))
    cil(B('porcelana', 'porcelana', True), base + Vector((0, 0, 0.06)), 0.016, 0.12, lados=14)
    for j in range(4):
        cil(B('porcelana', 'porcelana', True), base + Vector((0, 0, 0.02 + j * 0.028)), 0.036, 0.01, lados=18)
    cil(B('iso_grampo', 'cobre', True), base + Vector((0, 0, 0.135)), 0.016, 0.03, lados=12)
    ISO.append(base + Vector((0, 0, 0.14)))
EL = Vector((0.0, 1.38, 0))
cil(B('eletroduto', 'ferro', True), EL + Vector((0, 0, Z0 + 0.05)), 0.07, 0.1, lados=20)
cil(B('eletroduto', 'ferro', True), EL + Vector((0, 0, Z0 + 0.1)), 0.08, 0.012, lados=20)
for i in range(3):
    dx = (i - 1) * 0.04
    pts = catmull([EL + Vector((dx, 0, Z0 + 0.1)), EL + Vector((dx, -0.02, 0.5)), ISO[i] + Vector((0, 0.16, 0.12)), ISO[i] + Vector((0, 0.015, 0.0))], 6)
    mangueira(B('cabos', 'cabo', True), pts, 0.016)
for i, x in enumerate((-0.08, 0.08)):                                     # armário → face norte da plataforma
    cil(B('prensa_cabo', 'ferro', True), Vector((x, AP + 0.03, 0.22)), 0.028, 0.03, Vector((0, 1, 0)), lados=16)
    cil(B('prensa_cabo', 'ferro', True), Vector((x, 0.85, 0.22)), 0.028, 0.03, Vector((0, 1, 0)), lados=16)
    pts = catmull([Vector((x, 0.84, 0.22)), Vector((x + 0.03, 0.78, 0.16)), Vector((x, AP + 0.04, 0.22))], 5)
    mangueira(B('cabos', 'cabo', True), pts, 0.02)
pts = catmull([Vector((0.3, 0.95, 0.2)), Vector((0.5, 0.8, 0.14)), Vector((0.85, 0.5, 0.11)), Vector((0.98, -0.1, 0.12)), Vector((0.98, -0.27, 0.33))], 8)
mangueira(B('cabos', 'cabo', True), pts, 0.013)                            # força do motor-bomba
for p in pts[6:30:8]:
    caixa(B('calhas', 'ferro'), Vector((p.x, p.y, Z0 + 0.012)), (0.05, 0.05, 0.024))

# ------------------------------------------------------------------ defletor de jato (oeste) com ladrilho refratário
A0, A1 = math.radians(150), math.radians(212)
RD0, RD1 = 0.92, 1.32
ZDF0, ZDF1 = 0.10, 0.36
INCL = math.atan2(ZDF1 - ZDF0, RD1 - RD0)
NSEG = 11
for j in range(NSEG):
    a = A0 + (j + 0.5) * (A1 - A0) / NSEG
    d = Vector((math.cos(a), math.sin(a), 0))
    R = rot_face(d)
    Rt = R @ Matrix.Rotation(INCL, 3, 'X')
    w = 2 * ((RD0 + RD1) / 2) * math.sin((A1 - A0) / NSEG / 2) - 0.004
    c = d * ((RD0 + RD1) / 2) + Vector((0, 0, (ZDF0 + ZDF1) / 2 - 0.02))
    L = math.hypot(RD1 - RD0, ZDF1 - ZDF0)
    caixa(B('defletor_chapa', 'ferro'), c, (w, L, 0.03), Rt)
    for ti in range(4):
        for tj in range(2):
            tc = c + Rt @ Vector(((tj - 0.5) * w / 2, (ti - 1.5) * L / 4, 0.02))
            m = 'chamusco' if (j in (6, 7, 8) and ti < 3) or random.random() < 0.25 else 'refratario'
            caixa(B('defletor_ladrilho_' + m, m), tc, (w / 2 - 0.008, L / 4 - 0.008, 0.012), Rt)
    caixa(B('defletor_parede', 'ferro'), d * (RD1 + 0.02) + Vector((0, 0, (Z0 + ZDF1 + 0.04) / 2)), (w + 0.004, 0.03, ZDF1 + 0.04 - Z0), R)
    for sx in (-1, 1):
        parafuso(d * (RD1 + 0.037) + R @ Vector((sx * w * 0.3, 0, 0)) + Vector((0, 0, 0.22)), d, r=0.009)
for j in range(NSEG + 1):                                                  # nervuras de apoio
    a = A0 + j * (A1 - A0) / NSEG
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('defletor_nervura', 'casco'), d * (RD0 + RD1) / 2 * 1.02 + Vector((0, 0, (Z0 + 0.25) / 2)), (0.02, (RD1 - RD0) * 0.8, 0.25 - Z0), rot_face(d))
    cil(B('parafusos', 'aco'), d * (RD1 - 0.02) + Vector((0, 0, Z0 + 0.006)), 0.012, 0.012, lados=6)
caixa(B('defletor_listras', 'listras'), Vector((math.cos(A0), math.sin(A0), 0)) * 1.12 + Vector((0, 0, Z0 + 0.001)), (0.03, 0.45, 0.002), rot_face(Vector((math.cos(A0), math.sin(A0), 0))))

# ------------------------------------------------------------------ paiol (sul) com boca de entrada e visor
caixa_de(B('paiol', 'grafite'), (-0.30, PY0, Z0), (0.20, PY1, PZ1 - 0.02))
for a_, b_ in (((0.20, PY0, Z0), (0.30, -1.32, PZ1 - 0.02)), ((0.20, -0.86, Z0), (0.30, PY1, PZ1 - 0.02)),
               ((0.20, -1.32, Z0), (0.30, -0.86, 0.22)), ((0.20, -1.32, 0.74), (0.30, -0.86, PZ1 - 0.02))):
    caixa_de(B('paiol', 'grafite'), a_, b_)
# tampo com a escotilha (vão em x de -0.06 a 0.06)
caixa_de(B('paiol_tampo', 'ferro'), (-0.31, PY0 - 0.01, PZ1 - 0.02), (-0.065, PY1 + 0.01, PZ1))
caixa_de(B('paiol_tampo', 'ferro'), (0.065, PY0 - 0.01, PZ1 - 0.02), (0.31, PY1 + 0.01, PZ1))
caixa_de(B('paiol_tampo', 'ferro'), (-0.065, PY0 - 0.01, PZ1 - 0.02), (0.065, PY0 + 0.03, PZ1))
caixa_de(B('paiol_tampo', 'ferro'), (-0.065, PY1 - 0.03, PZ1 - 0.02), (0.065, PY1 + 0.01, PZ1))
caixa_de(B('paiol_vao', 'escuro'), (-0.065, PY0 + 0.03, PZ1 - 0.0198), (0.065, PY1 - 0.03, PZ1 - 0.0195))
caixa_de(B('paiol_listras', 'listras'), (-0.12, PY0 + 0.02, PZ1), (-0.065, PY1 - 0.02, PZ1 + 0.002))
caixa_de(B('paiol_listras', 'listras'), (0.065, PY0 + 0.02, PZ1), (0.12, PY1 - 0.02, PZ1 + 0.002))
for x in (-0.27, -0.16, 0.16, 0.27):
    for y in (PY0 + 0.03, (PY0 + PY1) / 2, PY1 - 0.03):
        parafuso((x, y, PZ1 + 0.006), (0, 0, 1), r=0.009)
for sx in (-1, 1):                                                        # cantoneiras amarelas
    for sy in (-1, 1):
        x0, x1 = (0.278, 0.306) if sx > 0 else (-0.306, -0.278)
        y0, y1 = (PY0 - 0.006, PY0 + 0.022) if sy < 0 else (PY1 - 0.022, PY1 + 0.006)
        caixa_de(B('paiol_canto', 'amarelo'), (x0, y0, Z0), (x1, y1, PZ1 - 0.02))
for z in (0.3, 0.6):                                                      # cintas
    caixa_de(B('paiol_cinta', 'amarelo2'), (-0.305, PY0 - 0.006, z - 0.02), (0.305, PY1 + 0.006, z + 0.02))
caixa_de(B('paiol_faixa', 'vermelho'), (-0.305, PY0 - 0.008, 0.68), (0.305, PY0 - 0.002, 0.72))
caixa_de(B('paiol_faixa', 'vermelho'), (-0.305, PY1 + 0.002, 0.68), (0.305, PY1 + 0.008, 0.72))
# alívio de explosão no tampo (chapa fina aparafusada)
# boca de entrada (S1): vão, moldura, cortina de borracha, mesa de rolos, listras
caixa_de(B('boca_vao', 'escuro'), (-0.075, PY0 - 0.004, 0.14), (0.075, PY0 + 0.01, 0.27))
for sx in (-1, 1):
    caixa_de(B('boca_moldura', 'ferro'), (sx * 0.09 - 0.015, PY0 - 0.016, 0.12), (sx * 0.09 + 0.015, PY0, 0.29))
caixa_de(B('boca_moldura', 'ferro'), (-0.105, PY0 - 0.016, 0.27), (0.105, PY0, 0.295))
caixa_de(B('boca_listras', 'listras'), (-0.14, PY0 - 0.012, 0.31), (0.14, PY0, 0.36))
for j in range(6):
    x = -0.0625 + j * 0.025
    caixa(B('boca_cortina', 'borracha'), Vector((x, PY0 - 0.006, 0.225 + (0.012 if j in (2, 3) else 0))), (0.022, 0.004, 0.09 - (0.024 if j in (2, 3) else 0)),
          Matrix.Rotation(0.15 if j in (2, 3) else 0.0, 3, 'X'))
    caixa(B('boca_cortina', 'borracha'), Vector((x, PY0 - 0.006, 0.264)), (0.022, 0.004, 0.012))
for sx in (-1, 1):
    caixa_de(B('rolos_lado', 'amarelo'), (sx * 0.1 - 0.01, -1.475, 0.1), (sx * 0.1 + 0.01, PY0 - 0.016, 0.17))
for y in (-1.455, -1.425, -1.395):
    cil(B('rolos', 'aco', True), Vector((0, y, 0.145)), 0.011, 0.19, Vector((1, 0, 0)), lados=12)
# visor leste com o estoque de foguetes
XW = 0.30
caixa_de(B('visor_fundo', 'escuro'), (0.2, -1.32, 0.22), (0.205, -0.86, 0.74))
for a_, b_ in (((0.21, -1.32, 0.22), (XW + 0.004, -1.31, 0.74)), ((0.21, -0.87, 0.22), (XW + 0.004, -0.86, 0.74)),
               ((0.21, -1.32, 0.22), (XW + 0.004, -0.86, 0.24)), ((0.21, -1.32, 0.72), (XW + 0.004, -0.86, 0.74))):
    caixa_de(B('visor_nicho', 'grafite'), a_, b_)
for y in (-1.33, -0.85):
    caixa_de(B('visor_quadro', 'ferro'), (XW, y - 0.012, 0.21), (XW + 0.016, y + 0.012, 0.75))
for z in (0.22, 0.74):
    caixa_de(B('visor_quadro', 'ferro'), (XW, -1.34, z - 0.012), (XW + 0.016, -0.84, z + 0.012))
for y in (-1.2, -1.09, -0.98):
    tubo(B('visor_grade', 'aco'), (XW - 0.006, y, 0.24), (XW - 0.006, y, 0.72), 0.004, 6)
for z in (0.28, 0.43, 0.58):
    caixa_de(B('visor_prateleira', 'ferro'), (0.205, -1.32, z - 0.04), (0.29, -0.86, z - 0.032))
cil(B('luz_paiol', 'luz_paiol', True), Vector((0.25, -1.09, 0.71)), 0.012, 0.18, Vector((0, 1, 0)), lados=10)
# motor do elevador (oeste) e cabo até a plataforma
cil(B('paiol_motor', 'grafite', True), Vector((-0.36, -1.09, 0.5)), 0.06, 0.12, Vector((1, 0, 0)), lados=24)
for j in range(4):
    cil(B('paiol_motor_aletas', 'ferro', True), Vector((-0.33 - j * 0.025, -1.09, 0.5)), 0.068, 0.006, Vector((1, 0, 0)), lados=24)
caixa_de(B('paiol_motor_flange', 'ferro'), (-0.31, -1.16, 0.43), (-0.3, -1.02, 0.57))
caixa_de(B('paiol_motor_cx', 'grafite'), (-0.4, -1.13, 0.56), (-0.33, -1.05, 0.6))
pts = catmull([Vector((-0.37, -1.09, 0.6)), Vector((-0.4, -1.0, 0.66)), Vector((-0.32, -0.82, 0.3)), Vector((-0.2, -AP - 0.06, 0.22)), Vector((-0.2, -AP - 0.02, 0.22))], 6)
mangueira(B('cabos', 'cabo', True), pts, 0.014)
cil(B('prensa_cabo', 'ferro', True), Vector((-0.2, -AP - 0.022, 0.22)), 0.026, 0.03, Vector((0, 1, 0)), lados=16)
for j in range(6):
    escorrido('base', Vector((random.uniform(-0.25, 0.25), PY0 - 0.003, random.uniform(0.5, 0.78))), Vector((0, -1, 0)), random.uniform(0.06, 0.18),
              'ferrugem' if j % 2 else 'chamusco', random.uniform(0.006, 0.014))
for k in range(4):
    mancha(B('po', 'po'), (random.uniform(-0.25, 0.25), random.uniform(PY0 + 0.05, PY1 - 0.05)), random.uniform(0.03, 0.06), PZ1 + 0.0012)

# ------------------------------------------------------------------ trilho do braço no convés
for y in (AY - 0.045, AY + 0.045):
    caixa_de(B('trilho', 'aco'), (-0.28, y - 0.012, ZD), (0.28, y + 0.012, ZD + 0.03))
caixa_de(B('cremalheira', 'ferro'), (-0.27, AY - 0.006, ZD), (0.27, AY + 0.006, ZD + 0.022))
for x in (-0.28, 0.28):
    caixa_de(B('trilho_batente', 'amarelo'), (x - 0.015, AY - 0.07, ZD), (x + 0.015, AY + 0.07, ZD + 0.06))
    caixa_de(B('trilho_batente_bor', 'borracha'), (x - 0.02 * (1 if x < 0 else -1) - 0.006, AY - 0.05, ZD + 0.015), (x - 0.02 * (1 if x < 0 else -1) + 0.006, AY + 0.05, ZD + 0.05))
for x in (-0.24, -0.08, 0.08, 0.24):
    for y in (AY - 0.045, AY + 0.045):
        parafuso((x, y, ZD + 0.034), (0, 0, 1), r=0.007)
# esteira porta-cabos (fixa no convés, ponta no carro)
bm = B('porta_cabos', 'borracha')
for j in range(14):
    x = -0.26 + j * 0.02
    caixa(bm, Vector((x, AY + 0.1, ZD + 0.02)), (0.018, 0.05, 0.03))

# ------------------------------------------------------------------ giro
giro = bpy.data.objects.new('giro', None)
sc.collection.objects.link(giro)
G = 'giro'
cil(B('coroa', 'aco', True, G), Vector((0, 0, (ZG0 + ZG1) / 2)), R_COROA - 0.012, ZG1 - ZG0, lados=72)
for k in range(88):
    a = k * 2 * PI / 88
    caixa(B('coroa_dentes', 'aco', False, G), Vector((math.cos(a), math.sin(a), 0)) * (R_COROA - 0.004) + Vector((0, 0, (ZG0 + ZG1) / 2)),
          (0.026, 0.016, ZG1 - ZG0), Matrix.Rotation(a, 3, 'Z'))
cil(B('mesa', 'ferro', True, G), Vector((0, 0, (ZG1 + ZM) / 2)), 0.46, ZM - ZG1, lados=64)
for k in range(24):
    a = k * 2 * PI / 24
    cil(B('parafusos', 'aco', False, G), Vector((math.cos(a), math.sin(a), 0)) * 0.43 + Vector((0, 0, ZM + 0.006)), 0.01, 0.012, lados=6)
caixa_de(B('placa_giro', 'grafite', False, G), (-0.30, -0.36, ZM), (0.40, 0.36, ZP))
for x in (-0.26, 0.05, 0.36):
    for s in (-1, 1):
        parafuso((x, s * 0.33, ZP + 0.006), (0, 0, 1), G)
caixa_de(B('placa_listras', 'listras', False, G), (0.36, -0.36, ZP), (0.40, 0.36, ZP + 0.002))
PERFIL = [(-0.22, ZP), (0.30, ZP), (0.30, 0.98), (0.15, 1.24), (-0.10, 1.24), (-0.22, 1.12)]
for s in (-1, 1):
    y0, y1 = (YB0, YB1) if s > 0 else (-YB1, -YB0)
    prisma_xz(B('bochechas', 'amarelo', False, G), PERFIL, y0, y1)
    yo = s * (YB1 + 0.002)
    for x, z in ((-0.17, 0.7), (-0.17, 1.08), (-0.06, 1.2), (0.1, 1.2), (0.25, 0.7), (0.25, 0.95), (0.05, 0.7)):
        parafuso((x, yo, z), (0, s, 0), G, 0.011)
    cil(B('mancal', 'ferro', True, G), Vector((0, s * 0.305, TZ)), 0.095, 0.05, Vector((0, 1, 0)), lados=32)
    cil(B('mancal_tampa', 'aco', True, G), Vector((0, s * 0.336, TZ)), 0.06, 0.012, Vector((0, 1, 0)), lados=24)
    for k in range(6):
        a = k * PI / 3
        parafuso((math.cos(a) * 0.078, s * 0.333, TZ + math.sin(a) * 0.078), (0, s, 0), G, 0.009)
    caixa_de(B('bochecha_listras', 'listras', False, G), (-0.22, y0 - 0.001, ZP + 0.02), (0.3, y1 + 0.001, ZP + 0.06))
    for k in range(4):                                                    # fuligem da salva na bochecha
        z = random.uniform(0.75, 1.15)
        caixa(B('fuligem', 'chamusco', False, G), Vector((random.uniform(-0.2, -0.05), s * (YB1 + 0.0015), z)),
              (random.uniform(0.04, 0.1), 0.002, random.uniform(0.02, 0.06)))
    # caixa de eletrônica atrás da bochecha, com aletas e feixe até o mancal
    ye = s * 0.325
    caixa_de(B('eletronica', 'grafite', False, G), (-0.30, ye - 0.035, ZP), (-0.04, ye + 0.035, 0.86))
    caixa_de(B('eletronica_tampa', 'ferro', False, G), (-0.305, ye - 0.045, 0.86), (-0.035, ye + 0.045, 0.875))
    for j in range(8):
        x = -0.28 + j * 0.03
        caixa_de(B('eletronica_aletas', 'aco', False, G), (x - 0.004, min(ye + s * 0.035, ye + s * 0.06), 0.66), (x + 0.004, max(ye + s * 0.035, ye + s * 0.06), 0.83))
    for k, m in enumerate(('led_verde', 'led_ambar', 'led_verde')):
        cil(B('led_' + m, m, False, G), Vector((-0.31, ye - 0.02 + k * 0.02, 0.8)), 0.006, 0.006, Vector((-1, 0, 0)), lados=10)
    caixa_de(B('eletronica_ia', 'ia', False, G), (-0.302, ye - 0.03, 0.7), (-0.3, ye + 0.03, 0.705))
    pts = catmull([Vector((-0.12, ye, 0.875)), Vector((-0.1, ye, 0.95)), Vector((-0.08, s * 0.34, 1.05)), Vector((-0.06, s * 0.335, TZ - 0.04))], 5)
    feixe(B('cabos', 'cabo', True, G), B('abracadeiras', 'aco', True, G), pts, Vector((1, 0, 0)), n=3, r=0.01, passo=6)
# garfos dos pistões de elevação (camisa) e válvulas
A_PIS = Vector((0.32, 0.0, 0.67))
YP = 0.10
B_PIS = Vector((0.22, 0.0, -0.25))
for s in (-1, 1):
    y = s * YP
    for dy in (-0.035, 0.035):
        caixa_de(B('garfo', 'ferro', False, G), (A_PIS.x - 0.04, y + dy - 0.008, ZP), (A_PIS.x + 0.04, y + dy + 0.008, A_PIS.z + 0.035))
    cil(B('pino', 'aco', True, G), Vector((A_PIS.x, y, A_PIS.z)), 0.012, 0.095, Vector((0, 1, 0)), lados=12)
    caixa_de(B('valvula', 'amarelo2', False, G), (0.16, y - 0.035, ZP), (0.24, y + 0.035, ZP + 0.06))
    for k in range(2):
        mancha(B('oleo', 'oleo', False, G), (A_PIS.x + random.uniform(-0.06, 0.04), y + random.uniform(-0.04, 0.04)), random.uniform(0.015, 0.03), ZP + 0.0012)
# mastro do radar sobre a caixa de eletrônica do lado −y
RAD = Vector((-0.17, -0.33, 1.52))
tubo(B('mastro', 'aco', True, G), (RAD.x, RAD.y, 0.875), (RAD.x, RAD.y, RAD.z - 0.03), 0.022, 16)
cil(B('mastro_base', 'ferro', True, G), Vector((RAD.x, RAD.y, 0.89)), 0.04, 0.03, lados=16)
for z in (1.05, 1.3):
    cil(B('mastro_anel', 'ferro', True, G), Vector((RAD.x, RAD.y, z)), 0.028, 0.02, lados=16)
cil(B('mastro_topo', 'grafite', True, G), Vector((RAD.x, RAD.y, RAD.z - 0.02)), 0.04, 0.04, lados=20)
pts = catmull([Vector((RAD.x + 0.02, RAD.y - 0.03, 0.88)), Vector((RAD.x + 0.025, RAD.y - 0.03, 1.2)), Vector((RAD.x + 0.03, RAD.y - 0.035, RAD.z - 0.04))], 6)
mangueira(B('cabos', 'cabo', True, G), pts, 0.007)
abracar(B('abracadeiras', 'aco', True, G), pts, 0.01, 4)
# olho da IA na frente da placa
cil(B('olho_caixa', 'grafite', True, G), Vector((0.37, 0.25, ZP + 0.04)), 0.035, 0.05, Vector((1, 0, 0)), lados=20)
cil(B('olho', 'olho', False, G), Vector((0.396, 0.25, ZP + 0.04)), 0.024, 0.004, Vector((1, 0, 0)), lados=20)

radar = bpy.data.objects.new('radar', None)
sc.collection.objects.link(radar)
radar.parent = giro
radar.location = RAD
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.01)), 0.035, 0.03, lados=20)
caixa_de(bm, (-0.02, -0.02, 0.02), (0.13, 0.02, 0.05))
obj('radar_braco', bm, 'grafite', radar)
bm = bmesh.new()                                                         # antena plana com elementos
caixa_de(bm, (0.13, -0.18, 0.0), (0.15, 0.18, 0.14))
obj('radar_painel', bm, 'amarelo2', radar)
bm = bmesh.new()
for i in range(7):
    for j in range(3):
        caixa_de(bm, (0.149, -0.165 + i * 0.05, 0.015 + j * 0.042), (0.158, -0.135 + i * 0.05, 0.037 + j * 0.042))
obj('radar_elementos', bm, 'aco', radar)
bm = bmesh.new()
caixa_de(bm, (0.157, -0.17, 0.066), (0.16, 0.17, 0.072))
obj('radar_ia', bm, 'ia', radar)
bm = bmesh.new()
caixa_de(bm, (0.125, -0.185, -0.006), (0.155, 0.185, 0.004))
caixa_de(bm, (0.125, -0.185, 0.136), (0.155, 0.185, 0.146))
caixa_de(bm, (-0.08, -0.03, 0.015), (-0.02, 0.03, 0.06))                 # contrapeso
obj('radar_quadro', bm, 'ferro', radar)
bm = bmesh.new()
cil(bm, Vector((-0.05, 0, 0.068)), 0.008, 0.02, lados=8)
obj('radar_led', bm, 'led_verm', radar)

# ------------------------------------------------------------------ casulo de tubos (inclina no munhão)
casulo = bpy.data.objects.new('casulo', None)
sc.collection.objects.link(casulo)
casulo.parent = giro
casulo.location = (0, 0, TZ)
K = 'casulo'
E = 0.012
bm = B('casulo_chapa', 'amarelo', False, K)
caixa_de(bm, (PX0, -PH - E, PH), (PX1, PH + E, PH + E))
caixa_de(bm, (PX0, -PH - E, -PH - E), (PX1, PH + E, -PH))
caixa_de(B('casulo_lado', 'amarelo', False, K), (PX0, PH, -PH), (PX1, PH + E, PH))
caixa_de(B('casulo_lado', 'amarelo2', False, K), (PX0, -PH - E, -PH), (PX1, -PH, PH))
placa_furos(B('casulo_frente', 'queimado', False, K), PX1 - 0.03, PX1, CENTROS, SP / 2, RO)
placa_furos(B('casulo_tras', 'queimado', False, K), PX0, PX0 + 0.03, CENTROS, SP / 2, RO)
for yc, zc in CENTROS:
    torno(B('tubos', 'tubo_int', True, K), [(PX0, RI), (PX1, RI), (PX1, RO), (PX0, RO)], 28, fechado=True, c=(yc, zc))
for x in (-0.33, -0.05, 0.25, 0.38):                                     # cintas de reforço
    bm = B('casulo_cintas', 'aco', False, K)
    caixa_de(bm, (x - 0.014, -PH - E - 0.01, PH + E), (x + 0.014, PH + E + 0.01, PH + E + 0.01))
    caixa_de(bm, (x - 0.014, -PH - E - 0.01, -PH - E - 0.01), (x + 0.014, PH + E + 0.01, -PH - E))
    for s in (-1, 1):
        caixa_de(bm, (x - 0.014, s * (PH + E) - 0.005 + 0.005 * s, -PH - E - 0.01), (x + 0.014, s * (PH + E) + 0.005 + 0.005 * s, PH + E + 0.01))
    for s in (-1, 1):
        for zz in (-0.15, 0.0, 0.15):
            parafuso((x, s * (PH + E + 0.011), zz), (0, s, 0), K, 0.007)
for x, z in ((-0.2, 0.1), (0.1, -0.1), (0.1, 0.1)):
    for s in (-1, 1):
        parafuso((x, s * (PH + E + 0.001), z), (0, s, 0), K, 0.009)
caixa_de(B('casulo_listras', 'listras', False, K), (PX1 - 0.05, -PH - E - 0.001, PH - 0.04), (PX1 - 0.002, PH + E + 0.001, PH + E + 0.001))
caixa_de(B('casulo_ia', 'ia', False, K), (0.0, PH + E, 0.1), (0.2, PH + E + 0.002, 0.11))
# munhões, olhais de içamento, orelhas dos pistões
for s in (-1, 1):
    cil(B('munhao', 'aco', True, K), Vector((0, s * 0.27, 0)), 0.05, 0.14, Vector((0, 1, 0)), lados=24)
    cil(B('munhao_colar', 'ferro', True, K), Vector((0, s * (PH + E + 0.01), 0)), 0.075, 0.02, Vector((0, 1, 0)), lados=28)
for x in (-0.25, 0.2):
    toro(B('olhal', 'ferro', True, K), Vector((x, 0, PH + E + 0.04)), 0.028, 0.008, 20, 8, Matrix.Rotation(PI / 2, 3, 'X'))
    caixa_de(B('olhal_base', 'ferro', False, K), (x - 0.03, -0.015, PH + E), (x + 0.03, 0.015, PH + E + 0.014))
for s in (-1, 1):
    y = s * YP
    for dy in (-0.03, 0.03):
        caixa_de(B('orelha', 'ferro', False, K), (B_PIS.x - 0.028, y + dy - 0.007, B_PIS.z - 0.025), (B_PIS.x + 0.028, y + dy + 0.007, -PH - E))
    cil(B('pino', 'aco', True, K), Vector((B_PIS.x, y, B_PIS.z)), 0.011, 0.08, Vector((0, 1, 0)), lados=12)
# caixa de disparo no topo traseiro e cabos descendo pela face traseira
caixa_de(B('caixa_disparo', 'grafite', False, K), (-0.38, -0.12, PH + E), (-0.22, 0.12, PH + E + 0.06))
caixa_de(B('caixa_disparo_tampa', 'ferro', False, K), (-0.385, -0.125, PH + E + 0.06), (-0.215, 0.125, PH + E + 0.068))
cil(B('led_verde', 'led_verde', False, K), Vector((-0.3, 0.126, PH + E + 0.04)), 0.006, 0.005, Vector((0, 1, 0)), lados=10)
for yb in (-SP / 2, SP / 2):
    pts = catmull([Vector((-0.37, yb, PH + E + 0.03)), Vector((PX0 - 0.025, yb, PH + E + 0.01)), Vector((PX0 - 0.012, yb, PH - 0.03)),
                   Vector((PX0 - 0.012, yb, -PH + 0.02))], 6)
    mangueira(B('cabos_disparo', 'cabo', True, K), pts, 0.006)
for yc, zc in CENTROS:                                                    # conector de ignição ao lado de cada tubo
    yb = -SP / 2 if yc <= 0 else SP / 2
    if abs(yc) < 1e-6:
        yb = -SP / 2
    caixa_de(B('conector', 'latao', False, K), (PX0 - 0.012, yb - 0.006, zc - 0.012), (PX0 - 0.002, yb + 0.006, zc + 0.012))
# fuligem nas faces do casulo (frente e trás) e escorridos
for k in range(18):
    yc, zc = random.choice(CENTROS)
    a = random.uniform(0, 2 * PI)
    for xf, sx in ((PX1 + 0.0008, 1), (PX0 - 0.0008, -1)):
        caixa(B('fuligem', 'chamusco', False, K), Vector((xf, yc + math.cos(a) * 0.055, zc + math.sin(a) * 0.055)), (0.001, random.uniform(0.015, 0.03), random.uniform(0.008, 0.02)))
for k in range(6):
    s = random.choice((-1, 1))
    x = random.uniform(-0.3, 0.3)
    caixa(B('escorridos', 'ferrugem', False, K), Vector((x, s * (PH + E + 0.001), random.uniform(-0.1, 0.05))), (random.uniform(0.006, 0.012), 0.002, random.uniform(0.06, 0.15)))

# ------------------------------------------------------------------ foguete, selo traseiro e meia-casca
def foguete(nome, pai=None, aberto=False, quente=False):
    """Foguete de 0,55 m, origem no bocal, nariz em +x: bocal, aletas, corpo oliva com faixa, ogiva e espoleta."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    if pai is not None:
        e.parent = pai
    bm = bmesh.new()
    torno(bm, [(0.002, 0.0), (0.002, 0.017), (0.0, 0.0215), (0.036, 0.0165), (0.04, 0.0)], 20)
    obj(nome + '_bocal', bm, 'brasa' if quente else 'queimado', e)
    bm = bmesh.new()
    torno(bm, [(0.036, 0.0), (0.036, 0.029), (0.046, RR), (0.40, RR), (0.40, 0.0)], 24)
    suavizar(obj(nome + '_corpo', bm, 'oliva', e))
    bm = bmesh.new()
    torno(bm, [(0.40, RR), (0.43, 0.031), (0.46, 0.028), (0.49, 0.023), (0.515, 0.017), (0.535, 0.01), (0.545, 0.005), (0.545, 0.0)], 24)
    suavizar(obj(nome + '_ogiva', bm, 'ogiva', e))
    bm = bmesh.new()
    torno(bm, [(0.544, 0.0), (0.544, 0.006), (0.553, 0.004), (0.556, 0.0)], 12)
    obj(nome + '_espoleta', bm, 'latao', e)
    bm = bmesh.new()
    torno(bm, [(0.30, RR + 0.0004), (0.33, RR + 0.0004), (0.33, 0.0), (0.30, 0.0)], 24)
    obj(nome + '_faixa', bm, 'faixa_amarela', e)
    bm = bmesh.new()
    torno(bm, [(0.37, RR + 0.0004), (0.38, RR + 0.0004), (0.38, 0.0), (0.37, 0.0)], 24)
    obj(nome + '_anel', bm, 'vermelho', e)
    bm = bmesh.new()
    torno(bm, [(0.046, RR + 0.0006), (0.054, RR + 0.0006), (0.054, 0.0), (0.046, 0.0)], 24)
    obj(nome + '_contato', bm, 'cobre', e)
    bm = bmesh.new()                                                     # aletas (dobradas no tubo, abertas em voo)
    rt = 0.068 if aberto else 0.0405
    for k in range(4):
        a = PI / 4 + k * PI / 2
        Rk = Matrix.Rotation(a, 3, 'X')
        perfil = [(0.05, RR - 0.002), (0.14, RR - 0.002), (0.12, rt), (0.065, rt)]
        vs0 = [bm.verts.new(Rk @ Vector((x, -0.0015, r))) for x, r in perfil]
        vs1 = [bm.verts.new(Rk @ Vector((x, 0.0015, r))) for x, r in perfil]
        bm.faces.new(vs0)
        bm.faces.new(list(reversed(vs1)))
        for i in range(4):
            bm.faces.new((vs0[i], vs1[i], vs1[(i + 1) % 4], vs0[(i + 1) % 4]))
        cil(bm, Rk @ Vector((0.06, 0, RR + 0.002)), 0.004, 0.012, Rk @ Vector((0, 1, 0)), lados=8)   # dobradiça
    obj(nome + '_aletas', bm, 'grafite', e)
    bm = bmesh.new()                                                     # placas de série gastas
    caixa_de(bm, (0.16, -0.012, RR - 0.001), (0.24, 0.012, RR + 0.0008))
    caixa_de(bm, (0.2, RR - 0.001, -0.008), (0.26, RR + 0.0008, 0.008))
    obj(nome + '_serie', bm, 'composito', e)
    return e


def selo(nome, pai=None):
    """Selo traseiro do tubo: disco de compósito, aro de aço e alça; normal em x, origem no centro."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    if pai is not None:
        e.parent = pai
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.044, 0.006, Vector((1, 0, 0)), lados=24)
    obj(nome + '_disco', bm, 'composito', e)
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 0.046, 0.0045, 28, 6, Matrix.Rotation(PI / 2, 3, 'Y'))
    obj(nome + '_aro', bm, 'aco', e)
    bm = bmesh.new()
    caixa_de(bm, (-0.007, -0.006, 0.03), (-0.003, 0.006, 0.05))
    caixa_de(bm, (-0.0035, -0.03, -0.006), (-0.0028, 0.03, 0.006))
    obj(nome + '_alca', bm, 'vermelho', e)
    return e


def meia_casca(nome):
    """Meia-casca guia (invólucro) que se solta na boca: meio cilindro com rebordo e frisos."""
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    bm = bmesh.new()
    n = 12
    an = [k * PI / n for k in range(n + 1)]
    for x0, x1, r0, r1 in ((-0.045, 0.045, 0.033, 0.038), (-0.045, -0.035, 0.038, 0.043)):
        vs = {}
        for i, (x, r) in enumerate(((x0, r0), (x1, r0), (x1, r1), (x0, r1))):
            vs[i] = [bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for a in an]
        for i in range(4):
            A, Bq = vs[i], vs[(i + 1) % 4]
            for k in range(n):
                bm.faces.new((A[k], A[k + 1], Bq[k + 1], Bq[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    obj(nome + '_casca', bm, 'composito', e)
    bm = bmesh.new()
    for x in (-0.01, 0.02):
        toro(bm, Vector((x, 0, 0)), 0.0385, 0.002, 24, 5, Matrix.Rotation(PI / 2, 3, 'Y'))
    for v in list(bm.verts):
        if v.co.z < -0.001:
            v.co.z = -0.001
    obj(nome + '_friso', bm, 'faixa_amarela', e)
    return e


# estoque visto pelo visor do paiol (deitados nas prateleiras, nariz para o norte)
for z in (0.28, 0.43, 0.58):
    f = foguete('foguete_estoque')
    f.location = (0.252, -1.365 + random.uniform(-0.01, 0.01), z)
    f.rotation_euler = (random.uniform(0, 2 * PI), 0, PI / 2)
# foguetes carregados no casulo (os 5 que não disparam são fixos)
estaticos = []
for r in range(3):
    for c in range(3):
        if (r, c) in DISPARO:
            continue
        yc, zc = tubo_yz(r, c)
        f = foguete('foguete_reserva', casulo)
        f.location = (X_TRAS_F, yc, zc)
        s_ = selo('selo_reserva', casulo)
        s_.location = (PX0 - 0.004, yc, zc)

# tampas frontais articuladas (uma por tubo)
tampas = []
for r in range(3):
    for c in range(3):
        yc, zc = tubo_yz(r, c)
        h = bpy.data.objects.new('tampa_dobradica', None)
        sc.collection.objects.link(h)
        h.parent = casulo
        h.location = (PX1 + 0.004, yc, zc + 0.05)
        bm = bmesh.new()
        cil(bm, Vector((0.004, 0, -0.05)), 0.05, 0.007, Vector((1, 0, 0)), lados=24)
        obj('tampa', bm, 'amarelo' if (r + c) % 3 else 'amarelo2', h)
        bm = bmesh.new()
        cil(bm, Vector((0.008, 0, -0.05)), 0.03, 0.003, Vector((1, 0, 0)), lados=20)
        caixa_de(bm, (0.0, -0.02, -0.006), (0.009, 0.02, 0.004))
        obj('tampa_reforco', bm, 'ferro', h)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0)), 0.006, 0.05, Vector((0, 1, 0)), lados=10)
        obj('tampa_pino', bm, 'aco', h)
        caixa_de(B('tampa_dobradica_base', 'ferro', False, K), (PX1, yc - 0.03, zc + 0.044), (PX1 + 0.006, yc + 0.03, zc + 0.056))
        tampas.append(h)

# ------------------------------------------------------------------ pistões de elevação (camisa no giro, haste no casulo)
L_CAM, L_HAS = 0.15, 0.16
pistoes = []
for i, s in enumerate((1, -1)):
    p = bpy.data.objects.new('pistao%d' % i, None)
    sc.collection.objects.link(p)
    p.parent = giro
    p.location = Vector((A_PIS.x, s * YP, A_PIS.z))
    p.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.022, 0.05, Vector((0, 1, 0)), lados=16)
    cil(bm, Vector((0, 0, 0.03 + L_CAM / 2)), 0.03, L_CAM, lados=24)
    cil(bm, Vector((0, 0, 0.03 + L_CAM)), 0.036, 0.02, lados=24)
    cil(bm, Vector((0, 0, 0.04)), 0.036, 0.02, lados=24)
    suavizar(obj('pistao%d_camisa' % i, bm, 'amarelo', p))
    bm = bmesh.new()
    for z in (0.045, 0.03 + L_CAM - 0.005):
        cil(bm, Vector((-0.034, 0, z)), 0.008, 0.016, Vector((1, 0, 0)), lados=10)
    mangueira(bm, bezier(Vector((-0.04, 0, 0.045)), Vector((-0.08, 0, 0.07)), Vector((-0.08, 0, 0.14)), Vector((-0.04, 0, 0.03 + L_CAM - 0.005)), 10), 0.006)
    suavizar(obj('pistao%d_mangueira' % i, bm, 'borracha', p))
    h = bpy.data.objects.new('pistao%d_haste_eixo' % i, None)
    sc.collection.objects.link(h)
    h.parent = p
    bm = bmesh.new()
    cil(bm, Vector((0, 0, L_HAS / 2)), 0.014, L_HAS, lados=20)
    cil(bm, Vector((0, 0, L_HAS)), 0.02, 0.045, Vector((0, 1, 0)), lados=16)
    suavizar(obj('pistao%d_haste' % i, bm, 'cromo', h))
    bm = bmesh.new()
    caixa_de(bm, (0.0135, -0.003, 0.02), (0.0145, 0.003, 0.08))
    obj('pistao%d_oleo' % i, bm, 'oleo', h)
    pistoes.append((p, h, s))

# ------------------------------------------------------------------ braço carregador
carro = bpy.data.objects.new('braco', None)
sc.collection.objects.link(carro)
C_ = 'carro'
caixa_de(B('carro', 'amarelo', False, C_), (-0.09, AY - 0.075, ZD + 0.03), (0.09, AY + 0.075, ZD + 0.12))
for sx in (-1, 1):
    for y in (AY - 0.045, AY + 0.045):
        caixa_de(B('carro_patim', 'ferro', False, C_), (sx * 0.07 - 0.02, y - 0.02, ZD + 0.02), (sx * 0.07 + 0.02, y + 0.02, ZD + 0.04))
cil(B('carro_motor', 'grafite', True, C_), Vector((0.11, AY, ZD + 0.08)), 0.032, 0.06, Vector((0, 0, 1)), lados=18)
caixa_de(B('carro_listras', 'listras', False, C_), (-0.09, AY - 0.076, ZD + 0.09), (0.09, AY - 0.075, ZD + 0.115))
for sx in (-1, 1):
    for sy in (-1, 1):
        parafuso((sx * 0.075, AY + sy * 0.06, ZD + 0.126), (0, 0, 1), C_, 0.008)
# coluna e forquilha do ombro
caixa_de(B('coluna', 'grafite', False, C_), (-0.045, AY - 0.045, ZD + 0.12), (0.045, AY + 0.045, SZ - 0.06))
for sx in (-1, 1):
    caixa_de(B('forquilha', 'amarelo', False, C_), (sx * 0.0495 - 0.0045, AY - 0.05, SZ - 0.09), (sx * 0.0495 + 0.0045, AY + 0.05, SZ + 0.035))
    caixa_de(B('forquilha_base', 'ferro', False, C_), (sx * 0.0495 - 0.012, AY - 0.055, SZ - 0.1), (sx * 0.0495 + 0.012, AY + 0.055, SZ - 0.075))
cil(B('ombro_motor', 'grafite', True, C_), Vector((-0.085, AY, SZ)), 0.045, 0.06, Vector((1, 0, 0)), lados=24)
cil(B('ombro_motor_tampa', 'ferro', True, C_), Vector((-0.12, AY, SZ)), 0.035, 0.012, Vector((1, 0, 0)), lados=20)
cil(B('ombro_eixo', 'aco', True, C_), Vector((0.06, AY, SZ)), 0.018, 0.03, Vector((1, 0, 0)), lados=12)
A_CIL = Vector((0.08, AY - 0.06, ZD + 0.17))                              # pino da camisa do cilindro da lança
for dx in (-0.025, 0.025):
    caixa_de(B('cil_orelha', 'ferro', False, C_), (A_CIL.x + dx - 0.005, A_CIL.y - 0.025, ZD + 0.12), (A_CIL.x + dx + 0.005, A_CIL.y + 0.025, A_CIL.z + 0.025))
cil(B('pino', 'aco', True, C_), A_CIL, 0.01, 0.05, Vector((1, 0, 0)), lados=10)
pts = catmull([Vector((0.0, AY + 0.1, ZD + 0.04)), Vector((0.0, AY + 0.08, ZD + 0.08)), Vector((-0.045, AY + 0.02, ZD + 0.2)), Vector((-0.06, AY, SZ - 0.04))], 6)
feixe(B('cabos', 'cabo', True, C_), B('abracadeiras', 'aco', True, C_), pts, Vector((1, 0, 0)), n=2, r=0.008, passo=6)

lanca = bpy.data.objects.new('braco_lanca', None)
sc.collection.objects.link(lanca)
lanca.parent = carro
lanca.location = (0, AY, SZ)
caixa_de(B('lanca', 'amarelo', False, 'lanca'), (-0.035, -0.04, -0.04), (0.035, 0.04, L_EXT))
cil(B('lanca_cubo', 'ferro', True, 'lanca'), Vector((0, 0, 0)), 0.05, 0.08, Vector((1, 0, 0)), lados=24)
caixa_de(B('lanca_boca', 'ferro', False, 'lanca'), (-0.04, -0.045, L_EXT - 0.03), (0.04, 0.045, L_EXT))
caixa_de(B('lanca_listras', 'listras', False, 'lanca'), (-0.036, 0.04, 0.2), (0.036, 0.041, 0.26))
B_CIL = 0.15
caixa_de(B('lanca_orelha', 'ferro', False, 'lanca'), (0.035, -0.07, B_CIL - 0.03), (0.11, -0.03, B_CIL - 0.02))
for dx in (0.052, 0.108):
    caixa_de(B('lanca_orelha', 'ferro', False, 'lanca'), (dx - 0.005, -0.075, B_CIL - 0.03), (dx + 0.005, -0.03, B_CIL + 0.025))
cil(B('pino', 'aco', True, 'lanca'), Vector((0.08, -0.06, B_CIL)), 0.009, 0.07, Vector((1, 0, 0)), lados=10)
for z in (0.06, 0.16, 0.26):
    parafuso((0.036, 0.0, z), (1, 0, 0), 'lanca', 0.008)
    parafuso((-0.036, 0.0, z), (-1, 0, 0), 'lanca', 0.008)
caixa(B('lanca_remendo', 'casco', False, 'lanca'), Vector((-0.0365, 0.0, 0.12)), (0.002, 0.05, 0.07))
interna = bpy.data.objects.new('braco_interna', None)
sc.collection.objects.link(interna)
interna.parent = lanca
caixa_de(B('interna', 'casco', False, 'interna'), (-0.026, -0.03, 0.0), (0.026, 0.03, L_INT))
caixa_de(B('interna_marcas', 'chamusco', False, 'interna'), (-0.0265, -0.02, 0.05), (0.0265, 0.02, 0.052))
cil(B('interna_ponta', 'ferro', True, 'interna'), Vector((0, 0, L_INT)), 0.04, 0.07, Vector((1, 0, 0)), lados=20)
caixa(B('interna_oleo', 'oleo', False, 'interna'), Vector((0.0265, 0.0, 0.1)), (0.001, 0.006, 0.1))
pulso = bpy.data.objects.new('braco_pulso', None)
sc.collection.objects.link(pulso)
pulso.parent = interna
pulso.location = (0, 0, L_INT)
P_ = 'pulso'
cil(B('pulso_motor', 'grafite', True, P_), Vector((-0.06, 0, 0)), 0.036, 0.05, Vector((1, 0, 0)), lados=20)
caixa_de(B('pulso_bloco', 'ferro', False, P_), (-0.03, -0.04, -0.07), (0.03, 0.04, -0.03))
caixa_de(B('garra_viga', 'amarelo', False, P_), (-0.025, -0.30, -0.07), (0.025, 0.30, -0.035))
caixa_de(B('garra_listras', 'listras', False, P_), (-0.026, 0.24, -0.07), (0.026, 0.30, -0.035))
for y in (-0.16, 0.16):
    caixa_de(B('garra_mancal', 'ferro', False, P_), (-0.055, y - 0.025, -0.08), (0.055, y + 0.025, -0.06))
caixa_de(B('soquete_suporte', 'ferro', False, P_), (-0.02, -0.375, -0.12), (0.02, -0.34, -0.035))
cil(B('soquete_cilindro', 'amarelo2', True, P_), Vector((0, -0.385, -0.10)), 0.024, 0.05, Vector((0, 1, 0)), lados=18)
cil(B('led_ambar', 'led_ambar', False, P_), Vector((0.026, 0.0, -0.05)), 0.006, 0.005, Vector((1, 0, 0)), lados=10)
mandibulas = []
for sx in (-1, 1):
    for y in (-0.16, 0.16):
        m = bpy.data.objects.new('mandibula', None)
        sc.collection.objects.link(m)
        m.parent = pulso
        m.location = (0, y, -0.07)
        bm = bmesh.new()
        caixa_de(bm, (sx * 0.042 - 0.006, -0.02, -0.075), (sx * 0.042 + 0.006, 0.02, 0.0))
        caixa_de(bm, (sx * 0.042 - 0.006 if sx > 0 else sx * 0.042 - 0.006, -0.02, -0.085), (sx * 0.042 + 0.006, 0.02, -0.075))
        obj('mandibula_chapa', bm, 'ferro', m)
        bm = bmesh.new()
        caixa_de(bm, (sx * 0.036 - 0.003, -0.015, -0.055), (sx * 0.036 + 0.003, 0.015, -0.01))
        obj('mandibula_patim', bm, 'borracha', m)
        mandibulas.append((m, sx))
soquete = []
for k in range(3):
    o = bpy.data.objects.new('soquete%d' % k, None)
    sc.collection.objects.link(o)
    o.parent = pulso
    bm = bmesh.new()
    cil(bm, Vector((0, 0.03, 0)), 0.016 - k * 0.003, 0.06 if k < 2 else 0.04, Vector((0, 1, 0)), lados=14)
    if k == 2:
        cil(bm, Vector((0, 0.055, 0)), 0.026, 0.012, Vector((0, 1, 0)), lados=18)
    obj('soquete%d_tubo' % k, bm, 'cromo' if k < 2 else 'ferro', o)
    soquete.append(o)
pts = [Vector((0.03, -0.02, 0.02)), Vector((0.05, -0.04, -0.03)), Vector((0.03, -0.2, -0.05)), Vector((0.0, -0.3, -0.1))]
mangueira(B('pulso_mangueira', 'borracha', True, P_), catmull(pts, 5), 0.006)
# cilindro da lança (camisa no carro, haste na orelha da lança)
cil_l = bpy.data.objects.new('braco_cilindro', None)
sc.collection.objects.link(cil_l)
cil_l.parent = carro
cil_l.location = A_CIL
cil_l.rotation_mode = 'QUATERNION'
cil_h = bpy.data.objects.new('braco_cilindro_haste', None)
sc.collection.objects.link(cil_h)
cil_h.parent = cil_l

# pinos do elevador (apresentam o foguete) e abas da escotilha
pinos = bpy.data.objects.new('paiol_pinos', None)
sc.collection.objects.link(pinos)
bm = bmesh.new()
for y in (-0.2, 0.2):
    cil(bm, Vector((0, y, -0.14)), 0.01, 0.2, lados=10)
    caixa_de(bm, (-0.02, y - 0.012, -0.045), (0.02, y + 0.012, -0.033))
obj('paiol_pinos_aco', bm, 'aco', pinos)
abas = []
for sx in (-1, 1):
    h = bpy.data.objects.new('paiol_aba', None)
    sc.collection.objects.link(h)
    h.location = (sx * 0.065, (PY0 + PY1) / 2, PZ1)
    bm = bmesh.new()
    caixa_de(bm, (-sx * 0.066 if sx > 0 else 0.0, -0.26, 0.0), (0.0 if sx > 0 else 0.066, 0.26, 0.012))
    obj('paiol_aba_chapa', bm, 'amarelo', h)
    bm = bmesh.new()
    caixa_de(bm, (-sx * 0.05 if sx > 0 else 0.016, -0.2, 0.012), (-0.016 if sx > 0 else 0.05, 0.2, 0.014))
    obj('paiol_aba_listras', bm, 'listras', h)
    abas.append((h, sx))

# ------------------------------------------------------------------ objetos estáticos
PAIS = {'base': None, 'giro': giro, 'casulo': casulo, 'carro': carro, 'lanca': lanca, 'interna': interna, 'pulso': pulso}
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(nome if g == 'base' else g + '_' + nome, bm, mat, PAIS[g])
    if liso:
        suavizar(o)
BMS.clear()
# cilindro da lança (malhas no próprio objeto)
L_CC, L_CH = 0.20, 0.24


def malha_cilindro():
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.018, 0.04, Vector((1, 0, 0)), lados=14)
    cil(bm, Vector((0, 0, 0.025 + L_CC / 2)), 0.022, L_CC, lados=20)
    cil(bm, Vector((0, 0, 0.025 + L_CC)), 0.026, 0.014, lados=20)
    suavizar(obj('braco_cilindro_camisa', bm, 'amarelo2', cil_l))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, L_CH / 2)), 0.01, L_CH, lados=16)
    cil(bm, Vector((0, 0, L_CH)), 0.015, 0.03, Vector((1, 0, 0)), lados=14)
    suavizar(obj('braco_cilindro_haste_m', bm, 'cromo', cil_h))


malha_cilindro()


# ------------------------------------------------------------------ cinemática do giro e do casulo
def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def tiro_info(q):
    ult = None
    for i, s in enumerate(TF):
        if q >= s:
            ult = i
    return (ult, q - TF[ult]) if ult is not None else (None, None)


def pose(q):
    """(yaw, pitch): sai da posição de carga, mira, salva, volta e espera a recarga."""
    if q <= 20:
        t = suave((q - 1) / 19)
        return YAW_C + (YAW_F - YAW_C) * t, PITCH_F * t
    if q <= 38:
        i, dt = tiro_info(q)
        kick = 0.0 if i is None else math.radians(1.1) * math.exp(-dt / 1.5) * (1 if dt > 0 else 0.3)
        return YAW_F + math.radians(0.4) * math.sin(q * 1.3) * (1 if i is not None else 0), PITCH_F + kick
    if q <= 48:
        t = suave((q - 38) / 10)
        return YAW_F + (YAW_C - YAW_F) * t, PITCH_F * (1 - t)
    return YAW_C, 0.0


def M_casulo(yaw, pitch):
    return Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation((0, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y')


def abertura_tampas(q):
    if q < 6 or q > 47:
        return 0.0
    if q <= 16:
        return suave((q - 6) / 10)
    if q <= 39:
        return 1.0
    return 1 - suave((q - 39) / 8)


# ------------------------------------------------------------------ cinemática do braço (lança telescópica)
def ik_lanca(w):
    """Pulso em (y, z) do mundo → (ângulo da lança no plano yz, comprimento)."""
    dy, dz = w[0] - AY, w[1] - SZ
    return math.atan2(dz, dy), math.hypot(dy, dz)


def alvo_tubo(k):
    r, c = DISPARO[k]
    yc, zc = tubo_yz(r, c)
    return -yc, TZ + zc                     # x do carro, z do centro do foguete (posição de carga)


def braco(q):
    """Estado do braço no quadro: (x do carro, pulso (y, z), mandíbulas fechadas 0..1, soquete 0..1, índice, fase)."""
    REP = (PICK.y, PICK.z + WZ + 0.05)
    PEG = (PICK.y, PICK.z + WZ)
    for k, R in enumerate(RC):
        if R <= q < R + 12:
            xt, zt = alvo_tubo(k)
            CARGA = (GY_C, zt + WZ)
            e = q - R
            if e < 2:
                t = suave(e / 2)
                return 0.0, (REP[0], REP[1] + (PEG[1] - REP[1]) * t), suave((e - 1.0) / 1.0), 0.0, k, 'pega'
            if e < 6:
                t = suave((e - 2) / 4)
                y = PEG[0] + (CARGA[0] - PEG[0]) * t
                z = PEG[1] + (CARGA[1] - PEG[1]) * t + 0.08 * math.sin(PI * t)
                return xt * t, (y, z), 1.0, 0.0, k, 'leva'
            if e < 9:
                t = suave((e - 6) / 3)
                return xt, CARGA, 0.0, t, k, 'soca'
            if e < 10:
                return xt, CARGA, 0.0, 1 - (e - 9), k, 'recolhe'
            t = suave((e - 10) / 2)
            return xt * (1 - t), (CARGA[0] + (REP[0] - CARGA[0]) * t, CARGA[1] + (REP[1] - CARGA[1]) * t), 0.0, 0.0, k, 'volta'
    return 0.0, REP, 0.0, 0.0, None, 'espera'


SOCA = 0.64                                                                 # curso do soquete (foguete entra no tubo)
lens = []
for q in range(1, QUADROS + 1):
    x_, w, *_ = braco(q)
    phi, L = ik_lanca(w)
    lens.append(L)
print('LANÇA comprimento min/max', round(min(lens), 3), round(max(lens), 3), 'limite', L_EXT - 0.05 + L_INT, L_INT + 0.02)


def foguete_carga_pos(k, q):
    """Centro do foguete de recarga k no quadro q (ou None se ainda escondido)."""
    R = RC[k]
    xt, zt = alvo_tubo(k)
    if q < R - 4:
        return None
    if q < R:
        return Vector((0, PICK.y, PICK.z - 0.2 * (1 - suave((q - (R - 4)) / 4))))
    if q < R + 2:
        return PICK.copy()
    if q < R + 9:
        x_, w, fech, soc, kk, fase = braco(q)
        return Vector((x_, w[0] + SOCA * soc, w[1] - WZ))
    return Vector((xt, GY_C + SOCA, zt))


# ------------------------------------------------------------------ voo dos foguetes
def boca_mundo(k, yaw, pitch):
    r, c = DISPARO[k]
    yc, zc = tubo_yz(r, c)
    return M_casulo(yaw, pitch) @ Vector((PX1 + 0.02, yc, zc))


def traseira_mundo(k, yaw, pitch):
    r, c = DISPARO[k]
    yc, zc = tubo_yz(r, c)
    return M_casulo(yaw, pitch) @ Vector((PX0 - 0.02, yc, zc))


CAMINHOS = []
for k in range(4):
    yaw, pitch = pose(TF[k])
    P0 = boca_mundo(k, yaw, pitch)
    d = M_casulo(yaw, pitch).to_3x3() @ Vector((1, 0, 0))
    T = ALVOS[k]
    hb = Vector((P0.x - T.x, P0.y - T.y, 0)).normalized()
    lat = Vector((-hb.y, hb.x, 0)) * (k - 1.5) * 0.9
    CAMINHOS.append((P0, P0 + d * (6.2 + 0.7 * k), T + hb * 5.0 + lat + Vector((0, 0, 5.5 + (k - 1.5) * 1.1)), T))


def bez(k, s):
    p0, p1, p2, p3 = CAMINHOS[k]
    return p0 * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + p3 * s ** 3


def bez_d(k, s):
    p0, p1, p2, p3 = CAMINHOS[k]
    return (p1 - p0) * 3 * (1 - s) ** 2 + (p2 - p1) * 6 * s * (1 - s) + (p3 - p2) * 3 * s * s


def s_voo(dt):
    return min(1.0, (dt / FL) ** 1.35)


# ------------------------------------------------------------------ física simples das sobras
def chao_h(x, y):
    r = math.hypot(x, y)
    a = math.atan2(y, x) % (2 * PI)
    if max(abs(x), abs(y)) > 1.48:
        return 0.0
    if max(abs(x * math.cos(k * PI / 4) + y * math.sin(k * PI / 4)) for k in range(4)) < AP + 0.02:
        return ZD
    if A0 <= a <= A1 and RD0 <= r <= RD1:
        return ZDF0 + (r - RD0) / (RD1 - RD0) * (ZDF1 - ZDF0) + 0.02
    if -0.3 < x < 0.3 and PY0 < y < PY1:
        return PZ1
    if 0.82 < x < 1.42 and -0.44 < y < 0.44:
        return 0.16
    return Z0


def simula(p, v, eul, w, h_rest, deitar, semente):
    """Gravidade, giro no ar, até dois quiques com perda, desliza com atrito e deita. Devolve [(pos, euler)] por
    quadro desde o lançamento e o quadro em que parou."""
    rnd = random.Random(semente)
    p, v, eul, w = p.copy(), v.copy(), list(eul), Vector(w)
    passo = 1 / 240
    no_chao, quiques, parou = False, 0, None
    quadros, t = [], 0.0
    for e in range(QUADROS + 1):
        while t < e / FPS - 1e-9:
            t += passo
            h = chao_h(p.x, p.y)
            if not no_chao:
                v.z -= 9.81 * passo
                p += v * passo
                for i in range(3):
                    eul[i] += w[i] * passo
                h = chao_h(p.x, p.y)
                if p.z - h_rest <= h:
                    p.z = h + h_rest
                    if v.z < -0.7 and quiques < 2:
                        v.z = -v.z * 0.3
                        v.x *= 0.55
                        v.y *= 0.55
                        w *= 0.5
                        w.z += rnd.uniform(-4, 4)
                        quiques += 1
                    else:
                        v.z = 0.0
                        no_chao = True
            else:
                p.z = h + h_rest
                vh = Vector((v.x, v.y, 0))
                s = vh.length
                if s > 0:
                    vh *= max(0.0, s - 2.5 * passo) / s
                v = Vector((vh.x, vh.y, 0))
                p += v * passo
                alvo = deitar(eul)
                for i in range(2):
                    eul[i] += (alvo[i] - eul[i]) * min(1.0, 16 * passo)
                w.z *= math.exp(-6 * passo)
                eul[2] += w.z * passo
                if v.length < 0.01 and parou is None:
                    parou = e
        quadros.append((p.copy(), tuple(eul)))
    return quadros, parou if parou is not None else QUADROS


def deitar_selo(eul):
    """Disco com normal em x: deita com o eixo x na vertical."""
    return (round(eul[0] / PI) * PI, (PI / 2 if math.sin(eul[1]) >= 0 else -PI / 2), eul[2])


def deitar_casca(eul):
    return (round(eul[0] / PI) * PI, 0.0, eul[2])


# ------------------------------------------------------------------ partículas e objetos animados
def volume(nome, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    o = obj(nome, bm, mat)
    o.rotation_mode = 'QUATERNION'
    return o


def bolinha(nome, mat, r, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    return obj(nome, bm, mat)


def chave(o, q, *canais):
    for c in canais:
        o.keyframe_insert(c, frame=q)


def mostrar(o, vis, q, filhos=True):
    for ob in [o] + (list(o.children_recursive) if filhos else []):
        ob.hide_render = ob.hide_viewport = not vis
        ob.keyframe_insert('hide_render', frame=q)
        ob.keyframe_insert('hide_viewport', frame=q)


f_tubo, f_voo, f_carga, s_tubo, s_carga = [], [], [], [], []
for k, (r, c) in enumerate(DISPARO):
    yc, zc = tubo_yz(r, c)
    f = foguete('foguete_tubo%d' % k, casulo)
    f.location = (X_TRAS_F, yc, zc)
    f_tubo.append(f)
    s_ = selo('selo_tubo%d' % k, casulo)
    s_.location = (PX0 - 0.004, yc, zc)
    s_tubo.append(s_)
    fv = foguete('foguete_voo%d' % k, None, aberto=True, quente=True)
    fv.rotation_mode = 'QUATERNION'
    f_voo.append(fv)
    fc = foguete('foguete_carga%d' % k)
    fc.rotation_euler = (0, 0, PI / 2)
    f_carga.append(fc)
    sc_ = selo('selo_carga%d' % k, fc)
    sc_.location = ((PX0 - 0.004) - X_TRAS_F, 0, 0)
    s_carga.append(sc_)
# chama do foguete em voo (filhos do foguete; o bocal fica em x = 0, a chama sai para −x)
chamas = []
for k, fv in enumerate(f_voo):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0, radius2=0.017, depth=0.22,
                          matrix=Matrix.Translation((-0.11, 0, 0)) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
    obj('chama_nucleo', bm, 'nucleo_chama', fv)
    fo = volume('chama_fogo', 'fogo')
    fo.parent = fv
    fo.location = (-0.2, 0, 0)
    fo.scale = (0.22, 0.05, 0.05)
    fo.color = (1, 0, 0, 1)
    lz = bpy.data.lights.new('Chama%d' % k, 'POINT')
    lz.color = (1.0, 0.5, 0.15)
    lz.energy = 450
    lz.shadow_soft_size = 0.05
    lo = bpy.data.objects.new('Chama%d' % k, lz)
    sc.collection.objects.link(lo)
    lo.parent = fv
    lo.location = (-0.15, 0, 0)
    chamas.append(fo)
# jato traseiro no disparo: fogo, núcleo e luz
jatos = []
for k in range(4):
    fo = volume('jato_fogo', 'fogo')
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.03, radius2=0.0, depth=0.28,
                          matrix=Matrix.Translation((0, 0, 0.14)))
    nu = obj('jato_nucleo', bm, 'nucleo_chama')
    nu.rotation_mode = 'QUATERNION'
    lz = bpy.data.lights.new('Jato%d' % k, 'POINT')
    lz.color = (1.0, 0.5, 0.15)
    lz.shadow_soft_size = 0.15
    lo = bpy.data.objects.new('Jato%d' % k, lz)
    sc.collection.objects.link(lo)
    jatos.append((fo, nu, lz, lo))
N_JF = 7
fumaca_jato = [[volume('fumaca_jato', 'fumaca') for _ in range(N_JF)] for k in range(4)]
rnd_j = [[(random.uniform(-0.45, 0.45), random.uniform(-0.15, 0.2), random.uniform(0.8, 1.25), random.uniform(0, 6)) for _ in range(N_JF)] for k in range(4)]
N_RS = 34
rastros = [[volume('rastro', 'rastro') for _ in range(N_RS)] for k in range(4)]
N_RES = 3
residuais = [[volume('fumaca_residual', 'fiapo') for _ in range(N_RES)] for k in range(4)]
# explosões
N_POE, N_EST, N_FA = 14, 16, 14
explosoes = []
for k in range(4):
    T = ALVOS[k]
    cl = volume('explosao_clarao', 'clarao_v')
    fb = volume('explosao_fogo', 'fogo_exp')
    fa = [(bolinha('explosao_faisca', 'faisca', 0.025, 0), Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)).normalized() * random.uniform(4, 11)
           + Vector((0, 0, random.uniform(3, 10)))) for _ in range(N_FA)]
    fms = [volume('explosao_fumaca', 'fumaca') for _ in range(3)]
    poe = [volume('explosao_poeira', 'poeira') for _ in range(N_POE)]
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 1.0, 0.035, 72, 8)
    on = obj('explosao_onda', bm, 'onda')
    est = []
    for j in range(N_EST):
        bm = bmesh.new()
        pedra(bm, Vector((0, 0, 0)), random.uniform(0.04, 0.1))
        est.append((obj('estilhaco', bm, 'terra_queimada' if j % 3 else 'casco'),
                    Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)).normalized() * random.uniform(2.5, 7.0) + Vector((0, 0, random.uniform(4, 9))),
                    Vector((random.uniform(-9, 9), random.uniform(-9, 9), random.uniform(-9, 9)))))
    lz = bpy.data.lights.new('Explosão%d' % k, 'POINT')
    lz.color = (1.0, 0.55, 0.2)
    lz.shadow_soft_size = 0.8
    lo = bpy.data.objects.new('Explosão%d' % k, lz)
    sc.collection.objects.link(lo)
    lo.location = T + Vector((0, 0, 1.0))
    explosoes.append((cl, fb, fms, poe, on, est, lz, fa))
# sobras ejetadas: selo traseiro (para trás) e duas meias-cascas (na boca)
sobras = []          # (obj, anterior, trajetória, parou, quadro de saída)
for k in range(4):
    yaw, pitch = pose(TF[k])
    Mc = M_casulo(yaw, pitch)
    rnd = random.Random(300 + k)
    b = Mc.to_3x3() @ Vector((-1, 0, 0))
    lado = Mc.to_3x3() @ Vector((0, 1, 0))
    p0 = traseira_mundo(k, yaw, pitch) + b * 0.01
    v0 = b * rnd.uniform(3.2, 4.0) + lado * rnd.uniform(-0.8, 0.8) + Vector((0, 0, rnd.uniform(0.6, 1.2)))
    e0 = (Mc.to_3x3()).to_euler('XYZ')
    tr, parou = simula(p0, v0, e0, Vector((rnd.uniform(-20, 20), rnd.uniform(-25, 25), rnd.uniform(-10, 10))), 0.005, deitar_selo, 400 + k)
    sobras.append((selo('selo_ejetado%d' % k), selo('selo_anterior%d' % k), tr, parou, TF[k]))
    print('SELO', k, 'parou em', TF[k] + parou, tuple(round(c, 2) for c in tr[parou][0]))
    for j, sg in enumerate((-1, 1)):
        yaw1, pitch1 = pose(TF[k] + 1)
        M1 = M_casulo(yaw1, pitch1)
        d = M1.to_3x3() @ Vector((1, 0, 0))
        lado = M1.to_3x3() @ Vector((0, 1, 0))
        p0 = boca_mundo(k, yaw1, pitch1) + d * 0.2
        v0 = d * rnd.uniform(4.5, 6.0) + lado * sg * rnd.uniform(1.4, 2.2) + Vector((0, 0, rnd.uniform(0.3, 1.0)))
        e0 = (M1.to_3x3() @ Matrix.Rotation(PI / 2 * (1 - sg), 3, 'X')).to_euler('XYZ')
        tr, parou = simula(p0, v0, e0, Vector((rnd.uniform(-25, 25), rnd.uniform(-15, 15), rnd.uniform(-12, 12))), 0.012, deitar_casca, 500 + k * 2 + j)
        sobras.append((meia_casca('casca_ejetada%d' % k), meia_casca('casca_anterior%d' % k), tr, parou, TF[k] + 1))
        print('CASCA', k, j, 'parou em', TF[k] + 1 + parou, tuple(round(c, 2) for c in tr[parou][0]))
for o, ant, tr, parou, q0 in sobras:
    ant.location, ant.rotation_euler = tr[parou][0], tr[parou][1]

# luzes fixas de cena e sol
luz_p = bpy.data.lights.new('Luz do paiol', 'POINT')
luz_p.color = AMBAR
luz_p.energy = 1.5
luz_p.shadow_soft_size = 0.02
lp = bpy.data.objects.new('Luz do paiol', luz_p)
sc.collection.objects.link(lp)
lp.location = (0.26, -1.09, 0.66)

# ------------------------------------------------------------------ sujeira estática: sobras de salvas anteriores, queimado, crateras
def livre(x, y):
    if max(abs(x), abs(y)) > 1.42:
        return False
    if max(abs(x * math.cos(k * PI / 4) + y * math.sin(k * PI / 4)) for k in range(4)) < AP + 0.08:
        return False
    for d, R, t, P in JACKS:
        q = Vector((x, y, 0))
        if (q - Vector((P.x, P.y, 0))).length < 0.2:
            return False
        along = q.dot(d)
        if 0.6 < along < 1.6 and abs(q.dot(t)) < 0.14:
            return False
    a = math.atan2(y, x) % (2 * PI)
    if A0 - 0.05 <= a <= A1 + 0.05 and RD0 - 0.04 <= math.hypot(x, y) <= RD1 + 0.06:
        return False
    if -0.35 < x < 0.35 and y < PY1 + 0.04:
        return False
    if 0.78 < x < 1.45 and -0.48 < y < 0.48:
        return False
    if -0.35 < x < 0.35 and y > 0.82:
        return False
    return True


bmq = B('queimado_laje', 'fuligem_chao')
for k in range(40):                                                         # leque de queimado do jato (oeste)
    a = random.uniform(A0 - 0.3, A1 + 0.35)
    r = random.uniform(0.75, 1.42)
    x, y = math.cos(a) * r, math.sin(a) * r
    if livre(x, y) or (A0 <= (a % (2 * PI)) <= A1 and RD0 > r):
        mancha(bmq, (x, y), random.uniform(0.05, 0.13), Z0 + 0.0009 + 0.0001 * (k % 3))
for k in range(16):
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.8, 1.42)
    x, y = math.cos(a) * r, math.sin(a) * r
    if livre(x, y):
        mancha(B('po', 'po'), (x, y), random.uniform(0.05, 0.12), Z0 + 0.0007)
for k in range(30):                                                         # queimado no defletor
    a = random.uniform(A0 + 0.05, A1 - 0.05)
    r = random.uniform(RD0 + 0.03, RD1 - 0.03)
    z = ZDF0 + (r - RD0) / (RD1 - RD0) * (ZDF1 - ZDF0) + 0.0275
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('defletor_fuligem', 'chamusco'), d * r + Vector((0, 0, z)), (random.uniform(0.03, 0.08), random.uniform(0.04, 0.1), 0.001),
          rot_face(d) @ Matrix.Rotation(INCL, 3, 'X'))
for k in (3, 4, 5):                                                          # fuligem nas faces oeste da plataforma
    n, R = FACES[k]
    for j in range(5):
        caixa(B('plataforma_fuligem', 'chamusco'), n * (AP + 0.024) + R @ Vector((random.uniform(-0.22, 0.22), 0, 0)) + Vector((0, 0, random.uniform(0.18, 0.33))),
              (random.uniform(0.04, 0.12), 0.002, random.uniform(0.02, 0.06)), R)
n_s = 0
while n_s < 12:                                                             # selos e cascas de salvas anteriores
    a = random.uniform(A0 - 0.5, A1 + 0.6)
    r = random.uniform(0.8, 1.42)
    x, y = math.cos(a) * r, math.sin(a) * r
    if not livre(x, y):
        continue
    o = selo('selo_chao', None) if n_s % 3 else meia_casca('casca_chao')
    o.location = (x, y, Z0 + (0.005 if n_s % 3 else 0.012))
    o.rotation_euler = (0, PI / 2, random.uniform(0, 2 * PI)) if n_s % 3 else (0, 0, random.uniform(0, 2 * PI))
    n_s += 1
for k in range(14):                                                          # meias-cascas no chão à frente
    rr = random.uniform(2.5, 5.0)
    a = YAW_F + random.uniform(-0.6, 0.6)
    o = meia_casca('casca_chao')
    o.location = (math.cos(a) * rr, math.sin(a) * rr, 0.012)
    o.rotation_euler = (PI * (k % 2), 0, random.uniform(0, 2 * PI))
for k, T in enumerate(ALVOS):                                                # crateras de salvas anteriores
    bmc = B('cratera', 'fuligem_chao')
    for j in range(3):
        mancha(bmc, (T.x + random.uniform(-0.4, 0.4), T.y + random.uniform(-0.4, 0.4)), random.uniform(0.9, 1.5), 0.002 + 0.0005 * j)
    mancha(B('cratera_centro', 'chamusco'), (T.x, T.y), 0.6, 0.004)
    for j in range(18):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.6, 2.2)
        pedra(B('cratera_terra', 'terra_queimada'), (T.x + math.cos(a) * r, T.y + math.sin(a) * r, 0.0), random.uniform(0.05, 0.14), 0.5)
for (nome, mat, liso, g), bm in BMS.items():
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj(nome, bm, mat)
    if liso:
        suavizar(o)
BMS.clear()


# ------------------------------------------------------------------ animação (laço de 4 s)
def por_direcao(o, pos, d, esc, cor, q):
    o.location = pos
    o.rotation_quaternion = Vector(d).normalized().to_track_quat('X', 'Z')
    o.scale = esc
    o.color = cor
    chave(o, q, 'location', 'rotation_quaternion', 'scale', 'color')


def esconder_vol(o, q, pos=(0, 0, -3)):
    o.location = pos
    o.scale = (0.05, 0.05, 0.05)
    o.color = (0, 0, 0, 1)
    o.hide_render = o.hide_viewport = True
    chave(o, q, 'location', 'scale', 'color', 'hide_render', 'hide_viewport')


def ver_vol(o, q):
    o.hide_render = o.hide_viewport = False
    chave(o, q, 'hide_render', 'hide_viewport')


brasa = base3d.M['brasa'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
brasa.default_value = 25.0
VENTO = Vector((0.35, 0.5, 0))
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    yaw, pitch = pose(q)
    giro.rotation_euler = (0, 0, yaw)
    chave(giro, q, 'rotation_euler')
    casulo.rotation_euler = (0, -pitch, 0)
    chave(casulo, q, 'rotation_euler')
    pinhao.rotation_euler = (0, 0, -yaw * R_COROA / R_PINHAO)
    chave(pinhao, q, 'rotation_euler')
    radar.rotation_euler = (0, 0, 2 * PI * 4 * fr)
    chave(radar, q, 'rotation_euler')
    Mp = Matrix.Translation((0, 0, TZ)) @ Matrix.Rotation(-pitch, 4, 'Y')
    for p, h, s in pistoes:
        A = Vector((A_PIS.x, s * YP, A_PIS.z))
        Bp = Mp @ Vector((B_PIS.x, s * YP, B_PIS.z))
        d = Bp - A
        p.rotation_quaternion = d.to_track_quat('Z', 'Y')
        h.location = (0, 0, d.length - L_HAS)
        chave(p, q, 'rotation_quaternion')
        chave(h, q, 'location')
    ab = abertura_tampas(q)
    for h in tampas:
        h.rotation_euler = (0, -math.radians(100) * ab, 0)
        chave(h, q, 'rotation_euler')
    # abas da escotilha do paiol
    ab_p = suave((q - 40) / 4) * (1 - suave((q - 88) / 6))
    for h, sx in abas:
        h.rotation_euler = (0, sx * math.radians(120) * ab_p, 0)
        chave(h, q, 'rotation_euler')
    # braço
    xc, w, fech, soc, kk, fase = braco(q)
    phi, L = ik_lanca(w)
    th = phi - PI / 2
    carro.location = (xc, 0, 0)
    chave(carro, q, 'location')
    lanca.rotation_euler = (th, 0, 0)
    chave(lanca, q, 'rotation_euler')
    interna.location = (0, 0, L - L_INT)
    chave(interna, q, 'location')
    pulso.rotation_euler = (-th, 0, 0)
    chave(pulso, q, 'rotation_euler')
    for m, sx in mandibulas:
        m.location.x = sx * 0.02 * (1 - fech)
        chave(m, q, 'location')
    for k2, o in enumerate(soquete):
        o.location = (0, -0.367 + SOCA * soc * (k2 + 1) / 3, -0.10)
        chave(o, q, 'location')
    A = A_CIL
    Bc = Vector((0, AY, SZ)) + Matrix.Rotation(th, 3, 'X') @ Vector((0.08, -0.06, B_CIL))
    dc = Bc - A
    cil_l.rotation_quaternion = dc.to_track_quat('Z', 'Y')
    cil_h.location = (0, 0, dc.length - L_CH)
    chave(cil_l, q, 'rotation_quaternion')
    chave(cil_h, q, 'location')
    # pinos do elevador acompanham o foguete apresentado
    zp = PICK.z - 0.25
    for k in range(4):
        R = RC[k]
        if R - 4 <= q < R + 2:
            zp = PICK.z - 0.2 * (1 - suave((q - (R - 4)) / 4))
        elif R + 2 <= q < R + 5:
            zp = PICK.z - 0.25 * suave((q - R - 2) / 3)
    pinos.location = (0, PICK.y, zp)
    chave(pinos, q, 'location')
    # foguetes: no tubo, em voo, de recarga
    for k in range(4):
        mostrar(f_tubo[k], q < TF[k], q)
        mostrar(s_tubo[k], q < TF[k], q)
        dt = q - TF[k]
        voa = 0 <= dt < FL
        mostrar(f_voo[k], voa, q)
        if voa:
            if dt == 0:
                Mc = M_casulo(yaw, pitch)
                r, c = DISPARO[k]
                yc, zc = tubo_yz(r, c)
                pos = Mc @ Vector((X_TRAS_F + 0.25, yc, zc))
                dd = Mc.to_3x3() @ Vector((1, 0, 0))
            else:
                s = s_voo(dt)
                pos = bez(k, s)
                dd = bez_d(k, s)
            f_voo[k].location = pos
            f_voo[k].rotation_quaternion = dd.normalized().to_track_quat('X', 'Z')
        else:
            f_voo[k].location = (0, 0, -3)
        chave(f_voo[k], q, 'location', 'rotation_quaternion')
        pc = foguete_carga_pos(k, q)
        mostrar(f_carga[k], pc is not None, q)
        f_carga[k].location = (pc if pc is not None else Vector((0, PICK.y, 0.3))) - Vector((0, LR / 2, 0))
        chave(f_carga[k], q, 'location')
        # jato traseiro
        fo, nu, lz, lo = jatos[k]
        if 0 <= dt <= 4:
            Mc = M_casulo(*pose(TF[k]))
            E_ = traseira_mundo(k, *pose(TF[k]))
            b = Mc.to_3x3() @ Vector((-1, 0, 0))
            f_ = [1.0, 0.85, 0.55, 0.3, 0.12][dt]
            ver_vol(fo, q)
            por_direcao(fo, E_ + b * (0.35 + 0.1 * dt), b, (0.42 + 0.1 * dt, 0.13 + 0.04 * dt, 0.13 + 0.04 * dt), (f_, 0, 0, 1), q)
            nu.hide_render = nu.hide_viewport = dt > 2
            nu.location = E_
            nu.rotation_quaternion = b.to_track_quat('Z', 'Y')
            nu.scale = (1, 1, max(0.05, 1.0 - 0.35 * dt))
            lo.location = E_ + b * 0.3
            lz.energy = 700 * f_
        else:
            esconder_vol(fo, q)
            nu.hide_render = nu.hide_viewport = True
            nu.location = (0, 0, -3)
            nu.scale = (1, 1, 1)
            lo.location = (0, 0, -3)
            lz.energy = 0.0
        chave(nu, q, 'location', 'rotation_quaternion', 'scale', 'hide_render', 'hide_viewport')
        chave(lo, q, 'location')
        lz.keyframe_insert('energy', frame=q)
        # fumaça densa do jato: sai para trás, bate no chão/defletor, espalha, sobe e dilui
        for j, o in enumerate(fumaca_jato[k]):
            nasce = j * 0.6
            age = dt - nasce
            if 0 <= age <= 36:
                tt = age / FPS
                Mc = M_casulo(*pose(TF[k]))
                E_ = traseira_mundo(k, *pose(TF[k]))
                b0 = Mc.to_3x3() @ Vector((-1, 0, 0))
                lj, vj, fj, ph = rnd_j[k][j]
                b = Matrix.Rotation(lj, 3, 'Z') @ (b0 + Vector((0, 0, vj))).normalized()
                D = 1.9 * fj * (1 - math.exp(-tt / 0.13))
                pos = E_ + b * D
                rad = 0.1 + 0.75 * (1 - math.exp(-tt / 0.5))
                zmin = chao_h(pos.x, pos.y) + rad * 0.45
                if pos.z < zmin:
                    extra = (zmin - pos.z) * 0.8
                    hz = Vector((b.x, b.y, 0)).normalized()
                    pos = Vector((pos.x, pos.y, zmin)) + hz * extra
                pos += Vector((0, 0, 0.3 * tt)) + VENTO * tt
                u = age / 36
                ver_vol(o, q)
                por_direcao(o, pos, b, (rad * 1.3, rad, rad * 0.9), ((1 - u) ** 2.6 / (0.45 + 1.4 * rad), min(1.0, 0.1 + u * 2.2), 0, 1), q)
            else:
                esconder_vol(o, q)
        # rastro de fumaça em curva (nasce onde o foguete passa, engorda e dilui)
        for j, o in enumerate(rastros[k]):
            sj = ((j + 0.5) / N_RS) ** 1.25
            nasce = FL * sj ** (1 / 1.35)
            age = None
            for qq in (q, q + QUADROS):
                aa = qq - TF[k] - nasce
                if 0 <= aa <= 60:
                    age = aa
                    break
            if age is None:
                esconder_vol(o, q)
                continue
            s0 = ((j) / N_RS) ** 1.25
            s1 = ((j + 1) / N_RS) ** 1.25
            p0, p1 = bez(k, s0), bez(k, s1)
            u = age / 60
            rad = 0.05 + 0.5 * (1 - math.exp(-age / 16))
            pos = (p0 + p1) / 2 + Vector((0, 0, 0.012 * age)) + VENTO * age / FPS
            ver_vol(o, q)
            por_direcao(o, pos, p1 - p0, ((p1 - p0).length * 0.85 + rad * 0.7, rad, rad), ((1 - u) ** 1.2, 0.8 + 0.2 * u, 0, 1), q)
        # fumaça residual saindo do tubo disparado (frente e trás)
        for j, o in enumerate(residuais[k]):
            per = 16
            if dt is None or dt < 3:
                esconder_vol(o, q)
                continue
            age = (dt - 3 - j * 5) % per
            if dt - 3 - j * 5 < 0:
                esconder_vol(o, q)
                continue
            inten = max(0.0, 1 - (dt - 3) / 70)
            nas = q - age
            Mc = M_casulo(*pose(nas))
            r, c = DISPARO[k]
            yc, zc = tubo_yz(r, c)
            base_p = Mc @ Vector(((PX1 + 0.02) if j < 2 else (PX0 - 0.02), yc, zc))
            pos = base_p + Vector((0.01 * age, 0.004 * age, 0.018 * age))
            u = age / per
            rad = 0.02 + 0.05 * u
            ver_vol(o, q)
            o.location = pos
            o.rotation_quaternion = Quaternion((1, 0, 0), j + u)
            o.scale = (rad, rad, rad * 1.8)
            dd = inten * math.sin(PI * min(1.0, u * 1.2 + 0.05)) * (1 - u) * 1.4
            o.color = (dd, 0.4 + 0.5 * u, 0, 1)
            chave(o, q, 'location', 'rotation_quaternion', 'scale', 'color')
        # explosão em área no alvo
        cl, fb, fms, poe, on, est, lz, fa = explosoes[k]
        T = ALVOS[k]
        ea = q - TI[k]
        if 0 <= ea <= 2:
            ver_vol(cl, q)
            r_ = (0.9, 1.5, 1.8)[ea]
            cl.location = T + Vector((0, 0, 0.6))
            cl.scale = (r_, r_, r_ * 0.8)
            cl.color = ((1.0, 0.6, 0.25)[ea], 0, 0, 1)
            chave(cl, q, 'location', 'scale', 'color')
        else:
            esconder_vol(cl, q)
        for o, v0 in fa:
            tt = ea / FPS
            viva = 0 <= ea <= 9
            p = T + Vector((0, 0, 0.5)) + v0 * tt + Vector((0, 0, -4.9 * tt * tt))
            mostrar(o, viva and p.z > 0.02, q, False)
            o.location = p if viva else T
            o.scale = (1.0 + 2.5 * min(1, tt * 4), 1, 1) if viva else (1, 1, 1)
            o.rotation_euler = (0, -math.atan2(v0.z - 9.8 * tt, math.hypot(v0.x, v0.y)), math.atan2(v0.y, v0.x))
            chave(o, q, 'location', 'scale', 'rotation_euler')
        lz.energy = 0.0 if ea < 0 else 90000.0 * math.exp(-ea / 2.2)
        lz.keyframe_insert('energy', frame=q)
        if 0 <= ea <= 16:
            u = ea / 16
            ver_vol(fb, q)
            r_ = 0.8 + 2.1 * (1 - math.exp(-ea / 3))
            fb.location = T + Vector((0, 0, 0.5 + 1.3 * u))
            fb.rotation_quaternion = Quaternion((0, 0, 1), k)
            fb.scale = (r_, r_, r_ * 0.85)
            fb.color = ((1 - u) ** 1.3, 0, 0, 1)
            chave(fb, q, 'location', 'rotation_quaternion', 'scale', 'color')
        else:
            esconder_vol(fb, q)
        for j, o in enumerate(fms):
            age = ea - 2 - j * 2
            if 0 <= age <= 44 and q <= QUADROS:
                u = age / 44
                r_ = 1.0 + 2.6 * (1 - math.exp(-age / 12)) - 0.2 * j
                ver_vol(o, q)
                o.location = T + Vector((0.3 * j - 0.3, 0.2 * j, 1.4 + 3.2 * (1 - math.exp(-age / 18)) + 0.6 * j)) + VENTO * age / FPS
                o.rotation_quaternion = Quaternion((0, 0, 1), j + u)
                o.scale = (r_, r_, r_ * 0.9)
                o.color = ((1 - u) ** 1.2, min(1.0, 0.05 + 1.1 * u), 0, 1)
                chave(o, q, 'location', 'rotation_quaternion', 'scale', 'color')
            else:
                esconder_vol(o, q)
        for j, o in enumerate(poe):
            age = ea
            if 0 <= age <= 42:
                u = age / 42
                a = j * 2 * PI / N_POE + k
                rr = 0.8 + 5.5 * (1 - math.exp(-age / 5)) * (0.8 + 0.4 * ((j * 7) % 5) / 4)
                r_ = 0.4 + 1.5 * (1 - math.exp(-age / 9))
                ver_vol(o, q)
                o.location = T + Vector((math.cos(a) * rr, math.sin(a) * rr, r_ * 0.72 + 0.05 + 0.2 * u))
                o.rotation_quaternion = Quaternion((0, 0, 1), a)
                o.scale = (r_ * 1.4, r_, r_ * 0.7)
                o.color = ((1 - u) ** 1.1, min(1.0, 0.4 + 1.2 * u), 0, 1)
                chave(o, q, 'location', 'rotation_quaternion', 'scale', 'color')
            else:
                esconder_vol(o, q)
        mostrar(on, 0 <= ea <= 3, q, False)
        rr = 0.8 + 5.0 * (ea / 3) ** 0.7 if ea >= 0 else 0.5
        on.location = T + Vector((0, 0, 0.12))
        on.scale = (rr, rr, 0.6 + 0.6 * max(0, ea) / 3)
        chave(on, q, 'location', 'scale')
        for o, v0, w0 in est:
            if ea < 0:
                mostrar(o, False, q, False)
                o.location = T
                chave(o, q, 'location', 'rotation_euler')
                continue
            tt = ea / FPS
            p = T + Vector((0, 0, 0.3)) + v0 * tt + Vector((0, 0, -4.9 * tt * tt))
            if p.z < 0.04:
                tc = (v0.z + math.sqrt(v0.z ** 2 + 4 * 4.9 * 0.26)) / (2 * 4.9)
                p = T + Vector((0, 0, 0.3)) + v0 * tc + Vector((0, 0, -4.9 * tc * tc))
                p.z = 0.04
                rot = w0 * tc
            else:
                rot = w0 * tt
            mostrar(o, True, q, False)
            o.location = p
            o.rotation_euler = tuple(rot)
            chave(o, q, 'location', 'rotation_euler')
    # sobras ejetadas
    for o, ant, tr, parou, q0 in sobras:
        e = q - q0
        mostrar(ant, e < parou, q)
        mostrar(o, e >= 0, q)
        if e >= 0:
            o.location, o.rotation_euler = tr[min(e, len(tr) - 1)]
        else:
            o.location, o.rotation_euler = tr[0]
        chave(o, q, 'location', 'rotation_euler')
    # foguete entrando pela boca (esteira) e luz do paiol
    u = ((q - 48) % 12) / 12 if q >= 48 else 0.0
    if q == 1:
        pass

esteira_f = foguete('foguete_esteira')
esteira_f.rotation_euler = (0, 0, PI / 2)
for q in range(1, QUADROS + 1):
    u = ((q - 48) % 12) / 12 if q >= 48 else 0.0
    esteira_f.location = (0, -1.475 + 0.1 * u, 0.145 + 0.011 + RR)
    chave(esteira_f, q, 'location')
# laço linear nas chaves (sem suavizar entre quadros)
for o in list(sc.objects) + list(bpy.data.lights):
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (10, 4, -0.5), (120, 120, 1.0))
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
cam_d.clip_end = 300
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def foto(nome, quadro, pos, alvo, lente, amostras=128, res=(1300, 1000)):
    sc.cycles.samples = amostras
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.frame_set(quadro)
    mirar(pos, alvo, lente)
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


TA = ALVOS[0]
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    if so_uma in (None, '0'):
        foto('lanca_foguetes_0.png', 30, (1.3, -4.4, 2.2), (0.05, 0.1, 0.8), 30, 128, (1300, 1100))
    if so_uma in (None, 'perto'):
        foto('lanca_foguetes_perto.png', 53, (1.35, -2.05, 1.6), (0.03, -0.76, 1.0), 28)
    if so_uma in (None, 'salva'):
        foto('lanca_foguetes_salva.png', 37, (7.0, -9.0, 1.8), (5.6, 4.0, 4.6), 18, 112, (1500, 900))
    if so_uma in (None, 'impacto'):
        foto('lanca_foguetes_impacto.png', 46, tuple(TA + Vector((-13.0, -11.0, 3.8))), tuple(TA + Vector((0.3, 0.6, 1.4))), 30, 112, (1500, 1000))
if modo == 'dbg':
    exec(open(os.path.join(AQUI, '..', 'dbg.py')).read())
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    foto('lanca_foguetes_teste.png', int(v[7]), v[0:3], v[3:6], v[6], 24, (900, 700))
print('LANCA_FOGUETES ok')
