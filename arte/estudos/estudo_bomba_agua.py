"""Estudo isolado (fora do jogo): bomba d'água da IA, 2×2 tiles, encostada na margem de um rio turvo ao sul.
Regra: tira 40 de água/s; água suja na tomada rende menos (sonda de turbidez da IA no poço).
Estação de captação: poço de sucção aberto no cais de concreto, ligado ao rio por uma janela submersa com grade de
barras (galhos, folhas, borra, espuma e sucata presos do lado de fora, limo pendurado). Duas vigas I sobre o poço
seguram a placa-base da bomba vertical: coluna, carcaça de dois estágios com flanges e nervuras, sino de sucção e cesto
de crivo descendo na água, que redemoinha em volta da coluna (funil, espuma girando, folhas presas no giro).
Acima da placa: visor de vidro em que a água sobe em espiral (rosca helicoidal no eixo) puxada por três anéis de campo
violeta com bobinas de cobre e emissores de cristal; cabeçote de descarga com gaxeta pingando, lanterna aberta com
acoplamento e eixo à vista, motor vertical com aletas e tampa trocada. Recalque: bocal → válvula de retenção (contrapeso
que balança com o fluxo) → curva descendo → cano até a borda norte, flange igual à dos canos aprovados
(FLUIDO_SAI_N1: x = +0,5, y = +1, eixo a 0,34 m). Quadro da IA selado com olho violeta, antena, eletrocalha, poste de
cabos, conduíte do motor. Limo, escorridos de água e de ferrugem, respingos e poças.
Uso: blender -b --python estudo_bomba_agua.py -- foto [0|1|perto]  |  -- teste x y z ax ay az lente fr"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
random.seed(31)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS
no = mats.no


# ------------------------------------------------------------------ utilidades de geometria
def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
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
    fs = []
    for i in range(lados):
        j = (i + 1) % lados
        fs.append(bm.faces.new((an[0][i], an[0][j], an[1][j], an[1][i])))
        fs.append(bm.faces.new((an[2][i], an[3][i], an[3][j], an[2][j])))
        fs.append(bm.faces.new((an[1][i], an[1][j], an[3][j], an[3][i])))
        fs.append(bm.faces.new((an[0][i], an[2][i], an[2][j], an[0][j])))
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def esfera(bm, c, r, seg=20):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def varrer(bm, pts, raios, lados=32):
    """Tubo varrido ao longo de pts (transporte paralelo): curvas redondas de verdade."""
    limpos = []
    for p in pts:                                                          # pontos repetidos dão NaN e somem o objeto
        p = Vector(p)
        if not limpos or (p - limpos[-1]).length > 1e-5:
            limpos.append(p)
    pts = limpos
    n = len(pts)
    if not isinstance(raios, (list, tuple)):
        raios = [raios] * n
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
        aneis.append([bm.verts.new(pts[i] + (e1 * math.cos(a) + e2 * math.sin(a)) * raios[i])
                      for a in (k * 2 * PI / lados for k in range(lados))])
    for A, B_ in zip(aneis, aneis[1:]):
        for j in range(lados):
            bm.faces.new((A[j], A[(j + 1) % lados], B_[(j + 1) % lados], B_[j]))


def caminho(pts, Rc, passo=12):
    """Linha de cano com cotovelos de raio Rc (cantos de 90°)."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = (b - a).normalized(), (c - b).normalized()
        p0 = b - d1 * Rc
        cen = p0 + d2 * Rc
        for k in range(passo + 1):
            t = k / passo * PI / 2
            out.append(cen - d2 * Rc * math.cos(t) + d1 * Rc * math.sin(t))
    out.append(pts[-1])
    return out


def base_lat(u):
    u = Vector(u).normalized()
    s = u.cross(Z)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    return s, s.cross(u).normalized() if abs(u.z) > 0.9 else Z.copy()


def chapa_arco(bm, c, u, r_in, esp, larg, a0, a1, n=14):
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


def rot_de(u):
    u = Vector(u).normalized()
    s, up = base_lat(u)
    return Matrix((s, u, up)).transposed()


def folha(bm, c, tam, normal, ang=0.0, curva=0.25):
    """Folha: elipse pontuda levemente dobrada na nervura, deitada no plano de 'normal'."""
    c, n = Vector(c), Vector(normal).normalized()
    u, v, _ = base_de(n)
    ca, sa = math.cos(ang), math.sin(ang)
    u, v = u * ca + v * sa, -u * sa + v * ca
    vs = []
    N = 8
    for i in range(N + 1):
        t = i / N
        L = (t - 0.5) * tam
        w = math.sin(PI * t) ** 0.8 * tam * 0.28
        dob = curva * w
        vs.append((bm.verts.new(c + u * L + v * w + n * dob), bm.verts.new(c + u * L), bm.verts.new(c + u * L - v * w + n * dob)))
    for A, B_ in zip(vs, vs[1:]):
        for j in (0, 1):
            try:
                bm.faces.new((A[j], A[j + 1], B_[j + 1], B_[j]))
            except ValueError:
                pass


# baldes de malha por material (um objeto por material no fim)
BK = {}


def B(mat, liso=False):
    if (mat, liso) not in BK:
        BK[(mat, liso)] = bmesh.new()
    return BK[(mat, liso)]


def fechar():
    for (mat, liso), bm in BK.items():
        o = obj('%s%s' % (mat, '_liso' if liso else ''), bm, mat)
        if liso:
            suavizar(o)
    BK.clear()


# ------------------------------------------------------------------ materiais
def emissivo(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat():
    m = bpy.data.materials.new('Vidro')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.92, 0.92, 0.86, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Coat Weight'].default_value = 0.8
    b.inputs['Coat Roughness'].default_value = 0.03
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 20.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    alt = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.4, 'To Min': 0.0, 'To Max': 0.7})
    nt.links.new(sep.outputs['Z'], alt.inputs['Value'])           # encardido de barro embaixo
    enc = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(alt.outputs['Result'], enc.inputs[0])
    nt.links.new(ru.outputs['Fac'], enc.inputs[1])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.95, 0.96, 0.95, 1)
    cor.inputs[7].default_value = (0.33, 0.25, 0.12, 1)
    nt.links.new(enc.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.03, 'To Max': 0.55})
    nt.links.new(enc.outputs['Value'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    return m


FASES = {}


def valor_fase(nt, chave):
    val = no(nt, 'ShaderNodeValue')
    val.name = chave
    FASES.setdefault(chave, []).append(val)
    return val


def agua_espiral_mat():
    """Água subindo no visor: faixas em hélice (mesmo passo da rosca) que correm para cima, espuma e crista violeta
    onde o campo puxa. Coordenada do objeto (origem no eixo, meio do visor)."""
    m = bpy.data.materials.new('Água em espiral')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['IOR'].default_value = 1.0
    b.inputs['Transmission Weight'].default_value = 0.55
    b.inputs['Emission Color'].default_value = (0.55, 0.22, 1.0, 1)
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    th = no(nt, 'ShaderNodeMath', operation='ARCTAN2')
    nt.links.new(sep.outputs['Y'], th.inputs[0])
    nt.links.new(sep.outputs['X'], th.inputs[1])
    kz = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    kz.inputs[1].default_value = -K_HELICE
    nt.links.new(sep.outputs['Z'], kz.inputs[0])
    s1 = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(th.outputs['Value'], s1.inputs[0])
    nt.links.new(kz.outputs['Value'], s1.inputs[1])
    val = valor_fase(nt, 'visor')
    s2 = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(s1.outputs['Value'], s2.inputs[0])
    nt.links.new(val.outputs[0], s2.inputs[1])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    s3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    s3.inputs[1].default_value = 1.6
    nt.links.new(ru.outputs['Fac'], s3.inputs[0])
    nt.links.new(s2.outputs['Value'], s3.inputs[2])
    sen = no(nt, 'ShaderNodeMath', operation='SINE')
    nt.links.new(s3.outputs['Value'], sen.inputs[0])
    faixa = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.2, 'From Max': 0.9})
    nt.links.new(sen.outputs['Value'], faixa.inputs['Value'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.16, 0.13, 0.06, 1)
    cor.inputs[7].default_value = (0.62, 0.6, 0.5, 1)
    nt.links.new(faixa.outputs['Result'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    tr = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.6, 'To Max': 0.1})
    nt.links.new(faixa.outputs['Result'], tr.inputs['Value'])
    nt.links.new(tr.outputs['Result'], b.inputs['Transmission Weight'])
    crista = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.82, 'From Max': 1.0, 'To Min': 0.0, 'To Max': 2.2})
    nt.links.new(sen.outputs['Value'], crista.inputs['Value'])
    nt.links.new(crista.outputs['Result'], b.inputs['Emission Strength'])
    return m


def redemoinho_mat():
    """Água do poço: turva, com braços de espuma em espiral que giram e afundam para a coluna (coord. do objeto,
    origem no eixo da bomba)."""
    m = bpy.data.materials.new('Redemoinho')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['IOR'].default_value = 1.33
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    cb = no(nt, 'ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], cb.inputs['X'])
    nt.links.new(sep.outputs['Y'], cb.inputs['Y'])
    r = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(cb.outputs[0], r.inputs[0])
    th = no(nt, 'ShaderNodeMath', operation='ARCTAN2')
    nt.links.new(sep.outputs['Y'], th.inputs[0])
    nt.links.new(sep.outputs['X'], th.inputs[1])
    ln = no(nt, 'ShaderNodeMath', operation='LOGARITHM')
    ln.inputs[1].default_value = math.e
    nt.links.new(r.outputs['Value'], ln.inputs[0])
    a1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    a1.inputs[1].default_value = 3.0                                     # três braços
    nt.links.new(th.outputs['Value'], a1.inputs[0])
    a2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    a2.inputs[1].default_value = 7.0                                     # enrolamento
    nt.links.new(ln.outputs['Value'], a2.inputs[0])
    nt.links.new(a1.outputs['Value'], a2.inputs[2])
    val = valor_fase(nt, 'poco')
    a3 = no(nt, 'ShaderNodeMath', operation='SUBTRACT')
    nt.links.new(a2.outputs['Value'], a3.inputs[0])
    nt.links.new(val.outputs[0], a3.inputs[1])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    a4 = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    a4.inputs[1].default_value = 0.8
    nt.links.new(ru.outputs['Fac'], a4.inputs[0])
    nt.links.new(a3.outputs['Value'], a4.inputs[2])
    sen = no(nt, 'ShaderNodeMath', operation='SINE')
    nt.links.new(a4.outputs['Value'], sen.inputs[0])
    esp = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.38, 'From Max': 0.82})
    nt.links.new(sen.outputs['Value'], esp.inputs['Value'])
    fade = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.62, 'From Max': 0.2})
    nt.links.new(r.outputs['Value'], fade.inputs['Value'])
    f = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(esp.outputs['Result'], f.inputs[0])
    nt.links.new(fade.outputs['Result'], f.inputs[1])
    gr = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.5, 'Detail': 6.0, 'Distortion': 1.2})
    nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
    base = no(nt, 'ShaderNodeMix', data_type='RGBA')
    base.inputs[6].default_value = (0.07, 0.05, 0.022, 1)
    base.inputs[7].default_value = (0.16, 0.115, 0.05, 1)
    nt.links.new(gr.outputs['Fac'], base.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[7].default_value = (0.62, 0.57, 0.46, 1)
    nt.links.new(base.outputs[2], cor.inputs[6])
    nt.links.new(f.outputs['Value'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.04, 'To Max': 0.65})
    nt.links.new(f.outputs['Value'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    sulco = no(nt, 'ShaderNodeMath', operation='MULTIPLY')                # sulcos do giro (relevo)
    nt.links.new(sen.outputs['Value'], sulco.inputs[0])
    nt.links.new(fade.outputs['Result'], sulco.inputs[1])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.35})
    bump.inputs['Distance'].default_value = 0.01
    nt.links.new(sulco.outputs['Value'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def rio_mat():
    m = bpy.data.materials.new('Rio')
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['IOR'].default_value = 1.33
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.9, 'Detail': 6.0, 'Distortion': 1.5})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor.inputs[6].default_value = (0.075, 0.055, 0.025, 1)
    cor.inputs[7].default_value = (0.17, 0.12, 0.055, 1)
    nt.links.new(ru.outputs['Fac'], cor.inputs[0])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    onda = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], onda.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.12})
    nt.links.new(onda.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def terra_mat():
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
    cor.inputs[7].default_value = (0.055, 0.04, 0.025, 1)
    nt.links.new(molh.outputs['Result'], cor.inputs[0])
    nt.links.new(seca.outputs[2], cor.inputs[6])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.35
    nt.links.new(cor.outputs[2], var.inputs[6])
    nt.links.new(fino.outputs['Color'], var.inputs[7])
    nt.links.new(var.outputs[2], b.inputs['Base Color'])
    ro = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.95, 'To Max': 0.3})
    nt.links.new(molh.outputs['Result'], ro.inputs['Value'])
    nt.links.new(ro.outputs['Result'], b.inputs['Roughness'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.4})
    nt.links.new(fino.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def tinta_mat():
    """Estêncil gasto (números de série): branco encardido falhando em manchas."""
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


def escorrido_mat(nome, cor, rough, alfa=0.85):
    """Escorrido (água, ferrugem, limo): faixa que some em franjas irregulares (alfa por ruído esticado em z)."""
    m = mats.material(nome, cor, 0, rough, pintura=False, sujeira=0.0, desgaste=0.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = no(nt, 'ShaderNodeNewGeometry')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60.0, 60.0, 6.0)
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.0, 'Detail': 5.0})
    nt.links.new(mp.outputs['Vector'], ru.inputs['Vector'])
    a = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.5, 'To Min': 0.0, 'To Max': alfa})
    nt.links.new(ru.outputs['Fac'], a.inputs['Value'])
    nt.links.new(a.outputs['Result'], b.inputs['Alpha'])
    return m


def rustico(m, poeira=1.0, lama=1.0, fuligem=1.0, amassado=0.12, limo=1.0):
    """Camada de uso: poeira no que olha para cima, lama respingada logo acima da laje, fuligem, amassados, e faixa de
    limo verde-escuro na linha d'água (tudo em coordenada de mundo)."""
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
    baixo = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.1, 'From Max': 0.24, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sp.outputs['Z'], baixo.inputs['Value'])
    acima = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.07})
    nt.links.new(sp.outputs['Z'], acima.inputs['Value'])
    ba = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(baixo.outputs['Result'], ba.inputs[0])
    nt.links.new(acima.outputs['Result'], ba.inputs[1])
    lr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.6, 'To Min': 0.3, 'To Max': 1.0 * lama})
    nt.links.new(ru.outputs['Fac'], lr.inputs['Value'])
    fl = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(ba.outputs['Value'], fl.inputs[0])
    nt.links.new(lr.outputs['Result'], fl.inputs[1])
    # limo: faixa de Z_RIO-0,25 a Z_RIO+0,12 (mais forte logo acima da água), recortada por ruído
    l1 = no(nt, 'ShaderNodeMapRange', **{'From Min': Z_RIO + 0.16, 'From Max': Z_RIO + 0.02})
    nt.links.new(sp.outputs['Z'], l1.inputs['Value'])
    l2 = no(nt, 'ShaderNodeMapRange', **{'From Min': Z_RIO - 0.35, 'From Max': Z_RIO - 0.1})
    nt.links.new(sp.outputs['Z'], l2.inputs['Value'])
    l3 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(l1.outputs['Result'], l3.inputs[0])
    nt.links.new(l2.outputs['Result'], l3.inputs[1])
    lv = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.55, 'To Min': 0.35, 'To Max': 0.95 * limo})
    nt.links.new(gr.outputs['Fac'], lv.inputs['Value'])
    flm = no(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True)
    nt.links.new(l3.outputs['Value'], flm.inputs[0])
    nt.links.new(lv.outputs['Result'], flm.inputs[1])
    fu = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 0.75 * fuligem})
    nt.links.new(gr.outputs['Fac'], fu.inputs['Value'])
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    c1.inputs[7].default_value = (0.08, 0.07, 0.065, 1)
    nt.links.new(fu.outputs['Result'], c1.inputs[0])
    if cor is not None:
        nt.links.new(cor, c1.inputs[6])
    else:
        c1.inputs[6].default_value = b.inputs['Base Color'].default_value
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c2.inputs[7].default_value = (0.36, 0.31, 0.24, 1)
    nt.links.new(fp.outputs['Value'], c2.inputs[0])
    nt.links.new(c1.outputs[2], c2.inputs[6])
    c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c3.inputs[7].default_value = (0.1, 0.07, 0.04, 1)
    nt.links.new(fl.outputs['Value'], c3.inputs[0])
    nt.links.new(c2.outputs[2], c3.inputs[6])
    c4 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c4.inputs[7].default_value = (0.035, 0.05, 0.018, 1)
    nt.links.new(flm.outputs['Value'], c4.inputs[0])
    nt.links.new(c3.outputs[2], c4.inputs[6])
    nt.links.new(c4.outputs[2], b.inputs['Base Color'])
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
    rlm = no(nt, 'ShaderNodeMix', data_type='FLOAT')                  # limo é molhado e brilha
    rlm.inputs[3].default_value = 0.18
    nt.links.new(flm.outputs['Value'], rlm.inputs[0])
    nt.links.new(rmix.outputs[0], rlm.inputs[2])
    nt.links.new(rlm.outputs[0], b.inputs['Roughness'])
    soma2 = no(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    nt.links.new(soma.outputs['Value'], soma2.inputs[0])
    nt.links.new(flm.outputs['Value'], soma2.inputs[1])
    met = next((l for l in nt.links if l.to_socket == b.inputs['Metallic']), None)
    if met or b.inputs['Metallic'].default_value > 0:
        mm = no(nt, 'ShaderNodeMix', data_type='FLOAT')
        nt.links.new(soma2.outputs['Value'], mm.inputs[0])
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


Z_RIO = -0.35                # nível da água
P_HELICE = 0.135             # passo da rosca do visor (m por volta)
K_HELICE = 2 * PI / P_HELICE
VIOLETA = (0.55, 0.2, 1.0)

base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.0, sujeira=0.9, ferrugem=0.5),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.7, sujeira=0.8, ferrugem=0.3),
    'cano': mats.material('Cano de água', (0.13, 0.17, 0.19), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.8),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'bronze': mats.material('Bronze', (0.62, 0.40, 0.18), 1.0, 0.3, pintura=False, sujeira=0.5, ferrugem=0.2),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'oxido': mats.material('Primer vermelho', (0.34, 0.08, 0.045), 0, 0.55, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'cinza': mats.material('Peça trocada cinza', (0.33, 0.34, 0.33), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.5),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'mostrador': mats.material('Mostrador', (0.8, 0.78, 0.72), 0, 0.3, pintura=False, sujeira=0.5, desgaste=0.0),
    'preto': mats.material('Preto', (0.01, 0.01, 0.01), 0, 0.4, pintura=False, sujeira=0.0, desgaste=0.0),
    'fio_v': mats.material('Fio vermelho', (0.5, 0.03, 0.02), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'fio_a': mats.material('Fio azul', (0.03, 0.08, 0.4), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'fio_m': mats.material('Fio amarelo', (0.55, 0.42, 0.03), 0, 0.4, pintura=False, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': mats.material('Lama', (0.13, 0.085, 0.04), 0, 0.22, pintura=False, sujeira=0.4, desgaste=0.0),
    'lama_seca': mats.material('Lama seca', (0.2, 0.15, 0.09), 0, 0.9, pintura=False, sujeira=0.3, desgaste=0.0),
    'alga': mats.material('Alga', (0.05, 0.075, 0.025), 0, 0.35, pintura=False, sujeira=0.5, desgaste=0.0),
    'galho': mats.material('Galho', (0.11, 0.08, 0.05), 0, 0.85, pintura=False, sujeira=0.5, desgaste=0.0),
    'folha_seca': mats.material('Folha seca', (0.26, 0.13, 0.04), 0, 0.6, pintura=False, sujeira=0.4, desgaste=0.0),
    'folha_verde': mats.material('Folha verde', (0.09, 0.15, 0.03), 0, 0.45, pintura=False, sujeira=0.4, desgaste=0.0),
    'folha_amarela': mats.material('Folha amarela', (0.42, 0.3, 0.05), 0, 0.55, pintura=False, sujeira=0.4, desgaste=0.0),
    'escuma': mats.material('Escuma', (0.15, 0.12, 0.07), 0, 0.6, pintura=False, sujeira=0.2, desgaste=0.0),
    'espuma': mats.material('Espuma', (0.27, 0.25, 0.19), 0, 0.85, pintura=False, sujeira=0.1, desgaste=0.0),
    'pedra': mats.material('Pedra', (0.15, 0.145, 0.13), 0, 0.85, pintura=False, sujeira=0.7, desgaste=0.0),
    'palha': mats.material('Palha', (0.28, 0.22, 0.11), 0, 0.8, pintura=False, sujeira=0.5, desgaste=0.0),
    'poca': mats.material('Poça', (0.02, 0.022, 0.02), 0, 0.03, pintura=False, sujeira=0.0, desgaste=0.0),
    'molhado': escorrido_mat('Escorrido de água', (0.1, 0.095, 0.085), 0.12, 0.7),
    'ferrugem_esc': escorrido_mat('Escorrido de ferrugem', (0.3, 0.1, 0.03), 0.8, 0.9),
    'limo_esc': escorrido_mat('Escorrido de limo', (0.03, 0.055, 0.015), 0.25, 0.95),
    'tinta': tinta_mat(),
    'vidro': vidro_mat(),
    'agua_visor': agua_espiral_mat(),
    'agua_poco': redemoinho_mat(),
    'rio': rio_mat(),
    'terra': terra_mat(),
    'gota': mats.material('Gota', (0.6, 0.65, 0.62), 0, 0.02, pintura=False, sujeira=0.0, desgaste=0.0),
    'cristal': emissivo('Cristal', (0.5, 0.15, 1.0), 4.0, (0.2, 0.05, 0.5)),
    'anel0': emissivo('Anel de campo 0', VIOLETA, 6.0),
    'anel1': emissivo('Anel de campo 1', VIOLETA, 6.0),
    'anel2': emissivo('Anel de campo 2', VIOLETA, 6.0),
    'olho': emissivo('Olho da IA', VIOLETA, 5.0),
    'farol': emissivo('Farol', (1.0, 0.35, 0.03), 12.0),
    'listras': base3d.listras_mat(),
    'lampada': base3d.lampada_mat(),
})
gt = base3d.M['gota'].node_tree.nodes
for n in gt:
    if n.type == 'BSDF_PRINCIPLED':
        n.inputs['Transmission Weight'].default_value = 1.0
        n.inputs['IOR'].default_value = 1.33
for chave, kw in (('amarelo', {}), ('grafite', {}), ('cano', {}), ('ferro', dict(amassado=0.1)),
                  ('aco', dict(amassado=0.0, fuligem=0.5)), ('oxido', {}), ('cinza', {}),
                  ('concreto', dict(amassado=0.0, fuligem=0.6)), ('borracha', dict(amassado=0.0, fuligem=0.0)),
                  ('cromo', dict(amassado=0.0, poeira=0.4, fuligem=0.3)), ('bronze', dict(amassado=0.0, poeira=0.3))):
    rustico(base3d.M[chave], **kw)

# ------------------------------------------------------------------ medidas
Z_LAJE = 0.08
WX0, WX1 = -0.8, 0.32                      # poço de sucção (largura em x)
WYN = -0.35                                # parede norte do poço
YB = -1.35                                 # frente da baía de tomada (grade), entre dois pilares que entram no rio
YC0, YC1 = -1.06, -0.98                    # muro do cais
PC = Vector((-0.25, -0.8, 0.0))            # eixo da bomba vertical


def P(z, dx=0.0, dy=0.0):
    return Vector((PC.x + dx, PC.y + dy, z))


YV = (PC.y - 0.22, PC.y + 0.22)            # vigas I (correm em x, de pilar a pilar)
Z_VIGA = 0.22
Z_PLACA = 0.25
Z_D = 0.99                                 # eixo do bocal de recalque
VX = 0.12                                  # válvula de retenção
X_DESCE = 0.5
Z_CANO = 0.34                              # eixo do cano na borda (igual aos canos)
R_REC = 0.10

# ------------------------------------------------------------------ laje com o poço, cais, pilares e grade
cz = B('concreto')
caixa_de(cz, (-0.98, WYN, 0), (0.98, 0.98, Z_LAJE))
caixa_de(cz, (-0.98, YC1, 0), (WX0 - 0.08, WYN, Z_LAJE))
caixa_de(cz, (WX1 + 0.08, YC1, 0), (0.98, WYN, Z_LAJE))
for x0, x1 in ((WX0 - 0.08, WX0), (WX1, WX1 + 0.08)):                     # paredes laterais = pilares até o rio
    caixa_de(cz, (x0, YB, -0.9), (x1, WYN, Z_LAJE))
caixa_de(cz, (WX0 - 0.08, WYN, -0.9), (WX1 + 0.08, WYN + 0.08, 0.0))       # parede norte
caixa_de(cz, (WX0, YB, -0.95), (WX1, WYN, -0.88))                          # fundo
caixa_de(cz, (-1.0, YC0, -0.9), (WX0 - 0.08, YC1, Z_LAJE))                 # cais dos dois lados
caixa_de(cz, (WX1 + 0.08, YC0, -0.9), (1.0, YC1, Z_LAJE))
for x0, x1 in ((WX0 - 0.13, WX0 - 0.08), (WX1 + 0.08, WX1 + 0.13)):        # testa dos pilares (quebra-corrente)
    caixa_de(cz, (x0, YB, -0.9), (x1, YB + 0.12, Z_LAJE - 0.02))
for sx in (-1, 1):                                                         # alas de contenção
    caixa_de(cz, (sx * 1.0 if sx > 0 else -1.09, -1.42, -0.9), (1.09 if sx > 0 else -1.0, YC1, 0.06))
for x in (-0.9, 0.62, 0.85):                                               # contrafortes
    caixa_de(cz, (x - 0.05, -1.11, -0.9), (x + 0.05, YC0, 0.0))
for k in range(30):                                                        # concreto lascado nas quinas
    x = random.uniform(-0.98, 0.98)
    if WX0 - 0.1 < x < WX1 + 0.1:
        continue
    pedra(B('concreto'), (x, YC0 + 0.005, Z_LAJE - 0.005), random.uniform(0.01, 0.025), 0.6)
for k in range(10):
    xp = random.choice((WX0 - 0.08, WX0, WX1, WX1 + 0.08))
    pedra(B('concreto'), (xp, random.uniform(YB, -0.4), Z_LAJE - 0.005), random.uniform(0.01, 0.02), 0.6)
for (a, b) in (((WX0 - 0.012, YC1, Z_LAJE - 0.012), (WX0 + 0.002, WYN + 0.012, Z_LAJE + 0.002)),
               ((WX1 - 0.002, YC1, Z_LAJE - 0.012), (WX1 + 0.012, WYN + 0.012, Z_LAJE + 0.002)),
               ((WX0 - 0.012, WYN - 0.002, Z_LAJE - 0.012), (WX1 + 0.012, WYN + 0.012, Z_LAJE + 0.002))):
    caixa_de(B('aco'), a, b)                                               # cantoneira de borda do poço
lst = B('listras')
caixa_de(lst, (WX0 - 0.08, YB, Z_LAJE), (WX0 - 0.012, WYN + 0.06, Z_LAJE + 0.003))
caixa_de(lst, (WX1 + 0.012, YB, Z_LAJE), (WX1 + 0.08, WYN + 0.06, Z_LAJE + 0.003))
caixa_de(lst, (WX0 - 0.06, WYN + 0.012, Z_LAJE), (WX1 + 0.06, WYN + 0.06, Z_LAJE + 0.003))
caixa_de(lst, (-0.985, YC0 - 0.001, Z_LAJE), (WX0 - 0.08, YC0 + 0.035, Z_LAJE + 0.003))
caixa_de(lst, (WX1 + 0.08, YC0 - 0.001, Z_LAJE), (0.985, YC0 + 0.035, Z_LAJE + 0.003))

# grade de barras na frente da baía (entre as testas dos pilares), quadro amarelo e olhais para drone
YG = YB - 0.03
GX0, GX1 = WX0 - 0.03, WX1 + 0.03
for x in (GX0, GX1):                                                       # guias em U chumbadas nos pilares
    caixa_de(B('amarelo'), (x - 0.035, YG - 0.035, -0.88), (x + 0.035, YB, 0.14))
caixa_de(B('amarelo'), (GX0 - 0.035, YG - 0.035, 0.08), (GX1 + 0.035, YB, 0.14))   # travessa de cima
for x in (GX0 + 0.2, GX1 - 0.2):
    toro(B('ferro', True), Vector((x, YG - 0.01, 0.175)), 0.03, 0.009, Y, nR=16, nr=6)
    caixa_de(B('ferro'), (x - 0.03, YG - 0.025, 0.14), (x + 0.03, YG + 0.005, 0.152))
n = 34
for k in range(n + 1):                                                     # barras chatas
    x = GX0 + 0.04 + (GX1 - GX0 - 0.08) * k / n
    caixa_de(B('ferro'), (x - 0.006, YG - 0.025, -0.87), (x + 0.006, YG + 0.015, 0.08))
for z in (-0.62, -0.26, 0.0):                                              # tirantes horizontais
    caixa_de(B('ferro'), (GX0, YG - 0.035, z - 0.012), (GX1, YG - 0.022, z + 0.012))
for x in (GX0, GX1):                                                       # chumbadores das guias
    for z in (-0.1, 0.06):
        cil(B('aco'), Vector((x, YG - 0.04, z)), 0.012, 0.012, Y, lados=6)
caixa_de(B('oxido'), (GX0 + 0.35, YG - 0.04, -0.3), (GX0 + 0.47, YG - 0.035, -0.06))   # remendo de chapa na grade
for xx in (GX0 + 0.36, GX0 + 0.46):
    for zz in (-0.28, -0.08):
        cil(B('aco'), Vector((xx, YG - 0.042, zz)), 0.007, 0.006, Y, lados=6)

# lixo preso na grade: galhos, folhas (molhadas e secas acima d'água), borra, espuma, sucata, limo pendurado
for k in range(16):
    x = random.uniform(GX0, GX1)
    c = Vector((x, YG - 0.05, Z_RIO + random.uniform(-0.01, 0.03)))
    a = random.uniform(-0.35, 0.35)
    d = Vector((math.cos(a), random.uniform(-0.15, 0.15), math.sin(a) * 0.5)) * random.uniform(0.08, 0.26)
    tubo(B('galho', True), c - d, c + d, random.uniform(0.005, 0.013), 7)
for k in range(85):
    x = random.uniform(GX0 - 0.02, GX1 + 0.02)
    z = Z_RIO + random.uniform(-0.03, 0.07) if k < 68 else random.uniform(Z_RIO + 0.08, 0.06)
    mat = random.choice(('folha_seca', 'folha_seca', 'folha_verde', 'folha_amarela'))
    nrm = Vector((random.uniform(-0.4, 0.4), -1, random.uniform(-0.2, 0.9 if z < Z_RIO + 0.05 else 0.3)))
    folha(B(mat), (x, YG - 0.04 - random.uniform(0, 0.02), z), random.uniform(0.05, 0.11), nrm, random.uniform(0, PI))
for k in range(26):
    pedra(B('lama', True), (random.uniform(GX0, GX1), YG - 0.045, Z_RIO + random.uniform(-0.01, 0.04)),
          random.uniform(0.015, 0.04), 0.5)
for k in range(14):                                                        # escuma marrom encostada
    mancha(B('escuma'), (random.uniform(GX0, GX1), random.uniform(YG - 0.2, YG - 0.05)),
           random.uniform(0.02, 0.05), Z_RIO + 0.003)
for k in range(90):                                                        # bolhas de espuma suja em cachos
    c0 = Vector((random.uniform(GX0, GX1), YG - random.uniform(0.04, 0.14), Z_RIO + 0.002))
    pedra(B('espuma', True), c0, random.uniform(0.005, 0.014), 0.45)
sc_ = Vector((GX0 + 0.72, YG - 0.06, Z_RIO + 0.02))                       # sucata: chapa torta enferrujada
bm = B('oxido')
vs = []
for i in range(6):
    t = i / 5
    p = sc_ + Vector((t * 0.2 - 0.1, -0.02 * math.sin(t * PI) - 0.01, 0.05 * math.sin(t * 2.5)))
    vs.append((bm.verts.new(p - Vector((0, 0.003, 0.05))), bm.verts.new(p + Vector((0, 0.003, 0.06)))))
for A, B_ in zip(vs, vs[1:]):
    bm.faces.new((A[0], B_[0], B_[1], A[1]))
pts = bezier((GX0 + 0.2, YG - 0.05, Z_RIO + 0.03), (GX0 + 0.3, YG - 0.1, Z_RIO - 0.02),
             (GX0 + 0.4, YG - 0.04, Z_RIO + 0.06), (GX0 + 0.55, YG - 0.06, Z_RIO + 0.0), 10)
mangueira(B('borracha'), pts, 0.007)                                       # pedaço de cabo velho
for k in range(30):                                                        # fios de limo pendurados nas barras
    x = GX0 + 0.04 + (GX1 - GX0 - 0.08) * random.randint(0, n) / n
    z0 = Z_RIO + random.uniform(0.03, 0.12)
    pts = bezier((x, YG - 0.028, z0), (x + 0.01, YG - 0.04, z0 - 0.04), (x - 0.01, YG - 0.035, z0 - 0.08),
                 (x + random.uniform(-0.03, 0.03), YG - 0.045, Z_RIO - 0.01), 5)
    mangueira(B('alga', True), pts, random.uniform(0.003, 0.006))

# ------------------------------------------------------------------ vigas I, mesa da bomba e coluna mergulhada
XV0, XV1 = WX0 - 0.075, WX1 + 0.075
for yv in YV:
    caixa_de(B('amarelo'), (XV0, yv - 0.05, Z_LAJE + 0.008), (XV1, yv + 0.05, Z_LAJE + 0.022))   # mesa de baixo
    caixa_de(B('amarelo'), (XV0, yv - 0.05, Z_VIGA - 0.014), (XV1, yv + 0.05, Z_VIGA))           # mesa de cima
    caixa_de(B('amarelo'), (XV0, yv - 0.006, Z_LAJE + 0.022), (XV1, yv + 0.006, Z_VIGA - 0.014))  # alma
    for x in (WX0 + 0.08, WX0 + 0.3, WX1 - 0.25, WX1 - 0.06):              # enrijecedores
        for s in (-1, 1):
            caixa_de(B('amarelo'), (x - 0.006, yv + s * 0.006, Z_LAJE + 0.022), (x + 0.006, yv + s * 0.046, Z_VIGA - 0.014))
    for x0, x1 in ((WX0 - 0.08, WX0), (WX1, WX1 + 0.08)):                 # chapas de apoio chumbadas nos pilares
        caixa_de(B('ferro'), (x0, yv - 0.075, Z_LAJE), (x1, yv + 0.075, Z_LAJE + 0.008))
        for s in (-1, 1):
            q = Vector(((x0 + x1) / 2, yv + s * 0.062, Z_LAJE + 0.008))
            tubo(B('aco'), q, q + Z * 0.03, 0.006, 6)
            cil(B('aco'), q + Z * 0.012, 0.011, 0.01, lados=6)
cil(B('ferro', True), P((Z_VIGA + Z_PLACA) / 2), 0.27, Z_PLACA - Z_VIGA, lados=48)   # mesa redonda sobre as vigas
for k in range(16):                                                        # nervuras por baixo da mesa
    a = k * PI / 8
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('ferro'), P(Z_VIGA - 0.03) + d * 0.18, (0.16, 0.014, 0.06), Matrix((d, Z.cross(d), Z)).transposed())
for yv in YV:
    for x in (PC.x - 0.12, PC.x + 0.12):
        q = Vector((x, yv, Z_PLACA))
        tubo(B('aco'), q - Z * 0.04, q + Z * 0.022, 0.007, 6)
        cil(B('aco'), q + Z * 0.008, 0.013, 0.012, lados=6)
# coluna e carcaça de dois estágios (bowls), sino e cesto de crivo
cil(B('cano', True), P(0.015), 0.095, 0.43, lados=32)                      # coluna (0,23 → -0,20)


def junta(c, u, rp, nb=8, mat='ferro', mat2=None, matc='cano'):
    """Par de flanges aparafusadas com gargalos cônicos dos dois lados; parafusos atravessam as duas."""
    c, u = Vector(c), Vector(u).normalized()
    esp = 0.024
    rf = rp + 0.06
    cil(B(mat, True), c - u * esp / 2, rf, esp, u, lados=40)
    cil(B(mat2 or mat, True), c + u * esp / 2, rf, esp, u, lados=40)
    cil(B(matc, True), c - u * (esp + 0.02), rp, 0.04, u, lados=32, r2=rp + 0.014)
    cil(B(matc, True), c + u * (esp + 0.02), rp + 0.014, 0.04, u, lados=32, r2=rp)
    s, up = base_lat(u)
    for k in range(nb):
        a = PI / nb + k * 2 * PI / nb
        p = c + (s * math.cos(a) + up * math.sin(a)) * (rp + 0.036)
        tubo(B('aco'), p - u * (esp + 0.018), p + u * (esp + 0.018), 0.0075, 8)
        for sg in (-1, 1):
            cil(B('aco'), p + u * sg * (esp + 0.006), 0.014, 0.012, u, lados=6)


junta(P(-0.16), Z, 0.095, 8, matc='ferro')
cil(B('ferro', True), P(-0.235), 0.11, 0.07, Z, lados=36, r2=0.15)          # cone até a carcaça
for z0, z1 in ((-0.27, -0.42), (-0.47, -0.6)):                             # dois estágios
    zc = (z0 + z1) / 2
    cil(B('ferro', True), P(zc), 0.15, z0 - z1, lados=40)
    cil(B('ferro', True), P(zc), 0.158, 0.05, lados=40)                    # barriga do estágio
    for k in range(8):                                                     # nervuras
        a = k * PI / 4 + PI / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        caixa(B('ferro'), P(zc) + d * 0.16, (0.022, 0.022, z0 - z1 - 0.02), Matrix((d, Z.cross(d), Z)).transposed())
junta(P(-0.445), Z, 0.15, 12, matc='ferro')
cil(B('ferro', True), P(-0.66), 0.15, 0.12, Z, lados=40, r2=0.15)
cil(B('ferro', True), P(-0.69), 0.23, 0.06, Z, lados=40, r2=0.15)          # sino de sucção
toro(B('ferro', True), P(-0.72), 0.22, 0.014, Z, nR=40, nr=8)
for k in range(20):                                                        # cesto de crivo
    a = k * 2 * PI / 20
    tubo(B('aco'), P(-0.72) + Vector((math.cos(a), math.sin(a), 0)) * 0.2, P(-0.86) + Vector((math.cos(a), math.sin(a), 0)) * 0.17, 0.006, 6)
toro(B('aco', True), P(-0.79), 0.185, 0.007, Z, nR=36, nr=6)
cil(B('ferro', True), P(-0.865), 0.18, 0.015, lados=36)
for k in range(5):                                                         # folhas grudadas no cesto
    a = random.uniform(0, 2 * PI)
    folha(B('folha_seca'), P(random.uniform(-0.84, -0.74)) + Vector((math.cos(a), math.sin(a), 0)) * 0.2, 0.07,
          Vector((math.cos(a), math.sin(a), 0.2)), random.uniform(0, PI))

# ------------------------------------------------------------------ visor em espiral com anéis de campo
Z_V0, Z_V1 = 0.385, 0.815                  # vidro
cil(B('ferro', True), P(0.275), 0.2, 0.05, lados=40)                       # flange de base
for k in range(8):
    a = PI / 8 + k * PI / 4
    q = P(0.3) + Vector((math.cos(a), math.sin(a), 0)) * 0.178
    tubo(B('aco'), q - Z * 0.06, q + Z * 0.016, 0.008, 6)
    cil(B('aco'), q + Z * 0.006, 0.015, 0.012, lados=6)
cil(B('amarelo', True), P(0.33), 0.15, 0.06, lados=40)                     # colar de baixo
cil(B('ferro', True), P(Z_V0 - 0.0125), 0.17, 0.025, lados=40)
cil(B('ferro', True), P(Z_V1 + 0.0125), 0.17, 0.025, lados=40)
cil(B('amarelo', True), P(0.86), 0.15, 0.04, lados=40)                     # colar de cima
for k in range(6):                                                         # tirantes do visor
    a = k * PI / 3
    q = P(0.6) + Vector((math.cos(a), math.sin(a), 0)) * 0.145
    cil(B('cromo', True), q, 0.006, Z_V1 - Z_V0 + 0.08, lados=8)
    for z in (Z_V0 - 0.032, Z_V1 + 0.032):
        cil(B('aco'), Vector((q.x, q.y, z)), 0.012, 0.014, lados=6)
bm = bmesh.new()
tubo_oco(bm, P((Z_V0 + Z_V1) / 2), 0.125, 0.117, Z_V1 - Z_V0, Z, 48)
suavizar(obj('visor_vidro', bm, 'vidro'))
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.1155, Z_V1 - Z_V0 - 0.004, lados=48)
agua_v = obj('visor_agua', bm, 'agua_visor')
agua_v.location = P((Z_V0 + Z_V1) / 2)
suavizar(agua_v)
# anéis de campo: núcleo, bobina de cobre, faixa que brilha por dentro, emissores de cristal, postes
Z_ANEIS = (0.48, 0.6, 0.72)
ANG_POSTE = (PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3)
R_POSTE = 0.255
for i, z in enumerate(Z_ANEIS):
    c = P(z)
    toro(B('grafite', True), c, 0.19, 0.02, Z, nR=56, nr=10)
    toro(B('anel%d' % i), c, 0.171, 0.005, Z, nR=56, nr=6)
    for j in range(36):                                                    # espiras de cobre em volta do núcleo
        a = j * 2 * PI / 36
        if min(abs((a - ap + PI) % (2 * PI) - PI) for ap in ANG_POSTE) < 0.2:
            continue
        d = Vector((math.cos(a), math.sin(a), 0))
        toro(B('cobre', True), c + d * 0.19, 0.024, 0.0045, Z.cross(d), nR=14, nr=5)
    for ap in ANG_POSTE:
        d = Vector((math.cos(ap), math.sin(ap), 0))
        caixa(B('ferro'), c + d * 0.225, (0.05, 0.04, 0.03), Matrix((d, Z.cross(d), Z)).transposed())   # braçadeira
        cil(B('cristal'), c + d * 0.157, 0.011, 0.03, -d, lados=6, r2=0.003)                         # emissor
        toro(B('cobre', True), c + d * 0.165, 0.014, 0.003, d, nR=12, nr=5)
for ap in ANG_POSTE:                                                       # postes e aranhas de cima e de baixo
    d = Vector((math.cos(ap), math.sin(ap), 0))
    viga(B('amarelo'), P(0.33) + d * R_POSTE, P(0.9) + d * R_POSTE, 0.034)
    for z in (0.34, 0.875):
        viga(B('amarelo'), P(z) + d * 0.145, P(z) + d * (R_POSTE + 0.02), 0.03)
    caixa(B('ferro'), P(0.315) + d * R_POSTE, (0.06, 0.06, 0.012), Matrix((d, Z.cross(d), Z)).transposed())
luz_v = bpy.data.lights.new('Campo', 'POINT')
luz_v.color = VIOLETA
luz_v.energy = 6.0
luz_v.shadow_soft_size = 0.1
lv_o = bpy.data.objects.new('Campo', luz_v)
sc.collection.objects.link(lv_o)
lv_o.location = P(0.6, 0.0, -0.3)

# ------------------------------------------------------------------ cabeçote de descarga, gaxeta, lanterna, motor
cil(B('ferro', True), P(0.99), 0.17, 0.22, lados=40)                       # corpo do cabeçote (0,88 → 1,10)
cil(B('ferro', True), P(0.99), 0.178, 0.08, lados=40)
tubo(B('ferro', True), P(Z_D), Vector((-0.07, PC.y, Z_D)), R_REC, 32)     # bocal de recalque para leste
for k in range(6):                                                         # nervuras do cabeçote
    a = k * PI / 3 + PI / 6
    d = Vector((math.cos(a), math.sin(a), 0))
    if d.x > 0.6:
        continue
    caixa(B('ferro'), P(0.99) + d * 0.18, (0.03, 0.02, 0.2), Matrix((d, Z.cross(d), Z)).transposed())
cil(B('ferro', True), P(1.115), 0.19, 0.03, lados=40)                      # tampa do cabeçote
for k in range(10):
    a = k * 2 * PI / 10
    q = P(1.13) + Vector((math.cos(a), math.sin(a), 0)) * 0.17
    tubo(B('aco'), q - Z * 0.03, q + Z * 0.012, 0.007, 6)
    cil(B('aco'), q + Z * 0.004, 0.013, 0.01, lados=6)
cil(B('ferro', True), P(1.165), 0.06, 0.07, lados=24)                      # caixa de gaxeta
cil(B('aco', True), P(1.205), 0.075, 0.012, lados=24)                      # sobreposta da gaxeta
for s in (-1, 1):
    q = P(1.17, s * 0.065, 0.0)
    tubo(B('aco'), q - Z * 0.03, q + Z * 0.06, 0.006, 6)
    cil(B('aco'), q + Z * 0.05, 0.012, 0.01, lados=6)
# lanterna aberta (acoplamento à vista)
cil(B('ferro', True), P(1.145), 0.2, 0.03, lados=40)
cil(B('ferro', True), P(1.44), 0.2, 0.04, lados=40)
for k in range(4):
    a = PI / 4 + k * PI / 2
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('ferro'), P(1.29) + d * 0.175, (0.035, 0.07, 0.26), Matrix((d, Z.cross(d), Z)).transposed())
for k in range(2):                                                         # telas de proteção nas janelas (barras)
    a = k * PI
    for j in range(-3, 4):
        aa = a + j * 0.14
        d = Vector((math.cos(aa), math.sin(aa), 0))
        cil(B('amarelo', True), P(1.29) + d * 0.19, 0.004, 0.26, lados=6)
# motor vertical
cil(B('ferro', True), P(1.48), 0.22, 0.04, lados=40)
for k in range(8):
    a = PI / 8 + k * PI / 4
    q = P(1.5) + Vector((math.cos(a), math.sin(a), 0)) * 0.2
    tubo(B('aco'), q - Z * 0.07, q + Z * 0.012, 0.008, 6)
    cil(B('aco'), q + Z * 0.004, 0.015, 0.012, lados=6)
cil(B('grafite', True), P(1.71), 0.17, 0.42, lados=40)
for k in range(28):                                                        # aletas verticais
    a = k * 2 * PI / 28
    if abs(((a - PI / 2) + PI) % (2 * PI) - PI) < 0.42:
        continue
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('grafite'), P(1.71) + d * 0.185, (0.032, 0.007, 0.38), Matrix((d, Z.cross(d), Z)).transposed())
cil(B('cinza', True), P(1.95), 0.19, 0.08, lados=40, r2=0.165)              # tampa do ventilador (peça trocada)
for r in (0.06, 0.1, 0.14):
    toro(B('ferro', True), P(1.993), r, 0.006, Z, nR=36, nr=6)
for k in range(6):
    a = k * PI / 3
    viga(B('ferro'), P(1.993), P(1.993) + Vector((math.cos(a), math.sin(a), 0)) * 0.15, 0.01)
caixa(B('ferro'), P(2.01), (0.08, 0.03, 0.03))
toro(B('ferro', True), P(2.055), 0.035, 0.011, X, nR=20, nr=8)             # olhal de içamento (drone)
caixa(B('grafite'), P(1.69, 0.0, 0.225), (0.15, 0.09, 0.17))               # caixa de ligação (norte)
caixa(B('aco'), P(1.69, 0.0, 0.272), (0.12, 0.004, 0.13))                  # tampa da caixa
for sx in (-1, 1):
    for sz in (-1, 1):
        cil(B('aco'), P(1.69 + sz * 0.055, sx * 0.05, 0.276), 0.007, 0.006, Y, lados=6)
cil(B('aco'), P(1.785, 0.0, 0.225), 0.022, 0.03, lados=10)                 # prensa-cabo
caixa(B('aco'), P(1.6, 0.0, -0.172), (0.12, 0.006, 0.07))                  # placa do motor (sul)

# ------------------------------------------------------------------ rotor: eixo, rosca do visor, acoplamento
rotor = bpy.data.objects.new('rotor', None)
sc.collection.objects.link(rotor)
rotor.location = PC
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.5)), 0.02, 2.0, lados=16)                          # eixo (-0,5 → 1,5)
suavizar(obj('eixo', bm, 'cromo', rotor))
bm = bmesh.new()                                                           # rosca helicoidal (3 voltas)
N = 150
an = []
for i in range(N + 1):
    t = i / N
    z = Z_V0 + 0.012 + (Z_V1 - Z_V0 - 0.024) * t
    a = (z - Z_V0) * K_HELICE
    d = Vector((math.cos(a), math.sin(a), 0))
    an.append([bm.verts.new(d * r + Vector((0, 0, z + dz))) for r, dz in ((0.02, -0.004), (0.104, -0.003), (0.104, 0.003), (0.02, 0.004))])
for A, B_ in zip(an, an[1:]):
    for j in range(4):
        bm.faces.new((A[j], A[(j + 1) % 4], B_[(j + 1) % 4], B_[j]))
suavizar(obj('rosca', bm, 'bronze', rotor))
bm, bp = bmesh.new(), bmesh.new()                                          # acoplamento de flanges
for z, h in ((1.255, 0.05), (1.335, 0.05)):
    cil(bm, Vector((0, 0, z)), 0.045, h, lados=20)
for z in (1.287, 1.303):
    cil(bm, Vector((0, 0, z)), 0.07, 0.016, lados=24)
for k in range(6):
    a = k * PI / 3
    q = Vector((math.cos(a), math.sin(a), 0)) * 0.055
    cil(bp, q + Vector((0, 0, 1.295)), 0.006, 0.05, lados=6)
    for z in (1.27, 1.32):
        cil(bp, q + Vector((0, 0, z)), 0.011, 0.008, lados=6)
suavizar(obj('acoplamento', bm, 'aco', rotor))
obj('acoplamento_parafusos', bp, 'aco', rotor)
bm = bmesh.new()
caixa(bm, Vector((0.046, 0, 1.335)), (0.006, 0.02, 0.045))                 # marca de tinta (vê o giro)
caixa(bm, Vector((0.022, 0, 0.32 + 0.6)), (0.006, 0.012, 0.03))
obj('marca', bm, 'amarelo', rotor)

# ------------------------------------------------------------------ recalque: válvula de retenção, curva, borda norte
junta(Vector((-0.025, PC.y, Z_D)), X, R_REC, 8, matc='ferro')
cil(B('ferro', True), Vector((VX, PC.y, Z_D)), 0.13, 0.15, X, lados=40)    # corpo da retenção
for s in (-1, 1):
    cil(B('ferro', True), Vector((VX + s * 0.0975, PC.y, Z_D)), 0.13 if s > 0 else R_REC, 0.045, X, lados=40,
        r2=R_REC if s > 0 else 0.13)
cil(B('ferro', True), Vector((VX, PC.y, Z_D + 0.135)), 0.09, 0.05, lados=32)   # pescoço da tampa
cil(B('ferro', True), Vector((VX, PC.y, Z_D + 0.17)), 0.115, 0.022, lados=32)  # tampa
for k in range(8):
    a = PI / 8 + k * PI / 4
    q = Vector((VX, PC.y, Z_D + 0.181)) + Vector((math.cos(a), math.sin(a), 0)) * 0.1
    tubo(B('aco'), q - Z * 0.03, q + Z * 0.012, 0.006, 6)
    cil(B('aco'), q + Z * 0.004, 0.012, 0.01, lados=6)
cil(B('ferro', True), Vector((VX, PC.y - 0.145, Z_D + 0.03)), 0.03, 0.04, Y, lados=16)   # mancal do eixo da portinhola
caixa(B('tinta'), Vector((VX, PC.y - 0.131, Z_D - 0.04)), (0.1, 0.003, 0.015))           # seta de fluxo
for s in (-1, 1):
    viga(B('tinta'), Vector((VX + 0.05, PC.y - 0.131, Z_D - 0.04)), Vector((VX + 0.02, PC.y - 0.131, Z_D - 0.04 + s * 0.025)), 0.01)
junta(Vector((0.265, PC.y, Z_D)), X, R_REC, 8, matc='ferro')
LINHA = caminho([(0.3, PC.y, Z_D), (X_DESCE, PC.y, Z_D), (X_DESCE, PC.y, Z_CANO), (X_DESCE, 0.92, Z_CANO)], 0.2, 14)
varrer(B('cano', True), LINHA, R_REC, 36)
junta(Vector((X_DESCE, PC.y, 0.665)), Z, R_REC, 8, mat='ferro', mat2='oxido')
junta(Vector((X_DESCE, 0.3, Z_CANO)), Y, R_REC, 8)
# flange da borda igual aos canos aprovados (face em y = 1, furação em π/8 + kπ/4)
RF, EF, RBF = 0.158, 0.035, 0.133
cb = Vector((X_DESCE, 1.0, Z_CANO))
cil(B('cano', True), cb - Y * 0.0575, R_REC, 0.045, Y, lados=32, r2=0.112)
cil(B('ferro', True), cb - Y * EF / 2, RF, EF, Y, lados=40)
s_, up_ = base_lat(Y)
for k in range(8):
    a = PI / 8 + k * PI / 4
    p = cb + (s_ * math.cos(a) + up_ * math.sin(a)) * RBF
    tubo(B('aco'), p - Y * 0.058, p, 0.0105, 8)
    cil(B('aco'), p - Y * (EF + 0.008), 0.019, 0.016, Y, lados=6)


def suporte(c, u, r=R_REC, cor='amarelo'):
    """Suporte de chão (como nos canos): bloco de concreto, chapa, perfil H, sela e abraçadeira."""
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    rot = rot_de(u)
    chapa_arco(B('ferro', True), c, u, r + 0.001, 0.016, 0.1, math.radians(193), math.radians(347), 16)
    chapa_arco(B('aco', True), c, u, r + 0.001, 0.005, 0.04, math.radians(-10), math.radians(190), 20)
    zb = c.z - r - 0.014
    for sx in (-1, 1):
        q = c + s * sx * (r + 0.03) + Z * (-0.03)
        caixa(B('ferro'), q, (0.05, 0.1, 0.012), rot)
        tubo(B('aco'), q - Z * 0.02, q + Z * 0.035, 0.006, 6)
        cil(B('aco'), q + Z * 0.012, 0.011, 0.01, lados=6)
    pe = Vector((c.x, c.y, Z_LAJE))
    caixa_de(B('concreto'), pe + Vector((-0.12, -0.12, 0)), pe + Vector((0.12, 0.12, 0.04)))
    caixa(B('ferro'), pe + Z * 0.0475, (0.19, 0.19, 0.015), rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = pe + rot @ Vector((sx * 0.07, sy * 0.07, 0.06))
            tubo(B('aco'), q - Z * 0.008, q + Z * 0.02, 0.006, 6)
            cil(B('aco'), q, 0.012, 0.01, lados=6)
    h = zb - (Z_LAJE + 0.055)
    m = pe + Z * (0.055 + h / 2)
    caixa(B(cor), m, (0.012, 0.075, h), rot)
    for sy in (-1, 1):
        caixa(B(cor), m + u * sy * 0.035, (0.075, 0.01, h), rot)
    caixa(B(cor), pe + Z * (zb - Z_LAJE - 0.006), (0.11, 0.1, 0.012), rot)


suporte((X_DESCE, -0.15, Z_CANO), Y)
suporte((X_DESCE, 0.66, Z_CANO), Y)
# braçadeira da descida presa num pilarete na laje
for z in (0.55, 0.8):
    toro(B('aco', True), Vector((X_DESCE, PC.y, z)), R_REC + 0.006, 0.006, Z, nR=36, nr=6)
viga(B('amarelo'), Vector((X_DESCE + 0.2, PC.y, Z_LAJE)), Vector((X_DESCE + 0.2, PC.y, 0.82)), 0.05)
caixa_de(B('ferro'), (X_DESCE + 0.15, PC.y - 0.05, Z_LAJE), (X_DESCE + 0.25, PC.y + 0.05, Z_LAJE + 0.012))
for z in (0.55, 0.8):
    viga(B('amarelo'), Vector((X_DESCE + R_REC + 0.006, PC.y, z)), Vector((X_DESCE + 0.2, PC.y, z)), 0.03)
# remendo aparafusado na descida
chapa_arco(B('oxido', True), Vector((X_DESCE, PC.y, 0.5)), Z, R_REC + 0.001, 0.006, 0.09, math.radians(200), math.radians(290), 10)
for a in (math.radians(207), math.radians(283)):
    for w in (-0.03, 0.03):
        d = Vector((math.cos(a), math.sin(a), 0))
        s_, up_ = base_lat(Z)
        dd = s_ * math.cos(a) + up_ * math.sin(a)
        cil(B('aco'), Vector((X_DESCE, PC.y, 0.5 + w)) + dd * (R_REC + 0.009), 0.008, 0.008, dd, lados=6)

# ------------------------------------------------------------------ manômetros (ponteiro treme com a bomba)
GAUGES = []


def manometro(pos, normal, haste, r=0.036):
    pos, n = Vector(pos), Vector(normal).normalized()
    tubo(B('cromo', True), Vector(haste), pos, 0.007, 8)
    tubo(B('cromo', True), pos - n * 0.012, pos + n * 0.012, r, 24)
    tubo(B('cromo', True), pos + n * 0.012, pos + n * 0.016, r * 1.06, 24)
    tubo(B('mostrador'), pos + n * 0.011, pos + n * 0.0135, r * 0.9, 24)
    e = bpy.data.objects.new('ponteiro_piv', None)
    sc.collection.objects.link(e)
    e.location = pos + n * 0.0145
    e.rotation_mode = 'QUATERNION'
    e.rotation_quaternion = n.to_track_quat('Z', 'Y')
    bm = bmesh.new()
    caixa(bm, (0, r * 0.35, 0), (0.004, r * 0.75, 0.002))
    caixa(bm, (0, 0, -0.0005), (0.008, 0.008, 0.002))
    obj('ponteiro', bm, 'preto', e)
    GAUGES.append((e, n, random.uniform(-0.8, 0.4)))


manometro((X_DESCE - 0.17, PC.y, 0.8), -X, (X_DESCE - R_REC, PC.y, 0.8))
manometro((X_DESCE - 0.08, 0.05, Z_CANO + 0.2), -X, (X_DESCE, 0.05, Z_CANO + R_REC))
manometro(P(0.97, 0.0, -0.25), -Y, P(0.97, 0.0, -0.17))

# ------------------------------------------------------------------ quadro da IA, antena, eletrocalha, poste, cabos
QX0, QX1, QY0, QY1, QZ1 = -0.95, -0.62, 0.3, 0.9, 1.0
caixa_de(B('grafite'), (QX0, QY0, Z_LAJE), (QX1, QY1, QZ1))
caixa_de(B('concreto'), (QX0 - 0.02, QY0 - 0.02, Z_LAJE), (QX1 + 0.02, QY1 + 0.02, Z_LAJE + 0.05))   # sapata
for k in range(9):                                                         # aletas de calor
    y = QY0 + 0.04 + k * 0.065
    caixa_de(B('grafite'), (QX0 + 0.02, y, QZ1), (QX1 - 0.02, y + 0.012, QZ1 + 0.07))
caixa_de(B('ferro'), (QX1, QY0 + 0.08, 0.25), (QX1 + 0.006, QY1 - 0.08, 0.45))     # grelha
for k in range(8):
    z = 0.27 + k * 0.024
    caixa_de(B('preto'), (QX1 + 0.006, QY0 + 0.09, z), (QX1 + 0.008, QY1 - 0.09, z + 0.01))
caixa_de(B('preto'), (QX1, 0.5, 0.66), (QX1 + 0.012, 0.74, 0.84))          # moldura do olho
for k in range(4):                                                         # olho da IA: barras violeta
    caixa_de(B('olho'), (QX1 + 0.012, 0.52 + k * 0.055, 0.69 + 0.03 * (k % 2)), (QX1 + 0.016, 0.555 + k * 0.055, 0.81 - 0.03 * (k % 2)))
for k in range(3):
    cil(B('lampada'), Vector((QX1 + 0.006, 0.4 + k * 0.05, 0.92)), 0.013, 0.01, X, lados=12)
caixa_de(B('oxido'), (QX1, 0.36, 0.5), (QX1 + 0.004, 0.46, 0.6))            # chapa trocada (remendo)
for y in (0.37, 0.45):
    for z in (0.51, 0.59):
        cil(B('aco'), Vector((QX1 + 0.006, y, z)), 0.007, 0.006, X, lados=6)
# antena
AX, AY = -0.72, 0.82
tubo(B('aco', True), Vector((AX, AY, QZ1)), Vector((AX, AY, 1.8)), 0.016, 12)
for z in (1.2, 1.45):
    toro(B('aco', True), Vector((AX, AY, z)), 0.03, 0.006, Z, nR=16, nr=6)
toro(B('ferro', True), Vector((AX, AY, 1.72)), 0.08, 0.008, Z, nR=32, nr=6)
for k in range(3):
    a = k * 2 * PI / 3
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(B('ferro'), Vector((AX, AY, 1.7)), Vector((AX, AY, 1.72)) + d * 0.08, 0.008)
    cil(B('cristal'), Vector((AX, AY, 1.75)) + d * 0.08, 0.009, 0.06, lados=6, r2=0.002)
cil(B('farol'), Vector((AX, AY, 1.82)), 0.022, 0.04, lados=16)
caixa_de(B('aco'), (AX - 0.04, AY - 0.04, QZ1), (AX + 0.04, AY + 0.04, QZ1 + 0.02))
# eletrocalha em U: quadro → leste → sul até o poste de cabos
EC = [Vector((QX1, 0.6, 0)), Vector((-0.3, 0.6, 0)), Vector((-0.3, -0.14, 0))]
for a, b in zip(EC, EC[1:]):
    d = (b - a).normalized()
    s = Vector((-d.y, d.x, 0))
    lo = Vector((min(a.x, b.x), min(a.y, b.y), Z_LAJE)) - (s * 0.04 if s.x + s.y > 0 else -s * 0.04)
    hi = Vector((max(a.x, b.x), max(a.y, b.y), Z_LAJE + 0.01)) + (s * 0.04 if s.x + s.y > 0 else -s * 0.04)
    caixa_de(B('aco'), lo - d * 0.04, hi + d * 0.04)
    for sg in (-1, 1):
        o = s * sg * 0.04
        caixa_de(B('aco'), Vector((min(a.x, b.x), min(a.y, b.y), Z_LAJE)) + o - s * 0.003 * sg - d * 0.04 + Vector((-0.003 * abs(s.x), -0.003 * abs(s.y), 0)),
                 Vector((max(a.x, b.x), max(a.y, b.y), Z_LAJE + 0.05)) + o + d * 0.04 + Vector((0.003 * abs(s.x), 0.003 * abs(s.y), 0)))
    for t in (0.25, 0.75):
        q = a.lerp(b, t)
        caixa(B('aco'), Vector((q.x, q.y, Z_LAJE + 0.05)), (0.02 + abs(s.x) * 0.08, 0.02 + abs(s.y) * 0.08, 0.008))
for k in range(3):                                                         # cabos na calha
    o = (k - 1) * 0.02
    pts = [Vector((QX1 + 0.0, 0.6 + o, Z_LAJE + 0.025)), Vector((-0.3 - o, 0.6 + o, Z_LAJE + 0.025)),
           Vector((-0.3 - o, -0.14, Z_LAJE + 0.025))]
    varrer(B('borracha', True), caminho(pts, 0.06, 6), 0.009, 8)
PX, PY = -0.3, -0.21                                                       # poste de cabos
viga(B('amarelo'), Vector((PX, PY, Z_LAJE)), Vector((PX, PY, 1.85)), 0.06)
caixa_de(B('ferro'), (PX - 0.07, PY - 0.07, Z_LAJE), (PX + 0.07, PY + 0.07, Z_LAJE + 0.012))
caixa(B('grafite'), Vector((PX, PY + 0.06, 1.2)), (0.12, 0.06, 0.18))      # caixa de junção no poste
caixa(B('aco'), Vector((PX, PY + 0.092, 1.2)), (0.1, 0.004, 0.15))
for k in range(3):                                                         # cabos sobem pelo poste com abraçadeiras
    o = (k - 1) * 0.018
    tubo(B('borracha', True), Vector((PX + o, PY + 0.04, Z_LAJE + 0.03)), Vector((PX + o, PY + 0.04, 1.11)), 0.009, 8)
for z in (0.3, 0.6, 0.9):
    caixa(B('aco'), Vector((PX, PY + 0.045, z)), (0.08, 0.03, 0.012))
# conduíte: poste → caixa de ligação do motor
pts = bezier((PX, PY, 1.86), (PX, PY - 0.05, 2.02), (PC.x, PC.y + 0.3, 2.0), (PC.x, PC.y + 0.225, 1.8), 14)
varrer(B('borracha', True), pts, 0.018, 12)
tubo(B('borracha', True), Vector((PX, PY + 0.03, 1.29)), Vector((PX, PY + 0.03, 1.86)), 0.018, 12)
for z in (1.4, 1.6, 1.8):
    caixa(B('aco'), Vector((PX, PY + 0.035, z)), (0.08, 0.03, 0.012))
# cabos: caixa de junção → poste norte dos anéis (bobinas)
d_n = Vector((math.cos(ANG_POSTE[0]), math.sin(ANG_POSTE[0]), 0))
pe_n = P(0.0) + d_n * R_POSTE
for k in range(2):
    o = (k - 0.5) * 0.02
    pts = bezier((PX + o, PY + 0.03, 1.12), (PX + o, PY - 0.02, 0.9), (pe_n.x + o, pe_n.y + 0.08, 0.8), (pe_n.x + o, pe_n.y + 0.02, 0.7), 12)
    varrer(B('borracha', True), pts, 0.008, 8)
    for z in Z_ANEIS:
        tubo(B('borracha', True), Vector((pe_n.x + o, pe_n.y + 0.022, 0.7)), Vector((pe_n.x + o, pe_n.y + 0.022, Z_ANEIS[0])), 0.007, 8)
for z in (0.54, 0.66):
    caixa(B('aco'), Vector((pe_n.x, pe_n.y + 0.025, z)), (0.06, 0.02, 0.01))
# fiação exposta caindo da caixa de ligação do motor


def fios(a, b, solto=0.06):
    a, b = Vector(a), Vector(b)
    for k, m in enumerate(('fio_v', 'fio_a', 'fio_m')):
        off = Vector(((k - 1) * 0.008, (k - 1) * 0.006, 0))
        meio = (a + b) / 2 + Vector((0, 0, -solto)) + off * 2
        pts = bezier(a + off, a + off + Vector((0, 0, -solto * 0.6)), meio, b + off, 10)
        mangueira(B(m), pts, 0.0045)
        tubo(B('cobre'), b + off, b + off + (b - meio).normalized() * 0.015, 0.002, 6)


fios(P(1.6, 0.04, 0.27), P(1.52, 0.1, 0.3), 0.05)
# sonda de turbidez/nível pendurada no poço (água suja rende menos: a IA mede)
SX, SY = WX0 + 0.1, -1.22
caixa_de(B('amarelo'), (WX0 - 0.07, SY - 0.02, Z_LAJE), (SX + 0.03, SY + 0.02, Z_LAJE + 0.03))   # braço no pilar
for xx in (WX0 - 0.06, WX0 - 0.02):
    cil(B('aco'), Vector((xx, SY, Z_LAJE + 0.034)), 0.009, 0.008, lados=6)
tubo(B('aco', True), Vector((SX, SY, Z_LAJE + 0.03)), Vector((SX, SY, -0.62)), 0.018, 12)
cil(B('grafite', True), Vector((SX, SY, -0.66)), 0.03, 0.08, lados=16)
caixa(B('grafite'), Vector((SX, SY, Z_LAJE + 0.07)), (0.07, 0.07, 0.08))
cil(B('lampada'), Vector((SX - 0.036, SY, Z_LAJE + 0.08)), 0.01, 0.006, X, lados=10)
for k in range(4):                                                         # anéis de limo grudados na sonda
    toro(B('alga', True), Vector((SX, SY, Z_RIO + 0.02 - k * 0.04)), 0.02, 0.004, Z, nR=12, nr=5)
XP = WX0 - 0.04                                                           # cabo da sonda pelo topo do pilar oeste
pts = bezier((SX - 0.02, SY, Z_LAJE + 0.11), (XP, SY, Z_LAJE + 0.15), (XP, SY + 0.1, Z_LAJE + 0.01), (XP, SY + 0.2, Z_LAJE + 0.009), 10)
pts += [Vector((XP, y, Z_LAJE + 0.009)) for y in (-0.9, -0.7)]
pts += bezier((XP, -0.7, Z_LAJE + 0.009), (XP, -0.6, Z_LAJE + 0.009), (WX0 - 0.13, -0.62, Z_LAJE + 0.01), (WX0 - 0.13, -0.57, Z_LAJE + 0.06), 8)[1:]
varrer(B('borracha', True), pts, 0.008, 8)
for y in (-1.05, -0.85):
    caixa(B('aco'), Vector((XP, y, Z_LAJE + 0.012)), (0.03, 0.02, 0.01))

# holofote + câmera da IA na borda oeste do poço (vê a tomada e o giro da água)
HX, HY = WX0 - 0.13, -0.55
viga(B('amarelo'), Vector((HX, HY, Z_LAJE)), Vector((HX, HY, 0.78)), 0.045)
caixa_de(B('ferro'), (HX - 0.06, HY - 0.06, Z_LAJE), (HX + 0.06, HY + 0.06, Z_LAJE + 0.012))
H_ALVO = Vector((PC.x - 0.05, PC.y - 0.1, Z_RIO))
H_POS = Vector((HX + 0.03, HY, 0.8))
dH = (H_ALVO - H_POS).normalized()
cil(B('grafite', True), H_POS, 0.05, 0.1, dH, lados=20)                    # corpo do holofote
cil(B('lampada'), H_POS + dH * 0.051, 0.042, 0.004, dH, lados=20)
cil(B('grafite', True), H_POS + Vector((0, 0, 0.075)), 0.025, 0.05, dH, lados=12)   # olho de câmera
cil(B('olho'), H_POS + Vector((0, 0, 0.075)) + dH * 0.026, 0.012, 0.003, dH, lados=12)
caixa(B('aco'), H_POS - dH * 0.06 + Vector((-0.03, 0, -0.01)), (0.03, 0.08, 0.03))
pts = bezier((HX, HY + 0.03, 0.7), (HX, HY + 0.08, 0.4), (HX, HY + 0.1, 0.1), (HX, HY + 0.25, Z_LAJE + 0.01), 10)
pts += [Vector((HX, y, Z_LAJE + 0.01)) for y in (0.0, 0.2)] + bezier((HX, 0.2, Z_LAJE + 0.01), (HX, 0.27, Z_LAJE + 0.01), (-0.85, 0.27, Z_LAJE + 0.05), (-0.85, 0.3, 0.16), 6)[1:]
varrer(B('borracha', True), pts, 0.008, 8)
luz_h = bpy.data.lights.new('Holofote', 'SPOT')
luz_h.color = (1.0, 0.75, 0.45)
luz_h.energy = 150.0
luz_h.spot_size = math.radians(70)
luz_h.spot_blend = 0.6
luz_h.shadow_soft_size = 0.03
lh = bpy.data.objects.new('Holofote', luz_h)
sc.collection.objects.link(lh)
lh.location = H_POS + dH * 0.06
lh.rotation_euler = dH.to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------------ números de série (estêncil apagado)
SEG = dict(a=(0, 1, 1, 0), b=(1, 1, 0, 1), c=(1, 0, 0, 1), d=(0, 0, 1, 0), e=(0, 0, 0, 1), f=(0, 1, 0, 1), g=(0, 0.5, 1, 0))
DIG = ['abcdef', 'bc', 'abged', 'abgcd', 'fgbc', 'afgcd', 'afgedc', 'abc', 'abcdefg', 'abfgcd']


def serie(c, u, r, ang, n=6, alt=0.03, apagado=0.35):
    c, u = Vector(c), Vector(u).normalized()
    s, up = base_lat(u)
    d = s * math.cos(ang) + up * math.sin(ang)
    t = d.cross(u).normalized()
    larg = alt * 0.55
    rot = Matrix((u, t, d)).transposed()
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
            caixa(B('tinta'), c + d * (r + 0.0012) + rot @ p, tam, rot)


serie(Vector((X_DESCE, -0.1, Z_CANO)), Y, R_REC, PI * 0.95, 7, 0.032)
serie(Vector((X_DESCE, PC.y, 0.75)), Z, R_REC + 0.001, PI * 0.95, 5, 0.026)
serie(Vector((PC.x - 0.02, PC.y, -0.07)), Z, 0.096, -PI / 2 + 0.2, 6, 0.028)

# ------------------------------------------------------------------ sujeira: limo, escorridos, respingos, poças, óleo
for k in range(30):                                                        # limo escorrendo no cais (fora)
    x = random.uniform(-0.98, 0.98)
    if GX0 - 0.05 < x < GX1 + 0.05 or any(abs(x - c) < 0.06 for c in (-0.9, 0.62, 0.85)):
        continue
    L = random.uniform(0.08, 0.35)
    caixa_de(B('limo_esc'), (x - random.uniform(0.008, 0.025), YC0 - 0.0015, Z_RIO - 0.05), (x + 0.012, YC0 - 0.0005, Z_RIO + L))
for k in range(24):                                                        # limo nas paredes do poço
    y = random.uniform(YB + 0.02, WYN - 0.02)
    L = random.uniform(0.06, 0.25)
    xw = random.choice((WX0 + 0.0008, WX1 - 0.0008))
    caixa_de(B('limo_esc'), (xw - 0.0006, y - 0.015, Z_RIO - 0.05), (xw + 0.0006, y + 0.012, Z_RIO + L))
for yv in YV:                                                              # ferrugem escorrendo das chapas de apoio
    for xw in (WX0 + 0.0012, WX1 - 0.0012):
        for k in range(3):
            y = yv + random.uniform(-0.07, 0.07)
            caixa_de(B('ferrugem_esc'), (xw - 0.0005, y - 0.012, Z_LAJE - random.uniform(0.15, 0.4)), (xw + 0.0005, y + 0.012, Z_LAJE))
for x in (GX0, GX1):                                                       # ferrugem das guias da grade
    caixa_de(B('ferrugem_esc'), (x - 0.02, YG - 0.0365, Z_RIO + 0.05), (x + 0.02, YG - 0.0355, 0.1))
for k in range(8):                                                         # água escorrendo da laje pelo cais
    x = random.uniform(-0.95, 0.95)
    if GX0 - 0.05 < x < GX1 + 0.05:
        continue
    caixa_de(B('molhado'), (x - 0.02, YC0 - 0.0012, Z_RIO), (x + 0.02, YC0 - 0.0003, Z_LAJE))
for k in range(5):                                                         # água escorrendo pela borda da mesa
    a = random.uniform(-PI * 0.9, -PI * 0.1)
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('molhado'), P(Z_VIGA + 0.015) + d * 0.2715, (0.025, 0.002, 0.03), Matrix((d.cross(Z), d, Z)).transposed())
for k in range(6):                                                         # escorridos no cabeçote (gaxeta)
    a = random.uniform(-PI * 0.6, PI * 0.3)
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('molhado'), P(1.0) + d * 0.1785, (0.012, 0.012, 0.2), Matrix((d, Z.cross(d), Z)).transposed())
for k in range(4):                                                         # ferrugem escorrida na descida
    a = random.uniform(PI * 0.6, PI * 1.4)
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('ferrugem_esc'), Vector((X_DESCE, PC.y, 0.56)) + d * (R_REC + 0.0012), (0.02, 0.002, 0.16), Matrix((d.cross(Z), d, Z)).transposed())
for k in range(3):                                                         # óleo escorrendo do mancal do motor
    a = random.uniform(-PI * 0.8, -PI * 0.2)
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(B('oleo'), P(1.5) + d * 0.2215, (0.012, 0.003, 0.05), Matrix((d.cross(Z), d, Z)).transposed())
for k in range(14):                                                        # respingos na laje perto do poço
    q = (random.uniform(WX0 - 0.15, WX1 + 0.3), random.uniform(WYN + 0.07, WYN + 0.35))
    mancha(B('molhado'), q, random.uniform(0.015, 0.05), Z_LAJE + 0.0012)
for k in range(8):
    q = (random.uniform(WX0 - 0.17, WX0 - 0.085), random.uniform(-0.95, WYN))
    mancha(B('molhado'), q, random.uniform(0.015, 0.04), Z_LAJE + 0.0012)
mancha(B('poca'), (X_DESCE - 0.08, PC.y - 0.06), 0.09, Z_LAJE + 0.0035)     # poça sob a junta da descida
mancha(B('molhado'), (X_DESCE - 0.05, PC.y - 0.08), 0.15, Z_LAJE + 0.0033)
mancha(B('poca'), (PC.x + 0.12, PC.y - 0.14), 0.07, Z_PLACA + 0.001)       # água na placa-base
for c, r in (((QX1 + 0.08, 0.6), 0.06), ((-0.2, 0.4), 0.05), ((X_DESCE + 0.2, PC.y + 0.06), 0.05)):
    mancha(B('oleo'), c, r, Z_LAJE + 0.0013)
for k in range(16):                                                        # lama seca arrastada da margem
    mancha(B('lama_seca'), (random.uniform(-0.95, 0.95), random.uniform(-0.97, 0.9)), random.uniform(0.02, 0.06), Z_LAJE + 0.0008)
for k in range(12):                                                        # folhas secas sopradas na laje
    folha(B('folha_seca'), (random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95), Z_LAJE + 0.004),
          random.uniform(0.05, 0.08), Vector((0, 0, 1)), random.uniform(0, PI), 0.15)

# ------------------------------------------------------------------ margem e rio (como no filtro aprovado)


def altura(x, y):
    ax = abs(x)
    if y > -0.98:
        h = 0.0
        if ax > 1.15 or y > 1.15:
            h += 0.03 * math.sin(x * 1.7) * math.cos(y * 2.1) + 0.02 * math.sin(x * 4.3 + y * 3.1)
        return h
    if ax < 1.04:
        return -0.9
    t = min(1.0, (-0.98 - y) / 1.1)
    h = -0.9 * t * t * (3 - 2 * t)
    return h + 0.03 * math.sin(x * 3.1) * (1 - t)


bm = bmesh.new()
xs = [-80, -50, -30, -20, -14, -10, -8, -6, -5] + [i * 0.2 - 4.4 for i in range(45)] + [5, 6, 8, 10, 14, 20, 30, 50, 80]
vs = [[bm.verts.new((x, y, altura(x, y))) for x in xs] for y in xs]
for j in range(len(xs) - 1):
    for i in range(len(xs) - 1):
        f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
        c = f.calc_center_median()
        if WX0 - 0.1 < c.x < WX1 + 0.1 and -1.0 < c.y < WYN + 0.1:
            bm.faces.remove(f)
suavizar(obj('margem', bm, 'terra'))
bm = bmesh.new()
caixa_de(bm, (-80, -80, Z_RIO - 0.02), (80, YB, Z_RIO))
caixa_de(bm, (-80, YB, Z_RIO - 0.02), (WX0 - 0.08, -1.0, Z_RIO))
caixa_de(bm, (WX1 + 0.08, YB, Z_RIO - 0.02), (80, -1.0, Z_RIO))
obj('rio', bm, 'rio')
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(70):
    sx = random.choice((-1, 1))
    x = sx * random.uniform(1.12, 2.8)
    y = random.uniform(-1.85, -1.05)
    pedra(bm, (x, y, altura(x, y) + 0.03), random.uniform(0.05, 0.13), 0.55)
for k in range(30):
    x, y = random.uniform(-3, 3), random.uniform(1.2, 3.5)
    pedra(bm2, (x, y, altura(x, y)), random.uniform(0.02, 0.06), 0.5)
for o in (obj('enrocamento', bm, 'pedra'), obj('pedras', bm2, 'pedra')):
    o.modifiers.new('sub', 'SUBSURF').levels = 1
    for pg in o.data.polygons:
        pg.use_smooth = True
bm = bmesh.new()
for k in range(40):
    sx = random.choice((-1, 1))
    x0 = sx * random.uniform(1.15, 2.6)
    y0 = random.uniform(-1.55, -1.15)
    base = Vector((x0, y0, max(altura(x0, y0), Z_RIO) - 0.02))
    for j in range(5):
        top = base + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), random.uniform(0.25, 0.55)))
        cil(bm, (base + top) / 2, 0.004, (top - base).length, top - base, lados=4, r2=0.001)
obj('juncos', bm, 'palha')
bm, bm2 = bmesh.new(), bmesh.new()
for k in range(16):
    c = (random.uniform(-3.5, 3.5), random.uniform(-4.5, -1.6))
    mancha(bm if k % 3 else bm2, c, random.uniform(0.03, 0.1), Z_RIO + 0.002)
obj('escuma_rio', bm, 'escuma')
obj('espuma_suja', bm2, 'lama_seca')
bm = bmesh.new()
for k in range(7):
    c = Vector((random.uniform(-3, 3), random.uniform(-3.5, -1.4), Z_RIO + 0.005))
    a = random.uniform(0, PI)
    d = Vector((math.cos(a), math.sin(a), 0)) * random.uniform(0.15, 0.4)
    tubo(bm, c - d, c + d, 0.012, 6)
obj('galhos_rio', bm, 'galho')

# ------------------------------------------------------------------ água do poço com funil do redemoinho
bm = bmesh.new()
nx, ny = 52, 42
x0, x1, y0, y1 = WX0 - PC.x, WX1 - PC.x, YB - 0.02 - PC.y, WYN - PC.y
grade_v = []
for j in range(ny + 1):
    lin = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        y = y0 + (y1 - y0) * j / ny
        r = math.hypot(x, y)
        dz = -0.1 * (0.16 / max(r, 0.16)) ** 2 + 0.1 * (0.16 / 0.6) ** 2 * (1 - min(r, 0.6) / 0.6)
        lin.append(bm.verts.new((x, y, dz)))
    grade_v.append(lin)
for j in range(ny):
    for i in range(nx):
        bm.faces.new((grade_v[j][i], grade_v[j][i + 1], grade_v[j + 1][i + 1], grade_v[j + 1][i]))
agua_p = obj('agua_poco', bm, 'agua_poco')
agua_p.location = (PC.x, PC.y, Z_RIO)
for pg in agua_p.data.polygons:
    pg.use_smooth = True


def z_funil(r):
    return Z_RIO - 0.1 * (0.16 / max(r, 0.16)) ** 2 + 0.1 * (0.16 / 0.6) ** 2 * (1 - min(r, 0.6) / 0.6)


toro(B('escuma', True), P(z_funil(0.155) + 0.004), 0.156, 0.008, Z, nR=40, nr=6)   # colar de espuma na coluna

# ------------------------------------------------------------------ fecha os baldes estáticos
fechar()

# ------------------------------------------------------------------ partes animadas
# espuma e folhas presas no giro (dois aros: dentro gira mais rápido)
giros = []
for k_g, (r0, r1, n_p) in enumerate(((0.17, 0.27, 9), (0.28, 0.42, 12))):
    e = bpy.data.objects.new('giro%d' % k_g, None)
    sc.collection.objects.link(e)
    e.location = P(0.0)
    bme, bmf, bml = bmesh.new(), bmesh.new(), bmesh.new()
    for k in range(n_p):
        a = k * 2 * PI / n_p + random.uniform(-0.2, 0.2)
        r = random.uniform(r0, r1)
        d = Vector((math.cos(a), math.sin(a), 0))
        q = d * r
        if not (WX0 + 0.03 < PC.x + q.x < WX1 - 0.03 and YB + 0.03 < PC.y + q.y < WYN - 0.03):
            continue
        z = z_funil(r) + 0.004
        if k % 3 == 0:
            folha(bml if k % 2 else bmf, q + Vector((0, 0, z + 0.002)), random.uniform(0.05, 0.08), Vector((0, 0, 1)), a + 1.2, 0.15)
        bmA = bmesh.new()
        res = bmesh.ops.create_circle(bme, cap_ends=True, segments=10, radius=1.0)
        t = Z.cross(d)
        for v in res['verts']:
            w = v.co.copy()
            v.co = q + t * w.x * random.uniform(0.04, 0.09) + d * w.y * 0.012 + Vector((0, 0, z))
        bmA.free()
    obj('giro_espuma%d' % k_g, bme, 'espuma', e)
    obj('giro_folha_a%d' % k_g, bmf, 'folha_seca', e)
    obj('giro_folha_b%d' % k_g, bml, 'folha_amarela', e)
    giros.append(e)
# bolhas de espuma ao longo dos três braços do redemoinho (giram junto com os braços do shader: 2 voltas por laço)
e = bpy.data.objects.new('bracos', None)
sc.collection.objects.link(e)
e.location = P(0.0)
bme = bmesh.new()
for k in range(3):
    c = PI / 2 + 0.4 + 2 * PI * k
    r = 0.17
    while r < 0.55:
        th = (c - 7.0 * math.log(r)) / 3.0
        for j in range(random.randint(2, 5)):
            q = Vector((math.cos(th), math.sin(th), 0)) * (r + random.uniform(-0.012, 0.012))
            q.rotate(Matrix.Rotation(random.uniform(-0.04, 0.04), 3, 'Z'))
            if not (WX0 + 0.03 < PC.x + q.x < WX1 - 0.03 and YB + 0.03 < PC.y + q.y < WYN - 0.03):
                continue
            pedra(bme, q + Vector((0, 0, z_funil(q.length) + 0.001)), random.uniform(0.005, 0.013) * (1.3 - r), 0.4)
        r += 0.012
o = obj('bracos_espuma', bme, 'espuma', e)
for pg in o.data.polygons:
    pg.use_smooth = True
giros.append(e)
# folhas descendo o rio até a grade
folhas_rio = []
for k in range(6):
    bm = bmesh.new()
    folha(bm, (0, 0, 0), random.uniform(0.06, 0.09), Vector((0, 0, 1)), random.uniform(0, PI), 0.15)
    o = obj('folha_rio', bm, random.choice(('folha_seca', 'folha_verde', 'folha_amarela')))
    x = random.uniform(GX0 + 0.05, GX1 - 0.05)
    folhas_rio.append((o, Vector((x + random.uniform(-0.6, 0.6), -2.4, Z_RIO + 0.004)), Vector((x, YG - 0.07, Z_RIO + 0.004)), k / 6))
# contrapeso da válvula de retenção (balança com o fluxo)
piv = bpy.data.objects.new('contrapeso', None)
sc.collection.objects.link(piv)
piv.location = (VX, PC.y - 0.17, Z_D + 0.03)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.02, 0.025, Y, lados=12)
viga(bm, Vector((0, 0, 0)), Vector((0.17, 0, -0.04)), 0.022)
obj('alavanca', bm, 'amarelo', piv)
bm = bmesh.new()
cil(bm, Vector((0.18, -0.005, -0.045)), 0.045, 0.05, Y, lados=20)
suavizar(obj('peso', bm, 'ferro', piv))
# gotas: (onde se forma, onde cai, vezes por laço)
GOTAS = [(Vector((-0.02, PC.y - 0.06, Z_D - 0.16)), z_funil(math.hypot(-0.02 - PC.x, 0.06)), 3),
         (Vector((X_DESCE - 0.15, PC.y - 0.03, 0.645)), Z_LAJE + 0.002, 2),
         (Vector((VX + 0.12, PC.y - 0.04, Z_D + 0.16)), z_funil(math.hypot(VX + 0.12 - PC.x, 0.04)), 2),
         (P(1.16, 0.05, -0.06), Z_PLACA + 0.002, 3)]
gotas = []
for p, zc, vezes in GOTAS:
    for rep in range(2):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.008)
        o = obj('gota', bm, 'gota')
        for pg in o.data.polygons:
            pg.use_smooth = True
        gotas.append((o, p, zc, vezes, rep * 0.5 + random.random() * 0.1))
# anéis de onda onde as gotas caem na água
ondas = []
for k in range(2):
    bm = bmesh.new()
    toro(bm, Vector((0, 0, 0)), 1.0, 0.05, Z, nR=32, nr=6)
    o = obj('onda', bm, 'espuma')
    ondas.append(o)


# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


DUR = QUADROS / FPS
VOLTAS = 12                                                                # eixo: 12 voltas por laço (3 rps)
anel_em = [base3d.M['anel%d' % i].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'] for i in range(3)]
olho_em = base3d.M['olho'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
farol_em = base3d.M['farol'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    rotor.rotation_euler = (0, 0, 2 * PI * VOLTAS * fr)
    rotor.keyframe_insert('rotation_euler', frame=q)
    for val in FASES['visor']:                                             # água sobe em espiral junto com a rosca
        val.outputs[0].default_value = 2 * PI * VOLTAS * fr
        val.outputs[0].keyframe_insert('default_value', frame=q)
    for val in FASES['poco']:                                              # redemoinho: braços giram (2 voltas)
        val.outputs[0].default_value = 2 * PI * 6 * fr
        val.outputs[0].keyframe_insert('default_value', frame=q)
    for k_g, e in enumerate(giros):
        e.rotation_euler = (0, 0, 2 * PI * (1 if k_g == 1 else 2) * fr)
        e.keyframe_insert('rotation_euler', frame=q)
    for i, inp in enumerate(anel_em):                                      # onda de campo subindo pelos anéis
        u = (4 * fr - i / 3) % 1.0
        inp.default_value = 2.5 + 14.0 * math.exp(-((u - 0.15) / 0.12) ** 2)
        inp.keyframe_insert('default_value', frame=q)
    luz_v.energy = 5.0 + 2.0 * math.sin(2 * PI * 4 * fr)
    luz_v.keyframe_insert('energy', frame=q)
    olho_em.default_value = 4.0 + 2.0 * math.sin(2 * PI * 2 * fr)
    olho_em.keyframe_insert('default_value', frame=q)
    farol_em.default_value = 18.0 if (fr * 2) % 1.0 < 0.15 else 0.4
    farol_em.keyframe_insert('default_value', frame=q)
    piv.rotation_euler = (0, 0.08 * math.sin(2 * PI * 8 * fr) + 0.03 * math.sin(2 * PI * 3 * fr), 0)
    piv.keyframe_insert('rotation_euler', frame=q)
    for e, nrm, f0 in GAUGES:
        e.rotation_quaternion = nrm.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), f0 - 0.12 * math.sin(2 * PI * 8 * fr))
        e.keyframe_insert('rotation_quaternion', frame=q)
    for o, a, b, f0 in folhas_rio:
        u = (fr + f0) % 1.0
        o.location = a.lerp(b, suave(u * 1.1)) + Vector((0.03 * math.sin(u * 9 + f0 * 20), 0, 0))
        o.rotation_euler = (0, 0, u * 1.5 + f0 * 6)
        s = min(1.0, u / 0.08) * (1.0 - suave((u - 0.9) / 0.1))
        o.scale = [max(0.01, s)] * 3
        for c in ('location', 'rotation_euler', 'scale'):
            o.keyframe_insert(c, frame=q)
    for k, (o, p, zc, vezes, f0) in enumerate(gotas):
        u = (vezes * fr + f0) % 1.0
        h = p.z - zc
        tq = math.sqrt(2 * max(h, 0.01) / 9.8) / (DUR / vezes)
        if u < 0.6:
            s = 0.25 + 0.75 * suave(u / 0.6)
            o.location = p - Z * 0.008 * s
            o.scale = (s, s, s)
        elif u < 0.6 + tq:
            t = (u - 0.6) * DUR / vezes
            o.location = p - Z * (0.008 + 4.9 * t * t)
            o.scale = (0.85, 0.85, 1.3)
        else:
            o.location = p - Z * 0.008
            o.scale = (0.05, 0.05, 0.05)
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for k, o in enumerate(ondas):                                          # onda da gota da válvula no poço
        p, zc, vezes = GOTAS[2]
        u = (vezes * fr + gotas[4 + k][4] - 0.6 - math.sqrt(2 * (p.z - zc) / 9.8) / (DUR / vezes)) % 1.0
        o.location = (p.x, p.y, zc + 0.003)
        rr = 0.01 + 0.12 * u
        o.scale = (rr, rr, 0.02 * (1 - u) + 0.002)
        o.hide_render = u > 0.6
        for c in ('location', 'scale', 'hide_render'):
            o.keyframe_insert(c, frame=q)

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
    pr = bpy.context.preferences.addons['cycles'].preferences
    pr.compute_device_type = 'OPTIX'
    pr.get_devices()
    for dv in pr.devices:
        dv.use = True
except Exception:
    sc.cycles.device = 'CPU'
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 12
sc.cycles.transmission_bounces = 12
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


ALVO = (0.0, -0.5, 0.7)
FOTOS = {
    '0': ('bomba_agua_0.png', (ALVO[0] + 1.9, ALVO[1] - 3.1, ALVO[2] + 1.4), ALVO, 34, 1200, 1100),
    '1': ('bomba_agua_1.png', (ALVO[0] + 2.4, ALVO[1] + 2.7, ALVO[2] + 1.6), ALVO, 34, 1200, 1100),
    'perto': ('bomba_agua_perto.png', (-0.6, -2.3, 1.75), (-0.25, -1.0, -0.3), 30, 1300, 1000),
}
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
modo = args[0]
FR_FOTO = int(QUADROS * 0.3) + 1
if modo == 'foto':
    so_uma = args[1] if len(args) > 1 else None
    sc.cycles.samples = 128
    sc.frame_set(FR_FOTO)
    for chave, (nome, pos, alvo, lente, rx, ry) in FOTOS.items():
        if so_uma and chave != so_uma:
            continue
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, nome)
        bpy.ops.render.render(write_still=True)
if modo == 'rapido':
    sc.cycles.samples = 24
    sc.frame_set(FR_FOTO)
    for chave, (nome, pos, alvo, lente, rx, ry) in FOTOS.items():
        if len(args) > 1 and chave != args[1]:
            continue
        sc.render.resolution_x, sc.render.resolution_y = rx // 2, ry // 2
        mirar(pos, alvo, lente)
        sc.render.filepath = os.path.join(AQUI, 'bomba_agua_teste_%s.png' % chave)
        bpy.ops.render.render(write_still=True)
if modo == 'teste':
    v = [float(x) for x in args[1:]]
    sc.cycles.samples = 32
    sc.render.resolution_x, sc.render.resolution_y = 1000, 800
    sc.frame_set(int(QUADROS * v[7]) + 1)
    mirar(v[0:3], v[3:6], v[6])
    sc.render.filepath = os.path.join(AQUI, 'bomba_agua_teste.png')
    bpy.ops.render.render(write_still=True)
print('BOMBA_AGUA ok')
