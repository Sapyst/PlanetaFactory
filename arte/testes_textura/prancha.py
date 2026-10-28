"""Prancha antes|depois de uma lista de modelos texturizados (para mostrar o andamento).
Uso: python3 prancha.py <saida.png> <nome> [<nome> ...]"""
import glob, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
B = os.path.expanduser('~/.local/share/Steam/steamapps/common/Blender/blender')
MONT = '/tmp/claude-1000/-mnt-d/a5102435-3091-41de-b608-b3dca92caa88/scratchpad/mont.py'
arqs = []
for n in sys.argv[2:]:
    achou = glob.glob(os.path.join(AQUI, '..', 'modelos', '**', n + '_tex_previa.png'), recursive=True)
    if achou:
        arqs.append(os.path.abspath(achou[0]))
subprocess.run([B, '-b', '--factory-startup', '--python', MONT, '--', os.path.abspath(sys.argv[1])] + arqs, capture_output=True)
print('PRANCHA', sys.argv[1], len(arqs))
