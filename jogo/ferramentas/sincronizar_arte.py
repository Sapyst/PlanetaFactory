"""Copia a arte gerada (arte/modelos, arte/texturas, arte/icones) para jogo/assets e monta jogo/dados/estruturas.json.
Rodar depois de arte/blender_scripts/gerar_tudo.sh (que já chama este script)."""
import json, os, glob, shutil
AQUI = os.path.dirname(os.path.abspath(__file__))
JOGO = os.path.abspath(os.path.join(AQUI, '..')); ARTE = os.path.abspath(os.path.join(JOGO, '..', 'arte'))
dest_m = os.path.join(JOGO, 'assets', 'modelos'); dest_t = os.path.join(JOGO, 'assets', 'texturas')
os.makedirs(dest_m, exist_ok=True); os.makedirs(dest_t, exist_ok=True)
defs = {}
for f in sorted(glob.glob(os.path.join(ARTE, 'modelos', '**', '*.json'), recursive=True)):
    if os.path.basename(f).startswith('_'): continue
    d = json.load(open(f, encoding='utf-8')); glb = f[:-5] + '.glb'
    pasta = os.path.join(dest_m, d['categoria']); os.makedirs(pasta, exist_ok=True)
    shutil.copy2(glb, os.path.join(pasta, d['nome'] + '.glb'))
    d['modelo'] = f"res://assets/modelos/{d['categoria']}/{d['nome']}.glb"
    for k in ('materiais',): d.pop(k, None)
    defs[d['nome']] = d
for f in glob.glob(os.path.join(ARTE, 'texturas', '*.png')):
    if not os.path.basename(f).startswith('_'): shutil.copy2(f, dest_t)
dest_i = os.path.join(JOGO, 'assets', 'icones'); os.makedirs(dest_i, exist_ok=True)
for f in glob.glob(os.path.join(ARTE, 'icones', '*.png')): shutil.copy2(f, dest_i)
json.dump(defs, open(os.path.join(JOGO, 'dados', 'modelos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(defs), 'modelos sincronizados')
