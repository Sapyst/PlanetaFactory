"""Estudo isolado (fora do jogo): DRONES do PlanetaFactory + ESTAÇÃO DE DRONES (2×2), cada ação animada.
Modelos em estudo_drones_modelo.py. Linha do tempo única, 24 qps, 6 blocos de 96 quadros (4 s), um por ação, com
marcadores: SPAWN 1–96 · DECOLAGEM/VOO/CURVA 97–192 · REPARO 193–288 · COMBATE 289–384 · POUSO/RECARGA 385–480 ·
DERRUBADO 481–576. Cada bloco é independente (vira um clipe no jogo).
Física: a atitude dos drones sai de uma simulação mola-amortecedor por quadro (inclina na direção da aceleração,
passa do ponto e volta; pairar com ruído de rajada; guinada com tranco; recuo de solda e de tiro; pêndulo da carga;
descontrole com hélice danificada). Sem humanos: nada de cabine, assento, escada.
Uso: blender -b --python estudo_drones.py -- foto   (ou 'foto <nome>' para uma só)"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha
import importlib
import estudo_drones_modelo as DM
importlib.reload(DM)
from estudo_drones_modelo import (peca, vazio, luz, colecao, toro, esfera, prisma, suavizar, Z_PATIM, DECK, TOPO_BERCO,
                                  TOPO_FAB, FAB, BERCOS, REVISTA, BRACO_EST)

PI = math.pi
FPS = 24
DT = 1.0 / FPS
G = 9.81
N = 576
BLOCOS = [('SPAWN', 1, 96), ('DECOLAGEM_VOO_CURVA', 97, 192), ('REPARO', 193, 288), ('COMBATE', 289, 384),
          ('POUSO_RECARGA', 385, 480), ('DERRUBADO', 481, 576)]
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, N
for nome, a, b in BLOCOS:
    sc.timeline_markers.new(nome, frame=a)

DM.criar_materiais()
M = base3d.M


def suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def rampa(f, a, b):
    return suave((f - a) / (b - a))


def lin(f, a, b):
    return min(1.0, max(0.0, (f - a) / (b - a)))


_ultq = {}


def chave(o, attr, f, idx=-1):
    if attr == 'rotation_quaternion':                                     # continuidade de sinal (q e -q)
        q = o.rotation_quaternion.copy()
        ant = _ultq.get(o.name)
        if ant is not None and ant.dot(q) < 0:
            q.negate()
            o.rotation_quaternion = q
        _ultq[o.name] = q
    o.keyframe_insert(attr, frame=f, index=idx) if idx >= 0 else o.keyframe_insert(attr, frame=f)


def chave_val(sock, v, f):
    sock.default_value = v
    sock.keyframe_insert('default_value', frame=f)


def descendentes(raiz):
    out = []
    for o in bpy.data.objects:
        p = o
        while p is not None:
            if p == raiz:
                out.append(o)
                break
            p = p.parent
    return out


def mostrar(objs, f, v):
    for o in objs:
        o.hide_render = not v
        o.hide_viewport = not v
        o.keyframe_insert('hide_render', frame=f)
        o.keyframe_insert('hide_viewport', frame=f)


# ================================================================== cenário: chão, capim
colecao('cenario')
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (80, 80, 1.0))
peca('chao', bm, 'chao')
bm = bmesh.new()
for k in range(220):                                                       # pedrinhas
    a, r = random.uniform(0, 2 * PI), random.uniform(1.2, 12)
    pedra(bm, Vector((math.cos(a) * r, math.sin(a) * r, 0.0)), random.uniform(0.02, 0.07), 0.5)
peca('pedras', bm, 'concreto')
bm = bmesh.new()
for k in range(30):                                                        # manchas de terra escura
    mancha(bm, (random.uniform(-10, 10), random.uniform(-8, 10)), random.uniform(0.3, 0.9), 0.001)
peca('terra', bm, 'fuligem')

# ================================================================== estação
colecao('estacao')
E = DM.estacao()
m_fab = DM.grade_laser_mat('Grade fab', (1.0, 0.03, 0.015), 1.2, 0.035)
E['fab_grade'].data.materials[0] = m_fab

# ================================================================== máquina avariada (alvo do reparo)
MQ = Vector((6.0, 1.5, 0.0))
colecao('maquina')
e_scan = vazio('scan_reparo', None, (MQ.x, MQ.y, -50))
e_solda = vazio('progresso_solda')
e_solda.rotation_mode = 'XYZ'
e_cura = vazio('cura_rachadura', None, (MQ.x, MQ.y, 2.0))
_cache = {}


def mapa_scan(chave_, m):
    if chave_ not in _cache:
        _cache[chave_] = DM.escanear(m, e_scan)
    return _cache[chave_]


DM.MAPA[0] = mapa_scan
bm = bmesh.new()
caixa_de(bm, (MQ.x - 0.6, MQ.y - 0.6, 0), (MQ.x + 0.6, MQ.y + 0.6, 0.1))
peca('maq_pe', bm, 'ferro')
bm = bmesh.new()
res = bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=14, use_grid_fill=True)
AMASSADOS = [(Vector((-0.15, -0.55, 0.62)), 0.2, 0.06), (Vector((0.55, 0.2, 0.4)), 0.16, 0.05), (Vector((0.3, -0.55, 0.25)), 0.12, 0.035)]
for v in bm.verts:
    p = Vector((v.co.x * 1.1, v.co.y * 1.1, 0.1 + (v.co.z + 0.5) * 0.95))
    for c, r, prof in AMASSADOS:
        d = (p - c).length
        if d < r:
            n = Vector((0, 1, 0)) if abs(c.y) > 0.5 else Vector((-1, 0, 0))
            n = Vector((0, 1 if c.y < 0 else -1, 0)) if abs(c.y) > 0.5 else Vector((-1 if c.x > 0 else 1, 0, 0))
            p += n * prof * (1 - (d / r) ** 2) ** 1.5 * random.uniform(0.8, 1.0)
    v.tag = (MQ + p - v.co).length > 1e-6 and (p - Vector((v.co.x * 1.1, v.co.y * 1.1, 0.1 + (v.co.z + 0.5) * 0.95))).length > 1e-5
    v.co = MQ + p
for fc in bm.faces:
    fc.smooth = any(v.tag for v in fc.verts)
peca('maq_corpo', bm, 'amarelo')
bm = bmesh.new()
caixa_de(bm, (MQ.x - 0.57, MQ.y - 0.57, 1.05), (MQ.x + 0.57, MQ.y + 0.57, 1.1))
peca('maq_tampa', bm, 'grafite')
bm = bmesh.new()
for k in range(7):                                                         # venezianas (leste)
    caixa(bm, (MQ.x + 0.56, MQ.y - 0.15, 0.45 + k * 0.055), (0.03, 0.5, 0.02), Matrix.Rotation(0.5, 3, 'Y'))
caixa_de(bm, (MQ.x + 0.55, MQ.y - 0.42, 0.4), (MQ.x + 0.58, MQ.y + 0.12, 0.42))
caixa_de(bm, (MQ.x + 0.55, MQ.y - 0.42, 0.83), (MQ.x + 0.58, MQ.y + 0.12, 0.85))
peca('maq_venezianas', bm, 'ferro')
bm = bmesh.new()                                                           # chapa solta pendurada (oeste)
caixa(bm, (MQ.x - 0.585, MQ.y + 0.15, 0.55), (0.012, 0.4, 0.34), Matrix.Rotation(0.22, 3, 'Y') @ Matrix.Rotation(0.15, 3, 'X'))
peca('maq_chapa_solta', bm, 'amarelo')
bm = bmesh.new()                                                           # chaminé e canos
cil(bm, MQ + Vector((0.38, 0.38, 1.3)), 0.06, 0.4, lados=16)
cil(bm, MQ + Vector((0.38, 0.38, 1.12)), 0.09, 0.04, lados=16)
tubo(bm, MQ + Vector((-0.4, 0.6, 0.8)), MQ + Vector((-0.4, 0.75, 0.8)), 0.03, 14)
tubo(bm, MQ + Vector((-0.4, 0.75, 0.8)), MQ + Vector((-0.4, 0.75, 0.06)), 0.03, 14)
esfera(bm, MQ + Vector((-0.4, 0.75, 0.8)), 0.03, 14)
peca('maq_canos', bm, 'queimado', liso=True)
bm = bmesh.new()
for c, r in ((Vector((0.1, -0.1)), 0.18), (Vector((-0.25, -0.15)), 0.12), (Vector((0.3, 0.2)), 0.1)):
    mancha(bm, (MQ.x + c.x, MQ.y + c.y), r, 1.1012)
peca('maq_fuligem', bm, 'fuligem')
bm = bmesh.new()
for k in range(5):                                                         # óleo escorrendo na face sul
    x = MQ.x + random.uniform(-0.4, 0.4)
    caixa_de(bm, (x - 0.004, MQ.y - 0.553, 0.12), (x + 0.004, MQ.y - 0.551, random.uniform(0.25, 0.5)))
mancha(bm, (MQ.x - 0.1, MQ.y - 0.75), 0.25, 0.002)
peca('maq_oleo', bm, 'oleo')
DM.MAPA[0] = None

# rachaduras: A no topo (soldada pelo braço), B na face sul (fecha quando o scan passa)
A0, A1 = MQ + Vector((-0.3, -0.16, 1.1)), MQ + Vector((0.24, 0.12, 1.1))
DIR_A = (A1 - A0).normalized()
ANG_A = math.atan2(DIR_A.y, DIR_A.x)


def zigue(p0, p1, n, amp, normal):
    lat = (p1 - p0).normalized().cross(normal).normalized()
    return [p0 + (p1 - p0) * (i / n) + lat * (amp * random.uniform(-1, 1) if 0 < i < n else 0) for i in range(n + 1)]


def faixa(bm, pts, larg, normal):
    for a, b in zip(pts, pts[1:]):
        d = (b - a)
        lat = d.normalized().cross(normal).normalized()
        w = larg * random.uniform(0.6, 1.3)
        vs = [bm.verts.new(p) for p in (a - lat * w, a + lat * w, b + lat * w * 0.8, b - lat * w * 0.8)]
        bm.faces.new(vs)


random.seed(3)
PTS_A = zigue(A0, A1, 14, 0.018, Vector((0, 0, 1)))
PTS_A = [p + Vector((0, 0, 0.0012)) for p in PTS_A]
RAMOS_A = [zigue(PTS_A[i], PTS_A[i] + Vector((random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), 0)), 4, 0.01, Vector((0, 0, 1)))
           for i in (4, 9)]
B0, B1 = MQ + Vector((0.2, -0.553, 0.98)), MQ + Vector((0.12, -0.553, 0.42))
PTS_B = zigue(B0, B1, 12, 0.02, Vector((0, -1, 0)))
m_rach_a = DM.mascarar(M['rachadura'], e_solda, 'X', True)
m_cord_a = DM.mascarar(M['cordao'], e_solda, 'X', False, ((1.0, 0.32, 0.04), 30.0))
m_rach_b = DM.mascarar(M['rachadura'], e_cura, 'Z', False)
m_cord_b = DM.mascarar(M['cordao'], e_cura, 'Z', True, ((1.0, 0.03, 0.015), 14.0))
for nome, pts_l, mr, mc, nrm in (('A', [PTS_A] + RAMOS_A, m_rach_a, m_cord_a, Vector((0, 0, 1))), ('B', [PTS_B], m_rach_b, m_cord_b, Vector((0, -1, 0)))):
    bm = bmesh.new()
    for pts in pts_l:
        faixa(bm, pts, 0.007, nrm)
    o = peca('rachadura_' + nome, bm, 'rachadura')
    o.data.materials[0] = mr
    bm = bmesh.new()
    for pts in pts_l[:1]:
        for a, b in zip(pts, pts[1:]):
            for t in (0.0, 0.33, 0.66):
                p = a + (b - a) * t + nrm * 0.0015
                rot = Matrix.Rotation(math.atan2((b - a).y, (b - a).x), 4, 'Z') if nome == 'A' else Matrix.Identity(4)
                bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=0.009,
                                          matrix=Matrix.Translation(p) @ rot @ Matrix.Diagonal((1.3, 1.0, 0.45, 1) if nome == 'A' else (1.0, 0.45, 1.3, 1)))
    o = peca('cordao_' + nome, bm, 'cordao')
    o.data.materials[0] = mc

# ================================================================== aranha (inimigo do jogo)
colecao('aranha')
SP = Vector((-6.0, 5.0, 0.0))
DIR_D = (Vector((0, 0, 0)) - SP).normalized()                             # da aranha para a estação
ARQ_ARANHA = '/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/modelos/inimigos/aranha/aranha_montada/aranha_montada.glb'
antes = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=ARQ_ARANHA)
aranha = [o for o in bpy.data.objects if o not in antes and o.type == 'MESH'][0]
for o in [o for o in bpy.data.objects if o not in antes]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    DM.COL[0].objects.link(o)
troca = {'P_Escuro': mats.material('Aranha escuro', (0.03, 0.028, 0.03), 1.0, 0.5, pintura=False, ferrugem=0.4, sujeira=0.9),
         'P_Inimigo': mats.material('Aranha carapaça', (0.17, 0.06, 0.06), 0, 0.45, desgaste=0.9, sujeira=0.9),
         'P_Metal': M['aco'], 'P_OlhoInimigo': DM.emissivo('Olho aranha', (1.0, 0.12, 0.02), 10.0)}
olhos = Vector()
n_ol = 0
for i, s in enumerate(aranha.material_slots):
    nm = s.material.name.split('.')[0]
    if nm == 'P_OlhoInimigo':
        for pg in aranha.data.polygons:
            if pg.material_index == i:
                olhos += pg.center
                n_ol += 1
    if nm in troca:
        s.material = troca[nm]
frente_ar = (olhos / max(n_ol, 1)).to_2d().normalized() if n_ol else Vector((1, 0))
YAW_AR = math.atan2(DIR_D.y, DIR_D.x) - math.atan2(frente_ar.y, frente_ar.x)
aranha_piv = vazio('aranha_pivo', None, SP)
aranha_piv.rotation_mode = 'XYZ'
aranha.parent = aranha_piv
aranha.location = (0, 0, 0)
aranha.rotation_mode = 'XYZ'
aranha.rotation_euler = (0, 0, YAW_AR)
for p in aranha.data.polygons:
    p.use_smooth = False
CENTRO_AR = SP + Vector((0, 0, 0.55))

# ================================================================== drones
# R1: drone de reparo que nasce no holograma (materiais com o efeito); L1 logístico; D1 defesa; sucata; vitrine
colecao('R1')
e_holo = vazio('holo_frente', None, (FAB.x, FAB.y, -50))
e_sol = vazio('holo_solido', None, (FAB.x, FAB.y, -50))
_hc, FANTASMAS = {}, []


def mapa_holo(chave_, m):
    if chave_ not in _hc:
        m2 = DM.holografar(m, e_holo, e_sol)
        _hc[chave_] = m2
        nt = m2.node_tree                                                   # fantasma liga devagar (nó de valor)
        vn = nt.nodes.new('ShaderNodeValue')
        vn.outputs[0].default_value = 0.0
        mg = nt.nodes['Fantasma_mix']
        src = mg.inputs[0].links[0].from_socket
        mu = nt.nodes.new('ShaderNodeMath')
        mu.operation = 'MULTIPLY'
        nt.links.new(src, mu.inputs[0])
        nt.links.new(vn.outputs[0], mu.inputs[1])
        nt.links.new(mu.outputs[0], mg.inputs[0])
        FANTASMAS.append(vn.outputs[0])
    return _hc[chave_]


DM.MAPA[0] = mapa_holo
R1 = DM.drone('reparo', 'R1')
DM.MAPA[0] = None
colecao('L1')
L1 = DM.drone('logistico', 'L1')
colecao('D1')
D1 = DM.drone('defesa', 'D1')
colecao('sucata')
SU = DM.drone('defesa', 'D1_sucata', amassar=0.0035)
colecao('vitrine')
VR = DM.drone('reparo', 'V_reparo')
VD = DM.drone('defesa', 'V_defesa')
VL = DM.drone('logistico', 'V_logistico')
colecao('efeitos')

# ================================================================== simulação física (mola-amortecedor por quadro)


def quat_de(up2, yaw):
    up = Vector((up2.x, up2.y, 1.0)).normalized()
    return Vector((0, 0, 1)).rotation_difference(up) @ Quaternion((0, 0, 1), yaw)


def simular(plano, f0, f1, seed=0, w_t=10.0, z_t=0.38, w_y=7.0, z_y=0.32, w_o=8.0, z_o=0.45):
    """Integra a atitude (inclinação 2D, guinada) e o deslocamento por recuo, quadro a quadro, a partir do plano de
    voo (posição alvo). Devolve {f: (pos, quat, info)}."""
    res = {}
    tilt, tv = Vector((0, 0)), Vector((0, 0))
    off, ov = Vector((0, 0, 0)), Vector((0, 0, 0))
    yaw, yv = None, 0.0
    PL = {f: plano(f) for f in range(f0, f1 + 1)}

    def pp(f):
        return PL[min(f1, max(f0, f))]['p']

    for f in range(f0, f1 + 1):
        P = PL[f]
        alvo_y = P['yaw']
        if yaw is None:
            yaw = alvo_y
        while alvo_y - yaw > PI:
            alvo_y -= 2 * PI
        while alvo_y - yaw < -PI:
            alvo_y += 2 * PI
        if P.get('preso'):
            tilt, tv, off, ov, yaw, yv = Vector((0, 0)), Vector((0, 0)), Vector((0, 0, 0)), Vector((0, 0, 0)), alvo_y, 0.0
            res[f] = (P['p'].copy(), quat_de(Vector((0, 0)), yaw), P)
            continue
        a = (pp(f + 2) - 2 * pp(f) + pp(f - 2)) / (2 * DT) ** 2
        alvo = Vector((a.x, a.y)) / G
        if alvo.length > 0.42:
            alvo *= 0.42 / alvo.length
        alvo += P.get('tilt_extra', Vector((0, 0)))
        t = f * DT
        r = P.get('ruido', 1.0)
        rajada = Vector((noise.noise(Vector((t * 0.9, seed, 0.3))), noise.noise(Vector((seed, t * 0.9, 1.7)))))
        alvo += rajada * 0.035 * r
        imp = P.get('impulso')
        if imp is not None:
            ov += imp
            tv += Vector((-imp.x, -imp.y)) * 6.0                          # recuo também empina o drone
        if P.get('tranco'):
            yv += P['tranco']
        for _ in range(4):
            h = DT / 4
            ta = (alvo - tilt) * w_t * w_t - tv * 2 * z_t * w_t
            tv += ta * h
            tilt += tv * h
            ya = (alvo_y - yaw) * w_y * w_y - yv * 2 * z_y * w_y
            yv += ya * h
            yaw += yv * h
            oa = -off * w_o * w_o - ov * 2 * z_o * w_o
            ov += oa * h
            off += ov * h
        bob = Vector((noise.noise(Vector((t * 1.3, seed + 4, 0))) * 0.012, noise.noise(Vector((seed + 9, t * 1.3, 0))) * 0.012,
                      math.sin(t * 2.1 + seed) * 0.012 + noise.noise(Vector((t * 2.0, 0, seed))) * 0.01)) * r
        res[f] = (P['p'] + off + bob, quat_de(tilt, yaw), P)
    return res


def gravar_drone(D, sim, faixa_vis=None):
    raiz = D['raiz']
    for f, (p, q, P) in sim.items():
        raiz.location = p
        raiz.rotation_quaternion = q
        chave(raiz, 'location', f)
        chave(raiz, 'rotation_quaternion', f)


def heading(v, padrao):
    return math.atan2(v.y, v.x) if v.to_2d().length > 1e-4 else padrao


def bez(P0, P1, P2, P3, u):
    return P0 * (1 - u) ** 3 + P1 * 3 * u * (1 - u) ** 2 + P2 * 3 * u * u * (1 - u) + P3 * u ** 3


# ---------------------------------------------------------------- R1: plano de voo por bloco
POS_FAB = Vector((FAB.x, FAB.y, TOPO_FAB + Z_PATIM + 0.004))
POS_BERCO = [Vector((B.x, B.y, TOPO_BERCO + Z_PATIM + 0.004)) for B in BERCOS]
HOVER_Z = 1.1 + 0.27


def ponto_solda(w):
    return A0 + (A1 - A0) * w


def pos_reparo(w):
    return ponto_solda(w) - DIR_A * 0.11 + Vector((0, 0, 0.27)) + Vector((-DIR_A.y, DIR_A.x, 0)) * 0.0


def progresso(f):
    return lin(f, 206, 262)


SUBIDA_FIM = 148
CURVA = (Vector((FAB.x, 0.8, 4.0)), Vector((FAB.x, 3.6, 4.3)), Vector((3.2, 5.6, 3.6)), pos_reparo(0.0) + Vector((-0.4, 0.3, 0.5)))


def plano_R1(f):
    if f <= 96:
        return dict(p=POS_FAB, yaw=0.0, giro=0.3 * rampa(f, 80, 96), preso=True)
    if f <= 192:
        if f < 106:
            return dict(p=POS_FAB, yaw=0.0, giro=0.3 + 0.7 * rampa(f, 97, 108), preso=True)
        if f <= SUBIDA_FIM:
            h1 = 0.45 * rampa(f, 106, 124)
            s = rampa(f, 120, SUBIDA_FIM)
            p = POS_FAB + Vector((0, 0.8 * s * s, h1 + (4.0 - POS_FAB.z - 0.45) * s))
            return dict(p=p, yaw=(PI / 2) * rampa(f, 124, 144), giro=1.0, ruido=0.3 + 0.4 * s)
        if f <= 184:
            u = rampa(f, SUBIDA_FIM, 184)
            p = bez(*CURVA, u)
            d = bez(*CURVA, min(1, u + 0.02)) - bez(*CURVA, max(0, u - 0.02))
            return dict(p=p, yaw=heading(d, PI / 2) if u < 0.85 else ANG_A, giro=1.0, ruido=0.5)
        u = rampa(f, 184, 192)
        return dict(p=CURVA[3] + (pos_reparo(0.0) - CURVA[3]) * u, yaw=ANG_A, giro=1.0)
    if f <= 288:
        w = progresso(f)
        p = pos_reparo(w)
        if f > 266:
            p = p + Vector((0, 0, 0.18 * rampa(f, 266, 280)))
        pulso = 206 <= f <= 262 and (f - 206) % 6 == 0
        return dict(p=p, yaw=ANG_A, giro=1.0, ruido=0.5,
                    impulso=(-DIR_A * 0.05 + Vector((0, 0, 0.035))) if pulso else None)
    if f <= 384:
        return dict(p=pos_reparo(1.0) + Vector((0, 0, 0.18)), yaw=ANG_A, giro=1.0)
    if f <= 480:
        P0 = Vector((3.4, 3.2, 2.7))
        topo = POS_BERCO[0] + Vector((0, 0, 0.9))
        if f <= 420:
            u = rampa(f, 385, 420)
            p = bez(P0, P0 + Vector((-1.2, -0.4, 0.2)), topo + Vector((0.9, 0.6, 0.3)), topo, u)
            y = heading(topo - P0, PI) if f < 408 else 0.0
            return dict(p=p, yaw=y, giro=1.0, tranco=(-1.8 if f == 408 else None))
        if f < 438:
            u = rampa(f, 420, 438)
            return dict(p=topo + (POS_BERCO[0] - topo) * u, yaw=0.0, giro=1.0, ruido=1.0 - 0.7 * u)
        return dict(p=POS_BERCO[0], yaw=0.0, giro=1.0 - rampa(f, 438, 462), preso=True)
    return dict(p=POS_BERCO[0], yaw=0.0, giro=0.0, preso=True)


# ---------------------------------------------------------------- L1 (logístico com placa em pêndulo)
L_CURVA = (Vector((-5.5, -4.5, 3.0)), Vector((-3.4, -1.0, 3.3)), Vector((-2.4, 3.6, 3.4)), Vector((1.8, 6.6, 3.0)))


def plano_L1(f):
    if 97 <= f <= 192:
        u = 0.15 + 0.85 * lin(f, 97, 192) ** 0.95
        p = bez(*L_CURVA, u)
        d = bez(*L_CURVA, min(1, u + 0.02)) - bez(*L_CURVA, max(0, u - 0.02))
        return dict(p=p, yaw=heading(d, 0.0), giro=1.0, ruido=0.7)
    return dict(p=POS_BERCO[1], yaw=0.0, giro=0.0, preso=True)


# ---------------------------------------------------------------- D1 (defesa): órbita, tiros, derrubado
ORB_R, ORB_Z = 3.0, 2.3
TH0 = math.atan2(DIR_D.y, DIR_D.x) - 1.2
TIROS = [f for a in (312, 336, 360) for f in range(a, a + 10, 2)] + list(range(486, 494, 2))
MORDIDA = 499


def orbita(f):
    th = TH0 + PI * (f - 289) / 96
    return SP + Vector((math.cos(th) * ORB_R, math.sin(th) * ORB_R, ORB_Z))


Q0 = SP + DIR_D * 2.6 + Vector((0, 0, 1.7))
Q1 = SP + DIR_D * 1.35 + Vector((0, 0, 0.95))
V_QUEDA = -DIR_D * -0.9 + Vector((0.6 * -DIR_D.y, 0.6 * DIR_D.x, 1.5))
A_QUEDA = -6.5
T_IMP = (V_QUEDA.z + math.sqrt(V_QUEDA.z ** 2 + 2 * -A_QUEDA * (Q1.z - 0.1))) / -A_QUEDA
F_IMP = MORDIDA + int(round(T_IMP * FPS))


def pos_queda(f):
    t = (f - MORDIDA) * DT
    return Q1 + V_QUEDA * t + Vector((0, 0, 0.5 * A_QUEDA * t * t))


def plano_D1(f):
    if 289 <= f <= 384:
        p = orbita(f)
        tiro = f in TIROS
        dirt = (CENTRO_AR - p).normalized()
        return dict(p=p, yaw=heading(SP - p, 0.0), giro=1.0, ruido=0.8, impulso=(-dirt * 0.09) if tiro else None)
    if 481 <= f < MORDIDA:
        u = rampa(f, 481, 494)
        p = Q0 + (Q1 - Q0) * u
        tiro = f in TIROS
        dirt = (CENTRO_AR - p).normalized()
        return dict(p=p, yaw=heading(SP - p, 0.0), giro=1.0, ruido=0.8, impulso=(-dirt * 0.09) if tiro else None)
    if MORDIDA <= f <= F_IMP:
        t = (f - MORDIDA) * DT
        caos = min(1.0, t * 2.5)
        fase = 9.0 * t + 6 * t * t
        ex = Vector((math.cos(fase), math.sin(fase))) * 0.75 * caos
        return dict(p=pos_queda(f), yaw=heading(SP - Q1, 0.0) + 2.0 * t + 14 * t * t, giro=0.85, ruido=2.0,
                    tilt_extra=ex, impulso=(-DIR_D * 0.6 + Vector((0, 0, 0.4))) if f == MORDIDA else None)
    return dict(p=pos_queda(F_IMP), yaw=0.0, giro=0.0, preso=True)


sim_R1 = {}
for nome, a, b in BLOCOS:
    sim_R1.update(simular(plano_R1, a, b, seed=1))
sim_L1 = {}
for nome, a, b in BLOCOS:
    sim_L1.update(simular(plano_L1, a, b, seed=2))
sim_D1 = {}
sim_D1.update(simular(plano_D1, 289, 384, seed=3))
sim_D1.update(simular(plano_D1, 481, F_IMP, seed=4, w_t=7.0, z_t=0.15, w_y=12, z_y=0.1))
for f in range(1, N + 1):                                                  # fora dos blocos dele: parado na órbita
    if f not in sim_D1:
        P = plano_D1(289)
        sim_D1[f] = (P['p'], quat_de(Vector((0, 0)), P['yaw']), dict(giro=0.0, preso=True))
gravar_drone(R1, sim_R1)
gravar_drone(L1, sim_L1)
gravar_drone(D1, sim_D1)
VIS_D1 = lambda f: (289 <= f <= 384) or (481 <= f < F_IMP)
VIS_L1 = lambda f: not (193 <= f <= 384)
VIS_R1 = lambda f: True


def mundo(sim, f, local):
    p, q, _ = sim[f]
    return p + q @ Vector(local)


# ================================================================== rotores, discos, LEDs, olho
def gravar_rotores(D, sim, nome_dano=None):
    ang = [0.0] * 4
    mat_op = D['borrao'].node_tree.nodes['Opacidade'].outputs[0]
    for f in range(1, N + 1):
        P = sim[f][2]
        g = P.get('giro', 0.0)
        dano = nome_dano and MORDIDA <= f
        for k, ro in enumerate(D['rotores']):
            gk = g
            if dano and k == 0:
                gk = 0.25 + 0.15 * math.sin(f * 1.7)
            ang[k] += gk * 2.3 * ro['sentido']
            wob = (0.18 * math.sin(f * 2.9), 0.18 * math.cos(f * 2.9)) if (dano and k == 0) else (0.0, 0.0)
            ro.rotation_euler = (wob[0], wob[1], ang[k])
            chave(ro, 'rotation_euler', f)
        chave_val(mat_op, 0.62 * rampa(g, 0.45, 0.95), f)
    for pa_ in D['pas']:
        pa_.cycles.motion_steps = 4                                       # borrão de giro de verdade (motion blur)


gravar_rotores(R1, sim_R1)
gravar_rotores(L1, sim_L1)
gravar_rotores(D1, sim_D1, nome_dano=True)

# LEDs piscando (todos os materiais de LED, inclusive as cópias do holograma)
leds = [M['led_v'], M['led_a']] + [m for k, m in _hc.items() if k in ('led_v', 'led_a')]
for f in range(1, N + 1, 2):
    on = (f // 6) % 4 == 0 or (f // 6) % 4 == 2 and (f % 6) < 2
    for m in leds:
        chave_val(DM.forca_de(m), 9.0 if on else 0.8, f)

# ================================================================== SPAWN: holograma vermelho
FRENTE0, FRENTE1 = TOPO_FAB, TOPO_FAB + 0.38


def z_holo(f):
    if f < 8:
        return FRENTE0 - 0.002
    if f > 96:
        return 60.0
    return FRENTE0 + (FRENTE1 - FRENTE0) * lin(f, 8, 58)


def z_sol(f):
    if f < 46:
        return FRENTE0 - 0.05
    if f > 96:
        return 60.0
    return FRENTE0 - 0.004 + (FRENTE1 - FRENTE0 + 0.004) * lin(f, 46, 80)


def frente(f):
    return z_holo(f) if f <= 58 else z_sol(f)


bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=0.43)
disco = peca('holo_grade_movel', bm, 'grade_holo')
bm = bmesh.new()
toro(bm, (0, 0, 0), 0.43, 0.005, nR=64)
aro = peca('holo_aro_movel', bm, 'emissor', disco)
bm = bmesh.new()
for v in ((0, 0, 0), (1, -0.5, 0), (1, 0.5, 0)):
    bm.verts.new(v)
bm.faces.new(bm.verts[:])
me_tri = bpy.data.meshes.new('triangulo')
bm.to_mesh(me_tri)
bm.free()


me_tris = {}


def leque(nome, chave_m):
    if chave_m not in me_tris:
        me = me_tri.copy()
        me.materials.append(M[chave_m])
        me_tris[chave_m] = me
    o = bpy.data.objects.new(nome, me_tris[chave_m])
    DM.COL[0].objects.link(o)
    o.rotation_mode = 'QUATERNION'
    return o


def apontar_leque(o, apice, e0, e1):
    Y = (e1 - e0)
    L = Y.length
    Y.normalize()
    X = (e0 + e1) / 2 - apice
    xy = X.dot(Y)
    Xp = X - Y * xy
    Z = Xp.normalized().cross(Y).normalized()
    R = Matrix((Xp.normalized(), Y, Z)).transposed()
    o.location = apice + Y * xy
    o.rotation_quaternion = R.to_quaternion()
    o.scale = (Xp.length, L, 1.0)


feixes = [leque('holo_feixe%d' % j, 'feixe') for j in range(3)]
luz_holo = luz('holo_luz', 'POINT', (1.0, 0.04, 0.02), 0.0, 0.2, None, POS_FAB)
for f in range(1, N + 1):
    zh, zs, zf = z_holo(f), z_sol(f), frente(f)
    e_holo.location = (FAB.x, FAB.y, zh)
    e_sol.location = (FAB.x, FAB.y, zs)
    chave(e_holo, 'location', f)
    chave(e_sol, 'location', f)
    for s in FANTASMAS:
        chave_val(s, rampa(f, 2, 10) * (1 - rampa(f, 78, 90)), f) if f <= 100 else None
    vis = 4 <= f <= 82
    disco.location = (FAB.x, FAB.y, zf)
    chave(disco, 'location', f)
    mostrar([disco, aro], f, vis)
    for j, o in enumerate(feixes):
        ap = E['projetores'][j]
        d = (Vector((FAB.x, FAB.y, zf)) - ap)
        lat = Vector((-d.y, d.x, 0)).normalized()
        c = Vector((FAB.x, FAB.y, zf))
        apontar_leque(o, ap, c - lat * 0.38, c + lat * 0.38)
        chave(o, 'location', f)
        chave(o, 'rotation_quaternion', f)
        chave(o, 'scale', f)
        mostrar([o], f, vis)
    luz_holo.location = (FAB.x, FAB.y, zf + 0.05)
    chave(luz_holo, 'location', f)
    luz_holo.data.energy = 25.0 * (rampa(f, 3, 8) * (1 - rampa(f, 78, 86))) if f <= 96 else 0.0
    luz_holo.data.keyframe_insert('energy', frame=f)
m_fab_f = next(n for n in m_fab.node_tree.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 1.2) < 1e-3).inputs[1]
for f in range(1, N + 1, 2):
    chave_val(m_fab_f, 1.2 + 5.0 * (rampa(f, 2, 8) * (1 - rampa(f, 80, 92)) if f <= 96 else 0.0), f)
# olho do R1 acende quando vira matéria
olho_R1 = DM.forca_de(R1['olho'].data.materials[0])
cristal_R1 = DM.forca_de(_hc['cristal'])
for f in (1, 76, 84, 97, N):
    chave_val(olho_R1, 0.0 if f <= 76 else 14.0, f)
    chave_val(cristal_R1, 0.0 if f <= 70 else 1.6, f)

# ================================================================== braço de solda (IK) + faíscas + scan
L1_B, L2_B = 0.11, 0.131


def ik_braco(alvo_turret):
    """IK planar no plano do giro. alvo no referencial do giro. Devolve (yaw, alfa ombro, beta cotovelo)."""
    v = Vector(alvo_turret) - Vector((0, 0, -0.034))
    yaw = math.atan2(v.y, v.x)
    d = math.hypot(v.x, v.y)
    dz = v.z
    D_ = min(L1_B + L2_B - 1e-4, math.hypot(d, dz))
    phi = math.atan2(-dz, d)
    g = math.acos(max(-1, min(1, (L1_B ** 2 + D_ ** 2 - L2_B ** 2) / (2 * L1_B * D_))))
    alfa = phi - g
    beta = PI - math.acos(max(-1, min(1, (L1_B ** 2 + L2_B ** 2 - D_ ** 2) / (2 * L1_B * L2_B))))
    return yaw, alfa, beta


GUARDADO = (0.0, 0.12, 2.75)


def rot_y(a):
    return Matrix.Rotation(a, 3, 'Y')


def orientar_pistao(camisa, haste, a, b):
    """Camisa presa em a apontando para b; haste presa em b apontando para a (no referencial do pai)."""
    d = (b - a)
    camisa.location = a
    camisa.rotation_quaternion = d.to_track_quat('Z', 'Y')
    haste.location = b
    haste.rotation_quaternion = (-d).to_track_quat('Z', 'Y')


def gravar_braco_solda(D, sim):
    giro, omb, cot = D['giro'], D['ombro'], D['cotovelo']
    for o in (giro, omb, cot):
        o.rotation_mode = 'XYZ'
    (c1, h1), (c2, h2) = D['pistoes']
    arco_f = DM.forca_de(D['arco'].data.materials[0])
    for f in range(1, N + 1):
        p, q, P = sim[f]
        pose = GUARDADO
        solda = 0.0
        if 193 <= f <= 288:
            W = ponto_solda(progresso(f)) + Vector((0, 0, 0.004))
            loc = q.inverted() @ (W - p) - Vector((0.035, 0, -0.066))
            alvo = ik_braco(loc)
            u = rampa(f, 194, 206) * (1 - rampa(f, 263, 274))
            pose = tuple(GUARDADO[i] + (alvo[i] - GUARDADO[i]) * u for i in range(3))
            if 206 <= f <= 262:
                solda = 1.0 if (f - 206) % 6 < 4 else 0.25
        giro.rotation_euler = (0, 0, pose[0])
        omb.rotation_euler = (0, pose[1], 0)
        cot.rotation_euler = (0, pose[2], 0)
        for o in (giro, omb, cot):
            chave(o, 'rotation_euler', f)
        # pistão do ombro (no giro): olhal na base → olhal no braço superior
        a = Vector((-0.026, 0, -0.02))
        b = Vector((0, 0, -0.034)) + rot_y(pose[1]) @ Vector((0.05, 0, 0.013))
        orientar_pistao(c1, h1, a, b)
        a2 = Vector((0.02, 0, -0.013))
        b2 = Vector((0.11, 0, 0)) + rot_y(pose[2]) @ Vector((0.035, 0, -0.011))
        orientar_pistao(c2, h2, a2, b2)
        for o in (c1, h1, c2, h2):
            chave(o, 'location', f)
            chave(o, 'rotation_quaternion', f)
        cint = solda * (0.7 + 0.3 * math.sin(f * 2.3))
        chave_val(arco_f, 140.0 * cint, f)
        D['luz_arco'].data.energy = 60.0 * cint
        D['luz_arco'].data.keyframe_insert('energy', frame=f)
        D['arco'].hide_render = cint < 0.05
        chave(D['arco'], 'hide_render', f)


gravar_braco_solda(R1, sim_R1)
for o in (VR['giro'], VR['ombro'], VR['cotovelo']):
    o.rotation_mode = 'XYZ'
VR['giro'].rotation_euler = (0, 0, 0.6)
VR['ombro'].rotation_euler = (0, 0.3, 0)
VR['cotovelo'].rotation_euler = (0, 1.0, 0)
orientar_pistao(*VR['pistoes'][0], Vector((-0.026, 0, -0.02)), Vector((0, 0, -0.034)) + rot_y(0.3) @ Vector((0.05, 0, 0.013)))
orientar_pistao(*VR['pistoes'][1], Vector((0.02, 0, -0.013)), Vector((0.11, 0, 0)) + rot_y(1.0) @ Vector((0.035, 0, -0.011)))
VR['arco'].hide_render = True
for D in (VR,):
    pass

# progresso da solda e cura da rachadura B
for f in range(1, N + 1):
    w = progresso(f) if 193 <= f <= 288 else (0.0 if f < 193 else 1.0)
    e_solda.location = ponto_solda(w) + (DIR_A * 0.004)
    e_solda.rotation_euler = (0, 0, ANG_A)
    chave(e_solda, 'location', f)
    chave(e_solda, 'rotation_euler', f)


def z_scan(f):
    if not (193 <= f <= 288):
        return -50.0
    return 0.6 + 0.52 * math.cos(2 * PI * (f - 193) / 46)


for f in range(1, N + 1):
    e_scan.location = (MQ.x, MQ.y, z_scan(f))
    chave(e_scan, 'location', f)
    if f < 239:
        zc = 2.0
    elif f <= 262:
        zc = z_scan(f)
    else:
        zc = -1.0
    if f > 288:
        zc = -1.0
    e_cura.location = (MQ.x, MQ.y, zc)
    chave(e_cura, 'location', f)
# folha de laser em volta da máquina + leque do olho até a borda do plano
bm = bmesh.new()
for sx, sy, w, h in ((0, -1, 1.36, 0.1), (0, 1, 1.36, 0.1), (-1, 0, 0.1, 1.16), (1, 0, 0.1, 1.16)):
    caixa(bm, (sx * 0.63, sy * 0.63, 0), (w, h, 0.002))
folha = peca('scan_folha', bm, 'folha_scan')
leques = [leque('scan_leque%d' % j, 'leque') for j in range(4)]
CANTOS = [Vector((-0.57, -0.57, 0)), Vector((0.57, -0.57, 0)), Vector((0.57, 0.57, 0)), Vector((-0.57, 0.57, 0))]
luz_scan = luz('scan_luz', 'POINT', (1.0, 0.04, 0.02), 0.0, 0.3, None, MQ)
for f in range(1, N + 1):
    z = z_scan(f)
    ativo = z > -10
    folha.location = (MQ.x, MQ.y, z)
    chave(folha, 'location', f)
    mostrar([folha] + leques, f, ativo)
    if ativo:
        olho = mundo(sim_R1, f, (0.165, 0, 0))
        for j, o in enumerate(leques):
            e0 = MQ + CANTOS[j] + Vector((0, 0, z))
            e1 = MQ + CANTOS[(j + 1) % 4] + Vector((0, 0, z))
            apontar_leque(o, olho, e0, e1)
            chave(o, 'location', f)
            chave(o, 'rotation_quaternion', f)
            chave(o, 'scale', f)
    luz_scan.location = (MQ.x, MQ.y - 0.8, max(z, 0.2))
    chave(luz_scan, 'location', f)
    luz_scan.data.energy = 30.0 if ativo else 0.0
    luz_scan.data.keyframe_insert('energy', frame=f)

# faíscas da solda (riscos alongados ao longo da velocidade)
bm = bmesh.new()
cil(bm, Vector((0, 0, -0.5)), 0.5, 1.0, lados=5)
me_faisca = bpy.data.meshes.new('faisca')
bm.to_mesh(me_faisca)
bm.free()
me_faisca.materials.append(M['faisca'])


def faisca_obj(nome):
    o = bpy.data.objects.new(nome, me_faisca)
    DM.COL[0].objects.link(o)
    o.rotation_mode = 'QUATERNION'
    return o


def gravar_faiscas(pool, eventos, vel_base, espalha, vida=10, gravidade=-9.8):
    """eventos: lista (f0, ponto, normal). Cada faísca nasce num evento e voa em arco; risco orientado."""
    random.seed(len(pool) * 7 + len(eventos))
    plano = {}
    for i, o in enumerate(pool):
        plano[o] = []
    k = 0
    for f0, pt, nrm in eventos:
        for _ in range(4):
            o = pool[k % len(pool)]
            k += 1
            v = (Vector(nrm) * vel_base + Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * espalha)
            plano[o].append((f0, pt.copy(), v, random.randint(vida // 2, vida)))
    for o, lst in plano.items():
        lst.sort(key=lambda x: x[0])
        for f in range(1, N + 1):
            vivo = None
            for (f0, pt, v, vd) in lst:
                if f0 <= f < f0 + vd:
                    vivo = (f0, pt, v, vd)
            if vivo:
                f0, pt, v, vd = vivo
                t = (f - f0) * DT
                vv = v + Vector((0, 0, gravidade * t))
                o.location = pt + v * t + Vector((0, 0, 0.5 * gravidade * t * t))
                o.rotation_quaternion = vv.to_track_quat('Z', 'Y')
                o.scale = (0.006, 0.006, max(0.012, min(0.09, vv.length * DT * 1.2)))
            else:
                o.scale = (0.004, 0.004, 0.01)
            chave(o, 'location', f)
            chave(o, 'rotation_quaternion', f)
            chave(o, 'scale', f)
            o.hide_render = vivo is None
            chave(o, 'hide_render', f)


ev_solda = [(f, ponto_solda(progresso(f)) + Vector((0, 0, 0.006)), (0, 0, 1)) for f in range(206, 263) if (f - 206) % 6 < 4]
gravar_faiscas([faisca_obj('faisca_solda%d' % i) for i in range(28)], ev_solda, 1.2, 0.9, vida=9)

# ================================================================== fumaça da máquina (diminui com o reparo)


def esfera_vol(nome, chave_m):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    return peca(nome, bm, chave_m)


def fum_maq(f):
    if f < 206:
        return 1.0
    return max(0.12, 1.0 - lin(f, 206, 272) * 0.88)


fumacas_m = [esfera_vol('fumaca_maq%d' % i, 'fumaca') for i in range(10)]
FONTES = [(MQ + Vector((0.38, 0.38, 1.5)), 1.0), (PTS_A[7], 0.6)]
for f in range(1, N + 1):
    k_ = fum_maq(f)
    for i, o in enumerate(fumacas_m):
        src, peso = FONTES[i % 2]
        u = (i / len(fumacas_m) + f / 70.0) % 1.0
        o.location = src + Vector((0.5 * u * u + 0.05 * math.sin(i), 0.2 * u, 1.2 * u + 0.05))
        s = (0.05 + 0.32 * u) * (0.35 + 0.65 * k_) * peso
        o.scale = [max(0.03, s)] * 3
        o.rotation_euler = (i, u * 2, i * 0.5)
        chave(o, 'location', f)
        chave(o, 'scale', f)
        chave(o, 'rotation_euler', f)
        o.hide_render = s < 0.035 or (f > 206 and i % 2 == 1 and k_ < 0.4)
        chave(o, 'hide_render', f)

# ================================================================== COMBATE: torre, traçantes, clarões, mira


def mira_torre(sim, f):
    p, q, _ = sim[f]
    base = p + q @ Vector((0, 0, -0.111))
    v = q.inverted() @ (CENTRO_AR - base)
    return math.atan2(v.y, v.x), math.atan2(-v.z, math.hypot(v.x, v.y))


def boca(sim, f, yaw_t, pitch_t, idx):
    p, q, _ = sim[f]
    Mx = (Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation((0, 0, -0.066)) @ Matrix.Rotation(yaw_t, 4, 'Z')
          @ Matrix.Translation((0, 0, -0.045)) @ Matrix.Rotation(pitch_t, 4, 'Y'))
    return Mx @ D1['muzzle'][idx]


tracantes = []
for i in range(6):
    tr = vazio('tracante%d' % i)
    tr.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -0.2)), 0.006, 0.4, lados=8)
    peca('tracante_nucleo%d' % i, bm, 'tiro', tr)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, -0.22)), 0.016, 0.44, lados=10)
    peca('tracante_halo%d' % i, bm, 'halo', tr)
    tracantes.append(tr)
luz_imp = luz('impacto_luz', 'POINT', (1.0, 0.25, 0.05), 0.0, 0.1, None, CENTRO_AR)
torre, canhao = D1['torre'], D1['canhao']
yaw_prev = None
impactos = []
for f in range(1, N + 1):
    if VIS_D1(f):
        yt, pt_ = mira_torre(sim_D1, f)
    else:
        yt, pt_ = 0.0, 0.3
    if f >= MORDIDA:
        yt, pt_ = yt + 0.6 * math.sin(f), 0.5
    torre.rotation_euler = (0, 0, yt)
    canhao.rotation_euler = (0, pt_, 0)
    chave(torre, 'rotation_euler', f)
    chave(canhao, 'rotation_euler', f)
    fl = f in TIROS
    D1['flash'].hide_render = not fl
    chave(D1['flash'], 'hide_render', f)
    D1['luz_flash'].data.energy = 80.0 if fl else 0.0
    D1['luz_flash'].data.keyframe_insert('energy', frame=f)
    D1['flash'].scale = (1.0, 1.0, 1.0) if fl else (0.3, 0.3, 0.3)
    chave(D1['flash'], 'scale', f)
# traçantes: do cano ao alvo em 4 quadros
random.seed(21)
voos = []
for n, fs in enumerate(TIROS):
    yt, pt_ = mira_torre(sim_D1, fs)
    m0 = boca(sim_D1, fs, yt, pt_, n % 2)
    H = CENTRO_AR + Vector((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), random.uniform(-0.15, 0.2))) - DIR_D * 0.0
    H = H + (m0 - H).normalized() * 0.32
    voos.append((fs, m0, H))
    impactos.append((fs + 4, H, (m0 - H).normalized()))
for i, tr in enumerate(tracantes):
    meus = voos[i::len(tracantes)]
    for f in range(1, N + 1):
        ativo = None
        for (fs, m0, H) in meus:
            if fs <= f < fs + 4:
                ativo = (fs, m0, H)
        if ativo:
            fs, m0, H = ativo
            u = (f - fs + 1) / 4
            d = (H - m0)
            tr.location = m0 + d * u
            tr.rotation_quaternion = d.to_track_quat('Z', 'Y')
        mostrar([tr] + list(tr.children), f, ativo is not None)
        chave(tr, 'location', f)
        chave(tr, 'rotation_quaternion', f)
for f in range(1, N + 1):
    e = [im for im in impactos if im[0] <= f < im[0] + 2]
    luz_imp.data.energy = 120.0 if e else 0.0
    if e:
        luz_imp.location = e[0][1] + e[0][2] * 0.15
    luz_imp.data.keyframe_insert('energy', frame=f)
    chave(luz_imp, 'location', f)
gravar_faiscas([faisca_obj('faisca_impacto%d' % i) for i in range(32)], impactos, 2.2, 1.4, vida=8)
# cápsulas ejetadas a cada tiro: caem girando e ficam no chão até o fim do bloco
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.0045, 0.016, lados=8)
me_cap = bpy.data.meshes.new('capsula')
bm.to_mesh(me_cap)
bm.free()
me_cap.materials.append(M['cobre'])
random.seed(31)
for n, fs in enumerate(TIROS):
    o = bpy.data.objects.new('capsula%d' % n, me_cap)
    DM.COL[0].objects.link(o)
    o.rotation_mode = 'XYZ'
    yt, pt_ = mira_torre(sim_D1, fs)
    p, q, _ = sim_D1[fs]
    Mx = (Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation((0, 0, -0.066)) @ Matrix.Rotation(yt, 4, 'Z')
          @ Matrix.Translation((0, 0, -0.045)) @ Matrix.Rotation(pt_, 4, 'Y'))
    p0 = Mx @ Vector((0.03, -0.036, 0.004))
    v0 = (Mx.to_3x3() @ Vector((random.uniform(-0.2, 0.2), -1.4, 0.5))) + Vector((0, 0, 0.3))
    fim = 384 if fs <= 384 else MORDIDA + 40
    w = Vector((random.uniform(-30, 30), random.uniform(-30, 30), random.uniform(-10, 10)))
    for f in range(1, N + 1):
        t = (f - fs) * DT
        vivo = fs <= f <= fim
        if vivo:
            pos = p0 + v0 * t + Vector((0, 0, -4.9 * t * t))
            if pos.z <= 0.005:
                tc = (v0.z + math.sqrt(v0.z ** 2 + 2 * 9.8 * (p0.z - 0.005))) / 9.8
                pos = p0 + v0 * tc + Vector((0, 0, -4.9 * tc * tc))
                pos.z = 0.005
                o.rotation_euler = (PI / 2, 0, w.z * tc)
            else:
                o.rotation_euler = tuple(w * t)
            o.location = pos
        chave(o, 'location', f)
        chave(o, 'rotation_euler', f)
        mostrar([o], f, vivo)
# clarão do impacto (estrela) que aparece 2 quadros
bm = bmesh.new()
for j in range(8):
    d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
    tubo(bm, Vector((0, 0, 0)), d * random.uniform(0.08, 0.16), 0.008, 4)
esfera(bm, Vector((0, 0, 0)), 0.035, 8)
estrela = peca('impacto_clarao', bm, 'clarão')
for f in range(1, N + 1):
    e = [im for im in impactos if im[0] <= f < im[0] + 2]
    if e:
        estrela.location = e[0][1]
    chave(estrela, 'location', f)
    mostrar([estrela], f, bool(e))
# laser e mira vermelha travando no alvo
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.5)), 0.0035, 1.0, lados=6)
laser = peca('laser_mira', bm, 'laser')
laser.rotation_mode = 'QUATERNION'
bm = bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1):
        c = Vector((sx * 0.5, sy * 0.5, 0))
        caixa(bm, c - Vector((sx * 0.08, 0, 0)), (0.16, 0.025, 0.006))
        caixa(bm, c - Vector((0, sy * 0.08, 0)), (0.025, 0.16, 0.006))
for j in range(12):
    if j % 3 != 2:
        a0 = j * PI / 6
        for t in range(4):
            a = a0 + t * (PI / 6) / 4
            caixa(bm, Vector((math.cos(a) * 0.38, math.sin(a) * 0.38, 0)), (0.02, 0.05, 0.004), Matrix.Rotation(a, 3, 'Z'))
for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    caixa(bm, Vector((sx * 0.18, sy * 0.18, 0)), (0.12 if sx else 0.02, 0.12 if sy else 0.02, 0.004))
mira = peca('mira_alvo', bm, 'mira')
mira.rotation_mode = 'QUATERNION'
for f in range(1, N + 1):
    ativo = (291 <= f <= 384) or (481 <= f < MORDIDA)
    if ativo:
        p = sim_D1[f][0]
        d = (p - CENTRO_AR)
        trava = rampa(f, 291, 308) if f <= 384 else rampa(f, 481, 489)
        s = 1.9 - 0.95 * trava
        giro_m = (1 - trava) * 3.0 + f * 0.01
        mira.location = CENTRO_AR + d.normalized() * 0.6
        mira.rotation_quaternion = d.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), giro_m)
        mira.scale = (s, s, s)
        olho = mundo(sim_D1, f, (0.18, 0, 0))
        dl = CENTRO_AR - olho
        laser.location = olho
        laser.rotation_quaternion = dl.to_track_quat('Z', 'Y')
        laser.scale = (1, 1, dl.length - 0.2)
    for o in (mira, laser):
        chave(o, 'location', f)
        chave(o, 'rotation_quaternion', f)
        chave(o, 'scale', f)
    mostrar([mira], f, ativo)
    mostrar([laser], f, ativo and (f >= 308 or 489 <= f))
# aranha: respira, tranco nos acertos, bote no drone (mordida)
for f in range(1, N + 1):
    bob = 0.02 * math.sin(f * 0.35)
    hit = any(im[0] <= f < im[0] + 3 for im in impactos)
    bote = math.sin(PI * lin(f, MORDIDA - 6, MORDIDA + 6)) if MORDIDA - 6 <= f <= MORDIDA + 6 else 0.0
    aranha_piv.location = SP + DIR_D * (0.45 * bote) + Vector((0, 0, bob + 0.12 * bote))
    tilt = -0.32 * bote + (0.04 * math.sin(f * 3) if hit else 0.0)
    eixo = Vector((-DIR_D.y, DIR_D.x, 0))
    aranha_piv.rotation_euler = Quaternion(eixo, tilt).to_euler('XYZ')
    chave(aranha_piv, 'location', f)
    chave(aranha_piv, 'rotation_euler', f)

# ================================================================== DERRUBADO: fumaça, queda girando, sucata
QC = pos_queda(F_IMP)
QC.z = 0.0
SU_raiz = SU['raiz']
SU_raiz.location = QC + Vector((0, 0, 0.1))
SU_raiz.rotation_quaternion = Euler((0.42, -0.25, 1.1)).to_quaternion()
duto0 = SU['dutos'][0]
rot0 = SU['rotores'][0]
bpy.context.view_layer.update()
for o in (duto0, rot0, SU['pas'][0], SU['discos'][0]):
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
for o in (duto0, rot0):
    o.location = QC + Vector((0.45, -0.3, 0.06 if o == duto0 else 0.05))
    o.rotation_mode = 'XYZ'
    o.rotation_euler = (1.25, 0.2, 0.6)
SU['pas'][0].parent = rot0
SU['pas'][0].matrix_parent_inverse = Matrix.Identity(4)
SU['pas'][0].location = (0, 0, 0)
SU['discos'][0].hide_render = True
SU['borrao'].node_tree.nodes['Opacidade'].outputs[0].default_value = 0.0
DM.forca_de(SU['olho'].data.materials[0])
bpy.context.view_layer.update()
zmin = min((o.matrix_world @ Vector(c)).z for o in descendentes(SU_raiz) if o.type == 'MESH' for c in o.bound_box)
SU_raiz.location.z += -zmin - 0.01
for o in SU['rotores'][1:]:
    o.rotation_mode = 'XYZ'
    o.rotation_euler = (0, 0, random.uniform(0, 6))
bm = bmesh.new()
for k in range(6):
    mancha(bm, (QC.x + random.uniform(-0.5, 0.5), QC.y + random.uniform(-0.5, 0.5)), random.uniform(0.15, 0.35), 0.003)
peca('sucata_queimado', bm, 'fuligem')
bm = bmesh.new()
for k in range(14):
    pedra(bm, QC + Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), 0.01)), random.uniform(0.008, 0.02), 0.3)
peca('sucata_cacos', bm, 'blindado')
olho_su = SU['olho'].data.materials[0].copy()
SU['olho'].data.materials[0] = olho_su
em_su = DM.forca_de(olho_su)
lista_su = descendentes(SU_raiz) + [duto0, rot0, SU['pas'][0], bpy.data.objects['sucata_queimado'], bpy.data.objects['sucata_cacos']]
lista_D1 = descendentes(D1['raiz'])
for f in range(1, N + 1):
    mostrar(lista_su, f, f >= F_IMP)
    mostrar(lista_D1, f, VIS_D1(f))
    chave_val(em_su, (6.0 if (f // 3) % 3 else 0.5) * (1 - lin(f, F_IMP, F_IMP + 40)), f)
lista_L1 = descendentes(L1['raiz'])
for f in range(1, N + 1):
    mostrar(lista_L1, f, VIS_L1(f))
    mostrar([L1['carga']], f, VIS_L1(f) and 97 <= f <= 192)
# rastro de fumaça da queda + fumaça da sucata + poeira do impacto
rastro = [esfera_vol('fumaca_rastro%d' % i, 'fumaca_rastro') for i in range(16)]
for i, o in enumerate(rastro):
    fb = MORDIDA + 1 + i * 2
    if fb > F_IMP:
        fb = F_IMP + (i - (F_IMP - MORDIDA) // 2) * 4
    for f in range(1, N + 1):
        if f < fb or fb >= N:
            mostrar([o], f, False)
            chave(o, 'location', f)
            chave(o, 'scale', f)
            continue
        idade = (f - fb) * DT
        if idade > 1.0:                                                   # dissipou
            mostrar([o], f, False)
            chave(o, 'location', f)
            chave(o, 'scale', f)
            continue
        if fb <= F_IMP:
            base = mundo(sim_D1, fb, (0.27 * math.cos(PI / 4), 0.27 * math.sin(PI / 4), 0.0))
        else:
            base = QC + Vector((0.1, 0.05, 0.1))
        o.location = base + Vector((0.2 * idade, 0.08 * idade, 0.3 * idade))
        s = min(0.42, 0.09 + 0.3 * idade)
        o.scale = (s, s, s * 1.2)
        o.rotation_euler = (i, idade, i * 0.3)
        mostrar([o], f, True)
        chave(o, 'location', f)
        chave(o, 'scale', f)
        chave(o, 'rotation_euler', f)
fumaca_su = [esfera_vol('fumaca_sucata%d' % i, 'fumaca_fina') for i in range(6)]
for i, o in enumerate(fumaca_su):
    for f in range(1, N + 1):
        ativo = f >= F_IMP + 4
        u = (i / 6 + (f - F_IMP) / 60.0) % 1.0
        o.location = QC + Vector((0.05 + 0.3 * u * u, 0.1 * u, 0.12 + 1.0 * u))
        s = 0.05 + 0.2 * u
        o.scale = (s, s, s)
        mostrar([o], f, ativo)
        chave(o, 'location', f)
        chave(o, 'scale', f)
ev_queda = [(MORDIDA, mundo(sim_D1, MORDIDA, (0.19, 0.19, 0)), (0, 0, 1)), (MORDIDA + 1, mundo(sim_D1, MORDIDA + 1, (0.19, 0.19, 0)), (0, 0, 1))]
ev_queda += [(f, mundo(sim_D1, f, (0.19, 0.19, 0)), (0, 0, 0.3)) for f in range(MORDIDA + 3, F_IMP, 5)]
ev_queda += [(F_IMP, QC + Vector((0, 0, 0.1)), (0, 0, 1)), (F_IMP + 1, QC + Vector((0, 0, 0.1)), (0, 0, 1))]
ev_queda += [(f, QC + Vector((0.05, 0.02, 0.12)), (0, 0, 0.6)) for f in range(F_IMP + 10, N, 11)]
gravar_faiscas([faisca_obj('faisca_queda%d' % i) for i in range(24)], ev_queda, 1.6, 1.2, vida=10)
luz_q = luz('queda_luz', 'POINT', (1.0, 0.3, 0.06), 0.0, 0.2, None, QC)
for f in range(1, N + 1):
    e = 0.0
    if MORDIDA <= f < MORDIDA + 3:
        e = 150.0
        luz_q.location = mundo(sim_D1, f, (0, 0, 0.1))
    elif F_IMP <= f < F_IMP + 3:
        e = 200.0
        luz_q.location = QC + Vector((0, 0, 0.3))
    elif f > F_IMP + 3:
        e = 6.0 * (0.6 + 0.4 * math.sin(f * 1.3))
        luz_q.location = QC + Vector((0, 0, 0.2))
    luz_q.data.energy = e
    luz_q.data.keyframe_insert('energy', frame=f)
    chave(luz_q, 'location', f)

# ================================================================== pêndulo da carga (L1)
pend = L1['pendulo']
LP = 0.17
bob, bob_v = None, Vector((0, 0, 0))
for f in range(1, N + 1):
    p, q, P = sim_L1[f]
    piv = p + q @ Vector((0, 0, -0.095))
    if bob is None or P.get('preso') or f == 97:
        bob = piv + Vector((0, 0, -LP))
        bob_v = Vector((0, 0, 0))
        if f == 97:                                                         # entra balançando um pouco
            bob_v = Vector((0.5, -0.3, 0))
    else:
        for _ in range(6):
            h = DT / 6
            bob_v += Vector((0, 0, -G)) * h
            bob_v *= (1 - 0.6 * h)
            nb = bob + bob_v * h
            d = nb - piv
            nb = piv + d.normalized() * LP
            bob_v = (nb - bob) / h
            bob = nb
    d_loc = q.inverted() @ (bob - piv)
    pend.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(d_loc.normalized())
    chave(pend, 'rotation_quaternion', f)

# ================================================================== POUSO: garras, plugue, carga, braço abastecedor, luzes
def gravar_berco(i, fecha_a, fecha_b, plug_a, plug_b, sempre=False):
    for f in range(1, N + 1):
        u = 1.0 if sempre else rampa(f, fecha_a, fecha_b)
        for (g, ca, ha, anc, sy) in E['garras'][i]:
            ang = (1 - u) * 1.05
            g.rotation_euler = (-sy * ang, 0, 0)
            chave(g, 'rotation_euler', f)
            ponta = g.location + Matrix.Rotation(-sy * ang, 3, 'X') @ Vector((0, sy * 0.012, 0.018))
            orientar_pistao(ca, ha, anc, ponta)
            for o in (ca, ha):
                chave(o, 'location', f)
                chave(o, 'rotation_quaternion', f)
        v = 1.0 if sempre else rampa(f, plug_a, plug_b)
        pl = E['plugues'][i]
        B = BERCOS[i]
        pl.location = (B.x - 0.24 + 0.05 * v - 0.05, B.y, TOPO_BERCO + Z_PATIM + 0.004 - 0.015)
        chave(pl, 'location', f)


def garra_bloco(f):
    # R1: aberto antes do pouso no bloco 5; fechado no bloco 6; aberto nos demais
    if f >= 481:
        return 1.0
    if 385 <= f <= 480:
        return rampa(f, 440, 448)
    return 0.0


for f in range(1, N + 1):
    u = garra_bloco(f)
    for (g, ca, ha, anc, sy) in E['garras'][0]:
        ang = (1 - u) * 1.05
        g.rotation_euler = (-sy * ang, 0, 0)
        chave(g, 'rotation_euler', f)
        ponta = g.location + Matrix.Rotation(-sy * ang, 3, 'X') @ Vector((0, sy * 0.012, 0.018))
        orientar_pistao(ca, ha, anc, ponta)
        for o in (ca, ha):
            chave(o, 'location', f)
            chave(o, 'rotation_quaternion', f)
    v = 1.0 if f >= 481 else (rampa(f, 446, 454) if 385 <= f <= 480 else 0.0)
    pl = E['plugues'][0]
    pl.location = (BERCOS[0].x - 0.24 + 0.05 * v - 0.05, BERCOS[0].y, TOPO_BERCO + Z_PATIM + 0.004 - 0.015)
    chave(pl, 'location', f)
    # berço B: L1 estacionado → fechado quando ele está lá
    ub = 0.0 if 97 <= f <= 384 else 1.0
    for (g, ca, ha, anc, sy) in E['garras'][1]:
        ang = (1 - ub) * 1.05
        g.rotation_euler = (-sy * ang, 0, 0)
        chave(g, 'rotation_euler', f)
        ponta = g.location + Matrix.Rotation(-sy * ang, 3, 'X') @ Vector((0, sy * 0.012, 0.018))
        orientar_pistao(ca, ha, anc, ponta)
        for o in (ca, ha):
            chave(o, 'location', f)
            chave(o, 'rotation_quaternion', f)
    pl = E['plugues'][1]
    pl.location = (BERCOS[1].x - 0.24 + 0.05 * ub - 0.05, BERCOS[1].y, TOPO_BERCO + Z_PATIM + 0.004 - 0.015)
    chave(pl, 'location', f)
    # luzes de pouso: piscam na aproximação (bloco 5), fixas depois; berço B fixo
    if 385 <= f < 438:
        la = 10.0 if (f // 4) % 2 == 0 else 0.6
    else:
        la = 3.0
    chave_val(DM.forca_de(E['luzes_pouso'][0]), la, f)
    E['luz_pouso_0'].data.energy = la * 0.8
    E['luz_pouso_0'].data.keyframe_insert('energy', frame=f)
    chave_val(DM.forca_de(E['luzes_pouso'][1]), 3.0, f) if f in (1, N) else None
    # farol giratório
    E['farol'].rotation_euler = (PI / 2 - 0.25, 0, f * 0.35)
    chave(E['farol'], 'rotation_euler', f)
# barra de carga: R1 enche no bloco 5 (e fica cheia no 6); L1 sempre cheio no berço
for f in range(1, N + 1):
    if f < 385:
        c = 0.3 if f >= 97 else 0.0
        c = 1.0 if f <= 96 and f > 82 else c
    elif f <= 480:
        c = 0.15 + 0.85 * lin(f, 452, 478) if f >= 452 else 0.15
    else:
        c = 1.0
    for j, m in enumerate(R1['led_carga']):
        aceso = c >= (j + 1) / 4 - 1e-3
        pisca = (not aceso) and c >= j / 4 and (f // 4) % 2 == 0 and 452 <= f <= 480
        chave_val(DM.forca_de(m), 9.0 if aceso else (5.0 if pisca else 0.0), f)
for j, m in enumerate(L1['led_carga']):
    chave_val(DM.forca_de(m), 9.0, 1)
for D in (VR, VD, VL):
    for j, m in enumerate(D['led_carga']):
        DM.forca_de(m).default_value = 9.0 if j < 3 else 0.0
for j, m in enumerate(D1['led_carga']):
    DM.forca_de(m).default_value = 9.0 if j < 2 else 0.0
for j, m in enumerate(SU['led_carga']):
    DM.forca_de(m).default_value = 0.0

# braço abastecedor: pega um remendo na revista e larga no funil do R1 (bloco 5)
AB = E['abast']
for o in (AB['giro'], AB['ombro'], AB['cotovelo'], AB['punho']):
    o.rotation_mode = 'XYZ'
L1A, L2A = 0.32, 0.26
BASE_AB = BRACO_EST + Vector((0, 0, DECK + 0.12))


def ik_abast(alvo):
    v = alvo - BASE_AB
    yaw = math.atan2(v.y, v.x)
    d = math.hypot(v.x, v.y)
    D_ = min(L1A + L2A - 1e-3, math.hypot(d, v.z))
    phi = math.atan2(-v.z, d)
    g = math.acos(max(-1, min(1, (L1A ** 2 + D_ ** 2 - L2A ** 2) / (2 * L1A * D_))))
    beta = PI - math.acos(max(-1, min(1, (L1A ** 2 + L2A ** 2 - D_ ** 2) / (2 * L1A * L2A))))
    return yaw, phi - g, beta


FUNIL = POS_BERCO[0] + Vector((-0.072, 0, 0.075 + 0.058))
PEGA = E['remendo_topo'] + Vector((0, 0, 0.058))
REPOUSO = (PI / 2 * 0.0 + 0.0, -0.9, 2.2)
for f in range(1, N + 1):
    if 446 <= f <= 480:
        if f < 454:
            u = rampa(f, 446, 454)
            alvo = ik_abast(PEGA + Vector((0, 0, 0.1 * (1 - u))))
            pose = tuple(REPOUSO[i] + (alvo[i] - REPOUSO[i]) * u for i in range(3))
            com = False
        elif f < 470:
            u = rampa(f, 455, 469)
            arco_z = 0.12 * math.sin(PI * u)
            pt = PEGA + (FUNIL - PEGA) * u + Vector((0, 0, arco_z))
            pose = ik_abast(pt)
            com = True
        else:
            u = rampa(f, 471, 480)
            alvo = ik_abast(FUNIL + Vector((0, 0, 0.08 * u)))
            pose = tuple(alvo[i] + (REPOUSO[i] - alvo[i]) * u for i in range(3))
            com = False
    else:
        pose, com = REPOUSO, False
    AB['giro'].rotation_euler = (0, 0, pose[0])
    AB['ombro'].rotation_euler = (0, pose[1], 0)
    AB['cotovelo'].rotation_euler = (0, pose[2], 0)
    AB['punho'].rotation_euler = (0, -(pose[1] + pose[2]), 0)                 # ventosa sempre para baixo
    for o in (AB['giro'], AB['ombro'], AB['cotovelo'], AB['punho']):
        chave(o, 'rotation_euler', f)
    (c1, h1), (c2, h2) = AB['pistoes']
    orientar_pistao(c1, h1, Vector((-0.06, 0, 0.06)), Vector((0, 0, 0.12)) + rot_y(pose[1]) @ Vector((0.14, 0, -0.02)))
    orientar_pistao(c2, h2, Vector((0.05, 0, 0.02)), Vector((0.32, 0, 0)) + rot_y(pose[2]) @ Vector((0.1, 0, 0.015)))
    for o in (c1, h1, c2, h2):
        chave(o, 'location', f)
        chave(o, 'rotation_quaternion', f)
    rem = E['remendo']
    if com:
        rem.location = pt + Vector((0, 0, -0.055))
        rem.rotation_quaternion = Quaternion((0, 0, 1), pose[0])
    elif f >= 470 and f <= 480:
        rem.location = FUNIL + Vector((0, 0, -0.055))
        rem.rotation_quaternion = Quaternion((0, 0, 1), 0)
    else:
        rem.location = PEGA + Vector((0, 0, -0.055))
        rem.rotation_quaternion = Quaternion((0, 0, 1), PI / 2)
    chave(rem, 'location', f)
    chave(rem, 'rotation_quaternion', f)
    mostrar([rem], f, not (470 < f <= 480))

# ================================================================== lavagem dos rotores: poeira e capim
colecao('capim')
random.seed(17)
TUFOS = []
for k in range(260):
    if k < 150:
        a, r = random.uniform(0, 2 * PI), random.uniform(1.15, 3.4)
        c = Vector((math.cos(a) * r, math.sin(a) * r, 0))
    elif k < 230:
        c = QC + Vector((random.uniform(-1.8, 1.8), random.uniform(-1.8, 1.8), 0))
        if (c - SP).length < 1.2:
            continue
    else:
        c = Vector((random.uniform(-1, 3), random.uniform(1.2, 4), 0))
    o = vazio('tufo', None, c)
    o.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    for j in range(7):
        aa = random.uniform(0, 2 * PI)
        d = Vector((math.cos(aa), math.sin(aa), 0))
        lat = Vector((-d.y, d.x, 0))
        h = random.uniform(0.12, 0.26)
        inc = random.uniform(0.05, 0.3)
        base = d * random.uniform(0, 0.04)
        vs = []
        for s in range(4):
            t = s / 3
            p = base + d * (inc * h * t * t) + Vector((0, 0, h * t))
            w = 0.006 * (1 - t) + 0.0005
            vs.append((bm.verts.new(p - lat * w), bm.verts.new(p + lat * w)))
        for (a1, b1), (a2, b2) in zip(vs, vs[1:]):
            bm.faces.new((a1, b1, b2, a2))
    peca('tufo_folhas', bm, 'capim', o)
    TUFOS.append(o)
ATORES = [(sim_R1, VIS_R1), (sim_L1, VIS_L1), (sim_D1, VIS_D1)]
for f in range(1, N + 1):
    fontes = []
    for sim, vis in ATORES:
        if not vis(f):
            continue
        p, q, P = sim[f]
        g = P.get('giro', 0.0)
        if g < 0.3:
            continue
        fontes.append((p, g))
    for i, o in enumerate(TUFOS):
        c = o.location
        w = Vector((0.25 * math.sin(f * 0.13 + i), 0.15 * math.cos(f * 0.11 + i * 0.7), 0)) * 0.25
        for p, g in fontes:
            h = max(0.2, p.z - 0.0)
            dd = (c - p).to_2d()
            r = dd.length
            m = g * max(0.0, 1 - h / 2.8) * math.exp(-(r / (0.45 + 0.55 * h)) ** 2)
            if r > 1e-3 and m > 0.01:
                w += dd.normalized().to_3d() * (1.6 * m * (1 + 0.3 * math.sin(f * 1.9 + i)))
        ang = min(1.15, w.length)
        eixo = Vector((0, 0, 1)).cross(w) if w.length > 1e-4 else Vector((1, 0, 0))
        o.rotation_quaternion = Quaternion(eixo.normalized(), ang) if w.length > 1e-4 else Quaternion()
        chave(o, 'rotation_quaternion', f)

colecao('poeira')


def superficie(p):
    if abs(p.x) < 1.0 and abs(p.y) < 1.0:
        return DECK
    if abs(p.x - MQ.x) < 0.6 and abs(p.y - MQ.y) < 0.6:
        return None
    return 0.0


for nome, (sim, vis) in zip(('R1', 'L1', 'D1'), ATORES):
    puffs = [esfera_vol('poeira_%s%d' % (nome, i), 'poeira') for i in range(8)]
    for f in range(1, N + 1):
        p, q, P = sim[f]
        g = P.get('giro', 0.0) if vis(f) else 0.0
        zs = superficie(p)
        forca = 0.0
        if zs is not None:
            h = p.z - Z_PATIM - zs
            forca = g * max(0.0, 1 - h / 1.6) if not P.get('preso') or g > 0.5 else 0.0
        if 499 <= f and nome == 'D1':
            forca = 0.0
        for i, o in enumerate(puffs):
            u = (i / len(puffs) + f / 22.0) % 1.0
            a = i * 2 * PI / len(puffs) + 0.4 * math.sin(f * 0.05 + i)
            if zs is None:
                zs_ = 0.0
            else:
                zs_ = zs
            o.location = Vector((p.x + math.cos(a) * (0.12 + 0.8 * u), p.y + math.sin(a) * (0.12 + 0.8 * u), zs_ + 0.04 + 0.1 * u))
            s = (0.08 + 0.26 * u) * forca
            o.scale = (max(0.03, s), max(0.03, s), max(0.03, s * 0.55))
            chave(o, 'location', f)
            chave(o, 'scale', f)
            o.hide_render = s < 0.04
            chave(o, 'hide_render', f)
# poeira do impacto da sucata
bum = [esfera_vol('poeira_impacto%d' % i, 'poeira') for i in range(7)]
for i, o in enumerate(bum):
    a = i * 2 * PI / 7
    for f in range(1, N + 1):
        t = (f - F_IMP) * DT
        ativo = 0 <= t < 1.6
        o.location = QC + Vector((math.cos(a) * (0.2 + 0.9 * min(t, 0.8)), math.sin(a) * (0.2 + 0.9 * min(t, 0.8)), 0.08 + 0.2 * t))
        s = max(0.04, (0.12 + 0.45 * min(t, 1.0)) * (1 - max(0, t - 1.0) / 0.6)) if ativo else 0.05
        o.scale = (s, s, s * 0.6)
        mostrar([o], f, ativo and s > 0.045)
        chave(o, 'location', f)
        chave(o, 'scale', f)

# ================================================================== vitrine (modelos parados, para fotos)
VIT = {'reparo': (VR, Vector((-2.9, -2.0, 1.2))), 'defesa': (VD, Vector((-1.85, -2.35, 1.25))), 'logistico': (VL, Vector((-0.8, -2.7, 1.35)))}
for tipo, (D, p) in VIT.items():
    D['raiz'].location = p
    D['raiz'].rotation_quaternion = Quaternion((0, 0, 1), -1.05) @ Quaternion((1, 0, 0), 0.0)
    for k, ro in enumerate(D['rotores']):
        ro.rotation_mode = 'XYZ'
        ro.rotation_euler = (0, 0, 0.4 + k * 0.7)
if 'torre' in VD:
    VD['torre'].rotation_euler = (0, 0, 1.0)
    VD['canhao'].rotation_euler = (0, 0.15, 0)
    VD['flash'].hide_render = True
    VD['luz_flash'].data.energy = 0.0
for D in (VR, VD, VL):
    D['borrao'].node_tree.nodes['Opacidade'].outputs[0].default_value = 0.0
VL['pendulo'].rotation_quaternion = Quaternion((1, 0, 0), 0.08)
bpy.data.collections['vitrine'].hide_render = True

# interpolação: quadros já são por quadro; booleanos ficam constantes
for o in list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.materials):
    tgt = o.node_tree if isinstance(o, bpy.types.Material) else o
    ad = getattr(tgt, 'animation_data', None)
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT' if fc.data_path.startswith('hide') else 'LINEAR'

# ================================================================== luz, mundo, câmera
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 3.6
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(-35))
mundo_ = bpy.data.worlds.new('Mundo')
sc.world = mundo_
bg = mundo_.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.5
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
sc.cycles.transparent_max_bounces = 24
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -0.5
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


def pos_em(sim, f):
    return sim[f][0]


def fotos():
    p_curva = pos_em(sim_R1, 158)
    v_curva = (pos_em(sim_R1, 160) - pos_em(sim_R1, 156)).normalized()
    p_comb = pos_em(sim_D1, 340)
    mid = (p_comb + CENTRO_AR) / 2
    perp = Vector((-(p_comb - SP).y, (p_comb - SP).x, 0)).normalized()
    p_q = pos_em(sim_D1, MORDIDA + 9)
    p_R = pos_em(sim_R1, 116)
    p_dc = pos_em(sim_D1, 340)
    atras = (p_dc - CENTRO_AR).to_2d().normalized().to_3d()
    lado = Vector((-atras.y, atras.x, 0))
    p_q = pos_em(sim_D1, MORDIDA + 12)
    dq = (p_q - SP).to_2d().normalized().to_3d()
    lq = Vector((-dq.y, dq.x, 0))
    soc = ['aranha', 'maquina', 'sucata', 'efeitos', 'poeira']
    L = [
        ('drones_modelos', 520, (-0.9, -5.3, 2.0), (-1.55, -1.25, 0.95), 31, True, 3.6, soc),
        ('drones_spawn', 64, (-0.15, -1.95, 1.45), (FAB.x, FAB.y, TOPO_FAB + 0.16), 40, False, 1.4, []),
        ('drones_decolagem', 116, (-2.1, -1.8, 1.15), (FAB.x, 0.05, 1.05), 38, False, 3.6, []),
        ('drones_curva', 158, tuple(p_curva + Vector((v_curva.y, -v_curva.x, 0)) * 1.25 - v_curva * 0.5 + Vector((0, 0, 0.55))), tuple(p_curva + Vector((0, 0, -0.05))), 42, False, 3.6, []),
        ('drones_reparo', 228, tuple(MQ + Vector((-1.05, -1.35, 1.55))), tuple(MQ + Vector((-0.12, -0.15, 1.12))), 36, False, 2.2, []),
        ('drones_combate', 340, tuple(p_dc + atras * 1.5 + lado * 0.8 + Vector((0, 0, 0.35))), tuple(p_dc + (CENTRO_AR - p_dc) * 0.45), 32, False, 3.0, []),
        ('drones_pouso', 467, (-0.95, 1.45, 1.5), (0.4, 0.35, 0.95), 36, False, 3.0, []),
        ('drones_derrubado', MORDIDA + 12, tuple(p_q + lq * 2.3 + dq * 0.9 + Vector((0, 0, 0.1))), tuple((p_q * 0.7 + CENTRO_AR * 0.3) + Vector((0, 0, -0.2))), 32, False, 3.0, []),
        ('drones_derrubado_sucata', N - 10, tuple(QC + lq * 1.4 + dq * 0.9 + Vector((0, 0, 0.75))), tuple(QC + Vector((0.15, -0.1, 0.12))), 34, False, 3.0, []),
        ('drone_reparo_perto', 520, tuple(VIT['reparo'][1] + Vector((0.5, -0.7, 0.3))), tuple(VIT['reparo'][1] + Vector((0, 0, -0.05))), 50, True, 3.6, soc),
        ('drone_defesa_perto', 520, tuple(VIT['defesa'][1] + Vector((0.78, -0.5, 0.18))), tuple(VIT['defesa'][1] + Vector((-0.03, 0, -0.07))), 50, True, 3.6, soc),
        ('drone_logistico_perto', 520, tuple(VIT['logistico'][1] + Vector((0.6, -0.72, 0.18))), tuple(VIT['logistico'][1] + Vector((0, 0, -0.12))), 46, True, 3.6, soc),
        ('estacao_perto', 474, (-1.7, -2.4, 2.1), (0.0, 0.0, 0.75), 30, False, 3.6, ['aranha', 'maquina']),
    ]
    return L


modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
so_esta = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None
if modo == 'foto':
    sc.cycles.samples = int(os.environ.get('AMOSTRAS', '128'))
    for nome, fr, cp, ca, lente, vit, s, ocultar in fotos():
        for c in bpy.data.collections:
            if c.name in ('aranha', 'maquina', 'sucata', 'efeitos', 'poeira'):
                c.hide_render = c.name in ocultar
        if so_esta and not any(x == nome for x in so_esta.split(',')):
            continue
        sc.render.resolution_x, sc.render.resolution_y = (1300, 1000)
        bpy.data.collections['vitrine'].hide_render = not vit
        sol.energy = s
        sc.render.use_motion_blur = not vit
        sc.render.motion_blur_shutter = 0.5
        for o in bpy.data.objects:                                        # borrão só no giro das hélices
            o.cycles.use_motion_blur = ('_pas' in o.name or '_sino' in o.name)
        cam.animation_data_clear()
        mirar(cp, ca, lente)
        sc.frame_set(fr)
        sc.render.filepath = os.path.join(AQUI, nome + '.png')
        bpy.ops.render.render(write_still=True)
if modo == 'salvar':
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(AQUI, 'drones.blend'))
print('DRONES ok', 'F_IMP', F_IMP)
if modo == 'debug':
    for fr in (446, 454, 458, 463, 469, 476):
        sc.frame_set(fr)
        pu = bpy.data.objects['abast_punho'].matrix_world.translation
        print('DBG', fr, 'punho', tuple(round(v, 3) for v in pu), 'remendo', tuple(round(v, 3) for v in E['remendo'].matrix_world.translation), 'FUNIL', tuple(round(v, 3) for v in FUNIL), 'PEGA', tuple(round(v,3) for v in PEGA))
