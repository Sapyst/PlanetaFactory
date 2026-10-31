"""Entradas do para_jogo.py para a LIMPEZA NOVA (fase 2.6 do docs/PLANO_INTEGRACAO.md). Nenhuma foto: os estudos
são montados no modo 'nada' (o estudo_limpeza_2x2.py renderiza dentro de cena_final mesmo sem 'foto': aqui ela vira
um retorno vazio antes de rodar).

Coletor de lixo 2 (coletor_lixo_2, 2×2) ← estudo_limpeza_2x2.py 'coletor': silo de duas câmaras, ciclones duplos,
  turbina, prensa enfardadeira, dois braços de sucção em torres giratórias (como no coletor 1, os bocais varrem além
  da laje na animação). Saem o drone-varredor com o cabo, a poeira e os fios dele (fica fora do tile; o jogo tem os
  drones de verdade), os fios de lama/cinza, as contas, o campo de sucção, o monte de fardos de fora e as poças.
Purificador de ar (purificador_ar, 2×2) ← estudo_limpeza_2x2.py 'purificador': saem a neblina, os fios de fuligem e o
  que passa da laje (fuligem e poças no chão).
Purificador atmosférico (purificador_ar_2, 3×3) ← estudo_purificador_atmosferico.py: sai o funil de fumaça (volume),
  as pedras e o que passa da área.
Viveiro 2 (viveiro_2, 2×2) ← estudo_viveiro2_semeador.py 'viveiro2': saem as árvores, cápsulas gastas e terra de fora
  e a cápsula em voo; as raízes que rachavam a laje são cortadas na borda. Seiva pela boca O0 (do estudo).
Semeador de bioma (semeador_bioma, 3×3) ← estudo_viveiro2_semeador.py 'semeador': a boca de água/seiva do estudo
  ficava fora do eixo do tile (y 0,38, z 0,32); aqui ela vem para o eixo e a altura dos canos (FLUIDO_ENT_O1 em
  y 0, z 0,35) — o cano corre por baixo do chassi (vigas a 0,56 m) como no estudo. Saem a grama, os brotos, as flores,
  os tocos, as brasas, a cinza e a névoa dos aspersores (o jogo restaura o chão de verdade).
Biodigestor (biodigestor, 3×3) ← estudo_biodigestor_tratamento.py 'bio': portas do estudo (água entra pelo sul,
  tile SO, a 0,30 m; seiva sai pelo leste a 0,34 m). O gasômetro inflava por shape key: fica na pose cheia.
Estação de tratamento (estacao_tratamento, 3×3) ← estudo_biodigestor_tratamento.py 'trat': como a bomba d'água, a
  tomada fica ao SUL (o cais e a grade avançam sobre o tile de água); saem a margem, o rio, as pedras, o lixo que boia,
  o jato de descarga, a pluma e as ondas; corta abaixo de −0,9 m. Água limpa sai pelo leste (porta do estudo, y −0,87,
  z 0,26 — fora do eixo, ver pendências).
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

SEM_FOTO = [("def cena_final(alvo, vistas, nome, perto, extra_perto=None):\n",
             "def cena_final(alvo, vistas, nome, perto, extra_perto=None):\n    return                       # conv_limpeza: sem foto\n")]
PORTA_SEMEADOR = [
    ("PORTA = Vector((-1.5, 0.38, 0.32))   # FLUIDO_ENT_O1",
     "PORTA = Vector((-1.5, 0.0, 0.35))    # FLUIDO_ENT_O1 (fase 2.6: eixo do tile, altura dos canos)"),
    # no estudo o cano descia por x = −1,25, através do pórtico do injetor oeste (pernas em y 0 e −0,24): agora contorna
    # por fora dele (x −1,40) até y 0,38, entra sob o piso e desce por x −0,95, livre das mãos-francesas
    ("cano(bm_aco, bm_f, [PORTA, Vector((-1.25, PORTA.y, PORTA.z)), Vector((-1.25, -0.42, PORTA.z)),",
     "cano(bm_aco, bm_f, [PORTA, Vector((-1.40, PORTA.y, PORTA.z)), Vector((-1.40, 0.38, PORTA.z)), Vector((-0.95, 0.38, PORTA.z)), Vector((-0.95, -0.42, PORTA.z)),"),
    ("for p_ in (Vector((-1.38, PORTA.y, 0)), Vector((-0.4, -0.42, 0)), Vector((0.4, -0.42, 0))):",
     "for p_ in (Vector((-1.40, 0.2, 0)), Vector((-0.4, -0.42, 0)), Vector((0.4, -0.42, 0))):"),
]


# fase 5: a fuligem do estudo, assada sem a luz dele, deixava a torre e os ventiladores pretos, e o miolo sumia; aqui a
# fuligem pesa menos da metade e a casca atrás dos painéis é chapa, não preto
PURIFICADOR_CLARO = [
    ("f2.inputs[1].default_value = forca", "f2.inputs[1].default_value = forca * 0.4"),
    ("suavizar(obj('casca_interna', bm, 'fuligem'))", "suavizar(obj('casca_interna', bm, 'chapa'))"),
]


def _executar(estudo, args, trocas=()):
    caminho = os.path.join(AQUI, estudo)
    cod = open(caminho, encoding='utf-8').read()
    for velho, novo in trocas:
        assert velho in cod, 'trecho não achado em %s: %s' % (estudo, velho[:60])
        cod = cod.replace(velho, novo, 1)
    sys.argv = [sys.argv[0], '--python', caminho, '--'] + list(args)
    sys.path.insert(0, AQUI)
    exec(compile(cod, caminho, 'exec'), {'__name__': '__main__', '__file__': caminho})


def _sem_shape_keys(sc):
    """Shape key (membrana que infla) não passa na redução: fica a pose base."""
    for o in sc.objects:
        if o.type == 'MESH' and o.data.shape_keys:
            o.shape_key_clear()


def _tirar_nomes(sc, prefixos):
    """Tira objetos cujo nome (sem o sufixo .001) começa com um dos prefixos."""
    import bpy
    for o in list(_de._vivos(sc)):
        base = o.name.split('.')[0]
        if any(base.startswith(p) for p in prefixos):
            _de._apagar(o)


def _cortar_nomes(sc, prefixos, x0, x1, y0, y1, z0=-0.03):
    """Recorte só nas peças fixas que passam da área (o resto, inclusive o que se mexe, fica)."""
    import bpy, bmesh
    from mathutils import Vector
    for o in [o for o in sc.objects if o.type == 'MESH' and any(o.name.split('.')[0].startswith(p) for p in prefixos)]:
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


# ------------------------------------------------------------------ ganchos
def _coletor2(sc):
    g = _de._g()
    _tirar_nomes(sc, ('drone_', 'rotor_drone', 'cabo_drone', 'cabo_forca', 'cabo_abracadeiras', 'fio_drone', 'poeira_drone',
                      'campo_drone', 'fio_sujeira', 'fio_grumo', 'conta', 'campo', 'vortice_', 'fardos_monte', 'fardos_farelo',
                      'oleo_pocas', 'chao_sujeira'))
    _de._limite_brilho(g, 120)


def _purificador(sc):
    g = _de._g()
    _tirar_nomes(sc, ('neblina', 'fio_fuligem', 'chao_sujeira'))
    _eb._recortar(sc, -1.0, 1.0, -1.0, 1.0, -0.03, 0.0)
    _de._limite_brilho(g, 120)


def _purificador2(sc):
    g = _de._g()
    _tirar_nomes(sc, ('pedras', 'chao', 'centelha'))
    _eb._recortar(sc, -1.5, 1.5, -1.5, 1.5, -0.03, 0.0)
    _de._limite_brilho(g, 160)


def _viveiro2(sc):
    g = _de._g()
    _tirar_nomes(sc, ('capsulas_gastas', 'terra_fora', 'troncos', 'copa', 'agulhas', 'caule_fora', 'folha_fora', 'capsula_voo', 'chao', 'semente',
                      'bolha'))
    _cortar_nomes(sc, ('raizes',), -1.0, 1.0, -1.0, 1.0)
    _sem_shape_keys(sc)
    _de._limite_brilho(g, 140)


def _semeador(sc):
    g = _de._g()
    _tirar_nomes(sc, ('grama', 'brotos', 'flores', 'tocos', 'brasas', 'restolho', 'cinza', 'nevoa_asp', 'lama_furo', 'chao',
                      'fumo', 'vapor', 'esporos', 'po_chao', 'respingo'))
    _cortar_nomes(sc, ('lama_pe',), -1.5, 1.5, -1.5, 1.5)
    _sem_shape_keys(sc)
    _de._limite_brilho(g, 160)


def _biodigestor(sc):
    g = _de._g()
    _sem_shape_keys(sc)
    _tirar_nomes(sc, ('chao',))
    _eb._recortar(sc, -1.5, 1.5, -1.5, 1.5, -0.03, 0.0)
    _de._limite_brilho(g, 160)


CENARIO_TRAT = ('margem', 'rio', 'enrocamento', 'pedras', 'jato', 'pluma', 'onda', 'nevoa', 'trat_alga', 'trat_palha',
                'trat_escuma', 'trat_galho', 'trat_plastico', 'trat_folha', 'trat_espuma', 'chao')


def _tratamento(sc):
    g = _de._g()
    _sem_shape_keys(sc)
    _tirar_nomes(sc, CENARIO_TRAT)
    _eb._recortar(sc, -1.5, 1.5, -1.95, 1.5, -0.9, 0.0)
    _de._limite_brilho(g, 160)


_BASE = dict(script='conv_limpeza.py', cat='maquinas', tex=1024, tirar=[])
CONFIG = {
    'coletor_lixo_2': dict(_BASE, args=['coletor_lixo_2'], estudo='estudo_limpeza_2x2.py', tris=9000, depois_de_montar=_coletor2),
    'purificador_ar': dict(_BASE, args=['purificador_ar'], estudo='estudo_limpeza_2x2.py', tris=8500, depois_de_montar=_purificador),
    'purificador_ar_2': dict(_BASE, args=['purificador_ar_2'], estudo='estudo_purificador_atmosferico.py', tris=11000,
                             depois_de_montar=_purificador2),
    'viveiro_2': dict(_BASE, args=['viveiro_2'], estudo='estudo_viveiro2_semeador.py', tris=9500, depois_de_montar=_viveiro2),
    'semeador_bioma': dict(_BASE, args=['semeador_bioma'], estudo='estudo_viveiro2_semeador.py', tris=11000,
                           depois_de_montar=_semeador),
    'biodigestor': dict(_BASE, args=['biodigestor'], estudo='estudo_biodigestor_tratamento.py', tris=11000,
                        depois_de_montar=_biodigestor),
    'estacao_tratamento': dict(_BASE, args=['estacao_tratamento'], estudo='estudo_biodigestor_tratamento.py', tris=11000,
                               margem=0.5, depois_de_montar=_tratamento),
}


if __name__ == '__main__':
    _peca = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''
    if _peca == 'coletor_lixo_2':
        _executar('estudo_limpeza_2x2.py', ['nada', 'coletor'], SEM_FOTO)
    elif _peca == 'purificador_ar':
        _executar('estudo_limpeza_2x2.py', ['nada', 'purificador'], SEM_FOTO)
    elif _peca == 'purificador_ar_2':
        _executar('estudo_purificador_atmosferico.py', ['nada'], PURIFICADOR_CLARO)
    elif _peca == 'viveiro_2':
        _executar('estudo_viveiro2_semeador.py', ['viveiro2', 'nada'])
    elif _peca == 'semeador_bioma':
        _executar('estudo_viveiro2_semeador.py', ['semeador', 'nada'], PORTA_SEMEADOR)
    elif _peca == 'biodigestor':
        _executar('estudo_biodigestor_tratamento.py', ['nada', 'bio'])
    elif _peca == 'estacao_tratamento':
        _executar('estudo_biodigestor_tratamento.py', ['nada', 'trat'])
