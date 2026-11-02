# noctua-fonts

*[Versão em português](README-pt-BR.md)*

Where the Noctua typefaces were made: the Noctua Iosevka build plan, the Noto families (four of
them also patched with Nerd Fonts icons), the icon-only Symbols Nerd Font, the notes for
converting fonts to WOFF2, the Python tools that instantiate, rename, repair and publish the
fonts, with their tests, and a specimen site for Noctua Iosevka. It is kept as the record of how
each font was made, and to rebuild one. The 642 built fonts are not in git: they are assets of a
GitHub release, and git keeps the SHA-256 of each one. The only fonts in git are the specimen
site's small subset fonts, under `site/public/`.

These documents, with the scripts in [`tools/`](../tools/), are what the repository holds besides
the fonts. Every command below runs from the repository root.

> **Where to put it, and where to start an agent.** This repository belongs to a workspace: clone
> it only inside `noctua-workspace/repos/`, and start your agents only from the workspace root —
> never from inside this repository. An agent started in it cannot see the sibling repositories or
> the shared documents, so it guesses.
>
> Nothing here is built or consumed by the other projects; the fonts they ship were copied out by
> hand. Read a font's own document before using anything from it.
>
> To use the fonts, none of this applies: clone the repository anywhere, as below.

---

## Getting the fonts

A fresh clone has none of the built fonts. The 642 built fonts (TTF and WOFF2, about 4.2 GiB) are
assets of the release [`v1.0.0`](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0),
as 23 zip archives that [`font-archives.json`](../tools/font-archives.json) describes, and git keeps
[`SHA256SUMS`](../SHA256SUMS) instead: one SHA-256 per font.
[`font-archives.py`](../tools/font-archives.py) downloads the archives and checks every font against
`SHA256SUMS`. It needs Python 3.9 or later and nothing else.

Every archive, about 1.9 GiB to download:

```bash
git clone https://github.com/noctua-world/noctua-fonts.git
cd noctua-fonts
./tools/font-archives.py fetch
./tools/font-archives.py verify
```

Only some archives, by name:

```bash
./tools/font-archives.py fetch --archive noctua-noto-woff2.zip symbols-nerd-font.zip
./tools/font-archives.py verify --allow-missing
```

`./tools/font-archives.py list` prints the names of the 23 archives, each with how many of its fonts
are present, and `font-archives.json` says what each one holds:

| archive | holds | download, each |
|---|---|---|
| `noctua-iosevka-ttf-<width>.zip` | Noctua Iosevka, the 27 faces of one width, as TTF | about 84 MiB |
| `noctua-iosevka-woff2-<width>.zip` | the same faces as WOFF2 | about 44 MiB |
| `noctua-iosevka-nerd-font-ttf-<width>.zip` | its Nerd Font build, NoctuaIosevka Nerd Font Mono, 27 faces as TTF | about 145 MiB |
| `noctua-iosevka-nerd-font-woff2-<width>.zip` | the same faces as WOFF2 | about 81 MiB |
| `noctua-noto-ttf.zip` | Noctua Noto, 49 TTF | about 79 MiB |
| `noctua-noto-woff2.zip` | Noctua Noto, 49 WOFF2 | about 58 MiB |
| `symbols-nerd-font.zip` | Symbols Nerd Font and Symbols Nerd Font Mono, as TTF and WOFF2 | about 5 MiB |

`<width>` is `normal`, `condensed`, `semicondensed`, `semiextended` or `extended`. Every archive
also carries the licence files of its fonts.

`fetch` writes a font only when its SHA-256 matches `SHA256SUMS`, so a wrong or tampered download
can make it fail, never install a different font. Each archive is all or nothing: one that fails
leaves the tree as it was. An archive whose fonts are all present and correct is not downloaded
again, and a font present with another hash (your own rebuild, say) is never replaced unless you
pass `--force`. Without it, the archive that holds such a font is refused as a whole, before it is
downloaded, so its missing fonts are not fetched either; the other archives still are, and `fetch`
ends with exit status 1. `verify` checks that every font `SHA256SUMS` lists is present and
matches, and that every font present is listed; `--allow-missing` checks only the fonts present
and counts the missing ones. On Windows, run the tool through Python:
`python tools/font-archives.py fetch`.

### Without Python

Download the archives you want from the
[release page](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0), or from
`https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/` followed by the archive's
name, into a folder outside the repository (`~/Downloads` below). On macOS, Safari unpacks a zip
it downloads and removes the zip, unless *Open “safe” files after downloading* is off in its
General settings; `curl` keeps the zip as it is, as in
`curl -L -o ~/Downloads/noctua-noto-ttf.zip https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/noctua-noto-ttf.zip`.

The paths inside every zip start at the repository root (`noctua-noto/…`, `noctua-iosevka/TTF/…`),
so unpack it from there, then check the fonts against `SHA256SUMS`. `unzip -n` never overwrites a
file: each archive also holds licence files that git already has, and a plain `unzip` stops to ask
about them.

On Linux:

```bash
unzip -n ~/Downloads/noctua-noto-ttf.zip
sha256sum -c --ignore-missing SHA256SUMS
```

On macOS:

```bash
unzip -n ~/Downloads/noctua-noto-ttf.zip
shasum -a 256 -c --ignore-missing SHA256SUMS
```

Every font must be reported `OK`. `--ignore-missing` skips the fonts of the archives you did not
unpack; once you have all 23, drop it, and a missing font is an error too. The release also
carries a file named `SHA256SUMS`, with the hashes of the zips themselves. It is not the
repository's `SHA256SUMS`, which lists the fonts: never save it over that one. On Windows, use
`font-archives.py`, above.

---

## Fonts

| font | folder | docs |
|---|---|---|
| **Noctua Iosevka** — monospaced, for terminals and code | [`noctua-iosevka/`](../noctua-iosevka/) | [EN](noctua-iosevka-en.md) · [pt-BR](noctua-iosevka-pt-BR.md) |
| **Noctua Noto** — text and UI, in many scripts; four families also with Nerd Fonts icons | [`noctua-noto/`](../noctua-noto/) | [EN](noctua-noto-en.md) · [pt-BR](noctua-noto-pt-BR.md) |
| **Symbols Nerd Font** — icons only, as a fallback for any text font | [`symbols-nerd-font/`](../symbols-nerd-font/) | [EN](symbols-nerd-font-en.md) · [pt-BR](symbols-nerd-font-pt-BR.md) |

Noctua Iosevka's build plan,
[`noctua-iosevka/private-build-plans.toml`](../noctua-iosevka/private-build-plans.toml), is the
source of truth for that typeface. It also pins the toolchain that built it: Iosevka v34.7.0, the
Nerd Fonts patcher image by digest, and ttfautohint 1.8.4. The typeface's document explains how to
rebuild it ([§5](noctua-iosevka-en.md#5-rebuilding-from-scratch)).

## Specimen site

Noctua Iosevka has a specimen site, in English at <https://noctua-world.github.io/noctua-fonts/>
and in Portuguese at <https://noctua-world.github.io/noctua-fonts/pt-BR/>. It is the
`site/public/` folder of `main`, which
[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) deploys to GitHub Pages on every
push that changes it. `site/public/` is generated: the source is the rest of
[`site/`](../site/), `site/build.py` writes the pages, and `site/subset-fonts.py` the subset fonts
they use. Never edit `site/public/` by hand. [`site/README.md`](../site/README.md) explains how
the site is built and checked.

## Tools

Run each one with `--help` for its full usage; the three that rewrite fonts need fontTools
installed even for that.

| script | what it does | needs |
|---|---|---|
| [`instantiate-variable-font.py`](../tools/instantiate-variable-font.py) | variable font → static instances: its named instances, or the weights, widths and axis values you give | fontTools; brotli for WOFF2 |
| [`rename-font-family.py`](../tools/rename-font-family.py) | rewrites the family name recorded inside font files, and their file names; a problem it can foresee refuses the whole batch before any font is touched | fontTools; brotli for WOFF2 |
| [`fix-nerd-semiextended-names.py`](../tools/fix-nerd-semiextended-names.py) | gives the SemiExtended faces of a Nerd Fonts Mono build back their family and bold bits, which the patcher gets wrong for that width | fontTools; brotli for WOFF2 |
| [`font-archives.py`](../tools/font-archives.py) | fetches and verifies the fonts; for a release, rewrites `SHA256SUMS` and packs the archives | Python 3.9 or later, standard library only |
| [`check.py`](../tools/check.py) | runs every check of the repository (see [Checking](#checking)) | Python 3.11 or later, with fontTools and brotli (without them it runs nothing) |
| [`readme-art.py`](../tools/readme-art.py) | draws the animated title and the button of the repository's README, into [`.github/readme/`](../.github/readme/), from the outlines of the built fonts | fontTools, and the Noctua Iosevka fonts fetched |

Install fontTools and brotli in a virtual environment, at the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

The last line puts the environment's Python first on the `PATH` of this shell, so `./tools/check.py`
and the tools find fontTools; run it again in each new shell. Git ignores `.venv/`. The tools run on
Python 3.9 or later, but the tests that `./tools/check.py` runs need 3.11 or later (they read the
build plan with `tomllib`), so make the environment with such a `python3`. A bare `pip install`
fails on the system Python of Debian, Ubuntu, Arch and Homebrew, which mark it as externally managed
(PEP 668), and on Debian and Ubuntu `python3 -m venv` also needs the `python3-venv` package. On
Windows: `python -m venv .venv`, then `.venv\Scripts\python -m pip install fonttools brotli`, and
run each script with the environment's Python, as in `.venv\Scripts\python tools/check.py`. That
needs no activation, so it works in cmd.exe and PowerShell alike; PowerShell refuses
`.venv\Scripts\activate` unless its execution policy allows scripts. With Nix, the shell under
*Installing* in [Converting TTF to WOFF2](convert-ttf-to-woff2-en.md#choosing-a-tool) has both
packages.

Converting TTF to WOFF2 for the web: [EN](convert-ttf-to-woff2-en.md) ·
[pt-BR](convert-ttf-to-woff2-pt-BR.md). Which command wrote each WOFF2 here, and how to rebuild one
so that it still matches `SHA256SUMS`:
[This repository's WOFF2 files](convert-ttf-to-woff2-en.md#this-repositorys-woff2-files).

## Checking

Run `./tools/check.py` before every commit:

```bash
./tools/check.py
```

It runs, in order, the test suite; `site/build.py --check`, which fails when `site/public/` differs
from what `site/` generates; and `./tools/font-archives.py verify --allow-missing`, which fails when
a font present does not match `SHA256SUMS` or is not listed there, while a missing font is not an
error. It needs Python 3.11 or later, with fontTools and brotli (see [Tools](#tools)): without them
it runs no step at all, says what is missing and exits with status 1. Otherwise every step runs even
when an earlier one fails, and the exit status is 0 only when all of them pass. `./tools/check.py
--release` also requires every font in `SHA256SUMS` to be present and every font to belong to
exactly one archive (`./tools/font-archives.py list`): run it before packing a release.

GitHub Actions runs the same check on each push to `main` and each pull request
([`.github/workflows/check.yml`](../.github/workflows/check.yml)): `check.py` on Linux, macOS and
Windows, with Python 3.11 and 3.14 and the fontTools and brotli this repository was made with, and
once more with the newest Python, fontTools and brotli; and every test but `tests/test_licences.py`,
which needs 3.11, on Python 3.9, the oldest the tools support. When a release is published,
[`.github/workflows/release-assets.yml`](../.github/workflows/release-assets.yml) downloads its 23
archives on the three systems and checks every font, with `font-archives.py` and with the
`sha256sum` and `shasum` commands above.

## Maintaining the release

For whoever maintains the repository. A font change (a face rebuilt, a font added, removed or
renamed) needs a new release:

1. Before changing anything, fetch every archive and check that the tree is complete:

   ```bash
   ./tools/font-archives.py fetch
   ./tools/font-archives.py verify
   ```

2. Change the fonts. A font added or renamed must fall in exactly one archive of
   `tools/font-archives.json`. If the change touches Noctua Iosevka, also rebuild the specimen
   site's subset fonts, which are cut from it, as [`site/README.md`](../site/README.md) explains.
3. Rewrite `SHA256SUMS` with `./tools/font-archives.py manifest`. It refuses while a font
   `SHA256SUMS` lists is missing from the tree, since the rewrite would drop it; pass
   `--remove-missing` only for a font removed or renamed on purpose. It prints what it added,
   removed and changed: check that this is what you meant.
4. Change the release tag from the current one, `v1.0.0`, to the new release's (`v1.1.0` in the
   example below) everywhere it is written: `"tag"` in `tools/font-archives.json`, and the
   documents in `docs/` that name it (both READMEs, the three font documents and the conversion
   notes, in both languages). The specimen site reads the tag from `tools/font-archives.json`:
   regenerate `site/public/` with `python3 site/build.py`, as
   [`site/README.md`](../site/README.md) explains, and `./tools/check.py` fails until you do. No
   check compares the documents, though. This command lists every place but `site/public/`, this
   step included:

   ```bash
   git grep -n -F v1.0.0 -- ':(exclude)site/public'
   ```

5. Run `./tools/check.py --release`.
6. Run `./tools/font-archives.py pack`. It writes the zips and a `SHA256SUMS` of them into `dist/`,
   which git ignores. It leaves any other file there alone, and step 8 attaches everything in
   `dist/`: delete any other file first.
7. Commit the change, `SHA256SUMS` and `tools/font-archives.json` included, and push it.
8. Tag that commit with a signed tag, push the tag, and create the release from it with every file
   in `dist/` attached. With the GitHub CLI, after the push of step 7:

   ```bash
   git tag -s v1.1.0 -m v1.1.0
   git push origin v1.1.0
   gh release create v1.1.0 --verify-tag dist/*
   ```

   The tag is signed like the commits, so `git verify-tag v1.1.0` checks it once the signer's
   public SSH key is in the file that gpg.ssh.allowedSignersFile names, as for
   `git verify-commit`. `--verify-tag` makes gh refuse to run unless that tag is already on
   GitHub; without it, a mistyped tag would make GitHub create an unsigned one on whatever commit
   is the latest of the default branch. In a terminal, gh asks for a title and release notes
   before it creates the release. Publishing it starts
   [`release-assets.yml`](../.github/workflows/release-assets.yml), which downloads the 23 archives
   on Linux, macOS and Windows and checks every font: wait for it to pass.

Why a new tag: `fetch` refuses an archive unless it holds exactly the fonts that
`font-archives.json` assigns to it from `SHA256SUMS`, and its licence files, and it refuses the
whole archive when a font it must write does not have the SHA-256 listed there. Once a font
changes, or is added, removed or renamed, the current release's archive that it belongs to no
longer matches. `fetch` takes every archive from the one tag in `font-archives.json`, so the new
release must carry all 23, which `pack` writes. Replacing the assets of a published release instead
would break every checkout of an earlier commit, whose `SHA256SUMS` and `font-archives.json` still
name the old fonts and that release. Leave every published release as it is.

## Licence

The repository's own content — the scripts and their tests, the documents, the Noctua Iosevka build
plan, and the specimen site's source with the pages generated from it — is licensed under either the
[MIT license](../licenses/LICENSE-MIT) or the [Apache License 2.0](../licenses/LICENSE-APACHE), at
your option (`MIT OR Apache-2.0`, see [`LICENSE`](../LICENSE)). Unless you explicitly state
otherwise, any contribution you intentionally submit for inclusion is licensed the same way, without
any additional terms or conditions.

The fonts are not covered by it. Every font file (`*.ttf`, `*.woff2`), the site's subset fonts
included, stays under its family's licence. The texts are in each font folder's `licenses/`, and
every archive carries those of the fonts it holds:

| fonts | licence | text |
|---|---|---|
| Noctua Iosevka, a custom build of Iosevka | SIL Open Font License 1.1 | [`noctua-iosevka/licenses/OFL-Iosevka.txt`](../noctua-iosevka/licenses/OFL-Iosevka.txt) |
| Noctua Noto | SIL Open Font License 1.1 | [`noctua-noto/licenses/`](../noctua-noto/licenses/), one `OFL-*.txt` per family |
| Symbols Nerd Font, and the Nerd Fonts icons inside the patched faces | shipped by the Nerd Fonts project with its MIT license; each icon set keeps its own licence | [`symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt`](../symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt), copied into [`noctua-iosevka/licenses/`](../noctua-iosevka/licenses/) and [`noctua-noto/licenses/`](../noctua-noto/licenses/) |

Not every icon set is MIT: Codicons and Font Awesome are under CC BY 4.0, Material Design Icons
under Apache 2.0, Pomicons and Weather Icons under the SIL Open Font License 1.1, and Font Logos
under the Unlicense. The rest of each patched face stays under its family's OFL.
[`LICENSE`](../LICENSE) sets all of this out and names the Nerd Fonts lists that give every icon set
with its source and licence.
