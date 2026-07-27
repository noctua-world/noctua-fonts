# Converter TTF para WOFF2

*[English version](convert-ttf-to-woff2-en.md)*

WOFF2 é o formato de fonte da web: o mesmo TTF reempacotado com compressão **Brotli** e algumas
transformações específicas de fonte. **Nada é perdido** — glifos, hinting e tabelas de nome
sobrevivem intactos, e o arquivo costuma cair a **20–45%** do tamanho original. É o único formato que
vale a pena servir num `@font-face` hoje: todo navegador em uso o suporta desde 2016–18.

---

## Escolher a ferramenta

Há dois caminhos, e ambos produzem arquivos equivalentes. Escolha pelo que já estiver à mão.

| | `woff2_compress` | `fonttools` |
|---|---|---|
| o que é | ferramenta de referência do Google, o mesmo código que os navegadores usam para decodificar | biblioteca Python de manipulação de fontes |
| entrada/saída | um arquivo por vez, saída **ao lado da origem**, sem opção de diretório | qualquer, controlável |
| também faz | `woff2_decompress` (WOFF2 → TTF), útil para validar | subsetting, instanciação, renomeação |
| dependência | binário do sistema | `pip install fonttools brotli` |

<details>
<summary><b>Instalando</b> — por distribuição / sistema</summary>

**`woff2_compress`** (pacote geralmente chamado `woff2`):

```bash
sudo pacman -S woff2                      # Arch, Manjaro
sudo apt install woff2                    # Debian, Ubuntu
sudo dnf install woff2-tools              # Fedora, RHEL
sudo zypper install woff2                 # openSUSE
brew install woff2                        # macOS (Homebrew)
nix-shell -p woff2                        # NixOS / Nix (shell efêmera)
```

No **NixOS** prefira a shell efêmera a instalar no perfil — é uma ferramenta de uso pontual. Para
deixar declarativo, adicione `woff2` a `environment.systemPackages`.

**`fonttools`** (funciona igual em qualquer sistema):

```bash
pip install fonttools brotli              # o brotli NÃO é opcional para WOFF2
pipx install fonttools[woff]              # alternativa isolada
nix-shell -p python3Packages.fonttools python3Packages.brotli   # NixOS / Nix
```

⚠️ O `fonttools` sozinho **não** lê nem escreve WOFF2: ele falha com
`ImportError: No module named brotli`. Instale sempre os dois.

</details>

---

## Converter

### Com `fonttools` — controla o destino

```bash
# um arquivo, saída onde você quiser
fonttools ttLib.woff2 compress -o web/MinhaFonte-Regular.woff2 MinhaFonte-Regular.ttf

# um diretório inteiro, em paralelo
mkdir -p web
find . -maxdepth 1 -name '*.ttf' -print0 \
  | xargs -0 -P "$(nproc)" -I{} sh -c \
      'fonttools ttLib.woff2 compress -o "web/$(basename "{}" .ttf).woff2" "{}"'
```

### Com `woff2_compress` — grava ao lado da origem

A ferramenta tem interface mínima: **um argumento** e **nenhum parâmetro**. Não existe opção de
diretório de saída, então o fluxo é "comprimir e depois mover":

```bash
woff2_compress MinhaFonte-Regular.ttf     # cria MinhaFonte-Regular.woff2 na mesma pasta

# lote em paralelo
ls *.ttf | xargs -P "$(nproc)" -n 1 woff2_compress
mkdir -p web && mv *.woff2 web/
```

### Lote grande

A compressão é single-thread por arquivo e o Brotli roda no nível máximo — conte **dezenas de
segundos por fonte** em arquivos grandes. Paralelize por arquivo (`-P`), não espere paralelismo
interno.

Se o lote for interrompido, **não recomece**: a conversão é determinística, então basta gerar a lista
do que falta e rodar só ela.

```bash
for f in *.ttf; do [ -f "${f%.ttf}.woff2" ] || echo "$f"; done \
  | xargs -P "$(nproc)" -n 1 woff2_compress
```

---

## Validar

Duas checagens baratas pegam truncamento e arquivos faltando:

```bash
# 1. contagem — deve bater com o nº de TTFs de origem
ls *.woff2 | wc -l

# 2. assinatura — todo WOFF2 válido começa com os 4 bytes "wOF2"
for f in *.woff2; do
  [ "$(head -c4 "$f")" = "wOF2" ] || echo "INVÁLIDO: $f"
done
```

Para a prova completa de um arquivo, faça o caminho inverso — se estivesse corrompido, falharia:

```bash
woff2_decompress MinhaFonte-Regular.woff2                    # → .ttf
fonttools ttLib.woff2 decompress MinhaFonte-Regular.woff2    # equivalente
```

---

## Usar na web

```css
@font-face {
  font-family: "Minha Fonte";
  src: url("web/MinhaFonte-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

Repita por peso/estilo **efetivamente usado**. Numa família grande (dezenas ou centenas de arquivos),
declarar tudo é contraproducente: o navegador só baixa o que a página referencia, mas cada regra
ainda custa parsing, e é fácil apontar sem querer para um peso que ninguém usa.

Se a fonte for **variável**, prefira um único `@font-face` com as faixas dos eixos — cobre todos os
pesos de uma vez, e o formato passa a ser `woff2-variations`:

```css
@font-face {
  font-family: "Minha Fonte";
  src: url("web/MinhaFonte-Variable.woff2") format("woff2-variations");
  font-weight: 100 900;
  font-display: swap;
}
```

⚠️ Sem as faixas declaradas, o navegador fica preso na **instância padrão** da fonte variável — que
nem sempre é Regular. Ver [Noctua Noto](noctua-noto-pt-BR.md), §5a, para um caso real em que o padrão
é Thin e o resultado é texto capilar com negrito falso por cima.
