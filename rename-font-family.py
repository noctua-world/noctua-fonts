#!/usr/bin/env python3
"""Rewrite the family name recorded inside font files.

Font lookup by name fails *silently*: ask for a family the system does not have
and you get a fallback face, with no error anywhere. So when the same typeface
carries different family names in different places -- common with fonts patched
by Nerd Fonts, where each person who runs the patcher may rename the output --
text quietly renders in the wrong font. This aligns files onto one chosen name.

    ./rename-font-family.py "<from>" "<to>" FONT.ttf [FONT.ttf ...]
    ./rename-font-family.py "MyFont Mono Nerd Font" "MyFontM Nerd Font" *.ttf

Only the identifier name records are touched (IDs 1/3/4/6/16/18/20/21).
Copyright, trademark and license (IDs 0/7/13/14) are left alone. Both the
spaced form ("My Font") and the compact PostScript form ("MyFont") are
replaced. The file itself is renamed when its name carries the compact form,
and a sibling .woff2 is regenerated if one exists.

Idempotent (running it again does nothing) and reversible (swap <from> and
<to>; the round trip returns a byte-identical file).

Requires: fonttools (plus brotli if .woff2 files are present)
          ->  pip install fonttools brotli
"""

import argparse
import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    sys.exit("error: fonttools not found.  ->  pip install fonttools brotli")

# Name IDs that identify the font. Never 0/7/13/14 -- those are legal text and
# may legitimately contain the old name.
IDENTIFIER_IDS = {1, 3, 4, 6, 16, 18, 20, 21}


def rewrite(font, old, new):
    """Swap the strings in the identifier name records. True if anything changed."""
    old_compact, new_compact = old.replace(" ", ""), new.replace(" ", "")
    changed = False
    for record in font["name"].names:
        if record.nameID not in IDENTIFIER_IDS:
            continue
        value = str(record)
        updated = value.replace(old, new).replace(old_compact, new_compact)
        if updated != value:
            record.string = updated
            changed = True
    return changed


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("old", metavar="FROM", help='current family, e.g. "Foo Mono Nerd Font"')
    p.add_argument("new", metavar="TO", help='desired family, e.g. "FooM Nerd Font"')
    p.add_argument("fonts", nargs="+", type=Path, metavar="FONT", help="font files to fix")
    args = p.parse_args()

    old_compact, new_compact = args.old.replace(" ", ""), args.new.replace(" ", "")

    for path in args.fonts:
        if not path.is_file():
            sys.exit(f"error: no such file: {path}")

        font = TTFont(path)
        if not rewrite(font, args.old, args.new):
            print(f"  {path.name}: already '{args.new}' -- nothing to do")
            continue

        # rename the file too when its name carries the compact form
        target = path
        if old_compact in path.name:
            target = path.with_name(path.name.replace(old_compact, new_compact))

        font.save(target)
        if target != path:
            path.unlink()

        # regenerate the sibling .woff2, if there was one
        old_web = path.with_suffix(".woff2")
        if old_web.exists():
            old_web.unlink()
            try:
                font.flavor = "woff2"
                font.save(target.with_suffix(".woff2"))
            except ImportError:
                sys.exit("\nerror: brotli not found (needed to rebuild the WOFF2).  "
                         "->  pip install brotli")

        print(f"  {path.name:<38} -> {target.name:<36} ({font['name'].getDebugName(1)})")

    print("\nverify:  fc-query --format='%{family}|%{style}\\n' <font>")


if __name__ == "__main__":
    main()
