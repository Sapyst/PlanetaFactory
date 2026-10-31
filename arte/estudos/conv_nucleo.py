"""Entrada do para_jogo.py para a CHEGADA DO NÚCLEO (fase 2.6 do docs/PLANO_INTEGRACAO.md, item 3).

Núcleo em queda (nucleo_queda) ← estudo_nucleo_queda.py: o mesmo modelo de estudo_nucleo.py fechado como cápsula
  (pétalas recolhidas em saia ablativa, ogiva por cima), com a linha do tempo de 10 s (240 quadros) exportada como a
  animação "chegada": impacto no quadro 60 (cratera, torrões e pedras), ogiva ejetada (80–100), pétalas cravando no
  chão (95–150), cabos-raiz (128–170), esteiras saindo das gargantas (165–195), monólito subindo e anéis abrindo
  (165–205) e, no quadro 240, a pose do quadro 1 do laço do núcleo do jogo (estudo_nucleo.py) — a abertura troca a
  cápsula pelo núcleo de verdade ali.
  O deslocamento da queda (a cápsula vindo de 38 m, inclinada) e o tranco do impacto saem: quem leva a cápsula do
  alto até o chão é a abertura do jogo (cenas/abertura.gd), que já fazia a descida abaixo das nuvens. Saem o fogo da
  reentrada, o rastro de fumaça e a poeira (volumes; o jogo tem os seus), o chão, a câmera e o sol. A brasa das placas
  (emissão animada no material) não passa para o glTF: o brilho da reentrada é o do jogo (sprite de calor e rastro).
  Ver `_preparar`: é ela que faz a cápsula sair assada e a pose final bater com o núcleo do jogo.
Rodar: blender -b --python para_jogo.py -- nucleo_queda"""
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_defesa_energia', os.path.join(AQUI, 'conv_defesa_energia.py'))
_de = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_de)
sys.modules.setdefault('conv_defesa_energia', _de)


def _parar_capsula():
    """A abertura do jogo faz a descida: a cápsula fica na origem (antes da limpeza, que tiraria o que está no alto)."""
    import bpy
    cap = bpy.data.objects.get('capsula')
    if cap is not None:
        cap.animation_data_clear()
        cap.location = (0, 0, 0)
        cap.rotation_mode = 'QUATERNION'
        cap.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()


def _curvas_fora(o, props):
    """Tira as curvas destas propriedades da ação do objeto (Blender 5: as curvas ficam no canal do slot)."""
    from bpy_extras import anim_utils
    ad = o.animation_data
    if not ad or not ad.action:
        return
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    if cb:
        for fc in [fc for fc in cb.fcurves if fc.data_path in props]:
            cb.fcurves.remove(fc)


def _preparar():
    """Roda antes da limpeza do para_jogo, com a cena do estudo completa.

    1. Brasa: a reentrada liga Emission Strength a um nó em ogiva e placas ablativas. `brilha()` vê a ligação e trata a
       malha inteira como luz: material liso P_Fogo e redução a 200 tris. Era o "cone laranja chapado". Sem a ligação, as
       placas são assadas, com a mancha da brasa como queimado na cor; o calor é o do jogo (sprite e rastro, cenas/abertura.gd).
    2. Materiais animados valem pelo quadro 1, com o cristal e as frestas apagados: sairiam assados e na troca pelo núcleo
       viravam luz de repente. Ficam acesos, como no núcleo.
    3. hide_render não passa para o glTF. O que nasce escondido era apagado pela limpeza (cabos-raiz, fragmentos, terra das
       pétalas, cratera, que brotavam só na troca) e o que some no meio ficava (a ogiva parada no ar a 4,5 m depois de
       ejetada). Vira escala quase zero na animação.
    4. Mesmo recorte do núcleo (ajustes_fase5.py), para a pose final bater com ele na troca."""
    import bpy
    from conv_defesa_energia import _g
    sc = bpy.context.scene
    for m in bpy.data.materials:
        nt = m.node_tree
        if not nt:
            continue
        nt.animation_data_clear()
        p = nt.nodes.get('Principled BSDF')
        if p is None:
            continue
        e = p.inputs['Emission Strength']
        for l in list(e.links):                     # brasa: sai da luz e fica como queimado na cor assada, com a mesma mancha
            mascara = l.from_node.inputs[0].links[0].from_socket
            nt.links.remove(l)
            e.default_value = 0.0
            base = p.inputs['Base Color']
            mix = nt.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.inputs['B'].default_value = (0.62, 0.20, 0.035, 1)
            if base.links:
                nt.links.new(base.links[0].from_socket, mix.inputs['A'])
            else:
                mix.inputs['A'].default_value = base.default_value
            nt.links.new(mascara, mix.inputs['Factor'])
            nt.links.new(mix.outputs['Result'], base)
        if m.name.split('.')[0] == 'Cristal':
            e.default_value = 3.0
        elif m.name.split('.')[0] == 'Fresta':
            e.default_value = 6.0
    # os escorridos da ogiva nascem virados para dentro: o jogo não desenha o verso e eles sumiam
    import bmesh
    from mathutils import Vector
    o = bpy.data.objects.get('ogiva_queimado')
    if o is not None:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        for f in bm.faces:
            c = f.calc_center_median()
            if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
                f.normal_flip()
        bm.to_mesh(o.data)
        bm.free()
    SAI = ('fogo', 'rastro', 'poeira', 'calor', 'chao', 'pedras', 'torroes', 'rachaduras')
    NAO_CORTA = ('petala', 'pistao', 'ogiva', 'tampa', 'minerio', 'fragmento', 'arco', 'anel', 'monolito')
    sc.frame_set(240)
    corta = [o for o in sc.objects if o.type == 'MESH' and not o.name.lower().startswith(NAO_CORTA) and not any(t in o.name.lower() for t in SAI)]
    _g()['cortar_fixos'](corta, (-1.53, 1.53, -1.53, 1.53))
    com_hide = []
    for o in sc.objects:
        ad = o.animation_data
        if ad and ad.action and not any(t in o.name.lower() for t in SAI):
            from bpy_extras import anim_utils
            cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
            if cb and any(fc.data_path == 'hide_render' for fc in cb.fcurves):
                com_hide.append(o)
    pose = {o.name: [] for o in com_hide}
    for q in range(1, 241):
        sc.frame_set(q)
        for o in com_hide:
            pose[o.name].append((o.hide_render, o.scale.copy()))
    for o in com_hide:
        _curvas_fora(o, ('hide_render', 'hide_viewport'))
        o.hide_render = False
        o.hide_viewport = False
        if o.type != 'MESH':
            continue
        for q, (esc, s) in enumerate(pose[o.name], 1):
            o.scale = (1e-4, 1e-4, 1e-4) if esc else s
            o.keyframe_insert('scale', frame=q)
    sc.frame_set(1)
    bpy.context.view_layer.update()


CONFIG = {
    'nucleo_queda': dict(script='conv_nucleo.py', args=['nucleo_queda'], estudo='estudo_nucleo_queda.py', cat='maquinas', tris=16000, tex=1024,
                         tirar=['fogo', 'rastro', 'poeira', 'labareda', 'pedras', 'torroes', 'rachaduras'],
                         quadros=240, animacao='chegada', por_peca=True, sem_escala_animada=True),
}


if __name__ == '__main__' and 'nucleo_queda' in sys.argv:
    caminho = os.path.join(AQUI, 'estudo_nucleo_queda.py')
    sys.argv = [sys.argv[0], '--python', caminho, '--', 'nada']
    sys.path.insert(0, AQUI)
    exec(compile(open(caminho, encoding='utf-8').read(), caminho, 'exec'), {'__name__': '__main__', '__file__': caminho})
    _parar_capsula()
    _preparar()
