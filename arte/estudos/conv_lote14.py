"""Entradas do para_jogo.py para o LOTE 14 (energia II; docs/PLANO_INTEGRACAO.md) e o acumulador 2 que sobrou do lote 13.
Rodar: blender -b --python para_jogo.py -- <nome>

- acumulador_2 ← estudo_acumulador_2.py (feito pelo Antigravity; FEITOS_ANTIGRAVITY.md). 2×2, sem bocas. Fica o laço do
  estudo (o jogo toca enquanto ligado): ventilador do radiador, anel de foco, pulso de escala do cristal e as 12 barras
  de LED acendendo em sequência. Saem luzes e câmera.
- turbina_alta ← estudo_turbina_alta.py (Antigravity). 3×3, sem bocas. Como a turbina eólica (conv_defesa_energia.py), a
  nacele vira para o vento e o rotor gira no ritmo dele pelo Animador do jogo (partes nacele/helice; o rotor passa do
  tile, 1,65 m de raio, lá no alto: margem 0,4). A hélice do estudo fica em +X: a nacele vai a −90° para ela ficar em −Y
  (frente do vento no jogo). Sai a animação do estudo: a guinada de ±6° e os pinhões (quem gira é o vento), o cata-vento
  e o pulso do cristal (aceso fixo); a ventoinha do óleo e o anemômetro viram as partes rotor/antena do Animador
  (giram no eixo vertical deles). Saem o chão, as luzes e a câmera. O fio prende na base, nos 4 blocos de ancoragem.
- acumulador_cristal ← estudo_acumulador_cristal.py (Antigravity). 2×2, sem bocas. Fica o laço do estudo (o jogo toca
  enquanto ligado): ventilador do radiador criogênico, anel de foco, pulso de escala dos 4 cristais e do central, e as
  16 barras de LED. Saem o chão, as luzes das câmaras e a câmera; o brilho que pulsava no material fica fixo.
- reator_cristal ← estudo_reator_cristal.py (Antigravity). 3×3. Só a entrada de item ao sul (S1) é boca no jogo: a
  árvore pede só o combustível (célula de energia ou cristal carregado), sem subproduto nem refrigeração; a bica norte e
  o bocal oeste do estudo ficam como desenho (se fossem bocas, o jogo avisaria "não ligada" para sempre). Fica o laço
  do estudo (o jogo toca enquanto queima): anel de polarização, barras de controle, núcleo de cristal, êmbolo do
  injetor, rotor do fluxômetro e roletes. Saem a célula e o cartucho em trânsito (ficariam parados no ar com o reator
  parado), o chão, as luzes e a câmera.
- reator_fusao ← estudo_reator_fusao.py (Antigravity). 3×3. Bocas no jogo: entrada de item ao sul (S1, cristal carregado)
  e de água a oeste (O1); a árvore não pede subproduto, então a bica norte e o bocal de vapor a leste ficam como desenho.
  Fica o laço do estudo (o jogo toca enquanto gera): cordão de plasma com o pulso de escala, anel polarizador, os dois
  fluxômetros e os roletes. Saem o cristal e o cartucho em trânsito, o chão, as luzes e a câmera.
- nucleo_singularidade ← estudo_nucleo_singularidade.py (Antigravity). 3×3, sem bocas. Fica o laço do estudo (o jogo toca
  enquanto ligado): os 3 anéis do giroscópio, o disco de acreção, o pulso da esfera e as ventoinhas criogênicas. O estudo
  tem 13.038 triângulos e boa parte gira: vai a 12.000 (o refinador 2 tem 11.577; 3,16 m em y: passa 8 cm do tile de cada lado). Saem o chão, as luzes
  e a câmera."""
import math
import os
import sys

# estes estudos dão sys.exit no modo "nada": roda em outro modo, que só monta a cena sem renderizar
SO_MONTAR = ['montar']

AQUI = os.path.dirname(os.path.abspath(__file__))


def _g():
    """Globais do para_jogo.py (quem chamou o gancho): brilha, reduzir…"""
    f = sys._getframe(1)
    while f is not None:
        if 'montar_estudo' in f.f_globals and 'reduzir' in f.f_globals:
            return f.f_globals
        f = f.f_back
    raise RuntimeError('para_jogo.py não encontrado na pilha')


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


def _acumulador2_exportar(sc, raiz, dados):
    dados['descricao'] = ('Acumulador 2 2×2 (estudo_acumulador_2.py): banco de fluxo redox com 4 pilhas bipolares, tanques '
                          'de eletrólito, bomba magnética com radiador e ventilador, coluna de carga com 12 barras de LED '
                          'e anel de foco com cristal. Guarda 200 MJ, carrega e descarrega até 1,5 MW.')


def _acumulador_cristal_exportar(sc, raiz, dados):
    dados['descricao'] = ('Acumulador de cristal 2×2 (estudo_acumulador_cristal.py): 4 câmaras de titânio com um cristal '
                          'de tempestade levitando em cada, coluna central com 16 barras de LED e anel de foco, radiador '
                          'criogênico com ventilador e barramentos de cobre ao sul. Guarda 600 MJ, troca até 4 MW.')


def _reator_cristal_exportar(sc, raiz, dados):
    dados['descricao'] = ('Reator de cristal 3×3 (estudo_reator_cristal.py): vaso octogonal blindado com cintas e anéis de '
                          'contenção, cristal de tempestade suspenso emitindo plasma violeta, barras de controle, anel de '
                          'polarização no teto, eclusa de injeção ao sul. 8 MW queimando célula de energia ou cristal '
                          'carregado.')


def _reator_fusao_exportar(sc, raiz, dados):
    dados['descricao'] = ('Reator de fusão 3×3 (estudo_reator_fusao.py): tokamak de aço e titânio com 8 bobinas em D, cordão '
                          'de plasma azul visível por 4 janelas de quartzo, solenoide central com anel polarizador, injetores '
                          'de feixe, canhão de injeção ao sul e trocador de calor. 30 MW com cristal carregado e água.')


def _nucleo_singularidade_exportar(sc, raiz, dados):
    dados['descricao'] = ('Núcleo de singularidade 3×3 (estudo_nucleo_singularidade.py): giroscópio de 3 anéis em volta de um '
                          'micro-buraco negro com disco de acreção e jatos polares, 4 torres de confinamento, tanques de '
                          'hélio com radiadores e subestação. 100 MW, sem combustível e sem poluição.')


def _turbina_alta_montar(sc):
    import bpy
    from mathutils import Vector
    _acesos_fixos()(sc)
    for o in sc.objects:
        o.animation_data_clear()
    nacele = bpy.data.objects['nacele']
    helice = bpy.data.objects['helice']
    nacele.rotation_euler = (0.0, 0.0, -math.pi / 2)    # hélice do estudo em +X → −Y (frente do vento no jogo)
    helice.rotation_euler = (0.0, 0.0, 0.0)
    for n in ('pinhao_guinada0', 'pinhao_guinada1', 'anemometro', 'catavento', 'ventoinha_oleo'):
        o = bpy.data.objects.get(n)
        if o is not None:
            o.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    partes = CONFIG['turbina_alta']['partes']
    for parte, o in (('nacele', nacele), ('luzn', nacele), ('helice', helice), ('luzh', helice),
                     ('rotor', bpy.data.objects['ventoinha_oleo']), ('antena', bpy.data.objects['anemometro'])):
        p = o.matrix_world.translation
        partes[parte]['pivo'] = (round(p.x, 3), round(p.y, 3), round(p.z, 3))

    g = _g()

    def brilha(o):
        return any(g['brilha'](s.material) for s in o.material_slots)

    def desc(o):
        return [c for f in o.children for c in [f] + desc(f)]
    d_hel = set(desc(helice))
    for o in desc(nacele):
        if o.type != 'MESH':
            continue
        if o in d_hel:
            o.name = ('PHLUZ__' if brilha(o) else 'PHEL__') + o.name
        else:
            o.name = ('PNLUZ__' if brilha(o) else 'PNAC__') + o.name


def _turbina_alta_exportar(sc, raiz, dados):
    dados['terminais'] = [[sx * 1.2, sy * 1.2, 0.35] for sx in (-1, 1) for sy in (-1, 1)]
    dados['descricao'] = ('Turbina alta 3×3 (estudo_turbina_alta.py): torre estaiada de 3 estágios com colar de estais e '
                          'cremalheira, nacele amarela que vira para o vento, rotor de 3 pás de 3,3 m a 4,9 m de altura, '
                          'anel de foco com cristal, radiador de óleo com ventoinha e mastro com anemômetro. 600 kW; conta '
                          'como +2 níveis de altura no vento.')


CONFIG = {
    'acumulador_2': dict(script='estudo_acumulador_2.py', cat='energia', tris=9000, tex=1024,
                         tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                         depois_de_montar=_acesos_fixos(), antes_de_exportar=_acumulador2_exportar),
    'acumulador_cristal': dict(script='estudo_acumulador_cristal.py', cat='energia', tris=7000, tex=1024, args=SO_MONTAR,
                               tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                               depois_de_montar=_acesos_fixos(), antes_de_exportar=_acumulador_cristal_exportar),
    'reator_cristal': dict(script='estudo_reator_cristal.py', cat='energia', tris=7000, tex=1024, args=SO_MONTAR,
                           tirar=['corpo_oleo', 'EFEITO_', 'celula_combustivel', 'cartucho_gasto'], margem=0.08,
                           depois_de_montar=_acesos_fixos(), antes_de_exportar=_reator_cristal_exportar),
    'reator_fusao': dict(script='estudo_reator_fusao.py', cat='energia', tris=7500, tex=1024, args=SO_MONTAR,
                         tirar=['corpo_oleo', 'EFEITO_', 'cristal_carga', 'cartucho_descarte'], margem=0.08,
                         depois_de_montar=_acesos_fixos(), antes_de_exportar=_reator_fusao_exportar),
    'nucleo_singularidade': dict(script='estudo_nucleo_singularidade.py', cat='energia', tris=12000, tex=1024, args=SO_MONTAR,
                                 tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                                 depois_de_montar=_acesos_fixos(), antes_de_exportar=_nucleo_singularidade_exportar),
    'turbina_alta': dict(script='estudo_turbina_alta.py', cat='energia', tris=8000, tex=1024, args=SO_MONTAR,
                         tirar=['corpo_oleo', 'EFEITO_'], margem=0.4,
                         depois_de_montar=_turbina_alta_montar, antes_de_exportar=_turbina_alta_exportar,
                         partes={
                             'rotor': dict(objetos=['ventoinha_oleo_mesh'], pai='nacele', tris=200),
                             'antena': dict(objetos=['anemometro_conchas'], pai='nacele', tris=240),
                             'luzh': dict(objetos=['PHLUZ__'], pai='helice', tris=240),
                             'helice': dict(objetos=['PHEL__'], pai='nacele', tris=1800),
                             'luzn': dict(objetos=['PNLUZ__'], pai='nacele', tris=240),
                             'nacele': dict(objetos=['PNAC__'], pai='corpo', tris=1800),
                         }),
}
