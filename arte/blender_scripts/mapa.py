"""Objetos de mapa: vegetação por bioma, rochas, montanhas, jazidas de recurso e enfeites de água.
Tipos: 'estrutura' = bloqueia tiles (precisa limpar para construir); 'deco' = enfeite sem colisão (grama, seixos).
Jazidas ocupam 1 tile e são mineradas por cima (extrator/broca).
Uso: blender --background --python mapa.py
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, rodar
from mathutils import Vector

V, R, J, A = 'mapa/vegetacao', 'mapa/rochas', 'mapa/jazidas', 'mapa/agua'
PI = math.pi

def apoiar(m):
    zmin = min(v.co.z for p in m.partes for v in p.bm.verts)
    for p in m.partes:
        for v in p.bm.verts: v.co.z -= zmin
    return m

def bloqueio(m):
    m.ocupa_canto = True   # obstáculo natural: some ao construir; pode encostar nos cantos
    return m

# ---------------------------------------------------------------- vegetação
def _arvore(nome, semente, altura, copa, desc):
    m = bloqueio(Modelo(nome, V, descricao=desc)); p = m.parte(); rnd = random.Random(semente)
    p.cil((0, 0, altura*0.30), 0.09, altura*0.60, 'P_Tronco', lados=6, r2=0.06)
    for i in range(3):
        a = rnd.uniform(0, 2*PI); d = 0.0 if i == 0 else 0.13
        p.pedra((math.cos(a)*d, math.sin(a)*d, altura*0.60 + i*0.16), copa*(1 - 0.18*i), (1, 1, 0.8),
                'P_Folha' if i % 2 == 0 else 'P_FolhaClara', semente*10 + i, ruido=0.12)
    return m

def arvore_campina_a(): return _arvore('arvore_campina_a', 1, 1.6, 0.40, 'Árvore da campina (bloqueia 1 tile).')
def arvore_campina_b(): return _arvore('arvore_campina_b', 2, 2.1, 0.34, 'Árvore alta da campina (bloqueia 1 tile).')

def _revolucao(p, aneis, mats):
    """Liga anéis de vértices (mesmo nº de pontos) em quads; mats[i] = material entre o anel i e i+1.
    Último anel pode ser um ponto só (fecha em leque)."""
    from lib_pf import Q
    vs = [[p.bm.verts.new(Q(v)) for v in anel] for anel in aneis]
    for i in range(len(vs) - 1):
        a, b = vs[i], vs[i + 1]
        mi = p._mi(mats[i])
        n = len(a)
        if len(b) == 1:
            for k in range(n):
                p.bm.faces.new((a[k], a[(k + 1) % n], b[0])).material_index = mi
        else:
            for k in range(n):
                p.bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])).material_index = mi


def _um_cogumelo(p, base, altura, chapeu, rnd, lados=14):
    """Cogumelo orgânico: pé curvo que afina (bulbo embaixo, leve alargamento sob o chapéu), chapéu abaulado e
    irregular com a borda ondulada e caída, lamelas por baixo (material que brilha)."""
    curva = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized() * altura * rnd.uniform(0.06, 0.14)
    fase = rnd.uniform(0, 2 * PI)
    def eixo(t):                                   # espinha do pé (curva suave)
        return base + Vector((0, 0, altura * t)) + curva * math.sin(t * PI / 2) ** 1.5
    def raio_pe(t):
        return chapeu * (0.42 - 0.30 * t + 0.22 * math.exp(-t * 9.0) + 0.10 * math.exp(-(1 - t) * 10.0))
    aneis = []
    for i in range(10):
        t = i / 9.0
        c = eixo(t)
        r = raio_pe(t)
        aneis.append([c + Vector((math.cos(a) * r * (1 + rnd.uniform(-0.05, 0.05)), math.sin(a) * r * (1 + rnd.uniform(-0.05, 0.05)), 0))
                      for a in (2 * PI * k / lados for k in range(lados))])
    _revolucao(p, aneis, ['P_FungoCaule'] * 9)
    # chapéu: perfil (raio relativo, altura relativa) de dentro (sob o chapéu) até o topo; borda ondulada
    topo = eixo(1.0)
    perfil = [(0.18, -0.02), (0.55, 0.00), (0.92, -0.10), (1.00, -0.04), (0.98, 0.10), (0.85, 0.28), (0.62, 0.42), (0.32, 0.50)]
    mats = ['P_Biomassa', 'P_Biomassa', 'P_Chapeu', 'P_Chapeu', 'P_Chapeu', 'P_Chapeu', 'P_Chapeu', 'P_Chapeu']
    aneis = []
    for rr, hh in perfil:
        anel = []
        for k in range(lados):
            a = 2 * PI * k / lados
            onda = 1 + 0.07 * math.sin(5 * a + fase) + 0.04 * math.sin(9 * a + fase * 2) + rnd.uniform(-0.03, 0.03)
            caida = 0.05 * math.sin(3 * a + fase) * rr           # borda que cai mais de um lado
            anel.append(topo + Vector((math.cos(a) * chapeu * rr * onda, math.sin(a) * chapeu * rr * onda, chapeu * (hh - caida))))
        aneis.append(anel)
    aneis.append([topo + Vector((0, 0, chapeu * 0.54))])
    _revolucao(p, aneis, mats)


def _cogumelo(nome, semente, altura, chapeu, desc):
    m = bloqueio(Modelo(nome, V, descricao=desc)); p = m.parte(); rnd = random.Random(semente)
    _um_cogumelo(p, Vector((0, 0, 0)), altura, chapeu, rnd)
    for k in range(3):                               # filhotes em volta do pé
        a = rnd.uniform(0, 2 * PI); d = rnd.uniform(0.24, 0.36)
        _um_cogumelo(p, Vector((math.cos(a) * d, math.sin(a) * d, 0)), rnd.uniform(0.14, 0.26), rnd.uniform(0.07, 0.11), rnd, lados=8)
    # encaixa no tile 1×1 (centraliza e reduz só no plano, se precisar)
    xs = [v.co.x for v in p.bm.verts]; ys = [v.co.y for v in p.bm.verts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = min(1.0, 0.92 / max(max(xs) - min(xs), max(ys) - min(ys)))
    for v in p.bm.verts:
        v.co.x = round((v.co.x - cx) * k, 6)
        v.co.y = round((v.co.y - cy) * k, 6)
    return m

def cogumelo_gigante_a(): return _cogumelo('cogumelo_gigante_a', 3, 1.3, 0.56, 'Cogumelo gigante da floresta fúngica. Corte dá biomassa.')
def cogumelo_gigante_b(): return _cogumelo('cogumelo_gigante_b', 4, 1.8, 0.52, 'Cogumelo gigante alto. Corte dá biomassa.')

def arbusto():
    m = bloqueio(Modelo('arbusto', V, descricao='Arbusto da campina (bloqueia 1 tile, limpa rápido).')); p = m.parte()
    for i, (x, y, r) in enumerate(((0, 0, 0.26), (0.18, 0.08, 0.17), (-0.15, 0.12, 0.16), (0.02, -0.18, 0.15))):
        p.pedra((x, y, r*0.7), r, (1, 1, 0.75), 'P_Folha' if i % 2 else 'P_FolhaClara', 20 + i, ruido=0.12)
    return apoiar(m)

def cacto_cristal():
    m = bloqueio(Modelo('cacto_cristal', V, descricao='Planta cristalina do deserto de sílex.')); p = m.parte()
    p.cil((0, 0, 0.45), 0.10, 0.90, 'P_Malaquita', lados=6, r2=0.07)
    p.barra((0, 0, 0.45), (0.22, 0, 0.62), 0.09, 0.09, 'P_Malaquita'); p.cil((0.22, 0, 0.75), 0.05, 0.26, 'P_Malaquita', lados=6)
    p.barra((0, 0, 0.30), (-0.20, 0.02, 0.42), 0.08, 0.08, 'P_Malaquita'); p.cil((-0.20, 0.02, 0.52), 0.045, 0.20, 'P_Malaquita', lados=6)
    for x, h in ((0, 0.98), (0.22, 0.94), (-0.20, 0.66)): p.cil((x, 0, h), 0.04, 0.10, 'P_Cristal', lados=5, r2=0.0)
    return m

def arvore_morta():
    m = bloqueio(Modelo('arvore_morta', V, descricao='Árvore seca do cinzal.')); p = m.parte()
    p.cil((0, 0, 0.6), 0.08, 1.2, 'P_Cinza', lados=6, r2=0.04)
    for a, z, l in ((0.3, 0.7, 0.35), (2.4, 0.9, 0.30), (4.3, 1.05, 0.25)):
        p.barra((0, 0, z), (math.cos(a)*l, math.sin(a)*l, z + 0.25), 0.04, 0.04, 'P_Cinza')
    return m

def junco():
    m = Modelo('junco', V, tipo='deco', descricao='Juncos do pântano e beira de lago (enfeite).'); p = m.parte(); rnd = random.Random(7)
    for i in range(7):
        x, y = rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2); h = rnd.uniform(0.35, 0.65)
        p.cil((x, y, h/2), 0.015, h, 'P_Lodo', lados=4)
        if i % 3 == 0: p.cil((x, y, h + 0.04), 0.025, 0.10, 'P_Tronco', lados=5)
    return m

def grama_tufo():
    m = Modelo('grama_tufo', V, tipo='deco', descricao='Tufo de grama (enfeite; balança com o vento no shader).'); p = m.parte(); rnd = random.Random(8)
    for i in range(6):
        a = 2*PI*i/6 + rnd.uniform(-0.3, 0.3); x, y = math.cos(a)*0.06, math.sin(a)*0.06; h = rnd.uniform(0.18, 0.30)
        p.cil((x, y, h/2), 0.025, h, 'P_FolhaClara' if i % 2 else 'P_Folha', lados=3, r2=0.0, rot=a)
    return m

def flor_luminosa():
    m = Modelo('flor_luminosa', V, tipo='deco', descricao='Flor bioluminescente (enfeite; brilha à noite).'); p = m.parte()
    for x, y, h in ((0, 0, 0.30), (0.08, 0.05, 0.22), (-0.07, 0.06, 0.18)):
        p.cil((x, y, h/2), 0.012, h, 'P_Folha', lados=4)
        p.cil((x, y, h + 0.03), 0.045, 0.06, 'P_Cristal', lados=5, r2=0.01)
    return m

# ---------------------------------------------------------------- rochas e montanhas
def _rocha(nome, w, semente, escala, n, desc, mat='P_Rocha', tipo='estrutura'):
    m = Modelo(nome, R, w, w, tipo=tipo, descricao=desc)
    if tipo == 'estrutura': bloqueio(m)
    p = m.parte(); rnd = random.Random(semente); lim = w/2 - 0.04
    for i in range(n):
        r = escala*rnd.uniform(0.55, 1.0) if i else escala
        x = rnd.uniform(-lim + r, lim - r) if i else 0; y = rnd.uniform(-lim + r, lim - r) if i else 0
        p.pedra((x, y, r*0.45), r, (1, 1, rnd.uniform(0.6, 0.9)), mat if i % 3 else 'P_RochaEscura', semente*10 + i, ruido=0.15)
    for v in p.bm.verts:
        v.co.x = max(-lim, min(lim, v.co.x)); v.co.y = max(-lim, min(lim, v.co.y))
    return apoiar(m)

def seixos():     return _rocha('seixos', 1, 31, 0.07, 4, 'Seixos soltos (enfeite).', tipo='deco')
def pedregulho(): return _rocha('pedregulho', 1, 32, 0.30, 2, 'Pedregulho (bloqueia 1 tile; dá pedra).')
def rocha_grande(): return _rocha('rocha_grande', 2, 33, 0.70, 4, 'Rocha grande 2×2 (bloqueia; dá bastante pedra).')

def _montanha(nome, w, semente, altura, desc):
    """Maciço de picos facetados (cones de 5–7 lados) com rochedos na base. Tudo dentro da área."""
    m = bloqueio(Modelo(nome, R, w, w, descricao=desc)); p = m.parte(); rnd = random.Random(semente); lim = w/2 - 0.04
    picos = [(0, 0, altura, w*0.34)]
    for i in range(5):
        a = 2*PI*i/5 + rnd.uniform(-0.4, 0.4); d = w*rnd.uniform(0.18, 0.26)
        picos.append((math.cos(a)*d, math.sin(a)*d, altura*rnd.uniform(0.45, 0.75), w*rnd.uniform(0.17, 0.23)))
    for i, (x, y, h, r) in enumerate(picos):
        lados = rnd.choice((5, 6, 7))
        vs = p.cil((x, y, h/2), r, h, 'P_Rocha' if i % 2 == 0 else 'P_RochaEscura', lados=lados, r2=r*0.12, rot=rnd.uniform(0, 1))
        for v in vs:   # torce um pouco os vértices para quebrar a simetria
            if v.co.z > 0.01: v.co.x += rnd.uniform(-0.08, 0.08)*w/3; v.co.y += rnd.uniform(-0.08, 0.08)*w/3
    p.cil((picos[0][0], picos[0][1], altura*0.93), w*0.075, altura*0.14, 'P_Cinza', lados=5, r2=0.0)   # cume claro
    for i in range(int(w*2.5)):
        a = rnd.uniform(0, 2*PI); d = w*rnd.uniform(0.34, 0.42); r = w*rnd.uniform(0.05, 0.09)
        p.pedra((math.cos(a)*d, math.sin(a)*d, r*0.4), r, (1, 1, 0.8), 'P_RochaEscura' if i % 2 else 'P_Rocha', semente*10 + i)
    for v in p.bm.verts:
        v.co.x = max(-lim, min(lim, v.co.x)); v.co.y = max(-lim, min(lim, v.co.y)); v.co.z = max(0.0, v.co.z)
    return m

def montanha_3x3(): return _montanha('montanha_3x3', 3, 41, 2.6, 'Formação de montanha 3×3 (intransponível; não dá para construir em cima).')
def montanha_5x5(): return _montanha('montanha_5x5', 5, 42, 4.2, 'Montanha 5×5 (intransponível).')

# ---------------------------------------------------------------- jazidas (1 tile; mineradas por cima)
def _jazida(nome, desc, chao, pedaco):
    m = Modelo(nome, J, descricao=desc); p = m.parte(); rnd = random.Random(hash(nome) % 1000)
    # sem base: o chão do tile de jazida é uma camada própria do terreno (textura 'jazida'), então as manchas
    # vizinhas se fundem; aqui só os pedaços de minério, espalhados pelo tile inteiro
    for i in range(6):
        a = rnd.uniform(0, 2*PI); d = rnd.uniform(0.05, 0.34); pedaco(p, math.cos(a)*d, math.sin(a)*d, i, rnd)
    for v in p.bm.verts: v.co.z = max(0.0, v.co.z)     # pedaços meio enterrados
    return m

def _pedra_com(mat_veio):
    def f(p, x, y, i, rnd):
        p.pedra((x, y, 0.05), 0.08, (1, 1, 0.7), 'P_Rocha' if i % 2 else mat_veio, 100 + i, ruido=0.2)
    return f

def _cristal(p, x, y, i, rnd):
    h = rnd.uniform(0.15, 0.32); p.cil((x, y, h/2), 0.05, h, 'P_Cristal', lados=6, r2=0.0, rot=rnd.uniform(0, 1))

def jazida_cristal(): return _jazida('jazida_cristal', 'Jazida de cristal (extrator).', 'P_RochaEscura', _cristal)
def jazida_ferro():   return _jazida('jazida_ferro', 'Jazida de ferro (broca).', 'P_Ferrugem', _pedra_com('P_Ferrugem'))
def jazida_cobre():   return _jazida('jazida_cobre', 'Jazida de cobre (broca).', 'P_RochaEscura', _pedra_com('P_Malaquita'))
def jazida_carvao():  return _jazida('jazida_carvao', 'Jazida de carvão (broca).', 'P_RochaEscura', _pedra_com('P_Carvao'))
def jazida_pedra():   return _jazida('jazida_pedra', 'Jazida de pedra (broca).', 'P_Rocha', _pedra_com('P_Pedra'))
def jazida_silex():   return _jazida('jazida_silex', 'Jazida de sílex (broca).', 'P_RochaEscura', _pedra_com('P_Silex'))
def jazida_areia():
    def f(p, x, y, i, rnd): p.cil((x, y, 0.04), 0.10, 0.08, 'P_Areia', lados=7, r2=0.04)
    return _jazida('jazida_areia', 'Duna de areia (broca).', 'P_Ferrugem', f)
def poca_seiva():
    m = Modelo('poca_seiva', J, descricao='Poça de seiva (bomba por cima). Fluido do planeta.'); p = m.parte(); rnd = random.Random(9)
    pts = [(math.cos(2*PI*k/10)*rnd.uniform(0.34, 0.44), math.sin(2*PI*k/10)*rnd.uniform(0.34, 0.44)) for k in range(10)]
    p.prisma(pts, 0, 0.03, 'P_RochaEscura')
    p.prisma([(x*0.8, y*0.8) for x, y in pts], 0.03, 0.045, 'P_Seiva')
    for i in range(4):
        a = 2*PI*i/4 + 0.4; p.pedra((math.cos(a)*0.40, math.sin(a)*0.40, 0.04), 0.05, (1, 1, 0.8), 'P_Rocha', 200 + i)
    for v in p.bm.verts:
        v.co.x = max(-0.47, min(0.47, v.co.x)); v.co.y = max(-0.47, min(0.47, v.co.y))
    return apoiar(m)

# ---------------------------------------------------------------- água (o líquido é shader do chão; aqui só enfeites)
def vitoria_regia():
    m = Modelo('vitoria_regia', A, tipo='deco', descricao='Folhas flutuantes de lago/lagoa (enfeite; boia no shader).'); p = m.parte()
    for x, y, r in ((0, 0, 0.16), (0.20, 0.10, 0.10), (-0.14, 0.16, 0.08)):
        p.cil((x, y, 0.01), r, 0.02, 'P_Folha', lados=8)
    p.cil((0.0, 0.0, 0.04), 0.03, 0.04, 'P_Biomassa', lados=5, r2=0.0)
    return m

def rocha_agua():
    return _rocha('rocha_agua', 1, 51, 0.25, 3, 'Rochas de margem/rio (bloqueia 1 tile).', mat='P_RochaEscura')

TODOS = [arvore_campina_a, arvore_campina_b, cogumelo_gigante_a, cogumelo_gigante_b, arbusto, cacto_cristal, arvore_morta,
         junco, grama_tufo, flor_luminosa, seixos, pedregulho, rocha_grande, montanha_3x3, montanha_5x5,
         jazida_cristal, jazida_ferro, jazida_cobre, jazida_carvao, jazida_pedra, jazida_silex, jazida_areia, poca_seiva,
         vitoria_regia, rocha_agua]

if __name__ == '__main__':
    rodar(TODOS, os.path.join(lib_pf.RAIZ, 'mapa', '_relatorio_mapa.json'))
