# Noctua Iosevka

*[Versão em português](noctua-iosevka-pt-BR.md)*

An in-house **monospaced** typeface for terminals, editors and code. It is a custom build of
[Iosevka](https://github.com/be5invis/Iosevka) — not a fork: nothing was redrawn. What exists is a
deliberate selection among the variants Iosevka already offers, plus a remapped width ladder.

Files live in [`noctua-iosevka/`](noctua-iosevka/).

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

The italic is a **true cursive** (distinct shapes), not a slanted roman — the oblique is the slanted
one. Both exist separately.

</details>

---

## 3. Installing

<details open>
<summary><b>Linux</b> (fontconfig)</summary>

Per user, no root needed:

```bash
mkdir -p ~/.local/share/fonts/NoctuaIosevka
cp noctua-iosevka/TTF-nerdfonts/*.ttf ~/.local/share/fonts/NoctuaIosevka/
fc-cache -f
```

For a system-wide install use `/usr/local/share/fonts/` instead (needs root). To also get the
icon-free family, repeat with `TTF/` into its own folder — the names are distinct and do not clash.

Confirm what became available:

```bash
fc-list : family | grep -i noctua | sort -u
fc-match "NoctuaIosevka Nerd Font Mono"
```

**On declarative distributions** (NixOS, Guix), do not copy into `$HOME`: point the package manager
at the files. On NixOS a local package plus `fonts.packages` is the way — installing by copy works,
but disappears on the next rebuild that prunes the profile.

</details>

<details>
<summary><b>macOS</b></summary>

Copy the `.ttf` files into `~/Library/Fonts/` (per user), or install them through Font Book.

</details>

<details>
<summary><b>Windows</b></summary>

Select all the `.ttf` files, right-click and choose "Install" (or "Install for all users").

</details>

<details>
<summary><b>Web</b></summary>

Use the `.woff2` files already generated in `WOFF2/` and `WOFF2-nerdfonts/`. See
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

**Italic** — confirm cursive shapes, clearly distinct from both roman and oblique. Code comments are
the natural test.

---

## 5. Rebuilding from scratch

<details>
<summary><b>Full rebuild guide</b> — Iosevka build + Nerd Fonts patch + re-hinting</summary>

The pipeline:

```
private-build-plans.toml
        │
        ▼
   Iosevka build  ──►  TTF (hinted, plain)
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
                final fonts
```

The core idea: the patch runs on the **unhinted** output and `ttfautohint` runs **afterwards** —
yielding the rendering quality of an official build, with the icons inside.

### Step 1 — Prerequisites

**Node.js** (with **npm**), **git**, **ttfautohint** and **Docker**.

```bash
# Arch — ttfautohint comes from the AUR, and pacman aborts the ENTIRE transaction
# if any package in the list is missing. Keep the commands separate:
sudo pacman -S --needed nodejs npm git
yay -S ttfautohint

# Debian / Ubuntu
sudo apt install nodejs npm git ttfautohint docker.io

# Fedora
sudo dnf install nodejs npm git ttfautohint docker

# NixOS / Nix — ephemeral shell with everything:
nix-shell -p nodejs git ttfautohint docker
```

**Docker** is used only for the Nerd Fonts patch: the `nerdfonts/patcher` image bundles FontForge and
`font-patcher`, so neither has to be installed on the system.

```bash
sudo systemctl enable --now docker.service
sudo usermod -aG docker "$USER"   # requires a new login to take effect
```

On NixOS this is declarative: `virtualisation.docker.enable = true;` plus the user in the `docker`
group.

### Step 2 — The build plan

The entire design lives in one declarative file:
[`noctua-iosevka/private-build-plans.toml`](noctua-iosevka/private-build-plans.toml). It is the
project's source of truth.

> **The filename is not negotiable.** Iosevka's build system looks exclusively for
> `private-build-plans.toml` at the **root of the cloned repository**. No other name or location
> works. To keep a canonical copy under its own name, symlink it into the root.

### Step 3 — Clone and pin Iosevka

The TOML alone does not guarantee reproducibility: variant names change between versions. The
complete recipe is **TOML + exact repository version**.

```bash
git clone --depth 1 --branch <release-tag> https://github.com/be5invis/Iosevka.git iosevka
cd iosevka
ln -s /path/to/private-build-plans.toml private-build-plans.toml
npm install
```

If you must use `main`, record the exact commit (`git rev-parse --short HEAD`) in a comment at the
top of the TOML — a recorded commit is still reproducible; "main, some day" is not.

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

The loop is resumable — each finished font gets a stamp in `.done/`:

```bash
cd /path/to/workdir   # where TTF-Unhinted/ lives
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

### Step 7 — Final validation

```bash
for f in final/*.ttf; do
  fc-query "$f" >/dev/null || echo "CORRUPT: $f"
done
```

Total silence means 135 structurally sound files. If any fails (rare, tied to problematic FontForge
versions in the image), repeat Step 5 pinning an earlier tag — for example `nerdfonts/patcher:3.3.6`
— and redo Steps 6 and 7.

Then install (§3) and run the acceptance tests (§4).

</details>

<details>
<summary><b>Known and harmless issues</b></summary>

**Odd names on the SemiExtended width.** The patcher's renaming algorithm fragments the name
"SemiExtended", exiling those faces into per-weight mini-families (e.g.
`NoctuaIosevkaBoldSemi Nerd Font Mono Extended`). It is cosmetic collateral: the main family holds
the other four widths cleanly, and SemiExtended remains installed and usable under the mangled names.
To fix them, [`rename-font-family.py`](rename-font-family.py) rewrites the names.

**Guarding against memory exhaustion.** For heavy builds on limited machines, an early OOM killer
(`earlyoom` or `systemd-oomd`) is worth installing: it turns the worst case from "frozen system, hold
the power button" into "process killed, message in the log". For containers of unknown appetite,
`--memory=4g --memory-swap=4g` on `docker run` imposes a hard ceiling — the container dies, the
machine survives.

</details>

---

## 6. License

**SIL OFL 1.1** — [`noctua-iosevka/licenses/`](noctua-iosevka/licenses/), © 2015-2026 Renzhi Li.
**Redistribution requires shipping it alongside the fonts**, and that includes serving them from a
website.

Two consequences worth knowing:

- **Iosevka's OFL reserves no font name.** The copyright line carries no *"with Reserved Font Name"*
  clause, which is precisely what makes it legitimate for this custom build to ship under its own
  name. Had upstream reserved the name, a renamed derivative would need written permission.
- **This build is a Modified Version**, so OFL §5 applies: it must stay under the OFL and cannot be
  relicensed. That obligation does **not** reach documents or sites that merely *use* the font — only
  redistribution of the font software itself.
