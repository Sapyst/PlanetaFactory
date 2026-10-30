"""Entradas do para_jogo.py para o combate do meio (fase 2.4 do docs/PLANO_INTEGRACAO.md).

Lança-foguetes (torre_foguetes, 3×3) ← estudo_lanca_foguetes.py: pose do quadro 1 do laço (posição de carga: giro a
  90°, casulo de 9 tubos deitado e virado para +Y do Blender, que é a frente do jogo com o giro em 0). Partes: giro
  (mesa, placa, pistões de elevação, radar do mastro) e canhao (casulo, tubos, tampas fechadas, foguetes nos tubos),
  filho do giro. O braço carregador, o paiol (boca S1) e a unidade hidráulica ficam no corpo. Saem os efeitos (fogo,
  rastros, clarões, foguetes em voo), as sobras no chão (selos e meias-cascas de salvas anteriores, cratera) e o
  foguete da esteira de fora. Pontos para o jogo (Blender, giro 0): boca (frente do tubo do meio) e ejecao (traseira
  do casulo: o selo traseiro sai por ali a cada disparo, com a fumaça do jato).
Mina de pulso (mina_pulso, 1×1) ← estudo_muros_mina.py, coleção 'mina' no quadro 1 (armada: tampa fechada, LED
  vermelho); sai o resto da cena (os muros montados na mesma origem) e os efeitos do disparo (onda, arcos, faíscas,
  torrões, poeira). Fixa (o pulso o jogo desenha: anel no chão).
Muro de liga (muro_liga / muro_liga_lado) e muro de campo (muro_escudo / muro_escudo_lado) ← estudo_muros_mina.py,
  como o muro de tijolo (conv_combate.py): o gancho refaz a peça do estudo na origem (pilar sem pano; pano norte) e
  a malha baixa vem da redução com o miúdo enxugado (parafusos, decalques). No pano do campo a parede translúcida e
  os arcos saem: o jogo desenha a parede de campo por cima do trilho (shader campo_escudo, render/shaders).
Gerador de escudo (gerador_escudo, 2×2) ← estudo_gerador_escudo.py com a animação do laço ("trabalho": cardã de três
  anéis girando, cristal, pistões ajustando os emissores, ventoinhas do radiador), que o jogo toca enquanto o escudo
  tem carga. Saem a bolha hexagonal (o jogo desenha a sua, shader campo_escudo, no raio da regra), o fio de luz até o
  topo da bolha, o feixe, os impactos (cuspe ácido, projétil, respingos), arcos, faíscas, fumaça do capacitor, os
  blocos de máquina de fora e as pedras do chão; o que passa da área 2×2 é recortado.
Artilharia (artilharia, 3×3) ← estudo_artilharia.py na pose do quadro 50 (carregada e elevada a 55°, cunha fechada,
  antes do disparo): no jogo o obus fica nessa elevação (só mira ninhos longe) e o giro só gira em Z; o cano de 3,7 m
  passa da área, mas a 55° a ponta fica acima de 3,6 m na borda (não varre as peças vizinhas). Partes: giro
  (plataforma, paiol com granadas, carregador, cilindros de elevação, telêmetro com radar) e canhao (berço, cano,
  freio de boca, culatra), filho do giro. Saem os estojos velhos do chão, a granada que entrava, o estojo ejetado, os
  efeitos do tiro e os pinhões dos motores de giro com o eixo (a coroa gira e eles ficariam parados, cruzando os
  dentes; o eixo entrava no convés que gira).
  Pontos: boca (freio de boca) e ejecao (atrás da culatra, lado da calha: o estojo sai a cada tiro).
Rodar: blender -b --python para_jogo.py -- <nome>"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_defesa_energia', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conv_defesa_energia.py'))
_de = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_de)

_spec = _iu.spec_from_file_location('conv_esteiras_bracos', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conv_esteiras_bracos.py'))
_eb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eb)

PI = math.pi
_g, _apagar, _vivos, _marcar, _limite_brilho, _tirar = _de._g, _de._apagar, _de._vivos, _de._marcar, _de._limite_brilho, _de._tirar


def _r3(v):
    return [round(float(x), 4) for x in v]


def _sem_animacao_e_luz(sc):
    for o in list(sc.objects):
        o.animation_data_clear()
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)


# ------------------------------------------------------------------ lança-foguetes
_LF = {}


def foguetes_montar(sc):
    g = _g()
    _sem_animacao_e_luz(sc)
    _tirar(sc, 'casca_anterior', 'casca_chao', 'selo_anterior', 'selo_chao', 'cratera', 'foguete_esteira')
    giro = bpy.data.objects['giro']
    casulo = bpy.data.objects['casulo']
    # no jogo a coroa gira e o pinhão do motor ficaria parado: os dentes dele cruzam os da coroa, a mesa (encostam) e
    # as aletas do motor (já no estudo). Sai o pinhão; fica o eixo saindo do redutor, na borda da coroa
    _tirar(sc, 'pinhao_dentes')
    giro.rotation_euler = (0, 0, PI / 2)              # posição de carga: casulo para +Y (frente do jogo)
    casulo.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    mc = casulo.matrix_world
    _LF['giro'] = giro.matrix_world.translation.copy()
    _LF['canhao'] = mc.translation.copy()
    _LF['boca'] = mc @ Vector((0.43, 0.0, 0.0))
    _LF['ejecao'] = mc @ Vector((-0.42, 0.0, 0.0))
    p = CONFIG['torre_foguetes']['partes']
    p['giro']['pivo'] = tuple(round(x, 4) for x in _LF['giro'])
    p['luzg']['pivo'] = p['giro']['pivo']
    p['canhao']['pivo'] = tuple(round(x, 4) for x in _LF['canhao'])
    p['luzc']['pivo'] = p['canhao']['pivo']
    _marcar(casulo, 'PCAN__', 'PCLUZ__', g)
    _marcar(giro, 'PGIRO__', 'PGLUZ__', g, pular=(casulo,))
    _limite_brilho(g, 120)


def foguetes_exportar(sc, raiz, dados):
    dados['boca'] = _r3(_LF['boca'])
    dados['ejecao'] = _r3(_LF['ejecao'])
    dados['vel_ejecao'] = [-1.6, 0.25, 0.9]                  # (frente, esquerda, cima) m/s: o selo sai para trás
    dados['capsula'] = {'escala': 2.6, 'fumaca': 3.0}        # selo maior que a cápsula de bala; jato com mais fumaça
    dados['descricao'] = ('Lança-foguetes 3×3: plataforma octogonal com quatro estabilizadores hidráulicos, unidade '
                          'hidráulica, armário de força, defletor de jato, paiol com boca ao sul (S1, foguetes por '
                          'esteira ou braço) e braço carregador. Giro com coroa dentada, pistões de elevação e radar; '
                          'casulo de 9 tubos com tampas. Partes: base, giro (gira em Z), canhao (casulo, filho do '
                          'giro), luzg/luzc. Pontos (Blender, giro 0): boca (frente dos tubos) e ejecao (traseira do '
                          'casulo, por onde sai o selo de cada disparo).')


# ------------------------------------------------------------------ muros e mina (estudo_muros_mina.py)
def _funcao_muros(nome):
    import gc
    for f in gc.get_objects():
        if callable(f) and getattr(f, '__name__', '') == nome and getattr(getattr(f, '__code__', None), 'co_filename', '').endswith('estudo_muros_mina.py'):
            return f
    raise RuntimeError('função do estudo não achada: ' + nome)


def _refazer(sc, fazer):
    """Cena com os três muros e a mina na mesma origem: apaga tudo e refaz só a peça (geometria; sem animação)."""
    for o in _vivos(sc):
        if o.type in ('MESH', 'EMPTY', 'LIGHT'):
            _apagar(o)
    fazer()
    _sem_animacao_e_luz(sc)
    _tirar(sc, 'arco', 'faisca', 'projetil', 'torrao', 'poeira', '_campo')
    g = _g()
    for o in _vivos(sc):
        if o.type == 'MESH' and any(g['vidro'](s.material) or g['tem_volume'](s.material) or g['mancha_suave'](s.material)
                                    for s in o.material_slots):
            _apagar(o)
    return g


def mina_montar(sc):
    g = _g()
    _de._so_colecao(sc, 'mina')
    _sem_animacao_e_luz(sc)
    _tirar(sc, 'arco', 'faisca', 'projetil', 'torrao', 'poeira', 'onda', 'clarao', 'fumaca')
    _eb._recortar(sc, -0.5, 0.5, -0.5, 0.5, -0.03, 0.0)     # monte de terra e capim dentro do tile; o chão cobre o resto
    _limite_brilho(g, 60)


def muro_liga_montar(sc):
    _limite_brilho(_refazer(sc, lambda: _funcao_muros('liga_centro')('mliga_c', 0.0, 0.0, (), 400)), 60)


def muro_liga_lado_montar(sc):
    g = _refazer(sc, lambda: _funcao_muros('liga_lado')('mliga_l', 0.0, 0.0, 0, 431))
    _eb._recortar(sc, -0.5, 0.5, -0.5, 0.5, -0.03, 0.0)
    _limite_brilho(g, 60)


BOBINAS_CAMPO = ((0.40, 0.66), (0.76, 1.02), (1.12, 1.36))      # do estudo (carretéis da coluna)


def muro_escudo_montar(sc):
    """O fio esmaltado das três bobinas (hélices, 24 mil triângulos) a redução não desmancha: na malha baixa ele vira
    um cilindro por bobina no raio de fora do enrolamento (a cor do fio vem do assado do alto)."""
    g = _refazer(sc, lambda: _funcao_muros('campo_centro')('mcampo_c', 0.0, 0.0, (), 500))
    _limite_brilho(g, 80)
    orig = g['reduzir']

    def reduzir(o, alvo):
        if o.name == 'muro_escudo_corpo':
            mats = [(s.material.name if s.material else '') for s in o.material_slots]
            idx = next((i for i, n in enumerate(mats) if n.startswith('Fio esmaltado')), -1)
            if idx >= 0:
                bm = bmesh.new()
                bm.from_mesh(o.data)
                bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == idx], context='FACES')
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
                antes = set(bm.faces)
                inv = o.matrix_world.inverted()
                for z0, z1 in BOBINAS_CAMPO:
                    bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=0.0957, radius2=0.0957,
                                          depth=(z1 - z0) - 0.038, matrix=inv @ Matrix.Translation((0, 0, (z0 + z1) / 2)))
                for f in bm.faces:
                    if f not in antes:
                        f.material_index = idx
                bm.to_mesh(o.data)
                bm.free()
                o.data.update()
        orig(o, alvo)
    g['reduzir'] = reduzir


def muro_escudo_lado_montar(sc):
    g = _refazer(sc, lambda: _funcao_muros('campo_lado')('mcampo_l', 0.0, 0.0, 0, 531))
    _eb._recortar(sc, -0.5, 0.5, -0.5, 0.5, -0.03, 0.0)     # nada passa da borda (o pano do vizinho começa ali)
    _limite_brilho(g, 60)


def muro_escudo_lado_exportar(sc, raiz, dados):
    dados['campo'] = {'y0': 0.272, 'y1': 0.5, 'z0': 0.11, 'z1': 1.32}     # onde o jogo desenha a parede (Blender)


# ------------------------------------------------------------------ gerador de escudo
def escudo_montar(sc):
    g = _g()
    for o in list(sc.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    _tirar(sc, 'bolha', 'fio_luz', 'feixe', 'cuspe', 'projetil', 'respingo', 'impacto', 'arco', 'faisca', 'fumaca',
           'blocos_', 'pedras')
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)
    _limite_brilho(g, 120)


def escudo_exportar(sc, raiz, dados):
    dados['descricao'] = ('Gerador de escudo 2×2: base blindada octogonal (chapas aparafusadas, uma em zarcão), rede pelo '
                          'eletroduto sul → transformador → eletrocalha → banco de capacitores (um estufado) → base; '
                          'radiador com ventoinhas ao norte, central hidráulica a leste com quatro pistões que inclinam os '
                          'emissores; coluna-bobina com a taça e o cristal da IA no cardã de três anéis. Sem portas (só '
                          'energia). A bolha o jogo desenha. Animação "trabalho" enquanto tem carga.')


def _cortar(objs, x0, x1, y0, y1, z0):
    """Corta as malhas `objs` na caixa (mundo): o que passa dos lados ou fica abaixo de z0 sai."""
    for o in objs:
        if o.type != 'MESH' or bpy.data.objects.get(o.name) is None:
            continue
        if o.data.users > 1:
            o.data = o.data.copy()
        mw = o.matrix_world.copy()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(mw)
        for co, no in (((x1, 0, 0), (1, 0, 0)), ((x0, 0, 0), (-1, 0, 0)), ((0, y1, 0), (0, 1, 0)),
                       ((0, y0, 0), (0, -1, 0)), ((0, 0, z0), (0, 0, -1))):
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(co),
                                   plane_no=Vector(no), clear_outer=True)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        if not bm.faces:
            bm.free()
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        bm.transform(mw.inverted())
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()


# ------------------------------------------------------------------ artilharia
_AR = {}
Q_ARTILHARIA = 50


def artilharia_montar(sc):
    g = _g()
    sc.frame_set(Q_ARTILHARIA)                        # carregada e elevada a 55°, antes do tiro
    for o in list(sc.objects):
        if o.type == 'MESH' and o.hide_render:        # o que só aparece em outros quadros (efeitos, estojo no ar)
            bpy.data.objects.remove(o, do_unlink=True)
    _sem_animacao_e_luz(sc)
    _tirar(sc, 'estojo_chao', 'estojo_laco', 'estojo_ejetado', 'granada_entrando', 'pinhao_dentes', 'pinhao_eixo', 'jato_freio',
           'clarao', 'fumaca', 'fiapo', 'faisca', 'pedrinha', 'poeira', 'onda')
    giro = bpy.data.objects['giro']
    canhao = bpy.data.objects['canhao']
    cano = bpy.data.objects['cano']
    giro.rotation_euler = (0, 0, PI / 2)              # cano do estudo em +X → +Y (frente do jogo)
    bpy.context.view_layer.update()
    # só o cano passa da área: o resto (sujeira no chão, patolas, mangueiras) é cortado na borda 3×3
    no_giro = {giro} | set(_de._descendentes(giro))
    _cortar([o for o in sc.objects if o not in no_giro], -1.5, 1.5, -1.5, 1.5, -0.03)
    _cortar([o for o in _de._descendentes(giro) if o not in set(_de._descendentes(canhao))], -1.5, 1.5, -1.5, 1.5, -0.03)
    mc = cano.matrix_world
    _AR['giro'] = giro.matrix_world.translation.copy()
    _AR['canhao'] = canhao.matrix_world.translation.copy()
    _AR['boca'] = mc @ Vector((3.66, 0.0, 0.0))
    _AR['ejecao'] = mc @ Vector((-0.52, -0.1, -0.06))
    p = CONFIG['artilharia']['partes']
    for k in ('giro', 'canhao'):
        p[k]['pivo'] = tuple(round(x, 4) for x in _AR[k])
    p['luzg']['pivo'] = p['giro']['pivo']
    p['luzc']['pivo'] = p['canhao']['pivo']
    _marcar(canhao, 'PCAN__', 'PCLUZ__', g)
    _marcar(giro, 'PGIRO__', 'PGLUZ__', g, pular=(canhao,))
    _limite_brilho(g, 120)


def artilharia_exportar(sc, raiz, dados):
    dados['boca'] = _r3(_AR['boca'])
    dados['ejecao'] = _r3(_AR['ejecao'])
    dados['vel_ejecao'] = [-0.7, -0.6, 0.4]                  # o estojo sai para trás, pela calha (lado direito)
    dados['capsula'] = {'escala': 3.2, 'fumaca': 4.0}        # estojo grande fumegando
    dados['descricao'] = ('Artilharia 3×3: laje com patolas hidráulicas e sapatas cravadas, pedestal octogonal, paiol '
                          'de recebimento ao sul (S1, granadas por esteira ou braço). Giro sobre coroa dentada: paiol '
                          'blindado, carregador com bandeja e soquete, unidade hidráulica, telêmetro com olho violeta e '
                          'radar. Obus elevado a 55°: berço com cilindros de recuo, cano longo com evacuador e freio de '
                          'boca, culatra de cunha. Partes: base, giro (gira em Z), canhao (filho do giro), luzg/luzc. '
                          'Pontos (Blender, giro 0): boca (freio de boca) e ejecao (calha do estojo).')


# ------------------------------------------------------------------ entradas
_ESCUDO = dict(script='estudo_gerador_escudo.py', cat='defesa', tris=9000, tex=1024, tirar=['estencil_fundo'],
               depois_de_montar=escudo_montar, antes_de_exportar=escudo_exportar)
_MUROS = dict(script='estudo_muros_mina.py', cat='defesa', tex=512, anima=False, tirar=[])
CONFIG = {
    'artilharia': dict(
        script='estudo_artilharia.py', cat='defesa', tris=8000, tex=1024, corpo='base', anima=False, tirar=[],
        margem=2.4, depois_de_montar=artilharia_montar, antes_de_exportar=artilharia_exportar,
        partes={
            'giro': dict(objetos=['PGIRO__'], pivo=(0.0, 0.0, 0.6), pai='base', tris=2200),
            'luzg': dict(objetos=['PGLUZ__'], pivo=(0.0, 0.0, 0.6), pai='giro', tris=160),
            'canhao': dict(objetos=['PCAN__'], pivo=(0.0, 0.0, 1.55), pai='giro', tris=1600),
            'luzc': dict(objetos=['PCLUZ__'], pivo=(0.0, 0.0, 1.55), pai='canhao', tris=80),
        }),
    'gerador_escudo': _ESCUDO,
    'mina_pulso': dict(script='estudo_muros_mina.py', cat='defesa', tris=1400, tex=512, anima=False,
                       tirar=['chao_queimado', 'capim_deitado'], depois_de_montar=mina_montar),
    'muro_liga': dict(_MUROS, tris=900, depois_de_montar=muro_liga_montar),
    'muro_liga_lado': dict(_MUROS, tris=500, depois_de_montar=muro_liga_lado_montar),
    'muro_escudo': dict(_MUROS, tris=1400, depois_de_montar=muro_escudo_montar),
    'muro_escudo_lado': dict(_MUROS, tris=400, depois_de_montar=muro_escudo_lado_montar, antes_de_exportar=muro_escudo_lado_exportar),
    'torre_foguetes': dict(
        script='estudo_lanca_foguetes.py', cat='defesa', tris=7400, tex=1024, corpo='base', anima=False,
        tirar=['foguete_voo', 'foguete_carga', 'selo_ejetado', 'selo_carga', 'casca_ejetada', 'fiapo'],
        depois_de_montar=foguetes_montar, antes_de_exportar=foguetes_exportar,
        partes={
            'giro': dict(objetos=['PGIRO__'], pivo=(0.0, 0.0, 0.5), pai='base', tris=1500),
            'luzg': dict(objetos=['PGLUZ__'], pivo=(0.0, 0.0, 0.5), pai='giro', tris=160),
            'canhao': dict(objetos=['PCAN__'], pivo=(0.0, 0.0, 1.08), pai='giro', tris=1500),
            'luzc': dict(objetos=['PCLUZ__'], pivo=(0.0, 0.0, 1.08), pai='canhao', tris=80),
        }),
}
