"""Entradas do para_jogo.py para o CLIMA (fase 2.5 do docs/PLANO_INTEGRACAO.md).

Para-raios (para_raios, 1×1) e para-raios de cristal (para_raios_2, 1×1) ← estudo_para_raios.py, coleções 'pr' e 'pc'
  (a coleção 'raio' — os dois juntos com o relâmpago — sai). Laje, mastro em gomos, estais, captor no topo, descida
  de cobre, caixa com centelhador, capacitores. Saem os arcos, faíscas, plasma, a descida acesa e a figura de
  Lichtenberg acesa (efeitos do raio: o jogo desenha o seu); o que passa do tile (brita, Lichtenberg queimado no chão,
  terra queimada) é recortado na borda. Ponto para o jogo: ponta_raio (topo do captor: onde o raio do jogo bate).
Captador de carga (captador_carga, 2×2) ← estudo_captador_carga.py: câmara octogonal com o banho e o carrossel, pórtico
  dos eletrodos, banco de capacitores, mastro treliçado com a coroa de pontas e o cristal-guia. Saem as bolhas e o
  vapor do banho, os pulsos do cabo, arcos e estalos, os cristais que andam nas esteiras de fora (entrando e saindo;
  o jogo leva os itens) e o que passa da área. Os "raios" do carrossel (aros) e da placa de alta tensão são peças:
  trocam de nome antes da limpeza (o para_jogo tira tudo que tem "raio" no nome). Portas do estudo: ITEM_ENT_S1,
  ITEM_SAI_O0, FLUIDO_ENT_N0 (0,275 m). Ponto: ponta_raio (ponta captora no alto do mastro, canto nordeste).
Semeador de nuvens (semeador_nuvens, 2×2) e defletor de vento (defletor_vento, 2×2) ← estudo_clima_2x2.py (sem portas).
  Semeador: saem a nuvem, a chuva, a cortina, os rastros, estouros, projéteis e estojos no ar, a chama e a pluma dos
  queimadores, os respingos, o capim e as pedras; os estojos velhos do chão ficam (os de fora da área são cortados).
  Defletor: a cabeça giratória (giro) vira 66° — 22 dentes da coroa, assim os pinhões fixos seguem engrenados —
  para o vento sair para +Y do Blender (a frente do jogo): no jogo o vento do raio de 40 m sopra para onde a peça
  aponta (o jogador gira com R). Saem as folhas voando, as linhas de fluxo, a poeira, o capim e as pedras; os feixes de
  cabo do armário aos motores, que no estudo atravessavam a coroa e a borda da plataforma que gira, perdem o trecho de
  dentro (somem por baixo da coroa). Conferido por BVH: nada que gira cruza peça fixa (fora o rolamento, face com face).
Cúpula contra raios (cupula_raios, 3×3) e regulador climático (regulador_clima, 3×3) ← estudo_clima_3x3.py.
  Cúpula: sai a cúpula de campo de 30 m (o jogo desenha a sua, shader campo_escudo), o céu, a chuva, os raios, os
  blocos de fábrica de fora, as pedras e as poças. O guarda-chuva (varetas, pontas, rede) abria 2,25 m do centro:
  acima de 4 m tudo é apertado para dentro (fator suave até 0,64 a 5,1 m) e fica na área 3×3; hastes de terra,
  caixas de inspeção e a cordoalha que iam até 2,8 m são recortadas na borda. Ponto: ponta_raio (cristal do topo).
  Regulador: as antenas parabólicas e os canhões de calor passavam da área (até 2 m do centro): a máquina inteira
  (menos a laje) fica a 0,75 do tamanho, em volta do centro do topo da laje. Os pratos das antenas cruzavam os
  braços-garra no estudo: ficam a 0,72 em volta do pivô de azimute. Saem o vapor, as frentes de onda, o ar
  quente, o céu com o furo, a cortina de chuva, os raios de fora, os blocos e as pedras; os canos e as torres "de
  vapor" são peças e trocam de nome antes da limpeza.
Rodar: blender -b --python para_jogo.py -- <nome>"""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_esteiras_bracos', os.path.join(AQUI, 'conv_esteiras_bracos.py'))
_eb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eb)
_spec = _iu.spec_from_file_location('conv_defesa_energia', os.path.join(AQUI, 'conv_defesa_energia.py'))
_de = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_de)

_PONTA = {}


def _r3(v):
    return [round(float(x), 4) for x in v]


def _renomear(trocas):
    """Peças cujo nome tem palavra de efeito (raio, vapor): o para_jogo as tiraria na limpeza."""
    import bpy
    for o in list(bpy.data.objects):
        for velho, novo in trocas:
            if velho in o.name:
                o.name = o.name.replace(velho, novo)


def _executar(estudo, args, trocas, depois=None):
    caminho = os.path.join(AQUI, estudo)
    sys.argv = [sys.argv[0], '--python', caminho, '--'] + list(args)
    sys.path.insert(0, AQUI)
    g = {'__name__': '__main__', '__file__': caminho}
    exec(compile(open(caminho, encoding='utf-8').read(), caminho, 'exec'), g)
    _renomear(trocas)
    if depois:
        depois(g)
    return g


def _animar_semeador(g):
    """No modo 'nada' o estudo só monta: o laço (carrossel, culatra, bobinas) é feito no estado 'chuva' (trabalhando)."""
    g['estado_semeador']('chuva', g['EF'])
    g['animar_semeador']('chuva', g['EF'])


def _animar_defletor(g):
    g['estado_defletor']()
    g['animar_defletor'](g['EF'])


def _topo(objs):
    """Ponto mais alto (mundo) das malhas `objs`, no meio delas em x, y."""
    from mathutils import Vector
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    if not pts:
        return None
    z = max(p.z for p in pts)
    return Vector(((min(p.x for p in pts) + max(p.x for p in pts)) / 2, (min(p.y for p in pts) + max(p.y for p in pts)) / 2, z))


def _exportar_ponta(nome):
    def f(sc, raiz, dados):
        if nome in _PONTA:
            dados['ponta_raio'] = _r3(_PONTA[nome])
    return f


# ------------------------------------------------------------------ para-raios
def _para_raios(colecao, nome):
    def f(sc):
        g = _de._g()
        _de._so_colecao(sc, colecao)
        _de._tirar(sc, 'arco', 'fsc_', 'plasma', 'descida_brilho', 'lich_brilho', 'corona')
        _eb._recortar(sc, -0.5, 0.5, -0.5, 0.5, -0.03, 0.0)
        p = _topo([o for o in sc.objects if o.type == 'MESH'])
        _PONTA[nome] = (0.0, 0.0, p.z) if p is not None else (0.0, 0.0, 3.0)
        _de._limite_brilho(g, 80)
    return f


# ------------------------------------------------------------------ captador
def _captador(sc):
    import bpy
    g = _de._g()
    _de._tirar(sc, 'bolha', 'vapor', 'pulso', 'arco_', 'estalo', 'faisca', 'cristal_entra', 'cristal_sai')
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)
    pc = bpy.data.objects.get('ponta_captora')
    p = _topo([pc]) if pc else None
    _PONTA['captador_carga'] = tuple(p) if p is not None else (0.75, 0.75, 3.6)
    _de._limite_brilho(g, 120)


# ------------------------------------------------------------------ semeador e defletor
def _semeador(sc):
    g = _de._g()
    _de._tirar(sc, 'estojo_tiro', 'projetil', 'estouro', 'ultima', 'fiapo', 'pluma', 'particula', 'respingo', 'cortina',
               'nuvem', 'capim', 'pedras')
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)
    _de._limite_brilho(g, 120)


def _cabos_fora_da_coroa(sc):
    """No estudo os feixes de cabo do armário até os motores atravessam a coroa dentada e a borda da plataforma que
    gira (r < 0,66 m, z 0,235–0,38): o trecho de dentro sai (o cabo some por baixo da coroa, como se entrasse na base)."""
    import bpy, bmesh
    for o in [o for o in sc.objects if o.type == 'MESH' and o.name.split('.')[0] in ('cabos_borracha', 'cabos_cabo_verm', 'abracadeiras')]:
        if o.data.users > 1:
            o.data = o.data.copy()
        mw = o.matrix_world
        bm = bmesh.new()
        bm.from_mesh(o.data)
        fora = [v for v in bm.verts if (lambda p: p.xy.length < 0.665 and 0.235 < p.z < 0.385)(mw @ v.co)]
        if fora:
            bmesh.ops.delete(bm, geom=fora, context='VERTS')
            bm.to_mesh(o.data)
            o.data.update()
        bm.free()


GIRO_DEFLETOR = 66.0          # graus: 25° do estudo + 66° = 91° (22 dentes de 3°: os pinhões fixos seguem engrenados)


def _defletor(sc):
    import bpy
    g = _de._g()
    _de._tirar(sc, 'folha_voando', 'fluxo', 'capim', 'pedras')
    for o in sc.objects:                       # saco da biruta ondula por shape key: a redução não aceita (fica liso)
        if o.type == 'MESH' and o.data.shape_keys:
            o.shape_key_clear()
    giro = bpy.data.objects['giro']
    giro.rotation_euler.z += math.radians(GIRO_DEFLETOR)
    bpy.context.view_layer.update()
    _cabos_fora_da_coroa(sc)
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)
    _de._limite_brilho(g, 120)


# ------------------------------------------------------------------ cúpula e regulador
def _apertar_alto(sc, z0, z1, fator):
    """Vértices acima de z0 chegam ao centro (x, y × fator a partir de z1, suave entre os dois)."""
    import bpy, bmesh
    for o in [o for o in sc.objects if o.type == 'MESH']:
        if o.data.users > 1:
            o.data = o.data.copy()
        mw = o.matrix_world.copy()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(mw)
        mexeu = False
        for v in bm.verts:
            if v.co.z > z0:
                t = min(1.0, (v.co.z - z0) / (z1 - z0))
                s = 1.0 + (fator - 1.0) * (t * t * (3 - 2 * t))
                v.co.x *= s
                v.co.y *= s
                mexeu = True
        if mexeu:
            bm.transform(mw.inverted())
            bm.to_mesh(o.data)
            o.data.update()
        bm.free()


def _cupula(sc):
    import bpy
    g = _de._g()
    _de._tirar(sc, 'cupula', 'blocos_', 'pedras', 'pocas', 'cortina', 'sinalizador')
    _apertar_alto(sc, 4.0, 5.1, 0.64)
    _eb._recortar(sc, -1.5, 1.5, -1.5, 1.5, -0.03, 0.0)
    cr = bpy.data.objects.get('cristal_corpo')
    p = _topo([cr]) if cr else None
    _PONTA['cupula_raios'] = tuple(p) if p is not None else (0.0, 0.0, 8.4)
    _de._limite_brilho(g, 160)


ESCALA_REGULADOR = 0.75
ESCALA_ANTENAS = 0.72


def _regulador(sc):
    import bpy
    from mathutils import Matrix
    g = _de._g()
    _de._tirar(sc, 'onda', 'ar_quente', 'blocos_', 'pedras', 'pocas', 'cortina', 'tampa_sombra', 'nuvem')
    # no estudo os pratos das antenas (Ø 1,3 m, mirando a 45°) cruzam os braços-garra: a 0,72 do tamanho, em volta do
    # pivô de azimute, passam livres (conferido por BVH nos quadros 1, 25, 49 e 73 da mira)
    for n in ('antena_0_azimute', 'antena_1_azimute'):
        if bpy.data.objects.get(n):
            bpy.data.objects[n].scale = (ESCALA_ANTENAS,) * 3
    laje = [o for o in sc.objects if o.name.startswith('laje')]
    zl = max((o.matrix_world @ v.co).z for o in laje for v in o.data.vertices) if laje else 0.1
    # um pai com a escala: a animação do estudo (anéis, antenas) segue valendo por baixo dele
    esc = bpy.data.objects.new('_escala', None)
    sc.collection.objects.link(esc)
    esc.matrix_world = Matrix.Translation((0, 0, zl)) @ Matrix.Scale(ESCALA_REGULADOR, 4) @ Matrix.Translation((0, 0, -zl))
    for o in [o for o in sc.objects if o.parent is None and o not in laje and o is not esc]:
        o.parent = esc
    bpy.context.view_layer.update()
    _eb._recortar(sc, -1.5, 1.5, -1.5, 1.5, -0.03, 0.0)
    _de._limite_brilho(g, 160)


TROCAS_CAPTADOR = [('carrossel_raios', 'carrossel_aros'), ('placa_at_raio', 'placa_at_simbolo')]
TROCAS_SEMEADOR = [('carrossel_raios', 'carrossel_aros')]
TROCAS_CUPULA = [('aneis_raios', 'aneis_aros')]
TROCAS_REGULADOR = [('torres_vapor', 'torres_coluna'), ('canos_vapor', 'canos_quente')]

_PR = dict(script='estudo_para_raios.py', args=['nada'], cat='clima', tex=512, tirar=[], anima=True)
CONFIG = {
    'para_raios': dict(_PR, tris=3200, depois_de_montar=_para_raios('pr', 'para_raios'),
                       antes_de_exportar=_exportar_ponta('para_raios')),
    'para_raios_2': dict(_PR, tris=4200, depois_de_montar=_para_raios('pc', 'para_raios_2'),
                         antes_de_exportar=_exportar_ponta('para_raios_2')),
    'captador_carga': dict(script='conv_clima.py', args=['captador_carga'], estudo='estudo_captador_carga.py', cat='clima',
                           tris=9000, tex=1024, tirar=['pedras', 'mastro_queimado'], depois_de_montar=_captador,
                           antes_de_exportar=_exportar_ponta('captador_carga')),
    'semeador_nuvens': dict(script='conv_clima.py', args=['semeador_nuvens'], estudo='estudo_clima_2x2.py', cat='clima',
                            tris=9000, tex=1024, tirar=[], depois_de_montar=_semeador),
    'defletor_vento': dict(script='conv_clima.py', args=['defletor_vento'], estudo='estudo_clima_2x2.py', cat='clima',
                           tris=8000, tex=1024, tirar=[], depois_de_montar=_defletor),
    'cupula_raios': dict(script='conv_clima.py', args=['cupula_raios'], estudo='estudo_clima_3x3.py', cat='clima',
                         tris=10000, tex=1024, tirar=[], depois_de_montar=_cupula,
                         antes_de_exportar=_exportar_ponta('cupula_raios')),
    'regulador_clima': dict(script='conv_clima.py', args=['regulador_clima'], estudo='estudo_clima_3x3.py', cat='clima',
                            tris=11000, tex=1024, tirar=[], depois_de_montar=_regulador),
}


if __name__ == '__main__':
    _peca = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''
    if _peca == 'captador_carga':
        _executar('estudo_captador_carga.py', ['nada'], TROCAS_CAPTADOR)
    elif _peca == 'semeador_nuvens':
        _executar('estudo_clima_2x2.py', ['nada', 'semeador'], TROCAS_SEMEADOR, _animar_semeador)
    elif _peca == 'defletor_vento':
        _executar('estudo_clima_2x2.py', ['nada', 'defletor'], [], _animar_defletor)
    elif _peca == 'cupula_raios':
        _executar('estudo_clima_3x3.py', ['nada', 'cupula'], TROCAS_CUPULA)
    elif _peca == 'regulador_clima':
        _executar('estudo_clima_3x3.py', ['nada', 'regulador'], TROCAS_REGULADOR)
