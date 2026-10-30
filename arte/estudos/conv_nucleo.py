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
Rodar: blender -b --python para_jogo.py -- nucleo_queda"""
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_defesa_energia', os.path.join(AQUI, 'conv_defesa_energia.py'))
_de = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_de)


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


def _queda(sc):
    g = _de._g()
    _de._tirar(sc, 'fogo', 'rastro', 'poeira', 'labareda')
    _de._limite_brilho(g, 200)


CONFIG = {
    'nucleo_queda': dict(script='conv_nucleo.py', args=['nucleo_queda'], estudo='estudo_nucleo_queda.py', cat='maquinas', tris=16000, tex=1024, tirar=[],
                         quadros=240, animacao='chegada', depois_de_montar=_queda),
}


if __name__ == '__main__' and 'nucleo_queda' in sys.argv:
    caminho = os.path.join(AQUI, 'estudo_nucleo_queda.py')
    sys.argv = [sys.argv[0], '--python', caminho, '--', 'nada']
    sys.path.insert(0, AQUI)
    exec(compile(open(caminho, encoding='utf-8').read(), caminho, 'exec'), {'__name__': '__main__', '__file__': caminho})
    _parar_capsula()
