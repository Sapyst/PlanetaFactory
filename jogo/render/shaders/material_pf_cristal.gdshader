// Variante de material_pf.gdshader para o cristal das construções (P_Cristal): a única com `instance uniform trabalho`.
shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_schlick_ggx;

#define TRABALHO_POR_OBJETO
#include "res://render/shaders/material_pf.gdshaderinc"
