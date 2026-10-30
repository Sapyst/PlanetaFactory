#!/usr/bin/env python3
"""Gera jogo/dados/arvore.json — a estrutura da árvore de tecnologia que a tela de pesquisa mostra — a partir de:
  docs/ARVORE_TECNOLOGIA.mmd  (nós, eras em subgraph, setas de pré-requisito, classes existente/objetivo)
  docs/ARVORE_TECNOLOGIA.md   (tabelas de balanceamento: pacotes, tempo por pacote, o que libera)
As pesquisas jogáveis continuam em dados/progressao.json; aqui elas só ganham era e posição na árvore.
Uso: python3 jogo/ferramentas/gerar_arvore.py"""
import json, os, re, sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MMD = os.path.join(RAIZ, 'docs', 'ARVORE_TECNOLOGIA.mmd')
MD = os.path.join(RAIZ, 'docs', 'ARVORE_TECNOLOGIA.md')
SAIDA = os.path.join(RAIZ, 'jogo', 'dados', 'arvore.json')
PROG = os.path.join(RAIZ, 'jogo', 'dados', 'progressao.json')

ERAS = {'era_base': 'base', 'era_meio': 'meio', 'era_avancado': 'avancada'}


def ler_mmd():
    nos, setas, classes = {}, [], {}
    era = ''
    nomes_era = {}
    for linha in open(MMD, encoding='utf-8'):
        l = linha.strip()
        m = re.match(r'subgraph (\w+)\["([^"]+)"\]', l)
        if m:
            era = ERAS.get(m.group(1), m.group(1).replace('era_', ''))
            nomes_era[era] = m.group(2).split(' — ')[0]
            continue
        if l == 'end':
            era = ''
            continue
        m = re.match(r'(\w+)\["([^"]+)"\]$', l)
        if m:
            nos[m.group(1)] = {'nome': m.group(2), 'era': era}
            continue
        m = re.match(r'(\w+)\s*-->\s*(\w+)$', l)
        if m:
            setas.append((m.group(1), m.group(2)))
            continue
        m = re.match(r'class ([\w,]+) (\w+)$', l)
        if m:
            for i in m.group(1).split(','):
                classes.setdefault(i, set()).add(m.group(2))
    return nos, setas, classes, nomes_era


def ler_custos():
    """Linhas | id | pacotes (tipo × qtd) | tempo | libera | das três tabelas de balanceamento."""
    custos = {}
    dentro = False
    for linha in open(MD, encoding='utf-8'):
        if linha.startswith('## Balanceamento'):
            dentro = True
            continue
        if dentro and linha.startswith('## ') and not linha.startswith('## Balanceamento'):
            break
        if not dentro or not linha.startswith('| '):
            continue
        c = [x.strip() for x in linha.strip().strip('|').split('|')]
        if len(c) != 4 or c[0] in ('ID',) or c[0].startswith('---'):
            continue
        try:
            tempo = float(c[2].replace(',', '.'))
        except ValueError:
            continue
        pacotes = []
        for parte in c[1].split('+'):
            m = re.match(r'\s*(.+?)\s*×\s*(\d+)', parte)
            if m:
                pacotes.append([m.group(1), int(m.group(2))])
        custos[c[0]] = {'pacotes': pacotes, 'tempo': tempo, 'libera': c[3]}
    return custos


MELHORIAS = ('dano_', 'cadencia_', 'alcance_', 'mineracao_', 'pesquisa_vel_', 'drones_bateria', 'drones_frota',
             'drones_velocidade', 'drones_defesa', 'harmonia_ninhos', 'simbiose', 'escudo_2', 'drones_tempestade',
             'drones_logisticos_2')


def tipo_de(i, n):
    """O que a tecnologia faz no jogo: estrutura (peça nova), receita (item novo), melhoria (bônus no que já
    existe), infinita (melhoria repetível) ou objetivo (fim da campanha)."""
    t = n.get('libera', '').strip()
    if n.get('objetivo'):
        return 'objetivo'
    if i.endswith('_infinito') or i.endswith('_infinita'):
        return 'infinita'
    if i.startswith('modulo_'):
        return 'receita'                                # módulo: item novo (receita) que se encaixa nas máquinas
    if i.startswith(MELHORIAS) or t[:1] in '+−':
        return 'melhoria'
    if t.lower().startswith('receita'):
        return 'receita'
    return 'estrutura'


def main():
    nos, setas, classes, nomes_era = ler_mmd()
    custos = ler_custos()
    jogaveis = json.load(open(PROG, encoding='utf-8'))['pesquisas']
    erros = []
    for a, b in setas:
        if a not in nos or b not in nos:
            erros.append('seta com nó desconhecido: %s --> %s' % (a, b))
        else:
            nos[b].setdefault('requer', []).append(a)
    for i, n in nos.items():
        n.setdefault('requer', [])
        c = custos.get(i)
        if c is None:
            erros.append('sem custo na tabela de balanceamento: ' + i)
        else:
            n.update(c)
        if 'existente' in classes.get(i, ()):
            n['existente'] = True
        if 'objetivo' in classes.get(i, ()):
            n['objetivo'] = True
        n['tipo'] = tipo_de(i, n)
    for i, p in jogaveis.items():                       # a árvore tem de bater com o que já se joga
        if i not in nos:
            erros.append('pesquisa jogável fora da árvore: ' + i)
        elif sorted(p.get('requer', [])) != sorted(nos[i]['requer']):
            erros.append('pré-requisitos diferentes em %s: jogo %s, árvore %s' % (i, p.get('requer'), nos[i]['requer']))
    # sem ciclos
    estado = {}

    def visita(i, pilha):
        if estado.get(i) == 1:
            erros.append('ciclo: ' + ' → '.join(pilha + [i]))
            return
        if estado.get(i) == 2:
            return
        estado[i] = 1
        for r in nos[i]['requer']:
            visita(r, pilha + [i])
        estado[i] = 2
    for i in nos:
        visita(i, [])
    if erros:
        print('\n'.join(erros))
        sys.exit(1)
    eras = [{'id': e, 'nome': nomes_era.get(e, e)} for e in ('base', 'meio', 'avancada')]
    saida = {'_nota': 'Gerado por jogo/ferramentas/gerar_arvore.py a partir de docs/ARVORE_TECNOLOGIA.mmd e .md. '
                      'Não editar à mão.', 'eras': eras, 'nos': nos}
    with open(SAIDA, 'w', encoding='utf-8') as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('arvore.json: %d nós, %d setas, %d jogáveis' % (len(nos), len(setas), len(jogaveis)))


main()
