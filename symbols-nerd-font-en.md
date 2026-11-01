# Symbols Nerd Font

*[Versão em português](symbols-nerd-font-pt-BR.md)*

The icon-only font from [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) — **10 410 icons and
no letters at all**. It exists to be a *fallback*: you keep whatever text font you like, and the
system falls back to this one for the icon codepoints.

The two `.ttf` files are **Nerd Fonts 3.4.0** as released, byte for byte the ones in its
`NerdFontsSymbolsOnly.zip`. The two `.woff2` files are web copies of them, with the same names,
metrics and outlines.

Git keeps only the license in [`symbols-nerd-font/`](symbols-nerd-font/). The fonts themselves are
a release asset, `symbols-nerd-font.zip`; §4 shows how to get them.

---

## 1. Two files, one real difference

| file | family | advance widths |
|---|---|---|
| `SymbolsNerdFont-Regular` | `Symbols Nerd Font` | **variable**: 849 different widths, up to 2729 units at 2048 upm |
| `SymbolsNerdFontMono-Regular` | `Symbols Nerd Font Mono` | **all 2048** = exactly one em |

Both hold the same 10 410 icons, at the same codepoints and under the same glyph names. What
changes is how much horizontal space each icon claims: in `Symbols Nerd Font`, 403 icons are wider
than one em. The outlines differ too: 10 054 of the icons are drawn differently in the two files,
and 9 271 of them are drawn larger in the Mono one. `md-account` (`U+F0004`) is 2048 units wide
there, and 1368 in `Symbols Nerd Font`.

- **`Symbols Nerd Font`** gives each icon the width of its own drawing, so icons keep their natural
  proportions. Use it in proportional text (UI, documents, web body text), and start with it in a
  terminal too.
- **`Symbols Nerd Font Mono`** gives every icon the same width, one em. Where text is laid out by
  advance widths, as in a browser, any icon then moves the text after it by the same amount. The
  web example in §4 uses it for `pre` blocks.

**Neither file fits a terminal cell.** A cell is narrower than one em: 0.6 em in Noctua Iosevka
(600 of 1000 units) and in DejaVu Sans Mono (1233 of 2048). A Mono icon is one em wide, about 1.7
cells, and most icons of `Symbols Nerd Font` are wider than a cell as well. What a terminal does
with a glyph wider than its cell is up to the terminal. In a test, Alacritty 0.17.0 and foot 1.27.0
both drew it at its natural size, over the next character: with Noctua Iosevka at 28 pt, `U+F0004`
covered 1.7 cells from the Mono file and 1.1 from `Symbols Nerd Font`. Nerd Fonts' own fontconfig
file, `10-nerd-font-symbols.conf` in the same `NerdFontsSymbolsOnly.zip`, prefers
`Symbols Nerd Font` for `monospace` and 368 other families, and never names the Mono file. If every
icon must take exactly one cell, use a patched font (§2). §5 shows how to check your terminal.

Each is a `.ttf` plus a matching `.woff2` for the web.

---

## 2. When to use this instead of a patched font

There are two ways to get Nerd Fonts icons, and they solve different problems.

| | patched font (e.g. `NotoSansM Nerd Font`) | this fallback font |
|---|---|---|
| how | icons built into a copy of the text font | separate font, reached by fallback |
| icon size | fitted to the text font: in `NotoSansM Nerd Font` each icon is 600 units wide, like its letters | its own: up to 2729 units at 2048 upm, one em in Mono |
| icons follow the text's weight | ❌ no — the same outlines in every weight | ❌ no — one Regular weight |
| works with **any** text font | ❌ needs a patched build per font | ✅ yes |
| disk cost | a full copy of the text font per weight | 2.4 MB per file (2.5 MB for Mono), once |
| updating the text font | requires re-patching | independent |

The weight row is measured: the Regular, Medium and Bold files of `NotoSansM Nerd Font` share all
10 396 icon outlines.

Use the **fallback** when you want to keep a text font that has no patched build, or when you do not
want to carry a patched copy of every weight. Use a **patched** font when the icons must take
exactly the text font's own cell.

> ⚠️ Pick one source of icons. A patched font installed anywhere on the system can serve the icons
> of other fonts too, ahead of this one. In a test with fontconfig 2.17.1 and `NotoSansM Nerd Font`
> installed beside both files of this font, an icon asked of `monospace`, of `DejaVu Sans Mono` or
> of `Noctua Iosevka` came from `NotoSansM Nerd Font`, even with the rule from §4 in place. §5 shows
> how to see which font you get.

---

## 3. What is inside

Codepoint ranges present in both files, measured directly from their `cmap`. The set of each range
comes from the glyph names (`pl-…`, `cod-…`, `md-…` and so on) and from the ranges in Nerd Fonts'
[`font-patcher`](https://github.com/ryanoasis/nerd-fonts/blob/v3.4.0/font-patcher) 3.4.0. A few
glyphs carry no set in their name, such as `uni2630`, or `heart` at `U+F08D0`.

| range | icons | icon set |
|---|---|---|
| `U+23FB–23FE`, `U+2B58` | 5 | IEC Power Symbols |
| `U+2630` | 1 | Powerline Extra |
| `U+2665`, `U+26A1` | 2 | Octicons |
| `U+276C–2771` | 6 | Heavy Angle Brackets |
| `U+E000–E00A` | 11 | Pomicons |
| `U+E0A0–E0D7` | 40 | Powerline and Powerline Extra |
| `U+E200–E2A9` | 170 | Font Awesome Extension |
| `U+E300–E3E3` | 228 | Weather Icons |
| `U+E5FA–E6B8` | 191 | Seti-UI + Custom |
| `U+E700–E8EF` | 496 | Devicons |
| `U+EA60–EC1E` | 439 | Codicons (VS Code) |
| `U+ED00–EFCE` | 719 | Font Awesome, with 12 progress-bar and spinner glyphs at `U+EE00–EE0B` |
| `U+F000–F2FF` | 768 | Font Awesome |
| `U+F300–F381` | 130 | Font Logos |
| `U+F400–F533` | 308 | Octicons |
| `U+F0001–F1AF0` | 6 896 | Material Design Icons |

The bulk — two thirds of the font — is Material Design Icons, in **plane 15**, the Supplementary
Private Use Area-A (`U+F0001` and up). Anything that truncates codepoints to 16 bits will silently
lose them.

The first four rows are 14 ordinary Unicode symbols, outside the Private Use Area:
⏻ ⏼ ⏽ ⏾ ☰ ♥ ⚡ ❬ ❭ ❮ ❯ ❰ ❱ ⭘. Fallback is only consulted for what the text font lacks, so a text
font that has them draws them itself: Noctua Iosevka has all 14, DejaVu Sans Mono has 8.

---

## 4. Installing

A clone of this repository does not hold these fonts. They come from the release archive
`symbols-nerd-font.zip` (about 5 MB), and `font-archives.py` fetches it. From the root of the
clone:

```bash
./font-archives.py fetch --archive symbols-nerd-font.zip
./font-archives.py verify --allow-missing
```

`fetch` writes a font only once its SHA-256 matches the committed `SHA256SUMS`.
`verify --allow-missing` checks the fonts that are present against that file and counts the
others as missing. The script needs Python 3.9 or newer and nothing outside its standard
library; on Windows, run it as `python font-archives.py`. To check with no tool at all, from the
same place, on Linux:

```bash
sha256sum -c SHA256SUMS --ignore-missing
```

On macOS:

```bash
shasum -a 256 -c SHA256SUMS --ignore-missing
```

Without a clone, download the archive from the release:
<https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/symbols-nerd-font.zip>.
It unpacks to `symbols-nerd-font/`, with the four fonts and the license. In a clone,
`./font-archives.py list` names all 23 archives, and `font-archives.json` says what each one holds.

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

```bash
mkdir -p ~/.local/share/fonts/SymbolsNerdFont
cp symbols-nerd-font/*.ttf ~/.local/share/fonts/SymbolsNerdFont/
fc-cache -f
fc-match "Symbols Nerd Font"
fc-match "Symbols Nerd Font Mono"
```

The last two lines must print `SymbolsNerdFont-Regular.ttf: "Symbols Nerd Font" "Regular"` and
`SymbolsNerdFontMono-Regular.ttf: "Symbols Nerd Font Mono" "Regular"`. Any other file means
fontconfig did not find the fonts.

fontconfig reaches this font on its own for codepoints your text font lacks. In a test with both
files installed and no rule, the icons came from `Symbols Nerd Font`, the file §1 suggests. To make
that choice explicit, or to choose the Mono file, put this in `~/.config/fontconfig/fonts.conf` (if
the file already exists, add the two `<alias>` blocks inside its `<fontconfig>`):

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

For the Mono file, write `Symbols Nerd Font Mono` in both blocks. The first block covers
`monospace` and the fonts that fontconfig already counts as monospace, DejaVu Sans Mono among them.
A font it does not know, such as Noctua Iosevka, needs a block of its own: with the Mono file in
the first block only, Noctua Iosevka still took its icons from `Symbols Nerd Font`. Put your own
text font's family name there. The rule does not take the letters away from your text font:
`fc-match monospace` still named DejaVu Sans Mono.

</details>

<details>
<summary><b>macOS / Windows</b></summary>

**macOS:** copy the `.ttf` files into `~/Library/Fonts/`, or install them through Font Book.

**Windows:** select the `.ttf` files, right-click and choose "Install".

On both, applications generally fall back automatically; terminals usually have an explicit
fallback-font setting worth pointing at the file you chose in §1.

</details>

<details>
<summary><b>Web</b></summary>

Fallback works through the CSS font stack — list it **after** your text font (here Noto Sans and
Noctua Iosevka), so it is only consulted for glyphs the text font does not have:

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

At 1.0–1.2 MB per file this is heavy for a page that shows a handful of icons. Subset it to the
codepoints you actually use, with `pyftsubset` from fontTools; WOFF2 output also needs brotli.
Install both in a virtual environment at the root of the clone (`.venv/` is git-ignored). A bare
`pip install` will not do: Debian, Ubuntu, Arch and Homebrew, among others, mark their Python as
externally managed (PEP 668) and refuse it with `externally-managed-environment`. On Debian and
Ubuntu, `python3 -m venv` also needs the `python3-venv` package (`sudo apt install python3-venv`).

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
.venv/bin/pyftsubset symbols-nerd-font/SymbolsNerdFont-Regular.ttf \
  --unicodes="U+E0B0-E0C8,U+F0001-F00FF" --flavor=woff2 \
  --output-file=symbols-subset.woff2
```

On Windows, start with `python -m venv .venv`, write `.venv\Scripts\` where the commands say
`.venv/bin/`, and put the last command on one line. To have `pyftsubset` on your `PATH`
everywhere instead, `pipx install "fonttools[woff]"` gives it an environment of its own; the `woff`
extra brings brotli, and the quotes keep zsh from expanding the brackets. On NixOS,
`nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])'` opens a shell with
`pyftsubset` on the `PATH`.

That example keeps 280 codepoints in 20 148 bytes, against 1 027 540 for the whole WOFF2.
`pyftsubset` warns that it drops the `PfEd` table: FontForge's private data, which nothing needs to
draw the icons.

</details>

---

## 5. Checking it works

Each of these must render as a symbol — not as a box, and not as a question mark:

```bash
printf 'powerline    devicons    codicons    material 󰀄\n'
```

In a terminal, also look at how much room each icon takes. If icons run over the next character,
your terminal draws them at their natural size (§1). In the terminals tested there, the Mono file
made that worse; a patched font sizes the icons to the letters (§2).

To see which installed font fontconfig picks for an icon, here `U+F0004`, ask for it through
`monospace` and through a named text font, then list every installed font that has it:

```bash
fc-match 'monospace:charset=f0004' family
fc-match 'Noctua Iosevka:charset=f0004' family
fc-list ':charset=f0004' family
```

With the rule from §4, the first two print `Symbols Nerd Font`, or `Symbols Nerd Font Mono` if you
chose it. If they name a patched font, that font is serving your icons (see the note in §2).

---

## 6. License

Nerd Fonts ships Symbols Nerd Font with its MIT license:
[`symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt`](symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt),
byte for byte the `LICENSE` in its 3.4.0 `NerdFontsSymbolsOnly.zip`. It requires its notice in all
copies, so **redistributing the font means shipping that file alongside it**;
`symbols-nerd-font.zip` carries it.

That file is not the whole story. The icon sets that Nerd Fonts gathers keep their own upstream
licenses, and not all of them are MIT: Codicons and Font Awesome are under CC BY 4.0, Material
Design Icons under Apache 2.0, Pomicons and Weather Icons under the SIL Open Font License 1.1, and
Font Logos under the Unlicense. Nerd Fonts lists every set with its license in
[`license-audit.md`](https://github.com/ryanoasis/nerd-fonts/blob/v3.4.0/license-audit.md), and the
[`LICENSE`](LICENSE) at the root of this repository sums it up. As in Nerd Fonts' own release, no
archive here carries a separate text for each set.

That root `LICENSE` puts this repository's own content (the scripts, their tests, the documentation,
the build plan and the site) under MIT OR Apache-2.0. It does not reach the fonts: each keeps the
license of its family.

The same MIT file also sits, byte for byte, in [`noctua-noto/licenses/`](noctua-noto/licenses/) and
[`noctua-iosevka/licenses/`](noctua-iosevka/licenses/), and that is not a duplicate by accident: the
27 Nerd Font faces of Noto and the 135 of Noctua Iosevka (each as a `.ttf` and a `.woff2`) embed
these icons, so they carry the same obligation.
