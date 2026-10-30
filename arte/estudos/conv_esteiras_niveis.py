"""Entradas do para_jogo.py para as ESTEIRAS EXPRESSA e QUÂNTICA (fase 2, item final do docs/PLANO_INTEGRACAO.md).

Mesmo método da esteira rápida (conv_logistica_base.py): as MESMAS peças e geometria da esteira do jogo
(conv_esteiras_bracos.py: reta, curvas, início, fim, rampa de junção, rampa, passagem entrada/saída), só com o
acabamento do nível de estudo_esteiras_niveis.py:
  expressa (logistica_4, nível 3): faixa AZUL-AÇO (0,13 0,22 0,36) gasta 0,25; as peças pintadas de amarelo (motor,
      guias da calha, pórtico da passagem) ficam no Azul-aço do estudo, lascadas até o aço. Lona P_EsteiraExpressa
      (o jogo rola no triplo). Saem como <peça>_expressa.
  quântica (logistica_5, nível 4): faixa VIOLETA (0,26 0,05 0,48) gasta 0,3; as peças amarelas viram o Ferro fundido
      enferrujado da estrutura rústica do estudo. Lona P_EsteiraQuantica (o jogo rola no quádruplo). Saem como
      <peça>_quantica.
Não entram (só cor/acabamento, como na rápida): o motor duplo e os rolos de apoio da expressa; o leito de bobinas,
o campo violeta, os anéis de campo, o conversor e a levitação dos itens da quântica.
Rodar: blender -b --python para_jogo.py -- esteira_reta_expressa   (etc.)"""
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
import importlib.util as _iu
_spec = _iu.spec_from_file_location('conv_esteiras_bracos', os.path.join(AQUI, 'conv_esteiras_bracos.py'))
_eb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_eb)
_spec2 = _iu.spec_from_file_location('conv_logistica_base', os.path.join(AQUI, 'conv_logistica_base.py'))
_lb = _iu.module_from_spec(_spec2)
_spec2.loader.exec_module(_lb)

AMARELO_LISTRA = (0.62, 0.42, 0.04)

# sufixo → (faixa, gasta, nome da tinta, (cor, metal, rugosidade, kwargs), material da lona, descrição)
NIVEIS = {
    'expressa': dict(faixa=(0.13, 0.22, 0.36), gasta=0.25, tinta='AzulExpressa',
                     mat=((0.10, 0.17, 0.27), 0, 0.42, dict(desgaste=0.85, sujeira=0.75)), lona='P_EsteiraExpressa',
                     desc='Esteira expressa (logistica_4): a mesma peça da esteira com o acabamento do nível 3 do '
                          'estudo (faixa azul-aço gasta, lascada até o aço); lona P_EsteiraExpressa (o jogo rola no '
                          'triplo da velocidade).'),
    'quantica': dict(faixa=(0.26, 0.05, 0.48), gasta=0.3, tinta='FerroQuantica',
                     mat=((0.16, 0.155, 0.15), 1.0, 0.62, dict(pintura=False, ferrugem=1.0, sujeira=0.9)),
                     lona='P_EsteiraQuantica',
                     desc='Esteira quântica (logistica_5): a mesma peça da esteira com o acabamento do nível 4 do '
                          'estudo (faixa violeta gasta, estrutura de ferro fundido enferrujado); lona '
                          'P_EsteiraQuantica (o jogo rola no quádruplo da velocidade).'),
}


def _pintar(cfg):
    def f(sc):
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
                    for n in m.node_tree.nodes:
                        if n.type == 'MIX' and n.blend_type == 'MIX' and n.data_type == 'RGBA' and \
                                tuple(round(x, 2) for x in n.inputs[7].default_value[:3]) == AMARELO_LISTRA:
                            n.inputs[7].default_value = (*cfg['faixa'], 1)
                    _lb._lascar(m, cfg['gasta'])
                    feitos.add(m.name)
                elif base == 'Amarelo':
                    v = bpy.data.materials.get(cfg['tinta'])
                    if v is None:
                        cor, metal, rug, kw = cfg['mat']
                        v = mats.material(cfg['tinta'], cor, metal, rug, **kw)
                        if kw.get('pintura', True):
                            _lb._lascar(v, cfg['gasta'] * 0.6)
                    s.material = v
    return f


def _antes(base, cfg):
    junta = _eb._uma_malha(base)

    def f(sc, raiz, dados):
        junta(sc, raiz, dados)
        for o in sc.objects:
            if o.type == 'MESH':
                for s in o.material_slots:
                    if s.material is not None and s.material.name.split('.')[0] == 'P_Esteira':
                        s.material.name = cfg['lona']
        dados['descricao'] = cfg['desc']
    return f


def _tunel(cfg):
    pinta = _pintar(cfg)

    def f(sc):
        _eb._acessorio()(sc)
        pinta(sc)
    return f


CONFIG = {}
for _suf, _cfg in NIVEIS.items():
    for _p, _t in (('esteira_reta', 700), ('esteira_curva_esq', 1100), ('esteira_curva_dir', 1100),
                   ('esteira_rampa', 900), ('esteira_inicio', 1200), ('esteira_fim', 1000), ('esteira_juncao', 1100)):
        CONFIG[_p + '_' + _suf] = dict(script='conv_esteiras_bracos.py', args=[_p], cat='logistica/esteira', tris=_t,
                                       tex=512, anima=False, tirar=[], depois_de_montar=_pintar(_cfg),
                                       antes_de_exportar=_antes(_p, _cfg))
    for _p, _c in (('esteira_tunel_entrada', (0.0, 0.0, 0.0)), ('esteira_tunel_saida', (0.0, 3.0, 0.0))):
        CONFIG[_p + '_' + _suf] = dict(script='estudo_esteira_acessorios.py', args=['tunel'], cat='logistica/esteira',
                                       tris=2000, tex=1024, anima=False, centro=_c,
                                       tirar=_eb.VIZINHOS + ['rampa_sobe' if 'entrada' in _p else 'rampa_desce'],
                                       depois_de_montar=_tunel(_cfg), antes_de_exportar=_antes(_p, _cfg))
