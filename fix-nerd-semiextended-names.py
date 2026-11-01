#!/usr/bin/env python3
"""Give the SemiExtended faces of a Nerd Fonts Mono build back their family
and their bold bits.

The Nerd Fonts patcher rebuilds the names of every face it patches from its own
reading of the style. It reads every other width correctly, but it splits the
SemiExtended width (Iosevka spells it "Semi-Extended"): "Semi" is glued,
together with the weight, onto the family, and "Extended" is kept as the
style. Each SemiExtended weight therefore lands in a family of its own --
"NoctuaIosevkaBoldSemi Nerd Font Mono", style "Extended" -- instead of the
family that holds every other width, and asking for "NoctuaIosevka Nerd Font
Mono" at semi-expanded width silently hands you the nearest other width. On
the Bold weight the patcher, taking "Bold" for part of the family, also
cleared the bold bits (OS/2 fsSelection bit 5, head macStyle bit 0) that the
Bold faces of every other width carry; once the names say "Bold" again, a face
whose bits say otherwise is taken for a regular one by Windows style linking
and by the applications that read the bits.

This tool recognises those faces and rewrites their names and style bits to
exactly the convention the patcher used for the widths it did understand, then
gives the file the name its siblings follow:

    ./fix-nerd-semiextended-names.py [--dry-run] [--ttf-dir DIR] FONT [FONT ...]
    ./fix-nerd-semiextended-names.py TTF-nerdfonts WOFF2-nerdfonts
    ./fix-nerd-semiextended-names.py TTF-nerdfonts/*.ttf WOFF2-nerdfonts/*.woff2
    ./fix-nerd-semiextended-names.py --ttf-dir TTF-nerdfonts WOFF2-nerdfonts/*.woff2

Each FONT is a .ttf or .woff2 file, a directory -- which stands for the .ttf
and .woff2 files directly inside it, not those of its subdirectories -- or a
wildcard pattern. A pattern that names no existing path is expanded by the
tool itself, as a POSIX shell would have done, because cmd.exe and PowerShell
pass it to the program as it was typed; a pattern that matches nothing is an
error. Faces this tool does not fix are reported as skipped and left alone:
the other widths, fonts that are not Nerd Fonts, and faces of the other Nerd
Fonts variants ("Nerd Font", "Nerd Font Propo") unless they look mangled (see
Safety). A file of any other type (.otf, .woff, ...) named as a FONT or
matched by a pattern is refused, as is a directory that holds no .ttf or
.woff2 file.

What it recognises (mangled, as the patcher wrote it). With BASE the family
before the patch (e.g. NoctuaIosevka), WM the weight as the patcher spells it
inside the family (Thin, Extralight, Light, none for Regular, Medium, Semibold,
Bold, Extrabold, Heavy), S the slope (none, Italic or Oblique) and M the
mangled family BASE + WM + "Semi Nerd Font Mono", with no space before WM or
"Semi" (e.g. "NoctuaIosevkaBoldSemi Nerd Font Mono"):

    ID 1   M Extended[ Obl]          ID 2   Regular | Italic
    ID 3   M Extended[ S] VERSION     ID 4   M Extended[ S]
    ID 6   BASEWMSemiNFM-Extended[S]  ID 16  M       ID 17  Extended[ S]

What it writes (the convention of the correctly named siblings), with FAMILY =
"BASE Nerd Font Mono" and W the weight as the siblings spell it (Thin,
ExtraLight, Light, none for Regular, Medium, SemiBold, Bold, ExtraBold, Heavy):

    ID 1   FAMILY SemiExtended[ W unless Regular or Bold][ Obl if Oblique]
    ID 2   Regular | Bold | Italic | Bold Italic   (an Oblique counts as Italic)
    ID 3   FAMILY SemiExtended[ W][ S] VERSION
    ID 4   FAMILY SemiExtended[ W][ S]
    ID 6   BASENFM-SemiExtended[W][S]   (Bold Oblique: BASENFM-SemiExtendedObliqueBold)
    ID 16  FAMILY
    ID 17  SemiExtended[ W][ S]
    file   BASENerdFontMono-SemiExtended[W][S].ttf / .woff2
    bits   OS/2 fsSelection BOLD (bit 5) and head macStyle Bold (bit 0) set
           if W is Bold, clear otherwise; fsSelection REGULAR (bit 6) clear

Every record of those IDs is rewritten, on whatever platform and encoding the
face carries it (the patcher writes Macintosh 1/0/0 and Windows 3/1/0x409
copies with the same text). VERSION is kept from the face's own ID 3.

Style bits. The rule is the one every correctly named Nerd face of this
repository's build follows -- the four other widths, as TTF and as WOFF2 --
and it predicts each one's bits exactly: fsSelection BOLD and macStyle Bold
are set exactly on usWeightClass 700, the weight the names call Bold,
whatever the slope (ExtraBold and Heavy have them clear), and fsSelection
REGULAR only on the upright Regular of the normal width (usWidthClass 5), so
never on a SemiExtended face. Those three bits are set or cleared to follow
it, on a mangled face and on a face whose names are already fixed alike.
Every other bit is checked, not set: it must already be as the siblings carry
it, or the face is refused. Those are the slope bits -- fsSelection ITALIC
(bit 0) exactly on an Italic face, OBLIQUE (bit 9) exactly on an Oblique one,
macStyle Italic (bit 1) exactly on an Italic one -- and the bits that depend
on neither weight nor slope, the same on every sibling: fsSelection
USE_TYPO_METRICS (bit 7) and WWS (bit 8) set and all the rest clear, and no
other macStyle bit. A face fixed or found already fixed therefore carries
exactly the fsSelection and macStyle of its siblings. The plain, unpatched
faces are not the model: Iosevka's own convention sets BOLD from weight 700
up, REGULAR on every upright face below it, ITALIC on an Oblique face too
and macStyle's width bits; the patcher rewrote all of it on every Nerd face.

What it changes: the 'name' table, OS/2 fsSelection and head macStyle, and
nothing else. A TTF is loaded with recalcTimestamp=False and
recalcBBoxes=False and only its 'name' table is decompiled. The two style
fields are written into the raw table bytes (OS/2 bytes 62-63, head bytes
44-45), not through fontTools' table objects, which would recompile both
tables on save -- compiling OS/2 recomputes usFirstCharIndex and
usLastCharIndex from cmap. Every other table is copied byte for byte. The one
byte range these changes force elsewhere is head.checkSumAdjustment (head
bytes 8-11), the checksum of the whole file; head.modified is left alone. A
table that needs no change is not written: a face whose names are already
fixed keeps its 'name' table byte for byte. Every written file is reloaded
from disk and compared with the original before it replaces anything: each
table must be byte-identical to the original's with exactly the expected
style fields written into it ('name' aside when its names are rewritten;
head apart from checkSumAdjustment), every name record must hold exactly the
expected text, the records of other IDs (copyright, version, licence, the
stylistic-set names from 256 up) byte for byte, and the file read back
through fontTools must hold the expected fsSelection and macStyle and be
recognised as the fixed face.

WOFF2: a .woff2 whose fixed .ttf is found -- a TTF this same run fixed or found
already fixed (TTFs are always processed first, whatever the argument order),
<stem>.ttf in a --ttf-dir, or <stem>.ttf beside the .woff2 -- is regenerated
from that TTF (fontTools, flavor woff2, keeping the old file's WOFF2 header
version, metadata, private data and transformed tables), so the pair stays
identical in content. A TTF counterpart whose names or style bits are not
fixed is refused, unless this same run fixes it. Without one, the WOFF2's own
names and style bits are rewritten. Either way the new WOFF2 is decoded and
must hold the same tables as the old one apart from 'name' and the style
fields (head apart from checkSumAdjustment; glyf/loca compared glyph by glyph
if their bytes differ), and, when regenerated, the same tables as its TTF
apart from the glyf/loca re-encoding and the two head fields WOFF2 itself
rewrites: checkSumAdjustment and the "glyf/loca transformed" flag (bit 11 of
head.flags). Any other head change is refused -- among them the
indexToLocFormat switch a round trip makes for a TTF whose glyphs are not
2-byte aligned (none of this repository's fonts).

This is slow with fontTools: encoding a large face and decoding it to verify
take one to two minutes per WOFF2; a TTF takes seconds.

Idempotent: a face whose names and style bits already follow the convention
is reported as already fixed and left untouched. A face whose names follow it
but whose style bits do not is fixed in place, under its own file name, and
its 'name' table is kept byte for byte (a WOFF2 is regenerated from its fixed
TTF when one is found, as above).

--dry-run writes nothing. It runs every check that needs no written file --
recognition, the style bits, the target name, the TTF a WOFF2 would be
regenerated from (read from disk unless it is one this dry run would itself
fix) -- and reports what would happen, the style bits as old -> new. The
checks of the written file described above can only run for real, so a real
run can still refuse a file that the dry run passed.

Safety (fonts are untrusted binary input; every check fails closed):
  * A face is rewritten only when every identifying record equals, character
    for character, the mangled pattern rebuilt from its own OS/2 data:
    usWidthClass must be 6 (semi-expanded), usWeightClass must be the weight
    named in the family, and the fsSelection slope bits (0 italic, 9 oblique)
    must match the style. A semi-expanded Nerd Font Mono face that matches
    neither the mangled nor the fixed convention is an error, not a guess --
    and so is a mangled face whose BASE itself ends in a weight word, where
    family and weight cannot be told apart, and a semi-expanded face of
    another Nerd Fonts variant whose family carries the patcher's glued
    "Semi" right before " Nerd Font": it looks mangled, but the convention of
    that variant is not known here.
  * The style bits are computed only from that verified weight and slope, by
    the rule above, and only BOLD, REGULAR and macStyle Bold are ever
    changed. A face whose other bits differ from its siblings' (see Style
    bits) -- slope bits that contradict each other or its names, a lost WWS,
    a set UNDERSCORE, a macStyle width bit -- is refused: it has a defect
    this tool does not know, and is not repaired by guesswork. The two fields
    are written at their fixed offsets after checking that the table is long
    enough to hold them, so the write cannot reach a neighbouring field.
  * A face carrying identifier IDs whose convention is unknown here (18, 20,
    21, 22, 25), records of one ID that disagree between platforms, a DSIG
    signature (renaming would silently invalidate it), or a file type that
    does not match its extension is refused.
  * The new file name is built only from the closed weight and slope
    vocabularies above and from BASE, which must be ASCII letters and digits:
    no text from the font can put a separator or '..' into a path. The file
    stays in its own directory.
  * A wildcard is expanded only when the argument names no existing path, so
    a file whose name holds '*' or '?' is still taken literally, and what a
    pattern or a directory expands to goes through every check above, like a
    file named on the command line.
  * Symbolic links are refused (the link would be replaced by a file), and
    so is a symbolic link given as a directory.
  * An existing target is never overwritten. That includes a symbolic link
    or a hard link at the target name, even one that leads to the very file
    being fixed: the target counts as that file only when it is the same
    directory entry -- the same name, or a name differing only in case that
    the directory does not list separately (a case-insensitive file system).
    os.path.samefile alone would take a link for the source, report a rename
    that never happens and leave the link with the old names. The check is
    repeated just before the final rename; between that check and the rename
    another process could still create the target -- the tool is meant for a
    font directory nobody else is writing to.
  * Output goes to a private temporary file beside the target (mkstemp:
    exclusive creation, owner-only permissions), is flushed and fsync'ed,
    gets the original's permission bits, is verified, and only then is moved
    into place with os.replace. The old file is removed only after the new
    one is in place, and never when both names are the same file (a
    case-insensitive file system); on any failure the temporary file is
    deleted and the original is untouched.
  * Every font is closed before anything is renamed or removed (Windows
    refuses to replace an open file).

The convention was derived from, and is only applied to, the Mono variant
("Nerd Font Mono", PostScript "NFM") of font-patcher 3.4.0 -- the only variant
this repository builds.

Exit status: 0 when every file was fixed, already fixed or skipped; 1 when any
argument named nothing to work on or any file was refused or failed (those
files are left untouched -- the one exception, reported as such, is a fixed
file in place whose old name could not be removed); 2 on bad usage.

Requires: fonttools (plus brotli for .woff2 files)
          ->  pip install fonttools brotli
"""

import argparse
import glob
import os
import re
import shutil
import struct
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables.DefaultTable import DefaultTable
except ImportError:
    sys.exit("error: fonttools not found.  ->  pip install fonttools brotli")

# The only Nerd Fonts variant the convention below was derived from.
NERD_FAMILY = "Nerd Font Mono"
NERD_PS = "NFM"
NERD_FILE = "NerdFontMono"

WIDTH = "SemiExtended"
WIDTH_CLASS = 6  # OS/2 usWidthClass: semi-expanded

# (the patcher's spelling inside the mangled family, the siblings' spelling,
#  OS/2 usWeightClass). Regular has no word in either convention.
WEIGHTS = (
    ("Thin", "Thin", 100),
    ("Extralight", "ExtraLight", 200),
    ("Light", "Light", 300),
    ("", "", 400),
    ("Medium", "Medium", 500),
    ("Semibold", "SemiBold", 600),
    ("Bold", "Bold", 700),
    ("Extrabold", "ExtraBold", 800),
    ("Heavy", "Heavy", 900),
)

# The records this tool rewrites, and the identifier IDs whose convention it
# does not know: a face carrying one of the latter is refused rather than left
# half renamed.
REWRITTEN_IDS = (1, 2, 3, 4, 6, 16, 17)
UNKNOWN_IDENTIFIER_IDS = (18, 20, 21, 22, 25)

FS_ITALIC = 1 << 0  # OS/2 fsSelection
FS_BOLD = 1 << 5
FS_REGULAR = 1 << 6
FS_OBLIQUE = 1 << 9
MAC_BOLD = 1 << 0  # head macStyle
MAC_ITALIC = 1 << 1
# The bits that follow a face's weight or slope, and what every correctly
# named Nerd sibling carries in all the others: fsSelection USE_TYPO_METRICS
# (bit 7) and WWS (bit 8), and no macStyle bit at all.
FS_DEPENDENT = FS_ITALIC | FS_BOLD | FS_REGULAR | FS_OBLIQUE
MAC_DEPENDENT = MAC_BOLD | MAC_ITALIC
FS_CONSTANT = (1 << 7) | (1 << 8)
MAC_CONSTANT = 0
# Where the two style fields sit in the raw tables, each a big-endian uint16:
# fsSelection at the same offset in every OS/2 version, macStyle in the
# fixed-size head.
OS2_FS_SELECTION_OFFSET = 62
HEAD_MAC_STYLE_OFFSET = 44
HEAD_CHECKSUM_ADJUSTMENT = slice(8, 12)  # head bytes any change to the file forces
HEAD_FLAGS = slice(16, 18)
HEAD_FLAG_WOFF2_TRANSFORMED = 1 << 11  # set by WOFF2 when glyf/loca are transformed

EXTENSIONS = {".ttf": None, ".woff2": "woff2"}  # extension -> expected flavor

# A family of the Mono variant: "... Nerd Font Mono", alone or before the style
# words the legacy family (ID 1) adds.
MONO_FAMILY = re.compile(r" Nerd Font Mono(?: |$)")
# The patcher's mark on a SemiExtended face of any variant: "Semi" glued to the
# family right before " Nerd Font" (e.g. "NoctuaIosevkaBoldSemi Nerd Font Propo").
GLUED_SEMI = re.compile(r"[A-Za-z0-9]Semi Nerd Font(?: |$)")
GLOB_MAGIC = re.compile(r"[*?[]")


class Refusal(Exception):
    """A file this tool will not touch, with the reason why."""


class Incomplete(Exception):
    """The fixed file is in place, but the old one could not be removed."""


@dataclass(frozen=True)
class Face:
    base: str  # family before the patch, e.g. "NoctuaIosevka"
    weight: str  # the siblings' spelling, "" for Regular
    slope: str  # "", "Italic" or "Oblique"
    version: str  # the tail of name ID 3, e.g. "3.4.0"

    @property
    def file_stem(self):
        return f"{self.base}{NERD_FILE}-{WIDTH}{self.weight}{self.slope}"


def fixed_names(face):
    """Name ID -> text, following the correctly named siblings."""
    family = f"{face.base} {NERD_FAMILY}"
    style = " ".join(w for w in (WIDTH, face.weight, face.slope) if w)
    bold = face.weight == "Bold"
    legacy = " ".join(
        w
        for w in (
            WIDTH,
            "" if face.weight in ("", "Bold") else face.weight,
            "Obl" if face.slope == "Oblique" else "",
        )
        if w
    )
    if face.slope:
        subfamily = "Bold Italic" if bold else "Italic"
    else:
        subfamily = "Bold" if bold else "Regular"
    if bold and face.slope == "Oblique":
        ps_style = WIDTH + "ObliqueBold"  # the patcher's order for Bold Oblique
    else:
        ps_style = WIDTH + face.weight + face.slope
    return {
        1: f"{family} {legacy}",
        2: subfamily,
        3: f"{family} {style} {face.version}",
        4: f"{family} {style}",
        6: f"{face.base}{NERD_PS}-{ps_style}",
        16: family,
        17: style,
    }


def mangled_names(face, patcher_weight):
    """Name ID -> text, as the patcher wrote it for a SemiExtended face."""
    family = f"{face.base}{patcher_weight}Semi {NERD_FAMILY}"
    style = " ".join(w for w in ("Extended", face.slope) if w)
    return {
        1: f"{family} Extended" + (" Obl" if face.slope == "Oblique" else ""),
        2: "Italic" if face.slope else "Regular",
        3: f"{family} {style} {face.version}",
        4: f"{family} {style}",
        6: f"{face.base}{patcher_weight}Semi{NERD_PS}-{style.replace(' ', '')}",
        16: family,
        17: style,
    }


@dataclass(frozen=True)
class Style:
    """The two style fields a face carries."""

    fs_selection: int  # OS/2 fsSelection
    mac_style: int  # head macStyle

    def __str__(self):
        return f"fsSelection {self.fs_selection:#06x}, macStyle {self.mac_style:#06x}"


def describe_change(old, new):
    """'fsSelection 0x0180 -> 0x01a0, macStyle 0x0000 -> 0x0001'."""
    return (
        f"fsSelection {old.fs_selection:#06x} -> {new.fs_selection:#06x}, "
        f"macStyle {old.mac_style:#06x} -> {new.mac_style:#06x}"
    )


def sibling_style(face):
    """The style fields every correctly named sibling of this face carries.

    Measured on every correctly named Nerd face of this repository's build
    (the four other widths, TTF and WOFF2), whose two fields it predicts
    exactly: fsSelection BOLD and macStyle Bold are set exactly on
    usWeightClass 700, the weight the names call Bold, whatever the slope --
    ExtraBold (800) and Heavy (900) have them clear -- and fsSelection REGULAR
    only on the upright Regular of the normal width (usWidthClass 5), so never
    on a SemiExtended face. The slope bits and the constant ones are what a
    face must already carry (slope_bits_agree, constant_bits_agree): only
    BOLD, REGULAR and macStyle Bold can differ from it on a face that passes.
    """
    fs, mac = FS_CONSTANT, MAC_CONSTANT
    if face.slope == "Italic":
        fs |= FS_ITALIC
        mac |= MAC_ITALIC
    elif face.slope == "Oblique":
        fs |= FS_OBLIQUE
    if face.weight == "Bold":  # usWeightClass 700, nothing else
        fs |= FS_BOLD
        mac |= MAC_BOLD
    return Style(fs, mac)


def slope_bits_agree(slope, style):
    """The slope bits as the siblings carry them: fsSelection ITALIC exactly on
    Italic, OBLIQUE exactly on Oblique (never both), macStyle Italic exactly on
    Italic -- an Oblique face has it clear."""
    found = (
        bool(style.fs_selection & FS_ITALIC),
        bool(style.fs_selection & FS_OBLIQUE),
        bool(style.mac_style & MAC_ITALIC),
    )
    return found == (slope == "Italic", slope == "Oblique", slope == "Italic")


def constant_bits_agree(style):
    """The bits that depend on neither weight nor slope as every sibling
    carries them: fsSelection USE_TYPO_METRICS and WWS set and the rest clear
    (UNDERSCORE, NEGATIVE, OUTLINED, STRIKEOUT, the reserved bits), and no
    macStyle bit beyond Bold and Italic (the plain faces' width bits
    Condensed and Extended among them)."""
    fs_rest = style.fs_selection & ~FS_DEPENDENT
    mac_rest = style.mac_style & ~MAC_DEPENDENT
    return fs_rest == FS_CONSTANT and mac_rest == MAC_CONSTANT


@dataclass(frozen=True)
class Inspection:
    # "mangled" (names to rewrite, style bits too where they differ),
    # "misstyled" (names fixed, style bits not), "fixed", "unrelated" or
    # "suspect"
    kind: str
    face: Face = None
    reason: str = ""
    current: Style = None  # the style fields the face carries
    style: Style = None  # the style fields it must carry


def _valid_base(base):
    return bool(base) and base.isascii() and base.isalnum()


def _ends_in_weight(base):
    return any(base.lower().endswith(word.lower()) for word, _, _ in WEIGHTS if word)


def _first_difference(expected, actual):
    for name_id in sorted(expected):
        if expected[name_id] != actual.get(name_id):
            return f"name ID {name_id} is {actual.get(name_id)!r}, expected {expected[name_id]!r}"
    return "names differ"


def inspect_font(font):
    """Classify a loaded font. Reads 'name', 'OS/2' and 'head' only."""
    if "name" not in font or "OS/2" not in font or "head" not in font:
        return Inspection("unrelated", reason="no 'name', 'OS/2' or 'head' table")
    os2 = font["OS/2"]
    values = {}
    for record in font["name"].names:
        if record.nameID in REWRITTEN_IDS or record.nameID in UNKNOWN_IDENTIFIER_IDS:
            try:
                text = record.toUnicode()
            except UnicodeDecodeError:
                text = None
            values.setdefault(record.nameID, set()).add(text)

    families = {v for i in (1, 16) for v in values.get(i, ()) if v}
    if os2.usWidthClass != WIDTH_CLASS or not any("Nerd Font" in v for v in families):
        return Inspection("unrelated", reason="not a SemiExtended Nerd Font face")
    if not any(MONO_FAMILY.search(v) for v in families):
        if any(GLUED_SEMI.search(v) for v in families):
            return Inspection(
                "suspect",
                reason="looks like a mangled SemiExtended face of a Nerd Fonts variant other than Mono, "
                "whose convention this tool does not know",
            )
        return Inspection("unrelated", reason="a Nerd Fonts variant other than Mono, whose names this tool does not rewrite")

    unknown = sorted(i for i in UNKNOWN_IDENTIFIER_IDS if i in values)
    if unknown:
        return Inspection("suspect", reason=f"carries name IDs {unknown}, whose convention is unknown")
    names = {}
    for name_id in REWRITTEN_IDS:
        texts = values.get(name_id)
        if not texts:
            return Inspection("suspect", reason=f"has no name ID {name_id}")
        if len(texts) != 1 or None in texts:
            return Inspection("suspect", reason=f"name ID {name_id} differs between its records")
        (names[name_id],) = texts
    if "DSIG" in font:
        return Inspection("suspect", reason="carries a DSIG signature that renaming would invalidate")

    weight = [w for w in WEIGHTS if w[2] == os2.usWeightClass]
    if not weight:
        return Inspection("suspect", reason=f"usWeightClass {os2.usWeightClass} is not one of the nine weights")
    patcher_weight, sibling_weight, _ = weight[0]
    if os2.fsSelection & FS_OBLIQUE:
        slope = "Oblique"
    elif os2.fsSelection & FS_ITALIC:
        slope = "Italic"
    else:
        slope = ""
    _, sep, version = names[3].rpartition(" ")
    if not sep or not version or not all(part.isdigit() for part in version.split(".")):
        return Inspection("suspect", reason=f"name ID 3 {names[3]!r} does not end in a version")

    # Both readings are tried: a base that itself ends in "Semi" makes a fixed
    # family look like a mangled one at first sight.
    family = names[16]
    candidates = []
    for kind, tail, build in (
        ("mangled", f"{patcher_weight}Semi {NERD_FAMILY}", lambda f: mangled_names(f, patcher_weight)),
        ("fixed", f" {NERD_FAMILY}", fixed_names),
    ):
        base = family[: -len(tail)] if family.endswith(tail) else ""
        if _valid_base(base):
            face = Face(base, sibling_weight, slope, version)
            candidates.append((kind, face, build(face)))
    for kind, face, expected in candidates:
        if names == expected:
            if kind == "mangled" and _ends_in_weight(face.base):
                # "FooBoldSemi" at weight 400 reads as family "FooBold", Regular;
                # at 700 it would read as "Foo", Bold. Do not guess.
                return Inspection(
                    "suspect", reason=f"family {face.base!r} ends in a weight word; family and weight cannot be told apart"
                )
            # The bits this tool does not set must already be right: a face
            # that differs there has a defect the patcher's misreading does
            # not explain, and is refused rather than repaired by guesswork.
            current = Style(os2.fsSelection, font["head"].macStyle)
            if not slope_bits_agree(slope, current):
                return Inspection(
                    "suspect",
                    reason=f"its slope bits ({current}) do not follow the siblings' convention for "
                    + (f"an {slope} face" if slope else "an upright face"),
                )
            if not constant_bits_agree(current):
                return Inspection(
                    "suspect",
                    reason=f"its style bits ({current}) differ from the siblings' in bits that depend on "
                    f"neither weight nor slope (fsSelection {FS_CONSTANT:#06x} and macStyle "
                    f"{MAC_CONSTANT:#06x} there)",
                )
            style = sibling_style(face)
            if kind == "fixed" and style != current:
                kind = "misstyled"
            return Inspection(kind, face, current=current, style=style)
    if candidates:
        kind, _, expected = candidates[0]
        return Inspection("suspect", reason=f"names match neither convention; as {kind}, " + _first_difference(expected, names))
    return Inspection("suspect", reason=f"family {family!r} matches neither convention")


def open_font(path, flavor_expected):
    font = TTFont(path, lazy=True, recalcBBoxes=False, recalcTimestamp=False)
    if font.flavor != flavor_expected:
        font.close()
        raise Refusal(f"file content is {font.flavor or 'a plain sfnt'}, which does not match its extension")
    return font


# ---------------------------------------------------------------- verification


def _name_records(font):
    return [(r.platformID, r.platEncID, r.langID, r.nameID, r) for r in font["name"].names]


def check_names(original, written, expected):
    """Every record kept, the rewritten ones holding exactly the expected text."""
    before = sorted(_name_records(original), key=lambda t: t[:4])
    after = sorted(_name_records(written), key=lambda t: t[:4])
    if [t[:4] for t in before] != [t[:4] for t in after]:
        raise Refusal("verification failed: the set of name records changed")
    for (p, e, lang, name_id, old), (_, _, _, _, new) in zip(before, after):
        if name_id in expected:
            if new.toUnicode() != expected[name_id]:
                raise Refusal(f"verification failed: name ID {name_id} ({p},{e},{lang:#x}) is {new.toUnicode()!r}")
        elif new.toBytes() != old.toBytes():
            raise Refusal(f"verification failed: name ID {name_id} ({p},{e},{lang:#x}) changed")


def _mask_head(data, transform_flag=False):
    data = bytearray(data)
    data[HEAD_CHECKSUM_ADJUSTMENT] = b"\0\0\0\0"
    if transform_flag and len(data) >= HEAD_FLAGS.stop:
        (flags,) = struct.unpack(">H", data[HEAD_FLAGS])
        data[HEAD_FLAGS] = struct.pack(">H", flags & ~HEAD_FLAG_WOFF2_TRANSFORMED)
    return bytes(data)


def _canonical_glyphs(font):
    """Each glyph recompiled from its decoded form: same outline, same bytes."""
    glyf = font["glyf"]
    return [(name, glyf[name].compile(glyf, recalcBBoxes=False)) for name in font.getGlyphOrder()]


def glyphs_equal(a, b):
    return a.getGlyphOrder() == b.getGlyphOrder() and _canonical_glyphs(a) == _canonical_glyphs(b)


def _with_uint16(data, offset, value, tag):
    """`data` with the big-endian uint16 at `offset` replaced by `value`.

    The offset is fixed by the format, and a table too short to hold the field
    is refused rather than extended: the write can never reach past the field
    into its neighbours.
    """
    if len(data) < offset + 2:
        raise Refusal(f"table '{tag}' is too short ({len(data)} bytes) to hold its style field")
    return data[:offset] + struct.pack(">H", value) + data[offset + 2 :]


def styled(tag, data, style):
    """The raw bytes of table `tag` with the style field it holds set to `style`'s."""
    if tag == "OS/2":
        return _with_uint16(data, OS2_FS_SELECTION_OFFSET, style.fs_selection, tag)
    if tag == "head":
        return _with_uint16(data, HEAD_MAC_STYLE_OFFSET, style.mac_style, tag)
    return data


def restyle(font, style):
    """Write `style` into the raw OS/2 and head tables of `font` (not decoded).

    Each table is handed back to fontTools as raw bytes, so saving copies them
    as they are instead of recompiling them -- compiling OS/2 recomputes
    usFirstCharIndex and usLastCharIndex from cmap and decompiles head. Only
    the two uint16 fields change. A table already decompiled is refused: its
    object, not these bytes, is what fontTools would save.
    """
    for tag in ("OS/2", "head"):
        if font.isLoaded(tag):
            raise Refusal(f"internal error: '{tag}' is decompiled and would be recompiled")
        table = DefaultTable(tag)
        table.data = styled(tag, font.reader[tag], style)
        font[tag] = table


def check_tables(a, b, what, *, woff2=False, woff2_vs_sfnt=False, style=None, renamed=True):
    """Every table identical (head apart from checkSumAdjustment).

    'name' is skipped when renamed (check_names compares it record by record)
    and compared byte for byte otherwise. With `style`, `b` must hold `a`'s
    OS/2 and head with exactly those style fields written into them, every
    other byte unchanged. Between two sfnt files every byte counts. With
    woff2, at least one side is a decoded WOFF2, whose glyf/loca an encoder may
    lay out differently: when their bytes differ they are compared glyph by
    glyph instead. With woff2_vs_sfnt, `b` is a WOFF2 built from the sfnt `a`,
    and head may also differ in the flag WOFF2 sets when it transforms
    glyf/loca.
    """
    woff2 = woff2 or woff2_vs_sfnt
    tags_a, tags_b = sorted(a.reader.keys()), sorted(b.reader.keys())
    if tags_a != tags_b:
        raise Refusal(f"verification failed: {what}: the tables differ ({tags_a} / {tags_b})")
    glyphs_pending = False
    for tag in tags_a:
        if tag == "name" and renamed:
            continue
        data_a, data_b = a.reader[tag], b.reader[tag]
        if style is not None:
            data_a = styled(tag, data_a, style)
        if tag == "head":
            same = _mask_head(data_a, woff2_vs_sfnt) == _mask_head(data_b, woff2_vs_sfnt)
        else:
            same = data_a == data_b
        if not same:
            if woff2 and tag in ("glyf", "loca"):
                glyphs_pending = True
                continue
            raise Refusal(f"verification failed: {what}: table '{tag}' differs")
    if glyphs_pending and not glyphs_equal(a, b):
        raise Refusal(f"verification failed: {what}: the glyphs differ")


def check_face(written, face, style):
    """The written font, read back through fontTools' own parser, holds the
    expected style fields and is recognised as the fixed face.

    Independent of the offsets restyle and check_tables share: a wrong offset
    would pass the byte comparison, never this one.
    """
    found = Style(written["OS/2"].fsSelection, written["head"].macStyle)
    if found != style:
        raise Refusal(f"verification failed: the written file has {found}, expected {style}")
    inspection = inspect_font(written)
    if inspection.kind != "fixed" or inspection.face != face:
        raise Refusal(f"verification failed: the written file reads as {inspection.kind}, not as the fixed face")


def _flavor_tuple(flavor_data):
    return (
        flavor_data.majorVersion,
        flavor_data.minorVersion,
        flavor_data.metaData,
        flavor_data.privData,
        tuple(sorted(flavor_data.transformedTables)),
    )


WOFF2_VERSION_OFFSET = 24  # majorVersion, minorVersion: two uint16 in the fixed 48-byte header


def woff2_saver(font, old_flavor):
    """A save(fileobj) for write_temp that writes `font` as WOFF2 with the
    old file's header fields, transformed tables, metadata and private data.

    fontTools (4.61 at least) copies flavorData through a constructor that
    loses the header version -- WOFF2FlavorData(data=...) assigns minorVersion
    to majorVersion and leaves minorVersion unset -- so the version would
    silently become head.fontRevision. The two uint16 are therefore patched
    into the fixed header after saving (the header carries no checksum), and
    verification compares every one of these fields with the old file.
    """
    from fontTools.ttLib.woff2 import WOFF2FlavorData

    data = WOFF2FlavorData(transformedTables=old_flavor.transformedTables)
    data.metaData, data.privData = old_flavor.metaData, old_flavor.privData
    font.flavor, font.flavorData = "woff2", data

    def save(fh):
        font.save(fh)
        if old_flavor.majorVersion is not None and old_flavor.minorVersion is not None:
            fh.seek(WOFF2_VERSION_OFFSET)
            fh.write(struct.pack(">HH", old_flavor.majorVersion, old_flavor.minorVersion))
            fh.seek(0, os.SEEK_END)

    return save


# --------------------------------------------------------------------- writing


class Run:
    def __init__(self, dry_run, ttf_dirs):
        self.dry_run = dry_run
        self.ttf_dirs = ttf_dirs
        self.fixed_ttfs = {}  # file stem -> canonical paths of fixed TTFs seen in this run
        # Canonical paths of the TTFs a dry run would fix. Only these are taken
        # on trust as a WOFF2's counterpart: on disk they are not fixed yet (or
        # do not exist). Every other counterpart is read, in a dry run too.
        self.planned_ttfs = set()
        self.errors = 0

    def remember_ttf(self, path, face, planned=False):
        self.fixed_ttfs.setdefault(face.file_stem, set()).add(_canonical(path))
        if planned:
            self.planned_ttfs.add(_canonical(path))


def _canonical(path):
    return path.parent.resolve() / path.name


def plan_target(path, face):
    """The target path, and whether it is the source itself.

    The target is the source only when it is the same directory entry: the
    same name, or a name that differs only in case and that the directory does
    not list as an entry of its own (a case-insensitive file system answers
    for both spellings with the one entry). os.path.samefile alone is not
    enough: it follows a symbolic link and matches a hard link, so a link at
    the target name would pass for the source -- the tool would report a
    rename that never happens and leave the link holding the old names. Any
    other existing target, link or not, is refused. is_symlink comes first
    because exists() follows a link and is false for a dangling one.
    """
    target = path.with_name(face.file_stem + path.suffix.lower())
    if target.name == path.name:
        return target, True
    if target.is_symlink():
        raise Refusal(f"refusing to overwrite existing {target.name} (a symbolic link)")
    if not target.exists():
        return target, False
    if (
        target.name.casefold() == path.name.casefold()
        and target.name not in os.listdir(path.parent)
        and os.path.samefile(target, path)
    ):
        return target, True
    raise Refusal(f"refusing to overwrite existing {target.name}")


def write_temp(target, save):
    """Run save(fileobj) into a private temporary file beside target."""
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as fh:
            save(fh)
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return tmp


def install(tmp, source, target, in_place):
    """Move the verified temporary file into place, then drop the old name."""
    shutil.copymode(source, tmp)
    if in_place:
        os.replace(tmp, source)
        return
    if target.exists() or target.is_symlink():
        raise Refusal(f"refusing to overwrite {target.name}, which appeared while working")
    os.replace(tmp, target)
    # Never remove the source when both names reach the same file (a
    # case-insensitive file system): that would delete the font just written.
    if source.exists() and not os.path.samefile(source, target):
        try:
            os.remove(source)
        except OSError as exc:
            raise Incomplete(f"wrote {target.name} but could not remove the old file: {exc}") from exc


def plan_fix(path, inspection):
    """(target, in_place, renamed, restyled) for a mangled or misstyled face.

    A misstyled face keeps its names and its file name: only its style bits
    are rewritten, in place.
    """
    renamed = inspection.kind == "mangled"
    restyled = inspection.style != inspection.current
    if renamed:
        target, in_place = plan_target(path, inspection.face)
    else:
        target, in_place = path, True
    return target, in_place, renamed, restyled


def report(path, target, inspection, notes=()):
    """'-> TARGET (note; note)': what was or would be done to the face."""
    notes = list(notes)
    if inspection.kind == "misstyled":
        notes.append("names already fixed")
        if path.stem != inspection.face.file_stem:
            notes.append(f"file name differs from {inspection.face.file_stem}")
    if inspection.style != inspection.current:
        notes.append(describe_change(inspection.current, inspection.style))
    return f"{path} -> {target.name}" + (f" ({'; '.join(notes)})" if notes else "")


def rewrite(font, inspection, renamed, restyled):
    """Apply the fix to a loaded, not yet decoded font, before it is saved."""
    if renamed:
        expected = fixed_names(inspection.face)
        for record in font["name"].names:
            if record.nameID in expected:
                record.string = expected[record.nameID]
    if restyled:
        restyle(font, inspection.style)


def fix_sfnt(path, inspection, run):
    face = inspection.face
    target, in_place, renamed, restyled = plan_fix(path, inspection)
    if run.dry_run:
        print(f"would fix    {report(path, target, inspection)}", flush=True)
        run.remember_ttf(target, face, planned=True)
        return
    expected = fixed_names(face)
    tmp = None
    try:
        with open_font(path, None) as font:
            rewrite(font, inspection, renamed, restyled)
            tmp = write_temp(target, font.save)
        with open_font(path, None) as original, open_font(tmp, None) as written:
            check_tables(original, written, "new TTF vs old", style=inspection.style, renamed=renamed)
            check_names(original, written, expected)
            check_face(written, face, inspection.style)
        install(tmp, path, target, in_place)
        tmp = None
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    run.remember_ttf(target, face)
    print(f"fixed        {report(path, target, inspection)}", flush=True)


def find_counterpart(path, face, run):
    """The fixed TTF to regenerate this WOFF2 from, or None."""
    name = face.file_stem + ".ttf"
    found = set(run.fixed_ttfs.get(face.file_stem, ()))
    for directory in [*run.ttf_dirs, path.parent]:
        candidate = directory / name
        if candidate.is_file():
            found.add(_canonical(candidate))
    if len(found) > 1:
        raise Refusal("ambiguous TTF counterparts: " + ", ".join(sorted(map(str, found))))
    if not found:
        return None
    (ttf,) = found
    # A dry run cannot read a TTF it only plans to fix; every other counterpart
    # is read, so the dry run refuses what the real run would refuse here.
    if ttf not in run.planned_ttfs:
        with open_font(ttf, None) as font:
            inspection = inspect_font(font)
        if inspection.kind != "fixed" or inspection.face != face:
            why = ": its style bits are not fixed; give it to this run too" if inspection.kind == "misstyled" else ""
            raise Refusal(f"TTF counterpart {ttf} is not the fixed form of this face{why}")
    return ttf


def fix_woff2(path, inspection, run):
    face = inspection.face
    target, in_place, renamed, restyled = plan_fix(path, inspection)
    ttf = find_counterpart(path, face, run)
    if ttf:
        how = f"regenerated from {ttf}"
    else:
        how = " and ".join(w for w, done in (("names", renamed), ("style bits", restyled)) if done) + " rewritten"
    if run.dry_run:
        print(f"would fix    {report(path, target, inspection, [how])}", flush=True)
        return
    expected = fixed_names(face)
    tmp = None
    try:
        with open_font(path, "woff2") as old:
            old_flavor = old.flavorData  # read in full when the file is opened
        if ttf:
            with open_font(ttf, None) as font:
                tmp = write_temp(target, woff2_saver(font, old_flavor))
        else:
            with open_font(path, "woff2") as font:
                rewrite(font, inspection, renamed, restyled)
                tmp = write_temp(target, woff2_saver(font, old_flavor))
        with open_font(path, "woff2") as original, open_font(tmp, "woff2") as written:
            if _flavor_tuple(written.flavorData) != _flavor_tuple(original.flavorData):
                raise Refusal("verification failed: the WOFF2 header data changed")
            # A regenerated WOFF2 takes its 'name' table from the TTF, which may
            # lay out the same records differently: check_names compares them.
            check_tables(
                original, written, "new WOFF2 vs old", woff2=True, style=inspection.style, renamed=renamed or bool(ttf)
            )
            check_names(original, written, expected)
            check_face(written, face, inspection.style)
            if ttf:
                with open_font(ttf, None) as source:
                    check_tables(source, written, "new WOFF2 vs its TTF", woff2_vs_sfnt=True)
                    if source.reader["name"] != written.reader["name"]:
                        raise Refusal("verification failed: new WOFF2 vs its TTF: 'name' differs")
        install(tmp, path, target, in_place)
        tmp = None
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    print(f"fixed        {report(path, target, inspection, [how])}", flush=True)


def process(path, run):
    if path.is_symlink():
        raise Refusal("is a symbolic link")
    if not path.is_file():
        raise Refusal("is not a regular file" if path.exists() else "no such file")
    flavor = EXTENSIONS.get(path.suffix.lower(), False)
    if flavor is False:
        raise Refusal(f"unsupported extension {path.suffix!r} (expected .ttf or .woff2)")
    with open_font(path, flavor) as font:
        inspection = inspect_font(font)
    if inspection.kind == "unrelated":
        print(f"skipped      {path}: {inspection.reason}", flush=True)
    elif inspection.kind == "suspect":
        raise Refusal(inspection.reason)
    elif inspection.kind == "fixed":
        if flavor is None:
            run.remember_ttf(path, inspection.face)
        note = "" if path.stem == inspection.face.file_stem else f" (file name differs from {inspection.face.file_stem})"
        print(f"already fixed {path}{note}", flush=True)
    elif flavor is None:  # "mangled" or "misstyled"
        fix_sfnt(path, inspection, run)
    else:
        fix_woff2(path, inspection, run)


def matches(argument):
    """The paths one FONT argument names: itself, or what it matches as a pattern.

    A pattern is expanded only when the argument names no existing path (not
    even a dangling symbolic link), so a file whose name holds a wildcard
    character is taken literally. Each match is then judged on its own, as if
    a POSIX shell had expanded the pattern.
    """
    if os.path.lexists(argument) or not GLOB_MAGIC.search(str(argument)):
        return [argument]
    paths = sorted(Path(match) for match in glob.glob(str(argument)))
    if not paths:
        raise Refusal("no such file, and no file matches it as a pattern")
    return paths


def font_files(path):
    """A directory's .ttf and .woff2 entries (not those of its subdirectories).

    A symbolic link to a directory is not followed but handed on, and refused,
    like any other link. Anything else is handed on as it is, for process() to
    accept or refuse.
    """
    if not path.is_dir() or path.is_symlink():
        return [path]
    fonts = sorted(p for p in path.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not fonts:
        raise Refusal("is a directory with no .ttf or .woff2 file in it")
    return fonts


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "fonts",
        nargs="+",
        type=Path,
        metavar="FONT",
        help=".ttf or .woff2 files, directories of them, or wildcard patterns",
    )
    parser.add_argument("--dry-run", action="store_true", help="report what would change; write nothing")
    parser.add_argument(
        "--ttf-dir",
        action="append",
        default=[],
        type=Path,
        metavar="DIR",
        help="where to look for the fixed .ttf a .woff2 is regenerated from (repeatable)",
    )
    args = parser.parse_args(argv)
    for directory in args.ttf_dir:
        if not directory.is_dir():
            parser.error(f"--ttf-dir {directory}: not a directory")

    run = Run(args.dry_run, args.ttf_dir)
    paths = []
    for argument in args.fonts:
        try:
            named = matches(argument)
        except Refusal as exc:
            run.errors += 1
            print(f"error        {argument}: {exc}", file=sys.stderr)
            continue
        for path in named:
            try:
                paths.extend(font_files(path))
            except (Refusal, OSError) as exc:
                run.errors += 1
                print(f"error        {path}: {exc}", file=sys.stderr)

    # TTFs first, so a WOFF2 given in the same run finds its fixed TTF.
    seen, ordered = set(), []
    for path in sorted(paths, key=lambda p: p.suffix.lower() != ".ttf"):
        key = _canonical(path) if path.exists() else path
        if key not in seen:
            seen.add(key)
            ordered.append(path)

    for path in ordered:
        try:
            process(path, run)
        except ImportError as exc:
            run.errors += 1
            print(f"error        {path}: {exc}  ->  pip install brotli", file=sys.stderr)
        except Incomplete as exc:
            run.errors += 1
            print(f"error        {path}: {exc}", file=sys.stderr)
        except Refusal as exc:
            run.errors += 1
            print(f"error        {path}: {exc} -- left untouched", file=sys.stderr)
        except Exception as exc:  # a malformed font must not stop the others
            run.errors += 1
            print(f"error        {path}: {type(exc).__name__}: {exc} -- left untouched", file=sys.stderr)
    if run.errors:
        print(f"\n{run.errors} file(s) refused or failed; see the errors above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
