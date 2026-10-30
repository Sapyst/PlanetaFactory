"""Estudo isolado (fora do jogo): BIODIGESTOR e ESTAÇÃO DE TRATAMENTO da IA, 3×3 tiles cada (1 tile = 1 m; x leste,
y norte). Cada um é montado numa cena própria (argumento 'bio' ou 'trat').

BIODIGESTOR (resíduo + água suja → biomassa + seiva). Portas: resíduo entra pelo oeste (tile NO, na moega), água suja
entra pelo sul (tile SO, cano até o tanque de mistura), biomassa sai pelo leste (tile SE, na esteira), seiva sai pelo
leste (tile L, cano âmbar).
- Tanque de concreto com cintas de aço e anel de aperto; por cima o gasômetro de membrana dupla (balão de lona
  emborrachada com cintas) que infla e desinfla no laço; no ápice escotilha com respiro (vapor esverdeado) e o olho
  flutuante da IA.
- Moega de resíduo (lixo misturado) com rosca transportadora inclinada em calha aberta (hélice girando) até o tanque
  de mistura aberto, onde um agitador vertical gira na lama marrom com espuma, borbulhas e redemoinho.
- Bomba de cavidade progressiva leva a lama ao digestor. Trocador de calor casco-tubo (lama em laço com o tanque,
  água quente do queimador). Linha de gás amarela com pote de condensado e corta-chama até o queimador e o flare
  (chaminé com chama pequena no topo).
- Saída: prensa de rosca separa o digestato; a biomassa (pasta verde-escura) sai numa esteira; o líquido cai na
  bandeja e sobe para a coluna de campo violeta, que o clareia em seiva âmbar; cano âmbar com visor até a borda leste.
- Sujeira: lodo escorrendo do anel e do tanque de mistura, ferrugem escorrida dos parafusos, poças, óleo, poeira.

ESTAÇÃO DE TRATAMENTO (água suja → água limpa 60/s; limpa o rio num raio de 16 m), na margem de um rio que corre de
oeste para leste: a montante (oeste) a água é turva; a jusante da descarga ela fica limpa, com a transição visível.
- Tomada no cais (grade com lixo preso) e bomba vertical → tanque de aeração com difusores borbulhando (soprador de
  lóbulos com silenciador) → dois decantadores circulares com ponte raspadora girando; dentro, o campo violeta da IA
  separa o lodo (no fundo) da água límpida que brilha; janelas de vidro mostram as camadas → filtros de pressão →
  canal UV com lâmpadas em bainhas de quartzo (anéis limpadores com pistão) → cano de descarga que despeja água
  limpa no rio. Lodo dos decantadores vai à caçamba. Mastro de cristal da IA alimenta os emissores de campo.
Uso: blender -b --python estudo_biodigestor_tratamento.py -- foto bio|trat [0|perto]
     blender -b --python estudo_biodigestor_tratamento.py -- teste bio|trat x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto', 'bio']
MODO = ARGS[0]
QUAL = ARGS[1] if len(ARGS) > 1 else 'bio'
random.seed(31 if QUAL == 'bio' else 47)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no


# ================================================================== geometria
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def base_de(eixo):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    return q @ X, q @ Y, q @ Z


def toro(bm, centro, R, r, eixo=Z, nR=48, nr=12):
    u, v, w = base_de(eixo)
    centro = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = u * math.cos(a) + v * math.sin(a)
        aneis.append([bm.verts.new(centro + d * (R + r * math.cos(b)) + w * (r * math.sin(b)))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B_ = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B_[(j + 1) % nr], B_[j]))


def tubo_oco(bm, centro, ro, ri, h, eixo=Z, lados=40):
    u, v, w = base_de(eixo)
    centro = Vector(centro)
    an = {}
    for k, (r, z) in enumerate(((ro, -h / 2), (ro, h / 2), (ri, -h / 2), (ri, h / 2))):
        an[k] = [bm.verts.new(centro + (u * math.cos(a) + v * math.sin(a)) * r + w * z)
                 for a in (i * 2 * PI / lados for i in range(lados))]
    for i in range(lados):
        j = (i + 1) % lados
        bm.faces.new((an[0][i], an[0][j], an[1][j], an[1][i]))
        bm.faces.new((an[2][i], an[3][i], an[3][j], an[2][j]))
        bm.faces.new((an[1][i], an[1][j], an[3][j], an[3][i]))
        bm.faces.new((an[0][i], an[2][i], an[2][j], an[0][j]))


def arco_parede(bm, c, ri, ro, z0, z1, a0, a1, n=24):
    """Trecho de parede cilíndrica com espessura (de a0 a a1, radianos), fechado nas pontas."""
    c = Vector(c)
    col = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        col.append([bm.verts.new(c + d * r + Z * z) for r, z in ((ro, z0), (ro, z1), (ri, z1), (ri, z0))])
    for A, B_ in zip(col, col[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], B_[i], B_[j], A[j]))
    bm.faces.new(col[0][::-1])
    bm.faces.new(col[-1])


def esfera(bm, c, r, seg=20):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r,
                              matrix=Matrix.Translation(Vector(c)))


def base_lat(u):
    u = Vector(u).normalized()
    s = u.cross(Z)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    return s, s.cross(u).normalized() if abs(u.z) > 0.9 else (u.cross(s).normalized() if u.cross(s).z > 0 else -u.cross(s).normalized())


def chapa_arco(bm, c, u, r_in, esp, larg, a0, a1, n=14):
    """Chapa curva em volta do eixo u (calha, sela, abraçadeira, remendo); ângulo medido de s para cima."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    linhas = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        d = s * math.cos(a) + up * math.sin(a)
        linhas.append([bm.verts.new(c + d * rr + u * w) for rr in (r_in, r_in + esp) for w in (-larg / 2, larg / 2)])
    for A, B_ in zip(linhas, linhas[1:]):
        for (i, j) in ((0, 1), (3, 2), (2, 0), (1, 3)):
            bm.faces.new((A[i], A[j], B_[j], B_[i]))
    for L in (linhas[0], linhas[-1]):
        bm.faces.new((L[0], L[1], L[3], L[2]))


def bez(p0, p1, p2, p3, t):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    return p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ piscina de malhas por material (objetos estáticos)
POOL = {}


def B(mat, liso=False):
    if (mat, liso) not in POOL:
        POOL[(mat, liso)] = bmesh.new()
    return POOL[(mat, liso)]


def fechar_pool(pref):
    for (mat, liso), bm in list(POOL.items()):
        if not bm.verts:
            bm.free()
            continue
        o = obj('%s_%s%s' % (pref, mat, '_l' if liso else ''), bm, mat)
        if liso:
            suavizar(o)
    POOL.clear()


# ------------------------------------------------------------------ peças de tubulação e detalhes
def flange(c, eixo, r, esp=0.022, n=8, mat='ferro'):
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(B(mat, True), c, r, esp, eixo, lados=28)
    u, v, _ = base_de(eixo)
    for k in range(n):
        a = k * 2 * PI / n + 0.3
        p = c + (u * math.cos(a) + v * math.sin(a)) * (r - 0.012)
        cil(B('aco'), p, 0.006, esp + 0.016, eixo, lados=6)
        cil(B('aco'), p + eixo * (esp / 2 + 0.006), 0.0105, 0.007, eixo, lados=6)


def cano(pts, r, mat='cano', fl=True, fl_pontas=True, lados=24, fl_mat='ferro'):
    """Cano por pontos: retos, cotovelos redondos e flanges perto das emendas."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(B(mat, True), a, b, r, lados)
    for p in pts[1:-1]:
        esfera(B(mat, True), p, r, lados)
    if fl:
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            d, L = (b - a).normalized(), (b - a).length
            if L < r * 5:
                continue
            if i > 0 or fl_pontas:
                flange(a + d * r * 1.9, d, r * 1.5, r * 0.42, mat=fl_mat)
            if i < len(pts) - 2 or fl_pontas:
                flange(b - d * r * 1.9, d, r * 1.5, r * 0.42, mat=fl_mat)


def colar(c, eixo, r):
    """Colar de passagem numa parede (cano entrando no concreto)."""
    c = Vector(c)
    cil(B('ferro', True), c, r * 1.7, 0.03, eixo, lados=28)
    u, v, _ = base_de(eixo)
    for k in range(8):
        a = k * PI / 4 + 0.2
        cil(B('aco'), c + (u * math.cos(a) + v * math.sin(a)) * r * 1.45 + Vector(eixo).normalized() * 0.018,
            0.007, 0.012, eixo, lados=6)


GAUGES = []


def manometro(p, cima, face):
    p, cima, face = Vector(p), Vector(cima).normalized(), Vector(face).normalized()
    tubo(B('cromo'), p, p + cima * 0.07, 0.008, 8)
    c = p + cima * 0.1
    cil(B('cromo', True), c, 0.038, 0.024, face, lados=20)
    cil(B('mostrador'), c + face * 0.0125, 0.032, 0.002, face, lados=20)
    u, v, _ = base_de(face)
    ang = random.uniform(0.3, 2.4)
    d = u * math.cos(ang) + v * math.sin(ang)
    viga(B('ponteiro'), c + face * 0.0145 - d * 0.005, c + face * 0.0145 + d * 0.026, 0.003)


def atuador(c, eixo, r):
    """Válvula borboleta com atuador elétrico selado (sem volante: não há humanos) e luz de estado."""
    c, eixo = Vector(c), Vector(eixo).normalized()
    cil(B('grafite', True), c, r + 0.025, 0.055, eixo, lados=24)
    flange(c + eixo * 0.036, eixo, r + 0.03, 0.018, 8)
    flange(c - eixo * 0.036, eixo, r + 0.03, 0.018, 8)
    top = c + Z * (r + 0.025)
    cil(B('aco'), top + Z * 0.025, 0.012, 0.05, lados=10)
    caixa(B('amarelo'), top + Z * 0.085, (0.1, 0.075, 0.07))
    cil(B('grafite', True), top + Z * 0.085 + eixo.cross(Z).normalized() * 0.055, 0.025, 0.04,
        eixo.cross(Z), lados=14)
    cil(B('lampada'), top + Z * 0.12, 0.008, 0.008, lados=10)


def suporte(c, u, r):
    """Suporte de chão: bloco de concreto, perfil, sela e abraçadeira."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    chapa_arco(B('ferro', True), c, u, r + 0.001, 0.012, 0.07, math.radians(195), math.radians(345), 12)
    chapa_arco(B('aco', True), c, u, r + 0.001, 0.004, 0.03, math.radians(-12), math.radians(192), 16)
    pe = Vector((c.x, c.y, 0.08))
    caixa_de(B('concreto'), pe + Vector((-0.07, -0.07, 0)), pe + Vector((0.07, 0.07, 0.04)))
    zb = c.z - r - 0.012
    if zb > 0.14:
        viga(B('amarelo'), pe + Z * 0.04, Vector((c.x, c.y, zb)), 0.045)
    caixa(B('ferro'), Vector((c.x, c.y, zb - 0.006)), (0.09, 0.09, 0.012))


def remendo(c, u, r, a0, a1, larg, mat='oxido'):
    c, u = Vector(c), Vector(u).normalized()
    chapa_arco(B(mat, True), c, u, r + 0.001, 0.006, larg, a0, a1, 10)
    s, up = base_lat(u)
    for a in (a0 + 0.08 * (a1 - a0), a1 - 0.08 * (a1 - a0)):
        d = s * math.cos(a) + up * math.sin(a)
        for w in (-larg / 2 + 0.014, larg / 2 - 0.014):
            cil(B('aco'), c + d * (r + 0.009) + u * w, 0.008, 0.008, d, lados=6)


def remendo_plano(c, n, t, w, h, mat='oxido'):
    """Chapa aparafusada numa parede plana (n normal para fora, t lateral)."""
    c, n, t = Vector(c), Vector(n).normalized(), Vector(t).normalized()
    up = n.cross(t).normalized()
    rot = Matrix((t, up, n)).transposed()
    caixa(B(mat), c + n * 0.004, (w, h, 0.007), rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cil(B('aco'), c + n * 0.009 + t * sx * (w / 2 - 0.015) + up * sy * (h / 2 - 0.015), 0.007, 0.008, n, lados=6)


SEG = dict(a=(0, 1, 1, 0), b=(1, 1, 0, 1), c=(1, 0, 0, 1), d=(0, 0, 1, 0), e=(0, 0, 0, 1), f=(0, 1, 0, 1), g=(0, 0.5, 1, 0))
DIG = ['abcdef', 'bc', 'abged', 'abgcd', 'fgbc', 'afgcd', 'afgedc', 'abc', 'abcdefg', 'abfgcd']


def serie(c, n_, t_, n=6, alt=0.04, apagado=0.35):
    """Número de série em estêncil (7 segmentos) numa face plana: c centro, n_ normal, t_ direção do texto."""
    c, n_, t_ = Vector(c), Vector(n_).normalized(), Vector(t_).normalized()
    up = n_.cross(t_).normalized()
    larg = alt * 0.55
    rot = Matrix((t_, up, n_)).transposed()
    texto = [random.choice(DIG) for _ in range(n)]
    texto.insert(2, 'g')
    for i, dg in enumerate(texto):
        x0 = (i - len(texto) / 2) * larg * 1.5
        for sg in dg:
            if random.random() < apagado:
                continue
            hx, hy, vx, vy = SEG[sg]
            if sg in 'adg':
                p = Vector((x0 + larg / 2, alt * (hy - 0.5), 0))
                tam = (larg * 0.8, alt * 0.12, 0.0015)
            else:
                p = Vector((x0 + larg * hx, alt * (0.25 if sg in 'bf' else -0.25), 0))
                tam = (larg * 0.16, alt * 0.42, 0.0015)
            caixa(B('tinta'), c + n_ * 0.0012 + rot @ p, tam, rot)


def serie_cil(c, R, ang, z, n=6, alt=0.045):
    """Número de série na face de um cilindro vertical (centro c, raio R) no ângulo ang."""
    d = Vector((math.cos(ang), math.sin(ang), 0))
    serie(Vector((c[0], c[1], z)) + d * R, d, Z.cross(d), n, alt)


def fios(a, b, solto=0.06):
    a, b = Vector(a), Vector(b)
    for k, m in enumerate(('fio_v', 'fio_a', 'fio_m')):
        off = Vector(((k - 1) * 0.008, (k - 1) * 0.006, 0))
        meio = (a + b) / 2 + Vector((0, 0, -solto)) + off * 2
        pts = bezier(a + off, a + off + Vector((0, 0, -solto * 0.6)), meio, b + off, 10)
        mangueira(B(m), pts, 0.0045)
        tubo(B('cobre'), b + off, b + off + (b - meio).normalized() * 0.015, 0.002, 6)


def escorrido_cil(mat, c, R, a, z_top, L, w, esp=0.004):
    """Escorrido (lodo, ferrugem) descendo pela face de um cilindro vertical; afina e ondula."""
    bm = B(mat, True)
    n = 9
    linhas = []
    for i in range(n + 1):
        t = i / n
        z = z_top - L * t
        ww = w * (1 - 0.6 * t) * (1 + 0.25 * math.sin(i * 1.7 + a * 5))
        aa = a + 0.006 * math.sin(i * 2.3 + a) / R
        da = ww / (2 * R)
        e = esp * (1 - 0.5 * t)
        linhas.append([bm.verts.new((c[0] + math.cos(ang) * rr, c[1] + math.sin(ang) * rr, z))
                       for ang, rr in ((aa - da, R + 0.001), (aa + da, R + 0.001), (aa + da * 0.7, R + e), (aa - da * 0.7, R + e))])
    for A, B_ in zip(linhas, linhas[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], A[j], B_[j], B_[i]))
    bm.faces.new(linhas[0])
    bm.faces.new(linhas[-1][::-1])


def escorrido_plano(mat, p, n_, L, w, esp=0.004):
    """Escorrido numa parede plana vertical: p ponto do topo na face, n_ normal para fora."""
    p, n_ = Vector(p), Vector(n_).normalized()
    t_ = Z.cross(n_).normalized()
    bm = B(mat, True)
    nn = 8
    linhas = []
    for i in range(nn + 1):
        t = i / nn
        ww = w * (1 - 0.6 * t) * (1 + 0.25 * math.sin(i * 1.9 + p.x * 9))
        q = p - Z * L * t + t_ * 0.006 * math.sin(i * 2.1 + p.y * 7)
        e = esp * (1 - 0.5 * t)
        linhas.append([bm.verts.new(q + t_ * s * ww / 2 + n_ * d) for s, d in ((-1, 0.001), (1, 0.001), (0.7, e), (-0.7, e))])
    for A, B_ in zip(linhas, linhas[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], A[j], B_[j], B_[i]))
    bm.faces.new(linhas[0])
    bm.faces.new(linhas[-1][::-1])


def poca(c, r, mat='lodo_liq', z=0.0815):
    mancha(B(mat), c, r, z)
    mancha(B('halo'), c, r * 1.9, z - 0.0007)


# ================================================================== materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat(nome='Vidro', sujo=0.5):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Coat Weight'].default_value = 0.8
    b.inputs['Coat Roughness'].default_value = 0.03
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 16.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.7, 'To Min': 0.0, 'To Max': sujo})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.95, 0.96, 0.95, 1)
    cor.inputs[7].default_value = (0.3, 0.22, 0.1, 1)
    nt.links.new(f.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.03, 'To Max': 0.5})
    nt.links.new(f.outputs['Result'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    return m


def liquido_mat(nome, cor, rough=0.08, transm=0.0, forca=0.0, emis=None, bump=0.15, escala=9.0):
    """Líquido com ondulação (bump de ruído) e brilho opcional."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.33
    b.inputs['Emission Color'].default_value = (*(emis or cor), 1)
    b.inputs['Emission Strength'].default_value = forca
    if bump > 0:
        geo = no(nt, 'ShaderNodeNewGeometry')
        ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 4.0})
        nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
        bp = no(nt, 'ShaderNodeBump', **{'Strength': bump})
        nt.links.new(ru.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def lodo_mat(nome, c0, c1, rough=0.25, escala=6.0, bump=0.4):
    """Lama/lodo/pasta: duas cores em manchas, relevo granulado, brilho de molhado."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (*c0, 1)
    cor.inputs[7].default_value = (*c1, 1)
    nt.links.new(ru.outputs['Fac'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': rough * 0.5, 'To Max': rough * 1.8})
    nt.links.new(ru.outputs['Fac'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': escala * 9})
    nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
    bp = no(nt, 'ShaderNodeBump', **{'Strength': bump})
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def halo_mat():
    m = bpy.data.materials.new('Mancha de sujeira')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.06, 0.05, 0.035, 1)
    b.inputs['Roughness'].default_value = 0.7
    tc = no(nt, 'ShaderNodeTexCoord')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sp.inputs[0])
    cb = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sp.outputs['X'], cb.inputs['X'])
    nt.links.new(sp.outputs['Y'], cb.inputs['Y'])
    d = no(nt, 'ShaderNodeVectorMath', operation='DISTANCE')
    d.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(cb.outputs[0], d.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 5.0})
    nt.links.new(tc.outputs['Generated'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.25
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(d.outputs['Value'], soma.inputs[2])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.62, 'To Min': 0.7, 'To Max': 0.0})
    nt.links.new(soma.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def tinta_mat():
    m = mats.material('Estêncil apagado', (0.72, 0.7, 0.62), 0, 0.8, pintura=False, sujeira=0.9, desgaste=0.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 140.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.6, 'To Min': 0.0, 'To Max': 0.8})
    nt.links.new(ru.outputs['Fac'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def rustico(m, poeira=1.0, lama=1.0, fuligem=1.0, amassado=0.12, escorrido=0.0):
    """Camada de uso: poeira no que olha para cima, lama respingada embaixo, fuligem, amassados e (opcional)
    escorridos verticais de ferrugem/lodo (ruído esticado em z)."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    cor = lk.from_socket if lk else None
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 8.0, 'Detail': 3.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    gr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], gr.inputs['Vector'])
    cima = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.9})
    nt.links.new(sn.outputs['Z'], cima.inputs['Value'])
    pr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.62, 'To Min': 0.25, 'To Max': 0.95 * poeira})
    nt.links.new(ru.outputs['Fac'], pr.inputs['Value'])
    fp = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(cima.outputs['Result'], fp.inputs[0])
    nt.links.new(pr.outputs['Result'], fp.inputs[1])
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.1, 'From Max': 0.26, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sp.outputs['Z'], baixo.inputs['Value'])
    lr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.6, 'To Min': 0.3, 'To Max': 1.0 * lama})
    nt.links.new(ru.outputs['Fac'], lr.inputs['Value'])
    fl = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(baixo.outputs['Result'], fl.inputs[0])
    nt.links.new(lr.outputs['Result'], fl.inputs[1])
    fu = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.7, 'To Max': 0.75 * fuligem})
    nt.links.new(gr.outputs['Fac'], fu.inputs['Value'])
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    c1.inputs[7].default_value = (0.08, 0.07, 0.065, 1)
    nt.links.new(fu.outputs['Result'], c1.inputs[0])
    if cor is not None:
        nt.links.new(cor, c1.inputs[6])
    else:
        c1.inputs[6].default_value = b.inputs['Base Color'].default_value
    saida = c1.outputs[2]
    if escorrido > 0:                                                       # riscos verticais de ferrugem escorrida
        mp = no(nt, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (14.0, 14.0, 1.2)
        nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
        es = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.0, 'Detail': 6.0})
        nt.links.new(mp.outputs['Vector'], es.inputs['Vector'])
        ef = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.58, 'From Max': 0.72, 'To Max': escorrido})
        nt.links.new(es.outputs['Fac'], ef.inputs['Value'])
        ce = no(nt, 'ShaderNodeMix', data_type='RGBA')
        ce.inputs[7].default_value = (0.24, 0.09, 0.03, 1)
        nt.links.new(ef.outputs['Result'], ce.inputs[0])
        nt.links.new(saida, ce.inputs[6])
        saida = ce.outputs[2]
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c2.inputs[7].default_value = (0.36, 0.31, 0.24, 1)
    nt.links.new(fp.outputs['Value'], c2.inputs[0])
    nt.links.new(saida, c2.inputs[6])
    c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c3.inputs[7].default_value = (0.1, 0.07, 0.04, 1)
    nt.links.new(fl.outputs['Value'], c3.inputs[0])
    nt.links.new(c2.outputs[2], c3.inputs[6])
    nt.links.new(c3.outputs[2], b.inputs['Base Color'])
    rk = next((l for l in nt.links if l.to_socket == b.inputs['Roughness']), None)
    soma = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(fp.outputs['Value'], soma.inputs[0])
    nt.links.new(fl.outputs['Value'], soma.inputs[1])
    rmix = no(nt, 'ShaderNodeMix', data_type='FLOAT')
    rmix.inputs[3].default_value = 0.95
    nt.links.new(soma.outputs['Value'], rmix.inputs[0])
    if rk:
        nt.links.new(rk.from_socket, rmix.inputs[2])
    else:
        rmix.inputs[2].default_value = b.inputs['Roughness'].default_value
    nt.links.new(rmix.outputs[0], b.inputs['Roughness'])
    met = next((l for l in nt.links if l.to_socket == b.inputs['Metallic']), None)
    if met or b.inputs['Metallic'].default_value > 0:
        mm = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        nt.links.new(soma.outputs['Value'], mm.inputs[0])
        if met:
            nt.links.new(met.from_socket, mm.inputs[2])
        else:
            mm.inputs[2].default_value = b.inputs['Metallic'].default_value
        mm.inputs[3].default_value = 0.0
        nt.links.new(mm.outputs[0], b.inputs['Metallic'])
    if amassado > 0:
        vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 5.0})
        vo.feature = 'SMOOTH_F1'
        nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
        bump = no(nt, 'ShaderNodeBump', **{'Strength': amassado})
        bump.inputs['Distance'].default_value = 0.02
        nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
        nk = next((l for l in nt.links if l.to_socket == b.inputs['Normal']), None)
        if nk:
            nt.links.new(nk.from_socket, bump.inputs['Normal'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])


def membrana_mat():
    """Lona emborrachada do gasômetro: verde-oliva fosco, desbotada em manchas, com riscos de sujeira escorrida."""
    m = mats.material('Membrana', (0.11, 0.13, 0.075), 0, 0.62, pintura=False, sujeira=0.7, desgaste=0.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Sheen Weight'].default_value = 0.3
    return m


VIOLETA = (0.6, 0.3, 1.0)
SEIVA = (1.0, 0.55, 0.06)
FASES = []
FLUXO_F, FLUXO_K = 7.0, 14


def fluxo_mat(nome, forca):
    """Seiva correndo no visor: faixas âmbar e bolhas andando ao longo de z do objeto."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.08
    tc = no(nt, 'ShaderNodeTexCoord')
    vet = tc.outputs['Object']
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(vet, sep.inputs[0])
    val = no(nt, 'ShaderNodeValue')
    FASES.append(val)
    mz = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    mz.inputs[1].default_value = FLUXO_F
    nt.links.new(sep.outputs['Z'], mz.inputs[0])
    sub = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(mz.outputs['Value'], sub.inputs[0])
    nt.links.new(val.outputs[0], sub.inputs[1])
    pi2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    pi2.inputs[1].default_value = 2 * PI
    nt.links.new(sub.outputs['Value'], pi2.inputs[0])
    sen = no(nt, 'ShaderNodeMath', operation='SINE')
    nt.links.new(pi2.outputs['Value'], sen.inputs[0])
    faixa = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0})
    nt.links.new(sen.outputs['Value'], faixa.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.45, 0.13, 0.005, 1)
    cor.inputs[7].default_value = (1.0, 0.56, 0.08, 1)
    nt.links.new(faixa.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    nt.links.new(cor.outputs[2], b.inputs['Emission Color'])
    e1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    e1.inputs[1].default_value = 0.7 * forca
    e1.inputs[2].default_value = 0.3 * forca
    nt.links.new(faixa.outputs['Result'], e1.inputs[0])
    nt.links.new(e1.outputs['Value'], b.inputs['Emission Strength'])
    return m


def grad_mat(nome, eixo, v0, v1, cor0, cor1, tr0, tr1, em0=0.0, em1=0.0, emis=(1, 1, 1), ior=1.05):
    """Líquido que muda de cor/transparência/brilho ao longo de um eixo do mundo (v0 → v1), fronteira irregular."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['IOR'].default_value = ior
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Emission Color'].default_value = (*emis, 1)
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': v0, 'From Max': v1})
    nt.links.new(sep.outputs[eixo], t.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 14.0, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    sub = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    sub.inputs[1].default_value = 0.3
    sub.inputs[2].default_value = -0.15
    nt.links.new(ru.outputs['Fac'], sub.inputs[0])
    tt = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(t.outputs['Result'], tt.inputs[0])
    nt.links.new(sub.outputs['Value'], tt.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (*cor0, 1)
    cor.inputs[7].default_value = (*cor1, 1)
    nt.links.new(tt.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    tr = no(nt, 'ShaderNodeMapRange', **{'To Min': tr0, 'To Max': tr1})
    nt.links.new(tt.outputs['Value'], tr.inputs['Value'])
    nt.links.new(tr.outputs['Result'], b.inputs['Transmission Weight'])
    em = no(nt, 'ShaderNodeMapRange', **{'To Min': em0, 'To Max': em1})
    nt.links.new(tt.outputs['Value'], em.inputs['Value'])
    nt.links.new(em.outputs['Result'], b.inputs['Emission Strength'])
    return m


def pelicula_mat(nome='Película', cor=VIOLETA, f0=0.12, f1=0.55, e0=0.6, e1=4.0, freq=38.0):
    """Película de campo: translúcida com anéis de interferência que brilham."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*cor, 1)
    tc = no(nt, 'ShaderNodeTexCoord')
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], ln.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 4.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.25
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(ln.outputs['Value'], soma.inputs[2])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY', name='fase')
    mul.inputs[1].default_value = freq
    nt.links.new(soma.outputs['Value'], mul.inputs[0])
    onda = no(nt, 'ShaderNodeMath', operation='SINE')
    nt.links.new(mul.outputs['Value'], onda.inputs[0])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0, 'To Min': f0, 'To Max': f1})
    nt.links.new(onda.outputs['Value'], f.inputs['Value'])
    forca = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0, 'To Min': e0, 'To Max': e1})
    nt.links.new(onda.outputs['Value'], forca.inputs['Value'])
    nt.links.new(forca.outputs['Result'], em.inputs['Strength'])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def fogo_mat():
    m = base3d.volume_mat('Fogo', (1.0, 0.4, 0.05), 3.0, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 70.0
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1)
    return m


def terra_mat(molhada=True):
    m = bpy.data.materials.new('Terra')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 2.5, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])
    seca = no(nt, 'ShaderNodeMix', data_type='RGBA')
    seca.inputs[6].default_value = (0.19, 0.15, 0.10, 1)
    seca.inputs[7].default_value = (0.11, 0.13, 0.05, 1)
    capim = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.62})
    nt.links.new(ru.outputs['Fac'], capim.inputs['Value'])
    nt.links.new(capim.outputs['Result'], seca.inputs[0])
    molh = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.05, 'From Max': -0.3})
    nt.links.new(sep.outputs['Z'], molh.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[7].default_value = (0.065, 0.05, 0.03, 1)
    nt.links.new(molh.outputs['Result'], cor.inputs[0])
    nt.links.new(seca.outputs[2], cor.inputs[6])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.35
    nt.links.new(cor.outputs[2], var.inputs[6])
    nt.links.new(fino.outputs['Color'], var.inputs[7])
    nt.links.new(var.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.95, 'To Max': 0.35})
    nt.links.new(molh.outputs['Result'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.4})
    nt.links.new(fino.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def rio_mat(x0, x1, xp, yp):
    """Rio que corre para leste: turvo (marrom opaco, silte em redemoinho) a montante, limpo (verde-claro
    transparente, fundo visível) a jusante. Fronteira esticada no sentido da corrente + pluma clara saindo da
    descarga (xp, yp)."""
    m = bpy.data.materials.new('Rio')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['IOR'].default_value = 1.33
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.35, 1.6, 1.0)                    # silte esticado na corrente
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.3, 'Detail': 7.0, 'Distortion': 1.2})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    # mistura: x ao longo da corrente + pluma radial da descarga, deformada pelo ruído
    tx = no(nt, 'ShaderNodeMapRange', **{'From Min': x0, 'From Max': x1})
    nt.links.new(sep.outputs['X'], tx.inputs['Value'])
    dx = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(sep.outputs['X'], dx.inputs[0])
    dx.inputs[1].default_value = xp
    dy = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(sep.outputs['Y'], dy.inputs[0])
    dy.inputs[1].default_value = yp
    dyy = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    dyy.inputs[1].default_value = 1.6
    nt.links.new(dy.outputs['Value'], dyy.inputs[0])
    cb = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(dx.outputs['Value'], cb.inputs['X'])
    nt.links.new(dyy.outputs['Value'], cb.inputs['Y'])
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(cb.outputs[0], ln.inputs[0])
    pl = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.5, 'From Max': 0.4})
    nt.links.new(ln.outputs['Value'], pl.inputs['Value'])
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(tx.outputs['Result'], mx.inputs[0])
    nt.links.new(pl.outputs['Result'], mx.inputs[1])
    dist = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    dist.inputs[1].default_value = 0.7
    dist.inputs[2].default_value = -0.35
    nt.links.new(ru.outputs['Fac'], dist.inputs[0])
    mix_t = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(mx.outputs['Value'], mix_t.inputs[0])
    nt.links.new(dist.outputs['Value'], mix_t.inputs[1])
    nitido = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.7})
    nt.links.new(mix_t.outputs['Value'], nitido.inputs['Value'])
    turva = no(nt, 'ShaderNodeMix', data_type='RGBA')
    turva.inputs[6].default_value = (0.075, 0.052, 0.024, 1)
    turva.inputs[7].default_value = (0.17, 0.12, 0.055, 1)
    nt.links.new(ru.outputs['Fac'], turva.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    nt.links.new(turva.outputs[2], cor.inputs[6])
    cor.inputs[7].default_value = (0.42, 0.6, 0.5, 1)
    nt.links.new(nitido.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    tr = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.0, 'To Max': 0.97})
    nt.links.new(nitido.outputs['Result'], tr.inputs['Value'])
    nt.links.new(tr.outputs['Result'], b.inputs['Transmission Weight'])
    onda = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 3.0})
    nt.links.new(mp.outputs['Vector'], onda.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.1})
    nt.links.new(onda.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def jato_mat():
    m = bpy.data.materials.new('Jato')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    ag = no(nt, 'ShaderNodeBsdfPrincipled')
    ag.inputs['Base Color'].default_value = (0.9, 0.96, 0.97, 1)
    ag.inputs['Transmission Weight'].default_value = 1.0
    ag.inputs['Roughness'].default_value = 0.05
    ag.inputs['IOR'].default_value = 1.33
    br = no(nt, 'ShaderNodeBsdfPrincipled')
    br.inputs['Base Color'].default_value = (0.8, 0.84, 0.84, 1)
    br.inputs['Roughness'].default_value = 0.5
    br.inputs['Transmission Weight'].default_value = 0.3
    tc = no(nt, 'ShaderNodeTexCoord')
    esc = no(nt, 'ShaderNodeMapping')
    esc.inputs['Scale'].default_value = (14.0, 14.0, 2.5)
    nt.links.new(tc.outputs['Object'], esc.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 6.0})
    nt.links.new(esc.outputs['Vector'], ru.inputs['Vector'])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.65})
    nt.links.new(ru.outputs['Fac'], f.inputs['Value'])
    mix = no(nt, 'ShaderNodeMixShader')
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(ag.outputs[0], mix.inputs[1])
    nt.links.new(br.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def mancha_limpa_mat():
    """Pluma de água limpa que se abre no rio: some na borda (coordenada do objeto, raio 1)."""
    m = bpy.data.materials.new('Pluma limpa')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.5, 0.7, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['IOR'].default_value = 1.33
    b.inputs['Transmission Weight'].default_value = 0.85
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mix = no(nt, 'ShaderNodeMixShader')
    tc = no(nt, 'ShaderNodeTexCoord')
    ln = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], ln.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 3.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma.inputs[1].default_value = 0.45
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    nt.links.new(ln.outputs['Value'], soma.inputs[2])
    f = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.1, 'From Max': 0.5, 'To Min': 0.0, 'To Max': 0.85})
    nt.links.new(soma.outputs['Value'], f.inputs['Value'])
    nt.links.new(f.outputs['Result'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def campo_mat(nome, cor, dens, emis):
    """Camada de campo em volume: névoa violeta que brilha, mais densa no meio."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.05, 0.02, 0.1, 1)
    vol.inputs['Emission Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.6})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = dens
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    e.inputs[1].default_value = emis
    nt.links.new(mul.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'cano': mats.material('Cano', (0.13, 0.135, 0.13), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.75),
    'cano_gas': mats.material('Cano de gás', (0.7, 0.5, 0.06), 0, 0.45, desgaste=1.0, sujeira=1.0, ferrugem=0.6),
    'cano_seiva': mats.material('Cano de seiva', (0.10, 0.12, 0.10), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.75),
    'cano_quente': mats.material('Cano quente', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.7),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'inox': mats.material('Inox', (0.62, 0.62, 0.62), 1.0, 0.3, pintura=False, ferrugem=0.25, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'queimado': mats.material('Queimado', (0.13, 0.11, 0.12), 1.0, 0.55, pintura=False, ferrugem=0.6, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.8, desgaste=0.0),
    'concreto_t': mats.material('Concreto do tanque', (0.34, 0.33, 0.30), 0, 0.92, sujeira=1.0, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'cinta': mats.material('Cinta', (0.06, 0.055, 0.05), 0, 0.8, pintura=False, sujeira=0.6, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.79, 0.74), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'ponteiro': mats.material('Ponteiro', (0.5, 0.05, 0.02), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'oxido': mats.material('Primer vermelho', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'cinza': mats.material('Peça trocada cinza', (0.33, 0.34, 0.33), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.5),
    'verde_tr': mats.material('Peça trocada verde', (0.12, 0.2, 0.12), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.5),
    'lata': mats.material('Lata', (0.55, 0.56, 0.56), 1.0, 0.45, pintura=False, ferrugem=0.5, sujeira=1.0),
    'fio_v': mats.material('Fio vermelho', (0.5, 0.03, 0.02), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'fio_a': mats.material('Fio azul', (0.03, 0.08, 0.4), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'fio_m': mats.material('Fio amarelo', (0.55, 0.42, 0.03), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'membrana': membrana_mat(),
    'tinta': tinta_mat(),
    'halo': halo_mat(),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
    'luz_verde': emissivo('Luz verde', (0.15, 1.0, 0.25), 6.0),
    'luz_vermelha': emissivo('Luz vermelha', (1.0, 0.08, 0.03), 6.0),
    'emissor': emissivo('Emissor', (0.45, 0.12, 1.0), 1.4, (0.15, 0.03, 0.4)),
    'cristal': emissivo('Cristal', (0.5, 0.18, 1.0), 3.0, (0.22, 0.06, 0.65)),
    'vidro': vidro_mat(),
    'visor': vidro_mat('Visor', 0.25),
    'lama': lodo_mat('Lama', (0.09, 0.06, 0.03), (0.16, 0.11, 0.055), 0.3),
    'lama_seca': lodo_mat('Lama seca', (0.2, 0.15, 0.09), (0.26, 0.2, 0.13), 0.9, bump=0.2),
    'lodo_liq': liquido_mat('Lodo líquido', (0.07, 0.045, 0.02), rough=0.12, bump=0.1),
    'escorrido': lodo_mat('Lodo escorrido', (0.05, 0.04, 0.018), (0.09, 0.07, 0.03), 0.12, bump=0.1),
    'ferrugem_esc': lodo_mat('Ferrugem escorrida', (0.2, 0.07, 0.02), (0.3, 0.12, 0.04), 0.7, bump=0.1),
    'espuma_m': lodo_mat('Espuma marrom', (0.12, 0.085, 0.045), (0.24, 0.17, 0.09), 0.5, escala=14.0, bump=0.8),
    'espuma': lodo_mat('Espuma branca', (0.62, 0.6, 0.55), (0.8, 0.79, 0.74), 0.8, escala=16.0, bump=0.8),
    'bolha_lodo': liquido_mat('Bolha de lodo', (0.13, 0.09, 0.045), rough=0.04, bump=0.0),
    'bolha_agua': liquido_mat('Bolha de ar', (0.85, 0.88, 0.88), rough=0.1, transm=0.4, bump=0.0),
    'pedra': mats.material('Pedra', (0.15, 0.145, 0.13), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'galho': mats.material('Galho', (0.11, 0.08, 0.05), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'palha': mats.material('Palha', (0.28, 0.22, 0.11), 0, 0.8, pintura=False, sujeira=0.5, desgaste=0.0),
    'alga': mats.material('Alga', (0.05, 0.075, 0.025), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'folha': mats.material('Folhas', (0.09, 0.12, 0.03), 0, 0.6, pintura=False, sujeira=0.6, desgaste=0.0),
    'plastico': mats.material('Plástico desbotado', (0.12, 0.2, 0.32), 0, 0.5, pintura=False, sujeira=0.9, desgaste=0.0),
    'osso': mats.material('Resto claro', (0.55, 0.5, 0.4), 0, 0.7, pintura=False, sujeira=0.9, desgaste=0.0),
    'biomassa': lodo_mat('Biomassa', (0.02, 0.045, 0.015), (0.045, 0.08, 0.025), 0.28, escala=9.0, bump=0.6),
    'fluxo': fluxo_mat('Seiva correndo', 2.6),
    'gota_seiva': emissivo('Gota de seiva', SEIVA, 4.0),
    'pelicula': pelicula_mat(),
    'pelicula_fraca': pelicula_mat('Feixe', VIOLETA, 0.03, 0.18, 0.3, 2.0, 60.0),
    'fogo': fogo_mat(),
    'chama': emissivo('Miolo da chama', (1.0, 0.55, 0.12), 25.0),
    'brasa': emissivo('Brasa do queimador', (1.0, 0.32, 0.04), 14.0),
    'jato': jato_mat(),
    'campo': campo_mat('Campo do decantador', VIOLETA, 5.0, 3.0),
})
for chave, kw in (('amarelo', dict(escorrido=0.5)), ('grafite', {}), ('cano', dict(escorrido=0.6)),
                  ('cano_gas', dict(escorrido=0.4)), ('cano_seiva', {}), ('cano_quente', dict(escorrido=0.6)),
                  ('ferro', dict(amassado=0.1, escorrido=0.5)), ('aco', dict(amassado=0.0, fuligem=0.5)),
                  ('oxido', {}), ('cinza', dict(escorrido=0.5)), ('verde_tr', {}), ('lata', dict(amassado=0.4)),
                  ('inox', dict(amassado=0.0)), ('concreto', dict(amassado=0.0, fuligem=0.6)),
                  ('concreto_t', dict(amassado=0.0, fuligem=0.8, escorrido=0.5)),
                  ('borracha', dict(amassado=0.0, fuligem=0.0)), ('queimado', dict(amassado=0.0)),
                  ('membrana', dict(amassado=0.0, fuligem=0.6, poeira=1.3, escorrido=0.35)),
                  ('cromo', dict(amassado=0.0, poeira=0.4, fuligem=0.3))):
    rustico(base3d.M[chave], **kw)
for n in base3d.M['concreto'].node_tree.nodes:                              # manchas por cima não sujam a laje (AO)
    if n.type == 'AMBIENT_OCCLUSION':
        n.only_local = True

ANIM = []          # funções f(q, fr) chamadas em cada quadro


def chave(o, *cs, q):
    for c in cs:
        o.keyframe_insert(c, frame=q)


def vazio(nome, loc=(0, 0, 0), pai=None):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
    e.location = loc
    if pai is not None:
        e.parent = pai
    return e


def nuvem(nome, mat, n, origem, sobe, r0, r1, deriva=Vector((0.0, 0.0, 0.0)), voltas=1):
    """Baforadas de volume (vapor) que nascem em origem (função de fr ou vetor), sobem e crescem."""
    bols = []
    for k in range(n):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        bols.append(obj(nome, bm, mat))

    def f(q, fr):
        for k, o in enumerate(bols):
            u = (k / n + fr * voltas) % 1.0
            org = origem(fr) if callable(origem) else Vector(origem)
            o.location = org + Z * sobe * u + deriva * u + Vector((0.03 * math.sin(k * 2.1 + u * 6), 0.03 * math.cos(k * 1.3 + u * 5), 0))
            o.scale = [r0 + (r1 - r0) * u] * 3
            chave(o, 'location', 'scale', q=q)
    ANIM.append(f)


def chao_plano(tam=40):
    bm = bmesh.new()
    xs = [-tam, -12, -6, -4] + [i * 0.25 - 3.5 for i in range(29)] + [4, 6, 12, tam]
    vs = [[bm.verts.new((x, y, -0.005 + 0.02 * math.sin(x * 1.3) * math.cos(y * 1.7) * (1 if max(abs(x), abs(y)) > 1.6 else 0)))
           for x in xs] for y in xs]
    for j in range(len(xs) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    suavizar(obj('chao', bm, 'terra'))


def laje(listras_lados=()):
    caixa_de(B('concreto'), (-1.48, -1.48, 0), (1.48, 1.48, 0.08))
    for k in range(16):                                                     # rachaduras e emendas da laje
        if k % 2:
            x = random.uniform(-1.4, 1.4)
            caixa_de(B('oleo'), (x - 0.003, -1.46, 0.0801), (x + 0.003, -1.46 + random.uniform(0.2, 1.2), 0.0806))
    for x in (-0.5, 0.5):                                                   # juntas de dilatação nos limites dos tiles
        caixa_de(B('borracha'), (x - 0.006, -1.48, 0.0795), (x + 0.006, 1.48, 0.0805))
        caixa_de(B('borracha'), (-1.48, x - 0.006, 0.0795), (1.48, x + 0.006, 0.0805))
    for lado in listras_lados:
        if lado == 'N':
            caixa_de(B('listras'), (-1.485, 1.45, 0), (1.485, 1.485, 0.083))
        if lado == 'S':
            caixa_de(B('listras'), (-1.485, -1.485, 0), (1.485, -1.45, 0.083))
        if lado == 'L':
            caixa_de(B('listras'), (1.45, -1.485, 0), (1.485, 1.485, 0.083))
        if lado == 'O':
            caixa_de(B('listras'), (-1.485, -1.485, 0), (-1.45, 1.485, 0.083))


def armario(c, w, d, h, frente):
    """Armário de controle selado (sem porta): aletas, luzes de estado, antena, grelha, placa trocada."""
    c = Vector(c)
    f = Vector(frente).normalized()
    t = Z.cross(f).normalized()
    rot = Matrix((t, f, Z)).transposed()
    caixa(B('grafite'), c + Z * (0.08 + h / 2), (w, d, h), rot)
    for k in range(7):
        caixa(B('grafite'), c + Z * (0.08 + h + 0.03) + t * (-w / 2 + 0.03 + k * (w - 0.06) / 6), (0.012, d - 0.04, 0.06), rot)
    for k in range(3):
        cil(B(('luz_verde', 'lampada', 'luz_vermelha')[k]), c + f * (d / 2 + 0.003) + Z * (0.08 + h - 0.08) + t * (-0.05 + k * 0.05),
            0.012, 0.008, f, lados=12)
    caixa(B('ferro'), c + f * (d / 2 + 0.004) + Z * (0.08 + h * 0.4), (w * 0.7, 0.008, h * 0.25), rot)
    remendo_plano(c + f * (d / 2) + Z * (0.08 + h * 0.7) - t * w * 0.15, f, t, w * 0.35, h * 0.18, 'cinza')
    serie(c + f * (d / 2 + 0.002) + Z * (0.08 + h * 0.18), f, t, 5, 0.03)
    tubo(B('aco'), c + Z * (0.08 + h + 0.06) + t * w * 0.35, c + Z * (0.08 + h + 0.42) + t * w * 0.35, 0.006, 6)
    esfera(B('lampada'), c + Z * (0.08 + h + 0.43) + t * w * 0.35, 0.014, 10)
    return c + Z * (0.08 + h * 0.3) - t * (w / 2), c + f * (d / 2 + 0.01) + Z * (0.08 + h * 0.62) + t * w * 0.3


# ================================================================== BIODIGESTOR
def construir_biodigestor():
    base3d.M['terra'] = terra_mat()
    chao_plano()
    laje(('L',))
    T = Vector((0.25, 0.35, 0))
    RT = 0.78                    # raio externo do tanque
    ZT = 0.62                    # topo da parede
    ZD = 0.655                   # base da membrana (anel de aperto)
    RD = 0.73                    # raio da membrana na base

    # ---------------------------------------------------------- tanque de concreto
    cil(B('concreto_t', True), T + Z * ((0.08 + ZT) / 2), RT, ZT - 0.08, lados=64)
    cil(B('concreto_t', True), T + Z * 0.11, RT + 0.05, 0.06, lados=64)                 # sapata
    for z in (0.2, 0.36, 0.52):                                                        # cintas de aço protendido
        cil(B('ferro', True), T + Z * z, RT + 0.008, 0.03, lados=64)
        for k in range(4):                                                             # esticadores das cintas
            a = k * PI / 2 + 0.4 + z
            d = Vector((math.cos(a), math.sin(a), 0))
            caixa(B('aco'), T + d * (RT + 0.025) + Z * z, (0.03, 0.09, 0.045), Matrix.Rotation(a, 3, 'Z'))
    for k in range(10):                                                                # pilares (nervuras)
        a = k * 2 * PI / 10 + 0.15
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('concreto_t'), T + d * (RT + 0.018) + Z * ((0.14 + ZT) / 2), (0.04, 0.07, ZT - 0.14), Matrix.Rotation(a, 3, 'Z'))
    arco_parede(B('ferro', True), T, RT - 0.06, RT + 0.01, ZT, ZT + 0.016, 0, 2 * PI, 96)   # cantoneira do topo
    toro(B('ferro', True), T + Z * ZD, RD + 0.012, 0.03, nR=96, nr=12)                  # anel de aperto da membrana
    for k in range(36):                                                                # grampos do anel
        a = k * 2 * PI / 36
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('aco'), T + d * (RD + 0.045) + Z * (ZD - 0.005), (0.05, 0.022, 0.05), Matrix.Rotation(a, 3, 'Z'))
        cil(B('aco'), T + d * (RD + 0.06) + Z * (ZD + 0.025), 0.008, 0.02, lados=6)
    for k in range(14):                                                                # lodo escorrendo do anel
        a = random.uniform(0, 2 * PI)
        escorrido_cil('escorrido', T, RT, a, ZT + 0.005, random.uniform(0.12, 0.45), random.uniform(0.02, 0.05))
    for k in range(10):                                                                # ferrugem dos esticadores
        a = random.uniform(0, 2 * PI)
        escorrido_cil('ferrugem_esc', T, RT + 0.008, a, random.choice((0.2, 0.36, 0.52)) - 0.02, random.uniform(0.06, 0.18),
                      random.uniform(0.012, 0.025), 0.003)
    serie_cil(T, RT + 0.002, -1.95, 0.43, 6, 0.06)
    serie_cil(T, RT + 0.002, -0.35, 0.28, 5, 0.045)
    # placa de inspeção da IA (sensor de nível) na parede, com cabo
    a = -1.25
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('grafite'), T + d * (RT + 0.03) + Z * 0.44, (0.08, 0.05, 0.12), Matrix.Rotation(a + PI / 2, 3, 'Z'))
    cil(B('emissor'), T + d * (RT + 0.058) + Z * 0.47, 0.014, 0.008, d, lados=12)

    # ---------------------------------------------------------- gasômetro: membrana que infla e desinfla (shape key)
    def domo_pt(th, ph, s):
        H = 0.40 + 0.25 * s
        cph = math.cos(ph)
        r = RD * max(cph, 0.0) ** 0.8
        rug = (1 - s) * 0.04 + 0.006
        f = math.sin(min(ph * 1.9, PI)) * cph
        r += rug * f * math.sin(th * 13 + 1.7 * math.sin(th * 3))
        z = ZD + H * math.sin(ph) + (1 - s) * 0.02 * math.sin(th * 7) * math.sin(ph * 2)
        return Vector((T.x + r * math.cos(th), T.y + r * math.sin(th), z))

    NT_, NP_ = 120, 26

    def malha_domo(nome, mat, gerar):
        bm = bmesh.new()
        cos1, cos0, faces = gerar()
        vs = [bm.verts.new(p) for p in cos1]
        for f_ in faces:
            bm.faces.new([vs[i] for i in f_])
        o = obj(nome, bm, mat)
        o.shape_key_add(name='Basis')
        k = o.shape_key_add(name='murcho')
        for i, p in enumerate(cos0):
            k.data[i].co = p
        for pg in o.data.polygons:
            pg.use_smooth = True
        return o, k

    def ger_domo():
        c1, c0, faces = [], [], []
        for j in range(NP_):
            ph = (PI / 2) * j / NP_
            for i in range(NT_):
                th = 2 * PI * i / NT_
                c1.append(domo_pt(th, ph, 1.0))
                c0.append(domo_pt(th, ph, 0.0))
        c1.append(domo_pt(0, PI / 2, 1.0))
        c0.append(domo_pt(0, PI / 2, 0.0))
        topo = len(c1) - 1
        for j in range(NP_ - 1):
            for i in range(NT_):
                a, b = j * NT_ + i, j * NT_ + (i + 1) % NT_
                faces.append((a, b, b + NT_, a + NT_))
        for i in range(NT_):
            faces.append(((NP_ - 1) * NT_ + i, (NP_ - 1) * NT_ + (i + 1) % NT_, topo))
        return c1, c0, faces

    def ger_cintas():
        c1, c0, faces = [], [], []
        for k in range(8):
            th0 = k * PI / 4 + PI / 8
            n0 = len(c1)
            NJ = 22
            for j in range(NJ + 1):
                ph = 1.43 * j / NJ
                larg = 0.022 / (RD * max(math.cos(ph), 0.2))
                for s, c in ((1.0, c1), (0.0, c0)):
                    cen = Vector((T.x, T.y, ZD))
                    for dt, e in ((-larg, 0.004), (larg, 0.004), (larg, 0.011), (-larg, 0.011)):
                        p = domo_pt(th0 + dt, ph, s)
                        nrm = (p - cen).normalized()
                        c.append(p + nrm * e)
            for j in range(NJ):
                a = n0 + j * 4
                for i in range(4):
                    i2 = (i + 1) % 4
                    faces.append((a + i, a + i2, a + 4 + i2, a + 4 + i))
        return c1, c0, faces

    domo, k_domo = malha_domo('gasometro', 'membrana', ger_domo)
    cintas, k_cintas = malha_domo('gasometro_cintas', 'cinta', ger_cintas)
    for k in range(8):                                                                 # catracas das cintas no anel
        a = k * PI / 4 + PI / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('amarelo'), T + d * (RD + 0.07) + Z * (ZD - 0.07), (0.05, 0.07, 0.06), Matrix.Rotation(a, 3, 'Z'))
        cil(B('aco'), T + d * (RD + 0.07) + Z * (ZD - 0.07), 0.012, 0.09, Matrix.Rotation(a, 3, 'Z') @ Y, lados=8)
        escorrido_cil('ferrugem_esc', T, RT + 0.002, a + 0.03, ZT - 0.02, random.uniform(0.1, 0.25), 0.02, 0.003)
        viga(B('cinta'), T + d * (RD + 0.004) + Z * (ZD + 0.004), T + d * (RD + 0.065) + Z * (ZD - 0.05), 0.04)
    # ápice: escotilha com respiro e válvula de alívio (sobem e descem com a membrana)
    apice = vazio('apice', (T.x, T.y, ZD + 0.65))
    bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
    cil(bf, Vector((0, 0, 0.0)), 0.13, 0.03, lados=36)
    for k in range(12):
        a = k * PI / 6
        cil(bp, Vector((math.cos(a) * 0.115, math.sin(a) * 0.115, 0.02)), 0.008, 0.016, lados=6)
    cil(bm, Vector((0.0, 0, 0.06)), 0.035, 0.1, lados=20)                               # respiro
    cil(bm, Vector((0.0, 0, 0.125)), 0.06, 0.012, lados=20)
    cil(bm, Vector((0.0, 0, 0.16)), 0.07, 0.03, lados=20, r2=0.02)                     # chapéu
    for k in range(3):
        a = k * 2 * PI / 3
        viga(bm, Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.13)), Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.15)), 0.008)
    cil(bm, Vector((0.075, 0.03, 0.05)), 0.025, 0.06, lados=14)                         # válvula de alívio
    cil(bm, Vector((0.075, 0.03, 0.09)), 0.035, 0.02, lados=14)
    obj('apice_respiro', bm, 'grafite', apice)
    obj('apice_flange', bf, 'ferro', apice)
    obj('apice_parafusos', bp, 'aco', apice)
    # olho flutuante da IA (cristal pairando sobre o ápice) — mede a pressão sem tocar
    olho = vazio('olho_ia', (0, 0, 0.26), apice)
    bm = bmesh.new()                                                                   # cone de campo olho → escotilha
    cil(bm, Vector((0, 0, 0.13)), 0.11, 0.2, lados=32, r2=0.02)
    bmesh.ops.delete(bm, geom=[f_ for f_ in bm.faces if len(f_.verts) > 4], context='FACES')
    obj('olho_feixe', bm, 'pelicula_fraca', apice)
    bm, bc, be = bmesh.new(), bmesh.new(), bmesh.new()
    cil(be, Vector((0, 0, 0.03)), 0.035, 0.06, lados=6, r2=0.0)
    cil(be, Vector((0, 0, -0.025)), 0.035, 0.05, lados=6, r2=0.0)
    be.verts.ensure_lookup_table()
    toro(bc, Vector((0, 0, 0.0)), 0.075, 0.009, nR=40, nr=8)
    toro(bm, Vector((0, 0, 0.0)), 0.095, 0.006, nR=40, nr=6)
    for k in range(3):
        a = k * 2 * PI / 3
        caixa(bm, Vector((math.cos(a) * 0.095, math.sin(a) * 0.095, 0)), (0.03, 0.03, 0.03), Matrix.Rotation(a, 3, 'Z'))
    obj('olho_cristal', be, 'cristal', olho)
    obj('olho_bobina', bc, 'cobre', olho)
    obj('olho_aro', bm, 'grafite', olho)
    luz_o = bpy.data.lights.new('Olho', 'POINT')
    luz_o.color = VIOLETA
    luz_o.energy = 6.0
    luz_o.shadow_soft_size = 0.05
    lo = bpy.data.objects.new('Olho', luz_o)
    sc.collection.objects.link(lo)
    lo.parent = olho

    def f_domo(q, fr):
        s = 0.5 + 0.5 * math.sin(2 * PI * fr)                                          # 1 inflado, 0 murcho
        for k_ in (k_domo, k_cintas):
            k_.value = 1 - s
            k_.keyframe_insert('value', frame=q)
        apice.location = (T.x, T.y, ZD + 0.40 + 0.25 * s)
        chave(apice, 'location', q=q)
        olho.location = (0, 0, 0.26 + 0.02 * math.sin(2 * PI * 3 * fr))
        olho.rotation_euler = (0, 0, 2 * PI * fr)
        chave(olho, 'location', 'rotation_euler', q=q)
        luz_o.energy = 5 + 2 * math.sin(2 * PI * 4 * fr)
        luz_o.keyframe_insert('energy', frame=q)
    ANIM.append(f_domo)
    base3d.M['vapor_v'] = base3d.volume_mat('Vapor esverdeado', (0.55, 0.72, 0.38), 2.2, 1.2, 2.2)
    nuvem('vapor_apice', 'vapor_v', 3, lambda fr: apice.location + Z * 0.2 + Vector((0, 0, 0)), 0.55, 0.05, 0.2,
          Vector((0.25, 0.1, 0)))

    # ---------------------------------------------------------- tanque de mistura aberto com agitador
    CP, RP, ZP, ZL = Vector((-0.85, -0.88, 0)), 0.42, 0.52, 0.45
    tubo_oco(B('cinza', True), CP + Z * ((0.08 + ZP) / 2), RP, RP - 0.025, ZP - 0.08, Z, 56)
    cil(B('cinza', True), CP + Z * 0.1, RP + 0.02, 0.04, lados=56)
    for z in (0.18, 0.32, 0.46):
        toro(B('ferro', True), CP + Z * z, RP + 0.006, 0.01, nR=56, nr=8)
    toro(B('ferro', True), CP + Z * ZP, RP - 0.012, 0.016, nR=56, nr=8)                   # borda enrolada
    remendo(CP + Z * 0.3, Z, RP, math.radians(-150), math.radians(-120), 0.14)
    remendo(CP + Z * 0.38, Z, RP, math.radians(160), math.radians(190), 0.12, 'verde_tr')
    for k in range(16):                                                                # lama transbordando pela borda
        a = random.uniform(0, 2 * PI)
        escorrido_cil('escorrido', CP, RP + 0.005, a, ZP + 0.01, random.uniform(0.1, 0.4), random.uniform(0.02, 0.06), 0.006)
    for k in range(8):
        a = random.uniform(0, 2 * PI)
        escorrido_cil('ferrugem_esc', CP, RP + 0.014, a, random.choice((0.18, 0.32, 0.46)) - 0.01, random.uniform(0.05, 0.12), 0.015, 0.003)
    serie_cil(CP, RP + 0.002, -0.9, 0.25, 5, 0.04)
    cil(B('lodo_liq'), CP + Z * (ZL - 0.01), RP - 0.026, 0.02, lados=56)               # superfície da lama
    for k in range(12):                                                                # espuma marrom (placas + bolhas)
        a, r = random.uniform(0, 2 * PI), random.uniform(0.12, RP - 0.08)
        c0 = Vector((CP.x + math.cos(a) * r, CP.y + math.sin(a) * r, ZL))
        mancha(B('espuma_m'), (c0.x, c0.y), random.uniform(0.02, 0.05), ZL + 0.002)
        for j in range(random.randint(4, 9)):
            pedra(B('espuma_m'), c0 + Vector((random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), 0.004)),
                  random.uniform(0.006, 0.016), 0.55)
    toro(B('espuma_m'), CP + Z * (ZL + 0.002), RP - 0.04, 0.018, nR=56, nr=8)          # colar de espuma na parede
    for k in range(20):
        a, r = random.uniform(0, 2 * PI), random.uniform(0.1, RP - 0.06)
        pedra(B('lama'), (CP.x + math.cos(a) * r, CP.y + math.sin(a) * r, ZL + 0.004), random.uniform(0.01, 0.025), 0.4)
    # ponte do agitador (perfil I apoiado na borda) e motorredutor
    for sy in (-1, 1):
        caixa_de(B('amarelo'), (CP.x - RP - 0.04, CP.y + sy * 0.06 - 0.008, ZP + 0.01), (CP.x + RP + 0.04, CP.y + sy * 0.06 + 0.008, ZP + 0.11))
        caixa_de(B('amarelo'), (CP.x - RP - 0.04, CP.y + sy * 0.06 - 0.03, ZP + 0.11), (CP.x + RP + 0.04, CP.y + sy * 0.06 + 0.03, ZP + 0.125))
    for sx in (-1, 1):
        caixa_de(B('ferro'), (CP.x + sx * RP - 0.05, CP.y - 0.1, ZP - 0.06), (CP.x + sx * RP + 0.05, CP.y + 0.1, ZP + 0.01))
    caixa_de(B('ferro'), (CP.x - 0.1, CP.y - 0.1, ZP + 0.125), (CP.x + 0.1, CP.y + 0.1, ZP + 0.145))
    caixa_de(B('amarelo'), (CP.x - 0.08, CP.y - 0.08, ZP + 0.145), (CP.x + 0.08, CP.y + 0.08, ZP + 0.27))       # redutor
    cil(B('grafite', True), CP + Z * (ZP + 0.4), 0.075, 0.24, lados=28)                                     # motor
    for k in range(4):
        cil(B('grafite', True), CP + Z * (ZP + 0.31 + k * 0.05), 0.088, 0.014, lados=28)
    cil(B('grafite', True), CP + Z * (ZP + 0.54), 0.08, 0.05, lados=28, r2=0.06)
    caixa_de(B('grafite'), (CP.x + 0.07, CP.y - 0.04, ZP + 0.35), (CP.x + 0.13, CP.y + 0.04, ZP + 0.43))       # caixa de ligação
    serie(Vector((CP.x, CP.y - 0.081, ZP + 0.2)), -Y, -X, 4, 0.03)
    agit = vazio('agitador', (CP.x, CP.y, 0))
    bm, bm2 = bmesh.new(), bmesh.new()
    cil(bm, Vector((0, 0, (ZL - 0.05 + ZP + 0.125) / 2)), 0.022, ZP + 0.125 - ZL + 0.05, lados=14)
    cil(bm, Vector((0, 0, ZP + 0.06)), 0.045, 0.04, lados=14)                          # acoplamento com parafusos
    for k in range(6):
        a = k * PI / 3
        cil(bm2, Vector((math.cos(a) * 0.035, math.sin(a) * 0.035, ZP + 0.06)), 0.006, 0.05, lados=6)
    obj('agitador_eixo', bm, 'aco', agit)
    obj('agitador_parafusos', bm2, 'cromo', agit)
    bm = bmesh.new()                                                                   # redemoinho de espuma girando
    for k in range(3):
        pts = [Vector((math.cos(k * 2 * PI / 3 + t * 2.2) * (0.05 + t * 0.28), math.sin(k * 2 * PI / 3 + t * 2.2) * (0.05 + t * 0.28), ZL + 0.004))
               for t in (i / 14 for i in range(15))]
        mangueira(bm, pts, 0.012)
    obj('redemoinho', bm, 'espuma_m', agit)

    def f_agit(q, fr):
        agit.rotation_euler = (0, 0, -2 * PI * 4 * fr)
        chave(agit, 'rotation_euler', q=q)
    ANIM.append(f_agit)
    # borbulhas: crescem na superfície e estouram
    bolhas = []
    for k in range(14):
        bm = bmesh.new()
        esfera(bm, (0, 0, 0), 1.0, 14)
        o = obj('borbulha', bm, 'bolha_lodo')
        a, r = random.uniform(0, 2 * PI), random.uniform(0.06, RP - 0.08)
        bolhas.append((o, Vector((CP.x + math.cos(a) * r, CP.y + math.sin(a) * r, ZL)), random.random(), random.uniform(0.012, 0.03)))

    def f_bolhas(q, fr):
        for o, p, ph, rr in bolhas:
            u = (ph + fr * 3) % 1.0
            o.location = p
            sc_ = rr * (0.2 + 0.8 * u)
            o.scale = (sc_, sc_, sc_ * 0.8)
            o.hide_render = u > 0.92
            chave(o, 'location', 'scale', 'hide_render', q=q)
    ANIM.append(f_bolhas)
    base3d.M['vapor_v2'] = base3d.volume_mat('Vapor esverdeado baixo', (0.55, 0.72, 0.38), 1.6, 0.5, 1.3)
    nuvem('vapor_tanque', 'vapor_v2', 3, CP + Z * (ZL + 0.05), 0.7, 0.08, 0.3, Vector((0.2, 0.15, 0)))

    # ---------------------------------------------------------- entrada de água suja (porta sul, tile SO)
    RA = 0.065
    cano([(-1.0, -1.47, 0.3), (-1.0, -1.27, 0.3)], RA, fl_pontas=True)
    flange(Vector((-1.0, -1.47 + 0.011, 0.3)), Y, RA * 1.7, 0.022, 8)
    colar(Vector((-1.0, -1.29, 0.3)), Y, RA)
    atuador(Vector((-1.0, -1.37, 0.3)), Y, RA)

    # ---------------------------------------------------------- moega de resíduo e rosca transportadora inclinada
    H = Vector((-1.1, 0.88, 0))
    ZM0, ZM1 = 0.62, 1.02
    bm = bmesh.new()
    t0 = [(-0.3, -0.3), (0.3, -0.3), (0.3, 0.3), (-0.3, 0.3)]
    b0 = [(-0.09, -0.09), (0.09, -0.09), (0.09, 0.09), (-0.09, 0.09)]
    vb = [bm.verts.new((H.x + x, H.y + y, ZM0)) for x, y in b0]
    vt = [bm.verts.new((H.x + x, H.y + y, ZM1)) for x, y in t0]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    mo = obj('moega', bm, 'amarelo')
    sol = mo.modifiers.new('esp', 'SOLIDIFY')
    sol.thickness = 0.018
    for i in range(4):                                                                 # aro e nervuras
        j = (i + 1) % 4
        viga(B('ferro'), Vector((H.x + t0[i][0], H.y + t0[i][1], ZM1)), Vector((H.x + t0[j][0], H.y + t0[j][1], ZM1)), 0.03)
        viga(B('ferro'), Vector((H.x + t0[i][0] * 1.03, H.y + t0[i][1] * 1.03, ZM1 - 0.02)),
             Vector((H.x + b0[i][0] * 1.1, H.y + b0[i][1] * 1.1, ZM0 + 0.01)), 0.022)
    for sx in (-1, 1):                                                                 # pernas da moega
        for sy in (-1, 1):
            p_top = Vector((H.x + sx * 0.25, H.y + sy * 0.25, ZM1 - 0.08))
            viga(B('amarelo'), Vector((H.x + sx * 0.3, H.y + sy * 0.3, 0.08)), p_top, 0.04)
            caixa_de(B('ferro'), (H.x + sx * 0.3 - 0.05, H.y + sy * 0.3 - 0.05, 0.08), (H.x + sx * 0.3 + 0.05, H.y + sy * 0.3 + 0.05, 0.095))
    viga(B('amarelo'), Vector((H.x - 0.29, H.y - 0.3, 0.35)), Vector((H.x + 0.29, H.y - 0.3, 0.35)), 0.03)
    viga(B('amarelo'), Vector((H.x - 0.3, H.y - 0.29, 0.35)), Vector((H.x - 0.3, H.y + 0.29, 0.35)), 0.03)
    remendo_plano(Vector((H.x - 0.2, H.y, (ZM0 + ZM1) / 2 + 0.05)), Vector((-0.9, 0, -0.45)), -Y, 0.18, 0.12, 'cinza')
    serie(Vector((H.x, H.y - 0.215, 0.85)), Vector((0, -0.9, -0.43)), X, 5, 0.035)
    for k in range(5):
        escorrido_plano('escorrido', Vector((H.x - 0.2 + k * 0.1, H.y - 0.296, ZM1 - 0.01)), Vector((0, -0.9, -0.4)), random.uniform(0.08, 0.25), 0.03)
    # lixo na moega: monte de restos misturados
    for k in range(70):
        x, y = random.uniform(-0.26, 0.26), random.uniform(-0.26, 0.26)
        zz = ZM1 - 0.08 + 0.1 * (1 - (x * x + y * y) / 0.14) + random.uniform(-0.02, 0.02)
        m = random.choice(('lama', 'lama', 'folha', 'folha', 'galho', 'plastico', 'osso', 'lata'))
        if m == 'galho':
            a = random.uniform(0, PI)
            dd = Vector((math.cos(a), math.sin(a), random.uniform(-0.3, 0.3))) * random.uniform(0.06, 0.14)
            c = Vector((H.x + x, H.y + y, zz))
            tubo(B('galho'), c - dd, c + dd, random.uniform(0.006, 0.012), 6)
        elif m in ('lata', 'plastico'):
            caixa(B(m), Vector((H.x + x, H.y + y, zz)), (random.uniform(0.03, 0.08), random.uniform(0.02, 0.06), 0.006),
                  Matrix.Rotation(random.uniform(0, PI), 3, 'Z') @ Matrix.Rotation(random.uniform(-0.6, 0.6), 3, 'X'))
        else:
            pedra(B(m), (H.x + x, H.y + y, zz), random.uniform(0.02, 0.05), 0.5)
    # rosca: calha aberta em U, inclinada da boca da moega até sobre o tanque de mistura
    RA0 = Vector((H.x, H.y + 0.1, 0.40))
    RA1 = Vector((-0.95, -0.5, 0.95))
    U = (RA1 - RA0).normalized()
    L = (RA1 - RA0).length
    RR = 0.085
    s_, up_ = base_lat(U)
    chapa_arco(B('amarelo', True), (RA0 + RA1) / 2, U, RR + 0.004, 0.012, L, PI, 2 * PI, 20)
    for sg in (-1, 1):                                                                 # abas da calha
        p = (RA0 + RA1) / 2 + s_ * sg * (RR + 0.01) + up_ * 0.035
        caixa(B('amarelo'), p, (0.012, L, 0.075), Matrix((s_, U, up_)).transposed())
        caixa(B('ferro'), p + up_ * 0.04 + s_ * sg * 0.015, (0.04, L, 0.008), Matrix((s_, U, up_)).transposed())
    for k in range(6):                                                                 # anéis de reforço da calha
        p = RA0 + U * (0.1 + k * (L - 0.2) / 5)
        chapa_arco(B('ferro', True), p, U, RR + 0.016, 0.01, 0.025, PI - 0.25, 2 * PI + 0.25, 16)
    # tampa aparafusada sobre o primeiro trecho (sob a moega) — o resto fica aberto
    chapa_arco(B('verde_tr', True), RA0 + U * 0.43, U, RR + 0.03, 0.008, 0.36, 0.0, PI, 14)
    for k in range(4):
        for sg in (-1, 1):
            cil(B('aco'), RA0 + U * (0.28 + k * 0.1) + s_ * sg * (RR + 0.03) + up_ * 0.005, 0.008, 0.02, up_, lados=6)
    tg = (RA0.y - H.y) / -U.y                                                          # garganta da moega → calha
    pg_ = RA0 + U * tg
    caixa_de(B('amarelo'), (H.x - 0.095, H.y - 0.095, pg_.z + 0.05), (H.x + 0.095, H.y + 0.095, ZM0 + 0.01))
    for k in range(3):                                                                 # ferrugem da calha
        p = RA0 + U * (0.6 + k * 0.25) + s_ * (RR + 0.025) + up_ * 0.06
        escorrido_plano('ferrugem_esc', p, s_, 0.1, 0.02, 0.003)
    # tampa de fundo e mancais nas pontas
    for pp, sg in ((RA0, -1), (RA1, 1)):                                               # tampas de ponta em U
        chapa_arco(B('ferro', True), pp + U * sg * 0.01, U, 0.02, RR - 0.004, 0.02, PI, 2 * PI, 16)
        caixa(B('ferro'), pp + U * sg * 0.01 + up_ * 0.035, (2 * RR + 0.05, 0.02, 0.075), Matrix((s_, U, up_)).transposed())
        cil(B('ferro', True), pp + U * sg * 0.04, 0.04, 0.05, U, lados=16)          # mancal
    # motorredutor na ponta de baixo (atrás da moega)
    cil(B('amarelo', True), RA0 - U * 0.1, 0.075, 0.12, U, lados=24)
    cil(B('grafite', True), RA0 - U * 0.27, 0.065, 0.2, U, lados=24)
    for k in range(6):
        cil(B('grafite', True), RA0 - U * (0.2 + k * 0.03), 0.075, 0.007, U, lados=24)
    cil(B('grafite', True), RA0 - U * 0.39, 0.068, 0.04, -U, lados=24, r2=0.055)
    caixa(B('grafite'), RA0 - U * 0.27 + up_ * 0.08, (0.07, 0.07, 0.05), Matrix((s_, U, up_)).transposed())
    # pernas da rosca (cavaletes)
    for t in (0.45, 0.85):
        p = RA0 + U * (L * t) - up_ * (RR + 0.02)
        for sg in (-1, 1):
            viga(B('amarelo'), Vector((p.x + s_.x * sg * 0.08, p.y + s_.y * sg * 0.08, 0.08)), p + s_ * sg * 0.08, 0.035)
        caixa(B('ferro'), p, (0.22, 0.05, 0.02), Matrix((s_, U, up_)).transposed())
        for sg in (-1, 1):
            caixa_de(B('ferro'), (p.x + s_.x * sg * 0.08 - 0.045, p.y + s_.y * sg * 0.08 - 0.045, 0.08),
                     (p.x + s_.x * sg * 0.08 + 0.045, p.y + s_.y * sg * 0.08 + 0.045, 0.092))
    # bica de descarga até o tanque de mistura
    bica0 = RA1 - U * 0.08 - up_ * RR
    bica1 = Vector((bica0.x, CP.y + 0.25, ZP + 0.08))
    db = (bica1 - bica0)
    caixa(B('amarelo'), (bica0 + bica1) / 2, (0.15, 0.15, db.length), Matrix(base_de(db)).transposed())
    # hélice girando (parente: vazio com z local = eixo da rosca)
    rosca = vazio('rosca', RA0)
    rosca.rotation_mode = 'QUATERNION'
    q_rosca = U.to_track_quat('Z', 'Y')
    rosca.rotation_quaternion = q_rosca
    bm = bmesh.new()
    cil(bm, Vector((0, 0, L / 2)), 0.022, L, Z, lados=14)
    passo, nh = 0.13, int(L / 0.13 * 24)
    an = []
    for i in range(nh + 1):
        t = i / 24
        z = 0.03 + t * passo
        if z > L - 0.03:
            break
        a = t * 2 * PI
        d = Vector((math.cos(a), math.sin(a), 0))
        an.append([bm.verts.new(d * 0.02 + Z * z), bm.verts.new(d * (RR - 0.006) + Z * z),
                   bm.verts.new(d * (RR - 0.006) + Z * (z + 0.008)), bm.verts.new(d * 0.02 + Z * (z + 0.008))])
    for A, B_ in zip(an, an[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], A[j], B_[j], B_[i]))
    obj('rosca_helice', bm, 'aco', rosca)
    bm = bmesh.new()                                                                   # crosta de lama na hélice
    for k in range(25):
        z = random.uniform(0.1, L - 0.1)
        a = z / passo * 2 * PI + random.uniform(-0.3, 0.3)
        r = random.uniform(0.03, RR - 0.02)
        pedra(bm, Vector((math.cos(a) * r, math.sin(a) * r, z)), random.uniform(0.012, 0.022), 0.6)
    obj('rosca_crosta', bm, 'lama', rosca)

    def f_rosca(q, fr):
        rosca.rotation_quaternion = q_rosca @ Quaternion(Z, -2 * PI * 3 * fr)
        chave(rosca, 'rotation_quaternion', q=q)
    ANIM.append(f_rosca)
    # pedaços de resíduo caindo da bica
    caem = []
    for k in range(5):
        bm = bmesh.new()
        pedra(bm, (0, 0, 0), random.uniform(0.018, 0.03), 0.7)
        caem.append((obj('residuo_caindo', bm, random.choice(('lama', 'folha', 'lama'))), random.random(),
                     Vector((random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), 0))))

    def f_caem(q, fr):
        for o, ph, off in caem:
            u = (ph + fr * 2) % 1.0
            o.location = bica1 + off + Vector((0, -0.02 * u, -(bica1.z - ZL) * u * u))
            o.rotation_euler = (u * 6, u * 4, ph * 9)
            chave(o, 'location', 'rotation_euler', q=q)
    ANIM.append(f_caem)

    # ---------------------------------------------------------- bomba de cavidade progressiva (mistura → digestor)
    PX = -0.15
    xw = CP.x + math.sqrt(RP ** 2 - (-1.1 - CP.y) ** 2)
    cano([(xw - 0.03, -1.1, 0.2), (PX - 0.05, -1.1, 0.2)], 0.05, fl_pontas=False)        # sucção
    colar(Vector((xw + 0.012, -1.1, 0.2)), X, 0.05)
    cil(B('grafite', True), Vector((PX, -1.1, 0.2)), 0.085, 0.16, Y, lados=24)          # carcaça de sucção
    cil(B('cinza', True), Vector((PX, -0.9, 0.2)), 0.06, 0.26, Y, lados=24)             # estator
    for y in (-1.0, -0.82):
        flange(Vector((PX, y, 0.2)), Y, 0.08, 0.02, 8)
    cil(B('grafite', True), Vector((PX, -0.74, 0.2)), 0.075, 0.08, Y, lados=24)         # câmara de descarga
    cil(B('amarelo', True), Vector((PX, -1.24, 0.2)), 0.07, 0.1, Y, lados=24)           # redutor
    cil(B('grafite', True), Vector((PX, -1.38, 0.2)), 0.07, 0.17, Y, lados=24)          # motor
    for k in range(3):
        cil(B('grafite', True), Vector((PX, -1.33 - k * 0.045, 0.2)), 0.08, 0.012, Y, lados=24)
    caixa_de(B('grafite'), (PX - 0.04, -1.42, 0.27), (PX + 0.04, -1.34, 0.31))
    caixa_de(B('ferro'), (PX - 0.1, -1.46, 0.08), (PX + 0.1, -0.7, 0.11))                # base (skid)
    for y in (-1.38, -1.1, -0.9, -0.74):
        caixa_de(B('ferro'), (PX - 0.05, y - 0.03, 0.11), (PX + 0.05, y + 0.03, 0.14))
    serie(Vector((PX - 0.061, -0.9, 0.2)), -X, Y, 4, 0.025)
    cano([(PX, -0.74, 0.27), (PX, -0.74, 0.45), (PX, -0.31, 0.45)], 0.045)
    colar(Vector((PX, -0.33, 0.45)), Y, 0.045)
    manometro(Vector((PX, -0.6, 0.45 + 0.045)), Z, -X)
    poca((PX + 0.05, -0.95), 0.08, 'oleo')
    poca((PX - 0.02, -1.2), 0.06, 'lodo_liq')

    # ---------------------------------------------------------- trocador de calor (lama em laço; água quente do queimador)
    YE, ZE, RE = 1.31, 0.3, 0.11
    XE0, XE1 = -0.52, 0.4
    cil(B('oxido', True), Vector(((XE0 + XE1) / 2, YE, ZE)), RE, XE1 - XE0, X, lados=36)                  # casco
    for x in (XE0 - 0.04, XE1 + 0.04):
        cil(B('amarelo', True), Vector((x, YE, ZE)), RE + 0.005, 0.07, X, lados=36)                    # cabeçotes
        flange(Vector((x + (0.04 if x < 0 else -0.04), YE, ZE)), X, RE + 0.03, 0.022, 14)
        cil(B('amarelo', True), Vector((x + (-0.045 if x < 0 else 0.045), YE, ZE)), RE - 0.02, 0.02, X, lados=36)
    for x in (XE0 + 0.15, XE1 - 0.15):
        suporte(Vector((x, YE, ZE)), X, RE)
    remendo(Vector((-0.1, YE, ZE)), X, RE, math.radians(60), math.radians(120), 0.16, 'cinza')
    serie(Vector((0.15, YE - RE - 0.001, ZE + 0.02)), -Y, X, 6, 0.035)
    # laço de lama: cabeçote oeste → tanque; cabeçote leste → tanque
    cano([(XE0 - 0.09, YE, ZE), (XE0 - 0.18, YE, ZE), (XE0 - 0.18, 0.98, ZE), (-0.22, 0.98, ZE)], 0.045)
    colar(Vector((-0.225, 0.98, ZE)), X, 0.045)
    cano([(XE1 + 0.09, YE, ZE), (0.56, YE, ZE), (0.56, 1.06, ZE)], 0.045, fl_pontas=False)
    colar(Vector((0.56, 1.065, ZE)), Y, 0.045)
    # água quente: bocais em cima do casco até o queimador
    F = Vector((1.22, 1.18, 0))
    for x, z in ((XE1 - 0.1, 0.5), (XE0 + 0.1, 0.58)):
        cano([(x, YE, ZE + RE - 0.01), (x, YE, z), (F.x - 0.155, YE, z)], 0.03, 'cano_quente', fl_pontas=False)
        flange(Vector((x, YE, ZE + RE + 0.03)), Z, 0.05, 0.016, 6)
    manometro(Vector((0.7, YE, 0.58 + 0.03)), Z, -Y)

    # ---------------------------------------------------------- queimador e flare
    ZF = 2.0
    caixa_de(B('grafite'), (F.x - 0.15, F.y - 0.17, 0.08), (F.x + 0.15, F.y + 0.17, 0.66))
    for k in range(5):
        caixa_de(B('grafite'), (F.x + 0.15, F.y - 0.13 + k * 0.065, 0.42), (F.x + 0.155, F.y - 0.1 + k * 0.065, 0.62))
    caixa_de(B('ferro'), (F.x - 0.09, F.y - 0.178, 0.16), (F.x + 0.09, F.y - 0.17, 0.32))          # moldura do visor
    caixa_de(B('brasa'), (F.x - 0.065, F.y - 0.182, 0.185), (F.x + 0.065, F.y - 0.176, 0.295))     # fogo pelo visor
    for k in range(5):
        caixa_de(B('ferro'), (F.x - 0.065 + k * 0.03, F.y - 0.186, 0.185), (F.x - 0.06 + k * 0.03, F.y - 0.18, 0.295))
    serie(Vector((F.x + 0.02, F.y - 0.171, 0.5)), -Y, X, 4, 0.03)
    remendo_plano(Vector((F.x + 0.151, F.y + 0.05, 0.25)), X, Y, 0.14, 0.12, 'oxido')
    cil(B('queimado', True), F + Z * (0.66 + (ZF - 0.66) / 2), 0.055, ZF - 0.66, lados=24)        # chaminé do flare
    for z in (0.9, 1.3, 1.7):
        flange(F + Z * z, Z, 0.08, 0.02, 8)
    cil(B('queimado', True), F + Z * (ZF + 0.06), 0.09, 0.12, lados=28)                           # para-vento
    for k in range(12):
        a = k * PI / 6
        caixa(B('ferro'), F + Z * (ZF + 0.06) + Vector((math.cos(a), math.sin(a), 0)) * 0.092, (0.012, 0.02, 0.1),
              Matrix.Rotation(a, 3, 'Z'))
    tubo(B('aco'), F + Vector((0.08, 0.0, 0.7)), F + Vector((0.08, 0.0, ZF + 0.08)), 0.01, 8)       # linha do piloto
    for z in (1.0, 1.4, 1.8):
        viga(B('ferro'), F + Vector((0.055, 0, z)), F + Vector((0.09, 0, z)), 0.012)
    caixa(B('grafite'), F + Vector((0.12, 0.0, 0.75)), (0.06, 0.05, 0.08))                        # ignitor
    for sx in (-1, 1):                                                                            # escoras no teto do queimador
        for sy in (-1, 1):
            pe = F + Vector((sx * 0.12, sy * 0.14, 0.66))
            viga(B('amarelo'), pe + Z * 0.01, F + Vector((sx, sy, 0)).normalized() * 0.05 + Z * 1.25, 0.022)
            caixa_de(B('ferro'), (pe.x - 0.03, pe.y - 0.03, 0.66), (pe.x + 0.03, pe.y + 0.03, 0.675))
    for k in range(5):                                                                            # fuligem escorrida
        escorrido_cil('ferrugem_esc', F, 0.055, random.uniform(0, 2 * PI), ZF - 0.02, random.uniform(0.2, 0.6), 0.02, 0.003)
    # chama pequena
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    chama = obj('flare_chama', bm, 'fogo')
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.05)), 0.035, 0.1, lados=12, r2=0.004)
    miolo = obj('flare_miolo', bm, 'chama')
    miolo.location = F + Z * (ZF + 0.1)
    luz_f = bpy.data.lights.new('Chama', 'POINT')
    luz_f.color = (1.0, 0.5, 0.15)
    luz_f.shadow_soft_size = 0.06
    lf = bpy.data.objects.new('Chama', luz_f)
    sc.collection.objects.link(lf)
    lf.location = F + Z * (ZF + 0.2)
    base3d.M['fumaca'] = base3d.volume_mat('Fumaça do flare', (0.06, 0.06, 0.06), 1.2, ZF + 0.3, ZF + 1.0)
    nuvem('fumaca_flare', 'fumaca', 3, F + Z * (ZF + 0.3), 0.6, 0.06, 0.18, Vector((0.25, -0.1, 0)))

    def f_chama(q, fr):
        fl = 1 + 0.15 * math.sin(2 * PI * 7 * fr) + 0.08 * math.sin(2 * PI * 13 * fr + 1)
        chama.location = F + Z * (ZF + 0.2) + Vector((0.015 * math.sin(2 * PI * 5 * fr), 0, 0))
        chama.scale = (0.06 * fl, 0.06 * fl, 0.13 * fl)
        chave(chama, 'location', 'scale', q=q)
        miolo.scale = (1, 1, fl)
        chave(miolo, 'scale', q=q)
        luz_f.energy = 30 * fl
        luz_f.keyframe_insert('energy', frame=q)
    ANIM.append(f_chama)

    # ---------------------------------------------------------- linha de gás (amarela): anel → pote → corta-chama → queimador
    a = PI / 4
    g0 = T + Vector((math.cos(a), math.sin(a), 0)) * (RT - 0.01) + Z * 0.55
    g1 = T + Vector((math.cos(a), math.sin(a), 0)) * (RT + 0.14) + Z * 0.55
    RG = 0.035
    cano([g0, g1, Vector((g1.x, g1.y, 0.3)), Vector((g1.x, F.y, 0.3)), Vector((F.x - 0.15, F.y, 0.3))], RG, 'cano_gas',
         fl=False)
    flange(Vector((g1.x, g1.y, 0.45)), Z, RG * 1.6, 0.016, 6)
    flange(Vector((F.x - 0.165, F.y, 0.3)), X, RG * 1.7, 0.02, 8)
    colar(g0 + Vector((math.cos(a), math.sin(a), 0)) * 0.012, Vector((math.cos(a), math.sin(a), 0)), RG)
    cil(B('amarelo', True), Vector((g1.x, g1.y, 0.2)), 0.06, 0.16, lados=24)          # pote de condensado
    cil(B('amarelo', True), Vector((g1.x, g1.y, 0.12)), 0.06, 0.04, lados=24, r2=0.03)
    tubo(B('aco'), Vector((g1.x, g1.y, 0.1)), Vector((g1.x + 0.06, g1.y, 0.1)), 0.008, 8)
    cil(B('cano_gas', True), Vector(((g1.x + F.x - 0.15) / 2 + 0.03, F.y, 0.3)), 0.06, 0.1, X, lados=24)  # corta-chama
    for sx in (-1, 1):
        flange(Vector(((g1.x + F.x - 0.15) / 2 + 0.03 + sx * 0.055, F.y, 0.3)), X, 0.07, 0.016, 8)
    atuador(Vector((g1.x, (g1.y + F.y) / 2, 0.3)), Y, RG)
    manometro(Vector((g1.x, g1.y, 0.55 + RG)), Z, Vector((1, -1, 0)))
    poca((g1.x + 0.07, g1.y), 0.05, 'oleo')

    # ---------------------------------------------------------- saída do digestato → prensa de rosca → esteira (biomassa)
    YPR, ZPR, RPR = -0.95, 0.42, 0.1
    XP0, XP1 = 0.3, 1.0
    cano([(0.5, -0.37, 0.5), (0.5, -0.7, 0.5), (0.5, -0.7, 0.8), (0.5, YPR, 0.8), (0.5, YPR, 0.68)], 0.045)
    colar(Vector((0.5, -0.395, 0.5)), Y, 0.045)
    caixa_de(B('amarelo'), (0.42, YPR - 0.08, ZPR + 0.06), (0.58, YPR + 0.08, 0.66))                 # boca de entrada
    cil(B('amarelo', True), Vector((0.45, YPR, ZPR)), RPR + 0.01, 0.3, X, lados=32)                 # corpo de entrada
    cil(B('grafite', True), Vector((0.24, YPR, ZPR)), 0.075, 0.12, X, lados=24)                     # redutor
    cil(B('grafite', True), Vector((0.1, YPR, ZPR)), 0.065, 0.16, X, lados=24)                      # motor
    for k in range(5):
        cil(B('grafite', True), Vector((0.05 + k * 0.03, YPR, ZPR)), 0.075, 0.006, X, lados=24)
    # peneira: anéis + barras, com a pasta verde-escura dentro
    for x in (0.6, 0.7, 0.8, 0.9, 0.98):
        cil(B('ferro', True), Vector((x, YPR, ZPR)), RPR + 0.012, 0.016, X, lados=32)
    for k in range(16):
        a = k * 2 * PI / 16
        p = Vector((0, math.cos(a), math.sin(a))) * (RPR + 0.004)
        tubo(B('inox'), Vector((0.6, YPR, ZPR)) + p, Vector((0.98, YPR, ZPR)) + p, 0.005, 6)
    cil(B('biomassa'), Vector((0.79, YPR, ZPR)), RPR - 0.004, 0.38, X, lados=28)
    for k in range(10):
        a = random.uniform(-PI, 0)
        pedra(B('biomassa'), Vector((random.uniform(0.62, 0.96), YPR + math.cos(a) * RPR, ZPR + math.sin(a) * RPR)), 0.012, 0.6)
    flange(Vector((0.6, YPR, ZPR)), X, RPR + 0.03, 0.02, 10)
    cil(B('amarelo', True), Vector((1.02, YPR, ZPR)), 0.07, 0.05, X, lados=24, r2=0.035)            # cone de pressão
    # pistões do cone (camisa no anel, haste no cone)
    for sg in (-1, 1):
        a0 = Vector((0.9, YPR + sg * 0.14, ZPR + 0.06))
        caixa(B('ferro'), Vector((0.98, YPR + sg * 0.11, ZPR + 0.06)), (0.03, 0.07, 0.03))
        cil(B('amarelo', True), Vector((0.82, YPR + sg * 0.14, ZPR + 0.06)), 0.018, 0.14, X, lados=16)
        cil(B('cromo', True), Vector((0.93, YPR + sg * 0.14, ZPR + 0.06)), 0.008, 0.1, X, lados=10)
        viga(B('ferro'), Vector((0.75, YPR + sg * 0.14, ZPR + 0.06)), Vector((0.75, YPR + sg * 0.1, ZPR + 0.04)), 0.02)
        mangueira(B('borracha'), bezier((0.77, YPR + sg * 0.15, ZPR + 0.075), (0.74, YPR + sg * 0.2, ZPR + 0.2),
                                        (0.3, YPR + sg * 0.15, ZPR + 0.25), (0.24, YPR + sg * 0.05, ZPR + 0.075), 10), 0.007)
    # bandeja do líquido sob a peneira
    caixa_de(B('cinza'), (0.56, YPR - 0.14, 0.2), (1.0, YPR + 0.14, 0.215))
    for sg in (-1, 1):
        caixa_de(B('cinza'), (0.56, YPR + sg * 0.14 - 0.006, 0.215), (1.0, YPR + sg * 0.14 + 0.006, 0.27))
    caixa_de(B('cinza'), (0.554, YPR - 0.14, 0.215), (0.566, YPR + 0.14, 0.27))
    caixa_de(B('cinza'), (0.994, YPR - 0.14, 0.215), (1.006, YPR + 0.14, 0.27))
    caixa_de(B('lodo_liq'), (0.566, YPR - 0.134, 0.215), (0.994, YPR + 0.134, 0.25))
    for k in range(8):
        mancha(B('espuma_m'), (random.uniform(0.6, 0.95), YPR + random.uniform(-0.1, 0.1)), random.uniform(0.015, 0.04), 0.251)
    # gotejo da peneira para a bandeja
    gotas_p = []
    for k in range(8):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.008)
        gotas_p.append((obj('gota_prensa', bm, 'lodo_liq'), Vector((random.uniform(0.62, 0.96), YPR + random.uniform(-0.04, 0.04), ZPR - RPR)), random.random()))

    def f_gotas(q, fr):
        for o, p, ph in gotas_p:
            u = (ph + fr * 3) % 1.0
            o.location = p - Z * (p.z - 0.25) * u * u
            chave(o, 'location', q=q)
    ANIM.append(f_gotas)
    # pernas da prensa
    for x in (0.25, 0.5, 0.88):
        for sg in (-1, 1):
            viga(B('amarelo'), Vector((x, YPR + sg * 0.12, 0.08)), Vector((x, YPR + sg * 0.08, ZPR - 0.07)), 0.03)
        caixa_de(B('ferro'), (x - 0.04, YPR - 0.15, 0.08), (x + 0.04, YPR + 0.15, 0.095))
    serie(Vector((0.45, YPR - RPR - 0.012, ZPR + 0.03)), -Y, X, 5, 0.03)
    # esteira da biomassa até a borda leste
    XB0, XB1, ZB, WB = 0.96, 1.48, 0.24, 0.13
    for sg in (-1, 1):
        caixa_de(B('amarelo'), (XB0 - 0.05, YPR + sg * (WB + 0.01) - 0.01, ZB - 0.07), (XB1, YPR + sg * (WB + 0.01) + 0.01, ZB + 0.03))
        for x in (XB0 + 0.05, XB1 - 0.06):
            viga(B('amarelo'), Vector((x, YPR + sg * (WB + 0.01), 0.08)), Vector((x, YPR + sg * (WB + 0.01), ZB - 0.07)), 0.03)
    for k in range(6):
        cil(B('aco', True), Vector((XB0 + k * (XB1 - XB0 - 0.02) / 5, YPR, ZB - 0.015)), 0.025, 2 * WB, Y, lados=16)
    caixa_de(B('borracha'), (XB0 - 0.03, YPR - WB, ZB + 0.008), (XB1, YPR + WB, ZB + 0.016))
    caixa_de(B('borracha'), (XB0 - 0.03, YPR - WB, ZB - 0.05), (XB1, YPR + WB, ZB - 0.042))
    for k in range(8):
        x = XB0 + k * 0.065
        caixa_de(B('borracha'), (x, YPR - WB + 0.01, ZB + 0.016), (x + 0.008, YPR + WB - 0.01, ZB + 0.03))
    cil(B('grafite', True), Vector((XB1 - 0.06, YPR - WB - 0.07, ZB - 0.015)), 0.045, 0.1, Y, lados=20)     # motor da esteira
    for k in range(6):
        mancha(B('biomassa'), (random.uniform(XB0, XB1), YPR + random.uniform(-0.1, 0.1)), random.uniform(0.02, 0.05), ZB + 0.017)
    for k in range(6):
        poca((random.uniform(0.6, 1.4), YPR + random.uniform(-0.25, 0.25)), random.uniform(0.03, 0.07), 'biomassa')
    torroes = []
    for k in range(7):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        for v in bm.verts:
            v.co *= 1 + 0.2 * math.sin(v.co.x * 4 + k) * math.cos(v.co.y * 3 - k)
        o = obj('biomassa_torrao', bm, 'biomassa')
        for pg in o.data.polygons:
            pg.use_smooth = True
        torroes.append(o)

    def f_torroes(q, fr):
        for k, o in enumerate(torroes):
            u = (k / len(torroes) + fr) % 1.0
            x = XB0 + 0.08 + (XB1 - XB0 - 0.08) * u
            o.location = (x, YPR + 0.03 * math.sin(k * 2.3), ZB + 0.045)
            o.scale = (0.05, 0.04, 0.028)
            o.rotation_euler = (0, 0, k)
            o.hide_render = u > 0.97
            chave(o, 'location', 'scale', 'rotation_euler', 'hide_render', q=q)
    ANIM.append(f_torroes)
    # pasta saindo pelo cone (cordão extrudado pendendo sobre a esteira)
    pts = bezier((1.03, YPR, ZPR - 0.02), (1.08, YPR, ZPR - 0.05), (1.1, YPR, ZB + 0.12), (1.12, YPR, ZB + 0.04), 10)
    mangueira(B('biomassa'), pts, 0.028)
    nuvem('vapor_prensa', 'vapor_v2', 2, Vector((0.8, YPR, ZPR + 0.15)), 0.5, 0.06, 0.2, Vector((0.1, 0.2, 0)))

    # ---------------------------------------------------------- coluna de campo: líquido marrom → seiva âmbar
    S = Vector((1.25, -0.35, 0))
    ZS0, ZS1 = 0.3, 0.98
    cil(B('amarelo', True), S + Z * ((0.08 + ZS0) / 2), 0.15, ZS0 - 0.08, lados=36)
    cil(B('amarelo', True), S + Z * (ZS1 + 0.05), 0.15, 0.1, lados=36)
    cil(B('amarelo', True), S + Z * (ZS1 + 0.13), 0.15, 0.06, lados=36, r2=0.05)
    for z in (ZS0 + 0.01, ZS1 - 0.01):
        flange(S + Z * z, Z, 0.165, 0.02, 14)
    tubo_oco(B('vidro', True), S + Z * ((ZS0 + ZS1) / 2), 0.12, 0.112, ZS1 - ZS0 - 0.002, Z, 48)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        cil(B('cromo', True), S + Vector((math.cos(a), math.sin(a), 0)) * 0.145 + Z * ((ZS0 + ZS1) / 2), 0.007, ZS1 - ZS0 + 0.05, lados=8)
    base3d.M['seiva_col'] = grad_mat('Líquido virando seiva', 'Z', 0.48, 0.82, (0.07, 0.045, 0.02), (0.9, 0.42, 0.03),
                                     0.0, 0.25, 0.0, 1.6, SEIVA, 1.05)
    cil(B('seiva_col', True), S + Z * ((ZS0 + ZS1) / 2), 0.11, ZS1 - ZS0 - 0.004, lados=48)
    for z in (0.5, 0.62, 0.74):                                                        # anéis de campo (bobina + emissores)
        toro(B('cobre', True), S + Z * z, 0.14, 0.012, nR=48, nr=8)
        for k in range(3):
            a = k * 2 * PI / 3 + z * 4
            caixa(B('grafite'), S + Vector((math.cos(a), math.sin(a), 0)) * 0.155 + Z * z, (0.035, 0.035, 0.04), Matrix.Rotation(a, 3, 'Z'))
            cil(B('emissor'), S + Vector((math.cos(a), math.sin(a), 0)) * 0.175 + Z * z, 0.01, 0.012,
                Vector((math.cos(a), math.sin(a), 0)), lados=8)
    for z in (0.56, 0.68):
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0)), 1.0, 0.004, lados=48)
        p = obj('membrana_coluna', bm, 'pelicula')
        p.location = S + Z * z
        p.scale = (0.105, 0.105, 1)
    luz_c = bpy.data.lights.new('Coluna', 'POINT')
    luz_c.color = VIOLETA
    luz_c.energy = 8.0
    luz_c.shadow_soft_size = 0.1
    lc = bpy.data.objects.new('Coluna', luz_c)
    sc.collection.objects.link(lc)
    lc.location = S + Vector((-0.35, -0.1, 0.65))
    luz_s = bpy.data.lights.new('Seiva', 'POINT')
    luz_s.color = SEIVA
    luz_s.energy = 1.5
    ls = bpy.data.objects.new('Seiva', luz_s)
    sc.collection.objects.link(ls)
    ls.location = S + Vector((-0.3, 0.05, 0.9))
    bols = []
    for k in range(10):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.005, 0.009))
        bols.append((obj('bolha_seiva', bm, 'gota_seiva'), S + Vector((random.uniform(-0.07, 0.07), random.uniform(-0.07, 0.07), 0)), random.random()))

    def f_bols(q, fr):
        for o, p, ph in bols:
            u = (ph + fr * 2) % 1.0
            o.location = p + Z * (ZS0 + 0.05 + (ZS1 - ZS0 - 0.1) * u) + X * 0.01 * math.sin(u * 20 + ph * 9)
            chave(o, 'location', q=q)
        luz_c.energy = 5 * (0.85 + 0.15 * math.sin(2 * PI * 6 * fr))
        luz_c.keyframe_insert('energy', frame=q)
    ANIM.append(f_bols)
    serie(S + Vector((0, -0.151, 0.18)), -Y, X, 4, 0.03)
    # dreno da bandeja até a base da coluna
    cano([(0.78, YPR + 0.08, 0.205), (0.78, YPR + 0.08, 0.15), (0.78, -0.62, 0.15), (S.x, -0.62, 0.15), (S.x, S.y - 0.14, 0.15)],
         0.03, fl_pontas=False)
    # cano âmbar de seiva: topo da coluna → visor → borda leste (porta L, y = 0)
    RS = 0.045
    cano([S + Z * 1.15, S + Z * 1.25, Vector((S.x, 0.0, 1.25)), Vector((S.x, 0.0, 0.86))], RS, 'cano_seiva', fl_pontas=False)
    cano([Vector((S.x, 0.0, 0.5)), Vector((S.x, 0.0, 0.34)), Vector((1.47, 0.0, 0.34))], RS, 'cano_seiva', fl_pontas=False)
    flange(Vector((1.47 - 0.011, 0.0, 0.34)), X, RS * 1.7, 0.022, 8)
    # visor de vidro no trecho vertical (seiva correndo)
    for z in (0.5, 0.86):
        flange(Vector((S.x, 0.0, z)), Z, RS * 1.6, 0.02, 8)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), RS - 0.004, 0.34, Z, lados=24)
    vis = obj('visor_seiva', bm, 'fluxo')
    vis.location = (S.x, 0.0, 0.68)
    vis.rotation_euler = (PI, 0, 0)                                                    # z local para baixo = sentido do fluxo
    tubo_oco(B('visor', True), Vector((S.x, 0.0, 0.68)), RS + 0.004, RS - 0.002, 0.33, Z, 32)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        cil(B('cromo', True), Vector((S.x + math.cos(a) * 0.065, math.sin(a) * 0.065, 0.68)), 0.005, 0.36, lados=8)
    suporte(Vector((1.38, 0.0, 0.34)), X, RS)
    atuador(Vector((S.x, -0.17, 1.25)), Y, RS)
    for k in range(4):                                                                 # crosta e respingos de seiva
        mancha(B('gota_seiva'), (S.x + random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.1)), random.uniform(0.01, 0.025), 0.0815)

    # ---------------------------------------------------------- armário, eletrocalha e cabos
    cab0, cab1 = armario(Vector((-1.32, -0.05, 0)), 0.22, 0.3, 0.62, X)
    YC, XC0, XC1 = -0.6, -0.42, 0.66
    caixa_de(B('aco'), (XC0, YC - 0.04, 0.08), (XC1, YC + 0.04, 0.09))
    for s in (-1, 1):
        caixa_de(B('aco'), (XC0, YC + s * 0.04 - 0.003, 0.08), (XC1, YC + s * 0.04 + 0.003, 0.13))
    for x in (XC0 + 0.05, -0.05, 0.3, XC1 - 0.05):
        caixa_de(B('aco'), (x - 0.01, YC - 0.045, 0.125), (x + 0.01, YC + 0.045, 0.135))
    for k in range(3):
        tubo(B('borracha', True), Vector((XC0, YC + (k - 1) * 0.018, 0.105)), Vector((XC1, YC + (k - 1) * 0.018, 0.105)), 0.009, 8)
    for k in range(3):                                                                 # feixe do armário até a calha
        mangueira(B('borracha'), bezier(cab0 + Vector((0, 0.02 * k, 0)), cab0 + Vector((0.3, -0.1, -0.12)),
                                         Vector((-0.7, -0.4, 0.1)), Vector((XC0 + 0.01, YC + (k - 1) * 0.018, 0.105)), 14), 0.009)
    for t in (0.3, 0.6):
        p = bez(cab0, cab0 + Vector((0.3, -0.1, -0.12)), Vector((-0.7, -0.4, 0.1)), Vector((XC0, YC, 0.105)), t)
        caixa(B('aco'), Vector((p.x, p.y, 0.09)), (0.05, 0.05, 0.02))
    cabos = [
        bezier((XC0 + 0.03, YC + 0.02, 0.11), (XC0 - 0.1, YC - 0.05, 0.4), (CP.x + 0.15, CP.y + 0.3, ZP + 0.6), (CP.x + 0.1, CP.y, ZP + 0.39), 14),
        bezier((PX + 0.06, YC - 0.02, 0.11), (PX + 0.15, -0.8, 0.12), (PX + 0.13, -1.38, 0.2), (PX + 0.07, -1.38, 0.24), 14),
        bezier((0.2, YC - 0.02, 0.11), (0.2, -0.75, 0.15), (0.12, YPR + 0.1, 0.3), (0.1, YPR, ZPR + 0.06), 14),
        bezier((XC1, YC - 0.02, 0.11), (0.95, -0.66, 0.1), (XB1 - 0.06, YPR - 0.3, 0.12), (XB1 - 0.06, YPR - WB - 0.12, ZB), 14),
        bezier((XC1, YC + 0.02, 0.11), (1.0, -0.5, 0.11), (S.x - 0.25, S.y, 0.4), (S.x - 0.165, S.y, 0.62), 14),
    ]
    rm = RA0 - U * 0.27 + up_ * 0.1
    cabos.append(bezier(cab0 + Vector((0, 0.1, 0.2)), cab0 + Vector((-0.1, 0.4, 0.2)), (rm.x - 0.25, rm.y - 0.2, rm.z + 0.25), rm, 16))
    for pts in cabos:
        mangueira(B('borracha'), pts, 0.011)
    fios(cab1, cab1 + Vector((0.15, 0.1, -0.25)))
    # sujeira geral da laje
    for k in range(10):
        poca((random.uniform(-1.4, -0.3), random.uniform(-1.4, -0.4)), random.uniform(0.03, 0.09), 'lodo_liq')
    for k in range(8):
        poca((T.x + math.cos(k) * (RT + 0.12), T.y + math.sin(k) * (RT + 0.12)), random.uniform(0.04, 0.09), 'escorrido')
    for k in range(10):
        mancha(B('lama_seca'), (random.uniform(-1.45, 1.4), random.uniform(-1.45, 1.4)), random.uniform(0.03, 0.08), 0.0812)
    for k in range(6):
        x, y = random.uniform(-1.4, -0.7), random.uniform(0.3, 1.4)
        pedra(B(random.choice(('folha', 'lama', 'plastico'))), (x, y, 0.09), random.uniform(0.012, 0.025), 0.4)
    for c, r in (((-0.95, 0.0), 0.06), ((0.1, YPR), 0.08), ((F.x, F.y - 0.25), 0.07)):
        poca(c, r, 'oleo')
    fechar_pool('bio')
    return dict(alvo=Vector((0.15, 0.05, 0.6)), cam0=((3.4, -3.7, 2.7), (0.1, 0.0, 0.55), 32),
                perto=((-1.75, -2.35, 1.55), (-0.45, -0.35, 0.62), 30))


# ================================================================== ESTAÇÃO DE TRATAMENTO
def construir_tratamento():
    base3d.M['terra'] = terra_mat()
    Z_RIO = -0.35
    YC_ = -1.48                                                                       # face do cais
    X_OUT, Y_JATO = 1.2, -1.66
    base3d.M['rio'] = rio_mat(0.7, 3.4, X_OUT, -2.2)
    base3d.M['agua_limpa'] = grad_mat('Água límpida', 'Z', 0.25, 0.54, (0.45, 0.66, 0.64), (0.7, 0.9, 0.9), 0.8, 0.96,
                                      0.0, 0.08, (0.75, 0.92, 1.0), 1.33)
    base3d.M['agua_aera'] = liquido_mat('Água em aeração', (0.2, 0.17, 0.11), rough=0.25, bump=0.5, escala=14.0)
    base3d.M['agua_turva'] = liquido_mat('Água turva', (0.15, 0.1, 0.045), rough=0.1, bump=0.2)
    base3d.M['agua_uv'] = liquido_mat('Água do canal UV', (0.78, 0.92, 0.95), rough=0.03, transm=0.92, forca=0.12,
                                      emis=(0.7, 0.85, 1.0), bump=0.12)
    base3d.M['lampada_uv'] = emissivo('Lâmpada UV', (0.5, 0.32, 1.0), 9.0)
    base3d.M['lodo_fundo'] = lodo_mat('Lodo do fundo', (0.06, 0.04, 0.02), (0.13, 0.09, 0.045), 0.35, escala=8.0, bump=0.6)
    base3d.M['pluma'] = mancha_limpa_mat()
    base3d.M['pelicula_dec'] = pelicula_mat('Campo do decantador', (0.5, 0.2, 1.0), 0.15, 0.55, 0.3, 1.8, 30.0)
    base3d.M['pelicula_dec2'] = pelicula_mat('Campo tênue', (0.5, 0.2, 1.0), 0.02, 0.12, 0.1, 0.8, 50.0)
    base3d.M['escuma'] = lodo_mat('Escuma', (0.1, 0.075, 0.04), (0.17, 0.13, 0.07), 0.5, escala=12.0, bump=0.5)
    base3d.M['nevoa'] = base3d.volume_mat('Névoa', (0.85, 0.88, 0.9), 2.5, -0.4, 0.4)
    laje(('L',))

    # ---------------------------------------------------------- cais, margem e rio
    caixa_de(B('concreto'), (-1.5, YC_ - 0.08, -0.9), (1.5, YC_, 0.08))
    for sx in (-1, 1):
        caixa_de(B('concreto'), (sx * 1.5 if sx > 0 else -1.59, -1.95, -0.9), (1.59 if sx > 0 else -1.5, YC_, 0.06))
    for x in (-0.35, 0.35):
        caixa_de(B('concreto'), (x - 0.05, YC_ - 0.13, -0.9), (x + 0.05, YC_ - 0.08, 0.0))
    caixa_de(B('alga'), (-1.5, YC_ - 0.083, Z_RIO - 0.12), (0.6, YC_ - 0.081, Z_RIO + 0.1))      # limo só a montante
    for k in range(18):
        x = random.uniform(-1.45, 0.5)
        caixa_de(B('alga'), (x - 0.01, YC_ - 0.0825, Z_RIO + 0.05), (x + 0.01, YC_ - 0.0812, Z_RIO + random.uniform(0.12, 0.32)))
    caixa_de(B('escorrido'), (0.6, YC_ - 0.083, Z_RIO - 0.05), (1.5, YC_ - 0.081, Z_RIO + 0.03))   # a jusante: linha fina

    def altura(x, y):
        if y > YC_:
            return 0.03 * math.sin(x * 1.7) * math.cos(y * 2.1) if (abs(x) > 1.65 or y > 1.65) else 0.0
        if abs(x) < 1.54:
            return -0.9
        t = min(1.0, (YC_ - y) / 1.1)
        return -0.9 * t * t * (3 - 2 * t) + 0.03 * math.sin(x * 3.1) * (1 - t)

    bm = bmesh.new()
    xs = [-80, -50, -30, -20, -14, -10, -8, -6] + [i * 0.2 - 5.4 for i in range(55)] + [6, 8, 10, 14, 20, 30, 50, 80]
    vs = [[bm.verts.new((x, y, altura(x, y))) for x in xs] for y in xs]
    for j in range(len(xs) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    suavizar(obj('margem', bm, 'terra'))
    bm = bmesh.new()
    caixa_de(bm, (-80, -80, Z_RIO - 0.02), (80, YC_ - 0.08, Z_RIO))
    obj('rio', bm, 'rio')
    bm, bm2 = bmesh.new(), bmesh.new()
    for k in range(80):
        sx = random.choice((-1, 1))
        x = sx * random.uniform(1.62, 3.4)
        y = random.uniform(-2.3, -1.52)
        pedra(bm, (x, y, altura(x, y) + 0.03), random.uniform(0.05, 0.13), 0.55)
    for k in range(45):                                                               # seixos no fundo limpo (aparecem)
        x, y = random.uniform(0.6, 5.0), random.uniform(-4.5, -1.7)
        pedra(bm2, (x, y, altura(x, y) + 0.02), random.uniform(0.04, 0.12), 0.5)
    for k in range(30):
        x, y = random.uniform(-3.5, 3.5), random.uniform(1.65, 4.0)
        pedra(bm2, (x, y, altura(x, y)), random.uniform(0.02, 0.06), 0.5)
    for o in (obj('enrocamento', bm, 'pedra'), obj('pedras', bm2, 'pedra')):
        o.modifiers.new('sub', 'SUBSURF').levels = 1
        for pg in o.data.polygons:
            pg.use_smooth = True
    for k in range(50):                                                               # juncos
        sx = random.choice((-1, 1))
        x0 = sx * random.uniform(1.65, 3.2)
        y0 = random.uniform(-2.0, -1.6)
        base = Vector((x0, y0, max(altura(x0, y0), Z_RIO) - 0.02))
        for j in range(5):
            top = base + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), random.uniform(0.25, 0.55)))
            cil(B('palha'), (base + top) / 2, 0.004, (top - base).length, top - base, lados=4, r2=0.001)
    for k in range(30):                                                               # plantas d'água voltando a jusante
        x0, y0 = random.uniform(1.0, 4.5), random.uniform(-3.5, -1.8)
        base = Vector((x0, y0, -0.89))
        for j in range(3):
            pts = bezier(base, base + Vector((0.05, 0.0, 0.2)), base + Vector((0.18, random.uniform(-0.05, 0.05), 0.35)),
                         base + Vector((0.3, random.uniform(-0.08, 0.08), 0.48)), 6)
            mangueira(B('alga'), pts, 0.006)
    for k in range(40):                                                               # escuma e lixo boiando a montante
        c = (random.uniform(-5.0, 0.8), random.uniform(-4.5, -1.62))
        if k % 2:
            mancha(B('escuma'), c, random.uniform(0.03, 0.1), Z_RIO + 0.002)
    for k in range(10):
        c = Vector((random.uniform(-4.5, 0.5), random.uniform(-3.5, -1.7), Z_RIO + 0.005))
        a = random.uniform(0, PI)
        d = Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.15, 0.4)
        tubo(B('galho'), c - d, c + d, 0.012, 6)
    for k in range(6):
        c = Vector((random.uniform(-4.0, 0.0), random.uniform(-3.0, -1.8), Z_RIO + 0.004))
        caixa(B('plastico'), c, (random.uniform(0.06, 0.14), random.uniform(0.04, 0.08), 0.01), Matrix.Rotation(random.uniform(0, PI), 3, 'Z'))

    # ---------------------------------------------------------- tomada d'água a montante: câmara de grade + bomba vertical
    TX0, TX1, TY0, TY1 = -1.18, -0.72, YC_ - 0.34, YC_ - 0.08
    XT, YT = (TX0 + TX1) / 2, (TY0 + TY1) / 2
    for x, y in ((TX0, TY0), (TX1, TY0)):
        caixa_de(B('amarelo'), (x - 0.025, y - 0.025, -0.9), (x + 0.025, y + 0.025, 0.08))
    for z in (0.04, -0.14, -0.55):
        caixa_de(B('amarelo'), (TX0 - 0.02, TY0 - 0.02, z - 0.015), (TX1 + 0.02, TY0, z + 0.015))
        for x in (TX0, TX1):
            caixa_de(B('amarelo'), (x - 0.02, TY0, z - 0.015), (x + 0.02, TY1, z + 0.015))
    for k in range(13):
        x = TX0 + (TX1 - TX0) * k / 12
        caixa_de(B('ferro'), (x - 0.006, TY0 - 0.006, -0.88), (x + 0.006, TY0 + 0.006, 0.05))
    for k in range(1, 6):
        y = TY0 + (TY1 - TY0) * k / 6
        for x in (TX0, TX1):
            caixa_de(B('ferro'), (x - 0.006, y - 0.006, -0.88), (x + 0.006, y + 0.006, 0.05))
    caixa_de(B('ferro'), (TX0 - 0.03, TY0 - 0.03, 0.05), (TX1 + 0.03, TY1 + 0.0, 0.08))      # tampa da câmara
    caixa_de(B('agua_turva'), (TX0, TY0, Z_RIO - 0.3), (TX1, TY1, Z_RIO + 0.004))
    for k in range(10):
        x = random.uniform(TX0 - 0.02, TX1 + 0.02)
        c = Vector((x, TY0 - 0.02, Z_RIO + 0.01))
        a = random.uniform(-0.4, 0.4)
        d = Vector((math.cos(a), 0, math.sin(a) * 0.4)) * random.uniform(0.08, 0.2)
        tubo(B('galho'), c - d, c + d, random.uniform(0.006, 0.012), 6)
    for k in range(16):
        pedra(B('lama'), (random.uniform(TX0, TX1), TY0 - 0.025, Z_RIO + random.uniform(-0.01, 0.04)), random.uniform(0.02, 0.045), 0.5)
    for k in range(10):
        pedra(B('folha'), (random.uniform(TX0, TX1), TY0 - 0.02, Z_RIO + random.uniform(0.0, 0.05)), random.uniform(0.015, 0.03), 0.3)
    cil(B('cano', True), Vector((XT, YT, (Z_RIO - 0.45 + 0.06) / 2)), 0.07, 0.06 - Z_RIO + 0.45, lados=24)   # coluna da bomba
    cil(B('cano', True), Vector((XT, YT, Z_RIO - 0.48)), 0.1, 0.06, lados=24, r2=0.07)
    cil(B('grafite', True), Vector((XT, YT, 0.17)), 0.1, 0.18, lados=28)                                # cabeçote
    flange(Vector((XT, YT, 0.09)), Z, 0.13, 0.02, 10)
    cil(B('amarelo', True), Vector((XT, YT, 0.3)), 0.075, 0.08, lados=24)                               # lanterna
    cil(B('grafite', True), Vector((XT, YT, 0.47)), 0.09, 0.26, lados=28)                               # motor
    for k in range(4):
        cil(B('grafite', True), Vector((XT, YT, 0.38 + k * 0.055)), 0.1, 0.014, lados=28)
    cil(B('grafite', True), Vector((XT, YT, 0.63)), 0.095, 0.06, lados=28, r2=0.06)
    caixa(B('grafite'), Vector((XT + 0.1, YT, 0.5)), (0.06, 0.08, 0.08))
    serie(Vector((XT, YT - 0.101, 0.2)), -Y, X, 4, 0.03)
    for k in range(5):
        escorrido_cil('ferrugem_esc', Vector((XT, YT)), 0.1, random.uniform(-PI, 0), 0.25, random.uniform(0.06, 0.14), 0.015, 0.003)
    # recalque da tomada até o tanque de aeração
    A0, A1 = Vector((-1.40, -1.15, 0)), Vector((-0.24, 0.05, 0))
    ZA, ZAG = 0.52, 0.45
    XR = XT + 0.28
    cano([(XT + 0.1, YT, 0.17), (XR, YT, 0.17), (XR, YT, 0.72), (XR, -1.0, 0.72), (XR, -1.0, 0.58)], 0.055, fl_pontas=False)
    atuador(Vector((XR, -1.22, 0.72)), Y, 0.055)
    manometro(Vector((XR + 0.055, YT, 0.45)), X, X)
    caixa_de(B('amarelo'), (XR - 0.04, -1.38, 0.08), (XR + 0.04, -1.32, 0.66))
    chapa_arco(B('aco', True), Vector((XR, -1.35, 0.72)), Y, 0.057, 0.005, 0.03, math.radians(-15), math.radians(195), 16)

    # ---------------------------------------------------------- tanque de aeração (borbulhando)
    for (a, b) in (((A0.x, A0.y), (A1.x, A0.y + 0.06)), ((A0.x, A1.y - 0.06), (A1.x, A1.y)),
                   ((A0.x, A0.y), (A0.x + 0.06, A1.y)), ((A1.x - 0.06, A0.y), (A1.x, A1.y))):
        caixa_de(B('concreto_t'), (a[0], a[1], 0.08), (b[0], b[1], ZA))
    caixa_de(B('agua_aera'), (A0.x + 0.06, A0.y + 0.06, 0.1), (A1.x - 0.06, A1.y - 0.06, ZAG))
    for x in (A0.x, A1.x):
        for y in (A0.y, A1.y):
            caixa_de(B('ferro'), (x - 0.035, y - 0.035, ZA - 0.01), (x + 0.035, y + 0.035, ZA + 0.01))
    for k in range(10):                                                               # escorridos na parede de fora
        x = random.uniform(A0.x + 0.05, A1.x - 0.05)
        escorrido_plano('escorrido', Vector((x, A0.y, ZA)), -Y, random.uniform(0.08, 0.3), random.uniform(0.02, 0.05))
    for k in range(6):
        y = random.uniform(A0.y + 0.05, A1.y - 0.05)
        escorrido_plano('escorrido', Vector((A1.x, y, ZA)), X, random.uniform(0.08, 0.3), random.uniform(0.02, 0.05))
    caixa_de(B('alga'), (A0.x + 0.06, A0.y + 0.059, ZAG - 0.01), (A1.x - 0.06, A0.y + 0.061, ZAG + 0.03))
    serie(Vector(((A0.x + A1.x) / 2, A0.y - 0.001, 0.3)), -Y, X, 6, 0.05)
    # ar: soprador de lóbulos, silenciador, distribuidor e descidas
    XS, YS = 0.0, -0.45
    caixa_de(B('ferro'), (XS - 0.13, YS - 0.42, 0.08), (XS + 0.13, YS + 0.17, 0.11))
    caixa_de(B('amarelo'), (XS - 0.1, YS - 0.1, 0.11), (XS + 0.1, YS + 0.1, 0.33))                   # carcaça dos lóbulos
    for sg in (-1, 1):
        cil(B('amarelo', True), Vector((XS + sg * 0.1, YS, 0.22)), 0.07, 0.02, X, lados=20)
    cil(B('grafite', True), Vector((XS, YS - 0.26, 0.2)), 0.08, 0.2, Y, lados=24)                    # motor
    for k in range(3):
        cil(B('grafite', True), Vector((XS, YS - 0.2 - k * 0.05, 0.2)), 0.09, 0.012, Y, lados=24)
    caixa(B('amarelo'), Vector((XS, YS - 0.13, 0.2)), (0.12, 0.05, 0.12))                             # proteção da correia
    cil(B('cinza', True), Vector((XS, YS + 0.32, 0.4)), 0.085, 0.5, lados=24)                         # silenciador / filtro
    cil(B('cinza', True), Vector((XS, YS + 0.32, 0.68)), 0.11, 0.06, lados=24, r2=0.08)
    for k in range(10):
        a = k * PI / 5
        caixa(B('ferro'), Vector((XS + math.cos(a) * 0.09, YS + 0.32 + math.sin(a) * 0.09, 0.6)), (0.01, 0.01, 0.06))
    cano([(XS, YS + 0.1, 0.22), (XS, YS + 0.32, 0.22), (XS, YS + 0.32, 0.15)], 0.04, fl=False)
    caixa_de(B('ferro'), (XS - 0.07, YS + 0.25, 0.08), (XS + 0.07, YS + 0.39, 0.15))
    XD = A1.x + 0.07
    cano([(XS - 0.1, YS, 0.22), (XD, YS, 0.22), (XD, YS, 0.62)], 0.04, fl_pontas=False)
    cano([(XD, -0.95, 0.62), (XD, -0.15, 0.62)], 0.045, fl_pontas=False)
    cil(B('cano', True), Vector((XD, -0.95, 0.62)), 0.05, 0.02, Y, lados=20)
    cil(B('cano', True), Vector((XD, -0.15, 0.62)), 0.05, 0.02, Y, lados=20)
    esfera(B('cano', True), Vector((XD, YS, 0.62)), 0.046, 20)
    manometro(Vector((XD + 0.045, -0.75, 0.62)), X, X)
    for y in (-0.6, -0.3):
        caixa_de(B('amarelo'), (XD - 0.03, y - 0.03, 0.08), (XD + 0.03, y + 0.03, 0.62 - 0.045))
    DESC = []
    for y in (-0.9, -0.55, -0.2):
        cano([(XD, y, 0.62), (A0.x + 0.03, y, 0.62)], 0.03, fl=False)
        esfera(B('cano', True), Vector((XD, y, 0.62)), 0.04, 16)
        cil(B('cano', True), Vector((A0.x + 0.03, y, 0.62)), 0.035, 0.015, X, lados=16)
        caixa_de(B('ferro'), (A0.x + 0.01, y - 0.04, ZA), (A0.x + 0.05, y + 0.04, 0.62 - 0.03))
        for x in (-0.55, -0.9, -1.22):
            cano([(x, y, 0.62), (x, y, 0.18)], 0.018, fl=False)
            flange(Vector((x, y, 0.56)), Z, 0.03, 0.012, 4)
            esfera(B('cano', True), Vector((x, y, 0.62)), 0.032, 14)
            DESC.append(Vector((x, y)))
    # espuma branca e escuma marrom por cima das descidas
    for p in DESC:
        for j in range(26):
            a, r = random.uniform(0, 2 * PI), 0.11 * math.sqrt(random.random())
            pedra(B('espuma'), (p.x + math.cos(a) * r, p.y + math.sin(a) * r, ZAG + 0.004), random.uniform(0.007, 0.017), 0.6)
        mancha(B('espuma'), (p.x, p.y), 0.09, ZAG + 0.002)
    for k in range(10):
        mancha(B('espuma_m'), (random.uniform(A0.x + 0.12, A1.x - 0.12), random.choice((A0.y + 0.12, A1.y - 0.12))),
               random.uniform(0.04, 0.08), ZAG + 0.0025)
    bolhas = []
    for k in range(60):
        bm = bmesh.new()
        esfera(bm, (0, 0, 0), 1.0, 12)
        p = random.choice(DESC)
        bolhas.append((obj('bolha_aeracao', bm, 'bolha_agua'),
                       Vector((p.x + random.uniform(-0.1, 0.1), p.y + random.uniform(-0.08, 0.08), ZAG)), random.random(),
                       random.uniform(0.008, 0.02)))

    def f_bolhas(q, fr):
        for o, p, ph, rr in bolhas:
            u = (ph + fr * 4) % 1.0
            o.location = p + Z * (0.012 * math.sin(u * PI))
            sc_ = rr * (0.3 + 0.7 * math.sin(u * PI))
            o.scale = (sc_, sc_, sc_ * 0.8)
            o.hide_render = u > 0.95
            chave(o, 'location', 'scale', 'hide_render', q=q)
    ANIM.append(f_bolhas)
    base3d.M['vapor_a'] = base3d.volume_mat('Névoa da aeração', (0.8, 0.82, 0.78), 0.9, 0.45, 1.0)
    for p in DESC[::3]:
        nuvem('nevoa_aeracao', 'vapor_a', 2, Vector((p.x, p.y, ZAG + 0.05)), 0.4, 0.06, 0.16, Vector((0.12, 0.08, 0)))
    # transbordo do tanque de aeração para o decantador 1
    caixa_de(B('concreto'), (-0.95, A1.y, 0.3), (-0.69, A1.y + 0.1, ZA))
    cano([(-0.82, A1.y + 0.05, 0.3), (-0.82, A1.y + 0.05, 0.24), (-0.82, 0.31, 0.24)], 0.05, fl=False)
    colar(Vector((-0.82, 0.27, 0.24)), Y, 0.05)

    # ---------------------------------------------------------- decantadores circulares com ponte raspadora e campo
    RD_, RI_ = 0.56, 0.51
    ZDW, ZW, ZF_, ZLD = 0.6, 0.545, 0.37, 0.24
    JA0, JA1 = math.radians(-78), math.radians(-12)                                # janela de vidro (SE)
    base3d.M['lodo_campo'] = lodo_mat('Lodo separado', (0.05, 0.035, 0.018), (0.11, 0.075, 0.035), 0.3, escala=10.0, bump=0.7)
    pontes = []
    DEC = (Vector((-0.82, 0.84, 0)), Vector((0.82, 0.84, 0)))
    for idx, D in enumerate(DEC):
        arco_parede(B('concreto_t', True), D, RI_, RD_, 0.08, ZDW, JA1, JA0 + 2 * PI, 72)
        arco_parede(B('concreto_t', True), D, RI_, RD_, 0.08, 0.13, JA0, JA1, 14)
        arco_parede(B('concreto_t', True), D, RI_, RD_, ZDW - 0.05, ZDW, JA0, JA1, 14)
        arco_parede(B('vidro', True), D, RI_ + 0.012, RI_ + 0.022, 0.13, ZDW - 0.05, JA0, JA1, 24)
        for k in range(6):                                                         # montantes da janela
            a = JA0 + (JA1 - JA0) * k / 5
            dd = Vector((math.cos(a), math.sin(a), 0))
            caixa(B('ferro'), D + dd * (RI_ + 0.042) + Z * ((0.13 + ZDW - 0.05) / 2), (0.018, 0.025, ZDW - 0.18),
                  Matrix.Rotation(a, 3, 'Z'))
            for z in (0.16, 0.33, 0.52):
                cil(B('aco'), D + dd * (RI_ + 0.052) + Z * z, 0.007, 0.008, dd, lados=6)
        for z in (0.135, ZDW - 0.055):
            arco_parede(B('ferro', True), D, RI_ + 0.033, RI_ + 0.05, z - 0.01, z + 0.01, JA0, JA1, 20)
        arco_parede(B('ferro', True), D, RI_ - 0.004, RD_ + 0.008, ZDW, ZDW + 0.012, 0, 2 * PI, 96)
        for k in range(10):                                                        # escorridos do concreto
            a = random.uniform(JA1, JA0 + 2 * PI)
            escorrido_cil('escorrido', D, RD_, a, ZDW - 0.005, random.uniform(0.1, 0.35), random.uniform(0.02, 0.05))
        serie_cil(D, RD_ + 0.002, PI * 0.75 if idx == 0 else PI * 0.25, 0.35, 6, 0.05)
        # camadas: lodo no fundo, campo violeta, água límpida brilhando
        cil(B('lodo_campo', True), D + Z * ((0.08 + ZLD) / 2), RI_ - 0.002, ZLD - 0.08, lados=64)
        for k in range(24):
            a, r = random.uniform(0, 2 * PI), random.uniform(0.08, RI_ - 0.03)
            pedra(B('lodo_campo'), (D.x + math.cos(a) * r, D.y + math.sin(a) * r, ZLD), random.uniform(0.01, 0.022), 0.4)
        cil(B('agua_limpa', True), D + Z * ((ZLD + ZW) / 2), RI_ - 0.002, ZW - ZLD, lados=64)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0)), 1.0, 0.004, lados=64)
        pel = obj('campo_decantador', bm, 'pelicula_dec')
        pel.location = D + Z * ZF_
        pel.scale = (RI_ - 0.006, RI_ - 0.006, 1)
        bm = bmesh.new()                                                           # segunda película mais tênue (camada espessa)
        cil(bm, Vector((0, 0, 0)), 1.0, 0.004, lados=64)
        pel2 = obj('campo_decantador2', bm, 'pelicula_dec2')
        pel2.location = D + Z * (ZF_ + 0.03)
        pel2.scale = (RI_ - 0.01, RI_ - 0.01, 1)
        for k in range(30):                                                        # flocos presos no campo
            a, r = random.uniform(0, 2 * PI), random.uniform(0.15, RI_ - 0.05)
            pedra(B('lama'), (D.x + math.cos(a) * r, D.y + math.sin(a) * r, ZF_ + random.uniform(-0.01, 0.01)), random.uniform(0.005, 0.01), 0.6)
        luz = bpy.data.lights.new('Campo', 'POINT')
        luz.color = VIOLETA
        luz.energy = 3.0
        luz.shadow_soft_size = 0.3
        lo_ = bpy.data.objects.new('Campo', luz)
        sc.collection.objects.link(lo_)
        lo_.location = D + Z * (ZF_ + 0.04) + Vector((0.18, -0.18, 0))
        # vertedor periférico com dentes em V e calha
        arco_parede(B('aco', True), D, RI_ - 0.08, RI_ - 0.072, 0.44, ZW + 0.012, 0, 2 * PI, 72)
        for k in range(72):
            a = k * 2 * PI / 72
            dd = Vector((math.cos(a), math.sin(a), 0))
            caixa(B('aco'), D + dd * (RI_ - 0.076) + Z * (ZW + 0.02), (0.008, 0.02, 0.016), Matrix.Rotation(a, 3, 'Z'))
        # poço de alimentação no centro (água turva) e pilar
        tubo_oco(B('amarelo', True), D + Z * 0.5, 0.15, 0.14, 0.22, Z, 40)
        cil(B('agua_turva'), D + Z * (ZW - 0.002), 0.14, 0.01, lados=40)
        for k in range(10):
            a, r = random.uniform(0, 2 * PI), random.uniform(0.03, 0.12)
            mancha(B('espuma_m'), (D.x + math.cos(a) * r, D.y + math.sin(a) * r), random.uniform(0.015, 0.04), ZW + 0.005)
        cil(B('concreto', True), D + Z * 0.45, 0.06, 0.74, lados=20)
        caixa_de(B('amarelo'), (D.x - 0.08, D.y - 0.08, 0.82), (D.x + 0.08, D.y + 0.08, 0.93))        # redutor
        cil(B('grafite', True), D + Vector((0, 0, 1.03)), 0.06, 0.18, lados=24)                     # motor
        for k in range(3):
            cil(B('grafite', True), D + Vector((0, 0, 0.98 + k * 0.05)), 0.07, 0.012, lados=24)
        cil(B('lampada'), D + Vector((0, 0, 1.125)), 0.02, 0.012, lados=12)
        # emissores de campo na borda (cristal apontando para dentro)
        for k in range(4):
            a = JA1 + 0.5 + k * (2 * PI - (JA1 - JA0) - 1.0) / 3
            dd = Vector((math.cos(a), math.sin(a), 0))
            p = D + dd * (RD_ - 0.025) + Z * ZDW
            caixa(B('grafite'), p + Z * 0.05, (0.06, 0.06, 0.1), Matrix.Rotation(a, 3, 'Z'))
            toro(B('cobre', True), p + Z * 0.06 - dd * 0.04, 0.025, 0.006, -dd, nR=16, nr=6)
            cil(B('emissor'), p + Z * 0.06 - dd * 0.06, 0.016, 0.05, -dd + Z * -0.4, lados=6, r2=0.003)
        # ponte raspadora girando (duas mãos, centro → borda)
        ponte = vazio('ponte_%d' % idx, (D.x, D.y, 0))
        bm, bm2, bm3 = bmesh.new(), bmesh.new(), bmesh.new()
        cil(bm2, Vector((0, 0, 0.66)), 0.11, 0.06, lados=32)                              # anel giratório
        for k in range(36):
            a = k * 2 * PI / 36
            caixa(bm2, Vector((math.cos(a) * 0.115, math.sin(a) * 0.115, 0.7)), (0.012, 0.02, 0.016), Matrix.Rotation(a, 3, 'Z'))
        for sg in (-1, 1):
            for dy in (-0.035, 0.035):
                viga(bm, Vector((sg * 0.1, dy, 0.74)), Vector((sg * (RD_ + 0.01), dy, 0.70)), 0.018)    # banzo superior
                viga(bm, Vector((sg * 0.1, dy, 0.64)), Vector((sg * (RD_ + 0.01), dy, 0.645)), 0.018)    # banzo inferior
                for k in range(5):
                    x0 = sg * (0.1 + k * (RD_ - 0.1) / 5)
                    x1 = sg * (0.1 + (k + 1) * (RD_ - 0.1) / 5)
                    viga(bm, Vector((x0, dy, 0.64)), Vector((x1, dy, 0.735 - 0.04 * (k + 1) / 5)), 0.01)
                    viga(bm, Vector((x1, dy, 0.643)), Vector((x1, dy, 0.735 - 0.04 * (k + 1) / 5)), 0.01)
            caixa(bm, Vector((sg * (RD_ + 0.01), 0, 0.665)), (0.08, 0.11, 0.05))           # carro da roda na borda
            cil(bm3, Vector((sg * (RD_ - 0.025), 0, ZDW + 0.025)), 0.025, 0.03, Y, lados=16)
            for x in (0.25, 0.42):                                                         # raspadores até o lodo
                viga(bm, Vector((sg * x, 0, 0.64)), Vector((sg * x, 0, ZLD + 0.05)), 0.014)
                caixa(bm, Vector((sg * x, 0.04 * sg, ZLD + 0.04)), (0.012, 0.16, 0.05), Matrix.Rotation(0.5 * sg, 3, 'Z'))
            viga(bm, Vector((sg * 0.38, -0.03, 0.64)), Vector((sg * 0.38, -0.07, ZW + 0.01)), 0.012)   # escumadeira
            caixa(bm, Vector((sg * 0.38, -0.07, ZW + 0.01)), (0.14, 0.012, 0.03))
            for x in (0.2, 0.35):                                                          # emissores do braço
                cil(bm3, Vector((sg * x, 0, 0.625)), 0.016, 0.02, lados=12)
                toro(bm3, Vector((sg * x, 0, 0.61)), 0.018, 0.004, nR=12, nr=6)
        obj('ponte_trelica', bm, 'amarelo', ponte)
        obj('ponte_anel', bm2, 'ferro', ponte)
        obj('ponte_rodas', bm3, 'borracha', ponte)
        bm = bmesh.new()
        for sg in (-1, 1):
            for x in (0.2, 0.35):
                cil(bm, Vector((sg * x, 0, 0.608)), 0.008, 0.012, lados=6)
        obj('ponte_cristais', bm, 'cristal', ponte)
        pontes.append(ponte)

    def f_pontes(q, fr):
        for k, p in enumerate(pontes):
            p.rotation_euler = (0, 0, PI * fr * (1 if k == 0 else -1) + k * 0.6)
            chave(p, 'rotation_euler', q=q)
    ANIM.append(f_pontes)
    # tubulação entre os decantadores e para os filtros
    D1, D2 = DEC
    caixa_de(B('concreto'), (D1.x + RD_ - 0.01, D1.y - 0.08, 0.3), (D1.x + RD_ + 0.1, D1.y + 0.08, ZDW - 0.03))   # caixa de saída D1
    cano([(D1.x + RD_ + 0.1, D1.y, 0.4), (D2.x - RD_ + 0.02, D2.y, 0.4)], 0.05, fl_pontas=False)
    colar(Vector((D2.x - RD_ - 0.012, D2.y, 0.4)), X, 0.05)
    flange(Vector((-0.12, D1.y, 0.4)), X, 0.085, 0.02, 8)
    flange(Vector((0.12, D1.y, 0.4)), X, 0.085, 0.02, 8)
    a = math.radians(-100)
    po = D2 + Vector((math.cos(a), math.sin(a), 0)) * (RD_ + 0.04)
    caixa(B('concreto'), Vector((po.x, po.y, 0.45)), (0.16, 0.1, 0.3), Matrix.Rotation(a + PI / 2, 3, 'Z'))   # caixa de saída D2
    F1, F2 = Vector((0.55, -0.22, 0)), Vector((1.08, -0.22, 0))
    ZF0, ZF1, RFL = 0.22, 0.92, 0.16
    YMS = 0.06
    cano([(po.x, po.y - 0.05, 0.42), (po.x, YMS, 0.42), (po.x, YMS, 1.16), (po.x, F1.y, 1.16)], 0.045, fl_pontas=False)
    cano([(F1.x, F1.y, 1.16), (F2.x, F2.y, 1.16)], 0.045, fl=False)
    for Fv in (F1, F2):
        esfera(B('cano', True), Vector((Fv.x, Fv.y, 1.16)), 0.045, 20)
        cano([(Fv.x, Fv.y, 1.16), (Fv.x, Fv.y, ZF1 + 0.08)], 0.04, fl=False)
    esfera(B('cano', True), Vector((po.x, F1.y, 1.16)), 0.05, 20)
    atuador(Vector((po.x, -0.1, 1.16)), Y, 0.045)

    # ---------------------------------------------------------- filtros de pressão
    for i, Fv in enumerate((F1, F2)):
        mat_f = 'amarelo' if i == 0 else 'oxido'
        cil(B(mat_f, True), Fv + Z * ((ZF0 + ZF1) / 2), RFL, ZF1 - ZF0, lados=40)
        cil(B(mat_f, True), Fv + Z * (ZF1 + 0.05), RFL, 0.1, lados=40, r2=0.06)
        cil(B(mat_f, True), Fv + Z * (ZF0 - 0.05), 0.06, 0.1, lados=40, r2=RFL)
        for z in (0.4, 0.75):
            cil(B('ferro', True), Fv + Z * z, RFL + 0.008, 0.025, lados=40)
        flange(Fv + Z * (ZF1 - 0.06), Z, RFL + 0.025, 0.022, 16)
        for k in range(4):
            a = k * PI / 2 + PI / 4
            dd = Vector((math.cos(a), math.sin(a), 0))
            viga(B('amarelo'), Fv + dd * 0.22 + Z * 0.08, Fv + dd * (RFL - 0.01) + Z * 0.3, 0.03)
            caixa_de(B('ferro'), (Fv.x + dd.x * 0.22 - 0.035, Fv.y + dd.y * 0.22 - 0.035, 0.08), (Fv.x + dd.x * 0.22 + 0.035, Fv.y + dd.y * 0.22 + 0.035, 0.095))
        # visor de nível
        caixa(B('ferro'), Fv + Vector((0, -RFL - 0.02, 0.6)), (0.04, 0.02, 0.5))
        caixa(B('agua_limpa'), Fv + Vector((0, -RFL - 0.031, 0.6)), (0.02, 0.004, 0.46))
        manometro(Fv + Vector((RFL * 0.7, -RFL * 0.7, ZF1 - 0.12)), Vector((0.7, -0.7, 0)), Vector((0.7, -0.7, 0)))
        serie_cil(Fv, RFL + 0.002, -PI / 2 - 0.5, 0.3, 5, 0.035)
        for k in range(5):
            escorrido_cil('ferrugem_esc', Fv, RFL, random.uniform(0, 2 * PI), 0.74, random.uniform(0.08, 0.25), 0.02, 0.003)
        caixa(B('grafite'), Fv + Vector((-RFL - 0.03, 0, 0.6)), (0.04, 0.07, 0.09))              # olho de turbidez
        cil(B('emissor'), Fv + Vector((-RFL - 0.052, 0, 0.6)), 0.012, 0.008, -X, lados=10)
    remendo(F2 + Z * 0.55, Z, RFL, math.radians(-120), math.radians(-70), 0.14, 'cinza')
    # saída inferior dos filtros → canal UV
    ZMB = 0.16
    for Fv in (F1, F2):
        cano([(Fv.x, Fv.y, ZMB), (Fv.x, -0.5, ZMB)], 0.035, fl=False)
    cano([(F2.x, -0.5, ZMB), (0.4, -0.5, ZMB), (0.4, -0.62, ZMB)], 0.045, fl=False)
    esfera(B('cano', True), Vector((F1.x, -0.5, ZMB)), 0.045, 20)
    atuador(Vector((0.8, -0.5, ZMB)), X, 0.045)

    # ---------------------------------------------------------- canal UV com lâmpadas em bainha de quartzo
    U0, U1 = Vector((0.28, -1.12, 0)), Vector((1.44, -0.62, 0))
    ZU, ZUA = 0.42, 0.36
    for (a, b) in (((U0.x, U0.y), (U1.x, U0.y + 0.05)), ((U0.x, U1.y - 0.05), (U1.x, U1.y)),
                   ((U0.x, U0.y), (U0.x + 0.05, U1.y)), ((U1.x - 0.05, U0.y), (U1.x, U1.y))):
        caixa_de(B('concreto_t'), (a[0], a[1], 0.08), (b[0], b[1], ZU))
    caixa_de(B('lodo_campo'), (U0.x + 0.05, U0.y + 0.05, 0.08), (U1.x - 0.05, U1.y - 0.05, 0.1))
    caixa_de(B('agua_uv'), (U0.x + 0.05, U0.y + 0.05, 0.1), (U1.x - 0.05, U1.y - 0.05, ZUA))
    colar(Vector((0.4, U1.y + 0.012, ZMB)), Y, 0.045)
    YU = (U0.y + U1.y) / 2
    camisas = []
    for i, xm in enumerate((0.55, 0.82, 1.09)):
        caixa_de(B('amarelo'), (xm - 0.1, U0.y - 0.02, ZU), (xm + 0.1, U1.y + 0.02, ZU + 0.03))          # travessa
        caixa_de(B('grafite'), (xm - 0.07, YU - 0.17, ZU + 0.03), (xm + 0.07, YU + 0.17, ZU + 0.13))     # caixa de reatores
        for k in range(5):
            caixa_de(B('grafite'), (xm - 0.075, YU - 0.15 + k * 0.07, ZU + 0.13), (xm + 0.075, YU - 0.14 + k * 0.07, ZU + 0.16))
        cil(B('luz_verde' if i != 1 else 'luz_vermelha'), Vector((xm, YU - 0.172, ZU + 0.1)), 0.01, 0.008, -Y, lados=10)
        serie(Vector((xm, YU - 0.171, ZU + 0.06)), -Y, X, 4, 0.022)
        for k in range(5):
            y = YU - 0.16 + k * 0.08
            for dx in (-0.04, 0.04):
                p = Vector((xm + dx, y, 0))
                tubo_oco(B('vidro', True), p + Z * ((0.13 + ZU + 0.03) / 2), 0.018, 0.014, ZU + 0.03 - 0.13, Z, 16)
                cil(B('lampada_uv'), p + Z * ((0.15 + ZU) / 2), 0.008, ZU - 0.15, lados=10)
                cil(B('ferro', True), p + Z * 0.125, 0.02, 0.012, lados=16)
        luz = bpy.data.lights.new('UV', 'POINT')
        luz.color = (0.5, 0.32, 1.0)
        luz.energy = 2.5
        luz.shadow_soft_size = 0.2
        lu = bpy.data.objects.new('UV', luz)
        sc.collection.objects.link(lu)
        lu.location = (xm, YU, 0.3)
        # anel limpador (sobe e desce) com pistão preso na travessa
        lim = vazio('limpador_%d' % i, (xm, YU, 0.2))
        bm = bmesh.new()
        for sx in (-1, 1):
            caixa_de(bm, (sx * 0.07 - 0.005, -0.19, -0.006), (sx * 0.07 + 0.005, 0.19, 0.006))
        for y in (-0.2, -0.12, -0.04, 0.04, 0.12, 0.2):
            caixa_de(bm, (-0.07, y - 0.004, -0.004), (0.07, y + 0.004, 0.004))
        for k in range(5):
            for dx in (-0.04, 0.04):
                toro(bm, Vector((dx, -0.16 + k * 0.08, 0.0)), 0.021, 0.005, nR=16, nr=6)
        obj('limpador', bm, 'cromo', lim)
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.0)), 0.006, 0.36, lados=10)
        h_ = obj('limpador_haste', bm, 'cromo', lim)
        h_.location = (0.085, 0.0, 0.18)
        caixa(bm := bmesh.new(), Vector((0.0, 0, 0.0)), (0.03, 0.02, 0.012))
        obj('limpador_braco', bm, 'ferro', lim).location = (0.08, 0.0, 0.0)
        cil(B('amarelo', True), Vector((xm + 0.085, YU, ZU + 0.17)), 0.018, 0.2, lados=16)        # camisa do pistão
        cil(B('ferro', True), Vector((xm + 0.085, YU, ZU + 0.27)), 0.022, 0.016, lados=16)
        mangueira(B('borracha'), bezier((xm + 0.1, YU, ZU + 0.25), (xm + 0.15, YU + 0.05, ZU + 0.35), (xm + 0.12, YU + 0.2, ZU + 0.2),
                                        (xm + 0.07, YU + 0.17, ZU + 0.1), 8), 0.007)
        camisas.append(lim)

    def f_limp(q, fr):
        for i, lim in enumerate(camisas):
            u = 0.5 - 0.5 * math.cos(2 * PI * (fr + i / 3))
            lim.location.z = 0.16 + 0.17 * u
            chave(lim, 'location', q=q)
    ANIM.append(f_limp)
    for k in range(4):
        escorrido_plano('escorrido', Vector((random.uniform(0.35, 1.4), U0.y, ZU)), -Y, random.uniform(0.08, 0.2), 0.03)
    # saída: comporta no fim do canal → porta leste (água limpa 60/s) e descarga no rio
    cano([(U1.x - 0.06, -0.87, 0.26), (1.475, -0.87, 0.26)], 0.045, fl=False)
    flange(Vector((1.475 - 0.011, -0.87, 0.26)), X, 0.075, 0.022, 8)
    colar(Vector((U1.x + 0.012, -0.87, 0.26)), X, 0.045)
    RJ = 0.06
    cano([(X_OUT, U0.y + 0.02, 0.24), (X_OUT, YC_ - 0.12, 0.24), (X_OUT, YC_ - 0.2, 0.16)], RJ, fl_pontas=False)
    colar(Vector((X_OUT, U0.y - 0.012, 0.24)), Y, RJ)
    atuador(Vector((X_OUT, -1.3, 0.24)), Y, RJ)
    cil(B('cano', True), Vector((X_OUT, YC_ - 0.225, 0.135)), 0.085, 0.07, Vector((0, -0.08, -0.08)), lados=24, r2=RJ)
    caixa_de(B('ferro'), (X_OUT - 0.08, YC_ - 0.06, 0.08), (X_OUT + 0.08, YC_ - 0.0, 0.18))
    manometro(Vector((X_OUT, -1.2, 0.24 + RJ)), Z, X)
    # jato de água limpa
    N_BOC = Vector((X_OUT, YC_ - 0.26, 0.095))
    V0 = Vector((0, -0.9, -0.6))

    def no_jato(t):
        return N_BOC + V0 * t + Vector((0, 0, -4.9 * t * t))
    T_CAI = (V0.z + math.sqrt(V0.z ** 2 + 19.6 * (N_BOC.z - Z_RIO))) / 9.8
    IMP = no_jato(T_CAI)
    bm = bmesh.new()
    NJ, LJ = 30, 20
    an = []
    for i in range(NJ + 1):
        t = T_CAI * i / NJ
        c = no_jato(t)
        tg = (no_jato(t + 0.001) - c).normalized()
        v = tg.cross(X).normalized()
        r = 0.05 + 0.03 * (i / NJ) ** 1.5
        an.append([bm.verts.new(c + (X * math.cos(a) + v * math.sin(a)) * r * (1 + 0.08 * math.sin(a * 3 + i)))
                   for a in (j * 2 * PI / LJ for j in range(LJ))])
    for A_, B_ in zip(an, an[1:]):
        for j in range(LJ):
            bm.faces.new((A_[j], A_[(j + 1) % LJ], B_[(j + 1) % LJ], B_[j]))
    o = obj('jato', bm, 'jato')
    for pg in o.data.polygons:
        pg.use_smooth = True
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.0)
    pl = obj('pluma', bm, 'pluma')
    pl.location = (IMP.x + 0.5, IMP.y - 0.25, Z_RIO + 0.003)
    pl.scale = (1.4, 0.8, 1)
    for k in range(16):
        a = random.uniform(0, 2 * PI)
        r = random.uniform(0.02, 0.16)
        mancha(B('espuma'), (IMP.x + math.cos(a) * r, IMP.y + math.sin(a) * r), random.uniform(0.03, 0.08), Z_RIO + 0.006)
    ondas = []
    for k in range(3):
        bm = bmesh.new()
        toro(bm, Vector((0, 0, 0)), 1.0, 0.007, Z, nR=48, nr=6)
        ondas.append(obj('onda', bm, 'jato'))
    nevoas = []
    for k in range(3):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        nevoas.append(obj('nevoa', bm, 'nevoa'))

    def f_jato(q, fr):
        for k, o in enumerate(ondas):
            u = (k / len(ondas) + fr * 2) % 1.0
            o.location = (IMP.x, IMP.y, Z_RIO + 0.004)
            o.scale = (0.08 + 0.45 * u, 0.08 + 0.45 * u, 0.25 * (1 - u) + 0.02)
            chave(o, 'location', 'scale', q=q)
        for k, o in enumerate(nevoas):
            u = (k / len(nevoas) + fr * 2) % 1.0
            o.location = IMP + Vector((0.05 * math.sin(k * 2.0), 0.05 * k - 0.05, 0.03 + 0.3 * u))
            o.scale = [0.06 + 0.16 * u] * 3
            chave(o, 'location', 'scale', q=q)
    ANIM.append(f_jato)

    # ---------------------------------------------------------- lodo: bombas dos decantadores → caçamba
    CB0, CB1 = Vector((-0.2, 1.0, 0)), Vector((0.2, 1.42, 0))
    bm = bmesh.new()
    b0 = [(CB0.x + 0.03, CB0.y + 0.03), (CB1.x - 0.03, CB0.y + 0.03), (CB1.x - 0.03, CB1.y - 0.03), (CB0.x + 0.03, CB1.y - 0.03)]
    t0 = [(CB0.x, CB0.y), (CB1.x, CB0.y), (CB1.x, CB1.y), (CB0.x, CB1.y)]
    vb = [bm.verts.new((x, y, 0.1)) for x, y in b0]
    vt = [bm.verts.new((x, y, 0.42)) for x, y in t0]
    bm.faces.new(vb[::-1])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    cb = obj('cacamba', bm, 'amarelo')
    sm = cb.modifiers.new('esp', 'SOLIDIFY')
    sm.thickness = 0.015
    sm.offset = 1
    for i in range(4):
        j = (i + 1) % 4
        viga(B('ferro'), Vector((*t0[i], 0.42)), Vector((*t0[j], 0.42)), 0.025)
    for x in (CB0.x + 0.06, CB1.x - 0.06):
        caixa_de(B('ferro'), (x - 0.025, CB0.y + 0.04, 0.08), (x + 0.025, CB1.y - 0.04, 0.1))
    caixa_de(B('lodo_campo'), (CB0.x + 0.01, CB0.y + 0.01, 0.36), (CB1.x - 0.01, CB1.y - 0.01, 0.37))
    for k in range(20):
        pedra(B('lodo_campo'), (random.uniform(CB0.x + 0.03, CB1.x - 0.03), random.uniform(CB0.y + 0.03, CB1.y - 0.03), 0.37),
              random.uniform(0.012, 0.03), 0.45)
    for k in range(7):
        x = random.uniform(CB0.x + 0.02, CB1.x - 0.02)
        escorrido_plano('escorrido', Vector((x, CB0.y - 0.003, 0.42)), -Y, random.uniform(0.08, 0.25), 0.025)
    for sg, D in ((-1, D1), (1, D2)):
        xw = D.x - sg * math.sqrt(RD_ ** 2 - (1.22 - D.y) ** 2)
        xi = sg * 0.3
        cano([(xw + sg * 0.03, 1.22, 0.16), (xi, 1.22, 0.16), (xi, 1.22, 0.56), (sg * 0.1, 1.22, 0.56), (sg * 0.1, 1.22, 0.48)], 0.035,
             fl_pontas=False)
        colar(Vector((xw - sg * 0.012, 1.22, 0.16)), X, 0.035)
        cil(B('grafite', True), Vector(((xw + xi) / 2, 1.22, 0.16)), 0.06, 0.1, X, lados=20)       # bomba de lodo
        cil(B('grafite', True), Vector(((xw + xi) / 2, 1.3, 0.16)), 0.045, 0.1, Y, lados=20)
        caixa_de(B('ferro'), ((xw + xi) / 2 - 0.06, 1.16, 0.08), ((xw + xi) / 2 + 0.06, 1.36, 0.1))
    for k in range(6):
        poca((random.uniform(-0.25, 0.25), random.uniform(0.92, 1.0)), random.uniform(0.03, 0.06), 'lodo_liq')

    # ---------------------------------------------------------- mastro de cristal da IA (alimenta os campos)
    MC = Vector((0.0, 0.4, 0))
    caixa_de(B('grafite'), (MC.x - 0.12, MC.y - 0.12, 0.08), (MC.x + 0.12, MC.y + 0.12, 0.3))
    for k in range(5):
        caixa_de(B('grafite'), (MC.x - 0.125, MC.y - 0.1 + k * 0.05, 0.12), (MC.x + 0.125, MC.y - 0.09 + k * 0.05, 0.28))
    cil(B('amarelo', True), MC + Z * 0.62, 0.035, 0.64, lados=16)
    for z in (0.45, 0.7, 0.9):
        toro(B('cobre', True), MC + Z * z, 0.06, 0.012, nR=24, nr=8)
    cil(B('ferro', True), MC + Z * 0.96, 0.08, 0.03, lados=20)
    for k in range(4):
        a = k * PI / 2
        viga(B('ferro'), MC + Z * 0.97 + Vector((math.cos(a), math.sin(a), 0)) * 0.07,
             MC + Z * 1.12 + Vector((math.cos(a), math.sin(a), 0)) * 0.05, 0.012)
    cris = vazio('cristal_mastro', MC + Z * 1.1)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.05)), 0.045, 0.1, lados=6, r2=0.0)
    cil(bm, Vector((0, 0, -0.035)), 0.045, 0.07, lados=6, r2=0.0)
    for k in range(3):
        a = k * 2 * PI / 3
        cil(bm, Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.0)), 0.018, 0.08,
            Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1)), lados=6, r2=0.0)
    obj('cristal_mastro', bm, 'cristal', cris)
    luz_m = bpy.data.lights.new('Mastro', 'POINT')
    luz_m.color = VIOLETA
    luz_m.energy = 10.0
    lm = bpy.data.objects.new('Mastro', luz_m)
    sc.collection.objects.link(lm)
    lm.location = MC + Z * 1.1

    def f_mastro(q, fr):
        cris.location = MC + Z * (1.12 + 0.015 * math.sin(2 * PI * 2 * fr))
        cris.rotation_euler = (0, 0, 2 * PI * fr)
        chave(cris, 'location', 'rotation_euler', q=q)
        luz_m.energy = 9 + 3 * math.sin(2 * PI * 4 * fr)
        luz_m.keyframe_insert('energy', frame=q)
    ANIM.append(f_mastro)
    # cabos do mastro até os emissores de borda dos decantadores (feixes com abraçadeiras)
    for sg, D in ((-1, D1), (1, D2)):
        for k in range(2):
            a = (JA1 + 0.5 + (2 * PI - (JA1 - JA0) - 1.0) / 3 * (2 if sg < 0 else 0))
            dd = Vector((math.cos(a), math.sin(a), 0))
            alvo = D + dd * (RD_ + 0.01) + Z * (ZDW + 0.04)
            pts = bezier(MC + Vector((sg * 0.12, 0.02 * k, 0.2)), MC + Vector((sg * 0.3, 0.02 * k, 0.12)),
                         alvo + dd * 0.15 + Z * -0.3, alvo + dd * 0.01, 14)
            mangueira(B('borracha'), pts, 0.01)
    # armário de controle e cabos
    cab0, cab1 = armario(Vector((0.0, -1.18, 0)), 0.3, 0.2, 0.55, -Y)
    cabos = [
        bezier(cab0 + Vector((0, 0.05, 0)), (-0.25, -1.0, 0.1), (XT + 0.4, YT + 0.4, 0.1), (XT + 0.13, YT, 0.5), 14),
        bezier((0.0, -1.08, 0.3), (0.0, -0.95, 0.1), (XS + 0.1, YS - 0.4, 0.1), (XS + 0.05, YS - 0.3, 0.28), 12),
        bezier((0.12, -1.08, 0.3), (0.25, -0.95, 0.1), (0.3, -0.5, 0.1), (MC.x, MC.y - 0.12, 0.2), 14),
        bezier((0.15, -1.1, 0.4), (0.3, -1.2, 0.5), (0.55, -1.2, 0.55), (0.55, YU - 0.1, ZU + 0.13), 14),
    ]
    for pts in cabos:
        mangueira(B('borracha'), pts, 0.011)
    fios(cab1, cab1 + Vector((0.12, -0.1, -0.25)))
    for c, r in (((XS, YS - 0.2), 0.08), ((0.1, -1.3), 0.06), ((XT + 0.2, YC_ + 0.1), 0.05)):
        poca(c, r, 'oleo')
    for k in range(10):
        mancha(B('lama_seca'), (random.uniform(-1.45, 1.4), random.uniform(-1.45, 1.4)), random.uniform(0.03, 0.08), 0.0812)
    for k in range(8):
        poca((random.uniform(-1.4, -0.3), random.uniform(-1.45, -1.2)), random.uniform(0.03, 0.07), 'lodo_liq')
    fechar_pool('trat')
    return dict(alvo=Vector((0.15, -0.45, 0.25)), cam0=((2.5, -4.6, 3.7), (0.05, -0.35, 0.25), 32),
                perto=((2.4, -2.0, 1.85), (0.62, 0.05, 0.38), 30))


# ================================================================== montagem, animação, câmera
INFO = construir_biodigestor() if QUAL == 'bio' else construir_tratamento()
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for f in ANIM:
        f(q, fr)
    for val in FASES:
        val.outputs[0].default_value = FLUXO_K * fr
        val.outputs[0].keyframe_insert('default_value', frame=q)
for o in list(sc.objects) + [k.id_data for k in []]:
    ad = getattr(o, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
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
sc.cycles.max_bounces = 16
sc.cycles.transmission_bounces = 16
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


def renderizar():
    """GPU; se faltar memória (outros renders na mesma placa), tenta de novo e depois cai para CPU."""
    import time
    for tentativa in range(3):
        try:
            bpy.ops.render.render(write_still=True)
            return
        except RuntimeError as e:
            print('render falhou:', e)
            if tentativa == 1:
                sc.cycles.device = 'CPU'
            else:
                time.sleep(20)
    bpy.ops.render.render(write_still=True)


NOME = 'biodigestor' if QUAL == 'bio' else 'estacao_tratamento'
FR_FOTO = int(QUADROS * 0.12) + 1
if MODO == 'foto':
    so_uma = ARGS[2] if len(ARGS) > 2 else None
    sc.cycles.samples = 128
    sc.frame_set(FR_FOTO)
    ALVO = INFO['alvo']
    if so_uma in (None, '0'):
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
        mirar(*INFO['cam0'])
        sc.render.filepath = os.path.join(AQUI, '%s_0.png' % NOME)
        renderizar()
    for chave_f in ('perto', 'perto2'):
        if chave_f in INFO and so_uma in (None, chave_f):
            sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
            mirar(*INFO[chave_f])
            sc.render.filepath = os.path.join(AQUI, '%s_%s.png' % (NOME, chave_f))
            renderizar()
if MODO == 'teste':
    v = [float(x) for x in ARGS[2:]]
    sc.cycles.samples = 24
    sc.render.resolution_x, sc.render.resolution_y = 900, 760
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, '%s_teste.png' % NOME)
    renderizar()
print('BIO_TRAT ok')
