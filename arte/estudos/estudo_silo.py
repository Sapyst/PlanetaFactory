"""Estudo isolado (fora do jogo): SILO DE GRANEL (silo_granel, 3×3). Guarda 20.000 itens de UM tipo; braços colocam e
tiram. Sem humanos: nada de escada, guarda-corpo ou plataforma de operador; tudo serve à IA e aos drones.
- Laje 3×3 com listras na borda; oito colunas em perfil H chumbadas (placa, graute, chumbadores com porca), saia
  corrugada na metade norte e contraventamento em X com esticador; viga-anel no topo das colunas.
- Cilindro alto de chapa ondulada galvanizada (Ø 1,9 m) com cintas aparafusadas nas emendas, três anéis de reforço em
  cantoneira, montantes verticais aparafusados, anel de coroamento e teto cônico com nervuras radiais.
- Funil cônico embaixo, comporta de gaveta aberta por pistão (camisa no braço da comporta, haste na orelha da gaveta,
  mangueiras até a válvula na coluna) e rosca extratora inclinada (motor + redutor atrás, janela gradeada mostrando a
  hélice) que sobe até a bica sul e despeja o granel na caçamba de retirada (onde o braço pega).
- Elevador de canecas pelo oeste: pé com mancais e esticadores, moega de entrada (onde o braço despeja), duas pernas
  com flanges a cada seção, janela gradeada mostrando as canecas cheias subindo, cabeça com capô, redutor e motor,
  duto de descarga até o bocal do teto. Amarrações da perna aos anéis do silo. Eletrocalha com cabos descendo.
- Teto: filtro de respiro com chapéu e poeira saindo, dois radares de nível (corneta no bocal), mastro com radar
  giratório da IA, plataforma com escotilha de drone (tampa com dois pistões, luzes âmbar).
- Indicador de nível: visor de vidro com o granel dentro + régua com ponteiro.
- Toque da IA: faixa de vidro vertical mostrando o granel em grade de cubos perfeita demais, com luz violeta nas
  frestas e o plano de compactação no nível; emissores de campo nos anéis.
- Desgaste: amassados no costado, ferrugem escorrendo (shader + escorridos), remendos aparafusados e soldados, uma
  chapa trocada em zarcão, pó e montes de minério no chão, óleo sob os motores, fuligem, número de série apagado.
Animação (laço de 4 s): canecas sobem; rosca gira; comporta abre, granel cai da bica e para quando fecha; nível sobe e
desce (visor, ponteiro, grade da IA); radar gira; acoplamento gira; tampa do drone abre e fecha; poeira sai do filtro.
Uso: blender -b --python estudo_silo.py -- foto [silo_0 silo_perto silo_topo]
     blender -b --python estudo_silo.py -- teste x y z ax ay az lente quadro"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(31)
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


def quadro(n):
    t = Vector((n.y, -n.x, 0))
    return Matrix((t, n, UP)).transposed()


BMS = {}


def B(nome, mat, liso=False):
    k = (nome, mat, liso)
    if k not in BMS:
        BMS[k] = bmesh.new()
    return BMS[k]


def fechar():
    for (nome, mat, liso), bm in BMS.items():
        o = base3d.obj('silo_' + nome, bm, mat)
        if liso:
            suavizar(o)
    BMS.clear()


def ob(nome, bm, mat, pai=None, liso=False):
    o = base3d.obj(nome, bm, mat, pai)
    return suavizar(o) if liso else o


def vazio(nome, pai=None):
    e = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(e)
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
    b.inputs['Roughness'].default_value = 0.4
    return m


def vidro_sujo_mat():
    m = bpy.data.materials.new('Vidro sujo')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.5, 0.48, 0.44, 1)
    b.inputs['Transmission Weight'].default_value = 0.9
    b.inputs['IOR'].default_value = 1.45
    no = mats.no
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 8.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    r = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.4, 'From Max': 0.7, 'To Min': 0.04, 'To Max': 0.4})
    nt.links.new(ru.outputs['Fac'], r.inputs['Value'])
    nt.links.new(r.outputs['Result'], b.inputs['Roughness'])
    return m


def _cor_base(m):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    lk = b.inputs['Base Color'].links[0]
    src = lk.from_socket
    m.node_tree.links.remove(lk)
    return b, src


def empoeirar(m, z_lama=0.17, cor_po=(0.36, 0.30, 0.25)):
    """Poeira clara nas faces de cima (manchada) e lama escura subindo do pé (posição no mundo)."""
    nt = m.node_tree
    no = mats.no
    b, src = _cor_base(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    sn = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    cima = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.5, 'From Max': 0.95, 'To Min': 0.0, 'To Max': 0.6})
    nt.links.new(sn.outputs['Z'], cima.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 6.0, 'Detail': 5.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    rm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.35, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], rm.inputs['Value'])
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(cima.outputs['Result'], f.inputs[0])
    nt.links.new(rm.outputs['Result'], f.inputs[1])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix.inputs[7].default_value = (*cor_po, 1)
    nt.links.new(f.outputs['Value'], mix.inputs[0])
    nt.links.new(src, mix.inputs[6])
    sp = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sp.inputs[0])
    lama = no(nt, 'ShaderNodeMapRange', **{'From Min': z_lama, 'From Max': 0.06, 'To Min': 0.0, 'To Max': 0.8})
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
    mix2.inputs[7].default_value = (0.09, 0.05, 0.03, 1)
    nt.links.new(f2b.outputs['Value'], mix2.inputs[0])
    nt.links.new(mix.outputs[2], mix2.inputs[6])
    nt.links.new(mix2.outputs[2], b.inputs['Base Color'])
    return m


def escorrer(m, forca=0.85, esc=(13.0, 13.0, 0.9)):
    """Ferrugem escorrendo: ruído esticado na vertical (posição no mundo) vira faixas laranja-marrom que descem."""
    nt = m.node_tree
    no = mats.no
    b, src = _cor_base(m)
    geo = no(nt, 'ShaderNodeNewGeometry')
    vm = no(nt, 'ShaderNodeVectorMath', operation='MULTIPLY')
    vm.inputs[1].default_value = esc
    nt.links.new(geo.outputs['Position'], vm.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 6.0, 'Roughness': 0.65})
    nt.links.new(vm.outputs['Vector'], ru.inputs['Vector'])
    fx = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.57, 'From Max': 0.7, 'To Min': 0.0, 'To Max': forca})
    nt.links.new(ru.outputs['Fac'], fx.inputs['Value'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 45.0, 'Detail': 4.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])
    fm = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.45, 'To Max': 1.0})
    nt.links.new(fino.outputs['Fac'], fm.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(fx.outputs['Result'], mul.inputs[0])
    nt.links.new(fm.outputs['Result'], mul.inputs[1])
    mix = no(nt, 'ShaderNodeMix', data_type='RGBA', clamp_factor=True)
    mix.inputs[7].default_value = (0.27, 0.085, 0.025, 1)
    nt.links.new(mul.outputs['Value'], mix.inputs[0])
    nt.links.new(src, mix.inputs[6])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    return m


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


def estencil_mat():
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
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.18, 'From Max': 0.3, 'To Min': 0.0, 'To Max': 0.85})
    nt.links.new(mul.outputs['Value'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


VIOLETA = (0.55, 0.25, 1.0)
AMBAR = (1.0, 0.42, 0.04)
COR_MIN = (0.13, 0.06, 0.04)                      # minério de ferro (o granel deste estudo)
M = base3d.M
M.update({
    'galv': escorrer(empoeirar(mats.material('Galvanizado', (0.6, 0.62, 0.63), 0.75, 0.48, pintura=False, ferrugem=0.55,
                                             sujeira=0.45), z_lama=0.0), 0.8),
    'galv2': escorrer(empoeirar(mats.material('Galvanizado escuro', (0.42, 0.44, 0.45), 1.0, 0.45, pintura=False, ferrugem=0.6,
                                              sujeira=0.5), z_lama=0.0), 0.6),
    'teto': escorrer(empoeirar(mats.material('Teto', (0.55, 0.56, 0.56), 0.45, 0.6, pintura=False, ferrugem=0.45, sujeira=0.35), z_lama=0.0), 0.5, (9.0, 9.0, 9.0)),
    'amarelo': escorrer(empoeirar(mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.9, sujeira=0.85, ferrugem=0.45)), 0.6),
    'grafite': escorrer(empoeirar(mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.4)), 0.7),
    'funil': escorrer(empoeirar(mats.material('Funil', (0.3, 0.31, 0.32), 0.6, 0.5, desgaste=0.85, sujeira=0.9, ferrugem=0.7)), 0.9, (16, 16, 1.4)),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.6, sujeira=0.8, escovado=True),
    'ferro': empoeirar(mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9)),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.35),
    'cobre': mats.material('Cobre', (0.78, 0.40, 0.22), 1.0, 0.3, pintura=False, sujeira=0.6),
    'borracha': mats.material('Borracha', (0.02, 0.02, 0.022), 0, 0.75, pintura=False, sujeira=0.5, desgaste=0.0),
    'buraco': mats.material('Buraco', (0.01, 0.01, 0.01), 0, 0.9, pintura=False, sujeira=0.0, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'graute': mats.material('Graute', (0.4, 0.39, 0.36), 0, 0.95, sujeira=0.8, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'minerio': mats.material('Minério', COR_MIN, 0.15, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'minerio_g': mats.material('Minério em grade', (0.16, 0.075, 0.05), 0.4, 0.45, pintura=False, sujeira=0.3, desgaste=0.0),
    'zarcao': escorrer(empoeirar(mats.material('Zarcão', (0.42, 0.11, 0.045), 0, 0.6, desgaste=0.9, sujeira=0.85, ferrugem=0.4)), 0.5),
    'remendo': empoeirar(mats.material('Remendo', (0.3, 0.31, 0.27), 0.6, 0.55, pintura=False, desgaste=0.8, sujeira=0.9, ferrugem=0.9)),
    'solda': mats.material('Solda', (0.08, 0.07, 0.06), 0.9, 0.6, pintura=False, ferrugem=0.8, sujeira=0.8),
    'fio_r': mats.material('Fio vermelho', (0.4, 0.03, 0.02), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'fio_a': mats.material('Fio amarelo', (0.6, 0.45, 0.03), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'fio_z': mats.material('Fio azul', (0.03, 0.1, 0.4), 0, 0.45, pintura=False, sujeira=0.5, desgaste=0.0),
    'listras': base3d.listras_mat(),
    'vidro': vidro_sujo_mat(),
    'vidro_ia': emissivo('Vidro da faixa', (0, 0, 0), 0.0, base=(0.9, 0.9, 0.9)),
    'campo': emissivo('Campo da IA', VIOLETA, 4.0, base=(0.05, 0.02, 0.1)),
    'lente': emissivo('Lente do emissor', VIOLETA, 6.0),
    'plano': emissivo('Plano de compactação', VIOLETA, 2.2, base=(0.2, 0.1, 0.4)),
    'led_a': emissivo('LED âmbar', AMBAR, 8.0),
    'estencil': estencil_mat(),
    'poeira': base3d.volume_mat('Poeira do filtro', (0.62, 0.48, 0.38), 12.0, 3.8, 4.7),
    'poeira_b': base3d.volume_mat('Poeira da bica', (0.6, 0.42, 0.32), 5.0, 0.2, 0.6),
})
_gb = M['minerio_g'].node_tree.nodes['Principled BSDF']
_gb.inputs['Emission Color'].default_value = (*VIOLETA, 1)
_gb.inputs['Emission Strength'].default_value = 0.25
_vb = M['vidro_ia'].node_tree.nodes['Principled BSDF']
_vb.inputs['Transmission Weight'].default_value = 1.0
_vb.inputs['Roughness'].default_value = 0.03
M['fuligem_s'] = decal_mat('Fuligem suave', (0.01, 0.009, 0.009), 0.97)
M['oleo_s'] = decal_mat('Óleo suave', (0.008, 0.006, 0.004), 0.08)
M['po_s'] = decal_mat('Pó suave', (0.32, 0.27, 0.22), 0.95)
M['pomin_s'] = decal_mat('Pó de minério', (0.2, 0.09, 0.05), 0.95)
M['escorrido_s'] = decal_mat('Ferrugem escorrida', (0.26, 0.08, 0.022), 0.95)


def mat_animado(nome, cor, base=None):
    m = emissivo(nome, cor, 0.0, base=base or (0.03, 0.02, 0.015))
    M[nome] = m
    return m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


E_FAROL = mat_animado('farol', (1.0, 0.25, 0.03))
E_RADAR = mat_animado('radar_luz', VIOLETA)
E_DRONE = mat_animado('drone_luz', AMBAR)
E_CAMPO = M['plano'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
E_LENTE = M['lente'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']


def _cor(bm):
    return bm.loops.layers.color.get('Col') or bm.loops.layers.color.new('Col')


def _face(bm, vs, alfas):
    lay = _cor(bm)
    f = bm.faces.new(vs)
    for lp in f.loops:
        lp[lay] = (1, 1, 1, alfas[lp.vert])


def mancha_suave(bm, c, r, z, a0=0.95):
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


def texto(nome, corpo, tam, pos, n):
    cu = bpy.data.curves.new(nome, 'FONT')
    cu.body = corpo
    cu.size = tam
    cu.materials.append(M['estencil'])
    o = bpy.data.objects.new(nome, cu)
    sc.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (PI / 2, 0, math.atan2(n.y, n.x) + PI / 2)
    return o


def monte(bm, c, rx, ry, h, z0, n=20, m=8, fase=0.0, rot=0.0):
    """Monte de granel: cone baixo de encosta côncava com calombos; devolve a função de altura."""
    def alt(rho, ang):
        b = 1 + 0.12 * math.sin(3 * ang + fase) + 0.08 * math.sin(7 * ang + fase * 1.7)
        return z0 + h * max(0.0, 1 - rho) ** 1.6 * b
    topo = bm.verts.new((c[0], c[1], alt(0, 0)))
    aneis = []
    for k in range(1, m + 1):
        rho = k / m
        anel = []
        for i in range(n):
            a = i * 2 * PI / n
            w = 1 + 0.18 * math.sin(2 * a + fase) * rho + 0.07 * math.sin(5 * a + fase)
            x, y = math.cos(a) * rx * rho * w, math.sin(a) * ry * rho * w
            ca, sa = math.cos(rot), math.sin(rot)
            anel.append(bm.verts.new((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca, alt(rho, a) + (0.002 if k < m else 0.0))))
        aneis.append(anel)
    for i in range(n):
        bm.faces.new((topo, aneis[0][i], aneis[0][(i + 1) % n]))
    for A, Bn in zip(aneis, aneis[1:]):
        for i in range(n):
            bm.faces.new((A[i], Bn[i], Bn[(i + 1) % n], A[(i + 1) % n]))
    return alt


def pedrisco(bm, c, rx, ry, z, n, rmin=0.006, rmax=0.016):
    for k in range(n):
        a = random.uniform(0, 2 * PI)
        rho = random.uniform(0, 1) ** 0.6
        pedra(bm, (c[0] + math.cos(a) * rx * rho, c[1] + math.sin(a) * ry * rho, z), random.uniform(rmin, rmax), 0.6)


# ------------------------------------------------------------------ medidas
R = 0.95                     # raio do costado
AMP, PASSO = 0.011, 0.076    # chapa ondulada (onda horizontal)
ZL = 0.06                    # topo da laje
Z_VA0, Z_VA1 = 0.98, 1.08    # viga-anel sobre as colunas
Z_C0, Z_C1 = 1.08, 3.20      # costado
Z_APICE = 3.47
ANEIS = [1.62, 2.18, 2.72]
EMENDAS = [1.35, 1.90, 2.45, 2.96]
ESTEIOS = [math.radians(11.25 + 45 * k) for k in range(8)] + [math.radians(-123.75), math.radians(-101.25)]
A_JAN = math.radians(-112.5)                 # faixa da IA
JAN_DA = math.radians(6.0)
Z_J0, Z_J1 = 1.30, 2.95
A_VIS = math.radians(-157.5)                 # visor de nível
Z_V0, Z_V1 = 1.22, 3.06
TROCA = (math.radians(-146.25), math.radians(-123.75), 2.18, 2.72)    # chapa trocada (zarcão)
AMASSADOS = [(math.radians(-75), 1.42, 0.14, 0.04), (math.radians(-140), 2.98, 0.10, 0.03),
             (math.radians(-95), 2.62, 0.09, 0.022), (math.radians(150), 2.0, 0.13, 0.035)]
PERNAS = [math.radians(22.5 + 45 * k) for k in range(8)]
X_EL = -1.20                                  # elevador
Y_SOBE, Y_DESCE = (-0.24, -0.03), (0.03, 0.24)
Z_EL0, Z_EL1 = 0.50, 3.78
Z_JE0, Z_JE1 = 1.50, 2.62                     # janela das canecas
A_ROSCA = Vector((0, 0.22, 0.29))             # rosca extratora: do pé (sob o funil) à bica sul
B_ROSCA = Vector((0, -1.16, 0.68))
R_ROSCA = 0.10


def ang_dif(a, b):
    return (a - b + PI) % (2 * PI) - PI


def amassado(a, z):
    s = 0.0
    for (aa, za, ra, pa) in AMASSADOS:
        du = ang_dif(a, aa) * R
        s += pa * math.exp(-(du * du + (z - za) ** 2) / (ra * ra))
    return s


def r_costado(a, z):
    return R + AMP * math.sin(2 * PI * z / PASSO) - amassado(a, z)


def P_cil(a, r, z):
    return Vector((math.cos(a) * r, math.sin(a) * r, z))


def z_teto(r):
    return Z_C1 + 0.03 + (Z_APICE - Z_C1 - 0.03) * (1 - (r - 0.12) / (R + 0.06 - 0.12))


# ------------------------------------------------------------------ superfícies
def superficie(sel, na, nz, pos, fechado=True):
    """Grade (i ângulo, j altura); sel(i, j) devolve a chave (nome, mat, liso) da célula ou None (furo)."""
    vs = {}

    def V(k, i, j):
        i = i % na if fechado else i
        kk = (k, i, j)
        if kk not in vs:
            vs[kk] = B(*k).verts.new(pos(i, j))
        return vs[kk]
    for i in range(na if fechado else na - 1):
        for j in range(nz - 1):
            k = sel(i, j)
            if k is None:
                continue
            B(*k).faces.new((V(k, i, j), V(k, i + 1, j), V(k, i + 1, j + 1), V(k, i, j + 1)))


def anel(bm, r0, r1, z0, z1, n=144, gap=None, a0=0.0):
    """Anel de seção retangular (r0..r1, z0..z1); gap=(a_ini, a_fim) pula os segmentos dentro do intervalo."""
    pts = [[bm.verts.new(P_cil(a0 + i * 2 * PI / n, r, z)) for r, z in ((r0, z0), (r1, z0), (r1, z1), (r0, z1))] for i in range(n)]
    for i in range(n):
        if gap is not None:
            am = a0 + (i + 0.5) * 2 * PI / n
            if abs(ang_dif(am, (gap[0] + gap[1]) / 2)) < (gap[1] - gap[0]) / 2:
                continue
        A, Bn = pts[i], pts[(i + 1) % n]
        for j in range(4):
            bm.faces.new((A[j], Bn[j], Bn[(j + 1) % 4], A[(j + 1) % 4]))
    if gap is not None:                        # tampa as pontas cortadas
        for i in range(n):
            am0 = a0 + (i - 0.5) * 2 * PI / n
            am1 = a0 + (i + 0.5) * 2 * PI / n
            d0 = abs(ang_dif(am0, (gap[0] + gap[1]) / 2)) < (gap[1] - gap[0]) / 2
            d1 = abs(ang_dif(am1, (gap[0] + gap[1]) / 2)) < (gap[1] - gap[0]) / 2
            if d0 != d1:
                bm.faces.new(pts[i])


def meia_cil(bm, c, r, y0, y1, n=14):
    """Meio cilindro deitado (eixo y), parte de cima, com tampas."""
    fr, tr = [], []
    for k in range(n + 1):
        a = PI * k / n
        x, z = math.cos(a) * r, math.sin(a) * r
        fr.append(bm.verts.new((c[0] + x, y0, c[2] + z)))
        tr.append(bm.verts.new((c[0] + x, y1, c[2] + z)))
    for k in range(n):
        bm.faces.new((fr[k], fr[k + 1], tr[k + 1], tr[k]))
    bm.faces.new(fr)
    bm.faces.new(list(reversed(tr)))


def parafuso(bm, p, n, r=0.006, h=0.006):
    cil(bm, Vector(p) + Vector(n) * h / 2, r, h, Vector(n), lados=6)


# ================================================================== LAJE, COLUNAS, SAIA
bc = B('laje', 'concreto')
caixa_de(bc, (-1.48, -1.48, 0), (1.48, 1.48, ZL))
bl = B('laje_listras', 'listras')
e = 0.11
for a, b in (((-1.48, -1.48), (1.48, -1.48 + e)), ((-1.48, 1.48 - e), (1.48, 1.48)), ((-1.48, -1.48 + e), (-1.48 + e, 1.48 - e)),
             ((1.48 - e, -1.48 + e), (1.48, 1.48 - e))):
    caixa_de(bl, (a[0], a[1], ZL - 0.004), (b[0], b[1], ZL + 0.0015))
for k in range(16):                                              # pó claro e pó de minério na laje
    a = random.uniform(0, 2 * PI)
    r = random.uniform(0.7, 1.35)
    mancha_suave(B('po_s', 'po_s'), (math.cos(a) * r, math.sin(a) * r), random.uniform(0.12, 0.3), ZL + 0.0018, 0.4)
for c, r in (((0, -1.05), 0.45), ((-1.2, -0.75), 0.35), ((0.1, -0.5), 0.3), ((-0.75, -0.2), 0.25), ((0.4, -1.25), 0.22)):
    mancha_suave(B('pomin_s', 'pomin_s'), c, r, ZL + 0.0024, 0.9)
mancha_suave(B('oleo_s', 'oleo_s'), (0.0, 0.5), 0.17, ZL + 0.003, 0.95)       # sob o motor da rosca
mancha_suave(B('oleo_s', 'oleo_s'), (0.62, -0.18), 0.12, ZL + 0.003, 0.8)      # sob a válvula da comporta
for k in range(40):
    pedra(B('cascalho', 'concreto'), (random.uniform(-1.4, 1.4), random.uniform(-1.4, 1.4), ZL + 0.003), random.uniform(0.006, 0.014), 0.5)

bf, ba, bfe = B('ferro', 'ferro'), B('aco', 'aco'), B('colunas', 'amarelo')
for k, a in enumerate(PERNAS):
    n = Vector((math.cos(a), math.sin(a), 0))
    Q = quadro(n)
    c = n * R
    # placa de base, graute e quatro chumbadores com porca e arruela
    caixa(B('graute', 'graute'), c + Vector((0, 0, ZL + 0.012)), (0.24, 0.24, 0.024), Q)
    caixa(bf, c + Vector((0, 0, ZL + 0.032)), (0.2, 0.2, 0.016), Q)
    for su in (-1, 1):
        for sv in (-1, 1):
            p = c + Q @ Vector((su * 0.075, sv * 0.075, 0)) + Vector((0, 0, ZL + 0.04))
            cil(ba, p + Vector((0, 0, 0.02)), 0.008, 0.04, lados=8)
            cil(bf, p + Vector((0, 0, 0.004)), 0.018, 0.004, lados=10)
            cil(bf, p + Vector((0, 0, 0.012)), 0.014, 0.012, lados=6)
    # perfil H: duas mesas e a alma; nervuras na base
    h0, h1 = ZL + 0.04, Z_VA0
    for sv in (-1, 1):
        caixa(bfe, c + Q @ Vector((0, sv * 0.055, 0)) + Vector((0, 0, (h0 + h1) / 2)), (0.12, 0.012, h1 - h0), Q)
    caixa(bfe, c + Vector((0, 0, (h0 + h1) / 2)), (0.012, 0.1, h1 - h0), Q)
    for su in (-1, 1):
        caixa(bfe, c + Q @ Vector((su * 0.035, 0, 0)) + Vector((0, 0, h0 + 0.05)), (0.05, 0.1, 0.09), Q)
    # listras de perigo no pé (manga) e escorrido de ferrugem descendo da viga
    caixa(B('listras', 'listras'), c + Q @ Vector((0, 0.0625, 0)) + Vector((0, 0, h0 + 0.17)), (0.122, 0.003, 0.22), Q)
    faixa_suave(B('escorrido_s', 'escorrido_s'), c + Q @ Vector((random.uniform(-0.03, 0.03), 0.0625, 0)) + Vector((0, 0, h1 - 0.01)),
                c + Q @ Vector((0, 0.0625, 0)) + Vector((0, 0, h1 - random.uniform(0.25, 0.55))), Q @ Vector((0.012, 0, 0)))
    # parafusos da ligação coluna-viga
    for su in (-1, 1):
        for dz in (0.03, 0.065):
            parafuso(bf, c + Q @ Vector((su * 0.035, 0.061, 0)) + Vector((0, 0, h1 - dz)), n, 0.007)

# viga-anel (caixão) sobre as colunas + chapa de fundo do costado
anel(B('viga_anel', 'amarelo'), R - 0.1, R + 0.065, Z_VA0, Z_VA1, n=96)
for k in range(96):
    a = (k + 0.5) * 2 * PI / 96
    parafuso(bf, P_cil(a, R + 0.065, (Z_VA0 + Z_VA1) / 2), Vector((math.cos(a), math.sin(a), 0)), 0.006)

# saia corrugada (onda vertical) nos vãos norte, nordeste, leste e noroeste; os outros ficam abertos (funil à vista)
VAOS_SAIA = [math.radians(d) for d in (0, 45, 90, 135)]
R_S = R - 0.075


def sel_saia(i, j):
    a = (i + 0.5) * 2 * PI / 720
    for v in VAOS_SAIA:
        if abs(ang_dif(a, v)) < math.radians(22.5):
            return ('saia', 'grafite', True)
    return None


superficie(sel_saia, 720, 2, lambda i, j: P_cil(i * 2 * PI / 720, R_S + 0.007 * math.sin(i * 2 * PI / 720 * 84), ZL + 0.08 + j * (Z_VA0 - ZL - 0.08)))
# barras da saia (em cima e embaixo), só nos vãos fechados
for v in VAOS_SAIA:
    for z in (ZL + 0.1, Z_VA0 - 0.03):
        bmq = B('saia_quadro', 'ferro')
        for k in range(12):
            a0_ = v - math.radians(18.5) + k * math.radians(37) / 12
            a1_ = a0_ + math.radians(37) / 12
            p0, p1 = P_cil(a0_, R_S + 0.012, z), P_cil(a1_, R_S + 0.012, z)
            viga(bmq, p0, p1, 0.022)
# remendo na saia leste
caixa(B('remendo', 'remendo'), P_cil(math.radians(-4), R_S + 0.012, 0.55), (0.2, 0.006, 0.16), quadro(Vector((math.cos(math.radians(-4)), math.sin(math.radians(-4)), 0))))

# contraventamento em X com esticador nos vãos sudoeste e sudeste
for v in (math.radians(-135), math.radians(-45)):
    a0_, a1_ = v - math.radians(22.5), v + math.radians(22.5)
    for (pa, za), (pb, zb) in (((a0_, ZL + 0.12), (a1_, Z_VA0 - 0.06)), ((a1_, ZL + 0.12), (a0_, Z_VA0 - 0.06))):
        p, q_ = P_cil(pa, R - 0.07, za), P_cil(pb, R - 0.07, zb)
        tubo(B('tirante', 'aco'), p, q_, 0.009, 8)
        m_ = p.lerp(q_, 0.3)
        u = (q_ - p).normalized()
        tubo(B('esticador', 'ferro'), m_ - u * 0.05, m_ + u * 0.05, 0.016, 6)
    for (pa, za) in ((a0_, ZL + 0.12), (a1_, Z_VA0 - 0.06), (a1_, ZL + 0.12), (a0_, Z_VA0 - 0.06)):
        n_ = Vector((math.cos(pa), math.sin(pa), 0))
        caixa(bf, P_cil(pa, R - 0.068, za), (0.06, 0.012, 0.06), quadro(n_))

# ================================================================== FUNIL, COMPORTA E ROSCA
Z_F1, Z_F0 = Z_VA0, 0.56
R_F1, R_F0 = R - 0.1, 0.15
bm_f = B('funil', 'funil', True)


def pos_funil(i, j):
    a = i * 2 * PI / 96
    t = j / 20
    r = R_F1 + (R_F0 - R_F1) * t
    z = Z_F1 + (Z_F0 - Z_F1) * t
    d = 0.025 * math.exp(-((ang_dif(a, math.radians(-120)) * r) ** 2 + (z - 0.82) ** 2) / 0.012)     # amassado (batida)
    return P_cil(a, r - d, z)


superficie(lambda i, j: ('funil', 'funil', True), 96, 21, pos_funil)
for t in (0.33, 0.66):                                            # cintas do funil
    r = R_F1 + (R_F0 - R_F1) * t
    z = Z_F1 + (Z_F0 - Z_F1) * t
    anel(B('funil_cinta', 'grafite'), r - 0.005, r + 0.02, z - 0.015, z + 0.015, n=64)
    for k in range(24):
        a = (k + 0.5) * 2 * PI / 24
        parafuso(bf, P_cil(a, r + 0.02, z), Vector((math.cos(a), math.sin(a), 0)), 0.006)
for k in range(8):                                                # costuras radiais do funil
    a = k * 2 * PI / 8 + 0.2
    p0 = P_cil(a, R_F1 + 0.006, Z_F1 - 0.01)
    p1 = P_cil(a, R_F0 + 0.006, Z_F0 + 0.01)
    viga(B('funil_costura', 'grafite'), p0, p1, 0.016)
# escorridos no funil e fuligem/óleo
def r_funil(z):
    return R_F1 + (R_F0 - R_F1) * (Z_F1 - z) / (Z_F1 - Z_F0)


for a_d in (-100, -140, -60, 170):
    a = math.radians(a_d) + random.uniform(-0.1, 0.1)
    z0, z1 = random.uniform(0.86, 0.95), random.uniform(0.6, 0.7)
    faixa_suave(B('escorrido_s', 'escorrido_s'), P_cil(a, r_funil(z0) + 0.009, z0), P_cil(a, r_funil(z1) + 0.009, z1),
                Vector((-math.sin(a), math.cos(a), 0)) * 0.025, seg=8)
# bocal do funil com flange
cil(B('funil_bocal', 'ferro'), Vector((0, 0, Z_F0 - 0.012)), R_F0 + 0.04, 0.024, lados=24)
for k in range(10):
    a = k * 2 * PI / 10
    parafuso(bf, P_cil(a, R_F0 + 0.025, Z_F0), UP, 0.007)

# comporta de gaveta: caixa, guia da gaveta e braço que segura a camisa do pistão
Z_G0, Z_G1 = 0.46, Z_F0 - 0.024
bg = B('comporta', 'amarelo')
caixa_de(bg, (-0.2, -0.17, Z_G0), (0.2, 0.17, Z_G1))
caixa_de(B('comporta_fresta', 'buraco'), (0.199, -0.13, 0.468), (0.203, 0.13, 0.484))
for su in (-1, 1):
    caixa_de(bg, (0.2, su * 0.075 - 0.012, 0.47), (0.86, su * 0.075 + 0.012, 0.49))          # braços
caixa_de(bg, (0.82, -0.09, 0.455), (0.86, 0.09, 0.505))                                     # travessa traseira
for x in (-0.18, 0.18):
    for y in (-0.15, 0.15):
        parafuso(bf, (x, y, Z_G1), UP, 0.007)
caixa_de(B('listras', 'listras'), (-0.2, -0.1705, Z_G0 + 0.01), (0.2, -0.17, Z_G1 - 0.01))

# pistão da comporta: camisa presa na travessa, haste na orelha da gaveta (a gaveta corre para +x ao abrir)
Z_P = 0.48
camisa_x0, camisa_x1 = 0.47, 0.82
cil(B('camisa', 'amarelo', True), Vector(((camisa_x0 + camisa_x1) / 2, 0, Z_P)), 0.038, camisa_x1 - camisa_x0, Vector((1, 0, 0)), lados=20)
for x in (camisa_x0 + 0.012, camisa_x1 - 0.012):
    cil(bf, Vector((x, 0, Z_P)), 0.046, 0.024, Vector((1, 0, 0)), lados=8)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        cil(ba, Vector((x, math.cos(a) * 0.04, Z_P + math.sin(a) * 0.04)), 0.005, 0.03, Vector((1, 0, 0)), lados=6)
# portas do pistão e mangueiras até a válvula na coluna sudeste
A_VAL = PERNAS[7]                     # -22,5°
n_val = Vector((math.cos(A_VAL), math.sin(A_VAL), 0))
P_VAL = n_val * (R - 0.1) + Vector((0, 0, 0.5))
caixa(B('valvula', 'grafite'), P_VAL, (0.12, 0.06, 0.16), quadro(n_val))
caixa(bf, n_val * (R - 0.062) + Vector((0, 0, 0.5)), (0.16, 0.012, 0.2), quadro(n_val))
for dz in (-0.05, 0.0, 0.05):
    cil(B('solenoide', 'ferro'), P_VAL - n_val * 0.04 + Vector((0, 0, dz)), 0.018, 0.04, n_val, lados=10)
for x, dz in ((camisa_x0 + 0.04, 0.045), (camisa_x1 - 0.04, 0.045)):
    p = Vector((x, 0, Z_P + 0.045))
    cil(B('porta', 'cromo'), p, 0.012, 0.02, lados=8)
    alvo = P_VAL + quadro(n_val) @ Vector((0.03 if x < 0.6 else -0.03, -0.02, 0.08))
    mangueira(B('mangueira', 'borracha'), bezier(p + Vector((0, 0, 0.01)), p + Vector((0, 0, 0.12)), alvo + Vector((0, 0, 0.12)), alvo, 10), 0.011)
mangueira(B('mangueira', 'borracha'), bezier(P_VAL - Vector((0, 0, 0.08)), P_VAL - Vector((0, 0, 0.25)), P_VAL - n_val * 0.05 - Vector((0, 0, 0.35)), P_VAL - n_val * 0.05 - Vector((0, 0, 0.42)) + Vector((0, 0, -0.0)), 8), 0.013)
cil(bf, P_VAL - n_val * 0.05 + Vector((0, 0, ZL + 0.01 - 0.5)), 0.03, 0.02, lados=8)

# gaveta (animada) e haste (presa na orelha)
bm = bmesh.new()
caixa_de(bm, (-0.18, -0.13, 0.47), (0.18, 0.13, 0.482))
caixa_de(bm, (0.18, -0.02, 0.462), (0.215, 0.02, 0.5))
gaveta = ob('silo_gaveta', bm, 'aco')
bm = bmesh.new()
cil(bm, Vector((0.215 + 0.17, 0, Z_P)), 0.017, 0.34, Vector((1, 0, 0)), lados=16)
haste = ob('silo_haste', bm, 'cromo', liso=True)
haste.parent = gaveta

# rosca extratora inclinada: calha tubular (janela gradeada em cima), hélice que gira, motor e redutor atrás
D_ROS = (B_ROSCA - A_ROSCA)
L_ROS = D_ROS.length
E_ROS = vazio('silo_rosca_eixo')
E_ROS.location = A_ROSCA
E_ROS.rotation_mode = 'QUATERNION'
E_ROS.rotation_quaternion = D_ROS.normalized().to_track_quat('Z', 'Y')
Q_ROS = E_ROS.rotation_quaternion.to_matrix()


def W_ROS(x, y, z):
    return A_ROSCA + Q_ROS @ Vector((x, y, z))


T_INL = (A_ROSCA.y - 0.0) / (A_ROSCA.y - B_ROSCA.y) * L_ROS      # boca da comporta (y=0)
JR0, JR1 = T_INL + 0.25, T_INL + 0.75                             # janela gradeada


def pos_calha(i, j):
    a = i * 2 * PI / 32
    z = -0.06 + j * (L_ROS + 0.12) / 60
    return Vector((math.cos(a) * R_ROSCA, math.sin(a) * R_ROSCA, z))


def sel_calha(i, j):
    a = (i + 0.5) * 2 * PI / 32
    z = -0.06 + (j + 0.5) * (L_ROS + 0.12) / 60
    if abs(ang_dif(a, PI / 2)) < math.radians(55) and JR0 < z < JR1:
        return None
    if abs(ang_dif(a, PI / 2)) < math.radians(40) and abs(z - T_INL) < 0.1:
        return None
    return ('calha', 'amarelo', True)


bmc = bmesh.new()
BMS_TMP = BMS.copy()
BMS.clear()
superficie(sel_calha, 32, 61, pos_calha)
calha = ob('silo_calha', BMS.pop(('calha', 'amarelo', True)), 'amarelo', E_ROS, liso=True)
BMS.update(BMS_TMP)
bm = bmesh.new()
for z in (-0.05, T_INL - 0.14, T_INL + 0.14, JR0 - 0.02, JR1 + 0.02, L_ROS - 0.25, L_ROS + 0.05):  # flanges
    cil(bm, Vector((0, 0, z)), R_ROSCA + 0.022, 0.018, lados=32)
    for k in range(10):
        a = k * 2 * PI / 10 + 0.3
        cil(bm, Vector((math.cos(a) * (R_ROSCA + 0.015), math.sin(a) * (R_ROSCA + 0.015), z)), 0.006, 0.026, lados=6)
cil(bm, Vector((0, 0, -0.065)), R_ROSCA + 0.01, 0.012, lados=32)                     # tampa do pé
for k in range(5):                                                                    # grade da janela
    a = PI / 2 + math.radians(-44 + 22 * k)
    tubo(bm, Vector((math.cos(a) * (R_ROSCA + 0.004), math.sin(a) * (R_ROSCA + 0.004), JR0 - 0.02)),
         Vector((math.cos(a) * (R_ROSCA + 0.004), math.sin(a) * (R_ROSCA + 0.004), JR1 + 0.02)), 0.006, 6)
for z in (JR0 + 0.17, JR0 + 0.34):
    for k in range(10):
        a0_ = PI / 2 + math.radians(-55 + 11 * k)
        a1_ = a0_ + math.radians(11)
        tubo(bm, Vector((math.cos(a0_) * (R_ROSCA + 0.008), math.sin(a0_) * (R_ROSCA + 0.008), z)),
             Vector((math.cos(a1_) * (R_ROSCA + 0.008), math.sin(a1_) * (R_ROSCA + 0.008), z)), 0.006, 6)
# boca de entrada (pescoço quadrado até a transição da comporta)
ob('silo_calha_ferro', bm, 'ferro', E_ROS)
# pescoço da comporta até a calha (mundo)
p_in = W_ROS(0, 0, T_INL)
caixa_de(B('comporta', 'amarelo'), (-0.085, -0.085, p_in.z + R_ROSCA * 0.75), (0.085, 0.085, Z_G0))

# hélice (gira em volta do eixo local z)
bm = bmesh.new()
n_v = int((L_ROS + 0.02) / 0.13 * 28)
ri, ro = 0.024, R_ROSCA - 0.012
prev = None
for k in range(n_v + 1):
    t = k / 28 * 2 * PI
    z = -0.02 + k * 0.13 / 28
    par = (bm.verts.new((math.cos(t) * ri, math.sin(t) * ri, z)), bm.verts.new((math.cos(t) * ro, math.sin(t) * ro, z)))
    if prev:
        bm.faces.new((prev[0], prev[1], par[1], par[0]))
    prev = par
cil(bm, Vector((0, 0, L_ROS / 2)), ri, L_ROS + 0.1, lados=16)
helice = ob('silo_helice', bm, 'aco', E_ROS)
helice.modifiers.new('esp', 'SOLIDIFY').thickness = 0.008
# granel dentro da calha (fundo), visto pela janela
bm = bmesh.new()
for k in range(70):
    z = random.uniform(JR0 - 0.02, JR1 + 0.02)
    a = random.uniform(-PI / 2 - 0.9, -PI / 2 + 0.9)
    r = random.uniform(0.04, ro)
    pedra(bm, (math.cos(a) * r, math.sin(a) * r, z), random.uniform(0.008, 0.016), 0.8)
ob('silo_granel_calha', bm, 'minerio', E_ROS)

# acionamento atrás do pé: redutor, acoplamento, motor com aletas e ventoinha, base até a laje
bm_r = bmesh.new()
caixa(bm_r, Vector((0, 0.0, -0.15)), (0.17, 0.2, 0.16))
cil(bm_r, Vector((0, 0, -0.08)), 0.05, 0.04, lados=16)
ob('silo_redutor_rosca', bm_r, 'amarelo', E_ROS)
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.35)), 0.075, 0.24, lados=24)
ob('silo_motor_rosca', bm, 'grafite', E_ROS, liso=True)
bm = bmesh.new()
for k in range(16):
    a = k * 2 * PI / 16
    caixa(bm, Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, -0.37)), (0.012, 0.012, 0.2), Matrix.Rotation(a, 3, 'Z'))
cil(bm, Vector((0, 0, -0.495)), 0.08, 0.03, lados=24)
for k in range(6):
    caixa(bm, Vector((0, 0, -0.511)), (0.15, 0.006, 0.003), Matrix.Rotation(k * PI / 6, 3, 'Z'))
ob('silo_motor_aletas', bm, 'ferro', E_ROS)
bm = bmesh.new()
caixa(bm, Vector((0, 0.1, -0.33)), (0.08, 0.04, 0.07))                    # caixa de ligação do motor
ob('silo_motor_cx', bm, 'grafite', E_ROS)
p_cx = W_ROS(0, 0.12, -0.33)
mangueira(B('cabo', 'borracha'), bezier(p_cx, p_cx + Vector((0.08, 0.0, 0.06)), Vector((0.12, 0.62, 0.1)), Vector((0.06, 0.62, ZL + 0.02)), 10), 0.011)
caixa_de(B('cx_piso', 'ferro'), (-0.06, 0.56, ZL), (0.06, 0.68, ZL + 0.05))
p_mt = W_ROS(0, -0.07, -0.3)
caixa_de(B('base_motor', 'ferro'), (-0.12, p_mt.y - 0.1, ZL), (0.12, p_mt.y + 0.12, p_mt.z - 0.005))
# suportes da calha até a laje (dois cavaletes com berço)
for t in (0.55, 0.88):
    p = A_ROSCA + D_ROS * t
    zb = p.z - R_ROSCA - 0.01
    for sx in (-1, 1):
        viga(B('cavalete', 'grafite'), (sx * 0.13, p.y, ZL + 0.01), (sx * 0.06, p.y, zb), 0.035)
        caixa_de(bf, (sx * 0.13 - 0.04, p.y - 0.04, ZL), (sx * 0.13 + 0.04, p.y + 0.04, ZL + 0.012))
    caixa_de(B('cavalete', 'grafite'), (-0.1, p.y - 0.025, zb - 0.02), (0.1, p.y + 0.025, zb + 0.005))
# bica de descarga (desce da ponta da rosca) e caçamba de retirada onde o braço pega
p_b = W_ROS(0, 0, L_ROS - 0.06)
Z_BICA = 0.42
bb = B('bica', 'amarelo')
for a, b in (((-0.075, -0.075), (0.075, -0.06)), ((-0.075, 0.06), (0.075, 0.075)), ((-0.075, -0.06), (-0.06, 0.06)), ((0.06, -0.06), (0.075, 0.06))):
    caixa_de(bb, (a[0], p_b.y + a[1], Z_BICA), (b[0], p_b.y + b[1], p_b.z - 0.05))
caixa_de(B('bica_borda', 'ferro'), (-0.085, p_b.y - 0.085, Z_BICA - 0.012), (0.085, p_b.y + 0.085, Z_BICA + 0.012))
# caçamba
Y_CA = p_b.y
bk = B('cacamba', 'grafite')
X0, X1, Y0, Y1, Zc = -0.17, 0.17, Y_CA - 0.3, Y_CA + 0.12, 0.26
for a, b in (((X0, Y0), (X1, Y0 + 0.02)), ((X0, Y1 - 0.02), (X1, Y1)), ((X0, Y0), (X0 + 0.02, Y1)), ((X1 - 0.02, Y0), (X1, Y1))):
    caixa_de(bk, (a[0], a[1], ZL), (b[0], b[1], Zc))
caixa_de(bk, (X0, Y0, ZL), (X1, Y1, ZL + 0.02))
caixa_de(B('listras', 'listras'), (X0, Y0 - 0.003, Zc - 0.08), (X1, Y0, Zc - 0.01))
for x in (X0 - 0.01, X1 - 0.02):
    caixa_de(bf, (x, Y0 - 0.01, ZL), (x + 0.03, Y1 + 0.01, Zc + 0.012))
alt_m = monte(B('monte_cacamba', 'minerio', True), (0.0, Y_CA - 0.06), 0.145, 0.2, 0.075, 0.17, fase=1.2)
pedrisco(B('pedrisco', 'minerio'), (0.0, Y_CA - 0.06), 0.1, 0.14, 0.215, 30)
# derramado em volta da caçamba e no chão
for c, rx, ry, h, ro_ in (((0.34, Y_CA - 0.2), 0.14, 0.1, 0.045, 0.3), ((-0.3, Y_CA - 0.14), 0.12, 0.09, 0.035, 1.0),
                          ((0.3, Y0 + 0.04), 0.13, 0.07, 0.03, 0.0)):
    monte(B('monte_chao', 'minerio', True), c, rx, ry, h, ZL, fase=ro_ * 3, rot=ro_)
    pedrisco(B('pedrisco', 'minerio'), c, rx * 1.6, ry * 1.6, ZL + 0.004, 18, 0.005, 0.012)
mancha_suave(B('oleo_s', 'oleo_s'), (0.0, Y_CA + 0.2), 0.08, ZL + 0.003, 0.5)

# ================================================================== COSTADO
SEL_CAS = ('casca', 'galv', True)
SEL_TRO = ('chapa_trocada', 'zarcao', True)
NA_C = 192
NZ_C = int((Z_C1 - Z_C0) / (PASSO / 6)) + 1


def z_cas(j):
    return Z_C0 + (Z_C1 - Z_C0) * j / (NZ_C - 1)


def sel_cas(i, j):
    a = (i + 0.5) * 2 * PI / NA_C
    z = (z_cas(j) + z_cas(j + 1)) / 2
    if abs(ang_dif(a, A_JAN)) < JAN_DA and Z_J0 < z < Z_J1:
        return None
    if TROCA[0] < a < TROCA[1] and TROCA[2] < z < TROCA[3]:
        return SEL_TRO
    return SEL_CAS


superficie(sel_cas, NA_C, NZ_C, lambda i, j: P_cil(i * 2 * PI / NA_C, r_costado(i * 2 * PI / NA_C, z_cas(j)), z_cas(j)))

RC = R + AMP                                # face de fora das cristas
# anéis de reforço (cantoneira: aba horizontal + aba vertical), com parafusos
for z in ANEIS:
    anel(B('aneis', 'amarelo'), RC - 0.004, RC + 0.06, z - 0.007, z + 0.007, n=144)
    anel(B('aneis', 'amarelo'), RC + 0.048, RC + 0.06, z - 0.05, z - 0.007, n=144)
    for k in range(48):
        a = (k + 0.5) * 2 * PI / 48
        parafuso(bf, P_cil(a, RC + 0.062, z - 0.028), Vector((math.cos(a), math.sin(a), 0)), 0.006)
# anel de coroamento e chapa de base
anel(B('aneis', 'amarelo'), R - 0.02, RC + 0.07, Z_C1 - 0.03, Z_C1 + 0.03, n=144)
anel(B('aneis', 'amarelo'), R - 0.02, RC + 0.012, Z_C0, Z_C0 + 0.06, n=144)
# cintas nas emendas (sem a faixa da IA), parafusadas
for z in EMENDAS:
    anel(B('cintas', 'galv2'), RC - 0.002, RC + 0.006, z - 0.022, z + 0.022, n=192, gap=(A_JAN - JAN_DA - 0.04, A_JAN + JAN_DA + 0.04))
    for k in range(96):
        a = (k + 0.5) * 2 * PI / 96
        if abs(ang_dif(a, A_JAN)) < JAN_DA + 0.05:
            continue
        for dz in (-0.011, 0.011):
            parafuso(B('parafusos', 'aco'), P_cil(a, RC + 0.006, z + dz), Vector((math.cos(a), math.sin(a), 0)), 0.0045, 0.005)
# montantes verticais (perfil chapéu) aparafusados
for a in ESTEIOS:
    n_ = Vector((math.cos(a), math.sin(a), 0))
    Q = quadro(n_)
    caixa(B('montantes', 'galv2'), P_cil(a, RC + 0.016, (Z_C0 + 0.06 + Z_C1 - 0.03) / 2), (0.05, 0.03, Z_C1 - Z_C0 - 0.09), Q)
    caixa(B('montantes', 'galv2'), P_cil(a, RC + 0.003, (Z_C0 + 0.06 + Z_C1 - 0.03) / 2), (0.085, 0.006, Z_C1 - Z_C0 - 0.09), Q)
    z = Z_C0 + 0.12
    while z < Z_C1 - 0.08:
        for su in (-1, 1):
            parafuso(B('parafusos', 'aco'), P_cil(a, RC + 0.006, z) + Q @ Vector((su * 0.034, 0, 0)), n_, 0.0045, 0.005)
        z += 0.12

# chapa trocada: borda soldada e parafusos novos (cromados)
a0_, a1_, z0_, z1_ = TROCA
for k in range(25):
    a = a0_ + (a1_ - a0_) * k / 24
    for z in (z0_ + 0.012, z1_ - 0.012):
        parafuso(B('parafusos_novos', 'cromo'), P_cil(a, RC + 0.001, z), Vector((math.cos(a), math.sin(a), 0)), 0.0045, 0.005)


def chapa_curva(bm, a_c, z_c, w, h, r, esp=0.004):
    """Chapa curva (setor de cilindro) centrada em (a_c, z_c)."""
    da = w / 2 / r
    n = 10
    for k in range(n):
        for sgn, rr in ((0, r), (1, r + esp)):
            pass
    pts = []
    for k in range(n + 1):
        a = a_c - da + 2 * da * k / n
        pts.append([bm.verts.new(P_cil(a, rr, z)) for rr, z in ((r, z_c - h / 2), (r + esp, z_c - h / 2), (r + esp, z_c + h / 2), (r, z_c + h / 2))])
    for A, Bn in zip(pts, pts[1:]):
        for j in range(4):
            bm.faces.new((A[j], Bn[j], Bn[(j + 1) % 4], A[(j + 1) % 4]))
    bm.faces.new(pts[0])
    bm.faces.new(list(reversed(pts[-1])))


# remendos aparafusados (um soldado), com escorrido
for a_d, z_c, w, h, sold in ((-90, 2.02, 0.2, 0.17, False), (-45, 1.48, 0.17, 0.2, True), (-92, 2.85, 0.13, 0.12, False)):
    a_c = math.radians(a_d)
    chapa_curva(B('remendo', 'remendo', True), a_c, z_c, w, h, RC + 0.002)
    for su in (-1, 0, 1):
        for sz in (-1, 1):
            a = a_c + su * (w / 2 - 0.015) / RC
            parafuso(bf, P_cil(a, RC + 0.006, z_c + sz * (h / 2 - 0.015)), Vector((math.cos(a), math.sin(a), 0)), 0.006)
    if sold:
        chapa_curva(B('solda', 'solda', True), a_c, z_c + h / 2 + 0.003, w + 0.01, 0.006, RC + 0.001, 0.005)
        chapa_curva(B('solda', 'solda', True), a_c, z_c - h / 2 - 0.003, w + 0.01, 0.006, RC + 0.001, 0.005)


def escorrido_cil(bm, a, z_top, comp, w=0.022, seg=14):
    """Escorrido de ferrugem que acompanha a onda do costado (fica colado nas cristas e nos vales)."""
    alf = {}
    fila = []
    for i in range(seg + 1):
        t = i / seg
        z = z_top - comp * t
        ww = w * (1 - 0.6 * t) * (1 + 0.2 * math.sin(i * 1.9))
        da = ww / R
        par = []
        for aa in (a - da, a + da):
            v = bm.verts.new(P_cil(aa, r_costado(aa, z) + 0.0016, z))
            alf[v] = 0.9 * (1 - t) ** 0.8
            par.append(v)
        fila.append(par)
    for (p, q_), (r_, s_) in zip(fila, fila[1:]):
        _face(bm, (p, q_, s_, r_), alf)


for k in range(26):                                        # ferrugem descendo dos anéis, cintas e remendos
    a = random.uniform(-PI, PI)
    if abs(ang_dif(a, A_JAN)) < JAN_DA + 0.05:
        continue
    z0 = random.choice(ANEIS + EMENDAS + [Z_C1 - 0.03]) - 0.05
    escorrido_cil(B('escorrido_s', 'escorrido_s'), a, z0, random.uniform(0.15, 0.5))
for a_d, z in ((-90, 1.93), (-45, 1.38), (-60, 2.52), (-140, 2.92), (-92, 2.79)):
    escorrido_cil(B('escorrido_s', 'escorrido_s'), math.radians(a_d), z, random.uniform(0.3, 0.55), 0.03)

# ------------------------------------------------------------------ faixa da IA: grade de granel perfeita demais
nJ = Vector((math.cos(A_JAN), math.sin(A_JAN), 0))
tJ = Vector((-nJ.y, nJ.x, 0))
QJ = Matrix((tJ, nJ, UP)).transposed()


def LJ(u, v, z):
    return QJ @ Vector((u, v, 0)) + Vector((0, 0, z))


uJ = R * math.sin(JAN_DA)
vJ = R * math.cos(JAN_DA)
bq = B('jan_quadro', 'grafite')
for su in (-1, 1):
    caixa(bq, LJ(su * (uJ + 0.012), vJ + 0.035, (Z_J0 + Z_J1) / 2), (0.034, 0.06, Z_J1 - Z_J0 + 0.06), QJ)
    z = Z_J0 + 0.03
    while z < Z_J1:
        parafuso(bf, LJ(su * (uJ + 0.012), vJ + 0.066, z), nJ, 0.006)
        z += 0.1
for z in (Z_J0 - 0.012, Z_J1 + 0.012):
    caixa(bq, LJ(0, vJ + 0.035, z), (2 * uJ + 0.058, 0.06, 0.03), QJ)
caixa(B('vidro_ia', 'vidro_ia'), LJ(0, vJ + 0.003, (Z_J0 + Z_J1) / 2), (2 * uJ + 0.004, 0.006, Z_J1 - Z_J0), QJ)
# caixa interna (fundo escuro) com o plano violeta atrás da grade
caixa(B('jan_fundo', 'buraco'), LJ(0, vJ - 0.16, (Z_J0 + Z_J1) / 2), (2 * uJ + 0.03, 0.01, Z_J1 - Z_J0 + 0.02), QJ)
for su in (-1, 1):
    caixa(B('jan_fundo', 'buraco'), LJ(su * (uJ + 0.008), vJ - 0.07, (Z_J0 + Z_J1) / 2), (0.006, 0.19, Z_J1 - Z_J0 + 0.02), QJ)
bm = bmesh.new()
caixa(bm, LJ(0, vJ - 0.148, 0.5), (2 * uJ, 0.004, 1.0), QJ)
campo_fundo = ob('silo_campo_fundo', bm, 'campo')
# cubos em grade (cada fileira é um objeto: some acima do nível)
PASSO_G = 0.062
FILEIRAS = []
z = Z_J0 + 0.035
while z < Z_J1 - 0.03:
    bm = bmesh.new()
    for iu in range(-1, 2):
        for v in (vJ - 0.04, vJ - 0.1):
            caixa(bm, LJ(iu * PASSO_G, v - 0.008, z), (0.045, 0.045, 0.045), QJ)
    FILEIRAS.append((z, ob('silo_grade_%02d' % len(FILEIRAS), bm, 'minerio_g')))
    z += PASSO_G
bm = bmesh.new()
caixa(bm, LJ(0, vJ - 0.08, 0), (2 * uJ, 0.13, 0.004), QJ)
plano_nivel = ob('silo_plano_nivel', bm, 'plano')
# emissores de campo: em cima e embaixo da faixa e em três pontos do anel do meio
EMISSORES = [(A_JAN, Z_J1 + 0.07), (A_JAN, Z_J0 - 0.07)] + [(math.radians(d), ANEIS[1] + 0.05) for d in (-22.5, 67.5, 157.5)]
for a, z in EMISSORES:
    n_ = Vector((math.cos(a), math.sin(a), 0))
    Q = quadro(n_)
    p = P_cil(a, RC + 0.05, z)
    caixa(B('emissor', 'grafite'), p, (0.09, 0.06, 0.07), Q)
    cil(B('emissor_lente', 'lente'), p + n_ * 0.032, 0.022, 0.008, n_, lados=16)
    cil(bf, p + n_ * 0.03, 0.03, 0.006, n_, lados=8)
    for su in (-1, 1):
        caixa(B('aletas', 'ferro'), p + Q @ Vector((su * 0.05, 0, 0)), (0.008, 0.05, 0.06), Q)
    mangueira(B('cabo', 'borracha'), bezier(p - Q @ Vector((0.03, 0.02, 0.03)), p - Q @ Vector((0.06, 0.02, 0.07)),
                                           p - Q @ Vector((0.09, 0.0, 0.1)) - n_ * 0.035, p - Q @ Vector((0.12, 0.0, 0.14)) - n_ * 0.035, 6), 0.006)
caixa(B('placa', 'ferro'), LJ(0, RC + 0.008, Z_J0 - 0.15), (0.26, 0.008, 0.08), QJ)
for su in (-1, 1):
    parafuso(B('parafusos', 'aco'), LJ(su * 0.115, RC + 0.012, Z_J0 - 0.15), nJ, 0.005, 0.004)
texto('silo_ia_txt', '20 000', 0.05, LJ(-0.085, RC + 0.0125, Z_J0 - 0.168), nJ)

# ------------------------------------------------------------------ visor de nível + régua com ponteiro
nV = Vector((math.cos(A_VIS), math.sin(A_VIS), 0))
QV = quadro(nV)
RV = RC + 0.11
PV = lambda dz, du=0.0, dr=0.0: P_cil(A_VIS, RV + dr, dz) + QV @ Vector((du, 0, 0))
cil(B('visor', 'vidro', True), PV((Z_V0 + Z_V1) / 2), 0.028, Z_V1 - Z_V0, lados=20)
for z in (Z_V0, Z_V1):
    cil(B('visor_metal', 'cromo', True), PV(z), 0.036, 0.04, lados=16)
    tubo(B('visor_metal', 'cromo', True), PV(z, 0, -0.11), PV(z), 0.016, 12)
    cil(bf, PV(z, 0, -0.1), 0.03, 0.012, nV, lados=8)
for z in ANEIS:
    caixa(bf, PV(z + 0.03, 0, -0.05), (0.03, 0.12, 0.02), QV)
    cil(bf, PV(z + 0.03), 0.034, 0.02, lados=12)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.5)), 0.021, 1.0, lados=16)
coluna_visor = ob('silo_visor_granel', bm, 'minerio', liso=True)
coluna_visor.location = PV(Z_V0 + 0.02)
# régua com marcas e ponteiro
caixa(B('regua', 'grafite'), PV((Z_V0 + Z_V1) / 2, 0.075, -0.02), (0.06, 0.012, Z_V1 - Z_V0 - 0.05), QV)
for k in range(17):
    z = Z_V0 + 0.05 + k * (Z_V1 - Z_V0 - 0.1) / 16
    caixa(B('regua_marca', 'estencil'), PV(z, 0.075 - (0.0 if k % 4 else 0.01), -0.012), (0.03 if k % 4 else 0.05, 0.003, 0.006), QV)
bm = bmesh.new()
caixa(bm, Vector((0, 0, 0)), (0.07, 0.02, 0.018))
ponteiro = ob('silo_ponteiro', bm, 'led_a')
ponteiro.rotation_mode = 'QUATERNION'
ponteiro.rotation_quaternion = QV.to_quaternion()

# ================================================================== TETO
NA_T = 96


def pos_teto(i, j):
    a = i * 2 * PI / NA_T
    r = R + 0.06 - (R + 0.06 - 0.12) * j / 10
    rib = 0.0
    return P_cil(a, r, z_teto(r) + rib)


superficie(lambda i, j: ('teto', 'teto', False), NA_T, 11, pos_teto)
for k in range(24):                                           # nervuras radiais (costuras do teto)
    a = k * 2 * PI / 24
    p0, p1 = P_cil(a, R + 0.05, z_teto(R + 0.05) + 0.012), P_cil(a, 0.16, z_teto(0.16) + 0.012)
    viga(B('teto_nervura', 'grafite'), p0, p1, 0.022)
cil(B('coroa', 'grafite'), Vector((0, 0, Z_APICE + 0.015)), 0.17, 0.04, lados=24)
# ferrugem e fuligem no teto
for k in range(6):
    a = random.uniform(-PI, PI)
    r = random.uniform(0.3, 0.8)
    mancha_suave(B('fuligem_s', 'fuligem_s'), (math.cos(a) * r, math.sin(a) * r), 0.1, z_teto(r) + 0.004, 0.45)

# mastro central com radar giratório da IA
tubo(B('mastro', 'grafite'), (0, 0, Z_APICE + 0.03), (0, 0, Z_APICE + 0.33), 0.03, 16)
for k in range(3):
    a = k * 2 * PI / 3
    viga(B('mastro', 'grafite'), (math.cos(a) * 0.14, math.sin(a) * 0.14, Z_APICE + 0.035), (math.cos(a) * 0.03, math.sin(a) * 0.03, Z_APICE + 0.2), 0.018)
cil(bf, Vector((0, 0, Z_APICE + 0.34)), 0.05, 0.03, lados=16)
radar = vazio('silo_radar')
radar.location = (0, 0, Z_APICE + 0.355)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.02)), 0.04, 0.04, lados=16)
for su in (-1, 1):
    caixa(bm, Vector((su * 0.05, 0, 0.07)), (0.012, 0.04, 0.1))
caixa(bm, Vector((0, 0, 0.04)), (0.12, 0.04, 0.012))
ob('silo_radar_garfo', bm, 'grafite', radar)
bm = bmesh.new()
caixa(bm, Vector((0, 0.012, 0.11)), (0.26, 0.03, 0.1))
ob('silo_radar_painel', bm, 'ferro', radar)
bm = bmesh.new()
for k in range(6):
    caixa(bm, Vector((-0.1 + k * 0.04, -0.0045, 0.11)), (0.026, 0.004, 0.07))
ob('silo_radar_luz', bm, 'radar_luz', radar)

# radares de nível (corneta apontada para baixo, no bocal flangeado)
RADARES = [(math.radians(110), 0.6), (math.radians(5), 0.62)]
for a, r in RADARES:
    p = P_cil(a, r, z_teto(r))
    cil(B('bocal', 'grafite'), p + Vector((0, 0, 0.04)), 0.06, 0.1, lados=20)
    cil(bf, p + Vector((0, 0, 0.095)), 0.085, 0.014, lados=20)
    for k in range(8):
        aa = k * PI / 4
        parafuso(B('parafusos', 'aco'), p + Vector((math.cos(aa) * 0.07, math.sin(aa) * 0.07, 0.102)), UP, 0.006)
    cil(B('radar_nivel', 'amarelo', True), p + Vector((0, 0, 0.16)), 0.055, 0.11, lados=20)
    cil(B('radar_nivel', 'amarelo', True), p + Vector((0, 0, 0.23)), 0.04, 0.03, lados=20, r2=0.03)
    caixa(B('radar_nivel_cx', 'grafite'), p + Vector((0, 0, 0.16)) + Vector((math.cos(a), math.sin(a), 0)) * 0.065, (0.04, 0.04, 0.05))
    cil(B('led', 'led_a'), p + Vector((math.cos(a + 1.2), math.sin(a + 1.2), 0)) * 0.055 + Vector((0, 0, 0.19)), 0.008, 0.01, lados=8)

# filtro do respiro (manga) com chapéu; a poeira escapa por baixo do chapéu
A_FIL, R_FIL = math.radians(45), 0.56
P_FIL = P_cil(A_FIL, R_FIL, z_teto(R_FIL))
Z_FT = P_FIL.z + 0.42
cil(B('filtro', 'amarelo', True), P_FIL + Vector((0, 0, 0.21)), 0.14, 0.42, lados=28)
for z in (0.06, 0.2, 0.34):
    cil(B('filtro_cinta', 'ferro'), P_FIL + Vector((0, 0, z)), 0.148, 0.025, lados=28)
for k in range(10):
    a = k * 2 * PI / 10
    caixa(B('filtro_cinta', 'ferro'), P_FIL + Vector((math.cos(a) * 0.145, math.sin(a) * 0.145, 0.21)), (0.015, 0.015, 0.4), Matrix.Rotation(a, 3, 'Z'))
for k in range(4):                                                       # pés do chapéu
    a = k * PI / 2 + PI / 4
    tubo(B('filtro_cinta', 'ferro'), P_FIL + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.42)), P_FIL + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.5)), 0.008, 6)
cil(B('chapeu', 'grafite', True), P_FIL + Vector((0, 0, 0.53)), 0.2, 0.08, lados=28, r2=0.05)
cil(B('chapeu', 'grafite', True), P_FIL + Vector((0, 0, 0.488)), 0.2, 0.008, lados=28)
cil(B('buraco', 'buraco'), P_FIL + Vector((0, 0, 0.421)), 0.09, 0.004, lados=20)
cil(bf, P_FIL + Vector((0, 0, 0.02)), 0.17, 0.03, lados=28)
# pulsador de ar do filtro (tanque pequeno + mangueira)
pt = P_FIL + Vector((0.18, -0.12, 0.0))
pt.z = z_teto(pt.xy.length) + 0.09
cil(B('pulsador', 'cobre', True), pt, 0.045, 0.16, Vector((1, -0.3, 0)), lados=16)
mangueira(B('mangueira', 'borracha'), bezier(pt + Vector((0, 0, 0.04)), pt + Vector((0, 0, 0.15)), P_FIL + Vector((0.08, -0.12, 0.3)), P_FIL + Vector((0.1, -0.1, 0.32)), 8), 0.009)
mancha_suave(B('pomin_s', 'pomin_s'), (P_FIL.x + 0.05, P_FIL.y - 0.05), 0.3, z_teto(R_FIL) + 0.012, 0.8)
# pó assentado no chapéu
POEIRAS = []
for k in range(3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    POEIRAS.append(ob('silo_poeira_%d' % k, bm, 'poeira'))

# plataforma da escotilha de drone (sobre pés no teto), tampa com dois pistões e luzes
A_DR, R_DR = math.radians(-50), 0.56
PD = P_cil(A_DR, R_DR, 0)
Z_PD = 3.5
bpd = B('plataforma', 'grafite')
caixa_de(bpd, (PD.x - 0.27, PD.y - 0.27, Z_PD - 0.035), (PD.x + 0.27, PD.y + 0.27, Z_PD))
for sx in (-1, 1):
    for sy in (-1, 1):
        p = Vector((PD.x + sx * 0.22, PD.y + sy * 0.22, 0))
        zr = z_teto(p.xy.length)
        caixa_de(bpd, (p.x - 0.02, p.y - 0.02, zr - 0.01), (p.x + 0.02, p.y + 0.02, Z_PD - 0.035))
        caixa_de(bf, (p.x - 0.04, p.y - 0.04, zr - 0.006), (p.x + 0.04, p.y + 0.04, zr + 0.006))
        cil(B('led_drone', 'drone_luz'), Vector((PD.x + sx * 0.245, PD.y + sy * 0.245, Z_PD + 0.008)), 0.014, 0.016, lados=12)
for a, b in (((-0.27, -0.27), (0.27, -0.22)), ((-0.27, 0.22), (0.27, 0.27)), ((-0.27, -0.22), (-0.22, 0.22)), ((0.22, -0.22), (0.27, 0.22))):
    caixa_de(B('listras_pad', 'listras'), (PD.x + a[0], PD.y + a[1], Z_PD), (PD.x + b[0], PD.y + b[1], Z_PD + 0.003))
toro(B('pad_anel', 'estencil'), Vector((PD.x, PD.y, Z_PD + 0.002)), 0.19, 0.006, 48, 4, Matrix.Diagonal((1, 1, 0.2)))
# poço escuro e moldura sob a tampa
caixa_de(B('buraco', 'buraco'), (PD.x - 0.13, PD.y - 0.13, Z_PD + 0.0005), (PD.x + 0.13, PD.y + 0.13, Z_PD + 0.002))
for a, b in (((-0.15, -0.15), (0.15, -0.13)), ((-0.15, 0.13), (0.15, 0.15)), ((-0.15, -0.13), (-0.13, 0.13)), ((0.13, -0.13), (0.15, 0.13))):
    caixa_de(B('moldura', 'ferro'), (PD.x + a[0], PD.y + a[1], Z_PD), (PD.x + b[0], PD.y + b[1], Z_PD + 0.012))
# berço de encaixe do drone (quatro pinos guia) dentro do poço
for sx in (-1, 1):
    for sy in (-1, 1):
        cil(B('pinos', 'cromo'), Vector((PD.x + sx * 0.09, PD.y + sy * 0.09, Z_PD - 0.01)), 0.008, 0.03, lados=8)
# tampa (dobradiça no lado +x)
X_DOB = PD.x + 0.14
dobra = vazio('silo_tampa_dobra')
dobra.location = (X_DOB, PD.y, Z_PD + 0.016)
bm = bmesh.new()
caixa_de(bm, (-0.285, -0.14, -0.004), (0.005, 0.14, 0.012))
for k in range(3):
    caixa_de(bm, (-0.26 + k * 0.1, -0.12, 0.012), (-0.24 + k * 0.1, 0.12, 0.022))
for sy in (-1, 1):
    caixa_de(bm, (-0.112, sy * 0.14 - 0.0, 0.0), (-0.088, sy * 0.172, 0.024)) if sy > 0 else caixa_de(bm, (-0.112, -0.172, 0.0), (-0.088, -0.14, 0.024))
ob('silo_tampa', bm, 'amarelo', dobra)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.012, 0.26, Vector((0, 1, 0)), lados=10)
ob('silo_dobradica', bm, 'ferro', dobra)
cil(bf, Vector((X_DOB, PD.y, Z_PD + 0.016)), 0.014, 0.3, Vector((0, 1, 0)), lados=10)
# pistões da tampa: camisa na orelha da plataforma, haste na orelha da tampa
PIST_T = []
for sy in (-1, 1):
    piv = Vector((X_DOB - 0.2, PD.y + sy * 0.16, Z_PD + 0.02))
    caixa_de(bf, (piv.x - 0.02, piv.y - 0.012, Z_PD), (piv.x + 0.02, piv.y + 0.012, Z_PD + 0.035))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.05)), 0.014, 0.1, lados=12)
    cam = ob('silo_tampa_camisa_%d' % sy, bm, 'amarelo', liso=True)
    cam.location = piv
    cam.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -0.075)), 0.007, 0.15, lados=10)
    ha = ob('silo_tampa_haste_%d' % sy, bm, 'cromo', liso=True)
    ha.rotation_mode = 'QUATERNION'
    PIST_T.append((piv, sy, cam, ha))

# bocal de entrada do teto (recebe o duto do elevador) e granel derramado em volta
A_IN, R_IN = PI, 0.44
P_IN = P_cil(A_IN, R_IN, z_teto(R_IN))
cil(B('bocal', 'grafite'), P_IN + Vector((0, 0, 0.05)), 0.1, 0.13, lados=20)
cil(bf, P_IN + Vector((0, 0, 0.115)), 0.12, 0.014, lados=20)
monte(B('monte_teto', 'minerio', True), (P_IN.x + 0.12, P_IN.y - 0.05), 0.16, 0.1, 0.02, z_teto(R_IN - 0.12) - 0.004, fase=2)
pedrisco(B('pedrisco', 'minerio'), (P_IN.x + 0.15, P_IN.y), 0.2, 0.15, z_teto(R_IN - 0.15) + 0.002, 25, 0.004, 0.01)

# ================================================================== ELEVADOR DE CANECAS (oeste)
be = B('elevador', 'amarelo')
X0E, X1E = X_EL - 0.11, X_EL + 0.11
# pé (bota) com mancais, esticadores e porta de limpeza
caixa_de(be, (-1.34, -0.31, ZL), (-1.07, 0.31, Z_EL0))
caixa_de(bf, (-1.36, -0.33, ZL), (-1.055, 0.33, ZL + 0.025))
for sy in (-1, 1):
    y = sy * 0.31
    cil(B('mancal', 'ferro'), Vector((X_EL, y + sy * 0.03, 0.28)), 0.055, 0.06, Vector((0, 1, 0)), lados=16)
    cil(B('eixo', 'aco'), Vector((X_EL, y + sy * 0.065, 0.28)), 0.02, 0.03, Vector((0, 1, 0)), lados=12)
    for sz in (-1, 1):
        tubo(B('esticador', 'aco'), (X_EL - 0.06, y + sy * 0.03, 0.28 + sz * 0.07), (X_EL - 0.06, y + sy * 0.03, 0.28 + sz * 0.16), 0.009, 8)
        cil(bf, Vector((X_EL - 0.06, y + sy * 0.03, 0.28 + sz * 0.16)), 0.016, 0.012, lados=6)
caixa_de(B('porta_limpeza', 'grafite'), (-1.35, -0.18, 0.12), (-1.34, 0.18, 0.4))
for y in (-0.16, 0.16):
    for z in (0.14, 0.27, 0.38):
        parafuso(bf, (-1.35, y, z), Vector((-1, 0, 0)), 0.007)
texto('silo_serie', 'SG-07 %04d' % random.randint(1000, 9999), 0.045, Vector((-1.3415, 0.14, 0.43)), Vector((-1, 0, 0)))
# duas pernas com flanges a cada seção; a perna que sobe tem janela gradeada no lado sul
for (y0, y1), nome in ((Y_SOBE, 'sobe'), (Y_DESCE, 'desce')):
    paredes = [((X0E, y0, Z_EL0), (X0E + 0.008, y1, Z_EL1)), ((X1E - 0.008, y0, Z_EL0), (X1E, y1, Z_EL1)),
               ((X0E, y1 - 0.008, Z_EL0), (X1E, y1, Z_EL1))]
    if nome == 'sobe':
        paredes += [((X0E, y0, Z_EL0), (X1E, y0 + 0.008, Z_JE0)), ((X0E, y0, Z_JE1), (X1E, y0 + 0.008, Z_EL1)),
                    ((X0E, y0, Z_JE0), (X0E + 0.025, y0 + 0.008, Z_JE1)), ((X1E - 0.025, y0, Z_JE0), (X1E, y0 + 0.008, Z_JE1))]
    else:
        paredes += [((X0E, y0, Z_EL0), (X1E, y0 + 0.008, Z_EL1))]
    for a, b in paredes:
        caixa_de(be, a, b)
    z = Z_EL0 + 0.6
    while z < Z_EL1 - 0.2:
        caixa_de(B('flanges', 'grafite'), (X0E - 0.018, y0 - 0.018, z - 0.012), (X1E + 0.018, y1 + 0.018, z + 0.012))
        for xx in (X0E - 0.01, X1E + 0.01):
            for yy in (y0 + 0.04, y1 - 0.04):
                parafuso(bf, (xx, yy, z + 0.012), UP, 0.006)
        z += 0.6
# moldura e grade da janela das canecas
y0 = Y_SOBE[0]
for a, b in (((X0E - 0.01, Z_JE0 - 0.03), (X1E + 0.01, Z_JE0)), ((X0E - 0.01, Z_JE1), (X1E + 0.01, Z_JE1 + 0.03)),
             ((X0E - 0.01, Z_JE0), (X0E + 0.025, Z_JE1)), ((X1E - 0.025, Z_JE0), (X1E + 0.01, Z_JE1))):
    caixa_de(B('jan_el', 'grafite'), (a[0], y0 - 0.014, a[1]), (b[0], y0 + 0.002, b[1]))
for k in range(1, 4):
    x = X0E + 0.025 + k * (X1E - X0E - 0.05) / 4
    tubo(B('jan_el_grade', 'ferro'), (x, y0 - 0.008, Z_JE0), (x, y0 - 0.008, Z_JE1), 0.005, 6)
for z in (Z_JE0 + 0.37, Z_JE0 + 0.74):
    tubo(B('jan_el_grade', 'ferro'), (X0E + 0.02, y0 - 0.012, z), (X1E - 0.02, y0 - 0.012, z), 0.005, 6)
# correia (dentro) e fundo escuro
caixa_de(B('correia', 'borracha'), (X1E - 0.05, Y_SOBE[0] + 0.03, Z_EL0 + 0.1), (X1E - 0.04, Y_SOBE[1] - 0.03, Z_EL1 - 0.05))
caixa_de(B('buraco', 'buraco'), (X1E - 0.03, Y_SOBE[0] + 0.01, Z_JE0 - 0.05), (X1E - 0.0081, Y_SOBE[1] - 0.009, Z_JE1 + 0.05))
# canecas (animadas): perfil trapezoidal com granel por cima
P_CAN = 0.1625
N_CAN = 8
Z_CAN0 = Z_JE0 - 0.12
CANECAS = []
for k in range(N_CAN):
    bm = bmesh.new()
    xb = X1E - 0.04
    yc0, yc1 = Y_SOBE[0] + 0.035, Y_SOBE[1] - 0.035
    caixa_de(bm, (xb - 0.115, yc0, 0.0), (xb, yc1, 0.008))
    caixa_de(bm, (xb - 0.008, yc0, 0.0), (xb, yc1, 0.1))
    for yy in (yc0, yc1 - 0.006):
        caixa_de(bm, (xb - 0.12, yy, 0.0), (xb, yy + 0.006, 0.065))
    caixa(bm, Vector((xb - 0.125, (yc0 + yc1) / 2, 0.035)), (0.008, yc1 - yc0, 0.075), Matrix.Rotation(-0.3, 3, 'Y'))
    o = ob('silo_caneca_%d' % k, bm, 'grafite')
    bm = bmesh.new()
    for j in range(9):
        pedra(bm, (xb - random.uniform(0.02, 0.1), random.uniform(yc0 + 0.015, yc1 - 0.015), random.uniform(0.045, 0.07)), random.uniform(0.012, 0.02), 0.7)
    ob('silo_caneca_granel_%d' % k, bm, 'minerio', o)
    CANECAS.append(o)
# cabeça: caixa, capô, porta de inspeção, redutor, acoplamento e motor; farol no topo
caixa_de(be, (-1.36, -0.3, Z_EL1), (-1.04, 0.3, Z_EL1 + 0.18))
meia_cil(B('capo', 'amarelo', True), (X_EL, 0, Z_EL1 + 0.18), 0.16, -0.3, 0.3, 16)
caixa_de(B('flanges', 'grafite'), (-1.375, -0.315, Z_EL1 - 0.015), (-1.025, 0.315, Z_EL1 + 0.01))
caixa_de(B('porta_cabeca', 'grafite'), (-1.37, -0.2, Z_EL1 + 0.03), (-1.36, 0.0, Z_EL1 + 0.16))
for y in (-0.19, -0.01):
    for z in (Z_EL1 + 0.04, Z_EL1 + 0.15):
        parafuso(bf, (-1.37, y, z), Vector((-1, 0, 0)), 0.006)
cil(B('farol_base', 'ferro'), Vector((X_EL, -0.1, Z_EL1 + 0.35)), 0.035, 0.02, lados=12)
cil(B('farol', 'farol', True), Vector((X_EL, -0.1, Z_EL1 + 0.385)), 0.026, 0.05, lados=16)
caixa_de(B('redutor_el', 'grafite'), (-1.25, 0.3, Z_EL1 + 0.04), (-1.09, 0.48, Z_EL1 + 0.3))
cil(B('motor_el', 'grafite', True), Vector((-1.38, 0.39, Z_EL1 + 0.12)), 0.075, 0.18, Vector((1, 0, 0)), lados=24)
for k in range(12):
    a = k * 2 * PI / 12
    caixa(B('aletas', 'ferro'), Vector((-1.385, 0.39 + math.cos(a) * 0.08, Z_EL1 + 0.12 + math.sin(a) * 0.08)), (0.16, 0.012, 0.012), Matrix.Rotation(a, 3, 'X'))
cil(B('aletas', 'ferro'), Vector((-1.48, 0.39, Z_EL1 + 0.12)), 0.08, 0.022, Vector((1, 0, 0)), lados=24)
tubo(B('eixo', 'aco'), (-1.295, 0.39, Z_EL1 + 0.12), (-1.245, 0.39, Z_EL1 + 0.12), 0.016, 12)
caixa_de(B('base_motor', 'ferro'), (-1.47, 0.31, Z_EL1 + 0.03), (-1.25, 0.47, Z_EL1 + 0.045))
acop = vazio('silo_acoplamento')
acop.location = (-1.27, 0.39, Z_EL1 + 0.12)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.045, 0.03, Vector((1, 0, 0)), lados=16)
for k in range(6):
    a = k * PI / 3
    cil(bm, Vector((0.02, math.cos(a) * 0.032, math.sin(a) * 0.032)), 0.006, 0.02, Vector((1, 0, 0)), lados=6)
ob('silo_acoplamento_disco', bm, 'aco', acop)
faixa_suave(B('oleo_s', 'oleo_s'), Vector((-1.17, 0.4815, Z_EL1 + 0.27)), Vector((-1.17, 0.4815, Z_EL1 + 0.05)), Vector((0.02, 0, 0)))
faixa_suave(B('oleo_s', 'oleo_s'), Vector((-1.115, 0.2415, Z_EL1 - 0.02)), Vector((-1.115, 0.2415, Z_EL1 - 0.9)), Vector((0.012, 0, 0)), 0.7)
# duto de descarga até o bocal do teto
pd0 = Vector((-1.04, 0, Z_EL1 + 0.14))
pd1 = P_IN + Vector((0, 0, 0.18))
viga(B('duto', 'amarelo'), pd0 + Vector((-0.02, 0, 0)), pd1, 0.13)
u = (pd1 - pd0).normalized()
for t in (0.04, 0.5, 0.94):
    p = pd0.lerp(pd1, t)
    viga(B('flanges', 'grafite'), p - u * 0.012, p + u * 0.012, 0.16)
tubo(B('duto', 'amarelo'), pd1, P_IN + Vector((0, 0, 0.12)), 0.075, 16)
# amarrações da perna aos anéis do silo
for z in ANEIS + [Z_C1 + 0.02]:
    for y in (-0.12, 0.12):
        x_r = -math.sqrt((RC + 0.06) ** 2 - y * y)
        caixa_de(B('amarras', 'grafite'), (X1E, y - 0.015, z - 0.035), (x_r, y + 0.015, z - 0.005))
        parafuso(bf, (X1E + 0.02, y - 0.016, z - 0.02), Vector((0, -1, 0)), 0.006)
# moega de entrada (o braço despeja aqui), com grade e granel
bmh = bmesh.new()
top = [(-1.44, -0.70), (-1.04, -0.70), (-1.04, -0.31), (-1.44, -0.31)]
bot = [(-1.31, -0.46), (-1.13, -0.46), (-1.13, -0.31), (-1.31, -0.31)]
vt = [bmh.verts.new((x, y, 0.78)) for x, y in top]
vb = [bmh.verts.new((x, y, 0.36)) for x, y in bot]
for k in range(4):
    bmh.faces.new((vb[k], vb[(k + 1) % 4], vt[(k + 1) % 4], vt[k]))
mo = ob('silo_moega', bmh, 'amarelo')
mo.modifiers.new('esp', 'SOLIDIFY').thickness = 0.014
for a, b in (((-1.455, -0.715), (-1.025, -0.70)), ((-1.455, -0.325), (-1.025, -0.31)), ((-1.455, -0.70), (-1.44, -0.325)), ((-1.04, -0.70), (-1.025, -0.325))):
    caixa_de(B('moega_aro', 'ferro'), (a[0], a[1], 0.77), (b[0], b[1], 0.80))
for k in range(1, 6):
    y = -0.70 + k * 0.39 / 6
    caixa_de(B('moega_grade', 'grafite'), (-1.44, y - 0.006, 0.79), (-1.04, y + 0.006, 0.805))
monte(B('monte_moega', 'minerio', True), (-1.24, -0.5), 0.15, 0.12, 0.05, 0.62, fase=0.5)
for sx in (-1, 1):                                                       # pés da moega
    viga(B('cavalete', 'grafite'), (-1.24 + sx * 0.2, -0.68, ZL), (-1.24 + sx * 0.19, -0.66, 0.77), 0.035)
caixa_de(B('listras', 'listras'), (-1.44, -0.705, 0.68), (-1.04, -0.7, 0.76))
# granel caído em volta do pé e da moega
monte(B('monte_chao', 'minerio', True), (-1.26, -0.82), 0.2, 0.12, 0.05, ZL, fase=2.2, rot=0.4)
pedrisco(B('pedrisco', 'minerio'), (-1.2, -0.8), 0.3, 0.2, ZL + 0.004, 30, 0.005, 0.012)
monte(B('monte_chao', 'minerio', True), (-0.95, 0.1), 0.1, 0.08, 0.025, ZL, fase=4)
# eletrocalha com cabos: do mastro pelo teto até a perna e descendo até a caixa de junção no pé
A_CB = math.radians(150)
p_borda = P_cil(A_CB, R + 0.06, z_teto(R + 0.06) + 0.03)
x_ec, y_ec = -1.2, 0.29
caixa_de(B('eletrocalha', 'ferro'), (x_ec - 0.05, 0.262, 0.68), (x_ec + 0.05, 0.32, Z_EL1 - 0.05))
for k, (mat, dd) in enumerate((('fio_r', -0.012), ('fio_a', 0.0), ('fio_z', 0.012))):
    pts = [Vector((dd, dd, Z_APICE + 0.06)), P_cil(A_CB, 0.3, z_teto(0.3) + 0.02) + Vector((0, dd, 0)), P_cil(A_CB, 0.7, z_teto(0.7) + 0.02) + Vector((0, dd, 0))]
    mangueira(B('cabo_' + mat, mat), pts, 0.007)
    mangueira(B('cabo_' + mat, mat), bezier(pts[-1], p_borda + Vector((0, dd, 0.05)), Vector((x_ec + dd, 0.32, Z_EL1 - 0.2)), Vector((x_ec + dd, 0.31, Z_EL1 - 0.06)), 10), 0.007)
for r in (0.2, 0.5, 0.8):                                                # presilhas no teto
    caixa(B('presilha', 'ferro'), P_cil(A_CB, r, z_teto(r) + 0.02), (0.05, 0.05, 0.012), Matrix.Rotation(A_CB, 3, 'Z'))
caixa_de(B('cx_juncao', 'grafite'), (-1.29, 0.33, 0.5), (-1.11, 0.42, 0.68))
caixa_de(B('cx_juncao_tampa', 'ferro'), (-1.28, 0.42, 0.51), (-1.12, 0.425, 0.67))
caixa_de(bf, (-1.3, 0.31, 0.56), (-1.1, 0.33, 0.62))
cil(B('led', 'led_a'), Vector((-1.25, 0.428, 0.64)), 0.007, 0.008, Vector((0, 1, 0)), lados=8)
mangueira(B('cabo', 'borracha'), bezier(Vector((-1.2, 0.38, 0.5)), Vector((-1.2, 0.38, 0.3)), Vector((-1.1, 0.5, ZL + 0.05)), Vector((-0.9, 0.55, ZL + 0.015)), 10), 0.012)
mangueira(B('cabo', 'borracha'), bezier(Vector((-0.9, 0.55, ZL + 0.015)), Vector((-0.5, 0.6, ZL + 0.015)), Vector((-0.2, 0.62, ZL + 0.015)), Vector((0.0, 0.62, ZL + 0.015)), 10), 0.012)
# fiação rasgada no conduíte (fios soltos) junto da caixa de junção
for k, (mat, dx) in enumerate((('fio_r', -0.01), ('fio_a', 0.0), ('fio_z', 0.01))):
    a = Vector((-1.24 + dx, 0.4, 0.68))
    mangueira(B('fio_' + mat, mat), bezier(a, a + Vector((0, 0.03, 0.05)), Vector((x_ec + dx, 0.35, 0.66)), Vector((x_ec + dx, 0.31, 0.69)), 8), 0.0025)

fechar()

# ------------------------------------------------------------------ granel caindo da bica
PEDRAS_Q = []
for k in range(18):
    bm = bmesh.new()
    pedra(bm, (0, 0, 0), random.uniform(0.01, 0.018), 0.8)
    o = ob('silo_queda_%02d' % k, bm, 'minerio')
    o.rotation_mode = 'XYZ'
    PEDRAS_Q.append((o, random.uniform(-0.035, 0.035), random.uniform(-0.035, 0.035), random.uniform(0, 1), random.uniform(0, 6)))
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
poeira_bica = ob('silo_poeira_bica', bm, 'poeira_b')
poeira_bica.location = (0.0, Y_CA - 0.02, 0.33)
Z_TOPO_M = alt_m(0, 0)


# ================================================================== ANIMAÇÃO (laço de 4 s)
def chave(o, q, *props):
    for p in props:
        o.keyframe_insert(p, frame=q)


def nivel(fr):
    return 0.62 + 0.06 * math.sin(2 * PI * fr)


L_CAN = P_CAN * N_CAN
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # comporta: abre, fica aberta, fecha no fim (o granel só cai com ela aberta)
    ab = jan(fr, 0.03, 0.12) - jan(fr, 0.86, 0.95)
    gaveta.location = (0.16 * ab, 0, 0)
    chave(gaveta, q, 'location')
    fluxo = jan(fr, 0.1, 0.16) - jan(fr, 0.9, 0.96)
    # rosca gira
    helice.rotation_euler = (0, 0, -2 * PI * 8 * fr)
    chave(helice, q, 'rotation_euler')
    # granel caindo da bica na caçamba
    for o, dx, dy, ph, sp in PEDRAS_Q:
        u = (fr * 4 + ph) % 1.0
        z = Z_BICA - 0.01 - (Z_BICA - 0.01 - (Z_TOPO_M + 0.01)) * u * u
        o.location = (dx * (1 + u), Y_CA + dy * (1 + u * 0.6), z)
        o.rotation_euler = (sp + 9 * u, sp * 2 + 7 * u, 0)
        vis = fluxo > 0.5
        o.hide_render = not vis
        o.hide_viewport = not vis
        chave(o, q, 'location', 'rotation_euler', 'hide_render', 'hide_viewport')
    s = 0.09 + 0.02 * math.sin(2 * PI * 4 * fr)
    poeira_bica.scale = (s * 1.4, s * 1.2, s * 0.9)
    poeira_bica.hide_render = fluxo < 0.5
    chave(poeira_bica, q, 'scale', 'hide_render')
    # canecas sobem (6 passos por laço)
    for k, o in enumerate(CANECAS):
        o.location = (0, 0, Z_CAN0 + (k * P_CAN + 6 * P_CAN * fr) % L_CAN)
        chave(o, q, 'location')
    acop.rotation_euler = (2 * PI * 10 * fr, 0, 0)
    chave(acop, q, 'rotation_euler')
    # nível: visor, ponteiro, grade da IA e plano de compactação
    nv = nivel(fr)
    coluna_visor.scale = (1, 1, (Z_V1 - Z_V0 - 0.04) * nv)
    chave(coluna_visor, q, 'scale')
    ponteiro.location = PV(Z_V0 + 0.02 + (Z_V1 - Z_V0 - 0.04) * nv, 0.075, -0.004)
    chave(ponteiro, q, 'location')
    zn = Z_J0 + (Z_J1 - Z_J0) * nv
    for z, o in FILEIRAS:
        o.hide_render = z > zn
        o.hide_viewport = o.hide_render
        chave(o, q, 'hide_render', 'hide_viewport')
    z_pl = max([z for z, _ in FILEIRAS if z <= zn] + [Z_J0]) + PASSO_G / 2 + 0.002
    plano_nivel.location = (0, 0, z_pl)
    chave(plano_nivel, q, 'location')
    campo_fundo.location = (0, 0, Z_J0)
    campo_fundo.scale = (1, 1, z_pl - Z_J0)
    chave(campo_fundo, q, 'location', 'scale')
    E_CAMPO.default_value = 2.0 + 1.5 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr))
    E_CAMPO.keyframe_insert('default_value', frame=q)
    E_LENTE.default_value = 4.0 + 4.0 * (0.5 + 0.5 * math.sin(2 * PI * 4 * fr))
    E_LENTE.keyframe_insert('default_value', frame=q)
    # radar gira, farol e luzes piscam
    radar.rotation_euler = (0, 0, 2 * PI * 2 * fr)
    chave(radar, q, 'rotation_euler')
    E_RADAR.default_value = 0.8 + 1.2 * (0.5 + 0.5 * math.sin(2 * PI * 8 * fr))
    E_RADAR.keyframe_insert('default_value', frame=q)
    E_FAROL.default_value = 25.0 if (fr * 4) % 1.0 < 0.15 else 0.4
    E_FAROL.keyframe_insert('default_value', frame=q)
    E_DRONE.default_value = 10.0 if (fr * 2 + 0.25) % 1.0 < 0.5 else 1.0
    E_DRONE.keyframe_insert('default_value', frame=q)
    # tampa do drone abre e fecha; pistões acompanham
    ang = math.radians(105) * (jan(fr, 0.25, 0.4) - jan(fr, 0.7, 0.85))
    dobra.rotation_euler = (0, ang, 0)
    chave(dobra, q, 'rotation_euler')
    for piv, sy, cam, ha in PIST_T:
        l = Vector((-0.1 * math.cos(ang) + 0.012 * math.sin(ang), 0, 0.1 * math.sin(ang) + 0.012 * math.cos(ang)))           # orelha na tampa (local da dobradiça)
        at = Vector(dobra.location) + Vector((l.x, sy * 0.16, l.z))
        d = at - piv
        qd = d.normalized().to_track_quat('Z', 'Y')
        cam.rotation_quaternion = qd
        ha.location = at
        ha.rotation_quaternion = qd
        chave(cam, q, 'rotation_quaternion')
        chave(ha, q, 'location', 'rotation_quaternion')
    # poeira do filtro sai por baixo do chapéu e sobe
    for k, o in enumerate(POEIRAS):
        u = (fr * 2 + k / 3) % 1.0
        ang_p = k * 2.1 + 0.6
        o.location = P_FIL + Vector((math.cos(ang_p) * (0.2 + 0.25 * u), math.sin(ang_p) * (0.2 + 0.25 * u) - 0.1 * u, 0.47 + 0.4 * u))
        s = 0.07 + 0.16 * u
        o.scale = (s * 1.3, s, s * 0.8)
        chave(o, q, 'location', 'scale')

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
caixa(bm, (0, 0, -0.5), (18, 18, 1.0))
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


def polar(ang, dist, alt, zalvo):
    a = math.radians(ang)
    return Vector((math.cos(a) * dist, math.sin(a) * dist, alt)), Vector((0, 0, zalvo))


FOTOS = {
    'silo_0': (40, polar(232, 7.6, 3.4, 1.95), 32, (1100, 1300)),
    'silo_perto': (40, (Vector((-1.25, -3.0, 1.15)), Vector((-0.1, -0.45, 0.52))), 26, (1300, 1000)),
    'silo_topo': (40, (Vector((-1.9, -2.6, 5.6)), Vector((-0.15, -0.05, 3.42))), 30, (1300, 1000)),
}
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
args = sys.argv[sys.argv.index('--') + 2:] if '--' in sys.argv else []
if modo == 'foto':
    sc.cycles.samples = 128
    for nome in (args or list(FOTOS)):
        qd, (pos, alvo), lente, res = FOTOS[nome]
        sc.frame_set(qd)
        sc.render.resolution_x, sc.render.resolution_y = res
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(a) for a in args[:8]]
    sc.cycles.samples = 24
    sc.frame_set(int(v[7]))
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'silo_teste.png')
    bpy.ops.render.render(write_still=True)
print('SILO ok')
