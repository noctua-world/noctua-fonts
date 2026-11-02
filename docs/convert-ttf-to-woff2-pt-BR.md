# Converter TTF para WOFF2

*[English version](convert-ttf-to-woff2-en.md)*

WOFF2 é o formato de fonte da web: o mesmo TTF reempacotado com compressão **Brotli** e algumas
transformações específicas de fonte. Decodificado, um WOFF2 tem os mesmos contornos, o mesmo
hinting e as mesmas tabelas de nome do seu TTF. A única tabela descartada é a da assinatura digital
(`DSIG`), que os TTFs do Noctua Iosevka trazem vazia. Uma flag pode se perder, conforme a
ferramenta: ver [Escolher a ferramenta](#escolher-a-ferramenta). Neste repositório, um WOFF2 tem
**15–56%** do tamanho do seu TTF: cerca de 15% no Noctua Iosevka, cerca de 20% nas faces Nerd Font
dele e 23–56% no Noto e na Symbols Nerd Font. É o único formato que vale a pena servir num
`@font-face` hoje: todo navegador em uso o suporta desde 2016–18.

Todo TTF deste repositório já tem o seu WOFF2. Leia
[Os arquivos WOFF2 deste repositório](#os-arquivos-woff2-deste-repositório) antes de converter algum
deles.

---

## Escolher a ferramenta

Há dois caminhos. Os arquivos que eles geram não são idênticos byte a byte: nos 135 WOFF2 do
Noctua Iosevka, de cerca de 1,7 MB cada, os tamanhos diferem em até 5,5 KB. Eles também diferem
numa flag. A `OVERLAP_SIMPLE` marca um glifo cujos contornos podem se sobrepor, e alguns
renderizadores a usam para desenhar esse glifo corretamente. O `woff2_compress` 1.0.2 a descarta, e
o `woff2_decompress` 1.0.2 não a devolve ao decodificar um arquivo que a tem; o `fonttools` a mantém
nos dois sentidos. (A biblioteca WOFF2 passou a conhecer a flag em março de 2022, depois da 1.0.2,
a última versão lançada e a que as distribuições empacotam.) Os TTFs do Noctua Iosevka a ligam em
todo glifo com contornos, então para eles prefira o `fonttools`, como este repositório faz. Os TTFs
Nerd Font, Noto e Symbols daqui não a ligam, e os dois caminhos os decodificam para a mesma fonte:
escolha pelo que já estiver à mão.

| | `woff2_compress` | `fonttools` |
|---|---|---|
| o que é | ferramenta de referência do Google, o mesmo código que os navegadores usam para decodificar | biblioteca Python de manipulação de fontes |
| entrada/saída | um arquivo por vez, saída **ao lado da origem**, sem opção de diretório | qualquer caminho de entrada e de saída |
| também faz | `woff2_decompress` (WOFF2 → TTF), útil para validar | subsetting, instanciação, renomeação |
| dependência | binário do sistema | pacotes Python `fonttools` e `brotli`, num ambiente virtual |

<details>
<summary><b>Instalando</b> — por distribuição / sistema</summary>

**`woff2_compress`** (pacote geralmente chamado `woff2`):

| sistema | comando |
|---|---|
| Arch, Manjaro | `sudo pacman -S woff2` |
| Debian, Ubuntu | `sudo apt install woff2` |
| Fedora | `sudo dnf install woff2-tools` |
| openSUSE | `sudo zypper install woff2` |
| macOS (Homebrew) | `brew install woff2` |
| NixOS / Nix (shell efêmero) | `nix-shell -p woff2` |

O RHEL 9 e o 10 trazem a biblioteca WOFF2, mas não este comando (conferido no Rocky Linux). Neles,
use o `fonttools`.

No **NixOS**, prefira o shell efêmero a instalar no perfil: é uma ferramenta de uso pontual. Para
deixar declarativo, adicione `woff2` a `environment.systemPackages`.

O **`fonttools`** precisa do **`brotli`** junto. Sozinho, o `fonttools` **não lê nem escreve**
WOFF2: ele falha com `ImportError: No module named brotli`. Instale os dois num ambiente virtual,
uma pasta só sua de pacotes Python:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

Por que não um `pip install` direto: no Debian, no Ubuntu, no Arch e no Homebrew, o Python do
sistema pertence ao gerenciador de pacotes (PEP 668). Fora de um ambiente virtual, o pip recusa a
instalação com `error: externally-managed-environment`. No Debian e no Ubuntu, o
`python3 -m venv` também precisa do pacote `python3-venv` (`sudo apt install python3-venv`). A
última linha põe o `fonttools` do ambiente no `PATH` deste shell, para que os comandos abaixo o
encontrem; rode-a de novo em cada shell novo. Neste repositório, o git já ignora `.venv/`. No
Windows, os programas do ambiente ficam em `.venv\Scripts`: a linha de instalação é
`.venv\Scripts\python -m pip install fonttools brotli`.

Para ter os comandos do fontTools sem criar você mesmo um ambiente virtual, use o pipx. Ele os
mantém num ambiente só deles:

```bash
pipx install 'fonttools[woff]'
```

O extra `woff` traz o `brotli` junto. Mantenha as aspas: o zsh, shell padrão do macOS, lê colchetes
sem aspas como padrão de nome de arquivo e falha com `zsh: no matches found: fonttools[woff]`.

No **NixOS**, ou em qualquer sistema com Nix, um shell de uso pontual tem os dois, com o
`fonttools` no `PATH`:

```bash
nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])'
```

</details>

---

## Converter

### Com `fonttools` — você controla o destino

`-o` dá o nome do arquivo de saída. A pasta dele precisa existir: o `fonttools` não a cria e falha
com `FileNotFoundError`.

```bash
mkdir -p web
fonttools ttLib.woff2 compress -o web/MyFont-Regular.woff2 MyFont-Regular.ttf
```

Um diretório inteiro, vários arquivos de cada vez:

```bash
mkdir -p web
find . -maxdepth 1 -name '*.ttf' -print0 \
  | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" sh -c \
      'fonttools ttLib.woff2 compress -o "web/$(basename "$1" .ttf).woff2" "$1"' sh
```

`getconf _NPROCESSORS_ONLN` imprime o número de CPUs ativas, no Linux e no macOS. O `nproc` só
existe no Linux. Cada nome de arquivo chega ao `sh` interno como `$1`, então nomes com espaços ou
aspas não causam problema.

### Com `woff2_compress` — grava ao lado da origem

A ferramenta tem interface mínima: **um argumento** e **nenhuma opção**. Até
`woff2_compress --help` lê `--help` como nome de arquivo. Ela grava o WOFF2 ao lado do TTF, com o
mesmo nome, e substitui um arquivo que já esteja lá. Não existe opção de diretório de saída, então o
fluxo é "comprimir e depois mover".

```bash
woff2_compress MyFont-Regular.ttf
```

Isso cria `MyFont-Regular.woff2` na mesma pasta. Um diretório inteiro, vários arquivos de cada vez,
e depois a mudança de pasta:

```bash
printf '%s\0' *.ttf | xargs -0 -n 1 -P "$(getconf _NPROCESSORS_ONLN)" woff2_compress
mkdir -p web && mv *.woff2 web/
```

### Lotes grandes

Cada arquivo é comprimido numa CPU só, com o Brotli na qualidade máxima (11). Uma face de 10 MB do
Noctua Iosevka leva cerca de **14 s** com o `woff2_compress` e **21 s** com o `fonttools`. Para
andar mais rápido, converta vários arquivos ao mesmo tempo (`-P`); um arquivo sozinho não se divide
entre várias CPUs. Como medida: converter os 321 TTFs deste repositório com o `woff2_compress` em
16 CPUs levou cerca de 10 minutos. Nem todo WOFF2 guardado aqui foi gravado por ele, porém: ver
[Os arquivos WOFF2 deste repositório](#os-arquivos-woff2-deste-repositório).

Se o lote for interrompido, **não recomece**. As duas ferramentas gravam o WOFF2 de uma vez, quando
a compressão termina, então uma fonte parada no meio ainda não tem WOFF2. Converta só o que falta.
Para o lote do `woff2_compress`, antes de mover os arquivos:

```bash
for f in *.ttf; do [ -f "${f%.ttf}.woff2" ] || printf '%s\0' "$f"; done \
  | xargs -0 -r -n 1 -P "$(getconf _NPROCESSORS_ONLN)" woff2_compress
```

Para o lote do `fonttools`, que grava em `web/`:

```bash
for f in *.ttf; do [ -f "web/${f%.ttf}.woff2" ] || printf '%s\0' "$f"; done \
  | xargs -0 -r -n 1 -P "$(getconf _NPROCESSORS_ONLN)" sh -c \
      'fonttools ttLib.woff2 compress -o "web/$(basename "$1" .ttf).woff2" "$1"' sh
```

O `-r` impede que o `xargs` do GNU rode o comando uma vez, sem arquivo nenhum, quando não falta
nada. O `xargs` do macOS aceita a opção, e de todo modo nunca faz isso. Um WOFF2 cortado enquanto
era gravado conta como presente aqui; a checagem de tamanho abaixo o encontra.

---

## Validar

Rode as três primeiras checagens na pasta que contém os arquivos WOFF2. Elas não precisam de
ferramenta de fonte.

```bash
ls *.woff2 | wc -l
```

A contagem deve bater com o número de TTFs de origem.

```bash
for f in *.woff2; do
  [ "$(head -c4 "$f" | tr -d '\0')" = "wOF2" ] || echo "INVALID: $f"
done
```

Todo WOFF2 válido começa com os 4 bytes `wOF2`. Isso encontra um arquivo vazio, ou um que nem é
WOFF2. O `tr -d '\0'` descarta os bytes zero: um TTF começa com alguns, e o bash reclama deles.

```bash
for f in *.woff2; do
  od -An -tu1 -j8 -N4 "$f" 2>/dev/null \
    | awk -v size="$(wc -c < "$f")" '{ n = $1*16777216 + $2*65536 + $3*256 + $4 } END { exit !(NR && n == size) }' \
    || echo "SHORT: $f"
done
```

Os bytes 8–11 do cabeçalho guardam o tamanho do arquivo inteiro. Isso encontra um arquivo cortado.

Decodificar é a checagem mais forte: um arquivo cortado, e a maioria dos arquivos danificados, falham
na decodificação. A partir da pasta acima de `web/`:

```bash
woff2_decompress web/MyFont-Regular.woff2
fonttools ttLib.woff2 decompress web/MyFont-Regular.woff2
```

Use um ou outro. Os dois gravam a fonte decodificada ao lado do WOFF2, como
`web/MyFont-Regular.ttf`. O `woff2_decompress` **substitui** um arquivo com esse nome, então nunca o
rode na pasta do TTF de origem. O `fonttools`, em vez disso, escolhe um nome livre
(`MyFont-Regular#1.ttf`). Apague a cópia decodificada depois.

Decodificar não prova que todo byte está certo: um único byte alterado ainda pode decodificar. Só um
checksum prova isso, e este repositório guarda um para cada fonte gerada (ver a última seção).

---

## Usar na web

```css
@font-face {
  font-family: "My Font";
  src: url("web/MyFont-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

Repita por peso/estilo **efetivamente usado**. Numa família grande (dezenas ou centenas de arquivos),
declarar tudo é contraproducente: o navegador só baixa o que a página referencia, mas cada regra
ainda custa parsing, e é fácil apontar sem querer para um peso que ninguém usa.

Se a fonte for **variável**, um único `@font-face` cobre todos os pesos. Declare a faixa do eixo em
`font-weight`. Para um WOFF2 variável, `format("woff2")` basta:

```css
@font-face {
  font-family: "My Font";
  src: url("web/MyFont-Variable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}
```

⚠️ A **instância padrão** de uma fonte variável nem sempre é a Regular, e quem desenha o arquivo
sem definir o eixo `wght` recebe essa instância. A faixa declarada faz o `font-weight` percorrer o
eixo inteiro, então não depende do que o navegador faz sem ela. O
[Noctua Noto](noctua-noto-pt-BR.md), §5a, tem um caso real: o padrão é Thin em JP, KR, SC e
Hebrew. Medido lá no Chrome 150, JP e Hebrew saíram no 400 e no 700 mesmo sem `font-weight` na
regra. Outros navegadores não foram medidos.

---

## Os arquivos WOFF2 deste repositório

Cada TTF daqui tem um WOFF2 com o mesmo nome: em `noctua-iosevka/WOFF2/` e
`noctua-iosevka/WOFF2-nerdfonts/` para o Noctua Iosevka, e ao lado do TTF para o Noto e a Symbols
Nerd Font. Nenhum deles está no git. Eles são assets da release `v1.0.0` de
[noctua-world/noctua-fonts](https://github.com/noctua-world/noctua-fonts), em pacotes zip descritos
pelo `font-archives.json`, então um clone novo não tem nenhuma destas fontes. Baixe um pacote e
depois confira o que você tem contra o `SHA256SUMS` commitado:

```bash
./tools/font-archives.py fetch --archive noctua-noto-woff2.zip
./tools/font-archives.py verify --allow-missing
```

Sem `--archive`, o `fetch` baixa todo pacote em que falta alguma fonte: os 23, num clone novo. Os
nomes deles estão em `font-archives.json`. Sem a ferramenta, a mesma checagem se faz com
`sha256sum -c --ignore-missing SHA256SUMS` (Linux) ou
`shasum -a 256 -c --ignore-missing SHA256SUMS` (macOS). Tire o `--allow-missing` e o
`--ignore-missing` quando tiver todos os pacotes: aí uma fonte faltando passa a ser erro.

Para refazer um destes WOFF2 a partir do TTF e continuar batendo com o `SHA256SUMS`, use o comando
que o gravou:

- **os 135 de `noctua-iosevka/WOFF2/`:** `fonttools ttLib.woff2 compress`, que mantém a flag
  `OVERLAP_SIMPLE` dos seus TTFs. O fontTools 4.61.1 com o Brotli 1.2.0 os reproduz byte a byte;
  outra versão de qualquer um dos dois pode gravar outros bytes.
- **as 27 faces SemiExtended de `noctua-iosevka/WOFF2-nerdfonts/`:** foram gravadas pelo
  `fix-nerd-semiextended-names.py`, pelo fontTools, mantendo a versão de cabeçalho WOFF2 (1.0) dos
  arquivos do `woff2_compress` que substituiu. O script só reescreve uma face ainda não corrigida,
  então não consegue refazê-las a partir dos TTFs. O `fonttools ttLib.woff2 compress`, seguido da
  volta da versão de cabeçalho para 1.0 (bytes 24 a 27 do arquivo), as reproduz byte a byte:

  ```bash
  fonttools ttLib.woff2 compress -o web/MyFont-SemiExtended.woff2 MyFont-SemiExtended.ttf
  printf '\000\001\000\000' | dd of=web/MyFont-SemiExtended.woff2 bs=1 seek=24 conv=notrunc
  ```
- **os outros 159** (o resto de `WOFF2-nerdfonts/`, o Noto e a Symbols Nerd Font): o
  `woff2_compress` 1.0.2.

Refeito com outro destes comandos, um arquivo decodifica para a mesma fonte (uma face do Noctua
Iosevka sem a flag `OVERLAP_SIMPLE`, se foi o `woff2_compress` que a gravou), mas o
`./tools/font-archives.py verify` o aponta como divergente. Fique com o arquivo baixado.

Se uma fonte alterada for para ficar, o `./tools/font-archives.py manifest` reescreve o
`SHA256SUMS`. Ele calcula o hash das fontes presentes e se recusa a rodar enquanto faltar alguma
fonte que o `SHA256SUMS` lista, porque a reescrita a descartaria: baixe todos os pacotes antes.
Passe `--remove-missing` só para uma fonte removida ou renomeada de propósito. Confira que o
`./tools/font-archives.py verify` passa sem `--allow-missing` antes de alterar a fonte. Depois de
uma fonte refeita, o `manifest` deve informar `0 added, 0 removed, 1 changed`.

Um hash novo no `SHA256SUMS` também exige pacotes novos. O `fetch` confere cada fonte de um pacote
contra o `SHA256SUMS` e recusa o pacote inteiro se alguma diferir, então o pacote da `v1.0.0` que
contém a fonte antiga não pode mais ser baixado. O `./tools/font-archives.py pack` grava os 23
pacotes em `dist/`. Eles viram os assets de uma release nova, e a tag dela substitui `v1.0.0` no
`font-archives.json`.
