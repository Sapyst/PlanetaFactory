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
- **Elementos:** Árvore, Arbusto, Pedregulho, Rocha grande

### Floresta fúngica
- **Jazidas:** Seiva (50%), Carvão (38%), Cobre (12%)
- **Elementos:** Cogumelo gigante

### Deserto de sílex
- **Jazidas:** Sílex (40%), Areia (40%), Cobre (20%)
- **Elementos:** Cacto de cristal, Pedregulho, Rocha grande, Morro

### Planalto rochoso
- **Jazidas:** Pedra (36%), Ferro (27%), Cobre (27%), Sílex (9%)
- **Elementos:** Pedregulho, Rocha grande, Morro, Montanha

### Campo de cristal
- **Jazidas:** Cristal (86%), Pedra (14%)
- **Elementos:** Cacto de cristal, Pedregulho, Rocha grande

### Pântano
- **Jazidas:** Carvão (67%), Seiva (33%)
- **Elementos:** Árvore morta, Rocha na água

### Cinzal
- **Jazidas:** Pedra (38%), Carvão (38%), Ferro (25%)
- **Elementos:** Árvore morta, Pedregulho, Rocha grande, Morro

## Águas

Rio, lago, lagoa, mar e oceano não aceitam construção; a praia aceita. Na visão de recursos cada água aparece com o nome em azul.

## Elementos naturais (remover rende)

| Elemento | Rende |
|---|---|
| Pedregulho | 6 × Pedra |
| Rocha grande | 20 × Pedra |
| Morro | 45 × Pedra |
| Montanha | 120 × Pedra |
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
| **Divisor** — Reparte itens em até 3 saídas. | — | 80 | 4 placa de ferro, 2 circuito | Eletrônica |
| **Junção** — Junta até 3 esteiras em uma. | — | 80 | 4 placa de ferro, 2 circuito | Eletrônica |

### Braços

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Braço** — Pega atrás e solta na frente, um item por vez. | usa 13 kW | 60 | 2 placa de ferro, 1 engrenagem | início |
| **Braço rápido** — Braço 2× mais rápido (gasta mais energia). | usa 46 kW | 60 | 2 placa de ferro, 2 engrenagem, 2 circuito | Eletrônica |
| **Braço longo** — Braço que alcança 2 tiles. | usa 20 kW | 60 | 3 placa de ferro, 2 engrenagem | Logística 2 |
| **Baú** — Guarda itens; braços põem e tiram. | 1600 itens | 100 | 4 placa de ferro | início |
| **Baú grande** — Baú 2×2: guarda 4× mais. | 6400 itens | 300 | 16 placa de ferro, 4 barra de aço | Armazenagem |

### Canos

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Cano** — Leva fluidos. Arraste. | — | — | 1 placa de ferro | Fluidos |
| **Cano em T** — Divide o cano em 3. | — | 50 | 2 placa de ferro | Fluidos |
| **Cano em cruz** — Cruza canos em 4. | — | 50 | 2 placa de ferro | Fluidos |
| **Bomba** — Tira seiva de uma poça. | usa 30 kW | 150 | 5 placa de ferro, 3 engrenagem, 2 tubo | Fluidos |
| **Tanque** — Guarda muito fluido. | 25000 de fluido | 500 | 20 placa de ferro, 4 tubo | Fluidos |

### Produção

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Extrator de cristal** — Extrai cristal da jazida e despeja na esteira. | usa 90 kW · polui 10/min | 300 | 10 placa de ferro, 5 engrenagem, 5 placa de cobre | início |
| **Broca** — Fura a jazida e despeja minério na esteira. | usa 90 kW · polui 10/min | 300 | 8 placa de ferro, 4 engrenagem, 5 pedra | início |
| **Fornalha** — Funde minério em placas (queima carvão). | polui 4/min | 200 | 10 pedra | início |
| **Montadora** — Monta peças por receita. | usa 150 kW · polui 3/min | 300 | 12 placa de ferro, 6 engrenagem, 6 placa de cobre | início |
| **Refinador** — Processa fluidos. | usa 420 kW · polui 6/min | 350 | 5 barra de aço, 10 tubo, 5 circuito | Refino de seiva |
| **Laboratório** — Pesquisa com pacotes. | usa 60 kW | 150 | 10 placa de ferro, 10 placa de cobre, 5 engrenagem | início |
| **Terraplenagem** — Libera Aplainar o chão em qualquer lugar. | — | 400 | 30 placa de ferro, 15 engrenagem, 40 pedra | início |

### Limpeza

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Coletor de lixo** — Aspira sujeira e óleo do chão em volta (raio 6). | usa 40 kW | 200 | 10 placa de ferro, 6 engrenagem, 4 placa de cobre | Limpeza |
| **Filtro de água** — Encostado na água: limpa a água suja em volta (raio 7). | usa 60 kW | 200 | 12 placa de ferro, 6 tubo, 4 engrenagem | Limpeza |
| **Viveiro** — Com seiva pelo cano, planta mudas em volta (raio 8) que viram árvores e limpam o ar e o chão. | usa 20 kW | 150 | 8 placa de ferro, 4 tubo, 6 vidro | Reflorestamento |

### Energia

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Gerador** — Queima carvão e gera energia. | gera até 900 kW (combustível) · polui 30/min | 200 | 10 placa de ferro, 5 tubo, 10 pedra | início |
| **Painel solar** — Energia do sol, sem combustível: nada à noite, menos com nuvem e chuva, mais no verão. | gera até 300 kW (sol: zero à noite) | 120 | 6 placa de ferro, 8 vidro, 3 circuito | Energia renovável |
| **Turbina eólica** — Energia do vento, sem combustível (rende mais com vento forte). | gera até 200 kW (vento) | 180 | 14 placa de ferro, 10 engrenagem, 2 motor | Energia renovável |
| **Acumulador** — Guarda a sobra de energia da rede e devolve quando falta. | guarda 80 MJ (até 500 kW) | 250 | 10 placa de ferro, 8 bateria, 4 circuito | Acumulação |
| **Poste** — Leva energia por cabo. | — | 40 | 1 placa de ferro, 1 placa de cobre | início |
| **Torre sem fio** — Leva energia sem cabo, longe. | — | 120 | 20 placa de cobre, 10 circuito, 5 cristal lapidado | Energia sem fio |

### Defesa

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Torre** — Atira nas aranhas (munição por braço). | — | 400 | 10 placa de ferro, 6 engrenagem, 5 placa de cobre | Defesa |
| **Muro** — Barra aranhas. Arraste. | — | 350 | 5 pedra | início |

### Trilhos

| Peça | Ficha | ♥ | Custo | Libera |
|---|---|---|---|---|
| **Trilho** — Trilho do trem. Arraste. | — | 200 | 2 placa de ferro, 1 pedra | Ferrovia |
| **Curva de trilho** — Curva de trilho. | — | 200 | 8 placa de ferro, 4 pedra | Ferrovia |
| **Fim de linha** — Fim da linha. | — | 200 | 3 placa de ferro | Ferrovia |
| **Estação** — Trem carrega e descarrega aqui. | — | 400 | 15 placa de ferro, 5 engrenagem | Ferrovia |
| **Sinal** — Divide a linha em blocos. | — | 100 | 3 placa de ferro, 1 circuito | Ferrovia |
| **Trem** — Trem sobre um trilho reto. | — | — | 40 placa de ferro, 20 engrenagem, 10 tubo | Ferrovia |

### Opções no painel da peça

- **Reparar:** 1 placa de ferro a cada 25 pontos de integridade que faltam.
- **Ligada / desligada:** desligada não consome nem trabalha.
- **Modo** (máquinas elétricas): Econômico 50% da velocidade, 40% da energia, 60% da poluição · Normal · Turbo 150% da velocidade, 200% da energia, 160% da poluição. Coletor e filtro limpam no ritmo da velocidade.
- **Limite do baú:** 25%, 50% ou 100% da capacidade.

## Dia, noite e estações

- Um dia dura 720 s de jogo (12 min). A noite fica com cerca de 38% do ciclo na primavera e no outono; o verão tem dias mais longos e o inverno, mais curtos.
- **As estações seguem o calendário real:** cada uma dura 7 dias de verdade e passa mesmo com o jogo fechado (um ano = 4 semanas). Isso pede planejamento: estoque e acumuladores para o inverno.
- O painel solar rende pela luz do dia e do clima (nada à noite). A turbina rende pelo vento, dia e noite. Fontes grátis (núcleo, sol, vento) são usadas antes do combustível; a sobra carrega os acumuladores, que devolvem quando falta.

- **Primavera:** dia normal, secura 20% (fogo), clima mais provável: Chuva, Nublado.
- **Verão:** dia mais longo, secura 85% (fogo), clima mais provável: Céu limpo, Tempestade.
- **Outono:** dia normal, secura 50% (fogo), clima mais provável: Nublado, Tempestade.
- **Inverno:** dia mais curto, secura 10% (fogo), clima mais provável: Neblina, Nublado.
