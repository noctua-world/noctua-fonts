"""Tests for the GitHub Pages site: site/ (the sources) and docs/ (the generated output).

What they guard:

  * docs/ is exactly what site/build.py produces (`build.py --check` passes).
  * Both locales carry the same keys, and every key is used by the template, a generated
    fragment or a script.
  * Every relative href, src and url() in docs/ resolves to a file, and every JavaScript
    module import resolves too.
  * Nothing is fetched from another origin: no absolute http(s) URL in any src, srcset,
    url(), @import, import statement or <link rel=stylesheet|preload|icon|modulepreload>.
    Only <a href> and the canonical, hreflang and Open Graph metadata may point elsewhere.
  * The Content-Security-Policy meta is present, identical on both pages, and the policy the
    site is designed for; the HTML has no inline script bodies, no <style> elements, no
    style= and no on*= attributes, and the scripts call neither eval nor Function (with or
    without new).
  * <html lang>, the hreflang alternates, the canonical URLs and the language switch agree.
  * Every @font-face src exists; the licence of every font family shipped sits in
    docs/assets/fonts/licenses/, byte for byte the repository's copy; the site fonts stay
    within their 15 MB budget.
  * Every subset covers every character the two pages set with it: the text faces everything
    outside the terminal and the lab face, the terminal face what the terminal prints (the
    icons included, whether written as escapes or as literal characters), the lab face the
    character-variant machine and the coverage strips, the display faces the headings and the
    blocks set in them. The faces a block loads lazily are only used inside such a block.
  * The build fails on a key one locale lacks, on a key nothing uses, on a placeholder the
    template cannot fill, and on a terminal string longer than the terminal's grid allows.
  * The release the pages name and link to is font-archives.json's tag, and the repository
    they link to and live under is its repository: every release and repository link starts
    with https://github.com/<repository>/. No source of the site types a tag, a version, a
    release URL or the repository of its own.
  * A number the prose takes from the font or the build's tables (the code points, the sets,
    the character variants, the italic's redrawn code points ...) is typed in build.py only.
  * Every input, select and textarea has an accessible name.
  * Without scripts the page is a static specimen: every control a script drives is marked
    .js-only (hidden on a page without scripts), the lazily loaded faces apply at once, the
    sections are laid out whole (content-visibility only with scripts), and the terminal holds
    its still frame, 24 rows in each width of the session.
  * Every in-page reference resolves: href="#id", aria-controls, aria-labelledby,
    aria-describedby, for= and data-copy= all name an id the page has, and ids are unique.
  * Every sample character of the Unicode block table lies inside its block, the block totals
    are what Unicode assigns, and the generated HTML is in Unicode normal form C (a character
    that normalisation would fold is written as a character reference).
  * The scripts cap canvases at a device pixel ratio of 2 through motion.js's dpr(), and only
    the editor's minimap (a copy of the page's own markup) writes HTML from a string.
  * With fontTools installed and the built fonts present (optional, skipped otherwise): the
    code-point count, the stylistic-set names, the character-variant features, the code points
    the italic redraws and the block counts are re-measured from the TTFs.

The tests read files only. They need nothing beyond the standard library: subset-fonts.py
is loaded for its repertoire tables, which do not import fontTools.

Run from the repository root:

    python3 -m unittest discover -s tests -t . -p 'test_site.py' -v
"""

import importlib.util
import json
import re
import sys
import tempfile
import unicodedata
import unittest
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock
from urllib.parse import urlsplit

# Loading site/build.py and site/subset-fonts.py must not leave a __pycache__ in site/.
sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "site"
DOCS = REPO / "docs"
PAGES = {"en": DOCS / "index.html", "pt-BR": DOCS / "pt-BR" / "index.html"}
ARCHIVES = json.loads((REPO / "font-archives.json").read_text(encoding="utf-8"))
REPOSITORY = ARCHIVES["repository"]
SITE_URL = "https://{}.github.io/{}/".format(REPOSITORY.split("/")[0].lower(), REPOSITORY.split("/")[1])
CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'"
)
FONT_BUDGET = 15_000_000
LAZY_CLASSES = re.compile(r"^(lf[dtslm]|lw[1-9]|lx[1-5]|ls[uio])$")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


build = load("site_build", SITE / "build.py")
subset = load("site_subset_fonts", SITE / "subset-fonts.py")


# Which subset family an element sets its text in, from the classes that choose one. Display
# type is also chosen by a few component classes; everything else is the text family.
FAMILY_CLASSES = (
    ({"lfm", "term", "fs-icons"}, "term"),
    ({"lfl"}, "lab"),
    ({"lfs"}, "swatch"),
    ({"lft"}, "text"),
    ({"lfd", "sec-title", "hero-title", "footer-mark"}, "display"),
)


class Page(HTMLParser):
    """Collects what the tests need from one generated page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []          # (tag, attrs dict)
        self.scripts = []       # (attrs, body)
        self.styles = 0
        self.text = []          # visible text, outside script and style
        self.by_family = {}     # family -> text set in it
        self.lazy_outside = []  # lazily loaded face classes used outside a data-arm block
        self._stack = []        # (tag, armed, family) for open elements
        self._in_script = None
        self._skip = 0

    VOID = {"meta", "link", "br", "img", "input", "hr", "source", "area", "base", "col", "embed", "param", "track", "wbr"}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "style":
            self.styles += 1
        if tag == "script":
            self._in_script = (a, [])
        if tag in ("script", "style", "template"):
            self._skip += 1
        armed = ("data-arm" in a) or any(armed for _, armed, _ in self._stack)
        classes = (a.get("class") or "").split()
        lazy = [c for c in classes if LAZY_CLASSES.match(c)]
        if lazy and not armed:
            self.lazy_outside.append((tag, a.get("class")))
        family = self._stack[-1][2] if self._stack else "text"
        for names, fam in FAMILY_CLASSES:
            if names & set(classes):
                family = fam
                break
        if tag not in self.VOID:
            self._stack.append((tag, armed, family))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID and self._stack and self._stack[-1][0] == tag:
            self._stack.pop()

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script is not None:
            self.scripts.append((self._in_script[0], "".join(self._in_script[1])))
            self._in_script = None
        if tag in ("script", "style", "template"):
            self._skip = max(0, self._skip - 1)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        if self._in_script is not None:
            self._in_script[1].append(data)
        elif not self._skip:
            self.text.append(data)
            family = self._stack[-1][2] if self._stack else "text"
            self.by_family.setdefault(family, []).append(data)


def parse(path: Path) -> Page:
    p = Page()
    p.feed(path.read_text(encoding="utf-8"))
    p.close()
    return p


def is_external(url: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I)) or url.startswith("//")


def resolve(base: Path, url: str):
    """The file a relative URL names, or None for external, data and fragment-only URLs."""
    url = url.strip()
    if not url or url.startswith("#") or url.startswith("data:") or is_external(url):
        return None
    path = urlsplit(url).path
    target = (base.parent / path).resolve() if not path.startswith("/") else (DOCS / path.lstrip("/")).resolve()
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")
DATA_URI = re.compile(r"""url\(\s*(["'])data:.*?\1\s*\)""", re.S)


def css_text(path: Path) -> str:
    """A stylesheet without its data: URIs (an inline SVG may hold url(#id) references)."""
    return DATA_URI.sub("url(data:)", path.read_text(encoding="utf-8"))
CSS_IMPORT = re.compile(r"""@import\s+(?:url\()?\s*['"]?([^'")\s;]+)""")
JS_IMPORT = re.compile(r"""(?:\bimport\s*(?:[\w*{}\s,]+\s*from\s*)?|\bimport\s*\(\s*|\bexport\s+[\w*{}\s,]+\s+from\s*)["']([^"']+)["']""")


def docs_files(suffix: str):
    return sorted(p for p in DOCS.rglob(f"*{suffix}") if p.is_file())


class TestBuild(unittest.TestCase):
    def test_docs_match_the_sources(self):
        problems = build.check()
        self.assertEqual(problems, [], "run: python3 site/build.py\n" + "\n".join(problems))

    def test_check_flag_exits_zero(self):
        self.assertEqual(build.main(["--check"]), 0)

    def test_nojekyll(self):
        self.assertTrue((DOCS / ".nojekyll").is_file())

    def test_build_is_deterministic(self):
        self.assertEqual(build.build(), build.build())


class TestLocales(unittest.TestCase):
    def test_same_keys_both_ways(self):
        locales = build.load_locales()
        keys = {code: set(loc.strings) for code, loc in locales.items()}
        self.assertEqual(sorted(keys["en"] - keys["pt-BR"]), [], "keys missing in pt-BR")
        self.assertEqual(sorted(keys["pt-BR"] - keys["en"]), [], "keys missing in en")

    def test_every_key_is_used(self):
        locales = build.load_locales()
        template = build.TEMPLATE.read_text(encoding="utf-8")
        for loc in locales.values():
            build.render(template, loc)
        js_used = build.script_keys(build.static_files())
        for code, loc in locales.items():
            unused = sorted(k for k in loc.strings if not k.startswith("js.") and k not in loc.used)
            unused += sorted(k for k in loc.strings if k.startswith("js.") and k[3:] not in js_used)
            self.assertEqual(unused, [], f"{code}: unused keys")

    def test_missing_key_fails_the_build(self):
        loc = build.Locale("en", {})
        with self.assertRaises(build.BuildError):
            build.render("{{nope}}", loc)

    def test_a_key_one_locale_lacks_fails_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            for code in build.LOCALES:
                data = json.loads((build.I18N / f"{code}.json").read_text(encoding="utf-8"))
                if code == "pt-BR":
                    del data["skip"]
                (Path(tmp) / f"{code}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(build, "I18N", Path(tmp)), self.assertRaises(build.BuildError):
                build.load_locales()

    def test_an_unused_key_fails_the_build(self):
        real = build.load_locales

        def with_extra():
            locales = real()
            for loc in locales.values():
                loc.strings["zz.nobody_reads_this"] = "unused"
            return locales

        with mock.patch.object(build, "load_locales", with_extra), self.assertRaises(build.BuildError) as cm:
            build.build()
        self.assertIn("zz.nobody_reads_this", str(cm.exception))

    def test_an_unused_script_key_fails_the_build(self):
        real = build.load_locales

        def with_extra():
            locales = real()
            for loc in locales.values():
                loc.strings["js.nobody_reads_this"] = "unused"
            return locales

        with mock.patch.object(build, "load_locales", with_extra), self.assertRaises(build.BuildError):
            build.build()

    def test_an_unknown_placeholder_fails_the_build(self):
        loc = build.Locale("en", {"x": "{nonsense} code points"})
        with self.assertRaises(build.BuildError):
            build.render("{{x}}", loc)

    def test_measured_numbers_come_from_the_build(self):
        # 7,580 is typed once, in build.py, and formatted for each locale.
        for code, page in PAGES.items():
            html = page.read_text(encoding="utf-8")
            sep = build.DIGIT_SEP[code]
            self.assertIn(build.group_digits(build.CODE_POINTS, sep), html)
        template = build.TEMPLATE.read_text(encoding="utf-8")
        for code in build.LOCALES:
            raw = (build.I18N / f"{code}.json").read_text(encoding="utf-8")
            self.assertNotRegex(raw, r"7[.,]?580", f"{code}: type {{codepoints}} instead of the number")
        self.assertNotRegex(template, r"7[.,]?580", "template: use {{@codepoints}} instead of the number")

    def test_every_fact_the_prose_repeats_comes_from_the_build(self):
        # Each number build.py fills in is typed nowhere else: not in the strings, as a digit or
        # as a word, and (where the number cannot be mistaken for another) not in the template.
        facts = {k: v for k, v in build.facts("en").items() if v.replace(",", "").isdigit()}
        # A small number is a fact only with its unit: the slant is 9°, while the matrix's
        # "9 weights" is the build plan.
        unit = {"slant": r"\s*(°|deg|degrees|graus)"}
        words = r"\b(nineteen|ninety-nine|seventeen|twenty-four|dezenove|noventa e nove|dezessete|vinte e quatro)\b"
        for code in build.LOCALES:
            strings = json.loads((build.I18N / f"{code}.json").read_text(encoding="utf-8"))
            for key, value in strings.items():
                if key.startswith(("cov.", "js.")):
                    continue
                text = re.sub(r"\{[a-z_]+\}|<[^>]+>|\b(cv|ss)\d+", "", value)
                with self.subTest(code=code, key=key):
                    for name, n in facts.items():
                        self.assertNotRegex(text, rf"(?<![\d.,]){re.escape(n.replace(',', ''))}(?![\d.,]){unit.get(name, '')}",
                                            f"type {{{name}}} instead of the number")
                    self.assertNotRegex(text.lower(), words, "type the fact as a {placeholder}")
        template = re.sub(r"\b(cv|ss)\d+", "", build.TEMPLATE.read_text(encoding="utf-8"))
        for name in ("codepoints", "sets", "variants", "italic_redrawn", "first_shapes"):
            n = facts[name].replace(",", "")
            self.assertNotRegex(template, rf"(?<![\d.,#x]){n}(?![\d.,])", f"template: {name} is typed; use the build's value")
        self.assertNotRegex(template, rf"(?<![\d.,#x]){build.SLANT}\s*°", "template: the slant is typed; use the build's value")
        # The machine's "0" carries its feature and count (data-tag, data-n); cv.js reads them.
        zero = next(row for row in build.CHARACTER_VARIANTS if row[0] == "0")
        cv = (build.STATIC / "js" / "cv.js").read_text(encoding="utf-8")
        self.assertNotRegex(cv, rf"\b{zero[2]}\b", "cv.js: read the zero's count from the page")
        self.assertNotIn(f'"{zero[1]}"', cv, "cv.js: read the zero's feature from the page")

    def test_the_oblique_angle_is_the_fonts_slant(self):
        # Both slanted faces carry one italicAngle; the prose states it ({slant}), and every
        # CSS "oblique Ndeg" (the @font-face descriptors, the stylesheet, the scripts) is it.
        self.assertEqual(build.ITALIC_ANGLE[1], build.ITALIC_ANGLE[2])
        self.assertEqual(build.SLANT, -build.ITALIC_ANGLE[1])
        sources = [build.STATIC / "css" / "site.css", *sorted((build.STATIC / "js").glob("*.js")), SITE / "build.py"]
        angles = {f.name: set(re.findall(r"oblique (-?\d+(?:\.\d+)?)deg", f.read_text(encoding="utf-8"))) for f in sources}
        self.assertIn(str(build.SLANT), angles["build.py"])
        for name, found in angles.items():
            self.assertLessEqual(found, {str(build.SLANT)}, name)
        fonts_css = (DOCS / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"font-style:\s*oblique ([\d.]+)deg", fonts_css)), {str(build.SLANT)})

    def test_the_release_comes_from_font_archives_json(self):
        # The repository and the tag are typed once, in font-archives.json, which fetch reads
        # too: a new release only needs a rebuild, and no source of the site names a tag, a
        # version or the repository of its own.
        tag, repository = ARCHIVES["tag"], ARCHIVES["repository"]
        self.assertEqual(build.RELEASE_TAG, tag)
        self.assertEqual(build.REPOSITORY, repository)
        self.assertEqual(build.REPO_URL, f"https://github.com/{repository}")
        self.assertEqual(build.SITE_URL, SITE_URL)
        version = tag.removeprefix("v")
        owner, name = repository.split("/")
        named = re.compile(rf"(?<![\w.]){re.escape(version)}(?![\w.])")
        for path in [build.TEMPLATE, build.SITE / "build.py", *sorted(build.I18N.glob("*.json")),
                     *sorted(build.STATIC.rglob("*.js")), *sorted(build.STATIC.rglob("*.css"))]:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(REPO).as_posix()):
                self.assertIsNone(re.search(r"releases/(tag|download)/v?\d", text), "build the release URL from the tag")
                self.assertNotIn(tag, text, f"it names {tag}: type {{tag}} instead")
                self.assertIsNone(named.search(text), f"it names {version}: type {{tag}} or {{version}} instead")
                self.assertNotIn(repository.lower(), text.lower(), "build the repository URL from font-archives.json")
                self.assertNotIn(f"{owner.lower()}.github.io", text.lower(), "build the site URL from font-archives.json")
        repo = f"https://github.com/{repository}/"
        upstream = ("https://github.com/be5invis/Iosevka", "https://github.com/ryanoasis/nerd-fonts")
        for page in PAGES.values():
            html = page.read_text(encoding="utf-8")
            hrefs = [a.get("href") or "" for t, a in parse(page).tags if t == "a"]
            with self.subTest(page=page.relative_to(REPO).as_posix()):
                self.assertIn(f"/releases/tag/{tag}", html)
                self.assertIn(f"/releases/download/{tag}/noctua-iosevka-", html)
                releases = [h for h in hrefs if "/releases/" in h]
                self.assertGreaterEqual(len(releases), 1 + len(build.ARCHIVE_ORDER) * len(build.ARCHIVE_FORMATS))
                for h in releases:
                    self.assertTrue(h.startswith(repo + "releases/"), h)
                ours = [h for h in hrefs if h.startswith("https://github.com/") and not h.startswith(upstream)]
                for h in ours:
                    self.assertTrue((h + "/").startswith(repo), f"a repository link outside {repo}: {h}")
                self.assertGreaterEqual(len([h for h in ours if "/releases/" not in h]), 2, "the credits and the footer link the repository")

    def test_translations_differ(self):
        locales = build.load_locales()
        same = [k for k, v in locales["en"].strings.items()
                if v == locales["pt-BR"].strings[k] and len(v) > 12 and not k.startswith(("cov.", "dl.fmt", "scripts.latin_sample"))]
        self.assertLess(len(same), 6, f"untranslated strings: {same}")


class TestLinks(unittest.TestCase):
    def test_relative_urls_resolve(self):
        missing = []
        for page in PAGES.values():
            p = parse(page)
            for tag, a in p.tags:
                for attr in ("href", "src"):
                    if attr in a and a[attr] is not None:
                        target = resolve(page, a[attr])
                        if target is not None and not target.is_file():
                            missing.append(f"{page.relative_to(REPO)}: <{tag} {attr}={a[attr]!r}>")
        for css in docs_files(".css"):
            for _, url in CSS_URL.findall(css_text(css)):
                target = resolve(css, url)
                if target is not None and not target.is_file():
                    missing.append(f"{css.relative_to(REPO)}: url({url})")
        self.assertEqual(missing, [])

    def test_js_imports_resolve(self):
        missing = []
        for js in docs_files(".js"):
            for spec in JS_IMPORT.findall(js.read_text(encoding="utf-8")):
                if is_external(spec):
                    missing.append(f"{js.relative_to(REPO)}: external import {spec}")
                    continue
                if not (js.parent / spec).resolve().is_file():
                    missing.append(f"{js.relative_to(REPO)}: {spec}")
        self.assertEqual(missing, [])

    def test_nothing_loads_from_elsewhere(self):
        bad = []
        for page in PAGES.values():
            p = parse(page)
            for tag, a in p.tags:
                for attr in ("src", "srcset", "data", "poster"):
                    if a.get(attr) and re.search(r"https?:", a[attr]):
                        bad.append(f"<{tag} {attr}={a[attr]!r}>")
                if tag == "link":
                    rel = set((a.get("rel") or "").lower().split())
                    if rel & {"stylesheet", "preload", "icon", "modulepreload", "prefetch", "manifest"} and is_external(a.get("href") or ""):
                        bad.append(f"<link rel={a.get('rel')} href={a.get('href')!r}>")
                    elif rel and not rel <= {"canonical", "alternate", "stylesheet", "preload", "icon", "modulepreload"}:
                        bad.append(f"unexpected <link rel={a.get('rel')}>")
                if tag == "meta" and (a.get("property") or "").startswith("og:") and is_external(a.get("content") or ""):
                    if not (a.get("content") or "").startswith(SITE_URL):
                        bad.append(f"og metadata points outside the site: {a.get('content')}")
        for css in docs_files(".css"):
            text = css_text(css)
            bad += [f"{css.name}: url({u})" for _, u in CSS_URL.findall(text) if is_external(u) and not u.startswith("data:")]
            bad += [f"{css.name}: @import {u}" for u in CSS_IMPORT.findall(text)]
        for js in docs_files(".js"):
            text = js.read_text(encoding="utf-8")
            bad += [f"{js.name}: {m}" for m in re.findall(r"""\b(?:fetch|import)\s*\(\s*["'`]https?:[^"'`]*""", text)]
        self.assertEqual(bad, [])

    def test_external_links_are_plain_links(self):
        for page in PAGES.values():
            for tag, a in parse(page).tags:
                href = a.get("href") or ""
                if is_external(href):
                    self.assertTrue(
                        tag == "a" or (tag == "link" and set((a.get("rel") or "").split()) <= {"canonical", "alternate"}),
                        f"{tag} href={href}",
                    )
                    self.assertTrue(href.startswith("https://"), f"not https: {href}")


class TestSecurity(unittest.TestCase):
    def test_csp_meta_identical_on_both_pages(self):
        found = {}
        for code, page in PAGES.items():
            metas = [a.get("content") for t, a in parse(page).tags if t == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy"]
            self.assertEqual(len(metas), 1, f"{code}: one CSP meta expected")
            found[code] = metas[0]
        self.assertEqual(found["en"], found["pt-BR"])
        self.assertEqual(found["en"], CSP)

    def test_csp_comes_first(self):
        for page in PAGES.values():
            tags = [(t, a) for t, a in parse(page).tags if t in ("meta", "script", "link", "style")]
            first_active = next(i for i, (t, a) in enumerate(tags) if t != "meta")
            csp = next(i for i, (t, a) in enumerate(tags) if t == "meta" and a.get("http-equiv"))
            self.assertLess(csp, first_active)

    def test_no_inline_script_style_or_handlers(self):
        for code, page in PAGES.items():
            p = parse(page)
            self.assertEqual(p.styles, 0, f"{code}: <style> element")
            for attrs, body in p.scripts:
                self.assertTrue(attrs.get("src"), f"{code}: inline script")
                self.assertEqual(body.strip(), "", f"{code}: script with a body")
            for tag, a in p.tags:
                self.assertNotIn("style", a, f"{code}: style= on <{tag}>")
                handlers = [k for k in a if k.lower().startswith("on")]
                self.assertEqual(handlers, [], f"{code}: {handlers} on <{tag}>")
                for attr in ("href", "src", "action", "formaction"):
                    self.assertFalse((a.get(attr) or "").strip().lower().startswith("javascript:"), f"{code}: javascript: URL")

    def test_scripts_do_not_evaluate_strings(self):
        for js in docs_files(".js"):
            text = js.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\beval\s*\(", js.name)
            self.assertNotRegex(text, r"\b(?:new\s+)?Function\s*\(", js.name)
            self.assertNotRegex(text, r"\bset(?:Timeout|Interval)\s*\(\s*[\"'`]", js.name)


class TestLanguages(unittest.TestCase):
    def test_lang_and_alternates(self):
        expected = {"en": SITE_URL, "pt-BR": SITE_URL + "pt-BR/"}
        for code, page in PAGES.items():
            p = parse(page)
            html = next(a for t, a in p.tags if t == "html")
            self.assertEqual(html.get("lang"), code)
            alts = {a.get("hreflang"): a.get("href") for t, a in p.tags if t == "link" and a.get("rel") == "alternate"}
            self.assertEqual(alts, {"en": expected["en"], "pt-BR": expected["pt-BR"], "x-default": expected["en"]})
            canon = [a.get("href") for t, a in p.tags if t == "link" and a.get("rel") == "canonical"]
            self.assertEqual(canon, [expected[code]])
            og = {a.get("property"): a.get("content") for t, a in p.tags if t == "meta" and a.get("property")}
            self.assertEqual(og.get("og:url"), expected[code])
            self.assertEqual(og.get("og:locale"), "en_US" if code == "en" else "pt_BR")
            self.assertEqual(og.get("og:locale:alternate"), "pt_BR" if code == "en" else "en_US")
            for key in ("og:title", "og:description", "og:type"):
                self.assertTrue(og.get(key), key)

    def test_language_switch_is_plain_links(self):
        for code, page in PAGES.items():
            p = parse(page)
            links = [a for t, a in p.tags if t == "a" and a.get("hreflang")]
            self.assertGreaterEqual(len(links), 4)
            for a in links:
                target = resolve(page, a["href"])
                self.assertIsNotNone(target)
                want = PAGES["en"] if a["hreflang"] == "en" else PAGES["pt-BR"]
                self.assertEqual(target, want.resolve())
                self.assertEqual(a.get("lang"), a["hreflang"])
                self.assertEqual("aria-current" in a, a["hreflang"] == code)

    def test_metadata_present(self):
        for code, page in PAGES.items():
            p = parse(page)
            metas = {a.get("name"): a.get("content") for t, a in p.tags if t == "meta" and a.get("name")}
            self.assertTrue(metas.get("description"))
            self.assertIn("theme-color", metas)
            self.assertTrue(any(t == "title" for t, a in p.tags))
            icons = [a for t, a in p.tags if t == "link" and a.get("rel") == "icon"]
            self.assertEqual(len(icons), 1)
            self.assertTrue(icons[0]["href"].endswith(".svg"))


class TestFonts(unittest.TestCase):
    def faces(self):
        css = (DOCS / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
        return re.findall(r"@font-face\{[^}]*\}", css)

    def test_every_font_face_src_exists(self):
        css_path = DOCS / "assets" / "css" / "fonts.css"
        faces = self.faces()
        self.assertEqual(len(faces), sum(len(f.faces) for f in build.FAMILIES))
        for face in faces:
            urls = CSS_URL.findall(face)
            self.assertEqual(len(urls), 1, face)
            target = resolve(css_path, urls[0][1])
            self.assertTrue(target and target.is_file(), urls[0][1])

    def test_no_synthesis(self):
        css = (DOCS / "assets" / "css" / "site.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"html\s*\{[^}]*font-synthesis:\s*none")

    def test_licences_travel_with_the_fonts(self):
        lic = DOCS / "assets" / "fonts" / "licenses"
        shipped = {p.parent.name for p in (DOCS / "assets" / "fonts").rglob("*.woff2")}
        self.assertTrue(shipped)
        if shipped - {"term"}:
            self.assertEqual((lic / "OFL-Iosevka.txt").read_bytes(), (REPO / "noctua-iosevka" / "licenses" / "OFL-Iosevka.txt").read_bytes())
        if "term" in shipped:
            self.assertEqual(
                (lic / "LICENSE-NerdFontsSymbolsOnly.txt").read_bytes(),
                (REPO / "symbols-nerd-font" / "licenses" / "LICENSE-NerdFontsSymbolsOnly.txt").read_bytes(),
            )
            # The Nerd faces are patched Iosevka: the OFL applies to them as well.
            self.assertTrue((lic / "OFL-Iosevka.txt").is_file())

    def test_the_page_links_both_licences(self):
        for page in PAGES.values():
            hrefs = [a.get("href") for t, a in parse(page).tags if t == "a"]
            for name in ("OFL-Iosevka.txt", "LICENSE-NerdFontsSymbolsOnly.txt"):
                self.assertTrue(any(h and h.endswith(f"assets/fonts/licenses/{name}") for h in hrefs), name)

    def test_budget(self):
        total = sum(p.stat().st_size for p in (DOCS / "assets" / "fonts").rglob("*.woff2"))
        self.assertLessEqual(total, FONT_BUDGET, f"{total:,} bytes of site fonts")

    def test_no_stray_fonts(self):
        named = set()
        css_path = DOCS / "assets" / "css" / "fonts.css"
        for face in self.faces():
            named.add(resolve(css_path, CSS_URL.findall(face)[0][1]))
        on_disk = {p.resolve() for p in (DOCS / "assets" / "fonts").rglob("*.woff2")}
        self.assertEqual(on_disk - named, set())


class TestCoverage(unittest.TestCase):
    """Every subset must draw every character the pages set with it."""

    JS = DOCS / "assets" / "js"

    def page_text(self, family: str) -> set[str]:
        chars = set()
        for page in PAGES.values():
            chars |= set("".join(parse(page).by_family.get(family, [])))
        return chars

    @staticmethod
    def drawn(chars) -> set[str]:
        return {c for c in chars if not c.isspace() and unicodedata.category(c) not in ("Cc", "Cf")}

    def script_strings(self) -> set[str]:
        """Every string the scripts show in the text faces: strings.js and the scripts' own text."""
        chars = set((self.JS / "strings.js").read_text(encoding="utf-8"))
        for js in sorted(self.JS.glob("*.js")):
            if js.name not in ("strings.js", "terminal.js"):
                chars |= set(js.read_text(encoding="utf-8"))
        return chars

    def test_text_faces_cover_both_pages(self):
        # Checked against the text repertoire alone: nothing the terminal or the lab face draws
        # is counted here, so a character dropped from TEXT is caught even if another subset has it.
        chars = self.page_text("text") | self.page_text("display") | self.script_strings()
        missing = sorted(c for c in self.drawn(chars) if ord(c) not in subset.TEXT)
        self.assertEqual(missing, [], f"not in the text subset: {missing}")

    def test_display_faces_cover_both_locales(self):
        locales = build.load_locales()
        greek = set(range(0x370, 0x400))
        chars = set()
        for loc in locales.values():
            for value in loc.strings.values():
                chars |= set(re.sub(r"<[^>]+>", "", value))
        # Letters, digits, punctuation and spaces: what headings, buttons and labels are made of.
        wanted = {c for c in chars if unicodedata.category(c)[0] in "LNPZ" and ord(c) >= 0x20}
        missing = sorted(c for c in wanted if ord(c) not in subset.DISPLAY and ord(c) not in greek and not "\u0400" <= c <= "\u04ff")
        self.assertEqual(missing, [], f"not in the display subset: {missing}")

    def test_display_faces_cover_what_the_template_sets_in_them(self):
        # Headings, the hero, the footer mark and every block of class lfd, both pages, and the
        # words the tapes draw on their canvas.
        chars = self.page_text("display")
        chars |= set("".join(re.findall(r'"([^"]*)"', (self.JS / "ticker.js").read_text(encoding="utf-8").split("const FAMILY")[0])))
        missing = sorted(c for c in self.drawn(chars) if ord(c) not in subset.DISPLAY)
        self.assertEqual(missing, [], f"not in the display subset: {missing}")

    def test_lab_face_covers_the_machine_and_the_strips(self):
        lab = subset.lab_repertoire(build)
        chars = self.page_text("lab")
        self.assertTrue(chars, "no text set in the lab face")
        missing = sorted(c for c in self.drawn(chars) if ord(c) not in lab)
        self.assertEqual(missing, [], f"not in the lab subset: {missing}")
        strips = {ch for *_, strip in build.COVERAGE for ch in strip if ch != " "}
        self.assertEqual(sorted(c for c in strips if ord(c) not in lab), [])

    def test_terminal_face_covers_everything_the_terminal_prints(self):
        text = (self.JS / "terminal.js").read_text(encoding="utf-8")
        # Icons written as escapes and as literal characters (private use, planes 0 and 15).
        cps = {int(h, 16) for h in re.findall(r"\\u\{?([0-9A-Fa-f]{4,5})\}?", text)}
        cps |= {ord(c) for c in text if ord(c) > 0x7E and not c.isspace()}
        cps |= {cp for cp, _ in build.ICON_STRIP}
        cps |= {ord(c) for c in self.drawn(self.page_text("term"))}
        for loc in build.load_locales().values():
            for key in ("term.c1", "term.c2", "term.c3", "term.cell"):
                cps |= {ord(c) for c in self.drawn(loc.strings[key])}
        self.assertGreater(len([c for c in cps if 0xE000 <= c <= 0xF8FF or c >= 0xF0000]), 20, "the scan found too few icons")
        self.assertEqual(sorted(hex(c) for c in cps - subset.TERM), [])

    def test_lazy_faces_live_in_lazy_blocks(self):
        for code, page in PAGES.items():
            self.assertEqual(parse(page).lazy_outside, [], code)


class TestReferences(unittest.TestCase):
    """In-page references: every id an attribute names exists, once."""

    REF_ATTRS = ("aria-controls", "aria-labelledby", "aria-describedby", "aria-owns", "for")

    def test_ids_are_unique(self):
        for code, page in PAGES.items():
            ids = [a["id"] for t, a in parse(page).tags if a.get("id")]
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            self.assertEqual(dupes, [], code)

    def test_every_reference_resolves(self):
        for code, page in PAGES.items():
            tags = parse(page).tags
            ids = {a["id"] for t, a in tags if a.get("id")}
            missing = []
            for tag, a in tags:
                href = a.get("href") or ""
                if href.startswith("#") and len(href) > 1 and href[1:] not in ids:
                    missing.append(f"<{tag} href={href}>")
                for attr in self.REF_ATTRS:
                    for ref in (a.get(attr) or "").split():
                        if ref not in ids:
                            missing.append(f"<{tag} {attr}={ref}>")
                sel = a.get("data-copy")
                if sel is not None and (not sel.startswith("#") or sel[1:] not in ids):
                    missing.append(f"<{tag} data-copy={sel}>")
            self.assertEqual(missing, [], code)


class TestCoverageTable(unittest.TestCase):
    def test_strip_characters_lie_in_their_block(self):
        wrong = []
        for key, lo, hi, n, total, strip in build.COVERAGE:
            self.assertEqual(len(strip), build.STRIP, key)
            wrong += [f"{key}: U+{ord(c):04X}" for c in strip if c != " " and not lo <= ord(c) <= hi]
        self.assertEqual(wrong, [])

    def test_block_totals_are_what_unicode_assigns(self):
        # Assigned characters, control codes aside (the rule the table states).
        for key, lo, hi, n, total, strip in build.COVERAGE:
            assigned = sum(1 for cp in range(lo, hi + 1) if unicodedata.category(chr(cp)) not in ("Cn", "Cc"))
            self.assertEqual(assigned, total, key)
            self.assertLessEqual(n, total, key)

    def test_pages_are_in_normal_form_c(self):
        for code, page in PAGES.items():
            text = page.read_text(encoding="utf-8")
            self.assertTrue(unicodedata.is_normalized("NFC", text), f"{code}: a character normalisation would change")
        # ... and the two Greek Extended characters that NFC folds still reach the page.
        lab = set("".join(parse(PAGES["en"]).by_family.get("lab", [])))
        self.assertIn("\u1f71", lab)
        self.assertIn("\u1f7b", lab)


class TestScriptRules(unittest.TestCase):
    JS = SITE / "static" / "js"

    def test_canvases_are_capped_through_dpr(self):
        for js in sorted(self.JS.glob("*.js")):
            if js.name != "motion.js":
                self.assertNotIn("devicePixelRatio", js.read_text(encoding="utf-8"), f"{js.name}: use dpr() from motion.js")
        motion = (self.JS / "motion.js").read_text(encoding="utf-8")
        self.assertRegex(motion, r"export const dpr = \(\) => Math\.min\(2, window\.devicePixelRatio \|\| 1\);")

    def test_no_html_from_strings(self):
        for js in sorted(self.JS.glob("*.js")):
            text = js.read_text(encoding="utf-8")
            found = re.findall(r"\b(innerHTML|outerHTML|insertAdjacentHTML|document\.write)\b", text)
            if js.name == "code.js":
                # The minimap copies the page's own static markup, never anything a visitor typed.
                self.assertLessEqual(len(found), 2, js.name)
            else:
                self.assertEqual(found, [], js.name)


class TestTerminalStrings(unittest.TestCase):
    def test_a_long_terminal_string_fails_the_build(self):
        real = build.load_locales

        def too_long():
            locales = real()
            locales["pt-BR"].strings["term.cell"] = "x" * (build.TERM_ROOM["term.cell"] + 1)
            return locales

        with mock.patch.object(build, "load_locales", too_long), self.assertRaises(build.BuildError) as cm:
            build.build()
        self.assertIn("term.cell", str(cm.exception))

    def test_the_strings_fit(self):
        for loc in build.load_locales().values():
            for key, room in build.TERM_ROOM.items():
                self.assertLessEqual(len(loc.strings[key]), room, f"{loc.code} {key}")


LABELABLE = {"button", "input", "meter", "output", "progress", "select", "textarea"}


class Fields(HTMLParser):
    """The form fields of a page and what labels them, and the classes around every element."""

    VOID = Page.VOID

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fields = []      # (tag, attrs, labelled by a wrapping label)
        self.label_for = set()
        self.elements = []    # (tag, attrs, classes of the element and its ancestors)
        self._labels = []     # open <label>s: {"for": ..., "claimed": bool}
        self._stack = []      # (tag, classes)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        around = set().union(classes, *(c for _, c in self._stack))
        self.elements.append((tag, a, around))
        if tag == "label":
            if a.get("for"):
                self.label_for.add(a["for"])
            self._labels.append({"for": a.get("for"), "claimed": False})
        elif tag in LABELABLE and not (tag == "input" and (a.get("type") or "").lower() == "hidden"):
            # A label labels its for= target, or else the first labelable element inside it.
            wrapped = False
            if self._labels and not self._labels[-1]["claimed"]:
                self._labels[-1]["claimed"] = True
                wrapped = self._labels[-1]["for"] is None
            if tag in ("input", "select", "textarea"):
                self.fields.append((tag, a, wrapped))
        if tag not in self.VOID:
            self._stack.append((tag, classes))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID and self._stack and self._stack[-1][0] == tag:
            self._stack.pop()

    def handle_endtag(self, tag):
        if tag == "label" and self._labels:
            self._labels.pop()
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break


def fields(path: Path) -> Fields:
    f = Fields()
    f.feed(path.read_text(encoding="utf-8"))
    f.close()
    return f


class TestAccessibleNames(unittest.TestCase):
    def test_every_field_has_a_label(self):
        # for= on a <label>, a wrapping <label> whose first labelable element it is (an <output>
        # before the field takes the label instead), aria-label or aria-labelledby.
        for code, page in PAGES.items():
            f = fields(page)
            self.assertGreater(len(f.fields), 10, code)
            unnamed = [
                f"<{tag} id={a.get('id')!r} type={a.get('type')!r}>" for tag, a, wrapped in f.fields
                if not (wrapped or (a.get("id") and a["id"] in f.label_for) or (a.get("aria-label") or "").strip()
                        or (a.get("aria-labelledby") or "").strip())
            ]
            self.assertEqual(unnamed, [], code)


class TestWithoutScripts(unittest.TestCase):
    """What a visitor without JavaScript gets: a static specimen, not a broken app."""

    CSS = SITE / "static" / "css" / "site.css"
    # The one control a page keeps without scripts: the tester's text box (it takes typing on its
    # own). Nothing else is a tab stop there: the code and install panels are static groups, and
    # take focus only once ui.js has made them tab panels.
    NATIVE = {("textarea", "t-text")}

    def test_every_scripted_control_is_marked(self):
        for code, page in PAGES.items():
            unmarked = []
            for tag, a, around in fields(page).elements:
                role = a.get("role") or ""
                control = tag in ("button", "input", "select", "textarea") or role in ("tab", "radio", "switch", "button", "slider") \
                    or a.get("tabindex") not in (None, "-1")
                if control and "js-only" not in around and (tag, a.get("id")) not in self.NATIVE:
                    unmarked.append(f"<{tag} id={a.get('id')!r} class={a.get('class')!r}>")
            self.assertEqual(unmarked, [], f"{code}: controls a page without scripts would show, doing nothing")

    def test_the_stylesheet_hides_them_and_shows_the_rest(self):
        css = self.CSS.read_text(encoding="utf-8")
        self.assertRegex(css, r"html:not\(\.js\) \.js-only, html\.js \.static-only \{ display: none !important; \}")
        # The panels the tab lists would hide are all shown.
        self.assertRegex(css, r"html:not\(\.js\) \.pane\[hidden\] \{ display: block !important; \}")
        self.assertRegex(css, r"html:not\(\.js\) \.ins-pane\[hidden\] \{ display: block !important; \}")
        # As tab panels they take focus (the WAI-ARIA tab pattern); ui.js gives it to them.
        ui = (SITE / "static" / "js" / "ui.js").read_text(encoding="utf-8")
        self.assertRegex(ui, r'panel\.setAttribute\("role", "tabpanel"\);[^}]*panel\.tabIndex = 0;')

    def test_lazy_faces_apply_without_scripts(self):
        css = self.CSS.read_text(encoding="utf-8")
        for cls in ["lfd", "lft", "lfs", "lfl", "lfm", *(f"lw{i}" for i in range(1, 10)), *(f"lx{i}" for i in range(1, 6)), "lsu", "lsi", "lso"]:
            self.assertRegex(css, rf":is\(\[data-armed\], html:not\(\.js\)\) \.{cls} \{{", cls)
            self.assertNotRegex(css, rf"(?m)^\[data-armed\] \.{cls} \{{", f"{cls} applies only once armed")

    def test_sections_are_laid_out_whole_without_scripts(self):
        # content-visibility: auto skips the sections an in-page link jumps over, and without
        # ui.js laying them out first, the jump lands on guessed heights.
        css = re.sub(r"/\*.*?\*/", "", self.CSS.read_text(encoding="utf-8"), flags=re.S)
        rules = re.findall(r"([^{}]+)\{[^}]*content-visibility:\s*auto", css)
        self.assertTrue(rules)
        for selector in rules:
            self.assertTrue(selector.strip().startswith("html.js "), selector.strip())

    def test_the_terminal_holds_its_still_frame(self):
        for code, page in PAGES.items():
            html = page.read_text(encoding="utf-8")
            block = re.search(r'<div class="term-lines" id="term-lines">(.*?)</div></div>\s*<div class="term-side"', html, re.S).group(1)
            rows = re.findall(r'<div class="term-line"([^>]*)>(.*?)</div>', block)
            for cols in (build.TERM_COLS, build.TERM_NARROW):
                frame = [(attrs, unescape(re.sub(r"<[^>]+>", "", body))) for attrs, body in rows
                         if 'data-cols="' not in attrs or f'data-cols="{cols}"' in attrs]
                self.assertEqual(len(frame), build.TERM_ROWS, f"{code}: {cols} cells")
                for attrs, text in frame:
                    self.assertLessEqual(len(text), cols, f"{code}: {text!r}")
                    if 'data-row="panel"' in attrs:
                        self.assertEqual(len(text), cols, f"{code}: {text!r}")
                self.assertIn("term-cursor", block)
            side = re.search(r'<div class="term-side" id="term-side">(.*?<div class="term-nvim">.*?</div>)</div>', html, re.S)
            self.assertIsNotNone(side, f"{code}: the neo-tree and nvim split")
            for name in ("TTF", "TTF-nerdfonts", "WOFF2", "WOFF2-nerdfonts", "licenses", "private-build-plans.toml"):
                self.assertIn(f" {name}</span>", side.group(1), f"{code}: noctua-iosevka/{name} in the tree")


def _fonttools():
    try:
        import fontTools.ttLib  # noqa: F401
    except ImportError:
        return False
    return (REPO / "noctua-iosevka" / "TTF" / "NoctuaIosevka-Regular.ttf").is_file()


@unittest.skipUnless(_fonttools(), "needs fontTools and the built fonts under noctua-iosevka/TTF")
class TestFontFacts(unittest.TestCase):
    """The facts build.py states, measured again from the TTFs (read only)."""

    @classmethod
    def setUpClass(cls):
        from fontTools.ttLib import TTFont
        cls.TTFont = TTFont
        cls.regular = TTFont(REPO / "noctua-iosevka" / "TTF" / "NoctuaIosevka-Regular.ttf", lazy=True)

    @classmethod
    def tearDownClass(cls):
        cls.regular.close()

    def test_code_points(self):
        cmap = self.regular.getBestCmap()
        self.assertEqual(len(cmap), build.CODE_POINTS)
        for stem in ("NoctuaIosevka-CondensedThinItalic", "NoctuaIosevka-ExtendedHeavyOblique"):
            with self.TTFont(REPO / "noctua-iosevka" / "TTF" / f"{stem}.ttf", lazy=True) as other:
                self.assertEqual(set(other.getBestCmap()), set(cmap), stem)

    def test_block_counts(self):
        cmap = self.regular.getBestCmap()
        for key, lo, hi, n, total, strip in build.COVERAGE:
            drawn = sum(1 for cp in range(lo, hi + 1) if cp in cmap and unicodedata.category(chr(cp)) not in ("Cn", "Cc"))
            self.assertEqual(drawn, n, key)
            for ch in strip:
                if ch == " ":
                    continue
                self.assertIn(ord(ch), cmap, f"{key}: U+{ord(ch):04X}")

    def test_character_variant_features(self):
        tags = {rec.FeatureTag for rec in self.regular["GSUB"].table.FeatureList.FeatureRecord}
        self.assertEqual(len({t for t in tags if re.fullmatch(r"cv\d\d", t)}), build.CV_FEATURES)

    def test_character_variant_shapes(self):
        # Each of the machine's features is one alternate substitution: as many values as the
        # glyph has shapes, each a distinct outline, and the default value's is the default's.
        from fontTools.pens.recordingPen import DecomposingRecordingPen

        gsub = self.regular["GSUB"].table
        cmap = self.regular.getBestCmap()
        glyphs = self.regular.getGlyphSet()

        def outline(name):
            pen = DecomposingRecordingPen(glyphs)
            glyphs[name].draw(pen)
            return glyphs[name].width, tuple((op, tuple(args)) for op, args in pen.value)

        for ch, tag, n, default in build.CHARACTER_VARIANTS:
            with self.subTest(ch=ch, tag=tag):
                base = cmap[ord(ch)]
                found = []
                for rec in gsub.FeatureList.FeatureRecord:
                    if rec.FeatureTag != tag:
                        continue
                    for i in rec.Feature.LookupListIndex:
                        lookup = gsub.LookupList.Lookup[i]
                        for sub in lookup.SubTable:
                            sub = sub.ExtSubTable if lookup.LookupType == 7 else sub
                            if sub.LookupType == 3 and base in sub.alternates:
                                found.append(sub.alternates[base])
                self.assertEqual(len(found), 1)
                alternates = found[0]
                self.assertEqual(len(alternates), n)
                self.assertEqual(len({outline(g) for g in alternates}), n, "each value a distinct outline")
                self.assertEqual(outline(alternates[default - 1]), outline(base), "the default value")

    def test_code_points_the_italic_redraws(self):
        # Outlines decomposed, so a composite that differs only through its parts counts too.
        from fontTools.pens.recordingPen import DecomposingRecordingPen

        ttf = REPO / "noctua-iosevka" / "TTF"
        with self.TTFont(ttf / "NoctuaIosevka-Italic.ttf") as it, self.TTFont(ttf / "NoctuaIosevka-Oblique.ttf") as ob:
            def outline(font, glyphs, name):
                pen = DecomposingRecordingPen(glyphs)
                glyphs[name].draw(pen)
                return glyphs[name].width, pen.value

            ci, co = it.getBestCmap(), ob.getBestCmap()
            gi, go = it.getGlyphSet(), ob.getGlyphSet()
            self.assertEqual(set(ci), set(co))
            differ = sum(1 for cp in ci if outline(it, gi, ci[cp]) != outline(ob, go, co[cp]))
        self.assertEqual(differ, build.ITALIC_REDRAWN)

    def test_weight_and_width_classes_and_italic_angles(self):
        # Every one of the 135 faces: OS/2 usWeightClass (the CSS weight) and usWidthClass, and
        # post.italicAngle, the slant the prose states.
        ttf = REPO / "noctua-iosevka" / "TTF"
        for s in range(len(build.SLOPES)):
            for x in range(len(build.WIDTHS)):
                for w in range(len(build.WEIGHTS)):
                    stem = build.file_stem(w, x, s)
                    with self.TTFont(ttf / f"{stem}.ttf", lazy=True) as face:
                        got = (face["OS/2"].usWeightClass, face["OS/2"].usWidthClass, face["post"].italicAngle)
                    self.assertEqual(got, (build.WEIGHTS[w][0], build.WIDTH_CLASS[x], build.ITALIC_ANGLE[s]), stem)

    def test_stylistic_set_names(self):
        names = {}
        name_table = self.regular["name"]
        for rec in self.regular["GSUB"].table.FeatureList.FeatureRecord:
            params = rec.Feature.FeatureParams
            if rec.FeatureTag.startswith("ss") and params is not None and hasattr(params, "UINameID"):
                names[rec.FeatureTag] = name_table.getDebugName(params.UINameID)
        self.assertEqual(names, {tag: name for tag, name, _ in build.STYLISTIC_SETS})


if __name__ == "__main__":
    unittest.main()
