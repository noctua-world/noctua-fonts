#!/usr/bin/env python3
"""Write the subset WOFF2 faces of the specimen site into docs/assets/fonts/.

The sources are the built fonts of this repository, read and never changed:

    noctua-iosevka/TTF/NoctuaIosevka-*.ttf                  135 faces
    noctua-iosevka/TTF-nerdfonts/NoctuaIosevkaNerdFontMono-{Regular,Bold,Italic}.ttf

Five families come out, each a subset of the same files (the face matrix and the CSS
family names live in site/build.py, which writes the @font-face rules):

    text/     135 faces  "Noctua Iosevka"    the running text and the type tester
    display/  135 faces  "NI Display"        titles, headings, tapes, the width ladder
    swatch/   135 faces  "NI Swatch"         the 135-face wall and the explorer stage
    lab/        1 face   "NI Lab"            the character-variant machine (cv01-cv99) and
                                              the coverage strips
    term/       3 faces  "NoctuaIosevka Nerd Font Mono"  the terminal

and the licences travel with them, into docs/assets/fonts/licenses/: the SIL OFL 1.1 of
Iosevka, and the Nerd Fonts MIT licence because a Nerd Font face ships too.

The Unicode repertoire of each family is written below, and must cover every character
the two pages render with that family (tests/test_site.py checks the text and display
families against both locales). Layout features are kept per family: everything the page
demonstrates in the text faces, the character variants only in the lab face.

Requires fontTools and brotli, which the system Python here does not have:

    nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])' \\
      --run 'python3 site/subset-fonts.py'

Options: --jobs N (parallel workers, default 6), --only t,d,s,l,m (family codes).
The output is deterministic: head.modified is kept from the source and nothing in the
subsetting is random, so a rerun writes the same bytes.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
SOURCES = REPO / "noctua-iosevka"
OUT = REPO / "docs" / "assets" / "fonts"
LICENCES = {
    "OFL-Iosevka.txt": REPO / "noctua-iosevka" / "licenses" / "OFL-Iosevka.txt",
    "LICENSE-NerdFontsSymbolsOnly.txt": REPO / "symbols-nerd-font" / "licenses" / "LICENSE-NerdFontsSymbolsOnly.txt",
}


def _build_module():
    sys.dont_write_bytecode = True  # no __pycache__ left in site/
    spec = importlib.util.spec_from_file_location("site_build", SITE / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def span(a: int, b: int) -> set[int]:
    return set(range(a, b + 1))


def chars(text: str) -> set[int]:
    return {ord(c) for c in text}


# --- Unicode repertoires -------------------------------------------------------------

BASIC_LATIN = span(0x20, 0x7E)
LATIN_1 = span(0xA0, 0xFF)
LATIN_EXT_A = span(0x100, 0x17F)
PUNCTUATION = span(0x2010, 0x2027) | span(0x2030, 0x203A) | chars("‽⁄€№™−")
GREEK = span(0x370, 0x3FF)
CYRILLIC = span(0x400, 0x45F) | chars("Ґґ")
ARROWS = span(0x2190, 0x21FF)
MATH = chars("∀∂∃∄∅∆∇∈∉∋∏∑∓∕∘∙√∝∞∠∣∥∧∨∩∪∫∴∵∼≈≠≡≤≥≪≫⊂⊃⊆⊇⊕⊗⊥⋅⋯")
BOX_BLOCKS_SHAPES = span(0x2500, 0x25FF)
BRAILLE = span(0x2800, 0x28FF)
MISC = chars("✓✗❯❮⏎⌘⌥★☆♥⚡⌀")

# Running text, in all 135 faces: both locales, the Greek and Cyrillic samples, the symbol
# line, the owl and the cursor trail (half blocks, shades, box drawing, Braille).
TEXT = BASIC_LATIN | LATIN_1 | LATIN_EXT_A | PUNCTUATION | GREEK | CYRILLIC | ARROWS | MATH | BOX_BLOCKS_SHAPES | BRAILLE | MISC

# Display type: Latin for both locales (Latin-1 holds every Portuguese letter), and the
# Cyrillic of the slope plate ("cite птица").
DISPLAY = BASIC_LATIN | LATIN_1 | chars("ŒœŸſ") | PUNCTUATION | span(0x410, 0x44F) | chars("ЁёҐґ←↑→↓")

# Two glyph pairs: "Ag" on the wall and the stage, "Aa" on the explorer chips.
SWATCH = chars(" Aag")

# The terminal: everything the session prints, the Powerline separators, and the icons.
TERM_ICONS = {
    0xE0A0, 0xE0A1, 0xE0A2, 0xE0B0, 0xE0B1, 0xE0B2, 0xE0B3, 0xE0B4, 0xE0B5, 0xE0B6, 0xE0B7,
    0xE0BC, 0xE0BE, 0xE0C0, 0xE0C2,
    0xF17C, 0xF179, 0xF17A, 0xF313, 0xF303, 0xF07B, 0xF07C, 0xE606, 0xF48A, 0xE60B, 0xE702, 0xE725,
    0xF09B, 0xE7A8, 0xF120, 0xE795, 0xE62B, 0xE632, 0xE74E, 0xF4BC, 0xF017, 0xF00C, 0xF00D, 0xF0E7,
    0xF013, 0xF1C0, 0xF15B, 0xF004, 0xF005, 0xF240, 0xF1EB, 0xF035B, 0xF03D2, 0xE615, 0xE777, 0xE626,
    0xE628, 0xF031, 0xF308, 0xF015, 0xF2DB, 0xF489, 0xF487, 0xF0AC, 0xF2C9, 0xF4A5, 0xF02D, 0xF121,
    0xF061, 0xF071, 0xF05A, 0xF0A0, 0xF417, 0xF401, 0xF490, 0xF02CA, 0xF08AE, 0xF0238, 0xF073, 0xF02B,
}
TERM = BASIC_LATIN | LATIN_1 | PUNCTUATION | ARROWS | BOX_BLOCKS_SHAPES | BRAILLE | MISC | TERM_ICONS


def lab_repertoire(build) -> set[int]:
    # The slot machine's glyphs (cv28 also changes "S", so it comes along), and the sample
    # strips of the coverage table: 24 characters of each Unicode block, most of them outside
    # the text repertoire, so they live in this one face instead of in all 135.
    return chars(" S") | {ord(ch) for ch, *_ in build.CHARACTER_VARIANTS} | build.coverage_strip_chars()


# --- Layout features -----------------------------------------------------------------

BASE_FEATURES = ["ccmp", "locl", "mark", "mkmk"]
STYLISTIC = ["ss%02d" % i for i in list(range(1, 19)) + [20]]  # Iosevka 34 has no ss19
VARIANTS = ["cv%02d" % i for i in range(1, 100)]
TEXT_FEATURES = BASE_FEATURES + ["calt", "dlig", "HSKL", "zero", "onum", "lnum", "frac", "numr", "dnom"] + STYLISTIC
DISPLAY_FEATURES = BASE_FEATURES
SWATCH_FEATURES = ["ccmp"]
LAB_FEATURES = BASE_FEATURES + VARIANTS
TERM_FEATURES = BASE_FEATURES + ["calt"]

# Name records kept in every subset: copyright, family, style, unique ID, full name,
# version, PostScript name, and the licence description and URL the OFL asks to keep.
NAME_IDS = [0, 1, 2, 3, 4, 5, 6, 13, 14]


def plan(build) -> list[tuple[str, str, list[int], list[str]]]:
    """(source TTF, destination WOFF2, code points, features) for every face to write."""
    per_family = {
        "t": (TEXT, TEXT_FEATURES),
        "d": (DISPLAY, DISPLAY_FEATURES),
        "s": (SWATCH, SWATCH_FEATURES),
        "l": (lab_repertoire(build), LAB_FEATURES),
        "m": (TERM, TERM_FEATURES),
    }
    jobs = []
    for fam in build.FAMILIES:
        uni, feats = per_family[fam.key]
        for w, x, s in fam.faces:
            stem = build.file_stem(w, x, s, fam.prefix)
            jobs.append((fam.key, str(SOURCES / fam.source / f"{stem}.ttf"), str(OUT / fam.folder / f"{stem}.woff2"), sorted(uni), feats))
    return jobs


def subset_one(job) -> tuple[str, int]:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    _, src, dst, unicodes, features = job
    options = subset.Options()
    options.layout_features = list(features)
    options.flavor = "woff2"
    options.hinting = False          # the web faces are rendered unhinted, as browsers do with WOFF2
    options.desubroutinize = True
    options.name_IDs = NAME_IDS
    options.name_languages = [0x409]
    options.notdef_outline = True
    options.glyph_names = False
    options.recalc_timestamp = False
    font = TTFont(src, recalcTimestamp=False)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)
    font.flavor = "woff2"
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    tmp = dst + ".part"
    font.save(tmp, reorderTables=True)
    os.replace(tmp, dst)
    return dst, os.path.getsize(dst)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--jobs", type=int, default=6, help="parallel workers (default 6)")
    parser.add_argument("--only", default="t,d,s,l,m", help="comma-separated family codes to write (default: all)")
    args = parser.parse_args(argv)
    try:
        import fontTools  # noqa: F401
        import brotli  # noqa: F401
    except ImportError:
        print("fontTools and brotli are required; run this script through the nix-shell line in its docstring.", file=sys.stderr)
        return 2

    build = _build_module()
    only = set(args.only.split(","))
    jobs = [j for j in plan(build) if j[0] in only]
    missing = [j[1] for j in jobs if not Path(j[1]).is_file()]
    if missing:
        print(f"{len(missing)} source font(s) missing, first: {missing[0]}", file=sys.stderr)
        return 1

    totals: dict[str, int] = {}
    with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for dst, size in pool.map(subset_one, jobs, chunksize=1):
            folder = Path(dst).parent.name
            totals[folder] = totals.get(folder, 0) + size

    # The licences travel with the fonts (OFL-1.1 section 2; the Nerd Fonts MIT notice).
    lic_dir = OUT / "licenses"
    lic_dir.mkdir(parents=True, exist_ok=True)
    for name, src in LICENCES.items():
        shutil.copyfile(src, lic_dir / name)

    # Faces left over from an earlier plan would be served but never named in fonts.css.
    expected = {Path(j[2]) for j in plan(build)}
    for path in sorted(OUT.rglob("*.woff2")):
        if path not in expected:
            path.unlink()
            print(f"removed stale {path.relative_to(REPO)}")

    grand = sum(p.stat().st_size for p in OUT.rglob("*.woff2"))
    for folder, size in sorted(totals.items()):
        print(f"{folder:8} {size / 1024:9.1f} KiB written")
    print(f"all site fonts: {grand / 1024 / 1024:.2f} MiB ({grand} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
