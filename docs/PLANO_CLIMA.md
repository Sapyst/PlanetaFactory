# Plano: vento, árvores, tempestades com raios e drones de reparo

Proposta para depois da 0.9.0. Quatro etapas, cada uma vira uma versão testável. A ordem importa: o vento é a base das
outras três; as árvores precisam existir antes de o raio e o fogo terem o que queimar; os drones fecham o ciclo
(o clima estraga, a frota conserta).

## O que já existe
- Fogo anda a favor do vento (`ambiente_vivo.gd`: `vento_mult` 1,8) e a chuva apaga (`chuva_apaga`).
- Chuva cai inclinada pelo vento; fumaça e grama seguem a direção do vento.
- Clima tem tempestade e tufão; o relâmpago é só visual (não atinge nada).
- Poluição do ar vaza igual para os 4 lados (ignora o vento).
- Vento é um só para o mapa inteiro (direção que gira devagar + força do estado do clima).

---

## Etapa 1 — Vento de verdade (v0.10) — feita
Extra: a nacele da turbina vira para encarar o vento.

**Direção predominante por estação.** Cada estação tem um rumo médio (ex.: primavera de leste, inverno de sul) e a
direção do momento oscila em volta dele (±40°), com **rajadas** (picos de 3–8 s, até +60% de força) que passam
como ondas pelo mapa.

**Vento local.** Força = vento do clima × fator do lugar:
| Lugar | Fator |
|---|---|
| Alto (cada nível acima do entorno) | +12% por nível, até +36% |
| Campo aberto, praia, beira-mar | +15% |
| Floresta / perto de árvores (raio 4) | −30% |
| Atrás de construção alta, a sotavento (2 tiles) | −20% |
A turbina passa a render pelo vento **do tile dela** — posicionar vira decisão.

**Turbina em ventania.** Curva de potência: até 25% do vento não gira; sobe até o máximo em 85%; acima disso
(ventania, tufão) entra em **proteção** (pás em bandeira, rende 40%) — senão quebra (dano 2/s).

**Poluição com o vento.** O ar sujo do chunk vaza mais vento abaixo: 70% da difusão vai a favor, 30% para os lados
e contra. Ninhos a sotavento da fábrica recebem mais — escolher onde construir passa a importar.

**Visão de recursos (V).** Nova camada “Vento”: mapa de calor da força média do lugar e setas da direção
predominante da estação; ficha do tile mostra “vento médio aqui: 64% · de leste”.

**Medição.** Média móvel da força e da direção (últimos 10 min de jogo) guardada no save.

---

## Etapa 2 — Árvores por receita (v0.11)
**Receitas de árvore.** Cada espécie é uma receita (regras no Blender): altura do tronco, quantas vezes ramifica,
ângulo dos galhos, forma da copa, cor da folha por estação, se perde folha. Cada receita gera **6 variações** por
semente. Proposta inicial (6 espécies = 36 árvores):
| Espécie | Copa | Estação |
|---|---|---|
| Carvalho-de-campina | redonda larga | caduca: amarela/laranja no outono, nua no inverno |
| Bétula-prata | estreita, tronco claro | caduca: amarela no outono, nua no inverno |
| Pinheiro | cone em camadas | perene (não muda) |
| Salgueiro-do-pântano | galhos caídos | semi: amarelada no inverno |
| Acácia-seca | guarda-chuva achatada | perde metade no verão seco |
| Fungo-cristal (alienígena) | chapéu com cristais | perene, brilha fraco à noite |
Cada árvore tem 4 modelos: **com folha**, **sem folha**, **carbonizada** e **tronco caído**.

**Estações.** Caducas trocam de cor no outono, perdem folha no inverno e brotam na primavera — a troca anda pelo mapa
em alguns minutos (não pisca tudo junto). Perenes não mudam.

**Balanço no vento.** Copa e galhos balançam na direção do vento (o shader de vegetação já balança pela altura):
sutil com brisa, maior com vento forte e tempestade, e as **rajadas** passam como onda visível pela floresta.

**Fogo em etapas.** 1) a folhagem queima (brasa sobe pela copa, folha vira carvão e cai em cinza); 2) o tronco
queima; 3) se o fogo persistir (>20 s no tile), a árvore carbonizada **cai** na direção do vento e vira tronco caído
(obstáculo que rende carvão ao remover). Chuva interrompe em qualquer etapa; a árvore que sobrou fica queimada e
rebrota na próxima primavera se o tronco aguentou.

**Desempenho.** Continua em lote (MultiMesh por modelo); a queda é um nó temporário só durante a animação.

---

## Etapa 3 — Tempestades com raios e para-raios (v0.12)
**Nuvem carregada.** Tempestade e tufão trazem **células** de tempestade: áreas de ~35 m que andam com o vento,
visíveis como nuvem mais escura e baixa. Aviso no HUD quando uma célula vem na direção da fábrica (seta + tempo).

**Raio.** Dentro da célula cai um raio a cada 6–14 s (tufão: 3–7 s). O alvo é sorteado com peso pela **altura**:
coisa alta atrai (turbina, torre, árvore alta > máquina > esteira > chão).
| Onde cai | Efeito |
|---|---|
| Construção | perde 35% da vida máxima (pode destruir se já estiver avariada); esteira/cano só 15% |
| Árvore | folhas queimam na hora e a árvore pega fogo |
| Grama seca | acende fogo (chance pela secura da estação) |
| Água | só o clarão |
| Para-raios | absorve (ver abaixo) |
Clarão no chão, luz forte e trovão com atraso pela distância (já existe), marca queimada no ponto.

**Chuva apaga.** Fogo começado por raio enfrenta a chuva da própria tempestade: apaga aos poucos (cada tile perde
brasa mais rápido quanto mais forte a chuva).

**Para-raios** (1×1, mastro alto de cobre com cristal; pesquisa “Para-raios”). Pega todo raio que cairia num raio de
14 m. Cada raio rende **120 MJ** de uma vez na rede: carrega os acumuladores (o que não couber se perde, com faísca no
chão). Sem acumulador, um para-raios é só proteção. Faíscas e brilho reaproveitam o shader dos raios.

### Água como insumo (decidido)
A IA quer se espalhar: água é **essencial para crescer**, mas não é o primeiro passo — a base (broca, extrator,
fornalha comum, montadora, gerador, núcleo, laboratório) **nunca** precisa de água. Ela entra no nível do meio:
| Quem usa água | Para quê | Consumo |
|---|---|---|
| Fundir aço | têmpera | 20 por barra |
| Lapidar cristal | corte refrigerado | 10 por cristal |
| Refinador (bateria, núcleo, módulo) | resfriamento contínuo | 6/s trabalhando |
| Estação de drones | fabricar drone | 50 por drone |
| Captador de carga | banho do cristal | 30 por cristal carregado |
Sem água, essas receitas param (painel mostra “sem água”); o uso devolve parte como **água suja** (despejo, já
existe), então crescer sem filtro suja os rios — consequência, não ataque.

**Fontes de água** (fluido novo `agua`, pelos canos que já existem):
- **Bomba d'água** (2×2, encostada em rio/lago/canal escavado): 40/s fixo. Água suja na tomada rende menos.
- **Coletor de chuva** (2×2, em qualquer lugar): até 25/s durante chuva forte, 0 no seco; tanque próprio de 2.000.
- **Condensador de neblina** (2×2): até 12/s com neblina (forte no inverno, quase nada no verão); usa 80 kW.
- **Filtro de água** passa a também **soltar água limpa** pelo cano enquanto limpa.
Estações viram planejamento: verão seco = menos chuva e neblina → depender de rio ou estocar em tanques.

**Cristal carregado** (decidido): **Captador de carga** (2×2, alto) dentro de célula de tempestade converte
1 cristal lapidado + 30 de água em 1 **cristal carregado** a cada raio que recebe (atrai raio como para-raios, raio
de 6 m). Item novo para receitas avançadas (drone, torre sem fio melhorada, acumulador maior).

---

## Etapa 4 — Drones de reparo (v0.13)
**Drone.** Corpo hexagonal high-tech, 4 rotores em dutos, núcleo de cristal, braço de solda embaixo (faísca de solda
com o shader dos raios). Voa de verdade: decola, sobe a 4 m, curva suave, desvia de estruturas altas, pousa.
| Valor | Drone |
|---|---|
| Velocidade | 7 m/s |
| Reparo | 12 de vida/s (gasta 1 placa de ferro a cada 25, como o reparo manual) |
| Bateria | 90 s de voo; recarrega na base (60 kW por drone carregando) |
| Vida | 40 |
| Ataque | 3 de dano/s (a torre dá ~12/s) |

**Núcleo:** 2 drones passivos para sempre, alcance de 30 m em volta dele.

**Estação de drones** (2×2, pesquisa “Drones”): fabrica e abriga uma frota de até 8 (cada drone é uma receita na
própria estação: placas, motor, circuito). Alcance de 45 m. Tem estoque de placas para reparo (braços abastecem).

**Divisão inteligente.** Cada estação cuida da sua área; os chamados entram numa fila com prioridade:
`prioridade = importância da peça × dano`. Importância: núcleo 5 · torre 4 · gerador/acumulador 3 · máquina 2 ·
esteira/cano 1. Cada chamado recebe só os drones que precisa (1 por 60 de vida faltando, até 3), o mais perto e com
bateria; estação sobrecarregada pede ajuda à vizinha. Painel da estação mostra a fila e cada drone (indo, reparando,
voltando, recarregando).

**Combate** (decidido: só defendem a área — não vão atrás de ninho sozinhos). Drone parado e com bateria entra em
combate quando aranhas atacam dentro da área: fica em órbita a 3 m
do alvo e atira (dano baixo, ajuda a torre). Aranha pode derrubar drone que desce baixo (chance por mordida).
Drone derrubado vira sucata no chão e a estação fabrica outro.

**Clima.** Drones não voam com raios caindo na área (esperam na base) — o para-raios libera o voo em volta dele.

---

## Decisões de Sapyst (2026-10-29)
1. Árvores por receita = geradas por regras (6 espécies × 6 variações, com/sem folha, carbonizada, caída).
2. Raio **pode destruir** construção já avariada (tira 35% da vida máxima).
3. Entram coletor de chuva, condensador de neblina e cristal carregado — e **água vira insumo** das estruturas do
   nível do meio (não da base): essencial para a IA se espalhar, mas não o primeiro passo.
4. Drones **só defendem** a área da estação.

## Em aberto
- Ordem proposta: vento (v0.10) → árvores (v0.11) → tempestades, raios e água (v0.12) → drones (v0.13).
