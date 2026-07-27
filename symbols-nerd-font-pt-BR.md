# Symbols Nerd Font

*[English version](symbols-nerd-font-en.md)*

A fonte só-ícones do [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) — **10 410 glifos e
nenhuma letra**. Ela existe para ser *fallback*: você mantém a fonte de texto que quiser, e o sistema
recorre a esta para os codepoints de ícone.

Upstream sem modificação, **Nerd Fonts 3.4.0**. Arquivos em
[`symbols-nerd-font/`](symbols-nerd-font/).

---

## 1. Dois arquivos, uma diferença real

| arquivo | família | avanços |
|---|---|---|
| `SymbolsNerdFont-Regular` | `Symbols Nerd Font` | **variáveis** (326, 386, 453, 467, 496, 622 … num upm de 2048) |
| `SymbolsNerdFontMono-Regular` | `Symbols Nerd Font Mono` | **todos 2048** = exatamente um em |

Os mesmos 10 410 glifos, os mesmos contornos. O que muda é só quanto espaço horizontal cada ícone
reivindica — e é isso que decide qual você quer:

- **Em terminal**, use **`Symbols Nerd Font Mono`**. O terminal desenha numa grade fixa; um ícone
  mais largo que uma célula invade a coluna seguinte ou é cortado.
- **Em qualquer outro lugar** (interface proporcional, documentos, texto na web), use
  **`Symbols Nerd Font`**. Os ícones mantêm as proporções naturais em vez de serem espremidos num
  quadrado.

Cada um tem um `.ttf` e o `.woff2` par, para a web.

---

## 2. Quando usar isto em vez de uma fonte patchada

Há dois jeitos de ter os ícones do Nerd Fonts, e eles resolvem problemas diferentes.

| | fonte patchada (ex.: `NotoSansM Nerd Font`) | esta fonte de fallback |
|---|---|---|
| como | ícones embutidos numa cópia da fonte de texto | fonte separada, alcançada por fallback |
| ícones acompanham peso/estilo do texto | ✅ sim | ❌ não — sempre um único Regular |
| funciona com **qualquer** fonte de texto | ❌ precisa de uma build patchada por fonte | ✅ sim |
| custo em disco | uma cópia inteira da fonte de texto por peso | ~2,4 MB, uma vez |
| atualizar a fonte de texto | exige re-patchear | independente |

Use o **fallback** quando quiser manter uma fonte de texto que não tem build patchada, ou quando não
quiser carregar uma cópia patchada de cada peso. Use uma fonte **patchada** quando os ícones
precisarem assentar visualmente com o texto — mesmo peso, mesmas métricas verticais.

> ⚠️ Não instale as duas para a mesma fonte de texto. Se uma fonte patchada já fornece os codepoints
> de ícone, acrescentar esta só cria ambiguidade sobre qual arquivo o sistema escolhe.

---

## 3. O que tem dentro

Faixas de codepoint presentes no arquivo, medidas direto do `cmap` dele:

| faixa | glifos | conjunto de ícones |
|---|---|---|
| `U+E0B0–E0C8` | 25 | Powerline (separadores, símbolos extras) |
| `U+E200–E2A9` | 170 | Font Awesome Extension |
| `U+E300–E3E3` | 228 | Weather |
| `U+E5FA–E6B8` | 191 | Seti-UI + Custom |
| `U+E700–E8EF` | 496 | Devicons |
| `U+EA60–EC1E` | 435 | Codicons (VS Code) |
| `U+ED00–EFCE` | 719 | Font Awesome |
| `U+F000–F381` | 898 | Font Awesome (legado) + Font Logos |
| `U+F400–F533` | 308 | Octicons |
| `U+F0001–F1AF0` | 6 896 | Material Design Icons |

O grosso — dois terços da fonte — é Material Design Icons, no **plano 1** (`U+F0001` em diante).
Qualquer coisa que trunque codepoints para 16 bits perde esses glifos silenciosamente.

---

## 4. Instalar

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

```bash
mkdir -p ~/.local/share/fonts/SymbolsNerdFont
cp symbols-nerd-font/*.ttf ~/.local/share/fonts/SymbolsNerdFont/
fc-cache -f
fc-match "Symbols Nerd Font Mono"
```

O fontconfig chega nesta fonte sozinho para codepoints que a sua fonte de texto não tem. Para
tornar o fallback explícito e ordenado, acrescente-a ao alias `monospace` em
`~/.config/fontconfig/fonts.conf`:

```xml
<alias>
  <family>monospace</family>
  <prefer><family>Symbols Nerd Font Mono</family></prefer>
</alias>
```

</details>

<details>
<summary><b>macOS / Windows</b></summary>

**macOS:** copie os `.ttf` para `~/Library/Fonts/`, ou instale pelo Font Book.

**Windows:** selecione os `.ttf`, clique com o botão direito e escolha "Instalar".

Nos dois, os aplicativos geralmente fazem fallback sozinhos; terminais costumam ter uma configuração
explícita de fonte de fallback, que vale apontar para `Symbols Nerd Font Mono`.

</details>

<details>
<summary><b>Web</b></summary>

O fallback funciona pela pilha de fontes do CSS — liste-a **depois** da sua fonte de texto, para que
só seja consultada nos glifos que a de texto não tem:

```css
@font-face {
  font-family: "Symbols Nerd Font";
  src: url("symbols-nerd-font/SymbolsNerdFont-Regular.woff2") format("woff2");
  font-display: swap;
}

body { font-family: "Minha Fonte de Texto", "Symbols Nerd Font", sans-serif; }
pre  { font-family: "Minha Fonte Mono", "Symbols Nerd Font Mono", monospace; }
```

A 1,0–1,2 MB por arquivo isso é pesado para uma página que mostra meia dúzia de ícones. Faça um
subset dos codepoints que você realmente usa — o `pyftsubset` vem junto do `fonttools`:

```bash
pyftsubset symbols-nerd-font/SymbolsNerdFont-Regular.ttf \
  --unicodes="U+E0B0-E0C8,U+F0001-F00FF" --flavor=woff2 \
  --output-file=symbols-subset.woff2
```

</details>

---

## 5. Conferir

Cada um destes tem de renderizar como símbolo — não como quadrado, nem como interrogação:

```bash
printf 'powerline    devicons    codicons    material \U000f0004\n'
```

Em terminal, cada um deve ocupar exatamente **uma** célula. Se um ícone invade o caractere seguinte,
você está usando `Symbols Nerd Font` onde queria `Symbols Nerd Font Mono`.

Para confirmar qual arquivo de fato serviu um glifo:

```bash
fc-match -s "monospace" | head -3          # a cadeia de fallback, em ordem
```

---

## 6. Licença

MIT — [`symbols-nerd-font/licenses/`](symbols-nerd-font/licenses/). **Redistribuir exige enviá-la
junto.**

A mesma licença também está em [`noctua-noto/licenses/`](noctua-noto/licenses/), e não é duplicata
por descuido: os 27 arquivos patchados com Nerd Fonts daquele conjunto embutem exatamente estes
glifos, então carregam a mesma obrigação.
