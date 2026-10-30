"""Materiais físicos procedurais dos estudos (pintura gasta, sujeira nas frestas, aço com ferrugem, cromado, cobre)."""
import bpy


def no(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def material(nome, base, metal, rough, pintura=True, ferrugem=0.0, sujeira=0.6, desgaste=0.6, escovado=False):
    """Pintura (ou metal) com: quinas gastas mostrando metal, sujeira nas frestas, variação de brilho e ferrugem."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = no(nt, 'ShaderNodeOutputMaterial')
    bsdf = no(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    coord = no(nt, 'ShaderNodeTexCoord')
    # ruídos: manchas grandes (sujeira/ferrugem), fino (brilho), riscos (escovado)
    grande = no(nt, 'ShaderNodeTexNoise', **{'Scale': 9.0, 'Detail': 8.0, 'Roughness': 0.6})
    fino = no(nt, 'ShaderNodeTexNoise', **{'Scale': 90.0, 'Detail': 4.0})
    nt.links.new(coord.outputs['Object'], grande.inputs['Vector'])
    nt.links.new(coord.outputs['Object'], fino.inputs['Vector'])
    # quinas: diferença entre a normal real e a normal arredondada (bevel)
    bev = no(nt, 'ShaderNodeBevel', samples=8)
    bev.inputs['Radius'].default_value = 0.006
    geo = no(nt, 'ShaderNodeNewGeometry')
    dot = no(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    nt.links.new(bev.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Normal'], dot.inputs[1])
    quina = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.995, 'From Max': 0.9, 'To Min': 0.0, 'To Max': 1.0})
    nt.links.new(dot.outputs['Value'], quina.inputs['Value'])
    gasta = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
    nt.links.new(quina.outputs['Result'], gasta.inputs[0])
    gasta.inputs[1].default_value = desgaste * 1.7
    lasca = no(nt, 'ShaderNodeMath', operation='MULTIPLY')            # lascas: quina × ruído
    nt.links.new(gasta.outputs['Value'], lasca.inputs[0])
    nt.links.new(grande.outputs['Fac'], lasca.inputs[1])
    lasca_c = no(nt, 'ShaderNodeMath', operation='GREATER_THAN')
    nt.links.new(lasca.outputs['Value'], lasca_c.inputs[0])
    lasca_c.inputs[1].default_value = 0.33
    # sujeira nas frestas (oclusão ambiente)
    ao = no(nt, 'ShaderNodeAmbientOcclusion', samples=16)
    ao.inputs['Distance'].default_value = 0.08
    suj = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.92, 'From Max': 0.35, 'To Min': 0.0, 'To Max': min(1.0, sujeira * 1.3)})
    nt.links.new(ao.outputs['AO'], suj.inputs['Value'])
    # cor: base → (lasca) metal nu → (sujeira) marrom-escuro; ferrugem nas manchas
    metal_nu = (0.52, 0.52, 0.5, 1)
    c1 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c1.inputs[6].default_value = (*base, 1)
    c1.inputs[7].default_value = metal_nu
    nt.links.new(lasca_c.outputs['Value'], c1.inputs[0])
    var = no(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    var.inputs[0].default_value = 0.4
    nt.links.new(c1.outputs[2], var.inputs[6])
    nt.links.new(grande.outputs['Color'], var.inputs[7])
    c2 = no(nt, 'ShaderNodeMix', data_type='RGBA')
    c2.inputs[7].default_value = (0.06, 0.045, 0.03, 1)
    nt.links.new(suj.outputs['Result'], c2.inputs[0])
    nt.links.new(var.outputs[2], c2.inputs[6])
    cor_final = c2.outputs[2]
    if ferrugem > 0:
        fr = no(nt, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.68, 'To Min': 0.0, 'To Max': ferrugem})
        nt.links.new(grande.outputs['Fac'], fr.inputs['Value'])
        c3 = no(nt, 'ShaderNodeMix', data_type='RGBA')
        c3.inputs[7].default_value = (0.32, 0.12, 0.04, 1)
        nt.links.new(fr.outputs['Result'], c3.inputs[0])
        nt.links.new(cor_final, c3.inputs[6])
        cor_final = c3.outputs[2]
    nt.links.new(cor_final, bsdf.inputs['Base Color'])
    # metálico: pintura não é metal, a lasca é
    if pintura:
        mt = no(nt, 'ShaderNodeMath', operation='MULTIPLY')
        nt.links.new(lasca_c.outputs['Value'], mt.inputs[0])
        mt.inputs[1].default_value = 0.9
        nt.links.new(mt.outputs['Value'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Metallic'].default_value = metal
    # brilho: base ± ruído fino; sujeira deixa fosco; escovado: riscos alongados
    r = no(nt, 'ShaderNodeMapRange', **{'To Min': rough * 0.75, 'To Max': rough * 1.25})
    nt.links.new(fino.outputs['Fac'], r.inputs['Value'])
    rs = no(nt, 'ShaderNodeMath', operation='ADD')
    nt.links.new(r.outputs['Result'], rs.inputs[0])
    nt.links.new(suj.outputs['Result'], rs.inputs[1])
    nt.links.new(rs.outputs['Value'], bsdf.inputs['Roughness'])
    if escovado:
        wave = no(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z')
        wave.inputs['Scale'].default_value = 60.0
        wave.inputs['Distortion'].default_value = 8.0
        nt.links.new(coord.outputs['Object'], wave.inputs['Vector'])
        bump = no(nt, 'ShaderNodeBump', **{'Strength': 0.05})
        nt.links.new(wave.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


