#!/usr/bin/env python3
"""Rewrite the family name recorded inside font files.

Font lookup by name fails *silently*: ask for a family the system does not have
and you get a fallback face, with no error anywhere. So when the same typeface
carries different family names in different places -- common with fonts patched
by Nerd Fonts, where each person who runs the patcher may rename the output --
text quietly renders in the wrong font. This aligns files onto one chosen name.

    ./rename-font-family.py FROM TO FONT [FONT ...]
    ./rename-font-family.py "MyFont Mono Nerd Font" "MyFontM Nerd Font" *.ttf

What changes
  Only the identifier name records (IDs 1/3/4/6/16/18/20/21). Copyright,
  trademark and license (IDs 0/7/13/14) and every other record are left alone.
  Both the spaced form ("My Font") and the compact form ("MyFont") of FROM are
  replaced. The PostScript records (IDs 6 and 20) cannot hold a space: there
  the compact form becomes TO's compact form, and the hyphenated form some
  build tools write ("My-Font-Bold", as Iosevka does) TO's hyphenated form.
  When a font changes but a PostScript record holds FROM in none of those
  forms (a Nerd Fonts abbreviation such as "MyFontNFM-Bold", say), the record
  is kept and a note says so: the old and the new family may then share it.
  When a font's records change and its file name carries the compact form,
  the file is renamed too.

  An occurrence of FROM that is already part of TO is left alone, in records
  and in file names, so "Foo" -> "Foo Code" turns "Foo Bold" into
  "Foo Code Bold" and leaves "Foo Code Bold" (and FooCode-Bold.ttf) as they
  are; "Foo Code" -> "Foo" undoes it.

WOFF2 web copies
  A .woff2 beside a listed .ttf or .otf, with the same stem, is that font's
  web copy. Whenever the font changes, and also when the copy alone still
  carries FROM, the copy is rebuilt from the renamed font -- exactly as
  "fonttools ttLib.woff2 compress" would build it -- and renamed with it.
  That is done only when the copy's identifier records, once renamed, equal
  the font's: if they differ, the copy is another font (or another build of
  it), and the batch is refused rather than replace it; rename such a copy in
  a run of its own. Listing the copy as well (as "*" does) changes nothing:
  it is handled, and reported, with its font. Anything only the old copy held
  (WOFF2 metadata or private data) is not carried over. A .woff2 or .woff
  listed without its .ttf/.otf is renamed on its own and keeps its format.

Nothing changes unless everything can
  A batch runs in three steps, and only the last one touches a font.
  1. Check. Every argument is read and every change planned; nothing is
     written. A missing path, a symbolic link, something that is not a font,
     a font that would be rewritten but is hard-linked, read-only, digitally
     signed or has a 'name' table that cannot be written back whole (format
     1, or with malformed records), a web copy whose names do not match its
     font, a rename onto a file that already exists or onto another output
     of the batch, an invalid resulting PostScript or file name (one too long
     for the file system included), or a record that cannot be decoded or
     whose encoding cannot hold TO stops the whole batch here.
  2. Build. Every output is written in full to a hidden temporary file
     beside its target. A font that cannot be rebuilt (a damaged glyph
     table, say) or a full disk stops the batch: the temporary files are
     removed, and no font has changed.
  3. Move. Font by font, each temporary file is moved into place atomically
     and the font is reported. No font work is left for this step, so what
     can still stop it is a file that changed or appeared since step 1, or
     an error from the file system; the batch then stops, says how many
     files were handled and what of the font it stopped at was written, and
     leaves the fonts after that one as they were.

  An interruption leaves every font either as it was or completely
  rewritten. A file being renamed can, for an instant, exist under both
  names; a rerun then stops on the clash and names both. A kill or power
  loss at the wrong instant can also leave a hidden
  ".rename-font-family-*.tmp" file, or an empty file under a font's new
  name, beside the fonts -- never a damaged font.

Idempotent and reversible
  Running the same command again does nothing: a rename whose result a second
  run would change again is refused. Swapping FROM and TO restores every
  identifier record and the file name of each font the run changed; for each
  changed font where it would not -- because a record or the file name
  already contained TO before the run, or because the swapped run would be
  refused -- a note is printed. (A font the run left alone because it already
  carried TO is changed by the swap as well.) What else a rename keeps,
  exactly, for a .ttf or .otf:
    - every table except 'name' and 'head' is byte-for-byte unchanged, the
      tables keep their order in the file, and 'head' differs only in
      checkSumAdjustment (head.modified is kept);
    - 'name' holds the same records, in the same encodings, except the ones
      renamed; but fontTools lays the table out its own way (records sorted,
      repeated strings stored once), so after a round trip a file that was
      laid out otherwise has the same records, not the same 'name' bytes nor
      the same checkSumAdjustment -- the file is not byte-identical;
    - a file this tool has written is in that layout already, so from then
      on, when the swap restores every record, a rename followed by its
      reverse gives back a byte-identical file.
  A .woff2 or .woff is re-encoded on every write, so its file bytes change the
  first time even when every record comes back. Decoded, it keeps what a .ttf
  keeps, with one proviso for a .woff2: its glyf and loca tables go through
  fontTools' WOFF2 transform again, which is lossless by design (and was, on
  the files tried) but is not checked by this tool. A .woff2 or .woff this
  tool has written comes back byte-identical, as above.

Exit status: 0 when every file was handled (or had nothing to do), 1 when the
batch was refused or stopped, 2 on a usage error.

Requires: fonttools (plus brotli if .woff2 files are present)
          ->  pip install fonttools brotli
"""

# Security and safety, decided at design time:
#
# - Three steps: check (reads, plans, writes nothing), build (writes only new
#   hidden temporary files), move (the only step that touches a font). A batch
#   is never left half done because of something that could have been seen
#   in advance -- in particular never because of a file the tool itself
#   replaced (a .woff2 listed beside its .ttf is planned as part of that
#   .ttf, once), nor because a font turns out to be damaged where only a
#   full rebuild looks (that happens in the build step, before any move).
# - The build and the move steps each re-read every source and compare its
#   SHA-256 with the check step's; a file that changed in between stops the
#   batch instead of being overwritten with a plan made for other content.
# - Fonts are parsed from an in-memory copy, so no handle stays open on a file
#   about to be replaced (os.replace onto an open file fails on Windows).
# - Outputs go to a temporary file created by mkstemp (O_EXCL, private mode) in
#   the target's own directory, are fsync'ed, given the source's permission
#   bits and moved with os.replace, which is atomic on one file system. A
#   failure removes the temporary file. Temporary names have one fixed length,
#   so a long font name can never make its temporary name too long.
# - A rename onto a new name reserves that name with O_CREAT|O_EXCL before the
#   move, so a file that appeared after the check step is never overwritten.
# - Symbolic links are refused: os.replace would replace the link, not what it
#   points to. Hard-linked files are refused: an atomic rewrite would give one
#   name the new font and leave the other names on the old one. Read-only
#   files are refused: read-only is taken as "do not modify".
# - New file names are validated for every platform (no separators, no
#   characters Windows forbids, no device names -- CONIN$, COM1 to COM9 and
#   their superscript forms, "NUL .ttf" included -- and no more bytes than
#   the file system takes), since TO is free text and a "/" or ":" in it must
#   never turn into a path outside the font's directory or an NTFS alternate
#   data stream. On Windows a path past MAX_PATH is refused too, unless the
#   source's own path is already longer (long paths are then enabled).
# - A record that cannot be decoded strictly is refused rather than rewritten
#   from a lossy decoding, which would corrupt it. So is a 'name' table that
#   fontTools would not write back whole: format 1 (its language tags would
#   be dropped) or one with malformed records (fontTools skips them, and the
#   rewrite would silently lose them, copyright records included).
# - A same-stem .woff2 is replaced by a rebuild of its font only when its
#   identifier records, renamed, equal the font's; otherwise it is another
#   font, and replacing it would destroy it.
# - A font carrying a real digital signature (a DSIG table with signatures) is
#   refused: the rename would leave a signature that no longer verifies. The
#   empty placeholder DSIG many build tools emit is not a signature.
# - Every line printed goes through printable(): name records and file names
#   come from untrusted files, and a control character in them (ESC, BEL, the
#   C1 controls, bidirectional overrides, line separators) must never reach
#   the terminal raw, where it could retitle the window, clear the screen,
#   reorder the text or fake a line of output.

import argparse
import hashlib
import io
import ntpath
import os
import stat
import struct
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from fontTools.ttLib import TTFont
except ImportError:
    sys.exit("error: fonttools not found.  ->  pip install fonttools brotli")

# Name IDs that identify the font. Never 0/7/13/14 -- those are legal text and
# may legitimately contain the old name.
IDENTIFIER_IDS = frozenset({1, 3, 4, 6, 16, 18, 20, 21})
# PostScript name and PostScript CID findfont name: no spaces allowed.
POSTSCRIPT_IDS = frozenset({6, 20})
POSTSCRIPT_MAX_LENGTH = 63
POSTSCRIPT_FORBIDDEN = frozenset("[](){}<>/%")

# A listed file with one of these suffixes owns the same-stem web copy.
SOURCE_SUFFIXES = frozenset({".ttf", ".otf"})
WEB_COPY_SUFFIX = ".woff2"

# Characters no file name may carry on at least one supported platform.
FILE_NAME_FORBIDDEN = frozenset('<>:"/\\|?*')
# Device names Windows reserves, with any extension, and with spaces before
# it ("NUL .ttf"); the same set as Python 3.13's ntpath.isreserved.
WINDOWS_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {port + digit for port in ("COM", "LPT")
       for digit in "123456789\u00b9\u00b2\u00b3"})
# The longest file name every supported file system takes, in bytes of its
# encoded form: ext4 and APFS take 255 bytes of UTF-8, NTFS 255 UTF-16 units
# (and no name has more UTF-16 units than UTF-8 bytes).
NAME_MAX = 255
# MAX_PATH less its terminating NUL: the longest path Windows opens unless
# long paths are enabled.
WINDOWS_MAX_PATH = 259
# Temporary files: the prefix, mkstemp's eight random characters, the suffix.
TEMP_PREFIX = ".rename-font-family-"
TEMP_SUFFIX = ".tmp"
TEMP_NAME_LENGTH = len(TEMP_PREFIX) + 8 + len(TEMP_SUFFIX)
# Bidirectional controls, and the line and paragraph separators: they
# reorder what a terminal shows, or break it into lines.
LAYOUT_CONTROLS = frozenset("\u2028\u2029"
                            "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e"
                            "\u2066\u2067\u2068\u2069")


class RenameError(Exception):
    """A reason to refuse or stop the batch. Each argument is one message,
    and each message names its file."""


def messages(exc):
    """The messages an exception carries, one per line to print."""
    if isinstance(exc, RenameError):
        return [str(arg) for arg in exc.args]
    if isinstance(exc, OSError):
        return [str(exc)]
    return [f"{type(exc).__name__}: {exc}"]


# --------------------------------------------------------------------------
# String rewriting


def compact(name):
    """The PostScript-style form of a family name: its spaces removed."""
    return name.replace(" ", "")


def hyphenated(name):
    """The other PostScript-style form: its spaces turned into hyphens."""
    return name.replace(" ", "-")


def substitute(text, pairs):
    """Replace, left to right, each (old, new) pair's old in text with its new.

    An occurrence of an old that lies inside an occurrence of a new -- every
    occurrence in the text as given, overlapping ones included -- is kept.
    That is what makes a rename whose new contains its old idempotent
    ("Foo" -> "Foo Code" leaves "Foo Code" alone), while an old that contains
    its new, as in the reverse rename, is still replaced. A new that is also
    some pair's old guards nothing, or it would block that pair. Where several
    olds match at one position the longest wins, then the first pair.
    """
    pairs = [(old, new) for old, new in pairs if old]  # "" would never end
    olds = {old for old, _ in pairs}
    guards = []
    for guard in {new for _, new in pairs} - olds:
        start = text.find(guard)
        while guard and start != -1:
            guards.append((start, start + len(guard)))
            start = text.find(guard, start + 1)
    ordered = sorted(pairs, key=lambda pair: -len(pair[0]))  # stable
    out = []
    i = 0
    while i < len(text):
        for old, new in ordered:
            end = i + len(old)
            if text.startswith(old, i) and not any(
                    start <= i and end <= stop for start, stop in guards):
                out.append(new)
                i = end
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def record_pairs(name_id, old, new):
    """The (old, new) pairs that apply to a name record with this ID.

    A PostScript record takes the compact form and, where it differs, the
    hyphenated one. When FROM has no space both forms of it are one string:
    the compact pair, listed first, then wins, and the hyphenated TO still
    guards a record already on it ("Iosevka" -> "Noctua Iosevka" leaves
    "Noctua-Iosevka-Bold" alone).
    """
    if name_id not in POSTSCRIPT_IDS:
        return [(old, new), (compact(old), compact(new))]
    pairs = [(compact(old), compact(new))]
    if (hyphenated(old), hyphenated(new)) != pairs[0]:
        pairs.append((hyphenated(old), hyphenated(new)))
    return pairs


def describe_key(name_id, platform_id, encoding_id, language_id):
    return (f"ID {name_id} (platform {platform_id}, encoding {encoding_id}, "
            f"language {language_id})")


def describe(record):
    return describe_key(record.nameID, record.platformID, record.platEncID,
                        record.langID)


def decode(record, label):
    """The record's text, decoded strictly; RenameError if it cannot be."""
    try:
        return record.toUnicode()
    except (UnicodeDecodeError, LookupError) as exc:
        raise RenameError(
            f"{label}: name record {describe(record)} cannot be decoded "
            f"({exc}); refusing to rewrite a record that cannot be read"
        ) from None


def is_postscript_name(value):
    return len(value) <= POSTSCRIPT_MAX_LENGTH and all(
        33 <= ord(c) <= 126 and c not in POSTSCRIPT_FORBIDDEN for c in value)


def check_postscript_name(value, record, label):
    if not is_postscript_name(value):
        raise RenameError(
            f"{label}: name record {describe(record)} would become {value!r}, "
            "which is not a valid PostScript name (printable ASCII with no "
            f"spaces and none of []{{}}()<>/%, at most "
            f"{POSTSCRIPT_MAX_LENGTH} characters)")


def swap_problem(record, before, after, back_pairs):
    """Why renaming TO -> FROM after this run would not give this record
    back; None when the swapped run would accept it and restore it."""
    back = substitute(after, back_pairs)
    if back != before:
        return (f"name record {describe(record)} would come back as "
                f"{back!r}, not {before!r}")
    if back == after:
        return None
    if substitute(back, back_pairs) != back:
        return (f"the swapped run would be refused: on name record "
                f"{describe(record)}, {after!r} would become {back!r}, which "
                "a further run would change again")
    if record.nameID in POSTSCRIPT_IDS and not is_postscript_name(back):
        return (f"the swapped run would be refused: name record "
                f"{describe(record)} would become {back!r}, which is not a "
                "valid PostScript name")
    return None


def plan_records(name_table, old, new, label):
    """Plan the rename of one font's identifier records.

    Returns (changes, irreversible): changes is [(record, before, after)] for
    every identifier record the rename changes; irreversible is None when
    renaming new -> old afterwards would be accepted and give every
    identifier record back, else the first reason it would not.
    Raises RenameError when a record cannot be decoded, when the result is not
    stable (a second run would change it again) or when a PostScript record
    would become invalid. Nothing is modified.
    """
    changes = []
    irreversible = None
    for record in name_table.names:
        if record.nameID not in IDENTIFIER_IDS:
            continue
        before = decode(record, label)
        pairs = record_pairs(record.nameID, old, new)
        after = substitute(before, pairs)
        if irreversible is None:
            irreversible = swap_problem(
                record, before, after, record_pairs(record.nameID, new, old))
        if after == before:
            continue
        again = substitute(after, pairs)
        if again != after:
            raise RenameError(
                f"{label}: renaming is not stable on name record "
                f"{describe(record)}: {before!r} would become {after!r}, and "
                f"a second run would make it {again!r}; refusing")
        if record.nameID in POSTSCRIPT_IDS:
            check_postscript_name(after, record, label)
        changes.append((record, before, after))
    return changes, irreversible


def apply_changes(changes, label):
    """Write the planned strings into the records; check each one encodes."""
    for record, _, after in changes:
        record.string = after
        try:
            record.toBytes()
        except (UnicodeEncodeError, LookupError, TypeError):
            raise RenameError(
                f"{label}: name record {describe(record)} cannot hold "
                f"{after!r} in its encoding ({record.getEncoding()})"
            ) from None


def identifier_records(name_table):
    """{(name ID, platform, encoding, language): text} of the identifiers."""
    return {(r.nameID, r.platformID, r.platEncID, r.langID): r.toUnicode()
            for r in name_table.names if r.nameID in IDENTIFIER_IDS}


def postscript_notes(name_table, changes, old, new):
    """Notes for the PostScript records a changing font keeps although they
    hold no form of TO: the old and the new family may then share them."""
    changed = {id(record) for record, _, _ in changes}
    notes = []
    for record in name_table.names:
        if record.nameID not in POSTSCRIPT_IDS or id(record) in changed:
            continue
        text = record.toUnicode()
        if any(to in text for _, to in record_pairs(record.nameID, old, new)):
            continue
        note = (f"kept the PostScript name {text!r} (name ID {record.nameID}):"
                " it holds FROM in none of the forms this tool rewrites, so "
                "fonts of the old and the new family may now share it")
        if note not in notes:
            notes.append(note)
    return notes


# --------------------------------------------------------------------------
# File names


def name_max(directory):
    """The longest file name, in bytes, that directory takes: NAME_MAX, or
    less where its file system says so."""
    try:
        limit = os.pathconf(directory, "PC_NAME_MAX")
    except (AttributeError, ValueError, OSError):  # no pathconf on Windows
        return NAME_MAX
    return min(NAME_MAX, limit) if limit > 0 else NAME_MAX


def check_file_name(name, label, directory=None):
    """RenameError unless name is a portable file name that fits directory."""
    device = name.partition(".")[0].rstrip(" ").upper()
    reserved = getattr(ntpath, "isreserved", None)  # Python 3.13 and later
    if (not name or name in (".", "..") or name.endswith((" ", "."))
            or any(c in FILE_NAME_FORBIDDEN or ord(c) < 32 for c in name)
            or device in WINDOWS_DEVICE_NAMES
            or (reserved is not None and reserved(name))):
        raise RenameError(
            f"{label}: the renamed file would be called {name!r}, which is "
            "not a portable file name (no / \\ < > : \" | ? *, no control "
            "characters, no trailing space or dot, no device name such as "
            "NUL, COM1 or CONIN$)")
    limit = NAME_MAX if directory is None else name_max(directory)
    size = len(os.fsencode(name))
    if size > limit:
        raise RenameError(
            f"{label}: the renamed file would be called {name!r}, which is "
            f"{size} bytes long; a file name here can have at most {limit}")


def renamed_path(path, old, new):
    """(path the font is written to, why swapping would not restore that
    name or None).

    Only the compact form is replaced, and only in the name before the final
    suffix; the suffix is kept.
    """
    suffix = path.suffix
    stem = path.name[:len(path.name) - len(suffix)]
    pairs = [(compact(old), compact(new))]
    back_pairs = [(compact(new), compact(old))]
    new_stem = substitute(stem, pairs)
    back = substitute(new_stem, back_pairs)
    irreversible = None
    if back != stem:
        irreversible = f"the file name would come back as {back + suffix!r}"
    elif back != new_stem:
        if substitute(back, back_pairs) != back:
            irreversible = ("the swapped run would be refused: the file name "
                            f"{back + suffix!r} would change again")
        else:
            try:
                check_file_name(stem + suffix, path, path.parent)
            except RenameError:
                irreversible = ("the swapped run would be refused: "
                                f"{stem + suffix!r} is not a portable name")
    if new_stem == stem:
        return path, irreversible
    if substitute(new_stem, pairs) != new_stem:
        raise RenameError(
            f"{path}: renaming is not stable on the file name: {stem!r} would "
            f"become {new_stem!r}, and a second run would change it again")
    name = new_stem + suffix
    check_file_name(name, path, path.parent)
    return path.with_name(name), irreversible


def windows_path_problem(original, target, windows=None):
    """On Windows: why target, or the temporary file built beside it, would
    be a path longer than MAX_PATH while original is not (a longer original
    shows long paths are enabled). None elsewhere, or when it fits."""
    if windows is None:
        windows = os.name == "nt"
    if not windows:
        return None
    longest = max(len(os.path.abspath(target)),
                  len(os.path.abspath(target.parent)) + 1 + TEMP_NAME_LENGTH)
    if longest <= max(WINDOWS_MAX_PATH, len(os.path.abspath(original))):
        return None
    return (f"{original}: its new path, or the temporary file built beside "
            f"it, would be {longest} characters long; Windows opens at most "
            f"{WINDOWS_MAX_PATH} unless long paths are enabled")


# --------------------------------------------------------------------------
# Reading


def identity(path, st):
    """What makes two paths one file: device and inode -- or, on a file
    system that reports no inode (st_ino 0), the normalised absolute path,
    so distinct files are never merged and silently dropped."""
    if st.st_ino:
        return (st.st_dev, st.st_ino)
    return os.path.normcase(os.path.abspath(path))


def same_entry(a, b):
    """Whether two existing paths are one directory entry (case-insensitive
    file systems), without following symbolic links."""
    try:
        return identity(a, os.lstat(a)) == identity(b, os.lstat(b))
    except OSError:
        return False


def regular_file_stat(path, what="file"):
    """lstat a path that must be an existing regular file, not a link."""
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        raise RenameError(f"{path}: no such {what}") from None
    except OSError as exc:
        raise RenameError(f"{path}: cannot be read ({exc.strerror})") from None
    if stat.S_ISLNK(st.st_mode):
        raise RenameError(
            f"{path}: is a symbolic link; pass the file it points to")
    if not stat.S_ISREG(st.st_mode):
        raise RenameError(f"{path}: is not a regular file")
    return st


def read_bytes(path):
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RenameError(f"{path}: cannot be read ({exc.strerror})") from None


def open_font(path, data):
    """Parse a font from bytes. Timestamps and bounding boxes are kept as
    they are, so nothing changes that the rename does not change."""
    try:
        font = TTFont(io.BytesIO(data), recalcBBoxes=False,
                      recalcTimestamp=False)
        if "name" not in font:
            raise RenameError(f"{path}: has no 'name' table")
        font["name"]  # decompile now, so a damaged table fails in step 1
        return font
    except RenameError:
        raise
    except ImportError:
        raise RenameError(
            f"{path}: brotli not found (needed for WOFF2)  ->  pip install "
            "brotli") from None
    except Exception as exc:  # fontTools raises many types on bad input
        raise RenameError(
            f"{path}: not a font this tool can read ({exc})") from None


def check_name_table(path, font):
    """Refuse a 'name' table that fontTools would not write back whole."""
    raw = font.reader["name"]
    version, count = struct.unpack(">HH", raw[:4])
    if version != 0:
        raise RenameError(
            f"{path}: its 'name' table is format {version} (with language "
            "tags), which this tool cannot write back without losing them")
    lost = count - len(font["name"].names)
    if lost:
        raise RenameError(
            f"{path}: {lost} of the {count} records in its 'name' table are "
            "malformed; rewriting the table would drop them")


def digital_signatures(font):
    """Number of signatures in the font's DSIG table (0 when none)."""
    reader = font.reader
    if reader is None or "DSIG" not in reader:
        return 0
    data = reader["DSIG"]
    return int.from_bytes(data[4:6], "big") if len(data) >= 8 else 0


# --------------------------------------------------------------------------
# Step 1: check and plan


@dataclass
class Job:
    """One listed font, and the web copy it owns, if any."""
    source: Path
    digest: bytes
    target: Path
    changed: bool           # whether the font's own records change
    irreversible: Optional[str]  # why swapping FROM and TO would not undo it
    family: str             # family (ID 1) after the rename, for the report
    notes: List[str] = field(default_factory=list)
    sibling: Optional[Path] = None
    sibling_digest: Optional[bytes] = None
    sibling_target: Optional[Path] = None
    rebuild_sibling: bool = False
    sibling_listed: bool = False
    # [(temporary file, original, target)] built in step 2, not yet moved.
    staged: List[Tuple[Path, Path, Path]] = field(default_factory=list)

    def outputs(self):
        """[(original path, target path)] of every file this job writes."""
        out = []
        if self.changed:
            out.append((self.source, self.target))
        if self.rebuild_sibling:
            out.append((self.sibling, self.sibling_target))
        return out


def collect(paths):
    """Sort the arguments into [(source, sibling or None, sibling listed)].

    Raises RenameError (with every problem found, one per message) when a
    path is missing or unusable, or a web copy could belong to two fonts.
    """
    errors = []
    listed = {}  # identity -> path, in argument order, duplicates dropped
    for path in paths:
        try:
            st = regular_file_stat(path)
        except RenameError as exc:
            errors.extend(messages(exc))
            continue
        listed.setdefault(identity(path, st), path)

    owner_of = {}    # identity of a web copy -> the listed font owning it
    sibling_of = {}  # identity of a listed font -> (web copy path, identity)
    for key, path in listed.items():
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        sibling = path.with_suffix(WEB_COPY_SUFFIX)
        if not os.path.lexists(sibling):
            continue
        try:
            web_key = identity(sibling, regular_file_stat(sibling, "web copy"))
        except RenameError as exc:
            errors.append(f"{exc} (it is the web copy of {path})")
            continue
        if web_key in owner_of:
            errors.append(
                f"{sibling}: is the web copy of both {owner_of[web_key]} and "
                f"{path}; list only one of them")
            continue
        owner_of[web_key] = path
        sibling_of[key] = (sibling, web_key)
    if errors:
        raise RenameError(*errors)

    result = []
    for key, path in listed.items():
        if key in owner_of:
            continue  # a listed web copy: handled with the font that owns it
        sibling, web_key = sibling_of.get(key, (None, None))
        result.append((path, sibling, web_key in listed))
    return result


def plan_web_copy(job, font, old, new):
    """Decide whether the job's web copy is rebuilt from its (renamed) font;
    refuse when a rebuild would replace a font that is not its copy."""
    web = read_bytes(job.sibling)
    web_font = open_font(job.sibling, web)  # never replace what is no font
    job.sibling_digest = hashlib.sha256(web).digest()
    job.sibling_target = job.target.with_suffix(WEB_COPY_SUFFIX)
    stale, _ = plan_records(web_font["name"], old, new, job.sibling)
    job.rebuild_sibling = job.changed or bool(stale)
    if not job.rebuild_sibling:
        return
    check_name_table(job.sibling, web_font)
    apply_changes(stale, job.sibling)
    mine = identifier_records(font["name"])
    theirs = identifier_records(web_font["name"])
    if mine != theirs:
        key = sorted(set(mine) | set(theirs),
                     key=lambda k: (mine.get(k) == theirs.get(k), k))[0]
        raise RenameError(
            f"{job.sibling}: has the stem of {job.source.name}, so it would "
            f"be rebuilt from it as its web copy, but it is another font (or "
            f"another build): after the rename, its name record "
            f"{describe_key(*key)} would be {theirs.get(key)!r} where the "
            f"font's is {mine.get(key)!r}. Refusing to replace it; rename it "
            "in a run of its own, or move it away")


def plan_job(source, sibling, sibling_listed, old, new):
    data = read_bytes(source)
    font = open_font(source, data)
    changes, irreversible = plan_records(font["name"], old, new, source)
    target = source
    notes = []
    if changes:
        if digital_signatures(font):
            raise RenameError(
                f"{source}: is digitally signed (DSIG); renaming would leave "
                "a signature that no longer verifies -- remove the signature "
                "first if that is intended")
        check_name_table(source, font)
        apply_changes(changes, source)
        target, name_irreversible = renamed_path(source, old, new)
        irreversible = irreversible or name_irreversible
        notes = postscript_notes(font["name"], changes, old, new)
    job = Job(source=source, digest=hashlib.sha256(data).digest(),
              target=target, changed=bool(changes), irreversible=irreversible,
              family=font["name"].getDebugName(1) or "?", notes=notes,
              sibling=sibling, sibling_listed=sibling_listed)
    if sibling is not None:
        plan_web_copy(job, font, old, new)
    return job


def check_outputs(jobs):
    """Errors for outputs that would clash, or land where they may not."""
    errors = []
    seen = {}
    for job in jobs:
        for original, target in job.outputs():
            if target != original and os.path.lexists(target) \
                    and not same_entry(original, target):
                errors.append(
                    f"{original}: would be renamed to {target}, which already "
                    "exists; refusing to overwrite it")
            key = os.path.normcase(os.path.abspath(target))
            if key in seen:
                errors.append(
                    f"{target}: both {seen[key]} and {original} would be "
                    "written there")
            seen[key] = original
            st = os.lstat(original)
            if st.st_nlink > 1:
                errors.append(
                    f"{original}: has {st.st_nlink} hard links; rewriting it "
                    "would leave the other names on the old font")
            if not os.access(original, os.W_OK):
                errors.append(
                    f"{original}: is read-only; refusing to replace it")
            if not os.access(target.parent, os.W_OK):
                errors.append(f"{target.parent}: directory is not writable")
            problem = windows_path_problem(original, target)
            if problem:
                errors.append(problem)
    return errors


def plan(paths, old, new):
    """Step 1: every job, or RenameError listing every problem found."""
    errors = []
    jobs = []
    for source, sibling, sibling_listed in collect(paths):
        try:
            jobs.append(plan_job(source, sibling, sibling_listed, old, new))
        except RenameError as exc:
            errors.extend(messages(exc))
    errors += check_outputs(jobs)
    if errors:
        raise RenameError(*errors)
    return jobs


# --------------------------------------------------------------------------
# Step 2: build


def font_bytes(font, woff2=False):
    if woff2 and font.flavor != "woff2":
        font.flavor, font.flavorData = "woff2", None
    buffer = io.BytesIO()
    # Keep the source's table order; like fontTools' own WOFF2 converter.
    font.save(buffer, reorderTables=False)
    return buffer.getvalue()


def stage(target, data, mode):
    """Write data to a new temporary file in target's directory; its path."""
    fd, name = tempfile.mkstemp(
        prefix=TEMP_PREFIX, suffix=TEMP_SUFFIX, dir=target.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return tmp


def reread(path, digest):
    data = read_bytes(path)
    if hashlib.sha256(data).digest() != digest:
        raise RenameError(f"{path}: changed while this batch ran")
    return data


def build_job(job, old, new):
    """Step 2 for one job: write each of its outputs, in full, to a temporary
    file beside its target, and record it in job.staged."""
    if not job.outputs():
        return
    font = open_font(job.source, reread(job.source, job.digest))
    changes, _ = plan_records(font["name"], old, new, job.source)
    apply_changes(changes, job.source)
    builds = []
    if job.changed:
        builds.append((job.source, job.target, False))
    if job.rebuild_sibling:
        reread(job.sibling, job.sibling_digest)
        builds.append((job.sibling, job.sibling_target, True))
    for original, target, woff2 in builds:
        try:
            data = font_bytes(font, woff2=woff2)
        except Exception as exc:  # fontTools raises many types on bad input
            raise RenameError(
                f"{target}: cannot be built from {job.source} "
                f"({type(exc).__name__}: {exc}); a table of the font may be "
                "damaged") from None
        try:
            mode = stat.S_IMODE(os.lstat(original).st_mode)
            job.staged.append((stage(target, data, mode), original, target))
        except OSError as exc:
            raise RenameError(
                f"{target}: cannot be written ({exc.strerror or exc})"
            ) from None


def discard(jobs):
    """Remove every temporary file still staged; a message for each one that
    could not be removed."""
    problems = []
    for job in jobs:
        while job.staged:
            tmp = job.staged.pop()[0]
            try:
                tmp.unlink(missing_ok=True)
            except OSError as exc:
                problems.append(f"{tmp}: this temporary file could not be "
                                f"removed ({exc.strerror or exc})")
    return problems


# --------------------------------------------------------------------------
# Step 3: move


def commit(tmp, original, target):
    """Move a staged file into place. True when original must be removed."""
    if target == original:
        os.replace(tmp, original)
        return False
    if same_entry(original, target):
        # The same file under a name differing only in case, on a
        # case-insensitive file system: rewrite it, then rename it.
        os.replace(tmp, original)
        os.replace(original, target)
        return False
    try:  # reserve the new name, so nothing that appeared is overwritten
        os.close(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_BINARY", 0), 0o600))
    except FileExistsError:
        raise RenameError(
            f"{target}: appeared while this batch ran; refusing to overwrite "
            "it") from None
    try:
        os.replace(tmp, target)
    except BaseException:
        if os.path.lexists(tmp):  # not moved: target is still the empty
            Path(target).unlink(missing_ok=True)  # reservation made above
        raise
    return True


def commit_job(job):
    """Step 3 for one job: move its built files into place."""
    if not job.staged:
        return
    reread(job.source, job.digest)
    if job.rebuild_sibling:
        reread(job.sibling, job.sibling_digest)
    written = []
    try:
        remove = []
        while job.staged:
            tmp, original, target = job.staged[0]
            if commit(tmp, original, target):
                remove.append(original)
            job.staged.pop(0)
            written.append(target.name)
        for original in remove:
            os.unlink(original)
    except Exception as exc:
        if not written:
            raise
        raise RenameError(
            *messages(exc),
            f"{job.source}: handled only in part: {', '.join(written)} "
            "already written; check its files before a rerun") from None


# --------------------------------------------------------------------------
# Reporting


def printable(text):
    """text with every character that could drive or reorder a terminal --
    C0 and C1 controls, DEL, bidirectional controls, line separators --
    escaped as repr() escapes it."""
    return "".join(
        c if not (ord(c) < 32 or 127 <= ord(c) < 160 or c in LAYOUT_CONTROLS)
        else (f"\\x{ord(c):02x}" if ord(c) < 256 else f"\\u{ord(c):04x}")
        for c in text)


def say(line="", stream=None):
    # The report is advisory; a closed or unencodable stream must not stop a
    # batch half way through step 3.
    try:
        print(printable(line), file=stream or sys.stdout, flush=True)
    except (OSError, UnicodeError):
        pass


def complain(line):
    say(line, sys.stderr)


def report(job, new):
    """Print what was done for one job; the number of files reported."""
    count = 1
    if job.changed:
        say(f"  {job.source.name:<38} -> {job.target.name:<36} ({job.family})")
    else:
        say(f"  {job.source.name}: nothing to do ({job.family})")
    if job.rebuild_sibling:
        count += 1
        say(f"  {job.sibling.name:<38} -> {job.sibling_target.name:<36} "
            f"(rebuilt from {job.target.name})")
    elif job.sibling_listed:
        count += 1
        say(f"  {job.sibling.name}: nothing to do (web copy of "
            f"{job.source.name})")
    if job.changed and job.irreversible:
        say(f"    note: swapping FROM and TO will not give {job.source.name} "
            f"back exactly: {job.irreversible}")
    for note in job.notes:
        say(f"    note: {note}")
    return count


# --------------------------------------------------------------------------
# Command line


def family_name(text):
    if not text.strip():
        raise argparse.ArgumentTypeError("a family name cannot be empty")
    if any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise argparse.ArgumentTypeError(
            "a family name cannot contain control characters")
    return text


def parse_args(argv):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("old", metavar="FROM", type=family_name,
                   help='current family, e.g. "Foo Mono Nerd Font"')
    p.add_argument("new", metavar="TO", type=family_name,
                   help='desired family, e.g. "FooM Nerd Font"')
    p.add_argument("fonts", nargs="+", type=Path, metavar="FONT",
                   help="font files to fix (.ttf, .otf, .woff2, .woff)")
    args = p.parse_args(argv)
    if args.old == args.new:
        p.error("FROM and TO are the same")
    return args


def run(jobs, paths, old, new):
    """Steps 1 to 3, filling jobs as it goes; the exit status."""
    try:
        jobs.extend(plan(paths, old, new))
        for job in jobs:
            build_job(job, old, new)
    except Exception as exc:
        for line in messages(exc):
            complain(f"error: {line}")
        for line in discard(jobs):
            complain(f"warning: {line}")
        complain("nothing was changed.")
        return 1

    handled = 0
    for job in jobs:
        try:
            commit_job(job)
        except Exception as exc:
            for line in messages(exc):
                complain(f"error: {line}")
            complain(f"stopped at {job.source}: the {handled} file(s) "
                     "reported above were handled, the ones after it were "
                     "not touched.")
            return 1
        handled += report(job, new)

    if any(job.outputs() for job in jobs):
        say()
        say("verify:  fc-query --format='%{family}|%{style}\\n' <font>")
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    args = parse_args(argv)
    jobs = []
    try:
        return run(jobs, args.fonts, args.old, args.new)
    finally:  # an interruption, too, removes every temporary file left
        for line in discard(jobs):
            complain(f"warning: {line}")


if __name__ == "__main__":
    sys.exit(main())
