"""Estudo isolado (fora do jogo): LARVA ÁCIDA e a CRATERA (casa delas). Novo inimigo (pedido de Sapyst).
LARVA (~1,5 m de comprimento, bem menor que a aranha):
- 9 anéis de carne clara e úmida, mais grossa no meio, com placa de quitina escura nas costas de cada anel;
- glândulas de ácido verde-amarelo brilhando nos flancos, pezinhos curtos (falsas pernas) embaixo;
- cabeça dura e escura, olhinhos pretos, mandíbulas curvas e a boca brilhando de ácido;
- RASTEJAR (laço de 96 quadros = 4 s, 2 ondas): onda de contração da cauda para a cabeça — os anéis se juntam e se
  esticam, o anel contraído sobe um pouco (o corpo anda por ondas, sem pernas de verdade);
- CUSPE (pose): levanta a frente, recua a cabeça, a garganta acende e a gosma sai.
CRATERA (3×3 tiles, ±1,44 m): borda de terra levantada (o jogo não cava o terreno: o fundo fica no nível do chão e a
borda alta faz o buraco), chão de dentro manchado e corroído, poça de gosma ácida brilhando, cachos de ovos.

Uso: blender -b --python estudo_larva.py -- foto
     blender -b --python estudo_larva.py -- nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, bezier, mangueira, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(17)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def luz_mat(nome, cor, forca):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    b.inputs['Roughness'].default_value = 0.25
    return m


def carne_mat(nome, claro, escuro, aspereza=0.32, sss=0.12, escala=14.0):
    """Carne: manchada (ruído entre o claro e o escuro), úmida (pouca aspereza), um pouco translúcida."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = escala; nz.inputs['Detail'].default_value = 8.0
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = escala * 5; nz2.inputs['Detail'].default_value = 4.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MULTIPLY_ADD'
    nt.links.new(nz.outputs['Fac'], mx.inputs[0]); mx.inputs[1].default_value = 0.8
    nt.links.new(nz2.outputs['Fac'], mx.inputs[2])
    rmp = nt.nodes.new('ShaderNodeValToRGB')
    rmp.color_ramp.elements[0].position = 0.45; rmp.color_ramp.elements[0].color = (*escuro, 1)
    rmp.color_ramp.elements[1].position = 0.85; rmp.color_ramp.elements[1].color = (*claro, 1)
    nt.links.new(mx.outputs[0], rmp.inputs['Fac'])
    nt.links.new(rmp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = aspereza
    w = b.inputs.get('Subsurface Weight')
    if w is not None:
        w.default_value = sss
        b.inputs['Subsurface Radius'].default_value = (0.05, 0.03, 0.02)
    return m


def quitina_mat(nome, claro, escuro):
    """Quitina: manchada, com rachaduras (bordas de Voronoi escuras) e relevo de bossas; brilho de casca seca."""
    m = carne_mat(nome, claro, escuro, 0.5, 0.0, 9.0)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    cor = b.inputs['Base Color'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 22.0
    nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    rach = nt.nodes.new('ShaderNodeMapRange'); rach.inputs['From Min'].default_value = 0.0; rach.inputs['From Max'].default_value = 0.035
    nt.links.new(vor.outputs['Distance'], rach.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    nt.links.new(rach.outputs['Result'], mx.inputs['Factor'])
    nt.links.new(cor, mx.inputs['A']); mx.inputs['B'].default_value = (0.25, 0.22, 0.2, 1)
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(rach.outputs['Result'], inv.inputs[1])
    mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'
    nt.links.new(inv.outputs[0], mx2.inputs['Factor'])
    nt.links.new(cor, mx2.inputs['A']); nt.links.new(mx.outputs['Result'], mx2.inputs['B'])
    nt.links.new(mx2.outputs['Result'], b.inputs['Base Color'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 40.0; nz.inputs['Detail'].default_value = 10.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    soma = nt.nodes.new('ShaderNodeMath'); soma.operation = 'ADD'
    nt.links.new(nz.outputs['Fac'], soma.inputs[0]); nt.links.new(rach.outputs['Result'], soma.inputs[1])
    nt.links.new(soma.outputs[0], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def gosma_mat(nome, cor, brilho=0.6, transl=0.55):
    """Baba/gosma: molhada (lisa), meio translúcida, um brilho fraco próprio."""
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = 0.05
    t = b.inputs.get('Transmission Weight') or b.inputs.get('Transmission')
    if t is not None:
        t.default_value = transl
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = brilho
    return m


def poca_mat(nome):
    """Poça de ácido: o centro aceso (amarelo-esverdeado), a borda escura e oleosa, nata de espuma em manchas."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    dist = nt.nodes.new('ShaderNodeVectorMath'); dist.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], dist.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 7.0; nz.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY_ADD'
    nt.links.new(nz.outputs['Fac'], k.inputs[0]); k.inputs[1].default_value = 0.25; nt.links.new(dist.outputs['Value'], k.inputs[2])
    rmp = nt.nodes.new('ShaderNodeValToRGB')
    els = rmp.color_ramp.elements
    els[0].position = 0.1; els[0].color = (0.75, 0.95, 0.2, 1)
    els[1].position = 0.55; els[1].color = (0.06, 0.09, 0.02, 1)
    e = els.new(0.3); e.color = (0.30, 0.55, 0.06, 1)
    nt.links.new(k.outputs[0], rmp.inputs['Fac'])
    nt.links.new(rmp.outputs['Color'], b.inputs['Base Color'])
    em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'
    inv = nt.nodes.new('ShaderNodeMapRange'); inv.inputs['From Min'].default_value = 0.45; inv.inputs['From Max'].default_value = 0.05
    nt.links.new(k.outputs[0], inv.inputs['Value'])
    nt.links.new(rmp.outputs['Color'], b.inputs['Emission Color'])
    nt.links.new(inv.outputs['Result'], b.inputs['Emission Strength'])
    b.inputs['Roughness'].default_value = 0.08
    return m


base3d.M.update({
    'carne_larva': carne_mat('CarneLarva', (0.30, 0.17, 0.12), (0.10, 0.06, 0.045), 0.32, 0.15),
    'quitina_larva': quitina_mat('QuitinaLarva', (0.085, 0.062, 0.046), (0.02, 0.016, 0.013)),
    'baba': gosma_mat('BabaLarva', (0.42, 0.50, 0.12), 0.12, 0.7),
    'gosma_parede': gosma_mat('GosmaParede', (0.16, 0.22, 0.04), 0.08, 0.4),
    'crosta': carne_mat('CrostaAcida', (0.62, 0.58, 0.22), (0.25, 0.22, 0.08), 0.6, 0.0, 30.0),
    'ovo_melado': gosma_mat('OvoMelado', (0.70, 0.66, 0.45), 0.08, 0.35),
    'poca_det': poca_mat('PocaAcida'),
    'terra_cratera_mista': None,
    'mancha_chao': carne_mat('ManchaChao', (0.13, 0.15, 0.05), (0.04, 0.035, 0.02), 0.7, 0.0, 5.0),
    'acido_fundo': luz_mat('AcidoFundo', (0.35, 0.65, 0.06), 0.7),
    'garganta': carne_mat('GargantaLarva', (0.22, 0.06, 0.04), (0.06, 0.015, 0.012), 0.25, 0.1, 12.0),
    'dente': carne_mat('DenteLarva', (0.72, 0.66, 0.50), (0.38, 0.30, 0.14), 0.25, 0.05, 25.0),
    'pe_larva': mats.material('PeLarva', (0.25, 0.21, 0.15), 0.0, 0.5, pintura=False, sujeira=0.7),
    'olho_larva': mats.material('OlhoLarva', (0.01, 0.01, 0.012), 0.0, 0.08, pintura=False, sujeira=0.0, desgaste=0.0),
    'acido': luz_mat('AcidoLarva', (0.55, 0.95, 0.10), 3.5),
    'acido_poca': luz_mat('AcidoPoca', (0.16, 0.34, 0.03), 1.2),
    'terra_cratera': carne_mat('TerraCratera', (0.17, 0.14, 0.11), (0.06, 0.05, 0.04), 0.95, 0.0, 6.0),
    'terra_corroida': carne_mat('TerraCorroida', (0.16, 0.20, 0.06), (0.03, 0.035, 0.02), 0.6, 0.0, 9.0),
    'ovo': mats.material('OvoLarva', (0.62, 0.60, 0.42), 0.0, 0.2, pintura=False, sujeira=0.3, desgaste=0.0),
    'pedra': mats.material('PedraCratera', (0.18, 0.17, 0.16), 0.0, 0.9, pintura=False, sujeira=0.7),
    'chao': mats.material('ChaoEstudo', (0.20, 0.19, 0.18), 0.0, 0.92, sujeira=0.6),
})


def elipsoide(nome, mat, r, seg=(16, 10), achata=None, pai=None, ruido=0.0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg[0], v_segments=seg[1], radius=1.0)
    for v in bm.verts:
        k = 1.0 + ruido * noise.noise(v.co * 3.0 + Vector((r[0] * 7, 0, 0)))
        v.co = Vector((v.co.x * r[0], v.co.y * r[1], v.co.z * r[2])) * k
        if achata is not None and v.co.z < -achata:
            v.co.z = -achata
    o = obj(nome, bm, mat, pai)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# ================================================================== LARVA
# corpo gordo e baixo (lesma/tatuzinho), de massa única: placas de quitina sobrepostas no dorso, boca dentada na frente
COMP = 1.45
X0, X1 = -COMP * 0.55, COMP * 0.45            # cauda (−x) .. frente (+x, a boca)
NP = 5                                         # placas da carapaça (= ossos)
L_PLACA = (X1 - X0) * 0.95 / NP


def perfil(x):
    """(meia largura, meia altura) do corpo em x: grosso na frente e no meio, afinando até a cauda."""
    u = min(1.0, max(0.0, (x - X0) / (X1 - X0)))
    w = 0.42 * (0.16 + 0.84 * math.sin(PI * 0.5 * min(1.0, u / 0.72)) ** 0.75)    # cresce da cauda até a frente
    if u > 0.72:
        w *= 1 - 0.12 * ((u - 0.72) / 0.28) ** 2                                   # frente rombuda (a boca)
    return w, w * 0.78


def ponto(x, a, extra=0.0):
    """Ponto da pele (a = ângulo da seção: 0 lado direito, π/2 topo, π lado esquerdo; embaixo achata no chão)."""
    w, h = perfil(x)
    zc = h * 0.62
    y = math.cos(a) * (w + extra)
    z = zc + math.sin(a) * (h + extra)
    if math.sin(a) < 0:
        z = max(z, 0.02 + extra * 0.3)
        y *= 1.06                                  # a saia (sola) um pouco mais larga, como lesma
    return Vector((x, y, z))


def centro_placa(k):
    """x do centro da placa k (0 = cauda, NP-1 = a da frente)."""
    return X0 + (X1 - X0) * 0.04 + L_PLACA * (k + 0.5)


def montar_larva(nome, origem=Vector((0, 0, 0)), giro=0.0):
    arm_d = bpy.data.armatures.new(nome + '_esqueleto')
    arm = bpy.data.objects.new(nome, arm_d)
    sc.collection.objects.link(arm)
    arm.location = origem
    arm.rotation_euler = (0, 0, giro)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for k in range(NP):
        x0 = centro_placa(k)
        b = arm_d.edit_bones.new('seg%d' % k)
        b.head, b.tail, b.roll = (x0 - 0.06, 0, 0.2), (x0 + 0.06, 0, 0.2), 0.0
    b = arm_d.edit_bones.new('boca')
    b.head, b.tail, b.roll = (X1 - 0.08, 0, 0.18), (X1 + 0.04, 0, 0.18), 0.0
    bpy.ops.object.mode_set(mode='OBJECT')

    # ---- pele (corpo): seções ao longo de x; a frente entra pela boca até a garganta
    bm = bmesh.new()
    LADOS, SEC = 24, 40
    secoes = []
    for i in range(SEC + 1):
        x = X0 + (X1 - X0) * i / SEC
        anel = []
        for j in range(LADOS):
            a = 2 * PI * j / LADOS
            p = ponto(x, a)
            p += Vector((0, 0, 0)) + p * 0.025 * noise.noise(p * 7.0)
            anel.append(bm.verts.new(p))
        secoes.append(anel)
    w1, h1 = perfil(X1)
    boca_c = Vector((X1, 0, h1 * 0.62 * 0.92))
    for (dx, k_r) in ((0.03, 0.8), (-0.03, 0.68), (-0.16, 0.56), (-0.3, 0.46), (-0.42, 0.32)):   # lábio e garganta funda (com dobras)
        anel = []
        for j in range(LADOS):
            a = 2 * PI * j / LADOS
            anel.append(bm.verts.new(boca_c + Vector((dx, math.cos(a) * w1 * k_r, math.sin(a) * h1 * k_r * 0.8))))
        secoes.append(anel)
    fundo = bm.verts.new(boca_c + Vector((-0.47, 0, 0)))
    ponta = bm.verts.new(ponto(X0 - 0.04, PI / 2) * Vector((1, 0, 0.35)) + Vector((0, 0, 0.06)))
    for j in range(LADOS):
        k = (j + 1) % LADOS
        bm.faces.new((ponta, secoes[0][k], secoes[0][j]))
        for i in range(len(secoes) - 1):
            f = bm.faces.new((secoes[i][j], secoes[i][k], secoes[i + 1][k], secoes[i + 1][j]))
            if i >= SEC:
                f.material_index = 2                   # garganta: carne escura
        f = bm.faces.new((fundo, secoes[-1][j], secoes[-1][k]))
        f.material_index = 2                           # fundo da garganta: escuro (o ácido é a bola acesa lá dentro)
    corpo = obj(nome + '_corpo', bm, 'carne_larva')
    for m in ('quitina_larva', 'garganta', 'acido_fundo'):
        corpo.data.materials.append(base3d.M[m])
    for p_ in corpo.data.polygons:
        p_.use_smooth = True

    # ---- carapaça: placas sobrepostas (telha: a da frente cobre a borda da de trás), com verrugas
    bm = bmesh.new()
    placa_de = []                                       # vértice → placa
    for k in range(NP):
        xa, xb = centro_placa(k) - L_PLACA * 0.62, centro_placa(k) + L_PLACA * 0.5
        extra = 0.018 + 0.014 * k                      # cada placa por cima da de trás
        linhas, cols = 6, 22
        g_ext, g_int = [], []
        for i in range(linhas + 1):
            t = i / linhas
            x = xa + (xb - xa) * t
            lev = 0.022 * (1 - t) ** 2                 # a borda de trás levanta (lábio da telha)
            if i == 0:
                x = xa - 0.012 * (1 + noise.noise(Vector((k * 3.1, 0.5, 0.2))))   # (a lasca da borda vem por coluna, abaixo)
            re, ri = [], []
            for j in range(cols + 1):
                a = -0.28 + (PI + 0.56) * j / cols
                crista = 0.03 * math.exp(-((a - PI / 2) / 0.22) ** 2) * math.sin(PI * t)    # crista no dorso
                bossa = 0.02 * noise.noise(Vector((x * 9, a * 3, k * 1.7))) + 0.006 * noise.noise(Vector((x * 40, a * 12, k)))
                xx = x
                if i == 0:                                      # borda de trás lascada (dente de serra irregular)
                    xx = x + 0.03 * max(0.0, noise.noise(Vector((a * 5.0, k * 2.3, 0.7))) + 0.15 * math.sin(j * 2.7))
                re.append(bm.verts.new(ponto(xx, a, extra + lev + crista + bossa)))
                ri.append(bm.verts.new(ponto(xx, a, extra + lev + crista + bossa - 0.022)))
                placa_de += [k, k]
            g_ext.append(re)
            g_int.append(ri)
        for i in range(linhas):
            for j in range(cols):
                bm.faces.new((g_ext[i][j], g_ext[i][j + 1], g_ext[i + 1][j + 1], g_ext[i + 1][j]))
                bm.faces.new((g_int[i][j], g_int[i + 1][j], g_int[i + 1][j + 1], g_int[i][j + 1]))
        for i in range(linhas):                         # bordas grossas (laterais)
            for j in (0, cols):
                bm.faces.new((g_ext[i][j], g_ext[i + 1][j], g_int[i + 1][j], g_int[i][j]))
        for i in (0, linhas):                           # bordas grossas (frente e trás)
            for j in range(cols):
                bm.faces.new((g_ext[i][j], g_int[i][j], g_int[i][j + 1], g_ext[i][j + 1]))
        for v_i in range(16):                           # verrugas (bolhas de quitina) na placa, de vários tamanhos
            x = random.uniform(xa + 0.03, xb - 0.03)
            a = random.uniform(0.1, PI - 0.1)
            c = ponto(x, a, extra + 0.01)
            r_ = random.uniform(0.007, 0.03) if v_i % 3 else random.uniform(0.004, 0.009)
            ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r_)
            for v in ret['verts']:
                v.co = v.co * Vector((1, 1, 0.6)) + c
            placa_de += [k] * len(ret['verts'])
    carap = obj(nome + '_carapaca', bm, 'quitina_larva')
    for p_ in carap.data.polygons:
        p_.use_smooth = True

    # ---- dentes: fileira de fora (curvos, irregulares), fileira de dentro (miúdos, na garganta) e duas presas em gancho
    def dente(bm, base_, ponta_, r0, curva):
        """Dente curvo de uma malha só: anéis ao longo da curva, afinando até a ponta (sem degrau)."""
        meio_ = (base_ + ponta_) / 2 + curva
        pts = [Vector(p_) for p_ in bezier(base_, base_.lerp(meio_, 0.6), meio_.lerp(ponta_, 0.4), ponta_, 6)]
        aneis_ = []
        for q, c_ in enumerate(pts[:-1]):
            t_ = (pts[q + 1] - c_).normalized()
            u_ = t_.cross(Vector((0, 0, 1)) if abs(t_.z) < 0.9 else Vector((1, 0, 0))).normalized()
            v_ = t_.cross(u_)
            r_ = r0 * (1 - q / 6) ** 0.8
            aneis_.append([bm.verts.new(c_ + (u_ * math.cos(2 * PI * m_ / 7) + v_ * math.sin(2 * PI * m_ / 7)) * r_) for m_ in range(7)])
        topo_ = bm.verts.new(pts[-1])
        for q in range(len(aneis_) - 1):
            for m_ in range(7):
                n_ = (m_ + 1) % 7
                bm.faces.new((aneis_[q][m_], aneis_[q][n_], aneis_[q + 1][n_], aneis_[q + 1][m_]))
        for m_ in range(7):
            bm.faces.new((aneis_[-1][m_], aneis_[-1][(m_ + 1) % 7], topo_))

    bm = bmesh.new()
    rng = random.Random(len(nome))
    for j in range(20):
        a = 2 * PI * j / 20 + rng.uniform(-0.08, 0.08)
        base_ = boca_c + Vector((0.025, math.cos(a) * w1 * 0.77, math.sin(a) * h1 * 0.77 * 0.8))
        dentro = (boca_c - base_).normalized()
        comp = (0.04 + 0.08 * max(0.0, -math.sin(a)) ** 2) * rng.uniform(0.7, 1.3)
        ponta_ = base_ + (dentro * 0.75 + Vector((0.45, 0, 0))).normalized() * comp
        dente(bm, base_, ponta_, 0.011 + 0.006 * max(0.0, -math.sin(a)), Vector((0.012, 0, 0)) - dentro * 0.008)
    for j in range(13):
        a = 2 * PI * j / 13 + 0.2
        base_ = boca_c + Vector((-0.06, math.cos(a) * w1 * 0.66, math.sin(a) * h1 * 0.66 * 0.8))
        dentro = (boca_c + Vector((-0.06, 0, 0)) - base_).normalized()
        dente(bm, base_, base_ + (dentro * 0.9 + Vector((-0.3, 0, 0))).normalized() * rng.uniform(0.025, 0.045), 0.007, Vector((0, 0, 0)))
    for lado in (-1, 1):                                # presas: saem do canto de baixo e sobem em gancho para a frente
        base_ = boca_c + Vector((0.01, lado * w1 * 0.62, -h1 * 0.5))
        ponta_ = base_ + Vector((0.13, -lado * 0.05, 0.1))
        dente(bm, base_, ponta_, 0.022, Vector((0.05, lado * 0.02, -0.03)))
    dentes = obj(nome + '_dentes', bm, 'dente')

    # ---- pesos: pele suave entre os ossos; placas rígidas na própria placa; boca e dentes no osso da boca
    def pesar(o, por_vertice=None):
        gs = {('seg%d' % k): o.vertex_groups.new(name='seg%d' % k) for k in range(NP)}
        gs['boca'] = o.vertex_groups.new(name='boca')
        for v in o.data.vertices:
            if por_vertice is not None:
                gs['seg%d' % por_vertice[v.index]].add([v.index], 1.0, 'REPLACE')
                continue
            if v.co.x > X1 - 0.06:
                gs['boca'].add([v.index], 1.0, 'REPLACE')
                continue
            ws = [math.exp(-((v.co.x - centro_placa(k)) / (L_PLACA * 0.7)) ** 2) for k in range(NP)]
            tot = sum(ws) or 1.0
            for k, w_ in enumerate(ws):
                if w_ / tot > 0.01:
                    gs['seg%d' % k].add([v.index], w_ / tot, 'REPLACE')
        md = o.modifiers.new('esqueleto', 'ARMATURE')
        md.object = arm
        o.parent = arm

    pesar(corpo)
    pesar(carap, placa_de)
    # ---- baba: fios de gosma de cima a baixo da boca (com contas de gota) e um fio escorrendo até o chão
    bm = bmesh.new()
    for f_i in range(4):
        a_cima = rng.uniform(0.6, PI - 0.6)
        A = boca_c + Vector((0.035, math.cos(a_cima) * w1 * 0.7, math.sin(a_cima) * h1 * 0.7 * 0.8))
        B = boca_c + Vector((0.035, A.y + rng.uniform(-0.06, 0.06), -h1 * 0.5))
        cai = rng.uniform(0.06, 0.14)                   # o fio pende abaixo da linha (peso da gosma)
        pts = [Vector(p_) for p_ in bezier(A, A + Vector((0.025, 0, -cai)), B + Vector((0.03, 0, -cai)), B, 12)]
        for q, (a_, b_) in enumerate(zip(pts, pts[1:])):
            r_ = 0.0018 + 0.0022 * abs(math.cos(PI * q / 12))
            base3d.tubo(bm, a_, b_, r_, 5)
            if q in (5, 6, 7) and rng.random() < 0.5:   # gota juntando na barriga do fio
                ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r_ * 2.6)
                for v in ret['verts']:
                    v.co = v.co * Vector((1, 1, 1.4)) + a_
    for lado in (-0.4, 0.5):                            # fios pendurados do lábio de baixo até perto do chão
        A = boca_c + Vector((0.05, lado * w1 * 0.5, -h1 * 0.55))
        B = Vector((A.x + 0.06, A.y, 0.035))
        pts = [Vector(p_) for p_ in bezier(A, A + Vector((0.03, 0, -0.02)), B + Vector((0, 0, 0.05)), B, 8)]
        for q, (a_, b_) in enumerate(zip(pts, pts[1:])):
            base3d.tubo(bm, a_, b_, 0.006 * (1 - q / 10) + 0.002, 5)
        ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.011)    # a gota na ponta
        for v in ret['verts']:
            v.co = v.co * Vector((1, 1, 1.5)) + B
    baba = obj(nome + '_baba', bm, 'baba')
    for o_ in (dentes, baba):
        gd = o_.vertex_groups.new(name='boca')
        gd.add([v.index for v in o_.data.vertices], 1.0, 'REPLACE')
        o_.modifiers.new('esqueleto', 'ARMATURE').object = arm
        o_.parent = arm
        for p_ in o_.data.polygons:
            p_.use_smooth = True
    # glândulas de ácido na saia, dos dois lados
    bm = bmesh.new()
    gl_de = []
    ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.07)       # ácido juntando no fundo da garganta
    for v in ret['verts']:
        v.co = v.co * Vector((0.6, 1.0, 0.8)) + boca_c + Vector((-0.36, 0, -0.03))
    gl_de += [NP - 1] * len(ret['verts'])
    for k in range(NP):
        for lado in (-1, 1):
            for t in (0.3, 0.75):
                x = centro_placa(k) + (t - 0.5) * L_PLACA
                c = ponto(x, PI / 2 + lado * (PI / 2 + 0.22), 0.004)
                ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.018)
                for v in ret['verts']:
                    v.co = v.co * Vector((1.3, 0.8, 0.8)) + c
                gl_de += [k] * len(ret['verts'])
    for k in range(NP):                                 # poros acesos em algumas verrugas
        for v_i in range(3):
            x = centro_placa(k) + random.uniform(-0.4, 0.4) * L_PLACA
            a = random.uniform(0.4, PI - 0.4)
            c = ponto(x, a, 0.018 + 0.014 * k + 0.022)
            ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.008)
            for v in ret['verts']:
                v.co = v.co * Vector((1, 1, 0.5)) + c
            gl_de += [k] * len(ret['verts'])
    gland = obj(nome + '_glandulas', bm, 'acido')
    pesar(gland, gl_de)
    bpy.context.view_layer.update()
    return arm, dentes, None


def _osso(arm, nome):
    pb = arm.pose.bones[nome]
    pb.rotation_mode = 'XYZ'
    return pb


def pose_rastejar(arm, u, ondas=1):
    """Rastejo peristáltico: uma onda de contração corre da cauda para a cabeça. O trecho contraído encurta (até
    metade), engorda e sobe numa corcova (as placas se encavalam); o resto do corpo fica esticado e rente ao chão.
    A cabeça estica para a frente quando a onda chega nela (a boca mastiga um pouco) e o corpo serpenteia de leve.
    Osso ao longo de +X: no espaço dele, y = comprimento do corpo, z = para cima, x = para o lado."""
    def onda(k, uu):
        f = (ondas * uu - k / (NP - 1) * 0.85) % 1.0
        return math.sin(PI * min(1.0, f / 0.55)) ** 2 if f < 0.55 else 0.0     # pulso de 55% do ciclo
    cs = [onda(k, u) for k in range(NP)]
    x = 0.0
    xs, zs = [], []
    for k in range(NP):
        x += L_PLACA * (1.0 - 0.36 * cs[k])                                # contraído encurta (as placas se encavalam)
        xs.append(x)
        zs.append(0.07 * cs[k])
    meio = (xs[0] + xs[-1]) / 2
    for k in range(NP):
        pb = _osso(arm, 'seg%d' % k)
        pb.location = (0.025 * math.sin(2 * PI * (u - k / NP)), xs[k] - meio - centro_placa(k)
                       + (centro_placa(0) + centro_placa(NP - 1)) / 2, zs[k])
        g = 1.0 + 0.16 * cs[k]
        pb.scale = (g, 1.0 - 0.22 * cs[k], 1.0 + 0.18 * cs[k])
        pb.rotation_euler = (0, 0, 0.05 * math.sin(2 * PI * (u - k / NP)))
    pb = _osso(arm, 'boca')
    ch = cs[-1]
    pb.location = (0.02 * math.sin(2 * PI * u), _osso(arm, 'seg%d' % (NP - 1)).location[1] + 0.04 * (1.0 - ch),
                   zs[-1] + 0.03 * math.sin(2 * PI * u * 2))
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1.0 + 0.12 * ch, 1.0, 1.0 + 0.12 * ch)


def pose_cuspe(arm, _boca, k):
    """Cuspe: a frente ergue, a boca abre (dentes para fora) e a garganta acende."""
    pose_rastejar(arm, 0.0)
    for i, e in enumerate((0, 0, 0.25, 0.6, 1.0)):
        pb = _osso(arm, 'seg%d' % i)
        pb.location = (pb.location[0], pb.location[1], 0.22 * (e * k) ** 1.5)
        pb.rotation_euler = (0.45 * e * k, 0, 0)
    pb = _osso(arm, 'boca')
    pb.location = (0.0, pb.location[1] + 0.03 * k, 0.3 * k)
    pb.rotation_euler = (0.6 * k, 0, 0)
    pb.scale = (1 + 0.35 * k, 1.0, 1 + 0.35 * k)


larva, _dentes, boca = montar_larva('larva')
for q in range(1, QUADROS + 1):
    pose_rastejar(larva, (q - 1) / QUADROS)
    for pb in larva.pose.bones:
        pb.keyframe_insert('location', frame=q)
        pb.keyframe_insert('scale', frame=q)
        pb.keyframe_insert('rotation_euler', frame=q)

# ================================================================== CRATERA (longe da larva, em x = 8)
CX = 8.0


def terra_cratera_mat():
    """Terra da cratera com a mancha do ácido suave: forte perto da poça, em línguas pela encosta (ruído), sem borda."""
    m = carne_mat('TerraCrateraMista', (0.17, 0.14, 0.11), (0.06, 0.05, 0.04), 0.95, 0.0, 6.0)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    terra = b.inputs['Base Color'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sub = nt.nodes.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (CX, 0, 0)
    nt.links.new(tc.outputs['Object'], sub.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(sub.outputs['Vector'], sep.inputs[0])
    xy = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sep.outputs['X'], xy.inputs['X']); nt.links.new(sep.outputs['Y'], xy.inputs['Y'])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(xy.outputs['Vector'], ln.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY_ADD'
    nt.links.new(nz.outputs['Fac'], k.inputs[0]); k.inputs[1].default_value = -0.6; nt.links.new(ln.outputs['Value'], k.inputs[2])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.55; mr.inputs['From Max'].default_value = 0.2
    nt.links.new(k.outputs[0], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(mr.outputs['Result'], mx.inputs['Factor'])
    nt.links.new(terra, mx.inputs['A']); mx.inputs['B'].default_value = (0.09, 0.12, 0.03, 1)
    nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    return m


base3d.M['terra_cratera_mista'] = terra_cratera_mat()
bm = bmesh.new()
AN, LADOS = 9, 48
aneis_c = []
for j in range(AN):
    u = j / (AN - 1)
    r = 0.25 + 1.17 * u                             # 0,25 m (fundo) .. 1,42 m (pé de fora da borda)
    alto = math.sin(PI * min(1.0, max(0.0, (u - 0.35) / 0.65))) ** 0.8   # borda alta entre o fundo e o pé
    anel = []
    for i in range(LADOS):
        a = 2 * PI * i / LADOS
        k = 1 + 0.12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 0.3)))
        p3 = Vector((math.cos(a) * r, math.sin(a) * r, 0.0))
        z = 0.02 + 0.5 * alto * k * (1 - 0.3 * noise.noise(Vector((math.cos(a) * 4, math.sin(a) * 4, 1.1))))
        z += alto * (0.06 * noise.noise(p3 * 6.0 + Vector((0, 0, 3.3))) + 0.025 * noise.noise(p3 * 17.0))
        if j == AN - 1:
            z = 0.0
        anel.append(bm.verts.new(Vector((CX + math.cos(a) * r * k, math.sin(a) * r * k, z))))
    aneis_c.append(anel)
centro_v = bm.verts.new(Vector((CX, 0, 0.02)))
for i in range(LADOS):
    bm.faces.new((centro_v, aneis_c[0][i], aneis_c[0][(i + 1) % LADOS]))
for j in range(AN - 1):
    for i in range(LADOS):
        k = (i + 1) % LADOS
        bm.faces.new((aneis_c[j][i], aneis_c[j + 1][i], aneis_c[j + 1][k], aneis_c[j][k]))
o_cr = obj('cratera_terra', bm, 'terra_cratera')
for p in o_cr.data.polygons:
    p.use_smooth = True
o_cr.data.materials.clear()
o_cr.data.materials.append(base3d.M['terra_cratera_mista'])
# poça de ácido no fundo: superfície com ondulação, centro aceso, borda escura
from mathutils.bvhtree import BVHTree
bvh_cr = BVHTree.FromObject(o_cr, bpy.context.evaluated_depsgraph_get())
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=28, y_segments=28, size=0.5)
for v in list(bm.verts):
    a = math.atan2(v.co.y, v.co.x)
    lim = 0.44 * (1 + 0.16 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 5))))
    if v.co.length > lim:
        v.co *= lim / v.co.length
    v.co.z = 0.004 * noise.noise(v.co * 18)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
for v in bm.verts:
    v.co += Vector((CX + 0.08, -0.05, 0.034))
o_p = obj('cratera_poca', bm, 'poca_det')
o_p.data.transform(Matrix.Translation((-(CX + 0.08), 0.05, 0)))
o_p.location = (CX + 0.08, -0.05, 0)
for p_ in o_p.data.polygons:
    p_.use_smooth = True
# bolhas: inteiras (meia esfera) e estouradas (anel), de vários tamanhos
bm = bmesh.new()
for k in range(30):
    a = random.uniform(0, 2 * PI); rr = math.sqrt(random.random()) * 0.36
    c = Vector((CX + 0.08 + math.cos(a) * rr, -0.05 + math.sin(a) * rr, 0.036))
    r_ = random.uniform(0.008, 0.035)
    if k % 4:
        ret = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r_)
        for v in ret['verts']:
            v.co.z = max(v.co.z, 0.0) * 0.8
            v.co += c
    else:
        ret = bmesh.ops.create_circle(bm, cap_ends=False, segments=12, radius=r_)
        anel_ = ret['verts']
        ret2 = bmesh.ops.extrude_edge_only(bm, edges=[e for e in bm.edges if e.verts[0] in anel_ and e.verts[1] in anel_])
        for v in [e for e in ret2['geom'] if isinstance(e, bmesh.types.BMVert)]:
            v.co = v.co * 1.35 + Vector((0, 0, 0.004))
        for v in anel_:
            v.co += Vector((0, 0, 0.006))
        for v in set(anel_) | {e for e in ret2['geom'] if isinstance(e, bmesh.types.BMVert)}:
            v.co += c
obj('cratera_bolhas', bm, 'baba')
# espuma e nata amarelada na beira da poça, crosta de cristais na margem
bm = bmesh.new()
for k in range(40):
    a = random.uniform(0, 2 * PI); rr = random.uniform(0.33, 0.48)
    c = Vector((CX + 0.08 + math.cos(a) * rr, -0.05 + math.sin(a) * rr, 0.036))
    ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.008, 0.02))
    for v in ret['verts']:
        v.co = v.co * Vector((1, 1, 0.45)) + c
obj('cratera_espuma', bm, 'crosta')
bm = bmesh.new()
for k in range(26):
    a = random.uniform(0, 2 * PI); rr = random.uniform(0.47, 0.62)
    hit = bvh_cr.ray_cast(Vector((CX + math.cos(a) * rr, math.sin(a) * rr, 2.0)), Vector((0, 0, -1)))
    if hit[0] is None:
        continue
    for q in range(3):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=random.uniform(0.008, 0.016), radius2=0.0,
                              depth=random.uniform(0.02, 0.05),
                              matrix=Matrix.Translation(hit[0] + Vector((random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), 0.012)))
                              @ Matrix.Rotation(random.uniform(-0.5, 0.5), 4, 'X') @ Matrix.Rotation(random.uniform(-0.5, 0.5), 4, 'Y'))
obj('cratera_crosta', bm, 'crosta')
# escorridos de gosma pelas paredes de dentro (da borda até a poça), assentados na encosta
bm = bmesh.new()
for k in range(9):
    a0 = 2 * PI * k / 9 + random.uniform(-0.3, 0.3)
    larg = random.uniform(0.5, 1.4)
    pts = []
    for q in range(12):
        rr = random.uniform(0.85, 1.0) - 0.5 * q / 11 if q == 0 else 1.0 - 0.5 * q / 11
        a = a0 + 0.08 * math.sin(q * 1.3 + k)
        hit = bvh_cr.ray_cast(Vector((CX + math.cos(a) * rr, math.sin(a) * rr, 2.0)), Vector((0, 0, -1)))
        if hit[0] is not None:
            pts.append(hit[0] + hit[1] * 0.006)
    for q, (a_, b_) in enumerate(zip(pts, pts[1:])):
        lado = (b_ - a_).cross(Vector((0, 0, 1))).normalized() * (0.006 + 0.02 * q / 11) * larg * (0.7 + 0.6 * abs(noise.noise(Vector((q * 0.7, k, 0.3)))))
        v1, v2, v3, v4 = (bm.verts.new(a_ - lado), bm.verts.new(a_ + lado), bm.verts.new(b_ + lado * 1.1), bm.verts.new(b_ - lado * 1.1))
        bm.faces.new((v1, v4, v3, v2))
obj('cratera_escorridos', bm, 'gosma_parede')
bm = bmesh.new()                                  # torrões de terra jogados na borda
for k in range(26):
    a = random.uniform(0, 2 * PI)
    rr = random.uniform(0.95, 1.35)
    pedra(bm, (CX + math.cos(a) * rr, math.sin(a) * rr, 0.06 + 0.2 * max(0.0, 1.25 - rr)), random.uniform(0.06, 0.13), achatar=0.55)
obj('cratera_torroes', bm, 'terra_cratera')
# ovos em cachos (encostados no chão de dentro e na encosta)
for c_i, (ang, rr) in enumerate(((40, 0.62), (160, 0.55), (265, 0.7), (110, 0.68), (330, 0.6))):
    a = math.radians(ang)
    cx, cy = CX + math.cos(a) * rr, math.sin(a) * rr
    for k in range(6):
        e = elipsoide(f'cratera_ovo{c_i}_{k}', 'ovo_melado' if k % 2 else 'ovo', (0.07, 0.06, 0.08), (10, 8), ruido=0.06)
        e.location = (cx + random.uniform(-0.1, 0.1), cy + random.uniform(-0.1, 0.1), 0.06 + 0.1 * rr * 0.5 + random.uniform(0, 0.04))
        e.rotation_euler = (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, PI))
# pedras e terra jogada para fora
bm = bmesh.new()
for k in range(14):
    a = random.uniform(0, 2 * PI)
    rr = random.uniform(1.15, 1.38)
    pedra(bm, (CX + math.cos(a) * rr, math.sin(a) * rr, 0.04), random.uniform(0.05, 0.11), achatar=0.6)
obj('cratera_pedras', bm, 'pedra')
# o chão de fora tomado (manchas e trilhas de gosma) é a camada do chão do jogo (Infestacao, estilo larva)

# ================================================================== CUSPE (pose para as fotos: outra larva, perto da cratera)
cusp, _d2, boca2 = montar_larva('larva_cuspe', Vector((CX - 2.6, 1.6, 0)), -0.5)
pose_cuspe(cusp, boca2, 1.0)
gota = elipsoide('EFEITO_gosma', 'acido', (0.07, 0.05, 0.05), (10, 8), ruido=0.15)
gota.location = cusp.matrix_world @ Vector((1.35, 0, 0.75))
for k in range(4):
    g = elipsoide(f'EFEITO_gota{k}', 'acido', (0.02, 0.02, 0.02), (6, 5))
    g.location = cusp.matrix_world @ Vector((1.15 - k * 0.12, 0, 0.74 - k * 0.03))
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=0.22)
for v in bm.verts:
    v.co *= 1 + 0.25 * noise.noise(v.co * 6)
    v.co += cusp.matrix_world @ Vector((2.6, 0, 0.012))
obj('EFEITO_poca_cuspe', bm, 'acido_poca')

# ------------------------------------------------------------------ CENA, LUZ E CÂMERAS
bm = bmesh.new()
caixa(bm, (4, 0, -0.05), (30, 20, 0.10))
obj('EFEITO_chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 4.0; sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so); so.rotation_euler = (math.radians(52), 0, math.radians(-38))
sol2 = bpy.data.lights.new('Sol2', 'SUN'); sol2.energy = 1.5
so2 = bpy.data.objects.new('Sol2', sol2); sc.collection.objects.link(so2); so2.rotation_euler = (math.radians(-32), 0, math.radians(140))
mundo = bpy.data.worlds.new('Mundo'); sc.world = mundo
bg = mundo.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.45, 0.48, 0.58, 1); bg.inputs['Strength'].default_value = 0.65
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
sc.view_settings.exposure = -0.3
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and o.name.startswith('larva_') and not o.name.startswith('larva_cuspe'))
cusp.data.pose_position = 'POSE'
print(f'LARVA tris={tris}')
if modo == 'foto':
    sc.cycles.samples = 96
    sc.render.resolution_x, sc.render.resolution_y = 1100, 800
    fotos = [('larva_0', 24, (2.4, -2.0, 1.4), (0.05, 0, 0.22), 42), ('larva_1', 24, (0.0, -3.4, 0.7), (0, 0, 0.25), 42),
             ('larva_perto', 24, (1.75, -0.7, 0.55), (0.55, 0, 0.22), 45),
             ('larva_boca', 24, (1.3, -0.35, 0.32), (0.62, 0, 0.2), 55),
             ('cratera_perto', 1, (CX + 0.9, -1.7, 1.5), (CX + 0.05, -0.05, 0.05), 40),
             ('cratera_0', 1, (CX - 1.5, -3.6, 2.6), (CX, 0, 0.1), 32), ('cratera_cuspe', 1, (CX - 5.0, -2.8, 2.4), (CX - 1.3, 0.9, 0.3), 30)]
    for nome, q, pos, alvo, lente in fotos:
        sc.frame_set(q)
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
    # tira do rastejar: perfil, 6 fases de meia onda
    sc.render.resolution_x, sc.render.resolution_y = 700, 260
    mirar((0.0, -3.6, 0.6), (0, 0, 0.25), 45)
    for k, q in enumerate((1, 5, 9, 13, 17, 21)):
        sc.frame_set(q)
        sc.render.filepath = os.path.join(AQUI, f'larva_rastejar_{k}.png')
        bpy.ops.render.render(write_still=True)
    print('LARVA ok')
