"""Estudo isolado (fora do jogo): BAÚ DE ESTOQUE (bau_estoque, 1×1, até ~0,7 m), lote 16 — drones logísticos.
O baú 1×1 aprovado (estudo_baus.py: contêiner blindado de chapas corrugadas, escotilhas com pistões nos 4 lados,
sensores, barras de ocupação, campo de levitação por dentro) montado por este script, com o que faz dele o ESTOQUE dos
drones logísticos (o que sobra na garra vem para cá; o requisitante sem provedor é servido daqui):
- Teto vira PLATAFORMA DE POUSO: chapa xadrez aparafusada em volta da janela, alvo pintado (anel e cruz), anel de 8
  LEDs violeta, quatro balizas cônicas listradas nos cantos e faixa violeta na borda.
- ESCOTILHA DE TETO de duas folhas sobre a janela (abre para a garra do drone descer), com dobradiças, batentes e um
  pistãozinho por folha (camisa no teto, haste na orelha da folha).
- Farol de aproximação violeta num mastro curto no canto, cabo descendo pela quina até a caixa de junção do estudo.
- Amarelo do baú trocado por verde-oliva gasto (o estoque se lê de longe, entre os baús amarelos).
Animação 4 s: a do baú (escotilhas laterais, itens no campo) + escotilha do teto abrindo e fechando, LEDs do alvo
correndo, farol piscando.
Uso: blender -b --python estudo_bau_estoque.py -- foto | nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
MODO = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

_base = os.path.join(AQUI, 'estudo_baus.py')
sys.argv = [sys.argv[0], '--python', _base, '--', 'nada']
g = {'__name__': '__main__', '__file__': _base}
exec(compile(open(_base, encoding='utf-8').read(), _base, 'exec'), g)
import base3d, mats
from base3d import caixa, caixa_de, cil, tubo, bezier, mangueira

PI = math.pi
Z = Vector((0, 0, 1))
X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
sc = bpy.context.scene
random.seed(1622)
M = base3d.M
QUADROS = g['QUADROS'] if 'QUADROS' in g else 96
col = bpy.data.collections['bau']

# fica só o baú 1×1 (o grande e o que é dele saem)
for o in list(bpy.data.collections['bau_grande'].all_objects):
    if bpy.data.objects.get(o.name) is not None:
        bpy.data.objects.remove(o, do_unlink=True)

# ------------------------------------------------------------------ materiais
M['oliva'] = mats.material('Verde-oliva gasto', (0.2, 0.24, 0.1), 0, 0.45, desgaste=1.0, sujeira=0.95, ferrugem=0.55)
M['xadrez'] = mats.material('Chapa xadrez', (0.2, 0.2, 0.2), 0.9, 0.5, pintura=False, ferrugem=0.6, sujeira=1.0)
M['tinta_alvo'] = mats.material('Tinta do alvo', (0.72, 0.7, 0.62), 0, 0.6, desgaste=1.0, sujeira=1.0)
M['violeta_tinta'] = mats.material('Faixa violeta', (0.3, 0.07, 0.5), 0, 0.45, desgaste=1.0, sujeira=0.9, ferrugem=0.3)
LUZ = {}
for chave, nome, cor in (('alvo', 'LEDs do alvo', (0.55, 0.12, 1.0)), ('farol', 'Farol de aproximação', (0.6, 0.15, 1.0))):
    m = g['emissivo'](nome, cor, 0.0)
    LUZ[chave] = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    M[chave] = m
for o in col.all_objects:
    if o.type == 'MESH':
        for s in o.material_slots:
            if s.material and s.material.name.startswith('Amarelo'):
                s.material = M['oliva']


def obj(nome, bm, mat, liso=False, pai=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = base3d.obj(nome, bm, mat)
    col.objects.link(o)
    if liso:
        g['suavizar'](o) if 'suavizar' in g else None
    if pai is not None:
        o.parent = pai
    return o


def vazio(nome, loc):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    col.objects.link(e)
    e.location = loc
    return e


Cb = Vector((g['C_BAU'][0], g['C_BAU'][1], 0))
P = g['P_BAU']
ZT = P['Z1'] + 0.016                                      # em cima do teto e da grade da janela
JX, JY = P['jan'][0] / 2 + 0.01, P['jan'][1] / 2 + 0.01   # meia janela (com folga)
HW, HD = P['W'] / 2 - 0.03, P['D'] / 2 - 0.03

# ------------------------------------------------------------------ plataforma de pouso
bm = bmesh.new()
for (a, b) in (((-HW, -HD), (HW, -JY)), ((-HW, JY), (HW, HD)), ((-HW, -JY), (-JX, JY)), ((JX, -JY), (HW, JY))):
    caixa_de(bm, Cb + Vector((a[0], a[1], ZT)), Cb + Vector((b[0], b[1], ZT + 0.008)))
obj('bau_pouso_chapa', bm, 'xadrez')
bm = bmesh.new()
for (a, b) in (((-HW, -HD), (-HW + 0.03, HD)), ((HW - 0.03, -HD), (HW, HD))):             # cantoneiras de apoio
    caixa_de(bm, Cb + Vector((a[0], a[1], P['Z1'])), Cb + Vector((b[0], b[1], ZT)))
for sx in (-1, 1):
    for k in range(5):
        yy = -HD + 0.04 + k * (2 * HD - 0.08) / 4
        cil(bm, Cb + Vector((sx * (HW - 0.015), yy, ZT + 0.0095)), 0.006, 0.004, lados=6)
obj('bau_pouso_parafusos', bm, 'xadrez')
bm = bmesh.new()                                                                            # faixa violeta na borda
for (a, b) in (((-HW, -HD), (HW, -HD + 0.025)), ((-HW, HD - 0.025), (HW, HD))):
    caixa_de(bm, Cb + Vector((a[0], a[1], ZT + 0.008)), Cb + Vector((b[0], b[1], ZT + 0.0088)))
obj('bau_pouso_faixa', bm, 'violeta_tinta')
bm = bmesh.new()                                                                            # alvo: anel e cruz
n = 48
R0, R1 = 0.255, 0.275
for i in range(n):
    a0, a1 = 2 * PI * i / n, 2 * PI * (i + 1) / n
    if random.random() < 0.15:
        continue                                                                            # tinta falhada
    vs = [bm.verts.new(Cb + Vector((r * math.cos(a), r * math.sin(a), ZT + 0.0085))) for (r, a) in ((R0, a0), (R1, a0), (R1, a1), (R0, a1))]
    if all(abs(v.co.x - Cb.x) < HW and abs(v.co.y - Cb.y) < HD and not (abs(v.co.x - Cb.x) < JX and abs(v.co.y - Cb.y) < JY) for v in vs):
        bm.faces.new(vs)
for (a, b) in (((-HW + 0.04, -0.012), (-JX - 0.02, 0.012)), ((JX + 0.02, -0.012), (HW - 0.04, 0.012)),
               ((-0.012, -HD + 0.04), (0.012, -JY - 0.02)), ((-0.012, JY + 0.02), (0.012, HD - 0.04))):
    caixa_de(bm, Cb + Vector((a[0], a[1], ZT + 0.008)), Cb + Vector((b[0], b[1], ZT + 0.0086)))
obj('bau_pouso_alvo', bm, 'tinta_alvo')
bm = bmesh.new()                                                                            # 8 LEDs do alvo
bl = bmesh.new()
for k in range(8):
    a = k * PI / 4 + PI / 8
    p = Cb + Vector((0.30 * math.cos(a), 0.29 * math.sin(a), ZT + 0.008))
    cil(bm, p + Z * 0.004, 0.012, 0.008, lados=12)
    bmesh.ops.create_icosphere(bl, subdivisions=1, radius=0.006, matrix=Matrix.Translation(p + Z * 0.009))
obj('bau_pouso_ledbase', bm, 'xadrez')
obj('bau_pouso_leds', bl, 'alvo')
bm = bmesh.new()
bl = bmesh.new()
for sx in (-1, 1):                                                                          # balizas cônicas
    for sy in (-1, 1):
        p = Cb + Vector((sx * (HW - 0.035), sy * (HD - 0.045), ZT + 0.008))
        cil(bm, p + Z * 0.004, 0.026, 0.008, lados=16)
        cil(bm, p + Z * 0.04, 0.02, 0.064, lados=16, r2=0.006)
        cil(bl, p + Z * 0.035, 0.0155, 0.018, lados=16, r2=0.013)
obj('bau_pouso_balizas', bm, 'oliva', True)
obj('bau_pouso_balizas_listras', bl, 'listras' if 'listras' in M else 'oliva', True)

# ------------------------------------------------------------------ escotilha do teto (duas folhas sobre a janela)
folhas = []
for sx in (-1, 1):
    eixo = Cb + Vector((sx * JX, 0, ZT + 0.012))
    e = vazio('bau_escotilha%d' % (sx > 0), eixo)
    bm = bmesh.new()
    caixa_de(bm, Vector((-sx * JX if sx > 0 else 0.0, -JY, -0.004)), Vector((0.0 if sx > 0 else JX, JY, 0.004)))
    obj('bau_escotilha%d_folha' % (sx > 0), bm, 'oliva', pai=e)
    bm = bmesh.new()
    for k in range(3):                                                                      # nervuras
        yy = -JY + 0.04 + k * (2 * JY - 0.08) / 2
        caixa_de(bm, Vector((-sx * (JX - 0.01) if sx > 0 else 0.01, yy - 0.004, 0.004)), Vector((-0.01 if sx > 0 else JX - 0.01, yy + 0.004, 0.012)))
    obj('bau_escotilha%d_nervuras' % (sx > 0), bm, 'xadrez', pai=e)
    folhas.append((e, sx))
bm = bmesh.new()
for sx in (-1, 1):                                                                          # dobradiças fixas
    for yy in (-JY + 0.04, JY - 0.04):
        cil(bm, Cb + Vector((sx * JX, yy, ZT + 0.012)), 0.008, 0.04, Y, lados=12)
        caixa_de(bm, Cb + Vector((sx * JX - 0.01, yy - 0.02, ZT + 0.008)), Cb + Vector((sx * JX + sx * 0.02, yy + 0.02, ZT + 0.012)))
obj('bau_escotilha_dobradicas', bm, 'xadrez')

# ------------------------------------------------------------------ farol de aproximação (canto sudoeste) e cabo
FB = Cb + Vector((-HW + 0.05, -HD + 0.06, ZT + 0.008))
bm = bmesh.new()
cil(bm, FB + Z * 0.004, 0.02, 0.008, lados=12)
tubo(bm, FB, FB + Z * 0.13, 0.006, 8)
cil(bm, FB + Z * 0.13, 0.014, 0.008, lados=14)
for zz in (0.142, 0.17):
    g['toro'](bm, FB + Z * zz, 0.0125, 0.0018, 16, 4) if 'toro' in g else None
obj('bau_farol_mastro', bm, 'xadrez')
bm = bmesh.new()
cil(bm, FB + Z * 0.155, 0.012, 0.03, lados=14)
obj('bau_farol_luz', bm, 'farol', True)
bm = bmesh.new()
pts = [FB + Vector((0.012, 0, 0.02)), FB + Vector((0.025, 0.0, -0.005)), FB + Vector((0.025, 0.02, -0.02)),
       Cb + Vector((-HW + 0.06, -HD + 0.12, P['Z1'] - 0.02))]
mangueira(bm, bezier(*pts, 8), 0.004)
obj('bau_farol_cabo', bm, 'borracha' if 'borracha' in M else 'xadrez')

# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    ab = suave((fr - 0.25) / 0.12) * (1 - suave((fr - 0.62) / 0.12))
    for e, sx in folhas:
        e.rotation_euler = (0, sx * math.radians(100) * ab, 0)
        e.keyframe_insert('rotation_euler', frame=q)
    for chave, forca in (('alvo', 3.0 + 6.0 * (1.0 if (q // 3) % 2 == 0 else 0.3)),
                         ('farol', 12.0 if (q % 24) < 3 else 0.6)):
        LUZ[chave].inputs['Emission Strength'].default_value = forca
        LUZ[chave].inputs['Emission Strength'].keyframe_insert('default_value', frame=q)

if MODO in ('foto', 'teste'):
    sc.cycles.samples = 128 if MODO == 'foto' else 24
    g['quem']('bau') if 'quem' in g else None
    for nome, (pos, alvo, lente, res, qd) in {
        'bau_estoque_0': (Cb + Vector((1.5, -1.6, 1.3)), Cb + Vector((0, 0, 0.35)), 32, (1200, 1100), 40),
        'bau_estoque_teto': (Cb + Vector((0.6, -0.7, 1.3)), Cb + Vector((0, 0, 0.55)), 30, (1200, 1100), 48),
    }.items():
        sc.frame_set(qd)
        sc.render.resolution_x, sc.render.resolution_y = res if MODO == 'foto' else (res[0] // 2, res[1] // 2)
        g['mirar'](pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
print('BAU ESTOQUE ok')
