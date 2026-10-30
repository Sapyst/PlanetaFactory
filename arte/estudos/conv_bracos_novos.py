"""Entradas do para_jogo.py para o BRAÇO EMPILHADOR (fase 2, item final do docs/PLANO_INTEGRACAO.md).

Braço empilhador (braco_empilhador) ← estudo_bracos_novos.py (BRAÇO EMPILHADOR): braço reforçado de vigas-caixão,
  contrapeso de placas na traseira do giro, pistão de elevação na frente do braço 1, garra-gaiola com garfos de pinça
  embaixo, prensa compactadora e contador de 4 LEDs. Mesmo método do braço com filtro (conv_logistica_base.py): este
  arquivo roda como script (args ['braco_empilhador']), monta o estudo sem foto, fica só o empilhador (filtro e
  quântico saem), pose de repouso (braço 1 de pé, braço 2 adiante, pistão mirando, pinças fechadas, prensa em cima),
  sem a animação do estudo; saem a laje de 5 cm (tudo desce Z0), as esteiras de contexto e os 4 itens. Contador
  apagado. Partes do jogo pelo empty de cada malha: giro (+ pinhão), braco1, braco2, garra (+ pinças e prensa),
  camisa e haste do pistão de elevação (miram um no outro, como no braço longo e no com filtro).
Rodar: blender -b --python para_jogo.py -- braco_empilhador"""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_esteiras_bracos', os.path.join(AQUI, 'conv_esteiras_bracos.py'))
_eb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eb)

PI = math.pi
Z0 = 0.05
# pivôs do estudo (Zg = Z0 + 0,25; S = Zg + 0,20; L1 0,55; L2 0,62; pistão A = (0; 0,20; Zg + 0,08), P0 = S + (0;
# 0,085; 0,25)) descontada a laje
PIV_EMP = dict(giro=(0, 0, 0.25), braco1=(0, 0, 0.45), braco2=(0, 0, 1.00), garra=(0, 0.62, 1.00),
               camisa=(0, 0.20, 0.33), haste=(0, 0.085, 0.70))
PAI_EMP = dict(giro='base', braco1='giro', braco2='braco1', garra='braco2', camisa='giro', haste='braco1')
PARTE_DO_EMPTY = {'empilhador_giro': 'giro', 'empilhador_pinhao': 'giro', 'empilhador_braco1': 'braco1',
                  'empilhador_braco2': 'braco2', 'empilhador_garra': 'garra', 'empilhador_pinca_-1': 'garra',
                  'empilhador_pinca_1': 'garra', 'empilhador_prensa': 'garra',
                  'empilhador_pistao_camisa': 'camisa', 'empilhador_pistao_haste': 'haste'}


def _montar_empilhador():
    import bpy
    estudo = os.path.join(AQUI, 'estudo_bracos_novos.py')
    sys.argv = [sys.argv[0], '--python', estudo, '--', 'nada']
    g = {'__name__': '__main__', '__file__': estudo}
    exec(compile(open(estudo, encoding='utf-8').read(), estudo, 'exec'), g)
    sc = bpy.context.scene
    for cn in ('filtro', 'quantico'):                   # só o empilhador
        for o in list(bpy.data.collections[cn].objects):
            bpy.data.objects.remove(o, do_unlink=True)
    A = g['emp']
    g['posar2'](A, 0.0, PI / 2, 0.0, 1)                # repouso
    for pc, s_ in A['pincas']:                         # pinças fechadas
        pc.e.location = pc.pivo - A['g'].pivo
    A['prensa'].e.location = A['prensa'].pivo - A['g'].pivo
    for o in list(sc.objects):
        o.animation_data_clear()
        if o.type == 'LIGHT' and o.data.animation_data:
            o.data.animation_data_clear()
    for m in bpy.data.materials:
        if m.node_tree and m.node_tree.animation_data:
            m.node_tree.animation_data_clear()
    M = g['M']
    for k in range(4):                                 # contador apagado (garra vazia)
        b = M['cont%d' % k].node_tree.nodes.get('Principled BSDF')
        if b is not None:
            b.inputs['Emission Strength'].default_value = 0.0
    fora = ['empilhador_esteiras', 'empilhador_item_', 'chao']
    sai = set()
    for o in list(sc.objects):
        laje = o.type == 'MESH' and o.parent is not None and o.parent.name == 'empilhador_raiz'
        if laje or any(o.name.startswith(f) for f in fora):
            sai |= {o.name} | {c.name for c in o.children_recursive}
    for n in sai:
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    raiz = bpy.data.objects['empilhador_raiz']
    raiz.location = (0, 0, -Z0)
    bpy.context.view_layer.update()
    for k, o in enumerate([o for o in sc.objects if o.type in ('MESH', 'FONT')]):
        p = o.parent
        while p is not None:
            if p.type == 'EMPTY' and p.name in PARTE_DO_EMPTY:
                o.name = 'q%sq_%d' % (PARTE_DO_EMPTY[p.name], k)
                break
            p = p.parent


def _empilhador_json(sc, raiz, dados):
    # a gaiola desce 0,34 m do pulso (os outros braços, ~0,20): o pulso fica 0,10 m mais alto que o alvo do jogo para
    # o fundo da gaiola chegar ao item na mesma altura; a pilha fica dentro da gaiola, 0,23 m abaixo do pulso
    dados['garra'] = {'pulso_dz': 0.10, 'item': 0.23}
    corpo = next(o for o in sc.objects if o.type == 'MESH' and o.name.endswith('_base'))
    novos = []
    for t in dados.get('terminais', []):
        zs = [(corpo.matrix_world @ v.co).z for v in corpo.data.vertices
              if math.hypot((corpo.matrix_world @ v.co).x - t[0], (corpo.matrix_world @ v.co).y - t[1]) < 0.12]
        novos.append([t[0], t[1], round(max(zs), 3) if zs else t[2]])
    if novos:
        dados['terminais'] = novos
    dados['descricao'] = ('Braço empilhador: braço reforçado com garra-gaiola, pinças e prensa; leva até 4 itens iguais '
                          'por ciclo. Partes: giro, braco1, braco2, garra, camisa/haste do pistão de elevação.')


if __name__ == '__main__':
    if (sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '') == 'braco_empilhador':
        _montar_empilhador()

CONFIG = {}
CONFIG['braco_empilhador'] = dict(
    script='conv_bracos_novos.py', args=['braco_empilhador'], cat='logistica/bracos', tris=2800, tex=1024,
    anima=False, margem=1.0, corpo='base', tirar=[], estudo='estudo_bracos_novos.py',
    depois_de_montar=lambda sc: _eb._recortar(sc, -0.5, 0.5, -0.5, 2.0, 0.0, 0.0, False),
    partes={pn: dict(objetos=['q%sq' % pn], pivo=p, pai=PAI_EMP[pn],
                     tris=dict(giro=550, braco1=500, braco2=350, garra=450, camisa=250, haste=100)[pn])
            for pn, p in PIV_EMP.items()},
    antes_de_exportar=_empilhador_json)
