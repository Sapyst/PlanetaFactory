"""Estudo ambiental (Parte A — Grupo 1): ÁRVORES (6 espécies × 6 variantes = 36 modelos, limite rígido: 500 tris).
Espécies:
- arv_acacia_1..6        (Acácia-seca: deserto de sílex / cinzal; copa em patamares tabulares espinhosos, P_FolhaSeca)
- arv_betula_1..6        (Bétula-prata: campina; tronco claro fendado com musgo no pé, copa colunar/oval, P_FolhaBetula)
- arv_carvalho_1..6      (Carvalho-de-campina: campina; tronco nodoso com sapopembas e galhos aparentes, P_FolhaCaduca)
- arv_pinheiro_1..6      (Pinheiro: planalto rochoso / floresta fúngica; saias cônicas recortadas em pontas, P_FolhaPerene)
- arv_salgueiro_1..6     (Salgueiro-do-pântano: pântano; raízes aéreas, galhos arqueados e cortinas pendentes, P_FolhaSalgueiro)
- arv_fungo_cristal_1..6 (Fungo-cristal: floresta fúngica / campo de cristal; estipe fibrosa, chapéu com lamelas e drusas P_Cristal)

Regras cumpridas:
- Uma malha só por modelo, sem peças móveis, sem armadura e sem animação (quem mexe é o shader material_pf).
- Volumes fechados com espessura e faces para fora; sem transparência (folhas recortadas na malha).
- Origem na base central (z=0), tronco embaixo e copa conectada por galhos em cima, cabendo em 1×1 tile.
- Cada uma das 6 variantes tem arquitetura de tronco, galhos e copa própria (não é a mesma árvore girada).

Uso:
  blender -b --python estudo_amb_arvores.py -- foto
  blender -b --python estudo_amb_arvores.py -- nada [nome_modelo]
"""
import os, sys, math, random
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import amb_comum as amb
from amb_comum import ConstrutorMalha, PI, Z


def _raizes_base(cm, n_raizes, r_tronco, alcance, alt_raiz, mat, rnd, fase0=0.0):
    """Adiciona raízes tabulares/garras cravadas no chão (z=0) saindo da base do tronco."""
    for i in range(n_raizes):
        a = fase0 + 2 * PI * i / n_raizes + rnd.uniform(-0.25, 0.25)
        dx, dy = math.cos(a), math.sin(a)
        p0 = Vector((dx * r_tronco * 0.55, dy * r_tronco * 0.55, alt_raiz))
        p1 = Vector((dx * alcance * 0.65, dy * alcance * 0.65, alt_raiz * 0.38))
        p2 = Vector((dx * alcance, dy * alcance, 0.0))
        cm.ramo([p0, p1, p2], [r_tronco * 0.48, r_tronco * 0.30, r_tronco * 0.12],
                mat, lados=4, fechar_base=False, fechar_topo=True, fase0=a)


# ================================================================== 1. ACÁCIA-SECA (arv_acacia_1..6)
def construir_acacia(n, pos=(0, 0, 0)):
    nome = f'arv_acacia_{n}'
    cm = ConstrutorMalha(nome)
    rnd = random.Random(1000 + n * 73)
    casca, folha = 'P_Tronco', 'P_FolhaSeca'

    alturas = [1.88, 1.62, 1.87, 1.67, 1.92, 1.65]
    h = alturas[n - 1]
    _raizes_base(cm, 3, 0.085, 0.22, 0.18, casca, rnd, fase0=n * 0.7)

    if n == 1:
        # Var 1: Tronco inclinado que abre em 3 patamares tabulares escalonados largos
        p_meio = Vector((0.05, -0.03, h * 0.44))
        cm.ramo([(0, 0, 0), (0.03, -0.02, h * 0.22), p_meio], [0.09, 0.070, 0.055], casca, lados=6, sapopemba=0.35, torcao=0.4)
        alvos = [
            (Vector((-0.24, 0.15, h * 0.72)), 0.36, 0.18),
            (Vector((0.25, -0.11, h * 0.84)), 0.38, 0.18),
            (Vector((-0.02, -0.04, h * 0.96)), 0.44, 0.20),
        ]
        for idx, (pt, rc, esp) in enumerate(alvos):
            cm.ramo([p_meio + Vector((0, 0, -0.04)), (p_meio + pt) * 0.5 + Vector((0, 0, -0.04)), pt],
                    [0.045, 0.032, 0.020], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, rc, esp, folha, lados=7, pontas=0.20, queda_borda=0.03, assimetria=(1.12, 0.95),
                           rot_z=idx * 1.1, semente=110 + idx)
    elif n == 2:
        # Var 2: Bifurcada baixa em dois troncos divergentes com duas copas tabulares amplas
        p_garfo = Vector((0.0, 0.0, h * 0.26))
        cm.ramo([(0, 0, 0), p_garfo], [0.095, 0.072], casca, lados=6, sapopemba=0.4)
        for idx, (pt, rc) in enumerate(((Vector((-0.24, -0.10, h * 0.82)), 0.39),
                                        (Vector((0.22, 0.12, h * 0.95)), 0.43))):
            meio = p_garfo.lerp(pt, 0.52) + Vector((0.04 * (1 if idx else -1), -0.03, -0.05))
            cm.ramo([p_garfo, meio, pt], [0.055, 0.040, 0.022], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.19, folha, lados=8, pontas=0.22, queda_borda=0.03, assimetria=(1.12, 0.96),
                           rot_z=idx * 0.9, semente=120 + idx)
        p3 = Vector((0.04, -0.22, h * 0.66))
        cm.ramo([p_garfo, p3], [0.038, 0.018], casca, lados=4, fechar_base=False)
        cm.fronde_copa(p3, 0.29, 0.16, folha, lados=6, pontas=0.18, queda_borda=0.025, semente=125)
    elif n == 3:
        # Var 3: Varrida pelo vento do deserto (tronco vergado para +X e dossel em cascata horizontal)
        p1 = Vector((-0.05, 0.0, h * 0.25))
        p2 = Vector((0.08, 0.02, h * 0.52))
        cm.ramo([(0, 0, 0), p1, p2], [0.092, 0.070, 0.052], casca, lados=6, sapopemba=0.45, torcao=0.5)
        for idx, (pt, rc) in enumerate(((Vector((0.25, 0.06, h * 0.78)), 0.36),
                                        (Vector((0.04, -0.15, h * 0.90)), 0.41),
                                        (Vector((-0.18, 0.10, h * 0.96)), 0.38))):
            cm.ramo([p2, pt], [0.042, 0.020], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.18, folha, lados=7, pontas=0.22, queda_borda=0.03, assimetria=(1.15, 0.92),
                           rot_z=0.3 * idx, semente=130 + idx)
    elif n == 4:
        # Var 4: Trifurcada em cálice largo com toco de galho seco quebrado
        p_garfo = Vector((-0.02, 0.02, h * 0.38))
        cm.ramo([(0, 0, 0), p_garfo], [0.090, 0.066], casca, lados=6, sapopemba=0.35)
        cm.ramo([p_garfo, Vector((0.26, 0.18, h * 0.56))], [0.038, 0.012], casca, lados=4, fechar_base=False)
        for idx in range(3):
            a = idx * 2 * PI / 3 + 0.4
            pt = Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, h * (0.78 + 0.08 * idx)))
            cm.ramo([p_garfo, pt], [0.044, 0.020], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, 0.36, 0.18, folha, lados=7, pontas=0.20, queda_borda=0.03, rot_z=a, semente=140 + idx)
    elif n == 5:
        # Var 5: Tronco alto nodoso com braço baixo horizontal estendido e grande guarda-chuva no topo
        p1 = Vector((0.02, -0.02, h * 0.34))
        p2 = Vector((-0.03, 0.03, h * 0.64))
        cm.ramo([(0, 0, 0), p1, p2], [0.095, 0.072, 0.054], casca, lados=6, sapopemba=0.40, torcao=-0.5)
        pb = Vector((0.26, -0.12, h * 0.56))
        cm.ramo([p1, pb], [0.042, 0.020], casca, lados=5, fechar_base=False)
        cm.fronde_copa(pb, 0.31, 0.16, folha, lados=6, pontas=0.20, queda_borda=0.025, semente=151)
        for idx, (pt, rc) in enumerate(((Vector((-0.18, 0.12, h * 0.90)), 0.39),
                                        (Vector((0.12, 0.02, h * 0.97)), 0.43))):
            cm.ramo([p2, pt], [0.044, 0.022], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.19, folha, lados=7, pontas=0.21, queda_borda=0.03, semente=152 + idx)
    else:
        # Var 6: Duplo garfo torcido com 4 discos folhosos em espiral
        p1 = Vector((-0.04, -0.02, h * 0.32))
        p2 = Vector((0.05, 0.04, h * 0.58))
        cm.ramo([(0, 0, 0), p1, p2], [0.088, 0.066, 0.048], casca, lados=6, sapopemba=0.38, torcao=0.6)
        pts_c = [
            (p1, Vector((-0.24, -0.10, h * 0.62)), 0.31),
            (p1, Vector((0.20, -0.16, h * 0.72)), 0.32),
            (p2, Vector((-0.14, 0.18, h * 0.86)), 0.36),
            (p2, Vector((0.14, 0.06, h * 0.96)), 0.39),
        ]
        for idx, (orig, pt, rc) in enumerate(pts_c):
            cm.ramo([orig, pt], [0.038, 0.018], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.17, folha, lados=6, pontas=0.22, queda_borda=0.03, semente=160 + idx)

    return cm.finalizar(pos=pos, raio_max_xy=0.56)


# ================================================================== 2. BÉTULA-PRATA (arv_betula_1..6)
def construir_betula(n, pos=(0, 0, 0)):
    nome = f'arv_betula_{n}'
    cm = ConstrutorMalha(nome)
    rnd = random.Random(2000 + n * 89)
    casca, folha = 'P_TroncoClaro', 'P_FolhaBetula'

    alturas = [2.56, 2.60, 2.32, 2.50, 2.56, 2.70]
    h = alturas[n - 1]
    _raizes_base(cm, 3, 0.062, 0.15, 0.14, casca, rnd, fase0=n * 0.9)

    if n == 1:
        # Var 1: Fuste único esbelto com 4 andares de copa colunar-ovalada farta
        cm.ramo([(0, 0, 0), (0.02, -0.01, h * 0.38), (-0.02, 0.02, h * 0.75), (0, 0, h * 0.92)],
                [0.060, 0.045, 0.030, 0.016], casca, lados=6, sapopemba=0.25)
        for idx, (zf, ang, dist, rc, ez) in enumerate((
            (0.46, 0.4, 0.12, 0.25, 0.38),
            (0.60, 2.5, 0.13, 0.27, 0.40),
            (0.74, 4.6, 0.11, 0.25, 0.40),
            (0.90, 1.2, 0.04, 0.22, 0.45),
        )):
            p0 = Vector((0, 0, h * (zf - 0.10)))
            pt = Vector((math.cos(ang) * dist, math.sin(ang) * dist, h * zf))
            cm.ramo([p0, pt], [0.026, 0.014], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt, rc, ez, folha, lados=6, pontas=0.24, queda_borda=0.07, semente=210 + idx)
    elif n == 2:
        # Var 2: Bétula gêmea (dois troncos nascendo juntos da base, um alto e um médio)
        cm.ramo([(0, 0, 0), (-0.05, -0.02, h * 0.45), (-0.08, -0.03, h * 0.90)],
                [0.056, 0.038, 0.016], casca, lados=5, sapopemba=0.30)
        cm.ramo([(0.02, 0.01, 0.05), (0.08, 0.04, h * 0.38), (0.12, 0.05, h * 0.72)],
                [0.046, 0.032, 0.015], casca, lados=5, fechar_base=False)
        copas = [
            (Vector((-0.09, -0.04, h * 0.58)), 0.24, 0.38),
            (Vector((-0.08, -0.03, h * 0.88)), 0.23, 0.42),
            (Vector((0.12, 0.05, h * 0.50)), 0.22, 0.36),
            (Vector((0.12, 0.05, h * 0.74)), 0.23, 0.38),
        ]
        for idx, (pt, rc, ez) in enumerate(copas):
            cm.fronde_copa(pt, rc, ez, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=220 + idx)
    elif n == 3:
        # Var 3: Fuste sinuoso em S com galho baixo seco e coroa nos dois terços superiores
        p1 = Vector((0.04, 0.02, h * 0.32))
        p2 = Vector((-0.04, -0.02, h * 0.65))
        p3 = Vector((0.01, 0.02, h * 0.91))
        cm.ramo([(0, 0, 0), p1, p2, p3], [0.058, 0.044, 0.030, 0.015], casca, lados=6, sapopemba=0.28)
        cm.ramo([p1, Vector((0.15, 0.08, h * 0.42))], [0.024, 0.010], casca, lados=4, fechar_base=False)
        for idx, (orig, pt, rc, ez) in enumerate((
            (p1, Vector((-0.11, 0.06, h * 0.52)), 0.24, 0.38),
            (p2, Vector((0.10, -0.07, h * 0.68)), 0.26, 0.40),
            (p2, Vector((-0.09, -0.05, h * 0.80)), 0.24, 0.38),
            (p3, Vector((0.01, 0.02, h * 0.92)), 0.22, 0.42),
        )):
            cm.ramo([orig, pt], [0.025, 0.012], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt, rc, ez, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=230 + idx)
    elif n == 4:
        # Var 4: Candelabro trifurcado a meia altura
        pg = Vector((0, 0, h * 0.36))
        cm.ramo([(0, 0, 0), pg], [0.062, 0.046], casca, lados=6, sapopemba=0.26)
        for idx in range(3):
            a = idx * 2 * PI / 3 + 0.25
            zf = 0.78 + 0.07 * idx
            pm = Vector((math.cos(a) * 0.09, math.sin(a) * 0.09, h * 0.58))
            pt = Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, h * zf))
            cm.ramo([pg, pm, pt], [0.034, 0.024, 0.014], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pm + Vector((0, 0, 0.06)), 0.21, 0.34, folha, lados=5, pontas=0.20, queda_borda=0.05, semente=240 + idx)
            cm.fronde_copa(pt, 0.22, 0.38, folha, lados=5, pontas=0.22, queda_borda=0.06, semente=245 + idx)
    elif n == 5:
        # Var 5: Tronco principal alto + broto jovem lateral na base
        cm.ramo([(0, 0, 0), (-0.02, 0.02, h * 0.48), (-0.03, 0.03, h * 0.90)],
                [0.058, 0.040, 0.016], casca, lados=6, sapopemba=0.28)
        pb = Vector((0.12, -0.07, h * 0.44))
        cm.ramo([(0.02, -0.01, 0.04), pb], [0.034, 0.015], casca, lados=4, fechar_base=False)
        cm.fronde_copa(pb, 0.21, 0.34, folha, lados=5, pontas=0.20, queda_borda=0.05, semente=251)
        for idx, (zf, ox, oy, rc) in enumerate(((0.58, -0.10, 0.05, 0.25), (0.74, 0.06, 0.08, 0.25), (0.90, -0.02, 0.02, 0.22))):
            pt = Vector((ox, oy, h * zf))
            cm.ramo([Vector((-0.02, 0.02, h * (zf - 0.12))), pt], [0.026, 0.012], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.40, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=252 + idx)
    else:
        # Var 6: Porte alto (2.70 m) com bifurcação superior assimétrica e janelas no tronco
        p_div = Vector((0.01, -0.01, h * 0.54))
        cm.ramo([(0, 0, 0), (0.01, 0.0, h * 0.28), p_div], [0.062, 0.048, 0.038], casca, lados=6, sapopemba=0.30)
        p_esq = Vector((-0.09, 0.05, h * 0.92))
        p_dir = Vector((0.10, -0.06, h * 0.80))
        cm.ramo([p_div, p_esq], [0.030, 0.014], casca, lados=5, fechar_base=False)
        cm.ramo([p_div, p_dir], [0.028, 0.014], casca, lados=5, fechar_base=False)
        for idx, (pt, rc, ez) in enumerate((
            (Vector((0.07, 0.06, h * 0.44)), 0.23, 0.34),
            (p_dir, 0.24, 0.38),
            (Vector((-0.07, 0.04, h * 0.72)), 0.24, 0.38),
            (p_esq, 0.23, 0.42),
        )):
            if idx == 0:
                cm.ramo([Vector((0, 0, h * 0.34)), pt], [0.024, 0.012], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt, rc, ez, folha, lados=6, pontas=0.23, queda_borda=0.06, semente=260 + idx)

    return cm.finalizar(pos=pos, raio_max_xy=0.38)


# ================================================================== 3. CARVALHO-DE-CAMPINA (arv_carvalho_1..6)
def construir_carvalho(n, pos=(0, 0, 0)):
    nome = f'arv_carvalho_{n}'
    cm = ConstrutorMalha(nome)
    rnd = random.Random(3000 + n * 103)
    casca, folha = 'P_Tronco', 'P_FolhaCaduca'

    alturas = [1.92, 2.06, 1.94, 2.00, 1.88, 2.19]
    h = alturas[n - 1]
    _raizes_base(cm, 4, 0.115, 0.25, 0.22, casca, rnd, fase0=n * 0.5)

    if n == 1:
        # Var 1: Patriarca robusto — tronco central grosso com 4 braços abertos e cúpula densa
        pg = Vector((0.0, 0.0, h * 0.46))
        cm.ramo([(0, 0, 0), (0.02, -0.01, h * 0.24), pg], [0.115, 0.090, 0.075], casca, lados=6, sapopemba=0.45, torcao=0.35)
        for idx in range(4):
            a = idx * PI / 2 + 0.35
            pt = Vector((math.cos(a) * 0.23, math.sin(a) * 0.23, h * (0.68 + 0.03 * (idx % 2))))
            cm.ramo([pg, pt], [0.052, 0.028], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt + Vector((0, 0, 0.05)), 0.33, 0.34, folha, lados=6, pontas=0.22, queda_borda=0.06,
                           rot_z=a, semente=310 + idx)
        cm.fronde_copa((0, 0, h * 0.88), 0.38, 0.38, folha, lados=7, pontas=0.20, queda_borda=0.06, semente=319)
    elif n == 2:
        # Var 2: Tronco baixo dividido em 2 grandes troncos secundários retorcidos
        pg = Vector((0.0, 0.0, h * 0.30))
        cm.ramo([(0, 0, 0), pg], [0.12, 0.092], casca, lados=6, sapopemba=0.45)
        for idx, sgn in enumerate((-1, 1)):
            p_m = Vector((sgn * 0.16, sgn * 0.05, h * 0.56))
            p_t = Vector((sgn * 0.20, -sgn * 0.06, h * (0.78 + 0.06 * idx)))
            cm.ramo([pg, p_m, p_t], [0.065, 0.048, 0.026], casca, lados=5, fechar_base=False)
            cm.fronde_copa(p_m + Vector((0, sgn * 0.08, 0.08)), 0.32, 0.32, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=320 + idx)
            cm.fronde_copa(p_t + Vector((0, 0, 0.06)), 0.35, 0.36, folha, lados=7, pontas=0.22, queda_borda=0.06, semente=324 + idx)
        cm.fronde_copa((0.0, 0.04, h * 0.90), 0.34, 0.34, folha, lados=6, pontas=0.20, queda_borda=0.05, semente=329)
    elif n == 3:
        # Var 3: Carvalho inclinado com galho lateral baixo pesado e copa em 3 patamares
        p1 = Vector((0.04, -0.02, h * 0.32))
        p2 = Vector((-0.05, 0.04, h * 0.62))
        cm.ramo([(0, 0, 0), p1, p2], [0.115, 0.086, 0.062], casca, lados=6, sapopemba=0.42, torcao=-0.4)
        pb = Vector((0.25, -0.10, h * 0.54))
        cm.ramo([p1, pb], [0.052, 0.026], casca, lados=5, fechar_base=False)
        cm.fronde_copa(pb + Vector((0, 0, 0.04)), 0.32, 0.31, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=331)
        for idx, (pt, rc) in enumerate((
            (Vector((-0.20, -0.10, h * 0.72)), 0.33),
            (Vector((0.10, 0.18, h * 0.78)), 0.34),
            (Vector((-0.04, 0.02, h * 0.90)), 0.37),
        )):
            cm.ramo([p2, pt], [0.046, 0.024], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.34, folha, lados=6, pontas=0.21, queda_borda=0.06, semente=332 + idx)
    elif n == 4:
        # Var 4: 5 galhos radiais assimétricos e coroa larga
        pg = Vector((0.0, 0.0, h * 0.44))
        cm.ramo([(0, 0, 0), pg], [0.12, 0.085], casca, lados=6, sapopemba=0.48)
        for idx in range(5):
            a = idx * 2 * PI / 5 + 0.2
            pt = Vector((math.cos(a) * 0.23, math.sin(a) * 0.23, h * (0.66 + 0.05 * (idx % 3))))
            cm.ramo([pg, pt], [0.048, 0.024], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt + Vector((0, 0, 0.05)), 0.32, 0.33, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=340 + idx)
        cm.fronde_copa((0, 0, h * 0.89), 0.36, 0.34, folha, lados=6, pontas=0.20, semente=349)
    elif n == 5:
        # Var 5: Fuste torcido com galho seco descascado de um lado e copa assimétrica densa
        pg = Vector((-0.03, 0.02, h * 0.42))
        cm.ramo([(0, 0, 0), pg], [0.115, 0.082], casca, lados=6, sapopemba=0.45, torcao=0.5)
        cm.ramo([pg, Vector((0.26, 0.16, h * 0.62)), Vector((0.32, 0.20, h * 0.72))],
                [0.045, 0.026, 0.012], casca, lados=4, fechar_base=False)
        for idx, (pt, rc) in enumerate((
            (Vector((-0.22, 0.10, h * 0.68)), 0.34),
            (Vector((-0.09, -0.20, h * 0.74)), 0.34),
            (Vector((0.14, -0.10, h * 0.80)), 0.32),
            (Vector((-0.05, 0.02, h * 0.90)), 0.37),
        )):
            cm.ramo([pg, pt], [0.048, 0.024], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.34, folha, lados=6, pontas=0.22, queda_borda=0.06, semente=350 + idx)
    else:
        # Var 6: Carvalho alto (2.19 m) de tronco duplo fundido e copa em torre de múltiplos gomos
        p1 = Vector((0.0, 0.0, h * 0.36))
        p2 = Vector((0.02, 0.02, h * 0.68))
        cm.ramo([(0, 0, 0), p1, p2], [0.12, 0.088, 0.060], casca, lados=6, sapopemba=0.46)
        for idx, (orig, pt, rc) in enumerate((
            (p1, Vector((-0.22, -0.08, h * 0.58)), 0.33),
            (p1, Vector((0.21, 0.10, h * 0.62)), 0.33),
            (p2, Vector((-0.16, 0.14, h * 0.78)), 0.34),
            (p2, Vector((0.16, -0.12, h * 0.82)), 0.34),
            (p2, Vector((0.0, 0.0, h * 0.92)), 0.35),
        )):
            cm.ramo([orig, pt], [0.045, 0.022], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt, rc, 0.34, folha, lados=6, pontas=0.21, queda_borda=0.06, semente=360 + idx)

    return cm.finalizar(pos=pos, raio_max_xy=0.56)


# ================================================================== 4. PINHEIRO (arv_pinheiro_1..6)
def construir_pinheiro(n, pos=(0, 0, 0)):
    nome = f'arv_pinheiro_{n}'
    cm = ConstrutorMalha(nome)
    rnd = random.Random(4000 + n * 113)
    casca, folha = 'P_Tronco', 'P_FolhaPerene'

    alturas = [2.66, 2.51, 2.89, 2.59, 2.72, 2.65]
    h = alturas[n - 1]
    _raizes_base(cm, 4, 0.095, 0.22, 0.18, casca, rnd, fase0=n * 0.6)

    if n == 1:
        # Var 1: 5 saias estreladas recortadas em camadas ascendentes
        cm.ramo([(0, 0, 0), (0, 0, h * 0.92)], [0.092, 0.020], casca, lados=6, sapopemba=0.38)
        for k in range(5):
            u = k / 4.0
            zk = h * (0.28 + 0.60 * u)
            rk = 0.45 * (1.0 - 0.56 * u)
            ez = 0.44 * (1.0 - 0.22 * u)
            cm.fronde_copa((0, 0, zk), rk, ez, folha, lados=7 - (k // 2), pontas=0.28, queda_borda=0.10,
                           rot_z=k * 0.55, semente=410 + k)
    elif n == 2:
        # Var 2: Pinheiro de encosta — tronco arqueado, galhos baixos secos e 4 saias densas
        p1 = Vector((0.06, -0.03, h * 0.35))
        p2 = Vector((-0.02, 0.02, h * 0.90))
        cm.ramo([(0, 0, 0), p1, p2], [0.092, 0.062, 0.020], casca, lados=6, sapopemba=0.40)
        cm.ramo([Vector((0.04, -0.02, h * 0.22)), Vector((0.20, -0.08, h * 0.20))], [0.028, 0.010], casca, lados=4, fechar_base=False)
        cm.ramo([Vector((0.05, -0.02, h * 0.28)), Vector((-0.16, 0.10, h * 0.27))], [0.026, 0.010], casca, lados=4, fechar_base=False)
        for k in range(4):
            u = k / 3.0
            c = p1.lerp(p2, 0.15 + 0.82 * u)
            rk = 0.44 * (1.0 - 0.54 * u)
            cm.fronde_copa(c, rk, 0.45 * (1.0 - 0.18 * u), folha, lados=7 - (k // 2), pontas=0.28, queda_borda=0.10,
                           rot_z=k * 0.7, semente=420 + k)
    elif n == 3:
        # Var 3: Pinheiro alto (2.89 m) com 5 camadas e topo duplo bifurcado
        p_div = Vector((0, 0, h * 0.68))
        cm.ramo([(0, 0, 0), p_div], [0.095, 0.042], casca, lados=6, sapopemba=0.38)
        cm.ramo([p_div, Vector((-0.06, 0.03, h * 0.92))], [0.034, 0.015], casca, lados=4, fechar_base=False)
        cm.ramo([p_div, Vector((0.07, -0.04, h * 0.85))], [0.030, 0.014], casca, lados=4, fechar_base=False)
        for k in range(3):
            zk = h * (0.28 + 0.18 * k)
            rk = 0.45 * (1.0 - 0.18 * k)
            cm.fronde_copa((0, 0, zk), rk, 0.44, folha, lados=7, pontas=0.27, queda_borda=0.10, rot_z=k * 0.5, semente=430 + k)
        cm.fronde_copa((-0.06, 0.03, h * 0.88), 0.25, 0.40, folha, lados=5, pontas=0.26, queda_borda=0.09, semente=435)
        cm.fronde_copa((0.07, -0.04, h * 0.80), 0.24, 0.36, folha, lados=5, pontas=0.26, queda_borda=0.09, semente=436)
    elif n == 4:
        # Var 4: Pinheiro varrido por vento de altitude (saias assimétricas deslocadas para +X)
        cm.ramo([(0, 0, 0), (-0.03, 0.0, h * 0.45), (0.05, 0.02, h * 0.90)],
                [0.094, 0.058, 0.020], casca, lados=6, sapopemba=0.42)
        for k in range(5):
            u = k / 4.0
            zk = h * (0.28 + 0.60 * u)
            rk = 0.44 * (1.0 - 0.55 * u)
            ox = 0.05 * u + (0.03 if k % 2 else -0.01)
            cm.fronde_copa((ox, 0.01 * k, zk), rk, 0.42 * (1.0 - 0.2 * u), folha, lados=6,
                           pontas=0.30, queda_borda=0.10, assimetria=(1.15, 0.90), rot_z=k * 0.4, semente=440 + k)
    elif n == 5:
        # Var 5: Pinheiro antigo com falha a meia altura (mostrando o tronco e galho quebrado)
        cm.ramo([(0, 0, 0), (0.01, -0.02, h * 0.92)], [0.094, 0.020], casca, lados=6, sapopemba=0.40)
        cm.ramo([(0, 0, h * 0.50), (0.22, 0.12, h * 0.54)], [0.032, 0.012], casca, lados=4, fechar_base=False)
        for idx, (zf, rk, ez) in enumerate(((0.28, 0.45, 0.42), (0.40, 0.39, 0.40),
                                            (0.64, 0.33, 0.38), (0.77, 0.27, 0.36), (0.90, 0.20, 0.38))):
            cm.fronde_copa((0, 0, h * zf), rk, ez, folha, lados=6, pontas=0.28, queda_borda=0.10,
                           rot_z=idx * 0.6, semente=450 + idx)
    else:
        # Var 6: Pinheiro gêmeo (tronco principal + pinheiro menor nascendo da base)
        cm.ramo([(-0.04, 0, 0), (-0.06, 0.01, h * 0.91)], [0.088, 0.018], casca, lados=6, sapopemba=0.35)
        cm.ramo([(0.05, -0.02, 0.02), (0.14, -0.05, h * 0.56)], [0.055, 0.016], casca, lados=5, fechar_base=False)
        for k in range(3):
            u = k / 2.0
            cm.fronde_copa((-0.06, 0.01, h * (0.34 + 0.54 * u)), 0.40 * (1.0 - 0.50 * u), 0.44, folha,
                           lados=6, pontas=0.28, queda_borda=0.10, rot_z=k * 0.6, semente=460 + k)
        for k in range(2):
            u = k / 1.0
            cm.fronde_copa((0.14, -0.05, h * (0.28 + 0.26 * u)), 0.26 * (1.0 - 0.35 * u), 0.34, folha,
                           lados=5, pontas=0.26, queda_borda=0.09, rot_z=k * 0.8, semente=465 + k)

    return cm.finalizar(pos=pos, raio_max_xy=0.52)


# ================================================================== 5. SALGUEIRO-DO-PÂNTANO (arv_salgueiro_1..6)
def _cortinas_salgueiro(cm, centro_copa, r_anel, z_topo, n_fitas, folha, rnd):
    """Cria cortinas prismáticas 3D fechadas de folhagem pendente presas à copa (sem flutuar!)."""
    for k in range(n_fitas):
        a = 2 * PI * k / n_fitas + rnd.uniform(-0.14, 0.14)
        r0 = r_anel * rnd.uniform(0.82, 1.04)
        orig = Vector((centro_copa.x + math.cos(a) * r0, centro_copa.y + math.sin(a) * r0, z_topo))
        compr = rnd.uniform(0.62, 0.88)
        dir_f = Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, -1.0)).normalized()
        cm.lamina_folha(orig, dir_f, compr, rnd.uniform(0.10, 0.135), 0.06, folha, arco=-0.07)


def construir_salgueiro(n, pos=(0, 0, 0)):
    nome = f'arv_salgueiro_{n}'
    cm = ConstrutorMalha(nome)
    rnd = random.Random(5000 + n * 127)
    casca, folha = 'P_Tronco', 'P_FolhaSalgueiro'

    alturas = [1.54, 1.61, 1.52, 1.52, 1.45, 1.52]
    h = alturas[n - 1]
    _raizes_base(cm, 4, 0.11, 0.28, 0.28, casca, rnd, fase0=n * 0.8)

    if n == 1:
        # Var 1: Tronco curvo sobre raízes altas, abóbada central e 10 cortinas pendentes
        topo = Vector((0.04, -0.03, h * 0.68))
        cm.ramo([(0, 0, 0), (-0.04, 0.03, h * 0.34), topo], [0.115, 0.088, 0.065], casca, lados=6, sapopemba=0.45)
        for k in range(3):
            a = k * 2 * PI / 3 + 0.3
            pg = topo + Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, 0.10))
            cm.ramo([topo, pg], [0.045, 0.022], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pg + Vector((0, 0, 0.06)), 0.30, 0.26, folha, lados=6, pontas=0.20, queda_borda=0.08, semente=510 + k)
        cm.fronde_copa(topo + Vector((0, 0, 0.20)), 0.39, 0.30, folha, lados=7, pontas=0.18, queda_borda=0.09, semente=515)
        _cortinas_salgueiro(cm, topo, 0.35, topo.z + 0.12, 10, folha, rnd)
    elif n == 2:
        # Var 2: Dois troncos abertos em V com duas abóbadas choronas
        pg = Vector((0, 0, h * 0.26))
        cm.ramo([(0, 0, 0), pg], [0.12, 0.092], casca, lados=6, sapopemba=0.45)
        for idx, sgn in enumerate((-1, 1)):
            pt = Vector((sgn * 0.18, sgn * 0.06, h * (0.68 + 0.05 * idx)))
            cm.ramo([pg, pt], [0.062, 0.036], casca, lados=5, fechar_base=False)
            cm.fronde_copa(pt + Vector((0, 0, 0.14)), 0.34, 0.30, folha, lados=6, pontas=0.20, queda_borda=0.09, semente=520 + idx)
            _cortinas_salgueiro(cm, pt, 0.28, pt.z + 0.10, 5, folha, rnd)
    elif n == 3:
        # Var 3: Salgueiro debruçado sobre a água com raízes-escora traseiras
        p1 = Vector((-0.05, 0.0, h * 0.32))
        topo = Vector((0.12, 0.04, h * 0.66))
        cm.ramo([(0, 0, 0), p1, topo], [0.115, 0.085, 0.058], casca, lados=6, sapopemba=0.45)
        cm.fronde_copa(topo + Vector((0.04, 0, 0.18)), 0.39, 0.30, folha, lados=7, pontas=0.20, queda_borda=0.09, semente=531)
        cm.fronde_copa(p1 + Vector((-0.12, -0.06, 0.28)), 0.31, 0.28, folha, lados=6, pontas=0.20, queda_borda=0.08, semente=532)
        _cortinas_salgueiro(cm, topo + Vector((0.02, 0, 0)), 0.34, topo.z + 0.10, 9, folha, rnd)
    elif n == 4:
        # Var 4: Tronco grosso baixo com 3 braços abertos em estrela e cascatas separadas
        pg = Vector((0, 0, h * 0.38))
        cm.ramo([(0, 0, 0), pg], [0.12, 0.088], casca, lados=6, sapopemba=0.48)
        for k in range(3):
            a = k * 2 * PI / 3 + 0.5
            pt = Vector((math.cos(a) * 0.20, math.sin(a) * 0.20, h * 0.68))
            cm.ramo([pg, pt], [0.050, 0.026], casca, lados=4, fechar_base=False)
            cm.fronde_copa(pt + Vector((0, 0, 0.12)), 0.31, 0.28, folha, lados=6, pontas=0.20, queda_borda=0.09, semente=540 + k)
            _cortinas_salgueiro(cm, pt, 0.25, pt.z + 0.08, 3, folha, rnd)
    elif n == 5:
        # Var 5: Salgueiro retorcido com galho seco espetado para o alto e cabeleira varrida
        topo = Vector((-0.06, 0.04, h * 0.66))
        cm.ramo([(0, 0, 0), (0.04, -0.03, h * 0.34), topo], [0.115, 0.086, 0.060], casca, lados=6, sapopemba=0.42, torcao=0.5)
        cm.ramo([topo, Vector((0.18, -0.14, h * 0.96))], [0.038, 0.012], casca, lados=4, fechar_base=False)
        cm.fronde_copa(topo + Vector((-0.04, 0.02, 0.18)), 0.38, 0.29, folha, lados=7, pontas=0.20, queda_borda=0.09, semente=551)
        cm.fronde_copa(topo + Vector((0.12, 0.08, 0.10)), 0.29, 0.26, folha, lados=6, pontas=0.20, queda_borda=0.08, semente=552)
        _cortinas_salgueiro(cm, topo, 0.33, topo.z + 0.10, 9, folha, rnd)
    else:
        # Var 6: Raízes em gaiola alta de mangue/pântano e copa em cascata dupla
        topo = Vector((0.0, 0.0, h * 0.70))
        cm.ramo([(0, 0, 0.12), (0.02, 0.02, h * 0.42), topo], [0.105, 0.082, 0.058], casca, lados=6, fechar_base=True)
        _raizes_base(cm, 5, 0.12, 0.32, 0.38, casca, rnd, fase0=0.2)
        cm.fronde_copa(topo + Vector((0, 0, 0.18)), 0.37, 0.30, folha, lados=7, pontas=0.20, queda_borda=0.09, semente=561)
        cm.fronde_copa(topo + Vector((-0.10, 0.10, 0.06)), 0.30, 0.26, folha, lados=6, pontas=0.18, queda_borda=0.08, semente=562)
        _cortinas_salgueiro(cm, topo, 0.33, topo.z + 0.10, 8, folha, rnd)

    return cm.finalizar(pos=pos, raio_max_xy=0.56)


# ================================================================== 6. FUNGO-CRISTAL (arv_fungo_cristal_1..6)
def _chapeu_fungo_cristal(cm, topo, r_chapeu, alt_chapeu, n_lados, n_cristais, rnd, incl=(0.0, 0.0)):
    """Chapéu carnudo de fungo-cristal com lamelas inferiores bioluminescentes (P_Biomassa),
    borda lobada (P_ChapeuCristal) e drusas de cristal (P_Cristal) cravadas na umbrela."""
    topo = Vector(topo)
    fase = rnd.uniform(0, 2 * PI)
    perfis = [
        (0.24, -0.02, 'P_Biomassa'),
        (0.75, -0.05, 'P_Biomassa'),
        (1.00, 0.00, 'P_ChapeuCristal'),
        (0.84, 0.44, 'P_ChapeuCristal'),
        (0.42, 0.80, 'P_ChapeuCristal'),
    ]
    aneis = []
    for rr, hh, _ in perfis:
        anel = []
        for k in range(n_lados):
            a = 2 * PI * k / n_lados
            onda = 1.0 + 0.09 * math.sin(4 * a + fase) + 0.05 * math.cos(7 * a - fase)
            rx = r_chapeu * rr * onda
            ry = r_chapeu * rr * onda
            dz = alt_chapeu * hh + incl[0] * math.cos(a) * rx + incl[1] * math.sin(a) * ry
            anel.append(topo + Vector((math.cos(a) * rx, math.sin(a) * ry, dz)))
        aneis.append(anel)
    p_apice = topo + Vector((incl[0] * 0.04, incl[1] * 0.04, alt_chapeu))
    aneis.append([p_apice])

    vs = [[cm.bm.verts.new(p) for p in anel] for anel in aneis]
    for i in range(len(vs) - 1):
        mat_faixa = perfis[min(i, len(perfis) - 1)][2]
        idx_m = cm.mi(mat_faixa)
        A, B = vs[i], vs[i + 1]
        if len(B) == 1:
            for k in range(n_lados):
                f = cm.bm.faces.new((A[k], A[(k + 1) % n_lados], B[0]))
                f.material_index = idx_m
                f.smooth = True
        else:
            for k in range(n_lados):
                f = cm.bm.faces.new((A[k], A[(k + 1) % n_lados], B[(k + 1) % n_lados], B[k]))
                f.material_index = idx_m
                f.smooth = True
    f_base = cm.bm.faces.new(list(reversed(vs[0])))
    f_base.material_index = cm.mi('P_Biomassa')

    a0 = rnd.uniform(0, 2 * PI)
    for k in range(n_cristais):
        a = a0 + 2 * PI * k / n_cristais + rnd.uniform(-0.22, 0.22)
        d = r_chapeu * rnd.uniform(0.22, 0.56)
        base_c = topo + Vector((math.cos(a) * d, math.sin(a) * d, alt_chapeu * 0.35))
        eixo_c = Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, 1.0)).normalized()
        cm.cristal_prisma(base_c, eixo_c, rnd.uniform(0.038, 0.055), rnd.uniform(0.20, 0.34), 'P_Cristal', lados=5)


def construir_fungo_cristal(n, pos=(0, 0, 0)):
    nome = f'arv_fungo_cristal_{n}'
    cm = ConstrutorMalha(nome)
    rnd = random.Random(6000 + n * 139)
    caule = 'P_FungoCaule'

    alturas = [2.02, 1.66, 1.93, 1.80, 2.07, 1.92]
    h = alturas[n - 1]
    _raizes_base(cm, 4, 0.11, 0.24, 0.20, caule, rnd, fase0=n * 0.6)

    if n == 1:
        p1 = Vector((0.05, -0.03, h * 0.42))
        topo = Vector((-0.02, 0.02, h * 0.78))
        cm.ramo([(0, 0, 0), p1, topo], [0.115, 0.082, 0.065], caule, lados=7, sapopemba=0.45)
        _chapeu_fungo_cristal(cm, topo, 0.41, 0.27, 10, 5, rnd, incl=(0.06, -0.04))
        cm.cristal_prisma(p1 + Vector((0.05, 0, 0)), Vector((0.6, 0.2, 0.8)), 0.035, 0.18, 'P_Cristal', lados=5)
    elif n == 2:
        topo1 = Vector((-0.06, 0.03, h * 0.76))
        cm.ramo([(-0.02, 0, 0), (-0.08, 0.04, h * 0.40), topo1], [0.105, 0.075, 0.058], caule, lados=6, sapopemba=0.38)
        _chapeu_fungo_cristal(cm, topo1, 0.35, 0.25, 9, 4, rnd, incl=(-0.05, 0.04))

        topo2 = Vector((0.16, -0.08, h * 0.48))
        cm.ramo([(0.04, -0.02, 0.02), (0.12, -0.06, h * 0.25), topo2], [0.072, 0.052, 0.042], caule, lados=6, fechar_base=False)
        _chapeu_fungo_cristal(cm, topo2, 0.23, 0.17, 8, 3, rnd, incl=(0.08, -0.06))
    elif n == 3:
        topo = Vector((0.02, 0.02, h * 0.76))
        cm.ramo([(0, 0, 0), (-0.04, -0.03, h * 0.38), topo], [0.11, 0.080, 0.062], caule, lados=7, sapopemba=0.42)
        _chapeu_fungo_cristal(cm, topo, 0.39, 0.26, 10, 4, rnd)
        cm.cristal_prisma(topo + Vector((0, 0, 0.16)), Vector((0.04, -0.03, 1.0)), 0.055, 0.34, 'P_Cristal', lados=6)
    elif n == 4:
        pg = Vector((0, 0, h * 0.36))
        cm.ramo([(0, 0, 0), pg], [0.115, 0.085], caule, lados=6, sapopemba=0.44)
        t1 = Vector((-0.15, 0.06, h * 0.78))
        t2 = Vector((0.16, -0.07, h * 0.62))
        cm.ramo([pg, t1], [0.062, 0.046], caule, lados=6, fechar_base=False)
        cm.ramo([pg, t2], [0.058, 0.042], caule, lados=6, fechar_base=False)
        _chapeu_fungo_cristal(cm, t1, 0.29, 0.21, 8, 3, rnd, incl=(-0.06, 0.03))
        _chapeu_fungo_cristal(cm, t2, 0.26, 0.19, 8, 3, rnd, incl=(0.06, -0.04))
        cm.cristal_prisma(pg + Vector((0, 0, 0.02)), Vector((0.1, 0.5, 0.85)), 0.038, 0.20, 'P_Cristal', lados=5)
    elif n == 5:
        p1 = Vector((-0.06, 0.0, h * 0.38))
        topo = Vector((0.08, 0.04, h * 0.76))
        cm.ramo([(0, 0, 0), p1, topo], [0.118, 0.085, 0.065], caule, lados=7, sapopemba=0.46)
        _chapeu_fungo_cristal(cm, topo, 0.39, 0.27, 9, 5, rnd, incl=(0.10, 0.04))
        cm.cristal_prisma(Vector((0.14, -0.10, 0.02)), Vector((0.45, -0.35, 0.82)), 0.045, 0.26, 'P_Cristal', lados=5)
        cm.cristal_prisma(Vector((-0.12, 0.12, 0.02)), Vector((-0.40, 0.40, 0.82)), 0.038, 0.22, 'P_Cristal', lados=5)
    else:
        p_meio = Vector((0.03, -0.02, h * 0.48))
        topo = Vector((-0.02, 0.02, h * 0.78))
        cm.ramo([(0, 0, 0), p_meio, topo], [0.115, 0.082, 0.058], caule, lados=6, sapopemba=0.42)
        _chapeu_fungo_cristal(cm, p_meio, 0.37, 0.19, 8, 3, rnd)
        _chapeu_fungo_cristal(cm, topo, 0.30, 0.23, 8, 4, rnd)

    return cm.finalizar(pos=pos, raio_max_xy=0.48)


# ================================================================== MONTAGEM E EXECUÇÃO
def main():
    sc = amb.iniciar_cena(semente=101)
    construtores = [
        ('acacia', construir_acacia),
        ('betula', construir_betula),
        ('carvalho', construir_carvalho),
        ('pinheiro', construir_pinheiro),
        ('salgueiro', construir_salgueiro),
        ('fungo_cristal', construir_fungo_cristal),
    ]

    # Grade 6 colunas (variantes 1..6) × 6 linhas (espécies), espaçamento de 1.85 m
    objetos = []
    for lin, (_, fn) in enumerate(construtores):
        y = (2.5 - lin) * 1.95
        for col in range(6):
            x = (col - 2.5) * 1.85
            o = fn(col + 1, pos=(x, y, 0.0))
            objetos.append(o)

    vistas = [
        ('amb_arvores_0.png', (0.0, -17.2, 10.6), (0.0, 0.1, 0.9), 38.0, 1600, 1100),
        ('amb_arvores_1.png', (13.2, -12.4, 9.4), (0.0, 0.0, 0.9), 38.0, 1600, 1100),
        ('amb_arvores_perto.png', (4.8, -6.4, 3.2), (0.6, -1.6, 1.05), 36.0, 1600, 1100),
    ]
    amb.renderizar_estudo(sc, objetos, 'amb_arvores', limite_tris=500, bioma_chao='campina',
                          vistas_vitrine=vistas, espalhar_raio=(14.5, 10.5), n_espalhados=72,
                          escala_espalhados=(0.88, 1.16), dist_min=1.35)
    print('ESTUDO_AMB_ARVORES OK')


if __name__ == '__main__':
    main()
