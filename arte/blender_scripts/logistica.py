"""Logística: esteiras (chão e elevadas), rampa, pilares de canto, divisor, junção, braços, baú, canos e bomba.
Uso: blender --background --python logistica.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import (Modelo, rodar, esteira_trecho, cano_trecho, reto, curva_canto, girar_cam,
                    LONA, TRILHO, FRISO, CANO_Z, CANO_R, FLANGE_R, CANTO, NIVEL, RAMPA_SOBE)
from mathutils import Vector

E, C, B, P = 'logistica/esteira', 'logistica/canos', 'logistica/bracos', 'logistica/armazenagem'
PI = math.pi

# ---------------------------------------------------------------- esteiras (fluxo entra pelo sul)
def esteira_reta():
    m = Modelo('esteira_reta', E, descricao='Esteira reta. Também serve elevada, apoiada em pilares de canto.')
    esteira_trecho(m.parte(), reto((0, -0.5, 0), (0, 0.5, 0)))
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); m.porta('ITEM', 'SAI', 'N', perfil='esteira'); return m

def esteira_curva_dir():
    m = Modelo('esteira_curva_dir', E, descricao='Entra pelo sul e vira à direita (sai a leste).')
    esteira_trecho(m.parte(), curva_canto((0.5, -0.5, 0), 0.5, PI, PI/2))
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); m.porta('ITEM', 'SAI', 'L', perfil='esteira'); return m

def esteira_curva_esq():
    m = Modelo('esteira_curva_esq', E, descricao='Entra pelo sul e vira à esquerda (sai a oeste).')
    esteira_trecho(m.parte(), curva_canto((-0.5, -0.5, 0), 0.5, 0, PI/2))
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); m.porta('ITEM', 'SAI', 'O', perfil='esteira'); return m

def esteira_inicio():
    m = Modelo('esteira_inicio', E, descricao='Cabeceira com motor no sul. Recebe itens por braço ou pela lateral.')
    p = m.parte(); esteira_trecho(p, reto((0, -0.36, 0), (0, 0.5, 0)))
    for s in (-1, 1):  # fecha as pontas do lado da cabeceira
        pass
    p.caixa(-0.46, 0.46, -0.46, -0.36, 0.0, 0.26, 'P_Escuro'); p.caixa(-0.46, 0.46, -0.46, -0.36, 0.26, 0.285, 'P_Faixa')
    p.caixa(0.16, 0.40, -0.45, -0.37, 0.285, 0.38, 'P_Cobre')
    p.cil((0, -0.36, 0.13), 0.035, 0.80, 'P_Metal', eixo='X')
    m.porta('ITEM', 'SAI', 'N', perfil='esteira'); return m

def esteira_fim():
    m = Modelo('esteira_fim', E, descricao='Para-choque no norte. Itens param aqui para braços pegarem.')
    p = m.parte(); esteira_trecho(p, reto((0, -0.5, 0), (0, 0.38, 0)))
    p.caixa(-0.46, 0.46, 0.38, 0.46, 0.0, 0.24, 'P_Escuro'); p.caixa(-0.40, 0.40, 0.36, 0.38, 0.16, 0.24, 'P_Faixa')
    p.cil((0, 0.38, 0.13), 0.035, 0.80, 'P_Metal', eixo='X')
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); return m

def esteira_rampa():
    m = Modelo('esteira_rampa', E, descricao=f'Sobe {RAMPA_SOBE} m em 1 tile (~26,6°, abaixo do ângulo de escorregar). '
                                             'Girada 180° vira descida. Apoio por pilares de canto.')
    p = m.parte(); esteira_trecho(p, reto((0, -0.5, 0), (0, 0.5, RAMPA_SOBE)))
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); m.porta('ITEM', 'SAI', 'N', z=0.16 + RAMPA_SOBE, perfil='esteira'); return m

def _cubo_distribuidor(nome, desc, cor_topo, entradas, saidas):
    m = Modelo(nome, E, descricao=desc); p = m.parte()
    p.caixa(-0.40, 0.40, -0.40, 0.40, 0.10, 0.16, 'P_Esteira')                    # lona central
    p.caixa(-0.44, 0.44, -0.44, 0.44, 0.0, 0.10, 'P_Metal')                       # chassi
    for ang in (0, PI/2, PI, -PI/2):
        cam = girar_cam(reto((0, 0.40, 0), (0, 0.5, 0)), ang)
        p.varrer(cam, LONA, 'P_Esteira', uv=True)
        for s in (-1, 1):
            p.varrer(cam, (s*TRILHO[0], s*TRILHO[1], TRILHO[2], TRILHO[3]), 'P_Escuro')
            p.varrer(cam, (s*FRISO[0], s*FRISO[1], FRISO[2], FRISO[3]), 'P_Faixa')
    for x in (-0.40, 0.40):                                                       # pórtico
        for y in (-0.40, 0.40): p.caixa_c(x, y, 0.16, 0.06, 0.06, 0.32, 'P_Escuro')
    p.caixa(-0.43, 0.43, -0.43, 0.43, 0.48, 0.53, cor_topo)
    p.caixa(-0.30, 0.30, -0.30, 0.30, 0.53, 0.55, 'P_Escuro')
    p.cil((0, 0, 0.58), 0.06, 0.06, 'P_Cristal', lados=6)
    for l in entradas: m.porta('ITEM', 'ENT', l, perfil='esteira')
    for l in saidas: m.porta('ITEM', 'SAI', l, perfil='esteira')
    return m

def divisor():
    return _cubo_distribuidor('divisor', 'Entra pelo sul e reparte em até 3 saídas (norte, leste, oeste). Filtro opcional.',
                              'P_Faixa', 'S', 'NLO')
def juncao():
    return _cubo_distribuidor('juncao', 'Junta até 3 entradas (sul, leste, oeste) numa saída ao norte.',
                              'P_Cobre', 'SLO', 'N')

# ---------------------------------------------------------------- pilares de canto (esteira elevada)
def pilar_segmento():
    m = Modelo('pilar_segmento', E, tipo='canto', descricao=f'Fuste de {NIVEL} m. Fica no canto da grade (vértice entre 4 tiles).')
    m.parte().caixa(-CANTO, CANTO, -CANTO, CANTO, 0, NIVEL, 'P_Metal'); return m

def pilar_topo():
    m = Modelo('pilar_topo', E, tipo='canto', descricao=f'Último {NIVEL} m do pilar, com mesa que apoia a esteira elevada. '
                                                       'Altura do pilar = nível da esteira (n segmentos + topo).')
    m.topo_livre = NIVEL - 0.03; p = m.parte()
    p.caixa(-CANTO, CANTO, -CANTO, CANTO, 0, NIVEL - 0.03, 'P_Metal')
    p.caixa(-0.15, 0.15, -0.15, 0.15, NIVEL - 0.03, NIVEL, 'P_Escuro')
    return m

def pilar_base():
    m = Modelo('pilar_base', E, tipo='canto', descricao='Sapata do pilar (vai por baixo do primeiro segmento, sem altura extra).')
    p = m.parte(); p.caixa(-CANTO, CANTO, -CANTO, CANTO, 0, 0.04, 'P_Faixa'); return m

# ---------------------------------------------------------------- braços (pega do sul, solta ao norte)
def _braco(nome, desc, l1, l2, cor, cristal=False):
    m = Modelo(nome, B, descricao=desc)
    base = m.parte('base')
    base.cil((0, 0, 0.04), 0.30, 0.08, 'P_Escuro', lados=8, rot=PI/8)
    base.cil((0, 0, 0.15), 0.13, 0.14, 'P_Metal', lados=8)
    giro = m.parte('giro', pai='base', pivo=(0, 0, 0.22))
    giro.caixa_c(0, 0, 0.22, 0.24, 0.24, 0.10, cor)
    giro.cil((0, 0, 0.36), 0.06, 0.16, 'P_Escuro', eixo='X')
    sh = Vector((0, 0, 0.36))
    el = sh + Vector((0, 0.10, l1))                                    # repouso: braço 1 quase em pé
    wr = el + Vector((0, l2*0.80, -l2*0.60))                           # braço 2 descendo para a frente
    b1 = m.parte('braco1', pai='giro', pivo=tuple(sh))
    b1.barra(sh, el, 0.07, 0.07, 'P_Metal'); b1.cil(tuple(el), 0.05, 0.12, 'P_Escuro', eixo='X')
    b2 = m.parte('braco2', pai='braco1', pivo=tuple(el))
    b2.barra(el, wr, 0.06, 0.06, cor)
    g = m.parte('garra', pai='braco2', pivo=tuple(wr))
    g.caixa_c(wr.x, wr.y, wr.z - 0.05, 0.12, 0.08, 0.05, 'P_Escuro')
    for x in (-0.045, 0.045): g.caixa_c(wr.x + x, wr.y, wr.z - 0.12, 0.025, 0.05, 0.07, 'P_Metal')
    if cristal: g.cil((wr.x, wr.y, wr.z + 0.02), 0.03, 0.04, 'P_Cristal', lados=6)
    m.porta('ITEM', 'ENT', 'S'); m.porta('ITEM', 'SAI', 'N')
    return m

def braco():        return _braco('braco', 'Braço mecânico: pega do tile ao sul e solta no tile ao norte. Alcance 1 tile.', 0.30, 0.30, 'P_Faixa')
def braco_longo():  return _braco('braco_longo', 'Braço longo: alcance 2 tiles (pula um tile). Em repouso fica dentro do próprio tile.',
                                  0.38, 0.40, 'P_Cobre')
def braco_rapido(): return _braco('braco_rapido', 'Braço rápido: alcance 1 tile, 2× mais rápido, consome mais energia.',
                                  0.30, 0.30, 'P_Metal', cristal=True)

# ---------------------------------------------------------------- armazenagem
def bau():
    m = Modelo('bau', P, descricao='Baú 1×1. Braços colocam e tiram por qualquer lado.'); p = m.parte()
    v = p.caixa(-0.40, 0.40, -0.36, 0.36, 0.0, 0.50, 'P_Metal'); p.chanfrar(v, 0.03)
    v = p.caixa(-0.42, 0.42, -0.38, 0.38, 0.50, 0.62, 'P_Escuro'); p.chanfrar(v, 0.03)
    for x in (-0.25, 0.25): p.caixa(x - 0.04, x + 0.04, -0.385, 0.385, 0.06, 0.60, 'P_Faixa')
    p.caixa(-0.07, 0.07, -0.395, -0.38, 0.38, 0.52, 'P_Cobre')
    return m

# ---------------------------------------------------------------- canos (fluido; flange de junção nas bordas)
def _pe(p, x=0, y=0):
    p.caixa_c(x, y, 0, 0.14, 0.14, CANO_Z - CANO_R + 0.01, 'P_Escuro')

def cano_reto():
    m = Modelo('cano_reto', C, descricao='Cano reto (norte–sul).'); p = m.parte()
    cano_trecho(p, reto((0, -0.5, 0), (0, 0.5, 0))); _pe(p)
    m.porta('FLUIDO', 'ENT', 'S', perfil='cano'); m.porta('FLUIDO', 'SAI', 'N', perfil='cano'); return m

def cano_curva():
    m = Modelo('cano_curva', C, descricao='Cano em curva (sul–leste), uma malha só.'); p = m.parte()
    cam = curva_canto((0.5, -0.5, 0), 0.5, PI, PI/2); cano_trecho(p, cam)
    c = cam[len(cam)//2][0]; _pe(p, c.x, c.y)
    m.porta('FLUIDO', 'ENT', 'S', perfil='cano'); m.porta('FLUIDO', 'SAI', 'L', perfil='cano'); return m

def _cano_hub(nome, desc, lados):
    m = Modelo(nome, C, descricao=desc); p = m.parte()
    v = p.caixa_c(0, 0, CANO_Z - 0.17, 0.34, 0.34, 0.34, 'P_Metal'); p.chanfrar(v, 0.04)
    ang = dict(N=0, O=PI/2, S=PI, L=-PI/2)
    for l in lados:
        cano_trecho(p, girar_cam(reto((0, 0.17, 0), (0, 0.5, 0)), ang[l]), flange_ini=False)
        m.porta('FLUIDO', 'SAI', l, perfil='cano')
    _pe(p); return m

def cano_t():    return _cano_hub('cano_t', 'Cano em T (sul, norte, leste).', 'SNL')
def cano_cruz(): return _cano_hub('cano_cruz', 'Cano em cruz (4 lados).', 'SNLO')

def bomba():
    m = Modelo('bomba', C, descricao='Bomba sobre poça de seiva/água: empurra fluido pela saída ao norte.'); p = m.parte()
    v = p.caixa(-0.38, 0.38, -0.38, 0.22, 0.0, 0.12, 'P_Concreto'); p.chanfrar(v, 0.02)
    v = p.caixa(-0.28, 0.28, -0.30, 0.16, 0.12, 0.58, 'P_Metal'); p.chanfrar(v, 0.03)
    c = m.parte('cabecote', pai='corpo', pivo=(0, -0.07, 0.58))        # sobe e desce (bombeando)
    c.cil((0, -0.07, 0.68), 0.16, 0.20, 'P_Escuro', lados=8)
    c.cil((0, -0.07, 0.80), 0.08, 0.04, 'P_Faixa', lados=8)
    p.caixa(-0.29, 0.29, -0.31, 0.17, 0.30, 0.36, 'P_Faixa')
    cano_trecho(p, reto((0, 0.16, 0), (0, 0.5, 0)), flange_ini=False)
    m.porta('FLUIDO', 'SAI', 'N', perfil='cano'); return m

TODOS = [esteira_reta, esteira_curva_dir, esteira_curva_esq, esteira_inicio, esteira_fim, esteira_rampa,
         divisor, juncao, pilar_base, pilar_segmento, pilar_topo,
         braco, braco_longo, braco_rapido, bau,
         cano_reto, cano_curva, cano_t, cano_cruz, bomba]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'logistica', '_relatorio_logistica.json'))
