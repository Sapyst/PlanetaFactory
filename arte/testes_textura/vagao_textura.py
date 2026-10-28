"""Teste de textura: vagão de carga com pintura de metal gasta, assada numa textura só (1024²).
Lê o vagão do pipeline (não altera o original) e grava em arte/testes_textura/vagao_carga_tex/:
  vagao_carga_tex.png (textura), vagao_carga_tex.glb (modelo com a textura), antes_depois.png (comparação).
Procedural por material da paleta: sujeira mais forte embaixo, escorridos verticais, bordas raspadas (nó Bevel:
onde a normal arredondada difere da real = quina), ferrugem em manchas, placas e rebites no corpo de cobre.
Uso: blender -b --factory-startup --python vagao_textura.py"""
import bpy, os, math
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, 'vagao_carga_tex')
ORIGEM = os.path.join(AQUI, '..', 'modelos', 'transporte', 'veiculos', 'vagao_carga', 'vagao_carga.glb')
TAM = 1024
os.makedirs(SAIDA, exist_ok=True)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=ORIGEM)
sc = bpy.context.scene
if sc.world is None:
    sc.world = bpy.data.worlds.new('W')
objs = [o for o in sc.objects if o.type == 'MESH']
for o in sc.objects:
    o.hide_render = o.type == 'MESH' and o not in objs
print('OBJETOS', [o.name for o in objs], [m.name for o in objs for m in o.data.materials])


# ------------------------------------------------------------------ render "antes"
def render(arquivo, tipo):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = tipo
    sh.show_object_outline = True
    sh.object_outline_color = (0.02, 0.02, 0.02)
    sh.show_cavity = True
    sc.render.film_transparent = False
    sc.world.color = (0.16, 0.17, 0.19)
    sc.render.resolution_x, sc.render.resolution_y = 900, 640
    cam = sc.camera
    if cam is None:
        cam = bpy.data.objects.new('CAM', bpy.data.cameras.new('CAM'))
        sc.collection.objects.link(cam)
        sc.camera = cam
    cam.data.type = 'PERSP'
    cam.data.lens = 60
    alvo = Vector((0, 0, 0.42))
    cam.location = alvo + Vector((3.6, -2.9, 2.1))
    cam.rotation_euler = (alvo - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = arquivo
    bpy.ops.render.render(write_still=True)


render(os.path.join(SAIDA, '_antes.png'), 'MATERIAL')

# ------------------------------------------------------------------ UV: um atlas para todas as peças
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
    if not o.data.uv_layers:
        o.data.uv_layers.new(name='atlas')
    o.data.uv_layers.active = o.data.uv_layers[0]
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.012, scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')

img = bpy.data.images.new('vagao_carga_tex', TAM, TAM, alpha=False)
img.colorspace_settings.name = 'sRGB'


# ------------------------------------------------------------------ materiais procedurais (para assar)
def no(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k == 'loc':
            n.location = v
        else:
            setattr(n, k, v)
    return n


def mix(nt, a, b, fac, modo='MIX'):
    m = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type=modo)
    nt.links.new(fac, m.inputs[0])
    nt.links.new(a, m.inputs[6]) if not isinstance(a, (tuple, list)) else None
    if isinstance(a, (tuple, list)):
        m.inputs[6].default_value = (*a, 1)
    if isinstance(b, (tuple, list)):
        m.inputs[7].default_value = (*b, 1)
    else:
        nt.links.new(b, m.inputs[7])
    return m.outputs[2]


def faixa(nt, entrada, de, ate):
    r = no(nt, 'ShaderNodeMapRange')
    r.inputs[1].default_value = de
    r.inputs[2].default_value = ate
    nt.links.new(entrada, r.inputs[0])
    return r.outputs[0]


def procedural(mat):
    base = tuple(mat.diffuse_color[:3])
    if mat.use_nodes and mat.node_tree.nodes.get('Principled BSDF'):
        base = tuple(mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3])
    nome = mat.name
    pintado = nome in ('P_Cobre', 'P_Escuro', 'P_Faixa')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    saida = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfDiffuse')
    nt.links.new(bsdf.outputs[0], saida.inputs[0])
    coord = no(nt, 'ShaderNodeTexCoord').outputs['Object']
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(coord, sep.inputs[0])
    cor = base
    # variação de tom grande (pintura desigual)
    n1 = no(nt, 'ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 2.2
    n1.inputs['Detail'].default_value = 3
    nt.links.new(coord, n1.inputs['Vector'])
    tom = mix(nt, base, tuple(c * 0.82 for c in base), faixa(nt, n1.outputs['Fac'], 0.35, 0.75))
    cor = tom
    # placas e rebites no corpo de cobre (painéis de 0,6 m ao longo do vagão)
    if nome == 'P_Cobre':
        onda = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y')
        onda.inputs['Scale'].default_value = 0.52                 # placas de ~0,6 m
        onda.inputs['Distortion'].default_value = 0.0
        nt.links.new(coord, onda.inputs['Vector'])
        junta = faixa(nt, onda.outputs['Fac'], 0.985, 1.0)
        cor = mix(nt, cor, (0.20, 0.10, 0.05), junta)
        reb = no(nt, 'ShaderNodeTexVoronoi', feature='F1')
        reb.inputs['Scale'].default_value = 26.0
        nt.links.new(coord, reb.inputs['Vector'])
        pino = faixa(nt, reb.outputs['Distance'], 0.12, 0.05)
        cor = mix(nt, cor, tuple(min(1, c * 1.25) for c in base), pino)
    # escorridos verticais (chuva/óleo): ruído esticado em Z
    esc = no(nt, 'ShaderNodeTexNoise')
    esc.inputs['Scale'].default_value = 9.0
    esc.inputs['Detail'].default_value = 2
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, 0.12)
    nt.links.new(coord, mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], esc.inputs['Vector'])
    cor = mix(nt, cor, (0.08, 0.07, 0.06), faixa(nt, esc.outputs['Fac'], 0.58, 0.85), 'MIX')
    # sujeira de baixo para cima (poeira da linha)
    baixo = faixa(nt, sep.outputs['Z'], 0.55, 0.12)
    n2 = no(nt, 'ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 14.0
    nt.links.new(coord, n2.inputs['Vector'])
    poeira = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(baixo, poeira.inputs[0])
    nt.links.new(faixa(nt, n2.outputs['Fac'], 0.3, 0.7), poeira.inputs[1])
    meia = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(poeira.outputs[0], meia.inputs[0])
    meia.inputs[1].default_value = 0.55                      # poeira sem apagar a cor da peça
    cor = mix(nt, cor, (0.30, 0.25, 0.20), meia.outputs[0])
    if pintado:
        # ferrugem em manchas
        fe = no(nt, 'ShaderNodeTexNoise')
        fe.inputs['Scale'].default_value = 5.5
        fe.inputs['Detail'].default_value = 6
        fe.inputs['Roughness'].default_value = 0.7
        nt.links.new(coord, fe.inputs['Vector'])
        cor = mix(nt, cor, (0.34, 0.15, 0.06), faixa(nt, fe.outputs['Fac'], 0.62, 0.72))
        # quinas raspadas: normal arredondada (Bevel) ≠ normal da face
        bev = no(nt, 'ShaderNodeBevel', samples=8)
        bev.inputs['Radius'].default_value = 0.025
        geo = no(nt, 'ShaderNodeNewGeometry')
        dot = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
        nt.links.new(bev.outputs[0], dot.inputs[0])
        nt.links.new(geo.outputs['Normal'], dot.inputs[1])
        quina = faixa(nt, dot.outputs['Value'], 0.96, 0.82)
        n3 = no(nt, 'ShaderNodeTexNoise')
        n3.inputs['Scale'].default_value = 40.0
        nt.links.new(coord, n3.inputs['Vector'])
        raspa = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(quina, raspa.inputs[0])
        nt.links.new(faixa(nt, n3.outputs['Fac'], 0.5, 0.68), raspa.inputs[1])
        cor = mix(nt, cor, (0.46, 0.45, 0.44), raspa.outputs[0])
    nt.links.new(cor, bsdf.inputs['Color'])
    alvo = no(nt, 'ShaderNodeTexImage')
    alvo.image = img
    nt.nodes.active = alvo


feitos = set()
for o in objs:
    for m in o.data.materials:
        if m and m.name not in feitos:
            procedural(m)
            feitos.add(m.name)

# ------------------------------------------------------------------ assar só a cor
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 16
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=8, use_clear=True)
img.filepath_raw = os.path.join(SAIDA, 'vagao_carga_tex.png')
img.file_format = 'PNG'
img.save()
print('ASSADO', img.filepath_raw)

# ------------------------------------------------------------------ material final: uma textura só
final = bpy.data.materials.new('P_VagaoTex')
final.use_nodes = True
pb = final.node_tree.nodes['Principled BSDF']
tx = final.node_tree.nodes.new('ShaderNodeTexImage')
tx.image = img
final.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
pb.inputs['Roughness'].default_value = 0.62
pb.inputs['Metallic'].default_value = 0.25
for o in objs:
    o.data.materials.clear()
    o.data.materials.append(final)

render(os.path.join(SAIDA, '_depois.png'), 'TEXTURE')
bpy.ops.export_scene.gltf(filepath=os.path.join(SAIDA, 'vagao_carga_tex.glb'), export_format='GLB', use_selection=False,
                          export_yup=True, export_image_format='AUTO')

# ------------------------------------------------------------------ antes | depois lado a lado
a = bpy.data.images.load(os.path.join(SAIDA, '_antes.png'))
b = bpy.data.images.load(os.path.join(SAIDA, '_depois.png'))
w, h = a.size
lado = bpy.data.images.new('lado', w * 2, h)
pa = list(a.pixels)
pb_ = list(b.pixels)
px = [0.0] * (w * 2 * h * 4)
for y in range(h):
    px[y * w * 2 * 4: y * w * 2 * 4 + w * 4] = pa[y * w * 4: (y + 1) * w * 4]
    px[y * w * 2 * 4 + w * 4: (y + 1) * w * 2 * 4] = pb_[y * w * 4: (y + 1) * w * 4]
lado.pixels[:] = px
lado.filepath_raw = os.path.join(SAIDA, 'antes_depois.png')
lado.file_format = 'PNG'
lado.save()
print('PRONTO')
