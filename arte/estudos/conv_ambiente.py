"""Conversor para o jogo dos 67 modelos ambientais e de itens (8 estudos estudo_amb_*.py).
Mantém os nomes, categorias, áreas e tipos de modelos.json, uma única malha por modelo,
origem no centro da base (z = 0), materiais de vento/estação/brilho (P_Folha*, P_Cristal, P_Biomassa, <nome>_Tex)
e limites rígidos de triângulos.

Uso:
  blender -b --factory-startup --python arte/estudos/conv_ambiente.py -- todos
  blender -b --factory-startup --python arte/estudos/conv_ambiente.py -- <nome>
  blender -b --factory-startup --python arte/estudos/para_jogo.py -- <nome>
"""
import os, sys, json, math
import importlib.util as _iu

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELOS = os.path.abspath(os.path.join(AQUI, '..', 'modelos'))
SCRIPTS_ARTE = os.path.abspath(os.path.join(AQUI, '..', 'blender_scripts'))
for _p in (AQUI, SCRIPTS_ARTE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Mapa dos 67 modelos: nome -> (arquivo_estudo, categoria, orcamento_tris)
CATALOGO_AMB = {}
for _esp in ('acacia', 'betula', 'carvalho', 'pinheiro', 'salgueiro', 'fungo_cristal'):
    for _n in range(1, 7):
        CATALOGO_AMB[f'arv_{_esp}_{_n}'] = ('estudo_amb_arvores.py', 'mapa/vegetacao', 500)

for _m in ('arvore_campina_a', 'arvore_campina_b', 'arvore_morta'):
    CATALOGO_AMB[_m] = ('estudo_amb_arvores_soltas.py', 'mapa/vegetacao', 400)

for _m in ('arbusto', 'junco', 'flor_luminosa', 'cacto_cristal'):
    CATALOGO_AMB[_m] = ('estudo_amb_plantas.py', 'mapa/vegetacao', 200)
CATALOGO_AMB['vitoria_regia'] = ('estudo_amb_plantas.py', 'mapa/agua', 200)

for _m in ('cogumelo_gigante_a', 'cogumelo_gigante_b'):
    CATALOGO_AMB[_m] = ('estudo_amb_cogumelos.py', 'mapa/vegetacao', 600)

for _m in ('seixos', 'pedregulho', 'rocha_agua', 'rocha_grande'):
    CATALOGO_AMB[_m] = ('estudo_amb_rochas.py', 'mapa/rochas', 250)

for _m in ('montanha_3x3', 'montanha_5x5'):
    CATALOGO_AMB[_m] = ('estudo_amb_montanhas.py', 'mapa/rochas', 1200)

for _m in ('jazida_ferro', 'jazida_cobre', 'jazida_carvao', 'jazida_pedra',
           'jazida_areia', 'jazida_silex', 'jazida_cristal'):
    CATALOGO_AMB[_m] = ('estudo_amb_jazidas.py', 'mapa/jazidas', 300)

for _m in ('minerio_ferro', 'minerio_cobre', 'carvao', 'pedra',
           'areia', 'silex', 'cristal_bruto', 'biomassa'):
    CATALOGO_AMB[_m] = ('estudo_amb_itens.py', 'itens/recursos', 120)

ESPECIAIS = {
    'P_FolhaCaduca', 'P_FolhaBetula', 'P_FolhaPerene', 'P_FolhaSalgueiro', 'P_FolhaSeca',
    'P_Cristal', 'P_Biomassa', 'P_Seiva',
}

_MODS = {}


def _carregar_mod(arq):
    if arq not in _MODS:
        caminho = os.path.join(AQUI, arq)
        spec = _iu.spec_from_file_location(arq[:-3], caminho)
        mod = _iu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODS[arq] = mod
    return _MODS[arq]


def _construir_objeto(nome):
    estudo_arq, _, _ = CATALOGO_AMB[nome]
    mod = _carregar_mod(estudo_arq)
    if nome.startswith('arv_'):
        partes = nome.rsplit('_', 1)
        esp = partes[0][4:]
        idx = int(partes[1])
        fn = getattr(mod, f'construir_{esp}')
        return fn(idx, pos=(0, 0, 0))
    fn = getattr(mod, f'criar_{nome}')
    return fn()


def _ajustar_caixa_e_base(o, antigo):
    """Garante base em z=0 e caixa dentro da área de modelos.json (ou 0.26 m para itens)."""
    import bmesh
    from mathutils import Vector
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    if bm.verts:
        z_min = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.z -= z_min
        xs = [v.co.x for v in bm.verts]
        ys = [v.co.y for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        cx = (min(xs) + max(xs)) * 0.5
        cy = (min(ys) + max(ys)) * 0.5
        if antigo.get('tipo') == 'item':
            # Centraliza XY nos itens e garante que caibam em [-0.125, 0.125] e z <= 0.255
            for v in bm.verts:
                v.co.x -= cx
                v.co.y -= cy
            max_xy = max(max(abs(v.co.x), abs(v.co.y)) for v in bm.verts)
            if max_xy > 0.125:
                f = 0.125 / max_xy
                for v in bm.verts:
                    v.co.x *= f
                    v.co.y *= f
            z_max = max(v.co.z for v in bm.verts)
            if z_max > 0.255:
                fz = 0.255 / z_max
                for v in bm.verts:
                    v.co.z *= fz
        else:
            w, d = antigo.get('area', [1, 1])
            lim_x = w * 0.48
            lim_y = d * 0.48
            # Se o centro da caixa sair da meia-área ou algum vértice passar de 0.48 * área, reencaixa
            if abs(cx) > w * 0.18 or abs(cy) > d * 0.18:
                # Move suavemente mantendo a base próxima ao centro
                for v in bm.verts:
                    u_z = min(1.0, v.co.z / max(0.25, max(zs)))
                    v.co.x -= cx * (0.4 + 0.6 * u_z)
                    v.co.y -= cy * (0.4 + 0.6 * u_z)
            max_x = max(abs(v.co.x) for v in bm.verts)
            max_y = max(abs(v.co.y) for v in bm.verts)
            fx = min(1.0, lim_x / max(max_x, 1e-6))
            fy = min(1.0, lim_y / max(max_y, 1e-6))
            f = min(fx, fy)
            if f < 1.0:
                for v in bm.verts:
                    v.co.x *= f
                    v.co.y *= f
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    o.location = Vector((0, 0, 0))
    o.rotation_euler = (0, 0, 0)
    o.scale = (1, 1, 1)


def _material_paleta(nome):
    import bpy, lib_pf
    d = lib_pf.PALETA[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*d['c'], 1.0)
    b.inputs['Roughness'].default_value = d['r']
    b.inputs['Metallic'].default_value = d['m']
    b.inputs['Emission Strength'].default_value = d['e']
    if d['e']:
        b.inputs['Emission Color'].default_value = (*d['c'], 1.0)
    m.diffuse_color = (*d['c'], 1.0)
    return m


def _preencher_vazios(img, voltas=32):
    import numpy as np
    W, H = img.size
    a = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(H, W, 4)
    vazio = a[:, :, :3].max(2) <= 0.0
    for _ in range(voltas):
        if not vazio.any():
            break
        cheio = ~vazio
        soma = np.zeros((H, W, 3), np.float32)
        n = np.zeros((H, W), np.float32)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c = np.roll(cheio, d, (0, 1))
            soma += np.roll(a[:, :, :3], d, (0, 1)) * c[..., None]
            n += c
        novo = vazio & (n > 0)
        a[novo, :3] = soma[novo] / n[novo][:, None]
        vazio &= ~novo
    a[:, :, 3] = 1.0
    img.pixels.foreach_set(a.ravel())


def _assar_e_compactar_materiais(sc, o, nome, antigo):
    """Assa os materiais procedurais (tronco, rocha, minério, folha opaca) em <nome>_Tex e preserva ESPECIAIS."""
    import bpy, bmesh
    me = o.data
    w, d = antigo.get('area', [1, 1])
    tipo = antigo.get('tipo', 'estrutura')
    lado = 256 if tipo in ('item', 'deco') else (512 if w * d <= 1 else 1024)

    # Desdobra UV na malha única
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    me.uv_layers.active = me.uv_layers[0]
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=0.015, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    nomes_slots = [m.name.split('.')[0] if m else 'P_Rocha' for m in me.materials]
    tem_nao_especial = any(n not in ESPECIAIS for n in nomes_slots)

    mat_tex = None
    if tem_nao_especial:
        img = bpy.data.images.new(nome + '_tex', lado, lado, alpha=False)
        # Prepara cada slot para assar a cor difusa (metálico = 0, especiais neutros para não vazar cor no atlas)
        for idx, m in enumerate(list(me.materials)):
            if m is None:
                continue
            n_base = nomes_slots[idx]
            cp = m.copy()
            cp.use_nodes = True
            nt = cp.node_tree
            for nd in nt.nodes:
                if nd.type == 'BSDF_PRINCIPLED':
                    ent_m = nd.inputs['Metallic']
                    for l in list(ent_m.links):
                        nt.links.remove(l)
                    ent_m.default_value = 0.0
                    if n_base in ESPECIAIS:
                        for l in list(nd.inputs['Base Color'].links):
                            nt.links.remove(l)
                        nd.inputs['Base Color'].default_value = (0.06, 0.06, 0.06, 1.0)
                        if 'Emission Strength' in nd.inputs:
                            for l in list(nd.inputs['Emission Strength'].links):
                                nt.links.remove(l)
                            nd.inputs['Emission Strength'].default_value = 0.0
            ti = nt.nodes.new('ShaderNodeTexImage')
            ti.image = img
            nt.nodes.active = ti
            me.materials[idx] = cp

        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 10
        sc.render.bake.use_selected_to_active = False
        sc.render.bake.margin_type = 'EXTEND'
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=max(6, lado // 32), use_clear=True)
        _preencher_vazios(img)
        caminho_png = os.path.join(bpy.app.tempdir, nome + '_tex.png')
        img.filepath_raw = caminho_png
        img.file_format = 'PNG'
        img.save()
        img.pack()

        mat_tex = bpy.data.materials.new(nome + '_Tex')
        mat_tex.use_nodes = True
        nt = mat_tex.node_tree
        bsdf = nt.nodes['Principled BSDF']
        bsdf.inputs['Roughness'].default_value = 0.78
        bsdf.inputs['Metallic'].default_value = 0.0
        tx = nt.nodes.new('ShaderNodeTexImage')
        tx.image = img
        nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color'])
        nt.nodes.active = tx

    # Compacta slots: um único slot para <nome>_Tex + um slot por material especial usado
    novos_mats = []
    mapa_novo = {}
    if mat_tex is not None:
        mapa_novo['_TEX_'] = 0
        novos_mats.append(mat_tex)

    remap_slot = {}
    for idx, n_base in enumerate(nomes_slots):
        if n_base in ESPECIAIS:
            if n_base not in mapa_novo:
                mapa_novo[n_base] = len(novos_mats)
                novos_mats.append(_material_paleta(n_base))
            remap_slot[idx] = mapa_novo[n_base]
        else:
            remap_slot[idx] = mapa_novo['_TEX_']

    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        f.material_index = remap_slot.get(f.material_index, 0)
    # Remove slots que por acaso não tenham nenhuma face
    usados = sorted({f.material_index for f in bm.faces})
    compacto = {velho: i for i, velho in enumerate(usados)}
    for f in bm.faces:
        f.material_index = compacto[f.material_index]
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    for velho in usados:
        me.materials.append(novos_mats[velho])
    me.update()


def converter_um(nome):
    """Converte um modelo ambiental ou item diretamente para arte/modelos/<cat>/<nome>/<nome>.glb e .json."""
    import bpy
    from mathutils import Vector
    import amb_comum as amb

    estudo_arq, cat, orc_tris = CATALOGO_AMB[nome]
    pasta = os.path.join(MODELOS, cat, nome)
    json_arq = os.path.join(pasta, nome + '.json')
    antigo = json.load(open(json_arq, encoding='utf-8'))

    sc = amb.iniciar_cena(semente=101)
    o = _construir_objeto(nome)
    # Remove qualquer outro objeto que não seja o modelo
    for outro in list(sc.objects):
        if outro is not o:
            bpy.data.objects.remove(outro, do_unlink=True)

    _ajustar_caixa_e_base(o, antigo)
    _assar_e_compactar_materiais(sc, o, nome, antigo)

    o.name = nome + '_corpo'
    o.data.name = nome + '_corpo'
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    o.parent = raiz
    bpy.context.view_layer.update()

    o.data.calc_loop_triangles()
    n_tris = len(o.data.loop_triangles)
    assert n_tris <= orc_tris, f'{nome}: {n_tris} tris > limite {orc_tris}'

    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    dims = [round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)]

    bpy.ops.object.select_all(action='DESELECT')
    raiz.select_set(True)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    glb = os.path.join(pasta, nome + '.glb')
    bpy.ops.export_scene.gltf(
        filepath=glb,
        use_selection=True,
        export_yup=True,
        export_animations=False,
        export_image_format='JPEG',
    )

    antigo.update(
        tris=n_tris,
        dims=dims,
        partes=[dict(nome='corpo', pai=None, pivo=[0.0, 0.0, 0.0])],
        anima=False,
        estudo=estudo_arq,
    )
    json.dump(antigo, open(json_arq, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'CONV_AMB ok {nome:22s} | tris={n_tris:4d}/{orc_tris:4d} | dims={dims} | mats={[m.name.split(".")[0] for m in o.data.materials]}')


# CONFIG para compatibilidade com para_jogo.py
CONFIG = {
    nome: dict(
        script='conv_ambiente.py',
        args=[nome],
        estudo=estudo_arq,
        cat=cat,
        tris=orc_tris,
        tex=256 if cat.startswith('itens') else 512,
        tirar=['EFEITO_'],
        anima=False,
    )
    for nome, (estudo_arq, cat, orc_tris) in CATALOGO_AMB.items()
}


if __name__ == '__main__':
    _args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['todos']
    _alvo = _args[0] if _args else 'todos'
    if _alvo == 'todos':
        for _n in CATALOGO_AMB:
            converter_um(_n)
        print(f'CONV_AMB TODOS OK: {len(CATALOGO_AMB)} modelos convertidos.')
    elif _alvo in CATALOGO_AMB:
        converter_um(_alvo)
