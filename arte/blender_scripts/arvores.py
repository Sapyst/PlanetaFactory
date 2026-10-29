"""Árvores por receita: cada espécie é um conjunto de regras (altura, tronco, galhos, forma e folha da copa) e cada
variação sai de uma semente. 6 espécies × 6 variações. Tronco e galhos ficam embaixo da copa de verdade, para a árvore
nua (inverno, queimada, caída) continuar parecendo árvore. A folhagem usa material próprio por comportamento na estação
(o jogo troca cor e folha pelo perfil do material). Cabe em 1 tile (copa até 0,48 m do centro); até 400 triângulos.
Uso: blender --background --python arvores.py [-- nome ...]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar, Q
from mathutils import Vector, Matrix
import bmesh

V = 'mapa/vegetacao'
PI = math.pi
LIM = 0.48                      # raio máximo da copa (1 tile)
VARIACOES = 6

ESPECIES = {
    'carvalho':  dict(nome='Carvalho-de-campina', folha='P_FolhaCaduca', casca='P_Tronco', copa='redonda',
                      desc='copa redonda larga; caduca: amarela/laranja no outono, nua no inverno'),
    'betula':    dict(nome='Bétula-prata', folha='P_FolhaBetula', casca='P_TroncoClaro', copa='oval',
                      desc='estreita, tronco claro; caduca: amarela no outono, nua no inverno'),
    'pinheiro':  dict(nome='Pinheiro', folha='P_FolhaPerene', casca='P_Tronco', copa='cone',
                      desc='cone em camadas; perene (não muda)'),
    'salgueiro': dict(nome='Salgueiro-do-pântano', folha='P_FolhaSalgueiro', casca='P_Tronco', copa='chorao',
                      desc='galhos caídos; amarelado no inverno'),
    'acacia':    dict(nome='Acácia-seca', folha='P_FolhaSeca', casca='P_Tronco', copa='guarda_chuva',
                      desc='copa achatada em guarda-chuva; perde metade no verão seco'),
    'fungo_cristal': dict(nome='Fungo-cristal', folha='P_ChapeuCristal', casca='P_FungoCaule', copa='fungo',
                      desc='alienígena: chapéu com cristais que brilham; perene'),
}


def tubo(p, a, b, r0, r1, mat, lados=5):
    """Tronco/galho afilado de a até b (qualquer direção)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    q = d.normalized().to_track_quat('Z', 'Y')
    M = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
    res = bmesh.ops.create_cone(p.bm, cap_ends=True, segments=lados, radius1=r0, radius2=r1, depth=d.length, matrix=M)
    for v in res['verts']:
        v.co = Q(v.co)
    p.faces_de(res['verts'], mat)


def dentro(c, r, esc=(1, 1, 1)):
    """Puxa o centro de um tufo para a copa caber no tile."""
    c = Vector(c)
    m = r * max(esc[0], esc[1])
    plano = Vector((c.x, c.y, 0))
    if plano.length + m > LIM:
        k = max(0.0, LIM - m) / max(plano.length, 1e-6)
        c.x *= k; c.y *= k
    return c


def tufo(p, c, r, esc, mat, rnd):
    c = dentro(c, r, esc)
    p.pedra(c, r, esc, mat, rnd.randint(0, 99999), ruido=0.16)


def galhos(p, rnd, casca, h, n, z0, z1, elev, comp, r):
    pontas = []
    a0 = rnd.uniform(0, 2 * PI)
    for i in range(n):
        a = a0 + i * 2 * PI / n + rnd.uniform(-0.4, 0.4)
        z = rnd.uniform(z0, z1) * h
        e = math.radians(rnd.uniform(*elev))
        L = rnd.uniform(*comp)
        b = Vector((math.cos(a) * math.cos(e) * L, math.sin(a) * math.cos(e) * L, z + math.sin(e) * L))
        b = dentro(b, 0.12)
        tubo(p, (0, 0, z), b, r, r * 0.45, casca, lados=4)
        pontas.append(b)
    return pontas


def arvore(especie, n):
    e = ESPECIES[especie]
    nome = 'arv_%s_%d' % (especie, n)
    m = Modelo(nome, V, orcamento=400, descricao='%s (variação %d): %s. Bloqueia 1 tile.' % (e['nome'], n, e['desc']))
    m.ocupa_canto = True
    p = m.parte()
    rnd = random.Random(hash(especie) % 10007 * 31 + n * 977)
    folha, casca = e['folha'], e['casca']
    c = e['copa']
    if c == 'redonda':
        h = rnd.uniform(1.8, 2.3)
        tubo(p, (0, 0, 0), (rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), h * 0.55), 0.10, 0.06, casca, lados=6)
        for b in galhos(p, rnd, casca, h, rnd.randint(4, 5), 0.36, 0.55, (25, 45), (0.30, 0.40), 0.045):
            tufo(p, b + Vector((0, 0, 0.06)), rnd.uniform(0.2, 0.25), (1, 1, 0.82), folha, rnd)
        tufo(p, (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), h * 0.72), rnd.uniform(0.26, 0.3), (1, 1, 0.85), folha, rnd)
        tufo(p, (rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), h * 0.9), rnd.uniform(0.2, 0.24), (1, 1, 0.8), folha, rnd)
    elif c == 'oval':
        h = rnd.uniform(2.3, 2.9)
        tubo(p, (0, 0, 0), (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), h * 0.95), 0.065, 0.025, casca, lados=5)
        for b in galhos(p, rnd, casca, h, rnd.randint(5, 6), 0.4, 0.85, (40, 60), (0.14, 0.24), 0.025):
            tufo(p, b + Vector((0, 0, 0.05)), rnd.uniform(0.12, 0.16), (0.9, 0.9, 1.3), folha, rnd)
        tufo(p, (0, 0, h * 0.9), rnd.uniform(0.14, 0.17), (0.9, 0.9, 1.4), folha, rnd)
    elif c == 'cone':
        h = rnd.uniform(2.4, 3.1)
        tubo(p, (0, 0, 0), (0, 0, h * 0.97), 0.085, 0.02, casca, lados=5)
        camadas = 4
        base = rnd.uniform(0.25, 0.32) * h
        for k in range(camadas):
            f = k / camadas
            z = base + (h - base) * f * 0.92
            r = (0.46 - 0.30 * f) * rnd.uniform(0.92, 1.0)
            alt = (h - base) / camadas * 1.35
            p.cil((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), z + alt / 2), min(r, LIM), alt, folha, lados=7,
                  r2=0.03, rot=rnd.uniform(0, PI))
    elif c == 'chorao':
        h = rnd.uniform(1.6, 2.0)
        topo = Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), h * 0.62))
        tubo(p, (0, 0, 0), topo, 0.12, 0.07, casca, lados=6)
        galhos(p, rnd, casca, h, 3, 0.5, 0.6, (20, 35), (0.22, 0.3), 0.04)
        tufo(p, topo + Vector((0, 0, 0.2)), 0.34, (1.15, 1.15, 0.7), folha, rnd)
        for k in range(2):
            a = rnd.uniform(0, 2 * PI)
            tufo(p, topo + Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.08)), 0.2, (1, 1, 0.7), folha, rnd)
        fitas = 12
        for k in range(fitas):
            a = k * 2 * PI / fitas + rnd.uniform(-0.15, 0.15)
            r0 = rnd.uniform(0.32, 0.38)
            a_pt = Vector((math.cos(a) * r0, math.sin(a) * r0, topo.z + 0.1))
            b_pt = Vector((math.cos(a) * (r0 + 0.07), math.sin(a) * (r0 + 0.07), rnd.uniform(0.4, 0.75)))
            tubo(p, dentro(a_pt, 0.04), dentro(b_pt, 0.04), 0.04, 0.015, folha, lados=3)
    elif c == 'guarda_chuva':
        h = rnd.uniform(1.6, 2.0)
        garfo = Vector((0, 0, h * rnd.uniform(0.38, 0.46)))
        tubo(p, (0, 0, 0), garfo, 0.08, 0.06, casca, lados=5)
        a0 = rnd.uniform(0, 2 * PI)
        for k in range(3):
            a = a0 + k * 2 * PI / 3 + rnd.uniform(-0.3, 0.3)
            ponta = dentro(Vector((math.cos(a) * 0.24, math.sin(a) * 0.24, h * rnd.uniform(0.8, 0.86))), 0.24)
            tubo(p, garfo, ponta, 0.05, 0.03, casca, lados=4)
            tufo(p, ponta + Vector((0, 0, 0.05)), rnd.uniform(0.21, 0.24), (1.0, 1.0, 0.24), folha, rnd)
        tufo(p, (0, 0, h * 0.93), rnd.uniform(0.3, 0.33), (1.05, 1.05, 0.22), folha, rnd)
    elif c == 'fungo':
        h = rnd.uniform(1.4, 1.9)
        meio = Vector((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), h * 0.5))
        topo = Vector((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), h * 0.88))
        tubo(p, (0, 0, 0), meio, 0.11, 0.08, casca, lados=6)
        tubo(p, meio, topo, 0.08, 0.06, casca, lados=6)
        rc = rnd.uniform(0.42, 0.46)
        cc = dentro(topo + Vector((0, 0, 0.06)), rc)
        p.pedra(cc, rc, (1, 1, 0.3), folha, rnd.randint(0, 9999), ruido=0.08)
        a0 = rnd.uniform(0, 2 * PI)
        for k in range(4):                      # um por quadrante: cristais nunca se cruzam
            a = a0 + k * PI / 2 + rnd.uniform(-0.3, 0.3)
            d = rnd.uniform(0.12, 0.22)
            hc = rnd.uniform(0.18, 0.3)
            pc = Vector((cc.x + math.cos(a) * d, cc.y + math.sin(a) * d, cc.z + 0.08 + hc / 2))
            p.cil(pc, 0.045, hc, 'P_Cristal', lados=5, r2=0.0, rot=rnd.uniform(0, PI))
    zmin = min(v.co.z for v in p.bm.verts)
    for v in p.bm.verts:
        v.co.z -= zmin
    return m


TODOS = []
for _e in ESPECIES:
    for _n in range(1, VARIACOES + 1):
        TODOS.append((lambda e=_e, n=_n: arvore(e, n)))
        TODOS[-1].__name__ = 'arv_%s_%d' % (_e, _n)

if __name__ == '__main__':
    so = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    rodar([f for f in TODOS if not so or any(f.__name__.startswith(x) for x in so)], os.path.join(lib_pf.RAIZ, 'mapa', '_relatorio_arvores.json'))
