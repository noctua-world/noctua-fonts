# Symbols Nerd Font

*[Versão em português](symbols-nerd-font-pt-BR.md)*

The icon-only font from [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) — **10 410 glyphs and
no letters at all**. It exists to be a *fallback*: you keep whatever text font you like, and the
system falls back to this one for the icon codepoints.

Unmodified upstream, **Nerd Fonts 3.4.0**. Files live in
[`symbols-nerd-font/`](symbols-nerd-font/).

---

## 1. Two files, one real difference

| file | family | advance widths |
|---|---|---|
| `SymbolsNerdFont-Regular` | `Symbols Nerd Font` | **variable** (326, 386, 453, 467, 496, 622 … at 2048 upm) |
| `SymbolsNerdFontMono-Regular` | `Symbols Nerd Font Mono` | **all 2048** = exactly one em |

Same 10 410 glyphs, same outlines. The only thing that changes is how much horizontal space each
icon claims — and that decides which one you want:

- **In a terminal**, use **`Symbols Nerd Font Mono`**. A terminal draws on a fixed grid; an icon
  wider than one cell overlaps the next column or gets clipped.
- **Everywhere else** (proportional UI, documents, web body text), use **`Symbols Nerd Font`**. Icons
  keep their natural proportions instead of being squeezed into a square.

Each is a `.ttf` plus a matching `.woff2` for the web.

---

## 2. When to use this instead of a patched font

There are two ways to get Nerd Fonts icons, and they solve different problems.

| | patched font (e.g. `NotoSansM Nerd Font`) | this fallback font |
|---|---|---|
| how | icons baked into a copy of the text font | separate font, reached by fallback |
| icons match the text font's weight/style | ✅ yes | ❌ no — always one Regular weight |
| works with **any** text font | ❌ needs a patched build per font | ✅ yes |
| disk cost | a full copy of the text font per weight | ~2.4 MB, once |
| updating the text font | requires re-patching | independent |

Use the **fallback** when you want to keep a text font that has no patched build, or when you do not
want to carry a patched copy of every weight. Use a **patched** font when the icons must sit visually
with the text — matching weight, matching vertical metrics.

> ⚠️ Do not install both for the same text font. If a patched font already provides the icon
> codepoints, adding this one only creates an ambiguity about which file the system picks.

---

## 3. What is inside

Codepoint ranges present in the file, measured directly from its `cmap`:

| range | glyphs | icon set |
|---|---|---|
| `U+E0B0–E0C8` | 25 | Powerline (separators, extra symbols) |
| `U+E200–E2A9` | 170 | Font Awesome Extension |
| `U+E300–E3E3` | 228 | Weather |
| `U+E5FA–E6B8` | 191 | Seti-UI + Custom |
| `U+E700–E8EF` | 496 | Devicons |
| `U+EA60–EC1E` | 435 | Codicons (VS Code) |
| `U+ED00–EFCE` | 719 | Font Awesome |
| `U+F000–F381` | 898 | Font Awesome (legacy) + Font Logos |
| `U+F400–F533` | 308 | Octicons |
| `U+F0001–F1AF0` | 6 896 | Material Design Icons |

The bulk — two thirds of the font — is Material Design Icons, sitting in **plane 1**
(`U+F0001` and up). Anything that truncates codepoints to 16 bits will silently lose them.

---

## 4. Installing

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

```bash
mkdir -p ~/.local/share/fonts/SymbolsNerdFont
cp symbols-nerd-font/*.ttf ~/.local/share/fonts/SymbolsNerdFont/
fc-cache -f
fc-match "Symbols Nerd Font Mono"
```

fontconfig will reach this font automatically for codepoints your text font lacks. To make the
fallback explicit and ordered, add it to the `monospace` alias in
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

**macOS:** copy the `.ttf` files into `~/Library/Fonts/`, or install them through Font Book.

**Windows:** select the `.ttf` files, right-click and choose "Install".

On both, applications generally fall back automatically; terminals usually have an explicit
fallback-font setting worth pointing at `Symbols Nerd Font Mono`.

</details>

<details>
<summary><b>Web</b></summary>

Fallback works through the CSS font stack — list it **after** your text font, so it is only consulted
for glyphs the text font does not have:

```css
@font-face {
  font-family: "Symbols Nerd Font";
  src: url("symbols-nerd-font/SymbolsNerdFont-Regular.woff2") format("woff2");
  font-display: swap;
}

body { font-family: "My Text Font", "Symbols Nerd Font", sans-serif; }
pre  { font-family: "My Mono Font", "Symbols Nerd Font Mono", monospace; }
```

At 1.0–1.2 MB per file this is heavy for a page that shows a handful of icons. Subset it to the
codepoints you actually use — `pyftsubset` ships with `fonttools`:

```bash
pyftsubset symbols-nerd-font/SymbolsNerdFont-Regular.ttf \
  --unicodes="U+E0B0-E0C8,U+F0001-F00FF" --flavor=woff2 \
  --output-file=symbols-subset.woff2
```

</details>

---

## 5. Checking it works

Each of these must render as a symbol — not as a box, and not as a question mark:

```bash
printf 'powerline    devicons    codicons    material \U000f0004\n'
```

In a terminal, each one must occupy exactly **one** cell. If an icon overlaps the next character,
you are using `Symbols Nerd Font` where you want `Symbols Nerd Font Mono`.

To confirm which file actually served a glyph:

```bash
fc-match -s "monospace" | head -3          # the fallback chain, in order
```

---

## 6. License

MIT — [`symbols-nerd-font/licenses/`](symbols-nerd-font/licenses/). **Redistribution requires
shipping it alongside the font.**

The same license also sits in [`noctua-noto/licenses/`](noctua-noto/licenses/), and that is not a
duplicate by accident: the 27 Nerd Fonts patched files in that set embed these very glyphs, so they
carry the same obligation.
