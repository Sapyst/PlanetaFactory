"""Logística de transporte: trilhos, estação, sinal, locomotiva e vagões.
Trilho: bitola 0,50 m, topo do trilho em z = 0,14 (onde a roda apoia). Curva 3×3 com raio 2,5 m.
Veículos: origem no centro, rodas em z = 0 (o jogo soma 0,14 ao pôr no trilho). Partes: corpo + truques (giram nas curvas).
Uso: blender --background --python transporte.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, trilho_trecho, reto, curva_canto, BITOLA
from mathutils import Vector

T, VE = 'transporte/trilhos', 'transporte/veiculos'
PI = math.pi

def trilho_reto():
    m = Modelo('trilho_reto', T, descricao='Trilho reto norte–sul.'); m.ocupa_canto = True
    trilho_trecho(m.parte(), reto((0, -0.5, 0), (0, 0.5, 0)))
    m.porta('TRILHO', 'ENT', 'S', perfil='trilho'); m.porta('TRILHO', 'SAI', 'N', perfil='trilho'); return m

def trilho_curva():
    m = Modelo('trilho_curva', T, 3, 3, descricao='Curva de trilho 3×3 (raio 2,5 m): entra pelo sul (tile da esquerda), sai a leste (tile de cima).')
    m.ocupa_canto = True
    trilho_trecho(m.parte(), curva_canto((1.5, -1.5, 0), 2.5, PI, PI/2, seg=24))
    m.porta('TRILHO', 'ENT', 'S', 0, perfil='trilho'); m.porta('TRILHO', 'SAI', 'L', 0, perfil='trilho'); return m

def trilho_fim():
    m = Modelo('trilho_fim', T, descricao='Fim de linha com para-choque (norte).'); m.ocupa_canto = True; p = m.parte()
    trilho_trecho(p, reto((0, -0.5, 0), (0, 0.30, 0)))
    p.caixa(-0.42, 0.42, 0.30, 0.42, 0.0, 0.05, 'P_RochaEscura')
    p.caixa(-0.36, 0.36, 0.30, 0.40, 0.05, 0.40, 'P_Escuro'); p.caixa(-0.36, 0.36, 0.28, 0.30, 0.22, 0.34, 'P_Faixa')
    m.porta('TRILHO', 'ENT', 'S', perfil='trilho'); return m

def estacao():
    m = Modelo('estacao', T, 2, 3, descricao='Estação de carga 2×3: a linha passa a oeste (encostada). Braços tiram/põem nos vagões; '
                                              'esteiras entram e saem a leste.')
    p = m.parte()
    v = p.caixa(-0.95, 0.95, -1.45, 1.45, 0, 0.30, 'P_Concreto'); p.chanfrar(v, 0.03)
    p.caixa(-0.97, -0.90, -1.45, 1.45, 0.24, 0.30, 'P_Faixa')                         # borda da plataforma (lado do trem)
    for y in (-1.25, 1.25):
        for x in (-0.75, 0.75): p.caixa_c(x, y, 0.30, 0.10, 0.10, 1.30, 'P_Metal')
    v = p.caixa(-0.95, 0.95, -1.45, 1.45, 1.60, 1.70, 'P_Escuro'); p.chanfrar(v, 0.03)
    p.caixa(-0.70, 0.30, -0.40, 0.40, 1.70, 1.95, 'P_Metal')
    p.cil((-0.20, 0, 2.05), 0.08, 0.20, 'P_Cristal', lados=6)
    v = p.caixa(0.15, 0.85, -1.30, 1.30, 0.30, 1.05, 'P_Metal'); p.chanfrar(v, 0.03)   # armazém
    p.caixa(0.86, 0.88, -0.25, 0.25, 0.40, 0.90, 'P_Faixa')
    m.porta('ITEM', 'ENT', 'L', 2); m.porta('ITEM', 'SAI', 'L', 0)
    return m

def sinal_trem():
    m = Modelo('sinal_trem', T, descricao='Sinal de bloco: fica no tile ao lado da linha. Divide a linha em blocos (1 trem por bloco).')
    p = m.parte()
    p.caixa(-0.12, 0.12, -0.12, 0.12, 0, 0.08, 'P_Concreto')
    p.cil((0, 0, 0.75), 0.04, 1.4, 'P_Metal', lados=6)
    p.caixa_c(0, 0, 1.15, 0.16, 0.12, 0.40, 'P_Escuro')
    p.cil((0, -0.07, 1.45), 0.045, 0.02, 'P_Fogo', eixo='Y', lados=8)
    p.cil((0, -0.07, 1.27), 0.045, 0.02, 'P_Cristal', eixo='Y', lados=8)
    return m

# ---------------------------------------------------------------- veículos
def _truques(m, pai, ys):
    for i, y in enumerate(ys):
        t = m.parte(f'truque{i}', pai=pai, pivo=(0, y, 0.12))
        t.caixa_c(0, y, 0.06, 0.62, 0.50, 0.10, 'P_Escuro')
        for dy in (-0.15, 0.15):
            for s in (-1, 1): t.cil((s*BITOLA/2, y + dy, 0.075), 0.075, 0.05, 'P_Metal', eixo='X', lados=8)

def locomotiva():
    m = Modelo('locomotiva', VE, tipo='veiculo', orcamento=1500, descricao='Locomotiva (3 m). Partes: corpo + 2 truques.')
    c = m.parte('corpo', pivo=(0, 0, 0.12))
    v = c.caixa(-0.36, 0.36, -1.45, 1.45, 0.16, 0.30, 'P_Escuro'); c.chanfrar(v, 0.02)
    v = c.caixa(-0.33, 0.33, -1.20, 0.55, 0.30, 0.85, 'P_Faixa'); c.chanfrar(v, 0.04)
    v = c.caixa(-0.35, 0.35, 0.55, 1.35, 0.30, 1.05, 'P_Metal'); c.chanfrar(v, 0.04)   # cabine (frente = +Y)
    c.caixa(-0.30, 0.30, 1.35, 1.37, 0.65, 0.92, 'P_Vidro')
    c.caixa(-0.36, 0.36, 0.55, 1.35, 1.05, 1.10, 'P_Escuro')
    c.cil((0, -0.70, 1.00), 0.10, 0.30, 'P_Escuro', lados=8)
    c.cil((0, -0.20, 0.92), 0.12, 0.14, 'P_Cristal', lados=6)
    c.caixa(-0.30, 0.30, 1.40, 1.48, 0.18, 0.28, 'P_Escuro')
    _truques(m, 'corpo', (-0.85, 0.85)); return m

def vagao_carga():
    m = Modelo('vagao_carga', VE, tipo='veiculo', orcamento=1500, descricao='Vagão de carga (3 m). Itens carregados por braços na estação.')
    c = m.parte('corpo', pivo=(0, 0, 0.12))
    c.caixa(-0.36, 0.36, -1.45, 1.45, 0.16, 0.28, 'P_Escuro')
    v = c.caixa(-0.36, 0.36, -1.35, 1.35, 0.28, 0.80, 'P_Cobre'); c.chanfrar(v, 0.03)
    for y in (-0.9, -0.3, 0.3, 0.9): c.caixa(-0.37, 0.37, y - 0.03, y + 0.03, 0.28, 0.80, 'P_Escuro')
    c.caixa(-0.30, 0.30, -1.28, 1.28, 0.80, 0.84, 'P_Escuro')
    _truques(m, 'corpo', (-0.85, 0.85)); return m

def vagao_tanque():
    m = Modelo('vagao_tanque', VE, tipo='veiculo', orcamento=1500, descricao='Vagão-tanque (3 m) para fluidos.')
    c = m.parte('corpo', pivo=(0, 0, 0.12))
    c.caixa(-0.36, 0.36, -1.45, 1.45, 0.16, 0.28, 'P_Escuro')
    c.cil((0, 0, 0.62), 0.34, 2.60, 'P_Metal', eixo='Y', lados=10)
    for y in (-1.31, 1.31): c.cil((0, y, 0.62), 0.30, 0.04, 'P_Escuro', eixo='Y', lados=10)
    c.cil((0, 0, 0.62), 0.355, 0.12, 'P_Faixa', eixo='Y', lados=10)
    c.cil((0, 0, 1.00), 0.10, 0.10, 'P_Escuro', lados=8)
    _truques(m, 'corpo', (-0.85, 0.85)); return m

TODOS = [trilho_reto, trilho_curva, trilho_fim, estacao, sinal_trem, locomotiva, vagao_carga, vagao_tanque]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'transporte', '_relatorio_transporte.json'))
