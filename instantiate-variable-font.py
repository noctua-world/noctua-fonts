#!/usr/bin/env python3
"""Generate static font instances from a variable font.

A variable font stores a design space (weight, width, optical size...) in one
file. Some targets cannot use that design space and need one file per style:
the Nerd Fonts patcher rejects variable fonts outright, Flutter wants a file
per declared weight, and older print/PDF pipelines only read static faces.

With no axis options, this generates every *named instance* the font itself
declares -- the styles the designer intended. Pass axis options to generate a
specific set instead.

    ./instantiate-variable-font.py FONT.ttf --list
    ./instantiate-variable-font.py FONT.ttf                       # all named instances
    ./instantiate-variable-font.py FONT.ttf --weights 400 700 --woff2
    ./instantiate-variable-font.py FONT.ttf --weights 400 --widths 62.5 100
    ./instantiate-variable-font.py FONT.ttf --axis opsz=14 --weights 400

Output goes to ./static/ next to the input; the source is never overwritten.

Requires: fonttools (plus brotli for --woff2)  ->  pip install fonttools brotli
"""

import argparse
import itertools
import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
except ImportError:
    sys.exit("error: fonttools not found.  ->  pip install fonttools brotli")


def axis_table(font):
    """{tag: (min, default, max)} for every variation axis."""
    return {a.axisTag: (a.minValue, a.defaultValue, a.maxValue)
            for a in font["fvar"].axes}


def named_instances(font):
    """[(style name, {tag: value})] as declared by the font itself."""
    names = font["name"]
    out = []
    for inst in font["fvar"].instances:
        label = names.getDebugName(inst.subfamilyNameID) or "?"
        out.append((label, dict(inst.coordinates)))
    return out


def describe(font, path):
    axes = axis_table(font)
    print(f"{path.name}")
    print(f"  family: {font['name'].getDebugName(1)}")
    print("  axes:")
    for tag, (lo, default, hi) in axes.items():
        print(f"    {tag}  {lo} .. {hi}   (default {default})")
    print("  named instances:")
    for label, coords in named_instances(font):
        loc = "  ".join(f"{t}={v:g}" for t, v in coords.items())
        print(f"    {label:<24} {loc}")


def output_stem(font, requested, renamed):
    """Filename stem for an instance.

    When the font was renamed from its STAT table, its own PostScript name is
    the best answer -- that is the font's opinion of what this style is called.
    Otherwise the name table still describes the *default* style, and reusing it
    would silently label (say) a Medium Condensed as "Regular"; spell the
    requested coordinates out instead.
    """
    family = (font["name"].getDebugName(1) or "Font").replace(" ", "")
    if renamed:
        ps = font["name"].getDebugName(6)
        if ps:
            return ps.replace(" ", "")
    coords = "-".join(f"{t}{v:g}" for t, v in sorted(requested.items()))
    return f"{family}-{coords}"


def instantiate(source, location):
    """Pin every axis -> a true static instance (no fvar/STAT left).

    Returns (font, renamed). `renamed` is False when the location has no STAT
    axis values, in which case the name table still describes the default style.
    """
    font = TTFont(source)
    pinned = {tag: default for tag, (_, default, _) in axis_table(font).items()}
    pinned.update(location)
    try:
        instancer.instantiateVariableFont(
            font, pinned, inplace=True, updateFontNames=True)
        return font, True
    except ValueError:
        font = TTFont(source)
        instancer.instantiateVariableFont(font, pinned, inplace=True)
        return font, False


def parse_axis(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"expected TAG=VALUE, got {spec!r}")
    tag, _, value = spec.partition("=")
    try:
        return tag.strip(), float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("font", type=Path, help="variable font to instantiate (.ttf/.otf)")
    p.add_argument("--list", action="store_true",
                   help="show axes and named instances, generate nothing")
    p.add_argument("--weights", nargs="+", type=float, metavar="N",
                   help="wght values to generate (e.g. 400 700)")
    p.add_argument("--widths", nargs="+", type=float, metavar="N",
                   help="wdth values to generate (e.g. 62.5 100)")
    p.add_argument("--axis", action="append", type=parse_axis, default=[],
                   metavar="TAG=VALUE",
                   help="pin any other axis; repeatable (e.g. --axis opsz=14)")
    p.add_argument("--woff2", action="store_true", help="also write .woff2 (web)")
    p.add_argument("--out", type=Path, metavar="DIR",
                   help="output directory (default: ./static/ next to the input)")
    args = p.parse_args()

    if not args.font.is_file():
        sys.exit(f"error: no such file: {args.font}")

    font = TTFont(args.font, lazy=True)
    if "fvar" not in font:
        sys.exit(f"error: '{args.font.name}' is already STATIC (no fvar table) -- "
                 "nothing to instantiate.")

    if args.list:
        describe(font, args.font)
        return

    axes = axis_table(font)
    extra = dict(args.axis)
    requested_tags = set(extra)
    if args.weights:
        requested_tags.add("wght")
    if args.widths:
        requested_tags.add("wdth")
    unknown = sorted(requested_tags - set(axes))
    if unknown:
        sys.exit(f"error: font has no axis {', '.join(unknown)} "
                 f"(it has: {', '.join(axes)})")

    # no axis options -> the instances the font itself declares
    if not (args.weights or args.widths or extra):
        targets = named_instances(font)
    else:
        grid = {}
        if args.weights:
            grid["wght"] = args.weights
        if args.widths:
            grid["wdth"] = args.widths
        tags = list(grid)
        combos = itertools.product(*(grid[t] for t in tags)) if tags else [()]
        targets = [(None, {**extra, **dict(zip(tags, values))}) for values in combos]

    out_dir = args.out or args.font.parent / "static"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"from: {args.font.name}  ->  {out_dir}/")
    unnamed = 0
    for _, location in targets:
        instance, renamed = instantiate(args.font, location)
        if not renamed:
            unnamed += 1
        target = out_dir / (output_stem(instance, location, renamed) + args.font.suffix)

        instance.save(target)
        line = f"  {target.name:<44} {target.stat().st_size // 1024:>6} KB"

        if args.woff2:
            web = target.with_suffix(".woff2")
            try:
                instance.flavor = "woff2"
                instance.save(web)
            except ImportError:
                sys.exit("\nerror: brotli not found (needed for WOFF2).  "
                         "->  pip install brotli")
            line += f"  + {web.stat().st_size // 1024} KB woff2"
        print(line)

    if unnamed:
        print(f"\nnote: {unnamed} instance(s) sit at a location with no STAT entry, so "
              "the\n      font could not be renamed. Their filenames spell out the "
              "coordinates,\n      but the style name inside the file still reads as the "
              "default.")


if __name__ == "__main__":
    main()
