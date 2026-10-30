"""Estudo isolado (fora do jogo): montadora 2 (3×3 tiles).
Evolução industrial de Tier 2 da montadora básica:
- Silhueta 3×3 reconhecível: pórtico mais denso, treliças de reforço, acabamento em azul-petróleo industrial desgastado
  com primer óxido vermelho e chapas de reforço aparafusadas.
- Entradas e saídas de itens: esteira interna sul → norte a z = 0,23 m (topo da esteira).
- Entrada de fluidos: boca oeste a x = -1.44 m, y = 0.0 m, z = 0.35 m com flange padrão, válvula esfera e manômetro.
- 2 Slots de Módulos: baia lateral com dois cartuchos de módulo encaixados, aletas dissipadoras e LEDs de barramento.
- Estações internas:
  1. Alimentador rotativo + braço SCARA rápido com magazine de ponteiras.
  2. Prensa eletroidráulica dupla reforçada com guias cromadas, sensores ópticos e amortecedores.
  3. Braço de solda a laser/plasma de alta precisão com bateria externa de 3 cilindros de gás de purga (argônio).
- Fenômeno da IA: anel focalizador quântico no teto com cristal ressonador emitindo feixe de calibração atômica.
- Sistema de exaustão com ciclone centrífugo, coifa de captação e duto espiral no teto.
- Unidade hidráulica de alta pressão e compressor duplo em V.

Uso: blender -b --python estudo_montadora_2.py -- foto | video | nada
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço fechado
random.seed(42)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def curva(bm, p, r, lados=14):
    """Cotovelo arredondado (esfera do raio do tubo)."""
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=8, radius=r, matrix=Matrix.Translation(Vector(p)))


def cano(bm, bf, pts, r):
    """Cano rígido por pontos: trechos retos, cotovelos redondos e flanges perto de cada curva."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        tubo(bm, a, b, r, 16)
        u = (b - a).normalized()
        for c in (a + u * 0.05, b - u * 0.05):
            tubo(bf, c - u * 0.008, c + u * 0.008, r * 1.5, 16)
    for c in pts[1:-1]:
        curva(bm, c, r, 16)


def luz_mat(nome, cor, forca=6.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat():
    m = bpy.data.materials.new('Vidro')
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.72, 0.85, 0.82, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Alpha'].default_value = 0.35
    b.inputs['IOR'].default_value = 1.45
    return m


def malha_mat():
    """Tela de arame fina: chapa transparente onde não há fio."""
    m = bpy.data.materials.new('Tela')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.05, 0.05, 0.055, 1)
    b.inputs['Metallic'].default_value = 0.8
    b.inputs['Roughness'].default_value = 0.5
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hz = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(sep.outputs['X'], hz.inputs[0])
    nt.links.new(sep.outputs['Y'], hz.inputs[1])
    fios = []
    for entrada in (hz.outputs['Value'], sep.outputs['Z']):
        d = no(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = 0.03
        nt.links.new(entrada, d.inputs[0])
        fr = no(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs['Value'], fr.inputs[0])
        lt = no(nt, 'ShaderNodeMath', operation='LESS_THAN')
        lt.inputs[1].default_value = 0.12
        nt.links.new(fr.outputs['Value'], lt.inputs[0])
        fios.append(lt)
    mx = no(nt, 'ShaderNodeMath', operation='MAXIMUM')
    nt.links.new(fios[0].outputs['Value'], mx.inputs[0])
    nt.links.new(fios[1].outputs['Value'], mx.inputs[1])
    nt.links.new(mx.outputs['Value'], b.inputs['Alpha'])
    return m


base3d.M.update({
    'azul_petroleo': mats.material('Azul Industrial', (0.08, 0.22, 0.32), 0, 0.42, desgaste=1.2, sujeira=1.0, ferrugem=0.6),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=1.1, sujeira=1.0, ferrugem=0.55),
    'laranja': mats.material('Laranja', (0.62, 0.22, 0.04), 0, 0.45, desgaste=1.1, sujeira=1.0, ferrugem=0.55),
    'primer_oxido': mats.material('Primer Óxido', (0.38, 0.12, 0.08), 0, 0.65, desgaste=0.8, sujeira=0.9, ferrugem=0.85),
    'verde_gas': mats.material('Cilindro argônio', (0.04, 0.22, 0.16), 0, 0.45, desgaste=0.9, sujeira=0.8, ferrugem=0.35),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.7),
    'cinza': mats.material('Cinza', (0.22, 0.23, 0.24), 0, 0.5, desgaste=1.0, sujeira=1.0, ferrugem=0.6),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.7, sujeira=0.8, escovado=True),
    'peca': mats.material('Peça', (0.52, 0.53, 0.55), 1.0, 0.32, pintura=False, ferrugem=0.15, sujeira=0.3, escovado=True),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.12, pintura=False, sujeira=0.25),
    'cobre': mats.material('Cobre', (0.80, 0.42, 0.24), 1.0, 0.3, pintura=False, sujeira=0.6),
    'ouro': mats.material('Ouro Conector', (0.85, 0.68, 0.18), 1.0, 0.22, pintura=False, sujeira=0.2),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.6, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.06, pintura=False, sujeira=0.0, desgaste=0.0),
    'cordao': mats.material('Cordão', (0.16, 0.12, 0.1), 1.0, 0.5, pintura=False, sujeira=0.5, ferrugem=0.3),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'vidro': vidro_mat(),
    'malha': malha_mat(),
    'listras': base3d.listras_mat(),
    'faisca': luz_mat('Faísca', (0.4, 0.8, 1.0), 12.0),
    'laser': luz_mat('Laser Plasma', (0.1, 0.6, 1.0), 20.0),
    'cristal': luz_mat('Cristal IA', (0.2, 0.85, 1.0), 8.0),
    'verde': luz_mat('Luz verde', (0.15, 1.0, 0.25), 6.0),
    'vermelho': luz_mat('Luz vermelha', (1.0, 0.08, 0.05), 6.0),
    'ambar': luz_mat('Luz âmbar', (1.0, 0.5, 0.05), 6.0),
    'ciano': luz_mat('Luz ciano', (0.1, 0.9, 1.0), 8.0),
    'fumaca': base3d.volume_mat('Fumaça da solda', (0.20, 0.22, 0.24), 2.8, 0.65, 3.2),
})

H = 1.88                     # altura do pórtico reforçado
ZB = 0.62                    # cota de trabalho da esteira interna (mesma da montadora 1)
Y_ALIMENTA, Y_PRENSA, Y_LASER = -0.62, 0.0, 0.62

# ------------------------------------------------------------------ laje e fundação com canaletas
bm = bmesh.new()
caixa_de(bm, (-1.48, -1.48, 0), (1.48, 1.48, 0.08))                         # laje principal 3×3 tiles
# rebaixos / sapatas no concreto
for x in (-1.42, 1.42):
    for y in (-1.42, 0.0, 1.42):
        caixa_de(bm, (x - 0.12, y - 0.12, 0.08), (x + 0.12, y + 0.12, 0.11))
obj('laje', bm, 'concreto')

# canaletas e faixas de perigo zebradas
bm = bmesh.new()
for x0, x1 in ((-0.44, -0.36), (0.36, 0.44)):
    caixa_de(bm, (x0, -1.48, 0.081), (x1, 1.48, 0.083))
for y in (-0.35, 0.35):
    caixa_de(bm, (-0.65, y - 0.035, 0.081), (-0.44, y + 0.035, 0.083))
    caixa_de(bm, (0.44, y - 0.035, 0.081), (0.65, y + 0.035, 0.083))
obj('faixas_piso', bm, 'listras')

# ------------------------------------------------------------------ pórtico reforçado (azul-petróleo + chapas óxido)
POSTES = [(x, y) for x in (-1.42, 1.42) for y in (-1.42, 0.0, 1.42)] + [(x, y) for x in (-0.46, 0.46) for y in (-1.42, 1.42)]
bm = bmesh.new()
bm_ox = bmesh.new()

for x, y in POSTES:
    caixa_de(bm, (x - 0.045, y - 0.045, 0.08), (x + 0.045, y + 0.045, H))
    caixa_de(bm, (x - 0.08, y - 0.08, 0.08), (x + 0.08, y + 0.08, 0.13))   # sapata de aço
    # parafusos da sapata
    for dx, dy in ((-0.06, -0.06), (0.06, -0.06), (-0.06, 0.06), (0.06, 0.06)):
        cil(bm, Vector((x + dx, y + dy, 0.135)), 0.01, 0.014, lados=6)

# vigas superiores perimetrais e treliças diagonais
for y in (-1.42, 1.42):
    caixa_de(bm, (-1.42, y - 0.05, H - 0.09), (1.42, y + 0.05, H))
    # reforço angular tipo mão-francesa
    for x in (-1.35, 1.35):
        caixa_de(bm_ox, (x - 0.02, y - 0.048, H - 0.28), (x + 0.02, y + 0.048, H - 0.09))
for x in (-1.42, 1.42):
    caixa_de(bm, (x - 0.05, -1.42, H - 0.09), (x + 0.05, 1.42, H))
    for y in (-1.35, 1.35):
        caixa_de(bm_ox, (x - 0.048, y - 0.02, H - 0.28), (x + 0.048, y + 0.02, H - 0.09))

# vigas centrais longitudinais de sustentação do teto técnico
for x in (-0.92, 0.0, 0.92):
    caixa_de(bm, (x - 0.04, -1.42, H - 0.08), (x + 0.04, 1.42, H))

# vergas com listras de perigo sobre a esteira nas bocas norte e sul
for y in (-1.42, 1.42):
    caixa_de(bm, (-0.46, y - 0.055, 1.05), (0.46, y + 0.055, 1.15))

obj('portico', bm, 'azul_petroleo')
obj('portico_reforcos', bm_ox, 'primer_oxido')

bm_listras = bmesh.new()
for y in (-1.42, 1.42):
    caixa_de(bm_listras, (-0.46, y - 0.056, 1.05), (0.46, y + 0.056, 1.15))
obj('verga_listras', bm_listras, 'listras')

# chapas de rodapé grossas e chapas de fechamento inferior
bm_rod = bmesh.new()
for x in (-1.42, 1.42):
    caixa_de(bm_rod, (x - 0.015, -1.38, 0.08), (x + 0.015, 1.38, 0.48))
for y in (-1.42, 1.42):
    for x0, x1 in ((-1.38, -0.50), (0.50, 1.38)):
        caixa_de(bm_rod, (x0, y - 0.015, 0.08), (x1, y + 0.015, 0.48))
obj('rodape', bm_rod, 'cinza')

# janelas de inspeção e telas de proteção perimetral
bm_gaiola, bm_tela = bmesh.new(), bmesh.new()
for x in (-1.42, 1.42):
    # tela nas laterais
    for y0, y1 in ((-1.38, -0.05), (0.05, 1.38)):
        caixa_de(bm_tela, (x - 0.002, y0, 0.50), (x + 0.002, y1, H - 0.11))
        # requadro
        caixa_de(bm_gaiola, (x - 0.02, y0, 0.48), (x + 0.02, y1, 0.52))
        caixa_de(bm_gaiola, (x - 0.02, y0, H - 0.13), (x + 0.02, y1, H - 0.09))
        caixa_de(bm_gaiola, (x - 0.02, y0, 0.48), (x + 0.02, y0 + 0.03, H - 0.09))
        caixa_de(bm_gaiola, (x - 0.02, y1 - 0.03, 0.48), (x + 0.02, y1, H - 0.09))
obj('gaiola_molduras', bm_gaiola, 'grafite')
obj('gaiola_tela', bm_tela, 'malha')

# janelas de vidro aramado na frente sul e norte
bm_jan_mold, bm_vidro = bmesh.new(), bmesh.new()
for y in (-1.42, 1.42):
    for x0, x1 in ((-1.38, -0.50), (0.50, 1.38)):
        caixa_de(bm_vidro, (x0, y - 0.004, 0.50), (x1, y + 0.004, H - 0.11))
        caixa_de(bm_jan_mold, (x0, y - 0.02, 0.48), (x1, y + 0.02, 0.52))
        caixa_de(bm_jan_mold, (x0, y - 0.02, H - 0.13), (x1, y + 0.02, H - 0.09))
        caixa_de(bm_jan_mold, (x0, y - 0.02, 0.48), (x0 + 0.035, y + 0.02, H - 0.09))
        caixa_de(bm_jan_mold, (x1 - 0.035, y - 0.02, 0.48), (x1, y + 0.02, H - 0.09))
        caixa_de(bm_jan_mold, ((x0 + x1) / 2 - 0.015, y - 0.02, 0.48), ((x0 + x1) / 2 + 0.015, y + 0.02, H - 0.09))
obj('janelas_moldura', bm_jan_mold, 'grafite')
obj('janelas_vidro', bm_vidro, 'vidro')

# ------------------------------------------------------------------ esteira central (sul → norte, z = 0.23 m)
# bocas de esteira exatamente nas bordas y = -1.48 m e y = +1.48 m
bm_est = bmesh.new()
for x in (-0.30, 0.30):
    caixa_de(bm_est, (x - 0.025, -1.48, ZB - 0.16), (x + 0.025, 1.48, ZB - 0.01))
    for y in (-1.35, -0.8, -0.2, 0.4, 0.9, 1.35):
        caixa_de(bm_est, (x - 0.03, y - 0.03, 0.08), (x + 0.03, y + 0.03, ZB - 0.16))
obj('esteira_estrutura', bm_est, 'grafite')

bm_lona = bmesh.new()
caixa_de(bm_lona, (-0.26, -1.48, ZB - 0.02), (0.26, 1.48, ZB))
for y in (-1.46, 1.46):
    cil(bm_lona, Vector((0, y, ZB - 0.05)), 0.045, 0.52, Vector((1, 0, 0)), lados=16)
obj('esteira_lona', bm_lona, 'borracha')

# roletes de apoio intermediários
bm_rol = bmesh.new()
for yr in (-1.2, -0.8, -0.4, 0.2, 0.4, 0.8, 1.2):
    cil(bm_rol, Vector((0, yr, ZB - 0.04)), 0.022, 0.54, Vector((1, 0, 0)), lados=12)
obj('esteira_roletes', bm_rol, 'aco')

# taliscas de arraste móveis
taliscas = []
for i in range(12):
    bm_t = bmesh.new()
    caixa(bm_t, (0, 0, 0.002), (0.50, 0.018, 0.004))
    taliscas.append(obj('talisca_%d' % i, bm_t, 'grafite'))

# ------------------------------------------------------------------ peças em trânsito e processamento
pecas = []
for k in range(6):
    raiz = bpy.data.objects.new('peca_%d' % k, None)
    sc.collection.objects.link(raiz)
    # corpo base usinado
    bm_p = bmesh.new()
    caixa(bm_p, (0, 0, 0.04), (0.20, 0.18, 0.08))
    # rebaixo usinado no topo
    caixa(bm_p, (0, 0, 0.081), (0.14, 0.12, 0.01))
    corpo = obj('peca_corpo_%d' % k, bm_p, 'peca', raiz)

    # bloco eletrônico adicionado na estação 1
    bm_c = bmesh.new()
    cil(bm_c, Vector((0, 0, 0.045)), 0.04, 0.05, lados=14)
    comp = obj('peca_comp_%d' % k, bm_c, 'cobre', raiz)

    # cordão/gravação a laser adicionado na estação 3
    bm_cd = bmesh.new()
    caixa(bm_cd, (0, 0, 0.082), (0.18, 0.016, 0.006))
    caixa(bm_cd, (0, 0.04, 0.082), (0.12, 0.012, 0.006))
    cordao = obj('peca_cordao_%d' % k, bm_cd, 'cordao', raiz)
    pecas.append((raiz, corpo, comp, cordao))

# ------------------------------------------------------------------ ESTAÇÃO 2: Prensa Eletroidráulica Dupla (Centro: y = 0.0)
bm_pq = bmesh.new()
for x in (-0.46, 0.46):
    caixa_de(bm_pq, (x - 0.07, -0.10, 0.08), (x + 0.07, 0.10, 1.72))
    caixa_de(bm_pq, (x - 0.11, -0.14, 0.08), (x + 0.11, 0.14, 0.15))       # base pesada
caixa_de(bm_pq, (-0.56, -0.14, 1.60), (0.56, 0.14, 1.78))                   # viga superior maciça
caixa_de(bm_pq, (-0.40, -0.12, ZB - 0.22), (0.40, 0.12, ZB - 0.15))         # mesa de suporte inferior
obj('prensa_quadro', bm_pq, 'azul_petroleo')

# colunas de guia cromadas duplas
bm_pguias = bmesh.new()
for x in (-0.32, -0.18, 0.18, 0.32):
    cil(bm_pguias, Vector((x, 0, 1.15)), 0.024, 0.85, lados=16)
obj('prensa_guias', bm_pguias, 'cromo')

# duplo cilindro hidráulico de prensagem no topo
bm_pcil = bmesh.new()
for x in (-0.15, 0.15):
    cil(bm_pcil, Vector((x, 0, 1.95)), 0.09, 0.42, lados=20)
    cil(bm_pcil, Vector((x, 0, 2.16)), 0.105, 0.04, lados=20)
    cil(bm_pcil, Vector((x, 0, 1.75)), 0.105, 0.03, lados=20)
suavizar(obj('prensa_cilindros', bm_pcil, 'grafite'))

# cabeçote móvel da prensa (martelo)
martelo = bpy.data.objects.new('martelo', None)
sc.collection.objects.link(martelo)

bm_mh = bmesh.new()
for x in (-0.15, 0.15):
    cil(bm_mh, Vector((x, 0, 0.38)), 0.042, 0.72, lados=16)
suavizar(obj('martelo_hastes', bm_mh, 'cromo', martelo))

bm_mp = bmesh.new()
caixa(bm_mp, (0, 0, 0.035), (0.72, 0.18, 0.07))
for x in (-0.32, -0.18, 0.18, 0.32):
    cil(bm_mp, Vector((x, 0, 0.035)), 0.042, 0.09, lados=14)
# matriz de corte/estampo
caixa(bm_mp, (0, 0, -0.035), (0.24, 0.16, 0.07))
obj('martelo_placa', bm_mp, 'aco', martelo)

bm_ml = bmesh.new()
caixa(bm_ml, (0, -0.091, 0.035), (0.66, 0.004, 0.05))
obj('martelo_listras', bm_ml, 'listras', martelo)

# travas pneumáticas de alinhamento da peça sob a prensa
TRAVA_Y = -0.22
travas = []
for sx in (-1, 1):
    bm_ts = bmesh.new()
    caixa_de(bm_ts, (sx * 0.32 if sx > 0 else -0.36, TRAVA_Y - 0.05, ZB - 0.12),
                    (sx * 0.36 if sx > 0 else -0.32, TRAVA_Y + 0.05, ZB + 0.06))
    cil(bm_ts, Vector((sx * 0.50, TRAVA_Y, ZB + 0.045)), 0.032, 0.28, Vector((1, 0, 0)), lados=16)
    obj('trava_suporte_%s' % ('dir' if sx > 0 else 'esq'), bm_ts, 'grafite')

    pad = bpy.data.objects.new('trava_%s' % ('dir' if sx > 0 else 'esq'), None)
    sc.collection.objects.link(pad)
    bm_pad = bmesh.new()
    caixa(bm_pad, (sx * 0.01, 0, 0), (0.022, 0.08, 0.05))
    cil(bm_pad, Vector((sx * 0.12, 0, 0)), 0.014, 0.22, Vector((1, 0, 0)), lados=12)
    obj('trava_sapata_%s' % ('dir' if sx > 0 else 'esq'), bm_pad, 'cromo', pad)
    travas.append((pad, sx))

# ------------------------------------------------------------------ ESTAÇÃO 1: Alimentador Rotativo + Robô SCARA de Inserção
MESA = Vector((-0.98, Y_ALIMENTA, 0.08))
bm_mb = bmesh.new()
caixa_de(bm_mb, (MESA.x - 0.22, MESA.y - 0.22, 0.08), (MESA.x + 0.22, MESA.y + 0.22, 0.16))
cil(bm_mb, MESA + Vector((0, 0, 0.30)), 0.08, 0.32, lados=16)
obj('mesa_base', bm_mb, 'grafite')

# prato indexador rotativo
mesa_prato = bpy.data.objects.new('mesa_prato', None)
sc.collection.objects.link(mesa_prato)
mesa_prato.location = MESA + Vector((0, 0, 0.48))

bm_mp = bmesh.new()
cil(bm_mp, Vector((0, 0, 0.0)), 0.26, 0.04, lados=32)
for k in range(6):
    a = k * PI / 3
    cil(bm_mp, Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.022)), 0.048, 0.012, lados=14)
obj('mesa_disco', bm_mp, 'aco', mesa_prato)

# componentes nos ninhos do prato
bm_mc = bmesh.new()
for k in range(6):
    a = k * PI / 3
    cil(bm_mc, Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.05)), 0.038, 0.05, lados=12)
obj('mesa_componentes', bm_mc, 'cobre', mesa_prato)

# Braço robótico articulado SCARA/Antropomórfico (Oeste: alimenta na esteira)
L1, L2, G = 0.48, 0.42, 0.15


def criar_braco(nome, pos, estilo='garra'):
    base_o = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(base_o)
    base_o.location = pos

    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.04)), 0.18, 0.08, lados=16)
    cil(bm, Vector((0, 0, 0.18)), 0.11, 0.20, lados=16)
    caixa(bm, (0.13, -0.08, 0.15), (0.07, 0.06, 0.08))
    obj(nome + '_base', bm, 'grafite', base_o)

    giro = bpy.data.objects.new(nome + '_giro', None)
    sc.collection.objects.link(giro)
    giro.parent = base_o
    giro.location = (0, 0, 0.28)

    bm = bmesh.new()
    caixa(bm, (0, 0, 0.06), (0.24, 0.22, 0.12))
    for x in (-0.08, 0.08):
        caixa(bm, (x, 0, 0.17), (0.035, 0.09, 0.12))
    cil(bm, Vector((-0.16, 0, 0.07)), 0.05, 0.1, Vector((1, 0, 0)), lados=14)
    obj(nome + '_giro_corpo', bm, 'azul_petroleo', giro)

    ombro = bpy.data.objects.new(nome + '_ombro', None)
    sc.collection.objects.link(ombro)
    ombro.parent = giro
    ombro.location = (0, 0, 0.19)

    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.045, 0.13, Vector((1, 0, 0)), lados=14)
    for x in (-0.04, 0.04):
        caixa_de(bm, (x - 0.012, 0.0, -0.025), (x + 0.012, L1, 0.025))
    for k in range(1, 5):
        caixa(bm, (0, L1 * k / 5, 0), (0.07, 0.014, 0.014))
    cil(bm, Vector((0, L1, 0)), 0.05, 0.12, Vector((1, 0, 0)), lados=14)
    obj(nome + '_braco1', bm, 'azul_petroleo', ombro)

    # cabos flexíveis
    bm_c1 = bmesh.new()
    mangueira(bm_c1, bezier((-0.07, -0.02, 0.03), (-0.08, L1 * 0.3, 0.06), (-0.08, L1 * 0.7, 0.06), (-0.06, L1, 0.03), 8), 0.01)
    suavizar(obj(nome + '_cabos1', bm_c1, 'borracha', ombro))

    cotovelo = bpy.data.objects.new(nome + '_cotovelo', None)
    sc.collection.objects.link(cotovelo)
    cotovelo.parent = ombro
    cotovelo.location = (0, L1, 0)

    bm = bmesh.new()
    tubo(bm, (0, 0, 0), (0, L2, 0), 0.032, 14)
    for y in (0.14, 0.28):
        cil(bm, Vector((0, y, 0)), 0.038, 0.02, Vector((0, 1, 0)), lados=14)
    suavizar(obj(nome + '_braco2', bm, 'amarelo', cotovelo))

    punho = bpy.data.objects.new(nome + '_punho', None)
    sc.collection.objects.link(punho)
    punho.parent = cotovelo
    punho.location = (0, L2, 0)

    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), 0.035, 0.08, Vector((1, 0, 0)), lados=14)
    cil(bm, Vector((0, 0, -0.04)), 0.03, 0.05, lados=14)

    dedos = []
    if estilo == 'laser':
        # tocha de laser de alta precisão com bocal focalizador e sensor óptico
        tubo(bm, (0, 0, -0.06), (0, 0.03, -0.12), 0.024, 14)
        curva(bm, (0, 0.03, -0.12), 0.024, 14)
        cil(bm, Vector((0, 0.03, -0.15)), 0.035, 0.04, lados=16)       # anel dissipador
        obj(nome + '_laser_cabeca', bm, 'grafite', punho)
        bm_bico = bmesh.new()
        tubo(bm_bico, (0, 0.03, -0.15), (0, 0.03, -G + 0.005), 0.015, 12)
        suavizar(obj(nome + '_bico', bm_bico, 'cobre', punho))
    else:
        # garra pneumática dupla de componentes
        caixa(bm, (0, 0, -0.08), (0.12, 0.06, 0.04))
        cil(bm, Vector((0, 0.03, -0.08)), 0.014, 0.1, Vector((1, 0, 0)), lados=10)
        obj(nome + '_garra', bm, 'grafite', punho)
        for sx in (-1, 1):
            d = bpy.data.objects.new(nome + '_dedo_%d' % sx, None)
            sc.collection.objects.link(d)
            d.parent = punho
            bm_d = bmesh.new()
            caixa(bm_d, (0, 0, -0.12), (0.016, 0.035, 0.06))
            caixa(bm_d, (-sx * 0.008, 0, -0.15), (0.014, 0.032, 0.012))
            obj(nome + '_dedo_aco_%d' % sx, bm_d, 'aco', d)
            dedos.append((d, sx))

    # pistão telescópico de acionamento do ombro
    bm_cam = bmesh.new()
    cil(bm_cam, Vector((0, 0, 0.11)), 0.026, 0.22, lados=14)
    camisa = suavizar(obj(nome + '_camisa', bm_cam, 'grafite'))
    camisa.rotation_mode = 'QUATERNION'

    bm_has = bmesh.new()
    cil(bm_has, Vector((0, 0, 0.13)), 0.013, 0.26, lados=12)
    haste = suavizar(obj(nome + '_haste', bm_has, 'cromo'))
    haste.rotation_mode = 'QUATERNION'

    return {'base': base_o, 'giro': giro, 'ombro': ombro, 'cotovelo': cotovelo, 'punho': punho,
            'dedos': dedos, 'camisa': camisa, 'haste': haste}


BA = criar_braco('braco_alimenta', Vector((-0.58, -0.92, 0.08)), estilo='garra')
BL = criar_braco('braco_laser', Vector((0.58, 0.22, 0.08)), estilo='laser')
ANCORA, PONTO_B1 = Vector((0, -0.12, 0.12)), Vector((0, 0.24, -0.03))


def resolver_ik(b, ponta):
    pulso = Vector(ponta) + Vector((0, 0, G))
    om = b['base'].location + Vector((0, 0, 0.28 + 0.19))
    d = pulso - om
    th = math.atan2(-d.x, d.y)
    r = math.hypot(d.x, d.y)
    h = d.z
    dist = min(math.hypot(r, h), L1 + L2 - 1e-4)
    c = (dist * dist - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    a2 = -math.acos(max(-1.0, min(1.0, c)))
    a1 = math.atan2(h, r) - math.atan2(L2 * math.sin(a2), L1 + L2 * math.cos(a2))
    b['giro'].rotation_euler = (0, 0, th)
    b['ombro'].rotation_euler = (a1, 0, 0)
    b['cotovelo'].rotation_euler = (a2, 0, 0)
    b['punho'].rotation_euler = (-(a1 + a2), 0, 0)
    bpy.context.view_layer.update()
    pa = b['giro'].matrix_world @ ANCORA
    pb = b['ombro'].matrix_world @ PONTO_B1
    b['camisa'].location = pa
    b['camisa'].rotation_quaternion = (pb - pa).to_track_quat('Z', 'Y')
    b['haste'].location = pb
    b['haste'].rotation_quaternion = (pa - pb).to_track_quat('Z', 'Y')


def inserir_chaves_braco(b, q):
    for k in ('giro', 'ombro', 'cotovelo', 'punho'):
        b[k].keyframe_insert('rotation_euler', frame=q)
    for k in ('camisa', 'haste'):
        b[k].keyframe_insert('location', frame=q)
        b[k].keyframe_insert('rotation_quaternion', frame=q)


# ------------------------------------------------------------------ ESTAÇÃO 3 (Sudeste): Bateria de Gás Inerte (3 Cilindros)
GAS_POS = Vector((1.18, -0.65, 0.08))
bm_gb = bmesh.new()
caixa_de(bm_gb, (GAS_POS.x - 0.16, GAS_POS.y - 0.42, 0.08), (GAS_POS.x + 0.16, GAS_POS.y + 0.42, 0.14))
# correntes/abraçadeiras de retenção
for y in (-0.28, 0.0, 0.28):
    caixa_de(bm_gb, (GAS_POS.x - 0.15, GAS_POS.y + y - 0.12, 0.70), (GAS_POS.x + 0.15, GAS_POS.y + y + 0.12, 0.73))
obj('gas_suporte', bm_gb, 'grafite')

bm_gc = bmesh.new()
for y in (-0.28, 0.0, 0.28):
    p = GAS_POS + Vector((0, y, 0))
    cil(bm_gc, p + Vector((0, 0, 0.58)), 0.11, 0.90, lados=20)
    curva(bm_gc, p + Vector((0, 0, 1.03)), 0.11, 20)
    # válvula e manômetro
    cil(bm_gc, p + Vector((0, 0, 1.18)), 0.028, 0.12, lados=12)
    cil(bm_gc, p + Vector((0, 0, 1.24)), 0.045, 0.02, lados=14)
obj('gas_cilindros', bm_gc, 'verde_gas')

# ------------------------------------------------------------------ 2 SLOTS DE MÓDULOS (Lateral Sudoeste: x = -1.44 m, y = -0.65 m)
# Armário industrial em balanço com duas baias de cartuchos de módulo removíveis
MOD_POS = Vector((-1.44, -0.65, 0.72))
bm_mrack = bmesh.new()
# rack metálico fixado nos pilares
caixa_de(bm_mrack, (MOD_POS.x - 0.04, MOD_POS.y - 0.36, MOD_POS.z - 0.32),
                   (MOD_POS.x + 0.06, MOD_POS.y + 0.36, MOD_POS.z + 0.32))
# aberturas das duas baias
for ym in (-0.16, 0.16):
    caixa_de(bm_mrack, (MOD_POS.x - 0.05, MOD_POS.y + ym - 0.12, MOD_POS.z - 0.26),
                       (MOD_POS.x - 0.03, MOD_POS.y + ym + 0.12, MOD_POS.z + 0.26))
obj('modulo_rack', bm_mrack, 'grafite')

# dois cartuchos de módulo encaixados (azul e dourado com dissipadores)
bm_mods = bmesh.new()
bm_gold = bmesh.new()
bm_leds = bmesh.new()
for idx, ym in enumerate((-0.16, 0.16)):
    p_m = MOD_POS + Vector((-0.02, ym, 0))
    # chassi do cartucho
    caixa_de(bm_mods, (p_m.x - 0.08, p_m.y - 0.10, p_m.z - 0.22),
                      (p_m.x + 0.02, p_m.y + 0.10, p_m.z + 0.22))
    # puxador de alavanca frontal
    tubo(bm_mods, (p_m.x - 0.08, p_m.y - 0.06, p_m.z), (p_m.x - 0.11, p_m.y - 0.06, p_m.z), 0.008, 8)
    tubo(bm_mods, (p_m.x - 0.11, p_m.y - 0.06, p_m.z), (p_m.x - 0.11, p_m.y + 0.06, p_m.z), 0.008, 8)
    tubo(bm_mods, (p_m.x - 0.11, p_m.y + 0.06, p_m.z), (p_m.x - 0.08, p_m.y + 0.06, p_m.z), 0.008, 8)
    # aletas de dissipação de calor
    for k in range(5):
        za = p_m.z - 0.15 + k * 0.07
        caixa_de(bm_mods, (p_m.x - 0.075, p_m.y - 0.09, za), (p_m.x - 0.02, p_m.y + 0.09, za + 0.015))
    # contatos de barramento de alta velocidade em ouro
    caixa_de(bm_gold, (p_m.x + 0.02, p_m.y - 0.08, p_m.z - 0.18), (p_m.x + 0.035, p_m.y + 0.08, p_m.z + 0.18))
    # 4 LEDs por módulo
    for il in range(4):
        zl = p_m.z - 0.12 + il * 0.08
        cil(bm_leds, Vector((p_m.x - 0.082, p_m.y + 0.07, zl)), 0.008, 0.006, Vector((-1, 0, 0)), lados=10)

obj('modulos_corpo', bm_mods, 'azul_petroleo')
obj('modulos_ouro', bm_gold, 'ouro')
obj('modulos_leds', bm_leds, 'ciano')

# ------------------------------------------------------------------ BOCA DE FLUIDO (Oeste: x = -1.44 m, y = 0.0 m, z = 0.35 m)
# Flange padrão para cano de refrigerante com válvula esfera de alavanca vermelha e manômetro
bm_bf = bmesh.new()
bm_bflg = bmesh.new()
# tubo que entra na máquina
tubo(bm_bf, Vector((-1.44, 0.0, 0.35)), Vector((-1.05, 0.0, 0.35)), 0.045, 16)
# flange na face externa
tubo(bm_bflg, Vector((-1.44, 0.0, 0.35)), Vector((-1.42, 0.0, 0.35)), 0.075, 16)
for i in range(4):
    a = i * PI / 2
    cil(bm_bflg, Vector((-1.43, math.cos(a) * 0.06, 0.35 + math.sin(a) * 0.06)), 0.008, 0.018, Vector((-1, 0, 0)), lados=6)
# válvula esfera vermelha
cil(bm_bflg, Vector((-1.22, 0.0, 0.35)), 0.058, 0.08, Vector((1, 0, 0)), lados=14)
cil(bm_bflg, Vector((-1.22, 0.0, 0.42)), 0.016, 0.06, lados=10)
caixa_de(bm_bflg, (-1.24, -0.015, 0.45), (-1.10, 0.015, 0.47))          # alavanca vermelha
# manômetro em cima do tubo
cil(bm_bflg, Vector((-1.12, 0.0, 0.41)), 0.01, 0.04, lados=8)
cil(bm_bflg, Vector((-1.12, 0.0, 0.46)), 0.035, 0.02, Vector((0, 1, 0)), lados=18)
obj('boca_fluido_tubo', bm_bf, 'aco')
obj('boca_fluido_acessorios', bm_bflg, 'laranja')

# ------------------------------------------------------------------ FENÔMENO DA IA: Ressonador Harmônico Quântico de Teto
# Anel toroidal central no teto (z = H + 0.12) com cristal piezoelétrico central emitindo feixe de calibração atômica
bm_res = bmesh.new()
RES_CTR = Vector((0.0, 0.0, H + 0.12))
# suporte em cruzeta no teto
for sx, sy in ((-0.4, 0), (0.4, 0), (0, -0.4), (0, 0.4)):
    tubo(bm_res, RES_CTR, RES_CTR + Vector((sx, sy, -0.12)), 0.02, 12)
# anel de campo harmônico
base3d_toro = None
# construção procedural de toro
R_TORO, r_tubo, seg_u, seg_v = 0.32, 0.035, 24, 12
for u in range(seg_u):
    phi1 = u * 2 * PI / seg_u
    phi2 = (u + 1) * 2 * PI / seg_u
    p1 = RES_CTR + Vector((math.cos(phi1) * R_TORO, math.sin(phi1) * R_TORO, 0))
    p2 = RES_CTR + Vector((math.cos(phi2) * R_TORO, math.sin(phi2) * R_TORO, 0))
    tubo(bm_res, p1, p2, r_tubo, seg_v)
# 4 bobinas magnéticas no anel
for i in range(4):
    a = i * PI / 2
    pb = RES_CTR + Vector((math.cos(a) * R_TORO, math.sin(a) * R_TORO, 0))
    cil(bm_res, pb, 0.055, 0.08, Vector((math.sin(a), -math.cos(a), 0)), lados=14)
obj('ressonador_anel', bm_res, 'cobre')

# cristal quântico focalizador (animado em escala/pulso)
o_cristal = bpy.data.objects.new('cristal_ia', None)
sc.collection.objects.link(o_cristal)
o_cristal.location = RES_CTR + Vector((0, 0, -0.05))

bm_cr = bmesh.new()
# bico de foco e octaedro de cristal
cil(bm_cr, Vector((0, 0, 0.04)), 0.06, 0.08, lados=16)
# octaedro
bmesh.ops.create_icosphere(bm_cr, subdivisions=1, radius=0.075)
obj('cristal_ia_malha', bm_cr, 'cristal', o_cristal)

# feixe de calibração sutil em direção à esteira
bm_feixe = bmesh.new()
tubo(bm_feixe, Vector((0, 0, 0)), Vector((0, 0, -(H - ZB + 0.15))), 0.008, 8)
o_feixe = obj('feixe_reticulo', bm_feixe, 'laser', o_cristal)

# ------------------------------------------------------------------ SISTEMA DE EXAUSTÃO NO TETO (Ciclone + Dutos)
bm_ex = bmesh.new()
EX_POS = Vector((0.85, 0.85, H + 0.02))
# coifa sobre a solda a laser
coifa_pos = Vector((0.35, Y_LASER, H - 0.05))
cil(bm_ex, coifa_pos, 0.22, 0.12, lados=20)
# duto espiral da coifa até o exaustor
cano(bm_ex, bm_ex, [coifa_pos + Vector((0, 0, 0.06)), coifa_pos + Vector((0, 0, 0.22)),
                    EX_POS + Vector((-0.2, -0.2, 0.22)), EX_POS + Vector((0, 0, 0.22))], 0.045)
# caracol centrífugo do exaustor
cil(bm_ex, EX_POS + Vector((0, 0, 0.24)), 0.18, 0.18, Vector((0, 0, 1)), lados=24)
cil(bm_ex, EX_POS + Vector((0, 0, 0.24)), 0.11, 0.22, Vector((1, 0, 0)), lados=16)   # motor aletado
# chaminé de descarga vertical com chapéu chinês
tubo(bm_ex, EX_POS + Vector((0.14, 0.0, 0.30)), EX_POS + Vector((0.14, 0.0, 0.75)), 0.05, 16)
cil(bm_ex, EX_POS + Vector((0.14, 0.0, 0.78)), 0.09, 0.04, lados=16)                  # chapéu
obj('sistema_exaustao', bm_ex, 'grafite')

# ------------------------------------------------------------------ UNIDADE HIDRÁULICA (Nordeste) e COMPRESSOR DUPLO (Noroeste)
UH = Vector((1.05, 1.05, 0.08))
bm_uh = bmesh.new()
caixa_de(bm_uh, UH + Vector((-0.30, -0.24, 0)), UH + Vector((0.30, 0.24, 0.45)))
cil(bm_uh, UH + Vector((0.0, 0.0, 0.58)), 0.11, 0.26, Vector((1, 0, 0)), lados=18)
for k in range(7):
    cil(bm_uh, UH + Vector((-0.09 + k * 0.03, 0, 0.58)), 0.128, 0.008, Vector((1, 0, 0)), lados=18)
cil(bm_uh, UH + Vector((-0.18, 0.0, 0.58)), 0.07, 0.12, Vector((1, 0, 0)), lados=16)
caixa(bm_uh, UH + Vector((0.0, 0.0, 0.46)), (0.32, 0.18, 0.04))
obj('uh_tanque_motor', bm_uh, 'azul_petroleo')

# compressor com cilindros em V no noroeste
CP = Vector((-1.05, 1.05, 0.08))
bm_cp = bmesh.new()
cil(bm_cp, CP + Vector((0, 0, 0.22)), 0.18, 0.64, Vector((0, 1, 0)), lados=24)
for y in (-0.32, 0.32):
    curva(bm_cp, CP + Vector((0, y, 0.22)), 0.18, 24)
# cabeçote em V
for a_deg in (-30, 30):
    rad = math.radians(a_deg)
    cil(bm_cp, CP + Vector((math.sin(rad) * 0.12, 0.08, 0.48 + math.cos(rad) * 0.12)), 0.065, 0.14,
        Vector((math.sin(rad), 0, math.cos(rad))), lados=14)
obj('compressor_v', bm_cp, 'cinza')

# tubulações rígidas hidráulicas com flanges até a prensa central
bm_can, bm_cflg = bmesh.new(), bmesh.new()
for k, zk in ((0, 2.05), (1, 1.90)):
    x = 1.25 + 0.08 * k
    cano(bm_can, bm_cflg, [Vector((x, 0.95, 0.52)), Vector((x, 0.95, zk)), Vector((x, 0.22, zk)),
                           Vector((0.15, 0.22, zk)), Vector((0.15, 0.08, zk))], 0.022)
suavizar(obj('canos_prensa', bm_can, 'aco'))
suavizar(obj('canos_prensa_flanges', bm_cflg, 'grafite'))

# calhas duplas de cabo no teto e fiação espessa
bm_calha, bm_cabo = bmesh.new(), bmesh.new()
for x in (-0.92, 0.92):
    caixa_de(bm_calha, (x - 0.09, -1.38, H - 0.14), (x + 0.09, 1.38, H - 0.13))
    for sx in (-1, 1):
        caixa_de(bm_calha, (x + sx * 0.09 - 0.006, -1.38, H - 0.14), (x + sx * 0.09 + 0.006, 1.38, H - 0.07))
    for k in range(3):
        mangueira(bm_cabo, [Vector((x - 0.05 + k * 0.05, -1.36, H - 0.11)),
                            Vector((x - 0.05 + k * 0.05, 1.36, H - 0.11))], 0.010)
obj('calhas_teto', bm_calha, 'grafite')
suavizar(obj('cabos_teto', bm_cabo, 'borracha'))

# ------------------------------------------------------------------ PAINEL IHM DA IA, GIROFLEX E SINALIZADORES
PN = Vector((-1.22, -1.47, 0))
bm_pn = bmesh.new()
caixa_de(bm_pn, (-1.32, PN.y - 0.02, 0.52), (-0.96, PN.y + 0.03, 1.35))
caixa_de(bm_pn, (-1.16, PN.y - 0.01, 0.08), (-1.12, PN.y + 0.02, 0.52))    # pedestal
obj('painel_corpo', bm_pn, 'azul_petroleo')

bm_pnf = bmesh.new()
caixa_de(bm_pnf, (-1.28, PN.y - 0.024, 0.95), (-1.00, PN.y - 0.02, 1.25)) # tela principal
cil(bm_pnf, Vector((-1.06, PN.y - 0.03, 0.78)), 0.035, 0.02, Vector((0, -1, 0)), lados=16) # emergência
for i in range(3):
    cil(bm_pnf, Vector((-1.24 + i * 0.08, PN.y - 0.026, 0.65)), 0.016, 0.012, Vector((0, -1, 0)), lados=10)
obj('painel_detalhes', bm_pnf, 'grafite')

# giroflex no topo da prensa
bm_gfb = bmesh.new()
cil(bm_gfb, Vector((0.38, 0.0, 1.80)), 0.065, 0.03, lados=16)
obj('giroflex_base', bm_gfb, 'grafite')

bm_gf = bmesh.new()
cil(bm_gf, Vector((0.38, 0.0, 1.84)), 0.055, 0.08, lados=16)
o_giroflex = obj('giroflex_lente', bm_gf, 'ambar')

# torre de sinalização no alimentador
for i, (nome, z) in enumerate((('verde', 0.58), ('ambar', 0.64), ('vermelho', 0.70))):
    bmm = bmesh.new()
    cil(bmm, MESA + Vector((0, -0.32, z)), 0.032, 0.05, lados=14)
    obj('sinal_%s' % nome, bmm, nome)

# ------------------------------------------------------------------ EFEITOS: Faíscas de Solda e Fumaça
faiscas = []
vel_f = []
for k in range(16):
    bm_f = bmesh.new()
    bmesh.ops.create_icosphere(bm_f, subdivisions=1, radius=0.008)
    o = obj('EFEITO_faisca_%d' % k, bm_f, 'faisca')
    faiscas.append(o)
    a = random.uniform(0, 2 * PI)
    elev = random.uniform(0.3, 1.2)
    v = random.uniform(0.8, 2.2)
    vel_f.append(Vector((math.cos(a) * math.cos(elev) * v, math.sin(a) * math.cos(elev) * v, math.sin(elev) * v)))

fumacas = []
for k in range(6):
    bm_fm = bmesh.new()
    bmesh.ops.create_icosphere(bm_fm, subdivisions=1, radius=0.08)
    o = obj('EFEITO_fumaca_%d' % k, bm_fm, 'fumaca')
    fumacas.append(o)

# lâmpada pontual intensa na tocha de laser/plasma
luz_laser = bpy.data.lights.new('LuzLaser', 'POINT')
luz_laser.color = (0.2, 0.7, 1.0)
luz_laser.energy = 0.0
o_luz_laser = bpy.data.objects.new('EFEITO_LuzLaser', luz_laser)
sc.collection.objects.link(o_luz_laser)


# ------------------------------------------------------------------ ANIMAÇÃO (96 quadros em laço)
def pulso_tri(t, dur):
    t = t % 1.0
    return (t / (dur / 2)) if t < dur / 2 else (2.0 - t / (dur / 2)) if t < dur else 0.0


# cinemática e interpolação dos 96 quadros
for q in range(1, QUADROS + 1):
    sc.frame_set(q)
    u_ciclo = (q - 1) / QUADROS                 # 0 .. 1
    t_seg = (q - 1) / FPS                       # 0 .. 4 s

    # 1. Movimento da esteira e taliscas: avanço contínuo
    for i, tal in enumerate(taliscas):
        pos_y = -1.48 + ((i / 12.0 + u_ciclo * 2.0) % 1.0) * 2.96
        tal.location = (0, pos_y, ZB)
        tal.keyframe_insert('location', frame=q)

    # 2. Peças na esteira: deslocamento constante e estados sucessivos
    for k, (raiz, corpo, comp, cordao) in enumerate(pecas):
        prog = (k / 6.0 + u_ciclo * 2.0) % 1.0
        y_p = -1.48 + prog * 2.96
        raiz.location = (0, y_p, ZB)
        raiz.keyframe_insert('location', frame=q)

        # componente aparece após passar pela estação 1 (y > Y_ALIMENTA)
        comp.hide_render = y_p < Y_ALIMENTA
        comp.keyframe_insert('hide_render', frame=q)

        # cordão a laser aparece após passar pela estação 3 (y > Y_LASER)
        cordao.hide_render = y_p < Y_LASER
        cordao.keyframe_insert('hide_render', frame=q)

    # 3. Rotação do prato alimentador
    mesa_prato.rotation_euler = (0, 0, u_ciclo * 4 * PI)
    mesa_prato.keyframe_insert('rotation_euler', frame=q)

    # 4. Braço SCARA 1 (alimentador): ciclo de 2 segundos (48 quadros)
    u_sub = (q - 1) % 48 / 48.0
    if u_sub < 0.35:
        # vai até a mesa giratória
        w = u_sub / 0.35
        p_alvo = MESA + Vector((0.18 * math.cos(u_sub * 4), 0.18 * math.sin(u_sub * 4), 0.52))
    elif u_sub < 0.50:
        # desce para pegar
        p_alvo = MESA + Vector((0.18, 0.0, 0.49))
    elif u_sub < 0.85:
        # transporta até a peça na esteira (x = 0, y = Y_ALIMENTA, z = ZB + 0.08)
        w = (u_sub - 0.50) / 0.35
        p_alvo = Vector(((-0.8) * (1 - w), Y_ALIMENTA, 0.52 + 0.12 * math.sin(w * PI)))
    else:
        # posiciona e solta
        p_alvo = Vector((0.0, Y_ALIMENTA, ZB + 0.06))
    resolver_ik(BA, p_alvo)
    inserir_chaves_braco(BA, q)

    # 5. Prensa: ciclo rítmico (desce rápida, estampa em t = 0.5 e sobe)
    desce_prensa = pulso_tri(u_ciclo * 2.0, 0.45)
    martelo.location = (0, 0, 1.05 - 0.38 * desce_prensa)
    martelo.keyframe_insert('location', frame=q)

    # travas laterais fecham sincronizadas com o impacto da prensa
    for pad, sx in travas:
        pad.location = (sx * (0.24 - 0.10 * desce_prensa), TRAVA_Y, ZB + 0.045)
        pad.keyframe_insert('location', frame=q)

    # 6. Braço Laser (Estação 3): oscilação sobre o cordão na peça
    u_laser = (u_ciclo * 4.0) % 1.0
    soldando = 0.2 < u_laser < 0.8
    p_laser = Vector((0.06 * math.sin(u_laser * 2 * PI), Y_LASER + 0.03 * math.cos(u_laser * 2 * PI), ZB + 0.07))
    resolver_ik(BL, p_laser)
    inserir_chaves_braco(BL, q)

    # faíscas da solda e luz do plasma
    o_luz_laser.location = p_laser + Vector((0, 0, 0.04))
    luz_laser.energy = (25.0 + random.uniform(-8.0, 8.0)) if soldando else 0.0
    o_luz_laser.keyframe_insert('location', frame=q)
    luz_laser.keyframe_insert('energy', frame=q)

    for k, o in enumerate(faiscas):
        tt = ((k / len(faiscas) + u_ciclo * 6) % 1.0) * 0.32
        o.location = p_laser + vel_f[k] * tt + Vector((0, 0, -4.9 * tt * tt))
        o.hide_render = not soldando
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('hide_render', frame=q)

    # fumaça subindo até a coifa
    for k, o in enumerate(fumacas):
        uf = (k / len(fumacas) + u_ciclo * 3) % 1.0
        o.location = Vector((0.08 * math.sin(k + uf * 4), Y_LASER + 0.05 * math.cos(k), ZB + 0.10 + 0.9 * uf))
        s = 0.04 + 0.16 * uf
        o.scale = (s, s, s)
        o.hide_render = not soldando and uf < 0.1
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
        o.keyframe_insert('hide_render', frame=q)

    # 7. Fenômeno Quântico da IA: pulso de ressonância no cristal
    pulso_q = 1.0 + 0.15 * math.sin(u_ciclo * 8 * PI)
    o_cristal.scale = (pulso_q, pulso_q, pulso_q)
    o_cristal.keyframe_insert('scale', frame=q)


# ------------------------------------------------------------------ CÂMERAS, ILUMINAÇÃO E MODOS
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.5), (14, 14, 1.0))
obj('chao', bm_chao, 'chao')

sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(45), 0, math.radians(-35))

mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.6

sc.render.engine = 'CYCLES'
sc.cycles.device = 'GPU'
try:
    pr = bpy.context.preferences.addons['cycles'].preferences
    pr.compute_device_type = 'OPTIX'
    pr.get_devices()
    for dv in pr.devices:
        dv.use = True
except Exception:
    sc.cycles.device = 'CPU'

sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.35

cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 0.75)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'

if modo in ('foto', 'perto'):
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1300, 1100
    if modo == 'foto':
        sc.frame_set(int(QUADROS * 0.15) + 1)
        for i, (ang, alt) in enumerate(((300, 4.6), (215, 4.4), (120, 4.8), (35, 4.2))):
            a = math.radians(ang)
            mirar(Vector(ALVO) + Vector((math.cos(a) * 4.6, math.sin(a) * 4.6, alt)), ALVO, 30)
            sc.render.filepath = os.path.join(AQUI, 'montadora_2_%d.png' % i)
            bpy.ops.render.render(write_still=True)
    sc.frame_set(int(QUADROS * 0.25))
    # close-up por cima entre as vigas do pórtico (sem grade na frente)
    mirar((0.95, -1.25, 2.45), (-0.15, -0.15, 0.72), 28)
    sc.render.filepath = os.path.join(AQUI, 'montadora_2_perto.png')
    bpy.ops.render.render(write_still=True)

elif modo == 'video':
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    a = math.radians(300)
    mirar(Vector(ALVO) + Vector((math.cos(a) * 6.0, math.sin(a) * 6.0, 3.2)), ALVO, 34)
    if hasattr(sc.render.image_settings, 'media_type'):
        sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = os.path.join(AQUI, 'montadora_2_video.mp4')
    bpy.ops.render.render(animation=True)

# Cálculo de triângulos para informação no console
total_tris = sum(len(o.data.polygons) * 2 for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO') and not o.name == 'chao')
print('MONTADORA 2 ok — tris aproximados: %d' % total_tris)
