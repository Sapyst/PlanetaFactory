"""Variações de energia e armazenagem (2×2): painel solar, turbina eólica, acumulador e baú grande.
Corpo recuado 0,05 m da borda (cantos livres para pilares); terminais de energia nos cantos.
Uso: blender --background --python estruturas_extra.py [-- nome]
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, terminais_cantos
from maquinas import base_ht, pistao

EN, P = 'energia', 'logistica/armazenagem'
PI = math.pi


def painel_solar():
    m = Modelo('painel_solar', EN, 2, 2, descricao='painel solar: duas placas de células inclinadas para o sul sobre '
               'cavaletes, moldura de aço; gera energia com sol (menos com nuvem e chuva), sem combustível.')
    p = m.parte(); base_ht(p, 2, 2)
    inc = math.radians(24)
    for sx in (-1, 1):
        x = sx*0.43
        for y, h in ((-0.55, 0.30), (0.55, 0.30 + 1.10*math.tan(inc))):   # cavaletes (frente baixa, trás alta)
            p.cil((x, y, 0.10 + h/2), 0.04, h, 'P_Escuro', lados=6)
        a = (x, -0.80, 0.30 + 0.10 - 0.25*math.tan(inc) + 0.05)
        b = (x, 0.80, a[2] + 1.60*math.tan(inc))
        p.barra(a, b, 0.76, 0.04, 'P_Vidro')                                   # células
        for dx in (-0.39, 0.39):                                               # moldura lateral
            p.barra((x + dx, a[1] - 0.02, a[2]), (x + dx, b[1] + 0.02, b[2]), 0.03, 0.055, 'P_Aco')
        for k in range(1, 4):                                                  # filetes entre células (luz)
            f = k/4.0
            yy = a[1] + (b[1] - a[1])*f; zz = a[2] + (b[2] - a[2])*f
            p.barra((x - 0.37, yy, zz + 0.022), (x + 0.37, yy, zz + 0.022), 0.012, 0.006, 'P_Cristal', lado=(0, 1, 0))
    v = p.caixa(-0.20, 0.20, -0.30, 0.30, 0.10, 0.26, 'P_Escuro'); p.chanfrar(v, 0.02)   # inversor
    p.caixa(-0.14, 0.14, -0.312, -0.30, 0.15, 0.20, 'P_Cristal')
    terminais_cantos(m, p, 0.112)
    return m


def turbina_eolica():
    m = Modelo('turbina_eolica', EN, 2, 2, descricao='turbina eólica: torre octogonal afilada, nacele e hélice de 3 pás '
               'virada para o sul (gira com o vento); gera energia sem combustível.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.cil((0, 0, 0.22), 0.42, 0.24, 'P_Escuro', lados=8, rot=PI/8, r2=0.34); p.chanfrar(v, 0.02)
    p.cil((0, 0, 1.47), 0.20, 2.26, 'P_Aco', lados=8, rot=PI/8, r2=0.11)
    for z in (0.80, 1.60):
        p.cil((0, 0, z), 0.20 - (z - 0.34)*0.04 + 0.012, 0.03, 'P_Cristal', lados=8, rot=PI/8)
    v = p.caixa(-0.17, 0.17, -0.24, 0.45, 2.58, 2.86, 'P_Escuro'); p.chanfrar(v, 0.03)   # nacele
    p.caixa(-0.12, 0.12, 0.45, 0.462, 2.66, 2.78, 'P_Cristal')
    h = m.parte('helice', pai='corpo', pivo=(0, -0.36, 2.72))                  # hélice (gira em torno do eixo norte)
    h.cil((0, -0.34, 2.72), 0.11, 0.20, 'P_Aco', lados=8, eixo='Y')
    h.cil((0, -0.47, 2.72), 0.07, 0.07, 'P_Cristal', lados=8, eixo='Y', r2=0.02)
    for k in range(3):
        a = PI/2 + k*2*PI/3
        h.barra((math.cos(a)*0.09, -0.34, 2.72 + math.sin(a)*0.09), (math.cos(a)*0.92, -0.34, 2.72 + math.sin(a)*0.92),
                0.12, 0.025, 'P_Metal', lado=(-math.sin(a), 0, math.cos(a)))
    terminais_cantos(m, p, 0.112)
    return m


def acumulador():
    m = Modelo('acumulador', EN, 2, 2, descricao='acumulador: quatro células octogonais com faixa de carga e núcleo de '
               'cristal que pulsa no meio; guarda a sobra de energia da rede e devolve quando falta.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.caixa(-0.74, 0.74, -0.74, 0.74, 0.09, 0.24, 'P_Escuro'); p.chanfrar(v, 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx*0.40, sy*0.40
            v = p.cil((x, y, 0.24 + 0.40), 0.26, 0.80, 'P_Aco', lados=8, rot=PI/8); p.chanfrar(v, 0.02)
            for z in (0.52, 0.80):
                p.cil((x, y, z), 0.27, 0.05, 'P_Cristal', lados=8, rot=PI/8)
            p.cil((x, y, 1.08), 0.20, 0.08, 'P_Escuro', lados=8, rot=PI/8, r2=0.14)
            p.cil((x, y, 1.15), 0.06, 0.06, 'P_Cobre', lados=6)
            p.barra((x*0.84, y*0.84, 1.13), (x*0.30, y*0.30, 1.30), 0.04, 0.04, 'P_Cobre')  # cabo ao núcleo
    v = p.cil((0, 0.04, 1.30), 0.13, 0.10, 'P_Escuro', lados=8, rot=PI/8); p.chanfrar(v, 0.01)
    c = m.parte('cristal', pai='corpo', pivo=(0, 0.04, 1.50))                  # núcleo (pulsa)
    c.cil((0, 0.04, 1.52), 0.10, 0.34, 'P_Cristal', lados=6, r2=0.0)
    terminais_cantos(m, p, 0.112)
    return m


def bau_grande():
    m = Modelo('bau_grande', P, 2, 2, descricao='Baú grande 2×2 (4× o baú). Braços colocam e tiram por qualquer lado.')
    p = m.parte()
    v = p.caixa(-0.88, 0.88, -0.84, 0.84, 0.0, 0.78, 'P_Metal'); p.chanfrar(v, 0.04)
    v = p.caixa(-0.91, 0.91, -0.87, 0.87, 0.78, 0.94, 'P_Escuro'); p.chanfrar(v, 0.04)
    for x in (-0.55, 0.55):
        p.caixa(x - 0.06, x + 0.06, -0.855, 0.855, 0.06, 0.90, 'P_Faixa')
    for y in (-0.50, 0.50):
        p.caixa(-0.895, 0.895, y - 0.05, y + 0.05, 0.10, 0.70, 'P_Faixa')
    p.caixa(-0.10, 0.10, -0.885, -0.87, 0.58, 0.76, 'P_Cobre')
    return m


TODOS = [painel_solar, turbina_eolica, acumulador, bau_grande]

if __name__ == '__main__':
    so = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    rodar([f for f in TODOS if not so or f.__name__ in so], os.path.join(lib_pf.RAIZ, 'energia', '_relatorio_extra.json'))
