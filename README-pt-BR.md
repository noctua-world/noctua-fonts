# noctua-fonts

*[English version](README.md)*

Tipografias usadas nos projetos, com documentação e ferramentas.

---

## ⚠️ Este repositório usa Git LFS

Os arquivos de fonte (`*.ttf`, `*.woff2` — 642 arquivos, ~2 GB) estão armazenados com
[Git LFS](https://git-lfs.com). **Instale o Git LFS antes de clonar.** Clonar sem ele funciona **sem
erro nenhum**, mas cada fonte chega como um arquivo de texto de ~130 bytes, assim:

```
version https://git-lfs.github.com/spec/v1
oid sha256:b4a1df...
size 1004120
```

### 1. Instalar o Git LFS

<details>
<summary>por sistema operacional</summary>

```bash
sudo pacman -S git-lfs             # Arch, Manjaro
sudo apt install git-lfs           # Debian, Ubuntu
sudo dnf install git-lfs           # Fedora, RHEL
sudo zypper install git-lfs        # openSUSE
brew install git-lfs               # macOS (Homebrew)
winget install GitHub.GitLFS       # Windows
```

No **NixOS**, declare `git-lfs` em `environment.systemPackages` e faça o rebuild. **Não** use
`nix-shell -p git-lfs`: os filtros clean/smudge ficam gravados na config do repositório, então todo
`git add` e `git checkout` falha assim que o binário sai do `$PATH`.

</details>

### 2. Habilitar — uma vez por máquina

```bash
git lfs install
```

Grava os filtros `lfs` no `~/.gitconfig`. Sem este passo, o passo 3 ainda entrega arquivos de
ponteiro.

### 3. Clonar

```bash
git clone <url-do-repositório> noctua-fonts
cd noctua-fonts
```

Baixa ~2 GB. Para evitar, ver *Clonar sem baixar tudo* abaixo.

### 4. Conferir

```bash
git lfs ls-files | wc -l     # esperado: 642
git lfs fsck                 # esperado: "Git LFS fsck OK"
```

Uma fonte real tem centenas de kilobytes; um ponteiro tem ~130 bytes:

```bash
ls -l noctua-noto/NotoSansMath-Regular.ttf     # ~1,0 MB = correto
```

<details>
<summary><b>Já clonou e recebeu arquivos de texto de ~130 bytes?</b></summary>

Nada se perdeu — os ponteiros sabem o que buscar. Instale o Git LFS (passo 1) e:

```bash
cd noctua-fonts
git lfs install --local      # --local: só neste repo, não mexe no ~/.gitconfig
git lfs pull
```

O `git status` deve voltar limpo e as fontes chegam no tamanho real.

</details>

<details>
<summary><b>Clonar sem baixar tudo</b> (2 GB)</summary>

Pule o download das fontes e busque só a pasta que você precisa:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone <url-do-repositório> noctua-fonts   # ~700 KB
cd noctua-fonts
git lfs install --local

git lfs pull --include="noctua-noto/**"            # ~144 MB
git lfs pull --include="noctua-iosevka/WOFF2/**"   # ~218 MB, só web
```

O que não for puxado continua ponteiro, e pode ser puxado depois a qualquer momento.

</details>

---

## Fontes

| fonte | arquivos | documentação |
|---|---|---|
| **Noctua Iosevka** — monoespaçada, para terminais e código | [`noctua-iosevka/`](noctua-iosevka/) | [pt-BR](noctua-iosevka-pt-BR.md) · [EN](noctua-iosevka-en.md) |
| **Noctua Noto** — texto e interface, com ícones do Nerd Fonts | [`noctua-noto/`](noctua-noto/) | [pt-BR](noctua-noto-pt-BR.md) · [EN](noctua-noto-en.md) |
| **Symbols Nerd Font** — só ícones, como fallback de qualquer fonte de texto | [`symbols-nerd-font/`](symbols-nerd-font/) | [pt-BR](symbols-nerd-font-pt-BR.md) · [EN](symbols-nerd-font-en.md) |

## Ferramentas

Servem para qualquer fonte; rode com `--help`. Exigem `pip install fonttools brotli`.

| script | para quê |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | fonte variável → instâncias estáticas |
| [`rename-font-family.py`](rename-font-family.py) | reescrever o nome de família gravado nos arquivos de fonte |

Converter TTF para WOFF2 para a web: [pt-BR](convert-ttf-to-woff2-pt-BR.md) ·
[EN](convert-ttf-to-woff2-en.md)

---

> Fontes são redistribuídas sob as suas próprias licenças — ver a pasta de cada uma.
