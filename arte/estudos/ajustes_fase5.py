"""Correções da conferência visual da fase 5 (docs/PLANO_INTEGRACAO.md, "Problemas encontrados na fase 5").
Cada entrada soma ao CONFIG da peça (o conv_*.py dela continua valendo): `tirar` acrescenta,
`depois` roda depois do depois_de_montar da peça, o resto substitui."""

AJUSTES = {
    'painel_solar': dict(por_peca=True, tris=9000),
    'estacao_drones': dict(por_peca=True, tris=11000, tirar=['maq_fuligem', 'maq_oleo', 'conves_fuligem', 'cacos_fuligem']),
    'estacao': dict(por_peca=True, tris=11000, trocas=[(
        'chapa_corrugada(bm, X_PONTA - 0.04, 0.96, y0, y1, Z_VIGA + 0.122 + 0.006 * (k % 2), furos)',
        'chapa_corrugada(bm, X_PONTA - 0.04, 0.96, y0, y1, Z_VIGA + 0.122 + 0.006 * (k % 2), ())')]),
    'acumulador': dict(por_peca=True, tris=9000, tirar=['chamusco']),
    'silo_granel': dict(por_peca=True, tris=10000),
    'coletor_chuva': dict(por_peca=True, tris=10000),
    'mina_pulso': dict(por_peca=True, tris=3000),
    'terraplenagem': dict(por_peca=True, tris=11000, cortar_fixos=(-1.53, 1.53, -1.53, 1.53)),
    'viveiro': dict(por_peca=True, tris=9000, cortar_fixos=(-1.03, 1.03, -1.03, 1.03),
                    tirar=['capsulas_gastas', 'terra_fora', 'folha_fora', 'caule_fora', 'copa', 'troncos']),
    'coletor_lixo': dict(por_peca=True, tris=9000, tirar=['oleo_po'], cortar_fixos=(-1.03, 1.03, -1.03, 1.03)),
    'nucleo': dict(por_peca=True, tris=14000, tirar=['pedras', 'torroes', 'rachaduras'], cortar_fixos=(-1.53, 1.53, -1.53, 1.53)),
    'purificador_ar_2': dict(por_peca=True, tris=15000, intactos=['paineis'],
                             cotas={'virola': 500, 'deque_vigas': 500, 'pas0': 200, 'pas1': 200, 'pas2': 200},
                             tirar=['_rebites', 'grampos', 'escorridos', '_paraf']),
    'cano_subterraneo_entrada': dict(por_peca=True, tris=3000, vidro_opaco={'vidro': (0.05, 0.075, 0.08)}),
    'cano_subterraneo_saida': dict(por_peca=True, tris=3000, vidro_opaco={'vidro': (0.05, 0.075, 0.08)}),
    'braco_quantico': dict(por_peca=True, tris=7800),
    'acumulador_cristal': dict(por_peca=True, tris=7500, vidro_opaco={'camaras_vidro': (0.035, 0.07, 0.08)}),
    'bau_grande': dict(vidro_opaco={'gr_vidro': (0.04, 0.06, 0.065)}),
}


def aplicar(config):
    for nome, a in AJUSTES.items():
        cfg = config[nome]
        a = dict(a)
        cfg['tirar'] = list(cfg.get('tirar', [])) + a.pop('tirar', [])
        depois = a.pop('depois', None)
        if depois:
            antes = cfg.get('depois_de_montar')

            def junto(sc, antes=antes, depois=depois):
                if antes:
                    antes(sc)
                depois(sc)
            cfg['depois_de_montar'] = junto
        cfg.update(a)
