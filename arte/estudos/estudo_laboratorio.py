"""Estudo isolado (fora do jogo): laboratório 3×3, entrada de item pelo sul (meio), como no jogo.
Laboratório de pesquisa da IA autônoma: esteira curta de roletes traz pacotes de pesquisa (módulo de cristal lapidado
+ engrenagem) pela boca sul; braço pega-e-põe coloca o pacote na gaveta do analisador. O analisador é o tambor
octogonal: comporta sobe por pistões, a gaveta entra e o pacote se desfaz sob lasers num anel de campo, com névoa
violeta vista pelas janelas. Cúpula de sensores com pilares de dados de cristal e varredor (radar) com antena girando
no topo. Racks de servidores e de cristais de dados com luzes piscando; feixes de cabos sobem para a eletrocalha.
Refrigeração líquida: radiador seco com dois ventiladores girando, bomba, reservatório, cinta de resfriamento no
tambor e canos de ida (isolados) e retorno (cobre). Exaustor centrífugo e chaminé soltando vapor. Armário de força.
Óleo, poeira de cristal, lascas de cristal, fuligem e pintura gasta.
Uso: blender -b --python estudo_laboratorio.py -- foto | video"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço: um pacote por ciclo
random.seed(31)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades de forma
def suavizar(o, tudo=False):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o


def curva(bm, p, r, lados=14):
    """Cotovelo arredondado (esfera do raio do tubo)."""
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, flange=True):
    """Cano rígido por pontos: trechos retos, cotovelos redondos e flanges perto de cada curva."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.14:
            for c in (a + u * 0.05, b - u * 0.05):
                tubo(bf, c - u * 0.008, c + u * 0.008, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def toro(bm, centro, R, r, nR=48, nr=10, eixo=None):
    """Anel tubular contínuo (sem emendas); eixo vertical, ou girado para `eixo`."""
    rot = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix() if eixo is not None else Matrix.Identity(3)
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def prisma(bm, c, ap, z0, z1, n=8):
    """Prisma de n lados com faces voltadas para os eixos (apótema `ap`)."""
    rv = ap / math.cos(PI / n)
    vs = []
    for z in (z0, z1):
        vs.append([bm.verts.new((c[0] + rv * math.cos(PI / n + 2 * PI * k / n), c[1] + rv * math.sin(PI / n + 2 * PI * k / n), z))
                   for k in range(n)])
    bm.faces.new(list(reversed(vs[0])))
    bm.faces.new(vs[1])
    for k in range(n):
        bm.faces.new((vs[0][k], vs[0][(k + 1) % n], vs[1][(k + 1) % n], vs[1][k]))


def casca(bm, c, r_out, r_in, z0, z1, n=32):
    """Anel grosso (cilindro oco): carenagem de ventilador, colar."""
    c = Vector(c)
    an = []
    for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
        an.append([bm.verts.new(c + Vector((r * math.cos(2 * PI * k / n), r * math.sin(2 * PI * k / n), z))) for k in range(n)])
    for i in range(4):
        A, B = an[i], an[(i + 1) % 4]
        for k in range(n):
            bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))


def hexa(bm, c, r, z0, z1, ponta=0.0):
    """Cristal lapidado: prisma hexagonal com ponta piramidal."""
    cil(bm, Vector((c[0], c[1], (z0 + z1) / 2)), r, z1 - z0, lados=6)
    if ponta > 0:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=0.0, depth=ponta,
                              matrix=Matrix.Translation((c[0], c[1], z1 + ponta / 2)))


def feixe(bc, ba, pts, n=3, r=0.009, passo=4, lado=Vector((1, 0, 0))):
    """Cabos paralelos seguindo a mesma curva, com abraçadeiras a cada `passo` pontos."""
    for i in range(n):
        off = lado * ((i - (n - 1) / 2) * r * 2.2)
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 1.2), 12)


# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat():
    m = bpy.data.materials.new('Vidro')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.8, 0.78, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Alpha'].default_value = 0.3
    b.inputs['IOR'].default_value = 1.45
    return m


def malha_mat():
    """Porta de rack perfurada: chapa transparente onde não há metal."""
    m = bpy.data.materials.new('Tela')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.04, 0.04, 0.045, 1)
    b.inputs['Metallic'].default_value = 0.7
    b.inputs['Roughness'].default_value = 0.5
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hz = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(sep.outputs['X'], hz.inputs[0])
    nt.links.new(sep.outputs['Y'], hz.inputs[1])
    fios = []
    for entrada in (hz.outputs['Value'], sep.outputs['Z']):
        d = no(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = 0.02
        nt.links.new(entrada, d.inputs[0])
        fr = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs['Value'], fr.inputs[0])
        lt = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
        lt.inputs[1].default_value = 0.3
        nt.links.new(fr.outputs['Value'], lt.inputs[0])
        fios.append(lt)
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fios[0].outputs['Value'], mx.inputs[0])
    nt.links.new(fios[1].outputs['Value'], mx.inputs[1])
    nt.links.new(mx.outputs['Value'], b.inputs['Alpha'])
    return m


def cristal_mat(nome, forca):
    """Cristal de dados: violeta translúcido que brilha por dentro."""
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.5, 0.28, 0.85, 1)
    b.inputs['Transmission Weight'].default_value = 0.6
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.55, 0.22, 1.0, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def po_mat():
    """Poeira de cristal: pó lilás acinzentado, fosco com pontos que cintilam."""
    m = bpy.data.materials.new('Pó de cristal')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 260.0, 'Detail': 2.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    cint = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.62, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], cint.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.2, 0.185, 0.23, 1)
    mix.inputs[7].default_value = (0.55, 0.4, 0.8, 1)
    nt.links.new(cint.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.85, 'To Max': 0.15})
    nt.links.new(cint.outputs['Result'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    return m


def nevoa_mat():
    """Névoa de dissolução: volume violeta que emite (o pacote se desfaz dentro dela)."""
    m = base3d.volume_mat('Névoa', (0.5, 0.25, 0.9), 2.5, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 12.0
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (0.6, 0.25, 1.0, 1)
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.15, sujeira=1.0, ferrugem=0.5),
    'laranja': mats.material('Laranja', (0.62, 0.22, 0.04), 0, 0.45, desgaste=1.1, sujeira=1.0, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'servidor': mats.material('Servidor', (0.11, 0.115, 0.12), 0, 0.45, desgaste=0.5, sujeira=0.6),
    'cinza': mats.material('Cinza', (0.22, 0.23, 0.24), 0, 0.5, desgaste=1.0, sujeira=1.0, ferrugem=0.6),
    'radiador': mats.material('Radiador', (0.34, 0.36, 0.37), 0, 0.45, desgaste=0.9, sujeira=1.0, ferrugem=0.4),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.9, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.9, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.015, 0.014, 0.013), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'lente': mats.material('Lente', (0.01, 0.012, 0.015), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
    'liquido': luz_mat('Fluido refrigerante', (0.25, 0.75, 0.2), 0.6),
    'vidro': vidro_mat(),
    'malha': malha_mat(),
    'listras': base3d.listras_mat(),
    'po': po_mat(),
    'cristal': cristal_mat('Cristal de dados', 1.0),
    'cristal_rack': cristal_mat('Cristal do rack', 1.5),
    'cristal_pac': cristal_mat('Cristal do pacote', 0.6),
    'lasca': cristal_mat('Lasca de cristal', 0.25),
    'nevoa': nevoa_mat(),
    'vapor': base3d.volume_mat('Vapor', (0.9, 0.9, 0.92), 3.0, 2.1, 3.1),
    'laser': luz_mat('Laser', (1.0, 0.45, 0.08), 25.0),
    'campo': luz_mat('Anel de campo', (0.6, 0.25, 1.0), 3.0),
    'giroflex': luz_mat('Giroflex', (1.0, 0.45, 0.04), 2.0),
    'tela': luz_mat('Tela', (0.45, 0.22, 0.9), 1.2),
    'energia': luz_mat('Campo de energia', (1.0, 0.55, 0.08), 4.0),
    'isolador': mats.material('Isolador', (0.33, 0.16, 0.08), 0, 0.2, desgaste=0.3, sujeira=1.0),
})
LEDS = []
for i, (nome, cor) in enumerate((('verde', (0.15, 1.0, 0.25)), ('verde', (0.15, 1.0, 0.25)), ('ambar', (1.0, 0.5, 0.05)),
                                 ('ambar', (1.0, 0.5, 0.05)), ('violeta', (0.6, 0.25, 1.0)), ('violeta', (0.6, 0.25, 1.0)),
                                 ('vermelho', (1.0, 0.08, 0.05)))):
    chave_led = 'led%d' % i
    base3d.M[chave_led] = luz_mat('LED %s %d' % (nome, i), cor, 5.0)
    LEDS.append(chave_led)

C = Vector((0.0, 0.1, 0.0))   # centro do tambor analisador
AP = 0.58                    # apótema do tambor
RV = AP / math.cos(PI / 8)
ZP, ZT = 0.2, 1.25           # topo do pedestal e topo das paredes
ZR = 1.32                    # topo do teto
ZB = 0.5                     # topo dos roletes da esteira
Y_PARA = -0.95               # pacote parado no fim da esteira
Y_FORA, Y_DENTRO = -0.64, 0.1  # gaveta: posição do pacote fora e dentro do tambor
ZG = 0.71                    # topo da gaveta
PAC = (0.12, 0.12, 0.1)      # pacote de pesquisa
Z_LEV = 0.9                  # centro do anel de campo: o pacote levita até ele e se desfaz

# ------------------------------------------------------------------ laje e faixas
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()                                                          # área do braço marcada no piso
for a, b in (((-0.95, -1.12, 0.08), (-0.9, -0.55, 0.082)), ((-0.95, -1.12, 0.08), (-0.26, -1.07, 0.082)),
             ((-0.95, -0.6, 0.08), (-0.6, -0.55, 0.082))):
    caixa_de(bm, a, b)
for x in (-0.26, 0.26):                                                   # corredor da esteira
    caixa_de(bm, (x - 0.025, -1.48, 0.08), (x + 0.025, -0.78, 0.082))
obj('faixas_piso', bm, 'listras')

# ------------------------------------------------------------------ tambor octogonal do analisador
bm = bmesh.new()
prisma(bm, C, 0.66, 0.08, ZP)                                             # pedestal
obj('tambor_pedestal', bm, 'cinza')
bm = bmesh.new()
prisma(bm, C, AP + 0.02, ZT, ZT + 0.03)                                   # beiral
prisma(bm, C, AP - 0.01, ZT + 0.03, ZR)                                   # teto
obj('tambor_teto', bm, 'grafite')
bm, bmg, bmv, bml = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
LARG = 2 * AP * math.tan(PI / 8)
JAN = (0.47, 0.98)                                                        # janelas (altura)
HATCH = (-0.16, 0.16, 0.62, 0.9)                                          # boca da gaveta (face sul)
for k in range(8):
    a = k * PI / 4
    rot = Matrix.Rotation(a, 3, 'Z')
    d = Vector((math.cos(a), math.sin(a), 0))
    cen = C + d * (AP - 0.01)
    def painel(y0, y1, z0, z1, alvo=bm, esp=0.02, saliente=0.0):
        """Retângulo na face k (y = largura local, z = altura)."""
        caixa(alvo, cen + d * saliente + rot @ Vector((0, (y0 + y1) / 2, 0)) + Vector((0, 0, (z0 + z1) / 2)),
              (esp, y1 - y0, z1 - z0), rot)
    w = LARG / 2 - 0.02
    if k == 6:                                                            # face sul: boca da gaveta
        painel(-w, w, ZP, HATCH[2])
        painel(-w, w, HATCH[3], ZT)
        painel(-w, HATCH[0], HATCH[2], HATCH[3])
        painel(HATCH[1], w, HATCH[2], HATCH[3])
        for y0, y1, z0, z1 in ((HATCH[0] - 0.04, HATCH[0], HATCH[2] - 0.04, HATCH[3] + 0.02),
                               (HATCH[1], HATCH[1] + 0.04, HATCH[2] - 0.04, HATCH[3] + 0.02),
                               (HATCH[0] - 0.04, HATCH[1] + 0.04, HATCH[2] - 0.04, HATCH[2])):
            painel(y0, y1, z0, z1, bml, 0.03, 0.015)                      # moldura listrada da boca
    elif k % 2 == 1:                                                      # faces diagonais: janelas de inspeção
        painel(-w, w, ZP, JAN[0])
        painel(-w, w, JAN[1], ZT)
        painel(-w, w, JAN[0], JAN[1], bmv, 0.008)
        for y0, y1, z0, z1 in ((-w, -w + 0.035, JAN[0], JAN[1]), (w - 0.035, w, JAN[0], JAN[1]),
                               (-w, w, JAN[0] - 0.02, JAN[0] + 0.02), (-w, w, JAN[1] - 0.02, JAN[1] + 0.02),
                               (-0.012, 0.012, JAN[0], JAN[1])):
            painel(y0, y1, z0, z1, bmg, 0.035, 0.01)
    else:                                                                 # faces cheias com reforço e grelha de ar
        painel(-w, w, ZP, ZT)
        painel(-w + 0.02, w - 0.02, 0.62, 0.66, bmg, 0.03, 0.012)
        if k == 0:
            for j in range(6):
                painel(-0.12, 0.12, 0.78 + j * 0.04, 0.795 + j * 0.04, bmg, 0.025, 0.012)
    for j in range(5):                                                    # parafusos em cima e embaixo do painel
        for z in (ZP + 0.03, ZT - 0.03):
            y = -w + 0.04 + j * (2 * w - 0.08) / 4
            cil(bmg, cen + d * 0.012 + rot @ Vector((0, y, 0)) + Vector((0, 0, z)), 0.007, 0.008, d, lados=6)
    av = (k + 0.5) * PI / 4                                               # coluna no vértice
    dv = Vector((math.cos(av), math.sin(av), 0))
    caixa(bmg, C + dv * (RV - 0.005) + Vector((0, 0, (ZP + ZT) / 2)), (0.045, 0.045, ZT - ZP), Matrix.Rotation(av, 3, 'Z'))
obj('tambor_paineis', bm, 'amarelo')
obj('tambor_estrutura', bmg, 'grafite')
obj('tambor_janelas', bmv, 'vidro')
obj('tambor_boca_listras', bml, 'listras')
bm = bmesh.new()                                                          # escorridos de óleo e sujeira nas faces
for k in range(8):
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    for j in range(2):
        u = random.uniform(-0.15, 0.15)
        z1 = random.uniform(0.35, 0.6) if k % 2 else random.uniform(0.5, 1.1)
        caixa(bm, C + d * (AP + 0.0105) + t * u + Vector((0, 0, (ZP + 0.02 + z1) / 2)), (0.001, 0.008, z1 - ZP - 0.02),
              Matrix.Rotation(a, 3, 'Z'))
obj('tambor_escorridos', bm, 'oleo')

# comporta da boca (sobe por dois pistões) e caixa-guia acima
YS = C.y - AP - 0.035                                                     # plano da comporta (por fora da face sul)
bm = bmesh.new()
caixa_de(bm, (-0.182, YS - 0.03, HATCH[3] + 0.03), (0.182, YS - 0.012, HATCH[3] + 0.33))   # caixa onde a comporta se guarda
caixa_de(bm, (-0.182, YS - 0.03, HATCH[3] + 0.33), (0.182, C.y - AP, HATCH[3] + 0.35))
for x in (-0.19, 0.19):                                                   # guias laterais da comporta
    caixa_de(bm, (x - 0.012, YS - 0.012, HATCH[2] - 0.04), (x + 0.012, C.y - AP, HATCH[3] + 0.02))
obj('comporta_caixa', bm, 'grafite')
comporta = bpy.data.objects.new('comporta', None)
sc.collection.objects.link(comporta)
bm = bmesh.new()
caixa_de(bm, (-0.178, YS - 0.008, HATCH[2]), (0.178, YS + 0.008, HATCH[3] + 0.01))
for z in (HATCH[2] + 0.07, HATCH[2] + 0.17):
    caixa_de(bm, (-0.17, YS - 0.014, z), (0.17, YS - 0.008, z + 0.025))   # nervuras
obj('comporta_chapa', bm, 'aco', comporta)
bm = bmesh.new()
for x in (-0.21, 0.21):
    caixa_de(bm, (x - 0.04 if x < 0 else 0.17, YS - 0.06, HATCH[2] - 0.01), (-0.17 if x < 0 else x + 0.025, YS - 0.013, HATCH[2] + 0.025))   # orelhas
obj('comporta_orelhas', bm, 'grafite', comporta)
bm, bc = bmesh.new(), bmesh.new()
for x in (-0.21, 0.21):
    cil(bm, Vector((x, YS - 0.042, 0.42)), 0.02, 0.32, lados=16)          # camisas presas no pedestal
    cil(bm, Vector((x, YS - 0.042, 0.585)), 0.026, 0.02, lados=16)
    caixa_de(bm, (x - 0.03, YS - 0.07, ZP - 0.01), (x + 0.03, C.y - AP, ZP + 0.07))   # mancal inferior
obj('comporta_camisas', bm, 'laranja')
suavizar(sc.objects['comporta_camisas'])
hastes_comporta = []
for x in (-0.21, 0.21):
    h = bpy.data.objects.new('comporta_haste', None)
    sc.collection.objects.link(h)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.5)), 0.009, 1.0, lados=12)
    suavizar(obj('comporta_haste_cromo', bm, 'cromo', h))
    h.location = (x, YS - 0.042, 0.59)
    hastes_comporta.append(h)
bm = bmesh.new()                                                          # sapata de apoio da gaveta (roletes por fora)
caixa_de(bm, (-0.16, C.y - AP - 0.11, 0.64), (0.16, C.y - AP - 0.045, 0.655))
for x in (-0.15, 0.15):
    caixa_de(bm, (x - 0.012, C.y - AP - 0.11, ZP + 0.1), (x + 0.012, C.y - AP - 0.085, 0.64))
    caixa_de(bm, (x - 0.008, C.y - AP - 0.1, 0.655), (x + 0.008, C.y - AP - 0.05, 0.68))   # garfos dos roletes
obj('gaveta_apoio', bm, 'grafite')
bm = bmesh.new()
for y in (C.y - AP - 0.095, C.y - AP - 0.06):
    cil(bm, Vector((0, y, ZG - 0.04)), 0.012, 0.28, Vector((1, 0, 0)), lados=12)
suavizar(obj('gaveta_roletes', bm, 'cromo'))

# gaveta (carro sobre trilhos internos)
gaveta = bpy.data.objects.new('gaveta', None)
sc.collection.objects.link(gaveta)
bm = bmesh.new()
caixa_de(bm, (-0.12, -0.13, -0.025), (0.12, 0.43, -0.003))                # bandeja comprida (balança para fora)
for x in (-0.12, 0.12):
    caixa_de(bm, (x - 0.008, -0.13, -0.025), (x + 0.008, 0.12, 0.02))     # abas laterais
caixa_de(bm, (-0.12, -0.14, -0.025), (0.12, -0.125, 0.015))
obj('gaveta_bandeja', bm, 'aco', gaveta)
bm = bmesh.new()
caixa_de(bm, (-0.115, -0.12, -0.003), (0.115, 0.12, 0.0))                 # pó de cristal acumulado na bandeja
obj('gaveta_po', bm, 'po', gaveta)
bm = bmesh.new()
for x in (-0.1, 0.1):                                                     # trilhos internos, apoiados no piso do tambor
    caixa_de(bm, (x - 0.015, C.y - AP + 0.02, ZG - 0.06), (x + 0.015, C.y + AP - 0.05, ZG - 0.028))
    for y in (-0.3, 0.1, 0.5):
        caixa_de(bm, (x - 0.012, y - 0.012, ZP), (x + 0.012, y + 0.012, ZG - 0.06))
caixa_de(bm, (-0.14, C.y + AP - 0.13, ZG - 0.06), (0.14, C.y + AP - 0.03, ZG + 0.05))   # motor da gaveta (cremalheira)
obj('gaveta_trilhos', bm, 'grafite')

# ------------------------------------------------------------------ interior: anel de campo, lasers, luz
bm = bmesh.new()
toro(bm, Vector((0, Y_DENTRO, 0.9)), 0.14, 0.012)
obj('anel_campo', bm, 'campo')
bm = bmesh.new()
toro(bm, Vector((0, Y_DENTRO, 0.9)), 0.155, 0.006)
for k in range(3):
    a = k * 2 * PI / 3 + PI / 6
    tubo(bm, (math.cos(a) * 0.155, Y_DENTRO + math.sin(a) * 0.155, 0.9), (math.cos(a) * 0.155, Y_DENTRO + math.sin(a) * 0.155, ZT), 0.006, 6)
obj('anel_suporte', bm, 'aco')
LASER_CAB = []
bm = bmesh.new()
for k in range(3):
    a = k * 2 * PI / 3 - PI / 2
    p = Vector((math.cos(a) * 0.33, Y_DENTRO + math.sin(a) * 0.33, 1.12))
    LASER_CAB.append(p)
    alvo = Vector((0, Y_DENTRO, Z_LEV))
    cil(bm, p, 0.03, 0.09, alvo - p, lados=12)
    tubo(bm, p, Vector((p.x, p.y, ZT)), 0.012, 8)
obj('laser_cabecas', bm, 'grafite')
lasers = []
for p in LASER_CAB:
    alvo = Vector((0, Y_DENTRO, Z_LEV))
    bm = bmesh.new()
    tubo(bm, p + (alvo - p).normalized() * 0.05, alvo, 0.0025, 6)
    lasers.append(obj('laser', bm, 'laser'))
luz_an = bpy.data.lights.new('Analisador', 'POINT')
luz_an.color = (0.6, 0.3, 1.0)
luz_an.shadow_soft_size = 0.08
la = bpy.data.objects.new('Analisador', luz_an)
sc.collection.objects.link(la)
la.location = (0, Y_DENTRO, 0.95)
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
nevoa = obj('nevoa', bm, 'nevoa')
nevoa.location = (0, Y_DENTRO, Z_LEV)

# ------------------------------------------------------------------ cinta de resfriamento do tambor
R_CINTA = 0.74
bm = bmesh.new()
toro(bm, C + Vector((0, 0, 0.3)), R_CINTA, 0.018, 64, 12)
obj('cinta', bm, 'cobre')
bm = bmesh.new()
for k in range(8):
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, C + d * ((AP + R_CINTA) / 2) + Vector((0, 0, 0.3)), (R_CINTA - AP, 0.02, 0.05), Matrix.Rotation(a, 3, 'Z'))
obj('cinta_suportes', bm, 'grafite')

# ------------------------------------------------------------------ teto: cúpula de sensores, pilares de cristal, varredor
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.45, matrix=Matrix.Translation(C + Vector((0, 0, ZR))))
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < ZR - 0.001], context='VERTS')
cupula = suavizar(obj('cupula', bm, 'cinza'), True)
bm = bmesh.new()
toro(bm, C + Vector((0, 0, ZR + 0.01)), 0.45, 0.015)                     # colar da cúpula
toro(bm, C + Vector((0, 0, ZR + 0.22)), 0.395, 0.008)                    # costura
obj('cupula_colar', bm, 'grafite')
bm, bl = bmesh.new(), bmesh.new()
for k in range(6):                                                        # sensores: lente escura com aro
    a = k * PI / 3 + PI / 6
    el = math.radians(32)
    n = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
    p = C + Vector((0, 0, ZR)) + n * 0.45
    cil(bm, p + n * 0.02, 0.05, 0.05, n, lados=20)
    cil(bl, p + n * 0.046, 0.034, 0.006, n, lados=20)
obj('sensores', bm, 'grafite')
obj('sensores_lente', bl, 'lente')
bm, bg, bc, ba, bf_campo = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
PILARES = []
for k in range(4):
    a = PI / 4 + k * PI / 2
    p = C + Vector((math.cos(a), math.sin(a), 0)) * 0.52
    PILARES.append(p)
    hexa(bm, Vector((p.x - C.x, p.y - C.y)), 0.04, 0.0, 1.86 - ZR - 0.14, 0.08)   # cristal (no objeto que levita)
    cil(bg, Vector((p.x, p.y, ZR + 0.04)), 0.062, 0.08, lados=8)          # soquete
    toro(bf_campo, Vector((p.x, p.y, ZR + 0.085)), 0.045, 0.006, 24, 6)   # anel de campo no soquete
    q = C + Vector((math.cos(a), math.sin(a), 0)) * 0.36                 # escora do soquete até a cúpula
    tubo(bg, Vector((p.x, p.y, ZR + 0.06)), Vector((q.x, q.y, ZR + math.sqrt(0.45 ** 2 - 0.36 ** 2) - 0.01)), 0.01, 8)
    o = Vector((math.cos(a), math.sin(a), 0))
    mangueira(bc, bezier(Vector((p.x, p.y, ZR + 0.06)) + o * 0.05, Vector((p.x, p.y, ZR + 0.02)) + o * 0.09,
                         C + o * 0.6 + Vector((0, 0, ZR + 0.01)), C + o * 0.56 + Vector((0, 0, ZR + 0.003)), 8), 0.01)
pilares = bpy.data.objects.new('pilares', None)
sc.collection.objects.link(pilares)
pilares.location = (C.x, C.y, ZR + 0.14)
obj('pilares_cristal', bm, 'cristal', pilares)
obj('pilares_campo', bf_campo, 'campo')
obj('pilares_soquetes', bg, 'grafite')
suavizar(obj('pilares_cabos', bc, 'borracha'))
bm = bmesh.new()                                                          # mastro do varredor
cil(bm, C + Vector((0, 0, 1.76)), 0.07, 0.03, lados=16)
cil(bm, C + Vector((0, 0, 1.96)), 0.035, 0.4, lados=16)
cil(bm, C + Vector((0, 0, 2.15)), 0.05, 0.03, lados=16)
suavizar(obj('mastro', bm, 'grafite'))
antena = bpy.data.objects.new('antena', None)
sc.collection.objects.link(antena)
antena.location = C + Vector((0, 0, 2.165))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.03)), 0.06, 0.06, lados=16)                       # cubo giratório
caixa_de(bm, (-0.36, -0.025, 0.04), (0.36, 0.025, 0.07))                  # braço do varredor
caixa(bm, (-0.36, 0, 0.05), (0.06, 0.07, 0.05))                           # contrapeso
obj('varredor', bm, 'amarelo', antena)
bm = bmesh.new()
caixa(bm, (0.38, 0, 0.1), (0.03, 0.22, 0.13), Matrix.Rotation(-0.25, 3, 'Y'))   # painel de sensores do varredor
obj('varredor_painel', bm, 'grafite', antena)
bm = bmesh.new()
for j in range(4):
    caixa(bm, (0.364 + 0.0, -0.075 + j * 0.05, 0.1 + 0.0), (0.004, 0.035, 0.1), Matrix.Rotation(-0.25, 3, 'Y'))
obj('varredor_lentes', bm, 'lente', antena)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.2)), 0.007, 0.32, lados=8)                        # antena chicote
cil(bm, Vector((0, 0, 0.09)), 0.02, 0.05, lados=10)
obj('antena_haste', bm, 'aco', antena)
bm = bmesh.new()
curva(bm, (0, 0, 0.365), 0.012, 10)
obj('antena_ponta', bm, 'giroflex', antena)
bm = bmesh.new()                                                          # caixa de entrada de cabos
caixa_de(bm, (-0.08, C.y + 0.49, ZR), (0.08, C.y + 0.57, ZR + 0.06))      # caixa de passagem de cabos (norte)
obj('teto_caixas', bm, 'grafite')

# ------------------------------------------------------------------ esteira curta de roletes (boca sul)
RR = 0.5 / (50 * 2 * PI / 16)                                             # raio do rolete: o giro fecha o laço
bm = bmesh.new()
for x in (-0.19, 0.19):
    caixa_de(bm, (x - 0.02, -1.44, ZB - 0.09), (x + 0.02, -0.86, ZB - 0.01))   # perfis laterais
    for y in (-1.38, -0.94):
        caixa_de(bm, (x - 0.02, y - 0.02, 0.08), (x + 0.02, y + 0.02, ZB - 0.09))
        caixa_de(bm, (x - 0.04, y - 0.04, 0.08), (x + 0.04, y + 0.04, 0.095))
caixa_de(bm, (-0.19, -0.9, ZB - 0.09), (0.19, -0.86, ZB - 0.06))
for x in (-0.205, 0.205):                                                 # guias laterais
    caixa_de(bm, (x - 0.006, -1.44, ZB + 0.03), (x + 0.006, -0.86, ZB + 0.06))
    for y in (-1.3, -1.0):
        caixa_de(bm, (x - 0.006, y - 0.01, ZB - 0.01), (x + 0.006, y + 0.01, ZB + 0.03))
obj('esteira_estrutura', bm, 'grafite')
bm = bmesh.new()
caixa_de(bm, (-0.21, -0.88, ZB - 0.06), (0.21, -0.86, ZB + 0.09))        # batente final
caixa_de(bm, (-0.24, -1.48, 0.08), (-0.2, -1.44, 0.78))                  # portal da boca
caixa_de(bm, (0.2, -1.48, 0.08), (0.24, -1.44, 0.78))
caixa_de(bm, (-0.24, -1.48, 0.74), (0.24, -1.44, 0.8))
obj('esteira_batente', bm, 'listras')
roletes = []
for i in range(8):
    y = -1.44 + i * 0.07
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), RR, 0.36, Vector((1, 0, 0)), lados=16)
    r = suavizar(obj('rolete', bm, 'aco'))
    r.location = (0, y, ZB - RR)
    roletes.append(r)
bm = bmesh.new()                                                          # motor e capa da corrente (lado leste)
caixa_de(bm, (0.21, -1.4, ZB - 0.11), (0.24, -0.9, ZB - 0.01))
cil(bm, Vector((0.3, -1.25, ZB - 0.06)), 0.045, 0.12, Vector((1, 0, 0)), lados=16)
caixa(bm, (0.26, -1.25, ZB - 0.06), (0.04, 0.1, 0.1))
obj('esteira_motor', bm, 'laranja')
bm = bmesh.new()                                                          # sensor óptico de chegada
caixa_de(bm, (-0.3, -0.98, 0.08), (-0.27, -0.95, ZB + 0.12))
caixa(bm, (-0.25, -0.965, ZB + 0.07), (0.04, 0.03, 0.04))
obj('sensor_chegada', bm, 'grafite')
bm = bmesh.new()
caixa(bm, (-0.229, -0.965, ZB + 0.07), (0.003, 0.012, 0.012))
obj('sensor_chegada_luz', bm, LEDS[1])

# ------------------------------------------------------------------ pacotes de pesquisa (módulo: cristal lapidado + engrenagem)
def engrenagem(bm, c, r, dentes, eixo):
    cil(bm, c, r * 0.82, 0.012, eixo, lados=dentes * 2)
    rot = Vector(eixo).to_track_quat('Z', 'Y').to_matrix()
    for k in range(dentes):
        a = k * 2 * PI / dentes
        caixa(bm, Vector(c) + rot @ Vector((math.cos(a) * r * 0.92, math.sin(a) * r * 0.92, 0)), (r * 0.25, r * 0.18, 0.012),
              rot @ Matrix.Rotation(a, 3, 'Z'))


def pacote(nome):
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    sx, sy, sz = PAC
    bm = bmesh.new()
    for z in (-sz / 2 + 0.007, sz / 2 - 0.007):
        caixa(bm, (0, 0, z), (sx, sy, 0.014))                             # tampas
    for x in (-1, 1):
        for y in (-1, 1):
            caixa(bm, (x * (sx / 2 - 0.007), y * (sy / 2 - 0.007), 0), (0.014, 0.014, sz))   # cantoneiras
    obj(nome + '_quadro', bm, 'aco', raiz)
    bm = bmesh.new()
    hexa(bm, (0, 0), 0.03, -sz / 2 + 0.014, sz / 2 - 0.03, 0.02)
    obj(nome + '_cristal', bm, 'cristal_pac', raiz)
    bm = bmesh.new()
    engrenagem(bm, Vector((sx / 2 + 0.002, 0, 0)), 0.035, 10, Vector((1, 0, 0)))
    engrenagem(bm, Vector((-sx / 2 - 0.002, 0.015, -0.01)), 0.024, 8, Vector((1, 0, 0)))
    obj(nome + '_engrenagem', bm, 'latao', raiz)
    bm = bmesh.new()
    caixa(bm, (0, -sy / 2 - 0.001, 0.0), (0.06, 0.002, 0.02))
    obj(nome + '_etiqueta', bm, LEDS[4], raiz)
    return raiz


PA, PB = pacote('pacote_a'), pacote('pacote_b')
PD = pacote('pacote_dissolvendo')

# ------------------------------------------------------------------ braço pega-e-põe (mesmo desenho da montadora)
L1, L2, G = 0.5, 0.45, 0.16


def braco(nome, pos):
    base_o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(base_o)
    base_o.location = pos
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.03)), 0.2, 0.06, lados=8)
    cil(bm, Vector((0, 0, 0.17)), 0.11, 0.22, lados=16)
    for k in range(6):
        a = k * PI / 3
        cil(bm, Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 0.065)), 0.014, 0.012, lados=6)
    caixa(bm, (-0.15, -0.09, 0.14), (0.07, 0.06, 0.08))                   # caixa de ligação
    obj(nome + '_base', bm, 'grafite', base_o)
    giro = bpy.data.objects.new(nome + '_giro', None)
    sc.collection.objects.link(giro)
    giro.parent = base_o
    giro.location = (0, 0, 0.29)
    bm = bmesh.new()
    caixa(bm, (0, 0, 0.06), (0.24, 0.24, 0.12))
    for x in (-0.085, 0.085):
        caixa(bm, (x, 0, 0.17), (0.035, 0.1, 0.12))
    cil(bm, Vector((-0.17, 0, 0.07)), 0.05, 0.1, Vector((1, 0, 0)), lados=12)
    obj(nome + '_giro_corpo', bm, 'amarelo', giro)
    ombro = bpy.data.objects.new(nome + '_ombro', None)
    sc.collection.objects.link(ombro)
    ombro.parent = giro
    ombro.location = (0, 0, 0.2)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.045, 0.13, Vector((1, 0, 0)), lados=14)
    for x in (-0.04, 0.04):
        caixa_de(bm, (x - 0.012, 0.0, -0.025), (x + 0.012, L1, 0.025))
    for k in range(1, 5):
        caixa(bm, (0, L1 * k / 5, 0), (0.07, 0.014, 0.014))
    cil(bm, Vector((0, L1, 0)), 0.05, 0.12, Vector((1, 0, 0)), lados=14)
    obj(nome + '_braco1', bm, 'amarelo', ombro)
    bm = bmesh.new()
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
    suavizar(obj(nome + '_braco2', bm, 'amarelo', cotovelo))
    bm = bmesh.new()
    mangueira(bm, bezier((0.04, -0.03, 0.03), (0.06, L2 * 0.3, 0.05), (0.05, L2 * 0.7, 0.05), (0.03, L2, 0.03), 8), 0.009)
    suavizar(obj(nome + '_cabos2', bm, 'borracha', cotovelo))
    punho = bpy.data.objects.new(nome + '_punho', None)
    sc.collection.objects.link(punho)
    punho.parent = cotovelo
    punho.location = (0, L2, 0)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.035, 0.08, Vector((1, 0, 0)), lados=14)
    obj(nome + '_pulso', bm, 'grafite', punho)
    pg = bpy.data.objects.new(nome + '_pulso_giro', None)                 # giro do pulso: dedos sempre alinhados ao mundo
    sc.collection.objects.link(pg)
    pg.parent = punho
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -0.04)), 0.03, 0.05, lados=14)
    caixa(bm, (0, 0, -0.08), (0.22, 0.06, 0.04))
    cil(bm, Vector((0, 0.04, -0.08)), 0.014, 0.18, Vector((1, 0, 0)), lados=10)
    obj(nome + '_garra', bm, 'grafite', pg)
    dedos = []
    for sx in (-1, 1):
        d = bpy.data.objects.new(nome + '_dedo', None)
        sc.collection.objects.link(d)
        d.parent = pg
        bm = bmesh.new()
        caixa(bm, (0, 0, -0.12), (0.016, 0.05, 0.07))
        caixa(bm, (-sx * 0.006, 0, -0.15), (0.012, 0.046, 0.012))
        obj(nome + '_dedo_aco', bm, 'aco', d)
        dedos.append((d, sx))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.11)), 0.026, 0.22, lados=14)
    camisa = suavizar(obj(nome + '_camisa', bm, 'grafite'))
    camisa.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.13)), 0.013, 0.26, lados=12)
    haste = suavizar(obj(nome + '_haste', bm, 'cromo'))
    haste.rotation_mode = 'QUATERNION'
    return {'base': base_o, 'giro': giro, 'ombro': ombro, 'cotovelo': cotovelo, 'punho': punho, 'pg': pg,
            'dedos': dedos, 'camisa': camisa, 'haste': haste}


BR = braco('braco', Vector((-0.58, -0.86, 0.08)))
ANCORA, PONTO_B1 = Vector((0, -0.12, 0.12)), Vector((0, 0.24, -0.03))


def ik(b, ponta):
    pulso = Vector(ponta) + Vector((0, 0, G))
    om = b['base'].location + Vector((0, 0, 0.29 + 0.2))
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
    b['pg'].rotation_euler = (0, 0, -th)
    bpy.context.view_layer.update()
    pa = b['giro'].matrix_world @ ANCORA
    pb = b['ombro'].matrix_world @ PONTO_B1
    b['camisa'].location = pa
    b['camisa'].rotation_quaternion = (pb - pa).to_track_quat('Z', 'Y')
    b['haste'].location = pb
    b['haste'].rotation_quaternion = (pa - pb).to_track_quat('Z', 'Y')


def chave(b, q):
    for k in ('giro', 'ombro', 'cotovelo', 'punho', 'pg'):
        b[k].keyframe_insert('rotation_euler', frame=q)
    for k in ('camisa', 'haste'):
        b[k].keyframe_insert('location', frame=q)
        b[k].keyframe_insert('rotation_quaternion', frame=q)


# ------------------------------------------------------------------ racks de servidores e de cristais (norte)
RY0, RY1, RZ1 = 0.95, 1.35, 1.48
RACKS = [(-1.42, -0.94, False), (-0.9, -0.42, True), (0.42, 0.9, False)]
leds_por_mat = {k: bmesh.new() for k in LEDS}
for x0, x1, de_cristal in RACKS:
    bm = bmesh.new()
    caixa_de(bm, (x0, RY0, 0.08), (x0 + 0.02, RY1, RZ1))
    caixa_de(bm, (x1 - 0.02, RY0, 0.08), (x1, RY1, RZ1))
    caixa_de(bm, (x0, RY0, RZ1 - 0.03), (x1, RY1, RZ1))
    caixa_de(bm, (x0, RY1 - 0.02, 0.08), (x1, RY1, RZ1))
    caixa_de(bm, (x0, RY0, 0.08), (x1, RY1, 0.16))
    for x in (x0 + 0.04, x1 - 0.04):                                      # pés niveladores
        for y in (RY0 + 0.04, RY1 - 0.04):
            cil(bm, Vector((x, y, 0.085)), 0.02, 0.01, lados=8)
    obj('rack', bm, 'grafite')
    if de_cristal:                                                        # gaveteiro aberto: cristais levitam sobre os soquetes
        bm, bc = bmesh.new(), bmesh.new()
        for j in range(4):                                                # prateleiras com soquetes
            z = 0.24 + j * 0.3
            caixa_de(bm, (x0 + 0.02, RY0 + 0.02, z - 0.02), (x1 - 0.02, RY1 - 0.04, z))
            for i in range(6):
                x = x0 + 0.07 + i * (x1 - x0 - 0.14) / 5
                cil(bm, Vector((x, RY0 + 0.15, z + 0.015)), 0.025, 0.03, lados=6)
                hexa(bc, (x, RY0 + 0.15), 0.017, z + 0.06, z + 0.22 - (0.04 if (i + j) % 3 == 0 else 0), 0.035)
        obj('rack_prateleiras', bm, 'aco')
        cristais_rack = obj('rack_cristais', bc, 'cristal_rack')
    else:
        bm = bmesh.new()
        for j in range(12):                                               # servidores 1U/2U
            z0 = 0.2 + j * 0.1
            caixa_de(bm, (x0 + 0.025, RY0 + 0.01, z0), (x1 - 0.025, RY1 - 0.05, z0 + 0.085))
            for i in range(5):
                xl = x0 + 0.06 + i * 0.035
                caixa(leds_por_mat[random.choice(LEDS)], (xl, RY0 + 0.007, z0 + 0.06), (0.012, 0.006, 0.008))
            for i in range(6):                                            # baias de disco
                xd = x0 + 0.26 + i * 0.032
                caixa(bm, (xd, RY0 + 0.007, z0 + 0.042), (0.026, 0.006, 0.06))
        obj('rack_servidores', bm, 'servidor')
for k, b in leds_por_mat.items():
    obj('leds', b, k)

# ------------------------------------------------------------------ eletrocalha e feixes de dados
ZE = 1.66
bm, bc, ba = bmesh.new(), bmesh.new(), bmesh.new()
YE0, YE1 = 1.08, 1.32
for y in (YE0, YE1):                                                      # calha principal (escada), leste-oeste
    caixa_de(bm, (-1.42, y - 0.006, ZE), (1.06, y + 0.006, ZE + 0.07))
for k in range(17):
    x = -1.38 + k * 0.15
    caixa_de(bm, (x - 0.012, YE0, ZE), (x + 0.012, YE1, ZE + 0.012))
for x in (-0.07, 0.07):                                                   # ramal até o tambor
    caixa_de(bm, (x - 0.006, 0.7, ZE), (x + 0.006, YE0, ZE + 0.06))
for k in range(3):
    y = 0.74 + k * 0.13
    caixa_de(bm, (-0.07, y - 0.012, ZE), (0.07, y + 0.012, ZE + 0.012))
for x in (-1.35, -0.15, 1.02):                                            # postes atrás dos racks e mão-francesa
    caixa_de(bm, (x - 0.02, 1.42, 0.08), (x + 0.02, 1.46, ZE + 0.1))
    caixa_de(bm, (x - 0.04, 1.4, 0.08), (x + 0.04, 1.48, 0.1))
    caixa_de(bm, (x - 0.015, YE0 - 0.02, ZE - 0.03), (x + 0.015, 1.46, ZE))
    viga(bm, Vector((x, 1.44, ZE - 0.18)), Vector((x, YE0 + 0.05, ZE - 0.02)), 0.02)
caixa_de(bm, (0.1, 0.88, 0.08), (0.14, 0.92, ZE - 0.02))                  # poste do ramal
caixa_de(bm, (-0.1, 0.88, ZE - 0.03), (0.14, 0.92, ZE))
caixa_de(bm, (0.08, 0.86, 0.08), (0.16, 0.94, 0.1))
obj('eletrocalha', bm, 'aco')
bmc2 = bmesh.new()
for i in range(6):                                                        # cabos deitados na calha
    y = YE0 + 0.03 + i * 0.035
    mangueira(bc if i % 2 else bmc2, [Vector((-1.4, y, ZE + 0.022)), Vector((1.04, y, ZE + 0.022))], 0.011)
for i in range(3):
    x = -0.04 + i * 0.04
    mangueira(bc, [Vector((x, 0.72, ZE + 0.022)), Vector((x, YE0 + 0.02, ZE + 0.022))], 0.011)
for x0, x1, _ in RACKS:                                                   # feixes saindo do topo dos racks
    xc = (x0 + x1) / 2
    caixa_de(bm2 := bmesh.new(), (xc - 0.08, 1.1, RZ1), (xc + 0.08, 1.22, RZ1 + 0.04))
    obj('rack_prensa_cabo', bm2, 'grafite')
    feixe(bc, ba, bezier(Vector((xc, 1.16, RZ1 + 0.03)), Vector((xc, 1.16, RZ1 + 0.1)), Vector((xc + 0.05, 1.2, ZE - 0.05)),
                         Vector((xc + 0.1, 1.2, ZE + 0.02)), 8), n=4, r=0.01, passo=3)
feixe(bc, ba, bezier(Vector((0, 0.72, ZE + 0.02)), Vector((0, 0.66, ZE)), Vector((0, 0.66, ZR + 0.2)),
                     Vector((0, C.y + 0.53, ZR + 0.06)), 10), n=4, r=0.011, passo=3)
suavizar(obj('cabos_dados', bc, 'borracha'))
suavizar(obj('cabos_dados_laranja', bmc2, 'laranja'))
suavizar(obj('abracadeiras', ba, 'aco'))

# ------------------------------------------------------------------ refrigeração líquida: radiador seco, bomba, reservatório
RX0, RX1, RY_0, RY_1 = 1.02, 1.42, -0.82, 0.46
ZRAD = 0.66
bm = bmesh.new()
caixa_de(bm, (RX0, RY_0, 0.42), (RX1, RY_1, ZRAD - 0.01))                 # caixa da serpentina
for x in (RX0 + 0.03, RX1 - 0.03):                                        # pernas
    for y in (RY_0 + 0.03, RY_1 - 0.03, (RY_0 + RY_1) / 2):
        caixa_de(bm, (x - 0.025, y - 0.025, 0.08), (x + 0.025, y + 0.025, 0.42))
        caixa_de(bm, (x - 0.045, y - 0.045, 0.08), (x + 0.045, y + 0.045, 0.095))
caixa_de(bm, (RX0, RY_0, ZRAD - 0.01), (RX1, RY_0 + 0.03, ZRAD + 0.03))   # moldura do topo
caixa_de(bm, (RX0, RY_1 - 0.03, ZRAD - 0.01), (RX1, RY_1, ZRAD + 0.03))
caixa_de(bm, (RX0, RY_0, ZRAD - 0.01), (RX0 + 0.03, RY_1, ZRAD + 0.03))
caixa_de(bm, (RX1 - 0.03, RY_0, ZRAD - 0.01), (RX1, RY_1, ZRAD + 0.03))
caixa_de(bm, (RX0 + 0.03, -0.19, ZRAD - 0.01), (RX1 - 0.03, -0.16, ZRAD + 0.03))
obj('radiador', bm, 'radiador')
bm = bmesh.new()
for k in range(56):                                                       # aletas da serpentina
    y = RY_0 + 0.035 + k * (RY_1 - RY_0 - 0.07) / 55
    caixa_de(bm, (RX0 + 0.03, y - 0.0015, ZRAD - 0.03), (RX1 - 0.03, y + 0.0015, ZRAD + 0.01))
obj('radiador_aletas', bm, 'aluminio')
bm, bf = bmesh.new(), bmesh.new()                                         # coletores de entrada (oeste) e saída (leste)
cano(bm, bf, [Vector((RX0 - 0.03, RY_0 + 0.05, 0.55)), Vector((RX0 - 0.03, RY_1 - 0.05, 0.55))], 0.03)
cano(bm, bf, [Vector((RX1 + 0.03, RY_0 + 0.05, 0.5)), Vector((RX1 + 0.03, RY_1 + 0.07, 0.5))], 0.025)
for y in (RY_0 + 0.05, RY_1 - 0.05):
    cil(bm, Vector((RX0 - 0.03, y, 0.55)), 0.034, 0.02, Vector((0, 1, 0)), lados=16)   # tampões
cil(bm, Vector((RX1 + 0.03, RY_0 + 0.05, 0.5)), 0.03, 0.02, Vector((0, 1, 0)), lados=16)
for y in (RY_0 + 0.25, RY_1 - 0.25):
    tubo(bf, (RX0 - 0.03, y, 0.55), (RX0, y, 0.55), 0.015, 10)
    tubo(bf, (RX1, y, 0.5), (RX1 + 0.03, y, 0.5), 0.015, 10)
obj('radiador_coletores', bm, 'cobre')
suavizar(sc.objects['radiador_coletores'])
obj('radiador_coletores_flanges', bf, 'grafite')
VENT = [Vector((1.22, -0.5, ZRAD)), Vector((1.22, 0.15, ZRAD))]
ventiladores = []
for k, v in enumerate(VENT):
    bm = bmesh.new()
    casca(bm, v, 0.19, 0.175, 0.02, 0.12, 40)                             # anel venturi
    obj('vent_anel', bm, 'radiador')
    bm = bmesh.new()
    for R in (0.06, 0.12, 0.175):                                         # grade de proteção
        toro(bm, v + Vector((0, 0, 0.13)), R, 0.003, 48, 6)
    for j in range(6):
        a = j * PI / 3
        tubo(bm, v + Vector((0, 0, 0.13)), v + Vector((math.cos(a) * 0.185, math.sin(a) * 0.185, 0.13)), 0.004, 6)
    cil(bm, v + Vector((0, 0, 0.1)), 0.05, 0.06, lados=16)               # motor no centro da grade
    obj('vent_grade', bm, 'grafite')
    rotor = bpy.data.objects.new('vent_rotor', None)
    sc.collection.objects.link(rotor)
    rotor.location = v + Vector((0, 0, 0.055))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.04, 0.03, lados=16)
    for j in range(7):
        a = j * 2 * PI / 7
        caixa(bm, (math.cos(a) * 0.105, math.sin(a) * 0.105, 0), (0.13, 0.055, 0.004),
              Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(0.4, 3, 'X'))
    obj('vent_pas', bm, 'cinza', rotor)
    ventiladores.append(rotor)
bm = bmesh.new()                                                          # caixa de ligação dos ventiladores
caixa_de(bm, (RX1 - 0.005, -0.25, 0.48), (RX1 + 0.03, -0.1, 0.6))
obj('radiador_caixa', bm, 'cinza')

BP = Vector((1.15, 0.78, 0.0))                                            # bomba
bm = bmesh.new()
caixa_de(bm, (1.0, 0.6, 0.08), (1.38, 0.98, 0.12))                        # skid
for y in (0.68, 0.9):
    caixa_de(bm, (1.08, y - 0.03, 0.12), (1.22, y + 0.03, 0.2))
obj('bomba_skid', bm, 'grafite')
bm = bmesh.new()
cil(bm, BP + Vector((0, 0.06, 0.3)), 0.11, 0.07, Vector((0, 1, 0)), lados=24)   # voluta
cil(bm, BP + Vector((0, -0.03, 0.3)), 0.04, 0.1, Vector((0, 1, 0)), lados=16)   # bocal de sucção
cil(bm, BP + Vector((0, 0.06, 0.4)), 0.035, 0.08, lados=16)              # bocal de recalque
obj('bomba_voluta', bm, 'laranja')
suavizar(sc.objects['bomba_voluta'])
bm = bmesh.new()
cil(bm, BP + Vector((0, 0.24, 0.3)), 0.085, 0.26, Vector((0, 1, 0)), lados=24)   # motor com aletas
for k in range(8):
    cil(bm, BP + Vector((0, 0.13 + k * 0.03, 0.3)), 0.095, 0.006, Vector((0, 1, 0)), lados=24)
caixa(bm, BP + Vector((0, 0.24, 0.4)), (0.08, 0.08, 0.05))
obj('bomba_motor', bm, 'grafite')
suavizar(sc.objects['bomba_motor'])
RES = Vector((1.32, 1.2, 0.08))                                           # reservatório de expansão
bm = bmesh.new()
cil(bm, RES + Vector((0, 0, 0.38)), 0.1, 0.56, lados=24)
cil(bm, RES + Vector((0, 0, 0.68)), 0.05, 0.04, lados=16)
obj('reservatorio', bm, 'cinza')
suavizar(sc.objects['reservatorio'])
bm = bmesh.new()
for z in (0.12, 0.64):
    cil(bm, RES + Vector((0, 0, z)), 0.105, 0.025, lados=24)
for a in (0.0, 2.1, 4.2):
    caixa_de(bm, RES + Vector((math.cos(a) * 0.09 - 0.012, math.sin(a) * 0.09 - 0.012, 0.0)),
             RES + Vector((math.cos(a) * 0.09 + 0.012, math.sin(a) * 0.09 + 0.012, 0.13)))
obj('reservatorio_cintas', bm, 'grafite')
bm = bmesh.new()                                                          # visor de nível com fluido verde
caixa(bm, RES + Vector((-0.1, 0, 0.4)), (0.012, 0.03, 0.4))
obj('reservatorio_visor', bm, 'liquido')
bm, bmi, bf = bmesh.new(), bmesh.new(), bmesh.new()
Z1 = 0.3
# retorno quente (cobre): radiador → bomba; reservatório na sucção
cano(bm, bf, [Vector((RX1 + 0.03, RY_1 + 0.07, 0.5)), Vector((RX1 + 0.03, 0.58, 0.5)), Vector((RX1 + 0.03, 0.58, Z1)),
              BP + Vector((0, 0.58 - BP.y, Z1)), BP + Vector((0, -0.08, Z1))], 0.025)
cano(bm, bf, [RES + Vector((0, -0.1, 0.07)), Vector((RES.x, 0.58, 0.15)), Vector((RES.x, 0.58, Z1 - 0.025))], 0.018)
# ida fria (isolada): bomba → racks (atrás) e → cinta do tambor
YT = 1.385
cano(bmi, bf, [BP + Vector((0, 0.06, 0.44)), BP + Vector((0, 0.06, 0.55)), Vector((BP.x, YT, 0.55)), Vector((-1.3, YT, 0.55))], 0.026)
cano(bmi, bf, [BP + Vector((0, 0.06, 0.48)), Vector((0.75, BP.y + 0.06, 0.48)), Vector((0.75, BP.y + 0.06, 0.3)),
               Vector((0.75, 0.6, 0.3)), Vector((math.sqrt(R_CINTA ** 2 - (0.6 - C.y) ** 2) + 0.005, 0.6, 0.3))], 0.022)
for x0, x1, _ in RACKS:
    xc = x0 + 0.1
    tubo(bm, (xc, YT, 0.55), (xc, RY1 - 0.01, 0.55), 0.016, 12)          # ramais de ida
    tubo(bm, (x1 - 0.1, YT, 1.3), (x1 - 0.1, RY1 - 0.01, 1.3), 0.016, 12)  # ramais de volta
    cil(bf, Vector((xc, RY1 + 0.005, 0.55)), 0.03, 0.012, Vector((0, 1, 0)), lados=12)
    cil(bf, Vector((x1 - 0.1, RY1 + 0.005, 1.3)), 0.03, 0.012, Vector((0, 1, 0)), lados=12)
# retorno quente dos racks e da cinta até o radiador
cano(bm, bf, [Vector((-1.3, YT, 1.3)), Vector((0.95, YT, 1.3)), Vector((0.95, -0.6, 1.3)), Vector((0.95, -0.6, 0.55)),
              Vector((RX0 - 0.03, -0.6, 0.55))], 0.025)
YC = -0.15
cano(bm, bf, [Vector((math.sqrt(R_CINTA ** 2 - (YC - C.y) ** 2) - 0.005, YC, 0.3)), Vector((0.85, YC, 0.3)),
              Vector((0.85, YC, 0.55)), Vector((RX0 - 0.03, YC, 0.55))], 0.02)
suavizar(obj('canos_retorno', bm, 'cobre'))
suavizar(obj('canos_ida', bmi, 'isolante'))
suavizar(obj('canos_flanges', bf, 'grafite'))
bm = bmesh.new()                                                          # cavaletes do retorno alto
for y in (0.4, -0.35):
    caixa_de(bm, (0.93, y - 0.02, 0.08), (0.97, y + 0.02, 1.27))
    caixa_de(bm, (0.91, y - 0.04, 0.08), (0.99, y + 0.04, 0.095))
    caixa_de(bm, (0.91, y - 0.03, 1.265), (0.99, y + 0.03, 1.275))
obj('cavaletes', bm, 'grafite')
bm = bmesh.new()                                                          # manômetros e válvula na ida
for p in (BP + Vector((0.06, 0.06, 0.52)), Vector((0.75, BP.y + 0.06, 0.4))):
    cil(bm, p, 0.008, 0.05, Vector((1, 0, 0)), lados=8)
    cil(bm, p + Vector((0.035, 0, 0)), 0.03, 0.015, Vector((1, 0, 0)), lados=20)
obj('manometros', bm, 'cromo')
bm = bmesh.new()
cil(bm, Vector((0.92, BP.y + 0.06, 0.48)), 0.035, 0.07, Vector((1, 0, 0)), lados=16)
cil(bm, Vector((0.92, BP.y + 0.06, 0.56)), 0.007, 0.08, lados=8)
toro(bm, Vector((0.92, BP.y + 0.06, 0.6)), 0.04, 0.006, 24, 6)
obj('valvula', bm, 'laranja')

# ------------------------------------------------------------------ exaustor centrífugo e chaminé (oeste)
EX = Vector((-1.16, 0.1, 0.0))
bm = bmesh.new()
caixa_de(bm, EX + Vector((-0.2, -0.2, 0.72)), EX + Vector((0.2, 0.2, 1.12)))      # caixa do rotor
cil(bm, EX + Vector((0, -0.2, 0.92)), 0.15, 0.03, Vector((0, 1, 0)), lados=24)    # tampa do rotor
obj('exaustor', bm, 'amarelo')
bm = bmesh.new()
for x in (-0.17, 0.17):
    for y in (-0.17, 0.17):
        caixa_de(bm, EX + Vector((x - 0.02, y - 0.02, 0.08)), EX + Vector((x + 0.02, y + 0.02, 0.72)))
        caixa_de(bm, EX + Vector((x - 0.04, y - 0.04, 0.08)), EX + Vector((x + 0.04, y + 0.04, 0.095)))
caixa_de(bm, EX + Vector((-0.2, 0.2, 0.75)), EX + Vector((0.2, 0.42, 0.77)))      # base do motor
cil(bm, EX + Vector((0, 0.32, 0.84)), 0.065, 0.16, Vector((0, 1, 0)), lados=16)
for k in range(5):
    cil(bm, EX + Vector((0, 0.26 + k * 0.03, 0.84)), 0.075, 0.006, Vector((0, 1, 0)), lados=16)
caixa(bm, EX + Vector((0.1, 0.3, 0.84)), (0.03, 0.16, 0.12))                       # capa da correia
obj('exaustor_motor', bm, 'grafite')
bm, bf = bmesh.new(), bmesh.new()
cano(bm, bf, [Vector((-AP - 0.01, C.y, 0.95)), Vector((EX.x + 0.2, C.y, 0.95))], 0.07)   # duto do tambor
cano(bm, bf, [EX + Vector((0, 0, 1.12)), EX + Vector((0, 0, 2.12))], 0.085)              # chaminé
cil(bm, EX + Vector((0, 0, 2.22)), 0.15, 0.015, lados=24)                                 # chapéu
for k in range(3):
    a = k * 2 * PI / 3
    tubo(bm, EX + Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, 2.12)), EX + Vector((math.cos(a) * 0.11, math.sin(a) * 0.11, 2.215)), 0.006, 6)
suavizar(obj('dutos', bm, 'aluminio'))
suavizar(obj('dutos_flanges', bf, 'grafite'))
bm = bmesh.new()
for k in range(4):                                                        # estais da chaminé
    a = k * PI / 2 + PI / 4
    tubo(bm, EX + Vector((math.cos(a) * 0.09, math.sin(a) * 0.09, 1.75)), EX + Vector((math.cos(a) * 0.27, math.sin(a) * 0.27, 1.12)), 0.005, 6)
obj('estais', bm, 'aco')
bm = bmesh.new()                                                          # fuligem e condensado escorrido
for k in range(7):
    a = random.uniform(0, 2 * PI)
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, EX + d * 0.087 + Vector((0, 0, random.uniform(1.8, 2.05))), (0.003, 0.025, random.uniform(0.1, 0.3)), Matrix.Rotation(a, 3, 'Z'))
obj('chamine_fuligem', bm, 'fuligem')
vapores = []
for k in range(4):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))

# ------------------------------------------------------------------ unidade de força (sudoeste): transformador e anel levitando
PF = (-1.42, -1.42, -1.04, -1.12)                                          # x0, y0, x1, y1
TF = Vector(((PF[0] + PF[2]) / 2, (PF[1] + PF[3]) / 2, 0))
bm = bmesh.new()
caixa_de(bm, (PF[0] + 0.05, PF[1] + 0.04, 0.08), (PF[2] - 0.02, PF[3] - 0.04, 0.72))   # tanque
caixa_de(bm, (PF[0] + 0.03, PF[1] + 0.02, 0.72), (PF[2], PF[3] - 0.02, 0.76))           # tampa
obj('trafo', bm, 'cinza')
bm = bmesh.new()
for k in range(7):                                                        # aletas de calor (norte e sul)
    x = PF[0] + 0.08 + k * 0.045
    for y0, y1 in ((PF[1], PF[1] + 0.04), (PF[3] - 0.04, PF[3])):
        caixa_de(bm, (x - 0.006, y0, 0.14), (x + 0.006, y1, 0.66))
for k in range(5):                                                        # aletas (oeste)
    y = PF[1] + 0.07 + k * 0.04
    caixa_de(bm, (PF[0], y - 0.006, 0.14), (PF[0] + 0.05, y + 0.006, 0.66))
caixa_de(bm, (PF[2] - 0.02, -1.3, 0.08), (PF[2] + 0.02, -1.12, 0.2))      # caixa de saída dos cabos
obj('trafo_aletas', bm, 'grafite')
BUCHAS = [TF + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0)) for a in (PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3)]
bm, bc = bmesh.new(), bmesh.new()
for p in BUCHAS:                                                          # buchas isolantes com saias
    cil(bm, p + Vector((0, 0, 0.88)), 0.028, 0.24, lados=16)
    for k in range(5):
        cil(bm, p + Vector((0, 0, 0.79 + k * 0.045)), 0.05, 0.012, lados=16)
    cil(bc, p + Vector((0, 0, 1.03)), 0.018, 0.06, lados=12)              # terminal
obj('trafo_buchas', bm, 'isolador')
suavizar(sc.objects['trafo_buchas'])
obj('trafo_terminais', bc, 'cobre')
anel_forca = bpy.data.objects.new('anel_forca', None)                     # anel de campo que levita sobre as buchas
sc.collection.objects.link(anel_forca)
anel_forca.location = TF + Vector((0, 0, 1.2))
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), 0.15, 0.014, 48, 10)
obj('anel_forca_luz', bm, 'energia', anel_forca)
bm = bmesh.new()
for k in range(4):                                                        # quatro sapatas de aço no anel
    a = k * PI / 2
    caixa(bm, (math.cos(a) * 0.15, math.sin(a) * 0.15, 0), (0.05, 0.03, 0.04), Matrix.Rotation(a, 3, 'Z'))
obj('anel_forca_sapatas', bm, 'aco', anel_forca)
bm, ba = bmesh.new(), bmesh.new()
mangueira(bm, [Vector((-1.5, -1.28, 0.12)), Vector((PF[0] + 0.02, -1.28, 0.12))], 0.03)         # entrada de energia
feixe(bm, ba, bezier(Vector((PF[2] - 0.02, -1.15, 0.12)), Vector((-1.0, -0.7, 0.11)), Vector((-0.95, -0.42, 0.11)),
                     C + Vector((math.cos(1.25 * PI), math.sin(1.25 * PI), 0)) * 0.67 + Vector((0, 0, 0.12)), 18),
      n=2, r=0.022, passo=5)
feixe(bm, ba, bezier(Vector((PF[2] - 0.02, -1.22, 0.12)), Vector((-0.9, -1.2, 0.1)), Vector((-0.85, -1.0, 0.1)),
                     BR['base'].location + Vector((-0.17, -0.09, 0.1)), 14), n=2, r=0.012, passo=4)
suavizar(obj('cabos_forca', bm, 'borracha'))
suavizar(obj('cabos_forca_abracadeiras', ba, 'aco'))
bm = bmesh.new()
for k in range(3):                                                        # entrada dos cabos no pedestal do tambor
    a = 1.25 * PI
    d = Vector((math.cos(a), math.sin(a), 0))
caixa(bm, C + Vector((math.cos(1.25 * PI), math.sin(1.25 * PI), 0)) * 0.665 + Vector((0, 0, 0.13)), (0.03, 0.14, 0.1),
      Matrix.Rotation(1.25 * PI, 3, 'Z'))
obj('prensa_cabo_forca', bm, 'grafite')

# ------------------------------------------------------------------ sujeira: óleo, poeira e lascas de cristal
bm = bmesh.new()
for c, r in (((1.12, 0.8), 0.12), ((1.3, 0.62), 0.05), ((-0.62, -0.7), 0.09), ((0.36, -1.22), 0.07),
             ((1.18, -0.3), 0.08), ((-1.0, 0.2), 0.06), ((0.7, 0.85), 0.05)):
    mancha(bm, c, r, 0.0835)
for k in range(5):                                                        # escorridos no radiador e na bomba
    y = random.uniform(RY_0 + 0.1, RY_1 - 0.1)
    caixa_de(bm, (RX0 - 0.001, y, 0.43), (RX0, y + 0.007, random.uniform(0.5, 0.62)))
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for c, r in (((0.0, -0.66), 0.13), ((0.12, -0.84), 0.07), ((-0.2, -0.6), 0.07), ((0.45, -0.45), 0.06),
             ((0.0, -1.1), 0.06)):
    mancha(bm, c, r, 0.0838)
for k in range(4):                                                        # pó escorrido da boca no pedestal
    x = random.uniform(-0.25, 0.25)
    caixa_de(bm, (x, C.y - 0.66 - 0.001, 0.09), (x + random.uniform(0.04, 0.1), C.y - 0.66, ZP))
obj('po_cristal', bm, 'po')
bm, bs = bmesh.new(), bmesh.new()
for k in range(70):                                                       # lascas de cristal e grãos de pó
    p = Vector((random.gauss(0.0, 0.28), random.uniform(-0.98, -0.5), 0.085))
    if abs(p.x) < 0.22 and p.y < -0.84:
        p.x = math.copysign(random.uniform(0.24, 0.4), p.x if p.x else 1)
    alvo = bs if k % 3 else bm
    cil(alvo, p, random.uniform(0.003, 0.008), random.uniform(0.004, 0.012), Vector((random.uniform(-1, 1), random.uniform(-1, 1), 1)), lados=6)
obj('lascas', bm, 'lasca')
obj('graos', bs, 'po')
bm = bmesh.new()                                                          # fuligem sob a chaminé e no exaustor
mancha(bm, (-1.16, 0.1), 0.2, 0.0832)
obj('fuligem_piso', bm, 'fuligem')

# ------------------------------------------------------------------ animação
DUR = QUADROS / FPS


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return Vector(a) + (Vector(b) - Vector(a)) * x


def seg(t, marcos):
    """Interpola posições por marcos [(t0, p0), (t1, p1), ...] com suavização entre eles."""
    if t <= marcos[0][0]:
        return Vector(marcos[0][1])
    for (t0, p0), (t1, p1) in zip(marcos, marcos[1:]):
        if t <= t1:
            return lerp(p0, p1, suave((t - t0) / (t1 - t0)))
    return Vector(marcos[-1][1])


def y_gaveta(t):
    if t < 1.5:
        return Y_DENTRO
    if t < 2.15:
        return Y_DENTRO + (Y_FORA - Y_DENTRO) * suave((t - 1.5) / 0.65)
    if t < 3.15:
        return Y_FORA
    if t < 3.75:
        return Y_FORA + (Y_DENTRO - Y_FORA) * suave((t - 3.15) / 0.6)
    return Y_DENTRO


def comporta_sobe(t):
    if t < 1.2:
        return 0.0
    if t < 1.45:
        return suave((t - 1.2) / 0.25)
    if t < 3.78:
        return 1.0
    return 1.0 - suave((t - 3.78) / 0.2)


ZPAC = PAC[2] / 2
PARA = Vector((0, Y_PARA, ZB + ZPAC))
ALTO = Vector((0, Y_PARA, 0.96))
SOBRE = Vector((0, Y_FORA, 0.96))
NA_GAVETA = Vector((0, Y_FORA, ZG + ZPAC))
MARCOS = [(0.0, ALTO), (1.95, ALTO), (2.12, PARA), (2.22, PARA), (2.45, ALTO), (2.75, SOBRE), (2.95, NA_GAVETA),
          (3.05, NA_GAVETA), (3.25, SOBRE), (3.6, ALTO), (4.0, ALTO)]
em_led = [base3d.M[k].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'] for k in LEDS]
em_cristal = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_rack = base3d.M['cristal_rack'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_campo = base3d.M['campo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_energia = base3d.M['energia'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_giro = base3d.M['giroflex'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
padroes = [[random.random() < 0.6 for _ in range(32)] for _ in LEDS]

for q in range(1, QUADROS + 1):
    t = (q - 1) / FPS
    fr = (q - 1) / QUADROS
    # roletes giram só enquanto a esteira anda (0–2 s)
    s = 0.25 * min(t, 2.0)
    for r in roletes:
        r.rotation_euler = (-s / RR, 0, 0)
        r.keyframe_insert('rotation_euler', frame=q)
    # braço
    p = seg(t, MARCOS)
    ik(BR, p)
    chave(BR, q)
    fecha = suave((t - 2.12) / 0.08) * (1 - suave((t - 2.95) / 0.08))
    for d, sx in BR['dedos']:
        d.location = (sx * (0.1 - (0.1 - PAC[0] / 2 - 0.008) * fecha), 0, 0)
        d.keyframe_insert('location', frame=q)
    # gaveta e comporta
    yg = y_gaveta(t)
    gaveta.location = (0, yg, ZG)
    gaveta.keyframe_insert('location', frame=q)
    cs = comporta_sobe(t)
    comporta.location = (0, 0, 0.28 * cs)
    comporta.keyframe_insert('location', frame=q)
    for h in hastes_comporta:
        h.scale = (1, 1, 0.28 * cs + 0.03)
        h.location.z = 0.59
        h.keyframe_insert('scale', frame=q)
    # pacote A: esteira → parado → garra → gaveta → some dentro do tambor
    if t < 2.0:
        pa = Vector((0, -1.45 + 0.25 * t, ZB + ZPAC))
    elif t < 2.22:
        pa = PARA
    elif t < 2.95:
        pa = p
    else:
        pa = Vector((0, yg, ZG + ZPAC))
    PA.location = pa
    PA.hide_render = t >= 3.75
    PB.location = (0, -1.95 + 0.25 * min(t, 2.0), ZB + ZPAC)
    PB.hide_render = PB.location.y < -1.5
    for o in (PA, PB):
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('hide_render', frame=q)
    for o in list(PA.children) + list(PB.children):
        o.hide_render = o.parent.hide_render
        o.keyframe_insert('hide_render', frame=q)
    # pacote dissolvendo (3,75 s → 1,5 s do ciclo seguinte)
    u = ((t - 3.75) % 4.0) / 1.75
    dissolve = u < 1.0
    sobe = suave(u / 0.3)                                                 # levita da gaveta até o anel de campo
    PD.location = (0, Y_DENTRO, ZG + ZPAC + 0.01 + (Z_LEV - ZG - ZPAC - 0.01) * sobe)
    PD.scale = (1 - 0.6 * u, 1 - 0.6 * u, 1 - 0.75 * u) if dissolve else (0.4, 0.4, 0.25)
    PD.rotation_euler = (0.3 * sobe * math.sin(6 * u), 0.2 * sobe, 4.0 * u)
    for o in [PD] + list(PD.children):
        o.hide_render = not dissolve
        o.keyframe_insert('hide_render', frame=q)
    for c in ('location', 'scale', 'rotation_euler'):
        PD.keyframe_insert(c, frame=q)
    forca = math.sin(PI * min(u, 1.0)) if dissolve else 0.0
    tremor = 1 + 0.15 * math.sin(fr * 2 * PI * 17)
    nevoa.hide_render = forca < 0.05
    nevoa.scale = [0.07 + 0.06 * forca * tremor] * 3
    for c in ('scale', 'hide_render'):
        nevoa.keyframe_insert(c, frame=q)
    for o in lasers:
        o.hide_render = not (dissolve and int(t * 12) % 4 != 0)
        o.keyframe_insert('hide_render', frame=q)
    luz_an.energy = 6 + 40 * forca * tremor
    luz_an.keyframe_insert('energy', frame=q)
    em_campo.default_value = 2.0 + 10.0 * forca * tremor
    em_campo.keyframe_insert('default_value', frame=q)
    # varredor e ventiladores
    antena.rotation_euler = (0, 0, 2 * PI * fr)
    antena.keyframe_insert('rotation_euler', frame=q)
    for k, v in enumerate(ventiladores):
        v.rotation_euler = (0, 0, -2 * PI * 4 * fr + k * 0.4)
        v.keyframe_insert('rotation_euler', frame=q)
    # vapor do exaustor
    for k, o in enumerate(vapores):
        uu = (k / len(vapores) + fr * 2) % 1.0
        o.location = EX + Vector((0.25 * uu * uu, 0.12 * uu, 2.25 + 0.75 * uu))
        o.scale = [0.08 + 0.22 * uu] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # luzes: LEDs em padrões aleatórios, cristais pulsando, giroflex com a comporta aberta
    for i, e in enumerate(em_led):
        e.default_value = 6.0 if padroes[i][int(t * 8) % 32] else 0.4
        e.keyframe_insert('default_value', frame=q)
    em_cristal.default_value = 0.6 + 0.8 * (0.5 + 0.5 * math.sin(2 * PI * fr * 2)) + 1.2 * forca
    pilares.location.z = ZR + 0.14 + 0.012 * math.sin(2 * PI * fr * 2)
    pilares.keyframe_insert('location', frame=q)
    cristais_rack.location.z = 0.006 * math.sin(2 * PI * fr * 3 + 1.0)
    cristais_rack.keyframe_insert('location', frame=q)
    anel_forca.location.z = 1.2 + 0.02 * math.sin(2 * PI * fr * 2 + 0.5)
    anel_forca.rotation_euler = (0.06 * math.sin(2 * PI * fr), 0.06 * math.cos(2 * PI * fr), 2 * PI * fr)
    anel_forca.keyframe_insert('location', frame=q)
    anel_forca.keyframe_insert('rotation_euler', frame=q)
    em_energia.default_value = 3.0 + 2.0 * (0.5 + 0.5 * math.sin(2 * PI * fr * 4))
    em_energia.keyframe_insert('default_value', frame=q)
    em_cristal.keyframe_insert('default_value', frame=q)
    em_rack.default_value = 1.0 + 1.0 * (0.5 + 0.5 * math.sin(2 * PI * fr * 3 + 1.0))
    em_rack.keyframe_insert('default_value', frame=q)
    em_giro.default_value = (10.0 if int(t * 4) % 2 == 0 else 1.0) if cs > 0.01 else 0.6
    em_giro.keyframe_insert('default_value', frame=q)

# hastes da comporta: interpolação constante na visibilidade
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


ALVO = (0.0, 0.0, 0.85)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    for i, (ang, alt, tq) in enumerate(((300, 4.4, 2.6), (215, 4.2, 0.7), (120, 4.6, 0.7), (35, 4.0, 2.6))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt)), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, 'laboratorio_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    sc.frame_set(int(2.9 * FPS) + 1)                                      # braço pondo o pacote na gaveta
    mirar((1.25, -2.05, 1.55), (0.0, -0.55, 0.75), 30)
    sc.render.filepath = os.path.join(AQUI, 'laboratorio_perto.png')
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
    sc.render.filepath = os.path.join(AQUI, 'laboratorio_video.mp4')
    bpy.ops.render.render(animation=True)
print('LABORATORIO ok')
