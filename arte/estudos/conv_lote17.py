"""Entradas do para_jogo.py para o LOTE 17 (proliferação: sensor de varredura; docs/PLANO_INTEGRACAO.md).
Rodar: blender -b --python para_jogo.py -- <nome>

- sensor_varredura ← estudo_sensor_varredura.py (feito pelo Antigravity; FEITOS_ANTIGRAVITY.md). Já está no tile 2×2
  (laje centrada na origem). Fica a animação do estudo tocando enquanto o sensor varre: o giro (garfo, mesa, pinhão e
  pistões) dá a volta em 4 s e a antena sobe e desce de 12° a 26° com os pistões acompanhando — as duas partes
  animadas são as do próprio estudo ('giro' e 'antena', nomes neutros no .glb: o Animador só toca o laço). Saem a mancha
  de óleo (assada viraria borrão no concreto) e a luz do radar. O pulso do cristal e a corrida dos LEDs eram animação
  de material (não vai no .glb): os 8 LEDs e o cristal ficam acesos fixos com material da paleta (P_Cristal: o jogo
  pulsa enquanto o sensor trabalha)."""
import os, math

AQUI = os.path.dirname(os.path.abspath(__file__))


def _sensor_montar(sc):
    """Tira a animação de material (pulso do cristal, LEDs de setor) e deixa todos acesos por igual."""
    import bpy
    for m in bpy.data.materials:
        if m.node_tree is None:
            continue
        if m.node_tree.animation_data:
            m.node_tree.animation_data_clear()
        if m.name.startswith(('LED_Setor', 'CristalSensor')):
            p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if p is not None:
                p.inputs['Emission Strength'].default_value = 3.0
    for l in bpy.data.lights:
        if l.animation_data:
            l.animation_data_clear()


CONFIG = {
    'sensor_varredura': dict(script='estudo_sensor_varredura.py', cat='proliferacao', tris=8000, tex=1024,
                             tirar=['corpo_oleo', 'EFEITO_'], margem=0.08, depois_de_montar=_sensor_montar),
}
