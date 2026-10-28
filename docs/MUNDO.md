# Mundo procedural e distribuição bio-territorial

Plano infinito em tiles de 1 m, chunks de 32×32. Tudo é **função do tile e da semente** (`jogo/mundo/`):
gerar um chunk ou consultar um tile solto dá o mesmo resultado, em qualquer ordem — não existe costura.

## 1. Terreno (água × terra)
Ruído "continente" (FastNoiseLite, frequência 0,0028) dá a elevação; o spawn ganha dois sinos de altura
(garantia de terra firme). Faixas:

| Elevação | Terreno |
|---|---|
| < −0,32 | oceano |
| < −0,18 | mar |
| < −0,14 | praia |
| resto | terra, a não ser que: |
| \|ruído rio\| < ~0,012–0,022 | rio (serpenteia; alarga perto do mar) |
| ruído lago < −0,55 | lago |
| ruído lagoa < −0,58 | lagoa |

Num quadrado de 40 tiles em volta do spawn não há rio/lago/lagoa.

## 2. Clima → bioma
Temperatura e umidade (0..1) com distorção de domínio (bordas orgânicas). O bioma é o **centro mais próximo**
no plano clima (tabela em `jogo/dados/biomas.json`):

| Bioma | Clima (temp., umid.) | Obstáculos | Enfeites | Jazidas preferidas |
|---|---|---|---|---|
| campina | 0,55 / 0,55 | árvores, arbustos | grama, flores | ferro, cobre, pedra, carvão |
| floresta fúngica | 0,60 / 0,85 | cogumelos gigantes (22% dos tiles) | flores luminosas | seiva, carvão |
| deserto de sílex | 0,88 / 0,12 | cactos de cristal | seixos | sílex, areia, cobre |
| planalto rochoso | 0,30 / 0,30 | pedregulhos; rochas 2×2 e montanhas 3×3/5×5 | seixos | pedra, ferro, cobre |
| campo de cristal | 0,15 / 0,65 | cactos de cristal | seixos, flores | **cristal** |
| pântano | 0,75 / 0,95 | árvores mortas, rochas | juncos, vitória-régia | carvão, seiva |
| cinzal | 0,95 / 0,40 | árvores mortas, pedregulhos | seixos | pedra, carvão, ferro |

## 3. Jazidas (manchas de minério)
- Uma mancha por célula de 40×40, com o centro a ≥10 tiles da borda da célula → manchas nunca se sobrepõem.
- Tipo sorteado pelos pesos do bioma do centro. Chance, raio e riqueza **crescem com a distância do spawn**
  (o jogador é empurrado a expandir).
- Perto do spawn há 5 manchas fixas: cristal, ferro, cobre, carvão e pedra (testado: ≥25 tiles cada).
- O chão do tile de jazida usa a textura `jazida` e os pedaços de minério vêm por cima → a mancha lê como um campo contínuo.

## 4. Obstáculos e enfeites
- **Grandes** (rocha 2×2, montanhas): no máximo um por célula de 6×6, inteiro dentro da célula, só em terra sem jazida.
- **1×1** (árvore, cogumelo, pedregulho…): chance por tile pelo bioma. Precisam ser limpos para construir.
- **Enfeites** (grama, flores, seixos, juncos, vitória-régia na água): sem colisão, posição sorteada dentro do tile.
- Raio de 7 tiles livre no spawn.

## 5. Desenho
`DesenhoChunk`: 1 malha de chão por chunk (camada do Texture2DArray por tile) + 1 MultiMesh por tipo de objeto.
Texturas em loop sem emenda (`arte/texturas/`, medido em `_emenda.json`); vento, água e pulsos são shader.
