"""Estudo isolado (fora do jogo): BAÚ (1×1, até 0,62 m) e BAÚ GRANDE (2×2, até 0,94 m), o armazém da IA.
Braços colocam e tiram itens por qualquer lado (sem portas fixas no catálogo).
- Contêiner blindado: chapas corrugadas com amassados, montantes e longarinas amarelas gastas com rebites, cantoneiras
  de engate (como contêiner, com furos ovais), sapatas niveladoras sobre a laje, listras de perigo nos cantos.
- Escotilha automática em cada um dos 4 lados: tampa articulada no topo, aberta por dois pistões (camisa no suporte da
  parede, haste na orelha da tampa; mangueira do suporte ao coletor sob a escotilha, que atravessa a parede por colar).
  Sensores de aproximação nos cantos de cada moldura (acendem quando a escotilha trabalha).
- Janela gradeada no teto (vidro sujo + grade) e a escotilha aberta mostram o interior.
- Baú: os itens FLUTUAM em grade num campo (anéis de levitação violeta), 2 anéis de 8 vagas em volta do núcleo de campo.
- Baú grande: carrossel de 3 andares (lingotes, bobinas, cristais) com coroa e motor; ponte rolante interna no teto com
  mastro telescópico e garra de 4 dedos que arruma; gaveteiros no oeste (uma gaveta corre); campo flutuante no nordeste;
  unidade hidráulica no sudeste (motor, reservatório, coletor, canos até o piso). Barramento de cobre no trilho.
- Barra de luz de ocupação no topo de cada face, antena pequena com luz no topo, caixa de junção, exaustor no grande.
Animação (laço de 4 s):
  baú: escotilha sul abre, um item entra puxado pelo campo (anéis), escotilha fecha; escotilha norte abre e um item sai;
       a grade de itens se reorganiza (anel de cima meia-volta, de baixo dois passos ao contrário).
  grande: item entra pela escotilha sul até a prateleira; a garra o pega e põe no carrossel; o carrossel gira um passo;
       a garra tira o item que chegou e leva à prateleira leste; ele sai pela escotilha leste. Campo NE se reorganiza.
Uso: blender -b --python estudo_baus.py -- foto [bau_0 bau_perto bau_grande_0 bau_grande_perto baus_juntos]
     blender -b --python estudo_baus.py -- teste x y z ax ay az lente quadro quem(bau|grande|ambos)"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(23)
UP = Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=40, nr=10, rot=Matrix.Identity(3)):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + rot @ (d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, Bn = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], Bn[(j + 1) % nr], Bn[j]))


def curva(bm, p, r, lados=14):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r, flange=True):
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        if flange and (b - a).length > 0.12:
            for c in (a + u * 0.03, b - u * 0.03):
                tubo(bf, c - u * 0.005, c + u * 0.005, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def jan(fr, a, b):
    return suave((fr - a) / (b - a))


COL = [None]


def mover(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    COL[0].objects.link(o)
    return o


def ob(nome, bm, mat, pai=None, liso=False):
    o = base3d.obj(nome, bm, mat, pai)
    mover(o)
    return suavizar(o) if liso else o


def vazio(nome, pai=None):
    e = bpy.data.objects.new(nome, None)
    COL[0].objects.link(e)
    if pai is not None:
        e.parent = pai
    return e


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def cristal_mat():
    m = bpy.data.materials.new('Cristal')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.22, 0.06, 0.65, 1)
    b.inputs['Roughness'].default_value = 0.15
    b.inputs['Transmission Weight'].default_value = 0.45
    b.inputs['IOR'].default_value = 1.6
    b.inputs['Emission Color'].default_value = (0.5, 0.18, 1.0, 1)
    b.inputs['Emission Strength'].default_value = 1.8
    return m


def vidro_sujo_mat():
    """Vidro da janela do teto: translúcido, com poeira e marcas de chuva (fosco em manchas)."""
    m = bpy.data.materials.new('Vidro sujo')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.5, 0.48, 0.44, 1)
    b.inputs['Transmission Weight'].default_value = 0.92
    b.inputs['IOR'].default_value = 1.45
    no = mats.no
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    r = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.7, 'To Min': 0.04, 'To Max': 0.45})
    nt.links.new(ru.outputs['Fac'], r.inputs['Value'])
    nt.links.new(r.outputs['Result'], b.inputs['Roughness'])
    return m


def empoeirar(m, z_lama=0.17):
    """Poeira clara nas faces de cima (manchada) e lama escura subindo do pé (posição no mundo)."""
    nt = m.node_tree
    no = mats.no
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = b.inputs['Base Color'].links[0]
    src = lk.from_socket
    nt.links.remove(lk)
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    cima = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.95, 'To Min': 0.0, 'To Max': 0.55})
    nt.links.new(sn.outputs['Z'], cima.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    rm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.35, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], rm.inputs['Value'])
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(cima.outputs['Result'], f.inputs[0])
    nt.links.new(rm.outputs['Result'], f.inputs[1])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[7].default_value = (0.36, 0.32, 0.26, 1)
    nt.links.new(f.outputs['Value'], mix.inputs[0])
    nt.links.new(src, mix.inputs[6])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    lama = no(nt, 'ShaderNodeMapRange', **{'From Min': z_lama, 'From Max': 0.03, 'To Min': 0.0, 'To Max': 0.8})
    nt.links.new(sp.outputs['Z'], lama.inputs['Value'])
    ru2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], ru2.inputs['Vector'])
    f2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(lama.outputs['Result'], f2.inputs[0])
    nt.links.new(ru2.outputs['Fac'], f2.inputs[1])
    f2b = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    f2b.inputs[1].default_value = 1.6
    nt.links.new(f2.outputs['Value'], f2b.inputs[0])
    mix2 = no(nt, 'ShaderNodeMix', data_type='RGBA', clamp_factor=True)
    mix2.inputs[7].default_value = (0.075, 0.055, 0.035, 1)
    nt.links.new(f2b.outputs['Value'], mix2.inputs[0])
    nt.links.new(mix.outputs[2], mix2.inputs[6])
    nt.links.new(mix2.outputs[2], b.inputs['Base Color'])
    return m


def ferrugem_mat():
    """Escorrido de ferrugem: laranja-marrom fosco que some para baixo (posição local z do objeto não serve: usa ruído)."""
    m = mats.material('Escorrido', (0.30, 0.11, 0.03), 0, 0.95, pintura=False, sujeira=0.4, desgaste=0.0)
    return m


VIOLETA = (0.6, 0.3, 1.0)
AMBAR = (1.0, 0.42, 0.04)
M = base3d.M
M.update({
    'amarelo': empoeirar(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.85, ferrugem=0.45)),
    'parede': empoeirar(mats.material('Parede', (0.15, 0.18, 0.2), 0, 0.5, desgaste=0.85, sujeira=0.9, ferrugem=0.7)),
    'grafite': empoeirar(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3)),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.6, sujeira=0.8, escovado=True),
    'ferro': empoeirar(mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9)),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.78, 0.40, 0.22), 1.0, 0.3, pintura=False, sujeira=0.6),
    'lingote': mats.material('Lingote', (0.55, 0.56, 0.6), 1.0, 0.25, pintura=False, sujeira=0.2),
    'borracha': mats.material('Borracha', (0.02, 0.02, 0.022), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
    'buraco': mats.material('Buraco', (0.01, 0.01, 0.01), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'po': mats.material('Pó', (0.30, 0.27, 0.22), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'escorrido': ferrugem_mat(),
    'listras': base3d.listras_mat(),
    'cristal': cristal_mat(),
    'vidro': vidro_sujo_mat(),
    'halo': emissivo('Halo', (0.45, 0.15, 1.0), 3.0),
    'feixe': emissivo('Feixe', (0.45, 0.15, 1.0), 1.6),
    'campo': emissivo('Campo', (0.45, 0.15, 1.0), 0.9, base=(0.05, 0.02, 0.1)),
    'barra_on': emissivo('Barra acesa', AMBAR, 9.0),
    'barra_off': emissivo('Barra apagada', (0.05, 0.02, 0.0), 0.0, base=(0.03, 0.02, 0.015)),
    'luz_teto': emissivo('Luz do teto', (0.6, 0.35, 1.0), 2.5),
    'ponta': emissivo('Luz da antena', (1.0, 0.1, 0.05), 0.0),
    'zarcao': empoeirar(mats.material('Zarcão', (0.42, 0.11, 0.045), 0, 0.6, desgaste=0.9, sujeira=0.9, ferrugem=0.5)),
    'remendo': empoeirar(mats.material('Remendo', (0.3, 0.31, 0.27), 0.6, 0.55, pintura=False, desgaste=0.8, sujeira=0.9, ferrugem=0.9)),
    'solda': mats.material('Solda', (0.08, 0.07, 0.06), 0.9, 0.6, pintura=False, ferrugem=0.8, sujeira=0.8),
    'fuligem': mats.material('Fuligem', (0.012, 0.011, 0.011), 0, 0.97, pintura=False, sujeira=0.0, desgaste=0.0),
    'fio_r': mats.material('Fio vermelho', (0.4, 0.03, 0.02), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'fio_a': mats.material('Fio amarelo', (0.6, 0.45, 0.03), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'fio_z': mats.material('Fio azul', (0.03, 0.1, 0.4), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'cobre_nu': mats.material('Cobre nu', (0.85, 0.45, 0.25), 1.0, 0.25, pintura=False, sujeira=0.3),
})


def estencil_mat():
    """Tinta de estêncil branca gasta: some em manchas (número de série quase apagado)."""
    m = bpy.data.materials.new('Estêncil')
    nt = m.node_tree
    no = mats.no
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
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.18, 'From Max': 0.3, 'To Min': 0.0, 'To Max': 0.8})
    nt.links.new(mul.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


M['estencil'] = estencil_mat()
for k in ('halo', 'campo', 'barra_on', 'luz_teto'):
    M[k].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.4


def mat_animado(nome, cor, base=None):
    m = emissivo(nome, cor, 0.0, base=base or (0.03, 0.02, 0.015))
    M[nome] = m
    return m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


def decal_mat(nome, cor, rough, metal=0.0):
    """Mancha que se desfaz na borda: alfa do atributo 'Col' (pintado na malha) × ruído."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
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


M['fuligem_s'] = decal_mat('Fuligem suave', (0.01, 0.009, 0.009), 0.97)
M['oleo_s'] = decal_mat('Óleo suave', (0.008, 0.006, 0.004), 0.08)
M['po_s'] = decal_mat('Pó suave', (0.32, 0.29, 0.24), 0.95)
M['escorrido_s'] = decal_mat('Ferrugem escorrida', (0.28, 0.09, 0.025), 0.95)


def _cor(bm):
    return bm.loops.layers.color.get('Col') or bm.loops.layers.color.new('Col')


def _face(bm, vs, alfas):
    lay = _cor(bm)
    f = bm.faces.new(vs)
    for lp in f.loops:
        lp[lay] = (1, 1, 1, alfas[lp.vert])


def mancha_suave(bm, c, r, z, a0=0.95):
    """Mancha horizontal irregular com borda que some (centro denso, anel médio, borda transparente)."""
    n = 18
    fase = random.uniform(0, 6)
    alf = {}
    cen = bm.verts.new((c[0], c[1], z))
    alf[cen] = a0
    aneis = []
    for f, a in ((0.5, a0 * 0.85), (1.0, 0.0)):
        anel = []
        for k in range(n):
            ang = k * 2 * PI / n
            rr = r * f * (1 + 0.3 * math.sin(3 * ang + fase) + 0.15 * math.sin(5 * ang + fase * 2))
            v = bm.verts.new((c[0] + math.cos(ang) * rr, c[1] + math.sin(ang) * rr, z))
            alf[v] = a
            anel.append(v)
        aneis.append(anel)
    for k in range(n):
        _face(bm, (cen, aneis[0][k], aneis[0][(k + 1) % n]), alf)
        _face(bm, (aneis[0][k], aneis[1][k], aneis[1][(k + 1) % n], aneis[0][(k + 1) % n]), alf)


def faixa_suave(bm, topo, base, lat, a0=0.9, seg=6):
    """Escorrido vertical: cheio no topo, afinando e sumindo embaixo (lat = meia largura, vetor)."""
    alf = {}
    fila = []
    for i in range(seg + 1):
        t = i / seg
        p = Vector(topo).lerp(Vector(base), t)
        w = lat * (1.0 - 0.55 * t) * (1 + 0.25 * math.sin(i * 2.1))
        a, b = bm.verts.new(p - w), bm.verts.new(p + w)
        alf[a] = alf[b] = a0 * (1 - t) ** 0.8
        fila.append((a, b))
    for (a, b), (c, d) in zip(fila, fila[1:]):
        _face(bm, (a, b, d, c), alf)


# ------------------------------------------------------------------ itens (as mercadorias)
MEIA = {'lingote': 0.0125, 'engrenagem': 0.031, 'bobina': 0.031, 'cristal': 0.036}


def item(tipo, esc=1.0, halo=False, pai=None):
    """Item com origem no centro. Engrenagem fica em pé (eixo x) para ler de lado."""
    e = vazio('item_' + tipo, pai)
    e.rotation_mode = 'QUATERNION'
    S = Matrix.Scale(esc, 4)
    if tipo == 'lingote':
        bm = bmesh.new()
        vs = caixa(bm, (0, 0, 0), (0.07, 0.036, 0.025))
        for v in vs:
            if v.co.z > 0:
                v.co.x *= 0.8
                v.co.y *= 0.72
        bm.transform(S)
        ob('lingote', bm, 'lingote', e)
    elif tipo == 'engrenagem':
        bm, bb = bmesh.new(), bmesh.new()
        cil(bm, Vector((0, 0, 0)), 0.024, 0.014, Vector((1, 0, 0)), lados=24)
        for k in range(12):
            a = k * 2 * PI / 12
            caixa(bm, (0, 0.027 * math.cos(a), 0.027 * math.sin(a)), (0.014, 0.008, 0.008), Matrix.Rotation(a, 3, 'X'))
        cil(bb, Vector((0, 0, 0)), 0.008, 0.0145, Vector((1, 0, 0)), lados=12)
        bm.transform(S)
        bb.transform(S)
        ob('engrenagem', bm, 'aco', e)
        ob('engrenagem_furo', bb, 'buraco', e)
    elif tipo == 'bobina':
        bm, bf = bmesh.new(), bmesh.new()
        cil(bm, Vector((0, 0, 0)), 0.022, 0.05, lados=20)
        for z in (-0.028, 0.028):
            cil(bf, Vector((0, 0, z)), 0.029, 0.006, lados=20)
        cil(bf, Vector((0, 0, 0.0)), 0.007, 0.063, lados=10)
        bm.transform(S)
        bf.transform(S)
        ob('bobina', bm, 'cobre', e, liso=True)
        ob('bobina_carretel', bf, 'grafite', e)
    else:
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.018, radius2=0.0, depth=0.03,
                              matrix=Matrix.Translation((0, 0, 0.021)))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.018, radius2=0.018, depth=0.012)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0, radius2=0.018, depth=0.03,
                              matrix=Matrix.Translation((0, 0, -0.021)))
        bm.transform(S)
        ob('cristal', bm, 'cristal', e)
    if halo:
        bm = bmesh.new()
        toro(bm, Vector((0, 0, -(MEIA[tipo] + 0.014) * esc)), 0.03 * esc, 0.0022, 32, 6)
        h = ob('halo', bm, 'halo', e)
        h['halo'] = True
    return e


# ------------------------------------------------------------------ o contêiner
LADOS = {'S': Vector((0, -1, 0)), 'N': Vector((0, 1, 0)), 'L': Vector((1, 0, 0)), 'O': Vector((-1, 0, 0))}


def quadro(n):
    t = Vector((n.y, -n.x, 0))
    return Matrix((t, n, UP)).transposed()


def perfil(u, uref, per, dd):
    ph = ((u - uref) / per) % 1.0
    if ph < 0.35:
        return 0.0
    if ph < 0.5:
        return dd * (ph - 0.35) / 0.15
    if ph < 0.85:
        return dd
    return dd * (1 - (ph - 0.85) / 0.15)


def chapa(bm, C, R, v_out, dd, per, u0, u1, z0, z1, amass, uref=0.0):
    """Chapa corrugada vertical (ondas trapezoidais ao longo de u) entre u0..u1 e z0..z1, com amassados (para dentro)."""
    us = {u0, u1}
    k0 = math.floor((u0 - uref) / per) - 1
    for k in range(k0, k0 + int((u1 - u0) / per) + 4):
        for f in (0.0, 0.35, 0.5, 0.85):
            u = uref + (k + f) * per
            if u0 < u < u1:
                us.add(u)
    us = sorted(us)
    n = max(2, int(math.ceil((z1 - z0) / 0.022)))
    zs = [z0 + (z1 - z0) * i / n for i in range(n + 1)]

    def amassado(u, z):
        s = 0.0
        for (ua, za, ra, pa) in amass:
            s += pa * math.exp(-((u - ua) ** 2 + (z - za) ** 2) / (ra * ra))
        return s
    grade = [[bm.verts.new(C + R @ Vector((u, v_out - perfil(u, uref, per, dd) - amassado(u, z), z))) for z in zs] for u in us]
    for i in range(len(us) - 1):
        for j in range(len(zs) - 1):
            bm.faces.new((grade[i][j], grade[i + 1][j], grade[i + 1][j + 1], grade[i][j + 1]))


class Bau:
    def __init__(self, nome, C, P):
        self.nome, self.C, self.P = nome, Vector((C[0], C[1], 0)), P
        self.bms = {}
        self.anim = []             # funções f(q, fr) chamadas a cada quadro
        self.tampas = {}
        self.sensores = {}
        self.paredes = {}

    def B(self, nome, mat, liso=False):
        k = (nome, mat, liso)
        if k not in self.bms:
            self.bms[k] = bmesh.new()
        return self.bms[k]

    def fechar(self):
        for (nome, mat, liso), bm in self.bms.items():
            ob(self.nome + '_' + nome, bm, mat, liso=liso)
        self.bms = {}

    def W(self, x, y, z):
        return self.C + Vector((x, y, z))

    # -------------------------------------------------------------- casca
    def casca(self):
        P, C = self.P, self.C
        W2, D2 = P['W'] / 2, P['D'] / 2
        Zl, Z0, Z1, cp, rl, cc = P['Zl'], P['Z0'], P['Z1'], P['cp'], P['rail'], P['cc']
        T = P['T'] / 2
        # laje com listras na borda, poeira e óleo
        caixa_de(self.B('laje', 'concreto'), self.W(-T, -T, 0), self.W(T, T, Zl))
        bl = self.B('laje_listras', 'listras')
        e = 0.05 * P['T']
        for a, b in (((-T, -T), (T, -T + e)), ((-T, T - e), (T, T)), ((-T, -T + e), (-T + e, T - e)), ((T - e, -T + e), (T, T - e))):
            caixa_de(bl, self.W(a[0], a[1], Zl - 0.004), self.W(b[0], b[1], Zl + 0.0015))
        for k in range(10):
            ang = random.uniform(0, 2 * PI)
            r = random.uniform(0.75, 1.0)
            mancha_suave(self.B('po_s', 'po_s'), (C.x + math.cos(ang) * W2 * r * 1.05, C.y + math.sin(ang) * D2 * r * 1.05), random.uniform(0.06, 0.12) * P['T'], Zl + 0.0012, 0.8)
        for k in range(26):
            pedra(self.B('cascalho', 'concreto'), self.W(random.uniform(-T, T) * 0.95, random.uniform(-T, T) * 0.95, Zl + 0.003), random.uniform(0.004, 0.009), 0.5)
        # montantes, longarinas, cantoneiras de engate e sapatas
        ba, bf, bb, br = self.B('quadro', 'amarelo'), self.B('ferro', 'ferro'), self.B('buraco', 'buraco'), self.B('rebites', 'aco')
        for sx in (-1, 1):
            for sy in (-1, 1):
                caixa_de(ba, self.W(sx * W2, sy * D2, Z0 + cc * 0.8), self.W(sx * (W2 - cp), sy * (D2 - cp), Z1 - cc * 0.8))
                for zc in (Z0 + cc * 0.4, Z1 - cc * 0.4):        # cantoneira (casting) com furos ovais nas 3 faces
                    c = self.W(sx * (W2 - cc / 2 + 0.003), sy * (D2 - cc / 2 + 0.003), zc)
                    caixa(bf, c, (cc, cc, cc * 0.8))
                    caixa(bb, c + Vector((sx * (cc / 2 + 0.0005), 0, 0)), (0.002, cc * 0.32, cc * 0.42))
                    caixa(bb, c + Vector((0, sy * (cc / 2 + 0.0005), 0)), (cc * 0.5, 0.002, cc * 0.3))
                    dz = 1 if zc > Z0 + cc else -1
                    caixa(bb, c + Vector((0, 0, dz * (cc * 0.4 + 0.0005))), (cc * 0.5, cc * 0.3, 0.002))
                # sapata niveladora: placa na laje, fuso, porca sextavada
                c = self.W(sx * (W2 - cc / 2), sy * (D2 - cc / 2), 0)
                caixa(bf, c + Vector((0, 0, Zl + 0.005)), (cc * 1.35, cc * 1.35, 0.01))
                cil(self.B('fuso', 'aco'), c + Vector((0, 0, (Zl + Z0) / 2)), cc * 0.18, Z0 - Zl, lados=12)
                cil(bf, c + Vector((0, 0, Zl + 0.017)), cc * 0.32, 0.012, lados=6)
                cil(bf, c + Vector((0, 0, Z0 - 0.006)), cc * 0.4, 0.008, lados=6)
                for k in range(4):
                    a = k * PI / 2 + PI / 4
                    cil(br, c + Vector((math.cos(a) * cc * 0.55, math.sin(a) * cc * 0.55, Zl + 0.011)), 0.004, 0.006, lados=6)
                # listras de perigo nos montantes (duas faces de fora)
                z0l, z1l = Z0 + cc * 0.85, Z0 + cc * 0.85 + P['H'] * 0.3
                caixa_de(self.B('listras', 'listras'), self.W(sx * (W2 + 0.0015), sy * (D2 - cp), z0l), self.W(sx * (W2 - 0.0005), sy * D2, z1l))
                caixa_de(self.B('listras', 'listras'), self.W(sx * (W2 - cp), sy * (D2 + 0.0015), z0l), self.W(sx * W2, sy * (D2 - 0.0005), z1l))
                # escorridos de ferrugem descendo da cantoneira de cima
                for k in range(2):
                    zz = Z1 - cc * 0.8 - random.uniform(0.0, 0.03)
                    L = random.uniform(0.06, 0.16) * P['H'] / 0.47
                    off = random.uniform(-0.3, 0.3) * cp
                    if k == 0:
                        faixa_suave(self.B('escorrido_s', 'escorrido_s'), self.W(sx * (W2 + 0.0012), sy * (D2 - cp / 2) + off, zz), self.W(sx * (W2 + 0.0012), sy * (D2 - cp / 2) + off, zz - L), Vector((0, cp * 0.12, 0)))
                    else:
                        faixa_suave(self.B('escorrido_s', 'escorrido_s'), self.W(sx * (W2 - cp / 2) + off, sy * (D2 + 0.0012), zz), self.W(sx * (W2 - cp / 2) + off, sy * (D2 + 0.0012), zz - L), Vector((cp * 0.12, 0, 0)))
        for z0, z1 in ((Z0, Z0 + rl), (Z1 - rl, Z1)):         # longarinas de cima e de baixo, com rebites
            for sy in (-1, 1):
                caixa_de(ba, self.W(-(W2 - cc), sy * D2, z0), self.W(W2 - cc, sy * (D2 - cp * 0.8), z1))
                n = int((P['W'] - 2 * cc) / 0.07)
                for k in range(n + 1):
                    x = -(W2 - cc) + 0.02 + k * (P['W'] - 2 * cc - 0.04) / n
                    cil(br, self.W(x, sy * (D2 + 0.0015), (z0 + z1) / 2), 0.0038, 0.004, Vector((0, 1, 0)), lados=6)
            for sx in (-1, 1):
                caixa_de(ba, self.W(sx * W2, -(D2 - cc), z0), self.W(sx * (W2 - cp * 0.8), D2 - cc, z1))
                n = int((P['D'] - 2 * cc) / 0.07)
                for k in range(n + 1):
                    y = -(D2 - cc) + 0.02 + k * (P['D'] - 2 * cc - 0.04) / n
                    cil(br, self.W(sx * (W2 + 0.0015), y, (z0 + z1) / 2), 0.0038, 0.004, Vector((1, 0, 0)), lados=6)
        # piso (chapa xadrez escura) e teto com janela gradeada
        caixa_de(self.B('piso', 'ferro'), self.W(-(W2 - cp * 0.8), -(D2 - cp * 0.8), Z0), self.W(W2 - cp * 0.8, D2 - cp * 0.8, P['Zf']))
        jx, jy = P['jan'][0] / 2, P['jan'][1] / 2
        zt0, zt1 = Z1 - 0.02, Z1 - 0.008
        xi, yi = W2 - cp * 0.8, D2 - cp * 0.8
        bt = self.B('teto', 'parede')
        for a, b in (((-xi, -yi), (xi, -jy)), ((-xi, jy), (xi, yi)), ((-xi, -jy), (-jx, jy)), ((jx, -jy), (xi, jy))):
            caixa_de(bt, self.W(a[0], a[1], zt0), self.W(b[0], b[1], zt1))
        for sx in (-1, 1):                                       # nervuras do teto fora da janela
            for k in range(3):
                x = sx * (jx + (xi - jx) * (k + 0.5) / 3)
                caixa_de(bt, self.W(x - 0.008, -yi, zt1), self.W(x + 0.008, yi, zt1 + 0.006))
        # janela: aro, vidro sujo e grade
        bg = self.B('grade', 'grafite')
        a = 0.02 * P['T']
        for p0, p1 in (((-jx - a, -jy - a), (jx + a, -jy)), ((-jx - a, jy), (jx + a, jy + a)), ((-jx - a, -jy), (-jx, jy)), ((jx, -jy), (jx + a, jy))):
            caixa_de(bg, self.W(p0[0], p0[1], zt0), self.W(p1[0], p1[1], zt1 + 0.012))
        caixa_de(self.B('vidro', 'vidro'), self.W(-jx, -jy, zt0 + 0.004), self.W(jx, jy, zt0 + 0.008))
        nb = int(P['jan'][0] / 0.05)
        for k in range(1, nb):
            x = -jx + k * P['jan'][0] / nb
            caixa_de(bg, self.W(x - 0.004, -jy, zt1 + 0.004), self.W(x + 0.004, jy, zt1 + 0.012))
        for k in range(1, 3):
            y = -jy + k * P['jan'][1] / 3
            caixa_de(bg, self.W(-jx, y - 0.006, zt1 + 0.004), self.W(jx, y + 0.006, zt1 + 0.014))
        # paredes corrugadas com o vão da escotilha
        for lado, n in LADOS.items():
            R = quadro(n)
            hn = D2 if abs(n.y) > 0.5 else W2
            ht = W2 if abs(n.y) > 0.5 else D2
            v_out = hn - 0.006
            u_max = ht - cp
            za, zb = Z0 + rl, Z1 - rl
            hw, fw = P['hw'] / 2, P['fw']
            amass = []
            for k in range(random.choice((2, 3, 3, 4))):
                amass.append((random.uniform(-u_max, u_max) * 0.9, random.uniform(za + 0.05, zb - 0.05),
                              random.uniform(0.03, 0.07) * P['T'], random.uniform(0.008, 0.02) * P['T']))
            bw = self.B('parede', 'parede')
            g = hw + fw * 0.5
            chapa(bw, C, R, v_out, P['dd'], P['per'], -u_max, -g, za, zb, amass)
            chapa(bw, C, R, v_out, P['dd'], P['per'], g, u_max, za, zb, amass)
            chapa(bw, C, R, v_out, P['dd'], P['per'], -g, g, za, P['hz0'] - fw * 0.5, amass)
            chapa(bw, C, R, v_out, P['dd'], P['per'], -g, g, P['hz1'] + fw * 0.5, zb, amass)
            self.paredes[lado] = (R, v_out, amass, u_max, za, zb)
            self.escotilha(lado, n, R, v_out)

    # -------------------------------------------------------------- escotilha automática
    def escotilha(self, lado, n, R, v_out):
        P, C = self.P, self.C
        hw, fw, hz0, hz1, dd = P['hw'] / 2, P['fw'], P['hz0'], P['hz1'], P['dd']
        Lw = lambda u, v, z: C + R @ Vector((u, v, z))
        fo = v_out + 0.012 * P['T'] ** 0.5                       # face de fora da moldura
        bm = self.B('moldura', 'grafite')
        vi = v_out - dd - 0.006
        for u0, u1, z0, z1 in ((-hw - fw, hw + fw, hz0 - fw, hz0), (-hw - fw, hw + fw, hz1, hz1 + fw),
                               (-hw - fw, -hw, hz0, hz1), (hw, hw + fw, hz0, hz1)):
            a, b = R @ Vector((u0, vi, z0)), R @ Vector((u1, fo, z1))
            caixa_de(bm, C + Vector((min(a.x, b.x), min(a.y, b.y), z0)), C + Vector((max(a.x, b.x), max(a.y, b.y), z1)))
        # dobradiça: eixo no topo da moldura
        zh = hz1 + fw * 0.5
        vh = fo + 0.011 * P['T'] ** 0.5
        rh = 0.008 * P['T'] ** 0.5
        bf = self.B('ferro', 'ferro')
        for su in (-1, 1):
            cil(bf, Lw(su * (hw + fw * 0.5), vh, zh), rh, fw * 0.9, R @ Vector((1, 0, 0)), lados=12)
            a, b = Lw(su * (hw + fw * 0.5) - fw * 0.45, fo - 0.002, zh - rh * 0.9), Lw(su * (hw + fw * 0.5) + fw * 0.45, vh, zh + rh * 0.9)
            caixa_de(bf, Vector((min(a.x, b.x), min(a.y, b.y), a.z)), Vector((max(a.x, b.x), max(a.y, b.y), b.z)))
        # tampa (filha do pivô; local: x = tangente, y = normal, z = cima; gira em x)
        piv = vazio(self.nome + '_tampa_' + lado)
        piv.location = Lw(0, vh, zh)
        piv.rotation_mode = 'QUATERNION'
        Rq = R.to_quaternion()
        piv.rotation_quaternion = Rq
        hf = zh - hz0 + fw * 0.6                                 # altura da tampa
        wf = hw + fw * 0.75
        te = 0.008 * P['T'] ** 0.5
        bt, bg, bl = bmesh.new(), bmesh.new(), bmesh.new()
        caixa_de(bt, (-wf, -te, -hf), (wf, te, -rh * 0.6))
        for z in (-hf * 0.36, -hf * 0.7):                        # reforços horizontais
            caixa_de(bt, (-wf * 0.92, te, z - te), (wf * 0.92, te * 2.4, z + te))
        for su in (-1, 1):
            caixa_de(bt, (su * wf - su * te * 2.2 - te, te, -hf), (su * wf - su * te * 2.2 + te, te * 2.4, -rh))
        cil(bg, Vector((0, 0, 0)), rh, 2 * hw - 0.004, Vector((1, 0, 0)), lados=12)   # junta da dobradiça na tampa
        caixa_de(bl, (-wf * 0.92, te * 2.4 - 0.001, -hf + te * 0.4), (wf * 0.92, te * 2.4 + 0.0015, -hf + hf * 0.16))
        ob(self.nome + '_tampa', bt, 'zarcao' if P.get('trocada') == lado else 'amarelo', piv)
        if P.get('trocada') != lado:                             # placa de identificação rebitada, número apagado
            bp = bmesh.new()
            caixa_de(bp, (-wf * 0.55, te, -hf * 0.33 + te * 1.3), (-wf * 0.12, te + 0.002, -hf * 0.33 + te * 1.3 + hf * 0.13))
            ob(self.nome + '_tampa_placa', bp, 'aco', piv)
            texto(self.nome + '_tampa_num', 'Nº %s-%02d' % (self.nome.upper()[:2], random.randint(10, 99)), hf * 0.07,
                  Vector((-wf * 0.53, te + 0.0028, -hf * 0.33 + te * 1.3 + hf * 0.035)), Vector((0, 1, 0)), piv)
        ob(self.nome + '_tampa_junta', bg, 'ferro', piv)
        ob(self.nome + '_tampa_listras', bl, 'listras', piv)
        # sensor ótico no meio da tampa (vê o braço chegando)
        bs = bmesh.new()
        cil(bs, Vector((0, te * 2.4 + 0.006, -hf * 0.53)), 0.016 * P['T'] ** 0.5, 0.012, Vector((0, 1, 0)), lados=16)
        ob(self.nome + '_tampa_sensor', bs, 'grafite', piv)
        bs = bmesh.new()
        bmesh.ops.create_uvsphere(bs, u_segments=12, v_segments=6, radius=0.009 * P['T'] ** 0.5,
                                  matrix=Matrix.Translation((0, te * 2.4 + 0.012, -hf * 0.53)))
        forca_s = mat_animado(self.nome + '_sensor_' + lado, VIOLETA)
        ob(self.nome + '_tampa_lente', bs, self.nome + '_sensor_' + lado, piv)
        # pistões: escolhe orelha (fração da tampa) e suporte para curso viável (Lmax ≤ 1,75 Lmin)
        th = math.radians(P['abre'])
        za = P['Zf'] + 0.03 * P['T'] ** 0.5 - zh
        xl = hw + fw + 0.026 * P['T'] ** 0.5
        melhor = None
        for f in [0.12 + 0.02 * i for i in range(25)]:
            for ya in (0.0, 0.01, 0.02, 0.03):
                lug0 = Vector((0, 0, -f * hf))
                lug1 = Vector((0, f * hf * math.sin(th), -f * hf * math.cos(th)))
                anc = Vector((0, ya, za))
                L0, L1 = (lug0 - anc).length, (lug1 - anc).length
                if L1 <= 1.75 * L0 and (melhor is None or f > melhor[0]):
                    melhor = (f, ya, L0, L1)
        f, ya, L0, L1 = melhor
        rc = 0.012 * P['T'] ** 0.5
        Lc = L0 - 0.01
        Lr = L1 - Lc + 0.02
        bo = bmesh.new()
        for su in (-1, 1):                                       # orelhas da tampa
            caixa_de(bo, (su * wf if su > 0 else -xl - 0.008, -te, -f * hf - 0.012), (xl + 0.008 if su > 0 else -wf, te, -f * hf + 0.012))
            cil(bo, Vector((su * xl, 0, -f * hf)), 0.006, 0.026, Vector((1, 0, 0)), lados=8)
        ob(self.nome + '_tampa_orelhas', bo, 'ferro', piv)
        pist = []
        for su in (-1, 1):
            anc_l = Vector((su * xl, ya, za))
            anc_w = piv.location + R @ anc_l
            # suporte (olhal) na parede: bloco preso nas cristas da corrugação até o pino
            u_s = su * xl
            a = Lw(u_s - 0.016, v_out - 0.002, zh + za - 0.02)
            b = Lw(u_s + 0.016, vh + ya + 0.012, zh + za + 0.016)
            caixa_de(bf, Vector((min(a.x, b.x), min(a.y, b.y), a.z)), Vector((max(a.x, b.x), max(a.y, b.y), b.z)))
            cil(bf, anc_w, 0.007, 0.04, R @ Vector((1, 0, 0)), lados=8)
            bm = bmesh.new()
            cil(bm, Vector((0, 0, Lc / 2)), rc, Lc - 0.008, lados=14)
            cil(bm, Vector((0, 0, Lc - 0.004)), rc * 1.25, 0.012, lados=14)
            cil(bm, Vector((0, 0, 0.008)), rc * 1.2, 0.016, lados=14)
            cil(bm, Vector((rc * 0.9, 0, 0.026)), rc * 0.45, rc * 0.9, Vector((1, 0, 0)), lados=8)   # porta da mangueira
            cam = ob(self.nome + '_pistao_camisa', bm, 'amarelo', liso=True)
            cam.rotation_mode = 'QUATERNION'
            bm = bmesh.new()
            cil(bm, Vector((0, 0, Lr / 2)), rc * 0.5, Lr, lados=12)
            cil(bm, Vector((0, 0, 0)), rc * 0.85, 0.02, Vector((1, 0, 0)), lados=10)
            has = ob(self.nome + '_pistao_haste', bm, 'cromo', liso=True)
            has.rotation_mode = 'QUATERNION'
            pist.append((anc_w, Vector((su * xl, 0, -f * hf)), cam, has, su))
        # coletor hidráulico sob a escotilha + mangueiras dos suportes + colar atravessando a parede
        zc0 = P['Zf'] + 0.004
        zc1 = hz0 - fw - 0.004
        hc = zc1 - zc0
        a, b = Lw(-0.04 * P['T'], v_out - 0.002, zc0), Lw(0.04 * P['T'], v_out + 0.024 * P['T'] ** 0.5, zc1)
        caixa_de(self.B('coletor', 'grafite'), Vector((min(a.x, b.x), min(a.y, b.y), zc0)), Vector((max(a.x, b.x), max(a.y, b.y), zc1)))
        vm = v_out + 0.012 * P['T'] ** 0.5
        for su in (-1, 1):
            p0 = Lw(su * 0.04 * P['T'], vm, (zc0 + zc1) / 2)
            p3 = Lw(su * (xl - 0.004), vh + ya + 0.006, zh + za - 0.02)
            mangueira(self.B('mangueira', 'borracha'), bezier(p0, p0 + R @ Vector((su * 0.04, 0.02, 0)), p3 + Vector((0, 0, -0.03)), p3, 10), 0.0045 * P['T'] ** 0.5)
            cil(bf, p0, 0.007 * P['T'] ** 0.5, 0.012, R @ Vector((1, 0, 0)), lados=8)
        cil(bf, Lw(0, v_out + 0.026 * P['T'] ** 0.5, (zc0 + zc1) / 2), hc * 0.3, 0.008, R @ Vector((0, 1, 0)), lados=10)  # bujão de dreno
        # vazamento de óleo do coletor
        mancha_suave(self.B('oleo_s', 'oleo_s'), (Lw(0.01, v_out + 0.06, 0).x, Lw(0.01, v_out + 0.06, 0).y), 0.05 * P['T'], P['Zl'] + 0.0015)
        vd = v_out + 0.024 * P['T'] ** 0.5 + 0.0006
        faixa_suave(self.B('oleo_s', 'oleo_s'), Lw(0.01, vd, zc0 + hc * 0.3), Lw(0.01, vd, zc0 - 0.004), R @ Vector((0.006, 0, 0)))
        # sensores de aproximação nos cantos de baixo da moldura
        for su in (-1, 1):
            p = Lw(su * (hw + fw * 0.5), fo + 0.005, hz0 - fw * 0.5)
            cil(self.B('sensor_corpo', 'grafite'), p, 0.008 * P['T'] ** 0.5, 0.01, R @ Vector((0, 1, 0)), lados=12)
            bmesh.ops.create_uvsphere(self.B('sensor_lente_' + lado, self.nome + '_sensor_' + lado), u_segments=10, v_segments=6,
                                      radius=0.005 * P['T'] ** 0.5, matrix=Matrix.Translation(p + R @ Vector((0, 0.006, 0))))
        # barra de ocupação na longarina de cima (à direita da escotilha)
        ht = (P['W'] if abs(n.y) > 0.5 else P['D']) / 2
        u0, u1 = hw + fw + 0.07 * P['T'] ** 0.5, ht - P['cc'] - 0.012
        zb = P['Z1'] - P['rail'] / 2
        hb = P['rail'] * 0.42
        hn = (P['D'] if abs(n.y) > 0.5 else P['W']) / 2
        a, b = Lw(u0 - 0.008, hn - 0.004, zb - hb / 2 - 0.006), Lw(u1 + 0.008, hn + 0.006, zb + hb / 2 + 0.006)
        caixa_de(self.B('barra_moldura', 'grafite'), Vector((min(a.x, b.x), min(a.y, b.y), a.z)), Vector((max(a.x, b.x), max(a.y, b.y), b.z)))
        nseg = P['nseg']
        L = (u1 - u0) / nseg
        segs = []
        for k in range(nseg):
            uc = u0 + (k + 0.5) * L
            segs.append((Lw(uc, hn + 0.0068, zb), (L * 0.78, 0.002, hb) if abs(n.y) > 0.5 else (0.002, L * 0.78, hb)))
        self.tampas[lado] = {'piv': piv, 'Rq': Rq, 'pist': pist, 'Lc': Lc, 'th': th, 'forca_s': forca_s, 'segs': segs, 'R': R}

    def barras(self, cheio):
        """Liga os segmentos: `cheio` acesos fixos, o seguinte é o que muda (entra/sai), o resto apagado."""
        self.forca_barra = mat_animado(self.nome + '_barra_var', AMBAR)
        for lado, t in self.tampas.items():
            for k, (p, tam) in enumerate(t['segs']):
                m = 'barra_on' if k < cheio else (self.nome + '_barra_var' if k == cheio else 'barra_off')
                caixa(self.B('barra_' + m, m), p, tam)

    def animar_tampa(self, lado, q, aberta):
        t = self.tampas[lado]
        th = t['th'] * aberta
        rot = t['Rq'] @ Quaternion((1, 0, 0), th)
        piv = t['piv']
        piv.rotation_quaternion = rot
        piv.keyframe_insert('rotation_quaternion', frame=q)
        Mx = rot.to_matrix()
        for anc, lug_l, cam, has, su in t['pist']:
            lug = piv.location + Mx @ lug_l
            d = (lug - anc).normalized()
            cam.location = anc
            cam.rotation_quaternion = d.to_track_quat('Z', 'Y')
            has.location = lug
            has.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
            for o in (cam, has):
                o.keyframe_insert('location', frame=q)
                o.keyframe_insert('rotation_quaternion', frame=q)
        t['forca_s'].default_value = 0.8 + 4.0 * min(1.0, aberta * 3)
        t['forca_s'].keyframe_insert('default_value', frame=q)

    # -------------------------------------------------------------- teto: antena, caixa de junção
    def teto(self):
        P, C = self.P, self.C
        W2, D2 = P['W'] / 2, P['D'] / 2
        zt = P['Z1'] - 0.008
        s = P['T'] ** 0.5
        ax, ay = W2 - P['cc'] - 0.05 * s, D2 - P['cc'] - 0.05 * s
        bg = self.B('teto_peca', 'grafite')
        caixa_de(bg, self.W(ax - 0.025 * s, ay - 0.025 * s, zt), self.W(ax + 0.025 * s, ay + 0.025 * s, zt + 0.014))
        z_top = P['Htot'] - 0.012
        cil(self.B('antena', 'aco'), self.W(ax, ay, (zt + 0.014 + z_top) / 2), 0.0035 * s, z_top - zt - 0.014, lados=8)
        for k in range(3):
            zz = zt + 0.025 + k * (z_top - zt - 0.03) / 3
            cil(self.B('antena_anel', 'ferro'), self.W(ax, ay, zz), 0.008 * s, 0.003, lados=10)
        bmesh.ops.create_uvsphere(self.B('antena_ponta', 'ponta'), u_segments=10, v_segments=6, radius=0.007 * s,
                                  matrix=Matrix.Translation(self.W(ax, ay, z_top + 0.004)))
        # caixa de junção e cabo até a antena e ao prensa-cabo no teto
        jx, jy = ax - 0.12 * s, ay - 0.005
        caixa_de(bg, self.W(jx - 0.035 * s, jy - 0.022 * s, zt), self.W(jx + 0.035 * s, jy + 0.022 * s, zt + 0.03 * s))
        caixa_de(self.B('ferro', 'ferro'), self.W(jx - 0.03 * s, jy - 0.018 * s, zt + 0.03 * s), self.W(jx + 0.03 * s, jy + 0.018 * s, zt + 0.034 * s))
        p0 = self.W(jx + 0.035 * s, jy, zt + 0.012)
        p1 = self.W(ax - 0.025 * s, ay, zt + 0.008)
        mangueira(self.B('cabo', 'borracha'), bezier(p0, p0 + Vector((0.02, 0, 0.01)), p1 + Vector((-0.02, 0, 0.01)), p1, 8), 0.004)
        p0 = self.W(jx - 0.035 * s, jy, zt + 0.01)
        p1 = self.W(jx - 0.09 * s, jy - 0.02, zt + 0.002)
        mangueira(self.B('cabo', 'borracha'), bezier(p0, p0 + Vector((-0.02, 0, 0.012)), p1 + Vector((0.01, 0, 0.01)), p1, 8), 0.004)
        cil(self.B('ferro', 'ferro'), p1, 0.008, 0.008, lados=8)
        self.ponta = M['ponta'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


def texto(nome, corpo, tam, pos, n, pai=None):
    """Texto pintado (estêncil gasto) deitado na face de normal n (local do pai, se houver)."""
    cu = bpy.data.curves.new(nome, 'FONT')
    cu.body = corpo
    cu.size = tam
    cu.materials.append(M['estencil'])
    o = bpy.data.objects.new(nome, cu)
    COL[0].objects.link(o)
    if pai is not None:
        o.parent = pai
    o.location = pos
    o.rotation_euler = (PI / 2, 0, math.atan2(n.y, n.x) - PI / 2 + PI)
    return o


def rustico(b):
    """Carga rústica: remendos aparafusados e soldados, escorridos de óleo e ferrugem nas cristas da corrugação,
    fuligem, fiação exposta saindo do conduíte rasgado, número de série quase apagado nas longarinas."""
    P, C = b.P, b.C
    s = P['T'] ** 0.5
    for i, (lado, (R, v_out, amass, u_max, za, zb)) in enumerate(b.paredes.items()):
        n = LADOS[lado]
        L = lambda u, v, z: C + R @ Vector((u, v, z))
        hw = P['hw'] / 2 + P['fw']
        per = P['per']

        def crista(u):                                           # centro da crista mais próxima
            return round((u - 0.175 * per) / per) * per + 0.175 * per

        def aabb(bm, mat, u0, u1, v0, v1, z0, z1):
            a, c = L(u0, v0, z0), L(u1, v1, z1)
            caixa_de(b.B(bm, mat), Vector((min(a.x, c.x), min(a.y, c.y), z0)), Vector((max(a.x, c.x), max(a.y, c.y), z1)))

        def escorre(mat, u, z_top, comp, larg=0.22):
            uc = crista(u)
            if abs(uc) < hw + 0.03 or abs(uc) > u_max - 0.03:
                return
            for (ua, zd, ra, pa) in amass:
                if abs(uc - ua) < ra * 1.5:
                    return
            z1 = z_top
            z0 = max(za + 0.004, z_top - comp)
            faixa_suave(b.B(mat, mat), L(uc, v_out + 0.0006, z1), L(uc, v_out + 0.0006, z0), R @ Vector((per * larg / 2, 0, 0)))
        # ferrugem escorrendo das longarinas de cima, óleo sob os suportes dos pistões
        for k in range(5 + int(3 * P['T'])):
            escorre('escorrido_s', random.uniform(-u_max, u_max), zb - 0.002, random.uniform(0.08, 0.3) * P['H'] / 0.47)
        for su in (-1, 1):
            xl = P['hw'] / 2 + P['fw'] + 0.026 * s
            uc = crista(su * (xl + per * 0.6))
            if abs(uc) < u_max - 0.03:
                z_a = P['Zf'] + 0.03 * s
                faixa_suave(b.B('oleo_s', 'oleo_s'), L(uc, v_out + 0.0006, z_a + 0.03), L(uc, v_out + 0.0006, za + 0.003), R @ Vector((per * 0.1, 0, 0)))
        # remendo aparafusado (chapa de outra cor sobre um rasgo) em duas faces, com solda numa delas
        if i in (0, 2):
            w, h = 0.11 * s, 0.09 * s
            u = (hw + u_max) / 2 * (1 if i == 0 else -1)
            z = za + (zb - za) * 0.62
            aabb('remendo', 'remendo', u - w / 2, u + w / 2, v_out + 0.0005, v_out + 0.0045, z - h / 2, z + h / 2)
            for du in (-1, 1):
                for dz in (-1, 0, 1):
                    if dz == 0 and i == 2:
                        continue
                    p = L(u + du * (w / 2 - 0.009), v_out + 0.0055, z + dz * (h / 2 - 0.009))
                    cil(b.B('parafuso', 'ferro'), p, 0.0045 * s, 0.004, R @ Vector((0, 1, 0)), lados=6)
            if i == 0:
                aabb('solda', 'solda', u - w / 2 - 0.004, u + w / 2 + 0.004, v_out + 0.0002, v_out + 0.0035, z + h / 2, z + h / 2 + 0.004)
            # buraco de bala / rasgo ao lado do remendo, ferrugem em volta
            p = L(u + w * 0.85 * (1 if i == 0 else -1), v_out - 0.002, z - h * 0.3)
            cil(b.B('buraco', 'buraco'), p, 0.005 * s, 0.006, R @ Vector((0, 1, 0)), lados=8)
            escorre('escorrido_s', u + w * 0.85 * (1 if i == 0 else -1), z - h * 0.3, 0.08 * s)
        # número de série na longarina de baixo, quase apagado
        hn = (P['D'] if abs(n.y) > 0.5 else P['W']) / 2
        if i in (0, 1):
            u_t = -(u_max - 0.02) if True else 0
            texto(b.nome + '_serie', '%s %04d-%s' % ('IA', random.randint(100, 9999), random.choice('ABCDKX')), P['rail'] * 0.5,
                  L(-hw - 0.03, hn + 0.0045, P['Z0'] + P['rail'] * 0.28), n)
    # fiação exposta: conduíte da caixa de junção desce pelo montante sudeste, rasgado no meio, fios soltos até o sensor
    W2, D2 = P['W'] / 2, P['D'] / 2
    x = W2 + 0.006
    y0 = -(D2 - P['cp'] * 0.5)
    zt, zbx = P['Z1'] - P['cc'] * 0.9, P['Z0'] + P['cc'] * 1.1
    zr0, zr1 = zbx + (zt - zbx) * 0.38, zbx + (zt - zbx) * 0.6
    c = lambda z: b.W(x, y0, z)
    tubo(b.B('conduite', 'borracha'), c(zt), c(zr1), 0.007 * s, 10)
    tubo(b.B('conduite', 'borracha'), c(zr0), c(zbx), 0.007 * s, 10)
    for z in (zt - 0.02, zr1 + 0.03, zr0 - 0.03, zbx + 0.03):     # abraçadeiras no montante
        caixa(b.B('ferro', 'ferro'), c(z) + Vector((-0.002, 0, 0)), (0.006, 0.02 * s, 0.006))
    for k, (mat, dy) in enumerate((('fio_r', -0.004), ('fio_a', 0.0), ('fio_z', 0.004))):
        a, d = c(zr1) + Vector((0, dy, 0)), c(zr0) + Vector((0, dy, 0))
        sag = 0.012 + 0.008 * k
        mangueira(b.B('fio' + mat, mat), bezier(a, a + Vector((sag, 0, -0.02)), d + Vector((sag * 0.8, 0, 0.02)), d, 8), 0.0016 * s)
    caixa(b.B('fita', 'borracha'), c(zr1 - 0.004), (0.016 * s, 0.017 * s, 0.01))       # fita isolante remendando
    bmesh.ops.create_icosphere(b.B('cobre_nu', 'cobre_nu'), subdivisions=1, radius=0.003, matrix=Matrix.Translation(c(zr0 + 0.004) + Vector((0.008, 0, 0))))
    # fuligem: em volta da caixa de junção (curto queimou) e escorrendo do coletor hidráulico sul
    zt_ = P['Z1'] - 0.008
    jx = W2 - P['cc'] - 0.05 * s - 0.12 * s
    jy = D2 - P['cc'] - 0.05 * s - 0.005
    mancha_suave(b.B('fuligem_s', 'fuligem_s'), (C.x + jx, C.y + jy), 0.07 * s, zt_ + 0.0012)
    for k in range(3):
        mancha_suave(b.B('fuligem_s', 'fuligem_s'), (C.x + random.uniform(-W2, W2) * 0.6, C.y + random.uniform(-D2, -D2 * 0.5)), random.uniform(0.04, 0.08) * s, zt_ + 0.001, 0.6)


# ------------------------------------------------------------------ BAÚ 1×1
P_BAU = dict(T=1.0, W=0.80, D=0.74, Zl=0.035, Z0=0.075, Z1=0.54, cp=0.04, rail=0.035, cc=0.05, per=0.07, dd=0.01,
             hw=0.28, hz0=0.17, hz1=0.42, fw=0.022, jan=(0.30, 0.24), Htot=0.62, abre=110, nseg=8)
P_BAU['Zf'] = P_BAU['Z0'] + P_BAU['rail']
P_BAU['trocada'] = 'O'
P_BAU['H'] = P_BAU['Z1'] - P_BAU['Z0']
P_GR = dict(T=2.0, W=1.76, D=1.68, Zl=0.04, Z0=0.085, Z1=0.84, cp=0.065, rail=0.05, cc=0.08, per=0.10, dd=0.016,
            hw=0.50, hz0=0.30, hz1=0.62, fw=0.035, jan=(0.80, 0.66), Htot=0.94, abre=110, nseg=10)
P_GR['Zf'] = P_GR['Z0'] + P_GR['rail']
P_GR['trocada'] = 'N'
P_GR['H'] = P_GR['Z1'] - P_GR['Z0']

C_BAU = (-1.0, -0.5)
C_GR = (0.5, 0.0)

col_bau = bpy.data.collections.new('bau')
sc.collection.children.link(col_bau)
col_gr = bpy.data.collections.new('bau_grande')
sc.collection.children.link(col_gr)

# ================================================================== baú pequeno
COL[0] = col_bau
bau = Bau('bau', C_BAU, P_BAU)
bau.casca()
bau.teto()
rustico(bau)
bau.barras(5)
Cb = bau.C
# interior: emissor de campo no piso (grade violeta), moldura emissora no teto, núcleo de campo no centro
Zf = P_BAU['Zf']
bg = bau.B('emissor', 'grafite')
caixa_de(bg, Cb + Vector((-0.33, -0.3, Zf)), Cb + Vector((0.33, 0.3, Zf + 0.012)))
for k in range(-3, 4):
    caixa_de(bau.B('campo', 'campo'), Cb + Vector((k * 0.1 - 0.003, -0.29, Zf + 0.012)), Cb + Vector((k * 0.1 + 0.003, 0.29, Zf + 0.0135)))
for k in range(-2, 3):
    caixa_de(bau.B('campo', 'campo'), Cb + Vector((-0.32, k * 0.12 - 0.003, Zf + 0.012)), Cb + Vector((0.32, k * 0.12 + 0.003, Zf + 0.0135)))
zt0 = P_BAU['Z1'] - 0.02
for sx in (-1, 1):                                               # emissores do teto (barras sob o teto, fora da janela)
    caixa_de(bg, Cb + Vector((sx * 0.3 - 0.025, -0.26, zt0 - 0.022)), Cb + Vector((sx * 0.3 + 0.025, 0.26, zt0)))
    caixa_de(bau.B('luz_teto', 'luz_teto'), Cb + Vector((sx * 0.3 - 0.018, -0.24, zt0 - 0.0235)), Cb + Vector((sx * 0.3 + 0.018, 0.24, zt0 - 0.022)))
cil(bg, Cb + Vector((0, 0, Zf + 0.03)), 0.045, 0.04, lados=16)    # núcleo: base, coluna de cristal, capitel
for z in (Zf + 0.055, 0.44):
    toro(bau.B('nucleo_aneis', 'cobre'), Cb + Vector((0, 0, z)), 0.03, 0.007, 24, 8)
bm = bau.B('nucleo_cristal', 'cristal')
bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.018, radius2=0.012, depth=0.44 - Zf - 0.05,
                      matrix=Matrix.Translation(Cb + Vector((0, 0, (Zf + 0.05 + 0.44) / 2))))
cil(bg, Cb + Vector((0, 0, 0.45)), 0.04, 0.025, lados=16)
for k in range(4):                                               # cabos do núcleo ao emissor
    a = k * PI / 2 + PI / 4
    p0 = Cb + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, Zf + 0.02))
    p1 = Cb + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, Zf + 0.013))
    mangueira(bau.B('cabo', 'borracha'), bezier(p0, p0 + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.01)), p1 + Vector((0, 0, 0.01)), p1, 6), 0.004)
luz = bpy.data.lights.new('bau_luz', 'POINT')
luz.color = (0.7, 0.5, 1.0)
luz.energy = 9.0
luz.shadow_soft_size = 0.15
lo = bpy.data.objects.new('bau_luz', luz)
col_bau.objects.link(lo)
lo.location = Cb + Vector((0, 0, 0.47))
bau.fechar()

# grade flutuante: 2 anéis de 8 vagas
ANEL = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
DX, DY = 0.2, 0.165
Z_BAIXO, Z_CIMA = 0.215, 0.355


def vaga(s, z):
    """Posição ao longo do anel (s contínuo, anda pelas bordas do quadrado)."""
    s = s % 8
    i = int(math.floor(s))
    f = s - i
    a, b = ANEL[i], ANEL[(i + 1) % 8]
    return Vector(((a[0] + (b[0] - a[0]) * f) * DX, (a[1] + (b[1] - a[1]) * f) * DY, z))


TIPOS_CIMA = ['bobina', 'engrenagem', 'cristal', 'lingote']
TIPOS_BAIXO = ['lingote', 'engrenagem']
baixo = [(item(TIPOS_BAIXO[k % 2], halo=True), k) for k in range(8)]
cima = [(item(TIPOS_CIMA[k % 4], halo=True), k) for k in range(1, 8)]
entra = item('bobina', halo=True)
sai_k = 4
an_bau = []                                                      # anéis do feixe de transferência
for k in range(3):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 0.03, 0.0016, 32, 6)
    o = ob('bau_feixe', bm, 'feixe')
    o.rotation_mode = 'QUATERNION'
    an_bau.append(o)

# ================================================================== baú grande
COL[0] = col_gr
gr = Bau('gr', C_GR, P_GR)
gr.casca()
gr.teto()
rustico(gr)
gr.barras(6)
Cg = gr.C
Zf = P_GR['Zf']
ZT = 0.39                                                        # topo das prateleiras e do andar do meio
ESC = 1.15


def G(x, y, z):
    return Cg + Vector((x, y, z))


# prateleiras de recebimento atrás de cada escotilha (chapa, lábio, mãos-francesas até a parede, anel de campo)
for lado, n in LADOS.items():
    R = quadro(n)
    hn = (P_GR['D'] if abs(n.y) > 0.5 else P_GR['W']) / 2 - 0.006 - P_GR['dd']
    L = lambda u, v, z: Cg + R @ Vector((u, v, 0)) + Vector((0, 0, z))
    bf = gr.B('prateleira', 'grafite')
    for (u0, v0, z0), (u1, v1, z1) in ((((-0.13, hn - 0.31, ZT - 0.014)), (0.13, hn + 0.002, ZT)),
                                       ((-0.13, hn - 0.31, ZT), (0.13, hn - 0.296, ZT + 0.02))):
        a, b = L(u0, v0, z0), L(u1, v1, z1)
        caixa_de(bf, Vector((min(a.x, b.x), min(a.y, b.y), z0)), Vector((max(a.x, b.x), max(a.y, b.y), z1)))
    for su in (-1, 1):
        viga(gr.B('prateleira_mao', 'amarelo'), L(su * 0.1, hn - 0.24, ZT - 0.016), L(su * 0.1, hn - 0.004, ZT - 0.2), 0.016)
        caixa(gr.B('ferro', 'ferro'), L(su * 0.1, hn - 0.008, ZT - 0.2), (0.03, 0.03, 0.04))
    toro(gr.B('campo', 'campo'), L(0, hn - 0.15, ZT + 0.002), 0.045, 0.004, 32, 6)
    # por dentro: a linha hidráulica do coletor atravessa a parede e desce para o piso
    vp = hn - 0.002
    zc = (P_GR['Zf'] + 0.004 + P_GR['hz0'] - P_GR['fw'] - 0.004) / 2
    cano(gr.B('linha', 'aco', True), gr.B('ferro', 'ferro'), [L(0, vp, zc), L(0, vp - 0.06, zc), L(0, vp - 0.06, Zf)], 0.01, False)
    cil(gr.B('ferro', 'ferro'), L(0, vp - 0.06, Zf + 0.004), 0.022, 0.008, lados=12)
    cil(gr.B('ferro', 'ferro'), L(0, vp - 0.004, zc), 0.02, 0.008, R @ Vector((0, 1, 0)), lados=12)

# carrossel: mancal com coroa dentada e motor, coluna, 3 andares
bg = gr.B('carrossel_base', 'grafite')
cil(bg, G(0, 0, Zf + 0.02), 0.13, 0.04, lados=32)
for k in range(48):
    a = k * 2 * PI / 48
    caixa(gr.B('coroa', 'aco'), G(math.cos(a) * 0.137, math.sin(a) * 0.137, Zf + 0.03), (0.012, 0.008, 0.02), Matrix.Rotation(a, 3, 'Z'))
caixa_de(bg, G(0.15, -0.06, Zf), G(0.25, 0.06, Zf + 0.1))          # motor do carrossel com pinhão
cil(gr.B('ferro', 'ferro'), G(0.2, 0, Zf + 0.13), 0.04, 0.06, lados=16)
cil(gr.B('aco', 'aco'), G(0.155, 0, Zf + 0.03), 0.018, 0.022, lados=10)
for k in range(5):
    cil(gr.B('ferro', 'ferro'), G(0.2, 0, Zf + 0.105 + k * 0.012), 0.046, 0.004, lados=16)
mangueira(gr.B('cabo', 'borracha'), bezier(G(0.25, 0.03, Zf + 0.06), G(0.32, 0.05, Zf + 0.06), G(0.36, 0.1, Zf + 0.02), G(0.38, 0.12, Zf + 0.004), 8), 0.006)
car = vazio('carrossel')
car.location = Cg
car.rotation_mode = 'XYZ'
bm = bmesh.new()
cil(bm, Vector((0, 0, (Zf + 0.04 + 0.56) / 2)), 0.035, 0.56 - Zf - 0.04, lados=16)
cil(bm, Vector((0, 0, 0.57)), 0.05, 0.02, lados=16)
ob('carrossel_coluna', bm, 'aco', car, liso=True)
ANDARES = [(0.235, 0.42, 0.36, 'lingote'), (ZT - 0.005, 0.30, 0.25, 'bobina'), (0.49, 0.19, 0.13, 'cristal')]
N_SLOT = 8
PASSO = 2 * PI / N_SLOT
A_D = -PI / 2                                                    # vaga de troca: lado sul
bm, bl, bc = bmesh.new(), bmesh.new(), bmesh.new()
for z, Rp, Ri, tp in ANDARES:
    cil(bm, Vector((0, 0, z)), Rp, 0.01, lados=48)
    toro(bl, Vector((0, 0, z + 0.006)), Rp - 0.004, 0.005, 64, 8)
    for k in range(N_SLOT):                                      # raios por baixo
        a = k * PASSO + PASSO / 2
        caixa(bm, Vector((math.cos(a) * Rp / 2, math.sin(a) * Rp / 2, z - 0.012)), (Rp, 0.012, 0.014), Matrix.Rotation(a, 3, 'Z'))
        b = A_D + k * PASSO
        if tp == 'bobina':                                       # berço da bobina
            toro(bc, Vector((math.cos(b) * Ri, math.sin(b) * Ri, z + 0.007)), 0.034, 0.004, 24, 6)
        elif tp == 'lingote':
            for s in (-1, 1):
                caixa(bc, Vector((math.cos(b) * Ri, math.sin(b) * Ri, z + 0.009)) + Matrix.Rotation(b, 3, 'Z') @ Vector((0, s * 0.033, 0)),
                      (0.05, 0.006, 0.008), Matrix.Rotation(b, 3, 'Z'))
ob('carrossel_andares', bm, 'amarelo', car)
ob('carrossel_aros', bl, 'ferro', car)
ob('carrossel_bercos', bc, 'grafite', car)
for z, Rp, Ri, tp in ANDARES:
    if tp == 'bobina':
        continue
    for k in range(N_SLOT):
        b = A_D + k * PASSO
        zc = z + 0.005 + MEIA[tp] * ESC + (0.05 if tp == 'cristal' else 0.0)
        it = item(tp, ESC, halo=(tp == 'cristal'), pai=car)
        it.location = (math.cos(b) * Ri, math.sin(b) * Ri, zc)
        it.rotation_quaternion = Quaternion((0, 0, 1), b + PI / 2)
Z_BOB = ZT + 0.005 + MEIA['bobina'] * ESC
bobinas = {}
for k in range(1, 7):
    b = A_D + k * PASSO
    it = item('bobina', ESC, pai=car)
    it.location = (math.cos(b) * 0.25, math.sin(b) * 0.25, Z_BOB)
gr_entra = item('bobina', ESC)
gr_sai = item('bobina', ESC)

# gaveteiros a oeste (dos dois lados da prateleira oeste); a gaveta de cima corre
X_G0, X_G1 = -0.855, -0.62
gav_anim = []
for y0, y1 in ((0.2, 0.74), (-0.74, -0.2)):
    caixa_de(gr.B('gaveteiro', 'grafite'), G(X_G0, y0, Zf), G(X_G1 - 0.004, y1, 0.6))
    caixa_de(gr.B('gaveteiro', 'grafite'), G(X_G1 - 0.004, y0, 0.585), G(X_G1, y1, 0.6))
    for col in range(2):
        ya, yb = y0 + 0.012 + col * (y1 - y0 - 0.012) / 2, y0 + (col + 1) * (y1 - y0 - 0.012) / 2
        for lin in range(3):
            za, zb = Zf + 0.02 + lin * 0.145, Zf + 0.02 + (lin + 1) * 0.145 - 0.01
            mexe = (lin == 2 and col == 0 and y0 > 0)
            e = vazio('gaveta') if mexe else None
            off = Vector((0, 0, 0)) if not mexe else -G(X_G1, 0, 0)
            if mexe:
                e.location = G(X_G1, 0, 0)
            bm, bl, bk = bmesh.new(), bmesh.new(), bmesh.new()
            caixa_de(bm, G(X_G1, ya, za) + off, G(X_G1 + 0.014, yb, zb) + off)
            caixa_de(bl, G(X_G1 + 0.014, (ya + yb) / 2 - 0.05, zb - 0.03) + off, G(X_G1 + 0.0155, (ya + yb) / 2 + 0.05, zb - 0.018) + off)
            caixa_de(bk, G(X_G1 + 0.012, (ya + yb) / 2 - 0.03, za + 0.02) + off, G(X_G1 + 0.0145, (ya + yb) / 2 + 0.03, za + 0.03) + off)
            if mexe:                                             # caixa da gaveta com itens
                caixa_de(bm, G(X_G1 - 0.2, ya + 0.01, za + 0.01) + off, G(X_G1, ya + 0.016, zb - 0.02) + off)
                caixa_de(bm, G(X_G1 - 0.2, yb - 0.016, za + 0.01) + off, G(X_G1, yb - 0.01, zb - 0.02) + off)
                caixa_de(bm, G(X_G1 - 0.2, ya + 0.01, za + 0.01) + off, G(X_G1, yb - 0.01, za + 0.018) + off)
                for k in range(3):
                    for j in range(2):
                        it = item('engrenagem', ESC, pai=e)
                        it.location = Vector((-0.035 - j * 0.07, Cg.y + ya + 0.055 + k * 0.075, za + 0.018 + MEIA['engrenagem'] * ESC))
                        it.rotation_quaternion = Quaternion((0, 0, 1), PI / 2)
                ob('gaveta', bm, 'amarelo', e)
                ob('gaveta_etiqueta', bl, 'barra_on', e)
                ob('gaveta_fenda', bk, 'buraco', e)
                gav_anim.append(e)
            else:
                ob('gaveta', bm, 'amarelo')
                ob('gaveta_etiqueta', bl, 'barra_off' if (lin + col) % 2 else 'barra_on')
                ob('gaveta_fenda', bk, 'buraco')

# campo flutuante a nordeste: placa emissora no piso, 4 pilares, placa de cima, coluna de cristal
FC = Vector((0.56, 0.54, 0))
for (x0, y0), (x1, y1) in (((-0.22, -0.22), (0.22, 0.22)),):
    caixa_de(gr.B('emissor', 'grafite'), G(FC.x + x0, FC.y + y0, Zf), G(FC.x + x1, FC.y + y1, Zf + 0.018))
    caixa_de(gr.B('emissor', 'grafite'), G(FC.x + x0, FC.y + y0, 0.645), G(FC.x + x1, FC.y + y1, 0.665))
for k in range(-2, 3):
    caixa_de(gr.B('campo', 'campo'), G(FC.x + k * 0.08 - 0.003, FC.y - 0.2, Zf + 0.018), G(FC.x + k * 0.08 + 0.003, FC.y + 0.2, Zf + 0.0195))
    caixa_de(gr.B('campo', 'campo'), G(FC.x - 0.2, FC.y + k * 0.08 - 0.003, Zf + 0.018), G(FC.x + 0.2, FC.y + k * 0.08 + 0.003, Zf + 0.0195))
    caixa_de(gr.B('campo', 'campo'), G(FC.x + k * 0.08 - 0.003, FC.y - 0.2, 0.6435), G(FC.x + k * 0.08 + 0.003, FC.y + 0.2, 0.645))
for sx in (-1, 1):
    for sy in (-1, 1):
        caixa_de(gr.B('pilar', 'amarelo'), G(FC.x + sx * 0.2 - 0.014, FC.y + sy * 0.2 - 0.014, Zf + 0.018), G(FC.x + sx * 0.2 + 0.014, FC.y + sy * 0.2 + 0.014, 0.645))
bmesh.ops.create_cone(gr.B('nucleo', 'cristal'), cap_ends=True, segments=6, radius1=0.02, radius2=0.014, depth=0.645 - Zf - 0.06,
                      matrix=Matrix.Translation(G(FC.x, FC.y, (Zf + 0.04 + 0.625) / 2)))
cil(gr.B('emissor', 'grafite'), G(FC.x, FC.y, Zf + 0.03), 0.04, 0.03, lados=16)
cil(gr.B('emissor', 'grafite'), G(FC.x, FC.y, 0.63), 0.035, 0.03, lados=16)
GX, GY = 0.14, 0.14
ZF_B, ZF_C = 0.3, 0.48
f_baixo = [(item(['lingote', 'cristal'][k % 2], ESC, halo=True), k) for k in range(8)]
f_cima = [(item(['engrenagem', 'bobina'][k % 2], ESC, halo=True), k) for k in range(8)]

# unidade hidráulica a sudeste: base, motor, bomba, reservatório, coletor e canos para o piso
bs = gr.B('skid', 'grafite')
caixa_de(bs, G(0.44, -0.8, Zf), G(0.82, -0.44, Zf + 0.02))
cil(gr.B('hid_motor', 'amarelo', True), G(0.55, -0.66, Zf + 0.09), 0.055, 0.15, Vector((1, 0, 0)), lados=20)
for k in range(6):
    cil(gr.B('ferro', 'ferro'), G(0.5 + k * 0.02, -0.66, Zf + 0.09), 0.062, 0.004, Vector((1, 0, 0)), lados=20)
caixa_de(bs, G(0.48, -0.71, Zf + 0.02), G(0.62, -0.61, Zf + 0.04))
cil(gr.B('hid_bomba', 'ferro'), G(0.65, -0.66, Zf + 0.09), 0.04, 0.06, Vector((1, 0, 0)), lados=16)
cil(gr.B('hid_tanque', 'amarelo', True), G(0.74, -0.62, Zf + 0.12), 0.06, 0.3, Vector((0, 1, 0)), lados=24)
for y in (-0.75, -0.49):
    caixa_de(bs, G(0.7, y - 0.012, Zf + 0.02), G(0.78, y + 0.012, Zf + 0.07))
cil(gr.B('ferro', 'ferro'), G(0.74, -0.62, Zf + 0.185), 0.016, 0.014, lados=12)       # bocal de enchimento
cil(gr.B('vidro', 'vidro'), G(0.74, -0.677, Zf + 0.12), 0.018, 0.006, Vector((0, 1, 0)), lados=12)
caixa_de(gr.B('coletor', 'grafite'), G(0.6, -0.52, Zf + 0.02), G(0.68, -0.46, Zf + 0.08))
cano(gr.B('linha', 'aco', True), gr.B('ferro', 'ferro'),
     [G(0.65, -0.62, Zf + 0.09), G(0.65, -0.55, Zf + 0.09), G(0.65, -0.55, Zf + 0.06), G(0.65, -0.52, Zf + 0.06)], 0.01, False)
cano(gr.B('linha', 'aco', True), gr.B('ferro', 'ferro'),
     [G(0.74, -0.5, Zf + 0.1), G(0.74, -0.42, Zf + 0.1), G(0.66, -0.42, Zf + 0.1), G(0.66, -0.46, Zf + 0.08)], 0.009, False)
for x in (0.62, 0.66):                                           # saídas do coletor descem para o piso
    cano(gr.B('linha', 'aco', True), gr.B('ferro', 'ferro'), [G(x, -0.49, Zf + 0.04), G(x, -0.42, Zf + 0.04), G(x, -0.42, Zf)], 0.008, False)
    cil(gr.B('ferro', 'ferro'), G(x, -0.42, Zf + 0.004), 0.018, 0.008, lados=12)
mangueira(gr.B('cabo', 'borracha'), bezier(G(0.55, -0.71, Zf + 0.12), G(0.55, -0.77, Zf + 0.14), G(0.6, -0.79, Zf + 0.2), G(0.62, -0.795, Zf + 0.26), 10), 0.007)
caixa_de(gr.B('teto_peca', 'grafite'), G(0.56, -0.816, Zf + 0.26), G(0.68, -0.79, Zf + 0.38))     # quadro elétrico na parede
for k in range(4):
    caixa_de(gr.B('luzinhas_' + ('barra_on' if k % 3 else 'halo'), 'barra_on' if k % 3 else 'halo'), G(0.58 + k * 0.025, -0.791, Zf + 0.35), G(0.59 + k * 0.025, -0.789, Zf + 0.36))
mancha_suave(gr.B('oleo_s', 'oleo_s'), (Cg.x + 0.66, Cg.y - 0.5), 0.07, Zf + 0.001)

# ponte rolante interna: trilhos pendurados no teto, barramento de cobre, ponte, carro, mastro telescópico, garra
Z_TR = 0.77
for sy in (-1, 1):
    caixa_de(gr.B('trilho', 'amarelo'), G(-0.8, sy * 0.7 - 0.02, Z_TR), G(0.8, sy * 0.7 + 0.02, Z_TR + 0.022))
    for x in (-0.6, -0.2, 0.2, 0.6):
        caixa_de(gr.B('trilho_pendural', 'ferro'), G(x - 0.012, sy * 0.7 - 0.01, Z_TR + 0.022), G(x + 0.012, sy * 0.7 + 0.01, P_GR['Z1'] - 0.02))
    for x in (-0.79, 0.79):                                      # batentes
        caixa_de(gr.B('ferro', 'ferro'), G(x - 0.01, sy * 0.7 - 0.025, Z_TR - 0.02), G(x + 0.01, sy * 0.7 + 0.025, Z_TR + 0.022))
tubo(gr.B('barramento', 'cobre'), G(-0.8, 0.735, Z_TR + 0.01), G(0.8, 0.735, Z_TR + 0.01), 0.004, 8)
for x in (-0.6, -0.2, 0.2, 0.6):
    cil(gr.B('isolador', 'barra_off'), G(x, 0.728, Z_TR + 0.01), 0.006, 0.012, Vector((0, 1, 0)), lados=8)
gr.fechar()
ponte = vazio('ponte')
bm, bp = bmesh.new(), bmesh.new()
caixa_de(bm, (-0.025, -0.7, 0.728), (0.025, 0.7, 0.758))
for sy in (-1, 1):
    caixa_de(bm, (-0.05, sy * 0.7 - 0.025, 0.74), (0.05, sy * 0.7 + 0.025, Z_TR))        # cabeceira sob o trilho
    for sx in (-1, 1):
        cil(bp, Vector((sx * 0.032, sy * 0.7, Z_TR + 0.004)), 0.01, 0.046, Vector((0, 1, 0)), lados=10)  # rodas no trilho
caixa_de(bp, (-0.012, 0.725, Z_TR - 0.002), (0.012, 0.745, Z_TR + 0.012))                 # coletor do barramento
ob('ponte', bm, 'amarelo', ponte)
ob('ponte_rodas', bp, 'ferro', ponte)
carro = vazio('carro')
bm = bmesh.new()
caixa_de(bm, (-0.045, -0.04, 0.695), (0.045, 0.04, 0.728))
cil(bm, Vector((0.06, 0, 0.71)), 0.022, 0.04, Vector((1, 0, 0)), lados=14)
ob('carro', bm, 'grafite', carro)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.6475)), 0.022, 0.095, lados=16)
ob('mastro1', bm, 'amarelo', carro, liso=True)
est2, est3 = vazio('mastro2'), vazio('mastro3')
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.6475)), 0.017, 0.095, lados=14)
ob('mastro2', bm, 'aco', est2, liso=True)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.6475)), 0.012, 0.095, lados=12)
ob('mastro3', bm, 'cromo', est3, liso=True)
garra = vazio('garra')
bm, bl = bmesh.new(), bmesh.new()
cil(bm, Vector((0, 0, 0.01)), 0.048, 0.02, lados=24)
cil(bm, Vector((0, 0, 0.026)), 0.02, 0.014, lados=12)
toro(bl, Vector((0, 0, -0.001)), 0.03, 0.003, 32, 6)
ob('garra', bm, 'grafite', garra)
ob('garra_campo', bl, 'halo', garra)
dedos = []
for k in range(4):
    a = k * PI / 2 + PI / 4
    d = vazio('dedo', garra)
    d.rotation_euler = (0, 0, a)
    bm = bmesh.new()
    caixa_de(bm, (-0.006, -0.008, -0.058), (0.006, 0.008, 0.004))
    caixa_de(bm, (-0.016, -0.008, -0.058), (0.0, 0.008, -0.05))
    ob('dedo', bm, 'aco', d)
    dedos.append((d, a))
# festão: cabo do carro até a cabeceira (recalculado a cada quadro não; cabo curto preso ao carro sobe para a ponte)
luzes = []
for p, cor, en in ((G(0, 0, 0.7), (0.75, 0.55, 1.0), 30.0), (G(-0.4, 0.3, 0.6), (1.0, 0.6, 0.3), 12.0), (FC + Cg + Vector((0, 0, 0.4)), (0.7, 0.5, 1.0), 10.0), (G(0.1, -0.5, 0.65), (1.0, 0.75, 0.5), 10.0)):
    ld = bpy.data.lights.new('gr_luz', 'POINT')
    ld.color = cor
    ld.energy = en
    ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new('gr_luz', ld)
    col_gr.objects.link(lo)
    lo.location = p
an_gr = []
for k in range(3):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 0.05, 0.0024, 32, 6)
    o = ob('gr_feixe', bm, 'feixe')
    o.rotation_mode = 'QUATERNION'
    an_gr.append(o)
# exaustor no teto do grande (hélice girando sob a grade)
EX = G(-0.55, -0.5, P_GR['Z1'] - 0.008)
cil(gr.B('exaustor', 'grafite'), EX + Vector((0, 0, 0.025)), 0.09, 0.05, lados=24)
mancha_suave(gr.B('fuligem_s', 'fuligem_s'), (EX.x + 0.03, EX.y + 0.02), 0.2, EX.z + 0.0012)
bmesh.ops.delete(gr.B('exaustor', 'grafite'), geom=[f for f in gr.B('exaustor', 'grafite').faces if f.normal.z > 0.9], context='FACES_ONLY')
for k in range(-4, 5):
    caixa(gr.B('exaustor_grade', 'ferro'), EX + Vector((k * 0.018, 0, 0.051)), (0.004, 2 * math.sqrt(max(0.088 ** 2 - (k * 0.018) ** 2, 0.0001)), 0.004))
toro(gr.B('exaustor_grade', 'ferro'), EX + Vector((0, 0, 0.051)), 0.086, 0.004, 32, 6)
helice = vazio('helice')
helice.location = EX + Vector((0, 0, 0.035))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.018, 0.02, lados=12)
for k in range(5):
    a = k * 2 * PI / 5
    caixa(bm, Vector((math.cos(a) * 0.045, math.sin(a) * 0.045, 0)), (0.06, 0.022, 0.004), Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(0.35, 3, 'X'))
ob('helice', bm, 'aco', helice)
gr.fechar()
COL[0] = sc.collection


# ------------------------------------------------------------------ animação (laço de 4 s)
def caminho(pts, fr):
    """Interpola chaves (fr, valor) com suavização em cada trecho."""
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f0 <= fr <= f1:
            return v0.lerp(v1, suave((fr - f0) / (f1 - f0))) if isinstance(v0, Vector) else v0 + (v1 - v0) * suave((fr - f0) / (f1 - f0))
    return pts[-1][1]


def chave(o, q, *props):
    for p in props:
        o.keyframe_insert(p, frame=q)


def feixe(aneis, a, b, u, ativo, q):
    """Anéis do campo de transferência entre a boca da escotilha (a) e o item (b), correndo na direção do movimento."""
    d = (b - a)
    for k, o in enumerate(aneis):
        s = (k / len(aneis) + u * 3) % 1.0
        o.location = a + d * s
        o.rotation_quaternion = (Vector((round(d.x, 3), round(d.y, 3), 0)).normalized() if d.xy.length > 1e-3 else UP).to_track_quat('Z', 'Y')
        o.scale = [0.8 + 0.3 * math.sin(PI * s)] * 3
        o.hide_render = not ativo
        o.hide_viewport = not ativo
        chave(o, q, 'location', 'rotation_quaternion', 'scale', 'hide_render', 'hide_viewport')


def mostrar(o, vis, q):
    for c in [o] + list(o.children_recursive):
        c.hide_render = not vis
        c.hide_viewport = not vis
        chave(c, q, 'hide_render', 'hide_viewport')


H_ = Vector((0.35, -0.35, 0.58))
I_UP, I_DN = Vector((0, -0.66, 0.58)), Vector((0, -0.66, Z_BOB + MEIA['bobina'] * ESC))
D_UP, D_DN = Vector((0, -0.25, 0.58)), Vector((0, -0.25, Z_BOB + MEIA['bobina'] * ESC))
O_UP, O_DN = Vector((0.66, 0, 0.58)), Vector((0.66, 0, Z_BOB + MEIA['bobina'] * ESC))
BRACO = [(0.0, H_, 0), (0.15, H_, 0), (0.23, I_UP, 0), (0.29, I_DN, 0), (0.32, I_DN, 1), (0.37, I_UP, 1), (0.42, D_UP, 1),
         (0.46, D_DN, 1), (0.49, D_DN, 0), (0.52, D_UP, 0), (0.60, D_UP, 0), (0.63, D_DN, 0), (0.655, D_DN, 1), (0.69, D_UP, 1),
         (0.75, O_UP, 1), (0.78, O_DN, 1), (0.80, O_DN, 0), (0.83, O_UP, 0), (0.95, H_, 0), (1.0, H_, 0)]
GARRA_F = [(f, float(g)) for f, _, g in BRACO]
BRACO_P = [(f, p) for f, p, _ in BRACO]

for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # ---------------- baú
    abS = jan(fr, 0.04, 0.14) - jan(fr, 0.42, 0.52)
    abN = jan(fr, 0.46, 0.56) - jan(fr, 0.72, 0.82)
    for lado in LADOS:
        bau.animar_tampa(lado, q, abS if lado == 'S' else (abN if lado == 'N' else 0.0))
    fora_S = Vector((0, -0.78, Z_CIMA))
    fora_N = Vector((0, 0.78, Z_CIMA))
    gira_c = 4 * jan(fr, 0.80, 0.98)
    gira_b = -2 * jan(fr, 0.78, 0.96)
    bob = lambda k, z: Vector((0, 0, 0.006 * math.sin(2 * PI * (fr * 2 + k * 0.13 + z * 3))))
    for it, k in baixo:
        it.location = Cb + vaga(k + gira_b, Z_BAIXO) + bob(k, 1)
        it.rotation_quaternion = Quaternion((0, 0, 1), 2 * PI * fr + k)
        chave(it, q, 'location', 'rotation_quaternion')
    for it, k in cima:
        kk = k
        if k == sai_k and fr >= 0.56:                            # o item da vaga norte sai pela escotilha norte
            u = jan(fr, 0.56, 0.74)
            p = vaga(4, Z_CIMA).lerp(fora_N, u)
            it.location = Cb + p
            mostrar(it, fr < 0.75, q)
        else:
            it.location = Cb + vaga(k + gira_c, Z_CIMA) + bob(k, 2)
            if k == sai_k:
                mostrar(it, True, q)
        it.rotation_quaternion = Quaternion((0, 0, 1), -2 * PI * fr + k)
        chave(it, q, 'location', 'rotation_quaternion')
    u = jan(fr, 0.12, 0.40)
    p = fora_S.lerp(vaga(0, Z_CIMA), u) if fr < 0.80 else vaga(0 + gira_c, Z_CIMA)
    entra.location = Cb + p
    entra.rotation_quaternion = Quaternion((0, 0, 1), -2 * PI * fr)
    chave(entra, q, 'location', 'rotation_quaternion')
    mostrar(entra, fr >= 0.11, q)
    if 0.12 <= fr <= 0.40:
        feixe(an_bau, Cb + fora_S, Cb + p, fr, True, q)
    elif 0.56 <= fr <= 0.74:
        pN = [c for c, k in cima if k == sai_k][0].location
        feixe(an_bau, Cb + fora_N, pN.copy(), fr, True, q)
    else:
        feixe(an_bau, Cb, Cb + Vector((0, 0, 0.3)), fr, False, q)
    bau.forca_barra.default_value = 9.0 if 0.40 <= fr < 0.74 else 0.0
    bau.forca_barra.keyframe_insert('default_value', frame=q)
    # ---------------- grande
    abS = jan(fr, 0.02, 0.12) - jan(fr, 0.40, 0.50)
    abL = jan(fr, 0.70, 0.79) - jan(fr, 0.90, 1.0)
    for lado in LADOS:
        gr.animar_tampa(lado, q, abS if lado == 'S' else (abL if lado == 'L' else 0.0))
    phi = PASSO * jan(fr, 0.52, 0.60)
    car.rotation_euler = (0, 0, phi)
    chave(car, q, 'rotation_euler')
    g = caminho(BRACO_P, fr)
    fecha = caminho(GARRA_F, fr)
    e = 0.58 - g.z
    ponte.location = Cg + Vector((g.x, 0, 0))
    carro.location = Cg + Vector((g.x, g.y, 0))
    est2.location = Cg + Vector((g.x, g.y, -e / 2))
    est3.location = Cg + Vector((g.x, g.y, -e))
    garra.location = Cg + g
    for o in (ponte, carro, est2, est3, garra):
        chave(o, q, 'location')
    for d, a in dedos:
        r = 0.05 - 0.016 * fecha
        d.location = (math.cos(a) * r, math.sin(a) * r, 0)
        chave(d, q, 'location')
    na_garra = lambda: Cg + g - Vector((0, 0, MEIA['bobina'] * ESC))
    # item que entra: escotilha sul → prateleira → garra → vaga 0 do carrossel
    fora = G(0, -1.3, Z_BOB)
    prat = G(0, -0.66, Z_BOB)
    if fr < 0.26:
        p = fora.lerp(prat, jan(fr, 0.10, 0.26))
    elif fr < 0.32:
        p = prat
    elif fr < 0.49:
        p = na_garra()
    else:
        b = A_D + phi
        p = G(math.cos(b) * 0.25, math.sin(b) * 0.25, Z_BOB)
    gr_entra.location = p
    chave(gr_entra, q, 'location')
    mostrar(gr_entra, fr >= 0.09, q)
    # item que sai: vaga 7 → garra → prateleira leste → escotilha leste
    if fr < 0.655:
        b = A_D + 7 * PASSO + phi
        p = G(math.cos(b) * 0.25, math.sin(b) * 0.25, Z_BOB)
    elif fr < 0.80:
        p = na_garra()
    else:
        p = G(0.66, 0, Z_BOB).lerp(G(1.3, 0, Z_BOB), jan(fr, 0.81, 0.90))
    gr_sai.location = p
    chave(gr_sai, q, 'location')
    mostrar(gr_sai, fr < 0.91, q)
    if 0.10 <= fr <= 0.26:
        feixe(an_gr, fora, gr_entra.location.copy(), fr, True, q)
    elif 0.81 <= fr <= 0.90:
        feixe(an_gr, G(1.3, 0, Z_BOB), gr_sai.location.copy(), fr, True, q)
    else:
        feixe(an_gr, Cg, Cg + Vector((0, 0, 0.3)), fr, False, q)
    gr.forca_barra.default_value = 9.0 if 0.29 <= fr < 0.88 else 0.0
    gr.forca_barra.keyframe_insert('default_value', frame=q)
    # campo NE: anel de baixo 2 passos anti-horário, de cima 2 passos horário
    gb = 2 * jan(fr, 0.06, 0.26)
    gc = -2 * jan(fr, 0.62, 0.82)
    for lista, z, gg in ((f_baixo, ZF_B, gb), (f_cima, ZF_C, gc)):
        for it, k in lista:
            v = vaga(k + gg, 0)
            it.location = Cg + FC + Vector((v.x / DX * GX, v.y / DY * GY, z)) + Vector((0, 0, 0.007 * math.sin(2 * PI * (fr * 2 + k * 0.17))))
            it.rotation_quaternion = Quaternion((0, 0, 1), 2 * PI * fr * (1 if z < 0.4 else -1) + k)
            chave(it, q, 'location', 'rotation_quaternion')
    # gaveta corre para fora e volta
    for gv in gav_anim:
        gv.location = G(X_G1, 0, 0) + Vector((0.13 * (jan(fr, 0.30, 0.40) - jan(fr, 0.70, 0.80)), 0, 0))
        chave(gv, q, 'location')
    helice.rotation_euler = (0, 0, 2 * PI * 6 * fr)
    chave(helice, q, 'rotation_euler')
    # luzes das antenas piscam
    for b_ in (bau, gr):
        b_.ponta.default_value = 30.0 if (fr * 4) % 1.0 < 0.12 else 0.5
        b_.ponta.keyframe_insert('default_value', frame=q)
for o in list(bpy.data.objects) + list(bpy.data.materials):
    ad = getattr(o, 'animation_data', None) if not isinstance(o, bpy.types.Material) else (o.node_tree.animation_data if o.node_tree else None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR' if fc.data_path not in ('hide_render', 'hide_viewport') else 'CONSTANT'
                if 'Emission Strength' in fc.data_path or 'default_value' in fc.data_path:
                    kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (14, 14, 1.0))
base3d.obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bgn = mundo.node_tree.nodes['Background']
bgn.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bgn.inputs['Strength'].default_value = 0.55
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


def quem(x):
    col_bau.hide_render = x == 'grande'
    col_gr.hide_render = x == 'bau'


CB3 = Vector((C_BAU[0], C_BAU[1], 0))
CG3 = Vector((C_GR[0], C_GR[1], 0))


def polar(c, ang, dist, alt, zalvo):
    a = math.radians(ang)
    return c + Vector((math.cos(a) * dist, math.sin(a) * dist, alt)), c + Vector((0, 0, zalvo))


FOTOS = {
    'bau_0': ('bau', 30, polar(CB3, 242, 1.75, 1.0, 0.27), 34, (1200, 1000)),
    'bau_perto': ('bau', 30, ((CB3 + Vector((0.12, -1.05, 0.6))), CB3 + Vector((0.0, -0.15, 0.3))), 30, (1300, 1000)),
    'bau_grande_0': ('grande', 33, polar(CG3, 238, 3.0, 1.9, 0.38), 34, (1200, 1000)),
    'bau_grande_perto': ('grande', 33, ((CG3 + Vector((0.32, -1.6, 0.82))), CG3 + Vector((0.0, -0.45, 0.42))), 26, (1300, 1000)),
    'baus_juntos': ('ambos', 31, polar(Vector(((C_BAU[0] + C_GR[0]) / 2, -0.3, 0)), 252, 3.6, 1.9, 0.33), 32, (1400, 1000)),
}
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
args = sys.argv[sys.argv.index('--') + 2:] if '--' in sys.argv else []
if modo == 'foto':
    sc.cycles.samples = 128
    for nome in (args or list(FOTOS)):
        x, qd, (pos, alvo), lente, res = FOTOS[nome]
        quem(x)
        sc.frame_set(qd)
        sc.render.resolution_x, sc.render.resolution_y = res
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(a) for a in args[:8]]
    if len(args) > 9 and args[9] == 'semteto':
        for o in sc.objects:
            if o.name.endswith('_teto') or o.name.endswith('_vidro') or o.name.endswith('_grade') or 'exaustor' in o.name or 'helice' in o.name:
                o.hide_render = True
    sc.cycles.samples = 24
    quem(args[8] if len(args) > 8 else 'ambos')
    sc.frame_set(int(v[7]))
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'baus_teste.png')
    bpy.ops.render.render(write_still=True)
print('BAUS ok')
