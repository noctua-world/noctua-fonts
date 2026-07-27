# Noctua Iosevka

*[English version](noctua-iosevka-en.md)*

Fonte **monoespaçada** própria, para terminais, editores e código. É uma build customizada da
[Iosevka](https://github.com/be5invis/Iosevka) — não um fork: nenhum desenho foi redesenhado, o que
existe é uma seleção deliberada entre as variantes que a Iosevka já oferece, mais uma escada de
larguras remapeada.

Arquivos em [`noctua-iosevka/`](noctua-iosevka/).

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

O itálico é **cursivo de verdade** (formas distintas), não uma versão inclinada — o oblique é que é a
inclinada. As duas existem separadamente.

</details>

---

## 3. Instalar

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

Por usuário, sem root:

```bash
mkdir -p ~/.local/share/fonts/NoctuaIosevka
cp noctua-iosevka/TTF-nerdfonts/*.ttf ~/.local/share/fonts/NoctuaIosevka/
fc-cache -f
```

Para o sistema inteiro, use `/usr/local/share/fonts/` (requer root). Para também ter a família sem
ícones, repita com `TTF/` numa pasta própria — os nomes são distintos e não conflitam.

Confirme o que ficou disponível:

```bash
fc-list : family | grep -i noctua | sort -u
fc-match "NoctuaIosevka Nerd Font Mono"
```

**Em distribuições declarativas** (NixOS, Guix), não copie para o `$HOME`: aponte o gerenciador de
pacotes para os arquivos. No NixOS, um pacote local com `fonts.packages` é o caminho — instalar por
cópia funciona, mas some no próximo rebuild que limpar o perfil.

</details>

<details>
<summary><b>macOS</b></summary>

Copie os `.ttf` para `~/Library/Fonts/` (por usuário) ou instale-os pelo Font Book.

</details>

<details>
<summary><b>Windows</b></summary>

Selecione todos os `.ttf`, clique com o botão direito e escolha "Instalar" (ou "Instalar para todos
os usuários").

</details>

<details>
<summary><b>Web</b></summary>

Use os `.woff2` já gerados em `WOFF2/` e `WOFF2-nerdfonts/`. Ver
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

**Itálico** — confirme formas cursivas, bem distintas do romano e do oblique. Comentários de código
são o teste natural.

---

## 5. Reconstruir do zero

<details>
<summary><b>Guia completo de reconstrução</b> — build da Iosevka + patch Nerd Fonts + re-hinting</summary>

O pipeline:

```
private-build-plans.toml
        │
        ▼
  build da Iosevka  ──►  TTF (hintada, pristina)
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
              fontes finais
```

A lógica central: o patch roda sobre a saída **sem hinting** e o `ttfautohint` roda **depois** —
resultando na mesma qualidade de renderização de uma build oficial, com os ícones dentro.

### Passo 1 — Pré-requisitos

**Node.js** (com **npm**), **git**, **ttfautohint** e **Docker**.

```bash
# Arch — o ttfautohint vem do AUR, e o pacman aborta a transação INTEIRA se
# qualquer pacote da lista não existir. Separe os comandos:
sudo pacman -S --needed nodejs npm git
yay -S ttfautohint

# Debian / Ubuntu
sudo apt install nodejs npm git ttfautohint docker.io

# Fedora
sudo dnf install nodejs npm git ttfautohint docker

# NixOS / Nix — shell efêmera com tudo:
nix-shell -p nodejs git ttfautohint docker
```

O **Docker** é usado só para o patch do Nerd Fonts: a imagem `nerdfonts/patcher` embute o FontForge e
o `font-patcher`, evitando instalá-los no sistema.

```bash
sudo systemctl enable --now docker.service
sudo usermod -aG docker "$USER"   # requer novo login para valer
```

No NixOS isso é declarativo: `virtualisation.docker.enable = true;` e o usuário no grupo `docker`.

### Passo 2 — O plano de build

Todo o desenho vive num único arquivo declarativo:
[`noctua-iosevka/private-build-plans.toml`](noctua-iosevka/private-build-plans.toml). É a fonte da
verdade do projeto.

> **O nome do arquivo não é negociável.** O build da Iosevka procura exclusivamente por
> `private-build-plans.toml` na **raiz do repositório clonado**. Nenhum outro nome ou local funciona.
> Para manter uma cópia canônica com nome próprio, use um symlink apontando dela para a raiz.

### Passo 3 — Clonar e pinar a Iosevka

O TOML sozinho não garante reprodutibilidade: nomes de variantes mudam entre versões. A receita
completa é **TOML + versão exata do repositório**.

```bash
git clone --depth 1 --branch <tag-da-release> https://github.com/be5invis/Iosevka.git iosevka
cd iosevka
ln -s /caminho/para/private-build-plans.toml private-build-plans.toml
npm install
```

Se precisar usar a `main`, registre o commit exato (`git rev-parse --short HEAD`) num comentário no
topo do TOML — um commit anotado ainda é reproduzível; um "main de algum dia" não é.

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

Saídas em `dist/NoctuaIosevka/TTF/` (hintada, pristina) e `dist/NoctuaIosevka/TTF-Unhinted/`
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

O loop é retomável — cada fonte concluída ganha um carimbo em `.done/`:

```bash
cd /caminho/de/trabalho   # onde está TTF-Unhinted/
mkdir -p patched final .done

for f in TTF-Unhinted/*.ttf; do
  b="$(basename "$f")"
  [ -e ".done/$b" ] && continue
  docker run --rm -u "$(id -u):$(id -g)" \
    -v "$PWD/$f":"/in/$b":ro \
    -v "$PWD/patched":/out \
    nerdfonts/patcher --mono --complete \
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

### Passo 7 — Validação final

```bash
for f in final/*.ttf; do
  fc-query "$f" >/dev/null || echo "CORROMPIDO: $f"
done
```

Silêncio total = 135 arquivos estruturalmente íntegros. Se algum falhar (raro, ligado a versões
problemáticas do FontForge na imagem), repita o Passo 5 pinando uma tag anterior — por exemplo
`nerdfonts/patcher:3.3.6` — e refaça os Passos 6 e 7.

Depois, instale (§3) e rode os testes de aceitação (§4).

</details>

<details>
<summary><b>Problemas conhecidos e inofensivos</b></summary>

**Nomes estranhos na largura SemiExtended.** O algoritmo de renomeação do patcher fragmenta o nome
"SemiExtended", exilando essas faces em mini-famílias por peso (ex.:
`NoctuaIosevkaBoldSemi Nerd Font Mono Extended`). É colateral cosmético: a família principal contém
limpas as outras quatro larguras, e a SemiExtended continua instalada e utilizável sob os nomes
tortos. Para consertar, [`rename-font-family.py`](rename-font-family.py) reescreve os nomes.

**Proteção contra estouro de memória.** Para builds pesados em máquinas limitadas, vale instalar um
OOM killer precoce (`earlyoom` ou `systemd-oomd`): transforma o pior caso de "sistema travado, botão
de força" em "processo morto, mensagem no log". Para containers de apetite desconhecido,
`--memory=4g --memory-swap=4g` no `docker run` impõe um teto rígido — o container morre, a máquina
sobrevive.

</details>
