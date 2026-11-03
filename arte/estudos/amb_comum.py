"""Utilidades comuns para os estudos ambientais (Parte A do Pedido 3):
- Materiais orgânicos procedurais (casca fendida com musgo, folhagem com variação celular e nervuras, rocha estratificada
  com líquen e sujeira nas frestas, minérios oxidados, cristais bioluminescentes, chão de biomas do planeta).
- Construtores geométricos de malha única fechada (faces para fora, com espessura, sem transparência, origem na base
  z=0 e centro XY).
- Cena de conferência normal (vistas isométricas + close-up) e foto obrigatória a 30 m de altura com variantes
  espalhadas sobre chão parecido com o do jogo (câmera idêntica à CameraJogo: FOV 38°, inclinação ~64°).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, noise

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import mats, base3d

PI = math.pi
Z = Vector((0, 0, 1))


def iniciar_cena(semente=101):
    random.seed(semente)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = base3d.iniciar()
    sc.render.fps = 24
    sc.frame_start, sc.frame_end = 1, 1
    registrar_materiais()
    return sc


# ================================================================== MATERIAIS ORGÂNICOS PROCEDURAIS
def mat_org(nome, cor_base, cor_escura, cor_musgo=(0.14, 0.22, 0.08), rough=0.88, escala=12.0,
            estria_z=1.0, musgo_pe=0.45, bump_forca=0.35, metal=0.0, spec=0.25):
    """Material orgânico rústico (casca, rocha, caule, terra): sem aspecto plástico/liso, com frestas escuras (AO),
    variação por ruído em duas escalas, musgo/lama perto da base (z baixo) e relevo procedural."""
    if nome in bpy.data.materials:
        return bpy.data.materials[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    m.diffuse_color = (*cor_base, 1.0)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = spec
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    tc = no(nt, 'ShaderNodeTexCoord')
    mp = no(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, estria_z)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])

    ru1 = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 8.0, 'Roughness': 0.65, 'Distortion': 0.4})
    ru2 = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala * 4.5, 'Detail': 5.0, 'Roughness': 0.55})
    nt.links.new(mp.outputs['Vector'], ru1.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], ru2.inputs['Vector'])

    # Mistura cor base e cor escura pelo ruído principal + detalhe fino
    soma_r = no(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    soma_r.inputs[1].default_value = 0.72
    nt.links.new(ru1.outputs['Fac'], soma_r.inputs[0])
    nt.links.new(ru2.outputs['Fac'], soma_r.inputs[2])
    faixa = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.32, 'From Max': 0.78, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(soma_r.outputs['Value'], faixa.inputs['Value'])

    mix_base = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix_base.inputs[6].default_value = (*cor_escura, 1.0)
    mix_base.inputs[7].default_value = (*cor_base, 1.0)
    nt.links.new(faixa.outputs['Result'], mix_base.inputs[0])

    # Oclusão ambiente nas frestas e dobras
    ao = no(nt, 'ShaderNodeAmbientOcclusion', samples=12)
    ao.inputs['Distance'].default_value = 0.14
    suj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.92, 'From Max': 0.38, 'To Min': 0.0, 'To Max': 0.78})
    nt.links.new(ao.outputs['AO'], suj.inputs['Value'])

    mix_ao = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix_ao.inputs[7].default_value = (cor_escura[0] * 0.45, cor_escura[1] * 0.45, cor_escura[2] * 0.45, 1.0)
    nt.links.new(suj.outputs['Result'], mix_ao.inputs[0])
    nt.links.new(mix_base.outputs[2], mix_ao.inputs[6])
    cor_atual = mix_ao.outputs[2]

    # Musgo / umidade / líquen pela altura local ou normal superior
    if musgo_pe > 0.0:
        sep = no(nt, 'ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs[0])
        pe = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.45, 'To Min': musgo_pe, 'To Max': 0.0})
        nt.links.new(sep.outputs['Z'], pe.inputs['Value'])
        m_mul = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(pe.outputs['Result'], m_mul.inputs[0])
        nt.links.new(ru1.outputs['Fac'], m_mul.inputs[1])
        mix_m = no(nt, 'ShaderNodeMix', data_type='RGBA')
        mix_m.inputs[7].default_value = (*cor_musgo, 1.0)
        nt.links.new(m_mul.outputs['Value'], mix_m.inputs[0])
        nt.links.new(cor_atual, mix_m.inputs[6])
        cor_atual = mix_m.outputs[2]

    nt.links.new(cor_atual, bsdf.inputs['Base Color'])

    # Roughness variada (frestas mais foscas)
    r_map = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.2, 'From Max': 0.8,
                                            'To Min': max(0.08, rough - 0.14), 'To Max': min(1.0, rough + 0.10)})
    nt.links.new(ru2.outputs['Fac'], r_map.inputs['Value'])
    nt.links.new(r_map.outputs['Result'], bsdf.inputs['Roughness'])

    # Relevo procedural
    if bump_forca > 0.0:
        bump = no(nt, 'ShaderNodeBump', **{'Strength': bump_forca, 'Distance': 0.025})
        nt.links.new(soma_r.outputs['Value'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_folha(nome, cor_topo, cor_sombra, cor_borda, rough=0.78, escala=18.0):
    """Material opaco de folhagem alienígena/natural: variação entre topo iluminado, sombra nas reentrâncias,
    nervuras celulares e bordas queimadas/secas, sem transparência."""
    if nome in bpy.data.materials:
        return bpy.data.materials[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    m.diffuse_color = (*cor_topo, 1.0)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = rough
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.22
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    tc = no(nt, 'ShaderNodeTexCoord')
    geo = no(nt, 'ShaderNodeNewGeometry')
    sep_n = no(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sep_n.inputs[0])

    # Face voltada para cima mais clara; face inferior mais escura
    luz_z = no(nt, 'ShaderNodeMapRange', **{'From Min': -0.5, 'From Max': 0.85, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(sep_n.outputs['Z'], luz_z.inputs['Value'])

    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': escala, 'Detail': 6.0, 'Roughness': 0.6, 'Distortion': 0.35})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])

    mix1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix1.inputs[6].default_value = (*cor_sombra, 1.0)
    mix1.inputs[7].default_value = (*cor_topo, 1.0)
    nt.links.new(luz_z.outputs['Result'], mix1.inputs[0])

    # Variação de manchas/nervuras
    faixa = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.76, 'To Min': 0.0, 'To Max': 0.65})
    nt.links.new(ru.outputs['Fac'], faixa.inputs['Value'])
    mix2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix2.inputs[7].default_value = (*cor_borda, 1.0)
    nt.links.new(faixa.outputs['Result'], mix2.inputs[0])
    nt.links.new(mix1.outputs[2], mix2.inputs[6])

    # Oclusão ambiente interna da copa
    ao = no(nt, 'ShaderNodeAmbientOcclusion', samples=10)
    ao.inputs['Distance'].default_value = 0.22
    suj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.90, 'From Max': 0.35, 'To Min': 0.0, 'To Max': 0.55})
    nt.links.new(ao.outputs['AO'], suj.inputs['Value'])
    mix_ao = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix_ao.inputs[7].default_value = (cor_sombra[0] * 0.45, cor_sombra[1] * 0.45, cor_sombra[2] * 0.45, 1.0)
    nt.links.new(suj.outputs['Result'], mix_ao.inputs[0])
    nt.links.new(mix2.outputs[2], mix_ao.inputs[6])

    nt.links.new(mix_ao.outputs[2], bsdf.inputs['Base Color'])

    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.22, 'Distance': 0.015})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_emissivo_org(nome, cor_base, cor_emissao, forca=3.2, rough=0.22):
    """Cristal natural / lamelas bioluminescentes: superfície mineral ou carnuda com emissão interna."""
    if nome in bpy.data.materials:
        return bpy.data.materials[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    m.diffuse_color = (*cor_base, 1.0)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*cor_base, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Emission Color'].default_value = (*cor_emissao, 1.0)
    bsdf.inputs['Emission Strength'].default_value = forca
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    tc = no(nt, 'ShaderNodeTexCoord')
    ru = no(nt, 'ShaderNodeTexNoise', **{'Scale': 24.0, 'Detail': 5.0})
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.18, 'Distance': 0.01})
    nt.links.new(ru.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def mat_chao_planeta(bioma='campina'):
    """Chão orgânico que reproduz o visual de terreno.gdshader (mistura de camadas de terra, musgo, pedrisco e umidade)
    para a foto de 30 m de altura e fotos de conferência."""
    nome = f'EFEITO_Chao_{bioma}'
    if nome in bpy.data.materials:
        return bpy.data.materials[nome]
    paletas = {
        'campina': ((0.16, 0.25, 0.11), (0.10, 0.16, 0.07), (0.22, 0.18, 0.12)),
        'floresta_fungica': ((0.17, 0.11, 0.21), (0.10, 0.07, 0.13), (0.14, 0.20, 0.12)),
        'deserto_silex': ((0.48, 0.36, 0.20), (0.34, 0.25, 0.14), (0.26, 0.28, 0.32)),
        'planalto_rochoso': ((0.24, 0.23, 0.21), (0.15, 0.14, 0.13), (0.20, 0.22, 0.16)),
        'pantano': ((0.12, 0.15, 0.08), (0.07, 0.09, 0.05), (0.15, 0.12, 0.08)),
        'cinzal': ((0.16, 0.15, 0.15), (0.09, 0.08, 0.08), (0.22, 0.16, 0.12)),
        'misto': ((0.17, 0.24, 0.12), (0.22, 0.18, 0.13), (0.14, 0.17, 0.15)),
    }
    c1, c2, c3 = paletas.get(bioma, paletas['misto'])
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    no = mats.no
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.92
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.15
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    tc = no(nt, 'ShaderNodeTexCoord')
    ru_macro = no(nt, 'ShaderNodeTexNoise', **{'Scale': 0.18, 'Detail': 6.0, 'Roughness': 0.6, 'Distortion': 0.5})
    ru_medio = no(nt, 'ShaderNodeTexNoise', **{'Scale': 1.4, 'Detail': 8.0, 'Roughness': 0.65})
    ru_grao = no(nt, 'ShaderNodeTexNoise', **{'Scale': 14.0, 'Detail': 5.0})
    nt.links.new(tc.outputs['Object'], ru_macro.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], ru_medio.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], ru_grao.inputs['Vector'])

    f1 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.30, 'From Max': 0.70})
    nt.links.new(ru_macro.outputs['Fac'], f1.inputs['Value'])
    mix1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix1.inputs[6].default_value = (*c1, 1.0)
    mix1.inputs[7].default_value = (*c2, 1.0)
    nt.links.new(f1.outputs['Result'], mix1.inputs[0])

    f2 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.78, 'To Min': 0.0, 'To Max': 0.65})
    nt.links.new(ru_medio.outputs['Fac'], f2.inputs['Value'])
    mix2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    mix2.inputs[7].default_value = (*c3, 1.0)
    nt.links.new(f2.outputs['Result'], mix2.inputs[0])
    nt.links.new(mix1.outputs[2], mix2.inputs[6])

    # Grão fino de terra
    f3 = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 1.0, 'To Min': 0.78, 'To Max': 1.18})
    nt.links.new(ru_grao.outputs['Fac'], f3.inputs['Value'])
    mul = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    mul.inputs[0].default_value = 0.45
    nt.links.new(mix2.outputs[2], mul.inputs[6])
    nt.links.new(ru_grao.outputs['Color'], mul.inputs[7])

    nt.links.new(mul.outputs[2], bsdf.inputs['Base Color'])
    bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.28, 'Distance': 0.03})
    nt.links.new(ru_medio.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def registrar_materiais():
    """Preenche base3d.M com os materiais da paleta ambiental do jogo, todos com nós procedurais ricos."""
    base3d.M.update({
        # Troncos e caules
        'P_Tronco': mat_org('P_Tronco', (0.20, 0.12, 0.065), (0.09, 0.055, 0.03),
                            cor_musgo=(0.12, 0.19, 0.06), rough=0.90, escala=14.0, estria_z=0.28, musgo_pe=0.55, bump_forca=0.42),
        'P_TroncoClaro': mat_org('P_TroncoClaro', (0.64, 0.60, 0.54), (0.16, 0.14, 0.12),
                                 cor_musgo=(0.14, 0.20, 0.08), rough=0.84, escala=16.0, estria_z=3.2, musgo_pe=0.65, bump_forca=0.35),
        'P_FungoCaule': mat_org('P_FungoCaule', (0.34, 0.27, 0.38), (0.17, 0.12, 0.21),
                                cor_musgo=(0.18, 0.10, 0.26), rough=0.82, escala=12.0, estria_z=0.45, musgo_pe=0.50, bump_forca=0.32),
        'P_Cinza': mat_org('P_Cinza', (0.28, 0.26, 0.24), (0.12, 0.11, 0.10),
                           cor_musgo=(0.08, 0.07, 0.06), rough=0.92, escala=15.0, estria_z=0.35, musgo_pe=0.45, bump_forca=0.40),

        # Folhagens por perfil de estação (Materiais.gd)
        'P_FolhaCaduca': mat_folha('P_FolhaCaduca', (0.20, 0.36, 0.11), (0.09, 0.18, 0.05), (0.28, 0.32, 0.09)),
        'P_FolhaBetula': mat_folha('P_FolhaBetula', (0.30, 0.44, 0.14), (0.14, 0.24, 0.07), (0.42, 0.44, 0.12)),
        'P_FolhaPerene': mat_folha('P_FolhaPerene', (0.10, 0.23, 0.10), (0.05, 0.12, 0.05), (0.15, 0.26, 0.11)),
        'P_FolhaSalgueiro': mat_folha('P_FolhaSalgueiro', (0.22, 0.35, 0.13), (0.10, 0.18, 0.06), (0.28, 0.30, 0.10)),
        'P_FolhaSeca': mat_folha('P_FolhaSeca', (0.29, 0.33, 0.12), (0.16, 0.18, 0.06), (0.38, 0.30, 0.11)),
        'P_Folha': mat_folha('P_Folha', (0.18, 0.34, 0.11), (0.08, 0.17, 0.05), (0.24, 0.30, 0.09)),
        'P_FolhaClara': mat_folha('P_FolhaClara', (0.28, 0.44, 0.15), (0.13, 0.23, 0.07), (0.36, 0.42, 0.12)),
        'P_Lodo': mat_folha('P_Lodo', (0.16, 0.24, 0.09), (0.08, 0.12, 0.04), (0.20, 0.18, 0.07), rough=0.72),

        # Chapéus de fungos e plantas alienígenas
        'P_ChapeuCristal': mat_org('P_ChapeuCristal', (0.24, 0.14, 0.36), (0.11, 0.06, 0.19),
                                   cor_musgo=(0.16, 0.32, 0.38), rough=0.68, escala=14.0, estria_z=1.2, musgo_pe=0.35, bump_forca=0.36),
        'P_Chapeu': mat_org('P_Chapeu', (0.32, 0.15, 0.34), (0.15, 0.06, 0.18),
                            cor_musgo=(0.44, 0.24, 0.42), rough=0.74, escala=13.0, estria_z=1.0, musgo_pe=0.30, bump_forca=0.38),
        'P_Malaquita': mat_org('P_Malaquita', (0.12, 0.38, 0.26), (0.05, 0.18, 0.12),
                               cor_musgo=(0.24, 0.46, 0.32), rough=0.62, escala=16.0, estria_z=0.5, musgo_pe=0.35, bump_forca=0.35, metal=0.15),

        # Emissivos naturais (cristais e biomassa)
        'P_Cristal': mat_emissivo_org('P_Cristal', (0.22, 0.78, 0.86), (0.28, 0.88, 0.96), forca=3.6, rough=0.18),
        'P_Biomassa': mat_emissivo_org('P_Biomassa', (0.42, 0.76, 0.18), (0.48, 0.88, 0.22), forca=2.6, rough=0.35),

        # Rochas e minérios
        'P_Rocha': mat_org('P_Rocha', (0.32, 0.30, 0.27), (0.17, 0.16, 0.14),
                           cor_musgo=(0.16, 0.20, 0.11), rough=0.88, escala=11.0, estria_z=2.2, musgo_pe=0.35, bump_forca=0.42),
        'P_RochaEscura': mat_org('P_RochaEscura', (0.18, 0.17, 0.16), (0.08, 0.08, 0.075),
                                 cor_musgo=(0.11, 0.15, 0.08), rough=0.90, escala=13.0, estria_z=2.0, musgo_pe=0.40, bump_forca=0.44),
        'P_Pedra': mat_org('P_Pedra', (0.52, 0.49, 0.43), (0.30, 0.28, 0.24),
                           cor_musgo=(0.22, 0.21, 0.17), rough=0.86, escala=14.0, estria_z=1.8, musgo_pe=0.25, bump_forca=0.38),
        'P_Ferrugem': mat_org('P_Ferrugem', (0.54, 0.20, 0.11), (0.26, 0.08, 0.04),
                              cor_musgo=(0.68, 0.28, 0.14), rough=0.72, escala=16.0, estria_z=1.0, musgo_pe=0.20, bump_forca=0.40, metal=0.25),
        'P_Cobre': mat_org('P_Cobre', (0.76, 0.38, 0.14), (0.38, 0.18, 0.06),
                           cor_musgo=(0.16, 0.44, 0.28), rough=0.55, escala=18.0, estria_z=1.0, musgo_pe=0.35, bump_forca=0.32, metal=0.45),
        'P_Carvao': mat_org('P_Carvao', (0.055, 0.055, 0.062), (0.018, 0.018, 0.022),
                            cor_musgo=(0.09, 0.09, 0.10), rough=0.42, escala=20.0, estria_z=1.5, musgo_pe=0.15, bump_forca=0.36, spec=0.55),
        'P_Silex': mat_org('P_Silex', (0.34, 0.45, 0.64), (0.16, 0.22, 0.34),
                           cor_musgo=(0.48, 0.58, 0.74), rough=0.48, escala=16.0, estria_z=1.2, musgo_pe=0.20, bump_forca=0.34, spec=0.50),
        'P_Areia': mat_org('P_Areia', (0.76, 0.62, 0.30), (0.52, 0.40, 0.18),
                           cor_musgo=(0.84, 0.70, 0.38), rough=0.92, escala=24.0, estria_z=2.5, musgo_pe=0.20, bump_forca=0.28),
    })


def limpar_cena(semente=42):
    return iniciar_cena(semente=semente)


# ================================================================== CONSTRUTOR DE MODELO DE MALHA ÚNICA
class ConstrutorMalha:
    """Acumula geometria de múltiplos materiais num único BMesh fechado, garantindo faces voltadas para fora,
    origem na base central (z=0) e contagem rígida de triângulos."""
    def __init__(self, nome_ou_mats='modelo'):
        if isinstance(nome_ou_mats, (list, tuple)):
            self.nome = 'modelo'
            self.paleta = list(nome_ou_mats)
        else:
            self.nome = str(nome_ou_mats)
            self.paleta = []
        self.bm = bmesh.new()
        self.mats = []
        self._mapa_mat = {}

    def _resolver_mat(self, mat):
        if isinstance(mat, int):
            return self.paleta[mat]
        return mat

    def mi(self, nome_mat):
        nome_mat = self._resolver_mat(nome_mat)
        if nome_mat not in self._mapa_mat:
            self._mapa_mat[nome_mat] = len(self.mats)
            self.mats.append(base3d.M[nome_mat])
        return self._mapa_mat[nome_mat]

    def face(self, verts, nome_mat):
        try:
            f = self.bm.faces.new(verts)
            f.material_index = self.mi(nome_mat)
            return f
        except ValueError:
            return None

    def anel_tubo(self, aneis, mat, fechar_base=True, fechar_topo=True, suave=True):
        """Liga uma lista de anéis (cada anel é uma lista de Vector com o mesmo número de pontos) em faces quad/tri."""
        idx_m = self.mi(mat)
        vs = [[self.bm.verts.new(p) for p in anel] for anel in aneis]
        n = len(vs[0])
        for i in range(len(vs) - 1):
            A, B = vs[i], vs[i + 1]
            if len(B) == 1:
                for k in range(n):
                    f = self.bm.faces.new((A[k], A[(k + 1) % n], B[0]))
                    f.material_index = idx_m
                    f.smooth = suave
            else:
                for k in range(n):
                    f = self.bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))
                    f.material_index = idx_m
                    f.smooth = suave
        if fechar_base and len(vs[0]) >= 3:
            f = self.bm.faces.new(list(reversed(vs[0])))
            f.material_index = idx_m
            f.smooth = False
        if fechar_topo and len(vs[-1]) >= 3:
            f = self.bm.faces.new(vs[-1])
            f.material_index = idx_m
            f.smooth = False
        return vs

    def ramo(self, pts, raios, mat, lados=6, sapopemba=0.0, torcao=0.0, fechar_topo=True, fechar_base=True, fase0=0.0):
        """Cria um tronco ou galho orgânico varrido pelos pontos `pts` com raios `raios`.
        `sapopemba` alarga a base em raízes tabulares sinuosas."""
        pts = [Vector(p) for p in pts]
        m = len(pts)
        tans = [(pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(m)]
        e1 = Z.cross(tans[0])
        if e1.length < 1e-4:
            e1 = Vector((1, 0, 0))
        e1.normalize()
        aneis = []
        for i in range(m):
            t = tans[i]
            e1 = (e1 - t * e1.dot(t)).normalized()
            e2 = t.cross(e1).normalized()
            r = raios[i]
            u = i / max(1, m - 1)
            anel = []
            for k in range(lados):
                a = fase0 + 2 * PI * k / lados + u * torcao
                mod_r = 1.0
                if sapopemba > 0.0 and i == 0:
                    mod_r += sapopemba * max(0.0, math.cos(3 * a + fase0))
                elif sapopemba > 0.0 and i == 1:
                    mod_r += sapopemba * 0.35 * max(0.0, math.cos(3 * a + fase0))
                d = e1 * math.cos(a) + e2 * math.sin(a)
                anel.append(pts[i] + d * (r * mod_r))
            aneis.append(anel)
        return self.anel_tubo(aneis, mat, fechar_base=fechar_base, fechar_topo=fechar_topo, suave=True)

    def tubo_curvo(self, pts, raios, lados=6, mat=0, tampar_base=True, tampar_topo=True, sapopemba=0.0, torcao=0.0):
        return self.ramo(pts, raios, mat, lados=lados, sapopemba=sapopemba, torcao=torcao,
                         fechar_base=tampar_base, fechar_topo=tampar_topo)

    def fronde_copa(self, centro, raio_xy, espessura_z, mat, lados=7, pontas=0.22, queda_borda=0.06,
                    assimetria=(1.0, 1.0), rot_z=0.0, semente=1):
        """Volume fechado de folhagem recortada em gomos/pontas (sem transparência, nunca esférico/chibi).
        Tem cume facetado superior, borda recortada em zigue-zague (folhas salientes) e base chanfrada escura."""
        rnd = random.Random(semente)
        centro = Vector(centro)
        rz = Matrix.Rotation(rot_z, 3, 'Z')
        n = lados * 2  # alterna ponta de folha e reentrância
        anel_borda = []
        anel_meio = []
        for k in range(n):
            a = 2 * PI * k / n
            eh_ponta = (k % 2 == 0)
            f_r = (1.0 + pontas * rnd.uniform(0.75, 1.25)) if eh_ponta else (1.0 - pontas * 0.55 * rnd.uniform(0.8, 1.2))
            rx = raio_xy * assimetria[0] * f_r
            ry = raio_xy * assimetria[1] * f_r
            dz = -queda_borda * (1.25 if eh_ponta else 0.35) + rnd.uniform(-0.015, 0.015)
            p_b = Vector((math.cos(a) * rx, math.sin(a) * ry, dz))
            p_m = Vector((math.cos(a) * rx * 0.62, math.sin(a) * ry * 0.62, espessura_z * 0.48 + rnd.uniform(-0.01, 0.015)))
            anel_borda.append(centro + rz @ p_b)
            anel_meio.append(centro + rz @ p_m)
        p_topo = centro + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), espessura_z * 0.72))
        p_base = centro + Vector((0, 0, -espessura_z * 0.36))

        idx_m = self.mi(mat)
        v_base = self.bm.verts.new(p_base)
        v_borda = [self.bm.verts.new(p) for p in anel_borda]
        v_meio = [self.bm.verts.new(p) for p in anel_meio]
        v_topo = self.bm.verts.new(p_topo)

        for k in range(n):
            kn = (k + 1) % n
            f1 = self.bm.faces.new((v_borda[kn], v_borda[k], v_base))
            f1.material_index = idx_m
            f1.smooth = False
            f2 = self.bm.faces.new((v_borda[k], v_borda[kn], v_meio[kn], v_meio[k]))
            f2.material_index = idx_m
            f2.smooth = False
            f3 = self.bm.faces.new((v_meio[k], v_meio[kn], v_topo))
            f3.material_index = idx_m
            f3.smooth = False

    def tufo_folha(self, centro, raios_xyz, mat=0, semente=1, gomos=6, aneis=3):
        rx, ry, rz = raios_xyz
        r_med = (rx + ry) * 0.5
        assim = (rx / max(1e-4, r_med), ry / max(1e-4, r_med))
        self.fronde_copa(centro, r_med * 1.15, rz * 1.45, mat, lados=max(4, gomos // 2 + 2),
                         pontas=0.22, queda_borda=rz * 0.22, assimetria=assim, rot_z=semente * 0.37, semente=semente)

    def chapeu_cogumelo(self, centro, r_base=0.35, altura=0.25, espessura_borda=0.04,
                        lados=8, mat_topo=0, mat_baixo=1, semente=1):
        rnd = random.Random(semente)
        centro = Vector(centro)
        fase = rnd.uniform(0, 2 * PI)
        perfis = [
            (0.24, -espessura_borda * 0.6, mat_baixo),
            (0.76, -espessura_borda * 0.9, mat_baixo),
            (1.00, 0.0, mat_topo),
            (0.78, altura * 0.48, mat_topo),
            (0.38, altura * 0.84, mat_topo),
        ]
        aneis = []
        for rr, dz, _ in perfis:
            anel = []
            for k in range(lados):
                a = 2 * PI * k / lados
                onda = 1.0 + 0.08 * math.sin(3 * a + fase) + 0.05 * math.cos(5 * a - fase)
                r = r_base * rr * onda
                anel.append(centro + Vector((math.cos(a) * r, math.sin(a) * r, dz)))
            aneis.append(anel)
        p_apice = centro + Vector((0, 0, altura))
        aneis.append([p_apice])

        vs = [[self.bm.verts.new(p) for p in anel] for anel in aneis]
        for i in range(len(vs) - 1):
            idx_m = self.mi(perfis[min(i, len(perfis) - 1)][2])
            A, B = vs[i], vs[i + 1]
            if len(B) == 1:
                for k in range(lados):
                    f = self.bm.faces.new((A[k], A[(k + 1) % lados], B[0]))
                    f.material_index = idx_m
                    f.smooth = True
            else:
                for k in range(lados):
                    f = self.bm.faces.new((A[k], A[(k + 1) % lados], B[(k + 1) % lados], B[k]))
                    f.material_index = idx_m
                    f.smooth = True
        f_base = self.bm.faces.new(list(reversed(vs[0])))
        f_base.material_index = self.mi(mat_baixo)

    def lamina_folha(self, origem, dir_ou_fim, compr=None, larg=0.08, esp=0.03, mat=0, arco=-0.12,
                     larg_max=None, espessura=None):
        """Folha/ramo pendente ou folha larga recortada com espessura real (volume prismático fechado de seção triangular)."""
        origem = Vector(origem)
        if compr is None or larg_max is not None:
            # Assinatura por ponto inicial e final: (p_ini, p_fim, larg_max=..., espessura=..., arco=..., mat=...)
            p_fim = Vector(dir_ou_fim)
            delta = p_fim - origem
            compr = max(0.02, delta.length)
            u = delta.normalized()
            larg = larg_max if larg_max is not None else larg
            esp = espessura if espessura is not None else esp
        else:
            u = Vector(dir_ou_fim).normalized()

        lado = u.cross(Z)
        if lado.length < 1e-4:
            lado = Vector((1, 0, 0))
        lado.normalize()
        up = lado.cross(u).normalized()

        aneis = []
        for t, fl, fe in ((0.0, 0.50, 0.85), (0.55, 1.0, 1.0)):
            c = origem + u * (compr * t) + up * (arco * compr * (t ** 1.6))
            w = larg * 0.5 * fl
            h = esp * 0.5 * fe
            aneis.append([
                c - lado * w,
                c + up * h,
                c + lado * w,
            ])
        ponta = origem + u * compr + up * (arco * compr)
        aneis.append([ponta])
        self.anel_tubo(aneis, mat, fechar_base=True, fechar_topo=False, suave=False)

    def cristal_prisma(self, base_pt, eixo_dir, r_base, compr, mat='P_Cristal', lados=5):
        """Prisma cristalino facetado com ponta piramidal assimétrica."""
        base_pt = Vector(base_pt)
        u = Vector(eixo_dir).normalized()
        s = u.cross(Z)
        if s.length < 1e-4:
            s = Vector((1, 0, 0))
        s.normalize()
        v = s.cross(u).normalized()
        a0 = 0.37
        anel0 = []
        anel1 = []
        for k in range(lados):
            a = a0 + 2 * PI * k / lados
            d = s * math.cos(a) + v * math.sin(a)
            anel0.append(base_pt + d * r_base)
            anel1.append(base_pt + u * (compr * 0.72) + d * (r_base * 0.78))
        ponta = base_pt + u * compr
        self.anel_tubo([anel0, anel1, [ponta]], mat, fechar_base=True, fechar_topo=False, suave=False)

    def cristal_facetado(self, pos, direcao, comp=0.15, r_base=0.04, lados=5, mat=0):
        self.cristal_prisma(pos, direcao, r_base, comp, mat=mat, lados=lados)

    def rocha_estrato(self, centro, rx, ry, h, mat, lados=7, degraus=2, inclinacao=(0.05, -0.03), semente=1, fundo=-0.02):
        """Bloco rochoso geológico com estratos/patamares e faces chanfradas angulosas (sem parecer batata lisa)."""
        rnd = random.Random(semente)
        centro = Vector(centro)
        aneis = []
        n_aneis = degraus + 2
        for i in range(n_aneis):
            u = i / (n_aneis - 1)
            z = fundo if i == 0 else h * (u ** 0.88)
            f_r = 1.0 - 0.52 * (u ** 1.35)
            ox = inclinacao[0] * z
            oy = inclinacao[1] * z
            anel = []
            for k in range(lados):
                a = 2 * PI * k / lados + rnd.uniform(-0.14, 0.14)
                q = rnd.uniform(0.82, 1.18)
                anel.append(Vector((
                    centro.x + ox + math.cos(a) * rx * f_r * q,
                    centro.y + oy + math.sin(a) * ry * f_r * q,
                    centro.z + z + (0.0 if i == 0 else rnd.uniform(-0.02, 0.02) * h)
                )))
            aneis.append(anel)
        p_topo = Vector((centro.x + inclinacao[0] * h, centro.y + inclinacao[1] * h, centro.z + h))
        aneis.append([p_topo])
        self.anel_tubo(aneis, mat, fechar_base=True, fechar_topo=False, suave=False)

    def rocha_organica(self, centro, raios_xyz, mat=0, semente=1, gomos=6, aneis=2, achatar_base=True):
        rx, ry, rz = raios_xyz
        c = Vector(centro)
        z0 = (c.z - rz * 0.85) if not achatar_base else max(0.0, c.z - rz * 0.90)
        self.rocha_estrato(Vector((c.x, c.y, z0)), rx, ry, rz * 1.65, mat,
                           lados=max(5, gomos), degraus=max(1, aneis - 1), semente=semente, fundo=0.0)

    def finalizar(self, nome_ou_pos=None, pos=(0, 0, 0), apoiar_z=True, raio_max_xy=None, lim_rect_xy=None,
                  escala_xy=None, escala_z=None):
        """Recalcula normais para fora, garante base em z=0, respeita o limite da área e cria o objeto MESH."""
        if isinstance(nome_ou_pos, str):
            self.nome = nome_ou_pos
        elif nome_ou_pos is not None:
            pos = nome_ou_pos

        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        if apoiar_z and self.bm.verts:
            z_min = min(v.co.z for v in self.bm.verts)
            for v in self.bm.verts:
                v.co.z -= z_min
        if escala_z is not None and self.bm.verts:
            z_max = max(v.co.z for v in self.bm.verts)
            if z_max > 1e-4:
                fz = escala_z / z_max
                for v in self.bm.verts:
                    v.co.z *= fz
        if escala_xy is not None and self.bm.verts:
            dx = max(v.co.x for v in self.bm.verts) - min(v.co.x for v in self.bm.verts)
            dy = max(v.co.y for v in self.bm.verts) - min(v.co.y for v in self.bm.verts)
            d_atual = max(dx, dy)
            if d_atual > 1e-4:
                fxy = escala_xy / d_atual
                for v in self.bm.verts:
                    v.co.x *= fxy
                    v.co.y *= fxy
        if raio_max_xy is not None and self.bm.verts:
            r_atual = max(math.hypot(v.co.x, v.co.y) for v in self.bm.verts)
            if r_atual > raio_max_xy:
                f = raio_max_xy / r_atual
                for v in self.bm.verts:
                    v.co.x *= f
                    v.co.y *= f
        if lim_rect_xy is not None and self.bm.verts:
            lx, ly = lim_rect_xy
            for v in self.bm.verts:
                v.co.x = max(-lx, min(lx, v.co.x))
                v.co.y = max(-ly, min(ly, v.co.y))

        me = bpy.data.meshes.new(self.nome)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        me.calc_loop_triangles()

        o = bpy.data.objects.new(self.nome, me)
        bpy.context.scene.collection.objects.link(o)
        o.location = Vector(pos)
        return o


def info_modelo(o):
    o.data.calc_loop_triangles()
    tris = len(o.data.loop_triangles)
    vs = [v.co for v in o.data.vertices]
    dims = [round(max(v[k] for v in vs) - min(v[k] for v in vs), 3) for k in range(3)]
    return tris, dims


# ================================================================== CENA, CÂMERA E FOTOS (INCLUINDO 30 M)
def configurar_render(sc):
    sol = bpy.data.lights.new('EFEITO_Sol', 'SUN')
    sol.energy = 4.2
    sol.angle = math.radians(2.2)
    so = bpy.data.objects.new('EFEITO_Sol', sol)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(48), 0, math.radians(-35))

    mundo = bpy.data.worlds.new('Mundo')
    sc.world = mundo
    bg = mundo.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.50, 0.58, 0.70, 1)
    bg.inputs['Strength'].default_value = 0.65

    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.transparent_max_bounces = 2
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -0.35

    cam_d = bpy.data.cameras.new('EFEITO_Cam')
    cam = bpy.data.objects.new('EFEITO_Cam', cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam, cam_d


def mirar(cam, cam_d, pos, alvo, fov_graus=38.0):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(alvo) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens_unit = 'FOV'
    cam_d.angle = math.radians(fov_graus)


def altura_relevo(x, y, cx, cy, cz=0.0, relevo=0.14):
    if relevo <= 0.0:
        return cz
    dist_c = math.hypot(x - cx, y - cy)
    atenuar = min(1.0, (dist_c / 5.0) ** 2)
    return cz + atenuar * relevo * (
        math.sin(x * 0.28 + 0.7) * math.cos(y * 0.24 - 0.4) * 0.6 +
        math.sin(x * 0.65 - y * 0.52) * 0.4
    )


def criar_chao_bioma(nome_obj, centro, tam_xy, bioma='misto', relevo=0.14, semente=77):
    """Cria uma malha de terreno subdividida com ondulação natural (igual ao micro-relevo do DesenhoChunk)."""
    bm = bmesh.new()
    nx = ny = 42
    wx, wy = tam_xy
    cx, cy, cz = centro
    grade = []
    for j in range(ny + 1):
        linha = []
        for i in range(nx + 1):
            x = cx + (i / nx - 0.5) * wx
            y = cy + (j / ny - 0.5) * wy
            h = altura_relevo(x, y, cx, cy, cz, relevo)
            linha.append(bm.verts.new((x, y, h)))
        grade.append(linha)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grade[j][i], grade[j][i + 1], grade[j + 1][i + 1], grade[j + 1][i]))
            f.smooth = True
    me = bpy.data.meshes.new(nome_obj)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat_chao_planeta(bioma))
    o = bpy.data.objects.new(nome_obj, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def renderizar_estudo(sc, objetos_modelos, prefixo_arq, limite_tris, bioma_chao='misto',
                      vistas_vitrine=None, espalhar_raio=(15.0, 11.0), n_espalhados=65,
                      escala_espalhados=(0.88, 1.15), dist_min=1.35):
    """Valida todos os modelos contra `limite_tris`, trata o modo `-- nada [nome]` e renderiza as fotos de vitrine
    + a foto obrigatória de 30 m de altura com variantes espalhadas no chão do planeta."""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['foto']
    modo = argv[0] if argv else 'foto'
    alvo_unico = argv[1] if len(argv) > 1 else None

    # 1. Validação estrita de triângulos e dimensões
    relatorio = []
    for o in objetos_modelos:
        t, dims = info_modelo(o)
        assert t <= limite_tris, f"ERRO: {o.name} tem {t} tris (limite {limite_tris})!"
        relatorio.append((o.name, t, dims))

    if modo != 'foto':
        if alvo_unico:
            for o in list(objetos_modelos):
                if o.name == alvo_unico:
                    o.location = Vector((0, 0, 0))
                else:
                    bpy.data.objects.remove(o, do_unlink=True)
        for nome_m, t, dims in relatorio:
            if not alvo_unico or nome_m == alvo_unico:
                print(f"MODELO_OK {nome_m:24s} | tris={t:4d}/{limite_tris} | dims={dims}")
        return relatorio

    for nome_m, t, dims in relatorio:
        print(f"MODELO_OK {nome_m:24s} | tris={t:4d}/{limite_tris} | dims={dims}")

    cam, cam_d = configurar_render(sc)
    sc.cycles.samples = 20

    # Chão na área de vitrine (em torno da origem)
    chao_vit = criar_chao_bioma('EFEITO_chao_vitrine', (0, 0, 0), (60.0, 60.0), bioma=bioma_chao, relevo=0.0)

    if vistas_vitrine is None:
        vistas_vitrine = [
            (f'{prefixo_arq}_0.png', (0, -9.5, 6.2), (0, 0, 0.8), 38.0, 1400, 1000),
            (f'{prefixo_arq}_1.png', (8.5, 7.5, 5.8), (0, 0, 0.8), 38.0, 1400, 1000),
            (f'{prefixo_arq}_perto.png', (3.2, -3.6, 2.2), (0, 0, 0.7), 35.0, 1400, 1000),
        ]

    for arq, pos_c, alvo_c, fov, rx, ry in vistas_vitrine:
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        mirar(cam, cam_d, pos_c, alvo_c, fov)
        sc.render.filepath = os.path.join(AQUI, arq)
        bpy.ops.render.render(write_still=True)

    # 2. Foto obrigatória a 30 m de altura com variantes espalhadas sobre chão parecido com o do jogo
    # Montamos o campo espalhado centrado em (120, 0, 0) para não interferir com a vitrine
    cx_campo, cy_campo = 120.0, 0.0
    relevo_30m = 0.12
    criar_chao_bioma('EFEITO_chao_30m', (cx_campo, cy_campo, 0.0), (75.0, 75.0), bioma=bioma_chao, relevo=relevo_30m, semente=303)

    rnd = random.Random(303)
    ocupados = []
    instancias_30m = []
    rx_e, ry_e = espalhar_raio
    # Garante que todos os modelos do grupo apareçam várias vezes no campo de 30 m
    for idx in range(n_espalhados):
        molde = objetos_modelos[idx % len(objetos_modelos)]
        for _tent in range(40):
            px = cx_campo + rnd.uniform(-rx_e, rx_e)
            py = cy_campo + rnd.uniform(-ry_e, ry_e)
            if all(math.hypot(px - ox, py - oy) >= dist_min for ox, oy in ocupados):
                ocupados.append((px, py))
                break
        inst = bpy.data.objects.new(f'EFEITO_inst_{idx}', molde.data)
        sc.collection.objects.link(inst)
        esc = rnd.uniform(*escala_espalhados)
        pz = altura_relevo(px, py, cx_campo, cy_campo, 0.0, relevo_30m)
        inst.location = Vector((px, py, pz))
        inst.rotation_euler = (0, 0, rnd.uniform(0, 2 * PI))
        inst.scale = (esc, esc, esc)
        instancias_30m.append(inst)

    # Câmera a 30 m de altura exata sobre o campo, com inclinação da CameraJogo (~64° acima do horizonte, FOV 38°)
    # z = 30.0 m; com inclinação de 64°, distância horizontal = 30 / tan(64°) ≈ 14.63 m
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1100
    mirar(cam, cam_d, (cx_campo + 5.5, cy_campo - 13.6, 30.0), (cx_campo, cy_campo, 0.0), 38.0)
    sc.render.filepath = os.path.join(AQUI, f'{prefixo_arq}_30m.png')
    bpy.ops.render.render(write_still=True)

    return relatorio
