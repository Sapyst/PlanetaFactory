"""Entradas do para_jogo.py para o LOTE 13 (energia I; docs/PLANO_INTEGRACAO.md).
Rodar: blender -b --python para_jogo.py -- <nome>

- poste_alto ← estudo_poste_alto.py (feito pelo Antigravity; FEITOS_ANTIGRAVITY.md). 1×1, sem bocas (só energia).
  Fica o laço do estudo: o anel de ressonância no topo dá a volta em 4 s (o jogo toca enquanto a rede do poste tem
  geração). Os toquinhos de cabo de cobre que o estudo põe nas cadeias de isoladores ficam (são parte da torre); o
  fio de verdade o jogo desenha, preso nos "terminais" = pé dos 4 anéis corona (2 cruzetas, 3,27 m e 3,92 m). As
  cruzetas passam do tile (±0,79 m com o anel corona), lá no alto — como a torre de transmissão de verdade. Saem a
  mancha de óleo, as luzes e as faíscas de corona (EFEITO_, sumiam por hide_render). O pulso do nó da IA e o pisca
  do estrobo eram animação de luz: o anel violeta e o estrobo ficam acesos fixos (P_Cristal/P_Fogo).
- turbina_correnteza ← estudo_turbina_correnteza.py (Antigravity). 2×2, sem bocas. A linha d'água do estudo (z = 0)
  fica na altura do chão do tile de rio (o jogo pinta a água ali; o que está abaixo some no leito, como no rio). Fica o
  laço do estudo: o rotor dá 2 voltas em 4 s (eixo norte–sul: a correnteza passa de sul para norte no modelo), a boia
  de vazão sobe e desce, o estrobo e o cristal pulsam de escala. Sai a arfagem do catamarã: tudo está preso nele e,
  mexendo, iria inteiro para a parte móvel (que leva só 1/4 dos triângulos) — o casco fica parado e o rotor, a boia e
  as luzes se mexem. Saem a água e o leito do estudo (o rio é do mapa), luzes e câmera.
- gerador_fluido ← estudo_gerador_fluido.py (Antigravity). 3×3, entrada de fluido ao sul (FLUIDO_ENT_S1: flange do
  estudo em y = −1,44, z = 0,35). Fica o laço do estudo (o jogo toca enquanto queima): os dois ventiladores do teto, o
  volante, o rotor do visor de fluxo, o anel quântico e o estrobo. Sai o tremor do motor (microvibração de alta
  frequência: o bloco inteiro e o que está preso nele iriam para a parte móvel, que leva só 1/4 dos triângulos), as
  manchas de óleo (decalque), as luzes e a câmera.
- painel_solar_2 ← estudo_painel_solar_2.py (Antigravity). 2×2, sem bocas. Fica o laço do estudo inteiro (o jogo
  toca de dia): rastreador azimutal e de elevação, haste do atuador, limpadores nos trilhos, lentes orbitando e o
  pulso de escala do cristal. Quase tudo está preso no rastreador e se mexe — a parte móvel leva 1/4 do orçamento,
  então o orçamento vai alto (14.000) para o estudo (5.324) passar quase sem redução. Saem luzes e câmera."""
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


# pé de cada cadeia de isoladores (anel corona + grampo): cruzeta de baixo z 3,75 (±0,65), de cima z 4,40 (±0,50);
# a cadeia desce 0,48 m. O fio prende no terminal virado para o outro lado (Fiacao.ponto_fio).
TERMINAIS = [[x, 0.0, round(z - 0.48, 3)] for z, x in ((3.75, 0.65), (4.40, 0.50)) for x in (-x, x)]


def _poste_alto_exportar(sc, raiz, dados):
    dados['terminais'] = TERMINAIS
    dados['descricao'] = ('Poste alto (torre de transmissão): torre treliçada de 5 m com duas cruzetas e quatro cadeias '
                          'de isoladores (o fio prende no pé delas: "terminais"), para-raios e anel de ressonância '
                          'girando no topo. Fio de 30 m até outro poste alto, ligação de 3 m.')


def _turbina_montar(sc):
    import bpy
    _acesos_fixos()(sc)
    c = bpy.data.objects['catamara']
    c.animation_data_clear()
    c.location = (0.0, 0.0, 0.0)
    c.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()


def _turbina_exportar(sc, raiz, dados):
    dados['descricao'] = ('Turbina de correnteza 2×2 (estudo_turbina_correnteza.py): catamarã flutuante com grade '
                          'defletora, rotor hidrocinético de 4 pás meio submerso entre os pontões, gerador com aletas, '
                          'boia de vazão e cristal piezoelétrico. Vai no rio: 150 kW com a correnteza, cai na seca.')


def _gerador_fluido_montar(sc):
    import bpy
    _acesos_fixos()(sc)
    m = bpy.data.objects['motor_vibracao']
    sc.frame_set(1)
    pos = m.location.copy() - __import__('mathutils').Vector((0.0012, 0.0, 0.0))   # sem o tremor do quadro 1 (só em x)
    m.animation_data_clear()
    m.location = pos
    bpy.context.view_layer.update()


def _gerador_fluido_exportar(sc, raiz, dados):
    dados['descricao'] = ('Gerador a fluido 3×3 (estudo_gerador_fluido.py): motor a combustão de seiva com turbo, '
                          'silenciador e chaminé, radiador com dois ventiladores no teto, alternador com volante e '
                          'anel quântico de plasma. Combustível de seiva pelo cano ao sul: até 2,4 MW.')


def _painel2_exportar(sc, raiz, dados):
    dados['descricao'] = ('Painel solar 2 (estudo_painel_solar_2.py): pedestal com rastreador biaxial (azimute e '
                          'elevação com atuador de fuso), duas asas de células dopadas com cristal, limpadores '
                          'ultrassônicos, inversor e anel condensador com 3 lentes orbitando. Até 500 kW de dia; com '
                          'nuvem perde só 15%.')


CONFIG = {
    'poste_alto': dict(script='estudo_poste_alto.py', cat='energia', tris=4500, tex=1024,
                       tirar=['corpo_oleo', 'EFEITO_'], margem=0.35,
                       depois_de_montar=_acesos_fixos('NoIA_Violeta', 'EstroboAereo'),
                       antes_de_exportar=_poste_alto_exportar),
    'turbina_correnteza': dict(script='estudo_turbina_correnteza.py', cat='energia', tris=6000, tex=1024,
                               tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                               depois_de_montar=_turbina_montar, antes_de_exportar=_turbina_exportar),
    'gerador_fluido': dict(script='estudo_gerador_fluido.py', cat='energia', tris=9000, tex=1024,
                           tirar=['corpo_oleo', 'EFEITO_', 'manchas_oleo'], margem=0.08,
                           depois_de_montar=_gerador_fluido_montar, antes_de_exportar=_gerador_fluido_exportar),
    'painel_solar_2': dict(script='estudo_painel_solar_2.py', cat='energia', tris=14000, tex=1024,
                           tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                           depois_de_montar=_acesos_fixos(), antes_de_exportar=_painel2_exportar),
}
