"""Larva ácida para o jogo (glb com esqueleto): o corpo é UMA malha deformada por ossos (estudo_larva.py), o que o
para_jogo.py não trata. Aqui: monta o estudo, fica só a larva, assa a cor dos materiais (procedurais) numa textura
por peça, troca por material simples (o ácido fica aceso pela emissão) e exporta o glb com o esqueleto e duas ações:
  "andar"  — 24 quadros (1 s): uma onda de contração da cauda para a frente (o jogo toca em laço, pela distância andada);
  "cuspe"  — 24 quadros (1 s): ergue a frente, abre a boca, solta e volta.
Uso: blender -b --python exportar_larva.py"""
import bpy, bmesh, math, os, sys, json

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, '..', 'modelos', 'inimigos', 'larva', 'larva_acida')
ESTUDO = os.path.join(AQUI, 'estudo_larva.py')
sys.argv = [sys.argv[0], '--python', ESTUDO, '--', 'nada']
sys.path.insert(0, AQUI)
NS = {'__name__': '__main__', '__file__': ESTUDO}
exec(compile(open(ESTUDO, encoding='utf-8').read(), ESTUDO, 'exec'), NS)
sc = bpy.context.scene
arm = sc.objects['larva']
for o in list(sc.objects):
    if not (o is arm or o.parent is arm):
        bpy.data.objects.remove(o, do_unlink=True)
arm.animation_data_clear()
arm.location = (0, 0, 0)
arm.rotation_euler = (0, 0, 0)

# ------------------------------------------------------------------ assa a cor de cada peça numa textura
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 8
NS['pose_rastejar'](arm, 0.0, 1)
bpy.context.view_layer.update()
malhas = [o for o in arm.children if o.type == 'MESH']
for o in malhas:
    acesa = all(m and m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value > 1.0
                for m in o.data.materials if m and 'Principled BSDF' in m.node_tree.nodes and not m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].is_linked)
    if acesa and all('Acido' in m.name for m in o.data.materials if m):
        cor = o.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
        m = bpy.data.materials.new('P_Acido')
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = cor
        b.inputs['Emission Color'].default_value = cor
        b.inputs['Emission Strength'].default_value = 2.5
        o.data.materials.clear()
        o.data.materials.append(m)
        continue
    lado = 1024 if o.name.endswith(('_corpo', '_carapaca')) else 256
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    md = o.modifiers.new('reduz', 'DECIMATE')                # celular: metade dos triângulos (antes do esqueleto)
    md.ratio = 0.45 if not o.name.endswith(('_dentes', '_baba')) else 0.6
    bpy.ops.object.modifier_move_to_index(modifier='reduz', index=0)
    bpy.ops.object.modifier_apply(modifier='reduz')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    img = bpy.data.images.new(o.name + '_cor', lado, lado)
    for m in o.data.materials:
        nt = m.node_tree
        p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        p.inputs['Metallic'].default_value = 0.0
        tx = nt.nodes.new('ShaderNodeTexImage')
        tx.image = img
        nt.nodes.active = tx
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=4)
    img.pack()
    novo = bpy.data.materials.new(o.name + '_Tex')
    nt = novo.node_tree
    b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = img
    nt.links.new(tx.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.4
    o.data.materials.clear()
    o.data.materials.append(novo)

# ------------------------------------------------------------------ ações
def acao(nome, quadros, posar):
    arm.animation_data_create()
    act = bpy.data.actions.new(nome)
    arm.animation_data.action = act
    for q in range(quadros + 1):
        posar(q)
        for pb in arm.pose.bones:
            pb.keyframe_insert('location', frame=q + 1)
            pb.keyframe_insert('rotation_euler', frame=q + 1)
            pb.keyframe_insert('scale', frame=q + 1)
    act.use_fake_user = True
    tr = arm.animation_data.nla_tracks.new()
    tr.name = nome
    tr.strips.new(nome, 1, act)
    arm.animation_data.action = None


acao('andar', 24, lambda q: NS['pose_rastejar'](arm, q / 24.0, 1))
acao('cuspe', 24, lambda q: NS['pose_cuspe'](arm, None, min(1.0, q / 9.0) if q < 14 else max(0.0, 1.0 - (q - 13) / 10.0)))
NS['pose_rastejar'](arm, 0.0, 1)
sc.render.fps = 24

os.makedirs(SAIDA, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for o in malhas:
    o.select_set(True)
glb = os.path.join(SAIDA, 'larva_acida.glb')
bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_yup=True, export_animations=True,
                          export_animation_mode='NLA_TRACKS', export_skins=True, export_image_format='JPEG')
pts = [o.matrix_world @ v.co for o in malhas for v in o.data.vertices]
dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
tris = sum(len(o.data.polygons) for o in malhas)
json.dump({'nome': 'larva_acida', 'categoria': 'inimigos/larva', 'tipo': 'veiculo', 'area': [1, 1],
           'descricao': 'Larva ácida: corpo de massa única com placas de quitina, boca dentada e glândulas de ácido; anda contraindo e esticando e cospe gosma ácida.',
           'ocupa_canto': False, 'partes': [{'nome': 'corpo', 'pai': None, 'pivo': [0.0, 0.0, 0.0]}], 'portas': [],
           'tris': tris, 'dims': dims, 'anima': True, 'estudo': 'estudo_larva.py'},
          open(os.path.join(SAIDA, 'larva_acida.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('LARVA_EXPORTADA', tris, 'tris', dims)
