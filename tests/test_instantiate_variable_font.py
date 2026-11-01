"""Tests for instantiate-variable-font.py.

Unit tests build small synthetic variable fonts with fontTools' FontBuilder
(an fvar with wght and wdth, a gvar that moves the outline, and the STAT
variants the tool has to tell apart), so they need none of the repository's
fonts. The tests at the end read the real Noto fonts when they are present
and skip cleanly when they are not; they only ever write into temporary
directories.
"""

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.woff2 import WOFF2FlavorData
from fontTools.varLib import instancer

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "instantiate-variable-font.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("instantiate_variable_font", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = load_tool()

WGHT_WDTH = [("wght", 100, 400, 900, "Weight"), ("wdth", 75, 100, 100, "Width")]

# (style name, wght, wdth)
UPRIGHT_INSTANCES = [
    ("Thin", 100, 100),
    ("Regular", 400, 100),
    ("Bold", 700, 100),
    ("Black", 900, 100),
    ("Condensed", 400, 75),
    ("Condensed Bold", 700, 75),
]

ITALIC_INSTANCES = [
    ("Thin Italic", 100, 100),
    ("Italic", 400, 100),
    ("Bold Italic", 700, 100),
    ("Condensed Bold Italic", 700, 75),
]

STAT_FULL = [
    {"tag": "wght", "name": "Weight", "values": [
        {"value": 100, "name": "Thin"},
        {"value": 400, "name": "Regular", "flags": 0x2},
        {"value": 700, "name": "Bold"},
        {"value": 900, "name": "Black"},
    ]},
    {"tag": "wdth", "name": "Width", "values": [
        {"value": 75, "name": "Condensed"},
        {"value": 100, "name": "Normal", "flags": 0x2},
    ]},
]
# design axes, but not one Axis Value (what NotoSansDisplay ships)
STAT_NO_VALUES = [{"tag": "wght", "name": "Weight"}, {"tag": "wdth", "name": "Width"}]
# values for wght only: STAT would name a Condensed Bold just "Bold"
STAT_WEIGHT_ONLY = [STAT_FULL[0], {"tag": "wdth", "name": "Width"}]


def _rectangle(width):
    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((100, 700))
    pen.lineTo((100 + width, 700))
    pen.lineTo((100 + width, 0))
    pen.closePath()
    return pen.glyph()


def build_font(path, *, family="Test Sans", ps_family="TestSans", default_style="Regular",
               instances=UPRIGHT_INSTANCES, stat=STAT_NO_VALUES, ps_names=None,
               italic=False, flavor=None, variable=True, axes=WGHT_WDTH, names=None,
               flavor_data=None):
    """Write a two-glyph font to `path`; variable (wght+wdth) unless told not.

    `instances` are (style, wght, wdth); `ps_names` maps a style to the
    postscriptNameID string its fvar instance should carry; `stat` is a
    FontBuilder.setupStat axes list, or None for no STAT table at all.
    `axes` replaces the fvar axes (still wght and wdth: the gvar uses them);
    `names` overrides or adds FontBuilder name strings; `flavor_data` is
    stored with a WOFF/WOFF2 `flavor`.
    """
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({0x41: "A"})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": _rectangle(400)})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (600, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    ps_default = f"{ps_family}-{default_style.replace(' ', '')}"
    fb.setupNameTable({
        "familyName": family,
        "styleName": default_style,
        "uniqueFontIdentifier": f"1.000;TEST;{ps_default}",
        "fullName": f"{family} {default_style}",
        "psName": ps_default,
        "version": "Version 1.000",
        **(names or {}),
    })
    fb.setupOS2(usWeightClass=400, usWidthClass=5, achVendID="TEST",
                fsSelection=0x01 if italic else 0x40)
    fb.setupPost()
    fb.updateHead(macStyle=0b10 if italic else 0)
    if variable:
        fvar_instances = []
        for style, wght, wdth in instances:
            entry = {"location": {"wght": wght, "wdth": wdth}, "stylename": style}
            if ps_names and style in ps_names:
                entry["postscriptfontname"] = ps_names[style]
            fvar_instances.append(entry)
        fb.setupFvar(axes, fvar_instances)
        wider = [(0, 0), (0, 0), (200, 0), (200, 0), (0, 0), (200, 0), (0, 0), (0, 0)]
        narrower = [(0, 0), (0, 0), (-150, 0), (-150, 0), (0, 0), (-150, 0), (0, 0), (0, 0)]
        fb.setupGvar({".notdef": [], "A": [
            TupleVariation({"wght": (0, 1.0, 1.0)}, wider),
            TupleVariation({"wdth": (-1.0, -1.0, 0)}, narrower),
        ]})
        if stat is not None:
            fb.setupStat(stat)
    if flavor:
        fb.font.flavor = flavor
        fb.font.flavorData = flavor_data
    fb.save(str(path))
    return path


def build_one_axis_font(path, tag, minimum, default, maximum):
    """A variable font with the single axis `tag` and one named instance,
    'Regular', at its default (for ranges that are not whole numbers)."""
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({0x41: "A"})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": _rectangle(400)})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (600, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Frac", "styleName": "Regular", "psName": "Frac-Regular"})
    fb.setupOS2()
    fb.setupPost()
    fb.setupFvar([(tag, minimum, default, maximum, "Axis")],
                 [{"location": {tag: default}, "stylename": "Regular"}])
    wider = [(0, 0), (0, 0), (200, 0), (200, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
    fb.setupGvar({".notdef": [], "A": [TupleVariation({tag: (0, 1.0, 1.0)}, wider)]})
    fb.save(str(path))
    return path


def run_tool(*argv):
    """(exit status, stdout, stderr) of the tool's main()."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            status = tool.main([str(a) for a in argv])
        except SystemExit as exc:  # argparse: --help, usage errors
            status = exc.code
    return status, out.getvalue(), err.getvalue()


def names_of(path):
    """{nameID: Windows-English string} for the style records of a font file."""
    name = TTFont(path)["name"]
    return {i: (name.getName(i, 3, 1, 0x409).toUnicode() if name.getName(i, 3, 1, 0x409) else None)
            for i in (1, 2, 3, 4, 6, 16, 17)}


def table_offset(data, tag):
    """(offset, length) of table `tag` in the sfnt bytes `data`."""
    count = int.from_bytes(data[4:6], "big")
    for index in range(count):
        entry = 12 + 16 * index
        if data[entry:entry + 4] == tag:
            return (int.from_bytes(data[entry + 8:entry + 12], "big"),
                    int.from_bytes(data[entry + 12:entry + 16], "big"))
    raise KeyError(tag)


class ToolTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.out = self.tmp / "out"

    def font(self, name="TestSans-VF.ttf", **kwargs):
        return build_font(self.tmp / name, **kwargs)

    def assertNothingWritten(self):
        self.assertFalse(self.out.exists(), "the output directory should not exist")

    def output_names(self):
        return sorted(p.name for p in self.out.iterdir())


class HelpAndListTests(ToolTestCase):
    def test_help_shows_usage_but_not_the_maintainer_notes(self):
        status, out, _ = run_tool("--help")
        self.assertEqual(status, 0)
        self.assertIn("--weights", out)
        self.assertIn("How an instance is named", out)
        self.assertNotIn("Safety notes", out)

    def test_list_reports_axes_stat_state_instances_and_their_files(self):
        font = self.font()
        status, out, _ = run_tool(font, "--list")
        self.assertEqual(status, 0)
        self.assertIn("family: Test Sans", out)
        self.assertIn("wght  100 .. 900   (default 400)", out)
        self.assertIn("wdth  75 .. 100   (default 100)", out)
        self.assertIn("STAT: 0 axis value(s) -- cannot name instances", out)
        self.assertRegex(
            out, r"Condensed Bold\s+wght=700  wdth=75\s+-> TestSans-CondensedBold\.ttf  \(fvar\)")
        self.assertEqual(out.count("(fvar)"), len(UPRIGHT_INSTANCES))
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), [font.name])

    def test_list_shows_stat_naming_when_stat_can_name(self):
        status, out, _ = run_tool(self.font(stat=STAT_FULL), "--list")
        self.assertEqual(status, 0)
        self.assertIn("STAT: 6 axis value(s)\n", out)
        self.assertRegex(out, r"Condensed Bold\s+.*-> TestSans-BoldCondensed\.ttf  \(stat\)")
        self.assertEqual(out.count("(stat)"), len(UPRIGHT_INSTANCES))

    def test_list_flags_instances_that_share_a_file(self):
        font = self.font(instances=[("Bold", 700, 100), ("Bold", 700, 75)])
        status, out, _ = run_tool(font, "--list")
        self.assertEqual(status, 0)
        self.assertIn("2 named instances share a file name", out)

    def test_list_escapes_control_characters_from_the_font(self):
        font = self.font(instances=[("Evil\x1b[31mRed", 400, 100)])
        status, out, _ = run_tool(font, "--list")
        self.assertEqual(status, 0)
        self.assertNotIn("\x1b", out)
        self.assertIn("Evil\\x1b[31mRed", out)


class AxisValueTests(ToolTestCase):
    """Defect 1: out-of-range values used to be clamped without a word."""

    def test_weight_above_the_axis_is_refused_before_writing(self):
        status, _, err = run_tool(self.font(), "--weights", "400", "950", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("wght=950 is outside the font's wght axis range 100 .. 900", err)
        self.assertIn("nothing was written", err)
        self.assertNothingWritten()

    def test_width_below_the_axis_is_refused(self):
        status, _, err = run_tool(self.font(), "--widths", "50", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("wdth=50 is outside the font's wdth axis range 75 .. 100", err)
        self.assertNothingWritten()

    def test_axis_option_out_of_range_is_refused(self):
        status, _, err = run_tool(self.font(), "--axis", "wght=99.5", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("wght=99.5 is outside", err)
        self.assertNothingWritten()

    def test_non_finite_values_are_refused(self):
        # (argparse reads a bare "-inf" as an option; --axis takes it)
        for option in (["--weights", "nan"], ["--weights", "inf"], ["--axis", "wght=-inf"]):
            with self.subTest(option=option):
                status, _, err = run_tool(self.font(), *option, "--out", self.out)
                self.assertEqual(status, 1)
                self.assertIn("is not a finite number", err)
                self.assertNothingWritten()

    def test_a_huge_value_is_refused_not_overflowed(self):
        # 1e308 * 65536 is inf in floating point: the 16.16 comparison must
        # never be reached for it
        status, _, err = run_tool(self.font(), "--weights", "1e308", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("wght=1e+308 is outside the font's wght axis range 100 .. 900", err)
        self.assertNothingWritten()

    def test_the_ends_of_the_axis_are_accepted(self):
        status, _, err = run_tool(self.font(), "--weights", "100", "900", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Black.ttf", "TestSans-Thin.ttf"])

    def test_ends_that_are_not_whole_numbers_are_accepted(self):
        # fvar stores 0.1 as 6554/65536 = 0.100006...; comparing floats refused
        # the axis's own ends, including the value --list printed for them
        font = build_one_axis_font(self.tmp / "Frac.ttf", "CASL", 0.1, 0.5, 0.9)
        status, out, _ = run_tool(font, "--list")
        self.assertEqual(status, 0)
        self.assertIn("CASL  0.1 .. 0.9   (default 0.5)", out)
        for value in ("0.1", "0.100006", "0.9", "0.899994"):
            with self.subTest(value=value):
                status, _, err = run_tool(font, "--axis", f"CASL={value}", "--out", self.out)
                self.assertEqual(status, 0, err)

    def test_a_value_just_outside_a_fractional_end_is_refused_and_says_so(self):
        font = build_one_axis_font(self.tmp / "Frac.ttf", "CASL", 0.1, 0.5, 0.9)
        status, _, err = run_tool(font, "--axis", "CASL=0.09999", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("CASL=0.09999 is outside the font's CASL axis range 0.1 .. 0.9 "
                      "(default 0.5)", err)
        self.assertNothingWritten()

    def test_values_within_fvar_precision_of_an_end_are_that_end(self):
        status, _, err = run_tool(self.font(), "--weights", "99.9999999", "900.0000001",
                                  "--out", self.out)
        self.assertEqual(status, 0, err)
        # at fvar's precision they are the ends: the Thin and Black named instances
        self.assertEqual(self.output_names(), ["TestSans-Black.ttf", "TestSans-Thin.ttf"])
        self.assertEqual(TTFont(self.out / "TestSans-Thin.ttf")["OS/2"].usWeightClass, 100)

    def test_a_refused_value_is_never_printed_as_an_end_of_the_axis(self):
        # ':g' printed 99.9999 as "100" next to the range "100 .. 900"
        for value, shown in (("99.9999", "99.9999"), ("900.0001", "900.0001"),
                             ("99.99", "99.99")):
            with self.subTest(value=value):
                status, _, err = run_tool(self.font(), "--weights", value, "--out", self.out)
                self.assertEqual(status, 1)
                self.assertIn(f"wght={shown} is outside the font's wght axis range 100 .. 900",
                              err)
                self.assertNothingWritten()

    def test_number_formatting(self):
        self.assertEqual(tool.fixed_text(6554 / 65536), "0.1")
        self.assertEqual(tool.fixed_text(58982 / 65536), "0.9")
        self.assertEqual(tool.fixed_text(400.0), "400")
        self.assertEqual(tool.fixed_text(62.5), "62.5")
        self.assertEqual(tool.fixed_text(-0.0), "0")
        self.assertEqual(tool.fixed_text(-1.5), "-1.5")
        self.assertEqual(tool.number_text(950.0), "950")
        self.assertEqual(tool.number_text(99.9999999), "99.9999999")

    def test_repeated_weights_and_widths_add_up(self):
        # argparse used to keep only the last --weights, dropping 400 unannounced
        font = self.font()
        status, _, err = run_tool(font, "--weights", "400", "--weights", "700",
                                  "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf", "TestSans-Regular.ttf"])
        out = self.tmp / "widths"
        status, _, err = run_tool(font, "--widths", "75", "--widths", "100",
                                  "--weights", "700", "--out", out)
        self.assertEqual(status, 0, err)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["TestSans-Bold.ttf", "TestSans-CondensedBold.ttf"])

    def test_a_value_repeated_across_options_is_still_a_collision(self):
        status, _, err = run_tool(self.font(), "--weights", "700", "--weights", "700",
                                  "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("same file 'TestSans-Bold.ttf'", err)
        self.assertNothingWritten()

    def test_named_instance_outside_its_axis_is_refused(self):
        # a malformed font: fvar says wght 100..900, an instance sits at 1000
        font = self.font(instances=[("Regular", 400, 100), ("Ultra", 1000, 100)])
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("named instance 'Ultra'", err)
        self.assertIn("wght=1000 is outside", err)
        self.assertNothingWritten()

    def test_unknown_axis_is_refused(self):
        status, _, err = run_tool(self.font(), "--axis", "opsz=14", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("font has no axis opsz (it has: wght, wdth)", err)
        self.assertNothingWritten()

    def test_an_axis_given_twice_is_refused(self):
        font = self.font()
        status, _, err = run_tool(font, "--axis", "wdth=75", "--axis", "wdth=100",
                                  "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("--axis wdth is given more than once", err)
        status, _, err = run_tool(font, "--weights", "700", "--axis", "wght=400",
                                  "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("wght is given by both --weights and --axis", err)
        self.assertNothingWritten()

    def test_malformed_axis_option_is_a_usage_error(self):
        status, _, err = run_tool(self.font(), "--axis", "wght")
        self.assertEqual(status, 2)
        self.assertIn("expected TAG=VALUE", err)

    def test_static_font_is_refused(self):
        font = self.font("Static.ttf", variable=False)
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("already STATIC", err)
        self.assertNothingWritten()

    def test_missing_input_is_refused(self):
        status, _, err = run_tool(self.tmp / "nope.ttf")
        self.assertEqual(status, 1)
        self.assertIn("no such file", err)

    def test_font_without_named_instances_needs_axis_options(self):
        status, _, err = run_tool(self.font(instances=[]), "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("declares no named instances", err)
        self.assertNothingWritten()


class NamingTests(ToolTestCase):
    """Defect 2: a STAT without Axis Values used to leave every instance
    named 'Regular' inside, with coordinate file names."""

    EXPECTED = {
        # file stem: (ID 1, ID 2, ID 4, ID 16, ID 17)
        "TestSans-Thin": ("Test Sans Thin", "Regular", "Test Sans Thin", "Test Sans", "Thin"),
        "TestSans-Regular": ("Test Sans", "Regular", "Test Sans Regular", None, None),
        "TestSans-Bold": ("Test Sans", "Bold", "Test Sans Bold", None, None),
        "TestSans-Black": ("Test Sans Black", "Regular", "Test Sans Black", "Test Sans", "Black"),
        "TestSans-Condensed": ("Test Sans Condensed", "Regular", "Test Sans Condensed",
                               "Test Sans", "Condensed"),
        "TestSans-CondensedBold": ("Test Sans Condensed", "Bold", "Test Sans Condensed Bold",
                                   "Test Sans", "Condensed Bold"),
    }

    def check_fvar_named(self, font):
        status, out, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), sorted(f"{s}.ttf" for s in self.EXPECTED))
        faces = set()
        for stem, (family, style, full, typo_family, typo_style) in self.EXPECTED.items():
            with self.subTest(stem=stem):
                names = names_of(self.out / f"{stem}.ttf")
                self.assertEqual(names[1], family)
                self.assertEqual(names[2], style)
                self.assertEqual(names[4], full)
                self.assertEqual(names[6], stem)
                self.assertEqual(names[3], f"1.000;TEST;{stem}")
                self.assertEqual(names[16], typo_family)
                self.assertEqual(names[17], typo_style)
                faces.add((names[16] or names[1], names[17] or names[2]))
        self.assertEqual(len(faces), len(self.EXPECTED), "every file must be a distinct face")
        self.assertIn(f"{len(self.EXPECTED)} instance(s) were named from the font's own "
                      "named instances", out)
        self.assertNotIn("spell out the coordinates", out)

    def test_stat_without_axis_values_names_instances_from_fvar(self):
        self.check_fvar_named(self.font(stat=STAT_NO_VALUES))

    def test_no_stat_table_names_instances_from_fvar(self):
        self.check_fvar_named(self.font(stat=None))

    def test_mac_name_records_are_renamed_too(self):
        run_tool(self.font(), "--out", self.out)
        name = TTFont(self.out / "TestSans-CondensedBold.ttf")["name"]
        self.assertTrue(any(r.platformID == 1 for r in name.names), "the fixture has Mac names")
        self.assertEqual(name.getName(1, 1, 0, 0).toUnicode(), "Test Sans Condensed")
        self.assertEqual(name.getName(2, 1, 0, 0).toUnicode(), "Bold")
        self.assertEqual(name.getName(6, 1, 0, 0).toUnicode(), "TestSans-CondensedBold")
        self.assertEqual(name.getName(17, 1, 0, 0).toUnicode(), "Condensed Bold")

    def test_the_instance_postscript_name_is_used_when_present(self):
        font = self.font(ps_names={"Black": "TestSansPS-Heavy", "Bold": "TestSansPS-Bold"})
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertIn("TestSansPS-Heavy.ttf", self.output_names())
        self.assertIn("TestSansPS-Bold.ttf", self.output_names())
        names = names_of(self.out / "TestSansPS-Heavy.ttf")
        self.assertEqual(names[6], "TestSansPS-Heavy")
        self.assertEqual(names[17], "Black")
        self.assertEqual(names[3], "1.000;TEST;TestSansPS-Heavy")

    def test_axis_options_at_a_named_instance_use_its_names(self):
        status, out, err = run_tool(self.font(), "--weights", "700", "--widths", "75",
                                    "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-CondensedBold.ttf"])
        self.assertEqual(names_of(self.out / "TestSans-CondensedBold.ttf")[17], "Condensed Bold")

    def test_unspecified_axes_stay_at_their_default_when_matching(self):
        # --weights 700 alone -> wdth stays 100 -> the "Bold" named instance
        status, _, err = run_tool(self.font(), "--weights", "700", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"])

    def test_a_location_nothing_names_falls_back_to_coordinates(self):
        status, out, err = run_tool(self.font(), "--weights", "550", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-wght550.ttf"])
        self.assertIn("spell out the coordinates", out)
        names = names_of(self.out / "TestSans-wght550.ttf")
        self.assertEqual(names[2], "Regular")  # still the default's: that is what the note says
        self.assertEqual(TTFont(self.out / "TestSans-wght550.ttf")["OS/2"].usWeightClass, 550)

    def test_stat_names_win_when_stat_can_name(self):
        status, out, err = run_tool(self.font(stat=STAT_FULL), "--weights", "700",
                                    "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"])
        names = names_of(self.out / "TestSans-Bold.ttf")
        self.assertEqual((names[1], names[2], names[6]), ("Test Sans", "Bold", "TestSans-Bold"))
        self.assertNotIn("named from the font's own named instances", out)

    def test_stat_names_match_the_fonttools_renamer(self):
        # the plan copies the records fontTools' renamer produces on a scratch
        # copy; the result must equal instancing with updateFontNames=True
        font = self.font(stat=STAT_FULL)
        status, _, err = run_tool(font, "--weights", "700", "--widths", "75", "--out", self.out)
        self.assertEqual(status, 0, err)
        reference = instancer.instantiateVariableFont(
            TTFont(font), {"wght": 700, "wdth": 75}, updateFontNames=True)
        ours = TTFont(self.out / "TestSans-BoldCondensed.ttf")

        def records(f):
            return sorted((r.nameID, r.platformID, r.platEncID, r.langID, r.toUnicode())
                          for r in f["name"].names)

        self.assertEqual(records(ours), records(reference))
        self.assertEqual(ours["OS/2"].fsSelection, reference["OS/2"].fsSelection)
        self.assertEqual(ours["head"].macStyle, reference["head"].macStyle)

    def test_stat_with_an_axis_it_cannot_name_is_not_trusted_there(self):
        # STAT has wght values only: fontTools would call Condensed Bold just
        # "Bold" and collide with the real Bold; fvar names it instead.
        status, _, err = run_tool(self.font(stat=STAT_WEIGHT_ONLY), "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertIn("TestSans-CondensedBold.ttf", self.output_names())
        self.assertIn("TestSans-Bold.ttf", self.output_names())
        self.assertEqual(names_of(self.out / "TestSans-Bold.ttf")[1], "Test Sans")

    def test_a_thin_default_font_loses_its_typographic_names_on_ribbi_instances(self):
        # Like Noto Sans JP/KR/SC/Hebrew: the default is Thin, so the source
        # carries ID 1 "Test Sans Thin", ID 16 "Test Sans" and ID 17 "Thin".
        # A Bold instance that kept IDs 16/17 would still be called "Thin".
        thin_default = {"familyName": "Test Sans Thin", "styleName": "Regular",
                        "fullName": "Test Sans Thin", "psName": "TestSans-Thin",
                        "uniqueFontIdentifier": "1.000;TEST;TestSans-Thin",
                        "typographicFamily": "Test Sans", "typographicSubfamily": "Thin"}
        font = self.font(axes=[("wght", 100, 100, 900, "Weight"), ("wdth", 75, 100, 100, "Width")],
                         names=thin_default)
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 0, err)
        expected = {
            # stem: (ID 1, ID 2, ID 16, ID 17)
            "TestSans-Regular": ("Test Sans", "Regular", None, None),
            "TestSans-Bold": ("Test Sans", "Bold", None, None),
            "TestSans-Thin": ("Test Sans Thin", "Regular", "Test Sans", "Thin"),
            "TestSans-CondensedBold": ("Test Sans Condensed", "Bold", "Test Sans",
                                       "Condensed Bold"),
        }
        for stem, (family, style, typo_family, typo_style) in expected.items():
            with self.subTest(stem=stem):
                path = self.out / f"{stem}.ttf"
                names = names_of(path)
                self.assertEqual((names[1], names[2], names[16], names[17]),
                                 (family, style, typo_family, typo_style))
                self.assertEqual(names[3], f"1.000;TEST;{stem}")
                if typo_family is None:  # on no platform at all, Mac included
                    records = TTFont(path)["name"].names
                    self.assertFalse([r for r in records if r.nameID in (16, 17)])

    def test_a_style_name_mac_roman_cannot_spell_is_settled_while_planning(self):
        # FontBuilder writes Mac Roman records for IDs 1-6 but none for
        # "Čierny", which Mac Roman cannot encode. Filling the Mac records with
        # the English string used to fail at save time, after the first two
        # files were written.
        font = self.font(instances=[("Regular", 400, 100), ("Bold", 700, 100),
                                    ("Čierny", 900, 100)])
        status, out, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertNotIn("failed to encode", err)
        self.assertEqual(len(self.output_names()), 3)
        black = self.out / "TestSans-ierny.ttf"  # fontTools' PostScript alphabet
        names = names_of(black)
        self.assertEqual((names[1], names[2], names[17]),
                         ("Test Sans Čierny", "Regular", "Čierny"))
        mac = [r for r in TTFont(black)["name"].names
               if r.platformID == 1 and r.nameID in tool.STYLE_NAME_IDS]
        self.assertEqual(mac, [], "the Mac records must not keep naming the default")
        # a platform that can spell the names keeps its records
        bold = TTFont(self.out / "TestSans-Bold.ttf")["name"]
        self.assertEqual(bold.getName(2, 1, 0, 0).toUnicode(), "Bold")

    def test_names_that_cannot_be_encoded_are_refused_before_writing(self):
        # whatever produces the names, the planned name table is compiled
        # while planning: a record that cannot be encoded stops the run there
        real = tool.rename_from_instance

        def unencodable(font, inst):
            ps = real(font, inst)
            if inst.coordinates["wght"] == 900:
                font["name"].setName("Čierny", 2, 1, 0, 0)  # Mac Roman lacks Č
            return ps

        with mock.patch.object(tool, "rename_from_instance", unencodable):
            status, _, err = run_tool(self.font(), "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("named instance 'Black'", err)
        self.assertIn("its name table cannot be written", err)
        self.assertIn("nothing was written", err)
        self.assertNothingWritten()

    def test_a_failed_stat_rename_leaves_no_half_written_names(self):
        # fontTools' renamer may change some records before it gives up; the
        # next rule must start from the font's own names, not from those
        def half_then_fail(font, location):
            for triple in {(r.platformID, r.platEncID, r.langID) for r in font["name"].names}:
                font["name"].setName("Garbage", 1, *triple)
            raise ValueError("Cannot find Axis Values")

        with mock.patch.object(tool.instancer_names, "updateNameTable", half_then_fail):
            status, out, err = run_tool(self.font(stat=STAT_FULL), "--weights", "700",
                                        "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"])
        self.assertEqual(names_of(self.out / "TestSans-Bold.ttf")[1], "Test Sans")
        self.assertIn("named from the font's own named instances", out)

    def test_a_stat_renamer_crash_falls_back_to_fvar(self):
        # A STAT axis value whose name has a Windows record but no Mac one:
        # fontTools' renamer raises AttributeError ('NoneType' object has no
        # attribute 'toUnicode') on the Mac platform. That is not a refusal of
        # the font, just STAT being unable to name it: the next rule does.
        source = TTFont(self.font(stat=STAT_FULL))
        name = source["name"]
        bold = next(v for v in source["STAT"].table.AxisValueArray.AxisValue
                    if name.getDebugName(v.ValueNameID) == "Bold")
        name.removeNames(nameID=bold.ValueNameID, platformID=1)
        path = self.tmp / "NoMacBold.ttf"
        source.save(path)
        status, out, err = run_tool(path, "--weights", "700", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"])
        self.assertIn("named from the font's own named instances", out)

    def test_a_value_a_hair_off_an_end_is_named_by_stat_as_that_end(self):
        # 99.9999999 is wght 100 in fvar's precision: accepted, and named by
        # STAT's "Thin" axis value (fontTools clamps it onto 100 first)
        status, out, err = run_tool(self.font(stat=STAT_FULL), "--weights", "99.9999999",
                                    "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Thin.ttf"])
        self.assertNotIn("named from the font's own named instances", out)

    def test_italic_family_follows_the_ribbi_convention(self):
        font = self.font("TestSans-Italic-VF.ttf", default_style="Italic", italic=True,
                         instances=ITALIC_INSTANCES)
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 0, err)
        expected = {
            "TestSans-ThinItalic": ("Test Sans Thin", "Italic", "Thin Italic"),
            "TestSans-Italic": ("Test Sans", "Italic", None),
            "TestSans-BoldItalic": ("Test Sans", "Bold Italic", None),
            "TestSans-CondensedBoldItalic": ("Test Sans Condensed", "Bold Italic",
                                             "Condensed Bold Italic"),
        }
        self.assertEqual(self.output_names(), sorted(f"{s}.ttf" for s in expected))
        for stem, (family, style, typo_style) in expected.items():
            with self.subTest(stem=stem):
                names = names_of(self.out / f"{stem}.ttf")
                self.assertEqual((names[1], names[2], names[17]), (family, style, typo_style))


class StyleBitsTests(ToolTestCase):
    """OS/2 and head must agree with the names after instancing."""

    def bits(self, path):
        font = TTFont(path)
        os2 = font["OS/2"]
        return (os2.usWeightClass, os2.usWidthClass, os2.fsSelection & 0b1100001,
                font["head"].macStyle & 0b11)

    def test_upright_instances(self):
        run_tool(self.font(), "--out", self.out)
        # (weight class, width class, fsSelection italic|bold|regular bits, macStyle)
        self.assertEqual(self.bits(self.out / "TestSans-Regular.ttf"), (400, 5, 0x40, 0))
        self.assertEqual(self.bits(self.out / "TestSans-Bold.ttf"), (700, 5, 0x20, 0b01))
        self.assertEqual(self.bits(self.out / "TestSans-Black.ttf"), (900, 5, 0x40, 0))
        self.assertEqual(self.bits(self.out / "TestSans-Thin.ttf"), (100, 5, 0x40, 0))
        self.assertEqual(self.bits(self.out / "TestSans-CondensedBold.ttf"), (700, 3, 0x20, 0b01))

    def test_italic_instances(self):
        font = self.font("TestSans-Italic-VF.ttf", default_style="Italic", italic=True,
                         instances=ITALIC_INSTANCES)
        run_tool(font, "--out", self.out)
        self.assertEqual(self.bits(self.out / "TestSans-ThinItalic.ttf"), (100, 5, 0x01, 0b10))
        self.assertEqual(self.bits(self.out / "TestSans-BoldItalic.ttf"), (700, 5, 0x21, 0b11))
        self.assertEqual(self.bits(self.out / "TestSans-CondensedBoldItalic.ttf"),
                         (700, 3, 0x21, 0b11))

    def test_stat_named_instances(self):
        run_tool(self.font(stat=STAT_FULL), "--out", self.out)
        self.assertEqual(self.bits(self.out / "TestSans-Bold.ttf"), (700, 5, 0x20, 0b01))
        self.assertEqual(self.bits(self.out / "TestSans-Regular.ttf"), (400, 5, 0x40, 0))

    def test_output_is_static_and_keeps_a_reduced_stat(self):
        run_tool(self.font(stat=STAT_FULL), "--weights", "700", "--out", self.out)
        font = TTFont(self.out / "TestSans-Bold.ttf")
        for tag in ("fvar", "gvar", "avar", "HVAR", "MVAR"):
            self.assertNotIn(tag, font)
        self.assertIn("STAT", font)
        values = font["STAT"].table.AxisValueArray.AxisValue
        self.assertTrue(all(v.Value in (700, 100) for v in values))

    def test_regular_clears_stale_bold_and_italic_bits(self):
        font = TTFont(self.font())
        font["head"].macStyle = 0b11
        font["OS/2"].fsSelection = 0x21 | 0x80  # bold + italic + USE_TYPO_METRICS
        tool.fix_style_bits(font)  # ID 2 is "Regular"
        self.assertEqual(font["head"].macStyle, 0)
        self.assertEqual(font["OS/2"].fsSelection, 0x40 | 0x80)


class CollisionTests(ToolTestCase):
    """Defect 3: two targets writing one file used to overwrite silently."""

    def test_named_instances_with_the_same_name_are_refused(self):
        font = self.font(instances=[("Bold", 700, 100), ("Bold", 700, 75)])
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("two targets would write the same file 'TestSans-Bold.ttf'", err)
        self.assertIn("nothing was written", err)
        self.assertNothingWritten()

    def test_the_same_value_twice_is_refused(self):
        status, _, err = run_tool(self.font(), "--weights", "400", "400", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("same file 'TestSans-Regular.ttf'", err)
        self.assertNothingWritten()

    def test_coordinate_names_that_collide_are_refused(self):
        # :g formatting keeps six significant digits
        status, _, err = run_tool(self.font(), "--weights", "550.0001", "550.0002",
                                  "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("same file", err)
        self.assertNothingWritten()

    def test_names_differing_only_in_case_are_refused(self):
        font = self.font(instances=[("Bold", 700, 100), ("Heavy", 900, 100)],
                         ps_names={"Bold": "TestSans-Bold", "Heavy": "TestSans-BOLD"})
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("same file 'TestSans-BOLD.ttf'", err)
        self.assertNothingWritten()

    def test_the_input_is_never_overwritten(self):
        for input_name in ("TestSans-Bold.ttf", "testsans-bold.ttf"):
            with self.subTest(input_name=input_name):
                font = self.font(input_name)
                before = font.read_bytes()
                status, _, err = run_tool(font, "--weights", "700", "--out", self.tmp)
                self.assertEqual(status, 1)
                self.assertIn("would overwrite the input", err)
                self.assertEqual(font.read_bytes(), before)
                font.unlink()

    def test_a_hard_link_to_the_input_is_not_written_over(self):
        source = self.tmp / "in"
        source.mkdir()
        font = self.font("in/TestSans-VF.ttf")
        self.out.mkdir()
        try:
            os.link(font, self.out / "TestSans-Bold.ttf")
        except (OSError, AttributeError, NotImplementedError):
            self.skipTest("hard links are not available here")
        before = font.read_bytes()
        status, _, err = run_tool(font, "--weights", "700", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("would overwrite the input", err)
        self.assertEqual(font.read_bytes(), before)
        self.assertTrue(os.path.samefile(font, self.out / "TestSans-Bold.ttf"))

    def test_out_must_be_a_directory(self):
        not_a_dir = self.tmp / "file"
        not_a_dir.write_bytes(b"x")
        status, _, err = run_tool(self.font(), "--weights", "700", "--out", not_a_dir)
        self.assertEqual(status, 1)
        self.assertIn("is not a directory", err)

    def test_out_below_a_file_is_an_error_not_a_traceback(self):
        not_a_dir = self.tmp / "file"
        not_a_dir.write_bytes(b"x")
        status, _, err = run_tool(self.font(), "--weights", "700", "--out", not_a_dir / "sub")
        self.assertEqual(status, 1)
        self.assertIn("cannot create the output directory", err)
        self.assertIn("nothing was written", err)
        self.assertEqual(not_a_dir.read_bytes(), b"x")

    def test_an_output_path_that_is_a_directory_is_refused_before_writing(self):
        # found only at os.replace, it used to stop the run after three files
        (self.out / "TestSans-Bold.woff2").mkdir(parents=True)
        status, _, err = run_tool(self.font(), "--weights", "400", "700", "--woff2",
                                  "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("'TestSans-Bold.woff2' already exists", err)
        self.assertIn("is not a regular file", err)
        self.assertIn("nothing was written", err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.woff2"])

    def test_a_rerun_replaces_and_says_so(self):
        font = self.font()
        self.assertEqual(run_tool(font, "--weights", "700", "--out", self.out)[0], 0)
        status, out, _ = run_tool(font, "--weights", "700", "--out", self.out)
        self.assertEqual(status, 0)
        self.assertIn("(replaced)", out)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"])


class FormatTests(ToolTestCase):
    """Defect 4: a .woff2 input with --woff2 wrote the same path twice."""

    def test_ttf_input_with_woff2_writes_one_of_each(self):
        status, out, err = run_tool(self.font(), "--weights", "700", "--woff2", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf", "TestSans-Bold.woff2"])
        self.assertIsNone(TTFont(self.out / "TestSans-Bold.ttf").flavor)
        self.assertEqual(TTFont(self.out / "TestSans-Bold.woff2").flavor, "woff2")
        self.assertIn("KB woff2", out)

    def test_woff2_input_is_written_once_per_instance_as_woff2(self):
        font = self.font("TestSans-VF.woff2", flavor="woff2")
        before = font.read_bytes()
        status, out, err = run_tool(font, "--woff2", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertIn("already WOFF2", out)
        self.assertEqual(self.output_names(),
                         sorted(f"{stem}.woff2" for stem in NamingTests.EXPECTED))
        for path in self.out.iterdir():
            self.assertEqual(TTFont(path).flavor, "woff2")
        self.assertEqual(names_of(self.out / "TestSans-CondensedBold.woff2")[17], "Condensed Bold")
        self.assertEqual(font.read_bytes(), before)

    def test_woff2_input_beside_its_outputs_is_not_clobbered(self):
        font = self.font("TestSans-Regular.woff2", flavor="woff2")
        before = font.read_bytes()
        status, _, err = run_tool(font, "--woff2", "--out", self.tmp)
        self.assertEqual(status, 1)
        self.assertIn("would overwrite the input 'TestSans-Regular.woff2'", err)
        self.assertEqual(font.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["TestSans-Regular.woff2"])

    def test_woff2_metadata_and_private_data_are_kept(self):
        flavor_data = WOFF2FlavorData()
        flavor_data.privData = b"private bytes"
        flavor_data.metaData = b'<?xml version="1.0"?><metadata version="1.0"/>'
        font = self.font("TestSans-VF.woff2", flavor="woff2", flavor_data=flavor_data)
        status, _, err = run_tool(font, "--weights", "700", "--out", self.out)
        self.assertEqual(status, 0, err)
        kept = TTFont(self.out / "TestSans-Bold.woff2").flavorData
        self.assertEqual(kept.privData, b"private bytes")
        self.assertEqual(kept.metaData, flavor_data.metaData)

    def test_suffix_follows_the_contents_not_the_input_name(self):
        font = self.font("Mislabelled.otf")  # TrueType outlines inside
        status, _, err = run_tool(font, "--weights", "700", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"])

    def test_brotli_missing_is_refused_before_writing(self):
        with mock.patch.object(tool.woff2_support, "haveBrotli", False):
            status, _, err = run_tool(self.font(), "--weights", "700", "--woff2",
                                      "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("brotli not found", err)
        self.assertNothingWritten()


class WriteSafetyTests(ToolTestCase):
    def test_no_temporary_files_are_left_behind(self):
        run_tool(self.font(), "--woff2", "--out", self.out)
        self.assertFalse([p for p in self.out.iterdir() if p.name.startswith(".")])

    def test_a_failed_save_leaves_the_previous_file_and_no_temporary(self):
        target = self.tmp / "Kept.ttf"
        target.write_bytes(b"previous")

        class Exploding:
            def save(self, handle):
                handle.write(b"partial")
                raise RuntimeError("disk on fire")

        with self.assertRaises(RuntimeError):
            tool.write_atomically(Exploding(), target)
        self.assertEqual(target.read_bytes(), b"previous")
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["Kept.ttf"])

    def test_a_failed_save_of_a_new_file_leaves_nothing(self):
        class Exploding:
            def save(self, handle):
                raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            tool.write_atomically(Exploding(), self.tmp / "New.ttf")
        self.assertEqual(list(self.tmp.iterdir()), [])

    def test_a_failure_while_writing_counts_every_file_completed(self):
        # the failing target's own .ttf is complete and must be counted
        font = self.font()
        real = tool.write_atomically
        calls = []

        def fourth_fails(font, path):
            calls.append(path)
            if len(calls) == 4:
                raise RuntimeError("boom")
            return real(font, path)

        with mock.patch.object(tool, "write_atomically", fourth_fails):
            status, _, err = run_tool(font, "--weights", "400", "700", "--woff2",
                                      "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("failed to write wght=700", err)
        self.assertIn("boom", err)
        self.assertIn("3 file(s) written before the failure are complete, "
                      "among them TestSans-Bold.ttf", err)
        self.assertEqual(self.output_names(),
                         ["TestSans-Bold.ttf", "TestSans-Regular.ttf", "TestSans-Regular.woff2"])

    def test_a_run_whose_final_rename_fails_keeps_the_previous_file(self):
        # end to end: the tool must write through a temporary file and
        # os.replace, never into the output file itself
        self.out.mkdir()
        previous = self.out / "TestSans-Bold.ttf"
        previous.write_bytes(b"the previous run's font")
        with mock.patch.object(tool.os, "replace", side_effect=OSError("disk full")):
            status, _, err = run_tool(self.font(), "--weights", "700", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("failed to write", err)
        self.assertIn("0 file(s) written before the failure are complete", err)
        self.assertEqual(previous.read_bytes(), b"the previous run's font")
        self.assertEqual(self.output_names(), ["TestSans-Bold.ttf"], "no temporary file left")

    def test_the_temporary_file_is_created_exclusively(self):
        # a file already at the temporary name is neither written through nor
        # removed: it is someone else's
        path = self.tmp / "TestSans-Bold.ttf"
        planted = self.tmp / ".TestSans-Bold.ttf.feedfacecafebeef.tmp"
        planted.write_bytes(b"planted")
        with mock.patch.object(tool.secrets, "token_hex", return_value="feedfacecafebeef"):
            with self.assertRaises(FileExistsError):
                tool.write_atomically(TTFont(self.font()), path)
        self.assertEqual(planted.read_bytes(), b"planted")
        self.assertFalse(path.exists())

    def test_each_file_is_fsynced_before_it_is_renamed(self):
        events = []
        real_fsync, real_replace = os.fsync, os.replace

        def fsync(fd):
            events.append("fsync")
            return real_fsync(fd)

        def replace(src, dst):
            events.append("replace")
            return real_replace(src, dst)

        with mock.patch.object(tool.os, "fsync", fsync), \
                mock.patch.object(tool.os, "replace", replace):
            status, _, err = run_tool(self.font(), "--weights", "700", "--woff2",
                                      "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(events, ["fsync", "replace"] * 2)

    def test_written_files_get_ordinary_permissions(self):
        if os.name != "posix":
            self.skipTest("POSIX permission bits")
        run_tool(self.font(), "--weights", "700", "--out", self.out)
        umask = os.umask(0)
        os.umask(umask)
        mode = (self.out / "TestSans-Bold.ttf").stat().st_mode & 0o777
        self.assertEqual(mode, 0o666 & ~umask)


class MalformedInputTests(ToolTestCase):
    """A malformed font is an 'error: ...' (exit 1), never a traceback, and
    nothing is written. run_tool lets anything but SystemExit propagate, so
    a traceback would fail these tests with that exception."""

    def check_refused(self, font, *expected):
        for options in (["--list"], ["--out", self.out]):
            with self.subTest(options=options[0]):
                status, out, err = run_tool(font, *options)
                self.assertEqual(status, 1)
                self.assertTrue(err.startswith("error: "), err)
                for text in expected:
                    self.assertIn(text, err)
                self.assertNotIn("named instances:", out)
                self.assertNothingWritten()

    def test_a_garbage_fvar_table(self):
        font = self.font()
        data = bytearray(font.read_bytes())
        offset, length = table_offset(data, b"fvar")
        data[offset:offset + length] = b"\xff" * length
        font.write_bytes(bytes(data))
        self.check_refused(font, "cannot read 'TestSans-VF.ttf' as a font",
                           "unsupported 'fvar' version")

    def test_a_font_without_a_name_table(self):
        source = TTFont(self.font())
        del source["name"]
        path = self.tmp / "NoName.ttf"
        source.save(path)
        self.check_refused(path, "it has no name table")

    def test_a_truncated_font(self):
        font = self.font()
        data = font.read_bytes()
        font.write_bytes(data[:len(data) // 2])
        self.check_refused(font, "runs past the end of the file")

    def test_a_failure_past_the_checks_is_still_an_error_message(self):
        # stands for fontTools tripping over something the up-front checks
        # did not parse; the run stops before writing anything
        with mock.patch.object(tool, "stat_can_name", side_effect=RuntimeError("deep trouble")):
            status, _, err = run_tool(self.font(), "--out", self.out)
            self.assertEqual(status, 1)
            self.assertIn("cannot plan the instances of 'TestSans-VF.ttf': deep trouble", err)
            self.assertIn("nothing was written", err)
            self.assertNothingWritten()
            status, _, err = run_tool(self.font(), "--list")
            self.assertEqual(status, 1)
            self.assertIn("cannot list 'TestSans-VF.ttf': deep trouble", err)

    def test_an_error_without_text_is_named(self):
        self.assertEqual(tool.error_text(AssertionError()), "AssertionError")
        self.assertEqual(tool.error_text(ValueError("bad\x1b[0m")), "bad\\x1b[0m")


class OutputEncodingTests(ToolTestCase):
    def test_list_survives_a_console_that_cannot_encode_the_names(self):
        # Windows with output redirected: stdout is the locale code page
        # (cp1252 here), which has no 太字; the listing used to stop there
        # with a UnicodeEncodeError traceback
        font = self.font(instances=[("Regular", 400, 100), ("太字", 700, 100),
                                    ("Black", 900, 100)])
        raw_out, raw_err = io.BytesIO(), io.BytesIO()
        stdout = io.TextIOWrapper(raw_out, encoding="cp1252", errors="strict")
        stderr = io.TextIOWrapper(raw_err, encoding="cp1252", errors="strict")
        with mock.patch.object(sys, "stdout", stdout), mock.patch.object(sys, "stderr", stderr):
            status = tool.main([str(font), "--list"])
            stdout.flush()
            stderr.flush()
        out = raw_out.getvalue().decode("cp1252")
        self.assertEqual(status, 0, raw_err.getvalue())
        self.assertIn("\\u592a\\u5b57", out)
        self.assertIn("-> TestSans-Black.ttf  (fvar)", out)  # the line after it


class FileNameSafetyTests(ToolTestCase):
    def test_a_postscript_name_cannot_leave_the_output_directory(self):
        font = self.font(instances=[("Bold", 700, 100)], ps_names={"Bold": "../../escape"})
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["escape.ttf"])
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["TestSans-VF.ttf", "out"])

    def test_safe_stem(self):
        self.assertEqual(tool.safe_stem("NotoSans-Bold"), "NotoSans-Bold")
        self.assertEqual(tool.safe_stem("Family-wdth62.5-wght400"), "Family-wdth62.5-wght400")
        self.assertEqual(tool.safe_stem("../x"), "x")
        self.assertEqual(tool.safe_stem("a/b\\c:d"), "a_b_c_d")
        self.assertEqual(tool.safe_stem("-rf"), "rf")
        for bad in ("", "...", "CON", "nul.x", "com1", "x" * (tool.MAX_STEM + 1)):
            with self.subTest(bad=bad):
                with self.assertRaises(tool.ToolError):
                    tool.safe_stem(bad)

    def test_a_device_name_from_the_font_is_refused(self):
        font = self.font(instances=[("Bold", 700, 100)], ps_names={"Bold": "NUL"})
        status, _, err = run_tool(font, "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("Windows device name", err)
        self.assertNothingWritten()

    def test_coordinate_file_names_from_a_hostile_family_stay_inside(self):
        font = self.font(family="Evil/../Name")
        status, _, err = run_tool(font, "--weights", "550", "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["Evil_.._Name-wght550.ttf"])

    def test_axis_tags_from_the_font_are_escaped_when_printed(self):
        self.assertEqual(tool.format_location({"\x1b[2J": 1.0}), "\\x1b[2J=1")
        with self.assertRaises(tool.ToolError) as cm:
            tool.check_location({"\x1bab": (0, 0, 1)}, {"\x1bab": 2.0})
        self.assertNotIn("\x1b", str(cm.exception))

    def test_postscript_names_are_reduced_to_their_alphabet(self):
        self.assertEqual(tool.postscript_safe("Ab c(d)/e%f\x00"), "Abcdef")
        self.assertEqual(len(tool.postscript_safe("x" * 100)), tool.POSTSCRIPT_MAX)
        self.assertEqual(tool.derive_postscript("Noto Sans Display", "SemiCondensed Bold"),
                         "NotoSansDisplay-SemiCondensedBold")
        self.assertIsNone(tool.derive_postscript("日本語", "Bold"))


# ------------------------------------------------------------ the real fonts

NOTO = REPO / "noctua-noto"
DISPLAY = NOTO / "NotoSansDisplay-VariableFont_wdth,wght.ttf"
NOTO_SANS = NOTO / "NotoSans-VariableFont_wdth,wght.ttf"
HEBREW = NOTO / "NotoSansHebrew-VariableFont_wdth,wght.ttf"


@unittest.skipUnless(DISPLAY.is_file(), "the real NotoSansDisplay font is not present")
class RealDisplayTests(ToolTestCase):
    def test_list_plans_36_distinct_files_from_fvar(self):
        status, out, _ = run_tool(DISPLAY, "--list")
        self.assertEqual(status, 0)
        planned = [line.split("-> ", 1)[1].split()[0]
                   for line in out.splitlines() if "-> " in line]
        self.assertEqual(len(planned), 36)
        self.assertEqual(len({p.casefold() for p in planned}), 36)
        self.assertEqual(out.count("(fvar)"), 36)

    def test_one_instance_carries_its_own_names(self):
        status, _, err = run_tool(DISPLAY, "--weights", "700", "--widths", "87.5",
                                  "--out", self.out)
        self.assertEqual(status, 0, err)
        self.assertEqual(self.output_names(), ["NotoSansDisplay-SemiCondensedBold.ttf"])
        path = self.out / "NotoSansDisplay-SemiCondensedBold.ttf"
        names = names_of(path)
        self.assertEqual(names[1], "Noto Sans Display SemiCondensed")
        self.assertEqual(names[2], "Bold")
        self.assertEqual(names[16], "Noto Sans Display")
        self.assertEqual(names[17], "SemiCondensed Bold")
        font = TTFont(path)
        self.assertEqual((font["OS/2"].usWeightClass, font["OS/2"].usWidthClass), (700, 4))
        self.assertEqual(font["head"].macStyle & 0b11, 0b01)
        self.assertNotIn("fvar", font)


@unittest.skipUnless(NOTO_SANS.is_file(), "the real NotoSans font is not present")
class RealNotoSansTests(ToolTestCase):
    def test_out_of_range_weight_is_refused(self):
        status, _, err = run_tool(NOTO_SANS, "--weights", "950", "--out", self.out)
        self.assertEqual(status, 1)
        self.assertIn("wght=950 is outside the font's wght axis range 100 .. 900", err)
        self.assertNothingWritten()


@unittest.skipUnless(HEBREW.is_file(), "the real NotoSansHebrew font is not present")
class RealHebrewTests(ToolTestCase):
    def test_stat_names_every_named_instance(self):
        status, out, _ = run_tool(HEBREW, "--list")
        self.assertEqual(status, 0)
        self.assertIn("(default 100)", out)  # Thin is the default instance
        self.assertEqual(out.count("(stat)"), 9)
        self.assertIn("-> NotoSansHebrew-Regular.ttf  (stat)", out)


if __name__ == "__main__":
    unittest.main()
