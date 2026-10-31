# Pedido 3 para o Antigravity: ambiente e efeitos do PlanetaFactory

Responda sempre em português do Brasil. Quem pede é Sapyst (trate no feminino).

## O que é
Estudos e testes de **assets ambientais e efeitos visuais**. Você entrega estudos prontos e testados; outra pessoa só
implementa no jogo. **A grama fica de fora: já está boa.**

Pasta do projeto: `/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory`
Blender: `~/.local/share/Steam/steamapps/common/Blender/blender` (5.2) · Godot: `godot` (4.7.2, renderizador Mobile)

## Leia antes
1. `docs/BRIEF_ANTIGRAVITY.md` — as regras técnicas e de trabalho continuam valendo.
2. `arte/estudos/GUIA_ESTUDOS.md`, `base3d.py`, `mats.py`.
3. `jogo/dados/biomas.json`, `jogo/dados/recursos.json` e `jogo/dados/modelos.json` (dimensões atuais, categorias `mapa/*`).
4. `jogo/render/shaders/grama.gdshader` e `material_pf.gdshaderinc`, para ver o tom do jogo e como o vento age.
5. `arte/estudos/fotos/painel_final.jpg`, para ver como as estruturas estão no jogo: o ambiente tem de combinar com elas.

## Direção de arte
- Planeta **alienígena e natural**: a fábrica é a intrusa. O ambiente contrasta com ela: orgânico, irregular e sem rebite, sem o amarelo industrial.
- Realista e sujo, sem cara de desenho e sem chibi. Sem nada feito por humanos e sem nada "enxuto".
- Tem de ler de longe: a câmera do jogo fica de cima, entre 25 e 90 m. Avalie **sempre** por essa vista, não só de perto.
- **Efeito nunca pode parecer filtro de tela**, regra antiga dela. Efeito acontece num lugar do mundo e tem causa.

## Parte A: modelos, em Blender (`estudo_amb_<grupo>.py`)
Aparecem aos milhares, desenhados em lote. Por isso aqui **o limite de triângulos é rígido**:
- **Uma malha só por modelo**, sem peças móveis, sem armadura e sem animação: quem mexe é o shader.
- Volumes com espessura e faces para fora (o jogo não desenha o verso). **Sem transparência**: folha é malha opaca recortada no formato.
- Origem na base, no centro; Z para cima. O vento dobra pela altura: tronco embaixo e copa em cima, sem nada flutuando.
- Mantenha a área e a escala de referência atuais (`modelos.json`), salvo se propor outra e justificar.
- Cada variante tem de ser mesmo diferente, não a mesma árvore girada.

| Grupo | Modelos | Variantes | Limite por modelo |
|---|---|---|---|
| Árvores | acácia, bétula, carvalho, pinheiro, salgueiro, fungo de cristal | 6 de cada | 500 |
| Árvores soltas | árvore de campina (2), árvore morta | — | 400 |
| Plantas | arbusto, junco, flor luminosa, cacto de cristal, vitória-régia | — | 200 |
| Cogumelo gigante | a, b | — | 600 |
| Rochas | seixos, pedregulho, rocha na água, rocha grande | — | 250 |
| Montanhas | 3×3, 5×5 | — | 1.200 |
| Jazidas | areia, carvão, cobre, ferro, pedra, sílex, cristal | — | 300 |
| Itens na esteira | minério de ferro, minério de cobre, carvão, pedra, areia, sílex, cristal bruto, biomassa | — | 120 |

As jazidas devem indicar o minério pela cor e pela forma, de longe. Os itens passam aos milhares nas esteiras e têm de ser
reconhecíveis em tamanho pequeno.

Para cada grupo, além das fotos normais, entregue **uma foto de 30 m de altura com as variantes espalhadas sobre um chão parecido com o do jogo.**

## Parte B: efeitos, em Godot (`arte/estudos/efeitos/`)
Efeito precisa ser testado no motor. Crie **um projeto Godot próprio** nessa pasta, com renderizador Mobile, com uma cena por efeito,
cada uma com um disparo em laço e fundo neutro de dia e de noite. Só shaders e partículas procedurais, sem textura externa baixada.
Cada efeito tem de ser fácil de chamar: `tocar(origem, destino, cor...)` num script curto, sem depender de nada do jogo.

### Rastro do tiro, por arma
Metralhadora (traçante fino e rápido) · Torre de energia (feixe) · Lança-foguetes (rastro de fumaça e chama) ·
Foguete de enxame · Artilharia (granada em arco) · Munição perfurante · Munição carregada · Drone de combate.

### Impacto no alvo, por arma
Os mesmos acima, em três alvos: **aranha** (metal, faíscas), **chão** (terra e poeira) e **estrutura** (metal na chapa).
Mais: explosão de foguete, explosão de artilharia, disparo da mina de pulso (anel no chão que paralisa).

A cápsula ejetada a cada tiro **já existe no jogo: não refaça**. Só não cubra com fumaça demais.

### Brilhos e ambiente, com lógica de conceito
Cada um tem de ter um motivo no mundo, e você escreve o motivo no docstring. Exemplos: brilho sobre jazida de cristal, faísca de
fungo de cristal à noite, esporos perto de cogumelos, vaga-lumes na flor luminosa ao anoitecer, reflexo em água corrente, poeira em
chão seco com vento, vapor em poça de seiva, brasa em mato queimado. Pode propor outros com a mesma regra.

### Limites
- Até **200 partículas** por efeito de impacto e até **500** na explosão grande.
- Sem luz dinâmica em efeito pequeno. Só explosões e flash de disparo podem usar luz, curta e sem sombra.
- Testar **20 de cada efeito ao mesmo tempo** e anotar fps e ms por quadro.

## Testes e entregas
- Fotos de conferência para cada grupo; folha com a sequência de 4 quadros para cada efeito.
- Um painel único: `arte/estudos/fotos/painel_ambiente.jpg`, com todos os modelos e efeitos juntos, para ela não abrir um por um.
- Tabela em `arte/estudos/FEITOS_ANTIGRAVITY_3.md`: arquivo, o que é, triângulos ou partículas, ms medido, o que ficou pendente.
- Diga honestamente o que não conseguiu conferir (por exemplo, o movimento visto só em quadros).

## Regras de trabalho
- **Só crie arquivos novos** em `arte/estudos/` e `arte/estudos/efeitos/`. **Não mexa** em `jogo/`, `para_jogo.py`, `conv_*.py`, estudos existentes ou docs. Sem commit nem push.
- Um Blender ou um Godot por vez. Godot sempre com `flock /tmp/pf_godot.lock -c '...'` e com `--audio-driver Dummy`.
- **Outro agente trabalha no jogo ao mesmo tempo, e Sapyst pode estar jogando.** Não feche nem abra o jogo dela, não toque no save.
- Sem vídeo. Comece pelas árvores; depois siga a ordem das tabelas.
