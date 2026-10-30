"""Entradas do para_jogo.py para a LOGÍSTICA DA ERA BASE (fase 2.2b do docs/PLANO_INTEGRACAO.md).

Esteira rápida (logistica_3) ← estudo_esteiras_niveis.py (nível 2: faixa VERMELHA gasta, lascada até o aço).
  Mesmas peças e geometria da esteira do jogo (conv_esteiras_bracos.py: reta, curvas, início, fim, rampa de junção,
  rampa, passagem entrada/saída), com o acabamento do nível 2 do estudo: a faixa de perigo e as peças pintadas de
  amarelo (motor, guias da calha, pórtico da passagem) ficam vermelhas, gastas e lascadas até o aço (a mesma conta
  do listras_cor do estudo). A lona é a mesma com outro nome de material, P_EsteiraRapida: o jogo a rola no dobro da
  velocidade (Materiais.ROLAGEM). Saem como <peça>_rapida.
Braço com filtro (braco_filtro) ← estudo_bracos_novos.py (BRAÇO COM FILTRO): o braço normal com scanner — câmera na
  garra, painel de seleção no chão com 5 luzes da IA, giroflex vermelho engaiolado. Este arquivo roda como script
  (args ['braco_filtro']): monta o estudo sem foto, fica só o braço do filtro (empilhador e quântico saem), pose de
  repouso (braço 1 de pé, braço 2 adiante, pistão mirando, dedos fechados), sem a animação do estudo; saem a laje de
  5 cm (tudo desce Z0, como o braço rápido), as esteiras e as placas de contexto e o leque do feixe de leitura (no
  jogo ficaria aceso parado). Giroflex apagado; painel com a 1ª luz acesa (o que o estudo mostra em repouso).
  Partes do jogo pelo empty de cada malha: giro (+ pinhão), braco1, braco2, garra (+ dedos e câmera), camisa e haste
  do pistão de elevação (como no braço longo: miram um no outro). Mesmos pivôs do braço rápido.
Divisor com filtro (divisor_filtro) ← estudo_esteiras_niveis.py (cena 'filtro'): o divisor aprovado + leitor de item
  (barra com janela violeta), câmera da IA, mostrador com a amostra do item filtrado e giroflex, seletor de
  prioridade N/L/O com alavanca e pistão. Como o divisor do jogo (conv_esteiras_bracos.py): leito desce para o do
  jogo, recorte no tile, só o mecanismo (garfo/batente/palhetas) segue com a animação do estudo. Saem as esteiras
  vizinhas, os itens e a cortina/linha de leitura (só aparecem quando um item passa).
Silo de granel (silo_granel, 3×3) ← estudo_silo.py: costado ondulado Ø 1,9 m sobre oito colunas, funil, comporta
  com pistão, rosca extratora até a caçamba sul, elevador de canecas pelo oeste, teto com radares e escotilha de drone.
  Fica a animação do estudo (canecas, rosca, comporta, radar, tampa, ponteiro e visor de nível); saem os efeitos
  (poeira, granel caindo da bica) e a grade de cubos da IA atrás do vidro (26 peças animadas pequenas demais para o
  celular; o vidro sai de qualquer jeito).
Cano subterrâneo (cano_subterraneo_entrada / _saida) ← estudo_cano_subterraneo.py: a caixa de concreto com a válvula,
  o passamuros, a tampa de inspeção para drone, o respiro e o sensor da IA. A cena tem o conjunto inteiro (cano reto
  → entrada em x = 1 → 4 tiles de terra → saída em x = 6 → cano reto, fluxo para leste): `centro` traz cada caixa
  para a origem girada para o fluxo do jogo (entra pelo sul, segue para o norte). Saem os canos e tampas vizinhos, o
  trecho enterrado, a terra revirada, os marcos e as placas do meio (no jogo os tiles do meio ficam livres), o chão,
  a grama, as poças, as gotas e o vapor. O que fica abaixo do chão sai (o terreno do jogo cobre); a laje e o cano da
  superfície ficam. Desenhado em lote como os canos: uma malha só (conv_logistica._uma_malha).
Rodar: blender -b --python para_jogo.py -- <nome>"""
import os, sys, math

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_esteiras_bracos', os.path.join(AQUI, 'conv_esteiras_bracos.py'))
_eb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eb)
_spec2 = _iu.spec_from_file_location('conv_logistica', os.path.join(AQUI, 'conv_logistica.py'))
_lg = _iu.module_from_spec(_spec2)
_spec2.loader.exec_module(_lg)

PI = math.pi

# ------------------------------------------------------------------ esteira rápida
VERMELHO = (0.48, 0.035, 0.02)      # faixa do nível 2 do estudo_esteiras_niveis.py
GASTA = 0.55


def _lascar(m, gasta):
    """Lascas até o aço oxidado em manchas (como listras_cor do estudo_esteiras_niveis.py)."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = b.inputs['Base Color']
    if not ent.links:
        return
    src = ent.links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ru = nt.nodes.new('ShaderNodeTexNoise')
    ru.inputs['Scale'].default_value, ru.inputs['Detail'].default_value = 22.0, 10.0
    ru.inputs['Roughness'].default_value = 0.7
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.62 - 0.12 * gasta
    mr.inputs['From Max'].default_value = 0.66 - 0.12 * gasta
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    c = nt.nodes.new('ShaderNodeMix')
    c.data_type = 'RGBA'
    nt.links.new(mr.outputs['Result'], c.inputs[0])
    nt.links.new(src, c.inputs[6])
    c.inputs[7].default_value = (0.20, 0.17, 0.15, 1)
    nt.links.new(c.outputs[2], ent)


def _vermelhar(sc):
    """Faixa listrada: cor do nível 2 + lascas; peças amarelas: tinta vermelha gasta (mats do estudo)."""
    import bpy
    sys.path.insert(0, AQUI)
    import mats
    feitos = set()
    for o in sc.objects:
        if o.type != 'MESH':
            continue
        for s in o.material_slots:
            m = s.material
            if m is None:
                continue
            base = m.name.split('.')[0]
            if base == 'Listras' and m.name not in feitos:
                mix = [n for n in m.node_tree.nodes if n.type == 'MIX' and n.blend_type == 'MIX' and n.data_type == 'RGBA']
                for n in mix:
                    if tuple(round(x, 2) for x in n.inputs[7].default_value[:3]) == (0.62, 0.42, 0.04):
                        n.inputs[7].default_value = (*VERMELHO, 1)
                _lascar(m, GASTA)
                feitos.add(m.name)
            elif base == 'Amarelo':
                v = bpy.data.materials.get('VermelhoRapida')
                if v is None:
                    v = mats.material('VermelhoRapida', (0.42, 0.05, 0.03), 0, 0.45, desgaste=0.9, sujeira=0.8)
                    _lascar(v, GASTA * 0.6)
                s.material = v


def _antes_rapida(base):
    junta = _eb._uma_malha(base)

    def f(sc, raiz, dados):
        junta(sc, raiz, dados)
        for o in sc.objects:
            if o.type == 'MESH':
                for s in o.material_slots:
                    if s.material is not None and s.material.name.split('.')[0] == 'P_Esteira':
                        s.material.name = 'P_EsteiraRapida'
        dados['descricao'] = ('Esteira rápida (logistica_3): a mesma peça da esteira com o acabamento do nível 2 do '
                              'estudo (faixa vermelha gasta, lascada até o aço); lona P_EsteiraRapida (o jogo rola no '
                              'dobro da velocidade).')
    return f


def _depois_tunel(sc):
    _eb._acessorio()(sc)
    _vermelhar(sc)


CONFIG = {}
for _p, _t in (('esteira_reta', 700), ('esteira_curva_esq', 1100), ('esteira_curva_dir', 1100), ('esteira_rampa', 900),
               ('esteira_inicio', 1200), ('esteira_fim', 1000), ('esteira_juncao', 1100)):
    CONFIG[_p + '_rapida'] = dict(script='conv_esteiras_bracos.py', args=[_p], cat='logistica/esteira', tris=_t, tex=512,
                                  anima=False, tirar=[], depois_de_montar=_vermelhar, antes_de_exportar=_antes_rapida(_p))
for _p, _c in (('esteira_tunel_entrada', (0.0, 0.0, 0.0)), ('esteira_tunel_saida', (0.0, 3.0, 0.0))):
    CONFIG[_p + '_rapida'] = dict(script='estudo_esteira_acessorios.py', args=['tunel'], cat='logistica/esteira', tris=2000,
                                  tex=1024, anima=False, centro=_c,
                                  tirar=_eb.VIZINHOS + ['rampa_sobe' if 'entrada' in _p else 'rampa_desce'],
                                  depois_de_montar=_depois_tunel, antes_de_exportar=_antes_rapida(_p))


# ------------------------------------------------------------------ braço com filtro
Z0 = 0.05
PIV_FILTRO = dict(giro=(0, 0, 0.225), braco1=(0, 0, 0.40), braco2=(0, 0, 0.95), garra=(0, 0.62, 0.95),
                  camisa=(0, -0.20, 0.375), haste=(0, -0.05, 0.65))
PAI_FILTRO = dict(giro='base', braco1='giro', braco2='braco1', garra='braco2', camisa='giro', haste='braco1')
# empty do estudo → parte do jogo
PARTE_DO_EMPTY = {'filtro_giro': 'giro', 'filtro_pinhao': 'giro', 'filtro_braco1': 'braco1', 'filtro_braco2': 'braco2',
                  'filtro_garra': 'garra', 'filtro_dedo_-1': 'garra', 'filtro_dedo_1': 'garra',
                  'filtro_pistao_camisa': 'camisa', 'filtro_pistao_haste': 'haste'}


def _montar_braco_filtro():
    import bpy
    estudo = os.path.join(AQUI, 'estudo_bracos_novos.py')
    sys.argv = [sys.argv[0], '--python', estudo, '--', 'nada']
    g = {'__name__': '__main__', '__file__': estudo}
    exec(compile(open(estudo, encoding='utf-8').read(), estudo, 'exec'), g)
    sc = bpy.context.scene
    for cn in ('empilhador', 'quantico'):               # só o braço do filtro
        for o in list(bpy.data.collections[cn].objects):
            bpy.data.objects.remove(o, do_unlink=True)
    A = g['fil']
    g['posar2'](A, 0.0, PI / 2, 0.0, 1)                # repouso
    for d, s_ in A['dedos']:                           # dedos fechados
        d.e.location = d.pivo - A['g'].pivo
    for o in list(sc.objects):
        o.animation_data_clear()
        if o.type == 'LIGHT' and o.data.animation_data:
            o.data.animation_data_clear()
    for m in bpy.data.materials:
        if m.node_tree and m.node_tree.animation_data:
            m.node_tree.animation_data_clear()
    M = g['M']
    M['giroflex'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
    M['slot_flash'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 8.0
    fora = ['filtro_esteira_s', 'filtro_esteira_n', 'filtro_item_certo', 'filtro_item_errado', 'filtro_feixe', 'chao']
    sai = set()
    for o in list(sc.objects):
        laje = o.type == 'MESH' and o.parent is not None and o.parent.name == 'filtro_raiz'
        if laje or any(o.name.startswith(f) for f in fora):
            sai |= {o.name} | {c.name for c in o.children_recursive}
    for n in sai:
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    raiz = bpy.data.objects['filtro_raiz']
    raiz.location = (0, 0, -Z0)
    bpy.context.view_layer.update()
    for k, o in enumerate([o for o in sc.objects if o.type in ('MESH', 'FONT')]):
        p = o.parent
        while p is not None:
            if p.type == 'EMPTY' and p.name in PARTE_DO_EMPTY:
                o.name = 'q%sq_%d' % (PARTE_DO_EMPTY[p.name], k)
                break
            p = p.parent


def _braco_filtro_json(sc, raiz, dados):
    dados['garra'] = {'pulso_dz': -0.05, 'item': 0.065}   # dedos até 0,175 m abaixo do pulso (como o normal/longo)
    corpo = next(o for o in sc.objects if o.type == 'MESH' and o.name.endswith('_base'))
    novos = []
    for t in dados.get('terminais', []):
        zs = [(corpo.matrix_world @ v.co).z for v in corpo.data.vertices
              if math.hypot((corpo.matrix_world @ v.co).x - t[0], (corpo.matrix_world @ v.co).y - t[1]) < 0.12]
        novos.append([t[0], t[1], round(max(zs), 3) if zs else t[2]])
    if novos:
        dados['terminais'] = novos
    dados['descricao'] = ('Braço com filtro: o braço normal com scanner (câmera na garra), painel de seleção no chão com '
                          '5 luzes da IA e giroflex vermelho. Só pega os itens escolhidos (até 5). Partes: giro, braco1, '
                          'braco2, garra, camisa/haste do pistão de elevação.')


CONFIG['braco_filtro'] = dict(
    script='conv_logistica_base.py', args=['braco_filtro'], cat='logistica/bracos', tris=2400, tex=1024, anima=False,
    margem=1.0, corpo='base', tirar=[],
    depois_de_montar=lambda sc: _eb._recortar(sc, -0.5, 0.5, -0.5, 2.0, 0.0, 0.0, False),
    partes={pn: dict(objetos=['q%sq' % pn], pivo=p, pai=PAI_FILTRO[pn],
                     tris=dict(giro=500, braco1=450, braco2=300, garra=300, camisa=250, haste=100)[pn])
            for pn, p in PIV_FILTRO.items()},
    antes_de_exportar=_braco_filtro_json)


# ------------------------------------------------------------------ divisor com filtro
CONFIG['divisor_filtro'] = dict(script='estudo_esteiras_niveis.py', args=['filtro'], cat='logistica/esteira', tris=4000,
                                tex=1024, tirar=_eb.VIZINHOS + ['cortina', 'linha_leito'],
                                depois_de_montar=_eb._acessorio(-0.5, 0.5, -0.5, 0.5, ('batente', 'carro', 'palheta')))


# ------------------------------------------------------------------ silo de granel
CONFIG['silo_granel'] = dict(script='estudo_silo.py', args=['nada'], cat='logistica/armazenagem', tris=10000, tex=1024,
                             tirar=['poeira', 'queda_', 'silo_grade_', 'plano_nivel', 'campo_fundo', 'caneca_granel'])


# ------------------------------------------------------------------ cano subterrâneo
SUBTERRANEO_FORA = ['reto_o', 'reto_l', 'tampa_o', 'tampa_l', 'enterrado', 'fita_aviso', 'aterro', 'monte', 'torrao',
                    'pedra', 'marco', 'placa', 'solo', 'grama', 'poca', 'mancha', 'halo', 'agua_', 'furo', 'gota',
                    'vapor']
for _p, _c in (('cano_subterraneo_entrada', (1.0, 0.0, -PI / 2)), ('cano_subterraneo_saida', (6.0, 0.0, -PI / 2))):
    CONFIG[_p] = dict(script='estudo_cano_subterraneo.py', args=['nada'], cat='logistica/canos', tris=1600, tex=512,
                      anima=False, centro=_c, margem=0.06, tirar=list(SUBTERRANEO_FORA),
                      depois_de_montar=lambda sc: _eb._recortar(sc, -0.5, 0.5, -0.5, 0.5, -0.03, 0.0),
                      antes_de_exportar=_lg._uma_malha)


if __name__ == '__main__':
    _peca = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''
    if _peca == 'braco_filtro':
        _montar_braco_filtro()
