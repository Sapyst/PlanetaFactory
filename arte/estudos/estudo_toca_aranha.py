"""Estudo isolado (fora do jogo): TOCA DAS ARANHAS, 3×3 tiles (substitui o ninho de sucata; pedido de Sapyst:
"coberta de teias enroladas").
- Monte de terra calcinada e sucata meio enterrada (diâmetro ~2,5 m, altura ~1,9 m), dentro de [-1.44, 1.44] m.
- Entrada da toca ao sul (−Y): túnel escuro aberto no monte, com o brilho carmesim da incubação lá no fundo.
- Teia em funil na boca (como a das aranhas de toca): a seda afunila do monte e do chão para dentro do buraco.
- Teias enroladas: faixas largas e fios finos de seda dando voltas no monte, assentados na superfície (raio contra
  a malha: nada atravessa nada), sem cobrir a entrada.
- Casulos enrolados presos no monte; fios esticados do alto do monte até pedras-âncora no chão; fios no chão.
- Animação em laço de 96 quadros (4 s a 24 fps): núcleo carmesim pulsando ('nucleo_bioplasma') e dois casulos
  se mexendo ('casulo_vivo_0', 'casulo_vivo_1').

Uso: blender -b --python estudo_toca_aranha.py -- foto
     blender -b --python estudo_toca_aranha.py -- nada     (monta a cena e a animação, sem render: para_jogo.py)
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, cil, viga, pedra

PI = math.pi
FPS = 24
QUADROS = 96
random.seed(31)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def luz_mat(nome, cor, forca=10.0):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


base3d.M.update({
    'terra_toca': mats.material('TerraToca', (0.045, 0.037, 0.032), 0.0, 0.97, pintura=False, sujeira=0.9, desgaste=0.3),
    'tunel_toca': mats.material('TunelToca', (0.03, 0.02, 0.018), 0.0, 1.0, pintura=False, sujeira=0.8, desgaste=0.0),
    'sucata_toca': mats.material('SucataToca', (0.13, 0.12, 0.12), 0.7, 0.7, pintura=False, sujeira=0.95, ferrugem=0.6),
    'seda': mats.material('SedaTeia', (0.66, 0.64, 0.60), 0.0, 0.62, pintura=False, sujeira=0.45, desgaste=0.2),
    'seda_velha': mats.material('SedaVelha', (0.36, 0.33, 0.29), 0.0, 0.75, pintura=False, sujeira=0.85, desgaste=0.2),
    'pedra_toca': mats.material('PedraToca', (0.16, 0.15, 0.14), 0.0, 0.9, pintura=False, sujeira=0.7),
    'bioplasma_carmesim': luz_mat('BioplasmaIncubacao', (1.0, 0.02, 0.04), 4.0),
    'chao': mats.material('ChaoToca', (0.20, 0.19, 0.18), 0.0, 0.92, sujeira=0.6),
})

# ------------------------------------------------------------------ véu de teia: textura de fios (opaco) e buracos (transparente)
def textura_teia(lado=512, fios=150, seed=7):
    import numpy as np
    rng = np.random.default_rng(seed)
    alfa = np.zeros((lado, lado), dtype=np.float32)
    for _ in range(fios):                                  # fios longos levemente curvos, atravessando a fita
        x0, y0 = rng.uniform(0, lado, 2)
        ang = rng.uniform(0, np.pi) if rng.random() < 0.6 else rng.normal(np.pi / 2, 0.25)
        curva = rng.uniform(-0.002, 0.002)
        forca = rng.uniform(0.45, 1.0)
        for t in np.arange(-lado, lado, 0.7):
            a = ang + curva * t
            x, y = int(x0 + t * np.cos(a)) % lado, int(y0 + t * np.sin(a)) % lado
            alfa[y, x] = max(alfa[y, x], forca)
    for _ in range(14):                                    # manchas de seda emaranhada (mais fechadas)
        cx, cy, r = rng.uniform(0, lado), rng.uniform(0, lado), rng.uniform(18, 60)
        yy, xx = np.mgrid[0:lado, 0:lado]
        d = np.sqrt(((xx - cx + lado / 2) % lado - lado / 2) ** 2 + ((yy - cy + lado / 2) % lado - lado / 2) ** 2)
        alfa = np.maximum(alfa, np.clip(1 - d / r, 0, 1) ** 1.5 * 0.55 * (rng.random((lado, lado)) > 0.45))
    img = bpy.data.images.new('TexTeia', lado, lado, alpha=True)
    px = np.zeros((lado, lado, 4), dtype=np.float32)
    tom = 0.75 + 0.12 * rng.random((lado, lado))
    px[..., 0], px[..., 1], px[..., 2] = tom * 0.80, tom * 0.78, tom * 0.73
    px[..., 3] = alfa
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def material_veu(nome, img, escurece=1.0):
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = img
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (escurece, escurece * 0.97, escurece * 0.92, 1)
    nt.links.new(tx.outputs['Color'], mx.inputs['A'])
    nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    nt.links.new(tx.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = 0.6
    if hasattr(m, 'surface_render_method'):
        m.surface_render_method = 'DITHERED'
    if hasattr(m, 'blend_method'):
        m.blend_method = 'CLIP'
    m.use_backface_culling = False
    return m


_tex_teia = textura_teia()
base3d.M['veu'] = material_veu('VeuTeia', _tex_teia, 0.95)
base3d.M['veu_sujo'] = material_veu('VeuTeiaSujo', _tex_teia, 0.62)

ENTRADA_Z = 0.56          # centro da boca do túnel (a aranha passa: corpo de 1 m)
ENTRADA_R = 0.50          # raio da boca
CENTRO = Vector((0.0, 0.0, 0.62))

# ================================================================== 1. MONTE DE TERRA (forma com ruído, base plana)
bm_monte = bmesh.new()
bmesh.ops.create_uvsphere(bm_monte, u_segments=40, v_segments=20, radius=1.0)
for v in bm_monte.verts:
    d = v.co.normalized()
    ruido = noise.noise(d * 2.3 + Vector((3.1, 1.7, 0.4))) * 0.10 + noise.noise(d * 6.0) * 0.035
    r_xy = 1.22 * (1 + ruido)
    v.co = Vector((d.x * r_xy, d.y * r_xy, max(d.z, -0.02) * 1.9 * (1 + ruido)))
    if d.z < 0:
        v.co.z = -0.02                                    # fundo fecha no chão (fica escondido)
o_monte = obj('toca_monte', bm_monte, 'terra_toca')
for p in o_monte.data.polygons:
    p.use_smooth = True
bvh_monte = BVHTree.FromObject(o_monte, bpy.context.evaluated_depsgraph_get())   # antes do furo: para assentar as teias

# túnel: o cortador (cilindro fechado) deixa as paredes e o fundo do buraco com o material dele
bm_c = bmesh.new()
cil(bm_c, (0, 0, 0), ENTRADA_R * 0.7, 1.0, lados=22, r2=ENTRADA_R)  # afunila para dentro (topo do cone = boca, fora)
bmesh.ops.subdivide_edges(bm_c, edges=[e for e in bm_c.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5], cuts=6)
for vv in bm_c.verts:                                     # parede de terra irregular, não um cano
    r = Vector((vv.co.x, vv.co.y, 0)).length
    if r > 0.05:
        k = 1 + 0.16 * noise.noise(vv.co * 5.0 + Vector((2.0, 0.5, 1.0))) + 0.06 * noise.noise(vv.co * 13.0)
        vv.co.x *= k
        vv.co.y *= k
o_corte = obj('toca_cortador', bm_c, 'tunel_toca')
o_corte.matrix_world = Matrix.Translation((0.0, -1.10, ENTRADA_Z)) @ Matrix.Rotation(PI / 2, 4, 'X')
o_corte.data.transform(Matrix.Translation((0, 0, 0)))
bool_m = o_monte.modifiers.new('furo', 'BOOLEAN')
bool_m.operation = 'DIFFERENCE'
bool_m.object = o_corte
if hasattr(bool_m, 'material_mode'):
    bool_m.material_mode = 'TRANSFER'
bpy.context.view_layer.objects.active = o_monte
bpy.ops.object.modifier_apply(modifier='furo')
bpy.data.objects.remove(o_corte)
FUNDO_Y = -1.10 + 0.5                                     # fundo do túnel (onde o cortador acaba)


def superficie(d, extra=0.0):
    """Ponto da superfície do monte na direção d (a partir do centro) e a normal ali; None se não acerta."""
    d = d.normalized()
    hit = bvh_monte.ray_cast(CENTRO + d * 4.0, -d)
    if hit[0] is None:
        return None, None
    return hit[0] + hit[1] * extra, hit[1]


def na_entrada(p, folga=0.0):
    """Perto da boca (oval em volta do furo, de frente para o sul): ali a teia é o funil, não as voltas."""
    if p.y > -0.5:
        return False
    rx, rz = 0.78 + folga, 0.72 + folga
    return (p.x / rx) ** 2 + ((p.z - ENTRADA_Z) / rz) ** 2 < 1.0


def fita(bm, pts, normais, largura, offset, escala_u=0.6, varia=0.4):
    """Fita de seda assentada: segue os pontos, de face para fora (normal da superfície), afastada `offset`.
    UV: u ao longo (1 = escala_u metros), v de um lado ao outro (para o véu com textura de fios)."""
    if len(pts) < 2:
        return
    uv = bm.loops.layers.uv.verify()
    vs, us, acc = [], [], 0.0
    for i, (p, n) in enumerate(zip(pts, normais)):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        lado = t.cross(n).normalized() * (largura * 0.5 * (1 - varia + varia * math.sin(i * 0.9 + largura * 50)))
        base = p + n * offset
        if i:
            acc += (pts[i] - pts[i - 1]).length
        vs.append((bm.verts.new(base - lado), bm.verts.new(base + lado)))
        us.append(acc / escala_u)
    for i, ((a0, a1), (b0, b1)) in enumerate(zip(vs, vs[1:])):
        f = bm.faces.new((a0, b0, b1, a1))
        for lp, c in zip(f.loops, ((us[i], 0), (us[i + 1], 0), (us[i + 1], 1), (us[i], 1))):
            lp[uv].uv = c


# ================================================================== 2. SUCATA MEIO ENTERRADA (a toca é de fábrica)
bm_suc = bmesh.new()
for k, (ang, h) in enumerate(((35, 0.55), (150, 0.35), (215, 0.75), (320, 0.45))):
    d = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), h - 0.42))
    p, n = superficie(d)
    if p is None or na_entrada(p, 0.2):
        continue
    eixo = (n + Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), 0.5))).normalized()
    viga(bm_suc, p - eixo * 0.25, p + eixo * random.uniform(0.18, 0.32), random.uniform(0.07, 0.1))
obj('toca_sucata', bm_suc, 'sucata_toca')

# ================================================================== 3. TEIA EM FUNIL NA BOCA
bm_funil = bmesh.new()
ANEIS, LADOS = 6, 24
grade = []
for j in range(ANEIS):
    u = j / (ANEIS - 1)
    anel = []
    for i in range(LADOS):
        a = 2 * PI * i / LADOS
        r = ENTRADA_R * 0.72 + (1.05 - ENTRADA_R * 0.72) * u ** 1.5 * (0.9 + 0.35 * noise.noise(Vector((a * 1.7, 0.3, 0))))
        x, z = r * math.cos(a), max(ENTRADA_Z + r * math.sin(a), 0.012)
        hit = bvh_monte.ray_cast(Vector((x, -3.0, z)), Vector((0, 1, 0)))      # monte antes do furo: a borda inteira
        y_sup = hit[0].y if hit[0] is not None else -1.25
        if z <= 0.013:
            y_sup = min(y_sup, -1.25) - 0.25 * (1 - abs(math.cos(a)))      # embaixo: a seda deita no chão
        borda = ENTRADA_R * 0.84                           # dentro disso é sempre buraco (a boca varia ±16%)
        y = y_sup - 0.025 - 0.02 * math.sin(u * PI) + max(0.0, borda - r) * 2.5   # cobre a borda e afunda no buraco
        anel.append(bm_funil.verts.new(Vector((x, y, z))))
    grade.append(anel)
uv_f = bm_funil.loops.layers.uv.verify()
for j in range(ANEIS - 1):
    for i in range(LADOS):
        k = (i + 1) % LADOS
        f = bm_funil.faces.new((grade[j][i], grade[j][k], grade[j + 1][k], grade[j + 1][i]))
        for lp, c in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
            lp[uv_f].uv = (c[0] / 9.0, c[1] / 3.5)
o_funil = obj('toca_funil', bm_funil, 'veu')
o_funil2 = o_funil.copy()                                 # segunda camada, girada: o funil fica denso
o_funil2.data = o_funil.data.copy()
sc.collection.objects.link(o_funil2)
o_funil2.name = 'toca_funil_2'
for lp_uv in o_funil2.data.uv_layers.active.data:
    lp_uv.uv = (lp_uv.uv.x * 1.3 + 0.37, lp_uv.uv.y * 1.2 + 0.21)
o_funil2.data.transform(Matrix.Translation((0, -0.012, 0)))
for p in o_funil.data.polygons:
    p.use_smooth = True

# ================================================================== 4. TEIAS ENROLADAS NO MONTE (véus e fios)
def volta(bm, eixo_z, inclina, largura, offset, escala_u=0.6, varia=0.4, fase=0.0, amostras=110):
    """Uma volta de seda em torno do monte, assentada na superfície, interrompida na boca da toca e no chão."""
    eixo = eixo_z.normalized()
    u = eixo.cross(Vector((0, 0, 1)) if abs(eixo.z) < 0.99 else Vector((1, 0, 0))).normalized()
    v = eixo.cross(u)
    pts, nrm = [], []
    for s_ in range(amostras):
        t = 2 * PI * s_ / (amostras - 1) + fase
        d = (u * math.cos(t) + v * math.sin(t)) + eixo * inclina
        p, n = superficie(d) if d.z >= -0.62 else (None, None)
        if p is None or na_entrada(p, 0.05):
            fita(bm, pts, nrm, largura, offset, escala_u, varia)
            pts, nrm = [], []
            continue
        pts.append(p)
        nrm.append(n)
    fita(bm, pts, nrm, largura, offset, escala_u, varia)


bm_veu = bmesh.new()
bm_veu_s = bmesh.new()
for k in range(12):                                       # véus: faixas largas de rede, em camadas, meio soltas
    eixo = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.5, 2.4)))
    volta(bm_veu if k % 3 else bm_veu_s, eixo, random.uniform(-0.3, 0.5), random.uniform(0.28, 0.5),
          0.02 + 0.012 * (k % 4), 0.9, 0.25, random.uniform(0, PI), 44)
o_veu = obj('toca_veu', bm_veu, 'veu')
o_veu_s = obj('toca_veu_sujo', bm_veu_s, 'veu_sujo')
bm_fios = bmesh.new()
for k in range(52):                                       # fios finos dando voltas (uns colados, uns soltos)
    eixo = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.4, 2.6)))
    volta(bm_fios, eixo, random.uniform(-0.35, 0.6), random.uniform(0.006, 0.012), random.uniform(0.008, 0.07),
          1.0, 0.3, random.uniform(0, 2 * PI))
obj('toca_fios_enrolados', bm_fios, 'seda')

# ================================================================== 5. CASULOS ENROLADOS
def casulo(nome, p, n, comp, raio, voltas=7):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=1.0)
    for vv in bm.verts:
        vv.co = Vector((vv.co.x * raio, vv.co.y * raio, vv.co.z * comp * 0.5)) * (1 + 0.08 * noise.noise(vv.co * 5))
    # fita em espiral enrolando o casulo
    pts, nrm = [], []
    for s in range(60):
        t = s / 59
        a = t * voltas * 2 * PI
        z = (t - 0.5) * comp * 0.9
        rr = raio * math.sqrt(max(0.0, 1 - (2 * z / comp) ** 2)) + 0.004
        pts.append(Vector((rr * math.cos(a), rr * math.sin(a), z)))
        nrm.append(Vector((math.cos(a), math.sin(a), 0)))
    fita(bm, pts, nrm, 0.012, 0.004)
    o = obj(nome, bm, 'seda_velha')
    for pg in o.data.polygons:
        pg.use_smooth = True
    # deitado na superfície, comprido ao longo da encosta
    lado = n.cross(Vector((0, 0, 1)))
    if lado.length < 1e-3:
        lado = Vector((1, 0, 0))
    lado.normalize()
    desce = lado.cross(n).normalized()
    rot = Matrix((lado, n, desce)).transposed()          # x = lado, y = normal, z = ao longo da encosta
    o.matrix_world = Matrix.Translation(p + n * (raio * 0.85)) @ rot.to_4x4()
    return o


vivos = []
for k, (ang, h, comp, raio) in enumerate(((60, 0.65, 0.42, 0.11), (130, 0.25, 0.36, 0.10), (200, 0.55, 0.46, 0.12),
                                          (12, 0.2, 0.32, 0.09), (285, 0.75, 0.38, 0.10))):
    d = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), h - 0.42))
    p, n = superficie(d)
    if p is None or na_entrada(p, 0.15):
        continue
    o = casulo('casulo_vivo_%d' % len(vivos) if k in (0, 2) else 'toca_casulo_%d' % k, p, n, comp, raio)
    if k in (0, 2):
        vivos.append(o)

# ================================================================== 6. FIOS ESTICADOS ATÉ PEDRAS-ÂNCORA E FIOS NO CHÃO
bm_ped = bmesh.new()
bm_fio = bmesh.new()
for k, ang in enumerate((20, 75, 120, 165, 205, 335, 250, 300)):
    a = math.radians(ang + random.uniform(-6, 6))
    r_anc = 1.36 if ang % 90 not in range(30, 61) else 1.6
    ancora = Vector((math.cos(a) * r_anc, math.sin(a) * r_anc, 0.0))
    if na_entrada(ancora, 0.3):
        continue
    pedra(bm_ped, (ancora.x, ancora.y, 0.05), random.uniform(0.07, 0.1), achatar=0.6)
    for alt in (0.95, 0.7):
        ini, n_ini = superficie(Vector((math.cos(a), math.sin(a), alt - 0.42)), 0.012)
        if ini is None:
            continue
        fim = ancora + Vector((0, 0, 0.1))
        # o fio não pode entrar no monte: confere a reta contra a malha
        meio = bvh_monte.ray_cast(ini + n_ini * 0.01, (fim - ini).normalized(), (fim - ini).length)
        if meio[0] is not None:
            continue
        pts = [ini.lerp(fim, t) + Vector((0, 0, -0.04 * math.sin(t * PI))) for t in (i / 12 for i in range(13))]
        lado = (fim - ini).cross(Vector((0, 0, 1))).normalized()
        nrm = [lado.cross((fim - ini).normalized()) for _ in pts]
        fita(bm_fio, pts, nrm, 0.012, 0.0)
# fios deitados no chão, saindo da base
for k in range(16):
    a = 2 * PI * k / 16 + random.uniform(-0.1, 0.1)
    p0, _ = superficie(Vector((math.cos(a), math.sin(a), -0.38)))
    if p0 is None or na_entrada(p0, 0.25):
        continue
    r1 = random.uniform(1.3, 1.42)
    fim = Vector((math.cos(a + 0.05) * r1, math.sin(a + 0.05) * r1, 0.004))
    pts = [Vector((p0.x, p0.y, 0.004)).lerp(fim, t / 8) for t in range(9)]
    fita(bm_fio, pts, [Vector((0, 0, 1))] * len(pts), 0.016, 0.0)
obj('toca_ancoras', bm_ped, 'pedra_toca')
obj('toca_fios', bm_fio, 'seda')

# ================================================================== 7. NÚCLEO CARMESIM NO FUNDO DO TÚNEL
bm_nuc = bmesh.new()
bmesh.ops.create_icosphere(bm_nuc, subdivisions=2, radius=0.08)
o_nuc = obj('nucleo_bioplasma', bm_nuc, 'bioplasma_carmesim')
o_nuc.location = (0.0, FUNDO_Y - 0.12, ENTRADA_Z - 0.06)
luz_d = bpy.data.lights.new('luz_toca', 'POINT')
luz_d.color = (1.0, 0.05, 0.05)
luz_d.energy = 6
luz_d.shadow_soft_size = 0.2
luz_o = bpy.data.objects.new('luz_toca', luz_d)
sc.collection.objects.link(luz_o)
luz_o.location = (0.0, FUNDO_Y - 0.3, ENTRADA_Z)

# tudo dentro dos 3×3 tiles (±1,44 m): a seda que deita no chão e as pontas dos fios param na borda
for o in sc.objects:
    if o.type == 'MESH' and not o.name.startswith('EFEITO'):
        mw, mi = o.matrix_world, o.matrix_world.inverted()
        for v in o.data.vertices:
            w = mw @ v.co
            if abs(w.x) > 1.44 or abs(w.y) > 1.44:
                w.x, w.y = max(-1.44, min(1.44, w.x)), max(-1.44, min(1.44, w.y))
                v.co = mi @ w

# ================================================================== 8. ANIMAÇÃO (laço de 4 s)
for q in range(1, QUADROS + 1):
    u = (q - 1) / QUADROS
    s = 1.0 + 0.12 * math.sin(2 * PI * u * 2)
    o_nuc.scale = (s, s, s)
    o_nuc.keyframe_insert('scale', frame=q)
    luz_d.energy = 6 * (0.75 + 0.25 * math.sin(2 * PI * u * 2))
    luz_d.keyframe_insert('energy', frame=q)
    for i, o in enumerate(vivos):
        f = math.sin(2 * PI * u * (1 + i)) * math.exp(-((u * 4 + i * 1.7) % 4 - 1.0) ** 2 * 3)
        o.rotation_mode = 'XYZ'
        if q == 1:
            o['rot0'] = list(o.rotation_euler)
        r0 = o['rot0']
        o.rotation_euler = (r0[0] + 0.06 * f, r0[1] + 0.04 * f, r0[2])
        o.keyframe_insert('rotation_euler', frame=q)
        sz = 1.0 + 0.05 * abs(f)
        o.scale = (sz, 1.0, 1.0 + 0.03 * f)
        o.keyframe_insert('scale', frame=q)
for o in [o_nuc] + vivos:
    if o.animation_data and o.animation_data.action:
        for fc in getattr(o.animation_data.action, 'fcurves', []) or []:
            fc.modifiers.new('CYCLES')

# ------------------------------------------------------------------ CENA, ILUMINAÇÃO E CÂMERAS
bm_chao = bmesh.new()
caixa(bm_chao, (0, 0, -0.05), (14, 14, 0.10))
obj('EFEITO_chao', bm_chao, 'chao')

sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.2
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-38))
sol2 = bpy.data.lights.new('Sol2', 'SUN')
sol2.energy = 1.6
so2 = bpy.data.objects.new('Sol2', sol2)
sc.collection.objects.link(so2)
so2.rotation_euler = (math.radians(-32), 0, math.radians(140))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.45, 0.48, 0.58, 1)
bg.inputs['Strength'].default_value = 0.65

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
sc.view_settings.exposure = -0.30

cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, -0.1, 0.8)
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
tris = sum(len(o.data.polygons) for o in sc.objects if o.type == 'MESH' and not o.name.startswith('EFEITO'))
print(f'TOCA_ARANHA tris={tris}')

if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    for i, (ang, alt, f_num) in enumerate(((270, 2.6, 24), (200, 3.0, 15), (40, 3.4, 60), (115, 2.7, 84))):
        sc.frame_set(f_num)
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 4.0, math.sin(a) * 4.0, alt - ALVO[2])), ALVO, 35)
        sc.render.filepath = os.path.join(AQUI, f'toca_aranha_{i}.png')
        bpy.ops.render.render(write_still=True)
    sc.frame_set(24)
    mirar((0.3, -2.8, 0.95), (0.0, -0.9, 0.58), 40)
    sc.render.filepath = os.path.join(AQUI, 'toca_aranha_perto.png')
    bpy.ops.render.render(write_still=True)
    print('TOCA_ARANHA ok')
