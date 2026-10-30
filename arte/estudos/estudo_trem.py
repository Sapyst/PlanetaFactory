"""Estudo isolado (fora do jogo): TREM da IA — locomotiva autônoma, vagão de carga (gôndola) e vagão-tanque.
Catálogo: locomotiva 0,72 × 2,93 × 1,15; vagao_carga 0,74 × 2,90 × 0,84; vagao_tanque 0,72 × 2,90 × 1,05.
Bitola 0,50; topo do trilho = z 0 do veículo (no mundo z 0,14). Frente = +Y. Partes: corpo + truque0 (y −0,85) e
truque1 (y +0,85), que giram nas curvas (pivô no centro do truque).
NÃO HÁ HUMANOS: a locomotiva não tem cabine, janela, porta, escada, corrimão nem assento. A frente é um nariz
blindado de sensores (olho vermelho, lidar girando, câmeras, barra de sensores), faróis e limpa-trilhos amassado.
- Locomotiva diesel-elétrica: capô de motor blindado com portas de acesso (uma trocada, em primer cinza), grades de
  radiador laterais e dois ventiladores girando no teto; escapamento com tampa basculante soltando fumaça preta
  que dilui; filtro de ar; caixas de bateria no estrado; eletrocalha com cabos. Sob o estrado: reator de cristal
  violeta numa gaiola com anel de campo girando (alimenta os motores de tração) e reservatórios de ar.
- Truques: rodeiros com aro, friso e raios (locomotiva) ou disco (vagões), caixas de mancal com graxa, molas
  helicoidais, quadro com pedestais, amortecedores, sapatas de freio com timoneria e cilindro, motores de tração
  suspensos pelo nariz com caixa de engrenagem, janela de cristal e anel de campo no eixo (só locomotiva).
- Engates automáticos (cabeça com mandíbula que encaixa na do vizinho), mangueira de ar com acoplamento e cabo
  elétrico de jumper entre veículos, encanamento geral de freio, torneiras angulares.
- Vagão de carga: gôndola de chapas amassadas, montantes, remendo aparafusado, cordão de solda, escorridos de
  ferrugem, número de série apagado; 4 tampas basculantes abertas por pistões hidráulicos nas cabeceiras
  (mangueiras até o distribuidor; unidade hidráulica e bateria sob o estrado); minério à vista.
- Vagão-tanque: cilindro com tampos, anéis de reforço, cintas com esticadores até o estrado, berços, domo com
  escotilha de drone (alvo de pouso, anel de LED, garras), válvula de carga motorizada que vaza seiva, válvula de
  alívio com mola, saída inferior pingando, visor de nível com seiva, escorridos de seiva e de óleo.
- Trecho de trilho reto (lastro, dormentes de concreto, placas e grampos, trilhos).
Animação (laço de 4 s): o trem anda 6 m (o trecho de via corre para trás; rodas dão 11 voltas), suspensão balança
(cada vagão no seu ritmo), ventiladores, lidar, anel de campo, fumaça, tampas e pistões, nível do visor, pingos.
Uso: blender -b --python estudo_trem.py -- foto [trem_composicao locomotiva_perto truque_perto ...]
     blender -b --python estudo_trem.py -- teste x y z ax ay az lente quadro [solz]"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(37)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS

# ------------------------------------------------------------------ medidas
Z_TR = 0.14                  # topo do trilho no mundo (z 0 do veículo)
VOLTAS = 11                  # voltas da roda no laço
DESLOC = 6.0                 # metros andados no laço (1,5 m/s)
R = DESLOC / (2 * PI * VOLTAS)   # raio da roda (0,0868) para o laço fechar
Y_TRQ = 0.85                 # centro dos truques
EIXO = 0.17                  # meia distância entre eixos
ZB = 0.205                   # face de baixo do estrado
ZD = 0.328                   # topo do piso/estrado
VIOLETA = (0.55, 0.18, 1.0)


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    """Sombra suave com quinas vivas acima de 40° (tubos parecem tubos, tampas e bordas continuam retas)."""
    for pg in o.data.polygons:
        pg.use_smooth = True
    try:
        o.data.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        for pg in o.data.polygons:
            pg.use_smooth = len(pg.vertices) == 4
    return o


def matriz_eixo(eixo):
    return Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()


def toro(bm, centro, Rr, r, eixo=(0, 0, 1), nR=40, nr=10):
    q = matriz_eixo(eixo)
    c = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(c + q @ (d * (Rr + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def anel_grosso(bm, c, ro, ri, w, eixo=(1, 0, 0), lados=32):
    """Anel com espessura (aro de roda, braçadeira, cinta): raio externo ro, interno ri, largura w no eixo."""
    q = matriz_eixo(eixo)
    c = Vector(c)
    L = []
    for k in range(lados):
        a = 2 * PI * k / lados
        d = Vector((math.cos(a), math.sin(a), 0))
        L.append([bm.verts.new(c + q @ (d * r + Vector((0, 0, z)))) for (r, z) in ((ro, -w / 2), (ro, w / 2), (ri, w / 2), (ri, -w / 2))])
    for k in range(lados):
        A, B = L[k], L[(k + 1) % lados]
        for j in range(4):
            bm.faces.new((A[j], B[j], B[(j + 1) % 4], A[(j + 1) % 4]))


def prisma_xz(bm, pts, y0, y1):
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for k in range(n):
        bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))


def prisma_yz(bm, pts, x0, x1):
    a = [bm.verts.new((x0, y, z)) for y, z in pts]
    b = [bm.verts.new((x1, y, z)) for y, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for k in range(n):
        bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))


def prisma(bm, c, r0, r1, z0, z1, n=6, eixo=(0, 0, 1), ang0=0.0):
    """Prisma de n lados (cristal) ao longo do eixo, de z0 (raio r0) a z1 (raio r1); r1 = 0 faz ponta."""
    q = matriz_eixo(eixo)
    c = Vector(c)
    b = [bm.verts.new(c + q @ Vector((r0 * math.cos(ang0 + k * 2 * PI / n), r0 * math.sin(ang0 + k * 2 * PI / n), z0))) for k in range(n)]
    if r1 <= 0:
        t = bm.verts.new(c + q @ Vector((0, 0, z1)))
        bm.faces.new(list(reversed(b)))
        for k in range(n):
            bm.faces.new((b[k], b[(k + 1) % n], t))
        return
    t = [bm.verts.new(c + q @ Vector((r1 * math.cos(ang0 + k * 2 * PI / n), r1 * math.sin(ang0 + k * 2 * PI / n), z1))) for k in range(n)]
    bm.faces.new(list(reversed(b)))
    bm.faces.new(t)
    for k in range(n):
        bm.faces.new((b[k], b[(k + 1) % n], t[(k + 1) % n], t[k]))


def esfera(bm, c, r, seg=10, esc=(1, 1, 1)):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(4, seg // 2), radius=r,
                              matrix=Matrix.Translation(Vector(c)) @ Matrix.Diagonal((*esc, 1)))


def parafuso(bm, p, normal, r=0.0055):
    cil(bm, Vector(p) + Vector(normal).normalized() * 0.002, r, 0.004, normal, lados=6)


def mola(bm, a, b, r, rf, voltas):
    a, b = Vector(a), Vector(b)
    eixo = b - a
    q = matriz_eixo(eixo)
    n = voltas * 10
    pts = [a + eixo * (i / n) + q @ Vector((math.cos(i / 10 * 2 * PI) * r, math.sin(i / 10 * 2 * PI) * r, 0)) for i in range(n + 1)]
    mangueira(bm, pts, rf)


def arco_bloco(bm, cx, cy, cz, r0, r1, a0, a1, x0, x1, n=8):
    """Bloco curvo no plano YZ em volta de (cy, cz): raios r0..r1, ângulos a0..a1 (a partir de +Y para +Z), x0..x1."""
    sec = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        d = Vector((0, math.cos(a), math.sin(a)))
        c = Vector((0, cy, cz))
        sec.append([bm.verts.new(c + d * r + Vector((x, 0, 0))) for (r, x) in ((r0, x0), (r1, x0), (r1, x1), (r0, x1))])
    for A, B in zip(sec, sec[1:]):
        for j in range(4):
            bm.faces.new((A[j], A[(j + 1) % 4], B[(j + 1) % 4], B[j]))
    bm.faces.new(sec[0])
    bm.faces.new(list(reversed(sec[-1])))


def amassar(bm, ini, centro, raio, prof, direcao):
    """Mossa: empurra os vértices criados a partir de ini que estão perto do centro."""
    bm.verts.ensure_lookup_table()
    centro, direcao = Vector(centro), Vector(direcao).normalized()
    for v in bm.verts[ini:]:
        d = (v.co - centro).length
        if d < raio:
            v.co += direcao * prof * (1 - (d / raio) ** 2) ** 2


def digitos(bm, texto, origem, direita, cima, h=0.02, esp=0.0016, falha=0.18):
    """Número de série em 7 segmentos (estêncil gasto: falta pedaço)."""
    SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc',
           '7': 'abc', '8': 'abcdefg', '9': 'abcfgd', '-': 'g'}
    w = h * 0.55
    P = {'a': ((0, 1), (1, 1)), 'b': ((1, 1), (1, 0.5)), 'c': ((1, 0.5), (1, 0)), 'd': ((0, 0), (1, 0)),
         'e': ((0, 0.5), (0, 0)), 'f': ((0, 1), (0, 0.5)), 'g': ((0, 0.5), (1, 0.5))}
    direita, cima = Vector(direita).normalized(), Vector(cima).normalized()
    nrm = direita.cross(cima)
    for i, ch in enumerate(texto):
        base = Vector(origem) + direita * (i * w * 1.6)
        for sg in SEG.get(ch, ''):
            (x0, y0), (x1, y1) = P[sg]
            a = base + direita * (x0 * w) + cima * (y0 * h)
            b = base + direita * (x1 * w) + cima * (y1 * h)
            if random.random() < falha:
                continue
            dd = b - a
            rot = Matrix((dd.normalized(), nrm.cross(dd.normalized()), nrm)).transposed()
            caixa(bm, (a + b) / 2, (dd.length + esp, esp * 1.8, 0.0006), rot)


# ------------------------------------------------------------------ decalques (manchas com borda que some)
def _cor(bm):
    return bm.loops.layers.color.get('Col') or bm.loops.layers.color.new('Col')


def _face(bm, vs, alfas):
    lay = _cor(bm)
    f = bm.faces.new(vs)
    for lp in f.loops:
        lp[lay] = (1, 1, 1, alfas[lp.vert])


def mancha_plano(bm, c, eu, ev, r, a0=0.9, ajuste=None, alongar=1.0):
    """Mancha irregular no plano eu×ev (centro denso, borda transparente). ajuste(p) pode encostar no casco."""
    n = 18
    fase = random.uniform(0, 6)
    eu, ev = Vector(eu).normalized(), Vector(ev).normalized()
    aj = ajuste or (lambda p: p)
    alf = {}
    cen = bm.verts.new(aj(Vector(c)))
    alf[cen] = a0
    aneis = []
    for f, a in ((0.5, a0 * 0.85), (1.0, 0.0)):
        anel = []
        for k in range(n):
            ang = k * 2 * PI / n
            rr = r * f * (1 + 0.3 * math.sin(3 * ang + fase) + 0.15 * math.sin(5 * ang + fase * 2))
            v = bm.verts.new(aj(Vector(c) + eu * math.cos(ang) * rr * alongar + ev * math.sin(ang) * rr))
            alf[v] = a
            anel.append(v)
        aneis.append(anel)
    for k in range(n):
        _face(bm, (cen, aneis[0][k], aneis[0][(k + 1) % n]), alf)
        _face(bm, (aneis[0][k], aneis[1][k], aneis[1][(k + 1) % n], aneis[0][(k + 1) % n]), alf)


def faixa_caminho(bm, pts, lats, a0=0.9):
    """Escorrido ao longo de pts (cheio no começo, some no fim); lats = meia largura (vetor) em cada ponto."""
    alf = {}
    fila = []
    n = len(pts) - 1
    for i, (p, w) in enumerate(zip(pts, lats)):
        t = i / n
        a, b = bm.verts.new(p - w), bm.verts.new(p + w)
        alf[a] = alf[b] = a0 * (1 - t) ** 0.8
        fila.append((a, b))
    for (a, b), (c, d) in zip(fila, fila[1:]):
        _face(bm, (a, b, d, c), alf)


def escorrido(bm, topo, base, lat, a0=0.9, seg=8, ajuste=None):
    """Escorrido reto de topo a base, afinando; ajuste(p) encosta cada ponto na superfície (chapa amassada)."""
    aj = ajuste or (lambda p: p)
    pts, lats = [], []
    for i in range(seg + 1):
        t = i / seg
        p = Vector(topo).lerp(Vector(base), t) + Vector(lat).normalized() * 0.004 * math.sin(i * 1.7)
        pts.append(aj(p))
        lats.append(Vector(lat) * (1.0 - 0.6 * t) * (1 + 0.25 * math.sin(i * 2.1)))
    faixa_caminho(bm, pts, lats, a0)


# ------------------------------------------------------------------ materiais
no = mats.no


def _m(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def rustico(m, poeira=0.7, lama=0.6, riscos=0.45, mossa=0.5, cor_poeira=(0.36, 0.31, 0.24)):
    """Poeira em cima, lama/graxa embaixo, riscos finos com metal à mostra e mossas em relevo."""
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None:
        return m
    if b.inputs['Base Color'].links:
        src = b.inputs['Base Color'].links[0].from_socket
    else:
        rgb = no(nt, 'ShaderNodeRGB')
        rgb.outputs[0].default_value = b.inputs['Base Color'].default_value
        src = rgb.outputs[0]
    tc = no(nt, 'ShaderNodeTexCoord')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    nz = sn.outputs['Z']

    def ruido(escala, det=6.0, vet=None):
        r = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': det, 'Roughness': 0.65})
        nt.links.new(vet or tc.outputs['Object'], r.inputs['Vector'])
        return r.outputs['Fac']
    mp = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.85})
    nt.links.new(nz, mp.inputs['Value'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.62})
    nt.links.new(ruido(5.0), mr.inputs['Value'])
    f_po = _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', mp.outputs['Result'], mr.outputs['Result']), poeira)
    ml = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.15, 'From Max': -0.75})
    nt.links.new(nz, ml.inputs['Value'])
    ml2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.6})
    nt.links.new(ruido(7.0), ml2.inputs['Value'])
    f_la = _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', ml.outputs['Result'], ml2.outputs['Result']), lama)
    linhas = []
    for esc in ((55.0, 3.0, 3.0), (3.0, 55.0, 4.0)):
        mp_ = no(nt, 'ShaderNodeMapping')
        mp_.inputs['Scale'].default_value = esc
        mp_.inputs['Rotation'].default_value = (0.3, 0.2, 0.5)
        nt.links.new(tc.outputs['Object'], mp_.inputs['Vector'])
        r = ruido(1.0, 3.0, mp_.outputs['Vector'])
        d = _m(nt, 'ABSOLUTE', _m(nt, 'SUBTRACT', r, 0.5))
        linhas.append(_m(nt, 'LESS_THAN', d, 0.005))
    rmask = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.64})
    nt.links.new(ruido(3.0), rmask.inputs['Value'])
    f_ri = _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', _m(nt, 'MAXIMUM', linhas[0], linhas[1]), rmask.outputs['Result']), riscos)
    c = src
    for fac, cor in ((f_ri, (0.3, 0.29, 0.27)), (f_la, (0.075, 0.055, 0.035)), (f_po, cor_poeira)):
        mx = no(nt, 'ShaderNodeMix', data_type='RGBA')
        mx.inputs[7].default_value = (*cor, 1)
        nt.links.new(fac, mx.inputs[0])
        nt.links.new(c, mx.inputs[6])
        c = mx.outputs[2]
    nt.links.new(c, b.inputs['Base Color'])
    if b.inputs['Roughness'].links:
        rs = b.inputs['Roughness'].links[0].from_socket
    else:
        rs = b.inputs['Roughness'].default_value
    nt.links.new(_m(nt, 'ADD', rs, _m(nt, 'MULTIPLY', _m(nt, 'ADD', f_po, f_la), 0.5)), b.inputs['Roughness'])
    if not b.inputs['Metallic'].links:
        nt.links.new(_m(nt, 'MAXIMUM', b.inputs['Metallic'].default_value, _m(nt, 'MULTIPLY', f_ri, 0.9)), b.inputs['Metallic'])
    bp = no(nt, 'ShaderNodeBump', **{'Strength': 0.12 * mossa, 'Distance': 0.02})
    nt.links.new(ruido(18.0, 4.0), bp.inputs['Height'])
    if b.inputs['Normal'].links:
        nt.links.new(b.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def emissivo(nome, cor, forca, base=None, rough=0.3):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    b.inputs['Roughness'].default_value = rough
    return m


def forca_de(m):
    return m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.3, 0.06, 0.75, 1)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = 0.4
    b.inputs['Emission Color'].default_value = (*VIOLETA, 1)
    b.inputs['Emission Strength'].default_value = 3.0
    return m


def vidro_mat(nome, cor, rough=0.05, transm=0.95):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.45
    return m


def liquido_mat(nome, cor, emis=0.0, rough=0.08):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = 0.35
    b.inputs['Coat Weight'].default_value = 1.0
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = emis
    return m


def decal_mat(nome, cor, rough, metal=0.0, coat=0.0):
    """Mancha que se desfaz na borda: alfa do atributo 'Col' × ruído."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    at = no(nt, 'ShaderNodeVertexColor', layer_name='Col')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 35.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    rm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.65, 'To Min': 0.35, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], rm.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(at.outputs['Alpha'], mul.inputs[0])
    nt.links.new(rm.outputs['Result'], mul.inputs[1])
    nt.links.new(mul.outputs['Value'], b.inputs['Alpha'])
    return m


def estencil_mat():
    m = bpy.data.materials.new('Estêncil')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.62, 0.6, 0.55, 1)
    b.inputs['Roughness'].default_value = 0.85
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    ru2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 8.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru2.inputs['Vector'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(ru.outputs['Fac'], mul.inputs[0])
    nt.links.new(ru2.outputs['Fac'], mul.inputs[1])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.18, 'From Max': 0.3, 'To Min': 0.0, 'To Max': 0.75})
    nt.links.new(mul.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def fumaca_grad_mat(nome, dens, z0, z1):
    """Fumaça que sai preta e se dilui em cinza claro conforme sobe (z0 → z1 no mundo)."""
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    sep = next(n for n in nt.nodes if n.type == 'SEPXYZ')
    t = no(nt, 'ShaderNodeMapRange', **{'From Min': z0, 'From Max': z0 + (z1 - z0) * 0.7})
    nt.links.new(sep.outputs['Z'], t.inputs['Value'])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[6].default_value = (0.012, 0.011, 0.011, 1)
    mix.inputs[7].default_value = (0.42, 0.42, 0.43, 1)
    nt.links.new(t.outputs['Result'], mix.inputs[0])
    nt.links.new(mix.outputs[2], vol.inputs['Color'])
    return m


def perigo_vermelho_mat():
    m = base3d.listras_mat()
    m.name = 'Listras vermelhas'
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.blend_type == 'MIX':
            n.inputs[7].default_value = (0.42, 0.03, 0.02, 1)
    return m


M = base3d.M
M.update({
    'amarelo': mats.material('Amarelo loco', (0.72, 0.48, 0.05), 0, 0.42, ferrugem=0.55, desgaste=1.0, sujeira=0.95),
    'amarelo_gasto': mats.material('Amarelo gasto', (0.62, 0.41, 0.05), 0, 0.5, ferrugem=0.8, desgaste=1.0, sujeira=1.0),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, ferrugem=0.45, desgaste=0.8, sujeira=0.9),
    'zarcao': mats.material('Zarcão', (0.40, 0.10, 0.04), 0, 0.6, ferrugem=0.85, desgaste=0.9, sujeira=1.0),
    'tanque': mats.material('Tanque', (0.085, 0.09, 0.095), 0, 0.45, ferrugem=0.75, desgaste=0.9, sujeira=1.0),
    'cinza': mats.material('Primer cinza', (0.34, 0.35, 0.34), 0, 0.7, ferrugem=0.4, desgaste=0.8, sujeira=0.9),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.7, sujeira=0.85, escovado=True),
    'roda': mats.material('Aço roda', (0.3, 0.29, 0.28), 1.0, 0.5, pintura=False, ferrugem=1.0, sujeira=1.0),
    'ferro': mats.material('Ferro', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'queimado': mats.material('Queimado', (0.1, 0.085, 0.08), 1.0, 0.6, pintura=False, ferrugem=0.7, sujeira=1.0),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.78, 0.40, 0.22), 1.0, 0.3, pintura=False, sujeira=0.7),
    'borracha': mats.material('Borracha', (0.02, 0.02, 0.022), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
    'mola': mats.material('Mola', (0.12, 0.11, 0.1), 0.8, 0.5, pintura=False, ferrugem=1.0, sujeira=0.9),
    'motor': mats.material('Motor', (0.11, 0.11, 0.12), 1.0, 0.4, pintura=False, ferrugem=0.5, sujeira=0.9),
    'remendo': mats.material('Remendo', (0.3, 0.31, 0.27), 0.6, 0.55, pintura=False, desgaste=0.8, sujeira=0.9, ferrugem=1.0),
    'cordao': mats.material('Cordão de solda', (0.16, 0.13, 0.12), 1.0, 0.55, pintura=False, sujeira=0.3, ferrugem=0.5),
    'graxa': mats.material('Graxa', (0.03, 0.022, 0.012), 0, 0.12, pintura=False, sujeira=0.0, desgaste=0.0),
    'minerio': mats.material('Minério', (0.30, 0.13, 0.07), 0.2, 0.7, pintura=False, sujeira=0.5, ferrugem=0.6, desgaste=0.0),
    'minerio2': mats.material('Minério escuro', (0.13, 0.12, 0.11), 0.6, 0.45, pintura=False, sujeira=0.4, desgaste=0.0),
    'lastro': mats.material('Lastro', (0.17, 0.16, 0.15), 0, 0.85, pintura=False, sujeira=0.4, desgaste=0.0),
    'lastro2': mats.material('Lastro ferrugem', (0.2, 0.12, 0.08), 0, 0.9, pintura=False, sujeira=0.5, desgaste=0.0),
    'dormente': mats.material('Dormente', (0.24, 0.23, 0.21), 0, 0.9, sujeira=1.0, desgaste=0.5, ferrugem=0.3),
    'trilho': mats.material('Trilho', (0.24, 0.19, 0.16), 1.0, 0.6, pintura=False, ferrugem=1.0, sujeira=0.9),
    'trilho_topo': mats.material('Topo do trilho', (0.62, 0.62, 0.63), 1.0, 0.22, pintura=False, sujeira=0.2, escovado=True),
    'chao': mats.material('Chão', (0.23, 0.2, 0.16), 0, 0.92, sujeira=0.3, desgaste=0.0),
    'buraco': mats.material('Buraco', (0.012, 0.012, 0.012), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'radiador': mats.material('Colmeia', (0.05, 0.05, 0.05), 0.8, 0.6, pintura=False, sujeira=0.9, ferrugem=0.6),
    'cabo_v': mats.material('Cabo vermelho', (0.3, 0.03, 0.02), 0, 0.6, pintura=False, sujeira=0.8, desgaste=0.0),
    'cabo_a': mats.material('Cabo amarelo', (0.55, 0.38, 0.03), 0, 0.6, pintura=False, sujeira=0.8, desgaste=0.0),
    'cabo_p': mats.material('Cabo preto', (0.025, 0.025, 0.028), 0, 0.55, pintura=False, sujeira=0.6, desgaste=0.0),
    'tinta_branca': mats.material('Tinta branca', (0.7, 0.68, 0.6), 0, 0.7, desgaste=1.0, sujeira=1.0),
    'cristal': cristal_mat(),
    'campo': emissivo('Campo', VIOLETA, 7.0),
    'olho': emissivo('Olho vermelho', (1.0, 0.03, 0.015), 18.0),
    'led_v': emissivo('LED vermelho', (1.0, 0.04, 0.02), 9.0),
    'led_a': emissivo('LED âmbar', (1.0, 0.36, 0.04), 8.0),
    'farol': emissivo('Farol', (1.0, 0.85, 0.62), 22.0),
    'laser': emissivo('Lidar janela', (1.0, 0.05, 0.02), 6.0, base=(0.05, 0.02, 0.02)),
    'vidro': vidro_mat('Vidro escuro', (0.04, 0.05, 0.05), rough=0.08, transm=0.0),
    'vidro_tubo': vidro_mat('Vidro do visor', (0.75, 0.75, 0.7), rough=0.12),
    'seiva': liquido_mat('Seiva', (0.55, 0.26, 0.02), emis=0.4),
    'listras': base3d.listras_mat(),
    'listras_v': perigo_vermelho_mat(),
    'estencil': estencil_mat(),
    'escorrido_s': decal_mat('Ferrugem escorrida', (0.28, 0.09, 0.025), 0.95),
    'fuligem_s': decal_mat('Fuligem suave', (0.01, 0.009, 0.009), 0.97),
    'oleo_s': decal_mat('Óleo suave', (0.008, 0.006, 0.004), 0.08, coat=0.6),
    'seiva_s': decal_mat('Seiva escorrida', (0.42, 0.18, 0.015), 0.06, coat=1.0),
    'graxa_s': decal_mat('Graxa suave', (0.025, 0.018, 0.01), 0.15, coat=0.4),
    'solda_s': decal_mat('Calor de solda', (0.07, 0.05, 0.08), 0.5, metal=0.6),
    'po_s': decal_mat('Pó suave', (0.32, 0.29, 0.24), 0.95),
    'fumaca': fumaca_grad_mat('Fumaça', 10.0, 1.2, 2.5),
})
for k in ('amarelo', 'amarelo_gasto', 'grafite', 'zarcao', 'tanque', 'cinza', 'aco', 'ferro', 'motor', 'remendo',
          'queimado', 'roda', 'mola'):
    rustico(M[k])
for k in ('borracha', 'cabo_v', 'cabo_a', 'cabo_p', 'tinta_branca', 'trilho'):
    rustico(M[k], poeira=0.5, lama=0.4, riscos=0.25, mossa=0.2)
rustico(M['dormente'], poeira=0.6, lama=0.3, riscos=0.0, mossa=1.0, cor_poeira=(0.3, 0.27, 0.22))
for k in ('campo', 'led_a', 'led_v', 'olho'):
    M[k].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.4
DECAIS = {'escorrido_s', 'fuligem_s', 'oleo_s', 'seiva_s', 'graxa_s', 'solda_s', 'po_s', 'estencil'}


# ------------------------------------------------------------------ objetos e hierarquia
def vazio(nome, pai=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(o)
    o.empty_display_size = 0.05
    o.parent = pai
    o.location = loc
    return o


def malha(nome, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    o.data.materials.append(M[mat])
    return o


def chanfrar(o, w=0.0025):
    md = o.modifiers.new('Chanfro', 'BEVEL')
    md.width = w
    md.segments = 2
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(35)
    md.harden_normals = False
    return o


ANIM = []                    # funções f(q, fr) chamadas a cada quadro


class Veiculo:
    """Geometria em coordenadas do veículo (x lado, y frente, z do topo do trilho). Cada chave é um vazio com pivô."""

    def __init__(s, nome, yc):
        s.nome, s.yc = nome, yc
        s.raiz = vazio(nome, None, (0, yc, Z_TR))
        s.nos = {'raiz': (s.raiz, Vector((0, 0, 0)))}
        s.bms = {}

    def no(s, chave, pai, pivo):
        e_pai, p_pai = s.nos[pai]
        e = vazio(s.nome + '_' + chave, e_pai, Vector(pivo) - p_pai)
        s.nos[chave] = (e, Vector(pivo))
        return e

    def B(s, chave, mat, liso=False, bev=None):
        if bev is None:
            bev = not liso and mat not in DECAIS
        k = (chave, mat, liso, bev)
        if k not in s.bms:
            s.bms[k] = bmesh.new()
        return s.bms[k]

    def sep(s, chave, nome, bm, mat):
        e, p = s.nos[chave]
        o = malha(s.nome + '_' + nome, bm, mat)
        o.parent = e
        o.location = -p
        return o

    def fechar(s):
        for (ch, mat, liso, bev), bm in s.bms.items():
            if not bm.verts:
                bm.free()
                continue
            o = s.sep(ch, ch + '_' + mat, bm, mat)
            if liso:
                suavizar(o)
            if bev:
                chanfrar(o)
        s.bms = {}


def sujar_caixa(V, ch, c, normal, eu, r=0.03, mat='escorrido_s', comp=0.12):
    """Escorrido curto a partir de um ponto de uma face vertical (normal), descendo."""
    n = Vector(normal).normalized()
    p = Vector(c) + n * 0.0012
    escorrido(V.B(ch, mat), p, p - Vector((0, 0, comp)), Vector(eu).normalized() * r * 0.4)


# ------------------------------------------------------------------ rodeiro e truque
def rodeiro(V, chave, ya, tipo):
    bm = V.B(chave, 'roda', liso=True)
    tubo(bm, (-0.30, ya, R), (0.30, ya, R), 0.02, 16)                      # eixo (as pontas giram dentro dos mancais)
    bp = V.B(chave, 'tinta_branca', bev=False)
    for s in (-1, 1):
        x = s * 0.255
        anel_grosso(bm, (x, ya, R), R, R - 0.016, 0.042, X, 48)            # aro (pista de rolamento)
        anel_grosso(bm, (s * 0.230, ya, R), R + 0.012, R - 0.012, 0.008, X, 48)   # friso (por dentro do trilho)
        if tipo == 'raios':
            cil(bm, Vector((x, ya, R)), 0.028, 0.05, X, 16)                 # cubo
            for k in range(8):
                a = k * PI / 4 + 0.2
                d = Vector((0, math.cos(a), math.sin(a)))
                tubo(bm, Vector((x, ya, R)) + d * 0.026, Vector((x, ya, R)) + d * (R - 0.014), 0.0065, 6)
        else:
            cil(bm, Vector((x - s * 0.002, ya, R)), R - 0.012, 0.01, X, 40, r2=None)   # disco
            cil(bm, Vector((x, ya, R)), 0.03, 0.05, X, 16)                  # cubo
            bb = V.B(chave, 'buraco', bev=False)
            for k in range(4):                                              # furos de alívio (aparência)
                a = k * PI / 2 + 0.4
                c = Vector((x + s * 0.0035, ya + math.cos(a) * 0.05, R + math.sin(a) * 0.05))
                cil(bb, c, 0.011, 0.002, X, 12)
        for k in range(5):                                                  # porcas do cubo
            a = k * 2 * PI / 5
            parafuso(bm, Vector((x + s * 0.025, ya + math.cos(a) * 0.017, R + math.sin(a) * 0.017)), Vector((s, 0, 0)), 0.004)
        # marca de tinta no aro (mostra o giro) e na ponta do eixo
        caixa(bp, (s * 0.2765, ya, R - 0.008), (0.001, 0.008, 0.014))


def truque(V, i, yt, motor, rodas):
    T, Q, MO = 'truque%d' % i, 'quadro%d' % i, 'molas%d' % i
    V.no(T, 'raiz', (0, yt, 0.13))
    V.no(Q, T, (0, yt, 0.13))
    V.no(MO, T, (0, yt, 0.126))
    bq = V.B(Q, 'grafite')
    bmc = V.B(T, 'amarelo_gasto')
    bfe = V.B(Q, 'ferro')
    bg = V.B(T, 'graxa', liso=True)
    bgs = V.B(T, 'graxa_s')
    for j in (-1, 1):
        ya = yt + j * EIXO
        V.no('rod%d%d' % (i, j), T, (0, ya, R))
        rodeiro(V, 'rod%d%d' % (i, j), ya, rodas)
        for s in (-1, 1):
            # caixa de mancal (não gira): corpo, tampa com parafusos, graxeira, graxa vazando
            cil(bmc, Vector((s * 0.31, ya, R)), 0.034, 0.05, X, 20)
            cil(bmc, Vector((s * 0.339, ya, R)), 0.029, 0.008, X, 20)
            for k in range(6):
                a = k * PI / 3
                parafuso(bmc, Vector((s * 0.343, ya + math.cos(a) * 0.021, R + math.sin(a) * 0.021)), Vector((s, 0, 0)), 0.0035)
            caixa(bmc, (s * 0.31, ya, R + 0.036), (0.052, 0.05, 0.006))         # sela da mola
            cil(V.B(T, 'cobre'), Vector((s * 0.335, ya + 0.022, R + 0.022)), 0.004, 0.012, Vector((s, 0.6, 0.6)), 8)
            for k in range(3):                                                  # gotas de graxa na borda da tampa
                a = -0.9 - k * 0.5 + random.uniform(-0.2, 0.2)
                esfera(bg, Vector((s * 0.343, ya + math.cos(a) * 0.028, R + math.sin(a) * 0.028)), 0.005, 8, (0.9, 1.3, 0.8))
            mancha_plano(bgs, Vector((s * 0.3445, ya, R - 0.012)), Y, Z, 0.022, 0.9, alongar=1.0)
            escorrido(bgs, Vector((s * 0.3362, ya - 0.012, R - 0.03)), Vector((s * 0.3362, ya - 0.016, R - 0.075)), Vector((0, 0.006, 0)))
            # mola primária sobre o mancal
            mola(V.B(MO, 'mola', liso=True), (s * 0.31, ya, R + 0.039), (s * 0.31, ya, 0.152), 0.018, 0.0042, 3)
            # pedestal do quadro (pernas abraçando o mancal) e tirante de baixo
            for d in (-1, 1):
                caixa_de(bq, (s * 0.297, ya + d * 0.039, 0.045), (s * 0.323, ya + d * 0.052, 0.152))
            caixa_de(bq, (s * 0.297, ya - 0.052, 0.038), (s * 0.323, ya + 0.052, 0.048))
            # sapata de freio no aro (lado de fora do truque), cabeça, pendural e viga de freio
            if j > 0:
                arco_bloco(V.B(Q, 'ferro'), 0, ya, R, R + 0.003, R + 0.016, -0.42, 0.42, s * 0.237, s * 0.273)
            else:
                arco_bloco(V.B(Q, 'ferro'), 0, ya, R, R + 0.003, R + 0.016, PI - 0.42, PI + 0.42, s * 0.237, s * 0.273)
            caixa(bfe, (s * 0.255, ya + j * (R + 0.024), R), (0.03, 0.014, 0.05))
            viga(bfe, Vector((s * 0.255, ya + j * (R + 0.026), R + 0.024)), Vector((s * 0.255, yt + j * 0.305, 0.142)), 0.008)
        tubo(bfe, (-0.255, ya + j * (R + 0.034), R - 0.005), (0.255, ya + j * (R + 0.034), R - 0.005), 0.008, 8)
        if motor:
            # motor de tração suspenso pelo nariz: corpo, aletas, tampas, mancais no eixo, nariz no travessão
            ym = yt + j * 0.085
            bmo = V.B(T, 'motor', liso=True)
            cil(bmo, Vector((0, ym, 0.082)), 0.045, 0.33, X, 24)
            for xx in (-0.12, -0.06, 0.0, 0.06):
                anel_grosso(bmo, (xx, ym, 0.082), 0.048, 0.044, 0.008, X, 24)
            for s in (-1, 1):
                cil(V.B(T, 'ferro'), Vector((s * 0.168, ym, 0.082)), 0.04, 0.008, X, 20)
                caixa(V.B(T, 'ferro'), (s * 0.13, (ym + ya) / 2 + j * 0.01, R), (0.04, 0.085, 0.05))   # mancal de suspensão
            caixa(V.B(T, 'ferro'), (0, yt + j * 0.04, 0.125), (0.08, 0.03, 0.02))                  # nariz no travessão
            # caixa de engrenagem (lado +x) envolvendo pinhão e coroa
            bge = V.B(T, 'amarelo_gasto')
            caixa_de(bge, (0.176, ym - 0.03 * j, 0.03), (0.212, ya + j * 0.02, 0.135))
            cil(bge, Vector((0.194, ya + j * 0.02, 0.0825)), 0.0525, 0.036, X, 20)
            esfera(bg, Vector((0.213, ya, 0.05)), 0.006, 8, (0.6, 1.2, 1.6))                     # vazamento de óleo da caixa
            escorrido(V.B(T, 'oleo_s'), Vector((0.2132, ya - 0.01, 0.12)), Vector((0.2132, ya - 0.012, 0.04)), Vector((0, 0.008, 0)))
            # janela de cristal no motor (o toque da IA)
            caixa(V.B(T, 'ferro'), (0, ym, 0.126), (0.17, 0.04, 0.008))
            for xx in (-0.06, 0.0, 0.06):
                prisma(V.B(T, 'cristal', bev=False), (xx, ym, 0.119), 0.012, 0.0, 0.0, 0.028, 6, Z, 0.3)
            # anel de campo em volta do eixo (lado −x) com três presilhas
            toro(V.B(T, 'campo', bev=False), (-0.203, ya, R), 0.036, 0.0055, X, 40, 8)
            for k in range(3):
                a = k * 2 * PI / 3 + 0.5
                caixa(V.B(T, 'ferro'), (-0.203, ya + math.cos(a) * 0.036, R + math.sin(a) * 0.036), (0.016, 0.012, 0.012))
            # cabos do motor subindo ao estrado
            for k, (mt, xx) in enumerate((('cabo_p', 0.09), ('cabo_v', 0.11))):
                pts = bezier((xx, ym, 0.125), (xx, ym, 0.17), (xx, ym + j * 0.03, 0.17), (xx, ym + j * 0.05, 0.215), 8)
                mangueira(V.B(T, mt, liso=True), pts, 0.0065)
    # quadro: cordas superiores, ventre entre pedestais, travessões, prato de pião, ampara-balanço
    for s in (-1, 1):
        caixa_de(bq, (s * 0.288, yt - 0.32, 0.152), (s * 0.332, yt + 0.32, 0.185))
        caixa_de(bq, (s * 0.300, yt - 0.119, 0.095), (s * 0.320, yt + 0.119, 0.152))
        cil(V.B(Q, 'buraco', bev=False), Vector((s * 0.3205, yt, 0.124)), 0.018, 0.001, X, 16)     # furo de alívio
        for d in (-1, 1):
            caixa_de(bq, (s * 0.300, yt + d * 0.119, 0.07), (s * 0.320, yt + d * 0.125, 0.152))
        for yy in (-0.28, -0.2, -0.08, 0.08, 0.2, 0.28):
            parafuso(bq, (s * 0.332, yt + yy, 0.17), (s, 0, 0), 0.004)
        caixa_de(bfe, (s * 0.29, yt - 0.03, 0.185), (s * 0.33, yt + 0.03, 0.198))               # ampara-balanço
        # amortecedor vertical por fora (camisa no quadro, haste no estrado)
        a, b = Vector((s * 0.372, yt - 0.10, 0.105)), Vector((s * 0.372, yt + 0.035, 0.238))
        caixa_de(bfe, (s * 0.32, yt - 0.112, 0.095), (s * 0.372, yt - 0.088, 0.115))
        u = (b - a).normalized()
        cil(V.B(Q, 'amarelo_gasto', liso=True), a + u * 0.05, 0.013, 0.09, u, 14)
        cil(V.B(Q, 'cromo', liso=True), a + u * 0.12, 0.0055, 0.07, u, 10)
        for p in (a, b):
            cil(bfe, p, 0.009, 0.014, X, 10)
    caixa_de(bq, (-0.29, yt - 0.035, 0.135), (0.29, yt + 0.035, 0.18))
    cil(V.B(Q, 'ferro'), Vector((0, yt, 0.1875)), 0.055, 0.015, Z, 24)
    for d in (-1, 1):
        caixa_de(bq, (-0.29, yt + d * 0.30, 0.14), (0.29, yt + d * 0.32, 0.175))
        # cilindro de freio no travessão da ponta e timoneria até a viga de freio
        cy = yt + d * 0.36
        cil(V.B(Q, 'amarelo_gasto', liso=True), Vector((0.06, cy, 0.157)), 0.03, 0.07, Y, 16)
        cil(bfe, Vector((0.06, yt + d * 0.395, 0.157)), 0.034, 0.008, Y, 16)
        viga(bfe, Vector((0.06, yt + d * 0.33, 0.135)), Vector((0.0, yt + d * (EIXO + R + 0.034), R)), 0.009)
        mangueira(V.B(Q, 'borracha', liso=True), bezier((0.06, yt + d * 0.39, 0.175), (0.06, yt + d * 0.40, 0.21),
                                                       (0.12, yt + d * 0.40, 0.20), (0.14, yt + d * 0.38, 0.21), 6), 0.005)
    # sujeira do truque: poeira em cima das cordas, ferrugem escorrendo dos parafusos
    for s in (-1, 1):
        for yy in (-0.2, 0.08):
            sujar_caixa(V, Q, (s * 0.332, yt + yy, 0.165), (s, 0, 0), Y, 0.02, 'escorrido_s', 0.05)


# ------------------------------------------------------------------ estrado, engates e mangueiras
def estrado(V, pint, deck=True):
    C = 'corpo'
    bm = V.B(C, pint)
    bf = V.B(C, 'ferro')
    for s in (-1, 1):
        caixa_de(bm, (s * 0.348, -1.37, ZB), (s * 0.36, 1.37, 0.32))
        caixa_de(bm, (s * 0.31, -1.37, ZB), (s * 0.36, 1.37, ZB + 0.012))
        caixa_de(bm, (s * 0.31, -1.37, 0.308), (s * 0.36, 1.37, 0.32))
        for k in range(39):
            yy = -1.33 + k * 0.07
            parafuso(bm, (s * 0.36, yy, ZB + 0.008), (s, 0, 0), 0.0035)
            parafuso(bm, (s * 0.36, yy, 0.312), (s, 0, 0), 0.0035)
        # suporte do amortecedor do truque
        for yt in (-Y_TRQ, Y_TRQ):
            caixa_de(bf, (s * 0.36, yt + 0.02, 0.222), (s * 0.385, yt + 0.05, 0.256))
    caixa_de(bm, (-0.06, -1.37, 0.215), (0.06, 1.37, 0.31))
    for yb in (-Y_TRQ, Y_TRQ):
        caixa_de(bm, (-0.348, yb - 0.04, ZB), (0.348, yb + 0.04, 0.31))
        cil(bf, Vector((0, yb, 0.2)), 0.05, 0.01, Z, 24)                                      # pião
    for yb in (-0.35, 0.35):
        caixa_de(bm, (-0.348, yb - 0.02, 0.25), (0.348, yb + 0.02, 0.31))
    for e in (-1, 1):
        caixa_de(bm, (-0.36, e * 1.37, 0.20), (0.36, e * 1.41, 0.33))                         # testeira
        caixa_de(V.B(C, 'listras'), (-0.34, e * 1.41, 0.21), (0.34, e * 1.4125, 0.32))
        for x in (-0.3, -0.2, 0.2, 0.3):
            parafuso(bf, (x, e * 1.4125, 0.225), (0, e, 0), 0.005)
            parafuso(bf, (x, e * 1.4125, 0.305), (0, e, 0), 0.005)
    if deck:
        caixa_de(bm, (-0.36, -1.37, 0.32), (0.36, 1.37, ZD))
    # encanamento geral de freio, braçadeiras, torneiras angulares
    tubo(V.B(C, 'ferro', liso=True), (0.16, -1.40, 0.232), (0.16, 1.40, 0.232), 0.009, 10)
    for yy in (-1.1, -0.6, -0.2, 0.2, 0.6, 1.1):
        anel_grosso(bf, (0.16, yy, 0.232), 0.013, 0.009, 0.012, Y, 12)
    for e in (-1, 1):
        caixa(bf, (0.16, e * 1.425, 0.232), (0.03, 0.03, 0.03))
        cil(V.B(C, 'amarelo_gasto'), Vector((0.16, e * 1.425, 0.255)), 0.006, 0.02, Z, 8)
        engate(V, e)
    # escorridos de ferrugem nos rebites da longarina
    for s in (-1, 1):
        for yy in (-1.05, -0.4, 0.25, 0.95):
            yy += random.uniform(-0.1, 0.1)
            escorrido(V.B(C, 'escorrido_s'), Vector((s * 0.3612, yy, 0.31)), Vector((s * 0.3612, yy, 0.21)), Vector((0, 0.008, 0)))


def F(e, x, y, z):
    """Ponto na ponta e (±1): a ponta de trás é a da frente girada 180° (o engate encaixa no vizinho)."""
    return Vector((e * x, e * y, z))


def FY(e, x, y, z):
    """Ponto na ponta e sem espelhar x (encanamento e tomadas ficam do mesmo lado em todo veículo)."""
    return Vector((x, e * y, z))


def engate(V, e):
    """Engate automático na ponta e (±1): haste, cabeça com mandíbula que encaixa na do vizinho, pino, carrinho,
    cilindro pneumático de destrave (a IA solta o engate sozinha)."""
    C = 'corpo'
    bm = V.B(C, 'ferro')
    caixa_de(bm, F(e, -0.022, 1.37, 0.222), F(e, 0.022, 1.468, 0.262))
    caixa_de(bm, F(e, 0.0, 1.465, 0.212), F(e, 0.05, 1.50, 0.272))
    caixa_de(bm, F(e, -0.05, 1.465, 0.212), F(e, 0.0, 1.485, 0.272))
    caixa_de(bm, F(e, 0.004, 1.50, 0.218), F(e, 0.045, 1.514, 0.266))
    cil(V.B(C, 'aco'), F(e, 0.036, 1.488, 0.242), 0.007, 0.075, Z, 10)
    caixa_de(bm, F(e, -0.045, 1.41, 0.205), F(e, 0.045, 1.445, 0.221))
    cil(V.B(C, 'amarelo_gasto', liso=True), F(e, -0.03, 1.435, 0.29), 0.012, 0.05, Y, 12)
    tubo(V.B(C, 'cromo', liso=True), F(e, -0.03, 1.46, 0.29), F(e, -0.03, 1.476, 0.272), 0.004)
    mangueira(V.B(C, 'borracha', liso=True), bezier(F(e, -0.03, 1.415, 0.30), F(e, -0.06, 1.42, 0.32),
                                                    FY(e, 0.1 * e, 1.42, 0.30), FY(e, 0.16, 1.425, 0.25), 6), 0.004)
    mancha_plano(V.B(C, 'graxa_s'), F(e, 0.025, 1.4825, 0.2725), Y, X, 0.02, 0.8)


def mangueiras_entre(V, livre=False, e=-1):
    """Mangueira de ar com acoplamento e cabo de jumper na ponta e de V até o vizinho (3 m adiante em e);
    livre=True: mangueira pendurada no suporte (ponta solta)."""
    C = 'corpo'
    bb = V.B(C, 'borracha', liso=True)
    bf = V.B(C, 'ferro')
    if livre:
        pts = bezier(FY(e, 0.16, 1.43, 0.225), FY(e, 0.16, 1.47, 0.12), FY(e, 0.16, 1.50, 0.10), FY(e, 0.15, 1.45, 0.17), 8)
        mangueira(bb, pts, 0.008)
        caixa(bf, FY(e, 0.15, 1.45, 0.175), (0.03, 0.02, 0.015))
        caixa(bf, FY(e, 0.15, 1.418, 0.19), (0.02, 0.012, 0.04))
        return
    for lado in (0, 1):
        y0 = 1.43 if lado == 0 else 3.0 - 1.43
        y1 = 1.50 - 0.012 if lado == 0 else 1.50 + 0.012
        pts = bezier(FY(e, 0.16, y0, 0.225), FY(e, 0.16, y0 + (0.05 if lado == 0 else -0.05), 0.13),
                     FY(e, 0.15, y1 + (-0.03 if lado == 0 else 0.03), 0.11), FY(e, 0.15, y1, 0.125), 8)
        mangueira(bb, pts, 0.008)
        caixa(bf, FY(e, 0.15, y1, 0.125), (0.03, 0.022, 0.018))                   # acoplamento (gladhand)
    # cabo de jumper elétrico (lado −x): tomada em cada testeira e cabo grosso curvado
    for yy in (1.42, 3.0 - 1.42):
        caixa(V.B(C, 'grafite'), FY(e, -0.2, yy, 0.27), (0.05, 0.03, 0.05))
    pts = bezier(FY(e, -0.2, 1.44, 0.26), FY(e, -0.2, 1.46, 0.12), FY(e, -0.2, 3.0 - 1.46, 0.12), FY(e, -0.2, 3.0 - 1.44, 0.26), 12)
    mangueira(V.B(C, 'cabo_p', liso=True), pts, 0.011)


def reservatorio(V, x, y0, y1, z, r=0.05):
    C = 'corpo'
    b = V.B(C, 'grafite', liso=True)
    cil(b, Vector((x, (y0 + y1) / 2, z)), r, y1 - y0, Y, 24)
    for yy in (y0, y1):
        esfera(b, Vector((x, yy, z)), r, 20, (1, 0.6, 1))
    bf = V.B(C, 'ferro')
    for yy in (y0 + 0.12, y1 - 0.12):
        anel_grosso(bf, (x, yy, z), r + 0.005, r - 0.001, 0.018, Y, 24)
        caixa_de(bf, (x - 0.008, yy - 0.009, z + r), (x + 0.008, yy + 0.009, ZB))
    cil(V.B(C, 'aco'), Vector((x, (y0 + y1) / 2, z - r - 0.008)), 0.008, 0.02, Z, 8)      # dreno
    tubo(V.B(C, 'ferro', liso=True), (x, y1 + r * 0.5, z), (x, y1 + r * 0.5 + 0.03, z), 0.006)
    mangueira(V.B(C, 'ferro', liso=True), bezier((x, y1 + r * 0.6 + 0.03, z), (x, y1 + 0.1, 0.196),
                                                 (0.16, y1 + 0.1, 0.196), (0.16, y1 + 0.16, 0.232), 8), 0.006)
    escorrido(V.B(C, 'escorrido_s'), Vector((x - r - 0.001, y0 + 0.2, z)), Vector((x - r * 0.7, y0 + 0.2, z - r * 0.7)), Vector((0, 0.01, 0)))


# ------------------------------------------------------------------ LOCOMOTIVA
FUMACAS = []


def locomotiva():
    V = Veiculo('locomotiva', 3.0)
    C = 'corpo'
    V.no(C, 'raiz', (0, 0, 0.20))
    estrado(V, 'grafite')
    truque(V, 0, -Y_TRQ, True, 'raios')
    truque(V, 1, Y_TRQ, True, 'raios')
    ba, bg, bf = V.B(C, 'amarelo'), V.B(C, 'grafite'), V.B(C, 'ferro')
    # --- capô do motor (blindado, cantos chanfrados)
    prisma_xz(ba, [(-0.30, ZD), (0.30, ZD), (0.30, 0.80), (0.25, 0.86), (-0.25, 0.86), (-0.30, 0.80)], -1.33, 0.78)
    for s in (-1, 1):
        for k in range(30):
            yy = -1.30 + k * 0.071
            parafuso(ba, (s * 0.30, yy, ZD + 0.018), (s, 0, 0), 0.004)
            parafuso(ba, (s * 0.283, yy, 0.8204), (s * 0.768, 0, 0.64), 0.004)
        # juntas das portas de acesso (sem maçanetas: a IA abre por drone) e dobradiças
        for yy in (-0.40, 0.28, 0.58):
            caixa_de(V.B(C, 'buraco', bev=False), (s * 0.3, yy - 0.002, ZD + 0.03), (s * 0.3015, yy + 0.002, 0.79))
            for zz in (0.42, 0.68):
                cil(bf, Vector((s * 0.304, yy + 0.012, zz)), 0.006, 0.04, Z, 8)
        caixa_de(V.B(C, 'buraco', bev=False), (s * 0.3, -1.30, ZD + 0.03), (s * 0.3015, 0.76, ZD + 0.034))
        # grade do radiador (lateral, traseira) e grade da casa de máquinas
        for (y0, y1, z0, z1, n) in ((-1.27, -0.46, 0.46, 0.78, 11), (-0.33, 0.22, 0.56, 0.76, 7)):
            caixa_de(V.B(C, 'radiador', bev=False), (s * 0.2995, y0, z0), (s * 0.301, y1, z1))
            for zz in (z0, z1):
                caixa_de(bg, (s * 0.30, y0 - 0.015, zz - 0.008), (s * 0.312, y1 + 0.015, zz + 0.008))
            for yy in (y0, y1):
                caixa_de(bg, (s * 0.30, yy - 0.015, z0), (s * 0.312, yy + 0.015, z1))
            for k in range(n):
                zz = z0 + (k + 0.5) * (z1 - z0) / n
                caixa(bg, (s * 0.307, (y0 + y1) / 2, zz), (0.022, y1 - y0, (z1 - z0) / n * 0.9),
                      Matrix.Rotation(s * 0.7, 3, 'Y'))
            # ferrugem e óleo escorrendo da grade
            for t in (0.2, 0.55, 0.85):
                yy = y0 + (y1 - y0) * t + random.uniform(-0.03, 0.03)
                escorrido(V.B(C, 'escorrido_s' if t != 0.55 else 'oleo_s'), Vector((s * 0.3013, yy, z0 - 0.01)),
                          Vector((s * 0.3013, yy, z0 - random.uniform(0.07, 0.14))), Vector((0, 0.012, 0)))
    # porta trocada (primer cinza, aparafusada por fora) no lado −x e remendo soldado no lado +x
    caixa_de(V.B(C, 'cinza'), (-0.304, 0.25, 0.545), (-0.300, 0.56, 0.79))
    for yy in (0.26, 0.405, 0.55):
        for zz in (0.555, 0.78):
            parafuso(bf, (-0.304, yy, zz), (-1, 0, 0), 0.005)
    caixa_de(V.B(C, 'remendo'), (0.300, -0.33, 0.38), (0.305, -0.08, 0.52))
    for k in range(26):
        t = k / 25
        yy = -0.33 + 0.25 * t
        for zz in (0.38, 0.52):
            esfera(V.B(C, 'cordao', liso=True), Vector((0.3055, yy, zz + 0.002 * math.sin(k * 1.9))), 0.0045, 6, (1, 1, 0.7))
    mancha_plano(V.B(C, 'solda_s'), Vector((0.3008, -0.2, 0.38)), Y, Z, 0.06, 0.7, alongar=2.4)
    # testeira traseira do capô: olho traseiro, lanternas, listras
    caixa_de(V.B(C, 'listras'), (-0.28, -1.335, 0.36), (0.28, -1.33, 0.44))
    cil(bg, Vector((0, -1.345, 0.62)), 0.045, 0.03, Y, 20)
    cil(V.B(C, 'olho', bev=False), Vector((0, -1.362, 0.62)), 0.03, 0.004, Y, 20)
    for s in (-1, 1):
        cil(bg, Vector((s * 0.22, -1.345, 0.52)), 0.026, 0.03, Y, 16)
        cil(V.B(C, 'led_v', bev=False), Vector((s * 0.22, -1.362, 0.52)), 0.019, 0.004, Y, 16)
    digitos(V.B(C, 'estencil', bev=False), '0731', Vector((-0.10, -1.3312, 0.72)), (1, 0, 0), (0, 0, 1), 0.06, 0.004)
    # --- nariz de sensores (sem cabine): bloco blindado inclinado
    nar = [(0.78, ZD), (1.37, ZD), (1.37, 0.47), (1.12, 0.80), (0.78, 0.80)]
    prisma_yz(ba, nar, -0.335, 0.335)
    v_s = Vector((0, -0.25, 0.33)).normalized()
    n_s = Vector((0, 0.33, 0.25)).normalized()
    rot_s = Matrix((X, v_s, n_s)).transposed()
    meio = Vector((0, 1.245, 0.635))
    # chapa de blindagem da rampa com parafusos
    caixa(V.B(C, 'grafite'), meio + n_s * 0.008, (0.62, 0.40, 0.016), rot_s)
    for u in (-0.28, -0.14, 0.14, 0.28):
        for v in (-0.18, 0.18):
            parafuso(bf, meio + n_s * 0.016 + X * u + v_s * v, n_s, 0.007)
    # olho vermelho: carcaça, aro com parafusos, lente, viseira
    ce = meio + n_s * 0.016
    cil(bg, ce + n_s * 0.025, 0.09, 0.05, n_s, 32)
    anel_grosso(bf, ce + n_s * 0.05, 0.095, 0.068, 0.012, n_s, 32)
    cil(V.B(C, 'vidro', bev=False), ce + n_s * 0.044, 0.066, 0.006, n_s, 32)
    cil(V.B(C, 'olho', bev=False), ce + n_s * 0.048, 0.032, 0.004, n_s, 24)
    toro(V.B(C, 'olho', bev=False), ce + n_s * 0.0485, 0.05, 0.003, n_s, 32, 6)
    for k in range(8):
        a = k * PI / 4
        parafuso(bf, ce + n_s * 0.056 + (X * math.cos(a) + v_s * math.sin(a)) * 0.082, n_s, 0.004)
    caixa(V.B(C, 'amarelo_gasto'), ce + n_s * 0.035 + v_s * 0.10, (0.24, 0.07, 0.012),
          Matrix((X, n_s, v_s)).transposed())                                                 # viseira (aba)
    # chapas laterais do nariz (uma trocada em zarcão), números apagados
    for s in (-1, 1):
        caixa_de(V.B(C, 'zarcao' if s > 0 else 'grafite'), (s * 0.335, 0.82, 0.36), (s * 0.347, 1.33, 0.74))
        for yy in (0.84, 1.0, 1.16, 1.31):
            for zz in (0.38, 0.72):
                parafuso(bf, (s * 0.347, yy, zz), (s, 0, 0), 0.006)
        digitos(V.B(C, 'estencil', bev=False), '07-311', Vector((s * 0.3485, 1.25 if s < 0 else 0.90, 0.60)),
                (0, s, 0), (0, 0, 1), 0.05, 0.0035, 0.3)
        for yy in (0.92, 1.18):
            escorrido(V.B(C, 'escorrido_s'), Vector((s * 0.3482, yy, 0.715)), Vector((s * 0.3482, yy, 0.45)), Vector((0, 0.01, 0)))
    # faróis (carcaça, lente, grade) e marcadores
    for s in (-1, 1):
        cf = Vector((s * 0.22, 1.37, 0.40))
        cil(bg, cf + Y * 0.0225, 0.042, 0.045, Y, 24)
        cil(V.B(C, 'farol', bev=False), cf + Y * 0.0455, 0.033, 0.003, Y, 24)
        for zz in (-0.02, 0.0, 0.02):
            viga(bf, cf + Vector((-0.042, 0.048, zz)), cf + Vector((0.042, 0.048, zz)), 0.004)
        cil(V.B(C, 'led_v', bev=False), Vector((s * 0.31, 1.372, 0.44)), 0.012, 0.006, Y, 12)
        # câmeras nos cantos de cima da rampa
        cc = Vector((s * 0.27, 1.10, 0.815))
        caixa(bg, cc, (0.05, 0.06, 0.03))
        cil(V.B(C, 'vidro', bev=False), cc + Vector((0, 0.031, 0)), 0.011, 0.004, Y, 12)
        cil(V.B(C, 'led_v', bev=False), cc + Vector((s * -0.016, 0.031, 0.01)), 0.003, 0.003, Y, 6)
    # barra de sensores na frente do capô (acima do nariz)
    caixa_de(bg, (-0.26, 0.78, 0.80), (0.26, 0.80, 0.855))
    for k in range(7):
        cil(V.B(C, 'vidro', bev=False), Vector((-0.21 + k * 0.07, 0.8015, 0.828)), 0.012, 0.004, Y, 12)
    # lidar: mastro, colar e cabeça girando
    caixa_de(bg, (-0.06, 0.92, 0.80), (0.06, 1.04, 0.83))
    cil(bg, Vector((0, 0.98, 0.865)), 0.032, 0.07, Z, 16)
    toro(bf, (0, 0.98, 0.9), 0.05, 0.006, Z, 24, 6)
    V.no('lidar', C, (0, 0.98, 0.9))
    bl = V.B('lidar', 'grafite')
    cil(bl, Vector((0, 0.98, 0.93)), 0.058, 0.055, Z, 32)
    cil(V.B('lidar', 'vidro', bev=False), Vector((0, 0.98, 0.928)), 0.0595, 0.024, Z, 32)
    caixa(V.B('lidar', 'laser', bev=False), (0, 0.98 + 0.0598, 0.928), (0.022, 0.002, 0.018))
    caixa(V.B('lidar', 'laser', bev=False), (0, 0.98 - 0.0598, 0.928), (0.022, 0.002, 0.018))
    cil(bl, Vector((0, 0.98, 0.962)), 0.045, 0.01, Z, 24)
    caixa(bl, (0.0, 0.98 + 0.045, 0.965), (0.02, 0.02, 0.008))                               # aleta (mostra o giro)
    # antena e GPS
    tubo(V.B(C, 'aco', liso=True), (0.22, 0.30, 0.86), (0.22, 0.30, 1.08), 0.003, 6)
    cil(bf, Vector((0.22, 0.30, 0.87)), 0.012, 0.02, Z, 10)
    cil(V.B(C, 'led_v', bev=False), Vector((0.22, 0.30, 1.082)), 0.005, 0.006, Z, 8)
    cil(bg, Vector((0.22, 0.74, 0.868)), 0.03, 0.016, Z, 16)
    # --- teto: tampa do radiador e dois ventiladores
    caixa_de(bg, (-0.26, -1.29, 0.86), (0.26, -0.43, 0.874))
    for k in range(10):
        for s in (-1, 1):
            parafuso(bf, (s * 0.25, -1.27 + k * 0.092, 0.874), Z, 0.004)
    for k, yf in enumerate((-1.07, -0.65)):
        cil(V.B(C, 'radiador', bev=False), Vector((0, yf, 0.8745)), 0.136, 0.001, Z, 40)
        anel_grosso(V.B(C, 'grafite', liso=True), (0, yf, 0.89), 0.15, 0.137, 0.032, Z, 48)
        for kk in range(10):
            a = kk * PI / 5
            d = Vector((math.cos(a), math.sin(a), 0))
            viga(bf, Vector((0, yf, 0.906)) + d * 0.022, Vector((0, yf, 0.906)) + d * 0.146, 0.005)
        toro(bf, (0, yf, 0.906), 0.075, 0.0028, Z, 32, 6)
        toro(bf, (0, yf, 0.906), 0.118, 0.0028, Z, 40, 6)
        cil(bf, Vector((0, yf, 0.906)), 0.024, 0.01, Z, 16)
        V.no('ventilador%d' % k, C, (0, yf, 0.884))
        bv = V.B('ventilador%d' % k, 'grafite')
        cil(bv, Vector((0, yf, 0.884)), 0.03, 0.022, Z, 16)
        for b in range(6):
            a = b * PI / 3
            rot = Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(0.45, 3, 'X')
            caixa(bv, Vector((0, yf, 0.884)) + Matrix.Rotation(a, 3, 'Z') @ Vector((0.08, 0, 0)), (0.10, 0.04, 0.004), rot)
        caixa(V.B('ventilador%d' % k, 'amarelo_gasto'), Vector((0.11, yf, 0.887)), (0.03, 0.035, 0.002),
              Matrix.Rotation(0.45, 3, 'X'))
    # fuligem e pó no teto do radiador
    mancha_plano(V.B(C, 'fuligem_s'), Vector((0.05, -0.25, 0.8605)), X, Y, 0.18, 0.85, alongar=1.2)
    mancha_plano(V.B(C, 'po_s'), Vector((-0.15, -0.9, 0.8745)), X, Y, 0.12, 0.7)
    # --- escapamento: base, chaminé, quebra-faíscas, tampa basculante, fuligem
    caixa_de(bf, (-0.08, 0.10, 0.86), (0.08, 0.32, 0.90))
    bq = V.B(C, 'queimado', liso=True)
    cil(bq, Vector((0, 0.21, 0.96)), 0.042, 0.12, Z, 24)
    for zz in (0.915, 0.985):
        anel_grosso(V.B(C, 'ferro', liso=True), (0, 0.21, zz), 0.05, 0.04, 0.012, Z, 24)
    for k in range(8):
        parafuso(bf, (math.cos(k * PI / 4) * 0.07, 0.21 + math.sin(k * PI / 4) * 0.09, 0.90), Z, 0.005)
    V.no('tampa_esc', C, (0, 0.21 - 0.045, 1.02))
    cil(V.B('tampa_esc', 'queimado'), Vector((0, 0.21, 1.025)), 0.048, 0.006, Z, 24)
    cil(bf, Vector((0, 0.21 - 0.046, 1.02)), 0.006, 0.05, X, 8)
    mancha_plano(V.B(C, 'fuligem_s'), Vector((0, 0.21, 0.9005)), X, Y, 0.13, 0.95)
    for s in (-1, 1):
        escorrido(V.B(C, 'fuligem_s'), Vector((s * 0.29, 0.2, 0.81)), Vector((s * 0.3013, 0.2, 0.55)), Vector((0, 0.03, 0)), 0.8)
    # filtro de ar com grade
    caixa_de(ba, (-0.17, 0.42, 0.86), (0.17, 0.70, 0.95))
    for s in (-1, 1):
        caixa_de(V.B(C, 'radiador', bev=False), (s * 0.17, 0.45, 0.875), (s * 0.1715, 0.67, 0.935))
        for k in range(5):
            caixa(bg, (s * 0.175, 0.56, 0.882 + k * 0.012), (0.01, 0.22, 0.006), Matrix.Rotation(s * 0.6, 3, 'Y'))
    # eletrocalha com cabos no teto (sensores → caixa de junção)
    caixa_de(bf, (-0.245, -0.40, 0.86), (-0.19, 0.76, 0.866))
    for s in (-1, 1):
        caixa_de(bf, (-0.2175 + s * 0.0255, -0.40, 0.86), (-0.2175 + s * 0.0285, 0.76, 0.885))
    for k, mt in enumerate(('cabo_v', 'cabo_a', 'cabo_p')):
        xx = -0.23 + k * 0.012
        tubo(V.B(C, mt, liso=True), (xx, -0.40, 0.872), (xx, 0.76, 0.872), 0.005, 8)
    for yy in (-0.2, 0.15, 0.5):
        caixa(bf, (-0.2175, yy, 0.885), (0.06, 0.012, 0.004))
    caixa_de(bg, (-0.26, -0.43, 0.86), (-0.17, -0.34, 0.94))                                 # caixa de junção
    cil(V.B(C, 'led_a', bev=False), Vector((-0.215, -0.341, 0.92)), 0.006, 0.004, Y, 8)
    # caixas de bateria no estrado (dos dois lados), respiros e cabos entrando no capô
    for s in (-1, 1):
        caixa_de(bg, (s * 0.302, 0.40, ZD), (s * 0.356, 0.76, 0.53))
        caixa_de(V.B(C, 'amarelo_gasto'), (s * 0.300, 0.395, 0.52), (s * 0.358, 0.765, 0.535))
        for k in range(6):
            caixa_de(V.B(C, 'buraco', bev=False), (s * 0.356, 0.44 + k * 0.05, 0.47), (s * 0.3565, 0.47 + k * 0.05, 0.476))
        for k in range(3):
            cil(V.B(C, 'cobre'), Vector((s * 0.33, 0.47 + k * 0.1, 0.545)), 0.007, 0.02, Z, 8)
            mangueira(V.B(C, 'cabo_p' if k else 'cabo_v', liso=True),
                      bezier((s * 0.33, 0.47 + k * 0.1, 0.555), (s * 0.33, 0.47 + k * 0.1, 0.6), (s * 0.31, 0.5 + k * 0.1, 0.62),
                             (s * 0.30, 0.5 + k * 0.1, 0.63), 6), 0.005)
        escorrido(V.B(C, 'escorrido_s'), Vector((s * 0.3572, 0.62, 0.518)), Vector((s * 0.3572, 0.62, 0.36)), Vector((0, 0.01, 0)))
        mancha_plano(V.B(C, 'oleo_s'), Vector((s * 0.33, -0.1, ZD + 0.0008)), Y, X, 0.05, 0.9, alongar=2.0)
    # --- limpa-trilhos amassado (frente) com listras no frisão de baixo
    bc = V.B(C, 'amarelo_gasto')
    ini = len(bc.verts)
    A, Cd, Ce = Vector((0, 1.56, 0.035)), Vector((0.35, 1.42, 0.035)), Vector((-0.35, 1.42, 0.035))
    for Cx in (Cd, Ce):
        for k in range(8):
            t = k / 7
            b = A.lerp(Cx, t)
            viga(bc, b, Vector((b.x, 1.415, 0.185)), 0.016)
        viga(V.B(C, 'listras'), A, Cx, 0.024)
    viga(bc, Vector((-0.355, 1.415, 0.185)), Vector((0.355, 1.415, 0.185)), 0.022)
    amassar(bc, ini, (0.13, 1.50, 0.07), 0.12, 0.035, (-0.3, -1, 0.25))
    amassar(bc, ini, (-0.24, 1.46, 0.05), 0.08, 0.02, (0.2, -1, 0.1))
    caixa(bf, (0, 1.40, 0.19), (0.2, 0.03, 0.03))
    # --- sob o estrado: reator de cristal na gaiola + anel de campo, reservatórios de ar
    bga = V.B(C, 'ferro')
    for sx in (-1, 1):
        for sy in (-1, 1):
            viga(bga, Vector((sx * 0.16, sy * 0.22, 0.05)), Vector((sx * 0.16, sy * 0.22, ZB)), 0.016)
        for zz in (0.05, 0.19):
            viga(bga, Vector((sx * 0.16, -0.22, zz)), Vector((sx * 0.16, 0.22, zz)), 0.012)
        viga(bga, Vector((sx * 0.16, -0.22, 0.06)), Vector((sx * 0.16, 0.22, 0.18)), 0.008)
    for sy in (-1, 1):
        for zz in (0.05, 0.19):
            viga(bga, Vector((-0.16, sy * 0.22, zz)), Vector((0.16, sy * 0.22, zz)), 0.012)
        caixa_de(V.B(C, 'listras_v'), (-0.15, sy * 0.222, 0.06), (0.15, sy * 0.232, 0.10))
    bcr = V.B(C, 'cristal', bev=False)
    for k, (dx, dy, inc, h, r) in enumerate(((0, 0, 0, 0.13, 0.034), (0.05, 0.04, 0.3, 0.08, 0.022), (-0.05, -0.03, -0.28, 0.08, 0.024),
                                             (0.03, -0.07, 0.25, 0.065, 0.018), (-0.04, 0.07, -0.22, 0.07, 0.019))):
        eixo = Vector((math.sin(inc), math.sin(inc * 0.6), math.cos(inc)))
        base = Vector((dx, dy, 0.07))
        prisma(bcr, base, r, r * 0.9, 0.0, h * 0.75, 6, eixo, k * 0.4)
        prisma(bcr, base + eixo.normalized() * h * 0.75, r * 0.9, 0.0, 0.0, h * 0.25, 6, eixo, k * 0.4)
    cil(bga, Vector((0, 0, 0.065)), 0.08, 0.015, Z, 24)                                       # berço do cristal
    for k in range(4):
        a = k * PI / 2 + PI / 4
        viga(bga, Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.065)), Vector((math.cos(a) * 0.16 * 1.0, math.sin(a) * 0.22, 0.05)), 0.01)
    V.no('anel_campo', C, (0, 0, 0.13))
    toro(V.B('anel_campo', 'campo', bev=False), (0, 0, 0.13), 0.105, 0.006, Z, 48, 8)
    for k in range(3):
        a = k * 2 * PI / 3
        caixa(V.B('anel_campo', 'ferro'), (math.cos(a) * 0.105, math.sin(a) * 0.105, 0.13), (0.026, 0.026, 0.022),
              Matrix.Rotation(a, 3, 'Z'))
    for sy in (-1, 1):                                                                        # cabos do reator ao estrado
        for k, mt in enumerate(('cabo_v', 'cabo_p')):
            pts = bezier((-0.04 + k * 0.08, sy * 0.10, 0.2), (-0.04 + k * 0.08, sy * 0.14, 0.15),
                         (-0.04 + k * 0.08, sy * 0.2, 0.17), (-0.04 + k * 0.08, sy * 0.21, ZB), 8)
            mangueira(V.B(C, mt, liso=True), pts, 0.007)
    for s in (-1, 1):
        reservatorio(V, s * 0.265, -0.48, 0.42, 0.145)
    V.fechar()
    # luzes: faróis, olho, cristal
    luzes = []
    for s in (-1, 1):
        d = bpy.data.lights.new('Farol', 'SPOT')
        d.energy, d.color, d.spot_size, d.shadow_soft_size = 25.0, (1.0, 0.85, 0.62), math.radians(55), 0.02
        o = bpy.data.objects.new('Farol', d)
        sc.collection.objects.link(o)
        o.parent = V.nos[C][0]
        o.location = Vector((s * 0.22, 1.42, 0.40)) - V.nos[C][1]
        o.rotation_euler = (math.radians(80), 0, 0)
        luzes.append(o)
    for (nome, cor, en, pos, raio) in (('Olho', (1.0, 0.05, 0.02), 1.5, ce + n_s * 0.07, 0.03),
                                       ('Reator', VIOLETA, 6.0, Vector((0, 0, 0.13)), 0.05)):
        d = bpy.data.lights.new(nome, 'POINT')
        d.energy, d.color, d.shadow_soft_size = en, cor, raio
        o = bpy.data.objects.new(nome, d)
        sc.collection.objects.link(o)
        o.parent = V.nos[C][0]
        o.location = pos - V.nos[C][1]
    # fumaça (no mundo: o trem anda para +y, a fumaça fica para trás e sobe)
    for k in range(14):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        o = malha('fumaca', bm, 'fumaca')
        FUMACAS.append(o)
    return V


# ------------------------------------------------------------------ VAGÃO DE CARGA
def mossas(lista):
    def f(u, v):
        return sum(p * math.exp(-((u - a) ** 2 + (v - b) ** 2) / (r * r)) for (a, b, r, p) in lista)
    return f


def grade_chapa(nome, V, mat, f, nu, nv, virar=False):
    """Chapa (grade) com espessura para dentro; virar=True inverte a face para a normal apontar para fora."""
    bm = bmesh.new()
    vs = [[bm.verts.new(f(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            q = (vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1])
            bm.faces.new(tuple(reversed(q)) if virar else q)
    me = bpy.data.meshes.new(V.nome + '_' + nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(V.nome + '_' + nome, me)
    sc.collection.objects.link(o)
    o.data.materials.append(M[mat])
    e, p = V.nos['corpo']
    o.parent = e
    o.location = -p
    sol = o.modifiers.new('Espessura', 'SOLIDIFY')
    sol.thickness = 0.016
    sol.offset = -1
    sol.use_even_offset = True
    return o


TAMPAS = []                  # (vazio, s, fase)
PISTOES = []                 # (camisa, haste, base, vazio_tampa, s, lug_fechado, dobra)


def vagao_carga():
    V = Veiculo('vagao_carga', 0.0)
    C = 'corpo'
    V.no(C, 'raiz', (0, 0, 0.20))
    estrado(V, 'grafite')
    truque(V, 0, -Y_TRQ, False, 'disco')
    truque(V, 1, Y_TRQ, False, 'disco')
    ZT = 0.79
    # --- paredes laterais amassadas (mossas entre os montantes) e cabeceiras
    MOS = {1: [(-0.86, 0.52, 0.09, 0.022), (-0.30, 0.68, 0.07, 0.016), (0.80, 0.45, 0.11, 0.028), (0.28, 0.40, 0.06, 0.012),
               (-1.25, 0.42, 0.06, 0.01)],
           -1: [(-0.80, 0.42, 0.09, 0.025), (0.30, 0.66, 0.06, 0.014), (0.78, 0.48, 0.08, 0.02), (-0.33, 0.42, 0.05, 0.01),
                (1.24, 0.6, 0.05, 0.012)]}
    dent = {s: mossas(MOS[s]) for s in (-1, 1)}
    for s in (-1, 1):
        def f(u, v, s=s):
            y, z = -1.36 + 2.72 * u, ZD + (ZT - ZD) * v
            return Vector((s * (0.36 - dent[s](y, z)), y, z))
        grade_chapa('parede%d' % s, V, 'zarcao', f, 90, 16, virar=s < 0)
    MOS_C = {1: [(0.12, 0.55, 0.08, 0.02)], -1: [(-0.15, 0.45, 0.09, 0.024)]}
    for e in (-1, 1):
        dc = mossas(MOS_C[e])

        def f(u, v, e=e, dc=dc):
            x, z = -0.36 + 0.72 * u, ZD + (ZT - ZD) * v
            return Vector((x, e * (1.36 - dc(x, z)), z))
        grade_chapa('cabeceira%d' % e, V, 'zarcao', f, 24, 16, virar=e > 0)
    bz, bf = V.B(C, 'zarcao'), V.B(C, 'ferro')
    ESTACAS = (-1.12, -0.56, 0.0, 0.56, 1.12)
    for s in (-1, 1):
        caixa_de(bz, (s * 0.352, -1.375, ZT), (s * 0.376, 1.375, ZT + 0.025))                # friso de cima
        for yk in ESTACAS:
            caixa_de(bz, (s * 0.36, yk - 0.02, ZD), (s * 0.378, yk + 0.02, ZT))              # montante
            for zz in (0.36, 0.5, 0.64, 0.76):
                parafuso(bf, (s * 0.378, yk, zz), (s, 0, 0), 0.0045)
            escorrido(V.B(C, 'escorrido_s'), Vector((s * 0.3612, yk + 0.03, ZT - 0.005)),
                      Vector((s * 0.3612, yk + 0.034, ZT - random.uniform(0.18, 0.34))), Vector((0, 0.012, 0)),
                      ajuste=lambda p, s=s: Vector((s * (0.3612 - dent[s](p.y, p.z)), p.y, p.z)))
        for yy in (-1.36, 1.36):
            caixa_de(bz, (s * 0.345, yy - 0.015, ZD), (s * 0.375, yy + 0.015, ZT + 0.025))   # canto
        # dobradiças das tampas no friso
        for yy in (-1.2, -0.7, -0.2, 0.2, 0.7, 1.2):
            caixa_de(bf, (s * 0.352, yy - 0.025, ZT + 0.012), (s * 0.374, yy + 0.025, ZT + 0.03))
        tubo(V.B(C, 'aco', liso=True), (s * 0.366, -1.37, 0.822), (s * 0.366, 1.37, 0.822), 0.0045, 8)
    for e in (-1, 1):
        caixa_de(bz, (-0.375, e * 1.352, ZT), (0.375, e * 1.376, ZT + 0.025))
        for x in (-0.18, 0.18):
            caixa_de(bz, (x - 0.02, e * 1.36, ZD), (x + 0.02, e * 1.378, ZT))
    # remendo aparafusado (lado −x), cordão de solda de reparo, calor da solda
    caixa_de(V.B(C, 'remendo'), (-0.366, 0.12, 0.40), (-0.3605, 0.44, 0.62))
    for k in range(5):
        for zz in (0.41, 0.61):
            parafuso(bf, (-0.366, 0.13 + k * 0.075, zz), (-1, 0, 0), 0.005)
    for zz in (0.47, 0.54):
        parafuso(bf, (-0.366, 0.13, zz), (-1, 0, 0), 0.005)
        parafuso(bf, (-0.366, 0.43, zz), (-1, 0, 0), 0.005)
    for s in (-1, 1):
        y0, y1 = (-0.52, -0.06) if s < 0 else (0.06, 0.52)
        n = 40
        for k in range(n + 1):
            yy = y0 + (y1 - y0) * k / n
            esfera(V.B(C, 'cordao', liso=True), Vector((s * (0.3612 - dent[s](yy, 0.56)), yy, 0.56 + 0.003 * math.sin(k * 1.3))),
                   0.0042, 6, (0.9, 0.9, 0.7))
        mancha_plano(V.B(C, 'solda_s'), Vector((s * 0.3608, (y0 + y1) / 2, 0.56)), Y, Z, 0.05, 0.75, alongar=4.5,
                     ajuste=lambda p, s=s: Vector((s * (0.3608 - dent[s](p.y, p.z)), p.y, p.z)))
        # número de série apagado e mancha de tinta cinza por cima de parte dele
        y_num = s * 0.70
        digitos(V.B(C, 'estencil', bev=False), '31-0472', Vector((s * 0.3611, y_num, 0.67)), (0, s, 0), (0, 0, 1), 0.05, 0.0035, 0.28)
        caixa_de(V.B(C, 'cinza', bev=False), (s * 0.3612, y_num + s * 0.20, 0.66), (s * 0.3619, y_num + s * 0.29, 0.73))
        # óleo da hidráulica escorrendo nas pontas
        for yy in (-1.28, 1.28):
            escorrido(V.B(C, 'oleo_s'), Vector((s * 0.3612, yy, 0.5)), Vector((s * 0.3612, yy, ZD + 0.01)), Vector((0, 0.008, 0)))
    # --- minério: leito irregular e pedras (com lascas de cristal raras)
    bm = bmesh.new()
    nu, nv = 60, 14

    def monte(x, y):
        return 0.60 + 0.13 * (1 - (x / 0.36) ** 2) ** 0.6 * (1 - (abs(y) / 1.36) ** 4) * (0.85 + 0.15 * math.sin(y * 7.0 + x * 5))
    vs = []
    for i in range(nu + 1):
        y = -1.345 + 2.69 * i / nu
        vs.append([bm.verts.new((-0.345 + 0.69 * j / nv, y, monte(-0.345 + 0.69 * j / nv, y) + random.uniform(-0.01, 0.01)))
                   for j in range(nv + 1)])
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    V.sep(C, 'leito_minerio', bm, 'minerio')
    for mt, n in (('minerio', 260), ('minerio2', 140)):
        bp = V.B(C, mt, bev=False)
        for k in range(n):
            r = random.uniform(0.014, 0.04)
            x, y = random.uniform(-(0.335 - r), 0.335 - r), random.uniform(-(1.335 - r), 1.335 - r)
            pedra(bp, (x, y, monte(x, y) + r * 0.25), r, 0.7)
    bcr = V.B(C, 'cristal', bev=False)
    for k in range(9):
        x, y = random.uniform(-0.28, 0.28), random.uniform(-1.25, 1.25)
        prisma(bcr, (x, y, monte(x, y) - 0.005), 0.009, 0.0, 0.0, 0.035, 6,
               (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 1), random.uniform(0, 1))
    # pó de minério nos frisos e no estrado
    for s in (-1, 1):
        mancha_plano(V.B(C, 'po_s'), Vector((s * 0.364, random.uniform(-0.8, 0.8), ZT + 0.0255)), Y, X, 0.06, 0.8, alongar=4)
    # --- 4 tampas basculantes (dobradiça no friso), abertas por pistões nas cabeceiras
    for s in (-1, 1):
        for h in (-1, 1):
            ch = 'tampa%d%d' % (s, h)
            V.no(ch, C, (s * 0.366, 0, 0.822))
            bt = V.B(ch, 'zarcao' if (s, h) != (1, -1) else 'amarelo_gasto')   # uma tampa trocada (amarela)
            y0, y1 = (0.012, 1.385) if h > 0 else (-1.385, -0.012)
            caixa_de(bt, (s * 0.008, y0, 0.815), (s * 0.366, y1, 0.829))
            for yr in (y0 + 0.08, (y0 + y1) / 2, y1 - 0.08):
                caixa_de(bt, (s * 0.02, yr - 0.012, 0.829), (s * 0.35, yr + 0.012, 0.846))
            caixa_de(bt, (s * 0.008, y0, 0.80), (s * 0.016, y1, 0.815))                    # lábio de vedação
            caixa_de(bt, (s * 0.20, h * 1.377, 0.778), (s * 0.30, h * 1.385, 0.815))        # orelha do pistão
            cil(V.B(ch, 'ferro'), Vector((s * 0.236, h * 1.392, 0.80)), 0.008, 0.03, Y, 10)
            for k in range(8):
                parafuso(V.B(ch, 'ferro'), (s * 0.06 + s * k * 0.04, (y0 + y1) / 2, 0.846), Z, 0.0045)
            escorrido(V.B(ch, 'escorrido_s'), Vector((s * 0.2, h * 1.386, 0.81)), Vector((s * 0.21, h * 1.386, 0.78)), Vector((0.01, 0, 0)))
            mancha_plano(V.B(ch, 'po_s'), Vector((s * 0.18, (y0 + y1) / 2 + 0.2, 0.8292)), X, Y, 0.08, 0.35, alongar=1.5)
            TAMPAS.append((V.nos[ch][0], s, h))
            # pistão: camisa articulada na cabeceira, haste na orelha da tampa
            B_ = Vector((s * 0.08, h * 1.40, 0.43))
            L0 = Vector((s * 0.236, h * 1.40, 0.80))
            caixa_de(bf, (s * 0.06, h * 1.36, 0.41), (s * 0.10, h * 1.388, 0.45))
            cil(bf, B_, 0.01, 0.034, Y, 10)
            cc, ch_h = 'camisa%d%d' % (s, h), 'haste%d%d' % (s, h)
            V.no(cc, C, B_)
            V.no(ch_h, cc, B_)
            cil(V.B(cc, 'amarelo_gasto', liso=True), B_ + Z * 0.16, 0.019, 0.28, Z, 16)
            cil(V.B(cc, 'ferro'), B_ + Z * 0.03, 0.022, 0.02, Z, 16)
            cil(V.B(cc, 'ferro'), B_ + Z * 0.29, 0.022, 0.02, Z, 16)
            caixa(V.B(cc, 'ferro'), B_ + Z * 0.008, (0.02, 0.03, 0.03))
            cil(V.B(ch_h, 'cromo', liso=True), B_ + Z * 0.17, 0.0085, 0.34, Z, 12)
            cil(V.B(ch_h, 'ferro'), B_ + Z * 0.34, 0.012, 0.024, Y, 10)
            PISTOES.append((V.nos[cc][0], V.nos[ch_h][0], B_, s, h, L0))
            # mangueira hidráulica da camisa ao distribuidor
            mangueira(V.B(C, 'borracha', liso=True), bezier(B_ + Vector((s * 0.02, 0, 0.02)), B_ + Vector((s * 0.02, h * 0.012, -0.04)),
                                                            Vector((s * 0.05, h * 1.395, 0.37)), Vector((s * 0.035, h * 1.395, 0.39)), 8), 0.006)
        # (por ponta) distribuidor hidráulico e cano descendo ao estrado
    for h in (-1, 1):
        caixa_de(V.B(C, 'amarelo_gasto'), (-0.04, h * 1.36, 0.36), (0.04, h * 1.392, 0.42))
        for x in (-0.025, 0.025):
            cil(V.B(C, 'led_a' if x < 0 else 'led_v', bev=False), Vector((x, h * 1.393, 0.405)), 0.005, 0.003, Y, 8)
        tubo(V.B(C, 'ferro', liso=True), (0, h * 1.38, 0.36), (0, h * 1.38, 0.335), 0.007)
        mancha_plano(V.B(C, 'oleo_s'), Vector((0.0, h * 1.3925, 0.37)), X, Z, 0.03, 0.9)
        escorrido(V.B(C, 'oleo_s'), Vector((0.012, h * 1.3925, 0.36)), Vector((0.015, h * 1.3925, 0.335)), Vector((0.006, 0, 0)))
    # --- sob o estrado: unidade hidráulica, bateria, reservatório, válvula de freio
    caixa_de(V.B(C, 'amarelo_gasto'), (0.02, 0.06, 0.10), (0.30, 0.44, ZB))
    cil(V.B(C, 'motor', liso=True), Vector((0.16, 0.25, 0.08)), 0.045, 0.22, Y, 20)
    cil(bf, Vector((0.16, 0.135, 0.08)), 0.04, 0.012, Y, 20)
    for k in range(6):
        caixa_de(V.B(C, 'buraco', bev=False), (0.301, 0.09 + k * 0.055, 0.13), (0.302, 0.12 + k * 0.055, 0.19))
    mangueira(V.B(C, 'borracha', liso=True), bezier((0.28, 0.44, 0.15), (0.28, 0.6, 0.15), (0.34, 0.5, 0.2), (0.368, 0.5, 0.29), 8), 0.007)
    tubo(V.B(C, 'ferro', liso=True), (0.368, -1.38, 0.29), (0.368, 1.38, 0.29), 0.006)
    caixa_de(V.B(C, 'grafite'), (0.02, -0.44, 0.11), (0.30, -0.08, ZB))
    caixa_de(V.B(C, 'listras'), (0.302, -0.42, 0.12), (0.303, -0.10, 0.15))
    for k in range(3):
        cil(V.B(C, 'cobre'), Vector((0.20, -0.40 + k * 0.03, 0.105)), 0.006, 0.015, Z, 8)
    mangueira(V.B(C, 'cabo_v', liso=True), bezier((0.2, -0.08, 0.15), (0.2, 0.0, 0.12), (0.2, 0.0, 0.12), (0.2, 0.06, 0.15), 6), 0.007)
    reservatorio(V, -0.25, -0.46, 0.40, 0.145)
    caixa_de(V.B(C, 'grafite'), (-0.12, -0.30, 0.12), (-0.03, -0.12, ZB))
    escorrido(V.B(C, 'oleo_s'), Vector((0.301, 0.3, 0.2)), Vector((0.301, 0.3, 0.11)), Vector((0, 0.01, 0)))
    mangueiras_entre(V, e=1)              # para a locomotiva (adiante)
    mangueiras_entre(V, e=-1)             # para o vagão-tanque (atrás)
    V.fechar()
    return V


# ------------------------------------------------------------------ VAGÃO-TANQUE
RT, ZT0, YT = 0.32, 0.66, 1.18              # raio do tanque, z do eixo, meio comprimento da parte reta
PINGOS = []                                 # (objeto, origem, fase)


def no_casco(p, folga=0.0015):
    """Encosta o ponto p no casco cilíndrico (mantém y, projeta no raio)."""
    d = Vector((p.x, 0, p.z - ZT0))
    if d.length < 1e-6:
        d = Vector((0, 0, 1))
    d.normalize()
    return Vector((0, p.y, ZT0)) + d * (RT + folga + MOSSA_T(p.y, math.atan2(p.z - ZT0, p.x)))


MOS_T = [(-0.55, 2.6, 0.12, 0.018), (0.35, -2.7, 0.1, 0.014), (-0.95, -0.5, 0.08, 0.012)]   # (y, ângulo, raio, prof)


def MOSSA_T(y, a):
    return -sum(p * math.exp(-((y - yy) ** 2 + ((a - aa) * RT) ** 2) / (r * r)) for (yy, aa, r, p) in MOS_T)


def casco_tanque(V):
    """Casco por torno: tampos elípticos e parte reta, com mossas."""
    bm = bmesh.new()
    perfil = []
    for k in range(9):
        a = PI / 2 * (1 - k / 8)
        perfil.append((-YT - 0.12 * math.sin(a), RT * math.cos(a)))
    for k in range(1, 30):
        perfil.append((-YT + 2 * YT * k / 30, RT))
    for k in range(9):
        a = PI / 2 * k / 8
        perfil.append((YT + 0.12 * math.sin(a), RT * math.cos(a)))
    n = 64
    aneis = []
    for (y, r) in perfil:
        anel = []
        for k in range(n):
            a = 2 * PI * k / n
            rr = r + (MOSSA_T(y, (a + PI) % (2 * PI) - PI) if r > RT * 0.9 else 0.0)
            anel.append(bm.verts.new((math.cos(a) * rr, y, ZT0 + math.sin(a) * rr)))
        aneis.append(anel)
    for A, B in zip(aneis, aneis[1:]):
        for k in range(n):
            bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = V.sep('corpo', 'casco', bm, 'tanque')
    suavizar(o)
    for pg in o.data.polygons:
        pg.use_smooth = True
    return o


def arco_faixa(bm, yc, r, w, t, a0, a1, n=40):
    """Cinta curva em volta do eixo Y (ângulos a partir de +x, sentido +z)."""
    sec = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        d = Vector((math.cos(a), 0, math.sin(a)))
        c = Vector((0, 0, ZT0))
        sec.append([bm.verts.new(c + d * rr + Vector((0, yy, 0))) for (rr, yy) in ((r, yc - w / 2), (r + t, yc - w / 2), (r + t, yc + w / 2), (r, yc + w / 2))])
    for A, B in zip(sec, sec[1:]):
        for j in range(4):
            bm.faces.new((A[j], A[(j + 1) % 4], B[(j + 1) % 4], B[j]))
    bm.faces.new(sec[0])
    bm.faces.new(list(reversed(sec[-1])))


def berco(bm, yc, w):
    """Berço sob o tanque: chapa com topo em arco (encosta no casco) e base no estrado."""
    pts = []
    for k in range(17):
        a = math.radians(-15 - 150 * k / 16)
        pts.append((math.cos(a) * (RT + 0.004), ZT0 + math.sin(a) * (RT + 0.004)))
    cols = [((x, z), (x, 0.31)) for (x, z) in [(0.33, 0.56)] + pts + [(-0.33, 0.56)]]
    for lado in (yc - w / 2, yc + w / 2):
        pass
    fr = [[bm.verts.new((x, yy, z)) for yy in (yc - w / 2, yc + w / 2)] for ((x, z), _) in cols]
    bs = [[bm.verts.new((x, yy, zb)) for yy in (yc - w / 2, yc + w / 2)] for (_, (x, zb)) in cols]
    for i in range(len(cols) - 1):
        for j in (0, 1):
            bm.faces.new((fr[i][j], fr[i + 1][j], bs[i + 1][j], bs[i][j]))
        bm.faces.new((fr[i][0], fr[i + 1][0], fr[i + 1][1], fr[i][1]))
        bm.faces.new((bs[i][0], bs[i + 1][0], bs[i + 1][1], bs[i][1]))
    for i in (0, len(cols) - 1):
        bm.faces.new((fr[i][0], fr[i][1], bs[i][1], bs[i][0]))


def vagao_tanque():
    V = Veiculo('vagao_tanque', -3.0)
    C = 'corpo'
    V.no(C, 'raiz', (0, 0, 0.20))
    estrado(V, 'grafite', deck=False)
    truque(V, 0, -Y_TRQ, False, 'disco')
    truque(V, 1, Y_TRQ, False, 'disco')
    casco_tanque(V)
    bf, ba = V.B(C, 'ferro'), V.B(C, 'amarelo_gasto')
    for yb in (-Y_TRQ, Y_TRQ):
        berco(V.B(C, 'grafite'), yb, 0.06)
    # anéis de reforço (soldados), cordões de solda circulares
    for yy in (-1.12, -0.32, 0.32, 1.12):
        anel_grosso(V.B(C, 'tanque'), (0, yy, ZT0), RT + 0.008, RT - 0.004, 0.026, Y, 64)
    for yy in (-0.72, 0.72):
        toro(V.B(C, 'cordao', liso=True), (0, yy, ZT0), RT + 0.0005, 0.0035, Y, 64, 6)
    # tampos: faixa amarela de perigo pintada no centro do tampo e anel de parafusos
    for e in (-1, 1):
        cil(V.B(C, 'listras'), Vector((0, e * (YT + 0.118), ZT0)), 0.07, 0.006, Y, 24)
    # cintas sobre o tanque com esticadores até o estrado
    for yy in (-0.62, 0.62):
        arco_faixa(V.B(C, 'aco'), yy, RT + 0.001, 0.035, 0.005, math.radians(-12), math.radians(192))
        for s in (-1, 1):
            a = math.radians(-12) if s > 0 else math.radians(192)
            p0 = Vector((math.cos(a) * (RT + 0.004), yy, ZT0 + math.sin(a) * (RT + 0.004)))
            p1 = Vector((s * 0.338, yy, 0.335))
            tubo(V.B(C, 'aco', liso=True), p0, p1, 0.006)
            cil(ba, p0.lerp(p1, 0.55), 0.012, 0.06, p1 - p0, 10)                              # esticador
            caixa_de(bf, (s * 0.318, yy - 0.025, 0.32), (s * 0.358, yy + 0.025, 0.338))
            escorrido(V.B(C, 'escorrido_s'), no_casco(Vector((math.cos(a + s * 0.0) * RT, yy + 0.02, ZT0 + math.sin(a) * RT))),
                      no_casco(Vector((s * 0.2, yy + 0.025, ZT0 - 0.24))), Vector((0, 0.01, 0)), 0.8, 8, ajuste=no_casco)
    # --- domo com escotilha de drone (alvo de pouso, LEDs, garras de travamento)
    cil(V.B(C, 'tanque', liso=True), Vector((0, 0, 0.99)), 0.13, 0.10, Z, 40)
    anel_grosso(bf, (0, 0, 1.0375), 0.145, 0.12, 0.015, Z, 40)
    for k in range(16):
        a = k * PI / 8
        parafuso(bf, (math.cos(a) * 0.137, math.sin(a) * 0.137, 1.045), Z, 0.004)
    cil(ba, Vector((0, 0, 1.0525)), 0.124, 0.015, Z, 40)
    anel_grosso(V.B(C, 'listras'), (0, 0, 1.0605), 0.115, 0.08, 0.002, Z, 40)
    toro(V.B(C, 'led_a', bev=False), (0, 0, 1.061), 0.07, 0.004, Z, 40, 6)
    esfera(V.B(C, 'led_v', bev=False), (0, 0, 1.061), 0.012, 12, (1, 1, 0.6))
    cil(V.B(C, 'vidro', bev=False), Vector((0.04, 0.0, 1.0615)), 0.008, 0.003, Z, 10)
    for k in range(3):
        a = k * 2 * PI / 3 + 0.5
        d = Vector((math.cos(a), math.sin(a), 0))
        rot = Matrix.Rotation(a, 3, 'Z')
        caixa(bf, Vector((0, 0, 1.06)) + d * 0.142, (0.024, 0.026, 0.04), rot)
        caixa(bf, Vector((0, 0, 1.077)) + d * 0.128, (0.03, 0.022, 0.008), rot)
    cil(bf, Vector((-0.135, 0, 1.05)), 0.01, 0.06, Y, 10)                                  # dobradiça
    caixa(bf, (-0.13, 0, 1.06), (0.03, 0.04, 0.01))
    cil(V.B(C, 'amarelo_gasto', liso=True), Vector((-0.17, 0.0, 1.0)), 0.012, 0.07, Vector((0.6, 0, 1)), 10)   # atuador
    mancha_plano(V.B(C, 'po_s'), Vector((0.05, 0.05, 1.0602)), X, Y, 0.06, 0.6)
    # --- válvula de carga motorizada (vaza seiva) — no topo, adiante do domo
    yv = 0.24
    cil(V.B(C, 'ferro', liso=True), Vector((0, yv, 0.99)), 0.028, 0.06, Z, 20)
    cil(bf, Vector((0, yv, 1.022)), 0.045, 0.01, Z, 20)
    esfera(V.B(C, 'ferro', liso=True), (0, yv, 1.055), 0.035, 16)
    caixa_de(ba, (-0.03, yv - 0.03, 1.085), (0.035, yv + 0.03, 1.13))                    # atuador elétrico
    caixa_de(V.B(C, 'listras'), (-0.03, yv + 0.03, 1.09), (0.035, yv + 0.031, 1.11))
    tubo(V.B(C, 'ferro', liso=True), (0.03, yv, 1.055), (0.10, yv, 1.055), 0.02, 16)
    cil(bf, Vector((0.105, yv, 1.055)), 0.034, 0.012, X, 20)                              # flange
    cil(bf, Vector((0.117, yv, 1.055)), 0.032, 0.01, X, 20)                               # tampa cega
    for k in range(6):
        a = k * PI / 3
        parafuso(bf, (0.123, yv + math.cos(a) * 0.024, 1.055 + math.sin(a) * 0.024), X, 0.0035)
    mangueira(V.B(C, 'cabo_p', liso=True), bezier((-0.03, yv, 1.11), (-0.08, yv, 1.11), (-0.1, 0.1, 1.08), (-0.1, 0.08, 1.04), 8), 0.005)
    # seiva vazando da flange: gota pendurada, poça brilhante e escorrido descendo o casco
    bse = V.B(C, 'seiva', liso=True)
    esfera(bse, (0.112, yv - 0.005, 1.02), 0.008, 10, (1, 1, 1.3))
    mancha_plano(V.B(C, 'seiva_s'), no_casco(Vector((0.11, yv, 0.97))), Y, X, 0.05, 0.95, ajuste=no_casco)
    pts, lats = [], []
    for k in range(25):
        t = k / 24
        a = math.radians(70 - 145 * t)
        yy = yv + 0.012 * math.sin(k * 0.9)
        pts.append(no_casco(Vector((math.cos(a), yy, ZT0 + math.sin(a))), 0.0018))
        lats.append(Vector((0, 0.014 * (1 - 0.5 * t) * (1 + 0.3 * math.sin(k * 1.7)), 0)))
    faixa_caminho(V.B(C, 'seiva_s'), pts, lats, 0.95)
    for dy, comp in ((0.05, 70), (-0.04, 45)):
        pts2, lats2 = [], []
        for k in range(15):
            t = k / 14
            a = math.radians(55 - comp * t)
            pts2.append(no_casco(Vector((math.cos(a), yv + dy + 0.008 * math.sin(k), ZT0 + math.sin(a))), 0.0016))
            lats2.append(Vector((0, 0.007 * (1 - 0.5 * t), 0)))
        faixa_caminho(V.B(C, 'seiva_s'), pts2, lats2, 0.8)
    a_fim = math.radians(-75)
    PINGOS.append(('seiva', no_casco(Vector((math.cos(a_fim), yv, ZT0 + math.sin(a_fim))), 0.004) - Vector((0, 0, 0.004)), 0.0))
    # --- válvula de alívio (mola à mostra) e óleo escorrendo pelo lado −x
    yr = -0.24
    cil(bf, Vector((0, yr, 0.995)), 0.035, 0.04, Z, 20)
    cil(V.B(C, 'aco', liso=True), Vector((0, yr, 1.025)), 0.02, 0.02, Z, 16)
    mola(V.B(C, 'mola', liso=True), (0, yr, 1.035), (0, yr, 1.085), 0.016, 0.0035, 4)
    tubo(V.B(C, 'cromo', liso=True), (0, yr, 1.03), (0, yr, 1.1), 0.005)
    cil(V.B(C, 'amarelo_gasto', liso=True), Vector((0, yr, 1.1)), 0.03, 0.014, Z, 20)
    mancha_plano(V.B(C, 'oleo_s'), no_casco(Vector((-0.04, yr, 0.98))), Y, X, 0.05, 0.9, ajuste=no_casco)
    pts, lats = [], []
    for k in range(21):
        t = k / 20
        a = math.radians(100 + 140 * t)
        pts.append(no_casco(Vector((math.cos(a), yr + 0.01 * math.sin(k * 0.7), ZT0 + math.sin(a))), 0.0017))
        lats.append(Vector((0, 0.016 * (1 - 0.5 * t), 0)))
    faixa_caminho(V.B(C, 'oleo_s'), pts, lats, 0.95)
    # --- visor de nível (lado +x): tubo de vidro, coluna de seiva, grade, escala, registros
    xv, yg, zg0, zg1 = 0.355, 0.80, 0.45, 0.88
    for zz in (zg0, zg1):
        xs = math.sqrt(RT ** 2 - (zz - ZT0) ** 2)
        tubo(V.B(C, 'ferro', liso=True), (xs - 0.01, yg, zz), (xv, yg, zz), 0.012, 12)
        esfera(V.B(C, 'ferro', liso=True), (xv, yg, zz), 0.016, 12)
        cil(ba, Vector(((xs + xv) / 2, yg, zz)), 0.02, 0.02, X, 12)                     # registro
    cil(V.B(C, 'vidro_tubo', liso=True, bev=False), Vector((xv, yg, (zg0 + zg1) / 2)), 0.014, zg1 - zg0 - 0.03, Z, 20)
    V.no('nivel', C, (xv, yg, zg0 + 0.016))
    cil(V.B('nivel', 'seiva', liso=True), Vector((xv, yg, zg0 + 0.016 + 0.13)), 0.0105, 0.26, Z, 16)
    for k in range(3):
        a = k * 2 * PI / 3 + PI / 2
        tubo(V.B(C, 'aco', liso=True), (xv + math.cos(a) * 0.024, yg + math.sin(a) * 0.024, zg0 + 0.01),
             (xv + math.cos(a) * 0.024, yg + math.sin(a) * 0.024, zg1 - 0.01), 0.0028)
    for zz in (zg0 + 0.12, zg0 + 0.30):
        toro(bf, (xv, yg, zz), 0.024, 0.003, Z, 20, 6)
    caixa_de(V.B(C, 'grafite'), (xv - 0.002, yg - 0.05, zg0 + 0.02), (xv + 0.002, yg - 0.03, zg1 - 0.02))
    for k in range(9):
        zz = zg0 + 0.03 + k * 0.045
        caixa_de(V.B(C, 'tinta_branca', bev=False), (xv + 0.002, yg - 0.048, zz), (xv + 0.0025, yg - (0.038 if k % 2 else 0.032), zz + 0.003))
    # --- saída inferior com válvula que pinga
    xo = 0.14
    zb = ZT0 - math.sqrt(RT ** 2 - xo ** 2)
    cil(V.B(C, 'ferro', liso=True), Vector((xo, 0.0, zb - 0.02)), 0.025, 0.07, Z, 16)
    esfera(V.B(C, 'ferro', liso=True), (xo, 0.0, 0.29), 0.032, 14)
    caixa_de(ba, (xo - 0.02, -0.06, 0.275), (xo + 0.02, -0.03, 0.305))                   # atuador
    cil(V.B(C, 'ferro', liso=True), Vector((xo, 0.0, 0.245)), 0.02, 0.05, Z, 14)
    cil(bf, Vector((xo, 0.0, 0.215)), 0.027, 0.012, Z, 16)
    esfera(bse, (xo, 0.0, 0.205), 0.006, 10, (1, 1, 1.4))
    mancha_plano(V.B(C, 'seiva_s'), Vector((xo + 0.0255, 0.0, 0.25)), Y, Z, 0.025, 0.8)
    PINGOS.append(('seiva', Vector((xo, 0.0, 0.199)), 0.5))
    # --- números apagados e sujeira no casco
    for s in (-1, 1):
        a = 0.15 if s > 0 else PI - 0.15
        tang = Vector((-math.sin(a), 0, math.cos(a)))
        cima = tang if s > 0 else -tang
        org = Vector((math.cos(a) * (RT + 0.0015), 0.03 if s < 0 else -0.28, ZT0 + math.sin(a) * (RT + 0.0015))) - cima * 0.025
        digitos(V.B(C, 'estencil', bev=False), '84-2207', org, (0, s, 0), cima, 0.05, 0.0035, 0.3)
        for yy in (-1.0, -0.12, 0.45, 1.0):
            yy += random.uniform(-0.05, 0.05)
            a0 = math.radians(5 if s > 0 else 175)
            pts, lats = [], []
            for k in range(11):
                t = k / 10
                aa = a0 - s * math.radians(70) * t
                pts.append(no_casco(Vector((math.cos(aa), yy + 0.006 * math.sin(k), ZT0 + math.sin(aa))), 0.0016))
                lats.append(Vector((0, 0.012 * (1 - 0.55 * t), 0)))
            faixa_caminho(V.B(C, 'escorrido_s'), pts, lats, 0.7)
        mancha_plano(V.B(C, 'po_s'), no_casco(Vector((0.0, -0.9 + s * 0.3, 1.0))), Y, X, 0.12, 0.7, ajuste=no_casco, alongar=2)
    # --- sob o tanque: reservatório, válvula de controle, bateria pequena
    reservatorio(V, -0.25, -0.46, 0.40, 0.15)
    caixa_de(V.B(C, 'grafite'), (0.18, -0.32, 0.13), (0.30, -0.12, ZB))
    caixa_de(V.B(C, 'listras'), (0.302, -0.30, 0.15), (0.303, -0.14, 0.17))
    mangueiras_entre(V, livre=True, e=-1)
    V.fechar()
    return V


# ------------------------------------------------------------------ via (lastro, dormentes, trilhos)
L_VIA = 24.0
PASSO = 0.5
SEGMENTOS = []


def via():
    variantes = []
    for v in range(5):
        random.seed(100 + v)
        bms = {k: bmesh.new() for k in ('lastro', 'lastro2', 'dormente', 'ferro', 'escorrido_s', 'oleo_s')}
        prisma_xz(bms['lastro'], [(-0.56, 0.0), (0.56, 0.0), (0.44, 0.035), (-0.44, 0.035)], -PASSO / 2 - 0.002, PASSO / 2 + 0.002)
        for yd in (-0.125, 0.125):
            caixa_de(bms['dormente'], (-0.41, yd - 0.045, 0.012), (0.41, yd + 0.045, 0.052))
            for s in (-1, 1):
                caixa_de(bms['ferro'], (s * 0.25 - 0.035, yd - 0.032, 0.052), (s * 0.25 + 0.035, yd + 0.032, 0.06))
                for d in (-1, 1):
                    mangueira(bms['ferro'], [Vector((s * 0.25 + d * 0.03, yd - 0.018, 0.062)), Vector((s * 0.25 + d * 0.022, yd, 0.07)),
                                              Vector((s * 0.25 + d * 0.03, yd + 0.018, 0.062))], 0.0035)
                mancha_plano(bms['escorrido_s'], Vector((s * 0.25, yd + 0.046, 0.04)), X, Z, 0.03, 0.7, alongar=1.5)
            if random.random() < 0.5:
                mancha_plano(bms['oleo_s'], Vector((random.uniform(-0.15, 0.15), yd, 0.0525)), X, Y, 0.04, 0.9, alongar=1.6)
        for k in range(420):
            y = random.uniform(-PASSO / 2, PASSO / 2)
            x = random.uniform(-0.55, 0.55)
            zt = 0.035 if abs(x) < 0.44 else 0.035 * (0.56 - abs(x)) / 0.12
            if abs(x) < 0.42 and (abs(y - 0.125) < 0.047 or abs(y + 0.125) < 0.047):
                continue
            r = random.uniform(0.007, 0.016)
            pedra(bms['lastro' if random.random() < 0.8 else 'lastro2'], (x, y, zt + r * 0.15), r, 0.7)
        variantes.append(bms)
    meshes = []
    for v, bms in enumerate(variantes):
        mm = []
        for k, bm in bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = bpy.data.meshes.new('via_%s_%d' % (k, v))
            bm.to_mesh(me)
            bm.free()
            me.materials.append(M[k])
            mm.append((k, me))
        meshes.append(mm)
    n = int(L_VIA / PASSO)
    for i in range(n):
        e = vazio('via_seg%d' % i, None, (0, -L_VIA / 2 + (i + 0.5) * PASSO, 0))
        for k, me in meshes[(i * 7) % len(meshes)]:
            o = bpy.data.objects.new('via_%s' % k, me)
            sc.collection.objects.link(o)
            o.parent = e
            if k == 'dormente':
                chanfrar(o, 0.004)
        SEGMENTOS.append((e, -L_VIA / 2 + (i + 0.5) * PASSO))
    for s in (-1, 1):                                                                    # trilhos (perfil: patim, alma, boleto)
        bm = bmesh.new()
        x = s * 0.25
        caixa_de(bm, (x - 0.025, -L_VIA / 2, 0.06), (x + 0.025, L_VIA / 2, 0.069))
        caixa_de(bm, (x - 0.005, -L_VIA / 2, 0.069), (x + 0.005, L_VIA / 2, 0.118))
        prisma_xz(bm, [(x - 0.014, 0.118), (x + 0.014, 0.118), (x + 0.014, 0.137), (x - 0.014, 0.137)], -L_VIA / 2, L_VIA / 2)
        chanfrar(malha('trilho', bm, 'trilho'), 0.003)
        bm = bmesh.new()
        caixa_de(bm, (x - 0.0135, -L_VIA / 2, 0.137), (x + 0.0135, L_VIA / 2, Z_TR))
        chanfrar(malha('trilho_topo', bm, 'trilho_topo'), 0.002)


# ------------------------------------------------------------------ montagem
loco = locomotiva()
carga = vagao_carga()
tanq = vagao_tanque()
via()
VEICS = (loco, carga, tanq)
# pingos (gotas de seiva caindo do tanque)
GOTAS = []
for (mt, org, fase) in PINGOS:
    for k in range(2):
        bm = bmesh.new()
        esfera(bm, (0, 0, 0), 0.006, 10, (1, 1, 1.5))
        o = malha('gota', bm, mt)
        suavizar(o)
        for pg in o.data.polygons:
            pg.use_smooth = True
        o.parent = tanq.nos['corpo'][0]
        GOTAS.append((o, org - tanq.nos['corpo'][1], fase + k * 0.5))


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def abertura(f):
    """Ciclo da tampa: abre (0–0,22), fica aberta, fecha (0,62–0,84), fica fechada."""
    f %= 1.0
    if f < 0.22:
        return suave(f / 0.22)
    if f < 0.62:
        return 1.0
    if f < 0.84:
        return 1.0 - suave((f - 0.62) / 0.22)
    return 0.0


ABRE = math.radians(105)
BALANCO = {'locomotiva': (0.0035, 0.0022, 3, 5, 0.0), 'vagao_carga': (0.006, 0.003, 4, 6, 1.3),
           'vagao_tanque': (0.005, 0.0032, 5, 7, 2.4)}
SAIDA_ESC = Vector((0, 3.0 + 0.21, Z_TR + 1.03))
olho_e = forca_de(M['olho'])
campo_e = forca_de(M['campo'])
led_e = forca_de(M['led_a'])
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # via correndo para trás (o trem anda +y)
    for e, y0 in SEGMENTOS:
        e.location.y = ((y0 - DESLOC * fr + L_VIA / 2) % L_VIA) - L_VIA / 2
        e.keyframe_insert('location', index=1, frame=q)
    for V in VEICS:
        rol, sobe, n1, n2, fase = BALANCO[V.nome]
        ec, pc = V.nos['corpo']
        ec.rotation_euler = (0.0012 * math.sin(2 * PI * n2 * fr + fase),
                             rol * math.sin(2 * PI * n1 * fr + fase) + 0.4 * rol * math.sin(2 * PI * (n1 + 3) * fr), 0)
        ec.location = pc + Vector((0, 0, sobe * math.sin(2 * PI * n2 * fr + fase * 0.7)))
        ec.keyframe_insert('rotation_euler', frame=q)
        ec.keyframe_insert('location', frame=q)
        for i in (0, 1):
            eq, pq = V.nos['quadro%d' % i]
            et, pt = V.nos['truque%d' % i]
            dz = 0.0018 * math.sin(2 * PI * (8 + i) * fr + fase + i)
            eq.location = Vector((0, 0, dz))
            eq.rotation_euler = (0, 0.004 * math.sin(2 * PI * (6 + i) * fr + fase), 0)
            eq.keyframe_insert('location', frame=q)
            eq.keyframe_insert('rotation_euler', frame=q)
            em, pm = V.nos['molas%d' % i]
            em.scale = (1, 1, (0.026 + dz) / 0.026)
            em.keyframe_insert('scale', frame=q)
            for j in (-1, 1):
                er, _ = V.nos['rod%d%d' % (i, j)]
                er.rotation_euler = (-2 * PI * VOLTAS * fr, 0, 0)
                er.keyframe_insert('rotation_euler', frame=q)
    # locomotiva: ventiladores, lidar, anel de campo, tampa do escapamento, olho pulsando
    for k in (0, 1):
        ev, _ = loco.nos['ventilador%d' % k]
        ev.rotation_euler = (0, 0, 2 * PI * (12 + k) * fr)
        ev.keyframe_insert('rotation_euler', frame=q)
    el, _ = loco.nos['lidar']
    el.rotation_euler = (0, 0, -2 * PI * 8 * fr)
    el.keyframe_insert('rotation_euler', frame=q)
    ea, _ = loco.nos['anel_campo']
    ea.rotation_euler = (0.09 * math.sin(2 * PI * fr), 0.09 * math.cos(2 * PI * fr), 2 * PI * 3 * fr)
    ea.keyframe_insert('rotation_euler', frame=q)
    et, _ = loco.nos['tampa_esc']
    et.rotation_euler = (math.radians(55) + 0.12 * math.sin(2 * PI * 10 * fr) + 0.06 * math.sin(2 * PI * 17 * fr), 0, 0)
    et.keyframe_insert('rotation_euler', frame=q)
    olho_e.default_value = 18.0 * (0.75 + 0.25 * math.sin(2 * PI * 2 * fr))
    olho_e.keyframe_insert('default_value', frame=q)
    campo_e.default_value = 7.0 * (0.7 + 0.3 * math.sin(2 * PI * 4 * fr) ** 2)
    campo_e.keyframe_insert('default_value', frame=q)
    led_e.default_value = 8.0 if (fr * 4) % 1.0 < 0.6 else 0.6
    led_e.keyframe_insert('default_value', frame=q)
    # fumaça: sai preta da chaminé, fica para trás e sobe diluindo
    for k, o in enumerate(FUMACAS):
        u = (k / len(FUMACAS) + fr * 2) % 1.0
        o.location = SAIDA_ESC + Vector((0.12 * u + 0.03 * math.sin(k * 2.1), -2.6 * u - 0.05, 0.75 * u ** 0.65 + 0.03))
        o.scale = [0.05 + 0.34 * u, 0.06 + 0.42 * u, 0.05 + 0.3 * u]
        o.rotation_euler = (k, u * 2, k * 0.5)
        for c in ('location', 'scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
    # tampas e pistões do vagão de carga (frente e trás defasadas)
    ang = {}
    for (et, s, h) in TAMPAS:
        a = ABRE * abertura(fr + (0.0 if h > 0 else 0.5))
        ang[(s, h)] = a
        et.rotation_euler = (0, s * a, 0)
        et.keyframe_insert('rotation_euler', frame=q)
    for (ec, eh, B_, s, h, L0) in PISTOES:
        H = Vector((s * 0.366, L0.y, 0.822))
        L = H + Matrix.Rotation(s * ang[(s, h)], 3, 'Y') @ (L0 - H)
        d = L - B_
        ec.rotation_mode = 'QUATERNION'
        ec.rotation_quaternion = d.normalized().to_track_quat('Z', 'Y')
        ec.keyframe_insert('rotation_quaternion', frame=q)
        eh.location = Vector((0, 0, d.length - 0.34))
        eh.keyframe_insert('location', frame=q)
    # nível do visor balançando com o trem
    en, _ = tanq.nos['nivel']
    en.scale = (1, 1, 1.0 + 0.06 * math.sin(2 * PI * 2 * fr + 0.4) + 0.025 * math.sin(2 * PI * 7 * fr))
    en.keyframe_insert('scale', frame=q)
    # gotas de seiva: crescem penduradas, soltam e caem até o lastro
    for (o, org, fase) in GOTAS:
        u = (fr * 2 + fase) % 1.0
        if u < 0.6:
            o.location = org + Vector((0, 0, -0.004 * u / 0.6))
            o.scale = [0.4 + 0.6 * u / 0.6] * 2 + [0.4 + 0.9 * u / 0.6]
        else:
            t = (u - 0.6) * 2.0
            dz = 4.9 * t * t
            o.location = org + Vector((0, -DESLOC / 4 * t * 0.0, -0.004 - dz))
            o.scale = [0.9, 0.9, 1.3 + min(2.0, dz * 6)] if org.z - dz > -0.1 else [0.001] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)

# ------------------------------------------------------------------ chão (textura corre com a via), luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (30, 30, 1.0))
chao = base3d.obj('chao', bm, 'chao')
nt = M['chao'].node_tree
coord = next(n for n in nt.nodes if n.type == 'TEX_COORD')
mp = nt.nodes.new('ShaderNodeMapping')
for lk in list(coord.outputs['Object'].links):
    nt.links.new(mp.outputs['Vector'], lk.to_socket)
nt.links.new(coord.outputs['Object'], mp.inputs['Vector'])
for q, dy in ((1, 0.0), (QUADROS + 1, DESLOC)):
    mp.inputs['Location'].default_value = (0, dy, 0)
    mp.inputs['Location'].keyframe_insert('default_value', frame=q)
rustico(M['chao'], poeira=0.3, lama=0.0, riscos=0.0, mossa=1.0, cor_poeira=(0.32, 0.27, 0.2))
random.seed(5)
for k in range(40):                                                                        # pedras soltas fora da via
    bm = bmesh.new()
    pedra(bm, (random.choice((-1, 1)) * random.uniform(0.7, 3.5), random.uniform(-9, 9), 0.01), random.uniform(0.02, 0.08), 0.6)
    base3d.obj('pedra', bm, 'lastro2')

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
    prf = bpy.context.preferences.addons['cycles'].preferences
    prf.compute_device_type = 'OPTIX'
    prf.get_devices()
    for dv in prf.devices:
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


# nome: (posição, alvo, lente, resolução, quadro, giro do sol em z)
FOTOS = {
    'trem_composicao': ((-5.4, 7.4, 2.0), (0.3, 0.2, 0.45), 29, (1700, 950), 31, -35),
    'locomotiva_perto': ((-0.95, 6.05, 0.95), (0.0, 4.2, 0.58), 30, (1300, 1000), 31, -150),
    'truque_perto': ((-1.0, 4.45, 0.55), (-0.25, 3.86, 0.13), 32, (1300, 1000), 31, -35),
    'vagao_carga_perto': ((-1.25, 1.9, 2.45), (0.0, 0.2, 0.6), 30, (1300, 1000), 61, -35),
    'vagao_tanque_perto': ((1.75, -1.25, 1.4), (0.15, -2.75, 0.78), 30, (1300, 1000), 31, 40),
}
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
args = sys.argv[sys.argv.index('--') + 2:] if '--' in sys.argv else []
if modo == 'foto':
    sc.cycles.samples = 128
    for nome in (args or list(FOTOS)):
        pos, alvo, lente, res, qd, solz = FOTOS[nome]
        so.rotation_euler = (math.radians(50), 0, math.radians(solz))
        sc.frame_set(qd)
        sc.render.resolution_x, sc.render.resolution_y = res
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(a) for a in args[:8]]
    so.rotation_euler = (math.radians(50), 0, math.radians(float(args[8]) if len(args) > 8 else -35))
    sc.cycles.samples = 24
    sc.frame_set(int(v[7]))
    sc.render.resolution_x, sc.render.resolution_y = 1000, 700
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'trem_teste.png')
    bpy.ops.render.render(write_still=True)
print('TREM ok')
