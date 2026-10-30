"""Estudo isolado (fora do jogo): COMPARADOR (comparador, 1×1), lote 16 — categoria Lógica.
Recebe o valor de um canal da rede lógica (sensores) e liga/desliga as máquinas, braços e bombas encostadas nele,
por condição (maior/menor que um número). Materiais e peças prontas do estudo_canos.py.
- A comparação é mecânica e à vista ("logicamente surreal"): atrás de um visor gradeado, uma BALANÇA de braço —
  num prato, uma esfera de campo violeta do tamanho do valor recebido; no outro, a pilha de pesos de referência (o
  número escolhido); o braço tomba e fecha o contato de mercúrio que manda ligar ou desligar.
- Armário de ferro fundido sobre pés, venezianas, tampa aparafusada, antena do canal com anel, banco de três
  contatores no leste com LEDs, tambor de ajuste do número no oeste.
- Quatro eletrodutos corrugados saindo da base para as quatro bordas do tile, cada um numa tomada de comando com LED
  (é por ela que o comparador manda nos vizinhos encostados).
Animação 4 s: a esfera cresce e encolhe (valor do canal), o braço tomba, contatores e LEDs das tomadas trocam.
Uso: blender -b --python estudo_comparador.py -- foto | nada"""
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
random.seed(1621)
QUADROS = g['QUADROS']
Peca, remendo, serie = g['Peca'], g['remendo'], g['serie']
varrer, toro, chapa_arco, suavizar = g['varrer'], g['toro'], g['chapa_arco'], g['suavizar']
M = base3d.M
LUZ = {}
L16.luz(g, 'esfera', 'Esfera do valor', (0.55, 0.12, 1.0), LUZ)
L16.luz(g, 'liga', 'LED liga', (0.15, 1.0, 0.25), LUZ)
L16.luz(g, 'desliga', 'LED desliga', (1.0, 0.05, 0.02), LUZ)
L16.luz(g, 'canal', 'Anel do canal', (0.15, 1.0, 0.3), LUZ)
V = lambda x, y, z: Vector((x, y, z))


def corrugado(bm, pts, r, passo=0.008, lados=12):
    dens = []
    for a, b in zip(pts, pts[1:]):
        k = max(1, int((b - a).length / passo))
        dens += [a.lerp(b, i / k) for i in range(k)]
    dens.append(pts[-1])
    varrer(bm, dens, [r * (1.12 if i % 2 else 0.94) for i in range(len(dens))], lados)


P = Peca('comparador', 0, 0)
# laje e pés
caixa_de(P.B('concreto'), V(-0.42, -0.42, 0), V(0.42, 0.42, 0.05))
for sx in (-1, 1):
    for sy in (-1, 1):
        caixa_de(P.B('ferro'), V(sx * 0.2 - 0.03, sy * 0.15 - 0.03, 0.05), V(sx * 0.2 + 0.03, sy * 0.15 + 0.03, 0.12))
        cil(P.B('aco'), V(sx * 0.2, sy * 0.15, 0.06), 0.012, 0.012, Z, lados=6)
# armário
X0, X1, Y0, Y1, Z0, Z1 = -0.24, 0.24, -0.18, 0.18, 0.12, 0.72
E = 0.015                                                                                    # espessura da chapa
caixa_de(P.B('grafite'), V(X0, Y1 - E, Z0), V(X1, Y1, Z1))                                     # fundo (norte)
caixa_de(P.B('grafite'), V(X0, Y0 + 0.02, Z0), V(X0 + E, Y1, Z1))                              # laterais
caixa_de(P.B('grafite'), V(X1 - E, Y0 + 0.02, Z0), V(X1, Y1, Z1))
caixa_de(P.B('grafite'), V(X0, Y0 + 0.02, Z0), V(X1, Y1, Z0 + E))                              # piso
caixa_de(P.B('oxido'), V(X0 + E, Y1 - E - 0.002, Z0 + 0.1), V(X1 - E, Y1 - E, Z1 - 0.06))    # fundo interno em primer
caixa_de(P.B('grafite'), V(X0 - 0.01, Y0 + 0.01, Z1), V(X1 + 0.01, Y1 + 0.01, Z1 + 0.025))       # tampo com aba
for (a, b) in ((V(X0, Y0, Z0), V(X0 + 0.04, Y0 + 0.02, Z1)), (V(X1 - 0.04, Y0, Z0), V(X1, Y0 + 0.02, Z1)),
               (V(X0, Y0, Z0), V(X1, Y0 + 0.02, Z0 + 0.12)), (V(X0, Y0, Z1 - 0.05), V(X1, Y0 + 0.02, Z1))):
    caixa_de(P.B('ferro'), a, b)                                                             # moldura do visor (sul)
for k in range(9):                                                                           # parafusos da moldura
    for zz in (Z0 + 0.1, Z1 - 0.025):
        cil(P.B('aco'), V(X0 + 0.03 + k * 0.0525, Y0 - 0.001, zz), 0.005, 0.004, Y, lados=6)
for k in range(7):                                                                           # grade do visor
    xx = X0 + 0.04 + (X1 - X0 - 0.08) * (k + 0.5) / 7
    caixa_de(P.B('aco'), V(xx - 0.004, Y0 + 0.006, Z0 + 0.12), V(xx + 0.004, Y0 + 0.014, Z1 - 0.05))
caixa_de(P.B('aco'), V(X0 + 0.04, Y0 + 0.006, (Z0 + Z1) / 2 + 0.01), V(X1 - 0.04, Y0 + 0.014, (Z0 + Z1) / 2 + 0.02))
for sx in (-1, 1):                                                                           # venezianas no norte
    for k in range(7):
        zz = Z0 + 0.12 + k * 0.05
        caixa(P.B('grafite'), V(sx * 0.11, Y1 + 0.006, zz), (0.16, 0.01, 0.03), Matrix.Rotation(-0.6, 3, 'X'))
# balança dentro: coluna, cutelo, braço (anima), pratos nas correntes, esfera e pesos
caixa_de(P.B('ferro'), V(-0.03, -0.05, Z0 + 0.02), V(0.03, 0.05, Z0 + 0.04))
tubo(P.B('cromo', True), V(0, 0, Z0 + 0.04), V(0, 0, Z0 + 0.42), 0.012, 14)
caixa_de(P.B('aco'), V(-0.02, -0.02, Z0 + 0.42), V(0.02, 0.02, Z0 + 0.45))
braco = bpy.data.objects.new('comparador_braco', None)
sc.collection.objects.link(braco)
braco.location = V(0, 0, Z0 + 0.45)
pratos = []
B = Peca('comparador_balanca', 0, 0)
caixa(B.B('aco'), V(0, 0, 0), (0.36, 0.012, 0.018))
cil(B.B('ferro', True), V(0, 0, 0), 0.016, 0.03, Y, lados=16)
caixa(B.B('amarelo'), V(0, 0, 0.03), (0.006, 0.006, 0.06))                                    # ponteiro
B.fim()
for n in ('comparador_balanca_aco', 'comparador_balanca_ferro', 'comparador_balanca_amarelo'):
    o = sc.objects[n]
    o.parent = braco
    o.location = (0, 0, 0)
for sx in (-1, 1):
    e = bpy.data.objects.new('comparador_prato%d' % (sx > 0), None)
    sc.collection.objects.link(e)
    e.parent = braco
    e.location = (sx * 0.17, 0, 0)
    bm = bmesh.new()
    for k in range(5):                                                                      # corrente (elos)
        zz = -0.015 - k * 0.022
        toro(bm, V(0, 0, zz), 0.008, 0.0018, 12, 4, X if k % 2 else Y)
    toro(bm, V(0, 0, -0.13), 0.06, 0.004, 32, 6)
    cil(bm, V(0, 0, -0.132), 0.058, 0.004, Z, lados=28)
    for k in range(3):
        a = k * 2 * PI / 3
        tubo(bm, V(0, 0, -0.12), V(0.055 * math.cos(a), 0.055 * math.sin(a), -0.13), 0.0015, 4)
    base3d.obj('comparador_prato%d_aco' % (sx > 0), bm, 'aco').parent = e
    pratos.append(e)
esfera = bpy.data.objects.new('comparador_esfera', None)
sc.collection.objects.link(esfera)
esfera.parent = pratos[0]
esfera.location = (0, 0, -0.09)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.035)
suavizar(base3d.obj('comparador_esfera_luz', bm, 'esfera')).parent = esfera
bm = bmesh.new()
for k in range(4):                                                                         # pesos de referência
    cil(bm, V(0, 0, -0.122 + k * 0.016), 0.04 - k * 0.006, 0.014, Z, lados=24)
cil(bm, V(0, 0, -0.06), 0.006, 0.02, Z, lados=10)
base3d.obj('comparador_pesos_ferro', bm, 'ferro').parent = pratos[1]
# contato de mercúrio sob o ponteiro (a ampola do lado "liga")
caixa_de(P.B('cobre'), V(-0.006, -0.02, Z0 + 0.525), V(0.006, 0.02, Z0 + 0.53))
caixa_de(P.B('aco'), V(-0.004, 0.018, Z0 + 0.45), V(0.004, 0.024, Z0 + 0.53))                     # suporte do contato
# contatores no leste e tambor do número no oeste
for k in range(3):
    yy = -0.1 + k * 0.1
    caixa_de(P.B('cinza'), V(X1, yy - 0.04, Z0 + 0.22), V(X1 + 0.07, yy + 0.04, Z0 + 0.36))
    caixa_de(P.B('preto'), V(X1 + 0.07, yy - 0.025, Z0 + 0.30), V(X1 + 0.072, yy + 0.025, Z0 + 0.34))
    for chave, zz in (('liga', Z0 + 0.33), ('desliga', Z0 + 0.31)):
        bmesh.ops.create_icosphere(P.B(chave), subdivisions=1, radius=0.005,
                                   matrix=Matrix.Translation(V(X1 + 0.074, yy + (0.012 if chave == 'liga' else -0.012), zz)))
    for zz in (Z0 + 0.23, Z0 + 0.35):
        cil(P.B('aco'), V(X1 + 0.071, yy, zz), 0.004, 0.003, X, lados=6)
cil(P.B('ferro', True), V(X0 - 0.03, 0.0, Z0 + 0.32), 0.07, 0.06, X, lados=28)
cil(P.B('mostrador', True), V(X0 - 0.03, 0.0, Z0 + 0.32), 0.071, 0.03, X, lados=28)
for j in range(10):
    a = j * 2 * PI / 10
    caixa(P.B('preto'), V(X0 - 0.03, 0.071 * math.cos(a), Z0 + 0.32 + 0.071 * math.sin(a)), (0.012, 0.002, 0.008),
          Matrix.Rotation(a, 3, 'X'))
cil(P.B('aco', True), V(X0 - 0.065, 0.0, Z0 + 0.32), 0.012, 0.012, X, lados=12)
# antena do canal
tubo(P.B('aco'), V(0.15, 0.12, Z1 + 0.025), V(0.15, 0.12, Z1 + 0.28), 0.003, 6)
bm = bmesh.new()
toro(bm, V(0.15, 0.12, Z1 + 0.22), 0.013, 0.003, 20, 6)
base3d.obj('comparador_canal', bm, 'canal')
cil(P.B('borracha', True), V(0.15, 0.12, Z1 + 0.29), 0.006, 0.02, Z, lados=10)
caixa_de(P.B('cinza'), V(-0.12, -0.06, Z1 + 0.025), V(0.04, 0.10, Z1 + 0.035))                    # tampa aparafusada
for xx in (-0.11, 0.03):
    for yy in (-0.05, 0.09):
        cil(P.B('aco'), V(xx, yy, Z1 + 0.037), 0.005, 0.004, Z, lados=6)
# quatro eletrodutos até as tomadas de comando nas bordas
tomadas = []
for k, (d, s) in enumerate(((Y, X), (-Y, X), (X, Y), (-X, Y))):
    borda = d * 0.47
    a = V(0, 0, 0.12) + d * (0.12 if abs(d.y) > 0 else 0.2) + s * 0.07
    b = borda + s * 0.07 + V(0, 0, 0.09)
    corrugado(P.B('borracha', True), bezier(a, a - Z * 0.05, b - d * 0.12 + Z * 0.0, b - d * 0.02, 10), 0.012)
    caixa_de(P.B('amarelo'), b - d * 0.02 - s * 0.05 + V(0, 0, -0.04) + (d * 0 if True else 0),
             b + d * 0.025 + s * 0.05 + V(0, 0, 0.05))
    tomadas.append(b + d * 0.002 + V(0, 0, 0.055))
P.fim()
# LED de cada tomada (objeto por tomada: liga/desliga)
for k, p in enumerate(tomadas):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.008, matrix=Matrix.Translation(p))
    base3d.obj('comparador_tomada%d' % k, bm, 'liga' if k % 2 == 0 else 'desliga')

# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    valor = 0.5 + 0.5 * math.sin(2 * PI * fr)
    s = 0.6 + 0.8 * valor
    esfera.scale = (s, s, s)
    esfera.keyframe_insert('scale', frame=q)
    tomba = max(-1.0, min(1.0, (valor - 0.5) * 4))
    braco.rotation_euler = (0, 0.14 * tomba, 0)
    braco.keyframe_insert('rotation_euler', frame=q)
    for e in pratos:                                                       # os pratos ficam de pé
        e.rotation_euler = (0, -0.14 * tomba, 0)
        e.keyframe_insert('rotation_euler', frame=q)
    liga = 1.0 if tomba > 0 else 0.0
    L16.chave_luz(LUZ, 'esfera', 6.0 + 4.0 * valor, q)
    L16.chave_luz(LUZ, 'liga', 0.1 + 6.0 * liga, q)
    L16.chave_luz(LUZ, 'desliga', 0.1 + 6.0 * (1 - liga), q)
    L16.chave_luz(LUZ, 'canal', 4.0 + 2.0 * math.sin(2 * PI * fr * 2), q)
L16.linear()
cam = L16.cena()
L16.fotos(MODO, cam, {
    'comparador_0': ((1.3, -1.6, 1.2), (0, 0, 0.42), 32, 1200, 1100),
    'comparador_perto': ((0.35, -0.95, 0.6), (0, 0, 0.45), 30, 1200, 1100),
}, quadro=20)
print('COMPARADOR ok')
