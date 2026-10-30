"""Estudo isolado (fora do jogo): coletor de lixo (aspirador ambiental da IA), 2×2 tiles, sem portas.
Silo octogonal com visor mostrando o lodo em camadas; separador ciclônico sobre o teto (eclusa rotativa despeja o
sólido no silo); filtro de cartuchos e turbina de exaustão girando com vapor saindo. Dois braços de sucção (leste e
oeste) em torres giratórias: cada lança é erguida por um pistão (pistao0 leste, pistao1 oeste) e uma mangueira
corrugada grossa vai do bocal, pela lança, até a junta rotativa no eixo da torre e dali pelo cano fixo até o ciclone.
Os bocais pairam sobre o chão e varrem em arco a lama e o óleo em volta: atrás fica a faixa limpa; à frente, a
sujeira sobe em fios flutuantes puxada pelo campo violeta da IA. Decantador lamelar ao norte (óleo flutua e é
raspado para um tambor; água clara vai para o ralo); prensa compactadora a sudoeste enchendo tambores; tambores de
resíduo compactado empilhados a sudeste. Lama escorrendo, respingos, óleo.
Uso: blender -b --python estudo_coletor_lixo.py -- foto   (ou -- teste)"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import mats, base3d
from base3d import obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha

PI = math.pi
FPS = 24
QUADROS = 96                 # 4 s em laço
EX, EY, EZ = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
random.seed(23)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = base3d.iniciar()
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, QUADROS


def suavizar(o):
    """Sombra suave só nas laterais (quads) — tubos parecem tubos; tampas continuam planas."""
    for pg in o.data.polygons:
        pg.use_smooth = len(pg.vertices) == 4
    return o


def toro(bm, centro, R, r, nR=64, nr=16):
    aneis = []
    for i in range(nR):
        a = i * 2 * PI / nR
        d = Vector((math.cos(a), math.sin(a), 0))
        aneis.append([bm.verts.new(Vector(centro) + d * (R + r * math.cos(b)) + Vector((0, 0, r * math.sin(b))))
                      for b in (j * 2 * PI / nr for j in range(nr))])
    for i in range(nR):
        A, B = aneis[i], aneis[(i + 1) % nR]
        for j in range(nr):
            bm.faces.new((A[j], A[(j + 1) % nr], B[(j + 1) % nr], B[j]))


def octo(bm, c, r, z0, z1, r2=None):
    """Prisma (ou tronco) octogonal com faces viradas para os pontos cardeais."""
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0,
                          matrix=Matrix.Translation(Vector(c) + Vector((0, 0, (z0 + z1) / 2))) @ Matrix.Rotation(PI / 8, 4, 'Z'))


def tubo_curvo(bm, pts, raio, lados=16, corrug=0.0, passo=0.02):
    """Tubo ao longo de uma polilinha densa, reamostrada; raio fixo ou função de u (0→1); corrug alterna anéis."""
    pts = [Vector(p) for p in pts]
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    tot = L[-1]
    n = max(2, int(tot / passo))

    def ponto(s):
        for i in range(len(L) - 1):
            if L[i + 1] >= s:
                f = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
                return pts[i].lerp(pts[i + 1], f)
        return pts[-1]
    P = [ponto(tot * i / n) for i in range(n + 1)]
    aneis, nrm = [], None
    for i, p in enumerate(P):
        t = (P[min(i + 1, n)] - P[max(i - 1, 0)]).normalized()
        if nrm is None:
            nrm = t.orthogonal().normalized()
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        u = i / n
        r = raio(u) if callable(raio) else raio
        if corrug and 0 < i < n:
            r *= (1.0 - corrug * (i % 2))
        aneis.append([bm.verts.new(p + (nrm * math.cos(a) + bi * math.sin(a)) * r)
                      for a in (j * 2 * PI / lados for j in range(lados))])
    for A, B in zip(aneis, aneis[1:]):
        for j in range(lados):
            bm.faces.new((A[j], A[(j + 1) % lados], B[(j + 1) % lados], B[j]))
    bm.faces.new(list(reversed(aneis[0])))
    bm.faces.new(aneis[-1])
    return P


def esfera(bm, c, r, seg=12):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r, matrix=Matrix.Translation(Vector(c)))


def gota(bm, c, r, achatar=0.45):
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in res['verts']:
        v.co = Vector(c) + Vector((v.co.x * random.uniform(0.8, 1.3), v.co.y * random.uniform(0.8, 1.3), v.co.z * achatar))


# ------------------------------------------------------------------ materiais
def mancha_lisa(bm, c, r, z, seg=40):
    """Poça de borda orgânica: raio com harmônicos baixos, sem quinas."""
    fs = [random.uniform(0, 6) for _ in range(4)]
    vs = []
    for k in range(seg):
        a = k * 2 * PI / seg
        f = 1 + 0.22 * math.sin(2 * a + fs[0]) + 0.14 * math.sin(3 * a + fs[1]) + 0.08 * math.sin(5 * a + fs[2]) + 0.04 * math.sin(9 * a + fs[3])
        vs.append(bm.verts.new((c[0] + math.cos(a) * r * f, c[1] + math.sin(a) * r * f * 0.8, z)))
    bm.faces.new(vs)


def emis_mat(nome, cor, forca, base=None):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or cor), 1)
    b.inputs['Emission Color'].default_value = (*cor, 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def vidro_mat(nome, cor, transm, rough=0.05):
    m = bpy.data.materials.new(nome)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = 0.25
    b.inputs['Base Color'].default_value = (*cor, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transm
    b.inputs['IOR'].default_value = 1.4
    return m


def lama_mat(nome, cor, rough, bump=0.4):
    """Lama: marrom com variação, brilho molhado irregular e relevo grumoso."""
    m = bpy.data.materials.new(nome)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 18.0, 'Detail': 8.0, 'Roughness': 0.65})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    cor_m = no(nt, 'ShaderNodeMix', data_type='RGBA')
    cor_m.inputs[6].default_value = (*cor, 1)
    cor_m.inputs[7].default_value = (cor[0] * 0.45, cor[1] * 0.45, cor[2] * 0.45, 1)
    nt.links.new(ru.outputs['Fac'], cor_m.inputs[0])
    nt.links.new(cor_m.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': rough * 0.4, 'To Max': rough * 1.6})
    nt.links.new(ru.outputs['Fac'], rg.inputs['Value'])
    nt.links.new(rg.outputs['Result'], b.inputs['Roughness'])
    bp = no(nt, 'ShaderNodeBump', **{'Strength': bump})
    nt.links.new(ru.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def fio_mat():
    """Fio de sujeira levitando: lama escura com veios violeta do campo correndo por dentro."""
    m = lama_mat('Fio de sujeira', (0.10, 0.065, 0.035), 0.3, 0.2)
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 40.0, 'Detail': 3.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    veio = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.6, 'From Max': 0.72, 'To Min': 0.0, 'To Max': 3.0})
    nt.links.new(ru.outputs['Fac'], veio.inputs['Value'])
    nt.links.new(veio.outputs['Result'], b.inputs['Emission Strength'])
    b.inputs['Emission Color'].default_value = (0.55, 0.18, 1.0, 1)
    return m


def campo_mat():
    """Campo de sucção: névoa violeta tênue sob o bocal, mais densa no centro, com ruído (não é filtro de tela)."""
    m = bpy.data.materials.new('Campo')
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    vol = no(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.05, 0.02, 0.1, 1)
    vol.inputs['Emission Color'].default_value = (0.5, 0.16, 1.0, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 5.0, 'Detail': 4.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    comp = no(nt, 'ShaderNodeVectorMath', operation='LENGTH')
    nt.links.new(tc.outputs['Object'], comp.inputs[0])
    borda = no(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.2})
    nt.links.new(comp.outputs['Value'], borda.inputs['Value'])
    mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(borda.outputs['Result'], mul.inputs[0])
    nt.links.new(ru.outputs['Fac'], mul.inputs[1])
    d = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    d.inputs[1].default_value = 3.0
    nt.links.new(mul.outputs['Value'], d.inputs[0])
    nt.links.new(d.outputs['Value'], vol.inputs['Density'])
    e = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    e.inputs[1].default_value = 6.0
    nt.links.new(mul.outputs['Value'], e.inputs[0])
    nt.links.new(e.outputs['Value'], vol.inputs['Emission Strength'])
    return m


base3d.M.update({
    'amarelo': mats.material('Amarelo', (0.72, 0.48, 0.05), 0, 0.42, desgaste=0.85, sujeira=0.9),
    'grafite': mats.material('Grafite', (0.07, 0.075, 0.08), 0, 0.5, desgaste=0.6, sujeira=0.8),
    'silo': mats.material('Silo', (0.16, 0.17, 0.15), 0, 0.55, desgaste=0.7, sujeira=1.0, ferrugem=0.4),
    'aco': mats.material('Aço', (0.42, 0.43, 0.44), 1.0, 0.42, pintura=False, ferrugem=0.85, sujeira=0.8, escovado=True),
    'casco': mats.material('Casco', (0.24, 0.22, 0.21), 1.0, 0.5, pintura=False, ferrugem=0.95, sujeira=1.0),
    'ferro': mats.material('Ferro fundido', (0.09, 0.085, 0.08), 0.8, 0.7, pintura=False, ferrugem=0.9, sujeira=0.9),
    'cromo': mats.material('Cromo', (0.85, 0.86, 0.88), 1.0, 0.14, pintura=False, sujeira=0.3),
    'borracha': mats.material('Borracha', (0.025, 0.025, 0.027), 0, 0.6, pintura=False, sujeira=0.9, desgaste=0.0),
    'tambor': mats.material('Tambor', (0.16, 0.2, 0.13), 0, 0.5, desgaste=0.9, sujeira=1.0, ferrugem=0.6),
    'concreto': mats.material('Concreto', (0.33, 0.32, 0.30), 0, 0.9, sujeira=0.7, desgaste=0.0),
    'chao': mats.material('Chão', (0.30, 0.28, 0.25), 0, 0.9, sujeira=0.3, desgaste=0.0),
    'oleo': mats.material('Óleo', (0.012, 0.01, 0.008), 0, 0.05, pintura=False, sujeira=0.0, desgaste=0.0),
    'lama': lama_mat('Lama', (0.12, 0.08, 0.045), 0.25),
    'lama_seca': lama_mat('Lama seca', (0.22, 0.17, 0.11), 0.85, 0.6),
    'sedimento': lama_mat('Sedimento', (0.08, 0.075, 0.07), 0.7),
    'lodo': lama_mat('Lodo', (0.17, 0.10, 0.04), 0.35),
    'agua_lodo': lama_mat('Água turva', (0.10, 0.12, 0.05), 0.15, 0.05),
    'espuma': lama_mat('Espuma', (0.32, 0.27, 0.18), 0.7, 0.3),
    'vazio': mats.material('Vazio', (0.01, 0.01, 0.012), 0, 0.8, pintura=False, sujeira=0.0, desgaste=0.0),
    'vidro': vidro_mat('Vidro', (0.8, 0.82, 0.8), 0.9, 0.04),
    'agua': vidro_mat('Água do decantador', (0.16, 0.17, 0.08), 0.35, 0.03),
    'fio': fio_mat(),
    'campo': campo_mat(),
    'anel_campo': emis_mat('Anel de campo', (0.55, 0.18, 1.0), 10.0, (0.1, 0.04, 0.2)),
    'led': emis_mat('LED', (0.6, 0.2, 1.0), 6.0),
    'led_ambar': emis_mat('LED âmbar', (1.0, 0.45, 0.05), 6.0),
    'listras': base3d.listras_mat(),
    'vapor': base3d.volume_mat('Vapor', (0.92, 0.92, 0.94), 5.0, 2.15, 3.0),
})

# ------------------------------------------------------------------ cotas
R_SILO = 0.46                      # raio do octógono (vértice); face a 0,425
AP = R_SILO * math.cos(PI / 8)
Z_SILO, Z_TETO = 1.1, 1.22
P = 1.1                            # altura do pino da lança
TORRE_X = 0.68

# ------------------------------------------------------------------ laje
bm = bmesh.new()
caixa_de(bm, (-1.0, -1.0, 0), (1.0, 1.0, 0.08))
obj('laje', bm, 'concreto')
bm = bmesh.new()
caixa_de(bm, (-1.005, -1.005, 0.0), (1.005, -0.985, 0.08))
caixa_de(bm, (-1.005, 0.985, 0.0), (1.005, 1.005, 0.08))
obj('laje_listras', bm, 'listras')

# ------------------------------------------------------------------ silo octogonal
bm = bmesh.new()
octo(bm, (0, 0, 0), R_SILO, 0.08, Z_SILO)
obj('silo', bm, 'silo')
bm = bmesh.new()
octo(bm, (0, 0, 0), R_SILO + 0.02, 0.08, 0.16)                                   # saia da base
octo(bm, (0, 0, 0), R_SILO + 0.012, 0.18, 0.22)                                  # cintas
octo(bm, (0, 0, 0), R_SILO + 0.012, 1.0, 1.04)
octo(bm, (0, 0, 0), R_SILO + 0.015, Z_SILO - 0.01, Z_SILO + 0.02)
obj('silo_cintas', bm, 'amarelo')
bm = bmesh.new()
octo(bm, (0, 0, 0), R_SILO, Z_SILO, Z_TETO, r2=0.25)                             # teto em tronco
octo(bm, (0, 0, 0), 0.26, Z_TETO, Z_TETO + 0.02)
obj('silo_teto', bm, 'silo')
bm, br = bmesh.new(), bmesh.new()
for k in range(8):                                                               # nervuras nos vértices
    a = PI / 8 + k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    caixa(bm, d * (R_SILO + 0.008) + Vector((0, 0, 0.6)), (0.03, 0.03, 0.96), Matrix.Rotation(a, 3, 'Z'))
for k in range(8):                                                               # rebites nas cintas (faces)
    a = k * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    for z in (0.2, 1.02):
        for j in (-2, -1, 1, 2):
            if k == 6 and z < 0.5 and abs(j) < 2:
                continue
            cil(br, d * (AP + 0.022) + t * j * 0.07 + Vector((0, 0, z)), 0.007, 0.01, d, lados=6)
obj('silo_nervuras', bm, 'grafite')
obj('silo_rebites', br, 'aco')

# visor sul: lodo em camadas onduladas atrás do vidro
YV = -AP
base3d.M.update({
    'v_lodo': emis_mat('Visor lodo', (0.3, 0.16, 0.05), 0.8, (0.2, 0.11, 0.04)),
    'v_agua': emis_mat('Visor água', (0.2, 0.25, 0.08), 1.0, (0.12, 0.15, 0.05)),
    'v_espuma': emis_mat('Visor espuma', (0.4, 0.34, 0.22), 0.6, (0.35, 0.3, 0.2)),
    'v_sedimento': emis_mat('Visor sedimento', (0.1, 0.09, 0.08), 0.5, (0.09, 0.085, 0.08)),
})
VISOR_MAT = {'lodo': 'v_lodo', 'agua_lodo': 'v_agua', 'espuma': 'v_espuma', 'sedimento': 'v_sedimento'}
bm = bmesh.new()
for sx in (-1, 1):
    caixa_de(bm, (sx * 0.1, YV - 0.045, 0.28), (sx * 0.128, YV + 0.002, 0.92))
for z in (0.28, 0.9):
    caixa_de(bm, (-0.128, YV - 0.045, z), (0.128, YV + 0.002, z + 0.022))
obj('visor_moldura', bm, 'ferro')
bm = bmesh.new()
for z in (0.29, 0.45, 0.6, 0.75, 0.91):
    for sx in (-1, 1):
        cil(bm, Vector((sx * 0.114, YV - 0.047, z)), 0.008, 0.008, -EY, lados=6)
obj('visor_parafusos', bm, 'aco')
CAMADAS = (('sedimento', 0.43), ('lodo', 0.58), ('oleo', 0.635), ('agua_lodo', 0.79), ('espuma', 0.83), ('vazio', 0.902))
z_baixo = lambda x: 0.30
for k, (mat, zt) in enumerate(CAMADAS):
    bm = bmesh.new()
    fase = random.uniform(0, 6)
    amp = 0.0 if mat == 'vazio' else (0.004 if mat in ('oleo', 'espuma') else 0.01)
    z_cima = (lambda zt, fase, amp: (lambda x: zt + amp * math.sin(x * 38 + fase) + amp * 0.5 * math.sin(x * 91 + fase * 2)))(zt, fase, amp)
    xs = [-0.1 + 0.2 * i / 24 for i in range(25)]
    baixo = [bm.verts.new((x, YV - 0.012, z_baixo(x))) for x in xs]
    cima = [bm.verts.new((x, YV - 0.012, z_cima(x))) for x in xs]
    for i in range(24):
        bm.faces.new((baixo[i], baixo[i + 1], cima[i + 1], cima[i]))
    obj('visor_' + mat, bm, VISOR_MAT.get(mat, mat))
    z_baixo = z_cima
bm = bmesh.new()
for k in range(14):                                                              # bolhas na água turva
    gota(bm, (random.uniform(-0.09, 0.09), YV - 0.022, random.uniform(0.65, 0.78)), random.uniform(0.003, 0.007), 1.0)
for k in range(10):                                                              # grumos no lodo
    gota(bm, (random.uniform(-0.09, 0.09), YV - 0.018, random.uniform(0.44, 0.56)), random.uniform(0.005, 0.01), 0.7)
obj('visor_bolhas', bm, 'espuma')
bm = bmesh.new()
caixa_de(bm, (-0.1, YV - 0.034, 0.3), (0.1, YV - 0.03, 0.9))
obj('visor_vidro', bm, 'vidro')
bm = bmesh.new()                                                                 # régua de nível que a IA lê
caixa_de(bm, (0.14, YV - 0.012, 0.3), (0.162, YV + 0.002, 0.9))
obj('regua', bm, 'grafite')
bm, bl = bmesh.new(), bmesh.new()
for k in range(12):
    z = 0.32 + k * 0.05
    caixa_de(bl if z < 0.8 else bm, (0.145, YV - 0.015, z), (0.157, YV - 0.011, z + 0.022))
obj('regua_apagada', bm, 'vazio')
obj('regua_leds', bl, 'led')

# ------------------------------------------------------------------ eclusa rotativa, ciclone, filtro e turbina
bm = bmesh.new()
caixa_de(bm, (-0.11, -0.1, Z_TETO + 0.02), (0.11, 0.1, 1.34))                    # eclusa (válvula rotativa)
cil(bm, Vector((0.0, -0.13, 1.29)), 0.055, 0.07, EY, lados=14)                   # motor da eclusa
for j in range(5):
    cil(bm, Vector((0.0, -0.105 - j * 0.012, 1.29)), 0.064, 0.005, EY, lados=14)
obj('eclusa', bm, 'grafite')
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.07, radius2=0.2, depth=0.16,
                      matrix=Matrix.Translation((0, 0, 1.42)))                    # cone do ciclone
cil(bm, Vector((0, 0, 1.63)), 0.2, 0.26, lados=32)                               # corpo cilíndrico
suavizar(obj('ciclone', bm, 'aco'))
bm = bmesh.new()
for z in (1.5, 1.76):
    cil(bm, Vector((0, 0, z)), 0.215, 0.025, lados=32)
cil(bm, Vector((0, 0, 1.345)), 0.085, 0.02, lados=20)
obj('ciclone_flanges', bm, 'ferro')
bm = bmesh.new()
for k in range(4):                                                               # pernas do ciclone no teto
    a = PI / 4 + k * PI / 2
    d = Vector((math.cos(a), math.sin(a), 0))
    viga(bm, d * 0.36 + Vector((0, 0, 1.16)), d * 0.205 + Vector((0, 0, 1.5)), 0.03)
    caixa(bm, d * 0.36 + Vector((0, 0, 1.165)), (0.07, 0.07, 0.015), Matrix.Rotation(a, 3, 'Z'))
obj('ciclone_pernas', bm, 'amarelo')
for s in (1, -1):                                                                # entradas tangenciais
    bm = bmesh.new()
    caixa(bm, (s * 0.2, s * 0.12, 1.64), (0.2, 0.1, 0.13))
    obj('ciclone_entrada', bm, 'aco')
bm = bmesh.new()
cil(bm, Vector((0, 0, 1.81)), 0.08, 0.08, lados=20)                              # tubo de vórtice
suavizar(obj('vortice', bm, 'aco'))
bm = bmesh.new()
caixa_de(bm, (-0.19, -0.19, 1.85), (0.19, 0.19, 2.03))                            # caixa do filtro
obj('filtro', bm, 'grafite')
bm = bmesh.new()
for s in (-1, 1):                                                                # cartuchos plissados à mostra (leste/oeste)
    for k in range(15):
        y = -0.15 + k * 0.0214
        caixa_de(bm, (s * 0.19, y - 0.004, 1.87), (s * 0.202, y + 0.004, 2.01))
obj('filtro_pregas', bm, 'lama_seca')
bm = bmesh.new()
for s in (-1, 1):
    for z in (1.865, 2.015):
        caixa_de(bm, (s * 0.205 - 0.01, -0.17, z - 0.008), (s * 0.205 + 0.01, 0.17, z + 0.008))
    for y in (-0.165, 0.165):
        caixa_de(bm, (s * 0.205 - 0.01, y - 0.008, 1.86), (s * 0.205 + 0.01, y + 0.008, 2.02))
obj('filtro_grades', bm, 'ferro')
bm = bmesh.new()                                                                 # turbina de exaustão
bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.17, radius2=0.17, depth=0.15, matrix=Matrix.Translation((0, 0, 2.105)))
bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.155, radius2=0.155, depth=0.15, matrix=Matrix.Translation((0, 0, 2.105)))
suavizar(obj('turbina_casco', bm, 'casco'))
bm = bmesh.new()
toro(bm, (0, 0, 2.18), 0.163, 0.012, 48, 10)
toro(bm, (0, 0, 2.04), 0.168, 0.012, 48, 10)
cil(bm, Vector((0, 0, 2.06)), 0.03, 0.06, lados=12)                              # mancal do eixo
for k in range(3):                                                               # aranha do mancal
    a = k * 2 * PI / 3
    viga(bm, Vector((0, 0, 2.05)), Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 2.05)), 0.014)
for k in range(6):                                                               # grade de proteção no topo
    a = k * PI / 6
    viga(bm, Vector((-math.cos(a) * 0.162, -math.sin(a) * 0.162, 2.185)), Vector((math.cos(a) * 0.162, math.sin(a) * 0.162, 2.185)), 0.008)
obj('turbina_aros', bm, 'ferro')
rotor = bpy.data.objects.new('rotor', None)
sc.collection.objects.link(rotor)
rotor.location = (0, 0, 2.12)
bm = bmesh.new()
esfera(bm, (0, 0, 0.0), 0.04, 14)
cil(bm, Vector((0, 0, -0.03)), 0.012, 0.06, lados=8)
for k in range(7):
    a = k * 2 * PI / 7
    rot = Matrix.Rotation(a, 3, 'Z') @ Matrix.Rotation(0.5, 3, 'X')
    caixa(bm, Matrix.Rotation(a, 3, 'Z') @ Vector((0.095, 0, 0)), (0.11, 0.045, 0.006), rot)
obj('rotor_pas', bm, 'aco', rotor)

# ------------------------------------------------------------------ torres giratórias e braços de sucção
BRACOS = []
for lado, nome_p in ((1, 'pistao0'), (-1, 'pistao1')):
    T = Vector((lado * TORRE_X, 0, 0))
    bm = bmesh.new()                                                             # base fixa: rolamento de giro
    cil(bm, T + Vector((0, 0, 0.115)), 0.16, 0.07, lados=28)
    caixa(bm, T + Vector((-lado * 0.13, 0.13, 0.13)), (0.08, 0.06, 0.1))         # caixa de anéis coletores
    obj('torre_base', bm, 'grafite')
    bm = bmesh.new()
    for k in range(16):
        a = k * 2 * PI / 16
        cil(bm, T + Vector((math.cos(a) * 0.145, math.sin(a) * 0.145, 0.155)), 0.008, 0.012, lados=6)
    obj('torre_parafusos', bm, 'aco')
    giro = bpy.data.objects.new('giro', None)
    sc.collection.objects.link(giro)
    giro.location = T
    giro.rotation_euler = (0, 0, 0 if lado > 0 else PI)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.185)), 0.135, 0.05, lados=28)                         # colar giratório
    obj('torre_colar', bm, 'amarelo', giro)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, (0.21 + P - 0.1) / 2)), 0.07, P - 0.1 - 0.21, lados=20)  # coluna
    suavizar(obj('torre_coluna', bm, 'amarelo', giro))
    bm = bmesh.new()
    for sy in (-1, 1):                                                           # garfo do pino
        caixa_de(bm, (-0.06, sy * 0.05, P - 0.11), (0.06, sy * 0.07, P + 0.07))
    caixa_de(bm, (-0.06, -0.07, P + 0.07), (0.06, 0.07, P + 0.09))               # tampa do garfo
    caixa_de(bm, (0.065, -0.03, 0.56), (0.12, 0.03, 0.64))                       # orelha do pistão
    for sy in (-1, 1):
        caixa_de(bm, (0.09, sy * 0.022 - 0.006, 0.6), (0.13, sy * 0.022 + 0.006, 0.66))
    caixa_de(bm, (-0.115, -0.05, 0.42), (-0.07, 0.05, 0.56))                     # bloco hidráulico
    obj('torre_garfo', bm, 'grafite', giro)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, P)), 0.022, 0.17, EY, lados=12)                        # pino
    cil(bm, Vector((0, 0, P + 0.165)), 0.07, 0.15, lados=20)                     # junta rotativa da mangueira
    cil(bm, Vector((0.075, 0, P + 0.16)), 0.05, 0.05, EX, lados=16)              # saída lateral
    obj('junta_rotativa', bm, 'aco', giro)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, P + 0.1)), 0.082, 0.02, lados=20)
    cil(bm, Vector((0, 0, P + 0.235)), 0.082, 0.02, lados=20)
    cil(bm, Vector((0.1, 0, P + 0.16)), 0.068, 0.018, EX, lados=16)
    obj('junta_flanges', bm, 'ferro', giro)
    bm = bmesh.new()                                                             # mangueiras hidráulicas do pistão
    mangueira(bm, bezier((-0.07, 0.03, 0.5), (0.0, 0.09, 0.52), (0.07, 0.07, 0.6), (0.1, 0.035, 0.63), 10), 0.009)
    mangueira(bm, bezier((-0.07, -0.03, 0.47), (0.02, -0.12, 0.45), (0.1, -0.12, 0.75), (0.13, -0.045, 0.9), 12), 0.009)
    obj('torre_hidraulica', bm, 'borracha', giro)

    lanca = bpy.data.objects.new('lanca', None)                                  # lança: gira no pino (arfagem)
    sc.collection.objects.link(lanca)
    lanca.parent = giro
    lanca.location = (0, 0, P)
    E = Vector((0.42, 0, 0.1))
    F = Vector((0.48, 0, -0.67))
    BOCA = Vector((0.6, 0, -0.85))
    bm = bmesh.new()
    viga(bm, Vector((-0.03, 0, -0.006)), E, 0.07)                                # lança
    viga(bm, E, F, 0.06)                                                         # antebraço
    cil(bm, Vector((0, 0, 0)), 0.045, 0.095, EY, lados=16)                       # cubo do pino
    caixa(bm, Vector((0.24, 0, 0.0)), (0.05, 0.03, 0.06))                         # olhal da haste
    caixa_de(bm, (0.47, -0.035, -0.74), (0.555, 0.035, -0.66))                   # suporte do bocal
    obj('braco', bm, 'amarelo', lanca)
    bm = bmesh.new()
    for sy in (-1, 1):                                                           # chapas do joelho
        caixa(bm, E + Vector((-0.01, sy * 0.042, -0.03)), (0.16, 0.012, 0.16), Matrix.Rotation(-0.2, 3, 'Y'))
    cil(bm, E, 0.022, 0.11, EY, lados=12)
    cil(bm, Vector((0.24, 0, -0.045)), 0.012, 0.075, EY, lados=10)              # pino do olhal
    for t in (0.35, 0.7):                                                        # abraçadeiras da mangueira
        p = E.lerp(F, t)
        viga(bm, p + Vector((0.03, 0, 0)), Vector((0.62 + 0.06 * (t < 0.5), 0, p.z)), 0.022)
    obj('braco_juntas', bm, 'grafite', lanca)
    bm = bmesh.new()                                                             # bocal de sucção (capuz)
    bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.17, radius2=0.075, depth=0.13,
                          matrix=Matrix.Translation(BOCA + Vector((0, 0, 0.065))))
    cil(bm, BOCA + Vector((0, 0, 0.145)), 0.075, 0.035, lados=20)
    suavizar(obj('bocal', bm, 'casco', lanca))
    bm = bmesh.new()
    cil(bm, BOCA + Vector((0, 0, 0.165)), 0.085, 0.016, lados=20)
    for k in range(6):                                                           # nervuras do capuz
        a = k * PI / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        viga(bm, BOCA + d * 0.165 + Vector((0, 0, 0.005)), BOCA + d * 0.08 + Vector((0, 0, 0.125)), 0.014)
    obj('bocal_nervuras', bm, 'ferro', lanca)
    bm = bmesh.new()
    toro(bm, BOCA + Vector((0, 0, -0.004)), 0.168, 0.013, 48, 10)               # anel de campo na boca
    obj('bocal_anel', bm, 'anel_campo', lanca)
    bm = bmesh.new()                                                             # lama grudada no capuz e na mangueira
    for k in range(16):
        a = random.uniform(0, 2 * PI)
        h = random.uniform(0.0, 0.1)
        rr = 0.17 - (0.17 - 0.075) * h / 0.13 + 0.004
        gota(bm, BOCA + Vector((math.cos(a) * rr, math.sin(a) * rr, h + 0.005)), random.uniform(0.008, 0.02), 0.5)
    obj('bocal_lama', bm, 'lama', lanca)
    bm = bmesh.new()                                                             # mangueira corrugada grossa
    pts = bezier((0.1, 0, 0.16), (0.32, 0, 0.16), (0.6, 0, 0.42), (0.66, 0, 0.05), 30)
    pts += bezier((0.66, 0, 0.05), (0.7, 0, -0.32), (0.6, 0, -0.5), BOCA + Vector((0, 0, 0.16)), 30)[1:]
    tubo_curvo(bm, pts, 0.06, 16, corrug=0.13, passo=0.016)
    suavizar(obj('mangueira', bm, 'borracha', lanca))
    bm = bmesh.new()
    for t in (0.35, 0.7):
        p = E.lerp(F, t)
        toro(bm, Vector((0.62 + 0.06 * (t < 0.5), 0, p.z)), 0.064, 0.008, 24, 6)
    obj('mangueira_abracadeiras', bm, 'aco', lanca)
    luz = bpy.data.lights.new('Campo', 'POINT')
    luz.color = (0.6, 0.25, 1.0)
    luz.energy = 6
    luz.shadow_soft_size = 0.15
    lo = bpy.data.objects.new('Campo', luz)
    sc.collection.objects.link(lo)
    lo.parent = lanca
    lo.location = BOCA + Vector((0, 0, -0.06))
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    campo = obj('campo', bm, 'campo', lanca)
    campo.location = BOCA + Vector((0, 0, -0.05))
    campo.scale = (0.2, 0.2, 0.11)

    # pistão da lança (camisa na orelha da coluna, haste no olhal sob a lança)
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.15)), 0.032, 0.3, EZ, 18)
    cil(bm, Vector((0, 0, 0.012)), 0.038, 0.024, EZ, 18)
    cil(bm, Vector((0, 0, 0.288)), 0.038, 0.024, EZ, 18)
    cil(bm, Vector((0, 0, 0)), 0.012, 0.05, EY, 10)
    cil(bm, Vector((0.03, 0, 0.06)), 0.01, 0.025, EX, 8)                        # portas de óleo
    cil(bm, Vector((0.03, 0, 0.26)), 0.01, 0.025, EX, 8)
    camisa = suavizar(obj(nome_p + '_camisa', bm, 'amarelo', giro))
    camisa.rotation_mode = 'QUATERNION'
    bm = bmesh.new()
    cil(bm, Vector((0, 0, 0.14)), 0.015, 0.28, EZ, 14)
    cil(bm, Vector((0, 0, 0)), 0.011, 0.05, EY, 10)
    caixa(bm, (0, 0, 0.015), (0.028, 0.026, 0.03))
    haste = suavizar(obj(nome_p + '_haste', bm, 'cromo', giro))
    haste.rotation_mode = 'QUATERNION'

    # fios de sujeira puxados pelo campo (no quadro da torre; nascem na lama além da faixa limpa)
    fios = []
    for k in range(14):
        r = random.uniform(0.84, 1.2)
        a = random.uniform(-0.45, 0.45)
        G = Vector((r * math.cos(a), r * math.sin(a), 0.012))
        M = Vector((0.6, 0, P - 0.85)) + Vector((random.uniform(-0.06, 0.06), random.uniform(-0.06, 0.06), 0))
        dirg = (G - M).xy.to_3d().normalized()
        cam = bezier(G, G + Vector((0, 0, random.uniform(0.15, 0.3))) - dirg * 0.05,
                     M + dirg * random.uniform(0.05, 0.12) + Vector((0, 0, -0.12)), M + Vector((0, 0, 0.03)), 40)
        ond = random.uniform(0, 6)
        cam = [p + Vector((0, 0, 0)) + (EZ.cross(dirg)) * 0.008 * math.sin(i * 0.3 + ond) for i, p in enumerate(cam)]
        fios.append(cam)
        bm = bmesh.new()
        tubo_curvo(bm, cam, lambda u: 0.008 * (1 - u) ** 1.5 + 0.002, 8, passo=0.012)
        suavizar(obj('fio_sujeira', bm, 'fio', giro))
        bm = bmesh.new()                                                         # grumo de lama arrancado do chão
        gota(bm, G, random.uniform(0.02, 0.035), 0.45)
        obj('fio_grumo', bm, 'lama', giro)
    contas = []
    for k in range(len(fios) * 4):
        bm = bmesh.new()
        gota(bm, (0, 0, 0), random.uniform(0.006, 0.013), 0.8)
        contas.append((obj('conta_lama', bm, 'lama', giro), fios[k % len(fios)], (k // len(fios)) / 4 + random.uniform(0, 0.1)))
    BRACOS.append(dict(lado=lado, giro=giro, lanca=lanca, camisa=camisa, haste=haste, contas=contas,
                       A=Vector((0.11, 0, 0.63)), B=Vector((0.24, 0, -0.045))))

    # cano fixo: da junta rotativa até a entrada tangencial do ciclone
    bm = bmesh.new()
    topo = T + Vector((0, 0, P + 0.245))
    cot = Vector((T.x, 0, 1.64))
    fim = Vector((lado * 0.36, lado * 0.12, 1.64))
    tubo(bm, topo, cot, 0.05, 20)
    tubo(bm, cot, fim, 0.05, 20)
    esfera(bm, cot, 0.05, 20)
    suavizar(obj('cano_fixo', bm, 'casco'))
    bm = bmesh.new()
    cil(bm, topo + Vector((0, 0, 0.01)), 0.068, 0.02, lados=20)
    d = (fim - cot).normalized()
    cil(bm, fim - d * 0.01, 0.068, 0.02, d, lados=20)
    cil(bm, cot.lerp(fim, 0.5), 0.062, 0.025, d, lados=20)
    obj('cano_flanges', bm, 'ferro')
    bm = bmesh.new()                                                             # escora do cano no teto
    m = cot.lerp(fim, 0.4)
    viga(bm, m - Vector((0, 0, 0.05)), Vector((lado * 0.43, m.y * 0.5, Z_SILO + 0.01)), 0.025)
    obj('cano_escora', bm, 'amarelo')

# ------------------------------------------------------------------ cabos de força (silo → torres) em eletrocalha
bm, bc = bmesh.new(), bmesh.new()
for lado in (1, -1):
    caixa_de(bm, (lado * AP, 0.12, 0.6), (lado * (AP + 0.05), 0.26, 0.74))    # caixa de junção
    for j in range(3):
        y = 0.15 + j * 0.035
        mangueira(bc, bezier((lado * (AP + 0.05), y, 0.62), (lado * (AP + 0.12), y, 0.55),
                             (lado * (TORRE_X - 0.1), y, 0.4), (lado * (TORRE_X - 0.1), y - 0.02 * 0, 0.19), 12), 0.011)
    caixa_de(bm, (lado * (TORRE_X - 0.13) - 0.03, 0.13, 0.25), (lado * (TORRE_X - 0.13) + 0.03, 0.25, 0.27))   # abraçadeira
obj('caixa_juncao', bm, 'grafite')
obj('cabos', bc, 'borracha')
bm = bmesh.new()
for lado in (1, -1):
    for j in range(3):
        caixa_de(bm, (min(lado * (AP + 0.05), lado * (AP + 0.052)), 0.14 + j * 0.035, 0.7),
                 (max(lado * (AP + 0.05), lado * (AP + 0.052)), 0.155 + j * 0.035, 0.715))
obj('caixa_leds', bm, 'led')

# ------------------------------------------------------------------ decantador lamelar (norte)
DX0, DX1, DY0, DY1, DZ = -0.55, 0.55, 0.6, 0.95, 0.5
bm = bmesh.new()
caixa_de(bm, (DX0, DY0, 0.08), (DX1, DY0 + 0.02, DZ))
caixa_de(bm, (DX0, DY1 - 0.02, 0.08), (DX1, DY1, DZ))
caixa_de(bm, (DX0, DY0, 0.08), (DX0 + 0.02, DY1, DZ))
caixa_de(bm, (DX1 - 0.02, DY0, 0.08), (DX1, DY1, DZ))
obj('decantador', bm, 'silo')
bm = bmesh.new()
for x in (DX0, DX1):                                                             # cantoneiras e borda
    for y in (DY0, DY1):
        caixa_de(bm, (x - 0.018, y - 0.018, 0.08), (x + 0.018, y + 0.018, DZ + 0.02))
for y in (DY0, DY1):
    caixa_de(bm, (DX0 - 0.015, y - 0.015, DZ - 0.01), (DX1 + 0.015, y + 0.015, DZ + 0.015))
caixa_de(bm, (DX0 - 0.012, DY0 - 0.012, 0.2), (DX1 + 0.012, DY0 + 0.0, 0.23))
obj('decantador_borda', bm, 'amarelo')
bm = bmesh.new()
caixa_de(bm, (DX0 + 0.02, DY0 + 0.02, 0.1), (DX1 - 0.02, DY1 - 0.02, DZ - 0.04))
obj('decantador_agua', bm, 'agua')
bm = bmesh.new()
for k in range(11):                                                              # placas lamelares inclinadas
    x = -0.36 + k * 0.07
    caixa(bm, (x, (DY0 + DY1) / 2, 0.36), (0.006, DY1 - DY0 - 0.06, 0.24), Matrix.Rotation(0.6, 3, 'Y'))
obj('lamelas', bm, 'aco')
bm = bmesh.new()                                                                 # óleo flutuando a leste
mancha(bm, (0.32, 0.78), 0.12, DZ - 0.038)
mancha(bm, (0.2, 0.7), 0.06, DZ - 0.038)
obj('decantador_oleo', bm, 'oleo')
bm = bmesh.new()                                                                 # calha raspadora de óleo
caixa_de(bm, (0.43, DY0 + 0.02, DZ - 0.07), (0.53, DY1 - 0.02, DZ - 0.055))
for x in (0.43, 0.53):
    caixa_de(bm, (x - 0.006, DY0 + 0.02, DZ - 0.07), (x + 0.006, DY1 - 0.02, DZ - 0.02))
obj('raspador', bm, 'ferro')
bm = bmesh.new()                                                                 # entrada: do silo ao decantador
tubo(bm, (0.0, AP - 0.01, 0.24), (0.0, DY0 + 0.01, 0.24), 0.045, 20)
suavizar(obj('cano_lodo', bm, 'casco'))
bm = bmesh.new()
for y in (AP + 0.012, DY0 - 0.01, 0.51):
    cil(bm, Vector((0, y, 0.24)), 0.06, 0.022, EY, lados=20)
caixa_de(bm, (-0.05, 0.48, 0.27), (0.05, 0.54, 0.35))                            # atuador da válvula
obj('cano_lodo_flanges', bm, 'ferro')
bm = bmesh.new()
caixa_de(bm, (0.02, 0.535, 0.31), (0.035, 0.542, 0.325))
obj('valvula_led', bm, 'led_ambar')
bm = bmesh.new()                                                                 # saída de óleo → tambor
OT = Vector((0.8, 0.78, 0))
tubo(bm, (0.48, 0.78, DZ - 0.05), (0.62, 0.78, DZ - 0.05), 0.022, 14)
tubo(bm, (0.62, 0.78, DZ - 0.05), (0.62, 0.78, DZ + 0.06), 0.022, 14)
tubo(bm, (0.62, 0.78, DZ + 0.06), (OT.x, 0.78, DZ + 0.06), 0.022, 14)
tubo(bm, (OT.x, 0.78, DZ + 0.06), (OT.x, 0.78, 0.5), 0.022, 14)
for p in ((0.62, 0.78, DZ - 0.05), (0.62, 0.78, DZ + 0.06), (OT.x, 0.78, DZ + 0.06)):
    esfera(bm, p, 0.022, 14)
suavizar(obj('cano_oleo', bm, 'casco'))
bm = bmesh.new()                                                                 # saída de água clara → ralo
tubo(bm, (DX0 + 0.01, 0.86, 0.4), (-0.76, 0.86, 0.4), 0.03, 16)
tubo(bm, (-0.76, 0.86, 0.4), (-0.76, 0.86, 0.1), 0.03, 16)
esfera(bm, (-0.76, 0.86, 0.4), 0.03, 16)
suavizar(obj('cano_agua', bm, 'casco'))
bm = bmesh.new()
caixa_de(bm, (-0.88, 0.74, 0.08), (-0.64, 0.98, 0.085))
obj('ralo_fundo', bm, 'vazio')
bm = bmesh.new()
for k in range(9):
    x = -0.87 + k * 0.028
    caixa_de(bm, (x, 0.74, 0.08), (x + 0.012, 0.98, 0.092))
for y in (0.74, 0.97):
    caixa_de(bm, (-0.88, y, 0.08), (-0.64, y + 0.012, 0.094))
obj('ralo_grade', bm, 'ferro')


def tambor(bc, ba, c, r, h, eixo=EZ, faixa=None):
    c = Vector(c)
    e = Vector(eixo).normalized()
    cil(bc, c, r, h, e, lados=28)
    for f in (-0.5, -0.17, 0.17, 0.5):                                           # aros e frisos
        cil(ba, c + e * h * f * (0.98 if abs(f) == 0.5 else 1), r + 0.006, 0.014, e, lados=28)
    cil(ba, c + e * (h / 2 + 0.004), r * 0.93, 0.01, e, lados=28)                # tampa
    cil(ba, c + e * (h / 2 + 0.01) + (e.orthogonal().normalized() * r * 0.55), 0.022, 0.012, e, lados=10)   # bujão
    if faixa is not None:
        cil(faixa, c + e * h * 0.0, r + 0.003, 0.08, e, lados=28)


bm, ba = bmesh.new(), bmesh.new()                                                # tambor do óleo
tambor(bm, ba, OT + Vector((0, 0, 0.29)), 0.12, 0.42)
obj('tambor_oleo', bm, 'tambor')
obj('tambor_oleo_aros', ba, 'grafite')

# ------------------------------------------------------------------ prensa compactadora (sudoeste)
PC = Vector((-0.6, -0.68, 0))
bm = bmesh.new()
caixa_de(bm, (PC.x - 0.28, PC.y - 0.27, 0.08), (PC.x + 0.28, PC.y + 0.27, 0.11))  # mesa
for sx in (-1, 1):
    for sy in (-1, 1):
        caixa_de(bm, (PC.x + sx * 0.22 - 0.03, PC.y + sy * 0.21 - 0.03, 0.11), (PC.x + sx * 0.22 + 0.03, PC.y + sy * 0.21 + 0.03, 1.03))
for sy in (-1, 1):
    caixa_de(bm, (PC.x - 0.26, PC.y + sy * 0.21 - 0.04, 0.95), (PC.x + 0.26, PC.y + sy * 0.21 + 0.04, 1.05))
caixa_de(bm, (PC.x - 0.12, PC.y - 0.25, 0.95), (PC.x + 0.12, PC.y + 0.25, 1.05))  # travessa do cilindro
obj('prensa', bm, 'amarelo')
bm = bmesh.new()
for sx in (-1, 1):                                                               # guias da placa
    cil(bm, Vector((PC.x + sx * 0.16, PC.y, 0.55)), 0.013, 0.8, lados=10)
obj('prensa_guias', bm, 'cromo')
bm = bmesh.new()
cil(bm, PC + Vector((0, 0, 1.3)), 0.065, 0.5, lados=24)                          # camisa do cilindro principal
cil(bm, PC + Vector((0, 0, 1.06)), 0.085, 0.03, lados=24)
cil(bm, PC + Vector((0, 0, 1.55)), 0.08, 0.03, lados=24)
suavizar(obj('prensa_cilindro', bm, 'grafite'))
bm, ba = bmesh.new(), bmesh.new()
tambor(bm, ba, PC + Vector((0, 0, 0.31)), 0.15, 0.4)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY')   # tambor aberto
obj('prensa_tambor', bm, 'tambor')
obj('prensa_tambor_aros', ba, 'grafite')
bm = bmesh.new()
cil(bm, PC + Vector((0, 0, 0.12)), 0.148, 0.01, lados=28)                         # fundo do tambor
cil(bm, PC + Vector((0, 0, 0.3)), 0.146, 0.36, lados=28)                          # lodo compactado dentro
obj('prensa_lodo', bm, 'lodo')
placa = bpy.data.objects.new('prensa_placa', None)
sc.collection.objects.link(placa)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0)), 0.12, 0.04, lados=28)
caixa(bm, (0, 0, 0.03), (0.36, 0.06, 0.03))                                     # travessa nas guias
for sx in (-1, 1):
    cil(bm, Vector((sx * 0.16, 0, 0.03)), 0.024, 0.05, lados=12)
obj('prensa_placa', bm, 'ferro', placa)
bm = bmesh.new()
cil(bm, Vector((0, 0, 0.36)), 0.03, 0.66, lados=16)
suavizar(obj('prensa_haste', bm, 'cromo', placa))
bm = bmesh.new()                                                                 # rosca de lodo: silo → boca lateral do tambor
SA = Vector((-0.31, -0.31, 0.72))
SB = PC + Vector((0.115, 0.115, 0.62))
tubo(bm, SA, SB, 0.045, 20)
cil(bm, SA + (SB - SA).normalized() * 0.02, 0.06, 0.03, SB - SA, lados=20)
cil(bm, SA.lerp(SB, 0.4), 0.075, 0.12, SB - SA, lados=20)                        # motor da rosca
suavizar(obj('rosca', bm, 'casco'))
bm = bmesh.new()
SBb = SB + (SB - SA).normalized() * 0.02
cil(bm, SBb + Vector((0, 0, -0.03)), 0.04, 0.06, lados=14)                        # bica que desce para o tambor
obj('rosca_bica', bm, 'ferro')
bm = bmesh.new()                                                                 # unidade hidráulica e mangueiras
caixa_de(bm, (-0.96, -0.4, 0.08), (-0.8, -0.26, 0.3))
cil(bm, Vector((-0.88, -0.33, 0.34)), 0.05, 0.08, lados=14)
obj('hidraulica', bm, 'grafite')
bm = bmesh.new()
mangueira(bm, bezier((-0.88, -0.3, 0.38), (-0.88, -0.3, 0.9), (-0.75, -0.6, 1.2), PC + Vector((-0.06, 0.03, 1.12)), 14), 0.011)
mangueira(bm, bezier((-0.85, -0.36, 0.38), (-0.8, -0.4, 1.0), (-0.72, -0.6, 1.6), PC + Vector((-0.06, -0.03, 1.48)), 16), 0.011)
obj('hidraulica_mangueiras', bm, 'borracha')

# ------------------------------------------------------------------ tambores de resíduo compactado empilhados (sudeste)
bm = bmesh.new()
caixa_de(bm, (0.28, -0.92, 0.08), (0.94, -0.52, 0.1))
for x in (0.3, 0.6, 0.9):
    caixa_de(bm, (x - 0.02, -0.92, 0.1), (x + 0.02, -0.52, 0.14))
obj('estrado', bm, 'grafite')
bm, ba, bf = bmesh.new(), bmesh.new(), bmesh.new()
tambor(bm, ba, (0.44, -0.72, 0.36), 0.145, 0.42, faixa=bf)
tambor(bm, ba, (0.76, -0.72, 0.36), 0.145, 0.42, faixa=bf)
tambor(bm, ba, (0.6, -0.72, 0.587 + 0.145), 0.145, 0.42, EX)
obj('tambores', bm, 'tambor')
obj('tambores_aros', ba, 'grafite')
obj('tambores_faixa', bf, 'listras')

# ------------------------------------------------------------------ chão em volta: lama e óleo, com a faixa limpa varrida
def sst(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def sujeira(x, y):
    """0 = chão limpo, 1 = lama. Manchas por ruído que rareiam com a distância; faixa varrida pelos bocais limpa."""
    d = math.hypot(x, y)
    dens = noise.noise(Vector((x * 1.4, y * 1.4, 2.0))) * 0.5 + noise.noise(Vector((x * 5, y * 5, 4.0))) * 0.25
    v = sst(-0.06, 0.06, dens - (-0.3 + (d - 1.3) * 0.3))
    for lado in (1, -1):
        rx, ry = lado * (x - lado * TORRE_X), y
        r = math.hypot(rx, ry)
        a = abs(math.atan2(ry, rx))
        borda = 0.02 * noise.noise(Vector((x * 14, y * 14, 1)))
        c = sst(0.3, 0.38, r) * (1 - sst(0.76, 0.81, r + borda)) * (1 - sst(0.74, 0.86, a + borda * 2))
        v *= 1 - c
        VARR[0] = max(VARR[0], c)
    return v


VARR = [0.0]


def chao_mat():
    """Chão de terra batida; a máscara 'sujo' (por vértice) mistura lama molhada, com borda irregular e relevo."""
    m = bpy.data.materials.new('Chão sujo')
    nt = m.node_tree
    no = mats.no
    b = nt.nodes['Principled BSDF']
    geo = no(nt, 'ShaderNodeNewGeometry')
    at = no(nt, 'ShaderNodeAttribute', attribute_name='sujo')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 8.0, 'Roughness': 0.6})
    nt.links.new(geo.outputs['Position'], ru.inputs['Vector'])
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 60.0, 'Detail': 6.0})
    nt.links.new(geo.outputs['Position'], fino.inputs['Vector'])
    soma = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(ru.outputs['Fac'], soma.inputs[0])
    soma.inputs[1].default_value = 0.35
    nt.links.new(at.outputs['Fac'], soma.inputs[2])
    mk = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.62, 'From Max': 0.7})
    nt.links.new(soma.outputs['Value'], mk.inputs['Value'])
    terra = no(nt, 'ShaderNodeMix', data_type='RGBA')
    terra.inputs[6].default_value = (0.33, 0.30, 0.26, 1)
    terra.inputs[7].default_value = (0.24, 0.22, 0.19, 1)
    nt.links.new(ru.outputs['Fac'], terra.inputs[0])
    av = no(nt, 'ShaderNodeAttribute', attribute_name='varrido')                  # faixa varrida: úmida, mais escura
    umido = no(nt, 'ShaderNodeMix', data_type='RGBA')
    umido.inputs[7].default_value = (0.25, 0.24, 0.225, 1)
    nt.links.new(av.outputs['Fac'], umido.inputs[0])
    nt.links.new(terra.outputs[2], umido.inputs[6])
    terra = umido
    lama = no(nt, 'ShaderNodeMix', data_type='RGBA')
    lama.inputs[6].default_value = (0.11, 0.075, 0.04, 1)
    lama.inputs[7].default_value = (0.05, 0.035, 0.02, 1)
    nt.links.new(fino.outputs['Fac'], lama.inputs[0])
    cor = no(nt, 'ShaderNodeMix', data_type='RGBA')
    nt.links.new(mk.outputs['Result'], cor.inputs[0])
    nt.links.new(terra.outputs[2], cor.inputs[6])
    nt.links.new(lama.outputs[2], cor.inputs[7])
    nt.links.new(cor.outputs[2], b.inputs['Base Color'])
    rg = no(nt, 'ShaderNodeMapRange', **{'To Min': 0.88, 'To Max': 0.18})
    nt.links.new(mk.outputs['Result'], rg.inputs['Value'])
    rr = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(fino.outputs['Fac'], rr.inputs[0])
    rr.inputs[1].default_value = 0.25
    rv = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    nt.links.new(av.outputs['Fac'], rv.inputs[0])
    rv.inputs[1].default_value = -0.3
    nt.links.new(rg.outputs['Result'], rv.inputs[2])
    nt.links.new(rv.outputs['Value'], rr.inputs[2])
    nt.links.new(rr.outputs['Value'], b.inputs['Roughness'])
    h = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(mk.outputs['Result'], h.inputs[0])
    nt.links.new(fino.outputs['Fac'], h.inputs[1])
    bp = no(nt, 'ShaderNodeBump', **{'Strength': 0.35, 'Distance': 0.01})
    nt.links.new(h.outputs['Value'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


base3d.M['chao_sujo'] = chao_mat()
bm = bmesh.new()
PASSO, EXT = 0.03, 3.2
N = int(2 * EXT / PASSO)
V, SUJ, VAR = [], [], []
for j in range(N + 1):
    for i in range(N + 1):
        x, y = -EXT + i * PASSO, -EXT + j * PASSO
        VARR[0] = 0.0
        v = sujeira(x, y) if max(abs(x), abs(y)) > 0.98 else 0.0
        SUJ.append(v)
        VAR.append(VARR[0])
        V.append(bm.verts.new((x, y, 0.001 + 0.007 * v)))
for j in range(N):
    for i in range(N):
        a = j * (N + 1) + i
        bm.faces.new((V[a], V[a + 1], V[a + N + 2], V[a + N + 1]))
chao_lama = obj('lama_chao', bm, 'chao_sujo')
at = chao_lama.data.attributes.new('sujo', 'FLOAT', 'POINT')
at.data.foreach_set('value', SUJ)
at = chao_lama.data.attributes.new('varrido', 'FLOAT', 'POINT')
at.data.foreach_set('value', VAR)
for pg in chao_lama.data.polygons:
    pg.use_smooth = True
bm = bmesh.new()
for c, r, z in (((-1.6, 0.9), 0.16, 0.0095), ((1.5, 1.2), 0.12, 0.0095), ((-1.3, -1.5), 0.18, 0.0095), ((1.8, -0.9), 0.1, 0.0095),
                ((0.2, 0.3), 0.06, 0.0822), ((-0.3, -0.9), 0.07, 0.0822), ((0.78, 0.45), 0.05, 0.0822)):
    mancha_lisa(bm, c, r, z)
obj('oleo_poças', bm, 'oleo')
bm = bmesh.new()
for k in range(14):                                                              # lama na laje (respingos, rastros)
    c = (random.uniform(-0.95, 0.95), random.uniform(-0.95, 0.95))
    if math.hypot(*c) < R_SILO + 0.05:
        continue
    mancha(bm, c, random.uniform(0.04, 0.1), 0.0815)
obj('laje_lama', bm, 'lama_seca')
bm = bmesh.new()
for k in range(70):                                                              # respingos na laje e no pé do silo
    a = random.uniform(0, 2 * PI)
    r = random.uniform(R_SILO + 0.03, 0.75)
    gota(bm, (math.cos(a) * r, math.sin(a) * r, 0.083), random.uniform(0.006, 0.018), 0.3)
for k in range(30):
    gota(bm, (PC.x + random.uniform(-0.25, 0.25), PC.y + random.uniform(-0.25, 0.25), 0.112), random.uniform(0.006, 0.016), 0.3)
for k in range(40):                                                              # respingos subindo na base do silo
    f = random.randrange(8)
    a = f * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    z = 0.09 + random.expovariate(9.0)
    if z > 0.6 or (f == 6 and z > 0.27):
        continue
    gota(bm, d * (AP + 0.002) + t * random.uniform(-0.16, 0.16) + Vector((0, 0, z)), random.uniform(0.005, 0.012), 0.6)
obj('respingos', bm, 'lama')


def escorrido(bm, base, d, t, z_top, comp, larg):
    """Lama escorrendo numa parede de normal d: filete que afina e termina numa gota."""
    n = 6
    for k in range(n):
        f = k / n
        w = larg * (1 - 0.6 * f)
        caixa(bm, base + d * 0.003 + Vector((0, 0, z_top - comp * (f + 0.5 / n))), (0.004, w, comp / n + 0.002), Matrix.Rotation(math.atan2(d.y, d.x), 3, 'Z'))
    gota(bm, base + d * 0.006 + Vector((0, 0, z_top - comp)), larg * 0.7, 1.2)


bm = bmesh.new()
for k in range(5):                                                               # sob o visor (vazou da vedação)
    x = random.uniform(-0.09, 0.09)
    escorrido(bm, Vector((x, YV - 0.045, 0)), -EY, EX, 0.28, random.uniform(0.06, 0.16), random.uniform(0.012, 0.022))
for k in range(16):                                                              # do teto (eclusa transborda) pelas faces
    f = random.choice((0, 1, 2, 3, 4, 5, 7))
    a = f * PI / 4
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    escorrido(bm, d * AP + t * random.uniform(-0.14, 0.14), d, t, Z_SILO - 0.01, random.uniform(0.12, 0.45), random.uniform(0.012, 0.03))
for k in range(5):                                                               # tambor da prensa
    a = random.uniform(0, 2 * PI)
    d = Vector((math.cos(a), math.sin(a), 0))
    escorrido(bm, PC.xy.to_3d() + d * 0.15, d, Vector((-d.y, d.x, 0)), 0.51, random.uniform(0.08, 0.22), random.uniform(0.012, 0.022))
for x in (0.44, 0.76):                                                           # tambores empilhados
    for k in range(2):
        a = random.uniform(-2.2, -0.9)
        d = Vector((math.cos(a), math.sin(a), 0))
        escorrido(bm, Vector((x, -0.72, 0)) + d * 0.145, d, Vector((-d.y, d.x, 0)), 0.57, random.uniform(0.1, 0.25), random.uniform(0.012, 0.02))
obj('escorridos', bm, 'lama')
bm = bmesh.new()
gota(bm, (0, 0, Z_TETO + 0.025), 0.12, 0.25)                                     # lama em volta da eclusa
for k in range(8):
    a = random.uniform(0, 2 * PI)
    gota(bm, (math.cos(a) * random.uniform(0.12, 0.24), math.sin(a) * random.uniform(0.12, 0.24), Z_TETO + 0.012), random.uniform(0.02, 0.05), 0.3)
obj('teto_lama', bm, 'lama')

# ------------------------------------------------------------------ gotas animadas, vapor
gotas = []
for k in range(4):                                                               # pingando da bica da rosca no tambor
    bm = bmesh.new()
    gota(bm, (0, 0, 0), 0.012, 1.4)
    gotas.append(obj('gota', bm, 'lama'))
vapores = []
for k in range(7):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    vapores.append(obj('vapor', bm, 'vapor'))

# ------------------------------------------------------------------ animação (laço de 4 s)
def suave(x):
    return x * x * (3 - 2 * x)


for q in range(1, QUADROS + 1):
    fr = (q - 1) / QUADROS
    for i, b in enumerate(BRACOS):
        fase = 0.0 if i == 0 else 0.5
        yaw = 0.5 * math.sin(2 * PI * (fr + fase))
        p = 0.035 * math.sin(4 * PI * (fr + fase)) + 0.01
        g = b['giro']
        g.rotation_euler = (0, 0, yaw + (0 if b['lado'] > 0 else PI))
        g.keyframe_insert('rotation_euler', frame=q)
        b['lanca'].rotation_euler = (0, -p, 0)
        b['lanca'].keyframe_insert('rotation_euler', frame=q)
        Rp = Matrix.Rotation(-p, 3, 'Y')
        A = b['A']
        Bp = Vector((0, 0, P)) + Rp @ b['B']
        dr = (Bp - A).normalized()
        b['camisa'].location = A
        b['camisa'].rotation_quaternion = dr.to_track_quat('Z', 'Y')
        b['haste'].location = Bp
        b['haste'].rotation_quaternion = (-dr).to_track_quat('Z', 'Y')
        for o in (b['camisa'], b['haste']):
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('rotation_quaternion', frame=q)
        for o, cam, u0 in b['contas']:
            u = (u0 + fr * 2) % 1.0
            idx = u * (len(cam) - 1)
            k0 = int(idx)
            pos = cam[k0].lerp(cam[min(k0 + 1, len(cam) - 1)], idx - k0)
            o.location = pos
            o.scale = [max(0.05, 1.0 - 0.7 * u)] * 3
            o.keyframe_insert('location', frame=q)
            o.keyframe_insert('scale', frame=q)
    rotor.rotation_euler = (0, 0, -2 * PI * 9 * fr)
    rotor.keyframe_insert('rotation_euler', frame=q)
    # prensa: desce devagar (0–0,55), segura, sobe (0,7–1)
    if fr < 0.55:
        s = suave(fr / 0.55)
    elif fr < 0.7:
        s = 1.0
    else:
        s = 1.0 - suave((fr - 0.7) / 0.3)
    placa.location = PC + Vector((0, 0, 0.88 - 0.36 * s))
    placa.keyframe_insert('location', frame=q)
    em = base3d.M['anel_campo'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    em.default_value = 8 + 4 * math.sin(2 * PI * 6 * fr) ** 2
    em.keyframe_insert('default_value', frame=q)
    for k, o in enumerate(gotas):
        tt = ((k / len(gotas) + fr * 3) % 1.0)
        o.location = SBb + Vector((0, 0, -0.07 - 0.25 * tt * tt))
        o.scale = [1.0 if tt < 0.9 else 0.01] * 3
        o.keyframe_insert('location', frame=q)
        o.keyframe_insert('scale', frame=q)
    for k, o in enumerate(vapores):
        u = (k / len(vapores) + fr) % 1.0
        o.location = Vector((0.25 * u * u + 0.03 * math.sin(k * 2.0), 0.1 * u, 2.2 + 0.75 * u))
        o.scale = [0.1 + 0.28 * u] * 3
        o.rotation_euler = (k, u * 2, k * 0.5)
        for c in ('location', 'scale', 'rotation_euler'):
            o.keyframe_insert(c, frame=q)
for o in list(sc.objects) + list(bpy.data.materials):
    ad = getattr(o, 'animation_data', None)
    if o in bpy.data.materials.values() and o.node_tree:
        ad = o.node_tree.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ cena: chão, luz, câmera
bm = bmesh.new()
caixa(bm, (0, 0, -0.5), (12, 12, 1.0))
obj('chao', bm, 'chao_sujo')
sol = bpy.data.lights.new('Sol', 'SUN')
sol.energy = 4.0
sol.angle = math.radians(2.5)
so = bpy.data.objects.new('Sol', sol)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-35))
mundo = bpy.data.worlds.new('Mundo')
sc.world = mundo
bg = mundo.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.55, 0.62, 0.75, 1)
bg.inputs['Strength'].default_value = 0.55
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
sc.view_settings.exposure = -0.5
cam_d = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def mirar(pos, alvo, lente):
    cam.location = pos
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lente


ALVO = (0.0, 0.0, 0.85)
VISTAS = ((300, 2.1), (210, 2.4), (120, 2.6), (30, 2.0))
modo = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'foto'
sc.frame_set(int(QUADROS * 0.12) + 1)
if modo in ('foto', 'teste'):
    teste = modo == 'teste'
    sc.cycles.samples = 24 if teste else 128
    esc = 0.5 if teste else 1.0
    sc.render.resolution_x, sc.render.resolution_y = int(1100 * esc), int(1300 * esc)
    vistas = VISTAS[:1] if teste else VISTAS
    for i, (ang, alt) in enumerate(vistas):
        a = math.radians(ang)
        mirar(Vector(ALVO) + Vector((math.cos(a) * 5.0, math.sin(a) * 5.0, alt)), ALVO, 34)
        sc.render.filepath = os.path.join(AQUI, ('coletor_lixo_teste%d.png' if teste else 'coletor_lixo_%d.png') % i)
        bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y = int(1300 * esc), int(1000 * esc)
    mirar((2.55, -1.55, 0.95), (1.15, 0.05, 0.3), 32)                            # de perto: bocal leste, fios e faixa limpa
    sc.render.filepath = os.path.join(AQUI, 'coletor_lixo_teste_perto.png' if teste else 'coletor_lixo_perto.png')
    bpy.ops.render.render(write_still=True)
    mirar((-0.55, -2.35, 1.05), (-0.25, -0.5, 0.6), 30)                          # de perto: visor, prensa, tambores
    sc.render.filepath = os.path.join(AQUI, 'coletor_lixo_teste_perto2.png' if teste else 'coletor_lixo_perto2.png')
    bpy.ops.render.render(write_still=True)
print('COLETOR ok')
