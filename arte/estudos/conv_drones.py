"""Entradas do para_jogo.py para os DRONES (fase 2.6 do docs/PLANO_INTEGRACAO.md).

Estação de drones (estacao_drones, 2×2) ← estudo_drones.py (cena montada no modo 'nada'), só a coleção 'estacao':
  laje, colunas, convés, fabricadora com os 3 projetores do holograma, 2 berços de recarga com garras e plugue,
  revista de remendos com o braço abastecedor, tanque d'água com bomba, estoque de placas, farol, sujeira e cacos.
  A animação do jogo ("trabalho", laço de 4 s) é o bloco POUSO/RECARGA do estudo (quadros 385–480: garras fecham,
  plugue encaixa, braço abastecedor vai à revista): as chaves descem 384 quadros. Sai o remendo que o braço leva
  (no estudo ele cai no funil do drone pousado, que no jogo é desenhado à parte) e os cabos que iam até 1,6 m (recorte
  na borda). Entrada de água do jogo: ramal novo pela borda SUL, tile leste, a 0,35 m (FLUIDO_ENT_S1), reto até o
  costado do tanque (passa por baixo da diagonal da estrutura, que está a 0,5 m ali).
Drones (drone_reparo, drone_defesa, drone_logistico; categoria 'drones', tipo 'veiculo') ← estudo_drones_modelo.py,
  a mesma função drone() do estudo montada sozinha na origem (centro do corpo; frente +X; patins em z = −0,158).
  Partes que o jogo mexe (DesenhoDrones): rotor0..3 (sino + pás; giram no eixo deles), e por tipo
    reparo    giro → ombro → cotovelo (braço de solda; a tocha fica no cotovelo)
    defesa    torre (guinada) → canhao (elevação) → boca (emissores, brilho)
    logistico pendulo (junta cardã, haste, garra) → carga (placa presa na garra; o jogo esconde sem carga)
  Saem o disco de borrão das hélices (o jogo gira as pás de verdade), o arco de solda e o clarão de boca (efeitos do
  jogo) e os pistõezinhos do braço de solda (no estudo são orientados quadro a quadro; parados na pose de descanso
  entrariam no corpo).
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

DESLOCA = 384            # bloco POUSO/RECARGA (385–480) vira o laço 1–96
R_DUTO_C = 0.27


def _curvas(a):
    """F-curves de uma ação (Blender 5: camadas → faixas → channelbags)."""
    if hasattr(a, 'layers'):
        for ly in a.layers:
            for st in ly.strips:
                for cb in st.channelbags:
                    yield from cb.fcurves
    else:
        yield from a.fcurves


def _deslocar_chaves(desloca):
    import bpy
    for a in bpy.data.actions:
        for fc in _curvas(a):
            for kp in fc.keyframe_points:
                kp.co.x -= desloca
                kp.handle_left.x -= desloca
                kp.handle_right.x -= desloca
            fc.update()


def _ramal_agua(sc):
    """Entrada do jogo: borda sul, tile leste (x = 0,5), eixo a 0,35 m, reto até o costado do tanque."""
    import bpy, bmesh
    from mathutils import Vector, Matrix
    import base3d
    from base3d import tubo, cil, caixa_de
    M = base3d.M
    Z, ZT = 0.35, 0.27                     # porta do jogo; entrada no tanque entre as cintas de 0,18 e 0,36
    pts = [Vector((0.5, -0.99, Z)), Vector((0.5, -0.86, Z)), Vector((0.5, -0.86, ZT)), Vector((0.58, -0.86, ZT)),
           Vector((0.58, -0.68, ZT))]      # desvia do visor de nível (x ≤ 0,48) e entra no costado do tanque
    bm, bf, bs = bmesh.new(), bmesh.new(), bmesh.new()
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, 0.022, 14)
    for p in pts[1:-1]:                    # cotovelos
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.022, matrix=Matrix.Translation(p))
    cil(bf, Vector((0.5, -0.975, Z)), 0.034, 0.02, Vector((0, 1, 0)), lados=14)        # flange da porta (borda sul)
    cil(bf, Vector((0.58, -0.697, ZT)), 0.034, 0.016, Vector((0, 1, 0)), lados=14)     # flange no costado
    caixa_de(bs, (0.515, -0.875, 0.081), (0.565, -0.845, ZT - 0.022))            # pé do cano sobre a laje
    for nome, b, m in (('kit_ramal', bm, 'cobre'), ('kit_ramal_flanges', bf, 'ferro'), ('kit_ramal_pe', bs, 'amarelo_gasto')):
        me = bpy.data.meshes.new(nome)
        b.to_mesh(me)
        b.free()
        o = bpy.data.objects.new(nome, me)
        sc.collection.objects.link(o)
        o.data.materials.append(M[m])


def _estacao(sc):
    g = _de._g()
    _de._so_colecao(sc, 'estacao')
    _de._tirar(sc, 'remendo_braco')
    _ramal_agua(sc)
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)
    _de._limite_brilho(g, 140)


def _drone_montar(sc):
    g = _de._g()
    _de._tirar(sc, 'borrao', '_arco', 'clarao', 'pistao_')
    _de._limite_brilho(g, 60)


def _rotores(nome):
    out = {}
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        out['rotor%d' % k] = dict(objetos=['%s_sino%d' % (nome, k), '%s_pas%d' % (nome, k)],
                                  pivo=(round(math.cos(a) * R_DUTO_C, 5), round(math.sin(a) * R_DUTO_C, 5), 0.0), tris=180)
    return out


def _partes(tipo):
    nome = 'drone_' + tipo
    p = _rotores(nome)
    if tipo == 'reparo':
        p['giro'] = dict(objetos=[nome + '_braco_base'], pivo=(0.035, 0.0, -0.066), tris=120)
        p['ombro'] = dict(objetos=[nome + '_braco_sup'], pivo=(0.035, 0.0, -0.1), pai='giro', tris=90)
        p['cotovelo'] = dict(objetos=[nome + '_braco_ant', nome + '_tocha', nome + '_marcas_solda', nome + '_mangueira'],
                             pivo=(0.145, 0.0, -0.1), pai='ombro', tris=160)
    elif tipo == 'defesa':
        p['torre'] = dict(objetos=[nome + '_torre_casa', nome + '_torre_celula'], pivo=(0.0, 0.0, -0.066), tris=200)
        p['canhao'] = dict(objetos=[nome + '_culatra', nome + '_canos', nome + '_boca_fuligem', nome + '_ejecao'],
                           pivo=(0.0, 0.0, -0.111), pai='torre', tris=260)
        p['boca'] = dict(objetos=[nome + '_emissores'], pivo=(0.158, 0.0, -0.111), pai='canhao', tris=60)
    else:
        p['pendulo'] = dict(objetos=[nome + '_haste', nome + '_garra'], pivo=(0.0, 0.0, -0.095), tris=260)
        p['carga'] = dict(objetos=[nome + '_placa_ferro'], pivo=(0.0, 0.0, -0.167), pai='pendulo', tris=24)
    return p


CONFIG = {
    'estacao_drones': dict(script='conv_drones.py', args=['estacao_drones'], estudo='estudo_drones.py', cat='drones',
                           tris=9000, tex=1024, tirar=['farol_luz', 'luz_pouso'], depois_de_montar=_estacao),
}
for _t in ('reparo', 'defesa', 'logistico'):
    CONFIG['drone_' + _t] = dict(script='conv_drones.py', args=['drone_' + _t], estudo='estudo_drones_modelo.py',
                                 cat='drones', tris=2600, tex=512, anima=False, tirar=[], depois_de_montar=_drone_montar,
                                 partes=_partes(_t))


def _so_drone(tipo):
    import bpy
    sys.path.insert(0, AQUI)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import base3d, estudo_drones_modelo as DM
    base3d.iniciar()
    DM.criar_materiais()
    DM.colecao('drone')
    DM.drone(tipo, 'drone_' + tipo)
    bpy.context.view_layer.update()


if __name__ == '__main__':
    _peca = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''
    if _peca == 'estacao_drones':
        caminho = os.path.join(AQUI, 'estudo_drones.py')
        sys.argv = [sys.argv[0], '--python', caminho, '--', 'nada']
        sys.path.insert(0, AQUI)
        exec(compile(open(caminho, encoding='utf-8').read(), caminho, 'exec'), {'__name__': '__main__', '__file__': caminho})
        _deslocar_chaves(DESLOCA)
    elif _peca.startswith('drone_'):
        _so_drone(_peca[6:])
