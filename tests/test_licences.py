"""Tests for the repository's licence files and for the pins in the Iosevka build plan.

What they guard:

  * LICENSE, LICENSE-MIT and LICENSE-APACHE exist. LICENSE states the dual licence,
    keeps the fonts out of it, and does not call every Nerd Fonts icon MIT: the icon
    sets Nerd Fonts gathers keep their upstream licences (CC BY 4.0, Apache 2.0, SIL
    OFL 1.1, the Unlicense), and LICENSE has to say so. When the sibling repositories
    are checked out beside this one, LICENSE-APACHE and LICENSE-MIT are byte-identical
    to theirs; a lone clone skips that comparison.
  * Every copy of the Nerd Fonts licence is byte-identical to the original in
    symbols-nerd-font/licenses/.
  * noctua-iosevka/private-build-plans.toml still parses, its notes are TOML comments
    only (Iosevka's build reads the file), and they pin Iosevka v34.7.0,
    nerdfonts/patcher:4.26.0 by digest, and ttfautohint 1.8.4.
  * Against the real fonts, when they are present: name ID 5 of every TTF face agrees
    with those pins, and the Material Design icons of one Nerd Font face per width are
    the ones the pinned patcher draws. nerdfonts/patcher:4.25.0, the pin first
    recorded, draws 132 of them differently, so this test would have caught it.

The unit tests build their fonts in memory with fontTools' FontBuilder. The tests
that read the real fonts skip when the fonts are absent, as in a fresh clone, where
git tracks none of them.

Safety: these tests only read. Nothing is written into the repository or next to the
fonts, and no fontconfig cache is touched. Pin parsing fails closed: a pin line that
is missing, duplicated, or malformed is an error, never a silent pass.
"""

import hashlib
import io
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    # Before 3.11. check.py refuses such a Python; CI's oldest job runs the other modules on 3.9,
    # and unittest reports this one as skipped.
    raise unittest.SkipTest("needs Python 3.11 or later, for tomllib")

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import otRound
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parent.parent
WORKSPACE_REPOS = REPO.parent
SIBLINGS = ("noctua-colors", "noctua-design")
PLAN = REPO / "noctua-iosevka" / "private-build-plans.toml"
NERD_LICENSE = "LICENSE-NerdFontsSymbolsOnly.txt"
NERD_LICENSE_ORIGINAL = REPO / "symbols-nerd-font" / "licenses" / NERD_LICENSE
NERD_LICENSE_COPIES = (
    REPO / "noctua-iosevka" / "licenses" / NERD_LICENSE,
    REPO / "noctua-noto" / "licenses" / NERD_LICENSE,
)
PLAIN_TTF = REPO / "noctua-iosevka" / "TTF"
NERD_TTF = REPO / "noctua-iosevka" / "TTF-nerdfonts"

EXPECTED_PINS = {
    "iosevka_tag": "v34.7.0",
    "iosevka_commit": "6828cb0bd569992bb19565a5e448540de3b50541",
    "patcher_tag": "4.26.0",
    "patcher_digest": "d18c1bd44f4577bf359f5cc0b61767bbda2658c6680ff9255cd770e630527efb",
    "nerd_fonts_version": "3.4.0",
    "ttfautohint": "1.8.4",
}
# The image first pinned by mistake. It predates the Material Design ScaleGroups
# (nerd-fonts PR #2033) and does not reproduce the shipped faces.
REJECTED_PATCHER = ("4.25.0", "a08d50b3461bff7c33b3bf33f913f46482f7f9b7157d92529021a7ad99f5ed73")

# ---------------------------------------------------------------------------
# Pins in the build plan's comment header

PIN_PATTERNS = {
    "iosevka_tag": re.compile(
        r"^#\s+Iosevka\s+git tag (v\d+\.\d+\.\d+) of https://github\.com/be5invis/Iosevka$"),
    "iosevka_commit": re.compile(r"^#\s+= commit ([0-9a-f]{40})$"),
    "patcher_tag": re.compile(
        r"^#\s+Nerd Fonts patcher\s+Docker image nerdfonts/patcher:(\d+\.\d+\.\d+),"
        r" which stamps \"Nerd Fonts \d+\.\d+\.\d+\"[.;]?$"),
    "nerd_fonts_version": re.compile(
        r"^#\s+Nerd Fonts patcher\s+Docker image nerdfonts/patcher:\d+\.\d+\.\d+,"
        r" which stamps \"Nerd Fonts (\d+\.\d+\.\d+)\"[.;]?$"),
    "patcher_digest": re.compile(r"^#\s+= sha256:([0-9a-f]{64})$"),
    "ttfautohint": re.compile(r"^#\s+ttfautohint\s+(\d+\.\d+\.\d+),"),
}


def comment_header(text):
    """The lines before the first TOML statement: comments and blank lines only."""
    header = []
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            break
        header.append(line)
    return header


def read_pins(text):
    """{pin: value} from the comment header. Raises ValueError unless each pin is
    found exactly once, so a lost or doubled pin line fails rather than passes."""
    header = comment_header(text)
    pins = {}
    for name, pattern in PIN_PATTERNS.items():
        found = [m.group(1) for m in map(pattern.match, header) if m]
        if len(found) != 1:
            raise ValueError(f"pin {name!r}: expected one line, found {len(found)}")
        pins[name] = found[0]
    return pins


# ---------------------------------------------------------------------------
# Material Design icon fingerprint

MDI_FIRST, MDI_LAST = 0xF0001, 0xF1AF0   # Nerd Fonts' Material Design icon range


def mdi_fingerprint(font):
    """(icon count, SHA-256 hex) over the Material Design icons of a TrueType font.

    Each icon contributes its code point, advance width, contour ends, and every point
    with its on-curve bit, so a change in scale, position, or width changes the hash.
    Glyph names and the encoding details of the glyf table do not."""
    cmap = font.getBestCmap() or {}
    glyf, hmtx = font["glyf"], font["hmtx"]
    digest = hashlib.sha256()
    count = 0
    for code_point in range(MDI_FIRST, MDI_LAST + 1):
        name = cmap.get(code_point)
        if name is None:
            continue
        coordinates, ends, flags = glyf[name].getCoordinates(glyf)
        points = ";".join(f"{otRound(x)},{otRound(y)},{flag & 1}"
                          for (x, y), flag in zip(coordinates, flags))
        digest.update(f"U+{code_point:X} {hmtx[name][0]} {list(ends)} {points}\n".encode("ascii"))
        count += 1
    return count, digest.hexdigest()


# mdi_fingerprint of what each image draws, keyed by OS/2 usWidthClass. Measured on
# 2026-11-01 by running the image (by digest) with the build guide's --mono --complete
# on a scratch copy of one shipped plain face of each width. On that day all 27 shipped
# Nerd faces of each width had exactly the 4.26.0 value.
MDI_ICON_COUNT = 6896
PINNED_PATCHER_MDI = {   # nerdfonts/patcher:4.26.0, sha256:d18c1bd4...
    3: "22ee233552d726397ffed21b6f9a850fbf44aa8de85fe08a60f198294ddfb050",  # Condensed
    4: "4c2c0082e5d724ee0cb3eea418cad3178bea42a0793ec77ed76985fc540e96c5",  # SemiCondensed
    5: "41b5c62fc980063e93b0dc8b4dd2ff26e479d94b2f22e4f56c56a2fb5fea5523",  # Normal
    6: "9168ab888c53831e43a0859dfd40c97ad79d26086815e9f765db2a04dfb35dd0",  # SemiExtended
    7: "ff61f2c3886f8cfdc49d157e3411c9f884f5637f96f3899585919a52057bcc35",  # Extended
}
REJECTED_PATCHER_MDI = {   # nerdfonts/patcher:4.25.0, sha256:a08d50b3...
    3: "afae653bd7a2897c049f1137af3556d1e074a20fb854002105f9d4afba7981ae",
    4: "119b15851e1c5a451b35d15181340de666468f679b51a020ce93f1adf7d09af6",
    5: "7d5a94b51b21b3f98e5cc8c2b9b5312f9c700e0be97590f2793ba5f248289c12",
    6: "c05d1fac5cfdc168b566072b1862830505ea03110cffafb291f4b747fb21e4ec",
    7: "347cd9ba3a08aa855464660fb41921ee7f6fa8c281e1cea25bc3c6d1feead555",
}


def _square(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def build_font(icons, extra=None, names=None):
    """An in-memory TrueType font. icons maps a code point to (advance, box); extra
    adds glyphs outside the icon range the same way; names renames glyphs."""
    names = names or {}
    order = [".notdef"]
    cmap, glyphs, metrics = {}, {}, {}
    pen = TTGlyphPen(None)
    glyphs[".notdef"], metrics[".notdef"] = pen.glyph(), (500, 0)
    for code_point, (advance, box) in {**icons, **(extra or {})}.items():
        name = names.get(code_point, f"uni{code_point:X}")
        pen = TTGlyphPen(None)
        _square(pen, *box)
        order.append(name)
        cmap[code_point] = name
        glyphs[name] = pen.glyph()
        metrics[name] = (advance, box[0])
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Synthetic", "styleName": "Regular"})
    builder.setupOS2()
    builder.setupPost()
    data = io.BytesIO()
    builder.save(data)
    data.seek(0)
    return TTFont(data)


ICONS = {0xF00DA: (500, (50, 0, 450, 400)), 0xF013C: (500, (0, 0, 500, 500))}

# ---------------------------------------------------------------------------
# Unit tests: no real fonts needed


SAMPLE_HEADER = """\
# A plan.
#
#   Iosevka             git tag v1.2.3 of https://github.com/be5invis/Iosevka
#                       = commit 0123456789abcdef0123456789abcdef01234567
#   Nerd Fonts patcher  Docker image nerdfonts/patcher:4.5.6, which stamps "Nerd Fonts 3.2.1".
#                       Pull it by digest.
#                       = sha256:89abcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567
#   ttfautohint         1.8.4, for both hinting passes

[buildPlans.Sample]
family = "Sample"
"""
SAMPLE_PINS = {
    "iosevka_tag": "v1.2.3",
    "iosevka_commit": "0123456789abcdef0123456789abcdef01234567",
    "patcher_tag": "4.5.6",
    "patcher_digest": "89abcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567",
    "nerd_fonts_version": "3.2.1",
    "ttfautohint": "1.8.4",
}


class PinParsingTest(unittest.TestCase):
    def test_reads_every_pin(self):
        self.assertEqual(read_pins(SAMPLE_HEADER), SAMPLE_PINS)

    def test_a_missing_pin_line_is_an_error(self):
        without = "\n".join(line for line in SAMPLE_HEADER.splitlines()
                            if not line.startswith("#   ttfautohint"))
        with self.assertRaisesRegex(ValueError, "ttfautohint"):
            read_pins(without)

    def test_a_doubled_pin_line_is_an_error(self):
        doubled = "#                       = sha256:" + "0" * 64 + "\n" + SAMPLE_HEADER
        with self.assertRaisesRegex(ValueError, "patcher_digest"):
            read_pins(doubled)

    def test_a_malformed_digest_is_an_error(self):
        short = SAMPLE_HEADER.replace("01234567\n#   ttfautohint", "0123456\n#   ttfautohint")
        self.assertNotEqual(short, SAMPLE_HEADER)
        with self.assertRaisesRegex(ValueError, "patcher_digest"):
            read_pins(short)

    def test_a_pin_after_the_first_table_does_not_count(self):
        moved = [line for line in SAMPLE_HEADER.splitlines()
                 if not line.startswith("#   ttfautohint")]
        moved.append("#   ttfautohint         1.8.4, moved below the tables")
        with self.assertRaisesRegex(ValueError, "ttfautohint"):
            read_pins("\n".join(moved))

    def test_a_header_with_no_statement_after_it_is_still_read(self):
        self.assertEqual(comment_header("# a\n\n# b\n"), ["# a", "", "# b"])


class MdiFingerprintTest(unittest.TestCase):
    def test_counts_only_the_material_design_range(self):
        font = build_font(ICONS, extra={0x41: (500, (0, 0, 10, 10)), 0xF1AF1: (500, (0, 0, 9, 9))})
        self.assertEqual(mdi_fingerprint(font)[0], 2)

    def test_glyph_names_do_not_matter(self):
        renamed = build_font(ICONS, names={0xF00DA: "mdi-a", 0xF013C: "mdi-b"})
        self.assertEqual(mdi_fingerprint(renamed), mdi_fingerprint(build_font(ICONS)))

    def test_a_rescaled_icon_changes_it(self):
        rescaled = {**ICONS, 0xF00DA: (500, (60, 10, 440, 390))}
        self.assertNotEqual(mdi_fingerprint(build_font(rescaled))[1],
                            mdi_fingerprint(build_font(ICONS))[1])

    def test_an_advance_change_changes_it(self):
        wider = {**ICONS, 0xF013C: (600, (0, 0, 500, 500))}
        self.assertNotEqual(mdi_fingerprint(build_font(wider))[1],
                            mdi_fingerprint(build_font(ICONS))[1])

    def test_glyphs_outside_the_range_do_not_matter(self):
        a = build_font(ICONS, extra={0x41: (500, (0, 0, 10, 10))})
        b = build_font(ICONS, extra={0x41: (700, (5, 5, 90, 90))})
        self.assertEqual(mdi_fingerprint(a), mdi_fingerprint(b))

    def test_a_font_without_icons_has_none(self):
        self.assertEqual(mdi_fingerprint(build_font({}))[0], 0)


# ---------------------------------------------------------------------------
# The repository's own files


class RootLicenceTest(unittest.TestCase):
    def setUp(self):
        self.text = (REPO / "LICENSE").read_text(encoding="utf-8")

    def test_the_three_files_exist(self):
        for name in ("LICENSE", "LICENSE-MIT", "LICENSE-APACHE"):
            self.assertTrue((REPO / name).is_file(), name)

    def test_states_the_dual_licence(self):
        self.assertTrue(self.text.startswith(
            "noctua-fonts is dual-licensed, at your option, under either of:"))
        self.assertIn("see LICENSE-APACHE", self.text)
        self.assertIn("see LICENSE-MIT", self.text)

    def test_keeps_the_fonts_out_of_it(self):
        self.assertIn("The fonts are NOT covered by it.", self.text)
        for path in ("noctua-iosevka/licenses/OFL-Iosevka.txt", "noctua-noto/licenses/",
                     f"symbols-nerd-font/licenses/{NERD_LICENSE}"):
            self.assertIn(path, self.text)

    def test_does_not_call_every_nerd_fonts_icon_mit(self):
        """The Nerd Fonts icon sets keep their upstream licences, and several are not
        MIT. LICENSE once said the icons in the patched faces were all MIT."""
        flat = " ".join(self.text.split())
        self.assertNotIn("are under the MIT license too", flat)
        for licence in ("CC BY 4.0", "Apache 2.0", "SIL Open Font License 1.1", "Unlicense"):
            self.assertIn(licence, flat)
        for list_ in ("license-audit.md", "src/glyphs/README.md",
                      "https://github.com/ryanoasis/nerd-fonts"):
            self.assertIn(list_, flat)

    def test_the_mit_text_names_the_noctua_project(self):
        first = (REPO / "LICENSE-MIT").read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(first, "Copyright (c) 2026 The Noctua Project Contributors")

    def test_the_texts_match_the_sibling_repositories(self):
        siblings = [WORKSPACE_REPOS / s for s in SIBLINGS if (WORKSPACE_REPOS / s).is_dir()]
        if not siblings:
            self.skipTest("no sibling repository is checked out beside this one")
        for sibling in siblings:
            for name in ("LICENSE-APACHE", "LICENSE-MIT"):
                with self.subTest(sibling=sibling.name, file=name):
                    self.assertEqual((REPO / name).read_bytes(), (sibling / name).read_bytes())


class NerdLicenceCopyTest(unittest.TestCase):
    def test_every_copy_is_identical_to_the_original(self):
        original = NERD_LICENSE_ORIGINAL.read_bytes()
        for copy in NERD_LICENSE_COPIES:
            with self.subTest(copy=copy.relative_to(REPO).as_posix()):
                self.assertEqual(copy.read_bytes(), original)


class BuildPlanTest(unittest.TestCase):
    def setUp(self):
        self.text = PLAN.read_text(encoding="utf-8")

    def test_still_parses_and_keeps_its_family(self):
        plan = tomllib.loads(self.text)
        self.assertEqual(plan["buildPlans"]["NoctuaIosevka"]["family"], "Noctua Iosevka")

    def test_the_notes_are_comments_before_the_first_table(self):
        header = comment_header(self.text)
        self.assertGreater(len(header), 1)
        self.assertEqual(self.text.splitlines()[len(header)], "[buildPlans.NoctuaIosevka]")
        self.assertTrue(self.text.isascii())

    def test_records_the_pins(self):
        self.assertEqual(read_pins(self.text), EXPECTED_PINS)
        self.assertIn("Pull it by digest", self.text)

    def test_does_not_pin_the_patcher_that_misses_the_faces(self):
        """4.25.0 was pinned first; patching with it changes 132 Material Design icons."""
        pins = read_pins(self.text)
        self.assertNotEqual(pins["patcher_tag"], REJECTED_PATCHER[0])
        self.assertNotEqual(pins["patcher_digest"], REJECTED_PATCHER[1])

    def test_the_two_images_are_told_apart_in_every_width(self):
        self.assertEqual(set(PINNED_PATCHER_MDI), set(REJECTED_PATCHER_MDI))
        for width, digest in PINNED_PATCHER_MDI.items():
            self.assertNotEqual(digest, REJECTED_PATCHER_MDI[width], width)


# ---------------------------------------------------------------------------
# The real fonts, when present


def _faces(folder):
    return sorted(folder.glob("*.ttf")) if folder.is_dir() else []


def _read(path, reader):
    """reader(font) on a lazily opened font, closing the file afterwards."""
    with TTFont(path, lazy=True) as font:
        return reader(font)


@unittest.skipUnless(_faces(PLAIN_TTF) and _faces(NERD_TTF),
                     "the built Noctua Iosevka fonts are not in this checkout")
class RealFontPinTest(unittest.TestCase):
    def setUp(self):
        self.pins = read_pins(PLAN.read_text(encoding="utf-8"))
        self.version = self.pins["iosevka_tag"].removeprefix("v")

    def test_name_id_5_agrees_with_the_pins(self):
        expected = {
            PLAIN_TTF: f"Version {self.version}; ttfautohint (v{self.pins['ttfautohint']})",
            NERD_TTF: f"Version {self.version};Nerd Fonts {self.pins['nerd_fonts_version']}",
        }
        for folder, version in expected.items():
            for path in _faces(folder):
                with self.subTest(face=path.name):
                    self.assertEqual(_read(path, lambda f: f["name"].getDebugName(5)), version)

    def test_the_material_design_icons_are_the_pinned_patchers(self):
        """One face of each width. On 2026-11-01 all 27 faces of a width shared the
        value, and fingerprinting all 135 takes about two minutes, too slow here."""
        by_width = {}
        for path in _faces(NERD_TTF):
            by_width.setdefault(_read(path, lambda f: f["OS/2"].usWidthClass), path)
        self.assertEqual(set(by_width), set(PINNED_PATCHER_MDI))
        for width, path in sorted(by_width.items()):
            with self.subTest(width=width, face=path.name):
                count, digest = _read(path, mdi_fingerprint)
                self.assertEqual(count, MDI_ICON_COUNT)
                self.assertNotEqual(digest, REJECTED_PATCHER_MDI[width],
                                    "these icons were drawn by nerdfonts/patcher:4.25.0")
                self.assertEqual(digest, PINNED_PATCHER_MDI[width])


if __name__ == "__main__":
    unittest.main()
