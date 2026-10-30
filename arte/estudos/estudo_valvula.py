"""Estudo isolado (fora do jogo): VÁLVULA (valvula, 1×1), lote 16 — categoria Lógica.
Peça de cano (entra no sul, sai no norte, eixo a 0,34 m, flanges do estudo_canos.py) que separa duas redes e só deixa o
fluido passar acima/abaixo de um nível (ou quando o comparador manda).
- Válvula gaveta flangeada no meio: corpo de ferro fundido com nervuras, castelo aparafusado, haste ascendente cromada
  dentro da arcada, atuador elétrico no topo (motor deitado com aletas, redutor, indicador de posição listrado que
  gira), caixa de chaves fim de curso com LEDs.
- Linhas de pilotagem de cobre dos dois lados do corpo (montante e jusante) até o pressostato diferencial da IA
  preso no atuador: é como ela compara o nível das duas redes.
- Trechos de cano até as flanges da borda, dois suportes, remendo, número de série, gotejamento no castelo.
Animação 4 s: a gaveta abre e fecha (haste sobe/desce, indicador gira 90°), LEDs aberto/fechado, ponteiro.
Uso: blender -b --python estudo_valvula.py -- foto | nada"""
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
random.seed(1619)
QUADROS = g['QUADROS']
Peca, flange, suporte, remendo, serie, manometro = g['Peca'], g['flange'], g['suporte'], g['remendo'], g['serie'], g['manometro']
varrer, toro, chapa_arco, suavizar = g['varrer'], g['toro'], g['chapa_arco'], g['suavizar']
CZ, R, RF, EF, RB = g['CZ'], g['R'], g['RF'], g['EF'], g['RB']
M = base3d.M
LUZ = {}
L16.luz(g, 'aberta', 'LED aberta', (0.15, 1.0, 0.25), LUZ)
L16.luz(g, 'fechada', 'LED fechada', (1.0, 0.05, 0.02), LUZ)
L16.luz(g, 'ia', 'LED da IA', (0.55, 0.12, 1.0), LUZ)
C = lambda x, y, z=CZ: Vector((x, y, z))

P = Peca('valvula', 0, 0)
flange(P, C(0, -0.5), -Y)
flange(P, C(0, 0.5), Y)
for sg in (-1, 1):
    tubo(P.B('cano', True), C(0, sg * 0.47), C(0, sg * 0.20), R, 32)
    flange(P, C(0, sg * 0.165), -Y * sg, pescoco=False)                          # flange do cano contra a da válvula
    cil(P.B('ferro', True), C(0, sg * 0.1475), RF, EF, Y, lados=40)              # flange da válvula
    for k in range(8):
        a = PI / 8 + k * PI / 4
        p = C(0, sg * 0.125) + Vector((math.cos(a), 0, math.sin(a))) * RB
        cil(P.B('aco'), p, 0.019, 0.016, Y, lados=6)
    suporte(P, C(0, sg * 0.34), Y)
# corpo (oval com nervuras) e castelo
cil(P.B('ferro', True), C(0, 0), 0.135, 0.25, Y, lados=36)
cil(P.B('ferro', True), C(0, 0, CZ + 0.06), 0.11, 0.24, Z, lados=32, r2=0.08)
for k in range(6):
    a = k * PI / 3
    caixa(P.B('ferro'), C(0.13 * math.cos(a), 0, CZ + 0.13 * math.sin(a)), (0.012, 0.22, 0.03), Matrix.Rotation(-a, 3, 'Y'))
cil(P.B('ferro', True), C(0, 0, CZ + 0.19), 0.12, 0.03, Z, lados=32)                 # flange do castelo
for k in range(10):
    a = k * 2 * PI / 10
    cil(P.B('aco'), C(0.105 * math.cos(a), 0.105 * math.sin(a), CZ + 0.21), 0.011, 0.012, Z, lados=6)
cil(P.B('ferro', True), C(0, 0, CZ + 0.25), 0.075, 0.09, Z, lados=28)                  # castelo
cil(P.B('ferro', True), C(0, 0, CZ + 0.30), 0.045, 0.02, Z, lados=20)                  # sobreposta (gaxeta)
# arcada (dois montantes) e mesa do atuador
for sx in (-1, 1):
    caixa_de(P.B('amarelo'), C(sx * 0.06 - 0.012, -0.03, CZ + 0.29), C(sx * 0.06 + 0.012, 0.03, CZ + 0.47))
caixa_de(P.B('amarelo'), C(-0.085, -0.045, CZ + 0.47), C(0.085, 0.045, CZ + 0.49))
# haste ascendente (anima) e porca de acionamento
haste = bpy.data.objects.new('valvula_haste', None)
sc.collection.objects.link(haste)
haste.location = C(0, 0, CZ + 0.30)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.09)), 0.014, 0.18, Z, lados=16)
suavizar(base3d.obj('valvula_haste_cromo', bm, 'cromo')).parent = haste
bm = bmesh.new()
for k in range(14):                                                                  # rosca (anéis)
    g['toro'](bm, Vector((0, 0, 0.02 + k * 0.011)), 0.0145, 0.0018, 16, 4)
base3d.obj('valvula_haste_rosca', bm, 'aco').parent = haste
# atuador elétrico: redutor, motor deitado com aletas, indicador de posição
ZA = CZ + 0.49
caixa_de(P.B('grafite'), C(-0.08, -0.07, ZA), C(0.08, 0.07, ZA + 0.13))
cil(P.B('grafite', True), C(0.15, 0, ZA + 0.06), 0.055, 0.14, X, lados=28)
for k in range(10):
    a = k * 2 * PI / 10
    caixa(P.B('grafite'), C(0.15, 0.06 * math.cos(a), ZA + 0.06 + 0.06 * math.sin(a)), (0.11, 0.008, 0.008), Matrix.Rotation(a, 3, 'X'))
cil(P.B('ferro', True), C(0.225, 0, ZA + 0.06), 0.058, 0.012, X, lados=28)
caixa_de(P.B('cinza'), C(-0.07, -0.13, ZA + 0.02), C(0.02, -0.07, ZA + 0.11))          # chaves fim de curso
for j, (chave, xx) in enumerate((('aberta', -0.045), ('fechada', -0.02), ('ia', 0.005))):
    cil(P.B('preto'), C(xx, -0.131, ZA + 0.085), 0.007, 0.003, Y, lados=12)
    bmesh.ops.create_icosphere(P.B(chave), subdivisions=2, radius=0.0045, matrix=Matrix.Translation(C(xx, -0.133, ZA + 0.085)))
indic = bpy.data.objects.new('valvula_indicador', None)
sc.collection.objects.link(indic)
indic.location = C(0, 0, ZA + 0.13)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.02)), 0.045, 0.04, Z, lados=28)
base3d.obj('valvula_indicador_amarelo', bm, 'amarelo').parent = indic
bm = bmesh.new()
caixa(bm, Vector((0, 0, 0.0405)), (0.08, 0.016, 0.002))
base3d.obj('valvula_indicador_seta', bm, 'preto').parent = indic
# pressostato diferencial da IA e linhas de pilotagem dos dois lados do corpo
caixa_de(P.B('cinza'), C(-0.17, -0.05, ZA - 0.02), C(-0.08, 0.05, ZA + 0.08))
cil(P.B('cromo', True), C(-0.125, -0.051, ZA + 0.03), 0.028, 0.008, Y, lados=24)
for sg in (-1, 1):
    a = C(-0.11, sg * 0.10, CZ + 0.03)
    tubo(P.B('ferro'), a + Vector((0.03, 0, 0)), a, 0.012, 10)
    pts = [a, a + Vector((-0.05, 0, 0.03)), C(-0.17, sg * 0.04, ZA - 0.05), C(-0.15, sg * 0.03, ZA - 0.02)]
    varrer(P.B('cobre', True), bezier(*pts, 10), 0.005, 8)
manometro(P, C(-0.125, 0.0, ZA + 0.13), Z, C(-0.125, 0.0, ZA + 0.08), 0.028)
# cabo do atuador até o chão
cil(P.B('aco'), C(0.06, 0.07, ZA + 0.02), 0.009, 0.014, Y, lados=6)
pts = [C(0.06, 0.08, ZA + 0.02), C(0.09, 0.18, ZA - 0.05), C(0.2, 0.22, 0.3), C(0.22, 0.24, 0.0)]
varrer(P.B('borracha', True), bezier(*pts, 12), 0.008, 10)
caixa_de(P.B('concreto'), C(0.18, 0.2, 0), C(0.26, 0.28, 0.02))
remendo(P, C(0, -0.32), Y, R, math.radians(30), math.radians(110), 0.07)
serie(P, C(0, 0.30), Y, R, math.radians(150), 5)
g['pingo'](P, C(0.0, 0.07, CZ + 0.17), 'gota', 1, r_poca=0.05)
caixa_de(P.B('tinta'), C(0.136, -0.05, CZ - 0.02), C(0.137, 0.05, CZ + 0.02))
P.fim()

# ------------------------------------------------------------------ animação (laço de 4 s): fecha e abre
def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    aberto = suave((fr - 0.05) / 0.2) * (1 - suave((fr - 0.55) / 0.2))
    haste.location = C(0, 0, CZ + 0.30 + 0.07 * aberto)
    haste.keyframe_insert('location', frame=q)
    indic.rotation_euler = (0, 0, PI / 2 * aberto)
    indic.keyframe_insert('rotation_euler', frame=q)
    L16.chave_luz(LUZ, 'aberta', 0.1 + 6.0 * aberto, q)
    L16.chave_luz(LUZ, 'fechada', 0.1 + 6.0 * (1 - aberto), q)
    L16.chave_luz(LUZ, 'ia', 5.0 if (q // 8) % 2 == 0 else 0.4, q)
L16.gotas_e_ponteiros(g, QUADROS)
L16.linear()
cam = L16.cena()
L16.fotos(MODO, cam, {
    'valvula_0': ((1.5, -1.5, 1.3), (0, 0, 0.5), 32, 1200, 1100),
    'valvula_perto': ((0.7, -0.75, 1.05), (0, 0, 0.75), 30, 1200, 1100),
}, quadro=30)
print('VALVULA ok')
