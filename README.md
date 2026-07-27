# noctua-fonts

Typefaces used across the projects, with their documentation and tooling.
*Tipografias usadas nos projetos, com documentação e ferramentas.*

---

## ⚠️ This repository uses Git LFS

The font files (`*.ttf`, `*.woff2` — 638 files, ~2 GB) are stored with
[Git LFS](https://git-lfs.com). **Install Git LFS before cloning.** Cloning without it succeeds
without any error, but every font arrives as a ~130-byte text file like this:

```
version https://git-lfs.github.com/spec/v1
oid sha256:b4a1df...
size 1004120
```

> *Os arquivos de fonte estão em Git LFS. **Instale o Git LFS antes de clonar.** Sem ele o clone
> funciona sem erro nenhum, mas cada fonte chega como um arquivo de texto de ~130 bytes.
> A recuperação está no fim desta seção.*

### 1. Install Git LFS · *Instalar o Git LFS*

<details>
<summary>per operating system · <i>por sistema operacional</i></summary>

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

*No **NixOS**, declare `git-lfs` em `environment.systemPackages`. **Não** use `nix-shell -p git-lfs`:
os filtros ficam gravados na config do repositório e todo `add`/`checkout` falha se o binário sumir
do `$PATH`.*

</details>

### 2. Enable it — once per machine · *Habilitar — uma vez por máquina*

```bash
git lfs install
```

Writes the `lfs` filters into `~/.gitconfig`. Without this step, step 3 still produces pointer files.
*Grava os filtros no `~/.gitconfig`. Sem este passo, o passo 3 ainda entrega arquivos de ponteiro.*

### 3. Clone · *Clonar*

```bash
git clone <repository-url> noctua-fonts
cd noctua-fonts
```

Downloads ~2 GB. To avoid that, see *Clone without downloading everything* below.
*Baixa ~2 GB. Para evitar, ver "Clonar sem baixar tudo" abaixo.*

### 4. Check it worked · *Conferir*

```bash
git lfs ls-files | wc -l     # expected: 638
git lfs fsck                 # expected: "Git LFS fsck OK"
```

A real font is hundreds of kilobytes; a pointer is ~130 bytes:
*Uma fonte real tem centenas de KB; um ponteiro tem ~130 bytes:*

```bash
ls -l noctua-noto/NotoSansMath-Regular.ttf     # ~1.0 MB = correct · correto
```

<details>
<summary><b>Already cloned and got ~130-byte text files?</b> · <i>Já clonou e recebeu arquivos de texto?</i></summary>

Nothing is lost — the pointers know what to fetch. Install Git LFS (step 1), then:
*Nada se perdeu — os ponteiros sabem o que buscar. Instale o Git LFS (passo 1) e:*

```bash
cd noctua-fonts
git lfs install --local      # --local: only this repo, leaves ~/.gitconfig alone
git lfs pull
```

`git status` should come back clean and the fonts arrive at full size.
*O `git status` deve voltar limpo e as fontes chegam no tamanho real.*

</details>

<details>
<summary><b>Clone without downloading everything</b> (2 GB) · <i>Clonar sem baixar tudo</i></summary>

Skip the font download, then fetch only the folder you need:
*Pule o download das fontes e busque só a pasta que você precisa:*

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone <repository-url> noctua-fonts   # ~700 KB
cd noctua-fonts
git lfs install --local

git lfs pull --include="noctua-noto/**"            # ~144 MB
git lfs pull --include="noctua-iosevka/WOFF2/**"   # ~218 MB, web only
```

Anything not pulled stays a pointer, and you can pull it later at any time.
*O que não for puxado continua ponteiro, e pode ser puxado depois a qualquer momento.*

</details>

---

## Fonts · *Fontes*

| font | files | docs |
|---|---|---|
| **Noctua Iosevka** — monospaced, for terminals and code | [`noctua-iosevka/`](noctua-iosevka/) | [EN](noctua-iosevka-en.md) · [pt-BR](noctua-iosevka-pt-BR.md) |
| **Noctua Noto** — text and UI, with Nerd Fonts icons | [`noctua-noto/`](noctua-noto/) | [EN](noctua-noto-en.md) · [pt-BR](noctua-noto-pt-BR.md) |

## Tools · *Ferramentas*

Font-agnostic; run with `--help`. Require `pip install fonttools brotli`.
*Servem para qualquer fonte; rode com `--help`.*

| script | what it does · *para quê* |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | variable font → static instances · *fonte variável → estáticas* |
| [`rename-font-family.py`](rename-font-family.py) | rewrite the family name recorded inside font files · *reescrever o nome de família gravado nos arquivos* |

Converting TTF to WOFF2 for the web · *Converter TTF para WOFF2*:
[EN](convert-ttf-to-woff2-en.md) · [pt-BR](convert-ttf-to-woff2-pt-BR.md)

---

> Fonts are redistributed under their own licenses — see each font's folder.
> *Fontes são redistribuídas sob as suas próprias licenças — ver a pasta de cada uma.*
