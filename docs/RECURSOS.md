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
