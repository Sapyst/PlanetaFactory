"""PROPOSTA de estilo high-tech da IA (não entra no jogo): fornalha, montadora, esteira e gerador redesenhados.
Mesmas áreas, portas e alturas das peças atuais — só muda a forma. Linguagem: blindagem grafite chanfrada, veios
de luz ciano nas emendas, octógonos/hexágonos, peças suspensas por campo; nada humano (sem chaminé, porta, janela).
Uso: blender -b --factory-startup --python proposta_hitech.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, reto, LONA, TRILHO, FRISO
from maquinas import RECUO

PR = 'proposta'
PI = math.pi


def boca(p, m, lado, k, io, larg=0.44):
    """Boca de item high-tech: bloco baixo chanfrado na borda, fenda de luz (laranja = entra, ciano = sai)."""
    hw, hd = m.w/2, m.d/2
    luz = 'P_Cristal' if io == 'SAI' else 'P_Fogo'
    if lado in 'SN':
        x = -hw + 0.5 + k if lado == 'S' else hw - 0.5 - k
        y0 = -hd if lado == 'S' else hd - 0.30; y1 = y0 + 0.30
        v = p.caixa(x - larg/2 - 0.05, x + larg/2 + 0.05, y0, y1, 0.0, 0.40, 'P_Escuro'); p.chanfrar(v, 0.04)
        yb = -hd if lado == 'S' else hd - 0.015
        p.caixa(x - larg/2, x + larg/2, yb, yb + 0.015, 0.17, 0.30, luz)
        p.caixa(x - larg/2, x + larg/2, y0 + 0.08, y1 - 0.08, 0.40, 0.415, luz)
    else:
        y = hd - 0.5 - k if lado == 'L' else -hd + 0.5 + k
        x0 = hw - 0.30 if lado == 'L' else -hw; x1 = x0 + 0.30
        v = p.caixa(x0, x1, y - larg/2 - 0.05, y + larg/2 + 0.05, 0.0, 0.40, 'P_Escuro'); p.chanfrar(v, 0.04)
        xb = hw - 0.015 if lado == 'L' else -hw
        p.caixa(xb, xb + 0.015, y - larg/2, y + larg/2, 0.17, 0.30, luz)
        p.caixa(x0 + 0.08, x1 - 0.08, y - larg/2, y + larg/2, 0.40, 0.415, luz)
    m.porta('ITEM', io, lado, k)


def base_ht(p, w, d, h=0.10):
    """Placa grafite chanfrada com um veio de luz rente à borda."""
    v = p.caixa(-w/2 + RECUO, w/2 - RECUO, -d/2 + RECUO, d/2 - RECUO, 0, h, 'P_Escuro'); p.chanfrar(v, 0.05)
    e = 0.10
    for (x0, x1, y0, y1) in ((-w/2 + e, w/2 - e, -d/2 + e, -d/2 + e + 0.03), (-w/2 + e, w/2 - e, d/2 - e - 0.03, d/2 - e),
                             (-w/2 + e, -w/2 + e + 0.03, -d/2 + e, d/2 - e), (w/2 - e - 0.03, w/2 - e, -d/2 + e, d/2 - e)):
        p.caixa(x0, x1, y0, y1, h, h + 0.012, 'P_Cristal')


def fornalha_ht():
    m = Modelo('fornalha_ht', PR, 2, 2, descricao='PROPOSTA — fornalha de indução: cadinho octogonal, núcleo incandescente '
               'visto por frestas, bobinas de cobre e aletas de calor. Entra pelo sul, sai pelo norte.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.cil((0, 0.05, 0.42), 0.78, 0.64, 'P_Aco', lados=8, rot=PI/8, r2=0.70); p.chanfrar(v, 0.04)
    for z in (0.30, 0.50):                                     # frestas do núcleo incandescente
        p.cil((0, 0.05, z), 0.80, 0.035, 'P_Fogo', lados=8, rot=PI/8)
    for z in (0.66, 0.76, 0.86):                               # bobinas de indução
        p.cil((0, 0.05, z), 0.60, 0.05, 'P_Cobre', lados=12)
    v = p.cil((0, 0.05, 1.02), 0.52, 0.26, 'P_Escuro', lados=8, rot=PI/8, r2=0.36); p.chanfrar(v, 0.03)
    p.cil((0, 0.05, 1.16), 0.30, 0.05, 'P_Fogo', lados=8, rot=PI/8)
    for k in range(8):                                         # nervuras de dissipação rentes ao cadinho
        a = PI/8 + k*PI/4
        p.caixa_c(math.cos(a)*0.80, 0.05 + math.sin(a)*0.80, 0.42, 0.06, 0.16, 0.58, 'P_Escuro', rot=a)
    boca(p, m, 'S', 1, 'ENT'); boca(p, m, 'N', 0, 'SAI')
    return m


def montadora_ht():
    m = Modelo('montadora_ht', PR, 3, 3, descricao='PROPOSTA — montadora: câmara blindada octogonal, anel manipulador '
               'suspenso que gira e prisma de montagem de cristal. Entra pelo sul, sai pelo norte (meio).')
    p = m.parte(); base_ht(p, 3, 3)
    v = p.cil((0, 0, 0.42), 1.28, 0.62, 'P_Escuro', lados=8, rot=PI/8, r2=1.18); p.chanfrar(v, 0.05)
    p.cil((0, 0, 0.76), 1.19, 0.05, 'P_Cristal', lados=8, rot=PI/8)
    v = p.cil((0, 0, 0.96), 1.05, 0.36, 'P_Aco', lados=8, rot=PI/8, r2=0.86); p.chanfrar(v, 0.04)
    for k in range(4):                                         # pilares que sustentam o campo
        a = k*PI/2 + PI/4
        x, y = math.cos(a)*0.95, math.sin(a)*0.95
        p.cil((x, y, 1.45), 0.08, 0.62, 'P_Metal', lados=6)
        p.cil((x, y, 1.80), 0.06, 0.06, 'P_Cristal', lados=6)
    p.cil((0, 0, 1.20), 0.40, 0.10, 'P_Cristal', lados=8, rot=PI/8)
    an = m.parte('antena', pai='corpo', pivo=(0, 0, 1.62))     # anel manipulador (gira)
    for k in range(8):
        a = k*PI/4
        an.caixa_c(math.cos(a)*0.72, math.sin(a)*0.72, 1.62, 0.30, 0.10, 0.08, 'P_Aco', rot=a + PI/2)
    for k in range(3):
        a = k*2*PI/3
        an.barra((math.cos(a)*0.70, math.sin(a)*0.70, 1.58), (math.cos(a)*0.30, math.sin(a)*0.30, 1.38), 0.06, 0.06, 'P_Metal')
        an.cil((math.cos(a)*0.28, math.sin(a)*0.28, 1.34), 0.05, 0.06, 'P_Cristal', lados=6)
    cr = m.parte('cristal', pai='corpo', pivo=(0, 0, 1.40))   # prisma de montagem (pulsa)
    cr.cil((0, 0, 1.52), 0.16, 0.30, 'P_Cristal', lados=6, r2=0.0)
    cr.cil((0, 0, 1.30), 0.16, 0.14, 'P_Cristal', lados=6, r2=0.10)
    boca(p, m, 'S', 1, 'ENT'); boca(p, m, 'N', 1, 'SAI')
    return m


def gerador_ht():
    m = Modelo('gerador_ht', PR, 2, 2, descricao='PROPOSTA — gerador: câmara de reação vertical com anéis de contenção '
               'e núcleo luminoso; combustível entra pelo sul. Energia vai por postes.')
    p = m.parte(); base_ht(p, 2, 2)
    v = p.cil((0, 0.08, 0.30), 0.72, 0.40, 'P_Escuro', lados=8, rot=PI/8, r2=0.64); p.chanfrar(v, 0.04)
    p.cil((0, 0.08, 1.00), 0.30, 1.10, 'P_Cristal', lados=8, rot=PI/8)         # núcleo
    for z in (0.62, 0.95, 1.28):                                               # anéis de contenção
        v = p.cil((0, 0.08, z), 0.48, 0.10, 'P_Aco', lados=8, rot=PI/8); p.chanfrar(v, 0.02)
    for k in range(3):
        a = k*2*PI/3 + PI/6
        x, y = math.cos(a)*0.55, 0.08 + math.sin(a)*0.55
        p.cil((x, y, 0.95), 0.07, 1.00, 'P_Metal', lados=6)
        p.cil((x, y, 1.48), 0.09, 0.06, 'P_Cobre', lados=6)
    v = p.cil((0, 0.08, 1.62), 0.42, 0.14, 'P_Escuro', lados=8, rot=PI/8, r2=0.30); p.chanfrar(v, 0.02)
    an = m.parte('antena', pai='corpo', pivo=(0, 0.08, 1.80))               # anel de campo (gira)
    for k in range(6):
        a = k*PI/3
        an.caixa_c(math.cos(a)*0.36, 0.08 + math.sin(a)*0.36, 1.80, 0.18, 0.06, 0.04, 'P_Cristal', rot=a + PI/2)
    boca(p, m, 'S', 1, 'ENT')
    return m


def esteira_ht():
    m = Modelo('esteira_ht', PR, descricao='PROPOSTA — esteira de levitação: mesma lona e perfil de junção, trilhos '
               'grafite com veio de luz no lugar da faixa zebrada e berço magnético brilhando por baixo.')
    p = m.parte()
    cam = reto((0, -0.5, 0), (0, 0.5, 0))
    p.varrer(cam, LONA, 'P_Esteira', uv=True)
    for s in (-1, 1):
        p.varrer(cam, (s*TRILHO[0], s*TRILHO[1], TRILHO[2], TRILHO[3]), 'P_Escuro')
        p.varrer(cam, (s*TRILHO[0], s*TRILHO[1], FRISO[2], FRISO[3]), 'P_Cristal')
    p.varrer([(cam[0][0] * 0 + (cam[0][0] + cam[1][0]) / 2 - cam[0][1]*0.08, cam[0][1]),
              ((cam[0][0] + cam[1][0]) / 2 + cam[0][1]*0.08, cam[0][1])], (-0.36, 0.36, 0.0, 0.07), 'P_Aco', tampa=(True, True))
    p.varrer(reto((0, -0.44, 0), (0, 0.44, 0)), (-0.30, 0.30, 0.0, 0.025), 'P_Cristal', tampa=(True, True))   # berço (não toca a junção)
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); m.porta('ITEM', 'SAI', 'N', perfil='esteira')
    return m


TODOS = [fornalha_ht, montadora_ht, gerador_ht, esteira_ht]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, PR, '_relatorio_proposta.json'))
