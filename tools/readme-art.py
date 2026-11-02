#!/usr/bin/env python3
"""Draw the art of the repository's README: the animated title and the button to the site.

    python3 tools/readme-art.py            write .github/readme/*.svg
    python3 tools/readme-art.py --check    exit 1 if a file there differs from what it draws

GitHub shows a README's images but runs none of its styles or scripts, and an SVG shown as an
image loads no font. So every letter here is the font's own outline, read from the built TTFs
under noctua-iosevka/, and the motion is CSS inside each SVG, which an image does run:

  hero-light.svg, hero-dark.svg      "Noctua Iosevka" in ExtraBold, a ripple of weight sweeping
                                     across it through all nine weights, Heavy to Thin, every
                                     glyph a real face; behind each line a misregistered plate
                                     of the third ink; a tape of symbols and Nerd Fonts icons
  button-light.svg, button-dark.svg  the button that links to the specimen site

The light pair is the site's paper and riso inks, multiplied; the dark pair its phosphor inks,
added as light. The README picks one per colour scheme with <picture>. Motion stops under
prefers-reduced-motion, on the resting ExtraBold.

Needs fontTools and the built fonts (./tools/font-archives.py fetch restores them): the nine
Normal Upright faces of noctua-iosevka/TTF/ and NoctuaIosevkaNerdFontMono-Regular.ttf. The
output is deterministic: the same fonts always give the same bytes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / ".github" / "readme"
TTF = REPO / "noctua-iosevka" / "TTF"
NERD = REPO / "noctua-iosevka" / "TTF-nerdfonts" / "NoctuaIosevkaNerdFontMono-Regular.ttf"

WEIGHTS = ("Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Heavy")
REST = 7  # ExtraBold, the weight the site's hero sets its title in
UPM = 1000
ADVANCE = 600  # every glyph of the Normal width, in font units

# The site's colours (site/static/css/site.css), per scheme.
THEMES = {
    "light": {
        "bg": "#f3eee3", "fg": "#17151c", "fg2": "#48434f", "line1": "#e3176c", "line2": "#2a50ff",
        "plate": "#ffcc00", "dot_a": "#ff3d8f", "dot_b": "#2a50ff", "blend": "multiply", "shadow": "#ff3d8f",
    },
    "dark": {
        "bg": "#0b0a10", "fg": "#f1ede4", "fg2": "#b4aebd", "line1": "#ff4fa0", "line2": "#3fc8ff",
        "plate": "#d6ff3a", "dot_a": "#ff4fa0", "dot_b": "#3fc8ff", "blend": "screen", "shadow": "#d6ff3a",
    },
}

# The hero: 1200 x 600 units.
W, H = 1200, 600
MARGIN = 56
EM = 200  # the title's size
LINE1, LINE2 = "Noctua", "Iosevka"
BASE1, BASE2 = 302, 462  # baselines: the site's line height of 0.8 em
META = ("A CUSTOM BUILD OF IOSEVKA", "135 FACES", "SIL OFL 1.1")
META_SIZE, META_TRACK = 15, 0.14  # px, em: the site's meta pills
TAPE_SIZE = 28
TAPE = (
    "135 faces ◆ 9 weights ◆ 5 widths ◆ 3 slopes ◆ "
    "\uf313 \uf17c \uf179 \uf17a \ue725 \uf09b \ue7a8 \ue606 \ue626 \ue777 \ue628 \uf48a \uf4bc \uf0e7 \U000f03d2 ◆ "
    "-> => != <= >= :: ◆ ≠ ≤ ≥ → ⇒ ⇔ ◆ λ ∀ ∃ ∑ ∫ √ ∞ ◆ "
    "░▒▓█ ⣿⡇⢸⠿ ╭─╮ ◆ 0O il1I rn m ◆ "
)

# The ripple, in steps of STEP seconds: from the resting ExtraBold it swells to Heavy, thins to
# Thin and comes back, so each of the nine faces shows in turn.
STEP = 0.15
RIPPLE = (8, 8, 6, 5, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 5, 6)
LEAD = 1.0  # seconds of rest before the ripple starts
PERIOD = 6.6  # seconds, ripple and rest
SPREAD = 0.075  # seconds between one letter and the next


def fmt(x: float, places: int = 2) -> str:
    s = f"{x:.{places}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def scale(s: float) -> str:
    """A glyph's scale from font units to px, exact: a size of 15 px is 0.015, not 0.02."""
    return f"scale({fmt(s, 6)} {fmt(-s, 6)})"


def load_fonts():
    try:
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.ttLib import TTFont
    except ImportError:
        sys.exit("error: needs fontTools (see docs/README.md, Tools)")
    missing = [p for p in [*(TTF / f"NoctuaIosevka-{w}.ttf" for w in WEIGHTS), NERD] if not p.is_file()]
    if missing:
        sys.exit(f"error: {len(missing)} font(s) missing, {missing[0]} first: run ./tools/font-archives.py fetch")

    def outlines(path: Path, chars: str) -> dict[str, str]:
        with TTFont(path, lazy=True) as font:
            cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
            out = {}
            for ch in sorted(set(chars) - {" "}):
                if ord(ch) not in cmap:
                    raise SystemExit(f"error: {path.name} has no glyph for U+{ord(ch):04X}")
                name = cmap[ord(ch)]
                if glyphs[name].width != ADVANCE:
                    raise SystemExit(f"error: {path.name}: {name} is not {ADVANCE} units wide")
                pen = SVGPathPen(glyphs, ntos=lambda v: fmt(v))
                glyphs[name].draw(pen)
                out[ch] = pen.getCommands()
            return out

    title = {w: outlines(TTF / f"NoctuaIosevka-{name}.ttf", LINE1 + LINE2) for w, name in enumerate(WEIGHTS)}
    meta = outlines(TTF / "NoctuaIosevka-Regular.ttf", "".join(META))
    bold = outlines(TTF / "NoctuaIosevka-ExtraBold.ttf", BUTTON_TEXT)
    tape = outlines(NERD, TAPE)
    return title, meta, bold, tape


def glyph_id(prefix: str, ch: str) -> str:
    return f"{prefix}{ord(ch):x}"


def defs(prefix: str, outlines: dict[str, str]) -> list[str]:
    return [f'<path id="{glyph_id(prefix, ch)}" d="{d}"/>' for ch, d in sorted(outlines.items()) if d]


def run(prefix: str, text: str, x: float, baseline: float, size: float, track: float = 0.0,
        attrs: str = "") -> str:
    """A line of text as <use> elements, each glyph scaled from font units to `size` px."""
    s = size / UPM
    step = (ADVANCE / UPM + track) * size
    uses = []
    for i, ch in enumerate(text):
        if ch != " ":
            uses.append(f'<use href="#{glyph_id(prefix, ch)}" x="{fmt(i * step / s)}"/>')
    return (f'<g{attrs} transform="translate({fmt(x)} {fmt(baseline)}) {scale(s)}">'
            + "".join(uses) + "</g>")


def width(text: str, size: float, track: float = 0.0) -> float:
    return len(text) * (ADVANCE / UPM + track) * size - track * size


def ripple_keyframes() -> str:
    """One set of keyframes per weight: shown while the ripple is at that weight, and the
    resting weight between ripples. step-end holds each value until the next keyframe."""
    times = [0.0, LEAD] + [LEAD + (i + 1) * STEP for i in range(len(RIPPLE))] + [PERIOD]
    weights = [REST] + list(RIPPLE) + [REST]  # the weight from each time to the next
    css = []
    for w in range(len(WEIGHTS)):
        frames = []
        for t, shown in zip(times, weights):
            frames.append(f"{fmt(100 * t / PERIOD)}%{{opacity:{1 if shown == w else 0}}}")
        frames.append(f"100%{{opacity:{1 if REST == w else 0}}}")
        css.append(f"@keyframes w{w}{{{''.join(frames)}}}")
    return "".join(css)


def hero(theme: str, title, meta, tape) -> str:
    c = THEMES[theme]
    copy = width(TAPE, TAPE_SIZE)  # one turn of the tape: TAPE ends in its own separator
    css = [
        ".r use{opacity:0;animation:" f"{fmt(PERIOD)}s step-end infinite}}",
        f".r use.w{REST}{{opacity:1}}",
        *(f".r .w{w}{{animation-name:w{w}}}" for w in range(len(WEIGHTS))),
        *(f".p{p} use{{animation-delay:{fmt(p * SPREAD)}s}}" for p in range(len(LINE1 + LINE2))),
        ripple_keyframes(),
        ".plate{transform:translate(7px,5px);animation:drift 9s ease-in-out infinite}",
        "@keyframes drift{0%,100%{transform:translate(7px,5px)}50%{transform:translate(2px,9px)}}",
        f".ink{{mix-blend-mode:{c['blend']}}}",
        ".tape{animation:tape 40s linear infinite}",
        f"@keyframes tape{{to{{transform:translateX(-{fmt(copy)}px)}}}}",
        "@media (prefers-reduced-motion:reduce){.r use,.plate,.tape{animation:none}}",
    ]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">',
        "<title id=\"t\">Noctua Iosevka: its name set in its own faces, a ripple of weight sweeping "
        "across it through all nine of its weights</title>",
        f"<style>{''.join(css)}</style>",
        "<defs>",
        *defs("m", meta),
        *defs("k", tape),
        *(p for w in range(len(WEIGHTS)) for p in defs(f"w{w}-", title[w])),
    ]
    # The ground: the site's paper with two halftone screens, or its screen with scanlines.
    if theme == "light":
        out += [
            '<pattern id="sa" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(15)">'
            f'<circle cx="5" cy="5" r="1.7" fill="{c["dot_a"]}"/></pattern>',
            '<pattern id="sb" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(75)">'
            f'<circle cx="5" cy="5" r="1.5" fill="{c["dot_b"]}"/></pattern>',
            '<radialGradient id="fa" cx="0.92" cy="0.12" r="0.75"><stop offset="0" stop-color="#fff"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>',
            '<radialGradient id="fb" cx="0.06" cy="0.95" r="0.7"><stop offset="0" stop-color="#fff"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>',
            f'<mask id="ma"><rect width="{W}" height="{H}" fill="url(#fa)"/></mask>',
            f'<mask id="mb"><rect width="{W}" height="{H}" fill="url(#fb)"/></mask>',
        ]
    else:
        out += [
            '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
            '<rect width="4" height="1" fill="#fff" fill-opacity="0.035"/></pattern>',
            f'<radialGradient id="ga" cx="0.18" cy="0.42" r="0.55"><stop offset="0" stop-color="{c["dot_a"]}" '
            'stop-opacity="0.16"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>',
            f'<radialGradient id="gb" cx="0.82" cy="0.72" r="0.5"><stop offset="0" stop-color="{c["dot_b"]}" '
            'stop-opacity="0.14"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>',
            '<filter id="glow" x="-10%" y="-20%" width="120%" height="140%"><feGaussianBlur stdDeviation="5" '
            'result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        ]
    out += [f'<clipPath id="tc"><rect y="508" width="{W}" height="{H - 508}"/></clipPath>', "</defs>",
            f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>']
    if theme == "light":
        out += [f'<rect class="ink" width="{W}" height="{H}" fill="url(#sa)" opacity="0.32" mask="url(#ma)"/>',
                f'<rect class="ink" width="{W}" height="{H}" fill="url(#sb)" opacity="0.22" mask="url(#mb)"/>']
    else:
        out += [f'<rect width="{W}" height="{H}" fill="url(#ga)"/>', f'<rect width="{W}" height="{H}" fill="url(#gb)"/>']

    # The meta pills, as the site's hero opens: the first one inverted.
    x, top, h = MARGIN, 34, 32
    for i, text in enumerate(META):
        w_ = width(text, META_SIZE, META_TRACK) + 26
        fill, ink = (c["fg"], c["bg"]) if i == 0 else (c["bg"], c["fg"])
        out.append(f'<rect x="{fmt(x)}" y="{top}" width="{fmt(w_)}" height="{h}" fill="{fill}" stroke="{c["fg"]}"/>')
        out.append(run("m", text, x + 13, top + 21, META_SIZE, META_TRACK, f' fill="{ink}"'))
        x += w_ - 1

    # The title: a misregistered plate of the third ink behind each line, at the resting
    # weight, printed onto the ground; then the line itself over it, in its own ink, its
    # letters rippling through the nine weights. As a letter thins, the plate shows round it.
    x1 = MARGIN
    x2 = W - MARGIN - width(LINE2, EM)
    glow = ' filter="url(#glow)"' if theme == "dark" else ""
    for text, x0, base in ((LINE1, x1, BASE1), (LINE2, x2, BASE2)):
        out.append(f'<g class="ink"><g class="plate" fill="{c["plate"]}" opacity="0.9">'
                   + run(f"w{REST}-", text, x0, base, EM) + "</g></g>")
    for line, (text, x0, base, colour) in enumerate(((LINE1, x1, BASE1, c["line1"]), (LINE2, x2, BASE2, c["line2"]))):
        s = EM / UPM
        letters = []
        for i, ch in enumerate(text):
            p = i + (len(LINE1) if line else 0)
            uses = "".join(f'<use class="w{w}" href="#{glyph_id(f"w{w}-", ch)}"/>' for w in range(len(WEIGHTS)))
            letters.append(f'<g class="p{p}" transform="translate({fmt(i * ADVANCE)} 0)">{uses}</g>')
        out.append(f'<g{glow}><g class="r" fill="{colour}" transform="translate({fmt(x0)} {base}) '
                   f'{scale(s)}">' + "".join(letters) + "</g></g>")

    # The tape: symbols and icons, every one a single cell, running left for ever. Two turns,
    # from the left edge, cover the frame at every moment, and the second takes the first's
    # place when the loop restarts.
    out += [f'<path d="M0 508.5H{W}" stroke="{c["fg"]}" stroke-opacity="0.18"/>',
            f'<g clip-path="url(#tc)"><g class="tape" fill="{c["fg2"]}">',
            run("k", TAPE, 0, 565, TAPE_SIZE), run("k", TAPE, copy, 565, TAPE_SIZE),
            "</g></g>"]
    out.append("</svg>")
    return "\n".join(out) + "\n"


BUTTON_TEXT = "Explore the specimen \u2192"
BH = 105  # the pill, its offset shadow and a margin


def button(theme: str, bold) -> str:
    c = THEMES[theme]
    size = 30
    text_w = width(BUTTON_TEXT, size)
    pill_w, pill_h, x0, y0 = text_w + 88, 72, 12, 12
    arrow_x = x0 + 44 + (len(BUTTON_TEXT) - 1) * (ADVANCE / UPM) * size
    css = (
        ".arrow{animation:nudge 2.4s ease-in-out infinite}"
        "@keyframes nudge{0%,55%,100%{transform:translateX(0)}70%{transform:translateX(7px)}}"
        ".sheen{animation:sheen 4.8s ease-in-out infinite}"
        f"@keyframes sheen{{0%,40%{{transform:translateX(-{fmt(pill_w)}px)}}75%,100%{{transform:translateX({fmt(pill_w)}px)}}}}"
        "@media (prefers-reduced-motion:reduce){.arrow,.sheen{animation:none}.sheen{display:none}}"
    )
    label = BUTTON_TEXT[:-1].rstrip()
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(pill_w + 36)} {BH}" role="img" aria-labelledby="t">',
        "<title id=\"t\">Explore the specimen site of Noctua Iosevka</title>",
        f"<style>{css}</style>",
        "<defs>", *defs("b", bold),
        f'<clipPath id="pc"><rect x="{x0}" y="{y0}" width="{fmt(pill_w)}" height="{pill_h}" rx="{pill_h // 2}"/></clipPath>',
        '<linearGradient id="sg" x1="0" x2="1"><stop offset="0.35" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="0.5" stop-color="#fff" stop-opacity="0.28"/><stop offset="0.65" stop-color="#fff" '
        'stop-opacity="0"/></linearGradient>',
        "</defs>",
        f'<rect x="{x0 + 9}" y="{y0 + 9}" width="{fmt(pill_w)}" height="{pill_h}" rx="{pill_h // 2}" fill="{c["shadow"]}"/>',
        f'<rect x="{x0}" y="{y0}" width="{fmt(pill_w)}" height="{pill_h}" rx="{pill_h // 2}" fill="{c["fg"]}"/>',
        f'<g clip-path="url(#pc)"><rect class="sheen" x="{x0}" y="{y0}" width="{fmt(pill_w)}" height="{pill_h}" fill="url(#sg)"/></g>',
        run("b", label, x0 + 44, y0 + 47, size, attrs=f' fill="{c["bg"]}"'),
        '<g class="arrow">' + run("b", BUTTON_TEXT[-1], arrow_x, y0 + 47, size, attrs=f' fill="{c["bg"]}"') + "</g>",
        "</svg>",
    ]
    return "\n".join(out) + "\n"


def draw() -> dict[str, bytes]:
    title, meta, bold, tape = load_fonts()
    files = {}
    for theme in THEMES:
        files[f"hero-{theme}.svg"] = hero(theme, title, meta, tape).encode("utf-8")
        files[f"button-{theme}.svg"] = button(theme, bold).encode("utf-8")
    return files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if .github/readme/ differs from what this draws")
    args = parser.parse_args(argv)
    files = draw()
    if args.check:
        stale = [name for name, data in files.items() if not (OUT / name).is_file() or (OUT / name).read_bytes() != data]
        for name in stale:
            print(f"differs: .github/readme/{name}", file=sys.stderr)
        if stale:
            print("run: python3 tools/readme-art.py", file=sys.stderr)
            return 1
        print(".github/readme/ matches what tools/readme-art.py draws.")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (OUT / name).write_bytes(data)
        print(f"wrote .github/readme/{name} ({len(data):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
