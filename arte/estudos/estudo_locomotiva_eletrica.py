"""Estudo isolado (fora do jogo): LOCOMOTIVA ELÉTRICA (locomotiva_eletrica, 3 m sobre trilho), lote 16.
A locomotiva autônoma aprovada (estudo_trem.py: nariz blindado de sensores, capô com portas de acesso, grades,
ventiladores, truques com motores de tração e anel de campo, engates, mangueiras) montada por este script com o que
faz dela ELÉTRICA (pesquisa trem_eletrico: 2× velocidade, sem poluição):
- Sem escapamento, sem tampa basculante, sem fumaça e sem fuligem do diesel: o teto ganha a CAIXA DE RESISTORES de
  frenagem (grelhas de fita em venezianas, cantoneiras, parafusos) e duas buchas de porcelana marrom com hastes de
  cobre que levam a energia do trilho para o inversor; cabo grosso em eletrocalha correndo pelo teto.
- Sapatas coletoras nos dois truques e nos dois lados (o terceiro trilho fica a 0,41 m do eixo, por fora do trilho de
  rolamento): braço isolado preso no quadro do truque, mola, sapata de ferro fundido que encosta POR BAIXO da cabeça
  do terceiro trilho, fusível em caixa e cabo trançado subindo para o corpo.
- Pintura de grafite azulado gasta (no lugar do amarelo do diesel) com faixa violeta da IA e raios de estêncil; o
  truque continua amarelo gasto.
- Na via do estudo, um terceiro trilho (perfil, faixa de contato, isoladores em pedestais, tampa amarela) para a
  sapata ter onde encostar.
O vagão de carga e o vagão-tanque seguem engatados atrás (contexto). Animação: a do estudo do trem (rodas, suspensão,
ventiladores, lidar, anel de campo) + faísca curta nas sapatas.
Uso: blender -b --python estudo_locomotiva_eletrica.py -- foto | nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
MODO = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

_base = os.path.join(AQUI, 'estudo_trem.py')
sys.argv = [sys.argv[0], '--python', _base, '--', 'nada']
g = {'__name__': '__main__', '__file__': _base}
exec(compile(open(_base, encoding='utf-8').read(), _base, 'exec'), g)
import base3d, mats
from base3d import caixa, caixa_de, cil, tubo, bezier, mangueira

PI = math.pi
Z = Vector((0, 0, 1))
X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
sc = bpy.context.scene
random.seed(1617)
M = g['M']
Z_TR = g['Z_TR']

# ------------------------------------------------------------------ o diesel sai
for n in [o.name for o in sc.objects]:
    o = bpy.data.objects.get(n)
    if o is None:
        continue
    if n.startswith('fumaca') or n.startswith('locomotiva_tampa_esc') or n in ('locomotiva_corpo_queimado',
                                                                                'locomotiva_corpo_fuligem_s'):
        for c in list(o.children_recursive):
            bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(sc.objects):                                  # a locomotiva vira locomotiva_eletrica
    if o.name == 'locomotiva' or o.name.startswith('locomotiva_'):
        o.name = 'locomotiva_eletrica' + o.name[len('locomotiva'):]

# ------------------------------------------------------------------ pintura elétrica
M['eletrico'] = mats.material('Grafite azulado', (0.12, 0.16, 0.2), 0, 0.42, ferrugem=0.5, desgaste=1.0, sujeira=0.95)
M['eletrico_gasto'] = mats.material('Grafite azulado gasto', (0.1, 0.13, 0.16), 0, 0.5, ferrugem=0.75, desgaste=1.0,
                                    sujeira=1.0)
M['violeta_tinta'] = mats.material('Faixa violeta', (0.3, 0.07, 0.5), 0, 0.45, desgaste=1.0, sujeira=0.9, ferrugem=0.3)
M['isolador'] = mats.material('Porcelana marrom', (0.22, 0.09, 0.04), 0, 0.15, pintura=False, sujeira=0.8, desgaste=0.0)
M['inox'] = mats.material('Faixa de contato', (0.66, 0.66, 0.68), 1.0, 0.18, pintura=False, ferrugem=0.1, sujeira=0.6,
                          escovado=True)
M['tampa'] = mats.material('Tampa de compósito', (0.68, 0.47, 0.06), 0, 0.55, desgaste=0.9, sujeira=1.0)
M['concreto'] = M.get('concreto') or mats.material('Concreto', (0.33, 0.32, 0.3), 0, 0.9, pintura=False, sujeira=0.8,
                                                   desgaste=0.0)
M['arco'] = g['emissivo']('Faísca da sapata', (0.75, 0.6, 1.0), 0.0, base=(0.1, 0.08, 0.14))
for o in sc.objects:
    if o.type == 'MESH' and o.name.startswith('locomotiva_eletrica_corpo_amarelo'):
        for s in o.material_slots:
            s.material = M['eletrico_gasto' if 'gasto' in o.name else 'eletrico']


def malha(nome, bm, mat, pai=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    me.materials.append(M[mat])
    if pai is not None:
        bpy.context.view_layer.update()
        o.parent = pai
        o.matrix_parent_inverse = pai.matrix_world.inverted()
    return o


class Lote:
    """Geometria no mundo, um objeto por material, filho de `pai` (fica na posição)."""
    def __init__(s, nome, pai):
        s.nome, s.pai, s.bms = nome, pai, {}

    def B(s, mat, liso=False):
        return s.bms.setdefault((mat, liso), bmesh.new())

    def fim(s):
        for (mat, liso), bm in s.bms.items():
            o = malha('%s_%s' % (s.nome, mat), bm, mat, s.pai)
            if liso:
                g['suavizar'](o)


corpo = sc.objects['locomotiva_eletrica_corpo']
ZT = Z_TR                                   # topo do trilho no mundo (z 0 do veículo)
YC = 3.0                                    # centro da locomotiva no mundo

# ------------------------------------------------------------------ faixa violeta e raios no capô
P = Lote('locomotiva_eletrica_corpo_faixa', corpo)
for sx in (-1, 1):
    x = sx * 0.3605
    for y0, y1 in ((1.72, 2.55), (3.70, 4.30)):
        bm = P.B('violeta_tinta')
        vs = [bm.verts.new(Vector((x, y, z))) for (y, z) in ((y0, 0.60), (y1, 0.60), (y1, 0.66), (y0, 0.66))]
        bm.faces.new(vs if sx > 0 else list(reversed(vs)))
    for yr in (2.25, 4.0):                                             # raio de estêncil (aviso de alta tensão)
        bm = P.B('tinta_branca')
        pts = [(yr - 0.03, 0.80), (yr + 0.005, 0.765), (yr - 0.005, 0.765), (yr + 0.03, 0.72), (yr - 0.002, 0.758),
               (yr + 0.008, 0.758)]
        vs = [bm.verts.new(Vector((sx * 0.3612, y, z))) for (y, z) in pts]
        bm.faces.new(vs if sx > 0 else list(reversed(vs)))
P.fim()

# ------------------------------------------------------------------ caixa de resistores e buchas no teto
P = Lote('locomotiva_eletrica_corpo_resistores', corpo)
ZR0 = 1.085                                                            # teto do capô (no mundo)
Y0R, Y1R = 2.86, 3.40
caixa_de(P.B('grafite'), (-0.20, Y0R, ZR0), (0.20, Y1R, ZR0 + 0.012))                    # base
for sx in (-1, 1):
    caixa_de(P.B('eletrico_gasto'), (sx * 0.20 - 0.012, Y0R, ZR0), (sx * 0.20, Y1R, ZR0 + 0.10))   # laterais
    for k in range(9):                                                                 # venezianas
        y = Y0R + 0.04 + k * 0.055
        caixa(P.B('grafite'), Vector((sx * 0.206, y, ZR0 + 0.055)), (0.006, 0.04, 0.07),
              Matrix.Rotation(sx * 0.5, 3, 'Y'))
caixa_de(P.B('grafite'), (-0.19, Y0R, ZR0 + 0.012), (0.19, Y0R + 0.012, ZR0 + 0.10))
caixa_de(P.B('grafite'), (-0.19, Y1R - 0.012, ZR0 + 0.012), (0.19, Y1R, ZR0 + 0.10))
for k in range(11):                                                                    # grelha de fitas por cima
    x = -0.18 + k * 0.036
    caixa_de(P.B('ferro'), (x - 0.004, Y0R + 0.015, ZR0 + 0.095), (x + 0.004, Y1R - 0.015, ZR0 + 0.103))
for y in (Y0R + 0.10, Y0R + 0.27, Y1R - 0.10):
    caixa_de(P.B('aco'), (-0.205, y - 0.008, ZR0 + 0.103), (0.205, y + 0.008, ZR0 + 0.11))
    for sx in (-1, 1):
        cil(P.B('aco'), Vector((sx * 0.19, y, ZR0 + 0.113)), 0.006, 0.005, lados=6)
caixa_de(P.B('fuligem_s') if 'fuligem_s' in M else P.B('ferro'), (-0.15, Y0R + 0.02, ZR0 + 0.1031), (0.05, Y0R + 0.2, ZR0 + 0.1035))
# buchas de porcelana com hastes de cobre (energia do trilho → inversor)
for sx in (-1, 1):
    b = Vector((sx * 0.12, 3.56, ZR0))
    cil(P.B('grafite', True), b + Z * 0.008, 0.035, 0.016, lados=20)
    cil(P.B('isolador', True), b + Z * 0.055, 0.02, 0.08, lados=20)
    for k in range(4):
        g['toro'](P.B('isolador'), b + Z * (0.03 + k * 0.018), 0.027, 0.004, nR=20, nr=6)
    tubo(P.B('cobre'), b + Z * 0.095, b + Z * 0.13, 0.006, 8)
    cil(P.B('cobre', True), b + Z * 0.13, 0.012, 0.01, lados=10)
cabo = [Vector((-0.12, 3.56, ZR0 + 0.13)), Vector((-0.05, 3.56, ZR0 + 0.15)), Vector((0.05, 3.56, ZR0 + 0.15)),
        Vector((0.12, 3.56, ZR0 + 0.13))]
mangueira(P.B('cabo_p'), bezier(*cabo, 10), 0.007)
# eletrocalha no teto: das buchas até a frente (inversor dentro do nariz)
caixa_de(P.B('aco'), (0.22, 3.42, ZR0), (0.27, 3.95, ZR0 + 0.025))
mangueira(P.B('cabo_p'), [Vector((0.12, 3.56, ZR0 + 0.012)), Vector((0.2, 3.5, ZR0 + 0.02)), Vector((0.245, 3.5, ZR0 + 0.02)),
                          Vector((0.245, 3.94, ZR0 + 0.02))], 0.008)
P.fim()

# ------------------------------------------------------------------ sapatas coletoras (2 truques × 2 lados)
XS0, XS1 = 0.383, 0.403                                 # sapata embaixo da cabeça do terceiro trilho (por dentro)
ZS1 = 0.0225                                            # face de contato (z do veículo: 0 = topo do trilho)
for i in (0, 1):
    tr = sc.objects['locomotiva_eletrica_truque%d' % i]
    yt = YC + (2 * i - 1) * 0.85
    P = Lote('locomotiva_eletrica_truque%d_sapata' % i, tr)
    for sx in (-1, 1):
        y0 = yt + (0.36 if i == 1 else -0.36)                          # na ponta de fora do quadro (além das rodas)
        a = Vector((sx * 0.345, y0, ZT + 0.07))
        caixa_de(P.B('ferro'), a + Vector((-0.012, -0.03, -0.005)), a + Vector((0.012, 0.03, 0.03)))     # mão no quadro
        xr = sx * 0.352                                                 # haste por dentro da tampa do terceiro trilho
        cil(P.B('isolador', True), Vector((xr, y0, ZT + 0.05)), 0.011, 0.03, Z, lados=16)         # isolador da haste
        for k in range(2):
            g['toro'](P.B('isolador'), Vector((xr, y0, ZT + 0.044 + k * 0.012)), 0.013, 0.0025, nR=16, nr=5)
        tubo(P.B('grafite'), Vector((xr, y0, ZT + 0.036)), Vector((xr, y0, ZT + ZS1 - 0.012)), 0.005, 8)
        tubo(P.B('grafite'), Vector((xr, y0, ZT + ZS1 - 0.012)), Vector((sx * XS1, y0, ZT + ZS1 - 0.012)), 0.0045, 8)
        g['toro'](P.B('aco'), Vector((xr, y0, ZT + 0.03)), 0.008, 0.0022, nR=12, nr=4)            # mola
        caixa_de(P.B('ferro'), Vector((sx * XS0 if sx > 0 else -XS1, y0 - 0.06, ZT + ZS1 - 0.008)),
                 Vector((sx * XS1 if sx > 0 else -XS0, y0 + 0.06, ZT + ZS1 - 0.0005)))            # sapata
        caixa_de(P.B('cobre'), Vector((sx * XS0 if sx > 0 else -XS1, y0 - 0.055, ZT + ZS1 - 0.0005)),
                 Vector((sx * XS1 if sx > 0 else -XS0, y0 + 0.055, ZT + ZS1)))                    # face gasta, pó de cobre
        # caixa do fusível no quadro e cabo trançado subindo para o corpo
        f = Vector((sx * 0.345, y0 + (0.08 if i == 0 else -0.08), ZT + 0.12))
        caixa_de(P.B('cinza'), f + Vector((-0.02, -0.03, -0.025)), f + Vector((0.02, 0.03, 0.025)))
        mangueira(P.B('cabo_p'), bezier(a + Z * 0.04, a + Z * 0.07, f - Z * 0.05, f - Z * 0.025, 8), 0.005)
    P.fim()
    bm = bmesh.new()
    for sx in (-1, 1):
        y0 = yt + (0.36 if i == 1 else -0.36)
        g['esfera'](bm, (sx * 0.39, y0 + 0.062, ZT + ZS1 - 0.004), 0.005, 6)
    malha('locomotiva_eletrica_truque%d_faisca' % i, bm, 'arco', tr)

# ------------------------------------------------------------------ terceiro trilho na via do estudo (contexto)
UT = 0.41
bm_a, bm_i, bm_t, bm_c, bm_x, bm_l = (bmesh.new() for _ in range(6))
L2 = g['L_VIA'] / 2
caixa_de(bm_a, (-UT - 0.024, -L2, ZT), (-UT + 0.024, L2, ZT + 0.007))
caixa_de(bm_a, (-UT - 0.005, -L2, ZT + 0.007), (-UT + 0.005, L2, ZT + 0.024))
caixa_de(bm_a, (-UT - 0.03, -L2, ZT + 0.024), (-UT + 0.03, L2, ZT + 0.032))
caixa_de(bm_x, (-UT - 0.03, -L2, ZT + 0.0225), (-UT + 0.03, L2, ZT + 0.024))
caixa_de(bm_t, (-UT - 0.045, -L2, ZT + 0.0335), (-UT + 0.045, L2, ZT + 0.039))
caixa_de(bm_t, (-UT - 0.048, -L2, ZT + 0.02), (-UT - 0.042, L2, ZT + 0.0335))
y = -L2 + 0.25
while y < L2:
    caixa_de(bm_c, (-UT - 0.05, y - 0.05, 0.0), (-UT + 0.05, y + 0.05, 0.075))
    cil(bm_i, Vector((-UT, y, 0.075 + 0.032)), 0.014, 0.064, lados=16)
    caixa_de(bm_a, (-UT - 0.024, y - 0.012, ZT - 0.006), (-UT + 0.024, y + 0.012, ZT))
    caixa_de(bm_a, (-UT - 0.034, y - 0.01, ZT), (-UT - 0.028, y + 0.01, ZT + 0.0335))
    y += 0.5
for bm, mt, nome in ((bm_a, 'aco', 'terceiro_aco'), (bm_i, 'isolador', 'terceiro_isolador'), (bm_t, 'tampa', 'terceiro_tampa'),
                     (bm_c, 'concreto', 'terceiro_pedestal'), (bm_x, 'inox', 'terceiro_contato')):
    malha(nome, bm, mt)
bm_l.free()

# ------------------------------------------------------------------ faísca piscando nas sapatas
pa = next(n for n in M['arco'].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
for q in range(1, g['QUADROS'] + 1):
    pa.inputs['Emission Strength'].default_value = 25.0 if q in (11, 12, 47, 80) else 0.0
    pa.inputs['Emission Strength'].keyframe_insert('default_value', frame=q)

if MODO == 'foto':
    sc.cycles.samples = 128
    for nome, (pos, alvo, lente, res, qd, solz) in {
        'locomotiva_eletrica_0': ((2.6, 0.6, 1.6), (0.0, 2.9, 0.55), 30, (1300, 1000), 1, -35),
        'locomotiva_eletrica_1': ((-2.4, 5.6, 1.7), (0.0, 3.0, 0.55), 30, (1300, 1000), 1, 40),
        'locomotiva_eletrica_sapata': ((-1.0, 1.35, 0.45), (-0.39, 2.05, 0.16), 30, (1300, 1000), 1, -35),
    }.items():
        g['so'].rotation_euler = (math.radians(50), 0, math.radians(solz))
        sc.frame_set(qd)
        sc.render.resolution_x, sc.render.resolution_y = res
        g['mirar'](pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
print('LOCOMOTIVA ELETRICA ok')
