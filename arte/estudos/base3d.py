"""Funções comuns dos estudos isolados: materiais especiais (listras, lâmpada, volume) e geometria (caixa, cilindro,
tubo, viga, bézier, mangueira, pedra, mancha). O estudo preenche base3d.M com os materiais antes de criar objetos."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

PI = math.pi
M = {}
sc = None


def iniciar():
    global sc
    sc = bpy.context.scene
    return sc

def listras_mat():
    m = bpy.data.materials.new('Listras')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type, wave.bands_direction, wave.wave_profile = 'BANDS', 'DIAGONAL', 'SAW'
    wave.inputs['Scale'].default_value = 7.0
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    corte = nt.nodes.new('ShaderNodeMath')
    corte.operation = 'GREATER_THAN'
    corte.inputs[1].default_value = 0.5
    nt.links.new(wave.outputs['Fac'], corte.inputs[0])
    sujo = nt.nodes.new('ShaderNodeTexNoise')
    sujo.inputs['Scale'].default_value = 14.0
    nt.links.new(tc.outputs['Object'], sujo.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (0.03, 0.03, 0.03, 1)
    mix.inputs[7].default_value = (0.62, 0.42, 0.04, 1)
    nt.links.new(corte.outputs['Value'], mix.inputs[0])
    gasto = nt.nodes.new('ShaderNodeMix')
    gasto.data_type, gasto.blend_type = 'RGBA', 'MULTIPLY'
    gasto.inputs[0].default_value = 0.5
    nt.links.new(mix.outputs[2], gasto.inputs[6])
    nt.links.new(sujo.outputs['Color'], gasto.inputs[7])
    nt.links.new(gasto.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    return m


def lampada_mat():
    m = bpy.data.materials.new('Lâmpada')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1.0, 0.45, 0.05, 1)
    b.inputs['Emission Color'].default_value = (1.0, 0.42, 0.04, 1)
    b.inputs['Emission Strength'].default_value = 6.0
    return m


def volume_mat(nome, cor, dens, z0, z1):
    """Volume com ruído; a densidade some conforme sobe (z0 → z1 no mundo): fumaça e poeira que se desfazem."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (*cor, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ru = nt.nodes.new('ShaderNodeTexNoise')
    ru.inputs['Scale'].default_value = 3.0
    ru.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    forma = nt.nodes.new('ShaderNodeMapRange')                 # bolha: some na borda da esfera
    forma.inputs['From Min'].default_value = 0.42
    forma.inputs['From Max'].default_value = 0.68
    nt.links.new(ru.outputs['Fac'], forma.inputs['Value'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    sobe = nt.nodes.new('ShaderNodeMapRange')
    sobe.inputs['From Min'].default_value = z0
    sobe.inputs['From Max'].default_value = z1
    sobe.inputs['To Min'].default_value = dens
    sobe.inputs['To Max'].default_value = 0.0
    nt.links.new(sep.outputs['Z'], sobe.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(forma.outputs['Result'], mul.inputs[0])
    nt.links.new(sobe.outputs['Result'], mul.inputs[1])
    nt.links.new(mul.outputs['Value'], vol.inputs['Density'])
    return m




# ------------------------------------------------------------------ geometria
def obj(nome, bm, mat, pai=None):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    o.data.materials.append(M[mat])
    if pai is not None:
        o.parent = pai
    return o


def caixa(bm, centro, tam, rot=Matrix.Identity(3)):
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res['verts']:
        v.co = Vector(centro) + rot @ Vector((v.co.x * tam[0], v.co.y * tam[1], v.co.z * tam[2]))
    return res['verts']


def caixa_de(bm, a, b):
    """Caixa alinhada aos eixos entre os cantos a e b."""
    a, b = Vector(a), Vector(b)
    caixa(bm, (a + b) / 2, tuple(abs(b[i] - a[i]) for i in range(3)))


def cil(bm, centro, r, h, eixo=Vector((0, 0, 1)), lados=12, r2=None):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=r, radius2=r if r2 is None else r2, depth=h,
                          matrix=Matrix.Translation(centro) @ q)


def tubo(bm, a, b, r, lados=8):
    a, b = Vector(a), Vector(b)
    cil(bm, (a + b) / 2, r, (b - a).length, b - a, lados)


def viga(bm, a, b, w):
    """Barra quadrada de a até b."""
    a, b = Vector(a), Vector(b)
    q = (b - a).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((a + b) / 2) @ q @ Matrix.Diagonal((w, w, (b - a).length, 1)))


def bezier(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    return [p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3
            for t in (i / n for i in range(n + 1))]


def mangueira(bm, pts, r):
    for a, b in zip(pts, pts[1:]):
        u = (b - a).normalized()
        tubo(bm, a - u * r * 0.6, b + u * r * 0.6, r, 6)


def pedra(bm, centro, r, achatar=0.6):
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    rot = Matrix.Rotation(random.uniform(0, 2 * PI), 3, 'Z') @ Matrix.Rotation(random.uniform(-0.5, 0.5), 3, 'X')
    for v in res['verts']:
        c = v.co * random.uniform(0.75, 1.2)
        c.z *= achatar
        v.co = Vector(centro) + rot @ c



def mancha(bm, centro, r, z):
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=14, radius=r)
    for v in res['verts']:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 + 0.35 * math.sin(a * 3 + random.random()) + 0.15 * random.random()
        v.co = Vector((centro[0] + v.co.x * f, centro[1] + v.co.y * f * random.uniform(0.6, 1.0), z))


