"""Modelos do estudo de drones (PlanetaFactory): materiais, efeitos de shader (holograma, scan, máscara de solda),
os 3 drones (reparo, defesa, logístico) e a estação de drones 2×2. Usado por estudo_drones.py.
Convenção do drone: origem no centro do corpo, frente = +X, cima = +Z. Patins tocam o chão em z = -0,158."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
COL = [None]                 # coleção atual
MAPA = [None]                # função opcional chave → material (holograma do drone que nasce)
Z_PATIM = 0.158              # do centro do corpo até a base dos patins
R_DUTO_C = 0.27              # raio do centro dos dutos
R_DUTO = 0.105


# ------------------------------------------------------------------ utilidades
def colecao(nome):
    c = bpy.data.collections.new(nome)
    bpy.context.scene.collection.children.link(c)
    COL[0] = c
    return c


def mat(chave):
    m = base3d.M[chave]
    return MAPA[0](chave, m) if MAPA[0] else m


def peca(nome, bm, chave, pai=None, liso=False):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    (COL[0] or bpy.context.scene.collection).objects.link(o)
    o.data.materials.append(mat(chave))
    if pai is not None:
        o.parent = pai
    if liso:
        suavizar(o)
    return o


def vazio(nome, pai=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(nome, None)
    (COL[0] or bpy.context.scene.collection).objects.link(o)
    o.empty_display_size = 0.05
    o.parent = pai
    o.location = loc
    return o


def luz(nome, tipo, cor, energia, raio=0.05, pai=None, loc=(0, 0, 0)):
    d = bpy.data.lights.new(nome, tipo)
    d.color = cor
    d.energy = energia
    d.shadow_soft_size = raio
    o = bpy.data.objects.new(nome, d)
    (COL[0] or bpy.context.scene.collection).objects.link(o)
    o.parent = pai
    o.location = loc
    return o


def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, eixo=(0, 0, 1), nR=40, nr=10):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix()
    c = Vector(centro)
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(c + q @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def anel_aberto(bm, centro, r, h, eixo=(0, 0, 1), lados=32):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=lados, radius1=r, radius2=r, depth=h,
                          matrix=Matrix.Translation(centro) @ q)


def prisma(bm, c, r0, r1, z0, z1, n=6, ang0=PI / 6):
    """Prisma/tronco de n lados entre z0 (raio r0) e z1 (raio r1); vértice no ângulo ang0 (face plana na frente)."""
    c = Vector(c)
    b = [bm.verts.new(c + Vector((r0 * math.cos(ang0 + k * 2 * PI / n), r0 * math.sin(ang0 + k * 2 * PI / n), z0))) for k in range(n)]
    t = [bm.verts.new(c + Vector((r1 * math.cos(ang0 + k * 2 * PI / n), r1 * math.sin(ang0 + k * 2 * PI / n), z1))) for k in range(n)]
    bm.faces.new(list(reversed(b)))
    bm.faces.new(t)
    for k in range(n):
        bm.faces.new((b[k], b[(k + 1) % n], t[(k + 1) % n], t[k]))


def esfera(bm, c, r, seg=10, esc=(1, 1, 1)):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(4, seg // 2), radius=r,
                              matrix=Matrix.Translation(c) @ Matrix.Diagonal((*esc, 1)))


def parafuso(bm, p, normal, r=0.0055):
    cil(bm, Vector(p) + Vector(normal).normalized() * 0.002, r, 0.004, normal, lados=6)


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    b.inputs['Roughness'].default_value = 0.3
    return m


def forca_de(m):
    """Socket de força de emissão do material (Principled ou Emission)."""
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n.inputs['Emission Strength']
        if n.type == 'EMISSION':
            return n.inputs['Strength']


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.3, 0.06, 0.75, 1)
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = 0.4
    b.inputs['Emission Color'].default_value = (0.5, 0.16, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 1.6
    return m


def luz_aditiva(nome, cor, forca, gradiente=None):
    """Luz no ar (feixe, folha de laser, traçante): transparente + emissão; gradiente opcional no eixo local."""
    m = bpy.data.materials.new(nome)
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*cor, 1)
    em.inputs['Strength'].default_value = forca
    ad = no(nt, 'ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs['Surface'])
    if gradiente:
        eixo, a, b = gradiente
        tc = no(nt, 'ShaderNodeTexCoord')
        sp = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sp.inputs[0])
        mr = no(nt, 'ShaderNodeMapRange', **{'From Min': a, 'From Max': b})
        nt.links.new(sp.outputs[eixo], mr.inputs['Value'])
        mu = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        mu.inputs[1].default_value = forca
        nt.links.new(mr.outputs['Result'], mu.inputs[0])
        nt.links.new(mu.outputs[0], em.inputs['Strength'])
    return m


def grade_laser_mat(nome, cor, forca, passo=0.04):
    """Disco/folha com grade de linhas de laser (o resto transparente); linhas em x e y do objeto."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    tc = no(nt, 'ShaderNodeTexCoord')
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sp.inputs[0])
    linhas = []
    for ax in ('X', 'Y'):
        d = no(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = passo
        nt.links.new(sp.outputs[ax], d.inputs[0])
        f = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs[0], f.inputs[0])
        lt = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
        lt.inputs[1].default_value = 0.09
        nt.links.new(f.outputs[0], lt.inputs[0])
        linhas.append(lt.outputs[0])
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(linhas[0], mx.inputs[0])
    nt.links.new(linhas[1], mx.inputs[1])
    vl = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')            # some na borda do disco
    nt.links.new(tc.outputs['Object'], vl.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.85, 'From Max': 1.0, 'To Min': 1.0, 'To Max': 0.25})
    nt.links.new(vl.outputs['Value'], borda.inputs['Value'])
    tot = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(mx.outputs[0], tot.inputs[0])
    nt.links.new(borda.outputs['Result'], tot.inputs[1])
    base = no(nt, 'ShaderNodeMath', operation='ADD')                   # véu leve entre as linhas
    base.inputs[1].default_value = 0.06
    nt.links.new(tot.outputs[0], base.inputs[0])
    em = no(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*cor, 1)
    fz = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    fz.inputs[1].default_value = forca
    nt.links.new(base.outputs[0], fz.inputs[0])
    nt.links.new(fz.outputs[0], em.inputs['Strength'])
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    ad = no(nt, 'ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs['Surface'])
    return m


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


def _saida(nt):
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    return out, out.inputs['Surface'].links[0].from_socket


def _coord(nt, alvo):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.object = alvo
    sp = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sp.inputs[0])
    return sp


VERMELHO = (1.0, 0.025, 0.012)


def holografar(m, e_holo, e_solido):
    """Cópia do material com o nascimento por holograma: acima do plano e_holo só um fantasma de wireframe; entre
    e_solido e e_holo holograma vermelho (linhas de varredura, wireframe, frente brilhante); abaixo de e_solido a
    matéria real, com uma franja brilhante onde ela acabou de se solidificar."""
    m2 = m.copy()
    m2.name = m.name + ' (holo)'
    nt = m2.node_tree
    out, orig = _saida(nt)
    sh, ss = _coord(nt, e_holo), _coord(nt, e_solido)
    zh, zs = sh.outputs['Z'], ss.outputs['Z']
    escondido = _m(nt, 'GREATER_THAN', zh, 0.0)
    holo = _m(nt, 'GREATER_THAN', zs, 0.0)
    wf = nt.nodes.new('ShaderNodeWireframe')
    wf.use_pixel_size = False
    wf.inputs['Size'].default_value = 0.0014
    fio = wf.outputs['Fac']
    linha = _m(nt, 'GREATER_THAN', _m(nt, 'SINE', _m(nt, 'MULTIPLY', zh, 480.0)), 0.6)
    frente = _m(nt, 'SUBTRACT', 1.0, _m(nt, 'DIVIDE', _m(nt, 'ABSOLUTE', zh), 0.014), clamp=True)
    franja = _m(nt, 'SUBTRACT', 1.0, _m(nt, 'DIVIDE', _m(nt, 'ABSOLUTE', zs), 0.01), clamp=True)
    # holograma
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.35
    borda = lw.outputs['Facing']
    f_h = _m(nt, 'ADD', _m(nt, 'ADD', 0.9, _m(nt, 'MULTIPLY', linha, 1.6)),
             _m(nt, 'ADD', _m(nt, 'ADD', _m(nt, 'MULTIPLY', fio, 2.0), _m(nt, 'MULTIPLY', borda, 2.8)), _m(nt, 'MULTIPLY', frente, 10.0)))
    em_h = nt.nodes.new('ShaderNodeEmission')
    em_h.inputs['Color'].default_value = (*VERMELHO, 1)
    nt.links.new(f_h, em_h.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix_h = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(_m(nt, 'ADD', _m(nt, 'ADD', 0.55, _m(nt, 'MULTIPLY', fio, 0.35)), _m(nt, 'ADD', frente, _m(nt, 'MULTIPLY', borda, 0.35)), clamp=True), mix_h.inputs[0])
    nt.links.new(tr.outputs[0], mix_h.inputs[1])
    nt.links.new(em_h.outputs[0], mix_h.inputs[2])
    # fantasma (acima da frente): só wireframe fraco
    em_g = nt.nodes.new('ShaderNodeEmission')
    em_g.inputs['Color'].default_value = (*VERMELHO, 1)
    em_g.inputs['Strength'].default_value = 1.2
    mix_g = nt.nodes.new('ShaderNodeMixShader')
    mix_g.name = 'Fantasma_mix'
    nt.links.new(_m(nt, 'MULTIPLY', fio, 0.55), mix_g.inputs[0])
    tr2 = nt.nodes.new('ShaderNodeBsdfTransparent')
    nt.links.new(tr2.outputs[0], mix_g.inputs[1])
    nt.links.new(em_g.outputs[0], mix_g.inputs[2])
    # sólido + franja
    em_s = nt.nodes.new('ShaderNodeEmission')
    em_s.inputs['Color'].default_value = (*VERMELHO, 1)
    nt.links.new(_m(nt, 'MULTIPLY', franja, 10.0), em_s.inputs['Strength'])
    ad_s = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(orig, ad_s.inputs[0])
    nt.links.new(em_s.outputs[0], ad_s.inputs[1])
    m1 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(holo, m1.inputs[0])
    nt.links.new(ad_s.outputs[0], m1.inputs[1])
    nt.links.new(mix_h.outputs[0], m1.inputs[2])
    m2_ = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(escondido, m2_.inputs[0])
    nt.links.new(m1.outputs[0], m2_.inputs[1])
    nt.links.new(mix_g.outputs[0], m2_.inputs[2])
    nt.links.new(m2_.outputs[0], out.inputs['Surface'])
    return m2


def escanear(m, e_scan, passo=0.08):
    """Scan vermelho: faixa brilhante onde o plano e_scan corta a superfície + grade vermelha perto do plano."""
    m2 = m.copy()
    m2.name = m.name + ' (scan)'
    nt = m2.node_tree
    out, orig = _saida(nt)
    sp = _coord(nt, e_scan)
    z = sp.outputs['Z']
    faixa = _m(nt, 'SUBTRACT', 1.0, _m(nt, 'DIVIDE', _m(nt, 'ABSOLUTE', z), 0.012), clamp=True)
    linhas = []
    for ax in ('X', 'Y', 'Z'):
        f = _m(nt, 'FRACT', _m(nt, 'DIVIDE', sp.outputs[ax], passo))
        linhas.append(_m(nt, 'LESS_THAN', f, 0.05))
    g = _m(nt, 'MAXIMUM', _m(nt, 'MAXIMUM', linhas[0], linhas[1]), linhas[2])
    perto = _m(nt, 'POWER', _m(nt, 'SUBTRACT', 1.0, _m(nt, 'DIVIDE', _m(nt, 'ABSOLUTE', z), 0.2), clamp=True), 2.0)
    forca = _m(nt, 'ADD', _m(nt, 'MULTIPLY', faixa, 18.0), _m(nt, 'MULTIPLY', _m(nt, 'MULTIPLY', g, perto), 1.6))
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*VERMELHO, 1)
    nt.links.new(forca, em.inputs['Strength'])
    ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(orig, ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs['Surface'])
    return m2


def mascarar(m, alvo, eixo, mostrar_frente, brilho=None):
    """Mostra o material só de um lado do vazio `alvo` (eixo local): rachadura que some atrás da tocha, cordão de
    solda que aparece atrás dela (com brilho quente que esfria nos últimos 6 cm)."""
    m2 = m.copy()
    m2.name = m.name + ' (máscara)'
    nt = m2.node_tree
    out, orig = _saida(nt)
    sp = _coord(nt, alvo)
    x = sp.outputs[eixo]
    vis = _m(nt, 'GREATER_THAN', x, 0.0) if mostrar_frente else _m(nt, 'LESS_THAN', x, 0.0)
    src = orig
    if brilho:
        cor, forca = brilho
        q = _m(nt, 'SUBTRACT', 1.0, _m(nt, 'DIVIDE', _m(nt, 'ABSOLUTE', x), 0.07), clamp=True)
        q = _m(nt, 'POWER', q, 2.0)
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (*cor, 1)
        nt.links.new(_m(nt, 'MULTIPLY', q, forca), em.inputs['Strength'])
        ad = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(orig, ad.inputs[0])
        nt.links.new(em.outputs[0], ad.inputs[1])
        src = ad.outputs[0]
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(vis, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(src, mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m2


def borrao_mat(nome):
    """Disco de borrão da hélice: anéis concêntricos translúcidos; opacidade no nó 'Opacidade' (quadro-chave)."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    tc = no(nt, 'ShaderNodeTexCoord')
    vl = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], vl.inputs[0])
    an = no(nt, 'ShaderNodeMath', operation='SINE')
    mu = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    mu.inputs[1].default_value = 260.0
    nt.links.new(vl.outputs['Value'], mu.inputs[0])
    nt.links.new(mu.outputs[0], an.inputs[0])
    an2 = no(nt, 'ShaderNodeMapRange', **{'From Min': -1.0, 'From Max': 1.0, 'To Min': 0.45, 'To Max': 0.9})
    nt.links.new(an.outputs[0], an2.inputs['Value'])
    perfil = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.012, 'From Max': 0.03, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(vl.outputs['Value'], perfil.inputs['Value'])          # cubo aparece nítido
    op = no(nt, 'ShaderNodeValue')
    op.name = op.label = 'Opacidade'
    op.outputs[0].default_value = 0.0
    a1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(an2.outputs['Result'], a1.inputs[0])
    nt.links.new(perfil.outputs['Result'], a1.inputs[1])
    a2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(a1.outputs[0], a2.inputs[0])
    nt.links.new(op.outputs[0], a2.inputs[1])
    b = no(nt, 'ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.16, 0.16, 0.17, 1)
    b.inputs['Roughness'].default_value = 0.25
    tr = no(nt, 'ShaderNodeBsdfTransparent')
    mx = no(nt, 'ShaderNodeMixShader')
    nt.links.new(a2.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


def perigo_vermelho_mat():
    m = base3d.listras_mat()
    m.name = 'Listras vermelhas'
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.blend_type == 'MIX':
            n.inputs[7].default_value = (0.42, 0.03, 0.02, 1)
    return m


def rustico(m, poeira=0.7, lama=0.6, riscos=0.45, mossa=0.5, cor_poeira=(0.36, 0.31, 0.24)):
    """Camada de uso por cima do material: poeira assentada nas faces de cima, lama/graxa nas de baixo, riscos finos
    que mostram metal, mossas em relevo. Tudo procedural (normal do mundo + ruídos em coordenadas do objeto)."""
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None:
        return m
    no = mats.no
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
    # poeira (em cima) e lama (embaixo), com manchas
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
    # riscos: ruído esticado em duas direções → linhas finas
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
    # poeira e lama deixam fosco; risco deixa metálico
    if b.inputs['Roughness'].links:
        rs = b.inputs['Roughness'].links[0].from_socket
    else:
        rs = b.inputs['Roughness'].default_value
    nt.links.new(_m(nt, 'ADD', rs, _m(nt, 'MULTIPLY', _m(nt, 'ADD', f_po, f_la), 0.5)), b.inputs['Roughness'])
    if not b.inputs['Metallic'].links:
        nt.links.new(_m(nt, 'MAXIMUM', b.inputs['Metallic'].default_value, _m(nt, 'MULTIPLY', f_ri, 0.9)), b.inputs['Metallic'])
    # mossas e grão (relevo)
    bp = no(nt, 'ShaderNodeBump', **{'Strength': 0.12 * mossa, 'Distance': 0.02})
    nt.links.new(ruido(18.0, 4.0), bp.inputs['Height'])
    if b.inputs['Normal'].links:
        nt.links.new(b.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def digitos(bm, texto, origem, direita, cima, h=0.02, esp=0.0016):
    """Número de série em 7 segmentos (tinta de estêncil), no plano direita×cima."""
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
            if random.random() < 0.15:                                   # estêncil gasto: falta pedaço
                continue
            dd = b - a
            rot = Matrix((dd.normalized(), nrm.cross(dd.normalized()), nrm)).transposed()
            caixa(bm, (a + b) / 2, (dd.length + esp, esp * 1.8, 0.0006), rot)


def arco_tubo(bm, c, R, r, a0, a1, z=0.0, n=10):
    pts = [Vector(c) + Vector((math.cos(a0 + (a1 - a0) * i / n) * R, math.sin(a0 + (a1 - a0) * i / n) * R, z)) for i in range(n + 1)]
    mangueira(bm, pts, r)


def mola(bm, a, b, r, rf, voltas):
    a, b = Vector(a), Vector(b)
    eixo = (b - a)
    q = eixo.normalized().to_track_quat('Z', 'Y').to_matrix()
    n = voltas * 8
    pts = [a + eixo * (i / n) + q @ Vector((math.cos(i / 8 * 2 * PI) * r, math.sin(i / 8 * 2 * PI) * r, 0)) for i in range(n + 1)]
    mangueira(bm, pts, rf)


def criar_materiais():
    M = base3d.M
    M.update({
        'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, ferrugem=0.45, desgaste=1.0, sujeira=0.95),
        'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
        'casco': mats.material('Casco drone', (0.13, 0.135, 0.14), 0, 0.45, ferrugem=0.5, desgaste=1.0, sujeira=1.0),
        'chapa': mats.material('Chapa', (0.2, 0.2, 0.19), 1.0, 0.45, pintura=False, ferrugem=0.5, sujeira=0.9),
        'chapa_ferrugem': mats.material('Chapa remendo', (0.26, 0.2, 0.16), 1.0, 0.6, pintura=False, ferrugem=1.0, sujeira=1.0),
        'blindado': mats.material('Blindado', (0.075, 0.08, 0.07), 0, 0.5, ferrugem=0.5, desgaste=1.0, sujeira=1.0),
        'vermelho': mats.material('Tinta vermelha', (0.36, 0.035, 0.02), 0, 0.45, desgaste=0.9, sujeira=0.7),
        'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.6, sujeira=0.8, escovado=True),
        'ferro': mats.material('Ferro', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
        'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
        'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
        'borracha': mats.material('Borracha', (0.018, 0.018, 0.02), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
        'helice': mats.material('Hélice', (0.035, 0.035, 0.038), 0, 0.32, desgaste=0.5, sujeira=0.6),
        'motor': mats.material('Motor', (0.11, 0.11, 0.12), 1.0, 0.35, pintura=False, sujeira=0.7),
        'amarelo_gasto': mats.material('Amarelo gasto', (0.66, 0.43, 0.05), 0, 0.5, ferrugem=0.7, desgaste=1.0, sujeira=1.0),
        'placa_suja': mats.material('Placa suja', (0.4, 0.39, 0.38), 1.0, 0.5, pintura=False, ferrugem=0.8, sujeira=1.0, escovado=True),
        'adesivo': mats.material('Adesivo', (0.62, 0.6, 0.52), 0, 0.6, desgaste=1.0, sujeira=1.0),
        'tinta_preta': mats.material('Estêncil', (0.03, 0.03, 0.03), 0, 0.7, desgaste=1.0, sujeira=0.6),
        'cabo_v': mats.material('Cabo vermelho', (0.3, 0.03, 0.02), 0, 0.6, pintura=False, sujeira=0.8, desgaste=0.0),
        'cabo_a': mats.material('Cabo amarelo', (0.55, 0.38, 0.03), 0, 0.6, pintura=False, sujeira=0.8, desgaste=0.0),
        'placa_ferro': mats.material('Placa de ferro', (0.5, 0.5, 0.51), 1.0, 0.38, pintura=False, ferrugem=0.25, sujeira=0.4, escovado=True),
        'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
        'chao': mats.material('Chão', (0.23, 0.2, 0.16), 0, 0.92, sujeira=0.3, desgaste=0.0),
        'fuligem': mats.material('Fuligem', (0.02, 0.018, 0.016), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
        'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
        'solda': mats.material('Marca de solda', (0.16, 0.13, 0.12), 1.0, 0.6, pintura=False, sujeira=0.2, ferrugem=0.3),
        'queimado': mats.material('Queimado', (0.1, 0.085, 0.08), 1.0, 0.6, pintura=False, ferrugem=0.7, sujeira=1.0),
        'capim': mats.material('Capim', (0.2, 0.2, 0.07), 0, 0.7, pintura=False, sujeira=0.2, desgaste=0.0),
        'agua': emissivo('Água', (0.05, 0.12, 0.16), 0.0, base=(0.08, 0.14, 0.16)),
        'vidro': emissivo('Visor', (0.0, 0.0, 0.0), 0.0, base=(0.05, 0.06, 0.06)),
        'listras': base3d.listras_mat(),
        'listras_v': perigo_vermelho_mat(),
        'cristal': cristal_mat(),
        'lente': emissivo('Olho vermelho', (1.0, 0.03, 0.015), 14.0),
        'led_v': emissivo('LED vermelho', (1.0, 0.04, 0.02), 9.0),
        'led_a': emissivo('LED âmbar', (1.0, 0.36, 0.04), 7.0),
        'led_carga': emissivo('LED carga', (1.0, 0.36, 0.04), 0.0, base=(0.05, 0.03, 0.02)),
        'lampada': emissivo('Lâmpada pouso', (1.0, 0.3, 0.04), 6.0),
        'farol_v': emissivo('Lâmpada vermelha', (1.0, 0.03, 0.015), 9.0),
        'emissor': emissivo('Emissor', (1.0, 0.03, 0.015), 6.0),
        'arco': emissivo('Arco de solda', (0.85, 0.8, 1.0), 120.0),
        'faisca': emissivo('Faísca', (1.0, 0.28, 0.03), 22.0),
        'brasa': emissivo('Brasa', (1.0, 0.28, 0.03), 18.0),
        'tiro': emissivo('Traçante', (1.0, 0.02, 0.01), 25.0),
        'clarão': emissivo('Clarão', (1.0, 0.25, 0.05), 80.0),
        'rachadura': mats.material('Rachadura', (0.012, 0.01, 0.01), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
        'cordao': mats.material('Cordão de solda', (0.2, 0.17, 0.15), 1.0, 0.5, pintura=False, sujeira=0.2),
        'halo': luz_aditiva('Halo traçante', (1.0, 0.02, 0.01), 1.5),
        'feixe': luz_aditiva('Feixe holo', (1.0, 0.03, 0.015), 0.9, ('X', 0.0, 1.0)),
        'leque': luz_aditiva('Leque scan', (1.0, 0.03, 0.015), 0.8, ('X', 0.0, 1.0)),
        'laser': luz_aditiva('Laser mira', (1.0, 0.03, 0.015), 12.0),
        'grade_holo': grade_laser_mat('Grade holo', (1.0, 0.03, 0.015), 2.2, 0.035),
        'folha_scan': grade_laser_mat('Folha scan', (1.0, 0.03, 0.015), 2.5, 0.07),
        'mira': emissivo('Mira', (1.0, 0.03, 0.015), 10.0),
        'fumaca': base3d.volume_mat('Fumaça', (0.03, 0.03, 0.03), 9.0, -10.0, 10.0),
        'fumaca_fina': base3d.volume_mat('Fumaça fina', (0.07, 0.07, 0.07), 1.0, -10.0, 10.0),
        'fumaca_rastro': base3d.volume_mat('Fumaça rastro', (0.04, 0.04, 0.04), 6.0, -10.0, 10.0),
        'poeira': base3d.volume_mat('Poeira', (0.5, 0.43, 0.33), 22.0, -10.0, 10.0),
    })
    for k in ('amarelo', 'amarelo_gasto', 'grafite', 'casco', 'chapa', 'chapa_ferrugem', 'blindado', 'vermelho', 'aco',
              'ferro', 'motor', 'placa_ferro', 'placa_suja', 'adesivo', 'queimado', 'solda', 'cobre'):
        rustico(M[k])
    for k in ('helice', 'borracha', 'cabo_v', 'cabo_a', 'tinta_preta'):
        rustico(M[k], poeira=0.5, lama=0.4, riscos=0.25, mossa=0.2)
    rustico(M['concreto'], poeira=0.5, lama=0.3, riscos=0.0, mossa=1.0, cor_poeira=(0.3, 0.27, 0.22))


# ------------------------------------------------------------------ hélice com perfil e torção
def pa(bm, ang, sentido, z, r0=0.017, r1=0.088):
    """Uma pá com perfil (arqueado) e torção (passo maior na raiz). sentido ±1 = giro anti-horário/horário."""
    rot = Matrix.Rotation(ang, 3, 'Z')
    secoes = []
    N = 7
    for i in range(N):
        s = i / (N - 1)
        r = r0 + (r1 - r0) * s
        corda = 0.03 * (1 - s) + 0.015 * s + 0.006 * math.sin(PI * s)
        passo = 0.5 * (1 - s) + 0.17 * s
        esp = corda * 0.11
        pts = []
        for j in range(8):                                                 # ataque → fuga por cima, volta por baixo
            u = j / 7
            pts.append((corda * (u - 0.35), esp * math.sin(PI * u ** 0.7) + corda * 0.05 * math.sin(PI * u)))
        for j in range(6, 0, -1):
            u = j / 7
            pts.append((corda * (u - 0.35), -esp * 0.25 * math.sin(PI * u) + corda * 0.05 * math.sin(PI * u)))
        q = Matrix.Rotation(-passo * sentido, 3, 'X')
        anel = []
        for (y, zz) in pts:
            p = q @ Vector((0, -y * sentido, zz))                          # bordo de ataque na direção do giro
            anel.append(bm.verts.new(rot @ Vector((r, p.y, p.z)) + Vector((0, 0, z))))
        secoes.append(anel)
    n = len(secoes[0])
    for a, b in zip(secoes, secoes[1:]):
        for j in range(n):
            bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
    bm.faces.new(list(reversed(secoes[0])))
    bm.faces.new(secoes[-1])


# ------------------------------------------------------------------ drone
def drone(tipo, nome, amassar=0.0):
    """Monta um drone ('reparo', 'defesa', 'logistico'). Devolve dict com raiz, rotores (vazios), dutos, discos e
    as articulações do tipo. Peças separadas e pivôs nomeados como no jogo."""
    random.seed(hash(nome) % 1000)
    raiz = vazio(nome)
    raiz.rotation_mode = 'QUATERNION'
    D = {'raiz': raiz, 'tipo': tipo, 'rotores': [], 'dutos': [], 'discos': [], 'pas': [], 'leds': []}
    casco = {'reparo': 'casco', 'defesa': 'blindado', 'logistico': 'amarelo'}[tipo]
    R, AP = 0.15, 0.15 * math.cos(PI / 6)

    # corpo hexagonal: miolo, tronco de cima e de baixo, tampas
    bm = bmesh.new()
    prisma(bm, (0, 0, 0), R, R, -0.04, 0.04)
    prisma(bm, (0, 0, 0), R, 0.115, 0.04, 0.065)
    prisma(bm, (0, 0, 0), 0.12, R, -0.06, -0.04)
    peca(nome + '_corpo', bm, casco, raiz)
    bm = bmesh.new()
    prisma(bm, (0, 0, 0), 0.118, 0.118, 0.065, 0.071)
    prisma(bm, (0, 0, 0), 0.122, 0.122, -0.066, -0.06)
    peca(nome + '_tampas', bm, 'grafite' if tipo != 'logistico' else 'casco', raiz)

    # chapas aparafusadas nas faces (frente tem o olho, trás a bateria)
    chapas = {'reparo': ['amarelo', 'chapa', 'chapa_ferrugem', 'amarelo'],
              'defesa': ['blindado', 'vermelho', 'blindado', 'chapa'],
              'logistico': ['chapa', 'amarelo', 'chapa_ferrugem', 'chapa']}[tipo]
    bmp = bmesh.new()
    for i, k in enumerate((1, 2, 4, 5)):
        fi = k * PI / 3
        rot = Matrix.Rotation(fi, 3, 'Z')
        n = rot @ Vector((1, 0, 0))
        t = rot @ Vector((0, 1, 0))
        esp = 0.014 if tipo == 'defesa' else 0.007
        bm = bmesh.new()
        c = n * (AP + esp / 2) + Vector((0, 0, random.uniform(-0.003, 0.003)))
        caixa(bm, c, (esp, 0.118, 0.066), rot @ Matrix.Rotation(random.uniform(-0.03, 0.03), 3, 'X'))
        if tipo == 'defesa':                                           # saia blindada inclinada por baixo
            caixa(bm, n * (AP + 0.012) + Vector((0, 0, -0.05)), (0.012, 0.13, 0.04), rot @ Matrix.Rotation(-0.45, 3, 'Y'))
        peca(nome + '_chapa%d' % k, bm, chapas[i], raiz)
        for sx in (-1, 1):
            for sz in (-1, 1):
                parafuso(bmp, n * (AP + esp) + t * sx * 0.05 + Vector((0, 0, sz * 0.025)), n)
        if k == 2 and tipo != 'defesa':                                # cordão de solda de um remendo antigo
            bms = bmesh.new()
            for j in range(9):
                esfera(bms, n * (AP + esp + 0.001) + t * (-0.055 + j * 0.0137) + Vector((0, 0, 0.036)), 0.004, 6, (1.4, 1, 0.6))
            peca(nome + '_cordao', bms, 'solda', raiz)
    for j in range(12):                                                # parafusos da tampa
        a = j * PI / 6 + 0.1
        parafuso(bmp, Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.071)), (0, 0, 1), 0.005)
    peca(nome + '_parafusos', bmp, 'aco', raiz)

    # marcas: fuligem de solda por baixo, riscos
    bm = bmesh.new()
    for j in range(4):
        a = random.uniform(0, 2 * PI)
        res = bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=random.uniform(0.012, 0.025))
        for v in res['verts']:
            v.co = Vector((math.cos(a) * 0.07 + v.co.x * random.uniform(0.6, 1.3), math.sin(a) * 0.07 + v.co.y, -0.0665))
    peca(nome + '_fuligem', bm, 'fuligem', raiz)

    # núcleo de cristal com colar e garras
    bm = bmesh.new()
    prisma(bm, (0, 0, 0), 0.026, 0.026, 0.075, 0.13, 6, 0)
    v_top = bm.verts.new((0, 0, 0.17))
    vs = [v for v in bm.verts if abs(v.co.z - 0.13) < 1e-6]
    vs.sort(key=lambda v: math.atan2(v.co.y, v.co.x))
    for j in range(6):
        bm.faces.new((vs[j], vs[(j + 1) % 6], v_top))
    cr = peca(nome + '_cristal', bm, 'cristal', raiz)
    bm = bmesh.new()
    toro(bm, (0, 0, 0.078), 0.034, 0.008, nR=24, nr=8)
    for j in range(3):
        a = j * 2 * PI / 3 + PI / 6
        d = Vector((math.cos(a), math.sin(a), 0))
        viga(bm, d * 0.036 + Vector((0, 0, 0.082)), d * 0.027 + Vector((0, 0, 0.122)), 0.007)
    peca(nome + '_colar', bm, 'cobre', raiz, liso=True)
    D['cristal'] = cr
    luz(nome + '_luz_cristal', 'POINT', (0.55, 0.2, 1.0), 0.6, 0.02, raiz, (0, 0, 0.12))

    # olho sensor (frente)
    bm = bmesh.new()
    cil(bm, Vector((AP + 0.012, 0, 0.0)), 0.031, 0.04, Vector((1, 0, 0)), lados=20)
    for sy in (-1, 1):
        cil(bm, Vector((AP + 0.006, sy * 0.05, 0.022)), 0.009, 0.02, Vector((1, 0, 0)), lados=10)
    peca(nome + '_olho_casa', bm, 'grafite', raiz, liso=True)
    bm = bmesh.new()
    toro(bm, Vector((AP + 0.032, 0, 0)), 0.026, 0.005, (1, 0, 0), 24, 8)
    peca(nome + '_olho_aro', bm, 'cromo', raiz, liso=True)
    bm = bmesh.new()
    cil(bm, Vector((AP + 0.031, 0, 0)), 0.021, 0.004, Vector((1, 0, 0)), lados=20)
    for sy in (-1, 1):
        cil(bm, Vector((AP + 0.0165, sy * 0.05, 0.022)), 0.006, 0.002, Vector((1, 0, 0)), lados=10)
    D['olho'] = peca(nome + '_olho', bm, 'lente', raiz)
    if tipo == 'defesa':                                               # viseira blindada com fenda
        bm = bmesh.new()
        caixa(bm, (AP + 0.04, 0, 0.034), (0.04, 0.1, 0.028), Matrix.Rotation(0.35, 3, 'Y'))
        caixa(bm, (AP + 0.036, 0, -0.033), (0.034, 0.1, 0.022), Matrix.Rotation(-0.3, 3, 'Y'))
        for sy in (-1, 1):
            caixa(bm, (AP + 0.03, sy * 0.052, 0), (0.04, 0.012, 0.09))
        peca(nome + '_viseira', bm, 'blindado', raiz)
    else:
        bm = bmesh.new()
        caixa(bm, (AP + 0.026, 0, 0.036), (0.036, 0.075, 0.008), Matrix.Rotation(0.25, 3, 'Y'))   # pala
        peca(nome + '_pala', bm, 'grafite', raiz)

    # bateria encaixada (trás) com trilhos, alça e barra de carga
    bat = 0.08 if tipo == 'logistico' else 0.065
    bm = bmesh.new()
    caixa_de(bm, (-AP - bat, -0.042, -0.03), (-AP + 0.004, 0.042, 0.03))
    peca(nome + '_bateria', bm, 'grafite', raiz)
    bm = bmesh.new()
    for sy in (-1, 1):
        caixa_de(bm, (-AP - 0.03, sy * 0.044 - 0.004, -0.034), (-AP + 0.004, sy * 0.044 + 0.004, 0.034))   # trilhos
    tubo(bm, (-AP - bat - 0.004, -0.025, 0.012), (-AP - bat - 0.004, 0.025, 0.012), 0.004, 8)
    for sy in (-1, 1):
        tubo(bm, (-AP - bat + 0.003, sy * 0.025, 0.012), (-AP - bat - 0.006, sy * 0.025, 0.012), 0.004, 8)
    cil(bm, Vector((-AP - bat - 0.001, 0, -0.015)), 0.01, 0.006, Vector((1, 0, 0)), lados=10)   # tomada de carga
    peca(nome + '_trilhos', bm, 'aco', raiz)
    bm = bmesh.new()
    caixa_de(bm, (-AP - bat + 0.006, -0.042, 0.018), (-AP - bat * 0.4, 0.042, 0.03))
    peca(nome + '_bat_faixa', bm, 'listras', raiz)
    leds = []
    for j in range(4):
        bm = bmesh.new()
        caixa(bm, (-AP - bat * 0.55, -0.027 + j * 0.018, 0.0305), (0.01, 0.012, 0.002))
        m = mat('led_carga').copy()
        m.name = '%s carga %d' % (nome, j)
        o = peca(nome + '_led_carga%d' % j, bm, 'led_carga', raiz)
        o.data.materials[0] = m
        leds.append(m)
    D['led_carga'] = leds

    # antenas e LEDs
    bm, bl = bmesh.new(), bmesh.new()
    for sy in (-1, 1):
        b0 = Vector((-0.02, sy * 0.082, 0.071))
        cil(bm, b0 + Vector((0, 0, 0.006)), 0.008, 0.012, lados=8)
        meio = b0 + Vector((-0.02, sy * 0.008, 0.07))
        topo = meio + Vector((-0.06, sy * (0.03 if sy > 0 else 0.05), 0.06 if sy > 0 else 0.02))   # uma entortada
        tubo(bm, b0, meio, 0.0028, 6)
        tubo(bm, meio, topo, 0.0022, 6)
        esfera(bm, meio, 0.0035, 6)
        esfera(bl, topo, 0.006, 8)
    peca(nome + '_antenas', bm, 'aco', raiz)
    D['leds'].append(peca(nome + '_led_antena', bl, 'led_v', raiz))

    # braços até os dutos, dutos com grade, motor brushless e hélices
    bmb, bmd, bmg, bmm, bml_a, bml_v, bmc = (bmesh.new() for _ in range(7))
    for k in range(4):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        lat = Vector((-d.y, d.x, 0))
        C = d * R_DUTO_C
        rot = Matrix.Rotation(a, 3, 'Z')
        caixa(bmb, d * 0.14, (0.085, 0.044 if tipo != 'defesa' else 0.052, 0.03), rot)       # braço
        caixa(bmb, d * 0.104, (0.012, 0.06, 0.044), rot)                    # colar no corpo
        caixa(bmb, C - d * (R_DUTO + 0.004), (0.01, 0.06, 0.05), rot)       # flange no duto
        for sz in (-1, 1):
            parafuso(bmb, C - d * (R_DUTO + 0.009) + lat * 0.02 + Vector((0, 0, sz * 0.016)), -d, 0.004)
            parafuso(bmb, C - d * (R_DUTO + 0.009) - lat * 0.02 + Vector((0, 0, sz * 0.016)), -d, 0.004)
        # cabo do motor por cima do braço, presilhas
        p0, p1 = d * 0.11 + Vector((0, 0, 0.018)), C - d * (R_DUTO + 0.004) + Vector((0, 0, 0.022))
        mangueira(bmc, bezier(p0, p0 + Vector((0, 0, 0.012)), p1 + Vector((0, 0, 0.01)), p1, 6), 0.0045)
        caixa(bmb, d * 0.15 + Vector((0, 0, 0.018)), (0.008, 0.016, 0.01), rot)
        # duto: dois cascos e bordas
        bm = bmesh.new()
        anel_aberto(bm, C, R_DUTO, 0.06, lados=36)
        anel_aberto(bm, C, R_DUTO - 0.011, 0.06, lados=36)
        toro(bm, C + Vector((0, 0, 0.03)), R_DUTO - 0.0055, 0.0058, nR=36, nr=8)
        toro(bm, C + Vector((0, 0, -0.03)), R_DUTO - 0.0055, 0.0058, nR=36, nr=8)
        if tipo == 'defesa':
            toro(bm, C + Vector((0, 0, 0.0)), R_DUTO + 0.004, 0.006, nR=36, nr=8)
        for j in range(16):                                            # rebites na cinta do duto
            aa = j * 2 * PI / 16
            dd = Vector((math.cos(aa), math.sin(aa), 0))
            if dd.dot(-d) < 0.9:
                parafuso(bmb, C + dd * (R_DUTO + 0.0), dd, 0.0035)
        cor_duto = casco if tipo != 'reparo' else ('amarelo' if k % 2 == 0 else 'casco')
        if k == 3:                                                     # peça trocada de outro drone
            cor_duto = {'reparo': 'vermelho', 'defesa': 'amarelo_gasto', 'logistico': 'casco'}[tipo]
        duto = peca(nome + '_duto%d' % k, bm, cor_duto, raiz, liso=True)
        bm = bmesh.new()                                               # para-choques de borracha gastos (lado de fora)
        for (a0, a1) in ((a - 1.25, a - 0.35), (a - 0.2, a + 0.2), (a + 0.35, a + 1.25)):
            arco_tubo(bm, C, R_DUTO + 0.007, 0.0065, a0, a1, 0.0, 8)
        peca(nome + '_parachoque%d' % k, bm, 'borracha', raiz, liso=True)
        D['dutos'].append(duto)
        # grade de proteção por cima (acima das pás) e suportes do motor por baixo
        bm = bmesh.new()
        toro(bm, C + Vector((0, 0, 0.037)), 0.062, 0.0022, nR=28, nr=6)
        for j in range(4):
            aa = a + j * PI / 2
            dd = Vector((math.cos(aa), math.sin(aa), 0))
            tubo(bm, C + dd * 0.014 + Vector((0, 0, 0.037)), C + dd * (R_DUTO - 0.006) + Vector((0, 0, 0.033)), 0.0022, 6)
        cil(bm, C + Vector((0, 0, 0.037)), 0.016, 0.003, lados=12)
        for j in range(3):
            aa = a + PI / 3 + j * 2 * PI / 3
            dd = Vector((math.cos(aa), math.sin(aa), 0))
            caixa(bm, C + dd * 0.058 + Vector((0, 0, -0.024)), (0.072, 0.008, 0.006), Matrix.Rotation(aa, 3, 'Z'))
        peca(nome + '_grade%d' % k, bm, 'ferro', raiz, liso=True)
        # motor brushless (estator com aletas, fixo)
        cil(bmm, C + Vector((0, 0, -0.018)), 0.02, 0.026, lados=18)
        for j in range(12):
            aa = j * PI / 6
            dd = Vector((math.cos(aa), math.sin(aa), 0))
            caixa(bmm, C + dd * 0.022 + Vector((0, 0, -0.02)), (0.006, 0.0018, 0.02), Matrix.Rotation(aa, 3, 'Z'))
        # LED de navegação: âmbar na frente, vermelho atrás
        alvo = bml_a if d.x > 0 else bml_v
        caixa(alvo, C + d * (R_DUTO + 0.003), (0.004, 0.014, 0.008), rot)
        # rotor (gira): sino do motor, cubo, pás; sentidos opostos nas diagonais
        sent = 1 if k % 2 == 0 else -1
        ro = vazio(nome + '_rotor%d' % k, raiz, C)
        ro.rotation_mode = 'XYZ'
        ro['sentido'] = sent
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.0)), 0.021, 0.012, lados=18)
        cil(bm, Vector((0, 0, 0.0095)), 0.012, 0.007, lados=12)
        cil(bm, Vector((0, 0, 0.016)), 0.006, 0.006, lados=8)
        peca(nome + '_sino%d' % k, bm, 'motor', ro, liso=True)
        bm = bmesh.new()
        for j in range(3):
            pa(bm, j * 2 * PI / 3, sent, 0.0105)
        D['pas'].append(peca(nome + '_pas%d' % k, bm, 'helice', ro))
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=0.09)
        for v in bm.verts:
            v.co.z = 0.011
        disco = peca(nome + '_borrao%d' % k, bm, 'helice', ro)
        D['discos'].append(disco)
        D['rotores'].append(ro)
    peca(nome + '_bracos', bmb, casco if tipo != 'reparo' else 'grafite', raiz)
    peca(nome + '_cabos', bmc, 'borracha', raiz, liso=True)
    peca(nome + '_motores', bmm, 'motor', raiz, liso=True)
    D['leds'].append(peca(nome + '_led_frente', bml_a, 'led_a', raiz))
    D['leds'].append(peca(nome + '_led_tras', bml_v, 'led_v', raiz))
    bm_ = borrao_mat(nome + ' borrão')
    if MAPA[0]:
        bm_ = MAPA[0]('borrao', bm_)
    for o in D['discos']:
        o.data.materials[0] = bm_
    D['borrao'] = bm_

    # patins de pouso com contatos de carga, amortecedores de mola e sapatas
    bm, bc, bam, bcr, bmo, bsp = (bmesh.new() for _ in range(6))
    for sy in (-1, 1):
        y = sy * 0.085
        tubo(bm, (-0.12, y, -0.15), (0.12, y, -0.15), 0.008, 10)
        for sx in (-1, 1):
            tubo(bm, (sx * 0.12, y, -0.15), (sx * 0.145, y, -0.132), 0.008, 10)
            esfera(bm, Vector((sx * 0.12, y, -0.15)), 0.008, 10)
            a_ = Vector((sx * 0.05, sy * 0.07, -0.062))
            b_ = Vector((sx * 0.07, y, -0.15))
            m_ = a_ + (b_ - a_) * 0.55
            cil(bam, (a_ + m_) / 2, 0.009, (m_ - a_).length, m_ - a_, lados=10)        # camisa do amortecedor
            tubo(bcr, m_ - (b_ - a_) * 0.05, b_, 0.0045, 8)                            # haste
            mola(bmo, a_ + (b_ - a_) * 0.12, b_ - (b_ - a_) * 0.05, 0.0125, 0.0018, 7)
            caixa(bsp, Vector((sx * 0.105, y, -0.1595)), (0.04, 0.022, 0.006))      # sapata gasta
        caixa(bc, (0, y, -0.1575), (0.04, 0.012, 0.004))
    peca(nome + '_patins', bm, 'aco', raiz, liso=True)
    peca(nome + '_amortecedores', bam, 'grafite', raiz, liso=True)
    peca(nome + '_hastes', bcr, 'cromo', raiz, liso=True)
    peca(nome + '_molas', bmo, 'amarelo' if tipo != 'defesa' else 'vermelho', raiz, liso=True)
    peca(nome + '_sapatas', bsp, 'borracha', raiz)
    peca(nome + '_contatos', bc, 'cobre', raiz)

    # ---------------------------------------------------------- equipamento de cada tipo
    if tipo == 'reparo':
        # funil de placas (recebe remendos da estação), atrás do cristal
        bm = bmesh.new()
        caixa_de(bm, (-0.098, -0.045, 0.071), (-0.046, 0.045, 0.075))
        for sy in (-1, 1):
            caixa_de(bm, (-0.098, sy * 0.045 - 0.003, 0.071), (-0.046, sy * 0.045 + 0.003, 0.1))
        for x in (-0.098, -0.046):
            caixa_de(bm, (x - 0.003, -0.045, 0.071), (x + 0.003, 0.045, 0.1))
        peca(nome + '_funil', bm, 'amarelo', raiz)
        bm = bmesh.new()
        for j in range(2):
            caixa(bm, (-0.072, 0, 0.078 + j * 0.009), (0.046, 0.075, 0.007), Matrix.Rotation(0.05 * j, 3, 'Z'))
        D['remendos'] = peca(nome + '_remendos', bm, 'placa_ferro', raiz)
        # braço de solda articulado: giro → ombro → cotovelo → tocha, com pistões e mangueira
        giro = vazio(nome + '_braco_giro', raiz, (0.035, 0, -0.066))
        bm = bmesh.new()
        cil(bm, Vector((0, 0, -0.008)), 0.026, 0.016, lados=16)
        caixa(bm, (0, 0, -0.024), (0.03, 0.04, 0.018))
        for sy in (-1, 1):
            caixa(bm, (0, sy * 0.016, -0.032), (0.022, 0.006, 0.026))         # garfo do ombro
        caixa(bm, (-0.026, 0, -0.02), (0.012, 0.016, 0.014))                   # olhal do pistão
        peca(nome + '_braco_base', bm, 'grafite', giro, liso=True)
        ombro = vazio(nome + '_ombro', giro, (0, 0, -0.034))
        bm = bmesh.new()
        caixa_de(bm, (0.0, -0.01, -0.009), (0.11, 0.01, 0.009))
        cil(bm, Vector((0, 0, 0)), 0.011, 0.026, Vector((0, 1, 0)), lados=12)
        for sy in (-1, 1):
            caixa_de(bm, (0.095, sy * 0.012 - 0.003, -0.012), (0.12, sy * 0.012 + 0.003, 0.012))   # garfo do cotovelo
        caixa(bm, (0.05, 0, 0.013), (0.012, 0.012, 0.008))                     # olhal pistão ombro
        caixa(bm, (0.02, 0, -0.013), (0.012, 0.012, 0.008))                    # olhal pistão cotovelo
        peca(nome + '_braco_sup', bm, 'amarelo', ombro, liso=True)
        cotovelo = vazio(nome + '_cotovelo', ombro, (0.11, 0, 0))
        bm = bmesh.new()
        caixa_de(bm, (0.0, -0.008, -0.007), (0.085, 0.008, 0.007))
        cil(bm, Vector((0, 0, 0)), 0.009, 0.03, Vector((0, 1, 0)), lados=12)
        caixa(bm, (0.035, 0, -0.011), (0.01, 0.01, 0.007))
        peca(nome + '_braco_ant', bm, 'amarelo', cotovelo, liso=True)
        bm = bmesh.new()
        cil(bm, Vector((0.095, 0, 0)), 0.011, 0.024, Vector((1, 0, 0)), lados=12)
        cil(bm, Vector((0.117, 0, 0)), 0.0065, 0.024, Vector((1, 0, 0)), lados=12, r2=0.0035)
        peca(nome + '_tocha', bm, 'cobre', cotovelo, liso=True)
        bm = bmesh.new()
        cil(bm, Vector((0.07, 0, 0)), 0.0105, 0.03, Vector((1, 0, 0)), lados=12)
        peca(nome + '_tocha_queimado', bm, 'queimado', cotovelo, liso=True)
        bm = bmesh.new()
        for j in range(6):
            esfera(bm, Vector((0.02 + j * 0.01, 0.0085, 0.004 * math.sin(j))), 0.0028, 6, (1.3, 0.6, 1))
        for j in range(5):
            esfera(bm, Vector((0.104 + j * 0.0004, -0.011 + j * 0.005, 0.0)), 0.0026, 6)
        peca(nome + '_marcas_solda', bm, 'solda', cotovelo)
        bm = bmesh.new()
        esfera(bm, Vector((0.131, 0, 0)), 0.006, 10)
        D['arco'] = peca(nome + '_arco', bm, 'arco', cotovelo)
        D['luz_arco'] = luz(nome + '_luz_arco', 'POINT', (0.8, 0.75, 1.0), 0.0, 0.01, cotovelo, (0.14, 0, 0))
        bm = bmesh.new()                                                       # mangueira do gás até a tocha
        mangueira(bm, bezier((-0.01, 0.012, 0.0), (0.03, 0.02, 0.012), (0.08, 0.018, 0.01), (0.09, 0.012, 0.004), 6), 0.0035)
        peca(nome + '_mangueira', bm, 'borracha', cotovelo, liso=True)
        # pistões: camisa (presa num lado) e haste (no outro); orientados a cada quadro
        pis = []
        for nomep, pai in (('pistao_ombro', giro), ('pistao_cotovelo', ombro)):
            cam_o = vazio(nome + '_' + nomep + '_camisa', pai)
            cam_o.rotation_mode = 'QUATERNION'
            bm = bmesh.new()
            cil(bm, Vector((0, 0, 0.022)), 0.0062, 0.044, lados=10)
            peca(nome + '_' + nomep + '_c', bm, 'grafite', cam_o, liso=True)
            has_o = vazio(nome + '_' + nomep + '_haste', pai)
            has_o.rotation_mode = 'QUATERNION'
            bm = bmesh.new()
            cil(bm, Vector((0, 0, 0.024)), 0.0034, 0.048, lados=8)
            peca(nome + '_' + nomep + '_h', bm, 'cromo', has_o, liso=True)
            pis.append((cam_o, has_o))
        D.update(giro=giro, ombro=ombro, cotovelo=cotovelo, pistoes=pis)

    if tipo == 'defesa':
        # torre giratória embaixo com canhão duplo de pulso
        torre = vazio(nome + '_torre', raiz, (0, 0, -0.066))
        torre.rotation_mode = 'XYZ'
        bm = bmesh.new()
        cil(bm, Vector((0, 0, -0.006)), 0.05, 0.012, lados=24)
        prisma(bm, (0, 0, 0), 0.045, 0.035, -0.012, -0.055, 8, PI / 8)
        for sy in (-1, 1):
            caixa(bm, (0.0, sy * 0.04, -0.045), (0.035, 0.01, 0.04))
        peca(nome + '_torre_casa', bm, 'blindado', torre)
        bm = bmesh.new()
        caixa(bm, (-0.035, 0.0, -0.035), (0.02, 0.05, 0.03))                   # célula de energia
        mangueira(bm, bezier((-0.04, 0.02, -0.02), (-0.06, 0.03, 0.0), (-0.05, 0.03, 0.01), (-0.03, 0.03, 0.006), 5), 0.004)
        peca(nome + '_torre_celula', bm, 'grafite', torre)
        pitch = vazio(nome + '_canhao', torre, (0.0, 0, -0.045))
        pitch.rotation_mode = 'XYZ'
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0)), 0.016, 0.07, Vector((0, 1, 0)), lados=14)
        caixa_de(bm, (-0.02, -0.03, -0.016), (0.05, 0.03, 0.016))
        peca(nome + '_culatra', bm, 'grafite', pitch, liso=True)
        bm = bmesh.new()
        for sy in (-1, 1):
            cil(bm, Vector((0.11, sy * 0.014, 0)), 0.0075, 0.14, Vector((1, 0, 0)), lados=12)
            cil(bm, Vector((0.17, sy * 0.014, 0)), 0.0105, 0.022, Vector((1, 0, 0)), lados=12)   # freio de boca
            for j in range(3):
                cil(bm, Vector((0.07 + j * 0.025, sy * 0.014, 0)), 0.0105, 0.006, Vector((1, 0, 0)), lados=12)   # aletas
        peca(nome + '_canos', bm, 'queimado', pitch, liso=True)
        bm = bmesh.new()
        for sy in (-1, 1):
            cil(bm, Vector((0.176, sy * 0.014, 0)), 0.0108, 0.012, Vector((1, 0, 0)), lados=12)
        peca(nome + '_boca_fuligem', bm, 'fuligem', pitch, liso=True)
        bm = bmesh.new()                                                       # janela de ejeção das cápsulas
        caixa(bm, (0.03, -0.032, 0.004), (0.03, 0.004, 0.012))
        peca(nome + '_ejecao', bm, 'tinta_preta', pitch)
        bm = bmesh.new()
        for sy in (-1, 1):
            toro(bm, Vector((0.158, sy * 0.014, 0)), 0.0085, 0.0018, (1, 0, 0), 16, 6)
        D['emissor'] = peca(nome + '_emissores', bm, 'emissor', pitch)
        bm = bmesh.new()                                                       # clarão de boca (estrela)
        for sy in (-1, 1):
            for j in range(6):
                aa = j * PI / 3
                dd = Vector((0, math.cos(aa), math.sin(aa)))
                tubo(bm, Vector((0.185, sy * 0.014, 0)), Vector((0.185, sy * 0.014, 0)) + dd * 0.035 + Vector((0.01, 0, 0)), 0.003, 4)
            cil(bm, Vector((0.2, sy * 0.014, 0)), 0.012, 0.04, Vector((1, 0, 0)), lados=8, r2=0.002)
        D['flash'] = peca(nome + '_clarao', bm, 'clarão', pitch)
        D['luz_flash'] = luz(nome + '_luz_tiro', 'POINT', (1.0, 0.15, 0.05), 0.0, 0.02, pitch, (0.2, 0, 0))
        D['muzzle'] = [Vector((0.185, -0.014, 0)), Vector((0.185, 0.014, 0))]
        D.update(torre=torre, canhao=pitch)
        bm = bmesh.new()                                                       # faixas de perigo vermelhas
        for k in (1, 5):
            fi = k * PI / 3
            rot = Matrix.Rotation(fi, 3, 'Z')
            caixa(bm, rot @ Vector((AP + 0.0145, 0, 0.02)), (0.002, 0.11, 0.014), rot)
        peca(nome + '_faixa', bm, 'listras_v', raiz)

    if tipo == 'logistico':
        # garra suspensa num pivô (pêndulo): junta cardã + haste + garra de 4 dedos + placa de ferro
        bm = bmesh.new()
        cil(bm, Vector((0, 0, -0.075)), 0.03, 0.018, lados=16)
        caixa(bm, (0, 0, -0.088), (0.03, 0.03, 0.012))
        peca(nome + '_guincho', bm, 'grafite', raiz)
        pend = vazio(nome + '_pendulo', raiz, (0, 0, -0.095))
        pend.rotation_mode = 'QUATERNION'
        bm = bmesh.new()
        esfera(bm, Vector((0, 0, 0)), 0.012, 10)
        tubo(bm, (0, 0, 0), (0, 0, -0.12), 0.006, 10)
        cil(bm, Vector((0, 0, -0.128)), 0.028, 0.018, lados=16)
        peca(nome + '_haste', bm, 'aco', pend, liso=True)
        bm = bmesh.new()
        for j in range(4):
            aa = j * PI / 2 + PI / 4
            dd = Vector((math.cos(aa), math.sin(aa), 0))
            ro = Matrix.Rotation(aa, 3, 'Z')
            viga(bm, dd * 0.02 + Vector((0, 0, -0.13)), dd * 0.15 + Vector((0, 0, -0.142)), 0.012)
            viga(bm, dd * 0.15 + Vector((0, 0, -0.142)), dd * 0.152 + Vector((0, 0, -0.18)), 0.012)
            caixa(bm, dd * 0.142 + Vector((0, 0, -0.18)), (0.02, 0.016, 0.006), ro)      # unha por baixo da placa
        peca(nome + '_garra', bm, 'amarelo_gasto', pend)
        bm = bmesh.new()
        for j in range(4):                                                     # pistõezinhos dos dedos
            aa = j * PI / 2 + PI / 4
            dd = Vector((math.cos(aa), math.sin(aa), 0))
            tubo(bm, dd * 0.025 + Vector((0, 0, -0.118)), dd * 0.09 + Vector((0, 0, -0.135)), 0.0035, 6)
        peca(nome + '_garra_pist', bm, 'cromo', pend, liso=True)
        bm = bmesh.new()
        caixa_de(bm, (-0.105, -0.105, -0.176), (0.105, 0.105, -0.158))
        D['carga'] = peca(nome + '_placa_ferro', bm, 'placa_suja', pend)
        D['pendulo'] = pend

    detalhar_drone(D, nome, tipo, raiz, casco, R, AP)

    if amassar > 0:                                                            # sucata: amassa tudo
        for o in [o for o in bpy.data.objects if o.type == 'MESH' and _desc(o, raiz)]:
            for v in o.data.vertices:
                w = o.matrix_local.copy()
                v.co += Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * amassar
    return D


SERIE = {'R1': '07', 'L1': '21', 'D1': '13', 'D1_sucata': '13', 'V_reparo': '04', 'V_defesa': '11', 'V_logistico': '18'}


def detalhar_drone(D, nome, tipo, raiz, casco, R, AP):
    """Rebites nas quinas e nas linhas de painel, remendos aparafusados, feixes de fios com abraçadeiras, conectores,
    dissipador com aletas, adesivo com número de série apagado, fuligem e marcas de solda."""
    bm = bmesh.new()
    for k in range(6):                                                 # rebites nas quinas do hexágono
        a = PI / 6 + k * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        for z in (-0.03, -0.01, 0.01, 0.03):
            parafuso(bm, d * (R - 0.002) + Vector((0, 0, z)), d, 0.0032)
    for k in range(6):                                                 # linhas de painel no tampo com rebites
        a = k * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        for t in (0.055, 0.075, 0.095):
            parafuso(bm, d * t + Vector((0, 0, 0.0715)), (0, 0, 1), 0.0026)
    peca(nome + '_rebites', bm, 'ferro', raiz)
    bm = bmesh.new()
    for k in range(6):
        a = k * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(bm, d * 0.083 + Vector((0, 0, 0.0712)), (0.068, 0.0025, 0.0012), Matrix.Rotation(a, 3, 'Z'))
    for k in range(6):                                                 # emenda entre miolo e troncos
        a = PI / 6 + k * PI / 3
    peca(nome + '_juntas', bm, 'tinta_preta', raiz)
    # remendos aparafusados por cima
    bm, bp = bmesh.new(), bmesh.new()
    for (fi, z, w, h, gir) in ((4 * PI / 3, -0.012, 0.05, 0.036, 0.22), (2 * PI / 3, 0.018, 0.034, 0.026, -0.3)):
        rot = Matrix.Rotation(fi, 3, 'Z')
        n = rot @ Vector((1, 0, 0))
        t = rot @ Vector((0, 1, 0))
        esp = 0.014 if tipo == 'defesa' else 0.007
        c = n * (AP + esp + 0.0025) + t * 0.02 + Vector((0, 0, z))
        rr = rot @ Matrix.Rotation(gir, 3, 'X')
        caixa(bm, c, (0.004, w, h), rr)
        for sx in (-1, 1):
            for sz in (-1, 1):
                parafuso(bp, c + rr @ Vector((0.002, sx * (w / 2 - 0.006), sz * (h / 2 - 0.005))), n, 0.0034)
    caixa(bm, Vector((0.045, -0.06, 0.0735)), (0.04, 0.03, 0.004), Matrix.Rotation(0.5, 3, 'Z'))   # remendo no tampo
    for sx in (-1, 1):
        for sy in (-1, 1):
            parafuso(bp, Vector((0.045, -0.06, 0.0755)) + Matrix.Rotation(0.5, 3, 'Z') @ Vector((sx * 0.015, sy * 0.01, 0)), (0, 0, 1), 0.003)
    peca(nome + '_remendo_chapa', bm, 'chapa_ferrugem', raiz)
    peca(nome + '_remendo_parafusos', bp, 'ferro', raiz)
    # feixes de fios por baixo, com abraçadeiras, até os braços de trás; conectores
    bfs = [bmesh.new() for _ in range(3)]
    bab, bco = bmesh.new(), bmesh.new()
    for k in (1, 2):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = Vector((-0.02, 0.0, -0.068))
        p3 = d * (R_DUTO_C - R_DUTO - 0.01) + Vector((0, 0, -0.022))
        lat = Vector((-d.y, d.x, 0))
        for j, bf in enumerate(bfs):
            off = lat * ((j - 1) * 0.0055) + Vector((0, 0, -0.002 * abs(j - 1)))
            pts = bezier(p0 + off, p0 + d * 0.06 + off + Vector((0, 0, -0.008)), p3 - d * 0.05 + off + Vector((0, 0, -0.018)), p3 + off, 9)
            mangueira(bf, pts, 0.0028)
        mid = bezier(p0, p0 + d * 0.06 + Vector((0, 0, -0.008)), p3 - d * 0.05 + Vector((0, 0, -0.018)), p3, 9)
        for t in (2, 5, 8):
            dd = (mid[t + 1] - mid[t - 1]).normalized()
            toro(bab, mid[t], 0.0095, 0.0018, dd, 14, 5)
        cil(bco, p3 + d * 0.004, 0.009, 0.014, d, lados=10)
        cil(bco, p0 + Vector((0, 0, 0.004)), 0.011, 0.01, lados=10)
    for bf, mt in zip(bfs, ('borracha', 'cabo_v', 'cabo_a')):
        peca(nome + '_fios', bf, mt, raiz, liso=True)
    peca(nome + '_abracadeiras', bab, 'aco', raiz, liso=True)
    peca(nome + '_conectores', bco, 'grafite', raiz, liso=True)
    # dissipador com aletas por baixo, atrás
    bm = bmesh.new()
    caixa_de(bm, (-0.115, -0.05, -0.072), (-0.04, 0.05, -0.066))
    for j in range(9):
        caixa_de(bm, (-0.112, -0.046 + j * 0.0115, -0.088), (-0.043, -0.0445 + j * 0.0115, -0.072))
    peca(nome + '_dissipador', bm, 'aco', raiz)
    # adesivo apagado com número de série + listra
    fi = PI / 3
    rot = Matrix.Rotation(fi, 3, 'Z')
    n, t = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
    esp = 0.014 if tipo == 'defesa' else 0.007
    bm = bmesh.new()
    caixa(bm, n * (AP + esp + 0.0006) + Vector((0, 0, 0.012)), (0.001, 0.07, 0.034), rot)
    peca(nome + '_adesivo', bm, 'adesivo', raiz)
    bm = bmesh.new()
    digitos(bm, SERIE.get(nome, '00'), n * (AP + esp + 0.0014) - t * 0.012 + Vector((0, 0, 0.002)), t, (0, 0, 1), 0.02)
    caixa(bm, n * (AP + esp + 0.0014) + t * 0.024 + Vector((0, 0, 0.012)), (0.001, 0.012, 0.028), rot)
    peca(nome + '_serie', bm, 'tinta_preta', raiz)
    bm = bmesh.new()                                                   # número grande no tampo
    digitos(bm, SERIE.get(nome, '00'), Vector((-0.02, 0.07, 0.0722)), (1, 0, 0), (0, -1, 0), 0.026, 0.0022)
    peca(nome + '_serie_tampo', bm, 'tinta_preta', raiz)
    # fuligem perto dos motores (em cima dos braços) e escorrido de óleo
    bm = bmesh.new()
    for k in range(4):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        res = bmesh.ops.create_circle(bm, cap_ends=True, segments=9, radius=0.016)
        for v in res['verts']:
            v.co = d * 0.155 + Matrix.Rotation(a, 3, 'Z') @ Vector((v.co.x * 1.6, v.co.y * random.uniform(0.7, 1.1), 0)) + Vector((0, 0, 0.0152))
    peca(nome + '_fuligem_bracos', bm, 'fuligem', raiz)
    bm = bmesh.new()
    for k in (2, 4, 5):
        fi = k * PI / 3
        rot = Matrix.Rotation(fi, 3, 'Z')
        n_ = rot @ Vector((1, 0, 0))
        t_ = rot @ Vector((0, 1, 0))
        esp = 0.014 if tipo == 'defesa' else 0.007
        x = random.uniform(-0.04, 0.04)
        h = random.uniform(0.02, 0.05)
        caixa(bm, n_ * (AP + esp + 0.0008) + t_ * x + Vector((0, 0, 0.02 - h / 2)), (0.0008, 0.004, h), rot)
    peca(nome + '_oleo', bm, 'oleo', raiz)


def _desc(o, raiz):
    while o.parent is not None:
        if o.parent == raiz:
            return True
        o = o.parent
    return False


# ------------------------------------------------------------------ estação de drones 2×2
DECK = 0.70
TOPO_BERCO = DECK + 0.03
TOPO_FAB = DECK + 0.05
FAB = Vector((-0.5, 0.0, 0))
BERCOS = [Vector((0.5, 0.5, 0)), Vector((0.5, -0.5, 0))]
REVISTA = Vector((0.88, 0.0, 0))
BRACO_EST = Vector((0.36, 0.0, 0))


def estacao():
    """Estação 2×2: laje, estrutura, convés, fabricadora com 3 projetores do holograma, 2 berços de recarga com
    garras de encaixe e plugue, tanque d'água (50 por drone), estoque e revista de placas, braço abastecedor,
    farol giratório, cabos, canos e sujeira. Devolve dict com as partes animadas."""
    E = {}
    random.seed(5)
    bm = bmesh.new()
    caixa_de(bm, (-0.99, -0.99, 0), (0.99, 0.99, 0.08))
    peca('laje', bm, 'concreto')
    bm = bmesh.new()
    for s in (-1, 1):
        caixa_de(bm, (-0.995, s * 0.985 - 0.012, 0.0), (0.995, s * 0.985 + 0.012, 0.081))
    peca('laje_listras', bm, 'listras')
    # colunas, travessas e convés
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 0.92, sy * 0.92
            caixa_de(bm, (x - 0.04, y - 0.04, 0.08), (x + 0.04, y + 0.04, DECK - 0.04))
            caixa_de(bm, (x - 0.07, y - 0.07, 0.08), (x + 0.07, y + 0.07, 0.1))
    for sy in (-1, 1):
        viga(bm, (-0.9, sy * 0.92, 0.12), (0.9, sy * 0.92, DECK - 0.08), 0.03)
    caixa_de(bm, (-0.98, -0.98, DECK - 0.1), (0.98, -0.9, DECK - 0.04))
    caixa_de(bm, (-0.98, 0.9, DECK - 0.1), (0.98, 0.98, DECK - 0.04))
    caixa_de(bm, (-0.98, -0.9, DECK - 0.1), (-0.9, 0.9, DECK - 0.04))
    caixa_de(bm, (0.9, -0.9, DECK - 0.1), (0.98, 0.9, DECK - 0.04))
    caixa_de(bm, (-0.05, -0.9, DECK - 0.1), (0.05, 0.9, DECK - 0.04))
    peca('estrutura', bm, 'amarelo_gasto')
    bm = bmesh.new()
    caixa_de(bm, (-0.98, -0.98, DECK - 0.04), (0.98, 0.98, DECK))
    peca('conves', bm, 'grafite')
    bm = bmesh.new()
    for k in range(18):                                                   # chapa xadrez (antiderrapante)
        for j in range(18):
            if (k + j) % 2 == 0 and random.random() < 0.8:
                c = Vector((-0.94 + k * 0.11, -0.94 + j * 0.11, DECK + 0.001))
                caixa(bm, c, (0.035, 0.008, 0.002), Matrix.Rotation(PI / 4 if k % 2 else -PI / 4, 3, 'Z'))
    peca('conves_xadrez', bm, 'grafite')
    bm = bmesh.new()
    for s in (-1, 1):
        caixa_de(bm, (-0.98, s * 0.97 - 0.01, DECK), (0.98, s * 0.97 + 0.01, DECK + 0.004))
    peca('conves_listras', bm, 'listras')

    # ---- fabricadora: plataforma hexagonal sobre a câmara, 3 projetores do holograma
    bm = bmesh.new()
    cil(bm, FAB + Vector((0, 0, (0.08 + DECK - 0.04) / 2)), 0.3, DECK - 0.12, lados=24)
    peca('fab_camara', bm, 'casco', liso=True)
    bm = bmesh.new()
    for z in (0.2, 0.45):
        cil(bm, FAB + Vector((0, 0, z)), 0.31, 0.04, lados=24)
    for j in range(10):
        a = j * 2 * PI / 10
        cil(bm, FAB + Vector((math.cos(a) * 0.318, math.sin(a) * 0.318, 0.2)), 0.008, 0.01, Vector((math.cos(a), math.sin(a), 0)), lados=6)
    peca('fab_cintas', bm, 'ferro', liso=True)
    bm = bmesh.new()
    prisma(bm, FAB, 0.36, 0.34, DECK, TOPO_FAB, 6, 0)
    peca('fab_plataforma', bm, 'aco')
    bm = bmesh.new()
    prisma(bm, FAB, 0.29, 0.29, TOPO_FAB, TOPO_FAB + 0.002, 6, 0)
    E['fab_grade'] = peca('fab_grade', bm, 'grade_holo')
    bm = bmesh.new()
    toro(bm, FAB + Vector((0, 0, TOPO_FAB + 0.004)), 0.3, 0.006, nR=48)
    peca('fab_aro', bm, 'emissor')
    E['projetores'] = []
    bm, bml, bmc = bmesh.new(), bmesh.new(), bmesh.new()
    for j in range(3):
        a = PI / 2 + j * 2 * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        b0 = FAB + d * 0.5
        caixa(bm, b0 + Vector((0, 0, DECK + 0.02)), (0.1, 0.1, 0.04), Matrix.Rotation(a, 3, 'Z'))
        topo = b0 + Vector((0, 0, DECK + 0.62))
        viga(bm, b0 + Vector((0, 0, DECK + 0.04)), topo, 0.045)
        cab = topo - d * 0.06 + Vector((0, 0, 0.02))
        viga(bm, topo, cab, 0.04)
        alvo = FAB + Vector((0, 0, TOPO_FAB + 0.2))
        dirc = (alvo - cab).normalized()
        cil(bm, cab, 0.035, 0.07, dirc, lados=14)
        cil(bml, cab + dirc * 0.036, 0.024, 0.006, dirc, lados=14)
        E['projetores'].append(cab + dirc * 0.04)
        for k in range(4):                                                 # aletas do emissor
            cil(bm, cab - dirc * (0.01 + k * 0.012), 0.042, 0.004, dirc, lados=14)
        mangueira(bmc, bezier(b0 + d * 0.03 + Vector((0, 0, DECK + 0.05)), b0 + d * 0.08 + Vector((0, 0, DECK + 0.3)),
                              topo + d * 0.06 + Vector((0, 0, -0.1)), topo + d * 0.025, 8), 0.008)
    peca('projetores', bm, 'grafite')
    peca('projetores_lente', bml, 'emissor')
    peca('projetores_cabos', bmc, 'borracha', liso=True)

    # ---- berços de recarga: base, calhas dos patins, garras com pistão, plugue, luzes de pouso
    E['garras'], E['plugues'], E['luzes_pouso'] = [], [], []
    for i, B in enumerate(BERCOS):
        bm = bmesh.new()
        caixa_de(bm, (B.x - 0.3, B.y - 0.27, DECK), (B.x + 0.3, B.y + 0.27, TOPO_BERCO))
        peca('berco%d_base' % i, bm, 'casco')
        bm = bmesh.new()
        for sy in (-1, 1):
            y = B.y + sy * 0.085
            caixa_de(bm, (B.x - 0.17, y - 0.022, TOPO_BERCO), (B.x + 0.17, y - 0.012, TOPO_BERCO + 0.02))
            caixa_de(bm, (B.x - 0.17, y + 0.012, TOPO_BERCO), (B.x + 0.17, y + 0.022, TOPO_BERCO + 0.02))
            caixa_de(bm, (B.x - 0.03, y - 0.012, TOPO_BERCO), (B.x + 0.03, y + 0.012, TOPO_BERCO + 0.003))
        peca('berco%d_calhas' % i, bm, 'aco')
        bm = bmesh.new()
        for sy in (-1, 1):
            caixa_de(bm, (B.x - 0.025, B.y + sy * 0.085 - 0.01, TOPO_BERCO + 0.003), (B.x + 0.025, B.y + sy * 0.085 + 0.01, TOPO_BERCO + 0.006))
        peca('berco%d_contatos' % i, bm, 'cobre')
        bm = bmesh.new()                                                  # marca de pouso (anel listrado)
        toro(bm, B + Vector((0, 0, TOPO_BERCO + 0.0)), 0.23, 0.004, nR=48, nr=4)
        peca('berco%d_marca' % i, bm, 'listras')
        bm = bmesh.new()
        for j in range(8):
            a = j * PI / 4 + PI / 8
            caixa(bm, B + Vector((math.cos(a) * 0.285, math.sin(a) * 0.255, TOPO_BERCO + 0.006)), (0.03, 0.03, 0.012),
                  Matrix.Rotation(a, 3, 'Z'))
        lp = peca('berco%d_luzes' % i, bm, 'lampada')
        m = lp.data.materials[0].copy()
        m.name = 'Luz pouso %d' % i
        lp.data.materials[0] = m
        E['luzes_pouso'].append(m)
        # garras: 4 mandíbulas (2 por patim), cada uma com pivô e pistão
        gs = []
        for sy in (-1, 1):
            for sx in (-1, 1):
                pv = B + Vector((sx * 0.1, sy * 0.125, TOPO_BERCO + 0.012))
                g = vazio('berco%d_garra' % i, None, pv)
                g.rotation_mode = 'XYZ'
                g['lado'] = sy
                bm = bmesh.new()
                cil(bm, Vector((0, 0, 0)), 0.009, 0.03, Vector((1, 0, 0)), lados=10)
                caixa_de(bm, (-0.012, -sy * 0.004 - 0.004, 0.0), (0.012, -sy * 0.004 + 0.004, 0.034))
                caixa_de(bm, (-0.012, -sy * 0.034, 0.026), (0.012, -sy * 0.004, 0.034))
                caixa_de(bm, (-0.012, -sy * 0.034, 0.016), (0.012, -sy * 0.028, 0.034))
                peca('berco%d_mandibula' % i, bm, 'amarelo', g)
                bm = bmesh.new()
                caixa_de(bm, (pv.x - 0.02, pv.y - 0.012, TOPO_BERCO), (pv.x + 0.02, pv.y + 0.012, pv.z - 0.004))
                peca('berco%d_mancal' % i, bm, 'ferro')
                ca = vazio('berco%d_pist_c' % i)
                ca.rotation_mode = 'QUATERNION'
                bm = bmesh.new()
                cil(bm, Vector((0, 0, 0.014)), 0.006, 0.028, lados=10)
                peca('berco%d_pist_camisa' % i, bm, 'grafite', ca, liso=True)
                ha = vazio('berco%d_pist_h' % i)
                ha.rotation_mode = 'QUATERNION'
                bm = bmesh.new()
                cil(bm, Vector((0, 0, 0.016)), 0.0032, 0.032, lados=8)
                peca('berco%d_pist_haste' % i, bm, 'cromo', ha, liso=True)
                ancora = B + Vector((sx * 0.1, sy * 0.2, TOPO_BERCO + 0.006))
                gs.append((g, ca, ha, ancora, sy))
        E['garras'].append(gs)
        # plugue que entra na tomada da bateria (atrás do drone, -x)
        bm = bmesh.new()
        caixa_de(bm, (B.x - 0.3, B.y - 0.05, TOPO_BERCO), (B.x - 0.24, B.y + 0.05, TOPO_BERCO + 0.2))
        peca('berco%d_poste' % i, bm, 'grafite')
        pl = vazio('berco%d_plugue' % i, None, (B.x - 0.24, B.y, TOPO_BERCO + 0.158 - 0.015))
        bm = bmesh.new()
        cil(bm, Vector((0.015, 0, 0)), 0.012, 0.03, Vector((1, 0, 0)), lados=12)
        cil(bm, Vector((0.034, 0, 0)), 0.006, 0.012, Vector((1, 0, 0)), lados=10)
        peca('berco%d_plugue_corpo' % i, bm, 'amarelo', pl, liso=True)
        E['plugues'].append(pl)
        bm = bmesh.new()                                                  # cabo de força do poste ao convés
        mangueira(bm, bezier(Vector((B.x - 0.27, B.y + 0.05, TOPO_BERCO + 0.15)), Vector((B.x - 0.27, B.y + 0.12, TOPO_BERCO + 0.15)),
                             Vector((B.x - 0.3, B.y + 0.15, DECK + 0.02)), Vector((B.x - 0.36, B.y + 0.16, DECK + 0.01)), 8), 0.01)
        peca('berco%d_cabo' % i, bm, 'borracha', liso=True)
        E['luz_pouso_%d' % i] = luz('luz_pouso%d' % i, 'POINT', (1.0, 0.32, 0.05), 3.0, 0.05, None, B + Vector((0, 0, TOPO_BERCO + 0.05)))

    # ---- revista de remendos (placas) e braço abastecedor
    bm = bmesh.new()
    caixa_de(bm, (REVISTA.x - 0.08, REVISTA.y - 0.09, 0.08), (REVISTA.x + 0.08, REVISTA.y + 0.09, DECK + 0.26))
    peca('revista', bm, 'amarelo')
    bm = bmesh.new()
    caixa_de(bm, (REVISTA.x - 0.081, REVISTA.y - 0.05, DECK + 0.03), (REVISTA.x - 0.07, REVISTA.y + 0.05, DECK + 0.24))
    peca('revista_visor', bm, 'vidro')
    bm = bmesh.new()
    for k in range(14):
        caixa(bm, Vector((REVISTA.x - 0.072, REVISTA.y, DECK + 0.04 + k * 0.014)), (0.004, 0.08, 0.006),
              Matrix.Rotation(random.uniform(-0.02, 0.02), 3, 'X'))
    peca('revista_placas', bm, 'placa_ferro')
    bm = bmesh.new()
    caixa_de(bm, (REVISTA.x - 0.06, REVISTA.y - 0.06, DECK + 0.26), (REVISTA.x + 0.06, REVISTA.y + 0.06, DECK + 0.262))
    peca('revista_boca', bm, 'ferro')
    E['remendo_topo'] = REVISTA + Vector((0, 0, DECK + 0.268))
    bm = bmesh.new()                                                       # placa pronta na boca da revista
    caixa(bm, (0, 0, 0), (0.046, 0.075, 0.007))
    E['remendo'] = peca('remendo_braco', bm, 'placa_ferro')
    E['remendo'].rotation_mode = 'QUATERNION'
    # braço abastecedor: base giratória + 2 elos + ventosa
    giro = vazio('abast_giro', None, BRACO_EST + Vector((0, 0, DECK)))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.03)), 0.055, 0.06, lados=20)
    cil(bm, Vector((0, 0, 0.075)), 0.04, 0.03, lados=20)
    for sy in (-1, 1):
        caixa(bm, (0, sy * 0.03, 0.11), (0.05, 0.01, 0.06))
    peca('abast_base', bm, 'amarelo', giro, liso=True)
    omb = vazio('abast_ombro', giro, (0, 0, 0.12))
    bm = bmesh.new()
    caixa_de(bm, (0, -0.018, -0.016), (0.32, 0.018, 0.016))
    cil(bm, Vector((0, 0, 0)), 0.022, 0.05, Vector((0, 1, 0)), lados=14)
    peca('abast_elo1', bm, 'amarelo', omb, liso=True)
    cot = vazio('abast_cotovelo', omb, (0.32, 0, 0))
    bm = bmesh.new()
    caixa_de(bm, (0, -0.014, -0.012), (0.26, 0.014, 0.012))
    cil(bm, Vector((0, 0, 0)), 0.018, 0.04, Vector((0, 1, 0)), lados=14)
    peca('abast_elo2', bm, 'amarelo', cot, liso=True)
    pun = vazio('abast_punho', cot, (0.26, 0, 0))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -0.02)), 0.012, 0.04, lados=10)
    cil(bm, Vector((0, 0, -0.045)), 0.03, 0.01, lados=14)
    peca('abast_ventosa', bm, 'borracha', pun, liso=True)
    bm = bmesh.new()
    mangueira(bm, bezier((0.02, 0.02, 0.02), (0.15, 0.03, 0.05), (0.28, 0.03, 0.04), (0.31, 0.02, 0.02), 8), 0.006)
    peca('abast_mangueira', bm, 'borracha', omb, liso=True)
    pis = []
    for pai in (giro, omb):
        ca = vazio('abast_pist_c', pai)
        ca.rotation_mode = 'QUATERNION'
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.05)), 0.011, 0.1, lados=12)
        peca('abast_pistao_camisa', bm, 'grafite', ca, liso=True)
        ha = vazio('abast_pist_h', pai)
        ha.rotation_mode = 'QUATERNION'
        bm = bmesh.new()
        cil(bm, Vector((0, 0, 0.055)), 0.006, 0.11, lados=10)
        peca('abast_pistao_haste', bm, 'cromo', ha, liso=True)
        pis.append((ca, ha))
    E['abast'] = dict(giro=giro, ombro=omb, cotovelo=cot, punho=pun, pistoes=pis)

    # ---- embaixo do convés: tanque d'água, bomba, estoque de placas, caixa de junção
    T = Vector((0.45, -0.45, 0))
    bm = bmesh.new()
    cil(bm, T + Vector((0, 0, 0.36)), 0.27, 0.48, lados=28)
    esfera(bm, T + Vector((0, 0, 0.6)), 0.27, 28, (1, 1, 0.25))
    peca('tanque', bm, 'casco', liso=True)
    bm = bmesh.new()
    for z in (0.18, 0.36, 0.54):
        cil(bm, T + Vector((0, 0, z)), 0.277, 0.025, lados=28)
    for sx in (-1, 1):
        for sy in (-1, 1):
            viga(bm, T + Vector((sx * 0.17, sy * 0.17, 0.08)), T + Vector((sx * 0.19, sy * 0.19, 0.14)), 0.03)
    peca('tanque_cintas', bm, 'ferro', liso=True)
    bm = bmesh.new()                                                       # visor de nível
    caixa_de(bm, (T.x - 0.03, T.y - 0.285, 0.15), (T.x + 0.03, T.y - 0.27, 0.56))
    peca('tanque_visor_moldura', bm, 'aco')
    bm = bmesh.new()
    caixa_de(bm, (T.x - 0.016, T.y - 0.288, 0.17), (T.x + 0.016, T.y - 0.284, 0.44))
    peca('tanque_agua', bm, 'agua')
    bm = bmesh.new()
    caixa_de(bm, (T.x - 0.016, T.y - 0.288, 0.44), (T.x + 0.016, T.y - 0.284, 0.54))
    peca('tanque_vazio', bm, 'vidro')
    bm = bmesh.new()                                                       # bomba e cano até a fabricadora
    cil(bm, Vector((0.0, -0.62, 0.17)), 0.06, 0.14, Vector((1, 0, 0)), lados=16)
    caixa_de(bm, (-0.09, -0.7, 0.08), (0.09, -0.54, 0.1))
    peca('bomba', bm, 'amarelo', liso=True)
    bm = bmesh.new()
    pts = [T + Vector((-0.27, -0.17, 0.17)), Vector((0.07, -0.62, 0.17)), ]
    tubo(bm, Vector((T.x - 0.2, T.y - 0.17, 0.17)), Vector((0.07, -0.62, 0.17)) + Vector((0, 0, 0)), 0.022, 14)
    tubo(bm, Vector((-0.07, -0.62, 0.17)), Vector((-0.35, -0.62, 0.17)), 0.022, 14)
    tubo(bm, Vector((-0.35, -0.62, 0.17)), Vector((-0.35, -0.24, 0.17)), 0.022, 14)
    esfera(bm, Vector((-0.35, -0.62, 0.17)), 0.022, 14)
    peca('cano_agua', bm, 'cobre', liso=True)
    bm = bmesh.new()
    for p, d in ((Vector((-0.2, -0.62, 0.17)), (1, 0, 0)), (Vector((-0.35, -0.4, 0.17)), (0, 1, 0)), (Vector((0.12, -0.6, 0.17)), (1, -0.4, 0))):
        cil(bm, p, 0.032, 0.018, Vector(d), lados=14)
    peca('cano_flanges', bm, 'ferro')
    S0 = Vector((0.5, 0.48, 0))                                            # estoque: prateleira com pilha de placas
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            caixa_de(bm, (S0.x + sx * 0.17 - 0.012, S0.y + sy * 0.15 - 0.012, 0.08), (S0.x + sx * 0.17 + 0.012, S0.y + sy * 0.15 + 0.012, 0.5))
    for z in (0.12, 0.33, 0.5):
        caixa_de(bm, (S0.x - 0.19, S0.y - 0.17, z - 0.01), (S0.x + 0.19, S0.y + 0.17, z))
    peca('estoque', bm, 'grafite')
    bm = bmesh.new()
    for z0 in (0.12, 0.33):
        for k in range(9):
            caixa(bm, Vector((S0.x + random.uniform(-0.01, 0.01), S0.y + random.uniform(-0.01, 0.01), z0 + 0.006 + k * 0.016)),
                  (0.3, 0.26, 0.012), Matrix.Rotation(random.uniform(-0.04, 0.04), 3, 'Z'))
    peca('estoque_placas', bm, 'placa_ferro')
    bm = bmesh.new()                                                       # elevador do estoque até a revista
    tubo(bm, (S0.x + 0.19, S0.y - 0.1, 0.42), (REVISTA.x - 0.05, REVISTA.y + 0.09, 0.42), 0.02, 10)
    peca('estoque_alimentador', bm, 'aco', liso=True)
    bm = bmesh.new()                                                       # caixa de junção + eletrocalha
    caixa_de(bm, (-0.98, 0.55, 0.25), (-0.9, 0.8, 0.55))
    caixa_de(bm, (-0.9, -0.85, DECK - 0.14), (0.85, -0.78, DECK - 0.1))
    peca('juncao', bm, 'grafite')
    bm = bmesh.new()
    for j in range(4):
        mangueira(bm, bezier(Vector((-0.9, 0.6 + j * 0.05, 0.3)), Vector((-0.7, 0.6 + j * 0.05, 0.25)),
                             Vector((-0.6, -0.2 + j * 0.04, 0.3)), Vector((-0.5, -0.29, 0.35 + j * 0.05)), 10), 0.009)
    for j in range(3):
        mangueira(bm, bezier(Vector((-0.98, 0.62 + j * 0.06, 0.25)), Vector((-1.05, 0.62 + j * 0.06, 0.12)),
                             Vector((-1.2, 0.7 + j * 0.06, 0.02)), Vector((-1.6, 0.8 + j * 0.07, 0.015)), 10), 0.014)
    peca('cabos', bm, 'borracha', liso=True)
    # farol giratório no canto
    bm = bmesh.new()
    tubo(bm, (-0.92, 0.92, DECK), (-0.92, 0.92, DECK + 0.5), 0.02, 10)
    cil(bm, Vector((-0.92, 0.92, DECK + 0.51)), 0.04, 0.02, lados=14)
    peca('farol_mastro', bm, 'aco', liso=True)
    bm = bmesh.new()
    cil(bm, Vector((-0.92, 0.92, DECK + 0.55)), 0.035, 0.06, lados=16)
    peca('farol', bm, 'farol_v', liso=True)
    E['farol'] = luz('farol_luz', 'SPOT', (1.0, 0.04, 0.02), 30.0, 0.02, None, (-0.92, 0.92, DECK + 0.55))
    E['farol'].data.spot_size = 0.9
    E['farol'].rotation_mode = 'XYZ'
    # sujeira
    bm = bmesh.new()
    for c, r in (((0.2, -0.75), 0.1), ((-0.7, -0.3), 0.08), ((0.75, 0.2), 0.06), ((-0.2, 0.7), 0.07)):
        mancha(bm, c, r, 0.0815)
    peca('oleo', bm, 'oleo')
    bm = bmesh.new()
    for k in range(10):
        mancha(bm, (random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9)), random.uniform(0.04, 0.1), DECK + 0.0015)
    for j in range(3):                                                   # fuligem em volta da fabricadora
        a = j * 2 * PI / 3 + 0.4
        mancha(bm, (FAB.x + math.cos(a) * 0.4, FAB.y + math.sin(a) * 0.4), 0.09, DECK + 0.0016)
    for B in BERCOS:                                                     # queimado de motor em cima dos berços
        for sx in (-1, 1):
            for sy in (-1, 1):
                mancha(bm, (B.x + sx * 0.19, B.y + sy * 0.19), 0.06, TOPO_BERCO + 0.0008)
    peca('conves_fuligem', bm, 'fuligem')
    # concreto rachado e lascado
    bm = bmesh.new()
    for (p0, p1) in (((-0.99, -0.55), (-0.6, -0.95)), ((0.99, 0.3), (0.55, 0.62)), ((-0.2, 0.99), (0.15, 0.6)), ((0.6, -0.99), (0.9, -0.6))):
        pts = [Vector((p0[0] + (p1[0] - p0[0]) * t / 8 + random.uniform(-0.02, 0.02), p0[1] + (p1[1] - p0[1]) * t / 8 + random.uniform(-0.02, 0.02), 0.0806)) for t in range(9)]
        for q0, q1 in zip(pts, pts[1:]):
            d = (q1 - q0)
            caixa(bm, (q0 + q1) / 2, (d.length + 0.004, random.uniform(0.004, 0.008), 0.0012), Matrix.Rotation(math.atan2(d.y, d.x), 3, 'Z'))
    peca('laje_rachaduras', bm, 'fuligem')
    bm = bmesh.new()
    for c in ((-0.99, -0.99), (0.99, 0.6), (-0.4, 0.99)):              # quinas lascadas (cacos)
        for k in range(5):
            pedra(bm, Vector((c[0] * 0.98 + random.uniform(-0.06, 0.06), c[1] * 0.98 + random.uniform(-0.06, 0.06), 0.01)), random.uniform(0.01, 0.025), 0.5)
    peca('laje_cacos', bm, 'concreto')
    # berços: riscos de borracha dos patins, contatos gastos, pintura gasta na marca
    bm = bmesh.new()
    for B in BERCOS:
        for sy in (-1, 1):
            for k in range(5):
                y = B.y + sy * 0.085 + random.uniform(-0.03, 0.03)
                x0 = B.x + random.uniform(-0.25, 0.0)
                caixa_de(bm, (x0, y - 0.003, TOPO_BERCO + 0.0005), (x0 + random.uniform(0.08, 0.2), y + 0.003, TOPO_BERCO + 0.0012))
    peca('bercos_riscos', bm, 'borracha')
    # óleo escorrendo nas colunas e no tanque
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(2):
                x = sx * 0.92 + random.uniform(-0.025, 0.025)
                h = random.uniform(0.15, 0.4)
                caixa_de(bm, (x - 0.004, sy * 0.92 - sy * 0.0405 - 0.001, DECK - 0.04 - h), (x + 0.004, sy * 0.92 - sy * 0.0405 + 0.001, DECK - 0.04))
    for k in range(4):
        a = random.uniform(-PI, 0)
        caixa(bm, Vector((0.45 + math.cos(a) * 0.272, -0.45 + math.sin(a) * 0.272, 0.42)), (0.004, 0.008, random.uniform(0.1, 0.3)), Matrix.Rotation(a, 3, 'Z'))
    peca('oleo_escorrido', bm, 'oleo')
    # flanges e abraçadeiras extras
    bm = bmesh.new()
    for p, d in ((Vector((-0.35, -0.3, 0.17)), (0, 1, 0)), (Vector((0.45 - 0.2, -0.45 - 0.17, 0.17)), (1, -0.4, 0)), (Vector((-0.5, -0.62, 0.17)), (1, 0, 0))):
        cil(bm, p, 0.034, 0.016, Vector(d), lados=14)
        for k in range(6):
            aa = k * PI / 3
            q = Vector(d).normalized().to_track_quat('Z', 'Y').to_matrix()
            cil(bm, p + q @ Vector((math.cos(aa) * 0.026, math.sin(aa) * 0.026, 0)), 0.004, 0.024, Vector(d), lados=6)
    for k in range(5):
        caixa(bm, Vector((-0.75 + k * 0.35, -0.815, DECK - 0.1)), (0.02, 0.09, 0.01))
    peca('flanges_extra', bm, 'ferro', liso=True)
    # cacos de drone velho num canto do convés
    bm, bh, bf, bc = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    C0 = Vector((-0.8, -0.8, DECK))
    toro(bm, C0 + Vector((0.02, 0.06, 0.068)), 0.095, 0.009, Vector((0.35, 0.2, 1)), 30, 8)
    anel_aberto(bm, C0 + Vector((0.02, 0.06, 0.068)), 0.1, 0.05, Vector((0.35, 0.2, 1)), 30)
    caixa(bm, C0 + Vector((-0.07, -0.05, 0.012)), (0.11, 0.07, 0.008), Matrix.Rotation(0.6, 3, 'Z') @ Matrix.Rotation(0.15, 3, 'X'))
    caixa(bm, C0 + Vector((0.09, -0.08, 0.02)), (0.06, 0.05, 0.007), Matrix.Rotation(-0.4, 3, 'Z') @ Matrix.Rotation(0.6, 3, 'Y'))
    peca('cacos_casco', bm, 'chapa_ferrugem', liso=True)
    for j in range(3):
        aa = random.uniform(0, 2 * PI)
        pa(bh, aa, 1, 0.0)
    for v in bh.verts:
        v.co = C0 + Vector((0.1, 0.1, 0.006)) + Matrix.Rotation(0.4, 3, 'X') @ v.co * 1.0
    peca('cacos_pas', bh, 'helice')
    viga(bf, C0 + Vector((-0.12, 0.08, 0.012)), C0 + Vector((-0.02, 0.14, 0.014)), 0.016)
    viga(bf, C0 + Vector((-0.02, 0.14, 0.014)), C0 + Vector((0.05, 0.2, 0.04)), 0.014)
    peca('cacos_braco', bf, 'amarelo_gasto')
    mangueira(bc, bezier(C0 + Vector((-0.1, -0.02, 0.006)), C0 + Vector((-0.02, 0.1, 0.02)), C0 + Vector((0.08, -0.12, 0.004)), C0 + Vector((0.15, 0.0, 0.006)), 10), 0.004)
    for k in range(10):
        parafuso(bc, C0 + Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0.0)), (0, 0, 1), 0.004)
    peca('cacos_fios', bc, 'cabo_v', liso=True)
    bm = bmesh.new()
    mancha(bm, (C0.x, C0.y), 0.17, DECK + 0.0017)
    peca('cacos_fuligem', bm, 'fuligem')
    # números de série / estêncil nos berços
    bm = bmesh.new()
    for i, B in enumerate(BERCOS):
        digitos(bm, '0%d' % (i + 1), Vector((B.x + 0.18, B.y - 0.04, TOPO_BERCO + 0.0008)), (0, 1, 0), (-1, 0, 0), 0.06, 0.004)
    peca('bercos_numeros', bm, 'tinta_preta')
    return E
