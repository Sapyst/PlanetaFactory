"""Entradas do para_jogo.py para o LOTE 16 (fases 3+4: trilhos, drones e lógica; docs/PLANO_INTEGRACAO.md).
Rodar: blender -b --python para_jogo.py -- <nome>

- sinal_cadeia ← estudo_sinal_cadeia.py (o sinal de bloco do estudo_trilhos.py com cabeça de cadeia, lidar da saída e
  módulo de cadeia). Mesmo método do sinal_trem (conv_trilhos.py): centro no tile (1,5; −1,5), recorte 1×1, mato e
  manchas fora; todas as luzes ficam acesas fixas (P_Sinal): o sinal não é máquina (P_Cristal só acende trabalhando).
- bomba_estacao ← estudo_bomba_estacao.py (bomba de lóbulos reversível com motor deitado, braço de carga com junta
  giratória e acoplador na borda sul, boca de cano no norte a 0,34 m). Já está no tile; o pingo e as manchas saem; fica a
  animação do estudo (ventoinha, ponteiro, setas, LEDs) tocando enquanto bombeia.
- trilho_energizado ← estudo_trilho_energizado.py (o reto do sul do estudo dos trilhos, y −1..0, com terceiro trilho,
  tampa, isoladores e eletroduto de alimentação). Mesmo método do trilho_reto (conv_trilhos.py: recorte no tile, via
  baixa feita à mão, uma malha só para o lote); o terceiro trilho e a alimentação (objetos "terceiro_*") entram como
  detalhe dizimado; a luz "energizado" fica acesa fixa (P_Sinal).
- locomotiva_eletrica ← estudo_locomotiva_eletrica.py (a locomotiva do estudo_trem sem o diesel, com resistores,
  buchas, sapatas coletoras e pintura elétrica). Mesmo método da locomotiva (conv_trilhos._trem): só o veículo, pose de
  repouso, partes truque0/truque1 (as sapatas vão junto com o truque delas).
- Lógica (categoria nova "logica"): sensor_esteira, sensor_tanque, comparador, valvula ← estudo_<nome>.py (base comum
  lote16_base.py: materiais e peças prontas do estudo_canos.py). Já estão no tile; saem o contexto (esteira e itens do
  sensor de esteira), pingos e manchas; fica a animação do estudo (bolha, balança, gaveta, tambor) tocando enquanto a
  peça trabalha.
- bau_estoque ← estudo_bau_estoque.py (o baú 1×1 do estudo_baus.py com plataforma de pouso, escotilha de teto e farol;
  verde-oliva). Mesmo método do baú (conv_logistica.py: só a coleção 'bau', nomes neutros na animação do estudo)."""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))
PI = math.pi
import importlib.util as _iu


def _modulo(nome):
    spec = _iu.spec_from_file_location(nome, os.path.join(AQUI, nome + '.py'))
    m = _iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_tr = _modulo('conv_trilhos')
_lg = _modulo('conv_logistica')


# ------------------------------------------------------------------ sinal em cadeia
def _sinal_cadeia_exportar(sc, raiz, dados):
    """Toda luz fria (verde, violeta) vira P_Sinal: acesa fixa no jogo."""
    import bpy
    for m in bpy.data.materials:
        if m.name.startswith('P_Cristal') and m.node_tree:
            m.name = 'P_Sinal'


def _energizado_exportar(sc, raiz, dados):
    _tr._uma_malha(sc, raiz, dados)
    _sinal_cadeia_exportar(sc, raiz, dados)


_loco = _tr._trem('locomotiva_eletrica', 3.0, 7600)
_loco.update(script='estudo_locomotiva_eletrica.py', tirar=['via_', 'trilho', 'pedra', 'lastro', 'terceiro'])

_LIMPA = ['gota', 'poca_pingo', 'halo', 'contexto']

CONFIG = {
    'bau_estoque': dict(script='estudo_bau_estoque.py', cat='logistica/armazenagem', tris=3600, tex=1024,
                        centro=(-1.0, -0.5, 0.0), tirar=['halo'], depois_de_montar=_lg._so_colecao('bau'),
                        antes_de_exportar=_lg._neutro),
    'sensor_esteira': dict(script='estudo_sensor_esteira.py', cat='logica', tris=3600, tex=1024, tirar=_LIMPA, margem=0.03),
    'sensor_tanque': dict(script='estudo_sensor_tanque.py', cat='logica', tris=3800, tex=1024, tirar=_LIMPA, margem=0.03),
    'comparador': dict(script='estudo_comparador.py', cat='logica', tris=4500, tex=1024, tirar=_LIMPA, margem=0.03),
    'valvula': dict(script='estudo_valvula.py', cat='logica', tris=4200, tex=1024, tirar=_LIMPA, margem=0.03),
    'locomotiva_eletrica': _loco,
    'trilho_energizado': dict(script='estudo_trilho_energizado.py', cat='transporte/trilhos', tris=2200, tex=1024,
                              centro=(0.5, -0.5, 0.0), anima=False, tirar=['faisca'],
                              depois_de_montar=_tr._via_montar('trilho_energizado', 1, 1, _tr._reto, 'terceiro', 1300),
                              antes_de_exportar=_energizado_exportar),
    'bomba_estacao': dict(script='estudo_bomba_estacao.py', cat='transporte/trilhos', tris=5000, tex=1024,
                          tirar=['gota', 'poca_pingo', 'halo', 'derrame', 'oleo'], margem=0.03),
    'sinal_cadeia': dict(script='estudo_sinal_cadeia.py', cat='transporte/trilhos', tris=2600, tex=1024,
                         centro=(1.5, -1.5, 0.0), anima=False, tirar=[], depois_de_montar=_tr._sinal_montar,
                         antes_de_exportar=_sinal_cadeia_exportar),
}


# ------------------------------------------------------------------ braço quântico (estudo_bracos_novos.py)
# A lança telescópica não serve ao IK de 2 elos do Animador: a lança fica de pé (o braço 1 parado, como no estudo) e
# o jogo estica as seções (lanca1..4 andam k × e; ponta 4e; cabo estica; carretel gira; os anéis do rastro aparecem
# quando a ponta passa) até a origem escolhida (alcance 1 a 3 tiles: e = (alcance − 1) / 4). Pose de repouso do
# estudo no quadro 1 (lança recolhida, ponta a 1 tile). Saem: a laje (tudo desce Z0), as esteiras e os itens de
# contexto, o campo translúcido (o jogo desenha o item voando pelo caminho do campo) e a luz da ponta.
ZQ0 = 0.05
EQ = 1.21 - ZQ0                         # cotovelo (pivô da lança) depois de descer a laje
ZCQ = EQ + 0.22                          # altura do fluxo por cima da lança
Q_ANEIS = [0.30 + 0.25 * i for i in range(3, 11)]          # anéis do rastro além da seção fixa (y do braço)


def _montar_quantico():
    import bpy
    estudo = os.path.join(AQUI, 'estudo_bracos_novos.py')
    sys.argv = [sys.argv[0], '--python', estudo, '--', 'nada']
    g = {'__name__': '__main__', '__file__': estudo}
    exec(compile(open(estudo, encoding='utf-8').read(), estudo, 'exec'), g)
    sc = bpy.context.scene
    for cn in ('filtro', 'empilhador'):
        for o in list(bpy.data.collections[cn].all_objects):
            if bpy.data.objects.get(o.name) is not None:
                bpy.data.objects.remove(o, do_unlink=True)
    sc.frame_set(1)
    sai = set()
    for o in list(sc.objects):
        laje = o.type == 'MESH' and o.parent is not None and o.parent.name == 'quantico_raiz'
        if laje or o.name.startswith(('quantico_esteiras', 'quantico_item_', 'chao')) or o.name.endswith('_campo') \
                or o.type == 'LIGHT':
            sai |= {o.name} | {c.name for c in o.children_recursive}
    for n in sai:
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    for i in range(3, 3 + len(Q_ANEIS)):                # anéis do rastro: de pé e visíveis (o jogo mostra/esconde)
        e = bpy.data.objects.get('quantico_anel_%d' % i)
        if e is None:
            continue
        e.animation_data_clear()
        e.scale = (1, 1, 1)
        for c in e.children_recursive:
            c.animation_data_clear()
            c.hide_render = c.hide_viewport = False
    raiz = bpy.data.objects['quantico_raiz']
    raiz.animation_data_clear()
    raiz.location = (0, 0, -ZQ0)
    bpy.context.view_layer.update()


def _quantico_json(sc, raiz, dados):
    dados['lanca'] = {'eixo_z': EQ, 'fluxo_z': ZCQ, 'ponta_y': 1.0, 'emax': 0.5, 'aneis': Q_ANEIS, 'cabo_l0': 0.43}


if __name__ == '__main__':
    if (sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '') == 'braco_quantico':
        _montar_quantico()

_PQ = {'lanca%d' % k: dict(objetos=['quantico_estagio%d_' % k, 'quantico_tubo%d_' % k], pivo=(0, 0, EQ), pai='corpo', tris=200)
       for k in range(1, 5)}
_PQ['ponta'] = dict(objetos=['quantico_garra_'], pivo=(0, -1.0, EQ), pai='corpo', tris=450)
_PQ['cabo'] = dict(objetos=['quantico_cabo_'], pivo=(0.125, -0.42, EQ - 0.062), pai='corpo', tris=60)
_PQ['carretel'] = dict(objetos=['quantico_carretel_'], pivo=(0.125, -0.42, EQ), pai='corpo', tris=260)
for _i, _y in enumerate(Q_ANEIS):
    _PQ['anel%d' % (_i + 1)] = dict(objetos=['quantico_anel_%d_' % (_i + 3)], pivo=(0, -_y, ZCQ), pai='corpo', tris=90)
CONFIG['braco_quantico'] = dict(script='conv_lote16.py', args=['braco_quantico'], cat='logistica/bracos', tris=4600,
                                tex=1024, margem=3.5, corpo='base', tirar=[], estudo='estudo_bracos_novos.py',
                                partes=_PQ, antes_de_exportar=_quantico_json)
