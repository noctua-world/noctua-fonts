# The Noctua Iosevka site

The source of the repository's GitHub Pages site: one page whose only job is to show
Noctua Iosevka. It is published from `docs/` on `main` ("Deploy from a branch", folder
`/docs`), in two languages:

| page | URL | source of its strings |
|---|---|---|
| `docs/index.html` | https://noctua-world.github.io/noctua-fonts/ | `site/i18n/en.json` |
| `docs/pt-BR/index.html` | https://noctua-world.github.io/noctua-fonts/pt-BR/ | `site/i18n/pt-BR.json` |

Each URL names its language. There is no automatic redirect; the language switch is a pair of
plain links, and the pages carry `hreflang` alternates for search engines. Both addresses, and
every link to the repository and its release, come from the `repository` of
`font-archives.json` (see below).

**`docs/` is generated output.** Edit `site/`, rebuild, and commit both. Never edit `docs/`
by hand: `python3 site/build.py --check` (and the tests) fail when it drifts from the sources.

## What is in `site/`

| path | what it is |
|---|---|
| `template.html` | the one page template, for both languages |
| `i18n/en.json`, `i18n/pt-BR.json` | every string a visitor sees, aria labels and metadata included |
| `static/css/site.css` | the stylesheet (copied to `docs/assets/css/`) |
| `static/js/*.js` | the page's ES modules, hand-written, no dependencies (copied to `docs/assets/js/`) |
| `static/favicon.svg` | the icon |
| `build.py` | renders the pages and writes `docs/` — standard library only |
| `subset-fonts.py` | writes the subset WOFF2 faces into `docs/assets/fonts/` — fontTools and brotli |

`build.py` also generates three files from data it holds: `docs/assets/css/fonts.css` (one
`@font-face` per subset face), `docs/assets/css/facts.css` (the measured values the stylesheet
needs: the size that fits each one-line section title to its column, per language, the share
of the ASCII glyphs each stylistic set redraws, and the set the lens and the §06 title start
in) and `docs/assets/js/strings.js` (the strings the scripts show, in both languages, plus the
face matrix). The font facts the page states are constants at the top of `build.py`, measured
from the TTFs with fontTools and HarfBuzz: which glyphs each stylistic set redraws, how many
character-variant features the font carries and how many shapes each one in the machine has,
how many code points the italic redraws, the Unicode block counts and their sample strips, and
the OS/2 weight and width classes and the italic angle of every face. The optional font-fact
tests (they need fontTools and the built fonts) measure them all again but which glyphs each
set redraws: the code points and the block counts, the set names, the
character-variant features and the shapes of each glyph in the machine, the code points the
italic redraws, and the classes and the angle of all 135 faces. `LIGATURES` is not such a fact:
it is the selection of sequences the page shows, by the feature that forms them, and a feature
joins more than the page shows (`dlig` most of all), so the prose gives no count of them.

A number the prose takes from those facts is written once, in `build.py`: the locale strings
name it as a placeholder and the build fills it in, formatted for the language (7,580 in
English, 7.580 in Portuguese). They are `{codepoints}`, `{sets}` (19), `{variants}` (99),
`{first_shapes}` (the 33 shapes of the machine's first glyph), `{italic_redrawn}` (466),
`{slant}` (9, in degrees, from the italic angle), `{blocks}` (17), `{strip}` (24) and
`{set_default}` (`ss02`, the set that redraws the most); the template takes the hero's counters
as `{{@codepoints}}`, `{{@sets}}` and `{{@variants}}`, and `cv.js` reads the zero's feature and
count from the machine's button, where the build writes them. The explorer's slope chips take
the angle from the build too, and every `oblique 9deg` of the stylesheet and the scripts (the CSS
name of the oblique faces) is checked against it by the tests. The face matrix itself
(135 = 9 × 5 × 3) and the advances of the width ladder are the build plan, and the strings write
them out as such; so do the vertical metrics beside the guides.

The release and the repository work the same way: the page names the release and links to
its archives through `{tag}`, `{version}` and `{release_url}`, and to the repository through
`{{@repo_url}}`, all read from `font-archives.json` (its `tag` and its `repository`, the ones
`font-archives.py fetch` uses); the site's own address is `https://<owner>.github.io/<name>/`
from the same `repository`. For a new release, change that tag, run `python3 site/build.py` and
commit `docs/`; the tests fail if a source of the site names a tag, a version, a release URL or
the repository of its own.

### Template tags

| tag | becomes |
|---|---|
| `{{key}}` | the locale string, HTML-escaped |
| `{{&key}}` | the locale string as HTML (for strings that carry `<code>`, `<b>`, `<i>`, `<a>`) |
| `{{@name}}` | a per-page value: `lang`, `root`, `canonical`, the `hreflang` targets, `repo_url`, the hero's counters … |
| `{{%name}}` | a fragment `build.py` generates (the 135-tile wall, the set cards, the archives, the section titles drawn in several faces, the terminal's still frame …) |

Locale keys that start with `js.` belong to the scripts, which read them as `t("name")`.
A key missing from either language, a key nothing uses, an unknown tag, a placeholder the build
cannot fill or a script asking for a key that does not exist is a build failure. So is a
terminal string longer than the terminal's grid allows (`TERM_ROOM` in `build.py`: on a phone
the session is 38 cells wide, and the value beside fastfetch's "Cell" has 18 of them), and so
is any row of the terminal the build draws that does not fit its session or its buffer.

The terminal's still frame is written by the build (`term_still` in `build.py`): btop's two
panels, fastfetch and its owl, and the prompt, 24 rows, with btop's panels drawn for both
widths of the session (46 cells, and 38 in a terminal under 560 px, a phone; a container query
shows the right ones). The neo-tree and nvim split of the wide terminal and the tmux status
line are written there too. The page shows that frame without scripts and with motion off;
`terminal.js` plays the session on from it and comes back to it, taking the prompt, btop's
panels and fastfetch's rows from the page, and keeps the status line's clock.

A character that Unicode normalisation would fold into another one (two of the Greek Extended
samples, U+1F71 and U+1F7B, fold into Greek and Coptic) is written as an escape in `build.py`
and as a character reference in the page, so no editor or tool can change it; the tests check
that the pages are in normal form C and that every sample lies inside its block.

## Rebuilding

Run these from the repository root. The pages, the stylesheet and the scripts, with the
standard library only:

```bash
python3 site/build.py
```

To check that `docs/` matches the sources, without writing anything (exit status 1 if not):

```bash
python3 site/build.py --check
```

The subset fonts need fontTools and brotli. Run the script with the Python of the virtual
environment that [README.md](../README.md#tools) sets up:

```bash
.venv/bin/python site/subset-fonts.py
```

With Nix, a one-off shell has both instead:
`nix-shell -p 'python3.withPackages(ps: [ps.fonttools ps.brotli])' --run 'python3 site/subset-fonts.py'`.

The tests of the site (`./check.py` runs them with all the others):

```bash
python3 -m unittest discover -s tests -t . -p 'test_site.py' -v
```

`subset-fonts.py` takes `--jobs N` (parallel workers, 6 by default) and `--only t,d,s,l,m` to
rewrite some families only. A full run takes a few minutes. It reads the built fonts under
`noctua-iosevka/` and never writes there; restore them first with `./font-archives.py fetch`
if they are missing. Both scripts are deterministic: the same inputs give the same bytes.

## The fonts

All five families are subsets of the same files, so every face on the page is a real face of
Noctua Iosevka. The page sets `font-synthesis: none`: the browser may never fake a weight or
a slant.

| folder | CSS family | faces | for | what each face keeps |
|---|---|---|---|---|
| `text/` | `Noctua Iosevka` | 135 | running text, the type tester | Latin with Latin Extended-A, Greek, Cyrillic, punctuation, arrows, some mathematics, box drawing, blocks, geometric shapes, Braille; `calt`, `dlig`, `HSKL`, `zero`, `onum`, `frac`, `ss01`–`ss20` |
| `display/` | `NI Display` | 135 | titles, headings, tapes, the width ladder | Latin-1 and basic Cyrillic, no layout features |
| `swatch/` | `NI Swatch` | 135 | the 135-face wall, the explorer | the four glyphs of “Aa” and “Ag” |
| `lab/` | `NI Lab` | 1 | the character-variant machine, its section numeral, the coverage strips | the machine's glyphs with `cv01`–`cv99`, and 24 sample characters of each Unicode block in the coverage table |
| `term/` | `NoctuaIosevka Nerd Font Mono` | 3 | the terminal | Latin-1, box drawing, Braille, Powerline and the icons the terminal shows |

Three headings are set in the text faces (ExtraBold Condensed) because they need what only
those carry: §06 wears the stylistic set the lens shows, §08 starts with a live `calt`
ligature, and §11 writes Greek and Cyrillic in their own alphabets. The §11 sample rows use the
same face, and its italic for the Ukrainian line. Where a section is about a face, its outlined
numeral shows that face: §03 runs from Condensed to Extended, §04 is italic, §06 is set in the
text Thin and wears the lens's set, and §07 is set in the lab face with a random one of its
zero's character variants (`cv10`).

The character variants live only in the lab face: they cost about 45 KB per face, and only
the machine uses them. The coverage strips live there too: most of their characters (Latin
Extended-B, IPA, Greek Extended …) are outside the text repertoire, and one face is cheaper
than 135.

"Wear it" (the stylistic-set cards) sets the running text in a set. The display faces carry no
stylistic sets — with them, every display face would grow by 18 KB, past both budgets — so
headings keep their own shapes, and wearing a set fetches nothing.

Budgets, all checked by the tests or measured in the browser:

* **All site fonts ≤ 15 MB.** 13.8 MB today (13,847,008 bytes in 409 faces: text 135 × ~82 KB,
  display 135 × ~16 KB, swatch 135 × ~1.4 KB, lab 63 KB, terminal 3 × ~35 KB);
  `tests/test_site.py` fails above 15,000,000 bytes.
* **Fonts fetched by the first view ≤ 600 KB.** About 408–439 KB (20–23 faces, measured in
  Chrome from 320 to 2560 px, both languages, six seconds on the hero): the text Regular and
  Bold, the display faces of the hero and its tapes (Condensed on phones, where the wordmark is
  Condensed and the weight tape shares its faces), and the heading face of the sections just
  below. Measure it without forcing a layout
  of the whole page: a script that reads every element's box makes the browser lay out the
  sections it is skipping, and their faces load too.
* **Every other face loads only when used.** Sections far from the viewport carry
  `content-visibility: auto`, so their text is not even laid out; the special faces a block
  needs are listed in its `data-arm` attribute and fetched when it comes within half a
  viewport, before the block switches to them (`static/js/arm.js`). The 135-face sheet arms
  one slope's panel (45 faces) at a time, so the first panel fills in without waiting for the
  other two. The tester and the explorer fetch a text face only when the visitor picks it.
  Without scripts none of this can run: the page is laid out whole and every face it shows is
  fetched with it (see "Without JavaScript").

The licences travel with the fonts, as the SIL OFL 1.1 requires even when a website serves
them: `subset-fonts.py` copies `OFL-Iosevka.txt` and, because a Nerd Font face ships,
`LICENSE-NerdFontsSymbolsOnly.txt` into `docs/assets/fonts/licenses/`, and the page links both.

## Content Security Policy

Both pages carry the same policy as a `<meta http-equiv>`, before any script or stylesheet:

```
default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:;
connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'
```

So the generated HTML has no inline `<script>` bodies, no `<style>` elements, no `style=`
attributes and no `on…=` handlers, and the scripts never call `eval` or `Function`.
Scripts set styles through the CSSOM (`element.style.setProperty`), which the policy allows.
The theme and the motion setting are restored before the first paint by `boot.js`, a tiny
blocking script in `<head>` that reads `localStorage` inside `try`/`catch` (a classic script,
the only one: every other script is an ES module). It also marks `<html>` with the class `js`,
so the section menu button stands in for the list from the first paint, and the stylesheet
tells the two pages apart (see "Without JavaScript"). Nothing is fetched from another origin:
no CDN, no web font service, no analytics. The tests check all of this.

## Without JavaScript

The page is then a printed specimen, complete in itself: nothing on it asks for a click that
does nothing. The rules live in the stylesheet, under `html:not(.js)`, and in two classes the
template and the build put on elements: `.js-only` (not shown without scripts) and
`.static-only` (shown only without them).

* **What only a script can drive is not shown** (`.js-only`): the theme and motion switches,
  the explorer's chips and its scanner's note, the squint slider and "Print on one spot", the
  dot screen and "Print your own", the loupe's hint, the owl, the lens's instructions and "Wear
  it", "Show all sets", the character-variant picker, its Spin and its tiles, the ligature
  switches, the editor's tabs, minimap and language, the type tester's controls, the install
  tabs, every Copy button, the globe, the cursor trail, the ruler, the hero's shader, tapes and
  hint, the tmux clock and the colophon's count of loaded faces. The tests fail on a button,
  field, tab, radio, switch or tab stop outside a `.js-only` element (the tester's text box,
  which takes typing on its own, aside).
* **What scripts would hide is shown**: all five files of the editor and all three systems of
  the install steps, one under the other, each under its own name (a group named by its
  heading, and no tab stop; `ui.js` makes them tab panels named by their tabs, which take
  focus). All nineteen set cards show.
* **Every face is real at once.** The lazy face classes (`.lfd`, `.lw1`, `.lx5`, `.lsi` …)
  apply without `[data-armed]`, so the sheet's 135 tiles, the headings drawn in several faces,
  the width ladder and the download cards show their faces. The sheet's tiles and the set
  cards' specimens are static type (`ui.js`'s `asButton` turns them into buttons).
* **Still frames, not empty boxes**: the terminal shows the build's still frame and its side
  panel; the lens rests over the sample, in register, in the set that redraws the most, which
  the §06 title wears too (`facts.css`); each ligature group shows its own feature at work; the
  confusable pairs are printed on one spot, as the lede says; the machine shows its first glyph
  and its reading.
* **A few notes are written for this page** (`.static-only`): the sheet's hint, the lens's set,
  and the tester's (the text box stays in the Regular).
* **The page is laid out whole**: `content-visibility: auto` applies only with scripts, because
  without `ui.js` laying out the sections before a jump, an in-page link would be aimed at their
  guessed heights. A link lands on its section: clear of the fixed masthead above 1240 px, and
  12 px below the top of the window up to that width, where the masthead scrolls away with the
  page.
  So every face the page shows is fetched with it — about 170 faces, 1.1 MB on a phone and
  1.3 MB on a desktop (measured in Chrome, both languages) — where the scripted page fetches
  them as they come near; the 600 KB budget is the scripted page's first view.

Check it in a browser with JavaScript disabled, at a phone width and a desktop one, in both
schemes.

## Motion and accessibility

How motion is scheduled:

* **Canvas and script effects** (the hero shader, the tapes, the owl, the dot screen, the lens,
  the explorer's scanner, the globe, the terminal, the kinetic titles) register with one shared
  `requestAnimationFrame` loop in `motion.js`. Each effect ticks only while motion is on, the
  tab is visible and its element is near the viewport (an IntersectionObserver per element).
  Effects that need a box read it in the loop's read phase, which runs before any effect
  writes (the hero shader reads the title, the owl how far it has come into view, the
  explorer its tile centres, once per layout).
* **A few short loops of their own** check `motion.on` and stop by themselves: the registration
  spring that scroll speed sets off (`slip.js`), the cursor trail (`trail.js`), the scroll
  choreography (`scroll.js`, one frame per scroll event), the slot machine's spin (`cv.js`) and
  the decoding samples (`scripts.js`).
* **CSS animations** run only under `html[data-motion="on"]`, and stop when a section scrolls
  away because sections carry `content-visibility: auto` (a skipped subtree runs no animation).
  The looping marks that compete with reading are calmed: the editor's line scan runs once when
  the editor arrives, the registration wobbles and the confusable pairs run twice, and each
  starts again only while the pointer is over it; the hero's hint dot pulses only while the
  hero is on screen.
* The continuous animations move transforms and opacity. The lens of §06 is a round window
  that slides by transform while the copy of the text inside it slides the other way, so it
  stays in register without a repaint. The deliberate exceptions, which lay out a line or a
  box on purpose: the headings that scrub their weight with the scroll (four of them;
  `font-weight` steps through seven real faces, one layout per step), the width-breathing word
  (it steps through the five real widths, which is the point), the hero's slope cuts, the
  explorer's scanner (it puts a new face on the stage every 1.1 s, and the metric guides glide
  to the new advance with `left`/`width` transitions). One-shot entrances (the theme switch,
  the ladder, and the sheet's tiles, panel by panel as its faces arrive; a sheet already in
  view when the scripts start keeps still) use transforms too.

And the rest:

* `prefers-reduced-motion: reduce` gives a still page — the CSS honours it even without
  scripts — and the **Pause motion** button in the masthead stops everything and is
  remembered.
* The hero shader runs only where WebGL is fast. The context is requested with
  `failIfMajorPerformanceCaveat`, and a software renderer (SwiftShader, llvmpipe …) is refused
  by name. There, on any compile or link failure and on a lost context, the hero gets a still
  print of the same picture instead: `print.js` computes the shader's own frame on the CPU into
  a 2D canvas, once, in slices of a few milliseconds. If the shader's frames stay over 100 ms
  at its lowest resolution for three seconds, it holds its last frame. Until either has drawn,
  the hero is plain paper: the canvas fades in on its first complete frame. The shader falls
  back to `mediump` where `highp` is missing.
* Canvases are decorative (`aria-hidden`), capped at a device pixel ratio of 2 (all of them go
  through `dpr()` in `motion.js`, the loupe included) and sized to their box; the hero shader
  lowers its resolution when frames run long. The loupe redraws a line at the screen's pixel
  density, up to 2×; a canvas cannot apply OpenType features, so while the page wears a
  stylistic set it says that it shows the default shapes.
* In-page links land exactly on their target and move keyboard focus there, with or without
  motion (sections, and `<main>` for the skip link, take `tabindex="-1"`). A jump of more than
  three screens is instant; a shorter one glides. Once the page has come to rest the target is
  held in place for a moment, because faces arriving and blocks arming above it, or in it (a
  section's title takes its own faces and grows), can still change their height; the hold ends
  as soon as the visitor scrolls, types or touches. Below
  1240 px the section list folds into a menu button.
* Live regions speak only when the visitor changes something: the build writes their first
  reading (the character-variant count, the squint value in the page's number format), the
  scripts write a region only when its text changes, and the type tester says only its short
  state ("real face, loaded"), after the controls have been still for a moment. Copy buttons
  announce through one status region.
* Day (paper and three riso inks) and night (the same inks as phosphor light) are both
  designed; the choice is remembered, and the system setting is the default. By day each
  section carries a halftone field of its ink, a dot screen at that ink's angle; by night a
  soft glow, with the lime kept faint. Fields sit below the section heads. Three sections are
  printed on a solid plate — the ligatures on yellow (lime by night), the terminal on black,
  the download on pink — with the controls on them knocked out to the paper (the config copy
  buttons stay on the band, in its ink).
* Section heads take three layouts: a title fitted to the column on one line (§02, §06, §11,
  sized by `facts.css`), the lede beside a title set right (§04, §08, §10, §12, §14), and the
  title over the lede.
