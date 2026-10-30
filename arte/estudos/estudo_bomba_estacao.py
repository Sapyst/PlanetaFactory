"""Estudo isolado (fora do jogo): BOMBA DE ESTAÇÃO (bomba_estacao, 1×1, até ~0,95 m), lote 16.
Fica encostada na estação de trem (lado SUL da peça = a estação) e liga o tanque dela à rede de canos (cano pela borda
NORTE, eixo a 0,34 m, flange igual à dos canos do estudo_canos.py, de onde vêm os materiais e as peças prontas: flange
aparafusada, suporte, manômetro, remendo, número de série).
- Bomba em linha de eixo vertical: corpo de ferro fundido no oeste, motor de pé com aletas, tampa da ventoinha gradeada
  no topo (a ventoinha gira), olhal de içamento, caixa de ligação com eletroduto descendo até a laje.
- Válvula de inversão de 4 vias no meio (a mesma bomba enche ou esvazia o tanque da estação): bloco fundido com 4
  bocas — rede (norte), estação (sul), sucção e recalque da bomba (oeste, por dois cotovelos) — e atuador elétrico no
  leste com setas de LED (âmbar = carregando o trem, violeta = descarregando).
- Braço de carga articulado no sul: subida com visor de fluxo, junta giratória de dois anéis, contrapeso amarelo
  listrado para o norte, braço inclinado descendo até o acoplador de engate seco na borda sul (a boca encosta na
  estação), com três garras hidráulicas e mangueira até a unidade hidráulica.
- Skid de aço sobre laje de concreto com chumbadores, bandeja de gotejamento com óleo, caixa de comando da IA com
  LEDs e antena curta, cabos em eletrocalha, remendo aparafusado, pintura amarela gasta e grafite.
Animação 4 s: ventoinha do motor, ponteiro do manômetro tremendo, setas do atuador correndo (âmbar), fluxo no visor,
LEDs da caixa, pingo no acoplador.
Uso: blender -b --python estudo_bomba_estacao.py -- foto | nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
MODO = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

# ------------------------------------------------------------------ materiais e peças do estudo dos canos (sem a cena)
_base = os.path.join(AQUI, 'estudo_canos.py')
sys.argv = [sys.argv[0], '--python', _base, '--', 'nada']
g = {'__name__': '__main__', '__file__': _base}
exec(compile(open(_base, encoding='utf-8').read(), _base, 'exec'), g)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
g['GOTAS'].clear()
g['GAUGES'].clear()
import base3d, mats
from base3d import caixa, caixa_de, cil, tubo, bezier, mangueira, mancha

PI = math.pi
Z = Vector((0, 0, 1))
X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
sc = bpy.context.scene
random.seed(161)
QUADROS = g['QUADROS']
Peca, flange, manometro, suporte, remendo, serie = g['Peca'], g['flange'], g['manometro'], g['suporte'], g['remendo'], g['serie']
varrer, toro, chapa_arco, suavizar, obj = g['varrer'], g['toro'], g['chapa_arco'], g['suavizar'], base3d.obj
CZ, R, RF, EF = g['CZ'], g['R'], g['RF'], g['EF']
M = base3d.M
LUZ = {}


def luz(chave, nome, cor, forca=0.0):
    m = g['emissivo'](nome, cor, forca)
    LUZ[chave] = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    M[chave] = m


luz('seta_c', 'Seta de carga', (1.0, 0.45, 0.04))
luz('seta_d', 'Seta de descarga', (0.55, 0.12, 1.0))
luz('led1', 'LED da caixa 1', (0.15, 1.0, 0.25))
luz('led2', 'LED da caixa 2', (1.0, 0.45, 0.04))
M['cinza'] = mats.material('Cinza trocado', (0.33, 0.34, 0.33), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.5)
M['eletroduto'] = mats.material('Eletroduto', (0.12, 0.12, 0.13), 0, 0.6, pintura=False, sujeira=1.0, desgaste=0.0)
for _k, _n, _c in (('fio_v', 'Fio vermelho', (0.5, 0.04, 0.03)), ('fio_a', 'Fio azul', (0.04, 0.1, 0.45)),
                   ('fio_m', 'Fio amarelo', (0.6, 0.45, 0.03))):
    if _k not in M:
        M[_k] = mats.material(_n, _c, 0, 0.5, pintura=False, sujeira=0.6)
M['oxido'] = mats.material('Primer vermelho', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.6)
for k in ('cinza', 'eletroduto', 'oxido'):
    g['rustico'](M[k])

C = lambda x, y, z=CZ: Vector((x, y, z))


def curva(bm, a, da, b, db, r, n=12, lados=24):
    """Tubo de a (direção da) até b (chegando na direção db), bézier cúbica: cotovelo de raio longo."""
    a, b = Vector(a), Vector(b)
    da, db = Vector(da).normalized(), Vector(db).normalized()
    m = (b - a).length * 0.45
    varrer(bm, bezier(a, a + da * m, b - db * m, b, n), r, lados)


# ------------------------------------------------------------------ a bomba de estação
P = Peca('bomba_est', 0, 0)
# laje e skid
caixa_de(P.B('concreto'), (-0.47, -0.47, 0), (0.47, 0.47, 0.06))
for sx in (-1, 1):
    caixa_de(P.B('grafite'), (sx * 0.42 - 0.03, -0.44, 0.06), (sx * 0.42 + 0.03, 0.44, 0.12))        # longarinas
for yy in (-0.34, 0.0, 0.34):
    caixa_de(P.B('grafite'), (-0.39, yy - 0.025, 0.07), (0.39, yy + 0.025, 0.11))                 # travessas
caixa_de(P.B('ferro'), (-0.45, -0.45, 0.12), (0.45, 0.45, 0.13))                                  # chapa do skid
for sx in (-1, 1):
    for sy in (-1, 1):
        p = Vector((sx * 0.42, sy * 0.41, 0.13))
        tubo(P.B('aco'), p - Z * 0.01, p + Z * 0.025, 0.007, 6)
        cil(P.B('aco'), p + Z * 0.008, 0.013, 0.012, lados=6)
# bandeja de gotejamento sob a bomba de lóbulos, com óleo
caixa_de(P.B('aco'), (-0.16, -0.04, 0.13), (0.16, 0.24, 0.135))
for (a, b) in (((-0.16, -0.04), (-0.155, 0.24)), ((0.155, -0.04), (0.16, 0.24)), ((-0.16, -0.04), (0.16, -0.035)),
               ((-0.16, 0.235), (0.16, 0.24))):
    caixa_de(P.B('aco'), (a[0], a[1], 0.135), (b[0], b[1], 0.16))
bm = bmesh.new()
mancha(bm, (0.02, 0.1), 0.1, 0.137)
obj('bomba_est_oleo', bm, 'oleo')

# ---------------------------------------------------------------- rede (norte) → bomba de lóbulos (reversível)
YP = 0.10                                                              # centro da bomba
flange(P, C(0, 0.5), Y)                                                # boca da rede na borda norte
tubo(P.B('cano', True), C(0, 0.47), C(0, YP + 0.15), R, 32)
flange(P, C(0, YP + 0.135), Y, pescoco=False)
suporte(P, C(0, 0.37), Y)
# corpo de dois lóbulos (eixos em x), tampa frontal aparafusada no oeste, bocas norte/sul
for zz in (CZ - 0.055, CZ + 0.055):
    cil(P.B('ferro', True), C(0, YP, zz), 0.085, 0.2, X, lados=36)
caixa_de(P.B('ferro'), C(-0.1, YP - 0.085, CZ - 0.055), C(0.1, YP + 0.085, CZ + 0.055))
for sg in (1, -1):
    cil(P.B('ferro', True), C(0, YP + sg * 0.105), 0.075, 0.04, Y, lados=28)
cil(P.B('ferro', True), C(0, YP - 0.135 + EF / 2), RF, EF, Y, lados=40)                   # flange da boca sul
for k in range(8):
    a = PI / 8 + k * PI / 4
    p = C(0, YP - 0.135) + Vector((math.cos(a), 0, math.sin(a))) * g['RB']
    cil(P.B('aco'), p + Y * (EF + 0.008), 0.019, 0.016, Y, lados=6)
caixa_de(P.B('ferro'), C(-0.115, YP - 0.08, CZ - 0.13), C(-0.10, YP + 0.08, CZ + 0.13))    # tampa frontal
for k in range(10):
    a = k * 2 * PI / 10
    cil(P.B('aco'), C(-0.118, YP + 0.065 * math.cos(a), CZ + 0.115 * math.sin(a)), 0.009, 0.008, X, lados=6)
for zz in (CZ - 0.055, CZ + 0.055):
    cil(P.B('aco', True), C(-0.12, YP, zz), 0.022, 0.012, X, lados=16)                       # porcas dos rotores
for sx in (-1, 1):                                                                           # pés
    caixa_de(P.B('ferro'), C(sx * 0.09 - 0.02, YP - 0.07, 0.16), C(sx * 0.09 + 0.02, YP + 0.07, CZ - 0.11))
caixa_de(P.B('ferro'), C(-0.12, YP - 0.08, 0.135), C(0.12, YP + 0.08, 0.16))
remendo(P, C(0, YP, CZ + 0.055), X, 0.085, math.radians(40), math.radians(120), 0.06)
serie(P, C(0, YP, CZ - 0.055), X, 0.085, math.radians(-110), 4, 0.022)
manometro(P, C(-0.05, YP + 0.12, CZ + 0.17), Vector((-1, 0, 0)), C(0, YP + 0.12, CZ + 0.07), 0.032)
# caixa de engrenagens sincronizadoras (leste) com respiro e visor de óleo
caixa_de(P.B('grafite'), C(0.10, YP - 0.09, CZ - 0.12), C(0.20, YP + 0.09, CZ + 0.12))
for zz in (CZ - 0.105, CZ + 0.105):
    for yy in (YP - 0.075, YP + 0.075):
        cil(P.B('aco'), C(0.202, yy, zz), 0.007, 0.006, X, lados=6)
cil(P.B('vidro', True), C(0.201, YP - 0.04, CZ - 0.06), 0.014, 0.004, X, lados=16)
cil(P.B('oleo', True), C(0.2, YP - 0.04, CZ - 0.065), 0.012, 0.002, X, lados=16)
tubo(P.B('aco'), C(0.15, YP + 0.05, CZ + 0.12), C(0.15, YP + 0.05, CZ + 0.17), 0.008, 8)
cil(P.B('ferro', True), C(0.15, YP + 0.05, CZ + 0.18), 0.016, 0.02, Z, lados=12)
# painel de direção sobre a caixa: setas de LED (âmbar = rede → trem, violeta = trem → rede)
caixa_de(P.B('cinza'), C(0.105, YP - 0.08, CZ + 0.12), C(0.195, YP + 0.02, CZ + 0.14))
for chave, xx, sg in (('seta_c', 0.13, -1), ('seta_d', 0.17, 1)):
    bm = P.B(chave)
    pts = [(-0.006, 0.02), (0.006, 0.02), (0.006, -0.005), (0.014, -0.005), (0.0, -0.025), (-0.014, -0.005), (-0.006, -0.005)]
    vs = [bm.verts.new(C(xx + px, YP - 0.03 + sg * -py, CZ + 0.1412)) for (px, py) in pts]
    bm.faces.new(vs if sg < 0 else list(reversed(vs)))
# acoplamento com proteção listrada e motor deitado (leste)
ZE = CZ + 0.055                                                              # eixo do motor
cil(P.B('amarelo', True), C(0.24, YP, ZE), 0.065, 0.08, X, lados=28)
cil(P.B('listras', True), C(0.24, YP, ZE), 0.0655, 0.03, X, lados=28)
cil(P.B('grafite', True), C(0.36, YP, ZE), 0.085, 0.16, X, lados=36)
for k in range(14):
    a = k * 2 * PI / 14
    if math.sin(a) < -0.6:
        continue                                                              # sem aleta embaixo (pés)
    caixa(P.B('grafite'), C(0.36, YP + 0.092 * math.cos(a), ZE + 0.092 * math.sin(a)), (0.13, 0.016, 0.004),
          Matrix.Rotation(a + PI / 2, 3, 'X'))
for xx in (0.30, 0.42):                                                       # pés do motor
    caixa_de(P.B('grafite'), C(xx - 0.02, YP - 0.07, 0.135), C(xx + 0.02, YP + 0.07, ZE - 0.07))
    for sy in (-1, 1):
        cil(P.B('aco'), C(xx, YP + sy * 0.055, 0.14), 0.008, 0.01, Z, lados=6)
varrer(P.B('ferro', True), [C(0.44, YP, ZE), C(0.475, YP, ZE)], 0.088, 36)        # tampa da ventoinha
for k in range(4):
    toro(P.B('aco'), C(0.477, YP, ZE), 0.02 + 0.02 * k, 0.0022, 28, 4, X)
for k in range(6):
    a = k * PI / 3
    tubo(P.B('aco'), C(0.477, YP, ZE), C(0.477, YP + 0.086 * math.cos(a), ZE + 0.086 * math.sin(a)), 0.0022, 4)
toro(P.B('aco'), C(0.36, YP, ZE + 0.105), 0.02, 0.006, 20, 6, Y)                  # olhal de içamento
ventoinha = bpy.data.objects.new('bomba_est_ventoinha', None)
sc.collection.objects.link(ventoinha)
ventoinha.location = C(0.458, YP, ZE)
Vt = Peca('bomba_est_vent', 0, 0)
cil(Vt.B('ferro', True), Vector((0, 0, 0)), 0.018, 0.02, X, lados=12)
for k in range(7):
    a = k * 2 * PI / 7
    caixa(Vt.B('ferro'), Vector((0, 0.045 * math.cos(a), 0.045 * math.sin(a))), (0.004, 0.06, 0.018),
          Matrix.Rotation(a, 3, 'X') @ Matrix.Rotation(0.4, 3, 'Y'))
Vt.fim()
sc.objects['bomba_est_vent_ferro'].parent = ventoinha
# caixa de ligação no motor e eletroduto descendo até a laje (leste)
caixa_de(P.B('cinza'), C(0.32, YP - 0.04, ZE + 0.08), C(0.40, YP + 0.04, ZE + 0.14))
for xx in (0.33, 0.39):
    for yy in (YP - 0.03, YP + 0.03):
        cil(P.B('aco'), C(xx, yy, ZE + 0.142), 0.004, 0.004, Z, lados=6)
cil(P.B('aco'), C(0.36, YP - 0.045, ZE + 0.11), 0.01, 0.012, Y, lados=6)
pts = [C(0.36, YP - 0.05, ZE + 0.11), C(0.36, YP - 0.14, ZE + 0.11), C(0.43, YP - 0.2, 0.25), C(0.43, YP - 0.22, 0.135)]
varrer(P.B('eletroduto', True), bezier(pts[0], pts[1], pts[2], pts[3], 10), 0.01, 12)
cil(P.B('aco'), C(0.43, YP - 0.22, 0.14), 0.015, 0.012, Z, lados=6)
# boca sul → redução → braço de carga
tubo(P.B('cano', True), C(0, YP - 0.135), C(0, YP - 0.17), R, 32)
cil(P.B('cano', True), C(0, YP - 0.195), R, 0.05, Y, lados=32, r2=0.07)
YV = YP - 0.10                                                                # ponto de partida do braço (YV − 0,12)
# ---------------------------------------------------------------- braço de carga (sul) até o acoplador na borda
YR = -0.16                                                                 # subida
tubo(P.B('cano', True), C(0, YP - 0.22), C(0, YR - 0.02), 0.07, 28)
curva(P.B('cano', True), C(0, YR - 0.02), -Y, C(0, YR - 0.10, CZ + 0.12), Z, 0.07, 10)
tubo(P.B('cano', True), C(0, YR - 0.10, CZ + 0.12), C(0, YR - 0.10, 0.56), 0.07, 28)
# visor de fluxo na subida (vidro + fluxo de seiva)
for zz in (CZ + 0.17, CZ + 0.27):
    cil(P.B('ferro', True), C(0, YR - 0.10, zz), 0.09, 0.02, Z, lados=28)
for k in range(4):
    a = k * PI / 2 + PI / 4
    tubo(P.B('aco'), C(0.08 * math.cos(a), YR - 0.10 + 0.08 * math.sin(a), CZ + 0.16),
         C(0.08 * math.cos(a), YR - 0.10 + 0.08 * math.sin(a), CZ + 0.28), 0.005, 6)
tubo(P.B('vidro', True), C(0, YR - 0.10, CZ + 0.18), C(0, YR - 0.10, CZ + 0.26), 0.074, 32)
visor = bmesh.new()
cil(visor, Vector((0, 0, 0.04)), 0.064, 0.08, lados=28)
vo = suavizar(obj('bomba_est_seiva', visor, 'fluxo'))
vo.location = C(0, YR - 0.10, CZ + 0.18)
# junta giratória: dois anéis com rolamento à vista e graxeira
ZJ = 0.60
for zz in (ZJ - 0.04, ZJ + 0.0):
    cil(P.B('ferro', True), C(0, YR - 0.10, zz), 0.095, 0.03, Z, lados=32)
toro(P.B('cromo'), C(0, YR - 0.10, ZJ - 0.02), 0.095, 0.006, 32, 6)
cil(P.B('aco'), C(0.09, YR - 0.10, ZJ - 0.02), 0.006, 0.02, X, lados=6)
# cabeça da junta: cotovelo para o sul (braço) e para o norte (contrapeso)
cil(P.B('ferro', True), C(0, YR - 0.10, ZJ + 0.06), 0.08, 0.1, Z, lados=28)
A0 = C(0, YR - 0.10, ZJ + 0.06)
B0 = C(0, -0.43, 0.43)                                                     # cotovelo de descida do braço
curva(P.B('cano', True), A0 + Vector((0, -0.05, 0)), -Y, B0, (B0 - A0).normalized(), 0.06, 10)
curva(P.B('cano', True), B0, (B0 - A0).normalized(), C(0, -0.43, 0.30), -Z, 0.06, 10)
# acoplador de engate seco: corpo, flange na borda sul, garras hidráulicas
cil(P.B('ferro', True), C(0, -0.43, 0.27), 0.075, 0.06, Z, lados=28)
curva(P.B('cano', True), C(0, -0.43, 0.24), -Z, C(0, -0.47, CZ - 0.12), -Y, 0.055, 8)
cil(P.B('ferro', True), C(0, -0.49, CZ - 0.12), 0.09, 0.02, Y, lados=32)                      # face na borda
cil(P.B('borracha', True), C(0, -0.4995, CZ - 0.12), 0.07, 0.002, Y, lados=32)
for k in range(3):
    a = PI / 2 + k * 2 * PI / 3
    d = Vector((math.cos(a), 0, math.sin(a)))
    p0 = C(0, -0.46, CZ - 0.12) + d * 0.075
    caixa(P.B('amarelo'), p0 + d * 0.02, (0.03, 0.06, 0.02), Matrix.Rotation(-a + PI / 2, 3, 'Y'))
    tubo(P.B('cromo'), p0 + d * 0.02 + Vector((0, 0.03, 0)), p0 + d * 0.02 + Vector((0, 0.09, 0)), 0.007, 8)
    tubo(P.B('amarelo'), p0 + d * 0.02 + Vector((0, 0.09, 0)), p0 + d * 0.02 + Vector((0, 0.15, 0)), 0.011, 10)
# contrapeso: braço curto para o norte com placas listradas
caixa_de(P.B('ferro'), C(-0.03, YR - 0.05, ZJ + 0.09), C(0.03, YR + 0.16, ZJ + 0.12))
caixa_de(P.B('amarelo'), C(-0.09, YR + 0.10, ZJ + 0.05), C(0.09, YR + 0.22, ZJ + 0.17))
caixa_de(P.B('listras'), C(-0.0905, YR + 0.10, ZJ + 0.08), C(0.0905, YR + 0.221, ZJ + 0.12))
for sx in (-1, 1):
    cil(P.B('aco'), C(sx * 0.07, YR + 0.16, ZJ + 0.172), 0.01, 0.008, Z, lados=6)
# unidade hidráulica das garras (sudoeste) e mangueiras até as garras
caixa_de(P.B('grafite'), C(-0.40, -0.40, 0.13), C(-0.22, -0.22, 0.25))
cil(P.B('amarelo', True), C(-0.31, -0.31, 0.29), 0.05, 0.08, Z, lados=24)                     # reservatório
cil(P.B('ferro', True), C(-0.31, -0.31, 0.335), 0.02, 0.012, Z, lados=12)
for k, xx in enumerate((-0.065, 0.065)):
    a = C(-0.22, -0.33 + 0.05 * k, 0.21)
    b = C(xx, -0.31, CZ - 0.05 + (0.1 if k else 0.0))
    mangueira(P.B('borracha'), bezier(a, a + Vector((0.1, 0, 0.04)), b + Vector((-0.02, 0, 0.12)), b, 10), 0.009)
# caixa de comando da IA (noroeste): LEDs, antena curta, cabo correndo sob o cano até a caixa de engrenagens
caixa_de(P.B('cinza'), C(-0.42, 0.20, 0.13), C(-0.22, 0.42, 0.40))
caixa_de(P.B('cinza'), C(-0.22, 0.22, 0.15), C(-0.216, 0.40, 0.38))
for zz, chave in ((0.34, 'led1'), (0.30, 'led2')):
    cil(P.B('preto'), C(-0.215, 0.38, zz), 0.008, 0.003, X, lados=12)
    bmesh.ops.create_icosphere(P.B(chave), subdivisions=2, radius=0.005, matrix=Matrix.Translation(C(-0.213, 0.38, zz)))
for zz in (0.17, 0.36):
    for yy in (0.24, 0.38):
        cil(P.B('aco'), C(-0.214, yy, zz), 0.005, 0.004, X, lados=6)
tubo(P.B('aco'), C(-0.38, 0.38, 0.40), C(-0.38, 0.38, 0.60), 0.004, 6)
cil(P.B('borracha', True), C(-0.38, 0.38, 0.61), 0.008, 0.02, Z, lados=10)
caixa_de(P.B('tinta'), C(-0.2158, 0.25, 0.18), C(-0.2155, 0.33, 0.21))
for k in range(6):                                                              # venezianas no oeste da caixa
    zz = 0.20 + k * 0.03
    caixa(P.B('cinza'), C(-0.424, 0.31, zz), (0.008, 0.16, 0.012), Matrix.Rotation(0.5, 3, 'Y'))
cil(P.B('aco'), C(-0.32, 0.20, 0.36), 0.01, 0.012, Y, lados=6)                  # prensa-cabo e cabo da antena
caixa_de(P.B('adesivo') if 'adesivo' in M else P.B('amarelo'), C(-0.40, 0.198, 0.30), C(-0.34, 0.2, 0.36))
pts = [C(-0.22, 0.30, 0.17), C(-0.05, 0.30, 0.17), C(0.10, 0.28, 0.17), C(0.15, 0.20, 0.20)]
varrer(P.B('eletroduto', True), bezier(pts[0], pts[1], pts[2], pts[3], 12), 0.009, 12)
cil(P.B('aco'), C(0.15, YP + 0.094, 0.21), 0.012, 0.012, Y, lados=6)
remendo(P, C(0, 0.40), Y, R, math.radians(30), math.radians(110), 0.06)
serie(P, C(0, 0.30), Y, R, math.radians(150), 5)
P.fim()

# pingo no acoplador e mancha de seiva no chão (encosta na estação)
g['pingo'](Peca('bomba_est_pingo', 0, 0), C(0, -0.48, CZ - 0.21), 'gota', 1, r_poca=0.06)
bm = bmesh.new()
mancha(bm, (0.05, -0.3), 0.12, 0.131)
obj('bomba_est_derrame', bm, 'derramada')
g['halo'](Vector((-0.25, 0.14, 0)), 0.11, 0.139)

# ------------------------------------------------------------------ animação (laço de 4 s)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    ventoinha.rotation_euler = (0, 0, 2 * PI * 12 * fr)
    ventoinha.keyframe_insert('rotation_euler', frame=q)
    passo = (q - 1) // 6 % 4
    inp = LUZ['seta_c'].inputs['Emission Strength']
    inp.default_value = 9.0 if passo in (0, 1) else 1.5
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['seta_d'].inputs['Emission Strength']
    inp.default_value = 0.08
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['led1'].inputs['Emission Strength']
    inp.default_value = 6.0 if (q // 8) % 2 == 0 else 0.2
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['led2'].inputs['Emission Strength']
    inp.default_value = 5.0
    inp.keyframe_insert('default_value', frame=q)
for e, n, fase in g['GAUGES']:
    for q in range(1, QUADROS + 1):
        e.rotation_mode = 'QUATERNION'
        e.rotation_quaternion = n.to_track_quat('Z', 'Y') @ Matrix.Rotation(fase + 0.05 * math.sin(q * 1.7), 4, 'Z').to_quaternion()
        e.keyframe_insert('rotation_quaternion', frame=q)
for p, mat, vezes, fase in g['GOTAS']:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.009)
    o = obj('gota', bm, mat)
    for q in range(1, QUADROS + 1):
        u = ((q - 1) / QUADROS * vezes + fase) % 1.0
        t = max(0.0, u - 0.6) / 0.4 * 0.45
        o.location = p - Z * (0.011 + 4.9 * t * t)
        o.scale = (0.85, 0.85, 1.25) if u > 0.3 else (0.05 + u, 0.05 + u, 0.05 + u)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
for o in list(sc.objects) + list(bpy.data.materials):
    ad = o.node_tree.animation_data if isinstance(o, bpy.types.Material) and o.node_tree else getattr(o, 'animation_data', None)
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
cd = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.clip_start = 0.01


def foto(nome, pos, alvo, lente, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lente
    sc.render.filepath = os.path.join(AQUI, nome + '.png')
    bpy.ops.render.render(write_still=True)


FOTOS = {
    'bomba_estacao_0': ((1.7, -1.9, 1.4), (0, 0, 0.4), 32, 1200, 1100),
    'bomba_estacao_1': ((-1.6, 1.9, 1.5), (0, 0, 0.4), 32, 1200, 1100),
    'bomba_estacao_perto': ((0.75, -1.05, 0.75), (0.0, -0.3, 0.42), 30, 1200, 1100),
}
if MODO in ('foto', 'teste'):
    sc.cycles.samples = 128 if MODO == 'foto' else 24
    sc.frame_set(1)
    for nome, (pos, alvo, lente, rx, ry) in FOTOS.items():
        foto(nome, pos, alvo, lente, rx if MODO == 'foto' else rx // 2, ry if MODO == 'foto' else ry // 2)
print('BOMBA ESTACAO ok')
