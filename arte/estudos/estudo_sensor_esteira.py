"""Estudo isolado (fora do jogo): SENSOR DE ESTEIRA (sensor_esteira, 1×1), lote 16 — categoria Lógica.
Fica ao lado da esteira e CONTA os itens que passam no tile da frente (norte), mandando o valor pelo canal da rede
lógica. Materiais e peças prontas do estudo_canos.py (mesmo acabamento: amarelo gasto, grafite, ferro, cromo).
- Pedestal de aço sobre laje de concreto com chumbadores e listras de perigo; braço curto que leva a cabeça até a
  borda norte, na altura dos itens da esteira.
- Cabeça de leitura: caixa blindada com pala, cortina de luz (8 lentes violeta em coluna) olhando para a esteira,
  olho-câmera da IA e um apalpador mecânico de mola (rolete que encosta no item que passa — a conta mecânica que
  confere a da luz).
- Contador mecânico de tambores no alto (5 tambores numerados atrás de um visor), engrenado no apalpador por um eixo
  com junta; caixa de comando com LEDs, antena do canal, eletroduto até o chão, remendo e número de série.
- Na foto, um trecho de esteira de contexto no tile norte (fora da peça).
Animação 4 s: três itens passam: a cortina acende em cada um, o apalpador recua, o último tambor gira um passo; LEDs.
Uso: blender -b --python estudo_sensor_esteira.py -- foto | nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
MODO = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
import lote16_base as L16
g = L16.preparar()
import base3d
from base3d import caixa, caixa_de, cil, tubo, bezier, mangueira

PI = math.pi
Z = Vector((0, 0, 1))
X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
sc = bpy.context.scene
random.seed(1620)
QUADROS = g['QUADROS']
Peca, remendo, serie = g['Peca'], g['remendo'], g['serie']
varrer, toro, chapa_arco, suavizar = g['varrer'], g['toro'], g['chapa_arco'], g['suavizar']
M = base3d.M
LUZ = {}
L16.luz(g, 'cortina', 'Cortina de luz', (0.55, 0.12, 1.0), LUZ)
L16.luz(g, 'led1', 'LED da contagem', (0.15, 1.0, 0.25), LUZ)
L16.luz(g, 'led2', 'LED do canal', (1.0, 0.45, 0.04), LUZ)
L16.luz(g, 'olho', 'Olho da IA', (0.55, 0.12, 1.0), LUZ)
V = lambda x, y, z: Vector((x, y, z))
ZI = 0.24                                     # altura dos itens na esteira (lona a 0,16 + meio item)

P = Peca('sensor_esteira', 0, 0)
# laje, chapa e pedestal
caixa_de(P.B('concreto'), V(-0.30, -0.36, 0), V(0.30, 0.20, 0.05))
caixa_de(P.B('listras'), V(-0.301, -0.361, 0.02), V(0.301, 0.201, 0.045))
caixa_de(P.B('ferro'), V(-0.16, -0.24, 0.05), V(0.16, 0.08, 0.062))
for sx in (-1, 1):
    for sy in (-1, 1):
        p = V(sx * 0.13, -0.08 + sy * 0.13, 0.062)
        tubo(P.B('aco'), p - Z * 0.01, p + Z * 0.02, 0.006, 6)
        cil(P.B('aco'), p + Z * 0.006, 0.012, 0.01, lados=6)
caixa_de(P.B('amarelo'), V(-0.05, -0.13, 0.062), V(0.05, -0.03, 0.56))               # coluna-caixão
def prisma(bm, pts_base, h, eixo):
    """Chapa de base poligonal (pts num plano) com espessura h na direção eixo."""
    a = [bm.verts.new(Vector(p)) for p in pts_base]
    b = [bm.verts.new(Vector(p) + Vector(eixo) * h) for p in pts_base]
    n = len(a)
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))


for k in range(4):                                                                  # nervuras (mãos-francesas)
    a = k * PI / 2
    d = V(math.cos(a), math.sin(a), 0)
    t = V(-d.y, d.x, 0)
    p0 = V(0, -0.08, 0.062) + d * 0.05 - t * 0.004
    prisma(P.B('amarelo'), [p0, p0 + d * 0.07, p0 + Z * 0.13], 0.008, t)
# braço até a borda norte e cabeça de leitura
caixa_de(P.B('amarelo'), V(-0.035, -0.03, ZI + 0.03), V(0.035, 0.30, ZI + 0.09))
caixa_de(P.B('grafite'), V(-0.10, 0.30, ZI - 0.07), V(0.10, 0.44, ZI + 0.12))
caixa_de(P.B('grafite'), V(-0.11, 0.30, ZI + 0.12), V(0.11, 0.47, ZI + 0.135))      # pala
for k in range(8):                                                                  # cortina de luz
    zz = ZI - 0.055 + k * 0.022
    cil(P.B('preto'), V(-0.06, 0.44, zz), 0.008, 0.004, Y, lados=14)
    cil(P.B('cortina'), V(-0.06, 0.4425, zz), 0.0055, 0.002, Y, lados=14)
caixa_de(P.B('cromo'), V(-0.075, 0.44, ZI - 0.07), V(-0.072, 0.445, ZI + 0.11))
cil(P.B('grafite', True), V(0.05, 0.445, ZI + 0.07), 0.022, 0.03, Y, lados=24)       # olho-câmera
cil(P.B('preto', True), V(0.05, 0.461, ZI + 0.07), 0.016, 0.002, Y, lados=24)
cil(P.B('olho', True), V(0.05, 0.4625, ZI + 0.07), 0.007, 0.001, Y, lados=16)
for xx in (-0.09, 0.09):
    for zz in (ZI - 0.06, ZI + 0.11):
        cil(P.B('aco'), V(xx, 0.441, zz), 0.005, 0.004, Y, lados=6)
for sx in (-1, 1):                                                                  # aletas da cabeça
    for k in range(5):
        zz = ZI - 0.05 + k * 0.035
        caixa_de(P.B('ferro'), V(sx * 0.1 if sx > 0 else -0.108, 0.31, zz - 0.003), V(0.108 if sx > 0 else -0.1, 0.43, zz + 0.003))
caixa_de(P.B('adesivo') if 'adesivo' in M else P.B('amarelo'), V(-0.03, 0.299, ZI + 0.02), V(0.03, 0.30, ZI + 0.07))
caixa_de(P.B('oxido'), V(-0.1, 0.32, ZI - 0.071), V(0.04, 0.40, ZI - 0.07))                    # ferrugem embaixo
# apalpador: braço de mola com rolete (anima)
apalp = bpy.data.objects.new('sensor_esteira_apalpador', None)
sc.collection.objects.link(apalp)
apalp.location = V(0.07, 0.44, ZI - 0.02)
A = Peca('sensor_esteira_apalp', 0, 0)
caixa(A.B('aco'), V(0.0, 0.025, 0), (0.012, 0.05, 0.012))
cil(A.B('borracha', True), V(0, 0.052, -0.005), 0.012, 0.03, Z, lados=16)
A.fim()
for n in ('sensor_esteira_apalp_aco', 'sensor_esteira_apalp_borracha'):
    o = sc.objects[n]
    o.parent = apalp
    o.location = (0, 0, 0)
g['toro'](P.B('aco'), V(0.07, 0.44, ZI - 0.02), 0.01, 0.002, 12, 4)                 # mola do pivô
# eixo com junta até o contador
cil(P.B('ferro', True), V(0.07, 0.40, ZI + 0.14), 0.012, 0.012, Z, lados=12)               # bucha na pala (o eixo vem de dentro da cabeça)
tubo(P.B('aco', True), V(0.07, 0.40, ZI + 0.135), V(0.07, 0.40, ZI + 0.2), 0.005, 8)
cil(P.B('ferro', True), V(0.07, 0.40, ZI + 0.2), 0.009, 0.018, Z, lados=12)
tubo(P.B('aco', True), V(0.07, 0.40, ZI + 0.2), V(0.04, 0.12, ZI + 0.32), 0.005, 8)
# contador mecânico de tambores no alto da coluna
ZC = 0.60
caixa_de(P.B('grafite'), V(-0.10, -0.12, ZC - 0.05), V(0.10, 0.14, ZC + 0.07))
caixa_de(P.B('preto'), V(-0.08, 0.14, ZC - 0.025), V(0.08, 0.142, ZC + 0.035))
tambores = []
for k in range(5):
    e = bpy.data.objects.new('sensor_esteira_tambor%d' % k, None)
    sc.collection.objects.link(e)
    e.location = V(-0.06 + k * 0.03, 0.12, ZC + 0.005)
    bm = bmesh.new()
    cil(bm, V(0, 0, 0), 0.022, 0.024, X, lados=10)
    base3d.obj('sensor_esteira_tambor%d_mostrador' % k, bm, 'mostrador').parent = e
    bm = bmesh.new()
    for j in range(10):                                                         # algarismos (traço por face)
        a = j * 2 * PI / 10
        caixa(bm, V(0, 0.0225 * math.cos(a), 0.0225 * math.sin(a)), (0.008, 0.0015, 0.003 + 0.0015 * (j % 3)),
              Matrix.Rotation(a, 3, 'X'))
    base3d.obj('sensor_esteira_tambor%d_preto' % k, bm, 'preto').parent = e
    tambores.append(e)
for xx in (-0.09, 0.09):
    for zz in (ZC - 0.04, ZC + 0.06):
        cil(P.B('aco'), V(xx, 0.141, zz), 0.005, 0.004, Y, lados=6)
for sx in (-1, 1):                                                                  # aletas nas laterais
    for k in range(6):
        yy = -0.10 + k * 0.042
        caixa_de(P.B('ferro'), V(sx * 0.10 if sx > 0 else -0.112, yy - 0.004, ZC - 0.04), V(0.112 if sx > 0 else -0.10, yy + 0.004, ZC + 0.06))
caixa_de(P.B('cromo'), V(-0.085, 0.141, ZC - 0.03), V(0.085, 0.1425, ZC - 0.026))           # moldura do visor
caixa_de(P.B('cromo'), V(-0.085, 0.141, ZC + 0.036), V(0.085, 0.1425, ZC + 0.04))
caixa_de(P.B('cinza'), V(-0.06, -0.08, ZC + 0.07), V(0.06, 0.08, ZC + 0.078))                # tampa de inspeção
for xx in (-0.05, 0.05):
    for yy in (-0.07, 0.07):
        cil(P.B('aco'), V(xx, yy, ZC + 0.08), 0.004, 0.004, Z, lados=6)
caixa_de(P.B('cortina'), V(-0.1005, -0.12, ZC + 0.05), V(-0.1, 0.14, ZC + 0.056))             # faixa violeta da IA
caixa_de(P.B('tinta'), V(-0.04, -0.1205, ZC - 0.02), V(0.04, -0.12, ZC + 0.0))
# caixa de comando com LEDs, antena do canal, eletroduto
caixa_de(P.B('cinza'), V(0.05, -0.13, 0.30), V(0.13, -0.03, 0.42))
for zz, chave in ((0.39, 'led1'), (0.36, 'led2')):
    cil(P.B('preto'), V(0.131, -0.06, zz), 0.006, 0.003, X, lados=12)
    bmesh.ops.create_icosphere(P.B(chave), subdivisions=2, radius=0.004, matrix=Matrix.Translation(V(0.133, -0.06, zz)))
tubo(P.B('aco'), V(-0.07, -0.08, ZC + 0.07), V(-0.07, -0.08, ZC + 0.27), 0.003, 6)
g['toro'](P.B('led2'), V(-0.07, -0.08, ZC + 0.22), 0.011, 0.003, 18, 6)
cil(P.B('borracha', True), V(-0.07, -0.08, ZC + 0.28), 0.006, 0.02, Z, lados=10)
cil(P.B('aco'), V(0.09, -0.08, 0.295), 0.008, 0.012, Z, lados=6)
pts = [V(0.09, -0.08, 0.29), V(0.1, -0.1, 0.18), V(0.16, -0.2, 0.08), V(0.18, -0.24, 0.05)]
varrer(P.B('borracha', True), bezier(*pts, 10), 0.008, 10)
cil(P.B('aco'), V(0.18, -0.24, 0.054), 0.011, 0.01, Z, lados=6)
g['fios'](P, V(0.13, -0.05, 0.41), V(0.05, -0.02, 0.5), 2, 0.03)
caixa_de(P.B('tinta'), V(-0.051, -0.12, 0.35), V(-0.0505, -0.05, 0.38))
caixa_de(P.B('cinza'), V(-0.0505, -0.11, 0.15), V(0.0505, -0.05, 0.22))             # chapa trocada (remendo)
for zz in (0.16, 0.21):
    for yy in (-0.105, -0.055):
        cil(P.B('aco'), V(-0.051, yy, zz), 0.004, 0.003, X, lados=6)
P.fim()

# ------------------------------------------------------------------ esteira de contexto (tile norte, sai na conversão)
Ctx = Peca('contexto_esteira', 0, 0)
caixa_de(Ctx.B('grafite'), V(-0.5, 0.52, 0.10), V(0.5, 1.48, 0.15))
caixa_de(Ctx.B('aco'), V(-0.5, 0.55, 0.15), V(0.5, 1.45, 0.16))
for sy in (0.52, 1.45):
    caixa_de(Ctx.B('amarelo'), V(-0.5, sy, 0.10), V(0.5, sy + 0.03, 0.2))
Ctx.fim()
itens = []
for k in range(3):
    bm = bmesh.new()
    caixa(bm, V(0, 0, 0), (0.14, 0.14, 0.05))
    o = base3d.obj('contexto_item%d' % k, bm, 'cobre')
    itens.append(o)

# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    perto = 0.0
    for k, o in enumerate(itens):
        x = -0.7 + ((fr + k / 3) % 1.0) * 1.4
        o.location = V(x, 1.0, 0.185)
        o.keyframe_insert('location', frame=q)
        perto = max(perto, max(0.0, 1.0 - abs(x - 0.0) / 0.12))
    L16.chave_luz(LUZ, 'cortina', 1.0 + 9.0 * perto, q)
    apalp.rotation_euler = (0, 0, -0.5 * perto)
    apalp.keyframe_insert('rotation_euler', frame=q)
    passos = int(fr * 3 + 0.5)
    tambores[4].rotation_euler = (2 * PI / 10 * (passos + min(1.0, max(0.0, (fr * 3 + 0.5 - passos) * 4))), 0, 0)
    tambores[4].keyframe_insert('rotation_euler', frame=q)
    L16.chave_luz(LUZ, 'led1', 0.2 + 6.0 * perto, q)
    L16.chave_luz(LUZ, 'led2', 4.0, q)
    L16.chave_luz(LUZ, 'olho', 4.0 + 2.0 * math.sin(2 * PI * fr * 2), q)
L16.linear()
cam = L16.cena()
L16.fotos(MODO, cam, {
    'sensor_esteira_0': ((1.4, -1.5, 1.1), (0, 0.2, 0.35), 32, 1200, 1100),
    'sensor_esteira_perto': ((0.75, 1.15, 0.6), (0, 0.4, 0.3), 30, 1200, 1100),
}, quadro=33)
print('SENSOR ESTEIRA ok')
