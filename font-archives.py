#!/usr/bin/env python3
"""Publish the built fonts as release archives, check them, and fetch them back.

The built fonts (every *.ttf and *.woff2 under noctua-iosevka/, noctua-noto/
and symbols-nerd-font/) are not kept in git. They are published as GitHub
Release assets, split into the zip archives that font-archives.json describes,
and git keeps SHA256SUMS instead: one SHA-256 per built font, committed at the
repository root in the GNU coreutils format, so a tree can be checked with no
tool at all, with `sha256sum -c SHA256SUMS` on Linux or
`shasum -a 256 -c SHA256SUMS` on macOS.

Download and unpack every archive, or only some:

    ./font-archives.py fetch
    ./font-archives.py fetch --archive noctua-noto-ttf.zip symbols-nerd-font.zip

Check the tree against SHA256SUMS, or only the fonts that are present:

    ./font-archives.py verify
    ./font-archives.py verify --allow-missing

Show the archives with file counts and sizes; rewrite SHA256SUMS from the tree;
write dist/*.zip and dist/SHA256SUMS for a release:

    ./font-archives.py list
    ./font-archives.py manifest
    ./font-archives.py pack

(No command above carries a trailing comment: interactive zsh, the default
shell on macOS, passes "# ..." to the command as arguments.)

Commands:
  manifest  Hash every built font present in the tree and write SHA256SUMS
            atomically: "<64 lowercase hex>  <repo-relative POSIX path>", one
            line per font, sorted by path, LF line endings, UTF-8. It refuses
            an empty tree, so running it in a fresh clone cannot erase the list,
            and a tree that lacks fonts the current list names, so running it
            in a partly fetched tree cannot shrink it; --remove-missing drops
            them on purpose, after a font was removed or renamed.
  verify    Check that every SHA256SUMS entry exists and matches, and that no
            built font in the tree is missing from SHA256SUMS. A missing file
            is an error unless --allow-missing, which checks only the files
            present and reports how many are missing. Exit status 0 or 1.
  list      Show each archive with the number and total size of its files
            present in the tree, then whether every built font present belongs
            to exactly one archive. Exit status 1 when one does not, or when
            the tree has a problem (a symbolic link, say).
  pack      Verify strictly, prove that every SHA256SUMS path belongs to
            exactly one archive, then write deterministic zips (packing twice
            gives byte-identical files) and DIR/SHA256SUMS of the zips, to be
            attached to the release. Entry paths are repository-relative:
            unpacking an archive at the repository root restores the layout.
  fetch     Download archives from the release (all of them unless --archive
            is given) and unpack them, writing a font only when its SHA-256
            matches SHA256SUMS. An archive is fetched only if one of its fonts
            is absent or (with --force) different, and it is all or nothing:
            an archive that fails leaves the tree as it was (see Security for
            the one case where the file system can prevent that).

Data files:
  font-archives.json  The repository, the release tag, and the archives: for
                      each one its name, a description, "include" and optional
                      "exclude" globs matched against repo-relative POSIX
                      paths ("*" and "?" never cross a "/"; matching is
                      case-sensitive), and the licence files that travel in it.
  SHA256SUMS          The checksum manifest described above.

Security
--------
The trust anchor is SHA256SUMS as committed: commits in this repository are
signed, so its contents are exactly as trustworthy as the signed commit you
checked out. GitHub marks each signed commit "Verified"; locally,
`git verify-commit` checks one once the signer's public SSH key is in the file
that gpg.ssh.allowedSignersFile names. Nothing here can make up for an
unsigned or tampered checkout. Everything that
comes over the network -- the zip, its directory, its sizes, and the release's
own SHA256SUMS of the archives -- is untrusted input. The rule that follows is
that a font is written under its final name only after its bytes have hashed to
the value in SHA256SUMS. A compromised release, account, CDN or network can then
make `fetch` fail, never make it install a different font. What each refusal
defends against:

  * The base URL must be https:// (TLS with certificate and host name checks,
    the ssl module's defaults), or http:// to a loopback IP literal such as
    127.0.0.1 for a local mirror or a test. A host name, even "localhost", is
    refused for plain http, because name resolution can be redirected. A URL
    with credentials, a query or a fragment is refused. Redirects (GitHub
    answers every asset download with one, to its CDN) are checked against the
    same rule, so an https download cannot be downgraded to plain http.
  * The download is streamed into a temporary file and stopped once it reaches
    MAX_ARCHIVE_SIZE (GitHub's 2 GiB asset limit), whatever Content-Length
    says: a hostile server cannot fill the disk.
  * Before anything is extracted the whole zip directory is checked, using the
    raw entry name (zipfile turns a backslash into "/" on Windows, so the
    normalised name would hide it). Refused: absolute paths, drive letters,
    ".." and "." segments, backslashes, NUL and control characters, characters
    and device names Windows cannot store, and segments ending in a dot or a
    space -- the zip-slip family, which writes outside the repository or onto
    a file other than the one the name seems to say.
  * A zip that the zipfile module cannot read -- a damaged or hostile
    directory, an unsupported zip version, a name that is not valid UTF-8
    under the UTF-8 flag -- is refused like any other bad archive, with a
    message instead of a traceback, and the remaining archives are still
    fetched.
  * Symbolic links and any other non-regular entry are refused: a link written
    by one entry and followed by the next escapes the tree. Nothing is ever
    created as a link.
  * Duplicate entries are refused, and so are names that differ only in case:
    one copy could be checked and another written, and on case-insensitive
    file systems (Windows, macOS) two names land on the same file.
  * Every entry must be a SHA256SUMS path that font-archives.json assigns to
    that archive, or one of that archive's licence files; anything else
    (a script, a dotfile, .git/hooks/...) is refused. An archive that lacks an
    expected file is refused too: the release does not match the checkout.
  * Anything `pack` never writes is refused: encrypted entries (flag bits 0
    and 6), compressed patched data (flag bit 5), compression methods other
    than stored and deflate, and entries that need a zip version above 2.0.
    Each is a feature whose handling (and bugs) this tool has no need to
    trust.
  * Each entry's uncompressed size is capped at MAX_ENTRY_SIZE, both as
    declared and as actually decompressed: a zip bomb stops at the cap.
  * Each font is decompressed into a temporary file created exclusively
    (O_EXCL, so a planted link is never followed) in its destination directory,
    with a hidden name ending in ".part" so it is never taken for a font (and
    git ignores it, should a hard kill leave one behind), and hashed on the
    way. Only when every font of the archive has been staged and matched are
    they moved into place with os.replace. A font that --force replaces is
    first moved aside (".orig.part") and deleted only once the whole archive is
    in place. If any move fails -- on Windows, a font in use cannot be
    replaced -- every move already made is undone: new fonts are removed and
    replaced ones restored, then every staged file (and every directory the
    attempt created) is removed. No partial or unverified file ever appears
    under a font's name. The one thing this cannot promise is an undo that the
    file system itself refuses; the error then names each font left in place
    and where its original was kept. Peak disk use is the download, plus the
    fonts that matched, plus at most one capped entry.
  * Licence entries are compared byte for byte with the tracked file in the
    working tree and are never written: tracked files belong to git, and a
    release cannot change the licence text. A licence missing from the working
    tree cannot be compared, so the archive is refused until git restores it.
  * An existing font with the right hash is left alone. One with a different
    hash may be your own rebuild, so it is refused unless --force. An existing
    destination that is a link or a directory is always refused, and so is a
    destination whose directory resolves outside the repository root (a
    symbolic link in the checkout pointing elsewhere).
  * `manifest` refuses symbolic links (to files or directories) inside the font
    folders, names that are not portable, names that differ only in case, and
    an empty tree. A folder that cannot be listed is a problem for every
    command that looks at the tree (`manifest`, `verify`, `list`, `pack`), and
    a font that cannot be read is one for every command that hashes it
    (`manifest`, `verify`, `pack`): never a silent omission, since `manifest`
    would otherwise drop fonts from the trust anchor, and `verify` would miss
    a font that SHA256SUMS does not list. `pack` verifies
    before writing anything, hashes every font again while packing it (the
    file could change in between), refuses a font larger than fetch's
    MAX_ENTRY_SIZE and an archive of MAX_ARCHIVE_SIZE or more, and replaces the
    previous zips only once every new one is complete.
  * The SHA256SUMS that `pack` writes next to the archives is a convenience for
    people who download a zip by hand; `fetch` never relies on it.

What the licence files are is decided by font-archives.json; that they are
tracked in git is the maintainer's to keep (this tool reads no git data).

Line endings: `manifest` writes SHA256SUMS with LF. git can convert line
endings on checkout (Git for Windows defaults to core.autocrlf=true), so the
reader also accepts a SHA256SUMS in which every line ends in CRLF, as GNU
sha256sum does: the hashes and paths are the same. A mix of CRLF and LF, or a
stray CR, is still refused. Licence entries, though, are compared byte for
byte, so the licence files must be checked out exactly as committed. That is
what these .gitattributes rules guarantee, and the repository needs them:

    /SHA256SUMS -text
    /*/licenses/** -text

-text, not eol=lf: the committed licences mix CRLF and LF files, and both must
come out unchanged. In a checkout made without these rules, fetch refuses an
archive whose licence git converted, and says that line endings are the only
difference.

Determinism: entries are sorted; every entry has the 1980-01-01 00:00:00
timestamp, mode 0644, Unix as creating system and no extra fields; .woff2 is
stored (it is already Brotli-compressed) and everything else is deflated at
level 9. The output is byte-identical between runs with the same zlib. A
different zlib build may deflate differently, but the fonts inside are the
same, and SHA256SUMS is what checks them.

Portability: standard library only (no fontTools); pathlib throughout, no
shelling out, os.replace for every atomic write, "/" inside archives. Written
for Python 3.9 or newer; CI tests it on 3.9, 3.11, 3.14 and the newest Python
(.github/workflows/check.yml).
"""

import argparse
import fnmatch
import hashlib
import http.client
import ipaddress
import json
import os
import re
import secrets
import ssl
import stat
import struct
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants. Tests lower the two caps; every function reads them at call time.

MANIFEST_NAME = "SHA256SUMS"
CONFIG_NAME = "font-archives.json"
FONT_DIRS = ("noctua-iosevka", "noctua-noto", "symbols-nerd-font")
FONT_SUFFIXES = (".ttf", ".woff2")

MAX_ARCHIVE_SIZE = 2 * 1024 ** 3   # every archive, packed or downloaded, must be smaller
MAX_ENTRY_SIZE = 128 * 1024 ** 2   # uncompressed size cap per entry (the largest font is ~25 MB)
CHUNK_SIZE = 1024 * 1024
DOWNLOAD_TIMEOUT = 60              # seconds, per socket operation

ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = stat.S_IFREG | 0o644
ZIP_CREATE_SYSTEM = 3              # Unix, so the mode above is meaningful to unzip
ZIP_EXTRACT_VERSION = 20           # "version needed to extract" that pack writes (2.0)
DEFLATE_LEVEL = 9
TEMP_SUFFIX = ".part"              # fetch's staged fonts and pack's staged zips
BACKUP_SUFFIX = ".orig" + TEMP_SUFFIX  # a font moved aside while --force replaces it
DETAIL_LIMIT = 100                 # lines of detail shown per kind of problem

# General-purpose flag bits of a zip entry that pack never sets (APPNOTE 4.4.4).
_FLAG_ENCRYPTED = 0x01
_FLAG_PATCHED = 0x20
_FLAG_STRONG_ENCRYPTION = 0x40

# What zipfile raises, besides BadZipFile, on a damaged or hostile archive:
# zlib.error and EOFError from a broken deflate stream; RuntimeError, and its
# subclass NotImplementedError, for an encrypted entry, an unsupported flag or
# an unsupported zip version (that one is raised by the ZipFile constructor);
# ValueError, UnicodeDecodeError among them, for a name that is not valid UTF-8
# under the UTF-8 flag; struct.error from a short record. All of them mean the
# same thing here: the archive is refused and nothing is written.
_UNREADABLE_ZIP = (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError,
                   RuntimeError, ValueError, struct.error)

DEFAULT_ROOT = Path(__file__).resolve().parent
HELP = (__doc__ or "").split("\nSecurity\n")[0]  # __doc__ is None under python -OO


class FontArchivesError(Exception):
    """A refusal or failure, with a message meant for the person running the tool."""


# ---------------------------------------------------------------------------
# Paths and globs

_DRIVE = re.compile(r"^[A-Za-z]:")
_UNPORTABLE = frozenset('\\:*?"<>|')
_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)])


def path_problem(path):
    """Why `path` is not a safe, portable, repository-relative POSIX path; None if it is.

    Used for SHA256SUMS paths, licence paths and, on the raw name, every zip
    entry: the same rule decides what may be written and what may be listed.
    """
    if not isinstance(path, str) or not path:
        return "is empty"
    if "\\" in path:
        return "contains a backslash"
    if path.startswith("/"):
        return "is absolute"
    if _DRIVE.match(path):
        return "starts with a drive letter"
    for part in path.split("/"):
        if part == "":
            return "has an empty segment (a leading, trailing or doubled '/')"
        if part in (".", ".."):
            return f"has a {part!r} segment"
        bad = sorted({c for c in part if c in _UNPORTABLE or ord(c) < 32 or ord(c) == 127})
        if bad:
            return "contains characters that are not portable: " + " ".join(repr(c) for c in bad)
        if part[-1] in ". ":
            return "has a segment that ends in a dot or a space"
        if part.split(".")[0].rstrip(" ").upper() in _RESERVED:
            return "uses a name Windows reserves for a device"
    try:
        path.encode("utf-8")
    except UnicodeEncodeError:
        return "is not valid UTF-8"
    return None


def is_font_name(name):
    """True for the file names this tool treats as built fonts (suffix compared case-insensitively)."""
    return name.lower().endswith(FONT_SUFFIXES)


def manifest_path_problem(path):
    """Why `path` cannot be a SHA256SUMS entry; None if it can."""
    why = path_problem(path)
    if why:
        return why
    parts = path.split("/")
    if len(parts) < 2 or parts[0] not in FONT_DIRS:
        return "is not inside " + ", ".join(d + "/" for d in FONT_DIRS)
    if not is_font_name(parts[-1]):
        return "is not a " + " or ".join(FONT_SUFFIXES) + " file"
    return None


def pattern_problem(pattern):
    """Why `pattern` is not an acceptable include/exclude glob; None if it is."""
    if not isinstance(pattern, str) or not pattern:
        return "is empty"
    if "\\" in pattern:
        return "contains a backslash"
    if pattern.startswith("/") or _DRIVE.match(pattern):
        return "is absolute"
    for part in pattern.split("/"):
        if part == "":
            return "has an empty segment"
        if part in (".", ".."):
            return f"has a {part!r} segment"
        if "**" in part:
            return "uses '**', which this tool does not support"
    return None


def glob_match(pattern, path):
    """Match a repo-relative POSIX path against a glob, segment by segment.

    "*" and "?" never cross a "/", and matching is case-sensitive on every
    platform, so the result never depends on where the tool runs.
    """
    pattern_parts = pattern.split("/")
    path_parts = path.split("/")
    return len(pattern_parts) == len(path_parts) and all(
        fnmatch.fnmatchcase(part, pat) for part, pat in zip(path_parts, pattern_parts))


def _native(root, path):
    """The file system path of the repo-relative POSIX `path` under `root`."""
    return Path(root).joinpath(*path.split("/"))


def _rel(root, full):
    return Path(full).relative_to(root).as_posix()


def _case_collisions(paths):
    seen = {}
    found = []
    for path in sorted(paths):
        key = path.casefold()
        if key in seen:
            found.append(f"{seen[key]} and {path} differ only in case; "
                         "they would be one file on Windows and macOS")
        else:
            seen[key] = path
    return found


def _is_link(path):
    """True for a symbolic link, and for an NTFS junction where Python can tell."""
    isjunction = getattr(os.path, "isjunction", None)
    return os.path.islink(path) or bool(isjunction and isjunction(path))


def _details(lines, limit=None):
    limit = DETAIL_LIMIT if limit is None else limit
    lines = list(lines)
    shown = ["  " + line for line in lines[:limit]]
    if len(lines) > limit:
        shown.append(f"  ... and {len(lines) - limit} more")
    return shown


# ---------------------------------------------------------------------------
# font-archives.json

@dataclass(frozen=True)
class Archive:
    name: str
    description: str
    include: tuple
    exclude: tuple
    licenses: tuple

    def matches(self, path):
        return (any(glob_match(p, path) for p in self.include)
                and not any(glob_match(p, path) for p in self.exclude))


@dataclass(frozen=True)
class Config:
    repository: str
    tag: str
    archives: tuple

    def archive(self, name):
        for archive in self.archives:
            if archive.name == name:
                return archive
        raise FontArchivesError(
            f"no archive named {name!r}; font-archives.json has: "
            + ", ".join(a.name for a in self.archives))


_REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+")
_TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")
_ARCHIVE_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*\.zip")


def _no_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise FontArchivesError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def _string_list(value, what, required):
    if value is None and not required:
        return ()
    if not isinstance(value, list) or (required and not value):
        raise FontArchivesError(f"{what} must be a {'non-empty ' if required else ''}list of strings")
    if not all(isinstance(v, str) for v in value):
        raise FontArchivesError(f"{what} must contain only strings")
    if len(set(value)) != len(value):
        raise FontArchivesError(f"{what} lists the same value twice")
    return tuple(value)


def parse_config(data, source=CONFIG_NAME):
    """Parse and validate font-archives.json; a FontArchivesError says what is wrong."""
    try:
        obj = json.loads(data, object_pairs_hook=_no_duplicate_keys)
    except FontArchivesError as exc:
        raise FontArchivesError(f"{source}: {exc}") from None
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError
        raise FontArchivesError(f"{source}: not valid JSON: {exc}") from None
    try:
        return _config_from(obj)
    except FontArchivesError as exc:
        raise FontArchivesError(f"{source}: {exc}") from None


def _config_from(obj):
    if not isinstance(obj, dict):
        raise FontArchivesError("the top level must be an object")
    unknown = set(obj) - {"repository", "tag", "archives"}
    if unknown:
        raise FontArchivesError("unknown keys: " + ", ".join(sorted(unknown)))
    repository, tag, raw_archives = obj.get("repository"), obj.get("tag"), obj.get("archives")
    if not isinstance(repository, str) or not _REPOSITORY.fullmatch(repository):
        raise FontArchivesError("'repository' must look like 'owner/name'")
    if not isinstance(tag, str) or not _TAG.fullmatch(tag):
        raise FontArchivesError("'tag' must be letters, digits and . _ + - (no '/')")
    if not isinstance(raw_archives, list) or not raw_archives:
        raise FontArchivesError("'archives' must be a non-empty list")
    archives, names = [], set()
    for index, raw in enumerate(raw_archives):
        where = f"archives[{index}]"
        if not isinstance(raw, dict):
            raise FontArchivesError(f"{where} must be an object")
        unknown = set(raw) - {"name", "description", "include", "exclude", "licenses"}
        if unknown:
            raise FontArchivesError(f"{where}: unknown keys: " + ", ".join(sorted(unknown)))
        name = raw.get("name")
        if not isinstance(name, str) or not _ARCHIVE_NAME.fullmatch(name):
            raise FontArchivesError(
                f"{where}: 'name' must be lower-case letters, digits and . _ - ending in .zip")
        where = f"archive {name}"
        if name in names:
            raise FontArchivesError(f"{where} is listed twice")
        names.add(name)
        description = raw.get("description")
        if not isinstance(description, str) or not description.strip():
            raise FontArchivesError(f"{where}: 'description' must be a non-empty string")
        include = _string_list(raw.get("include"), f"{where}: 'include'", required=True)
        exclude = _string_list(raw.get("exclude"), f"{where}: 'exclude'", required=False)
        licenses = _string_list(raw.get("licenses"), f"{where}: 'licenses'", required=True)
        for pattern in include + exclude:
            why = pattern_problem(pattern)
            if why:
                raise FontArchivesError(f"{where}: the glob {pattern!r} {why}")
        for path in licenses:
            why = path_problem(path)
            if why:
                raise FontArchivesError(f"{where}: the licence path {path!r} {why}")
            if is_font_name(path):
                raise FontArchivesError(f"{where}: the licence path {path!r} is a font")
        archives.append(Archive(name, description, include, exclude, licenses))
    return Config(repository, tag, tuple(archives))


def load_config(root):
    path = Path(root) / CONFIG_NAME
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise FontArchivesError(f"cannot read {path}: {exc.strerror or exc}") from None
    return parse_config(data, str(path))


# ---------------------------------------------------------------------------
# The tree and SHA256SUMS

@dataclass
class Discovery:
    fonts: list      # sorted repo-relative POSIX paths of the built fonts present
    problems: list   # what makes the tree unfit to be listed or checked


def _where(root, filename):
    """`filename` from an OSError, relative to `root` when it is inside it."""
    try:
        return _rel(root, filename)
    except (TypeError, ValueError):
        return str(filename)


def discover_fonts(root):
    """Find every built font under the three font folders, without following links.

    Whatever keeps a folder or a font from being seen (a permission, an I/O
    error) is recorded as a problem, never skipped in silence: `manifest`
    would otherwise drop fonts from the trust anchor, and `verify` would miss
    a font that SHA256SUMS does not list.
    """
    root = Path(root)
    fonts, problems = [], []

    def unlistable(exc):  # os.walk's onerror: a folder it could not list
        problems.append(f"{_where(root, exc.filename)}: cannot be listed: {exc.strerror or exc}")

    for top in FONT_DIRS:
        base = root / top
        try:
            top_mode = os.lstat(base).st_mode
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError as exc:
            problems.append(f"{top}: cannot be read: {exc.strerror or exc}")
            continue
        if stat.S_ISLNK(top_mode) or _is_link(base):
            problems.append(f"{top}: is a symbolic link; refusing to follow it")
            continue
        if not stat.S_ISDIR(top_mode):
            continue
        for dirpath, dirnames, filenames in os.walk(base, onerror=unlistable, followlinks=False):
            here = Path(dirpath)
            for name in sorted(dirnames):
                if _is_link(here / name):
                    problems.append(f"{_rel(root, here / name)}: is a symbolic link to a "
                                    "directory; refusing to follow it")
                    dirnames.remove(name)
            dirnames.sort()
            for name in sorted(filenames):
                if not is_font_name(name):
                    continue
                full = here / name
                rel = _rel(root, full)
                try:
                    mode = os.lstat(full).st_mode
                except OSError as exc:
                    problems.append(f"{rel}: cannot be read: {exc.strerror or exc}")
                    continue
                if stat.S_ISLNK(mode):
                    problems.append(f"{rel}: is a symbolic link; a built font must be a regular file")
                    continue
                if not stat.S_ISREG(mode):
                    problems.append(f"{rel}: is not a regular file")
                    continue
                why = path_problem(rel)
                if why:
                    problems.append(f"{rel!r}: the name {why}")
                    continue
                fonts.append(rel)
    fonts.sort()
    problems.extend(_case_collisions(fonts))
    return Discovery(fonts, problems)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


_DIGEST = re.compile(r"[0-9a-f]{64}")
_LINE = re.compile(r"([0-9a-f]{64})  (.+)")


def format_manifest(entries):
    """SHA256SUMS bytes for {path: hex digest}: sorted by path, LF, UTF-8."""
    lines = []
    for path in sorted(entries):
        digest = entries[path]
        why = manifest_path_problem(path)
        if why:
            raise FontArchivesError(f"cannot list {path!r} in {MANIFEST_NAME}: it {why}")
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise FontArchivesError(f"{path}: {digest!r} is not a lower-case SHA-256 hex digest")
        lines.append(f"{digest}  {path}\n")
    return "".join(lines).encode("utf-8")


def parse_manifest(data, source=MANIFEST_NAME):
    """Parse SHA256SUMS strictly into {path: hex digest}.

    Strict on purpose: it is the trust anchor, so anything this tool would not
    have written (a stray CR, an unsorted or repeated path, an unsafe path, a
    path outside the font folders) means it was not produced by `manifest`.
    The one transformation accepted is CRLF on every line, which is what git
    makes of the LF file on checkout with core.autocrlf=true (the default of
    Git for Windows); GNU sha256sum accepts it too, and it changes no hash and
    no path.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise FontArchivesError(f"{source}: not valid UTF-8") from None
    if not text:
        raise FontArchivesError(f"{source}: is empty")
    if "\r" in text:
        crlf = text.count("\r\n")
        if crlf != text.count("\r") or crlf != text.count("\n"):
            raise FontArchivesError(
                f"{source}: contains a carriage return that is not part of a CRLF ending on "
                "every line; it must use LF line endings (git's CRLF conversion of every line "
                "is the only exception accepted)")
        text = text.replace("\r\n", "\n")
    if not text.endswith("\n"):
        raise FontArchivesError(f"{source}: does not end with a newline")
    entries, previous = {}, None
    for number, line in enumerate(text[:-1].split("\n"), 1):
        match = _LINE.fullmatch(line)
        if not match:
            raise FontArchivesError(
                f"{source}: line {number} is not '<64 lower-case hex digits>  <path>'")
        digest, path = match.groups()
        why = manifest_path_problem(path)
        if why:
            raise FontArchivesError(f"{source}: line {number}: {path!r} {why}")
        if path in entries:
            raise FontArchivesError(f"{source}: line {number}: {path} is listed twice")
        if previous is not None and path < previous:
            raise FontArchivesError(f"{source}: line {number}: {path} is out of order")
        entries[path] = digest
        previous = path
    collisions = _case_collisions(entries)
    if collisions:
        raise FontArchivesError(f"{source}: " + collisions[0])
    return entries


def read_manifest(root):
    path = Path(root) / MANIFEST_NAME
    if _is_link(path):
        raise FontArchivesError(f"{path} is a symbolic link; refusing to trust it")
    if not path.is_file():
        raise FontArchivesError(
            f"{path} not found. It is committed with the repository: check out a commit that "
            "has it (or, after building every font, create it with 'manifest').")
    return parse_manifest(path.read_bytes(), str(path))


def _create_exclusive(directory, base, suffix):
    """Create a new file next to its destination; O_EXCL never follows a planted link."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    for _ in range(16):
        candidate = Path(directory) / f".{base}.{secrets.token_hex(8)}{suffix}"
        try:
            return os.open(candidate, flags, 0o644), candidate
        except FileExistsError:
            continue
    raise FontArchivesError(f"cannot create a temporary file in {directory}")


def _unlink_quietly(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def atomic_write(path, data):
    """Write `data` to `path` through a temporary file and os.replace."""
    path = Path(path)
    fd, temp = _create_exclusive(path.parent, path.name, ".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except BaseException:
        _unlink_quietly(temp)
        raise


def write_manifest(root, remove_missing=False):
    """Hash the built fonts present and write SHA256SUMS; return (new, previous or None).

    A font listed in the previous SHA256SUMS but absent from the tree is a refusal unless
    remove_missing is true: in a partially fetched tree, rewriting the list would otherwise
    drop every font that was simply not fetched, and the next release would lose them.
    """
    root = Path(root)
    found = discover_fonts(root)
    if found.problems:
        raise FontArchivesError("refusing to write SHA256SUMS:\n" + "\n".join(_details(found.problems)))
    if not found.fonts:
        raise FontArchivesError(
            "no built fonts found under " + ", ".join(d + "/" for d in FONT_DIRS)
            + "; refusing to write an empty SHA256SUMS (in a fresh clone, run 'fetch' instead)")
    entries, unreadable = {}, []
    for path in found.fonts:
        try:
            entries[path] = sha256_file(_native(root, path))
        except OSError as exc:
            unreadable.append(f"{path}: cannot be read: {exc.strerror or exc}")
    if unreadable:
        raise FontArchivesError("refusing to write SHA256SUMS:\n" + "\n".join(_details(unreadable)))
    data = format_manifest(entries)
    previous = None
    target = root / MANIFEST_NAME
    if target.is_file() and not _is_link(target):
        try:
            previous = parse_manifest(target.read_bytes())
        except FontArchivesError:
            previous = None
    if previous is not None and not remove_missing:
        gone = sorted(set(previous) - set(entries))
        if gone:
            raise FontArchivesError(
                f"refusing to write {MANIFEST_NAME}: {len(gone)} font(s) it lists are not in the "
                "tree, and rewriting it would drop them:\n" + "\n".join(_details(gone))
                + "\nFetch them first ('fetch'), or pass --remove-missing if they were removed "
                "or renamed on purpose.")
    atomic_write(target, data)
    return entries, previous


@dataclass
class VerifyResult:
    listed: int
    matched: list
    mismatched: list
    missing: list
    unlisted: list
    problems: list
    allow_missing: bool

    @property
    def ok(self):
        return not (self.mismatched or self.unlisted or self.problems
                    or (self.missing and not self.allow_missing))


def verify_tree(root, manifest, allow_missing=False):
    """Compare the tree with SHA256SUMS; see VerifyResult.ok for the verdict."""
    root = Path(root)
    found = discover_fonts(root)
    problems = list(found.problems)
    matched, mismatched, missing = [], [], []
    for path in sorted(manifest):
        full = _native(root, path)
        try:
            mode = os.lstat(full).st_mode
        except (FileNotFoundError, NotADirectoryError):
            missing.append(path)
            continue
        except OSError as exc:
            problems.append(f"{path}: cannot be read: {exc.strerror or exc}")
            continue
        if stat.S_ISLNK(mode) or _is_link(full):
            continue  # discover_fonts has reported it; a link is never counted as a match
        if not stat.S_ISREG(mode):
            problems.append(f"{path}: is not a regular file")
            continue
        try:
            digest = sha256_file(full)
        except OSError as exc:
            problems.append(f"{path}: cannot be read: {exc.strerror or exc}")
            continue
        (matched if digest == manifest[path] else mismatched).append(path)
    unlisted = [path for path in found.fonts if path not in manifest]
    return VerifyResult(len(manifest), matched, mismatched, missing, unlisted, problems, allow_missing)


def verify_report(result):
    lines = []
    lines += [f"MISMATCH  {p}" for p in result.mismatched]
    if not result.allow_missing:
        lines += [f"MISSING   {p}" for p in result.missing]
    lines += [f"UNLISTED  {p} (a built font that {MANIFEST_NAME} does not list)" for p in result.unlisted]
    lines += [f"PROBLEM   {p}" for p in result.problems]
    shown = _details(lines)
    shown.append(
        f"{result.listed} listed in {MANIFEST_NAME}: {len(result.matched)} match, "
        f"{len(result.mismatched)} differ, {len(result.missing)} missing"
        + (" (allowed)" if result.allow_missing else "")
        + f"; {len(result.unlisted)} built fonts not listed; {len(result.problems)} other problems")
    shown.append("OK" if result.ok else "FAILED")
    return shown


# ---------------------------------------------------------------------------
# Archives: which file goes where

@dataclass
class Assignment:
    by_archive: dict   # archive name -> sorted paths that belong to it alone
    orphans: list      # paths no archive takes
    duplicates: dict   # path -> names of the archives that all take it

    @property
    def ok(self):
        return not self.orphans and not self.duplicates


def assign(paths, config):
    by_archive = {archive.name: [] for archive in config.archives}
    orphans, duplicates = [], {}
    for path in sorted(paths):
        owners = [archive.name for archive in config.archives if archive.matches(path)]
        if not owners:
            orphans.append(path)
        elif len(owners) > 1:
            duplicates[path] = owners
        else:
            by_archive[owners[0]].append(path)
    return Assignment(by_archive, orphans, duplicates)


def coverage_report(assignment, what="built fonts"):
    lines = []
    if assignment.orphans:
        lines.append(f"{len(assignment.orphans)} {what} belong to no archive:")
        lines += _details(assignment.orphans)
    if assignment.duplicates:
        lines.append(f"{len(assignment.duplicates)} {what} belong to more than one archive:")
        lines += _details(f"{p}: {', '.join(names)}" for p, names in assignment.duplicates.items())
    return lines


# ---------------------------------------------------------------------------
# pack

def _set_compress_level(info, level):
    try:
        info.compress_level = level      # Python 3.13 and newer
    except AttributeError:
        info._compresslevel = level      # Python 3.12 and older: same field, private name


def _zip_info(arcname, size):
    info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE_TIME)
    info.create_system = ZIP_CREATE_SYSTEM
    info.external_attr = ZIP_MODE << 16
    info.file_size = size
    if arcname.lower().endswith(".woff2"):
        info.compress_type = zipfile.ZIP_STORED   # WOFF2 is Brotli inside already
    else:
        info.compress_type = zipfile.ZIP_DEFLATED
        _set_compress_level(info, DEFLATE_LEVEL)
    return info


def _write_zip(handle, root, entries, name):
    """Write `entries` [(arcname, expected digest or None)] into a zip on `handle`.

    allowZip64 is on although no archive may need it: a refusal raised inside
    the `with` block makes ZipFile.close() write the central directory of what
    was written so far, and past 2 GiB that needs ZIP64. With allowZip64 off,
    close() would raise LargeZipFile and hide the refusal behind a traceback.
    Within the limits (entries up to MAX_ENTRY_SIZE, archives under
    MAX_ARCHIVE_SIZE, at most 65535 entries) zipfile writes no ZIP64 record
    either way, so the bytes of a valid archive are the same.
    """
    with zipfile.ZipFile(handle, "w", allowZip64=True) as archive:
        for arcname, expected in entries:
            source = _native(root, arcname)
            info = _zip_info(arcname, source.stat().st_size)
            digest = hashlib.sha256()
            with open(source, "rb") as src, archive.open(info, "w") as out:
                for chunk in iter(lambda: src.read(CHUNK_SIZE), b""):
                    digest.update(chunk)
                    out.write(chunk)
            if expected is not None and digest.hexdigest() != expected:
                raise FontArchivesError(f"{arcname} changed while it was being packed; run verify")
            if handle.tell() >= MAX_ARCHIVE_SIZE:
                raise FontArchivesError(
                    f"{name} would reach {MAX_ARCHIVE_SIZE} bytes; a release asset must be "
                    "smaller: split the archive in font-archives.json")


def pack(root, config, out_dir):
    """Write every archive and out_dir/SHA256SUMS; return [(name, files, size, digest)]."""
    root = Path(root)
    out_dir = Path(out_dir)
    manifest = read_manifest(root)
    result = verify_tree(root, manifest, allow_missing=False)
    if not result.ok:
        raise FontArchivesError(
            f"refusing to pack: the tree does not match {MANIFEST_NAME}\n" + "\n".join(verify_report(result)))
    assignment = assign(manifest, config)
    if not assignment.ok:
        raise FontArchivesError(
            f"refusing to pack: font-archives.json does not give every {MANIFEST_NAME} path "
            "to exactly one archive\n" + "\n".join(coverage_report(assignment, f"{MANIFEST_NAME} paths")))
    empty = [a.name for a in config.archives if not assignment.by_archive[a.name]]
    if empty:
        raise FontArchivesError("refusing to pack archives with no font in them: " + ", ".join(empty))
    problems = []
    for license_path in sorted({p for a in config.archives for p in a.licenses}):
        full = _native(root, license_path)
        if _is_link(full) or not full.is_file():
            problems.append(f"licence file {license_path} is missing or not a regular file")
    for path in sorted(manifest):
        size = _native(root, path).stat().st_size
        if size > MAX_ENTRY_SIZE:
            problems.append(f"{path} is {size} bytes, over the {MAX_ENTRY_SIZE}-byte cap fetch enforces")
    if os.path.normcase(os.path.realpath(out_dir)) == os.path.normcase(os.path.realpath(root)):
        problems.append(f"the output directory is the repository root, where {out_dir / MANIFEST_NAME} "
                        f"would overwrite the committed {MANIFEST_NAME}; choose another --out")
    elif os.path.lexists(out_dir) and not out_dir.is_dir():
        problems.append(f"the output directory {out_dir} exists and is not a directory")
    if problems:
        raise FontArchivesError("refusing to pack:\n" + "\n".join(_details(problems)))

    out_dir.mkdir(parents=True, exist_ok=True)
    staged = []
    try:
        for archive in config.archives:
            entries = sorted([(p, manifest[p]) for p in assignment.by_archive[archive.name]]
                             + [(p, None) for p in archive.licenses])
            fd, temp = _create_exclusive(out_dir, archive.name, TEMP_SUFFIX)
            staged.append((temp, out_dir / archive.name))
            with os.fdopen(fd, "wb") as handle:
                _write_zip(handle, root, entries, archive.name)
                handle.flush()
                os.fsync(handle.fileno())
            size = temp.stat().st_size
            if size >= MAX_ARCHIVE_SIZE:
                raise FontArchivesError(
                    f"{archive.name} is {size} bytes; a release asset must be smaller than "
                    f"{MAX_ARCHIVE_SIZE}: split the archive in font-archives.json")
        results = []
        for (temp, final), archive in zip(staged, config.archives):
            results.append((archive.name, len(assignment.by_archive[archive.name]),
                            temp.stat().st_size, sha256_file(temp)))
        for temp, final in staged:
            os.replace(temp, final)
        sums = "".join(f"{digest}  {name}\n" for name, _, _, digest in sorted(results))
        atomic_write(out_dir / MANIFEST_NAME, sums.encode("utf-8"))
        return results
    finally:
        for temp, _ in staged:
            _unlink_quietly(temp)


# ---------------------------------------------------------------------------
# fetch: the network

def url_problem(url, allow_loopback_http):
    """Why `url` may not be downloaded from; None if it may."""
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
        parts.port  # raises ValueError for a malformed port
    except ValueError as exc:
        return f"is not a valid URL ({exc})"
    if parts.scheme not in ("https", "http"):
        if not parts.scheme:
            return "has no scheme; only https:// is allowed"
        return f"uses the scheme {parts.scheme!r}; only https:// is allowed"
    if parts.username is not None or parts.password is not None:
        return "carries credentials"
    if not host:
        return "has no host"
    if parts.scheme == "https":
        return None
    if not allow_loopback_http:
        return "uses plain http://, which is allowed only from a loopback base URL"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return ("uses plain http:// to a host name; plain http:// is allowed only to a "
                "loopback IP address such as 127.0.0.1")
    if not address.is_loopback:
        return "uses plain http:// to an address that is not loopback"
    return None


def check_base_url(url):
    """Validate a --base-url and return it ending in '/'; refuse anything unsafe."""
    why = url_problem(url, allow_loopback_http=True)
    if why is None:
        parts = urllib.parse.urlsplit(url)
        if parts.query or parts.fragment or url.endswith(("?", "#")):
            why = "has a query or a fragment"
    if why:
        raise FontArchivesError(f"refusing the base URL {url!r}: it {why}")
    return url if url.endswith("/") else url + "/"


def default_base_url(config, tag=None):
    tag = config.tag if tag is None else tag
    if not _TAG.fullmatch(tag):
        raise FontArchivesError(f"refusing the tag {tag!r}: use letters, digits and . _ + - only")
    return f"https://github.com/{config.repository}/releases/download/{tag}/"


class _RedirectPolicy(urllib.request.HTTPRedirectHandler):
    """Apply the base URL rule to every redirect, so https is never downgraded."""

    max_redirections = 5

    def __init__(self, allow_loopback_http):
        super().__init__()
        self.allow_loopback_http = allow_loopback_http

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        why = url_problem(newurl, self.allow_loopback_http)
        if why:
            raise FontArchivesError(f"refusing the redirect to {newurl}: it {why}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _opener(url):
    """The opener for `url`: the ssl module's TLS checks and the redirect rule of its scheme.

    Only a plain-http (loopback) base URL may be redirected to plain http; an
    https download stays https through every redirect.
    """
    loopback = urllib.parse.urlsplit(url).scheme == "http"
    handlers = [_RedirectPolicy(allow_loopback_http=loopback),
                urllib.request.HTTPSHandler(context=ssl.create_default_context())]
    if loopback:
        handlers.append(urllib.request.ProxyHandler({}))  # a loopback mirror never goes via a proxy
    return urllib.request.build_opener(*handlers)


def download(url, handle):
    """Stream `url` into the binary file `handle`, refusing MAX_ARCHIVE_SIZE bytes or more."""
    why = url_problem(url, allow_loopback_http=True)
    if why:
        raise FontArchivesError(f"refusing to download {url}: it {why}")
    opener = _opener(url)
    request = urllib.request.Request(url, headers={
        "User-Agent": "noctua-fonts font-archives.py", "Accept": "application/octet-stream"})
    cap = MAX_ARCHIVE_SIZE
    try:
        with opener.open(request, timeout=DOWNLOAD_TIMEOUT) as response:
            status = getattr(response, "status", None)
            if status != 200:
                raise FontArchivesError(f"{url} answered HTTP {status}, not 200")
            declared = response.headers.get("Content-Length")
            if declared is not None:
                try:
                    declared_size = int(declared)
                except ValueError:
                    raise FontArchivesError(f"{url} sent an invalid Content-Length") from None
                if declared_size >= cap:
                    raise FontArchivesError(
                        f"{url} declares {declared_size} bytes; an archive must be smaller than {cap}")
            total = 0
            for chunk in iter(lambda: response.read(CHUNK_SIZE), b""):
                total += len(chunk)
                if total >= cap:
                    raise FontArchivesError(f"{url} sent {cap} bytes or more; an archive must be smaller")
                handle.write(chunk)
            return total
    except urllib.error.HTTPError as exc:
        raise FontArchivesError(f"download failed: HTTP {exc.code} {exc.reason} for {url}") from None
    except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
        reason = getattr(exc, "reason", None) or exc
        raise FontArchivesError(f"download failed for {url}: {reason}") from None


# ---------------------------------------------------------------------------
# fetch: unpacking

@dataclass
class FetchOutcome:
    name: str
    written: list      # fonts written (absent before, or replaced with --force)
    present: list      # fonts already present with the right hash
    licenses: int      # licence entries compared with the tracked files
    downloaded: bool
    leftovers: list = field(default_factory=list)  # replaced originals that could not be deleted


def _inside(real_root, path):
    """True when `path`, with every link in it resolved, stays inside `real_root`."""
    real = os.path.normcase(os.path.realpath(path))
    try:
        return os.path.commonpath([real_root, real]) == real_root
    except ValueError:  # different drives on Windows
        return False


def _make_dirs(directory, root, created):
    """Create `directory` and its missing parents below `root`, recording each one."""
    missing = []
    current = Path(directory)
    while not current.exists():
        if current == root or current.parent == current:
            break
        missing.append(current)
        current = current.parent
    for path in reversed(missing):
        path.mkdir()
        created.append(path)
    if not Path(directory).is_dir():
        raise FontArchivesError(f"{directory} is not a directory")


def _read_entry(archive, info, out=None):
    """Hash (and optionally copy) one entry, stopping at MAX_ENTRY_SIZE whatever it declared."""
    digest = hashlib.sha256()
    total = 0
    with archive.open(info) as src:
        for chunk in iter(lambda: src.read(CHUNK_SIZE), b""):
            total += len(chunk)
            if total > MAX_ENTRY_SIZE:
                raise FontArchivesError(
                    f"entry {info.orig_filename!r} decompresses past the {MAX_ENTRY_SIZE}-byte cap")
            digest.update(chunk)
            if out is not None:
                out.write(chunk)
    return digest.hexdigest()


def _check_listing(archive, spec, expected_fonts):
    """Check the whole zip directory before anything is read; return {name: ZipInfo}."""
    expected_licenses = set(spec.licenses)
    expected = set(expected_fonts) | expected_licenses
    problems, entries, names, folded = [], {}, set(), {}
    for info in archive.infolist():
        raw = info.orig_filename
        why = path_problem(raw)
        if why:
            problems.append(f"entry {raw!r} {why}")
            continue
        if info.filename != raw:
            problems.append(f"entry {raw!r} is not stored under its own name")
            continue
        if raw in names:
            problems.append(f"entry {raw!r} is a duplicate entry")
            continue
        names.add(raw)
        key = raw.casefold()
        if key in folded:
            problems.append(f"entries {folded[key]!r} and {raw!r} differ only in case")
            continue
        folded[key] = raw
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind == stat.S_IFLNK:
            problems.append(f"entry {raw!r} is a symbolic link")
            continue
        if kind not in (0, stat.S_IFREG) or info.external_attr & 0x10:
            problems.append(f"entry {raw!r} is not a regular file")
            continue
        if info.flag_bits & (_FLAG_ENCRYPTED | _FLAG_STRONG_ENCRYPTION):
            problems.append(f"entry {raw!r} is encrypted")
            continue
        if info.flag_bits & _FLAG_PATCHED:
            problems.append(f"entry {raw!r} holds compressed patched data (flag bit 5)")
            continue
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            problems.append(f"entry {raw!r} uses compression method {info.compress_type}; "
                            "only stored and deflate are accepted")
            continue
        if info.extract_version > ZIP_EXTRACT_VERSION:
            problems.append(f"entry {raw!r} needs zip version {info.extract_version / 10:.1f}; "
                            f"pack writes {ZIP_EXTRACT_VERSION / 10:.1f}")
            continue
        if info.file_size > MAX_ENTRY_SIZE:
            problems.append(f"entry {raw!r} declares {info.file_size} bytes, over the "
                            f"{MAX_ENTRY_SIZE}-byte cap per entry")
            continue
        if raw not in expected:
            problems.append(f"entry {raw!r} is unexpected: it is neither a {MANIFEST_NAME} path "
                            f"assigned to {spec.name} nor one of its licence files")
            continue
        entries[raw] = info
    absent = sorted(expected - names)
    if absent:
        problems.append(f"the archive lacks {len(absent)} expected files: " + ", ".join(absent[:5])
                        + (" ..." if len(absent) > 5 else ""))
    if problems:
        raise FontArchivesError(f"{spec.name}: refused, nothing written:\n" + "\n".join(_details(problems)))
    return entries


_LINE_ENDING_CHECK_LIMIT = 1024 * 1024  # licence files are a few KB


def _differs_only_in_line_endings(archive, info, local):
    """True when the entry and the local file are the same text once every CRLF is read as LF."""
    if info.file_size > _LINE_ENDING_CHECK_LIMIT or local.stat().st_size > _LINE_ENDING_CHECK_LIMIT:
        return False
    theirs, ours = archive.read(info), local.read_bytes()
    return theirs != ours and theirs.replace(b"\r\n", b"\n") == ours.replace(b"\r\n", b"\n")


def _discard(path):
    """Remove a temporary file of ours, best effort: a failure here must not hide the real error."""
    try:
        os.unlink(path)
    except OSError:
        pass


def _move_aside(dest):
    """Rename the existing `dest` to an unused hidden name next to it; return that name."""
    for _ in range(16):
        backup = dest.parent / f".{dest.name}.{secrets.token_hex(8)}{BACKUP_SUFFIX}"
        if not os.path.lexists(backup):
            os.replace(dest, backup)
            return backup
    raise FontArchivesError(f"cannot find an unused name next to {dest}")


def _move_into_place(temp, dest, path, action, moves, name):
    """Move one verified font into place, recording in `moves` how to undo it."""
    if action == "replace":
        if _is_link(dest) or not os.path.isfile(dest):
            raise FontArchivesError(
                f"{name}: refused: {path} changed during the download and is no longer a regular file")
        moves.append((dest, _move_aside(dest)))  # recorded only once the original is aside
        os.replace(temp, dest)
    else:
        if os.path.lexists(dest):
            raise FontArchivesError(f"{name}: refused: {path} appeared during the download; fetch again")
        os.replace(temp, dest)
        moves.append((dest, None))


def _roll_back(root, moves):
    """Undo `moves` [(dest, original moved aside or None)], newest first; return what is left."""
    left = []
    for dest, backup in reversed(moves):
        try:
            if backup is None:
                os.unlink(dest)
            else:
                os.replace(backup, dest)
        except FileNotFoundError:
            if backup is not None:
                left.append(f"{_where(root, dest)}: its original, moved aside to "
                            f"{_where(root, backup)}, has disappeared")
        except OSError as exc:
            if backup is None:
                left.append(f"{_where(root, dest)}: a verified font from the archive, could not be "
                            f"removed ({exc.strerror or exc})")
            else:
                left.append(f"{_where(root, dest)}: could not be restored ({exc.strerror or exc}); "
                            f"the original is at {_where(root, backup)}")
    return left


def _unpack(root, archive, spec, assigned, manifest, plan):
    """Check, stage, verify and move into place; return (fonts written, originals not deleted)."""
    entries = _check_listing(archive, spec, assigned)
    real_root = os.path.normcase(os.path.realpath(root))
    for license_path in sorted(spec.licenses):
        local = _native(root, license_path)
        if _is_link(local) or not local.is_file():
            raise FontArchivesError(
                f"{spec.name}: refused, nothing written: the licence file {license_path} is missing "
                "from the working tree (restore it from git), so its entry cannot be compared")
        if _read_entry(archive, entries[license_path]) != sha256_file(local):
            why = "differs from the tracked file"
            if _differs_only_in_line_endings(archive, entries[license_path], local):
                why += (" only in its line endings: git converted the working-tree copy on checkout "
                        "(core.autocrlf), which the repository's .gitattributes must prevent with "
                        "'-text' for the licence files; a clone made with "
                        "'git clone -c core.autocrlf=false' has the committed bytes")
            raise FontArchivesError(
                f"{spec.name}: refused, nothing written: the licence entry {license_path} {why}")
    wanted = sorted(p for p, action in plan.items() if action != "present")
    staged, created, moves, failed = [], [], [], True
    try:
        for path in wanted:
            dest = _native(root, path)
            _make_dirs(dest.parent, Path(root), created)
            if not _inside(real_root, dest.parent):
                raise FontArchivesError(f"{spec.name}: refused: {path} resolves outside the repository")
            fd, temp = _create_exclusive(dest.parent, dest.name, TEMP_SUFFIX)
            staged.append((temp, dest, path))
            with os.fdopen(fd, "wb") as out:
                got = _read_entry(archive, entries[path], out)
                out.flush()
                os.fsync(out.fileno())
            if got != manifest[path]:
                raise FontArchivesError(
                    f"{spec.name}: refused, nothing written: hash mismatch for {path}: the archive has "
                    f"{got}, {MANIFEST_NAME} says {manifest[path]}")
        # Every font is staged and verified. Moving them into place is the only
        # step that touches existing names, so it is undone as a whole on failure.
        try:
            for temp, dest, path in staged:
                _move_into_place(temp, dest, path, plan[path], moves, spec.name)
        except BaseException as exc:
            left = _roll_back(root, moves)
            if left and isinstance(exc, Exception):
                raise FontArchivesError(
                    f"{spec.name}: failed ({exc}), and undoing the moves already made failed too; "
                    "left as it is:\n" + "\n".join(_details(left))) from None
            if left:  # interrupted: say what is left, then stop as asked
                print(f"{spec.name}: interrupted; left as it is:\n" + "\n".join(_details(left)),
                      file=sys.stderr, flush=True)
            raise
        failed = False
    finally:
        for temp, _, _ in staged:
            _discard(temp)
        if failed:
            for directory in reversed(created):
                try:
                    directory.rmdir()
                except OSError:
                    pass
    leftovers = []
    for _, backup in moves:
        if backup is not None:
            try:
                os.unlink(backup)
            except FileNotFoundError:
                pass
            except OSError:
                leftovers.append(_where(root, backup))
    return wanted, leftovers


def fetch_archive(root, spec, assigned, manifest, base_url, force=False, log=None):
    """Fetch one archive; raise FontArchivesError on any refusal, leaving the tree as it was."""
    root = Path(root)
    real_root = os.path.normcase(os.path.realpath(root))
    plan, problems = {}, []
    for path in assigned:
        dest = _native(root, path)
        if not _inside(real_root, dest.parent):
            problems.append(f"{path}: its directory resolves outside the repository")
        elif os.path.lexists(dest):
            if _is_link(dest) or not dest.is_file():
                problems.append(f"{path}: exists and is not a regular file; remove it first")
            elif sha256_file(dest) == manifest[path]:
                plan[path] = "present"
            elif force:
                plan[path] = "replace"
            else:
                problems.append(f"{path}: exists with a different SHA-256; pass --force to replace it")
        else:
            plan[path] = "write"
    if problems:
        raise FontArchivesError(f"{spec.name}: refused before downloading:\n" + "\n".join(_details(problems)))
    present = sorted(p for p, action in plan.items() if action == "present")
    if len(present) == len(assigned):
        return FetchOutcome(spec.name, [], present, 0, downloaded=False)
    url = base_url + urllib.parse.quote(spec.name)
    if log:
        log(f"{spec.name}: downloading {url}")
    with tempfile.TemporaryDirectory(prefix="font-archives-") as scratch:
        zip_path = Path(scratch) / "download.zip"
        with open(zip_path, "wb") as handle:
            download(url, handle)
        try:
            with zipfile.ZipFile(zip_path) as archive:
                written, leftovers = _unpack(root, archive, spec, assigned, manifest, plan)
        except OSError as exc:  # a local failure (disk, permission, a font in use): undone
            raise FontArchivesError(f"{spec.name}: failed ({exc}); the tree was left as it was") from None
        except _UNREADABLE_ZIP as exc:  # whatever zipfile raises on a hostile or damaged zip
            raise FontArchivesError(
                f"{spec.name}: refused, nothing written: not a valid zip archive: "
                f"{type(exc).__name__}: {exc}") from None
    return FetchOutcome(spec.name, written, present, len(spec.licenses), downloaded=True,
                        leftovers=leftovers)


def fetch(root, config, names=None, base_url=None, tag=None, force=False, log=None):
    """Fetch the named archives (all by default); return [(name, outcome or None, error or None)]."""
    root = Path(root)
    if base_url is not None and tag is not None:
        raise FontArchivesError("--tag and --base-url cannot be combined")
    base = check_base_url(base_url) if base_url is not None else default_base_url(config, tag)
    manifest = read_manifest(root)
    assignment = assign(manifest, config)
    if not assignment.ok:
        raise FontArchivesError(
            f"font-archives.json does not give every {MANIFEST_NAME} path to exactly one archive\n"
            + "\n".join(coverage_report(assignment, f"{MANIFEST_NAME} paths")))
    wanted = list(dict.fromkeys(names)) if names else [a.name for a in config.archives]
    specs = [config.archive(name) for name in wanted]
    results = []
    for spec in specs:
        try:
            outcome = fetch_archive(root, spec, assignment.by_archive[spec.name], manifest, base, force, log)
            results.append((spec.name, outcome, None))
        except FontArchivesError as exc:
            results.append((spec.name, None, str(exc)))
        except OSError as exc:  # e.g. an existing font that cannot be read; go on with the rest
            results.append((spec.name, None, f"{spec.name}: failed before unpacking: {exc}"))
    return results


# ---------------------------------------------------------------------------
# Command line

def _size(n):
    return f"{n / 1024 ** 2:,.1f} MiB"


def _say(*lines):
    for line in lines:
        print(line, flush=True)


def cmd_manifest(args):
    entries, previous = write_manifest(args.root, remove_missing=args.remove_missing)
    _say(f"wrote {MANIFEST_NAME}: {len(entries)} built fonts")
    if previous is not None:
        added = sorted(set(entries) - set(previous))
        removed = sorted(set(previous) - set(entries))
        changed = sorted(p for p in set(entries) & set(previous) if entries[p] != previous[p])
        _say(f"compared with the previous {MANIFEST_NAME}: {len(added)} added, {len(removed)} removed, "
             f"{len(changed)} changed, {len(entries) - len(added) - len(changed)} unchanged")
        _say(*_details([f"added    {p}" for p in added] + [f"removed  {p}" for p in removed]
                       + [f"changed  {p}" for p in changed]))
    return 0


def cmd_verify(args):
    result = verify_tree(args.root, read_manifest(args.root), allow_missing=args.allow_missing)
    _say(*verify_report(result))
    return 0 if result.ok else 1


def cmd_list(args):
    config = load_config(args.root)
    found = discover_fonts(args.root)
    assignment = assign(found.fonts, config)
    width = max(len(a.name) for a in config.archives)
    _say(f"{'archive':<{width}}  {'files':>5}  {'size':>12}")
    total_files = total_bytes = 0
    for archive in config.archives:
        paths = assignment.by_archive[archive.name]
        size = sum(_native(args.root, p).stat().st_size for p in paths)
        total_files += len(paths)
        total_bytes += size
        _say(f"{archive.name:<{width}}  {len(paths):>5}  {_size(size):>12}")
    _say(f"{'total':<{width}}  {total_files:>5}  {_size(total_bytes):>12}")
    manifest_path = Path(args.root) / MANIFEST_NAME
    if manifest_path.is_file():
        try:
            listed = read_manifest(args.root)
            # os.path.isfile, not Path.is_file: inside a folder that cannot be read the
            # latter raises, and that folder is already reported as a problem below.
            present = sum(1 for p in listed if os.path.isfile(_native(args.root, p)))
            _say(f"{MANIFEST_NAME} lists {len(listed)} built fonts; {present} of them are present")
        except FontArchivesError as exc:
            _say(f"{MANIFEST_NAME} cannot be read: {exc}")
    else:
        _say(f"no {MANIFEST_NAME} yet")
    lines = coverage_report(assignment)
    if found.problems:
        lines.append("problems in the tree:")
        lines += _details(found.problems)
    if lines:
        _say(*lines)
        return 1
    _say(f"every built font present ({len(found.fonts)}) belongs to exactly one archive")
    return 0


def cmd_pack(args):
    out = args.out if args.out is not None else Path(args.root) / "dist"
    results = pack(args.root, load_config(args.root), out)
    width = max(len(name) for name, _, _, _ in results)
    for name, files, size, digest in results:
        _say(f"{name:<{width}}  {files:>4} fonts  {_size(size):>12}  {digest}")
    _say(f"wrote {len(results)} archives and {Path(out) / MANIFEST_NAME}")
    return 0


def cmd_fetch(args):
    results = fetch(args.root, load_config(args.root), names=args.archive, base_url=args.base_url,
                    tag=args.tag, force=args.force, log=_say)
    failed = 0
    for name, outcome, error in results:
        if error:
            failed += 1
            print(f"error: {error}", file=sys.stderr, flush=True)
        elif not outcome.downloaded:
            _say(f"{name}: up to date ({len(outcome.present)} fonts), not downloaded")
        else:
            _say(f"{name}: {len(outcome.written)} written, {len(outcome.present)} already present, "
                 f"{outcome.licenses} licence files match")
            for path in outcome.leftovers:
                _say(f"{name}: note: the replaced original {path} could not be deleted; delete it by hand")
    _say(f"{len(results) - failed} of {len(results)} archives fetched or up to date"
         + (f"; {failed} failed" if failed else ""))
    return 1 if failed else 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="font-archives.py", description=HELP,
        epilog="The security reasoning behind every refusal is in the module docstring.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, metavar="DIR",
                        help="the repository root (default: the directory that holds this script)")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    p = sub.add_parser("manifest", help="hash the built fonts in the tree and write SHA256SUMS",
                       description="Hash every built font present in the tree and write SHA256SUMS "
                                   "atomically. Refuses an empty tree, symbolic links, names "
                                   "that are not portable, and a tree that lacks fonts the "
                                   "current SHA256SUMS lists (unless --remove-missing).")
    p.add_argument("--remove-missing", action="store_true",
                   help="drop the fonts SHA256SUMS lists that are no longer in the tree "
                        "(after removing or renaming a font on purpose)")
    p.set_defaults(run=cmd_manifest)

    p = sub.add_parser("verify", help="check the tree against SHA256SUMS",
                       description="Check that every SHA256SUMS entry exists and matches, and that "
                                   "every built font in the tree is listed. Exit status 0 or 1.")
    p.add_argument("--allow-missing", action="store_true",
                   help="check only the files present and report how many are missing")
    p.set_defaults(run=cmd_verify)

    p = sub.add_parser("list", help="show the archives with file counts and sizes",
                       description="Show each archive with the number and total size of its files "
                                   "present in the tree, then whether every built font present "
                                   "belongs to exactly one archive (exit status 1 if not, or if "
                                   "the tree has a problem such as a symbolic link).")
    p.set_defaults(run=cmd_list)

    p = sub.add_parser("pack", help="write the release archives and their SHA256SUMS",
                       description="Verify strictly, check that every SHA256SUMS path belongs to "
                                   "exactly one archive, then write deterministic zips and "
                                   "DIR/SHA256SUMS of them. Other files in DIR are left alone.")
    p.add_argument("--out", type=Path, metavar="DIR",
                   help="output directory (default: dist/ under the repository root)")
    p.set_defaults(run=cmd_pack)

    p = sub.add_parser("fetch", help="download the release archives and unpack them safely",
                       description="Download archives from https://github.com/<repository>/releases/"
                                   "download/<tag>/<name> (or from --base-url) and unpack every font "
                                   "whose SHA-256 matches SHA256SUMS. An archive that fails leaves "
                                   "the tree as it was; should even undoing its moves fail, the "
                                   "error names every file left.")
    p.add_argument("--archive", action="extend", nargs="+", metavar="NAME",
                   help="archives to fetch (repeatable; default: all of them)")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--tag", help="release tag to download from (default: the tag in font-archives.json)")
    source.add_argument("--base-url", metavar="URL",
                        help="download <URL>/<name> instead; must be https://, or http:// to a "
                             "loopback IP address")
    p.add_argument("--force", action="store_true",
                   help="replace an existing font whose SHA-256 differs from SHA256SUMS")
    p.set_defaults(run=cmd_fetch)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except (FontArchivesError, OSError) as exc:  # OSError: a file or folder the tool cannot use
        print(f"error: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
