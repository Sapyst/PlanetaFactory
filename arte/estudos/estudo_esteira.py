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
M_MIN = RHO + 0.006  # margem mínima entre a ponta da peça e o eixo da catraca (a volta das placas cabe na peça)


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


def esteira(nome, caminho, origem, rot_z=0.0, motor=True, acoplar=()):
    raiz = bpy.data.objects.new(nome, None)
    sc.collection.objects.link(raiz)
    raiz.location = origem
    raiz.rotation_euler.z = rot_z
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
    # margem m: o laço de placas vira dentro da peça e o laço tem um número inteiro de placas (passo igual em todas)
    n_placas = int((2.0 * (L - 2.0 * M_MIN) + 2.0 * PI * RHO) / PASSO)
    Lr = (n_placas * PASSO - 2.0 * PI * RHO) / 2.0              # trecho reto em cima
    m = (L - Lr) / 2.0
    total = n_placas * PASSO
    # catracas nas pontas do laço (eixo atravessado, uma roda de cada lado) e eixo cromado
    rodas = []                                                   # (roda, razão de giro em relação ao eixo das catracas)
    for s in (m, L - m):
        p, d = f(s)
        mr = base(d)
        lado = mr @ Vector((0, 1, 0))
        for lado_s in (-1, 1):
            rodas.append((catraca(nome + '_catraca', p + mr @ Vector((0, lado_s * (W / 2 - 0.08), -RHO)), lado, 0.055, 10, 0.025, 'aco', raiz), 1.0))
        bm = bmesh.new()
        cil(bm, p + mr @ Vector((0, 0, -RHO)), 0.012, W + 0.02, lado, lados=8)
        obj(nome + '_eixo', bm, 'cromo', raiz)
    correntes = []
    y_fora = -(W / 2 + 0.075)
    if motor:
        # motor na cabeceira: coroa no eixo da catraca da ponta, por fora da lateral; motor preso por suporte à
        # perna da ponta, embaixo; corrente do pinhão do motor até a coroa
        pe_, de_ = f(L - m)
        mm = base(de_)
        lado = mm @ Vector((0, 1, 0))
        eixo_c = pe_ + mm @ Vector((0, 0, -RHO))
        coroa_c = eixo_c + mm @ Vector((0, y_fora, 0))
        pinhao_c = coroa_c + mm @ Vector((-0.02, 0, -0.17))
        bm = bmesh.new()
        cil(bm, eixo_c + mm @ Vector((0, y_fora * 0.93, 0)), 0.012, 0.09, lado, lados=8)             # ponta do eixo
        caixa(bm, pinhao_c + mm @ Vector((-0.0, 0.03, -0.0)), (0.11, 0.07, 0.085), mm)               # carcaça
        cil(bm, pinhao_c + mm @ Vector((-0.09, 0.03, 0)), 0.038, 0.07, mm @ Vector((1, 0, 0)), lados=12)
        for k in range(4):
            cil(bm, pinhao_c + mm @ Vector((-0.065 - 0.018 * k, 0.03, 0)), 0.045, 0.006, mm @ Vector((1, 0, 0)), lados=12)
        obj(nome + '_motor', bm, 'amarelo', raiz)
        bm = bmesh.new()                                                                             # suporte do motor
        caixa(bm, pinhao_c + mm @ Vector((0.0, 0.075, -0.0)), (0.13, 0.012, 0.11), mm)
        perna = pe_ + mm @ Vector((0, -(W / 2 + 0.03), -0.112))
        caixa(bm, (pinhao_c + mm @ Vector((0.03, 0.075, 0)) + Vector((perna.x, perna.y, pinhao_c.z))) / 2, (0.05, 0.02, 0.05), mm)
        obj(nome + '_suporte', bm, 'grafite', raiz)
        rodas.append((catraca(nome + '_pinhao', pinhao_c, lado, 0.03, 8, 0.02, 'cromo', raiz), 12 / 8))
        rodas.append((catraca(nome + '_coroa', coroa_c, lado, 0.05, 12, 0.02, 'aco', raiz), 1.0))
        correntes.append(corrente(nome, (pinhao_c, 0.03 * 0.95, coroa_c, 0.05 * 0.95, lado), raiz))
    # rodas de acoplamento: mais para fora que a coroa, no mesmo eixo; a corrente entre peças é feita depois
    acopla = {}
    for ponta in acoplar:
        p, d = f(m if ponta == 'pe' else L - m)
        mr = base(d)
        lado = mr @ Vector((0, 1, 0))
        y_ac = y_fora - 0.035
        c = p + mr @ Vector((0, y_ac, -RHO))
        bm = bmesh.new()
        y0 = -(W / 2 + 0.01)
        cil(bm, p + mr @ Vector((0, (y0 + y_ac - 0.015) / 2, -RHO)), 0.012, abs(y_ac - 0.015 - y0), lado, lados=8)
        obj(nome + '_ponta_eixo', bm, 'cromo', raiz)
        rodas.append((catraca(nome + '_acopla', c, lado, 0.05, 12, 0.02, 'aco', raiz), 1.0))
        acopla[ponta] = (c, lado)
    # placas do leito: cada placa é um objeto que anda pelo laço
    placas = []
    for k in range(n_placas):
        bm = bmesh.new()
        placa_trapezio(bm, PASSO, curv, -W / 2, W / 2, -0.006, 0.006)
        for dy in (-W / 4, W / 4):                                                 # nervuras ao longo da largura
            placa_trapezio(bm, 0.012 + FOLGA, 0.0, dy - (W / 4 - 0.03), dy + (W / 4 - 0.03), 0.006, 0.012)
        placas.append(obj(nome + '_placa', bm, 'placa', raiz))
    for r, _ in rodas:
        r['_q0'] = list(r.rotation_quaternion)
    mundo = Matrix.Translation(origem) @ Matrix.Rotation(rot_z, 4, 'Z')
    return {'f': f, 'L': L, 'm': m, 'Lr': Lr, 'total': total, 'placas': placas, 'rodas': rodas,
            'correntes': correntes, 'acopla': acopla, 'mundo': mundo}


def corrente(nome, laco, pai, passo_elo=0.026):
    """Corrente de rolos: elos (caixinhas) que percorrem o laço entre duas rodas."""
    n = max(8, int(round(comprimento_laco(laco) / passo_elo)))
    elos = []
    for k in range(n):
        bm = bmesh.new()
        caixa(bm, Vector((0, 0, 0)), (0.016, 0.012, 0.008))
        o = obj(nome + '_elo', bm, 'grafite', pai)
        o.rotation_mode = 'QUATERNION'
        elos.append(o)
    return {'laco': laco, 'elos': elos}


def comprimento_laco(laco):
    pc, rp, cc, rc, lado = laco
    cima = (cc - pc).normalized()
    frente = cima.cross(lado).normalized()
    return 2 * ((cc + frente * rc) - (pc + frente * rp)).length + PI * (rp + rc)


def ponto_laco(laco, d):
    """Ponto a d metros no laço da corrente: reta de pc a cc (lado +frente), meia-volta em cc, reta de volta,
    meia-volta em pc. frente = cima × eixo, então o sentido bate com o giro positivo das rodas em torno do eixo."""
    pc, rp, cc, rc, lado = laco
    cima = (cc - pc).normalized()
    frente = cima.cross(lado).normalized()
    a0, a1 = pc + frente * rp, cc + frente * rc
    b0, b1 = cc - frente * rc, pc - frente * rp
    reta = (a1 - a0).length
    d %= comprimento_laco(laco)
    if d < reta:
        return a0 + (a1 - a0) * (d / reta)
    d -= reta
    if d < PI * rc:
        a = d / rc
        return cc + frente * (rc * math.cos(a)) + cima * (rc * math.sin(a))
    d -= PI * rc
    if d < reta:
        return b0 + (b1 - b0) * (d / reta)
    d -= reta
    a = PI + d / rp
    return pc + frente * (rp * math.cos(a)) + cima * (rp * math.sin(a))


def no_laco(f, m, Lr, u):
    """Posição e orientação (quaternion) da placa a u metros do começo do laço (início do trecho de cima)."""
    from mathutils import Quaternion
    meia = PI * RHO
    if u < Lr:                                                      # em cima, indo
        p, d = f(m + u)
        return p, base(d).to_quaternion()
    u -= Lr
    if u < meia:                                                    # volta na cabeceira (desce)
        p, d = f(m + Lr)
        mb = base(d)
        a = u / RHO
        pos = p + mb @ Vector((RHO * math.sin(a), 0, RHO * math.cos(a) - RHO))
        return pos, mb.to_quaternion() @ Quaternion((0, 1, 0), a)
    u -= meia
    if u < Lr:                                                      # embaixo, voltando (de cabeça para baixo)
        p, d = f(m + Lr - u)
        mb = base(d)
        return p + mb @ Vector((0, 0, -2 * RHO)), mb.to_quaternion() @ Quaternion((0, 1, 0), PI)
    u -= Lr
    p, d = f(m)                                                     # volta no pé (sobe)
    mb = base(d)
    a = PI + u / RHO
    pos = p + mb @ Vector((RHO * math.sin(a), 0, RHO * math.cos(a) - RHO))
    return pos, mb.to_quaternion() @ Quaternion((0, 1, 0), a)


DURACAO = QUADROS / FPS
VEL_R = round(VEL * DURACAO / PASSO) * PASSO / DURACAO       # anda placas inteiras no vídeo (laço sem salto)
GIRO = PI * round(VEL_R * DURACAO / RHO / PI)                # giro do eixo no vídeo: múltiplo de 180° (10 e 12 dentes)


def animar_corrente(c, giro_raio):
    """A corrente anda o que a roda gira; arredondado para um número inteiro de elos no vídeo."""
    from mathutils import Quaternion
    comp = comprimento_laco(c['laco'])
    n = len(c['elos'])
    elo = comp / n
    desloc = round(giro_raio / elo) * elo
    lado = c['laco'][4]
    for q in range(1, QUADROS + 1):
        t = (q - 1) / FPS
        for k, o in enumerate(c['elos']):
            d = k * elo + desloc * t / DURACAO
            p = ponto_laco(c['laco'], d)
            tg = (ponto_laco(c['laco'], d + 0.002) - p).normalized()
            o.location = p
            o.rotation_quaternion = Matrix((tg, lado, tg.cross(lado))).transposed().to_quaternion()
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)


def animar(e, fase):
    from mathutils import Quaternion
    f, m, Lr, total = e['f'], e['m'], e['Lr'], e['total']
    for q in range(1, QUADROS + 1):
        t = (q - 1) / FPS
        for k, o in enumerate(e['placas']):
            p, qr = no_laco(f, m, Lr, (k * PASSO + VEL_R * t + fase) % total)
            o.location = p
            o.rotation_mode = 'QUATERNION'
            o.rotation_quaternion = qr
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
        for r, razao in e['rodas']:
            r.rotation_quaternion = Quaternion(r['_q0']) @ Quaternion((0, 0, 1), GIRO * razao * t / DURACAO)
            r.keyframe_insert('rotation_quaternion', frame=q)
    for c in e['correntes']:
        animar_corrente(c, GIRO * c['laco'][3])


# linha ligada: reta (2 m, para +x) → curva (entra por oeste, sai para +y) → rampa (sobe para +y).
# As pontas e as direções coincidem; a curva não tem motor: é puxada pela reta por uma corrente de acoplamento.
O_RETA = Vector((-1.5, -0.5, 0))
O_CURVA = O_RETA + Vector((1.5, 0, 0))
O_RAMPA = O_CURVA + Vector((0, 1.0, 0))
pecas = [esteira('reta', caminho_reta(2.0), O_RETA, acoplar=('cabeca',)),
         esteira('curva', caminho_curva(), O_CURVA, motor=False, acoplar=('pe',)),
         esteira('rampa', caminho_rampa(), O_RAMPA, rot_z=PI / 2)]
# fase: uma grade única de placas ao longo da linha — a placa que some na cabeceira de uma peça reaparece
# no pé da seguinte no mesmo compasso (δ_B ≡ δ_A + m_A − L_A − m_B, mod passo)
fase = 0.0
for i, e in enumerate(pecas):
    if i > 0:
        a = pecas[i - 1]
        fase = (fase + a['m'] - a['L'] - e['m']) % PASSO
    animar(e, fase)
# chapa de transferência (fixa) em cada junção: cobre o vão entre as voltas das placas, do topo de uma peça ao da outra
bm = bmesh.new()
for a, b in zip(pecas, pecas[1:]):
    pa, da = a['f'](a['L'] - a['m'])
    pb, db = b['f'](b['m'])
    pa, pb = a['mundo'] @ pa, b['mundo'] @ pb
    d = (pb - pa)
    mb = base(d.normalized())
    caixa(bm, (pa + pb) / 2 + mb @ Vector((0, 0, 0.004)), (d.length + 0.03, W - 0.01, 0.008), mb)
    for y in (-W / 2 + 0.03, W / 2 - 0.03):                              # parafusos de cabeça chata
        for x in (-0.25, 0.25):
            cil(bm, (pa + pb) / 2 + mb @ Vector((x * d.length, y, 0.009)), 0.007, 0.003, mb @ Vector((0, 0, 1)), lados=6)
obj('ponte', bm, 'aco')
# corrente de acoplamento: eixo da cabeceira da reta → eixo do pé da curva (mesmas rodas de 12 dentes)
ca, la = pecas[0]['acopla']['cabeca']
cb, _ = pecas[1]['acopla']['pe']
lado_m = (pecas[0]['mundo'].to_3x3() @ la).normalized()
acop = corrente('acopla', (pecas[0]['mundo'] @ ca, 0.05 * 0.95, pecas[1]['mundo'] @ cb, 0.05 * 0.95, lado_m), None)
animar_corrente(acop, GIRO * 0.05 * 0.95)
for o in sc.objects:
    if o.animation_data and o.animation_data.action:
        for fc in getattr(o.animation_data.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

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
    mirar((0.35, -2.0, 1.0), (-0.45, -0.45, 0.12), 35)
    sc.render.filepath = os.path.join(AQUI, 'esteira_foto_perto.png')
    bpy.ops.render.render(write_still=True)
    mirar((1.2, -4.6, 3.0), (-0.8, 0.0, 0.25), 30)
    sc.render.filepath = os.path.join(AQUI, 'esteira_foto_todas.png')
    bpy.ops.render.render(write_still=True)
if modo in ('tudo', 'video'):
    sc.cycles.samples = 96
    sc.cycles.seed = 7
    sc.cycles.use_animated_seed = False          # ruído parado entre quadros (não cintila)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.35
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    mirar((1.0, -3.9, 2.3), (-0.7, 0.0, 0.2), 30)
    os.makedirs(os.path.join(AQUI, 'quadros'), exist_ok=True)
    sc.render.filepath = os.path.join(AQUI, 'quadros', 'q')
    bpy.ops.render.render(animation=True)
print('ESTEIRA ok')
