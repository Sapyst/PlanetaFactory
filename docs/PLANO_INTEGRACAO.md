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

## Fase 2 — estruturas novas que já têm estudo: modelo + sistema + pesquisa jogável (1 por vez) — ENCERRADA (2.7)
Ordem pela árvore (pré-requisitos primeiro). Cada uma: converter, regra em estruturas.json, receita/itens se
preciso, sistema em jogo/simulacao (ou onde couber), pesquisa em progressao.json (tirar o "em breve"), testes.
Base: pacote de automação (destrava metade da árvore) e água como insumo (bomba d'água → refrigeradas +50%).
Lista: ver docs/ARVORE_TECNOLOGIA.md (Estruturas: temos × precisamos) e arte/estudos/.

## Fase 3 — artes que faltam (lotes 16, 17, 13, 10, 14, 11), 1 por vez, mais enxutas no processo
## Fase 4 — inserir essas no jogo, 1 por vez, como na fase 2
- [x] **Lote 16 (trilhos, drones e lógica)** — ver "Progresso das fases 3+4" abaixo.
- [x] Lote 17 (proliferação): sensor de varredura, farol de cristal, posto avançado, lançador de sementes, receptor de
  cápsulas (+ colônias), transportador quântico e silo de lançamento (estudos do Antigravity) — ver "Progresso das
  fases 3+4". Tudo depois do posto avançado segue em desenvolvimento até a **Transmissão longa** (poste alto, lote 13).
- [x] Lote 13 (energia I): poste alto, turbina de correnteza, gerador a fluido, painel solar 2, acumulador 2 (ver
  "Progresso das fases 3+4").
- [x] Lote 10 (produção I): montadora 2, refinador 2, fornalha de aço, fornalha elétrica, broca grande, laboratório 2.
- [x] Lote 14 (energia II): turbina alta, acumulador de cristal, reator de cristal, reator de fusão, núcleo de
  singularidade.
- [x] Lote 11 (produção II): forja quântica, fundição de cristal, montadora 3, montadora quântica, extrator ressonante, broca de
  núcleo, laboratório quântico, irradiador + módulos, pacote quântico, foguete, combate e infinitas. **A árvore fechou.**

## Fase 5 — só no fim de TUDO (a árvore inteira funcional): fotos no jogo + baterias de testes
Sapyst: "vai terminar literalmente toda a tech-tree e tudo mais. Faltando só as fotos com testes mesmo."
Entrega: TODAS as estruturas num ÚNICO painel (uma imagem/página com todas as fotos juntas, ex.: mosaico ou página
com a grade inteira + resultado dos testes), para ela não precisar abrir uma por uma.
- [x] **Feita em 2026-10-30.** Painel: arte/estudos/fotos/painel_final.png (3984×8053; painel_final.jpg, 2600 px; fora do git).
  141 fotos: as 131 peças do menu + 10 de conferência. Roteiro `-- modo demo roteiro fotos_finais [so <peça>]`
  (jogo/interface/roteiro_fotos.gd) + arte/estudos/painel_final.py. Fotos e dados por modelo em arte/estudos/fotos/final/.
  Mesma luz e elevação de câmera (50°), distância ajustada ao tamanho da peça, animações ligadas. Variantes de esteira têm foto
  própria. Máquina solta, sem energia nem insumo (`animar_tudo`). Sem janela visível: Xwayland privado sem gerenciador de janelas,
  `--gpu-index 1 --audio-driver Dummy`, user:// isolado por XDG_DATA_HOME.
  - **Testes**: 73.254 verificações, 0 falhas; 187 scripts compilam; demo e os roteiros combate, clima, drones, limpeza2, chegada,
    lote10/11/13/14/16/17, agua e trem rodam sem erro de script (só o aviso de recursos na saída, que já existia). 166 pesquisas.
  - **Desempenho** (`-- modo demo roteiro carga mostruario|patio`; Radeon 890M, 1280×720, tudo animando, sem vsync; celular NÃO
    medido): mostruário, 467 estruturas, 655 mil tris somados: zoom 44 m 33 fps (30,6 ms; p95 57,9; GPU 15,2; 5,9 mi tris desenhados
    com sombras; 3.670 chamadas), zoom 25 m 51 fps, zoom 90 m 43 fps. Pátio, 1.175 estruturas (350 máquinas, 4 de cada), 2,6 mi tris
    somados: zoom 44 m 17 fps (59,4 ms; p95 79,1; GPU 20,8; 6,5 mi tris; 5.369 chamadas), 25 m 24 fps, 90 m 22 fps; quadro dominado
    pela CPU. O chão soma 2,2 mi tris, mais que qualquer grupo de peças. Mais pesadas: núcleo 13.721, núcleo de singularidade
    12.620, semeador de bioma 11.852, laboratório 11.756, refinador 2 11.577, regulador climático 11.446, estação de tratamento
    11.393, viveiro 2 11.375, biodigestor 11.194, terraplenagem 11.165 (fora da conta: cápsula da abertura, 17.426).
  - **Problemas objetivos**: ver seção seguinte (os 4 bugs medidos corrigidos em 2026-10-30; a conferência visual segue aberta).

### Problemas encontrados na fase 5
Bugs medidos (corrigidos em 2026-10-30; teste: jogo/testes/test_malha_no_lugar.gd):
- [x] **cano_reto, cano_curva, cano_t, cano_cruz, cano_subterraneo_entrada/saida**: `Materiais.malha_de` ignorava a translação do nó `_corpo`
  do .glb (reto +19,84 m, curva 3 m, T 2 m; os outros ~0,36 m baixos e fora do eixo). Agora assa o transform do nó nos vértices quando não é
  identidade (só esses 6; regera LOD). Bocas conferidas nas portas a 0,35 m (até 1,5 cm de folga). Os outros 140 modelos de uma malha têm nó na
  origem, exceto muro_lado, que não passa por malha_de.
- [x] **Fábrica grande, "Too many instances using shader instance variables"**: cada objeto cujo shader tem `instance uniform` reserva 16 vec4 do
  buffer global (65.536 vec4 = ~4.090 objetos), mesmo sem usar. O `trabalho` foi para a variante material_pf_cristal.gdshader (só P_Cristal; corpo
  comum em material_pf.gdshaderinc, inclusive o encardido) e o buffer subiu para 262.144 vec4 (4 MB; ~16.380 objetos), porque o extrator de cristal
  tem 29 objetos de cristal. Pátio: 3.693 avisos → 0. **Fps não mudou**: A/B antigo×novo intercalado, 2 rodadas, com a máquina carregada (outro
  jogo aberto, carga ~13): pátio 44 m 14–15 × 14–25 fps (o 25 foi uma rodada só e não repetiu), 25 m 19–23 × 19–21, 90 m 15–17 × 15–16;
  mostruário 44 m 30–31 × 28–29, 25 m 49–50 × 47–55, 90 m 42–45 × 39–42. O gargalo do pátio continua sendo a CPU.
- [x] **rampa_desce (todas as classes)**: o modelo não tinha culpa. `DesenhoChunk.atualizar` sem `crescer_de` durante o crescimento do piso (1,6 s, disparado
  pelo pilar do trecho alto) era sobrescrita pela mistura com a imagem final antiga; e o que ficava além do raio de 7 m nunca chegava à final.
  Afetava qualquer peça posta logo depois de outra construção no chunk. Também: a margem de chunks tocados era 1 tile, com piso espalhando 2.
Conferência visual, por peça (lista original; o que foi feito está em "Correção da conferência", logo abaixo):
- **painel_solar**: só a estrutura; não se vê placa (buraco de vidro). painel_solar_2 está bom.
- **estacao_drones**: laje com manchas pretas irregulares. **estacao** (telhado) e **acumulador** (topo dos tanques): pintas pretas
  (reconversão pendente da fase 1).
- **purificador_ar_2**: 7 m em 3×3, três tubos pretos no topo e miolo emaranhado. **coletor_chuva**, **viveiro**: escuros e
  emaranhados, silhueta não se lê.
- **silo_granel**: peça amarela solta, flutuando atrás do topo. **coletor_chuva**: ponto lilás solto acima. **mina_pulso**: placa em
  triângulo e caco solto fora do anel. **braco**: bola laranja sem textura no chão, fora da base; base cinza lisa, destoa dos outros braços.
- **extrator_cristal, extrator_ressonante**: mancha preta opaca no alto (provável fumaça; origem não confirmada).
- **cano_subterraneo_entrada/saida, braco_quantico**: pequenos e confusos.
- **Caixa além da área** (m × área; pode ser cabo ou peça móvel): terraplenagem 6,2×6,1 em 3×3, nucleo 5,7×5,7 em 3×3, viveiro 4,2×3,9 em 2×2,
  coletor_lixo 3,7×3,0 em 2×2, coletor_lixo_2 3,2×2,1 em 2×2, artilharia 3,7 em 3, estacao 3,05 em 2×3.
- **nucleo**: corpo central pequeno para o papel e para os 3×3 (só o exterior das raízes chega à borda); foto sem piso, fora do menu.
- **Antigos, sem textura** (resolvido: ver "Pedido 2"): plataforma_agua (284 tris), ponte_agua (150), ninho_aranha (264), aranha (632), poca de seiva amarela chapada
  sob a **bomba**, nucleo_queda (cone laranja chapado).
- **Classes de esteira**: rápida, expressa e quântica só diferem na faixa fina; no painel quase não se distinguem.
- Sem achado: textura preta (0 superfícies abaixo de 3% de luminância na varredura), escala absurda, modelo que falta no menu.
- Não conferido nesta rodada: efeitos em ação (raio, bolha, holograma, tiro, voo do foguete), pois as fotos são de peça solta.

Correção da conferência (2026-10-31; ajustes por peça em arte/estudos/ajustes_fase5.py, código em para_jogo.py):
- **Causa da maioria (não era vidro)**: a redução usava uma taxa só no corpo inteiro. Chapa, placa e coluna de 12 faces viravam lascas em triângulo
  e cascas sem o lado de fora, e o jogo não desenha o verso. Foi isso que "sumiu" com as placas do painel solar e a torre do elevador do silo
  (a peça amarela solta era a cabeça dela), soltou o ponto lilás do coletor de chuva e fez a placa em triângulo da mina. Conferido em Blender com
  corte de verso ligado. Novo `por_peca` em para_jogo.py (`reduzir_por_peca`): cada malha tem cota própria, a leve fica inteira, só a pesada desce.
  Opções novas: `cotas`, `intactos`, `vidro_opaco`, `cortar_fixos`, `trocas`, `PF_ASSAR_CPU=1` (com o jogo dela na NVIDIA, o assado na GPU falha; rodar
  também com `CUDA_VISIBLE_DEVICES=` vazio). Sem `por_peca`, a conversão segue como antes.
- **Peças reconvertidas** (tris antes → depois): painel_solar 5.004 → 8.348; estacao_drones 8.112 → 9.423; estacao 9.136 → 10.717; acumulador 6.066 →
  10.372; silo_granel 6.678 → 11.474; coletor_chuva 5.738 → 10.756; mina_pulso 1.648 → 4.011; braco 1.962 → 2.002; terraplenagem 11.165 → 11.034;
  viveiro 7.561 → 10.674; coletor_lixo 7.757 → 8.028; nucleo 13.721 → 14.004; purificador_ar_2 8.446 → 16.130 (a mais pesada de todas);
  cano_subterraneo_entrada 1.087 → 2.876; _saida 1.103 → 2.855; braco_quantico 7.860 → 8.159; acumulador_cristal 5.846 → 7.238; bau_grande 6.781 → 6.780.
  Soma das 18: 115.671 → 154.881 (+34%). **Fps não medido de novo; celular não medido.** Os limites de triângulos de 5 testes subiram por causa disso
  (test_mina_pulso, test_cano_subterraneo, test_limpeza_nova, test_coletor_condensador, test_acumulador_cristal).
- **As outras peças (fora dessa lista) seguem na redução antiga** e podem ter o mesmo defeito em grau menor; não foram varridas.
- **Manchas pretas**: estacao_drones e acumulador eram decalques opacos do estudo (`conves_fuligem`, `maq_fuligem`, `chamusco`), retirados; estacao eram os
  furos de ferrugem da telha, que agora saem fechados (`trocas`). **extrator_cristal/ressonante**: não era malha: era a fumaça do jogo (`render/efeitos.gd`),
  que nasce no topo da caixa do modelo; extrator e broca não têm chaminé, entraram em `SEM_CHAMINE` (as brocas fariam o mesmo trabalhando).
- **braco**: a bola laranja era o terminal de energia no canto do tile, sem base embaixo: ganhou chapa de chão e conduíte. Tintas sujas no lugar da cor lisa da lib_pf.
- **purificador_ar_2**: os três "tubos pretos" eram o tremor de calor do estudo (material só de refração, assado preto), novo filtro `so_efeito`: altura 7,03 → 5,77 m.
  Fuligem do estudo a 40% e casca interna em chapa, via `PURIFICADOR_CLARO` em conv_limpeza.py.
- **Vidro**: acumulador_cristal, bau_grande e cano subterrâneo com vidro opaco escuro. Sem mudança: painel_solar_2, laboratórios e reatores (janelas pequenas, leem bem).
- **Além da área**: terraplenagem 3,06×3,06, nucleo 3,15×3,12 e viveiro 2,06×2,06 (torrões, pedras, cápsulas e árvores saíram; raízes e cabos cortados na borda); coletor_lixo
  2,82×2,01 (poças saíram). **Ficam de propósito**: braços do coletor_lixo (2,82) e coletor_lixo_2 (3,2), que se mexem, mas estão fora do tile já na pose de repouso, não só
  num instante: decisão de Sapyst; cano da artilharia (3,7, alto e gira); balanço do pórtico da estacao (3,04, por cima da linha, é o desenho).
- **nucleo**: só com escala não dá (as pétalas já chegam à borda). Corpo maior = mudar `R_CORPO` (0,62 m) em estudo_nucleo.py, ajustando pétalas e bocas, e estudo_nucleo_queda.py junto. Não feito.
- **Esteiras**: `Materiais.COR_LONA` (vermelho, azul-aço, violeta) e encardido na lona pelo shader, valendo para toda a classe; nenhum modelo reconvertido.
- **Abertos**: braco_quantico ainda confuso (anéis soltos em volta, são o campo do estudo); triângulo vermelho pequeno no chão ao lado da mina na foto, fora da caixa do modelo (±0,5 m), origem não achada;
  mina continua um monte de terra que quase esconde o anel violeta. painel_final.png não foi remontado (fotos novas em fotos/final/ só das peças mudadas).
- Verificação: 73.770 verificações, 0 falhas; 188 scripts compilam; demo sem janela (`--quit-after 400 -- modo demo` e `--quit-after 600 res://cenas/mundo_demo.tscn`) sem erro de script.

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
- [x] 2.4 combate do meio (arte/estudos/conv_combate_meio.py; testes test_ciencia_militar.gd, test_lanca_foguetes.gd,
      test_mina_pulso.gd, test_muros_liga_campo.gd, test_gerador_escudo.gd, test_artilharia.gd; roteiro sem janela
      `-- modo demo roteiro combate`). Pesquisas novas (13), custos e pré-requisitos da árvore: ciencia_militar,
      dano_bala_3, cadencia_bala_2, liga_leve, processador, torre_foguetes, dano_foguete_1, cadencia_foguete_1, mina_pulso,
      muro_liga, escudo_1 jogáveis; muro_escudo e artilharia ligadas mas travadas pela árvore (ver pendências). Itens
      novos: pacote militar, liga leve, processador, foguete, granada (modelo e ícone derivados com outro matiz).
  - Pacote militar (2 munições + 1 aço + 2 tijolos → 2, montadora). Com ele, dano_energia_3 e cadencia_energia_1 (já
    ligadas) ficaram pesquisáveis e foram conferidas (+30% de dano; +20% de tiros e −10% de energia por tiro);
    dano_energia_4 e cadencia_energia_2 seguem travadas (pacote de tempestade, 2.5).
  - Torre de munição genérica pela regra (`municao_item`, `tiros_por_item`): o braço só entrega o item da torre.
    Lança-foguetes 3×3 (8.668 triângulos): foguete = 1 disparo, guarda 18, 1,5/s, 40 de dano em área (raio 2,5 m) a
    30 m; o foguete voa a 24 m/s e explode no ponto mirado. Todo disparo ejeta o selo traseiro (cápsula 2,6× maior,
    "capsula" em modelos.json) com fumaça 3× pela traseira do casulo; o foguete voa com rastro; explosão com
    faíscas, fumaça e clarão. Bônus dano_foguete / cadencia_foguete.
  - Mina de pulso 1×1 (1.648 triângulos, 0,38 m: as aranhas passam por cima): aranha a 1,2 m dispara, atordoa as de
    3 m por 3 s (paradas, sem morder), rearma em 20 s (salvo junto); anel violeta no chão.
  - Muro de liga (pilar 764 + pano 374 triângulos; 1.500 ♥) e muro de campo (pilar 1.147 + pano 92; 800 ♥,
    regenera 5 ♥/s × energia da rede, 10 kW por pilar — `Fabrica.energia(id)`): mesmo sistema do tijolo (arrasta
    em linha, liga em qualquer muro vizinho). No pilar do campo o fio esmaltado das bobinas (24 mil triângulos) virou
    um cilindro por bobina na malha baixa (a cor vem do assado). A parede translúcida do pano é do jogo
    (`render/shaders/campo_parede`, mesma trama do escudo).
  - Gerador de escudo 2×2 (9.721 triângulos, com a animação do estudo — cardã, pistões, ventoinhas — enquanto tem
    carga): bolha de 8 m; mordida em construção dentro dela gasta 0,02 MJ por ponto da carga (8 MJ = 400 de dano)
    em vez de vida; recarrega da rede a 200 kW (mesma carga da torre de energia, `carga_mj`). A bolha é do jogo
    (`render/shaders/campo_escudo`): meia esfera quase invisível, borda e trama hexagonal fraca, some sem carga e
    acende em âmbar onde a mordida bateu. Processador (2 circuitos + 1 resina + 1 lapidado + 5 água) no refinador.
  - Artilharia 3×3 (9.556 triângulos): obus fixo a 55° (pose do quadro 50 do estudo; a 1,5 m do centro o cano já está
    a 3,6 m de altura), giro mira; granada (2 liga leve + 1 foguete + 2 tijolos) = 1 disparo a cada 4 s, guarda 10,
    150 de dano em área (raio 4 m), só ninhos de 16 a 120 m, voo em arco alto; estojo ejetado 3,2× com fumaça 4×.
  - Conferido sem imagem, por BVH no Blender: giro do lança-foguetes e da artilharia girando 360° (de 10 em 10°) sem
    cruzar nada fixo (fora o contato coroa/rolamento, face com face); tudo dentro da área (recorte na borda), menos o
    cano da artilharia.
  - Verificação: os 116 scripts compilam (carregados sem janela), a demo e `-- modo demo roteiro combate` rodam sem
    erro (28 disparos, 28 explosões, 12 aranhas e 4 ninhos mortos, 1 pulso, muro de campo regenerando).
  - Pendências: (1) nada visto em imagem (sem fotos): conferir as silhuetas, a bolha e a parede de campo (shaders),
    o arco da granada, o selo/estojo maiores e se o rastro do foguete fica bom no zoom normal; (2) a artilharia pede
    `cartografia` (que pede o sensor de varredura, sem estudo) e o muro de campo pede `escudo_2` (tempestade): ficam
    travados na pesquisa (no modo demonstração se constroem); dano_foguete_2, cadencia_foguete_2, foguete_enxame,
    dano/alcance_artilharia, artilharia_automatica e escudo_2 não foram ligados (fase 2.5+); munição perfurante e
    posto avançado (também da ciência militar) seguem em breve (fora da lista); (3) saíram os pinhões dos motores de
    giro do lança-foguetes e da artilharia (e o eixo deste: entrava no convés) — no jogo a coroa gira e eles
    ficariam parados cruzando os dentes (no estudo do foguete os dentes já cruzavam a mesa e o motor);
    (4) o casulo do lança-foguetes não eleva e o obus fica a 55° (o Animador só gira o giro); tampas dos tubos
    fechadas, braço carregador e bandeja parados; o foguete mira onde a aranha estava (o raio cobre o passo dela);
    (5) "aranha não escala" do muro de liga não muda nada (no jogo nenhuma aranha escala; vale a vida);
    (6) a parede do muro de campo tem força fixa (não apaga sem energia); (7) a mina fica parada (LED vermelho; o
    disparo do estudo não entrou, só o anel do jogo); o recorte deixou 3 mm além do tile; (8) o escudo só absorve
    mordida de aranha (fogo e tufão passam); (9) as peças móveis do gerador de escudo vêm do estudo sem conferência de
    cruzamento no jogo (pose do laço); (10) ícones das 8 peças novas pelo render Workbench do icones.py (só esses);
    ícones dos 5 itens derivados (derivar_icone.gd: liga leve da placa de cobre, processador do circuito, foguete e
    granada da munição, pacote militar do pacote de pesquisa).
- [x] 2.5 clima (arte/estudos/conv_clima.py; testes test_raios.gd, test_para_raios.gd, test_captador_carga.gd,
      test_ciencia_tempestade.gd, test_maquinas_clima.gd; roteiro sem janela `-- modo demo roteiro clima`). Pesquisas novas
      (15), custos e pré-requisitos da árvore: para_raios, captador_carga, ciencia_tempestade, para_raios_2,
      semeadura_nuvens, cupula_tempestade, escudo_2, dano_bala_4, cadencia_bala_3, dano_foguete_2, cadencia_foguete_2
      jogáveis; controle_vento (pede `turbina_alta`), controle_clima (pede `computacao_quantica`), dano_artilharia_1 e
      alcance_artilharia_1 (pedem a artilharia, travada pela cartografia) ligadas mas travadas pela árvore. Itens novos:
      cristal carregado e pacote de tempestade (modelo e ícone derivados com outro matiz). Aba nova **Clima** na barra.
  - **Raios** (não existiam: só o desenho num ponto qualquer da vista). `ambiente/raios.gd` (Raios, lógica pura): o
    evento "raio" do Clima (`raios_por_s`: tempestade 0,1, tufão 0,15) cai a até 20 m de uma construção sorteada pelo
    peso altura² (o raio procura o ponto alto). Ordem: regulador cancela; cúpula com energia pega; para-raios/captador
    no raio deles pegam (captador antes, `prioridade`); sem proteção, a construção mais alta a até 3 m leva 150 de dano
    (o escudo carregado absorve: 3 MJ) e até 3 tiles de mato em volta podem pegar fogo; no chão, o mato pega fogo (na
    chuva apaga em segundos) ou fica a marca queimada (canal QUEIM do chão, nada de filtro). Contador de descargas
    salvo. O desenho (`DesenhoClima`) bate o raio no lugar: ponta do para-raios, topo da construção; na cúpula, no
    campo + arco do alto dela até o cristal; clarão mais fraco e trovão mais atrasado longe da câmera.
  - Para-raios 1×1 (2.500 triângulos) e de cristal (3.237): coleções 'pr'/'pc' do estudo, efeitos fora, brita e
    Lichtenberg cortados na borda do tile; `ponta_raio` no .json. 14 m / 120 MJ e 22 m / 200 MJ; papel "fonte" na
    Fiacao (o poste liga neles) e a energia vai para os acumuladores da rede (`Fabrica.injetar`, pelo espaço livre de
    cada um, sem limite de potência). Sem rede: só proteção.
  - Captador de carga 2×2 (9.054 triângulos, 16 peças com a animação do estudo — carrossel, eletrodos —, toca 4 s
    depois de cada raio). Pega em 10 m, antes dos para-raios. Cada raio: 1 cristal lapidado + 30 água → 1 cristal
    carregado (`Maquina.ciclo_agora`, receita `carregar_cristal` com `por_raio`); a sobra (60 MJ) vai para a rede.
    Estado "de prontidão" com insumo; portas do estudo (ITEM_ENT_S1, ITEM_SAI_O0, FLUIDO_ENT_N0).
  - Pacote de tempestade (cristal carregado + módulo de controle + liga leve → 2, 15 s) na **montadora** (a montadora 2
    da árvore não existe). Conferido: dano_energia_4 e cadencia_energia_2 ficam pesquisáveis com a ciência de
    tempestade e somam +30% / +20% na torre; **escudo 2** (bônus `escudo_raio` 0,5 → 12 m, `escudo_carga` 1,5 → 20 MJ
    = 1.000 de dano, `escudo_recarga` 1 → 400 kW; a bolha do desenho refaz no raio novo) e com ele o **muro de campo**
    ficam jogáveis.
  - Máquinas de clima (`ambiente/clima_local.gd`, ClimaLocal; regra `clima_local`), só ligadas e com energia:
    **semeador de nuvens** 2×2 (9.272 triângulos, 300 kW): chuva ≥ 75% em 40 m — coletor de chuva rende no lugar
    (`Fabrica.chuva_maq`), o fogo apaga e nada pega fogo; desenho: chuva de verdade só no círculo (partículas em anel a
    22 m, `DesenhoClimaLocal`), some quando o planeta já chove mais. **Defletor de vento** 2×2 (8.138 triângulos, 19
    peças móveis, 250 kW): o vento de 40 m sopra para a frente da peça (gira com R; a cabeça do estudo virou 66° = 22
    dentes, pinhões seguem engrenados), entre 30% e 80% — tufão não machuca, turbinas não entram em proteção (e a
    animação delas vira para lá), o fogo anda para lá e a poluição dos chunks cobertos vaza para lá
    (`Poluicao.vento_chunks`). **Cúpula contra raios** 3×3 (7.087 triângulos, 8,4 m, 400 kW): nenhum raio em 30 m, a
    descarga vai para os acumuladores (120 MJ); desenho: meia esfera de campo (shader campo_escudo, quase invisível)
    que acende ao pegar raio. **Regulador climático** 3×3 (11.446 triângulos, 1,5 MW): no painel, céu firme (sem chuva)
    ou chuva mansa (40%) em 80 m; nos dois, sem raio, sem tufão e vento até 40%.
  - Conferido sem imagem, por BVH no Blender: no defletor nada que gira cruza peça fixa (fora o rolamento, face com
    face) depois de tirar o trecho dos feixes de cabo que atravessava a coroa no estudo; no regulador os pratos das
    antenas cruzavam os braços-garra no estudo — ficaram a 0,72 (sem cruzar nos quadros 1/25/49/73). No captador e no
    semeador só sobram encaixes do próprio desenho (cristais e cestos no banho, eletrodos nas buchas e no tampo,
    culatra e hastes nas luvas/camisas, cabos presos na caixa das bobinas). Cúpula (guarda-chuva apertado acima de 4 m)
    e regulador (escala 0,75) usam transformação contínua: o que não se tocava continua sem se tocar.
  - Verificação: 65.079 verificações, 0 falhas (testar.sh); os 124 scripts compilam (carregados sem janela); a demo e
    `-- modo demo roteiro clima` rodam sem erro (raios no captador, para-raios, de cristal, chão com fogo, cúpula).
  - Pendências: (1) nada visto em imagem (sem fotos): conferir as 7 silhuetas, o recorte na borda (brita e Lichtenberg
    do para-raios, esteiras e mastro queimado do captador), o guarda-chuva da cúpula apertado a 0,64, o regulador a
    0,75 com antenas a 0,72, o raio batendo na ponta/no campo, a cúpula de 30 m e a chuva em anel do semeador;
    (2) **balanço**: o cristal carregado só vem de raio (1 por raio no captador; tempestade/tufão ~10–15% do tempo) —
    a era de tempestade fica lenta; ver com Sapyst (mais raios, mais cristais por raio ou o regulador puxando
    tempestade); (3) pacote de tempestade na montadora comum (montadora 2 sem estudo); (4) defletor e regulador
    travados pela árvore (turbina alta e computação quântica sem estudo; no modo demonstração se constroem);
    (5) o regulador muda só a lógica: a chuva do planeta continua caindo na vista dentro do raio dele, sem furo nas
    nuvens, sem chão seco; o chão molhado/poças do semeador seguem o clima do planeta (shader global); o defletor não
    tem efeito visual (linhas de fluxo, folhas e capim voando do estudo saíram; grama e nuvens seguem o vento do
    planeta); (6) para-raios sem animação (arcos, faíscas, LEDs de carga saíram); o semeador anima só 2 peças
    (carrossel/culatra), sem chama nos queimadores nem estojo ejetado; a ventoinha 1 do defletor fica parada (24 voltas
    no laço = múltiplo exato dos quadros que o para_jogo compara; a 2 gira); o saco da biruta perdeu a ondulação
    (shape key); (7) portas do captador como no estudo: itens a 0,20/0,25 m e água a 0,275 m (canos do jogo a 0,35);
    (8) o raio não machuca aranha nem ninho, não cai em drone (drones_tempestade, fase 2.6) e o para-raios não protege
    do tufão; munição carregada, módulos 2 e reator de cristal (que usam o cristal carregado) seguem em breve;
    (9) ícones das 7 peças pelo render Workbench do icones.py (só esses); ícones do cristal carregado e do pacote de
    tempestade derivados (derivar_icone.gd); (10) diagramas por era do ARVORE_TECNOLOGIA_FLUXO.md seguem com a lista
    antiga (só a legenda foi atualizada, como nas fases anteriores).
- [x] 2.6 drones, limpeza nova, chegada do núcleo (arte/estudos/conv_drones.py, conv_limpeza.py, conv_nucleo.py; testes
      test_drones.gd, test_limpeza_nova.gd, test_nucleo_queda.gd; roteiros sem janela `-- modo demo roteiro drones`,
      `-- modo demo roteiro limpeza2` e `--fixed-fps 30 -- novo roteiro chegada abertura`). Pesquisas novas (19), custos e
      pré-requisitos da árvore: drones, drones_bateria_1/2, drones_frota_1/2, drones_velocidade_1/2, drones_logisticos(_2),
      drones_tempestade, drones_defesa, coletor_lixo_2, purificador_ar, viveiro_2, biodigestor, recuperar_solo,
      purificador_ar_2, restauracao_bioma jogáveis; estacao_tratamento ligada mas travada (`refinador_2` sem estudo).
      O **pacote ecológico** (2.3) passou a ser pedido (coletor 2, purificadores, viveiro 2, biodigestor, recuperação de
      solo, tratamento, semeador). Itens novos: drone (sai da estação e vai para a frota) e resíduo. Aba nova **Drones**.
  - **Estação de drones** 2×2 (estudo_drones.py, só a coleção da estação; 8.112 triângulos): máquina (150 kW) com a
    receita do drone da árvore (4 placas + 1 motor + 2 circuitos + 50 de água, 12 s); água por um ramal novo pela borda
    sul, tile leste, 0,35 m (FLUIDO_ENT_S1), que desce entre as cintas e entra no costado do tanque (conferido por BVH:
    só toca o tanque). A animação "trabalho" é o bloco POUSO/RECARGA do estudo (quadros 385–480: garras, plugue, braço
    abastecedor) e toca quando um drone nasce, pousa ou decola. Frota 8 (+4/+8 com as melhorias), alcance 45 m.
  - **Drones** (`drones/drones.gd`, lógica; `drones/desenho_drones.gd`, desenho): os três modelos de
    estudo_drones_modelo.py montados sozinhos (2.780–3.038 triângulos; rotores, braço de solda, torre/canhão, pêndulo
    como partes), 1,5× no jogo. Tipo escolhido no painel da estação: **reparo** (escaneia e solda o que foi danificado
    no alcance a 25 ♥/s, 1 placa de ferro do núcleo a cada 25 ♥, como o Reparar), **combate** (orbita e atira nas aranhas:
    4 de dano, 2,5 tiros/s, 8 m; aranha a 2,2 m do drone baixo morde; vida 0 = cai e vira sucata) e **logístico**
    (pesquisa drones_logisticos: provedor → requisitante, 1 item por viagem; 4 e 2× alcance com logísticos 2). Bateria
    120 s (volta com folga), recarga no hangar com a energia da estação; com raios caindo ficam no hangar até
    drones_tempestade. Os desejos da Sapyst: nascem em **holograma vermelho** na fabricadora (shader `holograma`, leques
    dos 3 projetores, monta de baixo para cima, vira matéria com a borda acesa e desce para dentro), hélices girando em
    sentidos alternados com **atitude por mola-amortecedor** (inclina para onde acelera, passa do ponto, balança ao
    pairar, guinada com tranco), **scan vermelho** sobre a estrutura enquanto conserta (sobreposição `scan_reparo` na
    estrutura + folha de laser e leque do olho) com o braço de solda, faíscas e o clarão do arco, **tiro** com traçante,
    clarão de boca, recuo e **cápsula com fumacinha** pela janela de ejeção (`DesenhoColonia.ejetar_capsula`), pêndulo
    da carga com o item de verdade, derrubado girando com fumaça até virar sucata fumegando.
  - **Limpeza nova** (`AmbienteVivo._limpeza`), cada uma com efeito nos sistemas que já existiam: **coletor de lixo 2**
    2×2 (9.410 triângulos; raio 10, sujeira, óleo e a **cinza** do chão queimado; o que recolhe vira **resíduo**, 1 a
    cada 1,0 somado nos tiles, até 10 na saída), **purificador de ar** 2×2 (8.729; 6 de poluição/min do chunk),
    **purificador atmosférico** 3×3 (8.446; 40/min e 1 resíduo a cada 20 de poluição), **viveiro 2** 2×2 (11.375; raio
    12, planta no dobro do ritmo, mudas da árvore do bioma — `especie_do_bioma`, desenhadas com os modelos da espécie —
    que crescem 2× mais rápido), **biodigestor** 3×3 (11.194; 4 resíduos + 40 de água → 2 biomassas + 30 de seiva),
    **semeador de bioma** 3×3 (11.852; com seiva tira o queimado do chão em 14 m, devolve as árvores carbonizadas/caídas
    e planta mudas do bioma), **estação de tratamento** 3×3 (11.393; tomada ao sul como a bomba d'água, limpa a água suja
    em 16 m e solta 60 de água limpa/s; sem cano, a sobra volta ao rio) e a **recuperação de solo** (sem estrutura: o
    tile aplainado sai limpo).
  - **Chegada do núcleo** (estudo_nucleo_queda.py → `nucleo_queda`, animação "chegada" de 240 quadros; o para_jogo
    ganhou `quadros` e `animacao`): na abertura do jogo novo a cápsula fechada (pétalas em saia, ogiva) fica presa sob
    a nave, despenca abaixo das nuvens, bate e a animação do estudo toca do impacto em diante (ogiva ejetada, pétalas
    cravando, cabos-raiz, esteiras, monólito); no fim (pose do laço) dá lugar ao núcleo do jogo. A abertura passou de
    ~14 s para ~16 s (um toque pula, já com o núcleo pronto).
  - Energia/produção com estudo e fora do jogo: **nenhuma**. estudo_montadora_v1.py, estudo_terraplenagem_v1.py e
    estudo_esteira_v1.py são as versões antigas das peças que já estão no jogo (convertidas das versões novas). Fora de
    energia/produção, com estudo e ainda fora: esteira **expressa** e **quântica** (níveis 3 e 4 de
    estudo_esteiras_niveis.py; logistica_4/5) e o **vagão-tanque** (modelo do estudo_trem já existe; falta o sistema e
    a bomba de estação).
  - Fora do escopo, mas corrigido: `Fabrica.um_tipo` quebrava com um baú que as aranhas tinham acabado de derrubar
    (o desenho perguntava antes da fábrica remontar).
  - Verificação: 65.577 verificações, 0 falhas (testar.sh); os 130 scripts compilam (carregados sem janela); a
    demo, `-- modo demo roteiro drones` (reparos, 3 aranhas mortas, cápsulas, 4 engrenagens entregues), `-- modo demo
    roteiro limpeza2` e a abertura (`--fixed-fps 30 -- novo roteiro chegada abertura`: impacto, chegada e troca pelo
    núcleo em 15,7 s) rodam sem erro.
  - Pendências: (1) nada visto em imagem (sem fotos): conferir o holograma, a atitude e o balanço, o scan e o braço de
    solda, o tiro com a cápsula, o pêndulo, a sucata, a escala dos drones (0,6 m no estudo, 0,9 m no jogo) e as 9
    silhuetas novas; (2) porto logístico e baús logísticos sem modelo próprio (a estação faz de porto; provedor e
    requisitante são papéis do baú comum); o **baú de estoque** não foi feito; o que sobra na garra volta ao núcleo;
    (3) drones no hangar somem com a estação desmontada (não devolvem itens) e a sucata não devolve nada; os pousados
    entram no hangar (só 2 berços no modelo); (4) combate só caça aranhas (ninho não); a mordida é simplificada (aranha
    a 2,2 m do drone abaixo de 3 m); o raio não cai em drone (eles só ficam no hangar); (5) saíram do modelo: borrão
    das hélices, arco de solda, clarão de boca (efeitos do jogo) e os pistõezinhos do braço de solda (parados entrariam
    no corpo); a garra larga do logístico passa rente aos patins (balanço até 0,3 rad; recolhe 0,10 m no pouso);
    (6) o item drone na esteira usa o modelo do motor; drones_infinito segue em breve (colônias); (7) braços de sucção
    do coletor 2 passam da laje na animação (3,2 m, como o coletor 1); o drone-varredor do estudo saiu (fora do tile);
    viveiro 2 tem 84 nós e o semeador 81 (o viveiro 1 tem 93); (8) **água suja** não é fluido: o biodigestor bebe a
    água do cano (a 0,30 m, canos do jogo a 0,35) e a água limpa da estação de tratamento sai pela flange do estudo
    (y −0,87, z 0,26: fora do eixo do tile L0) — ver com Sapyst se a bomba numa tomada suja deveria mandar "água suja";
    (9) **balanço**: a árvore diz "1 resíduo a cada 20 de sujeira" sem unidade — ficou 1 a cada 1,0 de sujeira somada
    nos tiles (um tile imundo = 1); (10) o semeador devolve árvores e chão queimado, mas não a vegetação rasteira que o
    fogo apagou nem o bioma natural cinzal; a boca dele foi para o eixo (y 0, z 0,35) e o cano contorna o injetor oeste
    (no estudo atravessava o pórtico; conferido por BVH); o gasômetro do biodigestor não infla (shape key);
    (11) recuperação de solo sem ferramenta própria (vale ao Aplainar); estação de tratamento travada pelo refinador 2;
    harmonia_ninhos, simbiose e purificacao_infinita seguem em breve; (12) chegada do núcleo: a brasa da reentrada
    (emissão animada no material) não passa para o glTF; 17.426 triângulos (só na abertura); a pose final da cápsula e
    o núcleo do jogo saem de conversões diferentes — conferir se a troca não "pula"; (13) **melhoria do núcleo**: a árvore
    não tem melhoria de núcleo e não há modelo de núcleo mais robusto — nada ligado; (14) ícones das 9 peças novas e do
    item drone pelo render Workbench do icones.py (só esses); ícone do resíduo derivado do tijolo (derivar_icone.gd).
- [x] 2.7 fechamento da fase 2 (testes test_esteira_niveis.gd, test_vagao_tanque.gd, test_braco_empilhador.gd).
      Pesquisas logistica_4, vagao_tanque e braco_empilhador entram em progressao.json; logistica_5 também, mas
      travada pela árvore. **Fase 2 encerrada**: não sobra estudo de estrutura sem uso no jogo, a não ser o braço
      quântico e o divisor/junção por nível (ver pendências).
  - **Esteira expressa** (logistica_4, jogável: liga leve + pacote químico já existem) e **quântica** (logistica_5):
    mesmo método da rápida (arte/estudos/conv_esteiras_niveis.py): as MESMAS 9 peças com `"classe": 3` / `4`
    (Construtor.CLASSES_ESTEIRA), acabamento dos níveis 3 e 4 de estudo_esteiras_niveis.py — expressa: faixa
    azul-aço gasta 0,25 e as peças amarelas no Azul-aço do estudo; quântica: faixa violeta gasta 0,3 e as peças
    amarelas no ferro fundido enferrujado da estrutura rústica do estudo. Lonas P_EsteiraExpressa / P_EsteiraQuantica
    rolam a 3× e 4× (Materiais.ROLAGEM). 5,625 e 7,5 m/s, passagem até 8 e 10 tiles livres, troca ao arrastar por cima
    (devolve a velha, cobra a nova; desfazer volta). Custos: expressa 1 liga leve + 2 engrenagens (rampa 2+4, passagem
    6+10); quântica 2 ligas + 1 cristal carregado (rampa 3+2, passagem 10 + 6 + 2 processadores). A **quântica fica
    travada**: pede `computacao_quantica` (sem estudo) e o pacote quântico (forja quântica, sem estudo) — fase futura.
    No modo demonstração se constrói. Mesmas portas, áreas e triângulos da rápida (526 a 1.674).
  - Fora do escopo, mas necessário: `EsteiraCaminho` perdia a sobra do tick — a 30 quadros/s a expressa (0,1875 m por
    tick, item a cada 0,25 m) só aceitava/entregava 1 item a cada 2 ticks (2× em vez de 3×). Agora o item entra colado
    no anterior quando a fila é contínua e, com a fila toda encostada, o próximo sai no mesmo tick. Básica e rápida
    não mudam (múltiplos exatos); a quântica bate 30 itens/s = 1 por tick a 30 quadros/s.
  - **Vagão-tanque** (vagao_tanque): peça de menu **trem-tanque** (`Trem.COMPOSICOES`: locomotiva + 2 vagões-tanque +
    locomotiva; modelo vagao_tanque do estudo_trem que já estava no jogo), 25.000 de fluido por vagão. Como o vagão de
    carga com itens: a **estação** ganha um tanque (25.000) e o **cano com a boca virada para a estação** liga esse
    tanque à rede (a bomba de estação da árvore não tem estudo: o cano faz o papel dela, 1.000/s). Painel da estação:
    **Cano desligado** (padrão: não rouba fluido de rede nenhuma), **Cano → trem** (carregar: rede → tanque da estação
    → trem ao parar) e **Trem → cano** (descarregar: o fluido que o trem trouxe de OUTRA estação → tanque → rede). Um
    fluido só de cada lado (seiva não entra em rede de água). Salvo antigo sem tanque carrega normal.
    Travado pela árvore: `vagao_tanque` pede `trem_automatico` (rotas com condição + sinal em cadeia, sem estudo); no
    modo demonstração se constrói.
  - **Braço empilhador** (braco_empilhador, jogável: braço com filtro + processador; pacotes básico/automação/químico):
    estudo_bracos_novos.py via arte/estudos/conv_bracos_novos.py (como o braço com filtro: repouso, pinças fechadas,
    prensa em cima, contador apagado; partes giro/braco1/braco2/garra + camisa/haste do pistão da frente; 4.076
    triângulos). `Braco.pilha_max` = 4: na origem pega de uma vez os itens IGUAIS que já estão lá (que o destino
    aceita) e solta um por vez; `qtd` vai no salvo. Custa 4 barras de aço + 6 engrenagens + 1 processador.
  - Estudos de arte/estudos/ sem uso no jogo depois desta: estudo_esteira_v1.py, estudo_montadora_v1.py e
    estudo_terraplenagem_v1.py (versões antigas de peças que já estão no jogo), o **braço quântico** e o **divisor/junção
    de cada nível** (cena 'acessorios' de estudo_esteiras_niveis.py). Nada mais.
  - Verificação: 66.258 verificações, 0 falhas (testar.sh); os 132 scripts compilam (carregados sem janela); a demo
    (`--quit-after 400`) e `-- modo demo roteiro trem` rodam sem erro.
  - Pendências: (1) nada visto em imagem (sem fotos): conferir o azul-aço e o violeta das faixas no zoom normal (os
    ícones das 18 peças e do empilhador saíram pelo render Workbench do icones.py, só esses), a gaiola do empilhador
    (dims 0,80 × 1,11 × 1,15) e se a pilha na garra (`item` 0,23 abaixo do pulso, `pulso_dz` +0,10: a gaiola desce
    0,34 m) fica dentro da gaiola; (2) expressa/quântica: só cor/acabamento — o motor duplo e os rolos de apoio da
    expressa, o leito de bobinas, o campo violeta, os anéis, o conversor e a levitação dos itens da quântica não
    entraram; o divisor e a junção de 3 vias continuam servindo a todas as classes (não limitam a vazão), como na
    rápida; (3) a 30 quadros/s a esteira entrega no máximo 1 item por tick por caminho: a quântica fica exatamente no
    teto (30/s); abaixo de 30 quadros/s o laço da saída entrega mais de um por tick (até 8); (4) **braço quântico**
    (tem estudo, mas é outra máquina: lança telescópica de 5 seções que estica de 1 a 3 tiles e campo violeta que leva
    as placas por cima da lança — não serve o IK de 2 elos do Animador) não entrou: pede animação própria; está travado
    pela `computacao_quantica` de qualquer jeito; (5) trem-tanque: o vagão não mostra o nível (o modelo não tem
    visor/parte para isso); a estação não tem modelo de bomba (sem estudo) nem boca de cano no modelo: o cano só
    encosta na borda; (6) vagão-tanque e trem-tanque só jogáveis quando o `trem_automatico` existir (sinal em cadeia e
    rotas com condição — fase 3); (7) empilhador: a garra desenha um item só (a pilha não aparece); o contador de LEDs
    e a prensa/pinças ficam parados (sem animação do estudo); pega só o que já está na origem (não espera completar 4).

### Progresso das fases 3+4
- [x] **Lote 16: trilhos, drones e lógica** (estudos novos estudo_sinal_cadeia.py, estudo_bomba_estacao.py,
      estudo_trilho_energizado.py, estudo_locomotiva_eletrica.py, estudo_sensor_esteira.py, estudo_sensor_tanque.py,
      estudo_comparador.py, estudo_valvula.py, estudo_bau_estoque.py — os de lógica com a base comum lote16_base.py —
      e o braço quântico do estudo_bracos_novos.py; conversão em arte/estudos/conv_lote16.py; testes
      test_trem_automatico.gd, test_trem_eletrico.gd, test_rede_logica.gd, test_bau_estoque.gd, test_braco_quantico.gd
      e test_vagao_tanque.gd refeito para a bomba; roteiro sem janela `-- modo demo roteiro lote16`). Pesquisas novas
      em progressao.json (4): trem_automatico, trem_eletrico, rede_logica (jogáveis) e braco_quantico (travada:
      `computacao_quantica` sem estudo); vagao_tanque passa a ser pesquisável e drones_logisticos libera o baú de estoque.
      Categoria nova **Lógica** no menu. Cada estudo foi montado em cima do estudo aprovado da peça parecida (o script
      roda o estudo-base e acrescenta o que é novo), no mesmo nível, sem fotos (conferido por vistas rápidas internas,
      apagadas).
  - **Sinal em cadeia** (trem_automatico): o sinal de bloco com cabeça de cadeia (3 LEDs violeta que correm / anel
    vermelho), elos estampados, lidar da saída, módulo de cadeia e faixa violeta. Divide blocos como o sinal; o trem só
    passa se reservar, tudo ou nada, os blocos até o próximo sinal comum e o bloco depois dele (`GrafoTrilhos.cadeia`,
    `Trem._trecho_cadeia`). **Rotas com condição** no painel do trem (parada curta, 30 s, até encher, até esvaziar, por
    estação; esperando, troca carga a cada 1 s). Destrava o vagão-tanque.
  - **Bomba de estação** (vagao_tanque): bomba de lóbulos reversível com motor deitado, braço de carga com junta
    giratória e acoplador de engate seco na borda das costas, boca de cano na frente. Faz o papel que o cano fazia (o
    cano encostado direto não liga mais); 40 kW, vazão 1.000/s × energia; anima bombeando.
  - **Trilho energizado** + **locomotiva elétrica** (trem_eletrico): via reta do estudo dos trilhos com terceiro trilho
    em isoladores, tampa baixa (0,18 m: o estrado dos trens passa por cima) e eletroduto de alimentação com luz violeta
    (terminal do fio); peças encostadas formam um trecho e um poste perto de uma energiza o trecho. A locomotiva do
    estudo do trem sem o diesel, com caixa de resistores, buchas, sapatas coletoras por dentro da tampa e pintura
    grafite azulada; peça **trem elétrico**: 2× velocidade e tração no trilho energizado com energia (puxa 400 kW),
    1,5 m/s na bateria fora dele. A diesel agora polui andando (6 pontos/min por locomotiva).
  - **Rede lógica** (rede_logica): sensor de esteira (ao lado da esteira; cortina de luz, apalpador, contador de
    tambores; itens/min da média de 10 s), sensor de tanque (peça de cano; coluna de levitação com bolha âmbar; nível da
    rede em %), comparador (balança de braço atrás de grade: esfera do valor × pesos do número; tomadas de comando nas 4
    bordas; liga/desliga as estruturas encostadas) e válvula (gaveta com atuador e pressostato; entre duas redes:
    acima/abaixo de um nível ou sempre). Canais A–D somam os sensores; o desligado pelo comparador entra em
    `Fabrica.ligada` (energia, bombas, braços, válvula).
  - **Baú de estoque** (drones_logisticos): o baú 1×1 em verde-oliva com plataforma de pouso, escotilha de teto e
    farol. A sobra da garra vai para o estoque mais perto com lugar (antes voltava ao núcleo); requisitante sem provedor
    é servido do estoque.
  - **Braço quântico** (braco_quantico, travado): convertido com a lança de pé e as partes lanca1..4, ponta, cabo,
    carretel e anel1..8; `Animador._lanca_quantica` estica a lança até o alcance (1 a 3 tiles, painel do braço) e o
    item voa pelo caminho do campo (`ponto_garra`). Ciclo 0,2 s, até 8 iguais por vez.
  - Verificação: 67.572 verificações, 0 falhas (testar.sh); os 137 scripts compilam (carregados sem janela); a demo
    (`--quit-after 400`), `-- modo demo roteiro trem` e `-- modo demo roteiro lote16` (trem elétrico a 12 m/s parando
    na estação, sensor contando, bomba enchendo a estação, válvula, braço quântico entregando 64 placas) rodam sem
    erro.
  - Pendências: (1) nada visto em imagem (sem fotos): conferir as 10 silhuetas no zoom normal, as listras da tampa do
    terceiro trilho (no assado viraram manchas escuras), a pintura azulada da elétrica e o verde-oliva do estoque;
    ícones dos 10 pelo render Workbench do icones.py (só esses; o do braço quântico sem o rastro de anéis);
    (2) **mudanças de regra a confirmar com Sapyst**: o cano encostado na estação não liga mais (precisa da bomba de
    estação, com energia); a locomotiva diesel passou a poluir; (3) trem que não acha caminho para a próxima estação
    (malhas separadas, estações de outra linha) fica "sem rota" — já era assim; no painel, ligar só as estações da
    linha resolve; (4) o sensor de esteira conta pela fila: item que um braço põe ou tira entre o sensor e a saída
    pode errar a conta em 1; só olha esteira no chão (não a elevada); (5) as peças de lógica não gastam energia; o
    comparador não manda em outro comparador; não há fios de sinal visíveis (os canais são "sem fio"); (6) o sensor de
    tanque e a válvula animam o laço do estudo (a bolha não segue o nível de verdade); (7) a locomotiva elétrica não
    tem faísca nas sapatas nem som próprio; o trem elétrico fora do trilho energizado usa a bateria sem limite de
    tempo; (8) braço quântico: o campo translúcido saiu (o item voa sem o tubo violeta), as lâminas das ventoinhas
    seguem o laço do estudo, os anéis da descida ao norte passam por cima do tile da frente (como no estudo) e
    7.860 triângulos (mais que os outros braços, ~4.000); segue travado pela `computacao_quantica`; (9) o
    baú de estoque não tem limite por item nem filtro; a escotilha do teto anima no laço (não abre só quando o drone
    chega); (10) porto logístico e baús provedor/requisitante seguem sem modelo próprio (a estação e o baú comum fazem o
    papel).

- [x] **Lote 17: sensor de varredura** (estudo estudo_sensor_varredura.py feito pelo Antigravity, sem alteração;
      arte/estudos/conv_lote17.py; categoria de arte e do menu nova **Proliferação**; teste test_sensor_varredura.gd;
      roteiro sem janela `-- modo demo roteiro lote17`). Pesquisas novas em progressao.json (2): sensor_varredura
      (eletrônica; básico × 20) e cartografia "Varredura profunda" (sensor + processador; básico/automação/químico ×
      50; modo `varredura_profunda`). Com elas ficam pesquisáveis a **artilharia**, a **Leitura ambiental**
      (monitor_ambiental) e, com o pacote de tempestade, dano/alcance da artilharia 1.
  - **Modelo**: 7.133 triângulos, 2×2 (1,91 × 1,91 × 2,18 m), sem bocas. Fica o laço do estudo: o giro (garfo, mesa,
    pinhão, pistões) dá a volta em 4 s e a antena sobe e desce de 12° a 26° com os pistões acompanhando; saem a mancha
    de óleo e a luz do radar; o pulso do cristal e a corrida dos LEDs eram animação de material (não vão no .glb): os
    8 LEDs e o cristal ficam acesos fixos com P_Cristal (o jogo pulsa enquanto trabalha). Ícone pelo render Workbench
    (só ele).
  - **Função** (`ambiente/varredura.gd`, regra "varredura"): 150 kW; com energia, revela 1 chunk a cada 60 s
    (÷ energia), do mais perto para o mais longe, até 6 (profunda: 16); chunk já todo visto entra na hora. Revelar
    tira o chunk da névoa (`Descoberta.marcar_chunk`) e cria os ninhos dele (`Colonia.descobrir_chunk`, mesmo longe
    da câmera: a artilharia já os mira). Ninhos dos chunks de um sensor de pé ficam marcados (alfinete "⚠ Ninho",
    `render/desenho_varredura.gd`); com a profunda, mede as jazidas dos chunks (total da mancha, pobre/média/rica,
    fator de riqueza) no painel e em rótulos no mapa. Anima com energia, no ritmo dela. Vai no save.
  - **Em desenvolvimento** (pedido de Sapyst): pesquisa fora do jogo ou travada por pacote/pesquisa que não existe e
    peça sem modelo ou só liberada por ela ficam em cinza escuro com a etiqueta "Em desenvolvimento"
    (`Tema.botao_desenvolvimento`) na tela de pesquisa e na barra; não se escolhem/concluem (`Pesquisa.disponivel`,
    `avancar`) nem se constroem fora da demonstração (`Construtor._cobrar_plano`, motivo `em_desenvolvimento`).
    test_pesquisa.gd (`test_em_desenvolvimento`; `test_infinitas` passou a simular numa cópia dos dados, porque as
    infinitas pedem o pacote gênese).
  - Verificação: 67.786 verificações, 0 falhas (testar.sh); os 140 scripts compilam (carregados sem
    janela); a demo (`--quit-after 400`) roda sem erro; `-- modo demo roteiro lote17` revelou 16 de 16 chunks, marcou
    7 ninhos e mediu 5 jazidas (marcas desenhadas: 7 + 5), sensor animando com energia. test_esteira_niveis.gd
    ajustado (a quântica agora vem "em_desenvolvimento", não "bloqueado"); docs/RECURSOS.md regerado.
  - Pendências: (1) nada visto em imagem (sem fotos): conferir no zoom normal a silhueta (a grelha do refletor ficou
    rala depois da redução), os LEDs acesos fixos e o tamanho do alfinete/rótulos; (2) a **mira automática**
    (`artilharia_automatica`) segue em desenvolvimento e hoje a artilharia já mira sozinha qualquer ninho no alcance
    (não exige ninho marcado) — decidir com Sapyst se a artilharia passa a mirar só ninhos marcados pelo sensor;
    (3) a varredura não tem custo além da energia, nem raio visível (a ordem é por chunk, não por círculo); ninhos
    marcados só somem quando o sensor sai (o que foi revelado continua descoberto); (4) as faixas de riqueza
    (20 mil / 60 mil) são estimativa — calibrar quando houver mapas maiores.

- [x] **Lote 17: farol de cristal, posto avançado, lançador de sementes, receptor de cápsulas, transportador
      quântico, silo de lançamento** (estudos do Antigravity, sem alteração; arte/estudos/conv_lote17.py; um por vez;
      testes test_farol_cristal.gd, test_posto_avancado.gd, test_lancador_sementes.gd, test_receptor_capsulas.gd,
      test_transportador_quantico.gd, test_silo_lancamento.gd; roteiro `-- modo demo roteiro lote17` ampliado). O
      silo e o foguete de proliferação (`silo_lancamento`, `foguete_proliferacao`, modo `carga_semente`) também
      entraram — ligados e em desenvolvimento (casco de foguete e propulsão de cristal não existem). Pesquisas novas em
      progressao.json (5 + 2): farol_cristal (eletrônica; básico × 10) — **jogável**; posto_avancado (básico/automação/
      militar × 50), nucleo_semente (5 pacotes × 150; item núcleo-semente + receita na montadora), colonias (5 × 200;
      modo `colonias`; item pacote gênese, sem receita) e transportador_quantico (6 × 300, com o pacote quântico) —
      **ligadas mas em desenvolvimento**: o posto pede a `transmissao` (poste alto, sem estudo) e o resto da
      proliferação vem depois dele; o transportador pede também a `computacao_quantica` e o pacote quântico. Na
      demonstração todos se constroem.
  - **Modelos**: farol 5.080 tris (1×1; 1,06 × 1,06 × 2,84 m: os estais passam 3 cm do tile; raiz do .glb com
    sufixo `_raiz`, senão "farol_cristal" terminaria em _cristal e o Animador pulsaria o modelo inteiro); posto 8.746
    (3×3, 4 bocas de entrada; antena e pistões); lançador 6.020 (3×3, boca sul; sem a cápsula que voa e sem o clarão;
    o tubo passa 0,14 m da borda norte; `para_jogo.py` ganhou a opção `amostras` porque o recuo dos quadros 50–57
    não aparecia nas 8 amostras); receptor 5.912 (2×2, saída N0; sem a cápsula pairando e sem o canister); 
    transportador 7.550 (3×3, entrada S1 e saída N1; sem as cargas que somem por hide_render); silo 4.368 (3×3,
    itens S1 e O1, fluido L1; sem o foguete, que o jogo desenha crescendo com as partes e subindo). Pulsos e LEDs de
    material ficaram acesos fixos. Ícones pelo render Workbench do icones.py (só esses 6); ícones do núcleo-semente
    (do núcleo de cristal) e do pacote gênese (do pacote de pesquisa) derivados (derivar_icone.gd).
  - **Função**: farol (`ambiente/farol.gd`): 30 kW; à noite (luz do dia < 0,35) acende — luz de 10 m
    (`render/desenho_farol.gd`), tira a névoa num círculo (`Descoberta.marcar_circulo`) e avisa quando uma aranha
    entra na luz (1 aviso a cada 30 s por farol). Posto (grupo poste, `Fiacao.eh_nucleo`, `Fabrica.eh_posto`):
    −150 kW inesgotável sem cabo; estoque próprio de 3.200 em `Fabrica.baus` (braço; papel "estoque" dos drones); obra
    a até 32 m paga primeiro com ele (`Construtor.estoque_local`, `_pagar`, `rel.locais` no desfazer). Lançador
    (`ambiente/lancador.gd`): 600 kW (5% parado: `Fabrica.fator_kw`); semente por braço; rumo + distância no painel
    (60–400 m, anel no chão); carrega 20 s × energia, dispara (laço do estudo do começo: `Animador.reiniciar`), a
    cápsula sai em 2,08 s e voa a 40 m/s em arco; no lugar seco/plano/livre mais perto do alvo (até 6 tiles) nasce
    o posto avançado, limpando árvores e pedras; o chunk sai da névoa (e os ninhos dele aparecem). Colônias
    (`ambiente/genese.gd`): com `colonias`, o posto nascido da semente é colônia (kit no estoque) e faz 1 pacote
    gênese a cada 30 s, mandado por cápsula (60 m/s) ao receptor com energia e lugar mais perto; sem receptor, espera
    na colônia (até 20). Receptor: 100 kW, guarda 100 (braço tira), o laço toca a cada chegada. Transportador
    (`ambiente/transportador.gd`): 500 kW; entrada 20 / saída 200 na estrutura; 5 itens/s × energia para outro do
    mesmo canal (A–D) com lugar, em rodízio. Silo (`ambiente/silo.gd`): 1 MW; braço põe só o que a parte/carga pede;
    1 parte a cada 10 s × energia (1 casco + 5 processadores quânticos + 50 de propelente), 100 partes, depois a
    carga-semente (30 s, com a pesquisa do foguete); "Lançar o foguete" no painel → 6 s de subida
    (`render/desenho_silo.gd`) e a tela de vitória (`MenuPausa.abrir(false, true)`). Save: "lancador" e "genese"
    (voos); o resto vai na estrutura do mapa.
  - Verificação: 68.251 verificações, 0 falhas (testar.sh); os 154 scripts compilam (carregados sem janela); a demo
    (`--quit-after 400` e `res://cenas/mundo_demo.tscn --quit-after 600`) roda sem erro; `-- modo demo roteiro
    lote17`: 2 faróis acesos à meia-noite (2 luzes), farol no posto com energia sem cabo, lançador disparou, a semente
    pousou e virou colônia (kit com 2 drones), a colônia mandou 1 pacote gênese ao receptor, o transportador A
    mandou 10 engrenagens ao B; o silo (partes e carga postas pelo roteiro) lançou o foguete. docs/RECURSOS.md
    regerado.
  - Pendências / decisões para Sapyst: (1) nada visto em imagem (sem fotos): silhueta, luz do farol, voo da cápsula e
    anel do alvo; (2) a **Transmissão longa** (poste alto, lote 13) destrava toda a proliferação — até lá posto,
    lançador, receptor e transportador só na demonstração; (3) núcleo-semente na montadora comum (a montadora 3 não
    existe); (4) "estoque próprio" do posto = estoque de onde a obra perto dele paga primeiro (+ braço e drones) —
    confirmar se é isso; (5) a colônia não tem modelo próprio (é o posto avançado com kit) e os 2 drones do kit vão
    como item no estoque (não viram frota sozinhos); (6) o transportador troca com qualquer outro do mesmo canal, sem
    exigir que esteja numa colônia; (7) a boca N0 do receptor fica no tile oeste, mas a rampa do estudo sai no meio da
    borda (meio tile de diferença; a saída é por braço); (8) as faixas de alcance/tempo (carga 20 s, 40 m/s, 60 m/s,
    600/100/500 kW, taxa 5/s, silo 1 MW e 10 s por parte) são estimativas — calibrar jogando; (9) o silo ainda não
    liga no cano (o propelente de cristal não existe; entra por `SiloLancamento.abastecer`), e a vitória só abre a
    tela (não há cena/créditos de fim); (10) o estudo `estudo_poste_alto.py` (lote 13) apareceu pronto: é ele que
    destrava a `transmissao` e, com ela, toda a proliferação.

- [x] **Lote 13 (energia I): poste alto, turbina de correnteza, gerador a fluido, painel solar 2** e **lote 10 (produção
      I): montadora 2, refinador 2** (estudos do Antigravity, sem alteração; arte/estudos/conv_lote13.py e
      conv_lote10.py; um por vez; testes test_poste_alto.gd, test_turbina_correnteza.gd, test_gerador_fluido.gd,
      test_painel_solar_2.gd, test_montadora_2.gd, test_refinador_2.gd; roteiro `-- modo demo roteiro lote13`). Pesquisas
      novas em progressao.json (6, todas jogáveis): transmissao, turbina_rio, combustivel_seiva, renovavel_2,
      montadora_2, refinador_2 — marcadas "existente" no .mmd. Com a **transmissao**, o posto avançado, o núcleo-semente
      e as colônias saíram do "em desenvolvimento"; com o **refinador_2**, a estação de tratamento também.
  - **Modelos**: poste alto 3.702 tris (1×1, 5,7 m; as cruzetas passam do tile, ±0,79 m lá no alto; `terminais` no pé
    das 4 cadeias de isoladores); turbina de correnteza 5.347 (2×2; linha d'água do estudo na altura do chão do rio;
    sem a arfagem do casco — tudo preso nele iria para a parte móvel); gerador a fluido 7.410 (3×3, FLUIDO_ENT_S1; sem
    o tremor do motor e as manchas); painel solar 2 4.800 (2×2; orçamento 14.000 para o rastreador, que se mexe
    inteiro, passar quase sem redução); montadora 2 11.108 (3×3, S1 → N1 + fluido O1; sem as peças em trânsito e o
    feixe); refinador 2 11.577 (3×3, fluidos O1 e S1, L1, item N0 no tile oeste; o estudo tem 28.672; sem as células
    ejetadas e o flare). `para_jogo.py`: peça acesa (P_Cristal/P_Fogo) que se mexe agora também marca "anima" (o anel
    do poste alto ficava parado). Ícones pelo render Workbench do icones.py (script de um modelo só; só esses 6).
  - **Função**: poste alto (raio_fio 30, raio_ligacao 3; `Construtor.PASSO_POSTE` 20; anel com
    `Fabrica.transmitindo`); turbina de correnteza ("no_rio", "flutua", renovável "rio": 150 kW × `Fabrica.rio` =
    `Clima.vazao_rio`, estação + chuva; motivo "fora_do_rio"); gerador a fluido ("combustivel_fluido", fluido novo
    `combustivel_seiva`, receita no refinador; `Fabrica._tick_geradores_fluido`); painel solar 2 ("perda_nuvem" 0,15,
    `Fabrica.sol_limpo`/`encoberto`); montadora 2 e refinador 2 (mesmo "maquina", velocidade 1,0 / 2,0,
    "encaixes_modulo" só no painel).
  - Verificação: 68.545+ verificações, 0 falhas (testar.sh); os 161 scripts compilam (carregados sem janela); a demo
    (`--quit-after 400 -- modo demo` e `--quit-after 600 res://cenas/mundo_demo.tscn`) roda sem erro; roteiro lote13:
    energia do gerador a fluido (cano) atravessa 28 m de linha alta até a montadora (100%), anel girando, cabos
    desenhados; turbina no rio a 150 kW (primavera) ligada a um poste alto na margem; painel 2 a 489 kW (o 1 daria
    278); montadora 2 e refinador 2 trabalhando. docs/RECURSOS.md regerado.
  - Pendências / decisões para Sapyst: (1) nada visto em imagem (sem fotos); (2) **combustível de seiva** sem a água da
    árvore (refinador só tem 2 bocas de fluido) — pôr a água quando quiser (o refinador 2 tem 3 bocas); (3) "rende 15%
    com nuvem" do painel 2 lido como **perde só 15%**; (4) a turbina de correnteza vale em qualquer rotação (a
    correnteza não precisa bater com o eixo do rotor) e a seca é a `vazao_rio` da estação; (5) poste alto atrai raio
    (5,7 m: o mais alto pega) — sem para-raios próprio; (6) montadora 2 e refinador 2 não trocam a máquina antiga no
    lugar (a árvore não prevê) e os encaixes de módulo ficam vazios; a boca de fluido da montadora 2 não tem receita;
    o pacote de tempestade continua saindo também na montadora comum (restringir à 2 quebraria fábricas prontas);
    (7) números (custos, 700 kW do refinador 2, 200 kW da montadora 2, poluição 45 do gerador a fluido, vazões) são
    estimativa; (8) acumulador 2 (estudo pronto) ficou para a próxima rodada (limite de 6 por rodada).

- [x] **Acumulador 2 e lote 14 (energia II): turbina alta, acumulador de cristal, reator de cristal, reator de fusão,
      núcleo de singularidade** (estudos do Antigravity, sem alteração; arte/estudos/conv_lote14.py; um por vez; testes
      test_acumulador_2.gd, test_turbina_alta.gd, test_acumulador_cristal.gd, test_reator_cristal.gd,
      test_reator_fusao.gd, test_nucleo_singularidade.gd; roteiro `-- modo demo roteiro lote14`). Pesquisas novas em
      progressao.json (6): acumulacao_2, turbina_alta, acumulador_cristal, reator_cristal, fusao, singularidade — marcadas
      "existente" no .mmd. Com a **turbina_alta**, o defletor de vento saiu do "em desenvolvimento". `fusao` e
      `singularidade` ficam em desenvolvimento (computação quântica e pacote quântico não existem).
  - **Modelos**: acumulador 2 7.489 tris (2×2); turbina alta 7.562 (3×3; nacele e hélice viram partes do Animador; rotor
    passa do tile lá no alto); acumulador de cristal 5.846 (2×2); reator de cristal 6.702 (3×3, só ITEM_ENT_S1); reator
    de fusão 6.792 (3×3, ITEM_ENT_S1 e FLUIDO_ENT_O1); núcleo de singularidade 12.620 (3×3; mais pesado que os
    11.577 do refinador 2; 3,16 m em y). Saem os itens em trânsito (célula, cartuchos, cristal) e os efeitos. Estes
    estudos dão `sys.exit` no modo "nada": conv_lote14 os roda em modo "montar" (`SO_MONTAR`).
  - **Função e números**: ver "Acumulador 2 e lote 14" em docs/ARVORE_TECNOLOGIA.md. Sem item, fluido ou receita novos.
  - Verificação: 68.817 verificações, 0 falhas (testar.sh); os 167 scripts compilam; a demo (`--quit-after 400 -- modo
    demo` e `--quit-after 600 res://cenas/mundo_demo.tscn`) roda sem erro; roteiro lote14: as 6 peças na mesma rede, com
    os painéis abertos, reator de cristal a 8 MW e fusão a 30 MW (água do cano), animando. docs/RECURSOS.md regerado.
  - Pendências / decisões para Sapyst: (1) nada visto no jogo em imagem, só os ícones; (2) **bocas sem função**: a árvore
    não pede cartucho gasto nem vapor nem refrigeração no reator de cristal, então N1/O1 (cristal) e N1/L1 (fusão) ficam
    só como desenho — se quiser subproduto ou água no de cristal, é só pedir; (3) números que a árvore não dá são
    estimativa: MJ por combustível, estoque, 15 de água/s, poluição 20 e 8, custos de construção, vida; (4) o reator
    funciona pela mesma regra do gerador: a esteira não enfia item em construção, precisa de braço na boca sul; (5) a
    turbina alta deixa o cata-vento e os pinhões do estudo fixos: a nacele gira pelo vento de verdade.

- [x] **Lote 10, 2ª parte: fornalha de aço, fornalha elétrica, broca grande, laboratório 2** (estudos do Antigravity, sem
      alteração; arte/estudos/conv_lote10.py; um por vez; testes test_fornalha_aco.gd, test_fornalha_eletrica.gd,
      test_broca_grande.gd, test_laboratorio_2.gd; roteiro `-- modo demo roteiro lote10`). 4 pesquisas novas em
      progressao.json, marcadas "existente" no .mmd.
  - **Modelos**: fornalha de aço 6.456 tris (2×2, S1 → N0); fornalha elétrica 5.515 (2×2, S1 → N0 + fluido O1; `amostras`
    densas para o 1º eletrodo não sair parado); broca grande 6.972 (3×3, saída S1 + fluido O1; 5,22 m de altura; a vibração
    da peneira fica de fora, 8 mm que zeram nas amostras); laboratório 2 7.918 (3×3, S1 e O1 + fluido L1). Saem efeitos e
    itens em trânsito do laboratório. Os lingotes ficam sempre em brasa: o esfriar era animação de material. Ícones pelo
    render Workbench do icones.py (só esses 4).
  - **Função e números**: ver "Lote 10, 2ª parte" em docs/ARVORE_TECNOLOGIA.md. Sem item, fluido ou receita novos.
  - **O que o laboratório 2 destrava**: só tira o pré-requisito da computação quântica; ela segue fora do progressao.json
    até existirem a forja quântica e o pacote quântico, então fusão, singularidade, braço quântico, esteira quântica,
    transportador quântico, regulador climático e as infinitas continuam em desenvolvimento.
  - Verificação: 69.001 verificações, 0 falhas (testar.sh); os 171 scripts compilam; a demo (`--quit-after 400 -- modo demo`)
    roda sem erro; roteiro lote10: broca despejando na esteira, fornalha elétrica a 180 kW sem emissão, laboratório 2
    gastando pacote. Nenhum teste antigo precisou de ajuste. docs/RECURSOS.md regerado.
  - Pendências / decisões para Sapyst: (1) nada visto no jogo em imagem, só os ícones; (2) "−25% de poluição" lido por
    produto, como no refinador 2 (6/min no total, mais que os 4 da fornalha); (3) números que a árvore não dá são
    estimativa: kW, vida e custos de construção; (4) bocas de fluido sem função (elétrica O1, broca O1, laboratório L1);
    (5) só o laboratório 2 para de animar quando não pesquisa; o laboratório 1 segue animando sempre.

- [x] **Lote 11: forja quântica, fundição de cristal, montadora 3, montadora quântica, extrator ressonante, broca de núcleo,
      laboratório quântico, irradiador de módulos** (estudos do Antigravity, sem alteração; arte/estudos/conv_lote11.py; testes
      test_forja_quantica.gd, test_fundicao_cristal.gd, test_montadora_3.gd, test_montadora_quantica.gd, test_extrator_ressonante.gd,
      test_broca_nucleo.gd, test_laboratorio_quantico.gd, test_irradiador_modulos.gd, test_modulos.gd, test_municoes_especiais.gd,
      test_ninhos_e_mira.gd, test_infinitas_novas.gd, test_arvore_completa.gd; roteiro `-- modo demo roteiro lote11`). 37 pesquisas
      novas: as 166 da árvore agora estão em progressao.json.
  - **Modelos** (tris): forja 8.020; fundição 6.726; montadora 3 3.764; montadora quântica 5.736; extrator 4.952; broca de núcleo
    3.784; laboratório quântico 5.332; irradiador 6.704. Ficam as peças em trânsito (laço fechado, sem sumir). Ícones pelo render
    Workbench (só esses 8); ícones dos 16 itens novos derivados por matiz (derivar_icone.gd), modelo na esteira idem.
  - **Função, itens e decisões**: ver "Lote 11" em docs/ARVORE_TECNOLOGIA.md.
  - **Destravou**: fusão, singularidade, braço/esteira/transportador quânticos, regulador climático, silo de lançamento, foguete de
    proliferação (vitória alcançável no modo novo) e as 10 infinitas. test_arvore_completa.gd percorre a árvore do zero, sem contar o
    kit inicial: pesquisa só entra com pré-requisitos feitos e pacotes com receita liberada cujas entradas têm fonte.
  - **Em desenvolvimento**: nada. Nenhuma pesquisa nem peça.
  - Verificação: 72.5 mil verificações, 0 falhas (testar.sh); os 185 scripts compilam; a demo (`--quit-after 400 -- modo demo`) roda sem
    erro; roteiro lote11: as 6 peças do pátio com energia, módulos e irradiador valendo, painéis abertos. 9 testes antigos ajustados
    (esperavam isso em desenvolvimento; test_pesquisa simula o que faltava para seguir testando o mecanismo). docs/RECURSOS.md regerado.
  - Pendências / decisões para Sapyst: (1) nada visto no jogo em imagem, só os ícones; (2) **jazidas não se esgotam no jogo**: a
    "jazida esgotada rende 10%" da broca de núcleo está pronta na máquina, mas sem gatilho (ela hoje é só a broca mais rápida, 2,0
    estimado); ligar esgotamento mudaria a partida inteira, é decisão dela; (3) **artilharia passou a pedir ordem** até a Mira automática
    (a pesquisa não teria efeito de outro jeito), e **Escavar passou a pedir pesquisa**: partidas em andamento notam as duas; (4)
    "Simbiose: estruturas viram abrigo de musgo" é visual e não entrou; "laboratórios das colônias somam" já era verdade; (5) núcleo-semente
    segue na montadora comum e pacote de tempestade também (a tabela pede montadora 3 e 2 "ou melhor"): não mudei para não parar fábrica
    pronta; (6) números estimados: kW, vida, custos, tempos dos módulos, efeitos das munições; módulo de produtividade vale em toda
    receita (no Factorio, só intermediários) e o irradiador não leva produtividade; (7) bocas de fluido sem função nas 6 peças; (8) módulo
    só entra pelo painel, vindo do núcleo (braço não encaixa).

### Pedido 2: modelos antigos, cápsula, painel e fps de novo (2026-10-31)
Ver docs/BRIEF_ANTIGRAVITY_2.md. Conversão: arte/estudos/conv_antigos.py (remendos dos estudos ficam lá); teste novo: jogo/testes/test_modelos_antigos.gd.
- [x] **Modelos** (tris, limite do pedido): plataforma_agua 568 (600), ponte_agua 320 (400), poca_seiva 174 (300), aranha_corpo 656 (1.500), aranha_femur 136 (200), aranha_tibia 84
  (150), ninho_aranha 1.232 (5.000). Nenhum passou. `por_peca` ligado em todos; nenhum precisou de redução, o peso real ficou abaixo do alvo.
  - **Plataforma e ponte**: uma malha só (`Materiais.malha_de` só pega a primeira). Plataforma 1,00×1,00 m exatos no topo, pés em 0, topo em 1,90 = `ERGUIDO`. Antes: 0,96×0,984, com fresta. Ponte emenda
    em ±0,50 no fluxo, deque em 1,90, guias em 1,93. Foto `plataforma_grade`: sem fresta.
  - **Poça**: uma malha, seiva numa superfície P_Seiva lisa fora do assado; crosta e seiva escurecidas no conv. As bolhas do estudo saíram: a poça é MultiMesh do chunk, não anima.
  - **Aranha**: quadris conferidos em `MarchaAranha.QUADRIS`/`QUADRIL_Z`, fêmur vai do quadril ao joelho, ponta da tíbia em 0,90. O estudo fazia o cone do pé ao contrário (base larga no pé): desvirado no conv. Olhos separados
    e com o nome P_OlhoInimigo, senão a fúria (`Aranha.definir_furia`) não os acha. `aranha_montada` refeita dos 3 .glb (`blender -b --python conv_antigos.py -- aranha_montada`), porque estudo_drones.py a usa; a foto agora é a Aranha real, com IK.
  - **Ninho**: o `DesenhoColonia` ganhou Animador (o laço não tocava). No conv: blocos de minério para dentro dos 3×3, tampas na casca oca, e chão da câmara e chaminé acesos, porque o vermelho do estudo era a luz LuzNinho.
- [x] **Cápsula (nucleo_queda)**: 16.654 tris. **Causa do cone laranja**: a brasa da reentrada liga Emission Strength a um nó em ogiva e placas ablativas; `brilha()` trata a malha inteira como luz, material liso P_Fogo e redução a 200 tris.
  Agora são assadas, com a mancha da brasa como queimado na cor (conv_nucleo.py, `_preparar`). Achados no caminho: `hide_render` não vai para o glTF, então a ogiva ejetada ficava parada no ar a 4,5 m, e cabos-raiz, fragmentos, terra das pétalas e cratera
  (apagados pela limpeza) brotavam só na troca. Viraram escala quase zero animada. Cristal e frestas ficam acesos como no núcleo. Mesmo recorte do núcleo (±1,53; sem pedras, torrões, rachaduras).
  **Troca cápsula → núcleo**: caixa da pose final bate com a do núcleo a menos de 0,15 m (test_nucleo_queda.gd, `test_sem_pulo_na_troca`); `Abertura._trocar` volta o laço do núcleo ao quadro 1. Quadros 454–459 da abertura gravada: sem pulo visível, mas a placa "falta entrada" cobre boa parte do núcleo nessa hora.
- [x] **Painel**: arte/estudos/fotos/painel_final.png e .jpg (143 fotos; extras novos: plataforma_grade, poca_seiva, nucleo_queda_fim). cano_deslocado.jpg removida.
- [x] **Baterias**: 73.827 verificações, 0 falhas; 189 scripts compilam; demo e 37 roteiros sem janela sem erro de script (só o aviso de recursos na saída, que já existia). Nenhum limite de teste subiu.
- **Desempenho** (`roteiro carga`; Radeon 890M, 1280×720, tudo animando, sem vsync; sem outro jogo aberto, NVIDIA parada, carga ~1,4, com Claude e Antigravity abertos; 2 rodadas; celular NÃO medido):
  mostruário, 465 estruturas, 659 mil tris somados: 44 m 67–70 fps (p95 26–27 ms; GPU 11–12 ms; 5,9 mi tris desenhados; 3.667 chamadas), 25 m 130–132, 90 m 125–126.
  Pátio, 1.176 estruturas, 2,76 mi tris somados: 44 m 52–57 fps (p95 23–26 ms; GPU 9,8 ms; 6,6 mi tris; 5.345 chamadas), 25 m 73–77, 90 m 53.
  **Não comparar direto com os 33 e 17 fps da fase 5**: aquelas rodadas não têm condição anotada e as do A/B foram com outro jogo aberto. O que dá para comparar é o desenhado: mostruário 5,9 → 5,9 mi, pátio 6,5 → 6,6 mi (+2%). Não houve A/B só dos 34%, com e sem as 18 peças, na mesma condição.
  Mais pesadas: cápsula 16.654 (só na abertura), purificador atmosférico 16.130, núcleo 14.004, núcleo de singularidade 12.620, semeador de bioma 11.852, laboratório 11.756.
- **Problemas objetivos restantes** (painel e abertura): resolvidos ou remanejados na rodada abaixo; só sobra o que está em "Fica para Sapyst".

### Esteira direto no núcleo e defeitos do painel (2026-10-31)
- [x] **Esteira entra no núcleo sem braço** (pedido de Sapyst). `Fabrica._ligar_pontas` + `_entrega_no_nucleo`: a última peça do caminho, no chão e no mesmo nível de terreno, que aponta para qualquer tile do núcleo entrega no `estoque_nucleo`. Vale só `nome == "nucleo"`; posto avançado, máquina e baú continuam pedindo braço. O estoque do núcleo não tem limite, então a esteira nunca para por ele. `Construtor._recebe` conta o núcleo em frente: o traço termina em reta (o traço não vira sozinho para o lado do núcleo fora da boca). Peça "fim" de save antigo encostada também entrega; entrada de passagem subterrânea não. Salvar/carregar: nada novo a guardar. Teste: jogo/testes/test_esteira_nucleo.gd. docs/COMO_JOGAR.md atualizado.
- [x] **Núcleo sem "falta entrada"**: `Portas.mostra_aviso` exclui o núcleo; entradas opcionais.
- [x] **Poça de seiva**: **causa** dos discos: borda clara mais alta que a seiva, mesmo contorno e alturas diferentes por tile. Agora a crosta fica abaixo da seiva e escura, contorno irregular (conv_antigos.py), `DesenhoChunk` aumenta 1,5× e nivela a altura (só poça), e o shader (`seiva` em material_pf.gdshaderinc) dá ondulação e reflexo no espaço do mundo, contínuos entre poças, sem transparência. 218 tris.
- [x] **Capim**: **causa**: `atualizar_fabrica` pulava ninho e máquina de jazida inteiros, sem marcar nada. Agora marca B (o que a grama lê) só nos tiles da peça, sem R (sem piso).
- [x] **Traço preto dos extratores**: **causa**: cabo de energia real (`DesenhoFios`) ligando a peça da foto a um poste da base de demo ao lado; no jogo um poste perto faz o mesmo e é o certo. O roteiro de fotos agora busca jazida longe de construção (`_tem_construcao_perto`).
- [x] **Ninho**: forro vermelho-escuro por dentro da parede (conv_antigos.py). 1.336 tris. A foto agora registra o ninho no mapa.
- [x] **Estação de drones**: convés com tinta quase lisa no lugar do grafite que assava em manchas; óleo fora (ajustes_fase5.py). 9.379 tris.
- [x] **Mina de pulso**: sem capim, pedrinhas e chamusco; monte baixo e menor; anel violeta aceso em volta da tampa (a bobina do estudo ficava embaixo dela). 2.743 tris.
- [x] **Braço quântico**: saem o rastro e os anéis da descida e do pouso (conv_lote16.py); `lanca.aneis` vazio. test_braco_quantico.gd ajustado para isso. 7.245 tris. Na foto, ele ficava pequeno porque a caixa incluía os anéis.
- [x] **Plataforma e ponte**: deque de aço escuro quase sem ferrugem (conv_antigos.py) e giro por tile em `DesenhoPlataformas`. Conferidas na água de verdade: extra novo `plataforma_rio`.
- [x] **Ícones**: só mina, braço quântico, estação, plataforma e ponte. **Painel** remontado (144 fotos).
- Verificação: 73.917 verificações, 0 falhas; nenhum limite de teste subiu; demo sem janela sem erro de script.
- **Fica para Sapyst**: (1) **corpo do núcleo pequeno para os 3×3**: não mexido, é decisão dela. (2) **Poça**: emenda, mas o brilho é reflexo largo e discreto, lê como mancha escura molhada; o terreno fura a mancha em alguns pontos; não vista com sol em outro ângulo nem em partida. (3) **Braço quântico**: a cabeça ainda tem dois anéis empilhados, presos à ponta da lança. (4) O corte de capim no ninho e nos extratores deixa um quadrado curto em volta da base. (5) Posto avançado segue com braço: decidir se deve receber como o núcleo.

### Pedidos de interface, salvar e vento (2026-10-31)
- [x] **Filtro em todo braço**: Auto ou 1 item, em grade de ícones no fim do painel (nome na dica); Braço com filtro segue com até 5. `Fabrica.max_filtros`, `escolher_filtro`; `filtros` na estrutura, como antes, vai no save. Save antigo com vários itens num braço comum continua valendo até tocar. Testes em test_braco_filtro.gd.
- [x] **Roda sobre a interface não dá zoom**: **causa**: `mouse_force_pass_scroll_events` vem ligado no Control e lista no fim da rolagem não consome a roda, então ela chegava ao `_unhandled_input`. `Toque.sobre_ui` (qualquer Control que receba mouse na posição, em todo CanvasLayer visível) em `ControleConstrucao`; também nos gestos de trackpad. test_interface_roda.gd + roteiro `roda_ui` (eventos reais na cena: mapa dá zoom; peças, categorias, ferramentas, status, detalhe, estoque, pausa e pesquisa não).
- [x] **Estoque do núcleo** (`interface/painel_recursos.gd`): casas de ícone + número curto, nome na dica. Vertical (padrão, à esquerda, abaixo do status) ou horizontal (`recursos_orientacao`, em Configurações). Alça "menos/tudo" (`recursos_resumo`) e mais colunas se não couber. Desvia da gaveta de detalhe e da dica, para antes de ferramentas, faixa, peças e categorias. A linha "Núcleo:" saiu do status. test_painel_recursos.gd.
- [x] **Escala da interface**: padrão 0,8, mínimo 0,68, máximo 1,6 (`Sessao.TEXTO_*`), passo 0,04. Config antiga em exatos 1,0 vira 0,8 uma vez (`ui_v2`): o arquivo grava tudo junto, então "nunca mexeu" só se vê pelo valor. Celular segue com 1,35. Configurações ganhou rolagem própria, porque a 160% não cabia na tela. Conferido em foto a 68% e 160%.
- [x] **Salvar automático**: desligado, 1, 2, 5, 10, 15 ou 30 min. O padrão seguiu 2 min (já definido). `AutoSalvar` conta tempo real; dados no quadro + cópia profunda, texto e disco no WorkerThreadPool; escrita atômica com checagem de erro; Salvar agora e fechar esperam a gravação em curso. Pátio: 1,5 ms no quadro; 2,9 ms na outra thread; 160 KB. Sem salvar em demo e abertura, e nem depois da derrota (antes, fechar o jogo recriava o save apagado). Testes em `user://testes_salvos` e `testes_configuracoes.cfg`. test_salvar_auto.gd. Roda real, com intervalo de 5 s: só grava depois da abertura; o Continuar lê o arquivo.
- [x] **Vento forte**: **causa**: frequência multiplicada pela força (`TIME * (1.2 + 1.2 * intensidade)`), em árvores e grama. Além de acelerar, salta de fase quando a força muda. Agora: relógio `vento_tempo` (+30% no máximo), inclinação média, trancos irregulares com volta lenta, desfase por planta, curva por altura com teto, topo descendo para não esticar. Sequência com céu limpo, 0,4 s entre fotos: copa de bétula, faixa de 2,4 px (vento 35%) × 16,8 px (100%), desloca 11 px em média; sobe em ~0,8 s e volta em ~3 s, sem ritmo fixo. Grama fica penteada na direção do vento. Copa baixa e redonda mexe bem menos (medido antes de aumentar a flexão das plantas baixas em ~50%; não remedido).
  **GPU** (pátio, Radeon 890M, 1280×720; 1 rodada antes × 2 depois): 44 m 11,4 → 11,2–11,5 ms; 25 m 8,1 → 9,8 ms; 90 m 6,1 → 6,1 ms; fps igual (o pátio é limitado pela CPU).
- Verificação: 74.229 verificações, 0 falhas; nenhum limite de teste subiu; 195 scripts compilam; demo sem janela sem erro de script (só o aviso de recursos que já existia).
- **Fica para Sapyst**: sensação do vento em movimento e no tufão com chuva (só vi sequências de fotos, sem chuva) e o tamanho de 68% na tela dela.

### Lista para a fase 3 — estruturas da árvore ainda sem estudo/modelo
(Fonte: "Estruturas: temos × precisamos" do docs/ARVORE_TECNOLOGIA.md. Entre parênteses, o que cada uma destrava do que
já está ligado e travado.)
- Produção: tudo feito (lotes 10 e 11).
- Energia: ~~poste alto, turbina de correnteza, gerador a fluido, painel solar 2, acumulador 2~~ (lote 13), ~~turbina alta,
  acumulador de cristal, reator de cristal, reator de fusão, núcleo de singularidade~~ (lote 14).
- Proliferação: ~~sensor de varredura, farol de cristal, posto avançado, lançador de sementes, receptor de cápsulas,
  transportador quântico, silo de lançamento~~ (lote 17, feitos).
- Drones: se Sapyst quiser modelo próprio, porto logístico e baús provedor/requisitante (o estoque já tem, lote 16).
- Com estudo mas ainda fora do jogo: divisor/junção de cada nível (hoje os de 3 vias servem a todas as classes).
