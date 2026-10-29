# Árvore de tecnologia

Proposta completa da pesquisa do PlanetaFactory, do primeiro pacote ao foguete de proliferação. No jogo, a tela de pesquisa mostra esta árvore inteira (`jogo/dados/arvore.json`, gerado por `jogo/ferramentas/gerar_arvore.py` a partir de `ARVORE_TECNOLOGIA.mmd` e das tabelas de balanceamento abaixo): as 15 pesquisas de `jogo/dados/progressao.json` se pesquisam de verdade; as outras aparecem como "em breve" até a estrutura, o item ou o pacote existir. Cada tecnologia tem um tipo — estrutura nova, receita nova, melhoria (bônus no que já existe, campo `bonus` lido por `Pesquisa.bonus`), infinita ou objetivo. Fontes: `progressao.json`, `estruturas.json`, `itens.json`, `receitas.json`, `menu_construcao.json`, `docs/PLANO_CLIMA.md`.

## Eras e pacotes de pesquisa

A IA cresce em três eras. Na **era base** ela só precisa do que o chão dá de graça: minério, pedra, carvão e cristal; nada usa água, e a pesquisa sai do **pacote básico** (o pacote de pesquisa de hoje) e, depois da Automação, do **pacote de automação**. A **era do meio** começa quando a IA precisa de água para continuar crescendo (bomba d'água, refinador, química): surgem o **pacote militar** (defesa contra os ninhos), o **pacote químico** (resina e baterias, refinador com água) e o **pacote ecológico**, que só sai com **água limpa** — poluir demais trava a própria pesquisa. Na **era super avançada** a IA aprende a usar o clima do planeta: o **pacote de tempestade** precisa de cristal carregado por raios, o **pacote quântico** sai da forja quântica e o **pacote gênese** não tem receita, porque só as **colônias** (núcleos-semente lançados para outros pontos do planeta) o produzem. O fim da campanha é lançar o **foguete de proliferação**; depois dele restam as melhorias infinitas.

| Pacote | Item (ID) | Era | Receita | Máquina | Liberado por |
|---|---|---|---|---|---|
| Básico | `pacote_pesquisa` (já existe) | base | 1 cristal lapidado + 1 engrenagem → 1 (5 s) | montadora | início |
| Automação | `pacote_automacao` | base | 1 motor + 2 circuitos → 2 (10 s) | montadora | `automacao` |
| Militar | `pacote_militar` | meio | 2 munições + 1 barra de aço + 2 tijolos → 2 (10 s) | montadora | `ciencia_militar` |
| Químico | `pacote_quimico` | meio | 1 resina + 1 bateria + 20 água → 2 (12 s) | refinador | `quimica` |
| Ecológico | `pacote_ecologico` | meio | 5 biomassa + 1 vidro + 30 água **limpa** → 1 (8 s) | refinador | `bioquimica` |
| Tempestade | `pacote_tempestade` | super avançada | 1 cristal carregado + 1 módulo de controle + 1 liga leve → 2 (15 s) | montadora 2 ou melhor | `ciencia_tempestade` |
| Quântico | `pacote_quantico` | super avançada | 1 processador quântico + 1 célula de energia + 1 cristal carregado → 3 (20 s) | forja quântica | `computacao_quantica` |
| Gênese | `pacote_genese` | super avançada | sem receita: cada colônia viva gera 1 a cada 30 s e manda por cápsula ao receptor | colônia + receptor de cápsulas | `colonias` |

Como no Factorio, uma **unidade** de pesquisa gasta 1 pacote de cada tipo listado e leva o tempo da tabela no laboratório (velocidade 1,0). Uma tecnologia só pede um tipo de pacote depois que a tecnologia que libera a receita dele já está entre os seus pré-requisitos (direta ou indiretamente).

### Itens e fluidos novos

| Item | Receita proposta | Máquina | Tecnologia |
|---|---|---|---|
| Água (`agua`, fluido) | bomba d'água, coletor de chuva, condensador, filtro | — | `bomba_agua` |
| Briquete (`briquete`) | 4 biomassa → 1 (10 MJ) | montadora | `briquete` |
| Resina (`resina`) | 30 seiva + 10 água → 1 (3 s) | refinador | `quimica` |
| Liga leve (`liga_leve`) | 1 barra de aço + 2 placas de cobre + 1 resina → 2 (6 s) | montadora | `liga_leve` |
| Processador (`processador`) | 2 circuitos + 1 resina + 1 cristal lapidado + 5 água → 1 (8 s) | montadora | `processador` |
| Combustível de seiva (`combustivel_seiva`, fluido) | 40 seiva + 10 água → 30 (4 s; 12 MJ por 10) | refinador | `combustivel_seiva` |
| Cristal carregado (`cristal_carregado`) | 1 cristal lapidado + 30 água por raio recebido | captador de carga | `captador_carga` |
| Resíduo (`residuo`) | sai do coletor de lixo 2 (1 a cada 20 de sujeira) | coletor de lixo 2 | `coletor_lixo_2` |
| Munição perfurante (`municao_perfurante`) | 1 munição + 1 barra de aço → 1 (3 s) | montadora | `municao_perfurante` |
| Munição carregada (`municao_carregada`) | 1 munição perfurante + 1 cristal carregado → 5 (5 s) | montadora | `municao_cristal` |
| Foguete (`foguete`) | 1 resina + 1 barra de aço + 1 circuito → 1 (6 s) | montadora | `torre_foguetes` |
| Foguete de enxame (`foguete_enxame`) | 2 foguetes + 1 processador → 1 (10 s) | montadora | `foguete_enxame` |
| Granada de artilharia (`granada`) | 2 liga leve + 1 foguete + 2 tijolos → 1 (12 s) | montadora | `artilharia` |
| Módulos (`modulo_velocidade_1`…`_3`, eficiência, produtividade) | nível 1: 3 processadores + 2 circuitos; nível 2: 3 do nível 1 + 2 cristais carregados; nível 3: 3 do nível 2 + 1 processador quântico | montadora | `modulo_*` |
| Drone (`drone`) | 4 placas de ferro + 1 motor + 2 circuitos + 50 água | estação de drones | `drones` |
| Processador quântico (`processador_quantico`) | 2 processadores + 1 cristal carregado + 1 liga leve → 1 (20 s) | forja quântica | `computacao_quantica` |
| Núcleo-semente (`nucleo_semente`) | 4 núcleos de cristal + 2 células de energia + 10 liga leve + 2 processadores → 1 (60 s) | montadora 3 ou melhor | `nucleo_semente` |
| Propelente de cristal (`propelente_cristal`, fluido) | 1 cristal carregado + 50 combustível de seiva → 50 (10 s) | refinador 2 | `propulsao_cristal` |
| Casco de foguete (`casco_foguete`) | 10 liga leve + 2 processadores quânticos → 1 (30 s) | montadora quântica | `casco_foguete` |
| Mapa estelar (`mapa_estelar`) | 1 processador quântico + 5 pacotes gênese → 1 (30 s) | forja quântica | `navegacao` |
| Carga-semente (`carga_semente`) | 1 núcleo-semente + 1 mapa estelar + 10 módulos de produtividade 3 | silo de lançamento | `foguete_proliferacao` |

O foguete precisa de 100 partes no silo; cada parte = 1 casco de foguete + 50 propelente de cristal + 5 processadores quânticos. Com a carga-semente dentro, o lançamento encerra a campanha.

## Tabela principal

Ordenada por era e, dentro dela, por dependência (toda tecnologia aparece depois dos seus pré-requisitos). **Era base** (35): de `defesa` a `vagao_tanque`; **Era do meio** (60): de `refino` a `artilharia`; **Era super avançada** (71): de `ciencia_tempestade` a `eficiencia_infinita`. Total: **166 tecnologias**, das quais 10 são melhorias infinitas no fim.

| ID da tecnologia | Nome da tecnologia | Pré-requisitos |
|---|---|---|
| defesa | Munição | — |
| logistica | Logística 2 | — |
| aco | Aço | — |
| fluidos | Fluidos | — |
| limpeza | Limpeza | — |
| eletronica | Eletrônica | logistica |
| armazenagem | Armazenagem | aco |
| reflorestar | Reflorestamento | limpeza, fluidos |
| muros_reforcados | Muro de tijolo | defesa |
| dano_energia_1 | Torre de energia: dano 1 | defesa |
| cano_subterraneo | Cano subterrâneo | fluidos, logistica |
| sensor_varredura | Sensor de varredura | eletronica |
| farol_cristal | Farol de cristal | eletronica |
| monitor_ambiental | Leitura ambiental | sensor_varredura, limpeza |
| ferrovia | Ferrovia | logistica, aco |
| sem_fio | Energia sem fio | eletronica |
| renovavel | Energia renovável | eletronica |
| briquete | Briquete de biomassa | reflorestar |
| automacao | Automação | eletronica |
| torre_metralhadora | Metralhadora | defesa, aco |
| dano_bala_1 | Munição: dano 1 | torre_metralhadora |
| cadencia_bala_1 | Metralhadora: cadência 1 | torre_metralhadora |
| montadora_2 | Montadora 2 | automacao, aco |
| logistica_3 | Logística 3 | logistica, automacao |
| braco_filtro | Braço com filtro | automacao |
| divisor_filtro | Divisor com filtro | automacao |
| fornalha_aco | Fornalha de aço | aco, automacao |
| mineracao_1 | Produtividade de mineração 1 | automacao |
| pesquisa_vel_1 | Velocidade de pesquisa 1 | automacao |
| trem_automatico | Trem automático | ferrovia, automacao |
| silo_granel | Silo de granel | armazenagem, automacao |
| dano_bala_2 | Munição: dano 2 | dano_bala_1, automacao |
| dano_energia_2 | Torre de energia: dano 2 | dano_energia_1, automacao |
| transmissao | Transmissão longa | aco, automacao |
| vagao_tanque | Vagão-tanque | trem_automatico, fluidos |
| refino | Refino de seiva | fluidos, eletronica, aco |
| acumulacao | Acumulação | renovavel, refino |
| energia | Energia avançada | refino |
| bomba_agua | Água como insumo | fluidos, automacao |
| filtro_agua_limpa | Filtro que devolve água | bomba_agua, limpeza |
| coletor_chuva | Coletor de chuva | bomba_agua |
| condensador_neblina | Condensador de neblina | coletor_chuva |
| escavar_canal | Escavação de canal | bomba_agua |
| supressor_fogo | Supressor de incêndio | bomba_agua, limpeza |
| turbina_rio | Turbina de correnteza | bomba_agua, renovavel |
| para_raios | Para-raios | automacao, aco |
| ciencia_militar | Ciência militar | torre_metralhadora, muros_reforcados, automacao |
| drones | Drones de reparo | bomba_agua, sem_fio |
| drones_bateria_1 | Bateria de drone 1 | drones, acumulacao |
| quimica | Química de seiva | refino, bomba_agua |
| liga_leve | Liga leve | quimica, aco |
| processador | Processador de cristal | quimica |
| bioquimica | Bioquímica | reflorestar, filtro_agua_limpa, quimica |
| combustivel_seiva | Combustível de seiva | quimica, briquete |
| fornalha_eletrica | Fornalha elétrica | fornalha_aco, quimica |
| captador_carga | Captador de carga | para_raios, acumulacao, quimica |
| logistica_4 | Logística 4 | logistica_3, liga_leve |
| braco_empilhador | Braço empilhador | braco_filtro, processador |
| montadora_3 | Montadora 3 | montadora_2, processador |
| rede_logica | Rede lógica | processador, divisor_filtro |
| modulo_velocidade_1 | Módulo de velocidade 1 | processador, montadora_2 |
| modulo_eficiencia_1 | Módulo de eficiência 1 | processador |
| modulo_produtividade_1 | Módulo de produtividade 1 | processador |
| broca_grande | Broca grande | mineracao_1, liga_leve |
| extrator_2 | Extrator ressonante | processador, mineracao_1 |
| mineracao_2 | Produtividade de mineração 2 | mineracao_1, quimica |
| pesquisa_vel_2 | Velocidade de pesquisa 2 | pesquisa_vel_1, quimica |
| laboratorio_2 | Laboratório 2 | pesquisa_vel_2, processador |
| drones_frota_1 | Frota de drones 1 | drones, processador |
| drones_velocidade_1 | Velocidade de drone 1 | drones, liga_leve |
| drones_logisticos | Drones logísticos | drones, processador, silo_granel |
| renovavel_2 | Painel solar 2 | renovavel, processador |
| turbina_alta | Turbina eólica alta | renovavel, liga_leve |
| acumulacao_2 | Acumulador 2 | acumulacao, processador |
| trem_eletrico | Locomotiva elétrica | trem_automatico, liga_leve |
| cartografia | Varredura profunda | sensor_varredura, processador |
| coletor_lixo_2 | Coletor de lixo 2 | limpeza, bioquimica |
| purificador_ar | Purificador de ar | bioquimica |
| viveiro_2 | Viveiro 2 | reflorestar, bioquimica |
| biodigestor | Biodigestor | bioquimica, coletor_lixo_2 |
| recuperar_solo | Recuperação de solo | viveiro_2, coletor_lixo_2 |
| harmonia_ninhos | Convivência com ninhos | monitor_ambiental, purificador_ar |
| municao_perfurante | Munição perfurante | ciencia_militar, dano_bala_2 |
| dano_bala_3 | Munição: dano 3 | dano_bala_2, ciencia_militar |
| cadencia_bala_2 | Metralhadora: cadência 2 | cadencia_bala_1, ciencia_militar |
| dano_energia_3 | Torre de energia: dano 3 | dano_energia_2, ciencia_militar |
| cadencia_energia_1 | Torre de energia: cadência 1 | dano_energia_2, ciencia_militar |
| mina_pulso | Mina de pulso | ciencia_militar |
| posto_avancado | Posto avançado | transmissao, silo_granel, ciencia_militar |
| torre_foguetes | Lança-foguetes | ciencia_militar, quimica |
| dano_foguete_1 | Foguetes: dano 1 | torre_foguetes |
| cadencia_foguete_1 | Lança-foguetes: cadência 1 | torre_foguetes |
| muro_liga | Muro de liga | muros_reforcados, liga_leve, ciencia_militar |
| escudo_1 | Gerador de escudo | ciencia_militar, processador, acumulacao |
| artilharia | Artilharia | torre_foguetes, liga_leve, cartografia |
| ciencia_tempestade | Ciência de tempestade | captador_carga, processador, liga_leve, bioquimica |
| para_raios_2 | Para-raios de cristal | para_raios, ciencia_tempestade |
| acumulador_cristal | Acumulador de cristal | acumulacao_2, ciencia_tempestade |
| reator_cristal | Reator de cristal | energia, ciencia_tempestade |
| fundicao_cristal | Fundição de cristal | fornalha_eletrica, ciencia_tempestade |
| refinador_2 | Refinador 2 | quimica, ciencia_tempestade |
| irradiador_modulos | Irradiador de módulos | modulo_velocidade_1, modulo_eficiencia_1, ciencia_tempestade |
| modulo_velocidade_2 | Módulo de velocidade 2 | modulo_velocidade_1, ciencia_tempestade |
| modulo_eficiencia_2 | Módulo de eficiência 2 | modulo_eficiencia_1, ciencia_tempestade |
| modulo_produtividade_2 | Módulo de produtividade 2 | modulo_produtividade_1, ciencia_tempestade |
| mineracao_3 | Produtividade de mineração 3 | mineracao_2, ciencia_tempestade |
| pesquisa_vel_3 | Velocidade de pesquisa 3 | pesquisa_vel_2, ciencia_tempestade |
| drones_frota_2 | Frota de drones 2 | drones_frota_1, ciencia_tempestade |
| drones_bateria_2 | Bateria de drone 2 | drones_bateria_1, ciencia_tempestade |
| drones_velocidade_2 | Velocidade de drone 2 | drones_velocidade_1, ciencia_tempestade |
| drones_logisticos_2 | Drones logísticos 2 | drones_logisticos, ciencia_tempestade |
| drones_tempestade | Voo na tempestade | drones_bateria_2, para_raios_2 |
| drones_defesa | Drones de defesa | drones_frota_1, dano_energia_3, ciencia_tempestade |
| purificador_ar_2 | Purificador atmosférico | purificador_ar, ciencia_tempestade |
| estacao_tratamento | Estação de tratamento | filtro_agua_limpa, refinador_2 |
| restauracao_bioma | Restauração de bioma | recuperar_solo, ciencia_tempestade |
| semeadura_nuvens | Semeadura de nuvens | condensador_neblina, ciencia_tempestade |
| cupula_tempestade | Cúpula contra raios | para_raios_2, escudo_1 |
| controle_vento | Defletor de vento | semeadura_nuvens, turbina_alta |
| dano_bala_4 | Munição: dano 4 | dano_bala_3, ciencia_tempestade |
| cadencia_bala_3 | Metralhadora: cadência 3 | cadencia_bala_2, ciencia_tempestade |
| municao_cristal | Munição de cristal carregado | municao_perfurante, ciencia_tempestade |
| dano_foguete_2 | Foguetes: dano 2 | dano_foguete_1, ciencia_tempestade |
| cadencia_foguete_2 | Lança-foguetes: cadência 2 | cadencia_foguete_1, ciencia_tempestade |
| foguete_enxame | Foguete de enxame | dano_foguete_2 |
| dano_energia_4 | Torre de energia: dano 4 | dano_energia_3, ciencia_tempestade |
| cadencia_energia_2 | Torre de energia: cadência 2 | cadencia_energia_1, ciencia_tempestade |
| dano_artilharia_1 | Artilharia: dano 1 | artilharia, ciencia_tempestade |
| alcance_artilharia_1 | Artilharia: alcance 1 | artilharia, ciencia_tempestade |
| artilharia_automatica | Mira automática | alcance_artilharia_1, cartografia |
| escudo_2 | Escudo 2 | escudo_1, ciencia_tempestade |
| muro_escudo | Muro de campo | muro_liga, escudo_2 |
| nucleo_semente | Núcleo-semente | posto_avancado, drones_frota_1, ciencia_tempestade |
| colonias | Colônias | nucleo_semente, drones_logisticos |
| computacao_quantica | Computação quântica | ciencia_tempestade, laboratorio_2, energia |
| modulo_velocidade_3 | Módulo de velocidade 3 | modulo_velocidade_2, computacao_quantica |
| modulo_eficiencia_3 | Módulo de eficiência 3 | modulo_eficiencia_2, computacao_quantica |
| modulo_produtividade_3 | Módulo de produtividade 3 | modulo_produtividade_2, computacao_quantica |
| montadora_4 | Montadora quântica | montadora_3, computacao_quantica |
| logistica_5 | Logística 5 | logistica_4, computacao_quantica |
| braco_quantico | Braço quântico | braco_empilhador, computacao_quantica |
| broca_profunda | Broca de núcleo | broca_grande, computacao_quantica |
| laboratorio_3 | Laboratório quântico | laboratorio_2, computacao_quantica |
| fusao | Reator de fusão | reator_cristal, computacao_quantica |
| controle_clima | Regulador climático | controle_vento, cupula_tempestade, computacao_quantica |
| simbiose | Simbiose | restauracao_bioma, harmonia_ninhos, computacao_quantica |
| dano_artilharia_2 | Artilharia: dano 2 | dano_artilharia_1, computacao_quantica |
| alcance_artilharia_2 | Artilharia: alcance 2 | alcance_artilharia_1, computacao_quantica |
| transportador_quantico | Transportador quântico | colonias, computacao_quantica |
| rede_colonias | Mente distribuída | transportador_quantico |
| singularidade | Núcleo de singularidade | fusao, colonias |
| casco_foguete | Casco de liga quântica | liga_leve, computacao_quantica |
| propulsao_cristal | Propulsão de cristal | reator_cristal, computacao_quantica |
| navegacao | Navegação estelar | cartografia, computacao_quantica, colonias |
| silo_lancamento | Silo de lançamento | casco_foguete, propulsao_cristal |
| foguete_proliferacao | Foguete de proliferação | silo_lancamento, navegacao, rede_colonias |
| mineracao_infinita | Produtividade de mineração N | mineracao_3, colonias, computacao_quantica |
| pesquisa_infinita | Velocidade de pesquisa N | pesquisa_vel_3, rede_colonias |
| dano_bala_infinito | Munição: dano N | dano_bala_4, colonias, computacao_quantica |
| dano_foguete_infinito | Foguetes: dano N | dano_foguete_2, colonias, computacao_quantica |
| dano_artilharia_infinito | Artilharia: dano N | dano_artilharia_2, colonias |
| dano_energia_infinito | Torre de energia: dano N | dano_energia_4, colonias, computacao_quantica |
| escudo_infinito | Escudo N | escudo_2, colonias, computacao_quantica |
| drones_infinito | Velocidade de frota N | drones_velocidade_2, colonias, computacao_quantica |
| purificacao_infinita | Purificação N | simbiose, colonias |
| eficiencia_infinita | Eficiência de rede N | fusao, colonias |

## Balanceamento

Base dos números: as pesquisas atuais custam de 8 a 60 unidades de 4 a 8 s; isso continua igual. Daí em diante o custo sobe aos poucos: era base 8–40 unidades de 4–6 s, era do meio 20–100 de 6–10 s, era super avançada 80–400 de 10–20 s, o foguete 1.000 de 20 s e as infinitas 500 de 30 s no nível 1 (× 1,5 a cada nível).

| Era | Tecnologias | Unidades (sem infinitas) | Tempo de laboratório (1 lab, vel. 1,0) | Ritmo esperado | Horas de pesquisa |
|---|---|---|---|---|---|
| Era base | 35 | 836 | 1,3 h | 4 unidades/min, 1–2 laboratórios | 3,5 h |
| Era do meio | 60 | 3.005 | 6,6 h | 10 unidades/min, 2–4 laboratórios (Lab 2 + bônus) | 5,0 h |
| Era super avançada | 71 | 11.810 | 47,8 h | 25 unidades/min, 4–8 laboratórios (Lab quântico + bônus) | 7,9 h |

Somando, são cerca de **16 h só de pesquisa** no ritmo esperado. Com o tempo de montar a fábrica, mudar de lugar, defender e limpar (a pesquisa fica parada boa parte desse tempo), a campanha até o foguete fica em **25 a 35 h**, dentro da meta de 20–40 h para celular. O gargalo é produzir os pacotes, não o laboratório: por isso os laboratórios novos aceleram e os pacotes ficam mais caros de fazer a cada era.

### Era base

| ID | Pacotes (tipo × quantidade) | Tempo por pacote (s) | Libera |
|---|---|---|---|
| defesa | básico × 8 | 4 | Receita munição (2 sílex + 1 placa de cobre) |
| logistica | básico × 12 | 4 | Rampa sobe/desce, passagem subterrânea, braço longo; receita circuito |
| aco | básico × 20 | 5 | Receita barra de aço (fornalha) |
| fluidos | básico × 20 | 5 | Cano, cano em T, cano em cruz, bomba de seiva, tanque |
| limpeza | básico × 10 | 4 | Coletor de lixo, filtro de água |
| eletronica | básico × 20 | 5 | Divisor, junção, braço rápido; receita motor |
| armazenagem | básico × 10 | 4 | Baú grande |
| reflorestar | básico × 16 | 5 | Viveiro |
| muros_reforcados | básico × 10 | 4 | Muro de tijolo (700 ♥, o dobro do muro de pedra) |
| dano_energia_1 | básico × 15 | 4 | +20% de dano da torre básica |
| cano_subterraneo | básico × 15 | 5 | Cano subterrâneo: entrada e saída (até 9 tiles por baixo) |
| sensor_varredura | básico × 20 | 5 | Sensor de varredura 2×2: revela 1 chunk/min até 6 chunks e marca ninhos |
| farol_cristal | básico × 10 | 4 | Farol 1×1: luz de 10 m à noite (mostra a fábrica e as aranhas que chegam) |
| monitor_ambiental | básico × 15 | 5 | Camada Poluição/Sujeira na visão de recursos (V) e aviso de fúria dos ninhos |
| ferrovia | básico × 30 | 6 | Trilho, curva, fim de linha, estação, sinal, trem |
| sem_fio | básico × 30 | 6 | Torre sem fio |
| renovavel | básico × 30 | 6 | Painel solar, turbina eólica |
| briquete | básico × 15 | 5 | Receita briquete (4 biomassa → 1 briquete de 10 MJ; queima com −30% de poluição) |
| automacao | básico × 25 | 5 | Receita pacote de automação; laboratório aceita o pacote |
| torre_metralhadora | básico × 20 | 5 | Metralhadora 2×2 (munição comum, 10 tiros/s) |
| dano_bala_1 | básico × 20 | 5 | +10% de dano das balas |
| cadencia_bala_1 | básico × 20 | 5 | +10% de tiros por segundo |
| montadora_2 | básico × 30 + automação × 30 | 6 | Montadora 2 (velocidade 1,0, 2 encaixes de módulo) |
| logistica_3 | básico × 40 + automação × 40 | 6 | Esteira rápida (3,75 itens/s) com rampa, passagem, divisor e junção rápidos |
| braco_filtro | básico × 30 + automação × 30 | 6 | Braço com filtro (escolhe até 5 itens) |
| divisor_filtro | básico × 25 + automação × 25 | 6 | Divisor com filtro e prioridade de saída |
| fornalha_aco | básico × 30 + automação × 30 | 6 | Fornalha de aço 2×2 (velocidade 2,0, −25% de poluição; queima combustível) |
| mineracao_1 | básico × 40 + automação × 40 | 6 | +10% de minério por ciclo (broca e extrator) |
| pesquisa_vel_1 | básico × 40 + automação × 40 | 6 | +20% de velocidade dos laboratórios |
| trem_automatico | básico × 40 + automação × 40 | 6 | Rotas com condição (esperar cheio, vazio ou tempo) e sinal em cadeia |
| silo_granel | básico × 30 + automação × 30 | 6 | Silo 3×3 (20.000 itens de um só tipo) |
| dano_bala_2 | básico × 40 + automação × 40 | 6 | +15% de dano das balas |
| dano_energia_2 | básico × 40 + automação × 40 | 6 | +20% de dano da torre básica |
| transmissao | básico × 30 + automação × 30 | 6 | Poste alto 1×1 (fio de 30 m, ligação de 3 m) |
| vagao_tanque | básico × 30 + automação × 30 | 6 | Vagão-tanque (25.000 de fluido) e bomba de estação |

### Era do meio

| ID | Pacotes (tipo × quantidade) | Tempo por pacote (s) | Libera |
|---|---|---|---|
| refino | básico × 40 | 6 | Refinador; receitas bateria, núcleo de cristal, módulo de controle |
| acumulacao | básico × 40 | 6 | Acumulador |
| energia | básico × 60 | 8 | Receita célula de energia |
| bomba_agua | básico × 30 + automação × 30 | 6 | Bomba d'água 2×2 (40/s na margem), fluido água, receitas refrigeradas (aço e lapidação com +50%) |
| filtro_agua_limpa | básico × 20 + automação × 20 | 6 | Filtro de água passa a soltar água limpa pelo cano enquanto limpa |
| coletor_chuva | básico × 25 + automação × 25 | 6 | Coletor de chuva 2×2 (até 25/s com chuva forte, tanque de 2.000) |
| condensador_neblina | básico × 30 + automação × 30 | 6 | Condensador de neblina 2×2 (até 12/s com neblina, usa 80 kW) |
| escavar_canal | básico × 20 + automação × 20 | 6 | Terraplenagem cava canal de água (leva o rio até a bomba) |
| supressor_fogo | básico × 25 + automação × 25 | 6 | Supressor 1×1: borrifa água em 8 m, apaga fogo e molha grama seca |
| turbina_rio | básico × 30 + automação × 30 | 6 | Turbina de correnteza 2×2 no rio (150 kW, cai na seca) |
| para_raios | básico × 30 + automação × 30 | 6 | Para-raios 1×1 (pega raios em 14 m; 120 MJ por raio para os acumuladores) |
| ciencia_militar | básico × 40 + automação × 40 | 6 | Receita pacote militar |
| drones | básico × 50 + automação × 50 | 8 | Estação de drones 2×2 (frota de 8, alcance 45 m, 50 de água por drone) |
| drones_bateria_1 | básico × 40 + automação × 40 | 8 | +30% de tempo de voo dos drones |
| quimica | básico × 50 + automação × 50 | 8 | Receitas resina e pacote químico (refinador) |
| liga_leve | básico × 40 + automação × 40 + químico × 40 | 8 | Receita liga leve (1 aço + 2 placas de cobre + 1 resina → 2) |
| processador | básico × 60 + automação × 60 + químico × 60 | 8 | Receita processador (2 circuitos + 1 resina + 1 cristal lapidado + 5 água) |
| bioquimica | básico × 40 + automação × 40 + químico × 40 | 8 | Receita pacote ecológico |
| combustivel_seiva | básico × 40 + automação × 40 + químico × 40 | 8 | Receita combustível de seiva (fluido) e gerador a fluido 3×3 (2,4 MW) |
| fornalha_eletrica | básico × 50 + automação × 50 + químico × 50 | 8 | Fornalha elétrica 2×2 (velocidade 2,0, sem combustível, 2 encaixes de módulo) |
| captador_carga | básico × 60 + automação × 60 + químico × 60 | 8 | Captador de carga 2×2 e o item cristal carregado (1 lapidado + 30 água por raio) |
| logistica_4 | básico × 60 + automação × 60 + químico × 60 | 8 | Esteira expressa (5,625 itens/s) com rampa, passagem, divisor e junção expressos |
| braco_empilhador | básico × 50 + automação × 50 + químico × 50 | 8 | Braço empilhador (leva até 4 itens por vez) |
| montadora_3 | básico × 60 + automação × 60 + químico × 60 | 8 | Montadora 3 (velocidade 1,5, 4 encaixes de módulo) |
| rede_logica | básico × 40 + automação × 40 + químico × 40 | 8 | Sensor de esteira, sensor de tanque, comparador e válvula (1×1) |
| modulo_velocidade_1 | básico × 50 + automação × 50 + químico × 50 | 8 | Módulo de velocidade 1 (+20% velocidade, +50% energia) |
| modulo_eficiencia_1 | básico × 50 + automação × 50 + químico × 50 | 8 | Módulo de eficiência 1 (−30% energia e −30% poluição) |
| modulo_produtividade_1 | básico × 75 + automação × 75 + químico × 75 | 8 | Módulo de produtividade 1 (+4% produto, −15% velocidade, +40% poluição) |
| broca_grande | básico × 50 + automação × 50 + químico × 50 | 8 | Broca grande 3×3 (2,5× velocidade, −20% de poluição por minério) |
| extrator_2 | básico × 50 + automação × 50 + químico × 50 | 8 | Extrator ressonante 3×3 (2× velocidade no cristal) |
| mineracao_2 | básico × 60 + automação × 60 + químico × 60 | 8 | +10% de minério por ciclo |
| pesquisa_vel_2 | básico × 60 + automação × 60 + químico × 60 | 8 | +30% de velocidade dos laboratórios |
| laboratorio_2 | básico × 80 + automação × 80 + químico × 80 | 8 | Laboratório 2 3×3 (2× velocidade, 2 encaixes de módulo) |
| drones_frota_1 | básico × 40 + automação × 40 + químico × 40 | 8 | +4 drones por estação (8 → 12) |
| drones_velocidade_1 | básico × 40 + automação × 40 + químico × 40 | 8 | +25% de velocidade dos drones |
| drones_logisticos | básico × 75 + automação × 75 + químico × 75 | 10 | Porto logístico 2×2, baú provedor, baú requisitante e baú de estoque (1×1) |
| renovavel_2 | básico × 60 + automação × 60 + químico × 60 | 8 | Painel solar 2 (2×2, 500 kW, rende 15% com nuvem) |
| turbina_alta | básico × 60 + automação × 60 + químico × 60 | 8 | Turbina alta 3×3 (600 kW, conta como +2 níveis de altura no vento) |
| acumulacao_2 | básico × 60 + automação × 60 + químico × 60 | 8 | Acumulador 2 (2×2, 200 MJ, 1,5 MW) |
| trem_eletrico | básico × 60 + automação × 60 + químico × 60 | 8 | Trilho energizado e locomotiva elétrica (2× velocidade, sem poluição) |
| cartografia | básico × 50 + automação × 50 + químico × 50 | 8 | Sensor de varredura 2: até 16 chunks e mostra a riqueza das jazidas |
| coletor_lixo_2 | básico × 40 + automação × 40 + químico × 40 + ecológico × 40 | 8 | Coletor de lixo 2 (raio 10, recolhe cinza e devolve o item resíduo) |
| purificador_ar | básico × 50 + automação × 50 + químico × 50 + ecológico × 50 | 8 | Purificador de ar 2×2 (absorve 6 de poluição/min do chunk) |
| viveiro_2 | básico × 50 + automação × 50 + químico × 50 + ecológico × 50 | 8 | Viveiro 2 (raio 12, escolhe a espécie do bioma, mudas crescem 2× mais rápido) |
| biodigestor | básico × 50 + automação × 50 + químico × 50 + ecológico × 50 | 8 | Biodigestor 3×3 (resíduo + água suja → biomassa + seiva) |
| recuperar_solo | básico × 60 + automação × 60 + químico × 60 + ecológico × 60 | 8 | Terraplenagem recupera chão queimado, sujo ou com óleo |
| harmonia_ninhos | básico × 60 + automação × 60 + químico × 60 + ecológico × 60 | 8 | Ninho com fúria 0 não expande na direção da fábrica; −25% de grupos de ataque |
| municao_perfurante | básico × 40 + automação × 40 + militar × 40 | 8 | Receita munição perfurante (+60% dano, atravessa 1 aranha) |
| dano_bala_3 | básico × 60 + automação × 60 + militar × 60 | 8 | +20% de dano das balas |
| cadencia_bala_2 | básico × 60 + automação × 60 + militar × 60 | 8 | +20% de tiros por segundo |
| dano_energia_3 | básico × 60 + automação × 60 + militar × 60 | 8 | +30% de dano da torre básica |
| cadencia_energia_1 | básico × 50 + automação × 50 + militar × 50 | 8 | +20% de tiros por segundo e −10% de energia por tiro |
| mina_pulso | básico × 30 + automação × 30 + militar × 30 | 8 | Mina de pulso 1×1 (atordoa aranhas por 3 s, rearma em 20 s) |
| posto_avancado | básico × 50 + automação × 50 + militar × 50 | 8 | Posto avançado 3×3: núcleo-filho com estoque próprio e 150 kW sem fio |
| torre_foguetes | básico × 60 + automação × 60 + militar × 60 + químico × 60 | 8 | Lança-foguetes 3×3 e receita foguete (dano em área) |
| dano_foguete_1 | básico × 60 + automação × 60 + militar × 60 + químico × 60 | 8 | +20% de dano dos foguetes |
| cadencia_foguete_1 | básico × 60 + automação × 60 + militar × 60 + químico × 60 | 8 | +20% de disparos por segundo |
| muro_liga | básico × 40 + automação × 40 + militar × 40 + químico × 40 | 8 | Muro de liga (1.500 ♥, aranhas não escalam) |
| escudo_1 | básico × 75 + automação × 75 + militar × 75 + químico × 75 | 10 | Gerador de escudo 2×2 (bolha de 8 m que absorve 400 de dano, recarrega pela rede) |
| artilharia | básico × 100 + automação × 100 + militar × 100 + químico × 100 | 10 | Artilharia 3×3 e receita granada (alcance 120 m contra ninhos) |

### Era super avançada

| ID | Pacotes (tipo × quantidade) | Tempo por pacote (s) | Libera |
|---|---|---|---|
| ciencia_tempestade | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 | 10 | Receita pacote de tempestade |
| para_raios_2 | básico × 80 + automação × 80 + químico × 80 + ecológico × 80 + tempestade × 80 | 10 | Para-raios de cristal 1×1 (22 m, 200 MJ por raio) |
| acumulador_cristal | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Acumulador de cristal 2×2 (600 MJ, 4 MW) |
| reator_cristal | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Reator de cristal 3×3 (8 MW, queima célula de energia ou cristal carregado) |
| fundicao_cristal | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Fundição de cristal 3×3 (velocidade 4,0, 4 encaixes, funde direto do minério para aço) |
| refinador_2 | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Refinador 2 3×3 (velocidade 2,0, 3 encaixes, devolve 50% menos água suja) |
| irradiador_modulos | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Irradiador 3×3: divide o efeito de 2 módulos com as máquinas em 3 tiles |
| modulo_velocidade_2 | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | Módulo de velocidade 2 (+30%) |
| modulo_eficiencia_2 | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | Módulo de eficiência 2 (−40% energia e poluição) |
| modulo_produtividade_2 | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Módulo de produtividade 2 (+6% produto) |
| mineracao_3 | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +10% de minério por ciclo |
| pesquisa_vel_3 | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +40% de velocidade dos laboratórios |
| drones_frota_2 | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | +8 drones por estação (12 → 20) |
| drones_bateria_2 | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | +50% de tempo de voo |
| drones_velocidade_2 | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | +35% de velocidade dos drones |
| drones_logisticos_2 | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Drone logístico leva 4 itens; porto com 2× alcance |
| drones_tempestade | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | Drones blindados: voam com raios caindo na área |
| drones_defesa | básico × 120 + automação × 120 + militar × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | +100% de dano dos drones em combate e +50% de vida |
| purificador_ar_2 | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Purificador atmosférico 3×3 (absorve 40 de poluição/min) |
| estacao_tratamento | básico × 100 + automação × 100 + químico × 100 + ecológico × 100 + tempestade × 100 | 12 | Estação de tratamento 3×3: água suja → água limpa (60/s), limpa o rio em 16 m |
| restauracao_bioma | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Semeador de bioma 3×3: devolve cinzal e terra queimada à vegetação original |
| semeadura_nuvens | básico × 120 + automação × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Semeador de nuvens 2×2: chama chuva num raio de 40 m (apaga fogo, enche coletores) |
| cupula_tempestade | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Cúpula 3×3: nenhum raio cai num raio de 30 m |
| controle_vento | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Defletor 2×2: fixa a direção do vento em 40 m (poluição longe dos ninhos) |
| dano_bala_4 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +20% de dano das balas |
| cadencia_bala_3 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +20% de tiros por segundo |
| municao_cristal | básico × 120 + automação × 120 + militar × 120 + químico × 120 + ecológico × 120 + tempestade × 120 | 12 | Receita munição carregada (dano elétrico salta para 2 aranhas) |
| dano_foguete_2 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +30% de dano dos foguetes |
| cadencia_foguete_2 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +20% de disparos por segundo |
| foguete_enxame | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Receita foguete de enxame (abre em 4 ogivas menores) |
| dano_energia_4 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +30% de dano da torre básica |
| cadencia_energia_2 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +20% de tiros por segundo |
| dano_artilharia_1 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +30% de dano das granadas |
| alcance_artilharia_1 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | +20% de alcance (120 → 144 m) |
| artilharia_automatica | básico × 200 + automação × 200 + militar × 200 + químico × 200 + ecológico × 200 + tempestade × 200 | 12 | Artilharia dispara sozinha em ninhos revelados no alcance |
| escudo_2 | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Gerador de escudo: bolha de 12 m, 1.000 de dano, recarga 2× |
| muro_escudo | básico × 150 + automação × 150 + militar × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Muro de campo 1×1 (regenera 5 ♥/s com energia) |
| nucleo_semente | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Receita núcleo-semente e lançador de sementes 3×3 (alcance 400 m) |
| colonias | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 | 12 | Semente pousada vira colônia (kit + 2 drones) que fabrica pacote gênese; receptor de cápsulas 2×2 |
| computacao_quantica | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 | 12 | Forja quântica 3×3; receitas processador quântico e pacote quântico |
| modulo_velocidade_3 | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 + quântico × 200 | 15 | Módulo de velocidade 3 (+50%) |
| modulo_eficiencia_3 | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 + quântico × 200 | 15 | Módulo de eficiência 3 (−50% energia e poluição) |
| modulo_produtividade_3 | básico × 300 + automação × 300 + químico × 300 + ecológico × 300 + tempestade × 300 + quântico × 300 | 15 | Módulo de produtividade 3 (+10% produto) |
| montadora_4 | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 + quântico × 200 | 15 | Montadora quântica 3×3 (velocidade 2,5, 4 encaixes, 2 receitas ao mesmo tempo) |
| logistica_5 | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 + quântico × 200 | 15 | Esteira quântica (7,5 itens/s) com rampa, passagem, divisor e junção quânticos |
| braco_quantico | básico × 150 + automação × 150 + químico × 150 + ecológico × 150 + tempestade × 150 + quântico × 150 | 15 | Braço quântico (ciclo 0,2 s, 8 itens por vez, alcance 1 a 3) |
| broca_profunda | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 + quântico × 200 | 15 | Broca de núcleo 3×3: jazida esgotada continua rendendo 10% para sempre |
| laboratorio_3 | básico × 200 + automação × 200 + químico × 200 + ecológico × 200 + tempestade × 200 + quântico × 200 | 15 | Laboratório quântico 3×3 (4× velocidade, 4 encaixes) |
| fusao | básico × 300 + automação × 300 + químico × 300 + ecológico × 300 + tempestade × 300 + quântico × 300 | 15 | Reator de fusão 3×3 (30 MW; consome água e cristal carregado) |
| controle_clima | básico × 400 + automação × 400 + militar × 400 + químico × 400 + ecológico × 400 + tempestade × 400 + quântico × 400 | 20 | Regulador 3×3: escolhe o clima num raio de 80 m |
| simbiose | básico × 300 + automação × 300 + químico × 300 + ecológico × 300 + tempestade × 300 + quântico × 300 | 15 | Estruturas viram abrigo de musgo: −50% de poluição global; ninhos em paz não atacam |
| dano_artilharia_2 | básico × 250 + automação × 250 + militar × 250 + químico × 250 + ecológico × 250 + tempestade × 250 + quântico × 250 | 15 | +40% de dano das granadas |
| alcance_artilharia_2 | básico × 250 + automação × 250 + militar × 250 + químico × 250 + ecológico × 250 + tempestade × 250 + quântico × 250 | 15 | +30% de alcance |
| transportador_quantico | básico × 300 + automação × 300 + químico × 300 + ecológico × 300 + tempestade × 300 + quântico × 300 | 15 | Transportador quântico 3×3: troca itens entre colônias sem trilho |
| rede_colonias | básico × 300 + automação × 300 + químico × 300 + ecológico × 300 + tempestade × 300 + quântico × 300 + gênese × 300 | 15 | Laboratórios das colônias somam na pesquisa; colônias trocam energia |
| singularidade | básico × 500 + automação × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 20 | Núcleo de singularidade 3×3 (100 MW, sem poluição) |
| casco_foguete | básico × 250 + automação × 250 + químico × 250 + ecológico × 250 + tempestade × 250 + quântico × 250 | 15 | Receita casco de foguete |
| propulsao_cristal | básico × 250 + automação × 250 + químico × 250 + ecológico × 250 + tempestade × 250 + quântico × 250 | 15 | Receita propelente de cristal (fluido) |
| navegacao | básico × 300 + automação × 300 + químico × 300 + ecológico × 300 + tempestade × 300 + quântico × 300 | 15 | Receita mapa estelar (cartão de rota do foguete) |
| silo_lancamento | básico × 400 + automação × 400 + químico × 400 + ecológico × 400 + tempestade × 400 + quântico × 400 | 20 | Silo de lançamento 3×3 (monta o foguete por 100 partes) |
| foguete_proliferacao | básico × 1000 + automação × 1000 + militar × 1000 + químico × 1000 + ecológico × 1000 + tempestade × 1000 + quântico × 1000 + gênese × 1000 | 20 | Receita carga-semente; lançar o foguete = fim da campanha |
| mineracao_infinita | básico × 500 + automação × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de minério por nível — infinita (custo × 1,5 por nível) |
| pesquisa_infinita | básico × 500 + automação × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de velocidade dos laboratórios por nível — infinita (custo × 1,5 por nível) |
| dano_bala_infinito | básico × 500 + automação × 500 + militar × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de dano das balas por nível — infinita (custo × 1,5 por nível) |
| dano_foguete_infinito | básico × 500 + automação × 500 + militar × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de dano dos foguetes por nível — infinita (custo × 1,5 por nível) |
| dano_artilharia_infinito | básico × 500 + automação × 500 + militar × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de dano das granadas por nível — infinita (custo × 1,5 por nível) |
| dano_energia_infinito | básico × 500 + automação × 500 + militar × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de dano da torre básica por nível — infinita (custo × 1,5 por nível) |
| escudo_infinito | básico × 500 + automação × 500 + militar × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +15% de capacidade de escudo por nível — infinita (custo × 1,5 por nível) |
| drones_infinito | básico × 500 + automação × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de velocidade de drones e trens por nível — infinita (custo × 1,5 por nível) |
| purificacao_infinita | básico × 500 + automação × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | +10% de limpeza de coletores, filtros e purificadores por nível — infinita (custo × 1,5 por nível) |
| eficiencia_infinita | básico × 500 + automação × 500 + químico × 500 + ecológico × 500 + tempestade × 500 + quântico × 500 + gênese × 500 | 30 | −5% de consumo de energia de todas as máquinas por nível (até −50%) — infinita (custo × 1,5 por nível) |

## Estruturas: temos × precisamos

Tamanhos na grade de tiles. "Temos" = já está em `estruturas.json`/`menu_construcao.json` com modelo; "falta" = modelo,
regra e ícone a criar (todas no estilo high-tech de IA: cristal, metal escovado, luzes; nada humano, sem portas,
janelas ou chaminés). Peças de níveis (esteira rápida/expressa/quântica, montadoras, laboratórios) podem reaproveitar o
modelo do nível anterior com outra cor de luz e detalhe.

### Esteiras
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Esteira (reta, curvas, início, fim, junção) | 1×1 | temos | leva 1,875 itens/s | início |
| Rampa sobe / rampa desce | 1×1 | temos | sobe/desce 0,5 m | `logistica` |
| Passagem: entrada / saída | 1×1 | temos | leva por baixo até 4 tiles | `logistica` |
| Divisor / junção | 1×1 | temos | reparte em 3 / junta 3 | `eletronica` |
| Divisor com filtro | 1×1 | falta | manda um item escolhido para uma saída e dá prioridade a outra | `divisor_filtro` |
| Esteira rápida + rampa, passagem (6 tiles), divisor e junção rápidos | 1×1 | falta | 3,75 itens/s | `logistica_3` |
| Esteira expressa + rampa, passagem (8 tiles), divisor e junção expressos | 1×1 | falta | 5,625 itens/s | `logistica_4` |
| Esteira quântica + rampa, passagem (10 tiles), divisor e junção quânticos | 1×1 | falta | 7,5 itens/s | `logistica_5` |

### Braços
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Braço | 1×1 | temos | pega atrás e solta na frente (0,83 s) | início |
| Braço rápido | 1×1 | temos | ciclo 0,42 s | `eletronica` |
| Braço longo | 1×1 | temos | alcança 2 tiles | `logistica` |
| Baú | 1×1 | temos | 1.600 itens | início |
| Baú grande | 2×2 | temos | 6.400 itens | `armazenagem` |
| Braço com filtro | 1×1 | falta | só pega os itens escolhidos (até 5) | `braco_filtro` |
| Braço empilhador | 1×1 | falta | leva até 4 itens por ciclo | `braco_empilhador` |
| Braço quântico | 1×1 | falta | ciclo 0,2 s, 8 itens, alcance ajustável 1–3 | `braco_quantico` |
| Silo de granel | 3×3 | falta | 20.000 itens de um tipo só | `silo_granel` |

### Canos
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Cano (reta, curva), cano em T, cano em cruz | 1×1 | temos | leva fluido (100 por peça) | `fluidos` |
| Bomba (seiva) | 1×1 | temos | tira seiva da poça | `fluidos` |
| Tanque | 2×2 | temos | guarda 25.000 | `fluidos` |
| Cano subterrâneo: entrada / saída | 1×1 | falta | passa o cano por baixo até 9 tiles | `cano_subterraneo` |
| Bomba d'água | 2×2 | falta | na margem de rio/lago/canal: 40 de água/s | `bomba_agua` |
| Coletor de chuva | 2×2 | falta | até 25/s com chuva forte, tanque de 2.000 | `coletor_chuva` |
| Condensador de neblina | 2×2 | falta | até 12/s com neblina, 80 kW | `condensador_neblina` |

### Produção
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Extrator de cristal | 3×3 | temos | cristal bruto da jazida | início |
| Broca | 2×2 | temos | minério, carvão, pedra, sílex, areia | início |
| Fornalha | 2×2 | temos | funde com carvão | início |
| Montadora | 3×3 | temos | monta por receita (vel. 0,75) | início |
| Refinador | 3×3 | temos | receitas com fluido | `refino` |
| Laboratório | 3×3 | temos | pesquisa com pacotes | início |
| Terraplenagem | 3×3 | temos | libera aplainar (e, com pesquisa, cavar canal e recuperar solo) | início |
| Fornalha de aço | 2×2 | falta | vel. 2,0 com combustível, −25% de poluição | `fornalha_aco` |
| Fornalha elétrica | 2×2 | falta | vel. 2,0 sem combustível, 2 módulos | `fornalha_eletrica` |
| Fundição de cristal | 3×3 | falta | vel. 4,0, 4 módulos, minério direto em aço | `fundicao_cristal` |
| Montadora 2 / Montadora 3 | 3×3 | falta | vel. 1,0 e 2 módulos / vel. 1,5 e 4 módulos | `montadora_2`, `montadora_3` |
| Montadora quântica | 3×3 | falta | vel. 2,5, 4 módulos, 2 receitas ao mesmo tempo | `montadora_4` |
| Refinador 2 | 3×3 | falta | vel. 2,0, 3 módulos, menos água suja | `refinador_2` |
| Forja quântica | 3×3 | falta | processador quântico, pacote quântico, mapa estelar | `computacao_quantica` |
| Broca grande | 3×3 | falta | 2,5× mais rápida, −20% de poluição por minério | `broca_grande` |
| Extrator ressonante | 3×3 | falta | 2× mais rápido no cristal | `extrator_2` |
| Broca de núcleo | 3×3 | falta | jazida esgotada rende 10% para sempre | `broca_profunda` |
| Laboratório 2 / Laboratório quântico | 3×3 | falta | 2× e 2 módulos / 4× e 4 módulos | `laboratorio_2`, `laboratorio_3` |
| Irradiador de módulos | 3×3 | falta | divide 2 módulos com as máquinas em 3 tiles | `irradiador_modulos` |

### Limpeza
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Coletor de lixo | 2×2 | temos | aspira sujeira e óleo (raio 6) | `limpeza` |
| Filtro de água | 2×2 | temos | limpa água suja (raio 7); com pesquisa, solta água limpa | `limpeza`, `filtro_agua_limpa` |
| Viveiro | 2×2 | temos | planta mudas com seiva (raio 8) | `reflorestar` |
| Supressor de incêndio | 1×1 | falta | borrifa água em 8 m, apaga fogo | `supressor_fogo` |
| Coletor de lixo 2 | 2×2 | falta | raio 10, recolhe cinza, devolve resíduo | `coletor_lixo_2` |
| Purificador de ar | 2×2 | falta | absorve 6 de poluição/min do chunk | `purificador_ar` |
| Purificador atmosférico | 3×3 | falta | absorve 40 de poluição/min | `purificador_ar_2` |
| Viveiro 2 | 2×2 | falta | raio 12, espécie do bioma, 2× mais rápido | `viveiro_2` |
| Biodigestor | 3×3 | falta | resíduo + água suja → biomassa + seiva | `biodigestor` |
| Estação de tratamento | 3×3 | falta | água suja → limpa (60/s) e limpa o rio em 16 m | `estacao_tratamento` |
| Semeador de bioma | 3×3 | falta | devolve cinzal e terra queimada ao bioma original | `restauracao_bioma` |

### Energia
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Gerador | 2×2 | temos | 900 kW queimando combustível | início |
| Painel solar | 2×2 | temos | até 300 kW de dia | `renovavel` |
| Turbina eólica | 2×2 | temos | até 200 kW com vento | `renovavel` |
| Acumulador | 2×2 | temos | 80 MJ, 500 kW | `acumulacao` |
| Poste | 1×1 | temos | fio de 9 m | início |
| Torre sem fio | 1×1 | temos | fio de 40 m sem cabo | `sem_fio` |
| Poste alto | 1×1 | falta | fio de 30 m | `transmissao` |
| Turbina de correnteza | 2×2 | falta | 150 kW no rio, cai na seca | `turbina_rio` |
| Gerador a fluido | 3×3 | falta | 2,4 MW com combustível de seiva | `combustivel_seiva` |
| Painel solar 2 | 2×2 | falta | 500 kW, 15% com nuvem | `renovavel_2` |
| Turbina alta | 3×3 | falta | 600 kW, conta +2 níveis de altura | `turbina_alta` |
| Acumulador 2 | 2×2 | falta | 200 MJ, 1,5 MW | `acumulacao_2` |
| Acumulador de cristal | 2×2 | falta | 600 MJ, 4 MW | `acumulador_cristal` |
| Reator de cristal | 3×3 | falta | 8 MW com célula de energia ou cristal carregado | `reator_cristal` |
| Reator de fusão | 3×3 | falta | 30 MW com água e cristal carregado | `fusao` |
| Núcleo de singularidade | 3×3 | falta | 100 MW, sem poluição | `singularidade` |

### Defesa
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Torre (energia) | 2×2 | temos | tiro a energia da rede, munição como reserva | início |
| Muro (pedra) | 1×1 | temos | 350 ♥, barra aranhas | início |
| Metralhadora | 2×2 | falta | munição comum, 10 tiros/s, alcance 18 m | `torre_metralhadora` |
| Lança-foguetes | 3×3 | falta | foguetes, dano em área, alcance 30 m | `torre_foguetes` |
| Artilharia | 3×3 | falta | granadas, alcance 120 m, mira em ninhos | `artilharia` |
| Muro de tijolo | 1×1 | falta | 700 ♥ | `muros_reforcados` |
| Muro de liga | 1×1 | falta | 1.500 ♥, aranha não escala | `muro_liga` |
| Muro de campo | 1×1 | falta | regenera 5 ♥/s com energia | `muro_escudo` |
| Mina de pulso | 1×1 | falta | atordoa aranhas 3 s, rearma em 20 s | `mina_pulso` |
| Gerador de escudo | 2×2 | falta | bolha de 8–12 m que absorve dano | `escudo_1` |

### Trilhos
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Trilho, curva, fim de linha | 1×1 (curva no modelo atual) | temos | caminho do trem | `ferrovia` |
| Estação | 2×3 | temos | trem carrega e descarrega | `ferrovia` |
| Sinal | 1×1 | temos | divide a linha em blocos | `ferrovia` |
| Trem (locomotiva) | sobre trilho | temos | leva carga | `ferrovia` |
| Sinal em cadeia | 1×1 | falta | só libera a entrada se a saída do cruzamento estiver livre | `trem_automatico` |
| Vagão-tanque | sobre trilho | falta | 25.000 de fluido | `vagao_tanque` |
| Bomba de estação | 1×1 | falta | enche/esvazia vagão-tanque | `vagao_tanque` |
| Trilho energizado | 1×1 | falta | dá energia à locomotiva elétrica | `trem_eletrico` |
| Locomotiva elétrica | sobre trilho | falta | 2× velocidade, sem poluição | `trem_eletrico` |

### Clima (categoria nova)
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Para-raios | 1×1 | falta | pega raios em 14 m, 120 MJ por raio | `para_raios` |
| Para-raios de cristal | 1×1 | falta | 22 m, 200 MJ por raio | `para_raios_2` |
| Captador de carga | 2×2 | falta | transforma cristal lapidado + água em cristal carregado a cada raio | `captador_carga` |
| Semeador de nuvens | 2×2 | falta | chama chuva em 40 m | `semeadura_nuvens` |
| Defletor de vento | 2×2 | falta | fixa a direção do vento em 40 m | `controle_vento` |
| Cúpula contra raios | 3×3 | falta | nenhum raio em 30 m | `cupula_tempestade` |
| Regulador climático | 3×3 | falta | escolhe o clima em 80 m | `controle_clima` |

### Drones (categoria nova)
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Estação de drones | 2×2 | falta | fabrica e abriga drones de reparo (8 a 20) | `drones` |
| Porto logístico | 2×2 | falta | base dos drones logísticos | `drones_logisticos` |
| Baú provedor / requisitante / de estoque | 1×1 | falta | oferece, pede e guarda itens para os drones | `drones_logisticos` |

### Lógica (categoria nova)
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Sensor de esteira | 1×1 | falta | conta itens que passam | `rede_logica` |
| Sensor de tanque | 1×1 | falta | lê o nível de um tanque | `rede_logica` |
| Comparador | 1×1 | falta | liga/desliga máquinas, braços e bombas por condição | `rede_logica` |
| Válvula | 1×1 | falta | só deixa passar fluido acima/abaixo de um nível | `rede_logica` |

### Proliferação (categoria nova)
| Peça | Tamanho | Situação | O que faz | Pesquisa |
|---|---|---|---|---|
| Sensor de varredura | 2×2 | falta | revela o mapa em volta e marca ninhos (nível 2: 16 chunks e riqueza) | `sensor_varredura`, `cartografia` |
| Farol de cristal | 1×1 | falta | luz de 10 m à noite | `farol_cristal` |
| Posto avançado | 3×3 | falta | núcleo-filho: estoque próprio e 150 kW sem fio | `posto_avancado` |
| Lançador de sementes | 3×3 | falta | lança um núcleo-semente até 400 m | `nucleo_semente` |
| Receptor de cápsulas | 2×2 | falta | recebe os pacotes gênese das colônias | `colonias` |
| Transportador quântico | 3×3 | falta | troca itens entre colônias | `transportador_quantico` |
| Silo de lançamento | 3×3 | falta | monta e lança o foguete de proliferação | `silo_lancamento` |

**Contagem:** 34 linhas "temos" e **76 linhas "falta"** (uma linha pode juntar variantes, como a família da esteira
rápida ou os três baús logísticos), em 8 categorias atuais e 4 novas (Clima, Drones, Lógica, Proliferação).

## Decisões e pontos em aberto

- **Água na base continua seca (decidido).** Fundir aço e lapidar cristal ficam sem água, como hoje. A pesquisa
  `bomba_agua` libera as versões **refrigeradas** dessas duas receitas (com água, +50% de produto). Assim nada que já
  funciona quebra.
- **As 14 pesquisas originais não mudam** (a 15ª, `dano_energia_1`, entrou depois como a primeira melhoria jogável: +20% de dano da torre com energia). Mesmos IDs, pré-requisitos e custos (incluindo `energia`, que existe no jogo
  mesmo fora da lista do pedido). `refino`, `acumulacao` e `energia` ficam na era do meio, ainda pagas só com pacote
  básico, como hoje.
- **Torre básica a energia** continua liberada no início; `defesa` segue sendo a receita de munição.
- **Pacote gênese** prende o fim de jogo à proliferação: sem colônias não há infinitas nem foguete.
- **Tamanho máximo 3×3**, inclusive o silo de lançamento (o foguete é montado por partes dentro dele).

