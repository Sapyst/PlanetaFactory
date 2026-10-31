"""Correções da conferência visual da fase 5 (docs/PLANO_INTEGRACAO.md, "Problemas encontrados na fase 5").
Cada entrada soma ao CONFIG da peça (o conv_*.py dela continua valendo): `tirar` acrescenta,
`depois` roda depois do depois_de_montar da peça, o resto substitui."""

def _conves_limpo(sc):
    """Convés da estação: o grafite do estudo assava em manchas de ruído e AO; aqui é tinta quase lisa."""
    import bpy

    def tinta(nome, cor):
        m = bpy.data.materials.new(nome)
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes['Principled BSDF']
        ru = nt.nodes.new('ShaderNodeTexNoise')
        ru.inputs['Scale'].default_value = 5.0
        co = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(co.outputs['Object'], ru.inputs['Vector'])
        rp = nt.nodes.new('ShaderNodeValToRGB')
        rp.color_ramp.elements[0].position, rp.color_ramp.elements[1].position = 0.35, 0.65
        rp.color_ramp.elements[0].color = (cor[0] * 0.92, cor[1] * 0.92, cor[2] * 0.92, 1)
        rp.color_ramp.elements[1].color = (cor[0] * 1.08, cor[1] * 1.08, cor[2] * 1.08, 1)
        nt.links.new(ru.outputs['Fac'], rp.inputs['Fac'])
        nt.links.new(rp.outputs['Color'], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.6
        return m
    for nome, cor in (('conves', (0.05, 0.053, 0.058)), ('conves_xadrez', (0.075, 0.08, 0.085))):
        o = bpy.data.objects.get(nome)
        if o is not None:
            o.data.materials[0] = tinta('Convés ' + nome, cor)


# mina de pulso: o monte de terra subia até o flange e cobria a bobina, que ainda fica sob a tampa. O monte fica baixo e mais
# curto (cabe no tile sem o recorte serrilhado) e um anel violeta aceso abraça a tampa, à vista da câmera do jogo.
_MINA_TROCAS = [
    ("hh = 0.036 + 0.012 * (r - 0.205) / 0.04", "hh = 0.016 + 0.006 * (r - 0.205) / 0.04"),
    ("t = min(1.0, (r - 0.245) / 0.25)\n        hh = 0.048 * (1 - t * t * (3 - 2 * t)) - 0.003 * t", "t = min(1.0, (r - 0.245) / 0.17)\n        hh = 0.022 * (1 - t * t * (3 - 2 * t)) - 0.003 * t"),
    ("rs = [0.207 + (0.62 - 0.207) * (k / 16) ** 1.35 for k in range(17)]", "rs = [0.207 + (0.43 - 0.207) * (k / 16) ** 1.35 for k in range(17)]"),
    ("alt_terra(r, an_) - (0.006 if r > 0.6 else 0.0)", "alt_terra(r, an_) - (0.006 if r > 0.41 else 0.0)"),
    ("    toro(P.B('bobina_luz', True), (0, 0, zc), 0.188, 0.0102, 72, 10)\n",
     "    toro(P.B('bobina_luz', True), (0, 0, 0.056), 0.232, 0.0125, 40, 6)\n"),
    ("    varrer(P.B('cobre', True), pts, 0.0016, 5)\n", ""),
    ("    for k in range(70):\n        r = random.uniform(0.22, 0.6)", "    for k in range(0):\n        r = random.uniform(0.22, 0.6)"),
    ("    for k in range(46):\n        r = random.uniform(0.25, 0.62)", "    for k in range(0):\n        r = random.uniform(0.25, 0.62)"),
    ("    for k in range(9):                                                   # capim deitado", "    for k in range(0):                                                   # capim deitado"),
    ("    for k in range(7):\n        a = random.uniform(0, 2 * PI)\n        r = random.uniform(0.62, 0.95)", "    for k in range(0):\n        a = random.uniform(0, 2 * PI)\n        r = random.uniform(0.62, 0.95)"),
]

AJUSTES = {
    'painel_solar': dict(por_peca=True, tris=9000),
    'estacao_drones': dict(por_peca=True, tris=11000, depois=_conves_limpo, tirar=['maq_fuligem', 'maq_oleo', 'conves_fuligem', 'cacos_fuligem', 'oleo']),
    'estacao': dict(por_peca=True, tris=11000, trocas=[(
        'chapa_corrugada(bm, X_PONTA - 0.04, 0.96, y0, y1, Z_VIGA + 0.122 + 0.006 * (k % 2), furos)',
        'chapa_corrugada(bm, X_PONTA - 0.04, 0.96, y0, y1, Z_VIGA + 0.122 + 0.006 * (k % 2), ())')]),
    'acumulador': dict(por_peca=True, tris=9000, tirar=['chamusco']),
    'silo_granel': dict(por_peca=True, tris=10000),
    'coletor_chuva': dict(por_peca=True, tris=10000),
    'mina_pulso': dict(por_peca=True, tris=3000, trocas=_MINA_TROCAS),
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
