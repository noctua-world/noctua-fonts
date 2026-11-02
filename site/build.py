#!/usr/bin/env python3
"""Build the Noctua Iosevka specimen site into site/public/, which GitHub Pages serves.

Standard library only. One template, two locales:

    site/template.html + site/i18n/en.json     ->  site/public/index.html
    site/template.html + site/i18n/pt-BR.json  ->  site/public/pt-BR/index.html

plus the static assets (site/static/ -> site/public/assets/), the @font-face sheet
(site/public/assets/css/fonts.css), the measured values the stylesheet needs
(site/public/assets/css/facts.css: the fitted titles and the stylistic-set bars) and the
strings the scripts show (site/public/assets/js/strings.js), all generated here.
.github/workflows/pages.yml deploys site/public/ as it is.

The subset fonts under site/public/assets/fonts/ are written by site/subset-fonts.py,
not by this script. This script only names them in fonts.css, from the face
matrix below, which subset-fonts.py reads too.

Template tags:

    {{key}}    a locale string, HTML-escaped
    {{&key}}   a locale string inserted as HTML (it may carry <code>, <b>, <i>, <a>)
    {{@name}}  a per-page value: lang, root, canonical, hreflang targets ...
    {{%name}}  a fragment generated here from the font facts and the locale

A locale string the template renders may name a fact as a {placeholder}: the measured
{codepoints}, {sets}, {variants}, {italic_redrawn} and the other counts of facts(), formatted
for the locale, and the release, read from tools/font-archives.json ({tag}, {version},
{release_url}). The build fills it in, so each is typed once. The repository the page links to
and the site's own address come from tools/font-archives.json too.

Without JavaScript the page is a static specimen: the template marks what only a script can
drive .js-only, and the build writes what a script would otherwise draw (the terminal's still
frame, its side panel and status line) into the page.

A key missing from either locale, a key that neither the template, a generated
fragment nor the scripts use, an unknown tag and an unknown placeholder are all build
failures.
Locale keys that start with "js." are not used by the template: they go into
strings.js, and every one of them must be read by some script as t("name").

Usage:

    python3 site/build.py            write site/public/
    python3 site/build.py --check    rebuild in memory; exit 1 if site/public/ differs

The build is deterministic: the same sources always give the same bytes.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import unicodedata
from collections import namedtuple
from pathlib import Path

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
PUBLIC = SITE / "public"
TEMPLATE = SITE / "template.html"
I18N = SITE / "i18n"
STATIC = SITE / "static"

LOCALES = ("en", "pt-BR")


def _archives_config() -> tuple[str, str]:
    """The repository ("owner/name") and the tag of the release the downloads point at, both
    from tools/font-archives.json, the file tools/font-archives.py fetches from, so that the
    repository and a new release are each named in one place."""
    data = json.loads((REPO / "tools" / "font-archives.json").read_text(encoding="utf-8"))
    repository, tag = data.get("repository"), data.get("tag")
    # The same rules font-archives.py applies to the two fields.
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+", repository):
        sys.exit(f"font-archives.json: 'repository' must look like 'owner/name', not {repository!r}")
    if not isinstance(tag, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", tag):
        sys.exit(f"font-archives.json: 'tag' must be letters, digits and . _ + -, not {tag!r}")
    return repository, tag


REPOSITORY, RELEASE_TAG = _archives_config()
_OWNER, _NAME = REPOSITORY.split("/")
REPO_URL = f"https://github.com/{REPOSITORY}"
# GitHub Pages serves a project site at https://<owner>.github.io/<name>/ (host names are
# lower case; the path keeps the repository's own spelling).
SITE_URL = f"https://{_OWNER.lower()}.github.io/{_NAME}/"
RELEASE_URL = f"{REPO_URL}/releases/tag/{RELEASE_TAG}"
DOWNLOAD_URL = f"{REPO_URL}/releases/download/{RELEASE_TAG}/"

# site/public/ paths that subset-fonts.py owns. --check and the stale-file sweep leave them alone.
FONTS_DIR = "assets/fonts/"

# ---------------------------------------------------------------------------
# The face matrix: 9 weights x 5 widths x 3 slopes = 135 real faces.
# ---------------------------------------------------------------------------

WEIGHTS = (
    (100, "Thin"), (200, "ExtraLight"), (300, "Light"), (400, "Regular"), (500, "Medium"),
    (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold"), (900, "Heavy"),
)
# (name, advance in units per 1000, CSS font-stretch, the CSS keyword the build plan maps it to)
WIDTHS = (
    ("Condensed", 456, "75%", "condensed"),
    ("SemiCondensed", 548, "87.5%", "semi-condensed"),
    ("Normal", 600, "100%", "normal"),
    ("SemiExtended", 658, "112.5%", "semi-expanded"),
    ("Extended", 720, "125%", "expanded"),
)
# (name, CSS font-style). Both slanted faces carry the same italicAngle (ITALIC_ANGLE below), and
# the oblique's CSS angle is that slant.
SLOPES = (("Upright", "normal"), ("Italic", "italic"), ("Oblique", "oblique 9deg"))

REGULAR = (3, 2, 0)  # weight, width and slope indices of NoctuaIosevka-Regular

# Read from all 135 TTFs: OS/2 usWidthClass per width (usWeightClass is the CSS weight), and
# post.italicAngle per slope.
WIDTH_CLASS = (3, 4, 5, 6, 7)
ITALIC_ANGLE = (0, -9, -9)
# The slant of both slanted faces, in degrees, as the prose states it ({slant}).
SLANT = -ITALIC_ANGLE[1]


def style_name(w: int, x: int, s: int) -> str:
    """The style part of a face name: "Condensed Bold Italic", or "Regular"."""
    parts = [p for p in (WIDTHS[x][0], WEIGHTS[w][1], SLOPES[s][0]) if p not in ("Normal", "Regular", "Upright")]
    return " ".join(parts) or "Regular"


def file_stem(w: int, x: int, s: int, prefix: str = "NoctuaIosevka") -> str:
    """The file name of a face without its extension, as the build names it."""
    return f"{prefix}-{style_name(w, x, s).replace(' ', '')}"


ALL_FACES = tuple((w, x, s) for x in range(5) for w in range(9) for s in range(3))


# key:     short code used by the data-arm attributes in the template
# css:     the CSS font-family name
# folder:  site/public/assets/fonts/<folder>/
# source:  the folder under noctua-iosevka/ that holds the TTF sources
# prefix:  the file-name prefix of the source faces
# faces:   (weight, width, slope) index triples
# display: the font-display descriptor
Family = namedtuple("Family", "key css folder source prefix faces display")


FAMILIES = (
    # The full text faces: every glyph the page sets in running text, every layout feature
    # the page demonstrates except the character variants (see "lab").
    Family("t", "Noctua Iosevka", "text", "TTF", "NoctuaIosevka", ALL_FACES, "swap"),
    # Lean faces for display type (titles, headings, the tapes, the width ladder).
    Family("d", "NI Display", "display", "TTF", "NoctuaIosevka", ALL_FACES, "swap"),
    # Four glyphs per face, for the 135-face wall and the explorer.
    Family("s", "NI Swatch", "swatch", "TTF", "NoctuaIosevka", ALL_FACES, "block"),
    # One Regular face that keeps cv01-cv99, for the character-variant machine.
    Family("l", "NI Lab", "lab", "TTF", "NoctuaIosevka", (REGULAR,), "block"),
    # The Nerd Font twin, under its real family name, for the terminal.
    Family("m", "NoctuaIosevka Nerd Font Mono", "term", "TTF-nerdfonts", "NoctuaIosevkaNerdFontMono",
           ((3, 2, 0), (6, 2, 0), (3, 2, 1)), "swap"),
)

LICENCE_FILES = ("OFL-Iosevka.txt", "LICENSE-NerdFontsSymbolsOnly.txt")

# ---------------------------------------------------------------------------
# Font facts. Measured on 2026-11-01 from noctua-iosevka/TTF/NoctuaIosevka-Regular.ttf
# with fontTools (tables, outlines) and HarfBuzz (shaping each feature on and off).
# ---------------------------------------------------------------------------

# Stylistic sets: the tag, the name the font's name table gives it (IDs 257-275), and
# the visible ASCII characters (U+0021-U+007E, 94 of them) whose outline the set changes.
# There is no ss19 in Iosevka 34.
STYLISTIC_SETS = (
    ("ss01", "Andale Mono Style", "#%*0124679@DGIJKMRVWXZ_adefgiltvwy{}"),
    ("ss02", "Anonymous Pro Style", "!$%*,.1246789:;?@CDGIJKMRSTVWXYZacdefijlrvwxyz{}"),
    ("ss03", "Consolas Style", "#%*124679?@DGKMRVWXZ_abdefgklqtvwy{}"),
    ("ss04", "Menlo Style", "!#%&*,.01246789:;?DGKMQRVWXZ_adefijtvwy{}"),
    ("ss05", "Fira Mono Style", "#%&*0126789@DGKMRVWXZ^_adefgklrtvwy"),
    ("ss06", "Liberation Mono Style", "!#%,.0145689:;?@DGKMRVWXZadefijrtvwy{}"),
    ("ss07", "Monaco Style", "#%*014679@DGKMRVWXZabdefgiklqrtvwy"),
    ("ss08", "Pragmata Pro Style", "#$%&*04679DGIJKMNQRVWXYZadefgklvwxyz{}"),
    ("ss09", "Source Code Pro Style", "#$*01245689DGKMRVWXZadefgilrtvwy"),
    ("ss10", "Envy Code R Style", "$%14578AJKMQRVWXZ_abdefgijklqtvwy"),
    ("ss11", "X Window Style", "$%()*012456789^{}~"),
    ("ss12", "Ubuntu Mono Style", "#$%0145689DGKMRVWXZ_abdefgiklmnpqrtuvwy{}"),
    ("ss13", "Lucida Style", "!#%,.014689:;?DGKMRVWXZadefijklrtvwy"),
    ("ss14", "JetBrains Mono Style", "#%&()*012478?GJKMQRVWXZadefgjktuvwy"),
    ("ss15", "IBM Plex Mono Style", "#&*012456789?DKMRVWXZ_adefgjlrtvwy{}"),
    ("ss16", "PT Mono Style", "#$%*1246789CDGKMRSTVWXZ_bcdefghklqrtuvwy{}"),
    ("ss17", "Recursive Mono Style", "!#$&*,.15679:;?@BGKMRSUVWXZ_abdefghijlmnrtvwy{}"),
    ("ss18", "Input Mono Style", "#%*014689?GKMRVWXZ_abdefgklqvwy"),
    ("ss20", "Curly Style", "679KRVWXYZkvwxyz"),
)
ASCII_VISIBLE = 94

# The character-variant features the font carries: cv01 to cv99, every one of them.
CV_FEATURES = 99

# Code points whose Italic outline differs from the Oblique one (NoctuaIosevka-Italic.ttf
# against -Oblique.ttf, composite glyphs decomposed): the letters the italic redraws, the
# accented letters built on them, and a few symbols. Every other code point is shared.
ITALIC_REDRAWN = 466

# Character variants for the slot machine: the character, its cv feature, how many values
# the feature takes (each value is a distinct outline), and the value whose outline is the
# default glyph. So "a" has 33 shapes in all, cv36 = 1 ... 33, and cv36 = 2 is the default.
CHARACTER_VARIANTS = (
    ("a", "cv36", 33, 2), ("g", "cv42", 16, 9), ("f", "cv41", 45, 32), ("0", "cv10", 54, 25),
    ("m", "cv48", 58, 29), ("r", "cv52", 28, 1), ("t", "cv54", 30, 1), ("y", "cv59", 18, 2),
    ("k", "cv46", 40, 1), ("l", "cv47", 14, 10), ("1", "cv01", 9, 5), ("Q", "cv26", 11, 2),
    ("G", "cv17", 36, 2), ("W", "cv32", 45, 35), ("ß", "cv63", 48, 17), ("а", "cv87", 33, 1),
    ("χ", "cv84", 26, 1), ("$", "cv28", 5, 2),
)

# The ligatures the page shows, by the feature that forms them: a selection, not every sequence
# a feature changes (dlig, for one, also joins -< >- ~< >~ =| /\ \/ {| and |}), so the prose
# gives no count. Every joined form still fills exactly the cells of the characters it replaces
# (the glyph count never changes). &&, ** and += never join.
LIGATURES = (
    ("calt", ("->", "=>", "!=", "==", "===", "!==", "<=", ">=", "<=>", "::", ":=", "::=", "|>", "<|>",
              "<-", "<->", "-->", "<!--", ">>=", "=<<", "~>", "<~>", "||", "..", "...", "??", "?.",
              "</>", "//", "/*", ";;", "<>", "<*>", ">>", "==>")),
    ("dlig", ("++", "--", "##", "~~", "__", "|=", ".=", "=<", "[|", "|]", "|-", "-|")),
    ("HSKL", ("/=", "=/=")),
)

# Unicode blocks of the cmap. All 135 faces share one cmap of 7,580 code points.
# Per block: its first and last code point, the code points the font maps, out of the
# characters Unicode 15.1 assigns to the block, control codes aside (one rule for every block,
# so Basic Latin is 95, not 128, and Greek and Coptic is 135, not 144). The strip is a sample of
# 24 of the block's characters, evenly spaced, letters and symbols first; a space marks a
# character the font does not draw. Greek Extended holds two characters that Unicode
# normalisation folds into Greek and Coptic (U+1F71 and U+1F7B become U+03AC and U+03CD), so
# they are written as escapes here and as character references in the page.
CODE_POINTS = 7580
STRIP = 24  # characters in each block's sample strip
COVERAGE = (
    ("cov.basic_latin", 0x0000, 0x007F, 95, 95, "$147<ADGJMPSWZadgjmpsvy~"),
    ("cov.latin1", 0x0080, 0x00FF, 96, 96, "¢¦ª°´º¾ÃÇËÎÒÖÚÝáåéìðôøûÿ"),
    ("cov.latin_ext_a", 0x0100, 0x017F, 128, 128, "ĀĆċđĖĜġħĬĲķĽłňōœŘŞţũŮŴŹſ"),
    ("cov.latin_ext_b", 0x0180, 0x024F, 208, 208, "ƀƉƒƛƤƭƶƿǈǑǚǣǬǵǾȇȐșȢȫȴȽɆɏ"),
    ("cov.ipa", 0x0250, 0x02AF, 96, 96, "ɐɔɘɜɡɥɩɭɱɵɹɽʂʆʊʎʒʖʚʞʣʧʫʯ"),
    ("cov.latin_ext_add", 0x1E00, 0x1EFF, 256, 256, "ḀḋḖḡḬḷṃṎṙṤṯṺẅẐẛẦằẼỈồỞứỴỿ"),
    ("cov.greek", 0x0370, 0x03FF, 121, 135, "ͰͶͽΉΑΗΜΣΩίδκπφϋϑϗϝ   ϴϹϿ"),
    ("cov.greek_ext", 0x1F00, 0x1FFF, 233, 233, "ἀἊἔἢἬἶὁὍὛὧάύᾇᾑᾛᾥᾯᾺῆῐ῝ῧῳ῾"),
    ("cov.cyrillic", 0x0400, 0x04FF, 256, 256, "ЀЋЖРЫжсыіѡѬѷҁғҞҩҴҾӉӔӟөӴӿ"),
    ("cov.cyrillic_sup", 0x0500, 0x052F, 48, 48, "ԀԂԄԆԈԊԌԎԐԒԔԖԙԛԝԟԡԣԥԧԩԫԭԯ"),
    ("cov.punct", 0x2000, 0x206F, 94, 111, "‐–‖’“‟•‥‰″‶‹‽⁀⁃⁆⁉⁌⁏⁒⁕⁘⁛⁞"),
    ("cov.arrows", 0x2190, 0x21FF, 112, 112, "←↕↚↞↣↨↭↲↷↻⇀⇅⇊⇏⇔⇘⇝⇢⇧⇬⇱⇵⇺⇿"),
    ("cov.math", 0x2200, 0x22FF, 256, 256, "∀∋∖∡∬∷≃≎≙≤≯≺⊅⊐⊛⊦⊱⊼⋈⋓⋞⋩⋴⋿"),
    ("cov.box", 0x2500, 0x257F, 128, 128, "─┆┋┑┖├┡┧┬┲┷┽╂╈╍╓╘╞╣╩╮╴╹╿"),
    ("cov.blocks", 0x2580, 0x259F, 32, 32, "▀▁▃▄▅▇█▉▋▌▍▏▐▒▓▔▖▗▘▚▛▜▞▟"),
    ("cov.geometric", 0x25A0, 0x25FF, 96, 96, "■▤▨▬▱▵▹▽◁◅◉◍◒◖◚◞◢◦◪◮◳◷◻◿"),
    ("cov.braille", 0x2800, 0x28FF, 256, 256, "⠁⠌⠗⠢⠭⠸⡃⡎⡙⡤⡯⡺⢆⢑⢜⢧⢲⢽⣈⣓⣞⣩⣴⣿"),
)


def coverage_strip_chars() -> set[int]:
    """Every character the coverage strips draw (they are set in the lab face)."""
    return {ord(ch) for *_, strip in COVERAGE for ch in strip if ch != " "}


def char_html(ch: str) -> str:
    """A character for the page: escaped, and as a character reference where Unicode
    normalisation would fold it into another one (so no editor or tool can change it)."""
    return f"&#x{ord(ch):X};" if unicodedata.normalize("NFC", ch) != ch else esc(ch)


def group_digits(n: int, sep: str) -> str:
    return f"{n:,}".replace(",", sep)


# Facts the locale strings may name as {placeholders}; filled per locale at render time,
# so a number the page takes from the font or from the tables above is typed in one place.
DIGIT_SEP = {"en": ",", "pt-BR": "."}


def facts(code: str) -> dict[str, str]:
    num = lambda n: group_digits(n, DIGIT_SEP[code])  # noqa: E731
    return {
        "codepoints": num(CODE_POINTS),
        "sets": num(len(STYLISTIC_SETS)),
        "set_default": SET_DEFAULT,
        "variants": num(CV_FEATURES),
        # The machine's first glyph and its count of shapes ("a", 33), which the lede explains.
        "first_shapes": num(CHARACTER_VARIANTS[0][2]),
        "italic_redrawn": num(ITALIC_REDRAWN),
        "blocks": num(len(COVERAGE)),
        "strip": num(STRIP),
        "slant": num(SLANT),
        # The release, from tools/font-archives.json: its tag ("v1.2.3"), version ("1.2.3") and page.
        "tag": RELEASE_TAG,
        "version": RELEASE_TAG.removeprefix("v"),
        "release_url": RELEASE_URL,
    }

ACCEPTANCE = "il1I| 0O8B 5SZ2 3 5 S g q 9 rn m"
SMALL_SIZES = (9, 10, 11, 12, 13, 14, 16, 20)

# The Nerd Fonts icons shown beside the terminal (code point, name in the Nerd Fonts 3.4.0 cheat
# sheet, glyphnames.json; U+E626 is custom-go there, as the Symbols font names it, and seti-go
# is U+E627).
ICON_STRIP = (
    (0xF17C, "nf-fa-linux"), (0xF313, "nf-linux-nixos"), (0xF179, "nf-fa-apple"), (0xF17A, "nf-fa-windows"),
    (0xE725, "nf-dev-git_branch"), (0xF09B, "nf-fa-github"), (0xE7A8, "nf-dev-rust"), (0xE606, "nf-seti-python"),
    (0xE626, "nf-custom-go"), (0xE777, "nf-dev-haskell"), (0xE628, "nf-seti-typescript"), (0xF48A, "nf-oct-markdown"),
    (0xF4BC, "nf-oct-cpu"), (0xF1C0, "nf-fa-database"), (0xF0E7, "nf-fa-bolt"), (0xF03D2, "nf-md-owl"),
)

# Release archives: (format key, file-name part).
ARCHIVE_FORMATS = (
    ("dl.fmt_nerd_ttf", "nerd-font-ttf"), ("dl.fmt_ttf", "ttf"),
    ("dl.fmt_woff2", "woff2"), ("dl.fmt_nerd_woff2", "nerd-font-woff2"),
)
ARCHIVE_ORDER = (2, 0, 1, 3, 4)  # Normal first, then the ladder

PAGES = {
    "en": {
        "path": "index.html", "root": "", "canonical": SITE_URL,
        "og_locale": "en_US", "og_locale_alt": "pt_BR", "href_en": "./", "href_pt": "pt-BR/",
    },
    "pt-BR": {
        "path": "pt-BR/index.html", "root": "../", "canonical": SITE_URL + "pt-BR/",
        "og_locale": "pt_BR", "og_locale_alt": "en_US", "href_en": "../", "href_pt": "./",
    },
}

TAG = re.compile(r"\{\{([&@%]?)([A-Za-z0-9_.\-]+)\}\}")
JS_KEY = re.compile(r"""\bt\(\s*["']([a-z0-9_.\-]+)["']""")


class BuildError(Exception):
    pass


def esc(text: str) -> str:
    return html.escape(text, quote=True)


class Locale:
    def __init__(self, code: str, strings: dict[str, str]):
        self.code = code
        self.strings = strings
        self.used: set[str] = set()

    def raw(self, key: str) -> str:
        if key not in self.strings:
            raise BuildError(f"{self.code}: missing key {key!r}")
        self.used.add(key)
        return self.strings[key]

    def t(self, key: str) -> str:
        return esc(self.raw(key))

    def text(self, key: str) -> str:
        """The string with its {fact} placeholders filled in, unescaped (for measuring it)."""
        return fill_facts(self.raw(key), self.code, key)

    def fmt(self, key: str, **values) -> str:
        """An escaped string with {name} placeholders filled in."""
        text = self.raw(key)
        for name, value in values.items():
            text = text.replace("{" + name + "}", str(value))
        if re.search(r"\{[a-z_]+\}", text):
            raise BuildError(f"{self.code}: {key!r} has an unfilled placeholder")
        return esc(text)


# ---------------------------------------------------------------------------
# Generated fragments
# ---------------------------------------------------------------------------

SLOPE_KEYS = ("slope.upright", "slope.italic", "slope.oblique")


def en_name(loc: Locale, name: str, tag: str = "span", cls: str = "") -> str:
    """A style name (a file-name word such as "SemiCondensed"), marked English on other pages."""
    attrs = (f' class="{cls}"' if cls else "") + ("" if loc.code == "en" else ' lang="en"')
    return f"<{tag}{attrs}>{esc(name)}</{tag}>"


def gen_chips(loc: Locale, page: dict) -> str:
    """The three radio groups of the explorer; each chip is set in the face it selects."""
    out = []
    slopes = (("up", 0, "0°", "lsu"), ("it", 1, f"{-ITALIC_ANGLE[1]}°", "lsi"), ("ob", 2, f"{-ITALIC_ANGLE[2]}°", "lso"))
    groups = (
        ("wght", "faces.axis_weight", [(str(w), en_name(loc, name), str(w), f"lw{i + 1}", i == 3) for i, (w, name) in enumerate(WEIGHTS)], "chips-9"),
        ("wdth", "faces.axis_width", [(str(i + 1), en_name(loc, name), str(adv), f"lx{i + 1}", i == 2) for i, (name, adv, _, _) in enumerate(WIDTHS)], "chips-5"),
        ("slope", "faces.axis_slope", [(v, f"<span>{loc.t(SLOPE_KEYS[s])}</span>", small, cls, v == "up") for v, s, small, cls in slopes], "chips-3"),
    )
    for name, legend, chips, cls in groups:
        out.append(f'<fieldset class="axis axis-{name}"><legend>{loc.t(legend)}</legend><div class="chips {cls}">')
        for value, label, small, face, checked in chips:
            # The space keeps the accessible name readable ("Thin 100", not "Thin100").
            out.append(
                f'<label class="chip"><input type="radio" name="{name}" value="{value}"{" checked" if checked else ""}>'
                f'<span class="chip-face lfs {face}" aria-hidden="true">Aa</span>'
                f'<span class="chip-meta">{label} <small>{small}</small></span></label>'
            )
        out.append("</div></fieldset>")
    return "\n      ".join(out)


def gen_wall(loc: Locale, page: dict) -> str:
    """The 135-face wall: one panel per slope, a row per width, a column per weight.

    Each tile is written as static type, a face named for what it shows, which is what a page
    without scripts presents; explorer.js turns every tile into a button."""
    out = []
    slope_cls = ("lsu", "lsi", "lso")
    for s in range(len(SLOPES)):
        # Each slope's 45 faces arm on their own, so a panel fills in as soon as it is near.
        out.append(f'<div class="wall-panel" data-s="{s}" data-arm="s:100-900:1-5:{"uio"[s]}">')
        out.append(f'<h4><span>{loc.t(SLOPE_KEYS[s])}</span><span>{loc.t("faces.wall_count")}</span></h4>')
        out.append('<div class="wall-grid">')
        out.append('<span class="wall-lab wall-corner" aria-hidden="true"></span>')
        for w, _ in WEIGHTS:
            out.append(f'<span class="wall-lab" aria-hidden="true">{w}</span>')
        lang = "" if loc.code == "en" else ' lang="en"'
        for x, (_, adv, _, _) in enumerate(WIDTHS):
            out.append(f'<span class="wall-lab row" aria-hidden="true">{adv}</span>')
            for w in range(9):
                label = esc(f"Noctua Iosevka {style_name(w, x, s)}")
                out.append(
                    f'<span class="tile lfs lw{w + 1} lx{x + 1} {slope_cls[s]}" data-w="{w}" data-x="{x}" data-s="{s}" '
                    f'role="img" aria-label="{label}"{lang}>Ag</span>'
                )
        out.append("</div></div>")
    return "\n      ".join(out)


def gen_ladder(loc: Locale, page: dict) -> str:
    out = []
    for i, (name, adv, pct, _) in enumerate(WIDTHS):
        normal = " rung-normal" if name == "Normal" else ""
        out.append(
            f'<li class="rung{normal}" data-reveal><div class="rung-meta">{en_name(loc, name, "b")}<span class="rung-val">{adv}</span>'
            f'<code>font-stretch: {pct}</code></div><div class="rung-sample-wrap">'
            f'<p class="rung-sample lfd lw5 lx{i + 1}">cells[0..16] -&gt; ok</p></div></li>'
        )
    return "\n    ".join(out)


def gen_small_sizes(loc: Locale, page: dict) -> str:
    """The acceptance set at 9-20 px in the three slopes. Each sample carries its slope's name,
    shown on narrow screens (where the header row is gone) and read by screen readers."""
    out = []
    slopes = (("", SLOPE_KEYS[0]), (" lsi", SLOPE_KEYS[1]), (" lso", SLOPE_KEYS[2]))
    for px in SMALL_SIZES:
        cells = "".join(
            f'<span class="ss-c"><span class="ss-k">{loc.t(key)}</span><span class="ss-s{cls}">{esc(ACCEPTANCE)}</span></span>'
            for cls, key in slopes
        )
        out.append(f'<p class="ss-row px{px}" data-px="{px}"><span class="ss-px">{px} px</span>{cells}</p>')
    return "\n    ".join(out)


# Each set card is a small specimen of the glyphs the set redraws, the most telling first: the
# set's shape printed over the default one (in the pink ink), so the difference shows at a glance.
SET_GLYPH_ORDER = "agy0l1fitkrQGRKMWZ$@&*%#{}?!wvdejxz24795368BCDIJNSTUVXYbchmnopqsu_^~()[];:,.|/\\<>=+-'\"`"
SET_GLYPHS = 16


def sets_by_count() -> list[tuple[str, str, str]]:
    """The stylistic sets, the one that changes most glyphs first (ties in tag order)."""
    return sorted(STYLISTIC_SETS, key=lambda s: (-len(s[2]), s[0]))


# The set the lens and the §06 title start in (and keep, without scripts): the card that
# changes most. facts.css gives it to them, so the page shows it before any script runs.
SET_DEFAULT = sets_by_count()[0][0]


def set_glyphs(changed: str) -> str:
    rank = {ch: i for i, ch in enumerate(SET_GLYPH_ORDER)}
    return "".join(sorted(changed, key=lambda ch: (rank.get(ch, len(rank)), ch))[:SET_GLYPHS])


def gen_sets(loc: Locale, page: dict) -> str:
    """The set cards. Each card's specimen is written as static type (sets.js turns it into the
    button that loads the set into the lens); "Wear it" exists only with scripts."""
    out = []
    for tag, name, changed in sets_by_count():
        current = tag == SET_DEFAULT
        glyphs = "".join(f'<span class="sg"><i class="sd">{esc(ch)}</i><i class="sv">{esc(ch)}</i></span>' for ch in set_glyphs(changed))
        count = loc.fmt("sets.count", n=len(changed), total=ASCII_VISIBLE)
        out.append(
            f'<li class="set{" is-picked" if current else ""}" data-ss="{tag}">'
            f'<span class="set-pick">'
            f'<span class="sr-only js-only">{loc.t("sets.pick_sr")} </span>'
            f'<span class="set-head"><span class="set-tag">{tag}</span><span class="set-name">{esc(name)}</span></span>'
            f'<span class="set-glyphs" aria-hidden="true">{glyphs}</span>'
            f'<span class="set-count">{count}</span><span class="set-bar" aria-hidden="true"><span></span></span></span>'
            f'<button type="button" class="set-wear js-only" aria-pressed="false">{loc.t("sets.wear")}'
            f'<span class="sr-only">: {esc(name)}</span></button></li>'
        )
    return "\n    ".join(out)


def gen_set_default(loc: Locale, page: dict) -> str:
    """The lens's name tag, for the set it starts in."""
    name = next(n for t, n, _ in STYLISTIC_SETS if t == SET_DEFAULT)
    return f"<b>{SET_DEFAULT}</b> {esc(name)}"


def gen_ss_options(loc: Locale, page: dict) -> str:
    return "\n          ".join(f'<option value="{tag}">{tag} · {esc(name)}</option>' for tag, name, _ in STYLISTIC_SETS)


# Glyphs of the slot machine that look like a Latin letter carry their script, seen and heard.
CV_SCRIPTS = {"а": "cyr", "χ": "greek"}


def gen_cv_pick(loc: Locale, page: dict) -> str:
    out = []
    for i, (ch, tag, n, default) in enumerate(CHARACTER_VARIANTS):
        sc = CV_SCRIPTS.get(ch)
        script = f" ({loc.raw(f'cv.script_{sc}')})" if sc else ""
        label = loc.fmt("cv.pick_aria", ch=ch, script=script, tag=tag, n=n)
        mark = f'<small class="cv-sc lft" aria-hidden="true">{loc.t(f"cv.sc_{sc}")}</small>' if sc else ""
        out.append(
            f'<button type="button" role="radio" class="lfl" aria-checked="{"true" if i == 0 else "false"}" '
            f'tabindex="{0 if i == 0 else -1}" data-ch="{esc(ch)}" data-tag="{tag}" data-n="{n}" data-def="{default}" '
            f'aria-label="{label}">{esc(ch)}{mark}</button>'
        )
    return "\n      ".join(out)


def gen_cv_count(loc: Locale, page: dict) -> str:
    """The machine's first reading, written by the build so the live region starts settled."""
    ch, tag, n, default = CHARACTER_VARIANTS[0]
    return loc.fmt("js.cv_count", n=n, tag=tag, **{"def": default})


LIG_GROUPS = {"calt": "lig.group_calt", "dlig": "lig.group_dlig", "HSKL": "lig.group_hskl"}


def gen_ligatures(loc: Locale, page: dict) -> str:
    """One labelled group per feature. Each tile shows the joined form over its cell grid and,
    under it, the code points it is made of."""
    out = []
    for feature, seqs in LIGATURES:
        out.append(
            f'<div class="lig-group lig-g-{feature.lower()}"><h3 class="lig-h"><code>{feature}</code> '
            f'<span>{loc.t(LIG_GROUPS[feature])}</span> <small>{loc.fmt("lig.count", n=len(seqs))}</small></h3>'
            f'<ul class="lig-list">'
        )
        for seq in seqs:
            cps = " ".join(f"{ord(c):02X}" for c in seq)
            out.append(f'<li><span class="lg">{esc(seq)}</span><span class="lig-cp" aria-hidden="true">{cps}</span></li>')
        out.append("</ul></div>")
    return "\n      ".join(out)


def gen_icon_strip(loc: Locale, page: dict) -> str:
    return "\n        ".join(
        f'<li title="{name}"><span aria-hidden="true">&#x{cp:X};</span><span class="sr-only">{name}</span></li>'
        for cp, name in ICON_STRIP
    )


def gen_coverage(loc: Locale, page: dict) -> str:
    """One row per Unicode block: its name, a strip of its own characters set in the font (an
    empty cell where the font draws nothing), and the count."""
    out = []
    for key, _lo, _hi, n, total, strip in COVERAGE:
        cells = "".join('<i class="miss"></i>' if ch == " " else f"<i>{char_html(ch)}</i>" for ch in strip)
        out.append(
            f'<li class="cov"><span class="cov-name">{loc.t(key)}</span>'
            f'<span class="cov-strip lfl" aria-hidden="true">{cells}</span>'
            f'<span class="cov-num"><span aria-hidden="true">{n}/{total}</span>'
            f'<span class="sr-only">{loc.fmt("scripts.cov_of", n=n, total=total)}</span></span></li>'
        )
    return "\n      ".join(out)


def gen_downloads(loc: Locale, page: dict) -> str:
    out = []
    for x in ARCHIVE_ORDER:
        name, adv, _, _ = WIDTHS[x]
        lower = name.lower()
        featured = name == "Normal"
        # Each link names its width too, so twenty links never read as five identical lists.
        lang_en = "" if loc.code == "en" else ' lang="en"'
        links = "".join(
            f'<a href="{DOWNLOAD_URL}noctua-iosevka-{part}-{lower}.zip">{loc.t(fmt)}'
            f'<span class="sr-only"{lang_en}>, {esc(name)}</span></a>' for fmt, part in ARCHIVE_FORMATS
        )
        small = loc.fmt("dl.recommended", adv=adv) if featured else str(adv)
        out.append(
            f'<li class="dl-card{" dl-featured" if featured else ""}" data-reveal><h3>{en_name(loc, name, "span", f"lfd lw8 lx{x + 1}")}'
            f'<small>{small}</small></h3><p class="dl-links">{links}</p></li>'
        )
    return "\n    ".join(out)


# --- Section titles that demonstrate their own axis ------------------------------------
# Each is drawn letter by letter or word by word in real faces; screen readers get the plain
# sentence instead, so the title is never spelt out one letter at a time.

def _titled(loc: Locale, key: str, visual: str) -> str:
    return f'<span class="sr-only">{esc(loc.text(key))}</span><span class="t-vis" aria-hidden="true">{visual}</span>'


def gen_title_faces(loc: Locale, page: dict) -> str:
    """§02: Thin to Heavy, one weight per letter, across the whole title."""
    text = loc.text("faces.title")
    n = sum(1 for ch in text if ch != " ")
    words, i = [], 0
    for word in text.split(" "):
        spans = []
        for ch in word:
            spans.append(f'<span class="lw{round(i * 8 / max(1, n - 1)) + 1}">{esc(ch)}</span>')
            i += 1
        words.append(f'<span class="nb">{"".join(spans)}</span>')
    return _titled(loc, "faces.title", " ".join(words))


def _per_word(loc: Locale, key: str, classes: tuple[str, ...]) -> str:
    words = loc.text(key).split(" ")
    k = len(classes) - 1
    out = [f'<span class="nb {classes[round(i * k / max(1, len(words) - 1))]}">{esc(w)}</span>' for i, w in enumerate(words)]
    return _titled(loc, key, " ".join(out))


def gen_title_widths(loc: Locale, page: dict) -> str:
    """§03: the five widths, one word each, Condensed to Extended."""
    return _per_word(loc, "widths.title", ("lx1", "lx2", "lx3", "lx4", "lx5"))


def gen_title_slopes(loc: Locale, page: dict) -> str:
    """§04: upright, then oblique, then italic."""
    return _per_word(loc, "slopes.title", ("lsu", "lso", "lsi"))


# §11's title after its Latin word: the Greek and the Cyrillic words, in their own alphabets.
TITLE_SCRIPTS_REST = (("Ελληνικά,", "el", "lft t-gk"), ("Кириллица.", "ru", "lft t-cy"))


def scripts_title_visible(loc: Locale) -> str:
    return " ".join([loc.raw("scripts.title_latin") + ","] + [text for text, _, _ in TITLE_SCRIPTS_REST])


def gen_title_scripts(loc: Locale, page: dict) -> str:
    """§11: Latin, Greek and Cyrillic, each written in its own alphabet and ink."""
    parts = [f'<span class="t-la">{loc.t("scripts.title_latin")},</span>']
    parts += [f'<span class="{cls}" lang="{lang}">{esc(text)}</span>' for text, lang, cls in TITLE_SCRIPTS_REST]
    return _titled(loc, "scripts.title", " ".join(parts))


def gen_title_legibility(loc: Locale, page: dict) -> str:
    """§05: the *marked* word is printed twice, in two inks, slightly out of register."""
    text = loc.text("legibility.title")
    m = re.search(r"\*([^*]+)\*", text)
    if not m:
        raise BuildError(f"{loc.code}: legibility.title must mark one *word*")
    word = esc(m.group(1))
    # Punctuation touching the word stays on its line: the overprint is one atomic box, and a
    # line may break on either side of it.
    after = re.match(r"\S*", text[m.end():]).group(0)
    ovp = f'<span class="ovp"><span class="ovp-a">{word}</span><span class="ovp-b">{word}</span></span>'
    visual = esc(text[:m.start()]) + f'<span class="nb">{ovp}{esc(after)}</span>' + esc(text[m.end() + len(after):])
    return f'<span class="sr-only">{esc(text.replace("*", ""))}</span><span class="t-vis" aria-hidden="true">{visual}</span>'


# --- The terminal (§10) -----------------------------------------------------------------
# A session in NoctuaIosevka Nerd Font Mono. Its still frame is written here, into the page:
# btop's two panels, then fastfetch and its owl, then the prompt, TERM_ROWS rows. It is what
# the page shows without scripts and with motion off, and what terminal.js plays the session
# on from and comes back to; the script takes the prompt, btop's panels and fastfetch's rows
# from it, so each is written once, here. The session is TERM_COLS cells wide, and TERM_NARROW
# in a terminal under 560 px (a phone), where btop's panels are drawn narrower (the page holds
# both, and the stylesheet shows the one that fits); every other row fits both. In a wide
# terminal, the Emacs frame beside the session (emacs -nw, treemacs and a buffer) and the tmux
# status line under it come from here too.
TERM_COLS, TERM_NARROW = 46, 38
TERM_ROWS = 24
TERM_OWL = 13  # cells of fastfetch's owl
TERM_BUF = 49  # cells of the Emacs buffer in the wide terminal, its line numbers included
# Cells of text in the treemacs window. treemacs truncates its lines, and a terminal Emacs marks
# a cut line with a "$" in its last cell.
TERM_TREE_COLS = 21

class Key(str):
    """A locale key that stands for its string in a row of the terminal."""


# Nerd Fonts icons, by what the session uses them for (each is in subset-fonts.py's TERM_ICONS).
TI = {
    "os": "", "folder": "", "open": "", "branch": "", "check": "",
    "md": "", "py": "", "config": "", "sep": "", "sep_l": "",
    "round_r": "", "round_l": "", "term": "", "emacs": "", "cpu": "",
    "mem": "\U000f035b", "file": "\uf15b", "clock": "", "bolt": "", "font": "", "lock": "",
}

TERM_PROMPT = (
    ("k-dim", "╭─"), ("pl-a k-bold", f" {TI['os']} owl "), ("pl-ab", TI["sep"]), ("pl-b", f" {TI['open']} ~/fonts "),
    ("pl-bc", TI["sep"]), ("pl-c k-bold", f" {TI['branch']} main {TI['check']} "), ("pl-cf", TI["sep"]),
)
# btop's process panel: two rows (name, icon), so the still frame is exactly one screen.
TERM_PROCS = (("ghostty", "term"), ("emacs", "emacs"))
TERM_OWL_ROWS = (
    (("k-g", " ▄▄       ▄▄ "),),
    (("k-g", " █▀█▄▄▄▄▄█▀█ "),),
    (("k-g", "█ ▄▀▀▄ ▄▀▀▄ █"),),
    (("k-g", "█ █"), ("k-y", "◉"), ("k-g", " █ █"), ("k-y", "◉"), ("k-g", " █ █")),
    (("k-g", "█ ▀▄▄▀"), ("k-a", "▼"), ("k-g", "▀▄▄▀ █")),
    (("k-g", "▀█ "), ("k-dim", "░▒▓▓▓▒░"), ("k-g", " █▀")),
    (("k-g", " █ "), ("k-dim", "╲╱╲╱╲╱╲"), ("k-g", " █ ")),
    (("k-g", "  ▀▄▄▄▄▄▄▄▀  "),),
    (("k-a", "   ╨     ╨   "),),
)
# fastfetch's readings beside the owl; the cell is described in the locale's words.
TERM_INFO = (
    (("k-g k-bold", "owl"), ("k-w", "@"), ("k-g k-bold", "nest")),
    (("k-dim", "────────"),),
    (("k-b k-bold", "Font  "), ("k-w", "NoctuaIosevka NFM")),
    (("k-b k-bold", "Faces "), ("k-w", f"{len(ALL_FACES)} = {len(WEIGHTS)} × {len(WIDTHS)} × {len(SLOPES)}")),
    (("k-b k-bold", "Cell  "), ("k-w", Key("term.cell"))),
    (("k-b k-bold", "Icons "), ("k-w", "Nerd Fonts 3.4.0")),
    (("k-b k-bold", "Base  "), ("k-w", "Iosevka 34.7.0")),
    (("k-b k-bold", "Lic   "), ("k-w", "SIL OFL 1.1")),
    tuple((f"blk-{i}", "███") for i in range(1, 8)),
)
# The repository in treemacs: noctua-iosevka/ open, with everything it holds. treemacs draws no
# guides by default; it indents each level by two spaces (treemacs-indentation), and sorts each
# folder's directories, then its files, by name, capitals first (treemacs-sorting).
TERM_TREE = (
    (("k-b k-bold", f"{TI['open']} noctua-fonts"),),
    (("", "  "), ("k-b", f"{TI['folder']} docs")),
    (("", "  "), ("k-b", f"{TI['folder']} licenses")),
    (("", "  "), ("k-b", f"{TI['open']} noctua-iosevka")),
    (("", "    "), ("k-b", f"{TI['folder']} TTF")),
    (("", "    "), ("k-b", f"{TI['folder']} TTF-nerdfonts")),
    (("", "    "), ("k-b", f"{TI['folder']} WOFF2")),
    (("", "    "), ("k-b", f"{TI['folder']} WOFF2-nerdfonts")),
    (("", "    "), ("k-b", f"{TI['folder']} licenses")),
    (("", "    "), ("k-w", f"{TI['config']} private-build-plans.toml")),
    (("", "  "), ("k-b", f"{TI['folder']} noctua-noto")),
    (("", "  "), ("k-b", f"{TI['folder']} site")),
    (("", "  "), ("k-b", f"{TI['folder']} symbols-nerd-font")),
    (("", "  "), ("k-b", f"{TI['folder']} tests")),
    (("", "  "), ("k-b", f"{TI['folder']} tools")),
    (("", "  "), ("k-w", f"{TI['file']} LICENSE")),
    (("", "  "), ("k-w", f"{TI['md']} README.md")),
    (("", "  "), ("k-w", f"{TI['file']} SHA256SUMS")),
)
# The ghostty config open in Emacs, its comments in the locale's words.
TERM_BUF_ROWS = (
    (("k-dim k-it", "# ~/.config/ghostty/config"),),
    (("k-dim k-it", "# "), ("k-dim k-it", Key("term.c1"))),
    (("k-b", "font-family"), ("k-w", " = "), ("k-a", '"NoctuaIosevka Nerd Font Mono"')),
    (("k-b", "font-size"), ("k-w", "   = "), ("k-y", "13")),
    (),
    (("k-dim k-it", "# "), ("k-dim k-it", Key("term.c2"))),
    (("k-dim k-it", "# font-feature = -calt"),),
    (),
    (("k-dim k-it", "# "), ("k-dim k-it", Key("term.c3"))),
    (("k-c", " ".join(TI[k] for k in ("os", "folder", "branch", "check", "md", "py", "term", "emacs", "cpu", "mem", "clock", "font", "lock", "bolt"))),),
    (("k-dim", " ".join("▔" * 14)),),
    (("pl-a", " a "), ("pl-ab", TI["sep"]), ("pl-b", " b "), ("pl-bc", TI["sep"]), ("pl-c", " c "), ("pl-cf", TI["sep"]),
     ("k-dim", " "), ("pl-cf", TI["round_l"]), ("pl-c", " round "), ("pl-cf", TI["round_r"])),
)
# Emacs gives each window its own mode line. The buffer's, in the prompt's Powerline segments:
# the buffer, its major mode (the one Emacs 30 picks for this file, conf-unix-mode), the branch
# and where point is. treemacs's, as treemacs draws it beside a Powerline mode line (spaceline):
# its major mode, here in the inactive window's colours.
TERM_TREE_MODE = (("pl-d", " Treemacs "), ("pl-df", TI["sep"]))
TERM_MODE = (("pl-a k-bold", f" {TI['emacs']} config "), ("pl-ab", TI["sep"]), ("pl-b", " Conf[Unix] "), ("pl-bd", TI["sep"]),
             ("pl-d", f" {TI['branch']} main  All L3 "), ("pl-df", TI["sep"]))
# The echo area, across the frame, with what Emacs says when it starts on a file.
TERM_ECHO = (("k-dim", "For information about GNU Emacs and the GNU system, type C-h C-a."),)
TERM_STATUS = (("pl-a k-bold", f" {TI['term']} 0 "), ("pl-ab", TI["sep"]), ("pl-b", " 1:zsh* "), ("pl-bd", TI["sep"]),
               ("pl-d tmux-more", " 2:emacs 3:btop "), ("pl-df", TI["sep"]))
# The time a still frame shows btop's graphs at, and the seed of their noise: the same every time.
TERM_STILL_AT, TERM_SEED = 5.4, 7


def _rng(seed: int):
    """motion.js's seeded generator (mulberry32), so a still frame is the same on every build."""
    a = seed & 0xFFFFFFFF

    def nxt() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((a ^ (a >> 15)) * (a | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return nxt


def _js_round(x: float) -> int:
    return math.floor(x + 0.5)


def _braille(levels: list[int]) -> str:
    """Two samples per character, four dot rows, filled bottom-up in each column."""
    left, right = (0x40, 0x04, 0x02, 0x01), (0x80, 0x20, 0x10, 0x08)
    out = []
    for i in range(0, len(levels), 2):
        b = 0
        for k in range(min(4, levels[i])):
            b |= left[k]
        for k in range(min(4, levels[i + 1] if i + 1 < len(levels) else 0)):
            b |= right[k]
        out.append(chr(0x2800 + b))
    return "".join(out)


def _bar(k: float, n: int) -> str:
    full = math.floor(k * n)
    part = k * n - full
    tip = ("▓" if part > 0.66 else "▒" if part > 0.33 else "░") if full < n else ""
    return "█" * full + tip + " " * max(0, n - full - 1)


def term_panels(cols: int) -> list[tuple[str, tuple, dict]]:
    """btop's cpu and process panels as they stand TERM_STILL_AT seconds in: (part, segments,
    data) per row. terminal.js draws the same rows while the session plays."""
    rand = _rng(TERM_SEED)
    vals = [1 + int(rand() * 3) for _ in range((cols - 4) * 2)]
    time = TERM_STILL_AT
    for j in range(len(vals) // 2 - 1, -1, -1):
        at = time - j * 0.09
        del vals[:2]
        for k in range(2):
            vals.append(max(0, min(8, _js_round(4 + math.sin(at * 3 + k) * 2.2 + math.sin(at * 7.3) * 1.4 + (rand() - 0.5) * 2.2))))

    def top(title: str, right: str) -> tuple:
        return (("k-dim", f"╭─ {title} {'─' * max(1, cols - 8 - len(title) - len(right))} {right} ─╮"),)

    bottom = (("k-dim", f"╰{'─' * (cols - 2)}╯"),)
    n = max(4, (cols - 26) // 2)
    c0 = 0.35 + 0.3 * math.sin(time * 2.1) ** 2
    c1 = 0.2 + 0.5 * math.cos(time * 1.3) ** 2
    pc = lambda x: str(_js_round(x * 100)).rjust(3)  # noqa: E731
    rows = [
        ("top", top("cpu", "3.1 GHz"), {}),
        ("g1", (("k-dim", "│ "), ("k-g", _braille([max(0, x - 4) for x in vals])), ("k-dim", " │")), {}),
        ("g2", (("k-dim", "│ "), ("k-g", _braille([min(4, x) for x in vals])), ("k-dim", " │")), {}),
        ("c", (("k-dim", "│ "), ("k-w", "c0 ▕"), ("k-a", _bar(c0, n)), ("k-w", f"▏{pc(c0)}% c1 ▕"), ("k-a", _bar(c1, n)),
               ("k-w", f"▏{pc(c1)}%"), ("k-dim", f"{' ' * max(0, cols - 22 - 2 * n)}│")), {}),
        ("bottom", bottom, {}),
        ("top", top("proc", f"{len(TERM_PROCS)} tasks"), {}),
    ]
    for i, (name, icon) in enumerate(TERM_PROCS):
        k = abs(math.sin(time * (0.7 + i * 0.4) + i))
        rows.append(("proc", (("k-dim", "│ "), ("k-b", f"{TI[icon]} "), ("k-w", name.ljust(9)), ("k-g", _bar(k, cols - 20)),
                              ("k-w", f"{str(_js_round(k * 100)).rjust(4)}%"), ("k-dim", " │")), {"name": name, "icon": TI[icon]}))
    rows.append(("bottom", bottom, {}))
    return rows


def _cells(segs) -> int:
    return sum(len(text) for _, text in segs)


def _term_line(segs, cls: str = "term-line", **data) -> str:
    attrs = "".join(f' data-{k}="{esc(str(v))}"' for k, v in data.items())
    spans = "".join(f'<span class="{c}">{esc(t)}</span>' if c else f"<span>{esc(t)}</span>" for c, t in segs)
    return f'<div class="{cls}"{attrs}>{spans}</div>'


def _term_text(loc: Locale, segs) -> tuple:
    """Segments with the locale's strings in place of their keys."""
    return tuple((c, loc.raw(t) if isinstance(t, Key) else t) for c, t in segs)


def term_still(loc: Locale) -> list[tuple[str, tuple, dict]]:
    """The still frame as (row kind, segments, data), both widths of btop's panels included."""
    prompt = lambda cmd, cursor=False: (  # noqa: E731
        ("prompt1", TERM_PROMPT, {}),
        ("prompt2", (("k-dim", "╰─"), ("k-c k-bold", "❯ "), ("k-w term-input", cmd)) + ((("term-cursor", " "),) if cursor else ()), {}),
    )
    rows = [*prompt("btop --preset glyphs")]
    for cols in (TERM_COLS, TERM_NARROW):
        rows += [("panel", segs, {"cols": cols, "part": part, **data}) for part, segs, data in term_panels(cols)]
    rows += prompt("fastfetch")
    blank = (("", " " * TERM_OWL),)
    for i in range(max(len(TERM_OWL_ROWS), len(TERM_INFO))):
        info = _term_text(loc, TERM_INFO[i]) if i < len(TERM_INFO) else ()
        rows.append(("ff", (TERM_OWL_ROWS[i] if i < len(TERM_OWL_ROWS) else blank) + (("", " "),) + info, {}))
    rows += prompt("", cursor=True)
    return rows


def check_term_frame(locales: dict[str, "Locale"]) -> None:
    """Every row of the still frame fits the session (btop's panels fill it exactly), in both
    widths, and every line of the Emacs buffer fits the buffer."""
    for code, loc in locales.items():
        rows = term_still(loc)
        for cols in (TERM_COLS, TERM_NARROW):
            frame = [(kind, segs) for kind, segs, data in rows if data.get("cols", cols) == cols]
            if len(frame) != TERM_ROWS:
                raise BuildError(f"the terminal's still frame has {len(frame)} rows at {cols} cells, not {TERM_ROWS}")
            for kind, segs in frame:
                if _cells(segs) > cols or (kind == "panel" and _cells(segs) != cols):
                    raise BuildError(f"{code}: a {kind} row of the terminal is {_cells(segs)} cells; the session has {cols}")
        for segs in TERM_BUF_ROWS:
            if 4 + _cells(_term_text(loc, segs)) > TERM_BUF:
                raise BuildError(f"{code}: a line of the terminal's Emacs buffer is too long for its {TERM_BUF} cells")
    if _cells(TERM_TREE_MODE) > TERM_TREE_COLS:
        raise BuildError(f"the treemacs mode line is too long for its {TERM_TREE_COLS} cells")


def _truncated(segs, cols: int) -> tuple:
    """A row cut at a window's edge, as a terminal Emacs cuts a truncated line: the text fills
    all but the last cell, which shows a "$"."""
    if _cells(segs) <= cols:
        return tuple(segs)
    out, room = [], cols - 1
    for c, t in segs:
        if room > 0:
            out.append((c, t[:room]))
            room -= len(t[:room])
    return tuple(out) + (("k-dim", "$"),)


def gen_term_still(loc: Locale, page: dict) -> str:
    out = []
    for kind, segs, data in term_still(loc):
        out.append(_term_line(segs, row=kind, **data))
    return "".join(out)


def gen_term_side(loc: Locale, page: dict) -> str:
    """The Emacs frame of the wide terminal: treemacs and the buffer, each with its mode line,
    and the echo area."""
    spans = lambda segs: "".join(f'<span class="{c}">{esc(t)}</span>' for c, t in segs)  # noqa: E731
    tree = "".join(_term_line(_truncated(segs, TERM_TREE_COLS)) for segs in TERM_TREE)
    buf = "".join(_term_line((("k-dim", f"{i + 1:>3} "),) + _term_text(loc, segs)) for i, segs in enumerate(TERM_BUF_ROWS))
    return (f'<div class="term-tree">{tree}</div><div class="term-buf">{buf}</div>'
            f'<div class="term-tree-mode">{spans(TERM_TREE_MODE)}</div><div class="term-mode">{spans(TERM_MODE)}</div>'
            f'<div class="term-echo">{spans(TERM_ECHO)}</div>')


def gen_term_status(loc: Locale, page: dict) -> str:
    """The tmux status line. Its clock is read by terminal.js; without scripts it is left out."""
    segs = "".join(f'<span class="{c}">{esc(t)}</span>' for c, t in TERM_STATUS)
    clock = (f'<span class="term-clock js-only"><span class="pl-cf">{TI["sep_l"]}</span>'
             f'<span class="pl-c k-bold"> {TI["clock"]} <span class="term-time">--:--</span> </span></span>')
    return f'{segs}<span class="sp"></span>{clock}'


GENERATORS = {
    "chips": gen_chips, "wall": gen_wall, "ladder": gen_ladder, "small_sizes": gen_small_sizes,
    "sets": gen_sets, "set_default": gen_set_default, "ss_options": gen_ss_options,
    "cv_pick": gen_cv_pick, "cv_count": gen_cv_count, "ligatures": gen_ligatures,
    "icon_strip": gen_icon_strip, "coverage": gen_coverage, "downloads": gen_downloads,
    "title_faces": gen_title_faces, "title_widths": gen_title_widths, "title_slopes": gen_title_slopes,
    "title_legibility": gen_title_legibility, "title_scripts": gen_title_scripts,
    "term_still": gen_term_still, "term_side": gen_term_side, "term_status": gen_term_status,
}

# --- Titles set on one line, fitted to the column ---------------------------------------
# Three section titles run the full width on one line (the others wrap). In a monospace a
# line is exactly its character count times the advance, so the size that fills the column is
# known here: 100cqi / (characters × 0.456 em, the Condensed advance, plus a little slack).
# Where that size would fall under FIT_MIN, the title wraps at its usual size instead.
FIT_ADVANCE = 0.456
FIT_SLACK = 1.03
FIT_MIN = 44  # px
FIT_TITLES = (
    ("faces-title", lambda loc: loc.text("faces.title")),
    ("sets-title", lambda loc: loc.text("sets.title")),
    ("scripts-title", scripts_title_visible),
)

# --- The hero's meta row -----------------------------------------------------------------
# Pills over the title: the build, the release and the licence, then the face the hero is
# showing (cycler.js names its file, up to META_FILE_CHARS characters) and, at the right, the
# hint. The face pill is shown only where the whole row holds on one line with the longest
# name, so the hint never drops to a second row. Every pill is set in the 0.6 em monospace at
# META_PX, so its width is known here: its characters × (0.6 em plus its tracking), plus its
# padding and borders in px. These are site.css's sizes (.hero-meta, .now, .hero-hint).
META_PX = 11
META_PILL = (0.6 + 0.14, 2 * 12 + 2)
META_FILE = (0.6 + 0.02, 39 + 8 + 4 + 12 + 2)  # the "Ag" disc, the gap, padding, borders
META_FILE_GAP = 12  # the face pill's left margin
META_HINT = (0.6 + 0.08, 8 + 8 + 2 * 11 + 2)  # the dot, the gap, padding, borders
META_FILE_CHARS = max(len(file_stem(*face)) for face in ALL_FACES) + len(".woff2")


def meta_pills(loc: "Locale") -> tuple[str, ...]:
    """The text of the pills before the face pill, as the template writes them."""
    return (loc.text("hero.meta_build"), loc.text("hero.meta_release"), "SIL OFL 1.1")


def meta_row_width(loc: "Locale") -> int:
    """The px the hero's meta row needs to hold every pill on one line, the longest file name
    in the face pill. Each pill but the hint overlaps the next by 1 px."""
    em, px = META_PILL
    width = sum(len(text) * em * META_PX + px for text in meta_pills(loc))
    width += META_FILE_GAP + META_FILE_CHARS * META_FILE[0] * META_PX + META_FILE[1]
    width += len(loc.text("hero.hint")) * META_HINT[0] * META_PX + META_HINT[1]
    return math.ceil(width - len(meta_pills(loc)) - 1)


def facts_css(locales: dict[str, "Locale"]) -> str:
    """The stylesheet's measured values: the fitted titles and the width the hero's face pill
    needs, per language, the share of the ASCII glyphs each stylistic set redraws (the bars
    under the set cards), and the set the page starts in."""
    lines = [
        "/* Generated by site/build.py from the locale strings and the font facts. Do not edit. */",
    ]
    for code, loc in locales.items():
        for el_id, text_of in FIT_TITLES:
            em = round(len(text_of(loc)) * FIT_ADVANCE * FIT_SLACK, 2)
            lines.append(
                f"@container head (min-width: {round(em * FIT_MIN)}px) {{ html[lang=\"{code}\"] #{el_id} "
                f"{{ white-space: nowrap; max-width: none; font-size: calc(100cqi / {em}); }} }}"
            )
        lines.append(
            f"@container meta (min-width: {meta_row_width(loc)}px) {{ html[lang=\"{code}\"] .hero-meta .now "
            f"{{ display: inline-flex; }} }}"
        )
    for tag, _, changed in STYLISTIC_SETS:
        lines.append(f'.set[data-ss="{tag}"] {{ --k: {len(changed) / ASCII_VISIBLE:.3f}; }}')
    # The set the lens and the §06 title start in (sets.js changes it on a pick).
    lines.append(f'.lens-stage {{ --feat: "{SET_DEFAULT}"; }}')
    lines.append(f'.t-sets, .t-sets-num {{ font-feature-settings: "{SET_DEFAULT}" 1; }}')
    return "\n".join(lines) + "\n"


# --- Strings the terminal prints into a fixed grid ---------------------------------------
# On a phone the session is 38 cells wide; a fastfetch line is the owl (13), a space and a
# six-cell label, so the value beside "Cell" has 18 cells. The editor buffer of the wide
# terminal has room for 43 after its line number and "# ". A longer translation would be
# clipped. (check_term_frame then measures every row the build draws.)
TERM_ROOM = {"term.cell": TERM_NARROW - TERM_OWL - 1 - 6, "term.c1": TERM_BUF - 4 - 2, "term.c2": TERM_BUF - 4 - 2, "term.c3": TERM_BUF - 4 - 2}


def check_term_strings(locales: dict[str, "Locale"]) -> None:
    for code, loc in locales.items():
        for key, room in TERM_ROOM.items():
            value = loc.strings.get(key, "")
            if len(value) > room:
                raise BuildError(f"{code}: {key!r} is {len(value)} cells; the terminal has room for {room}")

# ---------------------------------------------------------------------------
# Pages, stylesheet, strings
# ---------------------------------------------------------------------------

def page_values(code: str) -> dict[str, str]:
    p = PAGES[code]
    return {
        "lang": code, "root": p["root"], "canonical": p["canonical"],
        "url_en": PAGES["en"]["canonical"], "url_pt": PAGES["pt-BR"]["canonical"],
        "og_locale": p["og_locale"], "og_locale_alt": p["og_locale_alt"],
        "href_en": p["href_en"], "href_pt": p["href_pt"],
        "cur_en": ' aria-current="page"' if code == "en" else "",
        "cur_pt": ' aria-current="page"' if code == "pt-BR" else "",
        "codepoints": facts(code)["codepoints"],
        "sets": facts(code)["sets"],
        "variants": facts(code)["variants"],
        # The repository, from tools/font-archives.json: its page, and its name as the footer shows it.
        "repo_url": REPO_URL,
        "repo_label": REPO_URL.removeprefix("https://"),
        # The squint slider's first reading, with the language's decimal separator.
        "squint0": "0.0 px" if code == "en" else "0,0 px",
        # Marks style names (file-name words such as "SemiBold") as English on other pages.
        "lang_en": "" if code == "en" else ' lang="en"',
    }


PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def fill_facts(text: str, code: str, key: str) -> str:
    """Fills {fact} placeholders of a string the template renders; any other placeholder fails."""
    values = facts(code)

    def sub(m: re.Match) -> str:
        if m.group(1) not in values:
            raise BuildError(f"{code}: {key!r} has the placeholder {m.group(0)} and the template fills only {sorted(values)}")
        return values[m.group(1)]

    return PLACEHOLDER.sub(sub, text)


def render(template: str, loc: Locale) -> str:
    values = page_values(loc.code)

    def sub(m: re.Match) -> str:
        kind, name = m.group(1), m.group(2)
        if kind == "@":
            if name not in values:
                raise BuildError(f"unknown page value {{{{@{name}}}}}")
            return values[name]
        if kind == "%":
            if name not in GENERATORS:
                raise BuildError(f"unknown fragment {{{{%{name}}}}}")
            return GENERATORS[name](loc, PAGES[loc.code])
        if name.startswith("js."):
            raise BuildError(f"template uses the script-only key {name!r}")
        text = fill_facts(loc.raw(name), loc.code, name)
        return text if kind == "&" else esc(text)

    out = TAG.sub(sub, template)
    left = re.search(r"\{\{|\}\}", out)
    if left:
        raise BuildError(f"{loc.code}: malformed template tag near {out[max(0, left.start() - 40):left.end() + 40]!r}")
    return out


def fonts_css() -> str:
    lines = [
        "/* Generated by site/build.py. One @font-face per subset face that site/subset-fonts.py writes",
        "   into ../fonts/. Every face is a real file: the page sets font-synthesis: none. Do not edit. */",
    ]
    for fam in FAMILIES:
        for w, x, s in fam.faces:
            stem = file_stem(w, x, s, fam.prefix)
            lines.append(
                f'@font-face{{font-family:"{fam.css}";src:url("../fonts/{fam.folder}/{stem}.woff2") format("woff2");'
                f"font-weight:{WEIGHTS[w][0]};font-stretch:{WIDTHS[x][2]};font-style:{SLOPES[s][1]};"
                f"font-display:{fam.display}}}"
            )
    return "\n".join(lines) + "\n"


def face_manifest() -> dict:
    """What the scripts need to know about the faces, for strings.js."""
    return {
        "weights": [[w, n] for w, n in WEIGHTS],
        "widths": [[n, adv, pct, kw] for n, adv, pct, kw in WIDTHS],
        "widthClass": list(WIDTH_CLASS),
        "italicAngle": list(ITALIC_ANGLE),
        "slopes": [[n, css] for n, css in SLOPES],
        "faces": len(ALL_FACES),
        "families": {f.key: f.css for f in FAMILIES},
        "sets": [[tag, name, changed] for tag, name, changed in STYLISTIC_SETS],
    }


def strings_js(locales: dict[str, Locale]) -> str:
    table = {}
    for code, loc in locales.items():
        table[code] = {k[3:]: v for k, v in sorted(loc.strings.items()) if k.startswith("js.")}
    body = json.dumps(table, ensure_ascii=False, sort_keys=True, indent=1)
    faces = json.dumps(face_manifest(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "// Generated by site/build.py from site/i18n/*.json and the face matrix. Do not edit.\n"
        f"const TABLE = {body};\n"
        f"export const FACES = {faces};\n"
        'const lang = document.documentElement.lang in TABLE ? document.documentElement.lang : "en";\n'
        "export const LANG = lang;\n"
        "/** A string for the page language, with {name} placeholders filled from vars. */\n"
        "export function t(key, vars) {\n"
        "  let s = TABLE[lang][key];\n"
        "  if (s === undefined) return key;\n"
        "  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));\n"
        "  return s;\n"
        "}\n"
    )


def load_locales() -> dict[str, Locale]:
    locales = {}
    for code in LOCALES:
        path = I18N / f"{code}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            raise BuildError(f"cannot read {path}: {err}") from err
        if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
            raise BuildError(f"{path}: expected a flat object of strings")
        empty = [k for k, v in data.items() if not v.strip()]
        if empty:
            raise BuildError(f"{path}: empty strings for {empty}")
        locales[code] = Locale(code, data)
    keys = {code: set(loc.strings) for code, loc in locales.items()}
    base = keys[LOCALES[0]]
    for code in LOCALES[1:]:
        missing = sorted(base - keys[code])
        extra = sorted(keys[code] - base)
        if missing or extra:
            raise BuildError(f"locale keys differ: missing in {code}: {missing}; missing in {LOCALES[0]}: {extra}")
    return locales


def static_files() -> dict[str, bytes]:
    out = {}
    for path in sorted(STATIC.rglob("*")):
        if path.is_file():
            out["assets/" + path.relative_to(STATIC).as_posix()] = path.read_bytes()
    return out


def script_keys(files: dict[str, bytes]) -> set[str]:
    used = set()
    for rel, data in files.items():
        if rel.endswith(".js"):
            used.update(JS_KEY.findall(data.decode("utf-8")))
    return used


def build() -> dict[str, bytes]:
    """Every file this script owns under site/public/, as relative path -> bytes."""
    template = TEMPLATE.read_text(encoding="utf-8")
    locales = load_locales()
    check_term_strings(locales)
    check_term_frame(locales)
    files: dict[str, bytes] = {}
    for code, loc in locales.items():
        files[PAGES[code]["path"]] = render(template, loc).encode("utf-8")
    statics = static_files()
    files.update(statics)
    files["assets/css/fonts.css"] = fonts_css().encode("utf-8")
    files["assets/css/facts.css"] = facts_css(locales).encode("utf-8")
    files["assets/js/strings.js"] = strings_js(locales).encode("utf-8")

    # Every key must be read somewhere: by the template, a fragment, or a script.
    js_used = script_keys(statics)
    for code, loc in locales.items():
        js_keys = {k[3:] for k in loc.strings if k.startswith("js.")}
        unknown = sorted(js_used - js_keys)
        if unknown:
            raise BuildError(f"{code}: scripts call t() with keys the locale lacks: {unknown}")
        unused = sorted(k for k in loc.strings if not k.startswith("js.") and k not in loc.used)
        unused += sorted("js." + k for k in js_keys - js_used)
        if unused:
            raise BuildError(f"{code}: keys that nothing uses: {unused}")
    return files


def owned(rel: str) -> bool:
    return not rel.startswith(FONTS_DIR)


def public_files(public: Path) -> dict[str, Path]:
    if not public.is_dir():
        return {}
    return {p.relative_to(public).as_posix(): p for p in sorted(public.rglob("*")) if p.is_file()}


def check(public: Path = PUBLIC) -> list[str]:
    """Differences between a fresh build and site/public/, as human-readable lines (empty = in
    sync)."""
    want = build()
    have = public_files(public)
    problems = []
    for rel, data in sorted(want.items()):
        if rel not in have:
            problems.append(f"missing: site/public/{rel}")
        elif have[rel].read_bytes() != data:
            problems.append(f"differs: site/public/{rel}")
    for rel in sorted(have):
        if owned(rel) and rel not in want:
            problems.append(f"not produced by the build: site/public/{rel}")
    return problems


def write(public: Path = PUBLIC) -> list[str]:
    want = build()
    written = []
    for rel, data in sorted(want.items()):
        dest = public / rel
        if dest.is_file() and dest.read_bytes() == data:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        written.append(rel)
    for rel, path in public_files(public).items():
        if owned(rel) and rel not in want:
            path.unlink()
            written.append(f"{rel} (removed)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="rebuild in memory and exit 1 if site/public/ differs")
    args = parser.parse_args(argv)
    try:
        if args.check:
            problems = check()
            for line in problems:
                print(line, file=sys.stderr)
            if problems:
                print(f"site/public/ is out of date: {len(problems)} difference(s). Run python3 site/build.py.", file=sys.stderr)
                return 1
            print("site/public/ matches the sources.")
            return 0
        written = write()
        print(f"wrote {len(written)} file(s) under site/public/" + "".join(f"\n  {w}" for w in written))
        return 0
    except BuildError as err:
        print(f"build failed: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
