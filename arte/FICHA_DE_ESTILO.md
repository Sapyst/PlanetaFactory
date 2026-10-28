# Ficha de estilo — modelos 3D low-poly

Fonte única das medidas: `blender_scripts/lib_pf.py`. Regenerar tudo: `blender_scripts/gerar_tudo.sh`.

## Mapa e grade
- Plano infinito procedural, dividido em tiles de **1 m × 1 m** (unidade do Blender = unidade do Godot).
- Toda estrutura ocupa um retângulo **inteiro** de tiles (1×1, 2×2, 3×3…). Origem no centro da área, chão em z = 0. Exportar com Y-up (glTF).
- **Cantos livres:** em cada vértice da grade (onde 4 tiles se encontram) fica um quadrado de **±0,03 m** reservado para pilares.
  Nenhuma estrutura põe vértice ali (o verificador barra). Exceção: muro.
- **Corpo recuado 0,05 m** da borda da área nas máquinas; só bocas de item e canos chegam à borda, nas portas.
- Subterrâneo: se existir, será outro mapa — não há "descer" em 3D.

## Portas (como máquinas, esteiras, canos e braços se ligam)
- Toda porta fica **no meio da borda de um tile** da área. A esteira/cano/braço vizinho é um tile normal — sem ímã nem encaixe por proximidade.
- No .glb, cada porta é um nó vazio `PORTA_<ITEM|FLUIDO>_<ENT|SAI>_<lado><k>` (lado S/N/L/O; k = índice do tile na borda,
  contando da esquerda de quem olha de fora). O eixo +Y do nó aponta para fora. Também está no `.json` ao lado de cada modelo.
- Item: altura da lona (z = 0,16). Fluido: eixo do cano (z = 0,35).
- **Braços** pegam do tile atrás (sul) e soltam no tile da frente (norte); por isso toda máquina aceita braço em qualquer tile da borda.

## Esteira
- 1 faixa central. Perfil de junção (16 vértices): lona ±0,40 (z 0,10–0,16), trilhos 0,40–0,46 (z 0,04–0,20), friso 0,40–0,46 (z 0,20–0,225).
- Até 4 itens por tile (passo 0,25 m).
- **Elevada:** mesmas peças, apoiadas em **pilares nos cantos da grade** (`pilar_base` + n×`pilar_segmento` 0,5 m + `pilar_topo`).
  Níveis múltiplos de **0,5 m**. Só passa por cima de estrutura mais baixa que o nível. O jogo põe pilares onde o canto está livre.
- **Rampa:** sobe 0,5 m por tile (~26,6°, abaixo do ângulo de escorregar). Girada 180° vira descida.

## Junções exatas
Peças que se ligam (esteira, cano, rampa) têm a ponta exatamente no plano da borda, perpendicular a ela, com o **mesmo perfil de vértices**
da peça reta e ponta aberta. Curvas usam tangente exata. O verificador compara vértice a vértice. Peças que dobram são **uma malha só**.

## Paleta
Estrutura: `P_Concreto`, `P_Escuro`, `P_Metal`, `P_Cobre`, `P_Faixa`, `P_Cristal` (emissivo), `P_Esteira`, `P_Fogo` (emissivo), `P_Vidro`.
Itens/recursos: `P_Pedra`, `P_Ferrugem`, `P_Malaquita`, `P_Carvao`, `P_Areia`, `P_Silex`, `P_Biomassa` (emissivo), `P_Aco`, `P_Tijolo`, `P_Placa`, `P_Municao`.
Valores em `lib_pf.PALETA`. Máquina usa só a paleta de estrutura; roxo vivo (`P_Biomassa`) é do planeta, não das máquinas.
Itens precisam contrastar com a lona preta (por isso o carvão é cinza-grafite, não preto).

## Forma e orçamento
- Sombreado facetado, sem textura (só a lona tem UV: V = distância, para rolar no shader).
- Chanfro de 1 segmento nas peças grandes. Cilindros de 5 a 12 lados.
- Item: cabe em 0,26 × 0,26 × 0,26 m, base em z = 0, **≤ 100 triângulos**. Estrutura: ≤ 1.500.

## Mapa, transporte e inimigos
- Obstáculos naturais (árvore, rocha, montanha) usam a área inteira e podem ocupar canto (somem ao limpar).
- Enfeites (`deco`): sem grade e sem colisão, cabem em 1 tile.
- Jazidas: só os pedaços de minério; o chão da mancha é a textura `jazida` do terreno.
- Trilho: bitola 0,50 m, topo do trilho z = 0,14, perfil de junção checado; curva 3×3 com raio 2,5 m.
- Veículos e inimigos: tipo `veiculo` (livre), origem no centro, rodas/pés em z = 0. Trem: corpo + truques.
- Aranha: corpo + `aranha_femur` (0,70 m) + `aranha_tibia` (0,90 m) ao longo de +X, origem na junta; quadril z = 0,55.
- Peças móveis exportadas como partes nomeadas (`_hastes`, `_rotor`, `_braco`, `_antena`, `_cabecote`, `_giro`…).

## Texturas
512² em loop **sem emenda** (ruído espectral periódico), uma por bioma + jazida, praia, água rasa/funda e ruído de detalhe.
O script mede a emenda (razão borda/vizinho ≈ 1,0 em todas).

## Fluxo
1. Modelo descrito em código em `blender_scripts/` (`itens.py`, `logistica.py`, `maquinas.py`).
2. `rodar()` monta, **verifica** (área, cantos, portas, perfis, paleta, orçamento), exporta `.glb` + `.blend` + `.json` + prévia.
3. Pranchas de coerência em `modelos/**/_prancha_*.png`; catálogo em `CATALOGO.md`.
