"""Estudo isolado (fora do jogo): painel solar, 2×2 tiles, sem portas, até 1,08 m de altura.
Duas placas de células inclinadas para o sul, cada uma num tubo de torção apoiado em mancais sobre cavaletes de aço
enferrujado. Seguidor solar: um pistão hidráulico por placa (camisa presa num olhal na laje, haste num olhal sob a
placa) inclina a placa acompanhando o sol; mangueiras até a pequena unidade hidráulica (tanque, motor, bloco de
válvulas) no fundo. Por trás: caixas de junção, cabos em eletrocalha sob a placa, saída coaxial pela ponta do tubo de
torção (não torce com o giro), eletrocalha no chão até o inversor (aletas, LEDs) e eletroduto até a borda norte.
Robô limpador corre em trilhos nas bordas da placa com escova girando. Fenômeno da IA: bastões-guia de luz na borda
interna das placas mandam feixes violeta até um cristal acumulador preso por garras e bobina de cobre; três lentes
flutuam em órbita sobre ele concentrando o sol em feixes âmbar. Sujeira: pó no vidro (mais embaixo e nos cantos),
folhas e lama presas na borda baixa onde a escova não alcança, respingos de lama na linha de gotejamento, ferrugem
nos cavaletes, óleo sob a unidade hidráulica.
Uso: blender -b --python estudo_painel_solar.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(23)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=48, nr=12, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def folha(bm, centro, L, ang, curva=0.004):
    """Folha seca: contorno pontudo, nervura levemente curvada."""
    vs = []
    n = 10
    for i in range(n):
        t = i * 2 * PI / n
        x = 0.5 * L * math.cos(t)
        y = 0.22 * L * math.sin(t) * (abs(math.cos(t)) ** 0.15 if i % (n // 2) else 1)
        z = curva * (1 - (2 * x / L) ** 2) + random.uniform(-0.001, 0.001)
        p = Matrix.Rotation(ang, 3, 'Z') @ Vector((x, y, z))
        vs.append(bm.verts.new(Vector(centro) + p))
    bm.faces.new(vs)


def ferrugento(m, de=0.42):
    """Ferrugem cobre mais área (baixa o limiar do ruído grande)."""
    for n in m.node_tree.nodes:
        if n.type == 'MAP_RANGE' and abs(n.inputs['From Min'].default_value - 0.55) < 1e-4:
            n.inputs['From Min'].default_value = de
            n.inputs['From Max'].default_value = de + 0.1
    return m


def mancha_el(bm, c, rx, ry, z):
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=1.0)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.25 * math.sin(a * 3 + random.random()) + 0.1 * random.random()
        v.co = Vector((c[0] + v.co.x * rx * f, c[1] + v.co.y * ry * f, z))


# ------------------------------------------------------------------ materiais
CEL = 0.105                 # lado da célula
NX, NY = 6, 11
CX2, CY2 = NX * CEL / 2, NY * CEL / 2          # meia-largura e meio-comprimento da área de células


def celula_mat():
    """Células azul-escuras em grade, fundo claro entre elas, filetes de prata, vidro com verniz; pó acumula
    embaixo (y local baixo) e nos cantos da moldura."""
    no = mats.no
    m = bpy.data.materials.new('Células')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = no(nt, 'ShaderNodeTexCoord')
    desl = no(nt, 'ShaderNodeVectorMath', operation='ADD')
    desl.inputs[1].default_value = (CX2, CY2, 0)
    nt.links.new(tc.outputs['Object'], desl.inputs[0])
    tj = no(nt, 'ShaderNodeTexBrick', **{'Scale': 1.0, 'Mortar Size': 0.004, 'Brick Width': CEL, 'Row Height': CEL,
                                         'Mortar Smooth': 0.0, 'Bias': 0.0})
    tj.offset = 0.0
    tj.inputs['Color1'].default_value = (0.012, 0.022, 0.06, 1)
    tj.inputs['Color2'].default_value = (0.016, 0.028, 0.072, 1)
    tj.inputs['Mortar'].default_value = (0.5, 0.52, 0.55, 1)
    nt.links.new(desl.outputs[0], tj.inputs['Vector'])
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(desl.outputs[0], sep.inputs[0])
    fx = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    fx.inputs[1].default_value = 3.0 / CEL
    nt.links.new(sep.outputs['X'], fx.inputs[0])
    fr = no(nt, 'ShaderNodeMath', operation='FRACT')
    nt.links.new(fx.outputs['Value'], fr.inputs[0])
    bus = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
    bus.inputs[1].default_value = 0.045
    nt.links.new(fr.outputs['Value'], bus.inputs[0])
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c1.inputs[7].default_value = (0.42, 0.43, 0.45, 1)
    nt.links.new(bus.outputs['Value'], c1.inputs[0])
    nt.links.new(tj.outputs['Color'], c1.inputs[6])
    # pó: ruído × (mais embaixo) + bordas
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 32.0, 'Detail': 8.0, 'Roughness': 0.7})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    ruf = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.48, 'From Max': 0.8})
    nt.links.new(ru.outputs['Fac'], ruf.inputs['Value'])
    sy = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sy.inputs[0])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': -CY2, 'From Max': 0.25, 'To Min': 0.75, 'To Max': 0.08})
    nt.links.new(sy.outputs['Y'], baixo.inputs['Value'])
    p1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(ruf.outputs['Result'], p1.inputs[0])
    nt.links.new(baixo.outputs['Result'], p1.inputs[1])
    ax = no(nt, 'ShaderNodeMath', operation='ABSOLUTE')
    nt.links.new(sy.outputs['X'], ax.inputs[0])
    ay = no(nt, 'ShaderNodeMath', operation='ABSOLUTE')
    nt.links.new(sy.outputs['Y'], ay.inputs[0])
    bx = no(nt, 'ShaderNodeMapRange', **{'From Min': CX2 - 0.035, 'From Max': CX2, 'To Min': 0.0, 'To Max': 0.7})
    nt.links.new(ax.outputs['Value'], bx.inputs['Value'])
    by = no(nt, 'ShaderNodeMapRange', **{'From Min': CY2 - 0.035, 'From Max': CY2, 'To Min': 0.0, 'To Max': 0.7})
    nt.links.new(ay.outputs['Value'], by.inputs['Value'])
    bm_ = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(bx.outputs['Result'], bm_.inputs[0])
    nt.links.new(by.outputs['Result'], bm_.inputs[1])
    po = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(p1.outputs['Value'], po.inputs[0])
    nt.links.new(bm_.outputs['Value'], po.inputs[1])
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c2.inputs[7].default_value = (0.36, 0.30, 0.22, 1)
    nt.links.new(po.outputs['Value'], c2.inputs[0])
    nt.links.new(c1.outputs[2], c2.inputs[6])
    nt.links.new(c2.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.22, 'To Max': 0.85})
    nt.links.new(po.outputs['Value'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    cw = no(nt, 'ShaderNodeMapRange', **{'To Min': 1.0, 'To Max': 0.1})
    nt.links.new(po.outputs['Value'], cw.inputs['Value'])
    nt.links.new(cw.outputs['Result'], b.inputs['Coat Weight'])
    b.inputs['Coat Roughness'].default_value = 0.03
    b.inputs['Metallic'].default_value = 0.25
    return m


def brilho_mat(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat(nome, forca):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.26, 0.05, 0.55, 1)
    b.inputs['Roughness'].default_value = 0.14
    b.inputs['IOR'].default_value = 1.55
    b.inputs['Transmission Weight'].default_value = 0.85
    b.inputs['Emission Color'].default_value = (0.45, 0.1, 1.0, 1)
    b.inputs['Emission Strength'].default_value = forca
    ru = mats.no(nt, 'ShaderNodeTexNoise', **{'Scale': 30.0, 'Detail': 6.0})
    bump = mats.no(nt, 'ShaderNodeBump', **{'Strength': 0.25})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def vidro_mat(nome, cor, rough=0.02, emis=0.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['IOR'].default_value = 1.5
    b.inputs['Transmission Weight'].default_value = 1.0
    if emis:
        b.inputs['Emission Color'].default_value = (*cor, 1)
        b.inputs['Emission Strength'].default_value = emis
    return m


def feixe_mat(nome, cor, forca):
    """Feixe de luz visível: brilho aditivo que some nas laterais (parece raio, não bastão)."""
    no = mats.no
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*cor, 1)
    lw = no(nt, 'ShaderNodeLayerWeight', **{'Blend': 0.5})
    f = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    f.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs['Facing'], f.inputs[1])
    pw = no(nt, 'ShaderNodeMath', operation='POWER')
    pw.inputs[1].default_value = 2.5
    nt.links.new(f.outputs['Value'], pw.inputs[0])
    k = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    k.inputs[1].default_value = forca
    nt.links.new(pw.outputs['Value'], k.inputs[0])
    nt.links.new(k.outputs['Value'], em.inputs['Strength'])
    ad = no(nt, 'ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs['Surface'])
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.8),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.6, sujeira=0.8, escovado=True),
    'cavalete': ferrugento(mats.material('Cavalete', (0.30, 0.30, 0.29), 1.0, 0.6, pintura=False, ferrugem=1.0,
                                         sujeira=1.0)),
    'aluminio': mats.material('Alumínio', (0.52, 0.53, 0.54), 1.0, 0.33, pintura=False, sujeira=0.95, desgaste=0.2),
    'fundo': mats.material('Fundo da placa', (0.50, 0.50, 0.47), 0, 0.7, sujeira=0.9, desgaste=0.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'cerdas': mats.material('Cerdas', (0.05, 0.045, 0.04), 0, 0.85, pintura=False, sujeira=0.8, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.19, 0.15, 0.105), 0, 0.85, pintura=False, sujeira=0.3, desgaste=0.0),
    'ferrugem': mats.material('Escorrido de ferrugem', (0.26, 0.10, 0.035), 0, 0.8, pintura=False, sujeira=0.2,
                              desgaste=0.0),
    'folha': mats.material('Folha seca', (0.28, 0.14, 0.04), 0, 0.7, pintura=False, sujeira=0.6, desgaste=0.0),
    'folha2': mats.material('Folha velha', (0.16, 0.10, 0.045), 0, 0.75, pintura=False, sujeira=0.6, desgaste=0.0),
    'celula': celula_mat(),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'led_verde': brilho_mat('LED verde', (0.15, 1.0, 0.25), 12.0),
    'led_ambar': brilho_mat('LED âmbar', (1.0, 0.5, 0.05), 10.0),
    'guia': vidro_mat('Guia de luz', (0.45, 0.2, 0.9), 0.08, 0.8),
    'lente': vidro_mat('Lente', (0.95, 0.9, 0.8), 0.01),
    'cristal': cristal_mat('Cristal', 1.0),
    'feixe_violeta': feixe_mat('Feixe violeta', (0.42, 0.1, 1.0), 6.0),
    'feixe_ambar': feixe_mat('Feixe âmbar', (1.0, 0.55, 0.15), 4.0),
})
M = base3d.M

# ------------------------------------------------------------------ medidas
XC = 0.53                   # centro das placas (±x)
Z_AX = 0.55                 # eixo de giro (centro do tubo de torção) — no plano local da placa é z = -0,035
Z_T = -0.035                # centro do tubo de torção no sistema local da placa
W2, L2 = CX2 + 0.03, CY2 + 0.03                 # meia-largura e meio-comprimento da moldura
Z_FB, Z_FT, Z_VID = 0.03, 0.085, 0.072         # moldura (base/topo) e topo do vidro, local
TH_MED, TH_AMP = math.radians(26), math.radians(8)
CRI = Vector((0.0, -0.15, 0.0))                # cristal acumulador (entre as placas)
Z_CRI0, Z_CRI1 = 0.21, 0.53                     # base e ponta do cristal
B_PIST = 0.50               # y do olhal do pistão na laje
LUG = Vector((0, 0.38, -0.065))                # olhal sob a placa (local)


def tilt(fr):
    return TH_MED + TH_AMP * math.sin(2 * PI * fr)


def local_para_mundo(s, p, th):
    return Vector((s * XC, 0, Z_AX)) + Matrix.Rotation(th, 3, 'X') @ (Vector(p) - Vector((0, 0, Z_T)))


# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-0.95, -0.95, 0), (0.95, 0.95, 0.06))
obj('laje', bm, 'concreto')
bm = bmesh.new()
for s in (-1, 1):                                                            # ladrilhos de perigo sob os pistões
    caixa_de(bm, (s * XC - 0.09, B_PIST - 0.08, 0.06), (s * XC + 0.09, B_PIST + 0.08, 0.063))
caixa_de(bm, (-0.2, 0.66, 0.06), (0.2, 0.68, 0.063))                         # faixa diante da unidade hidráulica
obj('ladrilho_listras', bm, 'listras')

# ------------------------------------------------------------------ placas (cada uma num pivô que gira em x)
pivos, robos, escovas, nos_guia = [], [], [], []
for s in (-1, 1):                         # s = lado de fora (oeste −1, leste +1)
    pv = bpy.data.objects.new('pivo_placa', None)
    sc.collection.objects.link(pv)
    pv.location = (s * XC, 0, Z_AX)
    pv.rotation_mode = 'XYZ'
    pivos.append(pv)

    def P(nome, bm, mat):
        o = obj(nome, bm, mat, pv)
        # malha feita em coordenadas locais com o eixo em z = Z_T: desloca para o eixo ficar na origem do pivô
        o.location = (0, 0, -Z_T)
        return o

    # células e fundo
    bm = bmesh.new()
    caixa_de(bm, (-CX2, -CY2, 0.036), (CX2, CY2, Z_VID))
    P('celulas', bm, 'celula')
    bm = bmesh.new()
    caixa_de(bm, (-W2 + 0.005, -L2 + 0.005, Z_FB), (W2 - 0.005, L2 - 0.005, 0.036))
    P('fundo', bm, 'fundo')
    # moldura (quatro perfis com lábio sobre o vidro)
    bm = bmesh.new()
    for sy in (-1, 1):
        caixa_de(bm, (-W2, sy * CY2, Z_FB), (W2, sy * L2, Z_FT))
        caixa_de(bm, (-CX2, sy * (CY2 - 0.006), Z_VID), (CX2, sy * CY2, Z_FT))
    for sx in (-1, 1):
        caixa_de(bm, (sx * CX2, -CY2, Z_FB), (sx * W2, CY2, Z_FT))
        caixa_de(bm, (sx * (CX2 - 0.006), -CY2 + 0.006, Z_VID), (sx * CX2, CY2 - 0.006, Z_FT))
    P('moldura', bm, 'aluminio')
    # travessas sob a placa, tubo de torção, abraçadeiras
    bm = bmesh.new()
    for x in (-0.205, 0.0, 0.205):
        caixa_de(bm, (x - 0.015, -L2 + 0.03, Z_T + 0.03), (x + 0.015, L2 - 0.03, Z_FB))
    caixa_de(bm, (-0.035, LUG.y - 0.035, Z_T + 0.015), (0.035, LUG.y + 0.035, Z_T + 0.03))    # chapa do olhal
    for sx in (-1, 1):                                                                     # orelhas do olhal
        caixa_de(bm, (sx * 0.022, LUG.y - 0.025, LUG.z - 0.022), (sx * 0.031, LUG.y + 0.025, Z_T + 0.015))
    P('travessas', bm, 'aco')
    bm = bmesh.new()
    cil(bm, (s * 0.0275, 0, Z_T), 0.03, 0.715, Vector((1, 0, 0)), 20)                    # −s·0,33 … s·0,385
    cil(bm, (s * 0.388, 0, Z_T), 0.033, 0.008, Vector((1, 0, 0)), 20)                    # tampa da ponta
    cil(bm, (s * 0.397, 0, Z_T), 0.014, 0.014, Vector((1, 0, 0)), 12)                    # prensa-cabo coaxial
    cil(bm, (s * 0.355, 0.036, Z_T), 0.011, 0.016, Vector((0, 1, 0)), 12)                # prensa-cabo lateral
    cil(bm, (0, LUG.y, LUG.z), 0.007, 0.075, Vector((1, 0, 0)), 10)                      # pino do olhal
    suavizar(P('tubo_torcao', bm, 'aco'))
    bm = bmesh.new()
    for x in (-0.205, 0.0, 0.205):
        caixa_de(bm, (x - 0.02, -0.038, Z_T - 0.042), (x + 0.02, 0.038, Z_T - 0.03))
        for sy in (-1, 1):
            cil(bm, (x, sy * 0.036, Z_T - 0.006), 0.005, 0.072, lados=8)
    P('abracadeiras', bm, 'cavalete')
    # caixas de junção, cabos até a eletrocalha sob a placa, eletrocalha
    bm, bc = bmesh.new(), bmesh.new()
    YC = 0.14
    for x in (-0.1, 0.1):
        caixa_de(bm, (x - 0.04, 0.22, Z_FB - 0.026), (x + 0.04, 0.29, Z_FB))
        for dx in (-0.018, 0.018):
            cil(bm, (x + dx, 0.215, Z_FB - 0.014), 0.007, 0.012, Vector((0, 1, 0)), 8)
            pts = bezier((x + dx, 0.21, Z_FB - 0.014), (x + dx, 0.17, Z_FB - 0.014), (x + dx * 0.4, YC + 0.01, -0.02),
                         (x + dx * 0.4, YC, Z_T - 0.012), 6)
            mangueira(bc, pts, 0.0055)
    obj_cx = P('caixas_juncao', bm, 'grafite')
    bm = bmesh.new()
    xi, xo = -s * 0.30, s * 0.36
    x0, x1 = min(xi, xo), max(xi, xo)
    caixa_de(bm, (x0, YC - 0.03, Z_T - 0.025), (x1, YC + 0.03, Z_T - 0.021))                # fundo
    for sy in (-1, 1):
        caixa_de(bm, (x0, YC + sy * 0.03, Z_T - 0.025), (x1, YC + sy * 0.026, Z_T + 0.008))  # abas (penduradas)
    for x in (-0.205, 0.0, 0.205):                                                         # tirantes
        for sy in (-1, 1):
            caixa_de(bm, (x - 0.004, YC + sy * 0.03, Z_T + 0.008), (x + 0.004, YC + sy * 0.034, Z_T + 0.03))
    P('eletrocalha_placa', bm, 'aco')
    for k in range(3):                                                                     # feixe dentro da calha
        tubo(bc, (x0 + 0.01, YC - 0.012 + k * 0.012, Z_T - 0.014), (x1 - 0.01, YC - 0.012 + k * 0.012, Z_T - 0.014),
             0.0055, 8)
    pts = bezier((xo - s * 0.005, YC, Z_T - 0.014), (xo, YC - 0.02, Z_T - 0.014), (s * 0.355, 0.075, Z_T),
                 (s * 0.355, 0.044, Z_T), 6)
    mangueira(bc, pts, 0.008)
    suavizar(P('cabos_placa', bc, 'borracha'))
    # trilhos do robô nas bordas norte e sul
    bm = bmesh.new()
    for sy in (-1, 1):
        caixa_de(bm, (-0.37, sy * 0.617, 0.072), (0.37, sy * 0.633, 0.09))
        for x in (-0.3, 0.0, 0.3):
            caixa_de(bm, (x - 0.012, sy * L2, 0.05), (x + 0.012, sy * 0.617, 0.085))
        for x in (-0.37, 0.37):                                                            # batentes
            caixa_de(bm, (x - 0.006, sy * 0.612, 0.072), (x + 0.006, sy * 0.638, 0.105))
    P('trilhos', bm, 'aco')
    # guia de luz na borda interna (fenômeno): bastão de vidro violeta, presilhas e nó de acoplamento
    bm = bmesh.new()
    xg = -s * 0.362
    cil(bm, (xg, 0, 0.06), 0.011, 2 * (CY2 - 0.02), Vector((0, 1, 0)), 12)
    P('guia_luz', bm, 'guia')
    bm = bmesh.new()
    for y in (-0.45, 0.1, 0.45):
        caixa_de(bm, (-s * W2, y - 0.01, 0.045), (xg + s * 0.002, y + 0.01, 0.075))
        toro(bm, (xg, y, 0.06), 0.013, 0.0035, 16, 6, Matrix.Rotation(PI / 2, 3, 'X'))
    P('presilhas_guia', bm, 'aco')
    bm = bmesh.new()
    cil(bm, (xg, -0.15, 0.06), 0.022, 0.04, Vector((0, 1, 0)), 6)
    no_g = P('no_guia', bm, 'cobre')
    nos_guia.append((pv, Vector((xg, -0.15, 0.06))))
    # sujeira presa na borda baixa (onde a escova não alcança): folhas e lama
    bm, bl = bmesh.new(), bmesh.new()
    for k in range(9):
        x = random.choice((-1, 1)) * random.uniform(0.12, 0.33) if k < 7 else random.uniform(-0.3, 0.3)
        folha(bm if k % 2 else bl, (x, -CY2 + 0.004, Z_FT + 0.0015 + 0.0008 * k), random.uniform(0.03, 0.05),
              random.uniform(-0.6, 0.6) + (PI / 2 if k % 3 == 0 else 0))
    P('folhas_placa', bm, 'folha')
    P('folhas_placa2', bl, 'folha2')
    bm = bmesh.new()
    for k in range(6):
        x = random.uniform(-CX2 + 0.03, CX2 - 0.03)
        caixa(bm, (x, -CY2 - 0.004, Z_FT + 0.001), (random.uniform(0.04, 0.12), 0.022, 0.003))
    for sx in (-1, 1):                                                                     # canto baixo enlameado
        caixa(bm, (sx * (CX2 - 0.03), -CY2 + 0.025, Z_VID + 0.0012), (0.05, 0.04, 0.0025))
    P('lama_placa', bm, 'lama')

    # robô limpador (corre em x local nos trilhos, escova em y local)
    rb = bpy.data.objects.new('robo', None)
    sc.collection.objects.link(rb)
    rb.parent = pv
    robos.append(rb)

    def R(nome, bm, mat, pai=rb):
        o = obj(nome, bm, mat, pai)
        return o
    bm, bw, bl2, bs = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for sy in (-1, 1):
        caixa_de(bm, (-0.045, sy * 0.605, 0.128 - Z_T), (0.045, sy * 0.648, 0.16 - Z_T))           # carro
        caixa_de(bm, (-0.045, sy * 0.645, 0.095 - Z_T), (0.045, sy * 0.652, 0.16 - Z_T))            # chapa lateral
        for x in (-0.03, 0.03):
            cil(bw, (x, sy * 0.625, 0.108 - Z_T), 0.018, 0.014, Vector((0, 1, 0)), 16)              # rodas no trilho
            cil(bw, (x, sy * 0.638, 0.108 - Z_T), 0.005, 0.018, Vector((0, 1, 0)), 8)               # eixo
        caixa_de(bs, (-0.046, sy * 0.648, 0.13 - Z_T), (0.046, sy * 0.652, 0.158 - Z_T))           # listras no carro
        caixa_de(bm, (-0.012, sy * 0.57, 0.098 - Z_T), (0.012, sy * 0.58, 0.15 - Z_T))              # mancal da escova
    caixa_de(bm, (-0.03, -0.62, 0.15 - Z_T), (0.03, 0.62, 0.172 - Z_T))                             # viga
    caixa_de(bm, (-0.035, -0.12, 0.172 - Z_T), (0.035, 0.12, 0.192 - Z_T))                          # bateria
    for k in range(5):                                                                               # nervuras da viga
        caixa_de(bm, (-0.031, -0.5 + k * 0.25 - 0.004, 0.15 - Z_T), (0.031, -0.5 + k * 0.25 + 0.004, 0.174 - Z_T))
    R('robo_corpo', bm, 'amarelo')
    cil(bw, (0, -0.675, 0.13 - Z_T), 0.025, 0.05, Vector((0, 1, 0)), 16)                            # motor
    for k in range(4):
        cil(bw, (0, -0.66 - k * 0.01, 0.13 - Z_T), 0.028, 0.003, Vector((0, 1, 0)), 16)            # aletas
    suavizar(R('robo_rodas_motor', bw, 'grafite'))
    R('robo_listras', bs, 'listras')
    bm = bmesh.new()
    cil(bm, (0, -0.64, 0.17 - Z_T), 0.008, 0.016, lados=10)
    o_lamp = R('robo_lampada', bm, 'lampada')
    bm = bmesh.new()                                                                                 # cabo motor→bateria
    mangueira(bm, bezier((0, -0.66, 0.15 - Z_T), (0, -0.66, 0.185 - Z_T), (0, -0.2, 0.19 - Z_T), (0, -0.12, 0.183 - Z_T), 6),
              0.004)
    suavizar(R('robo_cabo', bm, 'borracha'))
    # escova: núcleo + 8 fileiras de tufos (uma amarela para ver o giro)
    es = bpy.data.objects.new('escova_eixo', None)
    sc.collection.objects.link(es)
    es.parent = rb
    es.location = (0, 0, 0.105 - Z_T)
    es.rotation_mode = 'XYZ'
    escovas.append(es)
    bm, bt, ba = bmesh.new(), bmesh.new(), bmesh.new()
    cil(bm, (0, 0, 0), 0.006, 1.15, Vector((0, 1, 0)), 10)
    cil(bm, (0, 0, 0), 0.013, 1.1, Vector((0, 1, 0)), 16)
    for k in range(8):
        a = k * 2 * PI / 8
        d = Vector((math.cos(a), 0, math.sin(a)))
        for j in range(22):
            y = -0.54 + j * 0.0514
            c = d * 0.0205 + Vector((0, y, 0))
            caixa(ba if k == 0 else bt, c, (0.016, 0.028, 0.006), Matrix.Rotation(-a, 3, 'Y'))
    R('escova_nucleo', bm, 'grafite', es)
    R('escova_cerdas', bt, 'cerdas', es)
    R('escova_cerdas_marca', ba, 'amarelo', es)

# ------------------------------------------------------------------ cavaletes (aço enferrujado) e mancais
bm, bb, bf = bmesh.new(), bmesh.new(), bmesh.new()
ZTOP = Z_AX - 0.085
for s in (-1, 1):
    for xt in (s * XC - 0.29, s * XC + 0.29):
        top_y, foot_y = 0.035, 0.30
        for sy in (-1, 1):
            viga(bm, (xt, sy * foot_y, 0.07), (xt, sy * top_y, ZTOP - 0.01), 0.035)
            caixa_de(bf, (xt - 0.05, sy * foot_y - 0.05, 0.06), (xt + 0.05, sy * foot_y + 0.05, 0.072))   # sapata
            for dx in (-0.03, 0.03):
                cil(bf, (xt + dx, sy * foot_y + sy * 0.03, 0.078), 0.007, 0.012, lados=6)                # porcas
        zb = 0.24                                                                                          # travessa
        yb = foot_y + (top_y - foot_y) * (zb - 0.07) / (ZTOP - 0.08)
        caixa_de(bm, (xt - 0.012, -yb, zb - 0.015), (xt + 0.012, yb, zb + 0.015))
        viga(bm, (xt, -yb + 0.02, zb + 0.015), (xt, 0.05, ZTOP - 0.07), 0.02)                              # diagonal
        caixa_de(bm, (xt - 0.04, -0.065, ZTOP - 0.012), (xt + 0.04, 0.065, ZTOP))                          # sela
        cil(bb, (xt, 0, Z_AX), 0.05, 0.05, Vector((1, 0, 0)), 20)                                          # mancal
        caixa_de(bb, (xt - 0.025, -0.06, ZTOP), (xt + 0.025, 0.06, Z_AX - 0.02))                           # pé do mancal
        cil(bb, (xt, 0, Z_AX + 0.05), 0.008, 0.012, lados=8)                                              # graxeira
        for sy in (-1, 1):
            cil(bf, (xt, sy * 0.05, ZTOP + 0.012), 0.007, 0.012, lados=6)
obj('cavaletes', bm, 'cavalete')
suavizar(obj('mancais', bb, 'grafite'))
obj('sapatas', bf, 'cavalete')

# ------------------------------------------------------------------ pistões do seguidor solar
dists = []
for q in range(200):
    th = tilt(q / 200)
    lug = local_para_mundo(1, LUG, th)
    dists.append((lug - Vector((XC, B_PIST, 0.10))).length)
DMIN, DMAX = min(dists), max(dists)
LC = DMIN - 0.05                     # camisa
LH = DMIN - 0.06                     # haste
assert LC + LH > DMAX + 0.05, (LC, LH, DMAX)
print('PISTÃO curso %.3f–%.3f  camisa %.3f  haste %.3f' % (DMIN, DMAX, LC, LH))
camisas, hastes, portas = [], [], []
d_med = (local_para_mundo(1, LUG, TH_MED) - Vector((XC, B_PIST, 0.10))).normalized()
q_med = d_med.to_track_quat('Z', 'Y')
for s in (-1, 1):
    B = Vector((s * XC, B_PIST, 0.10))
    bm = bmesh.new()                                                         # olhal na laje
    caixa_de(bm, (B.x - 0.06, B.y - 0.05, 0.063), (B.x + 0.06, B.y + 0.05, 0.075))
    for sx in (-1, 1):
        caixa_de(bm, (B.x + sx * 0.022, B.y - 0.03, 0.075), (B.x + sx * 0.031, B.y + 0.03, 0.125))
    cil(bm, B, 0.007, 0.075, Vector((1, 0, 0)), 10)
    for dx in (-0.045, 0.045):
        for dy in (-0.035, 0.035):
            cil(bm, (B.x + dx, B.y + dy, 0.08), 0.006, 0.01, lados=6)
    obj('olhal_base', bm, 'aco')
    bm, ba, bl = bmesh.new(), bmesh.new(), bmesh.new()
    cil(bm, (0, 0, 0), 0.02, 0.04, Vector((1, 0, 0)), 16)                    # olho da camisa
    cil(ba, (0, 0, (0.025 + LC) / 2), 0.032, LC - 0.025, lados=20)          # camisa
    cil(bm, (0, 0, 0.032), 0.036, 0.016, lados=20)                           # tampa de fundo
    cil(bm, (0, 0, LC - 0.008), 0.036, 0.016, lados=20)                      # cabeçote
    cil(bm, (0, 0.04, 0.07), 0.009, 0.02, Vector((0, 1, 0)), 10)            # porta do fundo
    cil(bm, (0, 0.04, LC - 0.03), 0.009, 0.02, Vector((0, 1, 0)), 10)       # porta da haste
    mangueira(bl, [Vector((0, 0.05, LC - 0.03)), Vector((0, 0.05, 0.1))], 0.005)   # linha rígida até perto do fundo
    cil(bl, (0, 0.06, 0.1), 0.007, 0.03, Vector((0, 1, 0)), 10)
    cmz = obj('camisa_pecas', bm, 'aco')
    cm = obj('camisa', ba, 'amarelo')
    cl = obj('camisa_linha', bl, 'aco')
    for o in (cmz, cl):
        o.parent = cm
    suavizar(cm); suavizar(cmz); suavizar(cl)
    cm.rotation_mode = 'QUATERNION'
    camisas.append((cm, B))
    bm = bmesh.new()
    cil(bm, (0, 0, 0), 0.018, 0.04, Vector((1, 0, 0)), 16)                   # olho da haste
    cil(bm, (0, 0, (0.018 + LH) / 2), 0.016, LH - 0.018, lados=16)
    hs = suavizar(obj('haste', bm, 'cromo'))
    hs.rotation_mode = 'QUATERNION'
    hastes.append((hs, s))
    # portas no mundo (posição média) para as mangueiras
    portas.append([B + q_med @ Vector((0, 0.075, 0.1)), B + q_med @ Vector((0, 0.05, 0.07))])

# ------------------------------------------------------------------ unidade hidráulica (norte, centro)
bm, bg, ba, bc = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
caixa_de(bg, (-0.19, 0.71, 0.06), (0.19, 0.93, 0.10))                          # skid
for x in (-0.16, 0.16):
    caixa_de(bg, (x - 0.02, 0.69, 0.06), (x + 0.02, 0.95, 0.075))
caixa_de(bm, (-0.165, 0.73, 0.10), (0.165, 0.91, 0.26))                         # tanque
cil(bm, (0.11, 0.87, 0.275), 0.022, 0.03, lados=12)                             # respiro
cil(bg, (0.11, 0.87, 0.30), 0.026, 0.02, lados=12)
cil(bg, (0.065, 0.83, 0.36), 0.056, 0.2, lados=24)                              # motor vertical
for k in range(9):
    cil(bg, (0.065, 0.83, 0.28 + k * 0.018), 0.062, 0.006, lados=24)            # aletas
cil(bm, (0.065, 0.83, 0.475), 0.06, 0.03, lados=24)                             # tampa do ventilador
caixa_de(bg, (0.12, 0.80, 0.37), (0.16, 0.86, 0.43))                            # caixa de ligação
caixa_de(ba, (-0.15, 0.70, 0.26), (0.0, 0.77, 0.31))                            # bloco de válvulas
for x in (-0.11, -0.04):
    cil(ba, (x, 0.735, 0.34), 0.017, 0.06, lados=12)                           # solenoides
    caixa_de(bg, (x - 0.022, 0.712, 0.355), (x + 0.022, 0.758, 0.395))          # bobina
cil(ba, (-0.135, 0.85, 0.30), 0.03, 0.08, lados=16)                             # filtro
mangueira(ba, [Vector((-0.135, 0.85, 0.26)), Vector((-0.135, 0.85, 0.262))], 0.01)
caixa_de(ba, (-0.03, 0.71, 0.31), (-0.005, 0.735, 0.33))                       # transdutor de pressão
PORTAS_HPU = []
for k, x in enumerate((-0.135, -0.105, -0.045, -0.015)):
    cil(ba, (x, 0.69, 0.285), 0.009, 0.02, Vector((0, 1, 0)), 10)
    PORTAS_HPU.append(Vector((x, 0.68, 0.285)))
obj('hpu_tanque', bm, 'amarelo')
suavizar(obj('hpu_motor', bg, 'grafite'))
suavizar(obj('hpu_valvulas', ba, 'aco'))
bm = bmesh.new()
cil(bm, (-0.0175, 0.71, 0.322), 0.005, 0.006, Vector((0, 1, 0)), 8)
o_led_hpu = obj('hpu_led', bm, 'led_verde')
bm = bmesh.new()
caixa_de(bm, (-0.165, 0.729, 0.235), (0.165, 0.7305, 0.258))
obj('hpu_listras', bm, 'listras')
# mangueiras HPU → pistões (duas por pistão), com terminais prensados
bm, bt = bmesh.new(), bmesh.new()
for k, (ph, pp) in enumerate(zip(PORTAS_HPU, [portas[0][0], portas[0][1], portas[1][1], portas[1][0]])):
    s = -1 if k < 2 else 1
    a, b = ph, pp + Vector((0, 0.018, 0))
    pts = bezier(a, a + Vector((0, -0.10, 0.02 + 0.02 * k)), b + Vector((-s * 0.06, 0.14, 0.06)), b, 18)
    mangueira(bm, pts, 0.0095)
    for p, u in ((a, Vector((0, -1, 0))), (b, (pts[-2] - pts[-1]).normalized())):
        cil(bt, p + u * 0.012, 0.012, 0.022, u, 10)
suavizar(obj('mangueiras', bm, 'borracha'))
suavizar(obj('terminais', bt, 'aco'))

# ------------------------------------------------------------------ inversor (norte, leste) e eletroduto até a borda
bm, bk, bl = bmesh.new(), bmesh.new(), bmesh.new()
caixa_de(bk, (0.45, 0.73, 0.06), (0.79, 0.91, 0.10))                            # base
caixa_de(bm, (0.46, 0.74, 0.10), (0.78, 0.90, 0.47))                            # gabinete
caixa_de(bm, (0.455, 0.735, 0.465), (0.785, 0.905, 0.48))                       # tampa com aba
for k in range(9):                                                              # dissipador (aletas, leste)
    z = 0.14 + k * 0.035
    caixa_de(bk, (0.78, 0.75, z - 0.006), (0.83, 0.89, z + 0.006))
cil(bk, (0.53, 0.738, 0.30), 0.055, 0.006, Vector((0, 1, 0)), 24)               # ventoinha (grade)
for k in range(4):
    caixa_de(bk, (0.48, 0.733, 0.27 + k * 0.02), (0.58, 0.736, 0.276 + k * 0.02))
for x in (0.52, 0.58, 0.64, 0.70):                                              # prensa-cabos embaixo
    cil(bk, (x, 0.73, 0.13), 0.012, 0.022, Vector((0, 1, 0)), 12)
cil(bk, (0.62, 0.91, 0.20), 0.016, 0.03, Vector((0, 1, 0)), 12)                 # saída norte
obj('inversor', bm, 'grafite')
suavizar(obj('inversor_pecas', bk, 'aco'))
LEDS_V, LEDS_A = bmesh.new(), bmesh.new()
for k in range(4):
    cil(LEDS_V if k < 3 else LEDS_A, (0.64 + k * 0.03, 0.738, 0.42), 0.007, 0.006, Vector((0, 1, 0)), 10)
o_ledv = obj('inversor_leds', LEDS_V, 'led_verde')
obj('inversor_led_ambar', LEDS_A, 'led_ambar')
bm = bmesh.new()
caixa_de(bm, (0.62, 0.738, 0.44), (0.76, 0.7385, 0.46))
obj('inversor_listras', bm, 'listras')
bm = bmesh.new()                                                                # eletroduto até a borda norte
pts = bezier((0.62, 0.925, 0.20), (0.62, 0.94, 0.20), (0.62, 0.935, 0.09), (0.66, 0.935, 0.09), 8)
pts += bezier((0.66, 0.935, 0.09), (0.75, 0.935, 0.09), (0.80, 0.935, 0.09), (0.86, 0.935, 0.09), 3)[1:]
mangueira(bm, pts, 0.014)
suavizar(obj('eletroduto', bm, 'cavalete'))
bm = bmesh.new()
caixa_de(bm, (0.86, 0.905, 0.06), (0.95, 0.95, 0.15))                           # caixa de conexão na borda
cil(bm, (0.95, 0.927, 0.105), 0.022, 0.012, Vector((1, 0, 0)), 16)              # tomada na face da borda
obj('caixa_borda', bm, 'grafite')
bm = bmesh.new()
for x in (0.70, 0.80):                                                          # abraçadeiras do eletroduto
    toro(bm, (x, 0.935, 0.09), 0.017, 0.0035, 16, 6, Matrix.Rotation(PI / 2, 3, 'Y'))
    caixa_de(bm, (x - 0.006, 0.915, 0.06), (x + 0.006, 0.955 - 0.005, 0.072))
obj('abracadeiras_eletroduto', bm, 'aco')

# ------------------------------------------------------------------ eletrocalha no chão e cabos
bm = bmesh.new()
TR = 0.035                     # meia-largura
def calha(a, b):
    a, b = Vector(a), Vector(b)
    caixa_de(bm, (min(a.x, b.x) - TR, min(a.y, b.y) - TR, 0.06), (max(a.x, b.x) + TR, max(a.y, b.y) + TR, 0.066))
    if abs(a.x - b.x) > abs(a.y - b.y):
        for sy in (-1, 1):
            caixa_de(bm, (min(a.x, b.x) - TR, a.y + sy * TR - 0.002, 0.06), (max(a.x, b.x) + TR, a.y + sy * TR + 0.002, 0.11))
    else:
        for sx in (-1, 1):
            caixa_de(bm, (a.x + sx * TR - 0.002, min(a.y, b.y) - TR, 0.06), (a.x + sx * TR + 0.002, max(a.y, b.y) + TR, 0.11))
calha((-0.91, 0.62), (0.45, 0.62))
calha((0.84, 0.62), (0.91, 0.62))
for s in (-1, 1):
    calha((s * 0.91, -0.06), (s * 0.91, 0.585))
calha((0.02, 0.005), (0.02, 0.585))
obj('eletrocalha_chao', bm, 'aco')
bc = bmesh.new()
for s in (-1, 1):                                                               # saída coaxial do tubo de torção
    p0 = Vector((s * (XC + 0.404), 0, Z_AX))
    pts = bezier(p0, p0 + Vector((s * 0.03, 0, -0.02)), Vector((s * 0.915, 0.0, 0.3)), Vector((s * 0.912, 0.0, 0.08)), 10)
    mangueira(bc, pts, 0.011)
    pts = bezier((s * 0.912, 0.0, 0.08), (s * 0.912, 0.4, 0.078), (s * 0.912, 0.6, 0.078), (s * 0.85, 0.62, 0.078), 10)
    mangueira(bc, pts, 0.011)
pts = [Vector(p) for p in ((-0.85, 0.625, 0.078), (0.48, 0.625, 0.078))]
mangueira(bc, pts, 0.011)
mangueira(bc, [Vector((-0.85, 0.608, 0.078)), Vector((0.5, 0.608, 0.078))], 0.011)
for k, x in enumerate((0.52, 0.58, 0.64)):                                      # sobem da calha para o inversor
    y0 = 0.625 if k == 0 else (0.608 if k == 1 else 0.64)
    pts = bezier((x - 0.04, y0, 0.078), (x, y0, 0.078), (x, 0.69, 0.13), (x, 0.715, 0.13), 8)
    mangueira(bc, pts, 0.010)
mangueira(bc, [Vector((0.86, 0.62, 0.078)), Vector((0.80, 0.62, 0.078))], 0.011)
pts = bezier((0.80, 0.62, 0.078), (0.72, 0.62, 0.078), (0.70, 0.68, 0.13), (0.70, 0.715, 0.13), 8)
mangueira(bc, pts, 0.010)
mangueira(bc, [Vector((0.02, -0.035, 0.08)), Vector((0.02, 0.64, 0.075))], 0.012)  # cristal → calha
pts = bezier((0.02, 0.64, 0.075), (0.02, 0.66, 0.075), (0.48, 0.64, 0.078), (0.56, 0.64, 0.078), 10)
mangueira(bc, pts, 0.010)
pts = bezier((0.12, 0.62, 0.09), (0.16, 0.66, 0.2), (0.14, 0.78, 0.4), (0.14, 0.81, 0.40), 10)  # alimenta o motor
mangueira(bc, pts, 0.008)
suavizar(obj('cabos_chao', bc, 'borracha'))

# ------------------------------------------------------------------ cristal acumulador, garras, bobina e lentes
bm, bg, bc = bmesh.new(), bmesh.new(), bmesh.new()
cil(bg, CRI + Vector((0, 0, 0.085)), 0.12, 0.05, lados=24)                      # base
cil(bg, (0.02, -0.04, 0.085), 0.017, 0.02, Vector((0, 1, 0)), 12)               # prensa-cabo da base
for k in range(6):
    a = k * PI / 3
    cil(bg, CRI + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.113)), 0.008, 0.008, lados=6)
cil(bm, CRI + Vector((0, 0, 0.15)), 0.05, 0.08, lados=16)                       # coluna
cil(bm, CRI + Vector((0, 0, 0.198)), 0.062, 0.016, lados=6)                     # colar
for k in range(3):
    a = k * 2 * PI / 3 + PI / 6                                                 # nas faces do hexágono
    d = Vector((math.cos(a), math.sin(a), 0))
    p0 = CRI + d * 0.05 + Vector((0, 0, 0.19))
    p1 = CRI + d * 0.092 + Vector((0, 0, 0.24))
    p2 = CRI + d * 0.092 + Vector((0, 0, 0.452))
    viga(bm, p0, p1, 0.018)
    viga(bm, p1, p2, 0.018)
    caixa(bm, CRI + d * 0.07 + Vector((0, 0, 0.32)), (0.042, 0.022, 0.03), Matrix.Rotation(a, 3, 'Z'))   # sapata
toro(bc, CRI + Vector((0, 0, 0.462)), 0.092, 0.013, 40, 10)                     # bobina de cobre
for k in range(14):                                                             # espiras aparentes
    a = k * 2 * PI / 14
    toro(bc, CRI + Vector((math.cos(a) * 0.092, math.sin(a) * 0.092, 0.462)), 0.0145, 0.0028, 12, 5,
         Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(PI / 2, 3, 'X'))
obj('berco_base', bg, 'grafite')
obj('berco_garras', bm, 'amarelo')
suavizar(obj('bobina', bc, 'cobre'))
bm = bmesh.new()
cil(bm, CRI + Vector((0, 0, (Z_CRI0 + 0.45) / 2)), 0.055, 0.45 - Z_CRI0, lados=6)
cil(bm, CRI + Vector((0, 0, 0.45 + (Z_CRI1 - 0.45) / 2)), 0.055, Z_CRI1 - 0.45, lados=6, r2=0.004)
for k in range(3):                                                              # cristais menores
    a = k * 2 * PI / 3
    p = CRI + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.30))
    cil(bm, p + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.06)), 0.016, 0.12,
        Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1)), 6, r2=0.003)
obj('cristal', bm, 'cristal')
luz_c = bpy.data.lights.new('Brilho do cristal', 'POINT')
luz_c.color = (0.6, 0.3, 1.0)
luz_c.shadow_soft_size = 0.05
lco = bpy.data.objects.new('Brilho do cristal', luz_c)
sc.collection.objects.link(lco)
lco.location = CRI + Vector((0, -0.09, 0.36))
lentes = []
for k in range(3):
    bm, br = bmesh.new(), bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=12, radius=0.05)
    for v in bm.verts:
        v.co.z *= 0.2
    toro(br, (0, 0, 0), 0.051, 0.0055, 40, 8)
    for j in range(3):                                                          # pinos do anel
        a = j * 2 * PI / 3
        cil(br, (math.cos(a) * 0.058, math.sin(a) * 0.058, 0), 0.004, 0.02, lados=6)
    lo = obj('lente', bm, 'lente')
    for pg in lo.data.polygons:
        pg.use_smooth = True
    ro = suavizar(obj('lente_anel', br, 'cobre', lo))
    lo.rotation_mode = 'QUATERNION'
    lentes.append(lo)

# feixes (cilindro unitário 0..1 em z, apontado e esticado por quadro)
def feixe(mat, r):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=r, radius2=r * 0.7, depth=1.0,
                          matrix=Matrix.Translation((0, 0, 0.5)))
    o = obj('feixe', bm, mat)
    for pg in o.data.polygons:
        pg.use_smooth = True
    o.rotation_mode = 'QUATERNION'
    o.visible_shadow = False
    return o
feixes_g = [feixe('feixe_violeta', 0.012) for _ in range(2)]
feixes_l = [feixe('feixe_ambar', 0.009) for _ in range(3)]

# ------------------------------------------------------------------ sujeira no chão: lama, folhas, óleo, ferrugem
bm = bmesh.new()
for s in (-1, 1):                                                               # respingos na linha de gotejamento
    for k in range(7):                                                          # faixa escorrida
        mancha_el(bm, (s * XC - 0.3 + k * 0.1 + random.uniform(-0.02, 0.02), random.gauss(-0.58, 0.015)),
                  random.uniform(0.05, 0.08), random.uniform(0.018, 0.03), 0.0602 + 0.00004 * k)
    for k in range(12):                                                         # respingos
        x = s * XC + random.uniform(-0.34, 0.34)
        mancha(bm, (x, random.gauss(-0.58, 0.05), 0), random.uniform(0.005, 0.011), 0.0606 + 0.00004 * k)
for (x, y) in ((-0.9, -0.9), (0.88, -0.9), (-0.9, 0.9)):
    for k in range(6):
        mancha(bm, (x + random.uniform(-0.04, 0.04), y + random.uniform(-0.04, 0.04), 0), random.uniform(0.01, 0.03),
               0.0612 + 0.00005 * k)
obj('lama_chao', bm, 'lama')
bm = bmesh.new()
for k in range(5):
    pedra(bm, (random.uniform(-0.85, 0.85), random.uniform(-0.92, -0.8), 0.068), random.uniform(0.008, 0.015), 0.5)
obj('torroes', bm, 'lama')
bm, bl = bmesh.new(), bmesh.new()
for (cx, cy, n) in ((-0.88, -0.88, 6), (0.86, -0.86, 5), (-0.85, 0.86, 4), (0.3, -0.85, 3), (-0.24, 0.32, 3),
                    (0.91, 0.3, 2)):
    for k in range(n):
        folha(bm if k % 2 else bl, (cx + random.uniform(-0.06, 0.06), cy + random.uniform(-0.05, 0.05),
                                    0.0625 + 0.001 * k if abs(cx) < 0.9 else 0.0685 + 0.001 * k),
              random.uniform(0.03, 0.055), random.uniform(0, 2 * PI))
obj('folhas_chao', bm, 'folha')
obj('folhas_chao2', bl, 'folha2')
bm = bmesh.new()
mancha(bm, (-0.05, 0.66, 0), 0.08, 0.0632)
mancha(bm, (-0.09, 0.69, 0), 0.05, 0.1005)                                      # pingando no skid
for s in (-1, 1):
    mancha(bm, (s * XC + 0.02, B_PIST - 0.02, 0), 0.03, 0.0757)
obj('oleo', bm, 'oleo')
bm = bmesh.new()
for s in (-1, 1):
    for xt in (s * XC - 0.29, s * XC + 0.29):
        for sy in (-1, 1):
            mancha(bm, (xt + random.uniform(-0.02, 0.02), sy * 0.30 + sy * 0.05, 0), 0.04, 0.0604)
obj('ferrugem_chao', bm, 'ferrugem')

# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    return x * x * (3 - 2 * x)


TOPO = Vector((CRI.x, CRI.y, Z_CRI1))
MEIO = Vector((CRI.x, CRI.y, 0.36))
mat_cri = M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
mat_led = M['led_verde'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
mat_lamp = M['lampada'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
zmax = 0.0
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    th = tilt(fr)
    for k, pv in enumerate(pivos):
        pv.rotation_euler = (th, 0, 0)
        pv.keyframe_insert('rotation_euler', frame=q)
    for k, rb in enumerate(robos):                                              # robô vai e volta, fases opostas
        u = 0.5 - 0.5 * math.cos(2 * PI * (fr + 0.125 * k))
        rb.location = (-0.285 + 0.57 * u, 0, 0)
        rb.keyframe_insert('location', frame=q)
    for k, es in enumerate(escovas):
        es.rotation_euler = (0, 2 * PI * 10 * fr, 0)
        es.keyframe_insert('rotation_euler', frame=q)
    for (cm, B), (hs, s) in zip(camisas, hastes):
        lug = local_para_mundo(s, LUG, th)
        d = (lug - B).normalized()
        cm.location = B
        cm.rotation_quaternion = d.to_track_quat('Z', 'Y')
        hs.location = lug
        hs.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
        for o in (cm, hs):
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
    for k, (pv, p) in enumerate(nos_guia):                                      # feixes guia → cristal
        s = -1 if k == 0 else 1
        a = local_para_mundo(s, p, th)
        dv = MEIO - a
        f = feixes_g[k]
        f.location = a
        f.rotation_quaternion = dv.normalized().to_track_quat('Z', 'Y')
        f.scale = (1 + 0.15 * math.sin(2 * PI * (4 * fr + k * 0.5)),) * 2 + (dv.length - 0.05,)
        for c in ('location', 'rotation_quaternion', 'scale'):
            f.keyframe_insert(c, frame=q)
    for k, lo in enumerate(lentes):                                             # lentes em órbita
        a = 2 * PI * (fr + k / 3)
        pos = Vector((CRI.x + 0.085 * math.cos(a), CRI.y + 0.085 * math.sin(a),
                      0.86 + 0.012 * math.sin(2 * PI * 2 * fr + k * 2.1)))
        dv = TOPO - pos
        lo.location = pos
        lo.rotation_quaternion = dv.normalized().to_track_quat('Z', 'Y')
        f = feixes_l[k]
        f.location = pos + dv.normalized() * 0.012
        f.rotation_quaternion = dv.normalized().to_track_quat('Z', 'Y')
        f.scale = (1.0, 1.0, dv.length - 0.015)
        for o in (lo, f):
            for c in ('location', 'rotation_quaternion'):
                o.keyframe_insert(c, frame=q)
        f.keyframe_insert('scale', frame=q)
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr) ** 2
    mat_cri.default_value = 0.4 + 1.0 * pulso
    mat_cri.keyframe_insert('default_value', frame=q)
    luz_c.energy = 1.5 + 3 * pulso
    luz_c.keyframe_insert('energy', frame=q)
    mat_led.default_value = 12.0 if (int(fr * 8) % 2 == 0) else 1.0
    mat_led.keyframe_insert('default_value', frame=q)
    mat_lamp.default_value = 8.0 if (int(fr * 6) % 2 == 0) else 0.5
    mat_lamp.keyframe_insert('default_value', frame=q)
    if q in (1, QUADROS // 4 + 1, 3 * QUADROS // 4 + 1):                      # confere altura máxima
        sc.frame_set(q)
        bpy.context.view_layer.update()
        for o in sc.objects:
            if o.type == 'MESH' and not o.name.startswith('feixe'):
                for v in o.data.vertices:
                    z = (o.matrix_world @ v.co).z
                    if z > zmax:
                        zmax, zobj = z, o.name
print('ALTURA MÁXIMA %.3f m (%s)' % (zmax, zobj))
for o in list(sc.objects) + [luz_c] + [m.node_tree for m in bpy.data.materials]:
    ad = getattr(o, 'animation_data', None)
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
so.rotation_euler = (math.radians(48), 0, math.radians(-30))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.55
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
sc.view_settings.exposure = -0.5
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 0.42)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_vista = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None
if modo == 'foto':
    sc.cycles.samples = int(os.environ.get('AMOSTRAS', '128'))
    sc.frame_set(13)
    vistas = [(i, ang, alt) for i, (ang, alt) in enumerate(((290, 1.7), (215, 1.9), (110, 2.0), (35, 1.8)))]
    for i, ang, alt in vistas:
        if so_vista and so_vista != str(i):
            continue
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 3.6, math.sin(a) * 2.9, alt)), ALVO, 35)
        sc.render.filepath = os.path.join(AQUI, 'painel_solar_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    if not so_vista or so_vista == 'perto':
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        mirar((0.75, -1.45, 1.05), (0.02, -0.12, 0.5), 30)                      # cristal, feixes, lentes, robô
        sc.render.filepath = os.path.join(AQUI, 'painel_solar_perto.png')
        bpy.ops.render.render(write_still=True)
if so_vista == 'conferir':                                                       # vistas de conferência (não entregues)
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    for nome, pos, alvo in (('pistao', (0.15, 1.25, 0.55), (0.45, 0.5, 0.35)),
                            ('baixo', (-0.2, -0.6, 0.25), (-0.55, 0.2, 0.45)),
                            ('hpu', (-0.5, 1.4, 0.7), (0.0, 0.75, 0.25))):
        mirar(pos, alvo, 28)
        sc.render.filepath = os.path.join(AQUI, 'conferir_painel_%s.png' % nome)
        bpy.ops.render.render(write_still=True)
print('PAINEL SOLAR ok')
