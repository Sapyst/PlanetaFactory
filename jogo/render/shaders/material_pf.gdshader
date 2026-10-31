// Material único do jogo (low-poly facetado). Um só shader → menos trocas de estado na GPU.
// Estruturas trazem uma textura assada (pintura gasta, ferrugem, sujeira: arte/blender_scripts/texturizar.py) no UV;
// o resto da paleta (itens, mapa) continua cor lisa.
// Efeitos ligados por uniform (por material compartilhado, não por objeto):
//   vento   : balança a vegetação (proporcional à altura do vértice), inclinando para onde o vento sopra; mais com
//             vento forte e quando a rajada passa (vento_dir e rajada globais, clima.gdshaderinc)
//   rolagem : lona da esteira andando (UV.y = distância percorrida)
//   pulso   : brilho pulsando (cristais, luzes de status)
//   boiar   : sobe e desce na água (vitória-régia)
//   perfil_folha : folhagem das árvores por receita — cor e queda pela estação (estacao_atual), cada árvore no seu
//             tempo (sorte por instância + onda pelo mapa); copa some com o fogo antes do tronco
//   carbonizada : árvore queimada (de pé ou caída): tudo carvão, sem folha
//   por_trabalho : cristal das construções — brilho fraco que acende com `trabalho` (por objeto: o Animador manda).
//             Só na variante material_pf_cristal.gdshader: todo objeto cujo shader tem `instance uniform` reserva 16 vec4
//             do buffer global (65.536 vec4 = ~4.090 objetos), mesmo sem usar; com todo o jogo neste shader, a fábrica
//             grande estourava ("Too many instances using shader instance variables").
// Encardido (estruturas texturizadas): canal R do fogo_mapa = quanto a estrutura daquele tile já sujou (0 limpa .. 1
// imunda; AmbienteVivo.encardido: cresce com o tempo e com o trabalho, a chuva lava). Começa pelo pé e pelas frestas,
// escorre pelas laterais e assenta pó em cima; quanto mais encardida, mais cobre e mais escurece e fica fosca.
shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_schlick_ggx;

#include "res://render/shaders/material_pf.gdshaderinc"
