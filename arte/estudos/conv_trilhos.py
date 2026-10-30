"""Entradas do para_jogo.py para a FERROVIA (trilho_reto, trilho_curva, trilho_fim, sinal_trem) e o TREM
(locomotiva, vagao_carga, vagao_tanque).

estudo_trilhos.py é uma cena conjunta: reto (0,−2) → reto (0,−1) → curva (0..3, 0..3) → reto (3,2) → fim (4,2) e o
sinal em (1,−2). `centro` gira cada peça para a orientação das portas TRILHO do .json (entra pelo sul).
- O reto do jogo é o reto (3,2) do estudo (lastro inteiro nas duas pontas, emenda na entrada; o (0,−2) tem talude).
- `depois_de_montar` RECORTA a cena no tile: ilha pequena (pedra, folha de capim, parafuso) que cruza a borda sai;
  peça comprida (trilho, lastro, tala, eletroduto) é cortada no plano da borda. Assim a meia tala da peça vizinha
  fica e as emendas fecham dos dois lados. Os halos (degradê pelo Generated) saem: assados viram disco chapado.
  A via desce 3 mm: topo do boleto em 0,140 (TRILHO_FERRO_Z de lib_pf, onde a roda do trem apoia).
- Malha baixa da via feita à mão (`reduzir` trocado): lastro em perfil, dormentes, placas, trilho de perfil
  simplificado (patim/alma/boleto) e contratrilho, no mesmo caminho e superelevação do estudo — a cor (brita, mato,
  grampos, óleo) vem do assado do detalhado. No fim de linha o para-choque é o do estudo, dizimado.
  Nas bordas o perfil é idêntico em todas as peças (lastro, trilhos a ±0,24, boleto a 0,140): a emenda casa.
- Trilhos vão em lote (DesenhoLotes: MultiMesh com a 1ª malha do .glb): sem animação e tudo numa malha só
  (`antes_de_exportar` junta a luz do para-choque ao corpo).

estudo_trem.py tem locomotiva (y 3), vagão de carga (y 0) e vagão-tanque (y −3) engatados sobre um trecho de via.
- Fica só o veículo (os outros, a via, o lastro, as pedras e o chão saem); pose de repouso (sem balanço da
  suspensão); animação do estudo fora (o jogo não toca animação no trem).
- Partes que o jogo mexe: truque0 (y −0,85) e truque1 (y +0,85), pivô no centro do truque; o DesenhoTrens gira
  "*truque0"/"*truque1". Os vazios do estudo com o mesmo nome ganham sufixo _e (senão a parte viraria
  "truque0.001" e o jogo não a acharia).
- Vagão de carga: o minério do estudo vira a parte "pilha" (o jogo mostra só com carga); tampas de um lado abertas
  (quadro 39 do laço), as do outro fechadas."""
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix

PI = math.pi
Z = Vector((0, 0, 1))


# ------------------------------------------------------------------ utilidades
def _g():
    """Globais do para_jogo.py (quem chamou o gancho)."""
    f = sys._getframe(1)
    while f is not None:
        if 'montar_estudo' in f.f_globals and 'reduzir' in f.f_globals:
            return f.f_globals
        f = f.f_back
    raise RuntimeError('para_jogo.py não encontrado na pilha')


def _apagar(o):
    for c in list(o.children):
        _apagar(c)
    bpy.data.objects.remove(o, do_unlink=True)


def _vivos(sc):
    for nome in [o.name for o in sc.objects]:
        o = bpy.data.objects.get(nome)
        if o is not None:
            yield o


def _soltar(o):
    """Tira o objeto da cena sem mexer nos filhos (que guardam a posição no mundo)."""
    for c in list(o.children):
        mw = c.matrix_world.copy()
        c.parent = o.parent
        c.matrix_world = mw
    bpy.data.objects.remove(o, do_unlink=True)


def _sem_animacao(sc):
    for o in sc.objects:
        o.animation_data_clear()


def _ilhas(bm):
    bm.verts.index_update()
    visto = bytearray(len(bm.verts))
    out = []
    for v in bm.verts:
        if visto[v.index]:
            continue
        visto[v.index] = 1
        pilha, comp = [v], []
        while pilha:
            a = pilha.pop()
            comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if not visto[b.index]:
                    visto[b.index] = 1
                    pilha.append(b)
        out.append(comp)
    return out


def recortar(sc, w, d, tol=2e-4, ilha_max=0.05):
    """Tudo fica dentro do tile: ilha pequena que cruza a borda sai inteira, peça comprida é cortada na borda."""
    hx, hy = w / 2, d / 2
    planos = [(Vector((hx, 0, 0)), Vector((1, 0, 0))), (Vector((-hx, 0, 0)), Vector((-1, 0, 0))),
              (Vector((0, hy, 0)), Vector((0, 1, 0))), (Vector((0, -hy, 0)), Vector((0, -1, 0)))]
    bpy.context.view_layer.update()
    for o in _vivos(sc):
        if o.type != 'MESH':
            continue
        mw = o.matrix_world.copy()
        cs = [mw @ Vector(c) for c in o.bound_box]
        if all(-hx - tol <= c.x <= hx + tol and -hy - tol <= c.y <= hy + tol for c in cs):
            continue
        if o.data.users > 1:
            o.data = o.data.copy()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        tirar = []
        for comp in _ilhas(bm):
            ps = [mw @ v.co for v in comp]
            x0, x1 = min(p.x for p in ps), max(p.x for p in ps)
            y0, y1 = min(p.y for p in ps), max(p.y for p in ps)
            fora = x1 <= -hx + tol or x0 >= hx - tol or y1 <= -hy + tol or y0 >= hy - tol
            cruza = x0 < -hx - tol or x1 > hx + tol or y0 < -hy - tol or y1 > hy + tol
            if fora or (cruza and max(x1 - x0, y1 - y0) < ilha_max):
                tirar += comp
        if tirar:
            bmesh.ops.delete(bm, geom=tirar, context='VERTS')
        inv = mw.inverted()
        rot_t = mw.to_3x3().transposed()
        for co, no in planos:
            if not bm.verts:
                break
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6,
                                   plane_co=inv @ co, plane_no=(rot_t @ no).normalized(), clear_outer=True)
        vazio = not bm.faces
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        if vazio:
            _soltar(o)


def _marcar_detalhe(objs, grupo='detalhe'):
    for o in objs:
        if o.type != 'MESH':
            continue
        vg = o.vertex_groups.get(grupo) or o.vertex_groups.new(name=grupo)
        vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')


# ------------------------------------------------------------------ via baixa (mesmas medidas do estudo_trilhos.py)
G = 0.24            # meia bitola
ZDT = 0.080         # topo do dormente
ZTB = ZDT + 0.007   # base do trilho
HT = 0.056          # altura do trilho
ZR = 0.06           # eixo de giro da superelevação
UD = 0.38
UB = 0.42
CANT = math.asin(0.012 / (2 * G))
DZ = -0.003         # a via desce 3 mm: boleto em 0,140
_TR = [(0.022, 0.0), (0.022, 0.005), (0.0035, 0.011), (0.0035, 0.036), (0.0115, 0.040), (0.0115, 0.053), (0.007, 0.056)]
PERFIL_TR = _TR + [(-w, z) for (w, z) in reversed(_TR)]
LASTRO = [(-UB, 0.0), (-0.40, 0.03), (-0.37, 0.058), (0.37, 0.058), (0.40, 0.03), (UB, 0.0)]


class Reta:
    def __init__(s, a, b):
        s.a, s.b = Vector(a), Vector(b)
        s.L = (s.b - s.a).length
        s.t = (s.b - s.a).normalized()

    def pc(s, x):
        return s.a + s.t * x

    def tang(s, x):
        return s.t


class Arco:
    def __init__(s, c, R, th0, th1):
        s.c, s.R, s.th0 = Vector(c), R, th0
        s.sg = 1 if th1 > th0 else -1
        s.L = R * abs(th1 - th0)

    def pc(s, x):
        t = s.th0 + s.sg * x / s.R
        return s.c + Vector((math.cos(t), math.sin(t), 0)) * s.R

    def tang(s, x):
        t = s.th0 + s.sg * x / s.R
        return Vector((-math.sin(t), math.cos(t), 0)) * s.sg


def quadro(cam, x, rolar=0.0):
    p, t = cam.pc(x), cam.tang(x)
    n0 = Z.cross(t).normalized()
    n = n0 * math.cos(rolar) + Z * math.sin(rolar)
    up = -n0 * math.sin(rolar) + Z * math.cos(rolar)
    return lambda u, a, z: p + t * a + n * u + up * (z - ZR) + Z * (ZR + DZ)


def varrer(bm, cam, xs, perfil, u0, z0, rolar, esc=None, fechar=False):
    aneis = []
    for x in xs:
        Q = quadro(cam, x, rolar(x))
        e = esc(x) if esc else 1.0
        aneis.append([bm.verts.new(Q(u0 + w * (1 + 0.12 * (1 - e)), 0, z0 + max(z * e, min(z, 0.003)))) for (w, z) in perfil])
    k = len(perfil)
    for A, B in zip(aneis, aneis[1:]):
        for j in range(k if fechar else k - 1):
            bm.faces.new((A[j], A[(j + 1) % k], B[(j + 1) % k], B[j]))


def bloco(bm, Q, u0, u1, a0, a1, z0, z1, a0t=None, a1t=None):
    """Caixa sem fundo (topo pode ser mais estreito: dormente trapezoidal)."""
    a0t = a0 if a0t is None else a0t
    a1t = a1 if a1t is None else a1t
    b = [bm.verts.new(Q(*p)) for p in ((u0, a0, z0), (u1, a0, z0), (u1, a1, z0), (u0, a1, z0))]
    t = [bm.verts.new(Q(*p)) for p in ((u0, a0t, z1), (u1, a0t, z1), (u1, a1t, z1), (u0, a1t, z1))]
    bm.faces.new(t)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((b[i], b[j], t[j], t[i]))


def via_baixa(cam, cant=False, contra=None, fim=False, n_curva=1):
    """Malha baixa da via no caminho cam (x = 0 na borda de entrada)."""
    L = cam.L
    bm = bmesh.new()
    if cant:
        def rolar(x):
            r = max(0.0, min(1.0, x / (0.3 * L), (L - x) / (0.3 * L)))
            return CANT * r * r * (3 - 2 * r)
    else:
        def rolar(x):
            return 0.0
    n_d = int(round(L / 0.2)) if not fim else 5
    esp = L / n_d if not fim else 0.2
    xs_d = [(k + 0.5) * esp for k in range(n_d)]
    x_leito = L if not fim else 0.98
    x_tr = L if not fim else 0.92

    def amostras(x1, n):
        return [x1 * i / n for i in range(n + 1)]
    # lastro (no fim desce em talude)
    if fim:
        def rampa(x):
            return max(0.0, min(1.0, (x_leito - x) / 0.07))
        xs_l = [0.0, x_leito - 0.07, x_leito - 0.035, x_leito]
    else:
        rampa = None
        xs_l = amostras(L, max(1, n_curva // 2))
    varrer(bm, cam, xs_l, LASTRO, 0.0, 0.0, rolar, esc=rampa)
    # dormentes e placas de apoio
    for xd in xs_d:
        Q = quadro(cam, xd, rolar(xd))
        bloco(bm, Q, -UD, UD, -0.04, 0.04, 0.045, ZDT, -0.034, 0.034)
        for u0 in (-G, G):
            bloco(bm, Q, u0 - 0.047, u0 + 0.047, -0.03, 0.03, ZDT, ZTB)
    # trilhos
    for u0 in (-G, G):
        varrer(bm, cam, amostras(x_tr, n_curva), PERFIL_TR, u0, ZTB, rolar)
    # contratrilho (curva): barra de guarda junto ao trilho interno, pontas abertas
    if contra:
        x0, x1 = contra
        UG = -G + 0.034

        def ug(x):
            f = max(0.0, 1 - min(x - x0, x1 - x) / 0.14)
            return UG + 0.022 * f * f
        z0, z1 = ZTB + 0.016, ZTB + HT + 0.012
        n = 24
        aneis = []
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            Q = quadro(cam, x, rolar(x))
            u = ug(x)
            aneis.append([bm.verts.new(Q(*p)) for p in ((u - 0.005, 0, z0), (u - 0.005, 0, z1), (u + 0.005, 0, z1),
                                                        (u + 0.005, 0, z0))])
        for A, B in zip(aneis, aneis[1:]):
            for j in range(3):
                bm.faces.new((A[j], A[j + 1], B[j + 1], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def _baixo_da_via(g, nome_corpo, construir, alvo_det=0):
    """Troca o `reduzir`: o corpo vira a via baixa feita à mão + (se houver) a parte marcada 'detalhe' dizimada."""
    orig = g['reduzir']

    def reduzir(o, alvo):
        if o.name != nome_corpo:
            return orig(o, alvo)
        juntar = []
        vg = o.vertex_groups.get('detalhe')
        if vg is not None and alvo_det:
            det = g['copia'](o)
            bm = bmesh.new()
            bm.from_mesh(det.data)
            camada = bm.verts.layers.deform.active
            fora = [v for v in bm.verts if camada is None or vg.index not in v[camada]]
            bmesh.ops.delete(bm, geom=fora, context='VERTS')
            bm.to_mesh(det.data)
            bm.free()
            det.data.update()
            if det.data.polygons:
                orig(det, alvo_det)
                juntar.append(det)
            else:
                bpy.data.objects.remove(det, do_unlink=True)
        bm = construir()
        me = bpy.data.meshes.new(nome_corpo + '_via')
        bm.to_mesh(me)
        bm.free()
        via = bpy.data.objects.new(nome_corpo + '_via', me)
        bpy.context.scene.collection.objects.link(via)
        juntar.append(via)
        bm = bmesh.new()                       # o corpo detalhado some (o alto já foi copiado): fica o baixo
        bm.to_mesh(o.data)
        bm.free()
        o.vertex_groups.clear()
        bpy.ops.object.select_all(action='DESELECT')
        for j in juntar:
            j.select_set(True)
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.join()
        print('VIA BAIXA', nome_corpo, g['tris'](o), 'tris')
    g['reduzir'] = reduzir


def _via_montar(nome, w, d, construir, detalhe=None, alvo_det=0, tirar=()):
    def f(sc):
        g = _g()
        for o in _vivos(sc):
            n = o.name.lower()
            if n.startswith('halo') or any(t in n for t in tirar):
                _apagar(o)
        recortar(sc, w, d)
        base = sc.objects.get('_base')
        base.matrix_world = Matrix.Translation((0, 0, DZ)) @ base.matrix_world
        bpy.context.view_layer.update()
        _sem_animacao(sc)
        if detalhe:
            _marcar_detalhe([o for o in sc.objects if o.name.startswith(detalhe)])
        _baixo_da_via(g, nome + '_corpo', construir, alvo_det)
    return f


def _uma_malha(sc, raiz, dados):
    """DesenhoLotes usa só a 1ª malha do .glb: luzes da paleta entram no corpo (superfície própria)."""
    ms = [o for o in sc.objects if o.type == 'MESH']
    corpo = next((o for o in ms if o.name.endswith('_corpo')), None)
    outros = [o for o in ms if o is not corpo]
    if corpo is None or not outros:
        return
    bpy.ops.object.select_all(action='DESELECT')
    for o in outros:
        o.select_set(True)
    corpo.select_set(True)
    bpy.context.view_layer.objects.active = corpo
    bpy.ops.object.join()
    for e in [o for o in sc.objects if o.type == 'EMPTY' and o is not raiz and not o.name.startswith('PORTA_')
              and not o.children]:
        bpy.data.objects.remove(e, do_unlink=True)


# caminhos já no referencial da peça (depois do `centro`)
def _reto():
    return via_baixa(Reta((0, -0.5, 0), (0, 0.5, 0)))


def _curva():
    c = Arco((1.5, -1.5, 0), 2.5, PI, PI / 2)
    return via_baixa(c, cant=True, contra=(0.38, c.L - 0.38), n_curva=32)


def _fim():
    return via_baixa(Reta((0, -0.5, 0), (0, 0.5, 0)), fim=True)


# ------------------------------------------------------------------ sinal
def _sinal_montar(sc):
    for o in _vivos(sc):
        n = o.name.lower()
        if n.startswith('halo') or n.startswith('tufo') or n.startswith('erva') or n.startswith('marca_bloco'):
            _apagar(o)
    recortar(sc, 1, 1)
    _sem_animacao(sc)


def _sinal_exportar(sc, raiz, dados):
    """Luz verde do sinal: acesa fixa (o P_Cristal do jogo é o cristal que só acende com trabalho)."""
    for m in bpy.data.materials:
        if m.name.startswith('P_Cristal') and m.node_tree:
            p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            c = p.inputs['Emission Color'].default_value if p else (0, 0, 0, 1)
            if c[1] > c[0] and c[1] > c[2]:
                m.name = 'P_Sinal'


# ------------------------------------------------------------------ trem
def _trem_montar(nome, quadro=1):
    def f(sc):
        for o in _vivos(sc):
            if o.name != '_base' and o.parent is not None and o.parent.name == '_base' and o.name != nome:
                _apagar(o)
        sc.frame_set(quadro)
        _sem_animacao(sc)
        for o in sc.objects:                     # chanfro do estudo fora: no corpo juntado ele ia para a malha baixa
            o.modifiers.clear()                  # (faixas com UV esticada por cima das ilhas do atlas)
        for o in sc.objects:
            if not o.name.startswith(nome + '_') or o.type != 'EMPTY':
                continue
            suf = o.name[len(nome) + 1:]
            if suf == 'corpo':
                o.location, o.rotation_euler = (0, 0, 0.2), (0, 0, 0)
            elif suf.startswith('quadro'):
                o.location, o.rotation_euler = (0, 0, 0), (0, 0, 0)
            elif suf.startswith('molas'):
                o.scale = (1, 1, 1)
            o.name = o.name + '_e'               # o nome da parte (truque0, corpo) fica livre para a malha
        raiz_e = sc.objects.get(nome)
        if raiz_e is not None:
            raiz_e.name = nome + '_e'            # a raiz do .glb leva o nome do modelo
        bpy.context.view_layer.update()
    return f


def _truques(nome):
    return {'truque%d' % i: dict(objetos=['%s_truque%d_' % (nome, i), '%s_quadro%d_' % (nome, i),
                                          '%s_molas%d_' % (nome, i), '%s_rod%d-1_' % (nome, i), '%s_rod%d1_' % (nome, i)],
                                 pivo=(0, (2 * i - 1) * 0.85, 0.27), tris=900) for i in (0, 1)}


def _trem(nome, yc, tris, quadro=1, extra=None):
    partes = _truques(nome)
    partes.update(extra or {})
    return dict(script='estudo_trem.py', cat='transporte/veiculos', tris=tris, tex=1024, centro=(0, yc), margem=2.0,
                anima=False, tirar=['via_', 'trilho', 'pedra', 'lastro'], partes=partes,
                depois_de_montar=_trem_montar(nome, quadro))


CONFIG = {
    'trilho_reto': dict(script='estudo_trilhos.py', cat='transporte/trilhos', tris=800, tex=512, centro=(3.5, 2.5, -PI / 2),
                        anima=False, tirar=[], depois_de_montar=_via_montar('trilho_reto', 1, 1, _reto),
                        antes_de_exportar=_uma_malha),
    'trilho_curva': dict(script='estudo_trilhos.py', cat='transporte/trilhos', tris=2600, tex=1024, centro=(1.5, 1.5, 0.0),
                         anima=False, tirar=[], depois_de_montar=_via_montar('trilho_curva', 3, 3, _curva),
                         antes_de_exportar=_uma_malha),
    'trilho_fim': dict(script='estudo_trilhos.py', cat='transporte/trilhos', tris=2000, tex=1024, centro=(4.5, 2.5, -PI / 2),
                       anima=False, tirar=[], depois_de_montar=_via_montar('trilho_fim', 1, 1, _fim, 'para_choque', 1600),
                       antes_de_exportar=_uma_malha),
    'sinal_trem': dict(script='estudo_trilhos.py', cat='transporte/trilhos', tris=2400, tex=1024, centro=(1.5, -1.5, 0.0),
                       anima=False, tirar=[], depois_de_montar=_sinal_montar, antes_de_exportar=_sinal_exportar),
    'locomotiva': _trem('locomotiva', 3.0, 7000),
    'vagao_carga': _trem('vagao_carga', 0.0, 6000, quadro=39,
                         extra={'pilha': dict(objetos=['vagao_carga_leito_minerio', 'vagao_carga_corpo_minerio',
                                                       'vagao_carga_corpo_cristal'], pivo=(0, 0, 0), tris=700)}),
    'vagao_tanque': _trem('vagao_tanque', -3.0, 6000),
}
