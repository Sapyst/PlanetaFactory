"""Estudo isolado (fora do jogo): refinador, 3×3 tiles. Fluido (seiva) entra a oeste no tile do meio (O1), fluido
refinado sai a leste no tile do meio (L1), produto sólido (célula/bateria) sai ao norte no tile oeste (N0).
Refinaria química compacta de fábrica autônoma:
- bomba centrífuga com motor na entrada oeste, recalque sobe até o coletor de carga dos reatores;
- dois reatores verticais com camisa de resfriamento (água da chuva), flange de corpo aparafusada, agitador no topo,
  válvulas atuadas, manômetros, válvula de alívio (PSV) ligada ao coletor de respiro e purgadores soltando vapor;
- funil coletor de chuva + filtro alimentando as camisas e o casco do trocador (o vapor sai pelos silenciadores);
- torre de fracionamento com seções flangeadas, visores de prato, visor de nível, bocas de visita, trilho-cremalheira
  com robô de inspeção (sem escada humana) e anel de campo da IA girando no alto;
- trocador de calor casco-e-tubo resfriando o fundo da torre antes da saída leste;
- flare (respiro com chama piloto) com vaso separador, estais, fuligem na ponta; recebe o topo da torre e as PSVs;
- reator norte descarrega sólido por válvula rotativa e rosca até o encapsulador, que solta células na bica norte;
- armário da IA com antena, eletrocalha e feixes de cabos até sensores e motores;
- respingos de seiva e óleo, crosta química nas flanges, fuligem.
Uso: blender -b --python estudo_refinador.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(23)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
Z0 = 0.08                    # topo da laje
Z_P = 0.30                   # altura das bocas de fluido (oeste e leste)


# ------------------------------------------------------------------ utilidades
def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=64, nr=16):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def curva(bm, p, r, lados=16):
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def base_perp(u):
    u = Vector(u).normalized()
    e1 = u.orthogonal().normalized()
    return e1, u.cross(e1).normalized()


def flange(bf, bp, c, u, r, parafusos=True):
    """Par de flanges aparafusadas no ponto c, eixo u, para cano de raio r."""
    c, u = Vector(c), Vector(u).normalized()
    for s in (-1, 1):
        tubo(bf, c + u * s * 0.003, c + u * s * 0.017, r * 1.65 + 0.006, 20)
    if not parafusos:
        return
    e1, e2 = base_perp(u)
    n = 6 if r < 0.03 else (8 if r < 0.05 else 12)
    for k in range(n):
        a = k * 2 * PI / n + 0.2
        p = c + (e1 * math.cos(a) + e2 * math.sin(a)) * (r * 1.35 + 0.004)
        tubo(bp, p - u * 0.03, p + u * 0.03, 0.0045, 6)
        for s in (-1, 1):                                                 # porcas
            tubo(bp, p + u * s * 0.022, p + u * s * 0.03, 0.008, 6)


def cano(bm, bf, bp, pts, r, folga=0.08, flanges=True):
    """Cano rígido: trechos retos, cotovelos redondos e flanges aparafusadas perto das curvas."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 20)
        u = (b - a).normalized()
        if flanges and (b - a).length > 2.5 * folga:
            flange(bf, bp, a + u * folga, u, r)
            flange(bf, bp, b - u * folga, u, r)
    for c in pts[1:-1]:
        curva(bm, c, r, 20)


def bocal(bm, bf, bp, c, u, r, comp):
    """Bocal soldado no vaso: toco de cano saindo de c na direção u, com flange na ponta."""
    c, u = Vector(c), Vector(u).normalized()
    tubo(bm, c - u * 0.02, c + u * comp, r, 20)
    flange(bf, bp, c + u * (comp - 0.01), u, r)
    return c + u * comp


GAUGES = []


def manometro(bc, bm_face, pos, normal, r=0.034, haste=None):
    """Manômetro: haste, caixa cromada, mostrador branco e ponteiro (objeto próprio, treme na animação)."""
    pos, n = Vector(pos), Vector(normal).normalized()
    if haste is not None:
        tubo(bc, Vector(haste), pos - n * 0.0, 0.007, 8)
    tubo(bc, pos - n * 0.012, pos + n * 0.012, r, 24)
    tubo(bc, pos + n * 0.012, pos + n * 0.016, r * 1.06, 24)               # aro
    tubo(bm_face, pos + n * 0.011, pos + n * 0.0135, r * 0.9, 24)
    e = bpy.data.objects.new('ponteiro_piv', None)
    sc.collection.objects.link(e)
    e.location = pos + n * 0.0145
    e.rotation_mode = 'QUATERNION'
    e.rotation_quaternion = n.to_track_quat('Z', 'Y')
    bm = bmesh.new()
    caixa(bm, (0, r * 0.35, 0), (0.004, r * 0.75, 0.002))
    obj('ponteiro', bm, 'preto', e)
    GAUGES.append((e, n, random.uniform(0, 2 * PI), random.uniform(0.25, 0.7)))


def valvula(bc, ba, bf, bp, c, u, r, cima=Vector((0, 0, 1))):
    """Válvula de controle atuada (sem volante: diafragma + posicionador da IA), flangeada dos dois lados."""
    c, u, cima = Vector(c), Vector(u).normalized(), Vector(cima).normalized()
    curva(bc, c, r * 1.7, 20)
    flange(bf, bp, c - u * r * 2.2, u, r)
    flange(bf, bp, c + u * r * 2.2, u, r)
    tubo(bc, c, c + cima * (r * 1.7 + 0.08), r * 0.7, 14)                 # castelo
    tubo(bc, c + cima * (r * 1.7 + 0.03), c + cima * (r * 1.7 + 0.045), r * 1.2, 14)
    p = c + cima * (r * 1.7 + 0.1)
    tubo(ba, p - cima * 0.02, p + cima * 0.02, 0.07, 24)                  # diafragma
    cil(ba, p + cima * 0.035, 0.07, 0.03, cima, lados=24, r2=0.035)
    e1, _ = base_perp(cima)
    caixa(bc, p - cima * 0.06 + e1 * 0.05, (0.04, 0.03, 0.05))            # posicionador


# ------------------------------------------------------------------ materiais
def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat():
    m = bpy.data.materials.new('Vidro')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.8, 0.82, 0.78, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.08
    b.inputs['Alpha'].default_value = 0.4
    return m


def malha_mat():
    """Tela de proteção do acoplamento: chapa transparente onde não há fio."""
    m = bpy.data.materials.new('Tela')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.55, 0.36, 0.04, 1)
    b.inputs['Roughness'].default_value = 0.5
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hz = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(sep.outputs['X'], hz.inputs[0])
    nt.links.new(sep.outputs['Y'], hz.inputs[1])
    fios = []
    for entrada in (hz.outputs['Value'], sep.outputs['Z']):
        d = no(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = 0.02
        nt.links.new(entrada, d.inputs[0])
        fr = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs['Value'], fr.inputs[0])
        lt = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
        lt.inputs[1].default_value = 0.18
        nt.links.new(fr.outputs['Value'], lt.inputs[0])
        fios.append(lt)
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fios[0].outputs['Value'], mx.inputs[0])
    nt.links.new(fios[1].outputs['Value'], mx.inputs[1])
    nt.links.new(mx.outputs['Value'], b.inputs['Alpha'])
    return m


def fogo_mat():
    """Chama em volume: absorve (não fica pálida sob o sol) e emite forte."""
    m = base3d.volume_mat('Fogo', (1.0, 0.4, 0.05), 4.0, -10.0, 10.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = 38.0
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)
    vol.inputs['Emission Color'].default_value = (1.0, 0.3, 0.03, 1)
    vol.inputs['Density'].default_value = 6.0
    return m


def fumaca_grad_mat(nome, dens, z0, z1):
    """Fumaça que sai preta e se dilui em cinza conforme sobe (z0 → z1 no mundo)."""
    m = base3d.volume_mat(nome, (0.02, 0.02, 0.02), dens, z0, z1)
    nt = m.node_tree
    no = mats.no
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


def seiva_mat():
    """Seiva: líquido âmbar-esverdeado, brilhante, com leve brilho próprio (no jogo ela pulsa)."""
    m = mats.material('Seiva', (0.16, 0.15, 0.015), 0, 0.06, pintura=False, sujeira=0.15, desgaste=0.0)
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Emission Color'].default_value = (0.6, 0.6, 0.05, 1)
    b.inputs['Emission Strength'].default_value = 0.06
    b.inputs['Coat Weight'].default_value = 1.0
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'cinza': mats.material('Cinza', (0.30, 0.31, 0.31), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'verde': mats.material('Cano de água', (0.07, 0.24, 0.12), 0, 0.45, desgaste=0.9, sujeira=0.9, ferrugem=0.5),
    'oxido': mats.material('Cano de respiro', (0.36, 0.09, 0.05), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.7),
    'processo': mats.material('Cano de processo', (0.16, 0.15, 0.14), 0.6, 0.5, pintura=False, ferrugem=0.8, sujeira=1.0),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'inox': mats.material('Inox', (0.62, 0.62, 0.62), 1.0, 0.28, pintura=False, ferrugem=0.25, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'crosta': mats.material('Crosta química', (0.62, 0.58, 0.42), 0, 0.95, pintura=False, sujeira=0.5, desgaste=0.0),
    'fuligem': mats.material('Fuligem', (0.015, 0.014, 0.013), 0, 0.95, pintura=False, sujeira=0.0, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.78, 0.72), 0, 0.3, pintura=False, sujeira=0.5, desgaste=0.0),
    'preto': mats.material('Preto', (0.01, 0.01, 0.01), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'bateria': mats.material('Casca da célula', (0.05, 0.05, 0.06), 0.6, 0.3, pintura=False, sujeira=0.2, desgaste=0.0),
    'seiva': seiva_mat(),
    'vidro': vidro_mat(),
    'malha': malha_mat(),
    'listras': base3d.listras_mat(),
    'liquido': luz_mat('Líquido no visor', (1.0, 0.55, 0.08), 2.5),
    'violeta': luz_mat('Campo violeta', (0.55, 0.12, 1.0), 9.0),
    'ambar': luz_mat('Luz âmbar', (1.0, 0.5, 0.05), 8.0),
    'ambar_pisca': luz_mat('Luz âmbar pisca', (1.0, 0.45, 0.04), 8.0),
    'verde_luz': luz_mat('Luz verde', (0.15, 1.0, 0.25), 6.0),
    'vermelho_luz': luz_mat('Luz vermelha', (1.0, 0.06, 0.04), 8.0),
    'fogo': fogo_mat(),
    'fumaca': fumaca_grad_mat('Fumaça do flare', 8.0, 3.5, 4.8),
    'vapor_alto': base3d.volume_mat('Vapor alto', (0.92, 0.92, 0.94), 9.0, 2.45, 3.5),
    'vapor_baixo': base3d.volume_mat('Vapor baixo', (0.92, 0.92, 0.94), 9.0, 0.35, 1.2),
    'vapor_troc': base3d.volume_mat('Vapor trocador', (0.92, 0.92, 0.94), 9.0, 0.95, 1.9),
})

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, Z0))
obj('laje', bm, 'concreto')
bm = bmesh.new()
for s in (-1, 1):
    caixa_de(bm, (-1.485, s * 1.47 - 0.008, 0.0), (1.485, s * 1.47 + 0.008, Z0 + 0.001))
    caixa_de(bm, (s * 1.47 - 0.008, -1.485, 0.0), (s * 1.47 + 0.008, 1.485, Z0 + 0.001))
obj('laje_listras', bm, 'listras')
bm = bmesh.new()                                                          # juntas de dilatação
for v in (-0.5, 0.5):
    caixa_de(bm, (-1.46, v - 0.004, Z0), (1.46, v + 0.004, Z0 + 0.002))
    caixa_de(bm, (v - 0.004, -1.46, Z0), (v + 0.004, 1.46, Z0 + 0.002))
obj('laje_juntas', bm, 'preto')

# ------------------------------------------------------------------ bomba de carga (entrada oeste O1)
PB = Vector((-1.05, 0.0, Z_P))                                            # centro da voluta (eixo x)
bm = bmesh.new()
caixa_de(bm, (-1.17, -0.17, Z0), (-0.5, 0.17, Z0 + 0.05))                 # base da bomba
for x in (-1.12, -0.6):
    for s in (-1, 1):
        cil(bm, Vector((x, s * 0.14, Z0 + 0.055)), 0.012, 0.012, lados=6)  # chumbadores
obj('bomba_base', bm, 'grafite')
bm = bmesh.new()
cil(bm, PB, 0.13, 0.1, Vector((1, 0, 0)), lados=28)                       # voluta
cil(bm, PB + Vector((0, 0.04, 0.09)), 0.07, 0.1, Vector((1, 0, 0)), lados=20)   # bojo do caracol
caixa_de(bm, (-1.1, -0.08, Z0 + 0.05), (-1.0, 0.08, PB.z - 0.1))          # pé da voluta
tubo(bm, PB + Vector((0.05, 0, 0)), PB + Vector((0.15, 0, 0)), 0.06, 16)  # caixa de mancal
caixa_de(bm, (-0.98, -0.05, Z0 + 0.05), (-0.92, 0.05, PB.z - 0.04))       # pé do mancal
suavizar(obj('bomba_voluta', bm, 'amarelo'))
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
boca_o = Vector((-1.47, 0, Z_P))
cano(bm, bf, bp, [boca_o, PB + Vector((-0.05, 0, 0))], 0.05, folga=0.05)  # sucção vindo da boca oeste
flange(bf, bp, boca_o + Vector((0.025, 0, 0)), (1, 0, 0), 0.05)            # flange da porta (O1)
rec0 = PB + Vector((0, 0.0, 0.13))
Z_CARGA = 1.95
cano(bm, bf, bp, [rec0, Vector((PB.x, 0, Z_CARGA))], 0.04)                # recalque sobe
cano(bm, bf, bp, [Vector((PB.x, -0.7, Z_CARGA)), Vector((PB.x, 0.7, Z_CARGA))], 0.04, flanges=False)
curva(bm, Vector((PB.x, 0, Z_CARGA)), 0.048)                              # tê do coletor
suavizar(obj('canos_carga', bm, 'processo'))
obj('canos_carga_flanges', bf, 'ferro')
obj('canos_carga_parafusos', bp, 'aco')
bm = bmesh.new()                                                          # motor elétrico da bomba
cil(bm, Vector((-0.68, 0, PB.z)), 0.11, 0.24, Vector((1, 0, 0)), lados=24)
for k in range(9):
    cil(bm, Vector((-0.78 + k * 0.025, 0, PB.z)), 0.122, 0.006, Vector((1, 0, 0)), lados=24)
cil(bm, Vector((-0.54, 0, PB.z)), 0.1, 0.04, Vector((1, 0, 0)), lados=24, r2=0.08)    # tampa da ventoinha
caixa_de(bm, (-0.79, -0.1, Z0 + 0.05), (-0.57, 0.1, PB.z - 0.09))         # pés do motor
caixa_de(bm, (-0.73, -0.05, PB.z + 0.1), (-0.63, 0.05, PB.z + 0.16))      # caixa de ligação
suavizar(obj('bomba_motor', bm, 'grafite'))
bm = bmesh.new()
caixa_de(bm, (-0.92, -0.075, PB.z - 0.075), (-0.8, 0.075, PB.z + 0.075))
obj('bomba_tela', bm, 'malha')
acop = bpy.data.objects.new('acoplamento', None)
sc.collection.objects.link(acop)
acop.location = Vector((-0.86, 0, PB.z))
bm = bmesh.new()
cil(bm, Vector((-0.025, 0, 0)), 0.045, 0.03, Vector((1, 0, 0)), lados=14)
cil(bm, Vector((0.025, 0, 0)), 0.045, 0.03, Vector((1, 0, 0)), lados=14)
for k in range(4):
    a = k * PI / 2
    cil(bm, Vector((0, math.cos(a) * 0.033, math.sin(a) * 0.033)), 0.007, 0.07, Vector((1, 0, 0)), lados=6)
tubo(bm, Vector((-0.07, 0, 0)), Vector((0.07, 0, 0)), 0.015, 10)
obj('acoplamento_aco', bm, 'aco', acop)

# ------------------------------------------------------------------ funil coletor de chuva + filtro (água das camisas)
FU = Vector((-1.2, -1.2, 0))
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=28, radius1=0.05, radius2=0.25, depth=0.25,
                      matrix=Matrix.Translation(FU + Vector((0, 0, 0.88))))
toro(bm, FU + Vector((0, 0, 1.005)), 0.25, 0.012, 40, 8)
suavizar(obj('funil', bm, 'verde'))
bm = bmesh.new()
for k in range(-5, 6):                                                    # grade de cima do funil
    w = math.sqrt(max(0.24 ** 2 - (k * 0.04) ** 2, 0.001))
    caixa(bm, FU + Vector((k * 0.04, 0, 1.0)), (0.006, 2 * w, 0.01))
for k in range(3):                                                        # pernas do funil
    a = k * 2 * PI / 3 + 0.5
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(bm, FU + d * 0.24 + Vector((0, 0, 0.99)), FU + d * 0.28 + Vector((0, 0, Z0)), 0.03)
    caixa(bm, FU + d * 0.28 + Vector((0, 0, Z0 + 0.008)), (0.07, 0.07, 0.016))
obj('funil_grade', bm, 'grafite')
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cil(bm, FU + Vector((0, 0, 0.62)), 0.07, 0.16, lados=20)                  # filtro (cesto)
cil(bm, FU + Vector((0, 0, 0.71)), 0.085, 0.025, lados=20)                # tampa aparafusada
tubo(bm, FU + Vector((0, 0, 0.7)), FU + Vector((0, 0, 0.77)), 0.035, 16)
suavizar(obj('filtro', bm, 'cinza'))
bm = bmesh.new()
ZA = 0.18                                                                  # coletor de água no chão
RX = -0.48
REATORES = (0.7, -0.7)
cano(bm, bf, bp, [FU + Vector((0, 0, 0.54)), FU + Vector((0, 0, ZA)), Vector((-1.22, 0.7, ZA)) + Vector((0.02, 0, 0)),
                  Vector((-1.2, 0.7, 0.82)), Vector((RX - 0.39, 0.7, 0.82))], 0.025)
cano(bm, bf, bp, [Vector((-1.2, -0.7, ZA)), Vector((-1.2, -0.7, 0.82)), Vector((RX - 0.39, -0.7, 0.82))], 0.025)
curva(bm, Vector((-1.2, -0.7, ZA)), 0.03)
cano(bm, bf, bp, [Vector((-1.2, -1.2, ZA)), Vector((0.45, -1.2, ZA)), Vector((0.45, -0.8, ZA)),
                  Vector((0.45, -0.8, 0.25))], 0.025)                      # ramal do casco do trocador
curva(bm, Vector((-1.2, -1.2, ZA)), 0.03)
for p in (Vector((-1.2, -0.95, Z0)), Vector((-1.2, 0.35, Z0)), Vector((-0.4, -1.2, Z0)), Vector((0.2, -1.2, Z0))):
    caixa(bm, p + Vector((0, 0, (ZA - Z0) / 2 - 0.012)), (0.05, 0.05, ZA - Z0 - 0.024))   # apoios do coletor
suavizar(obj('canos_agua', bm, 'verde'))
obj('canos_agua_flanges', bf, 'ferro')
obj('canos_agua_parafusos', bp, 'aco')

# ------------------------------------------------------------------ reatores com camisa
R_R, Z_FUNDO, Z_TOPO = 0.3, 0.6, 1.65
Z_C0, Z_C1, R_C = 0.74, 1.46, 0.33


def zh(off):
    """Altura do tampo abaulado a uma distância `off` do eixo."""
    return Z_TOPO + 0.12 * math.sqrt(max(0.0, 1 - (off / R_R) ** 2))


agitadores, vapor_sil, vapor_purg = [], [], []
bm_cas, bm_cam, bm_fer, bm_bf, bm_bp, bm_ac = (bmesh.new() for _ in range(6))
bm_cr, bm_face, bm_amb, bm_vio, bm_ver, bm_atu = (bmesh.new() for _ in range(6))
bm_proc, bm_vap, bm_resp = bmesh.new(), bmesh.new(), bmesh.new()
for RY in REATORES:
    s = 1 if RY > 0 else -1
    C = Vector((RX, RY, 0))
    cil(bm_cas, C + Vector((0, 0, (Z_FUNDO + Z_TOPO) / 2)), R_R, Z_TOPO - Z_FUNDO, lados=40)
    for zc in (Z_FUNDO, Z_TOPO):                                          # tampos abaulados
        bmesh.ops.create_uvsphere(bm_cas, u_segments=40, v_segments=16, radius=1.0,
                                  matrix=Matrix.Translation(C + Vector((0, 0, zc))) @ Matrix.Diagonal((R_R, R_R, 0.12, 1)))
    # camisa de resfriamento com cones de fechamento e cintas
    cil(bm_cam, C + Vector((0, 0, (Z_C0 + Z_C1) / 2)), R_C, Z_C1 - Z_C0, lados=40)
    cil(bm_cam, C + Vector((0, 0, Z_C0 - 0.03)), R_R + 0.004, 0.06, lados=40, r2=R_C)
    cil(bm_cam, C + Vector((0, 0, Z_C1 + 0.03)), R_C, 0.06, lados=40, r2=R_R + 0.004)
    for z in (0.95, 1.25):
        cil(bm_fer, C + Vector((0, 0, z)), R_C + 0.008, 0.03, lados=40)
    # flange do corpo aparafusada (tampo removível)
    cil(bm_fer, C + Vector((0, 0, Z_TOPO - 0.03)), R_R + 0.035, 0.05, lados=40)
    for k in range(24):
        a = k * 2 * PI / 24
        p = C + Vector((math.cos(a) * (R_R + 0.022), math.sin(a) * (R_R + 0.022), Z_TOPO - 0.03))
        cil(bm_ac, p, 0.006, 0.09, lados=6)
        for dz in (-0.04, 0.04):
            cil(bm_ac, p + Vector((0, 0, dz)), 0.011, 0.014, lados=6)
    # pernas com sapatas e orelhas
    for k in range(4):
        a = k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa_de(bm_fer, C + d * 0.335 + Vector((-0.025, -0.025, Z0)) + Vector((0, 0, 0.012)),
                 C + d * 0.335 + Vector((0.025, 0.025, 0.7)))
        caixa(bm_fer, C + d * 0.335 + Vector((0, 0, Z0 + 0.006)), (0.09, 0.09, 0.012))
        caixa(bm_fer, C + d * 0.32 + Vector((0, 0, 0.66)), (0.07, 0.07, 0.06), Matrix.Rotation(a, 3, 'Z'))
    # bocal de fundo → válvula rotativa (reator norte) ou dreno com válvula (reator sul)
    tubo(bm_cas, C + Vector((0, 0, 0.5)), C + Vector((0, 0, 0.43)), 0.05, 16)
    flange(bm_bf, bm_bp, C + Vector((0, 0, 0.44)), (0, 0, 1), 0.05)
    # agitador: lanterna, redutor, motor com aletas
    caixa(bm_fer, C + Vector((0, 0, 1.85)), (0.17, 0.17, 0.14))
    tubo(bm_fer, C + Vector((0, 0, Z_TOPO + 0.1)), C + Vector((0, 0, 1.78)), 0.05, 16)
    cil(bm_cr, C + Vector((0, 0, 1.775)), 0.065, 0.012, lados=20)
    ag = bpy.data.objects.new('agitador', None)                           # tampa da ventoinha gira (aletas à vista)
    sc.collection.objects.link(ag)
    ag.location = C + Vector((0, 0, 2.17))
    agitadores.append(ag)
    bmm = bmesh.new()
    cil(bmm, C + Vector((0, 0, 2.03)), 0.075, 0.22, lados=24)
    for k in range(7):
        cil(bmm, C + Vector((0, 0, 1.95 + k * 0.025)), 0.088, 0.006, lados=24)
    caixa(bmm, C + Vector((0.09, 0, 2.05)), (0.05, 0.07, 0.07))           # caixa de ligação
    suavizar(obj('agitador_motor', bmm, 'grafite'))
    bmv = bmesh.new()
    for k in range(6):
        a = k * PI / 3
        caixa(bmv, Vector((math.cos(a) * 0.035, math.sin(a) * 0.035, 0)), (0.06, 0.012, 0.01), Matrix.Rotation(a, 3, 'Z'))
    cil(bmv, Vector((0, 0, 0)), 0.018, 0.02, lados=10)
    obj('agitador_ventoinha', bmv, 'aco', ag)
    bmg = bmesh.new()                                                     # grade da ventoinha (fixa)
    for zg in (2.14, 2.2):
        toro(bmg, C + Vector((0, 0, zg)), 0.075, 0.005, 24, 6)
    for k in range(12):
        a = k * PI / 6
        viga(bmg, C + Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, 2.14)), C + Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, 2.2)), 0.005)
    for k in range(6):
        a = k * PI / 3
        viga(bmg, C + Vector((0, 0, 2.2)), C + Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, 2.2)), 0.006)
    cil(bmg, C + Vector((0, 0, 2.155)), 0.012, 0.03, lados=8)          # eixo da ventoinha
    obj('agitador_grade', bmg, 'aco')
    # alimentação: coletor de carga → válvula atuada → bocal no tampo (oeste)
    pf = C + Vector((-0.18, 0, 0))
    bocal(bm_proc, bm_bf, bm_bp, Vector((pf.x, RY, zh(0.18) - 0.01)), (0, 0, 1), 0.035, 0.09)
    cano(bm_proc, bm_bf, bm_bp, [Vector((PB.x, RY, Z_CARGA)), Vector((pf.x, RY, Z_CARGA)),
                                 Vector((pf.x, RY, zh(0.18) + 0.08))], 0.035, flanges=False)
    valvula(bm_fer, bm_atu, bm_bf, bm_bp, Vector((-0.86, RY, Z_CARGA)), (1, 0, 0), 0.035)
    curva(bm_proc, Vector((PB.x, RY, Z_CARGA)), 0.042)
    # saída de vapor de reação (leste do tampo) → torre
    pv = Vector((RX + 0.15, RY, zh(0.15) - 0.01))
    bocal(bm_proc, bm_bf, bm_bp, pv, (0, 0, 1), 0.045, 0.06)
    # PSV no tampo (lado do meio) → coletor de respiro
    pp = Vector((RX, RY - s * 0.17, zh(0.17) - 0.01))
    topo_psv = bocal(bm_fer, bm_bf, bm_bp, pp, (0, 0, 1), 0.03, 0.12)
    cil(bm_fer, topo_psv + Vector((0, 0, 0.04)), 0.045, 0.07, lados=16)    # corpo
    for k in range(4):                                                    # mola exposta
        cil(bm_ac, topo_psv + Vector((0, 0, 0.09 + k * 0.016)), 0.028, 0.005, lados=14)
    tubo(bm_ac, topo_psv + Vector((0, 0, 0.075)), topo_psv + Vector((0, 0, 0.15)), 0.006, 6)
    cil(bm_fer, topo_psv + Vector((0, 0, 0.16)), 0.02, 0.025, lados=12)   # chapéu
    saida = topo_psv + Vector((0, s * 0.0, 0.04))
    tubo(bm_fer, saida, saida + Vector((0, -s * 0.06, 0)), 0.022, 14)  # bocal de escape da PSV
    cano(bm_resp, bm_bf, bm_bp, [saida + Vector((0, -s * 0.06, 0)), Vector((RX, RY - s * 0.29, saida.z)),
                                 Vector((RX, RY - s * 0.29, 2.3)), Vector((RX, 0, 2.3))], 0.03, flanges=False)
    # manômetro no tampo (lado de fora)
    pm = Vector((RX, RY + s * 0.17, zh(0.17)))
    tubo(bm_cr, pm, pm + Vector((0, 0, 0.12)), 0.008, 8)
    manometro(bm_cr, bm_face, pm + Vector((0, s * 0.0, 0.16)), (0.3, s * 0.95, 0.1))
    # camisa: entrada de água (oeste, baixo), saída de vapor (lado de fora, alto) → silenciador
    bocal(bm_cam, bm_bf, bm_bp, C + Vector((-R_C + 0.005, 0, 0.82)), (-1, 0, 0), 0.025, 0.06)
    sv = bocal(bm_cam, bm_bf, bm_bp, C + Vector((0, s * (R_C - 0.005), 1.38)), (0, s, 0), 0.03, 0.08)
    yv = RY + s * 0.5
    cano(bm_vap, bm_bf, bm_bp, [sv, Vector((RX, yv, 1.38)), Vector((RX, yv, 2.3))], 0.03)
    cil(bm_fer, Vector((RX, yv, 2.42)), 0.06, 0.2, lados=20)               # silenciador
    cil(bm_fer, Vector((RX, yv, 2.53)), 0.045, 0.03, lados=20)
    for z in (2.34, 2.5):
        cil(bm_ac, Vector((RX, yv, z)), 0.065, 0.012, lados=20)
    viga(bm_fer, Vector((RX, yv, 1.6)), Vector((RX, RY + s * R_C, 1.48)), 0.025)    # suporte do respiro na camisa
    vapor_sil.append(Vector((RX, yv, 2.56)))
    # purgador na base da camisa (lado do meio, diagonal)
    a = -s * math.radians(40)
    d = Vector((math.cos(a), math.sin(a), 0))
    p0 = C + d * (R_R + 0.02) + Vector((0, 0, Z_C0 - 0.04))
    p1 = C + d * 0.42 + Vector((0, 0, 0.66))
    p2 = Vector((p1.x, p1.y, 0.4))
    cano(bm_vap, bm_bf, bm_bp, [p0, p1, p2], 0.014, flanges=False)
    cil(bm_fer, p2 + Vector((0, 0, -0.03)), 0.04, 0.07, d, lados=16)       # corpo do purgador
    caixa(bm_fer, p2 + Vector((0, 0, -0.03)) + d * 0.04, (0.03, 0.03, 0.03))
    cil(bm_ac, p2 + Vector((0, 0, -0.03)) + d * 0.075, 0.01, 0.04, d, lados=8)
    vapor_purg.append((p2 + Vector((0, 0, -0.03)) + d * 0.1, d))
    # sensor da IA na camisa (leste)
    caixa(bm_fer, C + Vector((R_C + 0.04, 0, 1.1)), (0.08, 0.14, 0.16))
    caixa(bm_vio, C + Vector((R_C + 0.081, -0.03, 1.14)), (0.004, 0.025, 0.012))
    caixa(bm_amb, C + Vector((R_C + 0.081, 0.03, 1.14)), (0.004, 0.012, 0.012))
    caixa(bm_ver, C + Vector((R_C + 0.081, 0.0, 1.08)), (0.004, 0.06, 0.006))
    # manômetro da camisa
    manometro(bm_cr, bm_face, C + Vector((-0.24, -s * 0.24, 1.32)) + Vector((-0.06, -s * 0.06, 0)),
              (-0.7, -s * 0.7, 0.1), haste=C + Vector((-0.235, -s * 0.235, 1.32)))
suavizar(obj('reator_casco', bm_cas, 'inox'))
suavizar(obj('reator_camisa', bm_cam, 'amarelo'))
obj('led_violeta', bm_vio, 'violeta')
obj('led_ambar', bm_amb, 'ambar_pisca')
obj('led_verde', bm_ver, 'verde_luz')
obj('reator_parafusos', bm_ac, 'aco')
# coletor de respiro: entre os reatores (x = RX), segue a leste em y=0 e sobe até o flare
FL = Vector((1.2, 1.2, 0))
cano(bm_resp, bm_bf, bm_bp, [Vector((RX, 0, 2.3)), Vector((FL.x, 0, 2.3)), Vector((FL.x, FL.y - 0.07, 2.3))], 0.035)
curva(bm_resp, Vector((RX, 0, 2.3)), 0.04)

# ------------------------------------------------------------------ torre de fracionamento
T = Vector((0.55, 0.42, 0))
R_T, Z_SAIA, Z_TT = 0.27, 0.45, 3.0
JUNTAS = (1.0, 1.6, 2.2)
PRATOS = (0.75, 1.2, 1.38, 1.8, 2.0, 2.4, 2.58)
bm = bmesh.new()
cil(bm, T + Vector((0, 0, (Z_SAIA + Z_TT) / 2)), R_T, Z_TT - Z_SAIA, lados=40)
bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=16, radius=1.0,
                          matrix=Matrix.Translation(T + Vector((0, 0, Z_TT))) @ Matrix.Diagonal((R_T, R_T, 0.12, 1)))
bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=16, radius=1.0,
                          matrix=Matrix.Translation(T + Vector((0, 0, Z_SAIA))) @ Matrix.Diagonal((R_T, R_T, 0.1, 1)))
suavizar(obj('torre', bm, 'cinza'))
bm = bmesh.new()                                                          # saia com abertura de acesso
bmesh.ops.create_cone(bm, cap_ends=False, segments=40, radius1=R_T + 0.02, radius2=R_T, depth=Z_SAIA - Z0,
                      matrix=Matrix.Translation(T + Vector((0, 0, (Z_SAIA + Z0) / 2))))
cil(bm, T + Vector((0, 0, Z0 + 0.015)), R_T + 0.07, 0.03, lados=40)       # anel de base
suavizar(obj('torre_saia', bm, 'listras'))
bm, bp = bmesh.new(), bmesh.new()
for z in JUNTAS:                                                          # juntas flangeadas entre seções
    for dz in (-0.014, 0.014):
        cil(bm, T + Vector((0, 0, z + dz)), R_T + 0.035, 0.024, lados=40)
    for k in range(28):
        a = k * 2 * PI / 28
        p = T + Vector((math.cos(a) * (R_T + 0.022), math.sin(a) * (R_T + 0.022), z))
        cil(bp, p, 0.005, 0.085, lados=6)
        for dz in (-0.034, 0.034):
            cil(bp, p + Vector((0, 0, dz)), 0.01, 0.012, lados=6)
for k in range(12):                                                       # chumbadores da saia
    a = k * PI / 6
    cil(bp, T + Vector((math.cos(a) * (R_T + 0.05), math.sin(a) * (R_T + 0.05), Z0 + 0.04)), 0.012, 0.04, lados=6)
obj('torre_juntas', bm, 'ferro')
obj('torre_parafusos', bp, 'aco')
# visores de prato (lado oeste-sudoeste): janelinha redonda com líquido âmbar borbulhando no prato
A_VIS = math.radians(205)
dV = Vector((math.cos(A_VIS), math.sin(A_VIS), 0))
bm, bv, bl, bp = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for z in PRATOS:
    c = T + dV * R_T + Vector((0, 0, z))
    tubo(bm, c - dV * 0.02, c + dV * 0.035, 0.05, 24)
    tubo(bv, c + dV * 0.035, c + dV * 0.04, 0.036, 24)
    tubo(bl, c + dV * 0.02, c + dV * 0.03, 0.037, 24)
    e1, e2 = base_perp(dV)
    for k in range(6):
        a = k * PI / 3
        p = c + dV * 0.037 + (e1 * math.cos(a) + e2 * math.sin(a)) * 0.043
        tubo(bp, p - dV * 0.006, p + dV * 0.008, 0.006, 6)
suavizar(obj('visores_prato', bm, 'ferro'))
obj('visores_vidro', bv, 'vidro')
obj('visores_parafusos', bp, 'aco')
liq_prato = obj('visores_liquido', bl, 'liquido')
bm = bmesh.new()                                                          # linha do prato: meia lua escura no fundo do visor
for z in PRATOS:
    c = T + dV * (R_T + 0.031) + Vector((0, 0, z - 0.018))
    caixa(bm, c, (0.006, 0.06, 0.016), Matrix.Rotation(A_VIS, 3, 'Z'))
obj('visores_prato_chapa', bm, 'preto')
# visor de nível (leste, seção de fundo): tubo de vidro entre dois bocais, líquido sobe e desce
dN = Vector((1, 0, 0))
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
for z in (0.62, 1.22):
    bocal(bm, bf, bp, T + dN * (R_T - 0.01) + Vector((0, 0, z)), dN, 0.02, 0.1)
    curva(bm, T + dN * (R_T + 0.11) + Vector((0, 0, z)), 0.022)
tubo(bm, T + dN * (R_T + 0.11) + Vector((0, 0, 0.62)), T + dN * (R_T + 0.11) + Vector((0, 0, 0.66)), 0.03, 16)
tubo(bm, T + dN * (R_T + 0.11) + Vector((0, 0, 1.18)), T + dN * (R_T + 0.11) + Vector((0, 0, 1.22)), 0.03, 16)
for dy in (-0.032, 0.032):                                                # guarda do vidro
    tubo(bm, T + dN * (R_T + 0.11) + Vector((0, dy, 0.65)), T + dN * (R_T + 0.11) + Vector((0, dy, 1.19)), 0.006, 6)
suavizar(obj('visor_nivel', bm, 'ferro'))
obj('visor_nivel_flanges', bf, 'ferro')
obj('visor_nivel_parafusos', bp, 'aco')
bm = bmesh.new()
tubo(bm, T + dN * (R_T + 0.11) + Vector((0, 0, 0.66)), T + dN * (R_T + 0.11) + Vector((0, 0, 1.18)), 0.022, 16)
suavizar(obj('visor_nivel_vidro', bm, 'vidro'))
nivel = bpy.data.objects.new('nivel', None)
sc.collection.objects.link(nivel)
nivel.location = T + dN * (R_T + 0.11) + Vector((0, 0, 0.66))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.5)), 0.016, 1.0, lados=16)
obj('visor_nivel_liquido', bm, 'liquido', nivel)
# olhos de ressonância (sudeste): a IA "escuta" os pratos por dentro; bocal pequeno, lente violeta, sem porta de gente
A_BV = math.radians(-40)
dB = Vector((math.cos(A_BV), math.sin(A_BV), 0))
bm, bf, bp, bl = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
for z in (1.3, 2.45):
    c = T + dB * (R_T - 0.01) + Vector((0, 0, z))
    tubo(bm, c, c + dB * 0.07, 0.04, 20)
    flange(bf, bp, c + dB * 0.07, dB, 0.04)
    tubo(bm, c + dB * 0.085, c + dB * 0.14, 0.05, 20)                     # corpo do sensor
    for k in range(3):                                                    # aletas de ressonância
        tubo(bm, c + dB * (0.1 + k * 0.014), c + dB * (0.106 + k * 0.014), 0.065, 20)
    tubo(bl, c + dB * 0.14, c + dB * 0.146, 0.032, 20)                    # lente
suavizar(obj('torre_sensores', bm, 'grafite'))
obj('torre_sensores_flanges', bf, 'ferro')
obj('torre_sensores_parafusos', bp, 'aco')
obj('torre_sensores_lente', bl, 'violeta')
# trilho-cremalheira de manutenção robótica (face norte): dois trilhos + cremalheira, sem degrau nem guarda-corpo
dR = Vector((0, 1, 0))
Y_TR = T.y + R_T + 0.075
Z_TR0, Z_TR1 = 0.5, 2.62
bm, bc = bmesh.new(), bmesh.new()
for dx in (-0.06, 0.06):
    caixa_de(bm, (T.x + dx - 0.012, Y_TR - 0.012, Z_TR0), (T.x + dx + 0.012, Y_TR + 0.012, Z_TR1))
caixa_de(bc, (T.x - 0.012, Y_TR - 0.008, Z_TR0), (T.x + 0.012, Y_TR + 0.004, Z_TR1))
z = Z_TR0 + 0.01
while z < Z_TR1 - 0.01:                                                   # dentes da cremalheira
    caixa(bc, (T.x, Y_TR + 0.008, z), (0.024, 0.008, 0.009))
    z += 0.022
for z in (0.55, 0.85, 1.2, 1.5, 1.85, 2.1, 2.55):                         # consoles até o costado (fora das juntas)
    caixa_de(bm, (T.x - 0.08, T.y + R_T - 0.01, z - 0.012), (T.x + 0.08, Y_TR - 0.012, z + 0.012))
caixa_de(bm, (T.x - 0.09, Y_TR - 0.02, Z_TR1), (T.x + 0.09, Y_TR + 0.02, Z_TR1 + 0.02))   # batente de fim de curso
obj('trilho', bm, 'amarelo')
obj('cremalheira', bc, 'aco')
robo = bpy.data.objects.new('robo', None)                                 # robô de inspeção que sobe e desce
sc.collection.objects.link(robo)
robo.location = Vector((T.x, Y_TR, 1.0))
bm = bmesh.new()
caixa(bm, (0, 0.06, 0), (0.17, 0.07, 0.16))
caixa(bm, (0, 0.11, 0.03), (0.08, 0.04, 0.07))                            # cabeça de sensores
obj('robo_corpo', bm, 'amarelo', robo)
bm = bmesh.new()
for dx in (-0.06, 0.06):
    for dz in (-0.055, 0.055):
        for s in (-1, 1):
            cil(bm, Vector((dx + s * 0.022, 0.0, dz)), 0.012, 0.012, Vector((0, 1, 0)), lados=10)   # rodas abraçando o trilho
caixa(bm, (0, 0.025, 0), (0.15, 0.012, 0.15))
cil(bm, Vector((0.0, 0.01, 0.0)), 0.016, 0.03, Vector((1, 0, 0)), lados=10)   # pinhão
obj('robo_rodas', bm, 'grafite', robo)
bm = bmesh.new()
cil(bm, Vector((0.0, 0.132, 0.04)), 0.012, 0.006, Vector((0, 1, 0)), lados=12)
cil(bm, Vector((0.022, 0.132, 0.02)), 0.007, 0.006, Vector((0, 1, 0)), lados=10)
obj('robo_olhos', bm, 'violeta', robo)
bm = bmesh.new()
cil(bm, Vector((-0.06, 0.06, 0.09)), 0.01, 0.02, lados=10)
obj('robo_luz', bm, 'ambar_pisca', robo)
bm = bmesh.new()                                                          # cabo do robô (festão) até a caixa no pé
mangueira(bm, bezier((T.x + 0.11, Y_TR, Z_TR0 + 0.05), (T.x + 0.2, Y_TR + 0.06, 0.4), (T.x + 0.2, Y_TR + 0.04, 0.2),
                     (T.x + 0.14, Y_TR - 0.02, 0.14), 8), 0.008)
caixa(bm, (T.x + 0.14, Y_TR - 0.05, 0.13), (0.08, 0.05, 0.1))
obj('robo_cabo', bm, 'grafite')
# anel de campo da IA (gira no alto da torre)
Z_AN, R_AN = 2.82, 0.5
bm = bmesh.new()
cil(bm, T + Vector((0, 0, Z_AN)), R_T + 0.03, 0.16, lados=40)             # colar emissor que sustenta o anel pelo campo
for dz in (-0.09, 0.09):
    cil(bm, T + Vector((0, 0, Z_AN + dz)), R_T + 0.05, 0.02, lados=40)
for k in range(16):                                                       # bobinas do colar
    a = k * 2 * PI / 16
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, T + d * (R_T + 0.045) + Vector((0, 0, Z_AN)), (0.03, 0.05, 0.14), Matrix.Rotation(a, 3, 'Z'))
obj('anel_colar', bm, 'grafite')
bm = bmesh.new()
cil(bm, T + Vector((0, 0, Z_AN)), R_T + 0.032, 0.012, lados=40)
obj('anel_colar_luz', bm, 'violeta')
anel = bpy.data.objects.new('anel', None)
sc.collection.objects.link(anel)
anel.location = T + Vector((0, 0, Z_AN))
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), R_AN, 0.03, 72, 14)                          # anel solto: levita, sem nada que o prenda
suavizar(obj('anel_estrutura', bm, 'grafite', anel))
bm = bmesh.new()
toro(bm, Vector((0, 0, 0)), R_AN - 0.028, 0.009, 72, 8)
obj('anel_campo', bm, 'violeta', anel)
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(8):                                                        # emissores do campo
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, d * R_AN, (0.05, 0.05, 0.08), Matrix.Rotation(a, 3, 'Z'))
    caixa(bm2, d * (R_AN + 0.026), (0.003, 0.03, 0.04), Matrix.Rotation(a, 3, 'Z'))
obj('anel_emissores', bm, 'cinza', anel)
obj('anel_emissores_luz', bm2, 'ambar', anel)
luz_anel = bpy.data.lights.new('Campo', 'POINT')
luz_anel.color = (0.6, 0.25, 1.0)
luz_anel.energy = 35
luz_anel.shadow_soft_size = 0.4
la = bpy.data.objects.new('Campo', luz_anel)
sc.collection.objects.link(la)
la.location = T + Vector((0, -0.6, Z_AN))
# antena no tampo da torre
bm = bmesh.new()
tubo(bm, T + Vector((-0.12, -0.08, Z_TT + 0.08)), T + Vector((-0.12, -0.08, 3.45)), 0.01, 8)
cil(bm, T + Vector((-0.12, -0.08, Z_TT + 0.12)), 0.03, 0.03, lados=10)
for z in (3.2, 3.32):
    viga(bm, T + Vector((-0.2, -0.08, z)), T + Vector((-0.04, -0.08, z)), 0.008)
obj('antena', bm, 'aco')
bm = bmesh.new()
cil(bm, T + Vector((-0.12, -0.08, 3.46)), 0.016, 0.03, lados=10)
obj('antena_luz', bm, 'vermelho_luz')

# ------------------------------------------------------------------ vapores dos reatores → torre; topo → flare
def ponto_torre(de, z):
    d = (T.xy - Vector(de).xy).normalized().to_3d()
    return T - d * (R_T - 0.01) + Vector((0, 0, z)), d


p_a, d_a = ponto_torre((0.15, 0.7), 1.84)
cano(bm_proc, bm_bf, bm_bp, [Vector((RX + 0.15, 0.7, zh(0.15) + 0.05)), Vector((RX + 0.15, 0.7, 1.84)),
                             Vector((0.15, 0.7, 1.84)), p_a - d_a * 0.12], 0.045)
bocal(bm_proc, bm_bf, bm_bp, p_a, -d_a, 0.045, 0.12)
p_b = T + Vector((0, -(R_T - 0.01), 2.03))
cano(bm_proc, bm_bf, bm_bp, [Vector((RX + 0.15, -0.7, zh(0.15) + 0.05)), Vector((RX + 0.15, -0.7, 2.03)),
                             Vector((RX + 0.15, -0.25, 2.03)), Vector((T.x, -0.25, 2.03)), p_b + Vector((0, -0.12, 0))], 0.045)
bocal(bm_proc, bm_bf, bm_bp, p_b, (0, -1, 0), 0.045, 0.12)
# fundo da torre → trocador (canal oeste, bocal de cima)
X_T0, X_T1, Y_TC, Z_TC, R_TC = 0.1, 1.02, -0.8, 0.42, 0.16
p_f = T + Vector((0, -(R_T - 0.01), 0.75))
bocal(bm_proc, bm_bf, bm_bp, p_f, (0, -1, 0), 0.04, 0.1)
cano(bm_proc, bm_bf, bm_bp, [p_f + Vector((0, -0.1, 0)), Vector((T.x, -0.45, 0.75)), Vector((0.16, -0.45, 0.75)),
                             Vector((0.16, Y_TC, 0.75)), Vector((0.16, Y_TC, Z_TC + R_TC + 0.07))], 0.04)
valvula(bm_fer, bm_atu, bm_bf, bm_bp, Vector((0.36, -0.45, 0.75)), (1, 0, 0), 0.04)
manometro(bm_cr, bm_face, Vector((T.x + 0.07, -0.2, 0.86)), (1, -0.3, 0.2), haste=Vector((T.x, -0.2, 0.75)))
# topo da torre → flare
cano(bm_resp, bm_bf, bm_bp, [T + Vector((0, 0, Z_TT + 0.1)), T + Vector((0, 0, 3.22)), Vector((FL.x, T.y, 3.22)),
                             Vector((FL.x, T.y, 2.92)), Vector((FL.x, FL.y - 0.07, 2.92))], 0.035)
bocal(bm_resp, bm_bf, bm_bp, T + Vector((0, 0, Z_TT + 0.08)), (0, 0, 1), 0.035, 0.04)

# ------------------------------------------------------------------ trocador de calor casco-e-tubo
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
cil(bm, Vector(((X_T0 + X_T1) / 2, Y_TC, Z_TC)), R_TC, (X_T1 - X_T0) - 0.24, Vector((1, 0, 0)), lados=36)
suavizar(obj('trocador_casco', bm, 'cinza'))
bm = bmesh.new()
for x0, x1 in ((X_T0, X_T0 + 0.12), (X_T1 - 0.12, X_T1)):                 # carretéis (cabeçotes) amarelos
    cil(bm, Vector(((x0 + x1) / 2, Y_TC, Z_TC)), R_TC + 0.01, x1 - x0, Vector((1, 0, 0)), lados=36)
suavizar(obj('trocador_cabecotes', bm, 'amarelo'))
for x in (X_T0 + 0.12, X_T1 - 0.12, X_T0 - 0.005, X_T1 + 0.005):          # flanges de espelho e tampas aparafusadas
    for s in (-1, 1):
        cil(bf, Vector((x + s * 0.012, Y_TC, Z_TC)), R_TC + 0.035, 0.022, Vector((1, 0, 0)), lados=36)
    for k in range(16):
        a = k * 2 * PI / 16
        p = Vector((x, Y_TC + math.cos(a) * (R_TC + 0.022), Z_TC + math.sin(a) * (R_TC + 0.022)))
        tubo(bp, p - Vector((0.035, 0, 0)), p + Vector((0.035, 0, 0)), 0.005, 6)
        for s in (-1, 1):
            tubo(bp, p + Vector((s * 0.026, 0, 0)), p + Vector((s * 0.034, 0, 0)), 0.009, 6)
for x in (0.3, 0.82):                                                     # selas
    caixa_de(bf, (x - 0.05, Y_TC - 0.15, Z0), (x + 0.05, Y_TC + 0.15, Z0 + 0.02))
    caixa_de(bf, (x - 0.012, Y_TC - 0.13, Z0), (x + 0.012, Y_TC + 0.13, Z_TC - 0.05))
    caixa_de(bf, (x - 0.03, Y_TC - 0.13, Z_TC - 0.13), (x + 0.03, Y_TC + 0.13, Z_TC - 0.1))
obj('trocador_flanges', bf, 'ferro')
obj('trocador_parafusos', bp, 'aco')
bm, bf, bp = bmesh.new(), bmesh.new(), bmesh.new()
bocal(bm, bf, bp, Vector((0.16, Y_TC, Z_TC + R_TC - 0.01)), (0, 0, 1), 0.04, 0.08)       # entrada (do fundo da torre)
bocal(bm, bf, bp, Vector((0.45, Y_TC, Z_TC - R_TC + 0.01)), (0, 0, -1), 0.025, 0.06)     # água no casco
pvt = bocal(bm, bf, bp, Vector((0.7, Y_TC, Z_TC + R_TC - 0.01)), (0, 0, 1), 0.025, 0.06)  # vapor do casco
cano(bm, bf, bp, [pvt, Vector((0.7, Y_TC, 0.88))], 0.025, flanges=False)
cil(bm, Vector((0.7, Y_TC, 0.92)), 0.045, 0.1, lados=18)                  # silenciador pequeno
obj('trocador_bocais', bm, 'aco')
obj('trocador_bocais_flanges', bf, 'ferro')
obj('trocador_bocais_parafusos', bp, 'aco')
bocal(bm_proc, bm_bf, bm_bp, Vector((X_T1 - 0.01, Y_TC, Z_TC)), (1, 0, 0), 0.04, 0.07)    # saída do produto
boca_l = Vector((1.47, 0, Z_P))
cano(bm_proc, bm_bf, bm_bp, [Vector((X_T1 + 0.06, Y_TC, Z_TC)), Vector((1.25, Y_TC, Z_TC)), Vector((1.25, 0, Z_TC)),
                             Vector((1.25, 0, Z_P)), boca_l], 0.04, folga=0.06)
flange(bm_bf, bm_bp, boca_l - Vector((0.025, 0, 0)), (1, 0, 0), 0.04)     # flange da porta (L1)
valvula(bm_fer, bm_atu, bm_bf, bm_bp, Vector((1.25, -0.42, Z_TC)), (0, 1, 0), 0.04)
manometro(bm_cr, bm_face, Vector((1.32, -0.2, Z_TC + 0.1)), (1, 0, 0.3), haste=Vector((1.25, -0.2, Z_TC)))
for y in (-0.62, -0.2):                                                   # apoios da linha de saída
    caixa_de(bm_fer, (1.225, y - 0.025, Z0), (1.275, y + 0.025, Z_TC - 0.04))
    caixa_de(bm_fer, (1.2, y - 0.04, Z_TC - 0.05), (1.3, y + 0.04, Z_TC - 0.04))
caixa_de(bm_fer, (1.335, -0.025, Z0), (1.385, 0.025, Z_P - 0.04))
caixa_de(bm_fer, (1.31, -0.04, Z_P - 0.05), (1.41, 0.04, Z_P - 0.04))
# apoios das linhas aéreas (pórticos simples)
for x, y, z in ((0.12, 0.7, 1.84), (0.25, -0.25, 2.03), (FL.x, 0.25, 2.3)):
    viga(bm_fer, Vector((x, y, z - 0.05)), Vector((x, y, Z0)), 0.045)
    caixa(bm_fer, Vector((x, y, Z0 + 0.008)), (0.1, 0.1, 0.016))
    caixa(bm_fer, Vector((x, y, z - 0.055)), (0.12, 0.12, 0.012))
for y in (-0.45, 0.45):
    viga(bm_fer, Vector((PB.x, y, Z_CARGA - 0.05)), Vector((PB.x - 0.0, y, Z0)), 0.04)
    caixa(bm_fer, Vector((PB.x, y, Z0 + 0.008)), (0.1, 0.1, 0.016))
    caixa(bm_fer, Vector((PB.x, y, Z_CARGA - 0.055)), (0.1, 0.1, 0.012))
manometro(bm_cr, bm_face, Vector((PB.x + 0.07, -0.0, 0.62)), (1, -0.4, 0.1), haste=Vector((PB.x, 0, 0.62)))

# ------------------------------------------------------------------ flare (respiro com chama piloto)
Z_FL = 3.3
bm = bmesh.new()
cil(bm, FL + Vector((0, 0, (Z0 + 0.62) / 2)), 0.17, 0.62 - Z0, lados=32)   # vaso separador (pega o condensado)
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=12, radius=1.0,
                          matrix=Matrix.Translation(FL + Vector((0, 0, 0.62))) @ Matrix.Diagonal((0.17, 0.17, 0.08, 1)))
suavizar(obj('flare_vaso', bm, 'oxido'))
bm = bmesh.new()
cil(bm, FL + Vector((0, 0, (0.68 + 2.95) / 2)), 0.055, 2.95 - 0.68, lados=24)
for z in (1.2, 1.9, 2.6):
    cil(bm, FL + Vector((0, 0, z)), 0.07, 0.02, lados=24)
suavizar(obj('flare_haste', bm, 'oxido'))
bm = bmesh.new()
cil(bm, FL + Vector((0, 0, (2.95 + Z_FL - 0.06) / 2)), 0.055, Z_FL - 0.06 - 2.95, lados=24)
cil(bm, FL + Vector((0, 0, Z_FL - 0.03)), 0.075, 0.06, lados=24)          # ponta do flare
bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.09, radius2=0.1, depth=0.1,
                      matrix=Matrix.Translation(FL + Vector((0, 0, Z_FL - 0.02))))   # quebra-vento
suavizar(obj('flare_ponta', bm, 'fuligem'))
bm = bmesh.new()
for k in range(3):                                                        # pilotos e linha de gás piloto
    a = k * 2 * PI / 3 + 0.3
    d = Vector((math.cos(a), math.sin(a), 0))
    tubo(bm, FL + d * 0.085 + Vector((0, 0, Z_FL - 0.2)), FL + d * 0.085 + Vector((0, 0, Z_FL + 0.02)), 0.008, 8)
a = 0.3
d = Vector((math.cos(a), math.sin(a), 0))
tubo(bm, FL + d * 0.085 + Vector((0, 0, Z_FL - 0.2)), FL + d * 0.07 + Vector((0, 0, 0.66)), 0.008, 8)
tubo(bm, FL + d * 0.07 + Vector((0, 0, 0.66)), FL + d * 0.18 + Vector((0, 0, 0.66)), 0.008, 8)
obj('flare_pilotos', bm, 'cobre')
bm = bmesh.new()                                                          # estais
for alvo in (Vector((1.45, 0.45, Z0)), Vector((0.45, 1.45, Z0)), Vector((1.45, 1.45, Z0))):
    topo = FL + Vector((0, 0, 2.6)) + (alvo - FL).xy.to_3d().normalized() * 0.07
    tubo(bm, topo, alvo + Vector((0, 0, 0.03)), 0.004, 6)
    caixa(bm, alvo + Vector((0, 0, 0.015)), (0.05, 0.05, 0.03))
obj('flare_estais', bm, 'aco')
chama = []
for k, (esc, alt) in enumerate(((0.085, 0.5), (0.035, 0.14))):              # chama do flare e chama piloto
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        v.co.z = (v.co.z + 1.0) / 2.0
    o = obj('chama', bm, 'fogo')
    o.location = FL + Vector((0, 0, Z_FL - 0.01))
    chama.append((o, esc, alt))
luz_fl = bpy.data.lights.new('Flare', 'POINT')
luz_fl.color = (1.0, 0.5, 0.15)
luz_fl.shadow_soft_size = 0.15
lf = bpy.data.objects.new('Flare', luz_fl)
sc.collection.objects.link(lf)
lf.location = FL + Vector((0, 0, Z_FL + 0.15))

# ------------------------------------------------------------------ produto sólido: válvula rotativa, rosca, encapsulador, bica norte (N0)
RA = Vector((RX, 0.7, 0))
CX, CY0, CY1 = -1.0, 0.98, 1.24                                           # encapsulador centrado no tile N0
bm = bmesh.new()
caixa(bm, RA + Vector((0, 0, 0.36)), (0.12, 0.12, 0.1))                   # válvula rotativa
cil(bm, RA + Vector((0.09, 0, 0.36)), 0.035, 0.06, Vector((1, 0, 0)), lados=14)   # redutor
cil(bm, RA + Vector((0.17, 0, 0.36)), 0.04, 0.1, Vector((1, 0, 0)), lados=14)     # motor
tubo(bm, RA + Vector((0, 0, 0.41)), RA + Vector((0, 0, 0.44)), 0.05, 16)
r0 = RA + Vector((0, 0, 0.27))
r1 = Vector((CX + 0.05, CY0 + 0.1, 0.26))
cil(bm, r0, 0.06, 0.06, lados=16)                                         # bota da rosca
tubo(bm, r0 + (r1 - r0).normalized() * -0.08, r1, 0.05, 20)               # calha tubular da rosca
cil(bm, r0 + (r1 - r0).normalized() * -0.12, 0.05, 0.07, r1 - r0, lados=14)   # motor da rosca
for t in (0.25, 0.7):
    p = r0 + (r1 - r0) * t
    caixa_de(bm, (p.x - 0.02, p.y - 0.02, Z0), (p.x + 0.02, p.y + 0.02, p.z - 0.045))
suavizar(obj('rosca', bm, 'amarelo'))
bm = bmesh.new()
caixa_de(bm, (CX - 0.16, CY0, Z0), (CX + 0.16, CY1, 0.34))                # encapsulador
obj('encapsulador', bm, 'grafite')
bm = bmesh.new()
caixa_de(bm, (CX - 0.17, CY0 - 0.01, 0.34), (CX + 0.17, CY1 + 0.01, 0.36))
for x in (CX - 0.1, CX + 0.1):
    caixa_de(bm, (x - 0.02, CY0 - 0.01, Z0), (x + 0.02, CY0, 0.34))
obj('encapsulador_quadro', bm, 'amarelo')
bm = bmesh.new()
caixa_de(bm, (CX - 0.075, CY1, 0.13), (CX + 0.075, CY1 + 0.003, 0.24))   # boca de saída escura
obj('encapsulador_boca', bm, 'preto')
bm = bmesh.new()
caixa_de(bm, (CX - 0.08, CY1, 0.245), (CX + 0.08, CY1 + 0.006, 0.255))
caixa_de(bm, (CX + 0.11, CY0 - 0.004, 0.27), (CX + 0.14, CY0, 0.3))
obj('encapsulador_luz', bm, 'ambar')
bm = bmesh.new()
caixa_de(bm, (CX - 0.13, CY0 - 0.005, 0.2), (CX - 0.05, CY0, 0.3))
obj('encapsulador_tela', bm, 'violeta')
# bica de roletes: do encapsulador até a borda norte, descendo
B0, B1 = Vector((CX, CY1, 0.13)), Vector((CX, 1.47, 0.1))
bm, br = bmesh.new(), bmesh.new()
for s in (-1, 1):
    caixa_de(bm, (CX + s * 0.085 - 0.008, CY1, 0.08), (CX + s * 0.085 + 0.008, 1.47, 0.17))
k = 0
while k * 0.035 < (B1 - B0).length - 0.01:
    p = B0 + (B1 - B0).normalized() * (0.02 + k * 0.035)
    cil(br, p, 0.012, 0.16, Vector((1, 0, 0)), lados=10)
    k += 1
caixa_de(bm, (CX - 0.1, 1.44, Z0), (CX + 0.1, 1.47, 0.09))
obj('bica_lados', bm, 'amarelo')
suavizar(obj('bica_roletes', br, 'aco'))
CELULAS = []
for k in range(3):                                                        # células/baterias saindo
    e = bpy.data.objects.new('celula', None)
    sc.collection.objects.link(e)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.045, 0.13, Vector((1, 0, 0)), lados=20)
    suavizar(obj('celula_casca', bm, 'bateria', e))
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.046, 0.02, Vector((1, 0, 0)), lados=20)
    obj('celula_faixa', bm, 'violeta', e)
    bm = bmesh.new()
    cil(bm, Vector((0.07, 0, 0)), 0.016, 0.014, Vector((1, 0, 0)), lados=12)
    cil(bm, Vector((-0.066, 0, 0)), 0.03, 0.006, Vector((1, 0, 0)), lados=12)
    obj('celula_polos', bm, 'cobre', e)
    CELULAS.append(e)

# ------------------------------------------------------------------ armário da IA, eletrocalha e cabos
AR = Vector((1.18, -1.22, 0))
bm = bmesh.new()
caixa_de(bm, (AR.x - 0.16, AR.y - 0.12, Z0), (AR.x + 0.16, AR.y + 0.12, 0.74))
caixa_de(bm, (AR.x - 0.18, AR.y - 0.14, 0.74), (AR.x + 0.18, AR.y + 0.14, 0.77))   # chapéu de chuva
obj('armario', bm, 'grafite')
bm = bmesh.new()
for k in range(5):
    caixa_de(bm, (AR.x - 0.12 + k * 0.035, AR.y + 0.12, 0.6), (AR.x - 0.1 + k * 0.035, AR.y + 0.123, 0.62))
obj('armario_leds', bm, 'violeta')
bm = bmesh.new()
caixa_de(bm, (AR.x + 0.07, AR.y + 0.12, 0.6), (AR.x + 0.11, AR.y + 0.123, 0.62))
obj('armario_led2', bm, 'ambar_pisca')
bm = bmesh.new()
for z in (0.25, 0.4):
    caixa_de(bm, (AR.x - 0.12, AR.y + 0.12, z), (AR.x + 0.12, AR.y + 0.124, z + 0.08))   # venezianas
tubo(bm, Vector((AR.x + 0.1, AR.y - 0.05, 0.77)), Vector((AR.x + 0.1, AR.y - 0.05, 1.5)), 0.012, 8)   # antena
for z in (1.2, 1.35):
    viga(bm, Vector((AR.x + 0.04, AR.y - 0.05, z)), Vector((AR.x + 0.16, AR.y - 0.05, z)), 0.008)
obj('armario_detalhes', bm, 'aco')
bm = bmesh.new()
cil(bm, Vector((AR.x + 0.1, AR.y - 0.05, 1.52)), 0.016, 0.03, lados=10)
obj('armario_antena_luz', bm, 'vermelho_luz')
# eletrocalha no piso: armário → oeste (y=-1.1) → norte (x=-0.05) até o reator norte
YE, XE = -1.08, -0.04
bm, bc, ba = bmesh.new(), bmesh.new(), bmesh.new()
for a, b in (((XE - 0.05, YE - 0.05), (AR.x - 0.16, YE + 0.05)), ((XE - 0.05, YE - 0.05), (XE + 0.05, 0.75))):
    caixa_de(bm, (a[0], a[1], Z0), (b[0], b[1], Z0 + 0.006))
    for s in (0, 1):                                                      # abas laterais
        if b[0] - a[0] > b[1] - a[1]:
            y = a[1] if s == 0 else b[1] - 0.006
            caixa_de(bm, (a[0], y, Z0), (b[0], y + 0.006, Z0 + 0.045))
        else:
            x = a[0] if s == 0 else b[0] - 0.006
            caixa_de(bm, (x, a[1], Z0), (x + 0.006, b[1], Z0 + 0.045))
obj('eletrocalha', bm, 'aco')


def feixe(bc, ba, pts, n=3, r=0.008, passo=4):
    for i in range(n):
        e1, _ = base_perp(pts[-1] - pts[0])
        off = Vector(((i - (n - 1) / 2) * r * 2.2, 0, 0)) if abs((pts[-1] - pts[0]).x) < 0.5 else Vector((0, (i - (n - 1) / 2) * r * 2.2, 0))
        mangueira(bc, [p + off for p in pts], r)
    for j in range(passo, len(pts) - 1, passo):
        u = (pts[j + 1] - pts[j - 1]).normalized()
        tubo(ba, pts[j] - u * 0.012, pts[j] + u * 0.012, r * (n + 1.2), 12)


ZC = Z0 + 0.02
feixe(bc, ba, [Vector((x, YE, ZC)) for x in (AR.x - 0.16, 0.8, 0.4, 0.0, XE)], 4, passo=2)
feixe(bc, ba, [Vector((XE, y, ZC)) for y in (YE, -0.6, 0.0, 0.6)], 3, passo=1)
feixe(bc, ba, bezier((AR.x - 0.16, YE, ZC), (AR.x - 0.12, YE, 0.3), (AR.x - 0.14, AR.y + 0.13, 0.3), (AR.x - 0.12, AR.y + 0.12, 0.3), 6), 4)
for RY in REATORES:                                                       # do piso até o sensor da camisa
    feixe(bc, ba, bezier((XE, RY, ZC), (XE, RY, 0.7), (RX + R_C + 0.12, RY, 1.0), (RX + R_C + 0.08, RY, 1.03), 10), 2)
feixe(bc, ba, bezier((XE, 0.0, ZC), (-0.3, 0.0, ZC), (-0.6, 0.1, ZC), (-0.68, 0.0, PB.z + 0.16), 10), 2)   # motor da bomba
suavizar(obj('cabos', bc, 'borracha'))
suavizar(obj('cabos_abracadeiras', ba, 'aco'))

# ------------------------------------------------------------------ objetos de processo acumulados
suavizar(obj('canos_processo', bm_proc, 'processo'))
suavizar(obj('canos_vapor', bm_vap, 'aco'))
suavizar(obj('canos_respiro', bm_resp, 'oxido'))
obj('flanges', bm_bf, 'ferro')
obj('flanges_parafusos', bm_bp, 'aco')
suavizar(obj('ferragens', bm_fer, 'ferro'))
suavizar(obj('atuadores', bm_atu, 'amarelo'))
obj('cromados', bm_cr, 'cromo')
obj('mostradores2', bm_face, 'mostrador')

# ------------------------------------------------------------------ sujeira: seiva, óleo, crosta, fuligem
bm = bmesh.new()
for c, r in (((-1.3, 0.05), 0.09), ((-1.15, -0.12), 0.06), ((-0.95, 0.2), 0.05), ((-0.55, 0.62), 0.12),
             ((-0.4, 0.8), 0.06), ((-0.6, -0.55), 0.07), ((-0.85, 1.25), 0.05), ((-1.42, -0.03), 0.04)):
    mancha(bm, c, r, Z0 + 0.0015)
for k in range(12):                                                       # respingos
    mancha(bm, (random.uniform(-1.35, -0.3), random.uniform(-0.6, 0.9)), random.uniform(0.01, 0.025), Z0 + 0.0016)
for RY in REATORES:                                                       # escorridos de seiva na camisa (da flange de alimentação)
    for k in range(4):
        a = math.radians(random.uniform(150, 210))
        d = Vector((math.cos(a), math.sin(a), 0))
        z1 = random.uniform(1.25, Z_C1)
        caixa(bm, Vector((RX, RY, 0)) + d * (R_C + 0.002) + Vector((0, 0, z1 - 0.15)),
              (0.004, random.uniform(0.012, 0.03), random.uniform(0.15, 0.4)), Matrix.Rotation(a, 3, 'Z'))
for k in range(3):                                                        # pingos na flange da sucção
    caixa(bm, Vector((-1.38 + k * 0.07, 0.0, Z_P - 0.06)) + Vector((0, 0.01 * k, 0)), (0.008, 0.008, 0.03))
obj('seiva_respingos', bm, 'seiva')
bm = bmesh.new()
for c, r in (((-0.7, 0.05), 0.1), ((-0.62, -0.1), 0.05), ((0.82, -0.62), 0.07), ((-0.3, 0.75), 0.05),
             ((1.25, 0.2), 0.05), ((0.4, 0.05), 0.06)):
    mancha(bm, c, r, Z0 + 0.0018)
obj('oleo', bm, 'oleo')
bm = bmesh.new()                                                          # crosta química nas flanges e em volta das válvulas
for c, rr in ((Vector((X_T0 + 0.12, Y_TC, Z_TC)), R_TC + 0.03), (Vector((X_T1 - 0.12, Y_TC, Z_TC)), R_TC + 0.03)):
    for k in range(14):
        a = random.uniform(PI * 1.1, PI * 1.9)
        pedra(bm, c + Vector((random.uniform(-0.02, 0.02), math.cos(a) * rr, math.sin(a) * rr)), random.uniform(0.008, 0.02), 0.7)
for k in range(16):                                                       # crosta na base da torre e no piso perto do trocador
    a = random.uniform(0, 2 * PI)
    pedra(bm, T + Vector((math.cos(a) * (R_T + 0.08), math.sin(a) * (R_T + 0.08), Z0 + 0.005)), random.uniform(0.01, 0.025), 0.35)
for c, r in (((0.3, -0.62), 0.07), ((0.85, -1.0), 0.06), ((0.55, 0.0), 0.05)):
    mancha(bm, c, r, Z0 + 0.0012)
for RY in REATORES:                                                       # crosta na flange do corpo dos reatores
    for k in range(10):
        a = random.uniform(0, 2 * PI)
        pedra(bm, Vector((RX + math.cos(a) * (R_R + 0.03), RY + math.sin(a) * (R_R + 0.03), Z_TOPO - 0.06)), random.uniform(0.008, 0.016), 0.6)
obj('crosta', bm, 'crosta')
bm = bmesh.new()                                                          # fuligem: escorridos abaixo da ponta do flare e no piso
for k in range(10):
    a = random.uniform(0, 2 * PI)
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, FL + d * 0.057 + Vector((0, 0, 2.75 + random.uniform(0, 0.15))), (0.003, random.uniform(0.008, 0.02), random.uniform(0.1, 0.3)),
          Matrix.Rotation(a, 3, 'Z'))
for k in range(5):
    mancha(bm, (FL.x + random.uniform(-0.25, 0.2), FL.y + random.uniform(-0.25, 0.2)), random.uniform(0.04, 0.09), Z0 + 0.0014)
obj('fuligem_flare', bm, 'fuligem')

# ------------------------------------------------------------------ vapores e fumaça
def bolhas(n, mat):
    lista = []
    for _ in range(n):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        lista.append(obj('vapor', bm, mat))
    return lista


vap_sil = [bolhas(4, 'vapor_alto') for _ in vapor_sil]
vap_purg = [bolhas(3, 'vapor_baixo') for _ in vapor_purg]
vap_troc = bolhas(3, 'vapor_troc')
fum_fl = bolhas(5, 'fumaca')

# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    return x * x * (3 - 2 * x)


bpy.context.view_layer.update()
mat_pisca = base3d.M['ambar_pisca'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
mat_liq = base3d.M['liquido'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
mat_vio = base3d.M['violeta'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    # anel de campo: 1 volta por laço; brilho pulsa
    anel.rotation_euler = (0.035 * math.sin(2 * PI * fr), 0.035 * math.cos(2 * PI * fr), 2 * PI * fr)   # gira e bamboleia
    anel.location = T + Vector((0, 0, Z_AN + 0.025 * math.sin(2 * PI * 2 * fr)))                     # flutua
    anel.keyframe_insert('rotation_euler', frame=q)
    anel.keyframe_insert('location', frame=q)
    mat_vio.default_value = 5.0 + 1.5 * math.sin(2 * PI * 2 * fr)
    mat_vio.keyframe_insert('default_value', frame=q)
    luz_anel.energy = 3 + 1 * math.sin(2 * PI * 2 * fr)
    luz_anel.keyframe_insert('energy', frame=q)
    # agitadores e acoplamento da bomba
    for k, ag in enumerate(agitadores):
        ag.rotation_euler = (0, 0, 2 * PI * 8 * fr * (1 if k == 0 else -1))
        ag.keyframe_insert('rotation_euler', frame=q)
    acop.rotation_euler = (2 * PI * 16 * fr, 0, 0)
    acop.keyframe_insert('rotation_euler', frame=q)
    # robô de inspeção: sobe, para no meio (inspeciona), desce
    if fr < 0.4:
        zr = 0.8 + 1.6 * suave(fr / 0.4)
    elif fr < 0.55:
        zr = 2.4
    else:
        zr = 2.4 - 1.6 * suave((fr - 0.55) / 0.45)
    robo.location = Vector((T.x, Y_TR, zr))
    robo.keyframe_insert('location', frame=q)
    # luzes que piscam
    mat_pisca.default_value = 10.0 if (fr * 8) % 1.0 < 0.5 else 0.5
    mat_pisca.keyframe_insert('default_value', frame=q)
    # líquido dos pratos borbulhando e nível subindo/descendo
    mat_liq.default_value = 2.5 + 0.8 * math.sin(2 * PI * 6 * fr) * math.sin(2 * PI * 3 * fr + 1)
    mat_liq.keyframe_insert('default_value', frame=q)
    nivel.scale = (1, 1, 0.55 + 0.12 * math.sin(2 * PI * fr) + 0.015 * math.sin(2 * PI * 9 * fr))
    nivel.keyframe_insert('scale', frame=q)
    # ponteiros dos manômetros tremendo
    for e, n, f0, base in GAUGES:
        ang = -2.2 + 4.4 * base + 0.06 * math.sin(2 * PI * 5 * fr + f0) + 0.03 * math.sin(2 * PI * 13 * fr + f0)
        e.rotation_quaternion = n.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), ang)
        e.keyframe_insert('rotation_quaternion', frame=q)
    # chama do flare tremulando; piloto sempre aceso
    for k, (o, esc, alt) in enumerate(chama):
        tr = 1 + 0.18 * math.sin(2 * PI * 7 * fr + k) + 0.1 * math.sin(2 * PI * 11 * fr + 2 * k)
        o.scale = (esc * (1 + 0.1 * math.sin(2 * PI * 9 * fr)), esc, alt * tr)
        o.rotation_euler = (0.08 * math.sin(2 * PI * 3 * fr), 0.12 + 0.05 * math.sin(2 * PI * 5 * fr), fr * 12)
        for c in ('scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
    luz_fl.energy = 120 * (1 + 0.25 * math.sin(2 * PI * 7 * fr) * math.sin(2 * PI * 3 * fr))
    luz_fl.keyframe_insert('energy', frame=q)
    for k, o in enumerate(fum_fl):                                        # fuligem que escapa da chama
        u = (k / len(fum_fl) + fr * 2) % 1.0
        o.location = FL + Vector((0.35 * u, 0.15 * u, Z_FL + 0.35 + 1.0 * u))
        o.scale = [0.05 + 0.22 * u] * 3
        o.rotation_euler = (k, u * 2, k * 0.7)
        for c in ('location', 'scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
    # vapor: silenciadores das camisas (contínuo), purgadores (golfadas), trocador
    for i, base_v in enumerate(vapor_sil):
        for k, o in enumerate(vap_sil[i]):
            u = (k / 4 + fr * 2 + i * 0.13) % 1.0
            o.location = base_v + Vector((0.25 * u * u, 0.1 * u, 0.9 * u + 0.05))
            o.scale = [0.05 + 0.2 * u] * 3
            o.rotation_euler = (k, u, i)
            for c in ('location', 'scale', 'rotation_euler'):
                o.keyframe_insert(c, frame=q)
    for i, (p, d) in enumerate(vapor_purg):
        golfada = 0.35 + 0.65 * max(0.0, math.sin(2 * PI * (fr * 2 + i * 0.5))) ** 2
        for k, o in enumerate(vap_purg[i]):
            u = (k / 3 + fr * 3) % 1.0
            o.location = p + d * (0.12 * u) + Vector((0, 0, 0.45 * u))
            o.scale = [max(0.01, (0.025 + 0.12 * u) * golfada)] * 3
            for c in ('location', 'scale'):
                o.keyframe_insert(c, frame=q)
    for k, o in enumerate(vap_troc):
        u = (k / 3 + fr * 2) % 1.0
        o.location = Vector((0.7 + 0.1 * u, Y_TC - 0.05 * u, 0.98 + 0.6 * u))
        o.scale = [0.03 + 0.13 * u] * 3
        for c in ('location', 'scale'):
            o.keyframe_insert(c, frame=q)
    # células saindo pela bica norte: 3 por laço, escondidas dentro do encapsulador
    for k, e in enumerate(CELULAS):
        u = (k / 3 + fr) % 1.0
        p = B0 + (B1 - B0) * (u * 1.25 - 0.2)
        e.location = p + Vector((0, 0, 0.06))
        e.rotation_euler = (math.atan2(B1.z - B0.z, B1.y - B0.y), 0, 0)
        visivel = 0.02 < u * 1.25 - 0.2 < 0.95
        e.scale = [1.0 if visivel else 0.001] * 3
        for c in ('location', 'rotation_euler', 'scale'):
            e.keyframe_insert(c, frame=q)
for o in list(sc.objects) + [luz_anel, luz_fl] + [base3d.M[m] for m in ('ambar_pisca', 'liquido', 'violeta')]:
    ad = getattr(o, 'animation_data', None) if not hasattr(o, 'node_tree') else getattr(o.node_tree, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (16, 16, 1.0))
obj('chao', bm, 'chao')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.6
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
sc.view_settings.exposure = -0.4
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 1.45)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1100, 1300
    sc.frame_set(int(QUADROS * 0.3) + 1)
    for i, (ang, alt) in enumerate(((300, 2.9), (210, 3.1), (120, 3.2), (30, 2.8))):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 7.6, math.sin(a) * 7.6, alt)), ALVO, 36)
        sc.render.filepath = os.path.join(AQUI, 'refinador_%d.png' % i)
        bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1000
    mirar((-2.6, 2.2, 2.3), (-0.6, 0.45, 1.0), 30)                        # de perto: reator norte, bomba, rosca e bica
    sc.render.filepath = os.path.join(AQUI, 'refinador_perto.png')
    bpy.ops.render.render(write_still=True)
print('REFINADOR ok')
