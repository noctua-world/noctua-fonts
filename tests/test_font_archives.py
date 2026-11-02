"""Tests for font-archives.py.

The tool never parses a font, so the "fonts" in the synthetic trees are
deterministic bytes. The fetch tests download from a local http.server bound to
127.0.0.1; nothing reaches the network. The RealRepository tests read the real
font-archives.json, .gitignore, .gitattributes, licence files and SHA256SUMS;
they never need the built fonts. A missing one is a failure, not a skip.
"""

import contextlib
import functools
import hashlib
import http.server
import importlib.util
import io
import json
import os
import random
import shutil
import stat
import struct
import sys
import tempfile
import threading
import unittest
import urllib.request
import warnings
import zipfile
import zlib
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "font-archives.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("font_archives_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fa = _load_tool()


def _can_symlink():
    with tempfile.TemporaryDirectory(prefix="font-archives-probe-") as tmp:
        try:
            os.symlink(tmp, Path(tmp) / "link", target_is_directory=True)
        except (OSError, NotImplementedError, AttributeError):
            return False
        return True


needs_symlinks = unittest.skipUnless(_can_symlink(), "cannot create symbolic links here")

# ---------------------------------------------------------------------------
# A synthetic repository

FONT_SIZES = {
    "noctua-iosevka/TTF/NoctuaIosevka-Regular.ttf": 4000,
    "noctua-iosevka/TTF/NoctuaIosevka-Bold.ttf": 3000,
    "noctua-iosevka/TTF/NoctuaIosevka-SemiBold.ttf": 2000,  # normal width, not SemiCondensed
    "noctua-iosevka/TTF/NoctuaIosevka-Condensed.ttf": 2500,
    "noctua-iosevka/TTF/NoctuaIosevka-SemiCondensedBold.ttf": 2500,
    "noctua-iosevka/WOFF2/NoctuaIosevka-Regular.woff2": 1500,
    "noctua-iosevka/WOFF2/NoctuaIosevka-Bold.woff2": 1400,
    "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf": 3500,
    "noctua-noto/NotoSans-VariableFont_wdth,wght.woff2": 1200,
    "symbols-nerd-font/SymbolsNerdFont-Regular.ttf": 1800,
}
LICENSES = {
    "noctua-iosevka/licenses/OFL.txt": b"SIL Open Font License 1.1 (Iosevka)\n" * 30,
    "noctua-noto/licenses/OFL-Noto.txt": b"SIL Open Font License 1.1 (Noto)\n" * 30,
    "symbols-nerd-font/licenses/LICENSE.txt": b"MIT License (Nerd Fonts)\n" * 30,
}
OTHER_FILES = {
    "README.md": b"# fonts\n",
    "noctua-iosevka/private-build-plans.toml": b"[buildPlans]\n",
    "docs/fonts/NoctuaIosevka-Subset.woff2": b"a subset font for the site",  # never listed
}
IOSEVKA_OFL = ["noctua-iosevka/licenses/OFL.txt"]
CONFIG = {
    "repository": "example/fonts",
    "tag": "v0.0.1",
    "archives": [
        {"name": "iosevka-ttf-normal.zip", "description": "Normal width.",
         "include": ["noctua-iosevka/TTF/NoctuaIosevka-*.ttf"],
         "exclude": ["noctua-iosevka/TTF/NoctuaIosevka-Condensed*.ttf",
                     "noctua-iosevka/TTF/NoctuaIosevka-SemiCondensed*.ttf"],
         "licenses": IOSEVKA_OFL},
        {"name": "iosevka-ttf-condensed.zip", "description": "Condensed.",
         "include": ["noctua-iosevka/TTF/NoctuaIosevka-Condensed*.ttf"], "licenses": IOSEVKA_OFL},
        {"name": "iosevka-ttf-semicondensed.zip", "description": "Semi-condensed.",
         "include": ["noctua-iosevka/TTF/NoctuaIosevka-SemiCondensed*.ttf"], "licenses": IOSEVKA_OFL},
        {"name": "iosevka-woff2.zip", "description": "WOFF2.",
         "include": ["noctua-iosevka/WOFF2/*.woff2"], "licenses": IOSEVKA_OFL},
        {"name": "noto.zip", "description": "Noto.",
         "include": ["noctua-noto/*.ttf", "noctua-noto/*.woff2"],
         "licenses": ["noctua-noto/licenses/OFL-Noto.txt"]},
        {"name": "symbols.zip", "description": "Symbols.",
         "include": ["symbols-nerd-font/*.ttf", "symbols-nerd-font/*.woff2"],
         "licenses": ["symbols-nerd-font/licenses/LICENSE.txt"]},
    ],
}
NOTO_TTF = "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf"
NOTO_WOFF2 = "noctua-noto/NotoSans-VariableFont_wdth,wght.woff2"
NOTO_LICENSE = "noctua-noto/licenses/OFL-Noto.txt"
SYMBOLS_TTF = "symbols-nerd-font/SymbolsNerdFont-Regular.ttf"


def font_bytes(rel, size):
    """Deterministic fake font: half compressible text, half pseudo-random bytes."""
    half = size // 2
    text = (rel.encode() * (half // len(rel) + 1))[:half]
    return text + random.Random(rel).randbytes(size - half)


def table_like_bytes():
    """About 30 KB of table-tag text: zlib deflates it to different sizes at levels 6 and 9."""
    words = [b"glyf", b"loca", b"hmtx", b"cmap", b"kern", b"GSUB", b"GPOS", b"name", b"post", b"head"]
    rng = random.Random("level-check")
    return b" ".join(rng.choice(words) for _ in range(6000))


def raw_deflate_size(data, level):
    compressor = zlib.compressobj(level, zlib.DEFLATED, -15)
    return len(compressor.compress(data) + compressor.flush())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_file(root, rel, data):
    path = Path(root).joinpath(*rel.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def make_tree(root, fonts=True, manifest=True, config=None):
    for rel, data in {**LICENSES, **OTHER_FILES}.items():
        write_file(root, rel, data)
    write_file(root, fa.CONFIG_NAME, json.dumps(CONFIG if config is None else config).encode())
    if fonts:
        for rel, size in FONT_SIZES.items():
            write_file(root, rel, font_bytes(rel, size))
    if manifest:
        fa.write_manifest(root)
    return Path(root)


def snapshot(root):
    """Every file under `root` with its bytes, to prove that a refusal changed nothing."""
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fa.main([str(a) for a in args])
    return code, out.getvalue(), err.getvalue()


def zip_records(data):
    """[(name, central header offset, local header offset)] of every entry of a zip."""
    eocd = data.rindex(b"PK\x05\x06")
    count, _, offset = struct.unpack_from("<HLL", data, eocd + 10)
    records = []
    for _ in range(count):
        assert data[offset:offset + 4] == b"PK\x01\x02"
        name_length, extra_length, comment_length = struct.unpack_from("<3H", data, offset + 28)
        local = struct.unpack_from("<L", data, offset + 42)[0]
        records.append((data[offset + 46:offset + 46 + name_length].decode("latin-1"), offset, local))
        offset += 46 + name_length + extra_length + comment_length
    return records


def patch_zip(data, name, flags=0, version=None, central_name_byte=None, local_name_byte=None):
    """Edit the headers of the entry `name` the way zipfile would never write them.

    flags are ORed into the general-purpose bits of both headers; version
    replaces the central "version needed to extract"; a name byte replaces the
    first byte of the name in the central or the local header.
    """
    out = bytearray(data)
    for entry, central, local in zip_records(data):
        if entry != name:
            continue
        for at in (central + 8, local + 6):
            struct.pack_into("<H", out, at, struct.unpack_from("<H", out, at)[0] | flags)
        if version is not None:
            struct.pack_into("<H", out, central + 6, version)
        if central_name_byte is not None:
            out[central + 46] = central_name_byte
        if local_name_byte is not None:
            out[local + 30] = local_name_byte
        return bytes(out)
    raise KeyError(name)


class TempTree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="font-archives-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "repo"
        self.root.mkdir()

    def restrict(self, path, mode):
        """chmod `path` until the test ends; skip when that does not restrict this user."""
        path = Path(path)
        original = stat.S_IMODE(os.stat(path).st_mode)
        is_dir = path.is_dir()
        os.chmod(path, mode)
        self.addCleanup(os.chmod, path, original)  # runs before the temporary tree is removed
        try:
            if is_dir:
                os.listdir(path)
            else:
                open(path, "rb").close()
        except PermissionError:
            return
        self.skipTest("file permissions do not restrict this user here (root, or Windows)")


# ---------------------------------------------------------------------------
# Paths, globs and font-archives.json

class PathRulesTest(unittest.TestCase):
    def test_accepts_repository_paths(self):
        for path in (NOTO_TTF, "noctua-iosevka/TTF/NoctuaIosevka-Bold.ttf", "a/b.txt"):
            self.assertIsNone(fa.path_problem(path), path)

    def test_refuses_unsafe_or_unportable_paths(self):
        cases = {
            "": "empty",
            "/etc/passwd": "absolute",
            "C:/fonts/x.ttf": "drive letter",
            "noctua-noto\\x.ttf": "backslash",
            "../x.ttf": "'..'",
            "noctua-noto/../../x.ttf": "'..'",
            "noctua-noto/./x.ttf": "'.'",
            "noctua-noto//x.ttf": "empty segment",
            "noctua-noto/x/": "empty segment",
            "noctua-noto/x\x00.ttf": "not portable",
            "noctua-noto/x:y.ttf": "not portable",
            "noctua-noto/CON.ttf": "reserves for a device",
            "noctua-noto/x.ttf.": "dot or a space",
            "noctua-noto/\udcff.ttf": "not valid UTF-8",  # what os.fsdecode makes of a byte 0xFF
        }
        for path, fragment in cases.items():
            with self.subTest(path=path):
                self.assertIn(fragment, fa.path_problem(path) or "")

    def test_star_never_crosses_a_slash_and_case_matters(self):
        self.assertTrue(fa.glob_match("noctua-noto/*.ttf", "noctua-noto/x.ttf"))
        self.assertFalse(fa.glob_match("noctua-noto/*.ttf", "noctua-noto/sub/x.ttf"))
        self.assertFalse(fa.glob_match("noctua-noto/*", "noctua-noto/sub/x.ttf"))
        self.assertFalse(fa.glob_match("noctua-noto/*.ttf", "noctua-noto/X.TTF"))

    def test_manifest_paths_must_be_fonts_inside_the_font_folders(self):
        self.assertIn("is not inside", fa.manifest_path_problem("docs/fonts/x.woff2"))
        self.assertIn("is not a", fa.manifest_path_problem("noctua-noto/licenses/OFL.txt"))
        self.assertIsNone(fa.manifest_path_problem(NOTO_WOFF2))

    def test_temporary_names_are_never_fonts(self):
        for name in ("X.ttf", "X.TTF", "X.woff2", "X.Woff2"):
            self.assertTrue(fa.is_font_name(name), name)
        for name in (".X.ttf.0123456789abcdef" + fa.TEMP_SUFFIX,
                     ".X.ttf.0123456789abcdef" + fa.BACKUP_SUFFIX, ".SHA256SUMS.0123456789abcdef.tmp"):
            self.assertFalse(fa.is_font_name(name), name)


class ConfigTest(unittest.TestCase):
    def parse(self, obj):
        return fa.parse_config(json.dumps(obj).encode())

    def test_the_synthetic_config_is_valid(self):
        config = self.parse(CONFIG)
        self.assertEqual(len(config.archives), 6)
        self.assertEqual(config.archive("noto.zip").licenses, (NOTO_LICENSE,))

    def test_refuses_duplicate_keys(self):
        with self.assertRaisesRegex(fa.FontArchivesError, "duplicate key"):
            fa.parse_config(b'{"repository": "a/b", "repository": "c/d", "tag": "v1", "archives": []}')

    def test_refuses_unsafe_values(self):
        def broken(**changes):
            archive = dict(CONFIG["archives"][0], **changes)
            return dict(CONFIG, archives=[archive])
        cases = [
            (dict(CONFIG, extra=1), "unknown keys"),
            (dict(CONFIG, tag="../v1"), "'tag'"),
            (dict(CONFIG, repository="not a repository"), "'repository'"),
            (broken(name="../escape.zip"), "'name'"),
            (broken(name="Archive.tar"), "'name'"),
            (broken(include=["noctua-noto/../*.ttf"]), "'..'"),
            (broken(include=["/noctua-noto/*.ttf"]), "absolute"),
            (broken(include=["noctua-noto/**/*.ttf"]), "'**'"),
            (broken(include=[]), "non-empty"),
            (broken(licenses=["/etc/passwd"]), "absolute"),
            (broken(licenses=["noctua-noto/x.ttf"]), "is a font"),
            (dict(CONFIG, archives=[CONFIG["archives"][0]] * 2), "listed twice"),
        ]
        for obj, fragment in cases:
            with self.subTest(fragment=fragment):
                with self.assertRaises(fa.FontArchivesError) as caught:
                    self.parse(obj)
                self.assertIn(fragment, str(caught.exception))


# ---------------------------------------------------------------------------
# manifest

class ManifestTest(TempTree):
    def manifest_bytes(self):
        return (self.root / "SHA256SUMS").read_bytes()

    def test_format_is_byte_exact(self):
        make_tree(self.root)
        expected = "".join(f"{sha(font_bytes(rel, FONT_SIZES[rel]))}  {rel}\n"
                           for rel in sorted(FONT_SIZES)).encode("utf-8")
        self.assertEqual(self.manifest_bytes(), expected)

    def test_lists_only_built_fonts_in_the_three_folders(self):
        make_tree(self.root)
        listed = fa.read_manifest(self.root)
        self.assertEqual(sorted(listed), sorted(FONT_SIZES))
        self.assertNotIn("docs/fonts/NoctuaIosevka-Subset.woff2", listed)

    def test_parse_round_trips(self):
        entries = {rel: sha(font_bytes(rel, size)) for rel, size in FONT_SIZES.items()}
        self.assertEqual(fa.parse_manifest(fa.format_manifest(entries)), entries)

    def test_cli_writes_and_compares_with_the_previous_manifest(self):
        make_tree(self.root)
        write_file(self.root, NOTO_TTF, b"rebuilt")
        code, out, _ = run_cli("--root", self.root, "manifest")
        self.assertEqual(code, 0)
        self.assertIn(f"wrote SHA256SUMS: {len(FONT_SIZES)} built fonts", out)
        self.assertIn("0 added, 0 removed, 1 changed", out)
        self.assertEqual(fa.read_manifest(self.root)[NOTO_TTF], sha(b"rebuilt"))

    def test_refuses_to_drop_a_listed_font_that_is_missing(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        (self.root / NOTO_TTF).unlink()
        code, out, err = run_cli("--root", self.root, "manifest")
        self.assertEqual(code, 1, out)
        self.assertIn("1 font(s) it lists are not in the tree", err)
        self.assertIn(NOTO_TTF, err)
        self.assertIn("--remove-missing", err)
        self.assertEqual(self.manifest_bytes(), before)

    def test_remove_missing_drops_it_on_purpose(self):
        make_tree(self.root)
        (self.root / NOTO_TTF).unlink()
        code, out, _ = run_cli("--root", self.root, "manifest", "--remove-missing")
        self.assertEqual(code, 0)
        self.assertIn("0 added, 1 removed, 0 changed", out)
        self.assertNotIn(NOTO_TTF, fa.read_manifest(self.root))

    def test_a_rename_needs_remove_missing(self):
        make_tree(self.root)
        old = self.root / NOTO_TTF
        old.rename(old.with_name("Renamed-" + old.name))
        with self.assertRaisesRegex(fa.FontArchivesError, "not in the tree"):
            fa.write_manifest(self.root)
        entries, _ = fa.write_manifest(self.root, remove_missing=True)
        self.assertNotIn(NOTO_TTF, entries)
        self.assertIn(str(Path(NOTO_TTF).with_name("Renamed-" + old.name).as_posix()), entries)

    def test_refuses_an_empty_tree(self):
        make_tree(self.root, fonts=False, manifest=False)
        code, _, err = run_cli("--root", self.root, "manifest")
        self.assertEqual(code, 1)
        self.assertIn("refusing to write an empty SHA256SUMS", err)
        self.assertFalse((self.root / "SHA256SUMS").exists())

    @needs_symlinks
    def test_refuses_a_symbolic_link(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        os.symlink(self.root / NOTO_TTF, self.root / "noctua-noto" / "Link.ttf")
        with self.assertRaisesRegex(fa.FontArchivesError, "symbolic link"):
            fa.write_manifest(self.root)
        self.assertEqual(self.manifest_bytes(), before)

    @needs_symlinks
    def test_refuses_a_symbolic_link_to_a_directory(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        elsewhere = self.tmp / "elsewhere"
        write_file(elsewhere, "Hidden.ttf", b"a font outside the repository")
        os.symlink(elsewhere, self.root / "noctua-noto" / "linked", target_is_directory=True)
        with self.assertRaisesRegex(fa.FontArchivesError, "noctua-noto/linked: is a symbolic link to a directory"):
            fa.write_manifest(self.root)
        self.assertEqual(self.manifest_bytes(), before)

    def test_refuses_names_that_differ_only_in_case(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        twin = self.root / "noctua-noto" / Path(NOTO_TTF).name.lower()
        twin.write_bytes(b"another font")
        if sum(1 for p in twin.parent.iterdir() if p.name.lower() == twin.name) < 2:
            self.skipTest("this file system ignores case")
        with self.assertRaisesRegex(fa.FontArchivesError, "differ only in case"):
            fa.write_manifest(self.root)
        self.assertEqual(self.manifest_bytes(), before)

    def test_an_upper_case_suffix_is_still_a_built_font(self):
        make_tree(self.root, manifest=False)
        write_file(self.root, "noctua-noto/Shouting.TTF", b"x")
        self.assertIn("noctua-noto/Shouting.TTF", fa.discover_fonts(self.root).fonts)

    @unittest.skipUnless(sys.platform.startswith("linux"), "needs a file system that stores any bytes")
    def test_a_name_that_is_not_utf8_is_a_problem(self):
        make_tree(self.root, manifest=False)
        try:
            with open(os.fsencode(self.root / "noctua-noto") + b"/\xff.ttf", "wb") as handle:
                handle.write(b"x")
        except OSError:
            self.skipTest("this file system refuses names that are not UTF-8")
        problems = fa.discover_fonts(self.root).problems
        self.assertTrue(any("not valid UTF-8" in p for p in problems), problems)

    def test_an_unreadable_folder_is_a_refusal_not_an_omission(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        self.restrict(self.root / "noctua-iosevka" / "WOFF2", 0o000)
        code, out, err = run_cli("--root", self.root, "manifest")
        self.assertEqual(code, 1, out)
        self.assertIn("noctua-iosevka/WOFF2: cannot be listed", err)
        self.assertEqual(self.manifest_bytes(), before)

    def test_an_unreadable_font_is_a_refusal(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        self.restrict(self.root / NOTO_TTF, 0o000)
        code, _, err = run_cli("--root", self.root, "manifest")
        self.assertEqual(code, 1)
        self.assertIn(f"{NOTO_TTF}: cannot be read", err)
        self.assertEqual(self.manifest_bytes(), before)

    def test_writes_through_a_temporary_file(self):
        make_tree(self.root)
        before = self.manifest_bytes()
        write_file(self.root, NOTO_TTF, b"rebuilt")
        with mock.patch.object(fa.os, "replace", side_effect=OSError(28, "No space left on device")):
            code, _, err = run_cli("--root", self.root, "manifest")
        self.assertEqual(code, 1)
        self.assertIn("error: [Errno 28] No space left on device", err)
        self.assertEqual(self.manifest_bytes(), before)  # the old file, whole
        self.assertEqual([p.name for p in self.root.iterdir() if p.name.endswith(".tmp")], [])

    def test_parse_refuses_what_manifest_would_never_write(self):
        good = f"{'a' * 64}  {NOTO_TTF}\n{'b' * 64}  {NOTO_WOFF2}\n"
        self.assertEqual(len(fa.parse_manifest(good.encode())), 2)
        cases = {
            "": "empty",
            good.replace("\n", "\r\n", 1): "carriage return",  # CRLF on one line only
            good.replace("\n", "\r\r\n"): "carriage return",
            good[:-1]: "newline",
            f"{'b' * 64}  {NOTO_WOFF2}\n{'a' * 64}  {NOTO_TTF}\n": "out of order",
            f"{'a' * 64}  {NOTO_TTF}\n{'a' * 64}  {NOTO_TTF}\n": "twice",
            f"{'A' * 64}  {NOTO_TTF}\n": "line 1",
            f"{'a' * 64} {NOTO_TTF}\n": "line 1",
            f"{'a' * 64}  noctua-noto/../../etc/x.ttf\n": "'..'",
            f"{'a' * 64}  /noctua-noto/x.ttf\n": "absolute",
            f"{'a' * 64}  docs/x.woff2\n": "is not inside",
            f"{'a' * 64}  noctua-noto/A.ttf\n{'a' * 64}  noctua-noto/a.ttf\n": "differ only in case",
        }
        for text, fragment in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(fa.FontArchivesError) as caught:
                    fa.parse_manifest(text.encode())
                self.assertIn(fragment, str(caught.exception))

    def test_parse_accepts_git_converting_every_line_to_crlf(self):
        good = f"{'a' * 64}  {NOTO_TTF}\n{'b' * 64}  {NOTO_WOFF2}\n"
        self.assertEqual(fa.parse_manifest(good.replace("\n", "\r\n").encode()),
                         fa.parse_manifest(good.encode()))


# ---------------------------------------------------------------------------
# verify

class VerifyTest(TempTree):
    def setUp(self):
        super().setUp()
        make_tree(self.root)

    def verify(self, *extra):
        return run_cli("--root", self.root, "verify", *extra)

    def test_ok(self):
        code, out, _ = self.verify()
        self.assertEqual(code, 0)
        self.assertIn(f"{len(FONT_SIZES)} match, 0 differ, 0 missing", out)
        self.assertTrue(out.rstrip().endswith("OK"))

    def test_mismatch(self):
        write_file(self.root, NOTO_TTF, b"tampered")
        code, out, _ = self.verify()
        self.assertEqual(code, 1)
        self.assertIn(f"MISMATCH  {NOTO_TTF}", out)
        self.assertEqual(self.verify("--allow-missing")[0], 1)

    def test_missing(self):
        (self.root / NOTO_TTF).unlink()
        code, out, _ = self.verify()
        self.assertEqual(code, 1)
        self.assertIn(f"MISSING   {NOTO_TTF}", out)

    def test_allow_missing_checks_only_what_is_present(self):
        (self.root / NOTO_TTF).unlink()
        (self.root / NOTO_WOFF2).unlink()
        code, out, _ = self.verify("--allow-missing")
        self.assertEqual(code, 0)
        self.assertIn("2 missing (allowed)", out)
        self.assertIn(f"{len(FONT_SIZES) - 2} match", out)

    def test_a_built_font_absent_from_the_manifest_is_an_error(self):
        write_file(self.root, "symbols-nerd-font/Unlisted.woff2", b"new")
        for extra in ((), ("--allow-missing",)):
            code, out, _ = self.verify(*extra)
            self.assertEqual(code, 1)
            self.assertIn("UNLISTED  symbols-nerd-font/Unlisted.woff2", out)

    def test_no_manifest(self):
        (self.root / "SHA256SUMS").unlink()
        code, _, err = self.verify()
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_a_manifest_git_converted_to_crlf_still_verifies(self):
        data = (self.root / "SHA256SUMS").read_bytes()
        (self.root / "SHA256SUMS").write_bytes(data.replace(b"\n", b"\r\n"))
        self.assertEqual(self.verify()[0], 0)

    def test_a_folder_that_cannot_be_listed_fails(self):
        write_file(self.root, "noctua-iosevka/WOFF2/Unlisted.woff2", b"not in SHA256SUMS")
        self.restrict(self.root / "noctua-iosevka" / "WOFF2", 0o111)  # traversable, not listable
        code, out, _ = self.verify()
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM   noctua-iosevka/WOFF2: cannot be listed", out)

    def test_an_unreadable_font_is_a_problem_not_a_traceback(self):
        self.restrict(self.root / NOTO_TTF, 0o000)
        code, out, _ = self.verify()
        self.assertEqual(code, 1)
        self.assertIn(f"PROBLEM   {NOTO_TTF}: cannot be read", out)
        self.assertIn(f"{len(FONT_SIZES) - 1} match", out)

    @needs_symlinks
    def test_a_listed_font_that_is_a_link_is_never_a_match(self):
        copy = self.tmp / "copy.ttf"
        shutil.copyfile(self.root / NOTO_TTF, copy)  # the right bytes, behind a link
        (self.root / NOTO_TTF).unlink()
        os.symlink(copy, self.root / NOTO_TTF)
        code, out, _ = self.verify()
        self.assertEqual(code, 1)
        self.assertIn(f"{NOTO_TTF}: is a symbolic link", out)
        self.assertNotIn(f"{NOTO_TTF}: is not a regular file", out)  # one problem, reported once
        self.assertIn(f"{len(FONT_SIZES) - 1} match", out)


# ---------------------------------------------------------------------------
# list and pack

class ListTest(TempTree):
    def test_counts_and_coverage(self):
        make_tree(self.root)
        code, out, _ = run_cli("--root", self.root, "list")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"noto\.zip\s+2\s")
        self.assertRegex(out, r"iosevka-ttf-normal\.zip\s+3\s")
        self.assertIn(f"every built font present ({len(FONT_SIZES)}) belongs to exactly one archive", out)

    def test_reports_an_orphan(self):
        make_tree(self.root)
        write_file(self.root, "noctua-iosevka/OTF/NoctuaIosevka-Regular.ttf", b"x")
        code, out, _ = run_cli("--root", self.root, "list")
        self.assertEqual(code, 1)
        self.assertIn("1 built fonts belong to no archive", out)

    def test_a_folder_that_cannot_be_listed_is_a_problem(self):
        make_tree(self.root)
        self.restrict(self.root / "noctua-iosevka" / "WOFF2", 0o000)
        code, out, _ = run_cli("--root", self.root, "list")
        self.assertEqual(code, 1)
        self.assertIn("noctua-iosevka/WOFF2: cannot be listed", out)


class PackTest(TempTree):
    def setUp(self):
        super().setUp()
        make_tree(self.root)
        self.config = fa.load_config(self.root)

    def pack(self, out):
        return fa.pack(self.root, self.config, self.tmp / out)

    def test_packing_twice_is_byte_identical(self):
        first = self.pack("one")
        for rel in FONT_SIZES:  # timestamps must not leak into the archives
            os.utime(self.root / rel, (1_700_000_000, 1_700_000_000))
        second = self.pack("two")
        self.assertEqual(first, second)
        names = sorted(a["name"] for a in CONFIG["archives"])
        self.assertEqual(sorted(p.name for p in (self.tmp / "one").iterdir()), sorted(names + ["SHA256SUMS"]))
        for name in names + ["SHA256SUMS"]:
            with self.subTest(name=name):
                self.assertEqual((self.tmp / "one" / name).read_bytes(), (self.tmp / "two" / name).read_bytes())

    def test_entries_are_sorted_fixed_and_compressed_as_specified(self):
        self.pack("dist")
        with zipfile.ZipFile(self.tmp / "dist" / "iosevka-ttf-normal.zip") as archive:
            infos = archive.infolist()
            self.assertEqual([i.filename for i in infos], sorted([
                "noctua-iosevka/TTF/NoctuaIosevka-Bold.ttf",
                "noctua-iosevka/TTF/NoctuaIosevka-Regular.ttf",
                "noctua-iosevka/TTF/NoctuaIosevka-SemiBold.ttf",
                "noctua-iosevka/licenses/OFL.txt"]))
            for info in infos:
                data = archive.read(info)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, stat.S_IFREG | 0o644)
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.extract_version, fa.ZIP_EXTRACT_VERSION)
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                self.assertEqual(info.extra, b"")
                self.assertEqual(info.compress_size, raw_deflate_size(data, 9))
        with zipfile.ZipFile(self.tmp / "dist" / "iosevka-woff2.zip") as archive:
            kinds = {i.filename: i.compress_type for i in archive.infolist()}
        self.assertEqual(kinds["noctua-iosevka/WOFF2/NoctuaIosevka-Regular.woff2"], zipfile.ZIP_STORED)
        self.assertEqual(kinds["noctua-iosevka/licenses/OFL.txt"], zipfile.ZIP_DEFLATED)

    def test_deflates_at_level_9_not_the_default(self):
        data = table_like_bytes()
        if raw_deflate_size(data, 9) == raw_deflate_size(data, 6):
            self.skipTest("this zlib deflates the sample to the same size at levels 6 and 9")
        write_file(self.root, NOTO_TTF, data)
        fa.write_manifest(self.root)
        self.pack("dist")
        with zipfile.ZipFile(self.tmp / "dist" / "noto.zip") as archive:
            self.assertEqual(archive.getinfo(NOTO_TTF).compress_size, raw_deflate_size(data, 9))

    def test_release_sums_and_extraction_at_the_root_restore_the_layout(self):
        results = self.pack("dist")
        lines = (self.tmp / "dist" / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, [f"{sha((self.tmp / 'dist' / n).read_bytes())}  {n}"
                                 for n in sorted(r[0] for r in results)])
        restored = self.tmp / "restored"
        for name, _, _, _ in results:
            with zipfile.ZipFile(self.tmp / "dist" / name) as archive:
                archive.extractall(restored)
        for rel, size in FONT_SIZES.items():
            self.assertEqual((restored / rel).read_bytes(), font_bytes(rel, size))
        for rel, data in LICENSES.items():
            self.assertEqual((restored / rel).read_bytes(), data)

    def test_an_orphan_fails_coverage(self):
        orphan = "noctua-iosevka/OTF/NoctuaIosevka-Regular.ttf"
        write_file(self.root, orphan, b"x")
        fa.write_manifest(self.root)
        with self.assertRaises(fa.FontArchivesError) as caught:
            self.pack("dist")
        self.assertIn("belong to no archive", str(caught.exception))
        self.assertIn(orphan, str(caught.exception))
        self.assertFalse((self.tmp / "dist").exists())

    def test_a_path_in_two_archives_fails_coverage(self):
        config = json.loads(json.dumps(CONFIG))
        config["archives"].append({"name": "noto-again.zip", "description": "Overlap.",
                                   "include": ["noctua-noto/*.ttf"], "licenses": [NOTO_LICENSE]})
        with self.assertRaises(fa.FontArchivesError) as caught:
            fa.pack(self.root, fa.parse_config(json.dumps(config).encode()), self.tmp / "dist")
        self.assertIn("more than one archive", str(caught.exception))
        self.assertIn(f"{NOTO_TTF}: noto.zip, noto-again.zip", str(caught.exception))

    def test_an_archive_must_stay_under_the_size_limit(self):
        with mock.patch.object(fa, "MAX_ARCHIVE_SIZE", 3000):
            with self.assertRaisesRegex(fa.FontArchivesError, "must be smaller|would reach"):
                self.pack("dist")
        self.assertEqual(list((self.tmp / "dist").iterdir()), [])  # no zip, no .part left

    def test_refuses_a_tree_that_does_not_match(self):
        write_file(self.root, NOTO_TTF, b"tampered")
        with self.assertRaisesRegex(fa.FontArchivesError, "does not match SHA256SUMS"):
            self.pack("dist")
        self.assertFalse((self.tmp / "dist").exists())

    def test_refuses_the_repository_root_as_output(self):
        before = (self.root / "SHA256SUMS").read_bytes()
        with self.assertRaisesRegex(fa.FontArchivesError, "repository root"):
            fa.pack(self.root, self.config, self.root)
        self.assertEqual((self.root / "SHA256SUMS").read_bytes(), before)

    def test_refuses_an_output_path_that_is_a_file(self):
        (self.tmp / "afile").write_bytes(b"x")
        code, _, err = run_cli("--root", self.root, "pack", "--out", self.tmp / "afile")
        self.assertEqual(code, 1)
        self.assertIn("exists and is not a directory", err)
        self.assertEqual((self.tmp / "afile").read_bytes(), b"x")

    def test_refuses_a_font_over_the_cap_fetch_enforces(self):
        with mock.patch.object(fa, "MAX_ENTRY_SIZE", 3000):
            with self.assertRaisesRegex(fa.FontArchivesError, "over the 3000-byte cap fetch enforces"):
                self.pack("dist")
        self.assertFalse((self.tmp / "dist").exists())

    def test_refuses_a_missing_licence(self):
        (self.root / NOTO_LICENSE).unlink()
        with self.assertRaisesRegex(fa.FontArchivesError, f"licence file {NOTO_LICENSE} is missing"):
            self.pack("dist")
        self.assertFalse((self.tmp / "dist").exists())

    def test_refuses_an_archive_with_no_font(self):
        config = json.loads(json.dumps(CONFIG))
        config["archives"].append({"name": "empty.zip", "description": "Nothing matches.",
                                   "include": ["noctua-noto/*.otf"], "licenses": [NOTO_LICENSE]})
        with self.assertRaisesRegex(fa.FontArchivesError, "no font in them: empty.zip"):
            fa.pack(self.root, fa.parse_config(json.dumps(config).encode()), self.tmp / "dist")

    def test_a_font_that_changes_after_verify_is_refused(self):
        real_verify = fa.verify_tree

        def verify_then_rebuild(*args, **kwargs):
            result = real_verify(*args, **kwargs)
            write_file(self.root, NOTO_TTF, b"rebuilt in the meantime")
            return result

        with mock.patch.object(fa, "verify_tree", verify_then_rebuild):
            with self.assertRaisesRegex(fa.FontArchivesError, f"{NOTO_TTF} changed while it was being packed"):
                self.pack("dist")
        self.assertEqual(list((self.tmp / "dist").iterdir()), [])  # every staged zip removed

    def test_cli_defaults_to_dist_under_the_root(self):
        code, out, _ = run_cli("--root", self.root, "pack")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.root / "dist" / "noto.zip").is_file())
        self.assertTrue((self.root / "dist" / "SHA256SUMS").is_file())


class PackSizeLimitTest(TempTree):
    """The 2 GiB guard as it behaves at real scale, where zipfile's own ZIP64 limit is crossed too."""

    def test_crossing_the_limit_is_a_clean_refusal(self):
        write_file(self.root, "noctua-noto/licenses/OFL.txt", b"licence\n")
        config = {"repository": "example/fonts", "tag": "v1", "archives": [
            {"name": "big.zip", "description": "Big.", "include": ["noctua-noto/*.woff2"],
             "licenses": ["noctua-noto/licenses/OFL.txt"]}]}
        write_file(self.root, fa.CONFIG_NAME, json.dumps(config).encode())
        for index in range(8):
            write_file(self.root, f"noctua-noto/F{index}.woff2", font_bytes(f"F{index}", 1000))
        fa.write_manifest(self.root)
        out = self.tmp / "dist"
        # MAX_ARCHIVE_SIZE is 2 GiB and zipfile.ZIP64_LIMIT is 2 GiB - 1: scale both down.
        with mock.patch.object(fa, "MAX_ARCHIVE_SIZE", 5000), mock.patch.object(zipfile, "ZIP64_LIMIT", 4999):
            code, _, err = run_cli("--root", self.root, "pack", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("error: big.zip would reach 5000 bytes", err)
        self.assertEqual(list(out.iterdir()), [])  # no zip, no .part left


# ---------------------------------------------------------------------------
# fetch, against a local server

class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # keep the test output clean
        pass

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/redirect-out/"):
            return self._redirect("http://example.invalid" + self.path)
        if self.path.startswith("/redirect-in/"):
            return self._redirect(self.path[len("/redirect-in"):])
        if self.path.startswith("/no-length/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            self.wfile.write(b"\0" * 10000)
            return None
        return super().do_GET()


class FetchTest(TempTree):
    @classmethod
    def setUpClass(cls):
        cls.served = Path(tempfile.mkdtemp(prefix="font-archives-served-"))
        handler = functools.partial(_Handler, directory=str(cls.served))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.served, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.release_name = self.id().rsplit(".", 1)[-1]
        self.release = self.served / self.release_name
        self.release.mkdir()
        self.base_url = f"{self.origin}/{self.release_name}/"
        self.source = make_tree(self.tmp / "source")
        self.config = fa.load_config(self.source)
        # A fresh clone: everything git tracks (licences, config, SHA256SUMS), no fonts.
        make_tree(self.root, fonts=False, manifest=False)
        shutil.copyfile(self.source / "SHA256SUMS", self.root / "SHA256SUMS")

    def publish(self):
        fa.pack(self.source, self.config, self.release)

    def fetch(self, *names, base_url=None, force=False):
        return fa.fetch(self.root, self.config, names=list(names) or None,
                        base_url=base_url or self.base_url, force=force)

    def craft(self, name, entries):
        """Serve a hand-made zip: entries are (name, bytes) or (name, bytes, external_attr)."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # zipfile warns about the duplicate entries we want
            with zipfile.ZipFile(self.release / name, "w", zipfile.ZIP_DEFLATED) as archive:
                for entry in entries:
                    info = zipfile.ZipInfo("placeholder", date_time=(1980, 1, 1, 0, 0, 0))
                    info.filename = entry[0]  # set after construction, so no normalisation
                    info.create_system = 3
                    info.external_attr = entry[2] if len(entry) > 2 else (stat.S_IFREG | 0o644) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, entry[1])

    def noto_entries(self):
        return [(NOTO_LICENSE, LICENSES[NOTO_LICENSE]),
                (NOTO_TTF, font_bytes(NOTO_TTF, FONT_SIZES[NOTO_TTF])),
                (NOTO_WOFF2, font_bytes(NOTO_WOFF2, FONT_SIZES[NOTO_WOFF2]))]

    def assert_refused(self, fragment, name="noto.zip", force=False):
        before = snapshot(self.root)
        results = fa.fetch(self.root, self.config, names=[name], base_url=self.base_url, force=force)
        self.assertEqual(len(results), 1)
        _, outcome, error = results[0]
        self.assertIsNone(outcome)
        self.assertIn(fragment, error or "")
        self.assertEqual(snapshot(self.root), before)  # nothing written, no .part left
        return error

    def assert_refused_after(self, entries, fragment):
        self.craft("noto.zip", entries)
        return self.assert_refused(fragment)

    def serve_patched(self, name, entry=NOTO_TTF, **change):
        """Serve the packed `name` with the headers of one entry edited (see patch_zip)."""
        published = getattr(self, "_published", None)
        if published is None:
            self.publish()
            published = self._published = {p.name: p.read_bytes() for p in self.release.iterdir()}
        (self.release / name).write_bytes(patch_zip(published[name], entry, **change))

    def flaky_replace(self, fails):
        """Patch os.replace to fail on the calls (numbered from 1) for which `fails(n)` is true.

        That is what Windows does when a font is in use. Returns the patcher.
        """
        real = os.replace
        calls = []

        def replace(src, dst):
            calls.append(dst)
            if fails(len(calls)):
                raise PermissionError(13, "The process cannot access the file because it is "
                                          "being used by another process", str(dst))
            return real(src, dst)

        return mock.patch.object(fa.os, "replace", replace)

    # --- the happy path

    def test_end_to_end_restores_every_font(self):
        self.publish()
        code, out, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url)
        self.assertEqual(code, 0, err)
        self.assertIn(f"{len(CONFIG['archives'])} of {len(CONFIG['archives'])} archives", out)
        for rel, size in FONT_SIZES.items():
            self.assertEqual((self.root / rel).read_bytes(), font_bytes(rel, size))
        self.assertEqual(run_cli("--root", self.root, "verify")[0], 0)
        self.assertEqual([p for p in self.root.rglob("*") if p.name.endswith(".part")], [])
        # Up to date now: fetching again downloads nothing, even with the release gone.
        shutil.rmtree(self.release)
        code, out, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url)
        self.assertEqual(code, 0, err)
        self.assertIn("up to date", out)

    def test_fetches_only_the_named_archives(self):
        self.publish()
        code, _, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url,
                               "--archive", "noto.zip", "--archive", "symbols.zip")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / NOTO_TTF).is_file())
        self.assertTrue((self.root / SYMBOLS_TTF).is_file())
        self.assertFalse((self.root / "noctua-iosevka/TTF").exists())

    def test_unknown_archive(self):
        code, _, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url,
                               "--archive", "nope.zip")
        self.assertEqual(code, 1)
        self.assertIn("no archive named 'nope.zip'", err)

    def test_follows_a_redirect_that_stays_on_loopback(self):
        self.publish()
        [(_, outcome, error)] = self.fetch("noto.zip", base_url=f"{self.origin}/redirect-in/{self.release_name}/")
        self.assertIsNone(error)
        self.assertEqual(outcome.written, [NOTO_TTF, NOTO_WOFF2])

    def test_a_different_existing_font_needs_force(self):
        self.publish()
        write_file(self.root, NOTO_TTF, b"my own rebuild")
        error = self.assert_refused("pass --force")
        self.assertIn(NOTO_TTF, error)
        [(_, outcome, error)] = self.fetch("noto.zip", force=True)
        self.assertIsNone(error)
        self.assertEqual((self.root / NOTO_TTF).read_bytes(), font_bytes(NOTO_TTF, FONT_SIZES[NOTO_TTF]))
        self.assertEqual(outcome.leftovers, [])
        self.assertEqual([p.name for p in self.root.rglob("*.part")], [])  # the original moved aside is gone

    def test_a_manifest_git_converted_to_crlf_still_fetches(self):
        self.publish()
        data = (self.root / "SHA256SUMS").read_bytes()
        (self.root / "SHA256SUMS").write_bytes(data.replace(b"\n", b"\r\n"))
        [(_, outcome, error)] = self.fetch("noto.zip")
        self.assertIsNone(error)
        self.assertEqual(outcome.written, [NOTO_TTF, NOTO_WOFF2])

    # --- refusals of a hostile archive

    def test_refuses_zip_slip(self):
        self.craft("noto.zip", self.noto_entries() + [("noctua-noto/../../evil.ttf", b"x")])
        self.assert_refused("'..' segment")
        self.assertFalse((self.tmp / "evil.ttf").exists())

    def test_refuses_an_absolute_path(self):
        self.craft("noto.zip", self.noto_entries() + [("/tmp/evil.ttf", b"x")])
        self.assert_refused("is absolute")

    def test_refuses_a_drive_letter(self):
        self.craft("noto.zip", self.noto_entries() + [("C:/evil.ttf", b"x")])
        self.assert_refused("drive letter")

    def test_refuses_a_backslash(self):
        self.craft("noto.zip", self.noto_entries() + [("noctua-noto\\..\\..\\evil.ttf", b"x")])
        self.assert_refused("backslash")

    def test_refuses_a_symbolic_link(self):
        entries = self.noto_entries()
        entries[1] = (NOTO_TTF, b"/etc/passwd", (stat.S_IFLNK | 0o777) << 16)
        self.assert_refused_after(entries, "symbolic link")

    def test_refuses_a_non_regular_entry_even_with_the_right_bytes(self):
        for attr in ((stat.S_IFDIR | 0o755) << 16, (stat.S_IFIFO | 0o644) << 16, 0x10):  # 0x10: MS-DOS folder
            with self.subTest(attr=hex(attr)):
                entries = self.noto_entries()
                entries[1] = (NOTO_TTF, entries[1][1], attr)
                self.assert_refused_after(entries, f"entry {NOTO_TTF!r} is not a regular file")

    def test_refuses_an_unexpected_entry(self):
        for extra in ("noctua-noto/Unexpected.ttf", "README.md", "noctua-iosevka/TTF/NoctuaIosevka-Bold.ttf"):
            with self.subTest(extra=extra):
                self.assert_refused_after(self.noto_entries() + [(extra, b"x")], "unexpected")

    def test_refuses_a_duplicate_entry(self):
        entries = self.noto_entries()
        self.assert_refused_after(entries + [entries[1]], "duplicate entry")

    def test_refuses_names_that_differ_only_in_case(self):
        self.assert_refused_after(self.noto_entries() + [(NOTO_TTF.lower(), b"x")], "differ only in case")

    def test_refuses_an_incomplete_archive(self):
        self.assert_refused_after(self.noto_entries()[:2], "lacks 1 expected files")

    def test_refuses_what_pack_never_writes(self):
        cases = [
            (dict(flags=0x01), f"entry {NOTO_TTF!r} is encrypted"),
            (dict(flags=0x40), f"entry {NOTO_TTF!r} is encrypted"),
            (dict(flags=0x20), f"entry {NOTO_TTF!r} holds compressed patched data"),
            (dict(version=45), f"entry {NOTO_TTF!r} needs zip version 4.5"),
        ]
        for change, fragment in cases:
            with self.subTest(change=change):
                self.serve_patched("noto.zip", **change)
                self.assert_refused(fragment)

    @unittest.skipUnless(importlib.util.find_spec("bz2"), "this Python has no bz2 module")
    def test_refuses_another_compression_method(self):
        with zipfile.ZipFile(self.release / "noto.zip", "w") as archive:
            for name, data in self.noto_entries():  # bzip2 would otherwise unpack the right bytes
                archive.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), data,
                                 compress_type=zipfile.ZIP_BZIP2)
        self.assert_refused(f"entry {NOTO_TTF!r} uses compression method {zipfile.ZIP_BZIP2}")

    def test_a_zip_that_zipfile_cannot_read_is_refused_not_a_traceback(self):
        cases = {
            "zip version 11.8": dict(version=118),  # the ZipFile constructor raises NotImplementedError
            "central name not UTF-8": dict(flags=0x800, central_name_byte=0xFF),  # UnicodeDecodeError
            "local name not UTF-8": dict(flags=0x800, local_name_byte=0xFF),
        }
        for label, change in cases.items():
            with self.subTest(label):
                self.serve_patched("noto.zip", **change)
                self.assert_refused("refused, nothing written: not a valid zip archive")

    def test_a_hostile_archive_does_not_stop_the_others(self):
        self.serve_patched("noto.zip", flags=0x800, central_name_byte=0xFF)
        code, out, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url,
                                 "--archive", "noto.zip", "--archive", "symbols.zip")
        self.assertEqual(code, 1)
        self.assertIn("error: noto.zip: refused, nothing written: not a valid zip archive", err)
        self.assertIn("1 of 2 archives fetched or up to date; 1 failed", out)
        self.assertTrue((self.root / SYMBOLS_TTF).is_file())
        self.assertFalse((self.root / NOTO_TTF).exists())

    def test_refuses_a_hash_mismatch_and_keeps_nothing(self):
        entries = self.noto_entries()
        entries[2] = (NOTO_WOFF2, b"not the font SHA256SUMS lists")  # the ttf is staged first
        error = self.assert_refused_after(entries, "hash mismatch")
        self.assertIn(NOTO_WOFF2, error)
        self.assertFalse((self.root / NOTO_TTF).exists())

    def test_a_hash_mismatch_removes_the_directories_it_created(self):
        self.craft("iosevka-woff2.zip", [
            ("noctua-iosevka/WOFF2/NoctuaIosevka-Bold.woff2", b"wrong"),
            ("noctua-iosevka/WOFF2/NoctuaIosevka-Regular.woff2",
             font_bytes("noctua-iosevka/WOFF2/NoctuaIosevka-Regular.woff2", 1500)),
            ("noctua-iosevka/licenses/OFL.txt", LICENSES["noctua-iosevka/licenses/OFL.txt"])])
        self.assert_refused("hash mismatch", name="iosevka-woff2.zip")
        self.assertFalse((self.root / "noctua-iosevka" / "WOFF2").exists())

    def test_refuses_a_licence_that_differs_from_the_tracked_file(self):
        entries = self.noto_entries()
        entries[0] = (NOTO_LICENSE, b"a different licence\n")
        error = self.assert_refused_after(entries, "licence entry")
        self.assertNotIn("line endings", error)
        self.assertEqual((self.root / NOTO_LICENSE).read_bytes(), LICENSES[NOTO_LICENSE])

    def test_a_licence_git_converted_to_crlf_is_refused_with_the_reason(self):
        self.publish()
        write_file(self.root, NOTO_LICENSE, LICENSES[NOTO_LICENSE].replace(b"\n", b"\r\n"))
        error = self.assert_refused(f"the licence entry {NOTO_LICENSE} differs from the tracked file "
                                    "only in its line endings")
        self.assertIn(".gitattributes", error)

    def test_refuses_when_a_licence_is_missing_from_the_tree(self):
        self.publish()
        (self.root / NOTO_LICENSE).unlink()
        self.assert_refused(f"the licence file {NOTO_LICENSE} is missing from the working tree")

    def test_refuses_an_oversized_entry(self):
        self.publish()
        with mock.patch.object(fa, "MAX_ENTRY_SIZE", 1000):
            self.assert_refused("cap per entry")

    def test_refuses_what_is_not_a_zip(self):
        (self.release / "noto.zip").write_bytes(b"this is not a zip archive")
        self.assert_refused("not a valid zip")

    # --- refusals that protect the tree itself

    def test_refuses_a_destination_that_is_a_directory(self):
        self.publish()
        (self.root / NOTO_TTF).mkdir()
        for force in (False, True):
            with self.subTest(force=force):
                self.assert_refused(f"{NOTO_TTF}: exists and is not a regular file", force=force)

    @needs_symlinks
    def test_refuses_a_destination_that_is_a_link_even_with_force(self):
        self.publish()
        victim = self.tmp / "victim.txt"
        victim.write_bytes(b"precious")
        os.symlink(victim, self.root / NOTO_TTF)
        for force in (False, True):
            with self.subTest(force=force):
                self.assert_refused(f"{NOTO_TTF}: exists and is not a regular file", force=force)
        self.assertEqual(victim.read_bytes(), b"precious")

    @needs_symlinks
    def test_refuses_a_font_folder_that_resolves_outside_the_repository(self):
        self.publish()
        outside = self.tmp / "outside"
        outside.mkdir()
        os.symlink(outside, self.root / "noctua-iosevka" / "WOFF2", target_is_directory=True)
        self.assert_refused("refused before downloading", name="iosevka-woff2.zip")
        self.assertEqual(list(outside.iterdir()), [])

    @needs_symlinks
    def test_refuses_a_folder_that_becomes_a_link_during_the_download(self):
        self.publish()
        outside = self.tmp / "outside"
        outside.mkdir()
        real_download = fa.download

        def download_then_swap(url, handle):
            size = real_download(url, handle)
            os.symlink(outside, self.root / "noctua-iosevka" / "WOFF2", target_is_directory=True)
            return size

        with mock.patch.object(fa, "download", download_then_swap):
            [(_, outcome, error)] = self.fetch("iosevka-woff2.zip")
        self.assertIsNone(outcome)
        self.assertIn("resolves outside the repository", error)
        self.assertEqual(list(outside.iterdir()), [])

    def test_a_font_that_appears_during_the_download_is_not_overwritten(self):
        self.publish()
        real_download = fa.download

        def download_then_create(url, handle):
            size = real_download(url, handle)
            write_file(self.root, NOTO_TTF, b"created meanwhile")
            return size

        with mock.patch.object(fa, "download", download_then_create):
            [(_, outcome, error)] = self.fetch("noto.zip")
        self.assertIn(f"{NOTO_TTF} appeared during the download", error)
        self.assertEqual((self.root / NOTO_TTF).read_bytes(), b"created meanwhile")
        self.assertFalse((self.root / NOTO_WOFF2).exists())
        self.assertEqual([p.name for p in self.root.rglob("*.part")], [])

    def test_an_existing_font_that_cannot_be_read_does_not_stop_the_others(self):
        self.publish()
        write_file(self.root, NOTO_TTF, b"my own rebuild")
        self.restrict(self.root / NOTO_TTF, 0o000)
        code, out, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url,
                                 "--archive", "noto.zip", "--archive", "symbols.zip")
        self.assertEqual(code, 1)
        self.assertIn("error: noto.zip: failed before unpacking", err)
        self.assertTrue((self.root / SYMBOLS_TTF).is_file())

    # --- all or nothing, when moving the verified fonts into place fails

    def test_a_failed_move_undoes_the_archive(self):
        self.publish()
        for fail_at in (1, 2):
            with self.subTest(fail_at=fail_at):
                before = snapshot(self.root)
                with self.flaky_replace(lambda n: n == fail_at):
                    [(_, outcome, error)] = self.fetch("noto.zip")
                self.assertIsNone(outcome)
                self.assertIn("The process cannot access the file", error)
                self.assertIn("the tree was left as it was", error)
                self.assertEqual(snapshot(self.root), before)
        [(_, outcome, error)] = self.fetch("noto.zip")  # nothing stuck: a later fetch works
        self.assertIsNone(error)

    def test_a_failed_move_with_force_restores_every_original(self):
        self.publish()
        mine = {NOTO_TTF: b"my own ttf rebuild", NOTO_WOFF2: b"my own woff2 rebuild"}
        for rel, data in mine.items():
            write_file(self.root, rel, data)
        for fail_at in (1, 2, 3, 4):  # aside, place, aside, place
            with self.subTest(fail_at=fail_at):
                before = snapshot(self.root)
                with self.flaky_replace(lambda n: n == fail_at):
                    [(_, outcome, error)] = self.fetch("noto.zip", force=True)
                self.assertIsNone(outcome)
                self.assertIn("the tree was left as it was", error)
                self.assertEqual(snapshot(self.root), before)

    def test_an_undo_that_fails_too_names_what_is_left(self):
        self.publish()
        mine = {NOTO_TTF: b"my own ttf rebuild", NOTO_WOFF2: b"my own woff2 rebuild"}
        for rel, data in mine.items():
            write_file(self.root, rel, data)
        # The ttf is moved aside and replaced; then every move fails, the undo included.
        with self.flaky_replace(lambda n: n >= 3):
            [(_, outcome, error)] = self.fetch("noto.zip", force=True)
        self.assertIsNone(outcome)
        self.assertIn("undoing the moves already made failed too", error)
        [backup] = (self.root / "noctua-noto").glob(".NotoSans-VariableFont_wdth,wght.ttf.*" + fa.BACKUP_SUFFIX)
        self.assertEqual(backup.read_bytes(), mine[NOTO_TTF])
        self.assertIn(f"{NOTO_TTF}: could not be restored", error)
        self.assertIn(f"the original is at {backup.relative_to(self.root).as_posix()}", error)
        self.assertEqual((self.root / NOTO_TTF).read_bytes(), font_bytes(NOTO_TTF, FONT_SIZES[NOTO_TTF]))
        self.assertEqual((self.root / NOTO_WOFF2).read_bytes(), mine[NOTO_WOFF2])

    def test_an_original_that_cannot_be_deleted_is_reported(self):
        self.publish()
        write_file(self.root, NOTO_TTF, b"my own ttf rebuild")
        real_unlink = os.unlink

        def unlink(path, *args, **kwargs):
            if str(path).endswith(fa.BACKUP_SUFFIX):
                raise PermissionError(13, "Access is denied", str(path))
            return real_unlink(path, *args, **kwargs)

        with mock.patch.object(fa.os, "unlink", unlink):
            code, out, err = run_cli("--root", self.root, "fetch", "--base-url", self.base_url,
                                     "--archive", "noto.zip", "--force")
        self.assertEqual(code, 0, err)
        [backup] = (self.root / "noctua-noto").glob("*" + fa.BACKUP_SUFFIX)
        self.assertEqual(backup.read_bytes(), b"my own ttf rebuild")
        self.assertIn(f"the replaced original {backup.relative_to(self.root).as_posix()} could not be "
                      "deleted", out)

    # --- refusals of a hostile server or URL

    def test_refuses_a_download_at_the_size_limit(self):
        self.publish()
        with mock.patch.object(fa, "MAX_ARCHIVE_SIZE", 100):
            self.assert_refused("declares")  # by Content-Length, before reading the body
            [(_, _, error)] = self.fetch("noto.zip", base_url=f"{self.origin}/no-length/")
        self.assertIn("sent 100 bytes or more", error)  # by counting, with no Content-Length

    def test_refuses_a_redirect_to_plain_http_elsewhere(self):
        self.assert_refused_url(f"{self.origin}/redirect-out/", "refusing the redirect")

    def assert_refused_url(self, base_url, fragment):
        before = snapshot(self.root)
        [(_, outcome, error)] = self.fetch("noto.zip", base_url=base_url)
        self.assertIsNone(outcome)
        self.assertIn(fragment, error or "")
        self.assertEqual(snapshot(self.root), before)

    def test_base_url_policy(self):
        for url in ("https://example.com/releases/", "https://example.com", "http://127.0.0.1:8000/x/",
                    "http://127.5.6.7/", "http://[::1]:8000/"):
            with self.subTest(url=url):
                self.assertTrue(fa.check_base_url(url).endswith("/"))
        for url, fragment in {
            "http://example.com/": "host name",
            "http://localhost:8000/": "host name",
            "http://10.0.0.1/": "not loopback",
            "ftp://127.0.0.1/": "scheme",
            "file:///etc/": "scheme",
            "https://user:secret@example.com/": "credentials",
            "https://example.com/?a=1": "query or a fragment",
            "https://example.com/#top": "query or a fragment",
            "https://example.com:http/": "not a valid URL",
            "not a url": "scheme",
        }.items():
            with self.subTest(url=url):
                with self.assertRaises(fa.FontArchivesError) as caught:
                    fa.check_base_url(url)
                self.assertIn(fragment, str(caught.exception))

    def test_cli_refuses_a_plain_http_base_url(self):
        code, _, err = run_cli("--root", self.root, "fetch", "--base-url", "http://example.com/")
        self.assertEqual(code, 1)
        self.assertIn("refusing the base URL", err)

    def test_default_url_is_the_github_release(self):
        self.assertEqual(fa.default_base_url(self.config),
                         "https://github.com/example/fonts/releases/download/v0.0.1/")
        self.assertEqual(fa.default_base_url(self.config, "v2.0.0"),
                         "https://github.com/example/fonts/releases/download/v2.0.0/")
        with self.assertRaisesRegex(fa.FontArchivesError, "refusing the tag"):
            fa.default_base_url(self.config, "../../evil")


class DownloadPolicyTest(unittest.TestCase):
    """The https-to-http downgrade defence, which a test without TLS can only check from inside."""

    @staticmethod
    def allows_loopback_http(url):
        [policy] = [h for h in fa._opener(url).handlers if isinstance(h, fa._RedirectPolicy)]
        return policy.allow_loopback_http

    def test_an_https_download_never_follows_a_redirect_to_plain_http(self):
        self.assertFalse(self.allows_loopback_http("https://github.com/o/r/releases/download/v1/a.zip"))
        self.assertTrue(self.allows_loopback_http("http://127.0.0.1:8000/a.zip"))
        request = urllib.request.Request("https://github.com/o/r/releases/download/v1/a.zip")
        for target in ("http://127.0.0.1:8000/a.zip", "http://example.com/a.zip", "file:///etc/passwd"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(fa.FontArchivesError, "refusing the redirect"):
                    fa._RedirectPolicy(False).redirect_request(request, None, 302, "Found", {}, target)
        followed = fa._RedirectPolicy(False).redirect_request(
            request, None, 302, "Found", {}, "https://objects.example.com/a.zip")
        self.assertEqual(followed.full_url, "https://objects.example.com/a.zip")


class ReadEntryTest(TempTree):
    def test_stops_at_the_cap_whatever_the_entry_declares(self):
        path = self.tmp / "entry.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("x.ttf", b"a" * 5000)
        with zipfile.ZipFile(path) as archive, mock.patch.object(fa, "MAX_ENTRY_SIZE", 1000):
            with self.assertRaisesRegex(fa.FontArchivesError, "decompresses past the 1000-byte cap"):
                fa._read_entry(archive, archive.getinfo("x.ttf"))


class HostileZipFuzzTest(TempTree):
    """Random corruption of a real archive: always a clean refusal or the right fonts, never a traceback."""

    def test_random_corruption_never_escapes_or_writes(self):
        source = make_tree(self.tmp / "source")
        config = fa.load_config(source)
        fa.pack(source, config, self.tmp / "release")
        good = (self.tmp / "release" / "noto.zip").read_bytes()
        make_tree(self.root, fonts=False, manifest=False)
        shutil.copyfile(source / "SHA256SUMS", self.root / "SHA256SUMS")
        manifest = fa.read_manifest(self.root)
        spec = config.archive("noto.zip")
        assigned = fa.assign(manifest, config).by_archive["noto.zip"]
        directory = zip_records(good)[0][1]  # where the central directory starts
        before = snapshot(self.root)
        served = {}

        def fake_download(url, handle):
            handle.write(served["data"])
            return len(served["data"])

        rng = random.Random(20261101)
        with mock.patch.object(fa, "download", fake_download), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for _ in range(400):
                data = bytearray(good)
                for _ in range(rng.choice((1, 2, 4, 8))):
                    # Half the hits land in the headers, where zipfile's parser lives.
                    start = directory if rng.random() < 0.5 else 0
                    data[rng.randrange(start, len(data))] = rng.randrange(256)
                served["data"] = bytes(data)
                try:
                    fa.fetch_archive(self.root, spec, assigned, manifest, "http://127.0.0.1:9/")
                except fa.FontArchivesError:
                    self.assertEqual(snapshot(self.root), before)
                    continue
                for path in assigned:  # a corruption zipfile tolerates must still give the right fonts
                    self.assertEqual(fa.sha256_file(self.root / path), manifest[path])
                    (self.root / path).unlink()


# ---------------------------------------------------------------------------
# The command line

class HelpTest(unittest.TestCase):
    def test_every_command_has_help(self):
        for argv in (["--help"], ["manifest", "--help"], ["verify", "--help"], ["list", "--help"],
                     ["pack", "--help"], ["fetch", "--help"]):
            with self.subTest(argv=argv):
                out = io.StringIO()
                with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as caught:
                    fa.main(argv)
                self.assertEqual(caught.exception.code, 0)
                self.assertIn("usage:", out.getvalue())

    def test_top_level_help_names_every_command(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            fa.main(["--help"])
        for command in ("manifest", "verify", "list", "pack", "fetch"):
            self.assertIn(command, out.getvalue())


# ---------------------------------------------------------------------------
# The real repository

REAL_MANIFEST = REPO / "SHA256SUMS"
NERD_LICENSE_COPY = "noctua-iosevka/licenses/LICENSE-NerdFontsSymbolsOnly.txt"
WIDTHS = {"normal": "", "condensed": "Condensed", "semicondensed": "SemiCondensed",
          "semiextended": "SemiExtended", "extended": "Extended"}
WEIGHTS = ["Thin", "ExtraLight", "Light", "", "Medium", "SemiBold", "Bold", "ExtraBold", "Heavy"]
SLOPES = ["", "Italic", "Oblique"]
IOSEVKA_KINDS = {  # archive stem: (folder, family, suffix)
    "noctua-iosevka-ttf": ("TTF", "NoctuaIosevka", "ttf"),
    "noctua-iosevka-woff2": ("WOFF2", "NoctuaIosevka", "woff2"),
    "noctua-iosevka-nerd-font-ttf": ("TTF-nerdfonts", "NoctuaIosevkaNerdFontMono", "ttf"),
    "noctua-iosevka-nerd-font-woff2": ("WOFF2-nerdfonts", "NoctuaIosevkaNerdFontMono", "woff2"),
}


def final_iosevka_names():
    """{path: archive} for every Iosevka file under the final naming scheme."""
    names = {}
    for stem, (folder, family, suffix) in IOSEVKA_KINDS.items():
        for width, width_word in WIDTHS.items():
            for weight in WEIGHTS:
                for slope in SLOPES:
                    style = (width_word + weight + slope) or "Regular"
                    names[f"noctua-iosevka/{folder}/{family}-{style}.{suffix}"] = f"{stem}-{width}.zip"
    return names


def rule_lines(path):
    """The non-comment lines of a .gitignore or .gitattributes, stripped."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


class RealRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.config = fa.load_config(REPO)

    def test_the_layout_has_23_archives(self):
        expected = [f"{stem}-{width}.zip" for stem in IOSEVKA_KINDS for width in WIDTHS]
        expected += ["noctua-noto-ttf.zip", "noctua-noto-woff2.zip", "symbols-nerd-font.zip"]
        self.assertEqual(sorted(a.name for a in self.config.archives), sorted(expected))
        self.assertEqual(self.config.repository, "noctua-world/noctua-fonts")

    def test_each_iosevka_width_gets_its_own_files(self):
        names = final_iosevka_names()
        self.assertEqual(len(names), 540)
        assignment = fa.assign(names, self.config)
        self.assertEqual((assignment.orphans, assignment.duplicates), ([], {}))
        for path, archive in names.items():
            self.assertIn(path, assignment.by_archive[archive], path)
        for stem in IOSEVKA_KINDS:
            for width in WIDTHS:
                self.assertEqual(len(assignment.by_archive[f"{stem}-{width}.zip"]), 27)

    def test_noto_and_symbols_go_to_their_archives(self):
        cases = {
            "noctua-noto/NotoSans-VariableFont_wdth,wght.ttf": "noctua-noto-ttf.zip",
            "noctua-noto/NotoSansMNerdFont-Bold.woff2": "noctua-noto-woff2.zip",
            "symbols-nerd-font/SymbolsNerdFont-Regular.ttf": "symbols-nerd-font.zip",
            "symbols-nerd-font/SymbolsNerdFontMono-Regular.woff2": "symbols-nerd-font.zip",
        }
        assignment = fa.assign(cases, self.config)
        for path, archive in cases.items():
            self.assertEqual(assignment.by_archive[archive].count(path), 1, path)

    def test_the_old_semiextended_nerd_names_are_not_taken_by_another_width(self):
        old = ["noctua-iosevka/TTF-nerdfonts/NoctuaIosevkaBoldSemiNerdFontMono-Extended.ttf",
               "noctua-iosevka/WOFF2-nerdfonts/NoctuaIosevkaSemiNerdFontMono-ExtendedItalic.woff2"]
        self.assertEqual(fa.assign(old, self.config).orphans, old)

    def test_nerd_font_archives_carry_both_licences(self):
        for archive in self.config.archives:
            if archive.name.startswith("noctua-iosevka-"):
                with self.subTest(archive=archive.name):
                    expected = {"noctua-iosevka/licenses/OFL-Iosevka.txt"}
                    if "-nerd-font-" in archive.name:
                        expected.add(NERD_LICENSE_COPY)
                    self.assertEqual(set(archive.licenses), expected)

    def test_every_licence_file_exists(self):
        for path in sorted({p for a in self.config.archives for p in a.licenses}):
            with self.subTest(path=path):
                full = fa._native(REPO, path)
                self.assertTrue(full.is_file(), path)

    def test_the_nerd_licence_copy_is_identical_to_the_original(self):
        copy = fa._native(REPO, NERD_LICENSE_COPY)
        original = REPO / "symbols-nerd-font" / "licenses" / "LICENSE-NerdFontsSymbolsOnly.txt"
        self.assertEqual(copy.read_bytes(), original.read_bytes())

    def test_noto_archives_carry_every_noto_licence(self):
        folder = REPO / "noctua-noto" / "licenses"
        present = {f"noctua-noto/licenses/{p.name}" for p in folder.iterdir() if p.is_file()}
        for name in ("noctua-noto-ttf.zip", "noctua-noto-woff2.zip"):
            self.assertEqual(set(self.config.archive(name).licenses), present, name)

    def test_every_manifest_path_is_in_exactly_one_archive(self):
        manifest = fa.read_manifest(REPO)
        assignment = fa.assign(manifest, self.config)
        self.assertEqual(assignment.orphans, [])
        self.assertEqual(assignment.duplicates, {})
        empty = [name for name, paths in assignment.by_archive.items() if not paths]
        self.assertEqual(empty, [])

    def test_gitignore_ignores_the_built_fonts_and_the_tool_leftovers(self):
        rules = set(rule_lines(REPO / ".gitignore"))
        for folder in fa.FONT_DIRS:  # suffixes in any case, as is_font_name reads them
            for rule in (f"/{folder}/**/*.[tT][tT][fF]", f"/{folder}/**/*.[wW][oO][fF][fF]2",
                         f"/{folder}/**/.*{fa.TEMP_SUFFIX}"):
                self.assertIn(rule, rules)
        self.assertTrue(fa.BACKUP_SUFFIX.endswith(fa.TEMP_SUFFIX))  # covered by the .part rule
        self.assertIn(f"/.{fa.MANIFEST_NAME}.*.tmp", rules)
        self.assertIn("/dist/", rules)

    def test_gitattributes_keeps_the_byte_exact_files_exact(self):
        """SHA256SUMS, the licence files and the site need -text, so that a Windows checkout
        keeps their bytes (the site's: site/build.py --check compares docs/ byte for byte)."""
        attributes = {}
        for line in rule_lines(REPO / ".gitattributes"):
            pattern, *values = line.split()
            attributes.setdefault(pattern, set()).update(values)
        for pattern in ("/SHA256SUMS", "/*/licenses/**", "/site/**", "/docs/**"):
            with self.subTest(pattern=pattern):
                values = attributes.get(pattern, set())
                self.assertTrue(values & {"-text", "binary"}, f"{pattern} must be marked -text")
                self.assertFalse({v for v in values if v.startswith("eol=")},
                                 f"{pattern} must keep its bytes; eol= would convert them")


if __name__ == "__main__":
    unittest.main()
