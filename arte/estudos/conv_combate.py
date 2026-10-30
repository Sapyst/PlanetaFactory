"""Entradas do para_jogo.py para o combate da era base: torre_metralhadora (estudo_metralhadora.py) e o muro de tijolo
muro_tijolo / muro_tijolo_lado (estudo_muros_mina.py, grupo 'tijolo'; liga, campo e mina ficam para a fase 2.4).

O que os ganchos fazem (o para_jogo.py não muda):
- torre_metralhadora: pose do quadro 1 do laço (implantada: pernas cravadas, cabeça no alto, trava recolhida). A arma
  do estudo aponta para +X; o jogo mira com o canhão em +Y do Blender (−Z do Godot) quando o giro está em 0: o gancho
  vira o giro para +Y e separa por hierarquia: giro (cabeça, garfo, caixa de munição, cinta, radar, casulo do sensor),
  canhao (culatra, motores, escudo, calhas) e tambor (feixe de 6 canos, gira no próprio eixo quando atira). LEDs e olho
  viram partes que brilham (luzg no giro, luzc no canhão). A elevação do estudo (≈4°) fica: o eixo do tambor vai para
  o .json ("eixo_tambor", Blender) junto com a boca dos canos ("boca") e a saída da calha de cápsulas ("ejecao"),
  que o jogo usa para o clarão e para ejetar a cápsula com fumacinha a cada tiro. Tiram-se os efeitos (clarão,
  traçantes, cápsulas e elos voando, fumaça, fiapos) e o acúmulo de cápsulas no chão (no jogo as cápsulas caem e
  somem). Brasa dos canos zerada (no jogo o cano não brilha parado); o cabo espiral do mastro fica na forma esticada.
- muro_tijolo / muro_tijolo_lado: como o muro de pedra (conv_defesa_energia.py), o estudo é rico demais (tijolo a
  tijolo, lascas, entulho) para 400–900 triângulos: o gancho refaz a peça do estudo na origem (pilar sem pano / pano
  norte), troca a malha baixa por uma casca simples na silhueta (sapata, alvenaria, cinta de concreto, capa, espetos
  de vergalhão, emissor) e o para_jogo assa nela a cor do modelo detalhado.
Rodar: blender -b --python para_jogo.py -- <nome>"""
import bpy, bmesh, math, sys
from mathutils import Vector

import importlib.util as _iu, os as _os
_spec = _iu.spec_from_file_location('conv_defesa_energia', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'conv_defesa_energia.py'))
_de = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_de)

PI = math.pi
_g, _apagar, _vivos, _marcar, _limite_brilho = _de._g, _de._apagar, _de._vivos, _de._marcar, _de._limite_brilho
_caixa, _espeto, _prisma, _tronco = _de._caixa, _de._espeto, _de._prisma, _de._tronco


def _r3(v):
    return [round(float(x), 4) for x in v]


# ------------------------------------------------------------------ metralhadora
_MET = {}


def metralhadora_montar(sc):
    g = _g()
    giro = bpy.data.objects['giro']
    canhao = bpy.data.objects['canhao']
    tambor = bpy.data.objects['tambor']
    for o in sc.objects:                              # pose do quadro 1 fica; animação sai
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys:    # cabo espiral: forma do quadro 1 (esticado)
            ks = o.data.shape_keys.key_blocks
            if 'Esticado' in ks:
                ks['Esticado'].value = 1.0
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            o.select_set(False)
    for m in bpy.data.materials:                      # canos sem brasa (não viram peça que brilha)
        if m.name.startswith('Canos') and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    e = n.inputs['Emission Strength']
                    for l in list(e.links):
                        m.node_tree.links.remove(l)
                    e.default_value = 0.0
    for o in list(sc.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    giro.rotation_euler = (0, 0, PI / 2)              # arma do estudo em +X → +Y (frente do jogo)
    tambor.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    # pivôs e pontos que o jogo usa (Blender, giro em 0)
    mc = canhao.matrix_world
    mt = tambor.matrix_world
    _MET['giro'] = giro.matrix_world.translation.copy()
    _MET['canhao'] = mc.translation.copy()
    _MET['tambor'] = mt.translation.copy()
    _MET['eixo'] = (mt.to_3x3() @ Vector((1, 0, 0))).normalized()
    _MET['boca'] = mc @ Vector((0.93, 0.0, 0.0))
    _MET['ejecao'] = mc @ Vector((-0.21, -0.16, -0.15))
    p = CONFIG['torre_metralhadora']['partes']
    for k in ('giro', 'canhao', 'tambor'):
        p[k]['pivo'] = tuple(round(x, 4) for x in _MET[k])
    p['luzg']['pivo'] = p['giro']['pivo']
    p['luzc']['pivo'] = p['canhao']['pivo']
    _marcar(tambor, 'PTAM__', 'PTLUZ__', g)
    _marcar(canhao, 'PCAN__', 'PCLUZ__', g, pular=(tambor,))
    _marcar(giro, 'PGIRO__', 'PGLUZ__', g, pular=(canhao,))
    _limite_brilho(g, 120)


def metralhadora_exportar(sc, raiz, dados):
    dados['eixo_tambor'] = _r3(_MET['eixo'])
    dados['boca'] = _r3(_MET['boca'])
    dados['ejecao'] = _r3(_MET['ejecao'])
    dados['vel_ejecao'] = [-0.3, -0.78, -0.1]                # (frente, esquerda, cima) m/s: cápsula sai para a direita, atrás
    dados['descricao'] = ('Metralhadora 2×2: casco blindado sobre laje, quatro estabilizadores cravados, mastro com a '
                          'cabeça giratória (garfo, caixa de munição com cinta, casulo sensor com olho violeta) e arma '
                          'gatling de 6 canos com escudo amassado. Munição entra pelo sul (S1). Partes: base, giro (gira '
                          'em Z), canhao (filho do giro), tambor (gira em eixo_tambor), luzg/luzc. Pontos (Blender, giro '
                          '0): boca dos canos e ejecao (saída da calha de cápsulas).')


# ------------------------------------------------------------------ muro de tijolo
TB, ZT_0, ZT_C0, ZT_C1, ZT_T = 0.30, 0.06, 0.70, 0.82, 1.40
HZ_UP = (ZT_T - ZT_C1) / 8
ZT_P, ZT_PC = ZT_C1 + 4 * HZ_UP, ZT_C1 + 5 * HZ_UP
PXT = 0.11


def casca_tijolo_pilar():
    bm = bmesh.new()
    _caixa(bm, (-0.325, -0.325, 0.0), (0.325, 0.325, ZT_0))
    _caixa(bm, (-TB - 0.006, -TB - 0.006, ZT_0), (TB + 0.006, TB + 0.006, ZT_C0))
    _caixa(bm, (-0.315, -0.315, ZT_C0), (0.315, 0.315, ZT_C1))
    _caixa(bm, (-TB - 0.006, -TB - 0.006, ZT_C1), (TB + 0.006, TB + 0.006, ZT_T))
    _caixa(bm, (-0.32, -0.32, ZT_T), (0.32, 0.32, ZT_T + 0.07))
    zt = ZT_T + 0.07
    for x in (-0.25, -0.125, 0.0, 0.125, 0.25):
        for y in (-0.25, 0.25):
            _espeto(bm, (x, y, zt), 0.0085, 0.05)
    for x in (-0.25, 0.25):
        for y in (-0.125, 0.0, 0.125):
            _espeto(bm, (x, y, zt), 0.0085, 0.05)
    _prisma(bm, (0, 0, 0), 0.055, zt, zt + 0.008)                 # emissor da IA
    _prisma(bm, (0, 0, 0), 0.036, zt + 0.008, zt + 0.04)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def casca_tijolo_pano():
    """Pano local: da face do pilar (y = 0,30) até a borda norte."""
    bm = bmesh.new()
    _caixa(bm, (-0.125, TB, 0.0), (0.125, 0.5, ZT_0))
    _caixa(bm, (-PXT - 0.004, TB - 0.004, ZT_0), (PXT + 0.004, 0.5, ZT_C0))
    _caixa(bm, (-0.125, TB - 0.004, ZT_C0), (0.125, 0.5, ZT_C1))
    _caixa(bm, (-PXT - 0.004, TB - 0.004, ZT_C1), (PXT + 0.004, 0.5, ZT_P))
    _caixa(bm, (-0.13, TB - 0.004, ZT_P), (0.13, 0.5, ZT_PC))
    for x, y in ((-0.07, 0.36), (0.07, 0.36), (0.0, 0.41), (-0.07, 0.46), (0.07, 0.46)):
        _espeto(bm, (x, y, ZT_PC), 0.0085, 0.045)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _funcao_muros(nome):
    import gc
    for f in gc.get_objects():
        if callable(f) and getattr(f, '__name__', '') == nome and getattr(getattr(f, '__code__', None), 'co_filename', '').endswith('estudo_muros_mina.py'):
            return f
    raise RuntimeError('função do estudo não achada: ' + nome)


def _refazer(sc, fazer):
    for o in _vivos(sc):                              # cena com os três muros e a mina: refaz só a peça, na origem
        if o.type in ('MESH', 'EMPTY', 'LIGHT'):
            _apagar(o)
    fazer()
    for o in list(sc.objects):
        o.animation_data_clear()
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    g = _g()
    for o in _vivos(sc):
        if o.type == 'MESH' and any(g['vidro'](s.material) or g['tem_volume'](s.material) or g['mancha_suave'](s.material)
                                    for s in o.material_slots):
            _apagar(o)
    return g


def muro_tijolo_montar(sc):
    g = _refazer(sc, lambda: _funcao_muros('tijolo_centro')('mtij_c', 0.0, 0.0, (), 300))
    # o anel violeta do emissor continua peça que brilha (P_Cristal), em cima do emissor da casca
    _limite_brilho(g, 80, casca_tijolo_pilar, 'muro_tijolo_corpo')


def muro_tijolo_lado_montar(sc):
    g = _refazer(sc, lambda: _funcao_muros('tijolo_lado')('mtij_l', 0.0, 0.0, 0, 331))
    _limite_brilho(g, 80, casca_tijolo_pano, 'muro_tijolo_lado_corpo')


# ------------------------------------------------------------------ entradas
CONFIG = {
    'torre_metralhadora': dict(
        script='estudo_metralhadora.py', cat='defesa', tris=6000, tex=1024, corpo='base', anima=False,
        tirar=['capsula_ejetada', 'capsula_anterior', 'elo_ejetado', 'elo_anterior', 'tracante', 'clarao', 'fiapo',
               'fumaca', 'acumulo_capsulas', 'acumulo_elos'],
        depois_de_montar=metralhadora_montar, antes_de_exportar=metralhadora_exportar,
        partes={
            'giro': dict(objetos=['PGIRO__'], pivo=(0.0, 0.0, 0.97), pai='base', tris=1400),
            'luzg': dict(objetos=['PGLUZ__'], pivo=(0.0, 0.0, 0.97), pai='giro', tris=160),
            'canhao': dict(objetos=['PCAN__'], pivo=(0.0, 0.0, 1.29), pai='giro', tris=1000),
            'luzc': dict(objetos=['PCLUZ__'], pivo=(0.0, 0.0, 1.29), pai='canhao', tris=60),
            'tambor': dict(objetos=['PTAM__'], pivo=(0.0, 0.0, 1.29), pai='canhao', tris=800),
        }),
    'muro_tijolo': dict(
        script='estudo_muros_mina.py', cat='defesa', tris=900, tex=512, anima=False, tirar=[],
        depois_de_montar=muro_tijolo_montar),
    'muro_tijolo_lado': dict(
        script='estudo_muros_mina.py', cat='defesa', tris=500, tex=512, anima=False, tirar=[],
        depois_de_montar=muro_tijolo_lado_montar),
}
