"""Tests for rename-font-family.py.

Every font here is synthetic, built with fontTools' FontBuilder in a temporary
directory, so the suite needs none of the repository's fonts. The tests that
read a real font copy it out first and skip when it is absent.
"""

import contextlib
import importlib.util
import io
import os
import random
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, woff2
from fontTools.ttLib.sfnt import SFNTWriter
from fontTools.ttLib.tables.DefaultTable import DefaultTable

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "rename-font-family.py"
REAL_FONT = ROOT / "noctua-iosevka" / "TTF" / "NoctuaIosevka-Regular.ttf"
REAL_PAIR = ROOT / "noctua-noto" / "NotoMusic-Regular.ttf"


def load_tool():
    spec = importlib.util.spec_from_file_location("rename_font_family", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = load_tool()

FROM, TO = "Noctua Iosevka", "Noctua Iosevka Code"
# A fixed, old head.modified, so a recalculated timestamp cannot pass for it.
MODIFIED = 3_000_000_000
LEGAL = {
    0: "Copyright 2026 the Noctua Iosevka authors",
    7: "Noctua Iosevka is a trademark",
    13: "Noctua Iosevka is licensed under the SIL OFL",
    14: "https://example.org/noctua-iosevka/license",
}
POSIX_USER = os.name == "posix" and os.geteuid() != 0


def names_for(family, style="Regular"):
    compact = family.replace(" ", "")
    return {
        **LEGAL,
        1: family,
        2: style,
        3: f"1.000;NONE;{compact}-{style}",
        4: f"{family} {style}",
        5: "Version 1.000",
        6: f"{compact}-{style}",
        16: family,
        17: style,
    }


def build_font(path, names, *, flavor=None, cff=False, dsig=False):
    """Write a two-glyph font with the given name records; return its path."""
    fb = FontBuilder(1000, isTTF=not cff)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({0x41: "A"})
    if cff:
        def charstring(draw):
            pen = T2CharStringPen(600, None)
            draw(pen)
            return pen.getCharString()

        def square(pen):
            pen.moveTo((100, 0))
            pen.lineTo((100, 700))
            pen.lineTo((500, 700))
            pen.lineTo((500, 0))
            pen.closePath()

        fb.setupCFF("Synthetic-Regular", {"FullName": "Synthetic"},
                    {".notdef": charstring(lambda pen: None),
                     "A": charstring(square)}, {})
    else:
        pen = TTGlyphPen(None)
        pen.moveTo((100, 0))
        pen.lineTo((100, 700))
        pen.lineTo((500, 700))
        pen.lineTo((500, 0))
        pen.closePath()
        fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (600, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable(names)
    fb.setupOS2()
    fb.setupPost()
    if dsig:
        fb.setupDummyDSIG()
    fb.font["head"].modified = MODIFIED
    fb.font.recalcTimestamp = False
    fb.font.flavor = flavor
    fb.save(str(path))
    return path


def write_raw_tables(path, replace, order=None):
    """Rewrite path keeping every table's bytes, except the tables given in
    replace ({tag: bytes}), which are written exactly as given; the table
    data is laid out in the order given, or else as it was."""
    font = TTFont(str(path), recalcTimestamp=False)
    reader = font.reader
    buffer = io.BytesIO()
    writer = SFNTWriter(buffer, len(reader.keys()), reader.sfntVersion)
    for tag in order or reader.keys():
        writer[tag] = replace.get(tag, reader[tag])
    writer.close()
    path.write_bytes(buffer.getvalue())
    return path


def data_order(path):
    """The table tags of path in the order their data is laid out."""
    data = path.read_bytes()
    count = struct.unpack(">H", data[4:6])[0]
    entries = [struct.unpack(">4sLLL", data[12 + 16 * i:28 + 16 * i])
               for i in range(count)]
    return [tag.decode() for tag, _, offset, _ in
            sorted(entries, key=lambda entry: entry[2])]


def name_table_bytes(records, version=0, lang_tags=()):
    """A raw 'name' table: records are (platform, encoding, language, name ID,
    bytes), each stored separately, in the order given."""
    directory, strings = b"", b""
    for platform, encoding, language, name_id, data in records:
        directory += struct.pack(">6H", platform, encoding, language, name_id,
                                 len(data), len(strings))
        strings += data
    tags = b""
    if version == 1:
        tags = struct.pack(">H", len(lang_tags))
        for tag in lang_tags:
            tags += struct.pack(">HH", len(tag), len(strings))
            strings += tag
    header = struct.pack(">3H", version, len(records),
                         6 + len(directory) + len(tags))
    return header + directory + tags + strings


def raw_records(path):
    font = TTFont(str(path))
    return [(r.platformID, r.platEncID, r.langID, r.nameID, r.toBytes())
            for r in font["name"].names]


def lay_out_name_table_unshared(path):
    """Rewrite path's 'name' table the way many build tools do and fontTools
    does not: records in file order, every string stored separately."""
    font = TTFont(str(path), recalcTimestamp=False)
    records = list(reversed(font["name"].names))  # not fontTools' order
    table = DefaultTable("name")
    table.data = name_table_bytes(
        [(r.platformID, r.platEncID, r.langID, r.nameID, r.toBytes())
         for r in records])
    font["name"] = table
    buffer = io.BytesIO()
    font.save(buffer)
    path.write_bytes(buffer.getvalue())
    return path


def damage_glyf(path):
    """Give glyph "A" a contour end point far past its data: damage that only
    a full decompile of 'glyf' (as the WOFF2 transform does) notices."""
    font = TTFont(str(path))
    raw = bytearray(font.reader["glyf"])
    struct.pack_into(">H", raw, font["loca"][1] + 10, 60000)
    return write_raw_tables(path, {"glyf": bytes(raw)})


def name_records(path):
    font = TTFont(str(path))
    return sorted((r.nameID, r.platformID, r.platEncID, r.langID, r.string)
                  for r in font["name"].names)


def identifier(path, name_id, platform=3):
    """The English record with this ID (Windows by default), decoded."""
    if platform == 3:
        record = TTFont(str(path))["name"].getName(name_id, 3, 1, 0x409)
    else:
        record = TTFont(str(path))["name"].getName(name_id, 1, 0, 0)
    return record.toUnicode()


def tables(path):
    font = TTFont(str(path))
    return {tag: font.reader[tag] for tag in font.reader.keys()}


def snapshot(directory):
    return {p.name: p.read_bytes() for p in sorted(Path(directory).iterdir())}


def run_tool(*args):
    """Run main() in-process; (exit status, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            status = tool.main([str(a) for a in args])
        except SystemExit as exc:
            status = exc.code
    return status, out.getvalue(), err.getvalue()


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        # Copies kept for comparison live apart, so they are never arguments.
        self._keep = tempfile.TemporaryDirectory()
        self.keep_dir = Path(self._keep.name)
        self.addCleanup(self._keep.cleanup)

    def keep(self, path):
        copy = self.keep_dir / path.name
        shutil.copyfile(path, copy)
        return copy

    def font(self, name, family=FROM, **kwargs):
        return build_font(self.dir / name, names_for(family), **kwargs)

    def pair(self, stem="NoctuaIosevka-Regular", family=FROM):
        """A .ttf and its web copy, made with fontTools' WOFF2 converter."""
        ttf = self.font(f"{stem}.ttf", family, dsig=True)
        web = self.dir / f"{stem}.woff2"
        woff2.compress(str(ttf), str(web))
        return ttf, web

    def assertRefusedUnchanged(self, before, *args, message):
        status, _, err = run_tool(*args)
        self.assertEqual(status, 1, err)
        self.assertIn(message, err)
        self.assertIn("nothing was changed", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(snapshot(self.dir), before)
        return err


class SubstituteTest(unittest.TestCase):
    def test_occurrence_inside_to_is_not_replaced(self):
        pairs = [(FROM, TO)]
        self.assertEqual(tool.substitute("Noctua Iosevka Bold", pairs),
                         "Noctua Iosevka Code Bold")
        self.assertEqual(tool.substitute("Noctua Iosevka Code Bold", pairs),
                         "Noctua Iosevka Code Bold")

    def test_to_containing_from_in_the_middle(self):
        pairs = [("Iosevka", "Noctua Iosevka")]
        self.assertEqual(tool.substitute("Iosevka Bold", pairs),
                         "Noctua Iosevka Bold")
        self.assertEqual(tool.substitute("Noctua Iosevka Bold", pairs),
                         "Noctua Iosevka Bold")

    def test_from_containing_to_is_still_replaced(self):
        pairs = [(TO, FROM)]
        self.assertEqual(tool.substitute("Noctua Iosevka Code Bold", pairs),
                         "Noctua Iosevka Bold")

    def test_occurrence_inside_to_is_kept_despite_an_overlapping_match(self):
        # "abab": the "ab" at 2 is part of the "bab" at 1, so it stays, even
        # though the "ab" at 0 (which is not) overlaps that "bab".
        self.assertEqual(tool.substitute("abab", [("ab", "bab")]), "babab")

    def test_a_to_that_equals_another_pairs_from_guards_nothing(self):
        pairs = tool.record_pairs(1, "FooBar", "Foo Bar")
        self.assertEqual(tool.substitute("FooBar Regular", pairs),
                         "Foo Bar Regular")

    def test_an_empty_from_is_ignored(self):
        self.assertEqual(tool.substitute("Foo", [("", "x")]), "Foo")

    def test_every_occurrence_is_replaced(self):
        self.assertEqual(tool.substitute("Foo / Foo", [("Foo", "Bar")]),
                         "Bar / Bar")

    def test_postscript_records_take_the_compact_and_hyphenated_forms(self):
        self.assertEqual(tool.record_pairs(6, FROM, TO),
                         [("NoctuaIosevka", "NoctuaIosevkaCode"),
                          ("Noctua-Iosevka", "Noctua-Iosevka-Code")])
        self.assertEqual(tool.record_pairs(6, "Foo", "Bar"), [("Foo", "Bar")])
        self.assertEqual(tool.record_pairs(1, "My Font", "Other"),
                         [("My Font", "Other"), ("MyFont", "Other")])

    def test_a_from_without_a_space_takes_the_compact_form(self):
        pairs = tool.record_pairs(6, "Iosevka", "Noctua Iosevka")
        self.assertEqual(tool.substitute("Iosevka-Bold", pairs),
                         "NoctuaIosevka-Bold")
        # The hyphenated TO still guards a record that is already on it.
        self.assertEqual(tool.substitute("Noctua-Iosevka-Bold", pairs),
                         "Noctua-Iosevka-Bold")


class IdentityTest(unittest.TestCase):
    def test_files_without_inodes_are_never_merged(self):
        no_inode = mock.Mock(st_dev=0, st_ino=0)
        self.assertNotEqual(tool.identity(Path("a.ttf"), no_inode),
                            tool.identity(Path("b.ttf"), no_inode))


class BatchValidationTest(TempDirTestCase):
    """Defect 1: a .ttf and its .woff2 listed together, and validation."""

    def check_pair_renamed(self, status, err):
        self.assertEqual(status, 0, err)
        ttf = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        web = self.dir / "NoctuaIosevkaCode-Regular.woff2"
        self.assertEqual(sorted(snapshot(self.dir)), [ttf.name, web.name])
        self.assertEqual(identifier(ttf, 1), TO)
        self.assertEqual(identifier(web, 1), TO)

    def test_ttf_then_its_woff2(self):
        ttf, web = self.pair()
        status, out, err = run_tool(FROM, TO, ttf, web)
        self.check_pair_renamed(status, err)
        self.assertEqual(out.count("NoctuaIosevka-Regular.woff2"), 1, out)

    def test_woff2_then_its_ttf(self):
        ttf, web = self.pair()
        self.check_pair_renamed(*run_tool(FROM, TO, web, ttf)[::2])

    def test_woff2_listed_twice_and_ttf_by_another_spelling(self):
        ttf, web = self.pair()
        other = self.dir / ".." / self.dir.name / ttf.name
        self.check_pair_renamed(*run_tool(FROM, TO, web, ttf, web, other)[::2])

    def test_missing_path_leaves_everything_unchanged(self):
        ttf, web = self.pair()
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(
            before, FROM, TO, ttf, web, self.dir / "absent.ttf",
            message="no such file")

    def test_missing_path_listed_first_leaves_everything_unchanged(self):
        ttf, web = self.pair()
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(
            before, FROM, TO, self.dir / "absent.ttf", ttf, web,
            message="no such file")

    def test_a_file_that_is_not_a_font_leaves_everything_unchanged(self):
        ttf, web = self.pair()
        (self.dir / "README.md").write_text("not a font\n")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(
            before, FROM, TO, *sorted(self.dir.iterdir()),
            message="not a font this tool can read")

    def test_a_directory_is_refused(self):
        ttf, _ = self.pair()
        (self.dir / "sub").mkdir()
        status, _, err = run_tool(FROM, TO, ttf, self.dir / "sub")
        self.assertEqual(status, 1)
        self.assertIn("is not a regular file", err)
        self.assertTrue(ttf.exists())

    def test_a_symbolic_link_is_refused(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        link = self.dir / "link.ttf"
        try:
            os.symlink(ttf, link)
        except (OSError, NotImplementedError):
            self.skipTest("cannot create symbolic links here")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, link,
                                    message="symbolic link")

    def test_a_hard_linked_file_is_refused(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        try:
            os.link(ttf, self.dir / "other-name.ttf")
        except (OSError, NotImplementedError):
            self.skipTest("cannot create hard links here")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="hard links")

    def test_a_signed_font_is_refused_and_the_dummy_signature_is_not(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        font = TTFont(str(ttf), recalcTimestamp=False)
        signed = DefaultTable("DSIG")
        signed.data = (struct.pack(">LHH", 1, 1, 0)
                       + struct.pack(">LLL", 1, 12, 20)
                       + struct.pack(">HHL", 0, 0, 4) + b"\x30\x00\x00\x00")
        font["DSIG"] = signed
        font.save(str(ttf))
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="digitally signed")
        # pair() fonts carry FontBuilder's empty placeholder DSIG.
        plain, _ = self.pair("Other-Regular")
        status, _, err = run_tool(FROM, TO, plain)
        self.assertEqual(status, 0, err)

    def test_usage_errors(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        for args in ((FROM, FROM, ttf), ("", TO, ttf), ("  ", TO, ttf),
                     (FROM, "Bad\nName", ttf), (FROM, TO)):
            with self.subTest(args=args):
                status, _, _ = run_tool(*args)
                self.assertEqual(status, 2)
        self.assertEqual(identifier(ttf, 1), FROM)

    def test_a_ttf_and_an_otf_sharing_one_web_copy_are_refused(self):
        ttf, web = self.pair()
        otf = self.font("NoctuaIosevka-Regular.otf", cff=True)
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf, otf, web,
                                    message="is the web copy of both")

    @unittest.skipUnless(POSIX_USER, "needs POSIX permissions, not root")
    def test_an_unwritable_directory_is_refused(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        before = snapshot(self.dir)
        os.chmod(self.dir, 0o555)
        self.addCleanup(os.chmod, self.dir, 0o755)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="directory is not writable")


class RoundTripTest(TempDirTestCase):
    """Defect 2: what a rename and its reverse actually keep."""

    def round_trip(self, path):
        status, _, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        renamed = path.with_name(path.name.replace("NoctuaIosevka",
                                                   "NoctuaIosevkaCode"))
        status, _, err = run_tool(TO, FROM, renamed)
        self.assertEqual(status, 0, err)
        self.assertEqual(sorted(snapshot(self.dir)), [path.name])
        return path

    def assert_kept_but_name_and_checksum(self, original, result):
        a, b = tables(original), tables(result)
        self.assertEqual(sorted(a), sorted(b))
        for tag in a:
            if tag not in ("name", "head"):
                self.assertEqual(a[tag], b[tag], tag)
        differing = [i for i, (x, y) in enumerate(zip(a["head"], b["head"]))
                     if x != y]
        self.assertTrue(set(differing) <= {8, 9, 10, 11}, differing)

    def test_original_file_comes_back_with_identical_records(self):
        path = lay_out_name_table_unshared(
            self.font("NoctuaIosevka-Regular.ttf", dsig=True))
        original_bytes = path.read_bytes()
        original_records = name_records(path)
        keep = self.keep(path)

        self.round_trip(path)
        self.assertEqual(name_records(path), original_records)
        self.assert_kept_but_name_and_checksum(keep, path)
        # The docstring used to promise a byte-identical file: it is not,
        # because fontTools re-lays the 'name' table it compiles.
        self.assertNotEqual(path.read_bytes(), original_bytes)
        self.assertNotEqual(tables(keep)["name"], tables(path)["name"])

    def test_a_file_the_tool_wrote_comes_back_byte_identical(self):
        for name, kwargs in (
                ("NoctuaIosevka-Regular.ttf", {}),
                ("NoctuaIosevka-Regular.otf", {"cff": True}),
                ("NoctuaIosevka-Regular.woff2", {"flavor": "woff2"}),
                ("NoctuaIosevka-Regular.woff", {"flavor": "woff"})):
            with self.subTest(name=name):
                path = lay_out_name_table_unshared(self.font(name, **kwargs))
                self.round_trip(path)        # now in the tool's own layout
                written = path.read_bytes()
                self.round_trip(path)
                self.assertEqual(path.read_bytes(), written)
                path.unlink()

    def test_a_rename_keeps_every_other_table_and_the_timestamp(self):
        for suffix, kwargs in ((".ttf", {"dsig": True}),
                               (".otf", {"cff": True}),
                               (".woff", {"flavor": "woff"})):
            with self.subTest(suffix=suffix):
                path = self.font(f"NoctuaIosevka-Regular{suffix}", **kwargs)
                keep = self.keep(path)
                status, _, err = run_tool(FROM, TO, path)
                self.assertEqual(status, 0, err)
                renamed = self.dir / f"NoctuaIosevkaCode-Regular{suffix}"
                self.assert_kept_but_name_and_checksum(keep, renamed)
                self.assertEqual(TTFont(str(renamed))["head"].modified,
                                 MODIFIED)
                renamed.unlink()

    def test_the_table_layout_is_kept(self):
        # Neither fontTools' recommended order nor tag order: the rename must
        # keep it, as fontTools' own WOFF2 converter does.
        path = self.font("NoctuaIosevka-Regular.ttf")
        order = sorted(TTFont(str(path)).reader.keys(), reverse=True)
        write_raw_tables(path, {}, order)
        self.assertEqual(data_order(path), order)
        self.assertEqual(run_tool(FROM, TO, path)[0], 0)
        self.assertEqual(
            data_order(self.dir / "NoctuaIosevkaCode-Regular.ttf"), order)

    def test_woff2_round_trip_keeps_decoded_tables(self):
        path = self.font("NoctuaIosevka-Regular.woff2", flavor="woff2")
        keep = self.keep(path)
        self.round_trip(path)
        self.assertEqual(name_records(path), name_records(keep))
        self.assert_kept_but_name_and_checksum(keep, path)
        self.assertEqual(TTFont(str(path)).flavor, "woff2")

    def test_a_record_that_already_carried_to_gets_a_note(self):
        names = names_for(FROM)
        names[3] = f"{TO} 1.000"
        path = build_font(self.dir / "NoctuaIosevka-Regular.ttf", names)
        status, out, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        self.assertIn("will not give NoctuaIosevka-Regular.ttf back", out)
        self.assertIn("would come back as 'Noctua Iosevka 1.000'", out)
        status, out, _ = run_tool(FROM, TO, self.font("Plain-Regular.ttf"))
        self.assertNotIn("note:", out)


class SwapTest(TempDirTestCase):
    """The promise: with no note, swapping FROM and TO restores the font."""

    def test_a_swap_that_would_be_refused_gets_a_note(self):
        # Found by review: forward "bb" -> "ab" gives "Xaaab", but the swap
        # "ab" -> "bb" gives "Xaabb" and a further run "Xabbb": refused.
        names = {1: "Xaabb", 2: "Regular", 3: "uid", 4: "Xaabb Regular",
                 6: "Fixed-Regular"}
        path = build_font(self.dir / "font.ttf", names)
        status, out, err = run_tool("bb", "ab", path)
        self.assertEqual(status, 0, err)
        self.assertEqual(identifier(path, 1), "Xaaab")
        self.assertIn("will not give font.ttf back exactly: the swapped run "
                      "would be refused", out)
        status, _, err = run_tool("ab", "bb", path)
        self.assertEqual(status, 1)
        self.assertIn("not stable", err)

    def test_a_file_name_that_would_not_come_back_gets_a_note(self):
        # The records come back, the file name would not: its compact TO
        # kept it from being renamed, and the swap would rename it.
        path = self.font("NoctuaIosevkaCode-Regular.ttf")
        status, out, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        self.assertIn("will not give NoctuaIosevkaCode-Regular.ttf back "
                      "exactly: the file name would come back as "
                      "'NoctuaIosevka-Regular.ttf'", out)

    def test_a_postscript_name_that_could_not_be_restored_gets_a_note(self):
        # "Foo(1)-Regular" is no valid PostScript name. The rename makes it
        # one ("Bar-Regular"), and the swap, which would restore it, would
        # be refused for that.
        names = names_for("Foo(1)")
        path = build_font(self.dir / "Plain-Regular.ttf", names)
        status, out, err = run_tool("Foo(1)", "Bar", path)
        self.assertEqual(status, 0, err)
        self.assertEqual(identifier(path, 6), "Bar-Regular")
        self.assertIn("the swapped run would be refused: name record ID 6", out)
        self.assertIn("not a valid PostScript name", out)
        status, _, err = run_tool("Bar", "Foo(1)", path)
        self.assertEqual(status, 1)
        self.assertIn("not a valid PostScript name", err)

    def test_a_file_name_that_could_not_be_restored_gets_a_note(self):
        # Checked on the path alone: no such file can exist on Windows.
        target, irreversible = tool.renamed_path(
            self.dir / "Foo:x-Regular.ttf", "Foo:x", "Bar")
        self.assertEqual(target.name, "Bar-Regular.ttf")
        self.assertIn("the swapped run would be refused: 'Foo:x-Regular.ttf' "
                      "is not a portable name", irreversible)


class SwapPropertyTest(unittest.TestCase):
    """Idempotence, and the swap promise, over many small random cases."""

    CASES = 4000

    @staticmethod
    def word(rng, alphabet, low, high):
        return "".join(rng.choice(alphabet)
                       for _ in range(rng.randint(low, high)))

    @staticmethod
    def rename_record(text, name_id, old, new):
        record = SimpleNamespace(nameID=name_id, platformID=3, platEncID=1,
                                 langID=0x409, toUnicode=lambda: text)
        changes, irreversible = tool.plan_records(
            SimpleNamespace(names=[record]), old, new, "test")
        return (changes[0][2] if changes else text), irreversible

    def test_records(self):
        rng = random.Random(1)
        checked = 0
        for _ in range(self.CASES):
            old, new = self.word(rng, "ab ", 1, 3), self.word(rng, "ab ", 1, 4)
            if not old.strip() or not new.strip() or old == new:
                continue
            name_id = rng.choice([1, 4, 6])
            text = self.word(rng, "ab-" if name_id == 6 else "ab ", 0, 7)
            try:
                after, irreversible = self.rename_record(text, name_id, old,
                                                         new)
            except tool.RenameError:
                continue
            case = (text, name_id, old, new, after)
            self.assertEqual(
                self.rename_record(after, name_id, old, new)[0], after, case)
            if irreversible is None:
                self.assertEqual(
                    self.rename_record(after, name_id, new, old)[0], text,
                    case)
            checked += 1
        self.assertGreater(checked, self.CASES // 4)

    def test_file_names(self):
        rng = random.Random(2)
        checked = 0
        for _ in range(self.CASES):
            old, new = self.word(rng, "ab", 1, 3), self.word(rng, "ab", 1, 4)
            if old == new:
                continue
            path = Path(self.word(rng, "ab", 1, 7) + ".ttf")
            try:
                target, irreversible = tool.renamed_path(path, old, new)
            except tool.RenameError:
                continue
            case = (path, old, new, target)
            self.assertEqual(tool.renamed_path(target, old, new)[0], target,
                             case)
            if irreversible is None:
                self.assertEqual(tool.renamed_path(target, new, old)[0], path,
                                 case)
            checked += 1
        self.assertGreater(checked, self.CASES // 4)


class IdempotenceTest(TempDirTestCase):
    """Defect 3: TO containing FROM, and the reverse rename."""

    def test_to_containing_from_twice(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        status, _, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        renamed = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        self.assertEqual(sorted(snapshot(self.dir)), [renamed.name])
        first = snapshot(self.dir)
        status, out, err = run_tool(FROM, TO, renamed)
        self.assertEqual(status, 0, err)
        self.assertIn("nothing to do", out)
        self.assertEqual(snapshot(self.dir), first)
        self.assertEqual(identifier(renamed, 1), TO)
        self.assertEqual(identifier(renamed, 4), f"{TO} Regular")
        self.assertEqual(identifier(renamed, 6), "NoctuaIosevkaCode-Regular")

    def test_reverse_twice(self):
        path = self.font("NoctuaIosevkaCode-Regular.ttf", TO)
        status, _, err = run_tool(TO, FROM, path)
        self.assertEqual(status, 0, err)
        back = self.dir / "NoctuaIosevka-Regular.ttf"
        self.assertEqual(sorted(snapshot(self.dir)), [back.name])
        self.assertEqual(identifier(back, 1), FROM)
        self.assertEqual(identifier(back, 6), "NoctuaIosevka-Regular")
        first = snapshot(self.dir)
        status, out, err = run_tool(TO, FROM, back)
        self.assertEqual(status, 0, err)
        self.assertEqual(snapshot(self.dir), first)

    def test_a_file_name_already_on_to_is_not_renamed_again(self):
        # Records still on FROM, file name already on TO's compact form: the
        # records change, the file name must not ("...CodeCode...").
        ttf, web = self.pair("NoctuaIosevkaCode-Regular")
        status, out, err = run_tool(FROM, TO, ttf)
        self.assertEqual(status, 0, err)
        self.assertEqual(sorted(snapshot(self.dir)), [ttf.name, web.name])
        self.assertNotIn("CodeCode", out)
        self.assertEqual(identifier(ttf, 1), TO)
        self.assertEqual(identifier(web, 1), TO)
        self.assertEqual(identifier(ttf, 6), "NoctuaIosevkaCode-Regular")
        first = snapshot(self.dir)
        self.assertEqual(run_tool(FROM, TO, ttf, web)[0], 0)
        self.assertEqual(snapshot(self.dir), first)
        # The reverse rename still renames the file (and its web copy).
        status, _, err = run_tool(TO, FROM, ttf)
        self.assertEqual(status, 0, err)
        self.assertEqual(sorted(snapshot(self.dir)),
                         ["NoctuaIosevka-Regular.ttf",
                          "NoctuaIosevka-Regular.woff2"])
        self.assertEqual(identifier(self.dir / "NoctuaIosevka-Regular.ttf",
                                    1), FROM)

    def test_the_file_name_guard_in_both_directions(self):
        for name, old, new, expected in (
                ("NoctuaIosevkaCode-Regular.ttf", FROM, TO,
                 "NoctuaIosevkaCode-Regular.ttf"),
                ("NoctuaIosevka-Regular.ttf", FROM, TO,
                 "NoctuaIosevkaCode-Regular.ttf"),
                ("NoctuaIosevkaCode-Regular.ttf", TO, FROM,
                 "NoctuaIosevka-Regular.ttf")):
            with self.subTest(name=name, old=old):
                target, _ = tool.renamed_path(self.dir / name, old, new)
                self.assertEqual(target.name, expected)

    def test_web_copy_listed_twice_over_two_runs(self):
        ttf, web = self.pair()
        self.assertEqual(run_tool(FROM, TO, ttf, web)[0], 0)
        first = snapshot(self.dir)
        status, out, err = run_tool(FROM, TO, *sorted(self.dir.iterdir()))
        self.assertEqual(status, 0, err)
        self.assertEqual(snapshot(self.dir), first)
        self.assertIn("web copy of NoctuaIosevkaCode-Regular.ttf", out)

    def test_an_unstable_rename_is_refused(self):
        path = build_font(self.dir / "aab.ttf", names_for("aab"))
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, "ab", "bc", path,
                                    message="not stable")

    def test_unstable_records_are_refused_whatever_the_file_name(self):
        path = build_font(self.dir / "font.ttf", names_for("aab"))
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, "ab", "bc", path,
                                    message="not stable on name record")

    def test_an_unstable_file_name_is_refused_when_the_records_are_not(self):
        # "xab" -> "xbc" is stable; the file name "aab" -> "abc" -> "bcc" not.
        path = build_font(self.dir / "aab.ttf", names_for("xab"))
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, "ab", "bc", path,
                                    message="not stable on the file name")


class NameRecordTest(TempDirTestCase):
    def test_legal_records_are_untouched(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        before = {r[:4]: r[4] for r in name_records(path) if r[0] in LEGAL}
        self.assertEqual(run_tool(FROM, TO, path)[0], 0)
        after_path = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        after = {r[:4]: r[4] for r in name_records(after_path)
                 if r[0] in LEGAL}
        self.assertEqual(after, before)
        self.assertEqual(identifier(after_path, 0), LEGAL[0])

    def test_compact_form_in_postscript_name_and_file_name(self):
        path = build_font(self.dir / "Iosevka-Bold.ttf",
                          names_for("Iosevka", "Bold"))
        status, _, err = run_tool("Iosevka", "Noctua Iosevka", path)
        self.assertEqual(status, 0, err)
        renamed = self.dir / "NoctuaIosevka-Bold.ttf"
        self.assertTrue(renamed.exists())
        self.assertFalse(path.exists())
        self.assertEqual(identifier(renamed, 1), "Noctua Iosevka")
        self.assertEqual(identifier(renamed, 6), "NoctuaIosevka-Bold")
        self.assertEqual(identifier(renamed, 6, platform=1),
                         "NoctuaIosevka-Bold")

    def test_hyphenated_form_in_postscript_name(self):
        # Iosevka writes a spaced family into the PostScript name with
        # hyphens: "Noctua-Iosevka-Bold".
        names = names_for(FROM, "Bold")
        names[6] = "Noctua-Iosevka-Bold"
        path = build_font(self.dir / "NoctuaIosevka-Bold.ttf", names)
        status, out, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        self.assertNotIn("note:", out)
        renamed = self.dir / "NoctuaIosevkaCode-Bold.ttf"
        for platform in (3, 1):
            self.assertEqual(identifier(renamed, 6, platform),
                             "Noctua-Iosevka-Code-Bold")
        first = snapshot(self.dir)
        self.assertEqual(run_tool(FROM, TO, renamed)[0], 0)
        self.assertEqual(snapshot(self.dir), first)
        self.assertEqual(run_tool(TO, FROM, renamed)[0], 0)
        self.assertEqual(identifier(path, 6), "Noctua-Iosevka-Bold")

    def test_a_postscript_name_without_from_gets_a_note(self):
        family = "NoctuaIosevka Nerd Font Mono"
        names = names_for(family)
        names[6] = "NoctuaIosevkaNFM-Regular"  # the patcher's abbreviation
        path = build_font(self.dir / "NoctuaIosevkaNerdFontMono-Regular.ttf",
                          names)
        status, out, err = run_tool(family, "Noctua Iosevka Mono", path)
        self.assertEqual(status, 0, err)
        renamed = self.dir / "NoctuaIosevkaMono-Regular.ttf"
        self.assertEqual(identifier(renamed, 1), "Noctua Iosevka Mono")
        self.assertEqual(identifier(renamed, 6), "NoctuaIosevkaNFM-Regular")
        self.assertEqual(out.count("kept the PostScript name "
                                   "'NoctuaIosevkaNFM-Regular'"), 1, out)

    def test_spaced_from_and_its_compact_form(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        self.assertEqual(run_tool(FROM, "Owl Mono", path)[0], 0)
        renamed = self.dir / "OwlMono-Regular.ttf"
        self.assertEqual(identifier(renamed, 4), "Owl Mono Regular")
        self.assertEqual(identifier(renamed, 3), "1.000;NONE;OwlMono-Regular")
        self.assertEqual(identifier(renamed, 6), "OwlMono-Regular")

    def test_file_name_without_the_compact_form_is_kept(self):
        path = self.font("Code-Regular.ttf")
        self.assertEqual(run_tool(FROM, TO, path)[0], 0)
        self.assertEqual(identifier(path, 1), TO)

    def test_a_font_without_from_is_left_alone(self):
        path = build_font(self.dir / "Other-Regular.ttf", names_for("Other"))
        before = snapshot(self.dir)
        status, out, _ = run_tool(FROM, TO, path)
        self.assertEqual(status, 0)
        self.assertIn("nothing to do (Other)", out)
        self.assertEqual(snapshot(self.dir), before)

    def test_an_encoding_that_cannot_hold_to_is_refused(self):
        names = names_for(FROM)
        names[6] = "Plain-Regular"  # the PostScript name does not change
        path = build_font(self.dir / "Plain.ttf", names)  # nor the file name
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, "Noctua 字", path,
                                    message="cannot hold")

    def test_an_invalid_postscript_name_is_refused(self):
        for to in ("Noctua (Iosevka)",          # a forbidden character
                   "Noctua Iosévka",            # not ASCII
                   "Noctua Iosevka " + "X" * 60):  # longer than 63
            with self.subTest(to=to):
                for leftover in self.dir.iterdir():
                    leftover.unlink()
                path = self.font("NoctuaIosevka-Regular.ttf")
                before = snapshot(self.dir)
                self.assertRefusedUnchanged(
                    before, FROM, to, path,
                    message="not a valid PostScript name")

    def test_a_separator_in_to_never_becomes_a_path(self):
        names = names_for(FROM)
        names[6] = "Fixed-Regular"  # isolate the file-name check
        for file_name, to in (("NoctuaIosevka-Regular.ttf", "../Escape"),
                              ("NoctuaIosevka-Regular.ttf", "Sub/Dir"),
                              ("NoctuaIosevka-Regular.ttf", "Back\\Slash"),
                              ("NoctuaIosevka-Regular.ttf", "C:Stream"),
                              ("NoctuaIosevka.ttf", "NUL"),
                              ("NoctuaIosevka.ttf", "CONIN$"),
                              ("NoctuaIosevka .x.ttf", "AUX")):
            with self.subTest(to=to):
                for leftover in self.dir.iterdir():
                    leftover.unlink()
                path = build_font(self.dir / file_name, names)
                before = snapshot(self.dir)
                self.assertRefusedUnchanged(before, FROM, to, path,
                                            message="not a portable file name")
        self.assertFalse((self.dir.parent / "Escape-Regular.ttf").exists())


class NameTableTest(TempDirTestCase):
    """A 'name' table fontTools would not write back whole is refused."""

    def test_a_format_1_name_table_is_refused(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        records = raw_records(path)
        records.append((3, 1, 0x8000, 1, FROM.encode("utf_16_be")))
        write_raw_tables(path, {"name": name_table_bytes(
            sorted(records), version=1,
            lang_tags=["pt-BR".encode("utf_16_be")])})
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, path,
                                    message="'name' table is format 1")

    def test_a_malformed_name_record_is_refused(self):
        # The Windows copyright record claims one byte more than is stored:
        # fontTools skips it, so a rewrite would silently drop it.
        path = self.font("NoctuaIosevka-Regular.ttf")
        records = sorted(raw_records(path), key=lambda r: r[3] == 0)
        data = bytearray(name_table_bytes(records))
        last = 6 + 12 * (len(records) - 1)  # the Windows ID 0 record
        self.assertEqual(struct.unpack_from(">HxxxxH", data, last), (3, 0))
        length = struct.unpack_from(">H", data, last + 8)[0]
        struct.pack_into(">H", data, last + 8, length + 1)
        write_raw_tables(path, {"name": bytes(data)})
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, path,
                                    message="are malformed")

    def test_such_a_table_is_fine_when_the_font_is_not_rewritten(self):
        path = build_font(self.dir / "Other-Regular.ttf", names_for("Other"))
        write_raw_tables(path, {"name": name_table_bytes(
            sorted(raw_records(path)), version=1, lang_tags=[b"\x00e"])})
        status, out, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        self.assertIn("nothing to do", out)


class FileNameTest(TempDirTestCase):
    def test_reserved_windows_names_are_refused(self):
        for name in ("NUL.ttf", "nul.ttf", "COM1.ttf", "COM\u00b9.ttf",
                     "LPT\u00b3.woff2", "CONIN$.ttf", "conout$.ttf",
                     "NUL .ttf", "AUX .x.ttf", "Foo.", "Foo ", "a:b.ttf"):
            with self.subTest(name=name):
                with self.assertRaises(tool.RenameError):
                    tool.check_file_name(name, "test")
        for name in ("CONSOLE.ttf", "NULL.ttf", "COM0.ttf", "LPT\u00b2-x.ttf",
                     "Noctua Iosevka.ttf", "Ünïcødé.ttf"):
            with self.subTest(name=name):
                tool.check_file_name(name, "test")

    def test_reserved_names_are_refused_without_ntpath_isreserved(self):
        # Python before 3.13 has no ntpath.isreserved: the tool's own rule
        # must refuse the same names on its own.
        with mock.patch.object(tool, "ntpath", SimpleNamespace()):
            for name in ("COM\u00b9.ttf", "LPT\u00b3.woff2", "CONIN$.ttf",
                         "conout$.ttf", "NUL .ttf", "AUX .x.ttf"):
                with self.subTest(name=name):
                    with self.assertRaises(tool.RenameError):
                        tool.check_file_name(name, "test")
            tool.check_file_name("CONSOLE.ttf", "test")

    def test_a_name_longer_than_the_file_system_takes_is_refused(self):
        tool.check_file_name("B" * 251 + ".ttf", "test")
        for name in ("B" * 252 + ".ttf", "\u00e9" * 126 + ".ttf"):
            with self.subTest(length=len(name)):
                with self.assertRaises(tool.RenameError):
                    tool.check_file_name(name, "test")

    def test_a_long_name_is_refused_before_anything_is_written(self):
        # The pair alone would fit (244 bytes); the third font's new name,
        # 264 bytes, would not. The batch must stop before the pair moves.
        names = names_for("Foo")
        names[6], names[3] = "Fixed-Regular", "uid"
        first = build_font(self.dir / "Foo.ttf", names)
        woff2.compress(str(first), str(self.dir / "Foo.woff2"))
        third = build_font(self.dir / "Foo-Regular-Long-Name-X.ttf", names)
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, "Foo", "B" * 240, first, third,
                                    message="264 bytes long")

    @unittest.skipIf(os.name == "nt", "a long path past MAX_PATH there")
    def test_a_name_that_fits_is_written_whatever_its_length(self):
        # 254 bytes: it fits, and so must its temporary file, whose name used
        # to be 14 bytes longer than the font's.
        if tool.name_max(self.dir) < 255:
            self.skipTest("this file system takes shorter names")
        names = names_for("Foo")
        names[6], names[3] = "Fixed-Regular", "uid"
        path = build_font(self.dir / "Foo-Regular-Long-Name-X.ttf", names)
        status, _, err = run_tool("Foo", "B" * 230, path)
        self.assertEqual(status, 0, err)
        (renamed,) = self.dir.iterdir()
        self.assertEqual(len(renamed.name), 254)
        self.assertEqual(identifier(renamed, 1), "B" * 230)

    def test_a_path_past_max_path_is_refused_on_windows(self):
        short = self.dir / "Foo.ttf"
        long_target = self.dir / ("B" * 300 + ".ttf")
        self.assertIsNone(tool.windows_path_problem(short, long_target,
                                                    windows=False))
        self.assertIsNone(tool.windows_path_problem(short, short,
                                                    windows=True))
        self.assertIn("unless long paths are enabled",
                      tool.windows_path_problem(short, long_target,
                                                windows=True))
        # A source already past the limit shows long paths are enabled.
        self.assertIsNone(tool.windows_path_problem(
            self.dir / ("A" * 320 + ".ttf"), long_target, windows=True))
        # The temporary file counts as well: a short final name in a deep
        # directory can still leave no room for it.
        deep = Path("C:/" + "d" * (tool.WINDOWS_MAX_PATH - 20))
        self.assertIn("temporary file", tool.windows_path_problem(
            deep / "A.ttf", deep / "B.ttf", windows=True))


class OutputTest(TempDirTestCase):
    """Font-supplied text is escaped before it reaches a terminal."""

    def test_control_characters_from_a_font_never_reach_the_terminal(self):
        names = names_for("Other")
        names[1] = "Other\x1b]0;PWNED\x07\x1b[2J\u202e"
        path = build_font(self.dir / "Other-Regular.ttf", names)
        status, out, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        for raw in ("\x1b", "\x07", "\u202e"):
            self.assertNotIn(raw, out + err)
        self.assertIn("Other\\x1b]0;PWNED\\x07\\x1b[2J\\u202e", out)

    def test_control_characters_in_a_path_are_escaped_in_errors(self):
        status, _, err = run_tool(FROM, TO, self.dir / "absent\x1b[2J\n.ttf")
        self.assertEqual(status, 1)
        self.assertNotIn("\x1b", err)
        self.assertIn("absent\\x1b[2J\\x0a.ttf: ", err)

    def test_printable(self):
        self.assertEqual(tool.printable("a\tb\x7fc\x9bd\u200fe\u2028f"),
                         "a\\x09b\\x7fc\\x9bd\\u200fe\\u2028f")
        self.assertEqual(tool.printable("Noctua Iosévka 字 — ok"),
                         "Noctua Iosévka 字 — ok")


class WebCopyTest(TempDirTestCase):
    def test_web_copy_is_rebuilt_and_decodes_to_the_same_names(self):
        ttf, web = self.pair()
        status, out, err = run_tool(FROM, TO, ttf)
        self.assertEqual(status, 0, err)
        new_ttf = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        new_web = self.dir / "NoctuaIosevkaCode-Regular.woff2"
        self.assertEqual(sorted(snapshot(self.dir)),
                         [new_ttf.name, new_web.name])
        self.assertEqual(TTFont(str(new_web)).flavor, "woff2")
        self.assertEqual(name_records(new_web), name_records(new_ttf))
        self.assertIn("rebuilt from NoctuaIosevkaCode-Regular.ttf", out)
        # It is exactly what fontTools' own converter makes of the new .ttf.
        expected = io.BytesIO()
        woff2.compress(str(new_ttf), expected)
        self.assertEqual(new_web.read_bytes(), expected.getvalue())

    def test_a_stale_web_copy_is_rebuilt_even_when_the_font_is_done(self):
        ttf = self.font("Fam-Regular.ttf", TO)
        web = self.dir / "Fam-Regular.woff2"
        build_font(web, names_for(FROM), flavor="woff2")
        status, out, err = run_tool(FROM, TO, ttf)
        self.assertEqual(status, 0, err)
        self.assertEqual(identifier(web, 1), TO)
        self.assertEqual(name_records(web), name_records(ttf))

    def test_an_unrelated_font_never_replaces_a_same_stem_web_copy(self):
        # Found by review: the .ttf carries neither FROM nor TO, its
        # same-stem .woff2 carries FROM. Rebuilding the .woff2 from the .ttf
        # would destroy it and leave a family that is neither.
        ttf = build_font(self.dir / "Fam-Regular.ttf",
                         names_for("Other Family"))
        web = build_font(self.dir / "Fam-Regular.woff2", names_for(FROM),
                         flavor="woff2")
        before = snapshot(self.dir)
        err = self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                          message="is another font")
        self.assertIn("'Noctua Iosevka Code' where the font's is "
                      "'Other Family'", err)
        # Renamed in a run of its own, the copy keeps its own content.
        status, _, err = run_tool(FROM, TO, web)
        self.assertEqual(status, 0, err)
        self.assertEqual(identifier(web, 1), TO)
        self.assertEqual(snapshot(self.dir)[ttf.name], before[ttf.name])

    def test_a_web_copy_of_another_family_is_not_replaced(self):
        ttf = self.font("Fam-Regular.ttf")
        build_font(self.dir / "Fam-Regular.woff2", names_for("Other Family"),
                   flavor="woff2")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="is another font")

    def test_a_web_copy_of_another_build_is_not_replaced(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        names = names_for(FROM)
        names[3] = "0.900;NONE;NoctuaIosevka-Regular"
        build_font(self.dir / "NoctuaIosevka-Regular.woff2", names,
                   flavor="woff2")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="is another font")

    def test_a_woff2_listed_alone_is_renamed_on_its_own(self):
        web = self.font("NoctuaIosevka-Regular.woff2", flavor="woff2")
        status, _, err = run_tool(FROM, TO, web)
        self.assertEqual(status, 0, err)
        renamed = self.dir / "NoctuaIosevkaCode-Regular.woff2"
        self.assertEqual(sorted(snapshot(self.dir)), [renamed.name])
        self.assertEqual(TTFont(str(renamed)).flavor, "woff2")
        self.assertEqual(identifier(renamed, 1), TO)

    def test_a_web_copy_that_is_not_a_font_is_not_replaced(self):
        ttf = self.font("NoctuaIosevka-Regular.ttf")
        (self.dir / "NoctuaIosevka-Regular.woff2").write_bytes(b"junk")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="not a font this tool can read")


class CollisionTest(TempDirTestCase):
    def test_an_existing_target_is_not_overwritten(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        (self.dir / "NoctuaIosevkaCode-Regular.ttf").write_bytes(b"precious")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, path,
                                    message="already exists")

    def test_an_existing_web_copy_target_is_not_overwritten(self):
        ttf, _ = self.pair()
        (self.dir / "NoctuaIosevkaCode-Regular.woff2").write_bytes(b"keep")
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, ttf,
                                    message="already exists")

    def test_two_outputs_onto_one_name_are_refused(self):
        a = build_font(self.dir / "FooBar.ttf", names_for("Foo"))
        b = build_font(self.dir / "BarFoo.ttf", names_for("Foo"))
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, "Foo", "Bar", a, b,
                                    message="would be written there")

    def test_a_target_that_appears_after_planning_is_not_overwritten(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        target = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        (job,) = tool.plan([path], FROM, TO)
        tool.build_job(job, FROM, TO)
        target.write_bytes(b"appeared")
        with self.assertRaises(tool.RenameError):
            tool.commit_job(job)
        self.assertEqual(tool.discard([job]), [])
        self.assertEqual(target.read_bytes(), b"appeared")
        self.assertEqual(identifier(path, 1), FROM)
        self.assertEqual(sorted(snapshot(self.dir)),
                         [path.name, target.name])

    def test_a_source_changed_after_planning_is_not_overwritten(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        (job,) = tool.plan([path], FROM, TO)
        build_font(path, names_for(FROM, "Bold"))
        changed = path.read_bytes()
        with self.assertRaises(tool.RenameError):
            tool.build_job(job, FROM, TO)
        self.assertEqual(path.read_bytes(), changed)
        self.assertEqual(sorted(snapshot(self.dir)), [path.name])

    def test_a_source_changed_after_building_is_not_overwritten(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        (job,) = tool.plan([path], FROM, TO)
        tool.build_job(job, FROM, TO)
        build_font(path, names_for(FROM, "Bold"))
        changed = path.read_bytes()
        with self.assertRaises(tool.RenameError):
            tool.commit_job(job)
        self.assertEqual(tool.discard([job]), [])
        self.assertEqual(path.read_bytes(), changed)
        self.assertEqual(sorted(snapshot(self.dir)), [path.name])


class AtomicWriteTest(TempDirTestCase):
    def test_a_failed_move_leaves_the_old_files_and_no_temporary(self):
        ttf, web = self.pair()
        before = snapshot(self.dir)
        with mock.patch.object(tool.os, "replace",
                               side_effect=OSError("simulated crash")):
            status, _, err = run_tool(FROM, TO, ttf, web)
        self.assertEqual(status, 1)
        self.assertIn("simulated crash", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_a_failed_move_in_place_leaves_the_old_file_whole(self):
        path = self.font("Code-Regular.ttf")  # rewritten under its own name
        before = snapshot(self.dir)
        with mock.patch.object(tool.os, "replace",
                               side_effect=OSError("simulated crash")):
            status, _, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 1)
        self.assertEqual(snapshot(self.dir), before)
        self.assertEqual(identifier(path, 1), FROM)

    def test_a_failed_write_leaves_the_old_file_and_no_temporary(self):
        path = self.font("NoctuaIosevka-Regular.otf", cff=True)
        before = snapshot(self.dir)
        with mock.patch.object(tool.os, "fsync",
                               side_effect=OSError("disk full")):
            status, _, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 1)
        self.assertIn("disk full", err)
        self.assertIn("nothing was changed", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_a_damaged_font_stops_the_batch_before_any_font_moves(self):
        # Found by review: only the WOFF2 rebuild decompiles 'glyf' in full,
        # and it used to fail after the fonts before it were renamed, with a
        # raw traceback. It is now built before anything is moved.
        good, _ = self.pair("NoctuaIosevka-A")
        bad, _ = self.pair("NoctuaIosevka-B")
        damage_glyf(bad)
        before = snapshot(self.dir)
        err = self.assertRefusedUnchanged(before, FROM, TO, good, bad,
                                          message="cannot be built from")
        self.assertIn("NoctuaIosevkaCode-B.woff2", err)

    def test_an_unexpected_error_while_moving_is_reported(self):
        ttf, _ = self.pair()
        before = snapshot(self.dir)
        with mock.patch.object(tool, "commit",
                               side_effect=ValueError("unexpected")):
            status, _, err = run_tool(FROM, TO, ttf)
        self.assertEqual(status, 1)
        self.assertIn("error: ValueError: unexpected", err)
        self.assertIn("stopped at", err)
        self.assertEqual(snapshot(self.dir), before)

    def test_the_stop_message_counts_the_files_handled(self):
        # A pair, then a font whose move fails: two files were handled.
        ttf, web = self.pair()
        other = self.font("NoctuaIosevka-Bold.ttf")
        real_commit_job = tool.commit_job

        def fail_on_other(job):
            if job.source == other:
                raise OSError("simulated failure")
            real_commit_job(job)

        with mock.patch.object(tool, "commit_job", side_effect=fail_on_other):
            status, out, err = run_tool(FROM, TO, ttf, other)
        self.assertEqual(status, 1)
        self.assertIn("the 2 file(s) reported above were handled", err)
        self.assertEqual(out.count(" -> "), 2, out)
        self.assertEqual(sorted(snapshot(self.dir)),
                         [other.name, "NoctuaIosevkaCode-Regular.ttf",
                          "NoctuaIosevkaCode-Regular.woff2"])

    def test_a_move_that_fails_half_way_through_a_pair_says_so(self):
        # The .ttf is moved into place, its web copy's move fails.
        ttf, web = self.pair()
        real_replace = os.replace
        calls = []

        def replace_once(src, dst):
            calls.append(dst)
            if len(calls) > 1:
                raise OSError("simulated failure")
            real_replace(src, dst)

        with mock.patch.object(tool.os, "replace", side_effect=replace_once):
            status, _, err = run_tool(FROM, TO, ttf)
        self.assertEqual(status, 1)
        self.assertIn("error: simulated failure", err)
        self.assertIn(f"{ttf}: handled only in part: "
                      "NoctuaIosevkaCode-Regular.ttf already written", err)
        self.assertIn("the 0 file(s) reported above were handled", err)
        self.assertEqual(sorted(snapshot(self.dir)), sorted(
            [ttf.name, web.name, "NoctuaIosevkaCode-Regular.ttf"]))

    def test_an_interruption_between_files_leaves_only_whole_fonts(self):
        ttf, web = self.pair()
        before = snapshot(self.dir)
        real_replace = os.replace
        calls = []

        def replace_once(src, dst):
            calls.append(dst)
            if len(calls) > 1:
                raise KeyboardInterrupt
            real_replace(src, dst)

        with mock.patch.object(tool.os, "replace", side_effect=replace_once):
            with self.assertRaises(KeyboardInterrupt):
                with contextlib.redirect_stdout(io.StringIO()):
                    tool.main([FROM, TO, str(ttf)])
        now = snapshot(self.dir)
        self.assertEqual(sorted(now), sorted(
            [ttf.name, web.name, "NoctuaIosevkaCode-Regular.ttf"]))
        self.assertEqual(now[ttf.name], before[ttf.name])
        self.assertEqual(now[web.name], before[web.name])
        self.assertEqual(identifier(self.dir / "NoctuaIosevkaCode-Regular.ttf",
                                    1), TO)
        # The rerun names the clash instead of overwriting anything.
        status, _, err = run_tool(FROM, TO, ttf)
        self.assertEqual(status, 1)
        self.assertIn("already exists", err)

    def test_an_interruption_while_building_leaves_no_temporary(self):
        first, _ = self.pair("NoctuaIosevka-A")
        second, _ = self.pair("NoctuaIosevka-B")
        before = snapshot(self.dir)
        real_font_bytes = tool.font_bytes
        calls = []

        def interrupt_third(font, woff2=False):
            calls.append(woff2)
            if len(calls) == 3:
                raise KeyboardInterrupt
            return real_font_bytes(font, woff2)

        with mock.patch.object(tool, "font_bytes",
                               side_effect=interrupt_third):
            with self.assertRaises(KeyboardInterrupt):
                with contextlib.redirect_stdout(io.StringIO()):
                    tool.main([FROM, TO, str(first), str(second)])
        self.assertEqual(snapshot(self.dir), before)

    def test_an_interrupt_just_after_a_move_keeps_the_moved_font(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        real_replace = os.replace

        def replace_then_interrupt(src, dst):
            real_replace(src, dst)
            raise KeyboardInterrupt

        with mock.patch.object(tool.os, "replace",
                               side_effect=replace_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):
                with contextlib.redirect_stdout(io.StringIO()):
                    tool.main([FROM, TO, str(path)])
        renamed = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        self.assertEqual(sorted(snapshot(self.dir)),
                         sorted([path.name, renamed.name]))
        self.assertEqual(identifier(renamed, 1), TO)
        self.assertEqual(identifier(path, 1), FROM)

    def test_permissions_are_kept(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        os.chmod(path, 0o640)
        self.assertEqual(run_tool(FROM, TO, path)[0], 0)
        renamed = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        if os.name == "posix":
            self.assertEqual(os.stat(renamed).st_mode & 0o777, 0o640)

    @unittest.skipUnless(POSIX_USER, "needs POSIX permissions, not root")
    def test_a_read_only_font_is_refused(self):
        path = self.font("NoctuaIosevka-Regular.ttf")
        os.chmod(path, 0o444)
        before = snapshot(self.dir)
        self.assertRefusedUnchanged(before, FROM, TO, path,
                                    message="read-only")


@unittest.skipUnless(REAL_FONT.is_file() and REAL_FONT.stat().st_size > 4096,
                     "the real Noctua Iosevka font is not present")
class RealFontTest(TempDirTestCase):
    """The three defects, on a copy of a real font (never the original)."""

    def test_real_font_round_trip_and_idempotence(self):
        path = self.dir / REAL_FONT.name
        shutil.copyfile(REAL_FONT, path)
        original_records = name_records(path)
        original_postscript = identifier(path, 6)
        status, out, err = run_tool(FROM, TO, path)
        self.assertEqual(status, 0, err)
        self.assertNotIn("note:", out)
        renamed = self.dir / "NoctuaIosevkaCode-Regular.ttf"
        self.assertEqual(identifier(renamed, 1), TO)
        # Iosevka's hyphenated PostScript name follows the family.
        self.assertEqual(identifier(renamed, 6), original_postscript.replace(
            "Noctua-Iosevka", "Noctua-Iosevka-Code"))
        first = snapshot(self.dir)
        self.assertEqual(run_tool(FROM, TO, renamed)[0], 0)
        self.assertEqual(snapshot(self.dir), first)
        self.assertEqual(run_tool(TO, FROM, renamed)[0], 0)
        self.assertEqual(name_records(path), original_records)
        a, b = tables(REAL_FONT), tables(path)
        for tag in a:
            if tag not in ("name", "head"):
                self.assertEqual(a[tag], b[tag], tag)


@unittest.skipUnless(REAL_PAIR.is_file() and REAL_PAIR.stat().st_size > 4096
                     and REAL_PAIR.with_suffix(".woff2").is_file(),
                     "the real Noto Music pair is not present")
class RealPairTest(TempDirTestCase):
    def test_a_real_pair_is_renamed_together(self):
        for source in (REAL_PAIR, REAL_PAIR.with_suffix(".woff2")):
            shutil.copyfile(source, self.dir / source.name)
        status, out, err = run_tool("Noto Music", "Noto Music Test",
                                    *sorted(self.dir.iterdir()))
        self.assertEqual(status, 0, err)
        ttf = self.dir / "NotoMusicTest-Regular.ttf"
        web = self.dir / "NotoMusicTest-Regular.woff2"
        self.assertEqual(sorted(snapshot(self.dir)), [ttf.name, web.name])
        self.assertEqual(identifier(ttf, 1), "Noto Music Test")
        self.assertEqual(name_records(web), name_records(ttf))


if __name__ == "__main__":
    unittest.main()
