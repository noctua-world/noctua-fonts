# noctua-fonts

*[English version](README.md)*

Onde as tipografias do Noctua foram feitas: o plano de build da Noctua Iosevka, as famílias Noto
(quatro delas também com os ícones do Nerd Fonts embutidos), a Symbols Nerd Font só de ícones, as
notas para converter fontes para WOFF2, as ferramentas em Python que instanciam, renomeiam,
consertam e publicam as fontes, com os seus testes, e um site de espécime da Noctua Iosevka. Fica
guardado como registro de como cada fonte foi feita, e para refazer qualquer uma delas. As 642
fontes geradas não estão no git: são assets de uma release do GitHub, e o git guarda o SHA-256 de
cada uma. As únicas fontes no git são as do site de espécime, pequenos subconjuntos em
`site/public/`.

Estes documentos, com os scripts de [`tools/`](../tools/), são o que o repositório guarda além das
fontes. Todo comando abaixo roda a partir da raiz do repositório.

> **Onde colocá-lo, e onde iniciar um agente.** Este repositório pertence a um workspace: clone-o
> apenas dentro de `noctua-workspace/repos/`, e inicie seus agentes apenas a partir da raiz do
> workspace — nunca de dentro deste repositório. Um agente iniciado nele não enxerga os
> repositórios irmãos nem os documentos compartilhados, então ele adivinha.
>
> Nada aqui é construído ou consumido pelos outros projetos; as fontes que eles distribuem foram
> copiadas à mão. Leia o documento da fonte antes de usar qualquer coisa dela.
>
> Para usar as fontes, nada disso se aplica: clone o repositório onde quiser, como abaixo.

---

## Como obter as fontes

Um clone novo não traz nenhuma das fontes geradas. As 642 fontes geradas (TTF e WOFF2, cerca de 4,2
GiB) são assets da release
[`v1.0.0`](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0), em 23 zips descritos
por [`font-archives.json`](../tools/font-archives.json), e o git guarda no lugar delas o
[`SHA256SUMS`](../SHA256SUMS): um SHA-256 por fonte. O
[`font-archives.py`](../tools/font-archives.py) baixa os zips e confere cada fonte contra o
`SHA256SUMS`. Ele só precisa de Python 3.9 ou mais novo.

Todos os zips, cerca de 1,9 GiB de download:

```bash
git clone https://github.com/noctua-world/noctua-fonts.git
cd noctua-fonts
./tools/font-archives.py fetch
./tools/font-archives.py verify
```

Só alguns zips, pelo nome:

```bash
./tools/font-archives.py fetch --archive noctua-noto-woff2.zip symbols-nerd-font.zip
./tools/font-archives.py verify --allow-missing
```

O `./tools/font-archives.py list` mostra o nome dos 23 zips, cada um com quantas das suas fontes
estão presentes, e o `font-archives.json` diz o que cada um traz:

| zip | conteúdo | download de cada um |
|---|---|---|
| `noctua-iosevka-ttf-<largura>.zip` | Noctua Iosevka, os 27 estilos de uma largura, em TTF | cerca de 84 MiB |
| `noctua-iosevka-woff2-<largura>.zip` | os mesmos estilos em WOFF2 | cerca de 44 MiB |
| `noctua-iosevka-nerd-font-ttf-<largura>.zip` | o build Nerd Font dela, NoctuaIosevka Nerd Font Mono, 27 estilos em TTF | cerca de 145 MiB |
| `noctua-iosevka-nerd-font-woff2-<largura>.zip` | os mesmos estilos em WOFF2 | cerca de 81 MiB |
| `noctua-noto-ttf.zip` | Noctua Noto, 49 TTF | cerca de 79 MiB |
| `noctua-noto-woff2.zip` | Noctua Noto, 49 WOFF2 | cerca de 58 MiB |
| `symbols-nerd-font.zip` | Symbols Nerd Font e Symbols Nerd Font Mono, em TTF e WOFF2 | cerca de 5 MiB |

`<largura>` é `normal`, `condensed`, `semicondensed`, `semiextended` ou `extended`. Todo zip traz
também os arquivos de licença das suas fontes.

O `fetch` só grava uma fonte quando o SHA-256 dela bate com o `SHA256SUMS`, então um download
errado ou adulterado pode fazê-lo falhar, nunca instalar outra fonte. Cada zip é tudo ou nada: se
um falhar, a árvore fica como estava. Um zip cujas fontes já estejam todas presentes e corretas não
é baixado de novo, e uma fonte presente com outro hash (um rebuild seu, por exemplo) nunca é
substituída, a não ser com `--force`. Sem ele, o zip que contém uma fonte assim é recusado inteiro,
antes de ser baixado, então as fontes que faltam nele também não são baixadas; os outros zips
seguem normalmente, e o `fetch` termina com código de saída 1. O `verify` confere se toda fonte
listada no `SHA256SUMS` está presente e bate, e se toda fonte presente está listada; com
`--allow-missing`, confere só as fontes presentes e conta as que faltam. No Windows, rode a
ferramenta pelo Python: `python tools/font-archives.py fetch`.

### Sem Python

Baixe os zips que quiser da
[página da release](https://github.com/noctua-world/noctua-fonts/releases/tag/v1.0.0), ou de
`https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/` seguido do nome do zip,
numa pasta fora do repositório (`~/Downloads` abaixo). No macOS, o Safari descompacta o zip que
baixa e o remove, a não ser que a opção de abrir arquivos “seguros” após o download esteja
desligada nos ajustes gerais dele; o `curl` mantém o zip como está, como em
`curl -L -o ~/Downloads/noctua-noto-ttf.zip https://github.com/noctua-world/noctua-fonts/releases/download/v1.0.0/noctua-noto-ttf.zip`.

Os caminhos dentro de todo zip começam na raiz do repositório (`noctua-noto/…`,
`noctua-iosevka/TTF/…`), então descompacte a partir dela e depois confira as fontes contra o
`SHA256SUMS`. O `unzip -n` nunca sobrescreve um arquivo: cada zip traz também arquivos de licença
que o git já tem, e um `unzip` simples para e pergunta o que fazer com eles.

No Linux:

```bash
unzip -n ~/Downloads/noctua-noto-ttf.zip
sha256sum -c --ignore-missing SHA256SUMS
```

No macOS:

```bash
unzip -n ~/Downloads/noctua-noto-ttf.zip
shasum -a 256 -c --ignore-missing SHA256SUMS
```

Toda fonte tem de aparecer como `OK`. O `--ignore-missing` pula as fontes dos zips que você não
descompactou; quando tiver os 23, tire-o, e uma fonte faltando também vira erro. A release traz
ainda um arquivo chamado `SHA256SUMS`, com os hashes dos próprios zips. Ele não é o `SHA256SUMS` do
repositório, que lista as fontes: nunca o salve por cima dele. No Windows, use o
`font-archives.py`, acima.

---

## Fontes

| fonte | pasta | documentação |
|---|---|---|
| **Noctua Iosevka** — monoespaçada, para terminais e código | [`noctua-iosevka/`](../noctua-iosevka/) | [pt-BR](noctua-iosevka-pt-BR.md) · [EN](noctua-iosevka-en.md) |
| **Noctua Noto** — texto e interface, em muitas escritas; quatro famílias também com ícones do Nerd Fonts | [`noctua-noto/`](../noctua-noto/) | [pt-BR](noctua-noto-pt-BR.md) · [EN](noctua-noto-en.md) |
| **Symbols Nerd Font** — só ícones, como fallback de qualquer fonte de texto | [`symbols-nerd-font/`](../symbols-nerd-font/) | [pt-BR](symbols-nerd-font-pt-BR.md) · [EN](symbols-nerd-font-en.md) |

O plano de build da Noctua Iosevka,
[`noctua-iosevka/private-build-plans.toml`](../noctua-iosevka/private-build-plans.toml), é a fonte
da verdade dessa tipografia. Ele também fixa as versões das ferramentas que a geraram: Iosevka
v34.7.0, a imagem do patcher do Nerd Fonts pelo digest e ttfautohint 1.8.4. O documento da
tipografia explica como refazê-la ([§5](noctua-iosevka-pt-BR.md#5-reconstruir-do-zero)).

## Site de espécime

A Noctua Iosevka tem um site de espécime, com a versão em inglês em
<https://noctua-world.github.io/noctua-fonts/> e a em português em
<https://noctua-world.github.io/noctua-fonts/pt-BR/>. Ele é a pasta `site/public/` do `main`, que
o [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) publica no GitHub Pages a cada
push que a muda. A `site/public/` é gerada: o código-fonte é o resto de [`site/`](../site/), o
`site/build.py` escreve as páginas e o `site/subset-fonts.py` as fontes em subconjunto que elas
usam. Nunca edite a `site/public/` à mão. O [`site/README.md`](../site/README.md) explica como o
site é gerado e conferido.

## Ferramentas

Rode cada uma com `--help` para ver o uso completo; as três que reescrevem fontes precisam do
fontTools instalado até para isso.

| script | para quê | precisa de |
|---|---|---|
| [`instantiate-variable-font.py`](../tools/instantiate-variable-font.py) | fonte variável → instâncias estáticas: as instâncias nomeadas dela, ou os pesos, larguras e valores de eixo que você der | fontTools; brotli para WOFF2 |
| [`rename-font-family.py`](../tools/rename-font-family.py) | reescreve o nome de família gravado nos arquivos de fonte, e o nome dos arquivos; um problema que ele consiga prever recusa o lote inteiro antes de mexer em qualquer fonte | fontTools; brotli para WOFF2 |
| [`fix-nerd-semiextended-names.py`](../tools/fix-nerd-semiextended-names.py) | devolve aos estilos SemiExtended de um build Nerd Fonts Mono a família e os bits de negrito, que o patcher erra nessa largura | fontTools; brotli para WOFF2 |
| [`font-archives.py`](../tools/font-archives.py) | baixa e confere as fontes; para uma release, reescreve o `SHA256SUMS` e empacota os zips | Python 3.9 ou mais novo, só biblioteca padrão |
| [`check.py`](../tools/check.py) | roda todas as conferências do repositório (ver [Conferir](#conferir)) | Python 3.11 ou mais novo, com fontTools e brotli (sem eles, não roda nada) |
| [`readme-art.py`](../tools/readme-art.py) | desenha o título animado e o botão do README do repositório, em [`.github/readme/`](../.github/readme/), a partir dos contornos das fontes geradas | fontTools, e as fontes da Noctua Iosevka baixadas |

Instale o fontTools e o brotli num ambiente virtual, na raiz do repositório:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fonttools brotli
. .venv/bin/activate
```

A última linha põe o Python do ambiente na frente do `PATH` deste shell, para que o
`./tools/check.py` e as ferramentas encontrem o fontTools; rode-a de novo em cada shell novo. O git
ignora `.venv/`. As ferramentas rodam no Python 3.9 ou mais novo, mas os testes que o
`./tools/check.py` roda precisam do 3.11 ou mais novo (eles leem o plano de build com o `tomllib`),
então crie o ambiente com um `python3` assim. Um `pip install` solto falha no Python do sistema no
Debian, no Ubuntu, no Arch e no Homebrew, que o marcam como gerenciado externamente (PEP 668), e no
Debian e no Ubuntu o `python3 -m venv` também precisa do pacote `python3-venv`. No Windows: `python
-m venv .venv`, depois `.venv\Scripts\python -m pip install fonttools brotli`, e rode cada script
com o Python do ambiente, como em `.venv\Scripts\python tools/check.py`. Isso dispensa a ativação,
então funciona tanto no cmd.exe quanto no PowerShell; o PowerShell recusa o
`.venv\Scripts\activate`, a não ser que a política de execução dele permita scripts. Com Nix, o
shell que aparece em *Instalando* no [Converter TTF para
WOFF2](convert-ttf-to-woff2-pt-BR.md#escolher-a-ferramenta) tem os dois pacotes.

Converter TTF para WOFF2 para a web: [pt-BR](convert-ttf-to-woff2-pt-BR.md) ·
[EN](convert-ttf-to-woff2-en.md). Qual comando gravou cada WOFF2 daqui, e como refazer um sem que
ele deixe de bater com o `SHA256SUMS`:
[Os arquivos WOFF2 deste repositório](convert-ttf-to-woff2-pt-BR.md#os-arquivos-woff2-deste-repositório).

## Conferir

Rode o `./tools/check.py` antes de cada commit:

```bash
./tools/check.py
```

Ele roda, em ordem, a suíte de testes; o `site/build.py --check`, que falha quando a `site/public/`
difere do que `site/` gera; e o `./tools/font-archives.py verify --allow-missing`, que falha quando
uma fonte presente não bate com o `SHA256SUMS` ou não está listada nele, enquanto uma fonte faltando
não é erro. Ele precisa do Python 3.11 ou mais novo, com o fontTools e o brotli (ver
[Ferramentas](#ferramentas)): sem eles, não roda etapa nenhuma, diz o que falta e sai com código 1.
Fora isso, toda etapa roda mesmo quando uma anterior falha, e o código de saída só é 0 quando todas
passam. O `./tools/check.py --release` exige também que toda fonte do `SHA256SUMS` esteja presente e
que toda fonte pertença a exatamente um zip (`./tools/font-archives.py list`): rode-o antes de
empacotar uma release.

O GitHub Actions roda a mesma conferência a cada push no `main` e a cada pull request
([`.github/workflows/check.yml`](../.github/workflows/check.yml)): o `check.py` no Linux, no macOS e
no Windows, com o Python 3.11 e o 3.14 e o fontTools e o brotli com que este repositório foi feito,
e mais uma vez com as versões mais novas do Python, do fontTools e do brotli; e todos os testes
menos o `tests/test_licences.py`, que precisa do 3.11, no Python 3.9, o mais antigo que as
ferramentas aceitam. Quando uma release é publicada, o
[`.github/workflows/release-assets.yml`](../.github/workflows/release-assets.yml) baixa os 23 zips
dela nos três sistemas e confere cada fonte, com o `font-archives.py` e com os comandos `sha256sum`
e `shasum` acima.

## Manter a release

Para quem mantém o repositório. Uma mudança de fonte (um estilo refeito, uma fonte acrescentada,
removida ou renomeada) exige uma release nova:

1. Antes de mudar qualquer coisa, baixe todos os zips e confira se a árvore está completa:

   ```bash
   ./tools/font-archives.py fetch
   ./tools/font-archives.py verify
   ```

2. Mude as fontes. Uma fonte acrescentada ou renomeada tem de pertencer a exatamente um zip do
   `tools/font-archives.json`. Se a mudança mexer na Noctua Iosevka, refaça também as fontes em
   subconjunto do site de espécime, que são recortadas dela, como explica o
   [`site/README.md`](../site/README.md).
3. Reescreva o `SHA256SUMS` com `./tools/font-archives.py manifest`. Ele se recusa a rodar enquanto
   faltar na árvore alguma fonte que o `SHA256SUMS` lista, porque a reescrita a apagaria da lista;
   passe `--remove-missing` só para uma fonte removida ou renomeada de propósito. Ele mostra o que
   acrescentou, removeu e mudou: confira se é isso que você queria.
4. Troque a tag da release atual, `v1.0.0`, pela da release nova (`v1.1.0` no exemplo abaixo) em
   todo lugar onde ela está escrita: o `"tag"` do `tools/font-archives.json` e os documentos de
   `docs/` que a citam (os dois READMEs, os três documentos de fonte e as notas de conversão, nas
   duas línguas). O site de espécime lê a tag do `tools/font-archives.json`: gere de novo a pasta
   `site/public/` com `python3 site/build.py`, como explica o
   [`site/README.md`](../site/README.md), e o `./tools/check.py` falha enquanto você não fizer
   isso. Já os documentos, nenhuma conferência compara. Este comando lista todos os lugares, menos
   a `site/public/`, e inclusive este passo:

   ```bash
   git grep -n -F v1.0.0 -- ':(exclude)site/public'
   ```

5. Rode `./tools/check.py --release`.
6. Rode `./tools/font-archives.py pack`. Ele grava os zips e um `SHA256SUMS` deles em `dist/`, que o
   git ignora. Ele não mexe em nenhum outro arquivo dali, e o passo 8 anexa tudo o que está em
   `dist/`: apague antes qualquer outro arquivo.
7. Faça o commit da mudança, com o `SHA256SUMS` e o `tools/font-archives.json`, e dê push.
8. Marque esse commit com uma tag assinada, dê push na tag e crie a release a partir dela, com
   todos os arquivos de `dist/` anexados. Com o GitHub CLI, depois do push do passo 7:

   ```bash
   git tag -s v1.1.0 -m v1.1.0
   git push origin v1.1.0
   gh release create v1.1.0 --verify-tag dist/*
   ```

   A tag é assinada como os commits, então o `git verify-tag v1.1.0` a confere quando a chave SSH
   pública de quem assinou está no arquivo que o gpg.ssh.allowedSignersFile indica, como no `git
   verify-commit`. O `--verify-tag` faz o gh se recusar a rodar se essa tag ainda não estiver no
   GitHub; sem ele, uma tag digitada errado faria o GitHub criar uma, sem assinatura, no commit que
   fosse o mais recente do branch padrão. Num terminal, o gh pergunta o título e as notas da release
   antes de criá-la. Publicá-la dispara o
   [`release-assets.yml`](../.github/workflows/release-assets.yml), que baixa os 23 zips no Linux,
   no macOS e no Windows e confere cada fonte: espere ele passar.

Por que uma tag nova: o `fetch` recusa um zip que não traga exatamente as fontes que o
`font-archives.json` atribui a ele a partir do `SHA256SUMS`, mais os arquivos de licença dele, e
recusa o zip inteiro quando uma fonte que ele precisa gravar não tem o SHA-256 listado ali. Quando
uma fonte muda, ou é acrescentada, removida ou renomeada, o zip da release atual a que ela pertence
deixa de bater. O `fetch` pega todos os zips da única tag do `font-archives.json`, então a release
nova precisa trazer os 23, que o `pack` grava. Substituir os assets de uma release publicada
quebraria todo checkout de um commit anterior, cujos `SHA256SUMS` e `font-archives.json` ainda
apontam para as fontes antigas e para aquela release. Deixe toda release publicada como está.

## Licença

O conteúdo próprio do repositório — os scripts e os seus testes, os documentos, o plano de build da
Noctua Iosevka e o código-fonte do site de espécime, com as páginas geradas a partir dele — está
licenciado sob a [licença MIT](../licenses/LICENSE-MIT) ou a [Apache License
2.0](../licenses/LICENSE-APACHE), à sua escolha (`MIT OR Apache-2.0`, ver [`LICENSE`](../LICENSE)).
Salvo declaração explícita em contrário, toda contribuição que você enviar intencionalmente para
inclusão fica licenciada da mesma forma, sem nenhum termo ou condição adicional.

As fontes não entram nesse licenciamento. Todo arquivo de fonte (`*.ttf`, `*.woff2`), incluídas as
fontes em subconjunto do site, segue sob a licença da sua família. Os textos ficam no `licenses/` de
cada pasta de fontes, e todo zip leva os textos das fontes que contém:

| fontes | licença | texto |
|---|---|---|
| Noctua Iosevka, um build próprio da Iosevka | SIL Open Font License 1.1 | [`noctua-iosevka/licenses/OFL-Iosevka.txt`](../noctua-iosevka/licenses/OFL-Iosevka.txt) |
| Noctua Noto | SIL Open Font License 1.1 | [`noctua-noto/licenses/`](../noctua-noto/licenses/), um `OFL-*.txt` por família |
| Symbols Nerd Font, e os ícones do Nerd Fonts dentro das fontes com patch | distribuídos pelo projeto Nerd Fonts com a licença MIT dele; cada conjunto de ícones mantém a sua própria licença | [`symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt`](../symbols-nerd-font/licenses/LICENSE-NerdFontsSymbolsOnly.txt), copiado para [`noctua-iosevka/licenses/`](../noctua-iosevka/licenses/) e [`noctua-noto/licenses/`](../noctua-noto/licenses/) |

Nem todo conjunto de ícones é MIT: Codicons e Font Awesome estão sob CC BY 4.0, Material Design
Icons sob Apache 2.0, Pomicons e Weather Icons sob a SIL Open Font License 1.1, e Font Logos sob a
Unlicense. O resto de cada fonte com patch segue sob a OFL da sua família. O [`LICENSE`](../LICENSE)
expõe tudo isso e indica as listas do Nerd Fonts que trazem cada conjunto de ícones com a sua
origem e a sua licença.
