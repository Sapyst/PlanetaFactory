"""Gera arte/CATALOGO.md a partir dos .json exportados de cada modelo."""
import json, os, glob
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dados = []
for f in sorted(glob.glob(os.path.join(RAIZ, 'modelos', '**', '*.json'), recursive=True)):
    if os.path.basename(f).startswith('_'): continue
    dados.append(json.load(open(f, encoding='utf-8')))
ordem = ['itens/recursos', 'itens/intermediarios', 'itens/avancados', 'logistica/esteira', 'logistica/bracos',
         'logistica/armazenagem', 'logistica/canos', 'maquinas', 'energia', 'defesa',
         'transporte/trilhos', 'transporte/veiculos', 'inimigos/aranha',
         'mapa/vegetacao', 'mapa/rochas', 'mapa/jazidas', 'mapa/agua']
titulos = {'itens/recursos': 'Recursos brutos', 'itens/intermediarios': 'Intermediários', 'itens/avancados': 'Avançados',
           'logistica/esteira': 'Esteiras, distribuidores e pilares', 'logistica/bracos': 'Braços mecânicos',
           'logistica/armazenagem': 'Armazenagem', 'logistica/canos': 'Canos e bomba', 'maquinas': 'Máquinas',
           'energia': 'Energia e fluidos', 'defesa': 'Defesa',
           'transporte/trilhos': 'Trilhos e estação', 'transporte/veiculos': 'Trem (veículos)', 'inimigos/aranha': 'Inimigos',
           'mapa/vegetacao': 'Mapa: vegetação', 'mapa/rochas': 'Mapa: rochas e montanhas', 'mapa/jazidas': 'Mapa: jazidas',
           'mapa/agua': 'Mapa: água'}
L = ['# Catálogo de modelos', '', f'{len(dados)} modelos. Gerado por `blender_scripts/catalogo.py` — não editar à mão.', '',
     'Portas: `ITEM`/`FLUIDO`/`TRILHO`, `ENT`/`SAI`, lado (S/N/L/O) e índice do tile na borda. Ficam no .glb como nós `PORTA_*`.',
     'Partes: peças móveis exportadas separadas (o jogo anima pelo nome — ver jogo/render/animacao/animador.gd).',
     'Texturas de chão em `texturas/` (loop sem emenda; relatório em `texturas/_emenda.json`).', '']
for cat in ordem:
    xs = [d for d in dados if d['categoria'] == cat]
    if not xs: continue
    L += [f'## {titulos[cat]}', '', '| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |', '|---|---|---|---|---|---|']
    for d in xs:
        area = {'item': 'item', 'canto': 'canto', 'deco': 'enfeite', 'veiculo': 'livre', 'segmento': 'peça'}.get(d['tipo'], f"{d['area'][0]}×{d['area'][1]}")
        portas = ', '.join(p['nome'].replace('PORTA_', '') for p in d['portas']) or '—'
        moveis = [x['nome'] for x in d.get('partes', []) if x['nome'] != 'corpo' and x['nome'] != 'base']
        if moveis: portas += ' · partes: ' + ', '.join(moveis)
        dims = ' × '.join(f'{v:.2f}'.replace('.', ',') for v in d['dims'])
        L.append(f"| `{d['nome']}` | {area} | {d['tris']} | {dims} | {portas} | {d['descricao']} |")
    L.append('')
erros = [d for d in dados if d.get('erros')]
L += ['## Verificação', '', 'Todos os modelos passaram na checagem automática.' if not erros else
      '\n'.join(f"- `{d['nome']}`: {d['erros']}" for d in erros), '']
open(os.path.join(RAIZ, 'CATALOGO.md'), 'w', encoding='utf-8').write('\n'.join(L))
print(len(dados), 'modelos;', len(erros), 'com erro')
