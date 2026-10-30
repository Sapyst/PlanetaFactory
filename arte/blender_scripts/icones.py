"""Ícones da barra de construção: cada estrutura construível renderizada em isométrico, fundo transparente.
Lê os .glb já exportados (rodar depois dos scripts de modelos). Saída: arte/icones/<nome>.png (192×192).
Itens (placas, engrenagens...) só com `-- itens`: arte/icones/itens/<nome>.png (128×128), para as casas da interface.
Uso: blender -b --factory-startup --python icones.py [-- itens] [-- so nome1,nome2]
Todos saem iguais: mesma câmera (direção fixa), mesma luz, ajuste pelos vértices de verdade, exposição igualada e um fio
claro em volta da silhueta (para peça escura não sumir no botão escuro). Peça alta e fina é achatada só no ícone."""
import bpy, bmesh, os, sys, json, glob, math
import numpy as np
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.dirname(__file__))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import preparar_cena, RAIZ

SAIDA = os.path.abspath(os.path.join(RAIZ, '..', 'icones'))
PULAR = ('mapa', 'itens', 'inimigos', 'proposta')
DIRECAO = (1, -1, 0.85)
MARGEM = 1.06
ALTURA_MAX = 1.30      # altura/largura máxima na tela; acima disso o modelo é achatado em z
ACHATA_MIN = 0.45      # nunca achata mais que isto
LUZ_ALVO = 0.46        # luminância mediana a que toda peça é levada
GANHO_MAX = 2.6

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ITENS = 'itens' in ARGS
SO = set(ARGS[ARGS.index('so') + 1].split(',')) if 'so' in ARGS else None
if ITENS:
    SAIDA = os.path.join(SAIDA, 'itens')
os.makedirs(SAIDA, exist_ok=True)

# trechos repetidos: um tile só de esteira/cano/trilho não diz o que é; três em fila dizem
REPETIR = {'esteira_reta': 2, 'esteira_reta_rapida': 2, 'esteira_reta_expressa': 2, 'esteira_reta_quantica': 2,
           'cano_reto': 2, 'trilho_reto': 2, 'trilho_energizado': 2}
# no jogo a lona de todas é preta e rola mais rápido; no ícone ganha a cor do nível (a mesma da faixa do modelo)
LONA = {'P_Esteira': (0.16, 0.16, 0.17), 'P_EsteiraRapida': (0.62, 0.07, 0.05), 'P_EsteiraExpressa': (0.05, 0.22, 0.72),
        'P_EsteiraQuantica': (0.42, 0.08, 0.80)}
# partes que só existem em movimento (rastros, peças em trânsito): saem do ícone
OMITIR = {'braco_quantico': ('braco_quantico_anel',)}
# entulho voando em volta da máquina (peças em trânsito): fora do quadro só encolheria o resto
SO_DENTRO = ('terraplenagem', 'coletor_lixo', 'viveiro')
# pose do braço no ícone: articulações (nome da parte → graus em x ou z) para ler como braço e não como poste
POSE = {'braco': {'_giro': ('z', -75), '_braco1': ('x', -22), '_braco2': ('x', 30)}}
# rampa_desce*: o mesmo modelo girado 180°, ícone próprio
DERIVADOS = {'esteira_rampa': ('rampa_desce', 180), 'esteira_rampa_rapida': ('rampa_desce_rapida', 180),
             'esteira_rampa_expressa': ('rampa_desce_expressa', 180), 'esteira_rampa_quantica': ('rampa_desce_quantica', 180)}


def cor_real(mat):
    """Workbench usa diffuse_color; o glTF guarda a cor no Principled. Material liso (luz, cristal, lona) copia de lá."""
    if not mat.use_nodes or not mat.node_tree:
        return
    bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return
    em = bsdf.inputs.get('Emission Color'); forca = bsdf.inputs.get('Emission Strength')
    base = bsdf.inputs['Base Color']
    tem_textura = any(n.type == 'TEX_IMAGE' and n.image for n in mat.node_tree.nodes)
    if tem_textura:
        return
    c = base.default_value
    if em and forca and forca.default_value > 0 and max(em.default_value[:3]) > 0.01:
        c = em.default_value
    mat.diffuse_color = (c[0], c[1], c[2], 1.0)


def pontos(objs):
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        M = np.array(ev.matrix_world)
        pts.append(co @ M[:3, :3].T + M[:3, 3])
        ev.to_mesh_clear()
    return np.concatenate(pts) if pts else np.zeros((1, 3))


def enquadrar(sc, objs, arquivo, res):
    """Câmera fixa; acha o achatamento em z e o quadro pelos vértices; renderiza."""
    pts = pontos(objs)
    d = Vector(DIRECAO).normalized()
    cam = sc.camera
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    M = cam.rotation_euler.to_matrix()
    ex = np.array(M.col[0]); ey = np.array(M.col[1])
    z0 = pts[:, 2].min()
    def medidas(s):
        p = pts.copy(); p[:, 2] = z0 + (p[:, 2] - z0) * s
        a, b = p @ ex, p @ ey
        return p, a, b
    s = 1.0
    _, a, b = medidas(s)
    while (b.max() - b.min()) / max(a.max() - a.min(), 1e-3) > ALTURA_MAX and s > ACHATA_MIN:
        s -= 0.01
        _, a, b = medidas(s)
    if s < 1.0:
        raiz = bpy.data.objects.new('RAIZ_ICONE', None); sc.collection.objects.link(raiz)
        raiz.location = (0, 0, z0); raiz.scale = (1, 1, s)
        for o in sc.objects:
            if o is not raiz and o is not cam and o.parent is None:
                o.parent = raiz
                o.matrix_parent_inverse = Matrix.Translation((0, 0, -z0))
        bpy.context.view_layer.update()
    c = ex * (a.max() + a.min()) / 2 + ey * (b.max() + b.min()) / 2
    cam.location = Vector(c.tolist()) + d * 40
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.data.ortho_scale = max(a.max() - a.min(), b.max() - b.min()) * MARGEM
    cam.data.clip_end = 200
    sc.render.filepath = arquivo
    bpy.ops.render.render(write_still=True)
    acabar(arquivo)


def acabar(arquivo):
    """Iguala a exposição (mediana da luminância → LUZ_ALVO) e passa o fio claro em volta da silhueta."""
    im = bpy.data.images.load(arquivo, check_existing=False)
    im.colorspace_settings.name = 'Non-Color'
    w, h = im.size
    px = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    rgb, al = px[..., :3], px[..., 3]
    op = al > 0.5
    if op.any():
        lum = rgb @ np.array([0.30, 0.59, 0.11])
        ganho = min(GANHO_MAX, LUZ_ALVO / max(float(np.median(lum[op])), 0.02))
        ganho = max(ganho, 1.0)
        rgb = rgb * ganho
        rgb = rgb / (1.0 + np.maximum(rgb - 0.85, 0.0) * 0.8)                # ombro: não estoura as luzes
        lum = (rgb @ np.array([0.30, 0.59, 0.11]))[..., None]
        rgb = np.clip(lum + (rgb - lum) * 1.18, 0.0, 1.0)                    # um pouco mais de cor
    viz = al.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            viz = np.maximum(viz, np.roll(np.roll(al, dy, 0), dx, 1))
    fio = np.clip(viz - al, 0.0, 1.0)
    FIO = np.array([0.72, 0.76, 0.80])
    a2 = al + fio * 0.6
    saida = rgb.copy()
    mix = (fio * 0.6 / np.maximum(a2, 1e-4))[..., None]
    saida = saida * (1 - mix) + FIO * mix
    saida[(a2 <= 0.0)] = 0.0
    px = np.dstack([saida, np.clip(a2, 0, 1)]).astype(np.float32)
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = arquivo; im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


def fazer(f, d, nome, giro=0):
    sc = preparar_cena()
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = 'RGBA'
    s = sc.display.shading
    s.show_object_outline = False
    s.show_cavity = not ITENS; s.cavity_type = 'WORLD'; s.cavity_ridge_factor = 1.0; s.cavity_valley_factor = 1.0
    s.color_type = 'TEXTURE'          # estruturas texturizadas
    bpy.ops.import_scene.gltf(filepath=f[:-5] + '.glb')
    for m in bpy.data.materials:
        cor_real(m)
        if m.name.split('.')[0] in LONA:
            m.diffuse_color = (*LONA[m.name.split('.')[0]], 1.0)
    fora = OMITIR.get(d['nome'], ())
    meia = max(d.get('area', [1, 1])) / 2 + 0.15
    for o in sc.objects:
        if o.type != 'MESH':
            continue
        if any(x in o.name for x in fora):
            o.hide_render = True
        elif d['nome'] in SO_DENTRO:                 # o entulho vem junto na malha: corta os vértices fora do tile
            o.data = o.data.copy()
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if max(abs((o.matrix_world @ v.co).x), abs((o.matrix_world @ v.co).y)) > meia], context='VERTS')
            bm.to_mesh(o.data); bm.free()
            if not o.data.vertices:
                o.hide_render = True
    for parte, (eixo, graus) in POSE.get(d['nome'], {}).items():
        o = next((x for x in sc.objects if x.name.endswith(parte)), None)
        if o:
            o.rotation_mode = 'XYZ'; o.rotation_euler['xyz'.index(eixo)] += math.radians(graus)
    bpy.context.view_layer.update()
    rep = REPETIR.get(d['nome'], 1)
    if rep > 1:
        for o in [x for x in sc.objects if x.type == 'MESH']:
            for i in range(1, rep):
                c = o.copy(); sc.collection.objects.link(c); c.location.y += i
        bpy.context.view_layer.update()
    if giro:
        topo = [o for o in sc.objects if o.parent is None]
        for o in topo:
            o.rotation_mode = 'XYZ'
            o.location.rotate(Euler((0, 0, math.radians(giro))))
            o.rotation_euler.z += math.radians(giro)
        bpy.context.view_layer.update()
    objs = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render]
    enquadrar(sc, objs, os.path.join(SAIDA, nome + '.png'), (128, 128) if ITENS else (192, 192))


n = 0
for f in sorted(glob.glob(os.path.join(RAIZ, '**', '*.json'), recursive=True)):
    if os.path.basename(f).startswith('_'):
        continue
    d = json.load(open(f, encoding='utf-8'))
    if ITENS:
        if d.get('tipo') != 'item':
            continue
    elif d.get('tipo') not in ('estrutura', 'canto', 'veiculo') or d['categoria'].startswith(PULAR) or d['nome'].startswith('drone_'):
        continue
    der = DERIVADOS.get(d['nome']) if not ITENS else None
    if SO is None or d['nome'] in SO:
        fazer(f, d, d['nome']); n += 1
    if der and (SO is None or der[0] in SO):
        fazer(f, d, der[0], der[1]); n += 1
print('ICONES', n)
