"""Estudo isolado (fora do jogo): montadora 3×3, entrada pelo sul (meio) e saída pelo norte (meio), como no jogo.
Gabinete industrial (pórtico de perfis, chapas de rodapé, gaiola de proteção, janelas de inspeção); esteira interna
de sul a norte passando por três estações: braço pega-e-põe (pega um componente da mesa giratória e põe na peça),
prensa hidráulica (desce, estampa a peça e solta vapor) e braço de solda (cordão com faíscas). Unidade hidráulica
alimenta a prensa por canos com flanges; compressor alimenta os braços por mangueiras; cabos em calha no teto;
painel de controle e giroflex com luzes piscando. Óleo, cavaco de metal, listras de perigo.
Uso: blender -b --python estudo_montadora.py -- foto | video"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço; a esteira anda 1 m = 2 peças (o ciclo das estações é de 2 s)
random.seed(21)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def curva(bm, p, r, lados=14):
    """Cotovelo arredondado (esfera do raio do tubo)."""
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r):
    """Cano rígido por pontos: trechos retos, cotovelos redondos e flanges perto de cada curva."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        for c in (a + u * 0.05, b - u * 0.05):
            tubo(bf, c - u * 0.008, c + u * 0.008, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def luz_mat(nome, cor):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = 6.0
    return m


def vidro_mat():
    m = bpy.data.materials.new('Vidro')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.82, 0.78, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['Alpha'].default_value = 0.35                                # vidro fino de inspeção: deixa ver dentro
    b.inputs['IOR'].default_value = 1.45
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.8),
    'laranja': mats.material('Laranja', (0.62, 0.22, 0.04), 0, 0.45, desgaste=0.8, sujeira=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'cinza': mats.material('Cinza', (0.22, 0.23, 0.24), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'peca': mats.material('Peça', (0.5, 0.5, 0.52), 1.0, 0.35, pintura=False, ferrugem=0.2, sujeira=0.4, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'cordao': mats.material('Cordão', (0.16, 0.12, 0.1), 1.0, 0.5, pintura=False, sujeira=0.5, ferrugem=0.3),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'vidro': vidro_mat(),
    'listras': base3d.listras_mat(),
    'faisca': luz_mat('Faísca', (1.0, 0.75, 0.35)),
    'verde': luz_mat('Luz verde', (0.15, 1.0, 0.25)),
    'vermelho': luz_mat('Luz vermelha', (1.0, 0.08, 0.05)),
    'ambar': luz_mat('Luz âmbar', (1.0, 0.5, 0.05)),
    'vapor': base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 4.0, 0.7, 1.6),
})

H = 1.75                     # altura do pórtico
ZB = 0.62                    # topo da esteira interna
V = 0.25                     # m/s
DUR = QUADROS / FPS
Y_POE, Y_PRENSA, Y_SOLDA = -0.6, 0.0, 0.6

# ------------------------------------------------------------------ laje, rodapé, pórtico, gaiola, janelas
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()                                                          # faixas de perigo em ladrilho no piso
for x0, x1 in ((-0.42, -0.36), (0.36, 0.42)):
    caixa_de(bm, (x0, -1.48, 0.08), (x1, 1.48, 0.082))
for y in (-0.32, 0.32):
    caixa_de(bm, (-0.6, y - 0.03, 0.08), (-0.42, y + 0.03, 0.082))
    caixa_de(bm, (0.42, y - 0.03, 0.08), (0.6, y + 0.03, 0.082))
obj('faixas_piso', bm, 'listras')
POSTES = [(x, y) for x in (-1.42, 1.42) for y in (-1.42, 0.0, 1.42)] + [(x, y) for x in (-0.45, 0.45) for y in (-1.42, 1.42)]
bm = bmesh.new()
for x, y in POSTES:
    caixa_de(bm, (x - 0.04, y - 0.04, 0.08), (x + 0.04, y + 0.04, H))
    caixa_de(bm, (x - 0.07, y - 0.07, 0.08), (x + 0.07, y + 0.07, 0.1))   # sapata do poste
for y in (-1.42, 1.42):                                                   # vigas do teto
    caixa_de(bm, (-1.42, y - 0.04, H - 0.08), (1.42, y + 0.04, H))
for x in (-1.42, 1.42):
    caixa_de(bm, (x - 0.04, -1.42, H - 0.08), (x + 0.04, 1.42, H))
for x in (-0.9, 0.9):                                                     # vigas das calhas de cabo
    caixa_de(bm, (x - 0.03, -1.42, H - 0.07), (x + 0.03, 1.42, H - 0.01))
for y in (-1.42, 1.42):                                                   # verga sobre a passagem da esteira
    caixa_de(bm, (-0.45, y - 0.05, 1.0), (0.45, y + 0.05, 1.08))
obj('portico', bm, 'amarelo')
bm = bmesh.new()
for y in (-1.42, 1.42):
    caixa_de(bm, (-0.45, y - 0.051, 1.0), (0.45, y + 0.051, 1.08))
obj('verga_listras', bm, 'listras')
bm = bmesh.new()                                                          # chapas de rodapé
for x in (-1.42, 1.42):
    caixa_de(bm, (x - 0.012, -1.38, 0.08), (x + 0.012, 1.38, 0.45))
for y in (-1.42, 1.42):
    for x0, x1 in ((-1.38, -0.49), (0.49, 1.38)):
        caixa_de(bm, (x0, y - 0.012, 0.08), (x1, y + 0.012, 0.45))
obj('rodape', bm, 'cinza')
bm = bmesh.new()                                                          # gaiola de proteção (leste e oeste)
for x in (-1.42, 1.42):
    for y0, y1 in ((-1.38, -0.04), (0.04, 1.38)):
        n = int((y1 - y0) / 0.09)
        for i in range(n + 1):
            y = y0 + (y1 - y0) * i / n
            caixa_de(bm, (x - 0.006, y - 0.006, 0.45), (x + 0.006, y + 0.006, H - 0.08))
        for z in (0.45, 0.85, 1.25, H - 0.09):
            caixa_de(bm, (x - 0.012, y0, z - 0.012), (x + 0.012, y1, z + 0.012))
obj('gaiola', bm, 'grafite')
bm, bv = bmesh.new(), bmesh.new()                                         # janelas de inspeção (norte e sul)
for y in (-1.42, 1.42):
    for x0, x1 in ((-1.38, -0.49), (0.49, 1.38)):
        caixa_de(bv, (x0, y - 0.004, 0.47), (x1, y + 0.004, H - 0.1))
        for a, b in (((x0, y - 0.02, 0.45), (x1, y + 0.02, 0.49)), ((x0, y - 0.02, H - 0.12), (x1, y + 0.02, H - 0.08)),
                     ((x0, y - 0.02, 0.45), (x0 + 0.04, y + 0.02, H - 0.08)), ((x1 - 0.04, y - 0.02, 0.45), (x1, y + 0.02, H - 0.08)),
                     (((x0 + x1) / 2 - 0.015, y - 0.02, 0.45), ((x0 + x1) / 2 + 0.015, y + 0.02, H - 0.08))):
            caixa_de(bm, a, b)
obj('janelas_moldura', bm, 'grafite')
obj('janelas_vidro', bv, 'vidro')

# ------------------------------------------------------------------ esteira interna (sul → norte)
bm = bmesh.new()
for x in (-0.28, 0.28):
    caixa_de(bm, (x - 0.02, -1.48, ZB - 0.14), (x + 0.02, 1.48, ZB - 0.01))       # longarinas
    for y in (-1.3, -0.7, 0.3, 0.9, 1.3):
        caixa_de(bm, (x - 0.025, y - 0.025, 0.08), (x + 0.025, y + 0.025, ZB - 0.14))   # pés
obj('esteira_estrutura', bm, 'grafite')
bm = bmesh.new()
caixa_de(bm, (-0.25, -1.46, ZB - 0.02), (0.25, 1.46, ZB))                  # lona
for y in (-1.44, 1.44):
    cil(bm, Vector((0, y, ZB - 0.045)), 0.04, 0.5, Vector((1, 0, 0)), lados=16)    # tambores
obj('esteira_lona', bm, 'borracha')
taliscas = []
for i in range(12):
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.0015), (0.48, 0.016, 0.003))
    taliscas.append(obj('talisca', bm, 'grafite'))


def y_esteira(s):
    return -1.5 + s % 3.0


# peças na esteira: bloco bruto → recebe componente → é estampado → recebe cordão de solda
pecas = []
for k in range(6):
    raiz = bpy.data.objects.new('peca', None)
    sc.collection.objects.link(raiz)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.04), (0.18, 0.16, 0.08))
    corpo = obj('peca_corpo', bm, 'peca', raiz)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.0)), 0.035, 0.05, lados=12)
    comp = obj('peca_componente', bm, 'cobre', raiz)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0), (0.17, 0.014, 0.012))
    cordao = obj('peca_cordao', bm, 'cordao', raiz)
    pecas.append((raiz, corpo, comp, cordao))

# ------------------------------------------------------------------ prensa hidráulica (estação do meio)
bm = bmesh.new()
for x in (-0.42, 0.42):
    caixa_de(bm, (x - 0.06, -0.08, 0.08), (x + 0.06, 0.08, 1.62))          # colunas
    caixa_de(bm, (x - 0.1, -0.12, 0.08), (x + 0.1, 0.12, 0.14))
caixa_de(bm, (-0.5, -0.12, 1.5), (0.5, 0.12, 1.66))                       # cabeçote
caixa_de(bm, (-0.36, -0.1, ZB - 0.2), (0.36, 0.1, ZB - 0.15))             # mesa inferior (sob a lona)
obj('prensa_quadro', bm, 'laranja')
bm = bmesh.new()
for x in (-0.42, 0.42):
    for z in (0.4, 0.9, 1.4):
        for y in (-0.085, 0.085):
            cil(bm, Vector((x, y, z)), 0.012, 0.008, Vector((0, 1, 0)), lados=6)   # parafusos das colunas
for x in (-0.3, 0.3):
    cil(bm, Vector((x, 0, 1.12)), 0.022, 0.75, lados=12)                  # guias cromadas
obj('prensa_parafusos', bm, 'cromo')
bm = bmesh.new()
cil(bm, Vector((0, 0, 1.85)), 0.11, 0.38, lados=24)                       # cilindro hidráulico
cil(bm, Vector((0, 0, 2.05)), 0.13, 0.04, lados=24)
cil(bm, Vector((0, 0, 1.67)), 0.13, 0.03, lados=24)
obj('prensa_cilindro', bm, 'grafite')
suavizar(sc.objects['prensa_cilindro'])
martelo = bpy.data.objects.new('martelo', None)
sc.collection.objects.link(martelo)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.35)), 0.045, 0.7, lados=16)                       # haste
obj('martelo_haste', bm, 'cromo', martelo)
bm = bmesh.new()
caixa(bm, (0, 0, 0.03), (0.66, 0.16, 0.06))                               # placa do martelo (corre nas guias)
for x in (-0.3, 0.3):
    cil(bm, Vector((x, 0, 0.03)), 0.04, 0.08, lados=12)                   # buchas nas guias
caixa(bm, (0, 0, -0.03), (0.22, 0.14, 0.06))                              # matriz
obj('martelo_placa', bm, 'aco', martelo)
bm = bmesh.new()
caixa(bm, (0, -0.081, 0.03), (0.6, 0.004, 0.045))
obj('martelo_listras', bm, 'listras', martelo)
Z_ABERTA, Z_FECHADA = 1.02, ZB + 0.08 * 0.62 + 0.06

# ------------------------------------------------------------------ braços (mesmo desenho do braço aprovado, menor)
L1, L2, G = 0.5, 0.45, 0.16


def braco(nome, pos, solda=False):
    base_o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(base_o)
    base_o.location = pos
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.03)), 0.2, 0.06, lados=8)
    cil(bm, Vector((0, 0, 0.17)), 0.11, 0.22, lados=16)
    for k in range(6):
        a = k * PI / 3
        cil(bm, Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 0.065)), 0.014, 0.012, lados=6)
    caixa(bm, (0.15, -0.09, 0.14), (0.07, 0.06, 0.08))                    # caixa de ligação
    obj(nome + '_base', bm, 'grafite', base_o)
    giro = bpy.data.objects.new(nome + '_giro', None)
    sc.collection.objects.link(giro)
    giro.parent = base_o
    giro.location = (0, 0, 0.29)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.06), (0.24, 0.24, 0.12))
    for x in (-0.085, 0.085):
        caixa(bm, (x, 0, 0.17), (0.035, 0.1, 0.12))                       # mancais do ombro
    cil(bm, Vector((-0.17, 0, 0.07)), 0.05, 0.1, Vector((1, 0, 0)), lados=12)   # motor do giro
    obj(nome + '_giro_corpo', bm, 'amarelo', giro)
    ombro = bpy.data.objects.new(nome + '_ombro', None)
    sc.collection.objects.link(ombro)
    ombro.parent = giro
    ombro.location = (0, 0, 0.2)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.045, 0.13, Vector((1, 0, 0)), lados=14)
    for x in (-0.04, 0.04):
        caixa_de(bm, (x - 0.012, 0.0, -0.025), (x + 0.012, L1, 0.025))   # longarinas
    for k in range(1, 5):
        caixa(bm, (0, L1 * k / 5, 0), (0.07, 0.014, 0.014))               # travessas
    cil(bm, Vector((0, L1, 0)), 0.05, 0.12, Vector((1, 0, 0)), lados=14)   # cotovelo
    obj(nome + '_braco1', bm, 'amarelo', ombro)
    bm = bmesh.new()                                                      # cabos ao longo do braço 1
    mangueira(bm, bezier((-0.07, -0.02, 0.03), (-0.08, L1 * 0.3, 0.06), (-0.08, L1 * 0.7, 0.06), (-0.06, L1, 0.03), 8), 0.01)
    suavizar(obj(nome + '_cabos1', bm, 'borracha', ombro))
    cotovelo = bpy.data.objects.new(nome + '_cotovelo', None)
    sc.collection.objects.link(cotovelo)
    cotovelo.parent = ombro
    cotovelo.location = (0, L1, 0)
    bm = bmesh.new()
    tubo(bm, (0, 0, 0), (0, L2, 0), 0.03, 14)
    for y in (0.15, 0.3):
        cil(bm, Vector((0, y, 0)), 0.036, 0.02, Vector((0, 1, 0)), lados=14)
    suavizar(obj(nome + '_braco2', bm, 'laranja' if solda else 'amarelo', cotovelo))
    bm = bmesh.new()
    mangueira(bm, bezier((0.04, -0.03, 0.03), (0.06, L2 * 0.3, 0.05), (0.05, L2 * 0.7, 0.05), (0.03, L2, 0.03), 8), 0.009)
    suavizar(obj(nome + '_cabos2', bm, 'borracha', cotovelo))
    punho = bpy.data.objects.new(nome + '_punho', None)
    sc.collection.objects.link(punho)
    punho.parent = cotovelo
    punho.location = (0, L2, 0)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.035, 0.08, Vector((1, 0, 0)), lados=14)
    cil(bm, Vector((0, 0, -0.04)), 0.03, 0.05, lados=14)
    dedos = []
    if solda:                                                             # tocha de solda: corpo curvo e bico de cobre
        tubo(bm, (0, 0, -0.06), (0, 0.03, -0.12), 0.022, 12)
        curva(bm, (0, 0.03, -0.12), 0.022, 12)
        obj(nome + '_tocha', bm, 'grafite', punho)
        bm = bmesh.new()
        tubo(bm, (0, 0.03, -0.12), (0, 0.03, -G + 0.005), 0.016, 12)
        suavizar(obj(nome + '_bico', bm, 'cobre', punho))
    else:                                                                 # garra pneumática de dois dedos
        caixa(bm, (0, 0, -0.08), (0.12, 0.06, 0.04))
        cil(bm, Vector((0, 0.04, -0.08)), 0.014, 0.1, Vector((1, 0, 0)), lados=10)
        obj(nome + '_garra', bm, 'grafite', punho)
        for sx in (-1, 1):
            d = bpy.data.objects.new(nome + '_dedo', None)
            sc.collection.objects.link(d)
            d.parent = punho
            bm = bmesh.new()
            caixa(bm, (0, 0, -0.12), (0.016, 0.04, 0.07))
            caixa(bm, (-sx * 0.008, 0, -0.155), (0.016, 0.036, 0.012))
            obj(nome + '_dedo_aco', bm, 'aco', d)
            dedos.append((d, sx))
    # pistão do ombro: camisa presa no giro, haste presa no braço 1 (orientados a cada quadro)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.11)), 0.026, 0.22, lados=14)
    camisa = suavizar(obj(nome + '_camisa', bm, 'grafite'))
    camisa.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.13)), 0.013, 0.26, lados=12)
    haste = suavizar(obj(nome + '_haste', bm, 'cromo'))
    haste.rotation_mode = 'QUATERNION'
    return {'base': base_o, 'giro': giro, 'ombro': ombro, 'cotovelo': cotovelo, 'punho': punho, 'dedos': dedos,
            'camisa': camisa, 'haste': haste}


BA = braco('braco_poe', Vector((-0.55, -1.02, 0.08)))
BS = braco('braco_solda', Vector((0.6, 0.18, 0.08)), solda=True)
ANCORA, PONTO_B1 = Vector((0, -0.12, 0.12)), Vector((0, 0.24, -0.03))    # no giro / no braço 1


def ik(b, ponta):
    """Põe o braço com a ponta da ferramenta em `ponta` (mundo): giro, ombro, cotovelo e punho nivelado."""
    pulso = Vector(ponta) + Vector((0, 0, G))
    bpy.context.view_layer.update()
    om = b['ombro'].matrix_world.translation if False else (b['base'].location + Vector((0, 0, 0.29 + 0.2)))
    d = pulso - om
    th = math.atan2(-d.x, d.y)
    r = math.hypot(d.x, d.y)
    h = d.z
    dist = min(math.hypot(r, h), L1 + L2 - 1e-4)
    c = (dist * dist - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    a2 = -math.acos(max(-1.0, min(1.0, c)))
    a1 = math.atan2(h, r) - math.atan2(L2 * math.sin(a2), L1 + L2 * math.cos(a2))
    b['giro'].rotation_euler = (0, 0, th)
    b['ombro'].rotation_euler = (a1, 0, 0)
    b['cotovelo'].rotation_euler = (a2, 0, 0)
    b['punho'].rotation_euler = (-(a1 + a2), 0, 0)
    bpy.context.view_layer.update()
    pa = b['giro'].matrix_world @ ANCORA
    pb = b['ombro'].matrix_world @ PONTO_B1
    b['camisa'].location = pa
    b['camisa'].rotation_quaternion = (pb - pa).to_track_quat('Z', 'Y')
    b['haste'].location = pb
    b['haste'].rotation_quaternion = (pa - pb).to_track_quat('Z', 'Y')


def chave(b, q):
    for k in ('giro', 'ombro', 'cotovelo', 'punho'):
        b[k].keyframe_insert('rotation_euler', frame=q)
    for k in ('camisa', 'haste'):
        b[k].keyframe_insert('location', frame=q)
        b[k].keyframe_insert('rotation_quaternion', frame=q)


# ------------------------------------------------------------------ mesa giratória (alimentador de componentes)
MESA = Vector((-1.0, -0.42, 0))
bm = bmesh.new()
cil(bm, MESA + Vector((0, 0, 0.27)), 0.07, 0.38, lados=16)                 # coluna
caixa(bm, MESA + Vector((0, 0, 0.1)), (0.3, 0.3, 0.04))
obj('mesa_base', bm, 'grafite')
mesa = bpy.data.objects.new('mesa', None)
sc.collection.objects.link(mesa)
mesa.location = MESA + Vector((0, 0, 0.48))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.0)), 0.24, 0.035, lados=32)
for k in range(6):
    a = k * PI / 3
    cil(bm, Vector((math.cos(a) * 0.17, math.sin(a) * 0.17, 0.02)), 0.045, 0.01, lados=12)   # ninhos
obj('mesa_prato', bm, 'aco', mesa)
bm = bmesh.new()
for k in range(6):
    a = k * PI / 3
    cil(bm, Vector((math.cos(a) * 0.17, math.sin(a) * 0.17, 0.05)), 0.035, 0.05, lados=12)
obj('mesa_componentes', bm, 'cobre', mesa)
bm = bmesh.new()
caixa(bm, MESA + Vector((0, -0.31, 0.3)), (0.04, 0.04, 0.44))             # torre de sinal do alimentador
obj('mesa_poste', bm, 'grafite')
comp_garra = None
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.035, 0.05, lados=12)
comp_garra = obj('componente_garra', bm, 'cobre')
PEGA = MESA + Vector((0.17 * math.cos(-PI / 3 + PI / 3), 0.0, 0)) + Vector((0, 0, 0))
PEGA = MESA + Vector((0.17, 0, 0.48 + 0.075))                             # ninho virado para o braço

# ------------------------------------------------------------------ unidade hidráulica (NE) e canos até a prensa
UH = Vector((1.05, 1.05, 0.08))
bm = bmesh.new()
caixa_de(bm, UH + Vector((-0.28, -0.22, 0)), UH + Vector((0.28, 0.22, 0.42)))   # tanque
obj('uh_tanque', bm, 'laranja')
bm = bmesh.new()
cil(bm, UH + Vector((0.0, 0.0, 0.55)), 0.1, 0.24, Vector((1, 0, 0)), lados=16)  # motor
for k in range(6):
    cil(bm, UH + Vector((-0.08 + k * 0.032, 0, 0.55)), 0.118, 0.008, Vector((1, 0, 0)), lados=16)
cil(bm, UH + Vector((-0.17, 0.0, 0.55)), 0.06, 0.1, Vector((1, 0, 0)), lados=14)   # bomba
caixa(bm, UH + Vector((0.0, 0.0, 0.44)), (0.3, 0.16, 0.04))
cil(bm, UH + Vector((0.18, -0.12, 0.47)), 0.035, 0.1, lados=12)           # bocal de enchimento
obj('uh_motor', bm, 'grafite')
bm = bmesh.new()
cil(bm, UH + Vector((-0.1, -0.225, 0.3)), 0.04, 0.012, Vector((0, -1, 0)), lados=20)   # manômetro
caixa(bm, UH + Vector((0.12, -0.222, 0.25)), (0.04, 0.006, 0.14))         # visor de nível
obj('uh_manometro', bm, 'cromo')
bm, bf = bmesh.new(), bmesh.new()
for k, zk in ((0, 1.95), (1, 1.8)):                                     # pressão (em cima) e retorno
    x = 1.22 + 0.07 * k
    cano(bm, bf, [Vector((x, 0.92, 0.5)), Vector((x, 0.92, zk)), Vector((x, 0.25, zk)), Vector((0.0, 0.25, zk)),
                  Vector((0.0, 0.1, zk))], 0.02)
suavizar(obj('canos_prensa', bm, 'aco'))
suavizar(obj('canos_flanges', bf, 'grafite'))

# ------------------------------------------------------------------ compressor (NO) e mangueiras até os braços
CP = Vector((-1.05, 1.05, 0.08))
bm = bmesh.new()
cil(bm, CP + Vector((0, 0, 0.2)), 0.16, 0.6, Vector((0, 1, 0)), lados=24)  # pulmão
for y in (-0.3, 0.3):
    curva(bm, CP + Vector((0, y, 0.2)), 0.16, 24)
obj('compressor_pulmao', bm, 'cinza')
suavizar(sc.objects['compressor_pulmao'])
bm = bmesh.new()
for y in (-0.22, 0.22):
    caixa(bm, CP + Vector((0, y, 0.03)), (0.24, 0.06, 0.06))              # berço
cil(bm, CP + Vector((0.0, 0.1, 0.45)), 0.07, 0.12, lados=16)              # cabeçote com aletas
for k in range(5):
    cil(bm, CP + Vector((0.0, 0.1, 0.4 + k * 0.025)), 0.09, 0.006, lados=16)
caixa(bm, CP + Vector((0.0, -0.15, 0.44)), (0.18, 0.14, 0.12))             # motor
caixa(bm, CP + Vector((0.11, -0.02, 0.45)), (0.02, 0.3, 0.12))            # protetor da correia
obj('compressor_cabeca', bm, 'grafite')
bm = bmesh.new()
mangueira(bm, bezier(CP + Vector((0.15, -0.3, 0.2)), CP + Vector((0.4, -0.8, 0.02)), Vector((-0.6, -0.4, 0.1)), BA['base'].location + Vector((-0.1, 0.12, 0.12)), 18), 0.014)
mangueira(bm, bezier(CP + Vector((0.15, 0.0, 0.25)), CP + Vector((0.9, -0.2, 0.02)), Vector((0.7, 0.9, 0.1)), BS['base'].location + Vector((0.05, 0.13, 0.12)), 18), 0.014)
suavizar(obj('mangueiras_ar', bm, 'borracha'))

# ------------------------------------------------------------------ calhas de cabo no teto e descidas até os braços
bm, bc = bmesh.new(), bmesh.new()
for x in (-0.9, 0.9):
    caixa_de(bm, (x - 0.08, -1.38, H - 0.13), (x + 0.08, 1.38, H - 0.12))  # fundo da calha
    for sx in (-1, 1):
        caixa_de(bm, (x + sx * 0.08 - 0.005, -1.38, H - 0.13), (x + sx * 0.08 + 0.005, 1.38, H - 0.07))
    for k in range(3):
        mangueira(bc, [Vector((x - 0.04 + k * 0.04, -1.36, H - 0.11)), Vector((x - 0.04 + k * 0.04, 1.36, H - 0.11))], 0.009)
for b, x in ((BA, -0.9), (BS, 0.9)):
    p = b['base'].location
    mangueira(bc, bezier((x, p.y, H - 0.12), (x, p.y, 1.1), (p.x + (0.25 if x < 0 else -0.25) * 0, p.y + 0.3, 0.7), p + Vector((0.1 if x < 0 else -0.12, 0.1, 0.2)), 16), 0.012)
obj('calhas', bm, 'grafite')
suavizar(obj('cabos', bc, 'borracha'))

# ------------------------------------------------------------------ painel de controle (sudoeste, por fora) e giroflex
PN = Vector((-1.2, -1.62, 0))
YP0 = -1.47                                                               # face do painel (dentro da laje)
bm = bmesh.new()
caixa_de(bm, (-1.3, YP0, 0.5), (-0.98, -1.445, 1.3))                     # caixa do painel presa no pórtico
caixa_de(bm, (-1.31, YP0 - 0.005, 1.3), (-0.97, -1.44, 1.32))
caixa_de(bm, (-1.16, YP0 + 0.005, 0.08), (-1.12, -1.445, 0.5))            # pé
obj('painel', bm, 'cinza')
bm = bmesh.new()
caixa_de(bm, (-1.26, YP0 - 0.004, 0.95), (-1.02, YP0, 1.22))             # tela
for k in range(3):
    cil(bm, Vector((-1.24 + k * 0.07, YP0 - 0.006, 0.78)), 0.02, 0.012, Vector((0, -1, 0)), lados=12)   # botões
caixa_de(bm, (-1.24, YP0 - 0.004, 0.56), (-1.04, YP0, 0.66))             # placa de identificação
mangueira(bm, bezier((-1.0, YP0 + 0.01, 1.32), (-0.96, YP0 + 0.01, 1.5), (-0.92, -1.42, 1.62), (-0.9, -1.38, H - 0.1), 8), 0.014)   # cabo até a calha
obj('painel_frente', bm, 'grafite')
bm = bmesh.new()
cil(bm, Vector((-1.06, YP0 - 0.01, 0.78)), 0.035, 0.02, Vector((0, -1, 0)), lados=16)   # botão de emergência
obj('painel_emergencia', bm, 'vermelho')
for i, nome in enumerate(('verde', 'ambar', 'vermelho')):
    bm = bmesh.new()
    cil(bm, Vector((-1.22 + i * 0.07, YP0 - 0.008, 0.88)), 0.02, 0.016, Vector((0, -1, 0)), lados=12)
    obj('painel_luz', bm, nome)
bm = bmesh.new()                                                          # giroflex sobre o cabeçote da prensa
cil(bm, Vector((0.35, 0.0, 1.7)), 0.05, 0.08, lados=16)
obj('giroflex', bm, 'ambar')
bm = bmesh.new()
cil(bm, Vector((0.35, 0.0, 1.66)), 0.06, 0.02, lados=16)
obj('giroflex_base', bm, 'grafite')
bm = bmesh.new()                                                          # torre de sinal na mesa giratória
for i, nome in enumerate(('verde', 'ambar', 'vermelho')):
    pass
for i, (nome, z) in enumerate((('verde', 0.56), ('ambar', 0.62), ('vermelho', 0.68))):
    bmm = bmesh.new()
    cil(bmm, MESA + Vector((0, -0.31, z)), 0.03, 0.05, lados=14)
    obj('sinal', bmm, nome)

# ------------------------------------------------------------------ luminárias internas (tubos de LED nas vigas)
bm, bl = bmesh.new(), bmesh.new()
for x in (-0.6, 0.6):
    caixa_de(bm, (x - 0.05, -1.0, H - 0.2), (x + 0.05, 1.0, H - 0.16))
    caixa_de(bl, (x - 0.035, -0.98, H - 0.205), (x + 0.035, 0.98, H - 0.2))
    for y in (-0.9, 0.9):
        caixa_de(bm, (x - 0.008, y - 0.008, H - 0.16), (x + 0.008, y + 0.008, H - 0.01))
obj('luminarias', bm, 'grafite')
lumi = luz_mat('LED', (1.0, 0.95, 0.85))
lumi.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 4.0
base3d.M['led'] = lumi
obj('led', bl, 'led')
for x in (-0.6, 0.6):
    la = bpy.data.lights.new('Luminária', 'AREA')
    la.shape = 'RECTANGLE'
    la.size, la.size_y = 0.08, 2.0
    la.energy = 35
    la.color = (1.0, 0.95, 0.85)
    oa = bpy.data.objects.new('Luminária', la)
    sc.collection.objects.link(oa)
    oa.location = (x, 0, H - 0.21)

# ------------------------------------------------------------------ sujeira: óleo, cavaco, limalha
bm = bmesh.new()
for c, r in (((0.75, 0.75), 0.14), ((0.2, 0.2), 0.08), ((-0.3, -0.25), 0.07), ((-0.75, 0.9), 0.1), ((0.9, -0.6), 0.06)):
    mancha(bm, c, r, 0.0835)
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for k in range(70):                                                       # cavaco: lascas finas torcidas
    p = Vector((random.uniform(-0.55, 0.55), random.uniform(-0.3, 0.9), 0.085))
    if abs(p.x) < 0.3:
        p.x = math.copysign(random.uniform(0.32, 0.6), p.x if p.x else 1)
    caixa(bm, p, (random.uniform(0.012, 0.03), 0.004, 0.003), Matrix.Rotation(random.uniform(0, PI), 3, 'Z') @ Matrix.Rotation(random.uniform(-0.6, 0.6), 3, 'X'))
obj('cavaco', bm, 'aco')

# ------------------------------------------------------------------ vapor da prensa e faíscas da solda
vapores = []
for k in range(3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))
faiscas = []
for k in range(14):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=0.005)
    faiscas.append(obj('faisca', bm, 'faisca'))
vel_f = [Vector((random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), random.uniform(0.3, 1.1))) for _ in faiscas]
luz_solda = bpy.data.lights.new('Arco', 'POINT')
luz_solda.color = (0.7, 0.8, 1.0)
luz_solda.shadow_soft_size = 0.02
ls = bpy.data.objects.new('Arco', luz_solda)
sc.collection.objects.link(ls)


# ------------------------------------------------------------------ animação
def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def y_peca(k, t):
    return y_esteira(k * 0.5 + V * t)


def lerp(a, b, x):
    return Vector(a) + (Vector(b) - Vector(a)) * x


def pulso(x, larg):
    return max(0.0, 1.0 - abs(x) / larg)


em = {n: base3d.M[n].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'] for n in ('verde', 'ambar', 'vermelho')}
for q in range(1, QUADROS + 1):
    t = (q - 1) / FPS
    fr = (q - 1) / QUADROS
    tc = t % 2.0                                                          # tempo dentro do ciclo de 2 s
    for i, o in enumerate(taliscas):
        o.location = (0, y_esteira(i * 0.25 + V * t), ZB)
        o.keyframe_insert('location', frame=q)
    # peças
    for k, (raiz, corpo, comp, cordao) in enumerate(pecas):
        y = y_peca(k, t)
        raiz.location = (0, y, ZB)
        raiz.keyframe_insert('location', frame=q)
        prensada = y > Y_PRENSA - 0.04                                     # a matriz já está descendo quando encosta
        corpo.scale = (1.12, 1.1, 0.62) if prensada else (1, 1, 1)
        corpo.keyframe_insert('scale', frame=q)
        h = 0.08 * corpo.scale.z
        comp.location = (0.0, 0.0, h + (0.012 if prensada else 0.025))
        comp.scale = (1.2, 1.2, 0.45) if prensada else (1, 1, 1)
        comp.hide_render = not (y > Y_POE + 0.005)
        cordao.location = (0, -0.09 * corpo.scale.y + 0.004, h - 0.004)
        cr = suave((y - (Y_SOLDA - 0.1)) / 0.2)
        cordao.scale = (max(cr, 0.02), 1, 1)
        cordao.hide_render = cr <= 0.01
        for o, cs in ((comp, ('location', 'scale', 'hide_render')), (cordao, ('location', 'scale', 'hide_render'))):
            for c in cs:
                o.keyframe_insert(c, frame=q)
    # prensa: desce no instante em que a peça passa pelo meio (t ≡ 0 mod 2)
    dt = min(tc, 2.0 - tc)
    desce = suave(1.0 - dt / 0.32)
    martelo.location = (0, 0, Z_ABERTA + (Z_FECHADA - Z_ABERTA) * desce)
    martelo.keyframe_insert('location', frame=q)
    for k, o in enumerate(vapores):                                       # vapor sobe da matriz depois da batida
        u = (tc - 0.15 - k * 0.12) / 0.9
        ativo = 0.0 < u < 1.0
        o.hide_render = not ativo
        u = min(max(u, 0.0), 1.0)
        o.location = Vector((0.12 * (k - 1), 0.05, ZB + 0.15 + 0.6 * u))
        o.scale = [0.06 + 0.16 * u] * 3
        for c in ('location', 'scale', 'hide_render'):
            o.keyframe_insert(c, frame=q)
    # braço pega-e-põe: põe o componente quando a peça passa em y = −0,6 (t ≡ 1,6 mod 2)
    ph = ((t - 1.6) % 2.0) / 2.0
    alto, baixo = 0.95, ZB + 0.08 + 0.05
    yp = Y_POE + V * (t - 1.6 - round((t - 1.6) / 2.0) * 2.0) if ph > 0.75 else Y_POE
    esteira_alto, esteira_baixo = Vector((0, yp, alto)), Vector((0, yp, baixo))
    mesa_alto, mesa_baixo = PEGA + Vector((0, 0, alto - PEGA.z)), PEGA + Vector((0, 0, 0.02))
    if ph < 0.1:
        p = lerp(Vector((0, Y_POE + V * ph * 2, baixo)), Vector((0, Y_POE + V * 0.2, alto)), suave(ph / 0.1))
    elif ph < 0.38:
        p = lerp(Vector((0, Y_POE + V * 0.2, alto)), mesa_alto, suave((ph - 0.1) / 0.28))
    elif ph < 0.48:
        p = lerp(mesa_alto, mesa_baixo, suave((ph - 0.38) / 0.1))
    elif ph < 0.58:
        p = lerp(mesa_baixo, mesa_alto, suave((ph - 0.48) / 0.1))
    elif ph < 0.85:
        alvo = Vector((0, Y_POE - V * (1.0 - 0.85) * 2, alto))
        p = lerp(mesa_alto, alvo, suave((ph - 0.58) / 0.27))
    else:
        x = (ph - 0.85) / 0.15
        y = Y_POE - V * (1.0 - ph) * 2
        p = Vector((0, y, alto + (baixo - alto) * suave(x)))
    ik(BA, p)
    chave(BA, q)
    fechada = 0.45 < ph < 0.995
    for d, sx in BA['dedos']:
        d.location = (sx * (0.035 if fechada else 0.06), 0, 0)
        d.keyframe_insert('location', frame=q)
    comp_garra.location = p + Vector((0, 0, 0.0))
    comp_garra.hide_render = not (0.47 < ph < 0.995)
    comp_garra.keyframe_insert('location', frame=q)
    comp_garra.keyframe_insert('hide_render', frame=q)
    mesa.rotation_euler = (0, 0, PI / 3 * (int(t / 2.0) + suave((ph - 0.6) / 0.3)) if ph >= 0.6 else PI / 3 * int(t / 2.0) + 0)
    mesa.keyframe_insert('rotation_euler', frame=q)
    # braço de solda: acompanha a peça entre y = 0,5 e 0,7 (t ≡ 0..0,8 mod 2), oscilando ao longo da borda
    yk = Y_SOLDA - 0.1 + V * tc
    soldando = tc < 0.8
    repouso = Vector((0.32, 0.45, 1.05))
    borda = Vector((0.07 * math.sin(2 * PI * 6 * tc), 0, 0))
    ponto = Vector((0, yk - 0.095, ZB + 0.05 + 0.005)) + borda
    if soldando:
        p = ponto
    elif tc < 1.15:
        p = lerp(Vector((0, Y_SOLDA + 0.1 - 0.095, ZB + 0.055)), repouso, suave((tc - 0.8) / 0.35))
    elif tc < 1.6:
        p = repouso
    else:
        p = lerp(repouso, Vector((0, Y_SOLDA - 0.1 - 0.095, ZB + 0.055)), suave((tc - 1.6) / 0.4))
    ik(BS, p)
    chave(BS, q)
    luz_solda.energy = (60 + 40 * math.sin(fr * 300)) if soldando else 0.0
    ls.location = p + Vector((0.02, -0.04, 0.03))
    luz_solda.keyframe_insert('energy', frame=q)
    ls.keyframe_insert('location', frame=q)
    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + fr * 6) % 1.0) * 0.3
        o.location = p + vel_f[k] * tt + Vector((0, 0, -4.9 * tt * tt))
        o.hide_render = not soldando
        for c in ('location', 'hide_render'):
            o.keyframe_insert(c, frame=q)
    # luzes: verde fixa piscando devagar, âmbar no giroflex quando a prensa desce, vermelha piscando rápido de vez em quando
    em['verde'].default_value = 6.0 if (int(t * 2) % 2 == 0) else 2.0
    em['ambar'].default_value = 2.0 + 10.0 * desce
    em['vermelho'].default_value = 8.0 if (1.0 < tc < 1.4 and int(t * 8) % 2 == 0) else 0.8
    for n in em:
        em[n].keyframe_insert('default_value', frame=q)

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('chao', bm, 'chao')
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
sc.view_settings.exposure = -0.4
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 0.7)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    sc.frame_set(int(QUADROS * 0.08) + 1)                                 # soldando e braço indo à mesa
    for i, (ang, alt) in enumerate(((300, 4.6), (215, 4.4), (120, 4.8), (35, 4.2))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.6, math.sin(a) * 4.6, alt)), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, 'montadora_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    sc.frame_set(1)                                                       # prensa fechada
    mirar((0.95, -1.15, 2.55), (-0.15, -0.1, 0.7), 26)                   # por cima, entre as vigas
    sc.render.filepath = os.path.join(AQUI, 'montadora_perto.png')
    bpy.ops.render.render(write_still=True)
if modo == 'video':
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(300)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 6.0, math.sin(a) * 6.0, 3.2)), ALVO, 34)
    if hasattr(sc.render.image_settings, 'media_type'):
        sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(AQUI, 'montadora_video.mp4')
    bpy.ops.render.render(animation=True)
print('MONTADORA ok')
