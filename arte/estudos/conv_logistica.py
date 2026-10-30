"""Entradas do para_jogo.py para a LOGÍSTICA: canos (reto, curva, T, cruz), bomba, tanque, baú, baú grande e estação.

- estudo_canos.py é uma cena conjunta (bomba → canos → tanque). `centro` traz cada peça para a origem; o gancho
  `depois_de_montar` tira o que é das peças VIZINHAS (objetos "<peça>_<material>" encostados na borda do tile, que o
  corte por área do conversor não pega) e a sujeira do conjunto (manchas, halos, espuma, respingos).
- Os canos 1×1 vão desenhados em lote (DesenhoLotes: MultiMesh com a 1ª malha do .glb): sem animação, orçamento
  baixo e tudo numa malha só (`antes_de_exportar` junta as luzinhas da paleta ao corpo).
- O cano reto do jogo é o reto "simples" do estudo (um suporte, flange nas duas pontas), que o conjunto não usa:
  este arquivo também serve de script (rodado pelo conversor como __main__) que monta o estudo e acrescenta a peça.
- estudo_baus.py: baú e baú grande lado a lado, cada um na sua coleção — fica só a coleção da peça.
- estudo_estacao.py: tira a linha (lastro, dormentes, trilhos), o vagão e a carga dele; corta as esteiras na borda
  leste (x = 0,96; dali em diante é a esteira do jogo) e os itens da fila que ficariam fora da área.
  O pórtico em balanço (cobertura, scanner, campo) passa por cima da linha e fica."""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))

# peças do conjunto do estudo_canos.py (prefixo dos objetos "<peça>_<material>")
PECAS_CANOS = ['bomba', 'reto_visor', 'reto_visor2', 't', 'curva_a', 'reto_isolado', 'reto_fole', 'curva_b', 'cruz',
               'tampao', 'tanque', 'reto_jogo']
SUJEIRA_CONJUNTO = ['halo', 'mancha', 'espuma', 'respingo']
# decalques com alfa por cor de vértice (estudo_baus.py): assados viram borrões chapados pretos — saem
DECAL_SUAVE = ['escorrido_s', 'fuligem_s', 'oleo_s', 'po_s']


def _bpy():
    import bpy
    return bpy


def _filhos_malha(o):
    return any(c.type == 'MESH' or _filhos_malha(c) for c in o.children)


def _remover(objs):
    bpy = _bpy()
    for o in list(objs):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError:
            pass


def _limpar_vazios(sc):
    """Empties que ficaram sem malha embaixo (pai de peça vizinha, animada) saem também."""
    while True:
        vaz = [o for o in sc.objects if o.type == 'EMPTY' and o.name != '_base' and not _filhos_malha(o)]
        if not vaz:
            return
        _remover(vaz)


def _centro_mundo(o):
    from mathutils import Vector
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return sum(cs, Vector()) / 8


def _sem_metal():
    """O assado é a passada DIFFUSE/COLOR: em material metálico ela sai preta (a cor do metal vai no especular).
    Antes de assar, metal vira 0 em todos os materiais — a textura leva a cor-base (o jogo usa material fosco)."""
    bpy = _bpy()
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                ent = n.inputs['Metallic']
                for l in list(ent.links):
                    m.node_tree.links.remove(l)
                ent.default_value = 0.0


def _isolar(w, d, minha, alheias=(), tirar_lote=False):
    """Tira objetos das peças vizinhas (pelo prefixo) e o que não tem dono cujo centro cai fora da área."""
    def f(sc):
        rem = []
        for o in sc.objects:
            if o.type != 'MESH':
                continue
            n = o.name
            if any(n.startswith(p + '_') for p in alheias if p != minha):
                rem.append(o)
                continue
            if any(n.startswith(p + '_') for p in alheias):
                continue                                            # da própria peça
            if any(t in n.lower() for t in SUJEIRA_CONJUNTO):
                rem.append(o)
                continue
            if tirar_lote and n.startswith('poca'):              # lote: poça repetida em todo tile fica feia
                rem.append(o)
                continue
            c = _centro_mundo(o)
            if abs(c.x) > w / 2 or abs(c.y) > d / 2:
                rem.append(o)
        _remover(rem)
        _limpar_vazios(sc)
    return f


def _so_colecao(nome):
    """Cena com dois baús: fica só a coleção da peça."""
    def f(sc):
        bpy = _bpy()
        _sem_metal()
        rem = [o for o in sc.objects if o.name != '_base' and o.type in ('MESH', 'EMPTY', 'FONT')
               and not any(c.name == nome for c in o.users_collection)]
        rem += [o for o in sc.objects if o.type == 'MESH' and 'halo' in o.name.lower()]
        _remover(rem)
        _textos_em_malha(sc)
        _limpar_vazios(sc)
        _juntar_itens(sc)
    return f


def _textos_em_malha(sc):
    """Estêncil de texto (curva FONT) vira malha: entra no corpo, é reduzido e assado como o resto."""
    bpy = _bpy()
    fs = [o for o in sc.objects if o.type == 'FONT']
    if not fs:
        return
    bpy.ops.object.select_all(action='DESELECT')
    for o in fs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fs[0]
    bpy.ops.object.convert(target='MESH')


def _brilha(m):
    p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m and m.node_tree else None
    if p is None:
        return False
    e = p.inputs['Emission Strength']
    return e.is_linked or e.default_value > 1.0


def _juntar_itens(sc):
    """Malhas filhas diretas do mesmo empty animado, sem animação própria, andam juntas: viram uma malha só
    (item flutuante, tampa + número pintado…) — menos nós e chamadas de desenho no celular. Brilho e não brilho
    ficam separados (o conversor trata a peça que brilha à parte)."""
    bpy = _bpy()
    for e in [o for o in sc.objects if o.type == 'EMPTY' and o.name != '_base']:
        grupos = {}
        for c in e.children:
            if c.type != 'MESH' or (c.animation_data and c.animation_data.action):
                continue
            b = any(_brilha(s.material) for s in c.material_slots)
            grupos.setdefault(b, []).append(c)
        for ms in grupos.values():
            if len(ms) < 2:
                continue
            bpy.ops.object.select_all(action='DESELECT')
            for m in ms:
                m.select_set(True)
            bpy.context.view_layer.objects.active = ms[0]
            bpy.ops.object.make_single_user(object=True, obdata=True)
            bpy.ops.object.join()


def _uma_malha(sc, raiz, dados):
    """Lote (MultiMesh) usa só a 1ª malha do .glb: luzinhas da paleta entram no corpo como outra superfície."""
    bpy = _bpy()
    _paleta(sc, raiz, dados)
    ms = [o for o in sc.objects if o.type == 'MESH']
    if len(ms) > 1:
        corpo = next((o for o in ms if o.name.endswith('_corpo')), ms[0])
        bpy.ops.object.select_all(action='DESELECT')
        for o in ms:
            o.select_set(True)
        bpy.context.view_layer.objects.active = corpo
        bpy.ops.object.join()
    # empties que sobraram sem malha (pivô do ponteiro do manômetro, _base): fora, com a animação deles
    _remover([o for o in sc.objects if o.type == 'EMPTY' and o is not raiz and not o.name.startswith('PORTA_')
              and not _filhos_malha(o)])


def _paleta(sc, raiz, dados):
    """O conversor cria um P_Fogo/P_Cristal por peça que brilha (P_Fogo.001…); o jogo liga o pulso pelo nome
    exato, então todas apontam para o primeiro de cada nome."""
    bpy = _bpy()
    for o in sc.objects:
        if o.type != 'MESH':
            continue
        for s in o.material_slots:
            m = s.material
            if m and '.' in m.name and m.name.split('.')[0] in ('P_Fogo', 'P_Cristal'):
                base = bpy.data.materials.get(m.name.split('.')[0])
                if base:
                    s.material = base


# partes que o Animador do jogo mexe pelo sufixo do nome (<modelo>_<parte>): nada do estudo pode cair nelas
PARTES_ANIMADOR = {'hastes', 'cristal', 'rotor', 'antena', 'nacele', 'helice', 'cabecote', 'braco', 'braco1', 'braco2',
                   'garra', 'giro', 'canhao'}


def _neutro(sc, raiz, dados):
    """Empties animados do estudo (braços da estação, itens do baú…) e malhas com sufixo perigoso ganham nome
    neutro: quem os mexe é a animação "trabalho" do estudo, não o Animador (a IK do jogo é de um braço só, guiado
    pela regra do Braço, e não serve para os dois braços da estação)."""
    _paleta(sc, raiz, dados)
    _juntar_brilhos_fixos(sc, raiz)
    nome = raiz.name
    i = 0
    for o in list(sc.objects):
        if o is raiz or o.name.startswith('PORTA_'):
            continue
        suf = o.name.split('.')[0].rsplit('_', 1)[-1].lower()
        if o.type == 'EMPTY' or suf in PARTES_ANIMADOR or suf.startswith('pistao'):
            o.name = '%s_%s%d' % (nome, 'e' if o.type == 'EMPTY' else 'b', i)
            i += 1


def _juntar_brilhos_fixos(sc, raiz):
    """Peças que brilham e não se mexem (etiquetas, barras de luz, LEDs), filhas diretas da raiz ou do _base: uma malha por
    material da paleta em vez de uma por peça."""
    bpy = _bpy()
    grupos = {}
    for o in sc.objects:
        if (o.type == 'MESH' and o.parent is not None and (o.parent is raiz or o.parent.name == '_base')
                and not o.name.endswith('_corpo')
                and not (o.animation_data and (o.animation_data.action or o.animation_data.nla_tracks))
                and o.material_slots and all(s.material and s.material.name.startswith('P_') for s in o.material_slots)):
            grupos.setdefault(o.material_slots[0].material.name, []).append(o)
    for ms in grupos.values():
        if len(ms) < 2:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for m in ms:
            m.select_set(True)
        bpy.context.view_layer.objects.active = ms[0]
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.join()


def _cano(minha, w=1, d=1, x=0.0, y=0.0, rot=0.0, script='estudo_canos.py', args=None, tris=900):
    return dict(script=script, args=args or ['nada'], cat='logistica/canos', tris=tris, tex=512, anima=False,
                tirar=list(SUJEIRA_CONJUNTO), centro=(x, y, rot), margem=0.06,
                depois_de_montar=_isolar(w, d, minha, PECAS_CANOS, tirar_lote=True), antes_de_exportar=_uma_malha)


# ------------------------------------------------------------------ estação
def _estacao_depois(sc):
    """Tira linha e vagão (fundidos por material com a estação: sai por ilha de malha), corta as esteiras na borda
    leste e tira os itens da fila que andariam fora da área."""
    bpy = _bpy()
    import bmesh
    from mathutils import Vector
    _sem_metal()
    fora = ('minerio_4', 'minerio_5', 'chapas_3', 'chapas_4', 'monte')
    rem = [o for o in sc.objects if any(o.name == f or o.name.startswith(f + '_') or o.name.startswith(f + '.')
                                        for f in fora)]
    # campo da IA (emissão + transparência, sem Principled): assado vira um cilindro preto opaco sobre a linha
    rem += [o for o in sc.objects if o.type == 'MESH' and any(s.material and s.material.name.startswith('Campo')
                                                              for s in o.material_slots)]
    _remover(rem)
    e = sc.objects.get('estacao')                     # o empty raiz do estudo tomaria o nome da raiz do conversor
    if e is not None:
        e.name = 'est_raiz'
    _textos_em_malha(sc)
    for o in [o for o in sc.objects if o.type == 'MESH']:
        for m in list(o.modifiers):
            if m.type in ('BEVEL', 'SOLIDIFY'):           # telha com espessura assava escura (o raio pegava o verso)
                o.modifiers.remove(m)
        if o.modifiers:
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.make_single_user(object=True, obdata=True)
            for m in list(o.modifiers):
                bpy.ops.object.modifier_apply(modifier=m.name)
    for o in [o for o in sc.objects if o.type == 'MESH' and (o.name.startswith('estacao_') or o.name.startswith('telha_'))]:
        if o.data.users > 1:
            o.data = o.data.copy()
        mw = o.matrix_world.copy()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(mw)
        # ilhas da linha e do vagão: inteiras a oeste da laje e baixas (o balanço do pórtico fica alto)
        vistos = set()
        apagar = []
        for f0 in bm.faces:
            if f0.index in vistos:
                continue
            ilha, pilha = [], [f0]
            vistos.add(f0.index)
            while pilha:
                f = pilha.pop()
                ilha.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g.index not in vistos:
                            vistos.add(g.index)
                            pilha.append(g)
            vs = {v for f in ilha for v in f.verts}
            cx = sum(v.co.x for v in vs) / len(vs)
            if cx < -0.96 and max(v.co.z for v in vs) < 0.95:          # (brita da borda passa um pouco de x)
                apagar.extend(ilha)
        bmesh.ops.delete(bm, geom=list(set(apagar)), context='FACES')
        # esteiras: daqui para leste é a esteira do jogo
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0.975, 0, 0)),
                               plane_no=Vector((1, 0, 0)), clear_outer=True)
        soltos = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=soltos, context='VERTS')
        bm.transform(mw.inverted())
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    # rolos das esteiras que ficaram além da borda
    _remover([o for o in sc.objects if o.type == 'MESH' and '_rolo_' in o.name and _centro_mundo(o).x > 0.975])
    _remover([o for o in sc.objects if o.type == 'MESH' and not o.data.polygons])
    _limpar_vazios(sc)
    _juntar_itens(sc)                                 # peças de cada elo do braço, rolo, item: uma malha por elo


CONFIG = {
    'cano_reto': _cano('reto_jogo', x=20.0, script='conv_logistica.py', args=['cano_reto'], tris=600),
    'cano_curva': _cano('curva_a', x=0.0, y=3.0),
    'cano_t': _cano('t', x=0.0, y=2.0, tris=1600),
    'cano_cruz': _cano('cruz', x=2.0, y=3.0, tris=1600),
    'bomba': dict(script='estudo_canos.py', cat='logistica/canos', tris=3000, tex=1024, centro=(0.0, 0.0, 0.0),
                  tirar=list(SUJEIRA_CONJUNTO), depois_de_montar=_isolar(1, 1, 'bomba', PECAS_CANOS),
                  antes_de_exportar=_paleta),
    'tanque': dict(script='estudo_canos.py', cat='energia', tris=4000, tex=1024, centro=(4.5, 3.5, 0.0),
                   tirar=list(SUJEIRA_CONJUNTO), depois_de_montar=_isolar(2, 2, 'tanque', PECAS_CANOS),
                   antes_de_exportar=_paleta),
    'bau': dict(script='estudo_baus.py', cat='logistica/armazenagem', tris=3000, tex=1024, centro=(-1.0, -0.5, 0.0),
                tirar=['halo'] + DECAL_SUAVE, depois_de_montar=_so_colecao('bau'), antes_de_exportar=_neutro),
    'bau_grande': dict(script='estudo_baus.py', cat='logistica/armazenagem', tris=6000, tex=1024, centro=(0.5, 0.0, 0.0),
                       tirar=['halo'] + DECAL_SUAVE, depois_de_montar=_so_colecao('bau_grande'),
                       antes_de_exportar=_neutro),
    'estacao': dict(script='estudo_estacao.py', cat='transporte/trilhos', tris=9000, tex=1024, margem=1.2,
                    tirar=[], depois_de_montar=_estacao_depois, antes_de_exportar=_neutro),
}


# ------------------------------------------------------------------ como script: estudo de canos + reto simples
def _montar_reto_simples():
    from mathutils import Vector
    estudo = os.path.join(AQUI, 'estudo_canos.py')
    sys.argv = [sys.argv[0], '--python', estudo, '--', 'nada']
    g = {'__name__': '__main__', '__file__': estudo}
    exec(compile(open(estudo, encoding='utf-8').read(), estudo, 'exec'), g)
    CZ, R = g['CZ'], g['R']
    P = g['Peca']('reto_jogo', 20.0, 0.0, 0)
    C = lambda y: Vector((0, y, CZ))
    g['flange'](P, C(-0.5), (0, -1, 0))
    g['flange'](P, C(0.5), (0, 1, 0))
    g['tubo'](P.B('cano', True), C(-0.47), C(0.47), R, 32)
    g['suporte'](P, C(0.0), (0, 1, 0))
    g['serie'](P, C(-0.3), (0, 1, 0), R, math.radians(30), 4, 0.025)
    g['remendo'](P, C(0.27), (0, 1, 0), R, math.radians(100), math.radians(165), 0.07)
    P.fim()


if __name__ == '__main__':
    _montar_reto_simples()
