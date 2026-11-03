"""Estudo Anatômico e Estrutural Independente: Aranha Orgânica (Cycles OptiX)
Versão 4: Iluminação de alta legibilidade, articulações conectadas, perspectiva 3D dos artículos da perna e detalhes biológicos nítidos.
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector, Matrix, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))

def init_cycles():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -0.1
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 1200
    sc.render.film_transparent = False

    mundo = bpy.data.worlds.new('Mundo')
    sc.world = mundo
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.02, 0.025, 0.03, 1.0)
    bg.inputs['Strength'].default_value = 0.5
    return sc

def no(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n

def criar_material_quitina_viva(nome, cor_escura=(0.012, 0.008, 0.007), cor_veio=(0.08, 0.025, 0.015), rough=0.12, coat=1.0, subsurf=0.28):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    coord = no(nt, 'ShaderNodeTexCoord')
    noise_poros = no(nt, 'ShaderNodeTexNoise', **{'Scale': 35.0, 'Detail': 5.0, 'Roughness': 0.6})
    nt.links.new(coord.outputs['Object'], noise_poros.inputs['Vector'])
    
    noise_veios = no(nt, 'ShaderNodeTexNoise', **{'Scale': 8.0, 'Detail': 4.0, 'Roughness': 0.4})
    nt.links.new(coord.outputs['Object'], noise_veios.inputs['Vector'])
    
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.10, 'Distance': 0.02})
    nt.links.new(noise_poros.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    ramp = no(nt, 'ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (*cor_escura, 1.0)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (*cor_veio, 1.0)
    nt.links.new(noise_veios.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Subsurface Weight'].default_value = subsurf
    bsdf.inputs['Subsurface Radius'].default_value = (0.7, 0.15, 0.08)
    bsdf.inputs['Subsurface Scale'].default_value = 0.03
    bsdf.inputs['Specular IOR Level'].default_value = 0.85
    
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Coat Roughness'].default_value = 0.015
    bsdf.inputs['Coat IOR'].default_value = 1.34
    return m

def criar_material_olho(nome):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (0.01, 0.002, 0.003, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['Specular IOR Level'].default_value = 1.0
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.01
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.10, 0.03, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 4.0
    return m

def criar_material_presa(nome):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (0.008, 0.003, 0.003, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.04
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.01
    return m

def criar_material_veneno(nome):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (0.80, 1.0, 0.75, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.01
    bsdf.inputs['Transmission Weight'].default_value = 0.98
    bsdf.inputs['IOR'].default_value = 1.34
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.01
    return m

def criar_material_pedestal(nome):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    coord = no(nt, 'ShaderNodeTexCoord')
    noise = no(nt, 'ShaderNodeTexNoise', **{'Scale': 16.0, 'Detail': 5.0})
    nt.links.new(coord.outputs['Object'], noise.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.10})
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    bsdf.inputs['Base Color'].default_value = (0.045, 0.048, 0.052, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.30
    bsdf.inputs['Coat Weight'].default_value = 0.8
    bsdf.inputs['Coat Roughness'].default_value = 0.06
    return m

# =========================================================================
# GEOMETRIA
# =========================================================================

def construir_cefalotorax_mesh(bm, mat_corpo_idx=0, mat_olho_idx=1, offset=Vector((0,0,0)), escala=1.0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=26, radius=0.45 * escala)
    verts = res['verts']
    for v in verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        if y < 0:
            largura = 1.0 + (y * 0.28)
        else:
            largura = 1.0 - (y * 0.45)
        v.co.x *= largura * 1.32
        v.co.y *= 1.40
        v.co.z *= 0.58
        
        if y < -0.12 and z > 0:
            v.co.z += (abs(y) - 0.12) * 0.28
            
        d_fovea = math.sqrt((v.co.x)**2 + (v.co.y - 0.04 * escala)**2)
        if d_fovea < 0.20 * escala and v.co.z > 0:
            v.co.z -= (0.20 * escala - d_fovea) * 0.45
            
        if v.co.z > 0 and abs(v.co.x) > 0.16 * escala:
            ang = math.atan2(v.co.y, v.co.x)
            v.co.z += math.sin(ang * 4.5) * 0.018 * escala
            
        if v.co.z < -0.07 * escala:
            v.co.z = -0.08 * escala + (v.co.z + 0.07 * escala) * 0.2
            
        v.co += offset
        
    for f in bm.faces:
        if any(v in verts for v in f.verts):
            f.material_index = mat_corpo_idx
            f.smooth = True
            
    olhos_coords = [
        (-0.065, -0.52, 0.15, 0.038),
        ( 0.065, -0.52, 0.15, 0.038),
        (-0.145, -0.48, 0.12, 0.028),
        ( 0.145, -0.48, 0.12, 0.028),
        (-0.055, -0.43, 0.18, 0.030),
        ( 0.055, -0.43, 0.18, 0.030),
        (-0.135, -0.40, 0.15, 0.026),
        ( 0.135, -0.40, 0.15, 0.026),
    ]
    for ox, oy, oz, raio in olhos_coords:
        p_olho = offset + Vector((ox, oy, oz)) * escala
        o_res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=raio * escala)
        for ov in o_res['verts']:
            ov.co += p_olho
        for f in bm.faces:
            if any(v in o_res['verts'] for v in f.verts):
                f.material_index = mat_olho_idx
                f.smooth = True

def construir_aparelho_bucal_mesh(bm, mat_corpo_idx=0, mat_presa_idx=2, mat_veneno_idx=3,
                                  offset=Vector((0,0,0)), escala=1.0, com_pedipalpos=True, com_teto=True):
    if com_teto:
        t_res = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.28 * escala)
        for tv in t_res['verts']:
            tv.co.y *= 0.6
            tv.co.z *= 0.4
            tv.co += offset + Vector((0, -0.44 * escala, 0.08 * escala))
        for f in bm.faces:
            if any(v in t_res['verts'] for v in f.verts):
                f.material_index = mat_corpo_idx
                f.smooth = True
                
    for lado in (-1, 1):
        cx = lado * 0.088 * escala
        base_paturon = offset + Vector((cx, -0.54 * escala, 0.01 * escala))
        
        p_res = bmesh.ops.create_cone(bm, segments=18, cap_ends=True, cap_tris=True,
                                      radius1=0.085 * escala, radius2=0.048 * escala, depth=0.28 * escala,
                                      matrix=Matrix.Translation(base_paturon) @ Matrix.Rotation(math.radians(24), 4, 'X') @ Matrix.Rotation(math.radians(-lado * 8), 4, 'Y'))
        for v in p_res['verts']:
            ang = math.atan2(v.co.y - base_paturon.y, v.co.x - base_paturon.x)
            v.co += Vector((math.cos(ang), math.sin(ang), 0)) * (math.sin(ang * 8.0) * 0.005 * escala)
        for f in bm.faces:
            if any(v in p_res['verts'] for v in f.verts):
                f.material_index = mat_corpo_idx
                f.smooth = True
                
        # Presas conectadas DIRETAMENTE à ponta do paturon
        ponto_base = base_paturon + Vector((lado * 0.012, -0.065 * escala, -0.125 * escala))
        passos = 14
        r_inicial = 0.032 * escala
        anel_ant = []
        for i_p in range(passos + 1):
            t = i_p / passos
            ang = t * math.radians(85)
            p_eixo = ponto_base + Vector((-lado * math.sin(ang) * 0.11 * escala,
                                          -math.cos(ang) * 0.05 * escala,
                                          -math.sin(ang) * 0.16 * escala))
            r = r_inicial * (1.0 - t * 0.92)
            
            anel = []
            for a_i in range(8):
                rad = a_i * 2 * math.pi / 8
                nx = math.cos(rad) * r
                ny = math.sin(rad) * r * 0.75
                anel.append(bm.verts.new(p_eixo + Vector((nx, ny, 0))))
            if anel_ant:
                for a_i in range(8):
                    f = bm.faces.new([anel_ant[a_i], anel_ant[(a_i+1)%8], anel[(a_i+1)%8], anel[a_i]])
                    f.material_index = mat_presa_idx
                    f.smooth = True
            else:
                v_topo = bm.verts.new(ponto_base + Vector((0, 0, 0.01 * escala)))
                for a_i in range(8):
                    f = bm.faces.new([anel[a_i], anel[(a_i+1)%8], v_topo])
                    f.material_index = mat_presa_idx
                    f.smooth = True
            anel_ant = anel
            
        v_ponta = bm.verts.new(p_eixo + Vector((-lado * 0.008 * escala, 0, -0.015 * escala)))
        for a_i in range(8):
            f = bm.faces.new([anel_ant[a_i], anel_ant[(a_i+1)%8], v_ponta])
            f.material_index = mat_presa_idx
            f.smooth = True
            
        # Gotícula de veneno
        g_res = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=0.016 * escala)
        for gv in g_res['verts']:
            gv.co.z *= 1.55
            gv.co += v_ponta.co + Vector((0, 0, -0.010 * escala))
        for f in bm.faces:
            if any(v in g_res['verts'] for v in f.verts):
                f.material_index = mat_veneno_idx
                f.smooth = True
                
        # Pedipalpos
        if com_pedipalpos:
            p_base_palpo = offset + Vector((lado * 0.19 * escala, -0.46 * escala, 0.04 * escala))
            articulos_palpo = [
                (Vector((0, 0, 0)), 0.045 * escala),
                (Vector((lado * 0.06, -0.10, -0.02)) * escala, 0.038 * escala),
                (Vector((lado * 0.09, -0.22,  0.03)) * escala, 0.034 * escala),
                (Vector((lado * 0.07, -0.34,  0.01)) * escala, 0.030 * escala),
                (Vector((lado * 0.03, -0.45, -0.05)) * escala, 0.038 * escala),
            ]
            anel_ant_p = []
            for p_no, r_no in articulos_palpo:
                pt = p_base_palpo + p_no
                anel_p = []
                for a_i in range(8):
                    rad = a_i * 2 * math.pi / 8
                    anel_p.append(bm.verts.new(pt + Vector((math.cos(rad) * r_no, 0, math.sin(rad) * r_no))))
                if anel_ant_p:
                    for a_i in range(8):
                        f = bm.faces.new([anel_ant_p[a_i], anel_ant_p[(a_i+1)%8], anel_p[(a_i+1)%8], anel_p[a_i]])
                        f.material_index = mat_corpo_idx
                        f.smooth = True
                else:
                    v_base_p = bm.verts.new(pt + Vector((0, 0.02 * escala, 0)))
                    for a_i in range(8):
                        f = bm.faces.new([anel_p[a_i], anel_p[(a_i+1)%8], v_base_p])
                        f.material_index = mat_corpo_idx
                        f.smooth = True
                anel_ant_p = anel_p
            v_ponta_palpo = bm.verts.new(p_base_palpo + articulos_palpo[-1][0] + Vector((0, -0.03 * escala, 0)))
            for a_i in range(8):
                f = bm.faces.new([anel_ant_p[a_i], anel_ant_p[(a_i+1)%8], v_ponta_palpo])
                f.material_index = mat_corpo_idx
                f.smooth = True

def construir_abdomen_mesh(bm, mat_corpo_idx=0, mat_fiandeira_idx=4, offset=Vector((0,0,0)), escala=1.0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=38, v_segments=28, radius=0.55 * escala)
    verts = res['verts']
    for v in verts:
        v.co.y *= 1.48
        fator_gota = 1.0 + (v.co.y * 0.35) if v.co.y > 0 else 1.0 + (v.co.y * 0.25)
        v.co.x *= fator_gota * 1.18
        v.co.z *= fator_gota * 0.82
        
        if v.co.y > 0:
            v.co.z -= (v.co.y ** 1.8) * 0.12 * escala
            
        if v.co.z > 0.05 * escala:
            estria = math.sin(v.co.y * 12.0) * 0.015 * escala
            v.co.z += estria
            
        v.co += offset
        
    for f in bm.faces:
        if any(v in verts for v in f.verts):
            f.material_index = mat_corpo_idx
            f.smooth = True
            
    # Roseta de 6 Fiandeiras na ponta póstero-ventral
    y_traseiro = 0.55 * escala * 1.48 * 0.92
    p_fian = offset + Vector((0, y_traseiro, -0.20 * escala))
    fian_coords = [
        (-0.045,  0.00,  0.03, 0.032, 0.08),
        ( 0.045,  0.00,  0.03, 0.032, 0.08),
        (-0.065,  0.02, -0.01, 0.025, 0.07),
        ( 0.065,  0.02, -0.01, 0.025, 0.07),
        (-0.028,  0.03, -0.04, 0.020, 0.05),
        ( 0.028,  0.03, -0.04, 0.020, 0.05),
    ]
    for fx, fy, fz, rb, comp in fian_coords:
        pos = p_fian + Vector((fx, fy, fz)) * escala
        f_res = bmesh.ops.create_cone(bm, segments=12, cap_ends=True, cap_tris=True,
                                      radius1=rb * escala, radius2=rb*0.35 * escala, depth=comp * escala,
                                      matrix=Matrix.Translation(pos) @ Matrix.Rotation(math.radians(-25), 4, 'X'))
        for f in bm.faces:
            if any(v in f_res['verts'] for v in f.verts):
                f.material_index = mat_fiandeira_idx
                f.smooth = True

def construir_perna_articulada_dissecada(bm, mat_corpo_idx=0, mat_membrana_idx=5, mat_garra_idx=2,
                                         origem=Vector((0,0,0)), escala=1.0, espacamento=0.08):
    articulos = [
        ('1_Coxa',      0.18 * escala, 0.082 * escala, 0.070 * escala),
        ('2_Trocanter', 0.11 * escala, 0.068 * escala, 0.065 * escala),
        ('3_Femur',     0.70 * escala, 0.078 * escala, 0.058 * escala),
        ('4_Patela',    0.16 * escala, 0.062 * escala, 0.056 * escala),
        ('5_Tibia',     0.82 * escala, 0.054 * escala, 0.036 * escala),
        ('6_Metatarso', 0.60 * escala, 0.034 * escala, 0.024 * escala),
        ('7_Tarso',     0.34 * escala, 0.022 * escala, 0.012 * escala),
    ]
    
    pos_x = origem.x
    for nome, comp, rb, rp in articulos:
        meio_x = pos_x + comp * 0.5
        c_res = bmesh.ops.create_cone(bm, segments=18, cap_ends=True, cap_tris=True,
                                      radius1=rb, radius2=rp, depth=comp,
                                      matrix=Matrix.Translation(Vector((meio_x, origem.y, origem.z))) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
        
        if 'Femur' in nome:
            for v in c_res['verts']:
                fator_m = math.sin((v.co.x - pos_x) / comp * math.pi)
                v.co.z += fator_m * 0.022 * escala
                v.co.y += fator_m * 0.014 * escala
                
        if 'Patela' in nome:
            for v in c_res['verts']:
                v.co.z += 0.018 * escala
                
        for f in bm.faces:
            if any(v in c_res['verts'] for v in f.verts):
                f.material_index = mat_corpo_idx
                f.smooth = True
                
        if 'Tibia' in nome:
            for s_i in range(5):
                s_x = pos_x + comp * (0.2 + s_i * 0.16)
                for s_ang in (-45, 45):
                    rad = math.radians(s_ang)
                    p_esp = Vector((s_x, origem.y + math.sin(rad) * 0.045 * escala, origem.z + math.cos(rad) * 0.045 * escala))
                    esp_res = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, cap_tris=True,
                                                    radius1=0.007 * escala, radius2=0.001, depth=0.050 * escala,
                                                    matrix=Matrix.Translation(p_esp) @ Matrix.Rotation(rad, 4, 'X'))
                    for f in bm.faces:
                        if any(v in esp_res['verts'] for v in f.verts):
                            f.material_index = mat_garra_idx
                            f.smooth = True
                            
        if 'Tarso' in nome:
            for g_lado in (-1, 1):
                p_garra = Vector((pos_x + comp + 0.02, origem.y + g_lado * 0.014, origem.z - 0.008))
                g_res = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, cap_tris=True,
                                              radius1=0.010 * escala, radius2=0.0015, depth=0.07 * escala,
                                              matrix=Matrix.Translation(p_garra) @ Matrix.Rotation(math.radians(115), 4, 'Y') @ Matrix.Rotation(math.radians(g_lado * 25), 4, 'Z'))
                for f in bm.faces:
                    if any(v in g_res['verts'] for v in f.verts):
                        f.material_index = mat_garra_idx
                        f.smooth = True
                        
        pos_x += comp + espacamento

def construir_perna_articulada_viva(bm, mat_corpo_idx=0, mat_membrana_idx=5, mat_garra_idx=2,
                                    origem=Vector((0,0,0)), escala=1.0, ang_azimute=0,
                                    altura_joelho=0.55, extensao_raio=1.55):
    R_az = Matrix.Rotation(math.radians(ang_azimute), 4, 'Z')
    r_ext = extensao_raio * escala
    h_j = altura_joelho * escala
    
    nos_locais = [
        Vector((0.00, 0, 0.00)),
        Vector((0.12 * escala, 0, 0.03 * escala)),
        Vector((0.20 * escala, 0, 0.06 * escala)),
        Vector((r_ext * 0.42, 0, h_j * 1.05)),
        Vector((r_ext * 0.52, 0, h_j)),
        Vector((r_ext * 0.78, 0, 0.05 * escala)),
        Vector((r_ext * 0.90, 0, -0.22 * escala)),
        Vector((r_ext * 1.00, 0, -0.42 * escala)),
    ]
    
    nos_globais = [origem + (R_az @ n) for n in nos_locais]
    raios = [0.075, 0.062, 0.070, 0.064, 0.054, 0.040, 0.026, 0.012]
    raios = [r * escala for r in raios]
    
    anel_ant = []
    for i in range(len(nos_globais)):
        pt = nos_globais[i]
        r = raios[i]
        
        if i < len(nos_globais) - 1:
            dir_v = (nos_globais[i+1] - pt).normalized()
        else:
            dir_v = (pt - nos_globais[i-1]).normalized()
        rot = dir_v.to_track_quat('Z', 'Y')
        
        anel = []
        for a_i in range(12):
            rad = a_i * 2 * math.pi / 12
            lx = math.cos(rad) * r * 0.88
            ly = math.sin(rad) * r
            anel.append(bm.verts.new(pt + (rot @ Vector((lx, ly, 0)))))
            
        if anel_ant:
            mat_idx = mat_corpo_idx
            if i in (2, 4, 5):
                mat_idx = mat_membrana_idx
            for a_i in range(12):
                f = bm.faces.new([anel_ant[a_i], anel_ant[(a_i+1)%12], anel[(a_i+1)%12], anel[a_i]])
                f.material_index = mat_idx
                f.smooth = True
        anel_ant = anel
        
    p_solo = nos_globais[-1]
    for g_lado in (-1, 1):
        dir_g = (R_az @ Vector((0.035, g_lado * 0.015, -0.025))).normalized()
        g_res = bmesh.ops.create_cone(bm, segments=8, cap_ends=True, cap_tris=True,
                                      radius1=0.008 * escala, radius2=0.0015, depth=0.05 * escala,
                                      matrix=Matrix.Translation(p_solo + dir_g * 0.025) @ dir_g.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        for f in bm.faces:
            if any(v in g_res['verts'] for v in f.verts):
                f.material_index = mat_garra_idx
                f.smooth = True

# =========================================================================
# RENDERS DAS CENAS
# =========================================================================

def criar_materiais_gerais():
    m_corpo = criar_material_quitina_viva('QuitinaViva')
    m_olho = criar_material_olho('OlhoAranideo')
    m_presa = criar_material_presa('PresaEsmalte')
    m_veneno = criar_material_veneno('VenenoTranslucido')
    m_fiandeira = criar_material_quitina_viva('Fiandeiras', (0.015, 0.010, 0.008), (0.08, 0.025, 0.015), rough=0.18)
    m_membrana = criar_material_quitina_viva('MembranaArticular', (0.025, 0.010, 0.006), (0.15, 0.035, 0.02), rough=0.22, subsurf=0.40)
    return [m_corpo, m_olho, m_presa, m_veneno, m_fiandeira, m_membrana]

def render_aranha_completa():
    print('>>> [1/5] RENDERIZANDO ARANHA COMPLETA MONTADA...')
    sc = init_cycles()
    mats = criar_materiais_gerais()
    
    me = bpy.data.meshes.new('AranhaCompleta')
    bm = bmesh.new()
    
    construir_cefalotorax_mesh(bm, 0, 1, offset=Vector((0, -0.22, 0.05)))
    construir_aparelho_bucal_mesh(bm, 0, 2, 3, offset=Vector((0, -0.22, 0.05)), com_pedipalpos=True, com_teto=False)
    construir_abdomen_mesh(bm, 0, 4, offset=Vector((0, 0.72, 0.15)))
    
    p_res = bmesh.ops.create_cone(bm, segments=14, cap_ends=True, cap_tris=True, radius1=0.12, radius2=0.10, depth=0.22,
                                  matrix=Matrix.Translation(Vector((0, 0.20, 0.08))) @ Matrix.Rotation(math.radians(90), 4, 'X'))
    for f in bm.faces:
        if any(v in p_res['verts'] for v in f.verts):
            f.material_index = 5
            f.smooth = True
            
    pernas = [
        (-1, -38,  1.02, 0.58, 1.55, Vector((-0.20, -0.40, 0.02))),
        ( 1,  38,  1.02, 0.58, 1.55, Vector(( 0.20, -0.40, 0.02))),
        (-1, -72,  0.98, 0.62, 1.50, Vector((-0.24, -0.26, 0.04))),
        ( 1,  72,  0.98, 0.62, 1.50, Vector(( 0.24, -0.26, 0.04))),
        (-1, -108, 0.94, 0.64, 1.45, Vector((-0.22, -0.10, 0.04))),
        ( 1,  108, 0.94, 0.64, 1.45, Vector(( 0.22, -0.10, 0.04))),
        (-1, -145, 1.15, 0.52, 1.75, Vector((-0.18,  0.06, 0.02))),
        ( 1,  145, 1.15, 0.52, 1.75, Vector(( 0.18,  0.06, 0.02))),
    ]
    for lado, az, esc, hj, ext, off in pernas:
        construir_perna_articulada_viva(bm, 0, 5, 2, origem=off, escala=esc, ang_azimute=az,
                                       altura_joelho=hj, extensao_raio=ext)
        
    bm.to_mesh(me)
    obj = bpy.data.objects.new('AranhaOrganica', me)
    sc.collection.objects.link(obj)
    for m in mats:
        obj.data.materials.append(m)
        
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2
    
    m_chao = criar_material_pedestal('RochaMolhada')
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.43))
    chao = bpy.context.active_object
    chao.data.materials.append(m_chao)
    for p in chao.data.polygons:
        p.use_smooth = True
        
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 750
    l1.size = 3.5
    l1.color = (1.0, 0.95, 0.90)
    ol1 = bpy.data.objects.new('Key', l1)
    ol1.location = (3.2, -4.0, 3.8)
    ol1.rotation_euler = (math.radians(45), 0, math.radians(35))
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 900
    l2.size = 4.0
    l2.color = (0.55, 0.78, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2)
    ol2.location = (-4.0, 4.2, 3.2)
    ol2.rotation_euler = (math.radians(-40), 0, math.radians(-140))
    sc.collection.objects.link(ol2)
    
    alvo = Vector((0, 0.15, 0.05))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 52
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((2.8, -3.8, 2.2))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    sc.render.filepath = os.path.join(AQUI, 'anatomia_aranha_completa.png')
    bpy.ops.render.render(write_still=True)

def render_cefalotorax():
    print('>>> [2/5] RENDERIZANDO CEFALOTÓRAX E OLHOS ISOLADOS...')
    sc = init_cycles()
    mats = criar_materiais_gerais()
    
    me = bpy.data.meshes.new('Cefalotorax')
    bm = bmesh.new()
    construir_cefalotorax_mesh(bm, 0, 1, offset=Vector((0, 0, 0)), escala=1.0)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('Cefalotorax', me)
    sc.collection.objects.link(obj)
    for m in mats:
        obj.data.materials.append(m)
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2
    
    m_ped = criar_material_pedestal('Pedestal')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.15, location=(0, 0, -0.16))
    ped = bpy.context.active_object
    ped.data.materials.append(m_ped)
    for p in ped.data.polygons:
        p.use_smooth = True
        
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 400
    l1.size = 2.0
    ol1 = bpy.data.objects.new('Key', l1)
    ol1.location = (1.5, -2.0, 1.8)
    ol1.rotation_euler = (math.radians(45), 0, math.radians(35))
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 450
    l2.size = 2.0
    l2.color = (0.6, 0.8, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2)
    ol2.location = (-1.8, 1.8, 1.5)
    ol2.rotation_euler = (math.radians(-40), 0, math.radians(-140))
    sc.collection.objects.link(ol2)
    
    alvo = Vector((0, -0.25, 0.08))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 70
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((0.75, -1.85, 0.90))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    sc.render.filepath = os.path.join(AQUI, 'anatomia_cefalotorax.png')
    bpy.ops.render.render(write_still=True)

def render_aparelho_bucal():
    print('>>> [3/5] RENDERIZANDO APARELHO BUCAL ISOLADO (QUELÍCERAS, PRESAS E PEDIPALPOS)...')
    sc = init_cycles()
    mats = criar_materiais_gerais()
    
    me = bpy.data.meshes.new('AparelhoBucal')
    bm = bmesh.new()
    construir_aparelho_bucal_mesh(bm, 0, 2, 3, offset=Vector((0, 0.35, 0.16)), escala=1.1, com_pedipalpos=True, com_teto=True)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('AparelhoBucal', me)
    sc.collection.objects.link(obj)
    for m in mats:
        obj.data.materials.append(m)
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2
    
    m_ped = criar_material_pedestal('Pedestal')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.15, location=(0, 0, -0.22))
    ped = bpy.context.active_object
    ped.data.materials.append(m_ped)
    for p in ped.data.polygons:
        p.use_smooth = True
        
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 380
    l1.size = 1.8
    ol1 = bpy.data.objects.new('Key', l1)
    ol1.location = (1.2, -1.8, 1.4)
    ol1.rotation_euler = (math.radians(45), 0, math.radians(35))
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 420
    l2.size = 2.0
    l2.color = (0.6, 0.8, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2)
    ol2.location = (-1.5, 1.5, 1.2)
    ol2.rotation_euler = (math.radians(-40), 0, math.radians(-140))
    sc.collection.objects.link(ol2)
    
    # Fill frontal suave para iluminar os paturons
    l3 = bpy.data.lights.new('Fill', 'POINT')
    l3.energy = 80
    l3.color = (1.0, 0.9, 0.8)
    ol3 = bpy.data.objects.new('Fill', l3)
    ol3.location = (0, -1.5, 0.2)
    sc.collection.objects.link(ol3)
    
    alvo = Vector((0, -0.10, 0.02))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 72
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((0.0, -1.85, 0.40))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    sc.render.filepath = os.path.join(AQUI, 'anatomia_aparelho_bucal.png')
    bpy.ops.render.render(write_still=True)

def render_abdomen():
    print('>>> [4/5] RENDERIZANDO ABDÔMEN (OPISTOSSOMA) E FIANDEIRAS ISOLADOS...')
    sc = init_cycles()
    mats = criar_materiais_gerais()
    
    me = bpy.data.meshes.new('Abdomen')
    bm = bmesh.new()
    construir_abdomen_mesh(bm, 0, 4, offset=Vector((0, 0, 0.08)), escala=1.0)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('Abdomen', me)
    sc.collection.objects.link(obj)
    for m in mats:
        obj.data.materials.append(m)
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2
    
    m_ped = criar_material_pedestal('Pedestal')
    bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.15, location=(0, 0, -0.32))
    ped = bpy.context.active_object
    ped.data.materials.append(m_ped)
    for p in ped.data.polygons:
        p.use_smooth = True
        
    # Luz frontal principal iluminando a face posterior das fiandeiras
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 550
    l1.size = 2.8
    l1.color = (1.0, 0.95, 0.90)
    ol1 = bpy.data.objects.new('Key', l1)
    ol1.location = (2.2, 2.8, 2.2)
    ol1.rotation_euler = (math.radians(-35), 0, math.radians(-145))
    sc.collection.objects.link(ol1)
    
    # Luz de preenchimento suave
    l2 = bpy.data.lights.new('Fill', 'AREA')
    l2.energy = 380
    l2.size = 3.0
    l2.color = (0.7, 0.85, 1.0)
    ol2 = bpy.data.objects.new('Fill', l2)
    ol2.location = (-2.5, -1.8, 1.8)
    ol2.rotation_euler = (math.radians(45), 0, math.radians(40))
    sc.collection.objects.link(ol2)
    
    alvo = Vector((0, 0.45, -0.05))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 58
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((1.75, 2.30, 1.15))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    sc.render.filepath = os.path.join(AQUI, 'anatomia_abdomen.png')
    bpy.ops.render.render(write_still=True)

def render_perna_articulos():
    print('>>> [5/5] RENDERIZANDO PERNA DISSECADA EM 7 ARTÍCULOS...')
    sc = init_cycles()
    mats = criar_materiais_gerais()
    
    me = bpy.data.meshes.new('PernaDissecada')
    bm = bmesh.new()
    construir_perna_articulada_dissecada(bm, 0, 5, 2, origem=Vector((-1.65, 0, 0.10)), escala=1.0, espacamento=0.08)
    bm.to_mesh(me)
    obj = bpy.data.objects.new('PernaDissecada', me)
    sc.collection.objects.link(obj)
    for m in mats:
        obj.data.materials.append(m)
    mod = obj.modifiers.new('Subsurf', 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2
    
    m_ped = criar_material_pedestal('PedestalPrancha')
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.06))
    ped = bpy.context.active_object
    ped.scale = (4.0, 0.90, 0.12)
    ped.data.materials.append(m_ped)
    for p in ped.data.polygons:
        p.use_smooth = False
    p_mod = ped.modifiers.new('Bevel', 'BEVEL')
    p_mod.width = 0.02
    p_mod.segments = 2
    
    l1 = bpy.data.lights.new('Key', 'AREA')
    l1.energy = 600
    l1.size = 3.5
    l1.color = (1.0, 0.95, 0.90)
    ol1 = bpy.data.objects.new('Key', l1)
    ol1.location = (0.5, -3.0, 3.2)
    ol1.rotation_euler = (math.radians(45), 0, math.radians(10))
    sc.collection.objects.link(ol1)
    
    l2 = bpy.data.lights.new('Rim', 'AREA')
    l2.energy = 650
    l2.size = 4.0
    l2.color = (0.6, 0.8, 1.0)
    ol2 = bpy.data.objects.new('Rim', l2)
    ol2.location = (-0.5, 3.0, 2.5)
    ol2.rotation_euler = (math.radians(-40), 0, math.radians(-170))
    sc.collection.objects.link(ol2)
    
    # Câmera com ângulo 3/4 elevado e campo visual perfeito
    alvo = Vector((0, 0, 0.08))
    cam_d = bpy.data.cameras.new('Cam')
    cam_d.lens = 42
    cam = bpy.data.objects.new('Cam', cam_d)
    cam.location = Vector((0.0, -2.6, 2.1))
    d = alvo - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam
    
    sc.render.filepath = os.path.join(AQUI, 'anatomia_perna_articulos.png')
    bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    render_aranha_completa()
    render_cefalotorax()
    render_aparelho_bucal()
    render_abdomen()
    render_perna_articulos()
    print('ESTUDO ANATÔMICO REFINADO V4 CONCLUÍDO COM SUCESSO!')
