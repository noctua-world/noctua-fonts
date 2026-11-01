# noctua-fonts

*[Versão em português](README-pt-BR.md)*

Where the Noctua typefaces were made: the Noctua Iosevka build plan, the Noto families patched
with Nerd Fonts icons, the icon-only Symbols Nerd Font, the notes for converting fonts to WOFF2,
two Python tools, and every font built, stored with Git LFS. It is kept as the record of how each
font was made, and to rebuild one.

> **Where to put it, and where to start an agent.** This repository belongs to a workspace: clone
> it only inside `noctua-workspace/repos/`, and start your agents only from the workspace root —
> never from inside this directory. An agent started here cannot see the sibling repositories or
> the shared documents, so it guesses.
>
> Nothing here is built or consumed by the other projects; the fonts they ship were copied out by
> hand. Read a font's own document before using anything from it.

---

## ⚠️ This repository uses Git LFS

The font files (`*.ttf` and `*.woff2`, about 4 GB in all) are stored with
[Git LFS](https://git-lfs.com). **Install Git LFS before cloning.** Cloning without it succeeds
with no error at all, but every font arrives as a text pointer of about 130 bytes, like this:

```
version https://git-lfs.github.com/spec/v1
oid sha256:b4a1df...
size 1004120
```

### 1. Install Git LFS

<details>
<summary>per operating system</summary>

```bash
sudo pacman -S git-lfs             # Arch, Manjaro
sudo apt install git-lfs           # Debian, Ubuntu
sudo dnf install git-lfs           # Fedora, RHEL
sudo zypper install git-lfs        # openSUSE
brew install git-lfs               # macOS (Homebrew)
winget install GitHub.GitLFS       # Windows
```

On **NixOS**, add `git-lfs` to `environment.systemPackages` and rebuild. Do **not** rely on
`nix-shell -p git-lfs`: the clean and smudge filters are written into the repository's config, so
every `git add` and `git checkout` fails once the binary leaves `$PATH`.

</details>

### 2. Enable it — once per machine

```bash
git lfs install
```

This writes the `lfs` filters into `~/.gitconfig`. Without it, step 3 still produces pointer
files.

### 3. Clone, inside the workspace

```bash
cd noctua-workspace/repos
git clone <repository-url> noctua-fonts
cd noctua-fonts
```

This downloads every font. To avoid that, see *Clone without downloading everything* below.

### 4. Check that it worked

```bash
git lfs fsck                                  # expected: "Git LFS fsck OK"
git lfs ls-files | awk '$2 == "-"' | wc -l    # fonts still pointers; expected: 0
```

In `git lfs ls-files`, `*` marks a font whose content is present and `-` one that is still a
pointer; `git lfs ls-files --size` adds each font's size. A real font is hundreds of kilobytes, a
pointer about 130 bytes:

```bash
ls -l noctua-noto/NotoSansMath-Regular.ttf     # about 1 MB when correct
```

<details>
<summary><b>Already cloned, and got text files of about 130 bytes?</b></summary>

Nothing is lost — the pointers know what to fetch. Install Git LFS (step 1), then:

```bash
cd noctua-fonts
git lfs install --local      # --local: this repository only; ~/.gitconfig is left alone
git lfs pull
```

`git status` comes back clean, and the fonts arrive at full size.

</details>

<details>
<summary><b>Clone without downloading everything</b></summary>

Skip the font download, then fetch only the folders you need:

```bash
cd noctua-workspace/repos
GIT_LFS_SKIP_SMUDGE=1 git clone <repository-url> noctua-fonts   # pointers only, under 1 MB
cd noctua-fonts
git lfs install --local

git lfs pull --include="noctua-noto/**"            # about 200 MB
git lfs pull --include="noctua-iosevka/WOFF2/**"   # about 220 MB, web only
```

Anything not pulled stays a pointer, and you can pull it at any time.

</details>

---

## Fonts

| font | files | docs |
|---|---|---|
| **Noctua Iosevka** — monospaced, for terminals and code | [`noctua-iosevka/`](noctua-iosevka/) | [EN](noctua-iosevka-en.md) · [pt-BR](noctua-iosevka-pt-BR.md) |
| **Noctua Noto** — text and UI, with Nerd Fonts icons | [`noctua-noto/`](noctua-noto/) | [EN](noctua-noto-en.md) · [pt-BR](noctua-noto-pt-BR.md) |
| **Symbols Nerd Font** — icons only, as a fallback for any text font | [`symbols-nerd-font/`](symbols-nerd-font/) | [EN](symbols-nerd-font-en.md) · [pt-BR](symbols-nerd-font-pt-BR.md) |

Noctua Iosevka's build plan, `noctua-iosevka/private-build-plans.toml`, is the source of truth
for that typeface; its document explains how to rebuild it.

## Tools

Font-agnostic; run either with `--help`. Both need `pip install fonttools brotli`.

| script | what it does |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | variable font → static instances |
| [`rename-font-family.py`](rename-font-family.py) | rewrite the family name recorded inside font files |

Converting TTF to WOFF2 for the web: [EN](convert-ttf-to-woff2-en.md) ·
[pt-BR](convert-ttf-to-woff2-pt-BR.md)

---

> Fonts are redistributed under their own licenses — see each font's folder.
