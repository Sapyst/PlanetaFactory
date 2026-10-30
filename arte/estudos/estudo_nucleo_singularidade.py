"""Estudo isolado (fora do jogo): NÚCLEO DE SINGULARIDADE da IA, 3×3 tiles (lote 14, energia II).
Potência nominal: 100 MW contínuos e limpos (sem poluição). Tecnologia: 'singularidade'.
Gerador supremo de energia do fim do jogo. Não possui bocas de transporte de itens ou fluidos
(a energia de 100 MW é irradiada diretamente para a malha elétrica da colônia autônoma).

Engenharia de contenção gravitacional da IA:
- Base monumental de concreto armado 2,96 × 2,96 m com cantos chanfrados octogonais, canaletas de
  barramento trifásico pesado, sapatas de ancoragem com parafusos colossais e chapas de aço xadrez.
- Gimbal Giroscópico Triaxial Central de Contenção de Horizonte de Eventos:
  * Anel Externo: toro colossal em titânio e cobre com 8 bobinas toroidais supercondutoras e mancais de rotação em Z.
  * Anel Médio: toro em ouro e cromo com guias de onda polarizadoras girando em eixo inclinado.
  * Anel Interno: toro de supercondução criogênica em contra-rotação ultra-veloz.
- O Núcleo de Singularidade (Micro-Buraco Negro contido):
  * Horizonte de Eventos central: esfera de absorção quântica absoluta (raio 0,14 m).
  * Disco de Acreção Relativístico: disco plano espiral com plasma ultra-brilhante em rotação acelerada e pulso harmônico.
  * Jatos Polares Relativísticos: cones duplos de emissão de plasma com anéis magnéticos de colimação em +Z e -Z.
- 4 Torres Monolíticas de Confinamento nos 4 quadrantes diagonais:
  * Pilares inclinados de treliça pesada em aço corten com condutores criogênicos flangeados de hélio líquido.
  * Cabeçotes projetores com bobinas de cobre e cristais multifacetados apontando feixes de contenção para a singularidade.
  * Barramento vertical de 8 LEDs indicadores de gradiente de campo em cada coluna.
- Subestação Periférica de 100 MW e Criogenia Extrema:
  * Laterais com buchas isoladoras em degrau para 100 MW e cabos de cobre maciços em feixes trançados.
  * Tanques Dewar cilíndricos horizontais de hélio líquido com manômetros de vácuo e radiadores aletados
    com ventiladores axiais criogênicos velozes.

Peças animadas separadas:
- 'anel_giro_ext': anel de confinamento externo girando continuamente a 360° em Z.
- 'anel_giro_med': anel médio girando continuamente a 360° em torno de eixo inclinado a 45°.
- 'anel_giro_int': anel interno girando em contra-rotação veloz a -720°.
- 'disco_acrecion': disco de acreção de plasma girando a alta rotação (4 voltas/ciclo) com pulso harmônico de escala.
- 'singularidade_esfera': horizonte de eventos oscilando suavemente em escala gravitacional.
- 'ventoinha_criog_0', 'ventoinha_criog_1': rotores dos radiadores criogênicos girando velozmente.
- 'luz_singularidade': emissão de plasma pontual no centro com variações de intensidade e cor.

Uso: blender -b --python estudo_nucleo_singularidade.py -- foto
     blender -b --python estudo_nucleo_singularidade.py -- nada
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
Z_SING = 1.25                # centro da singularidade gravitacional contida
R_SING = 0.14                # raio do horizonte de eventos
R_TORO_EXT = 0.85            # raio maior do anel externo
R_TORO_MED = 0.66            # raio maior do anel intermediário
R_TORO_INT = 0.48            # raio maior do anel interno

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

def toro(bm, centro, R, r, nR=32, nr=12, rot=Matrix.Identity(3)):
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

def horizonte_mat():
    m = bpy.data.materials.new('HorizonteEventos')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.005, 0.005, 0.006, 1)
    b.inputs['Roughness'].default_value = 0.98
    b.inputs['Metallic'].default_value = 0.0
    return m

def acrecao_mat():
    m = bpy.data.materials.new('DiscoAcrecao')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.9, 0.3, 1.0, 1)
    b.inputs['Emission Color'].default_value = (0.85, 0.45, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 28.0
    return m

base3d.M.update({
    'titânio': mats.material('TitânioEscuro', (0.12, 0.13, 0.15), 0.9, 0.35, pintura=False, sujeira=0.6, escovado=True),
    'aco': mats.material('AçoEstrutural', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'aluminio': mats.material('Alumínio', (0.7, 0.71, 0.72), 1.0, 0.35, pintura=False, sujeira=0.8, escovado=True),
    'cobre': mats.material('CobreCriogenico', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8, ferrugem=0.2),
    'latao': mats.material('Latão', (0.78, 0.6, 0.28), 1.0, 0.3, pintura=False, sujeira=0.6),
    'ouro': mats.material('OuroSupercondutor', (0.95, 0.78, 0.22), 1.0, 0.18, pintura=False, sujeira=0.2),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=0.9, ferrugem=0.4),
    'isolante': mats.material('Isolante', (0.03, 0.03, 0.032), 0, 0.95, sujeira=0.6, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.32, 0.31, 0.29), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'horizonte': horizonte_mat(),
    'acrecao': acrecao_mat(),
    'campo': luz_mat('CampoSingularidade', (0.35, 0.65, 1.0), 12.0),
    'cristal_res': luz_mat('CristalGravitacional', (0.75, 0.25, 1.0), 16.0),
    'led_grav': luz_mat('LedGravidade', (0.2, 0.9, 1.0), 14.0),
    'led_alerta': luz_mat('LedAlerta', (1.0, 0.15, 0.05), 10.0),
})

# ------------------------------------------------------------------ BASE E LAJE OCTOGONAL (3x3 tiles)
bm = bmesh.new()
# Base octogonal chanfrada de concreto
n_oct = 8
raio_oct = 1.46
angulos_oct = [(i + 0.5) * 2 * PI / n_oct for i in range(n_oct)]
v_inf = [bm.verts.new((raio_oct * math.cos(a), raio_oct * math.sin(a), 0.0)) for a in angulos_oct]
v_sup = [bm.verts.new((raio_oct * math.cos(a), raio_oct * math.sin(a), Z_LAJE)) for a in angulos_oct]
for i in range(n_oct):
    bm.faces.new((v_inf[i], v_inf[(i + 1) % n_oct], v_sup[(i + 1) % n_oct], v_sup[i]))
bm.faces.new(reversed(v_inf))
bm.faces.new(v_sup)

# Rodapé perimetral com dente reforçado
casca(bm, (0, 0, 0), raio_oct + 0.02, raio_oct - 0.04, 0.0, Z_LAJE * 0.6, n=32)
obj('laje_concreto', bm, 'concreto')

# Chapa xadrez de aço central e anel de aterramento
bm = bmesh.new()
casca(bm, (0, 0, 0), 1.25, 0.75, Z_LAJE, Z_LAJE + 0.02, n=32)
# Vigas de travamento radial em X e Y na laje
for a_deg in (0, 45, 90, 135, 180, 225, 270, 315):
    rad = math.radians(a_deg)
    d = Vector((math.cos(rad), math.sin(rad), 0))
    p1 = d * 0.75 + Vector((0, 0, Z_LAJE + 0.01))
    p2 = d * 1.35 + Vector((0, 0, Z_LAJE + 0.01))
    viga(bm, p1, p2, 0.04)
# Canaletas perimetrais com tampas de ferro fundido
casca(bm, (0, 0, 0), 1.35, 1.25, Z_LAJE, Z_LAJE + 0.015, n=32)
obj('placas_base_aco', bm, 'aco')

# Listras de perigo industrial ao redor do poço central
bm = bmesh.new()
casca(bm, (0, 0, 0), 0.74, 0.68, Z_LAJE, Z_LAJE + 0.022, n=24)
obj('listras_perigo_paco', bm, 'listras')

# Poço gravitacional rebaixado central
bm = bmesh.new()
casca(bm, (0, 0, 0), 0.68, 0.40, Z_LAJE - 0.04, Z_LAJE + 0.01, n=24)
cil(bm, Vector((0, 0, Z_LAJE - 0.04)), 0.40, 0.02, lados=24)
# Anel de bobina de confinamento inferior no poço
toro(bm, (0, 0, Z_LAJE + 0.06), 0.52, 0.035, nR=24, nr=10)
obj('poco_gravitacional', bm, 'titânio')

bm = bmesh.new()
toro(bm, (0, 0, Z_LAJE + 0.06), 0.52, 0.022, nR=24, nr=8)
toro(bm, (0, 0, Z_LAJE + 0.12), 0.46, 0.025, nR=24, nr=8)
obj('bobinas_poco_cobre', bm, 'cobre')

# ------------------------------------------------------------------ 4 TORRES DIAGONAIS DE CAMPO GRAVITACIONAL
# Localizadas nos 4 quadrantes diagonais: (±0.92, ±0.92)
P_TORRES = [
    Vector((0.92, 0.92, 0)),
    Vector((-0.92, 0.92, 0)),
    Vector((-0.92, -0.92, 0)),
    Vector((0.92, -0.92, 0))
]

bm_aco = bmesh.new()
bm_tit = bmesh.new()
bm_cob = bmesh.new()
bm_ouro = bmesh.new()
bm_cristal = bmesh.new()
bm_leds = bmesh.new()

for i, p_base in enumerate(P_TORRES):
    # Direção apontando para o centro (0, 0, Z_SING)
    dir_centro = (Vector((0, 0, Z_SING)) - (p_base + Vector((0, 0, 1.40)))).normalized()
    rot_para_centro = dir_centro.to_track_quat('-Z', 'Y').to_matrix().to_3x3()
    
    # Sapata e pedestal chanfrado
    caixa_de(bm_tit, (p_base[0] - 0.22, p_base[1] - 0.22, Z_LAJE),
                     (p_base[0] + 0.22, p_base[1] + 0.22, Z_LAJE + 0.18))
    # Parafusos tensores e placas de ancoragem
    for dx in (-0.18, 0.18):
        for dy in (-0.18, 0.18):
            hexa(bm_aco, (p_base[0] + dx, p_base[1] + dy), 0.022, Z_LAJE + 0.18, Z_LAJE + 0.22)
            cil(bm_aco, (p_base[0] + dx, p_base[1] + dy, Z_LAJE + 0.225), 0.009, 0.03, lados=8)
            
    # Coluna principal em treliça inclinada em direção ao centro
    p_topo = p_base * 0.78 + Vector((0, 0, 1.45))
    viga(bm_tit, p_base + Vector((0, 0, 0.18)), p_topo, 0.15)
    
    # Contrafortes de reforço externo
    p_apoio_ext = p_base * 1.25 + Vector((0, 0, Z_LAJE))
    caixa_de(bm_aco, (p_apoio_ext[0] - 0.08, p_apoio_ext[1] - 0.08, Z_LAJE),
                     (p_apoio_ext[0] + 0.08, p_apoio_ext[1] + 0.08, Z_LAJE + 0.10))
    tubo(bm_tit, p_apoio_ext + Vector((0, 0, 0.10)), p_base * 0.88 + Vector((0, 0, 0.85)), 0.045, 12)
    
    # Cabeçote do projetor gravitacional
    caixa_de(bm_tit, (p_topo[0] - 0.16, p_topo[1] - 0.16, p_topo[2] - 0.12),
                     (p_topo[0] + 0.16, p_topo[1] + 0.16, p_topo[2] + 0.12))
    
    # Canhão concentrador cônico apontando para o centro
    p_foco = p_topo + dir_centro * 0.18
    bmesh.ops.create_cone(bm_cob, cap_ends=True, segments=16, radius1=0.15, radius2=0.08, depth=0.22,
                          matrix=Matrix.Translation(p_foco) @ rot_para_centro.to_4x4())
    # Anel polarizador frontal em ouro
    p_anel = p_topo + dir_centro * 0.30
    toro(bm_ouro, p_anel, 0.09, 0.02, nR=16, nr=8, rot=rot_para_centro)
    
    # Cristal focalizador de campo gravitacional
    p_cristal = p_topo + dir_centro * 0.32
    bmesh.ops.create_cone(bm_cristal, cap_ends=True, segments=6, radius1=0.045, radius2=0.0, depth=0.12,
                          matrix=Matrix.Translation(p_cristal) @ rot_para_centro.to_4x4())
    
    # Bobinas magnéticas laterais no cabeçote
    u_lat = dir_centro.cross(Z_VEC).normalized()
    for sgn in (-1, 1):
        p_bob = p_topo + u_lat * (sgn * 0.18)
        tubo(bm_cob, p_bob - u_lat * (sgn * 0.05), p_bob + u_lat * (sgn * 0.05), 0.065, 14)
        tubo(bm_tit, p_topo, p_bob, 0.03, 10)
        
    # Barramento vertical de 8 LEDs indicadores de gradiente de campo
    d_col = (p_topo - (p_base + Vector((0, 0, 0.20))))
    for k in range(8):
        s = 0.12 + 0.76 * (k / 7.0)
        p_led = (p_base + Vector((0, 0, 0.20))) + d_col * s - dir_centro * 0.10
        caixa(bm_leds, p_led, (0.025, 0.025, 0.035))

obj('torres_aco', bm_aco, 'aco')
obj('torres_titânio', bm_tit, 'titânio')
obj('torres_cobre', bm_cob, 'cobre')
obj('torres_ouro', bm_ouro, 'ouro')
obj('torres_cristais', bm_cristal, 'cristal_res')
obj('torres_leds', bm_leds, 'led_grav')

# ------------------------------------------------------------------ GIMBAL GIROSCÓPICO TRIAXIAL CENTRAL
# Anel Externo (titânio e cobre) - Gira em Z
bm_ext = bmesh.new()
toro(bm_ext, (0, 0, 0), R_TORO_EXT, 0.038, nR=36, nr=12)
# 8 Eletroímãs supercondutores toroidais distribuídos no anel externo
for k in range(8):
    a = k * 2 * PI / 8
    pos_m = Vector((R_TORO_EXT * math.cos(a), R_TORO_EXT * math.sin(a), 0))
    rot_m = Matrix.Rotation(a, 3, 'Z')
    toro(bm_ext, pos_m, 0.065, 0.018, nR=16, nr=8, rot=rot_m)
    # Braçadeiras de retenção
    caixa(bm_ext, pos_m + Vector((0, 0, 0.045)), (0.04, 0.04, 0.02))
    caixa(bm_ext, pos_m - Vector((0, 0, 0.045)), (0.04, 0.04, 0.02))
# Mancais articulados de suporte para o anel médio nos eixos X
caixa(bm_ext, (R_TORO_EXT, 0, 0), (0.08, 0.07, 0.09))
caixa(bm_ext, (-R_TORO_EXT, 0, 0), (0.08, 0.07, 0.09))
cil(bm_ext, (R_TORO_EXT, 0, 0), 0.025, 0.12, lados=12)
cil(bm_ext, (-R_TORO_EXT, 0, 0), 0.025, 0.12, lados=12)

anel_giro_ext = obj('anel_giro_ext', bm_ext, 'titânio')
anel_giro_ext.location = Vector((0, 0, Z_SING))
suavizar(anel_giro_ext)

# Anel Médio (ouro e cromo) - Gira em torno do eixo X articulado
bm_med = bmesh.new()
toro(bm_med, (0, 0, 0), R_TORO_MED, 0.032, nR=32, nr=12)
# Guias de onda polarizadoras em cruz e anéis de campo
for k in range(12):
    a = k * 2 * PI / 12
    pos_m = Vector((R_TORO_MED * math.cos(a), R_TORO_MED * math.sin(a), 0))
    rot_m = Matrix.Rotation(a, 3, 'Z')
    toro(bm_med, pos_m, 0.048, 0.012, nR=14, nr=6, rot=rot_m)
# Mancais articulados para o anel interno no eixo Y
caixa(bm_med, (0, R_TORO_MED, 0), (0.06, 0.07, 0.07))
caixa(bm_med, (0, -R_TORO_MED, 0), (0.06, 0.07, 0.07))
cil(bm_med, (0, R_TORO_MED, 0), 0.020, 0.10, lados=10)
cil(bm_med, (0, -R_TORO_MED, 0), 0.020, 0.10, lados=10)

anel_giro_med = obj('anel_giro_med', bm_med, 'ouro')
anel_giro_med.location = Vector((0, 0, Z_SING))
suavizar(anel_giro_med)

# Anel Interno (cobre criogênico e cromo) - Gira velozmente em contra-rotação
bm_int = bmesh.new()
toro(bm_int, (0, 0, 0), R_TORO_INT, 0.025, nR=28, nr=10)
# Bobinas axiais e aletas de resfriamento quântico
for k in range(16):
    a = k * 2 * PI / 16
    pos_m = Vector((R_TORO_INT * math.cos(a), R_TORO_INT * math.sin(a), 0))
    rot_m = Matrix.Rotation(a, 3, 'Z')
    toro(bm_int, pos_m, 0.036, 0.009, nR=12, nr=6, rot=rot_m)

anel_giro_int = obj('anel_giro_int', bm_int, 'cobre')
anel_giro_int.location = Vector((0, 0, Z_SING))
suavizar(anel_giro_int)

# ------------------------------------------------------------------ O NÚCLEO DE SINGULARIDADE (MICRO-BURACO NEGRO)
# 1. Horizonte de eventos central (esfera negra absoluta)
bm_sing = bmesh.new()
bmesh.ops.create_uvsphere(bm_sing, u_segments=24, v_segments=16, radius=R_SING)
singularidade_esfera = obj('singularidade_esfera', bm_sing, 'horizonte')
singularidade_esfera.location = Vector((0, 0, Z_SING))
suavizar(singularidade_esfera, tudo=True)

# 2. Disco de Acreção Relativístico (espiral plana incandescente)
bm_disco = bmesh.new()
# Anel toroidal plano com pequena espessura volumétrica
r_in, r_out = 0.16, 0.44
casca(bm_disco, (0, 0, 0), r_out, r_in, -0.006, 0.006, n=36)

disco_acrecion = obj('disco_acrecion', bm_disco, 'acrecao')
disco_acrecion.location = Vector((0, 0, Z_SING))

# 3. Jatos Polares Relativísticos (cones de plasma colimados)
bm_jatos = bmesh.new()
# Jato superior (+Z)
bmesh.ops.create_cone(bm_jatos, cap_ends=False, segments=16, radius1=0.03, radius2=0.10, depth=0.85,
                      matrix=Matrix.Translation((0, 0, 0.50)))
# Anéis de estrangulamento magnético no jato superior
toro(bm_jatos, (0, 0, 0.35), 0.07, 0.012, nR=16, nr=6)
toro(bm_jatos, (0, 0, 0.65), 0.09, 0.012, nR=16, nr=6)
# Jato inferior (-Z)
bmesh.ops.create_cone(bm_jatos, cap_ends=False, segments=16, radius1=0.03, radius2=0.08, depth=0.75,
                      matrix=Matrix.Translation((0, 0, -0.45)) @ Matrix.Rotation(PI, 3, 'X').to_4x4())
toro(bm_jatos, (0, 0, -0.35), 0.065, 0.012, nR=16, nr=6)

jatos_polares = obj('jatos_polares', bm_jatos, 'campo')
jatos_polares.location = Vector((0, 0, Z_SING))
suavizar(jatos_polares)

# Luz Pontual Central da Singularidade
luz_sing_data = bpy.data.lights.new('LuzSingularidade', 'POINT')
luz_sing_data.color = (0.75, 0.35, 1.0)
luz_sing_data.energy = 320.0
luz_sing_data.shadow_soft_size = 0.15
luz_sing_obj = bpy.data.objects.new('LuzSingularidade', luz_sing_data)
sc.collection.objects.link(luz_sing_obj)
luz_sing_obj.location = Vector((0, 0, Z_SING))

# ------------------------------------------------------------------ SUBESTAÇÃO DE 100 MW (LESTE E OESTE)
bm_transf = bmesh.new()
bm_buchas = bmesh.new()
bm_cabos = bmesh.new()

for sgn in (-1, 1):
    x_sub = sgn * 1.15
    # Bloco blindado da subestação
    caixa_de(bm_transf, (x_sub - 0.22, -0.45, Z_LAJE), (x_sub + 0.22, 0.45, Z_LAJE + 0.65))
    # Aletas de refrigeração na lateral externa
    for y_a in [-0.35 + k * 0.07 for k in range(11)]:
        caixa(bm_transf, (x_sub + sgn * 0.24, y_a, Z_LAJE + 0.35), (0.03, 0.012, 0.50))
    # 3 Buchas isoladoras cerâmicas monumentais em degrau (100 MW trifásico)
    for k, y_b in enumerate((-0.28, 0.0, 0.28)):
        z_b = Z_LAJE + 0.65
        cil(bm_transf, (x_sub, y_b, z_b + 0.04), 0.07, 0.08, lados=14)
        # Degraus cerâmicos
        for step in range(4):
            z_step = z_b + 0.08 + step * 0.06
            cil(bm_buchas, (x_sub, y_b, z_step), 0.06 - step * 0.007, 0.05, lados=14)
            toro(bm_buchas, (x_sub, y_b, z_step + 0.025), 0.065 - step * 0.007, 0.010, nR=14, nr=6)
        # Terminal de cobre no topo da bucha
        z_top = z_b + 0.36
        cil(bm_cabos, (x_sub, y_b, z_top), 0.025, 0.08, lados=10)
        # Cabo de barramento descendo para a laje
        p_c1 = Vector((x_sub, y_b, z_top + 0.04))
        p_c2 = Vector((x_sub - sgn * 0.18, y_b, z_top + 0.12))
        p_c3 = Vector((x_sub - sgn * 0.35, y_b * 0.6, Z_LAJE + 0.25))
        tubo(bm_cabos, p_c1, p_c2, 0.018, 10)
        tubo(bm_cabos, p_c2, p_c3, 0.018, 10)

obj('subestacao_corpo', bm_transf, 'titânio')
obj('subestacao_buchas', bm_buchas, 'isolante')
obj('subestacao_barramentos', bm_cabos, 'cobre')

# ------------------------------------------------------------------ SISTEMA CRIOGÊNICO DE HÉLIO (NORTE E SUL)
bm_dewar = bmesh.new()
bm_rad = bmesh.new()
bm_canos = bmesh.new()

for sgn in (-1, 1):
    y_crio = sgn * 1.15
    # Tanque Dewar horizontal de hélio líquido (-269°C)
    cil(bm_dewar, (0, y_crio, Z_LAJE + 0.32), 0.24, 0.70, eixo=Vector((1, 0, 0)), lados=20)
    curva(bm_dewar, (-0.35, y_crio, Z_LAJE + 0.32), 0.24, lados=16)
    curva(bm_dewar, (0.35, y_crio, Z_LAJE + 0.32), 0.24, lados=16)
    # Berços de suporte em aço corten
    for x_b in (-0.26, 0.26):
        caixa_de(bm_dewar, (x_b - 0.04, y_crio - 0.22, Z_LAJE), (x_b + 0.04, y_crio + 0.22, Z_LAJE + 0.20))
        # Cintas de aperto metálicas
        toro(bm_dewar, (x_b, y_crio, Z_LAJE + 0.32), 0.245, 0.015, nR=20, nr=6, rot=Matrix.Rotation(PI / 2, 3, 'Y'))
    # Manômetro de vácuo analógico
    p_mano = Vector((0.36, y_crio, Z_LAJE + 0.48))
    cil(bm_dewar, p_mano, 0.05, 0.03, eixo=Vector((1, 0, 0)), lados=12)
    
    # Tubulação de alimentação criogênica com flanges indo para o poço central
    cano(bm_canos, bm_dewar, [
        (0.0, y_crio - sgn * 0.24, Z_LAJE + 0.32),
        (0.0, y_crio - sgn * 0.45, Z_LAJE + 0.32),
        (0.0, y_crio - sgn * 0.65, Z_LAJE + 0.12),
        (0.0, sgn * 0.50, Z_LAJE + 0.12)
    ], 0.035, flange=True)

obj('tanques_dewar', bm_dewar, 'aluminio')
obj('canos_criogenicos', bm_canos, 'cobre')

# Radiadores aletados com ventiladores axiais criogênicos
for i, sgn in enumerate((-1, 1)):
    y_rad = sgn * 1.36
    # Caixa do radiador
    caixa_de(bm_rad, (-0.32, y_rad - 0.08, Z_LAJE), (0.32, y_rad + 0.08, Z_LAJE + 0.55))
    # Bocal circular do ventilador
    casca(bm_rad, (0, y_rad, 0), 0.22, 0.20, Z_LAJE + 0.08, Z_LAJE + 0.48, n=20)

obj('radiador_criogenico', bm_rad, 'titânio')

# Ventoinhas criogênicas animadas separadas
ventoinhas = []
for i, sgn in enumerate((-1, 1)):
    y_rad = sgn * 1.36
    z_rad = Z_LAJE + 0.28
    bm_v = bmesh.new()
    cil(bm_v, (0, 0, 0), 0.055, 0.06, eixo=Vector((0, 1, 0)), lados=12)
    # 6 Pás helicoidais do ventilador
    for p in range(6):
        a_p = p * 2 * PI / 6
        rot_p = Matrix.Rotation(a_p, 3, 'Y')
        bmesh.ops.create_cube(bm_v, size=1.0, matrix=Matrix.Translation((0.11 * math.cos(a_p), 0, 0.11 * math.sin(a_p))) @
                              rot_p.to_4x4() @ Matrix.Rotation(math.radians(28), 3, 'Z').to_4x4() @ Matrix.Scale(0.12, 4, Vector((1, 0, 0))) @
                              Matrix.Scale(0.015, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.05, 4, Vector((0, 0, 1))))
    v_obj = obj(f'ventoinha_criog_{i}', bm_v, 'aco')
    v_obj.location = Vector((0, y_rad, z_rad))
    suavizar(v_obj)
    ventoinhas.append(v_obj)

# ------------------------------------------------------------------ ANIMAÇÃO (96 QUADROS, 4 s, LAÇO FECHADO)
for q in range(1, QUADROS + 1):
    t = (q - 1) / QUADROS     # 0.0 a 1.0
    
    # 1. Rotação do anel externo em Z (1 volta completa = 360°)
    ang_ext = t * 2 * PI
    anel_giro_ext.rotation_euler = Euler((0, 0, ang_ext), 'XYZ')
    anel_giro_ext.keyframe_insert('rotation_euler', frame=q)
    
    # 2. Rotação do anel médio em torno de eixo inclinado a 45°
    ang_med = t * 2 * PI
    q_inclinacao = Quaternion(Vector((1, 1, 0)).normalized(), math.radians(45))
    q_rot = Quaternion(Vector((0, 0, 1)), ang_med)
    anel_giro_med.rotation_euler = (q_inclinacao @ q_rot).to_euler()
    anel_giro_med.keyframe_insert('rotation_euler', frame=q)
    
    # 3. Contra-rotação veloz do anel interno (-2 voltas = -720°)
    ang_int = -t * 4 * PI
    q_inc_int = Quaternion(Vector((1, -1, 0)).normalized(), math.radians(35))
    q_rot_int = Quaternion(Vector((0, 0, 1)), ang_int)
    anel_giro_int.rotation_euler = (q_inc_int @ q_rot_int).to_euler()
    anel_giro_int.keyframe_insert('rotation_euler', frame=q)
    
    # 4. Rotação veloz e pulso harmônico do disco de acreção (4 voltas = 8*pi)
    ang_disco = t * 8 * PI
    disco_acrecion.rotation_euler = Euler((0, 0, ang_disco), 'XYZ')
    # Pulso respiratório de acreção (4 ciclos de respiração)
    pulso_disco = 1.0 + 0.06 * math.sin(4 * 2 * PI * t)
    disco_acrecion.scale = Vector((pulso_disco, pulso_disco, 1.0))
    disco_acrecion.keyframe_insert('rotation_euler', frame=q)
    disco_acrecion.keyframe_insert('scale', frame=q)
    
    # 5. Pulso gravitacional no horizonte de eventos (micro-oscilação)
    pulso_sing = 1.0 + 0.03 * math.cos(4 * 2 * PI * t)
    singularidade_esfera.scale = Vector((pulso_sing, pulso_sing, pulso_sing))
    singularidade_esfera.keyframe_insert('scale', frame=q)
    
    # 6. Rotação das ventoinhas criogênicas (6 voltas por ciclo)
    ang_vent = t * 12 * PI
    for i, v_o in enumerate(ventoinhas):
        sgn = 1 if i == 0 else -1
        v_o.rotation_euler = Euler((0, sgn * ang_vent, 0), 'XYZ')
        v_o.keyframe_insert('rotation_euler', frame=q)
        
    # 7. Variação harmônica da luz central de plasma
    luz_sing_data.energy = 320.0 + 80.0 * math.sin(4 * 2 * PI * t)
    luz_sing_data.keyframe_insert('energy', frame=q)

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
obj('EFEITO_chao', bm, 'chao')

# Luz Solar
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.8
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

ALVO = (0.0, 0.0, 1.15)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo == 'nada':
    tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH')
    print(f'NUCLEO_SINGULARIDADE_NADA_OK tris={tris}')
    sys.exit(0)

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    
    # 4 ângulos cardeais/isométricos
    for i, (ang, alt, tq) in enumerate(((305, 4.2, 0.35), (215, 4.0, 0.60), (125, 4.4, 0.85), (35, 3.8, 0.15))):
        sc.frame_set(int(tq * FPS) + 1)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.9, math.sin(a) * 4.9, alt - ALVO[2])), ALVO, 30)
        sc.render.filepath = os.path.join(AQUI, f'nucleo_singularidade_{i}.png')
        bpy.ops.render.render(write_still=True)
        
    # Close-up no horizonte de eventos, disco de acreção, anéis do gimbal e projetores
    sc.frame_set(int(0.50 * FPS) + 1)
    mirar((0.0, -1.45, 1.45), (0.0, 0.0, Z_SING), 35)
    sc.render.filepath = os.path.join(AQUI, 'nucleo_singularidade_perto.png')
    bpy.ops.render.render(write_still=True)

print('NUCLEO_SINGULARIDADE ok')
