# Pedido para o Antigravity: estudos 3D que faltam no PlanetaFactory

Responda sempre em português do Brasil. Quem pede é Sapyst (trate no feminino).

## O que é
PlanetaFactory é um jogo de fábrica 3D (Godot). Cada estrutura do jogo nasce como um **estudo**: um script Python
para o Blender (`arte/estudos/estudo_<nome>.py`) que monta o modelo inteiro por código — geometria, materiais sujos,
animação de trabalho e bocas de entrada/saída. Depois **outra pessoa** converte o estudo para o jogo e liga os
sistemas. **Seu trabalho é só escrever os estudos.**

Pasta do projeto: `/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory`
Blender: `~/.local/share/Steam/steamapps/common/Blender/blender` (5.2)

## Leia antes de começar (obrigatório)
1. `arte/estudos/GUIA_ESTUDOS.md` — premissa, o que Sapyst exige, regras técnicas. **Siga à risca.**
2. `arte/estudos/base3d.py` e `arte/estudos/mats.py` — peças prontas (caixa, cil, tubo, viga, mangueira, materiais
   com pintura/ferrugem/sujeira).
3. Exemplos aprovados: `estudo_fornalha.py` (o modelo de tudo: fogo, fumaça, câmera, modos), `estudo_montadora.py`,
   `estudo_silo.py`, `estudo_para_raios.py`, `estudo_drones_modelo.py`, `estudo_terraplenagem.py`.
4. `arte/CATALOGO.md` e `docs/ARVORE_TECNOLOGIA.md` — tamanho em tiles, bocas (entrada/saída de item e fluido) e
   função de cada estrutura. Se a estrutura não estiver no catálogo, use o que a árvore diz e escolha um tamanho
   coerente (1×1, 2×2 ou 3×3), anotando no docstring.

## Resumo das regras de arte (estão no guia; repito porque já foram recusadas antes)
- **Não há humanos.** Nada de cabine, assento, volante, escada, guarda-corpo, porta de gente. É uma IA que se
  constrói sozinha: mecânica pesada e gasta + fenômeno "logicamente surreal" (campo, levitação, ressonância, cristal
  que pulsa, geometria perfeita demais).
- **Nunca "enxuto":** detalhe desde o berço — tubos, pistões (camisa presa numa peça, haste na outra, mangueira
  chegando), cabos em feixes, canos que vêm de algum lugar e vão para algum lugar, escoamento, fumaça, vapor.
- **Rústico e sujo:** pintura lascada, ferrugem escorrendo, óleo, fuligem, remendos aparafusados, chapa trocada de
  outra cor, número de série apagado, poeira em cima, lama embaixo.
- **Silhueta que lê como a máquina que é**, de longe.
- **Nada atravessando nada** sem ser encaixe real. **Canos parecem canos** (muitos lados, suavizados, flanges,
  cotovelos redondos).
- **Armas:** cada tiro ejeta uma cápsula modelada, com fumacinha.

## Regras técnicas para o estudo funcionar no conversor
- Mesma estrutura dos exemplos: `read_factory_settings` → `base3d.iniciar()`, animação em laço de **96 quadros a
  24 qps** (4 s), modos lidos depois de `--` (`foto`, `teste`, ...). **Qualquer outro modo (ex.: `-- nada`) só monta
  a cena e sai sem renderizar** — o conversor roda assim.
- Estrutura ocupa a área de tiles inteira, centrada na origem (1 tile = 1 m; x leste, y norte). Bocas de esteira/braço
  na borda certa; **bocas de cano a 0,35 m de altura**, no eixo do tile.
- Chão, luzes, câmera e efeitos de cena (fumaça solta, poeira, volumes) com nome começando por `EFEITO` ou fora da área
  da estrutura — o conversor descarta isso. Peças que se mexem devem ser objetos separados (o conversor detecta o
  movimento). Vidro é removido no jogo: não dependa dele para a silhueta.
- Volume nunca com escala ~0 (o Blender aborta): esconda com `hide_render` em quadro-chave.
- Peso: mire em **3k–8k triângulos** no modelo final (o conversor decima), sem overdoing.

## Como trabalhar
- **Um estudo por vez, um Blender por vez.** O PC é um só, e outro agente também pode estar rodando o Blender em
  outro lote: **nunca rode dois Blender ao mesmo tempo.**
- Fotos só para conferir: `blender -b --python estudo_<nome>.py -- foto` (em primeiro plano, com `timeout`). Olhe cada
  foto, corrija até ficar bom e sem interpenetração. **Não rode vídeo.** Não espere com `while pgrep -f ...`.
- **Só crie arquivos novos `arte/estudos/estudo_<nome>.py`** (e as fotos, que ficam fora do git). **Não mexa** em
  `jogo/`, `para_jogo.py`, `conv_*.py`, outros estudos, docs ou configurações. **Não faça commit nem push.**
- Docstring no topo de cada estudo, como nos exemplos: o que é, tamanho, bocas, peças, animação, uso.
- Ao terminar cada estudo, escreva uma linha em `arte/estudos/FEITOS_ANTIGRAVITY.md` (crie se não existir):
  nome do arquivo, tamanho em tiles, bocas, o que anima, o que ficou pendente.

## Lista (nesta ordem; confirme nomes e funções em docs/ARVORE_TECNOLOGIA.md)
O lote 16 (trilhos e lógica) **já está sendo feito por outro agente — não faça.**

**Lote 17 — proliferação**
1. sensor de varredura (destrava a artilharia — prioridade)
2. farol de cristal
3. posto avançado
4. lançador de sementes
5. receptor de cápsulas
6. transportador quântico
7. silo de lançamento

**Lote 13 — energia I**
8. poste alto
9. turbina de correnteza (fica na água corrente)
10. gerador a fluido
11. painel solar 2
12. acumulador 2

**Lote 10 — produção I**
13. montadora 2 (prioridade: hoje o pacote de tempestade sai na montadora comum)
14. refinador 2 (prioridade: destrava a estação de tratamento)
15. fornalha de aço
16. fornalha elétrica
17. broca grande
18. laboratório 2

**Lote 14 — energia II**
19. turbina alta (prioridade: destrava o defletor de vento)
20. acumulador de cristal
21. reator de cristal
22. reator de fusão
23. núcleo de singularidade

**Lote 11 — produção II**
24. forja quântica (prioridade: destrava o regulador climático)
25. fundição de cristal
26. montadora 3
27. montadora quântica
28. extrator ressonante
29. broca de núcleo
30. laboratório quântico
31. irradiador de módulos

Para as versões "2/3" de máquinas que já existem (montadora, refinador, laboratório, acumulador, painel solar),
**parta do estudo da versão 1** (`estudo_montadora.py`, `estudo_refinador.py`, `estudo_laboratorio.py`,
`estudo_acumulador.py`, `estudo_painel_solar.py`) para manter a família reconhecível: mesma linguagem, mais robusta,
mais peças e o toque da IA mais forte a cada nível. Copie para um arquivo novo; não altere o original.
