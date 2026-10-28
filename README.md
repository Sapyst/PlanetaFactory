# PlanetaFactory (nome provisório)

Jogo de automação/fábrica para PC e celular: plano infinito procedural em grade 1×1, esteiras (inclusive elevadas),
braços mecânicos, logística de transporte e inimigos. Tema: planeta vivo — a fábrica drena o planeta e o
"sistema imunológico" dele reage.

## Pastas
- `jogo/` — projeto Godot 4.7 (código, dados, testes). Ver `jogo/README.md`.
- `arte/` — modelos 3D, texturas e o verificador. Ver `arte/FICHA_DE_ESTILO.md` e `arte/CATALOGO.md`.
- `docs/RECURSOS.md` — **guia dos recursos**: cada jazida (cor, item, máquina, em que bioma aparece), biomas, águas e o que
  cada elemento natural rende. Gerado dos dados por `jogo/ferramentas/gerar_doc_recursos.py`.
- `docs/MUNDO.md` — geração procedural e distribuição por bioma. `docs/fotos/` — capturas reais do jogo.

## Fluxo de trabalho (sem precisar abrir nada)
1. `arte/blender_scripts/gerar_tudo.sh` — regenera os 95 modelos + texturas, checa cada um, gera pranchas e catálogo, copia para o jogo.
2. `jogo/ferramentas/testar.sh` — importa e roda todos os testes do jogo sem janela.
3. `godot --path jogo --write-movie /tmp/q.png --fixed-fps 30 --quit-after 70 -- camera X Z DIST` — foto real.
4. `python3 jogo/ferramentas/gerar_sons.py` — sintetiza os sons; `python3 jogo/ferramentas/gerar_nuvens.py` — mapa das nuvens.
5. `godot --headless --path jogo --export-debug "Android" jogo/export/PlanetaFactory-0.3.2.apk` — APK.
6. `... -- camera -3 2 11 roteiro construir` (ou `roteiro toque`) — teste visual da construção com cliques/toques injetados.
7. `python3 jogo/ferramentas/gerar_doc_recursos.py` — atualiza `docs/RECURSOS.md`.
8. `... -- camera 8 -1 44 clima chuva` — foto com clima forçado (limpo, nublado, neblina, chuva, tempestade).

## Visual e clima
- Estruturas e assets naturais com textura assada (`arte/blender_scripts/texturizar.py`): paleta real (albedo PBR),
  pintura gasta, ferrugem, sujeira; sem linhas de malha. Luz: AgX, sol + luz de preenchimento fria, névoa aérea.
- Clima dinâmico (`jogo/dados/clima.json`, `jogo/ambiente/clima.gd` + `desenho_clima.gd`): estados trocam sozinhos com
  transição suave; nuvens numa camada alta com espessura variável (grossa não passa luz, fina passa parte, rasgos
  soltam feixes de sol); neblina de chão com corpo (fatias, abre em volta de máquinas e trens); chuva em volta da
  câmera com chão molhado e poças; tempestade com relâmpago e trovão. A chuva lava a poluição. Pode desligar nas
  configurações.

## Arte
- `arte/FICHA_DE_ESTILO.md` — regras de grade, portas, cantos livres, esteira elevada, paleta e orçamento.
- `arte/CATALOGO.md` — todos os modelos (gerado automaticamente).
- `arte/blender_scripts/` — modelos descritos em código + verificador. `gerar_tudo.sh` regenera tudo.
- `arte/modelos/<categoria>/<modelo>/` — `.glb` (Godot), `.blend`, `.json` (portas e medidas) e prévia.
- `arte/icones/` — ícones da barra de construção (renderizados dos .glb por `icones.py`, fundo transparente).
- `arte/_obsoleto/` — versões antigas, só para referência.

## Modelos (95), texturas (13) e ícones (37)
Itens 25 · logística 20 · máquinas/energia/defesa 12 · transporte 8 · inimigos 5 · mapa 25 (vegetação 10, rochas 6,
jazidas 8, água 1) · texturas de chão: 7 biomas + jazida + praia + 2 águas + ruído de detalhe.
