# Noctua Iosevka

*[Versão em português](noctua-iosevka-pt-BR.md)*

An in-house **monospaced** typeface for terminals, editors and code. It is a custom build of
[Iosevka](https://github.com/be5invis/Iosevka) — not a fork: nothing was redrawn. What exists is a
deliberate selection among the variants Iosevka already offers, plus a remapped width ladder.

The fonts belong in [`noctua-iosevka/`](../noctua-iosevka/), but git does not hold them: they come
from the release archives (§3). The specimen site shows the typeface:
<https://noctua-world.github.io/noctua-fonts/>, in Portuguese at
<https://noctua-world.github.io/noctua-fonts/pt-BR/>.

---

## 1. Two families

| family | where to use it | folders |
|---|---|---|
| **Noctua Iosevka** | editors and apps that do not need icons | `TTF/`, `WOFF2/` |
| **NoctuaIosevka Nerd Font Mono** | daily terminal use — every [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) icon baked in | `TTF-nerdfonts/`, `WOFF2-nerdfonts/` |

The names are distinct on purpose: the two **coexist when installed**, with no conflict. Each folder
holds **135 files** = 9 weights × 5 widths × 3 slopes.

> ⚠️ The string that goes into terminal and editor configuration is
> **`NoctuaIosevka Nerd Font Mono`**, character for character. Confirm with
> `fc-match "NoctuaIosevka Nerd Font Mono"` — name lookup fails silently, handing you a different
> font with no error at all.

---

## 2. What sets it apart

<details open>
<summary><b>A normal width of 600/1000</b> — the highest-impact decision</summary>

Stock Iosevka is famously narrow (half-em), which hurts how distinguishable glyphs are. The "Normal"
here uses a **0.6 em** advance, the same as JetBrains Mono.

The five widths (456, 548, **600**, 658, 720) were chosen to map honestly onto the CSS/OpenType width
classes once 600 = 100%:

| width | shape | CSS class |
|---|---|---|
| Condensed | 456 | `condensed` |
| SemiCondensed | 548 | `semi-condensed` |
| **Normal** | **600** | `normal` |
| SemiExtended | 658 | `semi-expanded` |
| Extended | 720 | `expanded` |

</details>

<details>
<summary><b>Glyph variants</b> — ambiguities attacked by shape, not by context</summary>

| classic ambiguity | how it is resolved |
|---|---|
| `0` `O` `o` | oval dotted zero — without colliding with `Ø`/`∅` |
| `i` `l` `1` `I` | "1" with top and bottom serifs, tailed serifed "l", serifed "I" |
| `Z` `2` `7` | "Z" with a horizontal crossbar |
| `a` `o` `α` | double-storey "a" |
| `rn` `m` | tailed "m" |
| `Q` `O` `0` | crossing-tailed "Q" |

The `motion-serifed` variants, spread across upper and lower case, give the family a consistent
**semi-serifed** identity, with anchor points that help peripheral recognition.

</details>

<details>
<summary><b>Three build decisions that are not accidental</b></summary>

**`spacing = "term"`** narrows symbols to the terminal cell while **keeping** ligatures in the file as
an optional feature (toggled per application via OpenType). The alternative, `fixed`, would strip
ligatures and even whole codepoints at compile time — one fewer option, set in stone.

**`noCvSs = false`** exports the `cv##`/`ss##` features, allowing glyph variants to be swapped at
runtime in any OpenType-aware editor — including stylistic set `ss14`, which puts on JetBrains Mono
shapes on demand.

**`exportGlyphNames = true`** preserves glyph names in the file, a compatibility requirement for the
Nerd Fonts patcher (and for terminal features such as Kitty's).

</details>

<details>
<summary><b>Coverage</b> — weights, widths and slopes</summary>

No `weights` or `slopes` section is declared in the build plan, because the desired selection matches
Iosevka's default: **all nine weights** (100–900) and **all three slopes** (Upright, Italic, Oblique).
Only `widths` is declared, because that ladder was remapped.

The italic is not just the slanted roman — the oblique is that. Both lean 9°, and the italic draws
its own shapes where it matters: 466 of the 7,580 code points differ, among them `C c e i t` with
their accented forms and `ß æ œ ſ` in Latin, `ε ι τ ϲ` in Greek, and most of lowercase Cyrillic
(measured on 2026-11-01 by comparing the decomposed outlines of the Italic and Oblique faces). The
rest are shared. Both exist separately.

</details>

---

## 3. Installing

A clone of this repository holds none of these fonts. They are assets of the release
[`v1.0.0`](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0), in zip archives that
[`font-archives.json`](../tools/font-archives.json) describes, and git keeps
[`SHA256SUMS`](../SHA256SUMS) instead: one SHA-256 per font. Twenty of the 23 archives hold Noctua
Iosevka, one per family, format and width. Each has the 27 faces of its width (9 weights × 3 slopes)
and the licence files of §6.

| archive | holds | download, each |
|---|---|---|
| `noctua-iosevka-nerd-font-ttf-<width>.zip` | NoctuaIosevka Nerd Font Mono as TTF, the one to install for a terminal | about 145 MiB (about 410 MiB unpacked) |
| `noctua-iosevka-nerd-font-woff2-<width>.zip` | the same faces as WOFF2, for the web | about 81 MiB (about the same unpacked) |
| `noctua-iosevka-ttf-<width>.zip` | Noctua Iosevka, the family without icons, as TTF | about 84 MiB (about 285 MiB unpacked) |
| `noctua-iosevka-woff2-<width>.zip` | the same faces as WOFF2 | about 44 MiB (about the same unpacked) |

`<width>` is `normal`, `condensed`, `semicondensed`, `semiextended` or `extended`. The Nerd Font in
the normal width:

```bash
git clone https://github.com/noctua-world/noctua-fonts.git
cd noctua-fonts
./tools/font-archives.py fetch --archive noctua-iosevka-nerd-font-ttf-normal.zip
./tools/font-archives.py verify --allow-missing
```

`--archive` takes several names. Every width of the Nerd Font, as TTF:

```bash
./tools/font-archives.py fetch --archive \
  noctua-iosevka-nerd-font-ttf-normal.zip \
  noctua-iosevka-nerd-font-ttf-condensed.zip \
  noctua-iosevka-nerd-font-ttf-semicondensed.zip \
  noctua-iosevka-nerd-font-ttf-semiextended.zip \
  noctua-iosevka-nerd-font-ttf-extended.zip
```

`font-archives.py` needs Python 3.9 or later and nothing else (on Windows, run it as `python
tools/font-archives.py …`). `fetch` writes a font only when its SHA-256 matches `SHA256SUMS`, and an
archive is all or nothing: one that fails leaves the tree as it was. `verify --allow-missing` checks
the fonts that are present and only counts the missing ones. The fonts land in the folders of §1:
`noctua-iosevka/TTF-nerdfonts/`, `noctua-iosevka/TTF/`, `noctua-iosevka/WOFF2-nerdfonts/` and
`noctua-iosevka/WOFF2/`.

Without a clone, download an archive from the release, such as
<https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/noctua-iosevka-nerd-font-ttf-normal.zip>.
Its paths start at the repository root: it unpacks to `noctua-iosevka/TTF-nerdfonts/`, with the
licence files in `noctua-iosevka/licenses/`. Run the commands below from the folder you unpacked it
in.

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

Per user, no root needed:

```bash
mkdir -p ~/.local/share/fonts/NoctuaIosevka
cp noctua-iosevka/TTF-nerdfonts/*.ttf ~/.local/share/fonts/NoctuaIosevka/
fc-cache -f
```

For a system-wide install use `/usr/local/share/fonts/` instead (needs root). To also get the
icon-free family, fetch its `noctua-iosevka-ttf-<width>.zip` archives and repeat with `TTF/` into
its own folder — the names are distinct and do not clash.

Confirm what became available:

```bash
fc-list : family | grep -i noctua | sort -u
fc-match "NoctuaIosevka Nerd Font Mono"
```

**On declarative distributions** (NixOS, Guix), do not copy into `$HOME`: let the package manager
install the fonts. On NixOS a local package made from the release archives, plus `fonts.packages`,
is the way. Installing by copy into `~/.local/share/fonts` also works, but it stays outside the
system configuration, so another machine built from that configuration will not have the fonts.

</details>

<details>
<summary><b>macOS</b></summary>

Copy the `.ttf` files of `noctua-iosevka/TTF-nerdfonts/` into `~/Library/Fonts/` (per user), or
install them through Font Book.

</details>

<details>
<summary><b>Windows</b></summary>

Select all the `.ttf` files of `noctua-iosevka\TTF-nerdfonts\`, right-click and choose "Install"
(or "Install for all users").

</details>

<details>
<summary><b>Web</b></summary>

Use the `.woff2` files of the WOFF2 archives, which land in `WOFF2/` and `WOFF2-nerdfonts/`. See
[Converting TTF to WOFF2](convert-ttf-to-woff2-en.md) for the `@font-face` rule and for regenerating
the files.

⚠️ Do not declare all 135 files on a page — only the weights/styles the page actually uses.

</details>

> **Restart the application completely.** Many programs discover fonts only when the *process*
> starts — and single-instance apps stay alive with every window closed. If the font does not show
> up, confirm the process actually died (`pgrep <app>`) before suspecting anything else.

> **If your environment manages fonts centrally, use its mechanism.** Environments that control the
> system font through their own tooling tend to inject configuration that overrides the user's,
> sometimes with counter-intuitive precedence — in Ghostty, for instance, files pulled in via
> `config-file` are processed *last*, beating any key set in your own config regardless of line
> order.

---

## 4. Acceptance tests

**Typographic** — at small sizes and in all three slopes, every character in these groups must be
unmistakable:

```
il1I|   0O8B   5SZ2   3 5 S   g q 9
```

**Icons** — in a terminal using the font, each symbol must render and occupy exactly **one** cell:

```bash
printf '  \n'
```

**Italic** — confirm its own shapes, distinct from the oblique: `c e i t` in Latin, most lowercase
Cyrillic. Code comments are the natural test.

---

## 5. Rebuilding from scratch

<details>
<summary><b>Full rebuild guide</b> — Iosevka build + Nerd Fonts patch + re-hinting + WOFF2 +
SemiExtended fix</summary>

The pipeline:

```
private-build-plans.toml
        │
        ▼
   Iosevka build  ──►  TTF (hinted, plain)  ──►  WOFF2 (fontTools)
        │
        └──►  TTF-Unhinted
                    │
                    ▼
         Nerd Fonts patch (Docker)
                    │
                    ▼
              ttfautohint
                    │
                    ▼
         WOFF2 (woff2_compress)
                    │
                    ▼
         SemiExtended name fix
                    │
                    ▼
                final fonts
```

The core idea: the patch runs on the **unhinted** output and `ttfautohint` runs **afterwards** —
yielding the rendering quality of an official build, with the icons inside.

### Step 1 — Prerequisites

**Node.js** 18 or later (with **npm**), **git**, **ttfautohint** and **Docker** build the fonts;
**woff2_compress** and **Python 3.11** or later with **fontTools** and **brotli** make the WOFF2
and fix the names (Steps 8 to 10); `fc-query`, from **fontconfig**, checks the files in Steps 4
and 7. The build plan pins ttfautohint at **1.8.4**, its latest release, for both hinting passes:
`ttfautohint --version` must print `ttfautohint 1.8.4`. The plan pins no Node.js version;
Iosevka v34.7.0 asks for 18.0.0 or later.

**Arch.** ttfautohint comes from the AUR, and pacman aborts the ENTIRE transaction if any package
in the list is missing, so keep the two commands separate:

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

**NixOS / Nix**, an ephemeral shell with the build tools:

```bash
nix-shell -p nodejs git ttfautohint docker woff2
```

Check `node --version` before building: Ubuntu 22.04 ships Node.js 12, too old for this build, so
take 18 or later from another source there (NodeSource or nvm, for instance). Debian 12 and
Ubuntu 24.04 ship 18.

**Docker** is used only for the Nerd Fonts patch: the `nerdfonts/patcher` image bundles FontForge and
`font-patcher`, so neither has to be installed on the system.

```bash
sudo systemctl enable --now docker.service
sudo usermod -aG docker "$USER"
```

The group change takes effect at your next login. On NixOS this is declarative:
`virtualisation.docker.enable = true;` plus the user in the `docker` group. On macOS, Docker
Desktop takes the place of both commands: install it and start it once.

**Python**, for Steps 8 to 10: install fontTools and brotli in a virtual environment at the root of
your clone of this repository (git ignores `.venv/`). A bare `pip install` fails on the system
Python of Debian, Ubuntu and Arch, and on Homebrew's, which mark it as externally managed (PEP 668);
[Converting TTF to WOFF2](convert-ttf-to-woff2-en.md) has the details, Windows included. The
`python3` that makes the environment must be 3.11 or later, because the tests that
`./tools/check.py` runs in Step 10 need it: an older one, such as Ubuntu 22.04's 3.10 or the 3.9 of
macOS's command-line tools, runs the tools but not the tests.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

The last line puts the environment's `python3` and `fonttools` on the `PATH` of this shell; run it
again in each new shell. On NixOS,
`nix-shell -p woff2 'python3.withPackages(ps: [ps.fonttools ps.brotli])'` opens a shell with
`woff2_compress`, fontTools and brotli instead, for Steps 8 to 10.

### Step 2 — The build plan

The entire design lives in one declarative file:
[`noctua-iosevka/private-build-plans.toml`](../noctua-iosevka/private-build-plans.toml). It is the
project's source of truth. Its header, in TOML comments, pins the toolchain to rebuild the fonts
with: Iosevka v34.7.0 (commit `6828cb0bd569992bb19565a5e448540de3b50541`), the Nerd Fonts patcher
image `nerdfonts/patcher:4.26.0` by digest, and ttfautohint 1.8.4. Changing any pin means
rebuilding every face: the 135 plain and the 135 Nerd Font ones, TTF and WOFF2.

> **The filename is not negotiable.** Iosevka's build system looks exclusively for
> `private-build-plans.toml` at the **root of the cloned repository**. No other name or location
> works. To keep a canonical copy under its own name, symlink it into the root.

### Step 3 — Clone and pin Iosevka

The TOML alone does not guarantee reproducibility: variant names change between versions. The
complete recipe is **TOML + exact repository version**, and the plan's header records it: tag
`v34.7.0`, commit `6828cb0bd569992bb19565a5e448540de3b50541`.

Clone it outside this repository, next to it for instance: run the commands below from the folder
that holds your `noctua-fonts/`, and `iosevka/` lands beside it. Steps 5 and 8 call that clone
`/path/to/iosevka`.

```bash
git clone --depth 1 --branch v34.7.0 https://github.com/be5invis/Iosevka.git iosevka
cd iosevka
git rev-parse HEAD
```

The last line must print `6828cb0bd569992bb19565a5e448540de3b50541`: a tag can be moved, a commit
cannot. Then link the plan in and install the build's dependencies:

```bash
ln -s /path/to/noctua-fonts/noctua-iosevka/private-build-plans.toml private-build-plans.toml
npm install
```

Do not build from `main` or from another tag. That is a change of pin: record the new tag and
commit in the plan's header and in `EXPECTED_PINS` in
[`tests/test_licences.py`](../tests/test_licences.py), rebuild every face, and update the Material
Design fingerprints there if the new faces draw the icons differently (Step 7).

### Step 4 — Build

One command produces **both** outputs: the `ttf::` target generates the unhinted instances as an
intermediate stage and runs `ttfautohint` over them.

```bash
npm run build -- --jCmd=4 ttf::NoctuaIosevka
```

> ⚠️ **About `--jCmd=N`, read before running.** The build parallelizes across every CPU thread by
> default, and peak RAM scales almost linearly with concurrent jobs. On memory-limited machines the
> default can **lock the system up**. Start conservative (`--jCmd=2`), watch consumption, and raise it
> only if there is headroom; `--jCmd=1` is the floor (serial build). 135 instances take a long time in
> any configuration — treat it as a leave-it-running task.

**The build is safely interruptible.** Its build system keeps a journal with a dependency graph: a
task is only recorded as complete once it genuinely finishes. Ctrl-C and re-running the same command
resumes where it left off. Worst case, in-flight work is redone.

Outputs land in `dist/NoctuaIosevka/TTF/` (hinted, plain) and `dist/NoctuaIosevka/TTF-Unhinted/` (raw
material for the patch). Validate before moving on — silence means success:

```bash
for f in dist/NoctuaIosevka/TTF/*.ttf dist/NoctuaIosevka/TTF-Unhinted/*.ttf; do
  fc-query "$f" >/dev/null || echo "CORRUPT: $f"
done
```

### Step 5 — Nerd Fonts patch

**Why the unhinted output:** `font-patcher` runs on FontForge, and that round trip can degrade or
discard the TrueType hinting. Patching the unhinted version and running `ttfautohint` *afterwards* —
the same tool the official build uses — restores hinting equivalent to an official build. Nothing is
lost.

**Why one file per container:** the image's entrypoint scans `/in` and patches **everything it
finds**, with internal parallelism sized to the CPU — which can exhaust RAM with dozens of concurrent
FontForge processes. Mounting a single file per run forces serial processing: constant, predictable
memory use, at the cost of time (hours for 135 fonts).

> ⚠️ **Never** mount the whole directory at `/in` and pass a filename as an argument: the name becomes
> an extra argument to *every* internal invocation, and they all fail.

**Why the image is named by tag and digest:** `nerdfonts/patcher` with no tag is `latest`, a newer
patcher (4.27.3 on 2026-11-01) that stamps Nerd Fonts 3.5.1 and does not reproduce these faces. The
`4.26.0` tag has been re-pushed once already, so the plan pins its digest as well; with a digest in
the name, Docker pulls by the digest. That image stamps `Nerd Fonts 3.4.0`, as the shipped faces
do. It is not the very build that patched them: that was the first `4.26.0` build, which can no
longer be pulled. The plan's header says how it was compared with the shipped faces. Patching one
face of each width reproduces the Material Design icons of all 135, and two faces, re-hinted as in
Step 6, came out with every table but `head` and `name` identical; that test patched the hinted
TTF, not `TTF-Unhinted` as below, and ran the image's `linux/amd64` variant. The digest names an
index of several platforms, so on an arm64 host (Apple Silicon, ARM Linux) Docker pulls the `arm64`
variant, which nobody compared. There, adding `--platform linux/amd64` to `docker run` runs the
compared one, if Docker can emulate amd64 (Docker Desktop can).

The loop is resumable — each finished font gets a stamp in `.done/`. It runs in
`dist/NoctuaIosevka/` of the Iosevka clone, the folder that holds `TTF-Unhinted/`, and so do
Steps 6 and 7:

```bash
cd /path/to/iosevka/dist/NoctuaIosevka
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

What each piece does: `--mono` forces icons to occupy exactly one terminal cell (without it,
double-width glyphs get clipped in several terminals); `--complete` injects every icon set; `-u`
ensures the output belongs to your user rather than root; `:ro` mounts the input read-only.

**Expected messages that are not errors:** the warning `Internal Error: Your version of iconv does
not support the "Mac Roman" encoding` is known noise from the image's FontForge builds and does not
affect modern fonts. An occasional warning about the FontForge version "producing unusable fonts in
some cases" is covered by the validation in Step 7 — let the problem prove it exists before reacting
to it.

### Step 6 — Re-hinting

Gives the patched fonts back the hinting that the FontForge round trip discarded. Fast (seconds per
file):

```bash
for f in patched/*.ttf; do
  ttfautohint --no-info "$f" "final/$(basename "$f")" || echo "FAILED: $f"
done
```

`--no-info` keeps ttfautohint's own note out of the version string (name ID 5), which then reads
`Version 34.7.0;Nerd Fonts 3.4.0`, as in the shipped faces.

### Step 7 — Validate the patched fonts

```bash
for f in final/*.ttf; do
  fc-query "$f" >/dev/null || echo "CORRUPT: $f"
done
```

Total silence means 135 structurally sound files. If one fails (rare, tied to problematic FontForge
versions in the image), delete the stamp of the file it came from in `.done/` and run Steps 5 to 7
again: the loop redoes only that file. Keep the pinned image. Docker Hub tags `nerdfonts/patcher`
with font-patcher's own version (4.x), never with the Nerd Fonts version it stamps, and other
images patch other icons: 4.25.0 draws 132 Material Design icons differently. Moving to another
image, `nerdfonts/patcher:4.27.3` for instance, is a change of pin: record its tag, its digest and
the Nerd Fonts version it stamps in the plan's header and in `EXPECTED_PINS` in
[`tests/test_licences.py`](../tests/test_licences.py), rebuild every face (Step 2), and update the
Material Design fingerprints in that file: `PINNED_PATCHER_MDI`, and `MDI_ICON_COUNT` if the count
changes.

### Step 8 — Copy into the repository and make the WOFF2

The rest runs from the root of your clone of this repository, in the virtual environment of
Step 1: the first two lines below see to both. On NixOS, run the block in the Nix shell of
Step 1 instead, without the `. .venv/bin/activate` line. The four Noctua Iosevka folders must start
empty: Step 9 never overwrites a file, so an older SemiExtended face would stop it. A fresh clone
has none of them; in a clone that fetched them, move them out of the repository first. Copy the
plain faces and the patched ones in:

```bash
cd /path/to/noctua-fonts
. .venv/bin/activate
mkdir -p noctua-iosevka/TTF noctua-iosevka/TTF-nerdfonts
cp /path/to/iosevka/dist/NoctuaIosevka/TTF/*.ttf noctua-iosevka/TTF/
cp /path/to/iosevka/dist/NoctuaIosevka/final/*.ttf noctua-iosevka/TTF-nerdfonts/
```

Then make each folder's WOFF2 with the tool that wrote this repository's own;
[Converting TTF to WOFF2](convert-ttf-to-woff2-en.md#this-repositorys-woff2-files) says which
wrote which, and with which versions. The versions matter less here than the tool: a rebuilt TTF
already differs from the shipped one, so its WOFF2 cannot match the shipped WOFF2 whatever the
version. To use the versions that wrote the shipped files anyway, install
`fonttools==4.61.1 brotli==1.2.0` into the environment of Step 1.

`noctua-iosevka/WOFF2/` comes from `TTF/` through fontTools, which keeps the `OVERLAP_SIMPLE` flag
that the Iosevka TTFs set on every glyph with contours:

```bash
mkdir -p noctua-iosevka/WOFF2
find noctua-iosevka/TTF -maxdepth 1 -name '*.ttf' -print0 \
  | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" sh -c \
      'fonttools ttLib.woff2 compress -o "noctua-iosevka/WOFF2/$(basename "$1" .ttf).woff2" "$1"' sh
```

`noctua-iosevka/WOFF2-nerdfonts/` comes from `TTF-nerdfonts/` through `woff2_compress` 1.0.2,
which writes next to its input, hence the move:

```bash
mkdir -p noctua-iosevka/WOFF2-nerdfonts
printf '%s\0' noctua-iosevka/TTF-nerdfonts/*.ttf \
  | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" woff2_compress
mv noctua-iosevka/TTF-nerdfonts/*.woff2 noctua-iosevka/WOFF2-nerdfonts/
```

Each folder now holds 135 files. The 27 SemiExtended WOFF2 of `WOFF2-nerdfonts/` are only the
input of Step 9, which writes them again from the fixed TTFs.

### Step 9 — Fix the SemiExtended faces

The patcher misreads the SemiExtended width (Iosevka spells it "Semi-Extended"): it glues "Semi" and
the weight onto the family and keeps "Extended" as the style. Each SemiExtended weight then lands in
a family of its own, such as `NoctuaIosevkaBoldSemi Nerd Font Mono`, style `Extended`, and asking
for `NoctuaIosevka Nerd Font Mono` at semi-expanded width silently hands you the nearest other
width. On the Bold weight it also clears the bold bits (OS/2 `fsSelection` bit 5, `head` `macStyle`
bit 0) that the Bold faces of every other width carry.
[`fix-nerd-semiextended-names.py`](../tools/fix-nerd-semiextended-names.py) repairs those 27 faces,
as TTF and as WOFF2: 54 files. Preview first; `--dry-run` writes nothing:

```bash
./tools/fix-nerd-semiextended-names.py --dry-run noctua-iosevka/TTF-nerdfonts noctua-iosevka/WOFF2-nerdfonts
```

It must report 54 files as `would fix` and the other 216 as `skipped`. Then the real run:

```bash
./tools/fix-nerd-semiextended-names.py noctua-iosevka/TTF-nerdfonts noctua-iosevka/WOFF2-nerdfonts
```

On Windows, run it as `python tools/fix-nerd-semiextended-names.py …`. It rewrites name IDs 1, 2, 3,
4, 6, 16 and 17 to the convention the patcher used for the other widths (family `NoctuaIosevka Nerd
Font Mono`, style `SemiExtended Bold` and so on), sets the bold bits exactly on the Bold weight, and
gives each file its siblings' pattern of name,
`NoctuaIosevkaNerdFontMono-SemiExtended[Weight][Slope]`. In a TTF, every other table is copied byte
for byte. It handles the TTFs first, whatever the order of the arguments, and writes each
SemiExtended WOFF2 again from its fixed TTF, so the pair stays identical in content. A TTF takes
seconds, a WOFF2 one to two minutes: the whole run takes close to an hour.

It refuses, and leaves untouched, what it cannot recognise for certain. Among those cases: a
semi-expanded Nerd Font Mono face whose names match neither the patcher's pattern nor the fixed
one, a face whose other style bits differ from its siblings', a face carrying name IDs 18, 20, 21,
22 or 25 or records of one ID that disagree between platforms, a face with a DSIG signature, a file
whose type does not match its extension, a symbolic link, and a file already present at the new
name. A `.otf` or `.woff` file named or matched, a directory with no `.ttf` or `.woff2` in it and a
pattern that matches nothing are errors too; `--help` lists every case. It then exits with
status 1. Other faces, such as the other widths or fonts that are not Nerd Fonts, it reports as
`skipped` and leaves alone. Run again over fixed faces, it reports them as `already fixed` and
changes nothing.

### Step 10 — Record the new fonts

A rebuilt face differs in bytes from the shipped one, at least in the time stamp of its `head`
table, so `./tools/font-archives.py verify` reports it as a `MISMATCH`. To keep the rebuild, rewrite
`SHA256SUMS`. `manifest` refuses while a font that `SHA256SUMS` lists is missing, so fetch the
other three archives first:

```bash
./tools/font-archives.py fetch --archive noctua-noto-ttf.zip noctua-noto-woff2.zip symbols-nerd-font.zip
./tools/font-archives.py manifest
./tools/check.py --release
```

`manifest` reports what it added, removed and changed: after a rebuild under the same pins it must
report `0 added, 0 removed`, with the Noctua Iosevka fonts among the changed. `check.py --release`
runs the tests (which check name ID 5 and the Material Design icons against the pins), the site
check, a strict `verify` and `font-archives.py list` (every font in exactly one archive).

The specimen site's subset fonts, under `site/public/`, are cut from these faces: regenerate them as
[`site/README.md`](../site/README.md) explains. New hashes need new archives and a new release:
[Maintaining the release](README.md#maintaining-the-release) has the whole procedure, the new tag
included, and the end of
[This repository's WOFF2 files](convert-ttf-to-woff2-en.md#this-repositorys-woff2-files) says why.

Then install the new faces from `noctua-iosevka/TTF-nerdfonts/` (§3) and run the acceptance tests
(§4).

</details>

<details>
<summary><b>Known issues</b></summary>

**The SemiExtended width, fixed here.** The patcher's renaming algorithm fragments the name
"SemiExtended", exiling those faces into per-weight mini-families (e.g. `NoctuaIosevkaBoldSemi Nerd
Font Mono Extended`), and it clears the bold bits of the Bold ones. The 27 SemiExtended faces of the
release archives, TTF and WOFF2, were repaired on 2026-11-01 by
[`fix-nerd-semiextended-names.py`](../tools/fix-nerd-semiextended-names.py), names and bold bits
both: they now sit in the main family with the other four widths, and `fc-match 'NoctuaIosevka Nerd
Font Mono:width=113:weight=200'` returns `NoctuaIosevkaNerdFontMono-SemiExtendedBold.ttf`. A rebuild
must run the tool again: Step 9.

**Guarding against memory exhaustion.** For heavy builds on limited machines, an early OOM killer
(`earlyoom` or `systemd-oomd`) is worth installing: it turns the worst case from "frozen system, hold
the power button" into "process killed, message in the log". For containers of unknown appetite,
`--memory=4g --memory-swap=4g` on `docker run` imposes a hard ceiling — the container dies, the
machine survives.

</details>

---

## 6. License

**SIL OFL 1.1**, Iosevka's licence —
[`noctua-iosevka/licenses/OFL-Iosevka.txt`](../noctua-iosevka/licenses/OFL-Iosevka.txt), © 2015-2026
Renzhi Li. **Redistribution requires shipping it alongside the fonts**, and that includes serving
them from a website. Every Noctua Iosevka archive carries it.

Two consequences worth knowing:

- **Iosevka's OFL reserves no font name.** The copyright line carries no *"with Reserved Font Name"*
  clause, which is precisely what makes it legitimate for this custom build to ship under its own
  name. Had upstream reserved the name, a renamed derivative would need written permission.
- **This build is a Modified Version**, so OFL §5 applies: it must stay under the OFL and cannot be
  relicensed. That obligation does **not** reach documents or sites that merely *use* the font — only
  redistribution of the font software itself.

**The Nerd Font faces also carry the Nerd Fonts icons.** Nerd Fonts ships them with its MIT license,
kept in
[`noctua-iosevka/licenses/LICENSE-NerdFontsSymbolsOnly.txt`](../noctua-iosevka/licenses/LICENSE-NerdFontsSymbolsOnly.txt),
byte for byte the one in [`symbols-nerd-font/licenses/`](../symbols-nerd-font/licenses/); the Nerd
Font archives carry it beside the OFL. The icon sets that Nerd Fonts gathers keep their own upstream
licences, and not all of them are MIT: Codicons and Font Awesome are under CC BY 4.0, Material
Design Icons under Apache 2.0, Pomicons and Weather Icons under the SIL Open Font License 1.1, and
Font Logos under the Unlicense. The [`LICENSE`](../LICENSE) at the root of this repository sums it
up and names Nerd Fonts' lists of every set. The rest of each patched face stays under the OFL.

That root `LICENSE` puts this repository's own content (its tools and their tests, the
documentation, the build plan and the site) under MIT OR Apache-2.0. It does not reach the fonts.
