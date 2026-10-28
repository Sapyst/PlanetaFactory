"""Texturas das estruturas (estilo aprovado no teste do vagão: rústico, neutro, realista).
Para cada .glb de estrutura/veículo: guarda o original em <nome>_sem_textura.glb (1ª vez), desdobra um atlas de UV
para todas as peças, monta um material procedural por material da paleta, ASSA só a cor numa textura
(512² peça 1×1, 1024² maior) e grava o .glb de volta com a textura. Materiais especiais não são assados e ficam
como estão (lona da esteira — rola pelo UV original, que vai para o 2º canal —, cristal, fogo, vidro, biomassa).
Também grava <nome>_tex_previa.png (antes | depois) para conferência.
Uso: blender -b --factory-startup --python texturizar.py -- [filtro de categoria ou nome]"""
import bpy, os, sys, json, glob, math
from mathutils import Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modelos'))
PULAR = ('itens', 'inimigos')
# Paleta REAL das texturas (sRGB 0–255), baseada em tabelas de albedo PBR (Lagarde/UE4, Sceneform, Polycount):
# materiais reais são pouco saturados — tijolo ~ (148,125,117), concreto envelhecido 122–147, ferro ~ (192,189,186).
REAL = {
    'P_Concreto': (138, 136, 130),     # concreto envelhecido
    'P_Escuro': (50, 52, 54),          # aço pintado de preto fosco, gasto
    'P_Metal': (132, 134, 135),        # aço galvanizado/escovado envelhecido
    'P_Aco': (98, 101, 104),
    'P_Cobre': (142, 98, 72),          # bronze/cobre apagado (sem brilho de catálogo)
    'P_Faixa': (176, 142, 60),         # amarelo de segurança desbotado
    'P_Tijolo': (132, 92, 78),         # tijolo dessaturado
    'P_RochaEscura': (98, 96, 93),     # brita da ferrovia / rocha escura
    # naturais (planeta vivo, mas com cor de material de verdade: folhagem oliva, casca, rocha, minério)
    'P_Folha': (80, 106, 72),           # folhagem densa (oliva-azulada: planeta estranho, sem neon)
    'P_FolhaClara': (112, 134, 90),
    'P_Lodo': (66, 74, 48),
    'P_Tronco': (86, 70, 58),          # casca
    'P_FungoCaule': (204, 196, 178),   # pé de cogumelo: claro, cremoso
    'P_Chapeu': (112, 82, 98),         # chapéu: malva escuro, fosco (fungo de verdade, sem neon)
    'P_Rocha': (152, 148, 140),
    'P_Pedra': (150, 145, 136),
    'P_Cinza': (90, 88, 86),           # cinza vulcânica
    'P_Ferrugem': (108, 66, 46),       # minério de ferro (hematita/limonita)
    'P_Malaquita': (62, 104, 86),      # minério de cobre
    'P_Carvao': (44, 44, 46),
    'P_Areia': (180, 160, 124),
    'P_Silex': (96, 100, 110),
}
FOLHAGEM = {'P_Folha', 'P_FolhaClara', 'P_Lodo'}
ROCHAS = {'P_Rocha', 'P_Pedra', 'P_Cinza', 'P_RochaEscura'}
MINERIOS = {'P_Ferrugem', 'P_Malaquita', 'P_Carvao', 'P_Areia', 'P_Silex'}
FERRUGEM = (104, 60, 38)
SUJEIRA = (38, 34, 30)
POEIRA = (112, 100, 86)


def lin(c):
    """sRGB 0–255 → linear (o Blender trabalha em linear)."""
    return tuple(((v / 255.0 + 0.055) / 1.055) ** 2.4 if v / 255.0 > 0.04045 else v / 255.0 / 12.92 for v in c)


SEM_LISTRAS = {'locomotiva', 'muro_centro', 'muro_lado'}   # faixa grande = pintura lisa (zebrado só em faixa fina)
_modelo_atual = ''
_modelo_cat = ''
ESPECIAIS = {'P_Esteira', 'P_Cristal', 'P_Fogo', 'P_Vidro', 'P_Biomassa', 'P_OlhoInimigo', 'P_Seiva'}
filtro = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else ''


# ------------------------------------------------------------------ nós
def no(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def faixa(nt, entrada, de, ate):
    r = no(nt, 'ShaderNodeMapRange')
    r.inputs[1].default_value = de
    r.inputs[2].default_value = ate
    nt.links.new(entrada, r.inputs[0])
    return r.outputs[0]


def mult(nt, a, b):
    m = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(a, m.inputs[0]) if not isinstance(a, float) else None
    if isinstance(a, float):
        m.inputs[0].default_value = a
    if isinstance(b, float):
        m.inputs[1].default_value = b
    else:
        nt.links.new(b, m.inputs[1])
    return m.outputs[0]


def mix(nt, a, b, fac):
    m = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MIX')
    if isinstance(fac, float):
        m.inputs[0].default_value = fac
    else:
        nt.links.new(fac, m.inputs[0])
    for i, v in ((6, a), (7, b)):
        if isinstance(v, (tuple, list)):
            m.inputs[i].default_value = (*v[:3], 1)
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[2]


def ruido(nt, coord, escala, detalhe=3.0, aspereza=0.5, esticar=None):
    n = no(nt, 'ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = escala
    n.inputs['Detail'].default_value = detalhe
    n.inputs['Roughness'].default_value = aspereza
    if esticar:
        mp = no(nt, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = esticar
        nt.links.new(coord, mp.inputs['Vector'])
        nt.links.new(mp.outputs[0], n.inputs['Vector'])
    else:
        nt.links.new(coord, n.inputs['Vector'])
    return n.outputs['Fac']


def quina(nt, raio=0.025):
    """1 nas quinas (normal arredondada pelo Bevel difere da normal da face)."""
    bev = no(nt, 'ShaderNodeBevel', samples=8)
    bev.inputs['Radius'].default_value = raio
    geo = no(nt, 'ShaderNodeNewGeometry')
    dot = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    nt.links.new(bev.outputs[0], dot.inputs[0])
    nt.links.new(geo.outputs['Normal'], dot.inputs[1])
    q = faixa(nt, dot.outputs['Value'], 0.97, 0.88)
    # quebra a quina em lascas soltas (ruído alto) — sem isso a aresta vira um contorno desenhado
    coord = no(nt, 'ShaderNodeTexCoord').outputs['Object']
    return mult(nt, q, faixa(nt, ruido(nt, coord, 22.0, 2, 0.5), 0.62, 0.72))


# ------------------------------------------------------------------ receitas por material da paleta
def ao(nt):
    """Oclusão de ambiente (0 nos vãos, 1 aberto): sujeira acumulada nos cantos."""
    a = no(nt, 'ShaderNodeAmbientOcclusion', samples=16)
    a.inputs['Distance'].default_value = 0.25
    return a.outputs['AO']


def juntas(nt, coord, escala, espessura=0.02):
    """Juntas de chapa/placa: 1 na linha de junta (textura de tijolo sem cor, só o rejunte)."""
    t = no(nt, 'ShaderNodeTexBrick')
    t.inputs['Scale'].default_value = escala
    t.inputs['Mortar Size'].default_value = espessura
    t.inputs['Mortar Smooth'].default_value = 0.2
    t.inputs['Bias'].default_value = 0.0
    t.inputs['Brick Width'].default_value = 1.0
    t.inputs['Row Height'].default_value = 0.5
    t.offset = 0.5
    t.inputs['Color1'].default_value = (0, 0, 0, 1)
    t.inputs['Color2'].default_value = (0, 0, 0, 1)
    t.inputs['Mortar'].default_value = (1, 1, 1, 1)
    nt.links.new(coord, t.inputs['Vector'])
    return t.outputs['Fac']


def procedural(mat, base_orig, img):
    nome = mat.name.split('.')[0]
    if nome in REAL:
        base = lin(REAL[nome])
    else:
        # fora da tabela: tira metade da saturação e escurece um pouco
        m = sum(base_orig) / 3
        base = tuple((m + (c - m) * 0.5) * 0.85 for c in base_orig)
    ferr, suj, poe = lin(FERRUGEM), lin(SUJEIRA), lin(POEIRA)
    nt = mat.node_tree
    nt.nodes.clear()
    saida = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfDiffuse')
    nt.links.new(bsdf.outputs[0], saida.inputs[0])
    coord = no(nt, 'ShaderNodeTexCoord').outputs['Object']
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(coord, sep.inputs[0])
    escuro = tuple(c * 0.78 for c in base)
    cor = mix(nt, base, escuro, faixa(nt, ruido(nt, coord, 2.2), 0.35, 0.75))          # tom desigual
    cor = mix(nt, cor, tuple(c * 0.9 for c in base), faixa(nt, ruido(nt, coord, 18.0, 4, 0.6), 0.3, 0.7))   # grão fino
    natural = _modelo_cat.startswith('mapa')
    if natural and nome in FOLHAGEM:
        cor = mix(nt, cor, tuple(c * 0.62 for c in base), faixa(nt, ruido(nt, coord, 3.5, 4, 0.6), 0.4, 0.7))      # cachos
        cor = mix(nt, cor, tuple(min(1, c * 1.3) for c in base), faixa(nt, ruido(nt, coord, 11.0, 3, 0.6), 0.62, 0.72))
        cor = mix(nt, cor, lin((118, 112, 64)), mult(nt, faixa(nt, ruido(nt, coord, 24.0, 2, 0.5), 0.72, 0.78), 0.6))  # folhas secas
        geo = no(nt, 'ShaderNodeNewGeometry')
        nz = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Normal'], nz.inputs[0])
        cor = mix(nt, cor, tuple(c * 0.55 for c in base), faixa(nt, nz.outputs['Z'], 0.1, -0.6))                   # sombra por baixo
    elif natural and nome == 'P_Tronco':
        cor = mix(nt, cor, tuple(c * 0.55 for c in base), faixa(nt, ruido(nt, coord, 30.0, 3, 0.6, (1.0, 1.0, 0.08)), 0.5, 0.7))  # sulcos
        cor = mix(nt, cor, lin((128, 132, 104)), mult(nt, faixa(nt, ruido(nt, coord, 6.0, 5, 0.7), 0.66, 0.74), 0.7))           # líquen
    elif natural and nome == 'P_Chapeu':
        geo = no(nt, 'ShaderNodeNewGeometry')
        nz = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Normal'], nz.inputs[0])
        cor = mix(nt, cor, tuple(c * 0.62 for c in base), faixa(nt, nz.outputs['Z'], 0.7, 1.0))                     # centro do topo mais escuro
        cor = mix(nt, cor, lin((186, 170, 160)), faixa(nt, ruido(nt, coord, 16.0, 2, 0.5), 0.73, 0.77))            # pintas claras
        cor = mix(nt, cor, tuple(c * 0.8 for c in base), faixa(nt, ruido(nt, coord, 50.0, 2, 0.5, (1.0, 1.0, 0.3)), 0.5, 0.7))  # estrias
    elif natural and nome == 'P_FungoCaule':
        cor = mix(nt, cor, tuple(c * 0.8 for c in base), faixa(nt, ruido(nt, coord, 40.0, 2, 0.5, (1.0, 1.0, 0.06)), 0.45, 0.7))  # fibras
        cor = mix(nt, cor, lin((150, 136, 112)), mult(nt, faixa(nt, ruido(nt, coord, 9.0, 4, 0.6), 0.66, 0.74), 0.5))
    elif natural and (nome in ROCHAS or nome in MINERIOS):
        estr = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z')
        estr.inputs['Scale'].default_value = 2.5
        estr.inputs['Distortion'].default_value = 6.0
        estr.inputs['Detail'].default_value = 3.0
        nt.links.new(coord, estr.inputs['Vector'])
        cor = mix(nt, cor, tuple(c * 0.86 for c in base), mult(nt, estr.outputs['Fac'], 0.5))                       # estratos
        veio = no(nt, 'ShaderNodeTexNoise', noise_type='RIDGED_MULTIFRACTAL')
        veio.inputs['Scale'].default_value = 3.0
        veio.inputs['Detail'].default_value = 6.0
        nt.links.new(coord, veio.inputs['Vector'])
        cor = mix(nt, cor, tuple(c * 0.72 for c in base), mult(nt, faixa(nt, veio.outputs['Fac'], 0.75, 0.95), 0.6))  # veios (orgânicos)
        if nome in MINERIOS:
            cor = mix(nt, cor, tuple(min(1, c * 1.8) for c in base), faixa(nt, ruido(nt, coord, 80.0, 1, 0.5), 0.74, 0.78))  # pintas do mineral
        else:
            geo = no(nt, 'ShaderNodeNewGeometry')
            nz = no(nt, 'ShaderNodeSeparateXYZ')
            nt.links.new(geo.outputs['Normal'], nz.inputs[0])
            liq = mult(nt, faixa(nt, nz.outputs['Z'], 0.45, 0.9), faixa(nt, ruido(nt, coord, 7.0, 6, 0.7), 0.55, 0.68))
            cor = mix(nt, cor, lin((124, 128, 86)), mult(nt, liq, 0.75))                                          # líquen por cima
    elif nome in ('P_Concreto', 'P_RochaEscura'):
        cor = mix(nt, cor, tuple(c * 0.62 for c in base), faixa(nt, ruido(nt, coord, 7.0, 6, 0.7), 0.6, 0.75))  # manchas
        cor = mix(nt, cor, tuple(min(1, c * 1.35) for c in base), faixa(nt, ruido(nt, coord, 60.0), 0.72, 0.8))  # brita/poros
        if nome == 'P_Concreto':
            cor = mix(nt, cor, tuple(c * 0.6 for c in base), mult(nt, juntas(nt, coord, 0.9, 0.012), 0.8))     # juntas da forma
        cor = mix(nt, cor, tuple(min(1, c * 1.25) for c in base), mult(nt, quina(nt, 0.03), faixa(nt, ruido(nt, coord, 30.0), 0.55, 0.7)))
    elif nome in ('P_Metal', 'P_Aco'):
        cor = mix(nt, cor, tuple(c * 0.82 for c in base), faixa(nt, ruido(nt, coord, 40.0, 2, 0.5, (1.0, 1.0, 0.04)), 0.4, 0.7))  # escovado
        cor = mix(nt, cor, tuple(c * 0.55 for c in base), mult(nt, juntas(nt, coord, 2.2, 0.018), 0.85))           # chapas
        cor = mix(nt, cor, ferr, mult(nt, faixa(nt, ruido(nt, coord, 6.0, 6, 0.7), 0.66, 0.76), 0.7))               # ferrugem
    elif nome == 'P_Tijolo':
        tij = no(nt, 'ShaderNodeTexBrick')
        tij.inputs['Scale'].default_value = 7.0
        tij.inputs['Mortar Size'].default_value = 0.015
        tij.inputs['Color1'].default_value = (*base, 1)
        tij.inputs['Color2'].default_value = (*escuro, 1)
        tij.inputs['Mortar'].default_value = (*lin((150, 144, 134)), 1)
        nt.links.new(coord, tij.inputs['Vector'])
        cor = mix(nt, cor, tij.outputs['Color'], 0.85)
    elif not natural:
        if nome == 'P_Faixa' and _modelo_atual not in SEM_LISTRAS:
            # listras zebradas de segurança (diagonal, ~8 cm), desbotadas
            onda = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL')
            onda.inputs['Scale'].default_value = 5.0
            onda.inputs['Distortion'].default_value = 0.0
            nt.links.new(coord, onda.inputs['Vector'])
            listra = faixa(nt, onda.outputs['Fac'], 0.48, 0.52)
            cor = mix(nt, cor, lin((44, 42, 40)), listra)
        if nome == 'P_Escuro':
            cor = mix(nt, cor, tuple(c * 0.6 for c in base), mult(nt, juntas(nt, coord, 2.0, 0.015), 0.9))           # chapas
        if nome == 'P_Cobre':
            cor = mix(nt, cor, lin((92, 116, 100)), mult(nt, faixa(nt, ruido(nt, coord, 4.5, 6, 0.7), 0.66, 0.74), 0.75))  # azinhavre
        cor = mix(nt, cor, ferr, faixa(nt, ruido(nt, coord, 5.5, 6, 0.7), 0.64, 0.73))                                # ferrugem
        # riscos finos (pintura raspada em traços)
        riscos = faixa(nt, ruido(nt, coord, 70.0, 1, 0.5, (0.08, 1.0, 1.0)), 0.74, 0.8)
        cor = mix(nt, cor, lin((96, 94, 92)), mult(nt, riscos, 0.6))
        cor = mix(nt, cor, lin((112, 110, 108)), mult(nt, quina(nt), faixa(nt, ruido(nt, coord, 40.0), 0.5, 0.68)))  # quinas
    # para todos: escorridos verticais, sujeira nos vãos (AO) e poeira de baixo para cima
    if not natural:
        cor = mix(nt, cor, suj, mult(nt, faixa(nt, ruido(nt, coord, 9.0, 2, 0.5, (1.0, 1.0, 0.12)), 0.6, 0.86), 0.7))
    cor = mix(nt, cor, suj, mult(nt, faixa(nt, ao(nt), 0.85, 0.25), 0.4 if natural else 0.75))   # sujeira nos vãos
    baixo = faixa(nt, sep.outputs['Z'], 0.55, 0.08)
    poeira = mult(nt, mult(nt, baixo, faixa(nt, ruido(nt, coord, 14.0), 0.3, 0.7)), 0.5)
    cor = mix(nt, cor, poe, poeira)
    nt.links.new(cor, bsdf.inputs['Color'])
    alvo = no(nt, 'ShaderNodeTexImage')
    alvo.image = img
    nt.nodes.active = alvo


def cor_base(mat):
    if mat.use_nodes and mat.node_tree.nodes.get('Principled BSDF'):
        return tuple(mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3])
    return tuple(mat.diffuse_color[:3])


# ------------------------------------------------------------------ prévia
def render(arquivo, tipo, objs):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = tipo
    sh.show_object_outline = False
    sh.show_cavity = False
    sc.world.color = (0.16, 0.17, 0.19)
    sc.render.resolution_x, sc.render.resolution_y = 640, 520
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    cam = sc.camera
    cam.data.type = 'ORTHO'
    d = Vector((1, -1, 0.85)).normalized()
    cam.location = c + d * 20
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = max((hi - lo).length * 1.05, 0.8)
    sc.render.filepath = arquivo
    bpy.ops.render.render(write_still=True)


def lado_a_lado(a_arq, b_arq, saida):
    a = bpy.data.images.load(a_arq)
    b = bpy.data.images.load(b_arq)
    w, h = a.size
    img = bpy.data.images.new('lado', w * 2, h)
    pa, pb = list(a.pixels), list(b.pixels)
    px = [0.0] * (w * 2 * h * 4)
    for y in range(h):
        px[y * w * 8: y * w * 8 + w * 4] = pa[y * w * 4:(y + 1) * w * 4]
        px[y * w * 8 + w * 4:(y + 1) * w * 8] = pb[y * w * 4:(y + 1) * w * 4]
    img.pixels[:] = px
    img.filepath_raw = saida
    img.file_format = 'PNG'
    img.save()
    for i in (a, b, img):
        bpy.data.images.remove(i)


# ------------------------------------------------------------------ um modelo
def texturizar(json_arq):
    global _modelo_atual, _modelo_cat
    d = json.load(open(json_arq, encoding='utf-8'))
    _modelo_atual = d['nome']
    _modelo_cat = d['categoria']
    pasta = os.path.dirname(json_arq)
    glb = json_arq[:-5] + '.glb'
    base_glb = json_arq[:-5] + '_sem_textura.glb'
    if not os.path.exists(base_glb):
        os.replace(glb, base_glb)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.world = bpy.data.worlds.new('W')
    cam = bpy.data.objects.new('CAM', bpy.data.cameras.new('CAM'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    bpy.ops.import_scene.gltf(filepath=base_glb)
    objs = [o for o in sc.objects if o.type == 'MESH']
    antes = os.path.join(pasta, '_antes.png')
    render(antes, 'MATERIAL', objs)
    w, dd = d.get('area', [1, 1])
    tam = 512 if w * dd <= 1 and d.get('tipo') != 'veiculo' else 1024
    if d.get('tipo') == 'deco':
        tam = 256                                  # enfeite miúdo: textura pequena
    img = bpy.data.images.new(d['nome'] + '_tex', tam, tam, alpha=False)
    # UV: atlas no 1º canal; o UV original (lona da esteira) vai para o 2º
    for o in objs:
        me = o.data
        if me.uv_layers:
            dados = [tuple(l.uv) for l in me.uv_layers[0].data]   # copia antes (referências mudam ao criar canal)
            me.uv_layers[0].name = 'atlas'
            me.uv_layers.new(name='original')
            orig = me.uv_layers['original']
            for i, uv in enumerate(dados):
                orig.data[i].uv = uv
        else:
            me.uv_layers.new(name='atlas')
        me.uv_layers.active = me.uv_layers['atlas']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    # materiais: especiais ficam (cópia só para o assado); os outros viram procedurais
    originais = {}
    for o in objs:
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            nome = m.name.split('.')[0]
            if nome in ESPECIAIS:
                originais.setdefault(m.name, m)
                cp = m.copy()
                cp.use_nodes = True
                t = cp.node_tree.nodes.new('ShaderNodeTexImage')
                t.image = img
                cp.node_tree.nodes.active = t
                o.data.materials[i] = cp
                cp['original'] = m.name
            elif not m.get('assado'):
                base = cor_base(m)
                m.use_nodes = True
                procedural(m, base, img)
                m['assado'] = True
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 24                    # AO precisa de mais amostras
    # margem larga, estendendo a cor da ilha: de longe (mipmap) o fundo não vaza como linha nas costuras do UV
    sc.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=max(8, tam // 32), use_clear=True)
    png = json_arq[:-5] + '_tex.png'
    img.filepath_raw = png
    img.file_format = 'PNG'
    img.save()
    # material final: uma textura para todo o resto; especiais voltam
    final = bpy.data.materials.new(d['nome'] + '_Tex')
    final.use_nodes = True
    pb = final.node_tree.nodes['Principled BSDF']
    tx = final.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = img
    final.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = 0.7
    pb.inputs['Metallic'].default_value = 0.15
    for o in objs:
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            if m.get('original'):
                o.data.materials[i] = originais[m['original']]
            elif m.get('assado'):
                o.data.materials[i] = final
    depois = os.path.join(pasta, '_depois.png')
    render(depois, 'TEXTURE', objs)
    lado_a_lado(antes, depois, json_arq[:-5] + '_tex_previa.png')
    os.remove(antes)
    os.remove(depois)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_yup=True, export_image_format='AUTO')
    print('TEX', d['nome'], tam)


for f in sorted(glob.glob(os.path.join(RAIZ, '**', '*.json'), recursive=True)):
    if os.path.basename(f).startswith('_'):
        continue
    d = json.load(open(f, encoding='utf-8'))
    if d.get('tipo') not in ('estrutura', 'veiculo', 'canto', 'deco') or d['categoria'].startswith(PULAR):
        continue
    if filtro and filtro not in d['categoria'] and filtro != d['nome']:
        continue
    try:
        texturizar(f)
    except Exception as e:
        print('ERRO', d['nome'], e)
