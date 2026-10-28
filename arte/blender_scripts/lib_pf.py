"""Biblioteca comum dos modelos do PlanetaFactory (Blender 5.x, rodar em segundo plano).

Regras (ver arte/FICHA_DE_ESTILO.md):
- 1 tile = 1 m. Estrutura ocupa w×d tiles inteiros, origem no centro, chão em z = 0.
- Itens: cabem em 0,26×0,26×0,26 m, base em z = 0 (o jogo apoia no topo da lona, z = 0,16).
- Portas = Empties "PORTA_<ITEM|FLUIDO>_<ENT|SAI>_<lado><n>" no meio da borda de um tile,
  eixo +Y do Empty aponta para fora. O Godot lê esses nós.
- Portas com perfil (esteira/cano) são checadas vértice a vértice contra a peça de referência.
"""
import bpy, bmesh, math, os, random, json
from mathutils import Vector, Matrix

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modelos'))

# ------------------------------------------------------------------ paleta
def _cor(c, e=0, r=0.7, m=0.0):
    return dict(c=c, e=e, r=r, m=m)
PALETA = {
    # estrutura (industrial)
    'P_Concreto': _cor((0.36, 0.35, 0.33), r=0.85),
    'P_Escuro':   _cor((0.10, 0.11, 0.14)),
    'P_Metal':    _cor((0.42, 0.46, 0.52), r=0.5, m=0.3),
    'P_Cobre':    _cor((0.78, 0.42, 0.20), r=0.4, m=0.5),
    'P_Faixa':    _cor((0.95, 0.75, 0.15)),
    'P_Cristal':  _cor((0.15, 1.00, 0.75), e=4),
    'P_Esteira':  _cor((0.05, 0.05, 0.06), r=0.9),
    'P_Fogo':     _cor((1.00, 0.45, 0.10), e=5),
    'P_Vidro':    _cor((0.55, 0.80, 0.90), r=0.15),
    # itens / recursos
    'P_Pedra':    _cor((0.45, 0.43, 0.40), r=0.9),
    'P_Ferrugem': _cor((0.55, 0.22, 0.10), r=0.8),
    'P_Malaquita':_cor((0.10, 0.60, 0.50), r=0.6),
    'P_Carvao':   _cor((0.17, 0.17, 0.19), r=0.25),
    'P_Areia':    _cor((0.80, 0.68, 0.45), r=0.95),
    'P_Silex':    _cor((0.32, 0.37, 0.52), r=0.3),
    'P_Biomassa': _cor((0.55, 0.15, 0.75), e=1.5),
    'P_Aco':      _cor((0.26, 0.30, 0.36), r=0.35, m=0.6),
    'P_Tijolo':   _cor((0.62, 0.25, 0.18), r=0.9),
    'P_Placa':    _cor((0.08, 0.40, 0.18), r=0.6),
    'P_Municao':  _cor((0.30, 0.34, 0.20), r=0.7),
    # ambiente
    'P_Folha':    _cor((0.22, 0.48, 0.36), r=0.8),
    'P_FolhaClara': _cor((0.36, 0.62, 0.42), r=0.8),
    'P_Tronco':   _cor((0.30, 0.22, 0.20), r=0.9),
    'P_FungoCaule': _cor((0.78, 0.74, 0.66), r=0.8),
    'P_Chapeu':   _cor((0.30, 0.20, 0.28), r=0.7),     # chapéu de cogumelo (fosco; o brilho fica nas lamelas)
    'P_Lodo':     _cor((0.22, 0.26, 0.14), r=0.9),
    'P_Rocha':    _cor((0.38, 0.37, 0.38), r=0.9),
    'P_RochaEscura': _cor((0.24, 0.23, 0.25), r=0.9),
    'P_Seiva':    _cor((0.75, 0.55, 0.10), e=1.0, r=0.2),
    'P_Agua':     _cor((0.12, 0.42, 0.48), r=0.1),
    'P_Cinza':    _cor((0.30, 0.29, 0.30), r=0.95),
    # inimigos
    'P_Inimigo':  _cor((0.16, 0.10, 0.12), r=0.4, m=0.5),
    'P_OlhoInimigo': _cor((1.00, 0.10, 0.20), e=6),
}
NOMES = list(PALETA)

def material(nome):
    x = bpy.data.materials.get(nome)
    if x: return x
    d = PALETA[nome]; x = bpy.data.materials.new(nome); x.use_nodes = True
    b = x.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*d['c'], 1)
    b.inputs['Roughness'].default_value = d['r']; b.inputs['Metallic'].default_value = d['m']
    b.inputs['Emission Strength'].default_value = d['e']
    if d['e']: b.inputs['Emission Color'].default_value = (*d['c'], 1)
    x.diffuse_color = (*d['c'], 1)
    return x

def Q(v): return Vector((round(v[0], 6), round(v[1], 6), round(v[2], 6)))

# ------------------------------------------------------------------ medidas compartilhadas
LONA   = (-0.40, 0.40, 0.10, 0.16)
TRILHO = (0.40, 0.46, 0.04, 0.20)
FRISO  = (0.40, 0.46, 0.20, 0.225)
CANTO = 0.03          # zona livre em cada canto do tile (para pilares de 0,06 m da esteira elevada)
NIVEL = 0.5           # degrau de altura da esteira elevada
RAMPA_SOBE = 0.5      # subida por tile da rampa (~26,6°)
BITOLA = 0.50         # distância entre os eixos dos trilhos
LASTRO = (-0.42, 0.42, 0.0, 0.05)
TRILHO_FERRO_Z = (0.08, 0.14)   # boleto do trilho (topo = 0,14: onde a roda apoia)
DORMENTE_PASSO = 0.25
TOPO_LONA = 0.16
CANO_Z, CANO_R, FLANGE_R, FLANGE_L, CANO_LADOS = 0.35, 0.11, 0.15, 0.05, 8

# ------------------------------------------------------------------ parte (uma malha)
class Parte:
    def __init__(self, modelo, nome, pai=None, pivo=(0, 0, 0)):
        self.modelo, self.nome, self.pai, self.pivo = modelo, nome, pai, Vector(pivo)
        self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('UVMap')

    def _mi(self, mat): return NOMES.index(mat)

    def faces_de(self, verts, mat):
        for f in {f for v in verts for f in v.link_faces}: f.material_index = self._mi(mat)

    def caixa(self, x0, x1, y0, y1, z0, z1, mat):
        vs = [self.bm.verts.new(Q(c)) for c in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
        for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
            self.bm.faces.new([vs[i] for i in f]).material_index = self._mi(mat)
        return vs

    def chanfrar(self, verts, w):
        vs = set(verts)
        eds = [e for e in self.bm.edges if e.verts[0] in vs and e.verts[1] in vs and len(e.link_faces) == 2
               and e.calc_face_angle(0) > 0.5]
        if eds:
            res = bmesh.ops.bevel(self.bm, geom=eds, offset=w, segments=1, affect='EDGES', profile=0.5)
            for v in self.bm.verts: v.co = Q(v.co)

    def barra(self, a, b, larg, alt, mat, lado=(1, 0, 0)):
        """Barra de seção larg×alt ligando os pontos a→b (para braços articulados)."""
        a, b = Vector(a), Vector(b); u = (b - a).normalized(); s = Vector(lado).normalized()
        s = (s - u*s.dot(u)).normalized(); up = u.cross(s)
        cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        va = [self.bm.verts.new(Q(a + s*x*larg/2 + up*y*alt/2)) for x, y in cs]
        vb = [self.bm.verts.new(Q(b + s*x*larg/2 + up*y*alt/2)) for x, y in cs]
        mi = self._mi(mat)
        self.bm.faces.new(list(reversed(va))).material_index = mi; self.bm.faces.new(vb).material_index = mi
        for k in range(4): self.bm.faces.new((va[k], va[(k+1) % 4], vb[(k+1) % 4], vb[k])).material_index = mi
        return va + vb

    def caixa_c(self, cx, cy, cz, sx, sy, sz, mat, rot=0.0):
        """Caixa centrada em (cx,cy) com base em cz; rot em Z."""
        vs = self.caixa(-sx/2, sx/2, -sy/2, sy/2, 0, sz, mat)
        bmesh.ops.transform(self.bm, verts=vs, matrix=Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(rot, 4, 'Z'))
        for v in vs: v.co = Q(v.co)
        return vs

    def cil(self, c, r, h, mat, lados=8, eixo='Z', r2=None, rot=0.0):
        """Cilindro/tronco centrado em c, altura h ao longo do eixo."""
        R = {'Z': Matrix.Identity(4), 'X': Matrix.Rotation(math.pi/2, 4, 'Y'), 'Y': Matrix.Rotation(math.pi/2, 4, 'X')}[eixo]
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=lados, radius1=r, radius2=(r if r2 is None else r2), depth=h,
                                    matrix=Matrix.Translation(c) @ R @ Matrix.Rotation(rot, 4, 'Z'))
        for v in res['verts']: v.co = Q(v.co)
        self.faces_de(res['verts'], mat); return res['verts']

    def pedra(self, c, r, esc, mat, semente, sub=1, ruido=0.18):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=Matrix.Identity(4))
        rnd = random.Random(semente)
        for v in res['verts']:
            v.co = Vector((v.co.x*esc[0], v.co.y*esc[1], v.co.z*esc[2])) * (1 + rnd.uniform(-ruido, ruido)) + Vector(c)
            v.co = Q(v.co)
        self.faces_de(res['verts'], mat); return res['verts']

    def prisma(self, pts2d, z0, z1, mat, centro=(0, 0), rot=0.0, eixo='Z'):
        """Extruda um polígono 2D (ordem anti-horária)."""
        M = Matrix.Translation((*centro, 0)) @ Matrix.Rotation(rot, 4, 'Z')
        if eixo == 'X': M = M @ Matrix.Rotation(math.pi/2, 4, 'Y')
        if eixo == 'Y': M = M @ Matrix.Rotation(-math.pi/2, 4, 'X')
        base = [self.bm.verts.new(Q(M @ Vector((x, y, z0)))) for x, y in pts2d]
        topo = [self.bm.verts.new(Q(M @ Vector((x, y, z1)))) for x, y in pts2d]
        mi = self._mi(mat); n = len(pts2d)
        self.bm.faces.new(list(reversed(base))).material_index = mi
        self.bm.faces.new(topo).material_index = mi
        for i in range(n):
            self.bm.faces.new((base[i], base[(i+1) % n], topo[(i+1) % n], topo[i])).material_index = mi
        return base + topo

    def engrenagem(self, c, r_ext, r_int, dentes, esp, mat, eixo='Z'):
        pts = []
        for i in range(dentes):
            a0 = 2*math.pi*i/dentes; d = 2*math.pi/dentes
            for f, r in ((0.0, r_int), (0.15, r_ext), (0.45, r_ext), (0.6, r_int)):
                a = a0 + f*d; pts.append((math.cos(a)*r, math.sin(a)*r))
        return self.prisma(pts, c[2]-esp/2, c[2]+esp/2, mat, centro=(c[0], c[1]), eixo=eixo)

    def varrer(self, cam, perfil, mat, uv=False, tampa=(False, False)):
        """Varre retângulo (lat0,lat1,z0,z1) ao longo de cam=[(ponto, tangente exata)]."""
        aneis = []; dist = [0.0]; mi = self._mi(mat); N = len(cam)
        for i, (p, t) in enumerate(cam):
            lat0, lat1, z0, z1 = perfil(i/(N-1)) if callable(perfil) else perfil
            n = Vector((-t.y, t.x, 0)).normalized()
            if i: dist.append(dist[-1] + (p - cam[i-1][0]).length)
            aneis.append([self.bm.verts.new(Q(p + n*l + Vector((0, 0, z)))) for l, z in ((lat0,z0),(lat1,z0),(lat1,z1),(lat0,z1))])
        for i in range(len(aneis)-1):
            a, b = aneis[i], aneis[i+1]
            for k in range(4):
                f = self.bm.faces.new((a[k], a[(k+1) % 4], b[(k+1) % 4], b[k])); f.material_index = mi
                if uv:
                    for lp in f.loops:
                        j = 0 if lp.vert in a else 1; idx = (a, b)[j].index(lp.vert)
                        lp[self.uv].uv = (0.0 if idx in (0, 3) else 1.0, dist[i+j])
        for ring, fecha, rev in ((aneis[0], tampa[0], True), (aneis[-1], tampa[1], False)):
            if fecha: self.bm.faces.new(list(reversed(ring)) if rev else ring).material_index = mi

    def tubo(self, cam, r, mat, lados=CANO_LADOS, z=0.0, tampa=(False, False), lado=None):
        """Tubo de seção poligonal ao longo de cam (no plano XY, altura z). Pontas abertas por padrão."""
        aneis = []; mi = self._mi(mat)
        for p, t in cam:
            t = t.normalized()
            if lado is None: n = Vector((-t.y, t.x, 0)); up = Vector((0, 0, 1))
            else: n = Vector(lado); up = t.cross(n).normalized()      # caminho num plano vertical
            aneis.append([self.bm.verts.new(Q(p + Vector((0, 0, z)) + n*math.cos(2*math.pi*(k+0.5)/lados)*r + up*math.sin(2*math.pi*(k+0.5)/lados)*r))
                          for k in range(lados)])
        for i in range(len(aneis)-1):
            a, b = aneis[i], aneis[i+1]
            for k in range(lados):
                self.bm.faces.new((a[k], a[(k+1) % lados], b[(k+1) % lados], b[k])).material_index = mi
        for ring, fecha, rev in ((aneis[0], tampa[0], True), (aneis[-1], tampa[1], False)):
            if fecha: self.bm.faces.new(list(reversed(ring)) if rev else ring).material_index = mi

# ------------------------------------------------------------------ caminhos
def reto(a, b):
    a, b = Vector(a), Vector(b); t = (b - a).normalized(); return [(a, t), (b, t)]

def curva_canto(canto, r, a0, a1, seg=8):
    """Arco de centro `canto`, ângulos a0→a1 (rad), com tangente exata no sentido do percurso."""
    c = Vector(canto); out = []; s = 1 if a1 > a0 else -1
    for i in range(seg+1):
        a = a0 + (a1 - a0)*i/seg
        out.append((c + r*Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a)*s, math.cos(a)*s, 0))))
    return out

def girar_cam(cam, ang):
    R = Matrix.Rotation(ang, 3, 'Z'); return [(R @ p, R @ t) for p, t in cam]

# ------------------------------------------------------------------ blocos reutilizáveis
def esteira_trecho(p, cam, travessa=True):
    p.varrer(cam, LONA, 'P_Esteira', uv=True)
    giro = cam[0][1].cross(cam[-1][1]).z          # >0 vira à esquerda, <0 à direita
    for s in (-1, 1):
        interno = len(cam) > 2 and ((giro > 0) == (s > 0))
        def tr(f, s=s, z0=TRILHO[2], z1=TRILHO[3], interno=interno):
            fora = TRILHO[1] - (0.02*math.sin(math.pi*f) if interno else 0)   # afina no meio: livra o canto
            return (s*TRILHO[0], s*fora, z0, z1)
        p.varrer(cam, tr, 'P_Escuro')
        p.varrer(cam, lambda f, tr=tr: tr(f, z0=FRISO[2], z1=FRISO[3]), 'P_Faixa')
    if travessa:
        if len(cam) == 2: m = (cam[0][0] + cam[1][0])/2; t = cam[0][1]; lt = 0.40
        else: m, t = cam[len(cam)//2]; lt = 0.38
        p.varrer([(m - t*0.06, t), (m + t*0.06, t)], (-lt, lt, 0.0, 0.10), 'P_Metal', tampa=(True, True))

def cano_trecho(p, cam, flange_ini=True, flange_fim=True, z=CANO_Z):
    """Cano com flange nas pontas que encostam na borda. Perfil de junção = anel do cano + anel da flange."""
    (a, ta), (b, tb) = cam[0], cam[-1]
    meio = list(cam)
    if flange_ini: meio[0] = (a + ta*FLANGE_L, ta)
    if flange_fim: meio[-1] = (b - tb*FLANGE_L, tb)
    p.tubo(meio, CANO_R, 'P_Cobre', z=z)
    if flange_ini: p.tubo([(a, ta), (a + ta*FLANGE_L, ta)], FLANGE_R, 'P_Escuro', z=z, tampa=(True, True))
    if flange_fim: p.tubo([(b - tb*FLANGE_L, tb), (b, tb)], FLANGE_R, 'P_Escuro', z=z, tampa=(True, True))

def trilho_trecho(p, cam, seg_curva=None):
    """Lastro + 2 trilhos (perfil de junção) + dormentes a cada 0,25 m de arco (meio-passo nas pontas, para emendar)."""
    p.varrer(cam, LASTRO, 'P_RochaEscura')
    for s in (-1, 1):
        x = s*BITOLA/2
        p.varrer(cam, (x - 0.03, x + 0.03, TRILHO_FERRO_Z[0], TRILHO_FERRO_Z[1]), 'P_Metal')
    # dormentes: posições por comprimento de arco
    comp = [0.0]
    for i in range(1, len(cam)): comp.append(comp[-1] + (cam[i][0] - cam[i-1][0]).length)
    total = comp[-1]; n = round(total/DORMENTE_PASSO)
    for k in range(n):
        alvo = (k + 0.5)*total/n
        i = max(j for j in range(len(comp)) if comp[j] <= alvo) if alvo < total else len(comp) - 2
        i = min(i, len(cam) - 2); f = (alvo - comp[i])/max(comp[i+1] - comp[i], 1e-9)
        pt = cam[i][0].lerp(cam[i+1][0], f); t = cam[i][1].lerp(cam[i+1][1], f).normalized()
        p.varrer([(pt - t*0.05, t), (pt + t*0.05, t)], (-0.36, 0.36, 0.05, 0.08), 'P_Tronco', tampa=(True, True))

# ------------------------------------------------------------------ modelo
class Modelo:
    def __init__(self, nome, categoria, w=1, d=1, tipo='estrutura', orcamento=None, descricao=''):
        self.nome, self.categoria, self.w, self.d, self.tipo = nome, categoria, w, d, tipo
        self.orcamento = orcamento or (100 if tipo == 'item' else 1500)
        self.descricao = descricao
        self.partes = []; self.portas = []; self.erros = []; self.info = {}
        self.ocupa_canto = False  # só o pilar ocupa canto

    def parte(self, nome='corpo', pai=None, pivo=(0, 0, 0)):
        p = Parte(self, nome, pai, pivo); self.partes.append(p); return p

    def porta(self, tipo, io, lado, k=0, z=None, perfil=None):
        """Porta no meio da borda do k-ésimo tile do lado (S/N/L/O, contando da esquerda p/ quem olha de fora)."""
        hw, hd = self.w/2, self.d/2
        if lado in 'SN':
            x = -hw + 0.5 + k if lado == 'S' else hw - 0.5 - k
            pos, dirv = Vector((x, -hd if lado == 'S' else hd, 0)), Vector((0, -1 if lado == 'S' else 1, 0))
        else:
            y = hd - 0.5 - k if lado == 'L' else -hd + 0.5 + k
            pos, dirv = Vector((hw if lado == 'L' else -hw, y, 0)), Vector((1 if lado == 'L' else -1, 0, 0))
        if z is None: z = dict(ITEM=TOPO_LONA, FLUIDO=CANO_Z, TRILHO=TRILHO_FERRO_Z[1])[tipo]
        pos.z = z
        self.portas.append(dict(nome=f'PORTA_{tipo}_{io}_{lado}{k}', tipo=tipo, io=io, pos=pos, dir=dirv, perfil=perfil))

    # -------------------------------------------- construção dos objetos
    def montar(self):
        col = bpy.data.collections.new(self.nome); bpy.context.scene.collection.children.link(col)
        objs = {}
        for p in self.partes:
            bmesh.ops.remove_doubles(p.bm, verts=p.bm.verts, dist=1e-6)
            bmesh.ops.recalc_face_normals(p.bm, faces=p.bm.faces)
            usados = sorted({f.material_index for f in p.bm.faces})
            remap = {mi: i for i, mi in enumerate(usados)}
            for f in p.bm.faces: f.material_index = remap[f.material_index]
            bmesh.ops.translate(p.bm, verts=p.bm.verts, vec=-p.pivo)
            me = bpy.data.meshes.new(f'{self.nome}_{p.nome}'); p.bm.to_mesh(me); p.bm.free()
            for mi in usados: me.materials.append(material(NOMES[mi]))
            for poly in me.polygons: poly.use_smooth = False
            o = bpy.data.objects.new(f'{self.nome}' if p.nome == 'corpo' and len(self.partes) == 1 else f'{self.nome}_{p.nome}', me)
            col.objects.link(o); objs[p.nome] = (o, p)
        for nome, (o, p) in objs.items():
            if p.pai:
                po, pp = objs[p.pai]; o.parent = po; o.location = p.pivo - pp.pivo
            else:
                o.location = p.pivo
        raiz = objs[self.partes[0].nome][0]
        for pt in self.portas:
            e = bpy.data.objects.new(pt['nome'], None); e.empty_display_type = 'SINGLE_ARROW'; e.empty_display_size = 0.3
            ang = math.atan2(-pt['dir'].x, pt['dir'].y)
            e.location = pt['pos'] - self.partes[0].pivo; e.rotation_euler = (0, 0, ang); e.parent = raiz
            col.objects.link(e)
        self.col = col; self.objs = [o for o, _ in objs.values()]
        bpy.context.view_layer.update()
        return col

    # -------------------------------------------- verificação
    def verificar(self, refs=None):
        dg = bpy.context.evaluated_depsgraph_get()
        tris = 0; pts = []; mats = set()
        for o in self.objs:
            me = o.data; me.calc_loop_triangles(); tris += len(me.loop_triangles)
            pts += [o.matrix_world @ v.co for v in me.vertices]
            mats |= {m.name for m in me.materials}
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        self.info.update(tris=tris, dims=[round(hi.x-lo.x, 3), round(hi.y-lo.y, 3), round(hi.z-lo.z, 3)], materiais=sorted(mats))
        e = 1e-5
        if tris > self.orcamento: self.erros.append(f'triângulos {tris} > orçamento {self.orcamento}')
        if not mats <= set(NOMES): self.erros.append(f'materiais fora da paleta: {mats - set(NOMES)}')
        if self.tipo == 'canto':
            lim = getattr(self, 'topo_livre', 1e9)   # acima disso pode abrir (fica sob a esteira elevada)
            fora = sum(1 for p in pts if (abs(p.x) > CANTO+e or abs(p.y) > CANTO+e) and p.z < lim - e)
            if fora: self.erros.append(f'{fora} vértices do pilar fora da zona do canto ({CANTO} m)')
        elif self.tipo == 'segmento':   # peça de articulação (origem na junta); montada pelo jogo
            pass
        elif self.tipo == 'veiculo':   # trem/inimigo: sem grade; só orçamento e chão
            if lo.z < -e: self.erros.append(f'abaixo do chão: z {lo.z:.3f}')
        elif self.tipo == 'deco':   # enfeite sem grade (grama, seixos): cabe em meio tile em volta do centro
            if lo.x < -0.5-e or hi.x > 0.5+e or lo.y < -0.5-e or hi.y > 0.5+e: self.erros.append('deco maior que 1 tile')
        elif self.tipo == 'item':
            if lo.x < -0.13-e or hi.x > 0.13+e or lo.y < -0.13-e or hi.y > 0.13+e: self.erros.append(f'item mais largo que 0,26 m: {lo} {hi}')
            if abs(lo.z) > e or hi.z > 0.26+e: self.erros.append(f'item fora da altura 0..0,26: z {lo.z:.3f}..{hi.z:.3f}')
        else:
            if lo.x < -self.w/2-e or hi.x > self.w/2+e or lo.y < -self.d/2-e or hi.y > self.d/2+e:
                self.erros.append(f'sai da área {self.w}×{self.d}: x {lo.x:.3f}..{hi.x:.3f} y {lo.y:.3f}..{hi.y:.3f}')
            if lo.z < -e: self.erros.append(f'abaixo do chão: z {lo.z:.3f}')
            if not getattr(self, 'ocupa_canto', False):
                hw, hd = self.w/2, self.d/2; inv = 0
                for x0 in [-hw + i for i in range(self.w + 1)]:
                    for y0 in [-hd + j for j in range(self.d + 1)]:
                        inv += sum(1 for p in pts if abs(p.x - x0) < CANTO - e and abs(p.y - y0) < CANTO - e)
                if inv: self.erros.append(f'{inv} vértices invadem a zona livre dos cantos ({CANTO} m)')
        for pt in self.portas:
            pos, d = pt['pos'], pt['dir']
            borda = (abs(pos.x) == self.w/2) if d.x else (abs(pos.y) == self.d/2)
            lat = pos.y if d.x else pos.x; meia = (self.d if d.x else self.w)/2
            centro_tile = abs(((lat + meia) % 1) - 0.5) < e
            if not (borda and centro_tile): self.erros.append(f'{pt["nome"]} fora do meio da borda de um tile')
            if pt['perfil'] and refs is not None:
                ref = refs[pt['perfil']]; dz = round(pos.z - dict(esteira=TOPO_LONA, cano=CANO_Z, trilho=TRILHO_FERRO_Z[1])[pt['perfil']], 4)
                got = {(l, round(z - dz, 4)) for l, z in perfil_na_borda(self.objs, pos, d)}
                if got != ref: self.erros.append(f'{pt["nome"]}: perfil {pt["perfil"]} não casa (dif {sorted(got ^ ref)[:4]})')
        return not self.erros

    # -------------------------------------------- saída
    def pasta(self):
        p = os.path.join(RAIZ, self.categoria, self.nome); os.makedirs(p, exist_ok=True); return p

    def exportar(self):
        p = self.pasta()
        for o in bpy.context.view_layer.objects: o.select_set(False)
        for o in self.col.objects: o.select_set(True)
        bpy.context.view_layer.objects.active = self.objs[0]
        bpy.ops.export_scene.gltf(filepath=os.path.join(p, self.nome + '.glb'), use_selection=True, export_yup=True)
        for o in self.col.objects: o.select_set(False)
        bpy.data.libraries.write(os.path.join(p, self.nome + '.blend'), set(self.col.objects) | {self.col}, fake_user=True)
        dados = dict(nome=self.nome, categoria=self.categoria, tipo=self.tipo, area=[self.w, self.d], descricao=self.descricao,
                     ocupa_canto=bool(getattr(self, 'ocupa_canto', False)),
                     partes=[dict(nome=x.nome, pai=x.pai, pivo=[round(c, 4) for c in x.pivo]) for x in self.partes],
                     portas=[dict(nome=x['nome'], tipo=x['tipo'], io=x['io'], pos=[round(c, 4) for c in x['pos']],
                                  dir=[int(c) for c in x['dir']]) for x in self.portas], **self.info)
        with open(os.path.join(p, self.nome + '.json'), 'w', encoding='utf-8') as f: json.dump(dados, f, ensure_ascii=False, indent=1)
        return dados

    def esconder(self):
        self.col.hide_render = True; self.col.hide_viewport = True

def perfil_na_borda(objs, pos, d):
    """(|lateral|, z) dos vértices no plano da borda, até 0,5 m de lado da porta."""
    lat_v = Vector((-d.y, d.x, 0)); s = set()
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; r = w - Vector((pos.x, pos.y, 0))
            if abs(r.dot(d)) < 1e-5 and abs(r.dot(lat_v)) <= 0.5 + 1e-6:
                s.add((round(abs(r.dot(lat_v)), 4), round(w.z, 4)))
    return s

def referencias():
    """Perfis de referência tirados das peças retas (esteira e cano)."""
    m = Modelo('_ref_esteira', '_tmp'); esteira_trecho(m.parte(), reto((0, -0.5, 0), (0, 0.5, 0))); m.montar()
    n = Modelo('_ref_cano', '_tmp'); cano_trecho(n.parte(), reto((0, -0.5, 0), (0, 0.5, 0))); n.montar()
    t = Modelo('_ref_trilho', '_tmp'); trilho_trecho(t.parte(), reto((0, -0.5, 0), (0, 0.5, 0))); t.montar()
    refs = dict(esteira=perfil_na_borda(m.objs, Vector((0, 0.5, 0)), Vector((0, 1, 0))),
                cano=perfil_na_borda(n.objs, Vector((0, 0.5, 0)), Vector((0, 1, 0))),
                trilho=perfil_na_borda(t.objs, Vector((0, 0.5, 0)), Vector((0, 1, 0))))
    for x in (m, n, t): x.esconder()
    return refs

# ------------------------------------------------------------------ prévia (Workbench, rápido e sem GPU)
def preparar_cena():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
    sh.show_object_outline = True; sh.object_outline_color = (0.02, 0.02, 0.02); sh.show_cavity = True
    sc.render.film_transparent = False
    if not sc.world: sc.world = bpy.data.worlds.new('W')
    sc.world.color = (0.16, 0.17, 0.19)
    sc.render.resolution_percentage = 100
    cam = bpy.data.objects.new('CAM', bpy.data.cameras.new('CAM')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    return sc

def render(objs, arquivo, res=(640, 640), margem=1.25, direcao=(1, -1, 0.85)):
    sc = bpy.context.scene; cam = sc.camera
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi)/2; d = Vector(direcao).normalized()
    cam.location = c + d*20; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    # escala: projeta os cantos no plano da câmera
    M = cam.rotation_euler.to_matrix(); ex, ey = M.col[0], M.col[1]
    proj = [((p - c).dot(ex), (p - c).dot(ey)) for p in pts]
    larg = max(abs(a) for a, _ in proj)*2; alt = max(abs(b) for _, b in proj)*2
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.data.ortho_scale = max(larg, alt*res[0]/res[1])*margem
    vis = set(objs)
    escondidos = []
    for o in sc.objects:
        if o.type == 'MESH' and o not in vis and not o.hide_render: o.hide_render = True; escondidos.append(o)
    sc.render.filepath = arquivo; bpy.ops.render.render(write_still=True)
    for o in escondidos: o.hide_render = False

# ------------------------------------------------------------------ execução em lote
def rodar(construtores, relatorio):
    """Monta, verifica, exporta e gera prévia de cada modelo. Grava relatório JSON."""
    preparar_cena(); refs = referencias(); res = []
    for fn in construtores:
        m = fn(); m.montar(); ok = m.verificar(refs)
        dados = m.exportar(); dados['erros'] = m.erros
        render(m.objs, os.path.join(m.pasta(), m.nome + '_previa.png'), res=(480, 480))
        m.esconder(); res.append(dados)
        print(('OK   ' if ok else 'ERRO ') + m.nome, m.info.get('tris'), m.erros)
    with open(relatorio, 'w', encoding='utf-8') as f: json.dump(res, f, ensure_ascii=False, indent=1)
    return res
