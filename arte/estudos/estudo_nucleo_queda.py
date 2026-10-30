"""Estudo isolado: a CHEGADA do núcleo (abertura do jogo). Usa exatamente o modelo de estudo_nucleo.py (a mesma
construção é executada aqui) e anima uma linha do tempo de 10 s (240 quadros a 24 qps) que termina na pose final:
  1–60    queda: cápsula fechada (pétalas recolhidas formando a saia ablativa + ogiva por cima, tudo em brasa),
          envolta em fogo de reentrada, com rastro de fumaça
  60–75   impacto: poeira sobe, cratera, rachaduras e queimado aparecem, terra e pedras são ejetadas
  80–100  a ogiva é ejetada (cargas pirotécnicas) e sai voando
  95–150  os pistões empurram as pétalas para fora até cravarem no chão (terra amontoa nas pontas)
  128–170 cabos-raiz descem e entram na terra; tampas das bocas recolhem
  165–195 esteiras curtas saem das gargantas
  165–205 o monólito sobe e começa a flutuar; os anéis se abrem e passam a girar; fragmentos saem do cristal
  200–240 tudo entra no laço do estado final (calor, arcos, minério nas esteiras); no quadro 240 a pose é a do
          estado final de estudo_nucleo.py (quadro 1 do laço)
Uso: blender -b --python estudo_nucleo_queda.py -- foto"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion

_AQUI = os.path.dirname(os.path.abspath(__file__))
_fonte = open(os.path.join(_AQUI, 'estudo_nucleo.py'), encoding='utf-8').read()
_i_anim = _fonte.index('# ------------------------------------------------------------------ animação')
_i_cena = _fonte.index('# ------------------------------------------------------------------ cena')
_i_modo = _fonte.index("modo = sys.argv")
exec(compile(_fonte[:_i_anim] + _fonte[_i_cena:_i_modo], 'estudo_nucleo.py', 'exec'), globals())

TOTAL = 240
sc.frame_start, sc.frame_end = 1, TOTAL
Q_IMPACTO = 60


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def faixa(q, q0, q1):
    return suave((q - q0) / (q1 - q0))


def fogo_mat(nome, forca):
    """Labareda em volume: absorve (não fica pálida sob o sol) e emite forte; densidade com ruído."""
    m = base3d.volume_mat(nome, (1.0, 0.4, 0.05), 3.0, -100.0, 100.0)
    nt = m.node_tree
    vol = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    mul = next(n for n in nt.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY')
    em = mats.no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    em.inputs[1].default_value = forca
    nt.links.new(mul.outputs['Value'], em.inputs[0])
    nt.links.new(em.outputs['Value'], vol.inputs['Emission Strength'])
    vol.inputs['Color'].default_value = (0.04, 0.015, 0.005, 1)
    vol.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1)
    return m


base3d.M.update({
    'fogo': fogo_mat('Fogo', 60.0),
    'rastro': base3d.volume_mat('Rastro', (0.05, 0.045, 0.04), 2.2, -100.0, 100.0),
    'poeira': base3d.volume_mat('Poeira', (0.36, 0.28, 0.2), 7.0, 0.0, 3.0),
    'ogiva': mats.material('Ogiva', (0.07, 0.06, 0.055), 0, 0.85, desgaste=1.0, sujeira=1.0),
})

# ------------------------------------------------------------------ peças só da chegada: ogiva e tampas das bocas
mundo_nomes = {'cratera', 'torroes', 'pedras', 'rachaduras', 'queimado_chao', 'chao', 'Cam', 'Sol'}
capsula = bpy.data.objects.new('capsula', None)
sc.collection.objects.link(capsula)
for o in list(sc.objects):
    if o.parent is None and o is not capsula and o.name not in mundo_nomes:
        o.parent = capsula

Z_OGIVA, R_OGIVA, TOPO_OGIVA = 0.7, 1.32, 2.75
ogiva = bpy.data.objects.new('ogiva', None)
sc.collection.objects.link(ogiva)
ogiva.parent = capsula
ogiva.location = (0, 0, Z_OGIVA)
ogiva.rotation_mode = 'XYZ'
bm = bmesh.new()
cil(bm, Vector((0, 0, (TOPO_OGIVA - Z_OGIVA) / 2)), R_OGIVA, TOPO_OGIVA - Z_OGIVA, lados=40, r2=0.12)
cil(bm, Vector((0, 0, TOPO_OGIVA - Z_OGIVA + 0.03)), 0.12, 0.06, lados=20, r2=0.06)
suavizar(obj('ogiva_casca', bm, 'ogiva', ogiva))
bm = bmesh.new()
toro(bm, Vector((0, 0, 0.02)), R_OGIVA - 0.01, 0.035, 72, 12)                         # anel de separação
for k in range(16):                                                                   # parafusos explosivos
    a = k * 2 * PI / 16
    cil(bm, d_de(a) * (R_OGIVA + 0.02) + Vector((0, 0, 0.02)), 0.018, 0.05, d_de(a), lados=8)
for h in (0.45, 0.95, 1.45):                                                          # cintas de reforço
    t = h / (TOPO_OGIVA - Z_OGIVA)
    toro(bm, Vector((0, 0, h)), R_OGIVA + (0.12 - R_OGIVA) * t + 0.004, 0.012, 72, 8)
suavizar(obj('ogiva_aneis', bm, 'aco', ogiva))
bm = bmesh.new()
for k in range(14):                                                                   # escorridos de queimado
    a = random.uniform(0, 2 * PI)
    h0 = random.uniform(0.05, 0.6)
    pts = []
    for i in range(8):
        h = h0 + (1.5 - h0) * i / 7
        r = R_OGIVA + (0.12 - R_OGIVA) * h / (TOPO_OGIVA - Z_OGIVA) + 0.006
        pts.append(d_de(a + 0.02 * math.sin(i)) * r + Vector((0, 0, h)))
    vs = []
    for i, p in enumerate(pts):
        lado = Vector((0, 0, 1)).cross(d_de(a)).normalized() * random.uniform(0.03, 0.07) * (1 - i / 9)
        vs.append((bm.verts.new(p + lado), bm.verts.new(p - lado)))
    for (a0, a1), (b0, b1) in zip(vs, vs[1:]):
        bm.faces.new((a0, a1, b1, b0))
obj('ogiva_queimado', bm, 'fuligem', ogiva)

tampas = []
for a in BOCAS:                                                                       # tampas das gargantas
    rot = Matrix.Rotation(a, 3, 'Z')
    gc = d_de(a) * (R_CORPO + 0.07) + Vector((0, 0, 0.3))
    bm = bmesh.new()
    caixa(bm, Vector((0, 0, 0)), (0.02, 0.4, 0.3), rot)
    for j in (-1, 1):
        caixa(bm, rot @ Vector((0.012, j * 0.12, 0)), (0.008, 0.03, 0.26), rot)       # nervuras
    o = obj('tampa_boca', bm, 'casco', capsula)
    o.location = gc + rot @ Vector((0.09, 0, 0))
    tampas.append((o, o.location.copy()))

# conjuntos por boca (esteira, correia, listras): recolhidos dentro do corpo durante a queda
esteiras = []
for o in sc.objects:
    if o.name.split('.')[0] in ('esteira', 'correia', 'esteira_listras') and o.type == 'MESH':
        c = sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
        esteiras.append((o, Vector((c.x, c.y, 0)).normalized()))

# cabos-raiz crescem a partir do centro do corpo
CENTRO_CABOS = Vector((0, 0, 0.4))
cabos = [bpy.data.objects[n] for n in ('cabos_raiz', 'cabos_abracadeiras')]
for o in cabos:
    o.data.transform(Matrix.Translation(-CENTRO_CABOS))
    o.location = CENTRO_CABOS
terra_cabos = bpy.data.objects['cabos_terra']
terras_petala = [o for o in sc.objects if o.name.split('.')[0] == 'petala_terra']

# mundo: cratera e ejetados (escala a partir do centro)
cratera = [bpy.data.objects[n] for n in ('cratera', 'rachaduras', 'queimado_chao')]
ejetados = [bpy.data.objects[n] for n in ('torroes', 'pedras')]

# fogo de reentrada (envolve a cápsula e rasga para trás) e rastro de fumaça
fogos = []
for k in range(3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    o = obj('fogo', bm, 'fogo')
    o.rotation_mode = 'QUATERNION'
    fogos.append(o)
rastros = []
for k in range(16):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    rastros.append(obj('rastro', bm, 'rastro'))
poeiras = []
for k in range(12):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    poeiras.append(obj('poeira', bm, 'poeira'))
vel_poeira = [(random.uniform(0, 2 * PI), random.uniform(0.9, 1.6), random.uniform(0.3, 1.0)) for _ in poeiras]

# trajetória da queda: vem do alto, inclinada, acelerando
P0 = Vector((-9.0, 7.0, 38.0))


def pos_queda(q):
    u = min(max((q - 1) / (Q_IMPACTO - 1), 0.0), 1.0)
    return P0.lerp(Vector((0, 0, 0)), u ** 1.6)


DIR_QUEDA = (Vector((0, 0, 0)) - P0).normalized()

# pétalas: fechadas (inclinadas para cima, formando a saia) → abertas (pose final)
BETA_FECHADA = math.radians(-58)


def brasa(mat, eixo, v0, v1):
    """Brasa de reentrada: forte na face de ataque (coordenada `eixo` do objeto perto de v0) e sumindo até v1,
    manchada por ruído. Devolve o nó Valor (intensidade) que a linha do tempo anima."""
    nt = mat.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1.0, 0.3, 0.05, 1)
    tc = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    gr = no(nt, 'ShaderNodeMapRange', **{'From Min': v0, 'From Max': v1, 'To Min': 1.0, 'To Max': 0.0})
    nt.links.new(sep.outputs[eixo], gr.inputs['Value'])
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 7.0, 'Detail': 6.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.65, 'To Min': 0.25, 'To Max': 1.0})
    nt.links.new(ru.outputs['Fac'], mr.inputs['Value'])
    m1 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(gr.outputs['Result'], m1.inputs[0])
    nt.links.new(mr.outputs['Result'], m1.inputs[1])
    val = no(nt, 'ShaderNodeValue')
    m2 = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(m1.outputs['Value'], m2.inputs[0])
    nt.links.new(val.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs['Value'], b.inputs['Emission Strength'])
    return val


brasa_petala = brasa(base3d.M['ablativo'], 'X', 0.0, 0.7)      # dobradiça (embaixo, na queda) mais quente
brasa_ogiva = brasa(base3d.M['ogiva'], 'Z', 0.0, 1.3)            # borda de baixo da ogiva mais quente


def pose_laco(q):
    """Fração do laço do estado final: no quadro 240 vale 0 (quadro 1 do laço de estudo_nucleo.py)."""
    return ((q - TOTAL) / QUADROS) % 1.0


def anel_laco(i, fr):
    if i == 0:
        return Quaternion((0, 0, 1), -4 * PI * fr) @ Quaternion((1, 0, 0), math.radians(12))
    if i == 1:
        return Quaternion((0, 0, 1), PI / 4) @ Quaternion((1, 0, 0), 2 * PI * fr)
    return Quaternion((0, 0, 1), 2 * PI * fr) @ Quaternion((0, 1, 0), math.radians(24)) @ Quaternion((0, 0, 1), -2 * PI * fr)


def chave(o, *canais, q):
    for c in canais:
        o.keyframe_insert(c, frame=q)


def mostrar(o, vis, q):
    o.hide_render = not vis
    o.hide_viewport = not vis
    chave(o, 'hide_render', 'hide_viewport', q=q)


cristal_em = base3d.M['cristal'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
fresta_em = base3d.M['fresta'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for q in range(1, TOTAL + 1):
    fr = pose_laco(q)
    # ---- cápsula: queda e assentamento
    p = pos_queda(q)
    capsula.location = p
    incl = 1.0 - faixa(q, 50, Q_IMPACTO)
    capsula.rotation_mode = 'QUATERNION'
    capsula.rotation_quaternion = Quaternion((0, 0, 1), 0).slerp(Vector((0, 0, -1)).rotation_difference(DIR_QUEDA), incl * 0.35)
    if Q_IMPACTO <= q < Q_IMPACTO + 8:                                   # tranco do impacto
        capsula.location.z = -0.05 * math.sin(PI * (q - Q_IMPACTO) / 8)
    chave(capsula, 'location', 'rotation_quaternion', q=q)
    # ---- brasa da reentrada nas placas ablativas e na ogiva
    calor = 1.0 - faixa(q, Q_IMPACTO - 4, Q_IMPACTO + 30)
    for val, f in ((brasa_petala, 6.0), (brasa_ogiva, 3.2)):
        val.outputs[0].default_value = f * calor * (0.85 + 0.15 * math.sin(q * 1.7))
        val.outputs[0].keyframe_insert('default_value', frame=q)
    # ---- fogo envolvendo e rasgando para trás (oposto ao movimento)
    for k, o in enumerate(fogos):
        vis = q < Q_IMPACTO
        mostrar(o, vis, q)
        if vis:
            tras = -DIR_QUEDA
            o.location = p + tras * (2.2 + 1.6 * k) + Vector((0, 0, 0.2))
            o.rotation_quaternion = tras.to_track_quat('Z', 'Y')
            l = 1.0 + 0.12 * math.sin(q * 2.3 + k)
            o.scale = (1.05 - 0.2 * k, 1.05 - 0.2 * k, (1.6 + 1.0 * k) * l)
            chave(o, 'location', 'rotation_quaternion', 'scale', q=q)
    # ---- rastro de fumaça: cada baforada nasce num ponto da trajetória e fica para trás, crescendo
    for k, o in enumerate(rastros):
        nasc = 1 + k * (Q_IMPACTO - 4) / len(rastros)
        vis = nasc <= q < Q_IMPACTO + 50
        mostrar(o, vis, q)
        if vis:
            idade = (q - nasc) / 24
            o.location = pos_queda(nasc) - DIR_QUEDA * 5.5 + Vector((0.4 * idade, 0.3 * idade, 0.5 * idade))
            o.scale = [1.0 + 1.8 * idade] * 3
            chave(o, 'location', 'scale', q=q)
    # ---- impacto: cratera aparece, terra e pedras voam, poeira sobe
    u = faixa(q, Q_IMPACTO, Q_IMPACTO + 8)
    for o in cratera:
        mostrar(o, q >= Q_IMPACTO, q)
        o.scale = (max(u, 0.05), max(u, 0.05), 1)
        chave(o, 'scale', q=q)
    v = faixa(q, Q_IMPACTO, Q_IMPACTO + 14)
    for o in ejetados:
        mostrar(o, q >= Q_IMPACTO, q)
        o.scale = (0.3 + 0.7 * v, 0.3 + 0.7 * v, 1)
        o.location = (0, 0, 0.9 * math.sin(PI * v))
        chave(o, 'scale', 'location', q=q)
    for k, o in enumerate(poeiras):
        vis = Q_IMPACTO <= q < Q_IMPACTO + 52                       # sobe, afina (densidade cai com a altura) e some
        mostrar(o, vis, q)
        if vis:
            a, vr, vz = vel_poeira[k]
            t = (q - Q_IMPACTO) / 24
            o.location = d_de(a) * (1.0 + 1.6 * vr * (1 - math.exp(-2.0 * t))) + Vector((0, 0, 0.3 + vz * t * 1.6))
            o.scale = [0.5 + 0.9 * (1 - math.exp(-1.5 * t))] * 3
            chave(o, 'location', 'scale', q=q)
    # ---- ogiva ejetada
    e = faixa(q, 80, 100)
    ogiva.location = Vector((0, 0, Z_OGIVA)) + Vector((2.2 * e, -1.4 * e, 5.0 * e - 1.2 * e * e))
    ogiva.rotation_euler = (0.9 * e, -1.6 * e, 0.4 * e)
    chave(ogiva, 'location', 'rotation_euler', q=q)
    mostrar(ogiva, q < 100, q)
    for c in ogiva.children:
        mostrar(c, q < 100, q)
    # ---- pétalas abrem; terra amontoa na ponta quando cravam
    ab = faixa(q, 95, 150)
    for ip, pt in enumerate(petalas):
        if q >= 200:
            ang = -math.radians(0.9) * (0.5 + 0.5 * math.sin(2 * PI * fr + ip * PI / 2))
            beta = -ang
        else:
            beta = BETA_FECHADA * (1 - ab)
        pt['pv'].rotation_quaternion = Quaternion((0, 0, 1), pt['a']) @ Quaternion((0, 1, 0), beta)
        chave(pt['pv'], 'rotation_quaternion', q=q)
    for o in terras_petala:
        mostrar(o, q >= 146, q)
        o.scale = [max(faixa(q, 146, 158), 0.05)] * 3
        chave(o, 'scale', q=q)
    bpy.context.view_layer.update()
    # pistões: camisa no olhal do corpo, haste no suporte da pétala; telescópicos quando a pétala está recolhida
    for ps in pistoes:
        pv = ps['pet']['pv']
        m = Matrix.Translation(pv.location) @ pv.rotation_quaternion.to_matrix().to_4x4()
        ponta = m @ ps['pet']['sup'][ps['k']]
        dv = ponta - ps['anc']
        d = dv.normalized()
        enc = min(1.0, dv.length / 0.62)
        ps['camisa'].location = ps['anc']
        ps['camisa'].rotation_quaternion = d.to_track_quat('Z', 'Y')
        ps['camisa'].scale = (1, 1, enc)
        ps['haste'].location = ponta
        ps['haste'].rotation_quaternion = (-d).to_track_quat('Z', 'Y')
        ps['haste'].scale = (1, 1, enc)
        for o in (ps['camisa'], ps['haste']):
            chave(o, 'location', 'rotation_quaternion', 'scale', q=q)
    # ---- cabos-raiz descem e entram na terra
    c = faixa(q, 128, 170)
    for o in cabos:
        mostrar(o, q >= 128, q)
        o.scale = [0.3 + 0.7 * c] * 3
        chave(o, 'scale', q=q)
    mostrar(terra_cabos, q >= 164, q)
    terra_cabos.scale = [max(faixa(q, 164, 176), 0.05)] * 3
    chave(terra_cabos, 'scale', q=q)
    # ---- tampas das bocas sobem para dentro do teto e somem; esteiras saem das gargantas
    t = faixa(q, 150, 166)
    for o, base_l in tampas:
        o.location = base_l + Vector((0, 0, 0.32 * t))
        chave(o, 'location', q=q)
        mostrar(o, q < 167, q)
    s = faixa(q, 165, 195)
    for o, d in esteiras:
        o.location = -d * 0.75 * (1 - s)
        chave(o, 'location', q=q)
    # ---- monólito sobe e passa a flutuar; anéis se abrem; fragmentos saem do cristal
    sobe = faixa(q, 165, 200)
    pulso = 0.5 + 0.5 * math.sin(2 * PI * 2 * fr) ** 2
    acende = faixa(q, 150, 200)
    flut = Vector((0, 0, 0.04 * math.sin(2 * PI * fr)))
    monolito.location = Vector((0, 0, 0.62 + (CM.z - 0.62) * sobe)) + flut * sobe   # guardado dentro da coluna
    monolito.rotation_euler = (0, 0, 2 * PI * fr * sobe)
    monolito.scale = [1 + 0.03 * pulso * acende] * 3
    chave(monolito, 'location', 'rotation_euler', 'scale', q=q)
    cristal_em.default_value = 0.15 + (0.8 + 2.2 * pulso) * acende
    cristal_em.keyframe_insert('default_value', frame=q)
    fresta_em.default_value = 0.4 + 5.6 * faixa(q, 100, 190)
    fresta_em.keyframe_insert('default_value', frame=q)
    luz_m.energy = (40 + 90 * pulso) * acende
    luz_m.keyframe_insert('energy', frame=q)
    abre = faixa(q, 172, 205)
    for i, o in enumerate(aneis):
        fechado = Vector((0, 0, 1.15 + 0.05 * (2 - i)))
        o.location = fechado.lerp(CM, abre)
        o.rotation_quaternion = Quaternion().slerp(anel_laco(i, fr), abre)
        chave(o, 'location', 'rotation_quaternion', q=q)
    sai = faixa(q, 196, 222)
    for o, a0, r, z, vel, fase in fragmentos:
        mostrar(o, q >= 196, q)
        a = a0 + vel * 2 * PI * fr
        final = Vector((math.cos(a) * r, math.sin(a) * r, z + 0.05 * math.sin(2 * PI * fr + fase)))
        o.location = monolito.location.lerp(final, sai)
        o.rotation_euler = (fase + 2 * PI * fr, fase * 0.5, 4 * PI * fr)
        chave(o, 'location', 'rotation_euler', q=q)
    # ---- arcos, calor e minério só no laço final
    for o, ig, vv in arcos:
        janela = (fr * 4 + ig * 0.37) % 1.0
        mostrar(o, q >= 214 and janela < 0.22 and int(janela / 0.075) == vv, q)
    for k, o in enumerate(calores):
        mostrar(o, q >= 200, q)
        cc = RESPIROS[k % 4]
        u2 = ((k // 4) / 2 + fr * 2 + k * 0.11) % 1.0
        o.location = cc + Vector((0.04 * math.sin(k + u2 * 6), 0.04 * math.cos(k + u2 * 5), 0.55 * u2 + 0.03))
        o.scale = [0.05 + 0.13 * u2] * 3
        chave(o, 'location', 'scale', q=q)
    for o, a, k in itens_esteira:
        mostrar(o, q >= 200, q)
        u3 = (k / 3 + fr) % 1.0
        o.location = d_de(a) * (1.45 - u3 * (1.45 - 0.5)) + Vector((0, 0, Z_ESTEIRA + 0.035))
        o.rotation_euler = (0, 0, k * 2.0)
        chave(o, 'location', q=q)

# ------------------------------------------------------------------ fotos dos momentos-chave
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
if modo == 'foto':
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1200
    momentos = [
        ('queda', 40, lambda: mirar(pos_queda(40) + Vector((9.5, 12.0, -1.5)), pos_queda(40) + Vector((-2.0, 1.6, 4.0)), 34)),
        ('impacto', 67, lambda: mirar(Vector((4.6, -5.6, 2.6)), Vector((0, 0, 0.8)), 30)),
        ('abrindo', 122, lambda: mirar(Vector((3.3, -3.6, 2.4)), Vector((0, 0, 0.7)), 32)),
        ('emergindo', 188, lambda: mirar(Vector((3.3, -3.6, 2.5)), Vector((0, 0, 1.05)), 32)),
        ('final', 240, lambda: mirar(Vector(ALVO) + Vector((math.cos(math.radians(300)) * 4.7, math.sin(math.radians(300)) * 4.7, 2.6)), ALVO, 33)),
    ]
    for nome, quadro, camera in momentos:
        sc.frame_set(quadro)
        camera()
        sc.render.filepath = os.path.join(AQUI, 'nucleo_queda_%s.png' % nome)
        bpy.ops.render.render(write_still=True)
print('NUCLEO QUEDA ok')
