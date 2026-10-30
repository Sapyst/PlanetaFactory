"""Estudo isolado (fora do jogo): braço mecânico com mais detalhe — pistão hidráulico, treliça, mangueira com
abraçadeiras, cabos com presilhas, motor com aletas, juntas reforçadas, punho e garra pneumática.
Mesmas partes do braço do jogo (base, giro, braco1, braco2, garra) e mesma escala (1 tile).
Uso: blender -b --factory-startup --python estudo_braco.py"""
import sys, os, math
sys.path.insert(0, '/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/blender_scripts')
import lib_pf
lib_pf.RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelos')    # isolado: nada vai para o jogo
from lib_pf import Modelo, rodar, Q, terminal
from mathutils import Vector, Matrix
import bmesh

PI = math.pi


def tubo(p, a, b, r0, r1, mat, lados=6, sobra=0.0):
    a, b = Vector(a), Vector(b)
    d = (b - a)
    u = d.normalized()
    a2, b2 = a - u * sobra, b + u * sobra                     # sobra: emenda de segmentos sem fresta
    d = b2 - a2
    q = d.normalized().to_track_quat('Z', 'Y')
    M = Matrix.Translation((a2 + b2) / 2) @ q.to_matrix().to_4x4()
    res = bmesh.ops.create_cone(p.bm, cap_ends=True, segments=lados, radius1=r0, radius2=r1, depth=d.length, matrix=M)
    for v in res['verts']:
        v.co = Q(v.co)
    p.faces_de(res['verts'], mat)


def bezier(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3)
    return out


def mangueira(p, pts, r, mat, aneis=None, passo=3, r_anel=None, mat_anel='P_Metal'):
    """Tubo flexível por pontos, com abraçadeiras (anéis) a cada `passo` pontos."""
    for i in range(len(pts) - 1):
        tubo(p, pts[i], pts[i + 1], r, r, mat, lados=6, sobra=r * 0.6)
    if aneis:
        for i in range(passo, len(pts) - 1, passo):
            u = (pts[i + 1] - pts[i - 1]).normalized()
            tubo(p, pts[i] - u * 0.012, pts[i] + u * 0.012, r_anel or r * 1.45, r_anel or r * 1.45, mat_anel, lados=8)


def braco_detalhado():
    m = Modelo('braco_detalhado', 'estudos', descricao='Estudo: braço com pistão, treliça, mangueira e cabos.', orcamento=4000)
    l1, l2 = 0.55, 0.62
    # ---------------------------------------------------------------- base: plinto, anel de parafusos, caixa de ligação
    base = m.parte('base')
    base.cil((0, 0, 0.03), 0.31, 0.06, 'P_Escuro', lados=8, rot=PI / 8)
    base.cil((0, 0, 0.075), 0.26, 0.03, 'P_Aco', lados=8, rot=PI / 8)
    for k in range(8):
        a = k * PI / 4
        base.cil((math.cos(a) * 0.225, math.sin(a) * 0.225, 0.095), 0.016, 0.012, 'P_Metal', lados=6)
    base.cil((0, 0, 0.16), 0.13, 0.14, 'P_Metal', lados=12)
    base.cil((0, 0, 0.215), 0.145, 0.02, 'P_Escuro', lados=12)              # anel coletor sob o giro
    base.caixa_c(0.18, -0.12, 0.09, 0.08, 0.06, 0.07, 'P_Escuro')              # caixa de ligação, sobre o anel
    base.caixa_c(0.18, -0.12, 0.16, 0.06, 0.04, 0.012, 'P_Faixa')
    terminal(m, base, 0.33, -0.33, 0.0, baixo=True)
    cabo_base = bezier((0.15, -0.12, 0.13), (0.13, -0.07, 0.15), (0.12, -0.03, 0.19), (0.13, 0.0, 0.205), 6)
    mangueira(base, cabo_base, 0.011, 'P_Escuro')
    # ---------------------------------------------------------------- giro: corpo, motor com aletas, mancais do ombro
    giro = m.parte('giro', pai='base', pivo=(0, 0, 0.225))
    v = giro.caixa_c(0, 0, 0.225, 0.26, 0.26, 0.11, 'P_Faixa')
    giro.chanfrar(v, 0.02)
    giro.caixa_c(0, -0.02, 0.33, 0.20, 0.16, 0.03, 'P_Escuro')                  # tampa (encaixada no corpo)
    giro.cil((-0.17, 0.0, 0.28), 0.055, 0.10, 'P_Aco', lados=10, eixo='X')     # motor do giro, de lado
    for k in range(4):
        giro.cil((-0.135 - 0.024 * k, 0.0, 0.28), 0.066, 0.008, 'P_Escuro', lados=10, eixo='X')   # aletas
    giro.cil((-0.225, 0.0, 0.28), 0.03, 0.02, 'P_Cobre', lados=8, eixo='X')
    for x in (-0.085, 0.085):                                                  # mancais do ombro
        v = giro.caixa_c(x, 0.0, 0.32, 0.035, 0.11, 0.10, 'P_Aco')
        giro.cil((x * 1.32, 0.0, 0.37), 0.022, 0.012, 'P_Metal', lados=6, eixo='X')
    giro.caixa_c(0.10, -0.11, 0.335, 0.07, 0.05, 0.05, 'P_Escuro')             # bloco de válvulas
    for k in range(2):
        giro.cil((0.085 + 0.03 * k, -0.11, 0.39), 0.012, 0.02, 'P_Cobre', lados=6)
    # camisa do pistão: presa atrás, no giro (articulação)
    ancora = Vector((0.0, -0.12, 0.31))
    giro.cil(tuple(ancora), 0.03, 0.08, 'P_Escuro', lados=8, eixo='X')
    sh = Vector((0, 0, 0.37))
    el = sh + Vector((0, 0.10, l1))
    wr = el + Vector((0, l2 * 0.30, -l2 * 0.95))
    alvo_pistao = sh + (el - sh) * 0.48 + Vector((0, -0.045, 0))
    meio = ancora + (alvo_pistao - ancora) * 0.58
    tubo(giro, ancora, meio, 0.028, 0.028, 'P_Aco', lados=10)
    tubo(giro, meio - (meio - ancora).normalized() * 0.01, meio + (meio - ancora).normalized() * 0.015, 0.034, 0.034, 'P_Escuro', lados=10)
    # ---------------------------------------------------------------- braço 1: treliça (duas longarinas + travessas)
    b1 = m.parte('braco1', pai='giro', pivo=tuple(sh))
    b1.cil(tuple(sh), 0.045, 0.15, 'P_Escuro', lados=10, eixo='X')
    for x in (-0.045, 0.045):
        b1.barra(sh + Vector((x, 0, 0)), el + Vector((x, 0, 0)), 0.022, 0.05, 'P_Metal')
    for k in range(1, 5):
        f = k / 5.0
        c = sh + (el - sh) * f
        b1.barra(c + Vector((-0.04, 0, 0)), c + Vector((0.04, 0, 0)), 0.018, 0.018, 'P_Aco')
    tubo(b1, meio, alvo_pistao, 0.014, 0.014, 'P_Metal', lados=8)              # haste cromada do pistão
    b1.cil(tuple(alvo_pistao), 0.02, 0.10, 'P_Escuro', lados=8, eixo='X')     # olhal da haste
    # ---------------------------------------------------------------- cotovelo reforçado
    b1.cil(tuple(el), 0.058, 0.14, 'P_Escuro', lados=10, eixo='X')
    for x in (-0.075, 0.075):
        b1.cil((el.x + x, el.y, el.z), 0.04, 0.012, 'P_Aco', lados=8, eixo='X')
        b1.cil((el.x + x * 1.12, el.y, el.z), 0.014, 0.012, 'P_Metal', lados=6, eixo='X')
    # mangueira do bloco de válvulas até o cotovelo, com abraçadeiras; cabos ao lado com presilhas
    hose = bezier((0.10, -0.11, 0.40), (0.14, -0.10, 0.52), (0.09, -0.02, 0.80), (0.06, el.y - 0.03, el.z - 0.02), 12)
    mangueira(b1, hose, 0.016, 'P_Escuro', aneis=True, passo=3)
    for dx, mat in ((-0.075, 'P_Cobre'), (-0.062, 'P_Escuro')):
        cabo = bezier((dx, -0.03, 0.40), (dx - 0.01, -0.02, 0.55), (dx, 0.04, 0.78), (dx, el.y - 0.02, el.z - 0.05), 10)
        mangueira(b1, cabo, 0.007, mat)
    for k in range(1, 4):
        f = k / 4.0
        c = sh + (el - sh) * f
        b1.caixa_c(-0.068, c.y, c.z, 0.03, 0.03, 0.02, 'P_Metal')               # presilhas dos cabos
    # ---------------------------------------------------------------- braço 2: viga afilada com furos de alívio
    b2 = m.parte('braco2', pai='braco1', pivo=tuple(el))
    tubo(b2, el, wr, 0.04, 0.03, 'P_Faixa', lados=8)
    for k in (0.3, 0.55):
        c = el + (wr - el) * k
        b2.cil(tuple(c), 0.022, 0.09, 'P_Escuro', lados=8, eixo='X')
    cabo2 = bezier((0.06, el.y - 0.02, el.z - 0.04), (0.08, el.y + 0.05, el.z - 0.15), (0.07, wr.y - 0.06, wr.z + 0.2), (0.04, wr.y, wr.z + 0.05), 8)
    mangueira(b2, cabo2, 0.012, 'P_Escuro', aneis=True, passo=3)
    # ---------------------------------------------------------------- punho rotativo + garra pneumática
    g = m.parte('garra', pai='braco2', pivo=tuple(wr))
    g.cil((wr.x, wr.y, wr.z - 0.01), 0.045, 0.04, 'P_Aco', lados=10)
    g.cil((wr.x, wr.y, wr.z - 0.035), 0.05, 0.012, 'P_Escuro', lados=10)
    v = g.caixa_c(wr.x, wr.y, wr.z - 0.085, 0.13, 0.075, 0.045, 'P_Escuro')
    g.chanfrar(v, 0.008)
    g.cil((wr.x, wr.y + 0.05, wr.z - 0.065), 0.016, 0.09, 'P_Metal', lados=8, eixo='X')   # cilindro pneumático
    for x in (-0.05, 0.05):
        g.caixa_c(wr.x + x, wr.y, wr.z - 0.125, 0.022, 0.05, 0.03, 'P_Aco')               # dedo, falange 1
        g.caixa_c(wr.x + x * 0.86, wr.y, wr.z - 0.16, 0.02, 0.046, 0.04, 'P_Metal')       # falange 2 (para dentro)
        g.caixa_c(wr.x + x * 0.74, wr.y, wr.z - 0.19, 0.03, 0.04, 0.012, 'P_Escuro')      # ponta emborrachada
    m.porta('ITEM', 'ENT', 'S')
    m.porta('ITEM', 'SAI', 'N')
    return m


if __name__ == '__main__':
    os.makedirs(lib_pf.RAIZ, exist_ok=True)
    rodar([braco_detalhado], os.path.join(lib_pf.RAIZ, '_relatorio.json'))
