"""Pranchas de coerência: itens em cima de esteiras e estruturas lado a lado na grade.
Uso: blender --background --python prancha.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib_pf; importlib.reload(lib_pf)
from lib_pf import Modelo, esteira_trecho, reto, preparar_cena, render, TOPO_LONA, RAIZ
import itens; importlib.reload(itens)
import logistica as L; importlib.reload(L)
import maquinas as MQ; importlib.reload(MQ)
import mapa as MP; importlib.reload(MP)
import transporte as TR; importlib.reload(TR)
import random
from mathutils import Vector
PI = math.pi

def faixa_esteira(n, y):
    m = Modelo(f'_esteira_{y}', '_tmp', w=n, d=1); p = m.parte()
    for i in range(n):
        x = -n/2 + 0.5 + i
        esteira_trecho(p, reto((x - 0.5, 0, 0), (x + 0.5, 0, 0)))
    m.montar()
    for o in m.objs: o.location.y = y
    return m.objs

def prancha_itens():
    preparar_cena(); objs = []
    grupos = [itens.TODOS[:8], itens.TODOS[8:16], itens.TODOS[16:]]
    for gi, g in enumerate(grupos):
        y = -gi*1.2; objs += faixa_esteira(len(g), y)
        for i, fn in enumerate(g):
            m = fn(); m.montar()
            for o in m.objs:
                if o.parent is None: o.location = (-len(g)/2 + 0.5 + i, y, TOPO_LONA)
            objs += m.objs
    bpy = lib_pf.bpy; bpy.context.view_layer.update()
    render(objs, os.path.join(RAIZ, 'itens', '_prancha_itens.png'), res=(1600, 900), margem=1.08, direcao=(0.35, -1, 0.9))

def prancha_itens_perto():
    preparar_cena(); objs = []
    for i, fn in enumerate(itens.TODOS):
        m = fn(); m.montar()
        for o in m.objs:
            if o.parent is None: o.location = ((i % 5)*0.4, -(i // 5)*0.4, 0)
        objs += m.objs
    lib_pf.bpy.context.view_layer.update()
    render(objs, os.path.join(RAIZ, 'itens', '_prancha_itens_perto.png'), res=(1400, 1400), margem=1.05, direcao=(0.6, -1, 0.9))

def colocar(fn, x, y, z=0.0, rot=0.0):
    m = fn(); m.montar()
    for o in m.objs:
        if o.parent is None: o.location = (x, y, z); o.rotation_euler = (0, 0, rot)
    return m.objs

def chao(w, d, cx=0, cy=0):
    m = Modelo('_chao', '_tmp', w=w, d=d); p = m.parte()
    for i in range(w):
        for j in range(d):
            x = -w/2 + i; y = -d/2 + j
            p.caixa(x + 0.005, x + 0.995, y + 0.005, y + 0.995, -0.02, 0.0, 'P_Concreto' if (i + j) % 2 else 'P_Pedra')
    m.montar()
    for o in m.objs: o.location = (cx, cy, 0)
    return m.objs

def pilar(x, y, h):
    objs = []; n = int(round(h/0.5)) - 1
    objs += colocar(L.pilar_base, x, y)
    for k in range(n): objs += colocar(L.pilar_segmento, x, y, 0.5*k)
    objs += colocar(L.pilar_topo, x, y, 0.5*n)
    return objs

def prancha_logistica():
    preparar_cena(); o = []; E = -PI/2
    o += chao(12, 9, 0.0, 0.0)
    # linha principal com subida, trecho elevado sobre um baú e descida
    o += colocar(L.esteira_inicio, -4.5, -0.5, 0, E); o += colocar(L.esteira_reta, -3.5, -0.5, 0, E)
    o += colocar(L.divisor, -2.5, -0.5, 0, E)
    o += colocar(L.esteira_rampa, -1.5, -0.5, 0.0, E); o += colocar(L.esteira_rampa, -0.5, -0.5, 0.5, E)
    o += colocar(L.esteira_reta, 0.5, -0.5, 1.0, E); o += colocar(L.esteira_reta, 1.5, -0.5, 1.0, E)
    o += colocar(L.esteira_rampa, 2.5, -0.5, 0.5, PI/2); o += colocar(L.esteira_rampa, 3.5, -0.5, 0.0, PI/2)
    o += colocar(L.esteira_fim, 4.5, -0.5, 0, E)
    o += colocar(L.bau, 0.5, -0.5); o += colocar(L.cano_reto, 1.5, -0.5, 0, E)       # embaixo do trecho elevado
    for x, h in ((-1.0, 0.5), (0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 0.5)):
        for y in (-1.0, 0.0): o += pilar(x, y, h)
    # saída lateral do divisor -> braço -> baú
    o += colocar(L.esteira_reta, -2.5, 0.5); o += colocar(L.esteira_fim, -2.5, 1.5)
    o += colocar(L.braco, -2.5, 2.5); o += colocar(L.bau, -2.5, 3.5)
    o += colocar(L.braco_longo, -0.5, 2.5); o += colocar(L.braco_rapido, 0.5, 2.5)
    o += colocar(L.juncao, 2.5, 2.5); o += colocar(L.esteira_curva_dir, 3.5, 1.5); o += colocar(L.esteira_curva_esq, 4.5, 1.5)
    # rede de canos
    o += colocar(L.bomba, -4.5, -3.5); o += colocar(L.cano_curva, -4.5, -2.5)
    o += colocar(L.cano_reto, -3.5, -2.5, 0, E); o += colocar(L.cano_t, -2.5, -2.5, 0, PI/2)
    o += colocar(L.cano_cruz, -1.5, -2.5); o += colocar(L.cano_reto, -0.5, -2.5, 0, E)
    lib_pf.bpy.context.view_layer.update()
    render(o, os.path.join(RAIZ, 'logistica', '_prancha_logistica.png'), res=(1600, 1200), margem=1.02, direcao=(0.55, -1, 0.95))
    render(o, os.path.join(RAIZ, 'logistica', '_prancha_logistica_lado.png'), res=(1600, 900), margem=1.02, direcao=(0.05, -1, 0.35))

def com_portas(fn, x, y):
    m = fn(); m.montar(); objs = list(m.objs)
    for o in m.objs:
        if o.parent is None: o.location = (x, y, 0)
    for pt in m.portas:
        c = Vector((x, y, 0)) + Vector((pt['pos'].x, pt['pos'].y, 0)) + pt['dir']*0.5
        rot = math.atan2(-pt['dir'].x, pt['dir'].y) + (PI if pt['io'] == 'ENT' else 0)
        objs += colocar(L.esteira_reta if pt['tipo'] == 'ITEM' else L.cano_reto, c.x, c.y, 0, rot)
    return objs

def prancha_maquinas():
    preparar_cena(); o = []
    o += chao(22, 12, 0, 0)
    pos = [(MQ.extrator_cristal, -8.5, 2.5), (MQ.broca_minerio, -5, 3), (MQ.fornalha, -2, 3), (MQ.montadora, 1.5, 2.5),
           (MQ.refinador, 6.5, 2.5), (MQ.laboratorio, -8.5, -3.5), (MQ.gerador, -5, -3), (MQ.tanque, -1, -3),
           (MQ.torre_defesa, 3, -3), (MQ.poste_energia, 5.5, -2.5)]
    for fn, x, y in pos: o += com_portas(fn, x, y)
    for i in range(4):
        o += colocar(MQ.muro_centro, 7.5 + i, -3.5)
        if i < 3: o += colocar(MQ.muro_lado, 7.5 + i, -3.5, 0, -PI/2)
        if i > 0: o += colocar(MQ.muro_lado, 7.5 + i, -3.5, 0, PI/2)
    lib_pf.bpy.context.view_layer.update()
    render(o, os.path.join(RAIZ, 'maquinas', '_prancha_maquinas.png'), res=(1800, 1100), margem=1.02, direcao=(0.5, -1, 0.95))

def chao_textura(nome, w, d, cx, cy, rep=4.0):
    bpy = lib_pf.bpy
    me = bpy.data.meshes.new('chao_' + nome)
    me.from_pydata([(-w/2, -d/2, 0), (w/2, -d/2, 0), (w/2, d/2, 0), (-w/2, d/2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, (u, v) in enumerate(((0, 0), (w/rep, 0), (w/rep, d/rep), (0, d/rep))): uv.data[i].uv = (u, v)
    mt = bpy.data.materials.new('T_' + nome); mt.use_nodes = True
    tex = mt.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(RAIZ, '..', 'texturas', nome + '.png'))
    mt.node_tree.links.new(tex.outputs['Color'], mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    me.materials.append(mt); o = bpy.data.objects.new('chao_' + nome, me); bpy.context.scene.collection.objects.link(o)
    o.location = (cx, cy, 0); return [o]

BIOMAS = [('campina', [MP.arvore_campina_a, MP.arvore_campina_b, MP.arbusto, MP.pedregulho], [MP.grama_tufo, MP.flor_luminosa], MP.jazida_ferro),
          ('floresta_fungica', [MP.cogumelo_gigante_a, MP.cogumelo_gigante_b], [MP.flor_luminosa, MP.seixos], MP.poca_seiva),
          ('deserto_silex', [MP.cacto_cristal, MP.pedregulho], [MP.seixos], MP.jazida_silex),
          ('planalto_rochoso', [MP.pedregulho, MP.rocha_grande], [MP.seixos], MP.jazida_cobre),
          ('campo_cristal', [MP.cacto_cristal, MP.pedregulho], [MP.seixos], MP.jazida_cristal),
          ('pantano', [MP.arvore_morta, MP.rocha_agua], [MP.junco, MP.vitoria_regia], MP.jazida_carvao),
          ('cinzal', [MP.arvore_morta, MP.pedregulho], [MP.seixos], MP.jazida_pedra)]

def prancha_biomas():
    preparar_cena(); bpy = lib_pf.bpy; o = []
    sc = bpy.context.scene; sc.display.shading.color_type = 'TEXTURE'
    rnd = random.Random(5); W = 6
    for bi, (nome, bloq, deco, jaz) in enumerate(BIOMAS):
        cx = (bi % 4)*(W + 1); cy = -(bi // 4)*(W + 1)
        o += chao_textura(nome, W, W, cx, cy)
        ocup = set()
        def livre(i, j): return (i, j) not in ocup
        for k in range(9):
            i, j = rnd.randrange(W), rnd.randrange(W)
            if livre(i, j):
                ocup.add((i, j)); fn = bloq[k % len(bloq)]
                if fn is MP.rocha_grande:
                    if i < W - 1 and j < W - 1 and all(livre(i + a, j + b) for a in (0, 1) for b in (0, 1)):
                        ocup |= {(i + a, j + b) for a in (0, 1) for b in (0, 1)}; o += colocar(fn, cx - W/2 + i + 1, cy - W/2 + j + 1)
                    continue
                o += colocar(fn, cx - W/2 + i + 0.5, cy - W/2 + j + 0.5, 0, rnd.uniform(0, 6.28))
        for k in range(3):
            i, j = rnd.randrange(W), rnd.randrange(W)
            if livre(i, j): ocup.add((i, j)); o += colocar(jaz, cx - W/2 + i + 0.5, cy - W/2 + j + 0.5, 0, rnd.uniform(0, 6.28))
        for k in range(14):
            fn = deco[k % len(deco)]
            o += colocar(fn, cx + rnd.uniform(-W/2 + 0.3, W/2 - 0.3), cy + rnd.uniform(-W/2 + 0.3, W/2 - 0.3), 0.001, rnd.uniform(0, 6.28))
    # montanhas e água num quadro extra
    cx, cy = 3*(W + 1), -(W + 1)
    o += chao_textura('planalto_rochoso', W, W, cx, cy - 0.0)
    o += colocar(MP.montanha_5x5, cx - 0.5, cy - 0.5); 
    bpy.context.view_layer.update()
    for x in o:
        if x.type == 'MESH' and x.name.startswith('chao_') is False:
            for m in x.data.materials:
                if m and not m.node_tree.nodes.get('Image Texture'): pass
    render(o, os.path.join(RAIZ, 'mapa', '_prancha_biomas.png'), res=(2000, 1100), margem=1.02, direcao=(0.35, -1, 1.1))

def prancha_transporte():
    preparar_cena(); o = []; E = -PI/2
    o += chao(14, 18, 0, 0)
    o += colocar(TR.trilho_fim, -1.5, -8.5, 0, PI)
    for k in range(12): o += colocar(TR.trilho_reto, -1.5, -7.5 + k)
    o += colocar(TR.trilho_curva, -0.5, 5.5)
    for k in range(3): o += colocar(TR.trilho_reto, 1.5 + k, 6.5, 0, E)
    o += colocar(TR.trilho_fim, 4.5, 6.5, 0, E)
    o += com_portas(TR.estacao, 0.0, -1.0)
    o += colocar(TR.sinal_trem, -2.5, 2.5)
    z = 0.12 + 0.14
    o += colocar(TR.locomotiva, -1.5, 2.0, z); o += colocar(TR.vagao_carga, -1.5, -1.05, z); o += colocar(TR.vagao_tanque, -1.5, -4.1, z)
    lib_pf.bpy.context.view_layer.update()
    render(o, os.path.join(RAIZ, 'transporte', '_prancha_transporte.png'), res=(1600, 1400), margem=1.02, direcao=(0.9, -0.7, 0.9))

if __name__ == '__main__':
    if 'transporte' in sys.argv: prancha_transporte()
    elif 'biomas' in sys.argv: prancha_biomas()
    elif 'maquinas' in sys.argv: prancha_maquinas()
    elif 'logistica' in sys.argv: prancha_logistica()
    else: prancha_itens(); prancha_itens_perto()
