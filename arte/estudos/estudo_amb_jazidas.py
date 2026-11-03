"""
Estudo de ambiente — Grupo 7: Jazidas (PlanetaFactory).
Modelos (7):
  - jazida_areia   (dunas/ondas douradas em crescente, P_Areia)
  - jazida_carvao  (veio de antracito negro em blocos clivados paralelos, P_Carvao)
  - jazida_cobre   (cristas de cobre nativo alaranjado + crosta verde de malaquita, P_Cobre + P_Malaquita)
  - jazida_ferro   (formação ferrífera bandada vermelho-ferrugem em placas nodulares, P_Ferrugem)
  - jazida_pedra   (afloramento calcário/granítico claro em lajes tabulares, P_Pedra)
  - jazida_silex   (lascas conchoidais pontiagudas azul-aço em leque, P_Silex)
  - jazida_cristal (drusa/geodo de cristais turquesa luminosos sobre matriz violeta, P_Cristal + P_ChapeuCristal)
Limite rígido: <= 300 triângulos por modelo. Malha única (MESH), sem transparência, origem na base (z=0).
Deixam claro qual é o minério pela cor e pelo formato até a 30 m de altura.
"""
import os
import sys
import math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb

PI = math.pi


def criar_jazida_areia():
    """Jazida de areia (~0.82 x 0.76 x 0.14 m): três cristas dunares douradas em meia-lua com grãos minerais."""
    c = amb.ConstrutorMalha(['P_Areia', 'P_Pedra'])
    m_ar, m_pe = 0, 1

    # Três ondas de duna (barcanas suaves paralelas)
    ondas = [
        ([Vector((-0.34, -0.18, 0.01)), Vector((-0.14, -0.24, 0.055)), Vector((0.12, -0.22, 0.065)), Vector((0.34, -0.12, 0.01))],
         [0.08, 0.15, 0.14, 0.07]),
        ([Vector((-0.38, 0.02, 0.01)), Vector((-0.12, -0.02, 0.085)), Vector((0.15, 0.01, 0.095)), Vector((0.38, 0.10, 0.01))],
         [0.09, 0.18, 0.17, 0.08]),
        ([Vector((-0.30, 0.22, 0.01)), Vector((-0.06, 0.18, 0.065)), Vector((0.18, 0.21, 0.060)), Vector((0.32, 0.28, 0.01))],
         [0.07, 0.14, 0.13, 0.06]),
    ]
    for pts, raios in ondas:
        c.tubo_curvo(pts, raios, lados=6, mat=m_ar, tampar_base=True, tampar_topo=True)

    # Domos baixos de areia preenchendo o leito e 3 seixos claros nas bordas
    c.rocha_organica(Vector((0.0, 0.0, 0.04)), (0.36, 0.32, 0.055), mat=m_ar, semente=701, gomos=8, aneis=2, achatar_base=True)
    for pos_s, sem in ((Vector((-0.28, -0.22, 0.03)), 702), (Vector((0.30, 0.18, 0.03)), 703), (Vector((0.22, -0.26, 0.025)), 704)):
        c.rocha_organica(pos_s, (0.065, 0.055, 0.035), mat=m_pe, semente=sem, gomos=5, aneis=2, achatar_base=True)

    return c.finalizar('jazida_areia', escala_xy=0.82, escala_z=0.14)


def criar_jazida_carvao():
    """Jazida de carvão (~0.80 x 0.82 x 0.18 m): estratos prismáticos negros inclinados (clivagem cúbica/antracito)."""
    c = amb.ConstrutorMalha(['P_Carvao', 'P_RochaEscura'])
    m_cv, m_ro = 0, 1

    # Leito xistoso escuro na base
    c.rocha_organica(Vector((0.0, 0.0, 0.03)), (0.38, 0.36, 0.05), mat=m_ro, semente=710, gomos=7, aneis=2, achatar_base=True)

    # 7 prismas angulosos de carvão mineral inclinados na mesma direção geológica
    blocos = [
        (Vector((-0.18, -0.14, 0.01)), Vector((-0.08, -0.18, 0.17)), 0.12, 4),
        (Vector((0.02, -0.06, 0.01)), Vector((0.14, -0.10, 0.18)), 0.13, 4),
        (Vector((-0.08, 0.12, 0.01)), Vector((0.04, 0.08, 0.16)), 0.12, 4),
        (Vector((0.18, 0.10, 0.01)), Vector((0.28, 0.06, 0.14)), 0.10, 4),
        (Vector((-0.26, 0.04, 0.01)), Vector((-0.18, 0.0, 0.13)), 0.10, 4),
        (Vector((0.08, -0.24, 0.01)), Vector((0.16, -0.27, 0.12)), 0.09, 4),
        (Vector((-0.04, 0.26, 0.01)), Vector((0.04, 0.23, 0.11)), 0.09, 4),
    ]
    for p0, p1, r_b, lados in blocos:
        c.tubo_curvo([p0, p1], [r_b, r_b * 0.82], lados=lados, mat=m_cv, tampar_base=True, tampar_topo=True, torcao=0.15)

    return c.finalizar('jazida_carvao', escala_xy=0.80, escala_z=0.18)


def criar_jazida_cobre():
    """Jazida de cobre (~0.82 x 0.78 x 0.19 m): veios dendríticos de cobre nativo brilhante + crostas verdes de malaquita."""
    c = amb.ConstrutorMalha(['P_Cobre', 'P_Malaquita', 'P_Rocha'])
    m_cu, m_mal, m_ro = 0, 1, 2

    # Matriz rochosa basal
    c.rocha_organica(Vector((0.0, 0.0, 0.03)), (0.36, 0.34, 0.05), mat=m_ro, semente=720, gomos=7, aneis=2, achatar_base=True)

    # 4 domos oxidados verdes de malaquita (contraste imediato com o laranja metálico)
    for pos_m, r_m, sem in (
        (Vector((-0.18, 0.10, 0.06)), (0.17, 0.15, 0.08), 721),
        (Vector((0.18, -0.10, 0.06)), (0.16, 0.14, 0.08), 722),
        (Vector((0.04, 0.20, 0.05)), (0.14, 0.12, 0.07), 723),
        (Vector((-0.10, -0.20, 0.05)), (0.15, 0.13, 0.07), 724),
    ):
        c.rocha_organica(pos_m, r_m, mat=m_mal, semente=sem, gomos=6, aneis=2, achatar_base=True)

    # Veios e pepitas salientes de cobre nativo alaranjado no centro e diagonais
    veios = [
        (Vector((-0.26, -0.14, 0.02)), Vector((0.0, 0.0, 0.16)), Vector((0.26, 0.14, 0.03)), [0.07, 0.11, 0.07]),
        (Vector((-0.14, 0.22, 0.02)), Vector((0.02, 0.02, 0.14)), Vector((0.20, -0.20, 0.02)), [0.06, 0.095, 0.06]),
    ]
    for p0, pm, p2, raios in veios:
        c.tubo_curvo([p0, pm, p2], raios, lados=5, mat=m_cu, tampar_base=True, tampar_topo=True)

    # 3 pepitas facetadas de cobre puro no topo
    for pos_p, dir_p in (
        (Vector((0.0, 0.0, 0.04)), Vector((0.1, -0.1, 1.0))),
        (Vector((-0.14, -0.06, 0.03)), Vector((-0.3, -0.2, 1.0))),
        (Vector((0.14, 0.08, 0.03)), Vector((0.3, 0.2, 1.0))),
    ):
        c.cristal_facetado(pos_p, dir_p, comp=0.15, r_base=0.075, lados=5, mat=m_cu)

    return c.finalizar('jazida_cobre', escala_xy=0.82, escala_z=0.19)


def criar_jazida_ferro():
    """Jazida de ferro (~0.80 x 0.80 x 0.19 m): formação ferrífera bandada (hematita/limonita vermelho-ferrugem)
    em placas escalonadas pesadas."""
    c = amb.ConstrutorMalha(['P_Ferrugem', 'P_RochaEscura'])
    m_fe, m_ro = 0, 1

    # Base de magnetita/rocha escura
    c.rocha_organica(Vector((0.0, 0.0, 0.03)), (0.38, 0.38, 0.055), mat=m_ro, semente=730, gomos=8, aneis=2, achatar_base=True)

    # 6 nódulos/placas tabulares espessas de minério de ferro oxidado (vermelho-tijolo forte)
    placas = [
        (Vector((-0.04, 0.02, 0.08)), (0.24, 0.22, 0.12), m_fe, 731),
        (Vector((0.18, -0.12, 0.07)), (0.18, 0.16, 0.10), m_fe, 732),
        (Vector((-0.20, -0.14, 0.065)), (0.17, 0.15, 0.095), m_fe, 733),
        (Vector((0.14, 0.18, 0.065)), (0.17, 0.16, 0.095), m_fe, 734),
        (Vector((-0.16, 0.19, 0.06)), (0.15, 0.14, 0.085), m_fe, 735),
        (Vector((0.02, -0.24, 0.05)), (0.14, 0.12, 0.075), m_ro, 736),
    ]
    for pos, raios, mat, sem in placas:
        c.rocha_organica(pos, raios, mat=mat, semente=sem, gomos=6, aneis=2, achatar_base=True)

    return c.finalizar('jazida_ferro', escala_xy=0.80, escala_z=0.19)


def criar_jazida_pedra():
    """Jazida de pedra (~0.84 x 0.82 x 0.18 m): lajes tabulares claras de calcário/granito em degraus concêntricos."""
    c = amb.ConstrutorMalha(['P_Pedra', 'P_Rocha'])
    m_pe, m_ro = 0, 1

    # Lajes claras bem legíveis sobre o solo verde/marrom
    lajes = [
        (Vector((0.0, 0.0, 0.07)), (0.28, 0.25, 0.11), m_pe, 741),
        (Vector((-0.22, -0.12, 0.055)), (0.19, 0.17, 0.085), m_pe, 742),
        (Vector((0.22, 0.10, 0.055)), (0.18, 0.17, 0.085), m_pe, 743),
        (Vector((-0.10, 0.22, 0.05)), (0.17, 0.15, 0.075), m_ro, 744),
        (Vector((0.12, -0.22, 0.05)), (0.17, 0.15, 0.075), m_pe, 745),
        (Vector((-0.26, 0.12, 0.04)), (0.13, 0.12, 0.06), m_pe, 746),
        (Vector((0.26, -0.10, 0.04)), (0.13, 0.12, 0.06), m_ro, 747),
    ]
    for pos, raios, mat, sem in lajes:
        c.rocha_organica(pos, raios, mat=mat, semente=sem, gomos=6, aneis=2, achatar_base=True)

    return c.finalizar('jazida_pedra', escala_xy=0.84, escala_z=0.18)


def criar_jazida_silex():
    """Jazida de sílex (~0.78 x 0.74 x 0.18 m): lascas conchoidais pontiagudas azul-aço dispostas em roseta afiada."""
    c = amb.ConstrutorMalha(['P_Silex', 'P_RochaEscura'])
    m_si, m_ro = 0, 1

    # Base escura de córtex
    c.rocha_organica(Vector((0.0, 0.0, 0.03)), (0.34, 0.32, 0.05), mat=m_ro, semente=750, gomos=7, aneis=2, achatar_base=True)

    # 8 lascas cortantes azul-aço (prismas de 4 lados inclinados como pontas de lança)
    lascas = [
        (Vector((0.0, 0.0, 0.02)), Vector((0.08, -0.05, 1.0)), 0.18, 0.095),
        (Vector((-0.14, -0.08, 0.02)), Vector((-0.45, -0.25, 0.85)), 0.16, 0.080),
        (Vector((0.15, 0.07, 0.02)), Vector((0.45, 0.20, 0.85)), 0.16, 0.080),
        (Vector((-0.06, 0.15, 0.02)), Vector((-0.20, 0.50, 0.82)), 0.15, 0.075),
        (Vector((0.08, -0.15, 0.02)), Vector((0.25, -0.50, 0.82)), 0.15, 0.075),
        (Vector((-0.22, 0.06, 0.015)), Vector((-0.60, 0.15, 0.72)), 0.13, 0.065),
        (Vector((0.22, -0.06, 0.015)), Vector((0.60, -0.15, 0.72)), 0.13, 0.065),
        (Vector((0.0, -0.24, 0.015)), Vector((0.0, -0.65, 0.70)), 0.12, 0.060),
    ]
    for pos, direcao, comp, rb in lascas:
        c.cristal_facetado(pos, direcao, comp=comp, r_base=rb, lados=4, mat=m_si)

    return c.finalizar('jazida_silex', escala_xy=0.78, escala_z=0.18)


def criar_jazida_cristal():
    """Jazida de cristal (~0.72 x 0.68 x 0.32 m): geodo aberto violeta com feixe radiante de 9 cristais ciano-turquesa."""
    c = amb.ConstrutorMalha(['P_Cristal', 'P_ChapeuCristal', 'P_RochaEscura'])
    m_cr, m_geo, m_ro = 0, 1, 2

    # Anel de matriz de geodo violeta/rocha na base
    c.rocha_organica(Vector((0.0, 0.0, 0.04)), (0.34, 0.32, 0.07), mat=m_geo, semente=760, gomos=8, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((-0.18, -0.12, 0.03)), (0.16, 0.14, 0.05), mat=m_ro, semente=761, gomos=6, aneis=2, achatar_base=True)

    # 9 prismas hexagonais/pentagonais de cristal luminoso brotando em drusa
    pontas = [
        (Vector((0.0, 0.0, 0.03)), Vector((0.02, -0.02, 1.0)), 0.30, 0.072, 6),
        (Vector((-0.10, 0.06, 0.03)), Vector((-0.32, 0.18, 0.92)), 0.25, 0.058, 5),
        (Vector((0.11, -0.05, 0.03)), Vector((0.34, -0.16, 0.90)), 0.24, 0.056, 5),
        (Vector((0.04, 0.12, 0.03)), Vector((0.12, 0.38, 0.88)), 0.22, 0.052, 5),
        (Vector((-0.05, -0.12, 0.03)), Vector((-0.15, -0.38, 0.88)), 0.22, 0.052, 5),
        (Vector((-0.18, -0.06, 0.02)), Vector((-0.55, -0.20, 0.78)), 0.18, 0.045, 5),
        (Vector((0.18, 0.08, 0.02)), Vector((0.55, 0.24, 0.78)), 0.18, 0.045, 5),
        (Vector((-0.08, 0.18, 0.02)), Vector((-0.25, 0.58, 0.75)), 0.16, 0.042, 5),
        (Vector((0.10, -0.17, 0.02)), Vector((0.30, -0.55, 0.75)), 0.16, 0.042, 5),
    ]
    for pos, direcao, comp, rb, lados in pontas:
        c.cristal_facetado(pos, direcao, comp=comp, r_base=rb, lados=lados, mat=m_cr)

    return c.finalizar('jazida_cristal', escala_xy=0.72, escala_z=0.32)


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_jazida_ferro(),
        criar_jazida_cobre(),
        criar_jazida_carvao(),
        criar_jazida_pedra(),
        criar_jazida_areia(),
        criar_jazida_silex(),
        criar_jazida_cristal(),
    ]
    # Duas fileiras na vitrine (4 na frente, 3 atrás) para ficarem grandes e bem legíveis
    posicoes = [
        (-1.45, -0.58), (-0.48, -0.58), (0.48, -0.58), (1.45, -0.58),
        (-0.98, 0.58), (0.0, 0.58), (0.98, 0.58),
    ]
    for o, (px, py) in zip(modelos, posicoes):
        o.location = Vector((px, py, 0.0))

    vistas = [
        ('amb_jazidas_0.png', (0.0, -5.4, 3.5), (0.0, 0.0, 0.10), 35.0, 1500, 1000),
        ('amb_jazidas_1.png', (3.6, -3.4, 2.7), (0.0, 0.0, 0.10), 38.0, 1500, 1000),
        ('amb_jazidas_perto.png', (0.4, -2.2, 1.30), (0.1, -0.2, 0.10), 36.0, 1500, 1000),
    ]
    # No campo de 30m, criamos agrupamentos (manchas de 4..6 jazidas do mesmo tipo, como no jogo real!)
    amb.renderizar_estudo(sc, modelos, 'amb_jazidas', limite_tris=300, bioma_chao='campina',
                          vistas_vitrine=vistas, espalhar_raio=(12.0, 8.5), n_espalhados=70,
                          escala_espalhados=(0.95, 1.15), dist_min=0.95)
    print("ESTUDO_AMB_JAZIDAS OK")


if __name__ == '__main__':
    main()
