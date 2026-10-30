"""Estudo isolado (fora do jogo): esteira detalhada e suas variações — reta (2 tiles), curva (90°) e rampa (sobe
0,5 m em 1 tile). Leito de placas de metal com nervuras que andam de verdade; laterais em perfil U com faixa de
listras de perigo; catracas (rodas dentadas) nas pontas; no meio, motor na lateral com pinhão, coroa e corrente de
rolos animada; pés com sapatas. Materiais físicos (mats.py). Renderiza um vídeo (48 quadros, laço perfeito) e uma
foto de perto.
Uso: blender -b --python estudo_esteira.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats

PI = math.pi
H = 0.20            # topo do leito
W = 0.60            # largura das placas
PASSO = 0.10        # uma placa a cada 10 cm
VEL = 0.5           # m/s
QUADROS = 48        # 2 s a 24 qps: anda 1,0 m = 10 placas (laço perfeito)
FPS = 24

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def listras_mat():
    m = bpy.data.materials.new('Listras')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'DIAGONAL'
    wave.wave_profile = 'SAW'
    wave.inputs['Scale'].default_value = 7.0
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    corte = nt.nodes.new('ShaderNodeMath')
    corte.operation = 'GREATER_THAN'
    corte.inputs[1].default_value = 0.5
    nt.links.new(wave.outputs['Fac'], corte.inputs[0])
    sujo = nt.nodes.new('ShaderNodeTexNoise')
    sujo.inputs['Scale'].default_value = 14.0
    nt.links.new(tc.outputs['Object'], sujo.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (0.03, 0.03, 0.03, 1)
    mix.inputs[7].default_value = (0.62, 0.42, 0.04, 1)
    nt.links.new(corte.outputs['Value'], mix.inputs[0])
    gasto = nt.nodes.new('ShaderNodeMix')
    gasto.data_type = 'RGBA'
    gasto.blend_type = 'MULTIPLY'
    gasto.inputs[0].default_value = 0.45
    nt.links.new(mix.outputs[2], gasto.inputs[6])
    nt.links.new(sujo.outputs['Color'], gasto.inputs[7])
    nt.links.new(gasto.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    return m


M = {
    'placa': mats.material('Placa', (0.40, 0.41, 0.42), 1.0, 0.5, pintura=False, ferrugem=0.85, sujeira=0.9, escovado=True),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.5),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.8, sujeira=0.7),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.025), 0, 0.85, sujeira=0.2, desgaste=0.0),
    'chao': mats.material('Chão', (0.26, 0.25, 0.23), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'listras': listras_mat(),
}


# ------------------------------------------------------------------ geometria
def obj(nome, bm, mat, pai=None):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nome, me)
    sc.collection.objects.link(o)
    o.data.materials.append(M[mat])
    if pai is not None:
        o.parent = pai
    return o


def caixa(bm, centro, tam, rot=Matrix.Identity(3)):
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res['verts']:
        v.co = Vector(centro) + rot @ Vector((v.co.x * tam[0], v.co.y * tam[1], v.co.z * tam[2]))
    return res['verts']


def cil(bm, centro, r, h, eixo=Vector((0, 0, 1)), lados=12):
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=r, radius2=r, depth=h, matrix=Matrix.Translation(centro) @ q)


def catraca(nome, centro, eixo, r, dentes, esp, mat, pai):
    """Roda dentada: disco + dentes trapezoidais + cubo."""
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0)), r * 0.82, esp, Vector((0, 0, 1)), lados=dentes * 2)
    for k in range(dentes):
        a = k * 2 * PI / dentes
        rot = Matrix.Rotation(a, 3, 'Z')
        caixa(bm, rot @ Vector((r * 0.9, 0, 0)), (r * 0.26, r * 0.22, esp * 0.9), rot)
    cil(bm, Vector((0, 0, 0)), r * 0.3, esp * 1.6, lados=8)
    o = obj(nome, bm, mat, pai)
    q = Vector(eixo).normalized().to_track_quat('Z', 'Y')
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = q
    o.location = centro
    return o


# ------------------------------------------------------------------ caminhos (posição e direção no comprimento s)
def caminho_reta(L):
    return L, lambda s: (Vector((s - L / 2, 0, H)), Vector((1, 0, 0))), 0.0


def caminho_curva(R=0.5):
    L = R * PI / 2
    c = Vector((-0.5, 0.5, 0))
    def f(s):
        a = -PI / 2 + s / R
        return Vector((c.x + R * math.cos(a), c.y + R * math.sin(a), H)), Vector((-math.sin(a), math.cos(a), 0))
    return L, f, 1.0 / R


def caminho_rampa(sobe=0.5):
    L = math.hypot(1.0, sobe)
    def f(s):
        t = s / L
        return Vector((t - 0.5, 0, H + sobe * t)), Vector((1.0, 0, sobe)).normalized()
    return L, f, 0.0


RHO = 0.066         # raio da volta das placas em torno do eixo das catracas (por fora dos dentes)
FOLGA = 0.014       # folga entre placas: a mesma em toda a largura, na reta e na curva


def varrer(bm, f, L, n, perfil):
    """Perfil fechado [(lado, cima), ...] varrido ao longo do caminho: malha contínua (sem degraus na curva)."""
    aneis = []
    for i in range(n + 1):
        p, d = f(L * i / n)
        m = base(d)
        aneis.append([bm.verts.new(p + m @ Vector((0, y, z))) for y, z in perfil])
    k = len(perfil)
    for i in range(n):
        a, b = aneis[i], aneis[i + 1]
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])


def ret(y0, y1, z0, z1):
    return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]


def placa_trapezio(bm, passo, curv, y0, y1, z0, z1):
    """Placa (ou nervura) cujo comprimento ao longo do caminho em cada lado é passo×(1 − curv·y) − FOLGA:
    na curva vira trapézio e a folga para a vizinha fica igual em toda a largura."""
    vs = []
    for z in (z0, z1):
        for y, sx in ((y0, -1), (y0, 1), (y1, 1), (y1, -1)):
            hx = (passo * (1.0 - curv * y) - FOLGA) / 2.0
            vs.append(bm.verts.new(Vector((sx * hx, y, z))))
    b0, b1 = vs[:4], vs[4:]
    bm.faces.new(list(reversed(b0)))
    bm.faces.new(b1)
    for j in range(4):
        bm.faces.new((b0[j], b0[(j + 1) % 4], b1[(j + 1) % 4], b1[j]))


def base(dirc):
    """Base ortonormal: frente (dirc), lado (para a esquerda), cima."""
    lado = Vector((0, 0, 1)).cross(dirc).normalized()
    cima = dirc.cross(lado).normalized()
    return Matrix((dirc, lado, cima)).transposed()


def esteira(nome, caminho, origem):
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    raiz.location = origem
    L, f, curv = caminho
    n_seg = max(8, int(L / 0.03))
    # laterais: perfil U contínuo (alma + abas) com faixa listrada por fora; leito de retorno embaixo
    for lado_s in (-1, 1):
        y = lado_s * (W / 2 + 0.03)
        bm, bl = bmesh.new(), bmesh.new()
        varrer(bm, f, L, n_seg, ret(y - 0.009, y + 0.009, -0.105, 0.015))                         # alma
        for z in (0.006, -0.106):
            varrer(bm, f, L, n_seg, ret(min(y, y - lado_s * 0.045), max(y, y - lado_s * 0.045), z, z + 0.012))   # abas
        yf = y + lado_s * 0.0105
        varrer(bl, f, L, n_seg, ret(yf - 0.0015, yf + 0.0015, -0.065, -0.015))                    # faixa listrada
        obj(nome + '_lateral', bm, 'grafite', raiz)
        obj(nome + '_faixa', bl, 'listras', raiz)
    # cavaletes: a cada ~0,5 m e nas pontas — pernas do chão até a aba de baixo, travessa sob o retorno,
    # mão-francesa diagonal e sapata aparafusada; na rampa as pernas crescem com a altura
    bm = bmesh.new()
    n_cav = max(2, int(round(L / 0.5)) + 1)
    for i in range(n_cav):
        s_c = 0.07 + (L - 0.14) * i / (n_cav - 1)
        p, d = f(s_c)
        m = base(d)
        dh = Vector((d.x, d.y, 0)).normalized()                  # pernas sempre em pé, alinhadas no plano
        mh = base(dh)
        pes = []
        for lado_s in (-1, 1):
            topo = p + m @ Vector((0, lado_s * (W / 2 + 0.03), -0.112))
            pes.append(topo)
            caixa(bm, Vector((topo.x, topo.y, topo.z / 2)), (0.04, 0.04, topo.z), mh)              # perna
            caixa(bm, Vector((topo.x, topo.y, 0.008)), (0.1, 0.09, 0.016), mh)                     # sapata
            for dx in (-0.032, 0.032):
                cil(bm, Vector((topo.x, topo.y, 0.02)) + mh @ Vector((dx, 0, 0)), 0.008, 0.012, lados=6)   # parafusos
        a0, a1 = pes
        zt = min(a0.z, a1.z) - 0.03
        caixa(bm, Vector(((a0.x + a1.x) / 2, (a0.y + a1.y) / 2, zt)), (0.035, (a1 - a0).length + 0.04, 0.03), mh)   # travessa
        bm2 = bm
        d0 = Vector((a0.x, a0.y, 0.06))
        d1 = Vector((a1.x, a1.y, zt - 0.02))
        e = (d1 - d0)
        q = e.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cube(bm2, size=1.0, matrix=Matrix.Translation((d0 + d1) / 2) @ q @ Matrix.Diagonal((0.022, 0.022, e.length, 1)))   # mão-francesa
    obj(nome + '_cavaletes', bm, 'aco', raiz)
    # catracas nas pontas (eixo atravessado, uma roda de cada lado) e eixo cromado
    rodas = []
    for s in (0.05, L - 0.05):
        p, d = f(s)
        m = base(d)
        lado = m @ Vector((0, 1, 0))
        for lado_s in (-1, 1):
            rodas.append(catraca(nome + '_catraca', p + m @ Vector((0, lado_s * (W / 2 - 0.08), -0.06)), lado, 0.055, 10, 0.025, 'aco', raiz))
        bm = bmesh.new()
        cil(bm, p + m @ Vector((0, 0, -0.06)), 0.012, W + 0.02, lado, lados=8)
        obj(nome + '_eixo', bm, 'cromo', raiz)
    # motor na cabeceira: coroa no eixo da catraca da ponta, por fora da lateral; motor preso por suporte à perna
    # da ponta, embaixo; corrente do pinhão do motor até a coroa
    pe_, de_ = f(L - 0.05)
    mm = base(de_)
    lado = mm @ Vector((0, 1, 0))
    eixo_c = pe_ + mm @ Vector((0, 0, -0.06))
    y_fora = -(W / 2 + 0.075)
    coroa_c = eixo_c + mm @ Vector((0, y_fora, 0))
    pinhao_c = coroa_c + mm @ Vector((-0.02, 0, -0.17))
    bm = bmesh.new()
    cil(bm, eixo_c + mm @ Vector((0, y_fora * 0.93, 0)), 0.012, 0.09, lado, lados=8)                 # ponta do eixo
    caixa(bm, pinhao_c + mm @ Vector((-0.0, 0.03, -0.0)), (0.11, 0.07, 0.085), mm)                   # carcaça
    cil(bm, pinhao_c + mm @ Vector((-0.09, 0.03, 0)), 0.038, 0.07, mm @ Vector((1, 0, 0)), lados=12)
    for k in range(4):
        cil(bm, pinhao_c + mm @ Vector((-0.065 - 0.018 * k, 0.03, 0)), 0.045, 0.006, mm @ Vector((1, 0, 0)), lados=12)
    obj(nome + '_motor', bm, 'amarelo', raiz)
    bm = bmesh.new()                                                                                 # suporte do motor
    caixa(bm, pinhao_c + mm @ Vector((0.0, 0.075, -0.0)), (0.13, 0.012, 0.11), mm)
    perna = pe_ + mm @ Vector((0, -(W / 2 + 0.03), -0.112))
    caixa(bm, (pinhao_c + mm @ Vector((0.03, 0.075, 0)) + Vector((perna.x, perna.y, pinhao_c.z))) / 2, (0.05, 0.02, 0.05), mm)
    obj(nome + '_suporte', bm, 'grafite', raiz)
    pinhao = catraca(nome + '_pinhao', pinhao_c + mm @ Vector((0, -0.0, 0)), lado, 0.03, 8, 0.02, 'cromo', raiz)
    coroa = catraca(nome + '_coroa', coroa_c, lado, 0.05, 12, 0.02, 'aco', raiz)
    # corrente: elos ao longo do laço (pinhão embaixo, coroa em cima)
    elos = []
    for k in range(26):
        bm = bmesh.new()
        caixa(bm, Vector((0, 0, 0)), (0.014, 0.012, 0.008))
        elos.append(obj(nome + '_elo', bm, 'grafite', raiz))
    laco = (pinhao_c, 0.03 * 0.95, coroa_c, 0.05 * 0.95, mm)
    # placas do leito: cada placa é um objeto que anda pelo caminho
    placas = []
    total = 2.0 * L + 2.0 * PI * RHO           # laço da corrente de placas: em cima, volta na cabeceira, embaixo, volta no pé
    n_placas = int(round(total / PASSO))
    passo = total / n_placas                   # placas inteiras no laço (passo quase igual ao nominal)
    for k in range(n_placas):
        bm = bmesh.new()
        placa_trapezio(bm, passo, curv, -W / 2, W / 2, -0.006, 0.006)
        for dy in (-W / 4, W / 4):                                                 # nervuras ao longo da largura
            placa_trapezio(bm, 0.012 + FOLGA, 0.0, dy - (W / 4 - 0.03), dy + (W / 4 - 0.03), 0.006, 0.012)
        placas.append(obj(nome + '_placa', bm, 'placa', raiz))
    return {'f': f, 'L': L, 'passo': passo, 'total': total, 'placas': placas, 'rodas': rodas, 'pinhao': pinhao, 'coroa': coroa, 'elos': elos, 'laco': laco}


def ponto_laco(laco, u):
    """Laço da corrente (0..1): reta subindo, meia-volta na coroa, reta descendo, meia-volta no pinhão."""
    pc, rp, cc, rc, mm = laco
    frente = mm @ Vector((1, 0, 0))
    cima = (cc - pc).normalized()
    reta = (cc - pc).length
    voltas = PI * rp + PI * rc
    total = 2 * reta + voltas
    d = (u % 1.0) * total
    if d < reta:
        return pc + frente * rp + cima * d
    d -= reta
    if d < PI * rc:
        a = d / rc
        return cc + frente * (rc * math.cos(a)) + cima * (rc * math.sin(a))
    d -= PI * rc
    if d < reta:
        return cc - frente * rc - cima * d
    d -= reta
    a = PI + d / rp
    return pc + frente * (rp * math.cos(a)) + cima * (rp * math.sin(a))


def no_laco(f, L, u):
    """Posição e orientação (quaternion) da placa a u metros do começo do laço."""
    from mathutils import Quaternion
    meia = PI * RHO
    if u < L:                                                       # em cima, indo
        p, d = f(u)
        return p, base(d).to_quaternion()
    u -= L
    if u < meia:                                                    # volta na cabeceira (desce)
        p, d = f(L)
        m = base(d)
        c = p + m @ Vector((0, 0, -RHO))
        a = u / RHO
        pos = c + m @ Vector((RHO * math.sin(a), 0, RHO * math.cos(a)))
        return pos, base(d).to_quaternion() @ Quaternion((0, 1, 0), a)
    u -= meia
    if u < L:                                                       # embaixo, voltando (de cabeça para baixo)
        p, d = f(L - u)
        m = base(d)
        return p + m @ Vector((0, 0, -2 * RHO)), base(d).to_quaternion() @ Quaternion((0, 1, 0), PI)
    u -= L
    p, d = f(0.0)                                                   # volta no pé (sobe)
    m = base(d)
    c = p + m @ Vector((0, 0, -RHO))
    a = PI + u / RHO
    pos = c + m @ Vector((RHO * math.sin(a), 0, RHO * math.cos(a)))
    return pos, base(d).to_quaternion() @ Quaternion((0, 1, 0), a)


def animar(e):
    L, f, passo, total = e['L'], e['f'], e['passo'], e['total']
    duracao = QUADROS / FPS
    vel = round(VEL * duracao / passo) * passo / duracao        # anda passos inteiros no laço (vídeo sem salto)
    for q in range(1, QUADROS + 1):
        t = (q - 1) / FPS
        for k, o in enumerate(e['placas']):
            p, qr = no_laco(f, L, (k * passo + vel * t) % total)
            o.location = p
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = qr
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
        for r in e['rodas'] + [e['pinhao'], e['coroa']]:
            raio = 0.03 if r == e['pinhao'] else 0.055
            dentes = 8 if r == e['pinhao'] else (12 if r == e['coroa'] else 10)
            passo_ang = 2 * PI / dentes
            w = round(vel * duracao / raio / passo_ang) * passo_ang / duracao
            if r not in r.get('_q0', [r]) or '_q0' not in r:
                r['_q0'] = list(r.rotation_quaternion)
            q0 = Matrix.Identity(3)
            from mathutils import Quaternion
            base_q = Quaternion(r['_q0'])
            r.rotation_quaternion = base_q @ Quaternion((0, 0, 1), -w * t)
            r.keyframe_insert('rotation_quaternion', frame=q)
        for k, o in enumerate(e['elos']):
            o.location = ponto_laco(e['laco'], k / len(e['elos']) + t * 0.5)
            o.keyframe_insert('location', frame=q)
    for o in sc.objects:
        if o.animation_data and o.animation_data.action:
            for fc in getattr(o.animation_data.action, 'fcurves', []):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'


pecas = [esteira('reta', caminho_reta(2.0), Vector((-2.4, 0.4, 0))),
         esteira('curva', caminho_curva(), Vector((0.2, -0.3, 0))),
         esteira('rampa', caminho_rampa(), Vector((1.9, 0.6, 0)))]
for e in pecas:
    animar(e)

# chão, luz e câmera
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(M['chao'])
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 5.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(30))
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
    for d in pr.devices:
        d.use = True
except Exception:
    sc.cycles.device = 'CPU'
sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.4
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'tudo'
if modo in ('tudo', 'foto'):
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    sc.frame_set(12)
    mirar((0.6, -2.4, 1.5), (0.05, 0.05, 0.2), 35)
    sc.render.filepath = os.path.join(AQUI, 'esteira_foto_perto.png')
    bpy.ops.render.render(write_still=True)
    mirar((0.2, -5.6, 4.2), (0.0, 0.3, 0.2), 30)
    sc.render.filepath = os.path.join(AQUI, 'esteira_foto_todas.png')
    bpy.ops.render.render(write_still=True)
if modo in ('tudo', 'video'):
    sc.cycles.samples = 96
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False          # ruído parado entre quadros (não cintila)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.35
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    mirar((-0.6, -3.4, 2.1), (-0.6, 0.25, 0.15), 32)
    os.makedirs(os.path.join(AQUI, 'quadros'), exist_ok=True)
    sc.render.filepath = os.path.join(AQUI, 'quadros', 'q')
    bpy.ops.render.render(animation=True)
print('ESTEIRA ok')
