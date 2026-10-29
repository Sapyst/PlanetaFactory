"""Auditoria de sobreposição: faces de peças diferentes no MESMO plano e de frente para o mesmo lado, cobrindo-se
(z-fighting: a superfície pisca/atravessa). Uso: blender -b --factory-startup --python auditar_sobreposicao.py [-- filtro]
Lê o .glb sem textura (backup) quando existe, senão o .glb. Imprime 'SOBREPOE nome área_total pares' por modelo."""
import bpy, bmesh, sys, os, glob, json, math
from mathutils import Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modelos'))
filtro = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ''


def area_poli(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def recorta(sujeito, recorte):
    """Sutherland–Hodgman (recorte convexo, sentido anti-horário)."""
    def dentro(p, a, b): return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9
    def inter(p, q, a, b):
        x1, y1 = p; x2, y2 = q; x3, y3 = a; x4, y4 = b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12: return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    saida = sujeito
    for i in range(len(recorte)):
        a, b = recorte[i], recorte[(i + 1) % len(recorte)]
        ent = saida; saida = []
        if not ent: break
        s = ent[-1]
        for e in ent:
            if dentro(e, a, b):
                if not dentro(s, a, b): saida.append(inter(s, e, a, b))
                saida.append(e)
            elif dentro(s, a, b):
                saida.append(inter(s, e, a, b))
            s = e
    return saida


def ccw(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return pts if a > 0 else list(reversed(pts))


def auditar(caminho):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=caminho)
    faces = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        for f in bm.faces:
            if f.calc_area() < 1e-5: continue
            n = f.normal.normalized()
            if n.z < -0.9 and max(v.co.z for v in f.verts) < 0.01:
                continue                                  # face de baixo encostada no chão: nunca aparece
            faces.append((n, n.dot(f.verts[0].co), [v.co.copy() for v in f.verts], o.name))
        bm.free()
    grupos = {}
    for i, (n, d, vs, on) in enumerate(faces):
        k = (round(n.x, 2), round(n.y, 2), round(n.z, 2), round(d, 3))
        grupos.setdefault(k, []).append(i)
    total = 0.0; pares = 0; exemplo = None
    for k, ids in grupos.items():
        if len(ids) < 2 or len(ids) > 400: continue
        n = Vector(k[:3]).normalized()
        u = n.orthogonal().normalized(); w = n.cross(u)
        proj = [ccw([(v.dot(u), v.dot(w)) for v in faces[i][2]]) for i in ids]
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                pa, pb = proj[a], proj[b]
                if max(p[0] for p in pa) < min(p[0] for p in pb) or max(p[0] for p in pb) < min(p[0] for p in pa): continue
                if max(p[1] for p in pa) < min(p[1] for p in pb) or max(p[1] for p in pb) < min(p[1] for p in pa): continue
                r = recorta(pa, pb)
                if len(r) >= 3:
                    ar = area_poli(r)
                    if ar > 2e-4:
                        total += ar; pares += 1
                        if exemplo is None: exemplo = (round(ar, 4), [round(c, 3) for c in faces[ids[a]][2][0]])
    return total, pares, exemplo


saida = []
for js in sorted(glob.glob(os.path.join(RAIZ, '**', '*.json'), recursive=True)):
    nome = os.path.splitext(os.path.basename(js))[0]
    if nome.startswith('_') or (filtro and filtro not in js): continue
    pasta = os.path.dirname(js)
    glb = os.path.join(pasta, nome + '_sem_textura.glb')
    if not os.path.exists(glb): glb = os.path.join(pasta, nome + '.glb')
    if not os.path.exists(glb): continue
    total, pares, ex = auditar(glb)
    if pares:
        print('SOBREPOE %-24s %.3f m² em %d pares  ex %s' % (nome, total, pares, ex))
        saida.append((nome, total, pares))
print('AUDITORIA %d modelos com sobreposição' % len(saida))
