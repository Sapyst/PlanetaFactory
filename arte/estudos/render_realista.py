"""Estudo: o braço detalhado com materiais físicos realistas (Cycles), sem textura assada. Troca cada material da
paleta (P_*) por um procedural: pintura gasta nas quinas (o metal aparece), sujeira nas frestas (oclusão),
aço escovado com ferrugem, cromado na haste, cobre escurecido, borracha. Chão de concreto, sol e céu.
Uso: blender -b --factory-startup --python render_realista.py"""
import bpy, os, math
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(AQUI, 'modelos', 'estudos', 'braco_detalhado', 'braco_detalhado_sem_textura.glb')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'GPU'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
except Exception:
    sc.cycles.device = 'CPU'
sc.cycles.samples = 96
sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -1.3
sc.render.resolution_x = 1100
sc.render.resolution_y = 1100
sc.render.film_transparent = False


def no(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def material(nome, base, metal, rough, pintura=True, ferrugem=0.0, sujeira=0.6, desgaste=0.6, escovado=False):
    """Pintura (ou metal) com: quinas gastas mostrando metal, sujeira nas frestas, variação de brilho e ferrugem."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    coord = no(nt, 'ShaderNodeTexCoord')
    # ruídos: manchas grandes (sujeira/ferrugem), fino (brilho), riscos (escovado)
    grande = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 8.0, 'Roughness': 0.6})
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 90.0, 'Detail': 4.0})
    nt.links.new(coord.outputs['Object'], grande.inputs['Vector'])
    nt.links.new(coord.outputs['Object'], fino.inputs['Vector'])
    # quinas: diferença entre a normal real e a normal arredondada (bevel)
    bev = no(nt, 'ShaderNodeBevel', samples=8)
    bev.inputs['Radius'].default_value = 0.006
    geo = no(nt, 'ShaderNodeNewGeometry')
    dot = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    nt.links.new(bev.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Normal'], dot.inputs[1])
    quina = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.995, 'From Max': 0.9, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(dot.outputs['Value'], quina.inputs['Value'])
    gasta = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(quina.outputs['Result'], gasta.inputs[0])
    gasta.inputs[1].default_value = desgaste * 1.1
    lasca = no(nt, 'ShaderNodeMath', operation='MULTIPLY')            # lascas: quina × ruído
    nt.links.new(gasta.outputs['Value'], lasca.inputs[0])
    nt.links.new(grande.outputs['Fac'], lasca.inputs[1])
    lasca_c = no(nt, 'ShaderNodeMath', operation='GREATER_THAN')
    nt.links.new(lasca.outputs['Value'], lasca_c.inputs[0])
    lasca_c.inputs[1].default_value = 0.45
    # sujeira nas frestas (oclusão ambiente)
    ao = no(nt, 'ShaderNodeAmbientOcclusion', samples=16)
    ao.inputs['Distance'].default_value = 0.08
    suj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.85, 'From Max': 0.3, 'To Min': 0.0, 'To Max': sujeira})
    nt.links.new(ao.outputs['AO'], suj.inputs['Value'])
    # cor: base → (lasca) metal nu → (sujeira) marrom-escuro; ferrugem nas manchas
    metal_nu = (0.52, 0.52, 0.5, 1)
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c1.inputs[6].default_value = (*base, 1)
    c1.inputs[7].default_value = metal_nu
    nt.links.new(lasca_c.outputs['Value'], c1.inputs[0])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.25
    nt.links.new(c1.outputs[2], var.inputs[6])
    nt.links.new(grande.outputs['Color'], var.inputs[7])
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c2.inputs[7].default_value = (0.06, 0.045, 0.03, 1)
    nt.links.new(suj.outputs['Result'], c2.inputs[0])
    nt.links.new(var.outputs[2], c2.inputs[6])
    cor_final = c2.outputs[2]
    if ferrugem > 0:
        fr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.62, 'From Max': 0.72, 'To Min': 0.0, 'To Max': ferrugem})
        nt.links.new(grande.outputs['Fac'], fr.inputs['Value'])
        c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
        c3.inputs[7].default_value = (0.32, 0.12, 0.04, 1)
        nt.links.new(fr.outputs['Result'], c3.inputs[0])
        nt.links.new(cor_final, c3.inputs[6])
        cor_final = c3.outputs[2]
    nt.links.new(cor_final, bsdf.inputs['Base Color'])
    # metálico: pintura não é metal, a lasca é
    if pintura:
        mt = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(lasca_c.outputs['Value'], mt.inputs[0])
        mt.inputs[1].default_value = 0.9
        nt.links.new(mt.outputs['Value'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Metallic'].default_value = metal
    # brilho: base ± ruído fino; sujeira deixa fosco; escovado: riscos alongados
    r = no(nt, 'ShaderNodeMapRange', **{'To Min': rough * 0.75, 'To Max': rough * 1.25})
    nt.links.new(fino.outputs['Fac'], r.inputs['Value'])
    rs = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(r.outputs['Result'], rs.inputs[0])
    nt.links.new(suj.outputs['Result'], rs.inputs[1])
    nt.links.new(rs.outputs['Value'], bsdf.inputs['Roughness'])
    if escovado:
        wave = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z')
        wave.inputs['Scale'].default_value = 60.0
        wave.inputs['Distortion'].default_value = 8.0
        nt.links.new(coord.outputs['Object'], wave.inputs['Vector'])
        bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.05})
        nt.links.new(wave.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


MATS = {
    'P_Faixa': material('Pintura amarela', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.8, sujeira=0.7),
    'P_Escuro': material('Pintura grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.5),
    'P_Aco': material('Aço', (0.42, 0.43, 0.44), 1.0, 0.38, pintura=False, ferrugem=0.7, sujeira=0.6, escovado=True),
    'P_Metal': material('Cromado', (0.85, 0.86, 0.88), 1.0, 0.12, pintura=False, sujeira=0.35),
    'P_Cobre': material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.8),
    'P_Concreto': material('Concreto', (0.36, 0.35, 0.33), 0, 0.85, sujeira=0.4),
}

bpy.ops.import_scene.gltf(filepath=GLB)
objs = [o for o in sc.objects if o.type == 'MESH']
for o in objs:
    for i, s in enumerate(o.material_slots):
        nome = s.material.name.split('.')[0] if s.material else ''
        if nome in MATS:
            s.material = MATS[nome]
    for p in o.data.polygons:
        p.use_smooth = False
# chão de concreto
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.001))
chao = sc.objects[-1] if False else bpy.context.active_object
chao.data.materials.append(material('Chão', (0.16, 0.155, 0.145), 0, 0.9, sujeira=0.3, desgaste=0.0))
# luz: sol forte e céu
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.2
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), 0, math.radians(35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
mundo.use_nodes = True
ceu = mundo.node_tree.nodes.new('ShaderNodeTexSky')
ceu.sky_type = 'NISHITA' if hasattr(ceu, 'sky_type') and 'NISHITA' in [i.identifier for i in ceu.bl_rna.properties['sky_type'].enum_items] else ceu.sky_type
bg = mundo.node_tree.nodes['Background']
bg.inputs['Strength'].default_value = 0.22
mundo.node_tree.links.new(ceu.outputs[0], bg.inputs['Color'])
# câmera em volta
alvo = Vector((0, 0.08, 0.45))
cam_d = bpy.data.cameras.new('Cam')
cam_d.lens = 70
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
for i, ang in enumerate((215, 300, 35, 125)):
    a = math.radians(ang)
    cam.location = alvo + Vector((math.cos(a) * 2.6, math.sin(a) * 2.6, 1.55))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(AQUI, 'realista_%d.png' % i)
    bpy.ops.render.render(write_still=True)
print('REALISTA ok')
