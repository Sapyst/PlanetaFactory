"""Gera docs/RECURSOS.md (em português) a partir dos dados do jogo: jazidas, biomas, águas e elementos do mapa.
Rodar: python3 jogo/ferramentas/gerar_doc_recursos.py"""
import json, os

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, '..', 'dados')
SAIDA = os.path.join(AQUI, '..', '..', 'docs', 'RECURSOS.md')
ler = lambda n: json.load(open(os.path.join(DADOS, n), encoding='utf-8'))
rec, bio, itens, prog = ler('recursos.json'), ler('biomas.json'), ler('itens.json'), ler('progressao.json')
nome_item = lambda k: itens.get(k, {}).get('nome', k)
biomas = {k: v for k, v in bio.items() if not k.startswith('_')}


def pct(pesos):
    t = sum(pesos.values()) or 1
    return {k: round(100 * v / t) for k, v in pesos.items()}


L = ['# Recursos do mapa', '',
     'Guia do que existe no planeta e de onde tirar cada coisa. Gerado de `jogo/dados/` por '
     '`jogo/ferramentas/gerar_doc_recursos.py` — não editar à mão.', '',
     '## Como ver no jogo', '',
     '- **Visão de recursos** — tecla **V** (ou botão **Recursos**): o mapa fica cinza, cada jazida aparece na cor do '
     'recurso com o nome, quanto tem e qual máquina extrai, e cada bioma/água ganha o nome escrito no mapa.',
     '- **Ficha do tile** — com a visão ligada, passe o mouse (ou toque) num tile: mostra a zona, a jazida (quantidade '
     'naquele tile), o elemento natural e o que ele rende ao remover, ou a construção que está ali.',
     '- **Modo construção** — com uma peça na mão, toda esteira mostra uma faixa colorida com setas andando no sentido '
     'do fluxo (amarelo = chão, verde = 0,5 m, rosa = 1,0 m).', '',
     '## Jazidas', '',
     '| Recurso | Cor no mapa | Item que sai | Máquina | Onde aparece (chance por bioma) |',
     '|---|---|---|---|---|']
for tipo, j in rec['jazidas'].items():
    onde = []
    for b, d in biomas.items():
        p = pct(d.get('jazidas', {}))
        if tipo in p:
            onde.append('%s %d%%' % (rec['biomas'].get(b, b), p[tipo]))
    L.append('| **%s** | `%s` | %s | %s | %s |' % (j['nome'], j['cor'], nome_item(j['item']), j['extrator'], ', '.join(onde) or '—'))
L += ['', 'Perto do ponto inicial há sempre uma jazida de cada: cristal, ferro, cobre, carvão e pedra. '
      'Longe do início as manchas ficam maiores e mais ricas.', '',
      '## Biomas', '']
for b, d in biomas.items():
    L.append('### %s' % rec['biomas'].get(b, b))
    p = pct(d.get('jazidas', {}))
    L.append('- **Jazidas:** ' + ', '.join('%s (%d%%)' % (rec['jazidas'][k]['nome'], v) for k, v in sorted(p.items(), key=lambda x: -x[1])))
    els = list(d.get('obstaculos', {}).get('tipos', {}).keys()) + list(d.get('grandes', {}).get('tipos', {}).keys())
    if els:
        L.append('- **Elementos:** ' + ', '.join(dict.fromkeys(rec['elementos'].get(e, e) for e in els)))
    L.append('')
L += ['## Águas', '', 'Rio, lago, lagoa, mar e oceano não aceitam construção; a praia aceita. '
      'Na visão de recursos cada água aparece com o nome em azul.', '',
      '## Elementos naturais (remover rende)', '', '| Elemento | Rende |', '|---|---|']
vistos = set()
for k, nome in rec['elementos'].items():
    drops = prog.get('drops', {}).get(k, {})
    if nome in vistos or not drops:
        continue
    vistos.add(nome)
    L.append('| %s | %s |' % (nome, ', '.join('%d × %s' % (v, nome_item(i)) for i, v in drops.items())))
os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('docs/RECURSOS.md', len(L), 'linhas')
