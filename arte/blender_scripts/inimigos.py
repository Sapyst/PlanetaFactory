"""Inimigos: aranha mecânica (corpo + segmentos de perna para IK no jogo) e ninho que elas constroem.
Aranha: frente = +Y no Blender (= -Z no Godot). Quadril em z = 0,55. Segmentos deitados ao longo de +X,
origem na articulação de cima: fêmur (0 → 0,70) e tíbia (0 → 0,90, ponta = pé).
Medidas usadas pelo código do jogo: jogo/inimigos/aranha_ik.gd (constantes iguais).
Uso: blender --background --python inimigos.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar
from mathutils import Vector

I = 'inimigos/aranha'
PI = math.pi
QUADRIL_Z = 0.55
FEMUR, TIBIA = 0.70, 0.90
# quadris (x, y) — 3 por lado; o jogo lê as mesmas posições
QUADRIS = [(s*0.42, y) for y in (0.35, 0.0, -0.35) for s in (1, -1)]

def aranha_corpo():
    m = Modelo('aranha_corpo', I, tipo='veiculo', orcamento=800, descricao='Corpo da aranha mecânica (origem no chão, sob o centro).')
    p = m.parte()
    v = p.cil((0, 0.05, QUADRIL_Z), 0.50, 0.26, 'P_Inimigo', lados=8, rot=PI/8)
    for v_ in v: v_.co.y *= 1.25
    p.cil((0, 0.05, QUADRIL_Z + 0.17), 0.36, 0.10, 'P_Escuro', lados=8, r2=0.24, rot=PI/8)
    p.pedra((0, -0.62, QUADRIL_Z + 0.08), 0.36, (0.9, 1.1, 0.75), 'P_Inimigo', 7, ruido=0.06)       # abdômen
    for k in range(3): p.cil((0, -0.40 - 0.20*k, QUADRIL_Z + 0.33 - 0.02*k), 0.035, 0.06, 'P_OlhoInimigo', lados=5)
    p.caixa_c(0, 0.72, QUADRIL_Z - 0.10, 0.36, 0.22, 0.20, 'P_Escuro')                              # cabeça
    for x in (-0.09, 0.09):
        p.cil((x, 0.84, QUADRIL_Z + 0.02), 0.045, 0.02, 'P_OlhoInimigo', eixo='Y', lados=6)
    for x in (-0.13, 0.13): p.barra((x, 0.80, QUADRIL_Z - 0.10), (x*1.2, 0.98, QUADRIL_Z - 0.22), 0.04, 0.04, 'P_Metal')  # mandíbulas
    for x, y in QUADRIS: p.cil((x, y, QUADRIL_Z), 0.09, 0.14, 'P_Metal', lados=6)                 # encaixes
    return m

def aranha_femur():
    m = Modelo('aranha_femur', I, tipo='segmento', orcamento=200, descricao=f'Fêmur ({FEMUR} m ao longo de +X, origem no quadril).')
    p = m.parte()
    p.cil((0, 0, 0), 0.08, 0.12, 'P_Escuro', eixo='Y', lados=8)
    p.barra((0.04, 0, 0), (FEMUR - 0.04, 0, 0), 0.08, 0.10, 'P_Inimigo', lado=(0, 1, 0))
    p.barra((0.15, 0, 0.06), (FEMUR - 0.15, 0, 0.06), 0.04, 0.03, 'P_Metal', lado=(0, 1, 0))
    p.cil((FEMUR, 0, 0), 0.07, 0.11, 'P_Metal', eixo='Y', lados=8)
    return m

def aranha_tibia():
    m = Modelo('aranha_tibia', I, tipo='segmento', orcamento=200, descricao=f'Tíbia ({TIBIA} m ao longo de +X, origem no joelho, ponta = pé).')
    p = m.parte()
    p.barra((0.0, 0, 0), (TIBIA*0.75, 0, 0), 0.07, 0.08, 'P_Inimigo', lado=(0, 1, 0))
    p.cil((TIBIA*0.80, 0, 0), 0.0, TIBIA*0.30, 'P_Metal', eixo='X', lados=6, r2=0.05)   # ponta (pé) afiada
    p.caixa_c(TIBIA*0.35, 0, 0.04, 0.18, 0.05, 0.03, 'P_OlhoInimigo')
    return m

def aranha_montada():
    """Só para prévia/conferência: pernas em pose de pé com IK analítica (mesma do jogo)."""
    m = Modelo('aranha_montada', I, tipo='veiculo', orcamento=3000, descricao='Prévia montada (não usar no jogo; o jogo monta com IK).')
    p = m.parte(); c = aranha_corpo().partes[0]
    import bmesh
    tmp = c.bm.copy(); tmp.to_mesh(me := lib_pf.bpy.data.meshes.new('_t')); p.bm.from_mesh(me)
    for (hx, hy) in QUADRIS:
        d = Vector((hx, hy, 0)).normalized(); pe = Vector((hx, hy, 0.05)) + d*1.0          # pé a 1 m do quadril
        q = Vector((hx, hy, QUADRIL_Z)); alvo = pe - q; dist = alvo.length
        a = math.acos(max(-1, min(1, (FEMUR**2 + dist**2 - TIBIA**2)/(2*FEMUR*dist))))
        base = math.atan2(alvo.z, Vector((alvo.x, alvo.y)).length); el = base + a
        joelho = q + d*(FEMUR*math.cos(el)) + Vector((0, 0, FEMUR*math.sin(el)))
        p.barra(q, joelho, 0.08, 0.10, 'P_Inimigo', lado=(-d.y, d.x, 0))
        p.cil(tuple(joelho), 0.07, 0.11, 'P_Metal', lados=8)
        p.barra(joelho, pe + Vector((0, 0, 0.0)), 0.07, 0.08, 'P_Inimigo', lado=(-d.y, d.x, 0))
    return m

def ninho_aranha():
    m = Modelo('ninho_aranha', I, 3, 3, descricao='Ninho construído pelas aranhas: gera novas aranhas. Alvo prioritário.')
    p = m.parte()
    v = p.cil((0, 0, 0.15), 1.40, 0.30, 'P_RochaEscura', lados=9);
    for i in range(7):
        a = 2*PI*i/7; r = 0.95
        p.barra((math.cos(a)*1.3, math.sin(a)*1.3, 0.2), (math.cos(a)*0.35, math.sin(a)*0.35, 1.7), 0.14, 0.12, 'P_Inimigo')
    p.cil((0, 0, 0.9), 0.55, 1.2, 'P_Escuro', lados=7, r2=0.30)
    p.cil((0, 0, 1.65), 0.25, 0.30, 'P_OlhoInimigo', lados=7, r2=0.10)
    for i in range(5):
        a = 2*PI*i/5 + 0.3; p.pedra((math.cos(a)*0.95, math.sin(a)*0.95, 0.40), 0.20, (1, 1, 1.2), 'P_Inimigo', 300 + i)
    lim = 1.46
    for v_ in p.bm.verts: v_.co.x = max(-lim, min(lim, v_.co.x)); v_.co.y = max(-lim, min(lim, v_.co.y))
    m.ocupa_canto = True
    return m

TODOS = [aranha_corpo, aranha_femur, aranha_tibia, aranha_montada, ninho_aranha]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'inimigos', '_relatorio_inimigos.json'))
