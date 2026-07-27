# noctua-fonts

*[Versão em português](README-pt-BR.md)*

Typefaces used across the projects, with their documentation and tooling.

---

## ⚠️ This repository uses Git LFS

The font files (`*.ttf`, `*.woff2` — 642 files, ~2 GB) are stored with
[Git LFS](https://git-lfs.com). **Install Git LFS before cloning.** Cloning without it succeeds
without any error, but every font arrives as a ~130-byte text file like this:

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
`nix-shell -p git-lfs`: the clean/smudge filters are written into the repository's config, so every
`git add` and `git checkout` fails once the binary leaves `$PATH`.

</details>

### 2. Enable it — once per machine

```bash
git lfs install
```

Writes the `lfs` filters into `~/.gitconfig`. Without this step, step 3 still produces pointer files.

### 3. Clone

```bash
git clone <repository-url> noctua-fonts
cd noctua-fonts
```

Downloads ~2 GB. To avoid that, see *Clone without downloading everything* below.

### 4. Check it worked

```bash
git lfs ls-files | wc -l     # expected: 642
git lfs fsck                 # expected: "Git LFS fsck OK"
```

A real font is hundreds of kilobytes; a pointer is ~130 bytes:

```bash
ls -l noctua-noto/NotoSansMath-Regular.ttf     # ~1.0 MB = correct
```

<details>
<summary><b>Already cloned and got ~130-byte text files?</b></summary>

Nothing is lost — the pointers know what to fetch. Install Git LFS (step 1), then:

```bash
cd noctua-fonts
git lfs install --local      # --local: only this repo, leaves ~/.gitconfig alone
git lfs pull
```

`git status` should come back clean and the fonts arrive at full size.

</details>

<details>
<summary><b>Clone without downloading everything</b> (2 GB)</summary>

Skip the font download, then fetch only the folder you need:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone <repository-url> noctua-fonts   # ~700 KB
cd noctua-fonts
git lfs install --local

git lfs pull --include="noctua-noto/**"            # ~144 MB
git lfs pull --include="noctua-iosevka/WOFF2/**"   # ~218 MB, web only
```

Anything not pulled stays a pointer, and you can pull it later at any time.

</details>

---

## Fonts

| font | files | docs |
|---|---|---|
| **Noctua Iosevka** — monospaced, for terminals and code | [`noctua-iosevka/`](noctua-iosevka/) | [EN](noctua-iosevka-en.md) · [pt-BR](noctua-iosevka-pt-BR.md) |
| **Noctua Noto** — text and UI, with Nerd Fonts icons | [`noctua-noto/`](noctua-noto/) | [EN](noctua-noto-en.md) · [pt-BR](noctua-noto-pt-BR.md) |
| **Symbols Nerd Font** — icons only, as a fallback for any text font | [`symbols-nerd-font/`](symbols-nerd-font/) | [EN](symbols-nerd-font-en.md) · [pt-BR](symbols-nerd-font-pt-BR.md) |

## Tools

Font-agnostic; run with `--help`. Require `pip install fonttools brotli`.

| script | what it does |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | variable font → static instances |
| [`rename-font-family.py`](rename-font-family.py) | rewrite the family name recorded inside font files |

Converting TTF to WOFF2 for the web: [EN](convert-ttf-to-woff2-en.md) ·
[pt-BR](convert-ttf-to-woff2-pt-BR.md)

---

> Fonts are redistributed under their own licenses — see each font's folder.
