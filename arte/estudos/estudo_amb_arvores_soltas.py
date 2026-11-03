"""
Estudo de ambiente — Grupo 2: Árvores soltas (PlanetaFactory).
Modelos (3):
  - arvore_campina_a (~0.68 x 0.78 x 1.49 m)
  - arvore_campina_b (~0.68 x 0.59 x 1.75 m)
  - arvore_morta     (~0.59 x 0.47 x 1.32 m)
Limite rígido: <= 400 triângulos por modelo. Malha única (MESH), sem transparência, origem na base (z=0).
"""
import os
import sys
import math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb

PI = math.pi


def criar_arvore_campina_a():
    """Árvore de campina A: copa baixa, farta e assimétrica com tronco bifurcado robusto (~1.50 m)."""
    c = amb.ConstrutorMalha(['P_Tronco', 'P_Folha', 'P_FolhaClara'])
    m_tr, m_f1, m_f2 = 0, 1, 2

    # Tronco robusto com raízes largas na base
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((0.02, -0.02, 0.24)),
        Vector((-0.02, 0.03, 0.52)),
        Vector((-0.04, 0.02, 0.78)),
    ], [0.14, 0.10, 0.08, 0.06], lados=6, mat=m_tr, tampar_base=True, tampar_topo=True)

    # Raízes salientes
    for a in (0.3, 2.4, 4.5):
        c.tubo_curvo([
            Vector((math.cos(a) * 0.06, math.sin(a) * 0.06, 0.14)),
            Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.0)),
        ], [0.045, 0.024], lados=4, mat=m_tr, tampar_base=False, tampar_topo=True)

    # Galhos principais abrindo em 3 direções
    galhos = [
        (Vector((-0.02, 0.02, 0.50)), Vector((-0.20, -0.14, 0.88)), 0.22, 0.19, m_f1),
        (Vector((-0.03, 0.02, 0.56)), Vector((0.20, 0.12, 0.94)), 0.21, 0.18, m_f1),
        (Vector((-0.03, 0.02, 0.64)), Vector((0.04, -0.22, 0.98)), 0.20, 0.17, m_f2),
    ]
    for p0, p2, r_xy, r_z, m_fol in galhos:
        pm = (p0 + p2) * 0.5 + Vector((0, 0, -0.04))
        c.tubo_curvo([p0, pm, p2], [0.055, 0.04, 0.025], lados=5, mat=m_tr, tampar_base=False, tampar_topo=True)
        c.tufo_folha(p2 + Vector((0, 0, 0.04)), (r_xy, r_xy * 0.94, r_z), mat=m_fol, semente=int(abs(p2.x * 100) + 11), gomos=6, aneis=3)

    # Domo central e topo iluminado
    c.tufo_folha(Vector((-0.03, 0.02, 1.05)), (0.28, 0.26, 0.23), mat=m_f1, semente=31, gomos=7, aneis=3)
    c.tufo_folha(Vector((0.02, 0.05, 1.29)), (0.21, 0.19, 0.19), mat=m_f2, semente=47, gomos=6, aneis=3)

    return c.finalizar('arvore_campina_a', escala_xy=0.72, escala_z=1.49)


def criar_arvore_campina_b():
    """Árvore de campina B: mais alta e esguia (~1.75 m), tronco sinuoso e três patamares de copa."""
    c = amb.ConstrutorMalha(['P_Tronco', 'P_Folha', 'P_FolhaClara'])
    m_tr, m_f1, m_f2 = 0, 1, 2

    # Tronco sinuoso subindo até o patamar superior
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((-0.03, 0.02, 0.34)),
        Vector((0.04, -0.03, 0.72)),
        Vector((0.01, 0.03, 1.12)),
        Vector((-0.02, 0.01, 1.42)),
    ], [0.13, 0.095, 0.075, 0.055, 0.035], lados=6, mat=m_tr, tampar_base=True, tampar_topo=True)

    # Raízes na base
    for a in (1.1, 3.6):
        c.tubo_curvo([
            Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.13)),
            Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 0.0)),
        ], [0.04, 0.022], lados=4, mat=m_tr, tampar_base=False, tampar_topo=True)

    # Patamar inferior lateral
    p_b1 = Vector((0.01, -0.01, 0.62))
    p_f1 = Vector((-0.19, -0.11, 0.88))
    c.tubo_curvo([p_b1, (p_b1 + p_f1) * 0.5, p_f1], [0.048, 0.035, 0.022], lados=5, mat=m_tr, tampar_base=False, tampar_topo=True)
    c.tufo_folha(p_f1 + Vector((0, 0, 0.04)), (0.19, 0.17, 0.16), mat=m_f1, semente=61, gomos=6, aneis=3)

    # Patamar médio oposto
    p_b2 = Vector((0.03, 0.0, 0.90))
    p_f2 = Vector((0.18, 0.10, 1.18))
    c.tubo_curvo([p_b2, (p_b2 + p_f2) * 0.5, p_f2], [0.045, 0.032, 0.020], lados=5, mat=m_tr, tampar_base=False, tampar_topo=True)
    c.tufo_folha(p_f2 + Vector((0, 0, 0.04)), (0.21, 0.19, 0.18), mat=m_f1, semente=73, gomos=6, aneis=3)

    # Copa principal e coroa clara no alto
    c.tufo_folha(Vector((-0.03, 0.03, 1.38)), (0.24, 0.22, 0.21), mat=m_f1, semente=89, gomos=7, aneis=3)
    c.tufo_folha(Vector((-0.01, -0.02, 1.59)), (0.18, 0.16, 0.16), mat=m_f2, semente=97, gomos=6, aneis=3)

    return c.finalizar('arvore_campina_b', escala_xy=0.64, escala_z=1.75)


def criar_arvore_morta():
    """Árvore seca e retorcida (~1.32 m): madeira acinzentada e galhos quebrados sem folhagem."""
    c = amb.ConstrutorMalha(['P_Tronco', 'P_Cinza'])
    m_tr, m_cz = 0, 1

    # Tronco principal retorcido com ponta lascada
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((0.03, -0.02, 0.25)),
        Vector((-0.04, 0.03, 0.54)),
        Vector((-0.08, 0.05, 0.85)),
        Vector((-0.14, 0.08, 1.12)),
    ], [0.13, 0.095, 0.072, 0.048, 0.018], lados=6, mat=m_tr, tampar_base=True, tampar_topo=True)

    # Três raízes secas retorcidas agarrando o solo
    for a, comp in ((0.4, 0.22), (2.5, 0.20), (4.6, 0.24)):
        c.tubo_curvo([
            Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.15)),
            Vector((math.cos(a) * comp * 0.6, math.sin(a) * comp * 0.6, 0.07)),
            Vector((math.cos(a) * comp, math.sin(a) * comp, 0.0)),
        ], [0.048, 0.034, 0.018], lados=4, mat=m_cz, tampar_base=False, tampar_topo=True)

    # Galho principal direito subindo até 1.32 m com ramificações quebradas
    c.tubo_curvo([
        Vector((-0.02, 0.01, 0.48)),
        Vector((0.09, -0.05, 0.76)),
        Vector((0.18, -0.10, 1.06)),
        Vector((0.23, -0.14, 1.32)),
    ], [0.062, 0.044, 0.028, 0.012], lados=5, mat=m_tr, tampar_base=False, tampar_topo=True)

    # Galhos secundários quebrados em ângulos secos
    ramos_secos = [
        ([Vector((0.09, -0.05, 0.74)), Vector((0.24, 0.08, 0.90)), Vector((0.30, 0.14, 1.02))], [0.034, 0.022, 0.010], m_cz),
        ([Vector((-0.05, 0.04, 0.68)), Vector((-0.20, -0.12, 0.84)), Vector((-0.27, -0.18, 0.96))], [0.038, 0.024, 0.010], m_cz),
        ([Vector((-0.09, 0.06, 0.90)), Vector((-0.02, 0.20, 1.10)), Vector((0.02, 0.26, 1.22))], [0.030, 0.018, 0.009], m_cz),
        ([Vector((0.16, -0.09, 1.00)), Vector((0.08, -0.21, 1.15))], [0.024, 0.010], m_cz),
    ]
    for pts, raios, mat_g in ramos_secos:
        c.tubo_curvo(pts, raios, lados=4, mat=mat_g, tampar_base=False, tampar_topo=True)

    return c.finalizar('arvore_morta', escala_xy=0.58, escala_z=1.32)


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_arvore_campina_a(),
        criar_arvore_campina_b(),
        criar_arvore_morta(),
    ]
    posicoes = [(-1.4, 0.0), (0.0, 0.0), (1.4, 0.0)]
    for o, (px, py) in zip(modelos, posicoes):
        o.location = Vector((px, py, 0.0))

    vistas = [
        ('amb_arvores_soltas_0.png', (0.0, -4.6, 2.4), (0.0, 0.0, 0.75), 38.0, 1400, 950),
        ('amb_arvores_soltas_1.png', (3.6, 3.4, 2.5), (0.0, 0.0, 0.75), 38.0, 1400, 950),
        ('amb_arvores_soltas_perto.png', (1.2, -2.5, 1.4), (0.2, 0.0, 0.72), 36.0, 1400, 950),
    ]
    amb.renderizar_estudo(sc, modelos, 'amb_arvores_soltas', limite_tris=400, bioma_chao='campina',
                          vistas_vitrine=vistas, espalhar_raio=(13.5, 9.5), n_espalhados=48,
                          escala_espalhados=(0.88, 1.16), dist_min=1.35)
    print("ESTUDO_AMB_ARVORES_SOLTAS OK")


if __name__ == '__main__':
    main()
