"""Base comum dos estudos de LÓGICA do lote 16 (sensor de esteira, sensor de tanque, comparador, válvula): monta o
estudo dos canos aprovado (estudo_canos.py) só para ter os materiais e as peças prontas dele (flange aparafusada,
suporte, manômetro, remendo, número de série, fiação exposta, pingo), apaga a cena dele e devolve o namespace.
Também: luz animável, chão/sol/câmera e fotos (só no modo foto)."""
import bpy, bmesh, math, os, sys
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))


def preparar():
    base = os.path.join(AQUI, 'estudo_canos.py')
    argv = sys.argv
    sys.argv = [argv[0], '--python', base, '--', 'nada']
    g = {'__name__': '__main__', '__file__': base}
    exec(compile(open(base, encoding='utf-8').read(), base, 'exec'), g)
    sys.argv = argv
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    g['GOTAS'].clear()
    g['GAUGES'].clear()
    return g


def luz(g, chave, nome, cor, LUZ):
    """Material emissivo com força animável (LUZ[chave] = nó Principled)."""
    import base3d
    m = g['emissivo'](nome, cor, 0.0)
    LUZ[chave] = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    base3d.M[chave] = m


def chave_luz(LUZ, chave, forca, q):
    inp = LUZ[chave].inputs['Emission Strength']
    inp.default_value = forca
    inp.keyframe_insert('default_value', frame=q)


def gotas_e_ponteiros(g, quadros):
    """Anima os pingos e os ponteiros dos manômetros criados pelas peças prontas do estudo dos canos."""
    import base3d
    from mathutils import Matrix
    for e, n, fase in g['GAUGES']:
        for q in range(1, quadros + 1):
            e.rotation_mode = 'QUATERNION'
            e.rotation_quaternion = n.to_track_quat('Z', 'Y') @ Matrix.Rotation(fase + 0.05 * math.sin(q * 1.7), 4, 'Z').to_quaternion()
            e.keyframe_insert('rotation_quaternion', frame=q)
    for p, mat, vezes, fase in g['GOTAS']:
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.009)
        o = base3d.obj('gota', bm, mat)
        for q in range(1, quadros + 1):
            u = ((q - 1) / quadros * vezes + fase) % 1.0
            t = max(0.0, u - 0.6) / 0.4 * 0.45
            o.location = p - Vector((0, 0, 0.011 + 4.9 * t * t))
            o.scale = (0.85, 0.85, 1.25) if u > 0.3 else (0.05 + u,) * 3
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('scale', frame=q)


def linear():
    for o in list(bpy.context.scene.objects) + list(bpy.data.materials):
        ad = (o.node_tree.animation_data if o.node_tree else None) if isinstance(o, bpy.types.Material) else o.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, 'fcurves', []):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'


def cena(lado=12.0):
    import base3d
    sc = bpy.context.scene
    bm = bmesh.new()
    base3d.caixa(bm, (0, 0, -0.5), (lado, lado, 1.0))
    base3d.obj('chao', bm, 'chao')
    sol = bpy.data.lights.new('Sol', 'SUN')
    sol.energy = 4.0
    sol.angle = math.radians(2.5)
    so = bpy.data.objects.new('Sol', sol)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(-35))
    cd = bpy.data.cameras.new('Cam')
    cam = bpy.data.objects.new('Cam', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.clip_start = 0.01
    return cam


def fotos(modo, cam, fotos, quadro=1):
    """fotos = {nome: (pos, alvo, lente, rx, ry)}; só renderiza no modo foto/teste."""
    if modo not in ('foto', 'teste'):
        return
    sc = bpy.context.scene
    sc.cycles.samples = 128 if modo == 'foto' else 24
    sc.frame_set(quadro)
    for nome, (pos, alvo, lente, rx, ry) in fotos.items():
        if modo == 'teste':
            rx, ry = rx // 2, ry // 2
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        cam.location = pos
        cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lente
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
