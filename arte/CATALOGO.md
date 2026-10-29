# Catálogo de modelos

150 modelos. Gerado por `blender_scripts/catalogo.py` — não editar à mão.

Portas: `ITEM`/`FLUIDO`/`TRILHO`, `ENT`/`SAI`, lado (S/N/L/O) e índice do tile na borda. Ficam no .glb como nós `PORTA_*`.
Partes: peças móveis exportadas separadas (o jogo anima pelo nome — ver jogo/render/animacao/animador.gd).
Texturas de chão em `texturas/` (loop sem emenda; relatório em `texturas/_emenda.json`).

## Recursos brutos

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `areia` | item | 48 | 0,22 × 0,22 × 0,16 | — | Saco de areia: vidro e silício. |
| `biomassa` | item | 88 | 0,22 × 0,22 × 0,17 | — | Fungo vivo do planeta. Combustível e química. |
| `carvao` | item | 40 | 0,22 × 0,17 × 0,13 | — | Combustível das fornalhas e geradores. |
| `cristal_bruto` | item | 50 | 0,20 × 0,16 × 0,23 | — | Cristal arrancado pelo extrator. Base de quase tudo. |
| `minerio_cobre` | item | 80 | 0,22 × 0,19 × 0,16 | — | Rocha com malaquita (cobre). |
| `minerio_ferro` | item | 80 | 0,18 × 0,20 × 0,18 | — | Rocha com veios de ferro. |
| `pedra` | item | 20 | 0,20 × 0,19 × 0,16 | — | Rocha comum: tijolo, muro, concreto. |
| `silex` | item | 28 | 0,22 × 0,17 × 0,11 | — | Sílex: pedra dura e afiada, usada em munição e ferramentas. |

## Intermediários

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `barra_aco` | item | 12 | 0,17 × 0,09 × 0,07 | — | Lingote de aço. |
| `bateria` | item | 76 | 0,14 × 0,14 × 0,21 | — | Bateria química. |
| `circuito` | item | 60 | 0,22 × 0,16 × 0,04 | — | Placa de circuito. |
| `cristal_lapidado` | item | 16 | 0,16 × 0,18 × 0,21 | — | Cristal cortado: foco de energia. |
| `engrenagem` | item | 92 | 0,24 × 0,24 × 0,05 | — | Engrenagem de ferro. |
| `fio_cobre` | item | 84 | 0,20 × 0,22 × 0,22 | — | Carretel de fio de cobre. |
| `nucleo_cristal` | item | 76 | 0,20 × 0,20 × 0,22 | — | Cristal lapidado preso em gaiola: armazena energia. |
| `placa_cobre` | item | 36 | 0,23 × 0,18 × 0,10 | — | Pilha de chapas de cobre. |
| `placa_ferro` | item | 36 | 0,23 × 0,18 × 0,10 | — | Pilha de chapas de ferro. |
| `tijolo` | item | 36 | 0,22 × 0,22 × 0,14 | — | Par de tijolos de pedra cozida. |
| `tubo` | item | 84 | 0,24 × 0,13 × 0,13 | — | Tubo de ferro para canos e máquinas. |
| `vidro` | item | 24 | 0,22 × 0,22 × 0,04 | — | Painel de vidro com moldura. |

## Avançados

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `celula_energia` | item | 96 | 0,23 × 0,16 × 0,15 | — | Célula de energia portátil. |
| `modulo_controle` | item | 60 | 0,22 × 0,18 × 0,12 | — | Módulo de controle com tela de cristal. |
| `motor` | item | 88 | 0,23 × 0,16 × 0,19 | — | Motor elétrico. |
| `municao` | item | 87 | 0,22 × 0,14 × 0,18 | — | Caixa de munição das torres. |
| `pacote_pesquisa` | item | 70 | 0,18 × 0,18 × 0,24 | — | Frasco de pesquisa para o laboratório. |

## Esteiras, distribuidores e pilares

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `divisor` | 1×1 | 260 | 1,00 × 1,00 × 0,61 | ITEM_ENT_S0, ITEM_SAI_N0, ITEM_SAI_L0, ITEM_SAI_O0 | Entra pelo sul e reparte em até 3 saídas (norte, leste, oeste). Filtro opcional. |
| `esteira_curva_dir` | 1×1 | 300 | 0,96 × 0,96 × 0,23 | ITEM_ENT_S0, ITEM_SAI_L0 | Entra pelo sul e vira à direita (sai a leste). |
| `esteira_curva_esq` | 1×1 | 300 | 0,96 × 0,96 × 0,23 | ITEM_ENT_S0, ITEM_SAI_O0 | Entra pelo sul e vira à esquerda (sai a oeste). |
| `esteira_fim` | 1×1 | 100 | 0,92 × 0,96 × 0,24 | ITEM_ENT_S0 | Para-choque no norte. Itens param aqui para braços pegarem. |
| `esteira_inicio` | 1×1 | 110 | 0,92 × 0,96 × 0,38 | ITEM_SAI_N0 | Cabeceira com motor no sul. Recebe itens por braço ou pela lateral. |
| `esteira_juncao` | 1×1 | 108 | 0,92 × 1,25 × 0,32 | ITEM_ENT_S0, ITEM_SAI_N0 | Rampa de junção: ponta de esteira que entrega na lateral de outra. Uma calha passa por cima do trilho vizinho e deita o item na outra esteira (0,25 m além da borda norte). |
| `esteira_rampa` | 1×1 | 48 | 0,92 × 1,00 × 0,69 | ITEM_ENT_S0, ITEM_SAI_N0 | Sobe 0.5 m em 1 tile (~26,6°, abaixo do ângulo de escorregar). Girada 180° vira descida. Apoio por pilares de canto. |
| `esteira_reta` | 1×1 | 48 | 0,92 × 1,00 × 0,23 | ITEM_ENT_S0, ITEM_SAI_N0 | Esteira reta. Também serve elevada, apoiada em pilares de canto. |
| `esteira_tunel_entrada` | 1×1 | 132 | 0,92 × 0,96 × 0,47 | ITEM_ENT_S0 | Passagem subterrânea (entrada): a esteira mergulha no pórtico e o item segue por baixo até a saída alinhada à frente (até 4 tiles livres no meio). |
| `esteira_tunel_saida` | 1×1 | 132 | 0,92 × 0,96 × 0,47 | ITEM_SAI_N0 | Passagem subterrânea (saída): o item volta à superfície e segue para o norte. |
| `juncao` | 1×1 | 260 | 1,00 × 1,00 × 0,61 | ITEM_ENT_S0, ITEM_ENT_L0, ITEM_ENT_O0, ITEM_SAI_N0 | Junta até 3 entradas (sul, leste, oeste) numa saída ao norte. |
| `pilar_base` | canto | 12 | 0,06 × 0,06 × 0,04 | — | Sapata do pilar (vai por baixo do primeiro segmento, sem altura extra). |
| `pilar_segmento` | canto | 12 | 0,06 × 0,06 × 0,50 | — | Fuste de 0.5 m. Fica no canto da grade (vértice entre 4 tiles). |
| `pilar_topo` | canto | 24 | 0,30 × 0,30 × 0,50 | — | Último 0.5 m do pilar, com mesa que apoia a esteira elevada. Altura do pilar = nível da esteira (n segmentos + topo). |

## Braços mecânicos

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `braco` | 1×1 | 252 | 0,68 × 0,73 × 0,96 | ITEM_ENT_S0, ITEM_SAI_N0 · partes: giro, braco1, braco2, garra | Braço mecânico: pega do tile ao sul e solta no tile ao norte. Alcance 1 tile. |
| `braco_longo` | 1×1 | 252 | 0,68 × 0,88 × 1,46 | ITEM_ENT_S0, ITEM_SAI_N0 · partes: giro, braco1, braco2, garra | Braço longo: alcance 2 tiles (pula um tile). Em repouso fica dentro do próprio tile. |
| `braco_rapido` | 1×1 | 272 | 0,68 × 0,73 × 0,96 | ITEM_ENT_S0, ITEM_SAI_N0 · partes: giro, braco1, braco2, garra | Braço rápido: alcance 1 tile, 2× mais rápido, consome mais energia. |

## Armazenagem

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `bau` | 1×1 | 60 | 0,84 × 0,78 × 0,62 | — | Baú 1×1. Braços colocam e tiram por qualquer lado. |
| `bau_grande` | 2×2 | 84 | 1,82 × 1,75 × 0,94 | — | Baú grande 2×2 (4× o baú). Braços colocam e tiram por qualquer lado. |

## Canos e bomba

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `bomba` | 1×1 | 312 | 0,76 × 0,88 × 0,82 | FLUIDO_SAI_N0 · partes: cabecote | bomba: corpo octogonal sobre a poça, êmbolo com anel de luz que sobe e desce; empurra fluido pela saída ao norte. |
| `cano_cruz` | 1×1 | 232 | 1,00 × 1,00 × 0,52 | FLUIDO_SAI_S0, FLUIDO_SAI_N0, FLUIDO_SAI_L0, FLUIDO_SAI_O0 | Cano em cruz (4 lados). |
| `cano_curva` | 1×1 | 196 | 0,64 × 0,64 × 0,49 | FLUIDO_ENT_S0, FLUIDO_SAI_L0 | Cano em curva (sul–leste), uma malha só. |
| `cano_reto` | 1×1 | 84 | 0,28 × 1,00 × 0,49 | FLUIDO_ENT_S0, FLUIDO_SAI_N0 | Cano reto (norte–sul). |
| `cano_t` | 1×1 | 188 | 0,67 × 1,00 × 0,52 | FLUIDO_SAI_S0, FLUIDO_SAI_N0, FLUIDO_SAI_L0 | Cano em T (sul, norte, leste). |

## Máquinas

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `broca_minerio` | 2×2 | 924 | 1,90 × 1,95 × 1,62 | ITEM_SAI_S0 · partes: rotor, pistao0, pistao1 | broca: carcaça octogonal blindada, coroa de lâminas que gira em volta do eixo de perfuração e dois pistões que cravam a broca. Saída sul (tile da esquerda). |
| `coletor_lixo` | 2×2 | 1100 | 1,90 × 1,90 × 1,52 | — · partes: rotor, pistao0, pistao1 | coletor de lixo: silo octogonal com janela de lodo, dois bocais de sucção que descem até o chão e turbina de exaustão que gira no topo; aspira sujeira e óleo em volta. |
| `extrator_cristal` | 3×3 | 1398 | 2,90 × 2,95 × 2,55 | ITEM_SAI_S1 · partes: hastes, cristal, pistao0, pistao1, pistao2, pistao3 | extrator de cristal: câmara octogonal sobre a jazida, quatro pilones que suspendem o prisma de ressonância, anel de extração que sobe e desce e calha de luz até a boca sul. |
| `filtro_agua` | 2×2 | 1420 | 1,90 × 1,90 × 1,48 | — · partes: rotor, pistao0, pistao1 | filtro de água: três colunas de vidro com água limpa, coletor por cima e bomba de impulsor que gira; tomada d'água pelo ralo da borda sul. |
| `fornalha` | 2×2 | 836 | 1,90 × 2,00 × 1,19 | ITEM_ENT_S1, ITEM_SAI_N0 · partes: pistao0, pistao1 | fornalha de indução: cadinho octogonal, núcleo incandescente visto por frestas, bobinas de cobre e aletas de calor. Entra pelo sul, sai pelo norte. |
| `laboratorio` | 3×3 | 1302 | 2,90 × 2,95 × 2,54 | ITEM_ENT_S1 · partes: antena, pistao0, pistao1, pistao2, pistao3 | laboratório: tambor octogonal, cúpula de sensores com pilares de dados de cristal e varredor que gira no topo. Entra pelo sul (meio). |
| `montadora` | 3×3 | 1442 | 2,90 × 3,00 × 1,83 | ITEM_ENT_S1, ITEM_SAI_N1 · partes: antena, cristal, pistao0, pistao1, pistao2, pistao3 | montadora: câmara blindada octogonal, anel manipulador suspenso que gira e prisma de montagem de cristal. Entra pelo sul, sai pelo norte (meio). |
| `nucleo` | 3×3 | 1426 | 3,00 × 3,00 × 2,56 | ITEM_ENT_S1, ITEM_ENT_N1, ITEM_ENT_L1, ITEM_ENT_O1 · partes: cristal, antena, pistao0, pistao1, pistao2, pistao3 | Núcleo: a unidade semeadora da IA. Tudo que entra (esteira nas 4 bocas ou braço) vira estoque para construir. Partes: cristal (monólito pulsa), antena (anel gira). |
| `refinador` | 3×3 | 1374 | 3,00 × 2,95 × 3,12 | FLUIDO_ENT_O1, FLUIDO_SAI_L1, ITEM_SAI_N0 · partes: antena, pistao0, pistao1 | refinador: dois reatores octogonais e torre de fracionamento com anel de campo que gira; fluido entra a oeste, sai a leste; item ao norte. |
| `terraplenagem` | 3×3 | 1158 | 2,90 × 2,90 × 2,23 | — · partes: antena, cristal, cabecote, pistao0, pistao1 | Terraplenagem: unidade de modelagem do terreno da IA. Enquanto existir, libera Aplainar em qualquer lugar do mapa. Partes: antena (anel de sensores gira), cristal (núcleo pulsa), bloco (rocha suspensa). |
| `viveiro` | 2×2 | 1052 | 1,95 × 1,90 × 1,73 | FLUIDO_ENT_O0 · partes: antena, pistao0, pistao1 | viveiro: estufa aberta (telhado de vidro) com canteiros de mudas, aspersor que gira no topo; seiva entra pelo cano a oeste e vira muda plantada em volta. |

## Energia e fluidos

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `acumulador` | 2×2 | 1278 | 1,90 × 1,90 × 1,69 | — · partes: cristal | acumulador: quatro células octogonais com faixa de carga e núcleo de cristal que pulsa no meio; guarda a sobra de energia da rede e devolve quando falta. |
| `gerador` | 2×2 | 1188 | 1,90 × 1,95 × 1,84 | ITEM_ENT_S1 · partes: antena, pistao0, pistao1 | gerador: câmara de reação vertical com anéis de contenção e núcleo luminoso; combustível entra pelo sul. Energia vai por postes. |
| `painel_solar` | 2×2 | 580 | 1,90 × 1,90 × 1,08 | — | painel solar: duas placas de células inclinadas para o sul sobre cavaletes, moldura de aço; gera energia com sol (menos com nuvem e chuva), sem combustível. |
| `poste_energia` | 1×1 | 94 | 0,70 × 0,40 × 2,30 | — | Poste de energia: liga máquinas num raio. Ocupa só o centro do tile. |
| `tanque` | 2×2 | 322 | 2,00 × 2,00 × 1,70 | FLUIDO_SAI_S0, FLUIDO_SAI_N0, FLUIDO_SAI_L0, FLUIDO_SAI_O0 | Tanque de fluido. Canos nos 4 lados (tile da esquerda de cada lado). |
| `torre_sem_fio` | 1×1 | 250 | 0,80 × 0,80 × 2,90 | — · partes: cristal | Torre de energia sem fio: liga postes/torres e máquinas a distância, sem cabo. |
| `turbina_eolica` | 2×2 | 624 | 1,90 × 1,90 × 3,64 | — · partes: nacele, helice | turbina eólica: torre octogonal afilada; a nacele gira no topo para encarar o vento e a hélice de 3 pás gira com ele; gera energia sem combustível. |

## Defesa

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `muro_centro` | 1×1 | 24 | 0,64 × 0,64 × 1,50 | — | Pilar do muro (centro do tile). O jogo junta muro_lado para cada vizinho com muro. |
| `muro_lado` | 1×1 | 24 | 0,48 × 0,20 × 1,26 | — | Pano de muro do centro até a borda norte (girar para os outros lados). |
| `torre_defesa` | 2×2 | 688 | 1,90 × 1,95 × 1,38 | ITEM_ENT_S1 · partes: pistao0, pistao1, giro, canhao | torre de defesa: pedestal octogonal, cabeça blindada com olho sensor e canhão de trilho duplo. Munição entra pelo sul. Partes: base, giro (gira em Z), canhao (inclina). |

## Trilhos e estação

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `estacao` | 2×3 | 140 | 1,92 × 2,90 × 2,15 | ITEM_ENT_L2, ITEM_SAI_L0 | Estação de carga 2×3: a linha passa a oeste (encostada). Braços tiram/põem nos vagões; esteiras entram e saem a leste. |
| `sinal_trem` | 1×1 | 100 | 0,24 × 0,24 × 1,55 | — | Sinal de bloco: fica no tile ao lado da linha. Divide a linha em blocos (1 trem por bloco). |
| `trilho_curva` | 3×3 | 768 | 2,92 × 2,92 × 0,14 | TRILHO_ENT_S0, TRILHO_SAI_L0 | Curva de trilho 3×3 (raio 2,5 m): entra pelo sul (tile da esquerda), sai a leste (tile de cima). |
| `trilho_fim` | 1×1 | 96 | 0,84 × 0,92 × 0,40 | TRILHO_ENT_S0 | Fim de linha com para-choque (norte). |
| `trilho_reto` | 1×1 | 72 | 0,84 × 1,00 × 0,14 | TRILHO_ENT_S0, TRILHO_SAI_N0 | Trilho reto norte–sul. |

## Trem (veículos)

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `locomotiva` | livre | 368 | 0,72 × 2,93 × 1,15 | — · partes: truque0, truque1 | Locomotiva (3 m). Partes: corpo + 2 truques. |
| `vagao_carga` | livre | 332 | 0,74 × 2,90 × 0,84 | — · partes: truque0, truque1 | Vagão de carga (3 m). Itens carregados por braços na estação. |
| `vagao_tanque` | livre | 432 | 0,72 × 2,90 × 1,05 | — · partes: truque0, truque1 | Vagão-tanque (3 m) para fluidos. |

## Inimigos

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `aranha_corpo` | livre | 320 | 1,00 × 1,96 × 0,60 | — | Corpo da aranha mecânica (origem no chão, sob o centro). |
| `aranha_femur` | peça | 80 | 0,85 × 0,12 × 0,16 | — | Fêmur (0.7 m ao longo de +X, origem no quadril). |
| `aranha_montada` | livre | 632 | 2,91 × 2,08 × 0,89 | — | Prévia montada (não usar no jogo; o jogo monta com IK). |
| `aranha_tibia` | peça | 34 | 0,85 × 0,10 × 0,11 | — | Tíbia (0.9 m ao longo de +X, origem no joelho, ponta = pé). |
| `ninho_aranha` | 3×3 | 264 | 2,76 × 2,72 × 1,80 | — | Ninho construído pelas aranhas: gera novas aranhas. Alvo prioritário. |

## Mapa: vegetação

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `arbusto` | 1×1 | 80 | 0,62 × 0,57 × 0,43 | — | Arbusto da campina (bloqueia 1 tile, limpa rápido). |
| `arv_acacia_1` | 1×1 | 132 | 0,79 × 0,81 × 1,88 | — | Acácia-seca (variação 1): copa achatada em guarda-chuva; perde metade no verão seco. Bloqueia 1 tile. |
| `arv_acacia_2` | 1×1 | 132 | 0,82 × 0,82 × 1,61 | — | Acácia-seca (variação 2): copa achatada em guarda-chuva; perde metade no verão seco. Bloqueia 1 tile. |
| `arv_acacia_3` | 1×1 | 132 | 0,80 × 0,83 × 1,88 | — | Acácia-seca (variação 3): copa achatada em guarda-chuva; perde metade no verão seco. Bloqueia 1 tile. |
| `arv_acacia_4` | 1×1 | 132 | 0,82 × 0,74 × 1,67 | — | Acácia-seca (variação 4): copa achatada em guarda-chuva; perde metade no verão seco. Bloqueia 1 tile. |
| `arv_acacia_5` | 1×1 | 132 | 0,83 × 0,80 × 1,92 | — | Acácia-seca (variação 5): copa achatada em guarda-chuva; perde metade no verão seco. Bloqueia 1 tile. |
| `arv_acacia_6` | 1×1 | 132 | 0,84 × 0,71 × 1,65 | — | Acácia-seca (variação 6): copa achatada em guarda-chuva; perde metade no verão seco. Bloqueia 1 tile. |
| `arv_betula_1` | 1×1 | 228 | 0,53 × 0,46 × 2,56 | — | Bétula-prata (variação 1): estreita, tronco claro; caduca: amarela no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_betula_2` | 1×1 | 228 | 0,38 × 0,46 × 2,60 | — | Bétula-prata (variação 2): estreita, tronco claro; caduca: amarela no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_betula_3` | 1×1 | 228 | 0,41 × 0,44 × 2,32 | — | Bétula-prata (variação 3): estreita, tronco claro; caduca: amarela no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_betula_4` | 1×1 | 196 | 0,48 × 0,41 × 2,50 | — | Bétula-prata (variação 4): estreita, tronco claro; caduca: amarela no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_betula_5` | 1×1 | 196 | 0,48 × 0,48 × 2,56 | — | Bétula-prata (variação 5): estreita, tronco claro; caduca: amarela no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_betula_6` | 1×1 | 228 | 0,48 × 0,53 × 2,70 | — | Bétula-prata (variação 6): estreita, tronco claro; caduca: amarela no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_carvalho_1` | 1×1 | 188 | 0,81 × 0,78 × 1,92 | — | Carvalho-de-campina (variação 1): copa redonda larga; caduca: amarela/laranja no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_carvalho_2` | 1×1 | 188 | 0,83 × 0,83 × 2,06 | — | Carvalho-de-campina (variação 2): copa redonda larga; caduca: amarela/laranja no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_carvalho_3` | 1×1 | 188 | 0,79 × 0,84 × 1,94 | — | Carvalho-de-campina (variação 3): copa redonda larga; caduca: amarela/laranja no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_carvalho_4` | 1×1 | 220 | 0,86 × 0,91 × 1,99 | — | Carvalho-de-campina (variação 4): copa redonda larga; caduca: amarela/laranja no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_carvalho_5` | 1×1 | 220 | 0,86 × 0,82 × 1,87 | — | Carvalho-de-campina (variação 5): copa redonda larga; caduca: amarela/laranja no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_carvalho_6` | 1×1 | 188 | 0,82 × 0,88 × 2,19 | — | Carvalho-de-campina (variação 6): copa redonda larga; caduca: amarela/laranja no outono, nua no inverno. Bloqueia 1 tile. |
| `arv_fungo_cristal_1` | 1×1 | 92 | 0,78 × 0,75 × 2,02 | — | Fungo-cristal (variação 1): alienígena: chapéu com cristais que brilham; perene. Bloqueia 1 tile. |
| `arv_fungo_cristal_2` | 1×1 | 92 | 0,77 × 0,75 × 1,66 | — | Fungo-cristal (variação 2): alienígena: chapéu com cristais que brilham; perene. Bloqueia 1 tile. |
| `arv_fungo_cristal_3` | 1×1 | 92 | 0,77 × 0,79 × 1,93 | — | Fungo-cristal (variação 3): alienígena: chapéu com cristais que brilham; perene. Bloqueia 1 tile. |
| `arv_fungo_cristal_4` | 1×1 | 92 | 0,81 × 0,83 × 1,80 | — | Fungo-cristal (variação 4): alienígena: chapéu com cristais que brilham; perene. Bloqueia 1 tile. |
| `arv_fungo_cristal_5` | 1×1 | 92 | 0,82 × 0,79 × 2,07 | — | Fungo-cristal (variação 5): alienígena: chapéu com cristais que brilham; perene. Bloqueia 1 tile. |
| `arv_fungo_cristal_6` | 1×1 | 92 | 0,80 × 0,76 × 1,92 | — | Fungo-cristal (variação 6): alienígena: chapéu com cristais que brilham; perene. Bloqueia 1 tile. |
| `arv_pinheiro_1` | 1×1 | 112 | 0,87 × 0,89 × 2,66 | — | Pinheiro (variação 1): cone em camadas; perene (não muda). Bloqueia 1 tile. |
| `arv_pinheiro_2` | 1×1 | 112 | 0,84 × 0,85 × 2,51 | — | Pinheiro (variação 2): cone em camadas; perene (não muda). Bloqueia 1 tile. |
| `arv_pinheiro_3` | 1×1 | 112 | 0,84 × 0,85 × 2,89 | — | Pinheiro (variação 3): cone em camadas; perene (não muda). Bloqueia 1 tile. |
| `arv_pinheiro_4` | 1×1 | 112 | 0,83 × 0,82 × 2,59 | — | Pinheiro (variação 4): cone em camadas; perene (não muda). Bloqueia 1 tile. |
| `arv_pinheiro_5` | 1×1 | 112 | 0,82 × 0,84 × 2,71 | — | Pinheiro (variação 5): cone em camadas; perene (não muda). Bloqueia 1 tile. |
| `arv_pinheiro_6` | 1×1 | 112 | 0,85 × 0,86 × 2,65 | — | Pinheiro (variação 6): cone em camadas; perene (não muda). Bloqueia 1 tile. |
| `arv_salgueiro_1` | 1×1 | 212 | 0,87 × 0,86 × 1,54 | — | Salgueiro-do-pântano (variação 1): galhos caídos; amarelado no inverno. Bloqueia 1 tile. |
| `arv_salgueiro_2` | 1×1 | 212 | 0,92 × 0,83 × 1,61 | — | Salgueiro-do-pântano (variação 2): galhos caídos; amarelado no inverno. Bloqueia 1 tile. |
| `arv_salgueiro_3` | 1×1 | 212 | 0,88 × 0,89 × 1,52 | — | Salgueiro-do-pântano (variação 3): galhos caídos; amarelado no inverno. Bloqueia 1 tile. |
| `arv_salgueiro_4` | 1×1 | 212 | 0,85 × 0,86 × 1,52 | — | Salgueiro-do-pântano (variação 4): galhos caídos; amarelado no inverno. Bloqueia 1 tile. |
| `arv_salgueiro_5` | 1×1 | 212 | 0,91 × 0,89 × 1,45 | — | Salgueiro-do-pântano (variação 5): galhos caídos; amarelado no inverno. Bloqueia 1 tile. |
| `arv_salgueiro_6` | 1×1 | 212 | 0,83 × 0,86 × 1,52 | — | Salgueiro-do-pântano (variação 6): galhos caídos; amarelado no inverno. Bloqueia 1 tile. |
| `arvore_campina_a` | 1×1 | 80 | 0,67 × 0,78 × 1,49 | — | Árvore da campina (bloqueia 1 tile). |
| `arvore_campina_b` | 1×1 | 80 | 0,68 × 0,59 × 1,75 | — | Árvore alta da campina (bloqueia 1 tile). |
| `arvore_morta` | 1×1 | 56 | 0,58 × 0,47 × 1,32 | — | Árvore seca do cinzal. |
| `cacto_cristal` | 1×1 | 108 | 0,50 × 0,20 × 1,03 | — | Planta cristalina do deserto de sílex. |
| `cogumelo_gigante_a` | 1×1 | 1254 | 0,92 × 0,91 × 1,60 | — | Cogumelo gigante da floresta fúngica. Corte dá biomassa. |
| `cogumelo_gigante_b` | 1×1 | 1254 | 0,92 × 0,91 × 2,08 | — | Cogumelo gigante alto. Corte dá biomassa. |
| `flor_luminosa` | enfeite | 84 | 0,24 × 0,14 × 0,36 | — | Flor bioluminescente (enfeite; brilha à noite). |
| `grama_tufo` | enfeite | 24 | 0,16 × 0,16 × 0,29 | — | Tufo de grama (enfeite; balança com o vento no shader). |
| `junco` | enfeite | 132 | 0,25 × 0,34 × 0,73 | — | Juncos do pântano e beira de lago (enfeite). |

## Mapa: rochas e montanhas

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `montanha_3x3` | 3×3 | 264 | 2,67 × 2,54 × 2,60 | — | Formação de montanha 3×3 (intransponível; não dá para construir em cima). |
| `montanha_5x5` | 5×5 | 380 | 4,81 × 4,42 × 4,20 | — | Montanha 5×5 (intransponível). |
| `pedregulho` | 1×1 | 40 | 0,55 × 0,66 × 0,37 | — | Pedregulho (bloqueia 1 tile; dá pedra). |
| `rocha_agua` | 1×1 | 60 | 0,77 × 0,59 × 0,36 | — | Rochas de margem/rio (bloqueia 1 tile). |
| `rocha_grande` | 2×2 | 80 | 1,43 × 1,68 × 1,17 | — | Rocha grande 2×2 (bloqueia; dá bastante pedra). |
| `seixos` | enfeite | 80 | 0,45 × 0,60 × 0,10 | — | Seixos soltos (enfeite). |

## Mapa: jazidas

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `jazida_areia` | 1×1 | 144 | 0,36 × 0,52 × 0,08 | — | Duna de areia (broca). |
| `jazida_carvao` | 1×1 | 120 | 0,74 × 0,66 × 0,12 | — | Jazida de carvão (broca). |
| `jazida_cobre` | 1×1 | 120 | 0,55 × 0,41 × 0,12 | — | Jazida de cobre (broca). |
| `jazida_cristal` | 1×1 | 60 | 0,53 × 0,43 × 0,30 | — | Jazida de cristal (extrator). |
| `jazida_ferro` | 1×1 | 120 | 0,62 × 0,40 × 0,12 | — | Jazida de ferro (broca). |
| `jazida_pedra` | 1×1 | 120 | 0,56 × 0,41 × 0,12 | — | Jazida de pedra (broca). |
| `jazida_silex` | 1×1 | 120 | 0,54 × 0,59 × 0,12 | — | Jazida de sílex (broca). |
| `poca_seiva` | 1×1 | 152 | 0,82 × 0,83 × 0,08 | — | Poça de seiva (bomba por cima). Fluido do planeta. |

## Mapa: água

| Modelo | Área | Tri | Dimensões (m) | Portas | Descrição |
|---|---|---|---|---|---|
| `vitoria_regia` | enfeite | 92 | 0,52 × 0,40 × 0,06 | — | Folhas flutuantes de lago/lagoa (enfeite; boia no shader). |

## Verificação

Todos os modelos passaram na checagem automática.
