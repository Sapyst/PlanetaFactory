"""
Estudo de ambiente — Grupo 5: Rochas (PlanetaFactory).
Modelos (4):
  - seixos       (~0.45 x 0.60 x 0.10 m)
  - pedregulho   (~0.55 x 0.66 x 0.37 m)
  - rocha_agua   (~0.77 x 0.59 x 0.36 m)
  - rocha_grande (~1.43 x 1.68 x 1.17 m, 2x2)
Limite rígido: <= 250 triângulos por modelo. Malha única (MESH), sem transparência, origem na base (z=0).
"""
import os
import sys
import math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb


def criar_seixos():
    """Agrupamento natural de 6 seixos rolados e lascas minerais no chão (~0.46 x 0.58 x 0.11 m)."""
    c = amb.ConstrutorMalha(['P_Rocha', 'P_Pedra', 'P_RochaEscura'])
    m_r1, m_r2, m_r3 = 0, 1, 2

    pedrinhas = [
        (Vector((-0.08, -0.10, 0.045)), (0.11, 0.09, 0.055), m_r1, 11),
        (Vector((0.09, -0.04, 0.040)), (0.09, 0.10, 0.050), m_r2, 22),
        (Vector((-0.02, 0.11, 0.050)), (0.12, 0.08, 0.060), m_r3, 33),
        (Vector((0.11, 0.16, 0.032)), (0.07, 0.06, 0.038), m_r1, 44),
        (Vector((-0.14, 0.04, 0.030)), (0.06, 0.07, 0.035), m_r2, 55),
        (Vector((0.02, -0.20, 0.035)), (0.08, 0.06, 0.042), m_r3, 66),
    ]
    for pos, raios, mat, sem in pedrinhas:
        c.rocha_organica(pos, raios, mat=mat, semente=sem, gomos=6, aneis=2, achatar_base=True)

    return c.finalizar('seixos', escala_xy=0.52, escala_z=0.105)


def criar_pedregulho():
    """Pedregulho campestre (~0.55 x 0.66 x 0.37 m): bloco facetado principal com lascas basais encaixadas."""
    c = amb.ConstrutorMalha(['P_Rocha', 'P_RochaEscura', 'P_Pedra'])
    m_r1, m_r2, m_r3 = 0, 1, 2

    # Bloco principal inclinado
    c.rocha_organica(Vector((-0.02, 0.02, 0.18)), (0.24, 0.28, 0.22), mat=m_r1, semente=101, gomos=7, aneis=3, achatar_base=True)
    # Contraforte escuro fraturado
    c.rocha_organica(Vector((0.12, -0.10, 0.11)), (0.16, 0.18, 0.14), mat=m_r2, semente=102, gomos=6, aneis=2, achatar_base=True)
    # Duas lascas claras na base
    c.rocha_organica(Vector((-0.15, -0.14, 0.07)), (0.11, 0.10, 0.09), mat=m_r3, semente=103, gomos=6, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((0.08, 0.19, 0.06)), (0.10, 0.09, 0.08), mat=m_r3, semente=104, gomos=5, aneis=2, achatar_base=True)

    return c.finalizar('pedregulho', escala_xy=0.61, escala_z=0.375)


def criar_rocha_agua():
    """Rocha de margem/água (~0.77 x 0.59 x 0.36 m): basalto escuro erodido pela correnteza com capas de limo."""
    c = amb.ConstrutorMalha(['P_RochaEscura', 'P_Rocha', 'P_Lodo'])
    m_esc, m_med, m_lodo = 0, 1, 2

    # Corpo basáltico alongado e achatado pela água
    c.rocha_organica(Vector((-0.03, 0.0, 0.16)), (0.34, 0.25, 0.20), mat=m_esc, semente=201, gomos=7, aneis=3, achatar_base=True)
    c.rocha_organica(Vector((0.18, 0.06, 0.11)), (0.20, 0.18, 0.14), mat=m_med, semente=202, gomos=6, aneis=2, achatar_base=True)

    # Três placas de musgo/limo aquático abraçando o topo úmido e a linha d'água
    c.tufo_folha(Vector((-0.06, 0.02, 0.31)), (0.18, 0.14, 0.05), mat=m_lodo, semente=203, gomos=6, aneis=2)
    c.tufo_folha(Vector((0.16, 0.05, 0.21)), (0.13, 0.11, 0.045), mat=m_lodo, semente=204, gomos=5, aneis=2)
    c.rocha_organica(Vector((-0.22, -0.10, 0.05)), (0.14, 0.11, 0.06), mat=m_lodo, semente=205, gomos=5, aneis=2, achatar_base=True)

    return c.finalizar('rocha_agua', escala_xy=0.68, escala_z=0.362)


def criar_rocha_grande():
    """Rocha grande 2x2 (~1.43 x 1.68 x 1.17 m): afloramento monolítico estratificado com escarpa dupla."""
    c = amb.ConstrutorMalha(['P_Rocha', 'P_RochaEscura', 'P_Pedra'])
    m_r1, m_r2, m_r3 = 0, 1, 2

    # Torre rochosa principal
    c.rocha_organica(Vector((-0.12, 0.05, 0.56)), (0.54, 0.62, 0.66), mat=m_r1, semente=301, gomos=7, aneis=3, achatar_base=True)
    # Segundo pico inclinado escuro formando garganta
    c.rocha_organica(Vector((0.32, -0.18, 0.42)), (0.42, 0.48, 0.50), mat=m_r2, semente=302, gomos=7, aneis=3, achatar_base=True)
    # Degrau geológico claro na frente
    c.rocha_organica(Vector((-0.28, -0.36, 0.25)), (0.36, 0.34, 0.30), mat=m_r3, semente=303, gomos=6, aneis=2, achatar_base=True)
    # Contraforte traseiro e matacão lateral
    c.rocha_organica(Vector((0.22, 0.40, 0.28)), (0.34, 0.32, 0.34), mat=m_r1, semente=304, gomos=6, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((0.52, 0.08, 0.14)), (0.20, 0.22, 0.18), mat=m_r3, semente=305, gomos=5, aneis=2, achatar_base=True)

    return c.finalizar('rocha_grande', escala_xy=1.55, escala_z=1.17)


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_seixos(),
        criar_pedregulho(),
        criar_rocha_agua(),
        criar_rocha_grande(),
    ]
    posicoes = [(-2.2, 0.0), (-1.1, 0.0), (0.0, 0.0), (1.7, 0.0)]
    for o, (px, py) in zip(modelos, posicoes):
        o.location = Vector((px, py, 0.0))

    vistas = [
        ('amb_rochas_0.png', (-0.1, -6.5, 3.1), (-0.1, 0.0, 0.45), 38.0, 1400, 950),
        ('amb_rochas_1.png', (5.0, -4.6, 3.1), (-0.1, 0.0, 0.45), 38.0, 1400, 950),
        ('amb_rochas_perto.png', (-0.5, -2.8, 1.25), (-0.5, 0.0, 0.25), 36.0, 1400, 950),
    ]
    amb.renderizar_estudo(sc, modelos, 'amb_rochas', limite_tris=250, bioma_chao='deserto',
                          vistas_vitrine=vistas, espalhar_raio=(14.0, 10.0), n_espalhados=48,
                          escala_espalhados=(0.85, 1.18), dist_min=1.65)
    print("ESTUDO_AMB_ROCHAS OK")


if __name__ == '__main__':
    main()
