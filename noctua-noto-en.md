# Noctua Noto

*[Versão em português](noctua-noto-pt-BR.md)*

Base typeface for the projects, in two forms: the **plain Noto** families (variable, upstream from
Google Fonts) and the same families **patched with Nerd Fonts 3.4.0** — icon glyphs baked into the
text font, which removes the need for a separate icon font.

Files live in [`noctua-noto/`](noctua-noto/). Inventory taken on 2026-07-27; the numbers (sizes,
counts) describe that snapshot.

---

## 1. Inventory — 49 TTF (+ 49 matching WOFF2)

| group | count | variable? | which |
|---|---|---|---|
| **plain Noto** | **18** | ✅ `wght` 100–900; **14** of them also `wdth` 62.5–100 | Sans, Sans-Italic, Serif, Serif-Italic, Display, Display-Italic, Mono, Arabic, Armenian, Devanagari, Ethiopic, Georgian, Hebrew, Thai, JP, KR, SC, Emoji |
| **Nerd Font** patched | **27** | ❌ static | `NotoSans` and `NotoSansDisplay` (Light–Bold + italics), `NotoSerif` (Regular/Medium/Bold + italics), `NotoSansM` (Regular/Medium/Bold) |
| standalone | **4** | ❌ static | ColorEmoji (CBDT bitmap, 24 MB), Music, Math, Mongolian |

**Family names of the patched set** — what to write in CSS/QML/`pubspec` (read §5b before reaching
for Display):

| family | found by OS font lookup? |
|---|---|
| `NotoSans Nerd Font` | ✅ if the Noto variant of Nerd Fonts is installed |
| `NotoSerif Nerd Font` | ✅ likewise |
| `NotoSansM Nerd Font` | ✅ likewise — this is the **monospaced** one (`M` = Mono, the patcher's abbreviation) |
| `NotoSansDisplay Nerd Font` | ❌ **only by embedding the file** — see §5b |

<details>
<summary><b>The 18 variable fonts in detail</b> — axes, instances, sizes</summary>

| file | family | `wght` (min, **default**, max) | `wdth` | instances | TTF / WOFF2 |
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

All 18 carry `fvar` **plus `STAT` and named instances** (Thin, ExtraLight, Light, Regular, Medium,
SemiBold, Bold, ExtraBold, Black). Modern font managers enumerate each instance as a **separate
face** — meaning they already behave like an ordinary static family:

```console
$ fc-query --format='%{style} w=%{weight} var=%{variable}\n' NotoSans-VariableFont_wdth,wght.ttf
Regular w=80 var=False
Thin w=0 var=False
…
Black w=210 var=False
 w=[0 210] var=True          ← the variable face, on top of the 9 named ones
```

</details>

[`noctua-noto/licenses/`](noctua-noto/licenses/) holds the 20 licenses: SIL OFL per family, plus the
MIT of [Nerd Fonts](symbols-nerd-font-en.md) — the 27 patched files embed its glyphs.
**Redistribution requires shipping them alongside the fonts.**

---

## 2. Convert the variable fonts to static? **Not wholesale.**

Variable font support has been universal since 2017–18 (Chrome 62, Firefox 62, Safari 11, Edge 17,
FreeType 2.8.1, fontconfig 2.13, CoreText, DirectWrite, Qt 6, Flutter/Skia, HarfBuzz). It is not a
practical compatibility risk. Three concrete reasons to keep the variable files as the **master**:

1. **What projects usually name is already static.** The 27 `*NerdFont-*` files — the families that
   show up in CSS/QML — have no `fvar`, because the Nerd Fonts patcher (FontForge) **rejects
   variable fonts**. The split is already correct: the variable files are the unpatched complement,
   covering i18n scripts and arbitrary weights.
2. **Condensed exists ONLY as an axis.** In Sans, Serif, Mono, Arabic, Armenian, Devanagari,
   Ethiopic, Georgian, Hebrew and Thai the 9 named instances are **all `wdth=100`** — only `Display`
   publishes Condensed/SemiCondensed/ExtraCondensed as named instances (hence its 36). Flattening
   blindly throws Condensed away.
3. **You lose the intermediate weights** and gain nothing: 9 files where there was 1.

Generate static faces **on demand** with
[`instantiate-variable-font.py`](instantiate-variable-font.py), and only for the targets that need
them (§3).

---

## 3. Guide by target

<details open>
<summary><b>Web (browser)</b> — use the variable font directly</summary>

One file covers all 9 weights **and** the Condensed axis. The `@font-face` rule **must** declare the
ranges, otherwise the browser is stuck on the default instance:

```css
@font-face {
  font-family: "Noto Sans";
  src: url("NotoSans-VariableFont_wdth,wght.woff2") format("woff2-variations");
  font-weight:  100 900;      /* ⚠️ without this, JP/KR/SC/Hebrew render Thin — §5a */
  font-stretch: 62.5% 100%;   /* only on the 14 that have a wdth axis */
  font-display: swap;
}
```

**CJK requires subsetting.** `NotoSansSC` alone is 7.6 MB of WOFF2 — never load it whole. Slice it by
`unicode-range` with `pyftsubset` (ships with `fonttools`):

```bash
pyftsubset noctua-noto/NotoSansSC-VariableFont_wght.ttf \
  --unicodes="U+4E00-9FFF" --flavor=woff2 --layout-features="*" \
  --output-file=NotoSansSC-cjk.woff2
```

</details>

<details>
<summary><b>Flutter / mobile</b> — static faces are simpler</summary>

Flutter **cannot read WOFF2** → use TTF. Variable fonts do work (`FontVariation`), but `pubspec.yaml`
wants a `weight:` mapping per declared face. The path of least friction is to instantiate only the
weights you use and declare each file:

```bash
./instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 400 500 700
```

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

```bash
./instantiate-variable-font.py "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf" \
  --weights 300 400 500 600 700
nerd-font-patcher --complete noctua-noto/static/NotoSans-Bold.ttf
```

The 27 patched files here came from **Nerd Fonts 3.4.0**; use the same version to keep glyph coverage
consistent. To produce the WOFF2 files afterwards, see
[Converting TTF to WOFF2](convert-ttf-to-woff2-en.md).

</details>

---

## 4. Tools

At the root of this repository, generic (they work on any font) and documented via `--help`:

| script | what it does |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | variable → static. With no options it generates the *named instances* the font itself declares; `--list` shows the available axes and styles |
| [`rename-font-family.py`](rename-font-family.py) | align the family name recorded inside the files — this is what fixed §5b |

---

## 5. Pitfalls

### ⚠️ a) The default instance is Thin in `JP`, `KR`, `SC` and `Hebrew`

Those four have `wght` **default 100**, not 400 — `fc-query` literally reports `Thin,Regular` as the
first face. Anything that renders the default instance without pinning the axis gets **hairline
text**, and the browser then fabricates *fake bold* on top of Thin.

- **Web:** `font-weight: 100 900` in the `@font-face` rule (§3).
- **Instantiating:** `instantiate-variable-font.py` already handles it — it pins the axis and
  rewrites the name from the `STAT` table.

This is the **real** risk in this set — and one line fixes it. Converting nothing is required.

### ✅ b) Family naming of the patched set — aligned on 2026-07-27, with one caveat

The Nerd Fonts patcher abbreviates names, and whoever generates the files often renames them
afterwards. When the string does not match what the app asks for, name lookup falls back
**silently** — the text renders in a different font, with no error anywhere.

**What was done:** the 3 monospaced files were renamed from `NotoSansMono Nerd Font` to
**`NotoSansM Nerd Font`**, which is the patcher's own name — their original `UniqueID` already
recorded `NotoSansM Nerd Font Mono 3.4.0`. The files are now
`NotoSansMNerdFont-{Regular,Medium,Bold}.{ttf,woff2}`. The same string therefore works whether the
font is embedded or resolved by the OS. Verified that the design did not change: 14332 glyphs, a
cmap of 13900, and every advance at 600 (a single cell).

> ⚠️ **Caveat — `NotoSansDisplay Nerd Font` is not a name that exists outside these files.** The
> patcher **folds Display into the `NotoSans` family** (its original `UniqueID` still records
> `NotoSans Nerd Font Display 3.4.0`); the distinct name was assigned afterwards. Do not expect to
> find it installed — asking the OS for it lands on `NotoSans Nerd Font`, which is the **proportional
> text face**. Use it **only by embedding** the file, always with Sans in the fallback chain:
> ```css
> font-family: "NotoSansDisplay Nerd Font", "NotoSans Nerd Font", ui-sans-serif, sans-serif;
> ```

> ⚠️ None of this applies to the **variable** files: `NotoSansMono-VariableFont_wdth,wght.ttf` is the
> *unpatched* Noto Sans Mono, family `Noto Sans Mono` — the correct upstream name. Do not rename it.

### ⚠️ c) `NotoColorEmoji-Regular.ttf` is a bitmap font

24 MB of CBDT/CBLC — it does not scale like an outline, ignores CSS color, and older rasterizers
cannot read it. For monochrome vector emoji use `NotoEmoji-VariableFont_wght` (variable, `wght`
300–700).
