"""Entradas do para_jogo.py para o LOTE 10 (produção I; docs/PLANO_INTEGRACAO.md).
Rodar: blender -b --python para_jogo.py -- <nome>

- montadora_2 ← estudo_montadora_2.py (feito pelo Antigravity; FEITOS_ANTIGRAVITY.md). 3×3, entrada de item ao sul
  (S1), saída ao norte (N1) — as mesmas da montadora — e a boca de fluido a oeste do estudo (O1: flange em x = −1,44,
  z = 0,35; nenhuma receita de montadora bebe fluido ainda, fica ligada para quando houver). Fica o laço do estudo (o
  jogo toca enquanto ela trabalha): taliscas da esteira, mesa do alimentador, os dois braços (SCARA e laser), prensa,
  travas e o pulso de escala do cristal. Saem as 3 peças em trânsito na esteira (os componentes e o cordão apareciam
  por hide_render, que não vai no .glb: ficariam sempre à vista), o feixe de calibração do cristal (efeito), faíscas,
  fumaça, luzes e câmera; o vidro das janelas sai sozinho (para_jogo).
- refinador_2 ← estudo_refinador_2.py (Antigravity). 3×3, as bocas do estudo: fluido entra a oeste (O1) e ao sul (S1,
  a 2ª entrada que o refinador 1 não tem), sai a leste (L1), item sai ao norte no tile oeste (bica em x = −1,0). O
  estudo tem 28.672 triângulos: vai a 11.000 (o refinador 1 tem 8.885). Fica o laço do estudo (o jogo toca enquanto
  ele trabalha): os dois agitadores, o anel quântico, o robô de inspeção na cremalheira, a coluna do visor de nível e
  os ponteiros dos manômetros. Saem as 3 células que a bica ejeta (somem e voltam: ficariam paradas no ar), a chama e
  a fumaça do flare, luzes e câmera; o vidro dos visores sai sozinho (para_jogo).
- fornalha_aco ← estudo_fornalha_aco.py (Antigravity). 2×2, entrada de item ao sul (S1, x = +0,5) e saída ao norte (N0,
  x = −0,5), as bocas do estudo. Fica o laço (o jogo toca enquanto ela trabalha): caçamba do elevador skip, rotor do
  soprador, lingotes na corrente e o pulso do cristal. Saem faíscas, fumaça, vapor, luzes e câmera (efeitos); a cor dos
  lingotes fica fixa (o esfriar era animação de material, que não vai no .glb).
- fornalha_eletrica ← estudo_fornalha_eletrica.py (Antigravity). 2×2, S1 → N0 como a fornalha de aço, e a boca de
  fluido oeste (O1, flange em x = −0,96, z = 0,35; nenhuma receita de fornalha bebe fluido ainda, fica ligada). Fica o
  laço: os três eletrodos no ajuste fino do arco, lingotes na esteira e o pulso do cristal. Saem as faíscas e a fumaça
  (a fornalha não polui: nada de fumaça no jogo), o clarão do arco (luz), luzes e câmera.
- broca_grande ← estudo_broca_grande.py (Antigravity). 3×3, saída de item ao sul (S1, despeja na esteira como a broca)
  e boca de fluido a oeste (O1, névoa; sem uso por enquanto). Fica o laço: descida e giro do trado, hastes, ventoinhas,
  vibração da peneira e as pedras na esteira de saída. Saem fumaça, névoa, luzes e câmera.
- laboratorio_2 ← estudo_laboratorio_2.py (Antigravity; dá sys.exit no modo "nada": roda em "montar"). 3×3, entradas de
  item ao sul (S1) e a oeste (O1), boca de fluido a leste (L1; sem uso por enquanto). Fica o laço: carrossel, ventoinhas,
  rotor do fluxômetro, roletes, braço de carga, comporta, gaveta, anel de força e pulso do cristal. Saem o pacote e a
  amostra em trânsito (o pacote some no fim do ciclo e ficaria parado no ar sem a gaveta), a névoa e o vapor, luzes e
  câmera; o vidro das janelas sai sozinho (para_jogo)."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))


def _acesos_fixos(*prefixos):
    """Tira a animação de material/luz e deixa os materiais `prefixos` acesos por igual."""
    def montar(sc):
        import bpy
        for m in bpy.data.materials:
            if m.node_tree is None:
                continue
            if m.node_tree.animation_data:
                m.node_tree.animation_data_clear()
            if m.name.startswith(prefixos):
                p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if p is not None:
                    p.inputs['Emission Strength'].default_value = 3.0
        for l in bpy.data.lights:
            if l.animation_data:
                l.animation_data_clear()
    return montar


def _montadora2_exportar(sc, raiz, dados):
    dados['descricao'] = ('Montadora 2 3×3 (estudo_montadora_2.py): pórtico azul-petróleo com esteira interna sul → '
                          'norte, alimentador rotativo com braço SCARA, prensa eletroidráulica dupla com travas, braço '
                          'de solda a laser com cilindros de gás, baia com 2 encaixes de módulo, boca de fluido a oeste '
                          'e anel focalizador com cristal no teto. Velocidade 1,0 (a montadora faz 0,75).')


def _refinador2_exportar(sc, raiz, dados):
    dados['descricao'] = ('Refinador 2 3×3 (estudo_refinador_2.py): bomba centrífuga na entrada oeste, dois reatores '
                          'com agitadores, torre de destilação com robô de inspeção e anel quântico, trocador duplo na '
                          'saída leste, 2ª entrada de fluido ao sul, baia com 3 encaixes de módulo, flare e bica de '
                          'itens ao norte. Velocidade 2,0 (o refinador faz 1,0).')


def _fornalha_aco_exportar(sc, raiz, dados):
    dados['descricao'] = ('Fornalha de aço 2×2 (estudo_fornalha_aco.py): casco rebitado com anel de sopro e 6 ventaneiras, '
                          'elevador skip na entrada sul, soprador, recuperador com chaminé alta e bica com corrente de '
                          'lingoteiras na saída norte. Velocidade 2,0 (a fornalha faz 1,0); queima combustível.')


def _fornalha_eletrica_exportar(sc, raiz, dados):
    dados['descricao'] = ('Fornalha elétrica 2×2 (estudo_fornalha_eletrica.py): cuba de arco com 3 eletrodos de grafite e '
                          'braços de cobre, transformador com radiador, exaustão até o ciclone, baia com 2 encaixes de '
                          'módulo, boca de fluido a oeste e bica de lingotes ao norte. Velocidade 2,0, sem combustível '
                          'e sem poluição direta.')


def _broca_grande_exportar(sc, raiz, dados):
    dados['descricao'] = ('Broca grande 3×3 (estudo_broca_grande.py): torre treliçada com trado de tungstênio, 4 pistões '
                          'de avanço, britador e peneira, unidade de força com radiador duplo, boca de fluido a oeste e '
                          'esteira de saída ao sul. Velocidade 1,25 (a broca faz 0,5).')


def _laboratorio2_exportar(sc, raiz, dados):
    dados['descricao'] = ('Laboratório 2 3×3 (estudo_laboratorio_2.py): tambor de análise com gaveta e lasers, carrossel '
                          'óptico no topo, braço de carga na entrada sul, entrada oeste, boca de fluido a leste, radiador '
                          'em V, racks e baia com 2 encaixes de módulo. Velocidade 2,0 (o laboratório conta 1,0).')


CONFIG = {
    'montadora_2': dict(script='estudo_montadora_2.py', cat='maquinas', tris=10500, tex=1024,
                        tirar=['corpo_oleo', 'EFEITO_', 'peca_', 'feixe_reticulo'], margem=0.08,
                        depois_de_montar=_acesos_fixos(), antes_de_exportar=_montadora2_exportar),
    'refinador_2': dict(script='estudo_refinador_2.py', cat='maquinas', tris=11000, tex=1024,
                        tirar=['corpo_oleo', 'EFEITO_', 'celula_'], margem=0.08,
                        depois_de_montar=_acesos_fixos(), antes_de_exportar=_refinador2_exportar),
    'fornalha_aco': dict(script='estudo_fornalha_aco.py', cat='maquinas', tris=8000, tex=1024,
                         tirar=['chao', 'EFEITO_'], margem=0.08,
                         depois_de_montar=_acesos_fixos(), antes_de_exportar=_fornalha_aco_exportar),
    'fornalha_eletrica': dict(script='estudo_fornalha_eletrica.py', cat='maquinas', tris=6000, tex=1024,
                              amostras=list(range(1, 97, 5)),     # o 1º eletrodo (seno de 4 voltas) zera nas 8 de sempre
                              tirar=['chao', 'EFEITO_'], margem=0.08,
                              depois_de_montar=_acesos_fixos(), antes_de_exportar=_fornalha_eletrica_exportar),
    'broca_grande': dict(script='estudo_broca_grande.py', cat='maquinas', tris=8500, tex=1024,
                         tirar=['chao', 'EFEITO_'], margem=0.08,
                         depois_de_montar=_acesos_fixos(), antes_de_exportar=_broca_grande_exportar),
    'laboratorio_2': dict(script='estudo_laboratorio_2.py', cat='maquinas', tris=7000, tex=1024, args=['montar'],
                          tirar=['EFEITO_', 'pacote_', 'amostra_'], margem=0.08,
                          depois_de_montar=_acesos_fixos(), antes_de_exportar=_laboratorio2_exportar),
}
