"""Logística: esteiras (chão e elevadas), rampa, pilares de canto, divisor, junção, braços, baú, canos e bomba.
Uso: blender --background --python logistica.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import (terminal, Modelo, rodar, esteira_trecho, cano_trecho, reto, curva_canto, girar_cam,
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

def esteira_juncao():
    m = Modelo('esteira_juncao', E, descricao='Rampa de junção: ponta de esteira que entrega na lateral de outra. Uma calha '
               'passa por cima do trilho vizinho e deita o item na outra esteira (0,25 m além da borda norte).')
    m.alem_norte = 0.26                               # a calha avança sobre a esteira vizinha (só visual, sem ocupar)
    p = m.parte(); esteira_trecho(p, reto((0, -0.5, 0), (0, 0.5, 0)))
    # calha: sobe do fim da lona por cima do trilho da vizinha e desce até a lona dela (uma varredura só)
    cam = [(Vector((0, 0.42, 0.13)), Vector((0, 1, 0))), (Vector((0, 0.57, 0.215)), Vector((0, 1, 0))),
           (Vector((0, 0.75, 0.14)), Vector((0, 1, 0)))]
    p.varrer(cam, (-0.25, 0.25, 0.0, 0.03), 'P_Metal', tampa=(True, True))
    for lado in ((0.25, 0.29), (-0.29, -0.25)):       # abas laterais que guiam o item
        p.varrer(cam, (lado[0], lado[1], 0.0, 0.10), 'P_Escuro', tampa=(True, True))
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); m.porta('ITEM', 'SAI', 'N', perfil='esteira'); return m

def _portal(p, y0, y1, frente):
    """Pórtico da passagem subterrânea: bloco blindado com a boca escura virada para `frente` (y da face)."""
    v = p.caixa(-0.45, 0.45, y0, y1, 0.0, 0.10, 'P_Escuro'); p.chanfrar(v, 0.02)
    lado_boca = 1 if frente < (y0 + y1)/2 else -1      # +1: boca na face sul do bloco
    yb0, yb1 = (frente, frente + 0.10) if lado_boca == 1 else (frente - 0.10, frente)
    yf0, yf1 = (yb1, y1) if lado_boca == 1 else (y0, yb0)
    v = p.caixa(-0.45, 0.45, yf0, yf1, 0.10, 0.46, 'P_Escuro'); p.chanfrar(v, 0.03)      # fundo
    for x0, x1 in ((-0.45, -0.30), (0.30, 0.45)):                                         # batentes
        v = p.caixa(x0, x1, yb0, yb1, 0.10, 0.46, 'P_Aco'); p.chanfrar(v, 0.015)
    v = p.caixa(-0.30, 0.30, yb0, yb1, 0.32, 0.46, 'P_Aco'); p.chanfrar(v, 0.015)        # verga
    yl = (frente - 0.012, frente) if lado_boca == 1 else (frente, frente + 0.012)
    p.caixa(-0.26, 0.26, yl[0], yl[1], 0.36, 0.40, 'P_Cristal')                            # luz da boca
    p.caixa(-0.38, 0.38, yf0 + 0.06, yf1 - 0.06, 0.46, 0.475, 'P_Cristal')                # veio no topo
    p.caixa(-0.30, 0.30, yb0, yb1, 0.10, 0.13, 'P_Escuro')                                  # piso da boca

def esteira_tunel_entrada():
    m = Modelo('esteira_tunel_entrada', E, descricao='Passagem subterrânea (entrada): a esteira mergulha no pórtico e o '
               'item segue por baixo até a saída alinhada à frente (até 4 tiles livres no meio).')
    p = m.parte(); esteira_trecho(p, reto((0, -0.5, 0), (0, -0.02, 0)), travessa=False)
    _portal(p, -0.02, 0.46, -0.02)
    m.porta('ITEM', 'ENT', 'S', perfil='esteira'); return m

def esteira_tunel_saida():
    m = Modelo('esteira_tunel_saida', E, descricao='Passagem subterrânea (saída): o item volta à superfície e segue para o norte.')
    p = m.parte(); esteira_trecho(p, reto((0, 0.02, 0), (0, 0.5, 0)), travessa=False)
    _portal(p, -0.46, 0.02, 0.02)
    m.porta('ITEM', 'SAI', 'N', perfil='esteira'); return m

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
        cam_t = girar_cam(reto((0, 0.46, 0), (0, 0.5, 0)), ang)   # trilhos começam depois do canto (não cruzam o vizinho)
        for s in (-1, 1):
            p.varrer(cam_t, (s*TRILHO[0], s*TRILHO[1], TRILHO[2], TRILHO[3]), 'P_Escuro')
            p.varrer(cam_t, (s*FRISO[0], s*FRISO[1], FRISO[2], FRISO[3]), 'P_Faixa')
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
    terminal(m, base, 0.33, -0.33, 0.0, baixo=True)
    giro = m.parte('giro', pai='base', pivo=(0, 0, 0.22))
    giro.caixa_c(0, 0, 0.22, 0.24, 0.24, 0.10, cor)
    giro.cil((0, 0, 0.36), 0.06, 0.16, 'P_Escuro', eixo='X')
    sh = Vector((0, 0, 0.36))
    el = sh + Vector((0, 0.10, l1))                                    # repouso: braço 1 quase em pé
    wr = el + Vector((0, l2*0.30, -l2*0.95))                           # braço 2 pendendo (o jogo posa por IK)
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

# braços com comprimento de verdade: a garra alcança o centro do tile vizinho (ou o segundo, no longo)
def braco():        return _braco('braco', 'Braço mecânico: pega do tile ao sul e solta no tile ao norte. Alcance 1 tile.', 0.55, 0.62, 'P_Faixa')
def braco_longo():  return _braco('braco_longo', 'Braço longo: alcance 2 tiles (pula um tile). Em repouso fica dentro do próprio tile.',
                                  1.05, 1.12, 'P_Cobre')
def braco_rapido(): return _braco('braco_rapido', 'Braço rápido: alcance 1 tile, 2× mais rápido, consome mais energia.',
                                  0.55, 0.62, 'P_Metal', cristal=True)

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
    m = Modelo('bomba', C, descricao='bomba: corpo octogonal sobre a poça, êmbolo com anel de luz que sobe e desce; '
               'empurra fluido pela saída ao norte.'); p = m.parte()
    v = p.caixa(-0.38, 0.38, -0.38, 0.22, 0.0, 0.10, 'P_Escuro'); p.chanfrar(v, 0.03)
    p.caixa(-0.20, 0.20, -0.33, -0.31, 0.10, 0.112, 'P_Cristal')
    v = p.cil((0, -0.08, 0.34), 0.26, 0.48, 'P_Aco', lados=8, rot=PI/8, r2=0.21); p.chanfrar(v, 0.02)
    p.cil((0, -0.08, 0.40), 0.245, 0.03, 'P_Cristal', lados=8, rot=PI/8)
    c = m.parte('cabecote', pai='corpo', pivo=(0, -0.08, 0.58))        # êmbolo (sobe e desce, bombeando)
    c.cil((0, -0.08, 0.68), 0.15, 0.20, 'P_Escuro', lados=8, rot=PI/8)
    c.cil((0, -0.08, 0.80), 0.10, 0.04, 'P_Cristal', lados=8, rot=PI/8)
    terminal(m, p, 0.30, -0.30, 0.10, baixo=True)
    cano_trecho(p, reto((0, 0.16, 0), (0, 0.5, 0)), flange_ini=False)
    m.porta('FLUIDO', 'SAI', 'N', perfil='cano'); return m

TODOS = [esteira_reta, esteira_curva_dir, esteira_curva_esq, esteira_inicio, esteira_fim, esteira_rampa,
         esteira_juncao, esteira_tunel_entrada, esteira_tunel_saida,
         divisor, juncao, pilar_base, pilar_segmento, pilar_topo,
         braco, braco_longo, braco_rapido, bau,
         cano_reto, cano_curva, cano_t, cano_cruz, bomba]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'logistica', '_relatorio_logistica.json'))
