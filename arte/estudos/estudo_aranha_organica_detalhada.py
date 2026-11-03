"""Estudo Anatômico e Estrutural Avançado: Aranha Orgânica (Cycles Multi-thread)
Versão 7 - Perfeição Anatômica e Estética (Quitina Ébano Real, Sem Vãos, Macro Preciso):
1. Rosto Aracnídeo Realista:
   - Quitina ébano negra profunda e aveludada (sem aspecto caramelo/plástico).
   - 8 olhos de ônix negro vidrado com córneas reflexivas nítidas e cílios orbitais.
   - Quelíceras maciças orgânicas contínuas afuniladas com sulcos musculares.
   - Presas em foice vermelhas com gotas de veneno translúcidas.
   - Maxilas com escópula oral densa de filtragem cor de ferrugem.
2. Articulação do Joelho Perfeita:
   - Fêmur esclerotizado chanfrado encaixado na tíbia.
   - Dois côndilos esféricos laterais de pivô articular.
   - Membrana artrodial contínua sanfonada conectando as bordas sem buracos.
   - Macro-espinhos negros e afiados saindo de alvéolos circulares.
3. Garra Tarsal Pectinada & Escópula:
   - Enquadramento macro superior apoiado sobre ardósia negra.
   - Duas garras curvas pectinadas com fileira de dentes em pente.
   - Tufo denso em leque de escópula adesiva cor de cobre.
4. Organismo Completo em Postura Predatória Viva:
   - Prossoma com carapaça esculpida e esterno ventral plano.
   - As 8 pernas nascem 100% do esterno ventral do cefalotórax, com juntas articuladas contínuas e côndilos esféricos selando as conexões (zero vãos).
   - Abdômen em gota com fiandeiras traseiras e pedicelo anatômico.
"""
import bpy, bmesh, os, math
from mathutils import Vector, Matrix, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))

def init_cycles():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - High Contrast'
    sc.view_settings.exposure = -0.30 # Controla a superexposição para manter pretos profundos
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 1200
    sc.render.film_transparent = False

    mundo = bpy.data.worlds.new('Mundo')
    sc.world = mundo
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.008, 0.010, 0.014, 1.0)
    bg.inputs['Strength'].default_value = 0.30
    return sc

def no(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n

# =========================================================================
# MATERIAIS BIOLÓGICOS REALISTAS
# =========================================================================

def mat_quitina_ebano(nome='QuitinaEbano'):
    """Quitina de aracnídeo predador real: preto-ébano lustroso com penugem aveludada e cera sedosa."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    coord = no(nt, 'ShaderNodeTexCoord')
    noise = no(nt, 'ShaderNodeTexNoise', **{'Scale': 45.0, 'Detail': 4.0, 'Roughness': 0.60})
    nt.links.new(coord.outputs['Object'], noise.inputs['Vector'])
    
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.04, 'Distance': 0.01})
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Preto ébano sólido verdadeiro com leve modulação
    ramp = no(nt, 'ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.10
    ramp.color_ramp.elements[0].color = (0.002, 0.0015, 0.0015, 1.0) # Preto carvão absoluto
    ramp.color_ramp.elements[1].position = 0.90
    ramp.color_ramp.elements[1].color = (0.010, 0.006, 0.004, 1.0) # Mogno escuro profundo
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    bsdf.inputs['Roughness'].default_value = 0.22
    bsdf.inputs['Subsurface Weight'].default_value = 0.03 # Mínimo para não embranquecer
    bsdf.inputs['Subsurface Radius'].default_value = (0.2, 0.05, 0.02)
    bsdf.inputs['Coat Weight'].default_value = 0.70
    bsdf.inputs['Coat Roughness'].default_value = 0.05 # Cera biológica sedosa
    bsdf.inputs['Sheen Weight'].default_value = 0.95
    bsdf.inputs['Sheen Tint'].default_value = (0.6, 0.3, 0.15, 1.0) # Penugem aveludada quente nas bordas
    return m

def mat_olho_onix(nome='OlhoOnix'):
    """Lente corneal de ônix puro: espelho negro vítreo com catchlights nítidos."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (0.0002, 0.0002, 0.0004, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.001
    bsdf.inputs['Specular IOR Level'].default_value = 1.0
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.0005
    return m

def mat_presa_gradiente(nome='PresaGrad'):
    """Presa falciforme: base de esmalte negro e ponta vermelho-rubi/âmbar translúcida afiada."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    coord = no(nt, 'ShaderNodeTexCoord')
    sep = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(coord.outputs['Object'], sep.inputs['Vector'])
    
    ramp = no(nt, 'ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (0.28, 0.025, 0.006, 1.0) # Rubi translúcido
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (0.002, 0.001, 0.001, 1.0) # Base escura
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['Subsurface Weight'].default_value = 0.35
    bsdf.inputs['Subsurface Radius'].default_value = (0.6, 0.15, 0.04)
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.003
    return m

def mat_membrana_flexivel(nome='MembranaFlexivel'):
    """Membrana articular: tecido conjuntivo elástico leitoso-âmbar úmido nas dobras."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    coord = no(nt, 'ShaderNodeTexCoord')
    noise = no(nt, 'ShaderNodeTexNoise', **{'Scale': 35.0, 'Detail': 4.0})
    nt.links.new(coord.outputs['Object'], noise.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.08})
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    bsdf.inputs['Base Color'].default_value = (0.06, 0.038, 0.024, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.28
    bsdf.inputs['Subsurface Weight'].default_value = 0.55
    bsdf.inputs['Subsurface Radius'].default_value = (0.6, 0.3, 0.12)
    bsdf.inputs['Coat Weight'].default_value = 0.80
    bsdf.inputs['Coat Roughness'].default_value = 0.04
    return m

def mat_escopula_cobre(nome='EscopulaCobre'):
    """Cerdas táteis e tufos adesivos: cor de cobre/ferrugem aveludado."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (0.32, 0.08, 0.018, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.35
    bsdf.inputs['Sheen Weight'].default_value = 1.0
    bsdf.inputs['Sheen Tint'].default_value = (1.0, 0.45, 0.15, 1.0)
    bsdf.inputs['Coat Weight'].default_value = 0.50
    return m

def mat_veneno_gota(nome='VenenoViscoso'):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (0.85, 1.0, 0.80, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.005
    bsdf.inputs['Transmission Weight'].default_value = 0.98
    bsdf.inputs['IOR'].default_value = 1.35
    bsdf.inputs['Coat Weight'].default_value = 1.0
    return m

def mat_pedestal(nome='SoloArdosia'):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    coord = no(nt, 'ShaderNodeTexCoord')
    noise = no(nt, 'ShaderNodeTexNoise', **{'Scale': 15.0, 'Detail': 5.0})
    nt.links.new(coord.outputs['Object'], noise.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.10})
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    bsdf.inputs['Base Color'].default_value = (0.012, 0.014, 0.018, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.32
    bsdf.inputs['Coat Weight'].default_value = 0.55
    return m

def criar_mats():
    return [
        mat_quitina_ebano('QuitinaEbano'),         # idx 0
        mat_olho_onix('OlhoOnix'),                 # idx 1
        mat_presa_gradiente('PresaGrad'),          # idx 2
        mat_membrana_flexivel('MembranaFlexivel'), # idx 3
        mat_escopula_cobre('EscopulaCobre'),       # idx 4
        mat_veneno_gota('VenenoViscoso'),          # idx 5
    ]

# =========================================================================
# MODELAGEM ANATÔMICA BMESH
# =========================================================================

def construir_rosto_realista(bm, offset=Vector((0,0,0)), escala=1.0,
                             idx_quitina=0, idx_olho=1, idx_presa=2, idx_membrana=3, idx_escopula=4, idx_veneno=5):
    # 1. CARAPAÇA CEFÁLICA
    n_seg = 32
    passos_cara = 16
    aneis_cara = []
    for s in range(passos_cara + 1):
        t = s / passos_cara
        y = (-0.32 + t * 0.74) * escala
        rx = 0.36 * math.sin(t * math.pi * 0.88 + 0.15) * escala
        rz = 0.25 * math.sin(t * math.pi * 0.85 + 0.16) * escala
        fovea_dip = 0.038 * math.exp(-((t - 0.60) / 0.12)**2) * escala
        anel = []
        for i in range(n_seg):
            ang = i * 2 * math.pi / n_seg
            cos_a = math.cos(ang); sin_a = math.sin(ang)
            px = cos_a * rx * 1.15
            pz = sin_a * rz - fovea_dip * max(0, sin_a)
            if y < -0.16 * escala and sin_a < 0:
                pz -= abs(y + 0.16 * escala) * 0.40
            anel.append(bm.verts.new(offset + Vector((px, y, pz))))
        aneis_cara.append(anel)
        
    v_frente = bm.verts.new(offset + Vector((0, -0.34 * escala, -0.06 * escala)))
    for i in range(n_seg):
        f = bm.faces.new([aneis_cara[0][(i+1)%n_seg], aneis_cara[0][i], v_frente])
        f.material_index = idx_quitina; f.smooth = True
    for s in range(passos_cara):
        for i in range(n_seg):
            f = bm.faces.new([aneis_cara[s][i], aneis_cara[s][(i+1)%n_seg],
                              aneis_cara[s+1][(i+1)%n_seg], aneis_cara[s+1][i]])
            f.material_index = idx_quitina; f.smooth = True
    v_tras = bm.verts.new(offset + Vector((0, 0.44 * escala, 0.02 * escala)))
    for i in range(n_seg):
        f = bm.faces.new([aneis_cara[-1][i], aneis_cara[-1][(i+1)%n_seg], v_tras])
        f.material_index = idx_quitina; f.smooth = True

    # 2. 8 OLHOS DE ÔNIX VIDRADO
    olhos_data = [
        (-0.056, -0.27, 0.065, 0.038, Vector((-0.15, -0.95, 0.22))), # AME Esquerdo (Grande)
        ( 0.056, -0.27, 0.065, 0.038, Vector(( 0.15, -0.95, 0.22))), # AME Direito (Grande)
        (-0.135, -0.25, 0.048, 0.026, Vector((-0.55, -0.78, 0.18))), # ALE Esquerdo
        ( 0.135, -0.25, 0.048, 0.026, Vector(( 0.55, -0.78, 0.18))), # ALE Direito
        (-0.048, -0.21, 0.125, 0.028, Vector((-0.15, -0.60, 0.75))), # PME Esquerdo
        ( 0.048, -0.21, 0.125, 0.028, Vector(( 0.15, -0.60, 0.75))), # PME Direito
        (-0.128, -0.19, 0.110, 0.024, Vector((-0.65, -0.48, 0.55))), # PLE Esquerdo
        ( 0.128, -0.19, 0.110, 0.024, Vector(( 0.65, -0.48, 0.55))), # PLE Direito
    ]
    for ox, oy, oz, r_olho, d_dir in olhos_data:
        p_olho = offset + Vector((ox, oy, oz)) * escala
        d_norm = d_dir.normalized()
        q_olho = d_norm.to_track_quat('Z', 'Y')
        orbita = bmesh.ops.create_cone(bm, segments=16, cap_ends=True, radius1=r_olho * 1.25 * escala, radius2=r_olho * 1.08 * escala, depth=0.016 * escala,
                                       matrix=Matrix.Translation(p_olho) @ q_olho.to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in orbita['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
        lente = bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=14, radius=r_olho * escala)
        for v in lente['verts']:
            v.co += p_olho + d_norm * (r_olho * 0.42 * escala)
        for f in bm.faces:
            if any(v in lente['verts'] for v in f.verts): f.material_index = idx_olho; f.smooth = True
        for c_i in range(6):
            c_ang = c_i * (2 * math.pi / 6)
            p_cerda = p_olho + (q_olho @ Vector((math.cos(c_ang) * r_olho * 1.22 * escala, math.sin(c_ang) * r_olho * 1.22 * escala, 0)))
            d_cerda = (q_olho @ Vector((math.cos(c_ang) * 0.4, math.sin(c_ang) * 0.4, 0.85))).normalized()
            c_cone = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.0022*escala, radius2=0.0004, depth=0.038*escala,
                                           matrix=Matrix.Translation(p_cerda + d_cerda * 0.016 * escala) @ d_cerda.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in c_cone['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True

    # 3. QUELÍCERAS ORGÂNICAS INTEIRIÇAS
    for lado in (-1, 1):
        cx = lado * 0.082 * escala
        p_topo_q = offset + Vector((cx, -0.28 * escala, -0.01 * escala))
        passos_q = 16
        aneis_q = []
        compr_q = 0.36 * escala
        for step in range(passos_q + 1):
            t = step / passos_q
            z_q = p_topo_q.z - t * compr_q
            y_q = p_topo_q.y - math.sin(t * math.pi * 0.7) * 0.05 * escala
            x_q = p_topo_q.x + lado * math.sin(t * math.pi * 0.5) * 0.012 * escala
            if t < 0.20:
                f_topo = math.sin((t / 0.20) * (math.pi / 2))
                r_q = 0.082 * escala * (0.4 + 0.6 * f_topo)
            else:
                t_corpo = (t - 0.20) / 0.80
                r_q = 0.082 * escala * (1.0 - t_corpo * 0.42)
            anel = []
            for i in range(18):
                ang = i * 2 * math.pi / 18
                cos_a = math.cos(ang); sin_a = math.sin(ang)
                rx_q = r_q * (0.82 if (cos_a * lado) < 0 else 1.18)
                ry_q = r_q * (1.25 if sin_a < 0 else 0.80)
                sulco = math.sin(ang * 4) * 0.003 * escala
                px = x_q + cos_a * (rx_q + sulco)
                py = y_q + sin_a * (ry_q + sulco)
                anel.append(bm.verts.new(Vector((px, py, z_q))))
            aneis_q.append(anel)
            
        v_cupula_q = bm.verts.new(p_topo_q + Vector((0, 0, 0.03 * escala)))
        for i in range(18):
            f = bm.faces.new([aneis_q[0][i], aneis_q[0][(i+1)%18], v_cupula_q])
            f.material_index = idx_quitina; f.smooth = True
        for s in range(passos_q):
            for i in range(18):
                f = bm.faces.new([aneis_q[s][i], aneis_q[s][(i+1)%18],
                                  aneis_q[s+1][(i+1)%18], aneis_q[s+1][i]])
                f.material_index = idx_quitina; f.smooth = True
        v_alv_q = bm.verts.new(Vector((x_q, y_q, z_q - 0.015 * escala)))
        for i in range(18):
            f = bm.faces.new([aneis_q[-1][(i+1)%18], aneis_q[-1][i], v_alv_q])
            f.material_index = idx_quitina; f.smooth = True
            
        # Cerdas táteis
        for r_i in range(6):
            z_cerda = p_topo_q.z - (0.08 + r_i * 0.045) * escala
            for c_i in range(3):
                ang_c = math.radians(-65 + c_i * 22) if lado < 0 else math.radians(-115 - c_i * 22)
                p_c = Vector((cx + math.cos(ang_c) * 0.075 * escala, -0.33 * escala - math.sin(r_i * 0.25) * 0.02 * escala, z_cerda))
                d_c = Vector((lado * 0.15, -0.85, -0.50)).normalized()
                cerda = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.0028*escala, radius2=0.0005, depth=0.065*escala,
                                              matrix=Matrix.Translation(p_c) @ d_c.to_track_quat('Z', 'Y').to_matrix().to_4x4())
                for f in bm.faces:
                    if any(v in cerda['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True

        # 4. SULCO QUELICERAL COM DENTES
        p_sulco = Vector((cx - lado * 0.022 * escala, -0.30 * escala, z_q + 0.04 * escala))
        for d_i in range(4):
            p_dente = p_sulco + Vector((-lado * 0.011 * d_i, -0.028, -0.012 - d_i * 0.022)) * escala
            d_dente = Vector((-lado * 0.7, -0.3, -0.6)).normalized()
            dente_obj = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, radius1=0.008*escala, radius2=0.001, depth=0.028*escala,
                                              matrix=Matrix.Translation(p_dente) @ d_dente.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in dente_obj['verts'] for v in f.verts): f.material_index = idx_presa; f.smooth = True
        for d_i in range(4):
            p_dente = p_sulco + Vector((-lado * 0.009 * d_i, 0.024, -0.008 - d_i * 0.020)) * escala
            d_dente = Vector((-lado * 0.7, 0.3, -0.6)).normalized()
            dente_obj = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, radius1=0.006*escala, radius2=0.0008, depth=0.022*escala,
                                              matrix=Matrix.Translation(p_dente) @ d_dente.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in dente_obj['verts'] for v in f.verts): f.material_index = idx_presa; f.smooth = True

        # 5. PRESAS FALCIFORMES CURVAS COM VENENO
        p_art_presa = Vector((cx + lado * 0.038 * escala, -0.31 * escala, z_q + 0.02 * escala))
        passos_f = 16
        r_f_base = 0.028 * escala
        aneis_fang = []
        for i_f in range(passos_f + 1):
            t_f = i_f / passos_f
            ang_curva = t_f * math.radians(95)
            px = p_art_presa.x - lado * (math.sin(ang_curva) * 0.130 * escala)
            py = p_art_presa.y - (math.cos(ang_curva) * 0.048 - 0.048) * escala
            pz = p_art_presa.z - ((1.0 - math.cos(ang_curva)) * 0.115 + t_f * 0.05) * escala
            r_cur_f = r_f_base * (1.0 - t_f * 0.94)
            anel = []
            for a_i in range(10):
                rad = a_i * 2 * math.pi / 10
                fx = math.cos(rad) * r_cur_f; fy = math.sin(rad) * r_cur_f * 0.85
                anel.append(bm.verts.new(Vector((px + fx, py + fy, pz))))
            aneis_fang.append(anel)
            
        v_base_fang = bm.verts.new(p_art_presa + Vector((0, 0, 0.015 * escala)))
        for a_i in range(10):
            f = bm.faces.new([aneis_fang[0][(a_i+1)%10], aneis_fang[0][a_i], v_base_fang])
            f.material_index = idx_presa; f.smooth = True
        for s in range(passos_f):
            for a_i in range(10):
                f = bm.faces.new([aneis_fang[s][a_i], aneis_fang[s][(a_i+1)%10],
                                  aneis_fang[s+1][(a_i+1)%10], aneis_fang[s+1][a_i]])
                f.material_index = idx_presa; f.smooth = True
        v_ponta_fang = bm.verts.new(Vector((px, py, pz - 0.010 * escala)))
        for a_i in range(10):
            f = bm.faces.new([aneis_fang[-1][a_i], aneis_fang[-1][(a_i+1)%10], v_ponta_fang])
            f.material_index = idx_presa; f.smooth = True
            
        p_gota = v_ponta_fang.co + Vector((0, 0, -0.008 * escala))
        gota = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=0.012 * escala)
        for gv in gota['verts']:
            gv.co.z *= 1.5; gv.co += p_gota
        for f in bm.faces:
            if any(v in gota['verts'] for v in f.verts): f.material_index = idx_veneno; f.smooth = True

    # 6. MAXILAS COM ESCÓPULA ORAL
    for lado in (-1, 1):
        p_maxila = offset + Vector((lado * 0.052, -0.25, -0.27)) * escala
        max_base = bmesh.ops.create_cone(bm, segments=12, cap_ends=True, radius1=0.045*escala, radius2=0.035*escala, depth=0.08*escala,
                                         matrix=Matrix.Translation(p_maxila) @ Matrix.Rotation(math.radians(-lado * 20), 4, 'Y'))
        for f in bm.faces:
            if any(v in max_base['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
        for sc_i in range(32):
            ang_sc = sc_i * (2 * math.pi / 32)
            r_sc = 0.026 * escala * (0.5 + 0.5 * math.sin(sc_i * 0.4))
            p_pelo = p_maxila + Vector((math.cos(ang_sc) * r_sc - lado * 0.01 * escala,
                                        -0.036 * escala + math.sin(ang_sc) * r_sc * 0.4,
                                        -0.02 * escala - (sc_i % 4) * 0.008 * escala))
            d_pelo = Vector((-lado * 0.4, -0.7, -0.6)).normalized()
            pelo_sc = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.0025*escala, radius2=0.0004, depth=0.055*escala,
                                            matrix=Matrix.Translation(p_pelo) @ d_pelo.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in pelo_sc['verts'] for v in f.verts): f.material_index = idx_escopula; f.smooth = True

    # 7. PEDIPALPOS ARTICULADOS
    for lado in (-1, 1):
        p_pal_coxa = offset + Vector((lado * 0.22, -0.24, -0.06)) * escala
        pal_articulos = [
            (Vector((0, 0, 0)), 0.046 * escala),
            (Vector((lado * 0.05, -0.12, -0.05)) * escala, 0.040 * escala),
            (Vector((lado * 0.08, -0.28,  0.02)) * escala, 0.036 * escala),
            (Vector((lado * 0.04, -0.42, -0.06)) * escala, 0.032 * escala),
            (Vector((lado * 0.01, -0.52, -0.14)) * escala, 0.028 * escala),
        ]
        for ip in range(len(pal_articulos) - 1):
            pt_a = p_pal_coxa + pal_articulos[ip][0]
            pt_b = p_pal_coxa + pal_articulos[ip+1][0]
            d_pal = (pt_b - pt_a).normalized()
            compr = (pt_b - pt_a).length
            seg_p = bmesh.ops.create_cone(bm, segments=12, cap_ends=True, radius1=pal_articulos[ip][1], radius2=pal_articulos[ip+1][1],
                                          depth=compr, matrix=Matrix.Translation((pt_a + pt_b)*0.5) @ d_pal.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in seg_p['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
            for c_i in range(3):
                p_c_pal = pt_a.lerp(pt_b, 0.25 + c_i * 0.3) + Vector((lado * 0.028 * escala, -0.01 * escala, 0))
                d_c_pal = Vector((lado * 0.6, -0.4, -0.4)).normalized()
                c_pal = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.003*escala, radius2=0.0005, depth=0.045*escala,
                                              matrix=Matrix.Translation(p_c_pal) @ d_c_pal.to_track_quat('Z', 'Y').to_matrix().to_4x4())
                for f in bm.faces:
                    if any(v in c_pal['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True

def construir_articulacao_macro(bm, p_centro=Vector((0,0,0)), escala=1.0,
                                idx_quitina=0, idx_membrana=3, idx_espinho=0):
    """Constrói uma articulação do joelho contínua de alta fidelidade:
    - Fêmur esclerotizado com colar chanfrado rígido.
    - Dois côndilos esféricos de rotação nas laterais.
    - Membrana artrodial contínua sanfonada unindo as bordas sem buracos.
    - Ligamentos tensores laterais.
    - Alvéolos circulares elevados com macro-espinhos táteis negros.
    """
    n_seg = 24
    compr_femur = 0.45 * escala
    r_femur_topo = 0.095 * escala
    r_femur_base = 0.088 * escala
    
    passos_f = 10
    aneis_femur = []
    for step in range(passos_f + 1):
        t = step / passos_f
        z = compr_femur * (1.0 - t)
        r = r_femur_topo * (1.0 - t) + r_femur_base * t
        anel = []
        for i in range(n_seg):
            ang = i * 2 * math.pi / n_seg
            x = math.cos(ang) * r * 1.08
            y = math.sin(ang) * r * 0.94
            if step == passos_f:
                z_offset = abs(y) * 0.35 if y < 0 else -y * 0.15
                anel.append(bm.verts.new(p_centro + Vector((x, y, z + z_offset))))
            else:
                anel.append(bm.verts.new(p_centro + Vector((x, y, z))))
        aneis_femur.append(anel)
        
    v_topo = bm.verts.new(p_centro + Vector((0, 0, compr_femur)))
    for i in range(n_seg):
        f = bm.faces.new([aneis_femur[0][i], aneis_femur[0][(i+1)%n_seg], v_topo])
        f.material_index = idx_quitina; f.smooth = True
    for s in range(passos_f):
        for i in range(n_seg):
            f = bm.faces.new([aneis_femur[s][i], aneis_femur[s][(i+1)%n_seg],
                              aneis_femur[s+1][(i+1)%n_seg], aneis_femur[s+1][i]])
            f.material_index = idx_quitina; f.smooth = True
            
    anel_colar_distal = aneis_femur[-1]
    for lado in (-1, 1):
        p_cond = p_centro + Vector((lado * r_femur_base * 1.08, 0, 0.015 * escala))
        cond = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=0.022 * escala)
        for v in cond['verts']: v.co += p_cond
        for f in bm.faces:
            if any(v in cond['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
        p_lig_a = p_cond + Vector((0, -0.01, 0.01)) * escala
        p_lig_b = p_centro + Vector((lado * r_femur_base * 0.98, -0.04 * escala, -0.05 * escala))
        d_lig = (p_lig_b - p_lig_a).normalized()
        lig = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, radius1=0.009*escala, radius2=0.007*escala,
                                    depth=(p_lig_b - p_lig_a).length,
                                    matrix=Matrix.Translation((p_lig_a + p_lig_b)*0.5) @ d_lig.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in lig['verts'] for v in f.verts): f.material_index = idx_membrana; f.smooth = True

    # Segmento Distal (Tíbia flexionada a 48 graus)
    ang_flex = math.radians(48)
    R_flex = Matrix.Rotation(ang_flex, 4, 'X')
    eixo_tibia = (R_flex @ Vector((0, 0, -1))).normalized()
    compr_tibia = 0.50 * escala
    r_tibia_topo = 0.082 * escala
    r_tibia_base = 0.065 * escala
    passos_t = 12
    aneis_tibia = []
    p_origem_tibia = p_centro + (R_flex @ Vector((0, 0, -0.07 * escala)))
    
    for step in range(passos_t + 1):
        t = step / passos_t
        dist_t = compr_tibia * t
        r_t = r_tibia_topo * (1.0 - t) + r_tibia_base * t
        p_centro_anel = p_origem_tibia + eixo_tibia * dist_t
        anel = []
        for i in range(n_seg):
            ang = i * 2 * math.pi / n_seg
            vx = Vector((1, 0, 0)) * math.cos(ang) * r_t * 1.05
            vy = (R_flex @ Vector((0, 1, 0))) * math.sin(ang) * r_t * 0.92
            anel.append(bm.verts.new(p_centro_anel + vx + vy))
        aneis_tibia.append(anel)
        
    for s in range(passos_t):
        for i in range(n_seg):
            f = bm.faces.new([aneis_tibia[s][i], aneis_tibia[s][(i+1)%n_seg],
                              aneis_tibia[s+1][(i+1)%n_seg], aneis_tibia[s+1][i]])
            f.material_index = idx_quitina; f.smooth = True
    v_fim_tibia = bm.verts.new(p_origem_tibia + eixo_tibia * compr_tibia)
    for i in range(n_seg):
        f = bm.faces.new([aneis_tibia[-1][(i+1)%n_seg], aneis_tibia[-1][i], v_fim_tibia])
        f.material_index = idx_quitina; f.smooth = True

    # Membrana Artrodial Contínua Sanfonada
    passos_m = 6
    aneis_membrana = [anel_colar_distal]
    for s_m in range(1, passos_m):
        t = s_m / passos_m
        anel_m = []
        onda = math.sin(s_m * math.pi) * 0.012 * escala
        for i in range(n_seg):
            v_fem = anel_colar_distal[i].co
            v_tib = aneis_tibia[0][i].co
            pos_interp = v_fem.lerp(v_tib, t)
            ang = i * 2 * math.pi / n_seg
            sin_a = math.sin(ang)
            if sin_a < 0:
                pos_interp += Vector((0, -onda * 1.5, -onda * 0.5))
            else:
                pos_interp += Vector((0, onda * 0.5, onda * 0.3))
            anel_m.append(bm.verts.new(pos_interp))
        aneis_membrana.append(anel_m)
    aneis_membrana.append(aneis_tibia[0])
    
    for s_m in range(passos_m):
        for i in range(n_seg):
            f = bm.faces.new([aneis_membrana[s_m][i], aneis_membrana[s_m][(i+1)%n_seg],
                              aneis_membrana[s_m+1][(i+1)%n_seg], aneis_membrana[s_m+1][i]])
            f.material_index = idx_membrana; f.smooth = True

    # Alvéolos e Macro-espinhos Táteis de Quitina Negra
    espinhos_femur = [
        (math.radians(35), 0.08 * escala, 0.09 * escala),
        (math.radians(-35), 0.08 * escala, 0.09 * escala),
        (math.radians(110), 0.06 * escala, 0.08 * escala),
        (math.radians(-110), 0.06 * escala, 0.08 * escala),
    ]
    for ang_pos, z_pos, comp_esp in espinhos_femur:
        r_f = r_femur_base * 1.05
        p_base = p_centro + Vector((math.cos(ang_pos) * r_f, math.sin(ang_pos) * r_f, z_pos))
        d_esp = Vector((math.cos(ang_pos) * 0.8, math.sin(ang_pos) * 0.8, -0.6)).normalized()
        alv = bmesh.ops.create_cone(bm, segments=10, cap_ends=True, radius1=0.015*escala, radius2=0.012*escala, depth=0.008*escala,
                                    matrix=Matrix.Translation(p_base) @ d_esp.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in alv['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
        esp = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, radius1=0.011*escala, radius2=0.001, depth=comp_esp,
                                    matrix=Matrix.Translation(p_base + d_esp * comp_esp * 0.45) @ d_esp.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in esp['verts'] for v in f.verts): f.material_index = idx_espinho; f.smooth = True
            
    for i_esp in range(3):
        dist_esp = (0.08 + i_esp * 0.12) * escala
        p_base_t = p_origem_tibia + eixo_tibia * dist_esp
        for lado in (-1, 1):
            d_esp_t = (R_flex @ Vector((lado * 0.85, 0.2, -0.6))).normalized()
            p_esp_t = p_base_t + (R_flex @ Vector((lado * r_tibia_topo * 1.02, 0, 0)))
            alv = bmesh.ops.create_cone(bm, segments=10, cap_ends=True, radius1=0.014*escala, radius2=0.011*escala, depth=0.008*escala,
                                        matrix=Matrix.Translation(p_esp_t) @ d_esp_t.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in alv['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
            esp_t = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, radius1=0.010*escala, radius2=0.001, depth=0.10*escala,
                                          matrix=Matrix.Translation(p_esp_t + d_esp_t * 0.045 * escala) @ d_esp_t.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in esp_t['verts'] for v in f.verts): f.material_index = idx_espinho; f.smooth = True

def construir_garra_tarsal_macro(bm, p_tarso=Vector((0,0,0)), dir_pata=Vector((0,1,0)), escala=1.0,
                                 idx_quitina=0, idx_presa=2, idx_escopula=4):
    """Constrói o tarso terminal, pré-tarso com 2 garras curvas pectinadas e almofada de escópula adesiva."""
    q_dir = dir_pata.normalized().to_track_quat('Z', 'Y')
    
    # Segmento distal do tarso
    tarso_seg = bmesh.ops.create_cone(bm, segments=16, cap_ends=True, radius1=0.038*escala, radius2=0.024*escala, depth=0.28*escala,
                                      matrix=Matrix.Translation(p_tarso - q_dir @ Vector((0, 0, 0.14*escala))) @ q_dir.to_matrix().to_4x4())
    for f in bm.faces:
        if any(v in tarso_seg['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
        
    # Placa esclerotizada do pré-tarso conectando o tarso às garras
    pretarso = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=0.025 * escala)
    for v in pretarso['verts']:
        v.co = p_tarso + (q_dir @ Vector((v.co.x * 1.1, v.co.y * 1.0, v.co.z * 0.7)))
    for f in bm.faces:
        if any(v in pretarso['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True
        
    for c_i in range(8):
        ang_c = c_i * (math.pi / 4)
        p_c = p_tarso - q_dir @ Vector((math.cos(ang_c)*0.03*escala, math.sin(ang_c)*0.03*escala, 0.08*escala))
        d_c = (q_dir @ Vector((math.cos(ang_c)*0.5, math.sin(ang_c)*0.5, 0.8))).normalized()
        cerda = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.002*escala, radius2=0.0004, depth=0.045*escala,
                                      matrix=Matrix.Translation(p_c) @ d_c.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in cerda['verts'] for v in f.verts): f.material_index = idx_quitina; f.smooth = True

    # Pré-tarso com 2 Garras Curvas Pectinadas (dentes em pente)
    for g_lado in (-1, 1):
        p_base_g = p_tarso + (q_dir @ Vector((g_lado * 0.012 * escala, 0.005 * escala, 0.005 * escala)))
        passos = 14
        r_ini_g = 0.012 * escala
        aneis_garra = []
        for i_p in range(passos + 1):
            t = i_p / passos
            ang_g = t * math.radians(115)
            p_arco = p_base_g + (q_dir @ Vector((g_lado * 0.006 * escala * (1.0 - t),
                                                 math.sin(ang_g) * 0.080 * escala,
                                                 -math.cos(ang_g) * 0.055 * escala + 0.055 * escala)))
            r_cur = r_ini_g * (1.0 - t * 0.90)
            anel = []
            for a_i in range(8):
                rad = a_i * 2 * math.pi / 8
                anel.append(bm.verts.new(p_arco + (q_dir @ Vector((math.cos(rad) * r_cur, 0, math.sin(rad) * r_cur)))))
            aneis_garra.append(anel)
            
            if 3 <= i_p <= 10:
                p_dente = p_arco + (q_dir @ Vector((0, 0, -r_cur * 1.25)))
                d_cone = (q_dir @ Vector((0, 0.004, -0.014))).normalized()
                dente_g = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.003*escala, radius2=0.0005, depth=0.016*escala,
                                                matrix=Matrix.Translation(p_dente) @ d_cone.to_track_quat('Z', 'Y').to_matrix().to_4x4())
                for f in bm.faces:
                    if any(v in dente_g['verts'] for v in f.verts): f.material_index = idx_presa; f.smooth = True
                    
        v_base = bm.verts.new(p_base_g)
        for a_i in range(8):
            f = bm.faces.new([aneis_garra[0][(a_i+1)%8], aneis_garra[0][a_i], v_base])
            f.material_index = idx_presa; f.smooth = True
        for s in range(passos):
            for a_i in range(8):
                f = bm.faces.new([aneis_garra[s][a_i], aneis_garra[s][(a_i+1)%8],
                                  aneis_garra[s+1][(a_i+1)%8], aneis_garra[s+1][a_i]])
                f.material_index = idx_presa; f.smooth = True
        v_ponta = bm.verts.new(p_arco + (q_dir @ Vector((0, 0.008*escala, -0.008*escala))))
        for a_i in range(8):
            f = bm.faces.new([aneis_garra[-1][a_i], aneis_garra[-1][(a_i+1)%8], v_ponta])
            f.material_index = idx_presa; f.smooth = True

    # Almofada de Escópula Tarsal Adesiva
    p_esc = p_tarso + (q_dir @ Vector((0, 0.010 * escala, -0.010 * escala)))
    for p_i in range(36):
        ang_p = p_i * (math.pi / 18)
        p_pelo = p_esc + (q_dir @ Vector((math.cos(ang_p) * 0.018 * escala, math.sin(ang_p) * 0.018 * escala * 0.6, 0)))
        d_pelo = (q_dir @ Vector((math.cos(ang_p) * 0.4, 0.7, -0.85))).normalized()
        pelo = bmesh.ops.create_cone(bm, segments=6, cap_ends=True, radius1=0.0022*escala, radius2=0.0004, depth=0.045*escala,
                                     matrix=Matrix.Translation(p_pelo) @ d_pelo.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in pelo['verts'] for v in f.verts): f.material_index = idx_escopula; f.smooth = True

# =========================================================================
# FUNÇÕES DE RENDERIZAÇÃO
# =========================================================================

def render_1_rosto_macro():
    print('>>> [1/4] RENDERIZANDO ROSTO MACRO V7 (QUITINA ÉBANO PROFUNDA, 8 OLHOS ÔNIX, PRESAS RUBI)...')
    sc = init_cycles()
    mats = criar_mats()
    
    me = bpy.data.meshes.new('RostoMacroMesh')
    bm = bmesh.new()
    construir_rosto_realista(bm, offset=Vector((0, 0, 0)), escala=1.0,
                             idx_quitina=0, idx_olho=1, idx_presa=2, idx_membrana=3, idx_escopula=4, idx_veneno=5)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('RostoMacroMesh', me)
    sc.collection.objects.link(obj)
    for m in mats: obj.data.materials.append(m)
    
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1; mod.render_levels = 2
    
    # Iluminação calibrada (suave e contrastada para manter o preto ébano)
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 90; l1.size = 1.0; l1.color = (1.0, 0.98, 0.95)
    ol1 = bpy.data.objects.new('Key', l1); ol1.location = (0.65, -1.6, 0.65)
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 130; l2.size = 1.4; l2.color = (0.60, 0.80, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2); ol2.location = (-1.1, 0.9, 0.7)
    sc.collection.objects.link(ol2)
    
    l3 = bpy.data.lights.new('FillBocal', 'AREA')
    l3.energy = 40; l3.size = 0.8; l3.color = (1.0, 0.90, 0.82)
    ol3 = bpy.data.objects.new('FillBocal', l3); ol3.location = (0.0, -1.2, -0.65)
    sc.collection.objects.link(ol3)
    
    alvo = Vector((0.0, -0.30, -0.12))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 72
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((0.25, -1.75, 0.02))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    out_path = os.path.join(AQUI, 'aranha_organica_rosto_macro.png')
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f'>>> RENDER 1 CONCLUÍDO: {out_path}')

def render_2_articulacao_macro():
    print('>>> [2/4] RENDERIZANDO ARTICULAÇÃO E LIGAMENTO MACRO V7 (CÔNDILOS, MEMBRANA SANFONADA, ESPINHOS NEGROS)...')
    sc = init_cycles()
    mats = criar_mats()
    
    me = bpy.data.meshes.new('ArticulacaoMacroMesh')
    bm = bmesh.new()
    construir_articulacao_macro(bm, p_centro=Vector((0, 0, 0)), escala=1.0,
                                idx_quitina=0, idx_membrana=3, idx_espinho=0)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('ArticulacaoMacroMesh', me)
    sc.collection.objects.link(obj)
    for m in mats: obj.data.materials.append(m)
    
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1; mod.render_levels = 2
    
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 110; l1.size = 1.0; l1.color = (1.0, 0.98, 0.95)
    ol1 = bpy.data.objects.new('Key', l1); ol1.location = (0.7, -1.1, 0.4)
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 140; l2.size = 1.2; l2.color = (0.6, 0.8, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2); ol2.location = (-0.9, 0.7, 0.5)
    sc.collection.objects.link(ol2)
    
    alvo = Vector((0, 0, -0.02))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 100
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((0.45, -0.85, 0.15))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    out_path = os.path.join(AQUI, 'aranha_organica_articulacao_ligamento.png')
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f'>>> RENDER 2 CONCLUÍDO: {out_path}')

def render_3_boca_garras_macro():
    print('>>> [3/4] RENDERIZANDO GARRA TARSAL PECTINADA MACRO V7 (ENQUADRAMENTO SUPERIOR SOBRE ARDÓSIA)...')
    sc = init_cycles()
    mats = criar_mats()
    
    me = bpy.data.meshes.new('GarraMacroMesh')
    bm = bmesh.new()
    
    # Construir garra tarsal apoiada centralmente sobre a rocha
    construir_garra_tarsal_macro(bm, p_tarso=Vector((0.0, 0.0, 0.02)), dir_pata=Vector((0.0, -0.5, -0.85)), escala=1.5,
                                 idx_quitina=0, idx_presa=2, idx_escopula=4)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('GarraMacroMesh', me)
    sc.collection.objects.link(obj)
    for m in mats: obj.data.materials.append(m)
    
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1; mod.render_levels = 2
    
    # Pedestal de Ardósia negra
    m_ped = mat_pedestal('SoloArdosia')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.15))
    ped = bpy.context.active_object
    ped.scale = (2.5, 2.0, 0.10)
    ped.data.materials.append(m_ped)
    for p in ped.data.polygons: p.use_smooth = False
    
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 110; l1.size = 1.0; l1.color = (1.0, 0.98, 0.92)
    ol1 = bpy.data.objects.new('Key', l1); ol1.location = (0.5, -0.9, 0.8)
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 140; l2.size = 1.2; l2.color = (0.55, 0.75, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2); ol2.location = (-0.7, 0.7, 0.7)
    sc.collection.objects.link(ol2)
    
    # Câmera macro frontal focada nas garras e pente pectinada
    alvo = Vector((0.0, 0.05, 0.02))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 90
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((0.22, -0.95, 0.35))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    out_path = os.path.join(AQUI, 'aranha_organica_boca_garras.png')
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f'>>> RENDER 3 CONCLUÍDO: {out_path}')

def render_4_corpo_completo():
    print('>>> [4/4] RENDERIZANDO ORGANISMO COMPLETO V7 (8 PERNAS INTEIRIÇAS NO CEFALOTÓRAX, ZERO VÃOS)...')
    sc = init_cycles()
    mats = criar_mats()
    
    me = bpy.data.meshes.new('AranhaCompletaMesh')
    bm = bmesh.new()
    
    # 1. Rosto e Cefalotórax Frontal
    construir_rosto_realista(bm, offset=Vector((0, -0.22, 0.06)), escala=1.0,
                             idx_quitina=0, idx_olho=1, idx_presa=2, idx_membrana=3, idx_escopula=4, idx_veneno=5)
    
    # 2. Esterno Ventral Plano
    esterno = bmesh.ops.create_cone(bm, segments=18, cap_ends=True, radius1=0.28, radius2=0.22, depth=0.06,
                                    matrix=Matrix.Translation(Vector((0, -0.05, -0.04))))
    for f in bm.faces:
        if any(v in esterno['verts'] for v in f.verts): f.material_index = 0; f.smooth = True
        
    # 3. Pedicelo Articulado (Cintura)
    ped = bmesh.ops.create_cone(bm, segments=14, cap_ends=True, radius1=0.09, radius2=0.08, depth=0.18,
                                matrix=Matrix.Translation(Vector((0, 0.22, 0.07))) @ Matrix.Rotation(math.radians(90), 4, 'X'))
    for f in bm.faces:
        if any(v in ped['verts'] for v in f.verts): f.material_index = 3; f.smooth = True

    # 4. Opistossoma (Abdômen em Gota)
    passos_ab = 18
    n_seg_ab = 28
    aneis_ab = []
    p_centro_ab = Vector((0, 0.78, 0.16))
    for s in range(passos_ab + 1):
        t = s / passos_ab
        y_ab = (t - 0.35) * 0.95
        r_ab = 0.48 * math.sin(t * math.pi * 0.88 + 0.12)
        anel = []
        for i in range(n_seg_ab):
            ang = i * 2 * math.pi / n_seg_ab
            cos_a = math.cos(ang); sin_a = math.sin(ang)
            px = cos_a * r_ab * 1.15
            pz = sin_a * r_ab * 0.82
            anel.append(bm.verts.new(p_centro_ab + Vector((px, y_ab, pz))))
        aneis_ab.append(anel)
        
    v_ini_ab = bm.verts.new(p_centro_ab + Vector((0, -0.36 * 0.95, 0)))
    for i in range(n_seg_ab):
        f = bm.faces.new([aneis_ab[0][(i+1)%n_seg_ab], aneis_ab[0][i], v_ini_ab])
        f.material_index = 0; f.smooth = True
    for s in range(passos_ab):
        for i in range(n_seg_ab):
            f = bm.faces.new([aneis_ab[s][i], aneis_ab[s][(i+1)%n_seg_ab],
                              aneis_ab[s+1][(i+1)%n_seg_ab], aneis_ab[s+1][i]])
            f.material_index = 0; f.smooth = True
    v_fim_ab = bm.verts.new(p_centro_ab + Vector((0, 0.65 * 0.95, -0.05)))
    for i in range(n_seg_ab):
        f = bm.faces.new([aneis_ab[-1][i], aneis_ab[-1][(i+1)%n_seg_ab], v_fim_ab])
        f.material_index = 0; f.smooth = True
        
    # Fiandeiras Traseiras
    p_fian = v_fim_ab.co + Vector((0, 0.02, -0.04))
    for fx, fy, fz in [(-0.040, 0, 0.02), (0.040, 0, 0.02), (-0.055, 0.015, -0.01), (0.055, 0.015, -0.01), (-0.020, 0.025, -0.03), (0.020, 0.025, -0.03)]:
        f_c = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, radius1=0.025, radius2=0.008, depth=0.065,
                                    matrix=Matrix.Translation(p_fian + Vector((fx, fy, fz))) @ Matrix.Rotation(math.radians(-22), 4, 'X'))
        for f in bm.faces:
            if any(v in f_c['verts'] for v in f.verts): f.material_index = 0; f.smooth = True

    # 5. AS 8 PERNAS ANATÔMICAS (Conexões Contínuas e Seladas por Côndilos Articulares)
    pernas_cfg = [
        (-1, -38,  1.02, 0.58, 1.55, Vector((-0.20, -0.32, 0.00))),
        ( 1,  38,  1.02, 0.58, 1.55, Vector(( 0.20, -0.32, 0.00))),
        (-1, -72,  0.98, 0.62, 1.50, Vector((-0.23, -0.18, 0.01))),
        ( 1,  72,  0.98, 0.62, 1.50, Vector(( 0.23, -0.18, 0.01))),
        (-1, -108, 0.94, 0.64, 1.45, Vector((-0.22, -0.04, 0.01))),
        ( 1,  108, 0.94, 0.64, 1.45, Vector(( 0.22, -0.04, 0.01))),
        (-1, -145, 1.15, 0.52, 1.75, Vector((-0.18,  0.10, 0.00))),
        ( 1,  145, 1.15, 0.52, 1.75, Vector(( 0.18,  0.10, 0.00))),
    ]
    
    for lado, az, esc, hj, ext, off in pernas_cfg:
        R_az = Matrix.Rotation(math.radians(az), 4, 'Z')
        r_ext = ext * esc
        h_j = hj * esc
        nos = [
            Vector((0.00, 0, 0.00)),
            Vector((0.14 * esc, 0, 0.04 * esc)),
            Vector((r_ext * 0.44, 0, h_j * 1.05)),
            Vector((r_ext * 0.54, 0, h_j)),
            Vector((r_ext * 0.80, 0, 0.05 * esc)),
            Vector((r_ext * 1.00, 0, -0.42 * esc)),
        ]
        nos_g = [off + (R_az @ n) for n in nos]
        
        # Segmentos cilíndricos com sobreposição nas pontas (eliminando fendas)
        for i_s in range(len(nos_g) - 1):
            p_a = nos_g[i_s]
            p_b = nos_g[i_s+1]
            dir_s = (p_b - p_a).normalized()
            comp_seg = (p_b - p_a).length
            r_s = (0.075 - i_s * 0.010) * esc
            
            # Segmento estendido ligeiramente para dentro do próximo nó (overlap de 15%)
            seg = bmesh.ops.create_cone(bm, segments=12, cap_ends=True, radius1=r_s, radius2=r_s * 0.88, depth=comp_seg * 1.12,
                                        matrix=Matrix.Translation((p_a + p_b)*0.5) @ dir_s.to_track_quat('Z', 'Y').to_matrix().to_4x4())
            for f in bm.faces:
                if any(v in seg['verts'] for v in f.verts): f.material_index = 0; f.smooth = True
                
            # Côndilo articular esférico que sela perfeitamente cada nó da junta
            if i_s < len(nos_g) - 2:
                cond_no = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=10, radius=r_s * 0.95)
                for v in cond_no['verts']: v.co += p_b
                for f in bm.faces:
                    if any(v in cond_no['verts'] for v in f.verts): f.material_index = 0; f.smooth = True
                    
        # Garra tarsal pectinada no final de cada perna
        dir_final = (nos_g[-1] - nos_g[-2]).normalized()
        construir_garra_tarsal_macro(bm, p_tarso=nos_g[-1], dir_pata=dir_final, escala=esc * 0.9,
                                     idx_quitina=0, idx_presa=2, idx_escopula=4)

    bm.to_mesh(me)
    obj = bpy.data.objects.new('AranhaCompletaMesh', me)
    sc.collection.objects.link(obj)
    for m in mats: obj.data.materials.append(m)
    
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1; mod.render_levels = 2
    
    # Solo de Rocha/Ardósia escura
    m_chao = mat_pedestal('SoloRocha')
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.43))
    chao = bpy.context.active_object
    chao.data.materials.append(m_chao)
    for p in chao.data.polygons: p.use_smooth = True
    
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 220; l1.size = 3.0; l1.color = (1.0, 0.96, 0.90)
    ol1 = bpy.data.objects.new('Key', l1); ol1.location = (2.8, -3.5, 3.2)
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 260; l2.size = 3.5; l2.color = (0.55, 0.75, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2); ol2.location = (-3.2, 3.5, 2.8)
    sc.collection.objects.link(ol2)
    
    l3 = bpy.data.lights.new('Fill', 'AREA')
    l3.energy = 80; l3.size = 2.5; l3.color = (0.9, 0.85, 0.8)
    ol3 = bpy.data.objects.new('Fill', l3); ol3.location = (0, -2.5, 1.2)
    sc.collection.objects.link(ol3)
    
    alvo = Vector((0, 0.15, 0.05))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 50
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((2.4, -3.4, 2.0))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    out_path = os.path.join(AQUI, 'aranha_organica_corpo_pelugem.png')
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f'>>> RENDER 4 CONCLUÍDO: {out_path}')

if __name__ == '__main__':
    render_1_rosto_macro()
    render_2_articulacao_macro()
    render_3_boca_garras_macro()
    render_4_corpo_completo()
    print('TODOS OS 4 ESTUDOS ANATÔMICOS V7 FORAM CONCLUÍDOS COM SUCESSO!')
