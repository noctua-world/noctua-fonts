# Noctua Noto

*[Versão em português](noctua-noto-pt-BR.md)*

Base typeface for the projects, in two forms: the **plain Noto** families (variable, upstream from
Google Fonts) and the same families **patched with Nerd Fonts 3.4.0** — icon glyphs baked into the
text font, which removes the need for a separate icon font.

The files belong in [`noctua-noto/`](../noctua-noto/), but git does not hold them: they come from
the release archives (next section). Inventory taken on 2026-07-27 and measured again on 2026-11-01;
the numbers (sizes, counts) describe those files.

---

## Getting the fonts

A fresh clone has no fonts. They are assets of the GitHub release
[`v1.0.0`](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0), in zip archives that
[`font-archives.json`](../tools/font-archives.json) describes, and git keeps
[`SHA256SUMS`](../SHA256SUMS) instead: one SHA-256 per font. Two of the 23 archives hold this
document's fonts:

| archive | holds | download |
|---|---|---|
| `noctua-noto-ttf.zip` | the 49 TTF, plus the 20 licence files of [`noctua-noto/licenses/`](../noctua-noto/licenses/) | about 79 MiB (150 MiB unpacked) |
| `noctua-noto-woff2.zip` | the 49 WOFF2, plus the same 20 licence files | about 58 MiB (about the same unpacked) |

```bash
git clone https://github.com/noctua-world/noctua-fonts.git
cd noctua-fonts
./tools/font-archives.py fetch --archive noctua-noto-ttf.zip noctua-noto-woff2.zip
./tools/font-archives.py verify --allow-missing
```

`font-archives.py` needs Python 3.9 or later and nothing else (on Windows, run it as `python
tools/font-archives.py …`). `fetch` writes a font only when its SHA-256 matches `SHA256SUMS`, and an
archive is all or nothing: one that fails leaves the tree as it was. It does not download an archive
whose fonts are already present and correct. The licence files are already in git; `fetch` checks
that the archive's copies are identical to them and does not write them. Without `--archive` it
fetches all 23 archives (Noctua Iosevka and Symbols Nerd Font as well). `verify --allow-missing`
checks the fonts that are present and only counts the missing ones.

The same check works with nothing but the system's checksum command. On Linux:

```bash
sha256sum --ignore-missing -c SHA256SUMS
```

On macOS:

```bash
shasum -a 256 --ignore-missing -c SHA256SUMS
```

`--ignore-missing` skips the files that are not in the tree, here the fonts of the other 21 archives.

---

## 1. Inventory — 49 TTF (+ 49 matching WOFF2)

| group | count | variable? | which |
|---|---|---|---|
| **plain Noto** | **18** | ✅ `wght` 100–900 on 17, 300–700 on Emoji; **14** of them also `wdth` 62.5–100 | Sans, Sans-Italic, Serif, Serif-Italic, Display, Display-Italic, Mono, Arabic, Armenian, Devanagari, Ethiopic, Georgian, Hebrew, Thai, JP, KR, SC, Emoji |
| **Nerd Font** patched | **27** | ❌ static | `NotoSans` (Light–Bold + italics), `NotoSansDisplay` (Regular–Bold + italics), `NotoSerif` (Regular/Medium/Bold + italics), `NotoSansM` (Regular/Medium/Bold) |
| standalone | **4** | ❌ static | ColorEmoji (colour vector, COLR v1 and SVG, 24 MiB — §5c), Music, Math, Mongolian |

**Family names of the patched set** — what to write in CSS/QML/`pubspec` (read §5b first):

| family | found by OS font lookup? |
|---|---|
| `NotoSans Nerd Font` | ✅ if Nerd Fonts' own Noto package is installed |
| `NotoSerif Nerd Font` | ✅ likewise |
| `NotoSansM Nerd Font` | ⚠️ the name exists in Nerd Fonts' package, but there it is another variant, with wider icons — §5b. This is the **monospaced** one (`M` = Mono, the patcher's abbreviation) |
| `NotoSansDisplay Nerd Font` | ❌ **only by embedding the file** — §5b |

<details>
<summary><b>The 18 variable fonts in detail</b> — axes, instances, sizes</summary>

| file (`.ttf` / `.woff2`) | family | `wght` (min, **default**, max) | `wdth` | instances | TTF / WOFF2 (KiB) |
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

All 18 carry `fvar`, a `STAT` table and named instances. Fifteen name the 9 weights Thin,
ExtraLight, Light, Regular, Medium, SemiBold, Bold, ExtraBold and Black; the two Display files name
those 9 at four widths (36); Emoji names 5, Light to Bold. The two Display files' `STAT` has no axis
values (§5d). Modern font managers enumerate each instance as a **separate face** — meaning they
already behave like an ordinary static family:

```console
$ fc-query --format='%{style} w=%{weight} var=%{variable}\n' NotoSans-VariableFont_wdth,wght.ttf
Regular w=80 var=False
Thin w=0 var=False
…
Black w=210 var=False
 w=[0 210] var=True
```

The last line is the variable face itself, on top of the 9 named ones.

</details>

[`noctua-noto/licenses/`](../noctua-noto/licenses/) holds 20 licence files: the SIL Open Font
License 1.1 of each of the 19 Noto families, and the MIT license that [Nerd
Fonts](symbols-nerd-font-en.md) ships its icons with (`LICENSE-NerdFontsSymbolsOnly.txt`), for the
icons in the 27 patched faces. The icon sets that Nerd Fonts gathers keep their own upstream
licences, and not all of them are MIT; [`LICENSE`](../LICENSE) names those that are not and points
to Nerd Fonts' list of every set. **Redistribution requires shipping these files alongside the
fonts**; both archives carry all 20. The repository's own licence (MIT OR Apache-2.0) covers its
scripts and documents, not the fonts.

---

## 2. Convert the variable fonts to static? **Not wholesale.**

Variable font support has been universal since 2017–18 (Chrome 62, Firefox 62, Safari 11, Edge 17,
FreeType 2.8.1, fontconfig 2.13, CoreText, DirectWrite, Qt 6, Flutter/Skia, HarfBuzz). It is not a
practical compatibility risk. Three concrete reasons to keep the variable files as the **master**:

1. **What projects usually name is already static.** The 27 `*NerdFont-*` files — the families that
   show up in CSS/QML — have no `fvar`, because the Nerd Fonts patcher (FontForge) does not take
   variable fonts: given `NotoSansHebrew-VariableFont_wdth,wght.ttf`, the pinned patcher image (§3)
   exits with status 1 and writes nothing. The split is already correct: the variable files are the
   unpatched complement, covering i18n scripts and arbitrary weights.
2. **Condensed exists ONLY as an axis.** In Sans, Serif, Mono, Arabic, Armenian, Devanagari,
   Ethiopic, Georgian, Hebrew and Thai the 9 named instances are **all `wdth=100`** — only `Display`
   publishes SemiCondensed/Condensed/ExtraCondensed as named instances (hence its 36). Flattening
   blindly throws Condensed away.
3. **You lose the intermediate weights** and gain nothing: 9 files where there was 1.

Generate static faces **on demand** with
[`instantiate-variable-font.py`](../tools/instantiate-variable-font.py), and only for the targets
that need them (§3).

---

## 3. Guide by target

<details open>
<summary><b>Web (browser)</b> — use the variable font directly</summary>

One file covers all 9 weights **and** the Condensed axis. Declare the axis ranges in the
`@font-face` rule:

```css
@font-face {
  font-family: "Noto Sans";
  src: url("NotoSans-VariableFont_wdth,wght.woff2") format("woff2");
  font-weight: 100 900;
  font-stretch: 62.5% 100%;
  font-display: swap;
}
```

`font-weight` is the `wght` range: `100 900`, or `300 700` for Noto Emoji (§5a says why it
matters most for JP, KR, SC and Hebrew). `font-stretch` belongs only on the 14 files that have a
`wdth` axis. `format("woff2")` is enough for a variable WOFF2.

**CJK requires slicing.** `NotoSansSC` alone is 7.4 MiB of WOFF2 (`JP` 4.0 MiB, `KR` 3.7 MiB) —
never load one whole. Cut it into slices of 400 codepoints, in codepoint order, and give each slice
its own `@font-face` with a `unicode-range` that lists exactly the codepoints the slice holds; the
browser then fetches only the slices with characters on the page. `noctua-design` uses the same
rule, but it first subsets each CJK font to its CJK ranges, so none of its slices holds Latin. The
script below slices the whole font with fontTools (§4): save it as `slice-cjk.py`, outside the
repository.

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

It writes `NotoSansSC-000.woff2` to `NotoSansSC-077.woff2` and `NotoSansSC.css`, one `@font-face`
per slice. Each range is read back from the slice it describes, so it lists what that file holds.
The slices stay variable on `wght`, so every rule declares `font-weight: 100 900`. Measured: SC
gives 78 slices in about a minute, the largest 166 KiB; JP gives 42 and KR 58.

Slice 000 holds the font's Latin, Greek and Cyrillic, and the space. The browser loads the first
font in `font-family` whose `unicode-range` includes the space, whatever the text (CSS takes the
line's metrics from it), so put a Latin family before the CJK one. Measured in Chrome 150 with
`font-family: "Noto Sans", "Noto Sans SC"`: a line of six ideographs fetched exactly the six slices
that hold them, and Latin text fetched no SC slice. With `"Noto Sans SC"` alone, the six ideographs
also fetched slice 000; with `"Noto Sans SC", "Noto Sans"`, Latin text fetched slice 000.

</details>

<details>
<summary><b>Flutter / mobile</b> — static faces are simpler</summary>

Flutter **cannot read WOFF2** → use TTF. Variable fonts do work (`FontVariation`), but `pubspec.yaml`
wants a `weight:` mapping per declared face. The path of least friction is to instantiate only the
weights you use and declare each file:

```bash
./tools/instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 400 500 700 --out ~/noto-static
```

This writes `NotoSans-Regular.ttf`, `NotoSans-Medium.ttf` and `NotoSans-Bold.ttf`. Why `--out`: §4.

</details>

<details>
<summary><b>Desktop</b> (native toolkits, embedded webviews) — usually nothing to do</summary>

Resolution happens by **name**, through the OS font manager (fontconfig on Linux, CoreText on macOS,
DirectWrite on Windows), which already expands the named instances of a variable font.

> ⚠️ If the OS already ships Noto and the Noto variant of Nerd Fonts, **do not install these files
> alongside them**: it would duplicate the families and make it ambiguous which file a name lookup
> returns. Install them only where the system lacks them — or embed them in the app, which bypasses
> OS lookup entirely.

</details>

<details>
<summary><b>Re-patching with Nerd Fonts / PDF / print</b> — the only target that requires static faces</summary>

The patch runs in Docker (to install it, see Step 1 of
[Noctua Iosevka](noctua-iosevka-en.md)): the `nerdfonts/patcher` image bundles FontForge and
`font-patcher`. It patches every font in the folder mounted at `/in` and writes to the folder at
`/out`. `-u` makes the output yours rather than root's; `:ro` mounts the input read-only.

```bash
./tools/instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 300 400 500 600 700 --out ~/noto-static
mkdir -p ~/noto-patched
docker run --rm -u "$(id -u):$(id -g)" \
  -v ~/noto-static:/in:ro \
  -v ~/noto-patched:/out \
  nerdfonts/patcher:4.26.0@sha256:d18c1bd44f4577bf359f5cc0b61767bbda2658c6680ff9255cd770e630527efb \
  --complete
```

- **`--complete`** adds every icon set. **`--mono`** makes every icon one cell wide: the three
  `NotoSansM` faces were patched with it (§5b), so add it when patching Noto Sans Mono. The image
  patches the faces in parallel: here the whole block above, the five instances included, took
  about 70 seconds.
- **The image is pinned by digest.** It is the one pinned for the Noctua Iosevka Nerd faces in
  [`noctua-iosevka/private-build-plans.toml`](../noctua-iosevka/private-build-plans.toml), whose
  header says why: its tag has been re-pushed once. `nerdfonts/patcher` without a tag is the latest
  build (4.27.3 on 2026-11-01), which stamps a later Nerd Fonts version.
- **It does not reproduce the 27 faces here.** It stamps Nerd Fonts 3.4.0, as they do, but they
  carry 10,410 icon codepoints, exactly the set of Symbols Nerd Font in this repository. The image
  adds those 10,410 and 109 more Private Use Area codepoints (U+E6B9 to U+F385): 10,519 on a
  Noto Sans or Noto Sans Display instance. On a Noto Sans Mono instance it also adds the 256
  Braille patterns (U+2800 to U+28FF). Which patcher build made the 27 is not recorded.
- **The patcher picks the names.** `NotoSans-Bold.ttf` comes out as `NotoSansNerdFont-Bold.ttf`,
  family `NotoSans Nerd Font`, PostScript name `NotoSansNF-Bold`. A Noto Sans Mono instance with
  `--mono` comes out as `NotoSansMNerdFontMono-Regular.ttf`, family `NotoSansM Nerd Font Mono`. The
  27 here were renamed after patching (§5b).

To produce the WOFF2 files afterwards, see [Converting TTF to WOFF2](convert-ttf-to-woff2-en.md).

</details>

---

## 4. Tools

At the root of this repository, documented via `--help`. The font tools are generic: they work on
any font.

| script | what it does |
|---|---|
| [`font-archives.py`](../tools/font-archives.py) | fetch the fonts from the release (`fetch`) and check a tree against `SHA256SUMS` (`verify`); `list` shows each archive with its file count and size. Standard library only |
| [`instantiate-variable-font.py`](../tools/instantiate-variable-font.py) | variable → static. With no options it generates the *named instances* the font itself declares. `--weights` and `--widths` take several values and may be repeated (the values add up); `--axis TAG=VALUE` pins an axis by its tag. `--list` shows the axes, the file each named instance would be written to, and which rule names it (`stat`, `fvar` or `coords`). A value outside an axis range is refused before anything is written, never clamped |
| [`rename-font-family.py`](../tools/rename-font-family.py) | align the family name recorded inside the files — this is what fixed §5b. In `noctua-noto/` each `.ttf` has its `.woff2` beside it, under the same stem: renaming the `.ttf` rebuilds and renames that web copy too, as long as the copy's names match the font's. If they do not, the batch is refused and nothing changes |
| [`check.py`](../tools/check.py) | runs the test suite, `site/build.py --check` and `font-archives.py verify --allow-missing`. Run it before a commit |

**Python.** `instantiate-variable-font.py`, `rename-font-family.py`, `pyftsubset`, the slicing
script of §3 and `check.py`'s tests need fontTools, plus brotli for WOFF2. Install them in a
virtual environment, at the repository root (git ignores `.venv/`):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

On Linux and macOS, once it is active, `./tools/instantiate-variable-font.py`, `python3` and
`pyftsubset` all use it. On Windows: `python -m venv .venv`, then `.venv\Scripts\python -m pip
install fonttools brotli` and `.venv\Scripts\activate`. A Windows venv has `python`, not `python3`,
so run the scripts through it: `python tools/instantiate-variable-font.py …`. A bare `pip install`
fails on the system Python of Debian, Ubuntu and Arch, and on Homebrew's: they mark it as externally
managed (PEP 668). `pipx install fonttools` (then `pipx inject fonttools brotli`) gives you the
`fonttools` and `pyftsubset` commands, but the scripts here import fontTools, and pipx does not make
it importable for them. On NixOS, use a shell: `nix-shell -p 'python3.withPackages(ps: [ps.fonttools
ps.brotli])'`.

**Write generated fonts outside the font folders.** `instantiate-variable-font.py` writes to
`static/` next to its input by default. Git ignores that folder, but `font-archives.py verify` (and
so `check.py`) counts every font under `noctua-noto/`, `noctua-iosevka/` and `symbols-nerd-font/`,
`static/` included, and fails on one that `SHA256SUMS` does not list. The examples here pass
`--out ~/noto-static`.

---

## 5. Pitfalls

### ⚠️ a) The default instance is Thin in `JP`, `KR`, `SC` and `Hebrew`

Those four have `wght` **default 100**, not 400 — `fc-query` literally reports `Thin,Regular` as the
first face, the default instance. Anything that draws the file without setting the `wght` axis gets
**hairline text**.

- **Web:** declare `font-weight: 100 900` in the `@font-face` rule (§3), so that `font-weight`
  maps onto the whole axis. Measured in Chrome 150: even with no `font-weight` in the rule, Chrome
  set `wght` from `font-weight` and drew JP and Hebrew Regular at 400 and Bold at 700. Other
  browsers were not measured; the declared range does not depend on that.
- **Instantiating:** `instantiate-variable-font.py` names these four from their `STAT` table, which
  names all 9 named instances of each: `--weights 400` gives `<Family> Regular`, with
  `usWeightClass` 400. **But the weight is pinned only when you pass `--weights`**, or generate the
  named instances (no axis options). An axis you do not name stays at the font's default, Thin here:
  `--widths 75` on Hebrew writes `NotoSansHebrew-ThinCondensed.ttf`, and `--weights 400 --widths 75`
  writes `NotoSansHebrew-Condensed.ttf`.

This is the **real** risk in this set. The fix is to pin the axis where the file is used; nothing
has to be converted.

### ✅ b) Family naming of the patched set — aligned on 2026-07-27, with two caveats

The Nerd Fonts patcher abbreviates names, and whoever generates the files often renames them
afterwards. When the string does not match what the app asks for, name lookup falls back
**silently** — the text renders in a different font, with no error anywhere.

**What was done:** the 3 monospaced files were renamed from `NotoSansMono Nerd Font` to
**`NotoSansM Nerd Font`**, which keeps the patcher's abbreviation of Noto Sans Mono. The files are
now `NotoSansMNerdFont-{Regular,Medium,Bold}.{ttf,woff2}`. Verified that the design did not change:
14332 glyphs, a cmap of 13900, and every glyph but `.null` advancing 600 units (a single cell).

> ⚠️ **Caveat — elsewhere, `NotoSansM Nerd Font` names another variant.** These files are the
> patcher's **Mono** variant (`--mono`, every icon one cell wide). Their unique ID (name ID 3) was
> not part of the rename and still says so: `NotoSansM Nerd Font Mono Regular 3.4.0` (Medium and
> Bold likewise), exactly what the pinned image writes with `--mono`. The patcher calls that
> variant `NotoSansM Nerd Font Mono`. It gives `NotoSansM Nerd Font` to its default variant, whose
> wide icons take two or three cells: patching Noto Sans Mono Regular without `--mono` gives 243
> glyphs of advance 1200 and 9 of 1800, and Nerd Fonts' own `NotoSansMNerdFont-Regular.ttf` has the
> same. So the name means these single-cell files only when they are embedded; an OS with Nerd
> Fonts' Noto package installed resolves it to the wide variant. Where single-cell icons matter
> (a terminal, a grid), embed the files.

> ⚠️ **Caveat — `NotoSansDisplay Nerd Font` is not a name that exists outside these files.** The
> patcher **folds Display into the `NotoSans` family**: the pinned image names a Noto Sans Display
> Regular instance `NotoSansNerdFont-DisplayRegular.ttf`, typographic family `NotoSans Nerd Font`,
> style `Display Regular`, and the original unique ID of the Regular here still records
> `NotoSans Nerd Font Display 3.4.0`. The distinct name was assigned afterwards, and Nerd Fonts' own
> Noto package has no Display. Asking the OS for it gets whatever face the system falls back to
> (`fc-match` returns the same face as for `sans-serif`), with no error. Use it **only by embedding**
> the file, always with Sans in the fallback chain:
> ```css
> font-family: "NotoSansDisplay Nerd Font", "NotoSans Nerd Font", ui-sans-serif, sans-serif;
> ```

> ⚠️ None of this applies to the **variable** files: `NotoSansMono-VariableFont_wdth,wght.ttf` is the
> *unpatched* Noto Sans Mono, family `Noto Sans Mono` — the correct upstream name. Do not rename it.

### ⚠️ c) `NotoColorEmoji-Regular.ttf` draws only through its colour tables

24 MiB (5.4 MiB as WOFF2). Its emoji are vector colour glyphs, stored twice: in a `COLR` version 1
table (3993 glyphs, colours from a `CPAL` palette) and in an OpenType-SVG table (the same 3993
glyphs). The `glyf` outlines under them are empty (U+1F600 has 0 contours), so a renderer that reads
neither table draws nothing. For monochrome vector emoji use `NotoEmoji-VariableFont_wght`
(variable, `wght` 300–700).

### ⚠️ d) Noto Sans Display: its `STAT` table cannot name instances

Both Display files have a `STAT` table with design axes but no axis values, so `STAT` cannot name a
location. `instantiate-variable-font.py` then names each instance from the font's own named
instances (`fvar`). With no options it writes the 36 as `NotoSansDisplay-<Style>.ttf`:
`NotoSansDisplay-SemiCondensedBold.ttf`, and from the Italic file
`NotoSansDisplay-ExtraCondensedBoldItalic.ttf`. `fc-query` sees 36 distinct faces. One file took
under two minutes here, about three with `--woff2`.

Only a location that is one of the 36 gets a name. `--weights 400 700` writes
`NotoSansDisplay-Regular.ttf` and `NotoSansDisplay-Bold.ttf`, but `--weights 450` writes
`NotoSansDisplay-wght450.ttf`, whose names inside still read `Noto Sans Display Regular`. `--list`
shows beforehand which rule names each file.
