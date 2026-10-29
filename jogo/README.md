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
| `testes/` | `executar.gd` + `test_*.gd` (8.600+ verificações) |
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
