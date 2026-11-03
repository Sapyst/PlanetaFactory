"""
Estudo de ambiente — Grupo 4: Cogumelo gigante (PlanetaFactory).
Modelos (2):
  - cogumelo_gigante_a (~0.92 x 0.91 x 1.60 m)
  - cogumelo_gigante_b (~0.92 x 0.91 x 2.08 m)
Limite rígido: <= 600 triângulos por modelo. Malha única (MESH), sem transparência, origem na base (z=0).
"""
import os
import sys
import math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb

PI = math.pi


def criar_cogumelo_gigante_a():
    """Cogumelo gigante A (~1.60 m): estipe robusto com anel membranoso, grande chapéu abaulado com pintas
    em relevo e dois cogumelos jovens brotando da base micelial."""
    c = amb.ConstrutorMalha(['P_FungoCaule', 'P_Chapeu', 'P_ChapeuCristal', 'P_Cristal', 'P_Lodo'])
    m_caule, m_chap, m_pinta, m_luz, m_base = 0, 1, 2, 3, 4

    # Colar micelial na base
    c.rocha_organica(Vector((0.0, 0.0, 0.06)), (0.24, 0.22, 0.09), mat=m_base, semente=14, gomos=8, aneis=2, achatar_base=True)

    # Estipe principal bulboso e levemente arqueado
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((0.02, -0.02, 0.34)),
        Vector((-0.03, 0.02, 0.72)),
        Vector((-0.02, 0.01, 1.08)),
        Vector((0.0, 0.0, 1.32)),
    ], [0.16, 0.125, 0.10, 0.09, 0.11], lados=8, mat=m_caule, tampar_base=True, tampar_topo=True)

    # Anel (saia do estipe) a meia altura
    c.chapeu_cogumelo(Vector((-0.02, 0.01, 0.92)), r_base=0.19, altura=0.08, espessura_borda=0.025,
                      lados=8, mat_topo=m_caule, mat_baixo=m_luz, semente=21)

    # Grande chapéu principal abaulado com himênio luminoso por baixo
    c.chapeu_cogumelo(Vector((0.0, 0.0, 1.24)), r_base=0.45, altura=0.35, espessura_borda=0.055,
                      lados=9, mat_topo=m_chap, mat_baixo=m_luz, semente=33)

    # Verrugas/pintas salientes sobre o chapéu (prismas baixos de 5 lados)
    pintas = [
        (Vector((0.16, 0.08, 1.43)), Vector((0.3, 0.15, 1.0)), 0.055, 0.055),
        (Vector((-0.18, 0.10, 1.41)), Vector((-0.3, 0.2, 1.0)), 0.050, 0.050),
        (Vector((0.04, -0.22, 1.39)), Vector((0.1, -0.4, 1.0)), 0.055, 0.055),
        (Vector((-0.08, -0.14, 1.46)), Vector((-0.15, -0.25, 1.0)), 0.048, 0.048),
        (Vector((-0.02, 0.22, 1.38)), Vector((0.0, 0.4, 1.0)), 0.052, 0.052),
    ]
    for pos_p, dir_p, comp_p, rb_p in pintas:
        c.cristal_facetado(pos_p, dir_p, comp=comp_p, r_base=rb_p, lados=5, mat=m_pinta)

    # Dois cogumelos jovens laterais na base
    for p_ini, p_fim, r_ch, alt_ch, sem in (
        (Vector((0.12, -0.08, 0.0)), Vector((0.28, -0.18, 0.44)), 0.16, 0.14, 51),
        (Vector((-0.11, 0.10, 0.0)), Vector((-0.24, 0.20, 0.34)), 0.13, 0.11, 52),
    ):
        pm = (p_ini + p_fim) * 0.5 + Vector((0, 0, 0.02))
        c.tubo_curvo([p_ini, pm, p_fim], [0.055, 0.042, 0.035], lados=5, mat=m_caule, tampar_base=True, tampar_topo=True)
        c.chapeu_cogumelo(p_fim - Vector((0, 0, 0.03)), r_base=r_ch, altura=alt_ch, espessura_borda=0.025,
                          lados=6, mat_topo=m_chap, mat_baixo=m_luz, semente=sem)

    return c.finalizar('cogumelo_gigante_a', escala_xy=0.91, escala_z=1.60)


def criar_cogumelo_gigante_b():
    """Cogumelo gigante B (~2.08 m): colônia simbiótica alta de três níveis com chapéu campanulado alto,
    cogumelo médio secundário, orelhas-de-pau no caule e esporângios de cristal."""
    c = amb.ConstrutorMalha(['P_FungoCaule', 'P_Chapeu', 'P_ChapeuCristal', 'P_Cristal', 'P_Lodo'])
    m_caule, m_chap, m_pinta, m_luz, m_base = 0, 1, 2, 3, 4

    # Base micelial
    c.rocha_organica(Vector((0.0, 0.0, 0.07)), (0.25, 0.23, 0.10), mat=m_base, semente=64, gomos=7, aneis=2, achatar_base=True)

    # Estipe principal alto e sinuoso (~2.08 m no topo do chapéu)
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((-0.05, 0.03, 0.42)),
        Vector((0.04, -0.03, 0.92)),
        Vector((0.06, 0.02, 1.38)),
        Vector((0.02, 0.01, 1.72)),
    ], [0.15, 0.115, 0.092, 0.078, 0.090], lados=7, mat=m_caule, tampar_base=True, tampar_topo=True)

    # Chapéu superior campanulado/cônico
    c.chapeu_cogumelo(Vector((0.02, 0.01, 1.63)), r_base=0.41, altura=0.44, espessura_borda=0.055,
                      lados=9, mat_topo=m_chap, mat_baixo=m_luz, semente=77)

    # Cogumelo secundário médio abrindo para a esquerda
    c.tubo_curvo([
        Vector((-0.03, 0.01, 0.22)),
        Vector((-0.18, -0.08, 0.62)),
        Vector((-0.24, -0.12, 1.02)),
    ], [0.095, 0.072, 0.065], lados=6, mat=m_caule, tampar_base=False, tampar_topo=True)
    c.chapeu_cogumelo(Vector((-0.24, -0.12, 0.96)), r_base=0.27, altura=0.24, espessura_borda=0.04,
                      lados=7, mat_topo=m_chap, mat_baixo=m_luz, semente=88)

    # Cogumelo terciário baixo para a direita
    c.tubo_curvo([
        Vector((0.06, 0.04, 0.10)),
        Vector((0.22, 0.14, 0.48)),
    ], [0.068, 0.048], lados=5, mat=m_caule, tampar_base=False, tampar_topo=True)
    c.chapeu_cogumelo(Vector((0.22, 0.14, 0.44)), r_base=0.18, altura=0.16, espessura_borda=0.03,
                      lados=6, mat_topo=m_pinta, mat_baixo=m_luz, semente=92)

    # Orelhas-de-pau (fungos de prateleira) no estipe principal
    for z_pr, ang in ((0.76, 0.4), (1.18, 2.3), (1.42, -1.2)):
        pos_pr = Vector((math.cos(ang) * 0.09, math.sin(ang) * 0.09, z_pr))
        c.chapeu_cogumelo(pos_pr, r_base=0.13, altura=0.06, espessura_borda=0.022,
                          lados=5, mat_topo=m_pinta, mat_baixo=m_luz, semente=int(z_pr * 100))

    # Pintas de cristal no chapéu superior
    for pos_p, dir_p in (
        (Vector((0.15, 0.08, 1.84)), Vector((0.3, 0.15, 1.0))),
        (Vector((-0.14, -0.09, 1.82)), Vector((-0.3, -0.2, 1.0))),
        (Vector((0.02, -0.18, 1.78)), Vector((0.05, -0.35, 1.0))),
        (Vector((-0.04, 0.17, 1.80)), Vector((-0.1, 0.35, 1.0))),
    ):
        c.cristal_facetado(pos_p, dir_p, comp=0.065, r_base=0.048, lados=5, mat=m_pinta)

    return c.finalizar('cogumelo_gigante_b', escala_xy=0.91, escala_z=2.08)


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_cogumelo_gigante_a(),
        criar_cogumelo_gigante_b(),
    ]
    modelos[0].location = Vector((-0.85, 0.0, 0.0))
    modelos[1].location = Vector((0.85, 0.0, 0.0))

    vistas = [
        ('amb_cogumelos_0.png', (0.0, -4.4, 2.3), (0.0, 0.0, 0.90), 38.0, 1400, 950),
        ('amb_cogumelos_1.png', (3.4, 3.2, 2.4), (0.0, 0.0, 0.90), 38.0, 1400, 950),
        ('amb_cogumelos_perto.png', (1.1, -2.3, 1.25), (0.1, 0.0, 0.85), 36.0, 1400, 950),
    ]
    amb.renderizar_estudo(sc, modelos, 'amb_cogumelos', limite_tris=600, bioma_chao='fungos',
                          vistas_vitrine=vistas, espalhar_raio=(13.5, 9.5), n_espalhados=46,
                          escala_espalhados=(0.86, 1.18), dist_min=1.45)
    print("ESTUDO_AMB_COGUMELOS OK")


if __name__ == '__main__':
    main()
