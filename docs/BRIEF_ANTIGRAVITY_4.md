# Pedido 4 para o Antigravity: implementar direto no jogo, testar, commitar e lançar

Responda sempre em português do Brasil. Quem pede é Sapyst (trate no feminino).
**Trabalhe do começo ao fim sem parar para perguntar.** Quando houver dúvida, escolha o mais simples que cumpra o pedido
e anote a decisão no relatório final. Desta vez **você implementa no jogo**, testa, faz commit, push e release.

Pasta: `/mnt/d/Projetos/Jogos/PlanetaFactory` (repositório `github.com/Sapyst/PlanetaFactory`, público, MIT).
Godot 4.7.2, renderizador Mobile, projeto em `jogo/`. Blender em `~/.local/share/Steam/steamapps/common/Blender/blender`.

## Leia antes
- `jogo/README.md`, `docs/COMO_JOGAR.md`, `docs/PLANO_INTEGRACAO.md` (histórico e pendências).
- `docs/BRIEF_ANTIGRAVITY.md` e `docs/BRIEF_ANTIGRAVITY_3.md` (regras de arte; nunca efeito que pareça filtro de tela).
- `arte/estudos/FEITOS_ANTIGRAVITY_3.md` e `arte/estudos/efeitos/` (os 28 efeitos que você já fez).
- `git log -15 --stat` para ver o padrão de commits.

## Regras que não mudam
- **Identidade no GitHub: só "Sapyst".** Antes de cada commit/push rode
  `git grep -n -i -f <(grep -v '^#' ~/.claude/hooks/termos_privados.txt)` — tem de vir vazio. Não mude `git config`
  (o autor já é Sapyst). Nunca escreva nome real ou e-mail pessoal em arquivo, commit, notas de release.
- Commit em português, terminando com uma linha em branco e `Co-Authored-By: Antigravity`.
- **Nunca apague `jogo/.godot`** (o jogo fica em tela cinza). Se faltar: `godot --headless --path jogo --import`.
- Godot sempre com `flock /tmp/pf_godot.lock -c '...'` e `--audio-driver Dummy` em testes; testes **sem janela**.
  Não abra janela na tela dela, não feche o jogo dela, não toque no save (`~/.local/share/godot/app_userdata/PlanetaFactory/`):
  rode testes com `XDG_DATA_HOME` apontando para uma pasta temporária.
- Um Blender ou Godot pesado por vez.
- O jogo é testado no PC (Arch Linux) e também roda no celular (APK): o perfil celular da interface não pode mudar
  sem querer — `jogo/testes/conferir_celular.gd` (dentro do `testar.sh`) tem de seguir sem diferenças, salvo o que o pedido muda.

## Tarefas (nesta ordem; um commit por tarefa, com testes passando)

### 1. Travada ao trocar de categoria de construção
Trocar de aba no menu de construção cai a 1 fps. `BarraConstrucao._mostrar_categoria` (`jogo/interface/barra_construcao.gd`)
destrói e recria todos os botões a cada clique (ícone recarregado, consulta de pesquisa, texto com autowrap). Meça cada parte
por um roteiro sem janela (`jogo/interface/roteiro_teste.gd`; script `-s` não compila os autoloads), corrija a causa e troque
a recriação por painéis criados uma vez por categoria, só alternando visibilidade e atualizando quando pesquisa/custo mudar.
Teste: trocar de categoria não cria nem destrói botões e reflete pesquisa concluída.

### 2. Ambiente e efeitos no jogo
- Converta os 8 estudos `arte/estudos/estudo_amb_*.py` (67 modelos) mantendo os nomes que o jogo já usa (`modelos.json`),
  uma malha por modelo, origem na base, vento do shader funcionando, escala/área iguais. Não suba limites de triângulos de teste.
- Leve os efeitos de `arte/estudos/efeitos/` para `jogo/` e ligue: rastro e impacto por arma (metralhadora, torre de energia,
  lança-foguetes, enxame, artilharia, perfurante, carregada, drone de combate) com alvo aranha/chão/estrutura; explosões;
  pulso da mina; brilhos de ambiente só onde a coisa existe. **Termine os efeitos de tiro que estiverem fracos.**
  Conjunto reaproveitado de instâncias (nunca instanciar cena por tiro), teto global, rajada degrada pulando efeito.
  A cápsula ejetada a cada tiro já existe: mantenha.

### 3. Baú
- Cada baú tem inventário visível. **Itens só entram pelo maquinário** (braço, esteira, drone) — nunca pela mão.
- **Só podem sair à mão de um jeito:** botão "Enviar para a central" (tudo ou por item), que manda os itens ao estoque do núcleo.
- **Remover baú com itens pede confirmação** ("Este baú tem N itens. Remover e perder?" — ou envie à central antes, se for simples
  oferecer as duas opções). Vale para baú, baú grande, silo e baú de estoque.
- Salvar/carregar, filtro e copiar/colar que já existem continuam funcionando. Testes.

### 4. Antisserrilhado leve, PC e celular
Ligue um antisserrilhado leve nos dois (ex.: MSAA 2× ou FXAA; escolha o que o renderizador Mobile suporta melhor) e deixe
uma opção nas Configurações (Desligado/Leve/Alto, padrão Leve). Diga o que escolheu e por quê.

### 5. Jazidas cansam
Jazidas não esgotam, mas cada uma conta o quanto já foi extraído: depois de **muito tempo** de extração a frequência cai
**para a metade**; depois de **muito mais tempo**, a produção cai **75%** (fica em 25%). Escolha limiares em quantidade extraída
que levem horas de jogo normal (anote os números) e guarde no save. Mostre o estado no painel da broca ("rica", "cansada",
"exausta"). A broca de núcleo continua com a regra dela. Testes.

### 6. Aranha anda de lado
A aranha está boa, mas **a animação mostra ela andando de lado e não de frente**. Ache se é a orientação do corpo
(`jogo/inimigos/aranha.gd`, `marcha_aranha.gd`) ou o eixo do modelo (`arte/estudos/conv_antigos.py`) e corrija para ela
andar de frente, com as pernas batendo certo (os testes de `test_aranha` continuam passando).

### 7. Som
Refaça os efeitos sonoros para ficarem bons: tiros por arma, impactos, explosões, construir/remover, clique de interface,
máquinas trabalhando (fornalha, montadora, broca), esteira, trem, clima (chuva, trovão, vento forte), aranhas, alerta.
Gere por síntese própria (sem baixar sons de terceiros), WAV 44,1 kHz, volumes equilibrados entre si, sons de máquina
por distância e com limite de vozes simultâneas. Ligue tudo ao `jogo/nucleo/som.gd` e aos eventos. Volume geral/efeitos/ambiente nas Configurações.

### 8. Menu principal
Tire a imagem do jogo do fundo do menu principal e coloque **formas abstratas se mexendo** (geométricas, lentas, cores da UI),
leve no celular. É provisório.

## Testes (obrigatório antes de cada commit)
- `jogo/ferramentas/testar.sh` com **0 falhas**. Escreva teste novo para cada regra (baú, jazidas, aranha, menu).
- Todos os scripts compilam; a demo roda sem janela sem erro de script (`godot --headless --path jogo --quit-after 300 -- modo demo`).
- Se precisar mudar um teste antigo, diga qual e por quê no relatório. Não aumente limites para fazer passar.

## Release no fim
1. Suba a versão do jogo (`jogo/project.godot` e onde mais a versão aparecer) para a próxima minor.
2. Exporte com os presets já existentes em `jogo/export_presets.cfg` (APK e o que mais estiver lá). Se faltarem os templates de
   exportação, instale os oficiais da versão 4.7.2. Não crie chave de assinatura nova se já houver uma configurada; se não houver,
   use uma de depuração com CN=Sapyst.
3. `gh release create vX.Y.0` com os arquivos exportados e notas curtas em português (o que mudou), revisadas com o mesmo grep de privacidade.

## Relatório final (em `docs/RELATORIO_ANTIGRAVITY_4.md`, e commitado)
O que entrou por tarefa, decisões tomadas, números escolhidos (jazidas, AA), testes alterados, total de verificações,
link do release, e o que não conseguiu conferir (por exemplo, aparência e som só sem janela).
