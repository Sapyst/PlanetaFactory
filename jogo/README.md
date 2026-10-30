# PlanetaFactory — código do jogo (Godot 4.7)

Projeto Godot separado da arte. Toda regra numérica mora em `dados/*.json`; a arte (`../arte`) é copiada para
`assets/` por `ferramentas/sincronizar_arte.py`, que também gera `dados/modelos.json` (área, portas, partes).

## Rodar
```bash
godot --path jogo                       # abre a demo (mundo + mini-fábrica + aranhas)
jogo/ferramentas/testar.sh              # importa e roda todos os testes sem janela
jogo/ferramentas/testar.sh aranha       # só os testes cujo arquivo contém "aranha"
godot --headless --path jogo --quit-after 400          # roda a demo sem janela (pega erro de execução)
godot --path jogo --write-movie /tmp/q.png --fixed-fps 30 --quit-after 70 -- camera 13 -2 14   # foto
```
godot --path jogo --write-movie /tmp/r/q.png --fixed-fps 30 --quit-after 142 -- camera -3 2 11 roteiro construir   # teste visual com cliques injetados
godot --path jogo --write-movie /tmp/a/q.png --fixed-fps 30 --quit-after 200 -- roteiro ataque   # também: trem, poluicao, toque, painel
godot --headless --path jogo --fixed-fps 30 --quit-after 4000 -- acelerar 8 relatorio            # estado a cada 30 s de jogo
```

## Modos, salvar e progressão
- Menu inicial (`cenas/menu.tscn`): **Continuar**, **Novo jogo** (núcleo no spawn + kit inicial; construir custa itens do
  núcleo, remover devolve, limpar árvore/rocha rende material; pesquisa libera peças e receitas), **Demonstração**
  (fábrica pronta, tudo liberado, sem custo, não salva) e **Configurações** (volumes, tamanho da interface, sombras,
  autosalvar). Esc / botão Menu = pausa (salvar, carregar, configurações, sair).
- Salvo em `user://salvos/partida.sav` (texto; grava em .tmp e troca): a cada 2 min, ao fechar e quando o Android
  manda o app para o fundo. Núcleo destruído = derrota (o salvo é apagado).
- Pesquisa (botão Pesquisa / T): laboratório com energia gasta pacotes de pesquisa (montadora: cristal lapidado +
  engrenagem). Árvore e custos em `dados/progressao.json`.

## Energia por fios
Só se põe postes; os fios aparecem sozinhos (`energia/fiacao.gd`): poste ↔ poste até 9 m (5 vizinhos mais perto),
poste ↔ gerador e máquina até 5 m da borda. Máquina já ligada não troca de poste; no painel dela: "aceitar 1/2/3
fontes". Remover um poste religa quem ficou sem. Fantasma do poste mostra os fios que vai criar e o anel de 9 m.
**Torre sem fio** (pesquisa "Energia sem fio"): liga torres até 40 m e máquinas até 14 m, feixe ciano em vez de cabo.

## Fontes, acumulador e opções das peças
- `energia/rede_energia.gd`: em cada rede as fontes **grátis** (núcleo, painel solar, turbina eólica) entram primeiro;
  o gerador só queima carvão para cobrir o que falta. Sobra carrega os **acumuladores** (até `acumula_kw`), falta
  descarrega. `estat` por rede: pode gerar, gera, demanda, consumo, carga (+ carregando / − descarregando), acumulado.
- Painel solar: `energia_kw × luz do dia × luz do clima` (nada à noite). Turbina: `energia_kw × (0,05 + 0,95 × vento)`.
- Peça no mapa guarda as opções: `desligada`, `modo` (`eco`/`normal`/`turbo` → `Fabrica.MODOS`: velocidade, energia,
  poluição) e `limite` do baú (fração de `capacidade_itens`). **Reparar** custa 1 placa de ferro por 25 de integridade.
- Ficha técnica (`BarraConstrucao.ficha`) no botão da peça; painel da peça mostra integridade, armazenamento, geração
  e a rede. Tabela completa: `docs/RECURSOS.md` (gerado de `dados/`).
- Acumulador: o cristal do meio acende com a carga e as bobinas soltam faíscas (`render/arcos_eletricos.gd`: fitas em
  cruz, sem virar para a câmera), mais ainda carregando ou descarregando. Cristais das máquinas brilham fraco só
  trabalhando (`instance uniform trabalho` no `material_pf.gdshader`, comandado pelo `Animador`).

## Dia, noite e estações
- `Clima.hora` (0 = meia-noite) anda num ciclo de `dia_s` (720 s). `luz_dia()` rende o painel solar; `DesenhoClima`
  anda o sol de leste a oeste, deixa a luz alaranjada no fim da tarde e à noite troca para lua azulada fraca (a troca
  acontece com as duas apagadas no horizonte); céu, ambiente e névoa escurecem para azul-noite. HUD mostra período e hora.
- **Estações pelo calendário real** (`tempo_real`): 7 dias reais cada (`estacao_s`), passam com o jogo fechado.
  Cada uma muda a duração do dia (`dia_extra`), a secura (fogo) e os pesos do clima.
- Fotos: roteiros param o relógio ao meio da manhã; `-- hora 0.0` fotografa à meia-noite; `-- ciclo` deixa andar.

## Vento
- `Clima`: cada estação tem um rumo predominante (`vento_de` em `clima.json`); a direção do momento oscila ±40° em
  volta dele e vira devagar na troca de estação. **Rajadas**: frentes de vento mais forte (+18 a +43%) que nascem a
  barlavento de onde a câmera olha e atravessam o mapa (`vento_em(p)`); a grama e as árvores se curvam quando passam.
  `vento_medio` = média móvel de 10 min de jogo (vai no save).
- `ambiente/vento_local.gd`: fator do lugar — alto +12% por nível acima do entorno (até +36%), baixada até −24%,
  campo aberto/praia/beira-mar +15%, floresta/pântano −30%, árvores plantadas −6% cada, a sotavento de construção
  alta e larga −20%. Números em `ambiente.json` "vento_local".
- Turbina: rende pelo vento do lugar dela (clima × lugar × rajada) numa curva — parada abaixo de 25%, sobe até 85%,
  plena até 115%, acima disso pás em bandeira (40%, protege). A nacele vira devagar para encarar o vento.
- Poluição do ar: o que vaza do chunk vai 70% vento abaixo (`vento_a_favor`), o resto para os 4 lados.
- Fogo já corria a favor do vento; chuva já caía inclinada; grama e árvores agora inclinam na direção do vento.
- Visão de recursos: V de novo liga a camada **Vento** — mapa de calor do vento médio de cada lugar, setas no chão
  na direção média e a ficha do tile com "vento médio aqui". Roteiros: `vento`, `turbina`.

## Árvores por receita
- `arte/blender_scripts/arvores.py`: cada espécie é uma receita (altura, tronco, galhos, forma e folha da copa) e cada
  uma das 6 variações sai de uma semente: carvalho, bétula, pinheiro, salgueiro, acácia e fungo-cristal (36 modelos,
  até 400 triângulos, cabem em 1 tile). Tronco e galhos existem de verdade embaixo da copa.
- No mapa os biomas sorteiam a espécie (`arv_carvalho`) e `Distribuicao.obstaculo` escolhe a variação pelo tile
  (`arv_carvalho_3`); `Distribuicao.especie()` volta para a espécie (rendimento, nome, madeira no fogo).
- Folhagem com material próprio (`P_Folha*`, mantido pela texturização) e perfil de estação no shader
  (`Materiais.PERFIL_FOLHA`, global `estacao_atual`): caducas amarelam/alaranjam no outono, perdem a folha e ficam
  nuas no inverno, brotam verde-claro na primavera; salgueiro amarela no inverno; acácia seca e perde metade no
  verão; pinheiro e fungo-cristal não mudam. Cada árvore muda no seu tempo (sorte por instância + onda pelo mapa).
- Balanço: inclinam para onde o vento sopra, mais na ventania e quando a rajada passa.
- Fogo em etapas: a copa queima primeiro (folhas somem), depois o tronco carboniza. Fogo curto deixa a árvore de pé,
  queimada (`MapaOcupacao.arvores`), que rebrota na primavera; fogo de 18 s ou mais derruba a árvore carbonizada
  vento abaixo (animação de 1,4 s; desvia de construção; se não houver saída, cai em cima e tira 40 de vida).
  Árvore queimada rende 2 carvões; tronco caído, 3. Roteiros: `arvores` (com `-- estacao E F`), `queimada`.

## Sujeira, consequências e limpeza
- `ambiente/ambiente_vivo.gd`: máquinas sujam o chão em volta, vazam óleo, despejam na água; enxurrada leva a sujeira
  para rios e lagos. **Consequências:** bomba de seiva com poça contaminada rende menos e se desgasta; chão sujo perto
  do ninho deixa as aranhas furiosas (nascem mais rápido, atacam em grupos menores, mais longe, mais fortes; olhos
  mais vermelhos).
- **Limpeza** (pesquisas Limpeza e Reflorestamento): coletor de lixo aspira sujeira e óleo num raio de 6; filtro de
  água (encostado na água) limpa a água suja; viveiro transforma seiva em mudas plantadas em volta (a 3+ tiles de
  construção), que crescem até árvore e limpam o chão e o ar.

## Chão de fábrica
Em volta de cada construção o chão vira piso de concreto (espalha 2 tiles, borda irregular e suave); zona de
minério nunca vira piso. Cristais, grama e seixos debaixo de construção (ou no piso) não aparecem.

## Esteira elevada
Botão **Nível** (N, PageUp/PageDown): chão, 0,5 m, 1,0 m. "Rampa sobe" sobe do nível atual (e o nível sobe junto);
"Rampa desce" desce. O traço elevado planeja pilares nos cantos da grade (aparecem no fantasma); passa por cima de
esteira/trilho (baixos) e não de máquina; nada alto pode ser construído debaixo depois. Remover leva os pilares junto.

## Fluidez (câmera)
Mapa gerado em segundo plano (WorkerThreadPool, até 3 chunks ao mesmo tempo, com cache por chunk na geração) e
montado 1 por quadro; pré-carrega 1 chunk além da vista e só descarrega a 2. Câmera desliza com inércia.
Medido arrastando a câmera 18 m/s (`-- modo demo roteiro panorama`): antes 71 quadros > 33 ms e picos de 95 ms;
depois 0 quadros > 33 ms. Celular: 3D a 70% da resolução, sem sombra, sem brilho; aranhas só desenhadas perto da
vista. Contador de FPS embutido (ligado por padrão na fase de testes; Configurações desliga).

## Interface (reforma 0.12)
- Pesquisa em tela própria (`interface/tela_pesquisa.gd`): a árvore de tecnologia inteira (`dados/arvore.json`, 166
  nós, gerado por `ferramentas/gerar_arvore.py` de `docs/ARVORE_TECNOLOGIA.mmd` + tabelas do `.md`) em três faixas de
  era (chapa com listras no título), colunas por pré-requisito dentro da era, linhas ligando (verde = feito). Nós são
  placas `Tema.botao_cor_estilo`; tipo no nó (■ estrutura, ⚗ receita, ▲ melhoria, ∞ infinita, ★ objetivo). Só as
  pesquisas de `progressao.json` se pesquisam; o resto é "em breve". Zoom: pinça, Ctrl + roda, gesto do trackpad, − e +.
- Encardido: cada estrutura suja com o tempo (`AmbienteVivo.encardido`, 0..1; parada leva `encardido.cheio_s`,
  trabalhando e em chão sujo vai mais rápido) e a chuva lava (`chuva_limpa_s`), recomeçando o ciclo; vai no save. O
  valor vai no canal R do `fogo_mapa` e o `material_pf` cobre a estrutura de lama marrom (pé, frestas, escorridos) e
  pó claro (em cima), mais fosca. `-- roteiro encardido` fotografa limpa, meio suja e imunda.
- Melhorias: `bonus` na pesquisa (`progressao.json`), somado por `Pesquisa.bonus(chave)`; hoje lidos:
  `dano_torre_energia` e `dano_bala` (Colonia, tiro da torre) e `velocidade_pesquisa` (laboratório). `test_arvore`
  confere que toda chave de bônus tem quem a leia e que a árvore bate com as pesquisas jogáveis.
- Painel de detalhe como gaveta: do status até a borda de baixo, a lista rola dentro (nunca passa da tela). Em
  máquinas, cabeçalho com ícone, receita em casas (`interface/casa.gd`: número = o que tem; borda vermelha = falta),
  saída e barras de progresso e energia. Laboratório: botão "Abrir a pesquisa".
- Status do canto compacto (hora/clima, núcleo, pesquisa); tocar abre tudo.
- Modo construção: faixa listrada no alto dizendo o que a mão faz, com Sair; grade 1×1 no chão em volta do cursor.
- Estilo de fábrica (`interface/tema.gd`, texturas geradas por código): chapas grafite gastas com chanfro e rebites,
  filete de cobre, listras de perigo amarelo-sujo e preto na faixa e no Sair; paleta por situação (`Tema.COR`:
  destaque, perigo, sucesso, energia, pesquisa, água...) e por categoria (`Tema.CORES_CATEGORIA`, ícones tingidos).
- Ícones dos itens (`arte/icones/itens`, `icones.py -- itens`) para as casas.
- Torre de defesa básica liberada desde o começo: puxa 120 kW da rede até guardar 6 MJ, cada tiro gasta 0,05 MJ;
  munição vira reserva (pesquisa "Munição").

## Toque (celular primeiro)
- Toque × arrasto pelo dedo em milímetros reais (`interface/toque.gd`, 3,2 mm), não em pixels da tela de 720.
- Câmera: o chão fica preso embaixo do dedo (`CameraJogo.arrastar_tela`), sem atraso; pinça aproxima em volta do
  meio dos dedos (`zoom_em`); com o dedo na tela não há inércia, e soltar com o dedo parado não desliza.
- Listas (peças, painel de detalhe): `RolagemToque` rola arrastando em qualquer ponto (também sobre os botões), com
  embalo; o botão embaixo do dedo não é apertado se o toque virou arrasto (`RolagemToque.so_clique`).
- Pressionar e segurar 0,5 s = clique direito do mouse (larga traço, holograma e peça; vibra).
- Celular: interface 1,35× por padrão; tela estreita (< 1300 de largura lógica) põe as ferramentas só com ícone e
  estreita os painéis; a coluna de categorias cabe na altura. `-- roteiro telas celular` confere que nada passa da
  borda em 20:9, 16:9 e 4:3; `-- roteiro dedo celular [lista_cheia]` injeta toques e imprime o resultado.
- Categorias com ícones de símbolo em vetor (`assets/icones/categorias/*.svg`).

## Oval de visão, névoa e desempenho da grama
- `ambiente/visao.gd` (Visao): a tela vista como um oval deitado no chão, centrado no ponto olhado e do tamanho do
  zoom. Dentro, tudo desenha e anima; a borda é um degradê; fora, névoa escura (`aplicar_visao` em
  `clima.gdshaderinc`: chão, estruturas, vegetação). Fora do oval: objetos dos chunks escondidos (árvores, pedras,
  enfeites), grama some, Animador parado, fumaça das máquinas e chamas do fogo caladas, aranhas só na lógica, faíscas
  do acumulador paradas. A simulação continua igual — é só desenho.
- `ambiente/descoberta.gd`: o que já passou dentro do oval fica descoberto (células 2×2 tiles, no save); fora do oval,
  o descoberto aparece escuro e sem cor, o nunca visto quase preto — mascara a borda do mapa carregado.
- Grama em quadrantes de 16×16 m e duas camadas (`DesenhoChunk.ajustar_grama`): esparsa (1/3) até 40 m, detalhe
  (2/3) até 16 m com degradê; quadrante longe ou fora do oval não vai para a GPU. Medido (`-- roteiro medir`, câmera
  a 60 m, RTX): GPU 9,2 → 3,4 ms e 17,5 → 6,9 milhões de triângulos; densidade do celular 3,0 → 1,6 ms.
  `-- roteiro inventario` lista quem soma os triângulos.
- Árvores: cada chunk usa 3 das 6 variações de cada espécie (`Distribuicao.variacao_arvore`): 562 → 468 chamadas.
- Celular: sombra em 2 cascatas (em vez de 4) e até 60 m.
- Céu: só recebe cor nova quando a diferença se vê, e o reflexo é refeito aos poucos (Sky incremental).
- Sem música (só efeitos).

## Desempenho (medido: `testes/test_zdesempenho.gd` e `-- modo demo roteiro estresse`)
2 140 peças, 4 400 itens, 60 aranhas, 20 torres: passo de simulação ≈ 0,1 ms (fábrica) + 0,7 ms (aranhas/torres);
remontar a fábrica inteira ≈ 20 ms por construção. Desenho: esteiras/canos/trilhos em lote (MultiMesh por chunk:
~500 chamadas de desenho com 2 000 peças). O que mais pesa é posicionar os itens das esteiras (GDScript): até
~10 ms com 8 000 itens na tela — por isso só redesenha a 30 Hz, recorta o que está fora da tela e esconde os itens
com o zoom acima de 50 m. Se precisar de mais, é essa parte (não a simulação) que vale passar para C++.

## Android
`godot --headless --path jogo --export-debug "Android" jogo/export/PlanetaFactory-0.2.0.apk` (arm64, Vulkan Mobile,
paisagem, assinado com a chave de depuração em ~/.local/share/archivys_keys). Testado no emulador (x86_64, versão de
teste com OpenGL; o Vulkan do emulador sem janela não apresenta quadros): menu, jogo novo e construir com o dedo ok.

## Som
`ferramentas/gerar_sons.py` sintetiza os efeitos e a trilha (assets/sons); `nucleo/som.gd` toca (posicionado no
mundo, com intervalo mínimo por som).

## Fábrica do jogador
Tudo que se constrói funciona — a mini-fábrica da demo é só um mapa pronto rodando na mesma `Fabrica`.
- Esteira entrega na porta de entrada da máquina em que termina; esteira que termina na lateral de outra entra nela.
- Saída de máquina (porta) põe na esteira em frente. Braço: pega atrás, solta na frente, só pega o que o destino aceita.
- Logística da era base (fase 2.2b): **Esteira rápida** (`logistica_3`): as mesmas peças com `"classe": 2` na estrutura
  (`Construtor.CLASSES_ESTEIRA`; modelos `<peça>_rapida`, faixa vermelha; regra própria em estruturas.json), 3,75 m/s,
  passagem até 6 tiles livres (só liga entrada e saída da mesma classe). Trocar de classe no meio da linha parte o
  caminho em dois, ligados pela ponta (`elos` em `Fabrica._montar_esteiras`); traçar uma classe por cima da outra
  troca a peça (devolve o custo da velha, cobra a nova). **Braço com filtro**: até 5 itens (`filtro_max`), escolhidos
  no painel; os outros braços pegam o que o destino aceitar. **Divisor com filtro**: `filtro_item` sai só pela
  `saida_filtro`; o resto tenta a `prioridade` primeiro (Frente/Direita/Esquerda no painel; sem = rodízio).
  **Silo de granel** 3×3: armazém de 20.000 de um tipo só (`um_tipo`). **Cano subterrâneo**: a entrada liga na
  primeira saída alinhada à frente, mesma rotação, até 9 tiles livres — uma rede de fluido só.
- Água e química (fase 2.3): fluidos em `dados/fluidos.json` (`agua`, `agua_limpa` — serve onde se pede água —,
  `seiva`; `Registro.fluido_serve`). **Bomba d'água** 2×2 (`tomada_agua`: água encostada no lado sul do modelo,
  `MapaOcupacao.tiles_da_tomada`; água suja na tomada rende menos), **coletor de chuva** e **condensador de neblina**
  (`Fabrica.chuva`/`neblina` vêm do clima → `Maquina.clima`; 0 = `ESPERANDO_CLIMA`; `tanque_fluido` = tanque interno),
  **filtro** com `transborda` (solta água limpa com a pesquisa; sem cano não trava), **supressor de incêndio**
  (`AmbienteVivo._supressores`: apaga o fogo no raio e protege a vegetação; `Fabrica.jatos` → jato em `Efeitos`).
  Receitas refrigeradas (+50%), resina, pacote químico e ecológico no refinador; saída de fluido de receita que não
  solta fluido vira 2ª entrada (resina: seiva numa boca, água na outra). Sem janela: `-- roteiro agua`.
- Extrator/broca mineram a jazida de baixo; fornalha escolhe a receita pelo que chega e queima carvão/biomassa;
  montadora/refinador: receita escolhida no painel. Elétricos precisam de poste (cobertura 2,5) ligado a gerador com combustível.
- Torre: cada munição que chega (braço ou esteira na porta sul) = 10 tiros. Quem trabalha polui (e vira alvo por 60 s).
- **Clique/toque com a mão vazia** numa peça abre o painel: estado, conteúdo, combustível, munição, receitas.
  Num trem: carga e **rota** (liga/desliga estações na ordem; sem nenhuma, passa por todas).

## Trem, poluição e aranhas
- **Trem**: aba Trilhos → Trem, em cima de um trilho reto. Roda por todas as estações da malha em ordem; carrega o que
  braços deixaram na plataforma ("para enviar") e descarrega na estação seguinte ("recebido"). Sinal ao lado da linha
  divide blocos (1 trem por bloco). Numa volta, todos rodam no mesmo sentido; em linha com fim de linha, vai e vem.
  Trens que se encaram destravam: depois de 8–17 s esperando, um deles tenta a rota pelo outro lado.
- **Poluição**: máquinas emitem no chunk; a nuvem vaza para os vizinhos e o chão absorve (floresta muito, deserto pouco).
- **Ninhos** nascem longe do spawn (≥ 52 tiles), absorvem a poluição que chega e a transformam em aranhas. Juntou 4,
  o grupo ataca a fonte de poluição mais perto. Muro e máquina no caminho são mordidos; esteira e trilho ficam por baixo.
  De tempos em tempos as aranhas constroem um ninho novo (14–30 tiles do antigo, 26+ de qualquer estrutura).
- **Torre**: 18 m de alcance, 3 tiros/s, vem com 60 de munição e recebe mais pela Fabrica. Aranha primeiro, depois ninho.
- **Metralhadora** (pesquisa "Metralhadora": defesa + aço): 2×2, só bala — 10 tiros/s, 3 de dano, 18 m; começa vazia e
  guarda até 200 tiros (o braço não entrega na cheia). Melhorias `dano_bala` (dano 1 e 2) e `cadencia_bala` (cadência 1).
  O tambor de 6 canos gira na rajada e todo tiro (das duas torres) ejeta uma cápsula com fumacinha pela calha do modelo.
- **Muro de tijolo** (pesquisa "Muro de tijolo"): 700 ♥, o dobro do muro de pedra; custa 5 tijolos; arrasta em linha.
- Expansão só sai de ninho que absorveu poluição. Aranha que não se aproxima do destino por 15 s desiste.
- Ritmo medido na demo (`-- acelerar 8 relatorio`): ataques a cada ~6 min; torres seguram o grupo.

## Câmera
Entre isométrica e de cima: inclinação de 56° (zoom perto) a 74° (zoom longe), lente de 38°. Começa a 44 m;
zoom de 8 a 150 m. De longe carrega mais chunks (até 11×11), a névoa afina e os enfeites miúdos somem.

## Construir (PC e toque)
| | PC | Toque |
|---|---|---|
| Escolher peça | barra de baixo, ou 1..9 na aba aberta (Tab troca de aba) | tocar no botão |
| Pôr | clicar (o fantasma segue o mouse) | tocar; o fantasma segue o dedo e a peça entra ao soltar |
| Traçar esteira/cano/trilho/muro/poste | arrastar com o botão esquerdo | arrastar com um dedo |
| Girar | R (Shift+R ao contrário) | botão Girar |
| Remover (peça ou árvore/rocha) | X, depois clicar ou arrastar um retângulo | botão Remover |
| Desfazer / cancelar | Ctrl+Z / Esc ou clique direito | botões |
| Câmera | arrastar sem peça, botão do meio ou direito; roda ou +/−; Q/E; WASD | 1 dedo sem peça; 2 dedos = mover + pinça |

Fantasma verde = pode, vermelho = não pode (a dica em cima diz o motivo: ocupado, água, obstáculo, jazida que falta),
cinza = já está igual. Setas mostram as portas: branca entra, amarela sai.
Esteira traçada faz a curva em L sozinha e escolhe as pontas: **início** quando nada a alimenta, **fim** (para-choque)
quando nada recebe na frente, **reta** quando está ligada — e refaz isso nos vizinhos quando se põe ou remove algo.
Traçar por cima de uma esteira existente troca as peças (continuar a partir de um fim o transforma em reta).

## Pastas
| Pasta | O quê |
|---|---|
| `nucleo/` | `Grade` (tiles, chunks, cantos, rotação, portas no mundo), `Registro` (autoload, carrega os JSON), `RelogioSim` (passo fixo) |
| `mundo/` | `GeradorMundo` (terreno, clima, bioma, água), `Distribuicao` (jazidas, obstáculos, enfeites por hash do tile), `ChunkDados` |
| `construcao/` | `MapaOcupacao` (regras de colocar: área, água, obstáculo, jazida, cantos), `EsteiraElevada` (planeja pilares nos cantos), `Construtor` (planos de peça/traço/remoção, pontas automáticas, desfazer) |
| `logistica/` | `EsteiraCaminho` (linha inteira = 1 objeto, itens por espaços), `Braco` (pega atrás, solta na frente) |
| `maquinas/` | `Maquina` (receita, estados, dorme quando travada) |
| `simulacao/` | `Fabrica` (simula tudo que está no mapa: esteiras em caminhos com carga lateral, portas, braços, máquinas, baús, energia, combustível, munição da torre, estações; remonta a cada mudança guardando os itens), `DesenhoItens` |
| `energia/` | `RedeEnergia` (postes, cobertura, satisfação por rede, combustível dos geradores) |
| `transporte/` | `GrafoTrilhos` (montado do mapa: reta, curva 3×3 em arco, fim de linha, sinais, estações; A*, blocos, reserva), `Trem` (anda numa trilha planejada, freia em bloco ocupado, para centrado na estação, troca carga, inverte em linha sem saída), `DesenhoTrens` |
| `ambiente/` | `Poluicao` (por chunk: emite, espalha, o bioma absorve), `DesenhoPoluicao` (camada roxa, tecla P) |
| `inimigos/` | `MarchaAranha` (marcha trípode + IK), `Aranha` (nó visual, golpe e morte), `Colonia` (ninhos, poluição → aranhas, ataques, muro no caminho, torres, expansão), `DesenhoColonia` |
| `render/` | `DesenhoLotes` (MultiMesh de esteira/cano/trilho por chunk), `Efeitos` (fumaça, ícones de estado, destroços), `material_pf.gdshader` (material único: vento, esteira rolando, pulso, boiar), `terreno.gdshader`, `Materiais`, `DesenhoChunk`, `animacao/Animador` |
| `interface/` | `ControleConstrucao` (toda a entrada: separa gesto de construir de gesto de câmera), `BarraConstrucao` (UI por código), `Fantasma` (prévia verde/vermelha), `RoteiroTeste` (cliques/toques injetados) |
| `cenas/` | `menu` (menu inicial), `mundo_demo` (o jogo: modos novo/continuar/demonstração), `CameraJogo` |
| `progressao/` | `Pesquisa` (árvore, pacotes, o que libera) |
| `testes/` | `executar.gd` + `test_*.gd` (64.000+ verificações) |
| `dados/` | `itens`, `receitas`, `estruturas` (regras), `biomas`, `inimigos` (poluição, ninhos, aranhas, expansão, torre), `menu_construcao` (abas, nomes, textos de bloqueio), `modelos` (gerado) |

## Decisões de arquitetura
- **Lógica separada do desenho.** Tudo em `nucleo/ mundo/ construcao/ logistica/ maquinas/ energia/ transporte/` e
  `MarchaAranha` é RefCounted puro, testável sem janela. Os nós só desenham e animam.
- **Mundo sem estado.** Cada tile é função da semente; chunk nenhum depende de outro (testado: sem costura).
- **Escala.** Esteira = 1 objeto por linha (custo não cresce com o comprimento); máquinas dormem quando travadas;
  desenho por MultiMesh (1 chamada por tipo de modelo por chunk); 1 material compartilhado por cor.
- **Próximo passo de desempenho:** mover `EsteiraCaminho`, `Maquina` e `RedeEnergia` para C++ (GDExtension)
  mantendo a mesma interface — os testes atuais viram a especificação.

## Referências estudadas (só ideias, código próprio)
`Apps/ColecaoFactory/codigos` (Mindustry, shapez.io, OpenTTD — GPL): esteira por espaços entre itens (shapez),
blocos de sinal e reserva (OpenTTD), máquina que dorme (Mindustry). Nada foi copiado.
