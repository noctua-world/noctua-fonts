"""Tests for the repository's README, the page GitHub opens on: a short introduction to Noctua
Iosevka that sends the reader to the specimen site.

What they guard:

  * It stays that: every link goes to the site or to Iosevka, and nothing points into docs/,
    where the documents live on their own.
  * Every image it shows exists, in a light and a dark version, as a well-formed SVG with a
    title; it says it is a personal project before anything else; its introduction is
    justified.
  * The art has no ground of its own: it lies on GitHub's page, white or dark, so nothing in
    it may reach the frame's edge unless a soft cloud or fade, ending inside the frame, clears
    it first; else the frame would show as a box. Held still, the tape's first words read whole.
  * The SVGs are what tools/readme-art.py draws from the fonts (only where fontTools and the
    built fonts are present, as for the other tests that read the fonts).

Standard library only, apart from that last class; they read files and write nothing.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
ART = REPO / ".github" / "readme"
SITE_URL = "https://noctua-world.github.io/noctua-fonts/"
SVG = "{http://www.w3.org/2000/svg}"


class TestReadme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = README.read_text(encoding="utf-8")

    def test_it_opens_on_a_personal_project(self):
        first = self.text.strip().splitlines()[0]
        self.assertIn("A personal project", first)

    def test_links_go_to_the_site_or_to_iosevka(self):
        links = re.findall(r'href="([^"]+)"|\]\(([^)]+)\)', self.text)
        targets = [a or b for a, b in links]
        self.assertIn(SITE_URL, targets)
        for target in targets:
            self.assertIn(target, (SITE_URL, "https://github.com/be5invis/Iosevka"), target)

    def test_the_introduction_is_justified(self):
        self.assertRegex(self.text, r'<p align="justify">\s*Noctua Iosevka is ')

    def test_nothing_points_into_the_documents(self):
        self.assertNotRegex(self.text, r"docs/|\.md\b")

    def test_every_image_exists_in_both_schemes(self):
        sources = re.findall(r'(?:src|srcset)="([^"]+)"', self.text)
        self.assertTrue(sources)
        for source in sources:
            self.assertTrue((REPO / source).is_file(), source)
        for name in {Path(s).name for s in sources}:
            self.assertRegex(name, r"-(light|dark)\.svg$")
            other = name.replace("-light", "-dark") if "-light" in name else name.replace("-dark", "-light")
            self.assertIn(other, {Path(s).name for s in sources}, f"{name} has no other scheme")
        for picture in re.findall(r"<picture>(.*?)</picture>", self.text, re.S):
            self.assertIn('media="(prefers-color-scheme: dark)"', picture)
            self.assertRegex(picture, r'<img [^>]*alt="[^"]{10,}"')

    def test_the_images_are_svg_with_a_title(self):
        files = sorted(ART.glob("*.svg"))
        self.assertEqual(len(files), 4)
        for path in files:
            root = ET.parse(path).getroot()
            self.assertEqual(root.tag, f"{SVG}svg", path.name)
            title = root.find(f"{SVG}title")
            self.assertIsNotNone(title, path.name)
            self.assertTrue(title.text and title.text.strip(), path.name)
            # An SVG shown as an image loads nothing: no fonts, no other files.
            data = path.read_text(encoding="utf-8")
            self.assertNotRegex(data, r"@font-face|@import|url\((?!#)|href=\"(?!#)", path.name)
            # Motion stops for a reader who asks for less.
            self.assertIn("prefers-reduced-motion:reduce", data, path.name)

    def test_the_art_has_no_ground(self):
        # Whatever could reach the frame's edge must fade out before it: a rect as large as the
        # frame is filled with a cloud or lies under a fading mask, and so does every shape
        # drawn outside <defs> other than a rect (the tape's rule), and the tape itself.
        for path in sorted(ART.glob("*.svg")):
            art = _Art(path)
            for e in art.drawn():
                name = f"{path.name}: <{e.tag[len(SVG):]}> {e.get('class') or e.get('d') or ''}"
                if e.tag == f"{SVG}rect":
                    if art.whole(e) and not art.cloud(art.ref(e.get("fill"))):
                        self.assertIsNotNone(art.fading_mask(e), f"{name} paints the whole frame")
                elif e.tag in {f"{SVG}{t}" for t in ("path", "circle", "ellipse", "line", "polyline", "polygon",
                                                      "image", "text")}:
                    self.assertIsNotNone(art.fading_mask(e), f"{name} may reach the edge")
            if path.name.startswith("hero-"):
                tape = art.tape()
                self.assertIsNotNone(tape, f"{path.name}: no tape")
                self.assertIsNotNone(art.fading_mask(tape), f"{path.name}: the tape is cut at the edge")

    def test_the_still_tape_reads_whole(self):
        # Under reduced motion the tape holds still, and must start where its fade is over, or
        # its first words ("135 faces") lie faded at the edge.
        for path in sorted(ART.glob("hero-*.svg")):
            art = _Art(path)
            data = path.read_text(encoding="utf-8")
            still = re.search(r"@media \(prefers-reduced-motion:reduce\)\{[^@]*?\.tape\{transform:"
                              r"translateX\(([\d.]+)px\)\}", data)
            self.assertIsNotNone(still, f"{path.name}: the still tape has no resting place")
            first = re.match(r"translate\(([\d.]+) ", art.tape()[0].get("transform"))
            start = float(first.group(1)) + float(still.group(1))
            self.assertGreaterEqual(start, art.fade_full(art.fading_mask(art.tape())), path.name)


class _Art:
    """One SVG of the README art, read for what reaches the edge of its frame."""

    def __init__(self, path: Path):
        self.root = ET.parse(path).getroot()
        _, _, self.w, self.h = (float(v) for v in self.root.get("viewBox").split())
        self.ids = {e.get("id"): e for e in self.root.iter() if e.get("id")}
        self.parent = {child: e for e in self.root.iter() for child in e}

    def lineage(self, e):
        while e is not None:
            yield e
            e = self.parent.get(e)

    def drawn(self):
        """Every element that paints: not in <defs>, <title> or <style>."""
        hidden = {f"{SVG}{t}" for t in ("defs", "title", "style")}
        return [e for e in self.root.iter() if not any(a.tag in hidden for a in self.lineage(e))]

    def ref(self, value):
        m = re.fullmatch(r"url\(#([\w-]+)\)", value or "")
        return self.ids.get(m.group(1)) if m else None

    def whole(self, rect) -> bool:
        return (float(rect.get("x", 0)) <= 0 and float(rect.get("y", 0)) <= 0
                and float(rect.get("width", 0)) >= self.w and float(rect.get("height", 0)) >= self.h)

    def cloud(self, grad) -> bool:
        """A radial gradient clear at its rim and beyond, the rim inside the frame."""
        if grad is None or grad.tag != f"{SVG}radialGradient":
            return False
        if set(grad.attrib) != {"id", "gradientUnits", "cx", "cy", "r", "gradientTransform"} or (
                grad.get("gradientUnits"), grad.get("cx"), grad.get("cy"), grad.get("r")) != (
                "userSpaceOnUse", "0", "0", "1"):
            return False
        m = re.fullmatch(r"translate\(([\d.]+) ([\d.]+)\) scale\(([\d.]+) ([\d.]+)\)",
                         grad.get("gradientTransform"))
        if not m:
            return False
        cx, cy, rx, ry = map(float, m.groups())
        return (grad.findall(f"{SVG}stop")[-1].get("stop-opacity") == "0"
                and 0 < cx - rx and cx + rx < self.w and 0 < cy - ry and cy + ry < self.h)

    def fade(self, grad) -> bool:
        """A horizontal linear gradient clear at both ends, both ends inside the frame."""
        if grad is None or grad.tag != f"{SVG}linearGradient":
            return False
        if set(grad.attrib) != {"id", "gradientUnits", "x1", "x2"} or grad.get("gradientUnits") != "userSpaceOnUse":
            return False
        stops = grad.findall(f"{SVG}stop")
        return (stops[0].get("stop-opacity") == "0" == stops[-1].get("stop-opacity")
                and 0 <= float(grad.get("x1")) and float(grad.get("x2")) <= self.w)

    def fading_mask(self, e):
        """The mask on `e` or on what holds it, if that mask is nothing but clouds and fades."""
        for a in self.lineage(e):
            mask = self.ref(a.get("mask"))
            if mask is not None and mask.tag == f"{SVG}mask" and len(mask) and all(
                    r.tag == f"{SVG}rect" and (self.cloud(self.ref(r.get("fill"))) or self.fade(self.ref(r.get("fill"))))
                    for r in mask):
                return mask
        return None

    def tape(self):
        return next((e for e in self.root.iter(f"{SVG}g") if e.get("class") == "tape"), None)

    def fade_full(self, mask) -> float:
        """Where a fading mask's horizontal fade first reaches full strength."""
        grad = self.ref(mask[0].get("fill"))
        x1, x2 = float(grad.get("x1")), float(grad.get("x2"))
        full = next(s for s in grad.findall(f"{SVG}stop") if s.get("stop-opacity", "1") == "1")
        return x1 + float(full.get("offset")) * (x2 - x1)


def _fonts():
    try:
        import fontTools.ttLib  # noqa: F401
    except ImportError:
        return False
    return (REPO / "noctua-iosevka" / "TTF" / "NoctuaIosevka-Thin.ttf").is_file() and (
        REPO / "noctua-iosevka" / "TTF-nerdfonts" / "NoctuaIosevkaNerdFontMono-Regular.ttf").is_file()


@unittest.skipUnless(_fonts(), "needs fontTools and the built fonts under noctua-iosevka/")
class TestReadmeArt(unittest.TestCase):
    def test_the_art_is_what_the_script_draws(self):
        sys.dont_write_bytecode = True  # no __pycache__ left in tools/
        spec = importlib.util.spec_from_file_location("readme_art", REPO / "tools" / "readme-art.py")
        art = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(art)
        for name, data in art.draw().items():
            with self.subTest(file=name):
                self.assertEqual((ART / name).read_bytes(), data, "run: python3 tools/readme-art.py")


if __name__ == "__main__":
    unittest.main()
