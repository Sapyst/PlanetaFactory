"""Estudo isolado (fora do jogo): POSTE ALTO da IA, 1×1 tile (lote 13, energia I).
Alcance de transmissão: fio de 30 m (ligação local de 3 m).
Função: Torre metálica treliçada de transmissão de alta tensão em longas distâncias.
Equipada com ancoragens de cabos de grande vão, cadeias de isoladores de suspensão em disco,
anéis corona anti-arco, para-raios de óxido de zinco, fita de aterramento pesada e
nó de ressonância eletrostática da IA no topo para supressão harmônica de perdas em 30 metros.

Mecânica industrial pesada:
- Bloco de concreto armado 0,84 × 0,84 × 0,35 m com chanfros, 4 sapatas de aço fundido e chumbadores duplos.
- Torre treliçada quadrangular afilada (altura Z = 4,95 m) em cantoneiras de aço galvanizado oxidado,
  cruzetas diagonais de contraventamento, chapas de junção rebitadas e estêncil de alta tensão.
- Duas cruzetas horizontais em balanço (superior a Z = 4,40 m e inferior a Z = 3,75 m) com mãos-francesas.
- 4 conjuntos de cadeias de discos isoladores de suspensão (5 discos por cadeia) em cerâmica vitrificada
  com anéis corona toroidais em alumínio e grampos de ancoragem de tração pesada.
- Cabos condutores de alta tensão em catenária com alças de jumper de transposição.
- Para-raios tipo ponta de Franklin no ápice com anel de ressonância quântica da IA ('anel_ressonancia') e LED de sincronia.
- Caixa de telemetria e chave seccionadora na perna da torre a Z = 1,40 m com cabo blindado descendo ao terra.
- Chapa de remendo em primer vermelho rebitada sobre um dos montantes da torre.
- Animação em laço de 96 quadros (4 s a 24 qps): anel de ressonância superior girando e pulsando campo violeta,
  faíscas estocásticas de corona nos anéis de descarga, cabos condutores oscilando suavemente ao vento
  e estrobo de balizamento aéreo piscando no topo da torre.

Uso: blender -b --python estudo_poste_alto.py -- foto
     blender -b --python estudo_poste_alto.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, cil, tubo, viga, bezier, mangueira, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(1301)
Z = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades de modelagem
def suavizar(o, tudo=False):
    for pg in o.data.polygons:
        pg.use_smooth = tudo or (len(pg.vertices) == 4)
    return o


def curva_cotovelo(bm, p, r, lados=8):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=4, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano_rigido(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 10)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.08:
            for c in (a + u * 0.03, b - u * 0.03):
                tubo(bf, c - u * 0.005, c + u * 0.005, r * 1.5, 10)
    for c in pts[1:-1]:
        curva_cotovelo(bm, c, r, 10)


def toro(bm, centro, R, r, nR=24, nr=6, rot=Matrix.Identity(3)):
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = rot @ Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + rot @ Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def hexa_cristal(bm, c, r, h, ponta_sup=0.0, ponta_inf=0.0):
    c = Vector(c)
    z0, z1 = c.z - h / 2, c.z + h / 2
    vs0 = [bm.verts.new((c.x + r * math.cos(k * PI / 3), c.y + r * math.sin(k * PI / 3), z0)) for k in range(6)]
    vs1 = [bm.verts.new((c.x + r * math.cos(k * PI / 3), c.y + r * math.sin(k * PI / 3), z1)) for k in range(6)]
    if ponta_inf > 0:
        vp0 = bm.verts.new((c.x, c.y, z0 - ponta_inf))
        for k in range(6):
            bm.faces.new((vs0[(k + 1) % 6], vs0[k], vp0))
    else:
        bm.faces.new(list(reversed(vs0)))
    if ponta_sup > 0:
        vp1 = bm.verts.new((c.x, c.y, z1 + ponta_sup))
        for k in range(6):
            bm.faces.new((vs1[k], vs1[(k + 1) % 6], vp1))
    else:
        bm.faces.new(vs1)
    for k in range(6):
        bm.faces.new((vs0[k], vs0[(k + 1) % 6], vs1[(k + 1) % 6], vs1[k]))


# ------------------------------------------------------------------ MATERIAIS
M = base3d.M
M['concreto'] = mats.material('ConcretoBase', (0.34, 0.33, 0.31), 0.05, 0.90, pintura=False, ferrugem=0.10, sujeira=0.80)
M['aco_gasto'] = mats.material('AcoTorre', (0.38, 0.39, 0.40), 0.85, 0.38, pintura=False, ferrugem=0.45, sujeira=0.60, escovado=True)
M['aco_escuro'] = mats.material('AcoSapatas', (0.16, 0.16, 0.17), 0.88, 0.50, pintura=False, ferrugem=0.55, sujeira=0.70)
M['chassi_amarelo'] = mats.material('ChassiAmarelo', (0.68, 0.46, 0.08), 0.15, 0.45, pintura=True, ferrugem=0.35, sujeira=0.65, desgaste=0.75)
M['remendo_primer'] = mats.material('RemendoPrimer', (0.42, 0.16, 0.12), 0.10, 0.65, pintura=True, ferrugem=0.20, sujeira=0.40)
M['cobre'] = mats.material('CobreCondutor', (0.78, 0.40, 0.22), 0.92, 0.30, pintura=False, ferrugem=0.10, sujeira=0.45)
M['ceramica_verde'] = mats.material('CeramicaIsolador', (0.25, 0.45, 0.40), 0.10, 0.18, pintura=False, ferrugem=0.0, sujeira=0.30)
M['aluminio_corona'] = mats.material('AluminioCorona', (0.80, 0.82, 0.85), 0.95, 0.20, pintura=False, ferrugem=0.05, sujeira=0.25)
M['listras'] = base3d.listras_mat()
M['oleo'] = mats.material('OleoSujeira', (0.02, 0.02, 0.01), 0.20, 0.15, pintura=False, ferrugem=0.0, sujeira=0.95)
M['chao'] = mats.material('Chao', (0.28, 0.27, 0.25), 0.0, 0.92, sujeira=0.35, desgaste=0.0)

# Emissões
def mat_emissao(nome, cor, forca=5.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*cor, 1.0)
    bsdf.inputs['Emission Color'].default_value = (*cor, 1.0)
    bsdf.inputs['Emission Strength'].default_value = forca
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m

M['cristal_no'] = mat_emissao('NoIA_Violeta', (0.45, 0.20, 1.0), 6.5)
M['arco_corona'] = mat_emissao('ArcoCorona', (0.35, 0.75, 1.0), 12.0)
M['estrobo'] = mat_emissao('EstroboAereo', (1.0, 0.2, 0.1), 8.0)

# ==============================================================================
# 1. BLOCO DE FUNDAÇÃO 1×1 (0,84 × 0,84 × 0,25 m) COM SAPATAS E CHUMBADORES
# ==============================================================================
bm_con = bmesh.new()
bm_aco = bmesh.new()
bm_lis = bmesh.new()

H_BASE = 0.25
caixa(bm_con, (0, 0, H_BASE * 0.5), (0.84, 0.84, H_BASE))

# Cantos chanfrados com listras de perigo
for cx, cy in ((-0.41, 0), (0.41, 0), (0, -0.41), (0, 0.41)):
    caixa(bm_lis, (cx, cy, H_BASE * 0.5), (0.02 if cx != 0 else 0.70, 0.70 if cx != 0 else 0.02, H_BASE * 0.75))

# 4 sapatas de aço fundido com placas de base e chumbadores duplos
R_SAP = 0.32
pos_pernas_base = [
    Vector((-R_SAP, -R_SAP, H_BASE)),
    Vector((R_SAP, -R_SAP, H_BASE)),
    Vector((R_SAP, R_SAP, H_BASE)),
    Vector((-R_SAP, R_SAP, H_BASE))
]

for pb in pos_pernas_base:
    caixa(bm_aco, pb + Vector((0, 0, 0.02)), (0.16, 0.16, 0.04))
    for bx in (-0.05, 0.05):
        for by in (-0.05, 0.05):
            tubo(bm_aco, pb + Vector((bx, by, 0.02)), pb + Vector((bx, by, 0.07)), 0.012, 6)

# Barra chata de aterramento em cobre correndo até a haste fincada no chão
cano_rigido(bm_aco, bm_aco, [(-R_SAP, -R_SAP, H_BASE + 0.02), (-0.44, -0.44, 0.05), (-0.46, -0.46, -0.05)], 0.010)

# ==============================================================================
# 2. TORRE TRELIÇADA QUADRANGULAR AFILADA (ALTURA TOTAL Z = 4,95 m)
# ==============================================================================
Z_TOPO = 4.95
R_TOPO = 0.10

pos_pernas_topo = [
    Vector((-R_TOPO, -R_TOPO, Z_TOPO)),
    Vector((R_TOPO, -R_TOPO, Z_TOPO)),
    Vector((R_TOPO, R_TOPO, Z_TOPO)),
    Vector((-R_TOPO, R_TOPO, Z_TOPO))
]

# 4 montantes principais de cantoneira de aço
for pb, pt in zip(pos_pernas_base, pos_pernas_topo):
    tubo(bm_aco, pb + Vector((0, 0, 0.03)), pt, 0.026, 8)

# Níveis de travessas horizontais e cruzetas X de contraventamento
N_NIVEIS = 8
alturas_niveis = [H_BASE + (Z_TOPO - H_BASE) * (i / float(N_NIVEIS)) for i in range(1, N_NIVEIS + 1)]

for iniv, z_niv in enumerate(alturas_niveis):
    t_niv = (z_niv - H_BASE) / (Z_TOPO - H_BASE)
    r_niv = R_SAP * (1.0 - t_niv) + R_TOPO * t_niv
    # Travessas horizontais nos 4 lados
    pts_n = [
        Vector((-r_niv, -r_niv, z_niv)),
        Vector((r_niv, -r_niv, z_niv)),
        Vector((r_niv, r_niv, z_niv)),
        Vector((-r_niv, r_niv, z_niv))
    ]
    for k in range(4):
        p_a, p_b = pts_n[k], pts_n[(k + 1) % 4]
        viga(bm_aco, p_a, p_b, 0.022)

    # Cruzetas X no vão entre este nível e o anterior
    if iniv > 0:
        z_ant = alturas_niveis[iniv - 1]
        t_ant = (z_ant - H_BASE) / (Z_TOPO - H_BASE)
        r_ant = R_SAP * (1.0 - t_ant) + R_TOPO * t_ant
        pts_ant = [
            Vector((-r_ant, -r_ant, z_ant)),
            Vector((r_ant, -r_ant, z_ant)),
            Vector((r_ant, r_ant, z_ant)),
            Vector((-r_ant, r_ant, z_ant))
        ]
        for k in range(4):
            k1 = (k + 1) % 4
            tubo(bm_aco, pts_ant[k], pts_n[k1], 0.010, 5)
            tubo(bm_aco, pts_ant[k1], pts_n[k], 0.010, 5)

# Chapa de remendo em primer vermelho rebitada no montante inferior sudoeste
bm_rem = bmesh.new()
p_rem = pos_pernas_base[0] + Vector((0.02, 0.02, 0.65))
caixa(bm_rem, p_rem, (0.012, 0.14, 0.26))
for dz_r in (-0.08, 0.0, 0.08):
    tubo(bm_aco, p_rem + Vector((-0.01, 0, dz_r)), p_rem + Vector((0.02, 0, dz_r)), 0.006, 6)

# Degraus para manutenção robótica subindo pela perna sudeste
for ist in range(12):
    zs = H_BASE + 0.35 + ist * 0.32
    ts = (zs - H_BASE) / (Z_TOPO - H_BASE)
    rs = R_SAP * (1.0 - ts) + R_TOPO * ts
    tubo(bm_aco, (rs + 0.01, -rs, zs), (rs + 0.08, -rs, zs), 0.008, 6)

# ==============================================================================
# 3. CRUZETAS DUPLAS DE ALTA TENSÃO E CADEIAS DE ISOLADORES EM DISCO
# ==============================================================================
bm_cer = bmesh.new()
bm_cor = bmesh.new()
bm_cob = bmesh.new()

# Nível 1: Cruzeta Inferior a Z = 3.75 m (comprimento 1.40 m)
# Nível 2: Cruzeta Superior a Z = 4.40 m (comprimento 1.10 m)
cruzetas_info = [
    (3.75, 0.70),  # z, metade da envergadura em X
    (4.40, 0.55),
]

pontos_fixacao_cabos = []

for z_cruz, span_x in cruzetas_info:
    # Viga mestra da cruzeta cortando a torre no eixo X
    viga(bm_aco, Vector((-span_x, 0, z_cruz)), Vector((span_x, 0, z_cruz)), 0.045)
    # Mãos-francesas diagonais sustentando as pontas da cruzeta
    viga(bm_aco, Vector((-span_x * 0.85, 0, z_cruz - 0.02)), Vector((-0.12, 0, z_cruz - 0.40)), 0.028)
    viga(bm_aco, Vector((span_x * 0.85, 0, z_cruz - 0.02)), Vector((0.12, 0, z_cruz - 0.40)), 0.028)

    # Em cada extremidade da cruzeta: cadeia vertical de 5 discos isoladores
    for lado in (-1, 1):
        x_iso = lado * (span_x - 0.05)
        p_topo_iso = Vector((x_iso, 0, z_cruz))
        p_base_iso = Vector((x_iso, 0, z_cruz - 0.48))
        pontos_fixacao_cabos.append(p_base_iso)

        # Haste central da cadeia
        tubo(bm_aco, p_topo_iso, p_base_iso, 0.010, 8)

        # 5 discos cerâmicos com formato de saia de alta tensão
        for idisc in range(5):
            zd = z_cruz - 0.08 - idisc * 0.08
            cil(bm_cer, (x_iso, 0, zd), 0.075, 0.025, lados=10)

        # Anel corona toroidal em alumínio na ponta inferior da cadeia
        toro(bm_cor, (x_iso, 0, z_cruz - 0.46), 0.09, 0.012, nR=16, nr=4)

        # Grampo de ancoragem de tração pesado
        caixa(bm_aco, (x_iso, 0, z_cruz - 0.50), (0.05, 0.12, 0.06))

# Cabos condutores de alta tensão chegando do sul (y = -0.50) e saindo ao norte (y = +0.50)
for p_cabo in pontos_fixacao_cabos:
    # Cabo sul (catenária suave descendo)
    pts_s = [
        Vector((p_cabo.x, -0.48, p_cabo.z - 0.15)),
        Vector((p_cabo.x, -0.25, p_cabo.z - 0.08)),
        Vector((p_cabo.x, 0.0, p_cabo.z - 0.02))
    ]
    cano_rigido(bm_cob, bm_aco, pts_s, 0.014, flange=False)

    # Cabo norte
    pts_n = [
        Vector((p_cabo.x, 0.0, p_cabo.z - 0.02)),
        Vector((p_cabo.x, 0.25, p_cabo.z - 0.08)),
        Vector((p_cabo.x, 0.48, p_cabo.z - 0.15))
    ]
    cano_rigido(bm_cob, bm_aco, pts_n, 0.014, flange=False)

    # Alça de jumper de transposição em arco semicircular sob a cruzeta
    pts_j = bezier(
        Vector((p_cabo.x, -0.06, p_cabo.z - 0.04)),
        Vector((p_cabo.x + (0.08 if p_cabo.x > 0 else -0.08), -0.02, p_cabo.z - 0.20)),
        Vector((p_cabo.x + (0.08 if p_cabo.x > 0 else -0.08), 0.02, p_cabo.z - 0.20)),
        Vector((p_cabo.x, 0.06, p_cabo.z - 0.04)),
        8
    )
    cano_rigido(bm_cob, bm_aco, pts_j, 0.010, flange=False)

# ==============================================================================
# 4. TELEMETRIA E CAIXA DE CHAVE SECCIONADORA (Z = 1.40 m)
# ==============================================================================
bm_cha = bmesh.new()
caixa(bm_cha, (-0.22, 0.0, 1.45), (0.16, 0.24, 0.28))
# Tampa com dobradiças e trava
caixa(bm_aco, (-0.30, 0.0, 1.45), (0.015, 0.22, 0.26))
tubo(bm_aco, (-0.30, -0.10, 1.45), (-0.30, -0.10, 1.55), 0.008, 6)
# Eletroduto galvanizado subindo pela torre
cano_rigido(bm_aco, bm_aco, [(-0.22, 0.0, 1.60), (-0.14, 0.0, 2.20), (-0.08, 0.0, 3.60)], 0.012)
# Eletroduto descendo para a laje
cano_rigido(bm_aco, bm_aco, [(-0.22, 0.0, 1.30), (-0.22, 0.0, 0.45), (-0.28, 0.0, 0.25)], 0.014)

# ==============================================================================
# CRIAÇÃO DOS OBJETOS ESTÁTICOS
# ==============================================================================
o_con = obj('base_concreto', bm_con, 'concreto')
suavizar(o_con)

o_aco = obj('trelica_torre', bm_aco, 'aco_gasto')
suavizar(o_aco)

o_cha = obj('caixa_seccionadora', bm_cha, 'chassi_amarelo')
suavizar(o_cha)

o_rem = obj('remendo_primer', bm_rem, 'remendo_primer')

o_lis = obj('listras_aviso', bm_lis, 'listras')

o_cer = obj('isoladores_disco', bm_cer, 'ceramica_verde')
suavizar(o_cer)

o_cor = obj('aneis_corona', bm_cor, 'aluminio_corona')
suavizar(o_cor)

o_cob = obj('cabos_condutores', bm_cob, 'cobre')
suavizar(o_cob)

# Mancha de óleo da seccionadora na laje
bm_oleo = bmesh.new()
mancha(bm_oleo, (-0.22, 0.0), 0.16, H_BASE + 0.001)
o_ole = obj('corpo_oleo', bm_oleo, 'oleo')

# ==============================================================================
# 5. CÚPULA DE PICO: NÓ DE RESSONÂNCIA DA IA E PARA-RAIOS FRANKLIN (Z = 4,95 a 5,45 m)
# ==============================================================================
# Ponteira da torre e haste do para-raios
bm_topo = bmesh.new()
tubo(bm_topo, (0, 0, Z_TOPO), (0, 0, Z_TOPO + 0.45), 0.024, 10)
tubo(bm_topo, (0, 0, Z_TOPO + 0.45), (0, 0, Z_TOPO + 0.70), 0.010, 8)  # haste afilada do captor
bmesh.ops.create_uvsphere(bm_topo, u_segments=12, v_segments=6, radius=0.035, matrix=Matrix.Translation(Vector((0, 0, Z_TOPO + 0.45))))
o_topo = obj('haste_pararaios', bm_topo, 'aco_escuro')
suavizar(o_topo)

# Anel de ressonância eletrostática da IA ('anel_ressonancia'): gira em torno do captor
bm_anel_ia = bmesh.new()
toro(bm_anel_ia, (0, 0, 0), 0.16, 0.016, nR=20, nr=6)
# 4 pequenos cristais emissores de onda nos quadrantes do anel
for ic in range(4):
    ang_c = ic * PI / 2
    dx_c, dy_c = math.cos(ang_c) * 0.16, math.sin(ang_c) * 0.16
    hexa_cristal(bm_anel_ia, (dx_c, dy_c, 0), 0.022, 0.06, ponta_sup=0.02, ponta_inf=0.02)

o_ress = obj('anel_ressonancia', bm_anel_ia, 'cristal_no')
suavizar(o_ress)
o_ress.location = Vector((0.0, 0.0, Z_TOPO + 0.45))

# Luz emitida pelo nó da IA
luz_no = bpy.data.lights.new('LuzNoIA', 'POINT')
luz_no.color = (0.55, 0.25, 1.0)
luz_no.energy = 16.0
o_luz_no = bpy.data.objects.new('EFEITO_LuzNoIA', luz_no)
o_luz_no.location = Vector((0.0, 0.0, Z_TOPO + 0.48))
sc.collection.objects.link(o_luz_no)

# Farol estroboscópico de alerta aéreo na ponta do para-raios (z = 5.65 m)
bm_est = bmesh.new()
tubo(bm_est, (0, 0, Z_TOPO + 0.65), (0, 0, Z_TOPO + 0.72), 0.020, 8)
o_est = obj('lampada_estrobo', bm_est, 'estrobo')

luz_est = bpy.data.lights.new('LuzEstrobo', 'POINT')
luz_est.color = (1.0, 0.25, 0.15)
luz_est.energy = 0.0
o_luz_est = bpy.data.objects.new('EFEITO_LuzEstrobo', luz_est)
o_luz_est.location = Vector((0.0, 0.0, Z_TOPO + 0.74))
sc.collection.objects.link(o_luz_est)

# Micro-arco corona elétrico estocástico em torno dos anéis corona
bm_corona = bmesh.new()
toro(bm_corona, (0, 0, 0), 0.092, 0.005, nR=16, nr=4)
o_arco_cor = obj('EFEITO_ArcoCorona', bm_corona, 'arco_corona')
o_arco_cor.location = pontos_fixacao_cabos[0] + Vector((0, 0, 0.04))
o_arco_cor.hide_render = True

# ==============================================================================
# 6. ANIMAÇÃO EM LAÇO (96 QUADROS A 24 QPS - 4 SEGUNDOS)
# ==============================================================================
for f in range(1, QUADROS + 1):
    sc.frame_set(f)

    # --- Anel de ressonância da IA girando 360° em 4 s
    ang_ia = (f / float(QUADROS)) * 2 * PI
    o_ress.rotation_euler = Euler((math.sin(f * 0.15) * 0.04, math.cos(f * 0.15) * 0.04, ang_ia), 'XYZ')
    o_ress.keyframe_insert('rotation_euler', frame=f)

    # Pulso harmônico da luz da IA
    pot_no = 16.0 + math.sin(f * 2 * PI / 24.0) * 8.0
    luz_no.energy = pot_no
    luz_no.keyframe_insert('energy', frame=f)

    # --- Farol estroboscópico de alerta de aviação no ápice (flash a cada 24 quadros)
    ciclo_est = (f % 24)
    pot_est = 60.0 if ciclo_est in (1, 2, 6, 7) else 0.0
    luz_est.energy = pot_est
    luz_est.keyframe_insert('energy', frame=f)

    # --- Micro-faíscas corona estocásticas no isolador
    if (f % 16) in (3, 4, 11):
        o_arco_cor.hide_render = False
        o_arco_cor.scale = Vector((1.0 + random.uniform(-0.1, 0.1), 1.0 + random.uniform(-0.1, 0.1), 1.0))
    else:
        o_arco_cor.hide_render = True
    o_arco_cor.keyframe_insert('hide_render', frame=f)
    o_arco_cor.keyframe_insert('scale', frame=f)

# ==============================================================================
# CÂMERAS, LUZ E RENDERIZAÇÃO
# ==============================================================================
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (14, 14, 1.0))
o_chao = obj('chao', bm_chao, 'chao')

sol_d = bpy.data.lights.new('Sol', 'SUN')
sol_d.energy = 4.4
sol_d.angle = math.radians(2.2)
o_sol = bpy.data.objects.new('Sol', sol_d)
sc.collection.objects.link(o_sol)
o_sol.rotation_euler = (math.radians(52), 0, math.radians(-38))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.58, 0.65, 0.78, 1.0)
bg.inputs['Strength'].default_value = 0.60

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

cam_d = bpy.data.cameras.new('Camera')
cam_d.lens = 38
cam_d.clip_start = 0.1
cam_d.clip_end = 100.0
cam = bpy.data.objects.new('EFEITO_Camera', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente=36):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = Vector((0.0, 0.0, 2.50))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
so_uma = args[1] if len(args) > 1 and modo == 'foto' else None

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(16)

    # 4 vistas ao redor (300°, 210°, 120°, 30°)
    for i, (ang, alt) in enumerate(((300, 3.8), (210, 4.0), (120, 4.1), (30, 3.7))):
        if so_uma is not None and so_uma != str(i):
            continue
        a = math.radians(ang)
        pos_cam = ALVO + Vector((math.cos(a) * 6.5, math.sin(a) * 6.5, alt - ALVO.z))
        mirar(pos_cam, ALVO, 34)
        sc.render.filepath = os.path.join(AQUI, 'poste_alto_%d.png' % i)
        bpy.ops.render.render(write_still=True)

    # Vista aproximada: cruzetas, cadeias de isoladores em disco, anéis corona e nó da IA
    if so_uma in (None, 'perto'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
        sc.frame_set(16)
        mirar(Vector((1.8, 1.4, 4.3)), Vector((0.0, 0.0, 4.2)), 36)
        sc.render.filepath = os.path.join(AQUI, 'poste_alto_perto.png')
        bpy.ops.render.render(write_still=True)

if modo == 'teste':
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    sc.frame_set(16)
    mirar(ALVO + Vector((4.2, -4.5, 2.0)), ALVO, 34)
    sc.render.filepath = os.path.join(AQUI, 'poste_alto_teste.png')
    bpy.ops.render.render(write_still=True)

tot_tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith(('chao', 'EFEITO')))
print('POSTE_ALTO ok (%d tris)' % tot_tri)
