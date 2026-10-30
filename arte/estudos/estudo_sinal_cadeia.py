"""Estudo isolado (fora do jogo): SINAL EM CADEIA (sinal_cadeia, 1×1, até ~1,62 m), lote 16.
Mesmo sinal de bloco aprovado (estudo_trilhos.py: sapata e pedestal de concreto, mastro galvanizado, cabeça de LEDs com
palas, caixa de controle, eletrodutos, caixa de passagem e contato de trilho), montado por este script, com o que faz
dele um sinal EM CADEIA: ele não olha só o bloco da frente, olha a SAÍDA do cruzamento — só libera a entrada se a saída
estiver livre.
- Cabeça de cadeia logo abaixo da principal: braçadeira dupla no mastro, espelho de chapa com a marca da cadeia (dois
  elos de aço estampados e pintados de violeta), caixa com três LEDs violeta em linha (correm para a saída quando ela
  está livre; ficam vermelhos quando ela está ocupada), pala corrida e seta de estêncil.
- Lidar da saída: braço curto no lado norte do mastro com um disco de varredura (janela violeta) girando — é o olho que
  vigia o bloco depois do cruzamento.
- Módulo de cadeia: caixinha cinza parafusada sob a caixa de controle, com dois LEDs, prensa-cabos e o eletroduto do
  ramal que conversa com o próximo sinal (o ramal da caixa de passagem já existe no estudo dos trilhos).
- Cabos novos (cabeça de cadeia → caixa de controle; lidar → caixa) em borracha com abraçadeiras no mastro.
- A faixa branca de bloco do espelho principal vira violeta (marca de sinal em cadeia), e o pedestal ganha uma
  plaqueta de aço com elos.
Fica: trecho reto da via (os dois retos do sul do estudo) e a elétrica do bloco; a curva, o fim de linha e o resto saem.
Animação 4 s: cabeça principal verde → âmbar → vermelho (a do estudo dos trilhos); a de cadeia corre violeta enquanto
o principal está verde/âmbar e acende vermelha fixa quando o principal fecha; o lidar dá duas voltas; LEDs do módulo.
Uso: blender -b --python estudo_sinal_cadeia.py -- foto | nada"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
MODO = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

# ------------------------------------------------------------------ o sinal de bloco aprovado (sem fotos)
_base = os.path.join(AQUI, 'estudo_trilhos.py')
sys.argv = [sys.argv[0], '--python', _base, '--', 'nada']
g = {'__name__': '__main__', '__file__': _base}
exec(compile(open(_base, encoding='utf-8').read(), _base, 'exec'), g)
import base3d
from base3d import caixa_de, cil, tubo

PI = math.pi
Z = Vector((0, 0, 1))
Yv = Vector((0, 1, 0))
sc = bpy.context.scene
random.seed(16)
toro, varrer, catmull, corrugado = g['toro'], g['varrer'], g['catmull'], g['corrugado']
prisma, ret_arred, chapa_arco, Lote, emissivo = g['prisma'], g['ret_arred'], g['chapa_arco'], g['Lote'], g['emissivo']
principled, halo_em, decal = g['principled'], g['halo_em'], g['decal']
SC = g['SC']

# fica só o trecho reto do sul, o sinal e a elétrica do bloco (x −0,2..2,2; y −2,2..0,2)
for o in list(sc.objects):
    if o.type != 'MESH' or o.name == 'chao':
        continue
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(c.x for c in cs) / 8
    cy = sum(c.y for c in cs) / 8
    if not (-0.2 < cx < 2.2 and -2.2 < cy < 0.2):
        for c in list(o.children):
            bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(sc.objects):
    if o.type == 'EMPTY' and not o.children and o.name.startswith('tufo'):
        bpy.data.objects.remove(o, do_unlink=True)

# a faixa branca do espelho principal vira violeta (marca do sinal em cadeia)
o = sc.objects.get('sinal_tinta_bloco')
if o is not None:
    o.material_slots[0].material = base3d.M['tinta_violeta']

# ------------------------------------------------------------------ luzes novas
LUZ = {}


def luz(chave, nome, cor, base):
    m = emissivo(nome, cor, 0.0, base)
    LUZ[chave] = principled(m)
    base3d.M[chave] = m


for k in range(3):
    luz('cad%d' % k, 'LED de cadeia %d' % (k + 1), (0.62, 0.14, 1.0), (0.05, 0.012, 0.09))
luz('cad_r', 'LED de cadeia fechada', (1.0, 0.03, 0.01), (0.1, 0.01, 0.005))
luz('lidar', 'Janela do lidar', (0.55, 0.15, 1.0), (0.04, 0.012, 0.08))
luz('mod1', 'LED do módulo 1', (0.1, 1.0, 0.25), (0.01, 0.08, 0.02))
luz('mod2', 'LED do módulo 2', (0.62, 0.14, 1.0), (0.05, 0.012, 0.09))
base3d.M['elo'] = base3d.M['tinta_violeta']


def elo(bm, c, ang, R=0.012, a=0.006, r=0.0022, eixo_y=-1):
    """Elo de corrente achatado (estádio) no plano xz, girado `ang` em volta do eixo y."""
    pts = []
    n = 10
    for (cx, a0) in ((a, -PI / 2), (-a, PI / 2)):
        for k in range(n + 1):
            t = a0 + PI * k / n
            pts.append(Vector((cx + R * math.cos(t), 0, R * math.sin(t))))
    rot = Matrix.Rotation(ang, 3, 'Y')
    pts = [Vector(c) + rot @ p for p in pts] + [Vector(c) + rot @ pts[0]]
    varrer(bm, pts, r, 8, (False, False))


# ------------------------------------------------------------------ cabeça de cadeia
def cabeca_cadeia():
    P = Lote('cadeia')
    c = SC
    Y0 = c.y - 0.029                                          # frente do mastro
    ZH = 0.90                                                 # centro da cabeça de cadeia
    for zz in (ZH - 0.06, ZH + 0.06):                         # braçadeiras
        toro(P.B('aco'), c + Z * zz, 0.031, 0.004, 28, 6)
        caixa_de(P.B('aco'), Vector((c.x - 0.012, Y0 - 0.016, zz - 0.012)), Vector((c.x + 0.012, Y0 + 0.004, zz + 0.012)))
        for sx in (-1, 1):
            cil(P.B('aco'), Vector((c.x + sx * 0.018, c.y + 0.031, zz)), 0.005, 0.01, Yv, lados=6)
    # espelho com a marca da cadeia
    ret_arred(P.B('grafite'), Vector((c.x, Y0 - 0.016, ZH - 0.01)), 0.21, 0.19, 0.025, 0.01)
    ret_arred(P.B('tinta_violeta'), Vector((c.x, Y0 - 0.0262, ZH - 0.01)), 0.21, 0.19, 0.025, 0.0006)
    ret_arred(P.B('grafite'), Vector((c.x, Y0 - 0.0268, ZH - 0.01)), 0.19, 0.17, 0.018, 0.0006)
    YC = Y0 - 0.026
    ret_arred(P.B('grafite'), Vector((c.x, YC, ZH + 0.025)), 0.16, 0.07, 0.015, 0.045)      # caixa dos LEDs
    YF = YC - 0.045
    for k, xx in enumerate((-0.045, 0.0, 0.045)):
        cc = Vector((c.x + xx, YF, ZH + 0.025))
        toro(P.B('cromo'), cc - Vector((0, 0.002, 0)), 0.019, 0.0022, 24, 5, Yv)
        cil(P.B('preto'), cc - Vector((0, 0.001, 0)), 0.018, 0.002, Yv, lados=24)
        bm = P.B('cad%d' % k, True)
        for (dx, dz) in [(0, 0)] + [(0.008 * math.cos(j * PI / 3), 0.008 * math.sin(j * PI / 3)) for j in range(6)]:
            m = Matrix.Translation(cc + Vector((dx, -0.002, dz))) @ Matrix.Diagonal((1, 0.55, 1, 1))
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0035, matrix=m)
        # anel vermelho em volta do LED do meio (acende quando a saída está ocupada)
        if k == 1:
            toro(P.B('cad_r', True), cc - Vector((0, 0.0025, 0)), 0.0135, 0.0016, 24, 4, Yv)
    chapa_arco(P.B('grafite', True), Vector((c.x - 0.075, YF, ZH + 0.025)), Vector((1, 0, 0)), 0.03, 0.0025, 0.15,
               math.radians(30), math.radians(150), 12)                                      # pala corrida
    # seta de estêncil para a saída e elos estampados (marca da cadeia) no espelho, abaixo da caixa
    YS = Y0 - 0.0274
    decal(P.B('tinta'), [Vector((c.x - 0.06, YS, ZH - 0.045)), Vector((c.x + 0.02, YS, ZH - 0.045)),
                         Vector((c.x + 0.02, YS, ZH - 0.035)), Vector((c.x - 0.06, YS, ZH - 0.035))], 0)
    decal(P.B('tinta'), [Vector((c.x + 0.02, YS, ZH - 0.052)), Vector((c.x + 0.045, YS, ZH - 0.04)),
                         Vector((c.x + 0.02, YS, ZH - 0.028))], 0)
    for k, (dx, ang) in enumerate(((-0.03, 0.0), (-0.005, PI / 2 * 0.0), (0.02, 0.0))):
        elo(P.B('elo', True), Vector((c.x + dx * 1.0 + 0.0, YS - 0.002 - 0.0025 * (k % 2), ZH - 0.078)), 0.0 if k % 2 == 0 else 0.0,
            R=0.009, a=0.008, r=0.0021 if k % 2 == 0 else 0.0019)
    # parafusos do espelho e plaqueta de série
    for sx in (-1, 1):
        for zz in (ZH - 0.09, ZH + 0.07):
            cil(P.B('aco'), Vector((c.x + sx * 0.093, Y0 - 0.027, zz)), 0.004, 0.004, Yv, lados=6)
    caixa_de(P.B('aco'), Vector((c.x + 0.045, Y0 - 0.0285, ZH - 0.09)), Vector((c.x + 0.085, Y0 - 0.027, ZH - 0.072)))
    for j in range(3):
        if random.random() < 0.8:
            caixa_de(P.B('preto'), Vector((c.x + 0.05 + j * 0.011, Y0 - 0.029, ZH - 0.087)),
                     Vector((c.x + 0.057 + j * 0.011, Y0 - 0.0284, ZH - 0.075)))
    # escorrido de ferrugem do parafuso de baixo
    decal(P.B('oxido'), [Vector((c.x + 0.091, Y0 - 0.0276, ZH - 0.13)), Vector((c.x + 0.095, Y0 - 0.0276, ZH - 0.13)),
                         Vector((c.x + 0.0945, Y0 - 0.0276, ZH - 0.094)), Vector((c.x + 0.0915, Y0 - 0.0276, ZH - 0.094))], 0)
    # cabo da cabeça de cadeia até a caixa de controle (lado oeste do mastro, abraçadeiras)
    XC = c.x - 0.036
    cil(P.B('aco'), Vector((c.x - 0.03, YC + 0.004, ZH - 0.035)), 0.008, 0.012, lados=6)    # prensa-cabo
    pts = [Vector((c.x - 0.03, YC + 0.004, ZH - 0.04)), Vector((XC, c.y - 0.012, ZH - 0.09)),
           Vector((XC, c.y, 0.76)), Vector((c.x - 0.03, c.y + 0.06, 0.725)), Vector((c.x - 0.03, c.y + 0.08, 0.705))]
    varrer(P.B('borracha', True), catmull(pts, 5), 0.0055, 10)
    toro(P.B('aco'), c + Z * 0.79, 0.037, 0.0022, 28, 5)
    P.fim()


# ------------------------------------------------------------------ lidar da saída (lado norte do mastro)
def lidar():
    P = Lote('lidar_suporte')
    c = SC
    ZL = 1.40
    toro(P.B('aco'), c + Z * ZL, 0.031, 0.004, 28, 6)
    caixa_de(P.B('galv'), Vector((c.x - 0.012, c.y + 0.028, ZL - 0.012)), Vector((c.x + 0.012, c.y + 0.095, ZL + 0.004)))
    prisma(P.B('galv'), [Vector((c.x - 0.004, c.y + 0.03, ZL - 0.012)), Vector((c.x - 0.004, c.y + 0.07, ZL - 0.012)),
                         Vector((c.x - 0.004, c.y + 0.03, ZL - 0.05))], 0.008, Vector((1, 0, 0)))   # mão-francesa
    cil(P.B('grafite', True), Vector((c.x, c.y + 0.085, ZL + 0.012)), 0.03, 0.016, lados=24)     # base do lidar
    cil(P.B('aco'), Vector((c.x, c.y + 0.085, ZL + 0.022)), 0.012, 0.004, lados=16)
    cil(P.B('aco'), Vector((c.x + 0.018, c.y + 0.07, ZL + 0.004)), 0.0065, 0.01, lados=6)       # prensa-cabo
    pts = [Vector((c.x + 0.018, c.y + 0.07, ZL - 0.002)), Vector((c.x + 0.03, c.y + 0.05, ZL - 0.06)),
           Vector((c.x + 0.036, c.y + 0.02, 1.2)), Vector((c.x + 0.036, c.y + 0.02, 0.85)),
           Vector((c.x + 0.05, c.y + 0.06, 0.73)), Vector((c.x + 0.05, c.y + 0.08, 0.705))]
    varrer(P.B('borracha', True), catmull(pts, 5), 0.0045, 8)
    P.fim()
    # disco giratório (objeto próprio para a animação)
    e = bpy.data.objects.new('lidar_giro', None)
    sc.collection.objects.link(e)
    e.location = (c.x, c.y + 0.085, ZL + 0.024)
    D = Lote('lidar_disco')
    o0 = Vector((0, 0, 0))
    cil(D.B('grafite', True), o0 + Z * 0.017, 0.026, 0.034, lados=28)
    cil(D.B('lidar', True), o0 + Z * 0.017, 0.0262, 0.012, lados=28)
    cil(D.B('preto', True), o0 + Z * 0.036, 0.022, 0.004, lados=28)
    caixa_de(D.B('preto'), Vector((-0.006, 0.0258, 0.012)), Vector((0.006, 0.0275, 0.022)))     # janela emissora
    D.fim()
    for nome in ('lidar_disco_grafite', 'lidar_disco_lidar', 'lidar_disco_preto'):
        ob = sc.objects.get(nome)
        if ob is not None:
            ob.parent = e
            ob.location = (0, 0, 0)
    return e


# ------------------------------------------------------------------ módulo de cadeia (sob a caixa de controle)
def modulo():
    P = Lote('modulo')
    c = SC
    X0, X1, Yb, Yt, Zb, Zt = c.x - 0.05, c.x + 0.05, c.y + 0.042, c.y + 0.092, 0.27, 0.37
    caixa_de(P.B('cinza'), Vector((X0, Yb, Zb)), Vector((X1, Yt, Zt)))
    caixa_de(P.B('borracha'), Vector((X0 + 0.003, Yt, Zb + 0.003)), Vector((X1 - 0.003, Yt + 0.002, Zt - 0.003)))
    caixa_de(P.B('cinza'), Vector((X0 + 0.002, Yt + 0.002, Zb + 0.002)), Vector((X1 - 0.002, Yt + 0.006, Zt - 0.002)))
    for xx in (X0 + 0.01, X1 - 0.01):
        for zz in (Zb + 0.01, Zt - 0.01):
            cil(P.B('aco'), Vector((xx, Yt + 0.0075, zz)), 0.0042, 0.004, Yv, lados=6)
    for j, (chave, xx) in enumerate((('mod1', c.x - 0.015), ('mod2', c.x + 0.015))):
        cil(P.B('preto'), Vector((xx, Yt + 0.007, Zt - 0.03)), 0.005, 0.003, Yv, lados=16)
        bmesh.ops.create_icosphere(P.B(chave, True), subdivisions=2, radius=0.0032,
                                   matrix=Matrix.Translation(Vector((xx, Yt + 0.0088, Zt - 0.03))))
    elo(P.B('elo', True), Vector((c.x, Yt + 0.0072, Zb + 0.035)), PI / 2, R=0.007, a=0.006, r=0.0016, eixo_y=1)
    caixa_de(P.B('adesivo'), Vector((X0 + 0.01, Yt + 0.0061, Zb + 0.015)), Vector((X0 + 0.035, Yt + 0.0064, Zb + 0.03)))
    for zz in (Zb + 0.02, Zt - 0.02):                                            # braçadeiras ao mastro
        toro(P.B('aco'), c + Z * zz, 0.031, 0.0035, 28, 6)
        caixa_de(P.B('aco'), Vector((c.x - 0.012, c.y + 0.028, zz - 0.01)), Vector((c.x + 0.012, Yb, zz + 0.01)))
    # prensa-cabo embaixo e eletroduto corrugado até o pedestal (ramal para o próximo sinal)
    cil(P.B('aco'), Vector((c.x, c.y + 0.07, Zb - 0.007)), 0.009, 0.014, lados=6)
    pts = [Vector((c.x, c.y + 0.07, Zb - 0.014)), Vector((c.x, c.y + 0.078, 0.22)),
           Vector((c.x + 0.012, c.y + 0.088, 0.18)), Vector((c.x + 0.012, c.y + 0.088, 0.162))]
    corrugado(P.B('pvc', True), catmull(pts, 6), 0.0075)
    cil(P.B('galv'), Vector((c.x + 0.012, c.y + 0.088, 0.157)), 0.011, 0.012, lados=6)
    # plaqueta de elos no pedestal (face oeste)
    caixa_de(P.B('aco'), Vector((c.x - 0.1012, c.y - 0.04, 0.07)), Vector((c.x - 0.1004, c.y + 0.04, 0.115)))
    for k, dy in enumerate((-0.018, 0.0, 0.018)):
        elo(P.B('elo', True), Vector((c.x - 0.1025, c.y + dy, 0.0925)), 0.0, R=0.0075, a=0.006, r=0.0017)
    P.fim()


cabeca_cadeia()
GIRO = lidar()
modulo()
# um pouco mais de lama no pé do pedestal (o sinal novo foi chumbado depois: concreto mais limpo em volta)
halo_em('halo_lama', SC + Vector((0.08, 0.12, 0)), 0.14, 0.0011, 1.3, 0.8)

# o estêncil das elos dobra no plano xz: reaponta os elos para a face (o varrer cria no plano xz em y = c.y)
for o in sc.objects:
    if o.type == 'MESH' and o.name.endswith('_elo'):
        for pg in o.data.polygons:
            pg.use_smooth = True


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


QUADROS = g['QUADROS']
Q_VERM = (57, 96)                      # mesmo ciclo da cabeça principal (estudo dos trilhos)
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    fechado = g['nivel'](q, Q_VERM)
    # cadeia livre: os três correm para a saída (oeste → leste), um por vez, 3 voltas por segundo... devagar: 6 por laço
    passo = (q - 1) // 4 % 3
    for k in range(3):
        inp = LUZ['cad%d' % k].inputs['Emission Strength']
        corre = 9.0 if k == passo else 0.6
        inp.default_value = 0.05 + corre * (1.0 - fechado)
        inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['cad_r'].inputs['Emission Strength']
    inp.default_value = 0.04 + 12.0 * fechado
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['lidar'].inputs['Emission Strength']
    inp.default_value = 3.0 + 2.0 * math.sin(2 * PI * fr * 8)
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['mod1'].inputs['Emission Strength']
    inp.default_value = 5.0 if (q // 8) % 2 == 0 else 0.1
    inp.keyframe_insert('default_value', frame=q)
    inp = LUZ['mod2'].inputs['Emission Strength']
    inp.default_value = 0.2 + 6.0 * (1.0 - fechado)
    inp.keyframe_insert('default_value', frame=q)
    GIRO.rotation_euler = (0, 0, 2 * PI * 2 * fr)
    GIRO.keyframe_insert('rotation_euler', frame=q)
for m in bpy.data.materials:
    if m.node_tree:
        g['linear'](m.node_tree.animation_data)
g['linear'](GIRO.animation_data)

# ------------------------------------------------------------------ fotos
FOTOS = {
    'sinal_cadeia_0': ((2.55, -2.85, 1.25), (1.5, -1.5, 0.8), 30, (1100, 1300)),
    'sinal_cadeia_1': ((0.45, -0.25, 1.35), (1.5, -1.5, 0.85), 30, (1100, 1300)),
    'sinal_cadeia_perto': ((1.78, -2.02, 1.0), (1.5, -1.56, 0.92), 30, (1100, 1100)),
}
if MODO in ('foto', 'teste'):
    sc.cycles.samples = 128 if MODO == 'foto' else 24
    sc.frame_set(9)                                             # principal verde, cadeia correndo
    for nome, (pos, alvo, lente, (rx, ry)) in FOTOS.items():
        if MODO == 'teste':
            rx, ry = rx // 2, ry // 2
        g['foto'](nome + '.png', pos, alvo, lente, rx, ry)
print('SINAL CADEIA ok')
