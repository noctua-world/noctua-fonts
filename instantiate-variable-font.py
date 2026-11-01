#!/usr/bin/env python3
"""Generate static font instances from a variable font.

A variable font stores a design space (weight, width, optical size...) in one
file. Some targets cannot use that design space and need one file per style:
the Nerd Fonts patcher rejects variable fonts outright, Flutter wants a file
per declared weight, and older print/PDF pipelines only read static faces.

With no axis options, this generates every *named instance* the font itself
declares -- the styles the designer intended. Pass axis options to generate a
specific set instead; every axis you do not name stays at its default.
--weights and --widths take one or more values and may be repeated (the
values add up); one file is written per combination of the values given.

    ./instantiate-variable-font.py FONT.ttf --list
    ./instantiate-variable-font.py FONT.ttf
    ./instantiate-variable-font.py FONT.ttf --weights 400 700 --woff2
    ./instantiate-variable-font.py FONT.ttf --weights 400 --widths 62.5 100
    ./instantiate-variable-font.py FONT.ttf --axis opsz=14 --weights 400

Output goes to a static/ directory next to the input unless --out names
another. Each instance is written in the input's own format, chosen from its
contents rather than its file name: .ttf (TrueType outlines), .otf (CFF),
.woff or .woff2. --woff2 adds a .woff2 copy; for an input that is already
WOFF2 it adds nothing, and each instance is written once.

How an instance is named, inside the file and on disk (first match wins):
  1. STAT     the font's STAT axis values name the location (fontTools'
              renamer). Used only when every axis the location moves away from
              its default has STAT axis values, so no axis is silently dropped
              from the name.
  2. fvar     the location is exactly one of the font's named instances: its
              own style name and PostScript name are used. Name IDs 16/17 hold
              the typographic family and style; IDs 1/2 follow the R/I/B/BI
              convention (the legacy family carries the part of the style that
              is not Regular, Bold or Italic); ID 4 is the full name; ID 6 is
              the instance's PostScript name, or one derived from ID 25 (or
              the family) and the style; ID 3 is updated to match. A
              platform whose name records cannot spell the instance's names
              (Mac Roman records, for a style name with a letter Mac Roman
              lacks) has its style records removed rather than left naming
              the default.
  3. coords   neither applies: the file name spells the coordinates out, and
              the names inside the file still describe the default style. A
              note at the end says how many instances this happened to.
The file name is the PostScript name the instance ends up with (in case 3,
the family name and the coordinates), reduced to characters that are safe in
a file name. The bold/italic/regular bits of OS/2 fsSelection and
head.macStyle are set to agree with the legacy style name (ID 2); OS/2
usWeightClass and usWidthClass follow the wght and wdth coordinates
(fontTools sets them). A STAT table stays in the output, reduced to the
pinned location; fvar and the variation tables are removed.

Refused before anything is written (exit status 1):
  - an axis the font does not have, or a value outside the axis range
    (fontTools would clamp it silently), or one that is not finite. The
    range is compared at the precision fvar stores it in (16.16 fixed
    point), so the ends --list prints are always accepted;
  - the same axis given twice (an --axis tag repeated, or one that
    --weights or --widths already sets);
  - two targets that would write the same file (compared ignoring case,
    because macOS and Windows usually fold case);
  - a target that would overwrite the input;
  - an output path that exists and is not a regular file (a directory);
  - names the name table cannot encode (each planned table is compiled);
  - --woff2 (or a WOFF2 input) when brotli is not installed;
  - a malformed font: one whose tables run past the end of the file, or
    whose name, fvar, STAT, OS/2 or head table cannot be parsed.
A file already at an output path (from an earlier run, say) is replaced, and
the report marks it "(replaced)"; the input never is. Instancing itself runs
target by target while the files are written, so a font whose outlines or
variation data are malformed can still fail part-way: the error then says
how many files were complete before it.

Requires: fonttools (plus brotli for WOFF2), installed in a virtual
environment: see README.md, Tools.

Safety notes
------------
Every font is untrusted input, and these are the decisions that follow:

- The input is read into memory once. Planning and instancing both work from
  those bytes, so a file that changes during the run cannot make the plan and
  the output disagree.
- Output file names are built from strings inside the font (its PostScript or
  family name). Characters outside [A-Za-z0-9._+-] become "_" (so no path
  separator survives), leading dots, hyphens and underscores are dropped, and
  so are trailing dots: a name cannot climb out of the output directory, hide
  itself, read as a command-line option, or be one Windows cannot open. A
  name that is then empty, a Windows device name (CON, NUL, COM1...) or
  longer than MAX_STEM characters is refused, not repaired.
- Strings from the font that are printed (family and style names, axis tags,
  in --list, the report and error messages) have control characters escaped,
  so a crafted font cannot drive the terminal. Standard output and standard
  error are set to escape what their encoding cannot represent (a Japanese
  style name, with output redirected on Windows, where the file gets the
  cp1252 code page), so a listing is never cut short by an encoding error.
- Nothing is written, and the output directory is not created, until every
  target has been planned and checked (ranges, collisions, the input, output
  paths that are not regular files, brotli). The names of each target are
  decided on a throwaway copy of the font and that copy's name table is
  compiled, so a name that cannot be encoded is refused here and not found
  half-way through the writes.
- Each file is written to a temporary file in the output directory, created
  exclusively (it fails rather than follow a planted file or symlink),
  flushed and fsynced, then moved over the final name with os.replace. An
  interrupted run leaves the previous file or none, never a truncated font.
  The temporary file is removed if anything goes wrong after it was created;
  a file already at the temporary name is someone else's and is left alone.
- Parsing is fontTools'. Before planning, every table is checked to lie
  inside the file and the tables planning reads (name, fvar, STAT, OS/2,
  head) are parsed, so most malformed fonts are refused up front. Any error
  fontTools raises while reading, planning or writing is reported as
  "error: ..." (exit status 1), never as a traceback. Parsing is not
  hardened against resource exhaustion (a WOFF2 that inflates to an
  enormous font, say): run this on fonts you would install anyway.
- Name IDs 21/22 (WWS family/style), when a font has them, are left as the
  source had them.
"""

import argparse
import io
import itertools
import math
import os
import re
import secrets
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib import woff2 as woff2_support
    from fontTools.ttLib.tables._n_a_m_e import NameRecord
    from fontTools.varLib import instancer
    from fontTools.varLib.instancer import names as instancer_names
except ImportError:
    sys.exit("error: fonttools not found.  "
             "->  install fonttools and brotli in a virtual environment (README.md, Tools)")


# --help shows the docstring up to the safety notes; those are for maintainers.
HELP_TEXT = (__doc__ or "").split("\nSafety notes\n", 1)[0]

# name table IDs (OpenType 'name' table)
FAMILY = 1
SUBFAMILY = 2
UNIQUE_ID = 3
FULL_NAME = 4
VERSION = 5
POSTSCRIPT = 6
TYPO_FAMILY = 16
TYPO_SUBFAMILY = 17
PS_PREFIX = 25
# The records an instance's naming replaces, whichever way it is named.
STYLE_NAME_IDS = frozenset(
    {FAMILY, SUBFAMILY, UNIQUE_ID, FULL_NAME, POSTSCRIPT, TYPO_FAMILY, TYPO_SUBFAMILY})
WINDOWS_ENGLISH = (3, 1, 0x409)
NO_NAME_ID = 0xFFFF  # fvar instance without a postscriptNameID

RIBBI_WORDS = ("Regular", "Bold", "Italic")
POSTSCRIPT_MAX = 63  # OpenType: name ID 6 is at most 63 characters
POSTSCRIPT_FORBIDDEN = set("[](){}<>/%")
MAX_STEM = 150  # leaves room for the suffix and the temporary-file affixes
WINDOWS_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)})

# fsSelection / macStyle bits
FS_ITALIC, FS_BOLD, FS_REGULAR = 1 << 0, 1 << 5, 1 << 6
MAC_BOLD, MAC_ITALIC = 1 << 0, 1 << 1

# The tables planning reads; they are parsed up front so that a malformed one
# is refused before anything is written.
PLANNING_TABLES = ("name", "fvar", "STAT", "OS/2", "head")


class ToolError(Exception):
    """A refusal or failure reported to the user as 'error: ...' (exit 1)."""


def printable(text):
    """`text` with control and other non-printable characters escaped."""
    return "".join(ch if ch.isprintable() else ch.encode("unicode_escape").decode("ascii")
                   for ch in str(text))


def error_text(exc):
    """A printable description of `exc` (some fontTools errors have no text)."""
    return printable(exc) or type(exc).__name__


def fixed(value):
    """`value` in fvar's 16.16 fixed point, in units of 1/65536."""
    return round(value * 65536)


def same_coordinate(a, b):
    """Equal at the precision fvar stores coordinates in (16.16 fixed point)."""
    return fixed(a) == fixed(b)


def fixed_text(value):
    """The shortest decimal fvar stores as the same number as `value`.

    fvar keeps 0.1 as 6554/65536 = 0.100006103515625, which ':g' prints as
    '0.100006'; this prints '0.1', a value the range check accepts as that
    same end of the axis. Whole numbers print without a decimal point.
    """
    if not (math.isfinite(value) and abs(value) < 1e9):  # far beyond any 16.16 value
        return number_text(value)
    for places in range(18):
        text = f"{value:.{places}f}"
        if same_coordinate(float(text), value):
            break
    else:
        text = repr(float(value))
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def number_text(value):
    """`value` with every digit Python needs to read it back: 950.0 -> '950',
    99.9999999 -> '99.9999999' (never rounded onto an end of the axis)."""
    text = repr(float(value))
    return text[:-2] if text.endswith(".0") else text


def format_location(location):
    return "  ".join(f"{printable(tag)}={fixed_text(value)}" for tag, value in location.items())


# ---------------------------------------------------------------- the input

def check_table_extents(font, size):
    """None, or what is wrong when a table of `font` (an sfnt of `size`
    bytes) runs past the end of the file. fontTools checks this with an
    assert, which python -O removes, and which says nothing when it fails."""
    for tag, entry in font.reader.tables.items():
        if entry.offset + entry.length > size:
            return (f"its '{printable(tag)}' table runs past the end of the file "
                    f"(the file is truncated or damaged)")
    return None


class Source:
    """The input font, read once and kept in memory as uncompressed sfnt bytes.

    WOFF/WOFF2 input is decompressed once here; `flavor` remembers what it was,
    so the primary output can be written in the same format.
    """

    def __init__(self, path):
        self.path = path
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ToolError(f"cannot read {path}: {exc.strerror or exc}") from None
        where = f"cannot read '{printable(path.name)}' as a font"
        try:
            font = TTFont(io.BytesIO(data), lazy=True)
            self.flavor = font.flavor
            self.flavor_data = font.flavorData
            self.is_cff = "CFF " in font or "CFF2" in font
            if self.flavor is None:
                self.sfnt = data
            else:
                font.flavor = None
                font.flavorData = None
                buffer = io.BytesIO()
                font.save(buffer)
                self.sfnt = buffer.getvalue()
            font = self.open(lazy=False)  # not lazy: subtables are parsed too
            truncated = check_table_extents(font, len(self.sfnt))
            if truncated:
                raise ToolError(f"{where}: {truncated}")
            if "name" not in font:
                raise ToolError(f"{where}: it has no name table")
            for tag in PLANNING_TABLES:
                if tag in font:
                    font[tag]  # parse it now: a malformed table is refused up front
        except ToolError:
            raise
        except ImportError:
            raise ToolError("brotli not found (needed to read WOFF2).  "
                            "->  install brotli in a virtual environment (README.md, Tools)") from None
        except Exception as exc:  # fontTools raises many types on malformed input
            raise ToolError(f"{where}: {error_text(exc)}") from None

    def open(self, lazy=None):
        """A fresh TTFont over the sfnt bytes (a new object every call)."""
        return TTFont(io.BytesIO(self.sfnt), lazy=lazy)

    @property
    def suffix(self):
        """The primary output's suffix, from the contents, not the input's name."""
        if self.flavor == "woff2":
            return ".woff2"
        if self.flavor == "woff":
            return ".woff"
        return ".otf" if self.is_cff else ".ttf"


def axis_table(font):
    """{tag: (min, default, max)} for every variation axis."""
    return {a.axisTag: (a.minValue, a.defaultValue, a.maxValue)
            for a in font["fvar"].axes}


def named_instances(font):
    """[(style name, {tag: value}, instance)] as declared by the font itself."""
    names = font["name"]
    out = []
    for inst in font["fvar"].instances:
        label = names.getDebugName(inst.subfamilyNameID) or "?"
        out.append((label, dict(inst.coordinates), inst))
    return out


def check_location(axes, location, what=None):
    """Refuse a coordinate that is not finite or lies outside its axis.

    The range is compared at the precision fvar stores it in (16.16 fixed
    point): an axis declared as 0.1 .. 0.9 holds 6554/65536 .. 58982/65536,
    and 0.1 must be accepted as its minimum. A value accepted that way may
    lie a hair (under half of 1/65536) outside the stored end as a float;
    fontTools' instancer and STAT renamer both clamp it onto that end, which
    is the same value at fvar's precision, so no instance moves.
    """
    prefix = f"{what}: " if what else ""
    for raw_tag, value in location.items():
        lo, default, hi = axes[raw_tag]
        tag = printable(raw_tag)  # axis tags come from the font, too
        if not math.isfinite(value):
            raise ToolError(f"{prefix}{tag}={value} is not a finite number")
        # the first test keeps fixed() away from values whose 16.16 form overflows
        if not (lo - 1 <= value <= hi + 1 and fixed(lo) <= fixed(value) <= fixed(hi)):
            raise ToolError(
                f"{prefix}{tag}={number_text(value)} is outside the font's {tag} axis "
                f"range {fixed_text(lo)} .. {fixed_text(hi)} (default {fixed_text(default)})")


# ---------------------------------------------------------------- naming

def split_style(style):
    """(bold, italic, rest) of a style name, by its English RIBBI words.

    'SemiCondensed Bold Italic' -> (True, True, ['SemiCondensed']).
    """
    words = style.split()
    rest = [w for w in words if w not in RIBBI_WORDS]
    return "Bold" in words, "Italic" in words, rest


def ribbi_style(bold, italic):
    return {(False, False): "Regular", (True, False): "Bold",
            (False, True): "Italic", (True, True): "Bold Italic"}[(bold, italic)]


def postscript_safe(text):
    """`text` reduced to the characters a PostScript name may contain."""
    kept = "".join(ch for ch in text
                   if 33 <= ord(ch) <= 126 and ch not in POSTSCRIPT_FORBIDDEN)
    return kept[:POSTSCRIPT_MAX]


def derive_postscript(prefix, style):
    """'<prefix>-<style>' with everything but [A-Za-z0-9-] removed, as the
    fontTools STAT renamer does; None when the prefix has nothing left."""
    head = re.sub(r"[^A-Za-z0-9-]", "", prefix)
    if not head.strip("-"):
        return None
    return re.sub(r"[^A-Za-z0-9-]", "", f"{head}-{style}")[:POSTSCRIPT_MAX]


def safe_stem(text):
    """A file-name stem built from font-controlled `text` (see Safety notes)."""
    stem = re.sub(r"[^A-Za-z0-9._+-]+", "_", text).lstrip("._-").rstrip(".")
    if not stem:
        raise ToolError(f"cannot build a file name from {printable(text)!r}")
    if stem.split(".")[0].upper() in WINDOWS_DEVICE_NAMES:
        raise ToolError(f"refusing the file name {stem!r}: it is a Windows device name")
    if len(stem) > MAX_STEM:
        raise ToolError(f"refusing a file name of {len(stem)} characters "
                        f"(the limit is {MAX_STEM}): {stem[:40]}...")
    return stem


def record_string(records, name_id):
    """The Windows-English string for `name_id` among `records`, else any."""
    candidates = [r for r in records if r.nameID == name_id]
    for r in candidates:
        if (r.platformID, r.platEncID, r.langID) == WINDOWS_ENGLISH:
            return r.toUnicode(errors="replace")
    return candidates[0].toUnicode(errors="replace") if candidates else None


def style_records(name_table):
    return [r for r in name_table.names if r.nameID in STYLE_NAME_IDS]


def stat_can_name(font, location):
    """True when the STAT table has axis values for every axis the location
    moves away from its default (an axis without values would be dropped
    from the name, and two widths would both be called 'Bold')."""
    if "STAT" not in font:
        return False
    stat = font["STAT"].table
    if not (stat.DesignAxisRecord and stat.AxisValueArray and stat.AxisValueArray.AxisValue):
        return False
    design = [a.AxisTag for a in stat.DesignAxisRecord.Axis]
    valued = set()
    for value in stat.AxisValueArray.AxisValue:
        if value.Format in (1, 2, 3):
            indices = [value.AxisIndex]
        elif value.Format == 4:
            indices = [rec.AxisIndex for rec in value.AxisValueRecord]
        else:
            continue
        valued.update(design[i] for i in indices if 0 <= i < len(design))
    return all(tag in valued or same_coordinate(location[tag], default)
               for tag, (_, default, _) in axis_table(font).items())


def matching_instance(font, location):
    """The first fvar named instance at exactly `location`, or None."""
    axes = axis_table(font)
    for inst in font["fvar"].instances:
        if all(same_coordinate(location[tag], inst.coordinates.get(tag, default))
               for tag, (_, default, _) in axes.items()):
            return inst
    return None


def font_version(font, triple):
    name = font["name"]
    record = name.getName(VERSION, *triple) or name.getName(VERSION, *WINDOWS_ENGLISH)
    if record is None:
        return f"{font['head'].fontRevision:.3f}"
    # "Version 2.003; ttfautohint (v1.8)" -> "2.003"
    return record.toUnicode(errors="replace").split(";")[0].removeprefix("Version ").strip()


def unique_id(current, old_ps, old_full, new_ps, new_full, version, vendor):
    """Name ID 3 for the instance: the old one with the old PostScript (or
    full) name swapped for the new one, else 'version;vendor;psname'."""
    if current:
        if old_ps and old_ps in current:
            return current.replace(old_ps, new_ps)
        if old_full and old_full in current:
            return current.replace(old_full, new_full)
    return f"{version};{vendor};{new_ps}"


def encodes(text, triple):
    """True when `text` can be stored in a name record of `triple`
    (platform, encoding, language): Mac Roman has no C with caron, for one."""
    record = NameRecord()
    record.platformID, record.platEncID, record.langID = triple
    record.nameID, record.string = FAMILY, text
    try:
        record.toBytes()
    except Exception:  # UnicodeEncodeError; LookupError for a codec Python lacks
        return False
    return True


def names_problem(font):
    """None when the name table of `font` compiles, else what stops it.

    Every record is encoded first: the table's own compile() logs a warning
    per record while sorting before it raises."""
    name = font["name"]
    try:
        for record in name.names:
            record.toBytes()
        name.compile(font)
    except Exception as exc:
        return error_text(exc)
    return None


def rename_from_instance(font, inst):
    """Rewrite the style records of `font` (a scratch copy) from fvar
    instance `inst`'s own names. Returns the PostScript name, or None when
    the instance cannot be named (no style or family name, nothing to build
    a PostScript name from, no legacy name records to rewrite), in which
    case the font is left untouched.

    A platform with no record of the instance's style name gets the English
    one. When that platform's encoding cannot hold the new names (a Mac Roman
    record for a style with a letter Mac Roman lacks), its style records are
    removed instead: kept, they would still name the default style, and two
    files would claim to be the same face there. The names are then read
    from the platforms that can spell them (Windows, which is Unicode)."""
    name = font["name"]
    style_en = (name.getDebugName(inst.subfamilyNameID) or "").strip()
    family_en = name.getDebugName(TYPO_FAMILY) or name.getDebugName(FAMILY)
    if not style_en or not family_en:
        return None
    ps = None
    if inst.postscriptNameID not in (None, NO_NAME_ID):
        ps = postscript_safe(name.getDebugName(inst.postscriptNameID) or "") or None
    if ps is None:
        ps = derive_postscript(name.getDebugName(PS_PREFIX) or family_en, style_en)
    if not ps:
        return None

    def triples_with(name_id):
        return {(r.platformID, r.platEncID, r.langID) for r in name.names if r.nameID == name_id}

    triples = sorted(triples_with(FAMILY) & triples_with(SUBFAMILY))
    if not triples:  # no legacy family/style records to rewrite
        return None
    vendor = getattr(font["OS/2"], "achVendID", "") if "OS/2" in font else ""
    vendor = re.sub(r"[^\x21-\x7e]", "", vendor)

    # Decide every platform's names first, change the table after: a font
    # that cannot be named at all must be left exactly as it was.
    planned = {}
    for triple in triples:
        def current(name_id):
            record = name.getName(name_id, *triple)
            return record.toUnicode(errors="replace") if record else None

        family = current(TYPO_FAMILY) or current(FAMILY)
        style = (current(inst.subfamilyNameID) or "").strip() or style_en
        bold, italic, rest = split_style(style)
        full = f"{family} {style}"
        uid = unique_id(current(UNIQUE_ID), current(POSTSCRIPT), current(FULL_NAME),
                        ps, full, font_version(font, triple), vendor)
        values = {FAMILY: " ".join([family, *rest]), SUBFAMILY: ribbi_style(bold, italic),
                  UNIQUE_ID: uid, FULL_NAME: full, POSTSCRIPT: ps}
        if rest:  # only a style beyond R/I/B/BI needs typographic names (16/17)
            values[TYPO_FAMILY] = family
            values[TYPO_SUBFAMILY] = style
        if all(encodes(string, triple) for string in values.values()):
            planned[triple] = values
        else:
            planned[triple] = None  # this platform cannot spell them: drop its records
    if not any(planned.values()):
        return None

    for triple, values in planned.items():
        kept = values or {}
        for name_id in STYLE_NAME_IDS - set(kept):
            name.removeNames(nameID=name_id, platformID=triple[0],
                             platEncID=triple[1], langID=triple[2])
        for name_id, string in kept.items():
            name.setName(string, name_id, *triple)
    return ps


def coordinate_stem(font, requested):
    family = (font["name"].getDebugName(FAMILY) or "Font").replace(" ", "")
    coords = "-".join(f"{t}{v:g}" for t, v in sorted(requested.items()))
    return f"{family}-{coords}"


@dataclass
class Target:
    """One static instance to generate, and (once planned) how it is named."""
    location: dict                 # every axis, pinned
    requested: dict                # what was asked for (names the coords fallback)
    label: str = None              # the named instance's style name, if any
    instance: object = None        # the fvar NamedInstance, if generating one
    method: str = None             # "stat", "fvar" or "coords"
    records: list = None           # replacement style name records (None: keep)
    stem: str = None
    outputs: list = field(default_factory=list)  # [(Path, flavor)]

    def describe(self):
        where = format_location(self.location)
        if self.label is not None:
            return f"named instance '{printable(self.label)}' ({where})"
        return where


def plan_names(source, target):
    """(method, records, stem text) for `target`, computed on scratch copies
    of the font so that the plan exists before anything is instantiated.

    Each scratch name table is compiled here, so a name that cannot be
    encoded is refused (ToolError) while nothing has been written yet."""
    font = source.open(lazy=True)
    if stat_can_name(font, target.location):
        try:
            instancer_names.updateNameTable(font, dict(target.location))
        except Exception:
            pass  # STAT cannot name it after all (or is malformed): next rule
        else:
            records = style_records(font["name"])
            ps = record_string(records, POSTSCRIPT)
            if ps and names_problem(font) is None:
                return "stat", records, ps
        font = source.open(lazy=True)  # the renamer may have half-written names

    inst = target.instance
    if inst is None:
        inst = matching_instance(font, target.location)
    method, records = "coords", None
    if inst is not None:
        ps = rename_from_instance(font, inst)
        if ps:
            method, records, raw = "fvar", style_records(font["name"]), ps
    if method == "coords":
        raw = coordinate_stem(font, target.requested)
    problem = names_problem(font)
    if problem:
        raise ToolError(f"its name table cannot be written: {problem}")
    return method, records, raw


# ---------------------------------------------------------------- planning

def writes_over(path, protected):
    """True when writing `path` could replace the file `protected` (resolved):
    the same resolved path, the same name ignoring case in the same
    directory, or the same file on disk (hard or symbolic link)."""
    resolved = path.resolve()
    if resolved == protected:
        return True
    if (resolved.parent == protected.parent
            and resolved.name.casefold() == protected.name.casefold()):
        return True
    try:
        return os.path.samefile(path, protected)
    except OSError:  # does not exist (yet)
        return False


def plan(source, targets, out_dir, want_woff2):
    """Name every target and fix its output paths; refuse collisions,
    overwriting the input, and output paths that are not regular files.
    Writes nothing."""
    if out_dir.exists() and not out_dir.is_dir():
        raise ToolError(f"--out {out_dir} exists and is not a directory")
    formats = [(source.suffix, source.flavor)]
    if want_woff2 and source.flavor != "woff2":
        formats.append((".woff2", "woff2"))
    if any(flavor == "woff2" for _, flavor in formats) and not woff2_support.haveBrotli:
        raise ToolError("brotli not found (needed for WOFF2).  "
                        "->  install brotli in a virtual environment (README.md, Tools)")

    for target in targets:
        try:
            target.method, target.records, raw = plan_names(source, target)
            target.stem = safe_stem(raw)
        except ToolError as exc:
            raise ToolError(f"{target.describe()}: {exc}") from None
        target.outputs = [(out_dir / f"{target.stem}{suffix}", flavor)
                          for suffix, flavor in formats]

    protected = source.path.resolve()
    claimed = {}
    for target in targets:
        for path, _ in target.outputs:
            key = path.name.casefold()
            if key in claimed:
                raise ToolError(
                    f"two targets would write the same file '{path.name}':\n"
                    f"         {claimed[key].describe()}\n"
                    f"     and {target.describe()}")
            claimed[key] = target
            if writes_over(path, protected):
                raise ToolError(f"{target.describe()} would overwrite the input "
                                f"'{printable(source.path.name)}'; pass a different --out")
            # os.replace cannot put a file where a directory is, and should not
            # replace a device or a pipe: found here, not after other writes
            if path.exists() and not path.is_file():
                raise ToolError(f"{target.describe()}: '{path.name}' already exists in "
                                f"{out_dir} and is not a regular file")


# ---------------------------------------------------------------- writing

def apply_records(font, records):
    """Replace the style name records of `font` with `records`."""
    name = font["name"]
    name.names = [r for r in name.names if r.nameID not in STYLE_NAME_IDS] + list(records)


def fix_style_bits(font):
    """Make fsSelection and macStyle agree with the legacy style name (ID 2).

    fontTools' STAT renamer sets these too, but leaves macStyle alone for a
    Regular instance and does nothing when there is no Windows-English ID 2;
    the other two naming paths do not touch them at all.
    """
    name = font["name"]
    record = name.getName(SUBFAMILY, *WINDOWS_ENGLISH)
    style = record.toUnicode(errors="replace") if record else (name.getDebugName(SUBFAMILY) or "")
    bold, italic, _ = split_style(style)
    if "OS/2" in font:
        os2 = font["OS/2"]
        selection = os2.fsSelection & ~(FS_ITALIC | FS_BOLD | FS_REGULAR)
        if italic:
            selection |= FS_ITALIC
        if bold:
            selection |= FS_BOLD
        if not (bold or italic):
            selection |= FS_REGULAR
        os2.fsSelection = selection
    if "head" in font:
        head = font["head"]
        head.macStyle = ((head.macStyle & ~(MAC_BOLD | MAC_ITALIC))
                         | (MAC_BOLD if bold else 0) | (MAC_ITALIC if italic else 0))


def write_atomically(font, path):
    """Save `font` to `path` through an exclusive temporary file + os.replace."""
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    # Outside the try: when the name is taken, the file there is not ours to
    # remove ("x" refuses it, and refuses to follow a symlink planted there).
    handle = open(temporary, "xb")
    try:
        with handle:
            font.save(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def write_target(source, target, completed):
    """Instantiate `target` and write its outputs, appending (path, replaced)
    to `completed` as each one is in place, so a failure part-way through a
    target still counts the files it did write."""
    font = source.open()
    instancer.instantiateVariableFont(font, dict(target.location), inplace=True)
    if target.records is not None:
        apply_records(font, target.records)
    fix_style_bits(font)
    for path, flavor in target.outputs:
        replaced = path.exists()
        font.flavor = flavor
        font.flavorData = source.flavor_data if flavor == source.flavor else None
        write_atomically(font, path)
        completed.append((path, replaced))


# ---------------------------------------------------------------- CLI

def describe(source, font):
    """The --list report: axes, STAT state, named instances and their files."""
    axes = axis_table(font)
    print(f"{printable(source.path.name)}")
    print(f"  family: {printable(font['name'].getDebugName(FAMILY))}")
    print("  axes:")
    for tag, (lo, default, hi) in axes.items():
        print(f"    {printable(tag)}  {fixed_text(lo)} .. {fixed_text(hi)}   "
              f"(default {fixed_text(default)})")
    if "STAT" not in font:
        print("  STAT: none")
    else:
        stat = font["STAT"].table
        count = len(stat.AxisValueArray.AxisValue) if stat.AxisValueArray else 0
        print(f"  STAT: {count} axis value(s)"
              + ("" if count else " -- cannot name instances"))
    print("  named instances:")
    seen = {}
    for label, coords, inst in named_instances(font):
        location = {tag: default for tag, (_, default, _) in axes.items()}
        location.update(coords)
        target = Target(location=location, requested=dict(coords), label=label, instance=inst)
        try:
            check_location(axes, coords, target.describe())
            method, _, raw = plan_names(source, target)
            file_name = safe_stem(raw) + source.suffix
            result = f"-> {file_name}  ({method})"
            seen.setdefault(file_name.casefold(), []).append(label)
        except ToolError as exc:
            result = f"-> refused: {exc}"
        print(f"    {printable(label):<26} {format_location(coords):<24} {result}")
    clashes = sum(len(labels) for labels in seen.values() if len(labels) > 1)
    if clashes:
        print(f"\nnote: {clashes} named instances share a file name; generating "
              "them all would be refused.")


def parse_axis(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"expected TAG=VALUE, got {spec!r}")
    tag, _, value = spec.partition("=")
    try:
        return tag.strip(), float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}") from None


def build_parser():
    p = argparse.ArgumentParser(
        description=HELP_TEXT, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("font", type=Path,
                   help="variable font to instantiate (.ttf/.otf/.woff/.woff2)")
    p.add_argument("--list", action="store_true",
                   help="show axes, named instances and the file each would be "
                        "written to; generate nothing")
    # "extend": a repeated --weights adds its values instead of replacing them
    p.add_argument("--weights", nargs="+", action="extend", type=float, metavar="N",
                   help="wght values to generate (e.g. 400 700); repeatable, "
                        "the values add up")
    p.add_argument("--widths", nargs="+", action="extend", type=float, metavar="N",
                   help="wdth values to generate (e.g. 62.5 100); repeatable, "
                        "the values add up")
    p.add_argument("--axis", action="append", type=parse_axis, default=[],
                   metavar="TAG=VALUE",
                   help="pin an axis by its tag; repeatable, once per axis "
                        "(e.g. --axis opsz=14)")
    p.add_argument("--woff2", action="store_true",
                   help="also write .woff2 (web); nothing extra for a WOFF2 input")
    p.add_argument("--out", type=Path, metavar="DIR",
                   help="output directory (default: static/ next to the input)")
    return p


def build_targets(args, font, axes):
    extra = {}
    for tag, value in args.axis:
        if tag in extra:
            raise ToolError(f"--axis {tag} is given more than once")
        extra[tag] = value
    for option, tag, values in (("--weights", "wght", args.weights),
                                ("--widths", "wdth", args.widths)):
        if values and tag in extra:
            raise ToolError(f"{tag} is given by both {option} and --axis; use one")

    requested_tags = set(extra)
    if args.weights:
        requested_tags.add("wght")
    if args.widths:
        requested_tags.add("wdth")
    unknown = sorted(requested_tags - set(axes))
    if unknown:
        raise ToolError(f"font has no axis {', '.join(map(printable, unknown))} "
                        f"(it has: {', '.join(map(printable, axes))})")

    defaults = {tag: default for tag, (_, default, _) in axes.items()}
    if not (args.weights or args.widths or extra):
        # no axis options -> the instances the font itself declares
        targets = [Target(location={**defaults, **coords}, requested=dict(coords),
                          label=label, instance=inst)
                   for label, coords, inst in named_instances(font)]
        if not targets:
            raise ToolError("the font declares no named instances; "
                            "pass --weights, --widths or --axis")
    else:
        grid = {}
        if args.weights:
            grid["wght"] = args.weights
        if args.widths:
            grid["wdth"] = args.widths
        tags = list(grid)
        combos = itertools.product(*(grid[t] for t in tags)) if tags else [()]
        targets = []
        for values in combos:
            requested = {**extra, **dict(zip(tags, values))}
            targets.append(Target(location={**defaults, **requested}, requested=requested))

    for target in targets:
        # the requested values for an axis grid; every coordinate for a named instance
        check_location(axes, target.requested,
                       target.describe() if target.label is not None else None)
    return targets


def run(args):
    if not args.font.is_file():
        raise ToolError(f"no such file: {args.font}")
    source = Source(args.font)
    font = source.open(lazy=True)
    if "fvar" not in font:
        raise ToolError(f"'{printable(args.font.name)}' is already STATIC (no fvar table) "
                        "-- nothing to instantiate.")

    if args.list:
        try:
            describe(source, font)
        except ToolError:
            raise
        except Exception as exc:  # fontTools, on a font malformed past the checks
            raise ToolError(f"cannot list '{printable(args.font.name)}': "
                            f"{error_text(exc)}") from None
        return 0

    out_dir = args.out or args.font.parent / "static"
    try:
        axes = axis_table(font)
        targets = build_targets(args, font, axes)
        plan(source, targets, out_dir, args.woff2)
    except ToolError as exc:
        raise ToolError(f"{exc}\n       nothing was written.") from None
    except Exception as exc:  # fontTools, on a font malformed past the checks
        raise ToolError(f"cannot plan the instances of '{printable(args.font.name)}': "
                        f"{error_text(exc)}\n       nothing was written.") from None

    # -- nothing has been written up to here --
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ToolError(f"cannot create the output directory {out_dir}: "
                        f"{exc.strerror or exc}\n       nothing was written.") from None
    print(f"from: {printable(args.font.name)}  ->  {out_dir}/")
    if args.woff2 and source.flavor == "woff2":
        print("  (the input is already WOFF2: --woff2 adds nothing, "
              "each instance is written once)")
    completed = []
    for target in targets:
        start = len(completed)
        try:
            write_target(source, target, completed)
        except Exception as exc:
            partial = [path.name for path, _ in completed[start:]]
            among = f", among them {', '.join(partial)}" if partial else ""
            raise ToolError(f"failed to write {target.describe()}: {error_text(exc)}\n"
                            f"       ({len(completed)} file(s) written before the failure "
                            f"are complete{among})") from None
        (first, first_replaced), *more = completed[start:]
        line = f"  {first.name:<44} {first.stat().st_size // 1024:>6} KB"
        replaced = first_replaced
        for path, was_there in more:
            line += f"  + {path.stat().st_size // 1024} KB {path.suffix.lstrip('.')}"
            replaced = replaced or was_there
        if replaced:
            line += "  (replaced)"
        print(line)

    from_fvar = sum(t.method == "fvar" for t in targets)
    unnamed = sum(t.method == "coords" for t in targets)
    if from_fvar:
        print(f"\nnote: {from_fvar} instance(s) were named from the font's own named "
              "instances (fvar),\n      because its STAT table cannot name them.")
    if unnamed:
        print(f"\nnote: {unnamed} instance(s) sit at a location that neither STAT nor a "
              "named instance\n      names. Their filenames spell out the coordinates, "
              "but the style name\n      inside the file still reads as the default.")
    return 0


def main(argv=None):
    # Names from the font may hold characters the console's encoding lacks
    # (cp1252 on a redirected Windows stdout): escape them, never crash on them.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="backslashreplace")
            except (ValueError, OSError):  # a stream that cannot be reconfigured
                pass
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
