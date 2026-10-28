"""Extrator de Cristal (3x3 tiles, 1 tile = 1 m). Recria o modelo do zero.
Uso: blender --background --python extrator_cristal.py  (ou rodar pelo addon MCP)
"""
import bpy, math
col=bpy.data.collections.get('Extrator') or bpy.data.collections.new('Extrator')
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
def mat(n,c,e=0,r=0.7,m=0.0):
    x=bpy.data.materials.get(n) or bpy.data.materials.new(n); x.use_nodes=True
    b=x.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(*c,1); b.inputs['Roughness'].default_value=r; b.inputs['Metallic'].default_value=m
    b.inputs['Emission Strength'].default_value=e
    if e: b.inputs['Emission Color'].default_value=(*c,1)
    x.diffuse_color=(*c,1); return x
M={'metal':mat('P_Metal',(0.42,0.46,0.52),r=0.5,m=0.3),'escuro':mat('P_Escuro',(0.10,0.11,0.14)),'cobre':mat('P_Cobre',(0.78,0.42,0.20),r=0.4,m=0.5),
   'cristal':mat('P_Cristal',(0.15,1.0,0.75),4),'concreto':mat('P_Concreto',(0.36,0.35,0.33),r=0.85),'faixa':mat('P_Faixa',(0.95,0.75,0.15))}
def add(fn,nome,m,bev=0,sc=None,**k):
    fn(**k); o=bpy.context.active_object; o.name='EXT_'+nome
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o); o.data.materials.append(M[m])
    if sc: o.scale=sc; bpy.ops.object.transform_apply(scale=True)
    if bev:
        b=o.modifiers.new('bev','BEVEL'); b.width=bev; b.segments=1; b.limit_method='ANGLE'
    return o
O=bpy.ops

for o in list(bpy.data.objects):
    if o.name.startswith('EXT_'): bpy.data.objects.remove(o)
# placa 3x3 da grade (1 tile = 1 m)
add(O.mesh.primitive_cube_add,'Placa','concreto',bev=0.06,size=1,location=(0,0,0.06),sc=(3,3,0.12))
add(O.mesh.primitive_cube_add,'Base','escuro',bev=0.08,size=1,location=(0,0,0.32),sc=(2.5,2.5,0.4))
add(O.mesh.primitive_cube_add,'BaseTopo','metal',bev=0.05,size=1,location=(0,0,0.56),sc=(2.2,2.2,0.08))
add(O.mesh.primitive_cylinder_add,'Torre','metal',bev=0.04,vertices=8,radius=0.62,depth=1.3,location=(0,0,1.25),rotation=(0,0,math.pi/8))
add(O.mesh.primitive_cylinder_add,'Anel1','faixa',vertices=8,radius=0.66,depth=0.08,location=(0,0,0.75),rotation=(0,0,math.pi/8))
add(O.mesh.primitive_cylinder_add,'Anel2','escuro',vertices=8,radius=0.66,depth=0.1,location=(0,0,1.6),rotation=(0,0,math.pi/8))
# aletas encostadas por fora da torre, nas faces
for i in range(4):
    a=i*math.pi/2
    add(O.mesh.primitive_cube_add,f'Aleta{i}','escuro',bev=0.02,size=1,location=(math.cos(a)*0.66,math.sin(a)*0.66,1.2),rotation=(0,0,a),sc=(0.1,0.3,0.7))
add(O.mesh.primitive_cone_add,'Topo','metal',bev=0.03,vertices=8,radius1=0.62,radius2=0.3,depth=0.35,location=(0,0,2.075),rotation=(0,0,math.pi/8))
add(O.mesh.primitive_cylinder_add,'Gola','escuro',vertices=8,radius=0.34,depth=0.1,location=(0,0,2.29),rotation=(0,0,math.pi/8))
# cacho de cristais
add(O.mesh.primitive_cone_add,'Cristal','cristal',vertices=6,radius1=0.22,radius2=0,depth=0.9,location=(0,0,2.75))
add(O.mesh.primitive_cone_add,'Cristal2','cristal',vertices=6,radius1=0.13,radius2=0,depth=0.5,location=(0.17,0.05,2.55),rotation=(0,0.45,0))
add(O.mesh.primitive_cone_add,'Cristal3','cristal',vertices=6,radius1=0.11,radius2=0,depth=0.42,location=(-0.12,-0.13,2.52),rotation=(0.4,-0.3,0))
# pistões nos cantos, ligados à torre por braços
for i in range(4):
    a=math.pi/4+i*math.pi/2; x,y=math.cos(a)*1.25,math.sin(a)*1.25
    add(O.mesh.primitive_cylinder_add,f'PistaoCamisa{i}','escuro',vertices=6,radius=0.17,depth=0.45,location=(x,y,0.82))
    add(O.mesh.primitive_cylinder_add,f'PistaoHaste{i}','cobre',vertices=6,radius=0.09,depth=0.6,location=(x,y,1.3))
    add(O.mesh.primitive_cube_add,f'Braco{i}','metal',bev=0.02,size=1,location=(math.cos(a)*0.93,math.sin(a)*0.93,1.62),rotation=(0,0,a),sc=(0.72,0.14,0.1))
# saída na borda sul da grade (y=-1.5)
add(O.mesh.primitive_cube_add,'Saida','escuro',bev=0.03,size=1,location=(0,-1.32,0.45),sc=(0.6,0.36,0.5))
add(O.mesh.primitive_cube_add,'SaidaBoca','cristal',size=1,location=(0,-1.505,0.42),sc=(0.4,0.02,0.24))
for o in bpy.context.selected_objects: o.select_set(False)
for o in col.objects:
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=False
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces[0].shading.type='MATERIAL'

# cano único com curva
pts=[(0,-0.55,1.0),(0,-1.1,1.0)]
r=0.15
for i in range(1,4):
    t=math.radians(30*i); pts.append((0,-1.1-r*math.sin(t),0.85+r*math.cos(t)))
pts.append((0,-1.25,0.66))
cu=bpy.data.curves.new('EXT_Cano','CURVE'); cu.dimensions='3D'
sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
for p,c in zip(sp.points,pts): p.co=(*c,1)
cu.bevel_depth=0.09; cu.bevel_resolution=1; cu.use_fill_caps=True
o=bpy.data.objects.new('EXT_Cano',cu); col.objects.link(o)
for x in bpy.context.selected_objects: x.select_set(False)
bpy.context.view_layer.objects.active=o; o.select_set(True)
bpy.ops.object.convert(target='MESH')
o=bpy.context.active_object; o.data.materials.append(bpy.data.materials['P_Cobre'])
for p in o.data.polygons: p.use_smooth=False
o.select_set(False)
