"""Entradas do para_jogo.py para a ÁGUA (fase 2.3 do docs/PLANO_INTEGRACAO.md).

Bomba d'água (bomba_agua, 2×2) ← estudo_bomba_agua.py: estação de captação na margem — laje com o poço de sucção,
  cais, pilares, grade de barras da tomada (com o lixo preso), vigas I, bomba vertical com o visor em espiral e os
  anéis de campo, motor, recalque com válvula de retenção até a flange da borda norte (FLUIDO_SAI_N1, eixo a 0,35 m).
  A tomada fica ao SUL: o cais e a grade avançam 0,45 m sobre o tile de água vizinho (o jogo exige água encostada no
  lado sul, MapaOcupacao "tomada_agua"). Saem a margem, o rio, as pedras do enrocamento, juncos, escuma, folhas e
  galhos que boiam, as gotas e as ondas; o que fica abaixo de −0,9 m (fundo do poço) é cortado.
Coletor de chuva (coletor_chuva, 2×2) ← estudo_coletor_chuva.py no estado 'chuva' (pétalas abertas em cálice; a
  animação do estado — luzes, anemômetro, pingos — toca enquanto chove). A saída do estudo vinha a 0,56 m; aqui o
  recalque desce num pescoço de ganso até 0,35 m (altura dos canos do jogo) antes da flange da borda sul
  (FLUIDO_SAI_S1). Sai a chuva, as poças, o chão, o barro rachado (estado seco) e as gotas.
Condensador de neblina (condensador_neblina, 2×2) ← estudo_condensador_neblina.py: telas, plenum com serpentina,
  ventiladores, compressor, radiador, tanque e bomba. Saída FLUIDO_SAI_S0 a 0,28 m (do estudo; os canos do jogo
  ficam a 0,35 m — ver pendências no PLANO_INTEGRACAO). Saem a névoa em volume, as gotas, as poças e o chão.
Supressor de incêndio (supressor_fogo, 1×1) ← estudo_supressor_fogo.py: laje, pedestal, válvula de dilúvio,
  reservatório, torre giratória com o canhão monitor e o mastro de sensores (a torre e o canhão varrem com a
  animação do estudo enquanto borrifa). O cano do estudo chegava pelo oeste, 0,30 m fora do eixo e a 0,24 m de altura;
  no jogo os canos são centrados no tile a 0,35 m, então entra um ramal novo pelo LESTE, no eixo do tile e na altura
  dos canos (flange na borda, válvula de retenção, boca no pedestal entre as nervuras): FLUIDO_ENT_L0. A boca oeste
  fica fechada (o recorte no tile deixa a flange interna como flange cega). Saem o fogo, a fumaça, o jato, o vapor,
  a vegetação queimando, o chão e o cano de fora com as selas.
Filtro de água (filtro_agua, reconvertido) ← estudo_filtro_agua.py com um ramal novo de água limpa: um tê no coletor
  de cima desce pela borda norte até a flange do jogo (FLUIDO_SAI_N1, 0,35 m), com pé de apoio no trecho de baixo. Com a pesquisa
  "Filtro que devolve água" o filtro solta água limpa por ali (a saída que jorra no rio continua: é a sobra).
Rodar: blender -b --python para_jogo.py -- <nome>"""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_esteiras_bracos', os.path.join(AQUI, 'conv_esteiras_bracos.py'))
_eb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eb)

CENARIO_RIO = ('margem', 'rio', 'enrocamento', 'juncos', 'pedras', 'galhos_rio', 'escuma_rio', 'espuma_suja',
               'folha_rio', 'onda', 'gota')


def _sem_rio(sc):
    import bpy
    for o in [o for o in sc.objects if o.name.split('.')[0] in CENARIO_RIO]:
        bpy.data.objects.remove(o, do_unlink=True)
    _eb._recortar(sc, -1.0, 1.0, -1.45, 1.0, -0.9, 0.0)


# ------------------------------------------------------------------ estudos montados com remendo (sem foto)
def _executar(estudo, trocas, depois=None):
    """Roda o estudo (modo 'nada') com trechos do código trocados; `depois(g)` recebe os globais do estudo."""
    caminho = os.path.join(AQUI, estudo)
    cod = open(caminho, encoding='utf-8').read()
    for velho, novo in trocas:
        assert velho in cod, 'trecho não achado em %s: %s' % (estudo, velho[:60])
        cod = cod.replace(velho, novo, 1)
    sys.argv = [sys.argv[0], '--python', caminho, '--', 'nada']
    sys.path.insert(0, AQUI)
    g = {'__name__': '__main__', '__file__': caminho}
    exec(compile(cod, caminho, 'exec'), g)
    if depois:
        depois(g)
    return g


# coletor: o recalque desce a 0,35 m antes da borda (pescoço de ganso), a flange e o pé acompanham
TROCAS_COLETOR = [
    ("Z_SAIDA = 0.56\n", "Z_SAIDA = 0.56\nZ_PORTA = 0.35                 # eixo dos canos do jogo (fase 2.3)\n"),
    ("""cano(bm, bf, bp, [Vector((P_BOMBA.x, P_BOMBA.y - 0.1, P_BOMBA.z + 0.1)), Vector((P_BOMBA.x, P_BOMBA.y - 0.1, Z_SAIDA)),
                  Vector((X_SAIDA, P_BOMBA.y - 0.1, Z_SAIDA)), Vector((X_SAIDA, -0.985, Z_SAIDA))], 0.045)
flange(bf, bp, Vector((X_SAIDA, -0.975, Z_SAIDA)), Y, 0.085, 0.024, 10)""",
     """cano(bm, bf, bp, [Vector((P_BOMBA.x, P_BOMBA.y - 0.1, P_BOMBA.z + 0.1)), Vector((P_BOMBA.x, P_BOMBA.y - 0.1, Z_SAIDA)),
                  Vector((X_SAIDA, P_BOMBA.y - 0.1, Z_SAIDA)), Vector((X_SAIDA, -0.79, Z_SAIDA)),
                  Vector((X_SAIDA, -0.79, Z_PORTA)), Vector((X_SAIDA, -0.985, Z_PORTA))], 0.045)
flange(bf, bp, Vector((X_SAIDA, -0.975, Z_PORTA)), Y, 0.085, 0.024, 10)"""),
    ("caixa_de(bm, (X_SAIDA - 0.03, -0.9, 0.08), (X_SAIDA + 0.03, -0.86, Z_SAIDA - 0.045))",
     "caixa_de(bm, (X_SAIDA - 0.03, -0.9, 0.08), (X_SAIDA + 0.03, -0.86, Z_PORTA - 0.045))"),
]


def _coletor_chuva(g):
    g['estado']('chuva')
    g['animar']('chuva')


# supressor: ramal novo pelo leste, no eixo do tile e na altura dos canos do jogo
KIT_SUPRESSOR = '''
# ---- fase 2.3 (conv_agua.py): entrada do jogo pelo LESTE, no eixo do tile, a 0,35 m (canos do jogo)
ZJ = 0.35
for _a, _b in (((0.477, 0.0, ZJ), (0.375, 0.0, ZJ)), ((0.265, 0.0, ZJ), (0.146, 0.0, ZJ))):
    tubo(B('kit_cano', 'vermelho', True), Vector(_a), Vector(_b), R_LINHA, 24)
flange(Vector((0.488, 0.0, ZJ)), X, 0.085, 0.022, 8, mat='vermelho')       # flange da porta (borda leste)
flange(Vector((0.135, 0.0, ZJ)), X, 0.06, 0.016, 6)                         # boca leste do pedestal
for _x in (0.371, 0.269):                                                  # flanges da válvula de retenção
    flange(Vector((_x, 0.0, ZJ)), X, 0.07, 0.016, 6)
cil(B('kit_valvula', 'grafite', True), Vector((0.32, 0.0, ZJ)), 0.062, 0.09, X, lados=24)   # corpo da retenção
caixa(B('kit_valvula_tampa', 'ferro'), Vector((0.32, 0.0, ZJ + 0.07)), (0.07, 0.07, 0.03))   # tampa aparafusada
for _dx in (-0.025, 0.025):
    for _dy in (-0.025, 0.025):
        parafuso(Vector((0.32 + _dx, _dy, ZJ + 0.086)), Z)
caixa(B('kit_seta', 'amarelo'), Vector((0.32, -0.063, ZJ)), (0.05, 0.004, 0.012))          # seta do fluxo (estêncil)
caixa_de(B('kit_sela', 'ferro'), (0.405, -0.04, Z_LAJE), (0.445, 0.04, ZJ - R_LINHA))      # sela no chão
toro(B('kit_sela', 'ferro'), Vector((0.425, 0.0, ZJ)), R_LINHA + 0.006, 0.006, X, 24, 6)
escorrido(Vector((0.32, -0.062, ZJ - 0.03)), -Y, 0.06, w=0.008)
escorrido(Vector((0.488, 0.06, ZJ - 0.05)), X, 0.05, w=0.007)
'''
MARCA_SUPRESSOR = "flange(Vector((0.0, -0.135, Z_LINHA)), Y, 0.08, 0.02, 8)                  # boca do pedestal\n"


KIT_FILTRO = '''
# ---- fase 2.3 (conv_agua.py): ramal de água limpa para a rede de canos do jogo (borda norte, tile leste, 0,35 m)
bm, bf, bp, bpe = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
cano(bm, bf, bp, [(0.5, Y_COL, Z_COLET), (0.5, 0.72, Z_COLET), (0.4, 0.72, Z_COLET), (0.4, 0.72, 0.35), (0.4, 0.86, 0.35),
                  (0.5, 0.86, 0.35), (0.5, 0.985, 0.35)], 0.045, fl_pontas=False)
esfera(bm, Vector((0.5, Y_COL, Z_COLET)), R_COL_C + 0.01)                  # tê no coletor
flange(bf, bp, Vector((0.5, 0.975, 0.35)), Y, 0.085, 0.024, 10)            # flange da porta (borda norte)
caixa_de(bpe, (0.375, 0.765, 0.08), (0.425, 0.815, 0.35 - 0.045))         # pé do trecho de baixo
caixa_de(bpe, (0.355, 0.75, 0.08), (0.445, 0.83, 0.095))
suavizar(obj('kit_ramal', bm, 'cano'))
obj('kit_ramal_flanges', bf, 'ferro')
obj('kit_ramal_paraf', bp, 'aco')
obj('kit_ramal_pe', bpe, 'amarelo')
'''
MARCA_FILTRO = "obj('coletor_parafusos', bp, 'aco')\n"


def _recorte_supressor(sc):
    _eb._recortar(sc, -0.5, 0.5, -0.5, 0.5, -0.03, 0.0)


def _recorte_coletor(sc):
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)


def _recorte_condensador(sc):
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)


CONFIG = {
    'bomba_agua': dict(script='estudo_bomba_agua.py', args=['nada'], cat='logistica/canos', tris=10000, tex=1024,
                       margem=0.5, tirar=['folha_rio', 'onda', 'poca', 'bracos_espuma', 'giro_espuma', 'giro_folha', 'agua_poco'], depois_de_montar=_sem_rio),
    'coletor_chuva': dict(script='conv_agua.py', args=['coletor_chuva'], estudo='estudo_coletor_chuva.py', cat='logistica/canos', tris=10000, tex=1024,
                          tirar=['poca', 'barro_rachado', 'respingo', 'pingo', 'capim', 'pedras', 'anel_campo'], depois_de_montar=_recorte_coletor),
    'condensador_neblina': dict(script='estudo_condensador_neblina.py', args=['nada'], cat='logistica/canos', tris=10000,
                                tex=1024, tirar=['poca', 'pingo', 'respingo', 'bolha'], depois_de_montar=_recorte_condensador),
    'filtro_agua': dict(script='conv_agua.py', args=['filtro_agua'], estudo='estudo_filtro_agua.py', cat='maquinas', tris=8000, tex=1024, tirar=[]),
    'supressor_fogo': dict(script='conv_agua.py', args=['supressor_fogo'], estudo='estudo_supressor_fogo.py', cat='maquinas', tris=6000, tex=1024,
                           tirar=['vegetacao', 'arbusto', 'capim', 'brasa', 'cinza', 'galho', 'graveto', 'folhas', 'selas', 'pedras', 'poca', 'respingo'],
                           depois_de_montar=_recorte_supressor),
}


if __name__ == '__main__':
    _peca = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''
    if _peca == 'coletor_chuva':
        _executar('estudo_coletor_chuva.py', TROCAS_COLETOR, _coletor_chuva)
    elif _peca == 'filtro_agua':
        _executar('estudo_filtro_agua.py', [(MARCA_FILTRO, MARCA_FILTRO + KIT_FILTRO)])
    elif _peca == 'supressor_fogo':
        _executar('estudo_supressor_fogo.py', [(MARCA_SUPRESSOR, MARCA_SUPRESSOR + KIT_SUPRESSOR)])
