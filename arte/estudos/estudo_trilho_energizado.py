"""Estudo isolado (fora do jogo): TRILHO ENERGIZADO (trilho_energizado, 1×1), lote 16.
A via reta aprovada (estudo_trilhos.py: leito de brita, dormentes de concreto — um rachado, um de madeira —, trilhos de
perfil real, placas, grampos, talas) montada por este script nos dois retos do sul do estudo, com o TERCEIRO TRILHO
que dá energia à locomotiva elétrica (pesquisa trem_eletrico):
- Terceiro trilho no lado oeste, fora do trilho de rolamento (eixo a 0,41 m do eixo da via), contato por baixo: perfil
  de aço com faixa de contato de inox polida pelas sapatas da locomotiva, preso em isoladores de porcelana marrom
  (saias de chuva) sobre mãos-francesas aparafusadas na ponta dos dormentes (um a cada dois).
- Tampa de proteção por cima (tábua de compósito amarela gasta, listras de perigo e raios de estêncil), presa nos
  chapéus dos isoladores, rente à cabeça (a 0,18 m: o estrado dos trens passa por cima).
- Alimentação: eletroduto galvanizado saindo do chão na borda oeste, cabeçote de chuva, seccionadora com alavanca
  motorizada e luz violeta "energizado" no topo (onde o fio do poste chega), cabo grosso descendo até a orelha de
  cobre aparafusada na alma do terceiro trilho; cordoalha de cobre de aterramento até o trilho de rolamento.
- Sujeira: pó de cobre e fuligem de arco na faixa de contato, óleo, lama, ferrugem escorrendo dos parafusos.
Animação 4 s: luz "energizado" pulsando; faísca curta (luz de arco) piscando na orelha de cobre.
Uso: blender -b --python estudo_trilho_energizado.py -- foto | nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
MODO = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

_base = os.path.join(AQUI, 'estudo_trilhos.py')
sys.argv = [sys.argv[0], '--python', _base, '--', 'nada']
g = {'__name__': '__main__', '__file__': _base}
exec(compile(open(_base, encoding='utf-8').read(), _base, 'exec'), g)
import base3d, mats
from base3d import caixa_de, cil, tubo, bezier, mangueira

PI = math.pi
Z = Vector((0, 0, 1))
sc = bpy.context.scene
random.seed(1616)
toro, varrer, catmull, corrugado = g['toro'], g['varrer'], g['catmull'], g['corrugado']
Lote, Quadro, caixa_q, parafuso, decal = g['Lote'], g['Quadro'], g['caixa_q'], g['parafuso'], g['decal']
emissivo, principled, halo_em, mancha_em = g['emissivo'], g['principled'], g['halo_em'], g['mancha_em']
ZDT, ZTB, HT, UD, G = g['ZDT'], g['ZTB'], g['HT'], g['UD'], g['G']
M = base3d.M

# fica só a via dos dois retos do sul (x 0..1, y −2..0); sinal, elétrica do bloco, curva e fim saem
for o in list(sc.objects):
    if o.type not in ('MESH', 'EMPTY') or o.name == 'chao':
        continue
    if o.name.startswith(('sinal', 'eletrica', 'marca_bloco')):
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    if o.type != 'MESH':
        continue
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(c.x for c in cs) / 8
    cy = sum(c.y for c in cs) / 8
    if not (-0.3 < cx < 1.05 and -2.2 < cy < 0.2):
        for c in list(o.children):
            bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(o, do_unlink=True)

# ------------------------------------------------------------------ materiais novos
LUZ = {}


def luz(chave, nome, cor, base):
    m = emissivo(nome, cor, 0.0, base)
    LUZ[chave] = principled(m)
    M[chave] = m


luz('energ', 'Luz de energizado', (0.6, 0.14, 1.0), (0.05, 0.012, 0.09))
luz('arco', 'Faísca de arco', (0.75, 0.6, 1.0), (0.1, 0.08, 0.14))
M['isolador'] = mats.material('Porcelana marrom', (0.22, 0.09, 0.04), 0, 0.15, pintura=False, sujeira=0.8, desgaste=0.0)
M['inox'] = mats.material('Faixa de contato', (0.66, 0.66, 0.68), 1.0, 0.18, pintura=False, ferrugem=0.1, sujeira=0.6,
                          escovado=True)
M['cobre'] = mats.material('Cobre', (0.78, 0.4, 0.22), 1.0, 0.32, pintura=False, ferrugem=0.25, sujeira=0.8)
M['tampa'] = mats.material('Tampa de compósito', (0.68, 0.47, 0.06), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.0)
M['fuligem'] = mats.material('Fuligem de arco', (0.02, 0.018, 0.02), 0, 0.8, pintura=False, sujeira=0.0, desgaste=0.0)
for k, kw in (('isolador', dict(amassado=0.0, lz=(0.06, 0.12))), ('tampa', dict(amassado=0.1, lz=(0.12, 0.22))),
              ('cobre', dict(amassado=0.0, poeira=0.6, lz=(0.0, 0.2)))):
    g['rustico'](M[k], **kw)

UT = 0.41            # eixo do terceiro trilho (u: positivo = oeste de quem anda para o norte)
ZT0, ZT1 = 0.140, 0.172


def isolador(P, Q, a):
    """Mão-francesa na ponta do dormente + isolador de porcelana com saias + chapéu de aço."""
    caixa_q(P.B('galv'), Q, 0.30, 0.44, a - 0.03, a + 0.03, ZDT, ZDT + 0.007)          # chapa sobre o dormente
    for uu in (0.32, 0.355):
        parafuso(P.B('aco'), Q, uu, a, ZDT + 0.007, 0.0055, haste=0.003)
    caixa_q(P.B('galv'), Q, 0.432, 0.44, a - 0.03, a + 0.03, ZDT - 0.035, ZDT + 0.007)  # aba descendo no talude
    p0 = Q(UT, a, ZDT + 0.007)
    cil(P.B('galv', True), p0 + Z * 0.005, 0.018, 0.01, lados=16)
    cil(P.B('isolador', True), p0 + Z * 0.028, 0.014, 0.036, lados=20)
    for k in range(3):
        toro(P.B('isolador'), p0 + Z * (0.016 + k * 0.011), 0.019, 0.0035, 20, 6)
    cil(P.B('galv', True), p0 + Z * 0.0485, 0.017, 0.006, lados=16)                     # chapéu
    caixa_q(P.B('galv'), Q, UT - 0.024, UT + 0.024, a - 0.012, a + 0.012, ZT0 - 0.006, ZT0)  # garra do trilho
    for su in (-1, 1):
        caixa_q(P.B('galv'), Q, UT + su * 0.024 - 0.003, UT + su * 0.024 + 0.003, a - 0.012, a + 0.012, ZT0 - 0.006, ZT0 + 0.012)
    # suporte da tampa (haste do chapéu até a tampa)
    caixa_q(P.B('galv'), Q, UT + 0.028, UT + 0.034, a - 0.01, a + 0.01, ZT0, 0.1735)
    # escorrido de ferrugem do parafuso para a ponta do dormente
    decal(P.B('oxido'), [Q(0.355 - 0.003, a + 0.0, ZDT + 0.0075), Q(0.355 + 0.003, a, ZDT + 0.0075),
                         Q(0.38, a + 0.004, ZDT + 0.0075), Q(0.38, a - 0.004, ZDT + 0.0075)], 0.0004)


def terceiro(nome, cam, riser=True):
    P = Lote('terceiro_' + nome)
    L = cam.L
    for a in (0.1, 0.5, 0.9):
        isolador(P, Quadro(cam, a), 0.0)
    # perfil do terceiro trilho (patim largo, alma, boleto) com a faixa de contato por BAIXO do boleto e tampa por cima
    Q0, Q1 = Quadro(cam, 0.0), Quadro(cam, L)
    perfil = [(-0.028, ZT1 - 0.008), (0.028, ZT1 - 0.008), (0.028, ZT1), (-0.028, ZT1)]           # topo (boleto)

    def barra(mat, u0, u1, z0, z1):
        bm = P.B(mat)
        vs0 = [bm.verts.new(Q0(u, 0, z)) for (u, z) in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))]
        vs1 = [bm.verts.new(Q1(u, 0, z)) for (u, z) in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((vs0[i], vs0[j], vs1[j], vs1[i]))
    barra('aco', UT - 0.024, UT + 0.024, ZT0, ZT0 + 0.007)              # patim
    barra('aco', UT - 0.005, UT + 0.005, ZT0 + 0.007, ZT1 - 0.008)      # alma
    barra('aco', UT - 0.03, UT + 0.03, ZT1 - 0.008, ZT1)                # boleto (cabeça larga)
    barra('inox', UT - 0.03, UT + 0.03, ZT1 - 0.0095, ZT1 - 0.008)      # faixa de contato (por baixo)
    barra('fuligem', UT - 0.0305, UT - 0.022, ZT1 - 0.0096, ZT1 - 0.0094)   # fuligem de arco na beira
    barra('tampa', UT - 0.045, UT + 0.045, 0.1735, 0.179)              # tampa (baixa: o trem passa por cima)
    barra('tampa', UT + 0.042, UT + 0.048, 0.160, 0.1735)              # aba da tampa (lado de fora)
    for a0 in (0.08, 0.58):                                             # listras de perigo e raios de estêncil
        Qa = Quadro(cam, a0)
        decal(P.B('listras'), [Qa(UT - 0.044, 0, 0.1792), Qa(UT + 0.044, 0, 0.1792), Qa(UT + 0.044, 0.14, 0.1792),
                               Qa(UT - 0.044, 0.14, 0.1792)], 0)
    for a0 in (0.33, 0.83):
        Qa = Quadro(cam, a0)
        decal(P.B('tinta'), [Qa(UT + 0.02, -0.03, 0.1793), Qa(UT - 0.005, 0.0, 0.1793), Qa(UT + 0.006, 0.002, 0.1793),
                             Qa(UT - 0.02, 0.03, 0.1793), Qa(UT + 0.004, 0.003, 0.1793), Qa(UT - 0.007, 0.0, 0.1793)], 0)
    # orelha de cobre aparafusada na alma (a = 0,30) e cabo grosso até o eletroduto da borda
    Qc = Quadro(cam, 0.30)
    caixa_q(P.B('cobre'), Qc, UT + 0.005, UT + 0.013, -0.02, 0.02, ZT0 + 0.010, ZT1 - 0.011)
    for zz in (ZT0 + 0.014, ZT1 - 0.015):
        cil(P.B('aco'), Qc(UT + 0.016, 0, zz), 0.0045, 0.006, Qc.n, lados=6)
    if riser:
        base = Qc(0.475, 0.02, 0.0)
        tubo(P.B('galv', True), base - Z * 0.03, base + Z * 0.27, 0.0115, 14)            # eletroduto
        cil(P.B('concreto2'), base + Z * 0.004, 0.025, 0.012, lados=14)
        pts = [base + Z * 0.27, base + Z * 0.29 + Qc.n * 0.004, base + Z * 0.292 + Qc.n * 0.016,
               base + Z * 0.278 + Qc.n * 0.022]
        varrer(P.B('galv', True), catmull(pts, 4), 0.0115, 14)                            # cabeçote de chuva (oeste)
        caixa_de(P.B('cinza'), base + Vector((-0.019, -0.048, 0.20)), base + Vector((0.015, -0.014, 0.27)))  # seccionadora
        tubo(P.B('galv'), base + Vector((0, -0.014, 0.235)), base + Vector((0, -0.003, 0.235)), 0.006, 8)
        cil(P.B('aco'), base + Vector((0.0, -0.05, 0.245)), 0.006, 0.006, Vector((0, 1, 0)), lados=8)
        tubo(P.B('amarelo'), base + Vector((0.0, -0.053, 0.245)), base + Vector((0.0, -0.075, 0.27)), 0.0035, 6)   # alavanca
        bmesh.ops.create_icosphere(P.B('energ', True), subdivisions=2, radius=0.009,
                                   matrix=Matrix.Translation(base + Z * 0.30))                       # luz "energizado"
        cil(P.B('preto'), base + Z * 0.289, 0.011, 0.006, lados=14)
        caixa_de(P.B('adesivo'), base + Vector((-0.016, -0.0125, 0.06)), base + Vector((0.016, -0.0121, 0.10)))
        # cabo: sai por prensa-cabo no lado leste do eletroduto, por baixo da tampa, até a orelha na alma
        cil(P.B('aco'), base + Z * 0.125 - Qc.n * 0.013, 0.008, 0.01, Qc.n, lados=6)
        cabo = [base + Z * 0.125 - Qc.n * 0.018, Qc(0.45, 0.0, 0.122), Qc(UT + 0.03, 0.0, 0.14),
                Qc(UT + 0.013, 0.0, (ZT0 + ZT1) / 2)]
        varrer(P.B('borracha', True), catmull(cabo, 6), 0.0075, 12)
        cil(P.B('cobre'), Qc(UT + 0.015, 0, (ZT0 + ZT1) / 2), 0.011, 0.012, Qc.n, lados=10)
        # cordoalha de aterramento (cobre) do eletroduto ao patim do trilho de rolamento oeste
        corda = [base + Z * 0.02, Qc(0.40, 0.06, 0.03), Qc(0.33, 0.07, ZDT + 0.004), Qc(G + 0.03, 0.06, ZTB + 0.004)]
        varrer(P.B('cobre', True), catmull(corda, 5), 0.0035, 6)
        caixa_q(P.B('cobre'), Qc, G + 0.022, G + 0.032, 0.05, 0.07, ZTB, ZTB + 0.004)
        # lama e pó de cobre no pé do eletroduto
        halo_em('halo_lama', Vector((base.x, base.y, 0)), 0.07, 0.0011, 1.4, 0.6)
    # faísca: um objeto próprio (só a luz pisca)
    P.fim()
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.004, matrix=Matrix.Translation(Qc(UT + 0.009, 0.022, ZT0 + 0.012)))
    base3d.obj('terceiro_%s_faisca' % nome, bm, 'arco')


terceiro('a', g['reta_a'])
terceiro('b', g['reta_b'])

# ------------------------------------------------------------------ animação (laço de 4 s)
QUADROS = g['QUADROS']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    inp = LUZ['energ'].inputs['Emission Strength']
    inp.default_value = 5.0 + 3.0 * math.sin(2 * PI * fr * 2)
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['arco'].inputs['Emission Strength']
    inp.default_value = 30.0 if q in (17, 18, 61) else 0.0
    inp.keyframe_insert('default_value', frame=q)
for m in bpy.data.materials:
    if m.node_tree:
        g['linear'](m.node_tree.animation_data)

FOTOS = {
    'trilho_energizado_0': ((-0.9, -2.6, 1.0), (0.4, -1.0, 0.08), 32, (1300, 1000)),
    'trilho_energizado_perto': ((-0.35, -1.05, 0.42), (0.1, -0.7, 0.13), 32, (1300, 1000)),
}
if MODO in ('foto', 'teste'):
    sc.cycles.samples = 128 if MODO == 'foto' else 24
    sc.frame_set(9)
    for nome, (pos, alvo, lente, (rx, ry)) in FOTOS.items():
        g['foto'](nome + '.png', pos, alvo, lente, rx if MODO == 'foto' else rx // 2, ry if MODO == 'foto' else ry // 2)
print('TRILHO ENERGIZADO ok')
