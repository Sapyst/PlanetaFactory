"""Entrada do para_jogo.py para os 5 modelos antigos do pedido 2 (docs/BRIEF_ANTIGRAVITY_2.md), estudos do Antigravity:
plataforma_agua, ponte_agua, poca_seiva, aranha_corpo/femur/tibia e ninho_aranha.

Os estudos dão sys.exit no modo "nada": este arquivo é o `script` do CONFIG, roda o estudo e segura a saída. Os remendos
ficam aqui (REMENDOS), sem mexer nos estudos.

Peças desenhadas em lote (plataforma, ponte: DesenhoPlataformas; poça: DesenhoChunk) têm de ser UMA malha, porque
`Materiais.malha_de` só pega a primeira (`_uma_malha`): as luzes viram 2ª superfície. A poça não anima: é um MultiMesh, as
bolhas do estudo saem. A seiva fica fora do assado, para não perder o brilho molhado (material P_Seiva, liso).
Aranha: 3 modelos do mesmo estudo. O jogo acha os olhos pelo nome (P_OlhoInimigo: `Aranha.definir_furia`); olhos do corpo
ficam numa malha só; na tíbia o sensor é só cor assada, para não somar 6 malhas por aranha.

Rodar: blender -b --python para_jogo.py -- <nome>; prévia montada: blender -b --python conv_antigos.py -- aranha_montada"""
import math, os, sys
import importlib.util as _iu

AQUI = os.path.dirname(os.path.abspath(__file__))
_spec = _iu.spec_from_file_location('conv_defesa_energia', os.path.join(AQUI, 'conv_defesa_energia.py'))
_de = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_de)

ESTUDOS = {'plataforma_agua': 'estudo_plataforma_agua.py', 'ponte_agua': 'estudo_ponte_agua.py', 'poca_seiva': 'estudo_poca_seiva.py',
           'aranha_corpo': 'estudo_aranha.py', 'aranha_femur': 'estudo_aranha.py', 'aranha_tibia': 'estudo_aranha.py',
           'ninho_aranha': 'estudo_ninho_aranha.py'}

_CAPAS_NINHO = """
# (conv_antigos) casca oca com duas paredes: sem tampa, o jogo (que não desenha o verso) mostra o outro lado por entre elas
for s_i in range(SEG):
    s_nxt = (s_i + 1) % SEG
    bm_base.faces.new((aneis_ext[-1][s_i], aneis_ext[-1][s_nxt], aneis_int[-1][s_nxt], aneis_int[-1][s_i]))
    if s_i in (10, 11):
        bm_base.faces.new((aneis_int[2][s_i], aneis_int[2][s_nxt], aneis_ext[2][s_nxt], aneis_ext[2][s_i]))
for a_idx in range(2):
    for s_i, inv in ((10, False), (12, True)):
        q = (aneis_ext[a_idx][s_i], aneis_int[a_idx][s_i], aneis_int[a_idx + 1][s_i], aneis_ext[a_idx + 1][s_i])
        bm_base.faces.new(q if inv else tuple(reversed(q)))

o_base = obj('ninho_base', bm_base, 'chassi_escuro')"""

_SEIVA_VELHA = """v_centro = bm_seiva.verts.new(Vector((0.0, 0.0, 0.024)))
for i in range(N_LADOS):
    ang = 2 * PI * i / N_LADOS
    dx, dy = math.cos(ang), math.sin(ang)
    r_s = raios_seiva[i] + 0.008
    v_seiva.append(bm_seiva.verts.new(Vector((dx * r_s, dy * r_s, 0.022))))

for i in range(N_LADOS):
    nxt = (i + 1) % N_LADOS
    bm_seiva.faces.new((v_centro, v_seiva[i], v_seiva[nxt]))
"""
_SEIVA_NOVA = """v_centro = bm_seiva.verts.new(Vector((0.0, 0.0, 0.040)))
v_meio = []
for i in range(N_LADOS):
    ang = 2 * PI * i / N_LADOS
    dx, dy = math.cos(ang), math.sin(ang)
    r_s = raios_seiva[i] + 0.008
    v_seiva.append(bm_seiva.verts.new(Vector((dx * r_s, dy * r_s, 0.011))))
    v_meio.append(bm_seiva.verts.new(Vector((dx * r_s * 0.72, dy * r_s * 0.72, 0.034))))

for i in range(N_LADOS):
    nxt = (i + 1) % N_LADOS
    bm_seiva.faces.new((v_seiva[i], v_seiva[nxt], v_meio[nxt], v_meio[i]))
    bm_seiva.faces.new((v_centro, v_meio[i], v_meio[nxt]))
"""

# (conv_antigos) interior do ninho: forro vermelho-escuro por dentro da parede oca; no jogo a parede por dentro saía cinza
_FORRO_NINHO = """
base3d.M['ninho_forro'] = mats.material('ForroNinho', (0.11, 0.012, 0.012), 0.0, 0.9, pintura=False, sujeira=0.5, desgaste=0.0)
bm_forro = bmesh.new()
aneis_forro = [[bm_forro.verts.new(Vector((math.cos(2 * PI * s_i / SEG) * (r_in - 0.012), math.sin(2 * PI * s_i / SEG) * (r_in - 0.012), z_p))) for s_i in range(SEG)]
               for r_in, z_p in zip(raios_int, z_alturas)]
for a_idx in range(N_ANEIS - 1):
    for s_i in range(SEG):
        s_nxt = (s_i + 1) % SEG
        if not ((a_idx < 2) and (s_i in (10, 11))):
            bm_forro.faces.new((aneis_forro[a_idx + 1][s_i], aneis_forro[a_idx + 1][s_nxt], aneis_forro[a_idx][s_nxt], aneis_forro[a_idx][s_i]))
obj('ninho_forro', bm_forro, 'ninho_forro')
"""

REMENDOS = {
    # a ponta da tíbia nascia ao contrário (cone com a base larga no pé): o pé é a agulha em x = 0,90
    'aranha_corpo': [],
    # deque do estudo saía claro e com as mesmas manchas de ferrugem em todo tile: aço escuro, quase sem ferrugem
    # (DesenhoPlataformas ainda gira cada tile, para a textura não repetir igual)
    'plataforma_agua': [("mats.material('DeckAcoGasto', (0.28, 0.30, 0.32), 0.95, 0.45, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True)",
                         "mats.material('DeckAcoGasto', (0.07, 0.075, 0.08), 0.95, 0.45, pintura=False, ferrugem=0.08, sujeira=0.5, escovado=True)")],
    'ponte_agua': [("mats.material('DeckPonteGasto', (0.28, 0.30, 0.32), 0.95, 0.45, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True)",
                    "mats.material('DeckPonteGasto', (0.07, 0.075, 0.08), 0.95, 0.45, pintura=False, ferrugem=0.08, sujeira=0.5, escovado=True)")],
    'aranha_femur': [],
    # no sol do jogo a crosta do estudo saía clara, destacando cada poça (fica mais perto do chão escuro).
    # Liam como discos separados, um por tile: agora a borda é irregular e a crosta fica ABAIXO da seiva, então a seiva da
    # poça vizinha cobre a crosta desta e várias poças viram uma mancha só (DesenhoChunk gira, desloca e aumenta cada uma). O espelho é um domo baixo: a normal curva na borda pega o brilho molhado de qualquer ângulo.
    'poca_seiva': [("mats.material('CrostaSeca', (0.18, 0.15, 0.12), 0.0, 0.85, pintura=False, sujeira=0.9, ferrugem=0.4)",
                    "mats.material('CrostaSeca', (0.028, 0.022, 0.018), 0.0, 0.85, pintura=False, sujeira=0.5, ferrugem=0.0, desgaste=0.0)"),
                   ("dy * r_ext, -0.004)", "dy * r_ext, -0.044)"),
                   ("N_LADOS = 12", "N_LADOS = 16"),
                   ("raios_crosta = [0.41 + 0.02 * math.sin(i * 2.3) for i in range(N_LADOS)]",
                    "raios_crosta = [0.37 + 0.045 * math.sin(i * 2.3) + 0.03 * math.sin(i * 4.1 + 1.0) for i in range(N_LADOS)]"),
                   ("raios_seiva = [r * 0.76 for r in raios_crosta]", "raios_seiva = [r * 0.88 for r in raios_crosta]"),
                   ("(r_ext - 0.04), dy * (r_ext - 0.04), 0.028)", "(r_ext - 0.03), dy * (r_ext - 0.03), 0.009)"),
                   ("dy * r_int, 0.025)", "dy * r_int, 0.009)"),
                   (_SEIVA_VELHA, _SEIVA_NOVA),
                   ("    (0.38, 0.08, 0.04, 0.045),\n    (-0.25, 0.32, 0.04, 0.05),\n    (-0.35, -0.15, 0.035, 0.04),\n    (0.15, -0.36, 0.035, 0.045)\n",
                    "    (0.39, 0.07, 0.012, 0.022),\n    (-0.22, 0.32, 0.012, 0.024),\n    (-0.10, -0.37, 0.012, 0.018)\n")],
    'aranha_tibia': [("radius1=0.045, radius2=0.005, depth=0.22,\n                      matrix=Matrix.Translation((TIBIA - 0.11, 0.0, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, 'Y'))",
                      "radius1=0.045, radius2=0.005, depth=0.22,\n                      matrix=Matrix.Translation((TIBIA - 0.11, 0.0, 0.0)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))")],
    # blocos de minério passavam da área 3×3 (r até 1,35 + 0,34 de pedra)
    'ninho_aranha': [("r_bloco = random.uniform(1.15, 1.35)", "r_bloco = random.uniform(1.0, 1.14)"),
                     ("\no_base = obj('ninho_base', bm_base, 'chassi_escuro')", _CAPAS_NINHO + _FORRO_NINHO),
                     # o vermelho do estudo é a LuzNinho, que não vem para o jogo: do ângulo da câmera, a boca e o topo ficavam
                     # cinza. Chão da câmara e fundo da chaminé acesos (material do bioplasma, que o jogo pulsa)
                     ("\no_nucleo = obj('nucleo_bioplasma', bm_nucleo, 'bioplasma_carmesim')",
                      "\nbm_brilho = bmesh.new()\ncil(bm_brilho, (0, 0, 0.215), 0.88, 0.03, lados=16)\ncil(bm_brilho, (0, 0, 2.05), 0.27, 0.02, lados=10)\n"
                      "obj('ninho_camara_luz', bm_brilho, 'bioplasma_carmesim')\no_nucleo = obj('nucleo_bioplasma', bm_nucleo, 'bioplasma_carmesim')")],
}


def _sem_brilho(*nomes):
    """Luz que o lote não tem como ligar nem desligar por peça: fica como cor assada."""
    import bpy
    for m in bpy.data.materials:
        if m.name.split('.')[0] in nomes:
            p = m.node_tree.nodes.get('Principled BSDF')
            for l in list(p.inputs['Emission Strength'].links):
                m.node_tree.links.remove(l)
            p.inputs['Emission Strength'].default_value = 0.0
            p.inputs['Emission Color'].default_value = (0, 0, 0, 1)


def _separar_acesos(sc):
    """Malha com slot aceso misturado: o para_jogo trataria o corpo inteiro como luz. As faces acesas viram outra malha."""
    import bpy, bmesh
    g = _de._g()
    for o in [o for o in sc.objects if o.type == 'MESH']:
        acesos = [i for i, s in enumerate(o.material_slots) if g['brilha'](s.material)]
        if not acesos or len(acesos) == len(o.material_slots):
            continue
        luz = o.copy()
        luz.data = o.data.copy()
        luz.name = o.name + '_luz'
        sc.collection.objects.link(luz)
        for ob, fica in ((o, False), (luz, True)):
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.material_index in acesos) != fica], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
            bm.to_mesh(ob.data)
            bm.free()
        mat = o.material_slots[acesos[0]].material
        luz.data.materials.clear()
        luz.data.materials.append(mat)
        for i in reversed(acesos):
            o.data.materials.pop(index=i)
        for p in luz.data.polygons:
            p.material_index = 0


def _uma_malha(sc, raiz, dados):
    """Tudo numa malha só, na origem do modelo (o lote só desenha a primeira), com as luzes como 2ª superfície."""
    import bpy
    objs = [o for o in sc.objects if o.type == 'MESH']
    corpo = next(o for o in objs if o.name.endswith('_corpo'))
    if len(objs) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = corpo
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.join()


_SEIVA = {}


def _poca_montar(sc):
    """A seiva sai do assado (viraria fosca): volta na exportação como 2ª superfície, lisa."""
    import bpy
    o = bpy.data.objects['poca_superficie']
    _SEIVA['malha'] = o.data
    o.data.use_fake_user = True
    bpy.data.objects.remove(o, do_unlink=True)


def _poca_exportar(sc, raiz, dados):
    import bpy
    me = _SEIVA['malha']
    m = bpy.data.materials.new('P_Seiva')
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.035, 0.02, 0.006, 1)   # (linear: 0,10 do estudo vira café com leite no sol do jogo)
    p.inputs['Roughness'].default_value = 0.08
    p.inputs['Metallic'].default_value = 0.0
    me.materials.clear()
    me.materials.append(m)
    o = bpy.data.objects.new('poca_seiva_superficie', me)
    sc.collection.objects.link(o)
    o.parent = raiz
    _uma_malha(sc, raiz, dados)


def _olho_do_jogo(sc, raiz, dados):
    """A fúria da aranha acha os olhos por este nome."""
    import bpy
    for m in bpy.data.materials:
        if m.name.startswith('P_Fogo'):
            m.name = 'P_OlhoInimigo'


def _so_tibia(sc):
    _sem_brilho('OlhosAranha')


CONFIG = {
    'plataforma_agua': dict(script='conv_antigos.py', args=['plataforma_agua'], estudo='estudo_plataforma_agua.py', cat='logistica/apoio',
                            tris=600, tex=512, tirar=[], anima=False, por_peca=True, antes_de_exportar=_uma_malha),
    'ponte_agua': dict(script='conv_antigos.py', args=['ponte_agua'], estudo='estudo_ponte_agua.py', cat='logistica/apoio',
                       tris=400, tex=512, tirar=[], anima=False, por_peca=True, antes_de_exportar=_uma_malha),
    'poca_seiva': dict(script='conv_antigos.py', args=['poca_seiva'], estudo='estudo_poca_seiva.py', cat='mapa/jazidas',
                       tris=300, tex=512, tirar=['bolha'], anima=False, por_peca=True,
                       depois_de_montar=_poca_montar, antes_de_exportar=_poca_exportar),
    'aranha_corpo': dict(script='conv_antigos.py', args=['aranha_corpo'], estudo='estudo_aranha.py', cat='inimigos/aranha',
                         tris=1500, tex=512, tirar=['aranha_femur', 'aranha_tibia'], anima=False, por_peca=True,
                         depois_de_montar=_separar_acesos, antes_de_exportar=_olho_do_jogo),
    'aranha_femur': dict(script='conv_antigos.py', args=['aranha_femur'], estudo='estudo_aranha.py', cat='inimigos/aranha',
                         tris=200, tex=256, tirar=['aranha_corpo', 'aranha_tibia'], anima=False, por_peca=True),
    'aranha_tibia': dict(script='conv_antigos.py', args=['aranha_tibia'], estudo='estudo_aranha.py', cat='inimigos/aranha',
                         tris=150, tex=256, tirar=['aranha_corpo', 'aranha_femur'], anima=False, por_peca=True,
                         depois_de_montar=_so_tibia),
    'ninho_aranha': dict(script='conv_antigos.py', args=['ninho_aranha'], estudo='estudo_ninho_aranha.py', cat='inimigos/aranha',
                         tris=5000, tex=1024, tirar=['EFEITO_'], por_peca=True),
}


def _rodar_estudo(nome):
    caminho = os.path.join(AQUI, ESTUDOS[nome])
    sys.argv = [sys.argv[0], '--python', caminho, '--', 'nada']
    sys.path.insert(0, AQUI)
    codigo = open(caminho, encoding='utf-8').read()
    for velho, novo in REMENDOS.get(nome, ()):
        assert velho in codigo, 'trecho não achado: ' + velho[:60]
        codigo = codigo.replace(velho, novo, 1)
    try:
        exec(compile(codigo, caminho, 'exec'), {'__name__': '__main__', '__file__': caminho})
    except SystemExit:
        pass


def _aranha_montada():
    """Prévia (só o estudo_drones.py e quem olha usam; o jogo monta com IK): corpo + 6 pernas dos .glb novos, na pose de
    repouso de MarchaAranha (pé na "casa" de cada quadril, joelho para cima, mesmo `_segmento` de Aranha)."""
    import bpy, json
    from mathutils import Vector, Matrix
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    pasta = os.path.join(AQUI, '..', 'modelos', 'inimigos', 'aranha')
    malhas = {}
    for n in ('aranha_corpo', 'aranha_femur', 'aranha_tibia'):
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(pasta, n, n + '.glb'))
        novos = [o for o in bpy.data.objects if o not in antes]
        malhas[n] = [o.data for o in novos if o.type == 'MESH']
        for o in novos:
            bpy.data.objects.remove(o, do_unlink=True)
    raiz = bpy.data.objects.new('aranha_montada', None)
    sc.collection.objects.link(raiz)

    def por(nome, me, m=Matrix.Identity(4)):
        o = bpy.data.objects.new(nome, me)
        sc.collection.objects.link(o)
        o.parent = raiz
        o.matrix_world = m

    C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # Godot (x, y, z) → Blender (x, −z, y)

    def segmento(a, b):
        x = (b - a).normalized()
        z = x.cross(Vector((0, 1, 0))).normalized()
        y = z.cross(x).normalized()
        g = Matrix(((x.x, y.x, z.x, a.x), (x.y, y.y, z.y, a.y), (x.z, y.z, z.z, a.z), (0, 0, 0, 1)))
        return C @ g @ C.inverted()

    FEMUR, TIBIA, Z, ALCANCE = 0.70, 0.90, 0.55, 1.0
    for i, me in enumerate(malhas['aranha_corpo']):
        por('aranha_montada_corpo%d' % i, me)
    for i, (hx, frente) in enumerate(((0.42, 0.35), (-0.42, 0.35), (0.42, 0.0), (-0.42, 0.0), (0.42, -0.35), (-0.42, -0.35))):
        q = Vector((hx, Z, -frente))
        rad = Vector((hx, 0, -frente)).normalized()
        pe = Vector((hx, 0, -frente)) + rad * ALCANCE
        alvo = pe - q
        d = alvo.length
        h = Vector((alvo.x, 0, alvo.z))
        elev = math.atan2(alvo.y, h.length) + math.acos((FEMUR ** 2 + d ** 2 - TIBIA ** 2) / (2 * FEMUR * d))
        joelho = q + h.normalized() * FEMUR * math.cos(elev) + Vector((0, 1, 0)) * FEMUR * math.sin(elev)
        por('aranha_montada_femur%d' % i, malhas['aranha_femur'][0], segmento(q, joelho))
        por('aranha_montada_tibia%d' % i, malhas['aranha_tibia'][0], segmento(joelho, pe))
    bpy.context.view_layer.update()
    pm = os.path.join(pasta, 'aranha_montada')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(pm, 'aranha_montada.glb'), use_selection=True, export_yup=True, export_animations=False,
                              export_image_format='JPEG')
    pts = [o.matrix_world @ v.co for o in sc.objects if o.type == 'MESH' for v in o.data.vertices]
    j = json.load(open(os.path.join(pm, 'aranha_montada.json'), encoding='utf-8'))
    tris = 0
    for o in sc.objects:
        if o.type == 'MESH':
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
    j.update(tris=tris, dims=[round(max(p[k] for p in pts) - min(p[k] for p in pts), 3) for k in range(3)], estudo='estudo_aranha.py')
    json.dump(j, open(os.path.join(pm, 'aranha_montada.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('MONTADA ok', tris, 'tris', j['dims'])


if __name__ == '__main__':
    _a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if _a and _a[0] == 'aranha_montada':
        _aranha_montada()
    elif _a and _a[0] in ESTUDOS:
        _rodar_estudo(_a[0])
