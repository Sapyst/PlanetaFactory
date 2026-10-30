"""Entradas do para_jogo.py para defesa e rede de energia: torre_defesa, turbina_eolica, poste_energia, torre_sem_fio,
muro_centro e muro_lado (estudos estudo_torre_defesa.py, estudo_turbina_eolica.py e estudo_poste_muro.py).

O que os ganchos fazem (o para_jogo.py não muda):
- torre_defesa: a cabeça do estudo aponta o canhão para +X; o jogo mira com o canhão em +Y do Blender (−Z do Godot)
  quando o giro está em 0. Os ganchos tiram a animação do estudo, viram a cabeça para +Y e separam as peças por
  hierarquia: giro (cabeça, pistões, varredor) e canhao (canhão + cano). LEDs/olho viram parte "luzg" (filha do giro,
  material da paleta, brilha). Os pistões do estudo ligam a cabeça ao berço do canhão (quase horizontais): ficam
  fixos dentro do giro — o vai-e-vem vertical do Animador (pistao0/1) os soltaria do canhão.
- turbina_eolica: a hélice do estudo fica em +X; o jogo quer a hélice em −Y do Blender (gira no eixo Z do Godot) com
  a nacele em 0. Os ganchos viram a nacele −90°, tiram a animação e separam nacele / helice (+ luzes violeta
  "luzn"/"luzh" filhas de cada uma, para continuarem brilhando).
- poste_energia / torre_sem_fio: cena conjunta; fica só o grupo da peça (coleção "poste"/"torre"), sem cabos que
  vão para longe, arcos, faíscas e halos. O poste grava `terminais` = topo dos três isoladores (o fio prende no
  isolador virado para o outro lado, ver Fiacao.ponto_fio). A torre mantém a parte `cristal` (pulsa) com o pivô no
  centro do cristal; o feixe sem fio continua saindo do topo (dims − 0,12 m = cristal).
- muro_centro / muro_lado: o estudo é rico demais para 400–900 triângulos (pedras soltas). O gancho troca a malha
  baixa por uma casca simples na silhueta (caixas, pingadeira, espetos, arame) e o para_jogo assa nela a cor do
  modelo detalhado. O pilar é refeito sem pano em nenhum lado (o jogo junta os panos por vizinho).
Rodar: blender -b --python para_jogo.py -- <nome>"""
import bpy, bmesh, math, gc, sys
from mathutils import Vector, Matrix

PI = math.pi


# ------------------------------------------------------------------ utilidades
def _g():
    """Globais do para_jogo.py (quem chamou o gancho): brilha, vidro, reduzir…"""
    f = sys._getframe(1)
    while f is not None:
        if 'montar_estudo' in f.f_globals and 'reduzir' in f.f_globals:
            return f.f_globals
        f = f.f_back
    raise RuntimeError('para_jogo.py não encontrado na pilha')


def _apagar(o):
    for c in list(o.children):
        _apagar(c)
    bpy.data.objects.remove(o, do_unlink=True)


def _vivos(sc):
    """Objetos da cena por nome (apagar um pai apaga os filhos: a lista seguinte não pode guardar referência morta)."""
    for nome in [o.name for o in sc.objects]:
        o = bpy.data.objects.get(nome)
        if o is not None:
            yield o


def _sem_animacao(sc):
    for o in sc.objects:
        o.animation_data_clear()


def _descendentes(o):
    out = []
    for c in o.children:
        out.append(c)
        out += _descendentes(c)
    return out


def _marcar(raiz, fosco, luz, g, pular=()):
    """Renomeia as malhas sob `raiz` com um prefixo único (as partes do para_jogo pegam objetos por substring):
    `fosco` para as que vão ser assadas, `luz` para as que brilham (viram material da paleta)."""
    fora = set()
    for p in pular:
        fora |= {p} | set(_descendentes(p))
    n = 0
    for o in _descendentes(raiz):
        if o.type != 'MESH' or o in fora:
            continue
        br = any(g['brilha'](s.material) for s in o.material_slots)
        o.name = (luz if br else fosco) + o.name
        n += 1
    return n


def _tirar(sc, *subs):
    for o in _vivos(sc):
        if any(s in o.name.lower() for s in subs):
            _apagar(o)


def _so_colecao(sc, nome):
    for o in _vivos(sc):
        if o.type != 'EMPTY' and nome not in [c.name for c in o.users_collection]:
            _apagar(o)


def _limite_brilho(g, alvo_brilho, proxy=None, nome_corpo=None):
    """Troca o `reduzir` do para_jogo: peça que brilha (alvo 300) vai a `alvo_brilho`; o corpo, se houver `proxy`,
    vira a casca simples (bmesh em coordenadas do mundo) em vez de ser dizimado."""
    orig = g['reduzir']

    def reduzir(o, alvo):
        if proxy is not None and o.name == nome_corpo:
            bm = proxy()
            bm.transform(o.matrix_world.inverted())
            bm.to_mesh(o.data)
            bm.free()
            o.data.update()
            return
        if alvo == 300:                                # peça que brilha
            orig(o, alvo_brilho)
            return
        _enxugar(o)
        orig(o, alvo)
    g['reduzir'] = reduzir


# decalques (planos finos sobre a superfície): só valem na cor assada, não na malha baixa
DECALQUES = {'lama', 'fenda', 'escorrido de ferrugem', 'crosta de ferrugem', 'musgo', 'chamuscado', 'musgo (mancha)',
             'ácido (mancha)', 'ácido das aranhas', 'estêncil apagado', 'remendo de argamassa', 'óleo',
             'mancha de sujeira', 'zinabre', 'queimado de arco', 'crosta de eletrólito', 'chamusco', 'pó', 'fuligem',
             'escorrido', 'mancha de ferrugem', 'terra', 'brita', 'listras', 'faixa refletiva', 'plaqueta'}


def _enxugar(o, menor=0.045):
    """Malha baixa sem o miúdo: ilhas soltas com diagonal < `menor` (parafusos, porcas, LEDs, pedrinhas) e
    decalques. Com o orçamento indo só para as formas grandes, a redução não as desmancha; o detalhe tirado
    continua no modelo alto e entra na textura assada."""
    mats = [(s.material.name.lower().split('.')[0] if s.material else '') for s in o.material_slots]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    visto = set()
    fora = []
    for f in bm.faces:
        if f.index in visto:
            continue
        ilha, pilha = [], [f]
        visto.add(f.index)
        while pilha:
            x = pilha.pop()
            ilha.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in visto:
                        visto.add(y.index)
                        pilha.append(y)
        vs = {v for x in ilha for v in x.verts}
        lo = Vector((min(v.co.x for v in vs), min(v.co.y for v in vs), min(v.co.z for v in vs)))
        hi = Vector((max(v.co.x for v in vs), max(v.co.y for v in vs), max(v.co.z for v in vs)))
        decal = all(mats[x.material_index] in DECALQUES for x in ilha if x.material_index < len(mats))
        if (hi - lo).length < menor or decal:
            fora += ilha
    if fora and len(fora) < len(bm.faces):
        bmesh.ops.delete(bm, geom=fora, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(o.data)
        o.data.update()
    bm.free()


# ------------------------------------------------------------------ torre de defesa
def torre_defesa_montar(sc):
    g = _g()
    _sem_animacao(sc)                                 # pose do quadro 1; a faixa de carga fica parada
    giro = bpy.data.objects['giro']
    canhao = bpy.data.objects['canhao']
    giro.rotation_euler = (0, 0, PI / 2)              # canhão do estudo em +X → +Y (frente do jogo)
    bpy.context.view_layer.update()
    _marcar(canhao, 'PCAN__', 'PCLUZ__', g)
    _marcar(giro, 'PGIRO__', 'PGLUZ__', g, pular=(canhao,))
    _limite_brilho(g, 120)


def torre_defesa_exportar(sc, raiz, dados):
    dados['descricao'] = ('torre de defesa: pedestal octogonal blindado, banco de capacitores ao norte, cabeça '
                          'giratória com sensor e canhão de trilho duplo (railgun). Munição de reserva entra pelo sul. '
                          'Partes: base, giro (gira em Z), canhao (filho do giro), luzg (LEDs da cabeça).')


# ------------------------------------------------------------------ turbina eólica
def turbina_montar(sc):
    g = _g()
    _sem_animacao(sc)
    nacele = bpy.data.objects['nacele']
    helice = bpy.data.objects['helice']
    nacele.rotation_euler = (0, 0, -PI / 2)           # hélice do estudo em +X → −Y (frente do vento no jogo)
    helice.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    _marcar(helice, 'PHEL__', 'PHLUZ__', g)
    _marcar(nacele, 'PNAC__', 'PNLUZ__', g, pular=(helice,))
    _limite_brilho(g, 160)


def turbina_exportar(sc, raiz, dados):
    # fio prende em cima dos blocos de ancoragem dos cantos (±0,80; topo 0,18 + olhal): o terminal do modelo antigo
    # (±0,85 a 0,372 m) ficava solto no ar. Quatro cantos: o fio sempre chega pelo lado de fora, sem cruzar a torre.
    dados['terminais'] = [[sx * 0.8, sy * 0.8, 0.22] for sx in (-1, 1) for sy in (-1, 1)]


# ------------------------------------------------------------------ poste de energia
ISO_X = (-0.29, -0.13, 0.29)
Y_ARM = -0.095
Z_ISO = 1.98 + 0.119 + 0.0055                         # topo do pino do isolador (isolador_pt do estudo)


def poste_montar(sc):
    g = _g()
    _so_colecao(sc, 'poste')
    _sem_animacao(sc)
    _tirar(sc, '_cond', 'fsc_', 'halo', 'arco', 'poca_oleo', 'brita', 'musgo', 'lama')
    _limite_brilho(g, 100)


def poste_exportar(sc, raiz, dados):
    dados['terminais'] = [[x, Y_ARM, round(Z_ISO, 3)] for x in ISO_X]
    dados['descricao'] = ('Poste de energia: poste de concreto numa luva de aço, cruzeta com três isoladores (o fio '
                          'prende neles: "terminais"), transformador, captor com anel de campo. Ocupa só o centro do tile.')


# ------------------------------------------------------------------ torre sem fio
def torre_sf_montar(sc):
    g = _g()
    _so_colecao(sc, 'torre')
    _sem_animacao(sc)
    _tirar(sc, 'arco', 'fsc_', 'halo', 'brita')
    cr = bpy.data.objects['torre_cristal']
    cs = [cr.matrix_world @ Vector(c) for c in cr.bound_box]
    c = sum(cs, Vector()) / 8
    CONFIG['torre_sem_fio']['partes']['cristal']['pivo'] = (round(c.x, 3), round(c.y, 3), round(c.z, 3))
    _limite_brilho(g, 100)


# ------------------------------------------------------------------ muro (casca simples + cor assada do estudo)
LO, UP = 0.305, 0.25
Z_REC, Z_UP, Z_PIL = 0.72, 0.80, 1.38
Z_PANO = 1.10


def _caixa(bm, a, b):
    a, b = Vector(a), Vector(b)
    vs = [bm.verts.new((x, y, z)) for z in (a.z, b.z) for (x, y) in ((a.x, a.y), (b.x, a.y), (b.x, b.y), (a.x, b.y))]
    bm.faces.new(vs[3::-1])
    bm.faces.new(vs[4:])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))


def _tronco(bm, z0, z1, a0, a1):
    vs = [bm.verts.new((sx * a, sy * a, z)) for (z, a) in ((z0, a0), (z1, a1)) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))


def _espeto(bm, c, r, h):
    c = Vector(c)
    base = [bm.verts.new(c + Vector((math.cos(a) * r, math.sin(a) * r, 0))) for a in (PI / 4 + k * PI / 2 for k in range(4))]
    topo = bm.verts.new(c + Vector((0, 0, h)))
    for i in range(4):
        bm.faces.new((base[i], base[(i + 1) % 4], topo))


def _prisma(bm, c, r, z0, z1, n=8):
    c = Vector(c)
    an = [k * 2 * PI / n for k in range(n)]
    b = [bm.verts.new((c.x + math.cos(a) * r, c.y + math.sin(a) * r, z0)) for a in an]
    t = [bm.verts.new((c.x + math.cos(a) * r, c.y + math.sin(a) * r, z1)) for a in an]
    bm.faces.new(list(reversed(b)))
    bm.faces.new(t)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))


def casca_pilar():
    bm = bmesh.new()
    _caixa(bm, (-0.32, -0.32, 0.0), (0.32, 0.32, 0.05))
    _caixa(bm, (-LO - 0.005, -LO - 0.005, 0.05), (LO + 0.005, LO + 0.005, Z_REC))
    _tronco(bm, Z_REC, Z_UP, 0.318, UP)
    _caixa(bm, (-UP, -UP, Z_UP), (UP, UP, Z_PIL))
    _caixa(bm, (-0.272, -0.272, Z_PIL), (0.272, 0.272, Z_PIL + 0.06))
    zt = Z_PIL + 0.06
    _caixa(bm, (-0.255, -0.255, zt), (0.255, 0.255, zt + 0.012))
    for qd in range(4):
        R = Matrix.Rotation(qd * PI / 2, 3, 'Z')
        for i in range(5):
            if qd == 1 and i == 1:
                continue
            _espeto(bm, R @ Vector((-0.17 + i * 0.085, 0.235, zt + 0.012)), 0.011, 0.046)
    _prisma(bm, (0, 0, 0), 0.055, zt + 0.012, zt + 0.02)
    _prisma(bm, (0, 0, 0), 0.036, zt + 0.02, zt + 0.042)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def casca_pano():
    """Pano local: do centro até a borda norte (y 0,23 … 0,5)."""
    bm = bmesh.new()
    _caixa(bm, (-0.11, 0.30, 0.0), (0.11, 0.5, 0.05))
    _caixa(bm, (-0.10, 0.23, 0.05), (0.10, 0.5, Z_PANO))
    zc = Z_PANO + 0.055
    _caixa(bm, (-0.105, 0.24, Z_PANO), (0.105, 0.5, zc))
    for yy in (0.31, 0.46):
        for sx in (-1, 1):
            _espeto(bm, (sx * 0.06, yy, zc), 0.009, 0.044)
    _caixa(bm, (-0.012, 0.388, zc), (0.012, 0.412, 1.262))           # mourão do arame
    for zz in (1.2, 1.242):
        _caixa(bm, (-0.0035, 0.254, zz - 0.0035), (0.0035, 0.5, zz + 0.0035))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _funcao_estudo(nome):
    for f in gc.get_objects():
        if callable(f) and getattr(f, '__name__', '') == nome and getattr(getattr(f, '__code__', None), 'co_filename', '').endswith('estudo_poste_muro.py'):
            return f
    raise RuntimeError('função do estudo não achada: ' + nome)


def muro_centro_montar(sc):
    g = _g()
    for o in _vivos(sc):                              # cena conjunta: refaz só o pilar, sem pano em lado nenhum
        if o.type in ('MESH', 'EMPTY'):
            _apagar(o)
    _funcao_estudo('muro_centro')('muro_cx', 0.0, 0.0, (), 30, 2)
    _sem_animacao(sc)
    for o in _vivos(sc):
        if o.type == 'MESH' and any(g['vidro'](s.material) or g['tem_volume'](s.material) for s in o.material_slots):
            _apagar(o)
    _limite_brilho(g, 80, casca_pilar, 'muro_centro_corpo')


def muro_lado_montar(sc):
    g = _g()
    for o in _vivos(sc):
        if o.type == 'MESH' and not o.name.startswith('muro_l2_0'):
            _apagar(o)
    _sem_animacao(sc)
    _limite_brilho(g, 80, casca_pano, 'muro_lado_corpo')


# ------------------------------------------------------------------ entradas
CONFIG = {
    'torre_defesa': dict(
        script='estudo_torre_defesa.py', cat='defesa', tris=6000, tex=1024, corpo='base',
        tirar=['capsula', 'laser', 'fumaca', 'vapor', 'fiapo', 'plasma'],
        depois_de_montar=torre_defesa_montar, antes_de_exportar=torre_defesa_exportar,
        partes={
            'giro': dict(objetos=['PGIRO__'], pivo=(0.0, 0.0, 0.64), pai='base', tris=1400),
            'luzg': dict(objetos=['PGLUZ__'], pivo=(0.0, 0.0, 0.64), pai='giro', tris=160),
            'canhao': dict(objetos=['PCAN__'], pivo=(0.0, 0.05, 1.10), pai='giro', tris=1100),
        }),
    'turbina_eolica': dict(
        script='estudo_turbina_eolica.py', cat='energia', tris=6000, tex=1024,
        tirar=['pas_campo'],
        depois_de_montar=turbina_montar, antes_de_exportar=turbina_exportar,
        partes={
            'nacele': dict(objetos=['PNAC__'], pivo=(0.0, 0.0, 2.64), pai='corpo', tris=1500),
            'luzn': dict(objetos=['PNLUZ__'], pivo=(0.0, 0.0, 2.64), pai='nacele', tris=200),
            'helice': dict(objetos=['PHEL__'], pivo=(0.0, -0.5, 2.81), pai='nacele', tris=1500),
            'luzh': dict(objetos=['PHLUZ__'], pivo=(0.0, -0.5, 2.81), pai='helice', tris=240),
        }),
    'poste_energia': dict(
        script='estudo_poste_muro.py', cat='energia', tris=1400, tex=512, anima=False, tirar=[],
        depois_de_montar=poste_montar, antes_de_exportar=poste_exportar),
    'torre_sem_fio': dict(
        script='estudo_poste_muro.py', cat='energia', tris=1800, tex=512, anima=False, tirar=[],
        depois_de_montar=torre_sf_montar,
        partes={'cristal': dict(objetos=['torre_cristal'], pivo=(0.0, 0.0, 2.75), pai='corpo', tris=120)}),
    'muro_centro': dict(
        script='estudo_poste_muro.py', cat='defesa', tris=900, tex=512, anima=False, tirar=[],
        depois_de_montar=muro_centro_montar),
    'muro_lado': dict(
        script='estudo_poste_muro.py', cat='defesa', tris=500, tex=512, anima=False, tirar=[], centro=(2.0, 0.0),
        depois_de_montar=muro_lado_montar),
}
