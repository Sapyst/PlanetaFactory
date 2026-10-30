# Recursos do mapa

Guia do que existe no planeta e de onde tirar cada coisa. Gerado de `jogo/dados/` por `jogo/ferramentas/gerar_doc_recursos.py` — não editar à mão.

## Como ver no jogo

- **Visão de recursos** — tecla **V** (ou botão **Recursos**): o mapa fica cinza, cada jazida aparece na cor do recurso com o nome, quanto tem e qual máquina extrai, e cada bioma/água ganha o nome escrito no mapa.
- **Ficha do tile** — com a visão ligada, passe o mouse (ou toque) num tile: mostra a zona, a jazida (quantidade naquele tile), o elemento natural e o que ele rende ao remover, ou a construção que está ali.
- **Modo construção** — com uma peça na mão, toda esteira mostra uma faixa colorida com setas andando no sentido do fluxo (amarelo = chão, verde = 0,5 m, rosa = 1,0 m).

## Jazidas

| Recurso | Cor no mapa | Item que sai | Máquina | Onde aparece (chance por bioma) |
|---|---|---|---|---|
| **Ferro** | `#c4573a` | Minério de ferro | Broca de minério | Campina 36%, Planalto rochoso 27%, Cinzal 25% |
| **Cobre** | `#e8932f` | Minério de cobre | Broca de minério | Campina 27%, Floresta fúngica 12%, Deserto de sílex 20%, Planalto rochoso 27% |
| **Carvão** | `#2a2a2e` | Carvão | Broca de minério | Campina 18%, Floresta fúngica 38%, Pântano 67%, Cinzal 38% |
| **Pedra** | `#d8d2c4` | Pedra | Broca de minério | Campina 18%, Planalto rochoso 36%, Campo de cristal 14%, Cinzal 38% |
| **Sílex** | `#7d98c4` | Sílex | Broca de minério | Deserto de sílex 40%, Planalto rochoso 9% |
| **Areia** | `#f2d47a` | Areia | Broca de minério | Deserto de sílex 40% |
| **Cristal** | `#4fe6df` | Cristal bruto | Extrator de cristal | Campo de cristal 86% |
| **Seiva** | `#8fd146` | Biomassa | Bomba | Floresta fúngica 50%, Pântano 33% |

Perto do ponto inicial há sempre uma jazida de cada: cristal, ferro, cobre, carvão e pedra. Longe do início as manchas ficam maiores e mais ricas.

## Biomas

### Campina
- **Jazidas:** Ferro (36%), Cobre (27%), Pedra (18%), Carvão (18%)
- **Elementos:** Carvalho, Bétula-prata, Arbusto, Pedregulho, Rocha grande

### Floresta fúngica
- **Jazidas:** Seiva (50%), Carvão (38%), Cobre (12%)
- **Elementos:** Cogumelo gigante, Fungo-cristal, Pinheiro

### Deserto de sílex
- **Jazidas:** Sílex (40%), Areia (40%), Cobre (20%)
- **Elementos:** Cacto de cristal, Pedregulho, Acácia, Rocha grande, Morro

### Planalto rochoso
- **Jazidas:** Pedra (36%), Ferro (27%), Cobre (27%), Sílex (9%)
- **Elementos:** Pedregulho, Pinheiro, Rocha grande, Morro, Montanha

### Campo de cristal
- **Jazidas:** Cristal (86%), Pedra (14%)
- **Elementos:** Cacto de cristal, Pedregulho, Fungo-cristal, Rocha grande

### Pântano
- **Jazidas:** Carvão (67%), Seiva (33%)
- **Elementos:** Salgueiro, Árvore morta, Rocha na água

### Cinzal
- **Jazidas:** Pedra (38%), Carvão (38%), Ferro (25%)
- **Elementos:** Árvore morta, Pedregulho, Acácia, Rocha grande, Morro

## Águas

Rio, lago, lagoa, mar e oceano não aceitam construção; a praia aceita. Na visão de recursos cada água aparece com o nome em azul.

## Elementos naturais (remover rende)

| Elemento | Rende |
|---|---|
| Pedregulho | 6 × Pedra |
| Rocha grande | 20 × Pedra |
| Morro | 45 × Pedra |
| Montanha | 120 × Pedra |
| Carvalho | 5 × Biomassa |
| Bétula-prata | 4 × Biomassa |
| Pinheiro | 5 × Biomassa |
| Salgueiro | 4 × Biomassa |
| Acácia | 3 × Biomassa |
| Fungo-cristal | 4 × Biomassa, 1 × Cristal bruto |
| Árvore queimada | 2 × Carvão |
| Tronco caído | 3 × Carvão |
| Árvore | 4 × Biomassa |
| Árvore morta | 2 × Biomassa |
| Arbusto | 2 × Biomassa |
| Cogumelo gigante | 6 × Biomassa |
| Cacto de cristal | 3 × Cristal bruto |

## Construções

Ficha de cada peça do menu: energia, o que guarda, integridade (♥), custo e a pesquisa que libera ("início" = já vem liberada). No jogo a mesma ficha aparece no botão da peça e no painel ao tocar nela.

### Esteiras

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Esteira** — Leva itens. Arraste para traçar o caminho. | — | 50 | 1 placa de ferro | início |
| **Rampa sobe** — Sobe a esteira 0,5 m (passa por cima). | — | 50 | 2 placa de ferro, 1 engrenagem | Logística 2 |
| **Rampa desce** — Desce a esteira 0,5 m. | — | — | — | Logística 2 |
| **Passagem: entrada** — Leva a esteira por baixo do chão. Ponha a saída alinhada à frente, até 4 tiles livres no meio. | — | 120 | 5 placa de ferro, 2 engrenagem | Logística 2 |
| **Passagem: saída** — Onde a passagem subterrânea volta à superfície (mesma direção da entrada). | — | 120 | 5 placa de ferro, 2 engrenagem | Logística 2 |
| **Esteira rápida** — Leva o dobro de itens. Arraste por cima da esteira comum para trocar. | — | — | 2 placa de ferro, 1 engrenagem | Logística 3 |
| **Rampa rápida sobe** — Rampa da esteira rápida: sobe 0,5 m. | — | 70 | 3 placa de ferro, 3 engrenagem | Logística 3 |
| **Rampa rápida desce** — Rampa da esteira rápida: desce 0,5 m. | — | — | — | Logística 3 |
| **Passagem rápida: entrada** — Passagem rápida: saída alinhada à frente, até 6 tiles livres no meio. | — | 160 | 8 placa de ferro, 6 engrenagem | Logística 3 |
| **Passagem rápida: saída** — Onde a passagem rápida volta à superfície (só liga com entrada rápida). | — | 160 | 8 placa de ferro, 6 engrenagem | Logística 3 |
| **Esteira expressa** — Leva o triplo da esteira comum. Arraste por cima de outra esteira para trocar. | — | — | 1 liga leve, 2 engrenagem | Logística 4 |
| **Rampa expressa sobe** — Rampa da esteira expressa: sobe 0,5 m. | — | 80 | 2 liga leve, 4 engrenagem | Logística 4 |
| **Rampa expressa desce** — Rampa da esteira expressa: desce 0,5 m. | — | — | — | Logística 4 |
| **Passagem expressa: entrada** — Passagem expressa: saída alinhada à frente, até 8 tiles livres no meio. | — | 170 | 6 liga leve, 10 engrenagem | Logística 4 |
| **Passagem expressa: saída** — Onde a passagem expressa volta à superfície (só liga com entrada expressa). | — | 170 | 6 liga leve, 10 engrenagem | Logística 4 |
| **Esteira quântica** — Leva o quádruplo da esteira comum. Arraste por cima de outra esteira para trocar. | — | — | 2 liga leve, 1 cristal carregado | Logística 5 |
| **Rampa quântica sobe** — Rampa da esteira quântica: sobe 0,5 m. | — | 90 | 3 liga leve, 2 cristal carregado | Logística 5 |
| **Rampa quântica desce** — Rampa da esteira quântica: desce 0,5 m. | — | — | — | Logística 5 |
| **Passagem quântica: entrada** — Passagem quântica: saída alinhada à frente, até 10 tiles livres no meio. | — | 190 | 10 liga leve, 6 cristal carregado, 2 processador | Logística 5 |
| **Passagem quântica: saída** — Onde a passagem quântica volta à superfície (só liga com entrada quântica). | — | 190 | 10 liga leve, 6 cristal carregado, 2 processador | Logística 5 |
| **Divisor** — Reparte itens em até 3 saídas. | — | 80 | 4 placa de ferro, 2 circuito | Eletrônica |
| **Divisor com filtro** — Manda o item escolhido para uma saída; o resto vai pela prioridade. Toque nele para escolher. | — | 90 | 5 placa de ferro, 5 circuito | Divisor com filtro |
| **Junção** — Junta até 3 esteiras em uma. | — | 80 | 4 placa de ferro, 2 circuito | Eletrônica |

### Braços

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Braço** — Pega atrás e solta na frente, um item por vez. | usa 13 kW | 60 | 2 placa de ferro, 1 engrenagem | início |
| **Braço rápido** — Braço 2× mais rápido (gasta mais energia). | usa 46 kW | 60 | 2 placa de ferro, 2 engrenagem, 2 circuito | Eletrônica |
| **Braço longo** — Braço que alcança 2 tiles. | usa 20 kW | 60 | 3 placa de ferro, 2 engrenagem | Logística 2 |
| **Braço com filtro** — Só pega os itens que você escolher (até 5). Toque nele para escolher. | usa 16 kW | 60 | 3 placa de ferro, 2 engrenagem, 4 circuito | Braço com filtro |
| **Braço empilhador** — Leva até 4 itens iguais por vez (o que estiver na origem). | usa 30 kW | 90 | 4 barra de aço, 6 engrenagem, 1 processador | Braço empilhador |
| **Braço quântico** — Lança telescópica: pega de 1 a 3 tiles atrás (toque nele para escolher) e o campo leva até 8 itens iguais por vez ao tile da frente, a cada 0,2 s. | usa 150 kW | 150 | 4 liga leve, 4 processador, 2 cristal carregado | Braço quântico |
| **Baú** — Guarda itens; braços põem e tiram. | 1600 itens | 100 | 4 placa de ferro | início |
| **Baú grande** — Baú 2×2: guarda 4× mais. | 6400 itens | 300 | 16 placa de ferro, 4 barra de aço | Armazenagem |
| **Silo de granel** — Silo 3×3: 20.000 itens de um tipo só. | 20000 itens | 900 | 40 placa de ferro, 20 barra de aço, 10 engrenagem, 2 motor | Silo de granel |

### Canos

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Cano** — Leva fluidos. Arraste. | — | — | 1 placa de ferro | Fluidos |
| **Cano em T** — Divide o cano em 3. | — | 50 | 2 placa de ferro | Fluidos |
| **Cano em cruz** — Cruza canos em 4. | — | 50 | 2 placa de ferro | Fluidos |
| **Cano subterrâneo: entrada** — Passa o cano por baixo da terra. Ponha a saída alinhada à frente, até 9 tiles livres no meio. | — | 150 | 8 placa de ferro, 5 tubo | Cano subterrâneo |
| **Cano subterrâneo: saída** — Onde o cano subterrâneo volta à superfície (mesma direção da entrada). | — | 150 | 8 placa de ferro, 5 tubo | Cano subterrâneo |
| **Bomba** — Tira seiva de uma poça. | usa 30 kW | 150 | 5 placa de ferro, 3 engrenagem, 2 tubo | Fluidos |
| **Bomba d'água** — 2×2 na margem: a tomada (lado da grade) encosta na água. Solta 40 de água/s pelo cano; água suja rende menos. | usa 60 kW | 300 | 20 placa de ferro, 10 tubo, 1 motor, 20 pedra | Água como insumo |
| **Coletor de chuva** — 2×2 em qualquer lugar: até 25 de água/s com chuva forte, nada no seco. Guarda 2.000. | — | 250 | 24 placa de ferro, 8 tubo, 6 engrenagem | Coletor de chuva |
| **Condensador de neblina** — 2×2 com energia (80 kW): até 12 de água/s com neblina (mais no inverno). | usa 80 kW | 250 | 16 placa de ferro, 16 placa de cobre, 6 tubo, 2 motor, 4 circuito | Condensador de neblina |
| **Tanque** — Guarda muito fluido. | 25000 de fluido | 500 | 20 placa de ferro, 4 tubo | Fluidos |

### Produção

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Extrator de cristal** — Extrai cristal da jazida e despeja na esteira. | usa 90 kW · polui 10/min | 300 | 10 placa de ferro, 5 engrenagem, 5 placa de cobre | início |
| **Broca** — Fura a jazida e despeja minério na esteira. | usa 90 kW · polui 10/min | 300 | 8 placa de ferro, 4 engrenagem, 5 pedra | início |
| **Fornalha** — Funde minério em placas (queima carvão). | polui 4/min | 200 | 10 pedra | início |
| **Montadora** — Monta peças por receita. | usa 150 kW · polui 3/min | 300 | 12 placa de ferro, 6 engrenagem, 6 placa de cobre | início |
| **Montadora 2** — Monta as mesmas peças mais rápido (1,0 contra 0,75), com 2 encaixes de módulo. | usa 200 kW · polui 3/min | 400 | 10 barra de aço, 10 engrenagem, 6 circuito, 2 motor | Montadora 2 |
| **Refinador** — Processa fluidos. | usa 420 kW · polui 6/min | 350 | 5 barra de aço, 10 tubo, 5 circuito | Refino de seiva |
| **Refinador 2** — Processa fluidos 2× mais rápido e suja a metade por produto; 2ª entrada de fluido ao sul. | usa 700 kW · polui 6/min | 500 | 30 barra de aço, 30 tubo, 6 processador, 10 liga leve, 4 motor | Refinador 2 |
| **Laboratório** — Pesquisa com pacotes. | usa 60 kW | 150 | 10 placa de ferro, 10 placa de cobre, 5 engrenagem | início |
| **Terraplenagem** — Libera Aplainar o chão em qualquer lugar. | — | 400 | 30 placa de ferro, 15 engrenagem, 40 pedra | início |

### Limpeza

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Coletor de lixo** — Aspira sujeira e óleo do chão em volta (raio 6). | usa 40 kW | 200 | 10 placa de ferro, 6 engrenagem, 4 placa de cobre | Limpeza |
| **Coletor de lixo 2** — Aspira sujeira, óleo e cinza num raio de 10 m e compacta em resíduo (braço tira). | usa 80 kW | 320 | 16 placa de ferro, 8 engrenagem, 2 motor, 6 tubo | Coletor de lixo 2 |
| **Filtro de água** — Encostado na água: limpa a água suja em volta (raio 7). | usa 60 kW | 200 | 12 placa de ferro, 6 tubo, 4 engrenagem | Limpeza |
| **Estação de tratamento** — 3×3 na margem (tomada ao sul na água): limpa a água suja em 16 m e solta 60 de água limpa/s pelo cano (leste). | usa 600 kW | 900 | 40 barra de aço, 30 tubo, 4 motor, 6 processador, 20 vidro | Estação de tratamento |
| **Viveiro** — Com seiva pelo cano, planta mudas em volta (raio 8) que viram árvores e limpam o ar e o chão. | usa 20 kW | 150 | 8 placa de ferro, 4 tubo, 6 vidro | Reflorestamento |
| **Viveiro 2** — Com seiva pelo cano: planta árvores da espécie do bioma num raio de 12 m, 2× mais rápido. | usa 40 kW | 250 | 12 placa de ferro, 8 tubo, 10 vidro, 4 circuito | Viveiro 2 |
| **Semeador de bioma** — 3×3 com seiva pelo cano: tira o queimado do chão em 14 m, devolve as árvores carbonizadas e planta mudas do bioma. | usa 300 kW | 700 | 30 barra de aço, 12 tubo, 4 motor, 6 processador | Restauração de bioma |
| **Supressor de incêndio** — Com água pelo cano: apaga fogo num raio de 8 m e molha a vegetação em volta. | usa 15 kW | 250 | 8 placa de ferro, 6 tubo, 1 motor, 2 circuito | Supressor de incêndio |
| **Purificador de ar** — Com energia, tira 6 de poluição por minuto do ar do chunk. | usa 120 kW | 250 | 14 placa de ferro, 8 tubo, 2 motor, 4 circuito | Purificador de ar |
| **Purificador atmosférico** — 3×3: tira 40 de poluição por minuto do chunk e condensa em resíduo (braço tira). | usa 500 kW | 900 | 30 barra de aço, 20 tubo, 6 motor, 4 processador, 8 cristal lapidado | Purificador atmosférico |
| **Biodigestor** — 3×3: resíduo (braço) + água (cano sul) → biomassa (braço) + seiva (cano leste). | usa 200 kW | 600 | 20 barra de aço, 16 tubo, 2 motor, 20 tijolo | Biodigestor |

### Energia

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Gerador** — Queima carvão e gera energia. | gera até 900 kW (combustível) · polui 30/min | 200 | 10 placa de ferro, 5 tubo, 10 pedra | início |
| **Painel solar** — Energia do sol, sem combustível: nada à noite, menos com nuvem e chuva, mais no verão. | gera até 300 kW (sol: zero à noite) | 120 | 6 placa de ferro, 8 vidro, 3 circuito | Energia renovável |
| **Painel solar 2** — Até 500 kW de sol, seguindo o sol: com nuvem e chuva perde só 15%; nada à noite. | gera até 500 kW (sol: zero à noite) | 160 | 8 barra de aço, 12 vidro, 2 processador, 4 cristal lapidado | Painel solar 2 |
| **Turbina eólica** — Energia do vento, sem combustível: vira para o vento; rende mais no alto e em campo aberto, para na calmaria e se protege na ventania. | gera até 200 kW (vento) | 180 | 14 placa de ferro, 10 engrenagem, 2 motor | Energia renovável |
| **Acumulador** — Guarda a sobra de energia da rede e devolve quando falta. | guarda 80 MJ (até 500 kW) | 250 | 10 placa de ferro, 8 bateria, 4 circuito | Acumulação |
| **Poste** — Leva energia por cabo. | — | 40 | 1 placa de ferro, 1 placa de cobre | início |
| **Poste alto** — Leva energia por cabo bem longe: 30 m até outro poste alto (liga máquina só a 3 m). | — | 150 | 5 barra de aço, 5 placa de cobre, 2 pedra | Transmissão longa |
| **Torre sem fio** — Leva energia sem cabo, longe. | — | 120 | 20 placa de cobre, 10 circuito, 5 cristal lapidado | Energia sem fio |
| **Turbina de correnteza** — Energia do rio, sem combustível: vai na água corrente; rende menos na seca (verão) e mais com chuva. | gera até 150 kW | 200 | 20 placa de ferro, 10 engrenagem, 2 motor, 10 placa de cobre | Turbina de correnteza |
| **Gerador a fluido** — 2,4 MW queimando combustível de seiva (refinador) que chega pelo cano. | gera até 2400 kW · polui 45/min | 400 | 30 barra de aço, 20 tubo, 6 motor, 10 circuito | Combustível de seiva |

### Defesa

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Torre** — Atira nas aranhas (munição por braço). | usa 120 kW | 400 | 10 placa de ferro, 6 engrenagem, 5 placa de cobre | início |
| **Metralhadora** — 10 tiros/s com munição (braço traz). | — | 450 | 10 placa de ferro, 8 engrenagem, 4 barra de aço | Metralhadora |
| **Lança-foguetes** | — | 900 | 30 placa de ferro, 12 barra de aço, 2 motor, 10 circuito | Lança-foguetes |
| **Artilharia** | — | 1200 | 40 barra de aço, 20 liga leve, 4 motor, 4 processador | Artilharia |
| **Muro** — Barra aranhas. Arraste. | — | 350 | 5 pedra | início |
| **Muro de tijolo** — Muro com o dobro da vida. Arraste. | — | 700 | 5 tijolo | Muro de tijolo |
| **Muro de liga** | — | 1500 | 4 liga leve, 1 barra de aço | Muro de liga |
| **Muro de campo** | usa 10 kW | 800 | 2 liga leve, 4 circuito, 2 bateria | Muro de campo |
| **Mina de pulso** | — | 120 | 4 placa de ferro, 3 circuito, 1 bateria | Mina de pulso |
| **Gerador de escudo** | usa 200 kW | 500 | 20 barra de aço, 4 processador, 10 bateria, 6 cristal lapidado | Gerador de escudo |

### Clima

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Para-raios** | — | 300 | 6 barra de aço, 10 placa de cobre, 4 pedra | Para-raios |
| **Para-raios de cristal** | — | 450 | 10 barra de aço, 15 placa de cobre, 4 liga leve, 4 cristal lapidado | Para-raios de cristal |
| **Captador de carga** | — | 450 | 20 barra de aço, 30 placa de cobre, 10 circuito, 6 bateria, 8 tubo | Captador de carga |
| **Semeador de nuvens** | usa 300 kW | 400 | 20 barra de aço, 10 tubo, 2 motor, 4 processador | Semeadura de nuvens |
| **Defletor de vento** | usa 250 kW | 400 | 25 barra de aço, 10 liga leve, 4 motor, 2 processador | Defletor de vento |
| **Cúpula contra raios** | usa 400 kW | 900 | 40 barra de aço, 30 placa de cobre, 20 liga leve, 8 processador, 10 cristal carregado | Cúpula contra raios |
| **Regulador climático** | usa 1500 kW | 1200 | 60 barra de aço, 30 liga leve, 20 processador, 20 cristal carregado, 10 módulo de controle | Regulador climático |

### Drones

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Estação de drones** — 2×2 com energia e água pelo cano (sul): monta drones (placas, motor, circuitos) e os lança. No painel: reparo (solda o que as aranhas morderam, gasta placas), combate (caça aranhas) ou logístico (leva itens entre baús). | usa 150 kW | 500 | 10 barra de aço, 20 placa de ferro, 10 circuito, 2 motor, 6 tubo | Drones de reparo |
| **Baú de estoque** — Estoque dos drones logísticos: guarda o que sobra na garra e atende o requisitante quando nenhum provedor tem. | 1600 itens | 120 | 8 placa de ferro, 2 circuito, 1 liga leve | Drones logísticos |

### Lógica

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Sensor de esteira** — Ao lado da esteira, olhando para ela: conta os itens que passam e manda (itens/min) por um canal. | — | 60 | 3 placa de ferro, 2 circuito, 1 vidro | Rede lógica |
| **Sensor de tanque** — Peça de cano: lê o nível da rede (com o tanque) e manda (0–100%) por um canal. | — | 80 | 2 tubo, 2 circuito, 1 vidro | Rede lógica |
| **Comparador** — Liga ou desliga as máquinas, braços e bombas encostadas conforme o valor do canal (maior/menor que um número). | — | 80 | 4 placa de ferro, 3 circuito, 1 processador | Rede lógica |
| **Válvula** — Entre dois canos: só deixa o fluido passar acima ou abaixo de um nível (ou quando o comparador manda). | — | 100 | 3 tubo, 2 engrenagem, 1 motor, 1 circuito | Rede lógica |

### Proliferação

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Sensor de varredura** — 2×2 com energia (150 kW): revela os chunks em volta, 1 por minuto (até 6; 16 com a Varredura profunda), e marca os ninhos deles no mapa. | usa 150 kW | 450 | 20 placa de ferro, 10 engrenagem, 5 circuito, 2 cristal lapidado | Sensor de varredura |
| **Farol de cristal** — 1×1 com energia (30 kW): à noite acende uma luz de 10 m — mostra a fábrica, tira a névoa em volta e avisa quando aranhas entram na luz. | usa 30 kW | 150 | 6 placa de ferro, 2 circuito, 2 cristal lapidado | Farol de cristal |
| **Posto avançado** — 3×3 núcleo-filho: 150 kW sem cabo para as máquinas em volta, como o núcleo, e estoque próprio (3.200 itens, por braço): obras a até 32 m pagam primeiro com ele. | gera até 150 kW · 3200 itens | 1500 | 60 placa de ferro, 30 barra de aço, 20 engrenagem, 10 circuito, 4 processador, 2 núcleo de cristal | Posto avançado |
| **Lançador de sementes** — 3×3 com energia (600 kW): recebe o núcleo-semente por braço (boca sul) e o lança a até 400 m no rumo escolhido no painel; onde pousa nasce um posto avançado. | usa 600 kW | 900 | 60 barra de aço, 40 placa de cobre, 10 motor, 10 processador, 20 liga leve | Núcleo-semente |
| **Receptor de cápsulas** — 2×2 com energia (100 kW): recebe as cápsulas das colônias — 1 pacote gênese a cada 30 s de cada colônia — e guarda até 100 para os braços (saída ao norte). | usa 100 kW | 600 | 30 barra de aço, 20 placa de cobre, 4 motor, 10 circuito, 10 liga leve | Colônias |
| **Transportador quântico** — 3×3 com energia (500 kW): o braço põe itens na entrada (sul) e eles saem, sem trilho, no outro transportador do mesmo canal (A–D), 5 por segundo. | usa 500 kW | 800 | 40 liga leve, 20 processador, 10 cristal carregado, 60 placa de cobre, 40 barra de aço | Transportador quântico |
| **Silo de lançamento** — 3×3 com energia (1 MW): monta o foguete de proliferação — 100 partes (casco + 5 processadores quânticos por braço e 50 de propelente pelo cano) — e a carga-semente; lançar encerra a campanha. | usa 1000 kW | 3000 | 200 barra de aço, 100 liga leve, 40 processador, 20 motor, 100 placa de cobre | Silo de lançamento |

### Trilhos

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Trilho** — Trilho do trem. Arraste. | — | 200 | 2 placa de ferro, 1 pedra | Ferrovia |
| **Curva de trilho** — Curva de trilho. | — | 200 | 8 placa de ferro, 4 pedra | Ferrovia |
| **Fim de linha** — Fim da linha. | — | 200 | 3 placa de ferro | Ferrovia |
| **Trilho energizado** — Trilho reto com terceiro trilho: um poste perto energiza todas as peças encostadas. | usa 5 kW | 220 | 2 placa de ferro, 1 pedra, 2 placa de cobre, 2 fio de cobre | Locomotiva elétrica |
| **Estação** — Trem carrega e descarrega aqui. | — | 400 | 15 placa de ferro, 5 engrenagem | Ferrovia |
| **Bomba de estação** — Encoste as costas (braço de carga) na estação e ligue um cano na boca: enche ou esvazia o tanque dela (40 kW). | usa 40 kW | 150 | 6 placa de ferro, 6 tubo, 1 motor | Vagão-tanque |
| **Sinal** — Divide a linha em blocos. | — | 100 | 3 placa de ferro, 1 circuito | Ferrovia |
| **Sinal em cadeia** — Ao lado da linha, antes de um cruzamento: o trem só entra se a saída também estiver livre. | — | 100 | 3 placa de ferro, 2 circuito | Trem automático |
| **Trem** — Trem sobre um trilho reto. | — | — | 40 placa de ferro, 20 engrenagem, 10 tubo | Ferrovia |
| **Trem-tanque** — Trem com 2 vagões-tanque (25.000 de fluido cada) sobre um trilho reto. A bomba de estação enche ou esvazia. | — | — | 40 placa de ferro, 20 engrenagem, 30 tubo, 10 barra de aço | Vagão-tanque |
| **Trem elétrico** — Locomotivas elétricas: no dobro da velocidade sobre trilho energizado com energia, sem poluir (fora dele, devagar na bateria). | — | — | 40 placa de ferro, 20 engrenagem, 8 liga leve, 4 bateria, 4 motor | Locomotiva elétrica |

### Opções no painel da peça

- **Reparar:** 1 placa de ferro a cada 25 pontos de integridade que faltam.
- **Ligada / desligada:** desligada não consome nem trabalha.
- **Modo** (máquinas elétricas): Econômico 50% da velocidade, 40% da energia, 60% da poluição · Normal · Turbo 150% da velocidade, 200% da energia, 160% da poluição. Coletor e filtro limpam no ritmo da velocidade.
- **Limite do baú:** 25%, 50% ou 100% da capacidade.

## Dia, noite e estações

- Um dia dura 720 s de jogo (12 min). A noite fica com cerca de 38% do ciclo na primavera e no outono; o verão tem dias mais longos e o inverno, mais curtos.
- **As estações seguem o calendário real:** cada uma dura 7 dias de verdade e passa mesmo com o jogo fechado (um ano = 4 semanas). Isso pede planejamento: estoque e acumuladores para o inverno.
- O painel solar rende pela luz do dia e do clima (nada à noite). A turbina rende pelo vento, dia e noite. Fontes grátis (núcleo, sol, vento) são usadas antes do combustível; a sobra carrega os acumuladores, que devolvem quando falta.

- **Vento:** cada estação tem um rumo; a direção oscila ±40° em volta e rajadas atravessam o mapa. O lugar muda a força: +12% por nível acima do entorno (até +36%), +15% em campo aberto, praia e beira-mar, −30% em floresta e pântano, −6% por árvore plantada perto, −20% atrás de construção alta. A turbina fica parada abaixo de 25% de vento, chega ao máximo em 85% e acima de 115% põe as pás em bandeira (rende 40%). Veja o mapa do vento na visão de recursos (V duas vezes).

- **Primavera:** vento de leste, dia normal, secura 20% (fogo), clima mais provável: Chuva, Nublado.
- **Verão:** vento de nordeste, dia mais longo, secura 85% (fogo), clima mais provável: Céu limpo, Tempestade.
- **Outono:** vento de oeste, dia normal, secura 50% (fogo), clima mais provável: Nublado, Tempestade.
- **Inverno:** vento de sul, dia mais curto, secura 10% (fogo), clima mais provável: Neblina, Nublado.
