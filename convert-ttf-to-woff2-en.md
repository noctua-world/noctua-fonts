# Converting TTF to WOFF2

*[Versão em português](convert-ttf-to-woff2-pt-BR.md)*

WOFF2 is the web font format: the same TTF repackaged with **Brotli** compression plus a few
font-specific transforms. Decoded, a WOFF2 has the same outlines, hinting and name tables as its
TTF. The only table dropped is the digital signature (`DSIG`), which the Noctua Iosevka TTFs carry
empty. One flag can be lost, depending on the tool: see [Choosing a tool](#choosing-a-tool). In
this repository a WOFF2 is **15–56%** of the size of its TTF: about 15% for Noctua Iosevka, about
20% for its Nerd Font faces, and 23–56% for Noto and Symbols Nerd Font. It is the only format worth
serving from an `@font-face` today: every browser in use has supported it since 2016–18.

Every TTF in this repository already has its WOFF2. Read
[This repository's WOFF2 files](#this-repositorys-woff2-files) before converting one of them.

---

## Choosing a tool

There are two routes. Their files are not byte-identical: on the 135 Noctua Iosevka WOFF2, of about
1.7 MB each, their sizes differ by up to 5.5 KB. They also differ in one flag. `OVERLAP_SIMPLE`
marks a glyph whose contours may overlap, and some renderers use it to draw such a glyph
correctly. `woff2_compress` 1.0.2 drops it, and `woff2_decompress` 1.0.2 does not restore it when it
decodes a file that has it; `fonttools` keeps it both ways. (The WOFF2 library learned the flag in
March 2022, after 1.0.2, its last release and the one distributions package.) The Noctua Iosevka
TTFs set it on every glyph with contours, so for them prefer `fonttools`, as this repository does.
The Nerd Font, Noto and Symbols TTFs here do not set it, and both routes decode them to the same
font: pick whichever is already at hand.

| | `woff2_compress` | `fonttools` |
|---|---|---|
| what it is | Google's reference tool, the same code browsers use to decode | Python font manipulation library |
| input/output | one file at a time, output lands **next to the source**, no directory option | any input and output path |
| also does | `woff2_decompress` (WOFF2 → TTF), handy for validation | subsetting, instancing, renaming |
| dependency | system binary | Python packages `fonttools` and `brotli`, in a virtual environment |

<details>
<summary><b>Installing</b> — per distribution / system</summary>

**`woff2_compress`** (the package is usually called `woff2`):

| system | command |
|---|---|
| Arch, Manjaro | `sudo pacman -S woff2` |
| Debian, Ubuntu | `sudo apt install woff2` |
| Fedora | `sudo dnf install woff2-tools` |
| openSUSE | `sudo zypper install woff2` |
| macOS (Homebrew) | `brew install woff2` |
| NixOS / Nix (ephemeral shell) | `nix-shell -p woff2` |

RHEL 9 and 10 ship the WOFF2 library but not this command (checked on Rocky Linux). Use `fonttools`
there.

On **NixOS**, prefer the ephemeral shell over installing into a profile: this is a one-off tool. To
make it declarative, add `woff2` to `environment.systemPackages`.

**`fonttools`** needs **`brotli`** beside it. On its own, `fonttools` can **neither read nor write**
WOFF2: it stops with `ImportError: No module named brotli`. Install both in a virtual environment,
a private folder of Python packages:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

Why not a bare `pip install`: on Debian, Ubuntu, Arch and Homebrew, the system's Python belongs to
the package manager (PEP 668). Outside a virtual environment, pip stops with
`error: externally-managed-environment`. On Debian and Ubuntu, `python3 -m venv` also needs the
`python3-venv` package (`sudo apt install python3-venv`). The last line puts the environment's
`fonttools` on the `PATH` of this shell, so the commands below find it; run it again in each new
shell. In this repository, git already ignores `.venv/`. On Windows the environment's programs are
in `.venv\Scripts`: the install line is `.venv\Scripts\python -m pip install fonttools brotli`.

To get the fontTools commands without making a virtual environment yourself, use pipx. It keeps
them in an environment of their own:

```bash
pipx install 'fonttools[woff]'
```

The `woff` extra brings `brotli` with it. Keep the quotes: zsh, the default shell on macOS, reads
unquoted brackets as a file pattern and stops with `zsh: no matches found: fonttools[woff]`.

On **NixOS**, or anywhere with Nix, a one-off shell has both, with `fonttools` on the `PATH`:

```bash
nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])'
```

</details>

---

## Converting

### With `fonttools` — you control the destination

`-o` names the output file. Its folder must exist: `fonttools` does not create it and stops with
`FileNotFoundError`.

```bash
mkdir -p web
fonttools ttLib.woff2 compress -o web/MyFont-Regular.woff2 MyFont-Regular.ttf
```

A whole directory, several files at a time:

```bash
mkdir -p web
find . -maxdepth 1 -name '*.ttf' -print0 \
  | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" sh -c \
      'fonttools ttLib.woff2 compress -o "web/$(basename "$1" .ttf).woff2" "$1"' sh
```

`getconf _NPROCESSORS_ONLN` prints the number of CPUs online, on Linux and on macOS. `nproc` exists
only on Linux. Each file name reaches the inner `sh` as `$1`, so names with spaces or quotes are
safe.

### With `woff2_compress` — writes next to the source

The tool has a minimal interface: **one argument** and **no options**. Even `woff2_compress --help`
reads `--help` as a file name. It writes the WOFF2 beside the TTF, under the same name, and replaces
a file already there. There is no output-directory option, so the workflow is "compress, then move".

```bash
woff2_compress MyFont-Regular.ttf
```

That creates `MyFont-Regular.woff2` in the same folder. A whole directory, several files at a time,
then the move:

```bash
printf '%s\0' *.ttf | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" woff2_compress
mkdir -p web && mv *.woff2 web/
```

### Large batches

Each file is compressed on one CPU, with Brotli at its highest quality (11). One 10 MB Noctua
Iosevka face takes about **14 s** with `woff2_compress` and **21 s** with `fonttools`. To go faster,
convert several files at once (`-P`); one file cannot be spread over several CPUs. As a measure:
converting all 321 TTFs of this repository with `woff2_compress` on 16 CPUs took about 10 minutes.
Not every stored WOFF2 was written by it, though: see
[This repository's WOFF2 files](#this-repositorys-woff2-files).

If a batch is interrupted, **do not start over**. Both tools write the WOFF2 in one go, once its
compression is done, so a font stopped halfway has no WOFF2 yet. Convert only what is missing. For
the `woff2_compress` batch, before the move:

```bash
for f in *.ttf; do [ -f "${f%.ttf}.woff2" ] || printf '%s\0' "$f"; done \
  | xargs -0 -r -n 1 -P "$(getconf _NPROCESSORS_ONLN)" woff2_compress
```

For the `fonttools` batch, which writes into `web/`:

```bash
for f in *.ttf; do [ -f "web/${f%.ttf}.woff2" ] || printf '%s\0' "$f"; done \
  | xargs -0 -r -n 1 -P "$(getconf _NPROCESSORS_ONLN)" sh -c \
      'fonttools ttLib.woff2 compress -o "web/$(basename "$1" .ttf).woff2" "$1"' sh
```

`-r` stops GNU `xargs` from running the command once with no file when nothing is missing. The
macOS `xargs` accepts it, and never does that anyway. A WOFF2 cut short while it was being written
counts as present here; the length check below finds it.

---

## Validating

Run the first three checks in the folder that holds the WOFF2 files. They need no font tool.

```bash
ls *.woff2 | wc -l
```

The count must match the number of source TTFs.

```bash
for f in *.woff2; do
  [ "$(head -c4 "$f" | tr -d '\0')" = "wOF2" ] || echo "INVALID: $f"
done
```

Every valid WOFF2 starts with the 4 bytes `wOF2`. This finds an empty file, or one that is not
WOFF2 at all. `tr -d '\0'` drops zero bytes: a TTF starts with some, and bash warns about them.

```bash
for f in *.woff2; do
  od -An -tu1 -j8 -N4 "$f" 2>/dev/null \
    | awk -v size="$(wc -c < "$f")" '{ n = $1*16777216 + $2*65536 + $3*256 + $4 } END { exit !(NR && n == size) }' \
    || echo "SHORT: $f"
done
```

Bytes 8–11 of the header hold the length of the whole file. This finds a file cut short.

Decoding is the stronger check: a file cut short, and most damaged files, fail to decode. From
the folder above `web/`:

```bash
woff2_decompress web/MyFont-Regular.woff2
fonttools ttLib.woff2 decompress web/MyFont-Regular.woff2
```

Use either one. Both write the decoded font next to the WOFF2, as `web/MyFont-Regular.ttf`.
`woff2_decompress` **replaces** a file of that name, so never run it in the folder of the source
TTF. `fonttools` picks a free name instead (`MyFont-Regular#1.ttf`). Delete the decoded copy
afterwards.

Decoding is not proof that every byte is right: a single changed byte can still decode. Only a
checksum proves that, and this repository keeps one for each built font (see the last section).

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

If the font is **variable**, one `@font-face` covers every weight. Declare the axis range in
`font-weight`. `format("woff2")` is enough for a variable WOFF2:

```css
@font-face {
  font-family: "My Font";
  src: url("web/MyFont-Variable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}
```

⚠️ A variable font's **default instance** is not always Regular, and whatever draws the file
without setting its `wght` axis gets that instance. The declared range maps `font-weight` onto the
whole axis, so it does not depend on what a browser does without it.
[Noctua Noto](noctua-noto-en.md), §5a, has a real case: the default is Thin in JP, KR, SC and
Hebrew. Measured there in Chrome 150, JP and Hebrew drew at 400 and 700 even with no `font-weight`
in the rule. Other browsers were not measured.

---

## This repository's WOFF2 files

Each TTF here has a WOFF2 of the same name: in `noctua-iosevka/WOFF2/` and
`noctua-iosevka/WOFF2-nerdfonts/` for Noctua Iosevka, and beside the TTF for Noto and Symbols Nerd
Font. None of them is in git. They are assets of the release `v1.0.0` of
[noctua-world/noctua-fonts](https://github.com/noctua-world/noctua-fonts), as zip archives that
`font-archives.json` describes, so a fresh clone has none of these fonts. Fetch an archive, then
check what you have against the committed `SHA256SUMS`:

```bash
./font-archives.py fetch --archive noctua-noto-woff2.zip
./font-archives.py verify --allow-missing
```

With no `--archive`, `fetch` takes every archive that is missing a font: all 23 in a fresh clone.
Their names are in `font-archives.json`. Without the tool, the same check is
`sha256sum -c --ignore-missing SHA256SUMS` (Linux) or
`shasum -a 256 -c --ignore-missing SHA256SUMS` (macOS). Drop `--allow-missing` and
`--ignore-missing` once you have every archive: a missing font is then an error.

To rebuild one of these WOFF2 files from its TTF and still match `SHA256SUMS`, use the command that
wrote it:

- **the 135 in `noctua-iosevka/WOFF2/`:** `fonttools ttLib.woff2 compress`, which keeps the
  `OVERLAP_SIMPLE` flag of their TTFs. fontTools 4.61.1 with Brotli 1.2.0 reproduces them byte for
  byte; another version of either may write other bytes.
- **the 27 SemiExtended faces in `noctua-iosevka/WOFF2-nerdfonts/`:** these were written by
  `fix-nerd-semiextended-names.py`, through fontTools, keeping the WOFF2 header version (1.0) of
  the `woff2_compress` files it replaced. The script only rewrites a face that is not fixed yet,
  so it cannot rebuild these from their TTFs. `fonttools ttLib.woff2 compress`, followed by
  setting the header version back to 1.0 (bytes 24–27 of the file), reproduces them byte for byte:

  ```bash
  fonttools ttLib.woff2 compress -o web/MyFont-SemiExtended.woff2 MyFont-SemiExtended.ttf
  printf '\000\001\000\000' | dd of=web/MyFont-SemiExtended.woff2 bs=1 seek=24 conv=notrunc
  ```
- **the other 159** (the rest of `WOFF2-nerdfonts/`, Noto and Symbols Nerd Font):
  `woff2_compress` 1.0.2.

Rebuilt with another of these commands, a file decodes to the same font (a Noctua Iosevka face
without its `OVERLAP_SIMPLE` flag, if `woff2_compress` wrote it), but `./font-archives.py verify`
reports it as a mismatch. Keep the fetched file.

If a changed font is meant to stay, `./font-archives.py manifest` rewrites `SHA256SUMS`. It hashes
the fonts present, and it refuses to run while a font that `SHA256SUMS` lists is missing, since the
rewrite would drop it: fetch every archive first. Pass `--remove-missing` only for a font removed or
renamed on purpose. Check that `./font-archives.py verify` passes without `--allow-missing` before
you change the font. After one rebuilt font, `manifest` must report
`0 added, 0 removed, 1 changed`.

A new hash in `SHA256SUMS` also needs new archives. `fetch` checks every font of an archive against
`SHA256SUMS` and refuses the whole archive on a difference, so the `v1.0.0` archive that holds the
old font can no longer be fetched. `./font-archives.py pack` writes all 23 archives into `dist/`.
They become the assets of a new release, and its tag replaces `v1.0.0` in `font-archives.json`.
