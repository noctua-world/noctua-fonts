# noctua-fonts

*[English version](README.md)*

Onde as tipografias do Noctua foram feitas: o plano de build da Noctua Iosevka, as famílias Noto
com os ícones do Nerd Fonts embutidos, a Symbols Nerd Font só de ícones, as notas para converter
fontes para WOFF2, duas ferramentas em Python e todas as fontes geradas, armazenadas com Git LFS.
Fica guardado como registro de como cada fonte foi feita, e para refazer qualquer uma delas.

> **Onde colocá-lo, e onde iniciar um agente.** Este repositório pertence a um workspace: clone-o
> apenas dentro de `noctua-workspace/repos/`, e inicie seus agentes apenas a partir da raiz do
> workspace — nunca de dentro deste diretório. Um agente iniciado aqui não enxerga os repositórios
> irmãos nem os documentos compartilhados, então ele adivinha.
>
> Nada aqui é construído ou consumido pelos outros projetos; as fontes que eles distribuem foram
> copiadas à mão. Leia o documento da fonte antes de usar qualquer coisa dela.

---

## ⚠️ Este repositório usa Git LFS

Os arquivos de fonte (`*.ttf` e `*.woff2`, cerca de 4 GB no total) estão armazenados com
[Git LFS](https://git-lfs.com). **Instale o Git LFS antes de clonar.** Clonar sem ele funciona
**sem erro nenhum**, mas cada fonte chega como um ponteiro de texto de cerca de 130 bytes, assim:

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

No **NixOS**, declare `git-lfs` em `environment.systemPackages` e faça o rebuild. **Não** conte
com `nix-shell -p git-lfs`: os filtros clean e smudge ficam gravados na config do repositório,
então todo `git add` e `git checkout` falha assim que o binário sai do `$PATH`.

</details>

### 2. Habilitar — uma vez por máquina

```bash
git lfs install
```

Isso grava os filtros `lfs` no `~/.gitconfig`. Sem este passo, o passo 3 ainda entrega arquivos de
ponteiro.

### 3. Clonar, dentro do workspace

```bash
cd noctua-workspace/repos
git clone <url-do-repositório> noctua-fonts
cd noctua-fonts
```

Isso baixa todas as fontes. Para evitar, veja *Clonar sem baixar tudo* abaixo.

### 4. Conferir

```bash
git lfs fsck                                  # esperado: "Git LFS fsck OK"
git lfs ls-files | awk '$2 == "-"' | wc -l    # fontes ainda ponteiro; esperado: 0
```

No `git lfs ls-files`, `*` marca uma fonte cujo conteúdo está presente e `-` uma que ainda é
ponteiro; `git lfs ls-files --size` acrescenta o tamanho de cada fonte. Uma fonte real tem centenas
de kilobytes, um ponteiro cerca de 130 bytes:

```bash
ls -l noctua-noto/NotoSansMath-Regular.ttf     # cerca de 1 MB = correto
```

<details>
<summary><b>Já clonou e recebeu arquivos de texto de cerca de 130 bytes?</b></summary>

Nada se perdeu — os ponteiros sabem o que buscar. Instale o Git LFS (passo 1) e:

```bash
cd noctua-fonts
git lfs install --local      # --local: só neste repositório; o ~/.gitconfig fica intacto
git lfs pull
```

O `git status` volta limpo, e as fontes chegam no tamanho real.

</details>

<details>
<summary><b>Clonar sem baixar tudo</b></summary>

Pule o download das fontes e busque só as pastas de que você precisa:

```bash
cd noctua-workspace/repos
GIT_LFS_SKIP_SMUDGE=1 git clone <url-do-repositório> noctua-fonts   # só ponteiros, menos de 1 MB
cd noctua-fonts
git lfs install --local

git lfs pull --include="noctua-noto/**"            # cerca de 200 MB
git lfs pull --include="noctua-iosevka/WOFF2/**"   # cerca de 220 MB, só web
```

O que não for puxado continua ponteiro, e pode ser puxado a qualquer momento.

</details>

---

## Fontes

| fonte | arquivos | documentação |
|---|---|---|
| **Noctua Iosevka** — monoespaçada, para terminais e código | [`noctua-iosevka/`](noctua-iosevka/) | [pt-BR](noctua-iosevka-pt-BR.md) · [EN](noctua-iosevka-en.md) |
| **Noctua Noto** — texto e interface, com ícones do Nerd Fonts | [`noctua-noto/`](noctua-noto/) | [pt-BR](noctua-noto-pt-BR.md) · [EN](noctua-noto-en.md) |
| **Symbols Nerd Font** — só ícones, como fallback de qualquer fonte de texto | [`symbols-nerd-font/`](symbols-nerd-font/) | [pt-BR](symbols-nerd-font-pt-BR.md) · [EN](symbols-nerd-font-en.md) |

O plano de build da Noctua Iosevka, `noctua-iosevka/private-build-plans.toml`, é a fonte da
verdade dessa tipografia; o documento dela explica como refazê-la.

## Ferramentas

Servem para qualquer fonte; rode qualquer uma com `--help`. Ambas exigem
`pip install fonttools brotli`.

| script | para quê |
|---|---|
| [`instantiate-variable-font.py`](instantiate-variable-font.py) | fonte variável → instâncias estáticas |
| [`rename-font-family.py`](rename-font-family.py) | reescrever o nome de família gravado nos arquivos de fonte |

Converter TTF para WOFF2 para a web: [pt-BR](convert-ttf-to-woff2-pt-BR.md) ·
[EN](convert-ttf-to-woff2-en.md)

---

> Fontes são redistribuídas sob as suas próprias licenças — ver a pasta de cada uma.
