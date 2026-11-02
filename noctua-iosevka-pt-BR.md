# Noctua Iosevka

*[English version](noctua-iosevka-en.md)*

Fonte **monoespaçada** própria, para terminais, editores e código. É uma build customizada da
[Iosevka](https://github.com/be5invis/Iosevka) — não um fork: nenhum desenho foi redesenhado, o que
existe é uma seleção deliberada entre as variantes que a Iosevka já oferece, mais uma escada de
larguras remapeada.

O lugar das fontes é [`noctua-iosevka/`](noctua-iosevka/), mas o git não as guarda: elas vêm dos
zips da release (§3). O site de espécime mostra a família:
<https://noctua-world.github.io/noctua-fonts/pt-BR/>, em inglês em
<https://noctua-world.github.io/noctua-fonts/>.

---

## 1. Duas famílias

| família | onde usar | pastas |
|---|---|---|
| **Noctua Iosevka** | editores e apps que não precisam de ícones | `TTF/`, `WOFF2/` |
| **NoctuaIosevka Nerd Font Mono** | uso diário em terminais — traz todos os ícones do [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) embutidos | `TTF-nerdfonts/`, `WOFF2-nerdfonts/` |

Os nomes são distintos de propósito: as duas **coexistem instaladas** sem conflito. Cada pasta tem
**135 arquivos** = 9 pesos × 5 larguras × 3 inclinações.

> ⚠️ A string que vai na configuração de terminais e editores é
> **`NoctuaIosevka Nerd Font Mono`**, caractere por caractere. Confirme com
> `fc-match "NoctuaIosevka Nerd Font Mono"` — busca por nome falha em silêncio, entregando outra
> fonte sem nenhum erro.

---

## 2. O que a distingue

<details open>
<summary><b>Largura normal de 600/1000</b> — a decisão de maior impacto</summary>

A Iosevka padrão é notoriamente estreita (meia-em), o que reduz a distinguibilidade entre glifos. A
"Normal" daqui usa avanço **0,6 em**, o mesmo da JetBrains Mono.

As cinco larguras (456, 548, **600**, 658, 720) foram escolhidas para casar honestamente com as
classes de largura do CSS/OpenType uma vez que 600 = 100%:

| largura | shape | classe CSS |
|---|---|---|
| Condensed | 456 | `condensed` |
| SemiCondensed | 548 | `semi-condensed` |
| **Normal** | **600** | `normal` |
| SemiExtended | 658 | `semi-expanded` |
| Extended | 720 | `expanded` |

</details>

<details>
<summary><b>Variantes de glifo</b> — ambiguidades atacadas por forma, não por contexto</summary>

| ambiguidade clássica | como é resolvida |
|---|---|
| `0` `O` `o` | zero pontilhado oval — sem colidir com `Ø`/`∅` |
| `i` `l` `1` `I` | "1" com serifas de topo e base, "l" serifado com cauda, "I" serifado |
| `Z` `2` `7` | "Z" com crossbar horizontal |
| `a` `o` `α` | "a" de dois andares |
| `rn` `m` | "m" com cauda |
| `Q` `O` `0` | "Q" com cauda cruzada |

As variantes `motion-serifed`, espalhadas por maiúsculas e minúsculas, dão à família uma identidade
**semi-serifada** consistente, com pontos de ancoragem que ajudam o reconhecimento periférico.

</details>

<details>
<summary><b>Três decisões de build que não são acidentais</b></summary>

**`spacing = "term"`** estreita os símbolos para a célula do terminal **mantendo** as ligaduras no
arquivo como recurso opcional (ligáveis/desligáveis por aplicativo via OpenType). A alternativa
`fixed` removeria ligaduras e até codepoints inteiros na compilação — uma opção a menos, gravada em
pedra.

**`noCvSs = false`** exporta as features `cv##`/`ss##`, permitindo trocar variantes de glifo em tempo
de execução em qualquer editor com suporte a OpenType — incluindo o stylistic set `ss14`, que veste
as formas da JetBrains Mono sob demanda.

**`exportGlyphNames = true`** preserva os nomes dos glifos no arquivo, requisito de compatibilidade
com o patcher do Nerd Fonts (e com recursos de terminais como o Kitty).

</details>

<details>
<summary><b>Cobertura</b> — pesos, larguras e inclinações</summary>

Nenhuma seção `weights` ou `slopes` é declarada no plano de build porque a seleção desejada coincide
com o padrão da Iosevka: **todos os nove pesos** (100–900) e **as três inclinações** (Upright,
Italic, Oblique). Só `widths` foi declarada, porque a escada foi remapeada.

O itálico não é só o romano inclinado — esse é o oblique. Os dois pendem 9°, e o itálico desenha
formas próprias onde faz diferença: 466 dos 7.580 pontos de código diferem, entre eles `C c e i t`
com as formas acentuadas e `ß æ œ ſ` no latim, `ε ι τ ϲ` no grego e a maior parte das minúsculas do
cirílico (medido em 2026-11-01, comparando os contornos decompostos dos estilos Italic e Oblique). O
resto é compartilhado. As duas existem separadamente.

</details>

---

## 3. Instalar

Um clone deste repositório não traz nenhuma destas fontes. Elas são assets da release
[`v1.0.0`](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0), em zips descritos
por [`font-archives.json`](font-archives.json), e o git guarda no lugar delas o
[`SHA256SUMS`](SHA256SUMS): um SHA-256 por fonte. Vinte dos 23 zips trazem a Noctua Iosevka, um por
família, formato e largura. Cada um tem as 27 faces da sua largura (9 pesos × 3 inclinações) e os
arquivos de licença da §6.

| zip | conteúdo | download (cada zip) |
|---|---|---|
| `noctua-iosevka-nerd-font-ttf-<largura>.zip` | NoctuaIosevka Nerd Font Mono em TTF, a que se instala para o terminal | cerca de 145 MiB (cerca de 410 MiB descompactado) |
| `noctua-iosevka-nerd-font-woff2-<largura>.zip` | as mesmas faces em WOFF2, para a web | cerca de 81 MiB (quase o mesmo descompactado) |
| `noctua-iosevka-ttf-<largura>.zip` | Noctua Iosevka, a família sem ícones, em TTF | cerca de 84 MiB (cerca de 285 MiB descompactado) |
| `noctua-iosevka-woff2-<largura>.zip` | as mesmas faces em WOFF2 | cerca de 44 MiB (quase o mesmo descompactado) |

`<largura>` é `normal`, `condensed`, `semicondensed`, `semiextended` ou `extended`. A Nerd Font na
largura normal:

```bash
git clone https://github.com/noctua-world/noctua-fonts.git
cd noctua-fonts
./font-archives.py fetch --archive noctua-iosevka-nerd-font-ttf-normal.zip
./font-archives.py verify --allow-missing
```

O `--archive` aceita vários nomes. Todas as larguras da Nerd Font, em TTF:

```bash
./font-archives.py fetch --archive \
  noctua-iosevka-nerd-font-ttf-normal.zip \
  noctua-iosevka-nerd-font-ttf-condensed.zip \
  noctua-iosevka-nerd-font-ttf-semicondensed.zip \
  noctua-iosevka-nerd-font-ttf-semiextended.zip \
  noctua-iosevka-nerd-font-ttf-extended.zip
```

O `font-archives.py` só precisa de Python 3.9 ou mais novo (no Windows, rode-o como
`python font-archives.py …`). O `fetch` só grava uma fonte quando o SHA-256 dela bate com o
`SHA256SUMS`, e cada zip é tudo ou nada: se um falhar, a árvore fica como estava. O
`verify --allow-missing` confere as fontes presentes e só conta as que faltam. As fontes vão para
as pastas da §1: `noctua-iosevka/TTF-nerdfonts/`, `noctua-iosevka/TTF/`,
`noctua-iosevka/WOFF2-nerdfonts/` e `noctua-iosevka/WOFF2/`.

Sem clone, baixe um zip da release, por exemplo
<https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/noctua-iosevka-nerd-font-ttf-normal.zip>.
Os caminhos dentro dele começam na raiz do repositório: ele se descompacta em
`noctua-iosevka/TTF-nerdfonts/`, com os arquivos de licença em `noctua-iosevka/licenses/`. Rode os
comandos abaixo da pasta em que você o descompactou.

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

Por usuário, sem root:

```bash
mkdir -p ~/.local/share/fonts/NoctuaIosevka
cp noctua-iosevka/TTF-nerdfonts/*.ttf ~/.local/share/fonts/NoctuaIosevka/
fc-cache -f
```

Para o sistema inteiro, use `/usr/local/share/fonts/` (requer root). Para também ter a família sem
ícones, baixe os zips `noctua-iosevka-ttf-<largura>.zip` dela e repita com `TTF/` numa pasta própria
— os nomes são distintos e não conflitam.

Confirme o que ficou disponível:

```bash
fc-list : family | grep -i noctua | sort -u
fc-match "NoctuaIosevka Nerd Font Mono"
```

**Em distribuições declarativas** (NixOS, Guix), não copie para o `$HOME`: deixe o gerenciador de
pacotes instalar as fontes. No NixOS, um pacote local feito a partir dos zips da release, com
`fonts.packages`, é o caminho. Instalar por cópia em `~/.local/share/fonts` também funciona, mas
fica fora da configuração do sistema, então outra máquina montada a partir dessa configuração não
terá as fontes.

</details>

<details>
<summary><b>macOS</b></summary>

Copie os `.ttf` de `noctua-iosevka/TTF-nerdfonts/` para `~/Library/Fonts/` (por usuário) ou
instale-os pelo Font Book.

</details>

<details>
<summary><b>Windows</b></summary>

Selecione todos os `.ttf` de `noctua-iosevka\TTF-nerdfonts\`, clique com o botão direito e escolha
"Instalar" (ou "Instalar para todos os usuários").

</details>

<details>
<summary><b>Web</b></summary>

Use os `.woff2` dos zips WOFF2, que vão para `WOFF2/` e `WOFF2-nerdfonts/`. Ver
[Converter TTF para WOFF2](convert-ttf-to-woff2-pt-BR.md) para o `@font-face` e para regerar os
arquivos.

⚠️ Não declare os 135 arquivos numa página — só os pesos/estilos que a página realmente usa.

</details>

> **Reinicie completamente o aplicativo.** Muitos programas descobrem fontes apenas na inicialização
> do *processo* — e apps em modo instância única continuam vivos com todas as janelas fechadas. Se a
> fonte não aparece, confirme que o processo morreu (`pgrep <app>`) antes de suspeitar de outra coisa.

> **Se o seu ambiente gerencia fontes centralmente, use o mecanismo dele.** Ambientes que controlam a
> fonte do sistema por ferramenta própria costumam injetar configuração que sobrescreve a do usuário,
> às vezes com precedência contraintuitiva — no Ghostty, por exemplo, arquivos incluídos via
> `config-file` são processados *ao final*, vencendo qualquer chave do seu próprio config,
> independentemente da ordem das linhas.

---

## 4. Testes de aceitação

**Tipográfico** — em corpo pequeno e nas três inclinações, cada caractere destes grupos deve ser
inconfundível:

```
il1I|   0O8B   5SZ2   3 5 S   g q 9
```

**Ícones** — num terminal usando a fonte, cada símbolo deve renderizar e ocupar exatamente **uma**
célula:

```bash
printf '  \n'
```

**Itálico** — confirme as formas próprias dele, distintas do oblique: `c e i t` no latim, a maior
parte das minúsculas do cirílico. Comentários de código são o teste natural.

---

## 5. Reconstruir do zero

<details>
<summary><b>Guia completo de reconstrução</b> — build da Iosevka + patch Nerd Fonts + re-hinting +
WOFF2 + correção SemiExtended</summary>

O pipeline:

```
private-build-plans.toml
        │
        ▼
  build da Iosevka  ──►  TTF (hintada, pura)  ──►  WOFF2 (fontTools)
        │
        └──►  TTF-Unhinted
                    │
                    ▼
          patch Nerd Fonts (Docker)
                    │
                    ▼
              ttfautohint
                    │
                    ▼
         WOFF2 (woff2_compress)
                    │
                    ▼
     correção dos nomes SemiExtended
                    │
                    ▼
              fontes finais
```

A lógica central: o patch roda sobre a saída **sem hinting** e o `ttfautohint` roda **depois** —
resultando na mesma qualidade de renderização de uma build oficial, com os ícones dentro.

### Passo 1 — Pré-requisitos

**Node.js** 18 ou mais novo (com **npm**), **git**, **ttfautohint** e **Docker** compilam as fontes;
o **woff2_compress** e o **Python 3.11** ou mais novo com **fontTools** e **brotli** geram os WOFF2
e corrigem os nomes (Passos 8 a 10); o `fc-query`, do **fontconfig**, confere os arquivos nos
Passos 4 e 7. O plano de build fixa o ttfautohint em **1.8.4**, a release mais recente dele, nas
duas passadas de hinting: `ttfautohint --version` tem de imprimir `ttfautohint 1.8.4`. O plano não
fixa versão do Node.js; a Iosevka v34.7.0 pede 18.0.0 ou mais novo.

**Arch.** O ttfautohint vem do AUR, e o pacman aborta a transação INTEIRA se qualquer pacote da
lista não existir, então mantenha os dois comandos separados:

```bash
sudo pacman -S --needed nodejs npm git docker woff2
yay -S ttfautohint
```

**Debian / Ubuntu:**

```bash
sudo apt install nodejs npm git ttfautohint docker.io woff2 python3-venv
```

**Fedora:**

```bash
sudo dnf install nodejs npm git ttfautohint docker woff2-tools
```

**macOS (Homebrew):**

```bash
brew install node git ttfautohint woff2 fontconfig python
```

**NixOS / Nix**, um shell efêmero com as ferramentas do build:

```bash
nix-shell -p nodejs git ttfautohint docker woff2
```

Confira o `node --version` antes de compilar: o Ubuntu 22.04 traz o Node.js 12, velho demais para
este build, então lá instale o 18 ou mais novo por outro caminho (NodeSource ou nvm, por exemplo).
O Debian 12 e o Ubuntu 24.04 trazem o 18.

O **Docker** é usado só para o patch do Nerd Fonts: a imagem `nerdfonts/patcher` embute o FontForge e
o `font-patcher`, evitando instalá-los no sistema.

```bash
sudo systemctl enable --now docker.service
sudo usermod -aG docker "$USER"
```

A mudança de grupo vale a partir do próximo login. No NixOS isso é declarativo:
`virtualisation.docker.enable = true;` e o usuário no grupo `docker`. No macOS, o Docker Desktop
substitui os dois comandos: instale-o e abra-o uma vez.

**Python**, para os Passos 8 a 10: instale o fontTools e o brotli num ambiente virtual na raiz do
seu clone deste repositório (o git ignora `.venv/`). Um `pip install` solto falha no Python do
sistema no Debian, no Ubuntu e no Arch, e no do Homebrew, que o marcam como gerenciado externamente
(PEP 668); [Converter TTF para WOFF2](convert-ttf-to-woff2-pt-BR.md) tem os detalhes, Windows
incluído. O `python3` que cria o ambiente tem de ser 3.11 ou mais novo, porque os testes que o
`./check.py` roda no Passo 10 precisam dele: um mais antigo, como o 3.10 do Ubuntu 22.04 ou o 3.9
das ferramentas de linha de comando do macOS, roda as ferramentas, mas não os testes.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

A última linha põe o `python3` e o `fonttools` do ambiente no `PATH` deste shell; rode-a de novo em
cada shell novo. No NixOS,
`nix-shell -p woff2 'python3.withPackages(ps: [ps.fonttools ps.brotli])'` abre um shell com o
`woff2_compress`, o fontTools e o brotli no lugar disso, para os Passos 8 a 10.

### Passo 2 — O plano de build

Todo o desenho vive num único arquivo declarativo:
[`noctua-iosevka/private-build-plans.toml`](noctua-iosevka/private-build-plans.toml). É a fonte da
verdade do projeto. O cabeçalho dele, em comentários TOML, fixa as ferramentas com que as fontes
se reconstroem: a Iosevka v34.7.0 (commit `6828cb0bd569992bb19565a5e448540de3b50541`), a imagem
do patcher do Nerd Fonts `nerdfonts/patcher:4.26.0` pelo digest e o ttfautohint 1.8.4. Mudar
qualquer uma dessas versões fixadas significa reconstruir todas as faces: as 135 puras e as 135
Nerd Font, em TTF e em WOFF2.

> **O nome do arquivo não é negociável.** O build da Iosevka procura exclusivamente por
> `private-build-plans.toml` na **raiz do repositório clonado**. Nenhum outro nome ou local funciona.
> Para manter uma cópia canônica com nome próprio, use um symlink apontando dela para a raiz.

### Passo 3 — Clonar e fixar a versão da Iosevka

O TOML sozinho não garante reprodutibilidade: nomes de variantes mudam entre versões. A receita
completa é **TOML + versão exata do repositório**, e o cabeçalho do plano a registra: tag
`v34.7.0`, commit `6828cb0bd569992bb19565a5e448540de3b50541`.

Clone a Iosevka fora deste repositório, ao lado dele por exemplo: rode os comandos abaixo da pasta
onde está a sua `noctua-fonts/`, e a `iosevka/` fica ao lado dela. Os Passos 5 e 8 chamam esse
clone de `/caminho/para/iosevka`.

```bash
git clone --depth 1 --branch v34.7.0 https://github.com/be5invis/Iosevka.git iosevka
cd iosevka
git rev-parse HEAD
```

A última linha tem de imprimir `6828cb0bd569992bb19565a5e448540de3b50541`: uma tag pode ser movida,
um commit não. Depois, crie o link para o plano e instale as dependências do build:

```bash
ln -s /caminho/para/noctua-fonts/noctua-iosevka/private-build-plans.toml private-build-plans.toml
npm install
```

Não compile a partir da `main` nem de outra tag. Isso é trocar a versão fixada: registre a tag e o
commit novos no cabeçalho do plano e no `EXPECTED_PINS` de
[`tests/test_licences.py`](tests/test_licences.py), reconstrua todas as faces e atualize lá as
impressões digitais do Material Design se as faces novas desenharem os ícones de outro jeito
(Passo 7).

### Passo 4 — Compilar

Um comando gera as **duas** saídas: o alvo `ttf::` produz as instâncias sem hinting como estágio
intermediário e aplica o `ttfautohint` sobre elas.

```bash
npm run build -- --jCmd=4 ttf::NoctuaIosevka
```

> ⚠️ **Sobre o `--jCmd=N`, leia antes de rodar.** O build paraleliza usando todos os threads da CPU
> por padrão, e o pico de RAM escala quase linearmente com os jobs simultâneos. Em máquinas com
> memória limitada, o padrão pode **travar o sistema**. Comece conservador (`--jCmd=2`), acompanhe o
> consumo e suba só se houver folga; `--jCmd=1` é o piso (build serial). 135 instâncias demoram em
> qualquer configuração — trate como tarefa de deixar rodando.

**O build é interrompível sem risco.** O sistema de build mantém um journal com grafo de
dependências: uma tarefa só é registrada como concluída depois de terminar de verdade. Ctrl-C e
rodar o mesmo comando de novo retoma de onde parou. No pior caso, trabalho em voo é refeito.

Saídas em `dist/NoctuaIosevka/TTF/` (hintada, pura) e `dist/NoctuaIosevka/TTF-Unhinted/`
(matéria-prima do patch). Valide antes de prosseguir — silêncio = sucesso:

```bash
for f in dist/NoctuaIosevka/TTF/*.ttf dist/NoctuaIosevka/TTF-Unhinted/*.ttf; do
  fc-query "$f" >/dev/null || echo "CORROMPIDO: $f"
done
```

### Passo 5 — Patch do Nerd Fonts

**Por que a saída unhinted:** o `font-patcher` roda sobre o FontForge, e essa ida-e-volta pode
degradar ou descartar o hinting TrueType. Patchear a versão sem hinting e rodar o `ttfautohint`
*depois* — a mesma ferramenta que o build oficial usa — devolve hinting equivalente ao de uma build
oficial. Nada se perde.

**Por que um arquivo por container:** o entrypoint da imagem varre `/in` e patcheia **tudo o que
encontrar**, com paralelismo interno dimensionado pela CPU — o que pode esgotar a RAM com dezenas de
processos FontForge simultâneos. Montar um único arquivo por execução força o processamento serial:
consumo constante e previsível, ao custo de tempo (horas para 135 fontes).

> ⚠️ **Nunca** monte o diretório inteiro em `/in` e passe um nome de arquivo como argumento: o nome
> vira argumento extra de *todas* as invocações internas e todas falham.

**Por que a imagem vai com tag e digest:** `nerdfonts/patcher` sem tag é a `latest`, um patcher mais
novo (4.27.3 em 2026-11-01) que carimba Nerd Fonts 3.5.1 e não reproduz estas faces. A tag `4.26.0`
já foi republicada uma vez, então o plano fixa também o digest dela; com um digest no nome, o
Docker baixa pelo digest. Essa imagem carimba `Nerd Fonts 3.4.0`, como as faces distribuídas. Ela
não é o mesmo build que as patcheou: esse foi o primeiro build da `4.26.0`, que não pode mais ser
baixado. O cabeçalho do plano diz como ela foi comparada com as faces distribuídas. Patchear uma
face de cada largura reproduz os ícones do Material Design de todas as 135, e duas faces, com o
hinting refeito como no Passo 6, saíram com todas as tabelas idênticas, menos `head` e `name`; esse
teste patcheou o TTF hintado, não o `TTF-Unhinted` como abaixo, e rodou a variante `linux/amd64`
da imagem. O digest aponta um índice de várias plataformas, então num host arm64 (Apple Silicon,
Linux em ARM) o Docker baixa a variante `arm64`, que ninguém comparou. Lá, acrescentar
`--platform linux/amd64` ao `docker run` roda a que foi comparada, se o Docker conseguir emular
amd64 (o Docker Desktop consegue).

O loop é retomável — cada fonte concluída ganha um carimbo em `.done/`. Ele roda em
`dist/NoctuaIosevka/` do clone da Iosevka, a pasta onde está `TTF-Unhinted/`, e os Passos 6 e 7
também:

```bash
cd /caminho/para/iosevka/dist/NoctuaIosevka
mkdir -p patched final .done

for f in TTF-Unhinted/*.ttf; do
  b="$(basename "$f")"
  [ -e ".done/$b" ] && continue
  docker run --rm -u "$(id -u):$(id -g)" \
    -v "$PWD/$f":"/in/$b":ro \
    -v "$PWD/patched":/out \
    nerdfonts/patcher:4.26.0@sha256:d18c1bd44f4577bf359f5cc0b61767bbda2658c6680ff9255cd770e630527efb \
    --mono --complete \
  && touch ".done/$b"
done
```

O papel de cada peça: `--mono` força os ícones a ocuparem exatamente uma célula de terminal (sem
isso, glifos de largura dupla são cortados em vários terminais); `--complete` injeta todos os
conjuntos de ícones; `-u` garante que a saída pertença ao seu usuário, não ao root; `:ro` monta a
entrada como somente-leitura.

**Mensagens esperadas que não são erros:** o aviso `Internal Error: Your version of iconv does not
support the "Mac Roman" encoding` é ruído conhecido das builds do FontForge da imagem e não afeta
fontes modernas. Um eventual warning sobre a versão do FontForge "produzir fontes inutilizáveis em
alguns casos" é coberto pela validação do Passo 7 — deixe o problema provar que existe antes de
reagir a ele.

### Passo 6 — Re-hinting

Devolve às fontes patcheadas o hinting que a passagem pelo FontForge descartou. Rápido (segundos por
arquivo):

```bash
for f in patched/*.ttf; do
  ttfautohint --no-info "$f" "final/$(basename "$f")" || echo "FALHOU: $f"
done
```

O `--no-info` deixa a nota do próprio ttfautohint fora da string de versão (name ID 5), que então
fica `Version 34.7.0;Nerd Fonts 3.4.0`, como nas faces distribuídas.

### Passo 7 — Validar as fontes patcheadas

```bash
for f in final/*.ttf; do
  fc-query "$f" >/dev/null || echo "CORROMPIDO: $f"
done
```

Silêncio total = 135 arquivos estruturalmente íntegros. Se algum falhar (raro, ligado a versões
problemáticas do FontForge na imagem), apague em `.done/` o carimbo do arquivo de que ele veio e
rode de novo os Passos 5 a 7: o loop refaz só esse arquivo. Mantenha a imagem fixada. As tags da
`nerdfonts/patcher` no Docker Hub são a versão do próprio font-patcher (4.x), nunca a versão do
Nerd Fonts que a imagem carimba, e outras imagens geram ícones diferentes: a 4.25.0 desenha 132
ícones do Material Design de outro jeito. Passar para outra imagem, por exemplo
`nerdfonts/patcher:4.27.3`, é trocar a versão fixada: registre a tag, o digest e a versão do Nerd
Fonts que ela carimba no cabeçalho do plano e no `EXPECTED_PINS` de
[`tests/test_licences.py`](tests/test_licences.py), reconstrua todas as faces (Passo 2) e atualize
as impressões digitais do Material Design nesse arquivo: o `PINNED_PATCHER_MDI`, e o
`MDI_ICON_COUNT` se a contagem mudar.

### Passo 8 — Copiar para o repositório e gerar os WOFF2

O resto roda na raiz do seu clone deste repositório, no ambiente virtual do Passo 1: as duas
primeiras linhas abaixo cuidam disso. No NixOS, rode o bloco no shell do Nix do Passo 1, sem a
linha `. .venv/bin/activate`. As quatro pastas da Noctua Iosevka têm de começar vazias: o Passo 9
nunca sobrescreve um arquivo, então uma face SemiExtended mais antiga o faria parar. Um clone novo
não tem nenhuma delas; num clone que as baixou, tire-as do repositório antes. Copie as faces puras
e as patcheadas para o repositório:

```bash
cd /caminho/para/noctua-fonts
. .venv/bin/activate
mkdir -p noctua-iosevka/TTF noctua-iosevka/TTF-nerdfonts
cp /caminho/para/iosevka/dist/NoctuaIosevka/TTF/*.ttf noctua-iosevka/TTF/
cp /caminho/para/iosevka/dist/NoctuaIosevka/final/*.ttf noctua-iosevka/TTF-nerdfonts/
```

Depois gere os WOFF2 de cada pasta com a ferramenta que gravou os deste repositório;
[Converter TTF para WOFF2](convert-ttf-to-woff2-pt-BR.md#os-arquivos-woff2-deste-repositório) diz
qual gravou quais, e com quais versões. Aqui as versões importam menos que a ferramenta: um TTF
reconstruído já difere do distribuído, então o WOFF2 dele não tem como bater com o WOFF2
distribuído, seja qual for a versão. Para usar mesmo assim as versões que gravaram os arquivos
distribuídos, instale `fonttools==4.61.1 brotli==1.2.0` no ambiente do Passo 1.

`noctua-iosevka/WOFF2/` vem de `TTF/` pelo fontTools, que mantém a flag `OVERLAP_SIMPLE` que os
TTFs da Iosevka marcam em todo glifo com contornos:

```bash
mkdir -p noctua-iosevka/WOFF2
find noctua-iosevka/TTF -maxdepth 1 -name '*.ttf' -print0 \
  | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" sh -c \
      'fonttools ttLib.woff2 compress -o "noctua-iosevka/WOFF2/$(basename "$1" .ttf).woff2" "$1"' sh
```

`noctua-iosevka/WOFF2-nerdfonts/` vem de `TTF-nerdfonts/` pelo `woff2_compress` 1.0.2, que grava ao
lado da entrada, daí o `mv`:

```bash
mkdir -p noctua-iosevka/WOFF2-nerdfonts
printf '%s\0' noctua-iosevka/TTF-nerdfonts/*.ttf \
  | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" woff2_compress
mv noctua-iosevka/TTF-nerdfonts/*.woff2 noctua-iosevka/WOFF2-nerdfonts/
```

Cada pasta tem agora 135 arquivos. Os 27 WOFF2 SemiExtended de `WOFF2-nerdfonts/` são só a entrada
do Passo 9, que os grava de novo a partir dos TTFs corrigidos.

### Passo 9 — Corrigir as faces SemiExtended

O patcher lê errado a largura SemiExtended (a Iosevka a escreve "Semi-Extended"): cola "Semi" e o
peso na família e mantém "Extended" como estilo. Cada peso SemiExtended vai então parar numa
família própria, como `NoctuaIosevkaBoldSemi Nerd Font Mono`, estilo `Extended`, e pedir
`NoctuaIosevka Nerd Font Mono` na largura semi-expanded entrega em silêncio a largura mais próxima.
No peso Bold ele também zera os bits de negrito (bit 5 do `fsSelection` da OS/2, bit 0 do
`macStyle` da `head`) que as faces Bold de todas as outras larguras têm.
O [`fix-nerd-semiextended-names.py`](fix-nerd-semiextended-names.py) conserta essas 27 faces, em TTF
e em WOFF2: 54 arquivos. Veja antes o que ele faria; o `--dry-run` não grava nada:

```bash
./fix-nerd-semiextended-names.py --dry-run noctua-iosevka/TTF-nerdfonts noctua-iosevka/WOFF2-nerdfonts
```

Ele tem de listar 54 arquivos como `would fix` e os outros 216 como `skipped`. Depois, a execução
de verdade:

```bash
./fix-nerd-semiextended-names.py noctua-iosevka/TTF-nerdfonts noctua-iosevka/WOFF2-nerdfonts
```

No Windows, rode-o como `python fix-nerd-semiextended-names.py …`. Ele reescreve os name IDs 1, 2,
3, 4, 6, 16 e 17 na convenção que o patcher usou para as outras larguras (família
`NoctuaIosevka Nerd Font Mono`, estilo `SemiExtended Bold` e assim por diante), liga os bits de
negrito exatamente no peso Bold e dá a cada arquivo o padrão de nome dos irmãos,
`NoctuaIosevkaNerdFontMono-SemiExtended[Peso][Inclinação]`. Num TTF, todas as outras tabelas são
copiadas byte a byte. Ele trata os TTFs primeiro, qualquer que seja a ordem dos argumentos, e grava
de novo cada WOFF2 SemiExtended a partir do seu TTF corrigido, para o par continuar idêntico em
conteúdo. Um TTF leva segundos, um WOFF2 de um a dois minutos: a execução inteira leva perto de uma
hora.

Ele recusa, e deixa intocado, o que não consegue reconhecer com certeza. Entre esses casos: uma
face semi-expanded Nerd Font Mono cujos nomes não batem nem com o padrão do patcher nem com o
corrigido, uma face cujos outros bits de estilo diferem dos das irmãs, uma face com name IDs 18,
20, 21, 22 ou 25 ou com registros de um mesmo ID que divergem entre plataformas, uma face com
assinatura DSIG, um arquivo cujo tipo não bate com a extensão, um link simbólico e um arquivo que
já exista com o nome novo. Um `.otf` ou `.woff` nomeado ou casado por um padrão, uma pasta sem
nenhum `.ttf` ou `.woff2` e um padrão que não casa com nada também são erros; o `--help` lista
todos os casos. Aí ele sai com status 1. As outras faces, como as das outras larguras ou fontes que
não são Nerd Fonts, ele informa como `skipped` e deixa como estão. Rodado de novo sobre faces
corrigidas, ele informa `already fixed` para cada uma e não muda nada.

### Passo 10 — Registrar as fontes novas

Uma face reconstruída tem bytes diferentes dos da distribuída, no mínimo na data gravada na tabela
`head`, então o `./font-archives.py verify` a aponta como `MISMATCH`. Para ficar com a
reconstrução, reescreva o `SHA256SUMS`. O `manifest` se recusa a rodar enquanto faltar alguma
fonte que o `SHA256SUMS` lista, então baixe antes os outros três zips:

```bash
./font-archives.py fetch --archive noctua-noto-ttf.zip noctua-noto-woff2.zip symbols-nerd-font.zip
./font-archives.py manifest
./check.py --release
```

O `manifest` informa o que acrescentou, removeu e alterou: depois de uma reconstrução com as mesmas
versões fixadas, ele tem de informar `0 added, 0 removed`, com as fontes da Noctua Iosevka entre as
alteradas. O `check.py --release` roda os testes (que conferem o name ID 5 e os ícones do Material
Design contra as versões fixadas), a checagem do site, um `verify` estrito e o
`font-archives.py list` (cada fonte em exatamente um zip).

As fontes em subconjunto do site de espécime, em `docs/`, são recortadas destas faces: refaça-as
como explica o [`site/README.md`](site/README.md). Hashes novos exigem zips novos e uma
release nova: [Manter a release](README-pt-BR.md#manter-a-release) tem o procedimento inteiro,
inclusive a tag nova, e o fim de
[Os arquivos WOFF2 deste repositório](convert-ttf-to-woff2-pt-BR.md#os-arquivos-woff2-deste-repositório)
diz por quê.

Depois, instale as faces novas a partir de `noctua-iosevka/TTF-nerdfonts/` (§3) e rode os testes de
aceitação (§4).

</details>

<details>
<summary><b>Problemas conhecidos</b></summary>

**A largura SemiExtended, corrigida aqui.** O algoritmo de renomeação do patcher fragmenta o nome
"SemiExtended", exilando essas faces em mini-famílias por peso (ex.:
`NoctuaIosevkaBoldSemi Nerd Font Mono Extended`), e zera os bits de negrito das Bold. As 27 faces
SemiExtended dos zips da release, em TTF e em WOFF2, foram consertadas em 2026-11-01 pelo
[`fix-nerd-semiextended-names.py`](fix-nerd-semiextended-names.py), nomes e bits de negrito: agora
estão na família principal com as outras quatro larguras, e
`fc-match 'NoctuaIosevka Nerd Font Mono:width=113:weight=200'` devolve
`NoctuaIosevkaNerdFontMono-SemiExtendedBold.ttf`. Uma reconstrução tem de rodar a ferramenta de
novo: Passo 9.

**Proteção contra estouro de memória.** Para builds pesados em máquinas limitadas, vale instalar um
OOM killer precoce (`earlyoom` ou `systemd-oomd`): transforma o pior caso de "sistema travado, botão
de força" em "processo morto, mensagem no log". Para containers de apetite desconhecido,
`--memory=4g --memory-swap=4g` no `docker run` impõe um teto rígido — o container morre, a máquina
sobrevive.

</details>

---

## 6. Licença

**SIL OFL 1.1**, a licença da Iosevka —
[`noctua-iosevka/licenses/OFL-Iosevka.txt`](noctua-iosevka/licenses/OFL-Iosevka.txt), © 2015-2026
Renzhi Li. **Redistribuir exige enviá-la junto** — e servir a fonte a partir de um site é
redistribuir. Todo zip da Noctua Iosevka a leva.

Duas consequências que vale conhecer:

- **A OFL da Iosevka não reserva nome algum.** A linha de copyright não traz a cláusula *"with
  Reserved Font Name"*, e é justamente isso que torna legítimo esta build customizada circular com
  nome próprio. Se o upstream tivesse reservado o nome, um derivado renomeado precisaria de permissão
  por escrito.
- **Esta build é uma Modified Version**, então vale a §5 da OFL: tem de permanecer sob a OFL e não
  pode ser relicenciada. Essa obrigação **não** alcança documentos ou sites que apenas *usam* a fonte
  — só a redistribuição do font software em si.

**As faces Nerd Font também trazem os ícones do Nerd Fonts.** O Nerd Fonts os distribui com a
licença MIT dele, guardada em
[`noctua-iosevka/licenses/LICENSE-NerdFontsSymbolsOnly.txt`](noctua-iosevka/licenses/LICENSE-NerdFontsSymbolsOnly.txt),
byte a byte a de [`symbols-nerd-font/licenses/`](symbols-nerd-font/licenses/); os zips da Nerd Font
a levam ao lado da OFL. Os conjuntos de ícones que o Nerd Fonts reúne mantêm as licenças de origem,
e nem todas são MIT: Codicons e Font Awesome estão sob CC BY 4.0, Material Design Icons sob Apache
2.0, Pomicons e Weather Icons sob a SIL Open Font License 1.1, e Font Logos sob a Unlicense. O
[`LICENSE`](LICENSE) na raiz deste repositório resume isso e aponta as listas do Nerd Fonts com
cada conjunto. O resto de cada face patcheada continua sob a OFL.

Esse `LICENSE` da raiz põe o conteúdo próprio deste repositório (as ferramentas e os testes delas, a
documentação, o plano de build e o site) sob MIT OR Apache-2.0. Ele não alcança as fontes.
