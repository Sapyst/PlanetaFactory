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
  a fumaça do flare, luzes e câmera; o vidro dos visores sai sozinho (para_jogo)."""
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


CONFIG = {
    'montadora_2': dict(script='estudo_montadora_2.py', cat='maquinas', tris=10500, tex=1024,
                        tirar=['corpo_oleo', 'EFEITO_', 'peca_', 'feixe_reticulo'], margem=0.08,
                        depois_de_montar=_acesos_fixos(), antes_de_exportar=_montadora2_exportar),
    'refinador_2': dict(script='estudo_refinador_2.py', cat='maquinas', tris=11000, tex=1024,
                        tirar=['corpo_oleo', 'EFEITO_', 'celula_'], margem=0.08,
                        depois_de_montar=_acesos_fixos(), antes_de_exportar=_refinador2_exportar),
}
