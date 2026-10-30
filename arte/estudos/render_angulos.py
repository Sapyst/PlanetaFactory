import sys, os, math, bpy
sys.path.insert(0, '/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/blender_scripts')
import lib_pf
from lib_pf import preparar_cena, render
aqui = os.path.dirname(os.path.abspath(__file__))
glb = os.path.join(aqui, 'modelos', 'estudos', 'braco_detalhado', 'braco_detalhado.glb')
for i, ang in enumerate((0, 90, 200, 300)):
    sc = preparar_cena()
    sc.display.shading.color_type = 'TEXTURE'
    bpy.ops.import_scene.gltf(filepath=glb)
    objs = [o for o in sc.objects if o.type == 'MESH']
    raiz = [o for o in sc.objects if o.parent is None]
    for o in raiz:
        o.rotation_euler[2] += math.radians(ang)
    bpy.context.view_layer.update()
    render(objs, os.path.join(aqui, 'angulo_%d.png' % i), res=(720, 720), margem=1.05)
print('ANGULOS ok')
