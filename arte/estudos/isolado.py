"""Roda um script do jogo (texturizar, auditar) apontando para a pasta de modelos isolada do estudo."""
import sys, os
BS = '/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/blender_scripts'
sys.path.insert(0, BS)
import lib_pf
AQUI = '/tmp/claude-1000/-mnt-d/a5102435-3091-41de-b608-b3dca92caa88/scratchpad/estudo'
lib_pf.RAIZ = os.path.join(AQUI, 'modelos')
alvo = os.environ['ALVO']
src = open(os.path.join(BS, alvo), encoding='utf-8').read()
src = src.replace("RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modelos'))", "RAIZ = %r" % lib_pf.RAIZ)
__file__ = os.path.join(BS, alvo)
exec(compile(src, __file__, 'exec'))
