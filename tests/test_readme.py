"""Tests for the repository's README, the page GitHub opens on: a short introduction to Noctua
Iosevka that sends the reader to the specimen site.

What they guard:

  * It stays that: every link goes to the site or to Iosevka, and nothing points into docs/,
    where the documents live on their own.
  * Every image it shows exists, in a light and a dark version, as a well-formed SVG with a
    title; it says it is a personal project before anything else.
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
