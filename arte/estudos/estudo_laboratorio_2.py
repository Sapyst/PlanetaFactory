"""Estudo isolado (fora do jogo): LABORATÓRIO 2 da IA, 3×3 tiles (lote 10, produção I).
Velocidade: 2,0×. Encaixes de módulo: 2 slots com barramentos dourados e colunas indicadoras de LEDs ciano.
Bocas no padrão do jogo:
- ITEM_ENT_S1: esteira sul de pacotes de dados analíticos (x = 0,0, y = -1,50 m, z = 0,23 m)
- ITEM_ENT_O1: esteira oeste de cartuchos reagentes e amostras sólidas (x = -1,50 m, y = 0,0, z = 0,23 m)
- FLUIDO_ENT_L1: tubulação leste de fluido refrigerante/químico a z = 0,35 m (x = +1,50 m, y = 0,0)

Evolução mecânica pesada e autônoma da IA a partir do laboratório 1:
- Base de concreto armado 2,96 × 2,96 m com bacias de retenção, canaletas de piso e pintura de segurança zebrada.
- Tambor octogonal central de análise espectrométrica reforçado em azul-petróleo industrial e grafite com cintas duplas
  aparafusadas, 4 janelas de quartzo espesso com grades de proteção e comportas pneumáticas de vedação hermética.
- Interior do tambor: 4 emissores de laser cruzados (violeta/azul-ciano) convergindo no ponto focal com anel de indução,
  névoa quântica densa pulsante e gaveta móvel de sustentação analítica.
- 2 slots para módulos no quadrante sul-sudeste com molduras de bronze/aço, trava mecânica e display vertical de LEDs de carga.
- Alimentação sul: roletes motorizados contínuos com braço de carga de ciclo duplo abastecendo a gaveta analítica.
- Alimentação oeste: esteira lateral de roletes com bica guia e detector óptico de pacotes auxiliares.
- Conexão de fluido leste: bocal flangeado rígido a 0,35 m de altura com medidor de vazão de rotor giratório visível,
  filtro Y de sedimentos e tubulação aletada conectada à camisa criogênica do tambor.
- Cúpula de teto espectrométrica: carrossel óptico quântico com lentes colimadoras girando continuamente a 360° em Z,
  prisma cristalino lapidado central com pulso harmônico de ressonância e mastro com antena helicoidal de telemetria.
- Refrigeração extrema: radiador duplo em V no teto/nordeste com duas ventoinhas axiais contra-rotativas aletadas em alta velocidade,
  duas bombas magnéticas em bronze e visor de nível de fluido refrigerante verde fluorescente.
- Exaustor centrífugo duplo com chaminé aletada liberando vapor filtrado da pirólise de amostras.
- Racks de supercomputação quântica ao norte com frentes teladas, matrizes de LEDs de processamento pulsando em binário,
  dissipadores aletados e bancos de cristais de dados de quartzo ressonante.
- Unidade de alta tensão a sudoeste com transformador blindado e anel de confinamento magnético toroidal levitante.

Peças animadas separadas:
- 'carrossel_espectro': carrossel óptico superior com lentes girando continuamente a 360° em Z.
- 'antena_topo': antena de telemetria oscilando no topo do mastro.
- 'ventoinha_rad0', 'ventoinha_rad1': ventiladores axiais contra-rotativos do radiador duplo em V girando velozmente.
- 'rotor_fluxo': rotor do fluxômetro de fluido na entrada leste girando continuamente.
- 'braco_articulado': manipulador mecatrônico transferindo amostras da esteira para a câmara de ensaio.
- 'gaveta': bandeja de carregamento de amostras deslizando para dentro do tambor de análise.
- 'comporta': blindagem frontal da boca do tambor subindo e descendo com os pistões.
- 'anel_forca': anel de plasma magnético levitante oscilando e girando sobre o transformador.
- 'cristal_res': prisma cristalino superior com pulso harmônico de luminescência e escala.
- 'rolete_s0'..'s3', 'rolete_o0'..'o3': roletes de aço das esteiras sul e oeste girando com o fluxo.

Uso: blender -b --python estudo_laboratorio_2.py -- foto
     blender -b --python estudo_laboratorio_2.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço fechado
random.seed(523)
Z_VEC = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

# Cotas padronizadas
C = Vector((0.0, 0.05, 0.0))          # centro do tambor principal
AP = 0.65                             # apótema do tambor octogonal
RV = AP / math.cos(PI / 8)             # raio dos vértices
ZP = 0.16                             # topo do pedestal
ZT = 1.35                             # topo das paredes do tambor
ZR = 1.48                             # topo do beiral do teto
Z_EST = 0.23                          # altura da esteira de itens (bocas sul e oeste)
Z_CANO = 0.35                         # altura da tubulação de fluido (boca leste)

# ------------------------------------------------------------------ utilidades de forma
def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or len(pg.vertices) == 4
    return o

def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))

def cano(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.12:
            for c in (a + u * 0.04, b - u * 0.04):
                tubo(bf, c - u * 0.007, c + u * 0.007, r * 1.45, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)

def prisma(bm, c, ap, z0, z1, n=8):
    rv = ap / math.cos(PI / n)
    vs = []
    for z in (z0, z1):
        vs.append([bm.verts.new((c[0] + rv * math.cos(PI / n + 2 * PI * k / n),
                                 c[1] + rv * math.sin(PI / n + 2 * PI * k / n), z))
                   for k in range(n)])
    bm.faces.new(list(reversed(vs[0])))
    bm.faces.new(vs[1])
    for k in range(n):
        bm.faces.new((vs[0][k], vs[0][(k + 1) % n], vs[1][(k + 1) % n], vs[1][k]))

def casca(bm, c, r_out, r_in, z0, z1, n=24):
    c_xy = Vector((c[0], c[1], 0.0))
    an = []
    for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
        an.append([bm.verts.new(c_xy + Vector((r * math.cos(2 * PI * k / n), r * math.sin(2 * PI * k / n), z)))
                   for k in range(n)])
    for i in range(4):
        A, B = an[i], an[(i + 1) % 4]
        for k in range(n):
            bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))

def hexa(bm, c, r, z0, z1, ponta=0.0):
    cil(bm, Vector((c[0], c[1], (z0 + z1) / 2)), r, z1 - z0, lados=6)
    if ponta > 0:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=0.0, depth=ponta,
                              matrix=Matrix.Translation((c[0], c[1], z1 + ponta / 2)))

def feixe(bc, ba, pts, n=3, r=0.009, passo=4, lado=Vector((1, 0, 0))):
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
    b.inputs['Base Color'].default_value = (0.75, 0.85, 0.88, 1)
    b.inputs['Transmission Weight'].default_value = 0.95
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['Alpha'].default_value = 0.35
    b.inputs['IOR'].default_value = 1.48
    return m

def malha_mat():
    m = bpy.data.materials.new('Tela')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.05, 0.05, 0.055, 1)
    b.inputs['Metallic'].default_value = 0.8
    b.inputs['Roughness'].default_value = 0.4
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
        lt.inputs[1].default_value = 0.35
        nt.links.new(fr.outputs['Value'], lt.inputs[0])
        fios.append(lt)
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fios[0].outputs['Value'], mx.inputs[0])
    nt.links.new(fios[1].outputs['Value'], mx.inputs[1])
    nt.links.new(mx.outputs['Value'], b.inputs['Alpha'])
    return m

def cristal_mat(nome, cor, forca=1.5):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Transmission Weight'].default_value = 0.7
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['IOR'].default_value = 1.62
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

def nevoa_mat():
    m = base3d.volume_mat('NévoaQuântica', (0.45, 0.2, 0.9), 2.8, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 14.0
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (0.55, 0.2, 1.0, 1)
    return m

base3d.M.update({
    'petroleo': mats.material('Petróleo', (0.04, 0.26, 0.30), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.15, sujeira=1.0, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'servidor': mats.material('Servidor', (0.10, 0.11, 0.12), 0, 0.45, desgaste=0.5, sujeira=0.6),
    'cinza': mats.material('Cinza', (0.22, 0.23, 0.24), 0, 0.5, desgaste=1.0, sujeira=1.0, ferrugem=0.6),
    'radiador': mats.material('Radiador', (0.34, 0.36, 0.37), 0, 0.45, desgaste=0.9, sujeira=1.0, ferrugem=0.4),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.9, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.9, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'bronze': mats.material('Bronze', (0.55, 0.38, 0.18), 1.0, 0.35, pintura=False, sujeira=0.7),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.015, 0.014, 0.013), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'lente': mats.material('Lente', (0.05, 0.08, 0.12), 0, 0.04, pintura=False, sujeira=0.0),
    'liquido': luz_mat('FluidoCriogenico', (0.1, 0.85, 0.8), 0.8),
    'vidro': vidro_mat(),
    'malha': malha_mat(),
    'listras': base3d.listras_mat(),
    'cristal': cristal_mat('CristalDados', (0.52, 0.24, 0.9), 1.4),
    'cristal_rack': cristal_mat('CristalRack', (0.2, 0.7, 0.95), 1.8),
    'cristal_topo': cristal_mat('CristalTopo', (0.6, 0.2, 1.0), 3.0),
    'nevoa': nevoa_mat(),
    'vapor': base3d.volume_mat('VaporLab', (0.88, 0.9, 0.92), 2.8, 1.8, 3.2),
    'laser': luz_mat('LaserPlasma', (0.2, 0.8, 1.0), 28.0),
    'campo': luz_mat('AnelCampo', (0.55, 0.2, 1.0), 4.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.9, 0.95), 12.0),
    'led_ambar': luz_mat('LedAmbar', (1.0, 0.5, 0.05), 10.0),
    'led_verde': luz_mat('LedVerde', (0.1, 0.95, 0.25), 10.0),
    'ouro': mats.material('OuroContatos', (0.85, 0.7, 0.18), 1.0, 0.2, pintura=False, sujeira=0.2),
})

# ------------------------------------------------------------------ laje e demarcações de segurança
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, 0.08))
# Canaletas de escoamento e drenos
caixa_de(bm, (-1.35, -1.35, 0.07), (1.35, -1.30, 0.081))
caixa_de(bm, (-1.35, 1.30, 0.07), (1.35, 1.35, 0.081))
caixa_de(bm, (-1.35, -1.30, 0.07), (-1.30, 1.30, 0.081))
obj('laje', bm, 'concreto')

# Demarcações de faixa de perigo no piso
bm = bmesh.new()
# Área de giro do braço sul
caixa_de(bm, (-0.95, -1.15, 0.08), (-0.90, -0.55, 0.082))
caixa_de(bm, (-0.95, -1.15, 0.08), (-0.26, -1.10, 0.082))
# Corredores das esteiras
for x in (-0.28, 0.28):
    caixa_de(bm, (x - 0.025, -1.48, 0.08), (x + 0.025, -0.75, 0.082))
for y in (-0.28, 0.28):
    caixa_de(bm, (-1.48, y - 0.025, 0.08), (-0.75, y + 0.025, 0.082))
# Borda dos slots de módulo
caixa_de(bm, (0.55, -1.35, 0.08), (1.35, -1.30, 0.082))
caixa_de(bm, (1.30, -1.35, 0.08), (1.35, -0.65, 0.082))
obj('faixas_piso', bm, 'listras')

# ------------------------------------------------------------------ tambor octogonal do analisador Tier 2
bm = bmesh.new()
prisma(bm, C, 0.68, 0.08, ZP)                                             # pedestal octogonal reforçado
obj('tambor_pedestal', bm, 'cinza')

bm = bmesh.new()
prisma(bm, C, AP + 0.03, ZT, ZT + 0.04)                                   # beiral
prisma(bm, C, AP - 0.01, ZT + 0.04, ZR)                                   # teto
obj('tambor_teto', bm, 'grafite')

# Paredes, molduras e janelas de inspeção
bm, bmg, bmv, bml = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
LARG = 2 * AP * math.tan(PI / 8)
JAN = (0.50, 1.05)                                                        # altura das janelas ampliadas
HATCH = (-0.18, 0.18, 0.60, 0.95)                                         # boca da gaveta (face sul)

for k in range(8):
    a = k * PI / 4
    rot = Matrix.Rotation(a, 3, 'Z')
    d = Vector((math.cos(a), math.sin(a), 0))
    cen = C + d * (AP - 0.01)
    def painel(y0, y1, z0, z1, alvo=bm, esp=0.025, saliente=0.0):
        caixa(alvo, cen + d * saliente + rot @ Vector((0, (y0 + y1) / 2, 0)) + Vector((0, 0, (z0 + z1) / 2)),
              (esp, y1 - y0, z1 - z0), rot)
    w = LARG / 2 - 0.02
    if k == 6:  # Face sul: comporta e boca de entrada da gaveta
        painel(-w, w, ZP, HATCH[2])
        painel(-w, w, HATCH[3], ZT)
        painel(-w, HATCH[0], HATCH[2], HATCH[3])
        painel(HATCH[1], w, HATCH[2], HATCH[3])
        for y0, y1, z0, z1 in ((HATCH[0] - 0.045, HATCH[0], HATCH[2] - 0.045, HATCH[3] + 0.025),
                               (HATCH[1], HATCH[1] + 0.045, HATCH[2] - 0.045, HATCH[3] + 0.025),
                               (HATCH[0] - 0.045, HATCH[1] + 0.045, HATCH[2] - 0.045, HATCH[2])):
            painel(y0, y1, z0, z1, bml, 0.035, 0.02)                      # moldura listrada
    elif k in (1, 3, 5, 7):  # Faces diagonais: visores de quartzo com molduras reforçadas
        painel(-w, w, ZP, JAN[0])
        painel(-w, w, JAN[1], ZT)
        painel(-w, w, JAN[0], JAN[1], bmv, 0.012)
        # Moldura quádrupla e travessa vertical
        for y0, y1, z0, z1 in ((-w, -w + 0.04, JAN[0], JAN[1]), (w - 0.04, w, JAN[0], JAN[1]),
                               (-w, w, JAN[0] - 0.025, JAN[0] + 0.025), (-w, w, JAN[1] - 0.025, JAN[1] + 0.025),
                               (-0.015, 0.015, JAN[0], JAN[1])):
            painel(y0, y1, z0, z1, bmg, 0.04, 0.015)
        # Grade de proteção sobre o visor
        for jz in range(3):
            z_fio = JAN[0] + 0.12 + jz * 0.14
            tubo(bmg, cen + rot @ Vector((0, -w + 0.03, z_fio)) + d * 0.025,
                      cen + rot @ Vector((0, w - 0.03, z_fio)) + d * 0.025, 0.004, 8)
    else:  # Faces retas (Leste, Norte, Oeste): blindagem com aletas e conectores
        painel(-w, w, ZP, ZT)
        # Nervuras horizontais e grelhas
        painel(-w + 0.02, w - 0.02, 0.65, 0.70, bmg, 0.035, 0.015)
        if k == 0:  # Leste: conector com camisa criogênica
            tubo(bmg, cen + Vector((0, 0, 0.85)), cen + d * 0.08 + Vector((0, 0, 0.85)), 0.06, 16)
        elif k == 4:  # Oeste: passagem interna de amostras
            painel(-0.15, 0.15, 0.72, 0.98, bmg, 0.03, 0.015)
    
    # Parafusos industriais nas abas
    for j in range(5):
        for z in (ZP + 0.03, ZT - 0.03):
            y = -w + 0.04 + j * (2 * w - 0.08) / 4
            cil(bmg, cen + d * 0.015 + rot @ Vector((0, y, 0)) + Vector((0, 0, z)), 0.007, 0.01, d, lados=6)
    # Coluna reforçada em cada vértice
    av = (k + 0.5) * PI / 4
    dv = Vector((math.cos(av), math.sin(av), 0))
    caixa(bmg, C + dv * (RV - 0.004) + Vector((0, 0, (ZP + ZT) / 2)), (0.05, 0.05, ZT - ZP), Matrix.Rotation(av, 3, 'Z'))

obj('tambor_paineis', bm, 'petroleo')
obj('tambor_estrutura', bmg, 'grafite')
obj('tambor_janelas', bmv, 'vidro')
obj('tambor_boca_listras', bml, 'listras')

# Escorridos de óleo e poeira
bm = bmesh.new()
for k in range(8):
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    for j in range(2):
        u = random.uniform(-0.16, 0.16)
        z1 = random.uniform(0.4, 0.65) if k % 2 else random.uniform(0.55, 1.2)
        caixa(bm, C + d * (AP + 0.012) + t * u + Vector((0, 0, (ZP + 0.02 + z1) / 2)),
              (0.001, 0.009, z1 - ZP - 0.02), Matrix.Rotation(a, 3, 'Z'))
obj('tambor_escorridos', bm, 'oleo')

# Comporta pneumática da boca sul
YS = C.y - AP - 0.038
bm = bmesh.new()
caixa_de(bm, (-0.20, YS - 0.035, HATCH[3] + 0.03), (0.20, YS - 0.012, HATCH[3] + 0.35))
caixa_de(bm, (-0.20, YS - 0.035, HATCH[3] + 0.35), (0.20, C.y - AP, HATCH[3] + 0.37))
for x in (-0.21, 0.21):
    caixa_de(bm, (x - 0.014, YS - 0.014, HATCH[2] - 0.04), (x + 0.014, C.y - AP, HATCH[3] + 0.02))
obj('comporta_caixa', bm, 'grafite')

comporta = bpy.data.objects.new('comporta', None)
sc.collection.objects.link(comporta)
bm = bmesh.new()
caixa_de(bm, (-0.195, YS - 0.009, HATCH[2]), (0.195, YS + 0.009, HATCH[3] + 0.01))
for z in (HATCH[2] + 0.08, HATCH[2] + 0.20):
    caixa_de(bm, (-0.185, YS - 0.015, z), (0.185, YS - 0.009, z + 0.03))
obj('comporta_chapa', bm, 'aco', comporta)

# Cilindros pneumáticos da comporta
bm, bmc = bmesh.new(), bmesh.new()
for x in (-0.15, 0.15):
    tubo(bm, Vector((x, YS - 0.024, HATCH[3] + 0.34)), Vector((x, YS - 0.024, HATCH[3] + 0.12)), 0.012, 12)
    tubo(bmc, Vector((x, YS - 0.024, HATCH[3] + 0.14)), Vector((x, YS - 0.024, HATCH[3] - 0.02)), 0.007, 12)
    mangueira(bm, [Vector((x, YS - 0.024, HATCH[3] + 0.32)), Vector((x + (0.04 if x > 0 else -0.04), YS - 0.04, HATCH[3] + 0.30)),
                   Vector((x + (0.05 if x > 0 else -0.05), YS - 0.01, HATCH[3] + 0.25))], 0.004)
obj('comporta_camisas', bm, 'grafite')
obj('comporta_hastes', bmc, 'cromo', comporta)

# ------------------------------------------------------------------ gaveta de ensaio e interior do tambor
gaveta = bpy.data.objects.new('gaveta', None)
sc.collection.objects.link(gaveta)
bm, bmc = bmesh.new(), bmesh.new()
# Mesa da gaveta
caixa_de(bm, (-0.15, -0.15, HATCH[2] + 0.02), (0.15, 0.15, HATCH[2] + 0.04))
# Suporte com garras centradoras
for dx, dy in ((-0.11, -0.11), (0.11, -0.11), (-0.11, 0.11), (0.11, 0.11)):
    cil(bm, Vector((dx, dy, HATCH[2] + 0.05)), 0.014, 0.025, lados=8)
# Berço de quartzo central translúcido
cil(bmc, Vector((0, 0, HATCH[2] + 0.045)), 0.07, 0.015, lados=16)
obj('gaveta_mesa', bm, 'aco', gaveta)
obj('gaveta_berco', bmc, 'vidro', gaveta)

# Trilhos telescópicos da gaveta
bm = bmesh.new()
for x in (-0.165, 0.165):
    tubo(bm, Vector((x, YS + 0.01, HATCH[2] + 0.01)), Vector((x, C.y + 0.25, HATCH[2] + 0.01)), 0.01, 12)
obj('gaveta_trilhos', bm, 'cromo')

# ------------------------------------------------------------------ interior: 4 lasers cruzados e névoa
bm, bmlas = bmesh.new(), bmesh.new()
# Anel de campo no interior
cil(bm, C + Vector((0, 0, 0.78)), 0.42, 0.04, lados=24)
casca(bm, C + Vector((0, 0, 0.78)), 0.44, 0.38, 0.76, 0.80, 24)
# 4 canhões laser cruzados a 45°
for i, ang in enumerate((PI/4, 3*PI/4, 5*PI/4, 7*PI/4)):
    rot_las = Matrix.Rotation(ang, 3, 'Z')
    d_las = Vector((math.cos(ang), math.sin(ang), 0))
    p_orig = C + d_las * 0.38 + Vector((0, 0, 0.85))
    tubo(bm, p_orig + d_las * 0.05, p_orig, 0.022, 12)
    tubo(bm, p_orig, p_orig - d_las * 0.06, 0.014, 12)
    # Cone colimador
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.016, radius2=0.008, depth=0.03,
                          matrix=Matrix.Translation(p_orig - d_las * 0.075) @ rot_las.to_4x4())
    # Feixe laser convergindo no centro da gaveta
    p_foco = C + Vector((0, 0, HATCH[2] + 0.06))
    tubo(bmlas, p_orig - d_las * 0.08, p_foco, 0.0035, 8)
obj('interior_estrutura', bm, 'grafite')
obj('interior_lasers', bmlas, 'laser')

# Névoa quântica interior
bm = bmesh.new()
cil(bm, C + Vector((0, 0, 0.78)), 0.34, 0.35, lados=16)
obj('EFEITO_nevoa_interior', bm, 'nevoa')

# Luz pontual dos lasers pulsantes
luz_las_data = bpy.data.lights.new('LuzLaserInterna', 'POINT')
luz_las_data.energy = 85.0
luz_las_data.color = (0.3, 0.7, 1.0)
luz_las_data.shadow_soft_size = 0.08
luz_las_obj = bpy.data.objects.new('EFEITO_LuzLaser', luz_las_data)
sc.collection.objects.link(luz_las_obj)
luz_las_obj.location = C + Vector((0, 0, 0.78))

# ------------------------------------------------------------------ 2 SLOTS DE MÓDULOS (quadrante sul-sudeste)
# Exigência de Tier 2: 2 slots de módulos com indicadores visuais
bm, bmo, bml_mod = bmesh.new(), bmesh.new(), bmesh.new()
X_MOD, Y_MOD = 0.95, -0.95
caixa_de(bm, (X_MOD - 0.32, Y_MOD - 0.32, 0.08), (X_MOD + 0.32, Y_MOD + 0.32, 0.42))
for i, off_x in enumerate((-0.14, 0.14)):
    # Abertura do slot com chanfro
    caixa_de(bm, (X_MOD + off_x - 0.09, Y_MOD - 0.22, 0.41), (X_MOD + off_x + 0.09, Y_MOD + 0.22, 0.425))
    # Cartucho do módulo inserido
    caixa_de(bm, (X_MOD + off_x - 0.07, Y_MOD - 0.18, 0.25), (X_MOD + off_x + 0.07, Y_MOD + 0.18, 0.52))
    # Contatos e guias de ouro/latão
    for dy in (-0.12, 0.0, 0.12):
        caixa_de(bmo, (X_MOD + off_x - 0.075, Y_MOD + dy - 0.02, 0.43), (X_MOD + off_x + 0.075, Y_MOD + dy + 0.02, 0.50))
    # Coluna vertical de 4 LEDs indicadores por slot
    for j in range(4):
        cil(bml_mod, Vector((X_MOD + off_x, Y_MOD - 0.25, 0.16 + j * 0.06)), 0.009, 0.012, Vector((0, -1, 0)), lados=8)
obj('slots_modulo_base', bm, 'grafite')
obj('slots_modulo_contatos', bmo, 'ouro')
obj('slots_modulo_leds', bml_mod, 'led_ciano')

# Cabos blindados dos módulos indo para a base do tambor
bm = bmesh.new()
mangueira(bm, [Vector((X_MOD - 0.1, Y_MOD + 0.25, 0.25)), Vector((X_MOD - 0.25, Y_MOD + 0.45, 0.15)),
               Vector((C.x + 0.45, C.y - 0.45, 0.15))], 0.012)
mangueira(bm, [Vector((X_MOD + 0.1, Y_MOD + 0.25, 0.25)), Vector((X_MOD + 0.15, Y_MOD + 0.55, 0.15)),
               Vector((C.x + 0.55, C.y - 0.35, 0.15))], 0.012)
obj('slots_modulo_cabos', bm, 'isolante')

# ------------------------------------------------------------------ BOCA SUL (ITEM_ENT_S1): Esteira e manipulador
# Boca a x = 0.0, y = -1.50 m, z = 0.23 m
bm, bmr = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.24, -1.50, 0.08), (-0.20, -0.65, Z_EST + 0.04))
caixa_de(bm, (0.20, -1.50, 0.08), (0.24, -0.65, Z_EST + 0.04))
# Travessas e sensores ópticos
caixa_de(bm, (-0.24, -1.48, Z_EST - 0.05), (0.24, -1.44, Z_EST - 0.02))
caixa_de(bm, (-0.24, -0.80, Z_EST - 0.05), (0.24, -0.76, Z_EST - 0.02))
# Roletes da esteira sul
roletes_s = []
for i in range(4):
    y_r = -1.40 + i * 0.22
    r_obj = bpy.data.objects.new(f'rolete_s{i}', None)
    sc.collection.objects.link(r_obj)
    r_obj.location = Vector((0, y_r, Z_EST))
    bm_r = bmesh.new()
    cil(bm_r, Vector((0, 0, 0)), 0.022, 0.38, Vector((1, 0, 0)), lados=14)
    obj(f'rolete_s{i}_mesh', bm_r, 'aco', r_obj)
    roletes_s.append(r_obj)
obj('esteira_sul_calhas', bm, 'grafite')

# Braço mecânico articulado de alimentação rápida
braco_base = bpy.data.objects.new('braco_articulado', None)
sc.collection.objects.link(braco_base)
braco_base.location = Vector((-0.45, -0.85, 0.08))

bm, bmc = bmesh.new(), bmesh.new()
# Pedestal do robô
cil(bm, Vector((0, 0, 0.12)), 0.08, 0.24, lados=16)
# Ombro articulado
cil(bmc, Vector((0, 0, 0.28)), 0.05, 0.12, Vector((0, 1, 0)), lados=14)
tubo(bm, Vector((0, 0, 0.28)), Vector((0.22, 0.18, 0.42)), 0.028, 12)
obj('braco_membros', bm, 'amarelo', braco_base)
obj('braco_articulacoes', bmc, 'grafite', braco_base)

# Antebraço e garra
braco_garra = bpy.data.objects.new('braco_garra', None)
sc.collection.objects.link(braco_garra)
braco_garra.parent = braco_base
braco_garra.location = Vector((0.22, 0.18, 0.42))
bm, bmc = bmesh.new(), bmesh.new()
cil(bmc, Vector((0, 0, 0)), 0.04, 0.10, Vector((1, 0, 0)), lados=12)
tubo(bm, Vector((0, 0, 0)), Vector((0.20, 0.14, -0.20)), 0.022, 12)
cil(bmc, Vector((0.20, 0.14, -0.20)), 0.03, 0.06, Vector((0, 0, 1)), lados=12)
for dx in (-0.035, 0.035):
    caixa_de(bm, (0.20 + dx - 0.008, 0.14 - 0.025, -0.28), (0.20 + dx + 0.008, 0.14 + 0.025, -0.20))
obj('braco_garra_membro', bm, 'amarelo', braco_garra)
obj('braco_garra_junta', bmc, 'grafite', braco_garra)

# Pacote de pesquisa em trânsito (cartucho de cristal + microchip)
pacote = bpy.data.objects.new('pacote_pesquisa', None)
sc.collection.objects.link(pacote)
bm, bmc = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.06, -0.06, 0.0), (0.06, 0.06, 0.03))
for dy in (-0.04, 0.0, 0.04):
    caixa_de(bm, (-0.05, dy - 0.01, 0.03), (0.05, dy + 0.01, 0.04))
hexa(bmc, Vector((0, 0, 0.035)), 0.032, 0.035, 0.09, ponta=0.02)
obj('pacote_base', bm, 'ouro', pacote)
obj('pacote_cristal', bmc, 'cristal', pacote)

# ------------------------------------------------------------------ BOCA OESTE (ITEM_ENT_O1): Entrada lateral de amostras
# Boca a x = -1.50 m, y = 0.0 m, z = 0.23 m
bm, bmr_o = bmesh.new(), bmesh.new()
caixa_de(bm, (-1.50, -0.24, 0.08), (-0.70, -0.20, Z_EST + 0.04))
caixa_de(bm, (-1.50, 0.20, 0.08), (-0.70, 0.24, Z_EST + 0.04))
# Bica inclinada entrando na parede oeste do tambor
caixa_de(bm, (-0.72, -0.18, Z_EST - 0.02), (-0.52, 0.18, Z_EST + 0.08))
# Roletes da esteira oeste
roletes_o = []
for i in range(4):
    x_r = -1.40 + i * 0.22
    r_obj = bpy.data.objects.new(f'rolete_o{i}', None)
    sc.collection.objects.link(r_obj)
    r_obj.location = Vector((x_r, 0, Z_EST))
    bm_ro = bmesh.new()
    cil(bm_ro, Vector((0, 0, 0)), 0.022, 0.38, Vector((0, 1, 0)), lados=14)
    obj(f'rolete_o{i}_mesh', bm_ro, 'aco', r_obj)
    roletes_o.append(r_obj)
obj('esteira_oeste_calhas', bm, 'grafite')

# Cartucho de amostra entrando pela esteira oeste
amostra_o = bpy.data.objects.new('amostra_reagente', None)
sc.collection.objects.link(amostra_o)
bm, bmc = bmesh.new(), bmesh.new()
cil(bm, Vector((0, 0, 0.025)), 0.04, 0.05, lados=12)
cil(bmc, Vector((0, 0, 0.06)), 0.025, 0.04, lados=12)
obj('amostra_corpo', bm, 'aluminio', amostra_o)
obj('amostra_cristal', bmc, 'cristal_rack', amostra_o)

# ------------------------------------------------------------------ BOCA LESTE (FLUIDO_ENT_L1): Tubulação de refrigeração criogênica
# Boca a x = +1.50 m, y = 0.0 m, z = 0.35 m
bm, bf, bm_rot = bmesh.new(), bmesh.new(), bmesh.new()
# Flange de encaixe faceando o limite do tile (+1.50 m)
tubo(bf, Vector((1.50, 0, Z_CANO)), Vector((1.44, 0, Z_CANO)), 0.075, 16)
tubo(bm, Vector((1.44, 0, Z_CANO)), Vector((1.05, 0, Z_CANO)), 0.045, 16)
# Carcaça do medidor de vazão com visor circular de vidro
cil(bm, Vector((1.25, 0, Z_CANO)), 0.07, 0.06, Vector((0, 1, 0)), lados=16)
cil(bf, Vector((1.25, 0.032, Z_CANO)), 0.055, 0.008, Vector((0, 1, 0)), lados=16) # aro de latão
# Tubo subindo para alimentar a camisa do tambor e o radiador
cano(bm, bf, [Vector((1.05, 0, Z_CANO)), Vector((0.90, 0, Z_CANO)),
              Vector((0.90, 0, 0.85)), Vector((C.x + AP + 0.05, C.y, 0.85))], 0.035)
obj('tubo_fluido_leste', bm, 'aco')
obj('tubo_fluido_flanges', bf, 'latao')

# Rotor do medidor de fluxo (visível pela janela)
rotor_fluxo = bpy.data.objects.new('rotor_fluxo', None)
sc.collection.objects.link(rotor_fluxo)
rotor_fluxo.location = Vector((1.25, 0.025, Z_CANO))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.015, 0.012, Vector((0, 1, 0)), lados=8)
for ang in (0, PI/2, PI, 3*PI/2):
    rot_pa = Matrix.Rotation(ang, 3, 'Y')
    caixa(bm, rot_pa @ Vector((0.028, 0, 0)), (0.026, 0.006, 0.004), rot_pa)
obj('rotor_fluxo_pas', bm, 'bronze', rotor_fluxo)

# ------------------------------------------------------------------ REFRIGERAÇÃO REFORÇADA: Radiador em V duplo e bombas (Nordeste)
# Posicionado no quadrante nordeste (x ~ 0.85, y ~ 0.85)
bm, bma = bmesh.new(), bmesh.new()
X_RAD, Y_RAD, Z_RAD = 0.85, 0.85, 0.16
# Chassi do radiador
caixa_de(bm, (X_RAD - 0.40, Y_RAD - 0.35, Z_RAD), (X_RAD + 0.40, Y_RAD + 0.35, Z_RAD + 0.65))
# Aletas de dissipação
for iz in range(12):
    z_a = Z_RAD + 0.08 + iz * 0.045
    caixa_de(bma, (X_RAD - 0.38, Y_RAD - 0.36, z_a), (X_RAD + 0.38, Y_RAD + 0.36, z_a + 0.012))
# Carenagens circulares superiores para duas ventoinhas
casca(bm, (X_RAD - 0.18, Y_RAD, Z_RAD + 0.65), 0.17, 0.14, Z_RAD + 0.65, Z_RAD + 0.75, 20)
casca(bm, (X_RAD + 0.18, Y_RAD, Z_RAD + 0.65), 0.17, 0.14, Z_RAD + 0.65, Z_RAD + 0.75, 20)
# Grades protetoras
for off_x in (-0.18, 0.18):
    for a in range(4):
        ang = a * PI / 4
        tubo(bm, Vector((X_RAD + off_x - 0.14 * math.cos(ang), Y_RAD - 0.14 * math.sin(ang), Z_RAD + 0.75)),
                 Vector((X_RAD + off_x + 0.14 * math.cos(ang), Y_RAD + 0.14 * math.sin(ang), Z_RAD + 0.75)), 0.004, 6)
obj('radiador_chassi', bm, 'grafite')
obj('radiador_aletas', bma, 'radiador')

# Duas ventoinhas axiais contra-rotativas
ventoinhas = []
for i, off_x in enumerate((-0.18, 0.18)):
    v_obj = bpy.data.objects.new(f'ventoinha_rad{i}', None)
    sc.collection.objects.link(v_obj)
    v_obj.location = Vector((X_RAD + off_x, Y_RAD, Z_RAD + 0.70))
    bm_v = bmesh.new()
    cil(bm_v, Vector((0, 0, 0)), 0.035, 0.025, Z_VEC, lados=12)
    for k in range(5):
        ang = k * 2 * PI / 5
        rot_pa = Matrix.Rotation(ang, 3, 'Z') @ Matrix.Rotation(0.35, 3, 'X')
        caixa(bm_v, rot_pa @ Vector((0.07, 0, 0)), (0.08, 0.03, 0.004), rot_pa)
    obj(f'ventoinha_rad{i}_mesh', bm_v, 'aluminio', v_obj)
    ventoinhas.append(v_obj)

# Duas bombas magnéticas em bronze conectando ao radiador
bm, bf = bmesh.new(), bmesh.new()
for off_y in (-0.18, 0.18):
    cil(bm, Vector((X_RAD - 0.48, Y_RAD + off_y, Z_RAD + 0.18)), 0.07, 0.14, Vector((1, 0, 0)), lados=14)
    cil(bf, Vector((X_RAD - 0.48, Y_RAD + off_y, Z_RAD + 0.18)), 0.085, 0.02, Vector((1, 0, 0)), lados=14)
    # Manômetro em latão com ponteiro
    cil(bf, Vector((X_RAD - 0.48, Y_RAD + off_y, Z_RAD + 0.32)), 0.035, 0.02, Vector((0, 1, 0)), lados=12)
cano(bm, bf, [Vector((X_RAD - 0.48, Y_RAD, Z_RAD + 0.18)), Vector((C.x + 0.50, Y_RAD, Z_RAD + 0.18)),
              Vector((C.x + 0.50, C.y + 0.45, 0.45))], 0.028)
obj('bombas_corpo', bm, 'bronze')
obj('bombas_detalhes', bf, 'latao')

# ------------------------------------------------------------------ EXAUSTOR CENTRÍFUGO E CHAMINÉ (Noroeste)
bm, bmvap = bmesh.new(), bmesh.new()
X_EX, Y_EX = -0.85, 0.85
# Caracol voluta do exaustor centrífugo
cil(bm, Vector((X_EX, Y_EX, 0.45)), 0.22, 0.18, Vector((0, 1, 0)), lados=18)
# Duto de entrada vindo do tambor
tubo(bm, Vector((X_EX + 0.15, Y_EX, 0.45)), Vector((C.x - 0.55, C.y + 0.35, 0.65)), 0.05, 14)
# Chaminé vertical aletada
tubo(bm, Vector((X_EX, Y_EX, 0.55)), Vector((X_EX, Y_EX, 1.85)), 0.08, 16)
for iz in range(5):
    tubo(bm, Vector((X_EX, Y_EX, 1.10 + iz * 0.14 - 0.01)), Vector((X_EX, Y_EX, 1.10 + iz * 0.14 + 0.01)), 0.11, 16)
# Defletor cônico no topo da chaminé
bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.14, radius2=0.04, depth=0.12,
                      matrix=Matrix.Translation((X_EX, Y_EX, 1.92)))
obj('exaustor_chamine', bm, 'grafite')

# Volume de vapor suave saindo da chaminé
cil(bmvap, Vector((X_EX, Y_EX, 2.15)), 0.12, 0.45, lados=12)
obj('EFEITO_vapor_chamine', bmvap, 'vapor')

# ------------------------------------------------------------------ RACKS DE SUPERCOMPUTAÇÃO QUÂNTICA (Norte)
# Posicionado em y ~ +1.15 m, cobrindo x de -0.6 a +0.6
bm, bmt, bmc_rack, bml_rack = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
Y_RACK = 1.18
for i, x_r in enumerate((-0.42, 0.0, 0.42)):
    # Estrutura do rack de servidor
    caixa_de(bm, (x_r - 0.18, Y_RACK - 0.18, 0.08), (x_r + 0.18, Y_RACK + 0.18, 1.25))
    # Porta de tela metálica frontal (sul)
    caixa_de(bmt, (x_r - 0.16, Y_RACK - 0.182, 0.14), (x_r + 0.16, Y_RACK - 0.180, 1.18))
    # Grelha de exaustão e portas traseiras (norte)
    for jz in range(8):
        z_gr = 0.25 + jz * 0.11
        caixa_de(bmt, (x_r - 0.14, Y_RACK + 0.180, z_gr), (x_r + 0.14, Y_RACK + 0.184, z_gr + 0.035))
    # Fechaduras e canaleta vertical na traseira
    cil(bm, Vector((x_r + 0.15, Y_RACK + 0.185, 0.70)), 0.012, 0.02, Vector((0, 1, 0)), lados=8)
    tubo(bm, Vector((x_r - 0.12, Y_RACK + 0.182, 0.08)), Vector((x_r - 0.12, Y_RACK + 0.182, 1.20)), 0.01, 8)
    # Cristais de dados dentro do rack
    for jz in range(3):
        z_c = 0.35 + jz * 0.32
        hexa(bmc_rack, Vector((x_r - 0.07, Y_RACK, z_c)), 0.024, z_c, z_c + 0.12, ponta=0.03)
        hexa(bmc_rack, Vector((x_r + 0.07, Y_RACK, z_c)), 0.024, z_c, z_c + 0.12, ponta=0.03)
        # Painel com LEDs piscantes
        for jled in range(4):
            cil(bml_rack, Vector((x_r - 0.12 + jled * 0.08, Y_RACK - 0.175, z_c - 0.04)), 0.007, 0.01, Vector((0, -1, 0)), lados=6)
obj('racks_corpo', bm, 'servidor')
obj('racks_telas', bmt, 'malha')
obj('racks_cristais', bmc_rack, 'cristal_rack')
obj('racks_leds', bml_rack, 'led_ciano')

# Eletrocalhas e feixes maciços de cabos de fibra óptica
bm, bmcab, bma = bmesh.new(), bmesh.new(), bmesh.new()
# Eletrocalha suspensa entre os racks e o tambor
caixa_de(bm, (-0.55, 0.70, 1.28), (0.55, 0.85, 1.34))
tubo(bm, Vector((-0.45, 0.77, 1.28)), Vector((-0.45, 0.77, 0.08)), 0.025, 12)
tubo(bm, Vector((0.45, 0.77, 1.28)), Vector((0.45, 0.77, 0.08)), 0.025, 12)
# Feixes de cabos descendo dos racks para o tambor
feixe(bmcab, bma, [Vector((-0.35, Y_RACK - 0.18, 1.10)), Vector((-0.35, 0.80, 1.30)),
                   Vector((C.x - 0.25, C.y + 0.45, ZT + 0.02))], n=4, r=0.008)
feixe(bmcab, bma, [Vector((0.35, Y_RACK - 0.18, 1.10)), Vector((0.35, 0.80, 1.30)),
                   Vector((C.x + 0.25, C.y + 0.45, ZT + 0.02))], n=4, r=0.008)
obj('eletrocalha_calha', bm, 'grafite')
obj('eletrocalha_cabos', bmcab, 'isolante')
obj('eletrocalha_abracadeiras', bma, 'latao')

# ------------------------------------------------------------------ UNIDADE DE POTÊNCIA E ANEL MAGNÉTICO (Sudoeste)
X_POT, Y_POT = -0.95, -0.95
bm, bmcob = bmesh.new(), bmesh.new()
# Gabinete do transformador
caixa_de(bm, (X_POT - 0.30, Y_POT - 0.30, 0.08), (X_POT + 0.30, Y_POT + 0.30, 0.65))
# Aletas de refrigeração
for ix in range(8):
    x_al = X_POT - 0.24 + ix * 0.065
    caixa_de(bm, (x_al - 0.008, Y_POT - 0.32, 0.15), (x_al + 0.008, Y_POT + 0.32, 0.60))
# Isoladores de porcelana no topo
for dx, dy in ((-0.12, -0.12), (0.12, -0.12), (0.0, 0.12)):
    for iz in range(3):
        cil(bm, Vector((X_POT + dx, Y_POT + dy, 0.68 + iz * 0.04)), 0.035 - iz * 0.005, 0.03, lados=12)
    # Barramento maciço de cobre
    tubo(bmcob, Vector((X_POT + dx, Y_POT + dy, 0.80)), Vector((X_POT + dx, Y_POT + dy + 0.15, 0.80)), 0.012, 12)
obj('unidade_potencia_gabinete', bm, 'grafite')
obj('unidade_potencia_barramentos', bmcob, 'cobre')

# Anel de confinamento de plasma toroidal levitante
anel_forca = bpy.data.objects.new('anel_forca', None)
sc.collection.objects.link(anel_forca)
anel_forca.location = Vector((X_POT, Y_POT, 0.95))
bm = bmesh.new()
# Toro de plasma / condutor supercondutor
toro_pts = []
for a in range(24):
    ang = a * 2 * PI / 24
    d = Vector((math.cos(ang), math.sin(ang), 0))
    toro_pts.append(d * 0.20)
for p0, p1 in zip(toro_pts, toro_pts[1:] + [toro_pts[0]]):
    tubo(bm, p0, p1, 0.022, 10)
# Suportes estáticos flutuantes
for a in range(3):
    ang = a * 2 * PI / 3
    d = Vector((math.cos(ang), math.sin(ang), 0))
    cil(bm, d * 0.20, 0.03, 0.04, Z_VEC, lados=8)
obj('anel_forca_plasma', bm, 'campo', anel_forca)

# ------------------------------------------------------------------ TETO: Cúpula Espectrométrica, Carrossel Óptico e Antena
bm, bmo = bmesh.new(), bmesh.new()
# Colunas de suporte da cúpula de cristal
for a in range(6):
    ang = a * 2 * PI / 6
    p_col = C + Vector((0.42 * math.cos(ang), 0.42 * math.sin(ang), ZR))
    tubo(bm, p_col, p_col + Vector((0, 0, 0.35)), 0.022, 12)
    # Anel superior fixo
    tubo(bmo, p_col + Vector((0, 0, 0.35)),
              C + Vector((0.42 * math.cos(ang + PI/3), 0.42 * math.sin(ang + PI/3), ZR + 0.35)), 0.018, 12)
obj('cupula_colunas', bm, 'grafite')
obj('cupula_anel_fixo', bmo, 'latao')

# Prisma cristalino central ressonante
cristal_res = bpy.data.objects.new('cristal_res', None)
sc.collection.objects.link(cristal_res)
cristal_res.location = C + Vector((0, 0, ZR + 0.16))
bm = bmesh.new()
hexa(bm, Vector((0, 0, 0)), 0.11, -0.12, 0.12, ponta=0.10)
obj('cristal_res_geometria', bm, 'cristal_topo', cristal_res)

# Carrossel óptico quântico superior girando a 360° em Z
carrossel = bpy.data.objects.new('carrossel_espectro', None)
sc.collection.objects.link(carrossel)
carrossel.location = C + Vector((0, 0, ZR + 0.42))
bm, bmlen = bmesh.new(), bmesh.new()
# Eixo central e anel giratório
cil(bm, Vector((0, 0, 0)), 0.06, 0.08, Z_VEC, lados=16)
casca(bm, Vector((0, 0, 0)), 0.36, 0.30, -0.02, 0.02, 24)
# 4 braços ópticos com lentes colimadoras
for a in range(4):
    ang = a * PI / 2
    rot_br = Matrix.Rotation(ang, 3, 'Z')
    d_br = Vector((math.cos(ang), math.sin(ang), 0))
    tubo(bm, d_br * 0.06, d_br * 0.32, 0.014, 10)
    # Caixa da lente
    cil(bm, d_br * 0.32, 0.045, 0.03, d_br, lados=14)
    # Lente de quartzo
    cil(bmlen, d_br * 0.33, 0.038, 0.008, d_br, lados=14)
obj('carrossel_mecanica', bm, 'petroleo', carrossel)
obj('carrossel_lentes', bmlen, 'lente', carrossel)

# Antena helicoidal de telemetria no topo do mastro
antena = bpy.data.objects.new('antena_topo', None)
sc.collection.objects.link(antena)
antena.location = C + Vector((0, 0, ZR + 0.48))
bm = bmesh.new()
tubo(bm, Vector((0, 0, 0)), Vector((0, 0, 0.45)), 0.016, 12)
# Hélice de cobre em espiral em volta do mastro
helix_pts = []
for i in range(32):
    t_h = i / 31
    ang_h = t_h * 4 * PI
    r_h = 0.05
    helix_pts.append(Vector((r_h * math.cos(ang_h), r_h * math.sin(ang_h), 0.08 + t_h * 0.32)))
for p0, p1 in zip(helix_pts, helix_pts[1:]):
    tubo(bm, p0, p1, 0.004, 6)
# Esfera terminal no topo
curva(bm, Vector((0, 0, 0.46)), 0.025, 12)
obj('antena_topo_geo', bm, 'cobre', antena)

# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço fechado a 24 fps)
# Referências de emissão para animação harmônica
em_cristal = base3d.M['cristal_topo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_las = base3d.M['laser'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_campo = base3d.M['campo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
em_mod_led = base3d.M['led_ciano'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']

for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS                     # progresso 0..1 do ciclo
    fase = 2 * PI * t
    
    # 1. Carrossel óptico superior: rotação contínua e suave de 360° em Z
    carrossel.rotation_euler = Euler((0, 0, -fase), 'XYZ')
    carrossel.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Antena de telemetria: leve oscilação harmônica
    antena.rotation_euler = Euler((0.04 * math.sin(fase * 2), 0.04 * math.cos(fase * 2), 0.1 * math.sin(fase)), 'XYZ')
    antena.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Ventoinhas do radiador duplo: rotação ultra-rápida (6 voltas por ciclo)
    ventoinhas[0].rotation_euler = Euler((0, 0, fase * 6), 'XYZ')
    ventoinhas[1].rotation_euler = Euler((0, 0, -fase * 6), 'XYZ')
    ventoinhas[0].keyframe_insert('rotation_euler', frame=q)
    ventoinhas[1].keyframe_insert('rotation_euler', frame=q)
    
    # 4. Rotor do medidor de vazão de fluido: 4 voltas por ciclo
    rotor_fluxo.rotation_euler = Euler((0, fase * 4, 0), 'XYZ')
    rotor_fluxo.keyframe_insert('rotation_euler', frame=q)
    
    # 5. Roletes das esteiras sul e oeste girando
    for r_obj in roletes_s:
        r_obj.rotation_euler = Euler((fase * 3, 0, 0), 'XYZ')
        r_obj.keyframe_insert('rotation_euler', frame=q)
    for r_obj in roletes_o:
        r_obj.rotation_euler = Euler((0, fase * 3, 0), 'XYZ')
        r_obj.keyframe_insert('rotation_euler', frame=q)
        
    # 6. Comporta da boca sul: abre suavemente entre t=0.15 e 0.35, fecha entre 0.70 e 0.90
    if t < 0.15:
        z_comp = 0.0
    elif t < 0.35:
        s = (t - 0.15) / 0.20
        z_comp = 0.28 * (0.5 - 0.5 * math.cos(PI * s))
    elif t < 0.70:
        z_comp = 0.28
    elif t < 0.90:
        s = (t - 0.70) / 0.20
        z_comp = 0.28 * (0.5 + 0.5 * math.cos(PI * s))
    else:
        z_comp = 0.0
    comporta.location = Vector((0, 0, z_comp))
    comporta.keyframe_insert('location', frame=q)
    
    # 7. Gaveta de análise: desliza para fora entre 0.30 e 0.45, volta entre 0.55 e 0.70
    if t < 0.30:
        y_gav = 0.0
    elif t < 0.45:
        s = (t - 0.30) / 0.15
        y_gav = -0.38 * (0.5 - 0.5 * math.cos(PI * s))
    elif t < 0.55:
        y_gav = -0.38
    elif t < 0.70:
        s = (t - 0.55) / 0.15
        y_gav = -0.38 * (0.5 + 0.5 * math.cos(PI * s))
    else:
        y_gav = 0.0
    gaveta.location = Vector((0, y_gav, 0))
    gaveta.keyframe_insert('location', frame=q)
    
    # 8. Braço mecânico sul: cinemática de carregamento rápido sincronizada com a gaveta
    # Gira em Z para pegar na esteira (t ~ 0.25) e pôr na gaveta (t ~ 0.45)
    s_braco = 0.5 - 0.5 * math.cos(fase)
    ang_ombro = -0.45 + s_braco * 0.90
    ang_cot = 0.25 * math.sin(fase * 2)
    braco_base.rotation_euler = Euler((0, 0, ang_ombro), 'XYZ')
    braco_base.keyframe_insert('rotation_euler', frame=q)
    braco_garra.rotation_euler = Euler((ang_cot, 0, -ang_cot * 0.5), 'XYZ')
    braco_garra.keyframe_insert('rotation_euler', frame=q)

    # 8b. Pacote de pesquisa sul: esteira -> gaveta -> desintegração
    if t < 0.30:
        s_p = t / 0.30
        y_p = -1.45 + s_p * 0.70
        pacote.location = Vector((0.0, y_p, Z_EST + 0.025))
        pacote.scale = Vector((1.0, 1.0, 1.0))
    elif t < 0.45:
        s_p = (t - 0.30) / 0.15
        y_p = -0.75 + s_p * 0.37
        z_arc = 0.12 * math.sin(PI * s_p)
        pacote.location = Vector((0.0, y_p, Z_EST + 0.025 + z_arc))
        pacote.scale = Vector((1.0, 1.0, 1.0))
    elif t < 0.70:
        pacote.location = Vector((0.0, y_gav, HATCH[2] + 0.045))
        pacote.scale = Vector((1.0, 1.0, 1.0))
    else:
        s_p = (t - 0.70) / 0.25
        esc = max(0.001, 1.0 - s_p * 0.95)
        pacote.location = Vector((0.0, 0.0, HATCH[2] + 0.045))
        pacote.scale = Vector((esc, esc, esc))
    pacote.keyframe_insert('location', frame=q)
    pacote.keyframe_insert('scale', frame=q)

    # 8c. Amostra reagente na esteira oeste avançando em direção à bica
    s_o = (t * 2) % 1.0
    x_am = -1.45 + s_o * 0.75
    amostra_o.location = Vector((x_am, 0.0, Z_EST + 0.025))
    amostra_o.keyframe_insert('location', frame=q)
    
    # 9. Anel de plasma levitante na unidade de força: flutuação e rotação harmônica
    z_anel = 0.03 * math.sin(fase * 2)
    anel_forca.location = Vector((X_POT, Y_POT, 0.95 + z_anel))
    anel_forca.rotation_euler = Euler((0.05 * math.sin(fase), 0.05 * math.cos(fase), fase), 'XYZ')
    anel_forca.keyframe_insert('location', frame=q)
    anel_forca.keyframe_insert('rotation_euler', frame=q)
    
    # 10. Pulso de cristal e iluminação dos lasers internos
    pulso_c = 0.5 + 0.5 * math.sin(fase * 4)
    cristal_res.scale = Vector((1.0 + 0.05 * pulso_c, 1.0 + 0.05 * pulso_c, 1.0 + 0.08 * pulso_c))
    cristal_res.keyframe_insert('scale', frame=q)
    
    em_cristal.default_value = 2.0 + 4.0 * pulso_c
    em_cristal.keyframe_insert('default_value', frame=q)
    
    # Lasers mais intensos quando a gaveta está fechada (t > 0.75 ou t < 0.25)
    fator_laser = 1.0 if (t < 0.20 or t > 0.80) else 0.15
    em_las.default_value = 28.0 * fator_laser * (0.8 + 0.2 * math.sin(fase * 8))
    em_las.keyframe_insert('default_value', frame=q)
    luz_las_data.energy = 85.0 * fator_laser * (0.8 + 0.2 * math.sin(fase * 8))
    luz_las_data.keyframe_insert('energy', frame=q)
    
    # LEDs dos slots de módulo pulsando
    em_mod_led.default_value = 8.0 + 6.0 * (0.5 + 0.5 * math.sin(fase * 3))
    em_mod_led.keyframe_insert('default_value', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('EFEITO_chao', bm, 'chao')

# Luz Solar
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), 0, math.radians(-38))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.65

# Cycles GPU OptiX
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
sc.view_settings.exposure = -0.35

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

if modo == 'nada':
    # Apenas monta a cena e imprime a contagem de polígonos
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'LABORATORIO_2_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((300, 4.4, 0.85), (215, 4.2, 0.35), (120, 4.6, 0.15), (35, 4.0, 0.65))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt)), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'laboratorio_2_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up na boca sul / slots de módulos / cúpula
    sc.frame_set(int(0.40 * FPS) + 1)  # com a gaveta aberta e comporta levantada
    mirar((1.20, -1.85, 1.15), (0.05, -0.45, 0.55), 34)
    sc.render.filepath = os.path.join(AQUI, 'laboratorio_2_perto.png')
    bpy.ops.render.render(write_still=True)

print('LABORATORIO_2 ok')
