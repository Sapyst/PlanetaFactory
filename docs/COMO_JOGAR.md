# Como jogar

Você é a IA do núcleo que caiu no planeta. O objetivo é crescer: extrair, fabricar, pesquisar e se espalhar.
No jogo novo, a abertura mostra a chegada: a cápsula de reentrada despenca em brasa, bate, ejeta a ogiva, crava as
pétalas no chão e ergue o monólito — vira o núcleo (um toque pula).

## O que você tem no começo
- **Núcleo:** guarda tudo o que você junta (os números no canto de cima). Gera um pouco de energia sem fio: máquinas a
  até 7 m da borda dele funcionam sem poste.
- **Kit inicial:** 160 placas de ferro, 60 engrenagens, 60 placas de cobre, 80 pedras, 16 tubos, 40 carvões e
  10 munições. Construir gasta itens do núcleo; remover devolve.

## A regra principal: braço leva, esteira carrega
- **Broca** e **extrator** tiram o recurso do chão e soltam na **esteira** encostada na saída deles.
- A esteira leva os itens, mas **não entrega dentro de construções**. Quem tira da esteira e põe numa máquina, num baú
  ou no núcleo é o **braço**: ele pega de um lado e solta do outro.
- Para encher o núcleo: broca → esteira → braço → núcleo.
- Mais tarde (pesquisas com pacote de automação): **Esteira rápida** (o dobro de itens; arraste por cima da comum
  para trocar), **Braço com filtro** e **Divisor com filtro** (toque neles para escolher os itens), **Silo de
  granel** (20.000 de um tipo só) e **Cano subterrâneo** (passa o cano por baixo da terra, até 9 tiles).
- Com pacote químico: **Esteira expressa** (Logística 4: o triplo da comum, faixa azul; passagem até 8 tiles) e
  **Braço empilhador** (pega até 4 itens iguais de uma vez e solta um por um). Como a rápida, arraste a expressa por
  cima de outra esteira para trocar. A **Esteira quântica** (o quádruplo, faixa violeta, passagem até 10 tiles) já
  aparece na árvore, mas espera a Computação quântica.
- **Trem automático** (pesquisa): **Sinal em cadeia** — ponha antes de um cruzamento, ao lado da linha como o sinal;
  o trem só entra se a saída também estiver livre (ninguém para no meio do cruzamento). No painel do trem, cada
  estação da rota ganha a espera: parada curta, 30 s, **até encher** ou **até esvaziar** (enquanto espera, os braços
  vão enchendo a estação e o trem vai levando).
- **Trem-tanque** (pesquisa Vagão-tanque, depois do Trem automático): locomotiva + 2 vagões-tanque (25.000 de fluido
  cada), posto num trilho reto como o trem. Encoste as costas (o braço de carga) de uma **Bomba de estação** na
  estação, ligue um cano na boca dela e um poste perto (40 kW). Toque na estação: **Cano → trem** (carregar) enche o
  tanque da estação (25.000) e o trem leva ao parar; **Trem → cano** (descarregar) recebe o fluido que o trem trouxe
  de outra estação e solta no cano. Começa desligado (não puxa nada).
- **Locomotiva elétrica** (com liga leve): **Trilho energizado** é um trilho reto com terceiro trilho — basta um poste
  perto de uma peça para energizar todas as peças encostadas. O **Trem elétrico** anda e acelera no dobro sobre ele
  (fora dele, devagarinho na bateria) e não polui; a locomotiva comum solta um pouco de poluição andando.
- **Rede lógica** (com processador; categoria Lógica): o **Sensor de esteira** fica ao lado da esteira, olhando para
  ela, e conta os itens que passam (itens/min); o **Sensor de tanque** é uma peça de cano e lê o nível da rede (0–100%).
  Cada sensor manda pelo canal escolhido (A a D; sensores do mesmo canal somam). O **Comparador** liga ou desliga tudo
  o que está encostado nele (máquinas, braços, bombas, válvulas) quando o canal fica maior ou menor que o número dele.
  A **Válvula** separa dois canos: passa se a entrada estiver acima de um nível, se a saída estiver abaixo, ou sempre.
- **Baú de estoque** (Drones logísticos): os drones guardam nele o que sobra na garra e buscam nele o que um
  requisitante pede quando nenhum provedor tem.
- **Braço quântico** (precisa da Computação quântica, ainda em desenvolvimento): a lança estica de 1 a 3 tiles para
  trás (toque nele para escolher) e o campo leva até 8 itens iguais por vez, a cada 0,2 s.
- **Sensor de varredura** (pesquisa Sensor de varredura, depois da Eletrônica; aba Proliferação): radar 2×2 com
  energia (150 kW, poste perto). Revela os chunks em volta, **1 por minuto**, do mais perto para o mais longe, até
  **6** — o chunk sai da névoa e os **ninhos** dele aparecem marcados no mapa (alfinete vermelho "⚠ Ninho", visível de
  longe) enquanto o sensor estiver de pé. Toque nele para ver quantos chunks já revelou, quando vem o próximo e onde
  estão os ninhos. Com a **Varredura profunda** (sensor + processador; pacotes básico, automação e químico) vai até
  **16** chunks e mede a **riqueza das jazidas** (tipo, quantidade, pobre/média/rica e a distância), que também
  aparecem escritas no mapa. A Varredura profunda abre a pesquisa da **Artilharia**; o sensor também abre a
  **Leitura ambiental**.
- **Farol de cristal** (pesquisa Farol de cristal, depois da Eletrônica; aba Proliferação): torre 1×1 com energia
  (30 kW). Quando escurece, acende uma **luz de 10 m**: ilumina a fábrica, tira a névoa em volta e, quando uma
  **aranha entra na luz**, avisa de que lado ela vem (no máximo um aviso a cada 30 s por farol). De dia fica apagado.
- **Posto avançado** (aba Proliferação; a pesquisa pede a Transmissão longa, que ainda está em desenvolvimento — por
  enquanto só no modo Demonstração): um **núcleo-filho** 3×3. Tem energia própria, **150 kW sem cabo** para as
  máquinas até 7 m da borda (como o núcleo), e **estoque próprio** de 3.200 itens: braços põem e tiram dele, e os
  drones logísticos o usam como estoque. **Obras a até 32 m** dele pagam primeiro com esse estoque (o que faltar sai
  do núcleo) — mande material de trem para o posto e construa a base nova ali.
- **Lançador de sementes** (pesquisa Núcleo-semente, que pede o posto avançado; por enquanto só na Demonstração):
  canhão 3×3 com energia (600 kW). Faça o **núcleo-semente** na montadora (4 núcleos de cristal + 2 células de
  energia + 10 liga leve + 2 processadores, 60 s) e leve-o por braço à boca sul. No painel escolha o **rumo** (8
  direções) e a **distância** (60 a 400 m; um anel violeta marca o alvo no chão). Com semente e energia ele carrega
  20 s, dispara e a cápsula voa em arco: **onde pousa nasce um posto avançado** (no lugar seco e plano mais perto do
  alvo; árvores e pedras saem), e aquele pedaço do mapa sai da névoa — cuidado com os ninhos que aparecem ali. Se o
  alvo cai na água ou num desnível, o painel avisa e ele não dispara.
- **Colônias e Receptor de cápsulas** (pesquisa Colônias, depois do núcleo-semente; só na Demonstração por
  enquanto): com ela, a semente que pousa vira **colônia** — um posto avançado que já chega com um kit (material e 2
  drones) e **fabrica 1 pacote gênese a cada 30 s** (o pacote gênese não tem receita: só as colônias fazem). O
  pacote vem por cápsula até o **Receptor de cápsulas** 2×2 com energia (100 kW) mais perto, que guarda até 100 para
  os braços (saída ao norte). Sem receptor, os pacotes esperam na colônia (até 20).
- **Transportador quântico** (precisa da Computação quântica, ainda em desenvolvimento; só na Demonstração): 3×3 com
  energia (500 kW). O braço põe itens na entrada (sul) e eles saem, **sem trilho**, na saída (norte) de outro
  transportador no **mesmo canal** (A a D, no painel), 5 por segundo — para trocar itens entre colônias.
- **Silo de lançamento** (fim da árvore; ainda em desenvolvimento, só na Demonstração): 3×3 com energia (1 MW). Monta
  o **foguete de proliferação** por 100 partes — cada uma pede 1 casco de foguete e 5 processadores quânticos (braço,
  bocas sul e oeste) e 50 de propelente de cristal (cano, boca leste) — e você vê o foguete crescer no poço. Com as
  100 partes e a pesquisa Foguete de proliferação, monta a **carga-semente** (núcleo-semente + mapa estelar + 10
  módulos de produtividade 3). Pronto, o painel mostra **Lançar o foguete**: ele sobe e a campanha termina (a IA se
  proliferou); dá para continuar jogando. As peças do foguete ainda não existem no jogo.
- **Água** (pesquisa "Água como insumo", com pacote de automação): a **Bomba d'água** 2×2 fica na margem, com a tomada
  (o lado da grade) encostada num rio, lago ou canal, e solta 40 de água/s pelo cano. Água suja na tomada rende menos.
  Também dão água o **Coletor de chuva** (só quando chove; guarda 2.000), o **Condensador de neblina** (com neblina e
  energia) e o **Filtro de água** depois da pesquisa "Filtro que devolve água" (água limpa pelo cano).
  Com água no **Refinador** saem o **aço refrigerado** e a **lapidação refrigerada** (+50%); a fornalha e a montadora
  continuam fazendo os dois sem água. O **Supressor de incêndio** (aba Limpeza), com água pelo cano, apaga o fogo em
  8 m e não deixa a vegetação em volta pegar fogo.
- **Química** (refino + bomba d'água): **resina** (seiva por uma boca do refinador, água pela outra) e o **pacote
  químico** (resina + bateria + água), o terceiro tipo de pacote do laboratório. **Bioquímica** libera o **pacote
  ecológico**, que só sai com **água limpa**.
- **Clima** (aba Clima): em **tempestade** e **tufão** caem **raios** de verdade, perto da fábrica, nos pontos altos.
  Sem proteção, o raio tira 150 de vida da construção mais alta e pode pôr fogo no mato em volta (dentro da bolha de um
  gerador de escudo carregado, o escudo absorve). O **Para-raios** (automação + aço) pega todo raio que cairia a até
  14 m e, ligado num poste, manda 120 MJ para os acumuladores; o **de cristal** pega em 22 m (200 MJ). O **Captador de
  carga** pega os raios a até 10 m e, com cristal lapidado (braço na boca sul) e água (cano ao norte), transforma cada
  raio em um **cristal carregado** (sai a oeste) — o ingrediente do **pacote de tempestade** (cristal carregado +
  módulo de controle + liga leve na montadora), liberado pela **Ciência de tempestade**. Com ele: dano 4 e cadência 2
  da torre de energia, **Escudo 2** (bolha de 12 m, 1.000 de dano) e o **Muro de campo**, mais as melhorias de bala e
  foguete. Máquinas de clima (precisam de energia): **Semeador de nuvens** (chove em 40 m: apaga fogo e enche coletores),
  **Cúpula contra raios** (nenhum raio em 30 m), **Defletor de vento** (o vento de 40 m sopra para onde ele aponta —
  gire com R —, sem ventania de tufão) e **Regulador climático** (céu firme ou chuva mansa em 80 m, sem raio nem
  tufão); os dois últimos esperam tecnologias que ainda vão chegar.
- **Drones** (aba Drones; pesquisa Drones de reparo: água como insumo + energia sem fio): a **Estação de drones** 2×2
  precisa de energia e de água pelo cano (borda sul, tile leste). Ponha placas de ferro, motores e circuitos com braço:
  cada drone (4 placas + 1 motor + 2 circuitos + 50 de água) nasce em **holograma vermelho** na fabricadora e entra na
  frota (8 por estação; as melhorias de frota levam a 20). No painel da estação escolha o que a frota faz:
  **Reparo** — o drone voa até o que as aranhas, o fogo ou os raios estragaram (até 45 m), corre o **scan vermelho**
  sobre a peça e solda (25 ♥/s), gastando 1 placa de ferro do núcleo a cada 25 ♥ (como o Reparar à mão);
  **Combate** — caça as aranhas no alcance, orbitando e atirando (cada tiro solta uma cápsula com fumacinha); aranha
  perto morde o drone, e drone sem vida cai e vira sucata (a estação monta outro); **Logístico** (pesquisa Drones
  logísticos) — a estação vira porto: toque num baú e escolha **Provedor** (os drones tiram dele) ou **Requisitante**
  (escolha o item e a quantidade; os drones trazem até completar). Os drones voltam ao berço para recarregar antes de a
  bateria acabar; com **raios** caindo ficam no hangar até a pesquisa Voo na tempestade. Melhorias: bateria, frota,
  velocidade, logísticos 2 (4 itens por viagem, 2× alcance) e Drones de defesa (2× dano, +50% de vida).
- **Limpeza nova** (aba Limpeza; todas pedem o **pacote ecológico**): **Coletor de lixo 2** (raio 10: sujeira, óleo e
  a **cinza** do chão queimado, compactados em **resíduo** que o braço tira); **Purificador de ar** (tira 6 de poluição
  por minuto do chunk) e **Purificador atmosférico** 3×3 (40 por minuto, condensa em resíduo); **Viveiro 2** (seiva pelo
  cano: planta no dobro do ritmo, num raio de 12 m, mudas da **árvore do bioma** que crescem 2× mais rápido);
  **Biodigestor** 3×3 (resíduo por braço + água pelo cano sul → biomassa por braço + seiva pelo cano leste — fecha o
  ciclo: o lixo recolhido vira seiva para os viveiros); **Recuperação de solo** (Aplainar também limpa o chão);
  **Semeador de bioma** 3×3 (seiva pelo cano oeste: tira o queimado do chão em 14 m, devolve as árvores carbonizadas
  e planta mudas do bioma); **Estação de tratamento** 3×3 na margem (como a bomba d'água, a tomada encosta na água:
  limpa a água suja em 16 m e solta 60 de água limpa/s pelo cano leste) — esta ainda espera o Refinador 2.
- **Defesa do meio** (aba Defesa): **Ciência militar** (metralhadora + muro de tijolo + automação) libera o **pacote
  militar** (2 munições + 1 aço + 2 tijolos na montadora), que abre as melhorias de bala e da torre de energia.
  O **Lança-foguetes** 3×3 recebe **foguetes** (resina + aço + circuito) pela boca sul e acerta grupos de aranhas
  (dano em área, 30 m). A **Mina de pulso** atordoa as aranhas em 3 m por 3 s e rearma em 20 s. O **Muro de liga**
  aguenta 1.500 (feito de **liga leve**: aço + cobre + resina). O **Gerador de escudo** 2×2 (precisa de
  **processador**, feito no refinador com água) faz uma bolha de 8 m: enquanto tem carga, a mordida em qualquer
  construção dentro dela gasta o escudo, não a vida; ele recarrega pela rede. A **Artilharia** (granadas, ninhos a
  até 120 m) se pesquisa depois da **Varredura profunda** (sensor de varredura) — o sensor revela os ninhos longe,
  e ela os alcança; o **Muro de campo** (regenera com energia) espera o escudo 2 (pacote de tempestade).

## Primeiros passos
1. **Ache as jazidas:** aperte **V** (ou o botão **Recursos**). Cada jazida aparece colorida, com o nome, a quantidade
   e a máquina que a extrai. Perto do início sempre há cristal, ferro, cobre, **carvão** e pedra.
2. **Carvão:** ponha uma **Broca** em cima da jazida de carvão (a mancha preta), perto do núcleo para ter energia.
   Encoste uma **esteira** na saída da broca, leve a esteira até perto do núcleo e ponha um **braço** entre o fim da
   esteira e o núcleo. O carvão vai entrar no núcleo.
3. **Ferro:** faça o mesmo numa jazida de ferro. O minério precisa ir para uma **Fornalha**, também por braço. A
   fornalha queima carvão: um braço põe carvão nela e outro, minério. Um terceiro braço tira as placas e põe numa
   esteira ou no núcleo.
4. **Energia:** longe do núcleo, as máquinas precisam de um **Gerador**, que queima carvão (por braço), e de
   **Postes**. Os fios aparecem sozinhos. Toque numa máquina para ver se ela está com energia.
5. **Peças:** a **Montadora** faz engrenagens, tubos, fios e circuitos. Toque nela para escolher a receita.
6. **Pesquisa:** a montadora faz pacotes de pesquisa (cristal lapidado + engrenagem). Um braço leva os pacotes ao
   **Laboratório**. No botão **Pesquisa** (⚗ / T) abre a árvore: toque numa pesquisa para ver o que ela libera e
   aperte **Pesquisar**. A árvore mostra as três eras (base, meio, super avançada) lado a lado; arraste com o dedo
   para andar e use a pinça (ou − e +) para aproximar e afastar. Cada nó diz o tipo: ■ estrutura nova, ⚗ receita,
   ▲ melhoria do que já existe. Nós em **cinza escuro com a etiqueta "Em desenvolvimento"** ainda não estão no jogo
   (ou dependem de algo que ainda não está): dá para tocar e ver o que vão liberar, mas não se pesquisam. Na barra
   de construção, peça em cinza escuro com a mesma etiqueta também não se constrói (no modo Demonstração se constrói
   tudo o que já tem modelo).

## Cuidados
- **Poluição:** máquinas poluem, e as aranhas dos ninhos vêm atrás de quem polui. A **Torre** (já liberada) defende
  com a energia da rede — ligue-a a um poste; o **Muro** segura. Depois vêm a **Metralhadora** (pesquisa defesa + aço;
  um braço leva munição até ela) e o **Muro de tijolo** (o dobro da vida).
- **Sujeira:** chão sujo perto dos ninhos deixa as aranhas furiosas. Coletor de lixo, filtro de água e viveiro limpam.
- **Fogo:** máquinas quentes podem acender a vegetação seca, principalmente no verão. A chuva apaga.
- **Noite:** o painel solar para à noite; acumuladores seguram a energia.

## Controles
| Ação | PC | Celular |
|---|---|---|
| Mover a câmera | arrastar / WASD | arrastar (o chão fica preso no dedo) |
| Zoom | roda do mouse | pinça (aproxima onde estão os dedos) |
| Rolar uma lista | roda do mouse | arrastar em qualquer ponto dela, até em cima dos botões |
| Construir | escolher a peça na barra da direita e clicar | tocar na peça e no lugar |
| Girar a peça | R | botão da peça |
| Cancelar / largar a peça | clique direito | pressionar e segurar meio segundo (vibra) |
| Remover | X e clicar (ou arrastar um retângulo) | botão Remover |
| Ver jazidas / vento | V (de novo: vento) | botão Recursos |
| Pesquisa | T | botão ⚗ |
| Ver uma máquina | clicar com a mão vazia | tocar |

Veja também: `docs/RECURSOS.md` (jazidas, biomas e a ficha de cada construção).
