"""Tests for fix-nerd-semiextended-names.py.

The fonts are synthetic (fontTools FontBuilder) and carry, character for
character, the names and style bits the Nerd Fonts patcher wrote on the real
SemiExtended faces; the expected names and bits are the ones its correctly
named siblings of the other widths carry. Only the last class reads the real
fonts, and it skips when they are absent.
"""

import importlib.util
import io
import logging
import os
import re
import shutil
import struct
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables.DefaultTable import DefaultTable

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "fix-nerd-semiextended-names.py"
REAL_TTF = REPO / "noctua-iosevka" / "TTF-nerdfonts"
REAL_WOFF2 = REPO / "noctua-iosevka" / "WOFF2-nerdfonts"

_spec = importlib.util.spec_from_file_location("fix_nerd_semiextended_names", SCRIPT)
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

try:
    import brotli  # noqa: F401

    HAVE_BROTLI = True
except ImportError:
    HAVE_BROTLI = False

FAMILY = "NoctuaIosevka Nerd Font Mono"

# Records that are not identifiers and must come through untouched.
OTHER_NAMES = {
    0: "Copyright 2015-2026, Renzhi Li (aka. Belleve Invis, belleve@typeof.net).",
    5: "Version 34.7.0;Nerd Fonts 3.4.0",
    256: "Andale Mono Style",
}

# (case, mangled names, usWeightClass, fsSelection and macStyle as the patcher
#  left them, expected names, expected file stem)
CASES = {
    "regular": (
        {
            1: "NoctuaIosevkaSemi Nerd Font Mono Extended",
            2: "Regular",
            3: "NoctuaIosevkaSemi Nerd Font Mono Extended 3.4.0",
            4: "NoctuaIosevkaSemi Nerd Font Mono Extended",
            6: "NoctuaIosevkaSemiNFM-Extended",
            16: "NoctuaIosevkaSemi Nerd Font Mono",
            17: "Extended",
        },
        400, 0x0180, 0x0000,
        {
            1: f"{FAMILY} SemiExtended",
            2: "Regular",
            3: f"{FAMILY} SemiExtended 3.4.0",
            4: f"{FAMILY} SemiExtended",
            6: "NoctuaIosevkaNFM-SemiExtended",
            16: FAMILY,
            17: "SemiExtended",
        },
        "NoctuaIosevkaNerdFontMono-SemiExtended",
    ),
    "bold": (
        {
            1: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended",
            2: "Regular",
            3: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended 3.4.0",
            4: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended",
            6: "NoctuaIosevkaBoldSemiNFM-Extended",
            16: "NoctuaIosevkaBoldSemi Nerd Font Mono",
            17: "Extended",
        },
        700, 0x0180, 0x0000,
        {
            1: f"{FAMILY} SemiExtended",
            2: "Bold",
            3: f"{FAMILY} SemiExtended Bold 3.4.0",
            4: f"{FAMILY} SemiExtended Bold",
            6: "NoctuaIosevkaNFM-SemiExtendedBold",
            16: FAMILY,
            17: "SemiExtended Bold",
        },
        "NoctuaIosevkaNerdFontMono-SemiExtendedBold",
    ),
    "extralight-italic": (
        {
            1: "NoctuaIosevkaExtralightSemi Nerd Font Mono Extended",
            2: "Italic",
            3: "NoctuaIosevkaExtralightSemi Nerd Font Mono Extended Italic 3.4.0",
            4: "NoctuaIosevkaExtralightSemi Nerd Font Mono Extended Italic",
            6: "NoctuaIosevkaExtralightSemiNFM-ExtendedItalic",
            16: "NoctuaIosevkaExtralightSemi Nerd Font Mono",
            17: "Extended Italic",
        },
        200, 0x0181, 0x0002,
        {
            1: f"{FAMILY} SemiExtended ExtraLight",
            2: "Italic",
            3: f"{FAMILY} SemiExtended ExtraLight Italic 3.4.0",
            4: f"{FAMILY} SemiExtended ExtraLight Italic",
            6: "NoctuaIosevkaNFM-SemiExtendedExtraLightItalic",
            16: FAMILY,
            17: "SemiExtended ExtraLight Italic",
        },
        "NoctuaIosevkaNerdFontMono-SemiExtendedExtraLightItalic",
    ),
    "bold-italic": (
        {
            1: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended",
            2: "Italic",
            3: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended Italic 3.4.0",
            4: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended Italic",
            6: "NoctuaIosevkaBoldSemiNFM-ExtendedItalic",
            16: "NoctuaIosevkaBoldSemi Nerd Font Mono",
            17: "Extended Italic",
        },
        700, 0x0181, 0x0002,
        {
            1: f"{FAMILY} SemiExtended",
            2: "Bold Italic",
            3: f"{FAMILY} SemiExtended Bold Italic 3.4.0",
            4: f"{FAMILY} SemiExtended Bold Italic",
            6: "NoctuaIosevkaNFM-SemiExtendedBoldItalic",
            16: FAMILY,
            17: "SemiExtended Bold Italic",
        },
        "NoctuaIosevkaNerdFontMono-SemiExtendedBoldItalic",
    ),
    "oblique": (
        {
            1: "NoctuaIosevkaSemi Nerd Font Mono Extended Obl",
            2: "Italic",
            3: "NoctuaIosevkaSemi Nerd Font Mono Extended Oblique 3.4.0",
            4: "NoctuaIosevkaSemi Nerd Font Mono Extended Oblique",
            6: "NoctuaIosevkaSemiNFM-ExtendedOblique",
            16: "NoctuaIosevkaSemi Nerd Font Mono",
            17: "Extended Oblique",
        },
        400, 0x0380, 0x0000,
        {
            1: f"{FAMILY} SemiExtended Obl",
            2: "Italic",
            3: f"{FAMILY} SemiExtended Oblique 3.4.0",
            4: f"{FAMILY} SemiExtended Oblique",
            6: "NoctuaIosevkaNFM-SemiExtendedOblique",
            16: FAMILY,
            17: "SemiExtended Oblique",
        },
        "NoctuaIosevkaNerdFontMono-SemiExtendedOblique",
    ),
    "bold-oblique": (
        {
            1: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended Obl",
            2: "Italic",
            3: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended Oblique 3.4.0",
            4: "NoctuaIosevkaBoldSemi Nerd Font Mono Extended Oblique",
            6: "NoctuaIosevkaBoldSemiNFM-ExtendedOblique",
            16: "NoctuaIosevkaBoldSemi Nerd Font Mono",
            17: "Extended Oblique",
        },
        700, 0x0380, 0x0000,
        {
            1: f"{FAMILY} SemiExtended Obl",
            2: "Bold Italic",
            3: f"{FAMILY} SemiExtended Bold Oblique 3.4.0",
            4: f"{FAMILY} SemiExtended Bold Oblique",
            6: "NoctuaIosevkaNFM-SemiExtendedObliqueBold",
            16: FAMILY,
            17: "SemiExtended Bold Oblique",
        },
        "NoctuaIosevkaNerdFontMono-SemiExtendedBoldOblique",
    ),
}

# (fsSelection, macStyle) of each case's correctly named siblings: the values
# the real faces of the same weight and slope carry in every other width
# (TestRealFonts checks the real SemiExtended faces against them).
SIBLING_STYLE = {
    "regular": (0x0180, 0x0000),
    "bold": (0x01A0, 0x0001),
    "extralight-italic": (0x0181, 0x0002),
    "bold-italic": (0x01A1, 0x0003),
    "oblique": (0x0380, 0x0000),
    "bold-oblique": (0x03A0, 0x0001),
}

# (the patcher's spelling inside the mangled family, the siblings' spelling,
#  usWeightClass): the nine weights of the build.
WEIGHT_SPELLINGS = (
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
SLOPES = ("", "Italic", "Oblique")


def mangled_names_for(patcher_weight, slope):
    """The names the patcher writes on the SemiExtended face of this weight
    and slope (CASES holds six of them as measured on the real faces)."""
    family = f"NoctuaIosevka{patcher_weight}Semi Nerd Font Mono"
    style = " ".join(w for w in ("Extended", slope) if w)
    return {
        1: f"{family} Extended" + (" Obl" if slope == "Oblique" else ""),
        2: "Italic" if slope else "Regular",
        3: f"{family} {style} 3.4.0",
        4: f"{family} {style}",
        6: f"NoctuaIosevka{patcher_weight}SemiNFM-{style.replace(' ', '')}",
        16: family,
        17: style,
    }


def slope_style(slope):
    """(fsSelection, macStyle) every sibling of this slope carries apart from
    the bold bits: USE_TYPO_METRICS and WWS, and the slope's own bits."""
    fs = 0x0180 | (0x0001 if slope == "Italic" else 0) | (0x0200 if slope == "Oblique" else 0)
    return fs, 0x0002 if slope == "Italic" else 0x0000


# Raw byte ranges: the two style fields and the whole-file checksum.
OS2_FS_SELECTION = slice(62, 64)
HEAD_MAC_STYLE = slice(44, 46)
HEAD_CHECKSUM = slice(8, 12)
OS2_FIRST_CHAR_INDEX = 64


TIMESTAMP = 3_000_000_000  # fixed head.created/modified: fonts built apart stay comparable


def build_font(names, weight, fs_selection, mac_style=0, width=6, rise=0, dent=0):
    """A minimal TrueType font with the given names on both platforms.

    rise moves a point of "A" that sets the bounding box (head, hhea and maxp
    data change with it); dent moves one down into it, so only glyf and loca
    change.
    """
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({0x41: "A"})
    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((100, 700 + rise))
    pen.lineTo((400, 700 - dent))
    pen.lineTo((500, 700))
    pen.lineTo((500, 0))
    pen.closePath()
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (600, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({**OTHER_NAMES, **names}, mac=True)
    fb.setupOS2(version=4, usWeightClass=weight, usWidthClass=width, fsSelection=fs_selection)
    fb.setupPost()
    fb.font["head"].macStyle = mac_style
    fb.font["head"].created = fb.font["head"].modified = TIMESTAMP
    return fb.font


def save_case(directory, case, file_name=None, **build):
    names, weight, fs, mac, _, _ = CASES[case]
    font = build_font(names, weight, fs, mac, **build)
    path = directory / (file_name or (names[6].replace("NFM", "NerdFontMono") + ".ttf"))
    font.save(path)
    return path


def save_fixed_names(directory, case, fs=None, mac=None, file_name=None):
    """The face of `case` with its names already fixed, under the fixed file
    name, and the style bits the patcher left (or fs/mac when given)."""
    _, weight, case_fs, case_mac, expected, stem = CASES[case]
    font = build_font(expected, weight, case_fs if fs is None else fs, case_mac if mac is None else mac)
    path = directory / (file_name or f"{stem}.ttf")
    font.save(path)
    return path


def patch_uint16(path, tag, offset, value):
    """Write one uint16 into the raw bytes of table `tag`, nothing else."""
    font = TTFont(io.BytesIO(path.read_bytes()), lazy=True, recalcBBoxes=False, recalcTimestamp=False)
    table = DefaultTable(tag)
    table.data = font.reader[tag][:offset] + struct.pack(">H", value) + font.reader[tag][offset + 2 :]
    font[tag] = table
    out = io.BytesIO()
    font.save(out)
    font.close()
    path.write_bytes(out.getvalue())


def style_of(path):
    """(fsSelection, macStyle), read through fontTools."""
    with TTFont(path, lazy=True) as font:
        return font["OS/2"].fsSelection, font["head"].macStyle


def blank(data, *ranges):
    data = bytearray(data)
    for r in ranges:
        data[r] = bytes(r.stop - r.start)
    return bytes(data)


def loosen_glyph_encoding(path, glyph_name="A"):
    """Re-encode one all-on-curve simple glyph of the font at `path` without
    compression: a flag per point, every delta an int16. The outline, bounding
    box and every other table stay as they are; a WOFF2 round trip encodes the
    glyph compactly again, so glyf and loca bytes differ for the same glyphs --
    as they do between the real TTFs and their WOFF2s."""
    with TTFont(path, recalcBBoxes=False, recalcTimestamp=False) as font:
        glyf = font["glyf"]
        glyph = glyf[glyph_name]
        coordinates = glyph.getCoordinates(glyf)[0]
        assert glyph.numberOfContours > 0 and all(flag & 1 for flag in glyph.flags)
        data = struct.pack(">hhhhh", glyph.numberOfContours, glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax)
        data += struct.pack(f">{len(glyph.endPtsOfContours)}HH", *glyph.endPtsOfContours, 0)
        data += bytes([1] * len(coordinates))  # on curve; x and y each an int16 delta
        previous = (0, 0)
        xs, ys = b"", b""
        for x, y in coordinates:
            xs += struct.pack(">h", x - previous[0])
            ys += struct.pack(">h", y - previous[1])
            previous = (x, y)
        glyf[glyph_name] = Glyph(data + xs + ys)
        font.save(path)


def save_woff2_from(ttf, woff2, header_version=None, alter=None):
    """ttf saved as WOFF2, after alter(font) when given."""
    font = TTFont(ttf, recalcBBoxes=False, recalcTimestamp=False)
    if alter:
        alter(font)
    font.flavor = "woff2"
    font.save(woff2)
    font.close()
    if header_version:
        with open(woff2, "r+b") as fh:
            fh.seek(24)
            fh.write(struct.pack(">HH", *header_version))
    return woff2


def raise_underline(font):
    font["post"].underlinePosition += 1


def change_version_string(font):
    for record in font["name"].names:
        if record.nameID == 5:
            record.string = "Version 0.0.1"


def mangled_case_name(case, extension=".ttf"):
    return CASES[case][0][6].replace("NFM", "NerdFontMono") + extension


def fixed_case_name(case, extension=".ttf"):
    return CASES[case][5] + extension


def run_tool(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = tool.main([str(a) for a in args])
    return code, out.getvalue(), err.getvalue()


def records(path):
    with TTFont(path, lazy=True) as font:
        return {(r.platformID, r.platEncID, r.langID, r.nameID): r.toUnicode() for r in font["name"].names}


def raw_tables(path):
    with TTFont(path, lazy=True) as font:
        return {tag: font.reader[tag] for tag in font.reader.keys()}


def snapshot(directory):
    """Every entry of the directory: a link as its target, a file as its bytes."""
    entries = {}
    for p in sorted(directory.iterdir()):
        if p.is_symlink():
            entries[p.name] = ("link", os.readlink(p))
        elif p.is_dir():
            entries[p.name] = ("dir", snapshot(p))
        else:
            entries[p.name] = p.read_bytes()
    return entries


class FontTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        # Many synthetic fonts carry contradictory style bits on purpose, and
        # fontTools warns each time it compiles their OS/2 table (the tool never
        # does: it writes the raw bytes). Those warnings are noise here.
        os2_log = logging.getLogger("fontTools.ttLib.tables.O_S_2f_2")
        self.addCleanup(os2_log.setLevel, os2_log.level)
        os2_log.setLevel(logging.ERROR)

    def assert_names(self, path, expected):
        found = records(path)
        for platform in ((1, 0, 0), (3, 1, 0x409)):
            for name_id, text in {**OTHER_NAMES, **expected}.items():
                self.assertEqual(found.get((*platform, name_id)), text, f"{path.name} {platform} ID {name_id}")
        self.assertEqual(len(found), 2 * len({**OTHER_NAMES, **expected}), "records added or removed")

    def assert_no_temp_files(self):
        self.assertEqual([p.name for p in self.dir.iterdir() if p.name.endswith(".tmp")], [])

    def assert_only_style_changed(self, before, after, renamed=False):
        """`after` holds `before`'s tables (raw_tables) byte for byte apart
        from the two style fields and checkSumAdjustment -- and 'name', when
        renamed."""
        self.assertEqual(sorted(before), sorted(after))
        for tag in before:
            if tag == "name" and renamed:
                continue
            if tag == "OS/2":
                self.assertEqual(blank(before[tag], OS2_FS_SELECTION), blank(after[tag], OS2_FS_SELECTION), tag)
            elif tag == "head":
                self.assertEqual(
                    blank(before[tag], HEAD_CHECKSUM, HEAD_MAC_STYLE), blank(after[tag], HEAD_CHECKSUM, HEAD_MAC_STYLE)
                )
            else:
                self.assertEqual(before[tag], after[tag], tag)


class TestNames(FontTestCase):
    def test_each_case_gets_the_siblings_names_file_name_and_style_bits(self):
        for case, (_, _, fs, mac, expected, stem) in CASES.items():
            with self.subTest(case=case):
                source = save_case(self.dir, case)
                code, out, err = run_tool(source)
                self.assertEqual(code, 0, err)
                target = self.dir / f"{stem}.ttf"
                self.assertTrue(target.is_file(), out)
                self.assertFalse(source.exists(), "the mangled file must be gone")
                self.assert_names(target, expected)
                self.assertEqual(style_of(target), SIBLING_STYLE[case])
                if (fs, mac) == SIBLING_STYLE[case]:
                    self.assertNotIn("fsSelection", out)
                else:
                    self.assertIn(f"fsSelection {fs:#06x} -> {SIBLING_STYLE[case][0]:#06x}", out)

    def test_weight_spelling_follows_the_siblings(self):
        for mangled, sibling, weight in WEIGHT_SPELLINGS:
            with self.subTest(weight=weight):
                inspection = tool.inspect_font(build_font(mangled_names_for(mangled, ""), weight, 0x0180))
                self.assertEqual(inspection.kind, "mangled", inspection.reason)
                self.assertEqual(inspection.face.file_stem, f"NoctuaIosevkaNerdFontMono-SemiExtended{sibling}")
                legacy = f"{FAMILY} SemiExtended" + (f" {sibling}" if sibling not in ("", "Bold") else "")
                self.assertEqual(tool.fixed_names(inspection.face)[1], legacy)

    def test_only_names_and_the_two_style_fields_change(self):
        source = save_case(self.dir, "bold-oblique")
        before = raw_tables(source)
        with TTFont(source, lazy=True) as font:
            modified = font["head"].modified
        code, _, err = run_tool(source)
        self.assertEqual(code, 0, err)
        target = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtendedBoldOblique.ttf"
        after = raw_tables(target)
        self.assertNotEqual(before["name"], after["name"])
        # OS/2 apart from fsSelection (bytes 62-63); head apart from
        # checkSumAdjustment (8-11) and macStyle (44-45); the rest as it was.
        self.assert_only_style_changed(before, after, renamed=True)
        self.assertEqual(struct.unpack(">H", after["OS/2"][OS2_FS_SELECTION]), (0x03A0,))
        self.assertEqual(struct.unpack(">H", after["head"][HEAD_MAC_STYLE]), (0x0001,))
        with TTFont(target, lazy=True) as font:
            self.assertEqual(font["head"].modified, modified)

    def test_ttf_verification_is_byte_for_byte(self):
        a = save_case(self.dir, "regular", file_name="a.ttf")
        b = save_case(self.dir, "regular", file_name="b.ttf", rise=50)
        with TTFont(a, lazy=True) as fa, TTFont(b, lazy=True) as fb:
            with self.assertRaises(tool.Refusal):
                tool.check_tables(fa, fb, "test")
        with TTFont(a, lazy=True) as fa, TTFont(a, lazy=True) as same:
            tool.check_tables(fa, same, "test")

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_permission_bits_are_kept(self):
        source = save_case(self.dir, "regular")
        source.chmod(0o640)
        self.assertEqual(run_tool(source)[0], 0)
        target = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtended.ttf"
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)


class TestBehaviour(FontTestCase):
    def test_idempotent(self):
        source = save_case(self.dir, "oblique")
        self.assertEqual(run_tool(source)[0], 0)
        target = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtendedOblique.ttf"
        before = snapshot(self.dir)
        stat = target.stat()
        code, out, err = run_tool(target)
        self.assertEqual(code, 0, err)
        self.assertIn("already fixed", out)
        self.assertEqual(snapshot(self.dir), before)
        self.assertEqual(target.stat().st_mtime_ns, stat.st_mtime_ns)

    def test_dry_run_changes_nothing(self):
        source = save_case(self.dir, "bold")
        if HAVE_BROTLI:
            save_woff2_from(source, self.dir / "NoctuaIosevkaBoldSemiNerdFontMono-Extended.woff2")
        before = snapshot(self.dir)
        code, out, err = run_tool("--dry-run", *sorted(self.dir.iterdir()))
        self.assertEqual(code, 0, err)
        self.assertIn("would fix", out)
        self.assertIn("NoctuaIosevkaNerdFontMono-SemiExtendedBold.ttf", out)
        self.assertEqual(snapshot(self.dir), before)

    def test_refuses_to_overwrite_an_existing_target(self):
        source = save_case(self.dir, "regular")
        target = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtended.ttf"
        target.write_bytes(b"occupied")
        before = snapshot(self.dir)
        code, _, err = run_tool(source)
        self.assertEqual(code, 1)
        self.assertIn("refusing to overwrite", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_mangled_names_already_on_the_target_file_name_are_fixed_in_place(self):
        source = save_case(self.dir, "regular", file_name="NoctuaIosevkaNerdFontMono-SemiExtended.ttf")
        code, _, err = run_tool(source)
        self.assertEqual(code, 0, err)
        self.assertEqual([p.name for p in self.dir.iterdir()], [source.name])
        self.assert_names(source, CASES["regular"][4])

    def test_other_widths_and_plain_fonts_are_skipped(self):
        names = {
            1: f"{FAMILY} Condensed", 2: "Regular", 3: f"{FAMILY} Condensed 3.4.0", 4: f"{FAMILY} Condensed",
            6: "NoctuaIosevkaNFM-Condensed", 16: FAMILY, 17: "Condensed",
        }
        condensed = self.dir / "NoctuaIosevkaNerdFontMono-Condensed.ttf"
        build_font(names, 400, 0x0180, width=3).save(condensed)
        plain = self.dir / "NoctuaIosevka-SemiExtended.ttf"
        build_font({1: "Noctua Iosevka Semi-Extended", 2: "Regular"}, 400, 0x00C0).save(plain)
        before = snapshot(self.dir)
        code, out, err = run_tool(condensed, plain)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.count("skipped"), 2)
        self.assertEqual(snapshot(self.dir), before)

    def test_a_near_match_is_refused_not_guessed(self):
        names, _, fs, mac, _, _ = CASES["bold"]
        source = self.dir / "NoctuaIosevkaBoldSemiNerdFontMono-Extended.ttf"
        build_font(names, 400, fs, mac).save(source)  # "Bold" in the family, weight 400
        before = snapshot(self.dir)
        code, _, err = run_tool(source)
        self.assertEqual(code, 1)
        self.assertIn("left untouched", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_unknown_identifier_ids_are_refused(self):
        names, weight, fs, mac, _, _ = CASES["regular"]
        source = self.dir / "NoctuaIosevkaSemiNerdFontMono-Extended.ttf"
        build_font({**names, 21: "NoctuaIosevkaSemi Nerd Font Mono"}, weight, fs, mac).save(source)
        before = snapshot(self.dir)
        code, _, err = run_tool(source)
        self.assertEqual(code, 1)
        self.assertIn("convention is unknown", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_extension_must_match_content(self):
        source = save_case(self.dir, "regular")
        disguised = source.rename(self.dir / "NoctuaIosevkaSemiNerdFontMono-Extended.woff2")
        before = snapshot(self.dir)
        self.assertEqual(run_tool(disguised)[0], 1)
        self.assertEqual(snapshot(self.dir), before)

    def test_symbolic_links_are_refused(self):
        source = save_case(self.dir, "regular")
        link = self.dir / "link.ttf"
        try:
            link.symlink_to(source.name)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links unavailable here")
        before = snapshot(self.dir)
        code, _, err = run_tool(link)
        self.assertEqual(code, 1)
        self.assertIn("symbolic link", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_help_describes_the_tool(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as raised:
            tool.main(["--help"])
        self.assertEqual(raised.exception.code, 0)
        for word in ("SemiExtended", "--dry-run", "--ttf-dir", "WOFF2", "fsSelection", "macStyle"):
            self.assertIn(word, out.getvalue())
        # The bold bits are restored now: the help states the rule, and no
        # longer says they are left as they are.
        self.assertIn("Style bits. The rule is the one every correctly named Nerd face", out.getvalue())
        self.assertIn("BOLD (bit 5) and head macStyle Bold (bit 0) set", out.getvalue())
        self.assertNotIn("Known limit", out.getvalue())

    def test_the_help_prose_is_wrapped(self):
        # --help prints the description as written (RawDescriptionHelpFormatter):
        # its prose is wrapped at 79 columns, and only the indented usage
        # examples and name-table rows may run longer.
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            tool.main(["--help"])
        self.assertIn(tool.__doc__.strip(), out.getvalue())
        long = [line for line in tool.__doc__.splitlines() if len(line) > 79 and not re.match(r"    (\./|ID )", line)]
        self.assertEqual(long, [])


EXTRABOLD_FIXED_NAMES = {
    1: f"{FAMILY} SemiExtended ExtraBold",
    2: "Regular",
    3: f"{FAMILY} SemiExtended ExtraBold 3.4.0",
    4: f"{FAMILY} SemiExtended ExtraBold",
    6: "NoctuaIosevkaNFM-SemiExtendedExtraBold",
    16: FAMILY,
    17: "SemiExtended ExtraBold",
}


class TestStyleBits(FontTestCase):
    """fsSelection BOLD/REGULAR and macStyle Bold follow the siblings."""

    def test_a_face_with_fixed_names_and_cleared_bold_bits_is_fixed_in_place(self):
        for case in ("bold", "bold-italic", "bold-oblique"):
            with self.subTest(case=case):
                source = save_fixed_names(self.dir, case)
                before = raw_tables(source)
                self.assertNotEqual(style_of(source), SIBLING_STYLE[case], "the case this test is for")
                code, out, err = run_tool(source)
                self.assertEqual(code, 0, err)
                self.assertNotRegex(out, r"(?m)^already fixed")
                self.assertIn(f"fixed        {source} -> {source.name} (names already fixed; fsSelection ", out)
                self.assertTrue(source.is_file())
                self.assertEqual(style_of(source), SIBLING_STYLE[case])
                self.assert_only_style_changed(before, raw_tables(source))  # 'name' byte for byte too
                self.assert_names(source, CASES[case][4])
        self.assert_no_temp_files()

    def test_a_misstyled_face_keeps_its_own_file_name(self):
        source = save_fixed_names(self.dir, "bold", file_name="custom.ttf")
        code, out, err = run_tool(source)
        self.assertEqual(code, 0, err)
        self.assertIn("file name differs from NoctuaIosevkaNerdFontMono-SemiExtendedBold", out)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["custom.ttf"])
        self.assertEqual(style_of(source), SIBLING_STYLE["bold"])

    def test_dry_run_reports_a_misstyled_face_and_writes_nothing(self):
        source = save_fixed_names(self.dir, "bold-italic")
        before = snapshot(self.dir)
        code, out, err = run_tool("--dry-run", source)
        self.assertEqual(code, 0, err)
        self.assertIn(
            f"would fix    {source} -> {source.name} "
            "(names already fixed; fsSelection 0x0181 -> 0x01a1, macStyle 0x0002 -> 0x0003)",
            out,
        )
        self.assertEqual(snapshot(self.dir), before)

    def test_a_second_run_changes_no_byte(self):
        mangled = save_case(self.dir, "bold-oblique")
        misstyled = save_fixed_names(self.dir, "bold")
        code, out, err = run_tool(mangled, misstyled)
        self.assertEqual((code, out.count("fixed        ")), (0, 2), err)
        before = snapshot(self.dir)
        mtimes = {p.name: p.stat().st_mtime_ns for p in self.dir.iterdir()}
        for dry_run in ([], ["--dry-run"]):
            code, out, err = run_tool(*dry_run, self.dir)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(re.findall(r"(?m)^already fixed ", out)), 2, out)
            self.assertNotIn("would fix", out)
        self.assertEqual(snapshot(self.dir), before)
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in self.dir.iterdir()}, mtimes)

    def test_the_bits_follow_the_weight_in_both_directions(self):
        rows = [
            # (names, usWeightClass, fsSelection, macStyle found -> expected)
            (CASES["regular"][4], 400, 0x01C0, 0x0000, (0x0180, 0x0000)),  # REGULAR: normal width only
            (CASES["bold"][4], 700, 0x01C0, 0x0000, (0x01A0, 0x0001)),  # never REGULAR on a bold face
            (CASES["bold"][4], 700, 0x01A0, 0x0000, (0x01A0, 0x0001)),  # macStyle Bold alone lost
            (CASES["bold"][4], 700, 0x0180, 0x0001, (0x01A0, 0x0001)),  # fsSelection BOLD alone lost
            (EXTRABOLD_FIXED_NAMES, 800, 0x01A0, 0x0001, (0x0180, 0x0000)),  # ExtraBold is not Bold
        ]
        for names, weight, fs, mac, expected in rows:
            with self.subTest(name=names[6], fs=fs, mac=mac):
                source = self.dir / "face.ttf"
                build_font(names, weight, fs, mac).save(source)
                before = raw_tables(source)
                code, out, err = run_tool(source)
                self.assertEqual(code, 0, err)
                self.assertEqual(style_of(source), expected)
                self.assert_only_style_changed(before, raw_tables(source))

    def test_every_weight_and_slope_gets_the_bold_bits_exactly_at_700(self):
        # The helpers reproduce the six measured cases.
        for case, (names, weight, fs, mac, _, _) in CASES.items():
            (patcher_weight,) = [w for w, _, value in WEIGHT_SPELLINGS if value == weight]
            slope = "Oblique" if fs & 0x0200 else "Italic" if fs & 0x0001 else ""
            self.assertEqual(mangled_names_for(patcher_weight, slope), names, case)
            self.assertEqual(slope_style(slope), (fs, mac), case)
        # Each of the 27 faces, given with BOLD, REGULAR and macStyle Bold all
        # clear and then all set, first with its names mangled and then with
        # them fixed: BOLD and macStyle Bold come out set exactly on weight
        # 700, REGULAR never, and ID 2 says Bold on those faces and no other.
        for patcher_weight, sibling, weight in WEIGHT_SPELLINGS:
            for slope in SLOPES:
                fs, mac = slope_style(slope)
                bold = weight == 700
                expected = (fs | 0x0020, mac | 0x0001) if bold else (fs, mac)
                subfamily = " ".join(w for w in ("Bold" if bold else "", "Italic" if slope else "") if w) or "Regular"
                for given in ((fs, mac), (fs | 0x0060, mac | 0x0001)):
                    with self.subTest(weight=weight, slope=slope, given=given):
                        directory = self.dir / f"{weight}{slope}-{given[0]:04x}"
                        directory.mkdir()
                        mangled = directory / "mangled.ttf"
                        build_font(mangled_names_for(patcher_weight, slope), weight, *given).save(mangled)
                        code, out, err = run_tool(mangled)
                        self.assertEqual(code, 0, err)
                        target = directory / f"NoctuaIosevkaNerdFontMono-SemiExtended{sibling}{slope}.ttf"
                        self.assertEqual(style_of(target), expected)
                        self.assertEqual(records(target)[(3, 1, 0x409, 2)], subfamily)
                        # The same face, names fixed, with the bits as given again.
                        patch_uint16(target, "OS/2", OS2_FS_SELECTION.start, given[0])
                        patch_uint16(target, "head", HEAD_MAC_STYLE.start, given[1])
                        before = raw_tables(target)
                        code, out, err = run_tool(target)
                        self.assertEqual(code, 0, err)
                        self.assertEqual(style_of(target), expected)
                        self.assert_only_style_changed(before, raw_tables(target))
                        self.assertEqual(out.startswith("already fixed "), given == expected, out)

    def test_bits_that_depend_on_neither_weight_nor_slope_are_refused_not_repaired(self):
        # Every sibling carries fsSelection USE_TYPO_METRICS and WWS and no
        # other bit beside the weight and slope ones, and no macStyle bit
        # beside Bold and Italic. A face that differs there is refused, with
        # its names mangled or fixed, its bold bits right or wrong.
        rows = [
            ("bold", 0x0000, 0x0000),  # USE_TYPO_METRICS and WWS lost
            ("bold", 0x00A0, 0x0001),  # WWS lost, the bold bits right
            ("regular", 0x0100, 0x0000),  # USE_TYPO_METRICS lost
            ("bold-italic", 0x0183, 0x0002),  # UNDERSCORE (bit 1)
            ("oblique", 0x0390, 0x0000),  # STRIKEOUT (bit 4)
            ("oblique", 0x0780, 0x0000),  # a reserved bit (10)
            ("bold", 0x01A0, 0x0041),  # macStyle Extended (bit 6), the plain faces' width bit
            ("bold-oblique", 0x0380, 0x0020),  # macStyle Condensed (bit 5)
            ("regular", 0x0180, 0x8000),  # a reserved macStyle bit
        ]
        for case, fs, mac in rows:
            for names in ("mangled", "fixed"):
                with self.subTest(case=case, fs=fs, mac=mac, names=names):
                    directory = self.dir / f"{case}-{fs:04x}-{mac:04x}-{names}"
                    directory.mkdir()
                    if names == "fixed":
                        save_fixed_names(directory, case, fs, mac)
                    else:
                        build_font(CASES[case][0], CASES[case][1], fs, mac).save(directory / mangled_case_name(case))
                    before = snapshot(directory)
                    code, out, err = run_tool(directory)
                    self.assertEqual(code, 1, out)
                    self.assertIn("depend on neither weight nor slope", err)
                    self.assertIn("left untouched", err)
                    self.assertEqual(out, "")
                    self.assertEqual(snapshot(directory), before)

    def test_slope_bits_that_disagree_are_refused_not_repaired(self):
        rows = [
            ("bold-italic", 0x0181, 0x0000),  # Italic without macStyle Italic
            ("bold-oblique", 0x0380, 0x0002),  # Oblique with macStyle Italic
            ("oblique", 0x0381, 0x0000),  # ITALIC and OBLIQUE both
            ("bold", 0x0180, 0x0002),  # upright with macStyle Italic
        ]
        for case, fs, mac in rows:
            for names in ("mangled", "fixed"):
                with self.subTest(case=case, names=names):
                    directory = self.dir / f"{case}-{names}"
                    directory.mkdir()
                    if names == "fixed":
                        save_fixed_names(directory, case, fs, mac)
                    else:
                        _, weight, _, _, _, _ = CASES[case]
                        build_font(CASES[case][0], weight, fs, mac).save(directory / mangled_case_name(case))
                    before = snapshot(directory)
                    code, out, err = run_tool(directory)
                    self.assertEqual(code, 1, out)
                    self.assertIn("slope bits", err)
                    self.assertIn("left untouched", err)
                    self.assertEqual(snapshot(directory), before)

    def test_the_style_fields_are_written_as_bytes_not_recompiled(self):
        # A usFirstCharIndex that disagrees with cmap ("A" is its only
        # character): compiling OS/2 through fontTools would rewrite it.
        source = save_case(self.dir, "bold")
        patch_uint16(source, "OS/2", OS2_FIRST_CHAR_INDEX, 0x0020)
        with TTFont(source) as font:
            recompiled = font["OS/2"].compile(font)
        first_char = slice(OS2_FIRST_CHAR_INDEX, OS2_FIRST_CHAR_INDEX + 2)
        self.assertNotEqual(recompiled[first_char], b"\0\x20", "the case this test is for")
        before = raw_tables(source)
        code, out, err = run_tool(source)
        self.assertEqual(code, 0, err)
        after = raw_tables(self.dir / fixed_case_name("bold"))
        self.assert_only_style_changed(before, after, renamed=True)
        self.assertEqual(style_of(self.dir / fixed_case_name("bold")), SIBLING_STYLE["bold"])

    def test_other_widths_and_plain_faces_in_the_same_directory_are_left_alone(self):
        misstyled = save_fixed_names(self.dir, "bold")
        fixed = save_fixed_names(self.dir, "regular")
        names = {
            1: f"{FAMILY} Condensed", 2: "Bold", 3: f"{FAMILY} Condensed Bold 3.4.0", 4: f"{FAMILY} Condensed Bold",
            6: "NoctuaIosevkaNFM-CondensedBold", 16: FAMILY, 17: "Condensed Bold",
        }
        condensed = self.dir / "NoctuaIosevkaNerdFontMono-CondensedBold.ttf"
        build_font(names, 700, 0x0180, width=3).save(condensed)  # cleared bits, another width: not ours
        plain = self.dir / "NoctuaIosevka-SemiExtendedBold.ttf"
        build_font({1: "Noctua Iosevka Semi-Extended Bold", 2: "Regular"}, 700, 0x0080).save(plain)
        before = snapshot(self.dir)
        code, out, err = run_tool(self.dir)
        self.assertEqual(code, 0, err)
        after = snapshot(self.dir)
        self.assertEqual(sorted(after), sorted(before))
        for name in before:
            if name == misstyled.name:
                self.assertNotEqual(after[name], before[name])
            else:
                self.assertEqual(after[name], before[name], name)
        self.assertEqual(out.count("skipped"), 2)
        self.assertIn(f"already fixed {fixed}", out)


class TestTargets(FontTestCase):
    """A link at the target name is an existing target, never the source."""

    def assert_refused_untouched(self, *args, message="refusing to overwrite existing"):
        before = snapshot(self.dir)
        code, out, err = run_tool(*args)
        self.assertEqual(code, 1, out)
        self.assertIn(message, err)
        self.assertNotIn("fixed", out)
        self.assertEqual(snapshot(self.dir), before)
        self.assert_no_temp_files()

    def symlink(self, link, target):
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links unavailable here")

    def test_a_symbolic_link_to_the_source_at_the_target_name_is_refused(self):
        source = save_case(self.dir, "bold")
        self.symlink(self.dir / fixed_case_name("bold"), source.name)
        self.assert_refused_untouched(source)

    def test_a_dangling_symbolic_link_at_the_target_name_is_refused(self):
        source = save_case(self.dir, "bold")
        self.symlink(self.dir / fixed_case_name("bold"), "nowhere.ttf")
        self.assert_refused_untouched(source)

    def test_a_hard_link_to_the_source_at_the_target_name_is_refused(self):
        source = save_case(self.dir, "bold")
        try:
            os.link(source, self.dir / fixed_case_name("bold"))
        except (OSError, NotImplementedError):
            self.skipTest("hard links unavailable here")
        self.assert_refused_untouched(source)

    def test_a_hard_link_whose_name_differs_only_in_case_is_refused(self):
        source = save_case(self.dir, "regular", file_name=fixed_case_name("regular", ".TTF"))
        target = self.dir / fixed_case_name("regular")
        if target.exists():
            self.skipTest("case-insensitive file system: the two spellings are one entry")
        try:
            os.link(source, target)
        except (OSError, NotImplementedError):
            self.skipTest("hard links unavailable here")
        self.assert_refused_untouched(source)

    def test_on_a_case_insensitive_file_system_a_case_variant_is_the_source(self):
        # Simulated where the file system is case-sensitive: a hard link gives
        # the second spelling the same file, and the directory listing shows
        # one entry only, as a case-insensitive file system would.
        source = save_case(self.dir, "regular", file_name=fixed_case_name("regular", ".TTF"))
        target = self.dir / fixed_case_name("regular")
        if target.exists():
            self.skipTest("case-insensitive file system: covered by the real rename test")
        try:
            os.link(source, target)
        except (OSError, NotImplementedError):
            self.skipTest("hard links unavailable here")
        with TTFont(source, lazy=True) as font:
            face = tool.inspect_font(font).face
        with mock.patch.object(tool.os, "listdir", return_value=[source.name]):
            self.assertEqual(tool.plan_target(source, face), (target, True))
        with self.assertRaises(tool.Refusal):  # the real listing: two entries
            tool.plan_target(source, face)

    def test_a_source_whose_name_differs_from_the_target_only_in_case_is_fixed(self):
        # In place on a case-insensitive file system, renamed on a sensitive one.
        source = save_case(self.dir, "regular", file_name=fixed_case_name("regular", ".TTF"))
        code, out, err = run_tool(source)
        self.assertEqual(code, 0, err)
        (left,) = self.dir.iterdir()
        self.assertEqual(left.name.casefold(), fixed_case_name("regular").casefold())
        self.assert_names(left, CASES["regular"][4])


class TestArguments(FontTestCase):
    def test_a_directory_stands_for_the_fonts_directly_inside_it(self):
        source = save_case(self.dir, "bold")
        (self.dir / "notes.txt").write_text("not a font")
        nested = self.dir / "nested"
        nested.mkdir()
        save_case(nested, "regular")
        nested_before = snapshot(nested)
        code, out, err = run_tool(self.dir)
        self.assertEqual(code, 0, err)
        self.assertFalse(source.exists())
        self.assert_names(self.dir / fixed_case_name("bold"), CASES["bold"][4])
        self.assertEqual((self.dir / "notes.txt").read_text(), "not a font")
        self.assertEqual(snapshot(nested), nested_before, "subdirectories are not entered")

    def test_a_pattern_the_shell_left_unexpanded_is_expanded(self):
        source = save_case(self.dir, "oblique")
        code, out, err = run_tool(self.dir / "*.ttf")
        self.assertEqual(code, 0, err)
        self.assertFalse(source.exists())
        self.assert_names(self.dir / fixed_case_name("oblique"), CASES["oblique"][4])

    def test_an_existing_name_holding_a_wildcard_character_is_taken_literally(self):
        literal = save_case(self.dir, "regular", file_name="[a].ttf")
        plain = self.dir / "a.ttf"
        build_font({1: "Noctua Iosevka Semi-Extended", 2: "Regular"}, 400, 0x00C0).save(plain)
        plain_before = plain.read_bytes()
        code, out, err = run_tool(literal)
        self.assertEqual(code, 0, err)
        self.assertFalse(literal.exists())
        self.assertTrue((self.dir / fixed_case_name("regular")).is_file())
        self.assertEqual(plain.read_bytes(), plain_before)
        self.assertNotIn("skipped", out)

    def test_a_pattern_that_matches_nothing_is_an_error(self):
        save_case(self.dir, "regular")
        before = snapshot(self.dir)
        code, _, err = run_tool(self.dir / "*.woff2")
        self.assertEqual(code, 1)
        self.assertIn("no file matches it", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_each_match_of_a_pattern_is_judged_on_its_own(self):
        fonts, empty = self.dir / "fonts", self.dir / "fonts-empty"
        fonts.mkdir()
        empty.mkdir()
        source = save_case(fonts, "bold")
        code, out, err = run_tool(self.dir / "fonts*")
        self.assertEqual(code, 1, out)
        self.assertIn("fonts-empty: is a directory with no .ttf or .woff2 file", err)
        self.assertFalse(source.exists())
        self.assert_names(fonts / fixed_case_name("bold"), CASES["bold"][4])

    def test_a_directory_without_fonts_is_an_error_not_a_missing_file(self):
        empty = self.dir / "empty"
        empty.mkdir()
        code, _, err = run_tool(empty)
        self.assertEqual(code, 1)
        self.assertIn("is a directory with no .ttf or .woff2 file", err)
        self.assertNotIn("no such file", err)

    def test_a_symbolic_link_to_a_directory_is_refused(self):
        real = self.dir / "real"
        real.mkdir()
        source = save_case(real, "regular")
        link = self.dir / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links unavailable here")
        code, _, err = run_tool(link)
        self.assertEqual(code, 1)
        self.assertIn("symbolic link", err)
        self.assertTrue(source.exists())

    def test_other_nerd_fonts_variants_are_skipped_unless_they_look_mangled(self):
        family = "NoctuaIosevka Nerd Font"
        correct = {
            1: f"{family} SemiExtended", 2: "Regular", 3: f"{family} SemiExtended 3.4.0",
            4: f"{family} SemiExtended", 6: "NoctuaIosevkaNF-SemiExtended", 16: family, 17: "SemiExtended",
        }
        plain_nerd = self.dir / "NoctuaIosevkaNerdFont-SemiExtended.ttf"
        build_font(correct, 400, 0x0180).save(plain_nerd)
        before = snapshot(self.dir)
        code, out, err = run_tool(plain_nerd)
        self.assertEqual(code, 0, err)
        self.assertIn("skipped", out)
        self.assertIn("other than Mono", out)
        self.assertEqual(snapshot(self.dir), before)

        m = "NoctuaIosevkaBoldSemi Nerd Font Propo"
        mangled = {
            1: f"{m} Extended", 2: "Regular", 3: f"{m} Extended 3.4.0", 4: f"{m} Extended",
            6: "NoctuaIosevkaBoldSemiNFP-Extended", 16: m, 17: "Extended",
        }
        propo = self.dir / "NoctuaIosevkaBoldSemiNerdFontPropo-Extended.ttf"
        build_font(mangled, 700, 0x0180).save(propo)
        before = snapshot(self.dir)
        code, out, err = run_tool(propo)
        self.assertEqual(code, 1, out)
        self.assertIn("variant other than Mono", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_other_file_types_are_refused(self):
        source = save_case(self.dir, "regular")
        otf = source.rename(self.dir / "NoctuaIosevkaSemiNerdFontMono-Extended.otf")
        before = snapshot(self.dir)
        code, _, err = run_tool(otf)
        self.assertEqual(code, 1)
        self.assertIn("unsupported extension", err)
        self.assertEqual(snapshot(self.dir), before)


class TestVerification(FontTestCase):
    """Each check of a written TTF fires: the tool refuses and changes nothing.

    The faults are injected between the rewrite and the save, standing in for
    a fontTools or tool bug that the reload-and-compare step must catch.
    """

    def run_with_fault(self, alter, case="bold-italic", source=None):
        source = source or save_case(self.dir, case)
        real = tool.write_temp

        def write_temp(target, save):
            alter(save.__self__)  # the font about to be saved
            return real(target, save)

        before = snapshot(self.dir)
        with mock.patch.object(tool, "write_temp", write_temp):
            code, out, err = run_tool(source)
        self.assertEqual(code, 1, out)
        self.assertIn("verification failed", err)
        self.assertEqual(snapshot(self.dir), before)
        self.assert_no_temp_files()
        return err

    def test_a_changed_table_other_than_name_is_caught(self):
        self.assertIn("table 'post' differs", self.run_with_fault(raise_underline))

    def test_a_changed_record_of_another_id_is_caught(self):
        self.assertRegex(self.run_with_fault(change_version_string), r"name ID 5 \(\d+,\d+,0x[0-9a-f]+\) changed")

    def test_an_added_name_record_is_caught(self):
        err = self.run_with_fault(lambda font: font["name"].setName("Extra", 19, 3, 1, 0x409))
        self.assertIn("the set of name records changed", err)

    def test_a_wrong_rewritten_record_is_caught(self):
        def wrong(font):
            for record in font["name"].names:
                if record.nameID == 4:
                    record.string = "Wrong"

        self.assertIn("name ID 4", self.run_with_fault(wrong))

    def test_a_wrong_style_field_is_caught(self):
        def italic_too(font):  # head is the raw table restyle handed over
            head = font["head"]
            head.data = head.data[:44] + struct.pack(">H", 0x0003) + head.data[46:]

        self.assertIn("table 'head' differs", self.run_with_fault(italic_too, case="bold"))

    def test_another_byte_changed_beside_a_style_field_is_caught(self):
        def fs_type(font):
            os2 = font["OS/2"]
            os2.data = os2.data[:9] + bytes([os2.data[9] ^ 0x08]) + os2.data[10:]

        self.assertIn("table 'OS/2' differs", self.run_with_fault(fs_type, case="bold"))

    def test_a_style_change_that_was_never_written_is_caught(self):
        with mock.patch.object(tool, "restyle", lambda font, style: None):
            self.assertIn("table 'OS/2' differs", self.run_with_fault(lambda font: None, case="bold-oblique"))

    def test_bits_written_at_the_wrong_offset_are_caught_by_reading_them_back(self):
        # restyle and the byte comparison share the offset; reading the field
        # back through fontTools does not.
        with mock.patch.object(tool, "OS2_FS_SELECTION_OFFSET", 60):
            err = self.run_with_fault(lambda font: None, case="bold")
        self.assertIn("the written file has fsSelection 0x0180", err)

    def test_macstyle_written_at_the_wrong_offset_is_caught_by_reading_it_back(self):
        with mock.patch.object(tool, "HEAD_MAC_STYLE_OFFSET", 46):  # lowestRecPPEM
            err = self.run_with_fault(lambda font: None, case="bold-italic")
        self.assertIn("the written file has fsSelection 0x01a1, macStyle 0x0002, expected", err)

    def test_a_misstyled_face_keeps_its_name_table_byte_for_byte(self):
        # Trailing bytes change the table and no record in it: only comparing
        # the bytes, not the records, can tell.
        def pad_name(font):
            table = DefaultTable("name")
            table.data = font.reader["name"] + b"\0\0"
            font["name"] = table

        source = save_fixed_names(self.dir, "bold")
        self.assertIn("table 'name' differs", self.run_with_fault(pad_name, source=source))

    def test_styled_refuses_a_table_too_short_for_its_field(self):
        style = tool.Style(0x01A0, 0x0001)
        self.assertEqual(len(tool.styled("OS/2", bytes(64), style)), 64)
        self.assertEqual(len(tool.styled("head", bytes(46), style)), 46)
        for tag, size in (("OS/2", 63), ("head", 45)):
            with self.subTest(tag=tag), self.assertRaisesRegex(tool.Refusal, "too short"):
                tool.styled(tag, bytes(size), style)
        self.assertEqual(tool.styled("post", b"abc", style), b"abc")

    def test_restyle_refuses_a_decoded_table(self):
        path = save_fixed_names(self.dir, "bold")
        with TTFont(path, lazy=True) as font:
            font["OS/2"]  # decoded: saving would recompile it
            with self.assertRaisesRegex(tool.Refusal, "would be recompiled"):
                tool.restyle(font, tool.Style(0x01A0, 0x0001))

    def test_check_face_requires_the_style_and_the_fixed_face(self):
        path = save_fixed_names(self.dir, "bold", *SIBLING_STYLE["bold"])
        with TTFont(path, lazy=True) as font:
            inspection = tool.inspect_font(font)
            self.assertEqual(inspection.kind, "fixed")
            tool.check_face(font, inspection.face, inspection.style)
            with self.assertRaisesRegex(tool.Refusal, "has fsSelection 0x01a0, macStyle 0x0001, expected"):
                tool.check_face(font, inspection.face, tool.Style(0x0180, 0x0000))
            other = tool.Face(inspection.face.base, inspection.face.weight, inspection.face.slope, "9.9.9")
            with self.assertRaisesRegex(tool.Refusal, "not as the fixed face"):
                tool.check_face(font, other, inspection.style)

    def test_a_target_that_appears_while_working_is_not_overwritten(self):
        source = save_case(self.dir, "regular")
        source_bytes = source.read_bytes()
        target = self.dir / fixed_case_name("regular")
        real = tool.write_temp

        def write_temp(target_path, save):
            tmp = real(target_path, save)
            target_path.write_bytes(b"another process")
            return tmp

        with mock.patch.object(tool, "write_temp", write_temp):
            code, _, err = run_tool(source)
        self.assertEqual(code, 1)
        self.assertIn("appeared while working", err)
        self.assertEqual(target.read_bytes(), b"another process")
        self.assertEqual(source.read_bytes(), source_bytes)
        self.assert_no_temp_files()

    def test_a_dsig_signature_is_refused(self):
        names, weight, fs, mac, _, _ = CASES["regular"]
        font = build_font(names, weight, fs, mac)
        dsig = newTable("DSIG")
        dsig.ulVersion, dsig.usFlag, dsig.usNumSigs, dsig.signatureRecords = 1, 0, 0, []
        font["DSIG"] = dsig
        source = self.dir / mangled_case_name("regular")
        font.save(source)
        before = snapshot(self.dir)
        code, _, err = run_tool(source)
        self.assertEqual(code, 1)
        self.assertIn("DSIG", err)
        self.assertEqual(snapshot(self.dir), before)


@unittest.skipUnless(HAVE_BROTLI, "brotli is needed for WOFF2")
class TestWoff2(FontTestCase):
    def test_woff2_is_regenerated_from_the_fixed_ttf(self):
        ttf = save_case(self.dir, "bold-italic")
        woff2 = save_woff2_from(ttf, self.dir / "NoctuaIosevkaBoldSemiNerdFontMono-ExtendedItalic.woff2", (7, 3))
        code, out, err = run_tool(woff2, ttf)  # the order of the arguments does not matter
        self.assertEqual(code, 0, err)
        self.assertIn("regenerated from", out)
        new_ttf = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtendedBoldItalic.ttf"
        new_woff2 = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtendedBoldItalic.woff2"
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), sorted([new_ttf.name, new_woff2.name]))
        self.assert_names(new_woff2, CASES["bold-italic"][4])
        ttf_tables, woff2_tables = raw_tables(new_ttf), raw_tables(new_woff2)
        self.assertEqual(sorted(ttf_tables), sorted(woff2_tables))
        for tag in ttf_tables:
            if tag not in ("glyf", "loca", "head"):
                self.assertEqual(ttf_tables[tag], woff2_tables[tag], tag)
        with TTFont(new_ttf, lazy=True) as a, TTFont(new_woff2, lazy=True) as b:
            self.assertTrue(tool.glyphs_equal(a, b))
            self.assertEqual((b.flavorData.majorVersion, b.flavorData.minorVersion), (7, 3))

    def test_woff2_found_through_ttf_dir(self):
        ttf_dir, woff2_dir = self.dir / "TTF", self.dir / "WOFF2"
        ttf_dir.mkdir()
        woff2_dir.mkdir()
        ttf = save_case(ttf_dir, "oblique")
        woff2 = save_woff2_from(ttf, woff2_dir / "NoctuaIosevkaSemiNerdFontMono-ExtendedOblique.woff2")
        self.assertEqual(run_tool(ttf)[0], 0)
        code, out, err = run_tool("--ttf-dir", ttf_dir, woff2)
        self.assertEqual(code, 0, err)
        self.assertIn("regenerated from", out)
        new_woff2 = woff2_dir / "NoctuaIosevkaNerdFontMono-SemiExtendedOblique.woff2"
        self.assertEqual(
            raw_tables(new_woff2)["name"], raw_tables(ttf_dir / "NoctuaIosevkaNerdFontMono-SemiExtendedOblique.ttf")["name"]
        )

    def test_woff2_without_ttf_is_fixed_directly(self):
        ttf = save_case(self.dir, "extralight-italic")
        woff2 = save_woff2_from(ttf, self.dir / "NoctuaIosevkaExtralightSemiNerdFontMono-ExtendedItalic.woff2")
        ttf.unlink()
        before = raw_tables(woff2)
        code, out, err = run_tool(woff2)
        self.assertEqual(code, 0, err)
        self.assertIn("names rewritten", out)
        new_woff2 = self.dir / "NoctuaIosevkaNerdFontMono-SemiExtendedExtraLightItalic.woff2"
        self.assertFalse(woff2.exists())
        self.assert_names(new_woff2, CASES["extralight-italic"][4])
        after = raw_tables(new_woff2)
        for tag in before:
            if tag == "head":
                self.assertEqual(before[tag][:8] + before[tag][12:], after[tag][:8] + after[tag][12:])
            elif tag != "name":
                self.assertEqual(before[tag], after[tag], tag)

    def test_woff2_is_refused_when_its_ttf_has_other_content(self):
        ttf_dir = self.dir / "TTF"
        ttf_dir.mkdir()
        other = save_case(ttf_dir, "regular", rise=50)  # same face, different outline
        self.assertEqual(run_tool(other)[0], 0)
        unrelated_source = save_case(self.dir, "regular")
        woff2 = save_woff2_from(unrelated_source, self.dir / "NoctuaIosevkaSemiNerdFontMono-Extended.woff2")
        unrelated_source.unlink()
        before = snapshot(self.dir / "TTF"), woff2.read_bytes()
        code, _, err = run_tool("--ttf-dir", ttf_dir, woff2)
        self.assertEqual(code, 1)
        self.assertIn("verification failed", err)
        self.assertEqual((snapshot(self.dir / "TTF"), woff2.read_bytes()), before)
        self.assertFalse((self.dir / "NoctuaIosevkaNerdFontMono-SemiExtended.woff2").exists())
        self.assert_no_temp_files()

    def fixed_ttf_in(self, directory, case="regular", **build):
        directory.mkdir(exist_ok=True)
        code, _, err = run_tool(save_case(directory, case, **build))
        self.assertEqual(code, 0, err)
        return directory / fixed_case_name(case)

    def mangled_woff2(self, case="regular", header_version=None, alter=None, **build):
        """The mangled WOFF2 of `case` in self.dir, with no TTF beside it."""
        source = save_case(self.dir, case, file_name="source.ttf", **build)
        woff2 = save_woff2_from(source, self.dir / mangled_case_name(case, ".woff2"), header_version, alter)
        source.unlink()
        return woff2

    def assert_refused(self, *args, message):
        before = snapshot(self.dir)
        code, out, err = run_tool(*args)
        self.assertEqual(code, 1, out)
        self.assertIn(message, err)
        self.assertEqual(snapshot(self.dir), before)
        self.assert_no_temp_files()
        return err

    def test_a_counterpart_differing_in_one_glyph_only_is_refused(self):
        # The same bounding box, metrics, head and maxp: only the outline differs,
        # so nothing but the glyph-by-glyph comparison can tell.
        ttf_dir = self.dir / "TTF"
        self.fixed_ttf_in(ttf_dir, dent=50)
        woff2 = self.mangled_woff2()
        self.assert_refused("--ttf-dir", ttf_dir, woff2, message="the glyphs differ")

    def test_glyf_laid_out_again_by_woff2_is_compared_glyph_by_glyph(self):
        ttf = save_case(self.dir, "regular")
        loosen_glyph_encoding(ttf)
        woff2 = save_woff2_from(ttf, self.dir / mangled_case_name("regular", ".woff2"))
        code, out, err = run_tool(ttf, woff2)
        self.assertEqual(code, 0, err)
        new_ttf, new_woff2 = self.dir / fixed_case_name("regular"), self.dir / fixed_case_name("regular", ".woff2")
        self.assertNotEqual(raw_tables(new_ttf)["glyf"], raw_tables(new_woff2)["glyf"], "the case this test is for")
        with TTFont(new_ttf, lazy=True) as a, TTFont(new_woff2, lazy=True) as b:
            self.assertTrue(tool.glyphs_equal(a, b))

    def run_with_saver_fault(self, alter, message):
        """The regenerated WOFF2 is altered in transit; the old WOFF2 carries
        the same alteration, so only the comparison with the TTF can tell."""
        ttf_dir = self.dir / "TTF"
        self.fixed_ttf_in(ttf_dir)
        woff2 = self.mangled_woff2(alter=alter)
        real = tool.woff2_saver

        def woff2_saver(font, old_flavor):
            alter(font)
            return real(font, old_flavor)

        with mock.patch.object(tool, "woff2_saver", woff2_saver):
            self.assert_refused("--ttf-dir", ttf_dir, woff2, message=message)

    def test_a_woff2_that_does_not_hold_its_ttf_tables_is_caught(self):
        self.run_with_saver_fault(raise_underline, "new WOFF2 vs its TTF: table 'post' differs")

    def test_a_woff2_whose_names_differ_from_its_ttf_is_caught(self):
        self.run_with_saver_fault(change_version_string, "new WOFF2 vs its TTF: 'name' differs")

    def test_a_lost_woff2_header_version_is_caught(self):
        ttf_dir = self.dir / "TTF"
        self.fixed_ttf_in(ttf_dir)
        woff2 = self.mangled_woff2(header_version=(7, 3))
        real = tool.woff2_saver

        def woff2_saver(font, old_flavor):
            real(font, old_flavor)
            return font.save  # without the header-version patch

        with mock.patch.object(tool, "woff2_saver", woff2_saver):
            self.assert_refused("--ttf-dir", ttf_dir, woff2, message="the WOFF2 header data changed")

    def test_two_candidate_counterparts_are_refused_as_ambiguous(self):
        ttf_dir = self.dir / "TTF"
        ttf = self.fixed_ttf_in(ttf_dir)
        woff2 = self.mangled_woff2()
        shutil.copy2(ttf, self.dir / ttf.name)  # the same content, beside the WOFF2
        self.assert_refused("--ttf-dir", ttf_dir, woff2, message="ambiguous TTF counterparts")

    def test_a_counterpart_that_is_not_the_fixed_form_is_refused_in_a_dry_run_too(self):
        # Mangled names under the fixed file name, beside the WOFF2, not passed.
        woff2 = self.mangled_woff2()
        save_case(self.dir, "regular", file_name=fixed_case_name("regular"))
        for dry_run in (["--dry-run"], []):
            with self.subTest(dry_run=bool(dry_run)):
                err = self.assert_refused(*dry_run, woff2, message="is not the fixed form of this face")
                self.assertIn(fixed_case_name("regular"), err)

    def test_a_counterpart_with_another_version_is_refused(self):
        ttf_dir = self.dir / "TTF"
        names, weight, fs, mac, _, _ = CASES["regular"]
        ttf_dir.mkdir()
        other = {**names, 3: names[3].replace("3.4.0", "3.4.1")}
        source = ttf_dir / mangled_case_name("regular")
        build_font(other, weight, fs, mac).save(source)
        self.assertEqual(run_tool(source)[0], 0)
        woff2 = self.mangled_woff2()
        self.assert_refused("--ttf-dir", ttf_dir, woff2, message="is not the fixed form of this face")

    def test_a_misstyled_woff2_is_regenerated_from_its_fixed_ttf(self):
        ttf = save_fixed_names(self.dir, "bold-italic")
        woff2 = save_woff2_from(ttf, self.dir / fixed_case_name("bold-italic", ".woff2"), (7, 3))
        old = raw_tables(woff2)
        code, out, err = run_tool(woff2, ttf)
        self.assertEqual(code, 0, err)
        self.assertIn(f"regenerated from {ttf.resolve()}", out)
        self.assertEqual(out.count("names already fixed; fsSelection 0x0181 -> 0x01a1, macStyle 0x0002 -> 0x0003"), 2)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), sorted([ttf.name, woff2.name]))
        self.assertEqual(style_of(ttf), SIBLING_STYLE["bold-italic"])
        self.assertEqual(style_of(woff2), SIBLING_STYLE["bold-italic"])
        self.assert_only_style_changed(old, raw_tables(woff2))
        ttf_tables, woff2_tables = raw_tables(ttf), raw_tables(woff2)
        for tag in ttf_tables:
            if tag not in ("glyf", "loca", "head"):
                self.assertEqual(ttf_tables[tag], woff2_tables[tag], tag)
        with TTFont(woff2, lazy=True) as b:
            self.assertEqual((b.flavorData.majorVersion, b.flavorData.minorVersion), (7, 3))

    def test_a_misstyled_woff2_without_its_ttf_is_restyled_directly(self):
        ttf = save_fixed_names(self.dir, "bold-oblique", file_name="source.ttf")
        woff2 = save_woff2_from(ttf, self.dir / fixed_case_name("bold-oblique", ".woff2"))
        ttf.unlink()
        old = raw_tables(woff2)
        code, out, err = run_tool(woff2)
        self.assertEqual(code, 0, err)
        self.assertIn("(style bits rewritten; names already fixed; fsSelection 0x0380 -> 0x03a0", out)
        self.assertEqual(style_of(woff2), SIBLING_STYLE["bold-oblique"])
        self.assert_only_style_changed(old, raw_tables(woff2))

    def test_bits_written_at_the_wrong_offset_in_a_woff2_are_caught_by_reading_them_back(self):
        # A WOFF2 with no TTF to regenerate from is restyled directly. restyle
        # and the byte comparison share the offsets: only reading the fields
        # back through fontTools can tell, on this path as on the TTF's.
        rows = [
            ("OS2_FS_SELECTION_OFFSET", 60, "the written file has fsSelection 0x0180, macStyle 0x0001, expected"),
            ("HEAD_MAC_STYLE_OFFSET", 46, "the written file has fsSelection 0x01a0, macStyle 0x0000, expected"),
        ]
        for constant, offset, message in rows:
            for names in ("fixed", "mangled"):
                with self.subTest(field=constant, names=names):
                    for path in self.dir.iterdir():
                        path.unlink()
                    if names == "fixed":
                        source = save_fixed_names(self.dir, "bold", file_name="source.ttf")
                        woff2 = save_woff2_from(source, self.dir / fixed_case_name("bold", ".woff2"))
                        source.unlink()
                    else:
                        woff2 = self.mangled_woff2("bold")
                    with mock.patch.object(tool, constant, offset):
                        self.assert_refused(woff2, message=message)

    def test_a_second_run_over_woff2s_changes_no_byte(self):
        # One WOFF2 regenerated from its TTF, one restyled and one renamed and
        # restyled directly, with no TTF beside them.
        ttf = save_case(self.dir, "bold-italic")
        save_woff2_from(ttf, self.dir / mangled_case_name("bold-italic", ".woff2"))
        lone = save_fixed_names(self.dir, "bold-oblique", file_name="lone.ttf")
        save_woff2_from(lone, self.dir / fixed_case_name("bold-oblique", ".woff2"))
        lone.unlink()
        self.mangled_woff2("bold")
        code, out, err = run_tool(self.dir)
        self.assertEqual(code, 0, err)
        for how in ("regenerated from", "(style bits rewritten;", "(names and style bits rewritten;"):
            self.assertIn(how, out)
        files = sorted(p.name for p in self.dir.iterdir())
        woff2s = [fixed_case_name(case, ".woff2") for case in ("bold-italic", "bold-oblique", "bold")]
        self.assertEqual(files, sorted([fixed_case_name("bold-italic"), *woff2s]))
        before = snapshot(self.dir)
        mtimes = {p.name: p.stat().st_mtime_ns for p in self.dir.iterdir()}
        for dry_run in ([], ["--dry-run"]):
            with self.subTest(dry_run=bool(dry_run)):
                code, out, err = run_tool(*dry_run, self.dir)
                self.assertEqual(code, 0, err)
                for name in files:
                    self.assertIn(f"already fixed {self.dir / name}\n", out)
                self.assertEqual(out.count("\n"), len(files), out)
        self.assertEqual(snapshot(self.dir), before)
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in self.dir.iterdir()}, mtimes)

    def test_a_mangled_bold_woff2_without_its_ttf_gets_names_and_bits(self):
        woff2 = self.mangled_woff2("bold")
        code, out, err = run_tool(woff2)
        self.assertEqual(code, 0, err)
        self.assertIn("names and style bits rewritten", out)
        new_woff2 = self.dir / fixed_case_name("bold", ".woff2")
        self.assert_names(new_woff2, CASES["bold"][4])
        self.assertEqual(style_of(new_woff2), SIBLING_STYLE["bold"])

    def test_a_misstyled_ttf_counterpart_is_refused_unless_this_run_fixes_it(self):
        ttf_dir = self.dir / "TTF"
        ttf_dir.mkdir()
        ttf = save_fixed_names(ttf_dir, "bold")
        woff2 = save_woff2_from(ttf, self.dir / fixed_case_name("bold", ".woff2"))
        for dry_run in (["--dry-run"], []):
            with self.subTest(dry_run=bool(dry_run)):
                err = self.assert_refused(*dry_run, "--ttf-dir", ttf_dir, woff2, message="its style bits are not fixed")
                self.assertIn(str(ttf.resolve()), err)
        before = snapshot(self.dir)
        code, out, err = run_tool("--dry-run", "--ttf-dir", ttf_dir, woff2, ttf)
        self.assertEqual((code, out.count("would fix")), (0, 2), err)
        self.assertIn(f"regenerated from {ttf.resolve()}", out)
        self.assertEqual(snapshot(self.dir), before)
        code, out, err = run_tool("--ttf-dir", ttf_dir, woff2, ttf)
        self.assertEqual(code, 0, err)
        self.assertEqual(style_of(ttf), SIBLING_STYLE["bold"])
        self.assertEqual(style_of(woff2), SIBLING_STYLE["bold"])

    def test_a_dry_run_trusts_only_the_ttf_it_would_fix_itself(self):
        # The mangled TTF already carries the fixed file name: a dry run would
        # fix it in place, so the WOFF2 is reported as regenerated from it.
        ttf = save_case(self.dir, "regular", file_name=fixed_case_name("regular"))
        woff2 = save_woff2_from(ttf, self.dir / mangled_case_name("regular", ".woff2"))
        before = snapshot(self.dir)
        code, out, err = run_tool("--dry-run", ttf, woff2)
        self.assertEqual(code, 0, err)
        self.assertIn(f"regenerated from {ttf.resolve()}", out)
        self.assertEqual(snapshot(self.dir), before)
        code, out, err = run_tool(ttf, woff2)
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), [ttf.name, fixed_case_name("regular", ".woff2")])


@unittest.skipUnless(REAL_TTF.is_dir() and any(REAL_TTF.glob("*.ttf")), "real Nerd fonts absent")
class TestRealFonts(unittest.TestCase):
    """The built fonts: no mangled or misstyled face left, one family, no
    duplicate faces, and each SemiExtended face carrying the style bits of
    its siblings."""

    OTHER_WIDTHS = ("Condensed", "SemiCondensed", "Extended")

    def check_style_against_siblings(self, directory, extension):
        semi = sorted(directory.glob(f"*-SemiExtended*{extension}"))
        self.assertTrue(semi)
        styles = {}
        for path in semi:
            prefix, tail = path.stem.split("-SemiExtended", 1)  # tail: weight and slope
            mine = styles.setdefault(path, style_of(path))
            for width in self.OTHER_WIDTHS:
                sibling = path.with_name(f"{prefix}-{width}{tail}{extension}")
                self.assertEqual(style_of(sibling), mine, f"{path.name} vs {sibling.name}")
        # The cases the synthetic tests use are the real values.
        stems = {CASES[case][5]: case for case in SIBLING_STYLE}
        for path, style in styles.items():
            if path.stem in stems:
                self.assertEqual(style, SIBLING_STYLE[stems[path.stem]], path.name)

    def test_ttf_style_bits(self):
        self.check_style_against_siblings(REAL_TTF, ".ttf")

    @unittest.skipUnless(HAVE_BROTLI and REAL_WOFF2.is_dir(), "brotli or the WOFF2 directory absent")
    def test_woff2_style_bits(self):
        self.check_style_against_siblings(REAL_WOFF2, ".woff2")

    def check_directory(self, directory, pattern):
        paths = sorted(directory.glob(pattern))
        pairs, postscript = set(), set()
        for path in paths:
            with TTFont(path, lazy=True) as font:
                inspection = tool.inspect_font(font)
                self.assertIn(inspection.kind, ("fixed", "unrelated"), f"{path.name}: {inspection.reason}")
                names = font["name"]
                family = str(names.getName(16, 3, 1, 0x409) or names.getName(1, 3, 1, 0x409))
                style = str(names.getName(17, 3, 1, 0x409) or names.getName(2, 3, 1, 0x409))
                self.assertEqual(family, FAMILY, path.name)
                pairs.add((family, style))
                postscript.add(str(names.getName(6, 3, 1, 0x409)))
            if inspection.kind == "fixed":
                self.assertEqual(path.stem, inspection.face.file_stem)
        self.assertEqual(len(pairs), len(paths), "duplicate (family, subfamily)")
        self.assertEqual(len(postscript), len(paths), "duplicate PostScript names")

    def test_ttf(self):
        self.check_directory(REAL_TTF, "*.ttf")

    @unittest.skipUnless(HAVE_BROTLI and REAL_WOFF2.is_dir(), "brotli or the WOFF2 directory absent")
    def test_woff2(self):
        self.check_directory(REAL_WOFF2, "*.woff2")


if __name__ == "__main__":
    unittest.main()
