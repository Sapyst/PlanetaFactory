"""Estudo isolado (fora do jogo): SENSOR DE TANQUE (sensor_tanque, 1×1), lote 16 — categoria Lógica.
Peça de cano (entra no sul, sai no norte, eixo a 0,34 m, flanges iguais às do estudo_canos.py) que LÊ O NÍVEL da rede
em que está (o tanque ligado nela incluso) e manda o valor (0–100%) pelo canal da rede lógica.
- Trecho de cano com as duas flanges da borda, dois suportes de perfil H e um colar de tomada no topo com válvula
  esférica motorizada; dali o tubo de impulso de cobre (com serpentina de alívio) sobe até o transmissor.
- Transmissor numa coluna galvanizada (leste) sobre bloquinho de concreto: caixa com visor de LEDs, prensa-cabos,
  antena curta com anel do canal; abaixo dele a COLUNA DE LEVITAÇÃO: tubo de vidro com régua de 10 marcas e uma
  bolha âmbar que o campo violeta (anéis) segura na altura do nível — é o mostrador da IA.
- Eletroduto corrugado da caixa até o chão, número de série no cano, remendo aparafusado, pingo de seiva no colar.
Animação 4 s: a bolha sobe e desce (o nível da rede mudando), os anéis pulsam, o visor pisca, ponteiro do manômetro.
Uso: blender -b --python estudo_sensor_tanque.py -- foto | nada"""
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
random.seed(1618)
QUADROS = g['QUADROS']
Peca, flange, suporte, remendo, serie, manometro = g['Peca'], g['flange'], g['suporte'], g['remendo'], g['serie'], g['manometro']
varrer, toro, chapa_arco, suavizar = g['varrer'], g['toro'], g['chapa_arco'], g['suavizar']
CZ, R = g['CZ'], g['R']
M = base3d.M
LUZ = {}
L16.luz(g, 'visor', 'Visor do transmissor', (0.55, 0.12, 1.0), LUZ)
L16.luz(g, 'anel', 'Anel de levitação', (0.55, 0.12, 1.0), LUZ)
L16.luz(g, 'bolha', 'Bolha de nível', (1.0, 0.5, 0.06), LUZ)
L16.luz(g, 'canal', 'Anel do canal', (0.15, 1.0, 0.3), LUZ)
C = lambda x, y, z=CZ: Vector((x, y, z))

P = Peca('sensor_tanque', 0, 0)
# ---------------------------------------------------------------- trecho de cano com as flanges da borda
flange(P, C(0, -0.5), -Y)
flange(P, C(0, 0.5), Y)
tubo(P.B('cano', True), C(0, -0.47), C(0, 0.47), R, 32)
suporte(P, C(0, -0.32), Y)
suporte(P, C(0, 0.32), Y)
serie(P, C(0, -0.15), Y, R, math.radians(150), 5)
remendo(P, C(0, 0.18), Y, R, math.radians(200), math.radians(280), 0.07)
# colar de tomada no topo (y 0): sela, niple, válvula esférica motorizada
chapa_arco(P.B('ferro', True), C(0, 0), Y, R + 0.001, 0.012, 0.09, math.radians(30), math.radians(150), 14)
for sx in (-1, 1):
    caixa(P.B('ferro'), C(sx * 0.085, 0, CZ + 0.06), (0.03, 0.09, 0.012))
    tubo(P.B('aco'), C(sx * 0.085, 0, CZ + 0.02), C(sx * 0.085, 0, CZ + 0.09), 0.006, 6)
    cil(P.B('aco'), C(sx * 0.085, 0, CZ + 0.072), 0.011, 0.01, Z, lados=6)
tubo(P.B('aco', True), C(0, 0, CZ + 0.1), C(0, 0, CZ + 0.16), 0.018, 16)
cil(P.B('ferro', True), C(0, 0, CZ + 0.18), 0.03, 0.05, Y, lados=20)                     # corpo da esfera
caixa_de(P.B('grafite'), C(-0.025, -0.025, CZ + 0.205), C(0.025, 0.025, CZ + 0.255))      # atuador da válvula
caixa_de(P.B('amarelo'), C(-0.012, -0.026, CZ + 0.235), C(0.012, -0.025, CZ + 0.25))
tubo(P.B('aco', True), C(0, 0, CZ + 0.195), C(0.04, 0, CZ + 0.195), 0.01, 12)
g['pingo'](P, C(0, -0.03, CZ + 0.155), 'gota', 1, r_poca=0.05)
manometro(P, C(-0.08, 0.0, CZ + 0.24), Vector((-1, 0, 0)), C(-0.02, 0, CZ + 0.19), 0.03)
# tubo de impulso de cobre: da válvula até o transmissor, com serpentina de alívio
pts = [C(0.04, 0, CZ + 0.195), C(0.10, 0, CZ + 0.2), C(0.20, 0.0, CZ + 0.2)]
for k in range(10):                                                                   # serpentina
    a = k * PI / 2.5
    pts.append(C(0.24 + 0.012 * math.cos(a), 0.012 * math.sin(a), CZ + 0.2 + k * 0.012))
pts += [C(0.27, -0.04, 0.655), C(0.33, -0.08, 0.645)]
varrer(P.B('cobre', True), pts, 0.006, 8)

# ---------------------------------------------------------------- coluna, levitação e transmissor (leste)
XC, YC = 0.33, -0.04
XV = XC - 0.03                                                               # eixo da coluna de vidro
caixa_de(P.B('concreto'), C(XC - 0.08, YC - 0.08, 0), C(XC + 0.08, YC + 0.08, 0.05))
caixa_de(P.B('ferro'), C(XC - 0.06, YC - 0.06, 0.05), C(XC + 0.06, YC + 0.06, 0.06))
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(P.B('aco'), C(XC + sx * 0.045, YC + sy * 0.045, 0.066), 0.008, 0.01, Z, lados=6)
tubo(P.B('galv') if 'galv' in M else P.B('aco', True), C(XC + 0.03, YC + 0.03, 0.06), C(XC + 0.03, YC + 0.03, 0.82), 0.016, 14)
# coluna de vidro (régua de 10 marcas) com anéis de campo e a bolha
Z0V, Z1V = 0.16, 0.62
for zz in (Z0V - 0.02, Z1V + 0.02):
    cil(P.B('ferro', True), C(XV, YC, zz), 0.035, 0.04, Z, lados=24)
    caixa_de(P.B('ferro'), C(XV + 0.03, YC + 0.0, zz - 0.01), C(XC + 0.03, YC + 0.03, zz + 0.01))   # braçadeira ao poste
tubo(P.B('vidro', True), C(XV, YC, Z0V), C(XV, YC, Z1V), 0.026, 24)
for k in range(11):
    zz = Z0V + (Z1V - Z0V) * k / 10
    caixa_de(P.B('preto'), C(XV - 0.045, YC - 0.004, zz - 0.002), C(XV - 0.038, YC + 0.004, zz + 0.002))
tubo(P.B('aco'), C(XV - 0.048, YC, Z0V), C(XV - 0.048, YC, Z1V), 0.003, 6)                            # régua
aneis = []
for k in range(4):
    e = bpy.data.objects.new('sensor_tanque_anel%d' % k, None)
    sc.collection.objects.link(e)
    e.location = C(XV, YC, Z0V + 0.06 + k * 0.11)
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 0.034, 0.0035, 32, 6)
    o = base3d.obj('sensor_tanque_anel%d_luz' % k, bm, 'anel')
    o.parent = e
    aneis.append(e)
bolha = bpy.data.objects.new('sensor_tanque_bolha', None)
sc.collection.objects.link(bolha)
bolha.location = C(XV, YC, Z0V + 0.2)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.016)
suavizar(base3d.obj('sensor_tanque_bolha_luz', bm, 'bolha')).parent = bolha
# transmissor no topo: caixa, visor, prensa-cabos, antena do canal
ZT = 0.66
caixa_de(P.B('cinza'), C(XC - 0.06, YC - 0.05, ZT), C(XC + 0.07, YC + 0.06, ZT + 0.12))
caixa_de(P.B('borracha'), C(XC - 0.056, YC - 0.052, ZT + 0.004), C(XC + 0.066, YC - 0.05, ZT + 0.116))
caixa_de(P.B('cinza'), C(XC - 0.054, YC - 0.058, ZT + 0.006), C(XC + 0.064, YC - 0.052, ZT + 0.114))
caixa_de(P.B('preto'), C(XC - 0.03, YC - 0.0585, ZT + 0.05), C(XC + 0.04, YC - 0.058, ZT + 0.09))
for k in range(5):
    caixa_de(P.B('visor'), C(XC - 0.025 + k * 0.013, YC - 0.0588, ZT + 0.06), C(XC - 0.017 + k * 0.013, YC - 0.0585, ZT + 0.08))
for xx in (XC - 0.045, XC + 0.055):
    for zz in (ZT + 0.015, ZT + 0.105):
        cil(P.B('aco'), C(xx, YC - 0.059, zz), 0.004, 0.003, Y, lados=6)
cil(P.B('aco'), C(XC + 0.0, YC - 0.04, ZT - 0.008), 0.009, 0.016, Z, lados=6)                     # prensa-cabo (impulso)
caixa_de(P.B('tinta'), C(XC - 0.045, YC - 0.0589, ZT + 0.02), C(XC + 0.0, YC - 0.0586, ZT + 0.035))
tubo(P.B('aco'), C(XC + 0.05, YC + 0.04, ZT + 0.12), C(XC + 0.05, YC + 0.04, ZT + 0.30), 0.003, 6)  # antena
bm = bmesh.new()
toro(bm, C(XC + 0.05, YC + 0.04, ZT + 0.26), 0.012, 0.003, 20, 6)
base3d.obj('sensor_tanque_canal', bm, 'canal')
cil(P.B('borracha', True), C(XC + 0.05, YC + 0.04, ZT + 0.31), 0.006, 0.02, Z, lados=10)
# eletroduto da caixa até o chão
cil(P.B('aco'), C(XC + 0.06, YC + 0.0, ZT - 0.008), 0.009, 0.016, Z, lados=6)
pts = [C(XC + 0.06, YC, ZT - 0.016), C(XC + 0.08, YC, ZT - 0.2), C(XC + 0.1, YC + 0.06, 0.15), C(XC + 0.1, YC + 0.09, 0.0)]
varrer(P.B('eletroduto') if 'eletroduto' in M else P.B('borracha', True), bezier(*pts, 12), 0.009, 12)
g['fios'](P, C(XC + 0.07, YC + 0.05, ZT + 0.02), C(XC + 0.03, YC + 0.07, ZT - 0.08), 2, 0.03)
P.fim()

# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    nivel = 0.5 + 0.38 * math.sin(2 * PI * fr)
    bolha.location = C(XV, YC, Z0V + 0.02 + (Z1V - Z0V - 0.04) * nivel)
    bolha.keyframe_insert('location', frame=q)
    for k, e in enumerate(aneis):
        s = 1.0 + 0.06 * math.sin(2 * PI * (fr * 4 + k * 0.25))
        e.scale = (s, s, 1)
        e.keyframe_insert('scale', frame=q)
    L16.chave_luz(LUZ, 'anel', 6.0 + 3.0 * math.sin(2 * PI * fr * 4), q)
    L16.chave_luz(LUZ, 'bolha', 8.0, q)
    L16.chave_luz(LUZ, 'visor', 5.0 if (q // 6) % 4 else 1.0, q)
    L16.chave_luz(LUZ, 'canal', 4.0 + 2.0 * math.sin(2 * PI * fr * 2), q)
L16.gotas_e_ponteiros(g, QUADROS)
L16.linear()
cam = L16.cena()
L16.fotos(MODO, cam, {
    'sensor_tanque_0': ((1.6, -1.6, 1.2), (0.1, 0, 0.4), 32, 1200, 1100),
    'sensor_tanque_perto': ((0.85, -0.75, 0.7), (0.3, -0.04, 0.5), 30, 1200, 1100),
})
print('SENSOR TANQUE ok')
