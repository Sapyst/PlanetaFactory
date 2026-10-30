import sys, os
sys.path.insert(0, '/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/blender_scripts')
import lib_pf
lib_pf.RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelos')
exec(open('/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/blender_scripts/texturizar.py', encoding='utf-8').read())
