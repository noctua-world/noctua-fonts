# Converting TTF to WOFF2

*[Versão em português](convert-ttf-to-woff2-pt-BR.md)*

WOFF2 is the web font format: the same TTF repackaged with **Brotli** compression plus a few
font-specific transforms. **Nothing is lost** — glyphs, hinting and name tables survive intact, and
the file typically drops to **20–45%** of its original size. It is the only format worth serving from
an `@font-face` today: every browser in use has supported it since 2016–18.

---

## Choosing a tool

There are two routes, and both produce equivalent files. Pick whichever is already at hand.

| | `woff2_compress` | `fonttools` |
|---|---|---|
| what it is | Google's reference tool, the same code browsers use to decode | Python font manipulation library |
| input/output | one file at a time, output lands **next to the source**, no directory option | anything, fully controllable |
| also does | `woff2_decompress` (WOFF2 → TTF), handy for validation | subsetting, instancing, renaming |
| dependency | system binary | `pip install fonttools brotli` |

<details>
<summary><b>Installing</b> — per distribution / system</summary>

**`woff2_compress`** (the package is usually called `woff2`):

```bash
sudo pacman -S woff2                      # Arch, Manjaro
sudo apt install woff2                    # Debian, Ubuntu
sudo dnf install woff2-tools              # Fedora, RHEL
sudo zypper install woff2                 # openSUSE
brew install woff2                        # macOS (Homebrew)
nix-shell -p woff2                        # NixOS / Nix (ephemeral shell)
```

On **NixOS**, prefer the ephemeral shell over installing into a profile — this is a one-off tool. To
make it declarative, add `woff2` to `environment.systemPackages`.

**`fonttools`** (identical on every system):

```bash
pip install fonttools brotli              # brotli is NOT optional for WOFF2
pipx install fonttools[woff]              # isolated alternative
nix-shell -p python3Packages.fonttools python3Packages.brotli   # NixOS / Nix
```

⚠️ `fonttools` on its own can **neither read nor write** WOFF2: it fails with
`ImportError: No module named brotli`. Always install both.

</details>

---

## Converting

### With `fonttools` — you control the destination

```bash
# one file, output wherever you want
fonttools ttLib.woff2 compress -o web/MyFont-Regular.woff2 MyFont-Regular.ttf

# a whole directory, in parallel
mkdir -p web
find . -maxdepth 1 -name '*.ttf' -print0 \
  | xargs -0 -P "$(nproc)" -I{} sh -c \
      'fonttools ttLib.woff2 compress -o "web/$(basename "{}" .ttf).woff2" "{}"'
```

### With `woff2_compress` — writes next to the source

The tool has a minimal interface: **one argument** and **no options**. There is no output-directory
flag, so the workflow is "compress, then move":

```bash
woff2_compress MyFont-Regular.ttf         # creates MyFont-Regular.woff2 in the same folder

# parallel batch
ls *.ttf | xargs -P "$(nproc)" -n 1 woff2_compress
mkdir -p web && mv *.woff2 web/
```

### Large batches

Compression is single-threaded per file and Brotli runs at maximum level — expect **tens of seconds
per font** on large files. Parallelize across files (`-P`); do not expect internal parallelism.

If a batch is interrupted, **do not start over**: conversion is deterministic, so just build the list
of what is missing and run only that.

```bash
for f in *.ttf; do [ -f "${f%.ttf}.woff2" ] || echo "$f"; done \
  | xargs -P "$(nproc)" -n 1 woff2_compress
```

---

## Validating

Two cheap checks catch truncation and missing files:

```bash
# 1. count — must match the number of source TTFs
ls *.woff2 | wc -l

# 2. signature — every valid WOFF2 starts with the 4 bytes "wOF2"
for f in *.woff2; do
  [ "$(head -c4 "$f")" = "wOF2" ] || echo "INVALID: $f"
done
```

For full proof of a single file, run the reverse — a corrupt file would fail:

```bash
woff2_decompress MyFont-Regular.woff2                    # → .ttf
fonttools ttLib.woff2 decompress MyFont-Regular.woff2    # equivalent
```

---

## Using it on the web

```css
@font-face {
  font-family: "My Font";
  src: url("web/MyFont-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

Repeat per weight/style **actually used**. In a large family (dozens or hundreds of files), declaring
everything is counterproductive: the browser only downloads what the page references, but each rule
still costs parsing time, and it is easy to point at a weight nobody uses by accident.

If the font is **variable**, prefer a single `@font-face` with axis ranges — it covers every weight at
once, and the format string becomes `woff2-variations`:

```css
@font-face {
  font-family: "My Font";
  src: url("web/MyFont-Variable.woff2") format("woff2-variations");
  font-weight: 100 900;
  font-display: swap;
}
```

⚠️ Without declared ranges, the browser is stuck on the variable font's **default instance** — which
is not always Regular. See [Noctua Noto](noctua-noto-en.md), §5a, for a real case where the default
is Thin and the result is hairline text with fake bold layered on top.
