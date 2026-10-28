"""Máquinas, energia e defesa. Corpo recuado 0,05 m da borda da área (cantos livres para pilares);
só bocas de item e canos de fluido chegam à borda, nas portas.
Uso: blender --background --python maquinas.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, cano_trecho, reto, girar_cam, curva_canto, CANO_Z, CANO_R
from mathutils import Vector

M, EN, D = 'maquinas', 'energia', 'defesa'
PI = math.pi
RECUO = 0.05

def placa(p, w, d, h=0.12):
    v = p.caixa(-w/2 + RECUO, w/2 - RECUO, -d/2 + RECUO, d/2 - RECUO, 0, h, 'P_Concreto'); p.chanfrar(v, 0.04)

def boca(p, m, lado, k, io, larg=0.44):
    """Boca de item na borda (sai/entra no tile vizinho na altura da lona)."""
    hw, hd = m.w/2, m.d/2
    if lado in 'SN':
        x = -hw + 0.5 + k if lado == 'S' else hw - 0.5 - k; y0 = -hd if lado == 'S' else hd - 0.32; y1 = y0 + 0.32
        p.caixa(x - larg/2 - 0.06, x + larg/2 + 0.06, y0, y1, 0.0, 0.56, 'P_Escuro')
        yb = -hd if lado == 'S' else hd - 0.02
        p.caixa(x - larg/2, x + larg/2, yb, yb + 0.02, 0.16, 0.42, 'P_Cristal' if io == 'SAI' else 'P_Faixa')
    else:
        y = hd - 0.5 - k if lado == 'L' else -hd + 0.5 + k; x0 = hw - 0.32 if lado == 'L' else -hw; x1 = x0 + 0.32
        p.caixa(x0, x1, y - larg/2 - 0.06, y + larg/2 + 0.06, 0.0, 0.56, 'P_Escuro')
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
    return m

# ---------------------------------------------------------------- produção
def fornalha():
    m = Modelo('fornalha', M, 2, 2, descricao='Fornalha: funde minério em placa/barra. Entra pelo sul, sai pelo norte.')
    p = m.parte(); placa(p, 2, 2)
    v = p.caixa(-0.78, 0.78, -0.70, 0.78, 0.12, 1.10, 'P_Tijolo'); p.chanfrar(v, 0.05)
    p.caixa(-0.30, 0.30, -0.72, -0.70, 0.30, 0.70, 'P_Fogo')
    p.caixa(-0.40, 0.40, -0.74, -0.70, 0.70, 0.78, 'P_Escuro')
    v = p.caixa(-0.82, 0.82, -0.74, 0.82, 1.10, 1.22, 'P_Escuro'); p.chanfrar(v, 0.03)
    p.cil((0.45, 0.40, 1.70), 0.18, 0.96, 'P_Tijolo', lados=8)
    p.cil((0.45, 0.40, 2.22), 0.20, 0.08, 'P_Escuro', lados=8)
    boca(p, m, 'S', 1, 'ENT'); boca(p, m, 'N', 0, 'SAI')
    return m

def montadora():
    m = Modelo('montadora', M, 3, 3, descricao='Montadora: monta peças por receita. Entra pelo sul, sai pelo norte (meio).')
    p = m.parte(); placa(p, 3, 3)
    v = p.caixa(-1.25, 1.25, -1.25, 1.25, 0.12, 1.30, 'P_Metal'); p.chanfrar(v, 0.08)
    p.caixa(-1.26, 1.26, -1.26, 1.26, 0.90, 1.00, 'P_Faixa')
    p.caixa(-0.80, 0.80, -1.27, -1.25, 0.40, 0.85, 'P_Vidro')
    v = p.caixa(-0.95, 0.95, -0.95, 0.95, 1.30, 1.55, 'P_Escuro'); p.chanfrar(v, 0.05)
    b = m.parte('braco', pai='corpo', pivo=(0, 0, 1.55))               # gira em Z (vai e volta)
    b.cil((0, 0, 1.70), 0.30, 0.30, 'P_Metal', lados=8)
    b.barra((0, 0, 1.85), (0.55, 0.25, 2.35), 0.14, 0.14, 'P_Faixa')
    b.barra((0.55, 0.25, 2.35), (0.85, 0.40, 1.80), 0.12, 0.12, 'P_Metal')
    b.cil((0.85, 0.40, 1.74), 0.07, 0.12, 'P_Cristal', lados=6)
    for x in (-0.9, 0.9): p.cil((x, 0.9, 1.75), 0.12, 0.40, 'P_Cobre', lados=6)
    boca(p, m, 'S', 1, 'ENT'); boca(p, m, 'N', 1, 'SAI')
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
    p.barra((-0.10, 0.55, 1.5), (0.40, 0.0, 1.5), 0.12, 0.12, 'P_Cobre')
    cano_porta(p, m, 'O', 1, 'ENT', 0.32); cano_porta(p, m, 'L', 1, 'SAI', 0.50)
    p.caixa(1.0, 1.45, -0.20, 0.20, 0.12, 0.60, 'P_Escuro')
    boca(p, m, 'N', 0, 'SAI')
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
    return m

def nucleo():
    m = Modelo('nucleo', M, 3, 3, descricao='Núcleo: a base do jogador. Tudo que entra (esteira nas 4 bocas ou braço) vira estoque para construir.')
    p = m.parte(); placa(p, 3, 3, h=0.16)
    v = p.caixa(-1.15, 1.15, -1.15, 1.15, 0.16, 0.62, 'P_Escuro'); p.chanfrar(v, 0.05)
    p.caixa(-1.17, 1.17, -1.17, 1.17, 0.62, 0.70, 'P_Faixa')
    v = p.caixa(-0.80, 0.80, -0.80, 0.80, 0.70, 1.30, 'P_Metal'); p.chanfrar(v, 0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cil((sx*0.95, sy*0.95, 1.00), 0.14, 0.80, 'P_Concreto', lados=8)
            p.cil((sx*0.95, sy*0.95, 1.45), 0.08, 0.12, 'P_Cristal', lados=6)
    cr = m.parte('cristal', pai='corpo', pivo=(0, 0, 1.30))          # pulsa (Animador)
    cr.cil((0, 0, 1.75), 0.42, 0.90, 'P_Cristal', lados=6, r2=0.0)
    cr.cil((0, 0, 1.40), 0.46, 0.20, 'P_Cristal', lados=6, r2=0.42)
    for lado in 'SNLO':
        boca(p, m, lado, 1, 'ENT')
    return m

# ---------------------------------------------------------------- energia
def gerador():
    m = Modelo('gerador', EN, 2, 2, descricao='Gerador a combustão (carvão/biomassa). Combustível entra pelo sul. Energia vai por postes.')
    p = m.parte(); placa(p, 2, 2)
    v = p.caixa(-0.80, 0.80, -0.55, 0.80, 0.12, 0.50, 'P_Escuro'); p.chanfrar(v, 0.04)
    p.cil((0, 0.15, 0.95), 0.55, 1.40, 'P_Metal', eixo='X', lados=10)
    for x in (-0.55, 0.0, 0.55): p.cil((x, 0.15, 0.95), 0.58, 0.08, 'P_Cobre', eixo='X', lados=10)
    p.cil((-0.45, 0.55, 1.80), 0.14, 0.70, 'P_Escuro', lados=8)
    p.cil((0.45, 0.55, 1.65), 0.10, 0.40, 'P_Faixa', lados=6)
    p.cil((0.45, 0.55, 1.90), 0.06, 0.10, 'P_Cristal', lados=6)
    boca(p, m, 'S', 1, 'ENT')
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

TODOS = [nucleo, extrator_cristal, broca_minerio, fornalha, montadora, refinador, laboratorio,
         gerador, poste_energia, torre_sem_fio, tanque, torre_defesa, muro_centro, muro_lado]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'maquinas', '_relatorio_maquinas.json'))
