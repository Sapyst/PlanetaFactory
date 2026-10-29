"""Gera docs/RECURSOS.md (em português) a partir dos dados do jogo: jazidas, biomas, águas, elementos do mapa e a
ficha de cada construção (energia, armazenamento, integridade, custo, pesquisa).
Rodar: python3 jogo/ferramentas/gerar_doc_recursos.py"""
import json, os

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, '..', 'dados')
SAIDA = os.path.join(AQUI, '..', '..', 'docs', 'RECURSOS.md')
ler = lambda n: json.load(open(os.path.join(DADOS, n), encoding='utf-8'))
rec, bio, itens, prog = ler('recursos.json'), ler('biomas.json'), ler('itens.json'), ler('progressao.json')
est, menu, clima = ler('estruturas.json'), ler('menu_construcao.json'), ler('clima.json')
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

# ------------------------------------------------------------------ construções
libera = {}
for pq in prog['pesquisas'].values():
    for p in pq['libera']:
        libera[p] = pq['nome']
REN = {'sol': ' (sol: zero à noite)', 'vento': ' (vento)'}


def ficha(p):
    r = est.get(p, est.get(p + '_reta', {}))
    f = []
    kw = r.get('energia_kw', 0)
    if kw > 0:
        f.append('usa %d kW' % kw)
    elif kw < 0:
        f.append('gera até %d kW%s' % (-kw, REN.get(r.get('renovavel', ''), ' (combustível)' if r.get('combustivel') else '')))
    if 'acumula_mj' in r:
        f.append('guarda %d MJ (até %d kW)' % (r['acumula_mj'], r['acumula_kw']))
    if 'capacidade_itens' in r:
        f.append('%d itens' % r['capacidade_itens'])
    if r.get('capacidade', 0) > 100:
        f.append('%d de fluido' % r['capacidade'])
    if r.get('poluicao'):
        f.append('polui %g/min' % r['poluicao'])
    return ' · '.join(f) or '—'


L += ['', '## Construções', '',
      'Ficha de cada peça do menu: energia, o que guarda, integridade (♥), custo e a pesquisa que libera '
      '("início" = já vem liberada). No jogo a mesma ficha aparece no botão da peça e no painel ao tocar nela.', '']
for cat in menu['categorias']:
    L += ['### ' + cat['nome'], '', '| Peça | Ficha | ♥ | Custo | Libera |', '|---|---|---|---|---|']
    for p in cat['pecas']:
        r = est.get(p, est.get(p + '_reta', {}))
        custo = prog['custos'].get(p, {})
        desc = menu.get('explicacoes', {}).get(p, '')
        L.append('| **%s**%s | %s | %s | %s | %s |' % (
            menu['rotulos'].get(p, p), (' — ' + desc) if desc else '', ficha(p), r.get('vida', '—'),
            ', '.join('%d %s' % (v, nome_item(i).lower()) for i, v in custo.items()) or '—',
            'início' if p in prog['liberado_inicio'] else libera.get(p, '—')))
    L.append('')
L += ['### Opções no painel da peça', '',
      '- **Reparar:** 1 placa de ferro a cada 25 pontos de integridade que faltam.',
      '- **Ligada / desligada:** desligada não consome nem trabalha.',
      '- **Modo** (máquinas elétricas): Econômico 50% da velocidade, 40% da energia, 60% da poluição · Normal · '
      'Turbo 150% da velocidade, 200% da energia, 160% da poluição. Coletor e filtro limpam no ritmo da velocidade.',
      '- **Limite do baú:** 25%, 50% ou 100% da capacidade.', '',
      '## Dia, noite e estações', '',
      '- Um dia dura %d s de jogo (%d min). A noite fica com cerca de 38%% do ciclo na primavera e no outono; '
      'o verão tem dias mais longos e o inverno, mais curtos.' % (clima['dia_s'], clima['dia_s'] // 60),
      '- **As estações seguem o calendário real:** cada uma dura %d dias de verdade e passa mesmo com o jogo '
      'fechado (um ano = 4 semanas). Isso pede planejamento: estoque e acumuladores para o inverno.' % (clima['estacao_s'] // 86400),
      '- O painel solar rende pela luz do dia e do clima (nada à noite). A turbina rende pelo vento, dia e noite. '
      'Fontes grátis (núcleo, sol, vento) são usadas antes do combustível; a sobra carrega os acumuladores, '
      'que devolvem quando falta.', '']
for e in clima['estacoes']:
    L.append('- **%s:** dia %s, secura %d%% (fogo), clima mais provável: %s.' % (
        e['nome'], {0.0: 'normal'}.get(e.get('dia_extra', 0.0), 'mais longo' if e.get('dia_extra', 0) > 0 else 'mais curto'),
        round(100 * e['secura']), ', '.join(clima.get('nomes', {}).get(k, k) for k, v in sorted(e['pesos'].items(), key=lambda x: -x[1])[:2])))
os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('docs/RECURSOS.md', len(L), 'linhas')
