"""Ícones da barra de construção: cada estrutura construível renderizada em isométrico, fundo transparente.
Lê os .glb já exportados (rodar depois dos scripts de modelos). Saída: arte/icones/<nome>.png (192×192).
Uso: blender -b --factory-startup --python icones.py"""
import bpy, os, sys, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import preparar_cena, render, RAIZ

SAIDA = os.path.abspath(os.path.join(RAIZ, '..', 'icones'))
PULAR = ('mapa', 'itens', 'inimigos')

os.makedirs(SAIDA, exist_ok=True)
n = 0
for f in sorted(glob.glob(os.path.join(RAIZ, '**', '*.json'), recursive=True)):
    if os.path.basename(f).startswith('_'):
        continue
    d = json.load(open(f, encoding='utf-8'))
    if d.get('tipo') not in ('estrutura', 'canto', 'veiculo') or d['categoria'].startswith(PULAR):
        continue
    sc = preparar_cena()
    sc.render.film_transparent = True
    sc.display.shading.show_object_outline = False
    sc.display.shading.show_cavity = False
    sc.display.shading.color_type = 'TEXTURE'          # estruturas texturizadas
    bpy.ops.import_scene.gltf(filepath=f[:-5] + '.glb')
    objs = [o for o in sc.objects if o.type == 'MESH']
    render(objs, os.path.join(SAIDA, d['nome'] + '.png'), res=(192, 192), margem=1.08)
    n += 1
print('ICONES', n)
