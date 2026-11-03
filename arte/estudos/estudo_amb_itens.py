"""
Estudo de ambiente — Grupo 8: Itens na esteira (PlanetaFactory).
Modelos (8):
  - minerio_ferro  (~0.22 x 0.22 x 0.17 m, nódulo pesado vermelho-ferrugem, P_Ferrugem + P_RochaEscura)
  - minerio_cobre  (~0.22 x 0.22 x 0.17 m, pepita de cobre alaranjado com base de malaquita, P_Cobre + P_Malaquita)
  - carvao         (~0.22 x 0.22 x 0.16 m, aglomerado de prismas negros clivados, P_Carvao)
  - pedra          (~0.22 x 0.22 x 0.16 m, bloco de cantaria claro + lascas cinzas, P_Pedra + P_Rocha)
  - areia          (~0.23 x 0.23 x 0.13 m, monte duplo dourado em ondulações, P_Areia)
  - silex          (~0.21 x 0.21 x 0.17 m, leque de 3 lâminas pontiagudas azul-aço, P_Silex)
  - cristal_bruto  (~0.21 x 0.21 x 0.24 m, drusa de 4 pontas de cristal turquesa, P_Cristal + P_ChapeuCristal)
  - biomassa       (~0.22 x 0.22 x 0.16 m, feixe orgânico folhoso com bulbos verdes brilhantes, P_Biomassa + P_Folha)
Limite rígido: <= 120 triângulos por modelo. Malha única (MESH), sem transparência, origem na base (z=0).
"""
import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amb_comum as amb

PI = math.pi


def criar_minerio_ferro():
    """Minério de ferro (~0.22 x 0.22 x 0.17 m): bloco denso de hematita vermelho-ferrugem com núcleo escuro."""
    c = amb.ConstrutorMalha(['P_Ferrugem', 'P_RochaEscura'])
    m_fe, m_ro = 0, 1

    c.rocha_organica(Vector((0.0, 0.0, 0.06)), (0.10, 0.095, 0.085), mat=m_fe, semente=801, gomos=6, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((-0.045, -0.03, 0.04)), (0.065, 0.060, 0.055), mat=m_ro, semente=802, gomos=5, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((0.04, 0.035, 0.05)), (0.065, 0.060, 0.065), mat=m_fe, semente=803, gomos=5, aneis=2, achatar_base=True)

    return c.finalizar('minerio_ferro', escala_xy=0.22, escala_z=0.17)


def criar_minerio_cobre():
    """Minério de cobre (~0.22 x 0.22 x 0.17 m): base verde de malaquita coroada por 3 pepitas metálicas alaranjadas."""
    c = amb.ConstrutorMalha(['P_Cobre', 'P_Malaquita'])
    m_cu, m_mal = 0, 1

    c.rocha_organica(Vector((0.0, 0.0, 0.04)), (0.10, 0.09, 0.055), mat=m_mal, semente=811, gomos=6, aneis=2, achatar_base=True)
    c.cristal_facetado(Vector((-0.02, 0.01, 0.02)), Vector((-0.15, 0.08, 1.0)), comp=0.15, r_base=0.062, lados=5, mat=m_cu)
    c.cristal_facetado(Vector((0.04, -0.02, 0.02)), Vector((0.28, -0.15, 0.92)), comp=0.12, r_base=0.052, lados=5, mat=m_cu)
    c.cristal_facetado(Vector((0.01, 0.05, 0.02)), Vector((0.08, 0.30, 0.90)), comp=0.11, r_base=0.045, lados=4, mat=m_cu)

    return c.finalizar('minerio_cobre', escala_xy=0.22, escala_z=0.17)


def criar_carvao():
    """Carvão mineral (~0.22 x 0.22 x 0.16 m): 3 blocos prismáticos negros com clivagem cúbica nítida."""
    c = amb.ConstrutorMalha(['P_Carvao'])
    m_cv = 0

    blocos = [
        (Vector((-0.02, -0.01, 0.0)), Vector((0.02, 0.01, 0.15)), [0.075, 0.062]),
        (Vector((0.04, -0.03, 0.0)), Vector((0.07, -0.04, 0.11)), [0.058, 0.048]),
        (Vector((-0.05, 0.04, 0.0)), Vector((-0.07, 0.06, 0.10)), [0.055, 0.044]),
    ]
    for p0, p1, raios in blocos:
        c.tubo_curvo([p0, p1], raios, lados=4, mat=m_cv, tampar_base=True, tampar_topo=True, torcao=0.2)

    return c.finalizar('carvao', escala_xy=0.22, escala_z=0.16)


def criar_pedra():
    """Pedra (~0.22 x 0.22 x 0.16 m): bloco claro chanfrado de calcário/granito com duas pedras menores."""
    c = amb.ConstrutorMalha(['P_Pedra', 'P_Rocha'])
    m_pe, m_ro = 0, 1

    c.rocha_organica(Vector((-0.01, 0.01, 0.065)), (0.095, 0.085, 0.090), mat=m_pe, semente=831, gomos=6, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((0.05, -0.04, 0.040)), (0.060, 0.055, 0.055), mat=m_ro, semente=832, gomos=5, aneis=2, achatar_base=True)
    c.rocha_organica(Vector((-0.05, -0.04, 0.035)), (0.055, 0.050, 0.048), mat=m_pe, semente=833, gomos=5, aneis=2, achatar_base=True)

    return c.finalizar('pedra', escala_xy=0.22, escala_z=0.16)


def criar_areia():
    """Areia (~0.23 x 0.23 x 0.13 m): monte cônico duplo dourado com crista bem marcada."""
    c = amb.ConstrutorMalha(['P_Areia'])
    m_ar = 0

    c.chapeu_cogumelo(Vector((-0.015, 0.0, 0.015)), r_base=0.10, altura=0.105, espessura_borda=0.015,
                      lados=6, mat_topo=m_ar, mat_baixo=m_ar, semente=841)
    c.chapeu_cogumelo(Vector((0.045, 0.025, 0.012)), r_base=0.068, altura=0.072, espessura_borda=0.012,
                      lados=5, mat_topo=m_ar, mat_baixo=m_ar, semente=842)

    return c.finalizar('areia', escala_xy=0.23, escala_z=0.13)


def criar_silex():
    """Sílex (~0.21 x 0.21 x 0.17 m): 3 lâminas cortantes azul-aço em leque sobre córtex escuro."""
    c = amb.ConstrutorMalha(['P_Silex', 'P_RochaEscura'])
    m_si, m_ro = 0, 1

    c.rocha_organica(Vector((0.0, 0.0, 0.025)), (0.085, 0.080, 0.035), mat=m_ro, semente=850, gomos=5, aneis=2, achatar_base=True)
    c.cristal_facetado(Vector((0.0, 0.0, 0.015)), Vector((0.05, -0.05, 1.0)), comp=0.16, r_base=0.058, lados=4, mat=m_si)
    c.cristal_facetado(Vector((-0.04, 0.02, 0.015)), Vector((-0.42, 0.20, 0.88)), comp=0.13, r_base=0.048, lados=4, mat=m_si)
    c.cristal_facetado(Vector((0.04, -0.02, 0.015)), Vector((0.42, -0.20, 0.88)), comp=0.13, r_base=0.048, lados=4, mat=m_si)

    return c.finalizar('silex', escala_xy=0.21, escala_z=0.17)


def criar_cristal_bruto():
    """Cristal bruto (~0.21 x 0.21 x 0.24 m): drusa de 4 prismas luminosos ciano-turquesa sobre base violeta."""
    c = amb.ConstrutorMalha(['P_Cristal', 'P_ChapeuCristal'])
    m_cr, m_base = 0, 1

    c.rocha_organica(Vector((0.0, 0.0, 0.025)), (0.085, 0.080, 0.040), mat=m_base, semente=860, gomos=5, aneis=2, achatar_base=True)
    c.cristal_facetado(Vector((0.0, 0.0, 0.02)), Vector((0.02, 0.0, 1.0)), comp=0.22, r_base=0.048, lados=5, mat=m_cr)
    c.cristal_facetado(Vector((-0.035, 0.02, 0.02)), Vector((-0.35, 0.20, 0.90)), comp=0.17, r_base=0.038, lados=5, mat=m_cr)
    c.cristal_facetado(Vector((0.035, -0.02, 0.02)), Vector((0.35, -0.20, 0.90)), comp=0.16, r_base=0.036, lados=5, mat=m_cr)
    c.cristal_facetado(Vector((0.01, 0.04, 0.015)), Vector((0.12, 0.42, 0.86)), comp=0.14, r_base=0.032, lados=4, mat=m_cr)

    return c.finalizar('cristal_bruto', escala_xy=0.21, escala_z=0.24)


def criar_biomassa():
    """Biomassa (~0.22 x 0.22 x 0.16 m): feixe orgânico de folhagem densa e bulbos bioluminescentes verde-limão."""
    c = amb.ConstrutorMalha(['P_Biomassa', 'P_Folha', 'P_Tronco'])
    m_bio, m_fol, m_tr = 0, 1, 2

    # Base de caules cortados + folhagem + 2 bulbos energéticos brilhantes
    c.tubo_curvo([Vector((-0.08, -0.02, 0.02)), Vector((0.08, 0.02, 0.04))], [0.032, 0.028], lados=5, mat=m_tr)
    c.tufo_folha(Vector((-0.02, 0.02, 0.07)), (0.085, 0.075, 0.060), mat=m_fol, semente=871, gomos=5, aneis=2)
    c.tufo_folha(Vector((0.02, -0.01, 0.10)), (0.075, 0.070, 0.055), mat=m_bio, semente=872, gomos=5, aneis=2)

    return c.finalizar('biomassa', escala_xy=0.22, escala_z=0.16)


def _criar_trilho_esteira(nome_obj, p0, p1, larg=0.52):
    """Cria uma faixa escura simples representando a esteira sob os itens para leitura visual."""
    bm = bmesh.new()
    v0 = bm.verts.new((p0[0], p0[1] - larg * 0.5, p0[2]))
    v1 = bm.verts.new((p1[0], p1[1] - larg * 0.5, p1[2]))
    v2 = bm.verts.new((p1[0], p1[1] + larg * 0.5, p1[2]))
    v3 = bm.verts.new((p0[0], p0[1] + larg * 0.5, p0[2]))
    v4 = bm.verts.new((p0[0], p0[1] - larg * 0.5, p0[2] + 0.025))
    v5 = bm.verts.new((p1[0], p1[1] - larg * 0.5, p1[2] + 0.025))
    v6 = bm.verts.new((p1[0], p1[1] + larg * 0.5, p1[2] + 0.025))
    v7 = bm.verts.new((p0[0], p0[1] + larg * 0.5, p0[2] + 0.025))
    for f in ((v4, v5, v6, v7), (v0, v1, v5, v4), (v1, v2, v6, v5), (v2, v3, v7, v6), (v3, v0, v4, v7)):
        bm.faces.new(f)
    me = bpy.data.meshes.new(nome_obj)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(amb.base3d.M['P_RochaEscura'])
    o = bpy.data.objects.new(nome_obj, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def main():
    sc = amb.limpar_cena()
    modelos = [
        criar_minerio_ferro(),
        criar_minerio_cobre(),
        criar_carvao(),
        criar_pedra(),
        criar_areia(),
        criar_silex(),
        criar_cristal_bruto(),
        criar_biomassa(),
    ]
    # Duas fileiras de 4 itens sobre trilhos de esteira na vitrine
    posicoes = [
        (-0.54, -0.25), (-0.18, -0.25), (0.18, -0.25), (0.54, -0.25),
        (-0.54, 0.25), (-0.18, 0.25), (0.18, 0.25), (0.54, 0.25),
    ]
    _criar_trilho_esteira('EFEITO_esteira_vit_1', (-0.85, -0.25, 0.0), (0.85, -0.25, 0.0), larg=0.34)
    _criar_trilho_esteira('EFEITO_esteira_vit_2', (-0.85, 0.25, 0.0), (0.85, 0.25, 0.0), larg=0.34)
    for o, (px, py) in zip(modelos, posicoes):
        o.location = Vector((px, py, 0.025))

    # Na cena de 30m (centrada em x=120, y=0), também adicionamos 8 linhas de esteira cheias de itens
    # para provar que cada minério/item é reconhecível na esteira a 30 m de altura!
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
    if (argv[0] if argv else 'foto') == 'foto':
        cx_c, cy_c = 120.0, 0.0
        for idx_m, molde in enumerate(modelos):
            y_linha = cy_c + (idx_m - 3.5) * 1.35
            _criar_trilho_esteira(f'EFEITO_esteira_30m_{idx_m}', (cx_c - 7.5, y_linha, 0.14), (cx_c + 7.5, y_linha, 0.14), larg=0.44)
            for k in range(-14, 15):
                px = cx_c + k * 0.48
                pz = 0.165
                inst = bpy.data.objects.new(f'EFEITO_item_est_{idx_m}_{k}', molde.data)
                sc.collection.objects.link(inst)
                inst.location = Vector((px, y_linha, pz))

    vistas = [
        ('amb_itens_0.png', (0.0, -2.05, 1.32), (0.0, 0.0, 0.08), 34.0, 1500, 1000),
        ('amb_itens_1.png', (1.45, -1.35, 1.05), (0.0, 0.0, 0.08), 35.0, 1500, 1000),
        ('amb_itens_perto.png', (0.25, -0.92, 0.52), (0.05, -0.05, 0.09), 35.0, 1500, 1000),
    ]
    amb.renderizar_estudo(sc, modelos, 'amb_itens', limite_tris=120, bioma_chao='campina',
                          vistas_vitrine=vistas, espalhar_raio=(11.5, 8.5), n_espalhados=80,
                          escala_espalhados=(0.95, 1.08), dist_min=0.55)
    print("ESTUDO_AMB_ITENS OK")


if __name__ == '__main__':
    main()
