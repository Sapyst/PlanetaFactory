"""Entradas do para_jogo.py para o LOTE 17 (proliferação: sensor de varredura; docs/PLANO_INTEGRACAO.md).
Rodar: blender -b --python para_jogo.py -- <nome>

- sensor_varredura ← estudo_sensor_varredura.py (feito pelo Antigravity; FEITOS_ANTIGRAVITY.md). Já está no tile 2×2
  (laje centrada na origem). Fica a animação do estudo tocando enquanto o sensor varre: o giro (garfo, mesa, pinhão e
  pistões) dá a volta em 4 s e a antena sobe e desce de 12° a 26° com os pistões acompanhando — as duas partes
  animadas são as do próprio estudo ('giro' e 'antena', nomes neutros no .glb: o Animador só toca o laço). Saem a mancha
  de óleo (assada viraria borrão no concreto) e a luz do radar. O pulso do cristal e a corrida dos LEDs eram animação
  de material (não vai no .glb): os 8 LEDs e o cristal ficam acesos fixos com material da paleta (P_Cristal: o jogo
  pulsa enquanto o sensor trabalha).
- farol_cristal ← estudo_farol_cristal.py (Antigravity). 1×1. Fica o laço do estudo: o carrossel óptico ('giro':
  espelho parabólico e lente) dá a volta em 4 s. Saem a mancha de óleo e as luzes da cena (o jogo põe a luz de 10 m
  à noite). O pulso do cristal e o pisca dos LEDs eram animação de material: ficam acesos fixos (P_Fogo/P_Cristal).
- posto_avancado ← estudo_posto_avancado.py (Antigravity). 3×3, 4 bocas de entrada (meio de cada borda). Fica o laço
  do estudo: a antena irradiadora gira e os 4 pistões dos silos sobem e descem defasados. Saem a mancha de óleo e as
  luzes; o cristal-núcleo e os LEDs dos silos ficam acesos fixos.
- lancador_sementes ← estudo_lancador_sementes.py (Antigravity). 3×3, boca de entrada ao sul. Fica o laço do estudo
  (o jogo toca uma vez a cada disparo, do começo): culatra, recuo do tubo no quadro 50 com os pistões acompanhando.
  Saem a cápsula-semente que voa (o jogo desenha o voo até o alvo), o clarão de boca (assado viraria disco escuro), a
  mancha de óleo e as luzes; as 5 bobinas ficam acesas fixas (P_Cristal).
- receptor_capsulas ← estudo_receptor_capsulas.py (Antigravity). 2×2, saída ao norte (a esteira do estudo fica no meio
  da borda; a boca do jogo é a do tile oeste, N0). Fica o laço do estudo (o jogo toca uma vez a cada cápsula que
  chega, do começo): as 4 garras fecham com os pistões, o empurrador e os roletes.
  Saem a cápsula que desce (parada, ficaria pairando a 4 m; o jogo desenha o voo dela até o funil), o canister que
  desliza na esteira (sumia por hide_render, que não vai no .glb: ficaria sempre à vista), o campo de indução
  (efeito), a mancha de óleo e as luzes; o estrobo fica aceso fixo.
- transportador_quantico ← estudo_transportador_quantico.py (Antigravity). 3×3, entrada ao sul e saída ao norte. Fica
  o laço do estudo: os dois anéis em contra-rotação e o cristal central levitando. Saem as cargas que entram e saem
  (sumiam por hide_render), o feixe do salto (efeito), a mancha de óleo e as luzes; o cristal fica aceso fixo.
- silo_lancamento ← estudo_silo_lancamento.py (Antigravity). 3×3, entradas de item ao sul e a oeste e de fluido a
  leste. Fica o laço do estudo (robôs soldando, braços umbilicais recolhendo, roletes), que o jogo toca enquanto monta
  uma parte e no lançamento. Sai o foguete (o jogo desenha o foguete crescendo com as partes e subindo no lançamento;
  o do estudo subia 4,6 m e voltava, e o sumiço por hide_render não vai no .glb), a pluma, faíscas e luzes (efeito) e
  a mancha de óleo."""
import os, math

AQUI = os.path.dirname(os.path.abspath(__file__))


def _acesos_fixos(*prefixos):
    """Tira a animação de material (pulsos, LEDs piscando) e deixa os materiais `prefixos` acesos por igual."""
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


_sensor_montar = _acesos_fixos('LED_Setor', 'CristalSensor')


def _raiz_neutra(sc, raiz, dados):
    """A raiz do .glb leva o nome da peça; "farol_cristal" terminaria em _cristal e o Animador do jogo pulsaria o
    modelo inteiro como se fosse o cristal: a raiz ganha o sufixo neutro _raiz."""
    raiz.name = raiz.name + '_raiz'


CONFIG = {
    'sensor_varredura': dict(script='estudo_sensor_varredura.py', cat='proliferacao', tris=8000, tex=1024,
                             tirar=['corpo_oleo', 'EFEITO_'], margem=0.08, depois_de_montar=_sensor_montar),
    'farol_cristal': dict(script='estudo_farol_cristal.py', cat='proliferacao', tris=5000, tex=1024,
                          tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                          depois_de_montar=_acesos_fixos('CristalFarol', 'LEDCarga', 'LEDAltaTensao'),
                          antes_de_exportar=_raiz_neutra),
    'posto_avancado': dict(script='estudo_posto_avancado.py', cat='proliferacao', tris=9000, tex=1024,
                           tirar=['corpo_oleo', 'EFEITO_'], margem=0.08,
                           depois_de_montar=_acesos_fixos('CristalNucleoFilho', 'LEDSiloEstoque', 'LEDStatusPosto')),
    'lancador_sementes': dict(script='estudo_lancador_sementes.py', cat='proliferacao', tris=8000, tex=1024,
                              tirar=['corpo_oleo', 'EFEITO_', 'semente', 'clarao'], margem=0.08, amostras=list(range(1, 97, 2)),
                              depois_de_montar=_acesos_fixos('BobinaAceleracao')),
    'receptor_capsulas': dict(script='estudo_receptor_capsulas.py', cat='proliferacao', tris=6000, tex=1024,
                              tirar=['corpo_oleo', 'EFEITO_', 'nucleo_capsula', 'capsula_chegada'], margem=0.08,
                              depois_de_montar=_acesos_fixos('EstroboAproximacao')),
    'transportador_quantico': dict(script='estudo_transportador_quantico.py', cat='proliferacao', tris=8500, tex=1024,
                                   tirar=['corpo_oleo', 'EFEITO_', 'carga_entrada', 'carga_saida'], margem=0.08,
                                   depois_de_montar=_acesos_fixos('CristalQuantico')),
    'silo_lancamento': dict(script='estudo_silo_lancamento.py', cat='proliferacao', tris=9000, tex=1024,
                            tirar=['corpo_oleo', 'EFEITO_', 'foguete'], margem=0.08, depois_de_montar=_acesos_fixos()),
}
