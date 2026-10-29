"""Máquinas, energia e defesa. Corpo recuado 0,05 m da borda da área (cantos livres para pilares);
só bocas de item e canos de fluido chegam à borda, nas portas.
Uso: blender --background --python maquinas.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, cano_trecho, reto, girar_cam, curva_canto, terminal, terminais_cantos, CANO_Z, CANO_R
from mathutils import Vector

M, EN, D = 'maquinas', 'energia', 'defesa'
PI = math.pi
RECUO = 0.05

def boca_ht(p, m, lado, k, io, larg=0.44):
    """Boca de item high-tech: bloco baixo chanfrado na borda, fenda de luz (laranja = entra, ciano = sai)."""
    hw, hd = m.w/2, m.d/2
    luz = 'P_Cristal' if io == 'SAI' else 'P_Fogo'
    if lado in 'SN':
        x = -hw + 0.5 + k if lado == 'S' else hw - 0.5 - k
        y0 = -hd if lado == 'S' else hd - 0.30; y1 = y0 + 0.30
        v = p.caixa(x - larg/2 - 0.05, x + larg/2 + 0.05, y0 + (0.012 if lado == 'S' else 0), y1 - (0.012 if lado == 'N' else 0),
                    0.0, 0.40, 'P_Escuro'); p.chanfrar(v, 0.04)
        yb = -hd if lado == 'S' else hd - 0.015
        p.caixa(x - larg/2, x + larg/2, yb, yb + 0.015, 0.17, 0.30, luz)
        p.caixa(x - larg/2, x + larg/2, y0 + 0.08, y1 - 0.08, 0.40, 0.415, luz)
    else:
        y = hd - 0.5 - k if lado == 'L' else -hd + 0.5 + k
        x0 = hw - 0.30 if lado == 'L' else -hw; x1 = x0 + 0.30
        v = p.caixa(x0 + (0.012 if lado == 'O' else 0), x1 - (0.012 if lado == 'L' else 0), y - larg/2 - 0.05, y + larg/2 + 0.05,
                    0.0, 0.40, 'P_Escuro'); p.chanfrar(v, 0.04)
        xb = hw - 0.015 if lado == 'L' else -hw
        p.caixa(xb, xb + 0.015, y - larg/2, y + larg/2, 0.17, 0.30, luz)
        p.caixa(x0 + 0.08, x1 - 0.08, y - larg/2, y + larg/2, 0.40, 0.415, luz)
    m.porta('ITEM', io, lado, k)


def base_ht(p, w, d, h=0.10):
    """Placa grafite chanfrada com um veio de luz rente à borda."""
    v = p.caixa(-w/2 + RECUO, w/2 - RECUO, -d/2 + RECUO, d/2 - RECUO, 0, h, 'P_Escuro'); p.chanfrar(v, 0.05)
    e = 0.10
    for (x0, x1, y0, y1) in ((-w/2 + e, w/2 - e, -d/2 + e, -d/2 + e + 0.03), (-w/2 + e, w/2 - e, d/2 - e - 0.03, d/2 - e),
                             (-w/2 + e, -w/2 + e + 0.03, -d/2 + e + 0.03, d/2 - e - 0.03), (w/2 - e - 0.03, w/2 - e, -d/2 + e + 0.03, d/2 - e - 0.03)):
        p.caixa(x0, x1, y0, y1, h, h + 0.012, 'P_Cristal')


def placa(p, w, d, h=0.12):
    v = p.caixa(-w/2 + RECUO, w/2 - RECUO, -d/2 + RECUO, d/2 - RECUO, 0, h, 'P_Concreto'); p.chanfrar(v, 0.04)

def boca(p, m, lado, k, io, larg=0.44):
    """Boca de item na borda (sai/entra no tile vizinho na altura da lona)."""
    hw, hd = m.w/2, m.d/2
    if lado in 'SN':
        x = -hw + 0.5 + k if lado == 'S' else hw - 0.5 - k; y0 = -hd if lado == 'S' else hd - 0.32; y1 = y0 + 0.32
        p.caixa(x - larg/2 - 0.06, x + larg/2 + 0.06, y0 + (0.012 if lado == 'S' else 0), y1 - (0.012 if lado == 'N' else 0), 0.0, 0.56, 'P_Escuro')
        yb = -hd if lado == 'S' else hd - 0.02
        p.caixa(x - larg/2, x + larg/2, yb, yb + 0.02, 0.16, 0.42, 'P_Cristal' if io == 'SAI' else 'P_Faixa')
    else:
        y = hd - 0.5 - k if lado == 'L' else -hd + 0.5 + k; x0 = hw - 0.32 if lado == 'L' else -hw; x1 = x0 + 0.32
        p.caixa(x0 + (0.012 if lado == 'O' else 0), x1 - (0.012 if lado == 'L' else 0), y - larg/2 - 0.06, y + larg/2 + 0.06, 0.0, 0.56, 'P_Escuro')
        xb = hw - 0.02 if lado == 'L' else -hw
        p.caixa(xb, xb + 0.02, y - larg/2, y + larg/2, 0.16, 0.42, 'P_Cristal' if io == 'SAI' else 'P_Faixa')
    m.porta('ITEM', io, lado, k)

def cano_porta(p, m, lado, k, io, ate):
    """Toco de cano da parede (distância `ate` do centro da borda para dentro) até a borda, com flange."""
    hw, hd = m.w/2, m.d/2
    if lado in 'SN':
        x = -hw + 0.5 + k if lado == 'S' else hw - 0.5 - k; s = -1 if lado == 'S' else 1
        cano_trecho(p, reto((x, s*(hd - ate), 0), (x, s*hd, 0)), flange_ini=False)
    else:
        y = hd - 0.5 - k if lado == 'L' else -hd + 0.5 + k; s = 1 if lado == 'L' else -1
        cano_trecho(p, reto((s*(hw - ate), y, 0), (s*hw, y, 0)), flange_ini=False)
    m.porta('FLUIDO', io, lado, k, perfil='cano')

# ---------------------------------------------------------------- extração
def extrator_cristal():
    m = Modelo('extrator_cristal', M, 3, 3, descricao='Extrator de Cristal: vai sobre jazida de cristal. Saída no meio da borda sul.')
    p = m.parte(); placa(p, 3, 3)
    v = p.caixa(-1.25, 1.25, -1.25, 1.25, 0.12, 0.52, 'P_Escuro'); p.chanfrar(v, 0.08)
    v = p.caixa(-1.10, 1.10, -1.10, 1.10, 0.52, 0.60, 'P_Metal'); p.chanfrar(v, 0.05)
    p.cil((0, 0, 1.25), 0.62, 1.30, 'P_Metal', lados=8, rot=PI/8)
    p.cil((0, 0, 0.75), 0.66, 0.08, 'P_Faixa', lados=8, rot=PI/8)
    p.cil((0, 0, 1.60), 0.66, 0.10, 'P_Escuro', lados=8, rot=PI/8)
    for i in range(4):
        a = i*PI/2; p.caixa_c(math.cos(a)*0.66, math.sin(a)*0.66, 0.85, 0.10, 0.30, 0.70, 'P_Escuro', rot=a)
    p.cil((0, 0, 2.075), 0.62, 0.35, 'P_Metal', lados=8, r2=0.30, rot=PI/8)
    p.cil((0, 0, 2.29), 0.34, 0.10, 'P_Escuro', lados=8, rot=PI/8)
    cr = m.parte('cristal', pai='corpo', pivo=(0, 0, 2.30))            # pulsa (escala/brilho)
    cr.cil((0, 0, 2.75), 0.22, 0.90, 'P_Cristal', lados=6, r2=0.0)
    h = m.parte('hastes', pai='corpo', pivo=(0, 0, 0))                 # sobe e desce (pistões + braços)
    for i in range(4):
        a = PI/4 + i*PI/2; x, y = math.cos(a)*1.25, math.sin(a)*1.25
        p.cil((x, y, 0.82), 0.17, 0.45, 'P_Escuro', lados=6); h.cil((x, y, 1.30), 0.09, 0.60, 'P_Cobre', lados=6)
        h.caixa_c(math.cos(a)*0.93, math.sin(a)*0.93, 1.57, 0.72, 0.14, 0.10, 'P_Metal', rot=a)
    boca(p, m, 'S', 1, 'SAI')
    # cano único: sai da torre, faz a curva e desce até a boca
    cam = [(Vector((0, -0.55, 1.0)), Vector((0, -1, 0)))]
    for i in range(5):
        a = (PI/2)*i/4
        cam.append((Vector((0, -1.18 - 0.15*math.sin(a), 0.85 + 0.15*math.cos(a))), Vector((0, -math.cos(a), -math.sin(a)))))
    cam.append((Vector((0, -1.33, 0.56)), Vector((0, 0, -1))))
    p.tubo(cam, 0.09, 'P_Cobre', tampa=(True, True), lado=(1, 0, 0))
    terminais_cantos(m, p, 0.12)
    return m

def broca_minerio():
    m = Modelo('broca_minerio', M, 2, 2, descricao='Broca de minério (ferro, cobre, pedra, carvão, sílex). Saída sul (tile da esquerda).')
    p = m.parte(); placa(p, 2, 2)
    v = p.caixa(-0.80, 0.80, -0.80, 0.80, 0.12, 0.70, 'P_Metal'); p.chanfrar(v, 0.05)
    p.caixa(-0.81, 0.81, -0.81, 0.81, 0.40, 0.48, 'P_Faixa')
    v = p.caixa(-0.45, 0.45, -0.45, 0.45, 0.70, 1.05, 'P_Escuro'); p.chanfrar(v, 0.04)
    r = m.parte('rotor', pai='corpo', pivo=(0, 0, 1.10))               # gira em Z
    r.cil((0, 0, 1.45), 0.18, 0.80, 'P_Metal', lados=8, r2=0.10)
    r.engrenagem((0.0, 0.0, 1.10), 0.40, 0.32, 10, 0.08, 'P_Cobre')
    p.cil((0.55, 0.55, 1.05), 0.10, 0.70, 'P_Escuro', lados=6)
    boca(p, m, 'S', 0, 'SAI')
    terminais_cantos(m, p, 0.12)
    return m

# ---------------------------------------------------------------- produção
def fornalha():
    m = Modelo('fornalha', M, 2, 2, descricao='fornalha de indução: cadinho octogonal, núcleo incandescente '
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
    boca_ht(p, m, 'S', 1, 'ENT'); boca_ht(p, m, 'N', 0, 'SAI')
    return m

def montadora():
    m = Modelo('montadora', M, 3, 3, descricao='montadora: câmara blindada octogonal, anel manipulador '
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
    boca_ht(p, m, 'S', 1, 'ENT'); boca_ht(p, m, 'N', 1, 'SAI')
    terminais_cantos(m, p, 0.112)
    return m

def refinador():
    m = Modelo('refinador', M, 3, 3, descricao='Refinador: processa fluidos (seiva, óleo). Fluido entra a oeste, sai a leste; item ao norte.')
    p = m.parte(); placa(p, 3, 3)
    v = p.caixa(-1.20, 0.20, -1.20, 1.20, 0.12, 0.60, 'P_Metal'); p.chanfrar(v, 0.05)
    for y in (-0.55, 0.55):
        p.cil((-0.55, y, 1.20), 0.45, 1.20, 'P_Metal', lados=10)
        p.cil((-0.55, y, 1.84), 0.45, 0.08, 'P_Faixa', lados=10)
        p.cil((-0.55, y, 1.96), 0.45, 0.16, 'P_Escuro', lados=10, r2=0.25)
    p.cil((0.70, 0.0, 1.60), 0.35, 3.0, 'P_Escuro', lados=8)
    for z in (0.8, 1.6, 2.4): p.cil((0.70, 0.0, z), 0.38, 0.10, 'P_Cobre', lados=8)
    p.cil((0.70, 0.0, 3.15), 0.06, 0.10, 'P_Cristal', lados=6)
    p.barra((-0.10, -0.55, 1.5), (0.40, 0.0, 1.5), 0.12, 0.12, 'P_Cobre')
    p.barra((-0.10, 0.55, 1.5), (0.40, 0.0, 1.53), 0.12, 0.12, 'P_Cobre')
    cano_porta(p, m, 'O', 1, 'ENT', 0.32); cano_porta(p, m, 'L', 1, 'SAI', 0.50)
    p.caixa(1.0, 1.45, -0.20, 0.20, 0.12, 0.60, 'P_Escuro')
    boca(p, m, 'N', 0, 'SAI')
    terminais_cantos(m, p, 0.12)
    return m

def laboratorio():
    m = Modelo('laboratorio', M, 3, 3, descricao='Laboratório: consome pacotes de pesquisa. Entra pelo sul (meio).')
    p = m.parte(); placa(p, 3, 3)
    v = p.cil((0, 0, 0.50), 1.30, 0.76, 'P_Metal', lados=12); p.chanfrar(v, 0.04)
    p.cil((0, 0, 0.92), 1.32, 0.08, 'P_Faixa', lados=12)
    p.cil((0, 0, 1.30), 1.10, 0.70, 'P_Vidro', lados=12, r2=0.55)
    p.cil((0, 0, 1.75), 0.55, 0.20, 'P_Escuro', lados=12)
    an = m.parte('antena', pai='corpo', pivo=(0, 0, 1.85))             # gira em Z
    an.cil((0, 0, 2.25), 0.05, 0.80, 'P_Metal', lados=6)
    an.caixa_c(0, 0, 2.30, 0.50, 0.06, 0.06, 'P_Escuro')
    an.cil((0, 0, 2.70), 0.14, 0.18, 'P_Cristal', lados=6, r2=0.0)
    for i in range(3):
        a = PI/2 + i*2*PI/3; p.cil((math.cos(a)*0.60, math.sin(a)*0.60, 1.35), 0.12, 0.30, 'P_Cristal', lados=6)
    boca(p, m, 'S', 1, 'ENT')
    terminais_cantos(m, p, 0.12)
    return m

def nucleo():
    m = Modelo('nucleo', M, 3, 3, descricao='Núcleo: a unidade semeadora da IA. Tudo que entra (esteira nas 4 bocas ou braço) '
               'vira estoque para construir. Partes: cristal (monólito pulsa), antena (anel gira).')
    p = m.parte(); base_ht(p, 3, 3)
    v = p.cil((0, 0, 0.36), 1.06, 0.52, 'P_Escuro', lados=8, rot=PI/8, r2=0.96); p.chanfrar(v, 0.04)
    p.cil((0, 0, 0.64), 0.97, 0.05, 'P_Cristal', lados=8, rot=PI/8)
    v = p.cil((0, 0, 0.84), 0.80, 0.34, 'P_Aco', lados=8, rot=PI/8, r2=0.62); p.chanfrar(v, 0.03)
    for k in range(4):                                         # contrafortes que seguram o monólito
        a = PI/4 + k*PI/2
        p.barra((math.cos(a)*0.92, math.sin(a)*0.92, 0.62), (math.cos(a)*0.50, math.sin(a)*0.50, 1.18), 0.12, 0.12, 'P_Metal')
        p.cil((math.cos(a)*0.48, math.sin(a)*0.48, 1.24), 0.07, 0.08, 'P_Cristal', lados=6)
    p.cil((0, 0, 1.32), 0.34, 0.62, 'P_Escuro', lados=6, r2=0.27)
    cr = m.parte('cristal', pai='corpo', pivo=(0, 0, 1.66))   # monólito de cristal (pulsa)
    cr.cil((0, 0, 2.12), 0.28, 0.88, 'P_Cristal', lados=6, r2=0.0)
    cr.cil((0, 0, 1.74), 0.27, 0.16, 'P_Cristal', lados=6, r2=0.22)
    an = m.parte('antena', pai='corpo', pivo=(0, 0, 1.92))     # anel de dados (gira)
    for k in range(12):
        a = k*PI/6
        an.caixa_c(math.cos(a)*0.62, math.sin(a)*0.62, 1.92, 0.20, 0.07, 0.05, 'P_Aco', rot=a + PI/2)
    for lado in 'SNLO':
        boca_ht(p, m, lado, 1, 'ENT')
    return m

def terraplenagem():
    m = Modelo('terraplenagem', M, 3, 3, descricao='Terraplenagem: unidade de modelagem do terreno da IA. Enquanto existir, libera '
               'Aplainar em qualquer lugar do mapa. Partes: antena (anel de sensores gira), cristal (núcleo pulsa), bloco (rocha suspensa).')
    p = m.parte()
    v = p.caixa(-1.45, 1.45, -1.45, 1.45, 0.0, 0.10, 'P_Escuro'); p.chanfrar(v, 0.05)
    # base octogonal blindada com veios de luz
    v = p.cil((0, 0, 0.30), 1.05, 0.40, 'P_Metal', lados=8, rot=PI/8, r2=0.92); p.chanfrar(v, 0.04)
    p.cil((0, 0, 0.52), 0.94, 0.05, 'P_Cristal', lados=8, rot=PI/8)
    v = p.cil((0, 0, 0.66), 0.88, 0.22, 'P_Escuro', lados=8, rot=PI/8, r2=0.70); p.chanfrar(v, 0.03)
    # coluna emissora
    p.cil((0, 0, 1.25), 0.22, 1.00, 'P_Aco', lados=8, rot=PI/8, r2=0.16)
    for z in (0.95, 1.30, 1.65):
        p.cil((0, 0, z), 0.25, 0.04, 'P_Cristal', lados=8, rot=PI/8)
    # três emissores nos cantos, inclinados para o campo
    for a in (PI/4, PI/4 + 2*PI/3, PI/4 + 4*PI/3):
        x, y = math.cos(a) * 1.18, math.sin(a) * 1.18
        v = p.cil((x, y, 0.22), 0.20, 0.24, 'P_Escuro', lados=6); p.chanfrar(v, 0.03)
        p.barra((x, y, 0.32), (x * 0.78, y * 0.78, 0.95), 0.08, 0.08, 'P_Metal')
        p.cil((x * 0.76, y * 0.76, 0.98), 0.07, 0.10, 'P_Cristal', lados=6)
    # anel de sensores (gira)
    an = m.parte('antena', pai='corpo', pivo=(0, 0, 1.48))
    for k in range(10):
        a = k * 2 * PI / 10
        an.caixa_c(math.cos(a) * 0.62, math.sin(a) * 0.62, 1.48, 0.16, 0.10, 0.06, 'P_Metal', rot=a)
        if k % 2 == 0:
            an.cil((math.cos(a) * 0.62, math.sin(a) * 0.62, 1.53), 0.03, 0.04, 'P_Cristal', lados=6)
    # núcleo de cristal no topo (pulsa)
    cr = m.parte('cristal', pai='corpo', pivo=(0, 0, 1.80))
    cr.cil((0, 0, 2.02), 0.24, 0.42, 'P_Cristal', lados=6, r2=0.0)
    cr.cil((0, 0, 1.84), 0.26, 0.10, 'P_Cristal', lados=6, r2=0.24)
    # bloco de rocha compactada suspenso no campo (sobe e desce: "cabecote")
    bl = m.parte('cabecote', pai='corpo', pivo=(-0.92, -0.92, 1.25))
    v = bl.caixa_c(-0.92, -0.92, 1.30, 0.38, 0.34, 0.30, 'P_Rocha', rot=0.35); bl.chanfrar(v, 0.04)
    bl.cil((-0.92, -0.92, 1.10), 0.10, 0.03, 'P_Cristal', lados=6)
    return m

# ---------------------------------------------------------------- energia
def gerador():
    m = Modelo('gerador', EN, 2, 2, descricao='gerador: câmara de reação vertical com anéis de contenção '
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
    boca_ht(p, m, 'S', 1, 'ENT')
    terminais_cantos(m, p, 0.112)
    return m

def poste_energia():
    m = Modelo('poste_energia', EN, 1, 1, descricao='Poste de energia: liga máquinas num raio. Ocupa só o centro do tile.')
    p = m.parte()
    v = p.caixa(-0.20, 0.20, -0.20, 0.20, 0.0, 0.10, 'P_Concreto'); p.chanfrar(v, 0.02)
    p.cil((0, 0, 1.10), 0.06, 2.0, 'P_Metal', lados=6)
    p.caixa_c(0, 0, 1.85, 0.70, 0.08, 0.08, 'P_Escuro')
    for x in (-0.30, 0.30): p.cil((x, 0, 2.00), 0.04, 0.14, 'P_Cobre', lados=6)
    p.cil((0, 0, 2.20), 0.07, 0.20, 'P_Cristal', lados=6, r2=0.0)
    return m

def torre_sem_fio():
    m = Modelo('torre_sem_fio', EN, 1, 1, descricao='Torre de energia sem fio: liga postes/torres e máquinas a distância, sem cabo.')
    p = m.parte()
    v = p.caixa(-0.40, 0.40, -0.40, 0.40, 0.0, 0.14, 'P_Concreto'); p.chanfrar(v, 0.03)
    p.cil((0, 0, 0.55), 0.26, 0.82, 'P_Escuro', lados=8, r2=0.14)
    p.cil((0, 0, 1.55), 0.08, 1.20, 'P_Metal', lados=6)
    for z in (1.15, 1.40, 1.65, 1.90):                       # bobina
        p.cil((0, 0, z), 0.20, 0.06, 'P_Cobre', lados=10)
    p.cil((0, 0, 2.25), 0.30, 0.10, 'P_Faixa', lados=10)
    cr = m.parte('cristal', pai='corpo', pivo=(0, 0, 2.30))   # pulsa (Animador)
    cr.cil((0, 0, 2.62), 0.22, 0.55, 'P_Cristal', lados=6, r2=0.0)
    return m

def tanque():
    m = Modelo('tanque', EN, 2, 2, descricao='Tanque de fluido. Canos nos 4 lados (tile da esquerda de cada lado).')
    p = m.parte(); placa(p, 2, 2)
    p.cil((0, 0, 0.85), 0.80, 1.30, 'P_Metal', lados=12)
    p.cil((0, 0, 1.10), 0.82, 0.08, 'P_Faixa', lados=12)
    p.cil((0, 0, 1.60), 0.80, 0.20, 'P_Escuro', lados=12, r2=0.40)
    p.caixa_c(0, -0.80, 0.30, 0.20, 0.06, 1.00, 'P_Vidro')
    for l in 'SNLO': cano_porta(p, m, l, 0, 'SAI', 0.42)
    return m

# ---------------------------------------------------------------- defesa
def torre_defesa():
    m = Modelo('torre_defesa', D, 2, 2, descricao='Torre de defesa. Munição entra pelo sul. Partes: base, giro (gira em Z), canhao (inclina).')
    b = m.parte('base'); placa(b, 2, 2)
    v = b.cil((0, 0, 0.45), 0.75, 0.66, 'P_Escuro', lados=8, rot=PI/8); b.chanfrar(v, 0.05)
    b.cil((0, 0, 0.82), 0.60, 0.08, 'P_Faixa', lados=8, rot=PI/8)
    boca(b, m, 'S', 1, 'ENT', larg=0.30)
    g = m.parte('giro', pai='base', pivo=(0, 0, 0.86))
    v = g.cil((0, 0, 1.06), 0.50, 0.40, 'P_Metal', lados=8, rot=PI/8); g.chanfrar(v, 0.04)
    g.caixa_c(0, -0.10, 1.26, 0.70, 0.60, 0.20, 'P_Metal')
    g.cil((0, 0.25, 1.40), 0.06, 0.10, 'P_Cristal', lados=6)
    c = m.parte('canhao', pai='giro', pivo=(0, -0.20, 1.20))
    c.cil((0, -0.20, 1.20), 0.14, 0.40, 'P_Escuro', eixo='X', lados=8)
    for x in (-0.09, 0.09): c.barra((x, -0.20, 1.20), (x, -0.88, 1.24), 0.07, 0.07, 'P_Aco')
    return m

def muro_centro():
    m = Modelo('muro_centro', D, 1, 1, descricao='Pilar do muro (centro do tile). O jogo junta muro_lado para cada vizinho com muro.')
    m.ocupa_canto = True; p = m.parte()
    v = p.caixa(-0.30, 0.30, -0.30, 0.30, 0.0, 1.40, 'P_Concreto'); p.chanfrar(v, 0.04)
    p.caixa(-0.32, 0.32, -0.32, 0.32, 1.40, 1.50, 'P_Faixa')
    return m

def muro_lado():
    m = Modelo('muro_lado', D, 1, 1, descricao='Pano de muro do centro até a borda norte (girar para os outros lados).')
    m.ocupa_canto = True; p = m.parte()
    p.caixa(-0.22, 0.22, 0.30, 0.50, 0.0, 1.20, 'P_Concreto')
    p.caixa(-0.24, 0.24, 0.30, 0.50, 1.20, 1.26, 'P_Escuro')
    return m

TODOS = [nucleo, extrator_cristal, broca_minerio, fornalha, montadora, refinador, laboratorio, terraplenagem,
         gerador, poste_energia, torre_sem_fio, tanque, torre_defesa, muro_centro, muro_lado]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'maquinas', '_relatorio_maquinas.json'))
