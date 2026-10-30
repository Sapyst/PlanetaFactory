# Guia dos estudos de modelo (PlanetaFactory)

Estudos isolados, fora do jogo: cada estrutura vira um script Blender (`estudo_<nome>.py`) nesta pasta, com fotos
realistas em Cycles para Sapyst aprovar. Os aprovados depois viram versão leve para o jogo (celular). Responder e
comentar em português do Brasil.

## Premissa do jogo
O jogador é uma IA com defeito que só quer se proliferar num planeta. As máquinas são de uma fábrica autônoma (sem
operador humano: nada de cadeira, escada de operador, volante de motorista; painéis e sensores servem à IA). Mistura
de tecnologia alta da IA com mecânica industrial pesada e desgastada.

**NÃO HÁ HUMANOS.** Nada que pareça máquina feita para gente: sem trator, bulldozer, caminhão, cabine, assento,
volante, guarda-corpo, escada de operador, porta de pessoa. (Terraplenagem em forma de trator foi recusada: "muito
humano build".) Rústico SIM — aço gasto, óleo, rebites, pistões — mas a função é **logicamente surreal**: fundir
conceitos (campo de força, levitação, ressonância, geometria perfeita demais, cristal que pulsa) com a mecânica pesada
que segura o fenômeno. Pense "o que uma IA construiria para si", não "o que uma empresa humana compraria".

## O que Sapyst exige (pedidos repetidos)
- **Detalhe desde o berço:** tubos, pistões, cabos, canos, escoamento, labaredas, fumaça, vapor, faíscas — tudo o
  que a lógica de fábrica autônoma pedir. Cada pistão ligado a algo lógico (camisa presa numa peça, haste na outra,
  mangueira chegando). Canos e mangueiras vêm de algum lugar e vão para algum lugar (tanque, bomba, coletor, caixa de
  junção). Cabos em feixes com abraçadeiras e eletrocalhas.
- **Robusto e sujo:** pintura amarela gasta e lascada, grafite, aço com ferrugem, fuligem, óleo vazando e escorrendo,
  cavaco/pó/lama onde faz sentido, listras de perigo em ladrilho. Nada polido demais ("modelo polido demais fica feio
  e irreal"). No jogo a sujeira cresce com o tempo e a chuva lava; nas fotos, mostre a máquina num estado de uso médio.
- **Tem de LER como a máquina que é** (a broca antiga "não parecia broca"): silhueta reconhecível de longe.
- **Nada entrando em nada sem motivo:** confira de perto. Peça que passa por dentro de outra só se é encaixe real.
- **Tubos parecem tubos:** muitos lados, sombra suave só nas laterais (`suavizar`), cotovelos redondos (esfera no
  canto) ou `toro` para anéis; flanges nas emendas.
- **Sem ciano fixo:** cores por situação e tipo. Energia da IA em violeta/âmbar é aceita.
- **Fogo** em volume que absorve (cor escura) com emissão forte (não fica pálido sob o sol) — ver `fogo_mat` em
  `estudo_fornalha.py`. **Fumaça** preta que dilui em cinza — `fumaca_grad_mat` em `estudo_fornalha.py`.

- **Armas:** cada tiro ejeta UMA cápsula modelada de verdade (corpo, aro, espoleta, boca queimada), quente, girando,
  com fiapo de fumaça, quicando com física simples e ficando no chão com uma última fumacinha. Literalmente cada tiro.

- **Nunca "enxuto":** mesmo peça pequena (drone, baú, cano) leva textura rústica carregada — lascas, amassados,
  remendos aparafusados, peça trocada de outra cor, fiação exposta, ferrugem, fuligem, óleo, poeira em cima, lama
  embaixo, números de série apagados. Drones aprovados em forma mas recusados por "muito enxuta".

## Peças prontas para copiar
- `base3d.py`: obj, caixa, caixa_de, cil, tubo, viga, bezier, mangueira, pedra, mancha, volume_mat, listras_mat,
  lampada_mat (o estudo preenche `base3d.M` com os materiais e chama `base3d.iniciar()` depois de
  `read_factory_settings`).
- `mats.py`: `material(nome, base, metal, rough, pintura, ferrugem, sujeira, desgaste, escovado)`.
- `estudo_fornalha.py`: modelo de cena e de tudo (suavizar, toro, tijolo, brasa, lingote que esfria, fumaça, fogo,
  vazamentos, pressão, câmera, modos foto/vídeo). `estudo_montadora.py`, `estudo_broca.py`, `estudo_nucleo.py`:
  outros exemplos aprovados.

## Regras técnicas
- Tamanho em tiles e portas (entrada/saída de item e fluido) iguais ao `arte/CATALOGO.md` do jogo
  (`/mnt/d/DATA/Trabalhos/Projeto/Projetos de Jogos/PlanetaFactory/arte/CATALOGO.md`). 1 tile = 1 m; x leste, y norte.
  A estrutura ocupa a área de tiles inteira (base/laje) e as bocas ficam no tile certo da borda.
- Animação no script em laço de 4 s (96 quadros a 24 qps), mesmo sem renderizar vídeo: o que gira gira, pistões
  andam, fumaça sobe, luzes piscam. Volume nunca com escala ~0 (OpenVDB aborta): esconder com `hide_render` em
  quadro-chave.
- Renderizar SÓ fotos: `~/.local/share/Steam/steamapps/common/Blender/blender -b --python estudo_<nome>.py -- foto`
  (em primeiro plano, com `timeout`). Fotos `<nome>_0..3.png` (4 vistas em volta) + `<nome>_perto.png`. NÃO rodar
  vídeo. NÃO esperar com `while pgrep -f ...` (casa com o próprio comando e trava).
- Olhar cada foto você mesmo e iterar até ficar bom e sem interpenetração. Exposição sem estourar em branco.
- Não mexer em arquivos de outros estudos nem no repositório do jogo.
- Ao terminar, devolver: caminhos absolutos das fotos, resumo curto do que o modelo tem, o que corrigiu e o que ficou.

## Ordem dos lotes (definida por Sapyst)
Depois do lote 7 (defesa): 9 (água) → 12 (limpeza) → 15 (clima) → 16 (trilhos, drones, lógica) → 17 (proliferação)
→ 8 (logística; já iniciado antes da ordem) → 13 (energia I) → 10 (produção I) → 14 (energia II) → 11 (produção II).
