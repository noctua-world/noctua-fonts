# Noctua Noto

*[English version](noctua-noto-en.md)*

Tipografia base para os projetos, em duas formas: as famílias **Noto puras** (variáveis, upstream do
Google Fonts) e as mesmas famílias **patchadas com Nerd Fonts 3.4.0** — os glifos de ícone embutidos
na fonte de texto, o que dispensa uma fonte de ícones separada.

Arquivos em [`noctua-noto/`](noctua-noto/). Inventário levantado em 2026-07-27; números (tamanhos,
contagens) valem para aquele snapshot.

---

## 1. Inventário — 49 TTF (+ 49 WOFF2 pares)

| grupo | qtd | variável? | quais |
|---|---|---|---|
| **Noto puras** | **18** | ✅ `wght` 100–900; **14** delas também `wdth` 62.5–100 | Sans, Sans-Italic, Serif, Serif-Italic, Display, Display-Italic, Mono, Arabic, Armenian, Devanagari, Ethiopic, Georgian, Hebrew, Thai, JP, KR, SC, Emoji |
| **Nerd Font** patchadas | **27** | ❌ estáticas | `NotoSans` e `NotoSansDisplay` (Light–Bold + itálicos), `NotoSerif` (Regular/Medium/Bold + itálicos), `NotoSansM` (Regular/Medium/Bold) |
| avulsas | **4** | ❌ estáticas | ColorEmoji (bitmap CBDT, 24 MB), Music, Math, Mongolian |

**Famílias das patchadas** — o que escrever em CSS/QML/`pubspec` (leia §5b antes de usar a Display):

| família | encontrada por busca de nome no SO? |
|---|---|
| `NotoSans Nerd Font` | ✅ se a variante Noto do Nerd Fonts estiver instalada |
| `NotoSerif Nerd Font` | ✅ idem |
| `NotoSansM Nerd Font` | ✅ idem — é a **monoespaçada** (`M` = Mono, abreviação do patcher) |
| `NotoSansDisplay Nerd Font` | ❌ **só embutindo o arquivo** — ver §5b |

<details>
<summary><b>As 18 variáveis, em detalhe</b> — eixos, instâncias, tamanhos</summary>

| arquivo | família | `wght` (min, **default**, max) | `wdth` | instâncias | TTF / WOFF2 |
|---|---|---|---|---|---|
| `NotoSans-VariableFont_wdth,wght` | Noto Sans | 100, **400**, 900 | 62.5–100 | 9 | 1996 / 868 KB |
| `NotoSans-Italic-…` | Noto Sans | 100, **400**, 900 | 62.5–100 | 9 | 2246 / 994 KB |
| `NotoSerif-VariableFont_wdth,wght` | Noto Serif | 100, **400**, 900 | 62.5–100 | 9 | 1825 / 777 KB |
| `NotoSerif-Italic-…` | Noto Serif | 100, **400**, 900 | 62.5–100 | 9 | 2372 / 1017 KB |
| `NotoSansDisplay-VariableFont_wdth,wght` | Noto Sans Display | 100, **400**, 900 | 62.5–100 | **36** | 1503 / 666 KB |
| `NotoSansDisplay-Italic-…` | Noto Sans Display | 100, **400**, 900 | 62.5–100 | **36** | 1656 / 732 KB |
| `NotoSansMono-VariableFont_wdth,wght` | Noto Sans Mono | 100, **400**, 900 | 62.5–100 | 9 | 1667 / 714 KB |
| `NotoSansArabic` / `Armenian` / `Devanagari` | … | 100, **400**, 900 | 62.5–100 | 9 | 823 / 216 / 627 KB |
| `NotoSansEthiopic` / `Georgian` / `Thai` | … | 100, **400**, 900 | 62.5–100 | 9 | 1118 / 219 / 211 KB |
| `NotoSansHebrew` | Noto Sans Hebrew | 100, **⚠️ 100**, 900 | 62.5–100 | 9 | 109 / 56 KB |
| `NotoSansJP` | Noto Sans JP | 100, **⚠️ 100**, 900 | — | 9 | 8921 / 4093 KB |
| `NotoSansKR` | Noto Sans KR | 100, **⚠️ 100**, 900 | — | 9 | 10156 / 3812 KB |
| `NotoSansSC` | Noto Sans SC | 100, **⚠️ 100**, 900 | — | 9 | **17356 / 7607 KB** |
| `NotoEmoji-VariableFont_wght` | Noto Emoji | 300, **400**, 700 | — | 5 | 1942 / 1034 KB |

As 18 têm `fvar` **+ `STAT` + named instances** (Thin, ExtraLight, Light, Regular, Medium, SemiBold,
Bold, ExtraBold, Black). Gerenciadores de fonte modernos enumeram cada instância como uma **face
separada** — ou seja, elas já se comportam como uma família estática comum:

```console
$ fc-query --format='%{style} w=%{weight} var=%{variable}\n' NotoSans-VariableFont_wdth,wght.ttf
Regular w=80 var=False
Thin w=0 var=False
…
Black w=210 var=False
 w=[0 210] var=True          ← a face variável, além das 9 nomeadas
```

</details>

[`noctua-noto/licenses/`](noctua-noto/licenses/) traz as 20 licenças: SIL OFL por família, mais a MIT
do [Nerd Fonts](symbols-nerd-font-pt-BR.md) — os 27 arquivos patchados embutem os glifos dela.
**Redistribuir exige enviá-las junto.**

---

## 2. Converter as variáveis para estáticas? **Não em massa.**

Suporte a fontes variáveis é universal desde 2017–18 (Chrome 62, Firefox 62, Safari 11, Edge 17,
FreeType 2.8.1, fontconfig 2.13, CoreText, DirectWrite, Qt 6, Flutter/Skia, HarfBuzz). Não é um risco
prático de compatibilidade. Três razões concretas para manter as variáveis como **master**:

1. **O que os projetos costumam nomear já é estático.** As 27 `*NerdFont-*` — as famílias que
   aparecem em CSS/QML — não têm `fvar`, porque o patcher do Nerd Fonts (FontForge) **rejeita
   variáveis**. A separação já está correta: as variáveis são o complemento não-patchado, para
   cobertura de scripts i18n e pesos arbitrários.
2. **O Condensed existe SÓ como eixo.** Em Sans, Serif, Mono, Arabic, Armenian, Devanagari,
   Ethiopic, Georgian, Hebrew e Thai as 9 named instances são **todas `wdth=100`** — só a `Display`
   publica Condensed/SemiCondensed/ExtraCondensed como instâncias nomeadas (por isso 36). Achatar
   cegamente joga o Condensed fora.
3. **Perde os pesos intermediários** sem ganhar nada: 9 arquivos onde havia 1.

Gere estáticas **sob demanda**, com [`instantiate-variable-font.py`](instantiate-variable-font.py),
só para os alvos que exigem (§3).

---

## 3. Guia por alvo

<details open>
<summary><b>Web (browser)</b> — use a variável direto</summary>

Um arquivo cobre os 9 pesos **e** o eixo Condensed. O `@font-face` **precisa** declarar as faixas,
senão o browser fica preso na instância padrão:

```css
@font-face {
  font-family: "Noto Sans";
  src: url("NotoSans-VariableFont_wdth,wght.woff2") format("woff2-variations");
  font-weight:  100 900;      /* ⚠️ sem isto, JP/KR/SC/Hebrew renderizam Thin — §5a */
  font-stretch: 62.5% 100%;   /* só nas 14 que têm o eixo wdth */
  font-display: swap;
}
```

**CJK exige subsetting.** A `NotoSansSC` sozinha são 7,6 MB de WOFF2 — nunca carregue inteira. Fatie
por `unicode-range` com o `pyftsubset` (vem junto do `fonttools`):

```bash
pyftsubset noctua-noto/NotoSansSC-VariableFont_wght.ttf \
  --unicodes="U+4E00-9FFF" --flavor=woff2 --layout-features="*" \
  --output-file=NotoSansSC-cjk.woff2
```

</details>

<details>
<summary><b>Flutter / mobile</b> — estáticas são mais simples</summary>

Flutter **não lê WOFF2** → use TTF. Fontes variáveis funcionam (`FontVariation`), mas o
`pubspec.yaml` exige mapear `weight:` por face declarada. O caminho de menor atrito é instanciar só
os pesos usados e declarar cada arquivo:

```bash
./instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 400 500 700
```

</details>

<details>
<summary><b>Desktop</b> (toolkits nativos, webviews embutidos) — em geral, nada a fazer</summary>

Resolve por **nome**, via o gerenciador de fontes do SO (fontconfig no Linux, CoreText no macOS,
DirectWrite no Windows), que já expande as named instances das variáveis.

> ⚠️ Se o SO já provê a Noto e a variante Noto do Nerd Fonts, **não instale estes arquivos junto**:
> duplicaria as famílias e tornaria ambíguo qual arquivo a busca por nome devolve. Instale-os apenas
> onde o sistema não os tiver — ou embuta no app, o que ignora a busca do SO.

</details>

<details>
<summary><b>Re-patch com Nerd Fonts / PDF / impressão</b> — o único alvo que exige estáticas</summary>

```bash
./instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 300 400 500 600 700
nerd-font-patcher --complete noctua-noto/static/NotoSans-Bold.ttf
```

As 27 patchadas daqui vieram do **Nerd Fonts 3.4.0**; use a mesma versão para manter a cobertura de
glifos consistente. Para gerar os WOFF2 depois, ver
[Converter TTF para WOFF2](convert-ttf-to-woff2-pt-BR.md).

</details>

---

## 4. Ferramentas

Na raiz deste repositório, genéricas (servem para qualquer fonte) e documentadas em `--help`:

| script | para quê |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | variável → estáticas. Sem opções, gera as *named instances* que a própria fonte declara; `--list` mostra eixos e estilos disponíveis |
| [`rename-font-family.py`](rename-font-family.py) | alinhar o nome de família gravado nos arquivos — foi o que resolveu §5b |

---

## 5. Armadilhas

### ⚠️ a) Instância padrão = Thin em `JP`, `KR`, `SC` e `Hebrew`

Essas quatro têm `wght` **default 100**, não 400 — o `fc-query` mostra literalmente `Thin,Regular` na
primeira face. Quem renderizar a instância padrão sem fixar o eixo pega **texto capilar**, e o
browser ainda fabrica *negrito falso* em cima do Thin.

- **Web:** `font-weight: 100 900` no `@font-face` (§3).
- **Instanciando:** o `instantiate-variable-font.py` já resolve — pina o eixo e reescreve o nome a
  partir da tabela `STAT`.

É o risco **real** deste conjunto — e se resolve com uma linha, não convertendo nada.

### ✅ b) Nome de família das patchadas — alinhado em 2026-07-27, com uma ressalva

O patcher do Nerd Fonts abrevia nomes, e quem gera os arquivos costuma reescrevê-los depois. Quando a
string não bate com a que o app pede, a busca por nome cai em fallback **silencioso** — o texto
renderiza com outra fonte, sem erro nenhum.

**O que foi feito:** as 3 monoespaçadas foram renomeadas de `NotoSansMono Nerd Font` para
**`NotoSansM Nerd Font`**, que é o nome do próprio patcher — o `UniqueID` original delas já
registrava `NotoSansM Nerd Font Mono 3.4.0`. Os arquivos passaram a se chamar
`NotoSansMNerdFont-{Regular,Medium,Bold}.{ttf,woff2}`. Assim a mesma string funciona tanto embutida
quanto resolvida pelo SO. Conferido que o desenho não mudou: 14332 glifos, cmap de 13900 e todos os
avanços em 600 (uma célula).

> ⚠️ **Ressalva — `NotoSansDisplay Nerd Font` não é um nome que exista fora destes arquivos.** O
> patcher **funde a Display na família `NotoSans`** (o `UniqueID` original dela ainda registra
> `NotoSans Nerd Font Display 3.4.0`); o nome distinto foi atribuído depois. Não conte encontrá-la
> instalada — pedi-la ao SO cai na `NotoSans Nerd Font`, que é a **proporcional de texto**. Use-a
> **só embutindo** o arquivo, sempre com a Sans na cadeia de fallback:
> ```css
> font-family: "NotoSansDisplay Nerd Font", "NotoSans Nerd Font", ui-sans-serif, sans-serif;
> ```

> ⚠️ Nada disso vale para as **variáveis**: `NotoSansMono-VariableFont_wdth,wght.ttf` é a Noto Sans
> Mono *não-patchada*, família `Noto Sans Mono` — o nome upstream correto. Não renomear.

### ⚠️ c) `NotoColorEmoji-Regular.ttf` é bitmap

24 MB de CBDT/CBLC — não escala como vetor, não aceita cor via CSS e rasterizadores antigos não a
leem. Para emoji monocromático vetorial use `NotoEmoji-VariableFont_wght` (variável, `wght` 300–700).
