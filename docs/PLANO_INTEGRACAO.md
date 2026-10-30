# Plano de integração dos estudos no jogo (pedido de Sapyst, 2026-10-30)

Regras (dela): **um item por vez** (nada de vários agentes ao mesmo tempo), **sem fotos, vídeos ou gravações**,
**não compilar** (sem APK/exe), testar no PC. Tudo funcional **de acordo com a árvore de tecnologia**
(docs/ARVORE_TECNOLOGIA.md, jogo/dados/arvore.json, progressao.json). Sem "overdoing" nas artes novas, mas no
mesmo nível das já feitas (GUIA em arte/estudos/GUIA_ESTUDOS.md).

Ferramenta: arte/estudos/para_jogo.py (+ conv_*.py). Verificação: jogo/ferramentas/testar.sh; commit a cada item.

## Fase 1 — trocar o visual das estruturas que já existem (1 por vez)
Feito: fornalha, broca_minerio, montadora, extrator_cristal, refinador, laboratorio, terraplenagem, gerador,
painel_solar, acumulador, coletor_lixo, filtro_agua, viveiro, nucleo.
Em andamento / a fazer, nesta ordem:
- [x] torre_defesa, turbina_eolica, poste_energia, torre_sem_fio, muro_centro/muro_lado (conv_defesa_energia.py)
- [x] cano_reto, cano_curva, cano_t, cano_cruz, bomba, tanque (conv_logistica.py) — bomba ficou 1,10 m (esteira elevada a 1 m não passa mais por cima)
- [x] bau, bau_grande, estacao (conv_logistica.py)
- [x] trilho_reto, trilho_curva, trilho_fim, sinal_trem, locomotiva, vagao_carga, vagao_tanque (conv_trilhos.py)
      Pendências: para-choque do fim de linha 0,18 m dentro do fim da trilha; reconverter tudo de novo no fim
      (correção das pintas pretas do assado entrou depois dos outros).
- [x] esteiras (reta, curvas, início, fim, junção, rampa, túnel, divisor, juncao) e braços (braco, rapido, longo)
      (conv_esteiras_bracos.py — lona P_Esteira rolando, IK do braço)

## Fase 2 — estruturas novas que já têm estudo: modelo + sistema + pesquisa jogável (1 por vez)
Ordem pela árvore (pré-requisitos primeiro). Cada uma: converter, regra em estruturas.json, receita/itens se
preciso, sistema em jogo/simulacao (ou onde couber), pesquisa em progressao.json (tirar o "em breve"), testes.
Base: pacote de automação (destrava metade da árvore) e água como insumo (bomba d'água → refrigeradas +50%).
Lista: ver docs/ARVORE_TECNOLOGIA.md (Estruturas: temos × precisamos) e arte/estudos/.

## Fase 3 — artes que faltam (lotes 16, 17, 13, 10, 14, 11), 1 por vez, mais enxutas no processo
## Fase 4 — inserir essas no jogo, 1 por vez, como na fase 2

## Fase 5 — só no fim de TUDO (a árvore inteira funcional): fotos no jogo + baterias de testes
Sapyst: "vai terminar literalmente toda a tech-tree e tudo mais. Faltando só as fotos com testes mesmo."
Entrega: TODAS as estruturas num ÚNICO painel (uma imagem/página com todas as fotos juntas, ex.: mosaico ou página
com a grade inteira + resultado dos testes), para ela não precisar abrir uma por uma.

### Progresso da fase 2
- [x] 2.1 pacotes por tipo, automação, melhorias (mineração, pesquisa, dano/cadência de energia), briquete,
      leitura ambiental, infinitas (algumas travadas por pré-requisitos "em breve")
- [x] 2.2a combate da era base: metralhadora (munição, dano/cadência de bala), muro de tijolo
      (arte/estudos/conv_combate.py → torre_metralhadora, muro_tijolo, muro_tijolo_lado; testes test_metralhadora.gd e
      test_muro_tijolo.gd). Metralhadora: só bala (a munição da árvore, 2 sílex + 1 placa de cobre, receita da pesquisa
      "defesa" — não precisou item novo), 10 tiros/s, 3 de dano, 18 m, começa vazia e guarda 200 tiros (braço não
      entrega na cheia); pesquisas torre_metralhadora, dano_bala_1, cadencia_bala_1 e dano_bala_2 jogáveis (bônus
      dano_bala/cadencia_bala). Tambor gira na rajada; todo tiro (metralhadora e torre de energia) ejeta cápsula com
      fumacinha pela calha do modelo ("ejecao" em modelos.json; DesenhoColonia). Muro de tijolo: 700 ♥, 5 tijolos,
      pesquisa muros_reforcados; pilar de tijolo liga com pano de tijolo (e com muro de pedra vizinho).
      A árvore NÃO exige ciência militar para a metralhadora → pacote_militar/ciencia_militar ficam para a 2.4.
      Pendências: (1) nada foi visto em imagem (sem fotos): conferir na próxima rodada de fotos a silhueta da
      metralhadora (7.808 triângulos, um pouco acima da torre de energia, 7.196), as cascas do muro de tijolo e se
      a cápsula/fumacinha ficam visíveis no zoom normal; (2) o radar do casulo e a implantação do estudo (quadros
      101–196) não entram no jogo (o radar fica parado; a construção usa a Montagem genérica); (3) só a cápsula é
      ejetada (os elos da cinta, não); (4) "ejecao" da torre de energia foi posto à mão em
      arte/modelos/defesa/torre_defesa/torre_defesa.json a partir da PORTA do estudo (sobrevive à reconversão);
      (5) a recarga das torres agora guarda a sobra do tick: a torre de energia dá 3 tiros/s exatos a 30 quadros/s
      (antes ~2,7/s por arredondamento); (6) ícones da barra das 3 peças novas feitos com o mesmo render Workbench do
      icones.py (só esses 3).
- [x] 2.2b logística da era base (arte/estudos/conv_logistica_base.py; testes test_esteira_rapida.gd, test_braco_filtro.gd,
      test_divisor_filtro.gd, test_silo_granel.gd, test_cano_subterraneo.gd). Pesquisas logistica_3, braco_filtro,
      divisor_filtro, silo_granel e cano_subterraneo jogáveis (pré-requisitos e pacotes da árvore; nenhum pacote novo).
  - Esteira rápida (logistica_3): as MESMAS peças com `"classe": 2` na estrutura (Construtor.CLASSES_ESTEIRA) e modelo
    `<peça>_rapida` (reta, curvas, início, fim, junção lateral, rampa ↑/↓, passagem entrada/saída): geometria da esteira
    do jogo com o acabamento do nível 2 de estudo_esteiras_niveis.py (faixa e peças amarelas → vermelho gasto, lascado
    até o aço); lona P_EsteiraRapida rola no dobro (Materiais.ROLAGEM). 3,75 m/s, passagem até 6 tiles livres (só
    liga entrada e saída da mesma classe). Classe diferente na mesma linha = dois caminhos ligados pela ponta; traçar
    uma classe por cima da outra troca a peça (devolve a velha, cobra a nova; desfazer volta).
  - Braço com filtro: estudo_bracos_novos.py (scanner, painel de 5 luzes, giroflex, pistão de elevação como o longo),
    pivôs do braço rápido. Escolhe até 5 itens no painel (`filtro_max`); os outros braços ficam no Auto (o botão de
    escolher itens saiu deles; filtro de salvo antigo continua valendo e o Auto o limpa).
  - Divisor com filtro: estudo_esteiras_niveis.py cena 'filtro' (leitor, câmera, mostrador, seletor de prioridade);
    painel escolhe o item, a saída do filtro e a prioridade do resto (Frente/Direita/Esquerda; sem = rodízio).
  - Silo de granel 3×3: estudo_silo.py; 20.000 de um tipo só (o primeiro que entra; vazio aceita outro), braços por
    qualquer lado; canecas/rosca/comporta animam 2 s quando o conteúdo muda.
  - Cano subterrâneo: estudo_cano_subterraneo.py (as duas caixas, giradas para entrar pelo sul e sair pelo norte);
    a entrada liga na 1ª saída alinhada à frente, mesma rotação, até 9 tiles livres — uma rede de fluido só.
  - Fora do escopo, mas corrigido: no Godot 4.7.2 a cena do jogo não abria (tela_pesquisa.gd e fantasma.gd com
    variável repetida/sem tipo; os testes não carregam essas cenas). Agora os 104 scripts compilam e a demo roda sem
    erro (verificado sem janela).
  - Pendências: (1) nada visto em imagem (sem fotos): conferir na rodada de fotos o vermelho da esteira rápida, a pose
    de repouso e o pistão do braço com filtro (3.652 triângulos, acima do rápido, 3.110), o mecanismo do divisor com
    filtro no quadro 1, o silo (4,17 m de altura, 6.678 triângulos) e a tampa do cano subterrâneo (o vidro da janela
    sai no conversor; vê-se o chão por ela); (2) divisor e junção de 3 vias rápidos não foram feitos: não limitam a
    vazão (servem às duas classes); o motor maior com ventoinha e as placas de nervura dupla da rápida do estudo não
    entraram (só cor/acabamento); (3) feixe de leitura, giroflex e luzes do painel do braço/divisor ficam parados (não
    reagem ao item); a amostra do mostrador do divisor é sempre minério; (4) o item filtrado espera no divisor se a
    saída do filtro entupir (segura o que vem atrás, como no estudo); (5) silo: moega oeste e caçamba sul são só
    visuais (braço põe e tira por qualquer lado, como os baús); (6) cano subterrâneo: o que fica abaixo do chão é
    cortado em −0,03 m (terreno cobre) e o trecho enterrado não soma volume na rede; (7) ícones das 14 peças novas
    com o render Workbench do icones.py (só esses); (8) os diagramas por era do ARVORE_TECNOLOGIA_FLUXO.md seguem com a
    lista antiga de "existente" (já estava assim antes; só a legenda foi atualizada).
- [x] 2.3 água e químico (arte/estudos/conv_agua.py; testes test_bomba_agua.gd, test_refrigeradas.gd,
      test_coletor_condensador.gd, test_filtro_agua_limpa.gd, test_supressor_fogo.gd, test_quimica.gd; roteiro sem janela
      `-- roteiro agua`). Pesquisas jogáveis novas (7): bomba_agua, filtro_agua_limpa, coletor_chuva, condensador_neblina,
      supressor_fogo, quimica, bioquimica — custos e pré-requisitos da árvore. Itens novos: resina, pacote químico e
      pacote ecológico (modelo e ícone derivados com outro matiz). Fluidos em `dados/fluidos.json` (água, água limpa,
      seiva; a limpa serve onde se pede água).
  - Bomba d'água 2×2 (estudo_bomba_agua.py, 8.981 triângulos): 40 de água/s, 60 kW. Regra de lugar `tomada_agua`: os
    tiles logo além do lado SUL do modelo (gira com a peça; é onde ficam o cais e a grade) têm de ser água — rio, lago,
    mar raso ou canal escavado cheio; senão "tomada_seca". Água suja na tomada rende até 60% menos (AmbienteVivo).
  - Refrigeradas (decisão A): fundir aço e lapidar seguem sem água na fornalha e na montadora; bomba_agua libera
    `aco_refrigerado` (10 placas + 60 água → 3 barras, 32 s) e `lapidar_refrigerado` (4 brutos + 30 água → 3, 4 s), +50%,
    no REFINADOR: a fornalha e a montadora não têm boca de cano (sondado no Blender: a montadora não tem lugar livre na
    borda; a fornalha só teria no caminho da caçamba).
  - Coletor de chuva 2×2 (5.738 triângulos, sem energia): 25/s × chuva do clima, tanque de 2.000; o recalque do
    estudo (0,56 m) desce num pescoço de ganso até 0,35 m antes da flange. Condensador de neblina 2×2 (9.553
    triângulos, 80 kW): 12/s × neblina (o inverno tem mais neblina pelos pesos do clima). Sem chuva/neblina: estado
    "esperando o tempo mudar" (Maquina.Estado.ESPERANDO_CLIMA), sem ícone de alerta.
  - Filtro que devolve água: o filtro foi reconvertido com um ramal novo (tê no coletor de cima → borda norte,
    FLUIDO_SAI_N1, 0,35 m) e, com a pesquisa, solta 15 de água limpa/s; sem cano a sobra volta ao rio e ele continua
    limpando (`transborda`).
  - Supressor de incêndio 1×1 (6.412 triângulos, 15 kW): o fogo do jogo é o de vegetação (AmbienteVivo.fogo). Com
    energia e água no reservatório (200) vigia 8 m: havendo fogo gasta 10/s e apaga os focos do raio em 1–2 s; com
    água, a vegetação do raio não pega fogo (molhada). Estado "de prontidão" quando vigia. Jato: partículas
    (Efeitos) em arco do topo do modelo até o foco mais perto. A entrada do estudo vinha pelo oeste, 0,30 m fora do
    eixo e a 0,24 m; entrou um ramal novo pelo LESTE no eixo do tile a 0,35 m (FLUIDO_ENT_L0).
  - Química: resina (30 seiva + 10 água) e pacote químico (1 resina + 1 bateria + 20 água → 2) no refinador; a resina
    bebe seiva por uma boca e água pela outra (saída de fluido de receita que não solta fluido vira 2ª entrada).
    Com o pacote químico existindo, mineração 2 e velocidade de pesquisa 2 ficam pesquisáveis. Bioquímica: pacote
    ecológico (5 biomassa + 1 vidro + 30 água LIMPA → 1).
  - Verificação: os 110 scripts compilam (carregados sem janela), a demo e `-- roteiro agua` rodam sem erro.
  - Pendências: (1) nada visto em imagem (sem fotos): conferir a bomba d'água (cais e grade avançam 0,45 m sobre a
    água; em terra o chão do jogo cobre o poço aberto da laje — o redemoinho e a espuma do poço saíram), o pescoço
    de ganso do coletor, o ramal leste do supressor e o ramal norte do filtro (as peças novas foram conferidas sem
    imagem, por BVH no Blender, sem tocar em nada além do encaixe); (2) coletor fica sempre com as pétalas abertas
    (o estudo fecha no seco) e os 24 anéis de campo que descem pelos fios saíram (peso); (3) a saída do condensador
    está a 0,28 m (canos a 0,35): ajustar no estudo; (4) a torre e o canhão do supressor não miram o foco (a animação
    do estudo varre em laço); sem vapor no fogo; a boca oeste original ficou fechada (flange cega pelo recorte);
    (5) se Sapyst quiser as refrigeradas na fornalha/montadora, os modelos precisam de boca de cano (estudo); (6) o
    uso de água não devolve água suja (despejo) e o "resfriamento contínuo" do refinador do PLANO_CLIMA não entrou
    (quebraria bateria/núcleo/módulo de quem já joga); (7) escavar_canal e turbina_rio seguem "em breve" (fora da
    lista); (8) a água no cano não tem cor própria (o painel mostra o nome); (9) ícones das 4 peças novas e do filtro
    pelo render Workbench do icones.py (só esses); ícones dos 3 itens derivados (derivar_icone.gd); (10) nada pede
    ainda o pacote ecológico (as pesquisas dele seguem "em breve"); (11) a Maquina joga fora a sobra do ciclo (já era
    assim): em passos de 1 s o rendimento do clima cai um pouco, no jogo (1/30 s) menos de 3%.
- [ ] 2.4 combate do meio: lança-foguetes, mina, muros de liga/campo, escudo, artilharia, pacote militar
- [ ] 2.5 clima: para-raios, captador, pacote tempestade, semeador de nuvens, defletor, cúpula, regulador
- [ ] 2.6 drones (estação, reparo, combate, logísticos), limpeza nova, energia/produção que tiverem estudo
