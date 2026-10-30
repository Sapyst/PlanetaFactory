"""Estudo isolado (fora do jogo): cano subterrâneo (cano_subterraneo) — entrada e saída 1×1 que passam a seiva por
baixo da terra por até 9 tiles. 1 tile = 1 m; x leste, y norte; eixo do cano na superfície a 0,34 m (igual aos canos).
- Entrada: FLUIDO_ENT_S0 (flange com a face na borda sul do tile, casa com a do cano vizinho). O cano passa pela
  válvula de bloqueio atuada (sem volante), atravessa a parede da caixa de concreto por um passamuros e, dentro dela,
  mergulha num cotovelo de VIDRO (seiva âmbar descendo, anéis de campo violeta da IA, tirantes) visível pela janela da
  tampa de inspeção para drone (olhal de garra, balizas, marca fiducial, trava atuada). Desce em aço até −0,9 m,
  cotovelo de raio longo sobre pedestal e sai pela parede norte, enterrado. Ventosa sobre o cano e respiro pescoço de
  ganso na laje; bomba de dreno e boia no fundo úmido; caixa de junção, sensor da IA, concreto lascado com vergalhão.
- Saída: a mesma caixa girada 180° (FLUIDO_SAI_N0): a seiva sobe pelo vidro e volta à superfície.
- Trecho enterrado: cano revestido de fita, mantas nas juntas, fio traçador, fita de aviso, berço de areia na vala;
  na superfície, terra revirada sobre a vala, marcos de concreto (seta do fluxo, luz da IA) e placas rasas.
Conjunto: cano reto c/ visor (0,0) → entrada (1,0) → 4 tiles de terra (2..5) → saída (6,0) → reto c/ visor (7,0).
Reaproveita as funções e materiais de estudo_canos.py (executa a parte de definições dele).
Uso: blender -b --python estudo_cano_subterraneo.py -- foto            (conjunto e perto)
     blender -b --python estudo_cano_subterraneo.py -- foto corte      (meia seção do trecho enterrado)"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise as mnoise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODO = ARGS[0] if ARGS else 'foto'
SO_UMA = ARGS[1] if len(ARGS) > 1 else None
CORTE = SO_UMA == 'corte'

# ------------------------------------------------------------------ reaproveita estudo_canos.py (só as definições)
_src = open(os.path.join(AQUI, 'estudo_canos.py'), encoding='utf-8').read()
_fim = _src.index('# ------------------------------------------------------------------ bomba de êmbolo')
exec(compile(_src[:_fim], os.path.join(AQUI, 'estudo_canos.py'), 'exec'), globals())
random.seed(41)

X0C, X1C = -30.0, 30.0       # meia seção: o bloco de terra inteiro perde o lado y < 0 (frente do corte em y = 0)


def no_corte(x, y):
    return CORTE and X0C < x < X1C and y < 0.0


# ------------------------------------------------------------------ materiais novos
def solo_mat():
    """Chão: em cima grama rala e terra; no corte, camadas (terra preta, argila, cascalho) com pedriscos."""
    m = bpy.data.materials.new('Solo')
    nt = m.node_tree
    no = mats.no
    L = nt.links.new
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    L(geo.outputs['Normal'], sn.inputs[0])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    L(geo.outputs['Position'], sp.inputs[0])
    topo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.85})
    L(sn.outputs['Z'], topo.inputs['Value'])
    n1 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.7, 'Detail': 9.0, 'Roughness': 0.65})
    n2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 22.0, 'Detail': 4.0})
    for n in (n1, n2):
        L(geo.outputs['Position'], n.inputs['Vector'])
    mg = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.48, 'From Max': 0.7})
    L(n1.outputs['Fac'], mg.inputs['Value'])
    cg = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cg.inputs[6].default_value = (0.055, 0.095, 0.025, 1)
    cg.inputs[7].default_value = (0.15, 0.11, 0.07, 1)
    L(mg.outputs['Result'], cg.inputs[0])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.45
    L(cg.outputs[2], var.inputs[6])
    L(n2.outputs['Color'], var.inputs[7])
    # camadas
    nz = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.6, 'Detail': 6.0})
    L(geo.outputs['Position'], nz.inputs['Vector'])
    zz = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    zz.inputs[1].default_value = 0.3
    L(nz.outputs['Fac'], zz.inputs[0])
    L(sp.outputs['Z'], zz.inputs[2])
    mz = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.9, 'From Max': 0.2})
    L(zz.outputs['Value'], mz.inputs['Value'])
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    el = rampa.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.1, 0.085, 0.07, 1)
    el[1].position, el[1].color = 0.36, (0.16, 0.12, 0.09, 1)
    for pos, cor in ((0.42, (0.3, 0.155, 0.075, 1)), (0.72, (0.26, 0.14, 0.07, 1)), (0.8, (0.07, 0.048, 0.03, 1)),
                     (1.0, (0.06, 0.04, 0.025, 1))):
        e = el.new(pos)
        e.color = cor
    L(mz.outputs['Result'], rampa.inputs['Fac'])
    vo = no(nt, 'ShaderNodeTexVoronoi', **{'Scale': 20.0})
    L(geo.outputs['Position'], vo.inputs['Vector'])
    pd = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.16, 'From Max': 0.1})
    L(vo.outputs['Distance'], pd.inputs['Value'])
    pdm = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    L(pd.outputs['Result'], pdm.inputs[0])
    pdm.inputs[1].default_value = 0.8
    ped = no(nt, 'ShaderNodeMix', data_type='RGBA')
    ped.inputs[7].default_value = (0.36, 0.33, 0.29, 1)
    L(pdm.outputs['Value'], ped.inputs[0])
    L(rampa.outputs['Color'], ped.inputs[6])
    fim = no(nt, 'ShaderNodeMix', data_type='RGBA')
    L(topo.outputs['Result'], fim.inputs[0])
    L(ped.outputs[2], fim.inputs[6])
    L(var.outputs[2], fim.inputs[7])
    L(fim.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.93
    nb = no(nt, 'ShaderNodeTexNoise', **{'Scale': 16.0, 'Detail': 8.0})
    L(geo.outputs['Position'], nb.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.45})
    L(nb.outputs['Fac'], bump.inputs['Height'])
    vb = no(nt, 'ShaderNodeBump', **{'Strength': 0.5})
    L(pd.outputs['Result'], vb.inputs['Height'])
    L(bump.outputs['Normal'], vb.inputs['Normal'])
    L(vb.outputs['Normal'], b.inputs['Normal'])
    return m


def grama_mat():
    """Folhas: cada folha (ilha) sorteia entre verde e palha; base escura."""
    m = bpy.data.materials.new('Grama')
    nt = m.node_tree
    no = mats.no
    L = nt.links.new
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    rr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.25, 'From Max': 0.95})
    L(geo.outputs['Random Per Island'], rr.inputs['Value'])
    c = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c.inputs[6].default_value = (0.045, 0.1, 0.02, 1)
    c.inputs[7].default_value = (0.24, 0.2, 0.07, 1)
    L(rr.outputs['Result'], c.inputs[0])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    L(geo.outputs['Position'], sp.inputs[0])
    z = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.09, 'To Min': 0.3, 'To Max': 1.0})
    L(sp.outputs['Z'], z.inputs['Value'])
    mul = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    mul.inputs[0].default_value = 1.0
    L(c.outputs[2], mul.inputs[6])
    L(z.outputs['Result'], mul.inputs[7])
    L(mul.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Subsurface Weight'].default_value = 0.0
    return m


def fluxo_caminho_mat(nome, forca):
    """Igual a fluxo_mat de estudo_canos, mas a coordenada do fluxo é o comprimento ao longo do caminho (UV.x):
    a seiva faz a curva do cotovelo e desce. Fase em FASES (a mesma animação dos visores)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    L = nt.links.new
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.08
    uvn = no(nt, 'ShaderNodeUVMap')
    suv = no(nt, 'ShaderNodeSeparateXYZ')
    L(uvn.outputs['UV'], suv.inputs[0])
    ang = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    ang.inputs[1].default_value = 0.53
    L(suv.outputs['Y'], ang.inputs[0])
    vc = no(nt, 'ShaderNodeCombineXYZ')
    L(ang.outputs['Value'], vc.inputs['X'])
    L(suv.outputs['X'], vc.inputs['Z'])
    vet = vc.outputs[0]
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    L(vet, sep.inputs[0])
    val = no(nt, 'ShaderNodeValue')
    val.name = 'fase'
    FASES.append(val)
    mz = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    mz.inputs[1].default_value = FLUXO_F
    L(sep.outputs['Z'], mz.inputs[0])
    sub = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    L(mz.outputs['Value'], sub.inputs[0])
    L(val.outputs[0], sub.inputs[1])
    pi2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    pi2.inputs[1].default_value = 2 * PI
    L(sub.outputs['Value'], pi2.inputs[0])
    sen = no(nt, 'ShaderNodeMath', operation='SINE')
    L(pi2.outputs['Value'], sen.inputs[0])
    faixa = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0})
    L(sen.outputs['Value'], faixa.inputs['Value'])
    off = no(nt, 'ShaderNodeMath', operation='DIVIDE')
    off.inputs[1].default_value = FLUXO_F
    L(val.outputs[0], off.inputs[0])
    comb = no(nt, 'ShaderNodeCombineXYZ')
    L(off.outputs['Value'], comb.inputs['Z'])
    vsub = no(nt, 'ShaderNodeVectorMath', operation='SUBTRACT')
    L(vet, vsub.inputs[0])
    L(comb.outputs[0], vsub.inputs[1])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 34.0, 'Detail': 2.0})
    L(vsub.outputs['Vector'], ru.inputs['Vector'])
    bol = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.64, 'From Max': 0.72})
    L(ru.outputs['Fac'], bol.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.45, 0.13, 0.005, 1)
    cor.inputs[7].default_value = (1.0, 0.56, 0.08, 1)
    L(faixa.outputs['Result'], cor.inputs[0])
    cor2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor2.inputs[7].default_value = (1.0, 0.68, 0.22, 1)
    L(bol.outputs['Result'], cor2.inputs[0])
    L(cor.outputs[2], cor2.inputs[6])
    L(cor2.outputs[2], b.inputs['Base Color'])
    L(cor2.outputs[2], b.inputs['Emission Color'])
    e1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    e1.inputs[1].default_value = 0.7
    e1.inputs[2].default_value = 0.3
    L(faixa.outputs['Result'], e1.inputs[0])
    e2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    e2.inputs[1].default_value = 0.6
    L(bol.outputs['Result'], e2.inputs[0])
    L(e1.outputs['Value'], e2.inputs[2])
    e3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    e3.inputs[1].default_value = forca
    L(e2.outputs['Value'], e3.inputs[0])
    L(e3.outputs['Value'], b.inputs['Emission Strength'])
    return m


def fita_mat():
    """Revestimento do cano enterrado: fita betuminosa preta enrolada (faixas sobrepostas), terra grudada."""
    m = mats.material('Fita do cano enterrado', (0.035, 0.032, 0.028), 0, 0.5, pintura=False, sujeira=1.0, desgaste=0.0)
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = no(nt, 'ShaderNodeTexCoord')
    wv = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', wave_profile='SAW')
    wv.inputs['Scale'].default_value = 9.0
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    nt.links.new(wv.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def bump_ruido(m, escala, forca):
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 8.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': forca})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nk = next((l for l in nt.links if l.to_socket == b.inputs['Normal']), None)
    if nk:
        nt.links.new(nk.from_socket, bump.inputs['Normal'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


base3d.M.update({
    'solo': solo_mat(),
    'grama': grama_mat(),
    'terra': bump_ruido(mats.material('Terra revirada', (0.075, 0.052, 0.034), 0, 0.85, pintura=False, sujeira=0.6,
                                      desgaste=0.0), 30.0, 0.6),
    'areia': bump_ruido(mats.material('Berço de areia', (0.42, 0.34, 0.22), 0, 0.95, pintura=False, sujeira=0.3,
                                      desgaste=0.0), 40.0, 0.4),
    'aterro': bump_ruido(mats.material('Reaterro', (0.15, 0.105, 0.07), 0, 0.95, pintura=False, sujeira=0.6,
                                       desgaste=0.0), 14.0, 0.7),
    'pedra': bump_ruido(mats.material('Pedra', (0.2, 0.19, 0.17), 0, 0.85, pintura=False, sujeira=0.8, desgaste=0.0),
                        12.0, 0.5),
    'concreto_poco': mats.material('Concreto do poço', (0.24, 0.235, 0.22), 0, 0.9, sujeira=1.0, desgaste=0.0, ferrugem=0.25),
    'umido': mats.material('Concreto úmido', (0.12, 0.115, 0.1), 0, 0.3, pintura=False, sujeira=0.6, desgaste=0.0),
    'musgo': bump_ruido(mats.material('Musgo', (0.06, 0.11, 0.025), 0, 0.95, pintura=False, sujeira=0.5,
                                      desgaste=0.0), 60.0, 0.8),
    'ferrugem_esc': mats.material('Escorrido de ferrugem', (0.3, 0.1, 0.03), 0, 0.8, pintura=False, sujeira=0.3,
                                  desgaste=0.0),
    'fita': fita_mat(),
    'agua': liquido_mat('Água parada', (0.05, 0.05, 0.04), 0.0, 0.6, 0.02),
    'fluxo_c': fluxo_caminho_mat('Seiva no cotovelo de vidro', 10.0),
    'vidro_tampa': vidro_mat(),
    'baliza': emissivo('Baliza âmbar', (1.0, 0.5, 0.05), 8.0),
    'vapor_r': base3d.volume_mat('Vapor do respiro', (0.9, 0.9, 0.92), 2.5, 0.9, 1.7),
})
rustico(base3d.M['concreto_poco'], amassado=0.05, fuligem=0.6, lama=0.7)
base3d.M['vidro_tampa'].node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.25
rustico(base3d.M['terra'], poeira=0.22, lama=0.0, fuligem=0.0, amassado=0.25)


# ------------------------------------------------------------------ utilidades
def varrer_uv(bm, pts, raio, lados=32, tampas=(True, True)):
    """Tubo varrido com UV: u = comprimento ao longo do caminho, v = volta (para o fluxo que faz a curva)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    uv = bm.loops.layers.uv.verify()
    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + (pts[i] - pts[i - 1]).length)
    tans = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    e1 = Z.cross(tans[0])
    if e1.length < 1e-4:
        e1 = tans[0].orthogonal()
    e1.normalize()
    aneis = []
    for i in range(n):
        t = tans[i]
        e1 = (e1 - t * e1.dot(t)).normalized()
        e2 = t.cross(e1)
        aneis.append([bm.verts.new(pts[i] + (e1 * math.cos(a) + e2 * math.sin(a)) * raio)
                      for a in (k * 2 * PI / lados for k in range(lados))])
    for i in range(n - 1):
        A, B = aneis[i], aneis[i + 1]
        for j in range(lados):
            j1 = (j + 1) % lados
            f = bm.faces.new((A[j], A[j1], B[j1], B[j]))
            for lp, c in zip(f.loops, ((s[i], j / lados), (s[i], (j + 1) / lados), (s[i + 1], (j + 1) / lados),
                                       (s[i + 1], j / lados))):
                lp[uv].uv = c
    if tampas[0]:
        bm.faces.new(list(reversed(aneis[0])))
    if tampas[1]:
        bm.faces.new(aneis[-1])


def arco(c, r, a0, a1, n, eixo_y=True):
    """Pontos de um arco no plano y-z (local) em volta de c: p = c + r(sin θ·ŷ + cos θ·ẑ)."""
    c = Vector(c)
    return [c + Vector((0, r * math.sin(a), r * math.cos(a))) for a in (a0 + (a1 - a0) * i / n for i in range(n + 1))]


GOT = []          # (ponto mundo, material, vezes por laço, fase, z do chão)


def pingo2(P, p_local, z_chao=0.0, mat='gota', vezes=1, poca='derramada', r_poca=0.07):
    p = P.W(p_local)
    GOT.append((p, mat, vezes, random.random(), z_chao))
    if no_corte(p.x, p.y):
        return
    bm = bmesh.new()
    mancha(bm, (p.x, p.y), r_poca, z_chao + 0.0025 + random.random() * 0.001)
    obj('poca_pingo', bm, poca)


def poca_mundo(c, r, mat, z=0.003, com_halo=True):
    if no_corte(c[0], c[1]):
        return
    bm = bmesh.new()
    mancha(bm, c, r, z)
    obj('mancha', bm, mat)
    if com_halo:
        halo(c, r, z)


def serie_plana(P, c, normal, horiz, n, alt, apagado=0.35):
    """Estêncil numa face plana: reaproveita serie() com raio enorme (curvatura desprezível)."""
    c, d = Vector(c), Vector(normal).normalized()
    u = Vector(horiz).normalized()
    s, up = base_lat(u)
    a = math.atan2(d.dot(up), d.dot(s))
    Rg = 60.0
    serie(P, c - d * Rg, u, Rg, a, n, alt, apagado)


POCAS = []        # (x, y, r) no mundo: sem grama por cima
RESPIROS = []     # boca do respiro (mundo) para o vapor
MARCOS = []

# ------------------------------------------------------------------ medidas da caixa (local: superfície ao sul)
YF1 = 0.03                  # face do par de flanges de cima (aço → vidro)
YG0 = YF1 + EF              # começo do vidro
RBEND = 0.2                 # raio do cotovelo de vidro
YV = YG0 + RBEND            # eixo da descida
ZF2 = -0.10                 # par de flanges de baixo (vidro → aço)
ZB0, RB2 = -0.74, 0.16      # cotovelo de baixo
ZE = ZB0 - RB2              # eixo do cano enterrado (−0,9)
YS0, YS1 = -0.15, -0.09     # parede sul (lado da superfície)
YN0, YN1 = 0.44, 0.50       # parede norte (lado enterrado), face externa na borda do tile
XW, XI = 0.42, 0.36         # meia largura externa / interna
ZFUNDO, ZPISO = -1.25, -1.17
ZTETO, ZLAJE = 0.50, 0.58
YVAL = -0.31                # válvula de bloqueio
YVT = -0.068                # ventosa


def poco(tag, cx, cy, quartos, sx, saida=False):
    """Caixa de concreto da entrada (saida=False) ou da saída. Geometria local com a superfície ao sul; sx diz de
    que lado local (±x) ficam os acessórios que devem ir para o norte do mundo (atrás do plano do corte)."""
    P = Peca('poco_' + tag, cx, cy, quartos)        # caixa: entra no corte
    Ln = Peca('linha_' + tag, cx, cy, quartos)      # tubulação: fica inteira no corte
    C = lambda y, z=CZ: Vector((0, y, z))
    cz = 'concreto_poco'
    # --- paredes, fundo, laje (caixas sem sobreposição)
    caixa_de(P.B(cz), (-XW, YS0, ZFUNDO), (XW, YS1, ZTETO))
    caixa_de(P.B(cz), (-XW, YN0, ZFUNDO), (XW, YN1, ZTETO))
    for s_ in (-1, 1):
        caixa_de(P.B(cz), (s_ * XI, YS1, ZFUNDO), (s_ * XW, YN0, ZTETO))
    caixa_de(P.B(cz), (-XI, YS1, ZFUNDO), (XI, YN0, ZPISO))
    # laje com abertura (x ±0,25; y 0..0,40) e canto lascado no lado −sx da superfície
    xl = -sx
    caixa_de(P.B(cz), (min(xl * 0.34, -sx * -XW), YS0, ZTETO), (max(xl * 0.34, -sx * -XW), 0.0, ZLAJE))
    caixa_de(P.B(cz), (min(xl * 0.34, xl * XW), -0.07, ZTETO), (max(xl * 0.34, xl * XW), 0.0, ZLAJE))
    caixa_de(P.B(cz), (min(xl * 0.34, xl * XW), YS0, ZTETO), (max(xl * 0.34, xl * XW), -0.07, ZTETO + 0.025))
    caixa_de(P.B(cz), (-XW, 0.40, ZTETO), (XW, YN1, ZLAJE))
    for s_ in (-1, 1):
        caixa_de(P.B(cz), (s_ * 0.25, 0.0, ZTETO), (s_ * XW, 0.40, ZLAJE))
    for k in range(3):                                                       # vergalhões expostos no lascado
        q = Vector((xl * (0.36 + 0.025 * k), YS0 + 0.03 + 0.03 * k, ZTETO + 0.04))
        pts = [q + Vector((0, -0.04, 0)), q + Vector((0, 0.07, 0))] if k != 1 else \
            [q + Vector((0, 0.07, -0.01)), q + Vector((0, -0.01, 0)), q + Vector((xl * 0.035, -0.06, 0.035))]
        mangueira(P.B('aco'), pts, 0.005)
    pedra(P.B(cz), Vector((xl * 0.47, YS0 - 0.08, 0.02)), 0.035, 0.6)       # caco de concreto caído
    pedra(P.B(cz), Vector((xl * 0.5, YS0 - 0.02, 0.015)), 0.02, 0.6)
    # colarinho na base
    caixa_de(P.B(cz), (-XW - 0.03, YS0 - 0.03, -0.03), (XW + 0.03, YS0, 0.05))
    caixa_de(P.B(cz), (-XW - 0.03, YN1, -0.03), (XW + 0.03, YN1 + 0.03, 0.05))
    for s_ in (-1, 1):
        caixa_de(P.B(cz), (min(s_ * XW, s_ * (XW + 0.03)), YS0, -0.03), (max(s_ * XW, s_ * (XW + 0.03)), YN1, 0.05))
    # marcas de forma, furos de amarração, umidade subindo pela base
    for zz in (0.2, 0.38):
        caixa_de(P.B('umido'), (-XW, YS0 - 0.001, zz), (XW, YS0, zz + 0.005))
        for s_ in (-1, 1):
            x_ = s_ * (XW + 0.0005)
            caixa(P.B('umido'), (x_, (YS0 + YN1) / 2, zz), (0.001, YN1 - YS0, 0.005))
    for s_ in (-1, 1):
        for yy in (0.0, 0.33):
            for zz in (0.12, 0.42):
                cil(P.B('preto'), Vector((s_ * (XW + 0.001), yy, zz)), 0.009, 0.003, (1, 0, 0), lados=10)
                if random.random() < 0.7:
                    h = random.uniform(0.06, 0.16)
                    caixa(P.B('ferrugem_esc'), (s_ * (XW + 0.0012), yy + random.uniform(-0.004, 0.004), zz - h / 2 - 0.008),
                          (0.001, random.uniform(0.005, 0.012), h))
    for xx in (-0.25, 0.25):
        cil(P.B('preto'), Vector((xx, YS0 - 0.001, 0.12)), 0.009, 0.003, (0, 1, 0), lados=10)
    caixa_de(P.B('umido'), (-XW - 0.0015, YS0 - 0.0015, 0.0), (XW + 0.0015, YS0, 0.11))
    for s_ in (-1, 1):
        caixa_de(P.B('umido'), (min(s_ * XW, s_ * (XW + 0.0015)), YS0, 0.0), (max(s_ * XW, s_ * (XW + 0.0015)), YN1, 0.08 + 0.04 * random.random()))
    for k in range(9):                                                       # musgo no pé da parede
        s_ = random.choice((-1, 1))
        if random.random() < 0.4:
            q = Vector((random.uniform(-0.38, 0.38), YS0 - 0.035, 0.05))
        else:
            q = Vector((s_ * (XW + 0.035), random.uniform(YS0, YN1), 0.05))
        pedra(P.B('musgo'), q, random.uniform(0.02, 0.035), 0.45)
    serie_plana(P, (0.0, YS0, 0.11), (0, -1, 0), (1, 0, 0), 5, 0.05)
    for k in range(30):                                                      # escorridos de chuva e fuligem
        h = random.uniform(0.08, 0.42)
        lg = random.uniform(0.008, 0.045)
        mt = random.choice(('umido', 'umido', 'umido', 'ferrugem_esc'))
        face = random.choice(('S', 'X', 'X'))
        if face == 'S':
            caixa(P.B(mt), (random.uniform(-0.39, 0.39), YS0 - 0.0009, ZTETO - h / 2), (lg, 0.0012, h))
        else:
            s_ = random.choice((-1, 1))
            caixa(P.B(mt), (s_ * (XW + 0.0009), random.uniform(YS0 + 0.02, YN1 - 0.02), ZTETO - h / 2), (0.0012, lg, h))
    for k in range(10):                                                      # terra, folhas e óleo na laje e na tampa
        q = Vector((random.uniform(-0.38, 0.38), random.uniform(-0.12, 0.47), ZLAJE + 0.02))
        pedra(P.B('terra'), q, random.uniform(0.006, 0.014), 0.3)
    for k in range(3):
        bm = bmesh.new()
        mancha(bm, (0, 0), random.uniform(0.02, 0.05), 0)
        q = Vector((random.uniform(-0.25, 0.25), random.choice((0.0, 0.39)), ZLAJE + 0.0205))
        for v in bm.verts:
            v.co = P.W(q + Vector((v.co.x, v.co.y * 0.5, 0)))
        obj('poca_tampa_%s' % tag, bm, 'oleo')
    serie_plana(P, (-sx * XW, 0.17, 0.33), (-sx, 0, 0), (0, -sx, 0), 6, 0.045)
    # --- passamuros na parede sul (anéis) e vazamento de seiva por ele
    for yy in (YS0 - 0.01, YS1 + 0.01):
        cil(Ln.B('ferro', True), C(yy), 0.15, 0.02, (0, 1, 0), lados=40)
    cil(Ln.B('ferro', True), Vector((0, YN0 - 0.01, ZE)), 0.15, 0.02, (0, 1, 0), lados=40)
    for k in range(6):
        x_ = random.uniform(-0.12, 0.12)
        h = random.uniform(0.12, CZ - 0.15)
        caixa(P.B('crosta'), (x_, YS0 - 0.0015, CZ - 0.13 - h / 2), (random.uniform(0.01, 0.025), 0.002, h))
    for k in range(5):
        x_ = random.uniform(-0.15, 0.15)
        h = random.uniform(0.06, 0.2)
        caixa(P.B('ferrugem_esc'), (x_, YS0 - 0.0013, CZ - 0.14 - h / 2), (random.uniform(0.006, 0.014), 0.002, h))
    pingo2(Ln, Vector((0.05, YS0 - 0.025, CZ - 0.145)), 0.0, 'gota', 2, 'derramada', 0.06)
    pw = P.W(Vector((0.03, YS0 - 0.2, 0)))
    POCAS.append((pw.x, pw.y, 0.2))
    poca_mundo((pw.x, pw.y), 0.09, 'derramada', 0.0029)
    # --- tubulação da superfície: flange na borda, válvula atuada, ventosa
    flange(Ln, C(-0.5), (0, -1, 0))
    tubo(Ln.B('cano', True), C(-0.47), C(YF1 - 0.045), R, 32)
    bv = 'ferro' if saida else 'oxido'
    bmesh.ops.create_uvsphere(Ln.B(bv, True), u_segments=32, v_segments=16, radius=0.115,
                              matrix=Matrix.Translation(C(YVAL)))
    for yy in (YVAL - 0.057, YVAL + 0.057):
        toro(Ln.B('ferro', True), C(yy), R + 0.002, 0.005, 40, 6, eixo=(0, 1, 0))
    cil(Ln.B('ferro', True), C(YVAL) + Z * 0.115, 0.05, 0.02, lados=24)    # castelo
    tubo(Ln.B('ferro', True), C(YVAL) + Z * 0.1, C(YVAL) + Z * 0.2, 0.03, 16)
    caixa(Ln.B('grafite'), C(YVAL) + Z * 0.24, (0.12, 0.12, 0.08))        # atuador
    cil(Ln.B('grafite', True), C(YVAL) + Vector((sx * 0.09, 0, 0.24)), 0.035, 0.06, (1, 0, 0), lados=20)
    for k in range(4):
        toro(Ln.B('aco', True), C(YVAL) + Vector((sx * (0.068 + k * 0.013), 0, 0.24)), 0.037, 0.003, 20, 6, eixo=(1, 0, 0))
    caixa(Ln.B('amarelo'), C(YVAL) + Z * 0.284, (0.07, 0.014, 0.008), Matrix.Rotation(0.4, 3, 'Z'))  # indicador
    caixa(Ln.B('ambar'), C(YVAL) + Vector((-sx * 0.061, 0, 0.25)), (0.002, 0.05, 0.012))
    for k in range(4):
        a = PI / 4 + k * PI / 2
        cil(Ln.B('aco'), C(YVAL) + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.205)), 0.009, 0.01, lados=6)
    serie(Ln, C(YVAL), (0, 1, 0), 0.115, math.radians(205), 3, 0.022)
    pingo2(Ln, C(YVAL) + Vector((0.01, 0.02, -0.113)), 0.0, 'gota', 1, 'derramada', 0.08)
    manometro(Ln, C(-0.21) + Vector((sx * 0.17, 0, 0.03)), (sx, 0, 0), C(-0.21) + Vector((sx * 0.09, 0, 0.02)))
    # ventosa: tomada no topo do cano, atravessa a laje
    tubo(Ln.B('cano', True), C(YVT) + Z * 0.08, C(YVT) + Z * 0.33, 0.02, 16)
    cil(Ln.B('ferro', True), C(YVT) + Z * (ZLAJE - CZ + 0.007), 0.042, 0.014, lados=20)
    bmesh.ops.create_uvsphere(Ln.B('ferro', True), u_segments=18, v_segments=9, radius=0.03,
                              matrix=Matrix.Translation(C(YVT) + Z * 0.3))
    caixa(Ln.B('grafite'), C(YVT) + Vector((sx * 0.045, 0, 0.3)), (0.04, 0.035, 0.035))
    cil(Ln.B('oxido', True), C(YVT) + Z * 0.38, 0.055, 0.1, lados=28)
    cil(Ln.B('ferro', True), C(YVT) + Z * 0.437, 0.064, 0.016, lados=28)
    for k in range(6):
        a = k * PI / 3
        cil(Ln.B('aco'), C(YVT) + Vector((math.cos(a) * 0.052, math.sin(a) * 0.052, 0.449)), 0.008, 0.01, lados=6)
    tubo(Ln.B('cano', True), C(YVT) + Z * 0.445, C(YVT) + Z * 0.48, 0.012, 12)
    bmesh.ops.create_uvsphere(Ln.B('cano', True), u_segments=12, v_segments=6, radius=0.012,
                              matrix=Matrix.Translation(C(YVT) + Z * 0.48))
    tubo(Ln.B('cano', True), C(YVT) + Z * 0.48, C(YVT) + Vector((-sx * 0.05, 0, 0.48)), 0.012, 12)
    for k in range(4):
        a = -sx * 0.6 + random.uniform(-0.4, 0.4) + (0 if sx > 0 else PI)
        h = random.uniform(0.03, 0.08)
        caixa(Ln.B('crosta'), C(YVT) + Vector((math.cos(a) * 0.0565, math.sin(a) * 0.0565, 0.42 - h / 2)),
              (0.002, 0.012, h), Matrix.Rotation(a, 3, 'Z'))
    # --- dentro: par de flanges, cotovelo de vidro, descida, cotovelo de raio longo
    flange(Ln, C(YF1), (0, 1, 0))
    flange(Ln, C(YF1), (0, -1, 0), pescoco=False)
    pts = arco((0, YG0, CZ - RBEND), RBEND, 0.0, PI / 2, 28)
    pts += [Vector((0, YV, z)) for z in (0.06, -0.01, ZF2 + EF)]
    varrer(Ln.B('vidro', True), pts, 0.093, 40)
    fl = [C(YF1 - 0.01)] + pts + [Vector((0, YV, ZF2 - 0.01))]
    if saida:
        fl = list(reversed(fl))
    varrer_uv(Ln.B('fluxo_c', True), fl, 0.084, 32)
    flange(Ln, Vector((0, YV, ZF2)), (0, 0, -1), pescoco=False)
    flange(Ln, Vector((0, YV, ZF2)), (0, 0, 1))
    toro(Ln.B('borracha', True), C(YG0 + 0.004), 0.097, 0.005, 40, 6, eixo=(0, 1, 0))      # juntas do vidro
    toro(Ln.B('borracha', True), Vector((0, YV, ZF2 + EF + 0.004)), 0.097, 0.005, 40, 6)
    # tirantes do vidro: dois de lado e um por fora da curva, porcas nas pontas
    def tirante(off_fn, ini, fim_):
        cam = [ini] + [off_fn(p, i) for i, p in enumerate(pts)] + [fim_]
        varrer(Ln.B('aco', True), cam, 0.0075, 10, (True, True))
        for q, d in ((ini, Vector((0, -1, 0))), (fim_, Vector((0, 0, -1)))):
            cil(Ln.B('aco'), q + d * 0.005, 0.015, 0.012, d, lados=6)
    for s_ in (-1, 1):
        tirante(lambda p, i: p + Vector((s_ * RB, 0, 0)), C(YF1 - EF - 0.012) + Vector((s_ * RB, 0, 0)),
                Vector((s_ * RB, YV, ZF2 - EF - 0.012)))
    cen = Vector((0, YG0, CZ - RBEND))

    def fora(p, i):
        d = p - cen
        d.x = 0
        if p.z < cen.z:
            d = Vector((0, 1, 0))
        return p + d.normalized() * RB
    tirante(fora, C(YF1 - EF - 0.012, CZ + RB), Vector((0, YV + RB, ZF2 - EF - 0.012)))
    for ang in (PI / 4, 1.25):                                               # anéis de campo da IA
        p = cen + Vector((0, RBEND * math.sin(ang), RBEND * math.cos(ang)))
        toro(Ln.B('violeta', True), p, 0.113, 0.004, 48, 8, eixo=Vector((0, math.cos(ang), -math.sin(ang))))
    toro(Ln.B('violeta', True), Vector((0, YV, 0.02)), 0.113, 0.004, 48, 8)
    # descida em aço, abraçadeira à parede norte, cotovelo de raio longo e saída pela parede
    tubo(Ln.B('cano', True), Vector((0, YV, ZF2 - 0.05)), Vector((0, YV, ZB0)), R, 32)
    curva = [Vector((0, YV + RB2 - RB2 * math.cos(a), ZB0 - RB2 * math.sin(a))) for a in (PI / 2 * i / 36 for i in range(37))]
    varrer(Ln.B('cano', True), curva, R, 32)
    tubo(Ln.B('cano', True), Vector((0, YV + RB2, ZE)), Vector((0, YN1, ZE)), R, 32)
    for p, e in ((Vector((0, YV, ZB0)), Z), (Vector((0, YV + RB2, ZE)), Vector((0, 1, 0)))):
        toro(Ln.B('ferro', True), p, R + 0.002, 0.005, 40, 6, eixo=e)
    toro(Ln.B('aco', True), Vector((0, YV, -0.45)), R + 0.008, 0.008, 40, 8)
    for s_ in (-1, 1):
        viga(Ln.B('aco'), Vector((s_ * 0.05, YV + R + 0.01, -0.45)), Vector((s_ * 0.05, YN0, -0.45)), 0.016)
        cil(Ln.B('aco'), Vector((s_ * 0.05, YN0 - 0.004, -0.45)), 0.014, 0.008, (0, 1, 0), lados=6)
    serie(Ln, Vector((0, YV, -0.5)), (0, 0, 1), R, math.radians(180 if sx > 0 else 0), 4, 0.025)
    remendo(Ln, Vector((0, YV, -0.3)), (0, 0, 1), R, math.radians(110), math.radians(200), 0.08)
    # pedestal sob o cotovelo de baixo
    yp = YV + RB2 - (RB2 + R) * 0.5
    caixa_de(P.B(cz), (-0.12, 0.2, ZPISO), (0.12, YN0, ZPISO + 0.08))
    caixa(Ln.B('amarelo'), (0, yp, (ZPISO + 0.08 + ZB0 - (RB2 + R) * 0.866) / 2),
          (0.06, 0.012, ZB0 - (RB2 + R) * 0.866 - ZPISO - 0.08))
    caixa(Ln.B('amarelo'), (0, yp, (ZPISO + 0.08 + ZB0 - (RB2 + R) * 0.866) / 2), (0.012, 0.06, ZB0 - (RB2 + R) * 0.866 - ZPISO - 0.08))
    caixa(Ln.B('ferro'), (0, yp, ZPISO + 0.086), (0.1, 0.1, 0.012))
    # --- dentro: umidade, poça, bomba de dreno, boia, gotejamento
    hu = -0.95
    caixa_de(P.B('umido'), (-XI, YS1, ZPISO), (XI, YS1 + 0.0015, hu))
    caixa_de(P.B('umido'), (-XI, YN0 - 0.0015, ZPISO), (XI, YN0, hu + 0.05))
    for s_ in (-1, 1):
        caixa_de(P.B('umido'), (min(s_ * XI, s_ * (XI - 0.0015)), YS1, ZPISO), (max(s_ * XI, s_ * (XI - 0.0015)), YN0, hu - 0.03))
        for k in range(3):                                                   # escorridos vindos da laje
            yy = random.uniform(YS1 + 0.03, YN0 - 0.03)
            h = random.uniform(0.4, 1.1)
            caixa(P.B('umido'), (s_ * (XI - 0.0016), yy, ZTETO - h / 2), (0.001, random.uniform(0.015, 0.04), h))
    bm = bmesh.new()
    mancha(bm, (0, 0), 0.26, 0)
    for v in bm.verts:
        v.co = P.W(Vector((v.co.x * 1.1, 0.15 + v.co.y * 0.95, ZPISO + 0.002)))
        if CORTE:
            v.co.y = max(v.co.y, 0.002)
    obj('agua_%s' % tag, bm, 'agua')
    pingo2(Ln, Vector((0.0, YV - RF + 0.006, ZF2 - EF - 0.002)), ZPISO, 'gota', 2, 'poca', 0.09)
    pingo2(Ln, Vector((0.03, YN0 - 0.02, ZE - 0.152)), ZPISO, 'gota', 1, 'poca', 0.06)
    pb = Vector((sx * 0.25, 0.04, ZPISO))
    cil(P.B('ferro', True), pb + Z * 0.08, 0.055, 0.16, lados=24)
    toro(P.B('aco', True), pb + Z * 0.02, 0.058, 0.006, 24, 6)
    cil(P.B('grafite', True), pb + Z * 0.2, 0.045, 0.08, lados=24)
    caixa(P.B('ambar'), pb + Vector((0, -0.046, 0.21)), (0.02, 0.002, 0.006))
    tubo(P.B('cano', True), pb + Z * 0.24, pb + Vector((0, 0, ZB0 + 0.2 - ZPISO)), 0.018, 14)
    pc = pb + Vector((0, 0, ZB0 + 0.2 - ZPISO))
    bmesh.ops.create_uvsphere(P.B('cano', True), u_segments=14, v_segments=7, radius=0.018, matrix=Matrix.Translation(pc))
    tubo(P.B('cano', True), pc, Vector((sx * (XW + 0.01), pc.y, pc.z)), 0.018, 14)
    cil(P.B('ferro', True), Vector((sx * (XI - 0.005), pc.y, pc.z)), 0.03, 0.01, (1, 0, 0), lados=16)
    mangueira(P.B('borracha'), bezier(pb + Vector((-sx * 0.02, 0.03, 0.24)), pb + Vector((-sx * 0.02, 0.1, 0.5)),
                                      Vector((sx * (XI - 0.012), 0.2, -0.2)), Vector((sx * (XI - 0.012), 0.3, ZTETO - 0.01)), 14), 0.007)
    bo = Vector((sx * 0.3, 0.33, 0))
    caixa(P.B('aco'), (sx * (XI - 0.015), 0.33, -0.6), (0.03, 0.03, 0.012))
    tubo(P.B('aco'), Vector((sx * 0.3, 0.33, -0.6)), Vector((sx * 0.3, 0.33, -1.06)), 0.004, 6)
    bmesh.ops.create_uvsphere(P.B('amarelo', True), u_segments=16, v_segments=8, radius=0.03,
                              matrix=Matrix.Translation(Vector((sx * 0.3, 0.33, -1.09))))
    # --- tampa de inspeção para drone: chapa com janela, moldura, grade, dobradiça, olhal, fiducial, trava
    ty0, ty1, tx = -0.03, 0.43, 0.29
    wy0, wy1, wx = 0.08, 0.37, 0.22
    zt0, zt1 = ZLAJE, ZLAJE + 0.02
    caixa_de(P.B('amarelo'), (-tx, ty0, zt0), (tx, wy0, zt1))
    caixa_de(P.B('amarelo'), (-tx, wy1, zt0), (tx, ty1, zt1))
    for s_ in (-1, 1):
        caixa_de(P.B('amarelo'), (min(s_ * wx, s_ * tx), wy0, zt0), (max(s_ * wx, s_ * tx), wy1, zt1))
    for (a, b_) in (((-tx, ty0), (tx, ty0 + 0.015)), ((-tx, ty1 - 0.015), (tx, ty1)),
                    ((-tx, ty0 + 0.015), (-tx + 0.015, ty1 - 0.015)), ((tx - 0.015, ty0 + 0.015), (tx, ty1 - 0.015))):
        caixa_de(P.B('ferro'), (a[0], a[1], zt1), (b_[0], b_[1], zt1 + 0.014))   # aba de reforço
    caixa_de(P.B('vidro_tampa'), (-wx, wy0, zt0 + 0.006), (wx, wy1, zt0 + 0.014))
    for (a, b_) in (((-wx - 0.02, wy0 - 0.02), (wx + 0.02, wy0)), ((-wx - 0.02, wy1), (wx + 0.02, wy1 + 0.02)),
                    ((-wx - 0.02, wy0), (-wx, wy1)), ((wx, wy0), (wx + 0.02, wy1))):
        caixa_de(P.B('ferro'), (a[0], a[1], zt1), (b_[0], b_[1], zt1 + 0.012))   # moldura da janela
    for k in range(10):
        if k < 6:
            q = Vector((-wx - 0.01 + (2 * wx + 0.02) * (k % 3) / 2, wy0 - 0.01 if k < 3 else wy1 + 0.01, zt1 + 0.014))
        else:
            q = Vector((-wx - 0.01 if k < 8 else wx + 0.01, wy0 + (wy1 - wy0) * (0.33 if k % 2 == 0 else 0.67), zt1 + 0.014))
        cil(P.B('aco'), q, 0.007, 0.006, lados=6)
    for yy in (0.175, 0.275):
        caixa_de(P.B('aco'), (-wx - 0.01, yy - 0.006, zt1 + 0.012), (wx + 0.01, yy + 0.006, zt1 + 0.02))
    for k in range(5):                                                       # sujeira grudada no vidro (canto)
        pedra(P.B('terra'), Vector((random.uniform(-wx, -wx + 0.06) * (1 if k % 2 else -1), random.uniform(wy0, wy0 + 0.04),
                                    zt0 + 0.015)), random.uniform(0.008, 0.016), 0.25)
    for s_ in (-1, 1):                                                       # dobradiça (norte)
        caixa_de(P.B('ferro'), (s_ * 0.13, ty1 - 0.03, zt1), (s_ * 0.22, ty1, zt1 + 0.02))
        caixa_de(P.B('ferro'), (s_ * 0.13, ty1, ZLAJE), (s_ * 0.22, ty1 + 0.04, ZLAJE + 0.02))
        cil(P.B('aco', True), Vector((s_ * 0.175, ty1 + 0.002, zt1 + 0.012)), 0.012, 0.11, (1, 0, 0), lados=12)
    caixa(P.B('ferro'), (0, 0.035, zt1 + 0.01), (0.06, 0.016, 0.02))       # olhal de garra
    cil(P.B('ferro', True), Vector((0, 0.035, zt1 + 0.028)), 0.013, 0.03, (1, 0, 0), lados=12)
    fx = -sx * 0.2                                                          # marca fiducial para o drone
    caixa_de(P.B('preto'), (fx - 0.042, -0.027, zt1), (fx + 0.042, 0.057, zt1 + 0.002))
    for i in range(5):
        for j in range(5):
            if random.random() < 0.5:
                caixa(P.B('mostrador'), (fx - 0.028 + i * 0.014, 0.015 - 0.028 + j * 0.014, zt1 + 0.0025),
                      (0.0135, 0.0135, 0.002))
    caixa(P.B('grafite'), (sx * 0.2, ty0 - 0.03, ZLAJE + 0.02), (0.07, 0.04, 0.04))    # trava atuada
    tubo(P.B('cromo'), Vector((sx * 0.2, ty0 - 0.01, ZLAJE + 0.012)), Vector((sx * 0.2, ty0 + 0.02, ZLAJE + 0.012)), 0.007, 10)
    caixa(P.B('ambar'), (sx * 0.2, ty0 - 0.051, ZLAJE + 0.025), (0.03, 0.002, 0.006))
    if saida:                                                               # remendo aparafusado na tampa
        caixa_de(P.B('oxido'), (min(0.04 * sx, 0.2 * sx), 0.335, zt1), (max(0.04 * sx, 0.2 * sx), 0.415, zt1 + 0.004))
    for (a, b_) in (((-XW, YS0), (XW, YS0 + 0.035)), ((-XW, YN1 - 0.035), (XW, YN1))):     # listras na laje
        if a[1] == YS0:
            caixa_de(P.B('listras'), (min(-xl * XW, xl * 0.34), YS0, ZLAJE), (max(-xl * XW, xl * 0.34), YS0 + 0.035, ZLAJE + 0.002))
        else:
            caixa_de(P.B('listras'), (a[0], a[1], ZLAJE), (b_[0], b_[1], ZLAJE + 0.002))
    for (bx, by) in ((sx * 0.36, -0.11), (-sx * 0.36, 0.2), (sx * 0.37, 0.46)):  # balizas de pouso
        cil(P.B('ferro', True), Vector((bx, by, ZLAJE + 0.006)), 0.018, 0.012, lados=12)
        bmesh.ops.create_uvsphere(P.B('baliza', True), u_segments=12, v_segments=6, radius=0.012,
                                  matrix=Matrix.Translation(Vector((bx, by, ZLAJE + 0.016))))
    # respiro pescoço de ganso
    rx, ry = sx * 0.355, 0.24
    cr = [Vector((rx, ry, z)) for z in (ZTETO + 0.02, 0.8, 0.98)]
    cr += [Vector((rx, ry - 0.07 + 0.07 * math.cos(a), 0.98 + 0.07 * math.sin(a))) for a in (PI * i / 20 for i in range(1, 21))]
    cr += [Vector((rx, ry - 0.14, 0.9))]
    varrer(P.B('cinza', True), cr, 0.032, 24)
    cil(P.B('ferro', True), Vector((rx, ry, ZLAJE + 0.008)), 0.06, 0.016, lados=24)
    for k in range(4):
        a = PI / 4 + k * PI / 2
        cil(P.B('aco'), Vector((rx + math.cos(a) * 0.046, ry + math.sin(a) * 0.046, ZLAJE + 0.02)), 0.009, 0.01, lados=6)
    tubo(P.B('ferro', True), Vector((rx, ry - 0.14, 0.875)), Vector((rx, ry - 0.14, 0.905)), 0.04, 24)
    cil(P.B('preto', True), Vector((rx, ry - 0.14, 0.88)), 0.034, 0.003, lados=20)
    serie(P, Vector((rx, ry, 0.7)), (0, 0, 1), 0.032, math.radians(180 if sx < 0 else 0), 3, 0.02)
    RESPIROS.append(P.W(Vector((rx, ry - 0.14, 0.87))))
    # sensor da IA no canto da laje, antena, cabo até a caixa de junção
    sxp = Vector((-sx * 0.34, 0.45, ZLAJE))
    cil(P.B('grafite', True), sxp + Z * 0.015, 0.035, 0.03, lados=20)
    bmesh.ops.create_uvsphere(P.B('violeta', True), u_segments=12, v_segments=6, radius=0.014,
                              matrix=Matrix.Translation(sxp + Z * 0.04))
    bmesh.ops.create_uvsphere(P.B('vidro', True), u_segments=20, v_segments=10, radius=0.026,
                              matrix=Matrix.Translation(sxp + Z * 0.03))
    tubo(P.B('aco'), sxp + Vector((sx * 0.02, 0.0, 0.02)), sxp + Vector((sx * 0.02, 0.0, 0.24)), 0.003, 6)
    bmesh.ops.create_uvsphere(P.B('ambar', True), u_segments=8, v_segments=4, radius=0.006,
                              matrix=Matrix.Translation(sxp + Vector((sx * 0.02, 0, 0.245))))
    # caixa de junção na parede −sx (sul do mundo), conduíte até o chão, cabos do atuador e do sensor
    jb = Vector((-sx * (XW + 0.025), 0.12, 0.22))
    caixa(P.B('grafite'), jb, (0.05, 0.17, 0.21))
    caixa(P.B('cinza'), jb + Vector((-sx * 0.027, 0, 0)), (0.004, 0.16, 0.2))
    for dy in (-0.07, 0.07):
        for dz in (-0.09, 0.09):
            cil(P.B('aco'), jb + Vector((-sx * 0.03, dy, dz)), 0.006, 0.006, (1, 0, 0), lados=6)
    caixa(P.B('ambar'), jb + Vector((-sx * 0.03, 0.05, 0.075)), (0.002, 0.02, 0.008))
    serie_plana(P, jb + Vector((-sx * 0.0295, -0.02, 0.03)), (-sx, 0, 0), (0, -sx, 0), 4, 0.02, 0.2)
    tubo(P.B('cinza'), jb + Vector((0, -0.05, -0.105)), Vector((jb.x, jb.y - 0.05, -0.05)), 0.015, 12)
    for zz in (0.06, -0.0):
        toro(P.B('aco', True), Vector((jb.x, jb.y - 0.05, zz)), 0.017, 0.003, 16, 6)
    fios(P, jb + Vector((0, 0.05, -0.105)), jb + Vector((-sx * 0.04, 0.09, -0.2)))
    a = C(YVAL) + Vector((-sx * 0.06, 0.0, 0.25))
    b_ = jb + Vector((0, -0.04, 0.105))
    mangueira(P.B('borracha'), bezier(a, a + Vector((-sx * 0.42, -0.04, 0.0)), b_ + Vector((0, -0.12, 0.25)), b_, 18), 0.009)
    a = sxp + Vector((-sx * 0.03, 0, 0.01))
    mangueira(P.B('borracha'), bezier(a, a + Vector((-sx * 0.08, 0, 0.0)), b_ + Vector((0, 0.15, 0.2)), b_ + Vector((0, 0.06, 0)), 14), 0.006)
    # seiva escorrida na laje (ventosa) e óleo da trava
    for k in range(3):
        bm = bmesh.new()
        mancha(bm, (0, 0), random.uniform(0.02, 0.04), 0)
        for v in bm.verts:
            v.co = P.W(Vector((v.co.x + random.uniform(-0.03, 0.03), YVT - 0.06 + v.co.y, ZLAJE + 0.0025)))
        obj('poca_laje_%s' % tag, bm, 'derramada')
    pingo2(Ln, C(YVT) + Vector((-sx * 0.05, 0, 0.468)), ZLAJE, 'gota', 1, 'crosta', 0.03)
    P.fim()
    Ln.fim()
    return P, Ln


# ------------------------------------------------------------------ montagem
cano_reto('reto_o', 0, 0, 1, 'visor', sentido=-1)
cano_reto('reto_l', 7, 0, 1, 'visor', sentido=-1)


def flange_cega(nome, c, u):
    P = Peca(nome, 0, 0, 0)
    c, u = Vector(c), Vector(u)
    cil(P.B('ferro', True), c + u * EF / 2, RF, EF, u, lados=40)
    s, up = base_lat(u)
    for k in range(8):
        a = PI / 8 + k * PI / 4
        p = c + (s * math.cos(a) + up * math.sin(a)) * RB
        tubo(P.B('aco'), p, p + u * 0.057, 0.0105, 8)
        cil(P.B('aco'), p + u * (EF + 0.008), 0.019, 0.016, u, lados=6)
    cil(P.B('amarelo', True), c + u * (EF + 0.004), 0.05, 0.008, u, lados=20)
    P.fim()


flange_cega('tampa_o', (-0.5, 0, CZ), (-1, 0, 0))
flange_cega('tampa_l', (7.5, 0, CZ), (1, 0, 0))
poco('ent', 1, 0, -1, -1, saida=False)
poco('sai', 6, 0, 1, 1, saida=True)

# trecho enterrado (mundo)
E = Peca('enterrado', 0, 0, 0)
XA, XB = 1.5, 5.5
tubo(E.B('fita', True), (XA, 0, ZE), (XB, 0, ZE), R + 0.006, 32)
for xx in (2.5, 3.5, 4.5):
    tubo(E.B('borracha', True), (xx - 0.08, 0, ZE), (xx + 0.08, 0, ZE), R + 0.014, 32)
    for d in (-0.08, 0.08):
        toro(E.B('borracha', True), Vector((xx + d, 0, ZE)), R + 0.012, 0.004, 32, 6, eixo=(1, 0, 0))
tubo(E.B('fio_m'), (XA, 0, ZE + R + 0.022), (XB, 0, ZE + R + 0.022), 0.004, 8)
for xx in (2.0, 3.0, 4.0, 5.0):
    for d in (-0.035, 0.035):
        toro(E.B('violeta', True), Vector((xx + d, 0, ZE)), R + 0.055, 0.005, 48, 8, eixo=(1, 0, 0))
    for k in range(3):                                                       # pedras da vala encostadas
        pedra(E.B('pedra'), Vector((xx + random.uniform(-0.4, 0.4), random.uniform(0.05, 0.3), random.uniform(-1.1, -0.2))),
              random.uniform(0.02, 0.05), 0.7)
E.fim()
yc0 = 0.0 if CORTE else -0.075
bm = bmesh.new()
caixa_de(bm, (XA, yc0, -0.452), (XB, 0.075, -0.447))
obj('fita_aviso', bm, 'listras')
bm = bmesh.new()
caixa_de(bm, (XA, 0.0 if CORTE else -0.35, -1.15), (XB, 0.35, -0.68))
obj('aterro_areia', bm, 'areia')
bm = bmesh.new()
caixa_de(bm, (XA, 0.0 if CORTE else -0.35, -0.68), (XB, 0.35, -0.002))
obj('aterro', bm, 'aterro')


# terra revirada sobre a vala
def hmonte(x, y):
    t = abs(y) / 0.44
    if t >= 1:
        return -0.012
    base = 0.1 * (1 - t * t) ** 0.7 - 0.012 * t
    n = mnoise.noise(Vector((x * 3.1, y * 3.1, 0.5))) * 0.035 + mnoise.noise(Vector((x * 12, y * 12, 2.0))) * 0.014
    return base + n * (1 - 0.6 * t)


bm = bmesh.new()
nx = 160
ys = [(-0.44 if not CORTE else 0.0) + i * 0.02 for i in range(int((0.88 if not CORTE else 0.44) / 0.02) + 1)]
grade = [[bm.verts.new((XA + (XB - XA) * i / nx, y, hmonte(XA + (XB - XA) * i / nx, y))) for y in ys] for i in range(nx + 1)]
for i in range(nx):
    for j in range(len(ys) - 1):
        bm.faces.new((grade[i][j], grade[i + 1][j], grade[i + 1][j + 1], grade[i][j + 1]))
if CORTE:
    base_ = [bm.verts.new((v.co.x, 0.0, -0.06)) for v in (g[0] for g in grade)]
    for i in range(nx):
        bm.faces.new((grade[i][0], base_[i], base_[i + 1], grade[i + 1][0]))
monte = obj('monte', bm, 'terra')
suavizar(monte)
bm = bmesh.new()
for k in range(320):
    x = random.uniform(XA + 0.05, XB - 0.05)
    y = random.uniform(-0.42, 0.42)
    if no_corte(x, y + 0.03):
        continue
    pedra(bm, (x, y, hmonte(x, y) + 0.006), random.uniform(0.012, 0.045), 0.65)
obj('torrao', bm, 'terra')
bm = bmesh.new()
for k in range(45):
    x = random.uniform(-1.0, 8.0)
    y = random.uniform(-2.0, 2.5)
    if no_corte(x, y + 0.05) or (abs(y) < 0.2 and -0.6 < x < 7.6):
        continue
    if 0.8 < x < 6.2 and abs(y) < 0.5:
        if not (XA < x < XB):
            continue
        z = hmonte(x, y)
    else:
        z = 0.0
    pedra(bm, (x, y, z + 0.006), random.uniform(0.015, 0.05), 0.55)
obj('pedra', bm, 'pedra')


# marcos de concreto (lado norte da vala) e placas rasas sobre o cano
def tronco(bm, z0, z1, w, folga=0.0):
    larg = lambda z: (0.12 - 0.034 * (z + 0.25) / 0.63) / 2 + folga
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res['verts']:
        z = z0 if v.co.z < 0 else z1
        v.co = Vector((math.copysign(larg(z), v.co.x), math.copysign(larg(z), v.co.y), z))


for i, xx in enumerate((2.0, 3.0, 4.0, 5.0)):
    yy = 0.53 + random.uniform(-0.02, 0.02)
    MARCOS.append((xx, yy))
    P = Peca('marco%d' % i, xx, yy, 0)
    incl = Matrix.Rotation(random.uniform(-0.06, 0.06), 4, 'X') @ Matrix.Rotation(random.uniform(-0.05, 0.05), 4, 'Y')
    P.M = P.M @ incl
    tronco(P.B('concreto_poco'), -0.25, 0.38, 0.12)
    tronco(P.B('amarelo'), 0.29, 0.381, 0.12, 0.0015)
    w = (0.12 - 0.034 * (0.18 + 0.25) / 0.63) / 2
    caixa(P.B('ferro'), (0, -w - 0.004, 0.18), (0.08, 0.004, 0.12))       # plaqueta com seta do fluxo (leste)
    for dx in (-0.032, 0.032):
        cil(P.B('aco'), Vector((dx, -w - 0.007, 0.23)), 0.005, 0.004, (0, 1, 0), lados=6)
    caixa(P.B('tinta'), (-0.005, -w - 0.0065, 0.17), (0.04, 0.001, 0.008))
    for sg in (1, -1):
        caixa(P.B('tinta'), (0.016, -w - 0.0065, 0.17 + sg * 0.008), (0.022, 0.001, 0.007), Matrix.Rotation(-sg * 0.7, 3, 'Y'))
    serie_plana(P, (0, -w - 0.006, 0.135), (0, -1, 0), (1, 0, 0), 3, 0.016, 0.25)
    cil(P.B('grafite', True), Vector((0, 0, 0.388)), 0.022, 0.014, lados=16)
    bmesh.ops.create_uvsphere(P.B('baliza', True), u_segments=12, v_segments=6, radius=0.011,
                              matrix=Matrix.Translation(Vector((0, 0, 0.398))))
    if i == 2:                                                               # marco trincado e remendado
        caixa(P.B('umido'), (0.0, -w - 0.0008, 0.05), (0.004, 0.001, 0.14), Matrix.Rotation(0.3, 3, 'Y'))
    for k in range(5):
        a = random.uniform(0, 2 * PI)
        pedra(P.B('terra'), Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, 0.0)), random.uniform(0.015, 0.03), 0.6)
    P.fim()
for xx in (2.5, 3.5, 4.5):
    P = Peca('placa%d' % int(xx), xx, 0, 0)
    h = hmonte(xx, 0)
    caixa_de(P.B('concreto_poco'), (-0.08, -0.08, -0.02 - h + h), (0.08, 0.08, h + 0.025))
    caixa(P.B('tinta'), (-0.01, 0, h + 0.0255), (0.07, 0.012, 0.001))
    for sg in (1, -1):
        caixa(P.B('tinta'), (0.03, sg * 0.012, h + 0.0255), (0.035, 0.01, 0.001), Matrix.Rotation(-sg * 0.7, 3, 'Z'))
    caixa(P.B('ambar'), (0, -0.06, h + 0.0255), (0.1, 0.006, 0.001))
    P.fim()

# pedras grandes e raízes cortadas pela face do corte (só existem no modo corte)
if CORTE:
    bm = bmesh.new()
    for k in range(60):
        x = random.uniform(-3.0, 10.0)
        z = random.uniform(-3.0, -0.35)
        if (0.75 < x < 6.25 and z > -1.4) or (XA - 0.1 < x < XB + 0.1 and z > -1.25):
            continue
        r = random.uniform(0.04, 0.12) * (1.4 if z < -1.2 else 1.0)
        res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)            # pedra encravada no barranco
        sem = Vector((random.random() * 50, random.random() * 50, 0))
        for v in res['verts']:
            d = v.co.normalized()
            v.co = v.co * (0.8 + 0.35 * mnoise.noise(d * 1.6 + sem)) * Vector((1.0, 0.85, 0.65))
            v.co += Vector((x, r * random.uniform(0.25, 0.6) if False else 0, z))
        for v in res['verts']:
            v.co.y += r * 0.45
    pedras_corte = obj('pedras_corte', bm, 'pedra')
    suavizar(pedras_corte)
    bm = bmesh.new()
    for k in range(40):
        x = random.uniform(-3.0, 10.0)
        if 0.8 < x < 6.2:
            continue
        a = Vector((x, random.uniform(-0.02, 0.06), -0.02))
        pts = bezier(a, a + Vector((random.uniform(-0.1, 0.1), 0, -0.12)), a + Vector((random.uniform(-0.2, 0.2), 0.02, -0.25)),
                     a + Vector((random.uniform(-0.3, 0.3), -0.04, -random.uniform(0.25, 0.5))), 10)
        mangueira(bm, pts, random.uniform(0.003, 0.008))
    obj('solo_raizes', bm, 'terra')

# manchas no chão
for c_, r_, m_ in (((1.4, -0.85), 0.07, 'oleo'), ((5.9, -0.75), 0.1, 'derramada'),
                   ((6.9, 0.55), 0.08, 'oleo'), ((3.2, -0.62), 0.07, 'derramada')):
    POCAS.append((c_[0], c_[1], r_))
    poca_mundo(c_, r_, m_)

# ------------------------------------------------------------------ chão com furos (caixas e vala) e grama
bm = bmesh.new()
caixa_de(bm, (-14.0, -14.0, -3.6), (22.0, 18.0, 0.0))
solo = obj('solo', bm, 'solo')
furos = bpy.data.collections.new('furos')
sc.collection.children.link(furos)
for (a, b_) in (((0.848, -0.422, -1.252), (1.502, 0.422, 0.2)), ((5.498, -0.422, -1.252), (6.152, 0.422, 0.2)),
                ((XA - 0.002, -0.352, -1.152), (XB + 0.002, 0.352, 0.2))):
    bm = bmesh.new()
    caixa_de(bm, a, b_)
    me = bpy.data.meshes.new('furo')
    bm.to_mesh(me)
    o = bpy.data.objects.new('furo', me)
    furos.objects.link(o)
furos.hide_render = True
furos.hide_viewport = True
md = solo.modifiers.new('furos', 'BOOLEAN')
md.operation = 'DIFFERENCE'
md.operand_type = 'COLLECTION'
md.collection = furos
md.solver = 'EXACT'


def excl(x, y):
    if 0.8 < x < 1.55 and abs(y) < 0.47:
        return True
    if 5.45 < x < 6.2 and abs(y) < 0.47:
        return True
    if XA - 0.05 < x < XB + 0.05 and abs(y) < 0.38 + 0.03 * random.random():
        return True
    if (-0.55 < x < 0.55 or 6.45 < x < 7.55) and abs(y) < 0.17:
        return True
    for (mx, my) in MARCOS:
        if (x - mx) ** 2 + (y - my) ** 2 < 0.085 ** 2:
            return True
    for (px, py, r) in POCAS:
        if (x - px) ** 2 + (y - py) ** 2 < (r * 1.2) ** 2:
            return True
    if CORTE and X0C < x < X1C and y < 0.004:
        return True
    return False


bm = bmesh.new()
for _ in range(150000):
    x = random.uniform(-1.8, 8.8)
    y = random.uniform(-3.4, 3.8)
    d = mnoise.noise(Vector((x * 1.4, y * 1.4, 7.7)))
    if random.random() > 0.45 + 0.55 * d or excl(x, y):
        continue
    perto_borda = 0.0
    if XA < x < XB and abs(y) < 0.5:
        perto_borda = 0.3
    hh = random.uniform(0.025, 0.07) * (1.0 + 0.8 * max(d, 0) + perto_borda)
    yaw = random.uniform(0, 2 * PI)
    lean = random.uniform(0.1, 0.55)
    w = random.uniform(0.0022, 0.004)
    side = Vector((math.cos(yaw), math.sin(yaw), 0))
    fw = Vector((-side.y, side.x, 0))
    z0 = hmonte(x, y) if XA < x < XB and abs(y) < 0.44 else 0.0
    b0 = Vector((x, y, z0 - 0.004))
    m0 = b0 + Vector((0, 0, hh * 0.55)) + fw * hh * lean * 0.25
    t0 = b0 + Vector((0, 0, hh)) + fw * hh * lean
    v = [bm.verts.new(b0 - side * w), bm.verts.new(b0 + side * w), bm.verts.new(m0 + side * w * 0.7),
         bm.verts.new(m0 - side * w * 0.7), bm.verts.new(t0)]
    bm.faces.new(v[0:4])
    bm.faces.new((v[3], v[2], v[4]))
grama = obj('grama', bm, 'grama')
print('folhas de grama:', len(grama.data.polygons) // 2)

# ------------------------------------------------------------------ meia seção (corte em y = 0)
MANTER = ('pedras_corte', 'linha', 'reto', 'tampa_', 'manometro', 'mostrador', 'ponteiro', 'gota', 'vapor', 'enterrado', 'marco',
          'monte', 'aterro', 'fita_aviso', 'grama', 'solo', 'furo', 'respingo')
if CORTE:
    bm = bmesh.new()
    caixa_de(bm, (X0C, -40.0, -5.0), (X1C, 0.0, 3.0))
    me = bpy.data.meshes.new('cortador')
    bm.to_mesh(me)
    cortador = bpy.data.objects.new('cortador', me)
    sc.collection.objects.link(cortador)
    cortador.hide_render = True
    cortador.hide_viewport = True
    for o in list(sc.objects):
        if o.type != 'MESH' or o is cortador or o.name.startswith('furo'):
            continue
        if o.name.startswith(('poco', 'solo', 'placa')) or (o.name.startswith('reto') and o.name.endswith('_concreto')):
            md = o.modifiers.new('corte', 'BOOLEAN')
            md.operation = 'DIFFERENCE'
            md.object = cortador
            md.solver = 'EXACT'
            if o.name.startswith('poco'):
                md.use_self = True
                md.use_hole_tolerant = True
        elif not o.name.startswith(MANTER):
            cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
            cen = sum(cs, Vector()) / 8
            if X0C < cen.x < X1C and cen.y < 0.0:
                bpy.data.objects.remove(o)

# gotas (as de estudo_canos e as daqui) e vapor do respiro
for p, mat, vezes, fase in GOTAS:
    GOT.append((p, mat, vezes, fase, 0.0))
gotas = []
for p, mat, vezes, fase, zc in GOT:
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.011)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.z *= 1.7
    o = suavizar(obj('gota', bm, mat))
    gotas.append((o, p, vezes, fase, zc))
vapores = []
for boca in RESPIROS:
    for k in range(5):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        vapores.append((obj('vapor', bm, 'vapor_r'), boca, k / 5))

# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    return x * x * (3 - 2 * x)


DUR = QUADROS / FPS
vio = base3d.M['violeta'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
bal = base3d.M['baliza'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    fase = FLUXO_K * fr - 0.25 * math.sin(2 * PI * 4 * fr) / (2 * PI) * 2
    for val in FASES:
        val.outputs[0].default_value = fase
        val.outputs[0].keyframe_insert('default_value', frame=q)
    for e, n, f0 in GAUGES:
        e.rotation_quaternion = n.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), f0 - 0.2 * math.sin(2 * PI * 4 * fr))
        e.keyframe_insert('rotation_quaternion', frame=q)
    vio.default_value = 7.0 + 4.0 * math.sin(2 * PI * 2 * fr) ** 2
    vio.keyframe_insert('default_value', frame=q)
    bal.default_value = 9.0 if (fr * 2) % 1.0 < 0.18 else 1.2
    bal.keyframe_insert('default_value', frame=q)
    for o, p, vezes, f0, zc in gotas:
        u = (vezes * fr + f0) % 1.0
        h = max(0.01, p.z - zc - 0.004)
        tq = math.sqrt(2 * h / 9.8) / (DUR / vezes)
        if u < 0.7:
            s = 0.25 + 0.75 * suave(u / 0.7)
            o.location = p - Z * 0.011 * s
            o.scale = (s, s, s)
        elif u < 0.7 + tq:
            t = (u - 0.7) * DUR / vezes
            o.location = p - Z * (0.011 + 4.9 * t * t)
            o.scale = (0.85, 0.85, 1.25)
        else:
            o.location = p - Z * 0.011
            o.scale = (0.05, 0.05, 0.05)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for o, boca, f0 in vapores:
        u = (f0 + fr * 2) % 1.0
        o.location = boca + Vector((0.05 * u, 0.04 * u, -0.03 + 0.6 * u * u + 0.1 * u))
        o.scale = [max(0.02, 0.025 + 0.13 * u)] * 3
        o.rotation_euler = (f0 * 7, u * 2, f0 * 3)
        o.hide_render = u > 0.92
        o.hide_viewport = o.hide_render
        for c in ('location', 'scale', 'rotation_euler', 'hide_render', 'hide_viewport'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects) + list(bpy.data.materials):
    ad = getattr(o, 'animation_data', None)
    if isinstance(o, bpy.types.Material):
        ad = o.node_tree.animation_data if o.node_tree else None
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: luz, céu, câmera
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


def foto(nome, pos, alvo, lente, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente
    sc.render.filepath = os.path.join(AQUI, nome)
    bpy.ops.render.render(write_still=True)


FOTOS = {
    'conjunto': ('cano_subterraneo_conjunto.png', (3.9, -5.9, 2.9), (3.5, 0.2, 0.1), 25, 1600, 1000),
    'perto': ('cano_subterraneo_perto.png', (0.42, -1.12, 1.95), (1.1, 0.03, 0.32), 29, 1400, 1000),
    'janela': ('cano_subterraneo_janela.png', (1.0, -0.5, 1.6), (1.15, 0.0, 0.5), 35, 1000, 800),
    'corte': ('cano_subterraneo_corte.png', (2.6, -5.1, 0.95), (3.5, 0.0, -0.42), 25, 1600, 900),
}
if MODO in ('foto', 'teste'):
    sc.cycles.samples = 128 if MODO == 'foto' else 24
    sc.frame_set(int(QUADROS * 0.66) + 1)
    for chave, (nome, pos, alvo, lente, rx, ry) in FOTOS.items():
        if (CORTE and chave != 'corte') or (not CORTE and chave == 'corte') or (chave == 'janela' and SO_UMA != 'janela'):
            continue
        if SO_UMA and not CORTE and chave != SO_UMA:
            continue
        if MODO == 'teste':
            rx, ry = rx // 2, ry // 2
        foto(nome, pos, alvo, lente, rx, ry)
print('SUBTERRANEO ok')
