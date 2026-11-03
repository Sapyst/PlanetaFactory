"""
Estudo de ambiente — Grupo 6: Montanhas (PlanetaFactory).
Modelos (2):
  - montanha_3x3 (~2.67 x 2.54 x 2.60 m, ocupa 3x3 tiles)
  - montanha_5x5 (~4.81 x 4.42 x 4.20 m, ocupa 5x5 tiles)
Limite rígido: <= 1.200 triângulos por modelo. Malha única (MESH), sem transparência, origem na base (z=0).
"""
import os
import sys
import math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb

PI = math.pi


def criar_montanha_3x3():
    """Maciço rochoso 3x3 (~2.67 x 2.54 x 2.60 m): pico principal estratificado, ombro basáltico secundário,
    terraços de escarpa e contrafortes de sopé."""
    c = amb.ConstrutorMalha(['P_Rocha', 'P_RochaEscura', 'P_Pedra', 'P_Lodo'])
    m_r1, m_esc, m_ped, m_mus = 0, 1, 2, 3

    # Pico principal central-noroeste subindo a 2.60 m
    c.rocha_estrato(Vector((-0.18, 0.12, 0.0)), rx=0.92, ry=0.86, h=2.60, mat=m_r1,
                    lados=9, degraus=4, inclinacao=(0.08, -0.05), semente=601, fundo=0.0)

    # Pico secundário escuro (ombro sudeste)
    c.rocha_estrato(Vector((0.46, -0.28, 0.0)), rx=0.76, ry=0.72, h=1.96, mat=m_esc,
                    lados=8, degraus=3, inclinacao=(-0.06, 0.05), semente=602, fundo=0.0)

    # Terceira agulha/platô nordeste
    c.rocha_estrato(Vector((0.34, 0.44, 0.0)), rx=0.66, ry=0.62, h=1.55, mat=m_ped,
                    lados=8, degraus=3, inclinacao=(0.04, 0.04), semente=603, fundo=0.0)

    # 6 contrafortes e blocos de tálus cercando o sopé dentro do quadrado 3x3
    contrafortes = [
        (Vector((-0.68, -0.44, 0.0)), 0.56, 0.52, 1.15, m_esc, 611),
        (Vector((-0.56, 0.58, 0.0)), 0.52, 0.48, 1.05, m_ped, 612),
        (Vector((0.08, -0.68, 0.0)), 0.54, 0.48, 0.92, m_r1, 613),
        (Vector((0.72, 0.10, 0.0)), 0.48, 0.52, 0.98, m_r1, 614),
        (Vector((-0.14, 0.72, 0.0)), 0.50, 0.44, 0.86, m_esc, 615),
        (Vector((-0.82, 0.06, 0.0)), 0.44, 0.48, 0.78, m_ped, 616),
    ]
    for pos, rx, ry, h, mat, sem in contrafortes:
        c.rocha_estrato(pos, rx=rx, ry=ry, h=h, mat=mat, lados=7, degraus=2, semente=sem, fundo=0.0)

    # Dois patamares de vegetação rasteira/líquen nas fendas úmidas do sopé
    c.tufo_folha(Vector((-0.36, -0.48, 0.62)), (0.28, 0.24, 0.10), mat=m_mus, semente=620, gomos=5, aneis=2)
    c.tufo_folha(Vector((0.42, 0.28, 0.78)), (0.25, 0.22, 0.09), mat=m_mus, semente=621, gomos=5, aneis=2)

    return c.finalizar('montanha_3x3', escala_xy=2.66, escala_z=2.60)


def criar_montanha_5x5():
    """Cordilheira/maciço 5x5 (~4.81 x 4.42 x 4.20 m): cume principal imponente, duas cristas laterais,
    colo rochoso estratificado e anel de contrafortes de tálus."""
    c = amb.ConstrutorMalha(['P_Rocha', 'P_RochaEscura', 'P_Pedra', 'P_Lodo'])
    m_r1, m_esc, m_ped, m_mus = 0, 1, 2, 3

    # Cume central dominante (4.20 m)
    c.rocha_estrato(Vector((-0.15, 0.10, 0.0)), rx=1.45, ry=1.35, h=4.20, mat=m_r1,
                    lados=10, degraus=5, inclinacao=(0.07, -0.04), semente=701, fundo=0.0)

    # Crista leste alta (3.25 m)
    c.rocha_estrato(Vector((0.92, -0.35, 0.0)), rx=1.18, ry=1.12, h=3.25, mat=m_esc,
                    lados=9, degraus=4, inclinacao=(-0.08, 0.05), semente=702, fundo=0.0)

    # Crista oeste/sudoeste (2.85 m)
    c.rocha_estrato(Vector((-0.98, -0.42, 0.0)), rx=1.12, ry=1.05, h=2.85, mat=m_ped,
                    lados=9, degraus=4, inclinacao=(0.06, 0.06), semente=703, fundo=0.0)

    # Torreão norte (2.45 m)
    c.rocha_estrato(Vector((0.35, 0.88, 0.0)), rx=1.02, ry=0.95, h=2.45, mat=m_r1,
                    lados=8, degraus=3, inclinacao=(-0.04, -0.06), semente=704, fundo=0.0)

    # 8 contrafortes periféricos formando a saia geológica 5x5
    saia = [
        (Vector((-1.35, 0.68, 0.0)), 0.88, 0.82, 1.75, m_esc, 711),
        (Vector((-0.55, 1.22, 0.0)), 0.84, 0.78, 1.60, m_ped, 712),
        (Vector((1.22, 0.72, 0.0)), 0.86, 0.80, 1.68, m_esc, 713),
        (Vector((1.48, -0.12, 0.0)), 0.80, 0.86, 1.52, m_r1, 714),
        (Vector((0.42, -1.24, 0.0)), 0.92, 0.78, 1.58, m_ped, 715),
        (Vector((-0.48, -1.26, 0.0)), 0.86, 0.76, 1.44, m_r1, 716),
        (Vector((-1.52, -0.15, 0.0)), 0.78, 0.84, 1.48, m_esc, 717),
        (Vector((0.98, -1.08, 0.0)), 0.74, 0.70, 1.22, m_r1, 718),
    ]
    for pos, rx, ry, h, mat, sem in saia:
        c.rocha_estrato(pos, rx=rx, ry=ry, h=h, mat=mat, lados=7, degraus=2, semente=sem, fundo=0.0)

    # Manchas de líquen/musgo alpino nos platôs intermediários
    for pos_m, r_m, sem in (
        (Vector((-0.45, -0.78, 1.15)), (0.42, 0.36, 0.14), 731),
        (Vector((0.68, 0.38, 1.38)), (0.38, 0.34, 0.13), 732),
        (Vector((-0.72, 0.52, 1.28)), (0.36, 0.32, 0.12), 733),
    ):
        c.tufo_folha(pos_m, r_m, mat=m_mus, semente=sem, gomos=5, aneis=2)

    return c.finalizar('montanha_5x5', escala_xy=4.68, escala_z=4.20)


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_montanha_3x3(),
        criar_montanha_5x5(),
    ]
    modelos[0].location = Vector((-2.6, 0.0, 0.0))
    modelos[1].location = Vector((2.2, 0.0, 0.0))

    vistas = [
        ('amb_montanhas_0.png', (0.2, -12.6, 6.6), (0.2, 0.0, 1.6), 38.0, 1500, 1000),
        ('amb_montanhas_1.png', (9.8, -9.2, 6.4), (0.2, 0.0, 1.6), 38.0, 1500, 1000),
        ('amb_montanhas_perto.png', (-0.6, -7.2, 3.4), (0.3, 0.0, 1.5), 36.0, 1500, 1000),
    ]
    amb.renderizar_estudo(sc, modelos, 'amb_montanhas', limite_tris=1200, bioma_chao='campina',
                          vistas_vitrine=vistas, espalhar_raio=(15.0, 11.0), n_espalhados=14,
                          escala_espalhados=(0.90, 1.12), dist_min=4.8)
    print("ESTUDO_AMB_MONTANHAS OK")


if __name__ == '__main__':
    main()
