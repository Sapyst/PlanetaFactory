"""Converte um estudo isolado (Cycles, alto detalhe) no modelo do jogo (celular).
Monta a cena do estudo sem renderizar, tira o que é cenário/efeito (câmera, luzes, chão, volumes, vidro, o que fica
fora da área), separa o que se mexe do que é fixo, reduz a malha ao orçamento, ASSA a cor de tudo (sujeira inclusa)
numa textura só a partir do modelo detalhado, mantém as peças que brilham com material da paleta (P_Cristal/P_Fogo,
o jogo pulsa) e exporta o .glb com a animação de 4 s do estudo ("trabalho", o jogo toca em laço enquanto a máquina
trabalha) e o .json com as portas e a área que o jogo já usa.
Uso: blender -b --python para_jogo.py -- <nome>      (nome em CONFIG; mais entradas em conv_*.py, que definem CONFIG)

Opções de CONFIG além de script/cat/tris/tex/tirar:
  args      argumentos do estudo (padrão ['nada'])
  centro    (x, y[, rot_z]) onde a estrutura está na cena do estudo (cena com várias): ela vem para a origem e só
            fica o que está dentro da área dela
  margem    folga (m) além da área antes de tirar o que está fora (padrão 0,06)
  anima     False = tudo fixo (peças desenhadas em lote: esteira, cano, trilho, muro)
  corpo     nome da parte fixa (padrão 'corpo'; a torre usa 'base')
  partes    {nome: dict(objetos=[substrings], pivo=(x, y, z), pai='corpo', tris=n)}: peças que o JOGO mexe pelo nome
            (giro, canhao, nacele, helice, braco1...) — sem a animação do estudo, com pivô para o Animador
  depois_de_montar(sc)       função chamada com a cena já na origem e limpa (ajustes do estudo: tirar, mover, renomear)
  antes_de_exportar(sc, raiz, dados)  função chamada antes do .glb (ex.: material especial da lona; dados = .json)

Sempre (para todo estudo):
- texto (curva FONT) vira malha antes da limpeza: entra no corpo, é reduzido e assado;
- mancha transparente (alfa vindo da cor de vértice/atributo: decalque que se desfaz na borda) sai — assada, viraria
  um borrão chapado;
- malhas filhas diretas do mesmo empty, sem animação própria, andam juntas: viram uma (menos nós/chamadas de desenho);
  peças que brilham e não se mexem ficam uma malha por material da paleta;
- o assado é a passada DIFFUSE/COLOR, que sai preta em material metálico: metal vai a 0 antes de assar (o jogo usa
  material fosco com a cor assada);
- material da paleta é um por cor (P_Fogo, P_Fogo.001…; o jogo lê o nome sem o sufixo)."""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELOS = os.path.abspath(os.path.join(AQUI, '..', 'modelos'))

# nome do jogo → estudo, categoria, orçamento de triângulos, lado da textura, nomes de objeto a tirar (substring)
CONFIG = {
    'fornalha': dict(script='estudo_fornalha.py', cat='maquinas', tris=9000, tex=1024,
                     tirar=['chao', 'fumaca', 'vapor', 'faisca', 'jato', 'vazamento']),
}
# máquinas que já existem no jogo e só trocam o visual (estudo de uma estrutura só na cena)
for _n, _s, _c, _t in (('broca_minerio', 'estudo_broca.py', 'maquinas', 8000), ('montadora', 'estudo_montadora.py', 'maquinas', 11000),
                       ('extrator_cristal', 'estudo_extrator_cristal.py', 'maquinas', 10000),
                       ('refinador', 'estudo_refinador.py', 'maquinas', 11000), ('laboratorio', 'estudo_laboratorio.py', 'maquinas', 10000),
                       ('terraplenagem', 'estudo_terraplenagem.py', 'maquinas', 10000), ('gerador', 'estudo_gerador.py', 'energia', 8000),
                       ('painel_solar', 'estudo_painel_solar.py', 'energia', 5000), ('acumulador', 'estudo_acumulador.py', 'energia', 7000),
                       ('coletor_lixo', 'estudo_coletor_lixo.py', 'maquinas', 8000), ('filtro_agua', 'estudo_filtro_agua.py', 'maquinas', 8000),
                       ('viveiro', 'estudo_viveiro.py', 'maquinas', 8000), ('nucleo', 'estudo_nucleo.py', 'maquinas', 12000)):
    CONFIG[_n] = dict(script=_s, cat=_c, tris=_t, tex=1024, tirar=[])
import glob as _glob, importlib.util as _iu
for _f in sorted(_glob.glob(os.path.join(AQUI, 'conv_*.py'))):
    _spec = _iu.spec_from_file_location(os.path.basename(_f)[:-3], _f)
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    CONFIG.update(getattr(_mod, 'CONFIG', {}))
EFEITO = ('chao', 'ceu', 'terreno', 'fumaca', 'vapor', 'poeira', 'nevoa', 'faisca', 'jato', 'fogo', 'chama', 'raio',
          'chuva', 'gota', 'feixe', 'clarao', 'onda', 'rastro')


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return a[0] if a else 'fornalha'


def montar_estudo(cfg):
    """Roda o script do estudo num modo que não renderiza (constrói a cena e a animação)."""
    caminho = os.path.join(AQUI, cfg['script'])
    sys.argv = [sys.argv[0], '--python', caminho, '--'] + list(cfg.get('args', ['nada']))
    sys.path.insert(0, AQUI)
    codigo = open(caminho, encoding='utf-8').read()
    exec(compile(codigo, caminho, 'exec'), {'__name__': '__main__', '__file__': caminho})


def tem_volume(m):
    if not m or not m.use_nodes:
        return False
    return any(n.type == 'OUTPUT_MATERIAL' and n.inputs['Volume'].is_linked for n in m.node_tree.nodes)


def principled(m):
    if not m or not m.use_nodes:
        return None
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def brilha(m):
    p = principled(m)
    if p is None:
        return False
    e = p.inputs['Emission Strength']
    return e.is_linked or e.default_value > 1.0


def vidro(m):
    p = principled(m)
    if p is None:
        return False
    t = p.inputs.get('Transmission Weight') or p.inputs.get('Transmission')
    a = p.inputs['Alpha']
    return (t is not None and (t.is_linked or t.default_value > 0.5)) or (not a.is_linked and a.default_value < 0.6)


def mancha_suave(m):
    """Alfa que vem da cor de vértice/atributo (decalque que some na borda): sem alfa no assado vira borrão chapado."""
    p = principled(m)
    if p is None or not p.inputs['Alpha'].is_linked:
        return False
    pilha, visto = [l.from_node for l in p.inputs['Alpha'].links], set()
    while pilha:
        n = pilha.pop()
        if n.name in visto:
            continue
        visto.add(n.name)
        if n.type in ('VERTEX_COLOR', 'ATTRIBUTE'):
            return True
        pilha += [l.from_node for i in n.inputs for l in i.links]
    return False


def textos_em_malha():
    """Estêncil de texto (curva FONT) vira malha: entra no corpo e é assado como o resto."""
    sc = bpy.context.scene
    fs = [o for o in sc.objects if o.type == 'FONT' and o.visible_get()]
    if not fs:
        return
    bpy.ops.object.select_all(action='DESELECT')
    for o in fs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fs[0]
    bpy.ops.object.convert(target='MESH')


def sem_metal():
    """O assado (DIFFUSE/COLOR) sai preto em metal: metal a 0 em todos os materiais antes de assar."""
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                ent = n.inputs['Metallic']
                for l in list(ent.links):
                    m.node_tree.links.remove(l)
                ent.default_value = 0.0


def juntar(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def juntar_irmaos(fora=()):
    """Malhas filhas diretas do mesmo empty, sem animação própria, andam juntas: uma malha só (brilho à parte).
    `fora`: nomes já tomados pelas partes do jogo."""
    sc = bpy.context.scene
    for e in [o for o in sc.objects if o.type == 'EMPTY']:
        grupos = {}
        for c in e.children:
            if c.type != 'MESH' or c.name in fora or (c.animation_data and c.animation_data.action):
                continue
            grupos.setdefault(any(brilha(s.material) for s in c.material_slots), []).append(c)
        for objs in grupos.values():
            if len(objs) > 1:
                juntar(objs)


def fora_da_area(o, w, d, m=0.06):
    cantos = [o.matrix_world @ Vector(c) for c in o.bound_box]
    x0, x1 = min(c.x for c in cantos), max(c.x for c in cantos)
    y0, y1 = min(c.y for c in cantos), max(c.y for c in cantos)
    return x1 < -w / 2 - m or x0 > w / 2 + m or y1 < -d / 2 - m or y0 > d / 2 + m


def limpar(cfg, w, d):
    sc = bpy.context.scene
    tirar = [t.lower() for t in cfg['tirar']] + list(EFEITO)
    for o in list(sc.objects):
        nome = o.name.lower()
        mats = [s.material for s in getattr(o, 'material_slots', [])]
        sai = o.type in ('LIGHT', 'CAMERA') or any(t in nome for t in tirar)
        if o.type == 'MESH':
            sai = sai or not o.data.polygons or any(tem_volume(m) for m in mats) or any(vidro(m) for m in mats)
            sai = sai or any(mancha_suave(m) for m in mats)
            sai = sai or fora_da_area(o, w, d, cfg.get('margem', 0.06)) or o.hide_render
        if sai:
            bpy.data.objects.remove(o, do_unlink=True)


def dinamicos(quadros):
    """Objetos cuja matriz no mundo muda ao longo do laço (são exportados soltos, com a animação)."""
    sc = bpy.context.scene
    mats = {}
    for f in quadros:
        sc.frame_set(f)
        for o in sc.objects:
            mats.setdefault(o.name, []).append(o.matrix_world.copy())
    sc.frame_set(quadros[0])
    din = set()
    for nome, ms in mats.items():
        if any(sum(abs(a[i][j] - ms[0][i][j]) for i in range(4) for j in range(4)) > 1e-4 for a in ms[1:]):
            din.add(nome)
    return din


def tris(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def juntar_fixos(fixos, nome):
    """Tira do pai (mantendo a posição) e junta tudo o que é fixo numa malha só."""
    for o in fixos:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    for o in fixos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = fixos[0]
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    corpo = bpy.context.view_layer.objects.active
    corpo.name = nome
    return corpo


def reduzir(o, alvo):
    t = tris(o)
    if t <= alvo:
        return
    mod = o.modifiers.new('reduzir', 'DECIMATE')
    mod.ratio = max(0.01, alvo / t)
    mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=mod.name)


def copia(o):
    c = o.copy()
    c.data = o.data.copy()
    c.animation_data_clear()
    bpy.context.scene.collection.objects.link(c)
    c.matrix_world = o.matrix_world.copy()
    return c


def material_assado(nome, img):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    p = principled(m)
    p.inputs['Roughness'].default_value = 0.75
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = img
    nt.links.new(n.outputs['Color'], p.inputs['Base Color'])
    nt.nodes.active = n
    return m


_PALETA = {}


def material_brilho(m):
    """Peça que brilha: material liso da paleta (o jogo dá o brilho e o pulso pelo nome)."""
    p = principled(m)
    cor = tuple(p.inputs['Emission Color'].default_value) if p and not p.inputs['Emission Color'].is_linked else (1, 0.4, 0.1, 1)
    quente = cor[0] > cor[2]
    chave = ('P_Fogo' if quente else 'P_Cristal', tuple(round(c, 3) for c in cor))
    if chave in _PALETA:                           # um material por cor (luzes iguais juntam numa malha só)
        return _PALETA[chave]
    novo = bpy.data.materials.new(chave[0])
    _PALETA[chave] = novo
    pn = principled(novo)
    pn.inputs['Base Color'].default_value = cor
    pn.inputs['Emission Color'].default_value = cor
    pn.inputs['Emission Strength'].default_value = 2.0
    return novo


def assar(baixos, altos, lado, nome):
    """UV único (atlas) para todas as peças baixas; assa a cor do detalhado (com a sujeira procedural) nelas."""
    sc = bpy.context.scene
    sem_metal()
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 8
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences
        pr.compute_device_type = 'OPTIX'
        pr.get_devices()
        for dv in pr.devices:
            dv.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    for o in baixos + altos:                    # peça escondida neste quadro (some/aparece no laço) também assa
        o.hide_render = False
        o.hide_viewport = False
        o.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    for o in baixos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = baixos[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    img = bpy.data.images.new(nome + '_tex', lado, lado)
    mat = material_assado(nome + '_Tex', img)
    for o in baixos:
        o.data.materials.clear()
        o.data.materials.append(mat)
    sc.render.bake.use_selected_to_active = True
    sc.render.bake.cage_extrusion = 0.03
    sc.render.bake.max_ray_distance = 0.08
    sc.render.bake.margin = 6
    primeiro = True
    for b, a in zip(baixos, altos):
        bpy.ops.object.select_all(action='DESELECT')
        a.select_set(True)
        b.select_set(True)
        bpy.context.view_layer.objects.active = b
        sc.render.bake.use_clear = primeiro
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=primeiro, margin=6)
        primeiro = False
    caminho = os.path.join(bpy.app.tempdir, nome + '_tex.png')
    img.filepath_raw = caminho
    img.file_format = 'PNG'
    img.save()
    img.pack()
    return img


def main():
    nome = args()
    cfg = CONFIG[nome]
    pasta = os.path.join(MODELOS, cfg['cat'], nome)
    antigo = json.load(open(os.path.join(pasta, nome + '.json'), encoding='utf-8'))
    w, d = antigo['area']
    montar_estudo(cfg)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 96
    sc.frame_set(1)
    if cfg.get('centro'):                              # cena com várias estruturas: esta vem para a origem
        c = cfg['centro']
        base = bpy.data.objects.new('_base', None)
        sc.collection.objects.link(base)
        base.matrix_world = Matrix.Rotation(-(c[2] if len(c) > 2 else 0.0), 4, 'Z') @ Matrix.Translation((-c[0], -c[1], 0))
        for o in list(sc.objects):
            if o is not base and o.parent is None:
                o.parent = base
        bpy.context.view_layer.update()
    textos_em_malha()
    limpar(cfg, w, d)
    if cfg.get('depois_de_montar'):
        cfg['depois_de_montar'](sc)
    malhas = [o for o in sc.objects if o.type == 'MESH']
    # peças que o jogo mexe pelo nome: juntadas por parte, com pivô; saem da animação do estudo
    pecas = []
    usados = set()
    for pn, pd in cfg.get('partes', {}).items():
        objs = [o for o in malhas if o.name not in usados and any(t.lower() in o.name.lower() for t in pd['objetos'])]
        if not objs:
            print('AVISO parte sem objetos:', pn)
            continue
        usados |= {o.name for o in objs}
        for o in objs:
            o.animation_data_clear()
        pecas.append((pn, pd, objs))
    juntar_irmaos(usados)
    malhas = [o for o in sc.objects if o.type == 'MESH' and o.name not in usados]
    din = dinamicos([1, 13, 25, 37, 49, 61, 73, 85]) if cfg.get('anima', True) else set()
    brilhantes = [o for o in malhas if any(brilha(s.material) for s in o.material_slots)]
    fixos = [o for o in malhas if o.name not in din and o not in brilhantes]
    moveis = [o for o in malhas if o.name in din and o not in brilhantes]
    total = sum(tris(o) for o in fixos + moveis) or 1
    # alto (detalhado) guardado para assar; baixo reduzido ao orçamento
    corpo = juntar_fixos(fixos, nome + '_' + cfg.get('corpo', 'corpo')) if fixos else None
    pares = []
    if corpo:
        alto = copia(corpo)
        reduzir(corpo, int(cfg['tris'] * 0.75))
        pares.append((corpo, alto))
    t_moveis = sum(tris(o) for o in moveis) or 1
    for i, o in enumerate(moveis):
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.make_single_user(object=True, obdata=True)
        alto = copia(o)
        reduzir(o, max(24, int(cfg['tris'] * 0.25 * tris(o) / t_moveis)))
        o.name = f'{nome}_m{i}'                     # nome neutro: o Animador do jogo não mexe por cima
        pares.append((o, alto))
    for o in brilhantes:
        for s in o.material_slots:
            s.material = material_brilho(s.material)
        reduzir(o, 300)
    grupos = {}                                       # luzes fixas: uma malha por material da paleta
    for o in brilhantes:
        pai_fixo = o.parent is None or o.parent.name not in din
        if o.name not in din and pai_fixo and not (o.animation_data and o.animation_data.action):
            grupos.setdefault((o.parent.name if o.parent else '', tuple(s.material.name for s in o.material_slots)), []).append(o)
    brilhantes = [o for o in brilhantes if not any(o in g for g in grupos.values())] + \
                 [juntar(g) if len(g) > 1 else g[0] for g in grupos.values()]
    objs_partes = {}
    for pn, pd, objs in pecas:
        brilho = all(any(brilha(s.material) for s in o.material_slots) for o in objs)
        po = juntar_fixos(objs, f'{nome}_{pn}')
        sc.cursor.location = Vector(pd.get('pivo', (0, 0, 0)))
        bpy.ops.object.select_all(action='DESELECT')
        po.select_set(True)
        bpy.context.view_layer.objects.active = po
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        objs_partes[pn] = po
        if brilho:
            for s in po.material_slots:
                s.material = material_brilho(s.material)
            reduzir(po, pd.get('tris', 400))
        else:
            alto = copia(po)
            reduzir(po, pd.get('tris', int(cfg['tris'] * 0.12)))
            pares.append((po, alto))
    assar([b for b, _ in pares], [a for _, a in pares], cfg['tex'], nome)
    for _, a in pares:
        bpy.data.objects.remove(a, do_unlink=True)
    # raiz, portas (do .json atual do jogo) e exportação com a animação "trabalho"
    for pn, pd, _ in pecas:                            # hierarquia das partes (o jogo lê o pai em modelos.json)
        pai = objs_partes.get(pd.get('pai', 'corpo')) or corpo
        po = objs_partes[pn]
        if pai is not None and pai is not po:
            mw = po.matrix_world.copy()
            po.parent = pai
            po.matrix_world = mw
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    for o in list(sc.objects):
        if o is not raiz and o.parent is None:
            o.parent = raiz
    for pt in antigo.get('portas', []):
        e = bpy.data.objects.new(pt['nome'], None)
        sc.collection.objects.link(e)
        e.location = Vector(pt['pos'])
        e.rotation_euler = (0, 0, math.atan2(-pt['dir'][0], pt['dir'][1]))
        e.parent = raiz
    # todas as ações numa trilha NLA de mesmo nome → o glTF junta numa animação só ("trabalho")
    for o in sc.objects:
        ad = o.animation_data
        if ad and ad.action:
            tr = ad.nla_tracks.new()
            tr.name = 'trabalho'
            tr.strips.new('trabalho', 1, ad.action)
            ad.action = None
    if cfg.get('antes_de_exportar'):
        cfg['antes_de_exportar'](sc, raiz, antigo)
    bpy.ops.object.select_all(action='DESELECT')
    for o in sc.objects:
        o.select_set(True)
    glb = os.path.join(pasta, nome + '.glb')
    bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_yup=True, export_animations=True,
                              export_animation_mode='NLA_TRACKS', export_force_sampling=True, export_frame_range=True,
                              export_image_format='JPEG')
    pts = [o.matrix_world @ v.co for o in sc.objects if o.type == 'MESH' for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    antigo.update(tris=sum(tris(o) for o in sc.objects if o.type == 'MESH'),
                  dims=[round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)],
                  partes=[dict(nome=cfg.get('corpo', 'corpo'), pai=None, pivo=[0.0, 0.0, 0.0])] +
                  [dict(nome=pn, pai=pd.get('pai', cfg.get('corpo', 'corpo')), pivo=[round(v, 4) for v in pd.get('pivo', (0, 0, 0))])
                   for pn, pd, _ in pecas if pn in objs_partes], anima=bool(moveis),
                  estudo=cfg['script'])
    json.dump(antigo, open(os.path.join(pasta, nome + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('PARA_JOGO ok', nome, antigo['tris'], 'tris', len(moveis), 'peças móveis', len(brilhantes), 'brilhantes')


main()
