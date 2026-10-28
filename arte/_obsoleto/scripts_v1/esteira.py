"""Esteira modular (1 tile = 1 m, origem no centro do tile, chão em z = 0).

Peças (fluxo entra pelo sul, −Y):
  EST_Reta      sai pelo norte (+Y)
  EST_Curva     vira à direita, sai pelo leste (+X)
  EST_CurvaEsq  vira à esquerda, sai pelo oeste (−X)
  EST_Inicio    cabeceira com motor no sul; sai pelo norte
  EST_Fim       para-choque no norte; entra pelo sul

Encaixe: toda junção fica exatamente no plano da borda (±0,5), perpendicular a ela, com o mesmo
perfil de 16 vértices (lona, 2 trilhos, 2 frisos). Pontas de junção são abertas (sem tampa).
A lona (P_Esteira) tem UV com V = distância percorrida, para o shader do Godot rolar no sentido do fluxo.
Uso: blender --background --python esteira.py
"""
import bpy, bmesh, math
from mathutils import Vector
col=bpy.data.collections.get('Esteira') or bpy.data.collections.new('Esteira')
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
def mat(n,c,e=0,r=0.7,m=0.0):
    x=bpy.data.materials.get(n) or bpy.data.materials.new(n); x.use_nodes=True
    b=x.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(*c,1); b.inputs['Roughness'].default_value=r; b.inputs['Metallic'].default_value=m
    b.inputs['Emission Strength'].default_value=e
    if e: b.inputs['Emission Color'].default_value=(*c,1)
    x.diffuse_color=(*c,1); return x
M={'esteira':mat('P_Esteira',(0.05,0.05,0.06),r=0.9),'escuro':mat('P_Escuro',(0.10,0.11,0.14)),'faixa':mat('P_Faixa',(0.95,0.75,0.15)),
   'metal':mat('P_Metal',(0.42,0.46,0.52),r=0.5,m=0.3),'cobre':mat('P_Cobre',(0.78,0.42,0.20),r=0.4,m=0.5)}
ORD=list(M); E=ORD.index

# ---- medidas da esteira (m). Toda junção é no plano da borda do tile (±0,5) e perpendicular a ele.
LONA=(-0.40,0.40,0.10,0.16)          # lateral0, lateral1, z0, z1
TRILHO=(0.40,0.48,0.04,0.20)
FRISO=(0.40,0.48,0.20,0.225)
SEG_CURVA=8

def Q(v): return Vector((round(v.x,6),round(v.y,6),round(v.z,6)))
# caminhos = lista de (ponto, tangente exata)
def caminho_reto(y0=-0.5,y1=0.5):
    return [(Vector((0,y0,0)),Vector((0,1,0))),(Vector((0,y1,0)),Vector((0,1,0)))]
def caminho_curva(seg=SEG_CURVA):      # entra pelo sul, vira à direita, sai pelo leste
    c=Vector((0.5,-0.5,0)); out=[]
    for i in range(seg+1):
        a=math.pi-(math.pi/2)*i/seg
        out.append((c+0.5*Vector((math.cos(a),math.sin(a),0)),Vector((math.sin(a),-math.cos(a),0))))
    return out
def caminho_curva_esq(seg=SEG_CURVA):  # entra pelo sul, vira à esquerda, sai pelo oeste
    c=Vector((-0.5,-0.5,0)); out=[]
    for i in range(seg+1):
        a=(math.pi/2)*i/seg
        out.append((c+0.5*Vector((math.cos(a),math.sin(a),0)),Vector((-math.sin(a),math.cos(a),0))))
    return out

def varrer(bm,uvl,cam,perfil,mi,uv=False,tampa=(False,False)):
    """Varre o retângulo `perfil` ao longo de `cam`. Pontas abertas (encaixe) salvo `tampa`."""
    lat0,lat1,z0,z1=perfil; aneis=[]; dist=[0.0]
    for i,(p,t) in enumerate(cam):
        n=Vector((-t.y,t.x,0)).normalized()
        if i: dist.append(dist[-1]+(p-cam[i-1][0]).length)
        aneis.append([bm.verts.new(Q(p+n*l+Vector((0,0,z)))) for l,z in ((lat0,z0),(lat1,z0),(lat1,z1),(lat0,z1))])
    for i in range(len(aneis)-1):
        a,b=aneis[i],aneis[i+1]
        for k in range(4):
            f=bm.faces.new((a[k],a[(k+1)%4],b[(k+1)%4],b[k])); f.material_index=mi
            if uv:
                for lp in f.loops:
                    j=0 if lp.vert in a else 1; idx=(a,b)[j].index(lp.vert)
                    lp[uvl].uv=(0.0 if idx in (0,3) else 1.0, dist[i+j])
    for ring,fecha,rev in ((aneis[0],tampa[0],True),(aneis[-1],tampa[1],False)):
        if fecha: bm.faces.new(list(reversed(ring)) if rev else ring).material_index=mi

def caixa(bm,x0,x1,y0,y1,z0,z1,mi):
    vs=[bm.verts.new(Q(Vector(c))) for c in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
        bm.faces.new([vs[i] for i in f]).material_index=mi

def rolo(bm,y,z,r,mi,lados=8,meia=0.40):  # cilindro no eixo X
    m=__import__('mathutils').Matrix
    res=bmesh.ops.create_cone(bm,cap_ends=True,segments=lados,radius1=r,radius2=r,depth=2*meia,
        matrix=m.Translation((0,y,z))@m.Rotation(math.pi/2,4,'Y'))
    for f in {f for v in res['verts'] for f in v.link_faces}: f.material_index=mi

def esteira_base(bm,uvl,cam,tampa=(False,False)):
    varrer(bm,uvl,cam,LONA,E('esteira'),uv=True,tampa=tampa)
    for s in (-1,1):
        tr=(s*TRILHO[0],s*TRILHO[1],TRILHO[2],TRILHO[3]); fr=(s*FRISO[0],s*FRISO[1],FRISO[2],FRISO[3])
        varrer(bm,uvl,cam,tr,E('escuro'),tampa=tampa); varrer(bm,uvl,cam,fr,E('faixa'),tampa=tampa)
    if len(cam)==2: p,t=(cam[0][0]+cam[1][0])/2,cam[0][1]; lt=0.44     # travessa no meio do comprimento
    else: p,t=cam[len(cam)//2]; lt=0.40                                    # na curva, só sob a lona
    varrer(bm,uvl,[(p-t*0.06,t),(p+t*0.06,t)],(-lt,lt,0.0,0.10),E('metal'),tampa=(True,True))

def peca(nome,construir,loc=(0,0,0)):
    old=bpy.data.objects.get(nome)
    if old: bpy.data.objects.remove(old)
    me=bpy.data.meshes.new(nome); bm=bmesh.new(); uvl=bm.loops.layers.uv.new('UVMap')
    construir(bm,uvl)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
    bm.normal_update(); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    for k in ORD: me.materials.append(M[k])
    o=bpy.data.objects.new(nome,me); col.objects.link(o); o.location=loc; return o

def b_reta(bm,uvl): esteira_base(bm,uvl,caminho_reto())
def b_curva(bm,uvl): esteira_base(bm,uvl,caminho_curva())
def b_curva_esq(bm,uvl): esteira_base(bm,uvl,caminho_curva_esq())
def b_inicio(bm,uvl):
    # cabeceira do motor no lado sul; lona começa no rolo
    esteira_base(bm,uvl,caminho_reto(-0.36,0.5),tampa=(True,False))
    caixa(bm,-0.48,0.48,-0.5,-0.36,0.0,0.26,E('escuro'))
    caixa(bm,-0.48,0.48,-0.5,-0.36,0.26,0.285,E('faixa'))
    caixa(bm,0.18,0.42,-0.48,-0.38,0.285,0.38,E('cobre'))  # motor em cima da cabeceira (tudo dentro do tile)
    rolo(bm,-0.36,0.13,0.035,E('metal'))
def b_fim(bm,uvl):
    # para-choque no lado norte; lona termina no rolo
    esteira_base(bm,uvl,caminho_reto(-0.5,0.38),tampa=(False,True))
    caixa(bm,-0.48,0.48,0.38,0.5,0.0,0.24,E('escuro'))
    caixa(bm,-0.44,0.44,0.36,0.38,0.16,0.24,E('faixa'))
    rolo(bm,0.38,0.13,0.035,E('metal'))

for o in list(col.objects): bpy.data.objects.remove(o)
for i,(n,b) in enumerate((('EST_Reta',b_reta),('EST_Curva',b_curva),('EST_CurvaEsq',b_curva_esq),('EST_Inicio',b_inicio),('EST_Fim',b_fim))):
    peca(n,b,(4+2*i,0,0))
