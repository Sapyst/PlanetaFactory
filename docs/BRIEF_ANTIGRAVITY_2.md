# Pedido 2 para o Antigravity: estudos dos modelos antigos do PlanetaFactory

Responda sempre em português do Brasil. Quem pede é Sapyst (trate no feminino).

## Contexto
É a mesma tarefa do pedido anterior (`docs/BRIEF_ANTIGRAVITY.md`): leia esse arquivo de novo e siga **as mesmas regras de
arte, regras técnicas e limites**. Você escreve só estudos; outra pessoa converte e integra.
Pasta do projeto: `/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory`

Faltam 5 modelos que ainda estão no visual antigo, sem textura. Eles aparecem muitas vezes na tela, então **aqui o
limite de peso é pra valer** e é bem menor que o dos estudos anteriores. Detalhe vem da textura suja e da silhueta, não
de triângulo. O conversor assa a textura a partir do estudo: pode modelar rico, mas com poucas peças e formas limpas, para
ele reduzir sem virar lasca (a redução transformou placas finas em cacos em outras peças: prefira volumes com espessura
real e faces voltadas para fora, porque o jogo não desenha o verso).

## Lista, nesta ordem

### 1. `estudo_plataforma_agua.py` — plataforma sobre a água (1×1), até 600 triângulos
Deque blindado de 1 tile com 4 pilares que descem até o leito. O jogo põe uma sob **cada tile** construído sobre a água, então:
- ocupa 1,00×1,00 m exatos no topo e **emenda sem fresta com as vizinhas** em qualquer direção (nada de borda que se repita feia em grade);
- altura total 1,9 m: no estudo, **origem nos pés (z = 0) e topo do deque em z = 1,9** (o jogo desce a peça 1,9 m, para o topo ficar no nível do chão); confira no modelo atual em `arte/modelos/logistica/apoio/plataforma_agua/`;
- estática, sem animação. Marcas d'água e cracas na parte baixa dos pilares, ferrugem, chapa de piso gasta.

### 2. `estudo_ponte_agua.py` — ponte de esteira/cano/trilho sobre a água (1×1), até 400 triângulos
Vão estreito no sentido do fluxo (sul–norte) e 2 pilares nas laterais; mesma altura de 1,9 m e mesma linguagem da plataforma.
Emenda sem fresta com a próxima ponte no eixo norte–sul. Estática. Largura livre no meio para a esteira passar por cima.

### 3. `estudo_poca_seiva.py` — poça de seiva (1×1), até 300 triângulos
Fluido do planeta, onde a bomba é posta por cima. Tamanho cerca de 0,82×0,83 m e no máximo 0,09 m de altura, porque a bomba senta nela.
Seiva escura e viscosa, com borda de crosta seca e terra manchada. **O jogo não tem transparência**: o brilho molhado vem do material.
Pode ter 1 ou 2 bolhas que incham e estouram no laço de 4 s (objetos separados, baixo peso).

### 4. `estudo_aranha.py` — aranha mecânica, inimigo principal
O jogo monta a aranha por código (6 pernas com IK), então o estudo tem de gerar **3 objetos separados, com estes nomes e origens exatas**:
- `aranha_corpo`: até 1.500 triângulos. Cerca de 1,0×1,96×0,6 m. Origem no chão, sob o centro.
- `aranha_femur`: até 200 triângulos. **0,70 m ao longo de +X**, origem no quadril.
- `aranha_tibia`: até 150 triângulos. **0,90 m ao longo de +X**, origem no joelho, e a ponta em x = 0,90 é o pé.

Não mude os comprimentos nem as origens, senão as pernas descolam. Confira os atuais em `arte/modelos/inimigos/aranha/` e os pontos dos quadris em
`jogo/inimigos/marcha_aranha.gd` (`QUADRIS`, com os quadris a `QUADRIL_Z` = 0,55 m do chão): o corpo tem de ter a articulação de cada perna nesses pontos.
No modo `foto`, monte uma prévia com as 6 pernas numa pose de andar, só para você conferir; no modo `-- nada`, deixe só as 3 peças soltas na origem.
Sem animação no estudo (o jogo anima). Aparência: predador mecânico gasto, placas de blindagem, hidráulica nas juntas, sensores, nada de bicho fofo.
Tem de ler como aranha de longe e ser **bem diferente das máquinas da jogadora** (outra paleta: não use o amarelo industrial).

### 5. `estudo_ninho_aranha.py` — ninho (3×3), até 5.000 triângulos
Construído pelas aranhas, gera novas aranhas e é o alvo prioritário, então precisa chamar atenção e parecer hostil.
Ocupa a área 3×3 sem passar dela; altura de 2 a 3 m. Sucata e minério fundidos num monte montado pelas aranhas, câmara central
com brilho pulsante, abertura por onde a aranha sai. Mesma paleta da aranha. Animação em laço de 4 s: pulso do brilho, peças que se mexem, fumaça (fumaça com nome `EFEITO`).

## Fora deste pedido
A cápsula de queda do núcleo já tem estudo: **não mexa nela** (a correção é na conversão, feita do outro lado).

## Ao terminar cada um
Acrescente uma linha em `arte/estudos/FEITOS_ANTIGRAVITY.md`, na mesma tabela: arquivo, tamanho, bocas, o que anima, pendências, e "—" na coluna "No jogo".
Só crie arquivos `estudo_<nome>.py` novos. Não mexa em `jogo/`, `para_jogo.py`, `conv_*.py`, outros estudos ou docs. Sem commit nem push. Um Blender por vez.
