"""Estudo isolado (fora do jogo): ACUMULADOR, o banco de energia da IA, 2×2 tiles, sem portas.
Guarda a sobra de energia da rede (80 MJ, 500 kW) e devolve quando falta.
Quatro células octogonais grandes (amarelo gasto, nervuras de aço, tampa grafite aparafusada) com terminais de cobre
grossos, válvula de alívio de gás e visor de carga (faixa luminosa que sobe e desce: âmbar vazio → violeta cheio).
No meio, uma coluna-bobina de cobre sobe até um prato emissor com quatro garras: o cristal da IA levita num campo,
preso por nada, e recebe a energia pelos barramentos de cobre que vêm dos polos + das células; arcos pequenos saltam
das garras enquanto carrega. Refrigeração: bomba e radiador com ventoinha girando no leste, coletores ao longo dos
vãos, camisas de refrigeração em volta das células, visores com o fluido borbulhando, reservatório de expansão no
oeste. Cabos grossos em feixe: polos − até isoladores de porcelana nos cantos; entrada da rede por um cavalete de
isoladores no sul até a caixa de junção da coluna. Sujeira: queimado de arco, eletrólito vazando com crosta branca e
esverdeada, escorridos de ferrugem, pó.
Animação (laço de 4 s): a carga sobe (carregando: gás nas válvulas, arcos, faíscas no terminal frouxo, energia
fluindo da rede para o cristal e do cristal para as células) e desce (descarregando: fluxo invertido).
Uso: blender -b --python estudo_acumulador.py -- foto [0|1|2|3|perto]
     blender -b --python estudo_acumulador.py -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

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
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
    """Anel tubular contínuo (sem emendas), no plano xy local girado por `rot`."""
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


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, flange=True):
    """Cano rígido por pontos: trechos retos, cotovelos redondos e flanges perto de cada curva."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.16:
            for c in (a + u * 0.05, b - u * 0.05):
                tubo(bf, c - u * 0.008, c + u * 0.008, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def feixe(bc, ba, pts, lat, n=3, r=0.014, passo=4):
    """Cabos paralelos (deslocados em `lat`) seguindo a mesma curva, com abraçadeiras a cada `passo` pontos."""
    for i in range(n):
        off = lat * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 0.6), 12)


def octo(bm, c, apo, z0, z1):
    """Prisma octogonal com faces planas viradas para os eixos e as diagonais."""
    R = apo / math.cos(PI / 8)
    vs0 = [bm.verts.new((c.x + R * math.cos(PI / 8 + k * PI / 4), c.y + R * math.sin(PI / 8 + k * PI / 4), z0)) for k in range(8)]
    vs1 = [bm.verts.new((v.co.x, v.co.y, z1)) for v in vs0]
    bm.faces.new(list(reversed(vs0)))
    bm.faces.new(vs1)
    for k in range(8):
        bm.faces.new((vs0[k], vs0[(k + 1) % 8], vs1[(k + 1) % 8], vs1[k]))


def rot_face(n):
    """Matriz 3×3 com x tangente à face, y = normal da face (horizontal) e z para cima."""
    n = Vector((n.x, n.y, 0)).normalized()
    return Matrix((Vector((n.y, -n.x, 0)), n, Vector((0, 0, 1)))).transposed()


BMS = {}


def B(nome, mat, liso=False):
    """bmesh compartilhado por (nome, material): junta peças estáticas iguais num objeto só."""
    k = (nome, mat, liso)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat():
    """Cristal da IA: vidro violeta translúcido com brilho interno (a força é animada com a carga)."""
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.15
    b.inputs['Transmission Weight'].default_value = 0.45
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 2.0
    ru = mats.no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 6.0})      # trincas e nuvens internas
    bump = mats.no(nt, 'ShaderNodeBump', **{'Strength': 0.2})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def vidro_mat(nome, cor, forca=0.0):
    """Vidro (visor) com o fluido dentro: translúcido, um pouco de brilho próprio para ler de longe."""
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = 0.7
    b.inputs['IOR'].default_value = 1.45
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def campo_mat(nome, cor, dens, emis):
    """Campo de contenção em volume: névoa violeta tênue que brilha, mais densa no meio (ruído)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.05, 0.02, 0.1, 1)
    vol.inputs['Emission Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 4.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')                  # some na borda da esfera unitária
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.35})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = dens
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='forca')
    e.inputs[1].default_value = emis
    nt.links.new(mul.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.85, ferrugem=0.35),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.72, 0.36, 0.2), 1.0, 0.34, pintura=False, sujeira=0.9),
    'bobina': mats.material('Bobina', (0.78, 0.4, 0.2), 1.0, 0.25, pintura=False, sujeira=0.5),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'porcelana': mats.material('Porcelana', (0.42, 0.19, 0.09), 0, 0.2, pintura=False, sujeira=0.7, desgaste=0.0),
    'cabo': mats.material('Cabo', (0.035, 0.035, 0.04), 0, 0.6, pintura=False, sujeira=0.7, desgaste=0.0),
    'isol_verm': mats.material('Isolador vermelho', (0.45, 0.04, 0.03), 0, 0.5, desgaste=0.5, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'escuro': mats.material('Fundo do visor', (0.01, 0.01, 0.012), 0, 0.3, pintura=False, sujeira=0.0, desgaste=0.0),
    'chamusco': mats.material('Chamusco', (0.018, 0.015, 0.014), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'crosta': mats.material('Crosta de eletrólito', (0.62, 0.66, 0.55), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'crosta_verde': mats.material('Crosta verde', (0.2, 0.38, 0.18), 0, 0.8, pintura=False, sujeira=0.6, desgaste=0.0),
    'eletrolito': mats.material('Eletrólito', (0.1, 0.14, 0.06), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
    'ferrugem': mats.material('Escorrido', (0.2, 0.07, 0.02), 0.3, 0.8, pintura=False, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.2, 0.18, 0.16), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'cristal': cristal_mat(),
    'carga': emissivo('Faixa de carga', AMBAR, 1.6),
    'fluxo': emissivo('Fluxo', (0.5, 0.18, 1.0), 4.0),
    'arco': emissivo('Arco', (0.7, 0.5, 1.0), 16.0),
    'faisca': emissivo('Faísca', (1.0, 0.7, 0.3), 60.0),
    'anel_campo': emissivo('Anel do campo', (0.5, 0.2, 1.0), 4.0),
    'led_verde': emissivo('Led verde', (0.2, 1.0, 0.3), 10.0),
    'led_ambar': emissivo('Led âmbar', AMBAR, 10.0),
    'olho': emissivo('Olho do sensor', VIOLETA, 8.0, (0.05, 0.02, 0.1)),
    'refrigerante': vidro_mat('Refrigerante', (0.35, 0.75, 0.12), 0.6),
    'bolha': emissivo('Bolha', (0.85, 1.0, 0.7), 2.0),
    'campo': campo_mat('Campo', (0.5, 0.2, 1.0), 4.0, 3.0),
    'feixe_luz': campo_mat('Feixe', (0.5, 0.2, 1.0), 3.0, 6.0),
    'gas': base3d.volume_mat('Gás', (0.82, 0.85, 0.8), 4.0, 1.2, 1.9),
    'vapor': base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 3.0, 1.0, 1.7),
})

# ------------------------------------------------------------------ medidas
Z0 = 0.08                      # topo da laje
AP = 0.27                      # apótema da célula
R8 = AP / math.cos(PI / 8)     # raio até o vértice do octógono
Z_PL, Z_TOP, Z_CAP = 0.14, 1.10, 1.15
CELS = [Vector((sx * 0.47, sy * 0.47, 0)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]   # NE, NO, SO, SE
R_JAQ, r_JAQ = 0.335, 0.02     # camisas de refrigeração
Z_JAQ = (0.28, 0.88)
Y_COL = 0.16                   # coletores de refrigeração (|y|)
Z_ENT, Z_RET = 0.17, 0.97      # coletor de entrada (baixo) e de retorno (alto)
Z_BAR = 1.29                   # barramentos e anel coletor
R_ANEL = 0.24
CC = Vector((0, 0, 1.43))      # centro do cristal
Z_JAN0, H_JAN = 0.42, 0.36     # visor de carga
LAT_HEADER = (0.45, -0.62)     # x da bomba (leste) e da ponta oeste do coletor

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-0.98, -0.98, 0), (0.98, 0.98, Z0))
obj('laje', bm, 'concreto')
bm = B('laje_listras', 'listras')
for s in (-1, 1):
    caixa_de(bm, (-0.985, s * 0.985 - 0.012, 0.0), (0.985, s * 0.985 + 0.012, Z0 + 0.002))
    caixa_de(bm, (s * 0.985 - 0.012, -0.985, 0.0), (s * 0.985 + 0.012, 0.985, Z0 + 0.002))

# ------------------------------------------------------------------ células
janelas = []                   # (objeto da faixa)
SAIDAS_GAS = []                # (ponto, direção) das válvulas de alívio
VISORES = []                   # (base, topo) dos visores de refrigerante
for ic, C in enumerate(CELS):
    sx, sy = (1 if C.x > 0 else -1), (1 if C.y > 0 else -1)
    diag = Vector((sx, sy, 0)).normalized()                                # para fora (canto)
    perp = Vector((-diag.y, diag.x, 0))
    bm = B('celula_base', 'ferro')
    octo(bm, C, AP + 0.02, Z0, Z_PL)                                       # sapata
    for k in range(4):                                                     # chumbadores da sapata
        a = PI / 4 + k * PI / 2
        cil(B('parafusos', 'aco'), C + Vector((math.cos(a), math.sin(a), 0)) * (R8 + 0.005) * 0.93 + Vector((0, 0, Z_PL + 0.008)),
            0.014, 0.018, lados=6)
    octo(B('celula_corpo', 'amarelo'), C, AP, Z_PL, Z_TOP)
    bm = B('celula_nervuras', 'ferro')
    for k in range(8):                                                     # nervuras de aço nos vértices
        a = PI / 8 + k * PI / 4
        caixa(bm, C + Vector((math.cos(a), math.sin(a), 0)) * (R8 + 0.002) + Vector((0, 0, (Z_PL + Z_TOP) / 2)),
              (0.024, 0.024, Z_TOP - Z_PL), Matrix.Rotation(a, 3, 'Z'))
    for z in (Z_PL + 0.04, Z_TOP - 0.05):                                  # cintas grafite
        octo(B('celula_cintas', 'grafite'), C, AP + 0.006, z - 0.025, z + 0.025)
    # tampa aparafusada
    octo(B('tampa', 'grafite'), C, AP + 0.015, Z_TOP, Z_CAP)
    for k in range(16):
        a = k * 2 * PI / 16 + 0.1
        cil(B('parafusos', 'aco'), C + Vector((math.cos(a), math.sin(a), 0)) * 0.235 + Vector((0, 0, Z_CAP + 0.008)),
            0.012, 0.016, lados=6)
    for s in (-1, 1):                                                      # olhais de içamento
        p = C + perp * s * 0.2 + Vector((0, 0, Z_CAP))
        toro(B('olhais', 'aco', True), p + Vector((0, 0, 0.03)), 0.022, 0.007, 16, 8,
             rot_face(perp) @ Matrix.Rotation(PI / 2, 3, 'X'))
        caixa(B('olhais_base', 'ferro'), p + Vector((0, 0, 0.006)), (0.05, 0.03, 0.012), rot_face(perp))
    # terminais: + para dentro (vermelho), − para fora (preto)
    for polo, dist in (('+', -0.12), ('-', 0.12)):
        p = C + diag * dist
        cil(B('terminal_colar', 'isol_verm' if polo == '+' else 'borracha'), p + Vector((0, 0, Z_CAP + 0.018)), 0.055, 0.036, lados=20)
        cil(B('terminal_poste', 'cobre', True), p + Vector((0, 0, Z_CAP + 0.09)), 0.032, 0.16, lados=20)
        cil(B('terminal_porca', 'aco'), p + Vector((0, 0, Z_BAR - 0.024)), 0.048, 0.024, lados=6)
        cil(B('terminal_porca', 'aco'), p + Vector((0, 0, Z_BAR + 0.032)), 0.045, 0.02, lados=6)
    # válvula de alívio de gás na tampa
    bv = C + perp * 0.13 + Vector((0, 0, Z_CAP))
    bm = B('valvula', 'ferro', True)
    cil(bm, bv + Vector((0, 0, 0.012)), 0.045, 0.024, lados=16)            # flange
    cil(bm, bv + Vector((0, 0, 0.06)), 0.022, 0.08, lados=14)              # pescoço
    cil(bm, bv + Vector((0, 0, 0.11)), 0.038, 0.04, lados=14)              # corpo
    for k in range(4):
        cil(B('valvula_mola', 'aco'), bv + Vector((0, 0, 0.14 + k * 0.016)), 0.026, 0.006, lados=12)
    cil(bm, bv + Vector((0, 0, 0.21)), 0.02, 0.018, lados=12)              # chapéu
    tubo(bm, bv + Vector((0, 0, 0.11)), bv + Vector((0, 0, 0.11)) + diag * 0.09 + Vector((0, 0, 0.03)), 0.016, 12)
    SAIDAS_GAS.append((bv + Vector((0, 0, 0.11)) + diag * 0.1 + Vector((0, 0, 0.035)), (diag + Vector((0, 0, 0.6))).normalized()))
    # camisas de refrigeração e grampos
    for z in Z_JAQ:
        toro(B('camisas', 'casco', True), C + Vector((0, 0, z)), R_JAQ, r_JAQ, 64, 12)
        for k in range(8):
            a = PI / 8 + k * PI / 4
            caixa(B('grampos', 'ferro'), C + Vector((math.cos(a), math.sin(a), 0)) * 0.318 + Vector((0, 0, z)),
                  (0.03, 0.026, 0.05), Matrix.Rotation(a, 3, 'Z'))
    # visor de refrigerante (bypass entre as camisas, na face diagonal de fora)
    pv = C + diag * R_JAQ
    bm, bf = B('visor_cano', 'casco', True), B('flanges', 'ferro', True)
    tubo(bm, pv + Vector((0, 0, Z_JAQ[0])), pv + Vector((0, 0, 0.45)), 0.018, 16)
    tubo(bm, pv + Vector((0, 0, 0.72)), pv + Vector((0, 0, Z_JAQ[1])), 0.018, 16)
    for z in (0.45, 0.72):
        cil(bf, pv + Vector((0, 0, z)), 0.034, 0.024, lados=16)
    for k in range(3):                                                     # grade de proteção do vidro
        a = k * 2 * PI / 3 + 0.4
        o3 = Vector((math.cos(a), math.sin(a), 0)) * 0.03
        tubo(B('visor_grade', 'aco'), pv + o3 + Vector((0, 0, 0.45)), pv + o3 + Vector((0, 0, 0.72)), 0.004, 6)
    cil(B('visor_vidro', 'refrigerante', True), pv + Vector((0, 0, 0.585)), 0.022, 0.25, lados=20)
    VISORES.append((pv + Vector((0, 0, 0.47)), pv + Vector((0, 0, 0.7))))
    # visores de carga nas duas faces de fora (eixos)
    for n in (Vector((sx, 0, 0)), Vector((0, sy, 0))):
        R = rot_face(n)
        f = C + n * AP
        zc = Z_JAN0 + H_JAN / 2
        bm = B('visor_moldura', 'ferro')
        for s in (-1, 1):
            caixa(bm, f + R @ Vector((s * 0.042, 0.012, 0)) + Vector((0, 0, zc)), (0.016, 0.024, H_JAN + 0.05), R)
            caixa(bm, f + R @ Vector((0, 0.012, 0)) + Vector((0, 0, zc + s * (H_JAN / 2 + 0.017))), (0.1, 0.024, 0.018), R)
        caixa(B('visor_fundo', 'escuro'), f + R @ Vector((0, 0.004, 0)) + Vector((0, 0, zc)), (0.068, 0.008, H_JAN + 0.01), R)
        for k in range(1, 9):                                              # marcas de nível
            caixa(B('visor_marcas', 'grafite'), f + R @ Vector((0, 0.016, 0)) + Vector((0, 0, Z_JAN0 + k * H_JAN / 9)),
                  (0.068, 0.006, 0.006), R)
        for s in (-1, 1):                                                  # parafusos da moldura
            for zz in (Z_JAN0 - 0.017, Z_JAN0 + H_JAN + 0.017):
                cil(B('parafusos', 'aco'), f + R @ Vector((s * 0.035, 0.026, 0)) + Vector((0, 0, zz)), 0.006, 0.006, n, lados=6)
        bm = bmesh.new()
        caixa_de(bm, (-0.03, -0.003, 0.0), (0.03, 0.003, H_JAN))
        fx = obj('faixa_carga', bm, 'carga')
        fx.location = f + R @ Vector((0, 0.011, 0)) + Vector((0, 0, Z_JAN0))
        fx.rotation_euler = R.to_euler()
        janelas.append(fx)
    # sujeira: escorridos de ferrugem dos parafusos da tampa e da cinta
    for k in range(18):
        a = random.choice((0, 1, 2, 3, 4, 5, 6, 7)) * PI / 4
        n = Vector((math.cos(a), math.sin(a), 0))
        if n.dot(diag) < -0.3:
            continue
        L = random.uniform(0.1, 0.55)
        off = random.uniform(-0.09, 0.09)
        if abs(n.x) + abs(n.y) < 1.1 and abs(off) < 0.06:                  # não escorre por cima do visor
            continue
        R = rot_face(n)
        z1 = random.choice((Z_TOP - 0.08, Z_JAQ[1] - 0.03, 0.3))
        caixa(B('escorridos', 'ferrugem' if k % 3 else 'chamusco'),
              C + n * (AP + 0.001) + R @ Vector((off, 0, 0)) + Vector((0, 0, z1 - L / 2)),
              (random.uniform(0.006, 0.02), 0.002, min(L, z1 - Z_PL)), R)
    for k in range(3):                                                     # fuligem de arco no alto da face
        a = random.choice((0, 1, 2, 3, 4, 5, 6, 7)) * PI / 4
        n = Vector((math.cos(a), math.sin(a), 0))
        R = rot_face(n)
        for j in range(5):
            caixa(B('escorridos', 'chamusco'), C + n * (AP + 0.0012) + R @ Vector((random.uniform(-0.06, 0.06), 0, 0)) +
                  Vector((0, 0, Z_TOP - 0.1 - j * 0.004)), (random.uniform(0.003, 0.008), 0.002, random.uniform(0.04, 0.16)), R)

# eletrólito vazando: crosta nos terminais, escorrido pela face, poça com crosta na laje
for ic, C in enumerate(CELS):
    sx, sy = (1 if C.x > 0 else -1), (1 if C.y > 0 else -1)
    diag = Vector((sx, sy, 0)).normalized()
    for dist in (-0.12, 0.12):
        p = C + diag * dist
        for k in range(9 if ic in (0, 2) else 5):
            a = random.uniform(0, 2 * PI)
            r = random.uniform(0.05, 0.075)
            pedra(B('crosta', 'crosta' if random.random() < 0.6 else 'crosta_verde'),
                  p + Vector((math.cos(a) * r, math.sin(a) * r, Z_CAP + 0.004)), random.uniform(0.01, 0.022), 0.35)
    if ic in (0, 2):                                                       # duas células vazam de verdade
        n = Vector((0, sy, 0)) if ic == 0 else Vector((sx, 0, 0))
        R = rot_face(n)
        for k in range(4):
            off = 0.06 + k * 0.016
            L = random.uniform(0.35, 0.8)
            caixa(B('eletrolito_escorrido', 'crosta_verde' if k % 2 else 'crosta'),
                  C + n * (AP + 0.0015) + R @ Vector((off, 0, 0)) + Vector((0, 0, Z_TOP - 0.02 - L / 2)),
                  (random.uniform(0.008, 0.016), 0.003, L), R)
        pc = C + n * (AP + 0.1) + R @ Vector((0.09, 0, 0))
        mancha(B('eletrolito_poca', 'eletrolito'), (pc.x, pc.y), 0.09, Z0 + 0.0015)
        for k in range(14):
            a = random.uniform(0, 2 * PI)
            pedra(B('crosta', 'crosta'), Vector((pc.x + math.cos(a) * 0.1, pc.y + math.sin(a) * 0.08, Z0 + 0.002)),
                  random.uniform(0.008, 0.016), 0.3)

# ------------------------------------------------------------------ coluna-bobina central, prato emissor, garras
bm = B('coluna_caixa', 'grafite')
caixa_de(bm, (-0.11, -0.11, Z0), (0.11, 0.11, 0.24))
caixa_de(bm, (-0.115, -0.115, 0.235), (0.115, 0.115, 0.25))
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(B('parafusos', 'aco'), Vector((sx * 0.1, sy * 0.1, 0.252)), 0.008, 0.008, lados=6)
cil(B('coluna_nucleo', 'ferro', True), Vector((0, 0, 0.625)), 0.08, 0.75, lados=24)
for z in (0.3, 0.94):
    cil(B('coluna_flanges', 'aco', True), Vector((0, 0, z)), 0.125, 0.025, lados=24)
nz = 0
z = 0.325
while z < 0.92:
    toro(B('bobina', 'bobina', True), Vector((0, 0, z)), 0.097, 0.0105, 40, 8)
    z += 0.0215
for k in range(4):                                                         # réguas que seguram as espiras
    a = k * PI / 2 + PI / 4
    caixa(B('coluna_reguas', 'porcelana'), Vector((math.cos(a), math.sin(a), 0)) * 0.112 + Vector((0, 0, 0.62)),
          (0.018, 0.018, 0.62), Matrix.Rotation(a, 3, 'Z'))
bm = B('prato', 'ferro', True)
cil(bm, Vector((0, 0, 1.05)), 0.085, 0.1, lados=32, r2=0.19)
cil(bm, Vector((0, 0, 1.104)), 0.19, 0.01, lados=32)
toro(B('prato_aro', 'bobina', True), Vector((0, 0, 1.105)), 0.19, 0.012, 48, 10)
cil(B('prato_emissor', 'olho'), Vector((0, 0, 1.11)), 0.055, 0.006, lados=24)
GARRAS = []
for k in range(4):                                                         # garras nos eixos (entre os barramentos)
    d = Vector((math.cos(k * PI / 2), math.sin(k * PI / 2), 0))
    pts = [d * 0.15 + Vector((0, 0, 1.1)), d * 0.19 + Vector((0, 0, 1.26)), d * 0.2 + Vector((0, 0, 1.33)), d * 0.2 + Vector((0, 0, 1.45))]
    cano(B('garras', 'aco', True), B('garras_flanges', 'ferro', True), pts, 0.013, flange=False)
    caixa(B('garras_pe', 'ferro'), d * 0.15 + Vector((0, 0, 1.115)), (0.05, 0.05, 0.02), Matrix.Rotation(k * PI / 2, 3, 'Z'))
    for j in range(6):                                                     # bobina pequena na ponta
        toro(B('garras_bobina', 'bobina', True), d * 0.2 + Vector((0, 0, 1.345 + j * 0.016)), 0.022, 0.006, 20, 6)
    curva(B('garras_ponta', 'cromo', True), d * 0.2 + Vector((0, 0, 1.47)), 0.022, 16)
    GARRAS.append(d * 0.2 + Vector((0, 0, 1.47)) - d * 0.02)

# anel coletor e barramentos (polos + das células)
toro(B('anel_coletor', 'cobre', True), Vector((0, 0, Z_BAR)), R_ANEL, 0.016, 64, 12)
BARRAS = []
for C in CELS:
    diag = Vector((C.x, C.y, 0)).normalized()
    p0 = C - diag * 0.12
    a, b = diag * (R_ANEL - 0.02), Vector((p0.x, p0.y, 0)) + diag * 0.035
    R = rot_face(diag)
    caixa(B('barramentos', 'cobre'), (a + b) / 2 + Vector((0, 0, Z_BAR)), (0.05, (b - a).length, 0.014), R)
    for s in (-1, 1):                                                      # parafusos da emenda no anel
        cil(B('parafusos', 'aco'), diag * R_ANEL + R @ Vector((s * 0.014, 0, 0)) + Vector((0, 0, Z_BAR + 0.012)), 0.007, 0.01, lados=6)
    for t in (0.35, 0.7):                                                  # abraçadeiras isolantes
        p = a + (b - a) * t
        caixa(B('barras_isol', 'isol_verm'), p + Vector((0, 0, Z_BAR)), (0.064, 0.02, 0.028), R)
    BARRAS.append((a + Vector((0, 0, Z_BAR + 0.012)), b + Vector((0, 0, Z_BAR + 0.012))))
    for k in range(4):                                                     # queimado de arco na emenda
        mancha(B('chamusco', 'chamusco'), (p0.x + random.uniform(-0.06, 0.06), p0.y + random.uniform(-0.06, 0.06)),
               random.uniform(0.02, 0.05), Z_CAP + 0.0015)

# cristal levitando
cristal = bpy.data.objects.new('cristal', None)
sc.collection.objects.link(cristal)
cristal.location = CC
bm = bmesh.new()
rr = [0.09 * (1 + random.uniform(-0.12, 0.12)) for _ in range(6)]
anel_b = [bm.verts.new((math.cos(k * PI / 3) * rr[k], math.sin(k * PI / 3) * rr[k], -0.055)) for k in range(6)]
anel_c = [bm.verts.new((math.cos(k * PI / 3) * rr[k] * 0.93, math.sin(k * PI / 3) * rr[k] * 0.93, 0.065)) for k in range(6)]
topo = bm.verts.new((0.01, -0.006, 0.2))
fundo = bm.verts.new((-0.006, 0.008, -0.17))
for k in range(6):
    j = (k + 1) % 6
    bm.faces.new((anel_b[k], anel_b[j], anel_c[j], anel_c[k]))
    bm.faces.new((anel_c[k], anel_c[j], topo))
    bm.faces.new((anel_b[j], anel_b[k], fundo))
obj('cristal_corpo', bm, 'cristal', cristal)
for k in range(3):                                                         # lascas que orbitam junto
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.018)
    for v in bm.verts:
        v.co.z *= 2.2
    o = obj('lasca', bm, 'cristal', cristal)
    a = k * 2 * PI / 3
    o.location = (math.cos(a) * 0.14, math.sin(a) * 0.14, 0.03 * (k - 1))
    o.rotation_euler = (0.4, 0.3 * k, a)
luz_c = bpy.data.lights.new('Cristal', 'POINT')
luz_c.color = VIOLETA
luz_c.shadow_soft_size = 0.05
lc = bpy.data.objects.new('Cristal', luz_c)
sc.collection.objects.link(lc)
lc.location = Vector((0, 0, 1.17))                                         # abaixo do cristal (luz dentro estoura)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
campo = obj('campo', bm, 'campo')
campo.location = CC
campo.scale = (0.2, 0.2, 0.26)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 1.0, 1.0, lados=16)
feixe_o = obj('feixe', bm, 'feixe_luz')                                    # feixe do prato até o cristal
feixe_o.location = Vector((0, 0, (1.11 + CC.z - 0.17) / 2))
feixe_o.scale = (0.045, 0.045, (CC.z - 0.17 - 1.11) / 2 + 0.02)
aneis_campo = []
for k in range(2):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 0.155 + 0.012 * k, 0.003, 64, 6)
    o = obj('anel_campo', bm, 'anel_campo')
    o.location = CC
    o.rotation_mode = 'QUATERNION'
    aneis_campo.append(o)

# arcos: garra → cristal, 3 formas por garra
arcos = []
for ig, p0 in enumerate(GARRAS):
    for v in range(3):
        alvo = CC + (p0 - CC).normalized() * 0.075 + Vector((0, 0, random.uniform(-0.07, 0.07)))
        bm = bmesh.new()
        pts = [p0]
        for i in range(1, 7):
            t = i / 7
            pts.append(p0.lerp(alvo, t) + Vector([random.uniform(-1, 1) for _ in range(3)]) * 0.025 * math.sin(PI * t))
        pts.append(alvo)
        for a, b in zip(pts, pts[1:]):
            tubo(bm, a, b, 0.0035, 5)
        if v == 0:                                                         # galho
            m = pts[3]
            q = m + Vector([random.uniform(-1, 1) for _ in range(3)]) * 0.04
            tubo(bm, m, q, 0.0025, 5)
        arcos.append((obj('arco', bm, 'arco'), ig, v))

# ------------------------------------------------------------------ terminal frouxo (SE): arco e faíscas
C_SE = CELS[3]
P_FROUXO = C_SE + Vector((C_SE.x, C_SE.y, 0)).normalized() * 0.12 + Vector((0, 0, Z_CAP + 0.04))
arcos_t = []
for v in range(2):
    bm = bmesh.new()
    a0 = P_FROUXO + Vector((0.03, 0.0, 0.0))
    a1 = P_FROUXO + Vector((0.06 + 0.02 * v, -0.04 + 0.05 * v, -0.04))
    pts = [a0] + [a0.lerp(a1, t) + Vector([random.uniform(-1, 1) for _ in range(3)]) * 0.01 for t in (0.3, 0.6)] + [a1]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, 0.0025, 5)
    arcos_t.append(obj('arco_terminal', bm, 'arco'))
faiscas = []
for k in range(14):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.005)
    faiscas.append(obj('faisca', bm, 'faisca'))
vel_f = [Vector((random.uniform(-0.2, 0.9), random.uniform(-0.9, 0.2), random.uniform(0.3, 1.1))) for _ in faiscas]
luz_t = bpy.data.lights.new('Faísca', 'POINT')
luz_t.color = (0.8, 0.6, 1.0)
luz_t.shadow_soft_size = 0.02
lt = bpy.data.objects.new('Faísca', luz_t)
sc.collection.objects.link(lt)
lt.location = P_FROUXO + Vector((0.05, -0.02, 0.0))

# ------------------------------------------------------------------ refrigeração
# coletores de entrada (baixo) e retorno (alto) ao longo do vão leste-oeste
for sy in (-1, 1):
    y = sy * Y_COL
    cano(B('canos', 'casco', True), B('flanges', 'ferro', True),
         [(LAT_HEADER[0], sy * 0.09, Z_ENT), (LAT_HEADER[0], y, Z_ENT), (LAT_HEADER[1], y, Z_ENT)], 0.024)
    cil(B('flanges', 'ferro', True), Vector((LAT_HEADER[1] - 0.01, y, Z_ENT)), 0.036, 0.02, Vector((1, 0, 0)), lados=16)
    cano(B('canos', 'casco', True), B('flanges', 'ferro', True), [(0.72, y, Z_RET), (-0.62, y, Z_RET)], 0.024)
    for sx in (-1, 1):                                                     # subidas: coletor ↔ camisas
        x = sx * 0.47
        jy = sy * (0.47 - R_JAQ)
        tubo(B('canos', 'casco', True), (x, y, Z_ENT), (x, jy, Z_JAQ[0]), 0.016, 14)
        tubo(B('canos', 'casco', True), (x, jy, Z_JAQ[1]), (x, y, Z_RET), 0.016, 14)
        cil(B('flanges', 'ferro', True), Vector((x, y, Z_ENT + 0.03)), 0.022, 0.012, lados=14)
    for x in (-0.3, 0.3):                                                  # suportes dos coletores no chão
        caixa_de(B('suportes', 'ferro'), (x - 0.02, y - 0.03, Z0), (x + 0.02, y + 0.03, Z_ENT - 0.022))
cano(B('canos', 'casco', True), B('flanges', 'ferro', True),
     [(-0.62, -Y_COL, Z_RET), (-0.62, Y_COL, Z_RET)], 0.024, flange=False)
for sy in (-1, 1):
    curva(B('canos', 'casco', True), Vector((-0.62, sy * Y_COL, Z_RET)), 0.024)
cano(B('canos', 'casco', True), B('flanges', 'ferro', True), [(-0.62, 0, Z_RET), (-0.78, 0, Z_RET), (-0.78, 0, 0.86)], 0.024)
# visor no retorno
cil(B('visor_vidro', 'refrigerante', True), Vector((0.3, Y_COL, Z_RET)), 0.027, 0.12, Vector((1, 0, 0)), lados=20)
for x in (0.235, 0.365):
    cil(B('flanges', 'ferro', True), Vector((x, Y_COL, Z_RET)), 0.04, 0.02, Vector((1, 0, 0)), lados=16)
VISORES.append((Vector((0.25, Y_COL, Z_RET)), Vector((0.35, Y_COL, Z_RET))))

# reservatório de expansão (oeste)
RV = Vector((-0.78, 0, 0))
bm = B('reservatorio', 'amarelo', True)
cil(bm, RV + Vector((0, 0, 0.47)), 0.09, 0.76, lados=28)
bm = B('reservatorio_aros', 'ferro', True)
for z in (0.12, 0.47, 0.84):
    cil(bm, RV + Vector((0, 0, z)), 0.096, 0.025, lados=28)
cil(bm, RV + Vector((0, 0, Z0 + 0.012)), 0.12, 0.024, lados=28)
cil(B('reservatorio_vidro', 'refrigerante'), RV + Vector((-0.088, 0, 0.42)), 0.012, 0.5, lados=12)     # régua de nível
for z in (0.16, 0.68):
    caixa(B('reservatorio_aros', 'ferro'), RV + Vector((-0.09, 0, z)), (0.02, 0.03, 0.02))
cil(B('valvula', 'ferro', True), RV + Vector((0.03, 0.04, 0.87)), 0.025, 0.04, lados=12)              # tampa de enchimento
# bomba (leste, embaixo do radiador)
PB = Vector((LAT_HEADER[0], 0, 0))
XR0, XR1 = 0.72, 0.805           # radiador (x)
bm = B('bomba', 'amarelo', True)
cil(bm, PB + Vector((0, 0, 0.16)), 0.09, 0.14, lados=24)                  # caracol
cil(B('bomba_motor', 'grafite', True), PB + Vector((0, 0, 0.33)), 0.066, 0.2, lados=20)
for k in range(5):
    cil(B('bomba_aletas', 'ferro', True), PB + Vector((0, 0, 0.26 + k * 0.035)), 0.078, 0.008, lados=20)
caixa(B('bomba_motor', 'grafite'), PB + Vector((-0.07, 0, 0.36)), (0.05, 0.06, 0.07))                # caixa de ligação
cil(B('flanges', 'ferro', True), PB + Vector((0, 0, 0.24)), 0.1, 0.02, lados=24)
cano(B('canos', 'casco', True), B('flanges', 'ferro', True), [PB + Vector((0.08, 0, 0.15)), Vector((XR0, 0, 0.15))], 0.024)
for sy in (-1, 1):
    tubo(B('canos', 'casco', True), PB + Vector((0, sy * 0.05, Z_ENT)), PB + Vector((0, sy * 0.09, Z_ENT)), 0.024, 16)
# radiador com ventoinha (leste)
bm = B('radiador_tanques', 'casco')
caixa_de(bm, (XR0, -0.185, 0.1), (XR1, 0.185, 0.2))
caixa_de(bm, (XR0, -0.185, 0.92), (XR1, 0.185, 1.02))
bm = B('radiador_quadro', 'amarelo')
for s in (-1, 1):
    caixa_de(bm, (XR0 - 0.005, s * 0.19 - 0.014, Z0), (XR1 + 0.005, s * 0.19 + 0.014, 1.03))
bm = B('radiador_aletas', 'aco')
k = 0
for k in range(30):
    y = -0.17 + k * 0.0117
    caixa_de(bm, (XR0 + 0.01, y - 0.0018, 0.2), (XR1 - 0.01, y + 0.0018, 0.92))
for z in (0.4, 0.7):
    caixa_de(B('radiador_quadro', 'amarelo'), (XR1 - 0.004, -0.18, z - 0.01), (XR1 + 0.004, 0.18, z + 0.01))
cil(B('valvula', 'ferro', True), Vector((0.75, 0.12, 1.05)), 0.02, 0.06, lados=12)                    # respiro de vapor
FAN = Vector((0.858, 0, 0.56))
bm = B('fan_anel', 'grafite', True)
bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.17, radius2=0.17, depth=0.1,
                      matrix=Matrix.Translation(FAN) @ Vector((1, 0, 0)).to_track_quat('Z', 'Y').to_matrix().to_4x4())
toro(bm, FAN + Vector((0.05, 0, 0)), 0.17, 0.008, 48, 8, Matrix.Rotation(PI / 2, 3, 'Y'))
toro(bm, FAN + Vector((-0.05, 0, 0)), 0.17, 0.008, 48, 8, Matrix.Rotation(PI / 2, 3, 'Y'))
for s in (-1, 1):
    for t in (-1, 1):
        viga(B('fan_suporte', 'ferro'), FAN + Vector((-0.05, s * 0.12, t * 0.12)), Vector((XR1, s * 0.15, FAN.z + t * 0.15)), 0.016)
bm = B('fan_grade', 'aco')
for r in (0.05, 0.1, 0.15):
    toro(bm, FAN + Vector((0.065, 0, 0)), r, 0.0035, 40, 6, Matrix.Rotation(PI / 2, 3, 'Y'))
for k in range(6):
    a = k * PI / 6
    d = Vector((0, math.cos(a), math.sin(a)))
    tubo(bm, FAN + Vector((0.065, 0, 0)) - d * 0.17, FAN + Vector((0.065, 0, 0)) + d * 0.17, 0.003, 6)
cil(bm, FAN + Vector((0.065, 0, 0)), 0.03, 0.01, Vector((1, 0, 0)), lados=16)
fan = bpy.data.objects.new('ventoinha', None)
sc.collection.objects.link(fan)
fan.location = FAN
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.04, 0.05, Vector((1, 0, 0)), lados=16)
for k in range(7):
    a = k * 2 * PI / 7
    R = Matrix.Rotation(a, 3, 'X')
    caixa(bm, R @ Vector((0, 0, 0.1)), (0.008, 0.07, 0.12), R @ Matrix.Rotation(0.45, 3, 'Z'))
obj('ventoinha_pas', bm, 'grafite', fan)

# ------------------------------------------------------------------ cabos e isoladores
def isolador(bm_p, bm_a, base, z0, z1, rd, n):
    """Pilha de discos de porcelana sobre núcleo, com grampo de cobre no topo."""
    cil(bm_p, base + Vector((0, 0, (z0 + z1) / 2)), rd * 0.45, z1 - z0, lados=16)
    for k in range(n):
        z = z0 + 0.02 + k * (z1 - z0 - 0.04) / (n - 1)
        cil(bm_p, base + Vector((0, 0, z)), rd, 0.014, lados=20)
        cil(bm_p, base + Vector((0, 0, z - 0.009)), rd * 0.8, 0.006, lados=20)
    cil(bm_a, base + Vector((0, 0, z1 + 0.025)), rd * 0.55, 0.05, lados=14)
    cil(bm_a, base + Vector((0, 0, z1 + 0.055)), rd * 0.75, 0.014, lados=6)
    return base + Vector((0, 0, z1 + 0.04))


# isoladores nos cantos: polo − de cada célula
for C in CELS:
    sx, sy = (1 if C.x > 0 else -1), (1 if C.y > 0 else -1)
    diag = Vector((sx, sy, 0)).normalized()
    IB = Vector((sx * 0.85, sy * 0.85, 0))
    caixa(B('iso_base', 'ferro'), IB + Vector((0, 0, Z0 + 0.01)), (0.13, 0.13, 0.02))
    for a in range(4):
        q = IB + Vector((math.cos(PI / 4 + a * PI / 2), math.sin(PI / 4 + a * PI / 2), 0)) * 0.075
        cil(B('parafusos', 'aco'), q + Vector((0, 0, Z0 + 0.026)), 0.009, 0.014, lados=6)
    cil(B('iso_poste', 'amarelo', True), IB + Vector((0, 0, 0.21)), 0.032, 0.24, lados=16)
    topo_i = isolador(B('porcelana', 'porcelana', True), B('iso_grampo', 'cobre', True), IB, 0.33, 0.7, 0.058, 7)
    pt = C + diag * 0.12 + Vector((0, 0, Z_BAR + 0.05))
    lat = Vector((-diag.y, diag.x, 0))
    pts = bezier(pt, pt + Vector((0, 0, 0.22)), topo_i + Vector((0, 0, 0.45)) - diag * 0.05, topo_i + Vector((0, 0, 0.02)), 14)
    feixe(B('cabos', 'cabo', True), B('abracadeiras', 'aco', True), pts, lat, n=2, r=0.016, passo=5)
    # rede: do grampo desce por fora da pilha e entra no eletroduto da laje
    po = IB + diag * 0.1
    pts = bezier(topo_i + diag * 0.03, topo_i + diag * 0.1 + Vector((0, 0, 0.0)), po + Vector((0, 0, 0.5)), po + Vector((0, 0, Z0 + 0.06)), 12)
    mangueira(B('cabos', 'cabo', True), pts, 0.018)
    cil(B('eletroduto', 'ferro', True), po + Vector((0, 0, Z0 + 0.04)), 0.03, 0.08, lados=14)
    for k in range(3):                                                     # queimado no chão perto do isolador
        mancha(B('chamusco', 'chamusco'), (IB.x + random.uniform(-0.12, 0.12), IB.y + random.uniform(-0.12, 0.12)),
               random.uniform(0.03, 0.07), Z0 + 0.001)

# cavalete de entrada da rede (sul) → caixa de junção da coluna
YS = -0.86
bm = B('cavalete', 'amarelo')
for sx in (-1, 1):
    viga(bm, Vector((sx * 0.17, YS, Z0)), Vector((sx * 0.17, YS, 0.52)), 0.04)
    viga(bm, Vector((sx * 0.17, YS, 0.3)), Vector((sx * 0.06, YS, 0.48)), 0.025)
viga(B('cavalete_travessa', 'ferro'), Vector((-0.2, YS, 0.5)), Vector((0.2, YS, 0.5)), 0.05)
caixa(B('iso_base', 'ferro'), Vector((0, YS, Z0 + 0.01)), (0.42, 0.1, 0.02))
cil(B('eletroduto', 'ferro', True), Vector((0, -0.94, Z0 + 0.05)), 0.045, 0.1, lados=16)
for i, x in enumerate((-0.1, 0.0, 0.1)):
    base = Vector((x, YS, 0))
    tp = isolador(B('porcelana', 'porcelana', True), B('iso_grampo', 'cobre', True), base, 0.525, 0.73, 0.042, 5)
    # entrada: do eletroduto sobe até o borne embaixo da travessa
    pts = bezier(Vector((x * 0.3, -0.94, Z0 + 0.1)), Vector((x * 0.3, -0.94, 0.3)), Vector((x, -0.92, 0.35)), Vector((x, YS - 0.03, 0.475)), 8)
    mangueira(B('cabos', 'cabo', True), pts, 0.014)
    # saída: do grampo vai para o norte, desce no vão e corre baixo até a caixa da coluna
    pts = bezier(tp + Vector((0, 0.01, 0)), tp + Vector((0, 0.18, 0.12)), Vector((x * 0.6, -0.62, 0.12)), Vector((x * 0.5, -0.5, 0.115)), 10)
    pts += [Vector((x * 0.5, -0.5 + 0.07 * j, 0.115)) for j in range(1, 6)] + [Vector((x * 0.5, -0.12, 0.115))]
    mangueira(B('cabos', 'cabo', True), pts, 0.016)
    if i == 1:
        CABO_ENTRADA = pts
for y in (-0.42, -0.25):                                                   # abraçadeiras e calha no chão
    caixa(B('abracadeiras', 'aco'), Vector((0, y, 0.115)), (0.13, 0.03, 0.045))
    caixa(B('abracadeiras', 'ferro'), Vector((0, y, Z0 + 0.008)), (0.16, 0.05, 0.016))
for k in range(4):
    mancha(B('chamusco', 'chamusco'), (random.uniform(-0.2, 0.2), YS + random.uniform(-0.05, 0.1)), random.uniform(0.03, 0.06), Z0 + 0.001)

# sensor da IA (norte): caixa com olho e leds, cabo até a coluna
PS = Vector((0, 0.86, 0))
viga(B('sensor_poste', 'ferro'), PS + Vector((0, 0, Z0)), PS + Vector((0, 0, 0.36)), 0.045)
caixa(B('iso_base', 'ferro'), PS + Vector((0, 0, Z0 + 0.01)), (0.12, 0.12, 0.02))
caixa(B('sensor', 'grafite'), PS + Vector((0, -0.01, 0.46)), (0.2, 0.1, 0.2))
cil(B('sensor_lente', 'ferro', True), PS + Vector((0, -0.07, 0.48)), 0.04, 0.03, Vector((0, 1, 0)), lados=20)
cil(B('sensor_olho', 'olho'), PS + Vector((0, -0.086, 0.48)), 0.028, 0.004, Vector((0, 1, 0)), lados=20)
for k, m in enumerate(('led_verde', 'led_verde', 'led_ambar')):
    cil(B('led_' + m, m), PS + Vector((-0.06 + k * 0.06, -0.062, 0.4)), 0.008, 0.006, Vector((0, 1, 0)), lados=10)
pts = bezier(PS + Vector((0.05, -0.02, 0.36)), PS + Vector((0.05, -0.1, 0.2)), Vector((0.05, 0.5, 0.11)), Vector((0.05, 0.4, 0.11)), 8)
pts += [Vector((0.05, 0.4 - 0.07 * j, 0.11)) for j in range(1, 4)] + [Vector((0.05, 0.12, 0.11))]
mangueira(B('cabos', 'cabo', True), pts, 0.012)

# pó e sujeira na laje
for k in range(14):
    x, y = random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95)
    if max(abs(abs(x) - 0.47), abs(abs(y) - 0.47)) < 0.3:
        continue
    mancha(B('po', 'po'), (x, y), random.uniform(0.05, 0.12), Z0 + 0.0008)

# ------------------------------------------------------------------ objetos estáticos
for (nome, mat, liso), bm in BMS.items():
    o = obj(nome, bm, mat)
    if liso:
        suavizar(o)

# ------------------------------------------------------------------ partículas animadas
def bolinha(nome, mat, r, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    return obj(nome, bm, mat)


contas_barra = [(bolinha('fluxo', 'fluxo', 0.012), i, k) for i in range(4) for k in range(3)]
contas_cabo = [bolinha('fluxo', 'fluxo', 0.011) for k in range(5)]
contas_feixe = [bolinha('fluxo', 'fluxo', 0.014) for k in range(3)]
bolhas = [(bolinha('bolha', 'bolha', 0.006, 0), iv, k) for iv in range(len(VISORES)) for k in range(3)]
gases = []
for iv in range(4):
    for k in range(3):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        gases.append((obj('gas', bm, 'gas'), iv, k))
vapores = []
for k in range(3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))


def ao_longo(pts, u):
    """Ponto a fração u do comprimento de uma polilinha."""
    L = [(b - a).length for a, b in zip(pts, pts[1:])]
    s = u * sum(L)
    for (a, b), l in zip(zip(pts, pts[1:]), L):
        if s <= l:
            return a.lerp(b, s / l if l else 0)
        s -= l
    return pts[-1]


# ------------------------------------------------------------------ animação (laço de 4 s)
def nivel(fr):
    return 0.55 - 0.4 * math.cos(2 * PI * fr)                             # 0,15 (vazio) → 0,95 (cheio) → 0,15


carga_bsdf = base3d.M['carga'].node_tree.nodes['Principled BSDF']
cristal_bsdf = base3d.M['cristal'].node_tree.nodes['Principled BSDF']
campo_forca = base3d.M['campo'].node_tree.nodes['forca'].inputs[1]
feixe_forca = base3d.M['feixe_luz'].node_tree.nodes['forca'].inputs[1]
CAB_PTS = [p + Vector((0, 0, 0.018)) for p in CABO_ENTRADA]
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    lv = nivel(fr)
    fluxo = math.sin(2 * PI * fr)                                          # > 0 carregando, < 0 descarregando
    carregando = fluxo > 0.08
    # faixas de carga: altura = nível; cor do âmbar (vazio) ao violeta (cheio)
    for fx in janelas:
        fx.scale = (1, 1, max(0.02, lv))
        fx.keyframe_insert('scale', frame=q)
    t = min(1.0, max(0.0, (lv - 0.27) / 0.08))                            # âmbar só quando quase vazio
    cor = [AMBAR[i] * (1 - t) + (0.42, 0.1, 1.0)[i] * t for i in range(3)] + [1]
    carga_bsdf.inputs['Emission Color'].default_value = cor
    carga_bsdf.inputs['Emission Color'].keyframe_insert('default_value', frame=q)
    carga_bsdf.inputs['Base Color'].default_value = cor
    carga_bsdf.inputs['Base Color'].keyframe_insert('default_value', frame=q)
    # cristal: gira, flutua, brilho cresce com a carga e tremula enquanto carrega
    trem = (0.25 * math.sin(2 * PI * 13 * fr) * math.sin(2 * PI * 7 * fr + 1)) if carregando else 0.0
    cristal.location = CC + Vector((0, 0, 0.018 * math.sin(2 * PI * 2 * fr)))
    cristal.rotation_euler = (0.05 * math.sin(2 * PI * fr), 0.04 * math.cos(2 * PI * fr), 2 * PI * fr)
    cristal.keyframe_insert('location', frame=q)
    cristal.keyframe_insert('rotation_euler', frame=q)
    cristal_bsdf.inputs['Emission Strength'].default_value = 0.5 + 1.6 * lv + 0.8 * trem
    cristal_bsdf.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)
    luz_c.energy = 12 + 45 * lv + 20 * trem
    luz_c.keyframe_insert('energy', frame=q)
    campo_forca.default_value = 3.0 + 6.0 * lv
    campo_forca.keyframe_insert('default_value', frame=q)
    feixe_forca.default_value = 2.0 + 7.0 * abs(fluxo)
    feixe_forca.keyframe_insert('default_value', frame=q)
    for k, o in enumerate(aneis_campo):
        s = 1 if k == 0 else -1
        o.rotation_quaternion = (Quaternion((0, 0, 1), s * 2 * PI * fr * (k + 1)) @ Quaternion((1, 0, 0), math.radians(62 + 18 * k))
                                 @ Quaternion((0, 0, 1), 4 * PI * fr))
        o.scale = [1 + 0.04 * lv * math.sin(2 * PI * 4 * fr + k)] * 3
        o.keyframe_insert('rotation_quaternion', frame=q)
        o.keyframe_insert('scale', frame=q)
    # arcos garra → cristal: só carregando; piscam trocando de forma
    for o, ig, v in arcos:
        vis = carregando and ((q + ig * 2) % 5) < 3 and ((q // 2 + ig) % 3) == v
        o.hide_render = o.hide_viewport = not vis
        o.keyframe_insert('hide_render', frame=q)
        o.keyframe_insert('hide_viewport', frame=q)
    # terminal frouxo: arco e faíscas enquanto carrega
    for v, o in enumerate(arcos_t):
        vis = carregando and (q % 4) in ((0, 1) if v == 0 else (2,))
        o.hide_render = o.hide_viewport = not vis
        o.keyframe_insert('hide_render', frame=q)
        o.keyframe_insert('hide_viewport', frame=q)
    luz_t.energy = (6.0 if carregando and (q % 4) != 3 else 0.0)
    luz_t.keyframe_insert('energy', frame=q)
    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + fr * 6) % 1.0) * 0.3
        v = vel_f[k]
        p = P_FROUXO + Vector((0.04, -0.01, 0)) + v * tt + Vector((0, 0, -4.9 * tt * tt))
        viva = carregando and p.z > Z0 + 0.01
        o.location = p
        o.scale = [max(0.001, (1 - tt / 0.3)) if viva else 0.001] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    # energia fluindo: rede → coluna (cabo), prato → cristal (feixe), anel → células (barramentos); invertido ao descarregar
    forca_f = abs(fluxo)
    for o, i, k in contas_barra:
        u = (k / 3 + fr * 3 * (1 if fluxo > 0 else -1)) % 1.0
        a, b = BARRAS[i]
        o.location = a.lerp(b, u)
        o.scale = [max(0.001, forca_f)] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for k, o in enumerate(contas_cabo):
        u = (k / len(contas_cabo) + fr * 2 * (1 if fluxo > 0 else -1)) % 1.0
        o.location = ao_longo(CAB_PTS, u)
        o.scale = [max(0.001, forca_f)] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for k, o in enumerate(contas_feixe):
        u = (k / 3 + fr * 4 * (1 if fluxo > 0 else -1)) % 1.0
        o.location = Vector((0, 0, 1.12)).lerp(CC - Vector((0, 0, 0.16)), u)
        o.scale = [max(0.001, forca_f)] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    # ventoinha: 10 voltas no laço
    fan.rotation_euler = (2 * PI * 10 * fr, 0, 0)
    fan.keyframe_insert('rotation_euler', frame=q)
    # bolhas subindo nos visores de refrigerante
    for o, iv, k in bolhas:
        a, b = VISORES[iv]
        u = (k / 3 + fr * 3 + iv * 0.17) % 1.0
        o.location = a.lerp(b, u) + Vector((0.006 * math.sin(k * 3 + u * 9), 0.006 * math.cos(k * 2 + u * 7), 0))
        o.keyframe_insert('location', frame=q)
    # gás saindo das válvulas enquanto carrega (mais forte perto do cheio)
    for o, iv, k in gases:
        pt, d = SAIDAS_GAS[iv]
        u = (k / 3 + fr * 3 + iv * 0.29) % 1.0
        forca = max(0.0, fluxo) * (0.4 + 0.8 * lv)
        o.location = pt + d * (0.1 * u) + Vector((0.03 * u, 0.02 * u, 0.35 * u))
        o.scale = [max(0.02, (0.025 + 0.11 * u) * forca)] * 3
        o.rotation_euler = (k, u * 2, iv)
        o.hide_render = o.hide_viewport = forca < 0.15
        for c in ('location', 'scale', 'rotation_euler', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
    # vapor do respiro do radiador (sempre, fraco)
    for k, o in enumerate(vapores):
        u = (k / 3 + fr * 2) % 1.0
        o.location = Vector((0.75 + 0.05 * u, 0.12 + 0.02 * math.sin(k), 1.08 + 0.4 * u))
        o.scale = [0.03 + 0.1 * u] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
for o in list(sc.objects) + [luz_c, luz_t] + [base3d.M[m] for m in ('carga', 'cristal', 'campo', 'feixe_luz')]:
    ad = getattr(o, 'animation_data', None) or getattr(getattr(o, 'node_tree', None), 'animation_data', None)
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


ALVO = (0.0, 0.0, 0.72)
FR_FOTO = int(QUADROS * 0.3) + 1                                          # carregando, nível ~0,67, arcos acesos
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1100
    sc.frame_set(FR_FOTO)
    for i, (ang, alt) in enumerate(((300, 2.0), (210, 2.2), (120, 2.4), (30, 1.8))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.2, math.sin(a) * 4.2, alt)), ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'acumulador_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((1.35, -1.25, 1.95), (0.1, -0.08, 1.25), 34)                # cristal, garras, barramentos, terminal frouxo
        sc.render.filepath = os.path.join(AQUI, 'acumulador_perto.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':                                                       # câmera livre: -- teste x y z ax ay az lente fr
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'acumulador_teste.png')
    bpy.ops.render.render(write_still=True)
print('ACUMULADOR ok')
