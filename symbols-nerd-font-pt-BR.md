# Symbols Nerd Font

*[English version](symbols-nerd-font-en.md)*

A fonte só-ícones do [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) — **10 410 ícones e
nenhuma letra**. Ela existe para ser *fallback*: você mantém a fonte de texto que quiser, e o sistema
recorre a esta para os codepoints de ícone.

Os dois `.ttf` são o **Nerd Fonts 3.4.0** tal como foi lançado, byte a byte os do
`NerdFontsSymbolsOnly.zip` dele. Os dois `.woff2` são cópias deles para a web, com os mesmos nomes,
métricas e contornos.

O git guarda só a licença em [`symbols-nerd-font/`](symbols-nerd-font/). As fontes em si são um
asset da release, `symbols-nerd-font.zip`; a §4 mostra como obtê-las.

---

## 1. Dois arquivos, uma diferença real

| arquivo | família | avanços |
|---|---|---|
| `SymbolsNerdFont-Regular` | `Symbols Nerd Font` | **variáveis**: 849 larguras diferentes, até 2729 unidades num upm de 2048 |
| `SymbolsNerdFontMono-Regular` | `Symbols Nerd Font Mono` | **todos 2048** = exatamente um em |

Os dois têm os mesmos 10 410 ícones, nos mesmos codepoints e com os mesmos nomes de glifo. O que
muda é quanto espaço horizontal cada ícone ocupa: na `Symbols Nerd Font`, 403 ícones são mais
largos que um em. Os contornos também diferem: 10 054 dos ícones são desenhados de outro jeito nos
dois arquivos, e 9 271 deles saem maiores na Mono. O `md-account` (`U+F0004`) tem 2048 unidades de
largura nela, e 1368 na `Symbols Nerd Font`.

- **`Symbols Nerd Font`** dá a cada ícone a largura do próprio desenho, e assim os ícones mantêm as
  proporções naturais. Use-a em texto proporcional (interface, documentos, texto na web) e comece
  por ela também no terminal.
- **`Symbols Nerd Font Mono`** dá a todos os ícones a mesma largura, um em. Onde o texto é disposto
  pelas larguras de avanço, como num navegador, qualquer ícone empurra o texto seguinte pela mesma
  distância. O exemplo para a web da §4 a usa nos blocos `pre`.

**Nenhum dos dois arquivos cabe numa célula de terminal.** A célula é mais estreita que um em:
0,6 em na Noctua Iosevka (600 de 1000 unidades) e na DejaVu Sans Mono (1233 de 2048). Um ícone da
Mono tem um em de largura, cerca de 1,7 célula, e a maioria dos ícones da `Symbols Nerd Font`
também passa da largura de uma célula. O que o terminal faz com um glifo mais largo que a célula
depende do terminal. Num teste, o Alacritty 0.17.0 e o foot 1.27.0 desenharam o glifo no tamanho
natural, por cima do caractere seguinte: com a Noctua Iosevka em 28 pt, o `U+F0004` cobriu 1,7
célula vindo da Mono e 1,1 vindo da `Symbols Nerd Font`. O arquivo de fontconfig do próprio Nerd
Fonts, o `10-nerd-font-symbols.conf` do mesmo `NerdFontsSymbolsOnly.zip`, prefere a
`Symbols Nerd Font` para `monospace` e para outras 368 famílias, e não cita a Mono em lugar nenhum.
Se cada ícone tiver de ocupar exatamente uma célula, use uma fonte patchada (§2). A §5 mostra como
conferir no seu terminal.

Cada um vem em `.ttf` e num `.woff2` correspondente, para a web.

---

## 2. Quando usar isto em vez de uma fonte patchada

Há dois jeitos de ter os ícones do Nerd Fonts, e eles resolvem problemas diferentes.

| | fonte patchada (ex.: `NotoSansM Nerd Font`) | esta fonte de fallback |
|---|---|---|
| como | ícones embutidos numa cópia da fonte de texto | fonte separada, alcançada por fallback |
| tamanho do ícone | ajustado à fonte de texto: na `NotoSansM Nerd Font` cada ícone tem 600 unidades de largura, como as letras dela | o da própria fonte: até 2729 unidades num upm de 2048, um em na Mono |
| ícones acompanham o peso do texto | ❌ não — os mesmos contornos em todos os pesos | ❌ não — sempre um único Regular |
| funciona com **qualquer** fonte de texto | ❌ precisa de uma build patchada por fonte | ✅ sim |
| custo em disco | uma cópia inteira da fonte de texto por peso | 2,4 MB por arquivo (2,5 MB a Mono), uma vez |
| atualizar a fonte de texto | exige aplicar o patch de novo | independente |

A linha do peso foi medida: os arquivos Regular, Medium e Bold da `NotoSansM Nerd Font`
compartilham todos os 10 396 contornos de ícone.

Use o **fallback** quando quiser manter uma fonte de texto que não tem build patchada, ou quando não
quiser carregar uma cópia patchada de cada peso. Use uma fonte **patchada** quando os ícones
precisarem ocupar exatamente a célula da própria fonte de texto.

> ⚠️ Escolha uma única origem para os ícones. Uma fonte patchada instalada em qualquer lugar do
> sistema pode servir os ícones de outras fontes também, à frente desta. Num teste com o fontconfig
> 2.17.1 e a `NotoSansM Nerd Font` instalada ao lado dos dois arquivos desta fonte, um ícone pedido a
> `monospace`, à `DejaVu Sans Mono` ou à `Noctua Iosevka` veio da `NotoSansM Nerd Font`, mesmo com a
> regra da §4 em vigor. A §5 mostra como ver qual fonte você recebe.

---

## 3. O que tem dentro

Faixas de codepoint presentes nos dois arquivos, medidas direto do `cmap` deles. O conjunto de cada
faixa sai dos nomes de glifo (`pl-…`, `cod-…`, `md-…` e assim por diante) e das faixas do
[`font-patcher`](https://github.com/ryanoasis/nerd-fonts/blob/v3.4.0/font-patcher) 3.4.0 do Nerd
Fonts. Alguns glifos não trazem o conjunto no nome, como o `uni2630`, ou o `heart` em `U+F08D0`.

| faixa | ícones | conjunto de ícones |
|---|---|---|
| `U+23FB–23FE`, `U+2B58` | 5 | IEC Power Symbols |
| `U+2630` | 1 | Powerline Extra |
| `U+2665`, `U+26A1` | 2 | Octicons |
| `U+276C–2771` | 6 | Heavy Angle Brackets |
| `U+E000–E00A` | 11 | Pomicons |
| `U+E0A0–E0D7` | 40 | Powerline e Powerline Extra |
| `U+E200–E2A9` | 170 | Font Awesome Extension |
| `U+E300–E3E3` | 228 | Weather Icons |
| `U+E5FA–E6B8` | 191 | Seti-UI + Custom |
| `U+E700–E8EF` | 496 | Devicons |
| `U+EA60–EC1E` | 439 | Codicons (VS Code) |
| `U+ED00–EFCE` | 719 | Font Awesome, com 12 glifos de barra de progresso e de spinner em `U+EE00–EE0B` |
| `U+F000–F2FF` | 768 | Font Awesome |
| `U+F300–F381` | 130 | Font Logos |
| `U+F400–F533` | 308 | Octicons |
| `U+F0001–F1AF0` | 6 896 | Material Design Icons |

O grosso — dois terços da fonte — é Material Design Icons, no **plano 15**, a Supplementary Private
Use Area-A (`U+F0001` em diante). Qualquer coisa que trunque codepoints para 16 bits perde esses
glifos silenciosamente.

As quatro primeiras linhas são 14 símbolos Unicode comuns, fora da Private Use Area:
⏻ ⏼ ⏽ ⏾ ☰ ♥ ⚡ ❬ ❭ ❮ ❯ ❰ ❱ ⭘. O fallback só é consultado para o que falta na fonte de texto; se ela
tiver esses símbolos, é ela que os desenha. A Noctua Iosevka tem os 14; a DejaVu Sans Mono, 8.

---

## 4. Instalar

Um clone deste repositório não traz estas fontes. Elas vêm do pacote da release
`symbols-nerd-font.zip` (cerca de 5 MB), que o `font-archives.py` baixa. Na raiz do clone:

```bash
./font-archives.py fetch --archive symbols-nerd-font.zip
./font-archives.py verify --allow-missing
```

O `fetch` só grava uma fonte depois que o SHA-256 dela bate com o `SHA256SUMS` commitado.
O `verify --allow-missing` confere as fontes presentes contra esse arquivo e conta as outras como
ausentes. O script precisa de Python 3.9 ou mais novo e de nada além da biblioteca padrão; no
Windows, rode-o como `python font-archives.py`. Para conferir sem ferramenta nenhuma, no mesmo
lugar, no Linux:

```bash
sha256sum -c SHA256SUMS --ignore-missing
```

No macOS:

```bash
shasum -a 256 -c SHA256SUMS --ignore-missing
```

Sem clone, baixe o pacote direto da release:
<https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/symbols-nerd-font.zip>.
Ele se descompacta em `symbols-nerd-font/`, com as quatro fontes e a licença. Num clone, o
`./font-archives.py list` lista os 23 pacotes, e o `font-archives.json` diz o que cada um contém.

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

```bash
mkdir -p ~/.local/share/fonts/SymbolsNerdFont
cp symbols-nerd-font/*.ttf ~/.local/share/fonts/SymbolsNerdFont/
fc-cache -f
fc-match "Symbols Nerd Font"
fc-match "Symbols Nerd Font Mono"
```

As duas últimas linhas têm de imprimir `SymbolsNerdFont-Regular.ttf: "Symbols Nerd Font" "Regular"`
e `SymbolsNerdFontMono-Regular.ttf: "Symbols Nerd Font Mono" "Regular"`. Qualquer outro arquivo
quer dizer que o fontconfig não encontrou as fontes.

O fontconfig chega nesta fonte sozinho para codepoints que a sua fonte de texto não tem. Num teste
com os dois arquivos instalados e nenhuma regra, os ícones vieram da `Symbols Nerd Font`, o arquivo
que a §1 sugere. Para deixar essa escolha explícita, ou para escolher a Mono, ponha isto em
`~/.config/fontconfig/fonts.conf` (se o arquivo já existir, acrescente os dois blocos `<alias>`
dentro do `<fontconfig>` dele):

```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <alias>
    <family>monospace</family>
    <prefer><family>Symbols Nerd Font</family></prefer>
  </alias>
  <alias>
    <family>Noctua Iosevka</family>
    <accept><family>Symbols Nerd Font</family></accept>
  </alias>
</fontconfig>
```

Para a Mono, escreva `Symbols Nerd Font Mono` nos dois blocos. O primeiro bloco cobre `monospace` e
as fontes que o fontconfig já conta como monoespaçadas, entre elas a DejaVu Sans Mono. Uma fonte que
ele não conhece, como a Noctua Iosevka, precisa de um bloco próprio: com a Mono só no primeiro
bloco, a Noctua Iosevka continuou pegando os ícones da `Symbols Nerd Font`. Ponha ali o nome de
família da sua fonte de texto. A regra não tira as letras da sua fonte de texto: o
`fc-match monospace` continuou apontando a DejaVu Sans Mono.

</details>

<details>
<summary><b>macOS / Windows</b></summary>

**macOS:** copie os `.ttf` para `~/Library/Fonts/`, ou instale pelo Font Book.

**Windows:** selecione os `.ttf`, clique com o botão direito e escolha "Instalar".

Nos dois, os aplicativos geralmente fazem fallback sozinhos; terminais costumam ter uma configuração
explícita de fonte de fallback, que vale apontar para o arquivo que você escolheu na §1.

</details>

<details>
<summary><b>Web</b></summary>

O fallback funciona pela pilha de fontes do CSS — liste-a **depois** da sua fonte de texto (aqui,
Noto Sans e Noctua Iosevka), para que só seja consultada nos glifos que a de texto não tem:

```css
@font-face {
  font-family: "Symbols Nerd Font";
  src: url("symbols-nerd-font/SymbolsNerdFont-Regular.woff2") format("woff2");
  font-display: swap;
}
@font-face {
  font-family: "Symbols Nerd Font Mono";
  src: url("symbols-nerd-font/SymbolsNerdFontMono-Regular.woff2") format("woff2");
  font-display: swap;
}

body { font-family: "Noto Sans", "Symbols Nerd Font", sans-serif; }
pre  { font-family: "Noctua Iosevka", "Symbols Nerd Font Mono", monospace; }
```

Com 1,0–1,2 MB por arquivo, isso é pesado para uma página que mostra meia dúzia de ícones. Faça um
subset dos codepoints que você realmente usa com o `pyftsubset`, do fontTools; a saída em WOFF2
também precisa do brotli. Instale os dois num ambiente virtual na raiz do clone (o `.venv/` é
ignorado pelo git). Um `pip install` puro não serve: Debian, Ubuntu, Arch e Homebrew, entre outros,
marcam o Python deles como gerenciado externamente (PEP 668) e recusam o comando com
`externally-managed-environment`. No Debian e no Ubuntu, o `python3 -m venv` também precisa do
pacote `python3-venv` (`sudo apt install python3-venv`).

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
.venv/bin/pyftsubset symbols-nerd-font/SymbolsNerdFont-Regular.ttf \
  --unicodes="U+E0B0-E0C8,U+F0001-F00FF" --flavor=woff2 \
  --output-file=symbols-subset.woff2
```

No Windows, comece com `python -m venv .venv`, troque `.venv/bin/` por `.venv\Scripts\` nos
comandos e escreva o último numa linha só. Para ter o `pyftsubset` no `PATH` em qualquer lugar,
`pipx install "fonttools[woff]"` dá a ele um ambiente próprio; o extra `woff` traz o brotli, e as
aspas impedem o zsh de expandir os colchetes. No NixOS,
`nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])'` abre um shell com o
`pyftsubset` no `PATH`.

Esse exemplo guarda 280 codepoints em 20 148 bytes, contra 1 027 540 do WOFF2 inteiro. O
`pyftsubset` avisa que descarta a tabela `PfEd`: dados privados do FontForge, que não fazem falta
para desenhar os ícones.

</details>

---

## 5. Conferir

Cada um destes tem de renderizar como símbolo — não como quadrado, nem como interrogação:

```bash
printf 'powerline    devicons    codicons    material 󰀄\n'
```

No terminal, repare também no espaço que cada ícone ocupa. Se os ícones passam por cima do caractere
seguinte, o seu terminal os desenha no tamanho natural (§1). Nos terminais testados ali, a Mono
piorou isso; uma fonte patchada ajusta os ícones ao tamanho das letras (§2).

Para ver qual fonte instalada o fontconfig escolhe para um ícone, aqui o `U+F0004`, peça-o pela
`monospace` e por uma fonte de texto nomeada, e depois liste toda fonte instalada que o tem:

```bash
fc-match 'monospace:charset=f0004' family
fc-match 'Noctua Iosevka:charset=f0004' family
fc-list ':charset=f0004' family
```

Com a regra da §4, os dois primeiros imprimem `Symbols Nerd Font`, ou `Symbols Nerd Font Mono` se
foi essa a sua escolha. Se apontarem uma fonte patchada, é ela que está servindo os seus ícones
(veja a nota da §2).

---

## 6. Licença

O Nerd Fonts distribui a Symbols Nerd Font com a licença MIT dele:
[`symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt`](symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt),
byte a byte o `LICENSE` do `NerdFontsSymbolsOnly.zip` 3.4.0. Ela exige o aviso em todas as cópias,
então **redistribuir a fonte significa distribuir esse arquivo junto**; o `symbols-nerd-font.zip`
já o leva.

Esse arquivo não conta a história toda. Os conjuntos de ícones que o Nerd Fonts reúne mantêm as
licenças de origem, e nem todas são MIT: Codicons e Font Awesome estão sob CC BY 4.0, Material
Design Icons sob Apache 2.0, Pomicons e Weather Icons sob a SIL Open Font License 1.1, e Font Logos
sob a Unlicense. O Nerd Fonts lista cada conjunto com a sua licença em
[`license-audit.md`](https://github.com/ryanoasis/nerd-fonts/blob/v3.4.0/license-audit.md), e o
[`LICENSE`](LICENSE) na raiz deste repositório resume isso. Como na própria release do Nerd Fonts,
nenhum pacote daqui leva um texto separado para cada conjunto.

Esse `LICENSE` da raiz põe o conteúdo próprio deste repositório (os scripts, os testes deles, a
documentação, o plano de build e o site) sob MIT OR Apache-2.0. Ele não alcança as fontes: cada uma
mantém a licença da sua família.

O mesmo arquivo MIT também está, byte a byte, em [`noctua-noto/licenses/`](noctua-noto/licenses/) e
[`noctua-iosevka/licenses/`](noctua-iosevka/licenses/), e não é duplicata por descuido: as 27 fontes
Nerd Font da Noto e as 135 da Noctua Iosevka (cada uma em `.ttf` e em `.woff2`) embutem estes
ícones, então carregam a mesma obrigação.
