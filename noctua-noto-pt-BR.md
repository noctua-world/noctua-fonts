# Noctua Noto

*[English version](noctua-noto-en.md)*

Tipografia base para os projetos, em duas formas: as famílias **Noto puras** (variáveis, upstream do
Google Fonts) e as mesmas famílias **patchadas com Nerd Fonts 3.4.0** — os glifos de ícone embutidos
na fonte de texto, o que dispensa uma fonte de ícones separada.

O lugar dos arquivos é [`noctua-noto/`](noctua-noto/), mas o git não os guarda: eles vêm dos zips
da release (próxima seção). Inventário levantado em 2026-07-27 e medido de novo em 2026-11-01; os
números (tamanhos, contagens) descrevem esses arquivos.

---

## Como obter as fontes

Um clone novo não traz fonte nenhuma. Elas são assets da release
[`v1.0.0`](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0) do GitHub, em zips
descritos por [`font-archives.json`](font-archives.json), e o git guarda no lugar delas o
[`SHA256SUMS`](SHA256SUMS): um SHA-256 por fonte. Dos 23 zips, dois trazem as fontes deste
documento:

| zip | conteúdo | download |
|---|---|---|
| `noctua-noto-ttf.zip` | os 49 TTF, mais os 20 arquivos de licença de [`noctua-noto/licenses/`](noctua-noto/licenses/) | cerca de 79 MiB (150 MiB descompactado) |
| `noctua-noto-woff2.zip` | os 49 WOFF2, mais os mesmos 20 arquivos de licença | cerca de 58 MiB (quase o mesmo descompactado) |

```bash
git clone https://github.com/noctua-world/noctua-fonts.git
cd noctua-fonts
./font-archives.py fetch --archive noctua-noto-ttf.zip noctua-noto-woff2.zip
./font-archives.py verify --allow-missing
```

O `font-archives.py` só precisa de Python 3.9 ou mais novo (no Windows, rode-o como
`python font-archives.py …`). O `fetch` só grava uma fonte quando o SHA-256 dela bate com o
`SHA256SUMS`, e cada zip é tudo ou nada: se um falhar, a árvore fica como estava. Ele não baixa um
zip cujas fontes já estejam presentes e corretas. Os arquivos de licença já estão no git; o `fetch`
confere se as cópias do zip são idênticas a eles e não os grava. Sem `--archive`, ele baixa os 23
zips (Noctua Iosevka e Symbols Nerd Font também). O `verify --allow-missing` confere as fontes
presentes e só conta as que faltam.

A mesma conferência funciona só com o comando de checksum do sistema. No Linux:

```bash
sha256sum --ignore-missing -c SHA256SUMS
```

No macOS:

```bash
shasum -a 256 --ignore-missing -c SHA256SUMS
```

O `--ignore-missing` pula os arquivos que não estão na árvore, aqui as fontes dos outros 21 zips.

---

## 1. Inventário — 49 TTF (+ 49 WOFF2 correspondentes)

| grupo | qtd | variável? | quais |
|---|---|---|---|
| **Noto puras** | **18** | ✅ `wght` 100–900 em 17, 300–700 na Emoji; **14** delas também `wdth` 62.5–100 | Sans, Sans-Italic, Serif, Serif-Italic, Display, Display-Italic, Mono, Arabic, Armenian, Devanagari, Ethiopic, Georgian, Hebrew, Thai, JP, KR, SC, Emoji |
| **Nerd Font** patchadas | **27** | ❌ estáticas | `NotoSans` (Light–Bold + itálicos), `NotoSansDisplay` (Regular–Bold + itálicos), `NotoSerif` (Regular/Medium/Bold + itálicos), `NotoSansM` (Regular/Medium/Bold) |
| avulsas | **4** | ❌ estáticas | ColorEmoji (vetorial colorida, COLR v1 e SVG, 24 MiB — §5c), Music, Math, Mongolian |

**Famílias das patchadas** — o que escrever em CSS/QML/`pubspec` (leia a §5b antes):

| família | encontrada por busca de nome no SO? |
|---|---|
| `NotoSans Nerd Font` | ✅ se o pacote Noto do próprio Nerd Fonts estiver instalado |
| `NotoSerif Nerd Font` | ✅ idem |
| `NotoSansM Nerd Font` | ⚠️ o nome existe no pacote do Nerd Fonts, mas lá é outra variante, com ícones mais largos — §5b. É a **monoespaçada** (`M` = Mono, abreviação do patcher) |
| `NotoSansDisplay Nerd Font` | ❌ **só embutindo o arquivo** — §5b |

<details>
<summary><b>As 18 variáveis, em detalhe</b> — eixos, instâncias, tamanhos</summary>

| arquivo (`.ttf` / `.woff2`) | família | `wght` (min, **default**, max) | `wdth` | instâncias | TTF / WOFF2 (KiB) |
|---|---|---|---|---|---|
| `NotoSans-VariableFont_wdth,wght` | Noto Sans | 100, **400**, 900 | 62.5–100 | 9 | 1997 / 869 |
| `NotoSans-Italic-VariableFont_wdth,wght` | Noto Sans | 100, **400**, 900 | 62.5–100 | 9 | 2247 / 994 |
| `NotoSerif-VariableFont_wdth,wght` | Noto Serif | 100, **400**, 900 | 62.5–100 | 9 | 1825 / 777 |
| `NotoSerif-Italic-VariableFont_wdth,wght` | Noto Serif | 100, **400**, 900 | 62.5–100 | 9 | 2373 / 1017 |
| `NotoSansDisplay-VariableFont_wdth,wght` | Noto Sans Display | 100, **400**, 900 | 62.5–100 | **36** | 1504 / 667 |
| `NotoSansDisplay-Italic-VariableFont_wdth,wght` | Noto Sans Display | 100, **400**, 900 | 62.5–100 | **36** | 1656 / 733 |
| `NotoSansMono-VariableFont_wdth,wght` | Noto Sans Mono | 100, **400**, 900 | 62.5–100 | 9 | 1668 / 715 |
| `NotoSansArabic-VariableFont_wdth,wght` | Noto Sans Arabic | 100, **400**, 900 | 62.5–100 | 9 | 823 / 352 |
| `NotoSansArmenian-VariableFont_wdth,wght` | Noto Sans Armenian | 100, **400**, 900 | 62.5–100 | 9 | 216 / 110 |
| `NotoSansDevanagari-VariableFont_wdth,wght` | Noto Sans Devanagari | 100, **400**, 900 | 62.5–100 | 9 | 627 / 254 |
| `NotoSansEthiopic-VariableFont_wdth,wght` | Noto Sans Ethiopic | 100, **400**, 900 | 62.5–100 | 9 | 1119 / 389 |
| `NotoSansGeorgian-VariableFont_wdth,wght` | Noto Sans Georgian | 100, **400**, 900 | 62.5–100 | 9 | 219 / 122 |
| `NotoSansThai-VariableFont_wdth,wght` | Noto Sans Thai | 100, **400**, 900 | 62.5–100 | 9 | 212 / 105 |
| `NotoSansHebrew-VariableFont_wdth,wght` | Noto Sans Hebrew | 100, **⚠️ 100**, 900 | 62.5–100 | 9 | 110 / 57 |
| `NotoSansJP-VariableFont_wght` | Noto Sans JP | 100, **⚠️ 100**, 900 | — | 9 | 8921 / 4093 |
| `NotoSansKR-VariableFont_wght` | Noto Sans KR | 100, **⚠️ 100**, 900 | — | 9 | 10157 / 3813 |
| `NotoSansSC-VariableFont_wght` | Noto Sans SC | 100, **⚠️ 100**, 900 | — | 9 | **17357 / 7607** |
| `NotoEmoji-VariableFont_wght` | Noto Emoji | **300**, **400**, **700** | — | 5 | 1943 / 1034 |

As 18 têm `fvar`, uma tabela `STAT` e instâncias nomeadas (named instances). Quinze nomeiam os 9
pesos Thin, ExtraLight, Light, Regular, Medium, SemiBold, Bold, ExtraBold e Black; as duas Display nomeiam esses 9 em quatro
larguras (36); a Emoji nomeia 5, de Light a Bold. A `STAT` das duas Display não tem axis values
(§5d). Gerenciadores de fonte modernos enumeram cada instância como uma **face separada** — ou
seja, elas já se comportam como uma família estática comum:

```console
$ fc-query --format='%{style} w=%{weight} var=%{variable}\n' NotoSans-VariableFont_wdth,wght.ttf
Regular w=80 var=False
Thin w=0 var=False
…
Black w=210 var=False
 w=[0 210] var=True
```

A última linha é a própria face variável, além das 9 nomeadas.

</details>

[`noctua-noto/licenses/`](noctua-noto/licenses/) traz 20 arquivos de licença: a SIL Open Font
License 1.1 de cada uma das 19 famílias Noto, e a licença MIT com que o
[Nerd Fonts](symbols-nerd-font-pt-BR.md) distribui seus ícones (`LICENSE-NerdFontsSymbolsOnly.txt`),
para os ícones das 27 patchadas. Os conjuntos de ícones que o Nerd Fonts reúne mantêm as licenças de
origem, e nem todas são MIT; o [`LICENSE`](LICENSE) cita as que não são e aponta para a lista
completa do Nerd Fonts. **Redistribuir exige enviar
esses arquivos junto com as fontes**; os dois zips trazem os 20. A licença do próprio repositório
(MIT OR Apache-2.0) cobre os scripts e os documentos, não as fontes.

---

## 2. Converter as variáveis para estáticas? **Não em massa.**

Suporte a fontes variáveis é universal desde 2017–18 (Chrome 62, Firefox 62, Safari 11, Edge 17,
FreeType 2.8.1, fontconfig 2.13, CoreText, DirectWrite, Qt 6, Flutter/Skia, HarfBuzz). Não é um risco
prático de compatibilidade. Três razões concretas para manter as variáveis como **master**:

1. **O que os projetos costumam nomear já é estático.** As 27 `*NerdFont-*` — as famílias que
   aparecem em CSS/QML — não têm `fvar`, porque o patcher do Nerd Fonts (FontForge) não aceita
   fontes variáveis: com `NotoSansHebrew-VariableFont_wdth,wght.ttf`, a imagem fixada do patcher
   (§3) sai com status 1 e não grava nada. A separação já está correta: as variáveis são o
   complemento não-patchado, para cobertura de scripts i18n e pesos arbitrários.
2. **O Condensed existe SÓ como eixo.** Em Sans, Serif, Mono, Arabic, Armenian, Devanagari,
   Ethiopic, Georgian, Hebrew e Thai as 9 instâncias nomeadas são **todas `wdth=100`** — só a `Display`
   publica SemiCondensed/Condensed/ExtraCondensed como instâncias nomeadas (por isso 36). Achatar
   cegamente joga o Condensed fora.
3. **Perde os pesos intermediários** sem ganhar nada: 9 arquivos onde havia 1.

Gere estáticas **sob demanda**, com [`instantiate-variable-font.py`](instantiate-variable-font.py),
só para os alvos que exigem (§3).

---

## 3. Guia por alvo

<details open>
<summary><b>Web (browser)</b> — use a variável direto</summary>

Um arquivo cobre os 9 pesos **e** o eixo Condensed. Declare as faixas dos eixos no `@font-face`:

```css
@font-face {
  font-family: "Noto Sans";
  src: url("NotoSans-VariableFont_wdth,wght.woff2") format("woff2");
  font-weight: 100 900;
  font-stretch: 62.5% 100%;
  font-display: swap;
}
```

O `font-weight` é a faixa do `wght`: `100 900`, ou `300 700` na Noto Emoji (a §5a explica por que
ela importa mais em JP, KR, SC e Hebrew). O `font-stretch` só vale nas 14 que têm o eixo `wdth`. Para
um WOFF2 variável, `format("woff2")` basta.

**CJK exige fatiar.** A `NotoSansSC` sozinha são 7,4 MiB de WOFF2 (`JP` 4,0 MiB, `KR` 3,7 MiB) —
nunca carregue uma inteira. Corte-a em fatias de 400 codepoints, em ordem de codepoint, e dê a cada
fatia seu próprio `@font-face`, com um `unicode-range` que liste exatamente os codepoints que ela
contém; assim o browser só baixa as fatias com caracteres na página. O `noctua-design` usa a mesma
regra, mas antes reduz cada fonte CJK às faixas CJK, então nenhuma fatia dele traz latino. O script
abaixo fatia a fonte inteira com o fontTools (§4): salve-o como `slice-cjk.py`, fora do
repositório.

```python
# slice-cjk.py FONT FAMILY OUTDIR: 400 codepoints per slice, in codepoint order.
import os, sys
from fontTools import subset
from fontTools.ttLib import TTFont

font, family, out = sys.argv[1:]
stem = os.path.basename(font).split("-")[0]
codepoints = sorted(TTFont(font, lazy=True).getBestCmap())
os.makedirs(out, exist_ok=True)
rules = []
for n in range(0, len(codepoints), 400):
    options = subset.Options(flavor="woff2", layout_features=["*"])
    piece = subset.load_font(font, options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints[n:n + 400])
    subsetter.subset(piece)
    name = f"{stem}-{n // 400:03}.woff2"
    subset.save_font(piece, os.path.join(out, name), options)
    have = sorted(TTFont(os.path.join(out, name)).getBestCmap())  # the range, read from the file
    runs, start = [], have[0]
    for a, b in zip(have, have[1:] + [None]):
        if b != a + 1:
            runs.append(f"U+{start:X}" + (f"-{a:X}" if a > start else ""))
            start = b
    rules.append(f'@font-face {{ font-family: "{family}"; src: url("{name}") format("woff2"); '
                 f'font-weight: 100 900; font-display: swap; unicode-range: {", ".join(runs)}; }}')
with open(os.path.join(out, stem + ".css"), "w") as css:
    css.write("\n".join(rules) + "\n")
print(f"{len(rules)} slices in {out}")
```

```bash
python3 ~/slice-cjk.py noctua-noto/NotoSansSC-VariableFont_wght.ttf "Noto Sans SC" ~/noto-web/sc
```

Ele grava de `NotoSansSC-000.woff2` a `NotoSansSC-077.woff2` e o `NotoSansSC.css`, com um
`@font-face` por fatia. Cada faixa é lida de volta da fatia que descreve, então lista o que aquele
arquivo contém. As fatias continuam variáveis em `wght`, por isso toda regra declara
`font-weight: 100 900`. Medido: a SC dá 78 fatias em cerca de um minuto, a maior com 166 KiB; a JP
dá 42 e a KR, 58.

A fatia 000 traz o latino, o grego e o cirílico da fonte, e o espaço. O browser carrega a primeira
fonte do `font-family` cujo `unicode-range` inclui o espaço, seja qual for o texto (o CSS tira dela
as métricas da linha); por isso, ponha uma família latina antes da CJK. Medido no Chrome 150 com
`font-family: "Noto Sans", "Noto Sans SC"`: uma linha com seis ideogramas baixou exatamente as seis
fatias que os contêm, e o texto latino não baixou fatia nenhuma da SC. Com `"Noto Sans SC"` sozinha,
os seis ideogramas baixaram também a fatia 000; com `"Noto Sans SC", "Noto Sans"`, o texto latino
baixou a fatia 000.

</details>

<details>
<summary><b>Flutter / mobile</b> — estáticas são mais simples</summary>

Flutter **não lê WOFF2** → use TTF. Fontes variáveis funcionam (`FontVariation`), mas o
`pubspec.yaml` exige mapear `weight:` por face declarada. O caminho de menor atrito é instanciar só
os pesos usados e declarar cada arquivo:

```bash
./instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 400 500 700 --out ~/noto-static
```

Isso grava `NotoSans-Regular.ttf`, `NotoSans-Medium.ttf` e `NotoSans-Bold.ttf`. O porquê do
`--out` está na §4.

</details>

<details>
<summary><b>Desktop</b> (toolkits nativos, webviews embutidos) — em geral, nada a fazer</summary>

A resolução é por **nome**, pelo gerenciador de fontes do SO (fontconfig no Linux, CoreText no
macOS, DirectWrite no Windows), que já expande as instâncias nomeadas das variáveis.

> ⚠️ Se o SO já provê a Noto e a variante Noto do Nerd Fonts, **não instale estes arquivos junto**:
> duplicaria as famílias e tornaria ambíguo qual arquivo a busca por nome devolve. Instale-os apenas
> onde o sistema não os tiver — ou embuta no app, o que ignora a busca do SO.

</details>

<details>
<summary><b>Re-patch com Nerd Fonts / PDF / impressão</b> — o único alvo que exige estáticas</summary>

O patch roda no Docker (para instalá-lo, veja o Passo 1 da
[Noctua Iosevka](noctua-iosevka-pt-BR.md)): a imagem `nerdfonts/patcher` já traz o FontForge e o
`font-patcher`. Ela patcheia todas as fontes da pasta montada em `/in` e grava na pasta montada em
`/out`. O `-u` faz a saída ser sua, não do root; o `:ro` monta a entrada só para leitura.

```bash
./instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 300 400 500 600 700 --out ~/noto-static
mkdir -p ~/noto-patched
docker run --rm -u "$(id -u):$(id -g)" \
  -v ~/noto-static:/in:ro \
  -v ~/noto-patched:/out \
  nerdfonts/patcher:4.26.0@sha256:d18c1bd44f4577bf359f5cc0b61767bbda2658c6680ff9255cd770e630527efb \
  --complete
```

- **`--complete`** acrescenta todos os conjuntos de ícones. **`--mono`** deixa todo ícone com uma
  célula de largura: as três faces `NotoSansM` foram patchadas com ele (§5b), então acrescente-o ao
  patchear a Noto Sans Mono. A imagem patcheia as faces em paralelo: aqui, o bloco inteiro acima,
  com as cinco instâncias, levou cerca de 70 segundos.
- **A imagem é fixada pelo digest.** É a mesma fixada para as faces Nerd da Noctua Iosevka em
  [`noctua-iosevka/private-build-plans.toml`](noctua-iosevka/private-build-plans.toml), cujo
  cabeçalho explica o motivo: a tag dela já foi republicada uma vez. `nerdfonts/patcher` sem tag é o
  build mais recente (4.27.3 em 2026-11-01), que carimba uma versão posterior do Nerd Fonts.
- **Ela não reproduz as 27 faces daqui.** Carimba Nerd Fonts 3.4.0, como elas, mas elas trazem
  10.410 codepoints de ícone, exatamente o conjunto da Symbols Nerd Font deste repositório. A imagem
  acrescenta esses 10.410 e mais 109 codepoints da Área de Uso Privado (de U+E6B9 a U+F385): 10.519
  numa instância da Noto Sans ou da Noto Sans Display. Numa instância da Noto Sans Mono, acrescenta
  também os 256 padrões Braille (de U+2800 a U+28FF). Não há registro de qual build do patcher gerou
  as 27.
- **O patcher escolhe os nomes.** `NotoSans-Bold.ttf` sai como `NotoSansNerdFont-Bold.ttf`, família
  `NotoSans Nerd Font`, nome PostScript `NotoSansNF-Bold`. Uma instância da Noto Sans Mono com
  `--mono` sai como `NotoSansMNerdFontMono-Regular.ttf`, família `NotoSansM Nerd Font Mono`. As 27
  daqui foram renomeadas depois do patch (§5b).

Para gerar os WOFF2 depois, ver [Converter TTF para WOFF2](convert-ttf-to-woff2-pt-BR.md).

</details>

---

## 4. Ferramentas

Na raiz deste repositório, documentadas em `--help`. As ferramentas de fonte são genéricas: servem
para qualquer fonte.

| script | para quê |
|---|---|
| [`font-archives.py`](font-archives.py) | baixar as fontes da release (`fetch`) e conferir uma árvore contra o `SHA256SUMS` (`verify`); o `list` mostra cada zip com a quantidade e o tamanho dos seus arquivos. Só biblioteca padrão |
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | variável → estáticas. Sem opções, gera as *instâncias nomeadas* que a própria fonte declara. `--weights` e `--widths` aceitam vários valores e podem se repetir (os valores se somam); `--axis TAG=VALUE` fixa um eixo pela tag. `--list` mostra os eixos, o arquivo em que cada instância nomeada seria gravada e qual regra a nomeia (`stat`, `fvar` ou `coords`). Um valor fora da faixa de um eixo é recusado antes de qualquer gravação, nunca ajustado ao limite |
| [`rename-font-family.py`](rename-font-family.py) | alinhar o nome de família gravado nos arquivos — foi o que resolveu §5b. Em `noctua-noto/` cada `.ttf` tem o seu `.woff2` ao lado, com o mesmo nome-base: renomear o `.ttf` reconstrói e renomeia essa cópia web também, desde que os nomes da cópia batam com os da fonte. Se não baterem, o lote é recusado e nada muda |
| [`check.py`](check.py) | roda a suíte de testes, o `site/build.py --check` e o `font-archives.py verify --allow-missing`. Rode antes de cada commit |

**Python.** O `instantiate-variable-font.py`, o `rename-font-family.py`, o `pyftsubset`, o script de
fatiar da §3 e os testes do `check.py` precisam do fontTools, mais o brotli para WOFF2. Instale-os
num ambiente virtual, na raiz do repositório (o git ignora `.venv/`):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

No Linux e no macOS, com ele ativo, `./instantiate-variable-font.py`, `python3` e `pyftsubset`
passam a usá-lo. No Windows: `python -m venv .venv`, depois
`.venv\Scripts\python -m pip install fonttools brotli` e `.venv\Scripts\activate`. Um venv no
Windows tem `python`, não `python3`, então rode os scripts por ele: `python instantiate-variable-font.py …`.
Um `pip install` solto falha no Python do sistema no Debian, no Ubuntu e no Arch, e no do Homebrew:
eles o marcam como gerenciado externamente (PEP 668).
O `pipx install fonttools` (e depois `pipx inject fonttools brotli`) dá os comandos `fonttools` e
`pyftsubset`, mas os scripts daqui importam o fontTools, e o pipx não o deixa importável para eles.
No NixOS, use um shell: `nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])'`.

**Grave as fontes geradas fora das pastas de fontes.** Por padrão, o `instantiate-variable-font.py`
grava em `static/`, ao lado da entrada. O git ignora essa pasta, mas o `font-archives.py verify` (e,
portanto, o `check.py`) conta toda fonte sob `noctua-noto/`, `noctua-iosevka/` e
`symbols-nerd-font/`, `static/` inclusive, e falha com uma que o `SHA256SUMS` não lista. Os exemplos
daqui passam `--out ~/noto-static`.

---

## 5. Armadilhas

### ⚠️ a) Instância padrão = Thin em `JP`, `KR`, `SC` e `Hebrew`

Essas quatro têm `wght` **default 100**, não 400 — o `fc-query` mostra literalmente `Thin,Regular`
na primeira face, a instância padrão. Quem renderizar o arquivo sem definir o eixo `wght` recebe um
texto **finíssimo**.

- **Web:** declare `font-weight: 100 900` no `@font-face` (§3), para que o `font-weight` percorra o
  eixo inteiro. Medido no Chrome 150: mesmo sem `font-weight` na regra, o Chrome definiu o `wght` a
  partir do `font-weight` e desenhou JP e Hebrew em Regular no 400 e em Bold no 700. Outros browsers
  não foram medidos; a faixa declarada não depende disso.
- **Instanciando:** o `instantiate-variable-font.py` nomeia essas quatro pela tabela `STAT`, que
  dá nome às 9 instâncias nomeadas de cada uma: `--weights 400` dá `<Família> Regular`, com
  `usWeightClass` 400. **Mas o peso só fica fixado quando você passa `--weights`**, ou gera as
  instâncias nomeadas (sem opções de eixo). Um eixo que você não nomeia fica no default da fonte, aqui o Thin:
  `--widths 75` na Hebrew grava `NotoSansHebrew-ThinCondensed.ttf`, e `--weights 400 --widths 75`
  grava `NotoSansHebrew-Condensed.ttf`.

É o risco **real** deste conjunto. A solução é fixar o eixo onde o arquivo é usado; não é preciso
converter nada.

### ✅ b) Nome de família das patchadas — alinhado em 2026-07-27, com duas ressalvas

O patcher do Nerd Fonts abrevia nomes, e quem gera os arquivos costuma reescrevê-los depois. Quando a
string não bate com a que o app pede, a busca por nome cai em fallback **silencioso** — o texto
renderiza com outra fonte, sem erro nenhum.

**O que foi feito:** as 3 monoespaçadas foram renomeadas de `NotoSansMono Nerd Font` para
**`NotoSansM Nerd Font`**, que mantém a abreviação que o patcher usa para Noto Sans Mono. Os arquivos
passaram a se chamar `NotoSansMNerdFont-{Regular,Medium,Bold}.{ttf,woff2}`. Conferido que o desenho
não mudou: 14332 glifos, cmap de 13900 e todos os glifos, menos o `.null`, com avanço de 600
unidades (uma célula).

> ⚠️ **Ressalva — fora daqui, `NotoSansM Nerd Font` é outra variante.** Estes arquivos são a
> variante **Mono** do patcher (`--mono`, todo ícone com uma célula de largura). O ID único deles
> (name ID 3) ficou fora da renomeação e ainda diz isso: `NotoSansM Nerd Font Mono Regular 3.4.0`
> (Medium e Bold idem), exatamente o que a imagem fixada grava com `--mono`. O patcher chama essa
> variante de `NotoSansM Nerd Font Mono`. O nome `NotoSansM Nerd Font` ele dá à variante padrão,
> cujos ícones largos ocupam duas ou três células: patchear a Noto Sans Mono Regular sem `--mono` dá
> 243 glifos com avanço 1200 e 9 com 1800, e o `NotoSansMNerdFont-Regular.ttf` do próprio Nerd Fonts
> tem os mesmos números. Então o nome só designa estes arquivos de uma célula quando eles vão
> embutidos; um SO com o pacote Noto do Nerd Fonts instalado o resolve para a variante larga. Onde
> ícones de uma célula importam (um terminal, uma grade), embuta os arquivos.

> ⚠️ **Ressalva — `NotoSansDisplay Nerd Font` não é um nome que exista fora destes arquivos.** O
> patcher **funde a Display na família `NotoSans`**: a imagem fixada nomeia uma instância Regular da
> Noto Sans Display como `NotoSansNerdFont-DisplayRegular.ttf`, família tipográfica
> `NotoSans Nerd Font`, estilo `Display Regular`, e o ID único original da Regular daqui ainda
> registra `NotoSans Nerd Font Display 3.4.0`. O nome distinto foi atribuído depois, e o pacote Noto
> do próprio Nerd Fonts não tem Display. Pedi-la ao SO dá a face que o sistema usar de fallback (o
> `fc-match` devolve a mesma face que para `sans-serif`), sem erro. Use-a **só embutindo** o
> arquivo, sempre com a Sans na cadeia de fallback:
> ```css
> font-family: "NotoSansDisplay Nerd Font", "NotoSans Nerd Font", ui-sans-serif, sans-serif;
> ```

> ⚠️ Nada disso vale para as **variáveis**: `NotoSansMono-VariableFont_wdth,wght.ttf` é a Noto Sans
> Mono *não-patchada*, família `Noto Sans Mono` — o nome upstream correto. Não renomear.

### ⚠️ c) `NotoColorEmoji-Regular.ttf` só desenha pelas tabelas de cor

24 MiB (5,4 MiB em WOFF2). Os emojis são glifos vetoriais coloridos, guardados duas vezes: numa
tabela `COLR` versão 1 (3993 glifos, cores de uma paleta `CPAL`) e numa tabela OpenType-SVG (os
mesmos 3993 glifos). Os contornos `glyf` por baixo são vazios (U+1F600 tem 0 contornos), então um
renderizador que não lê nenhuma das duas tabelas não desenha nada. Para emoji monocromático vetorial
use `NotoEmoji-VariableFont_wght` (variável, `wght` 300–700).

### ⚠️ d) Noto Sans Display: a tabela `STAT` não consegue nomear instâncias

As duas Display têm uma tabela `STAT` com eixos de design, mas sem axis values, então a `STAT` não
consegue nomear uma posição. O `instantiate-variable-font.py` passa então a nomear cada instância
pelas instâncias nomeadas da própria fonte (`fvar`). Sem opções, ele grava as 36 como
`NotoSansDisplay-<Estilo>.ttf`: `NotoSansDisplay-SemiCondensedBold.ttf` e, a partir da Italic,
`NotoSansDisplay-ExtraCondensedBoldItalic.ttf`. O `fc-query` enxerga 36 faces distintas. Um arquivo
levou menos de dois minutos aqui, cerca de três com `--woff2`.

Só uma posição que seja uma das 36 recebe nome. `--weights 400 700` grava
`NotoSansDisplay-Regular.ttf` e `NotoSansDisplay-Bold.ttf`, mas `--weights 450` grava
`NotoSansDisplay-wght450.ttf`, cujos nomes internos ainda dizem `Noto Sans Display Regular`. O
`--list` mostra de antemão qual regra nomeia cada arquivo.
