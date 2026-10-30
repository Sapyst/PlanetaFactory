"""Entradas do para_jogo.py para o LOTE 11 (produção II; docs/PLANO_INTEGRACAO.md). Fecha a árvore.
Rodar: blender -b --python para_jogo.py -- <nome>

Todos são estudos do Antigravity (FEITOS_ANTIGRAVITY.md; dão sys.exit no modo "nada": rodam em "montar"), 3×3, com o laço do estudo (o jogo toca enquanto a máquina
trabalha). Saem o chão (EFEITO_chao), os efeitos EFEITO_* (faíscas, vapor, clarões), luzes e câmera; a animação de
material/luz não vai no .glb: o que brilha fica aceso por igual e o jogo pulsa P_Cristal. As peças em trânsito ficam:
andam em laço fechado na esteira do modelo, sem aparecer e sumir.

- forja_quantica ← estudo_forja_quantica.py. Entradas de item S1 e O1, saída N1, boca de fluido L1 (criogênico; nenhuma
  receita bebe fluido, fica ligada). Laço: martelo, anel de confinamento, carrossel óptico, fluxômetro, roletes, os dois
  braços e os processadores na esteira norte.
- fundicao_cristal ← estudo_fundicao_cristal.py. Entradas S1 e O1, saída N1, boca de água L1 (sem uso). Laço: turbilhão
  do banho, 4 cristais de foco, lingotes na corrente, fluxômetro e roletes. A cor dos lingotes fica fixa.
- montadora_3 ← estudo_montadora_3.py. S1 → N1 como a montadora, boca de fluido O1 (sem uso). Laço: prensa, SCARAs,
  lasers, anel quântico, exaustor, taliscas e fluxômetro.
- montadora_quantica ← estudo_montadora_quantica.py. Duas linhas cruzadas: S1 → N1 e O1 → L1 (as 2 receitas). Laço:
  peças das duas linhas, anéis contra-rotativos, cubo central, lasers de foco e roletes.
- extrator_ressonante ← estudo_extrator_ressonante.py. Despeja na esteira ao sul (S1), boca de fluido O1 (sem uso).
  Laço: sonotrodo, cristal ressonador, anel de sintonia, fluxômetro e fragmentos na esteira.
- broca_nucleo ← estudo_broca_nucleo.py. Despeja na esteira ao sul (S1), boca de fluido O1 (sem uso). Laço: haste com o
  trado, top drive, polias, peneira, fluxômetro e minério na esteira.
- laboratorio_quantico ← estudo_laboratorio_quantico.py. Entradas S1 e O1, boca de fluido L1 (sem uso). Laço: carrossel,
  ventoinhas, braço de análise, pacotes nas esteiras e fluxômetro.
- irradiador_modulos ← estudo_irradiador_modulos.py. Sem bocas. Laço: carrossel de antenas, cristal transmissor e as 4
  ventoinhas. O campo de luz (LuzCampo) é luz: sai; os LEDs ficam acesos."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))


def _acesos_fixos():
    """Tira a animação de material/luz: o .glb não leva, e o que brilha fica aceso por igual."""
    def montar(sc):
        import bpy
        for m in bpy.data.materials:
            if m.node_tree is not None and m.node_tree.animation_data:
                m.node_tree.animation_data_clear()
        for l in bpy.data.lights:
            if l.animation_data:
                l.animation_data_clear()
    return montar


def _desc(texto):
    def exportar(sc, raiz, dados):
        dados['descricao'] = texto
    return exportar


def _cfg(script, tris, texto):
    return dict(script=script, cat='maquinas', tris=tris, tex=1024, args=['montar'], tirar=['EFEITO_'], margem=0.08,
                depois_de_montar=_acesos_fixos(), antes_de_exportar=_desc(texto))


CONFIG = {
    'forja_quantica': _cfg('estudo_forja_quantica.py', 8000,
                           'Forja quântica 3×3 (estudo_forja_quantica.py): vaso blindado com martelo telescópico, anel de '
                           'confinamento, bigorna e carrossel óptico no teto, braços alimentador e ejetor, entradas sul e '
                           'oeste, saída norte, boca de fluido a leste. Faz processador quântico, pacote quântico e mapa estelar.'),
    'fundicao_cristal': _cfg('estudo_fundicao_cristal.py', 7000,
                             'Fundição de cristal 3×3 (estudo_fundicao_cristal.py): cadinho de metal líquido com 4 cristais '
                             'de foco, corrente de lingotes ao norte, entradas sul e oeste, baia com 4 encaixes de módulo, '
                             'coifa e ciclone. Velocidade 4,0; funde minério direto em aço.'),
    'montadora_3': _cfg('estudo_montadora_3.py', 6000,
                        'Montadora 3 3×3 (estudo_montadora_3.py): prensa dupla, 2 braços SCARA, 2 cabeçotes laser, anel '
                        'quântico e exaustor no teto, esteira interna sul → norte, baia com 4 encaixes de módulo e boca de '
                        'fluido a oeste. Velocidade 1,5.'),
    'montadora_quantica': _cfg('estudo_montadora_quantica.py', 7000,
                               'Montadora quântica 3×3 (estudo_montadora_quantica.py): duas linhas cruzadas sob a matriz '
                               'quântica (sul → norte e oeste → leste), anéis contra-rotativos, cubo central, 4 lasers de '
                               'foco e baia com 4 encaixes de módulo. Velocidade 2,5; 2 receitas ao mesmo tempo.'),
    'extrator_ressonante': _cfg('estudo_extrator_ressonante.py', 6000,
                                'Extrator ressonante 3×3 (estudo_extrator_ressonante.py): sonotrodo de titânio, cristal '
                                'ressonador, anel de sintonia, poço sísmico, boca de fluido a oeste e esteira de saída ao '
                                'sul. 2× a velocidade do extrator no cristal.'),
    'broca_nucleo': _cfg('estudo_broca_nucleo.py', 6000,
                         'Broca de núcleo 3×3 (estudo_broca_nucleo.py): torre derrick com top drive, haste e trado de '
                         'tungstênio, peneira vibratória, boca de fluido a oeste e esteira de saída ao sul. Jazida esgotada '
                         'continua rendendo 10% para sempre.'),
    'laboratorio_quantico': _cfg('estudo_laboratorio_quantico.py', 6000,
                                 'Laboratório quântico 3×3 (estudo_laboratorio_quantico.py): tambor espectrométrico, '
                                 'carrossel óptico, braço de análise, radiador criogênico em V, entradas sul e oeste, boca '
                                 'de fluido a leste e baia com 4 encaixes de módulo. Velocidade 4,0.'),
    'irradiador_modulos': _cfg('estudo_irradiador_modulos.py', 7000,
                               'Irradiador de módulos 3×3 (estudo_irradiador_modulos.py): torre transmissora com carrossel '
                               'de 4 antenas, cristal transmissor, 4 subestações criogênicas e baia de 2 módulos. Divide o '
                               'efeito dos módulos com as máquinas a até 3 tiles.'),
}
