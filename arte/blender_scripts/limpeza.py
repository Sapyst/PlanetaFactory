"""Estruturas de limpeza do planeta (2×2, high-tech como as máquinas): coletor de lixo, filtro de água e viveiro.
Corpo recuado 0,05 m da borda (cantos livres para pilares); terminais de energia nos cantos.
Uso: blender --background --python limpeza.py [-- nome]
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, terminais_cantos
import maquinas
from maquinas import base_ht, pistao, cano_porta

M = 'maquinas'
PI = math.pi


def coletor_lixo():
    m = Modelo('coletor_lixo', M, 2, 2, descricao='coletor de lixo: silo octogonal com janela de lodo, dois bocais de '
               'sucção que descem até o chão e turbina de exaustão que gira no topo; aspira sujeira e óleo em volta.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.caixa(-0.72, 0.72, -0.62, 0.62, 0.09, 0.36, 'P_Escuro'); p.chanfrar(v, 0.04)
    p.caixa(-0.60, 0.60, -0.632, -0.62, 0.20, 0.23, 'P_Cristal')
    v = p.cil((0, 0, 0.36 + 0.42), 0.50, 0.84, 'P_Aco', lados=8, rot=PI/8, r2=0.44); p.chanfrar(v, 0.02)
    p.cil((0, 0, 0.66), 0.495, 0.20, 'P_Lodo', lados=8, rot=PI/8, r2=0.48)           # janela: o lodo aspirado
    for z in (0.55, 0.77):
        p.cil((0, 0, z), 0.505 - (z - 0.36)*0.07, 0.025, 'P_Cristal', lados=8, rot=PI/8)
    v = p.cil((0, 0, 1.26), 0.40, 0.12, 'P_Escuro', lados=8, rot=PI/8, r2=0.26); p.chanfrar(v, 0.02)
    for sx in (-1, 1):                                                          # bocais de sucção
        p.barra((sx*0.36, 0.20, 0.95), (sx*0.70, 0.55, 0.42), 0.10, 0.10, 'P_Metal')
        p.barra((sx*0.70, 0.55, 0.46), (sx*0.70, 0.55, 0.20), 0.10, 0.10, 'P_Metal')
        p.cil((sx*0.70, 0.55, 0.15), 0.17, 0.10, 'P_Escuro', lados=8, rot=PI/8, r2=0.11)
        p.cil((sx*0.70, 0.55, 0.112), 0.18, 0.02, 'P_Cristal', lados=8, rot=PI/8)
    r = m.parte('rotor', pai='corpo', pivo=(0, 0, 1.32))                        # turbina de exaustão (gira)
    r.cil((0, 0, 1.40), 0.09, 0.16, 'P_Aco', lados=8)
    for k in range(5):
        a = k*2*PI/5
        r.caixa_c(math.cos(a)*0.20, math.sin(a)*0.20, 1.36, 0.24, 0.07, 0.02, 'P_Metal', rot=a + 0.5)
    r.cil((0, 0, 1.50), 0.05, 0.04, 'P_Cristal', lados=6)
    pistao(m, p, 0, -0.55, -0.745, 0.10, h=0.22); pistao(m, p, 1, 0.55, -0.745, 0.10, h=0.22)
    terminais_cantos(m, p, 0.112)
    return m


def filtro_agua():
    m = Modelo('filtro_agua', M, 2, 2, descricao='filtro de água: três colunas de vidro com água limpa, coletor por cima e '
               'bomba de impulsor que gira; tomada d\'água pelo ralo da borda sul.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.caixa(-0.72, 0.72, -0.72, 0.72, 0.10, 0.30, 'P_Escuro'); p.chanfrar(v, 0.04)
    cols = [(-0.40, 0.30), (0.40, 0.30), (0.0, -0.32)]
    for x, y in cols:
        p.cil((x, y, 0.36), 0.25, 0.12, 'P_Aco', lados=8, rot=PI/8)
        p.cil((x, y, 0.42 + 0.33), 0.21, 0.66, 'P_Vidro', lados=8, rot=PI/8)
        p.cil((x, y, 0.43 + 0.27), 0.18, 0.54, 'P_Agua', lados=8, rot=PI/8)         # água filtrada lá dentro
        for z in (0.75,):
            p.cil((x, y, z), 0.225, 0.025, 'P_Cristal', lados=8, rot=PI/8)
        v = p.cil((x, y, 1.14), 0.24, 0.10, 'P_Escuro', lados=8, rot=PI/8, r2=0.18); p.chanfrar(v, 0.015)
    for k, (a, b) in enumerate(((cols[0], cols[1]), (cols[1], cols[2]), (cols[2], cols[0]))):    # coletor por cima
        z = 1.24 + 0.006*k
        p.barra((a[0], a[1], z), (b[0], b[1], z), 0.08, 0.08, 'P_Metal')
    v = p.cil((0, 0.0, 1.30), 0.16, 0.16, 'P_Aco', lados=8, rot=PI/8); p.chanfrar(v, 0.01)
    r = m.parte('rotor', pai='corpo', pivo=(0, 0, 1.38))                        # impulsor (gira)
    r.cil((0, 0, 1.43), 0.06, 0.10, 'P_Escuro', lados=6)
    for k in range(3):
        a = k*2*PI/3
        r.caixa_c(math.cos(a)*0.15, math.sin(a)*0.15, 1.40, 0.20, 0.06, 0.02, 'P_Cristal', rot=a + 0.6)
    v = p.caixa(-0.30, 0.30, -0.92, -0.74, 0.105, 0.24, 'P_Escuro'); p.chanfrar(v, 0.02)   # ralo da tomada d'água
    for k in range(4):
        x = -0.21 + k*0.14
        p.caixa(x - 0.025, x + 0.025, -0.93, -0.92, 0.13, 0.21, 'P_Metal')
    p.caixa(-0.26, 0.26, -0.88, -0.78, 0.24, 0.255, 'P_Cristal')
    p.barra((0, -0.80, 0.28), (0, -0.55, 0.42), 0.10, 0.10, 'P_Metal')
    pistao(m, p, 0, -0.62, -0.55, 0.30, h=0.18); pistao(m, p, 1, 0.62, -0.55, 0.30, h=0.18)
    terminais_cantos(m, p, 0.112)
    return m


def viveiro():
    m = Modelo('viveiro', M, 2, 2, descricao='viveiro: estufa aberta (telhado de vidro) com canteiros de mudas, aspersor que gira no '
               'topo; seiva entra pelo cano a oeste e vira muda plantada em volta.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.caixa(-0.74, 0.74, -0.74, 0.74, 0.10, 0.30, 'P_Escuro'); p.chanfrar(v, 0.04)
    for sx in (-1, 1):                                                          # canteiros com terra e mudas
        p.caixa(sx*0.40 - 0.28, sx*0.40 + 0.28, -0.60, 0.60, 0.30, 0.40, 'P_Concreto')
        p.caixa(sx*0.40 - 0.24, sx*0.40 + 0.24, -0.56, 0.56, 0.40, 0.42, 'P_Lodo')
        for k in range(4):
            y = -0.42 + k*0.28
            p.cil((sx*0.40, y, 0.48), 0.05, 0.12, 'P_Tronco', lados=5)
            p.cil((sx*0.40, y, 0.62), 0.13, 0.20, 'P_Folha', lados=6, r2=0.0, rot=k)
    for sx in (-1, 1):                                                          # telhado de vidro (laterais abertas)
        p.barra((sx*0.70, 0, 0.97), (0.0, 0, 1.37), 1.34, 0.03, 'P_Vidro', lado=(0, 1, 0))
        p.barra((sx*0.72, -0.70, 0.965), (sx*0.72, 0.70, 0.965), 0.04, 0.04, 'P_Aco')
    for y in (-0.68, 0.68):                                                # arcos da estufa
        for a, b in (((-0.72, 0.29), (-0.72, 0.96)), ((0.72, 0.29), (0.72, 0.96)), ((-0.72, 0.96), (0.0, 1.40)), ((0.72, 0.96), (0.0, 1.40))):
            w = 0.05 if a[0] == b[0] else (0.044 if a[0] < 0 else 0.038)                            # inclinado mais fino: faces não coincidem na junta
            p.barra((a[0], y, a[1]), (b[0], y, b[1]), w, w, 'P_Aco', lado=(0, 1, 0))
    p.barra((0, -0.70, 1.42), (0, 0.70, 1.42), 0.06, 0.06, 'P_Aco')
    p.cil((0, 0, 1.53), 0.06, 0.18, 'P_Metal', lados=6)
    an = m.parte('antena', pai='corpo', pivo=(0, 0, 1.62))                     # aspersor (gira)
    an.cil((0, 0, 1.66), 0.07, 0.08, 'P_Aco', lados=8)
    for k in range(2):
        a = k*PI
        an.barra((math.cos(a)*0.06, math.sin(a)*0.06, 1.68), (math.cos(a)*0.34, math.sin(a)*0.34, 1.70), 0.04, 0.04, 'P_Metal')
        an.cil((math.cos(a)*0.36, math.sin(a)*0.36, 1.70), 0.045, 0.06, 'P_Seiva', lados=6)
    cano_porta(p, m, 'O', 0, 'ENT', 0.80)
    pistao(m, p, 0, 0.0, -0.45, 0.30, h=0.16, r=0.05); pistao(m, p, 1, 0.0, 0.45, 0.30, h=0.16, r=0.05)
    terminais_cantos(m, p, 0.112)
    return m


TODOS = [coletor_lixo, filtro_agua, viveiro]

if __name__ == '__main__':
    so = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    rodar([f for f in TODOS if not so or f.__name__ in so], os.path.join(lib_pf.RAIZ, 'maquinas', '_relatorio_limpeza.json'))
