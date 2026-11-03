"""
Estudo de ambiente — Grupo 3: Plantas (PlanetaFactory).
Modelos (5):
  - arbusto        (~0.62 x 0.57 x 0.43 m)
  - junco          (~0.25 x 0.34 x 0.73 m)
  - flor_luminosa  (~0.24 x 0.20 x 0.36 m)
  - cacto_cristal  (~0.50 x 0.22 x 1.03 m)
  - vitoria_regia  (~0.52 x 0.42 x 0.06 m)
Limite rígido: <= 200 triângulos por modelo. Malha única (MESH), com espessura, sem transparência, origem na base (z=0).
"""
import os
import sys
import math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb

PI = math.pi


def criar_arbusto():
    """Arbusto denso de campina com galhos basais curtos e gomos folhosos sobrepostos (~0.62 x 0.57 x 0.43 m)."""
    c = amb.ConstrutorMalha(['P_Tronco', 'P_Folha', 'P_FolhaClara'])
    m_tr, m_f1, m_f2 = 0, 1, 2

    # Pequena base lenhosa tripartida
    for a in (0.4, 2.5, 4.6):
        c.tubo_curvo([
            Vector((0.0, 0.0, 0.0)),
            Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.14)),
        ], [0.045, 0.025], lados=4, mat=m_tr, tampar_base=True, tampar_topo=False)

    # 4 tufos volumosos orgânicos interpenetrados
    c.tufo_folha(Vector((-0.11, -0.06, 0.18)), (0.19, 0.17, 0.15), mat=m_f1, semente=11, gomos=6, aneis=2)
    c.tufo_folha(Vector((0.12, -0.05, 0.19)), (0.18, 0.17, 0.15), mat=m_f1, semente=22, gomos=6, aneis=2)
    c.tufo_folha(Vector((0.0, 0.10, 0.20)), (0.19, 0.18, 0.16), mat=m_f1, semente=33, gomos=6, aneis=2)
    c.tufo_folha(Vector((0.01, -0.01, 0.29)), (0.18, 0.16, 0.14), mat=m_f2, semente=44, gomos=6, aneis=2)

    return c.finalizar('arbusto', escala_xy=0.61, escala_z=0.43)


def criar_junco():
    """Moita de juncos de margem d'água (~0.28 x 0.34 x 0.73 m) com hastes, espigas de taboa e lâminas arqueadas."""
    c = amb.ConstrutorMalha(['P_Folha', 'P_FolhaClara', 'P_Tronco'])
    m_f1, m_f2, m_esp = 0, 1, 2

    # 4 hastes de junco com espiga cilíndrica escura (taboa) perto da ponta
    hastes = [
        (Vector((-0.04, -0.03, 0.0)), Vector((-0.07, -0.05, 0.72)), True),
        (Vector((0.04, 0.02, 0.0)), Vector((0.08, 0.05, 0.66)), True),
        (Vector((-0.01, 0.05, 0.0)), Vector((-0.02, 0.10, 0.58)), True),
        (Vector((0.03, -0.05, 0.0)), Vector((0.06, -0.09, 0.52)), False),
    ]
    for p0, p2, tem_espiga in hastes:
        pm = (p0 + p2) * 0.5 + Vector(((p2.x - p0.x) * 0.2, (p2.y - p0.y) * 0.2, 0.02))
        c.tubo_curvo([p0, pm, p2], [0.016, 0.013, 0.007], lados=4, mat=m_f1, tampar_base=True, tampar_topo=True)
        if tem_espiga:
            pa = p0.lerp(p2, 0.68)
            pb = p0.lerp(p2, 0.88)
            c.tubo_curvo([pa, pb], [0.026, 0.024], lados=5, mat=m_esp, tampar_base=True, tampar_topo=True)

    # 5 lâminas arqueadas com espessura real
    for a, alt, inc in ((0.2, 0.44, 0.14), (1.5, 0.50, 0.16), (2.8, 0.38, 0.13), (4.1, 0.46, 0.15), (5.3, 0.36, 0.12)):
        dir_xy = Vector((math.cos(a), math.sin(a), 0.0))
        p_ini = dir_xy * 0.02
        p_fim = dir_xy * inc + Vector((0, 0, alt))
        c.lamina_folha(p_ini, p_fim, larg_max=0.032, espessura=0.012, arco=0.04, mat=m_f2)

    return c.finalizar('junco', escala_xy=0.31, escala_z=0.73)


def criar_flor_luminosa():
    """Flor bioluminescente (~0.24 x 0.20 x 0.36 m): roseta de folhas basais e cálice pendente com núcleo de cristal."""
    c = amb.ConstrutorMalha(['P_Folha', 'P_FolhaClara', 'P_ChapeuCristal', 'P_Cristal'])
    m_f1, m_f2, m_pet, m_luz = 0, 1, 2, 3

    # 4 folhas basais curvas com espessura
    for i in range(4):
        a = i * (PI / 2.0) + 0.35
        dir_xy = Vector((math.cos(a), math.sin(a), 0.0))
        c.lamina_folha(dir_xy * 0.015, dir_xy * 0.11 + Vector((0, 0, 0.08)), larg_max=0.048, espessura=0.015, arco=0.03, mat=m_f1)

    # Haste principal arqueada e haste secundária menor
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((-0.02, 0.01, 0.14)),
        Vector((0.02, 0.01, 0.27)),
        Vector((0.06, 0.0, 0.33)),
    ], [0.022, 0.016, 0.013, 0.010], lados=5, mat=m_f2, tampar_base=True, tampar_topo=True)

    # Cálice de pétalas e bulbo bioluminescente principal
    p_flor = Vector((0.06, 0.0, 0.31))
    c.chapeu_cogumelo(p_flor, r_base=0.065, altura=0.055, espessura_borda=0.016, lados=6, mat_topo=m_pet, mat_baixo=m_luz, semente=19)
    c.cristal_facetado(p_flor - Vector((0, 0, 0.045)), Vector((0.01, 0.0, 1.0)), comp=0.065, r_base=0.032, lados=5, mat=m_luz)

    # Botão luminoso secundário mais baixo
    c.tubo_curvo([
        Vector((-0.01, 0.01, 0.10)),
        Vector((-0.06, -0.02, 0.21)),
    ], [0.014, 0.009], lados=4, mat=m_f2, tampar_base=False, tampar_topo=True)
    c.cristal_facetado(Vector((-0.06, -0.02, 0.19)), Vector((-0.25, -0.1, 1.0)), comp=0.06, r_base=0.028, lados=5, mat=m_luz)

    return c.finalizar('flor_luminosa', escala_xy=0.22, escala_z=0.36)


def criar_cacto_cristal():
    """Cacto mineral do deserto (~0.50 x 0.22 x 1.03 m): coluna canelada com dois braços e pontas cristalinas."""
    c = amb.ConstrutorMalha(['P_Malaquita', 'P_Cristal', 'P_Tronco'])
    m_cac, m_cr, m_base = 0, 1, 2

    # Base lenhosa curta e fuste principal octogonal/hexagonal
    c.tubo_curvo([
        Vector((0.0, 0.0, 0.0)),
        Vector((0.0, 0.0, 0.12)),
        Vector((0.01, 0.0, 0.52)),
        Vector((0.0, 0.0, 0.90)),
    ], [0.095, 0.115, 0.108, 0.072], lados=6, mat=m_cac, tampar_base=True, tampar_topo=True)

    # Braço esquerdo subindo em cotovelo
    c.tubo_curvo([
        Vector((-0.06, 0.0, 0.38)),
        Vector((-0.19, 0.01, 0.43)),
        Vector((-0.21, 0.01, 0.68)),
    ], [0.068, 0.064, 0.048], lados=5, mat=m_cac, tampar_base=False, tampar_topo=True)

    # Braço direito mais alto
    c.tubo_curvo([
        Vector((0.06, 0.0, 0.48)),
        Vector((0.18, -0.01, 0.54)),
        Vector((0.20, -0.01, 0.78)),
    ], [0.064, 0.058, 0.044], lados=5, mat=m_cac, tampar_base=False, tampar_topo=True)

    # Cristais luminosos brotando dos topos e costelas
    cristais = [
        (Vector((0.0, 0.0, 0.86)), Vector((0.0, 0.0, 1.0)), 0.17, 0.048),
        (Vector((-0.21, 0.01, 0.65)), Vector((-0.12, 0.0, 1.0)), 0.13, 0.036),
        (Vector((0.20, -0.01, 0.75)), Vector((0.12, 0.0, 1.0)), 0.14, 0.036),
        (Vector((0.0, -0.08, 0.62)), Vector((0.0, -0.65, 0.75)), 0.11, 0.028),
        (Vector((0.0, 0.08, 0.34)), Vector((0.0, 0.65, 0.75)), 0.10, 0.026),
    ]
    for pos, direcao, comp, rb in cristais:
        c.cristal_facetado(pos, direcao, comp=comp, r_base=rb, lados=5, mat=m_cr)

    return c.finalizar('cacto_cristal', escala_xy=0.48, escala_z=1.03)


def criar_vitoria_regia():
    """Vitória-régia aquática (~0.52 x 0.42 x 0.06 m): disco flutuante com borda elevada, chanfro e flor central."""
    c = amb.ConstrutorMalha(['P_Folha', 'P_FolhaClara', 'P_ChapeuCristal', 'P_Cristal'])
    m_f1, m_f2, m_pet, m_luz = 0, 1, 2, 3

    # Disco principal com chanfro em V e borda levantada (10 setores)
    setores = 10
    r_int = 0.04
    r_med = 0.21
    r_ext = 0.24
    # Construímos como prisma chanfrado sólido usando anéis
    for i in range(setores):
        # Pular 1 setor para o recorte característico da vitória-régia
        if i == 0:
            continue
        a0 = (i / setores) * 2 * PI
        a1 = ((i + 1) / setores) * 2 * PI
        am = (a0 + a1) * 0.5
        p_ini = Vector((math.cos(am) * 0.01, math.sin(am) * 0.01, 0.012))
        p_fim = Vector((math.cos(am) * r_ext, math.sin(am) * r_ext, 0.036))
        c.lamina_folha(p_ini, p_fim, larg_max=0.088, espessura=0.018, arco=-0.008, mat=m_f1 if i % 2 == 0 else m_f2)

    # Folha menor secundária ao lado
    for i in range(5):
        am = (i / 5.0) * 2 * PI + 0.4
        p_ini = Vector((-0.14, 0.08, 0.010))
        p_fim = p_ini + Vector((math.cos(am) * 0.11, math.sin(am) * 0.11, 0.018))
        c.lamina_folha(p_ini, p_fim, larg_max=0.055, espessura=0.014, arco=-0.004, mat=m_f2)

    # Flor de lótus/vitória-régia central com miolo brilhante
    c.cristal_facetado(Vector((0.02, 0.0, 0.005)), Vector((0.0, 0.0, 1.0)), comp=0.055, r_base=0.042, lados=6, mat=m_pet)
    c.cristal_facetado(Vector((0.02, 0.0, 0.015)), Vector((0.0, 0.0, 1.0)), comp=0.048, r_base=0.024, lados=5, mat=m_luz)

    return c.finalizar('vitoria_regia', escala_xy=0.52, escala_z=0.06)


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_arbusto(),
        criar_junco(),
        criar_flor_luminosa(),
        criar_cacto_cristal(),
        criar_vitoria_regia(),
    ]
    posicoes = [(-1.40, 0.0), (-0.70, 0.0), (0.0, 0.0), (0.70, 0.0), (1.40, 0.0)]
    for o, (px, py) in zip(modelos, posicoes):
        o.location = Vector((px, py, 0.0))

    vistas = [
        ('amb_plantas_0.png', (0.0, -5.0, 2.3), (0.0, 0.0, 0.35), 38.0, 1400, 900),
        ('amb_plantas_1.png', (3.8, -3.6, 2.3), (0.0, 0.0, 0.35), 38.0, 1400, 900),
        ('amb_plantas_perto.png', (0.35, -2.2, 1.05), (0.35, 0.0, 0.32), 36.0, 1400, 900),
    ]
    amb.renderizar_estudo(sc, modelos, 'amb_plantas', limite_tris=200, bioma_chao='pantano',
                          vistas_vitrine=vistas, espalhar_raio=(12.5, 9.0), n_espalhados=65,
                          escala_espalhados=(0.90, 1.18), dist_min=1.05)
    print("ESTUDO_AMB_PLANTAS OK")


if __name__ == '__main__':
    main()
