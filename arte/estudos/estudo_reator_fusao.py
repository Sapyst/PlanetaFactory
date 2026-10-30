"""Estudo isolado (fora do jogo): REATOR DE FUSÃO da IA, 3×3 tiles (lote 14, energia II).
Potência nominal: 30 MW. Tecnologia: 'fusao'. Consome água (fluido) e cristais carregados (itens) em reação termonuclear limpa.
Bocas no padrão do jogo:
- ITEM_ENT_S1: esteira sul de cristais carregados (x = 0,0, y = -1,50 m, z = 0,23 m)
- ITEM_SAI_N1: esteira norte de cartuchos descarregados de retenção (x = 0,0, y = +1,50 m, z = 0,23 m)
- FLUIDO_ENT_O1: tubulação oeste de água para moderação e ciclo térmico a z = 0,35 m (x = -1,50 m, y = 0,0)
- FLUIDO_SAI_L1: tubulação leste de vapor d'água superaquecido a z = 0,35 m (x = +1,50 m, y = 0,0)

Engenharia termonuclear e confinamento magnético Tokamak da IA:
- Base maciça de concreto armado 2,96 × 2,96 m com canaletas criogênicas de drenagem, bacias e chapas de aço xadrez.
- Câmara de vácuo toroidal colossal (Tokamak) em aço inoxidável e titânio escovado, com 8 bobinas magnéticas
  supercondutoras em forma de "D" (D-shaped coils) em cobre criogênico e carcaças de aço com tirantes de pré-tensão.
- Anel de plasma termonuclear no interior do toro: cordão de fusão azul-celeste e branco-azulado incandescente
  girando em alta velocidade, visível através de 4 janelas de quartzo espesso com grades de boro.
- Solenoide central de indução magnética erguendo-se no centro do toro com condutores axiais e anéis polarizadores.
- Dois injetores de feixe neutro (NBI) tangenciais para aquecimento e injeção de energia de plasma com linhas de alta tensão.
- Sistema de alimentação sul: câmara de injeção por canhão de indução eletromagnética recebendo cristais da esteira de roletes.
- Ejeção norte: bica de descarte de matrizes de contenção descarregadas conduzindo para a esteira norte de roletes.
- Circuito de fluido oeste e leste: bocais rígidos flangeados a 0,35 m de altura, trocador de calor casco-e-tubo gigante,
  bomba de circulação forçada e tubos isolados com mantas térmicas.

Peças animadas separadas:
- 'solenoide_anel': anel de focalização magnética superior do solenoide central oscilando e girando a 360° em Z.
- 'toro_plasma': cordão toroidal de plasma no interior do vaso girando continuamente em Z com ondulação harmônica.
- 'rotor_fluxo_o': rotor do fluxômetro de entrada de água oeste girando a 4 voltas por ciclo.
- 'rotor_fluxo_l': rotor do fluxômetro de vapor leste girando a 4 voltas por ciclo.
- 'injetor_eletromagnetico': bobinas lineares do canhão injetor sul com cascata luminosa de ativação.
- 'rolete_s0'..'s3', 'rolete_n0'..'n3': roletes de aço das esteiras sul e norte girando continuamente.

Uso: blender -b --python estudo_reator_fusao.py -- foto
     blender -b --python estudo_reator_fusao.py -- nada
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
Z_LAJE = 0.08
Z_TORO = 0.85                # altura do centro do toro de fusão
R_MAIOR_TORO = 0.62          # raio maior do toro (distância do centro ao eixo do tubo)
R_MENOR_TORO = 0.24          # raio do tubo da câmara de vácuo
Z_EST = 0.23                 # altura da esteira de itens (bocas sul e norte)
Z_CANO = 0.35                # altura do tubo de fluido (bocas oeste e leste)

# ------------------------------------------------------------------ utilidades de geometria
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

def toro(bm, centro, R, r, nR=36, nr=12, rot=Matrix.Identity(3)):
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

# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m

def vidro_mat():
    m = bpy.data.materials.new('VidroFusao')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.75, 0.90, 1.0, 1)
    b.inputs['Transmission Weight'].default_value = 0.96
    b.inputs['Roughness'].default_value = 0.03
    b.inputs['Alpha'].default_value = 0.32
    b.inputs['IOR'].default_value = 1.55
    return m

def plasma_mat():
    m = bpy.data.materials.new('PlasmaFusao')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.2, 0.7, 1.0, 1)
    b.inputs['Emission Color'].default_value = (0.4, 0.85, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 24.0
    return m

base3d.M.update({
    'titânio': mats.material('TitânioEscuro', (0.12, 0.13, 0.15), 0.9, 0.35, pintura=False, sujeira=0.6, escovado=True),
    'aco': mats.material('AçoEstrutural', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('CobreCriogenico', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'bronze': mats.material('Bronze', (0.55, 0.38, 0.18), 1.0, 0.35, pintura=False, sujeira=0.7),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'vidro': vidro_mat(),
    'plasma': plasma_mat(),
    'cristal_temp': luz_mat('CristalTempestade', (0.55, 0.15, 1.0), 8.0),
    'campo': luz_mat('CampoTokamak', (0.2, 0.8, 1.0), 10.0),
    'led_ciano': luz_mat('LedCiano', (0.1, 0.9, 0.95), 12.0),
})

# ------------------------------------------------------------------ LAJE E BASE DE CONCRETO (3x3 tiles)
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z_LAJE))
# Bacia de contenção central circular
cil(bm, Vector((0, 0, (Z_LAJE + 0.18) / 2)), 1.15, 0.18 - Z_LAJE, lados=24)
# Sapatas de apoio para as 8 bobinas em D
for a in range(8):
    ang = a * 2 * PI / 8
    d_sap = Vector((math.cos(ang), math.sin(ang), 0))
    p_sap = d_sap * 0.95 + Vector((0, 0, 0.18))
    caixa(bm, p_sap, (0.18, 0.14, 0.10), Matrix.Rotation(ang, 3, 'Z'))
obj('laje_concreto', bm, 'concreto')

# Demarcações de perigo no piso
bm = bmesh.new()
for x in (-0.26, 0.26):
    caixa_de(bm, (x - 0.025, -1.48, 0.08), (x + 0.025, -0.75, 0.082))
    caixa_de(bm, (x - 0.025, 0.75, 0.08), (x + 0.025, 1.48, 0.082))
for y in (-0.26, 0.26):
    caixa_de(bm, (-1.48, y - 0.025, 0.08), (-0.75, y + 0.025, 0.082))
    caixa_de(bm, (0.75, y - 0.025, 0.08), (1.48, y + 0.025, 0.082))
obj('faixas_perigo', bm, 'listras')

# ------------------------------------------------------------------ CÂMARA DE VÁCUO TOROIDAL E BOBINAS EM "D" (TOKAMAK)
bm_toro, bm_vidro = bmesh.new(), bmesh.new()

# Vaso toroidal de vácuo em titânio escuro
toro(bm_toro, Vector((0, 0, Z_TORO)), R_MAIOR_TORO, R_MENOR_TORO, nR=36, nr=14)

# 4 Janelas de quartzo espesso para diagnóstico e inspeção do plasma
for ang in (PI/4, 3*PI/4, 5*PI/4, 7*PI/4):
    rot_j = Matrix.Rotation(ang, 3, 'Z')
    d_j = Vector((math.cos(ang), math.sin(ang), 0))
    p_jan = d_j * (R_MAIOR_TORO + R_MENOR_TORO * 0.85) + Vector((0, 0, Z_TORO))
    cil(bm_vidro, p_jan, 0.10, 0.06, d_j, lados=14)
    # Aro parafusado da janela
    cil(bm_toro, p_jan + d_j * 0.015, 0.12, 0.03, d_j, lados=14)

obj('camara_vacuo_toro', bm_toro, 'titânio')
obj('janelas_inspecao_plasma', bm_vidro, 'vidro')

# 8 Bobinas magnéticas supercondutoras em forma de "D" (D-shaped coils)
bm_bobinas, bm_cobre = bmesh.new(), bmesh.new()
for a in range(8):
    ang = a * 2 * PI / 8
    rot_bob = Matrix.Rotation(ang, 3, 'Z')
    d_b = Vector((math.cos(ang), math.sin(ang), 0))
    
    # Perfil em D: trecho reto perto do solenoide central, e arco circular externo
    # Trecho reto vertical interno (r ~ 0.28 m, z de 0.35 a 1.35 m)
    p_int0 = d_b * 0.28 + Vector((0, 0, 0.35))
    p_int1 = d_b * 0.28 + Vector((0, 0, 1.35))
    tubo(bm_bobinas, p_int0, p_int1, 0.045, 12)
    tubo(bm_cobre, p_int0, p_int1, 0.025, 8)
    
    # Arco externo passando por fora do toro (r ~ 0.98 m, z = 0.85 m)
    p_ext = d_b * 0.98 + Vector((0, 0, Z_TORO))
    tubo(bm_bobinas, p_int1, p_ext + Vector((0, 0, 0.25)), 0.045, 12)
    tubo(bm_bobinas, p_ext + Vector((0, 0, 0.25)), p_ext - Vector((0, 0, 0.25)), 0.045, 12)
    tubo(bm_bobinas, p_ext - Vector((0, 0, 0.25)), p_int0, 0.045, 12)
    # Condutores internos em cobre criogênico
    tubo(bm_cobre, p_int1, p_ext, 0.025, 8)
    tubo(bm_cobre, p_ext, p_int0, 0.025, 8)
    
    # Tirantes de reforço mecânico ligando as bobinas
    ang_prox = (a + 1) * 2 * PI / 8
    d_prox = Vector((math.cos(ang_prox), math.sin(ang_prox), 0))
    tubo(bm_bobinas, p_ext, d_prox * 0.98 + Vector((0, 0, Z_TORO)), 0.018, 8)

obj('bobinas_d_carcacaprotecao', bm_bobinas, 'aco')
obj('bobinas_d_cobre_supercondutor', bm_cobre, 'cobre')

# ------------------------------------------------------------------ SOLENOIDE CENTRAL DE INDUÇÃO E ANEL SUPERIOR
bm_sol = bmesh.new()
# Cilindro central do solenoide
cil(bm_sol, Vector((0, 0, Z_TORO)), 0.22, 1.40, Z_VEC, lados=18)
# Aletas de blindagem e barramentos de indução
for iz in range(8):
    z_sol = 0.35 + iz * 0.15
    cil(bm_sol, Vector((0, 0, z_sol)), 0.24, 0.03, Z_VEC, lados=18)
obj('solenoide_central', bm_sol, 'titânio')

# Anel polarizador magnético superior giratório no topo do solenoide
anel_sol = bpy.data.objects.new('solenoide_anel', None)
sc.collection.objects.link(anel_sol)
anel_sol.location = Vector((0, 0, Z_TORO + 0.72))
bm_as = bmesh.new()
toro(bm_as, Vector((0, 0, 0)), 0.32, 0.025, nR=24, nr=8)
for a in range(4):
    ang = a * PI / 2
    d_a = Vector((math.cos(ang), math.sin(ang), 0))
    cil(bm_as, d_a * 0.32, 0.035, 0.05, Z_VEC, lados=8)
obj('solenoide_anel_mesh', bm_as, 'campo', anel_sol)

# ------------------------------------------------------------------ CORDÃO TOROIDAL DE PLASMA DE FUSÃO (INTERIOR)
toro_plasma = bpy.data.objects.new('toro_plasma', None)
sc.collection.objects.link(toro_plasma)
toro_plasma.location = Vector((0, 0, Z_TORO))
bm_tp = bmesh.new()
# Toro de plasma incandescente brilhante
toro(bm_tp, Vector((0, 0, 0)), R_MAIOR_TORO, 0.09, nR=32, nr=12)
obj('toro_plasma_mesh', bm_tp, 'plasma', toro_plasma)

# Luz pontual omnidirecional de plasma no centro do reator
luz_plasma = bpy.data.lights.new('LuzFusao', 'POINT')
luz_plasma.energy = 150.0
luz_plasma.color = (0.45, 0.85, 1.0)
luz_plasma.shadow_soft_size = 0.12
luz_plasma_o = bpy.data.objects.new('EFEITO_LuzFusao', luz_plasma)
sc.collection.objects.link(luz_plasma_o)
luz_plasma_o.location = Vector((0, 0, Z_TORO))

# ------------------------------------------------------------------ INJETORES DE FEIXE NEUTRO (NBI)
bm_nbi = bmesh.new()
# Dois canhões NBI tangenciais injetando no toro
for ang_nbi in (PI/4, 5*PI/4):
    rot_n = Matrix.Rotation(ang_nbi, 3, 'Z')
    d_n = Vector((math.cos(ang_nbi), math.sin(ang_nbi), 0))
    p_orig = d_n * 1.15 + Vector((0, 0, Z_TORO + 0.15))
    p_alvo = d_n * 0.65 + Vector((0, 0, Z_TORO))
    tubo(bm_nbi, p_orig, p_alvo, 0.06, 14)
    # Caixa de alimentação do NBI
    caixa(bm_nbi, p_orig + d_n * 0.12, (0.16, 0.22, 0.25), rot_n)
    # Isoladores elétricos
    for iz in range(3):
        cil(bm_nbi, p_orig + d_n * 0.12 + Vector((0, 0, 0.16 + iz * 0.035)), 0.035, 0.025, lados=10)
obj('injetores_nbi', bm_nbi, 'grafite')

# ------------------------------------------------------------------ BOCA SUL (ITEM_ENT_S1): Esteira de cristais e canhão eletromagnético
# Boca a x = 0.0, y = -1.50 m, z = 0.23 m
bm_calhas_s, bm_inj_bob = bmesh.new(), bmesh.new()
caixa_de(bm_calhas_s, (-0.24, -1.50, 0.08), (-0.20, -0.65, Z_EST + 0.04))
caixa_de(bm_calhas_s, (0.20, -1.50, 0.08), (0.24, -0.65, Z_EST + 0.04))
# Eclusa hermética de injeção linear
caixa_de(bm_calhas_s, (-0.28, -0.75, Z_EST - 0.05), (0.28, -0.42, 0.60))

# Bobinas magnéticas lineares de aceleração do canhão de injeção
for j_b in range(4):
    y_b = -0.70 + j_b * 0.08
    casca(bm_inj_bob, (0, y_b, 0), 0.14, 0.10, Z_EST - 0.02, Z_EST + 0.08, 16)

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
obj('esteira_sul_calhas', bm_calhas_s, 'grafite')
obj('injetor_bobinas_lineares', bm_inj_bob, 'cobre')

# Cristal carregado em trânsito pela esteira sul
cristal_carga = bpy.data.objects.new('cristal_carga', None)
sc.collection.objects.link(cristal_carga)
bm_cc = bmesh.new()
hexa(bm_cc, Vector((0, 0, 0.035)), 0.04, -0.06, 0.06, ponta=0.03)
obj('cristal_carga_mesh', bm_cc, 'cristal_temp', cristal_carga)

# ------------------------------------------------------------------ BOCA NORTE (ITEM_SAI_N1): Esteira de ejeção de cartuchos
# Boca a x = 0.0, y = +1.50 m, z = 0.23 m
bm_calhas_n = bmesh.new()
caixa_de(bm_calhas_n, (-0.24, 0.65, 0.08), (-0.20, 1.50, Z_EST + 0.04))
caixa_de(bm_calhas_n, (0.20, 0.65, 0.08), (0.24, 1.50, Z_EST + 0.04))
# Bica inclinada de extração hermética
caixa_de(bm_calhas_n, (-0.26, 0.45, Z_EST - 0.02), (0.26, 0.72, 0.55))

# Roletes da esteira norte
roletes_n = []
for i in range(4):
    y_rn = 0.75 + i * 0.22
    r_obj = bpy.data.objects.new(f'rolete_n{i}', None)
    sc.collection.objects.link(r_obj)
    r_obj.location = Vector((0, y_rn, Z_EST))
    bm_rn = bmesh.new()
    cil(bm_rn, Vector((0, 0, 0)), 0.022, 0.38, Vector((1, 0, 0)), lados=14)
    obj(f'rolete_n{i}_mesh', bm_rn, 'aco', r_obj)
    roletes_n.append(r_obj)
obj('esteira_norte_calhas', bm_calhas_n, 'grafite')

# Cartucho de descarte saindo pela esteira norte
cartucho_descarte = bpy.data.objects.new('cartucho_descarte', None)
sc.collection.objects.link(cartucho_descarte)
bm_cd = bmesh.new()
cil(bm_cd, Vector((0, 0, 0.03)), 0.045, 0.06, Vector((0, 1, 0)), lados=12)
obj('cartucho_descarte_mesh', bm_cd, 'titânio', cartucho_descarte)

# ------------------------------------------------------------------ BOCA OESTE (FLUIDO_ENT_O1): Entrada de água / refrigeração
# Boca a x = -1.50 m, y = 0.0 m, z = 0.35 m
bm_cano_o, bf_o = bmesh.new(), bmesh.new()
tubo(bf_o, Vector((-1.50, 0, Z_CANO)), Vector((-1.44, 0, Z_CANO)), 0.075, 16)
tubo(bm_cano_o, Vector((-1.44, 0, Z_CANO)), Vector((-1.05, 0, Z_CANO)), 0.045, 16)
cil(bm_cano_o, Vector((-1.25, 0, Z_CANO)), 0.07, 0.06, Vector((0, 1, 0)), lados=16)
cil(bf_o, Vector((-1.25, 0.032, Z_CANO)), 0.055, 0.008, Vector((0, 1, 0)), lados=16)

# Rotor do medidor de fluxo oeste
rotor_fluxo_o = bpy.data.objects.new('rotor_fluxo_o', None)
sc.collection.objects.link(rotor_fluxo_o)
rotor_fluxo_o.location = Vector((-1.25, 0.025, Z_CANO))
bm_ro = bmesh.new()
cil(bm_ro, Vector((0, 0, 0)), 0.015, 0.012, Vector((0, 1, 0)), lados=8)
for ang in (0, PI/2, PI, 3*PI/2):
    rot_p = Matrix.Rotation(ang, 3, 'Y')
    caixa(bm_ro, rot_p @ Vector((0.028, 0, 0)), (0.026, 0.006, 0.004), rot_p)
obj('rotor_fluxo_o_pas', bm_ro, 'bronze', rotor_fluxo_o)

cano(bm_cano_o, bf_o, [Vector((-1.05, 0, Z_CANO)), Vector((-0.85, 0, Z_CANO)),
                       Vector((-0.85, 0.32, Z_CANO)), Vector((-0.65, 0.32, 0.65))], 0.038)
obj('tubo_agua_oeste', bm_cano_o, 'aco')
obj('tubo_agua_flanges', bf_o, 'latao')

# ------------------------------------------------------------------ BOCA LESTE (FLUIDO_SAI_L1): Saída de vapor / ciclo térmico
# Boca a x = +1.50 m, y = 0.0 m, z = 0.35 m
bm_cano_l, bf_l = bmesh.new(), bmesh.new()
tubo(bf_l, Vector((1.50, 0, Z_CANO)), Vector((1.44, 0, Z_CANO)), 0.075, 16)
tubo(bm_cano_l, Vector((1.44, 0, Z_CANO)), Vector((1.05, 0, Z_CANO)), 0.045, 16)
cil(bm_cano_l, Vector((1.25, 0, Z_CANO)), 0.07, 0.06, Vector((0, 1, 0)), lados=16)
cil(bf_l, Vector((1.25, 0.032, Z_CANO)), 0.055, 0.008, Vector((0, 1, 0)), lados=16)

# Rotor do medidor de fluxo leste
rotor_fluxo_l = bpy.data.objects.new('rotor_fluxo_l', None)
sc.collection.objects.link(rotor_fluxo_l)
rotor_fluxo_l.location = Vector((1.25, 0.025, Z_CANO))
bm_rl = bmesh.new()
cil(bm_rl, Vector((0, 0, 0)), 0.015, 0.012, Vector((0, 1, 0)), lados=8)
for ang in (0, PI/2, PI, 3*PI/2):
    rot_p = Matrix.Rotation(ang, 3, 'Y')
    caixa(bm_rl, rot_p @ Vector((0.028, 0, 0)), (0.026, 0.006, 0.004), rot_p)
obj('rotor_fluxo_l_pas', bm_rl, 'bronze', rotor_fluxo_l)

cano(bm_cano_l, bf_l, [Vector((1.05, 0, Z_CANO)), Vector((0.85, 0, Z_CANO)),
                       Vector((0.85, -0.32, Z_CANO)), Vector((0.65, -0.32, 0.65))], 0.038)
obj('tubo_vapor_leste', bm_cano_l, 'aco')
obj('tubo_vapor_flanges', bf_l, 'latao')

# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço fechado a 24 fps)
em_plasma = base3d.M['plasma'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']

for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    t = (q - 1) / QUADROS                     # progresso 0..1 do ciclo
    fase = 2 * PI * t
    
    # 1. Rotação do cordão de plasma no Tokamak: 4 voltas por ciclo
    toro_plasma.rotation_euler = Euler((0, 0, fase * 4), 'XYZ')
    toro_plasma.keyframe_insert('rotation_euler', frame=q)
    
    # Pulso harmônico de luminescência e escala do plasma
    pulso_p = 0.5 + 0.5 * math.sin(fase * 4)
    toro_plasma.scale = Vector((1.0 + 0.04 * pulso_p, 1.0 + 0.04 * pulso_p, 1.0 + 0.06 * pulso_p))
    toro_plasma.keyframe_insert('scale', frame=q)
    em_plasma.default_value = 20.0 + 15.0 * pulso_p
    em_plasma.keyframe_insert('default_value', frame=q)
    luz_plasma.energy = 120.0 + 70.0 * pulso_p
    luz_plasma.keyframe_insert('energy', frame=q)
    
    # 2. Anel de indução do solenoide central girando a 360° em Z
    anel_sol.rotation_euler = Euler((0, 0, -fase), 'XYZ')
    anel_sol.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Rotres dos fluxômetros leste e oeste girando
    rotor_fluxo_o.rotation_euler = Euler((0, fase * 4, 0), 'XYZ')
    rotor_fluxo_l.rotation_euler = Euler((0, fase * 4, 0), 'XYZ')
    rotor_fluxo_o.keyframe_insert('rotation_euler', frame=q)
    rotor_fluxo_l.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Roletes das esteiras sul e norte girando continuamente
    for r_obj in roletes_s:
        r_obj.rotation_euler = Euler((fase * 3, 0, 0), 'XYZ')
        r_obj.keyframe_insert('rotation_euler', frame=q)
    for r_obj in roletes_n:
        r_obj.rotation_euler = Euler((fase * 3, 0, 0), 'XYZ')
        r_obj.keyframe_insert('rotation_euler', frame=q)
        
    # 5. Entrada de cristal carregado na esteira sul
    if t < 0.50:
        s_c = t / 0.50
        y_c = -1.45 + s_c * 0.70
        cristal_carga.location = Vector((0.0, y_c, Z_EST + 0.025))
        cristal_carga.scale = Vector((1.0, 1.0, 1.0))
    elif t < 0.75:
        # Disparo no canhão de indução
        s_c = (t - 0.50) / 0.25
        y_c = -0.75 + s_c * 0.40
        cristal_carga.location = Vector((0.0, y_c, Z_EST + 0.025))
        cristal_carga.scale = Vector((1.0, 1.0, 1.0))
    else:
        # Fundindo no toro de plasma
        s_c = (t - 0.75) / 0.25
        esc_c = max(0.001, 1.0 - s_c * 0.98)
        cristal_carga.location = Vector((0.0, -0.35, Z_EST + 0.025))
        cristal_carga.scale = Vector((esc_c, esc_c, esc_c))
    cristal_carga.keyframe_insert('location', frame=q)
    cristal_carga.keyframe_insert('scale', frame=q)
    
    # 6. Ejeção de cartucho descarte na esteira norte
    s_d = (t * 2) % 1.0
    y_d = 0.70 + s_d * 0.75
    cartucho_descarte.location = Vector((0.0, y_d, Z_EST + 0.025))
    cartucho_descarte.keyframe_insert('location', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('EFEITO_chao', bm, 'chao')

# Luz Solar
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
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'REATOR_FUSAO_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((300, 4.2, 0.35), (215, 4.0, 0.60), (120, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'reator_fusao_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up nas bobinas em D, janela do toro com plasma de fusão e canhão sul
    sc.frame_set(int(0.60 * FPS) + 1)
    mirar((1.25, -1.85, 1.35), (0.15, -0.40, 0.80), 34)
    sc.render.filepath = os.path.join(AQUI, 'reator_fusao_perto.png')
    bpy.ops.render.render(write_still=True)

print('REATOR_FUSAO ok')
